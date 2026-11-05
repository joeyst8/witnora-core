"""R-090: native conjecture-triage differential controls."""
import unittest

from witnora_core.conjecture_triage import triage

try:
    from witnora_ve import conjecture_triage_run_native
except ImportError:
    conjecture_triage_run_native = None


@unittest.skipUnless(conjecture_triage_run_native is not None, "native wheel unavailable")
class ConjectureTriageEndToEndRust(unittest.TestCase):
    def test_full_studies(self):
        for count in (1, 5, 25):
            with self.subTest(count=count):
                self.assertEqual(triage(adversarial_per_seed=count),
                                 triage(adversarial_per_seed=count, backend="rust"))

    def test_witness_and_catalog(self):
        rows = [(2, [(0, 1)], {
            "n": 2, "m": 1, "alpha": 1, "tau": 1, "omega": 2,
            "chi": 2, "nu": 1, "delta": 1})]
        known, unclassified, rejected = conjecture_triage_run_native(
            ["n = (alpha+tau)", "chi = alpha", "m = nu"], rows)
        self.assertEqual(known, ["n = (alpha+tau)"])
        self.assertEqual(unclassified, ["m = nu"])
        self.assertEqual(rejected[0][:2], ("chi = alpha", 2))


if __name__ == "__main__":
    unittest.main()
