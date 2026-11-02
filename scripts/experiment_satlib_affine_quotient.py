"""Source-exact affine quotient for original SATLIB PARITY instances.

Experimental *known* SAT preprocessing, not a proposed new theorem: detect
complete CNF encodings of XORs, eliminate those linear constraints, encode the
remaining clauses in affine free coordinates, and validate any candidate model
against the original raw CNF. All construction/search time is charged.

Only par32-1-c is an operator development target. par32-2-c is a holdout and
must not be passed to the CLI during method development.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from multiprocessing import get_context
from random import Random
from time import perf_counter

from pysat.solvers import Cadical195, Glucose3, Minisat22

from scripts.benchmark_real_satlib_parity_gate import fetch_file, bounded_solve
from witnora_core.xor import detect_cnf_xor_patterns

SOLVERS = {"Minisat22": Minisat22, "Glucose3": Glucose3, "Cadical195": Cadical195}
FIXED_SHA = {"par32-1-c.cnf.Z": "5e3253738e729c3fda8cde22e67b6d8bae0df6d53e9afabb6bd74d5ceb700312"}


def _iter_bits(mask):
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low


def project_source(clauses, nvars, *, order="natural", max_xor_nodes=100000):
    """Return exactly equisatisfiable CNF, decoder, and measured structural data.

    The entire proof obligation is discharged by (1) full-encoding XOR
    recognition in the source, (2) explicit GF(2) elimination, and (3) local
    four-clause definitions of introduced XOR gate variables.
    """
    if order not in ("natural", "residual_first", "reverse"):
        raise ValueError("unsupported pivot order")
    from witnora_core.cnf import CNFFormula

    formula = CNFFormula(clauses)
    detected = detect_cnf_xor_patterns(formula)
    eqs = [e for e in detected.equations if e.safe_use and e.exact_full_encoding]
    used = {tuple(c) for e in eqs for c in e.source_clauses}
    residual = [tuple(c.literals) for c in formula.clauses if c.literals not in used]
    residual_vars = {abs(lit) for clause in residual for lit in clause}

    if order == "natural":
        positions = list(range(1, nvars + 1))
    elif order == "reverse":
        positions = list(range(nvars, 0, -1))
    else:
        positions = sorted(range(1, nvars + 1), key=lambda v: (v not in residual_vars, v))
    variable_position = {v: i for i, v in enumerate(positions)}
    pivots = {}
    for equation in eqs:
        bits = 0
        for v in equation.variables:
            bits ^= 1 << variable_position[v]
        rhs = equation.rhs
        while bits:
            pivot = bits.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = (bits, rhs)
                break
            other_bits, other_rhs = pivots[pivot]
            bits ^= other_bits
            rhs ^= other_rhs
        else:
            if rhs:
                raise ValueError("contradictory source XOR equations")

    free = [i for i in range(nvars) if i not in pivots]
    dimension = len(free)
    # Every original bit = XOR(mask of independent coordinates) XOR constant.
    masks = [0] * nvars
    constants = [0] * nvars
    for j, bit in enumerate(free):
        masks[bit] = 1 << j
    for pivot in sorted(pivots):
        row, rhs = pivots[pivot]
        rest = row ^ (1 << pivot)
        value = rhs
        coordinates = 0
        for pos in _iter_bits(rest):
            coordinates ^= masks[pos]
            value ^= constants[pos]
        masks[pivot] = coordinates
        constants[pivot] = value

    # For each original variable convert its affine expression into a direct
    # literal in the quotient CNF; new intermediate XOR variables are reused.
    original_to_affine = {positions[p]: (masks[p], constants[p]) for p in range(nvars)}
    output = []
    gate_cache = {}
    max_var = dimension

    def expression_var(mask):
        nonlocal max_var
        if mask.bit_count() == 1:
            return mask.bit_length()
        if mask in gate_cache:
            return gate_cache[mask]
        low = mask & -mask
        rest = mask ^ low
        left, right = expression_var(rest), low.bit_length()
        max_var += 1
        if max_var - dimension > max_xor_nodes:
            raise ValueError("projected XOR gate budget exceeded")
        out = max_var
        output.extend([(-left, -right, -out), (-left, right, out),
                       (left, -right, out), (left, right, -out)])
        gate_cache[mask] = out
        return out

    count_zero = 0
    count_satisfied = 0
    residual_widths = []
    for clause in residual:
        transformed = []
        satisfied = False
        coord_support = 0
        for literal in clause:
            mask, constant = original_to_affine[abs(literal)]
            coord_support |= mask
            if mask == 0:
                if bool(constant) == (literal > 0):
                    satisfied = True
                    break
                continue
            local = expression_var(mask)
            transformed.append(local if (literal > 0) ^ bool(constant) else -local)
        if satisfied:
            count_satisfied += 1
            continue
        if not transformed:
            count_zero += 1
        output.append(tuple(transformed))
        residual_widths.append(coord_support.bit_count())

    def decode(model):
        assignment = {abs(lit): lit > 0 for lit in model}
        free_value = sum(1 << i for i in range(dimension) if assignment.get(i + 1, False))
        return {v: bool((mask & free_value).bit_count() % 2 ^ constant)
                for v, (mask, constant) in original_to_affine.items()}

    sizes = Counter(len(c) for c in output)
    info = {"order": order, "nvars_original": nvars,
            "original_clause_count": len(clauses), "exact_xor_rows": len(eqs),
            "independent_xor_rank": len(pivots), "free_dimension": dimension,
            "removed_xor_encoding_clauses": len(used),
            "residual_clauses": len(residual),
            "residual_variables": len(residual_vars),
            "projected_variables": max_var,
            "new_xor_gates": len(gate_cache), "projected_clauses": len(output),
            "projected_clause_widths": dict(sorted(sizes.items())),
            "max_residual_coordinate_support": max(residual_widths, default=0),
            "mean_residual_coordinate_support": round(sum(residual_widths) / len(residual_widths), 3) if residual_widths else 0,
            "constant_true_clauses": count_satisfied, "empty_clauses": count_zero}
    return output, decode, info


def _worker(clauses, nvars, order, solver_name, queue, gate_budget):
    try:
        start = perf_counter()
        quotient, decoder, info = project_source(clauses, nvars, order=order,
                                                 max_xor_nodes=gate_budget)
        info["transform_ms"] = round((perf_counter() - start) * 1000, 2)
        with SOLVERS[solver_name](bootstrap_with=quotient) as solver:
            sat = solver.solve()
            stats = solver.accum_stats()
            if sat:
                model = decoder(solver.get_model())
                if not all(any(model[abs(lit)] == (lit > 0) for lit in c) for c in clauses):
                    raise AssertionError("quotient witness failed original raw CNF")
        info["status"] = "SAT" if sat else "UNSAT"
        info["verified_original_model"] = bool(sat)
        info["conflicts"] = stats.get("conflicts")
        info["total_worker_ms"] = round((perf_counter() - start) * 1000, 2)
        queue.put(info)
    except Exception as exc:
        queue.put({"status": "ERROR", "error": repr(exc)})


def bounded_quotient(clauses, nvars, order, solver_name, timeout_s=3.0,
                     gate_budget=100000):
    if not (0 < timeout_s <= 30):
        raise ValueError("timeout outside safe gate")
    if solver_name not in SOLVERS:
        raise ValueError("unknown solver")
    ctx = get_context("fork")
    queue = ctx.Queue()
    process = ctx.Process(target=_worker, args=(clauses, nvars, order, solver_name,
                                               queue, gate_budget))
    start = perf_counter()
    process.start()
    process.join(timeout_s)
    if process.is_alive():
        process.terminate()
        process.join(2)
        if process.is_alive():
            process.kill()
            process.join(2)
        queue.close()
        return {"status": "UNKNOWN_TIMEOUT", "wall_ms": round((perf_counter() - start) * 1000, 2)}
    if queue.empty():
        queue.close()
        return {"status": "ERROR", "error": "worker missing result"}
    result = queue.get()
    queue.close()
    result["wall_ms"] = round((perf_counter() - start) * 1000, 2)
    return result


def rename_source(clauses, nvars, mode):
    """Semantics-preserving numbering-only controls (no clause changes)."""
    if mode not in ("reverse", "random_1729"):
        raise ValueError("unsupported renaming control")
    permutation = list(range(1, nvars + 1))
    if mode == "reverse":
        permutation.reverse()
    else:
        Random(1729).shuffle(permutation)
    renamed = [tuple((1 if literal > 0 else -1) * permutation[abs(literal) - 1]
                     for literal in clause) for clause in clauses]
    return renamed, permutation


def _renaming_worker(clauses, nvars, mode, solver_name, queue):
    try:
        start = perf_counter()
        renamed, permutation = rename_source(clauses, nvars, mode)
        prep_ms = round((perf_counter() - start) * 1000, 2)
        with SOLVERS[solver_name](bootstrap_with=renamed) as solver:
            sat = solver.solve()
            stats = solver.accum_stats()
            if sat:
                transformed = {abs(lit): lit > 0 for lit in solver.get_model()}
                decoded = {v: transformed[permutation[v - 1]]
                           for v in range(1, nvars + 1)}
                if not all(any(decoded[abs(lit)] == (lit > 0) for lit in c)
                           for c in clauses):
                    raise AssertionError("renaming model failed original raw CNF")
        queue.put({"status": "SAT" if sat else "UNSAT", "control": mode,
                   "verified_original_model": bool(sat), "renaming_ms": prep_ms,
                   "conflicts": stats.get("conflicts"),
                   "total_worker_ms": round((perf_counter() - start) * 1000, 2)})
    except Exception as exc:
        queue.put({"status": "ERROR", "error": repr(exc)})


def bounded_renaming(clauses, nvars, mode, solver_name, timeout_s=7):
    if not (0 < timeout_s <= 30) or solver_name not in SOLVERS:
        raise ValueError("invalid bounded run")
    ctx = get_context("fork")
    queue = ctx.Queue()
    process = ctx.Process(target=_renaming_worker,
                          args=(clauses, nvars, mode, solver_name, queue))
    start = perf_counter()
    process.start()
    process.join(timeout_s)
    if process.is_alive():
        process.terminate()
        process.join(2)
        if process.is_alive():
            process.kill()
            process.join(2)
        queue.close()
        return {"status": "UNKNOWN_TIMEOUT", "wall_ms": round((perf_counter() - start) * 1000, 2)}
    if queue.empty():
        queue.close()
        return {"status": "ERROR", "error": "worker missing result"}
    result = queue.get()
    queue.close()
    result["wall_ms"] = round((perf_counter() - start) * 1000, 2)
    return result


def benchmark(name="par32-1-c.cnf.Z", timeout_s=3.0, orders=("natural", "residual_first"),
              controls=(), solvers=tuple(SOLVERS), repeats=1):
    if name not in FIXED_SHA:
        raise ValueError("only preregistered development instance is permitted")
    if repeats not in (1, 2, 3) or any(s not in SOLVERS for s in solvers):
        raise ValueError("unsupported repeat count or solver")
    if any(c not in ("original", "reverse", "random_1729") for c in controls):
        raise ValueError("unsupported control")
    source = fetch_file(name, True)
    if source["dimacs_sha256"] != FIXED_SHA[name]:
        raise AssertionError("official DIMACS source digest changed")
    results = {}
    for order in orders:
        results[order] = {
            solver: [bounded_quotient(source["clause_lists"], source["variables"],
                                     order, solver, timeout_s) for _ in range(repeats)]
            for solver in solvers
        }
    for control in controls:
        results["control_" + control] = {
            solver: [(bounded_solve(source["clause_lists"], solver, timeout_s)
                      if control == "original" else
                      bounded_renaming(source["clause_lists"], source["variables"],
                                       control, solver, timeout_s))
                     for _ in range(repeats)]
            for solver in solvers
        }
    return {"name": name, "dimacs_sha256": source["dimacs_sha256"],
            "time_budget_per_run_s": timeout_s,
            "repeat_count": repeats,
            "renaming_control_preserves_clauses_and_signs": True,
            "includes_source_processing_in_solver_gate": True,
            "excludes_network_source_download_from_solver_gate": True,
            "results": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--orders", nargs="+", default=["natural", "residual_first"],
                        choices=("natural", "residual_first", "reverse"))
    parser.add_argument("--controls", nargs="*", default=[],
                        choices=("original", "reverse", "random_1729"))
    parser.add_argument("--solvers", nargs="+", default=list(SOLVERS), choices=tuple(SOLVERS))
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args()
    print(json.dumps(benchmark(timeout_s=args.timeout, orders=tuple(args.orders),
                               controls=tuple(args.controls), solvers=tuple(args.solvers),
                               repeats=args.repeats), indent=2))
