"""Run the matching-based graph coloring experiment and archive falsifiers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from witnora_core.nonedge_matching_bound import run_experiment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=Path("nonedge-matching-bound-ledger.json"))
    args = parser.parse_args()
    report = run_experiment()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print({
        "training": report["training"],
        "holdout": report["holdout"],
        "first_improvement": {k: v for k, v in report["examples"]["first_improvement"].items()
                              if k in ("n", "edges", "chi", "baseline", "matching_bound", "hybrid")},
        "first_hybrid_gap": {k: v for k, v in report["examples"]["first_hybrid_gap"].items()
                             if k in ("n", "edges", "chi", "baseline", "matching_bound", "hybrid")},
        "first_connected_strong_improvement": {k: v for k, v in report["examples"]["first_connected_strong_improvement"].items()
                                               if k in ("n", "edges", "chi", "baseline", "strong_baseline", "matching_bound", "strong_hybrid")},
        "first_two_connected_strong_improvement": ({k: v for k, v in report["examples"]["first_two_connected_strong_improvement"].items()
                                                   if k in ("n", "edges", "chi", "baseline", "strong_baseline", "matching_bound", "strong_hybrid")}
                                                  if report["examples"]["first_two_connected_strong_improvement"] else None),
        "first_two_connected_brooks_improvement": ({k: v for k, v in report["examples"]["first_two_connected_brooks_improvement"].items()
                                                   if k in ("n", "edges", "chi", "strong_baseline", "brooks_baseline", "matching_bound", "brooks_hybrid")}
                                                  if report["examples"]["first_two_connected_brooks_improvement"] else None),
        "first_two_connected_degeneracy_improvement": ({k: v for k, v in report["examples"]["first_two_connected_degeneracy_improvement"].items()
                                                   if k in ("n", "edges", "chi", "brooks_baseline", "degeneracy_baseline", "matching_bound", "degeneracy_hybrid")}
                                                  if report["examples"]["first_two_connected_degeneracy_improvement"] else None),
        "first_two_connected_dsatur_improvement": ({k: v for k, v in report["examples"]["first_two_connected_dsatur_improvement"].items()
                                                   if k in ("n", "edges", "chi", "degeneracy_baseline", "dsatur_baseline", "matching_bound", "dsatur_hybrid")}
                                                  if report["examples"]["first_two_connected_dsatur_improvement"] else None),
        "lean_verified": False,
        "novelty_verified": False,
    })
    if report["training"]["hybrid_counterexamples"] or report["holdout"]["hybrid_counterexamples"]:
        raise AssertionError("hybrid bound fell below exact chromatic number")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
