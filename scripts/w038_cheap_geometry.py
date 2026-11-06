"""Source-only O(m k^2 + n^3) signed-geometry features; no clause-pair loops."""

from __future__ import annotations

import numpy as np


FEATURE_NAMES = ('degree_imbalance', 'pair_overlap', 'signed_interaction_spectral_radius')


def cheap_features(nvars: int, clauses: list[list[int]]) -> dict:
    if nvars < 1 or not clauses:
        raise ValueError('nonempty CNF and positive variable count required')
    positive = [0] * nvars
    negative = [0] * nvars
    signed_matrix = np.zeros((nvars, nvars), dtype=float)
    m = len(clauses)
    for clause in clauses:
        if not 1 <= len(clause) <= 3:
            raise ValueError('clauses must have width one to three')
        signs = {}
        for lit in clause:
            if not isinstance(lit, int) or lit == 0 or abs(lit) > nvars:
                raise ValueError('invalid literal')
            var = abs(lit)
            if var in signs:
                raise ValueError('repeated variable within clause')
            signs[var] = 1 if lit > 0 else -1
            (positive if lit > 0 else negative)[var - 1] += 1
        variables = sorted(signs)
        for i, a in enumerate(variables):
            for b in variables[i + 1:]:
                weight = signs[a] * signs[b] / m
                signed_matrix[a - 1, b - 1] += weight
                signed_matrix[b - 1, a - 1] += weight
    counts = [p + q for p, q in zip(positive, negative)]
    all_literals = sum(counts)
    pair_shared_count = sum(d * (d - 1) // 2 for d in counts)
    pair_count = m * (m - 1) // 2
    return {
        'degree_imbalance': sum(abs(p - q) for p, q in zip(positive, negative)) / all_literals,
        'pair_overlap': pair_shared_count / (3 * pair_count) if pair_count else 0.0,
        'signed_interaction_spectral_radius': float(np.max(np.abs(np.linalg.eigvalsh(signed_matrix)))),
    }
