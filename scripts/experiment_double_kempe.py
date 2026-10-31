"""Frozen adversarial study of two-step Kempe coloring repair."""
from __future__ import annotations

import json
from pathlib import Path

from witnora_core.double_kempe_lab import run_double_kempe_experiment


def main() -> None:
    report = run_double_kempe_experiment()
    Path("double-kempe-ledger.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print({"plan": report["plan"], "training": report["training"],
           "holdout": report["holdout"],
           "first_training_fix": report["examples"]["training"]["first_fix"],
           "first_holdout_fix": report["examples"]["holdout"]["first_fix"],
           "first_unresolved_holdout": report["examples"]["holdout"]["first_unresolved"],
           "novelty_verified": False, "lean_verified": False})


if __name__ == "__main__":
    main()
