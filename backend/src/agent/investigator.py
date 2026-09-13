"""
El investigador: recibe UN candidato de prioritized_candidates() y decide
si arma un hallazgo o cierra el lead.

Consulta herramientas segun la hipotesis que sugiere candidate["signal"],
le pide al modelo una decision corta (JSON de 2-3 campos, nunca prosa
libre ni la evidencia completa de vuelta), y arma el hallazgo -- exhibits,
money_trail, peso_amount -- en CODIGO. El modelo nunca calcula montos ni
decide si algo se publica; eso ultimo es del validador (Paso 4.3).

No importa nada de generate/ ni lee la respuesta correcta: solo consulta
el estate a traves de las 8 herramientas de tools/.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import db
import tools

SCHEME_TYPES = [
    "phantom_vendor", "kickback", "round_tripping",
    "threshold_splitting", "revenue_inflation",
]
SIGNAL_TO_SCHEME = {
    "phantom_vendor_efos_sin_contrato_ni_oc": "phantom_vendor",
    "kickback_transferencia_a_empleado": "kickback",
    "round_tripping_ciclo_a_empresa": "round_tripping",
    "threshold_splitting_facturas_bajo_umbral": "threshold_splitting",
    "revenue_inflation_factura_sin_bank_txn": "revenue_inflation",
}
CONFIDENCES = {"proven", "probable"}

SYSTEM_PROMPT = (
    "Eres un investigador forense fiscal en Mexico. Decides, con la "
    "evidencia que se te da, si un proveedor merece un hallazgo de "
    "fraude o si el lead debe cerrarse. Nunca calculas montos ni "
    "porcentajes -- eso lo hace el codigo. Nunca decides si un hallazgo "
    "se publica -- eso lo decide otro proceso despues de ti. Responde "
    "siempre con el JSON exacto que se te pide, sin texto adicional "
    "antes ni despues."
)


# ---------------------------------------------------------------------
# Recabar evidencia (codigo, sin modelo)
# ---------------------------------------------------------------------
def gather_evidence(conn, candidate):
    """Consulta las herramientas relevantes para esta hipotesis. Regresa
    un dict con lo recabado + la lista de herramientas llamadas (para
    tool_calls_made si el lead se cierra)."""
    rfc = candidate["rfc"]
    tool_calls = []

    def llamar(nombre, fn, *args, **kwargs):
        tool_calls.append(nombre)
        return fn(conn, *args, **kwargs)

    vendor = llamar("vendor", tools.vendor, rfc)
    support = llamar("support_for", tools.support_for, rfc)
    invoices_emitidas = llamar("invoices_by(issuer)", tools.invoices_by, rfc, "issuer")
    invoices_recibidas = llamar("invoices_by(receiver)", tools.invoices_by, rfc, "receiver")

    money_trail = None
    if candidate.get("ruta"):
        # round_tripping ya trae la ruta completa desde el detector: no
        # hace falta (ni conviene) volver a rastrearla con trace_money,
        # que solo sigue UNA rama y puede no ser la del ciclo sembrado.
        money_trail = {"ruta": candidate["ruta"], "saltos": candidate.get("saltos"),
                        "regresa_al_origen": True}
    elif vendor and vendor.get("bank_clabe"):
        money_trail = llamar("trace_money", tools.trace_money, vendor["bank_clabe"], max_hops=4)

    empresa_rfc = db.company_rfc(conn)
    reciprocidad = None
    if empresa_rfc and empresa_rfc != rfc:
        reciprocidad = llamar("reciprocity", tools.reciprocity, rfc, empresa_rfc)

    return {
        "rfc": rfc,
        "vendor": vendor,
        "support": support,
        "invoices_emitidas": invoices_emitidas,
        "invoices_recibidas": invoices_recibidas,
        "money_trail": money_trail,
        "reciprocity": reciprocidad,
        "empresa_rfc": empresa_rfc,
        "tool_calls_made": tool_calls,
    }


def _resumen_evidencia(evidence, candidate):
    """Texto compacto para el prompt -- nunca se le manda al modelo un
    volcado crudo de filas de SQL."""
    lineas = [
        f"RFC investigado: {evidence['rfc']}",
        f"Senal del detector: {candidate['signal']}",
    ]

    v = evidence["vendor"]
    if v:
        lineas.append(f"Proveedor: {v['legal_name']} ({v.get('category')}), alta {v.get('registered_date')}.")
        if v.get("efos_status"):
            lineas.append(f"Lista 69-B: estatus {v['efos_status']}, publicado {v.get('efos_publication_date')}.")
        else:
            lineas.append("No aparece en la lista 69-B.")
    else:
        lineas.append("No es un proveedor registrado (puede ser la propia empresa).")

    s = evidence["support"]
    lineas.append(f"Contratos en el expediente: {len(s['contracts'])}. "
                  f"Ordenes de compra: {len(s['purchase_orders'])}.")

    inv_e = evidence["invoices_emitidas"]
    if inv_e:
        total = sum(i["total"] for i in inv_e)
        lineas.append(f"Facturas emitidas por este RFC: {len(inv_e)}, total ${total:,.2f}.")
    inv_r = evidence["invoices_recibidas"]
    if inv_r:
        lineas.append(f"Facturas donde este RFC es receptor: {len(inv_r)}.")

    mt = evidence["money_trail"]
    if mt and mt.get("ruta"):
        ultimo = mt["ruta"][-1]
        lineas.append(
            f"Rastreo de dinero: {len(mt['ruta'])} salto(s), "
            f"monto en el ultimo salto ${ultimo['amount']:,.2f}, fecha {ultimo['date']}."
        )
        if mt.get("regresa_al_origen"):
            lineas.append("El dinero regresa a una cuenta de la empresa.")
    else:
        lineas.append("Sin transferencias salientes rastreables desde este proveedor.")

    r = evidence["reciprocity"]
    if r and r["invoices"]:
        lineas.append(f"Hay {len(r['invoices'])} factura(s) en algun sentido entre este RFC y la empresa.")

    extra = {k: val for k, val in candidate.items()
             if k not in ("rfc", "signal", "ruta", "txn_ids")}
    if extra:
        lineas.append(f"Datos adicionales del detector: {extra}")

    return "\n".join(lineas)


# ---------------------------------------------------------------------
# Los tres prompts. Cada uno pide JSON corto (2-3 campos), nunca prosa
# libre ni que el modelo repita la evidencia.
# ---------------------------------------------------------------------
def _prompt_decision(resumen):
    return (
        f"{resumen}\n\n"
        "Con esta evidencia, decide si hay elementos para armar un "
        "hallazgo de fraude contra este RFC, o si el lead debe cerrarse.\n\n"
        "Responde SOLO con este JSON, sin texto adicional:\n"
        '{"decision": "hallazgo" o "cerrar", '
        f'"scheme_type": uno de {SCHEME_TYPES} o null si decision es "cerrar"}}'
    )


def _prompt_hallazgo(resumen, scheme_type, rfc):
    return (
        f"{resumen}\n\n"
        f"Confirmaste un hallazgo de tipo {scheme_type} contra {rfc}. Redacta:\n"
        "- rule_broken: la regla o articulo especifico que se viola. Para "
        "estos esquemas, casi siempre es el Articulo 69-B del Codigo Fiscal "
        "de la Federacion (simulacion de operaciones) -- usa otro solo si "
        "la evidencia apunta claramente a una regla distinta. No describas "
        "un patron estadistico como si fuera la regla.\n"
        "- narrative: lenguaje llano, menos de 150 palabras, que un juez "
        "no tecnico pueda seguir sin ayuda\n"
        '- confidence: "proven" si la evidencia es concluyente, '
        '"probable" si es fuerte pero no definitiva\n\n'
        "Responde SOLO con este JSON:\n"
        '{"rule_broken": "...", "narrative": "...", "confidence": "proven"|"probable"}'
    )


def _prompt_cierre(resumen, rfc, signal):
    return (
        f"{resumen}\n\n"
        f"Decidiste cerrar el lead contra {rfc} (senal: {signal}) sin "
        "levantar un hallazgo. Redacta la razon especifica. Tu primera "
        "frase debe decir, con los numeros exactos de arriba, cuantos "
        "contratos y cuantas ordenes de compra tiene en el expediente "
        "(por ejemplo: 'Tiene 1 contrato y 1 orden de compra registrados'). "
        "Despues explica por que eso descarta el fraude. Nunca una razon "
        'generica como "evidencia insuficiente".\n\n'
        "Responde SOLO con este JSON:\n"
        '{"reason": "..."}'
    )


# ---------------------------------------------------------------------
# Construir el caso: entities, exhibits, peso_amount, money_trail.
# Siempre en codigo -- el modelo ya dijo que si a un hallazgo, pero no
# toca ni un numero de aqui en adelante.
# ---------------------------------------------------------------------
def _exhibit(exhibits, source_table, record_id, note):
    eid = f"EX-{len(exhibits) + 1:02d}"
    exhibits.append({
        "exhibit_id": eid, "source_table": source_table,
        "record_id": str(record_id), "note": note,
    })
    return eid


def _construir_caso(conn, scheme_type, candidate, evidence):
    rfc = candidate["rfc"]
    exhibits = []
    money_trail = []
    entities = [f"RFC:{rfc}"]
    vendor = evidence.get("vendor")
    peso_amount = 0.0

    if vendor:
        _exhibit(exhibits, "vendors", rfc,
                 f"Proveedor {vendor['legal_name']}, categoria {vendor.get('category')}.")

    if scheme_type == "phantom_vendor":
        if vendor and vendor.get("efos_status"):
            _exhibit(exhibits, "efos_list", rfc,
                      f"Estatus {vendor['efos_status']} en la lista 69-B, "
                      f"publicado {vendor.get('efos_publication_date')}.")
        total = 0.0
        for inv in evidence["invoices_emitidas"]:
            eid = _exhibit(exhibits, "invoices", inv["uuid"],
                            f"Factura sin contrato ni orden de compra que la respalde, ${inv['total']:,.2f}.")
            total += inv["total"]
            money_trail.append({"from": "EMPRESA", "to": f"RFC:{rfc}", "amount": inv["total"],
                                 "date": inv["issue_date"], "exhibit_id": eid})
        peso_amount = round(total, 2)

    elif scheme_type == "kickback":
        emp_id = candidate["emp_id"]
        entities.append(emp_id)
        amount = candidate["monto"]
        eid_txn = _exhibit(exhibits, "bank_txns", candidate["txn_id"],
                            f"Transferencia de {rfc} a {emp_id} por ${amount:,.2f}.")
        if evidence["invoices_emitidas"]:
            inv = evidence["invoices_emitidas"][0]
            _exhibit(exhibits, "invoices", inv["uuid"],
                     "Factura pagada por la empresa antes del reembolso al empleado.")
        money_trail = [{"from": f"RFC:{rfc}", "to": emp_id, "amount": amount,
                         "date": candidate["fecha"], "exhibit_id": eid_txn}]
        peso_amount = round(amount, 2)

    elif scheme_type == "round_tripping":
        ruta = candidate.get("ruta", [])
        for i, paso in enumerate(ruta):
            eid = _exhibit(exhibits, "bank_txns", paso["txn_id"],
                            f"Salto {i + 1} del ciclo, ${paso['amount']:,.2f}, {paso['date']}.")
            money_trail.append({"from": paso["from_clabe"], "to": paso["to_clabe"],
                                 "amount": paso["amount"], "date": paso["date"], "exhibit_id": eid})
        if evidence["invoices_emitidas"]:
            inv = evidence["invoices_emitidas"][0]
            _exhibit(exhibits, "invoices", inv["uuid"], "Factura que origino el primer pago del ciclo.")
        peso_amount = round(ruta[0]["amount"], 2) if ruta else 0.0

    elif scheme_type == "threshold_splitting":
        total = 0.0
        for uuid_ in candidate.get("invoice_ids", []):
            inv = next((i for i in evidence["invoices_emitidas"] if i["uuid"] == uuid_), None)
            if inv is None:
                continue
            eid = _exhibit(exhibits, "invoices", inv["uuid"],
                            f"${inv['total']:,.2f}, justo debajo del umbral inferido "
                            f"(${candidate.get('umbral_inferido', 0):,.2f}).")
            money_trail.append({"from": "EMPRESA", "to": f"RFC:{rfc}", "amount": inv["total"],
                                 "date": inv["issue_date"], "exhibit_id": eid})
            total += inv["total"]
        peso_amount = round(total, 2)

    elif scheme_type == "revenue_inflation":
        entities.append(f"RFC:{candidate['cliente_rfc']}")
        inv_uuid = candidate.get("invoice_id")
        inv = next((i for i in evidence["invoices_emitidas"] if i["uuid"] == inv_uuid), None)
        monto = candidate.get("monto") or (inv["total"] if inv else 0.0)
        if inv:
            eid = _exhibit(exhibits, "invoices", inv["uuid"],
                            f"Factura emitida por la empresa a {candidate['cliente_rfc']}, "
                            f"${monto:,.2f}, sin transferencia que la liquide.")
            # no hay bank_txn -- el "trail" es la venta registrada que
            # nunca se cobro. Se muestra igual, incompleta, porque eso
            # es exactamente la prueba: el dinero nunca llego.
            money_trail.append({"from": f"RFC:{rfc}", "to": f"RFC:{candidate['cliente_rfc']}",
                                 "amount": monto, "date": inv["issue_date"], "exhibit_id": eid})
        cliente = tools.vendor(conn, candidate["cliente_rfc"])
        if cliente:
            _exhibit(exhibits, "vendors", candidate["cliente_rfc"],
                     f"Cliente {cliente['legal_name']}: sin bank_txn de su CLABE hacia la empresa.")
        if inv:
            for entry in tools.ledger_for(conn, inv["uuid"])[:2]:
                _exhibit(exhibits, "ledger", entry["entry_id"],
                         "Asiento de la venta, sin contraparte de cobro en bank_txns.")
        peso_amount = round(monto, 2)

    # red de seguridad: nunca menos de 3 exhibits
    if len(exhibits) < 3:
        for inv in evidence.get("invoices_emitidas", []):
            if len(exhibits) >= 3:
                break
            for entry in tools.ledger_for(conn, inv["uuid"]):
                if len(exhibits) >= 3:
                    break
                _exhibit(exhibits, "ledger", entry["entry_id"], "Asiento contable relacionado.")

    return entities, exhibits, peso_amount, money_trail


# ---------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------
def investigate(conn, llm, candidate):
    """Procesa UN candidato. Regresa (kind, payload):
    kind="finding"  -> payload listo para submission["findings"]
    kind="lead"     -> payload listo para submission["leads_not_pursued"]
    (sin closed_by en finding; con closed_by="investigator" en lead)."""
    rfc = candidate["rfc"]
    scheme_type_sugerido = SIGNAL_TO_SCHEME.get(candidate["signal"])

    evidence = gather_evidence(conn, candidate)
    resumen = _resumen_evidencia(evidence, candidate)

    decision = llm.chat_json(_prompt_decision(resumen), system=SYSTEM_PROMPT)
    quiere_hallazgo = decision.get("decision") == "hallazgo"
    scheme_type = decision.get("scheme_type") or scheme_type_sugerido

    if quiere_hallazgo and scheme_type in SCHEME_TYPES:
        entities, exhibits, peso_amount, money_trail = _construir_caso(
            conn, scheme_type, candidate, evidence)

        if peso_amount > 0 and len(exhibits) >= 3:
            redaccion = llm.chat_json(_prompt_hallazgo(resumen, scheme_type, rfc),
                                       system=SYSTEM_PROMPT)
            confidence = redaccion.get("confidence")
            if confidence not in CONFIDENCES:
                confidence = "probable"
            finding = {
                "scheme_type": scheme_type,
                "entities": entities,
                "narrative": (redaccion.get("narrative") or "").strip()
                or "Sin narrativa generada.",
                "rule_broken": (redaccion.get("rule_broken") or "").strip()
                or "SAT Articulo 69-B",
                "peso_amount": peso_amount,
                "confidence": confidence,
                "exhibits": exhibits,
            }
            if money_trail:
                finding["money_trail"] = money_trail
            return "finding", finding

    cierre = llm.chat_json(_prompt_cierre(resumen, rfc, candidate["signal"]), system=SYSTEM_PROMPT)
    lead = {
        "entity": f"RFC:{rfc}",
        "signal": candidate["signal"],
        "reason": (cierre.get("reason") or "").strip()
        or "Evidencia examinada, sin elementos suficientes para un hallazgo.",
        "tool_calls_made": evidence["tool_calls_made"],
        "closed_by": "investigator",
    }
    return "lead", lead
