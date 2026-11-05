"""Rerun the frozen failure corpus with Kempe structural recoloring."""
from __future__ import annotations

import json
from pathlib import Path

from witnora_core.kempe_repair_lab import run_kempe_experiment


def main() -> None:
    report = run_kempe_experiment()
    Path("kempe-repair-ledger.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print({"plan": report["plan"], "training": report["training"],
           "holdout": report["holdout"],
           "first_training_kempe_fix": report["examples"]["training"]["first_kempe_fix"],
           "first_holdout_kempe_fix": report["examples"]["holdout"]["first_kempe_fix"],
           "first_unresolved_holdout": report["examples"]["holdout"]["first_unresolved"],
           "lean_verified": False, "novelty_verified": False})


if __name__ == "__main__":
    main()
