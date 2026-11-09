"""Independent truth-table and accounting tests for the W042 native engine."""

from __future__ import annotations

import json
import os
from pathlib import Path
import random
import subprocess
import unittest

from scripts.benchmark_w042_branching import parse_dimacs, verify_assignment


def exhaustive(n, clauses):
    for mask in range(1 << n):
        if all(any((bool(mask & (1 << (abs(lit) - 1))) == (lit > 0)) for lit in row)
               for row in clauses):
            return True
    return False


class W042BranchingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = os.environ.get('W042_RUST_BINARY')
        if not cls.binary or not Path(cls.binary).is_file():
            raise unittest.SkipTest('native Rust W042 binary not built')

    def invoke(self, n, clauses, cap=2_000_000):
        proc = subprocess.run([self.binary], input=json.dumps({
            'nvars': n, 'clauses': clauses, 'scan_cap': cap, 'repeats': 1,
        }), capture_output=True, text=True, timeout=20, check=True)
        return json.loads(proc.stdout)

    def test_130_fresh_random_sources_against_independent_truth_tables(self):
        rng = random.Random(420042)
        for case in range(130):
            n = rng.randrange(3, 9)
            clauses = []
            for _ in range(rng.randrange(1, 5 * n)):
                variables = rng.sample(range(1, n + 1), rng.randrange(1, min(3, n) + 1))
                clauses.append([v if rng.randrange(2) else -v for v in variables])
            truth = exhaustive(n, clauses)
            result = self.invoke(n, clauses)
            self.assertEqual(set(result['arms']), {'degree', 'moms', 'probe', 'gated_probe'}, case)
            for policy, arm in result['arms'].items():
                self.assertEqual(arm['verdict'], 'SAT' if truth else 'UNSAT', (case, policy))
                self.assertLessEqual(arm['clause_visits'], 2_000_000)
                if truth:
                    witness = arm['assignment']
                    self.assertTrue(all(any(witness[abs(lit) - 1] == (1 if lit > 0 else 0)
                                            for lit in row) for row in clauses), case)

    def test_budget_fail_closed_and_malformed_rejection(self):
        source = [[1, 2, 3], [-1, 2, 3], [1, -2, 3], [-1, -2, -3]]
        result = self.invoke(3, source, cap=1)
        for policy, arm in result['arms'].items():
            self.assertEqual(arm['verdict'], 'CENSORED', policy)
            self.assertEqual(arm['clause_visits'], 1)
        for bad in ([[0, 1]], [[1, -1]], [[4, 1]]):
            proc = subprocess.run([self.binary], input=json.dumps({
                'nvars': 3, 'clauses': bad, 'scan_cap': 100, 'repeats': 1,
            }), capture_output=True, text=True, timeout=10)
            self.assertNotEqual(proc.returncode, 0)

    def test_strict_publisher_parser(self):
        original = b'p cnf 50 218\n' + b'1 2 3 0\n' * 218 + b'%\n0\n'
        rows = parse_dimacs(original)
        self.assertEqual(len(rows), 218)
        with self.assertRaises(ValueError):
            parse_dimacs(original.replace(b'p cnf 50 218', b'p cnf 50 217'))
        with self.assertRaises(ValueError):
            parse_dimacs(original.replace(b'1 2 3 0', b'1 2 2 0', 1))
        self.assertFalse(verify_assignment(rows, [0] * 50))
        self.assertTrue(verify_assignment(rows, [1] + [0] * 49))


if __name__ == '__main__':
    unittest.main()
