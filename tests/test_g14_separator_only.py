"""Separator-only clauses: branch-conditioned empty-clause adversarial tests."""
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.operator_genesis import AffineResidueInstance, build_affine_residue_certificate, AFFINE_RESIDUE_SAT_WITNESS_VERIFIED, AFFINE_RESIDUE_CERTIFICATE_VERIFIED
from witnora_core.separator_affine_family_theorem import (
    SeparatorAffineFamilyInstance,
    SAT_CERTIFIED,
    UNSAT_CERTIFIED,
    build_separator_affine_certificate,
    check_separator_affine_certificate,
)


def instance(name, clauses):
    return SeparatorAffineFamilyInstance(
        instance_id=name, formula=CNFFormula.from_raw_clauses(clauses),
        separator_variables=[1], separator_bound_c=1,
        affine_arity_bound_r=2, expected_result="test",
        family="separator_only", n=1,
    )


class G14SeparatorOnly(unittest.TestCase):
    def test_empty_affine_component_trivial_sat_evidence(self):
        formula = CNFFormula.from_raw_clauses([])
        cert = build_affine_residue_certificate(
            AffineResidueInstance(instance_id="empty_sat_component",
                                  equations=(), formula=formula), max_arity=2)
        self.assertEqual(cert.status, AFFINE_RESIDUE_SAT_WITNESS_VERIFIED)
        self.assertEqual(cert.checker_status, AFFINE_RESIDUE_CERTIFICATE_VERIFIED)
        self.assertEqual(cert.solution, {})

    def test_opposite_units_cover_both_branches(self):
        item = instance("separator_unit_unsat", [[1], [-1]])
        cert = build_separator_affine_certificate(item)
        self.assertEqual(cert.final_result, UNSAT_CERTIFIED)
        self.assertEqual(len(cert.separator_assignments), 2)
        self.assertEqual(set(cert.unsat_cover["covering_unsat_component_per_assignment"]), {"S1", "S2"})
        self.assertEqual(
            check_separator_affine_certificate(item.formula, cert)["status"],
            "SEPARATOR_AFFINE_CERTIFICATE_VERIFIED",
        )

    def test_one_unit_cannot_be_misclassified_unsat(self):
        item = instance("separator_unit_sat", [[1]])
        cert = build_separator_affine_certificate(item)
        self.assertEqual(cert.final_result, SAT_CERTIFIED)
        self.assertIsNone(cert.unsat_cover)
        self.assertTrue(cert.sat_witness["verified_against_original_cnf"])
        self.assertEqual(
            check_separator_affine_certificate(item.formula, cert)["status"],
            "SEPARATOR_AFFINE_CERTIFICATE_VERIFIED",
        )


if __name__ == "__main__":
    unittest.main()
