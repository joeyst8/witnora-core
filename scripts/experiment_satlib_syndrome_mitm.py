"""Feasibility gate for a source-bound meet-in-the-middle parity-syndrome join.

Find a *real* vertex separator of the nonlinear+186-local-XOR primal graph.
Only if each conditional side has a manageable number of solutions should
we enumerate those side models and hash their 32-bit parity syndromes.

This is established separator/MITM mathematics, not an originality claim.
"""
from __future__ import annotations

import argparse
import json
from hashlib import sha256
from itertools import combinations
from multiprocessing import get_context
from time import perf_counter

from scripts.benchmark_real_satlib_parity_gate import fetch_file
from scripts.experiment_satlib_affine_quotient import FIXED_SHA
from scripts.experiment_satlib_residual_fourier import _bits, source_residual_parity_rows
from scripts.experiment_satlib_residual_geometry import (
    _minfill_upper_bound, exact_bounded_width_count,
)


def source_local_global(clauses, nvars):
    residual, variables, rows, info = source_residual_parity_rows(clauses, nvars)
    local = [(tuple(_bits(mask)), rhs) for mask, rhs in rows if mask.bit_count() == 3]
    global_rows = [(tuple(_bits(mask)), rhs) for mask, rhs in rows if mask.bit_count() > 3]
    if len(local) != 186 or len(global_rows) != 32:
        raise ValueError("this operator is not preregistered for this structure")
    return residual, variables, local, global_rows, info


def candidate_natural_separators(variables, clauses, local, *, min_side=100):
    graph = {v: set() for v in variables}
    for support in [tuple(abs(lit) for lit in clause) for clause in clauses] + \
                   [row for row, _ in local]:
        for a, b in combinations(set(support), 2):
            graph[a].add(b)
            graph[b].add(a)
    candidates = []
    for t in range(min(variables), max(variables)):
        left = {v for v in variables if v <= t}
        right = set(variables) - left
        boundary = {v for v in left if graph[v] & right}
        interior = left - boundary
        if len(interior) < min_side or len(right) < min_side:
            continue
        if any(graph[v] & right for v in interior):
            raise AssertionError("invalid separator: cross-edge remained")
        candidates.append({"cut_after_var": t, "boundary": tuple(sorted(boundary)),
                           "interior_left_count": len(interior),
                           "right_count": len(right),
                           "boundary_size": len(boundary),
                           "balance_offset": abs(len(interior) - len(right))})
    return sorted(candidates, key=lambda x: (x["boundary_size"],
                                             x["balance_offset"], x["cut_after_var"]))


def split_local_factors(residual, variables, local, candidate):
    boundary = set(candidate["boundary"])
    interior_left = {v for v in variables if v <= candidate["cut_after_var"]} - boundary
    right = set(variables) - interior_left - boundary
    left_clauses, right_clauses, left_xors, right_xors = [], [], [], []
    for clause in residual:
        support = {abs(lit) for lit in clause}
        if support & interior_left:
            if support & right:
                raise AssertionError("crossing clause invalidates separator")
            left_clauses.append(clause)
        elif support & right:
            right_clauses.append(clause)
        else:
            left_clauses.append(clause)
    for variables_, rhs in local:
        support = set(variables_)
        if support & interior_left:
            if support & right:
                raise AssertionError("crossing XOR invalidates separator")
            left_xors.append((variables_, rhs))
        elif support & right:
            right_xors.append((variables_, rhs))
        else:
            left_xors.append((variables_, rhs))
    return {"boundary": tuple(sorted(boundary)),
            "left_vars": tuple(sorted(interior_left | boundary)),
            "right_vars": tuple(sorted(right | boundary)),
            "left_clauses": left_clauses, "right_clauses": right_clauses,
            "left_xors": left_xors, "right_xors": right_xors}


