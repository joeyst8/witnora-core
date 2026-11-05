"""Direct G14 zero-separator and zero-variable-component completeness probes."""
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.separator_affine_family_theorem import (
    SeparatorAffineFamilyInstance,
    UNSAT_CERTIFIED,
    build_separator_affine_certificate,
    check_separator_affine_certificate,
)


def instance(name, clauses):
    return SeparatorAffineFamilyInstance(
        instance_id=name,
        formula=CNFFormula.from_raw_clauses(clauses),
        separator_variables=[],
        separator_bound_c=0,
        affine_arity_bound_r=2,
        expected_result=UNSAT_CERTIFIED,
        family="tc063_zero_separator",
        n=1,
    )


class G14ZeroSeparatorTest(unittest.TestCase):
    def test_unit_contradiction_has_native_single_branch_cover(self):
        item = instance("unit_zero_separator", [[1], [-1]])
        cert = build_separator_affine_certificate(item)
        self.assertEqual(cert.final_result, UNSAT_CERTIFIED)
        self.assertEqual(len(cert.separator_assignments), 1)
        self.assertEqual(cert.separator_variables, [])
        result = check_separator_affine_certificate(item.formula, cert)
        self.assertEqual(result["status"], "SEPARATOR_AFFINE_CERTIFICATE_VERIFIED", result)

    def test_empty_clause_has_zero_variable_cover_component(self):
        item = instance("empty_zero_separator", [[]])
        cert = build_separator_affine_certificate(item)
        self.assertEqual(cert.final_result, UNSAT_CERTIFIED)
        self.assertEqual(len(cert.separator_assignments), 1)
        self.assertEqual(cert.separator_verification["components_after_removal"][0]["component_id"], "C0")
        result = check_separator_affine_certificate(item.formula, cert)
        self.assertEqual(result["status"], "SEPARATOR_AFFINE_CERTIFICATE_VERIFIED", result)


if __name__ == "__main__":
    unittest.main()
