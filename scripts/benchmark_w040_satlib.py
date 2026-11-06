"""Source-verified fixed SATLIB uf20-91 SAT-only conditional search-work study."""

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

from scripts.w038_cheap_geometry import cheap_features,FEATURE_NAMES
from scripts.w040_bounded_dpll import solve_bounded


PUBLISHER_URL='https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/RND3SAT/uf20-91.tar.gz'
N=20
M=91
SAMPLE=200
SCANS_LIMIT=2_000_000
RIDGE=10.0
CV_SEED=400040
NULL_SEED=400041
PERMUTATIONS=499


def parse_dimacs(content: bytes):
    """Strictly parse DIMACS; reject non-source repairs, extra clauses, and header drift."""
    lines=content.decode('ascii').splitlines()
    header=None
    literals=[]
    for line in lines:
        words=line.split()
        if not words or words[0]=='c':
            continue
        if words[0]=='%':
            # Historical DIMACS files may end with a '%' postamble marker.
            # The 91 source clauses must still be present before it.
            break
        if words[0]=='p':
            if header is not None or len(words)!=4 or words[1]!='cnf':
                raise ValueError('invalid duplicate or non-CNF header')
            header=(int(words[2]),int(words[3]))
            continue
        if header is None:
            raise ValueError('clause before DIMACS header')
        literals.extend(int(tok) for tok in words)
    if header!=(N,M):
        raise ValueError(f'unexpected SATLIB header {header}')
    clauses=[]
    clause=[]
    for lit in literals:
        if lit==0:
            if len(clause)!=3 or len({abs(v) for v in clause})!=3:
                raise ValueError('expected 3 distinct variables per clause')
            clauses.append(clause)
            clause=[]
        else:
            if abs(lit)>N:
                raise ValueError('literal exceeds source variable count')
            clause.append(lit)
    if clause or len(clauses)!=M:
        raise ValueError('unterminated clause or changed clause count')
    return clauses


def source_cases(archive: bytes):
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tf:
        members=sorted((m for m in tf.getmembers() if m.isfile() and m.name.lower().endswith('.cnf')),
                       key=lambda m:m.name)
        names=[m.name for m in members]
        if len(names)!=len(set(names)):
            raise ValueError('duplicate official archive member names')
        if len(members)<SAMPLE:
            raise ValueError('too few source instances in official archive')
        selected=[]
        for member in members[:SAMPLE]:
            data=tf.extractfile(member).read()
            selected.append({'source_member':member.name,'source_sha256':hashlib.sha256(data).hexdigest(),
                             'clauses':parse_dimacs(data)})
        return selected,len(members)


def fixed_folds(n):
    indices=list(range(n));random.Random(CV_SEED).shuffle(indices)
    folds=[-1]*n
    for position,idx in enumerate(indices):
        folds[idx]=position%5
    return folds


def out_of_fold(feature_matrix,y,folds):
    x=np.asarray(feature_matrix,dtype=float); y=np.asarray(y,dtype=float)
    base=np.empty(len(y));geometry=np.empty(len(y))
    for fold in range(5):
        train=np.array([a!=fold for a in folds]);test=~train
        mu_y=y[train].mean()
        base[test]=mu_y
        mu=x[train].mean(axis=0);sd=np.maximum(x[train].std(axis=0),1e-12)
        a=np.column_stack((np.ones(sum(train)),(x[train]-mu)/sd))
        b=np.column_stack((np.ones(sum(test)),(x[test]-mu)/sd))
        penalty=np.diag([0.]+[RIDGE]*len(FEATURE_NAMES))
        beta=np.linalg.solve(a.T@a+penalty,a.T@y[train])
        geometry[test]=b@beta
    return base,geometry


def mse(y,pred):
    return float(np.mean(np.square(np.asarray(y)-pred)))


