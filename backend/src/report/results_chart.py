"""
Genera una imagen estatica (SVG, mas PNG via Chrome headless si esta
disponible) con el resultado agregado de una corrida de
eval/harness.py: recall global, recall por scheme_type, falsas
acusaciones y los tres numeros. Pensada para una diapositiva del pitch
y para embeberse en el resumen ejecutivo del case file (Fase 5) -- la
tabla de resultados 101-110 se queda fuera de la interfaz (frontend/),
tal como permite frontend/FRONTEND.md.

Puro codigo, sin modelo, sin librerias externas -- SVG a mano, igual
que el money trail en report/case_file.py. Lee los CSV que ya escribio
eval/harness.py (out/results_<nombre>.csv y _by_type.csv); no corre el
harness ni conoce ground_truth ni el estate.

Uso (imagen suelta para la diapositiva):
    python -m src.report.results_chart \\
        --results out/results_report.csv \\
        --by-type out/results_report_by_type.csv \\
        --out out/results_report.svg
"""
import argparse
import csv
import html
import shutil
import subprocess
import tempfile
from pathlib import Path

SCHEME_LABELS = {
    "phantom_vendor": "Proveedor fantasma",
    "kickback": "Kickback",
    "round_tripping": "Round-tripping",
    "threshold_splitting": "Fraccionamiento",
    "revenue_inflation": "Ingresos inflados",
}
_e = html.escape


def _leer_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _total_row(rows):
    for r in rows:
        if r["seed"] == "TOTAL":
            return r
    raise ValueError(f"{rows!r}: no trae una fila TOTAL")


def _fmt_pct(v):
    return f"{float(v):.1f}%"


def _fmt_money(v):
    return f"${float(v):,.2f}"


def _kpi_card(x, y, w, h, label, value, accent="#1f7a4d"):
    return f"""
<g>
  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#ffffff" stroke="#d5dbe3" stroke-width="1.5"/>
  <text x="{x + w / 2}" y="{y + 30}" text-anchor="middle" font-size="13" fill="#4a5568"
        font-family="-apple-system, 'Segoe UI', Roboto, Arial, sans-serif">{_e(label)}</text>
  <text x="{x + w / 2}" y="{y + h - 22}" text-anchor="middle" font-size="30" font-weight="700" fill="{accent}"
        font-family="-apple-system, 'Segoe UI', Roboto, Arial, sans-serif">{_e(value)}</text>
</g>"""


def build_results_svg(results_csv_path, by_type_csv_path, title="Resultado — seeds de reporte"):
    """Regresa el SVG (string, standalone) del dashboard de resultados.
    Puede embeberse tal cual dentro de otro documento HTML (case_file.py
    lo hace) o guardarse como .svg suelto."""
    rows = _leer_csv(results_csv_path)
    total = _total_row(rows)
    by_type = _leer_csv(by_type_csv_path)
    n_seeds = len(rows) - 1  # sin contar la fila TOTAL

    recall_pct = float(total["recall_pct"])
    false_acc_pct = float(total["false_accusation_rate_pct"])
    schemes_found = int(total["schemes_found"])
    schemes_planted = int(total["schemes_planted"])
    decoys_planted = int(total["decoys_planted"])
    decoys_accused = int(total["decoys_accused"])
    llm_calls_avg = float(total["llm_calls"])
    mxn_cost = float(total["mxn_cost"])
    wall_clock_avg = float(total["wall_clock_s"])
    peso_reconciles = str(total.get("peso_reconciles", "")).strip().lower() == "true"

    width = 980
    margin = 24
    card_w, card_h, gap = 176, 108, 15
    cards_y = 92
    cards = [
        ("Recall", f"{schemes_found}/{schemes_planted} ({_fmt_pct(recall_pct)})", "#1f7a4d"),
        ("Falsas acusaciones", f"{decoys_accused}/{decoys_planted} ({_fmt_pct(false_acc_pct)})",
         "#1f7a4d" if decoys_accused == 0 else "#a12626"),
        ("llm_calls (prom.)", f"{llm_calls_avg:g}", "#1a202c"),
        ("mxn_cost", _fmt_money(mxn_cost), "#1a202c"),
        ("wall_clock_s (prom.)", f"{wall_clock_avg:g}", "#1a202c"),
    ]
    cards_svg = "".join(
        _kpi_card(margin + i * (card_w + gap), cards_y, card_w, card_h, label, value, accent)
        for i, (label, value, accent) in enumerate(cards)
    )

    table_y = cards_y + card_h + 40
    row_h = 32
    col_x = [margin, margin + 380, margin + 560, margin + 740]
    header_row = f"""
<g>
  <rect x="{margin}" y="{table_y}" width="{width - 2 * margin}" height="{row_h}" fill="#f1f4f8"/>
  <text x="{col_x[0] + 12}" y="{table_y + 21}" font-size="13" font-weight="700" fill="#1a202c"
        font-family="-apple-system, 'Segoe UI', Roboto, Arial, sans-serif">Tipo de esquema</text>
  <text x="{col_x[1] + 12}" y="{table_y + 21}" font-size="13" font-weight="700" fill="#1a202c"
        font-family="-apple-system, 'Segoe UI', Roboto, Arial, sans-serif">Sembrados</text>
  <text x="{col_x[2] + 12}" y="{table_y + 21}" font-size="13" font-weight="700" fill="#1a202c"
        font-family="-apple-system, 'Segoe UI', Roboto, Arial, sans-serif">Encontrados</text>
  <text x="{col_x[3] + 12}" y="{table_y + 21}" font-size="13" font-weight="700" fill="#1a202c"
        font-family="-apple-system, 'Segoe UI', Roboto, Arial, sans-serif">Recall</text>
</g>"""

    body_rows = []
    for i, r in enumerate(by_type):
        y = table_y + row_h * (i + 1)
        label = SCHEME_LABELS.get(r["scheme_type"], r["scheme_type"])
        recall = _fmt_pct(r["recall_pct"]) if r["recall_pct"] not in ("", None) else "—"
        stripe = "#ffffff" if i % 2 == 0 else "#f8fafc"
        body_rows.append(f"""
<g>
  <rect x="{margin}" y="{y}" width="{width - 2 * margin}" height="{row_h}" fill="{stripe}"/>
  <text x="{col_x[0] + 12}" y="{y + 21}" font-size="13" fill="#1a202c"
        font-family="-apple-system, 'Segoe UI', Roboto, Arial, sans-serif">{_e(label)}</text>
  <text x="{col_x[1] + 12}" y="{y + 21}" font-size="13" fill="#1a202c"
        font-family="-apple-system, 'Segoe UI', Roboto, Arial, sans-serif">{_e(r['planted'])}</text>
  <text x="{col_x[2] + 12}" y="{y + 21}" font-size="13" fill="#1a202c"
        font-family="-apple-system, 'Segoe UI', Roboto, Arial, sans-serif">{_e(r['found'])}</text>
  <text x="{col_x[3] + 12}" y="{y + 21}" font-size="13" font-weight="700" fill="#1f7a4d"
        font-family="-apple-system, 'Segoe UI', Roboto, Arial, sans-serif">{_e(recall)}</text>
</g>""")

    table_h = row_h * (len(by_type) + 1)
    table_border = (
        f'<rect x="{margin}" y="{table_y}" width="{width - 2 * margin}" height="{table_h}" '
        f'fill="none" stroke="#d5dbe3" stroke-width="1.5"/>'
    )

    footer_y = table_y + table_h + 34
    reconcile_txt = "peso_amount reconcilia (2%) en los " + f"{n_seeds} seeds" if peso_reconciles \
        else "atencion: peso_amount no reconcilia en todos los seeds"
    footer = (
        f'<text x="{margin}" y="{footer_y}" font-size="12" fill="#718096" '
        f'font-family="-apple-system, \'Segoe UI\', Roboto, Arial, sans-serif">'
        f'{n_seeds} seeds &middot; {_e(reconcile_txt)} &middot; costo por corrida: $0.00 (Ollama local)</text>'
    )

    height = footer_y + 20

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"
     style="width:100%;height:auto;max-width:{width}px;display:block;">
  <rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>
  <text x="{margin}" y="36" font-size="20" font-weight="700" fill="#1a202c"
        font-family="-apple-system, 'Segoe UI', Roboto, Arial, sans-serif">{_e(title)}</text>
  <text x="{margin}" y="58" font-size="13" fill="#4a5568"
        font-family="-apple-system, 'Segoe UI', Roboto, Arial, sans-serif">Corrida de reporte (eval/harness.py) &mdash; no son seeds de tuning</text>
  {cards_svg}
  {header_row}
  {"".join(body_rows)}
  {table_border}
  {footer}
