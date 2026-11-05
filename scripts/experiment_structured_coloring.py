"""Evaluate repair pipeline on unrelated structured graph families."""
from __future__ import annotations

import json
from pathlib import Path

from witnora_core.structured_coloring_study import run_structured_study


def main() -> None:
    report = run_structured_study()
    Path("structured-coloring-ledger.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print({"plan": report["plan"], "statistics": report["statistics"],
           "first_improvement": report["examples"]["first_improvement"],
           "first_unresolved": report["examples"]["first_unresolved"],
           "novelty_verified": False, "lean_verified": False})


if __name__ == "__main__":
    main()
