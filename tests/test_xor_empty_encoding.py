"""Zero-variable XOR encoding must distinguish tautology from contradiction."""
import unittest
from itertools import product
from random import Random

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.xor import XorEquation, canonical_xor_cnf_clauses


class EmptyXorEncodingTest(unittest.TestCase):
    def test_seeded_noncontiguous_and_repeated_variable_encodings(self):
        rng = Random(20261029)
        pool = [1, 3, 5, 8, 11]
        for _ in range(180):
            variables = [rng.choice(pool) for _ in range(rng.randrange(0, 11))]
            rhs = rng.randrange(2)
            formula = CNFFormula.from_raw_clauses(
                canonical_xor_cnf_clauses(variables, rhs)
            )
            for values in product((False, True), repeat=len(pool)):
                assignment = dict(zip(pool, values))
                xor_true = (sum(bool(assignment[v]) for v in variables) % 2) == rhs
                self.assertEqual(
                    formula_satisfied(formula, assignment), xor_true,
                    f"raw_vars={variables} rhs={rhs} assignment={assignment}",
                )

    def test_exact_canonical_clause_family_for_all_small_distinct_supports(self):
        # Independent mask-based specification, including literal signs and
        # the exact clause family (stronger than truth-table equivalence).
        for size in range(7):
            support = tuple(2 * i + 1 for i in range(size))
            for rhs in (0, 1):
                expected = set()
                for mask in range(1 << size):
                    if mask.bit_count() % 2 == rhs:
                        continue
                    clause = tuple(sorted(
                        -var if (mask >> position) & 1 else var
                        for position, var in enumerate(support)
                    ))
                    expected.add(clause)
                self.assertEqual(
                    canonical_xor_cnf_clauses(reversed(support), rhs),
                    expected,
                    f"support={support} rhs={rhs}",
                )

    def test_repeated_ids_normalize_exactly_and_stably(self):
        rng = Random(630063)
        for _ in range(350):
            raw = [rng.randrange(1, 13) for _ in range(rng.randrange(20))]
            parity_support = tuple(
                var for var in range(1, 13) if raw.count(var) % 2
            )
            rhs = rng.randrange(2)
            self.assertEqual(
                canonical_xor_cnf_clauses(raw, rhs),
                canonical_xor_cnf_clauses(parity_support, rhs),
            )
            self.assertEqual(
                canonical_xor_cnf_clauses(tuple(reversed(raw)), rhs),
                canonical_xor_cnf_clauses(raw, rhs),
            )

    def test_equation_and_encoder_share_one_pass_toggle_normalization(self):
        rng = Random(6302026)
        for _ in range(400):
            raw = [rng.randrange(1, 35) for _ in range(rng.randrange(25))]
            rhs = rng.randrange(2)
            expected = tuple(sorted(
                v for v in set(raw) if raw.count(v) % 2 == 1
            ))
            equation = XorEquation(iter(raw), rhs)
            self.assertEqual(equation.variables, expected)
            self.assertEqual(
                canonical_xor_cnf_clauses(iter(raw), rhs),
                canonical_xor_cnf_clauses(expected, rhs),
            )

    def test_invalid_variable_ids_are_rejected_even_if_they_cancel(self):
        for variables in ([0], [-1], [0, 0], [-2, -2], [1, -3, -3]):
            for rhs in (0, 1):
                with self.subTest(variables=variables, rhs=rhs):
                    with self.assertRaises(ValueError):
                        canonical_xor_cnf_clauses(variables, rhs)

    def test_empty_even_equation_is_tautology(self):
        self.assertEqual(canonical_xor_cnf_clauses([], 0), set())
        self.assertEqual(CNFFormula.from_raw_clauses(
            canonical_xor_cnf_clauses([], 0)).num_clauses, 0)
        self.assertTrue(XorEquation([], 0).is_tautology)

    def test_repeated_xor_variables_cancel_mod_two(self):
        self.assertEqual(canonical_xor_cnf_clauses([1, 1], 0), set())
        self.assertEqual(canonical_xor_cnf_clauses([1, 1], 1), {()})
        self.assertEqual(canonical_xor_cnf_clauses([1, 1, 2], 1), {(2,)})
        self.assertEqual(canonical_xor_cnf_clauses([1, 2, 1], 0), {(-2,)})

    def test_empty_odd_equation_is_contradiction(self):
        self.assertEqual(canonical_xor_cnf_clauses([], 1), {()})
        formula = CNFFormula.from_raw_clauses(canonical_xor_cnf_clauses([], 1))
        self.assertTrue(formula.contains_empty_clause)
        self.assertTrue(XorEquation([], 1).is_contradiction)


if __name__ == "__main__":
    unittest.main()
