"""R-071 exact native spoke classifier against Python and brute SAT oracles."""
from itertools import product
import random
import unittest

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.spoke_collapse import (
    ParitySpoke, spoke_cnf, collapse_spokes, make_spoke_family,
)


class SpokeCollapseRustTests(unittest.TestCase):
    def test_500_seeded_spokes_and_changed_sources(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")
        rng = random.Random(71071)
        for trial in range(500):
            n = rng.randrange(2, 13)
            mids = rng.sample(range(3, 1000), n)
            spokes = tuple(ParitySpoke(mid, rng.randrange(2), rng.randrange(2))
                           for mid in mids)
            source = spoke_cnf(spokes)
            with self.subTest(trial=trial):
                self.assertEqual(spoke_cnf(spokes, backend="rust"), source)
                expected = collapse_spokes(source, spokes)
                self.assertEqual(collapse_spokes(source, spokes, backend="rust"),
                                 expected)
                if expected["status"] == "SAT_WITH_WITNESS":
                    self.assertTrue(formula_satisfied(source, expected["assignment"]))
                other = CNFFormula.from_raw_clauses(source.to_clause_lists() + [[2000]])
                self.assertEqual(collapse_spokes(other, spokes, backend="rust"),
                                 {"status": "UNSUPPORTED"})

    def test_family_witnesses_and_small_independent_enumeration(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")
        for n in range(2, 8):
            for contradictory in (False, True):
                formula, spokes = make_spoke_family(n, contradictory=contradictory)
                got, got_spokes = make_spoke_family(n, contradictory=contradictory,
                                                     backend="rust")
                self.assertEqual((got, got_spokes), (formula, spokes))
                self.assertEqual(collapse_spokes(formula, spokes, backend="rust"),
                                 collapse_spokes(formula, spokes))
                all_models = any(formula_satisfied(formula, dict(zip(formula.variables, bits)))
                                 for bits in product((False, True), repeat=len(formula.variables)))
                self.assertEqual(all_models, not contradictory)
        formula, spokes = make_spoke_family(3, contradictory=True)
        self.assertEqual(collapse_spokes(formula, (spokes[0], spokes[0]), backend="rust"),
                         {"status": "UNSUPPORTED"})
        with self.assertRaises(ValueError):
            spoke_cnf(spokes, backend="unknown")


if __name__ == "__main__":
    unittest.main()
