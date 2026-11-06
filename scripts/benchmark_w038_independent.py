"""Frozen W038 independent uniform-random eight-variable 3-CNF replication."""

from __future__ import annotations

import itertools
import json
import math
import os
from pathlib import Path
import random
import statistics
import time

import numpy as np

from scripts.w035_dpll_reference import solve
from scripts.w037_geometry_features import FEATURE_NAMES as ALL_NAMES, features
from scripts.w038_cheap_geometry import FEATURE_NAMES as CHEAP_NAMES, cheap_features


SEED = 380038
SIZES = (24, 32, 40, 48, 56)
N_VARS = 8
CASES_PER_SIZE = 40
PERMUTATIONS = 200
RIDGE = 10.0


def source_cases():
    pool = [[sign * var for sign, var in zip(signs, variables)]
            for variables in itertools.combinations(range(1, N_VARS + 1), 3)
            for signs in itertools.product((-1, 1), repeat=3)]
    assert len(pool) == 448 and len({tuple(c) for c in pool}) == 448
    rng = random.Random(SEED)
    return [(f'random8-m{size}-{i:02d}', size, rng.sample(pool, size))
            for size in SIZES for i in range(CASES_PER_SIZE)]


def size_folds(sizes):
    rng = random.Random(SEED + 1)
    folds = [-1] * len(sizes)
    for size in SIZES:
        ids = [i for i, val in enumerate(sizes) if val == size]
        if len(ids) != CASES_PER_SIZE:
            raise ValueError('unexpected size stratum')
        rng.shuffle(ids)
        for offset, index in enumerate(ids):
            folds[index] = offset % 5
    return folds


def regress(feature_matrix, target, sizes, folds):
    basis = np.array([[float(m == level) for level in SIZES] for m in sizes])
    x = np.asarray(feature_matrix, dtype=float)
    y = np.asarray(target, dtype=float)
    baseline = np.empty(len(y))
    augmented = np.empty(len(y))
    for fold in range(5):
        train = np.array([k != fold for k in folds]); test = ~train
        baseline[test] = basis[test] @ np.linalg.lstsq(basis[train], y[train], rcond=None)[0]
        mu = x[train].mean(axis=0); sd = np.maximum(x[train].std(axis=0), 1e-12)
        train_matrix = np.column_stack((basis[train], (x[train] - mu) / sd))
        test_matrix = np.column_stack((basis[test], (x[test] - mu) / sd))
        penalty = np.diag([0.] * len(SIZES) + [RIDGE] * x.shape[1])
        beta = np.linalg.solve(train_matrix.T @ train_matrix + penalty, train_matrix.T @ y[train])
        augmented[test] = test_matrix @ beta
    return baseline, augmented


def mse(y, pred):
    return float(np.mean(np.square(np.asarray(y) - pred)))


