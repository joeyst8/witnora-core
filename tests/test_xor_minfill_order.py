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
from witnora_core.xor_drat import _detected_equations, _sparse_xor_elimination_schedule


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
class XorMinFillOrderTest(unittest.TestCase):
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
        cls.detected = _detected_equations(cls.path)
        cls.verified_cert = cls.root / "tseitin15_minfill_verified.wcert"
        export_certificate_bundle(
            cls.formula,
            cls.path,
            cls.verified_cert,
            original_dimacs_text=cls.original_text,
            export_drat=True,
            export_xor_drat=True,
            drat_trim_path=cls.drat_trim,
            xor_elim_order="sparse-min-fill",
            xor_drat_max_row_width=8,
            xor_drat_max_proof_clauses=100000,
            xor_drat_max_proof_bytes=10_000_000,
            xor_drat_timeout_seconds=300,
        )
        cls.cap_cert = cls.root / "tseitin15_minfill_cap.wcert"
        export_certificate_bundle(
            cls.formula,
            cls.path,
            cls.cap_cert,
            original_dimacs_text=cls.original_text,
            export_drat=True,
            export_xor_drat=True,
            drat_trim_path=cls.drat_trim,
            xor_elim_order="sparse-min-fill",
            xor_drat_max_row_width=7,
            xor_drat_max_proof_clauses=100000,
            xor_drat_max_proof_bytes=10_000_000,
            xor_drat_timeout_seconds=300,
        )

    def test_minfill_order_determinism(self):
        first = _sparse_xor_elimination_schedule(self.detected)
        second = _sparse_xor_elimination_schedule(self.detected)
        self.assertEqual(first["elimination_order_variables"], second["elimination_order_variables"])
        self.assertEqual(first["row_operation_trace"], second["row_operation_trace"])
        print("XOR_MINFILL_ORDER_DETERMINISM_PASS")

    def test_minfill_trace_replay(self):
        checked = verify_wcert_raw(self.verified_cert)
        self.assertTrue(checked["verified"], checked)
        self.assertTrue(checked["checks"]["xor_elimination_trace_replayed"])
        self.assertTrue(checked["checks"]["xor_minfill_trace_replayed"])
        print("XOR_MINFILL_TRACE_REPLAY_PASS")

    def test_minfill_peak_width(self):
        status = json.loads((self.verified_cert / "xor_drat_status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["elimination_order_source"], "SPARSE_MIN_FILL")
        self.assertEqual(status["row_width_peak"], 8)
        self.assertEqual(status["peak_row_width"], 8)
        self.assertLessEqual(status["row_width_peak"], status["max_row_width_cap"])
        print("XOR_MINFILL_PEAK_WIDTH_PASS")

    def test_minfill_no_false_drat_claim(self):
        result = json.loads((self.cap_cert / "result.json").read_text(encoding="utf-8"))
        status = json.loads((self.cap_cert / "xor_drat_status.json").read_text(encoding="utf-8"))
        self.assertEqual(result["public_category"], UNSAT_XOR_NATIVE_ONLY)
        self.assertFalse(result["external_drat"])
        self.assertFalse(status["external_drat"])
        self.assertEqual(result["drat_claim"], "NOT_EXPORTED")
        print("XOR_MINFILL_NO_FALSE_DRAT_CLAIM_PASS")

    def test_minfill_proof_base_original(self):
        result = json.loads((self.verified_cert / "result.json").read_text(encoding="utf-8"))
        status = json.loads((self.verified_cert / "xor_drat_status.json").read_text(encoding="utf-8"))
        self.assertEqual(result["public_category"], UNSAT_DRAT_EXPORTED_VERIFIED)
        self.assertEqual(status["proof_base"], "original_cnf")
        self.assertTrue(status["external_drat"])
        print("XOR_MINFILL_PROOF_BASE_ORIGINAL_PASS")

    def test_minfill_cert_metadata(self):
        status = json.loads((self.verified_cert / "xor_drat_status.json").read_text(encoding="utf-8"))
        for key in [
            "elimination_order_source",
            "elimination_order_variables",
            "elimination_tie_break_rules",
            "row_operation_trace",
            "peak_row_width",
            "proof_clause_count_actual",
            "proof_file_size_bytes",
            "max_row_width_cap",
        ]:
            self.assertIn(key, status)
        self.assertEqual(status["elimination_order_source"], "SPARSE_MIN_FILL")
        self.assertTrue(status["row_operation_trace"])
        print("XOR_MINFILL_CERT_METADATA_PASS")

    def test_tseitin15_minfill_xor_drat_verified(self):
        result = json.loads((self.verified_cert / "result.json").read_text(encoding="utf-8"))
        status = json.loads((self.verified_cert / "xor_drat_status.json").read_text(encoding="utf-8"))
        self.assertEqual(result["public_category"], UNSAT_DRAT_EXPORTED_VERIFIED)
        self.assertEqual(status["xor_drat_status"], "VERIFIED")
        self.assertEqual(status["drat_trim_status"], "VERIFIED")
        self.assertTrue((self.verified_cert / "proof.drat").exists())
        checked = verify_wcert_raw(self.verified_cert)
        self.assertTrue(checked["verified"], checked)
        self.assertEqual(checked["public_category"], UNSAT_DRAT_EXPORTED_VERIFIED)
        print("TSEITIN_15_MINFILL_XOR_DRAT_VERIFIED_PASS")


if __name__ == "__main__":
    unittest.main()
