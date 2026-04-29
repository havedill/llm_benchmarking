# Contributing

## Ground Rules

- Use upstream benchmark logic from `geerlingguy/ai-benchmarks` (invoked by `scripts/run_geerling_bench.py`).
- Keep run execution separate from report generation.
- Do not commit hand-edited run artifacts.

## Required Run Metadata

Every submitted run must include:

- model provenance:
  - `ollama_model`
  - `huggingface_repo` (nullable for Ollama-only runs)
  - `huggingface_revision` (nullable for Ollama-only runs)
  - `digest` (nullable when not provided by upstream toolchain)
  - `quantization`
- system snapshot:
  - OS/kernel/CPU/memory
- OS tuning snapshot:
  - whether `tuned` is installed
  - active tuned profile
  - CPU governor
  - notes for manual tweaks

## Result Submission

1. Run benchmark and produce `runs/run_...`.
2. Verify both `results.jsonl` and `run_manifest.json` exist.
3. Attach or summarize raw logs from the run directory as needed.
4. Document any hardware/OS changes affecting performance.
