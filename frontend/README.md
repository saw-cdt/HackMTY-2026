# The Forensic Auditor — Interfaz

Frontend Vite + React del expediente de fraude fiscal. Consume el
`submission.json` que produce el backend y abre los `estate_seedNNN.db`
de forma 100 % local: el `.db` se parsea en el navegador con `sql.js`.

## Correr

```
npm install
npm run dev        # desarrollo
npm run build      # build de producción → dist/
npm run preview    # sirve dist/ para el demo
```

## El demo (sin backend)

El botón **«Cargar demo»** carga `public/demo/estate_seed004.db` (estate
real generado con seed 4) y `public/demo/submission_seed004.json` (informe
de ese mismo estate). Todo funciona sin red.

También puedes soltar archivos:
- `submission.json` → pestañas Resumen / Hallazgos / Contraste / Leads / Grafo
- `estate_seedNNN.db` → la pestaña Estate + resolución de CLABEs y nombres
  en el grafo + verificación de exhibits contra la base

## Qué muestra cada pestaña

| Pestaña | Contenido |
|---|---|
| Resumen | Empresa, periodo, seed, los tres números (`llm_calls`, `mxn_cost`, `wall_clock_seconds`), determinismo, hallazgos con su reconciliación |
| Hallazgos | Una tarjeta por hallazgo: regla, narrative, retador, trail + exhibits, reconciliación al 2 % |
| Contraste | Hallazgo acusado vs lead descartado, filas alineadas |
| Leads | Descartados con señal y razón específica |
| Grafo | Money trail que se construye en 6 pasos con posiciones fijas |
| Estate | El `.db` inspeccionado: 8 tablas, proveedores, 69-B |
| Resultados | Cargas acumuladas contra el ground truth de los seeds 1–10 |

## Formato esperado de submission.json

El frontend normaliza variantes (`run_metadata`/`runMetadata`, `peso_amount`/
`pesoAmount`, `money_trail`, `leads_not_pursued`, …). No cambia nada del
formato de salida del backend. La forma canónica:

```
{
  seed, company_rfc, company_label?, period,
  run_metadata: { llm_calls, mxn_cost, wall_clock_seconds, deterministic },
  findings: [
    {
      id, scheme_type, severity?, entities: ["RFC:...", "EMP:..."],
      peso_amount, return_pct?, narrative,
      challenger: { survives, argument, why_not_enough? },
      exhibits: [{ record_id, source_table, date?, amount, note?, peso? }],
      money_trail: [{ from_clabe?, to_clabe?, amount, exhibit_id, date? }]
    }
  ],
  leads_not_pursued: [
    { entity, signal, reason, tool_calls_made?, closed_by }
  ]
}
```

## Estructura

```
src/
  App.jsx                 estado global + pestañas + carga de archivos
  lib/
    normalize.js          submission.json canónico (tolerante a variantes)
    graph.js              trail/caso, posiciones fijas, curvas
    replay.js             coreografía de 6 pasos
    estate.js             sql.js: abre el .db, CLABEs, exhibits, 8 tablas
    schemes.js            los 5 esquemas + pipeline + closed_by
    format.js             MXN, fechas, números
  components/             DropZone, ThreeNumbers, ReconBox, GraphSvg,
                          TrailGraph, CaseGraph, FindingCard, SummaryTab,
                          ContrastView, LeadsTable, ResultsTab, EstatePanel
  styles.css              sistema de diseño (tema forense oscuro)
```

## Regenerar la demo

Los assets de `public/demo/` se generaron con el backend. Para rehacerlos:

```
python3 backend/src/generate/estate.py --seed 4 --out backend/out/
python3 backend/run_cli_or_similar --estate backend/out/estate_seed004.db
cp backend/out/estate_seed004.db frontend/public/demo/
cp backend/out/submission.json frontend/public/demo/submission_seed004.json
cp backend/out/truth_seed004.json frontend/public/demo/truth_survey.json
```