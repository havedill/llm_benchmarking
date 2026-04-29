# llm_benchmarking

Thin local wrapper around [`geerlingguy/ai-benchmarks`](https://github.com/geerlingguy/ai-benchmarks), using upstream `obench.sh` for Ollama throughput runs.

## What This Repo Does

- Uses upstream benchmark scripts (no custom benchmark engine).
- Stores local run artifacts in this repo for repeatability:
  - `results.jsonl`
  - `run_manifest.json`
- Tracks system/tuning metadata with each run.

## Quickstart

1. Make sure Ollama is installed and can run your model:
   - `ollama run llama3.2:3b`
2. Run benchmark(s):
   - `python3 scripts/run_geerling_bench.py --models "llama3.2:3b" --count 3`
   - `python3 scripts/run_geerling_bench.py --models "llama3.2:3b,qwen2.5-coder:7b" --count 3`

The script clones/updates upstream `ai-benchmarks` under `tools/ai-benchmarks` and executes `obench.sh` directly.

## Output Layout

- `runs/run_YYYYMMDD_HHMMSSZ/`
  - `results.jsonl` (one record per model iteration)
  - `run_manifest.json` (model provenance + system/tuning metadata)
  - `<model>.log` (raw `obench.sh` output per model)
- `runs/latest` symlink points to the newest run.
- `reports/results_table.md` is the tracked markdown summary table.

## Update Tracking Table

Rebuild the markdown table from local run artifacts:

- `bash scripts/update_results_table.sh`

## Notes

- To pin upstream exactly, use `--no-update` and manage `tools/ai-benchmarks` commit yourself.
- Use `docs/hardware.md` to keep a stable hardware/tuning profile for fair comparisons.
