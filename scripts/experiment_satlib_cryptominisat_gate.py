"""XOR-aware solver challenge to the source-exact SATLIB affine quotient.

The source is the locked official par32-1-c DIMACS object. par32-2-c is a
sealed holdout, deliberately not accepted here. Each worker's wall clock
includes normalization, source XOR discovery (when needed), transformation,
CryptoMiniSat startup, solving, and full raw-source model verification.
File download is intentionally outside the measured solver cap for every arm.
"""
from __future__ import annotations

import argparse
import json
from multiprocessing import get_context
from time import perf_counter

from scripts.benchmark_real_satlib_parity_gate import fetch_file
from scripts.experiment_satlib_affine_quotient import FIXED_SHA, project_source
from witnora_core.cnf import CNFFormula
from witnora_core.xor import detect_cnf_xor_patterns

MODES = ("raw_cnf", "native_xor", "affine_quotient")


def native_xor_source(clauses):
    """Partition exact complete XOR CNF encodings from residual clauses."""
    formula = CNFFormula(clauses)
    detected = detect_cnf_xor_patterns(formula)
    equations = [e for e in detected.equations if e.safe_use and e.exact_full_encoding]
    source = {tuple(c) for eq in equations for c in eq.source_clauses}
    residual = [list(c.literals) for c in formula.clauses if c.literals not in source]
    rows = [(list(eq.variables), bool(eq.rhs)) for eq in equations]
    return residual, rows, {"source_bound_xor_rows": len(rows),
                             "removed_exact_encoding_clauses": len(source),
                             "residual_clauses": len(residual)}


def _worker(raw_clauses, nvars, mode, queue):
    try:
        from pycryptosat import Solver, __version__
        start = perf_counter()
        decoder = None
        info = {"mode": mode, "solver": "pycryptosat", "version": __version__,
                "threads": 1}
        if mode == "raw_cnf":
            # Give CryptoMiniSat itself the opportunity to recover XORs.
            ordinary = raw_clauses
            xors = []
        elif mode == "native_xor":
            ordinary, xors, metadata = native_xor_source(raw_clauses)
            info.update(metadata)
        elif mode == "affine_quotient":
            ordinary, decoder, metadata = project_source(raw_clauses, nvars,
                                                        order="natural")
            xors = []
            info.update(metadata)
        else:
            raise ValueError("unsupported CryptoMiniSat mode")
        solver = Solver(threads=1)
        solver.add_clauses(ordinary)
        for vars_, rhs in xors:
            solver.add_xor_clause(vars_, rhs)
        info["preparation_ms"] = round((perf_counter() - start) * 1000, 2)
        sat, model = solver.solve()
        info["total_worker_ms"] = round((perf_counter() - start) * 1000, 2)
        if sat is None:
            info["status"] = "UNKNOWN"
        elif sat:
            if decoder is not None:
                original = decoder([i if model[i] else -i for i in range(1, len(model))])
            else:
                original = {i: bool(model[i]) for i in range(1, nvars + 1)}
            if not all(any(original[abs(lit)] == (lit > 0) for lit in c)
                       for c in raw_clauses):
                raise AssertionError("CryptoMiniSat witness violates original CNF")
            info["status"] = "SAT"
            info["verified_original_model"] = True
        else:
            # The locked source is known SAT; an UNSAT result indicates a bug.
            raise AssertionError("UNSAT contradicts official SAT source")
        queue.put(info)
    except Exception as exc:
        queue.put({"status": "ERROR", "mode": mode, "error": repr(exc)})


def bounded_cms(raw_clauses, nvars, mode, timeout_s=7):
    if mode not in MODES or not (0 < timeout_s <= 30):
        raise ValueError("unsupported mode or timeout")
    ctx = get_context("fork")
    queue = ctx.Queue()
    worker = ctx.Process(target=_worker, args=(raw_clauses, nvars, mode, queue))
    start = perf_counter()
    worker.start()
    worker.join(timeout_s)
    if worker.is_alive():
        worker.terminate()
        worker.join(2)
        if worker.is_alive():
            worker.kill()
            worker.join(2)
        queue.close()
        return {"status": "UNKNOWN_TIMEOUT", "mode": mode,
                "wall_ms": round((perf_counter() - start) * 1000, 2)}
    if queue.empty():
        queue.close()
        return {"status": "ERROR", "mode": mode, "error": "worker missing result"}
    result = queue.get()
    queue.close()
    result["wall_ms"] = round((perf_counter() - start) * 1000, 2)
    return result


def benchmark(*, name="par32-1-c.cnf.Z", timeout_s=7, repeats=2, modes=MODES):
    if name not in FIXED_SHA or repeats not in (1, 2, 3):
        raise ValueError("holdout locked or unsupported repeat count")
    source = fetch_file(name, True)
    if source["dimacs_sha256"] != FIXED_SHA[name]:
        raise AssertionError("DIMACS hash changed")
    if any(m not in MODES for m in modes):
        raise ValueError("unknown CryptoMiniSat mode")
    return {"benchmark": name, "dimacs_sha256": source["dimacs_sha256"],
            "solver": "CryptoMiniSat 5 via pycryptosat", "timeout_s": timeout_s,
            "repeats": repeats, "holdout_untouched": True,
            "wall_clock_includes_all_preprocessing": True,
            "network_download_excluded_every_arm": True,
            "results": {mode: [bounded_cms(source["clause_lists"], source["variables"],
                                           mode, timeout_s) for _ in range(repeats)]
                        for mode in modes}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=7)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--modes", nargs="+", choices=MODES, default=list(MODES))
    args = parser.parse_args()
    print(json.dumps(benchmark(timeout_s=args.timeout, repeats=args.repeats,
                               modes=tuple(args.modes)), indent=2))
