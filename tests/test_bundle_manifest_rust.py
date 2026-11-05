"""R-026 native bundle manifest hashes and complete certificate export parity."""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import random
import tempfile
import unittest

from witnora_core.dimacs import parse_dimacs
from witnora_core.proof import (
    certificate_bundle_file_hashes, collapse_path_from_result_dict,
    export_certificate_bundle, load_certificate_package, verify_certificate_bundle,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustBundleHashes(unittest.TestCase):
    def test_1200_randomized_exact_utf8_file_hash_maps(self):
        from witnora_ve import certificate_file_digests_native
        rng = random.Random(260112026)
        alphabet = "abcd😀é漢\r\n\t\\\x01"
        for case in range(1200):
            files = {
                f"proof_{i:03d}.json": "".join(rng.choice(alphabet)
                                               for _ in range(rng.randrange(120)))
                for i in range(rng.randrange(12))
            }
            got = certificate_bundle_file_hashes(files, backend="rust")
            expected = certificate_bundle_file_hashes(files)
            with self.subTest(case=case):
                self.assertEqual(got, expected)
                self.assertEqual(list(got), sorted(files))
                self.assertEqual(
                    got, {k: {"sha256": sha256(v.encode("utf-8")).hexdigest()}
                          for k, v in sorted(files.items())},
                )
                self.assertEqual(
                    dict(certificate_file_digests_native(list(files.items()))),
                    {k: v["sha256"] for k, v in expected.items()},
                )

    def test_reject_duplicate_and_bad_names(self):
        from witnora_ve import certificate_file_digests_native
        with self.assertRaises(ValueError):
            certificate_file_digests_native([("a", "x"), ("a", "y")])
        with self.assertRaises(ValueError):
            certificate_file_digests_native([("", "x")])
        with self.assertRaises(ValueError):
            certificate_file_digests_native([("bad\0name", "x")])
        with self.assertRaisesRegex(ValueError, "unknown"):
            certificate_bundle_file_hashes({}, backend="unknown")

    def test_real_sat_unsat_and_multicomponent_certificate_export(self):
        # Actual .wcert files go through the standard verifier and must be
        # byte-identical using Rust versus Python file-manifest hashes.
        from tests.test_certificate_export import run_export
        examples = Path(__file__).resolve().parents[1] / "examples"
        for name in ("bce_demo.dimacs", "unsat_demo.dimacs",
                     "multi_component_demo.dimacs"):
            with self.subTest(example=name), tempfile.TemporaryDirectory() as tmp:
                original_path = Path(tmp) / "original.wcert"
                code, _ = run_export(name, 2, original_path)
                self.assertEqual(code, 0)
                original_manifest, original_files = load_certificate_package(original_path)
                result = json.loads(original_files["result.json"])
                path = collapse_path_from_result_dict(result)
                formula = parse_dimacs((examples / name).read_text(encoding="utf-8"))
                rust_path = Path(tmp) / "rust.wcert"
                export_certificate_bundle(
                    formula, path, rust_path,
                    original_dimacs_text=(examples / name).read_text(encoding="utf-8"),
                    hash_backend="rust",
                )
                new_manifest, new_files = load_certificate_package(rust_path)
                self.assertEqual(new_manifest, original_manifest)
                self.assertEqual(new_files, original_files)
                self.assertTrue(verify_certificate_bundle(rust_path)["verified"])


if __name__ == "__main__":
    unittest.main()
