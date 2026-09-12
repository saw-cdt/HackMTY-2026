"""
Data estate prototype para The Forensic Auditor.

Usa SQLite en vez de Postgres para que cualquiera lo corra sin instalar
nada (python3 generate_data.py). El esquema es el mismo contrato de
schema.sql, adaptado a tipos de SQLite. Migrar a Postgres real es
correr schema.sql y volver a insertar (o portar este loader).

Siembra la empresa investigada + los 4 tipos de proveedor obligatorios:
  1. Legítimo    -> se espera DEFENDIBLE
  2. Desordenado -> se espera CORREGIR
  3. Simulador   -> se espera ACUSACION
  4. Recíproco   -> se espera DEFENDIBLE
"""
import sqlite3
import uuid
from datetime import date

DB_PATH = "forensic_auditor.db"

SCHEMA = """
CREATE TABLE proveedor (
    rfc TEXT PRIMARY KEY, nombre TEXT, giro TEXT,
    fecha_alta TEXT, es_cliente_tambien INTEGER DEFAULT 0
);
CREATE TABLE cfdi (
    uuid TEXT PRIMARY KEY, fecha TEXT, fecha_timbrado TEXT,
    rfc_emisor TEXT, rfc_receptor TEXT, tipo_comprobante TEXT,
    forma_pago TEXT, metodo_pago TEXT, uso_cfdi TEXT,
    subtotal REAL, total REAL, moneda TEXT DEFAULT 'MXN'
);
CREATE TABLE soporte_documental (
    id INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT, tipo TEXT,
    fecha TEXT, referencia TEXT, monto_amparado REAL
);
CREATE TABLE ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT, periodo TEXT,
    cuenta_contable TEXT, monto_deducido REAL, iva_acreditado REAL
);
CREATE TABLE cuenta (
    acct_id TEXT PRIMARY KEY, rfc TEXT, banco TEXT,
    titular_tipo TEXT, vinculo_con TEXT, tipo_vinculo TEXT DEFAULT 'ninguno'
);
CREATE TABLE cfdi_pago (
    id INTEGER PRIMARY KEY AUTOINCREMENT, uuid_factura TEXT,
    fecha_pago TEXT, monto REAL, forma_pago TEXT, tran_id TEXT
);
CREATE TABLE transaccion (
    tran_id TEXT PRIMARY KEY, orig_acct TEXT, bene_acct TEXT,
    monto REAL, fecha TEXT
);
CREATE TABLE efos_evento (
    id INTEGER PRIMARY KEY AUTOINCREMENT, rfc TEXT, etapa TEXT,
    fecha_dof TEXT, fecha_portal TEXT, oficio TEXT
);
CREATE TABLE gt_escenario (
    id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT,
    rfc_proveedor TEXT, uuids TEXT, acct_ids TEXT
);
"""

EMPRESA_RFC = "MNO900101AB1"


def new_uuid():
    return str(uuid.uuid4())


