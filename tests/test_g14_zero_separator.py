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

    def test_empty_clause_without_variables_exposes_separate_gap(self):
        item = instance("empty_zero_separator", [[]])
        cert = build_separator_affine_certificate(item)
        # Current component finder has no variable vertex to assign the
        # empty clause to; this is distinct from the now-fixed G5 arity gap.
        self.assertNotEqual(cert.final_result, UNSAT_CERTIFIED)


if __name__ == "__main__":
    unittest.main()
