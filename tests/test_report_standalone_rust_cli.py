"""Standalone Rust report CLI and original Python CLI must emit identical bytes."""

from __future__ import annotations

import json
import os
from pathlib import Path
import random
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


RUST_BIN = os.environ.get("WITNORA_RUST_REPORT_BIN")


@unittest.skipUnless(RUST_BIN and Path(RUST_BIN).is_file(),
                     "standalone Rust binary built only in GitHub CI")
class StandaloneRustReportCliTests(unittest.TestCase):
    def compare_cli(self, data):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "benchmark.json"
            rust_output = root / "rust.md"
            python_output = root / "python.md"
            source.write_text(json.dumps(data, ensure_ascii=True), encoding="utf-8")
            python = subprocess.run([sys.executable, "-m", "witnora_core.report",
                str(source), "--out", str(python_output)], capture_output=True, text=True)
            self.assertEqual(python.returncode, 0, python.stderr)
            native = subprocess.run([RUST_BIN, str(source), "--out", str(rust_output)],
                                    capture_output=True, text=True)
            self.assertEqual(native.returncode, 0, native.stderr)
            self.assertEqual(rust_output.read_bytes(), python_output.read_bytes())

    def test_empty_report_cli(self):
        self.compare_cli({})

    def test_nontrivial_report_cli(self):
        self.compare_cli({"version": "v2", "c_parameter": 4,
                          "summary": {"solved_count": 2, "sat_count": 1},
                          "per_case_results": [{"case_name": "one", "solved_route": "NO_COLLAPSE",
                            "determinism_pass": False, "post_s_width_order_status": "SKIPPED_SIZE_CAP",
                            "original_num_vars": 4, "original_num_clauses": 12},
                            {"case_name": "two", "solved_route": "RUST", "num_bce_removed": 7}]})

    def test_seeded_cli_byte_parity(self):
        rng = random.Random(5042026)
        for index in range(24):
            rows = [{"case_name": f"case_{i}",
                     "solved_route": rng.choice(("NO_COLLAPSE", "RUST", "PYTHON")),
                     "determinism_pass": rng.choice((True, False, None)),
                     "original_num_vars": rng.randrange(20),
                     "num_vars_eliminated": rng.randrange(5),
                     "collapse_path_length": rng.randrange(8)}
                    for i in range(rng.randrange(1, 7))]
            self.compare_cli({"version": f"seed_{index}",
                              "summary": {"total_cases": len(rows)},
                              "per_case_results": rows})

    def test_flag_before_input_matches_python_argparse(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "benchmark.json"
            output = root / "report.md"
            source.write_text('{"version":"v4"}', encoding="utf-8")
            native = subprocess.run([RUST_BIN, "--out", str(output), str(source)],
                                    capture_output=True, text=True)
            self.assertEqual(native.returncode, 0, native.stderr)
            self.assertIn("# Witnora Benchmark Report", output.read_text())

    def test_help_does_not_create_report(self):
        native = subprocess.run([RUST_BIN, "--help"], capture_output=True, text=True)
        self.assertEqual(native.returncode, 0)
        self.assertIn("usage:", native.stdout)

    def test_invalid_json_fails_closed(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "bad.json"
            output = Path(tmp) / "bad.md"
            source.write_text("{broken", encoding="utf-8")
            native = subprocess.run([RUST_BIN, str(source), "--out", str(output)],
                                    capture_output=True, text=True)
            self.assertNotEqual(native.returncode, 0)
            self.assertFalse(output.exists())

    def test_missing_source_fails_closed(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "missing.json"
            output = Path(tmp) / "missing.md"
            native = subprocess.run([RUST_BIN, str(source), "--out", str(output)],
                                    capture_output=True, text=True)
            self.assertNotEqual(native.returncode, 0)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
