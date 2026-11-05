"""Exhaustive truth and falsification checks for assumption probing."""
import random
import unittest
from itertools import product

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.forced_relation_probe import (
    probe_forced_relations, unit_conflict,
)


def brute_sat(formula):
    return any(formula_satisfied(formula, dict(zip(formula.variables, values)))
               for values in product((False, True), repeat=formula.num_vars))


class ForcedRelationProbeTests(unittest.TestCase):
    def test_detect_forced_unit(self):
        source = CNFFormula.from_raw_clauses([[1, 2], [1, -2], [-1, 3]])
        self.assertTrue(unit_conflict(source, -1))
        result, info = probe_forced_relations(source)
        self.assertIn(1, info["forced_literals"])
        self.assertTrue(brute_sat(result))

    def test_random_finite_equisatisfiability(self):
        rng = random.Random(98063)
        for _ in range(120):
            rows = []
            for _ in range(rng.randint(1, 16)):
                chosen = rng.sample(range(1, 7), rng.randint(1, 3))
                rows.append([v if rng.getrandbits(1) else -v for v in chosen])
            source = CNFFormula.from_raw_clauses(rows)
            transformed, info = probe_forced_relations(source)
            self.assertEqual(brute_sat(source), brute_sat(transformed))
            self.assertEqual((transformed, info), probe_forced_relations(source))
            self.assertFalse(info["promoted"])

    def test_probe_budget(self):
        source = CNFFormula.from_raw_clauses([[1, 2], [-1, 3]])
        result, meta = probe_forced_relations(source, max_probes=0)
        self.assertEqual(meta["checked_variables"], 0)
        self.assertTrue(brute_sat(result))
        with self.assertRaises(ValueError):
            probe_forced_relations(source, max_probes=-1)


if __name__ == "__main__":
    unittest.main()
