# Methodology

This document defines the benchmark contract for phase 1.

## Principles

- Focus on coding-quality tasks.
- Keep task set versioned and stable.
- Separate execution from report generation.
- Preserve model provenance and system state for every run.

## Task Schema

Each task JSON object must include:

- `task_id`: unique stable identifier.
- `title`: short name.
- `prompt`: full benchmark prompt.
- `category`: coding category (bugfix/refactor/feature/test).
- `difficulty`: easy/medium/hard.
- `expected_signals`: list of grading signals.

## Run Metadata Schema

Each run writes metadata including:

- `run_id`: deterministic timestamp-based ID.
- `created_at_utc`: ISO timestamp.
- `config_path`: config used for the run.
- `benchmark_version`: version of the task bundle.
- `system`:
  - `hostname`
  - `os_name`
  - `os_release`
  - `kernel`
  - `cpu_model`
  - `logical_cores`
  - `memory_total_bytes`
- `os_tuning`:
  - `tuned_installed`: boolean
  - `tuned_active_profile`: string or `null`
  - `governor`: string or `null`
  - `notes`: free-form text
- `model`:
  - `ollama_model`
  - `huggingface_repo`
  - `huggingface_revision`
  - `model_digest`
  - `quantization`

## Per-Task Result Schema

Each result record contains:

- `run_id`
- `task_id`
- `model_name`
- `success`: boolean
- `latency_ms`
- `prompt_tokens_est`
- `completion_tokens_est`
- `total_tokens_est`
- `response_chars`
- `score`: 0.0 to 1.0
- `errors`: list

## Output Files

Per run directory:

- `results.jsonl`: one JSON object per task result.
- `run_manifest.json`: run metadata and aggregate summary.
- `report_summary.json`: compact aggregate written by report script.

## Scoring

Initial scoring is deterministic and simple:

- base score from rubric signals in task definition.
- penalties for missing required output signals.
- report script computes aggregate mean/median and simple trends.

This can be extended later without changing raw result compatibility.
