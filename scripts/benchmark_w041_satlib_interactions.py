"""Frozen W041 interaction-only trial on independent publisher ranks 200:400."""

from __future__ import annotations

import hashlib
import io
import json
import math
import os
from pathlib import Path
import random
import statistics
import tarfile
import time

import numpy as np

from scripts.benchmark_w040_satlib import parse_dimacs,out_of_fold,mse,SCANS_LIMIT,PUBLISHER_URL
from scripts.w040_bounded_dpll import solve_bounded
from scripts.w041_interaction_features import FEATURE_NAMES,interaction_features


EXPECTED_ARCHIVE_SHA='be2835295e8500bb28f0314eba70bd0deaff1250b187260f7b6d0772bdf111a5'
START=200
COUNT=200
CV_SEED=410041
NULL_SEED=410042
PERMUTATIONS=499
RIDGE=10.0


def source_cases(archive):
    if hashlib.sha256(archive).hexdigest()!=EXPECTED_ARCHIVE_SHA:
        raise ValueError('official publisher archive SHA changed')
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tf:
        members=sorted((m for m in tf.getmembers() if m.isfile() and m.name.lower().endswith('.cnf')),
                       key=lambda m:m.name)
        names=[m.name for m in members]
        if len(names)!=len(set(names)) or len(members)<START+COUNT:
            raise ValueError('unexpected official SATLIB member count or names')
        chosen=[]
        for index,member in enumerate(members[START:START+COUNT],START):
            source=tf.extractfile(member).read()
            chosen.append({'source_rank':index,'source_member':member.name,
                           'source_sha256':hashlib.sha256(source).hexdigest(),
                           'clauses':parse_dimacs(source)})
    return chosen,len(members)


def fixed_folds(n):
    ids=list(range(n));random.Random(CV_SEED).shuffle(ids)
    folds=[-1]*n
    for offset,idx in enumerate(ids):
        folds[idx]=offset%5
    return folds


def run():
    archive=Path(os.environ['W041_ARCHIVE_PATH']).read_bytes()
    sources,total=source_cases(archive)
    interaction_features(20,sources[0]['clauses'])
    solve_bounded(sources[0]['clauses'],max_clause_scans=10)
    rows=[]
    for source in sources:
        start=time.perf_counter_ns()
        feat=interaction_features(20,source['clauses'])
        feature_ns=time.perf_counter_ns()-start
        start=time.perf_counter_ns()
        outcome=solve_bounded(source['clauses'],max_clause_scans=SCANS_LIMIT)
        dpll_ns=time.perf_counter_ns()-start
        if outcome['verdict']=='UNSAT':
            raise RuntimeError('reference UNSAT contradicts SATLIB published SAT label')
        if outcome['verdict']=='SAT':
            if not all(any(outcome['assignment'].get(abs(lit))==(lit>0) for lit in clause)
                       for clause in source['clauses']):
                raise RuntimeError('source SAT witness failed')
        rows.append({**source,'nvars':20,'clause_count':91,'publisher_label':'SAT',
                     'verdict':outcome['verdict'],'clause_scans':outcome['clause_scans'],
                     'target_log_scans':(math.log1p(outcome['clause_scans']) if outcome['verdict']=='SAT' else None),
                     'features':feat,'feature_wall_ns':feature_ns,'dpll_wall_ns':dpll_ns})
    censored=sum(r['verdict']=='CENSORED' for r in rows)
    report={'study':'W-CROSSDOMAIN-041','phase':'frozen-published-interaction-holdout',
            'source':PUBLISHER_URL,'publisher_archive_sha256':EXPECTED_ARCHIVE_SHA,
            'publisher_members':total,'source_rank_start':START,'source_rank_end_exclusive':START+COUNT,
            'sample_size':len(rows),'scan_cap':SCANS_LIMIT,'censored_count':censored,
            'feature_names':list(FEATURE_NAMES),'ridge':RIDGE,
            'cv_seed':CV_SEED,'null_seed':NULL_SEED,'permutations_planned':PERMUTATIONS,
            'median_feature_wall_ms':statistics.median(r['feature_wall_ns'] for r in rows)/1e6,
            'median_dpll_wall_ms':statistics.median(r['dpll_wall_ns'] for r in rows)/1e6,
            'rows':rows,'scope':'Untouched SATLIB ranks 200:400, 20-variable 91-clause SAT-only; new predeclared signed-interaction features'}
    if censored==0:
        folds=fixed_folds(len(rows))
        y=np.array([r['target_log_scans'] for r in rows])
        x=np.array([[r['features'][key] for key in FEATURE_NAMES] for r in rows])
        baseline,predicted=out_of_fold(x,y,folds)
        base=mse(y,baseline);geometry=mse(y,predicted)
        observed=(base-geometry)/base
        for i,row in enumerate(rows):
            row.update(fold=folds[i],baseline_pred=float(baseline[i]),
                       geometry_pred=float(predicted[i]))
        rng=random.Random(NULL_SEED);null=[]
        for _ in range(PERMUTATIONS):
            shuffled=list(range(len(rows)));rng.shuffle(shuffled)
            _,prediction=out_of_fold(x[shuffled],y,folds)
            null.append((base-mse(y,prediction))/base)
        report.update(inference_status='COMPLETE',baseline_oof_mse=base,
                      geometry_oof_mse=geometry,relative_oof_mse_improvement=observed,
                      baseline_oof_mae=float(np.mean(np.abs(y-baseline))),
                      geometry_oof_mae=float(np.mean(np.abs(y-predicted))),
                      null_improvements=null,
                      permutation_p=(1+sum(v>=observed for v in null))/(PERMUTATIONS+1))
    else:
        report.update(inference_status='INCONCLUSIVE_CENSORED',
                      note='No post-selection regression permitted after a capped DPLL target')
    Path(os.environ['W041_REPORT_PATH']).write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print('W041_COMPLETE',len(rows),'censored',censored,'status',report['inference_status'],
          'improvement',round(report.get('relative_oof_mse_improvement',float('nan')),5),
          'p',report.get('permutation_p','n/a'),flush=True)


if __name__=='__main__':
    run()
