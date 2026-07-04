"""Markdown report generation for Witnora benchmark JSON."""

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


def _results(data: dict[str, Any]) -> list[dict[str, Any]]:
    return list(data.get("per_case_results", []))


def generate_markdown_report(data: dict[str, Any]) -> str:
    summary = _summary(data)
    results = _results(data)
    route_counts: dict[str, int] = {}
    for result in results:
        route = str(result.get("solved_route", ""))
        route_counts[route] = route_counts.get(route, 0) + 1

    lines: list[str] = []
    lines.append("# Witnora Benchmark Report")
    lines.append("")

    lines.append("## Benchmark Overview")
    lines.extend(
        _table(
            ["Field", "Value"],
            [
                ["version", data.get("version", "")],
                ["c_parameter", data.get("c_parameter", "")],
                ["scale", data.get("scale", "")],
                ["timestamp", data.get("timestamp", "")],
                ["total_cases", summary.get("total_cases", len(results))],
            ],
        )
    )
    lines.append("")

    lines.append("## Summary Counts")
    lines.extend(
        _table(
            ["Metric", "Value"],
            [
                ["solved_count", summary.get("solved_count", 0)],
                ["sat_count", summary.get("sat_count", 0)],
                ["unsat_count", summary.get("unsat_count", 0)],
                ["no_collapse_count", summary.get("no_collapse_count", 0)],
            ],
        )
    )
    lines.append("")

    lines.append("## Route Breakdown")
    lines.extend(
        _table(
            ["Route", "Count"],
            sorted(route_counts.items(), key=lambda item: item[0]),
        )
    )
    lines.append("")

    lines.append("## Collapse Path Statistics")
    lines.extend(
        _table(
            ["Metric", "Value"],
            [
                ["average_collapse_path_length", summary.get("average_collapse_path_length", 0)],
                ["max_collapse_path_length", max((r.get("collapse_path_length", 0) for r in results), default=0)],
            ],
        )
    )
    lines.append("")

    lines.append("## Clause/Variable Reduction")
    lines.extend(
        _table(
            ["Metric", "Value"],
            [
                ["average_clause_reduction_pct", summary.get("average_clause_reduction_pct", 0)],
                ["average_variable_reduction_pct", summary.get("average_variable_reduction_pct", 0)],
            ],
        )
    )
    lines.append("")

    lines.append("## BCE / PLE / UP / SUB / VE Counts")
    lines.extend(
        _table(
            ["Count Type", "Total"],
            [
                ["BCE removed clauses", sum(r.get("num_bce_removed", 0) for r in results)],
                ["PLE assignments", sum(r.get("num_ple_assignments", 0) for r in results)],
                ["UP assignments", sum(r.get("num_up_assignments", 0) for r in results)],
                ["SUB removed clauses", sum(r.get("num_subsumed_clauses", 0) for r in results)],
                ["VE eliminations", sum(r.get("num_vars_eliminated", 0) for r in results)],
            ],
        )
    )
    lines.append("")

    lines.append("## Determinism Results")
    checked = [r for r in results if r.get("determinism_pass") is not None]
    lines.extend(
        _table(
            ["Metric", "Value"],
            [
                ["checked_cases", len(checked)],
                ["pass_rate", summary.get("certificate_hash_determinism_pass_rate", "")],
                ["failed_cases", ", ".join(r["case_name"] for r in checked if not r.get("determinism_pass"))],
            ],
        )
    )
    lines.append("")

    lines.append("## No-Collapse Cases")
    no_collapse = [r for r in results if r.get("solved_route") == "NO_COLLAPSE"]
    if no_collapse:
        lines.extend(
            _table(
                ["Case", "Failure Reason", "Original Vars", "Original Clauses"],
                [
                    [
                        r.get("case_name", ""),
                        r.get("failure_reason", ""),
                        r.get("original_num_vars", ""),
                        r.get("original_num_clauses", ""),
                    ]
                    for r in no_collapse
                ],
            )
        )
    else:
        lines.append("No no-collapse cases were reported.")
    lines.append("")

    lines.append("## Width Measurement Skips")
    skipped = [
        r
        for r in results
        if r.get("post_s_width_order_status") == "SKIPPED_SIZE_CAP"
    ]
    if skipped:
        lines.extend(
            _table(
                ["Case", "Post-S Vars", "Reason"],
                [
                    [
                        r.get("case_name", ""),
                        r.get("post_s_num_vars", ""),
                        r.get("post_s_width_order_skip_reason", ""),
                    ]
                    for r in skipped
                ],
            )
        )
    else:
        lines.append("No width-order measurements were skipped.")
    lines.append("")

    lines.append("## Limitations")
    lines.extend(
        [
            "- Benchmark measurements are not proofs of industrial SAT competitiveness.",
            "- Clique lower bound is max clause width minus one, not exact treewidth.",
            "- Exact width-order search remains capped and can be skipped for large formulas.",
            "- NO_COLLAPSE means only no certified collapse was found under the current grammar and c.",
            "- No LRAT/FRAT, Horn, XOR, backdoor, GNN, MCTS, or external SAT solver route is included.",
        ]
    )
    lines.append("")

    lines.append("## Claims Allowed / Claims Forbidden")
    lines.append("Allowed:")
    lines.extend(
        [
            "- Witnora measures certified collapse behavior for deterministic benchmark cases.",
            "- SAT results verify reconstructed assignments against the original CNF.",
            "- Certificate hashes are deterministic except for excluded runtime/timestamp data.",
        ]
    )
    lines.append("")
    lines.append("Forbidden:")
    lines.extend(
        [
            "- Do not claim P = NP.",
            "- Do not claim no-collapse formulas are hard.",
            "- Do not claim competitiveness with modern industrial SAT solvers from this benchmark alone.",
        ]
    )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a Witnora benchmark Markdown report")
    parser.add_argument("benchmark_json", help="benchmark JSON input")
    parser.add_argument("--out", required=True, help="Markdown report output path")
    args = parser.parse_args(argv)

    data = json.loads(Path(args.benchmark_json).read_text(encoding="utf-8"))
    report = generate_markdown_report(data)
    Path(args.out).write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
