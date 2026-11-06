"""Exploratory finite LP search for exact weighted Walsh UNSAT certificates.

The numerical LP only *proposes* nonnegative clause weights. The verifier
reconstructs the complete Fourier bound in Python integers before accepting
the claim; numerical tolerance is never a soundness argument.

This is research into a bounded, sufficient proof rule, not a SAT solver or
novel polynomial-time result. Standard SAT LP relaxations may be stronger.
"""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix


def clause_spectrum(clause: list[int], nvars: int, width: int = 3):
    signs = {}
    for lit in clause:
        if not isinstance(lit, int) or lit == 0 or abs(lit) > nvars:
            raise ValueError("invalid source literal")
        variable = abs(lit)
        sign = 1 if lit > 0 else -1
        if variable in signs and signs[variable] != sign:
            return {}  # satisfied tautologically by every assignment
        signs[variable] = sign
    if len(signs) > width:
        raise ValueError("clause exceeds fixed spectral width")
    variables = sorted(signs)
    coeffs = {}
    for size in range(len(variables) + 1):
        for subset in combinations(variables, size):
            a = (1 << (width-len(variables))) * (-1 if size % 2 else 1)
            for variable in subset:
                a *= signs[variable]
            coeffs[subset] = a
    return coeffs


def audit_integer_weights(clauses, nvars: int, weights: list[int], width: int = 3):
    """Independent exact source-clause verification; no optimizer required."""
    if len(weights) != len(clauses) or not any(w > 0 for w in weights):
        raise ValueError("missing or vacuous source weights")
    if any(not isinstance(w,int) or w < 0 for w in weights):
        raise ValueError("nonnegative integer weights required")
    coefficients = defaultdict(int)
    for clause, weight in zip(clauses, weights):
        for support, term in clause_spectrum(clause, nvars, width).items():
            coefficients[support] += weight * term
    constant = coefficients[()]
    l1 = sum(abs(term) for support,term in coefficients.items() if support)
    lower = constant-l1
    return {"status": "UNSAT_CERTIFIED" if lower > 0 else "NO_CERTIFICATE",
            "lower_bound_numerator": lower, "denominator": 1 << width,
            "source_nonzero_weights": sum(w > 0 for w in weights),
            "constant_numerator": constant, "nonconstant_l1_numerator": l1}


def search_integer_certificate(nvars: int, clauses: list[list[int]],
                               width: int = 3, max_clauses: int = 128,
                               scale: int = 1_000_000):
    """Solve a bounded LP, then round and *exactly audit* proposed weights."""
    m = len(clauses)
    if not m or m > max_clauses or scale < 1:
        raise ValueError("outside frozen bounded pilot")
    spectra = [clause_spectrum(clause, nvars, width) for clause in clauses]
    supports = sorted({support for row in spectra for support in row if support})
    q = len(supports)
    c = np.array([-float(row.get((),0)) for row in spectra]+[1.0]*q)
    inequality = lil_matrix((q*2,m+q),dtype=float)
    for j,support in enumerate(supports):
        for i,row in enumerate(spectra):
            term = row.get(support,0)
            if term:
                inequality[2*j,i] = term
                inequality[2*j+1,i] = -term
        inequality[2*j,m+j] = -1
        inequality[2*j+1,m+j] = -1
    equality = lil_matrix((1,m+q),dtype=float)
    for i in range(m):
        equality[0,i] = 1
    result = linprog(c, A_ub=inequality.tocsr(), b_ub=np.zeros(2*q),
                     A_eq=equality.tocsr(), b_eq=[1.0],
                     bounds=[(0,None)]*(m+q), method="highs")
    if not result.success:
        raise RuntimeError("LP failed: "+result.message)
    weights = [max(0,int(round(v*scale))) for v in result.x[:m]]
    if not any(weights):
        # No nonzero integer weights after rounding is not a certificate.
        return {"status":"NO_CERTIFICATE","optimizer_objective":float(-result.fun),
                "reason":"all candidate weights rounded to zero"}
    audit = audit_integer_weights(clauses,nvars,weights,width)
    return {**audit, "optimizer_objective":float(-result.fun),
            "weights":weights, "phase":"LP candidate + independent integer verifier",
            "candidate_scale":scale}
