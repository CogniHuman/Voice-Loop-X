#!/usr/bin/env python3
"""
Profile analysis utilities for VoiceLoop-X research workflows.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class StageSnapshot:
    name: str
    mean_ms: float
    p95_ms: float
    percentage: float
    samples: int


def _load_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _safe_stage(report: dict[str, Any], stage: str) -> StageSnapshot:
    data = report.get("stages", {}).get(stage, {})
    return StageSnapshot(
        name=stage,
        mean_ms=float(data.get("mean_ms", 0.0) or 0.0),
        p95_ms=float(data.get("p95_ms", 0.0) or 0.0),
        percentage=float(data.get("percentage", 0.0) or 0.0),
        samples=int(data.get("samples", 0) or 0),
    )


def _summary_metric(report: dict[str, Any], metric_key: str, fallback_stage: str | None = None) -> float:
    summary = report.get("summary", {})
    value = summary.get(metric_key)
    if value is not None:
        return float(value)
    if fallback_stage:
        return float(report.get("stages", {}).get(fallback_stage, {}).get("mean_ms", 0.0) or 0.0)
    return 0.0


def _pct_change(before: float, after: float) -> float:
    if before == 0:
        return 0.0
    return ((after - before) / before) * 100.0


def compare_reports(
    baseline_path: str | Path,
    candidate_path: str | Path,
    *,
    label_baseline: str = "baseline",
    label_candidate: str = "candidate",
) -> dict[str, Any]:
    baseline = _load_json(baseline_path)
    candidate = _load_json(candidate_path)

    tracked_stages = [
        "smart_turn",
        "transcription",
        "llm_first_token",
        "llm_full_generation",
        "tts_first_chunk",
        "tts_full_synthesis",
        "total_ttfa",
        "end_to_end",
    ]

    ttfa_before = _summary_metric(baseline, "mean_ttfa_ms", fallback_stage="total_ttfa")
    ttfa_after = _summary_metric(candidate, "mean_ttfa_ms", fallback_stage="total_ttfa")
    e2e_before = float(baseline.get("stages", {}).get("end_to_end", {}).get("mean_ms", 0.0) or 0.0)
    e2e_after = float(candidate.get("stages", {}).get("end_to_end", {}).get("mean_ms", 0.0) or 0.0)

    stage_rows = []
    for stage in tracked_stages:
        base_stage = _safe_stage(baseline, stage)
        cand_stage = _safe_stage(candidate, stage)
        if base_stage.samples == 0 and cand_stage.samples == 0:
            continue
        stage_rows.append(
            {
                "stage": stage,
                "baseline_mean_ms": round(base_stage.mean_ms, 2),
                "candidate_mean_ms": round(cand_stage.mean_ms, 2),
                "delta_ms": round(cand_stage.mean_ms - base_stage.mean_ms, 2),
                "delta_percent": round(_pct_change(base_stage.mean_ms, cand_stage.mean_ms), 2),
                "baseline_p95_ms": round(base_stage.p95_ms, 2),
                "candidate_p95_ms": round(cand_stage.p95_ms, 2),
            }
        )

    return {
        "labels": {"baseline": label_baseline, "candidate": label_candidate},
        "baseline_metadata": baseline.get("metadata", {}),
        "candidate_metadata": candidate.get("metadata", {}),
        "headline": {
            "ttfa_before_ms": round(ttfa_before, 2),
            "ttfa_after_ms": round(ttfa_after, 2),
            "ttfa_delta_ms": round(ttfa_after - ttfa_before, 2),
            "ttfa_delta_percent": round(_pct_change(ttfa_before, ttfa_after), 2),
            "end_to_end_before_ms": round(e2e_before, 2),
            "end_to_end_after_ms": round(e2e_after, 2),
            "end_to_end_delta_ms": round(e2e_after - e2e_before, 2),
            "end_to_end_delta_percent": round(_pct_change(e2e_before, e2e_after), 2),
        },
        "stages": stage_rows,
    }


def render_text_report(comparison: dict[str, Any]) -> str:
    labels = comparison["labels"]
    headline = comparison["headline"]

    lines = []
    lines.append("VOICELOOP-X PROFILE COMPARISON")
    lines.append(
        f"{labels['baseline']} -> {labels['candidate']}: "
        f"TTFA {headline['ttfa_before_ms']:.1f}ms -> {headline['ttfa_after_ms']:.1f}ms "
        f"({headline['ttfa_delta_percent']:+.1f}%)"
    )
    if headline["end_to_end_before_ms"] or headline["end_to_end_after_ms"]:
        lines.append(
            f"End-to-end {headline['end_to_end_before_ms']:.1f}ms -> "
            f"{headline['end_to_end_after_ms']:.1f}ms "
            f"({headline['end_to_end_delta_percent']:+.1f}%)"
        )
    lines.append("")
    lines.append(
        f"{'Stage':24s} {'Base Mean':>10s} {'Cand Mean':>10s} {'Delta':>10s} {'Delta %':>9s}"
    )
    lines.append("-" * 68)
    for row in comparison["stages"]:
        lines.append(
            f"{row['stage']:24s} "
            f"{row['baseline_mean_ms']:10.1f} "
            f"{row['candidate_mean_ms']:10.1f} "
            f"{row['delta_ms']:10.1f} "
            f"{row['delta_percent']:9.1f}"
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Compare two VoiceLoop-X profile JSON files")
    ap.add_argument("baseline", help="Path to baseline profile JSON")
    ap.add_argument("candidate", help="Path to candidate profile JSON")
    ap.add_argument("--baseline-label", default="baseline", help="Label for baseline run")
    ap.add_argument("--candidate-label", default="candidate", help="Label for candidate run")
    ap.add_argument("--output", help="Optional output JSON path for machine-readable comparison")
    args = ap.parse_args()

    comparison = compare_reports(
        args.baseline,
        args.candidate,
        label_baseline=args.baseline_label,
        label_candidate=args.candidate_label,
    )
    print(render_text_report(comparison))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(comparison, f, indent=2)
        print(f"\nSaved comparison JSON to {output_path}")


if __name__ == "__main__":
    main()
