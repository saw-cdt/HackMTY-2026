-- The Forensic Auditor — contrato de datos (congelado en H+4)
-- Postgres. Para migrar a Tiger Data solo cambia la connection string
-- y corre este script allá (ver nota de hypertable al final).

-- ============================================================
-- Generadas por nosotros
-- ============================================================

CREATE TABLE proveedor (
    rfc                 VARCHAR(13) PRIMARY KEY,
    nombre              TEXT NOT NULL,
    giro                TEXT,
    fecha_alta          DATE,
    es_cliente_tambien  BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE cfdi (
    uuid            UUID PRIMARY KEY,
    fecha           DATE NOT NULL,
    fecha_timbrado  TIMESTAMP,
    rfc_emisor      VARCHAR(13) NOT NULL REFERENCES proveedor(rfc),
    rfc_receptor    VARCHAR(13) NOT NULL,
    tipo_comprobante VARCHAR(1),   -- I=ingreso, E=egreso, etc.
    forma_pago      VARCHAR(2),
    metodo_pago     VARCHAR(3),
    uso_cfdi        VARCHAR(4),
    subtotal        NUMERIC(14,2) NOT NULL,
    total           NUMERIC(14,2) NOT NULL,
    moneda          VARCHAR(3) DEFAULT 'MXN'
);

CREATE TABLE cfdi_concepto (
    id              SERIAL PRIMARY KEY,
    uuid            UUID NOT NULL REFERENCES cfdi(uuid),
    clave_prod_serv VARCHAR(8),
    cantidad        NUMERIC(12,4),
    descripcion     TEXT,
    valor_unitario  NUMERIC(14,2),
    importe         NUMERIC(14,2)
);

CREATE TABLE soporte_documental (
    id              SERIAL PRIMARY KEY,
    uuid            UUID NOT NULL REFERENCES cfdi(uuid),
    tipo            VARCHAR(20) NOT NULL,  -- contrato | orden_compra | entrega
    fecha           DATE,
    referencia      TEXT,
    monto_amparado  NUMERIC(14,2)
);

CREATE TABLE ledger (
    id              SERIAL PRIMARY KEY,
    uuid            UUID NOT NULL REFERENCES cfdi(uuid),
    periodo         VARCHAR(7),   -- 'YYYY-MM'
    cuenta_contable VARCHAR(20),
    monto_deducido  NUMERIC(14,2),
    iva_acreditado  NUMERIC(14,2)
);

-- ============================================================
-- El puente factura <-> banco
-- ============================================================

CREATE TABLE cuenta (
    acct_id         VARCHAR(20) PRIMARY KEY,
    rfc             VARCHAR(13) NOT NULL,
    banco           TEXT,
    titular_tipo    VARCHAR(10) NOT NULL,  -- fisica | moral
    vinculo_con     VARCHAR(13),           -- rfc de la empresa investigada, si aplica
    tipo_vinculo    VARCHAR(15) DEFAULT 'ninguno'  -- socio | directivo | filial | ninguno
);

CREATE TABLE cfdi_pago (
    id              SERIAL PRIMARY KEY,
    uuid_factura    UUID NOT NULL REFERENCES cfdi(uuid),
    fecha_pago      DATE,
    monto           NUMERIC(14,2),
    forma_pago      VARCHAR(2),
    tran_id         VARCHAR(20)  -- FK logico a transaccion.tran_id (de AMLSim)
);

-- ============================================================
-- De AMLSim (normalizado en la carga)
-- ============================================================

CREATE TABLE transaccion (
    tran_id     VARCHAR(20) PRIMARY KEY,
    orig_acct   VARCHAR(20) NOT NULL REFERENCES cuenta(acct_id),
    bene_acct   VARCHAR(20) NOT NULL REFERENCES cuenta(acct_id),
    monto       NUMERIC(14,2) NOT NULL,
    fecha       DATE NOT NULL
);

-- ============================================================
-- Del SAT
-- ============================================================

CREATE TABLE efos_evento (
    id          SERIAL PRIMARY KEY,
    rfc         VARCHAR(13) NOT NULL,
    etapa       VARCHAR(20) NOT NULL,  -- presunto|definitivo|desvirtuado|sentencia_favorable
    fecha_dof   DATE,
    fecha_portal DATE,
    oficio      TEXT
);

-- ============================================================
-- Fuera del alcance del agente — en la práctica: otro esquema /
-- rol de Postgres sin permiso de SELECT para el usuario del agente.
-- ============================================================

CREATE TABLE gt_escenario (
    id              SERIAL PRIMARY KEY,
    tipo            VARCHAR(20) NOT NULL,  -- legitimo|desordenado|simulador|reciproco
    rfc_proveedor   VARCHAR(13) NOT NULL,
    uuids           UUID[],
    acct_ids        VARCHAR(20)[]
);

-- ============================================================
-- Índices (no opcionales con 60s de presupuesto)
-- ============================================================

CREATE INDEX ON cfdi(rfc_emisor, fecha);
CREATE INDEX ON cfdi(rfc_receptor, fecha);
CREATE INDEX ON transaccion(orig_acct, fecha);
CREATE INDEX ON transaccion(bene_acct, fecha);
CREATE INDEX ON efos_evento(rfc, etapa);
CREATE INDEX ON soporte_documental(uuid);
CREATE INDEX ON cfdi_pago(uuid_factura);

-- Migración a Tiger Data: correr este mismo script sin cambios.
-- Después, convertir `transaccion` a hypertable y agregar
-- continuous aggregates (aditivo, no rediseño).
