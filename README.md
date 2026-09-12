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
    tools/      las 8 herramientas SQL sobre el estate
    agent/      investigador, retador, validador
    report/     serializa submission.json y el case file
    cli.py      entrypoint; recibe la ruta del estate en tiempo de ejecución
    llm.py      envoltorio de Ollama: temperatura 0, caché por sha256,
                contadores llm_calls / wall_clock_seconds, modo replay sin red
  eval/         harness de métrica (recall, falsas acusaciones)
  out/          estates generados, ground truths, submission.json
  Makefile      check-format (corre validate_format.py) y check-isolation
                (falla si "ground_truth" se filtra fuera de generate/)
  validate_format.py   validador oficial de formato (verbatim, sin tocar)
frontend/
  src/          Vite + React
```

`backend/src/generate/schema.sql` es copia byte-idéntica de
`estate_schema.sql` — nombres de columna sin traducir ni renombrar, porque
los jueces los leen directo y cada exhibit cita un `source_table` por nombre.

## Estado actual

- [x] `llm.py` — envoltorio de Ollama verificado (cache-hit no incrementa
      `llm_calls` ni tarda, `chat_json` reintenta si la respuesta no parsea)
- [x] Estructura de `src/` + `eval/` + `out/` según el contrato
- [x] `schema.sql` oficial copiado tal cual
- [x] `Makefile` con `check-format` y `check-isolation` (ambos verificados)
- [ ] Generador del estate + ground truth por seed
- [ ] Las 8 herramientas SQL (`tools/`)
- [ ] Investigador / Retador / Validador (`agent/`)
- [ ] Serialización de `submission.json` + `case_file.html` (`report/`)
- [ ] `cli.py` conectado al pipeline real
- [ ] Frontend: drop de estate, grafo, contraste hallazgo vs. decoy

## Cómo correr lo que existe

```bash
cd backend
make check-isolation      # pasa vacío: aun no hay ground_truth en ningun .py

# check-format necesita un out/submission.json real, que sale del
# pipeline todavia no construido (generate/ -> tools/ -> agent/ -> report/)
```

Ollama corre local (`qwen2.5:7b` de momento) en `http://localhost:11434`;
`backend/src/llm.py` es la única pieza que le habla.

## Las reglas que no se negocian

1. Ningún hallazgo se imprime sin pasar por retador y validador.
2. Los montos salen de consultas SQL, nunca del modelo.
3. El ground truth vive aparte y el agente no puede leerlo — ni importarlo.
4. El mismo seed produce el mismo case file (determinismo: caché de prompts,
   temperatura 0, orden estable de candidatos).
