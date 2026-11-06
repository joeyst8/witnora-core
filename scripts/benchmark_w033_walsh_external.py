"""Exploratory W033 exact Walsh certificate on eight source-verified VLSAT2 CNFs.

This is a separate mathematical detector, not an end-to-end solver-speed trial.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

from scripts.benchmark_w027_smoke import parse_dimacs
from scripts.benchmark_w032_external import materialize
from scripts.w032_external_cases import cases_metadata, manifest
from scripts.w033_walsh_bound import walsh_bound


def run():
    frozen = json.loads(Path("research/results/w032_case_manifest.json").read_text())
    if frozen != manifest():
        raise RuntimeError("W032 external source hashes or cases changed")
    results = []
    with tempfile.TemporaryDirectory(prefix="witnora-w033-walsh-") as folder:
        for entry in cases_metadata():
            if entry["stratum"] != "official_external_vlsat2":
                continue
            source = materialize(entry)
            path = Path(folder) / (entry["case_id"] + ".cnf")
            path.write_bytes(source)
            nvars, clauses = parse_dimacs(path)
            if nvars != entry["variables"] or len(clauses) != entry["clauses"]:
                raise RuntimeError("source DIMACS parsed count changed")
            retained = [clause for clause in clauses if len(clause) <= 3]
            started = time.perf_counter_ns()
            result = walsh_bound(nvars, retained, max_width=3)
            elapsed_ns = time.perf_counter_ns() - started
            if result["status"] == "UNSAT_CERTIFIED" and entry["expected"] != "UNSAT":
                raise RuntimeError("invalid UNSAT certificate on published SAT case")
            results.append({
                "case_id": entry["case_id"],
                "publisher_expected": entry["expected"],
                "original_source_sha256": hashlib.sha256(source).hexdigest(),
                "original_variables": nvars,
                "original_clauses": len(clauses),
                "retained_width_at_most_3": len(retained),
                "skipped_width_above_3": len(clauses) - len(retained),
                "algorithm_wall_ns": elapsed_ns,
                "spectral_result": result,
            })
            print("W033", entry["case_id"],result["status"],
                  f"{elapsed_ns/1e6:.1f}ms", len(retained), "short clauses", flush=True)
    if len(results) != 8:
        raise RuntimeError("incomplete official source coverage")
    report = {
        "study": "W-CROSSDOMAIN-033",
        "phase": "source_frozen_spectral_exploration",
        "protocol": "docs/W_CROSSDOMAIN_033_SPECTRAL_CERTIFICATE_PROTOCOL.md",
        "source_manifest": "research/results/w032_case_manifest.json",
        "external_case_count": len(results),
        "algorithm": "exact Walsh L1 lower bound on 0-to-3-width source subformula",
        "results": results,
        "scope": "sound sufficient UNSAT certificate only, no general solver speed claim",
    }
    Path(os.environ["W033_REPORT_PATH"]).write_text(json.dumps(report, sort_keys=True, indent=2)+"\n")


if __name__ == "__main__":
    run()
