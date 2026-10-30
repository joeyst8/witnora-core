"""Preregistered finite graph conjecture discovery ledger."""
from __future__ import annotations

import json
from pathlib import Path

from witnora_core.graph_conjecture_lab import discover_conjectures


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("graph-conjecture-ledger.json"))
    args = parser.parse_args()
    report = discover_conjectures()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print({"training_graphs": report["training_graphs"],
           "holdout_graphs": report["holdout_graphs"],
           "templates_considered": report["templates_considered"],
           "surviving_conjectures": len(report["holdout_survivors"]),
           "falsified_on_holdout": len(report["falsified_on_holdout"]),
           "known_identity_survived": "alpha + tau = n" in report["holdout_survivors"],
           "new_theorem_proven": False})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
