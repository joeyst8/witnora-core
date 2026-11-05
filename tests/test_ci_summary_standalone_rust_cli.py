"""Native Rust CI log renderer must match the Python formatting oracle bytewise."""

from __future__ import annotations

import json
import os
from pathlib import Path
import random
import subprocess
from tempfile import TemporaryDirectory
import unittest

from witnora_core.ci import render_ci_log_summary


RUST_BIN = os.environ.get("WITNORA_RUST_CI_SUMMARY_BIN")


@unittest.skipUnless(RUST_BIN and Path(RUST_BIN).is_file(),
                     "standalone Rust CI summary binary built only in GitHub CI")
class StandaloneRustCiSummaryTests(unittest.TestCase):
    def compare_cli(self, report, failure_reasons):
        expected = render_ci_log_summary(report, failure_reasons).encode("utf-8")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_path = root / "report.json"
            reasons_path = root / "reasons.json"
            output = root / "ci-summary.txt"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            reasons_path.write_text(json.dumps(failure_reasons), encoding="utf-8")
            native = subprocess.run([RUST_BIN, str(report_path), str(reasons_path),
                "--out", str(output)], capture_output=True)
            self.assertEqual(native.returncode, 0, native.stderr)
            self.assertEqual(output.read_bytes(), expected)
            native_stdout = subprocess.run([RUST_BIN, str(report_path), str(reasons_path)],
                capture_output=True)
            self.assertEqual(native_stdout.returncode, 0, native_stdout.stderr)
            self.assertEqual(native_stdout.stdout, expected)

    def test_empty_and_nontrivial(self):
        self.compare_cli({}, [])
        self.compare_cli({
            "verdict": "PARTIALLY_VERIFIED",
            "verification_depth": "partial",
            "replay_depth": None,
            "selected_evidence": [{"instance_id": "case 1", "c": 3,
                                   "public_category": "UNSAT_XOR_NATIVE_ONLY"},
                                  {"instance_id": "case-2", "c": None}],
            "risk_flags": ["UNVERIFIED_CLAIM", "MISSING_FILE"],
            "checks_performed": [{"name": f"check_{i}"} for i in range(15)],
        }, ["missing_file", "partial_or_not_verified"])

    def test_128_seeded_byte_parity(self):
        rng = random.Random(5082026)
        verdicts = ["VERIFIED", "PARTIAL_REPLAY_VERIFIED", "OVERCLAIM", None]
        for trial in range(128):
            report = {"verdict": rng.choice(verdicts),
                      "verification_depth": rng.choice(["metadata", "partial", "full"]),
                      "replay_depth": rng.choice([None, "metadata", "partial"]),
                      "selected_evidence": [{"instance_id": f"case_{i}",
                          "c": rng.choice([None, 0, 1, 2, 3]),
                          "public_category": rng.choice(["SAT_MODEL_CHECKED",
                              "UNSAT_DRAT_EXPORTED_VERIFIED", None])}
                          for i in range(rng.randrange(0, 8))],
                      "risk_flags": [rng.choice(["OVERCLAIM", "MISSING_FILE",
                          "UNVERIFIED_CLAIM", "🙂", None])
                          for _ in range(rng.randrange(0, 5))],
                      "checks_performed": [{"name": f"check_{i}"}
                          for i in range(rng.randrange(0, 22))]}
            reasons = [rng.choice(["hash_mismatch", "overclaim", "missing_file",
                                   "partial_or_not_verified"])
                       for _ in range(rng.randrange(0, 6))]
            with self.subTest(trial=trial):
                self.compare_cli(report, reasons)

    def test_errors_do_not_create_output(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = root / "bad.json"
            reasons = root / "reasons.json"
            output = root / "never.txt"
            bad.write_text("{malformed", encoding="utf-8")
            reasons.write_text("[]", encoding="utf-8")
            native = subprocess.run([RUST_BIN, str(bad), str(reasons),
                "--out", str(output)], capture_output=True)
            self.assertNotEqual(native.returncode, 0)
            self.assertFalse(output.exists())

    def test_help_and_flag_order(self):
        help_result = subprocess.run([RUST_BIN, "--help"], capture_output=True)
        self.assertEqual(help_result.returncode, 0)
        self.assertIn(b"usage:", help_result.stdout)
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_path = root / "report.json"
            reasons_path = root / "reasons.json"
            output = root / "summary.txt"
            report_path.write_text("{}", encoding="utf-8")
            reasons_path.write_text("[]", encoding="utf-8")
            native = subprocess.run([RUST_BIN, "--out", str(output),
                str(report_path), str(reasons_path)], capture_output=True)
            self.assertEqual(native.returncode, 0, native.stderr)
            self.assertTrue(output.read_text().startswith("Witnora Verify CI Summary"))


if __name__ == "__main__":
    unittest.main()
