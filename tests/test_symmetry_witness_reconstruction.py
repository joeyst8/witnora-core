import unittest

from witnora_core.cnf import formula_satisfied
from witnora_core.collapse_theory import (
    SYMMETRY_SAT_WITNESS_RECONSTRUCTED,
    build_family_instances,
    build_symmetry_certificate,
    check_symmetry_certificate,
)


class SymmetryWitnessReconstructionTest(unittest.TestCase):
    def test_sat_witness_reconstruction(self):
        instance = build_family_instances(["symmetric-toy"])[0]
        cert = build_symmetry_certificate(instance)
        witness = {int(var): bool(value) for var, value in cert.lifted_assignment.items()}
        self.assertEqual(cert.status, SYMMETRY_SAT_WITNESS_RECONSTRUCTED)
        self.assertTrue(formula_satisfied(instance.formula, witness))
        self.assertEqual(check_symmetry_certificate(instance.formula, cert)["checker_status"], "PASS")
        print("SAT_WITNESS_RECONSTRUCTION_PASS")

    def test_quotient_lift_verification(self):
        instance = next(item for item in build_family_instances(["graph-coloring"]) if item.instance_id == "cycle_6_3color")
        cert = build_symmetry_certificate(instance)
        witness = {int(var): bool(value) for var, value in cert.lifted_assignment.items()}
        self.assertFalse(cert.quotient_used)
        self.assertTrue(formula_satisfied(instance.formula, witness))
        self.assertEqual(cert.reconstruction_map["type"], "direct_assignment_verification")
        print("QUOTIENT_LIFT_VERIFICATION_PASS")


if __name__ == "__main__":
    unittest.main()
