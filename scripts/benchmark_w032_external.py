"""W032 external-domain, source-verified, cost-inclusive exploratory pilot.

All primary cases are original published VLSAT2 CNFs. The Rust algorithms
run unchanged, then Kissat receives the original CNF only if no exact source
certificate is returned. Synthetic cases and decoys are audit controls only.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile

from scripts.benchmark_w022_vlsat import download, independent_dimacs_check
from scripts.benchmark_w027_smoke import parse_dimacs, run_arm
from scripts.w027_full_decoys import SPECS, clauses_for_spec, dimacs_bytes
from scripts.w030_smoke_cases import source_bytes
from scripts.w032_external_cases import cases_metadata, manifest
from tests.test_mixed_xor_recovery_rust import SAT, UNSAT, core, make_noise
from tests.test_w027_precheck import verify_certificate


ARMS = ("kissat", "w027_plus_kissat", "w030_prefix_plus_kissat")
REPEATS = 3
CAP_SECONDS = 6.0  # matched to frozen W030/W031 synthetic pilot cap


def materialize(entry):
    """Return publisher-origin or frozen-control exact DIMACS bytes."""
    name = entry["case_id"]
    if entry["stratum"] == "official_external_vlsat2":
        raw, compressed_sha = download(name)
        if compressed_sha != entry["compressed_sha256"]:
            raise RuntimeError(f"publisher compressed SHA mismatch: {name}")
        independent_dimacs_check(raw, name)
    elif entry["stratum"] == "frozen_adversarial_sat_decoy":
        spec = next(spec for spec in SPECS if spec[0] == name)
        raw = dimacs_bytes(clauses_for_spec(spec))
    elif entry["stratum"] == "synthetic_sanity_only":
        _, noise = make_noise(8192, 0)
        parity = SAT if entry["expected"] == "SAT" else UNSAT
        raw = source_bytes(64, core(parity) + noise)
    else:
        raise RuntimeError("unrecognized stratum")
    if hashlib.sha256(raw).hexdigest() != entry["cnf_sha256"]:
        raise RuntimeError(f"frozen uncompressed SHA mismatch: {name}")
    return raw


def run():
    old = Path(os.environ["W032_OLD_PRECHECK_BIN"])
    new = Path(os.environ["W032_PREFIX_BIN"])
    kissat = Path(os.environ["W032_KISSAT_BIN"])
    if not all(p.is_file() for p in (old, new, kissat)):
        raise RuntimeError("missing one or more pinned solver binaries")
    frozen = json.loads(Path("research/results/w032_case_manifest.json").read_text())
    if frozen != manifest():
        raise RuntimeError("source inputs changed after preregistration")

    rows = []
    diagnostics = []
    with tempfile.TemporaryDirectory(prefix="witnora-w032-external-") as directory:
        for index, entry in enumerate(cases_metadata()):
            source = materialize(entry)
            name = entry["case_id"]
            filename = Path(directory) / (name + ".cnf")
            filename.write_bytes(source)
            variables, clauses = parse_dimacs(filename)
            if variables != entry["variables"] or len(clauses) != entry["clauses"]:
                raise RuntimeError(f"parsed source identity mismatch: {name}")

            # Additional untimed diagnostic never substitutes for measured arm.
            probe = subprocess.run([str(new), str(filename)], capture_output=True,
                                   text=True, timeout=CAP_SECONDS, check=True)
            evidence = json.loads(probe.stdout)
            if evidence["status"] not in ("NO_CERTIFICATE", "UNSAT_CERTIFIED"):
                raise RuntimeError("invalid Rust status")
            if evidence["status"] == "UNSAT_CERTIFIED":
                if entry["expected"] == "SAT" or not verify_certificate(clauses, evidence):
                    raise RuntimeError(f"false or unaudited UNSAT certificate: {name}")
            elif entry["stratum"] == "synthetic_sanity_only" and entry["expected"] == "UNSAT":
                raise RuntimeError("Rust missed frozen synthetic sanity proof")
            diagnostics.append({"case_id": name, "stratum": entry["stratum"],
                                "expected": entry["expected"], "status": evidence["status"],
                                "read_clauses": evidence["read_clauses"],
                                "declared_clauses": evidence["clauses"]})

            for repeat in range(REPEATS):
                offset = (index + repeat) % len(ARMS)
                for arm in ARMS[offset:] + ARMS[:offset]:
                    if arm == "kissat":
                        result = run_arm("kissat", filename, clauses, entry["expected"], old, kissat, None)
                    else:
                        precheck = old if arm == "w027_plus_kissat" else new
                        result = run_arm("witnora_plus_kissat", filename, clauses,
                                         entry["expected"], precheck, kissat, None)
                    result.update(arm=arm, case_id=name, stratum=entry["stratum"],
                                  expected=entry["expected"], repeat=repeat,
                                  cnf_sha256=entry["cnf_sha256"])
                    rows.append(result)
                    print(f"W032 {name} {repeat} {arm}: {result['verdict']} "
                          f"{result['full_pipeline_wall_ns']/1e3:.0f}us", flush=True)

    medians = []
    for entry in frozen["entries"]:
        for arm in ARMS:
            selected = [r for r in rows if r["case_id"] == entry["case_id"] and r["arm"] == arm]
            solved = [r["full_pipeline_wall_ns"] for r in selected if r["verdict"] in ("SAT", "UNSAT")]
            medians.append({"case_id": entry["case_id"], "arm": arm,
                            "stratum": entry["stratum"], "expected": entry["expected"],
                            "solved_repetitions": len(solved),
                            "timeout_repetitions": sum(r["verdict"] == "TIMEOUT" for r in selected),
                            "median_solved_wall_ns": int(statistics.median(solved)) if solved else None})

    if len(rows) != 14 * len(ARMS) * REPEATS:
        raise RuntimeError("missing preregistered arm/case/repeat rows")
    report = {"study": "W-CROSSDOMAIN-032", "phase": "frozen_external_domain_pilot",
              "protocol": "docs/W_CROSSDOMAIN_032_EXTERNAL_DOMAIN_PROTOCOL.md",
              "case_count": 14, "external_case_count": 8,
              "repetitions_per_arm": REPEATS, "wall_cap_seconds": CAP_SECONDS,
              "memory_cap_bytes": 2*1024**3,
              "kissat_source_sha": os.environ["W032_KISSAT_SHA"],
              "manifest": "research/results/w032_case_manifest.json",
              "rows": rows, "per_case_arm_medians": medians,
              "prefix_diagnostics": diagnostics,
              "claim_scope": "8 official VLSAT2 external CNFs with 6s cap, plus six controls; solved-only timing analysis must account for censoring"}
    Path(os.environ["W032_REPORT_PATH"]).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("W032_COMPLETE",len(rows),"timed invocations",flush=True)


if __name__ == "__main__":
    run()
