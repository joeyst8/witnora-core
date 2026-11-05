"""Native no-Python benchmark compare CLI: byte parity with original Python."""

from __future__ import annotations

import json
import os
from pathlib import Path
import random
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


RUST_BIN = os.environ.get("WITNORA_RUST_COMPARE_BIN")


@unittest.skipUnless(RUST_BIN and Path(RUST_BIN).is_file(),
                     "standalone Rust comparison binary built only in GitHub CI")
class StandaloneRustCompareCliTests(unittest.TestCase):
    def compare_cli(self, left: dict, right: dict) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            left_source = root / "left.json"
            right_source = root / "right.json"
            python_output = root / "python.md"
            rust_output = root / "rust.md"
            left_source.write_text(json.dumps(left), encoding="utf-8")
            right_source.write_text(json.dumps(right), encoding="utf-8")
            python = subprocess.run([sys.executable, "-m", "witnora_core.compare",
                str(left_source), str(right_source), "--out", str(python_output)],
                capture_output=True, text=True)
            self.assertEqual(python.returncode, 0, python.stderr)
            native = subprocess.run([RUST_BIN, str(left_source), str(right_source),
                "--out", str(rust_output)], capture_output=True, text=True)
            self.assertEqual(native.returncode, 0, native.stderr)
            self.assertEqual(rust_output.read_bytes(), python_output.read_bytes())

    def test_empty_and_nontrivial(self):
        self.compare_cli({}, {})
        self.compare_cli(
            {"version": "v1", "summary": {"solved_count": 7,
             "average_clause_reduction_pct": 42.125}, "per_case_results": [
             {"case_name": "a", "status": "SAT", "solved_route": "old"},
             {"case_name": "z", "status": "UNSAT", "solved_route": "X"}]},
            {"version": "v2", "summary": {"solved_count": 8,
             "average_clause_reduction_pct": 42.75}, "per_case_results": [
             {"case_name": "z", "status": "SAT", "solved_route": "Y"},
             {"case_name": "a", "status": "UNSAT", "solved_route": "X"}]})

    def test_128_seeded_byte_parity(self):
        rng = random.Random(5052026)
        for seed in range(128):
            left, right = [], []
            for i in range(rng.randrange(0, 9)):
                name = f"case_{i}"
                for rows in (left, right):
                    if rng.randrange(5) == 0:
                        continue
                    rows.append({"case_name": name, "status": rng.choice(
                        ("SAT", "UNSAT", "UNKNOWN", None)),
                        "solved_route": rng.choice(("RUST", "PYTHON", "NO_COLLAPSE", None))})
            summaries = []
            for side in range(2):
                summaries.append({"solved_count": rng.randrange(100),
                    "no_collapse_count": rng.randrange(25),
                    "average_collapse_path_length": rng.randrange(20) / 4,
                    "average_clause_reduction_pct": rng.randrange(101) / 2,
                    "certificate_hash_determinism_pass_rate": rng.randrange(101) / 100})
            self.compare_cli(
                {"version": f"seed_{seed}", "summary": summaries[0], "per_case_results": left},
                {"version": f"seed_{seed+1}", "summary": summaries[1], "per_case_results": right})

    def test_help_and_flag_order(self):
        help_result = subprocess.run([RUST_BIN, "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("usage:", help_result.stdout)
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            left = root / "left.json"
            right = root / "right.json"
            output = root / "out.md"
            left.write_text("{}", encoding="utf-8")
            right.write_text("{}", encoding="utf-8")
            native = subprocess.run([RUST_BIN, "--out", str(output), str(left), str(right)],
                capture_output=True, text=True)
            self.assertEqual(native.returncode, 0, native.stderr)
            self.assertIn("# Witnora Benchmark Comparison", output.read_text())

    def test_malformed_input_fails_closed(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = root / "bad.json"
            right = root / "right.json"
            output = root / "out.md"
            bad.write_text("{broken", encoding="utf-8")
            right.write_text("{}", encoding="utf-8")
            native = subprocess.run([RUST_BIN, str(bad), str(right), "--out", str(output)],
                capture_output=True, text=True)
            self.assertNotEqual(native.returncode, 0)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
