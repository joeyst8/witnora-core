"""R-131: native exact XOR sidecar parsing and diagnostic errors."""
import random
import unittest

from witnora_core.xor import parse_xor_lines


class XorSidecarParserRustTests(unittest.TestCase):
    def test_seeded_multiline_sidecars(self):
        rng = random.Random(20261212)
        for trial in range(320):
            lines = ["# generated sidecar", "c witness"]
            for _ in range(rng.randrange(1, 15)):
                vars = [str(rng.randint(1, 400)) for _ in range(rng.randrange(1, 9))]
                lines.append("xor " + " ".join(vars) + " = " + str(rng.randrange(2)))
            with self.subTest(trial=trial):
                text = "\n".join(lines)
                self.assertEqual(parse_xor_lines(text, backend="rust"),
                                 parse_xor_lines(text))

    def test_malformed_rejected(self):
        for text in ("xor 1 = 2", "xor = 1", "no 1 2 = 0", "xor 1 = nope",
                     "xor -2 3 = 1", "xor 0 = 0"):
            for backend in ("python", "rust"):
                with self.subTest(text=text, backend=backend):
                    with self.assertRaises(ValueError):
                        parse_xor_lines(text, backend=backend)


if __name__ == "__main__":
    unittest.main()
