"""R-023 verify Rust BCE certificate SHA256 with the original Python representation."""
from __future__ import annotations

from hashlib import sha256
import os
import random
import unittest


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeBceDigest(unittest.TestCase):
    def test_1200_random_signed_proof_rows(self):
        from witnora_ve import blocked_clause_digest_native
        rng = random.Random(230112026)
        for _ in range(1200):
            rows = []
            for _ in range(rng.randrange(9)):
                other = [rng.randrange(-12, 13) for _ in range(rng.randrange(6))]
                resolvent = [rng.randrange(-12, 13) for _ in range(rng.randrange(9))]
                tautological = bool(rng.getrandbits(1))
                rows.append((other, resolvent, tautological))
            expected = sha256(repr(rows).encode("utf-8")).hexdigest()
            self.assertEqual(blocked_clause_digest_native(rows), expected)

    def test_canonical_examples(self):
        from witnora_ve import blocked_clause_digest_native
        for rows in ([], [([], [], True)],
                     [([-3, 1], [-1, 1, 2], True)]):
            self.assertEqual(blocked_clause_digest_native(rows),
                             sha256(repr(rows).encode("utf-8")).hexdigest())


if __name__ == "__main__":
    unittest.main()
