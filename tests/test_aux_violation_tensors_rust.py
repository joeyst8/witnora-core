"""R-077 finite auxiliary violation bridge and scope equivalence."""
import random
import unittest

from witnora_core.aux_violation_tensors import (
    independent_violation_mask, auxiliary_factor_scopes,
    direct_parity_factor_scopes, exact_source_models_small,
    auxiliary_weight_profile_small, constant_term_matches_source,
)
from witnora_core.sparse_parity_checks import build_sparse_odd_sketch


class AuxiliaryBridgeRustTests(unittest.TestCase):
    def setUp(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")

    def test_120_seeded_scopes_and_finite_profiles(self):
        rng = random.Random(77077)
        for trial in range(120):
            n = rng.randrange(3, 8)
            source = []
            for _ in range(rng.randrange(1, 13)):
                chosen = rng.sample(range(1, n + 1), 3)
                source.append([v if rng.randrange(2) else -v for v in chosen])
            sketch = build_sparse_odd_sketch(source, n, seed=73 + trial)
            with self.subTest(trial=trial):
                self.assertEqual(auxiliary_factor_scopes(source, sketch, backend="rust"),
                                 auxiliary_factor_scopes(source, sketch))
                self.assertEqual(direct_parity_factor_scopes(source, sketch, backend="rust"),
                                 direct_parity_factor_scopes(source, sketch))
                self.assertEqual(auxiliary_weight_profile_small(source, sketch, backend="rust"),
                                 auxiliary_weight_profile_small(source, sketch))
                self.assertEqual(exact_source_models_small(source, n, backend="rust"),
                                 exact_source_models_small(source, n))
                self.assertEqual(constant_term_matches_source(source, sketch, backend="rust"),
                                 constant_term_matches_source(source, sketch))
                for x in range(1 << n):
                    cnf = tuple(tuple(row) for row in source)
                    self.assertEqual(independent_violation_mask(cnf, x, backend="rust"),
                                     independent_violation_mask(cnf, x))

    def test_exponential_bound_enforced(self):
        source = [[1, 2, 3]]
        sketch = build_sparse_odd_sketch(source, 3)
        with self.assertRaises(ValueError):
            auxiliary_weight_profile_small(source, sketch, max_variables=2,
                                           backend="rust")
        with self.assertRaises(ValueError):
            exact_source_models_small(source, 3, max_variables=2, backend="rust")


if __name__ == "__main__":
    unittest.main()
