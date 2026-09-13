"""
El retador: recibe un hallazgo en BORRADOR (el que arma investigator.py)
y su UNICA tarea es construir la explicacion inocente mas fuerte posible
que encaje con esos mismos datos -- no decide si "cree" que es fraude,
intenta activamente tumbarlo.

Para eso vuelve a consultar el estate por su cuenta (contratos, ordenes
de compra, facturas) en vez de confiar solo en lo que el hallazgo ya
cito -- es exactamente el punto: un investigador pudo haber armado el
caso ignorando algo que lo explica.

Los hechos que se le presentan al modelo estan ACOTADOS al tipo de
esquema: una explicacion inocente tiene que ser PERTINENTE al flujo de
dinero que se acusa, no solo existir en algun lugar del expediente. Un
contrato del proveedor con la empresa explica por que la empresa le paga
al proveedor -- no explica por que ese proveedor le manda dinero a la
cuenta personal de un empleado (kickback), ni por que un tercero le
regresa dinero a la empresa (round_tripping), a menos que exista una
factura que ampare especificamente ESE flujo de retorno:

    kickback / round_tripping
        unico hecho relevante: una factura de quien RECIBIO el ultimo
        tramo de dinero hacia quien lo ENVIO. Contrato/OC no cuentan.
    phantom_vendor / threshold_splitting
        aqui si: contrato, orden de compra y su alcance.
    revenue_inflation
        unico hecho relevante: si existe cobro real (bank_txn) de la
        factura acusada.

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


# ---------------------------------------------------------------------
# Hechos especificos por tipo de esquema (ver docstring del modulo). Cada
# helper regresa un booleano -- el UNICO exculpatorio que aplica a ese
# tipo de esquema -- para que _tabla_de_hechos() lo traduzca a una tabla
# SI/NO que el modelo no pueda leer mal.
# ---------------------------------------------------------------------
def _resolver_rfc(conn, empresa_rfc, ref):
    """CLABE, 'EMPRESA', o 'RFC:xxx' -> el RFC que podria haber emitido
    una factura por esa cuenta. None si no resuelve a un RFC -- un
    empleado (CLABE de employees, o 'EMP:xxx') nunca tiene RFC propio,
    nunca puede facturar, y por lo tanto nunca puede amparar un flujo de
    dinero via una factura."""
    if ref == "EMPRESA":
        return empresa_rfc
    if isinstance(ref, str) and ref.startswith("RFC:"):
        return ref.split(":", 1)[1]
    if isinstance(ref, str) and ref.startswith("EMP:"):
        return None
    quien = tools.whose_clabe(conn, ref)
    if quien["tipo"] == "vendor":
        return quien["rfc"]
    if quien["tipo"] == "empresa":
        return empresa_rfc
    return None


def _factura_de_retorno_existe(conn, empresa_rfc, finding):
    """kickback / round_tripping: el UNICO hecho que importa es si el
    flujo de RETORNO -- el ultimo tramo del money_trail, de quien manda
    el dinero a quien lo recibe -- esta amparado por una factura DEL
    RECEPTOR HACIA QUIEN LO ENVIO. Esa es la unica operacion que
    explicaria por que el dinero se mueve en ese sentido. Un contrato del
    proveedor con la empresa no dice nada sobre ESTE flujo especifico
    -- por diseno, no se consulta aqui."""
    trail = finding.get("money_trail")
    if not trail:
        return False
    ultimo = trail[-1]
    emisor_rfc = _resolver_rfc(conn, empresa_rfc, ultimo.get("from"))
    receptor_rfc = _resolver_rfc(conn, empresa_rfc, ultimo.get("to"))
    if not emisor_rfc or not receptor_rfc:
        return False  # ej. el receptor es un empleado: no puede facturar
    row = conn.execute(
        "SELECT 1 FROM invoices WHERE issuer_rfc = ? AND receiver_rfc = ? LIMIT 1",
        (receptor_rfc, emisor_rfc),
    ).fetchone()
    return row is not None


def _cobro_real_existe(conn, empresa_rfc, finding):
    """revenue_inflation: el UNICO hecho que importa es si existe un
    bank_txn que de verdad liquide la factura acusada -- un contrato o
    una orden de compra no prueban que se cobro."""
    empresa_clabes = db.company_clabes(conn)
    if not empresa_clabes:
        return False
    placeholders = ",".join("?" for _ in empresa_clabes)
    for entity in finding.get("entities", []):
        if not entity.startswith("RFC:"):
            continue
        rfc = entity.split(":", 1)[1]
        if rfc == empresa_rfc:
            continue
        cliente = tools.vendor(conn, rfc)
        if not cliente or not cliente.get("bank_clabe"):
            continue
        row = conn.execute(
            f"SELECT 1 FROM bank_txns WHERE from_clabe = ? AND to_clabe IN ({placeholders}) LIMIT 1",
            (cliente["bank_clabe"], *empresa_clabes),
        ).fetchone()
        if row:
            return True
    return False


def _soporte_documental(conn, finding):
    """phantom_vendor / threshold_splitting: aqui si importan contrato y
    orden de compra -- consultados de nuevo, nunca confiando en lo que el
    investigador ya cito."""
    info = []
    for entity in finding.get("entities", []):
        if not entity.startswith("RFC:"):
            continue
        rfc = entity.split(":", 1)[1]
        info.append({"rfc": rfc, "support": tools.support_for(conn, rfc)})
    return info


def _tabla_de_hechos(conn, empresa_rfc, scheme_type, finding):
    """Los hechos que el retador verifico el mismo, acotados al tipo de
    esquema para que la explicacion inocente sea PERTINENTE al flujo de
    dinero acusado, no solo algo que exista en el expediente. Regresa
    (texto_para_el_prompt, hay_hecho_exculpatorio)."""
    lineas = ["HECHOS VERIFICADOS (el retador los confirmo el mismo, no el investigador):"]

    if scheme_type in ("kickback", "round_tripping"):
        hay_retorno = _factura_de_retorno_existe(conn, empresa_rfc, finding)
        lineas.append(
            "factura de quien RECIBIO el ultimo tramo de dinero hacia quien lo "
            f"ENVIO (unica operacion que ampararia ese flujo): {'SI' if hay_retorno else 'NO'}"
        )
        lineas.append(
            "(un contrato o una orden de compra del proveedor con la empresa NO "
            "cuentan aqui: explican por que la empresa le paga al proveedor, no "
            "por que ese dinero sale despues hacia otra cuenta)"
        )
        return "\n".join(lineas), hay_retorno

    if scheme_type == "revenue_inflation":
        cobro = _cobro_real_existe(conn, empresa_rfc, finding)
        lineas.append(
            f"cobro real de la factura acusada (bank_txn que la liquida): "
            f"{'SI' if cobro else 'NO'}"
        )
        return "\n".join(lineas), cobro

    # phantom_vendor / threshold_splitting (y cualquier tipo no previsto):
    # contrato, orden de compra y su alcance. PERO para threshold_splitting
    # especificamente, una orden de compra no cuenta como exculpatoria: se
    # genera una por cada factura del fraccionamiento, sea o no fraude --
    # es el mecanismo del esquema, no una defensa contra el. Solo un
    # contrato (una autorizacion unica que cubra la relacion recurrente,
    # como un contrato marco con cuota fija) explica el patron.
    if scheme_type == "threshold_splitting":
        lineas.append(
            "(para este tipo de esquema, la orden de compra por si sola NO "
            "cuenta como explicacion: se genera una por cada factura, sea o "
            "no fraude -- solo un contrato que autorice la relacion "
            "recurrente completa la explica)"
        )

    exculpatorio = False
    for c in _soporte_documental(conn, finding):
        s = c["support"]
        contratos, ordenes = s["contracts"], s["purchase_orders"]
        lineas.append(f"RFC {c['rfc']}:")
        if contratos:
            alcance = "; ".join(ct["scope_text"] for ct in contratos)
            lineas.append(f"  contrato registrado: SI ({len(contratos)}) -- alcance: {alcance}")
        else:
            lineas.append("  contrato registrado: NO")
        if ordenes:
            alcance = "; ".join(po["description"] for po in ordenes)
            lineas.append(f"  orden de compra registrada: SI ({len(ordenes)}) -- alcance: {alcance}")
        else:
            lineas.append("  orden de compra registrada: NO")

        if scheme_type == "threshold_splitting":
            exculpatorio = exculpatorio or bool(contratos)
        else:
            exculpatorio = exculpatorio or bool(contratos) or bool(ordenes)
    return "\n".join(lineas), exculpatorio


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


def _prompt(resumen, hechos):
    return (
        f"{resumen}\n\n"
        f"{hechos}\n\n"
        "Regla unica: tu conclusion depende SOLO de la tabla de HECHOS "
        "VERIFICADOS de arriba, nada mas.\n"
        "- Si esa tabla tiene el hecho relevante en SI, hay explicacion "
        "inocente: citalo con su numero o alcance exacto y concluye "
        "queda_explicado.\n"
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

    empresa_rfc = db.company_rfc(conn)
    scheme_type = finding.get("scheme_type")
    resumen = _resumen(finding)
    hechos, hay_hecho_exculpatorio = _tabla_de_hechos(conn, empresa_rfc, scheme_type, finding)

    veredicto = llm.chat_json(_prompt(resumen, hechos), system=SYSTEM_PROMPT)

    survives = veredicto.get("conclusion") != "queda_explicado"
    argument = (veredicto.get("argument") or "").strip()
    palabras = argument.split()
    if len(palabras) > MAX_PALABRAS_ARGUMENTO:
        argument = " ".join(palabras[:MAX_PALABRAS_ARGUMENTO])
    if not argument:
        argument = "Sin argumento generado."

    # Red de seguridad: el UNICO hecho que este sistema reconoce como
    # explicacion inocente es el que corresponde al tipo de esquema (ver
    # _tabla_de_hechos). Si no existe, es logicamente imposible que
    # "queda_explicado" sea correcto -- en pruebas el modelo a veces lo
    # dijo de todos modos, sin base, pese a resumir bien los hechos en su
    # propio argumento. No se le cree a ciegas: se corrige aqui, igual
    # que el validador (Fase 4.3) corrige cualquier otra cosa que no
    # reconcilie.
    if not hay_hecho_exculpatorio:
        survives = True
        # el argumento del modelo puede quedar mal formulado cuando lo
        # corregimos (a veces resume los hechos en el orden equivocado
        # para lo que "survives": true implica) -- se reemplaza por uno
        # parejo con el veredicto ya corregido, no con el que pudo haber
        # escrito el modelo antes de la correccion.
        argument = ("El retador no encontro ningun hecho pertinente a este flujo de "
                     "dinero especifico que lo explique: el hallazgo se sostiene.")

    return {"survives": survives, "argument": argument}
