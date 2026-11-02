"""Precommitted non-parity falsification of frozen syndrome ROBDD operator.

Use original SHA-checked DIMACS files, never generated substitutes. The
precommitted protocol is research/PR119_NONPARITY_PRECOMMITTED_PROTOCOL.md,
committed before these four sources were downloaded. UNSAT is only a complete
backend conclusion; source-structure failure is explicitly UNSUPPORTED.
"""
from __future__ import annotations

import argparse
import json
from hashlib import sha256
from multiprocessing import get_context
from subprocess import run
from time import perf_counter
from urllib.request import urlopen

from scripts.benchmark_real_satlib_parity_gate import BASE
from scripts.experiment_satlib_symbolic_cross_instance_gate import (
    cross_instance_symbolic_search,
)
from witnora_core.dimacs import parse_dimacs_with_raw


FROZEN_NONPARITY_SOURCES = {
    "hole8.cnf.Z": {
        "sha256": "e63ad9adca73c42dab2f89a3cec77dbf7800d595f72ce740b32004431e1bfd84",
        "expected_sat": False, "family": "pigeonhole"},
    "dubois20.cnf.Z": {
        "sha256": "82059aba0e5773644b386eb6bcbe53680655390cb041873a3cb3e93f7bd896a7",
        "expected_sat": False, "family": "dubois"},
    "aim-50-1_6-yes1-1.cnf.Z": {
        "sha256": "d96f1edb1db3d0e55a3ff0f7707517e41a79374acbb857df051e5441ab27657d",
        "expected_sat": True, "family": "AIM"},
    "aim-50-1_6-no-1.cnf.Z": {
        "sha256": "c0441193ae63b66e71461248e82273805f7194123263314ae73f318cdfa78b9d",
        "expected_sat": False, "family": "AIM"},
}


def fetch_frozen_source(name):
    if name not in FROZEN_NONPARITY_SOURCES:
        raise ValueError("unapproved source or sealed holdout")
    with urlopen(BASE + name, timeout=25) as stream:
        compressed = stream.read(3_000_001)
    if not compressed or len(compressed) > 3_000_000:
        raise ValueError("missing or oversized official archive")
    data = run(["uncompress", "-c"], input=compressed, capture_output=True,
               check=True, timeout=12).stdout
    if not data or len(data) > 12_000_000:
        raise ValueError("missing or oversized original DIMACS")
    digest = sha256(data).hexdigest()
    if digest != FROZEN_NONPARITY_SOURCES[name]["sha256"]:
        raise AssertionError("original DIMACS source SHA differs from frozen record")
    formula, clauses = parse_dimacs_with_raw(data.decode("ascii"))
    return {"source": name, "sha256": digest, "variables": formula.max_var,
            "clauses": len(clauses), "clause_lists": clauses,
            "expected_sat": FROZEN_NONPARITY_SOURCES[name]["expected_sat"],
            "family": FROZEN_NONPARITY_SOURCES[name]["family"]}


