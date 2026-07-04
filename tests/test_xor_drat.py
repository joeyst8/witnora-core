import json
import os
import tempfile
import unittest
from pathlib import Path

from witnora_core.cnf import CNFFormula
from witnora_core.drat_trim import find_drat_trim
from witnora_core.independent_check import verify_wcert_raw
from witnora_core.proof import export_certificate_bundle
from witnora_core.public_benchmarks import UNSAT_XOR_NATIVE_NOT_DRAT, _category_for_result
from witnora_core.runner import solve_with_xor
from witnora_core.xor import canonical_xor_cnf_clauses, parse_xor_lines
from witnora_core.xor_drat import (
    XOR_DRAT_NOT_RUN_NO_DRAT_TRIM,
    XOR_DRAT_UNSUPPORTED_SIDECAR_ORIGINAL_CNF,
    XOR_DRAT_VERIFIED,
)


def real_drat_trim_path() -> str | None:
    known = os.environ.get("WITNORA_DRAT_TRIM")
    found = find_drat_trim(known)
    if found:
        return found
    fallback = r"C:\Users\maham\AppData\Local\Temp\witnora-drat-trim-real\drat-trim\drat-trim.exe"
    return find_drat_trim(fallback)


def xor_formula(equations):
    clauses = []
    for variables, rhs in equations:
        clauses.extend(canonical_xor_cnf_clauses(variables, rhs))
    return CNFFormula.from_raw_clauses(clauses)


