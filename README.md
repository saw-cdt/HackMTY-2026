# The Forensic Auditor — HackMTY 2026 (Infosys)

Agente que investiga fraude de facturación en México sobre el schema y las
reglas oficiales del track. Cada acusación pasa por tres roles antes de
imprimirse:

```
Investigador  arma el hallazgo (hipótesis + evidencia)
Retador       intenta tumbarlo con la explicación inocente más fuerte posible
Validador     código, sin modelo: cita, reconcilia montos al 2%, cuenta exhibits
```

Lo que sobrevive se publica con su prueba. Lo que no, se documenta como
`lead_not_pursued` con quién lo cerró y por qué.

> Ningún hallazgo se imprime sin haber sido atacado.
> Si una tarea no sirve a esa frase, se corta.

## Formato oficial

El estate del jurado es un **SQLite `.db`** con 8 tablas fijas (`vendors`,
`invoices`, `ledger`, `bank_txns`, `purchase_orders`, `contracts`,
`employees`, `efos_list`) y la salida es `submission.json` (`findings[]` +
`leads_not_pursued[]` + `run_metadata`) más un `case_file.html`. Los cinco
tipos de esquema son un enum fijo: `phantom_vendor`, `kickback`,
`round_tripping`, `threshold_splitting`, `revenue_inflation`.

El ground truth vive aparte, en un JSON que el agente nunca abre. Regla dura:
la palabra `ground_truth` solo puede aparecer en `backend/src/generate/` (el
generador) y en `eval/` (el harness de métrica) — nunca en `tools/` ni en
`agent/`. Si aparece en cualquier otro lado, la calificación topa en 2 sin
importar los números.

## Estructura

```
backend/
  src/
    generate/   generador del estate + ground truth (único lugar,
                 junto con eval/, donde puede aparecer "ground_truth")
    tools/      las 8 herramientas SQL + los 5 detectores sobre el estate
    agent/      investigador (4.1), retador (4.2), validador (4.3)
    report/     case_file.py (HTML autocontenido), ui_block.py (bloque `ui`
                para el frontend), results_chart.py (imagen de la tabla
                101-110 para la diapositiva)
    cli.py      entrypoint real; investigador -> retador -> validador por
                cada candidato, escribe submission.json (+ bloque `ui`)
    llm.py      envoltorio del modelo: Ollama local por default, Gemini
                como respaldo (--backend gemini / MODEL_BACKEND=gemini),
                temperatura 0, caché por sha256, modo replay sin red
  eval/         harness de métrica (recall, falsas acusaciones, CSV por seed)
  out/          estates generados, ground truths, submission.json (gitignored)
  Makefile      check-format (corre validate_format.py) y check-isolation
                (falla si "ground_truth" se filtra fuera de generate/)
  validate_format.py   validador oficial de formato (verbatim, sin tocar)
frontend/
  src/          Vite + React — 4 estados de una sola app (no rutas):
                reposo (DropZone) -> corriendo (GraphView, revelado por
                step) -> resultado (StatCards + ContrastPanel auto-abierto)
                -> leads (LeadsList con búsqueda). Grafo SVG a mano,
                posiciones fijas, sin librerías externas ni CDN.
```

`backend/src/generate/schema.sql` es copia byte-idéntica de
`estate_schema.sql` — nombres de columna sin traducir ni renombrar, porque
los jueces los leen directo y cada exhibit cita un `source_table` por nombre.

## Estado actual

Pipeline completo, extremo a extremo (ver `CLAUDE.md` para el detalle fase
por fase). Todo lo de abajo está construido y corrido de verdad, no es plan:

- [x] Generador del estate + ground truth por seed (`generate/`), incluida
      la población limpia sin falsos positivos (`enforce_clean_population`)
- [x] Las 8 herramientas SQL + los 5 detectores (`tools/`)
- [x] Investigador / Retador / Validador (`agent/`) — Fases 4.1-4.3
- [x] `cli.py` conecta el ciclo completo y escribe `submission.json` real,
      incluido el bloque `ui` (`report/ui_block.py`) que consume el frontend
- [x] `case_file.py` — HTML autocontenido con las 5 secciones oficiales,
      SVG del money trail dibujado en código
- [x] `llm.py` — Ollama por default, **Gemini como respaldo real**
      (`--backend gemini` / `MODEL_BACKEND=gemini`, con reintento
      automático ante rate-limit y sobrecarga temporal de la API)
- [x] `Makefile` (`check-format`, `check-isolation`) y corrida oficial de
      reporte (seeds 101-110) ya hecha
- [x] Frontend: las 4 pantallas de `frontend/Frontend.md` como estados de
      una sola app — drop del estate, grafo progresivo, contraste
      auto-abierto, leads con búsqueda — verificado con conexión apagada
- [x] Backend desplegado en Vultr, corriendo en paralelo a la Mac —
      mismo `submission.json` en ambos (ver sección abajo)

## Cómo correr lo que existe

```bash
cd backend
make check-isolation                # 0 -- ground_truth no se filtra
python -m src.cli --estate out/estate_seed004.db --out out/submission.json
make check-format                   # valida ese submission.json
```

Ollama corre local (`qwen2.5:7b` de momento) en `http://localhost:11434`.
Para usar Gemini en vez de Ollama (respaldo, misma interfaz):

```bash
export GEMINI_API_KEY="tu-key"      # nunca en el repo
python -m src.cli --estate out/estate_seed004.db --out out/submission_gemini.json --backend gemini
```

`backend/src/llm.py` es la única pieza que le habla a cualquiera de los dos.

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Vultr — backend desplegado

El backend corre igual en un servidor de Vultr: mismo código, sin
dependencias externas (`backend/` es solo librería estándar de Python).

```bash
rsync -az backend/ usuario@IP_DEL_SERVIDOR:/ruta/forensic-auditor/
ssh usuario@IP_DEL_SERVIDOR
cd /ruta/forensic-auditor
python3 -m src.cli --estate out/estate_seedNNN.db \
  --out out/submission_seedNNN.json --mode replay
```

Verificado: mismo seed, mismo `submission.json` — `findings`,
`leads_not_pursued` y el bloque `ui` idénticos entre Vultr y local.

Vultr es el despliegue paralelo para la categoría del patrocinador.

## Las reglas que no se negocian

1. Ningún hallazgo se imprime sin pasar por retador y validador.
2. Los montos salen de consultas SQL, nunca del modelo.
3. El ground truth vive aparte y el agente no puede leerlo — ni importarlo.
4. El mismo seed produce el mismo case file (determinismo: caché de prompts,
   temperatura 0, orden estable de candidatos).
