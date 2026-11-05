"""Emit full conditional and transformation conjecture ledger."""
from __future__ import annotations

import json
from pathlib import Path

from witnora_core.conditional_graph_conjectures import run_experiment


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("conditional-graph-ledger.json"))
    args = parser.parse_args()
    result = run_experiment()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print({"training_graphs": result["training_graphs"],
           "holdout_graphs": result["holdout_graphs"],
           "templates_considered": result["templates_considered"],
           "survivors": len(result["holdout_survivors"]),
           "falsified": len(result["falsified_on_holdout"]),
           "theorem_proven": False})
    print("SURVIVORS", result["holdout_survivors"])
    print("FALSIFIED", [x["conjecture"] for x in result["falsified_on_holdout"]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
