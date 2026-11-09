"""Independent offline integrity replay of the retained W042 negative result."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

from scripts.benchmark_w042_branching import (
    ARCHIVES, CAP, M, N, POLICIES, SAMPLE, source_cases, summarize, verify_assignment,
)

ARCHIVE_PATH = Path('research/results/w042_satlib_raw.json.gz')
EXPECTED_GZIP_SHA = 'b0111420b7398e7ee81e314c5d1c02c4066f59b19116944aee976353b77b2551'
EXPECTED_JSON_SHA = '85a2e86fbbaad4f561b03eff76a6fe7889d93492644fb35f0f4b961fc0f101ee'


def audit(path=ARCHIVE_PATH, publisher_archive_dir=None):
    compressed = Path(path).read_bytes()
    if hashlib.sha256(compressed).hexdigest() != EXPECTED_GZIP_SHA:
        raise ValueError('W042 compressed archive drift')
    raw = gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest() != EXPECTED_JSON_SHA:
        raise ValueError('W042 decompressed JSON drift')
    record = json.loads(raw)
    if (record['nvars'], record['clauses_per_formula'], record['cases_per_label'],
            record['scan_cap'], record['repeats']) != (N, M, SAMPLE, CAP, 3):
        raise ValueError('frozen W042 protocol mismatch')
    rows = record['rows']
    if len(rows) != 64:
        raise ValueError('changed sample size')
    for label, (filename, _archive_sha) in ARCHIVES.items():
        subset = [r for r in rows if r['publisher_label'] == label]
        if len(subset) != SAMPLE or [r['source_rank'] for r in subset] != list(range(SAMPLE)):
            raise ValueError('source selection not frozen')
        if publisher_archive_dir is not None:
            original = source_cases(label, (Path(publisher_archive_dir) / filename).read_bytes())
            if [(r['source_member'], r['source_sha256'], r['clauses']) for r in subset] != [
                    (r['source_member'], r['source_sha256'], r['clauses']) for r in original]:
                raise ValueError('source differs from independently downloaded publisher bytes')
        for row in subset:
            if row['glucose3_verdict'] != label or len(row['clauses']) != M:
                raise ValueError('bad independent oracle/source record')
            if set(row['arms']) != set(POLICIES):
                raise ValueError('policy arm missing')
            for policy, arm in row['arms'].items():
                if arm['verdict'] != label or arm['clause_visits'] > CAP:
                    raise ValueError('wrong / censored source classification')
                if arm['verdict'] == 'SAT' and not verify_assignment(row['clauses'], arm['assignment']):
                    raise ValueError('invalid direct original-CNF witness')
                if len(arm['wall_repeats_ns']) != 3:
                    raise ValueError('missing timing repetitions')
            base = row['arms']['moms']
            probe = row['arms']['probe']
            gate = row['arms']['gated_probe']
            if probe['clause_visits'] - base['clause_visits'] != 16 * M:
                raise ValueError('full root probe not vacuous as expected')
            activated = gate['gate_activations'] != 0
            if gate['clause_visits'] - base['clause_visits'] != (16 * M if activated else 0):
                raise ValueError('gated root probe workload changed')
            for arm in (probe, gate):
                if arm['nodes'] != base['nodes'] or arm['decisions'] != base['decisions']:
                    raise ValueError('vacuous root probe changed search tree')
    if summarize(rows) != record['summary']:
        raise ValueError('reported totals differ from independent replay')
    print('W042_AUDIT_OK', len(rows), 'gated_delta_clause_visits',
          record['summary']['policies']['gated_probe']['total_capped_clause_work']
          - record['summary']['policies']['moms']['total_capped_clause_work'])
    return True


if __name__ == '__main__':
    import os
    audit(publisher_archive_dir=os.environ.get('W042_ARCHIVE_DIR'))
