"""
Conexion al estate + los dos "por eliminacion" que hacen falta porque el
schema oficial no tiene tabla de empresa ni de cuentas: vendors y
employees son las unicas dos listas de CLABE, asi que cualquier CLABE (o
RFC) que no aparezca en ninguna de las dos tiene que ser de la empresa
investigada.

Este modulo (y el resto de tools/) NUNCA importa nada de generate/ ni
lee la respuesta correcta (el truth.json aparte): solo consulta el
estate.db que recibe.
"""
import sqlite3


def connect(db_path):
    """Abre el estate con row_factory = sqlite3.Row, que el resto de
    tools/ asume para poder hacer dict(row)."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def company_clabes(conn):
    """CLABEs que no pertenecen a ningun vendor ni employee: por
    eliminacion, son de la empresa investigada (puede tener mas de una
    cuenta bancaria, igual que un proveedor)."""
    rows = conn.execute("""
        SELECT DISTINCT clabe FROM (
            SELECT from_clabe AS clabe FROM bank_txns
            UNION
            SELECT to_clabe AS clabe FROM bank_txns
        )
        WHERE clabe NOT IN (SELECT bank_clabe FROM vendors WHERE bank_clabe IS NOT NULL)
          AND clabe NOT IN (SELECT bank_clabe FROM employees WHERE bank_clabe IS NOT NULL)
    """).fetchall()
    return {r["clabe"] for r in rows}


def company_rfc(conn):
    """El RFC que aparece como emisor o receptor en invoices pero nunca
    como proveedor: por eliminacion, es la empresa investigada. Regresa
    None si el estate no tiene exactamente un candidato (ambiguo o vacio),
    en vez de adivinar."""
    rows = conn.execute("""
        SELECT DISTINCT rfc FROM (
            SELECT issuer_rfc AS rfc FROM invoices
            UNION
            SELECT receiver_rfc AS rfc FROM invoices
        )
        WHERE rfc NOT IN (SELECT rfc FROM vendors)
    """).fetchall()
    rfcs = {r["rfc"] for r in rows}
    return next(iter(rfcs)) if len(rfcs) == 1 else None
