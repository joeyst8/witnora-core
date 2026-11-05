"""Independent original-signed-CNF controls for W-CRC-001."""
import itertools
import random
import unittest

from witnora_core.crc_source import count_signed_cnf_crc, extract_exact_small_xors


def exhaustive_source_count(clauses, nvars):
    count = 0
    for assignment in itertools.product((False, True), repeat=nvars):
        if all(any(assignment[abs(lit)-1] == (lit > 0) for lit in clause)
               for clause in clauses):
            count += 1
    return count


def make_xor_cnf(vars, rhs):
    result = []
    for bits in itertools.product((0, 1), repeat=len(vars)):
        if sum(bits) % 2 != rhs:
            result.append(tuple(v if bit == 0 else -v
                                for v, bit in zip(vars, bits)))
    return result


def parity_chain_source(k, parity_rhs=0):
    assert k >= 3
    equations = []
    prev = k + 1
    equations.append(((1, 2, prev), 0))
    for i in range(3, k):
        nxt = k + i - 1
        equations.append(((prev, i, nxt), 0))
        prev = nxt
    equations.append(((prev, k), parity_rhs))
    return [clause for vars, rhs in equations for clause in make_xor_cnf(vars, rhs)], 2*k-2


class TestSourceCRC(unittest.TestCase):
    def test_exact_small_xor_patterns(self):
        for k in (1, 2, 3):
            vars = tuple(range(1, k + 1))
            for rhs in (0, 1):
                clauses = make_xor_cnf(vars, rhs)
                rows, remaining = extract_exact_small_xors(clauses, k)
                self.assertEqual(rows, (((1 << k) - 1, rhs),))
                self.assertEqual(remaining, ())
                count = count_signed_cnf_crc(clauses, k)
                self.assertEqual(count.models, 1 << (k-1))

    def test_malformed_literals_rejected_even_inside_tautology(self):
        with self.assertRaises(ValueError):
            count_signed_cnf_crc(((1, -1, 0),), 1)
        with self.assertRaises(ValueError):
            count_signed_cnf_crc(((3,),), 2)

    def test_adversarial_missing_gadget_clause_is_not_extracted(self):
        clauses = make_xor_cnf((1, 2, 3), 0)[:-1]
        rows, residual = extract_exact_small_xors(clauses, 3)
        self.assertEqual(rows, ())
        self.assertEqual(len(residual), 3)
        self.assertEqual(count_signed_cnf_crc(clauses, 3).models,
                         exhaustive_source_count(clauses, 3))

    def test_duplicate_tautology_empty_and_free_vars(self):
        clauses = ((1,), (1,), (1, -1), (2, 3))
        count = count_signed_cnf_crc(clauses, 5)
        self.assertEqual(count.models, exhaustive_source_count(clauses, 5))
        self.assertEqual(count_signed_cnf_crc(((),), 5).models, 0)

    def test_seeded_original_cnf_random(self):
        rng = random.Random(162001)
        for _ in range(400):
            n = rng.randrange(1, 9)
            clauses = []
            for _ in range(rng.randrange(0, 13)):
                clauses.append(tuple(rng.choice((-1, 1)) * rng.randrange(1,n+1)
                                     for _ in range(rng.randrange(0, 5))))
            # Plant a sound exact XOR gadget in one third of controls.
            if rng.randrange(3) == 0:
                vars = tuple(sorted(rng.sample(range(1,n+1), k=rng.randint(1,min(3,n)))))
                clauses.extend(make_xor_cnf(vars, rng.randrange(2)))
            result = count_signed_cnf_crc(clauses, n,
                                          max_inclusion_subsets=4096)
            self.assertIsNotNone(result)
            self.assertEqual(result.models, exhaustive_source_count(clauses,n),
                             msg=f"{n=} {clauses=}")

    def test_source_cnf_60_boundary_gadget_chain(self):
        xor_clauses, nvars = parity_chain_source(60)
        nonlinear = [tuple(range(i, i + 3)) for i in range(1, 61, 3)]
        result = count_signed_cnf_crc(
            xor_clauses + nonlinear, nvars,
            max_spectrum_terms=8, max_inclusion_subsets=64,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.models, (7**20 + 1)//2)
        self.assertEqual(result.extracted_affine_rows, 59)
        self.assertEqual(result.residual_clauses, 20)
        self.assertEqual(result.boundary_variables, 60)
        self.assertEqual(result.coefficient_stats.left_fourier_terms, 2)
        self.assertEqual(result.coefficient_stats.right_components, 20)

    def test_budget_failure_is_not_unsat(self):
        clauses = tuple((1, i) for i in range(2, 16))
        self.assertIsNone(count_signed_cnf_crc(
            clauses, 15, max_inclusion_subsets=100,
        ))


if __name__ == "__main__":
    unittest.main()