def classify_and_fallback(clauses, nvars, *, budget_s=12):
    """Charge the frozen classification before running an unmodified solver.

    If the frozen operator applies and completes SAT, use its independently
    source-verified model. Otherwise, only explicitly unsupported formulas
    are forwarded to unmodified single-thread CryptoMiniSat.
    """
    if not (0 < budget_s <= 30):
        raise ValueError("invalid portfolio cap")
    start = perf_counter()
    try:
        result = cross_instance_symbolic_search(clauses, nvars, budget_s=budget_s)
    except AssertionError as exc:
        if str(exc) != "contradictory exact source XOR system":
            raise
        # This is *not* a checked proof; it is a structural diagnostic that
        # still requires a complete backend UNSAT decision. Preserve it.
        result = {"status": "POTENTIAL_UNAUDITED_XOR_CONTRADICTION"}
    structural_ms = round((perf_counter() - start) * 1000, 2)
    if result["status"] == "SAT_VERIFIED_ORIGINAL":
        return {"status": "SAT_VERIFIED_ORIGINAL", "operator_used": True,
                "structural_status": result["status"], "structural_ms": structural_ms,
                "full_worker_ms": structural_ms, "verified_original_model": True}
    if not (result["status"].startswith("UNSUPPORTED_") or
            result["status"] == "POTENTIAL_UNAUDITED_XOR_CONTRADICTION"):
        return {"status": "UNKNOWN_INCOMPLETE", "operator_used": False,
                "structural_status": result["status"], "structural_ms": structural_ms,
                "full_worker_ms": structural_ms, "no_unsat_inference": True}

    from pycryptosat import Solver
    solver = Solver(threads=1)
    solver.add_clauses(clauses)
    sat, model = solver.solve()
    if sat is None:
        return {"status": "UNKNOWN_BACKEND", "operator_used": False,
                "structural_status": result["status"], "structural_ms": structural_ms,
                "full_worker_ms": round((perf_counter() - start) * 1000, 2),
                "no_unsat_inference": True}
    if sat:
        assignment = {i: bool(model[i]) for i in range(1, nvars + 1)}
        if not all(any(assignment[abs(lit)] == (lit > 0) for lit in clause)
                   for clause in clauses):
            raise AssertionError("fallback model violates original DIMACS")
        status = "SAT_VERIFIED_BACKEND"
    else:
        status = "UNSAT_BACKEND"
    return {"status": status, "operator_used": False,
            "structural_status": result["status"], "structural_ms": structural_ms,
            "full_worker_ms": round((perf_counter() - start) * 1000, 2),
            "verified_original_model": bool(sat)}


def plain_general_cms(clauses, nvars):
    """Raw original-CNF CryptoMiniSat, correctly supporting SAT *and* UNSAT."""
    from pycryptosat import Solver, __version__
    start = perf_counter()
    solver = Solver(threads=1)
    solver.add_clauses(clauses)
    sat, model = solver.solve()
    if sat is None:
        return {"status": "UNKNOWN_BACKEND", "no_unsat_inference": True,
                "worker_ms": round((perf_counter() - start) * 1000, 2)}
    if sat:
        assignment = {i: bool(model[i]) for i in range(1, nvars + 1)}
        if not all(any(assignment[abs(lit)] == (lit > 0) for lit in clause)
                   for clause in clauses):
            raise AssertionError("raw baseline model violates original DIMACS")
        status = "SAT_VERIFIED_BACKEND"
    else:
        status = "UNSAT_BACKEND"
    return {"status": status, "solver": "raw pycryptosat",
            "version": __version__, "threads": 1,
            "worker_ms": round((perf_counter() - start) * 1000, 2),
            "verified_original_model": bool(sat)}


def _plain_worker(clauses, nvars, queue):
    try:
        queue.put(plain_general_cms(clauses, nvars))
    except Exception as exc:
        queue.put({"status": "ERROR", "error": repr(exc)})


def bounded_plain_cms(clauses, nvars, *, budget_s=12):
    if not (0 < budget_s <= 30):
        raise ValueError("invalid baseline cap")
    ctx = get_context("fork")
    queue = ctx.Queue()
    process = ctx.Process(target=_plain_worker, args=(clauses, nvars, queue))
    start = perf_counter()
    process.start()
    process.join(budget_s)
    if process.is_alive():
        process.terminate()
        process.join(2)
        if process.is_alive():
            process.kill()
            process.join(2)
        queue.close()
        return {"status": "UNKNOWN_TIMEOUT", "wall_ms": round(
            (perf_counter() - start) * 1000, 2), "no_unsat_inference": True}
    if queue.empty():
        queue.close()
        return {"status": "ERROR", "error": "raw baseline worker did not return"}
    result = queue.get()
    queue.close()
    result["wall_ms"] = round((perf_counter() - start) * 1000, 2)
    return result


def _portfolio_worker(clauses, nvars, budget_s, queue):
    try:
        queue.put(classify_and_fallback(clauses, nvars, budget_s=budget_s))
    except Exception as exc:
        queue.put({"status": "ERROR", "error": repr(exc)})


