"""Strict public benchmark summary: native CLI agrees with Python's oracle."""

from __future__ import annotations

import json
import os
from pathlib import Path
import random
import subprocess
from tempfile import TemporaryDirectory
import unittest

from witnora_core.benchmark_artifact import strict_verification_summary


RUST_BIN = os.environ.get("WITNORA_RUST_ARTIFACT_SUMMARY_BIN")


@unittest.skipUnless(RUST_BIN and Path(RUST_BIN).is_file(),
                     "standalone Rust summary binary built only in GitHub CI")
class NativeArtifactSummaryCliTests(unittest.TestCase):
    def compare_cli(self, data):
        expected = strict_verification_summary(data)
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "public.json"
            output = root / "summary.json"
            source.write_text(json.dumps(data), encoding="utf-8")
            native = subprocess.run([RUST_BIN, str(source), "--out", str(output)],
                                    capture_output=True, text=True)
            self.assertEqual(native.returncode, 0, native.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), expected)
            piped = subprocess.run([RUST_BIN, str(source)],
                                   capture_output=True, text=True)
            self.assertEqual(piped.returncode, 0, piped.stderr)
            self.assertEqual(json.loads(piped.stdout), expected)

    def test_empty_and_uncertified_categories(self):
        self.compare_cli({})
        self.compare_cli({
            "strict_unsat_external_pass": False,
            "summary": {"unsat_total": 4, "externally_verified_unsat_count": 1,
                        "unverified_unsat_count": 1, "unsupported_drat_count": 1,
                        "xor_native_unsat_count": 1},
            "per_case_results": [
                {"instance_name": "verified", "public_category": "UNSAT_DRAT_EXPORTED_VERIFIED"},
                {"instance_name": "native-only", "public_category": "UNSAT_XOR_NATIVE_ONLY",
                 "external_checker_verified": True, "drat_export_status": "INCOMPLETE"},
                {"instance_name": "unverified", "public_category": "UNSAT_NOT_EXTERNALLY_VERIFIED"},
                {"instance_name": "unsupported", "public_category": "UNSUPPORTED_DRAT"},
            ],
        })

    def test_128_seeded_differential_cases(self):
        rng = random.Random(5072026)
        categories = ["SAT_MODEL_CHECKED", "NO_COLLAPSE", "UNSAT_DRAT_EXPORTED_VERIFIED",
                      "UNSAT_XOR_NATIVE_ONLY", "UNSUPPORTED_DRAT", "UNSAT_NOT_EXTERNALLY_VERIFIED"]
        for trial in range(128):
            rows = []
            for index in range(rng.randrange(0, 14)):
                category = rng.choice(categories)
                rows.append({"instance_name": f"seed{trial}_case{index}",
                             "public_category": category,
                             "external_checker_verified": rng.choice([False, True, None]),
                             "drat_export_status": rng.choice(["VALID", "SKIPPED", "FAILED"]),
                             "external_checker": rng.choice(["drat-trim", "none", None]),
                             "error_message": rng.choice(["", "not verified"])})
            summary = {key: rng.randrange(0, 20) for key in [
                "unsat_total", "externally_verified_unsat_count", "unverified_unsat_count",
                "unsupported_drat_count", "xor_native_unsat_count"]}
            with self.subTest(trial=trial):
                self.compare_cli({"summary": summary, "per_case_results": rows,
                    "strict_unsat_external_pass": rng.choice([True, False]),
                    "strict_unsat_external_failures": rng.sample(["a", "b", "c"],
                                                                rng.randrange(4))})

    def test_invalid_file_fails_closed(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "broken.json"
            target = root / "should-not-exist.json"
            source.write_text("{malformed", encoding="utf-8")
            result = subprocess.run([RUST_BIN, str(source), "--out", str(target)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(target.exists())

    def test_help(self):
        result = subprocess.run([RUST_BIN, "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
