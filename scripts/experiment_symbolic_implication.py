"""Emit rule-referenced derivations and unresolved Lean obligations."""
from __future__ import annotations

import json
from pathlib import Path

from witnora_core.symbolic_implication import triage_with_implications


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("symbolic-implication-ledger.json"))
    args = parser.parse_args()
    report = triage_with_implications()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print({"original_unclassified": report["original_unclassified"],
           "derived_relative_to_axioms": len(report["derived_relative_to_axioms"]),
           "unresolved": len(report["unresolved"]),
           "pending_lean_queue": len(report["lean_review_queue"]),
           "new_theorem_proven": False})
    print("UNRESOLVED_EXAMPLES", [x["conjecture"] for x in report["unresolved"][:10]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
