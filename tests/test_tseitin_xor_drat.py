import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from witnora_core.dimacs import parse_dimacs
from witnora_core.drat_trim import find_drat_trim
from witnora_core.independent_check import verify_wcert_raw
from witnora_core.proof import export_certificate_bundle
from witnora_core.public_benchmarks import UNSAT_DRAT_EXPORTED_VERIFIED, UNSAT_XOR_NATIVE_ONLY, find_cnfgen_cli
from witnora_core.runner import solve_with_xor
from witnora_core.xor_drat import XOR_DRAT_SKIPPED_ROW_WIDTH_CAP, XOR_DRAT_VERIFIED


def real_drat_trim_path() -> str | None:
    configured = os.environ.get("WITNORA_DRAT_TRIM")
    found = find_drat_trim(configured)
    if found:
        return found
    fallback = r"C:\Users\maham\AppData\Local\Temp\witnora-drat-trim-real\drat-trim\drat-trim.exe"
    return find_drat_trim(fallback)


def official_cnfgen_path() -> str | None:
    fallback = r"C:\Users\maham\AppData\Local\hermes\hermes-agent\venv\Scripts\cnfgen.exe"
    return find_cnfgen_cli(fallback)


@unittest.skipUnless(real_drat_trim_path() and official_cnfgen_path(), "real drat-trim and official CNFgen required")
class TseitinXorDRATTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.drat_trim = real_drat_trim_path()
        cls.cnfgen = official_cnfgen_path()
        cls.root = Path(tempfile.mkdtemp())
        proc = subprocess.run(
            [cls.cnfgen, "--seed", "10", "tseitin", "10"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr)
        cls.original_text = proc.stdout
        cls.formula = parse_dimacs(cls.original_text)
        cls.path = solve_with_xor(cls.formula, c=2, detect_cnf_xor=True, detect_xor_max_k=6)
        cls.verified_cert = cls.root / "tseitin10_verified.wcert"
        export_certificate_bundle(
            cls.formula,
            cls.path,
            cls.verified_cert,
            original_dimacs_text=cls.original_text,
            export_drat=True,
            export_xor_drat=True,
            drat_trim_path=cls.drat_trim,
            xor_drat_max_row_width=8,
            xor_drat_max_proof_clauses=50000,
            xor_drat_max_proof_bytes=5_000_000,
            xor_drat_timeout_seconds=120,
        )
        cls.cap_cert = cls.root / "tseitin10_cap.wcert"
        export_certificate_bundle(
            cls.formula,
            cls.path,
            cls.cap_cert,
            original_dimacs_text=cls.original_text,
            export_drat=True,
            export_xor_drat=True,
            drat_trim_path=cls.drat_trim,
            xor_drat_max_row_width=4,
            xor_drat_max_proof_clauses=50000,
            xor_drat_max_proof_bytes=5_000_000,
            xor_drat_timeout_seconds=120,
        )

    def test_skip_reason_explicit(self):
        xor_drat = json.loads((self.cap_cert / "xor_drat_status.json").read_text(encoding="utf-8"))
        self.assertEqual(xor_drat["xor_drat_status"], XOR_DRAT_SKIPPED_ROW_WIDTH_CAP)
        self.assertEqual(xor_drat["skip_reason"], xor_drat["reason"])
        self.assertNotIn("UNKNOWN", str(xor_drat.get("skip_reason")))
        self.assertEqual(xor_drat["row_width"], 8)
        print("TSEITIN_XOR_DRAT_SKIP_REASON_PASS")

    def test_tseitin10_verified(self):
        result = json.loads((self.verified_cert / "result.json").read_text(encoding="utf-8"))
        xor_drat = json.loads((self.verified_cert / "xor_drat_status.json").read_text(encoding="utf-8"))
        self.assertEqual(result["public_category"], UNSAT_DRAT_EXPORTED_VERIFIED)
        self.assertEqual(xor_drat["xor_drat_status"], XOR_DRAT_VERIFIED)
        self.assertTrue(xor_drat["external_drat"])
        self.assertTrue((self.verified_cert / "proof.drat").exists())
        print("TSEITIN_10_XOR_DRAT_VERIFIED_PASS")

    def test_no_false_claim_on_skip(self):
        result = json.loads((self.cap_cert / "result.json").read_text(encoding="utf-8"))
        xor_drat = json.loads((self.cap_cert / "xor_drat_status.json").read_text(encoding="utf-8"))
        self.assertEqual(result["public_category"], UNSAT_XOR_NATIVE_ONLY)
        self.assertFalse(result["external_drat"])
        self.assertEqual(result["drat_claim"], "NOT_EXPORTED")
        self.assertFalse(xor_drat["external_drat"])
        print("TSEITIN_XOR_DRAT_NO_FALSE_CLAIM_PASS")

    def test_proof_base_original(self):
        xor_drat = json.loads((self.verified_cert / "xor_drat_status.json").read_text(encoding="utf-8"))
        drat_status = json.loads((self.verified_cert / "drat_status.json").read_text(encoding="utf-8"))
        self.assertEqual(xor_drat["proof_base"], "original_cnf")
        self.assertEqual(drat_status["checked_against"], "original.dimacs")
        self.assertEqual(drat_status["proof_scope"], "END_TO_END_FROM_ORIGINAL_CNF")
        print("TSEITIN_XOR_DRAT_PROOF_BASE_ORIGINAL_PASS")

    def test_cap_metadata_present(self):
        xor_drat = json.loads((self.verified_cert / "xor_drat_status.json").read_text(encoding="utf-8"))
        required = [
            "row_width",
            "max_row_width_cap",
            "proof_clause_count_estimate",
            "proof_clause_count_actual",
            "max_proof_clause_cap",
            "internal_rup_status",
            "drat_trim_status",
            "drat_trim_runtime_seconds",
            "proof_file_size_bytes",
            "original_num_vars",
            "original_num_clauses",
            "detected_xor_equations",
            "max_detected_xor_arity",
        ]
        for key in required:
            self.assertIn(key, xor_drat)
        self.assertEqual(xor_drat["proof_file_size_bytes"], (self.verified_cert / "proof.drat").stat().st_size)
        print("TSEITIN_XOR_DRAT_CAP_METADATA_PASS")

    def test_independent_checker(self):
        checked = verify_wcert_raw(self.verified_cert)
        self.assertTrue(checked["verified"], checked)
        self.assertEqual(checked["public_category"], UNSAT_DRAT_EXPORTED_VERIFIED)
        self.assertTrue(checked["checks"]["xor_drat_exported_verified"])
        print("TSEITIN_XOR_DRAT_INDEPENDENT_CHECKER_PASS")


if __name__ == "__main__":
    unittest.main()
