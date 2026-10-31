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
        "first_improvement": report["examples"]["first_improvement"] is not None,
        "first_hybrid_gap": report["examples"]["first_hybrid_gap"] is not None,
        "lean_verified": False,
        "novelty_verified": False,
    })
    if report["training"]["hybrid_counterexamples"] or report["holdout"]["hybrid_counterexamples"]:
        raise AssertionError("hybrid bound fell below exact chromatic number")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