def build():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    cur = conn.cursor()

    def add_proveedor(rfc, nombre, giro, es_cliente=False):
        cur.execute(
            "INSERT INTO proveedor VALUES (?,?,?,?,?)",
            (rfc, nombre, giro, "2015-01-01", int(es_cliente)),
        )

    def add_cuenta(acct_id, rfc, banco, titular_tipo, vinculo_con=None, tipo_vinculo="ninguno"):
        cur.execute(
            "INSERT INTO cuenta VALUES (?,?,?,?,?,?)",
            (acct_id, rfc, banco, titular_tipo, vinculo_con, tipo_vinculo),
        )

    def add_cfdi(rfc_emisor, fecha, total, rfc_receptor=EMPRESA_RFC):
        u = new_uuid()
        cur.execute(
            "INSERT INTO cfdi VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (u, fecha, fecha + "T10:00:00", rfc_emisor, rfc_receptor,
             "I", "03", "PPD", "G03", total, total, "MXN"),
        )
        return u

    def add_soporte(u, tipo, fecha, monto_amparado):
        cur.execute(
            "INSERT INTO soporte_documental (uuid, tipo, fecha, referencia, monto_amparado) "
            "VALUES (?,?,?,?,?)",
            (u, tipo, fecha, f"{tipo.upper()}-{u[:8]}", monto_amparado),
        )

    def add_efos(rfc, etapa, fecha_dof, oficio):
        cur.execute(
            "INSERT INTO efos_evento (rfc, etapa, fecha_dof, fecha_portal, oficio) "
            "VALUES (?,?,?,?,?)",
            (rfc, etapa, fecha_dof, fecha_dof, oficio),
        )

    def add_pago_y_transaccion(u, fecha_pago, monto, orig_acct, bene_acct):
        tran_id = "T" + new_uuid()[:12]
        cur.execute(
            "INSERT INTO transaccion VALUES (?,?,?,?,?)",
            (tran_id, orig_acct, bene_acct, monto, fecha_pago),
        )
        cur.execute(
            "INSERT INTO cfdi_pago (uuid_factura, fecha_pago, monto, forma_pago, tran_id) "
            "VALUES (?,?,?,?,?)",
            (u, fecha_pago, monto, "03", tran_id),
        )
        return tran_id

    # cuenta de la empresa investigada (paga a todos los proveedores)
    add_cuenta("ACC-EMPRESA", EMPRESA_RFC, "BBVA", "moral")

    # ------------------------------------------------------------
    # 1) LEGÍTIMO — contrato + orden_compra + entrega, pago único, sin retorno
    # ------------------------------------------------------------
    rfc1 = "SIB150304CD2"
    add_proveedor(rfc1, "SERVICIOS INTEGRALES BAJIO SA", "Servicios de mantenimiento")
    add_cuenta("ACC-SIB-01", rfc1, "Santander", "moral")
    u1 = add_cfdi(rfc1, "2024-02-10", 500000.00)
    add_soporte(u1, "contrato", "2024-01-15", 500000.00)
    add_soporte(u1, "orden_compra", "2024-01-20", 500000.00)
    add_soporte(u1, "entrega", "2024-02-08", 500000.00)
    add_pago_y_transaccion(u1, "2024-02-15", 500000.00, "ACC-EMPRESA", "ACC-SIB-01")
    cur.execute("INSERT INTO gt_escenario (tipo, rfc_proveedor, uuids, acct_ids) VALUES (?,?,?,?)",
                ("legitimo", rfc1, u1, "ACC-SIB-01"))

    # ------------------------------------------------------------
    # 2) DESORDENADO — sin contrato, con entrega, pago único, sin retorno.
    #    Estatus definitivo, pero DESPUÉS de la fecha de la factura
    #    (estaba limpio cuando facturó).
    # ------------------------------------------------------------
    rfc2 = "TRE180422XY3"
    add_proveedor(rfc2, "TRANSPORTES DEL RIO SA", "Logística y transporte")
    add_cuenta("ACC-TRE-01", rfc2, "Banorte", "moral")
    u2 = add_cfdi(rfc2, "2024-03-15", 800000.00)
    add_soporte(u2, "entrega", "2024-03-20", 800000.00)  # sin contrato ni orden_compra
    add_pago_y_transaccion(u2, "2024-03-25", 800000.00, "ACC-EMPRESA", "ACC-TRE-01")
    add_efos(rfc2, "definitivo", "2025-08-20", "500-05-2025-XXXXX")  # posterior a la factura
    cur.execute("INSERT INTO gt_escenario (tipo, rfc_proveedor, uuids, acct_ids) VALUES (?,?,?,?)",
                ("desordenado", rfc2, u2, "ACC-TRE-01"))

    # ------------------------------------------------------------
    # 3) SIMULADOR — sin contrato ni entrega, retorno 92.9% en 12 días
    #    a una cuenta del socio mayoritario. Ya estaba en definitivo
    #    cuando facturó.
    # ------------------------------------------------------------
    rfc3 = "CDN190312AB1"
    add_proveedor(rfc3, "CONSULTORES DEL NORTE SA", "Consultoría")
    add_cuenta("ACC-CDN-01", rfc3, "Banregio", "moral")
    add_cuenta("ACC-SOCIO-01", rfc3, "Banregio", "fisica",
               vinculo_con=EMPRESA_RFC, tipo_vinculo="socio")
    u3 = add_cfdi(rfc3, "2024-04-02", 2400000.00)
    add_efos(rfc3, "definitivo", "2024-01-10", "500-05-2024-YYYYY")  # ANTES de facturar
    add_pago_y_transaccion(u3, "2024-04-05", 2400000.00, "ACC-EMPRESA", "ACC-CDN-01")
    # dispersión en saltos hasta la cuenta del socio, 92.9% de retorno
    cur.execute("INSERT INTO transaccion VALUES (?,?,?,?,?)",
                ("T-HOP-1", "ACC-CDN-01", "ACC-INT-1", 2300000.00, "2024-04-08"))
    add_cuenta("ACC-INT-1", "SHELL1RFC001", "Otro banco", "moral")
    cur.execute("INSERT INTO transaccion VALUES (?,?,?,?,?)",
                ("T-HOP-2", "ACC-INT-1", "ACC-INT-2", 2280000.00, "2024-04-11"))
    add_cuenta("ACC-INT-2", "SHELL2RFC002", "Otro banco", "moral")
    cur.execute("INSERT INTO transaccion VALUES (?,?,?,?,?)",
                ("T-HOP-3", "ACC-INT-2", "ACC-SOCIO-01", 2229600.00, "2024-04-17"))  # ~92.9%
    cur.execute("INSERT INTO gt_escenario (tipo, rfc_proveedor, uuids, acct_ids) VALUES (?,?,?,?)",
                ("simulador", rfc3, u3, "ACC-CDN-01,ACC-SOCIO-01"))

    # ------------------------------------------------------------
    # 4) RECÍPROCO — proveedor también es cliente. Dinero vuelve,
    #    pero con factura propia en sentido contrario, a cuenta moral.
    # ------------------------------------------------------------
    rfc4 = "RCP170815EF4"
    add_proveedor(rfc4, "GRUPO RECIPROCO SA", "Comercializadora", es_cliente=True)
    add_cuenta("ACC-RCP-01", rfc4, "HSBC", "moral")
    u4 = add_cfdi(rfc4, "2024-05-01", 2400000.00)
    add_soporte(u4, "contrato", "2024-04-20", 2400000.00)
    add_soporte(u4, "entrega", "2024-05-05", 2400000.00)
    add_pago_y_transaccion(u4, "2024-05-10", 2400000.00, "ACC-EMPRESA", "ACC-RCP-01")
    # factura recíproca: el proveedor le compra a la empresa y paga de vuelta
    u4b = add_cfdi(EMPRESA_RFC, "2024-05-20", 2200000.00, rfc_receptor=rfc4)
    add_pago_y_transaccion(u4b, "2024-05-25", 2200000.00, "ACC-RCP-01", "ACC-EMPRESA")
    cur.execute("INSERT INTO gt_escenario (tipo, rfc_proveedor, uuids, acct_ids) VALUES (?,?,?,?)",
                ("reciproco", rfc4, f"{u4},{u4b}", "ACC-RCP-01"))

    conn.commit()
    conn.close()
    print(f"OK -> {DB_PATH} creado con la empresa {EMPRESA_RFC} y 4 proveedores sembrados:")
    print(f"  {rfc1}  legitimo    (esperado: DEFENDIBLE)")
    print(f"  {rfc2}  desordenado (esperado: CORREGIR)")
    print(f"  {rfc3}  simulador   (esperado: ACUSACION)")
    print(f"  {rfc4}  reciproco   (esperado: DEFENDIBLE)")


if __name__ == "__main__":
    build()
