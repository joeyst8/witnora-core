"""Audit standard DSATUR bipartite-optimality against our implementation."""
from __future__ import annotations

import json
from pathlib import Path

from witnora_core.dsatur_bipartite_audit import run_bipartite_audit


def main() -> None:
    report = run_bipartite_audit()
    Path("dsatur-bipartite-audit-ledger.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["statistics"])
    if report["statistics"]["dsatur_violations"]:
        raise AssertionError("our DSATUR failed on a bipartite graph")


if __name__ == "__main__":
    main()
