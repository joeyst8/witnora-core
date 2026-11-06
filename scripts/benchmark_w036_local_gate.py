"""W036-A costed prefix-local proof study on 8 external + 8 frozen controls.

This deliberately does *not* benchmark complete solver pipelines. It screens
proof availability and local search overhead before a larger W036-B study.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import time

from scripts.benchmark_w032_external import materialize
from scripts.w030_smoke_cases import cases,manifest as synthetic_manifest,source_bytes
from scripts.w032_external_cases import cases_metadata,manifest as external_manifest
from scripts.w033_walsh_bound import walsh_bound
from scripts.w034_weighted_walsh import search_integer_certificate,audit_integer_weights
from scripts.w036_local_gate import read_prefix,neighborhoods,unit_propagation_contradiction,bounded_dpll


PERCENTS=(1,2,5)
CAPS=(16,32,64)
ANCHORS=3


def source_cases():
    source=json.loads(Path('research/results/w030_smoke_case_manifest.json').read_text())
    if source!=synthetic_manifest():
        raise RuntimeError('original W030 synthetic controls altered')
    frozen_by_id={entry['case_id']:entry for entry in source['entries']}
    result=[]
    for case in cases():
        raw=source_bytes(case['variables'],case['clauses'])
        frozen=frozen_by_id[case['case_id']]
        if hashlib.sha256(raw).hexdigest()!=frozen['cnf_sha256']:
            raise RuntimeError('synthetic source hash mismatch')
        result.append(({'case_id':case['case_id'],'stratum':'frozen_synthetic_control',
                        'expected':case['expected'],'declared_clauses':len(case['clauses']),
                        'sha256':frozen['cnf_sha256']},raw))
    external=json.loads(Path('research/results/w032_case_manifest.json').read_text())
    if external!=external_manifest():
        raise RuntimeError('published-source manifest altered')
    for entry in cases_metadata():
        if entry['stratum']!='official_external_vlsat2':continue
        raw=materialize(entry)  # independently SHA256-checked publisher bytes
        result.append(({'case_id':entry['case_id'],'stratum':'official_external_vlsat2',
                        'expected':entry['expected'],'declared_clauses':entry['clauses'],
                        'sha256':entry['cnf_sha256']},raw))
    if len(result)!=16:
        raise RuntimeError('frozen 16-case scope changed')
    return result


def run():
    results=[]
    with tempfile.TemporaryDirectory(prefix='witnora-w036-') as dirname:
        for entry,source in source_cases():
            name=entry['case_id']
            path=Path(dirname)/(name+'.cnf')
            path.write_bytes(source)
            per_budget=[]
            for percent in PERCENTS:
                prefix_limit=math.ceil(entry['declared_clauses']*percent/100)
                started=time.perf_counter_ns()
                prefix=read_prefix(path,prefix_limit)
                prefix_ns=time.perf_counter_ns()-started
                if prefix['read_clauses']!=prefix_limit:
                    raise RuntimeError('prefix scanner read a different budget')
                cap_results=[]
                for cap in CAPS:
                    select_start=time.perf_counter_ns()
                    candidates=neighborhoods(prefix,max_anchors=ANCHORS,max_clauses=cap)
                    select_ns=time.perf_counter_ns()-select_start
                    candidate_results=[]
                    for candidate in candidates:
                        original=candidate['clauses']
                        short=[clause for clause in original if len(clause)<=3]
                        start=time.perf_counter_ns()
                        root_unit=unit_propagation_contradiction(original)
                        unit_ns=time.perf_counter_ns()-start
                        start=time.perf_counter_ns()
                        dpll=bounded_dpll(original,max_nodes=128,max_clause_scans=16000)
                        dpll_ns=time.perf_counter_ns()-start
                        start=time.perf_counter_ns()
                        global_fourier=walsh_bound(prefix['variables'],short)
                        global_ns=time.perf_counter_ns()-start
                        start=time.perf_counter_ns()
                        weighted=search_integer_certificate(prefix['variables'],short,
                                                            max_clauses=64) if short else None
                        lp_ns=time.perf_counter_ns()-start
                        certificate=weighted is not None and weighted['status']=='UNSAT_CERTIFIED'
                        if certificate:
                            independent=audit_integer_weights(short,prefix['variables'],weighted['weights'])
                            if independent['status']!='UNSAT_CERTIFIED':
                                raise RuntimeError('non-audited weighted certificate')
                        if entry['expected']=='SAT' and (root_unit or dpll['status']=='UNSAT_CERTIFIED' or
                            global_fourier['status']=='UNSAT_CERTIFIED' or certificate):
                            raise RuntimeError('false original-source UNSAT proof on known SAT')
                        candidate_results.append({
                            'anchor':candidate['anchor'],
                            'source_clause_indices':candidate['source_indices'],
                            'selected_clauses':len(original),'short_clauses':len(short),
                            'source_selected_sha256':hashlib.sha256(source_bytes(prefix['variables'],original)).hexdigest(),
                            'root_unit_unsat':root_unit,'unit_wall_ns':unit_ns,
                            'dpll_status':dpll['status'],'dpll_nodes':dpll['nodes'],
                            'dpll_clause_scans':dpll['clause_scans'],'dpll_wall_ns':dpll_ns,
                            'unweighted_status':global_fourier['status'],'fourier_wall_ns':global_ns,
                            'weighted_status':weighted['status'] if weighted else 'NO_CERTIFICATE',
                            'weighted_bound_numerator':weighted.get('lower_bound_numerator') if weighted else None,
                            'weighted_nonzero_weights':weighted.get('source_nonzero_weights') if weighted else 0,
                            'weighted_wall_ns':lp_ns})
                    cap_results.append({'cap':cap,'selection_wall_ns':select_ns,
                                        'candidates':candidate_results})
                per_budget.append({'percent':percent,'limit':prefix_limit,
                                   'prefix_wall_ns':prefix_ns,
                                   'read_bytes':prefix['read_bytes'],
                                   'read_clauses':prefix['read_clauses'],
                                   'caps':cap_results})
            results.append({**entry,'budget_results':per_budget})
            print('W036_A',name,entry['expected'],'complete',flush=True)
    report={'study':'W-CROSSDOMAIN-036','phase':'A_prefix_local_exploration',
            'protocol':'docs/W_CROSSDOMAIN_036_LOCAL_CERTIFICATE_PROTOCOL.md',
            'cases':16,'external_cases':8,'budgets_percent':list(PERCENTS),
            'neighborhood_caps':list(CAPS),'max_anchors':ANCHORS,
            'source_cases':results,
            'scope':'prefix-local source proof coverage and Python algorithm costs only; no full solver pipeline or external advantage claim'}
    Path(os.environ['W036_REPORT_PATH']).write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print('W036_A_COMPLETE',len(results),'case studies',flush=True)


if __name__=='__main__':
    run()
