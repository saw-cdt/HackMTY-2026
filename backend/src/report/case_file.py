"""
Fase 5: el case file. Genera un HTML autocontenido con las 5 secciones
de case_file_structure.md, en ese orden exacto:

    1. Encabezado
    2. Resumen ejecutivo
    3. Una seccion por hallazgo (money trail como SVG local)
    4. Leads no perseguidos
    5. Metodo y limites

Lee el estate.db (solo para traducir RFC/CLABE/emp_id a nombres legibles)
y el submission.json que ya produjo cli.py. No corre el agente ni conoce
al modelo -- es pura serializacion de lo que el ciclo ya decidio.

Sin CDN, sin fuentes externas, sin llamadas de red: todo el CSS y el SVG
van embebidos en el propio archivo. Debe abrirse con el wifi apagado.

No importa nada de generate/ ni lee truth.json.
"""
import argparse
import html as html_mod
import json
import re
import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SRC_DIR))
sys.path.insert(0, str(_SRC_DIR / "tools"))
sys.path.insert(0, str(_SRC_DIR / "agent"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import db
import tools
import validator  # reutiliza la reconciliacion por tabla, misma tolerancia del 2%
import results_chart  # imagen del resultado agregado (eval/harness.py), opcional

SCHEME_LABELS = {
    "phantom_vendor": "Proveedor fantasma",
    "kickback": "Retorno a empleado (kickback)",
    "round_tripping": "Round-tripping",
    "threshold_splitting": "Fraccionamiento bajo el limite de aprobacion",
    "revenue_inflation": "Ingresos inflados",
}
CONFIDENCE_LABELS = {"proven": "Probado", "probable": "Probable"}
CLOSED_BY_LABELS = {
    "investigator": "el investigador",
    "challenger": "el retador",
    "validator": "el validador",
}
_CLABE_RE = re.compile(r"^\d{10,18}$")
_e = html_mod.escape


# ---------------------------------------------------------------------
# Lecturas auxiliares del estate -- solo para traducir ids a etiquetas
# legibles por humanos. Nunca inventan un dato que no este en el estate.
# ---------------------------------------------------------------------
def _periodo(conn):
    fila = conn.execute("""
        SELECT MIN(f) AS lo, MAX(f) AS hi FROM (
            SELECT issue_date AS f FROM invoices
            UNION ALL SELECT date FROM bank_txns
            UNION ALL SELECT date FROM ledger
        )
    """).fetchone()
    if not fila or not fila["lo"]:
        return "sin datos"
    return f"{fila['lo']} a {fila['hi']}"


def _entity_label(conn, empresa_rfc, raw):
    """'RFC:xxx' / 'EMP:0001' / un CLABE de 18 digitos / 'EMPRESA' ->
    nombre legible. Si no encuentra nada en el estate, regresa el
    identificador crudo tal cual -- nunca inventa un nombre."""
    if raw == "EMPRESA":
        return "Empresa investigada"
    if raw.startswith("RFC:"):
        rfc = raw[4:]
        if rfc == empresa_rfc:
            return f"Empresa investigada ({rfc})"
        v = tools.vendor(conn, rfc)
        return f"{v['legal_name']} ({rfc})" if v else raw
    if raw.startswith("EMP:"):
        row = conn.execute("SELECT name FROM employees WHERE emp_id = ?", (raw,)).fetchone()
        return f"{row['name']} ({raw})" if row else raw
    if _CLABE_RE.match(raw):
        quien = tools.whose_clabe(conn, raw)
        if quien["tipo"] == "vendor":
            return f"{quien['nombre']} ({quien['rfc']})"
        if quien["tipo"] == "employee":
            return f"{quien['nombre']} ({quien['emp_id']})"
        if quien["tipo"] == "empresa":
            return "Empresa investigada"
        return raw
    return raw


def _fmt_money(n):
    try:
        return f"${float(n):,.2f}"
    except (TypeError, ValueError):
        return str(n)


# ---------------------------------------------------------------------
# Money trail como SVG, generado localmente (sin librerias externas).
# ---------------------------------------------------------------------
def _truncar(texto, maxlen=26):
    return texto if len(texto) <= maxlen else texto[: maxlen - 1] + "…"


def _svg_money_trail(conn, empresa_rfc, money_trail):
    if not money_trail:
        return ('<p class="sin-trail">Sin transferencia que liquide esta '
                'operacion en <code>bank_txns</code> -- esa ausencia es '
                'precisamente la evidencia (ver narrative).</p>')

    nodos_crudos = [money_trail[0]["from"]] + [p["to"] for p in money_trail]
    etiquetas = [_entity_label(conn, empresa_rfc, r) for r in nodos_crudos]

    box_w, box_h, gap = 200, 60, 140
    margin_x, top_pad, bottom_pad = 20, 34, 34
    n = len(etiquetas)
    svg_w = margin_x * 2 + n * box_w + (n - 1) * gap
    svg_h = top_pad + box_h + bottom_pad
    cy = top_pad + box_h / 2

    partes = [
        f'<svg viewBox="0 0 {svg_w} {svg_h}" width="100%" '
        f'style="max-width:{svg_w}px" role="img" '
        f'aria-label="Money trail" xmlns="http://www.w3.org/2000/svg">',
        '<defs><marker id="flecha" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#4a5568"/></marker></defs>',
    ]

    xs = [margin_x + i * (box_w + gap) for i in range(n)]
    for i, etiqueta in enumerate(etiquetas):
        x = xs[i]
        partes.append(
            f'<g><title>{_e(nodos_crudos[i])}</title>'
            f'<rect x="{x}" y="{top_pad}" width="{box_w}" height="{box_h}" rx="8" '
            f'fill="#eef2f7" stroke="#4a5568" stroke-width="1.5"/>'
            f'<text x="{x + box_w / 2}" y="{cy + 5}" text-anchor="middle" '
            f'font-family="Arial, Helvetica, sans-serif" font-size="13" fill="#1a202c">'
            f'{_e(_truncar(etiqueta))}</text></g>'
        )

    for i, paso in enumerate(money_trail):
        x1, x2 = xs[i] + box_w, xs[i + 1]
        label_top = f"{_fmt_money(paso.get('amount'))}"
        label_bottom = f"{paso.get('date', '')} · {paso.get('exhibit_id', '')}"
        partes.append(
            f'<line x1="{x1}" y1="{cy}" x2="{x2 - 6}" y2="{cy}" '
            f'stroke="#4a5568" stroke-width="1.5" marker-end="url(#flecha)"/>'
            f'<text x="{(x1 + x2) / 2}" y="{top_pad - 10}" text-anchor="middle" '
            f'font-family="Arial, Helvetica, sans-serif" font-size="12" font-weight="bold" '
            f'fill="#1a202c">{_e(label_top)}</text>'
            f'<text x="{(x1 + x2) / 2}" y="{top_pad + box_h + 20}" text-anchor="middle" '
            f'font-family="Arial, Helvetica, sans-serif" font-size="11" fill="#4a5568">'
            f'{_e(label_bottom)}</text>'
        )

    partes.append("</svg>")
    return "\n".join(partes)


# ---------------------------------------------------------------------
# Reconciliacion de pesos -- misma regla y tolerancia que validator.py
# (que a su vez espeja validate_format.py oficial): suma por tabla,
# compara contra la que mejor empate dentro del 2%.
# ---------------------------------------------------------------------
def _reconciliacion_html(conn, finding):
    exhibits = finding.get("exhibits") or []
    peso = finding.get("peso_amount")
    por_tabla = validator._monto_por_tabla(conn, exhibits)

    filas = "".join(
        f"<tr><td>{_e(tabla)}</td><td class='num'>{_fmt_money(valor)}</td></tr>"
        for tabla, valor in sorted(por_tabla.items())
    )
    if not por_tabla:
        return (f"<table class='reconciliacion'><tbody>{filas}</tbody></table>"
                "<p class='reconciliacion-nota'>Ningun exhibit cita una tabla con "
                "monto reconciliable.</p>")

    mejor_tabla, mejor_valor = min(por_tabla.items(), key=lambda kv: abs(peso - kv[1]))
    tolerancia = 0.02 * max(mejor_valor, 1)
    diff = abs(peso - mejor_valor)
    ok = diff <= tolerancia
    nota = (
        f"peso_amount reclamado ({_fmt_money(peso)}) reconcilia contra "
        f"<b>{_e(mejor_tabla)}</b> ({_fmt_money(mejor_valor)}), diferencia de "
        f"{_fmt_money(diff)} ({(diff / max(mejor_valor, 1)) * 100:.2f}%), "
        f"{'dentro' if ok else 'FUERA'} del margen del 2%."
    )
    return (
        f"<table class='reconciliacion'><thead><tr><th>Tabla</th>"
        f"<th>Suma citada</th></tr></thead><tbody>{filas}</tbody></table>"
        f"<p class='reconciliacion-nota'>{nota}</p>"
    )


# ---------------------------------------------------------------------
# Secciones del reporte
# ---------------------------------------------------------------------
def _encabezado_html(conn, submission):
    meta = submission.get("run_metadata", {})
    empresa_rfc = db.company_rfc(conn) or "desconocido"
    return f"""
<header class="encabezado">
  <h1>The Forensic Auditor &mdash; Case File</h1>
  <table class="datos-clave">
    <tr><th>Empresa investigada</th><td>{_e(empresa_rfc)}</td></tr>
    <tr><th>Periodo auditado</th><td>{_e(_periodo(conn))}</td></tr>
    <tr><th>Seed del estate</th><td>{_e(str(submission.get('seed')))}</td></tr>
    <tr><th>Llamadas al modelo</th><td>{_e(str(meta.get('llm_calls', '?')))}</td></tr>
    <tr><th>Costo (MXN)</th><td>{_fmt_money(meta.get('mxn_cost', 0))}</td></tr>
    <tr><th>Tiempo de corrida</th><td>{meta.get('wall_clock_seconds', '?')} s</td></tr>
    <tr><th>Corrida determinista</th>
        <td>{'Si' if meta.get('deterministic') else 'No'} &mdash; el mismo seed
        produce el mismo submission.json byte a byte.</td></tr>
  </table>
</header>
"""


def _resumen_ejecutivo_html(submission, results_csv=None, results_by_type_csv=None):
    """results_csv / results_by_type_csv: rutas opcionales a los CSV que
    ya escribio eval/harness.py (ej. out/results_report.csv y su
    _by_type.csv) sobre una corrida de reporte de VARIOS seeds -- no
    tienen nada que ver con el seed de este case file en particular, se
    embeben aparte como validacion del sistema. Si no se dan, esta
    seccion simplemente no aparece -- nunca se inventa un resultado."""
    findings = submission.get("findings", [])
    leads = submission.get("leads_not_pursued", [])
    exposicion = sum(f.get("peso_amount", 0) for f in findings)
    n_proven = sum(1 for f in findings if f.get("confidence") == "proven")
    n_probable = sum(1 for f in findings if f.get("confidence") == "probable")

    resultado_agregado_html = ""
    if results_csv and results_by_type_csv:
        svg = results_chart.build_results_svg(
            results_csv, results_by_type_csv,
            title="Validacion del sistema — seeds de reporte",
        )
        resultado_agregado_html = f"""
  <h3>Validacion agregada (seeds de reporte, no este seed en particular)</h3>
  <p>Este case file describe UN seed. La imagen de abajo es la corrida
  de <code>eval/harness.py</code> sobre los seeds de reporte reservados
  para medir el sistema completo -- se incluye aqui como evidencia de
  que el pipeline esta validado, no como resultado de este caso.</p>
  <div class="money-trail">{svg}</div>"""

    if findings:
        cuerpo = (
            f"El sistema investigo {len(findings) + len(leads)} candidato(s) "
            f"sealados por los detectores. De ellos, {len(findings)} sobrevivieron "
            f"al retador y al validador y se publican como hallazgo; "
            f"{len(leads)} se cerraron sin acusacion, cada uno con su razon "
            f"especifica (seccion 4)."
        )
    else:
        cuerpo = (
            f"El sistema investigo {len(leads)} candidato(s) sealados por los "
            f"detectores. Ninguno sobrevivio hasta convertirse en hallazgo "
            f"publicado -- los {len(leads)} se cerraron, cada uno con su razon "
            f"especifica (seccion 4)."
        )

    return f"""
<section class="resumen">
  <h2>2. Resumen ejecutivo</h2>
  <p>{cuerpo}</p>
  <table class="resumen-tabla">
    <tr><th>Hallazgos</th>
        <td>{len(findings)} ({n_proven} probado(s), {n_probable} probable(s))</td></tr>
    <tr><th>Exposicion total</th><td>{_fmt_money(exposicion)}</td></tr>
    <tr><th>Leads investigados y cerrados</th><td>{len(leads)}</td></tr>
  </table>
{resultado_agregado_html}
</section>
"""


def _hallazgo_html(conn, empresa_rfc, i, finding):
    entities = finding.get("entities", [])
    entidades_html = ", ".join(
        f"{_e(_entity_label(conn, empresa_rfc, ent))} <code>{_e(ent)}</code>"
        for ent in entities
    )
    primera_entidad = _entity_label(conn, empresa_rfc, entities[0]) if entities else "?"
    confidence = finding.get("confidence")
    conf_label = CONFIDENCE_LABELS.get(confidence, confidence or "?")
    conf_clase = "conf-proven" if confidence == "proven" else "conf-probable"

    exhibits = finding.get("exhibits", [])
    filas_exhibits = "".join(
        f"<tr><td>{_e(ex.get('exhibit_id', ''))}</td>"
        f"<td>{_e(ex.get('source_table', ''))}</td>"
        f"<td>{_e(ex.get('record_id', ''))}</td>"
        f"<td>{_e(ex.get('note', ''))}</td></tr>"
        for ex in exhibits
    )

    retador_html = ""
    argumento = finding.get("challenger_argument")
    if argumento:
        retador_html = f"""
    <h4>Lo que argumento el retador</h4>
    <p class="retador">{_e(argumento)} &mdash; no basto para explicar la evidencia.</p>
"""

    scheme_type = finding.get("scheme_type")
    return f"""
<article class="hallazgo" id="hallazgo-{i}">
  <h3>{i}. {_e(primera_entidad)} &mdash; {_e(SCHEME_LABELS.get(scheme_type, scheme_type))}</h3>
  <p class="entidades">Entidades involucradas: {entidades_html}</p>

  <h4>Regla rota</h4>
  <p class="regla">{_e(finding.get('rule_broken', ''))}</p>

  <h4>Monto y confianza</h4>
  <p><span class="monto">{_fmt_money(finding.get('peso_amount'))}</span>
     <span class="badge {conf_clase}">{_e(conf_label)}</span></p>

  <h4>Que paso</h4>
  <p class="narrative">{_e(finding.get('narrative', ''))}</p>

  <h4>Money trail</h4>
  <div class="money-trail">{_svg_money_trail(conn, empresa_rfc, finding.get('money_trail'))}</div>

  <h4>Exhibits</h4>
  <table class="exhibits">
    <thead><tr><th>Exhibit</th><th>Tabla</th><th>Record id</th><th>Que prueba</th></tr></thead>
    <tbody>{filas_exhibits}</tbody>
  </table>

  <h4>Reconciliacion</h4>
  {_reconciliacion_html(conn, finding)}
  {retador_html}
</article>
"""


def _hallazgos_html(conn, submission):
    empresa_rfc = db.company_rfc(conn) or ""
    findings = submission.get("findings", [])
    if not findings:
        return """
<section class="hallazgos">
  <h2>3. Hallazgos</h2>
  <p>Ningun candidato investigado sobrevivio al retador y al validador en
  esta corrida. Ver la seccion 4 para el detalle de cada lead cerrado.</p>
</section>
"""
    cuerpo = "\n".join(
        _hallazgo_html(conn, empresa_rfc, i, f) for i, f in enumerate(findings, start=1)
    )
    return f"""
<section class="hallazgos">
  <h2>3. Hallazgos</h2>
  {cuerpo}
</section>
"""


def _leads_html(conn, submission):
    empresa_rfc = db.company_rfc(conn) or ""
    leads = submission.get("leads_not_pursued", [])
    if not leads:
        return """
<section class="leads">
  <h2>4. Leads no perseguidos</h2>
  <p>Ningun lead se cerro sin acusacion en esta corrida.</p>
</section>
"""
    filas = "".join(
        f"""<tr>
      <td>{_e(_entity_label(conn, empresa_rfc, l.get('entity', '')))}
          <br><code>{_e(l.get('entity', ''))}</code></td>
      <td>{_e(l.get('signal', ''))}</td>
      <td>{_e(l.get('reason', ''))}</td>
      <td>{', '.join(_e(t) for t in l.get('tool_calls_made', []) ) or '&mdash;'}</td>
      <td>{_e(CLOSED_BY_LABELS.get(l.get('closed_by'), l.get('closed_by', '')))}</td>
    </tr>"""
        for l in leads
    )
    return f"""
<section class="leads">
  <h2>4. Leads no perseguidos</h2>
  <p>Cada entidad senalada por un detector que NO termino en hallazgo,
  con la razon especifica y la evidencia que se examino antes de cerrarla.</p>
  <table class="leads-tabla">
    <thead><tr><th>Entidad</th><th>Senal</th><th>Razon</th>
               <th>Herramientas consultadas</th><th>Cerrado por</th></tr></thead>
    <tbody>{filas}</tbody>
  </table>
</section>
"""


def _metodo_limites_html():
    return """
<section class="metodo">
  <h2>5. Metodo y limites</h2>

  <h4>Arquitectura</h4>
  <p>Cinco detectores deterministas (sin modelo) priorizan candidatos sobre
  el estate SQLite. Cada candidato pasa por un investigador (arma el
  hallazgo o cierra el lead, con dos llamadas cortas al modelo), un retador
  (construye la explicacion inocente mas fuerte para tratar de tumbarlo,
  sin ver el detector que lo senalo) y un validador sin modelo (verifica
  formato y reconciliacion de pesos antes de publicar). El modelo nunca
  calcula montos ni decide si algo se publica.</p>
  <p>El analisis se corre por linea de comandos (<code>python -m src.cli</code>);
  no hay un endpoint ni un servidor que permita cargar un estate desde la
  interfaz y disparar la corrida en vivo. El frontend solo puede mostrar
  un <code>submission.json</code> ya generado de antemano -- soltar un
  <code>.db</code> ahi no ejecuta nada, solo busca su companion ya
  preparado.</p>

  <h4>Fuera de alcance en esta corrida</h4>
  <p>No generamos esquemas entrelazados en nuestro conjunto de prueba;
  el sistema los procesa pero no esta afinado para ellos. El
  fraccionamiento bajo el limite de aprobacion (<code>threshold_splitting</code>)
  depende de poder inferir un umbral de aprobacion a partir de
  <code>purchase_orders</code>; si el estate no permite inferirlo de forma
  concluyente, ese detector simplemente no corre en vez de inventar un
  numero.</p>
  <p>El retador reconoce cuatro tipos de explicacion inocente, acotados
  por tipo de esquema: contrato, orden de compra, una factura de retorno
  (para kickback/round_tripping) y un cobro real via <code>bank_txns</code>
  (para revenue_inflation). Una explicacion legitima que no encaje en
  estos cuatro patrones -- aunque sea cierta -- el retador no la
  reconoceria como exculpatoria.</p>

  <h4>Que el sistema NO puede detectar</h4>
  <p>Solo los cinco tipos de esquema del catalogo (proveedor fantasma,
  kickback, round-tripping, fraccionamiento bajo el limite, ingresos
  inflados). Fraude que no deje rastro en las 8 tablas del estate --
  efectivo fuera de <code>bank_txns</code>, colusion verbal, activos
  fisicos -- queda fuera del alcance de este sistema por diseno.</p>

  <h4>Sobre las metricas reportadas</h4>
  <p>Los estates de evaluacion (seeds de tuning y de reporte) los genera
  nuestro propio generador (<code>generate/</code>), no un dataset
  independiente o de un tercero. El 100% de recall reportado mide
  consistencia interna -- que el sistema encuentra lo que su propio
  generador sembro, bajo su propia definicion de cada esquema -- no una
  validacion externa contra fraude real o casos de otro origen.</p>

  <h4>Reproducibilidad</h4>
  <p>Desde <code>backend/</code>, con el mismo seed:</p>
  <pre>python -m src.generate.estate --seed &lt;N&gt; --out out/
python -m src.cli --estate out/estate_seed&lt;NNN&gt;.db --out out/submission.json
python -m src.report.case_file --estate out/estate_seed&lt;NNN&gt;.db \\
    --submission out/submission.json --out out/case_file.html</pre>
  <p>El mismo seed produce el mismo <code>submission.json</code> byte a
  byte (<code>llm_calls</code> incluido); <code>wall_clock_seconds</code>
  varia entre corridas a proposito -- mide el costo real de esa corrida,
  no una propiedad del seed.</p>
</section>
"""


_CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body {
  margin: 0; padding: 2rem 1.5rem 4rem;
  background: #ffffff; color: #1a202c;
  font-family: -apple-system, "Segoe UI", Roboto, Arial, Helvetica, sans-serif;
  line-height: 1.5;
}
.reporte { max-width: 880px; margin: 0 auto; }
h1 { font-size: 1.6rem; margin: 0 0 1rem; }
h2 { font-size: 1.25rem; margin: 2.5rem 0 0.75rem; border-bottom: 2px solid #1a202c; padding-bottom: 0.25rem; }
h3 { font-size: 1.1rem; margin: 0 0 0.25rem; }
h4 { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.04em;
     color: #4a5568; margin: 1.1rem 0 0.35rem; }
p { margin: 0.35rem 0; }
code { background: #f1f4f8; padding: 0.05rem 0.3rem; border-radius: 3px; font-size: 0.85em; }
pre { background: #f1f4f8; padding: 0.75rem 1rem; border-radius: 6px; overflow-x: auto; font-size: 0.85rem; }
table { border-collapse: collapse; width: 100%; margin: 0.4rem 0 1rem; font-size: 0.92rem; }
th, td { border: 1px solid #d5dbe3; padding: 0.4rem 0.6rem; text-align: left; vertical-align: top; }
th { background: #f1f4f8; }
.num { text-align: right; }
table.datos-clave th { width: 40%; background: none; border: none; padding-left: 0; }
table.datos-clave td { border: none; padding-left: 0; }
table.datos-clave tr { border-bottom: 1px solid #eef1f5; }
.resumen-tabla th { width: 45%; }
.badge { display: inline-block; padding: 0.15rem 0.55rem; border-radius: 999px;
         font-size: 0.8rem; font-weight: 600; margin-left: 0.5rem; }
.conf-proven { background: #1f7a4d; color: #fff; }
.conf-probable { background: #fff; color: #8a5a00; border: 1.5px solid #d99a1b; }
.monto { font-size: 1.15rem; font-weight: 700; }
.hallazgo { border: 1px solid #d5dbe3; border-radius: 8px; padding: 1rem 1.25rem;
            margin-bottom: 1.5rem; page-break-inside: avoid; }
.entidades { color: #4a5568; font-size: 0.9rem; }
.retador { background: #fff8e6; border-left: 3px solid #d99a1b; padding: 0.5rem 0.75rem; }
.reconciliacion-nota { font-size: 0.9rem; }
.money-trail { overflow-x: auto; }
.sin-trail { color: #7a1f1f; }
footer.pie { margin-top: 3rem; font-size: 0.8rem; color: #718096; text-align: center; }
@media print {
  body { padding: 0; }
  .hallazgo { break-inside: avoid; }
}
"""


def render_html(conn, submission, results_csv=None, results_by_type_csv=None):
    """Ensambla el HTML completo, en el orden de case_file_structure.md.
    results_csv/results_by_type_csv: opcionales, ver _resumen_ejecutivo_html."""
    partes = [
        "<!doctype html><html lang='es'><head><meta charset='utf-8'>",
        "<title>The Forensic Auditor — Case File</title>",
        f"<style>{_CSS}</style></head><body><div class='reporte'>",
        _encabezado_html(conn, submission),
        _resumen_ejecutivo_html(submission, results_csv, results_by_type_csv),
        _hallazgos_html(conn, submission),
        _leads_html(conn, submission),
        _metodo_limites_html(),
        "<footer class='pie'>Generado localmente, sin llamadas de red. "
        "Abre este archivo directamente en el navegador.</footer>",
        "</div></body></html>",
    ]
    return "\n".join(partes)


def build_case_file(estate_path, submission_path, out_path,
                     results_csv=None, results_by_type_csv=None):
    """Punto de entrada programatico: lee el estate y el submission.json
    ya producidos, escribe el HTML en out_path. Regresa el HTML tambien,
    por si el llamador (eval/harness.py mas adelante) quiere inspeccionarlo.
    results_csv/results_by_type_csv: opcionales, ver _resumen_ejecutivo_html."""
    conn = db.connect(estate_path)
    submission = json.loads(Path(submission_path).read_text(encoding="utf-8"))
    contenido = render_html(conn, submission, results_csv, results_by_type_csv)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(contenido, encoding="utf-8")
    return contenido


def main():
    parser = argparse.ArgumentParser(description="The Forensic Auditor -- genera el case file HTML")
    parser.add_argument("--estate", required=True, help="ruta al estate .db")
    parser.add_argument("--submission", required=True, help="ruta a submission.json ya producido")
    parser.add_argument("--out", required=True, help="ruta de salida para el case file .html")
    parser.add_argument("--results-csv", default=None,
                         help="opcional: CSV de eval/harness.py (ej. out/results_report.csv) para "
                              "embeber la validacion agregada en el resumen ejecutivo")
    parser.add_argument("--results-by-type-csv", default=None,
                         help="opcional: el _by_type.csv correspondiente a --results-csv")
    args = parser.parse_args()

    build_case_file(args.estate, args.submission, args.out,
                     results_csv=args.results_csv, results_by_type_csv=args.results_by_type_csv)
    print(f"OK -> {args.out}")


if __name__ == "__main__":
    main()
