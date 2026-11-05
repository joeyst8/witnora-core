"""R-027 exact compact certificate identity hash differential and real-path tests."""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import random
import tempfile
import unittest

from witnora_core.proof import collapse_path_from_result_dict, load_certificate_package


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeCertificateHash(unittest.TestCase):
    def test_1200_randomized_nested_compact_json_and_sha256(self):
        from witnora_ve import compact_certificate_hash_native
        rng = random.Random(270112026)
        alphabet = "abcd漢é😀\r\n\t\\\"\x01"

        def make(depth=0):
            choice = rng.randrange(6 if depth < 4 else 3)
            if choice == 0:
                return None
            if choice == 1:
                return bool(rng.getrandbits(1))
            if choice == 2:
                return rng.randrange(-(1 << 45), 1 << 45)
            if choice == 3:
                return "".join(rng.choice(alphabet) for _ in range(rng.randrange(12)))
            if choice == 4:
                return [make(depth + 1) for _ in range(rng.randrange(5))]
            return {
                "".join(rng.choice(alphabet) for _ in range(rng.randrange(8))):
                make(depth + 1) for _ in range(rng.randrange(5))
            }

        for case in range(1200):
            value = make()
            text = json.dumps(value, sort_keys=True, separators=(",", ":"))
            got, digest = compact_certificate_hash_native(value)
            with self.subTest(case=case):
                self.assertEqual(got, text)
                self.assertEqual(digest, sha256(text.encode("utf-8")).hexdigest())

    def test_real_sat_unsat_and_components_identity_hashes(self):
        from tests.test_certificate_export import run_export
        for name in ("bce_demo.dimacs", "unsat_demo.dimacs",
                     "multi_component_demo.dimacs"):
            with self.subTest(example=name), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "reference.wcert"
                code, _ = run_export(name, 2, path)
                self.assertEqual(code, 0)
                _, files = load_certificate_package(path)
                result = json.loads(files["result.json"])
                collapse = collapse_path_from_result_dict(result)
                self.assertEqual(collapse.certificate_hash_with_backend(backend="rust"),
                                 collapse.certificate_hash)
                self.assertEqual(collapse.certificate_hash,
                                 result["certificate_hash"])

    def test_unsupported_types_rejected(self):
        from witnora_ve import compact_certificate_hash_native
        for value in ({"float": 1.1}, {12: "not-string-key"},
                      {"giant": 1 << 90}):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    compact_certificate_hash_native(value)


if __name__ == "__main__":
    unittest.main()
