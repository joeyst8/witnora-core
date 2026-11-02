"""Truth-table-independent checking of XOR-only refutation certificates."""
import itertools
import json
import unittest
from pathlib import Path

from scripts.audit_satlib_dubois_xor_contradiction import (
    derive_candidate_refutation, verify_xor_refutation,
)


def canonical_xor_clauses(variables, rhs):
    clauses = []
    for bits in itertools.product((False, True), repeat=len(variables)):
        if (sum(bits) & 1) != rhs:
            clauses.append([(-v if truth else v)
                            for v, truth in zip(variables, bits)])
    return clauses


class SourceXorContradictionTests(unittest.TestCase):
    def test_archived_real_source_certificate_checks_offline(self):
        path = (Path(__file__).resolve().parents[1] / "research" /
                "PR119_DUBOIS20_SOURCE_XOR_CERTIFICATE.json")
        saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(saved["source"], "dubois20.cnf.Z")
        self.assertEqual(saved["source_sha256"],
                         "82059aba0e5773644b386eb6bcbe53680655390cb041873a3cb3e93f7bd896a7")
        proof = saved["proof_equations"]
        source_clauses = [c for row in proof for c in row["source_clauses"]]
        self.assertEqual(len({frozenset(c) for c in source_clauses}), 160)
        checked = verify_xor_refutation(source_clauses,
                                        saved["original_variables"], proof)
        self.assertEqual(checked["status"], "CHECKED_SOURCE_XOR_CONTRADICTION")
        self.assertEqual(checked["proof_rows"], 40)
        self.assertFalse(saved["lean_kernel_checked"])

    def test_exact_source_equations_give_independent_unsat_certificate(self):
        variables = (1, 2, 3)
        left = canonical_xor_clauses(variables, 0)
        right = canonical_xor_clauses(variables, 1)
        raw = left + right
        proof = [{"variables": list(variables), "rhs": rhs,
                  "source_clauses": clauses}
                 for rhs, clauses in ((0, left), (1, right))]
        result = verify_xor_refutation(raw, 3, proof)
        self.assertEqual(result["status"], "CHECKED_SOURCE_XOR_CONTRADICTION")
        self.assertEqual(result["proof_rows"], 2)
        self.assertEqual(result["distinct_source_clauses_covered"], 8)
        self.assertFalse(result["lean_kernel_checked"])

    def test_source_clause_tampering_fails_closed(self):
        variables = (1, 2, 3)
        first = canonical_xor_clauses(variables, 0)
        second = canonical_xor_clauses(variables, 1)
        proof = [{"variables": list(variables), "rhs": 0,
                  "source_clauses": first},
                 {"variables": list(variables), "rhs": 1,
                  "source_clauses": second[:-1]}]
        with self.assertRaises(AssertionError):
            verify_xor_refutation(first + second, 3, proof)
        proof[1]["source_clauses"] = [[1, 2, 4]]
        with self.assertRaises(ValueError):
            verify_xor_refutation(first + second, 3, proof)

    def test_no_xor_contradiction_is_not_unsat(self):
        only = canonical_xor_clauses((1, 2, 3), 0)
        derived = derive_candidate_refutation(only, 3)
        self.assertEqual(derived["status"],
                         "UNKNOWN_NO_EXTRACTED_XOR_CONTRADICTION")


if __name__ == "__main__":
    unittest.main()
