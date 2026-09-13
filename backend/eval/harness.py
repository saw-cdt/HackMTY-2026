"""
Fase 6 -- la metrica.

Corre el ciclo completo (generador -> detectores -> investigador ->
retador -> validador) sobre una lista de seeds, compara el
submission.json que produce cada corrida contra su truth_seedNNN.json,
y escribe una tabla con recall, falsas acusaciones, reconciliacion de
pesos y costo -- una fila por seed, mas un TOTAL.

Junto con src/generate/, este es el UNICO archivo del proyecto que
puede importar o mencionar "ground_truth" / leer truth_seedNNN.json.
src/tools/ y src/agent/ nunca lo tocan -- eso es lo que
`make check-isolation` verifica (solo barre src/, por eso este archivo
en eval/ no lo hace fallar).

Uso:
    python -m eval.harness --seeds tuning  --out out/results_tuning.csv
    python -m eval.harness --seeds report  --out out/results_report.csv
    python -m eval.harness --seeds 1-3,7   --out out/results_dev.csv --mode replay

Seeds de tuning: 1-10. Seeds de reporte: 101-110. No se mezclan: los
de reporte no se usan durante el desarrollo (ver CLAUDE.md).
"""
import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

_EVAL_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _EVAL_DIR.parent
_SRC_DIR = _BACKEND_DIR / "src"

sys.path.insert(0, str(_SRC_DIR))
sys.path.insert(0, str(_SRC_DIR / "generate"))

import cli as cli_module  # noqa: E402  (inserta a su vez src/tools y src/agent)
import estate as estate_module  # noqa: E402

TUNING_SEEDS = list(range(1, 11))
REPORT_SEEDS = list(range(101, 111))

CSV_COLUMNS = [
    "seed", "schemes_planted", "schemes_found", "recall_pct",
    "decoys_planted", "decoys_accused", "false_accusation_rate_pct",
    "peso_claimed", "peso_actual", "peso_reconciles",
    "llm_calls", "mxn_cost", "wall_clock_s",
]

PESO_TOLERANCE = 0.02  # misma tolerancia del 2% que usan validator.py y validate_format.py


def parse_seeds(spec: str) -> list[int]:
    """"1-10" -> [1..10]. "1,3,7-9" -> [1,3,7,8,9]. "tuning"/"report" ->
    los rangos fijos de arriba."""
    spec = spec.strip().lower()
    if spec == "tuning":
        return list(TUNING_SEEDS)
    if spec == "report":
        return list(REPORT_SEEDS)

    seeds: list[int] = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            lo, hi = chunk.split("-", 1)
            seeds.extend(range(int(lo), int(hi) + 1))
        else:
            seeds.append(int(chunk))
    return seeds


def ensure_estate(seed: int, estates_dir: Path, force: bool = False) -> tuple[Path, Path]:
    """Devuelve (estate_path, truth_path) para `seed`, generandolos con
    estate_module.build_estate() si no existen todavia (o si force=True).
    Determinista por seed: regenerar no cambia el contenido."""
    estate_path = estates_dir / f"estate_seed{seed:03d}.db"
    truth_path = estates_dir / f"truth_seed{seed:03d}.json"

    if force or not estate_path.exists() or not truth_path.exists():
        estate_module.build_estate(seed, estates_dir)

    return estate_path, truth_path


def _entities_overlap(finding_entities: list, scheme_entities: list) -> bool:
    return bool(set(finding_entities) & set(scheme_entities))


