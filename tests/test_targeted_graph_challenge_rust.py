"""R-092: full native graph-theorem challenge differential gate."""
import unittest

from witnora_core.targeted_graph_theorems import challenge, evaluate

try:
    from witnora_ve import targeted_graph_challenge_native
except ImportError:
    targeted_graph_challenge_native = None


@unittest.skipUnless(targeted_graph_challenge_native is not None,
                     "native Rust wheel unavailable")
class TargetedGraphChallengeRust(unittest.TestCase):
    def test_three_bounded_experiments(self):
        for each in (1, 5, 20):
            with self.subTest(each=each):
                self.assertEqual(challenge(random_each=each),
                                 challenge(random_each=each, backend="rust"))

    def test_graph_property(self):
        edges = ((0, 1), (1, 2), (0, 2))
        self.assertEqual(evaluate(3, edges), evaluate(3, edges, backend="rust"))

    def test_bad_input(self):
        with self.assertRaises(ValueError):
            targeted_graph_challenge_native([("bad", 3, [(0, 3)])])


if __name__ == "__main__":
    unittest.main()
