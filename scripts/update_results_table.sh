#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNS_DIR="${ROOT_DIR}/runs"
OUTPUT_MD="${ROOT_DIR}/reports/results_table.md"

if [[ ! -d "${RUNS_DIR}" ]]; then
  echo "No runs directory found at ${RUNS_DIR}"
  exit 1
fi

mkdir -p "$(dirname "${OUTPUT_MD}")"

python3 - "${RUNS_DIR}" "${OUTPUT_MD}" <<'PY'
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import re

runs_dir = Path(sys.argv[1])
output_md = Path(sys.argv[2])

rows = []

for run_dir in sorted(runs_dir.glob("run_*")):
    if not run_dir.is_dir():
        continue

    results_path = run_dir / "results.jsonl"
    manifest_path = run_dir / "run_manifest.json"
    if not results_path.exists():
        continue

    created_short = run_dir.name
    run_name = run_dir.name
    if run_name.startswith("run_") and len(run_name) >= len("run_YYYYMMDD_HHMMSSZ"):
        # Fallback when run_manifest.json is missing.
        # Example: run_20260429_141602Z -> 2026-04-29 14:16:02Z
        date_part = run_name[4:12]
        time_part = run_name[13:19]
        if date_part.isdigit() and time_part.isdigit():
            created_short = (
                f"{date_part[0:4]}-{date_part[4:6]}-{date_part[6:8]} "
                f"{time_part[0:2]}:{time_part[2:4]}:{time_part[4:6]}Z"
            )
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        created = manifest.get("created_at_utc", "")
        if created:
            try:
                created_short = datetime.fromisoformat(created).strftime("%Y-%m-%d %H:%M:%SZ")
            except ValueError:
                pass

    by_model = defaultdict(list)
    for raw in results_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        rec = json.loads(raw)
        model = rec.get("model", "unknown")
        rate = rec.get("eval_rate_tokens_per_sec")
        if isinstance(rate, (int, float)):
            by_model[model].append(float(rate))

    for model, rates in by_model.items():
        if not rates:
            continue
        mean_rate = sum(rates) / len(rates)
        rows.append(
            {
                "run_id": run_dir.name,
                "created": created_short,
                "model": model,
                "iterations": len(rates),
                "mean": mean_rate,
                "min": min(rates),
                "max": max(rates),
            }
        )

rows.sort(key=lambda r: r["mean"], reverse=True)


def normalize_created(created: str, run_id: str) -> str:
    if "-" in created and ":" in created:
        return created
    m = re.match(r"^run_(\d{8})_(\d{6})Z$", run_id)
    if not m:
        return created
    date_part, time_part = m.groups()
    return (
        f"{date_part[0:4]}-{date_part[4:6]}-{date_part[6:8]} "
        f"{time_part[0:2]}:{time_part[2:4]}:{time_part[4:6]}Z"
    )

lines = []
lines.append("# Benchmark Results Table")
lines.append("")
lines.append("Generated from local `runs/` artifacts via `scripts/update_results_table.sh`.")
lines.append("")
lines.append("| Run ID | Created UTC | Model | Iterations | Mean tok/s | Min tok/s | Max tok/s |")
lines.append("|---|---|---|---:|---:|---:|---:|")

if rows:
    for row in rows:
        created_display = normalize_created(row["created"], row["run_id"])
        lines.append(
            f"| {row['run_id']} | {created_display} | {row['model']} | {row['iterations']} | "
            f"{row['mean']:.2f} | {row['min']:.2f} | {row['max']:.2f} |"
        )
else:
    lines.append("| _no runs found_ | - | - | - | - | - | - |")

lines.append("")
output_md.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {output_md}")
PY
