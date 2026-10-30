"""Known graph controls, independent finite-bound checks."""
import unittest

from witnora_core.targeted_graph_theorems import (
    challenge, evaluate, mycielski_c5, special_graphs,
)


class TargetedGraphTheoremsTests(unittest.TestCase):
    def test_known_nonperfect_graph(self):
        n, edges = mycielski_c5()
        first, second, values = evaluate(n, edges)
        self.assertEqual((values["omega"], values["chi"]), (2, 4))
        self.assertTrue(first)
        self.assertTrue(second)

    def test_special_families(self):
        for _, n, edges in special_graphs():
            first, second, _ = evaluate(n, edges)
            self.assertTrue(first)
            self.assertTrue(second)

    def test_claims_remain_unproved(self):
        report = challenge(random_each=5)
        self.assertEqual(report["lean_status"], "NOT_FORMALIZED")
        self.assertFalse(report["theorem_proven"])


if __name__ == "__main__":
    unittest.main()
