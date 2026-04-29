# Contributing

## Ground Rules

- Keep benchmark execution logic in `scripts/run_benchmarks.py`.
- Keep report generation logic in `scripts/build_reports.py`.
- Do not commit hand-edited run artifacts.

## Required Run Metadata

Every submitted run must include:

- model provenance:
  - `ollama_model`
  - `huggingface_repo`
  - `huggingface_revision`
  - `model_digest`
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
2. Run report builder against that run.
3. Include generated `docs/results/run_...md` and `reports/*.png`.
4. Document any hardware/OS changes affecting performance.