def bounded_portfolio(clauses, nvars, *, budget_s=12):
    if not (0 < budget_s <= 30):
        raise ValueError("invalid worker cap")
    ctx = get_context("fork")
    queue = ctx.Queue()
    process = ctx.Process(target=_portfolio_worker,
                          args=(clauses, nvars, budget_s, queue))
    start = perf_counter()
    process.start()
    process.join(budget_s)
    if process.is_alive():
        process.terminate()
        process.join(2)
        if process.is_alive():
            process.kill()
            process.join(2)
        queue.close()
        return {"status": "UNKNOWN_TIMEOUT", "no_unsat_inference": True,
                "wall_ms": round((perf_counter() - start) * 1000, 2)}
    if queue.empty():
        queue.close()
        return {"status": "ERROR", "error": "portfolio worker did not return"}
    result = queue.get()
    queue.close()
    result["wall_ms"] = round((perf_counter() - start) * 1000, 2)
    return result


def _assert_completed_truth(outcome, expected_sat, source):
    status = outcome["status"]
    if status in ("SAT", "SAT_VERIFIED_BACKEND", "SAT_VERIFIED_ORIGINAL") and not expected_sat:
        raise AssertionError((source, "SAT contradicts known source UNSAT"))
    if status in ("UNSAT", "UNSAT_BACKEND") and expected_sat:
        raise AssertionError((source, "UNSAT contradicts known source SAT"))


def benchmark(*, names=tuple(FROZEN_NONPARITY_SOURCES), repeats=2, budget_s=12):
    if not names or any(n not in FROZEN_NONPARITY_SOURCES for n in names):
        raise ValueError("unapproved source / holdout must remain sealed")
    if repeats not in (1, 2) or not (0 < budget_s <= 12):
        raise ValueError("outside precommitted repeat/time contract")
    results = []
    for name in names:
        source = fetch_frozen_source(name)
        trials = []
        for index in range(repeats):
            portfolio = bounded_portfolio(source["clause_lists"],
                                          source["variables"], budget_s=budget_s)
            raw = bounded_plain_cms(source["clause_lists"], source["variables"],
                                    budget_s=budget_s)
            _assert_completed_truth(portfolio, source["expected_sat"], name)
            _assert_completed_truth(raw, source["expected_sat"], name)
            trials.append({"trial": index + 1, "portfolio": portfolio,
                           "raw_cms": raw})
        results.append({"source": name, "family": source["family"],
                        "sha256": source["sha256"], "variables": source["variables"],
                        "clauses": source["clauses"], "expected_sat": source["expected_sat"],
                        "trials": trials})
    return {"protocol": "research/PR119_NONPARITY_PRECOMMITTED_PROTOCOL.md",
            "source_download_and_parsing_excluded_both_arms": True,
            "sealed_holdout_untouched": True, "results": results}


def compact_benchmark(result):
    """Preserve complete trial status, expose timings without large records."""
    return {"protocol": result["protocol"],
            "sealed_holdout_untouched": result["sealed_holdout_untouched"],
            "results": [{"source": record["source"],
                         "family": record["family"],
                         "sha256": record["sha256"],
                         "expected_sat": record["expected_sat"],
                         "trials": [{"trial": trial["trial"],
                                     "structural_status": trial["portfolio"].get(
                                         "structural_status"),
                                     "structural_ms": trial["portfolio"].get(
                                         "structural_ms"),
                                     "portfolio_status": trial["portfolio"]["status"],
                                     "portfolio_ms": trial["portfolio"].get(
                                         "full_worker_ms"),
                                     "raw_status": trial["raw_cms"]["status"],
                                     "raw_ms": trial["raw_cms"].get("worker_ms"),
                                     "portfolio_wall_ms": trial["portfolio"].get(
                                         "wall_ms"),
                                     "raw_wall_ms": trial["raw_cms"].get("wall_ms")}
                                    for trial in record["trials"]]}
                        for record in result["results"]]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--names", nargs="+", default=list(FROZEN_NONPARITY_SOURCES),
                        choices=list(FROZEN_NONPARITY_SOURCES))
    parser.add_argument("--repeats", type=int, default=2, choices=(1, 2))
    parser.add_argument("--budget", type=float, default=12)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    report = benchmark(names=tuple(args.names), repeats=args.repeats,
                       budget_s=args.budget)
    print(json.dumps(compact_benchmark(report) if args.compact else report,
                     indent=2))
