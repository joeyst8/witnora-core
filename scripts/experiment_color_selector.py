"""Evaluate train-frozen cheap coloring repair selectors."""
from __future__ import annotations

import json
from pathlib import Path

from witnora_core.color_selector_lab import run_selector_study


def main() -> None:
    report = run_selector_study()
    Path("color-selector-ledger.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print({
        "chosen_rule": report["chosen_rule"],
        "train_chosen": report["train_scores"][report["chosen_rule"]],
        "holdout_random": {
            k: v for k, v in report["evaluations"]["holdout_random"].items()
            if k != "examples"},
        "holdout_structured": {
            k: v for k, v in report["evaluations"]["holdout_structured"].items()
            if k != "examples"},
        "novelty_verified": False, "lean_verified": False,
    })


if __name__ == "__main__":
    main()
