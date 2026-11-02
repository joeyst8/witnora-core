"""Fixed post-hoc XOR-aware CryptoMiniSat baseline against frozen PR119 cases.

This is a direct plain-DIMACS CNF challenge; no explicit XOR extension supplied.
Original inputs and their SHA-256-equivalent Witnora formula hashes were frozen
before this CryptoMiniSat baseline. A timeout is UNKNOWN, never a solver loss.
Native Witnora timings exclude Lean verification; CMS times include process
startup and DIMACS file read. Do NOT interpret these as an apples-to-apples race.
"""
from __future__ import annotations

import argparse
from itertools import product
import json
from pathlib import Path
import re
import shutil
from statistics import median
import subprocess
import sys
import tempfile
from time import perf_counter_ns

from scripts.experiment_noisy_tseitin_source_subset import (
    drop_one_xor_clause, make_case, source_subset_candidate,
)

FROZEN_HASHES = {
    (64, 47, 1): "0eec2fad66e671abfa9c03901c05295adc3923f4cb1c2030afb85f87354c3d9d",
    (64, 47, 4): "298b9ad6005e02eeaeb6b7bbca04608a3f26a3a99cc5bc12aecfc94200c64335",
    (64, 73, 1): "1ddb30bfee9632997766e58404141262cf85a3a782cd451f9955681f1efd831d",
    (64, 73, 4): "7fad95cbd80b59e25273185ea620946260f93f9735bf7485015da51e565d67ec",
    (96, 47, 1): "b7872ce4921ce3ecb0aad3d0d911d1991160d39d4102e47c3cbddcc2151c308d",
    (96, 47, 4): "be06eefd3b97a2810a63b8125c0731f6f8bb86435c1530b8e1c6ebb97d17dcef",
    (96, 73, 1): "5fc8913b5ceb6c444e9b25bdfa4d7054a255404c880624201c0cca4fb66e6b9f",
    (96, 73, 4): "a6629b1282403d0f3ada0e6cae9d7b7366bc7f481cf0804eeddc84cb47e30c5f",
    (128, 47, 1): "974e3a7bdadd66ad467542d2d71d92a3453e4ddb0900316a30049a512c3b2338",
    (128, 47, 4): "00455281f75649cbf8e29dbb8261bccf4f2eb94be5e4105935f002646372f1e0",
    (128, 73, 1): "318df66f91952934570d08362104dceb3813ea10ac8d945f2d85593c7e1742f7",
    (128, 73, 4): "ad326ff5dd501c9f9f916a581c5acd81dcdd0af468c6788a774d5990fdd25a90",
}
FROZEN_CONTROLS = {
    "sat_even64": "cb466b08d47f3da5c173f3a22617259c26c7fb9bdd73c068b763c4d2883d40fe",
    "sat_missing_xor_clause64": "9bd0b4b297a69955189a7cf298957cbf878251d3b7669a3e20c0e7a9582eab06",
}
SIZES = (64, 96, 128)
SEEDS = (47, 73)
NOISE_LEVELS = (1, 4)


def check_frozen_hash(formula, expected, label):
    if formula.formula_hash != expected:
        raise AssertionError(f"frozen input changed for {label}: {formula.formula_hash} != {expected}")


