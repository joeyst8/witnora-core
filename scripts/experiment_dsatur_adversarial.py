"""Run a predeclared adversarial search for deterministic DSATUR failures."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from witnora_core.dsatur_adversarial_lab import run_adversarial_search


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("dsatur-adversarial-ledger.json"))
    args = parser.parse_args()
    report = run_adversarial_search()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print({"plan": report["plan"], "statistics": report["statistics"],
           "first_failure": report["counterexamples"][0] if report["counterexamples"] else None,
           "lean_verified": False, "novelty_verified": False})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
