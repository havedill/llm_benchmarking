#!/usr/bin/env python3
import argparse
import json
import os
import platform
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
        return out if out else None
    except Exception:
        return None


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
    tuned_active = run_cmd(["tuned-adm", "active"])
    governor = run_cmd(["bash", "-lc", "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"])
    return {
        "tuned_installed": run_cmd(["bash", "-lc", "command -v tuned-adm >/dev/null && echo yes"]) == "yes",
        "tuned_active_profile": tuned_active,
        "governor": governor,
        "notes": "",
    }


def estimate_tokens(text: str):
    # Simple deterministic estimate for phase-1 scaffolding.
    return max(1, len(text) // 4)


def call_ollama(model: str, prompt: str):
    cmd = ["ollama", "run", model, prompt]
    return subprocess.check_output(cmd, text=True, timeout=120)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config_path = Path(args.config)
    cfg = read_json(config_path)
    tasks = read_json(Path(cfg["tasks_file"]))

    now = datetime.now(timezone.utc)
    run_id = now.strftime("run_%Y%m%d_%H%M%SZ")
    run_dir = Path(cfg.get("output_root", "runs")) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "run_id": run_id,
        "created_at_utc": now.isoformat(),
        "config_path": str(config_path),
        "benchmark_version": cfg["benchmark_version"],
        "system": detect_system(),
        "os_tuning": detect_os_tuning(),
        "model": cfg["model"],
        "dry_run": args.dry_run,
    }

    results_path = run_dir / "results.jsonl"
    success_count = 0
    total_score = 0.0

    with results_path.open("w", encoding="utf-8") as out:
        for task in tasks:
            prompt = task["prompt"]
            if args.dry_run:
                response = f"DRY_RUN_RESPONSE for {task['task_id']}"
                latency_ms = 25
            else:
                start = datetime.now(timezone.utc)
                response = call_ollama(cfg["model"]["ollama_model"], prompt)
                end = datetime.now(timezone.utc)
                latency_ms = int((end - start).total_seconds() * 1000)

            prompt_toks = estimate_tokens(prompt)
            completion_toks = estimate_tokens(response)
            score = 1.0 if response else 0.0
            success = bool(response)
            success_count += 1 if success else 0
            total_score += score

            rec = {
                "run_id": run_id,
                "task_id": task["task_id"],
                "model_name": cfg["model"]["ollama_model"],
                "success": success,
                "latency_ms": latency_ms,
                "prompt_tokens_est": prompt_toks,
                "completion_tokens_est": completion_toks,
                "total_tokens_est": prompt_toks + completion_toks,
                "response_chars": len(response),
                "score": score,
                "errors": [],
            }
            out.write(json.dumps(rec) + "\n")

    task_count = len(tasks)
    manifest["summary"] = {
        "task_count": task_count,
        "success_count": success_count,
        "mean_score": (total_score / task_count) if task_count else 0.0,
    }

    with (run_dir / "run_manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    latest_link = Path(cfg.get("output_root", "runs")) / "latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    latest_link.symlink_to(run_id)

    print(f"Wrote run artifacts to: {run_dir}")


if __name__ == "__main__":
    main()