def cryptominisat_plain_cnf(formula, timeout_s):
    binary = shutil.which("cryptominisat5")
    if not binary:
        raise RuntimeError("cryptominisat5 binary unavailable; fail closed")
    # Isolate a fresh solver process and limit it externally.
    with tempfile.TemporaryDirectory(prefix="witnora-cms-") as folder:
        dimacs = Path(folder) / "source.cnf"
        dimacs.write_text(formula.canonical_dimacs(), encoding="ascii")
        start = perf_counter_ns()
        try:
            run = subprocess.run(
                [binary, "--verb", "0", str(dimacs)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=timeout_s, check=False,
            )
        except subprocess.TimeoutExpired:
            return {"status": "UNKNOWN_TIMEOUT",
                    "wall_ms": round((perf_counter_ns() - start) / 1e6, 6)}
        elapsed = round((perf_counter_ns() - start) / 1e6, 6)
        statuses = re.findall(r"(?m)^s\s+(SATISFIABLE|UNSATISFIABLE|UNKNOWN)\s*$", run.stdout)
        if len(statuses) != 1:
            return {"status": "ERROR", "wall_ms": elapsed,
                    "return_code": run.returncode,
                    "stdout_tail": run.stdout[-500:],
                    "stderr_tail": run.stderr[-500:]}
        label = {"SATISFIABLE": "SAT", "UNSATISFIABLE": "UNSAT",
                 "UNKNOWN": "UNKNOWN_SOLVER"}[statuses[0]]
        if (label == "UNSAT" and run.returncode not in (0, 20)) or (
            label == "SAT" and run.returncode not in (0, 10)):
            raise AssertionError(f"contradictory CryptoMiniSat exit code {run.returncode} for {label}")
        return {"status": label, "wall_ms": elapsed, "return_code": run.returncode}



def native_fresh_process_plain_cnf(formula, timeout_s):
    """Time Python launch + DIMACS parse + native certificate work, like CLI solver."""
    with tempfile.TemporaryDirectory(prefix="witnora-native-") as folder:
        dimacs = Path(folder) / "source.cnf"
        dimacs.write_text(formula.canonical_dimacs(), encoding="ascii")
        start = perf_counter_ns()
        try:
            run = subprocess.run(
                [sys.executable, "-m", "scripts.noisy_tseitin_native_cli",
                 "--source", str(dimacs), "--expected-hash", formula.formula_hash],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                timeout=timeout_s, check=False,
            )
        except subprocess.TimeoutExpired:
            return {"status": "UNKNOWN_TIMEOUT",
                    "wall_ms": round((perf_counter_ns() - start) / 1e6, 6)}
        elapsed = round((perf_counter_ns() - start) / 1e6, 6)
        if run.returncode != 0:
            raise AssertionError(f"fresh-process native checker exited {run.returncode}: {run.stderr[-500:]}")
        try:
            report = json.loads(run.stdout)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"fresh-process native output invalid: {run.stdout[-500:]}") from exc
        if report["source_hash"] != formula.formula_hash:
            raise AssertionError("fresh-process native check read a different formula")
        return {"status": report["status"], "wall_ms": elapsed,
                "native_internal_ms": report["native_internal_ms"],
                "lean_formal_status": "NOT_LEAN_VERIFIED"}


def median_or_none(values):
    return round(median(values), 6) if values else None


