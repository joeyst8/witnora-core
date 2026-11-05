"""Native artifact SHA-256 and manifest lookup parity; not a proof verification test."""

from __future__ import annotations

import json
import os
from pathlib import Path
import random
import subprocess
from tempfile import TemporaryDirectory
import unittest

from witnora_core.verification_report import (
    _evidence_status, _manifest_lookup, parse_manifest_hash_table, sha256_file,
)


RUST_BIN = os.environ.get("WITNORA_RUST_EVIDENCE_CHECK_BIN")


@unittest.skipUnless(RUST_BIN and Path(RUST_BIN).is_file(),
                     "native artifact-integrity binary built only in GitHub CI")
class NativeArtifactIntegrityTests(unittest.TestCase):
    def run_native(self, *args):
        result = subprocess.run([RUST_BIN, *map(str, args)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_128_seeded_files_and_expected_hash_conditions(self):
        rng = random.Random(5102026)
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for trial in range(128):
                source = root / f"sample-{trial}.bin"
                source.write_bytes(rng.randbytes(rng.randrange(0, 3072)))
                actual = sha256_file(source)
                for expected in (None, actual, "F" * 64, actual.lower()):
                    cmd = ["check", str(source), "artifact"]
                    if expected is not None:
                        cmd.extend(["--expected", expected])
                    with self.subTest(trial=trial, expected=expected):
                        self.assertEqual(self.run_native(*cmd),
                                         _evidence_status(source, "artifact", expected))

    def test_large_file_and_missing_file(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "one-megabyte.bin"
            source.write_bytes(bytes(range(256)) * 4096)
            self.assertEqual(self.run_native("check", source, "source_zip"),
                             _evidence_status(source, "source_zip", None))
            missing = root / "not-present.bin"
            self.assertEqual(self.run_native("check", missing, "diagnostic_zip"),
                             _evidence_status(missing, "diagnostic_zip", None))

    def test_manifest_parser_and_lookup(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "proof.drat"
            target.write_text("0\n", encoding="utf-8")
            digest = sha256_file(target)
            source = ("| File | Hash | Note |\n"
                      f"| `proof.drat` | `{digest.lower()}` | expected |\n"
                      f"| `second.drat` | {digest} | expected |\n"
                      "  | `indented` | `" + digest + "` | not matched |\n"
                      "| `short` | 1234 | rejected |\n")
            manifest = root / "MANIFEST.md"
            manifest.write_text(source, encoding="utf-8")
            self.assertEqual(self.run_native("manifest", manifest),
                             parse_manifest_hash_table(source))
            expected = _manifest_lookup(target, parse_manifest_hash_table(source))
            self.assertEqual(self.run_native("check", target, "drat", "--manifest", manifest),
                             _evidence_status(target, "drat", expected))

    def test_malformed_input_does_not_create_output(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "result.json"
            missing = root / "missing-manifest.md"
            result = subprocess.run([RUST_BIN, "manifest", str(missing),
                                     "--out", str(output)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())

    def test_help(self):
        result = subprocess.run([RUST_BIN, "--help"], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn(b"usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
