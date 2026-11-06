"""W035 same-host Python DPLL versus W034 LP exact-certificate cost audit."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import statistics
import time

from scripts.w034_weighted_walsh import search_integer_certificate
from scripts.w035_dpll_reference import solve


SOURCE_SHA = '261ca8144fc27799c6790012157c42986be37d0c0378f0dbdac7a98d8681a8c7'


def run():
    packed=Path('research/results/w034_weighted_small_raw.json.gz').read_bytes()
    raw=gzip.decompress(packed)
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:
        raise RuntimeError('original W034 source evidence has changed')
    source=json.loads(raw)
    results=[]
    for index,case in enumerate(source['rows']):
        records=[]
        for rep in range(3):
            arms=['dpll_reference','w034_integer_audited_lp']
            if (rep+index)%2: arms.reverse()
            for arm in arms:
                start=time.perf_counter_ns()
                if arm=='dpll_reference':
                    result=solve(case['clauses'])
                    verdict=result['verdict']
                    if verdict!=case['ground_truth']:
                        raise RuntimeError('DPLL disagreed with exhaustive source truth')
                    detail={k:result[k] for k in ('nodes','decisions','unit_assignments','clause_scans')}
                else:
                    result=search_integer_certificate(5,case['clauses'])
                    verdict=result['status']
                    if verdict!=case['weighted_status']:
                        raise RuntimeError('weighted certificate outcome differs from original frozen W034')
                    detail={'integer_bound':result['lower_bound_numerator'],
                            'active_weights':result['source_nonzero_weights']}
                elapsed=time.perf_counter_ns()-start
                records.append({'case_id':case['case_id'],'rep':rep,'arm':arm,
                                'verdict':verdict,'wall_ns':elapsed,**detail})
        byarm={arm:statistics.median(r['wall_ns'] for r in records if r['arm']==arm)
               for arm in ('dpll_reference','w034_integer_audited_lp')}
        results.append({'case_id':case['case_id'],'ground_truth':case['ground_truth'],
                        'clauses':len(case['clauses']), 'invocations':records,
                        'median_wall_ns':byarm,
                        'lp_over_dpll_ratio':byarm['w034_integer_audited_lp']/byarm['dpll_reference']})
    report={'study':'W-CROSSDOMAIN-035','phase':'small_same_host_algorithm_cost_audit',
            'protocol':'docs/W_CROSSDOMAIN_035_DPLL_COST_PROTOCOL.md',
            'source_study':'W-CROSSDOMAIN-034','source_sha256':SOURCE_SHA,
            'source_cases':len(results),'reps_per_case_per_arm':3,
            'total_invocations':1200,
            'median_case_ratio_lp_over_dpll':statistics.median(r['lp_over_dpll_ratio'] for r in results),
            'cases_lp_faster_than_dpll':sum(r['lp_over_dpll_ratio']<1 for r in results),
            'rows':results,
            'scope':'same-host Python algorithm-only cost, DPLL is reference not pinned Kissat; 5 variable toy sample'}
    Path(os.environ['W035_REPORT_PATH']).write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print('W035_COMPLETE',len(results),'formulae; median LP/DPLL ratio',
          round(report['median_case_ratio_lp_over_dpll'],2),flush=True)


if __name__=='__main__':
    run()