def score_seed(truth: dict, submission: dict) -> dict:
    """Compara un submission.json contra su truth.json. No decide nada
    sobre el agente -- solo mide. Regla de match: un scheme sembrado
    cuenta como encontrado si existe un finding del mismo scheme_type
    que comparte al menos una entidad con el. Una acusacion a un decoy
    cuenta como falsa acusacion si algun finding lo incluye en
    entities, sin importar el scheme_type que le haya puesto el agente.

    Simplificacion conocida: si dos schemes DEL MISMO TIPO comparten una
    entidad (esquemas entrelazados), un mismo finding podria hacer match
    con ambos. No ha pasado en los seeds usados hasta ahora; documentado
    aqui en vez de resuelto con asignacion biunivoca, que no vale la
    complejidad para un caso que no se ha observado.

    Un scheme puede tener MAS de un finding que le haga match -- el
    investigador puede fragmentar un solo scheme sembrado (ej.
    revenue_inflation con varias facturas) en un finding por factura en
    vez de uno agregado. peso_claimed suma TODOS los findings que le
    hacen match a un scheme, no solo el primero, para no subestimar el
    monto reclamado en ese caso.
    """
    schemes = truth.get("schemes", [])
    decoys = truth.get("decoys", [])
    findings = submission.get("findings", [])

    matches = []
    for scheme in schemes:
        matched = [
            f for f in findings
            if f.get("scheme_type") == scheme.get("type")
            and _entities_overlap(f.get("entities", []), scheme.get("entities", []))
        ]
        matches.append((scheme, matched))

    schemes_planted = len(schemes)
    schemes_found = sum(1 for _, m in matches if m)

    decoys_planted = len(decoys)
    decoys_accused = sum(
        1 for decoy in decoys
        if any(decoy.get("entity") in f.get("entities", []) for f in findings)
    )

    peso_actual = round(sum(scheme["peso_amount"] for scheme, m in matches if m), 2)
    peso_claimed = round(
        sum(sum(f["peso_amount"] for f in m) for scheme, m in matches if m), 2
    )
    peso_reconciles = (
        peso_claimed == 0 if peso_actual == 0
        else abs(peso_claimed - peso_actual) <= PESO_TOLERANCE * peso_actual
    )

    by_type: dict = {}
    for scheme, m in matches:
        t = scheme["type"]
        planted, found = by_type.get(t, (0, 0))
        by_type[t] = (planted + 1, found + (1 if m else 0))

    return {
        "schemes_planted": schemes_planted,
        "schemes_found": schemes_found,
        "recall_pct": round(100 * schemes_found / schemes_planted, 1) if schemes_planted else None,
        "decoys_planted": decoys_planted,
        "decoys_accused": decoys_accused,
        "false_accusation_rate_pct": (
            round(100 * decoys_accused / decoys_planted, 1) if decoys_planted else 0.0
        ),
        "peso_claimed": peso_claimed,
        "peso_actual": peso_actual,
        "peso_reconciles": peso_reconciles,
        "by_type": by_type,
    }


def _merge_by_type(totals: dict, by_type: dict) -> None:
    for t, (planted, found) in by_type.items():
        p, f = totals.get(t, (0, 0))
        totals[t] = (p + planted, f + found)


def _totals_row(rows: list[dict]) -> dict:
    schemes_planted = sum(r["schemes_planted"] for r in rows)
    schemes_found = sum(r["schemes_found"] for r in rows)
    decoys_planted = sum(r["decoys_planted"] for r in rows)
    decoys_accused = sum(r["decoys_accused"] for r in rows)

    return {
        "seed": "TOTAL",
        "schemes_planted": schemes_planted,
        "schemes_found": schemes_found,
        "recall_pct": round(100 * schemes_found / schemes_planted, 1) if schemes_planted else None,
        "decoys_planted": decoys_planted,
        "decoys_accused": decoys_accused,
        "false_accusation_rate_pct": (
            round(100 * decoys_accused / decoys_planted, 1) if decoys_planted else 0.0
        ),
        "peso_claimed": round(sum(r["peso_claimed"] for r in rows), 2),
        "peso_actual": round(sum(r["peso_actual"] for r in rows), 2),
        "peso_reconciles": all(r["peso_reconciles"] for r in rows) if rows else None,
        # promedio, no suma -- lo que se pide en el paso de Fase 6 es el
        # costo TIPICO de una corrida, no el costo de correr todo el lote.
        "llm_calls": round(statistics.fmean(r["llm_calls"] for r in rows), 1) if rows else 0,
        "mxn_cost": round(statistics.fmean(r["mxn_cost"] for r in rows), 4) if rows else 0.0,
        "wall_clock_s": round(statistics.fmean(r["wall_clock_s"] for r in rows), 3) if rows else 0.0,
    }


def run_harness(seeds: list[int], estates_dir: Path, model: str, mode: str,
                 cache_dir: str | None, ollama_url: str | None,
                 force_regenerate: bool = False) -> tuple[list[dict], dict]:
    """Corre el ciclo completo para cada seed y devuelve (filas, totales_por_tipo)."""
    rows = []
    by_type_totals: dict = {}

    for seed in seeds:
        estate_path, truth_path = ensure_estate(seed, estates_dir, force=force_regenerate)
        truth = json.loads(truth_path.read_text(encoding="utf-8"))

        submission_path = estates_dir / f"submission_seed{seed:03d}.json"
        submission = cli_module.run(
            estate_path, submission_path, model=model,
            cache_dir=cache_dir, mode=mode, ollama_url=ollama_url, seed=seed,
        )

        score = score_seed(truth, submission)
        by_type = score.pop("by_type")
        _merge_by_type(by_type_totals, by_type)

        meta = submission["run_metadata"]
        rows.append({
            "seed": seed,
            **score,
            "llm_calls": meta["llm_calls"],
            "mxn_cost": meta["mxn_cost"],
            "wall_clock_s": meta["wall_clock_seconds"],
        })

    return rows, by_type_totals


