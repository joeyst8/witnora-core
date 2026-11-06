"""Independent n=10, label-matched SAT family with exact source-only geometry test."""

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
from scripts.w038_cheap_geometry import cheap_features,FEATURE_NAMES


SEED = 390039
N = 10
SIZES = (38, 42, 46)
LABELS = ('SAT', 'UNSAT')
PER_CELL = 30
PERMUTATIONS = 499
RIDGE = 10.0
MAX_ATTEMPTS = 20000
CELLS = tuple((m, label) for m in SIZES for label in LABELS)


def clause_pool():
    clauses = [[sign * var for sign,var in zip(signs, variables)]
               for variables in itertools.combinations(range(1, N + 1), 3)
               for signs in itertools.product((-1,1), repeat=3)]
    assert len(clauses) == 960 and len({tuple(c) for c in clauses}) == 960
    return clauses


def clause_truth_masks(pool):
    """An exhaustive 2^10-bit oracle, independent of the DPLL search implementation."""
    masks = {}
    for clause in pool:
        bits = 0
        for assignment in range(1 << N):
            if any(bool(assignment & (1 << (abs(lit) - 1))) == (lit > 0) for lit in clause):
                bits |= 1 << assignment
        masks[tuple(clause)] = bits
    return masks


def exact_truth(clauses, masks):
    alive = (1 << (1 << N)) - 1
    for clause in clauses:
        alive &= masks[tuple(clause)]
        if not alive:
            return 'UNSAT'
    return 'SAT'


def source_cases():
    pool = clause_pool()
    masks = clause_truth_masks(pool)
    rng = random.Random(SEED)
    result = []
    attempts_by_size = {}
    for m in SIZES:
        accepted = {label:0 for label in LABELS}
        for attempt in range(1, MAX_ATTEMPTS + 1):
            clauses = rng.sample(pool, m)
            label = exact_truth(clauses, masks)
            if accepted[label] < PER_CELL:
                case_id = f'independent10-m{m}-{label.lower()}-{accepted[label]:02d}'
                result.append((case_id, m, label, attempt, clauses))
                accepted[label] += 1
            if all(accepted[k] == PER_CELL for k in LABELS):
                attempts_by_size[str(m)] = attempt
                break
        else:
            raise RuntimeError(f'W039 failed frozen quota for size {m}: {accepted}')
    if len(result) != 180:
        raise AssertionError('W039 sample count changed')
    return result, attempts_by_size


def folds_for_cells(cells):
    rng = random.Random(SEED+1)
    assigned = [-1]*len(cells)
    for cell in CELLS:
        indices = [i for i,x in enumerate(cells) if x == cell]
        if len(indices) != PER_CELL:
            raise ValueError(f'mismatched cell count {cell}: {len(indices)}')
        rng.shuffle(indices)
        for offset,idx in enumerate(indices):
            assigned[idx] = offset % 5
    return assigned


def evaluate_models(x, y, cells, folds, conditional=True):
    """Out-of-fold baseline and ridge-augmented predictions, no test normalization leakage."""
    groups = CELLS if conditional else SIZES
    membership = cells if conditional else [cell[0] for cell in cells]
    basis = np.array([[float(g == item) for item in groups] for g in membership])
    x = np.asarray(x,dtype=float)
    y = np.asarray(y,dtype=float)
    plain = np.empty(len(y)); enhanced = np.empty(len(y))
    for fold in range(5):
        train = np.array([v != fold for v in folds]); test = ~train
        plain[test] = basis[test] @ np.linalg.lstsq(basis[train], y[train], rcond=None)[0]
        mu = x[train].mean(axis=0); sigma = np.maximum(x[train].std(axis=0),1e-12)
        a = np.column_stack((basis[train],(x[train]-mu)/sigma))
        b = np.column_stack((basis[test],(x[test]-mu)/sigma))
        penalty = np.diag([0.]*len(groups) + [RIDGE]*len(FEATURE_NAMES))
        enhanced[test] = b @ np.linalg.solve(a.T@a + penalty,a.T@y[train])
    return plain,enhanced


def mse(y,pred):
    return float(np.mean((np.asarray(y)-pred)**2))


