"""Persist counterexamples, incomplete novelty catalog and Lean obligations."""
from __future__ import annotations

import json
from pathlib import Path

from witnora_core.conjecture_triage import triage


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("conjecture-triage-v16.json"))
    args = parser.parse_args()
    report = triage()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print({"original_survivors": report["original_survivors"],
           "known_catalog_matches": len(report["catalog_known_identity_matches"]),
           "adversarial_graphs": report["adversarial_graphs"],
           "additional_falsifications": len(report["adversarially_falsified"]),
           "unclassified_survivors": len(report["unclassified_survivors"]),
           "lean_queue": len(report["lean_review_queue"]),
           "new_theorem_proven": False})
    print("UNCLASSIFIED_EXAMPLES", report["unclassified_survivors"][:12])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
