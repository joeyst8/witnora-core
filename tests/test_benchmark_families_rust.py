"""R-073 exact native/source parity for benchmark formula families."""
import unittest

from witnora_core.families import (
    make_blocked_clique_collapse_family, blocked_clique_collapse_family,
    random_2sat_family, random_3sat_family, bounded_treewidth_chain_family,
    bce_heavy_family, component_mixed_family, unsat_unit_conflict_family,
    tautology_noise_family,
)


class BenchmarkFamiliesRustTests(unittest.TestCase):
    def setUp(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")

    def check(self, fn, *args):
        reference = fn(*args)
        native = fn(*args, backend="rust")
        self.assertEqual(native.to_clause_lists(), reference.to_clause_lists())
        self.assertEqual(native.formula_hash, reference.formula_hash)

    def test_bounded_deterministic_families(self):
        for n in range(1, 41):
            with self.subTest(family="clique", n=n):
                self.check(make_blocked_clique_collapse_family, n)
                self.check(blocked_clique_collapse_family, n)
                self.check(tautology_noise_family, n)
                self.check(component_mixed_family, n)
                for count in (1, 2, 5):
                    self.check(bce_heavy_family, n, count)
            if n >= 5:
                self.check(bounded_treewidth_chain_family, n)
        self.check(unsat_unit_conflict_family)

    def test_400_seeded_random_source_hashes(self):
        for seed in range(200):
            n2 = 1 + seed % 20
            n3 = 3 + seed % 25
            count = seed % 31
            with self.subTest(seed=seed):
                self.check(random_2sat_family, n2, count, seed)
                self.check(random_3sat_family, n3, count, seed)

    def test_invalid_dimensions(self):
        with self.assertRaises(ValueError):
            make_blocked_clique_collapse_family(0, backend="rust")
        with self.assertRaises(ValueError):
            bounded_treewidth_chain_family(4, backend="rust")
        with self.assertRaises(ValueError):
            bce_heavy_family(2, 0, backend="rust")
        with self.assertRaises(ValueError):
            random_3sat_family(2, 1, 7, backend="rust")


if __name__ == "__main__":
    unittest.main()
