"""W042: frozen SATLIB 50-variable SAT/UNSAT branching study, no tuning.

Each result retains the original source and runs the same native Rust core
under four predetermined policies. See the preregistered protocol for claims.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import statistics
import subprocess
import tarfile

PUBLISHER = 'https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/RND3SAT/'
ARCHIVES = {
    'SAT': ('uf50-218.tar.gz', 'a40862e52dfdce78620b037254579a02dbda8182d2879433658a4c15cb00327c'),
    'UNSAT': ('uuf50-218.tar.gz', '24cc9f492673e0f975fecc56b3a4d8ac21c385cc46205d83b7491a787f43e13d'),
}
N, M, SAMPLE, CAP, REPEATS = 50, 218, 32, 2_000_000, 3
POLICIES = ('degree', 'moms', 'probe', 'gated_probe')


def parse_dimacs(raw: bytes):
    header = None
    flat = []
    postamble = False
    for line in raw.decode('ascii').splitlines():
        parts = line.split()
        if not parts or parts[0] == 'c':
            continue
        if parts[0] == '%':
            postamble = True
            continue
        if postamble:
            if parts[0] not in ('0',):
                raise ValueError('content after publisher DIMACS postamble')
            continue
        if parts[0] == 'p':
            if header is not None or len(parts) != 4 or parts[1] != 'cnf':
                raise ValueError('invalid or duplicate DIMACS header')
            header = (int(parts[2]), int(parts[3]))
        else:
            if header is None:
                raise ValueError('clauses before header')
            flat.extend(int(v) for v in parts)
    if header != (N, M):
        raise ValueError(f'unexpected original source header: {header}')
    clauses, row = [], []
    for lit in flat:
        if lit == 0:
            if len(row) != 3 or len({abs(v) for v in row}) != 3:
                raise ValueError('source clause must have three distinct variables')
            clauses.append(row)
            row = []
        else:
            if abs(lit) > N:
                raise ValueError('source literal outside header')
            row.append(lit)
    if row or len(clauses) != M:
        raise ValueError('incomplete or incorrect source clauses')
    return clauses


def source_cases(label, blob):
    archive_name, expected_sha = ARCHIVES[label]
    observed = hashlib.sha256(blob).hexdigest()
    if observed != expected_sha:
        raise ValueError(f'publisher archive hash changed: {archive_name} {observed}')
    selected = []
    with tarfile.open(fileobj=io.BytesIO(blob), mode='r:gz') as tf:
        members = sorted(
            (member for member in tf.getmembers() if member.isfile() and member.name.lower().endswith('.cnf')),
            key=lambda member: member.name,
        )
        names = [member.name for member in members]
        if len(members) < SAMPLE or len(names) != len(set(names)):
            raise ValueError('publisher archive member mismatch')
        for rank, member in enumerate(members[:SAMPLE]):
            if member.size > 100_000:
                raise ValueError('unexpectedly large source CNF')
            original = tf.extractfile(member).read()
            selected.append({
                'publisher_label': label,
                'source_archive': archive_name,
                'source_rank': rank,
                'source_member': member.name,
                'source_sha256': hashlib.sha256(original).hexdigest(),
                'clauses': parse_dimacs(original),
            })
    return selected


def verify_assignment(clauses, assignment):
    if not isinstance(assignment, list) or len(assignment) != N:
        raise ValueError('invalid assignment length')
    if not all(v in (-1, 0, 1) for v in assignment):
        raise ValueError('invalid assignment value')
    return all(any(assignment[abs(lit) - 1] == (1 if lit > 0 else 0) for lit in row)
               for row in clauses)


def run_native(binary, clauses):
    request = json.dumps({'nvars': N, 'clauses': clauses, 'scan_cap': CAP, 'repeats': REPEATS})
    proc = subprocess.run([str(binary)], input=request, text=True, capture_output=True,
                          check=True, timeout=120)
    result = json.loads(proc.stdout)
    if (result['nvars'], result['source_clause_count'], result['scan_cap'], result['repeats']) != (N, M, CAP, REPEATS):
        raise ValueError('native run changed the frozen input')
    if set(result['arms']) != set(POLICIES):
        raise ValueError('native run missing policy')
    for policy, stats in result['arms'].items():
        if stats['verdict'] not in ('SAT', 'UNSAT', 'CENSORED'):
            raise ValueError('bad native verdict')
        if stats['clause_visits'] > CAP or len(stats['wall_repeats_ns']) != REPEATS:
            raise ValueError('bad native accounting')
        if stats['verdict'] == 'SAT' and not verify_assignment(clauses, stats['assignment']):
            raise ValueError(f'bad original-CNF witness from {policy}')
        if stats['verdict'] != 'SAT' and stats['assignment'] is not None:
            raise ValueError('non-SAT verdict with witness')
    return result['arms']


def independent_glucose(clauses):
    from pysat.solvers import Solver
    with Solver(name='g3', bootstrap_with=clauses) as oracle:
        answer = oracle.solve()
        if answer and not verify_assignment(clauses, [1 if v in oracle.get_model() else 0 for v in range(1, N + 1)]):
            raise ValueError('Glucose model does not satisfy source')
    return 'SAT' if answer else 'UNSAT'


def capped_work(stats):
    return stats['clause_visits'] if stats['verdict'] != 'CENSORED' else 2 * CAP


def summarize(rows):
    by_policy = {}
    for policy in POLICIES:
        by_policy[policy] = {
            'solved_sat': sum(r['arms'][policy]['verdict'] == 'SAT' for r in rows),
            'solved_unsat': sum(r['arms'][policy]['verdict'] == 'UNSAT' for r in rows),
            'censored': sum(r['arms'][policy]['verdict'] == 'CENSORED' for r in rows),
            'total_capped_clause_work': sum(capped_work(r['arms'][policy]) for r in rows),
            'total_median_wall_ms': sum(r['arms'][policy]['median_wall_ns'] for r in rows) / 1e6,
            'median_case_wall_ms': statistics.median(r['arms'][policy]['median_wall_ns'] for r in rows) / 1e6,
            'gate_activated_cases': sum(r['arms'][policy]['gate_activations'] != 0 for r in rows),
        }
    moms, gate = by_policy['moms'], by_policy['gated_probe']
    effect = (moms['total_capped_clause_work'] - gate['total_capped_clause_work']) / moms['total_capped_clause_work']
    success = (
        gate['solved_sat'] >= moms['solved_sat']
        and gate['solved_unsat'] >= moms['solved_unsat']
        and effect >= 0.10
        and gate['total_median_wall_ms'] <= moms['total_median_wall_ms']
    )
    return {
        'policies': by_policy,
        'gated_vs_moms_capped_work_relative_improvement': effect,
        'primary_gate_passed': success,
        'primary_interpretation': ('FROZEN_THRESHOLD_PASSED_NEEDS_EXTERNAL_REPLICATION'
                                   if success else 'NO_COST_EFFECTIVE_ADVANTAGE_ESTABLISHED'),
        'pairwise_gated_minus_moms_capped_work':
            [capped_work(r['arms']['gated_probe']) - capped_work(r['arms']['moms']) for r in rows],
    }


def run():
    binary = Path(os.environ['W042_RUST_BINARY'])
    if not binary.is_file():
        raise ValueError('native Rust binary not found')
    rows = []
    for label in ('SAT', 'UNSAT'):
        filename, _ = ARCHIVES[label]
        blob = Path(os.environ['W042_ARCHIVE_DIR'], filename).read_bytes()
        for source in source_cases(label, blob):
            oracle = independent_glucose(source['clauses'])
            if oracle != label:
                raise ValueError('publisher label disagrees with independent Glucose3')
            arms = run_native(binary, source['clauses'])
            for policy, stats in arms.items():
                if stats['verdict'] not in (label, 'CENSORED'):
                    raise ValueError(f'{policy} disagrees with publisher and Glucose3')
            rows.append({**source, 'glucose3_verdict': oracle, 'arms': arms})
    if len(rows) != 2 * SAMPLE:
        raise RuntimeError('source selection changed')
    summary = summarize(rows)
    report = {
        'study': 'W-CROSSDOMAIN-042',
        'phase': 'preregistered-published-satlib-root-lookahead',
        'protocol': 'docs/W_CROSSDOMAIN_042_ACTIONABLE_BRANCHING_PROTOCOL.md',
        'source': PUBLISHER,
        'sha256_by_archive': {label: sha for label, (_, sha) in ARCHIVES.items()},
        'nvars': N, 'clauses_per_formula': M, 'cases_per_label': SAMPLE,
        'scan_cap': CAP, 'repeats': REPEATS,
        'summary': summary, 'rows': rows,
    }
    path = Path(os.environ['W042_REPORT_PATH'])
    path.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print('W042_COMPLETE', len(rows), 'primary', summary['primary_interpretation'],
          'work_improvement', round(summary['gated_vs_moms_capped_work_relative_improvement'], 6),
          'censored', {p: summary['policies'][p]['censored'] for p in POLICIES}, flush=True)


if __name__ == '__main__':
    run()