def write_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in CSV_COLUMNS})


def write_by_type_csv(by_type_totals: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["scheme_type", "planted", "found", "recall_pct"])
        for scheme_type in sorted(by_type_totals):
            planted, found = by_type_totals[scheme_type]
            recall = round(100 * found / planted, 1) if planted else ""
            writer.writerow([scheme_type, planted, found, recall])


def print_summary(rows: list[dict], totals: dict, by_type_totals: dict) -> None:
    print(f"{'seed':>6}  {'planted':>7}  {'found':>5}  {'recall%':>7}  "
          f"{'decoys':>6}  {'accused':>7}  {'false_acc%':>10}  "
          f"{'reconciles':>10}  {'llm':>4}  {'wall_s':>7}")
    for row in rows:
        print(f"{row['seed']:>6}  {row['schemes_planted']:>7}  {row['schemes_found']:>5}  "
              f"{row['recall_pct'] if row['recall_pct'] is not None else '-':>7}  "
              f"{row['decoys_planted']:>6}  {row['decoys_accused']:>7}  "
              f"{row['false_accusation_rate_pct']:>10}  {str(row['peso_reconciles']):>10}  "
              f"{row['llm_calls']:>4}  {row['wall_clock_s']:>7}")
    print(f"{totals['seed']:>6}  {totals['schemes_planted']:>7}  {totals['schemes_found']:>5}  "
          f"{totals['recall_pct'] if totals['recall_pct'] is not None else '-':>7}  "
          f"{totals['decoys_planted']:>6}  {totals['decoys_accused']:>7}  "
          f"{totals['false_accusation_rate_pct']:>10}  {str(totals['peso_reconciles']):>10}  "
          f"{totals['llm_calls']:>4}  {totals['wall_clock_s']:>7}")

    print("\npor tipo de esquema:")
    print(f"{'scheme_type':>20}  {'planted':>7}  {'found':>5}  {'recall%':>7}")
    for scheme_type in sorted(by_type_totals):
        planted, found = by_type_totals[scheme_type]
        recall = round(100 * found / planted, 1) if planted else "-"
        print(f"{scheme_type:>20}  {planted:>7}  {found:>5}  {recall:>7}")


def main():
    parser = argparse.ArgumentParser(description="The Forensic Auditor -- Fase 6, la metrica")
    parser.add_argument("--seeds", required=True,
                         help="'tuning' (1-10), 'report' (101-110), o rango/lista, ej. '1-5,8'")
    parser.add_argument("--estates-dir", default=str(_BACKEND_DIR / "out"),
                         help="donde viven/se generan estate_seedNNN.db y truth_seedNNN.json")
    parser.add_argument("--out", required=True, help="ruta del CSV de resultados")
    parser.add_argument("--model", default=cli_module.DEFAULT_MODEL)
    parser.add_argument("--mode", choices=["record", "replay"], default="record")
    parser.add_argument("--cache-dir", default=None,
                         help="cache de prompts compartido entre seeds (default: <estates-dir>/.llm_cache)")
    parser.add_argument("--ollama-url", default=None)
    parser.add_argument("--regenerate", action="store_true",
                         help="regenera estate+truth aunque ya existan (deben salir identicos: mismo seed)")
    args = parser.parse_args()

    seeds = parse_seeds(args.seeds)
    estates_dir = Path(args.estates_dir)
    estates_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = args.cache_dir or str(estates_dir / ".llm_cache")

    rows, by_type_totals = run_harness(
        seeds, estates_dir, model=args.model, mode=args.mode,
        cache_dir=cache_dir, ollama_url=args.ollama_url,
        force_regenerate=args.regenerate,
    )
    totals = _totals_row(rows)

    out_path = Path(args.out)
    write_csv(rows + [totals], out_path)
    write_by_type_csv(by_type_totals, out_path.with_name(out_path.stem + "_by_type.csv"))

    print_summary(rows, totals, by_type_totals)
    print(f"\nOK -> {out_path}")
    print(f"OK -> {out_path.with_name(out_path.stem + '_by_type.csv')}")


if __name__ == "__main__":
    main()
