"""Frozen W031 16-seed source-order robustness benchmark, Rust-first.

All 900 timings include complete pipeline, independent source-proof checks and
SAT model checks. Python only generates frozen test CNFs and orchestrates the
already verified Rust prechecks plus unmodified Kissat.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile

from scripts.benchmark_w027_smoke import parse_dimacs, run_arm
from scripts.w030_smoke_cases import source_bytes
from scripts.w031_order_cases import cases, manifest
from tests.test_w027_precheck import verify_certificate


ARMS = ("kissat", "w027_plus_kissat", "w030_prefix_plus_kissat")
REPEATS = 3
WALL_CAP = 6.0  # frozen run_arm hard cap for this synthetic-only study


def run():
    old = Path(os.environ["W031_OLD_PRECHECK_BIN"])
    new = Path(os.environ["W031_PREFIX_BIN"])
    kissat = Path(os.environ["W031_KISSAT_BIN"])
    if not all(p.is_file() for p in (old, new, kissat)):
        raise RuntimeError("missing one or more pinned solver binaries")

    frozen = json.loads(Path("research/results/w031_order_case_manifest.json").read_text())
    if frozen != manifest():
        raise RuntimeError("precommitted source manifest mismatch before timing")

    rows = []
    prefix_diagnostics = []
    with tempfile.TemporaryDirectory(prefix="witnora-w031-order-") as directory:
        for index, case in enumerate(cases()):
            source = source_bytes(case["variables"], case["clauses"])
            digest = hashlib.sha256(source).hexdigest()
            expected = frozen["entries"][index]
            if expected["case_id"] != case["case_id"] or expected["cnf_sha256"] != digest:
                raise RuntimeError("source content has changed since freeze")
            filename = Path(directory) / (case["case_id"] + ".cnf")
            filename.write_bytes(source)
            clauses = parse_dimacs(filename)[1]

            # Supplemental, independently source-audited prefix diagnostic.
            # This one invocation is outside the measured arm comparisons.
            scan = subprocess.run([str(new), str(filename)], check=True,
                                  capture_output=True, text=True, timeout=WALL_CAP)
            evidence = json.loads(scan.stdout)
            expected_status = "UNSAT_CERTIFIED" if case["expected"] == "UNSAT" else "NO_CERTIFICATE"
            if evidence["status"] != expected_status:
                raise RuntimeError("Rust source-prefix status differs from frozen label")
            if evidence["status"] == "UNSAT_CERTIFIED" and not verify_certificate(clauses, evidence):
                raise RuntimeError("Rust source-prefix proof failed independent audit")
            prefix_diagnostics.append({"case_id": case["case_id"],
                                       "status": evidence["status"],
                                       "read_clauses": evidence["read_clauses"],
                                       "declared_clauses": evidence["clauses"],
                                       "terminated_early": evidence["terminated_early"]})

            for repeat in range(REPEATS):
                shift = (index + repeat) % len(ARMS)
                for arm in ARMS[shift:] + ARMS[:shift]:
                    if arm == "kissat":
                        timed = run_arm("kissat", filename, clauses, case["expected"], old, kissat, None)
                    else:
                        detector = old if arm == "w027_plus_kissat" else new
                        timed = run_arm("witnora_plus_kissat", filename, clauses,
                                        case["expected"], detector, kissat, None)
                    timed.update(arm=arm, case_id=case["case_id"], expected=case["expected"],
                                 stratum=case["stratum"], order=case["order"],
                                 replicate=case.get("replicate"), repeat=repeat,
                                 cnf_sha256=digest)
                    rows.append(timed)
                    print(f"W031 {case['case_id']} repeat={repeat} {arm}: {timed['verdict']} "
                          f"{timed['full_pipeline_wall_ns'] / 1e6:.4f}ms", flush=True)

    medians = []
    for case in cases():
        name = case["case_id"]
        for arm in ARMS:
            selected = [r for r in rows if r["case_id"] == name and r["arm"] == arm]
            solved = [r["full_pipeline_wall_ns"] for r in selected if r["verdict"] in ("SAT", "UNSAT")]
            medians.append({"case_id": name, "arm": arm, "expected": case["expected"],
                            "stratum": case["stratum"], "order": case["order"],
                            "replicate": case.get("replicate"),
                            "solved_repetitions": len(solved),
                            "timeout_repetitions": sum(r["verdict"] == "TIMEOUT" for r in selected),
                            "median_solved_wall_ns": int(statistics.median(solved)) if solved else None})

    report = {"study": "W-CROSSDOMAIN-031", "phase": "preregistered_order_robustness",
              "protocol": "docs/W_CROSSDOMAIN_031_ORDER_ROBUSTNESS_PROTOCOL.md",
              "case_count": len(frozen["entries"]), "repeats_per_arm": REPEATS,
              "wall_cap_seconds": WALL_CAP, "memory_cap_bytes": 2 * 1024**3,
              "manifest": "research/results/w031_order_case_manifest.json",
              "kissat_source_sha": os.environ["W031_KISSAT_SHA"],
              "rows": rows, "per_case_arm_medians": medians,
              "prefix_diagnostics": prefix_diagnostics,
              "claim_scope": "finite 16-seed synthetic clause order study with planted-SAT controls; not external or P=NP"}
    if len(rows) != len(frozen["entries"]) * REPEATS * len(ARMS):
        raise RuntimeError("missing precommitted timed invocations")
    Path(os.environ["W031_REPORT_PATH"]).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("W031_COMPLETE", len(rows), "timed invocations", flush=True)


if __name__ == "__main__":
    run()
