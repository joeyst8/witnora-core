"""W027 preregistered Phase-1 *exploratory* cost-inclusive solver smoke.

Algorithms under test are Rust, Kissat and (when built) CryptoMiniSat;
Python only pins sources, times subprocesses and independently checks proof/model.
This is NOT the full W027 three-arm, 96-pair and eight-external benchmark.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import tempfile
import time

from scripts.benchmark_w022_vlsat import download, independent_dimacs_check
from tests.test_mixed_xor_recovery_rust import SAT, UNSAT, core, fingerprint, make_noise
from tests.test_w027_precheck import verify_certificate, write_dimacs


CAP_SECONDS = 6.0
MEMORY_BYTES = 2 * 1024**3
EXTERNAL = (("vlsat2_684_9417", "UNSAT"), ("vlsat2_1000_22250", "SAT"))
ARM_ORDER = ("kissat", "witnora_plus_kissat", "cryptominisat")


def memory_limit():
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_BYTES, MEMORY_BYTES))


def parse_dimacs(path):
    clauses = []
    current = []
    expected = None
    variables = None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("c"):
            continue
        if line.startswith("p "):
            parts = line.split()
            assert len(parts) == 4 and parts[1] == "cnf" and variables is None
            variables, expected = int(parts[2]), int(parts[3])
            continue
        assert variables is not None
        for word in line.split():
            lit = int(word)
            if lit == 0:
                clauses.append(current)
                current = []
            else:
                assert abs(lit) <= variables
                current.append(lit)
    assert variables is not None and not current and len(clauses) == expected
    return variables, clauses


def classify_solver(completed):
    if completed.returncode not in (0, 10, 20):
        return "ERROR"
    statuses = [line.strip() for line in completed.stdout.splitlines()
                if line.lstrip().startswith("s ")]
    if any(line == "s UNSATISFIABLE" for line in statuses):
        return "UNSAT"
    if any(line == "s SATISFIABLE" for line in statuses):
        return "SAT"
    return "ERROR"


def validate_model(clauses, output):
    assignment = {}
    for line in output.splitlines():
        if not line.lstrip().startswith("v "):
            continue
        for token in line.split()[1:]:
            lit = int(token)
            if lit == 0:
                continue
            key = abs(lit)
            if key in assignment and assignment[key] != (lit > 0):
                return False
            assignment[key] = lit > 0
    if not assignment:
        return False
    return all(any(assignment.get(abs(lit)) == (lit > 0)
                   for lit in clause) for clause in clauses)


def invoke(command, seconds):
    return subprocess.run(command, capture_output=True, text=True, timeout=max(0.02, seconds),
                          preexec_fn=memory_limit)


def run_arm(arm, filename, clauses, expected, precheck, kissat, cms):
    started = time.perf_counter_ns()
    precheck_ns = 0
    downstream_ns = 0
    result = {
        "arm": arm, "verdict": "ERROR", "returncode": None,
        "precheck_wall_ns": 0, "downstream_wall_ns": 0,
        "model_verified": False, "xor_certificate_verified": False,
        "used_downstream_solver": False,
    }
    try:
        if arm == "witnora_plus_kissat":
            scan_start = time.perf_counter_ns()
            scan = invoke([str(precheck), str(filename)], CAP_SECONDS)
            precheck_ns = time.perf_counter_ns() - scan_start
            result["precheck_wall_ns"] = precheck_ns
            if scan.returncode != 0:
                raise RuntimeError("Rust precheck failed: " + scan.stderr[-300:])
            evidence = json.loads(scan.stdout)
            result["precheck_blocks"] = evidence["recovered_xor_equations"]
            result["precheck_status"] = evidence["status"]
            if evidence["status"] == "UNSAT_CERTIFIED":
                if not verify_certificate(clauses, evidence):
                    raise RuntimeError("unsound source-derived UNSAT certificate")
                result.update(verdict="UNSAT", xor_certificate_verified=True, returncode=0)
            elif evidence["status"] != "NO_CERTIFICATE":
                raise RuntimeError("unknown precheck status")
        if result["verdict"] != "UNSAT":
            result["used_downstream_solver"] = True
            binary = cms if arm == "cryptominisat" else kissat
            remaining = CAP_SECONDS - (time.perf_counter_ns() - started) / 1e9
            if remaining <= 0:
                result["verdict"] = "TIMEOUT"
            else:
                solver_start = time.perf_counter_ns()
                completed = invoke([str(binary), str(filename)], remaining)
                downstream_ns = time.perf_counter_ns() - solver_start
                result["downstream_wall_ns"] = downstream_ns
                result["returncode"] = completed.returncode
                result["verdict"] = classify_solver(completed)
                if result["verdict"] == "SAT":
                    result["model_verified"] = validate_model(clauses, completed.stdout)
                    if not result["model_verified"]:
                        raise RuntimeError("solver SAT witness missing or invalid")
        if result["verdict"] in ("SAT", "UNSAT") and result["verdict"] != expected:
            raise RuntimeError("solver result contradicts frozen source label")
        if result["verdict"] == "ERROR":
            raise RuntimeError("solver failed without a valid status")
    except subprocess.TimeoutExpired:
        result["verdict"] = "TIMEOUT"
    result["full_pipeline_wall_ns"] = time.perf_counter_ns() - started
    result["wall_cap_seconds"] = CAP_SECONDS
    if result["full_pipeline_wall_ns"] > (CAP_SECONDS + 1.5) * 1e9:
        raise RuntimeError("wall cap unexpectedly exceeded")
    return result


def prepare_cases(folder):
    cases = []
    archive = json.loads(Path("research/results/w026_mixed_xor_recovery.json").read_text())
    for noise_size in (0, 8192):
        seed, noise = make_noise(noise_size, 0)
        frozen = next(row for row in archive["cases"]
                      if row["noise"] == noise_size and row["replicate"] == 0)
        assert seed == frozen["seed"] and fingerprint(noise) == frozen["noise_fingerprint_fnv64"]
        for parity, expected in ((SAT, "SAT"), (UNSAT, "UNSAT")):
            name = f"w026_d{noise_size}_r0_{expected.lower()}"
            path = folder / (name + ".cnf")
            write_dimacs(path, core(parity) + noise)
            clauses = parse_dimacs(path)[1]
            assert len(clauses) == noise_size + 20
            cases.append((name, expected, path, clauses, "synthetic"))
    w022 = json.loads(Path("research/results/w022_external_vlsat2.json").read_text())
    for name, expected in EXTERNAL:
        source = next(row for row in w022["cases"] if row["id"] == name)
        raw, compressed_sha = download(name)
        assert compressed_sha == source["compressed_sha256"]
        assert hashlib.sha256(raw).hexdigest() == source["cnf_sha256"]
        independent_dimacs_check(raw, name)
        path = folder / (name + ".cnf")
        path.write_bytes(raw)
        clauses = parse_dimacs(path)[1]
        cases.append((name, expected, path, clauses, "external_vlsat2"))
    return cases


def run():
    precheck = Path(os.environ["W027_PRECHECK_BIN"])
    kissat = Path(os.environ["W027_KISSAT_BIN"])
    cms_str = os.environ.get("W027_CMS_BIN")
    cms = Path(cms_str) if cms_str else None
    if cms is not None and not cms.is_file():
        cms = None
    available = [a for a in ARM_ORDER if a != "cryptominisat" or cms is not None]
    rows = []
    with tempfile.TemporaryDirectory(prefix="witnora-w027-smoke-") as directory:
        cases = prepare_cases(Path(directory))
        for i, (name, expected, filename, clauses, stratum) in enumerate(cases):
            digest = hashlib.sha256(filename.read_bytes()).hexdigest()
            for repeat in range(3):
                # Interleave order; no same-arm-first timing advantage.
                shift = (i + repeat) % len(available)
                for arm in available[shift:] + available[:shift]:
                    record = run_arm(arm, filename, clauses, expected, precheck, kissat, cms)
                    record.update(case_id=name, repeat=repeat, stratum=stratum,
                                  expected=expected, cnf_sha256=digest)
                    rows.append(record)
                    print(f"W027 {name} repeat={repeat} {arm}: {record['verdict']} "
                          f"{record['full_pipeline_wall_ns'] / 1e9:.5f}s", flush=True)
    medians = []
    for name in dict.fromkeys(r["case_id"] for r in rows):
        for arm in available:
            selected = [r for r in rows if r["case_id"] == name and r["arm"] == arm]
            solved = [r["full_pipeline_wall_ns"] for r in selected if r["verdict"] in ("SAT", "UNSAT")]
            medians.append({"case_id": name, "arm": arm,
                            "solved_repetitions": len(solved),
                            "timeout_repetitions": sum(r["verdict"] == "TIMEOUT" for r in selected),
                            "median_solved_wall_ns": int(statistics.median(solved)) if solved else None})
    report = {
        "study": "W-CROSSDOMAIN-027", "phase": "exploratory_smoke_not_full_protocol",
        "protocol": "docs/W_CROSSDOMAIN_027_PHASE1_SMOKE_PROTOCOL.md",
        "case_count": 6, "repeats": 3, "hard_wall_seconds": CAP_SECONDS,
        "memory_cap_bytes": MEMORY_BYTES,
        "arm_availability": {arm: arm in available for arm in ARM_ORDER},
        "kissat_source_sha": os.environ["W027_KISSAT_SHA"],
        "cms_source_sha": os.environ.get("W027_CMS_SHA"),
        "rows": rows, "per_case_arm_medians": medians,
        "claim_scope": "exploratory pipeline and soundness; no full W027 performance inference",
    }
    Path(os.environ["W027_REPORT_PATH"]).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("W027 SMOKE COMPLETE", len(rows), "timed invocations", flush=True)


if __name__ == "__main__":
    run()
