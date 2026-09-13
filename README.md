# The Forensic Auditor — HackMTY 2026 (Infosys)

Agent that investigates invoice fraud in Mexico against the track's official
schema and rules. Every accusation goes through three roles before it gets
printed:

```
Investigator  builds the finding (hypothesis + evidence)
Challenger    tries to knock it down with the strongest innocent explanation
Validator     code, no model: cites, reconciles amounts within 2%, counts exhibits
```

What survives gets published with its proof. What doesn't gets documented as
a `lead_not_pursued`, with who closed it and why.

> No finding gets printed without having been attacked.
> If a task doesn't serve that sentence, it gets cut.

## Official format

The jury's estate is a **SQLite `.db`** with 8 fixed tables (`vendors`,
`invoices`, `ledger`, `bank_txns`, `purchase_orders`, `contracts`,
`employees`, `efos_list`) and the output is `submission.json` (`findings[]` +
`leads_not_pursued[]` + `run_metadata`) plus a `case_file.html`. The five
scheme types are a fixed enum: `phantom_vendor`, `kickback`,
`round_tripping`, `threshold_splitting`, `revenue_inflation`.

The ground truth lives separately, in a JSON the agent never opens. Hard
rule: the word `ground_truth` may only appear under `backend/src/generate/`
(the generator) and `eval/` (the metric harness) — never in `tools/` or
`agent/`. If it shows up anywhere else, the score caps at 2 no matter the
numbers.

## Structure

```
backend/
  src/
    generate/   estate + ground truth generator (the only place, along with
                eval/, where "ground_truth" is allowed to appear)
    tools/      the 8 SQL tools + the 5 detectors over the estate
    agent/      investigator (4.1), challenger (4.2), validator (4.3)
    report/     case_file.py (self-contained HTML), ui_block.py (the `ui`
                block for the frontend), results_chart.py (the 101-110
                results-table image for the slide)
    cli.py      real entrypoint; investigator -> challenger -> validator per
                candidate, writes submission.json (+ the `ui` block)
    llm.py      model wrapper: local Ollama by default, Gemini as a real
                fallback (--backend gemini / MODEL_BACKEND=gemini), with
                automatic retry on rate-limit (429) and temporary API
                overload (503), sha256 prompt cache, network-free replay mode
  eval/         metric harness (recall, false accusations, per-seed CSV)
  out/          generated estates, ground truths, submission.json (gitignored)
  Makefile      check-format (runs validate_format.py) and check-isolation
                (fails if "ground_truth" leaks outside generate/)
  validate_format.py   official format validator (verbatim, untouched)
frontend/
  src/          Vite + React — 4 states of a single app (no routes):
                idle (DropZone) -> running (GraphView, revealed step by
                step) -> result (StatCards + auto-opened ContrastPanel)
                -> leads (LeadsList with search). Hand-drawn SVG graph,
                fixed positions, no external libraries or CDN.
```

`backend/src/generate/schema.sql` is a byte-identical copy of
`estate_schema.sql` — column names are neither translated nor renamed,
because the judges read them directly and every exhibit cites a
`source_table` by name.

## Current status

Full end-to-end pipeline (see `CLAUDE.md` for the phase-by-phase detail).
Everything below is actually built and has actually been run — it's not a
plan:

- [x] Estate + ground truth generator per seed (`generate/`), including
      clean-population enforcement with no false positives
      (`enforce_clean_population`)
- [x] The 8 SQL tools + the 5 detectors (`tools/`)
- [x] Investigator / Challenger / Validator (`agent/`) — Phases 4.1-4.3
- [x] `cli.py` wires the full cycle and writes a real `submission.json`,
      including the `ui` block (`report/ui_block.py`) the frontend consumes
- [x] `case_file.py` — self-contained HTML with the 5 official sections,
      money-trail SVG drawn in code
- [x] `llm.py` — Ollama by default, **Gemini as a real fallback**
      (`--backend gemini` / `MODEL_BACKEND=gemini`), with automatic retry
      on rate-limit and temporary API overload. **Verified live**: run on
      seed 004 with Gemini in place of Ollama, it flagged the exact same 3
      fraud schemes (`kickback`, `round_tripping`, `threshold_splitting`)
      in 18 seconds and 14 model calls — different wording, same findings
- [x] `Makefile` (`check-format`, `check-isolation`) and the official
      report run (seeds 101-110) already done
- [x] Frontend: the 4 screens from `frontend/Frontend.md` as states of a
      single app — estate drop, progressive graph, auto-opened contrast,
      searchable leads — verified with the network turned off

## How to run what exists

```bash
cd backend
make check-isolation                # 0 -- ground_truth doesn't leak
python -m src.cli --estate out/estate_seed004.db --out out/submission.json
make check-format                   # validates that submission.json
```

Ollama runs locally (`qwen2.5:7b` for now) at `http://localhost:11434`.
To use Gemini instead of Ollama (fallback, same interface):

```bash
export GEMINI_API_KEY="your-key"    # never in the repo
python -m src.cli --estate out/estate_seed004.db --out out/submission_gemini.json --backend gemini
```

`backend/src/llm.py` is the only piece that talks to either one.

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## The rules that don't get negotiated

1. No finding gets printed without going through the challenger and the
   validator.
2. Amounts come from SQL queries, never from the model.
3. The ground truth lives apart and the agent can't read it — or import it.
4. The same seed produces the same case file (determinism: prompt cache,
   temperature 0, stable candidate order).

## Acknowledgments

Thank you to the MLH team, Tecnológico de Monterrey, and Infosys for making
this hackathon possible.
