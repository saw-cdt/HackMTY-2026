"""
Las 8 herramientas del agente (seccion 4 de arquitectura), SQL puro sobre
el estate SQLite. Cada una devuelve DATOS, nunca un juicio: nada de
campos "sospechoso" o "riesgo". La interpretacion es trabajo del agente
(investigador/retador/validador), no de estas funciones.

Todas reciben `conn` (de db.connect()) como primer argumento -- el
llamador abre UNA conexion y la reutiliza en toda la investigacion, en
vez de reabrir el archivo en cada llamada.

Regla dura: este modulo (y todo tools/) nunca importa nada de generate/
ni lee la respuesta correcta (el truth.json aparte). Solo consulta el
estate que recibe.
"""
import detectors
from db import company_clabes


def prioritized_candidates(conn, max_hops=4):
    """Detectores deterministas, sin modelo. Orden estable: por señal y
    desempate por rfc, para que la misma corrida investigue en el mismo
    orden cada vez."""
    candidatos = []
    candidatos += detectors.detect_phantom_vendor(conn)
    candidatos += detectors.detect_kickback(conn)
    candidatos += detectors.detect_round_tripping(conn, max_hops=max_hops)
    candidatos += detectors.detect_threshold_splitting(conn)
    candidatos += detectors.detect_revenue_inflation(conn)
    candidatos.sort(key=lambda c: (c["signal"], c["rfc"]))
    return candidatos


def vendor(conn, rfc):
    """Fila de vendors mas su estatus en efos_list (si aparece)."""
    row = conn.execute("SELECT * FROM vendors WHERE rfc = ?", (rfc,)).fetchone()
    if row is None:
        return None
    efos = conn.execute(
        "SELECT status, publication_date FROM efos_list WHERE rfc = ?", (rfc,)
    ).fetchone()
    data = dict(row)
    data["efos_status"] = efos["status"] if efos else None
    data["efos_publication_date"] = efos["publication_date"] if efos else None
    return data


def invoices_by(conn, rfc, role):
    """role = issuer | receiver."""
    if role not in ("issuer", "receiver"):
        raise ValueError(f"role debe ser 'issuer' o 'receiver', no {role!r}")
    column = "issuer_rfc" if role == "issuer" else "receiver_rfc"
    rows = conn.execute(
        f"SELECT * FROM invoices WHERE {column} = ? ORDER BY issue_date", (rfc,)
    ).fetchall()
    return [dict(r) for r in rows]


def support_for(conn, rfc):
    """contracts y purchase_orders de ese proveedor."""
    contracts = conn.execute(
        "SELECT * FROM contracts WHERE vendor_rfc = ? ORDER BY start_date", (rfc,)
    ).fetchall()
    pos = conn.execute(
        "SELECT * FROM purchase_orders WHERE vendor_rfc = ? ORDER BY date", (rfc,)
    ).fetchall()
    return {
        "contracts": [dict(r) for r in contracts],
        "purchase_orders": [dict(r) for r in pos],
    }


def trace_money(conn, clabe, max_hops=4):
    """WITH RECURSIVE sobre bank_txns desde `clabe`. Devuelve la ruta, el
    monto que vuelve (si el ultimo salto regresa a `clabe`), y el CLABE
    destino.

    Cada salto exige b.date >= el salto anterior: el dinero no puede
    moverse antes de haber llegado. Si desde una CLABE salen varias
    transferencias validas en el mismo salto, sigue la de fecha mas
    temprana (desempate por txn_id) -- es la continuacion mas plausible
    del dinero que acaba de llegar, y es determinista: la misma consulta
    da el mismo resultado siempre.
    Si `clabe` tiene mucho fan-out (como la propia empresa pagando a
    decenas de proveedores), esta funcion sigue UNA sola rama; para
    encontrar ciclos hay que llamarla desde la CLABE del proveedor
    puntual que se esta investigando, no desde la de la empresa."""
    query = """
        WITH RECURSIVE ruta(txn_id, from_clabe, to_clabe, amount, date, hop) AS (
            SELECT txn_id, from_clabe, to_clabe, amount, date, 1
            FROM bank_txns WHERE from_clabe = :clabe
            UNION ALL
            SELECT b.txn_id, b.from_clabe, b.to_clabe, b.amount, b.date, r.hop + 1
            FROM bank_txns b JOIN ruta r ON b.from_clabe = r.to_clabe
            WHERE r.hop < :max_hops AND b.date >= r.date
        )
        SELECT * FROM ruta ORDER BY hop, date, txn_id
    """
    filas = [dict(r) for r in conn.execute(query, {"clabe": clabe, "max_hops": max_hops}).fetchall()]

    ruta = []
    clabe_actual = clabe
    for salto in range(1, max_hops + 1):
        candidatos = [f for f in filas if f["hop"] == salto and f["from_clabe"] == clabe_actual]
        if not candidatos:
            break
        paso = candidatos[0]
        ruta.append(paso)
        clabe_actual = paso["to_clabe"]

    regresa_al_origen = bool(ruta) and clabe_actual == clabe
    return {
        "clabe_origen": clabe,
        "ruta": ruta,
        "saltos": len(ruta),
        "clabe_destino": clabe_actual,
        "regresa_al_origen": regresa_al_origen,
        "monto_que_vuelve": ruta[-1]["amount"] if regresa_al_origen else None,
    }


def whose_clabe(conn, clabe):
    """A quien pertenece: vendors, employees o la empresa (por
    eliminacion). CLABE completo, nunca por prefijo -- dos personas en el
    mismo banco no estan vinculadas."""
    row = conn.execute(
        "SELECT rfc, legal_name FROM vendors WHERE bank_clabe = ?", (clabe,)
    ).fetchone()
    if row:
        return {"tipo": "vendor", "rfc": row["rfc"], "nombre": row["legal_name"]}

    row = conn.execute(
        "SELECT emp_id, name FROM employees WHERE bank_clabe = ?", (clabe,)
    ).fetchone()
    if row:
        return {"tipo": "employee", "emp_id": row["emp_id"], "nombre": row["name"]}

    if clabe in company_clabes(conn):
        return {"tipo": "empresa", "clabe": clabe}

    return {"tipo": "desconocido", "clabe": clabe}


def reciprocity(conn, rfc_a, rfc_b):
    """¿Hay CFDI en sentido contrario entre estos dos RFC? Folios y
    montos en ambos sentidos; cada factura ya trae su propio
    issuer_rfc/receiver_rfc, asi que el sentido es explicito por fila."""
    rows = conn.execute("""
        SELECT * FROM invoices
        WHERE (issuer_rfc = ? AND receiver_rfc = ?)
           OR (issuer_rfc = ? AND receiver_rfc = ?)
        ORDER BY issue_date
    """, (rfc_a, rfc_b, rfc_b, rfc_a)).fetchall()
    return {"rfc_a": rfc_a, "rfc_b": rfc_b, "invoices": [dict(r) for r in rows]}


def ledger_for(conn, uuid):
    """Asientos contables de esa factura."""
    rows = conn.execute(
        "SELECT * FROM ledger WHERE invoice_uuid = ? ORDER BY entry_id", (uuid,)
    ).fetchall()
    return [dict(r) for r in rows]