class XorDRATTest(unittest.TestCase):
    def setUp(self):
        self.drat_trim = real_drat_trim_path()

    def require_real_drat_trim(self):
        if not self.drat_trim:
            self.skipTest("real drat-trim not available")
        return self.drat_trim

    def export_xor_cert(self, formula, *, drat_trim_path=None, export_xor_drat=True, max_row_width=8):
        path = solve_with_xor(formula, c=4, detect_cnf_xor=True, detect_xor_max_k=6)
        cert_dir = Path(tempfile.mkdtemp()) / "xor_drat.wcert"
        export_certificate_bundle(
            formula,
            path,
            cert_dir,
            original_dimacs_text=formula.canonical_dimacs(),
            export_drat=True,
            export_xor_drat=export_xor_drat,
            drat_trim_path=drat_trim_path,
            xor_drat_max_row_width=max_row_width,
        )
        return path, cert_dir

    def assert_verified_xor_drat(self, cert_dir):
        xor_drat = json.loads((cert_dir / "xor_drat_status.json").read_text(encoding="utf-8"))
        drat_status = json.loads((cert_dir / "drat_status.json").read_text(encoding="utf-8"))
        self.assertEqual(xor_drat["xor_drat_status"], XOR_DRAT_VERIFIED)
        self.assertTrue(xor_drat["external_drat"])
        self.assertEqual(xor_drat["drat_claim"], "EXPORTED_VERIFIED")
        self.assertEqual(xor_drat["proof_base"], "original_cnf")
        self.assertEqual(xor_drat["source"], "detected_cnf_pattern")
        self.assertTrue((cert_dir / "proof.drat").exists())
        self.assertEqual(drat_status["external_checker"], "DRAT_TRIM")
        self.assertTrue(drat_status["external_checker_ran"])
        self.assertTrue(drat_status["external_checker_verified"])
        return xor_drat, drat_status

    def test_detected_k2_xor_drat(self):
        trim = self.require_real_drat_trim()
        formula = xor_formula([((1, 2), 0), ((2, 3), 0), ((1, 3), 1)])
        _path, cert = self.export_xor_cert(formula, drat_trim_path=trim)
        self.assert_verified_xor_drat(cert)
        print("XOR_DRAT_DETECTED_K2_UNSAT_PASS")

    def test_detected_k3_xor_drat(self):
        trim = self.require_real_drat_trim()
        formula = xor_formula([((1, 2, 3), 0), ((1, 2, 4), 0), ((3, 4), 1)])
        _path, cert = self.export_xor_cert(formula, drat_trim_path=trim)
        self.assert_verified_xor_drat(cert)
        print("XOR_DRAT_DETECTED_K3_UNSAT_PASS")

    def test_detected_k4_xor_drat_or_cap_skip(self):
        trim = self.require_real_drat_trim()
        formula = xor_formula([((1, 2, 3, 4), 0), ((1, 2, 3, 5), 0), ((4, 5), 1)])
        _path, cert = self.export_xor_cert(formula, drat_trim_path=trim)
        xor_drat = json.loads((cert / "xor_drat_status.json").read_text(encoding="utf-8"))
        if xor_drat["xor_drat_status"] == XOR_DRAT_VERIFIED:
            self.assert_verified_xor_drat(cert)
            print("XOR_DRAT_DETECTED_K4_UNSAT_PASS")
        else:
            self.assertIn(xor_drat["xor_drat_status"], {"SKIPPED_ROW_WIDTH_CAP", "SKIPPED_PROOF_SIZE_CAP"})
            self.assertFalse((cert / "proof.drat").exists())
            print("XOR_DRAT_DETECTED_K4_SKIPPED_CAP_PASS")

    def test_no_false_claim_when_disabled(self):
        formula = xor_formula([((1, 2), 0), ((2, 3), 0), ((1, 3), 1)])
        path, cert = self.export_xor_cert(formula, drat_trim_path=self.drat_trim, export_xor_drat=False)
        xor_status = json.loads((cert / "xor_status.json").read_text(encoding="utf-8"))
        drat_status = json.loads((cert / "drat_status.json").read_text(encoding="utf-8"))
        self.assertFalse(xor_status["external_drat"])
        self.assertEqual(xor_status["drat_claim"], "NOT_EXPORTED")
        self.assertEqual(_category_for_result(path.status, False, drat_status), UNSAT_XOR_NATIVE_NOT_DRAT)
        print("XOR_DRAT_NO_FALSE_CLAIM_PASS")

    def test_sidecar_no_original_cnf_claim(self):
        trim = self.require_real_drat_trim()
        formula = CNFFormula()
        sidecar = parse_xor_lines("xor 1 = 0\nxor 1 = 1\n")
        path = solve_with_xor(formula, c=2, xor_system=sidecar)
        cert = Path(tempfile.mkdtemp()) / "sidecar.wcert"
        export_certificate_bundle(
            formula,
            path,
            cert,
            original_dimacs_text=formula.canonical_dimacs(),
            export_drat=True,
            export_xor_drat=True,
            drat_trim_path=trim,
        )
        xor_drat = json.loads((cert / "xor_drat_status.json").read_text(encoding="utf-8"))
        self.assertEqual(xor_drat["xor_drat_status"], XOR_DRAT_UNSUPPORTED_SIDECAR_ORIGINAL_CNF)
        self.assertFalse(xor_drat["external_drat"])
        self.assertIsNone(xor_drat["proof_base"])
        self.assertFalse((cert / "proof.drat").exists())
        print("XOR_DRAT_SIDECAR_NO_ORIGINAL_CNF_CLAIM_PASS")

    def test_drat_trim_required(self):
        formula = xor_formula([((1, 2), 0), ((2, 3), 0), ((1, 3), 1)])
        _path, cert = self.export_xor_cert(formula, drat_trim_path=None)
        xor_drat = json.loads((cert / "xor_drat_status.json").read_text(encoding="utf-8"))
        self.assertEqual(xor_drat["xor_drat_status"], XOR_DRAT_NOT_RUN_NO_DRAT_TRIM)
        self.assertFalse(xor_drat["external_drat"])
        self.assertFalse((cert / "proof.drat").exists())
        print("XOR_DRAT_TRIM_REQUIRED_PASS")

    def test_cert_metadata(self):
        trim = self.require_real_drat_trim()
        formula = xor_formula([((1, 2), 0), ((2, 3), 0), ((1, 3), 1)])
        _path, cert = self.export_xor_cert(formula, drat_trim_path=trim)
        manifest = json.loads((cert / "manifest.json").read_text(encoding="utf-8"))
        result = json.loads((cert / "result.json").read_text(encoding="utf-8"))
        self.assertTrue((cert / "xor_drat_status.json").exists())
        self.assertTrue(manifest["external_drat"])
        self.assertEqual(result["unsat_certification_level"], "EXTERNAL_DRAT_LRAT_FRAT_VERIFIED")
        self.assertEqual(result["xor_data"]["xor_status"]["drat_claim"], "EXPORTED_VERIFIED")
        print("XOR_DRAT_CERT_METADATA_PASS")

    def test_independent_checker(self):
        trim = self.require_real_drat_trim()
        formula = xor_formula([((1, 2), 0), ((2, 3), 0), ((1, 3), 1)])
        _path, cert = self.export_xor_cert(formula, drat_trim_path=trim)
        result = verify_wcert_raw(cert)
        self.assertTrue(result["verified"])
        self.assertTrue(result["checks"]["xor_drat_exported_verified"])
        print("XOR_DRAT_INDEPENDENT_CHECKER_PASS")


if __name__ == "__main__":
    unittest.main()
