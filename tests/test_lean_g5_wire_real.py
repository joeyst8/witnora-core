"""Real Lean smoke test for the source-G5 numeric-wire acceptance gate.

This test invokes both production Python certificate generation and the
actual Lean executable checker, not a mocked subprocess.
"""
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.lean_g5_gate import verify_g5_certificate_with_lean
from witnora_core.operator_genesis import (
    AffineResidueInstance,
    build_affine_residue_certificate,
)


class G5WireRealLeanTest(unittest.TestCase):
    def test_small_conflicting_unit_rows_reach_lean_verified(self):
        formula = CNFFormula.from_raw_clauses([[1], [-1]])
        instance = AffineResidueInstance(
            instance_id="tc063_wire_codec_small_unsat",
            equations=(),
            formula=formula,
        )
        cert = build_affine_residue_certificate(instance, max_arity=2)
        result = verify_g5_certificate_with_lean(
            formula,
            cert,
            max_arity=2,
            timeout_seconds=120,
            use_sparse_checker=True,
        )
        self.assertTrue(result.get("verified"), result)
        self.assertEqual(result["lean_formal_status"], "LEAN_VERIFIED")


    def test_overlapping_affine_source_document_reaches_lean_verified(self):
        """Exercise exact DIMACS bytes, overlapping XOR extraction and indexed G5."""
        from pathlib import Path
        from witnora_core.dimacs import load_dimacs_with_document_evidence

        fixture = Path(__file__).resolve().parents[1] / "fixtures" / "tc063_three_row_affine_unsat.cnf"
        formula, raw, tokens, spellings, source = load_dimacs_with_document_evidence(fixture)
        self.assertEqual(formula.num_clauses, 10)
        instance = AffineResidueInstance(
            instance_id="tc063_three_row_affine_source_unsat",
            equations=(),
            formula=formula,
        )
        cert = build_affine_residue_certificate(instance, max_arity=3)
        self.assertEqual(cert.status, "AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED")
        self.assertEqual(len(cert.equations), 3)
        self.assertGreaterEqual(len(cert.row_operations), 2)

        result = verify_g5_certificate_with_lean(
            formula,
            cert,
            max_arity=3,
            timeout_seconds=180,
            raw_clauses=raw,
            source_tokens=tokens,
            source_spellings=spellings,
            source_text=source,
        )
        self.assertTrue(result.get("verified"), result)
        self.assertEqual(result["lean_formal_status"], "LEAN_VERIFIED")
        self.assertTrue(result["source_document_verified"], result)
        self.assertTrue(result["source_lexemes_verified"], result)
        self.assertTrue(result["source_normalization_verified"], result)

        # The same trusted row operations must not be accepted if the
        # original source document's declared clause count was tampered with.
        tampered_document = source.replace("p cnf 4 10", "p cnf 4 9")
        self.assertNotEqual(tampered_document, source)
        rejected = verify_g5_certificate_with_lean(
            formula,
            cert,
            max_arity=3,
            timeout_seconds=180,
            raw_clauses=raw,
            source_tokens=tokens,
            source_spellings=spellings,
            source_text=tampered_document,
        )
        self.assertFalse(rejected.get("verified"), rejected)
        self.assertEqual(rejected.get("lean_formal_status"), "NOT_LEAN_VERIFIED")
        self.assertEqual(rejected.get("reason"), "CNF_NORMALIZATION_REJECTED")


    def test_sparse_cycle_long_refutations_across_large_variable_ids(self):
        """Lean-verify long XOR refutations without dense max-ID allocation."""
        from time import perf_counter
        from witnora_core.xor import canonical_xor_cnf_clauses

        for n, offset in ((8, 0), (16, 1048576), (32, 16777216)):
            with self.subTest(cycle_rows=n, first_variable=offset + 1):
                equations = [
                    ([offset + i, offset + i + 1], 0)
                    for i in range(1, n)
                ]
                equations.append(([offset + 1, offset + n], 1))
                raw = [
                    list(clause)
                    for variables, rhs in reversed(equations)
                    for clause in sorted(canonical_xor_cnf_clauses(variables, rhs))
                ]
                formula = CNFFormula.from_raw_clauses(raw)
                self.assertEqual(formula.num_clauses, 2 * n)
                instance = AffineResidueInstance(
                    instance_id=f"tc063_sparse_cycle_{n}_{offset}",
                    equations=(),
                    formula=formula,
                )

                start = perf_counter()
                cert = build_affine_residue_certificate(instance, max_arity=2)
                generation_s = perf_counter() - start
                self.assertEqual(cert.status, "AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED")
                self.assertEqual(len(cert.equations), n)
                self.assertGreaterEqual(len(cert.row_operations), n - 1)

                start = perf_counter()
                result = verify_g5_certificate_with_lean(
                    formula,
                    cert,
                    max_arity=2,
                    timeout_seconds=180,
                    use_sparse_checker=True,
                )
                lean_s = perf_counter() - start
                self.assertTrue(result.get("verified"), result)
                self.assertEqual(result["lean_formal_status"], "LEAN_VERIFIED")
                print(
                    f"TC063_SPARSE_CYCLE n={n} max_id={offset + n} "
                    f"clauses={formula.num_clauses} "
                    f"indexed_ops={len(cert.row_operations)} "
                    f"python_generation_ms={generation_s * 1000:.1f} "
                    f"lean_gate_ms={lean_s * 1000:.1f}",
                    flush=True,
                )

                # Flip the closing parity: the same structural cycle is SAT,
                # so the producer must not label it an UNSAT certificate.
                sat_equations = equations[:-1] + [(equations[-1][0], 0)]
                sat_raw = [
                    list(clause)
                    for variables, rhs in sat_equations
                    for clause in sorted(canonical_xor_cnf_clauses(variables, rhs))
                ]
                sat_formula = CNFFormula.from_raw_clauses(sat_raw)
                sat_cert = build_affine_residue_certificate(
                    AffineResidueInstance(
                        instance_id=f"tc063_sparse_sat_control_{n}_{offset}",
                        equations=(),
                        formula=sat_formula,
                    ),
                    max_arity=2,
                )
                self.assertNotEqual(
                    sat_cert.status, "AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED"
                )

if __name__ == "__main__":
    unittest.main()
