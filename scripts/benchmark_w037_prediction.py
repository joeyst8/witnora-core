"""W037 held-out size-conditioned regression and within-size permutation test."""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics
import time

import numpy as np

from scripts.w035_dpll_reference import solve
from scripts.w037_geometry_features import FEATURE_NAMES, features


SEED=370037
SIZES=(12,16,20,24,32)
RIDGE=10.0
PERMUTATIONS=200
BOOTSTRAPS=2000
W034_SHA='261ca8144fc27799c6790012157c42986be37d0c0378f0dbdac7a98d8681a8c7'
W035_SHA='4451e2c8621c85aeca47e1e330cb29023acfe0920b3ed1a249a67d808c280e1a'


def load_frozen(path, expected):
    raw=gzip.decompress(Path(path).read_bytes())
    if hashlib.sha256(raw).hexdigest()!=expected:
        raise RuntimeError('source-frozen raw archive hash mismatch')
    return json.loads(raw)


def fixed_folds(sizes):
    rng=random.Random(SEED)
    output=[-1]*len(sizes)
    for m in SIZES:
        indices=[i for i,n in enumerate(sizes) if n==m]
        if len(indices)!=40:
            raise ValueError('frozen stratum no longer contains exactly 40 cases')
        rng.shuffle(indices)
        for position,i in enumerate(indices):output[i]=position%5
    return output


def predict(feature_matrix,target,sizes,folds):
    base=np.array([[float(m==level) for level in SIZES] for m in sizes])
    x=np.asarray(feature_matrix,dtype=float)
    y=np.asarray(target,dtype=float)
    baseline=np.empty(len(y));geometry=np.empty(len(y))
    for fold in range(5):
        train=np.array([a!=fold for a in folds]);test=~train
        baseline[test]=base[test]@np.linalg.lstsq(base[train],y[train],rcond=None)[0]
        mu=x[train].mean(axis=0)
        sd=np.maximum(x[train].std(axis=0),1e-12)
        train_matrix=np.column_stack((base[train],(x[train]-mu)/sd))
        test_matrix=np.column_stack((base[test],(x[test]-mu)/sd))
        penalty=np.diag([0.0]*5+[RIDGE]*len(FEATURE_NAMES))
        beta=np.linalg.solve(train_matrix.T@train_matrix+penalty,train_matrix.T@y[train])
        geometry[test]=test_matrix@beta
    return baseline,geometry


def mse(y,pred):
    return float(np.mean((np.asarray(y)-pred)**2))


def run():
    original=load_frozen('research/results/w034_weighted_small_raw.json.gz',W034_SHA)
    costs=load_frozen('research/results/w035_cost_raw.json.gz',W035_SHA)
    if len(original['rows'])!=200 or len(costs['rows'])!=200:
        raise RuntimeError('200-case evidence requirement failed')
    rows=[]
    for source,old in zip(original['rows'],costs['rows']):
        if source['case_id']!=old['case_id']:raise RuntimeError('source ID mismatch')
        started=time.perf_counter_ns()
        feat=features(5,source['clauses'])
        elapsed=time.perf_counter_ns()-started
        dpll=solve(source['clauses'])
        references=[r for r in old['invocations'] if r['arm']=='dpll_reference']
        if dpll['verdict']!=source['ground_truth'] or any(
            row['clause_scans']!=dpll['clause_scans'] for row in references):
            raise RuntimeError('independently recomputed DPLL target differs')
        rows.append({'case_id':source['case_id'],'clauses':len(source['clauses']),
                     'ground_truth':source['ground_truth'],
                     'target_clause_scans':dpll['clause_scans'],
                     'target_log_scans':math.log1p(dpll['clause_scans']),
                     'feature_wall_ns':elapsed,
                     'original_dpll_median_wall_ns':old['median_wall_ns']['dpll_reference'],
                     'features':feat})
    sizes=[r['clauses'] for r in rows]
    folds=fixed_folds(sizes)
    y=np.asarray([r['target_log_scans'] for r in rows])
    x=np.asarray([[r['features'][name] for name in FEATURE_NAMES] for r in rows])
    plain,predicted=predict(x,y,sizes,folds)
    base_loss=mse(y,plain)
    new_loss=mse(y,predicted)
    improvement=(base_loss-new_loss)/base_loss
    for i,row in enumerate(rows):
        row.update(heldout_fold=folds[i],baseline_heldout_prediction=float(plain[i]),
                   geometry_heldout_prediction=float(predicted[i]))

    rng=random.Random(SEED+1)
    null=[]
    for _ in range(PERMUTATIONS):
        permuted=x.copy()
        for size in SIZES:
            ids=[i for i,n in enumerate(sizes) if n==size]
            shuffled=ids.copy();rng.shuffle(shuffled)
            permuted[ids]=x[shuffled]
        _,null_pred=predict(permuted,y,sizes,folds)
        null.append((base_loss-mse(y,null_pred))/base_loss)
    p_value=(1+sum(value>=improvement for value in null))/(PERMUTATIONS+1)

    differences=np.square(y-plain)-np.square(y-predicted)
    rng=random.Random(SEED+2)
    groups={size:[i for i,n in enumerate(sizes) if n==size] for size in SIZES}
    bootstrap=[]
    for _ in range(BOOTSTRAPS):
        sampled=[rng.choice(groups[size]) for size in SIZES for _ in range(40)]
        bootstrap.append(float(np.mean(differences[sampled])))
    bootstrap.sort()
    by_size={}
    for size in SIZES:
        indices=[i for i,n in enumerate(sizes) if n==size]
        by_size[str(size)]={'baseline_mse':mse(y[indices],plain[indices]),
                            'geometry_mse':mse(y[indices],predicted[indices])}
    report={'study':'W-CROSSDOMAIN-037','phase':'frozen_size_conditioned_prediction',
            'protocol':'docs/W_CROSSDOMAIN_037_CONDITIONAL_GEOMETRY_PROTOCOL.md',
            'source_w034_sha256':W034_SHA,'source_w035_sha256':W035_SHA,
            'case_count':len(rows),'feature_names':list(FEATURE_NAMES),
            'seed':SEED,'ridge_penalty':RIDGE,'cross_validation_folds':5,
            'permutations':PERMUTATIONS,'bootstraps':BOOTSTRAPS,
            'baseline_heldout_mse':base_loss,'geometry_heldout_mse':new_loss,
            'relative_mse_improvement':improvement,
            'baseline_heldout_mae':float(np.mean(np.abs(y-plain))),
            'geometry_heldout_mae':float(np.mean(np.abs(y-predicted))),
            'within_size_permutation_p':p_value,'permutation_null_improvements':null,
            'paired_oof_squared_error_difference':float(np.mean(differences)),
            'paired_error_difference_bootstrap_ci_95':[bootstrap[49],bootstrap[1949]],
            'by_clause_count':by_size,
            'median_feature_wall_ms':statistics.median(r['feature_wall_ns'] for r in rows)/1e6,
            'median_original_dpll_wall_ms':statistics.median(r['original_dpll_median_wall_ns'] for r in rows)/1e6,
            'rows':rows,
            'scope':'200 synthetic n=5 CNFs; held-out size-conditioned prediction only; no solver speedup or external generalization claim'}
    Path(os.environ['W037_REPORT_PATH']).write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print('W037_COMPLETE',len(rows),'heldout_improvement',round(improvement,4),
          'permutation_p',round(p_value,4),flush=True)


if __name__=='__main__':
    run()