</svg>"""
    return svg


def write_svg(results_csv_path, by_type_csv_path, out_path, title="Resultado — seeds de reporte"):
    svg = build_results_svg(results_csv_path, by_type_csv_path, title=title)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8")
    return svg


def _chrome_binary():
    candidatos = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    return next((c for c in candidatos if c and Path(c).exists()), None)


def render_png(svg_path, png_path, width=980, height=None):
    """PNG via Chrome headless --screenshot -- sin librerias de Python.
    Si no hay Chrome/Chromium instalado, regresa False sin tronar (el
    .svg solo es igual de valido para una diapositiva)."""
    chrome = _chrome_binary()
    if not chrome:
        return False

    svg_path = Path(svg_path).resolve()
    png_path = Path(png_path).resolve()
    png_path.parent.mkdir(parents=True, exist_ok=True)

    if height is None:
        # el viewBox del svg trae el tamano real (ancho x alto); no hay
        # atributos width/height sueltos porque el svg es responsive
        # (para embeberse en el case file sin desbordar su contenedor).
        import re
        contenido = svg_path.read_text(encoding="utf-8")
        m = re.search(r'viewBox="0 0 (\d+) (\d+)"', contenido)
        height = int(m.group(2)) if m else 620

    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "chart.html"
        html_path.write_text(
            f"<!doctype html><html><body style='margin:0'>{svg_path.read_text(encoding='utf-8')}</body></html>",
            encoding="utf-8",
        )
        subprocess.run(
            [
                chrome, "--headless", "--disable-gpu",
                f"--screenshot={png_path}",
                f"--window-size={width},{height + 40}",
                "--default-background-color=00000000",
                html_path.as_uri(),
            ],
            check=True, capture_output=True, timeout=30,
        )
    return png_path.exists()


def main():
    parser = argparse.ArgumentParser(
        description="The Forensic Auditor -- imagen estatica del resultado agregado (eval/harness.py)"
    )
    parser.add_argument("--results", required=True, help="CSV de eval/harness.py, ej. out/results_report.csv")
    parser.add_argument("--by-type", required=True, help="CSV _by_type de eval/harness.py")
    parser.add_argument("--out", required=True, help="ruta de salida .svg")
    parser.add_argument("--png", default=None, help="ademas, ruta .png (via Chrome headless si esta disponible)")
    parser.add_argument("--title", default="Resultado — seeds de reporte")
    args = parser.parse_args()

    write_svg(args.results, args.by_type, args.out, title=args.title)
    print(f"OK -> {args.out}")

    if args.png:
        ok = render_png(args.out, args.png)
        print((f"OK -> {args.png}") if ok else "SIN PNG: no se encontro Chrome/Chromium en esta maquina (el .svg sigue siendo valido)")


if __name__ == "__main__":
    main()
