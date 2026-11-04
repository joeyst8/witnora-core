"""Planted satisfiable near-threshold 3-CNF cores behind exact XOR boundaries.

Synthetic difficulty is a hypothesis, not a guaranteed hardness classification.
All-true assignment is planted to independently establish satisfiability.
"""
from __future__ import annotations

import random

from .cnf import CNFFormula
from .xor import canonical_xor_cnf_clauses


def make_hard_separator_case(blocks: int, core_vars: int, width: int,
                             seed: int) -> tuple[CNFFormula, dict]:
    if blocks not in (2, 4, 8) or core_vars not in (18, 26) or width not in (2, 3):
        raise ValueError("case outside preregistered stress grid")
    rng = random.Random(seed)
    boundary = tuple(range(1, width + 1))
    rows = set()
    for block in range(blocks):
        local = tuple(range(100 + block * 100, 100 + block * 100 + core_vars))
        rows.update(canonical_xor_cnf_clauses(
            (*boundary, local[0], local[1]), (width + 2) % 2))
        for _ in range(round(4.2 * core_vars)):
            chosen = rng.sample(local, 3)
            signs = [bool(rng.getrandbits(1)) for _ in chosen]
            if not any(signs):
                signs[rng.randrange(3)] = True
            rows.add(tuple(sorted(v if pos else -v for v, pos in zip(chosen, signs))))
    formula = CNFFormula.from_raw_clauses(rows)
    return formula, {
        "blocks": blocks, "core_vars": core_vars, "width": width,
        "seed": seed, "boundary": boundary,
        "planted_satisfiable": True,
    }


def make_hard_separator_case_rust(
    blocks: int, core_vars: int, width: int, seed: int,
) -> tuple[CNFFormula, dict]:
    """Opt-in native CNF assembly; preserve Python's seeded sample stream."""
    from witnora_ve import make_hard_separator_case_native
    if blocks not in (2, 4, 8) or core_vars not in (18, 26) or width not in (2, 3):
        raise ValueError("case outside preregistered stress grid")
    rng = random.Random(seed)
    samples = []
    for block in range(blocks):
        local = tuple(range(100 + block * 100, 100 + block * 100 + core_vars))
        block_rows = []
        for _ in range(round(4.2 * core_vars)):
            chosen = rng.sample(local, 3)
            signs = [bool(rng.getrandbits(1)) for _ in chosen]
            if not any(signs):
                signs[rng.randrange(3)] = True
            block_rows.append([v if pos else -v for v, pos in zip(chosen, signs)])
        samples.append(block_rows)
    clauses = make_hard_separator_case_native(blocks,core_vars,width,samples)
    return CNFFormula.from_raw_clauses(clauses), {
        "blocks": blocks, "core_vars": core_vars, "width": width,
        "seed": seed, "boundary": tuple(range(1, width + 1)),
        "planted_satisfiable": True,
    }
