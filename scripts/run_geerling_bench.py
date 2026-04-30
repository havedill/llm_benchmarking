#!/usr/bin/env python3
import argparse
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


UPSTREAM_REPO = "https://github.com/geerlingguy/ai-benchmarks.git"
UPSTREAM_DIR = Path("tools/ai-benchmarks")
EVAL_RATE_RE = re.compile(r"eval rate:\s+([0-9]+(?:\.[0-9]+)?)")


def run_cmd(cmd):
    return subprocess.check_output(cmd, text=True).strip()


def run_cmd_optional(cmd):
    try:
        return run_cmd(cmd)
    except Exception:
        return None


def ensure_upstream(update: bool):
    if not UPSTREAM_DIR.exists():
        UPSTREAM_DIR.parent.mkdir(parents=True, exist_ok=True)
        subprocess.check_call(["git", "clone", UPSTREAM_REPO, str(UPSTREAM_DIR)])
        return
    if update:
        subprocess.check_call(["git", "-C", str(UPSTREAM_DIR), "pull", "--ff-only"])


def detect_system():
    mem_total = None
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                parts = line.split()
                if len(parts) >= 2:
                    mem_total = int(parts[1]) * 1024
                break

    cpu_model = None
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text(encoding="utf-8").splitlines():
            if "model name" in line:
                cpu_model = line.split(":", 1)[1].strip()
                break

    return {
        "hostname": socket.gethostname(),
        "os_name": platform.system(),
        "os_release": platform.version(),
        "kernel": platform.release(),
        "cpu_model": cpu_model,
        "logical_cores": os.cpu_count(),
        "memory_total_bytes": mem_total,
    }


def detect_os_tuning():
    governor = run_cmd_optional(
        ["bash", "-lc", "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"]
    )
    tuned_active = run_cmd_optional(["tuned-adm", "active"])
    return {
        "tuned_active_profile": tuned_active,
        "governor": governor,
        "notes": "",
    }


def parse_eval_rates(output: str):
    return [float(match.group(1)) for match in EVAL_RATE_RE.finditer(output)]


def run_obench_streaming(cmd, model: str, model_idx: int, model_total: int, count: int):
    rates = []
    log_lines = []
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    for line in process.stdout:
        log_lines.append(line)
        sys.stdout.write(line)
        sys.stdout.flush()
        match = EVAL_RATE_RE.search(line)
        if match:
            rate = float(match.group(1))
            rates.append(rate)
            progress(
                f"Model {model_idx}/{model_total} loop {len(rates)}/{count}: "
                f"{model} ({rate:.2f} tok/s)"
            )
    returncode = process.wait()
    return returncode, "".join(log_lines), rates


def parse_models(raw: str):
    return [m.strip() for m in raw.split(",") if m.strip()]


def require_cmd(name: str, reason: str):
    if shutil.which(name) is None:
        raise SystemExit(f"Missing required command '{name}': {reason}")


def progress(stage: str):
    print(f"[progress] {stage}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", required=True, help="Comma-separated Ollama model tags")
    parser.add_argument("--count", type=int, default=3, help="obench.sh --count per model")
    parser.add_argument("--no-update", action="store_true", help="Skip git pull on existing upstream clone")
    parser.add_argument(
        "--ollama-bin",
        default=None,
        help="Optional command path to pass through to obench.sh --ollama-bin",
    )
    parser.add_argument(
        "--comment",
        default="",
        help="Optional run note to capture tuning/config changes for result tables",
    )
    parser.add_argument("--output-root", default="runs", help="Root output directory")
    args = parser.parse_args()

    progress("Stage 1/5: parsing model list")
    models = parse_models(args.models)
    if not models:
        raise SystemExit("No models provided.")

    # obench.sh shells out to these tools directly.
    progress("Stage 2/5: checking required commands")
    require_cmd("ollama", "Install Ollama and ensure it is in PATH.")
    require_cmd("bc", "Install bc (e.g. sudo apt-get install -y bc).")

    progress("Stage 3/5: preparing upstream benchmark scripts")
    ensure_upstream(update=(not args.no_update))
    obench_script = UPSTREAM_DIR / "obench.sh"
    if not obench_script.exists():
        raise SystemExit(f"Missing upstream benchmark script: {obench_script}")

    now = datetime.now(timezone.utc)
    run_id = now.strftime("run_%Y%m%d_%H%M%SZ")
    run_dir = Path(args.output_root) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    upstream_commit = run_cmd_optional(["git", "-C", str(UPSTREAM_DIR), "rev-parse", "HEAD"])

    manifest = {
        "run_id": run_id,
        "created_at_utc": now.isoformat(),
        "comment": args.comment,
        "runner": "geerlingguy/ai-benchmarks obench.sh",
        "upstream_repo": UPSTREAM_REPO,
        "upstream_commit": upstream_commit,
        "system": detect_system(),
        "os_tuning": detect_os_tuning(),
        "model_provenance": [
            {
                "ollama_model": model,
                "huggingface_repo": None,
                "huggingface_revision": None,
                "digest": None,
                "quantization": None,
            }
            for model in models
        ],
    }

    results_path = run_dir / "results.jsonl"
    progress(f"Stage 4/5: running benchmark loop for {len(models)} model(s)")
    with results_path.open("w", encoding="utf-8") as out:
        for idx, model in enumerate(models, start=1):
            progress(f"Model {idx}/{len(models)} START: {model}")
            cmd = [str(obench_script), "--model", model, "--count", str(args.count)]
            if args.ollama_bin:
                cmd.extend(["--ollama-bin", args.ollama_bin])
            returncode, merged_output, rates = run_obench_streaming(
                cmd=cmd,
                model=model,
                model_idx=idx,
                model_total=len(models),
                count=args.count,
            )
            (run_dir / f"{model.replace('/', '_').replace(':', '_')}.log").write_text(
                merged_output, encoding="utf-8"
            )
            if returncode != 0:
                raise RuntimeError(f"Benchmark failed for model '{model}'. See run log in {run_dir}.")

            progress(f"Model {idx}/{len(models)} DONE: {model} ({len(rates)} eval-rate row(s))")
            for i, rate in enumerate(rates, start=1):
                record = {
                    "run_id": run_id,
                    "benchmark": "obench.sh",
                    "model": model,
                    "iteration": i,
                    "eval_rate_tokens_per_sec": rate,
                }
                out.write(json.dumps(record) + "\n")

    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    latest_link = Path(args.output_root) / "latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    latest_link.symlink_to(run_id)
    progress("Stage 5/5: finalized run artifacts")
    print(f"Wrote benchmark artifacts to: {run_dir}")


if __name__ == "__main__":
    main()
