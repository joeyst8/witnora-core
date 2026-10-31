"""Seeded independent-format and mutation assertions."""
import unittest

from witnora_core.ascii_certificate_adversarial import (
    exercise_seeded_cases, generate_structured_cases,
    independent_reference_bytes, mutate_bytes,
)
from witnora_core.lean_ascii_certificate_export import (
    serialize_ascii_certificate, emit_ascii_lean,
)


class AdversarialAsciiTests(unittest.TestCase):
    def test_structured_kernel_inputs(self):
        cases = generate_structured_cases()
        self.assertEqual(len(cases), 4)
        generated = emit_ascii_lean(cases)
        for name, n, edges, colors, clique in cases:
            self.assertEqual(
                serialize_ascii_certificate(n, edges, colors, clique),
                independent_reference_bytes(n, edges, colors, clique),
            )
            self.assertIn(f"{name}AsciiOptimal", generated)

    def test_seeded_independent_cross_check(self):
        trials = exercise_seeded_cases()
        self.assertEqual(len(trials), 200)
        self.assertEqual(trials, exercise_seeded_cases())
        self.assertTrue(all(len(bad) >= 6 for _, _, bad in trials))

    def test_mutation_families_change_bytes(self):
        data = b"2|2|0,1;0,2;1,2|0,1,2|0,1,2"
        variants = mutate_bytes(data)
        self.assertGreaterEqual(len(variants), 6)
        self.assertTrue(all(other != data for other in variants))


if __name__ == "__main__":
    unittest.main()
