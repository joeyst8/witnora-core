"""Machine-readable finite expression discovery and falsification ledger."""
from __future__ import annotations

import json
from pathlib import Path

from witnora_core.expression_conjecture_search import run_expression_search


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("expression-conjectures.json"))
    args = parser.parse_args()
    report = run_expression_search()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print({"training_graphs": report["training_graphs"],
           "holdout_graphs": report["holdout_graphs"],
           "expressions_generated": report["expressions_generated"],
           "candidate_equalities": report["candidate_equalities_generated"],
           "evaluated": report["candidates_evaluated"],
           "survivors": len(report["holdout_survivors"]),
           "falsified": len(report["falsified_on_holdout"]),
           "new_theorem_proven": False})
    print("EXAMPLE_SURVIVORS", report["holdout_survivors"][:15])
    print("EXAMPLE_FALSIFIED", [x["conjecture"] for x in report["falsified_on_holdout"][:10]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
