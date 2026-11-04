"""R-028 parity for native certificate file integrity verifier and tampering."""
from __future__ import annotations

import os
from pathlib import Path
import random
import tempfile
import unittest

from witnora_core.proof import (
    certificate_bundle_file_hashes, first_certificate_file_hash_failure,
    verify_certificate_bundle,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustFileIntegrity(unittest.TestCase):
    def test_1200_randomized_missing_changed_and_correct_file_maps(self):
        rng = random.Random(280112026)
        for case in range(1200):
            files = {
                f"entry_{j}.txt": "".join(rng.choice("abé漢😀\n\t")
                                          for _ in range(rng.randrange(40)))
                for j in range(rng.randrange(1, 10))
            }
            expected = certificate_bundle_file_hashes(files)
            modified = dict(files)
            action = rng.randrange(3)
            name = rng.choice(list(modified))
            if action == 1:
                del modified[name]
            if action == 2:
                modified[name] += "tamper"
            original = first_certificate_file_hash_failure(expected, modified)
            native = first_certificate_file_hash_failure(
                expected, modified, backend="rust")
            with self.subTest(case=case, action=action):
                self.assertEqual(native, original)

    def test_real_good_bundles_and_changed_file_detection(self):
        from tests.test_certificate_export import run_export
        for name in ("bce_demo.dimacs", "unsat_demo.dimacs",
                     "multi_component_demo.dimacs"):
            with self.subTest(example=name), tempfile.TemporaryDirectory() as tmp:
                cert = Path(tmp) / "proof.wcert"
                code, _ = run_export(name, 2, cert)
                self.assertEqual(code, 0)
                good_py = verify_certificate_bundle(cert)
                good_rust = verify_certificate_bundle(
                    cert, file_hash_backend="rust")
                self.assertEqual(good_rust, good_py)
                self.assertTrue(good_rust["verified"], good_rust)

                file = cert / "certificate_hash.txt"
                file.write_text("0" * 64 + "\n", encoding="utf-8")
                bad_py = verify_certificate_bundle(cert)
                bad_rust = verify_certificate_bundle(
                    cert, file_hash_backend="rust")
                self.assertEqual(bad_rust, bad_py)
                self.assertFalse(bad_rust["verified"])
                self.assertEqual(bad_rust["failed_check"], "file_hash")

    def test_unknown_backend_and_direct_invalid_inputs(self):
        from witnora_ve import verify_certificate_file_digests_native
        with self.assertRaisesRegex(ValueError, "unknown"):
            first_certificate_file_hash_failure({}, {}, backend="unknown")
        with self.assertRaises(ValueError):
            verify_certificate_file_digests_native([], [("a", "x"), ("a", "y")])


if __name__ == "__main__":
    unittest.main()
