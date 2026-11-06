"""Post-hoc W038 diagnostic; SAT labels are an unavailable oracle, not deployable inputs."""

from __future__ import annotations

import numpy as np

from scripts.benchmark_w038_independent import SIZES, RIDGE, size_folds, mse
from scripts.w038_cheap_geometry import FEATURE_NAMES


def oracle_label_control(rows):
    """Fivefold OOF baseline versus features with the true SAT/UNSAT answer as an oracle.

    This is not the preregistered W038 test; it diagnoses potential label mediation.
    """
    sizes = [row['clause_count'] for row in rows]
    folds = size_folds(sizes)
    y = np.array([row['target_log_scans'] for row in rows])
    x = np.array([[row['cheap_features'][k] for k in FEATURE_NAMES] for row in rows])
    basis = np.array([[float(m == s) for s in SIZES] + [float(row['verdict'] == 'SAT')]
                      for m, row in zip(sizes, rows)])
    plain = np.empty(len(y)); enhanced = np.empty(len(y))
    for fold in range(5):
        train = np.array([k != fold for k in folds]); test = ~train
        plain[test] = basis[test] @ np.linalg.lstsq(basis[train], y[train], rcond=None)[0]
        mu = x[train].mean(axis=0); sd = np.maximum(x[train].std(axis=0), 1e-12)
        a = np.column_stack((basis[train], (x[train] - mu) / sd))
        b = np.column_stack((basis[test], (x[test] - mu) / sd))
        penalty = np.diag([0.] * 6 + [RIDGE] * 3)
        enhanced[test] = b @ np.linalg.solve(a.T @ a + penalty, a.T @ y[train])
    baseline = mse(y, plain); extra = mse(y, enhanced)
    return {'oracle_label_baseline_mse':baseline,'oracle_label_plus_geometry_mse':extra,
            'relative_mse_improvement':(baseline-extra)/baseline}
