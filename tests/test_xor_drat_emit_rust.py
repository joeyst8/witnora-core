"""R-141: proof clause emission and explicit cap errors match Python."""
import random
import unittest

from witnora_core.xor_drat import _emit_clause


class XorDratEmitRustTests(unittest.TestCase):
    def test_seeded_decisions_and_state(self):
        rng = random.Random(141)
        for trial in range(250):
            clause = tuple(rng.sample(range(-120, 120), rng.randrange(0, 8)))
            existing = tuple(rng.sample(range(-120, 120), rng.randrange(0, 8)))
            seed_active = {existing}
            if rng.randrange(3) == 0:
                seed_active.add(clause)
            caps = {"max_proof_clauses": rng.randrange(0, 6),
                    "max_proof_bytes": rng.randrange(0, 90)}
            emitted = rng.randrange(0, 6)
            proof_bytes = rng.randrange(0, 90)
            width = rng.randrange(0, 12)
            args = (emitted, proof_bytes, width)
            with self.subTest(trial=trial):
                left_lines, right_lines = [], []
                left_active, right_active = set(seed_active), set(seed_active)
                left = _emit_clause(clause, lines=left_lines, active=left_active,
                    emitted=args[0], proof_bytes=args[1], max_width=args[2],
                    **caps, backend="rust")
                right = _emit_clause(clause, lines=right_lines, active=right_active,
                    emitted=args[0], proof_bytes=args[1], max_width=args[2], **caps)
                self.assertEqual((left, left_lines, left_active),
                                 (right, right_lines, right_active))


if __name__ == "__main__":
    unittest.main()
