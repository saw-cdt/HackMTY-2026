"""
Un detector determinista por tipo de esquema. Sin modelo, sin umbrales
mágicos: cada uno es una consulta (o una consulta + un recorrido simple
en Python cuando SQL puro no alcanza) contra el estate.

Cada detector regresa una lista de candidatos: dicts con al menos `rfc` y
`signal` (el nombre del propio detector, texto plano). Ese `signal` es
justo lo que despues va al campo "signal" de leads_not_pursued -- por eso
son datos ("estas facturas caen bajo el umbral"), nunca juicios ("esto es
fraude").

Nunca importa nada de generate/. Nunca lee la respuesta correcta (el
truth.json aparte).
"""
import datetime as dt
import math

from db import company_clabes, company_rfc

MIN_SPLIT_COUNT = 3
SPLIT_WINDOW_DAYS = 15


# ---------------------------------------------------------------------
# phantom_vendor: cruce con efos_list + ausencia de contracts y OC
# ---------------------------------------------------------------------
def detect_phantom_vendor(conn):
    rows = conn.execute("""
        SELECT v.rfc
        FROM vendors v
        JOIN efos_list e ON e.rfc = v.rfc
        WHERE NOT EXISTS (SELECT 1 FROM contracts c WHERE c.vendor_rfc = v.rfc)
          AND NOT EXISTS (SELECT 1 FROM purchase_orders p WHERE p.vendor_rfc = v.rfc)
    """).fetchall()
    return [
        {"rfc": r["rfc"], "signal": "phantom_vendor_efos_sin_contrato_ni_oc"}
        for r in rows
    ]


