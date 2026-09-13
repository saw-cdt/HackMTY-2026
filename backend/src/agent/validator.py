"""
El validador: SIN modelo, solo codigo. Verifica cada hallazgo antes de
publicarlo. Si algo falla, el hallazgo NO se publica -- pasa a
leads_not_pursued con closed_by: "validator" y el motivo especifico que
lo tumbo.

Las reglas espejan exactamente las que corre validate_format.py (el
validador oficial de los organizadores, en la raiz de backend/): mismos
nombres de tabla, misma columna de id por tabla, misma tolerancia del
2% sumando POR TABLA. No es casualidad -- es la misma regla aplicada en
dos momentos distintos: aqui, ANTES de que el hallazgo entre a
submission.json, para decidir si se publica; el oficial, DESPUES, sobre
el archivo ya armado, para confirmar que el formato completo es correcto.

No importa nada de generate/ ni lee la respuesta correcta.
"""
SCHEME_TYPES = {
    "phantom_vendor", "kickback", "round_tripping",
    "threshold_splitting", "revenue_inflation",
}
ID_COLUMN = {
    "ledger": "entry_id", "invoices": "uuid", "bank_txns": "txn_id",
    "vendors": "rfc", "efos_list": "rfc", "purchase_orders": "po_id",
    "contracts": "contract_id", "employees": "emp_id",
}
AMOUNT_COLUMN = {
    "invoices": "total", "bank_txns": "amount",
    "purchase_orders": "amount", "contracts": "value",
}
MIN_EXHIBITS = 3
MAX_NARRATIVE_WORDS = 150
PESO_TOLERANCE = 0.02


def _check_scheme_type(finding, errores):
    if finding.get("scheme_type") not in SCHEME_TYPES:
        errores.append(f"scheme_type invalido: {finding.get('scheme_type')!r}, "
                        f"debe ser uno de {sorted(SCHEME_TYPES)}")


def _check_entities(finding, errores):
    entities = finding.get("entities")
    if not entities:
        errores.append("entities esta vacio")
        return
    for e in entities:
        if not (str(e).startswith("RFC:") or str(e).startswith("EMP:")):
            errores.append(f"entity sin prefijo RFC: o EMP: -> {e!r}")


def _check_narrative(finding, errores):
    narrative = finding.get("narrative") or ""
    n = len(narrative.split())
    if n == 0:
        errores.append("narrative esta vacio")
    elif n > MAX_NARRATIVE_WORDS:
        errores.append(f"narrative tiene {n} palabras, maximo {MAX_NARRATIVE_WORDS}")


def _check_exhibits_existen(conn, finding, errores):
    """Al menos 3 exhibits, sin exhibit_id repetido, source_table valida,
    y cada record_id citado existe de verdad en esa tabla del estate."""
    exhibits = finding.get("exhibits") or []
    if len(exhibits) < MIN_EXHIBITS:
        errores.append(f"solo {len(exhibits)} exhibits, minimo {MIN_EXHIBITS}")

    vistos = set()
    for i, ex in enumerate(exhibits):
        eid = ex.get("exhibit_id")
        tabla = ex.get("source_table")
        rid = str(ex.get("record_id", ""))

        if eid in vistos:
            errores.append(f"exhibits[{i}]: exhibit_id {eid!r} repetido")
        vistos.add(eid)

        if tabla not in ID_COLUMN:
            errores.append(f"exhibits[{i}]: source_table invalida -> {tabla!r}")
            continue

        col = ID_COLUMN[tabla]
        row = conn.execute(f"SELECT 1 FROM {tabla} WHERE {col} = ?", (rid,)).fetchone()
        if row is None:
            errores.append(f"exhibits[{i}]: {tabla}.{rid!r} no existe en el estate")


