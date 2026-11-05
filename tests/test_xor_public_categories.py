import json
import os
import tempfile
import unittest
from pathlib import Path

from witnora_core.benchmark import enforce_unsat_external_verification
from witnora_core.certificate import XOR_UNSAT_NATIVE
from witnora_core.cnf import CNFFormula
from witnora_core.drat_trim import find_drat_trim
from witnora_core.independent_check import verify_wcert_raw
from witnora_core.proof import export_certificate_bundle
from witnora_core.public_benchmarks import (
    UNSAT_DRAT_EXPORTED_VERIFIED,
    UNSAT_XOR_NATIVE_ONLY,
    _category_for_result,
    summarize_public_results,
)
from witnora_core.runner import solve_with_xor
from witnora_core.xor import canonical_xor_cnf_clauses, parse_xor_lines


def real_drat_trim_path() -> str | None:
    configured = os.environ.get("WITNORA_DRAT_TRIM")
    found = find_drat_trim(configured)
    if found:
        return found
    fallback = r"C:\Users\maham\AppData\Local\Temp\witnora-drat-trim-real\drat-trim\drat-trim.exe"
    return find_drat_trim(fallback)


def xor_formula(equations):
    clauses = []
    for variables, rhs in equations:
        clauses.extend(canonical_xor_cnf_clauses(variables, rhs))
    return CNFFormula.from_raw_clauses(clauses)


class XorPublicCategoryTest(unittest.TestCase):
    def setUp(self):
        self.drat_trim = real_drat_trim_path()

    def require_real_drat_trim(self):
        if not self.drat_trim:
            self.skipTest("real drat-trim not available")
        return self.drat_trim

    def export_cert(self, formula, *, sidecar=None, export_xor_drat=True, drat_trim_path=None):
        path = solve_with_xor(
            formula,
            c=4,
            xor_system=sidecar,
            detect_cnf_xor=True,
            detect_xor_max_k=6,
        )
        cert_dir = Path(tempfile.mkdtemp()) / "category.wcert"
        export_certificate_bundle(
            formula,
            path,
            cert_dir,
            original_dimacs_text=formula.canonical_dimacs(),
            export_drat=True,
            export_xor_drat=export_xor_drat,
            drat_trim_path=drat_trim_path,
        )
        return path, cert_dir

    def test_xor_public_category_drat_verified(self):
        trim = self.require_real_drat_trim()
        formula = xor_formula([((1, 2), 0), ((2, 3), 0), ((1, 3), 1)])
        _path, cert = self.export_cert(formula, drat_trim_path=trim)
        result = json.loads((cert / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(result["status"], XOR_UNSAT_NATIVE)
        self.assertEqual(result["logical_status"], "UNSAT")
        self.assertEqual(result["discovery_route"], "XOR_NATIVE_CONTRADICTION")
        self.assertEqual(result["certification_level"], "EXTERNAL_DRAT_VERIFIED")
        self.assertEqual(result["public_category"], UNSAT_DRAT_EXPORTED_VERIFIED)
        self.assertTrue(result["external_drat"])
        self.assertEqual(result["drat_claim"], "EXPORTED_VERIFIED")
        self.assertEqual(result["proof_base"], "original_cnf")
        print("XOR_PUBLIC_CATEGORY_DRAT_VERIFIED_PASS")

    def test_xor_public_category_native_only(self):
        formula = xor_formula([((1, 2), 0), ((2, 3), 0), ((1, 3), 1)])
        _path, cert = self.export_cert(formula, export_xor_drat=False, drat_trim_path=self.drat_trim)
        result = json.loads((cert / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(result["logical_status"], "UNSAT")
        self.assertEqual(result["certification_level"], "NATIVE_XOR_ONLY")
        self.assertEqual(result["public_category"], UNSAT_XOR_NATIVE_ONLY)
        self.assertFalse(result["external_drat"])
        print("XOR_PUBLIC_CATEGORY_NATIVE_ONLY_PASS")

    def test_sidecar_not_original_cnf_unsat_category(self):
        trim = self.require_real_drat_trim()
        formula = CNFFormula()
        sidecar = parse_xor_lines("xor 1 = 0\nxor 1 = 1\n")
        _path, cert = self.export_cert(formula, sidecar=sidecar, drat_trim_path=trim)
        result = json.loads((cert / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(result["logical_status"], "UNSAT")
        self.assertEqual(result["discovery_route"], "XOR_SIDECAR_CONTRADICTION")
        self.assertEqual(result["certification_level"], "NATIVE_XOR_ONLY")
        self.assertEqual(result["public_category"], UNSAT_XOR_NATIVE_ONLY)
        self.assertFalse(result["external_drat"])
        self.assertNotEqual(result["public_category"], UNSAT_DRAT_EXPORTED_VERIFIED)
        print("XOR_SIDECAR_NOT_ORIGINAL_CNF_UNSAT_CATEGORY_PASS")

    def test_strict_benchmark_requires_drat(self):
        forged_unverified = {
            "drat_export_status": "EXPORTED",
            "external_checker": "DRAT_TRIM",
            "external_checker_ran": True,
            "external_checker_verified": False,
            "proof_base": "original_cnf",
            "drat_claim": "EXPORTED_VERIFIED",
        }
        category = _category_for_result(XOR_UNSAT_NATIVE, False, forged_unverified)
        self.assertEqual(category, UNSAT_XOR_NATIVE_ONLY)
        data = summarize_public_results(
            [
                {
                    "instance_name": "xor_unverified",
                    "status": "UNSAT",
                    "public_category": category,
                    "strict_unsat_external_pass": False,
                }
            ]
        )
        self.assertFalse(data["strict_unsat_external_pass"])
        with self.assertRaises(ValueError):
            enforce_unsat_external_verification("UNSAT", forged_unverified, strict=True)
        print("XOR_STRICT_BENCHMARK_REQUIRES_DRAT_PASS")

    def test_independent_checker_category(self):
        trim = self.require_real_drat_trim()
        formula = xor_formula([((1, 2), 0), ((2, 3), 0), ((1, 3), 1)])
        _path, cert = self.export_cert(formula, drat_trim_path=trim)
        checked = verify_wcert_raw(cert)
        self.assertTrue(checked["verified"])
        self.assertEqual(checked["status"], "UNSAT")
        self.assertEqual(checked["internal_status"], XOR_UNSAT_NATIVE)
        self.assertEqual(checked["discovery_route"], "XOR_NATIVE_CONTRADICTION")
        self.assertEqual(checked["certification_level"], "EXTERNAL_DRAT_VERIFIED")
        self.assertEqual(checked["public_category"], UNSAT_DRAT_EXPORTED_VERIFIED)
        self.assertTrue(checked["checks"]["xor_drat_exported_verified"])
        print("XOR_INDEPENDENT_CHECKER_CATEGORY_PASS")

    def test_no_ambiguous_xor_native_public_category(self):
        trim = self.require_real_drat_trim()
        formula = xor_formula([((1, 2), 0), ((2, 3), 0), ((1, 3), 1)])
        _path, cert = self.export_cert(formula, drat_trim_path=trim)
        result = json.loads((cert / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(result["public_category"], UNSAT_DRAT_EXPORTED_VERIFIED)
        self.assertNotEqual(result["public_category"], "UNSAT_XOR_NATIVE")
        self.assertNotEqual(result["public_category"], "UNSAT_XOR_NATIVE_NOT_DRAT")
        print("UNSAT_CATEGORY_NO_AMBIGUOUS_XOR_NATIVE_PASS")


if __name__ == "__main__":
    unittest.main()
