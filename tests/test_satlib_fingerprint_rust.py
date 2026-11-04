"""R-070 seeded Python/native structural fingerprint comparisons."""
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.satlib_fingerprint import fingerprint


class SatlibFingerprintRustTests(unittest.TestCase):
    def test_400_canonical_sources_with_empty_and_disconnected_cases(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")
        rng = random.Random(70070)
        for trial in range(400):
            rows = []
            for _ in range(rng.randrange(24)):
                rows.append([rng.choice((-1, 1)) * rng.randrange(1, 24)
                             for _ in range(rng.randrange(6))])
            source = CNFFormula.from_raw_clauses(rows)
            with self.subTest(trial=trial):
                self.assertEqual(fingerprint(source, backend="rust"),
                                 fingerprint(source, backend="python"))
        with self.assertRaises(ValueError):
            fingerprint(CNFFormula(), backend="other")


if __name__ == "__main__":
    unittest.main()