def _monto_por_tabla(conn, exhibits):
    """Suma los montos de los exhibits POR TABLA (invoices/bank_txns/
    purchase_orders/contracts). Una factura y la transferencia que la
    liquido son los mismos pesos vistos dos veces -- por eso se suma
    por tabla, nunca entre tablas."""
    por_tabla = {}
    for ex in exhibits:
        tabla = ex.get("source_table")
        col = AMOUNT_COLUMN.get(tabla)
        if not col or tabla not in ID_COLUMN:
            continue
        rid = str(ex.get("record_id", ""))
        row = conn.execute(
            f"SELECT {col} FROM {tabla} WHERE {ID_COLUMN[tabla]} = ?", (rid,)
        ).fetchone()
        if row is not None and row[0] is not None:
            por_tabla[tabla] = por_tabla.get(tabla, 0.0) + float(row[0])
    return por_tabla


def _check_peso_amount(conn, finding, errores):
    peso = finding.get("peso_amount")
    if not isinstance(peso, (int, float)) or peso <= 0:
        errores.append(f"peso_amount invalido: {peso!r}, debe ser numero positivo")
        return

    exhibits = finding.get("exhibits") or []
    por_tabla = _monto_por_tabla(conn, exhibits)
    if not por_tabla:
        errores.append("ningun exhibit cita una tabla con monto "
                        f"({sorted(AMOUNT_COLUMN)}): peso_amount no puede reconciliar")
        return

    mejor_tabla, mejor_valor = min(por_tabla.items(), key=lambda kv: abs(peso - kv[1]))
    tolerancia = PESO_TOLERANCE * max(mejor_valor, 1)
    if abs(peso - mejor_valor) > tolerancia:
        detalle = ", ".join(f"{t}={v:,.2f}" for t, v in sorted(por_tabla.items()))
        errores.append(
            f"peso_amount {peso:,.2f} no reconcilia dentro del 2% contra ningun "
            f"exhibit (mejor empate: {mejor_tabla}={mejor_valor:,.2f}) [{detalle}]"
        )


def _check_money_trail(finding, errores):
    """El destino de cada paso es el origen del siguiente, y cada paso
    cita un exhibit_id que existe en los exhibits del hallazgo."""
    trail = finding.get("money_trail")
    if not trail:
        return  # opcional a nivel estructura; su ausencia no rechaza el hallazgo aqui

    exhibit_ids = {ex.get("exhibit_id") for ex in (finding.get("exhibits") or [])}
    for i, paso in enumerate(trail):
        for campo in ("from", "to", "amount", "date", "exhibit_id"):
            if campo not in paso:
                errores.append(f"money_trail[{i}]: falta el campo {campo!r}")

        eid = paso.get("exhibit_id")
        if eid is not None and eid not in exhibit_ids:
            errores.append(f"money_trail[{i}]: exhibit_id {eid!r} no esta en "
                            "los exhibits de este hallazgo")

        if i > 0 and paso.get("from") != trail[i - 1].get("to"):
            errores.append(
                f"money_trail[{i}]: origen {paso.get('from')!r} no conecta con "
                f"el destino del paso anterior {trail[i - 1].get('to')!r}"
            )


def validate(conn, finding):
    """Corre las 6 reglas. Regresa (ok, motivo): motivo es None si ok es
    True, o el detalle especifico (todas las fallas juntas, no solo la
    primera) si ok es False."""
    errores = []
    _check_scheme_type(finding, errores)
    _check_entities(finding, errores)
    _check_narrative(finding, errores)
    _check_exhibits_existen(conn, finding, errores)
    _check_peso_amount(conn, finding, errores)
    _check_money_trail(finding, errores)

    if errores:
        return False, "; ".join(errores)
    return True, None


def gate(conn, finding):
    """Punto de entrada. Regresa (kind, payload):
    kind="finding" -> el hallazgo intacto, listo para submission["findings"]
    kind="lead"    -> leads_not_pursued con closed_by="validator" y el
                      motivo especifico de rechazo como reason."""
    ok, motivo = validate(conn, finding)
    if ok:
        return "finding", finding

    entities = finding.get("entities") or ["desconocido"]
    lead = {
        "entity": entities[0],
        "signal": finding.get("scheme_type") or "hallazgo_no_valido",
        "reason": motivo,
        "tool_calls_made": [],
        "closed_by": "validator",
    }
    return "lead", lead
