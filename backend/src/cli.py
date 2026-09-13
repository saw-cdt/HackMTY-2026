"""
Punto de entrada del pipeline. Recibe la ruta del estate en tiempo de
ejecucion -- rutas hardcodeadas fallan segun las reglas del track.

Corre el ciclo completo sobre CADA candidato de prioritized_candidates():
  investigador -> (retador, solo si armo hallazgo) -> validador

y escribe submission.json con el formato oficial (findings,
leads_not_pursued, run_metadata).

Uso:
    python -m src.cli --estate out/estate_seed001.db \
                       --out out/submission.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SRC_DIR))
sys.path.insert(0, str(_SRC_DIR / "tools"))
sys.path.insert(0, str(_SRC_DIR / "agent"))

import db
import tools
import investigator
import challenger
import validator
from llm import LLMClient

DEFAULT_MODEL = "qwen2.5:7b"


def _inferir_seed(estate_path):
    """out/estate_seed001.db -> 1. Si el archivo no sigue esa convencion
    (el estate de un juez podria no hacerlo), 0 en vez de tronar."""
    m = re.search(r"estate_seed(\d+)\.db$", str(estate_path))
    return int(m.group(1)) if m else 0


def run(estate_path, out_path, model=DEFAULT_MODEL, cache_dir=None,
        mode="record", ollama_url=None, seed=None):
    """Corre el ciclo completo y escribe submission.json en out_path.
    Regresa el dict de submission (por si el llamador quiere inspeccionarlo,
    ej. eval/harness.py mas adelante) ademas de escribirlo a disco."""
    conn = db.connect(estate_path)
    cache_dir = cache_dir or str(Path(out_path).parent / ".llm_cache")
    llm = LLMClient(model=model, cache_dir=cache_dir, mode=mode, ollama_url=ollama_url)

    if seed is None:
        seed = _inferir_seed(estate_path)

    findings = []
    leads = []

    for candidato in tools.prioritized_candidates(conn):
        kind, payload = investigator.investigate(conn, llm, candidato)

        if kind == "lead":
            leads.append(payload)
            continue

        # payload es un hallazgo en borrador -> el retador lo intenta tumbar
        veredicto = challenger.challenge(conn, llm, payload)
        if not veredicto["survives"]:
            leads.append({
                "entity": payload["entities"][0],
                "signal": candidato["signal"],
                "reason": veredicto["argument"],
                "tool_calls_made": [],
                "closed_by": "challenger",
            })
            continue

        # sobrevivio al retador: se guarda que se argumento y por que no
        # basto (no es un campo del schema oficial, pero report/case_file.py
        # -- Fase 5 -- lo va a necesitar; los validadores de formato
        # ignoran campos que no reconocen).
        payload["challenger_argument"] = veredicto["argument"]

        kind2, payload2 = validator.gate(conn, payload)
        (findings if kind2 == "finding" else leads).append(payload2)

    submission = {
        "seed": seed,
        "findings": findings,
        "leads_not_pursued": leads,
        "run_metadata": {
            # logical_calls, no llm.llm_calls: describe el trabajo que hizo
            # el agente (cuantas veces le pregunto algo al modelo), no
            # cuantas veces cruzo la red -- por eso es estable entre una
            # corrida en frio y un replay todo en cache. wall_clock_seconds
            # SI varia entre corridas a proposito (ver CLAUDE.md, "Estado
            # actual"): mide el costo real de ESTA corrida, y un replay en
            # cache legitimamente cuesta ~0.
            "llm_calls": llm.logical_calls,
            "mxn_cost": 0.0,
            "wall_clock_seconds": round(llm.wall_clock_seconds, 3),
            "deterministic": True,
        },
    }

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(submission, indent=2, ensure_ascii=False), encoding="utf-8")

    return submission


def main():
    parser = argparse.ArgumentParser(description="The Forensic Auditor -- corre el ciclo completo")
    parser.add_argument("--estate", required=True, help="ruta al estate .db")
    parser.add_argument("--out", required=True, help="ruta de salida para submission.json")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--cache-dir", default=None,
                         help="cache de prompts (default: junto a --out, en .llm_cache/)")
    parser.add_argument("--mode", choices=["record", "replay"], default="record",
                         help="record llama a Ollama si falta cache; replay solo lee, falla si no hay entrada")
    parser.add_argument("--ollama-url", default=None)
    parser.add_argument("--seed", type=int, default=None,
                         help="si no se da, se infiere de estate_seedNNN.db")
    args = parser.parse_args()

    submission = run(
        args.estate, args.out, model=args.model, cache_dir=args.cache_dir,
        mode=args.mode, ollama_url=args.ollama_url, seed=args.seed,
    )

    meta = submission["run_metadata"]
    print(f"OK -> {args.out}")
    print(f"   seed: {submission['seed']}")
    print(f"   findings: {len(submission['findings'])}  "
          f"leads_not_pursued: {len(submission['leads_not_pursued'])}")
    print(f"   llm_calls: {meta['llm_calls']}  wall_clock_seconds: {meta['wall_clock_seconds']}")


if __name__ == "__main__":
    main()