def run_experiment(timeout_s):
    rows = []
    for vertices, seed, noise in product(SIZES, SEEDS, NOISE_LEVELS):
        source = make_case(vertices, seed, noise, odd=True)
        check_frozen_hash(source, FROZEN_HASHES[(vertices, seed, noise)],
                          (vertices, seed, noise))
        candidate, _, _ = source_subset_candidate(
            source, f"cms_n{vertices}_seed{seed}_noise{noise}")
        if candidate["status"] != "SOURCE_SUBSET_G5_NATIVE_UNSAT_CANDIDATE":
            raise AssertionError("native source-subset contradiction failed")
        cms = cryptominisat_plain_cnf(source, timeout_s)
        fresh = native_fresh_process_plain_cnf(source, timeout_s)
        if fresh["status"] != "SOURCE_SUBSET_G5_NATIVE_UNSAT_CANDIDATE":
            raise AssertionError(f"fresh-process native contradiction failed: {fresh}")
        if cms["status"] not in ("UNSAT", "UNKNOWN_TIMEOUT", "UNKNOWN_SOLVER"):
            raise AssertionError(f"CryptoMiniSat contradicts frozen UNSAT or errored: {cms}")
        rows.append({
            "vertices": vertices, "seed": seed, "noise_per_vertex": noise,
            "source_sha256": source.formula_hash,
            "native": {
                "status": candidate["status"],
                "elapsed_ms": candidate["elapsed_ms"],
                "lean_formal_status": "NOT_LEAN_VERIFIED",
            },
            "cryptominisat5": cms,
            "native_fresh_process": fresh,
        })
    controls = []
    sat_formulas = (
        ("sat_even64", make_case(64, 101, 4, odd=False)),
        ("sat_missing_xor_clause64", drop_one_xor_clause(
            make_case(64, 101, 4, odd=True), 64, 101)),
    )
    for name, source in sat_formulas:
        check_frozen_hash(source, FROZEN_CONTROLS[name], name)
        native, _, _ = source_subset_candidate(source, name)
        cms = cryptominisat_plain_cnf(source, timeout_s)
        fresh = native_fresh_process_plain_cnf(source, timeout_s)
        if native["status"] != "DIAGNOSTIC_ONLY" or cms["status"] != "SAT" or fresh["status"] != "DIAGNOSTIC_ONLY":
            raise AssertionError(f"SAT control failed closed: {name}, {native['status']}, {cms}")
        controls.append({"name": name, "source_sha256": source.formula_hash,
                         "native_status": native["status"], "cryptominisat5": cms,
                         "native_fresh_process": fresh})
    solved = [r for r in rows if r["cryptominisat5"]["status"] == "UNSAT"]
    return {
        "kind": "FROZEN_NOISY_TSEITIN_MATCHED_PROCESS_AND_XOR_AWARE_BASELINE",
        "scope": "same 12 source hashes as frozen holdout; direct plain-DIMACS CryptoMiniSat5",
        "prior_art": "CryptoMiniSat Gaussian elimination / XOR reasoning is established; no novelty claim",
        "limitation": "fresh-process native and CryptoMiniSat include process startup/DIMACS parse; Python/compiled-language overheads differ; both exclude per-instance Lean kernel runtime",
        "solver_timeout_s": timeout_s, "rows": rows, "sat_controls": controls,
        "summary": {
            "cases": len(rows), "native_certified": len(rows),
            "native_fresh_process_certified": sum(r["native_fresh_process"]["status"] == "SOURCE_SUBSET_G5_NATIVE_UNSAT_CANDIDATE" for r in rows),
            "native_fresh_process_timeout": sum(r["native_fresh_process"]["status"] == "UNKNOWN_TIMEOUT" for r in rows),
            "native_fresh_process_wins_matched_input_boundary": sum(r["native_fresh_process"]["wall_ms"] < r["cryptominisat5"]["wall_ms"] for r in solved),
            "median_native_fresh_process_wall_ms": median_or_none([r["native_fresh_process"]["wall_ms"] for r in rows]),
            "cms_unsat": len(solved),
            "cms_timeout": sum(r["cryptominisat5"]["status"] == "UNKNOWN_TIMEOUT" for r in rows),
            "cms_unknown_solver": sum(r["cryptominisat5"]["status"] == "UNKNOWN_SOLVER" for r in rows),
            "native_wins_on_cms_solved_unbalanced_timing": sum(
                r["native"]["elapsed_ms"] < r["cryptominisat5"]["wall_ms"] for r in solved),
            "median_native_all_ms": median_or_none(
                [r["native"]["elapsed_ms"] for r in rows]),
            "median_native_matched_cms_solved_ms": median_or_none(
                [r["native"]["elapsed_ms"] for r in solved]),
            "median_cms_matched_solved_wall_ms": median_or_none(
                [r["cryptominisat5"]["wall_ms"] for r in solved]),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout-s", type=float, default=3.0)
    parser.add_argument("--out", type=Path,
                        default=Path("noisy_tseitin_frozen_cryptominisat.json"))
    args = parser.parse_args()
    if not 0.2 <= args.timeout_s <= 5:
        parser.error("timeout outside preregistered safe bound")
    result = run_experiment(args.timeout_s)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