def run():
    sample = source_cases()
    assert len(sample) == 200
    # Warm the Python/Numpy implementations without touching the frozen sample.
    warm = [[1, -2, 3], [1, 2, -3], [-1, 2, 3]]
    cheap_features(N_VARS, warm); features(N_VARS, warm); solve(warm)
    rows = []
    for case_id, size, clauses in sample:
        start = time.perf_counter_ns()
        cheap = cheap_features(N_VARS, clauses)
        cheap_ns = time.perf_counter_ns() - start
        start = time.perf_counter_ns()
        full = features(N_VARS, clauses)
        full_ns = time.perf_counter_ns() - start
        for name in CHEAP_NAMES:
            if not math.isclose(cheap[name], full[name], abs_tol=1e-11):
                raise AssertionError('cheap analytic feature differs from full W037 feature')
        start = time.perf_counter_ns()
        work = solve(clauses)
        dpll_ns = time.perf_counter_ns() - start
        rows.append({'case_id':case_id, 'clauses':clauses, 'nvars':N_VARS,
                     'clause_count':size, 'verdict':work['verdict'],
                     'target_clause_scans':work['clause_scans'],
                     'target_log_scans':math.log1p(work['clause_scans']),
                     'cheap_features':cheap, 'all_features':full,
                     'cheap_wall_ns':cheap_ns, 'all_wall_ns':full_ns,
                     'dpll_wall_ns':dpll_ns})
    sizes = [row['clause_count'] for row in rows]
    folds = size_folds(sizes)
    y = np.array([row['target_log_scans'] for row in rows])
    cheap_x = np.array([[row['cheap_features'][key] for key in CHEAP_NAMES] for row in rows])
    all_x = np.array([[row['all_features'][key] for key in ALL_NAMES] for row in rows])
    plain, cheap_pred = regress(cheap_x, y, sizes, folds)
    _, all_pred = regress(all_x, y, sizes, folds)
    base_loss = mse(y, plain); cheap_loss = mse(y, cheap_pred); all_loss = mse(y, all_pred)
    improvement = (base_loss - cheap_loss) / base_loss
    for i, row in enumerate(rows):
        row.update(fold=folds[i], baseline_pred=float(plain[i]),
                   cheap_pred=float(cheap_pred[i]), all_pred=float(all_pred[i]))
    rng = random.Random(SEED + 2)
    null = []
    for _ in range(PERMUTATIONS):
        permuted = cheap_x.copy()
        for size in SIZES:
            ids = [i for i, m in enumerate(sizes) if m == size]
            shuffled = ids.copy(); rng.shuffle(shuffled)
            permuted[ids] = cheap_x[shuffled]
        _, pred = regress(permuted, y, sizes, folds)
        null.append((base_loss - mse(y, pred)) / base_loss)
    median_cheap = statistics.median(row['cheap_wall_ns'] for row in rows)/1e6
    median_dpll = statistics.median(row['dpll_wall_ns'] for row in rows)/1e6
    report = {'study':'W-CROSSDOMAIN-038', 'phase':'frozen-independent-8var-replication',
              'protocol':'docs/W_CROSSDOMAIN_038_INDEPENDENT_CHEAP_GEOMETRY_PROTOCOL.md',
              'generator_seed':SEED,'sizes':SIZES,'nvars':N_VARS,'cases_per_size':CASES_PER_SIZE,
              'ridge':RIDGE,'permutations':PERMUTATIONS,
              'cheap_feature_names':CHEAP_NAMES,'all_feature_names':ALL_NAMES,
              'baseline_oof_mse':base_loss,'cheap_oof_mse':cheap_loss,
              'all_oof_mse':all_loss,'cheap_relative_improvement':improvement,
              'baseline_oof_mae':float(np.mean(np.abs(y-plain))),
              'cheap_oof_mae':float(np.mean(np.abs(y-cheap_pred))),
              'permutation_null_improvements':null,
              'permutation_p':(1+sum(value>=improvement for value in null))/(PERMUTATIONS+1),
              'median_cheap_feature_ms':median_cheap,
              'median_all_feature_ms':statistics.median(r['all_wall_ns'] for r in rows)/1e6,
              'median_dpll_ms':median_dpll,
              'cheap_feature_to_dpll_median_ratio':median_cheap/median_dpll,
              'by_clause_count':{str(size):{
                  'sat':sum(r['verdict']=='SAT' for r in rows if r['clause_count']==size),
                  'unsat':sum(r['verdict']=='UNSAT' for r in rows if r['clause_count']==size),
                  'baseline_mse':mse(y[[i for i,s in enumerate(sizes) if s==size]],
                                     plain[[i for i,s in enumerate(sizes) if s==size]]),
                  'cheap_mse':mse(y[[i for i,s in enumerate(sizes) if s==size]],
                                   cheap_pred[[i for i,s in enumerate(sizes) if s==size]])
              } for size in SIZES},'rows':rows,
              'scope':'Independent synthetic uniform-random n=8 source. No external SAT family or solver speedup claim.'}
    Path(os.environ['W038_REPORT_PATH']).write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print('W038_COMPLETE', len(rows), 'cheap-improvement',round(improvement,4),
          'p',round(report['permutation_p'],4), 'median-feature/dpll',
          round(report['cheap_feature_to_dpll_median_ratio'],3),flush=True)


if __name__ == '__main__':
    run()
