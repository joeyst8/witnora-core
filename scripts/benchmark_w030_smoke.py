"""Precommitted, cost-inclusive W030 exploratory solver smoke.

Compare unchanged-CNF Kissat, W027 precheck+Kissat, and W030 prefix+Kissat.
All SAT models and source-XOR UNSAT certificates are independently audited
inside the measured wall time by the frozen W027 runner.
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
from scripts.w030_smoke_cases import cases, manifest, source_bytes
from tests.test_w027_precheck import verify_certificate


ARMS = ("kissat", "w027_plus_kissat", "w030_prefix_plus_kissat")
CAP_SECONDS = 6.0  # inherited by scripts.benchmark_w027_smoke.run_arm


def summarize(rows):
    medians = []
    for name in dict.fromkeys(x["case_id"] for x in rows):
        for arm in ARMS:
            selected = [r for r in rows if r["case_id"] == name and r["arm"] == arm]
            solved = [r["full_pipeline_wall_ns"] for r in selected if r["verdict"] in ("SAT", "UNSAT")]
            medians.append({"case_id": name, "arm": arm,
                            "solved_repetitions": len(solved),
                            "timeout_repetitions": sum(r["verdict"] == "TIMEOUT" for r in selected),
                            "median_solved_wall_ns": int(statistics.median(solved)) if solved else None})
    return medians


def run():
    old = Path(os.environ["W030_OLD_PRECHECK_BIN"])
    prefix = Path(os.environ["W030_PREFIX_BIN"])
    kissat = Path(os.environ["W030_KISSAT_BIN"])
    for binary in (old, prefix, kissat):
        if not binary.is_file():
            raise RuntimeError(f"missing frozen binary: {binary}")

    frozen = json.loads(Path("research/results/w030_smoke_case_manifest.json").read_text())
    if frozen != manifest():
        raise RuntimeError("W030 frozen source hashes changed before timing")

    rows = []
    static_checks = []
    with tempfile.TemporaryDirectory(prefix="witnora-w030-smoke-") as directory:
        for index, case in enumerate(cases()):
            filename = Path(directory) / (case["case_id"] + ".cnf")
            encoded = source_bytes(case["variables"], case["clauses"])
            filename.write_bytes(encoded)
            clauses = parse_dimacs(filename)[1]
            digest = hashlib.sha256(encoded).hexdigest()
            if digest != frozen["entries"][index]["cnf_sha256"]:
                raise RuntimeError("source CNF hash changed")

            # Read fraction is diagnostic only. This independent prefix probe
            # is explicitly outside the timed arm measurements; both old and
            # prefix measured arms still run full source verification.
            completed = subprocess.run([str(prefix), str(filename)], capture_output=True,
                                       text=True, timeout=CAP_SECONDS, check=True)
            evidence = json.loads(completed.stdout)
            expected_status = "UNSAT_CERTIFIED" if case["expected"] == "UNSAT" else "NO_CERTIFICATE"
            if evidence["status"] != expected_status:
                raise RuntimeError("prefix detector disagreed with frozen status")
            if evidence["status"] == "UNSAT_CERTIFIED" and not verify_certificate(clauses, evidence):
                raise RuntimeError("independent source clause certificate failed")
            static_checks.append({"case_id": case["case_id"], "status": evidence["status"],
                                  "declared_clauses": evidence["clauses"],
                                  "read_clauses": evidence["read_clauses"],
                                  "terminated_early": evidence["terminated_early"]})

            for repeat in range(3):
                order = ARMS[(index + repeat) % len(ARMS):] + ARMS[:(index + repeat) % len(ARMS)]
                for arm in order:
                    if arm == "kissat":
                        result = run_arm("kissat", filename, clauses, case["expected"], old, kissat, None)
                    else:
                        precheck = old if arm == "w027_plus_kissat" else prefix
                        result = run_arm("witnora_plus_kissat", filename, clauses,
                                         case["expected"], precheck, kissat, None)
                    result.update(arm=arm, case_id=case["case_id"], repeat=repeat,
                                  stratum=case["stratum"], expected=case["expected"],
                                  cnf_sha256=digest)
                    rows.append(result)
                    print(f"W030 {case['case_id']} r={repeat} {arm} "
                          f"{result['verdict']} {result['full_pipeline_wall_ns'] / 1e6:.3f}ms", flush=True)

    report = {"study": "W-CROSSDOMAIN-030", "phase": "exploratory_smoke_not_full_protocol",
              "protocol": "docs/W_CROSSDOMAIN_030_SMOKE_PROTOCOL.md",
              "case_count": len(frozen["entries"]), "repetitions_per_arm": 3,
              "wall_cap_seconds": CAP_SECONDS, "memory_cap_bytes": 2 * 1024 ** 3,
              "kissat_source_sha": os.environ["W030_KISSAT_SHA"],
              "manifest": "research/results/w030_smoke_case_manifest.json",
              "static_prefix_checks": static_checks, "rows": rows,
              "per_case_arm_medians": summarize(rows),
              "claim_scope": "frozen eight-case exploratory cost-inclusive smoke, not representative or P=NP"}
    if len(rows) != len(frozen["entries"]) * len(ARMS) * 3:
        raise RuntimeError("missing timed arm rows")
    Path(os.environ["W030_REPORT_PATH"]).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("W030_SMOKE_COMPLETE", len(rows), "timed invocations", flush=True)


if __name__ == "__main__":
    run()
