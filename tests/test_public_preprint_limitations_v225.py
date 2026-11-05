import unittest

from witnora_core.public_preprint_prep_v225 import (
    HARDENED_STATUS,
    REQUIRED_LIMITATIONS,
    public_preprint_text,
)


class PublicPreprintLimitationsV225Test(unittest.TestCase):
    def test_limitations_present(self):
        text = public_preprint_text()
        for limitation in REQUIRED_LIMITATIONS:
            self.assertIn(limitation, text)
        print("PUBLIC_PREPRINT_LIMITATIONS_PASS")

    def test_tc063_framing(self):
        text = public_preprint_text()
        self.assertIn("TC-063 status: " + HARDENED_STATUS, text)
        self.assertIn("Scope: SAF(c,r)", text)
        self.assertIn("G5 affine soundness is a dependency", text)
        print("PUBLIC_PREPRINT_TC063_FRAMING_PASS")

    def test_native_certificate_boundary(self):
        text = public_preprint_text()
        self.assertIn("Native Witnora certificates are not DRAT/LRAT/FRAT proofs unless explicitly exported and externally checked.", text)
        print("PUBLIC_PREPRINT_NATIVE_CERT_BOUNDARY_PASS")

    def test_finite_evidence_boundary(self):
        text = public_preprint_text()
        self.assertIn("Finite tests and scaling runs support implementation, not proof.", text)
        self.assertIn("External proof bridge is absent.", text)


if __name__ == "__main__":
    unittest.main()
