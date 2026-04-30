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
   - `python3 scripts/run_geerling_bench.py --models "llama3.2:3b" --count 3 --comment "CPU governor set to performance"`

The script clones/updates upstream `ai-benchmarks` under `tools/ai-benchmarks` and executes `obench.sh` directly.

Use `--comment` to annotate run-specific tuning or configuration changes so they are visible in result tables.

## Output Layout

- `runs/run_YYYYMMDD_HHMMSSZ/`
  - `results.jsonl` (one record per model iteration)
  - `run_manifest.json` (model provenance + system/tuning metadata)
  - `<model>.log` (raw `obench.sh` output per model)
- `runs/latest` symlink points to the newest run.
- `reports/results_table.md` is the tracked summary; `bash scripts/update_results_table.sh` refreshes that file and the `## Results Table` section in this README (between `RESULTS_TABLE` markers).

## Results Table

<!-- RESULTS_TABLE_BEGIN -->
Generated from local `runs/` artifacts via `scripts/update_results_table.sh`.

| Run ID | Created UTC | Model | Comment | Iterations | Mean tok/s | Min tok/s | Max tok/s |
|---|---|---|---|---:|---:|---:|---:|
| run_20260430_135657Z | 2026-04-30 13:56:57Z | llama3.2:3b | better thermal paste + huge fan | 2 | 10.06 | 9.95 | 10.18 |
| run_20260430_140207Z | 2026-04-30 14:02:07Z | llama3.2:3b | better thermal paste + huge fan | 5 | 9.93 | 9.82 | 10.07 |
| run_20260429_141602Z | 2026-04-29 14:16:02Z | llama3.2:3b |  | 10 | 9.06 | 8.78 | 9.23 |
| run_20260429_151648Z | 2026-04-29 15:16:48Z | iambpn/nanbeige4.1-3B |  | 1 | 4.87 | 4.87 | 4.87 |
| run_20260429_154744Z | 2026-04-29 15:47:44Z | iambpn/nanbeige4.1-3B |  | 10 | 4.63 | 4.41 | 4.85 |
| run_20260430_140207Z | 2026-04-30 14:02:07Z | qwen2.5-coder:7b | better thermal paste + huge fan | 5 | 4.63 | 4.13 | 4.79 |
| run_20260429_142619Z | 2026-04-29 14:26:19Z | qwen2.5-coder:7b |  | 10 | 4.31 | 4.25 | 4.39 |
| run_20260430_140207Z | 2026-04-30 14:02:07Z | granite4.1:8b | better thermal paste + huge fan | 5 | 4.06 | 4.03 | 4.09 |
| run_20260430_103134Z | 2026-04-30 10:31:34Z | granite4.1:8b |  | 10 | 3.92 | 3.88 | 3.95 |
| run_20260430_131024Z | 2026-04-30 13:10:24Z | granite4.1:8b |  | 1 | 3.89 | 3.89 | 3.89 |
<!-- RESULTS_TABLE_END -->

Refresh this table after new runs:

- `bash scripts/update_results_table.sh`

## Notes

- To pin upstream exactly, use `--no-update` and manage `tools/ai-benchmarks` commit yourself.
- Use `docs/hardware.md` to keep a stable hardware/tuning profile for fair comparisons.
