"""
Las siete herramientas del agente + el gate de veredicto.
SQL puro (sin modelo) sobre el SQLite de generate_data.py.

Cada función devuelve DATOS, nunca un juicio — tal como pide el
doc de arquitectura. El gate al final es la única función que
etiqueta, y lo hace con reglas binarias, sin umbrales de porcentaje.
"""
import sqlite3

DB_PATH = "forensic_auditor.db"
EMPRESA_RFC = "MNO900101AB1"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------
# 1. candidatos_priorizados
# ---------------------------------------------------------------
def candidatos_priorizados():
    """Detectores baratos: proveedores sin soporte documental completo primero."""
    conn = _conn()
    rows = conn.execute("""
        SELECT p.rfc, p.nombre,
               COUNT(DISTINCT s.tipo) AS tipos_soporte,
               SUM(c.total) AS monto_total
        FROM proveedor p
        JOIN cfdi c ON c.rfc_emisor = p.rfc
        LEFT JOIN soporte_documental s ON s.uuid = c.uuid
        GROUP BY p.rfc
        ORDER BY tipos_soporte ASC, monto_total DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------
# 2. estatus_efos
# ---------------------------------------------------------------
def estatus_efos(rfc, fecha_factura):
    conn = _conn()
    rows = conn.execute(
        "SELECT etapa, fecha_dof, oficio FROM efos_evento WHERE rfc=? ORDER BY fecha_dof",
        (rfc,),
    ).fetchall()
    conn.close()
    if not rows:
        return {"estatus_a_la_fecha": "sin_registro", "retroactivo": False, "oficio": None}
    # último evento vigente en o antes de la fecha de la factura
    vigente = None
    for r in rows:
        if r["fecha_dof"] <= fecha_factura:
            vigente = r
    ultimo = rows[-1]
    return {
        "estatus_a_la_fecha": vigente["etapa"] if vigente else "presunto",
        "estatus_actual": ultimo["etapa"],
        "retroactivo": vigente is None and ultimo["etapa"] in ("definitivo",),
        "oficio": ultimo["oficio"],
        "fecha_dof": ultimo["fecha_dof"],
    }


# ---------------------------------------------------------------
# 3. facturas_de
# ---------------------------------------------------------------
def facturas_de(rfc_proveedor):
    conn = _conn()
    rows = conn.execute(
        "SELECT uuid, fecha, total FROM cfdi WHERE rfc_emisor=?", (rfc_proveedor,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------
# 4. materialidad
# ---------------------------------------------------------------
def materialidad(u):
    conn = _conn()
    rows = conn.execute(
        "SELECT tipo, referencia, monto_amparado FROM soporte_documental WHERE uuid=?", (u,)
    ).fetchall()
    total = conn.execute("SELECT total FROM cfdi WHERE uuid=?", (u,)).fetchone()["total"]
    conn.close()
    tipos = {r["tipo"] for r in rows}
    contrato = "contrato" in tipos
    entrega = "entrega" in tipos
    montos = [r["monto_amparado"] for r in rows if r["monto_amparado"] is not None]
    materialidad_parcial = bool(montos) and any(m < total for m in montos)
    return {
        "contrato": contrato,
        "orden_compra": "orden_compra" in tipos,
        "entrega": entrega,
        "materialidad_parcial": materialidad_parcial,
        "referencias": [dict(r) for r in rows],
    }


# ---------------------------------------------------------------
# 5. rastrear_dinero
# ---------------------------------------------------------------
def rastrear_dinero(u, max_saltos=4):
    conn = _conn()
    pago = conn.execute(
        "SELECT tran_id, monto FROM cfdi_pago WHERE uuid_factura=?", (u,)
    ).fetchone()
    if not pago:
        conn.close()
        return {"hay_pago": False}

    monto_original = pago["monto"]
    tran = conn.execute(
        "SELECT * FROM transaccion WHERE tran_id=?", (pago["tran_id"],)
    ).fetchone()
    cuenta_destino_inicial = tran["bene_acct"]

    # recorrer saltos siguientes desde la cuenta destino
    ruta = [cuenta_destino_inicial]
    actual = cuenta_destino_inicial
    monto_final = tran["monto"]
    fecha_inicial = tran["fecha"]
    fecha_final = tran["fecha"]
    saltos = 0
    while saltos < max_saltos:
        siguiente = conn.execute(
            "SELECT * FROM transaccion WHERE orig_acct=? ORDER BY fecha LIMIT 1", (actual,)
        ).fetchone()
        if not siguiente:
            break
        ruta.append(siguiente["bene_acct"])
        actual = siguiente["bene_acct"]
        monto_final = siguiente["monto"]
        fecha_final = siguiente["fecha"]
        saltos += 1

    cuenta_final = conn.execute(
        "SELECT * FROM cuenta WHERE acct_id=?", (actual,)
    ).fetchone()
    conn.close()

    pct_retorno = round(100 * monto_final / monto_original, 1) if monto_original else 0
    dias = (_to_date(fecha_final) - _to_date(fecha_inicial)).days

    return {
        "hay_pago": True,
        "monto_pagado": monto_original,
        "ruta": ruta,
        "saltos": saltos,
        "monto_retornado": monto_final,
        "pct_retorno": pct_retorno,
        "dias": dias,
        "cuenta_destino": actual,
        "titular_tipo": cuenta_final["titular_tipo"] if cuenta_final else None,
        "vinculo_con": cuenta_final["vinculo_con"] if cuenta_final else None,
        "tipo_vinculo": cuenta_final["tipo_vinculo"] if cuenta_final else None,
        "cuenta_destino_vinculada": bool(cuenta_final and cuenta_final["vinculo_con"]),
    }


def _to_date(s):
    from datetime import date
    y, m, d = map(int, s.split("-"))
    return date(y, m, d)


# ---------------------------------------------------------------
# 6. hay_reciprocidad
# ---------------------------------------------------------------
def hay_reciprocidad(rfc_a, rfc_b, periodo=None):
    conn = _conn()
    rows = conn.execute(
        "SELECT uuid, fecha, total FROM cfdi WHERE rfc_emisor=? AND rfc_receptor=?",
        (rfc_a, rfc_b),
    ).fetchall()
    conn.close()
    return {
        "hay_reciprocidad": len(rows) > 0,
        "facturas": [dict(r) for r in rows],
    }


# ---------------------------------------------------------------
# 7. deduccion
# ---------------------------------------------------------------
def deduccion(u):
    conn = _conn()
    row = conn.execute(
        "SELECT periodo, monto_deducido, iva_acreditado FROM ledger WHERE uuid=?", (u,)
    ).fetchone()
    conn.close()
    if not row:
        return {"deducido": False}
    return {"deducido": True, **dict(row)}


# ---------------------------------------------------------------
# EL GATE — vive en código, no en el prompt. Sin umbrales de %.
# ---------------------------------------------------------------
def gate_veredicto(ev):
    if ev["estatus"] in ("desvirtuado", "sentencia_favorable"):
        return "LIMPIO"
    if ev["contrato"] and ev["entrega"] and ev["pago_limpio"]:
        return "DEFENDIBLE"
    if ev["retorno"] and ev["reciprocidad_documentada"]:
        return "DEFENDIBLE"
    if ev["retorno"] and not ev["reciprocidad_documentada"] and ev["cuenta_destino_vinculada"]:
        return "ACUSACION"
    return "CORREGIR"


# ---------------------------------------------------------------
# Demo: correr el loop completo sobre los 4 proveedores sembrados
# ---------------------------------------------------------------
def investigar(rfc_proveedor):
    facturas = facturas_de(rfc_proveedor)
    resultados = []
    for f in facturas:
        u = f["uuid"]
        efos = estatus_efos(rfc_proveedor, f["fecha"])
        mat = materialidad(u)
        rastreo = rastrear_dinero(u)
        # "retorno" = el dinero se movió MÁS ALLÁ del pago inicial (hubo saltos
        # posteriores). El pago inicial en sí no es un retorno.
        retorno = rastreo.get("hay_pago") and rastreo.get("saltos", 0) > 0
        recip = {"hay_reciprocidad": False}
        if retorno:
            recip = hay_reciprocidad(EMPRESA_RFC, rfc_proveedor)

        ev = {
            "estatus": efos["estatus_a_la_fecha"],
            "contrato": mat["contrato"],
            "entrega": mat["entrega"],
            "pago_limpio": rastreo.get("hay_pago", False) and not retorno,
            "retorno": retorno,
            "reciprocidad_documentada": recip["hay_reciprocidad"],
            "cuenta_destino_vinculada": rastreo.get("cuenta_destino_vinculada", False),
        }
        veredicto = gate_veredicto(ev)
        resultados.append({
            "uuid": u, "monto": f["total"], "veredicto": veredicto,
            "evidencia": ev, "rastreo": rastreo, "materialidad": mat, "efos": efos,
        })
    return resultados


if __name__ == "__main__":
    proveedores = [
        ("SIB150304CD2", "legitimo", "DEFENDIBLE"),
        ("TRE180422XY3", "desordenado", "CORREGIR"),
        ("CDN190312AB1", "simulador", "ACUSACION"),
        ("RCP170815EF4", "reciproco", "DEFENDIBLE"),
    ]
    print(f"{'RFC':<15}{'tipo esperado':<15}{'esperado':<14}{'obtenido':<14}{'OK?'}")
    print("-" * 65)
    for rfc, tipo, esperado in proveedores:
        res = investigar(rfc)
        obtenido = res[0]["veredicto"]
        ok = "OK" if obtenido == esperado else "MISMATCH"
        print(f"{rfc:<15}{tipo:<15}{esperado:<14}{obtenido:<14}{ok}")
        if tipo == "simulador":
            r = res[0]["rastreo"]
            print(f"   -> retorno {r['pct_retorno']}% en {r['dias']} días, "
                  f"{r['saltos']} saltos, cuenta {r['cuenta_destino']}, "
                  f"vínculo: {r['tipo_vinculo']}")
