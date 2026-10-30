"""Record exact graph counterexamples and outstanding proof obligations."""
from __future__ import annotations

import json
from pathlib import Path

from witnora_core.targeted_graph_theorems import challenge


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("targeted-graph-theorems.json"))
    args = parser.parse_args()
    report = challenge()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print({"cases": report["cases"],
           "first_counterexamples": len(report["first_counterexamples"]),
           "second_counterexamples": len(report["second_counterexamples"]),
           "lean_status": report["lean_status"],
           "new_theorem_proven": False})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
