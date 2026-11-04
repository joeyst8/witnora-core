"""R-080 forbidden-claim scanner exact Python/Rust differential gate."""
import random
import tempfile
import unittest
from pathlib import Path

from witnora_core.claim_boundary import (
    FORBIDDEN_AFFIRMATIVE_CLAIMS, NEGATIVE_CONTEXT_MARKERS,
    scan_text_for_claim_boundary, scan_files_for_claim_boundary,
)


class ClaimBoundaryRustTests(unittest.TestCase):
    def setUp(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")

    def test_240_seeded_contexts(self):
        rng = random.Random(80080)
        vocabulary = ["Witnora", "may", "produce", "this", "example", "🙂", "å",
                      "theoretical", "evidence", "report", "scope", "clear", "\n", "\t"]
        for trial in range(240):
            before = " ".join(rng.choices(vocabulary, k=rng.randrange(0, 80)))
            phrase = rng.choice(FORBIDDEN_AFFIRMATIVE_CLAIMS)
            if rng.randrange(4) == 0:
                before += " " + rng.choice(NEGATIVE_CONTEXT_MARKERS)
            after = " ".join(rng.choices(vocabulary, k=rng.randrange(0, 35)))
            text = before + " " + phrase + " " + after
            with self.subTest(trial=trial):
                self.assertEqual(scan_text_for_claim_boundary(text, backend="rust"),
                                 scan_text_for_claim_boundary(text))

    def test_special_boundaries_and_file_aggregation(self):
        samples = ["HARD HARDENING UNKNOWN UNKNOWN_1",
                   "hard Hard HARD _HARD_ UNKNOWN, HARD!",
                   "Witnora does not claim it solves SAT or solves parity.",
                   "🚀\n\tP vs NP 0" , "state of the art " * 8,
                   "never claims competitive SAT solver status"]
        for sample in samples:
            self.assertEqual(scan_text_for_claim_boundary(sample, backend="rust"),
                             scan_text_for_claim_boundary(sample))
        with tempfile.TemporaryDirectory() as folder:
            paths = []
            for i, sample in enumerate(samples):
                path = Path(folder) / f"sample{i}.txt"
                path.write_text(sample, encoding="utf-8")
                paths.append(path)
            self.assertEqual(scan_files_for_claim_boundary(paths, backend="rust"),
                             scan_files_for_claim_boundary(paths))


if __name__ == "__main__":
    unittest.main()
