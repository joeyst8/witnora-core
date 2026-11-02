"""Incremental native-XOR syndrome-feasibility oracle for par32-1-c.

Expose 32 right-side syndrome coordinates as solver variables. For every
source-valid left assignment, ask the *same* CryptoMiniSat whether the right
side can realize the complementary signature. On UNSAT, optional sound
conflict clauses can cache entire forbidden 32-bit syndrome cylinders.

This is established incremental SAT under assumptions with exact residual
and source checks, *not* a claim of a novel SAT algorithm or speedup.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from hashlib import sha256
from multiprocessing import get_context
from time import perf_counter

from scripts.benchmark_real_satlib_parity_gate import fetch_file
from scripts.experiment_satlib_affine_quotient import FIXED_SHA
from scripts.experiment_satlib_syndrome_mitm import (
    candidate_natural_separators, exact_separator_counts,
    lift_original_xor_variables, parity_columns, source_local_global,
    split_local_factors,
)


def _boundary_units(boundary, value):
    return [var if value & (1 << i) else -var for i, var in enumerate(boundary)]


def _source_side_solver(split, side, boundary_value):
    from pycryptosat import Solver
    solver = Solver(threads=1)
    solver.add_clauses(split[f"{side}_clauses"])
    for variables, rhs in split[f"{side}_xors"]:
        solver.add_xor_clause(list(variables), bool(rhs))
    for literal in _boundary_units(split["boundary"], boundary_value):
        solver.add_clause([literal])
    return solver


def make_syndrome_oracle(split, side, boundary_value, global_rows, nvars):
    """Use y_i = XOR(original side-interior variables in global row i)."""
    solver = _source_side_solver(split, side, boundary_value)
    interior = set(split[f"{side}_vars"]) - set(split["boundary"])
    indicator_ids = []
    for index, (row, _) in enumerate(global_rows):
        indicator = nvars + index + 1
        solver.add_xor_clause([v for v in row if v in interior] + [indicator], False)
        indicator_ids.append(indicator)
    return solver, tuple(indicator_ids)


def assumptions_for_syndrome(indicator_ids, signature):
    return [v if signature & (1 << i) else -v for i, v in enumerate(indicator_ids)]


def unsat_clause_pattern(conflict_clause, assumptions, indicator_ids):
    """Translate *negated assumption* clause into an exact forbidden cube.

    pycryptosat get_conflict() returns a disjunction falsified by the current
    assumptions (opposite signs), not the assumption literals themselves.
    Reject unexpected output instead of accepting an unsound generalization.
    """
    if not conflict_clause:
        return None
    inverse = {v: index for index, v in enumerate(indicator_ids)}
    assumed = set(assumptions)
    mask = 0
    values = 0
    for literal in conflict_clause:
        if -literal not in assumed or abs(literal) not in inverse:
            return None
        bit = 1 << inverse[abs(literal)]
        mask |= bit
        if literal < 0:
            values |= bit
    return mask, values


def forbidden(patterns, signature):
    return any((signature & mask) == value for mask, value in patterns)


def add_forbidden_pattern(patterns, pattern):
    """Subsumption-pruned exact union of forbidden syndrome cubes."""
    if pattern is None:
        return False
    mask, values = pattern
    if any((old_mask & mask) == old_mask and (old_value & old_mask) == (values & old_mask)
           for old_mask, old_value in patterns):
        return False
    patterns[:] = [(old_mask, old_value) for old_mask, old_value in patterns
                   if not ((old_mask & mask) == mask and (old_value & mask) == values)]
    patterns.append(pattern)
    return True


def indexed_forbidden(index, signature):
    """Exact cube-union lookup with one lookup per *distinct* bitmask."""
    return any((signature & mask) in values for mask, values in index.items())


def add_indexed_pattern(index, pattern):
    if pattern is None:
        return False
    mask, value = pattern
    values = index.setdefault(mask, set())
    if value in values:
        return False
    values.add(value)
    return True


def incremental_syndrome_search(raw_clauses, nvars, *, cache_cores=True,
                                 indexed_cache=False, time_budget_s=30):
    if cache_cores not in (True, False) or not (0 < time_budget_s <= 60):
        raise ValueError("invalid frozen experiment configuration")
    if indexed_cache and not cache_cores:
        raise ValueError("indexed cache requires caching enabled")
    start = perf_counter()
    deadline = start + time_budget_s
    residual, variables, local, global_rows, _, source_equations = source_local_global(
        raw_clauses, nvars, return_source_equations=True)
    candidates = candidate_natural_separators(variables, residual, local)
    split = split_local_factors(residual, variables, local, candidates[0])
    source_ms = round((perf_counter() - start) * 1000, 2)
    counts = exact_separator_counts(split)
    count_ms = round((perf_counter() - start) * 1000 - source_ms, 2)
    if counts["local_model_count_from_join"] != 704494193:
        raise AssertionError("local count conservation failed")
    columns, full_target = parity_columns(global_rows)
    boundary = split["boundary"]
    batches = sorted(counts["conditional_model_counts"],
                     key=lambda x: (-(x["left"] * x["right"]), x["boundary_bits"]))
    records = []
    for batch in batches:
        b = batch["boundary_bits"]
        small = "left" if batch["left"] <= batch["right"] else "right"
        large = "right" if small == "left" else "left"
        if min(batch["left"], batch["right"]) > 50000:
            records.append({"boundary_bits": b, "status": "SKIP_SMALL_SIDE_CAP"})
            continue
        if perf_counter() > deadline:
            records.append({"boundary_bits": b, "status": "UNKNOWN_TIME_BUDGET"})
            break
        small_solver = _source_side_solver(split, small, b)
        large_solver, indicators = make_syndrome_oracle(split, large, b,
                                                         global_rows, nvars)
        small_interior = tuple(v for v in split[f"{small}_vars"] if v not in boundary)
        large_interior = tuple(v for v in split[f"{large}_vars"] if v not in boundary)
        boundary_mask = 0
        boundary_signature = 0
        for j, v in enumerate(boundary):
            if b & (1 << j):
                boundary_mask |= 1 << (v - 1)
                boundary_signature ^= columns.get(v, 0)
        queried = set()
        cores = []
        cube_index = {}
        stats = Counter()
        core_sizes = Counter()
        while perf_counter() < deadline:
            sat, model = small_solver.solve()
            if not sat:
                if stats["small_models"] != batch[small]:
                    raise AssertionError("small-side count contradicted exact DP")
                records.append({"boundary_bits": b, "status": "EXHAUSTIVE_BATCH_UNSAT",
                                "statistics": dict(stats), "stored_cores": len(cores)})
                break
            stats["small_models"] += 1
            signature = 0
            small_mask = 0
            block = []
            for v in small_interior:
                truth = bool(model[v])
                block.append(-v if truth else v)
                if truth:
                    signature ^= columns.get(v, 0)
                    small_mask |= 1 << (v - 1)
            small_solver.add_clause(block)
            required = full_target ^ boundary_signature ^ signature
            if required in queried:
                stats["duplicate_signature_skips"] += 1
                continue
            if cache_cores and (indexed_forbidden(cube_index, required)
                                if indexed_cache else forbidden(cores, required)):
                stats["core_cache_skips"] += 1
                continue
            queried.add(required)
            assumptions = assumptions_for_syndrome(indicators, required)
            result, large_model = large_solver.solve(assumptions=assumptions)
            stats["oracle_queries"] += 1
            if result is None:
                records.append({"boundary_bits": b, "status": "UNKNOWN_ORACLE"})
                return {"status": "UNKNOWN_INCOMPLETE", "records": records,
                        "elapsed_ms": round((perf_counter() - start) * 1000, 2)}
            if result:
                large_mask = sum(1 << (v - 1) for v in large_interior if large_model[v])
                combined = boundary_mask | small_mask | large_mask
                assignment = {v: bool(combined & (1 << (v - 1))) for v in variables}
                full = lift_original_xor_variables(raw_clauses, nvars, assignment,
                                                   source_equations=source_equations)
                digest = sha256(bytes(int(full[v]) for v in range(1, nvars + 1))).hexdigest()
                records.append({"boundary_bits": b, "status": "SYNDROME_ORACLE_SAT",
                                "statistics": dict(stats),
                                "core_size_histogram": dict(core_sizes),
                                "stored_cores": sum(map(len, cube_index.values()))
                                    if indexed_cache else len(cores),
                                "distinct_cache_masks": len(cube_index) if indexed_cache else None})
                return {"status": "SAT_VERIFIED_ORIGINAL", "model_sha256": digest,
                        "matched_boundary_bits": b, "cache_cores": cache_cores,
                        "indexed_cache": indexed_cache,
                        "source_ms": source_ms, "exact_count_ms": count_ms,
                        "elapsed_ms": round((perf_counter() - start) * 1000, 2),
                        "records": records}
            if cache_cores:
                conflict = large_solver.get_conflict()
                pattern = unsat_clause_pattern(conflict, assumptions, indicators)
                if pattern is not None:
                    core_sizes[pattern[0].bit_count()] += 1
                    inserted = (add_indexed_pattern(cube_index, pattern)
                                if indexed_cache else add_forbidden_pattern(cores, pattern))
                    if inserted:
                        stats["new_conflict_cubes"] += 1
        else:
            records.append({"boundary_bits": b, "status": "UNKNOWN_TIME_BUDGET",
                            "statistics": dict(stats),
                            "core_size_histogram": dict(core_sizes),
                            "stored_cores": sum(map(len, cube_index.values()))
                                if indexed_cache else len(cores),
                            "distinct_cache_masks": len(cube_index) if indexed_cache else None})
            break
    return {"status": "UNKNOWN_INCOMPLETE", "cache_cores": cache_cores,
            "indexed_cache": indexed_cache,
            "elapsed_ms": round((perf_counter() - start) * 1000, 2),
            "source_ms": source_ms, "exact_count_ms": count_ms,
            "records": records, "no_unsat_inference": True}


def _worker(clauses, nvars, cache_cores, indexed_cache, budget_s, queue):
    try:
        queue.put(incremental_syndrome_search(clauses, nvars,
                                             cache_cores=cache_cores,
                                             indexed_cache=indexed_cache,
                                             time_budget_s=budget_s))
    except Exception as exc:
        queue.put({"status": "ERROR", "error": repr(exc)})


def bounded_syndrome_oracle(clauses, nvars, *, cache_cores=True,
                           indexed_cache=False, budget_s=30):
    if not (0 < budget_s <= 60):
        raise ValueError("invalid worker cap")
    ctx = get_context("fork")
    queue = ctx.Queue()
    worker = ctx.Process(target=_worker, args=(clauses, nvars, cache_cores,
                                              indexed_cache, budget_s, queue))
    start = perf_counter()
    worker.start()
    worker.join(budget_s)
    if worker.is_alive():
        worker.terminate()
        worker.join(2)
        if worker.is_alive():
            worker.kill()
            worker.join(2)
        queue.close()
        return {"status": "UNKNOWN_TIMEOUT", "wall_ms": round((perf_counter() - start) * 1000, 2)}
    if queue.empty():
        queue.close()
        return {"status": "ERROR", "error": "oracle worker returned no data"}
    result = queue.get()
    queue.close()
    result["wall_ms"] = round((perf_counter() - start) * 1000, 2)
    return result


def benchmark(name="par32-1-c.cnf.Z", *, cache_cores=True,
              indexed_cache=False, budget_s=30):
    if name not in FIXED_SHA:
        raise ValueError("holdout locked")
    source = fetch_file(name, True)
    if source["dimacs_sha256"] != FIXED_SHA[name]:
        raise AssertionError("official source SHA changed")
    return {"source": name, "dimacs_sha256": source["dimacs_sha256"],
            "solver": "pycryptosat 5.17.0; single-thread",
            "incremental_assumption_oracle": bounded_syndrome_oracle(
                source["clause_lists"], source["variables"],
                cache_cores=cache_cores, indexed_cache=indexed_cache,
                budget_s=budget_s)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--without-core-cache", action="store_true")
    parser.add_argument("--indexed-cache", action="store_true")
    parser.add_argument("--budget", type=float, default=30)
    args = parser.parse_args()
    print(json.dumps(benchmark(cache_cores=not args.without_core_cache,
                               indexed_cache=args.indexed_cache,
                               budget_s=args.budget), indent=2))
