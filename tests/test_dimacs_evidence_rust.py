"""R-012 exact DIMACS source-text evidence parser differential tests."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.dimacs import (
    DIMACSError, parse_dimacs_with_text_evidence,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustDimacsEvidence(unittest.TestCase):
    def test_1200_signed_text_stream_and_cnf_differentials(self):
        rng = random.Random(120122026)
        for n in range(1, 13):
            for _ in range(100):
                rows = []
                for _ in range(rng.randrange(13)):
                    raw = []
                    for _ in range(rng.randrange(6)):
                        v = rng.randrange(1, n + 1)
                        lit = v if rng.randrange(2) else -v
                        raw.append(rng.choice((
                            str(lit), f"{lit:+d}",
                            f"-{v:03d}" if lit < 0 else f"+{v:03d}",
                        )))
                    rows.append(raw)
                lines = [f"c source {n}", f"p cnf +{n:03d} {len(rows)}"]
                for row in rows:
                    lines.append(" ".join(row + [rng.choice(("0", "+0", "-0"))]))
                text = "\n".join(lines) + "\n"
                with self.subTest(n=n, source=text):
                    python = parse_dimacs_with_text_evidence(text)
                    rust = parse_dimacs_with_text_evidence(text, backend="rust")
                    self.assertEqual(python, rust)

    def test_missing_header_bad_literal_bad_count(self):
        for bad in (
            "", "c only a comment", "1 0", "p dnf 2 1\n1 0",
            "p cnf -1 0", "p cnf 2 2\n1 0",
            "p cnf 2 1\n3 0", "p cnf 2 1\n1",
            "p cnf 1 0\np cnf 1 0", "p cnf 1 1\nzero 0",
        ):
            with self.subTest(bad=bad):
                for backend in ("python", "rust"):
                    with self.assertRaises(DIMACSError):
                        parse_dimacs_with_text_evidence(bad, backend=backend)

    def test_literal_spellings_and_zero_terminator_evidence(self):
        doc = "c exact spellings\np cnf +04 3\n+01 -002 0 0\nc comment\n-0\n"
        py = parse_dimacs_with_text_evidence(doc)
        rust = parse_dimacs_with_text_evidence(doc, backend="rust")
        self.assertEqual(py, rust)
        self.assertEqual(rust[2], [1, -2, 0, 0, 0])
        self.assertEqual(rust[3], ["+01", "-002", "0", "0", "-0"])

    def test_unknown_backend_rejected(self):
        with self.assertRaises(DIMACSError):
            parse_dimacs_with_text_evidence("p cnf 0 0", backend="other")


if __name__ == "__main__":
    unittest.main()
