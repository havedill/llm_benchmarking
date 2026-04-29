#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def read_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_placeholder_png(path: Path):
    # 1x1 transparent PNG
    png_bytes = bytes.fromhex(
        "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
        "0000000A49444154789C6360000002000154A24F5A0000000049454E44AE426082"
    )
    path.write_bytes(png_bytes)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, help="Path to run directory or runs/latest")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    results = read_jsonl(run_dir / "results.jsonl")
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))

    count = len(results)
    mean_score = sum(r["score"] for r in results) / count if count else 0.0
    mean_latency = sum(r["latency_ms"] for r in results) / count if count else 0.0
    total_tokens = sum(r["total_tokens_est"] for r in results)

    report_summary = {
        "run_id": manifest["run_id"],
        "task_count": count,
        "mean_score": mean_score,
        "mean_latency_ms": mean_latency,
        "total_tokens_est": total_tokens,
        "model": manifest["model"]["ollama_model"],
        "os_tuning": manifest.get("os_tuning", {}),
    }
    (run_dir / "report_summary.json").write_text(json.dumps(report_summary, indent=2), encoding="utf-8")

    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    chart_path = reports_dir / f"{manifest['run_id']}_score_latency.png"
    write_placeholder_png(chart_path)

    docs_results = Path("docs/results")
    docs_results.mkdir(parents=True, exist_ok=True)
    md_path = docs_results / f"{manifest['run_id']}.md"
    md = f"""# Run {manifest['run_id']}

- Model: `{manifest['model']['ollama_model']}`
- Tasks: {count}
- Mean score: {mean_score:.3f}
- Mean latency (ms): {mean_latency:.1f}
- Estimated total tokens: {total_tokens}
- Tuned profile: `{manifest.get('os_tuning', {}).get('tuned_active_profile')}`
- Governor: `{manifest.get('os_tuning', {}).get('governor')}`

![score-latency](../../reports/{chart_path.name})
"""
    md_path.write_text(md, encoding="utf-8")
    print(f"Wrote report summary: {md_path}")


if __name__ == "__main__":
    main()