def exact_separator_counts(split):
    """Compute all 2^|boundary| conditional solution counts, then cross-check."""
    boundary = split["boundary"]
    if len(boundary) > 10:
        raise ValueError("separator too wide for explicit conditional count")
    sides = {}
    for side in ("left", "right"):
        clauses = split[f"{side}_clauses"]
        equations = split[f"{side}_xors"]
        variables = split[f"{side}_vars"]
        scopes = [tuple(abs(lit) for lit in c) for c in clauses]
        scopes += [support for support, _ in equations]
        width = _minfill_upper_bound(variables, scopes, include_order=True)
        if width["minfill_upper_bound_width"] > 12:
            raise ValueError("side width exceeds exact counting cap")
        sides[side] = (width, variables, clauses, equations)

    count_rows = []
    for bits in range(1 << len(boundary)):
        units = [((var,) if bits & (1 << j) else (-var,))
                 for j, var in enumerate(boundary)]
        record = {"boundary_bits": bits}
        for side in ("left", "right"):
            width, variables, clauses, equations = sides[side]
            count, scope = exact_bounded_width_count(
                clauses + units, variables, width["elimination_order"],
                parity_equations=equations, max_scope_cap=13)
            if scope > width["minfill_upper_bound_width"] + 1:
                raise AssertionError("separator width factor mismatch")
            record[side] = count
        count_rows.append(record)
    product_sum = sum(x["left"] * x["right"] for x in count_rows)
    enumerations = sum(x["left"] + x["right"] for x in count_rows)
    return {"boundary": list(boundary),
            "left_width": sides["left"][0]["minfill_upper_bound_width"],
            "right_width": sides["right"][0]["minfill_upper_bound_width"],
            "conditional_model_counts": count_rows,
            "local_model_count_from_join": product_sum,
            "total_side_models_to_enumerate": enumerations,
            "largest_side_batch": max(max(x["left"], x["right"]) for x in count_rows)}


def parity_columns(global_rows):
    """For a partial model, XOR its true-variable column masks."""
    columns = {}
    rhs = 0
    for i, (support, value) in enumerate(global_rows):
        if value:
            rhs |= 1 << i
        for variable in support:
            columns[variable] = columns.get(variable, 0) ^ (1 << i)
    return columns, rhs


def enumerate_side_syndromes(split, side, boundary_bits, columns,
                              *, model_limit, deadline, match_signatures=None,
                              required_syndrome=None):
    """Enumerate source-local side assignments with native XOR constraints.

    Keeps just one representative per syndrome. The caller may infer a full
    impossibility result only when this enumeration is exhaustive.
    """
    from pycryptosat import Solver
    variables = split[f"{side}_vars"]
    boundary = split["boundary"]
    interior = tuple(v for v in variables if v not in boundary)
    solver = Solver(threads=1)
    solver.add_clauses(split[f"{side}_clauses"])
    for row, rhs in split[f"{side}_xors"]:
        solver.add_xor_clause(list(row), bool(rhs))
    for j, var in enumerate(boundary):
        solver.add_clause([var if boundary_bits & (1 << j) else -var])
    signatures = {}
    count = 0
    while True:
        if count >= model_limit or perf_counter() > deadline:
            return signatures, count, False, None
        sat, model = solver.solve()
        if not sat:
            return signatures, count, True, None
        count += 1
        source_mask = 0
        signature = 0
        block = []
        for var in interior:
            value = bool(model[var])
            block.append(-var if value else var)
            if value:
                source_mask |= 1 << (var - 1)
                signature ^= columns.get(var, 0)
        signatures.setdefault(signature, source_mask)
        if match_signatures is not None:
            other = match_signatures.get(signature ^ required_syndrome)
            if other is not None:
                if other & source_mask:
                    raise AssertionError("joined side interiors overlap")
                return signatures, count, False, other | source_mask
        solver.add_clause(block)


def xor_join(left, right, needed):
    """Match original variable bitmasks for complementary XOR syndromes."""
    for syndrome, left_model in left.items():
        right_model = right.get(syndrome ^ needed)
        if right_model is not None:
            if left_model & right_model:
                raise AssertionError("separator interior overlap")
            return left_model | right_model
    return None


