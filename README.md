# llm_benchmarking

Local, repeatable LLM benchmark suite for coding-quality and token-oriented metrics on your hardware using `ollama`, with human-readable Markdown summaries and generated charts.

## Phase 1 Scope

- Benchmark coding tasks only.
- Run local models served through `ollama`.
- Track Hugging Face provenance metadata for each model.
- Keep execution and reporting separate.

## Repository Layout

- `benchmarks/tasks/`: coding tasks and scoring metadata.
- `benchmarks/configs/`: run configs and model provenance fields.
- `scripts/run_benchmarks.py`: run execution only (writes raw artifacts).
- `scripts/build_reports.py`: reporting only (reads artifacts, writes charts/docs).
- `runs/`: raw artifacts (`jsonl` and summaries) grouped by run id.
- `reports/`: generated images.
- `docs/results/`: generated human-readable result pages.

## Quickstart

1. Install and run `ollama`.
2. Pull a local model in ollama (example):
   - `ollama pull qwen2.5-coder:7b`
3. Run a dry benchmark:
   - `python3 scripts/run_benchmarks.py --config benchmarks/configs/local_baseline.json --dry-run`
4. Build report artifacts:
   - `python3 scripts/build_reports.py --run-dir runs/latest`

## Reproducibility Rules

- Every run must include hardware, OS, and tuning metadata.
- Raw run artifacts are source-of-truth; reports are derived outputs.
- Do not mix benchmark execution and report generation in the same script.

## Current Status

Bootstrap scaffolding is in place. Use dry-run first to verify pipeline, then run with real models.

## Verification

Dry-run pipeline executed successfully:

- Command: `python3 scripts/run_benchmarks.py --config benchmarks/configs/local_baseline.json --dry-run`
- Command: `python3 scripts/build_reports.py --run-dir runs/latest`
- Artifacts:
  - `runs/run_20260429_114512Z/results.jsonl`
  - `runs/run_20260429_114512Z/run_manifest.json`
  - `runs/run_20260429_114512Z/report_summary.json`
  - `docs/results/run_20260429_114512Z.md`
  - `reports/run_20260429_114512Z_score_latency.png`