# ---------------------------------------------------------------------
# kickback: bank_txns cuyo to_clabe aparece en employees, pagadas por
# un CLABE que es de un proveedor conocido.
# ---------------------------------------------------------------------
def detect_kickback(conn):
    rows = conn.execute("""
        SELECT DISTINCT v.rfc, e.emp_id, b.txn_id, b.amount, b.date
        FROM bank_txns b
        JOIN employees e ON e.bank_clabe = b.to_clabe
        JOIN vendors v ON v.bank_clabe = b.from_clabe
    """).fetchall()
    return [
        {
            "rfc": r["rfc"],
            "signal": "kickback_transferencia_a_empleado",
            "emp_id": r["emp_id"],
            "txn_id": r["txn_id"],
            "monto": r["amount"],
            "fecha": r["date"],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------
# round_tripping: recorrido recursivo desde cada CLABE de la empresa que
# cierra el ciclo de vuelta en una CLABE de la empresa.
# ---------------------------------------------------------------------
def _reachable_edges(conn, origin_clabes, max_hops):
    """Aristas alcanzables desde `origin_clabes` en hasta max_hops saltos.
    a.date <= b.date obliga causalidad: el dinero no puede moverse antes
    de haber llegado (sin este filtro, una transferencia vieja sin
    relacion podia colarse como "siguiente salto" solo por compartir
    CLABE)."""
    if not origin_clabes:
        return []
    values_sql = ",".join("(?)" for _ in origin_clabes)
    query = f"""
        WITH RECURSIVE origenes(clabe) AS (VALUES {values_sql}),
        alcance(txn_id, from_clabe, to_clabe, amount, date, hop) AS (
            SELECT b.txn_id, b.from_clabe, b.to_clabe, b.amount, b.date, 1
            FROM bank_txns b JOIN origenes o ON o.clabe = b.from_clabe
            UNION ALL
            SELECT b.txn_id, b.from_clabe, b.to_clabe, b.amount, b.date, a.hop + 1
            FROM bank_txns b JOIN alcance a ON b.from_clabe = a.to_clabe
            WHERE a.hop < ? AND b.date >= a.date
        )
        SELECT * FROM alcance
    """
    rows = conn.execute(query, [*origin_clabes, max_hops]).fetchall()
    return [dict(r) for r in rows]


def detect_round_tripping(conn, max_hops=4):
    empresa_clabes = company_clabes(conn)
    if not empresa_clabes:
        return []

    edges = _reachable_edges(conn, empresa_clabes, max_hops)
    by_from = {}
    for e in edges:
        by_from.setdefault(e["from_clabe"], []).append(e)

    vendor_by_clabe = {
        r["bank_clabe"]: r["rfc"]
        for r in conn.execute(
            "SELECT rfc, bank_clabe FROM vendors WHERE bank_clabe IS NOT NULL"
        ).fetchall()
    }

    edge_by_txn = {e["txn_id"]: e for e in edges}
    candidatos = []
    ciclos_vistos = set()

    def dfs(clabe_actual, camino_clabes, camino_txns):
        if len(camino_txns) >= max_hops:
            return
        for edge in by_from.get(clabe_actual, []):
            if edge["txn_id"] in camino_txns:
                continue
            siguiente = edge["to_clabe"]
            ruta_txns = camino_txns + [edge["txn_id"]]
            if siguiente in empresa_clabes and len(ruta_txns) > 1:
                rfcs_intermedios = [
                    vendor_by_clabe[c] for c in camino_clabes[1:] if c in vendor_by_clabe
                ]
                key = tuple(ruta_txns)
                if rfcs_intermedios and key not in ciclos_vistos:
                    ciclos_vistos.add(key)
                    # la ruta completa (montos, fechas, clabes) va en cada
                    # candidato: el investigador no tiene forma de pedir
                    # "dame el bank_txn X" con las 8 herramientas, asi que
                    # se la damos de una vez.
                    ruta = [edge_by_txn[t] for t in ruta_txns]
                    for rfc in rfcs_intermedios:
                        candidatos.append({
                            "rfc": rfc,
                            "signal": "round_tripping_ciclo_a_empresa",
                            "txn_ids": ruta_txns,
                            "ruta": ruta,
                            "saltos": len(ruta_txns),
                        })
            else:
                dfs(siguiente, camino_clabes + [siguiente], ruta_txns)

    for origen in empresa_clabes:
        dfs(origen, [origen], [])

    return candidatos


# ---------------------------------------------------------------------
# threshold_splitting: agrupar por proveedor y ventana de fechas contra
# el limite inferido de purchase_orders (nunca un umbral fijo, nunca
# inventado: si ningun metodo es concluyente, None).
# ---------------------------------------------------------------------
STEP_MIN_SALTO_RATIO = 1.4    # que tan marcado debe ser el salto para confiar en el escalon
GAP_CANDIDATES = [50_000, 100_000, 250_000, 500_000]
GAP_BAND_RATIO = 0.20         # ventana +/- 20% alrededor de cada cifra redonda
GAP_MIN_RATIO = 3.0           # veces mas montos debajo que encima para que el hueco cuente
GAP_MIN_COUNT = 3             # minimo de montos "debajo" para no confiar en un punado


def infer_approval_threshold(conn):
    """Dos metodos, en ese orden. Si ninguno es concluyente, None -- y
    quien llama (detect_threshold_splitting) no corre sobre ese estate.
    Inventar un umbral produce falsas acusaciones, y eso pesa mas que
    perder un esquema.

    Metodo 1 -- escalones por approver:
        SELECT approver, MAX(amount) AS techo FROM purchase_orders
        GROUP BY approver ORDER BY techo
    Un escalon real es un salto marcado entre techos ordenados, no una
    progresion suave (con pocas personas por nivel, una puede tener
    mala suerte y no acercarse a su propio techo, asi que el minimo
    absoluto no sirve -- hay que encontrar el salto). Si el salto mas
    grande no supera STEP_MIN_SALTO_RATIO, no hay escalones claros.

    Metodo 2 -- el hueco en la distribucion (respaldo): para cada cifra
    redonda candidata (50k/100k/250k/500k), cuenta montos justo debajo y
    justo encima. Acumulacion debajo + escasez encima es la firma del
    umbral. Si ningun candidato muestra un hueco claro, tambien None."""
    umbral = _infer_por_escalones(conn)
    if umbral is not None:
        return umbral
    return _infer_por_hueco(conn)


def _infer_por_escalones(conn):
    rows = conn.execute("""
        SELECT approver, MAX(amount) AS techo
        FROM purchase_orders
        GROUP BY approver
        ORDER BY techo
    """).fetchall()
    if len(rows) < 2:
        return None

    techos = [r["techo"] for r in rows]
    frontera, mejor_salto = 0, 0.0
    for i in range(1, len(techos)):
        if techos[i - 1] <= 0:
            continue
        salto = techos[i] / techos[i - 1]
        if salto > mejor_salto:
            mejor_salto, frontera = salto, i

    if mejor_salto < STEP_MIN_SALTO_RATIO:
        return None  # progresion suave: no hay escalones claros que confiar

    techo_escalon_mas_bajo = techos[frontera - 1]
    return math.ceil(techo_escalon_mas_bajo / 50_000) * 50_000


def _infer_por_hueco(conn):
    amounts = [r["amount"] for r in conn.execute("SELECT amount FROM purchase_orders").fetchall()]
    if len(amounts) < GAP_MIN_COUNT:
        return None

    mejor = None
    for candidato in GAP_CANDIDATES:
        banda = candidato * GAP_BAND_RATIO
        debajo = sum(1 for a in amounts if candidato - banda <= a < candidato)
        encima = sum(1 for a in amounts if candidato <= a < candidato + banda)
        if debajo < GAP_MIN_COUNT:
            continue
        proporcion = debajo / (encima + 1)
        if mejor is None or proporcion > mejor[1]:
            mejor = (candidato, proporcion)

    if mejor is None or mejor[1] < GAP_MIN_RATIO:
        return None
    return mejor[0]


def detect_threshold_splitting(conn, window_days=SPLIT_WINDOW_DAYS, min_count=MIN_SPLIT_COUNT):
    threshold = infer_approval_threshold(conn)
    if threshold is None:
        return []

    rows = conn.execute("""
        SELECT uuid, issuer_rfc, issue_date, total
        FROM invoices
        WHERE total < ?
        ORDER BY issuer_rfc, issue_date
    """, (threshold,)).fetchall()

    por_proveedor = {}
    for r in rows:
        por_proveedor.setdefault(r["issuer_rfc"], []).append(dict(r))

    candidatos = []
    for rfc, facturas in por_proveedor.items():
        for i, ancla in enumerate(facturas):
            fecha_ancla = dt.date.fromisoformat(ancla["issue_date"])
            grupo = [
                f for f in facturas[i:]
                if (dt.date.fromisoformat(f["issue_date"]) - fecha_ancla).days <= window_days
            ]
            if len(grupo) >= min_count:
                candidatos.append({
                    "rfc": rfc,
                    "signal": "threshold_splitting_facturas_bajo_umbral",
                    "invoice_ids": [g["uuid"] for g in grupo],
                    "umbral_inferido": threshold,
                })
                break

    return candidatos


# ---------------------------------------------------------------------
# revenue_inflation: la empresa emite (issuer_rfc = empresa) y ningun
# bank_txn del cliente hacia la empresa liquida la factura.
# ---------------------------------------------------------------------
def detect_revenue_inflation(conn):
    rfc_empresa = company_rfc(conn)
    empresa_clabes = company_clabes(conn)
    if not rfc_empresa or not empresa_clabes:
        return []

    placeholders = ",".join("?" for _ in empresa_clabes)
    rows = conn.execute(f"""
        SELECT i.uuid, i.receiver_rfc, i.total, i.issue_date
        FROM invoices i
        LEFT JOIN vendors v ON v.rfc = i.receiver_rfc
        WHERE i.issuer_rfc = ?
          AND NOT EXISTS (
              SELECT 1 FROM bank_txns b
              WHERE b.from_clabe = v.bank_clabe
                AND b.to_clabe IN ({placeholders})
          )
    """, [rfc_empresa, *empresa_clabes]).fetchall()

    return [
        {
            "rfc": rfc_empresa,
            "signal": "revenue_inflation_factura_sin_bank_txn",
            "invoice_id": r["uuid"],
            "cliente_rfc": r["receiver_rfc"],
            "monto": r["total"],
        }
        for r in rows
    ]
