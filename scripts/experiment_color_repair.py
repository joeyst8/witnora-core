"""Reproducible coloring-repair study with training and held-out graphs."""
from __future__ import annotations

import json
from pathlib import Path

from witnora_core.color_repair_lab import run_repair_experiment


def main() -> None:
    report = run_repair_experiment()
    Path("color-repair-ledger.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print({"design": report["design"], "training": report["training"],
           "holdout": report["holdout"],
           "first_training_failure": report["examples"]["training"],
           "novelty_verified": False, "lean_verified": False})


if __name__ == "__main__":
    main()
