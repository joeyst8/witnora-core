"""Compare two Witnora benchmark JSON outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return lines


def _summary(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("summary", {})


def _results_by_case(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(result.get("case_name", "")): result
        for result in data.get("per_case_results", [])
    }


def _route_counts(data: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in data.get("per_case_results", []):
        route = str(result.get("solved_route", ""))
        counts[route] = counts.get(route, 0) + 1
    return counts


def generate_compare_report(left: dict[str, Any], right: dict[str, Any]) -> str:
    left_summary = _summary(left)
    right_summary = _summary(right)
    left_cases = _results_by_case(left)
    right_cases = _results_by_case(right)
    common_cases = sorted(set(left_cases) & set(right_cases))

    status_changes = [
        [
            case,
            left_cases[case].get("status", ""),
            right_cases[case].get("status", ""),
        ]
        for case in common_cases
        if left_cases[case].get("status") != right_cases[case].get("status")
    ]
    route_changes = [
        [
            case,
            left_cases[case].get("solved_route", ""),
            right_cases[case].get("solved_route", ""),
        ]
        for case in common_cases
        if left_cases[case].get("solved_route") != right_cases[case].get("solved_route")
    ]

    route_keys = sorted(set(_route_counts(left)) | set(_route_counts(right)))
    left_routes = _route_counts(left)
    right_routes = _route_counts(right)

    lines: list[str] = []
    lines.append("# Witnora Benchmark Comparison")
    lines.append("")

    lines.append("## Overview")
    lines.extend(
        _table(
            ["Field", "Left", "Right"],
            [
                ["version", left.get("version", ""), right.get("version", "")],
                ["c_parameter", left.get("c_parameter", ""), right.get("c_parameter", "")],
                ["scale", left.get("scale", ""), right.get("scale", "")],
                ["timestamp", left.get("timestamp", ""), right.get("timestamp", "")],
            ],
        )
    )
    lines.append("")

    lines.append("## Summary Delta")
    metric_names = [
        "solved_count",
        "no_collapse_count",
        "average_collapse_path_length",
        "average_clause_reduction_pct",
        "certificate_hash_determinism_pass_rate",
    ]
    lines.extend(
        _table(
            ["Metric", "Left", "Right", "Delta"],
            [
                [
                    metric,
                    left_summary.get(metric, 0),
                    right_summary.get(metric, 0),
                    _delta(left_summary.get(metric, 0), right_summary.get(metric, 0)),
                ]
                for metric in metric_names
            ],
        )
    )
    lines.append("")

    lines.append("## Route Breakdown")
    lines.extend(
        _table(
            ["Route", "Left", "Right", "Delta"],
            [
                [
                    route,
                    left_routes.get(route, 0),
                    right_routes.get(route, 0),
                    right_routes.get(route, 0) - left_routes.get(route, 0),
                ]
                for route in route_keys
            ],
        )
    )
    lines.append("")

    lines.append("## Cases That Changed Status")
    if status_changes:
        lines.extend(_table(["Case", "Left Status", "Right Status"], status_changes))
    else:
        lines.append("No common cases changed status.")
    lines.append("")

    lines.append("## Cases That Changed Route")
    if route_changes:
        lines.extend(_table(["Case", "Left Route", "Right Route"], route_changes))
    else:
        lines.append("No common cases changed route.")
    lines.append("")

    lines.append("## Determinism Pass Rate")
    lines.extend(
        _table(
            ["Side", "Pass Rate"],
            [
                ["left", left_summary.get("certificate_hash_determinism_pass_rate", "")],
                ["right", right_summary.get("certificate_hash_determinism_pass_rate", "")],
            ],
        )
    )
    lines.append("")
    return "\n".join(lines)


def _delta(left: Any, right: Any) -> Any:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return round(right - left, 6)
    return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare two Witnora benchmark JSON files")
    parser.add_argument("left_json")
    parser.add_argument("right_json")
    parser.add_argument("--out", required=True, help="Markdown comparison output path")
    args = parser.parse_args(argv)

    left = json.loads(Path(args.left_json).read_text(encoding="utf-8"))
    right = json.loads(Path(args.right_json).read_text(encoding="utf-8"))
    report = generate_compare_report(left, right)
    Path(args.out).write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
