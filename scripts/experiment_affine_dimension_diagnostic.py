"""Synthetic diagnostic for the algebraic-space branching hypothesis.

NOT a reproduction of the separate PARITY 16/32-bit SATLIB experiments.
Count affine free dimensions and unresolved CNF clauses after disjoint
clause-branch constraints, using exact GF(2) row elimination.
"""
from __future__ import annotations

from random import Random


def gf2_dimension(nvars, rows):
    """Return free affine dimension, or None for an inconsistent system."""
    basis = {}
    for mask, bit in rows:
        mask, bit = int(mask), int(bit) & 1
        while mask:
            pivot = mask.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (mask, bit)
                break
            old_mask, old_bit = basis[pivot]
            mask ^= old_mask
            bit ^= old_bit
        else:
            if bit:
                return None
    return nvars - len(basis)


def literal_row(lit, make_true):
    value = lit > 0 if make_true else lit < 0
    return 1 << (abs(lit) - 1), int(value)


def disjoint_clause_branches(nvars, rows, clause):
    """Each branch fixes earlier literals false, then its literal true."""
    prefix = []
    branches = []
    for lit in clause:
        new_rows = (*rows, *prefix, literal_row(lit, True))
        dimension = gf2_dimension(nvars, new_rows)
        if dimension is not None:
            branches.append((new_rows, dimension))
        prefix.append(literal_row(lit, False))
    return branches


def unresolved_count(nvars, rows, clauses):
    return sum(gf2_dimension(nvars, (*rows, *(
        literal_row(lit, False) for lit in clause))) is not None
        for clause in clauses)


def synthetic_instance(nvars, seed):
    rng = Random(630000 + 100 * nvars + seed)
    planted = {v: rng.randrange(2) for v in range(1, nvars + 1)}
    rows = []
    for _ in range(nvars // 2):
        variables = rng.sample(range(1, nvars + 1), 3)
        mask = sum(1 << (v - 1) for v in variables)
        rhs = sum(planted[v] for v in variables) % 2
        rows.append((mask, rhs))
    clauses = []
    for _ in range(2 * nvars):
        variables = rng.sample(range(1, nvars + 1), 3)
        clause = [v if rng.randrange(2) else -v for v in variables]
        if not any((lit > 0) == bool(planted[abs(lit)]) for lit in clause):
            clause[0] = -clause[0]
        clauses.append(tuple(clause))
    return tuple(rows), tuple(clauses)


def trace_case(nvars, seed, steps=5):
    rows, clauses = synthetic_instance(nvars, seed)
    trace = []
    for step in range(steps + 1):
        dimension = gf2_dimension(nvars, rows)
        unresolved = unresolved_count(nvars, rows, clauses)
        trace.append({"step": step, "free_dimension": dimension,
                      "unresolved_clauses": unresolved})
        if step == steps or not unresolved:
            break
        candidate = None
        for clause in clauses:
            branches = disjoint_clause_branches(nvars, rows, clause)
            if len(branches) == 0:
                continue
            # A clause already implied by the current affine state is not
            # useful to split: its branches cover the entire current state.
            count = sum(1 << d for _, d in branches)
            if count == 1 << dimension:
                continue
            score = (count, tuple(clause))
            if candidate is None or score < candidate[0]:
                candidate = (score, branches)
        if candidate is None:
            break
        # Stress-test the largest surviving branch, not an oracle-picked model.
        rows, _ = max(candidate[1], key=lambda item: item[1])
    return trace


def run(seeds=8, steps=5):
    if not 1 <= seeds <= 32 or not 1 <= steps <= 12:
        raise ValueError("invalid experiment budget")
    records = [
        {"nvars": nvars, "seed": seed, "trace": trace_case(nvars, seed, steps)}
        for nvars in (16, 32) for seed in range(seeds)
    ]
    return {
        "status": "SYNTHETIC_DIAGNOSTIC_NOT_SATLIB_REPRODUCTION",
        "records": records,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))
