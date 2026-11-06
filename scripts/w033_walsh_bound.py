"""Exact low-width Walsh spectrum of a CNF's clause-violation count.

For a Boolean assignment s in {-1,+1}^n, let E(s) count clauses
violated by s.  E is a multilinear polynomial (the Walsh expansion),
whose integer-scaled coefficients are computed directly from clauses.

The triangle inequality gives E(s) >= (constant - sum(abs(nonconstant)))/2^w.
Whenever this lower bound is positive, the original formula is UNSAT.
This is a sufficient condition, not a complete SAT procedure.

This module is research-only and does not claim the inequality is new.
"""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations


def walsh_bound(nvars: int, clauses: list[list[int]], max_width: int = 3) -> dict:
    """Compute exact integer-scaled Walsh L1 lower bound for low-width CNF.

    Raises ValueError for wider clauses, invalid literals, or invalid width.
    A tautological clause contributes zero; repeated literals are reduced.
    """
    if nvars < 0 or max_width < 0 or max_width > 20:
        raise ValueError("invalid nvars or max_width")
    coeffs: dict[tuple[int, ...], int] = defaultdict(int)
    used = 0
    tautologies = 0
    for clause in clauses:
        signs = {}
        tautology = False
        for lit in clause:
            if not isinstance(lit, int) or lit == 0 or abs(lit) > nvars:
                raise ValueError("invalid source literal")
            variable = abs(lit)
            sign = 1 if lit > 0 else -1
            if variable in signs and signs[variable] != sign:
                tautology = True
                break
            signs[variable] = sign
        if tautology:
            tautologies += 1
            continue
        if len(signs) > max_width:
            raise ValueError("clause exceeds bounded Walsh width")
        used += 1
        variables = sorted(signs)
        scalar = 1 << (max_width - len(variables))
        for size in range(len(variables) + 1):
            for subset in combinations(variables, size):
                weight = scalar * (-1 if size % 2 else 1)
                for variable in subset:
                    weight *= signs[variable]
                coeffs[subset] += weight

    constant = coeffs.get((), 0)
    nonconstant_l1 = sum(abs(value) for support, value in coeffs.items() if support)
    lower_numerator = constant - nonconstant_l1
    denominator = 1 << max_width
    return {
        "variables": nvars, "source_clauses": len(clauses),
        "non_tautological_clauses": used, "tautological_clauses": tautologies,
        "fourier_nonzero_nonconstant_terms": sum(bool(value) for support, value in coeffs.items() if support),
        "constant_numerator": constant,
        "nonconstant_l1_numerator": nonconstant_l1,
        "lower_bound_numerator": lower_numerator,
        "denominator": denominator,
        "status": "UNSAT_CERTIFIED" if lower_numerator > 0 else "NO_CERTIFICATE",
    }