def run():
    blob=Path(os.environ['W040_ARCHIVE_PATH']).read_bytes()
    publisher_sha=hashlib.sha256(blob).hexdigest()
    sources,total_members=source_cases(blob)
    cheap_features(N,sources[0]['clauses'])
    solve_bounded(sources[0]['clauses'],max_clause_scans=10)
    rows=[]
    for source in sources:
        start=time.perf_counter_ns()
        feat=cheap_features(N,source['clauses'])
        feature_ns=time.perf_counter_ns()-start
        start=time.perf_counter_ns()
        result=solve_bounded(source['clauses'],max_clause_scans=SCANS_LIMIT)
        dpll_ns=time.perf_counter_ns()-start
        if result['verdict']=='UNSAT':
            raise RuntimeError('reference UNSAT disagrees with publisher SAT label')
        if result['verdict']=='SAT':
            answer=result['assignment']
            if not all(any(answer.get(abs(lit))==(lit>0) for lit in clause)
                       for clause in source['clauses']):
                raise RuntimeError('reference solver assignment fails source clauses')
        rows.append({**source, 'nvars':N,'clause_count':M,'publisher_label':'SAT',
                     'verdict':result['verdict'],'clause_scans':result['clause_scans'],
                     'target_log_scans':(math.log1p(result['clause_scans']) if result['verdict']=='SAT' else None),
                     'features':feat,'feature_wall_ns':feature_ns,'dpll_wall_ns':dpll_ns})
    censored=sum(r['verdict']=='CENSORED' for r in rows)
    report={'study':'W-CROSSDOMAIN-040','phase':'frozen-published-satlib-single-family',
            'source':PUBLISHER_URL,'publisher_archive_sha256':publisher_sha,
            'publisher_member_count':total_members,'sample_size':len(rows),
            'scan_cap':SCANS_LIMIT,'censored_count':censored,
            'feature_names':list(FEATURE_NAMES),'ridge':RIDGE,'cv_seed':CV_SEED,
            'null_seed':NULL_SEED,'permutations_planned':PERMUTATIONS,
            'median_feature_wall_ms':statistics.median(r['feature_wall_ns'] for r in rows)/1e6,
            'median_dpll_wall_ms':statistics.median(r['dpll_wall_ns'] for r in rows)/1e6,
            'rows':rows,'scope':'SATLIB official published constant n=20 m=91 SAT only; one random-3-SAT family'}
    if censored==0:
        folds=fixed_folds(len(rows))
        y=np.array([r['target_log_scans'] for r in rows])
        x=np.array([[r['features'][k] for k in FEATURE_NAMES] for r in rows])
        baseline,predicted=out_of_fold(x,y,folds)
        base_loss=mse(y,baseline);geom_loss=mse(y,predicted)
        improvement=(base_loss-geom_loss)/base_loss
        for i,row in enumerate(rows):
            row.update(fold=folds[i],baseline_pred=float(baseline[i]),geometry_pred=float(predicted[i]))
        rng=random.Random(NULL_SEED)
        null=[]
        for _ in range(PERMUTATIONS):
            indices=list(range(len(rows)));rng.shuffle(indices)
            permuted=x[indices]
            _,prediction=out_of_fold(permuted,y,folds)
            null.append((base_loss-mse(y,prediction))/base_loss)
        report.update(inference_status='COMPLETE',baseline_oof_mse=base_loss,
                      geometry_oof_mse=geom_loss,relative_oof_mse_improvement=improvement,
                      baseline_oof_mae=float(np.mean(np.abs(y-baseline))),
                      geometry_oof_mae=float(np.mean(np.abs(y-predicted))),
                      null_improvements=null,
                      permutation_p=(1+sum(z>=improvement for z in null))/(PERMUTATIONS+1),
                      by_fold={str(k):{'baseline_mse':mse(y[np.array(folds)==k],baseline[np.array(folds)==k]),
                                       'geometry_mse':mse(y[np.array(folds)==k],predicted[np.array(folds)==k])}
                               for k in range(5)})
    else:
        report.update(inference_status='INCONCLUSIVE_CENSORED',
                      note='Preregistered protocol forbids fitting regressions after target-dependent censoring')
    Path(os.environ['W040_REPORT_PATH']).write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print('W040_COMPLETE',len(rows),'censored',censored,'publisher_sha256',publisher_sha,
          'status',report['inference_status'],
          'improvement',round(report.get('relative_oof_mse_improvement',float('nan')),5),
          'p',report.get('permutation_p','not tested'),flush=True)


if __name__=='__main__':
    run()
