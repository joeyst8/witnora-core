"""R-025 stable JSON byte-for-byte and SHA-256 parity for strict certificate subset."""
from __future__ import annotations

from hashlib import sha256
import os
import random
import unittest

from witnora_core.proof import stable_json


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeStableJson(unittest.TestCase):
    def test_1600_nested_randomized_certificate_values(self):
        from witnora_ve import stable_certificate_json_native
        rng = random.Random(250112026)
        alphabet = "aAzZ0_:/漢é😀\n\r\t\\\"\x01"
        def scalar():
            choice = rng.randrange(6)
            if choice == 0:
                return None
            if choice == 1:
                return bool(rng.getrandbits(1))
            if choice in (2, 3):
                return rng.randrange(-(1 << 45), 1 << 45)
            return "".join(rng.choice(alphabet) for _ in range(rng.randrange(14)))

        def generate(depth):
            if depth >= 4 or rng.randrange(5) < 2:
                return scalar()
            choice = rng.randrange(3)
            if choice == 0:
                return [generate(depth + 1) for _ in range(rng.randrange(5))]
            if choice == 1:
                return tuple(generate(depth + 1) for _ in range(rng.randrange(4)))
            return {
                "".join(rng.choice(alphabet) for _ in range(rng.randrange(8))): generate(depth + 1)
                for _ in range(rng.randrange(5))
            }

        for i in range(1600):
            payload = generate(0)
            expected = stable_json(payload)
            native, digest = stable_certificate_json_native(payload)
            with self.subTest(case=i, payload=payload):
                self.assertEqual(native, expected)
                self.assertEqual(stable_json(payload, backend="rust"), expected)
                self.assertEqual(digest, sha256(expected.encode("utf-8")).hexdigest())

    def test_stable_complete_step_record_and_empty_containers(self):
        from witnora_ve import stable_certificate_json_native
        for source in (
            {}, [], ["text", True, None, {"z": [1, -8], "a": "é"}],
            {"step_id": 1, "type": "VE", "details": {"status": "SAT"},
             "removed_clauses": [], "added_clauses": [[1]], "assigned_literals": [1]},
        ):
            expected = stable_json(source)
            native, digest = stable_certificate_json_native(source)
            self.assertEqual(native, expected)
            self.assertEqual(digest, sha256(expected.encode()).hexdigest())

    def test_unsupported_types_fail_closed(self):
        from witnora_ve import stable_certificate_json_native
        with self.assertRaises(ValueError):
            stable_certificate_json_native({"float": 1.5})
        with self.assertRaises(ValueError):
            stable_certificate_json_native({"bad": {1: "nonstring-key"}})
        with self.assertRaises(ValueError):
            stable_certificate_json_native({"oversize": 1 << 90})
        with self.assertRaisesRegex(ValueError, "unknown"):
            stable_json({}, backend="unrecognized")


if __name__ == "__main__":
    unittest.main()
