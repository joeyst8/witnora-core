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
from witnora_core.xor_drat import XOR_DRAT_SKIPPED_ROW_WIDTH_CAP
from witnora_core.xor_drat_diagnostic import DEFAULT_CAP_PROFILES


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
class TseitinXorDRATScalingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.drat_trim = real_drat_trim_path()
        cls.cnfgen = official_cnfgen_path()
        cls.root = Path(tempfile.mkdtemp())
        proc = subprocess.run(
            [cls.cnfgen, "--seed", "15", "tseitin", "15"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr)
        cls.original_text = proc.stdout
        cls.formula = parse_dimacs(cls.original_text)
        cls.path = solve_with_xor(cls.formula, c=2, detect_cnf_xor=True, detect_xor_max_k=6)
        cls.cap_cert = cls.root / "tseitin15_cap.wcert"
        export_certificate_bundle(
            cls.formula,
            cls.path,
            cls.cap_cert,
            original_dimacs_text=cls.original_text,
            export_drat=True,
            export_xor_drat=True,
            drat_trim_path=cls.drat_trim,
            xor_drat_max_row_width=8,
            xor_drat_max_proof_clauses=50000,
            xor_drat_max_proof_bytes=5_000_000,
            xor_drat_timeout_seconds=120,
        )

    def test_row_width_diagnostic(self):
        status = json.loads((self.cap_cert / "xor_drat_status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["xor_drat_status"], XOR_DRAT_SKIPPED_ROW_WIDTH_CAP)
        self.assertEqual(status["row_width"], 14)
        self.assertEqual(status["row_width_peak"], 14)
        self.assertEqual(status["row_width_initial"], 4)
        self.assertEqual(status["row_width_final_contradiction"], 0)
        self.assertIn("xor_elimination_order", status)
        self.assertNotIn("UNKNOWN", str(status.get("skip_reason")))
        print("TSEITIN_15_ROW_WIDTH_DIAGNOSTIC_PASS")

    def test_cap_sensitivity_profiles_are_recorded(self):
        self.assertEqual(DEFAULT_CAP_PROFILES["conservative"]["max_row_width"], 8)
        self.assertEqual(DEFAULT_CAP_PROFILES["medium"]["max_row_width"], 14)
        self.assertEqual(DEFAULT_CAP_PROFILES["medium"]["timeout_seconds"], 300.0)
        self.assertEqual(DEFAULT_CAP_PROFILES["high"]["max_row_width"], 16)
        self.assertEqual(DEFAULT_CAP_PROFILES["high"]["timeout_seconds"], 600.0)
        self.assertEqual(DEFAULT_CAP_PROFILES["diagnostic-high"]["max_row_width"], 18)
        self.assertEqual(DEFAULT_CAP_PROFILES["diagnostic-high"]["timeout_seconds"], 900.0)
        print("TSEITIN_15_CAP_SENSITIVITY_PASS")

    def test_no_false_drat_claim(self):
        result = json.loads((self.cap_cert / "result.json").read_text(encoding="utf-8"))
        status = json.loads((self.cap_cert / "xor_drat_status.json").read_text(encoding="utf-8"))
        self.assertEqual(result["public_category"], UNSAT_XOR_NATIVE_ONLY)
        self.assertFalse(result["external_drat"])
        self.assertFalse(status["external_drat"])
        self.assertEqual(result["drat_claim"], "NOT_EXPORTED")
        print("TSEITIN_15_NO_FALSE_DRAT_CLAIM_PASS")

    def test_proof_base_original_when_verified_only(self):
        result = json.loads((self.cap_cert / "result.json").read_text(encoding="utf-8"))
        status = json.loads((self.cap_cert / "xor_drat_status.json").read_text(encoding="utf-8"))
        if result["public_category"] == UNSAT_DRAT_EXPORTED_VERIFIED:
            self.assertEqual(status["proof_base"], "original_cnf")
        else:
            self.assertIsNone(status["proof_base"])
            self.assertFalse((self.cap_cert / "proof.drat").exists())
        print("TSEITIN_15_PROOF_BASE_ORIGINAL_PASS")

    def test_independent_checker_no_false_claim(self):
        checked = verify_wcert_raw(self.cap_cert)
        self.assertTrue(checked["verified"], checked)
        self.assertEqual(checked["public_category"], UNSAT_XOR_NATIVE_ONLY)
        self.assertFalse(checked["external_drat"])
        print("TSEITIN_15_INDEPENDENT_CHECKER_PASS")


if __name__ == "__main__":
    unittest.main()
