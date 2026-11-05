"""File-level claim-boundary Rust CLI agrees with the independent Python API."""

from __future__ import annotations

import json
import os
from pathlib import Path
import random
import subprocess
from tempfile import TemporaryDirectory
import unittest

from witnora_core.claim_boundary import (
    FORBIDDEN_AFFIRMATIVE_CLAIMS,
    NEGATIVE_CONTEXT_MARKERS,
    scan_files_for_claim_boundary,
)


RUST_BIN = os.environ.get("WITNORA_RUST_CLAIMS_BIN")


@unittest.skipUnless(RUST_BIN and Path(RUST_BIN).is_file(),
                     "standalone Rust claims binary built only in GitHub CI")
class StandaloneRustClaimsTests(unittest.TestCase):
    def run_case(self, contents: list[str]):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            paths = []
            for i, content in enumerate(contents):
                path = root / f"source {i}.txt"
                path.write_text(content, encoding="utf-8")
                paths.append(path)
            expected = scan_files_for_claim_boundary(paths)
            result = subprocess.run([RUST_BIN, *(str(p) for p in paths)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), expected)
            output = root / "claims.json"
            saved = subprocess.run([RUST_BIN, *(str(p) for p in paths),
                                    "--out", str(output)], capture_output=True, text=True)
            self.assertEqual(saved.returncode, 0, saved.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), expected)

    def test_nontrivial_file_aggregation(self):
        self.run_case([
            "Witnora solves SAT and claims state of the art performance.",
            "This work does not claim it solves SAT or P vs NP.",
            "HARD unknown UNKNOWN_1 \n\\t no full XOR extraction",
            "🚀🙂 local experiments avoid: competitive SAT solver",
            "No forbidden phrases occur here.",
        ])

    def test_128_seeded_file_differentials(self):
        rng = random.Random(5062026)
        words = ["Witnora", "bounded", "certificate", "🙂", "å", "ordinary",
                 "adjacent", "claims", "release", "text", "\n", "\t", "HARDENING"]
        for group in range(8):
            contents = []
            for _ in range(16):
                prefix = " ".join(rng.choices(words, k=rng.randrange(0, 18)))
                phrase = rng.choice(FORBIDDEN_AFFIRMATIVE_CLAIMS)
                suffix = " ".join(rng.choices(words, k=rng.randrange(0, 12)))
                if rng.randrange(3) == 0:
                    prefix += " " + rng.choice(NEGATIVE_CONTEXT_MARKERS)
                contents.append(prefix + " " + phrase + " " + suffix)
            with self.subTest(group=group):
                self.run_case(contents)

    def test_bad_inputs_are_fail_closed(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            missing = root / "not-present.txt"
            output = root / "claim-result.json"
            invalid = subprocess.run([RUST_BIN, str(missing), "--out", str(output)],
                                     capture_output=True, text=True)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertFalse(output.exists())
            raw = root / "non-utf8.txt"
            raw.write_bytes(bytes((0xff, 0xfe)))
            invalid_utf8 = subprocess.run([RUST_BIN, str(raw), "--out", str(output)],
                                          capture_output=True, text=True)
            self.assertNotEqual(invalid_utf8.returncode, 0)
            self.assertFalse(output.exists())

    def test_help(self):
        result = subprocess.run([RUST_BIN, "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
