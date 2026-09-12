"""
Ingesta del listado 69-B del SAT hacia la tabla efos_evento.

FORMATO REAL DEL SAT (verificado por investigación, no por descarga directa
porque el portal listados.sat.gob.mx sirve el CSV vía JS y no expone una
URL estable): una fila por RFC, columnas anchas — una por cada etapa
(presunción, definitivos, desvirtuados, sentencia favorable) — y cada
celda mezcla el número de oficio y la fecha en el mismo texto, ej.:

    "500-05-2025-36065 20/02/2026"

Esto confirma lo que dice el doc de arquitectura: hay que "pivotear" el
CSV ancho hacia la tabla larga efos_evento (una fila por EVENTO, no por
contribuyente), y cada celda necesita separarse en oficio + fecha con
regex antes de insertar.

ADVERTENCIA para quien reemplace el CSV de muestra por el real:
- El SAT publica 5 archivos separados (Presuntos, Definitivos,
  Desvirtuados, Sentencias Favorables, Listado completo) — usa el de
  "Listado completo" si quieres las 4 etapas en un solo archivo.
- Verificar encoding: los CSV del gobierno mexicano frecuentemente vienen
  en latin-1 / windows-1252, no UTF-8 (acentos rotos si se asume UTF-8).
  Este parser intenta UTF-8 primero y cae a latin-1.
- Verificar que los nombres de columna coincidan exactamente (pueden
  cambiar mayúsculas/acentos entre actualizaciones del SAT) — por eso
  aquí se normalizan antes de mapear.
"""
import csv
import re
import sqlite3
import unicodedata

DB_PATH = "forensic_auditor.db"

# etapa interna -> fragmento de columna que la identifica (normalizado)
ETAPA_MAP = {
    "presuncion": "presunto",
    "definitivos": "definitivo",
    "desvirtuados": "desvirtuado",
    "sentencia favorable": "sentencia_favorable",
}

FECHA_RE = re.compile(r"(\d{1,2}/\d{1,2}/\d{4})")


def _normalizar(texto):
    """minúsculas, sin acentos, espacios colapsados — para matchear headers
    aunque el SAT cambie mayúsculas o acentos entre publicaciones."""
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", texto.strip().lower())


def _leer_csv_con_encoding(path):
    """El SAT no siempre publica en UTF-8. Intentar UTF-8, caer a latin-1."""
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            with open(path, encoding=encoding) as f:
                rows = list(csv.DictReader(f))
            return rows, encoding
        except UnicodeDecodeError:
            continue
    raise ValueError(f"No se pudo decodificar {path} con utf-8 ni latin-1")


def _mapear_columnas(fieldnames):
    """Encuentra, para cada etapa, la columna de oficio+fecha correspondiente,
    sin depender de coincidencia exacta de texto (mayúsculas/acentos)."""
    normalizados = {c: _normalizar(c) for c in fieldnames}
    mapa = {}
    for etapa_col, etapa_interna in ETAPA_MAP.items():
        candidatos = [
            original for original, norm in normalizados.items()
            if etapa_col in norm and "dof" in norm  # preferimos la fecha DOF sobre la SAT
        ]
        if not candidatos:
            # si no hay columna DOF, usar la de SAT
            candidatos = [
                original for original, norm in normalizados.items()
                if etapa_col in norm
            ]
        if candidatos:
            mapa[etapa_interna] = candidatos[0]
    return mapa


def parse_oficio_fecha(celda):
    """No asumimos nada sobre el formato del número de oficio (el SAT ha
    usado placeholders y variantes alfanuméricas) — anclamos en la FECHA,
    que sí tiene un formato fijo, y tomamos todo lo anterior como oficio."""
    if not celda or not celda.strip():
        return None, None
    m = FECHA_RE.search(celda)
    if not m:
        return None, None
    oficio = celda[: m.start()].strip()
    if not oficio:
        return None, None
    d, mo, y = m.group(1).split("/")
    fecha_iso = f"{y}-{int(mo):02d}-{int(d):02d}"
    return oficio, fecha_iso


def ingerir_69b(csv_path, db_path=DB_PATH, verbose=True):
    rows, encoding = _leer_csv_con_encoding(csv_path)
    if not rows:
        print("Archivo vacío o sin filas.")
        return 0

    if verbose:
        print(f"Leído con encoding={encoding}. Columnas detectadas:")
        for c in rows[0].keys():
            print(f"  - {c}")

    columna_por_etapa = _mapear_columnas(rows[0].keys())
    if verbose:
        print(f"\nMapeo etapa -> columna: {columna_por_etapa}\n")

    conn = sqlite3.connect(db_path)
    conn.execute("""CREATE TABLE IF NOT EXISTS efos_evento (
        id INTEGER PRIMARY KEY AUTOINCREMENT, rfc TEXT, etapa TEXT,
        fecha_dof TEXT, fecha_portal TEXT, oficio TEXT)""")
    cur = conn.cursor()

    insertados = 0
    for fila in rows:
        rfc = fila.get("RFC", "").strip()
        if not rfc:
            continue
        for etapa_interna, col in columna_por_etapa.items():
            oficio, fecha = parse_oficio_fecha(fila.get(col, ""))
            if oficio and fecha:
                cur.execute(
                    "INSERT INTO efos_evento (rfc, etapa, fecha_dof, fecha_portal, oficio) "
                    "VALUES (?,?,?,?,?)",
                    (rfc, etapa_interna, fecha, fecha, oficio),
                )
                insertados += 1

    conn.commit()
    conn.close()
    if verbose:
        print(f"OK -> {insertados} eventos insertados en efos_evento (tabla larga)")
    return insertados


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "sample_69b.csv"
    ingerir_69b(path)
