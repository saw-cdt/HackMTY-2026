"""
El retador: recibe un hallazgo en BORRADOR (el que arma investigator.py)
y su UNICA tarea es construir la explicacion inocente mas fuerte posible
que encaje con esos mismos datos -- no decide si "cree" que es fraude,
intenta activamente tumbarlo.

Para eso vuelve a consultar el estate por su cuenta (contratos, ordenes
de compra, reciprocidad) en vez de confiar solo en lo que el hallazgo ya
cito -- es exactamente el punto: un investigador pudo haber armado el
caso ignorando algo que lo explica.

NUNCA recibe el candidato original de prioritized_candidates() ni su
"signal": no sabe que detector disparo esto, para que su argumento venga
solo de la evidencia, no de adivinar la intencion del detector. Tampoco
lee la respuesta correcta -- no importa nada de generate/.

Responde JSON corto: {"survives": true|false, "argument": "<40 palabras>"}.
Que pasa despues (cerrar con closed_by=challenger, o guardar el argumento
en el case file) lo decide quien orquesta el ciclo (Fase 4.4), no este
modulo.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import db
import tools

MAX_PALABRAS_ARGUMENTO = 40

SYSTEM_PROMPT = (
    "Eres un abogado defensor especializado en materia fiscal. Se te "
    "presenta un hallazgo de fraude ya armado, con su evidencia. Tu "
    "UNICA tarea es construir la explicacion inocente MAS FUERTE que "
    "encaje con esos mismos datos -- tu trabajo es intentar tumbarlo con "
    "el mejor argumento posible, no juzgar si te parece fraude. No "
    "inventes hechos que no esten en la evidencia de abajo. Responde "
    "siempre con el JSON exacto que se te pide, sin texto adicional "
    "antes ni despues."
)


def _clabe_de_entidad(conn, entity):
    """RFC:xxx -> su bank_clabe en vendors. EMP:xxx -> su bank_clabe en
    employees. None si no resuelve (o si la entidad es otra cosa)."""
    if entity.startswith("RFC:"):
        v = tools.vendor(conn, entity.split(":", 1)[1])
        return v["bank_clabe"] if v else None
    if entity.startswith("EMP:"):
        row = conn.execute(
            "SELECT bank_clabe FROM employees WHERE emp_id = ?", (entity,)
        ).fetchone()
        return row["bank_clabe"] if row else None
    return None


def _hay_transferencia_directa(conn, clabe_a, clabe_b):
    row = conn.execute(
        "SELECT 1 FROM bank_txns WHERE (from_clabe = ? AND to_clabe = ?) "
        "OR (from_clabe = ? AND to_clabe = ?) LIMIT 1",
        (clabe_a, clabe_b, clabe_b, clabe_a),
    ).fetchone()
    return row is not None


def vinculo_de_dinero_es_real(conn, finding):
    """Cuarto hecho, y el unico que se verifica ANTES de consultar al
    modelo: si el hallazgo acusa a 2+ entidades de estar vinculadas por
    dinero, ¿existe de verdad una transferencia directa entre sus CLABEs
    en bank_txns? Que dos entidades bancen en la misma institucion (o
    compartan region/plaza) no es un vinculo -- eso es exactamente el
    decoy "mismo banco": comparar CLABE completo, nunca por prefijo.

    Si el hallazgo tiene menos de 2 entidades resolubles a CLABE (ej.
    phantom_vendor, que solo acusa a un RFC), no hay vinculo que
    verificar y esto no aplica -- regresa True."""
    clabes = [c for c in (_clabe_de_entidad(conn, e) for e in finding.get("entities", [])) if c]
    if len(clabes) < 2:
        return True
    for i in range(len(clabes)):
        for j in range(i + 1, len(clabes)):
            if _hay_transferencia_directa(conn, clabes[i], clabes[j]):
                return True
    return False


def _contraevidencia(conn, finding):
    """Vuelve a consultar el estate para cada RFC del hallazgo, sin
    confiar en lo que el hallazgo ya cito. Los entities EMP: se ignoran
    aqui -- no hay herramienta para consultarlos por si solos."""
    empresa_rfc = db.company_rfc(conn)
    info = []
    for entity in finding.get("entities", []):
        if not entity.startswith("RFC:"):
            continue
        rfc = entity.split(":", 1)[1]
        vendor = tools.vendor(conn, rfc)
        support = tools.support_for(conn, rfc)
        recip_ida_y_vuelta = False
        if empresa_rfc and empresa_rfc != rfc:
            recip = tools.reciprocity(conn, rfc, empresa_rfc)
            # reciprocidad real = facturas en AMBOS sentidos. Una sola
            # factura del proveedor a la empresa no es reciprocidad --
            # es, muy probablemente, la misma factura ya acusada.
            hay_rfc_a_empresa = any(i["issuer_rfc"] == rfc for i in recip["invoices"])
            hay_empresa_a_rfc = any(i["issuer_rfc"] == empresa_rfc for i in recip["invoices"])
            recip_ida_y_vuelta = hay_rfc_a_empresa and hay_empresa_a_rfc
        info.append({"rfc": rfc, "vendor": vendor, "support": support,
                      "reciprocidad_real": recip_ida_y_vuelta})
    return info


def _resumen(finding):
    """Solo el contenido del hallazgo -- lo que el investigador alega.
    Los datos verificados de forma independiente van aparte (ver
    _tabla_de_hechos), pegados justo antes de la pregunta, para que no
    se diluyan entre la narrativa y los exhibits."""
    lineas = [
        f"Tipo de esquema alegado: {finding.get('scheme_type')}",
        f"Entidades acusadas: {', '.join(finding.get('entities', []))}",
        f"Regla que se alega rota: {finding.get('rule_broken')}",
        f"Monto: ${finding.get('peso_amount', 0):,.2f}. Confianza declarada: {finding.get('confidence')}.",
        f"Narrativa del investigador: {finding.get('narrative')}",
        "",
        "Exhibits citados por el investigador:",
    ]
    for ex in finding.get("exhibits", []):
        lineas.append(f"  - [{ex['source_table']}] {ex['record_id']}: {ex['note']}")

    if finding.get("money_trail"):
        lineas.append("Money trail citado:")
        for paso in finding["money_trail"]:
            lineas.append(f"  - {paso['from']} -> {paso['to']}: ${paso['amount']:,.2f} ({paso['date']})")

    return "\n".join(lineas)


def _tabla_de_hechos(contexto):
    """Los hechos que el retador verifico el mismo, como tabla SI/NO --
    nada de prosa que un modelo de 7B pueda leer mal."""
    lineas = ["HECHOS VERIFICADOS (el retador los confirmo el mismo, no el investigador):"]
    for c in contexto:
        s = c["support"]
        tiene_contrato = len(s["contracts"]) > 0
        tiene_oc = len(s["purchase_orders"]) > 0
        lineas.append(f"RFC {c['rfc']}:")
        lineas.append(f"  contrato registrado: {'SI (' + str(len(s['contracts'])) + ')' if tiene_contrato else 'NO'}")
        lineas.append(f"  orden de compra registrada: {'SI (' + str(len(s['purchase_orders'])) + ')' if tiene_oc else 'NO'}")
        lineas.append(f"  reciprocidad real (facturas en ambos sentidos): "
                       f"{'SI' if c['reciprocidad_real'] else 'NO'}")
    return "\n".join(lineas)


def _prompt(resumen, hechos):
    return (
        f"{resumen}\n\n"
        f"{hechos}\n\n"
        "Regla unica: tu conclusion depende SOLO de la tabla de HECHOS "
        "VERIFICADOS de arriba, nada mas.\n"
        "- Si esa tabla tiene al menos un SI (contrato, orden de compra, "
        "o reciprocidad real), hay explicacion inocente: cita el/los SI "
        "con su numero exacto y concluye queda_explicado.\n"
        "- Si esa tabla es todo NO, no hay explicacion inocente posible "
        "-- no inventes una. Concluye sigue_pareciendo_fraude.\n\n"
        "Responde SOLO con este JSON, argument en menos de 40 palabras:\n"
        '{"conclusion": "queda_explicado"|"sigue_pareciendo_fraude", "argument": "..."}'
    )


def challenge(conn, llm, finding):
    """Regresa exactamente {"survives": bool, "argument": str}. No decide
    closed_by ni toca el case file -- eso es de quien orquesta el ciclo.

    Internamente NO le pedimos al modelo el booleano "survives"
    directamente: en pruebas invertia la polaridad con frecuencia (un
    argumento que decia "esto lo explica" marcado igual que uno que
    decia "esto no basta"). En vez de eso pedimos una palabra sin
    ambiguedad de sentido y la traducimos aqui, en codigo."""
    if not vinculo_de_dinero_es_real(conn, finding):
        # Contradiccion factual, no de criterio: el hallazgo acusa a dos
        # o mas entidades de estar vinculadas por dinero, y bank_txns no
        # tiene ninguna transferencia directa entre sus CLABEs. No hace
        # falta -ni corresponde- preguntarle al modelo si esto "convence":
        # el vinculo que alega simplemente no existe.
        return {
            "survives": False,
            "argument": ("El hallazgo alega un vinculo de dinero entre las entidades "
                          "acusadas, pero no existe ninguna transferencia directa entre "
                          "sus CLABEs en bank_txns: el vinculo no existe."),
        }

    contexto = _contraevidencia(conn, finding)
    resumen = _resumen(finding)
    hechos = _tabla_de_hechos(contexto)

    veredicto = llm.chat_json(_prompt(resumen, hechos), system=SYSTEM_PROMPT)

    survives = veredicto.get("conclusion") != "queda_explicado"
    argument = (veredicto.get("argument") or "").strip()
    palabras = argument.split()
    if len(palabras) > MAX_PALABRAS_ARGUMENTO:
        argument = " ".join(palabras[:MAX_PALABRAS_ARGUMENTO])
    if not argument:
        argument = "Sin argumento generado."

    # Red de seguridad: los UNICOS hechos que este sistema reconoce como
    # explicacion inocente son contrato, orden de compra o reciprocidad
    # real (ver _tabla_de_hechos). Si NINGUNO existe, es logicamente
    # imposible que "queda_explicado" sea correcto -- en pruebas el
    # modelo a veces lo dijo de todos modos, sin base, pese a resumir
    # bien los hechos en su propio argumento. No se le cree a ciegas:
    # se corrige aqui, igual que el validador (Fase 4.3) corrige
    # cualquier otra cosa que no reconcilie.
    hay_hecho_exculpatorio = any(
        len(c["support"]["contracts"]) > 0
        or len(c["support"]["purchase_orders"]) > 0
        or c["reciprocidad_real"]
        for c in contexto
    )
    if not hay_hecho_exculpatorio:
        survives = True
        # el argumento del modelo puede quedar mal formulado cuando lo
        # corregimos (a veces resume los hechos en el orden equivocado
        # para lo que "survives": true implica) -- se reemplaza por uno
        # parejo con el veredicto ya corregido, no con el que pudo haber
        # escrito el modelo antes de la correccion.
        argument = ("El retador no encontro contrato, orden de compra, ni "
                     "reciprocidad real que lo explique: el hallazgo se sostiene.")

    return {"survives": survives, "argument": argument}