def run():
    generated, attempts = source_cases()
    warm = [[1,-2,3],[-1,2,-3],[1,2,3]]
    cheap_features(N,warm);solve(warm)
    rows = []
    for case_id,m,label,attempt,clauses in generated:
        start = time.perf_counter_ns()
        feat = cheap_features(N,clauses)
        elapsed = time.perf_counter_ns() - start
        start = time.perf_counter_ns()
        solution = solve(clauses)
        solver_elapsed = time.perf_counter_ns() - start
        if solution['verdict'] != label:
            raise RuntimeError(f'DPLL conflicts with independent exhaustive oracle for {case_id}')
        rows.append({'case_id':case_id,'clauses':clauses,'clause_count':m,'nvars':N,
                     'truth':label,'source_attempt':attempt,
                     'target_clause_scans':solution['clause_scans'],
                     'target_log_scans':math.log1p(solution['clause_scans']),
                     'features':feat,'feature_wall_ns':elapsed,'dpll_wall_ns':solver_elapsed})
    cells = [(r['clause_count'],r['truth']) for r in rows]
    folds = folds_for_cells(cells)
    x = np.array([[r['features'][k] for k in FEATURE_NAMES] for r in rows])
    y = np.array([r['target_log_scans'] for r in rows])
    baseline,predicted = evaluate_models(x,y,cells,folds,conditional=True)
    size_baseline,size_predicted = evaluate_models(x,y,cells,folds,conditional=False)
    base_loss = mse(y,baseline); geom_loss = mse(y,predicted)
    gain = (base_loss-geom_loss)/base_loss
    for i,row in enumerate(rows):
        row.update(fold=folds[i],conditional_baseline_pred=float(baseline[i]),
                   conditional_geometry_pred=float(predicted[i]),
                   size_baseline_pred=float(size_baseline[i]),
                   size_geometry_pred=float(size_predicted[i]))
    rng = random.Random(SEED+2)
    null = []
    for _ in range(PERMUTATIONS):
        shuffled = x.copy()
        for cell in CELLS:
            indices = [i for i,c in enumerate(cells) if c == cell]
            permutation = indices.copy();rng.shuffle(permutation)
            shuffled[indices] = x[permutation]
        _,prediction = evaluate_models(shuffled,y,cells,folds,conditional=True)
        null.append((base_loss-mse(y,prediction))/base_loss)
    report = {'study':'W-CROSSDOMAIN-039','phase':'frozen-n10-label-conditional',
              'protocol':'docs/W_CROSSDOMAIN_039_LABEL_CONDITIONAL_PROTOCOL.md',
              'nvars':N,'sizes':list(SIZES),'per_cell':PER_CELL,
              'generator_seed':SEED,'fold_seed':SEED+1,'permutation_seed':SEED+2,
              'ridge':RIDGE,'permutations':PERMUTATIONS,'feature_names':list(FEATURE_NAMES),
              'generation_attempts_by_size':attempts,
              'baseline_conditional_oof_mse':base_loss,
              'geometry_conditional_oof_mse':geom_loss,
              'relative_conditional_mse_improvement':gain,
              'baseline_conditional_oof_mae':float(np.mean(np.abs(y-baseline))),
              'geometry_conditional_oof_mae':float(np.mean(np.abs(y-predicted))),
              'size_only_baseline_oof_mse':mse(y,size_baseline),
              'size_plus_geometry_oof_mse':mse(y,size_predicted),
              'permutation_null_improvements':null,
              'within_cell_permutation_p':(1+sum(z>=gain for z in null))/(PERMUTATIONS+1),
              'median_feature_wall_ms':statistics.median(r['feature_wall_ns'] for r in rows)/1e6,
              'median_dpll_wall_ms':statistics.median(r['dpll_wall_ns'] for r in rows)/1e6,
              'by_cell':{f'{m}-{label}':{'baseline_mse':mse(y[[i for i,c in enumerate(cells) if c==(m,label)]],baseline[[i for i,c in enumerate(cells) if c==(m,label)]]),
                                         'geometry_mse':mse(y[[i for i,c in enumerate(cells) if c==(m,label)]],predicted[[i for i,c in enumerate(cells) if c==(m,label)]])}
                         for m,label in CELLS},
              'rows':rows,
              'scope':'Synthetic independent label-matched n=10 CNFs; label is unavailable oracle; no solver speedup or industrial-family generalization'}
    Path(os.environ['W039_REPORT_PATH']).write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print('W039_COMPLETE',len(rows),'conditional_improvement',round(gain,5),
          'p',report['within_cell_permutation_p'],'attempts',attempts,flush=True)


if __name__=='__main__':
    run()