def lift_original_xor_variables(clauses, nvars, residual_assignment):
    """Reconstruct XOR-only variables, then insist on the full raw CNF audit."""
    from witnora_core.cnf import CNFFormula
    from witnora_core.xor import detect_cnf_xor_patterns
    source = detect_cnf_xor_patterns(CNFFormula(clauses))
    equations = [eq for eq in source.equations if eq.safe_use and eq.exact_full_encoding]
    pivots = {}
    for eq in equations:
        rhs = eq.rhs
        mask = 0
        for var in eq.variables:
            if var in residual_assignment:
                rhs ^= int(residual_assignment[var])
            else:
                mask ^= 1 << (var - 1)
        while mask:
            pivot = mask.bit_length()
            if pivot not in pivots:
                pivots[pivot] = (mask, rhs)
                break
            old_mask, old_rhs = pivots[pivot]
            mask ^= old_mask
            rhs ^= old_rhs
        else:
            if rhs:
                raise AssertionError("candidate fails original XOR constraints")
    unknown = set(range(1, nvars + 1)) - set(residual_assignment)
    if set(pivots) != unknown:
        raise AssertionError("original XOR auxiliary variables not uniquely determined")
    result = dict(residual_assignment)
    for var in sorted(pivots):
        mask, rhs = pivots[var]
        mask ^= 1 << (var - 1)
        for other in _bits(mask):
            rhs ^= int(result[other])
        result[var] = bool(rhs)
    if not all(any(result[abs(lit)] == (lit > 0) for lit in clause)
               for clause in clauses):
        raise AssertionError("meet-in-middle model failed original raw CNF")
    return result


def matched_hash_prototype(raw_clauses, nvars, *, model_cap_per_side=50000,
                           time_budget_s=30, include_witness=False):
    """Bounded experiment, not a complete SAT procedure if batches are skipped."""
    if model_cap_per_side != 50000 or not (0 < time_budget_s <= 60):
        raise ValueError("experiment budget parameters locked")
    start = perf_counter()
    deadline = start + time_budget_s
    residual, variables, local, wide, _ = source_local_global(raw_clauses, nvars)
    candidates = candidate_natural_separators(variables, residual, local)
    candidate = candidates[0]
    split = split_local_factors(residual, variables, local, candidate)
    source_structure_ms = round((perf_counter() - start) * 1000, 2)
    count = exact_separator_counts(split)
    conditional_count_ms = round((perf_counter() - start) * 1000 - source_structure_ms, 2)
    if count["local_model_count_from_join"] != 704494193:
        raise AssertionError("local model conservation failed")
    columns, global_target = parity_columns(wide)
    batches = sorted(count["conditional_model_counts"],
                     key=lambda b: (-(b["left"] * b["right"]), b["boundary_bits"]))
    records = []
    for batch in batches:
        b = batch["boundary_bits"]
        if max(batch["left"], batch["right"]) > model_cap_per_side:
            records.append({"boundary_bits": b, "status": "SKIP_SIDE_MODEL_CAP"})
            continue
        if perf_counter() > deadline:
            records.append({"boundary_bits": b, "status": "UNKNOWN_TIME_BUDGET"})
            break
        left_start = perf_counter()
        left, left_count, left_complete, _ = enumerate_side_syndromes(
            split, "left", b, columns, model_limit=model_cap_per_side, deadline=deadline)
        left_enumeration_ms = round((perf_counter() - left_start) * 1000, 2)
        if not left_complete or left_count != batch["left"]:
            records.append({"boundary_bits": b, "status": "UNKNOWN_LEFT_ENUMERATION",
                            "enumerated": left_count})
            break
        boundary_mask = 0
        boundary_signature = 0
        for j, var in enumerate(split["boundary"]):
            if b & (1 << j):
                boundary_mask |= 1 << (var - 1)
                boundary_signature ^= columns.get(var, 0)
        right_start = perf_counter()
        right, right_count, right_complete, found = enumerate_side_syndromes(
            split, "right", b, columns, model_limit=model_cap_per_side,
            deadline=deadline, match_signatures=left,
            required_syndrome=global_target ^ boundary_signature)
        right_enumeration_ms = round((perf_counter() - right_start) * 1000, 2)
        if found is not None:
            all_bits = found | boundary_mask
            source_assignment = {v: bool(all_bits & (1 << (v - 1))) for v in variables}
            full = lift_original_xor_variables(raw_clauses, nvars, source_assignment)
            witness_bytes = bytes(int(full[v]) for v in range(1, nvars + 1))
            records.append({"boundary_bits": b, "status": "EARLY_STREAMED_SIGNATURE_MATCH",
                            "left_models": left_count, "right_models_seen": right_count})
            result = {"status": "SAT_VERIFIED_ORIGINAL", "matched_boundary_bits": b,
                    "elapsed_ms": round((perf_counter() - start) * 1000, 2),
                    "phase_ms": {"source_detection_and_separator": source_structure_ms,
                                 "eight_conditional_exact_counts": conditional_count_ms,
                                 "left_enumeration": left_enumeration_ms,
                                 "right_streamed_enumeration": right_enumeration_ms},
                    "verified_original_variables": nvars,
                    "verified_original_clauses": len(raw_clauses),
                    "model_boolean_vector_sha256": sha256(witness_bytes).hexdigest(),
                    "records": records}
            if include_witness:
                result["positive_original_variable_ids"] = [
                    v for v in range(1, nvars + 1) if full[v]
                ]
            return result
        if not right_complete or right_count != batch["right"]:
            records.append({"boundary_bits": b, "status": "UNKNOWN_RIGHT_ENUMERATION",
                            "enumerated": right_count})
            break
        records.append({"boundary_bits": b, "status": "EXHAUSTIVE_BATCH",
                        "left_models": left_count, "right_models": right_count,
                        "left_signatures": len(left), "right_signatures": len(right)})
        if xor_join(left, right, global_target ^ boundary_signature) is not None:
            raise AssertionError("streaming join failed to report an available match")
    return {"status": "UNKNOWN_INCOMPLETE", "elapsed_ms": round((perf_counter() - start) * 1000, 2),
            "records": records, "no_unsat_inference": True}


