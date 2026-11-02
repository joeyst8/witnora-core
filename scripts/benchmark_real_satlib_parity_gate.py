"""Source-hashed official DIMACS PARITY hardship screen (not a novel solver).

Official DIMACS archive .Z objects are fetched in memory and decompressed
with system uncompress; no fixture is generated or substituted. Native PySAT
solvers run in separate bounded child processes so TIMEOUT means UNKNOWN.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from multiprocessing import get_context
from subprocess import run
from time import perf_counter
from urllib.request import urlopen

from witnora_core.dimacs import parse_dimacs_with_raw
from witnora_core.satlib_fingerprint import fingerprint
from witnora_core.xor import detect_cnf_xor_patterns
from scripts.experiment_affine_dimension_diagnostic import gf2_dimension
from scripts.experiment_verified_flip_orbits import kernel_basis


BASE = "https://archive.dimacs.rutgers.edu/pub/challenge/satisfiability/benchmarks/cnf/"
FILES = (
    ("par8-1-c.cnf.Z", True),
    ("par16-1-c.cnf.Z", True),
    ("par16-2-c.cnf.Z", True),
    ("par32-1-c.cnf.Z", True),
    ("par32-2-c.cnf.Z", True),
    ("hole8.cnf.Z", False),
)
SOLVERS = ("Minisat22", "Glucose3", "Cadical195")


def affine_obstruction(formula):
    detected = detect_cnf_xor_patterns(formula)
    source_rows = tuple((sum(1 << (v - 1) for v in eq.variables), eq.rhs)
                        for eq in detected.equations
                        if eq.safe_use and eq.exact_full_encoding)
    source_clauses = {tuple(c) for eq in detected.equations
                      for c in eq.source_clauses}
    residual = [c.literals for c in formula.clauses if c.literals not in source_clauses]
    xor_variables = {v for eq in detected.equations for v in eq.variables}
    residual_vars = {abs(lit) for clause in residual for lit in clause}
    dimension = gf2_dimension(formula.max_var, source_rows)
    projected = None
    if dimension is not None and dimension <= 256:
        kernel = kernel_basis(tuple(mask for mask, _ in source_rows), formula.max_var)
        if len(kernel) != dimension:
            raise AssertionError("projection basis dimension mismatch")
        coordinates = [0] * (formula.max_var + 1)
        for coordinate, vector in enumerate(kernel):
            while vector:
                lowest = vector & -vector
                coordinates[lowest.bit_length()] |= 1 << coordinate
                vector ^= lowest
        supports = []
        for clause in residual:
            union = 0
            for lit in clause:
                union |= coordinates[abs(lit)]
            supports.append(union.bit_count())
        projected = {
            "residual_clause_count": len(supports),
            "min_coordinate_support": min(supports, default=0),
            "max_coordinate_support": max(supports, default=0),
            "mean_coordinate_support": round(sum(supports) / len(supports), 4)
                                       if supports else 0,
            "clauses_over_16_free_coordinates": sum(x > 16 for x in supports),
            "clauses_over_32_free_coordinates": sum(x > 32 for x in supports),
        }
    return {"verified_exact_xor_rows": len(source_rows),
            "xor_only_consistent": dimension is not None,
            "xor_only_free_dimensions": dimension,
            "xor_only_rank": formula.max_var - dimension if dimension is not None else None,
            "source_xor_encoding_clauses": len(source_clauses),
            "residual_non_xor_clauses": len(residual),
            "residual_variables": len(residual_vars),
            "residual_vars_touching_xor": len(residual_vars & xor_variables),
            "projected_residual_support": projected}


def fetch_file(name, expected_sat):
    if not any(name == record[0] for record in FILES):
        raise ValueError("unapproved external benchmark path")
    url = BASE + name
    with urlopen(url, timeout=25) as stream:
        compressed = stream.read(3_000_001)
    if not compressed or len(compressed) > 3_000_000:
        raise ValueError("missing or oversized compressed archive file")
    p = run(["uncompress", "-c"], input=compressed,
            capture_output=True, check=True, timeout=12)
    data = p.stdout
    if not data or len(data) > 12_000_000:
        raise ValueError("missing or oversized DIMACS")
    # The DIMACS reader validates clause counts, signed literals and syntax.
    formula, raw_clauses = parse_dimacs_with_raw(data.decode("ascii"))
    structural = fingerprint(formula)
    obstruction = affine_obstruction(formula)
    return {"name": name, "source_url": url,
            "archive_sha256": sha256(compressed).hexdigest(),
            "dimacs_sha256": sha256(data).hexdigest(),
            "original_bytes": len(data),
            "variables": formula.max_var, "clauses": len(raw_clauses),
            "normalized_clauses": len(formula.clauses),
            "structural_fingerprint": structural,
            "affine_obstruction": obstruction,
            "expected_sat": expected_sat,
            "clause_lists": raw_clauses}


def _worker(clauses, solver_name, output):
    from pysat import solvers
    try:
        solver_type = getattr(solvers, solver_name)
        start = perf_counter()
        with solver_type(bootstrap_with=clauses) as solver:
            sat = solver.solve()
            stats = solver.accum_stats()
            model = solver.get_model() if sat else None
        output.put({"status": "SAT" if sat else "UNSAT",
                    "elapsed_ms": (perf_counter() - start) * 1000,
                    "conflicts": stats.get("conflicts", None),
                    "model": model})
    except Exception as exc:
        output.put({"status": "ERROR", "error": str(exc)})


def bounded_solve(clauses, solver_name, timeout_s=3.0):
    if solver_name not in SOLVERS or not (0 < timeout_s <= 30):
        raise ValueError("invalid solver or time budget")
    ctx = get_context("fork")
    queue = ctx.Queue()
    proc = ctx.Process(target=_worker, args=(clauses, solver_name, queue))
    start = perf_counter()
    proc.start()
    proc.join(timeout_s)
    if proc.is_alive():
        proc.terminate()
        proc.join(2)
        if proc.is_alive():
            proc.kill()
            proc.join(2)
        queue.close()
        return {"status": "UNKNOWN_TIMEOUT", "wall_ms": (perf_counter() - start) * 1000}
    if queue.empty():
        queue.close()
        return {"status": "ERROR", "error": "solver worker exited without result"}
    result = queue.get()
    queue.close()
    result["wall_ms"] = (perf_counter() - start) * 1000
    if result["status"] == "SAT":
        assignment = {abs(lit): lit > 0 for lit in result["model"]}
        if not all(any((lit > 0) == assignment.get(abs(lit)) for lit in clause)
                   for clause in clauses):
            raise AssertionError("SAT model fails original source CNF")
    result.pop("model", None)
    return result


def benchmark(timeout_s=3.0, files=FILES, solvers=SOLVERS):
    with ThreadPoolExecutor(max_workers=3) as pool:
        fetched = list(pool.map(lambda spec: fetch_file(*spec), files))
    cases = []
    for source in fetched:
        results = {}
        for solver in solvers:
            result = bounded_solve(source["clause_lists"], solver, timeout_s)
            if result["status"] in ("SAT", "UNSAT") and (
                (result["status"] == "SAT") != source["expected_sat"]
            ):
                raise AssertionError((source["name"], solver, "source truth contradiction"))
            results[solver] = result
        cases.append({key: value for key, value in source.items() if key != "clause_lists"}
                     | {"results": results})
    return {"summary": {
        "cases": len(cases), "solvers": list(solvers),
        "timeout_per_solver_s": timeout_s,
        "official_archive_source": BASE,
        "all_completed_answers_match_known_truth": True,
        "minisat_timeouts": sum(c["results"].get("Minisat22", {}).get("status") == "UNKNOWN_TIMEOUT"
                                for c in cases),
        "cadical_timeouts": sum(c["results"].get("Cadical195", {}).get("status") == "UNKNOWN_TIMEOUT"
                                 for c in cases),
    }, "cases": cases}


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()
    report = benchmark(timeout_s=args.timeout)
    print(json.dumps(report, indent=2))