def _bounded_worker(clauses, nvars, queue, time_budget_s, include_witness):
    try:
        queue.put(matched_hash_prototype(clauses, nvars, time_budget_s=time_budget_s,
                                         include_witness=include_witness))
    except Exception as exc:
        queue.put({"status": "ERROR", "error": repr(exc)})


def bounded_matched_hash(clauses, nvars, time_budget_s=30, *, include_witness=False):
    if not (0 < time_budget_s <= 60):
        raise ValueError("invalid bounded worker budget")
    ctx = get_context("fork")
    queue = ctx.Queue()
    p = ctx.Process(target=_bounded_worker,
                    args=(clauses, nvars, queue, time_budget_s, include_witness))
    start = perf_counter()
    p.start()
    p.join(time_budget_s)
    if p.is_alive():
        p.terminate()
        p.join(2)
        if p.is_alive():
            p.kill()
            p.join(2)
        queue.close()
        return {"status": "UNKNOWN_TIMEOUT", "wall_ms": round((perf_counter() - start) * 1000, 2)}
    if queue.empty():
        queue.close()
        return {"status": "ERROR", "error": "worker exited without result"}
    output = queue.get()
    queue.close()
    output["wall_ms"] = round((perf_counter() - start) * 1000, 2)
    return output


def feasibility(clauses, nvars):
    residual, variables, local, global_rows, _ = source_local_global(clauses, nvars)
    candidates = candidate_natural_separators(variables, residual, local)
    best = candidates[0] if candidates else None
    counts = exact_separator_counts(split_local_factors(residual, variables, local, best)) \
        if best and best["boundary_size"] <= 8 else None
    if counts is not None and counts["local_model_count_from_join"] != 704494193:
        raise AssertionError("separator product does not match independently counted local models")
    return {"development_instance_only": True, "residual_vars": len(variables),
            "narrow_rows": len(local), "global_rows": len(global_rows),
            "candidate_count": len(candidates), "best_ten": candidates[:10],
            "best_boundary_size": candidates[0]["boundary_size"] if candidates else None,
            "exact_boundary_conditioned_counts": counts,
            "candidate_selection_frozen": "min boundary then balanced variable count"}


def benchmark(name="par32-1-c.cnf.Z", *, run_solver=False, emit_witness=False):
    if name not in FIXED_SHA:
        raise ValueError("holdout locked")
    source = fetch_file(name, True)
    if source["dimacs_sha256"] != FIXED_SHA[name]:
        raise AssertionError("source checksum mismatch")
    report = {"benchmark": name, "source_sha": source["dimacs_sha256"]}
    if run_solver:
        report["matched_hash_solver"] = bounded_matched_hash(source["clause_lists"],
                                                             source["variables"],
                                                             include_witness=emit_witness)
    else:
        report["feasibility"] = feasibility(source["clause_lists"], source["variables"])
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="par32-1-c.cnf.Z")
    parser.add_argument("--run-solver", action="store_true")
    parser.add_argument("--emit-witness", action="store_true")
    args = parser.parse_args()
    print(json.dumps(benchmark(args.name, run_solver=args.run_solver,
                               emit_witness=args.emit_witness), indent=2))
