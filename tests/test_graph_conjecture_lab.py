"""Independent small graph known-value and falsification checks."""
import unittest

from witnora_core.graph_conjecture_lab import (
    graph_metrics, discover_conjectures, holds,
)


class GraphConjectureLabTests(unittest.TestCase):
    def test_known_graph_metrics(self):
        triangle = graph_metrics(3, ((0, 1), (0, 2), (1, 2)))
        self.assertEqual((triangle["omega"], triangle["chi"], triangle["tau"]),
                         (3, 3, 2))
        path = graph_metrics(4, ((0, 1), (1, 2), (2, 3)))
        self.assertEqual((path["alpha"], path["nu"], path["chi"]), (2, 2, 2))
        self.assertFalse(holds(("le", "m", "n", ""), graph_metrics(
            5, tuple((i, j) for i in range(5) for j in range(i + 1, 5)))))

    def test_finite_candidates_not_claimed_theorems(self):
        report = discover_conjectures(holdout_per_size=30)
        self.assertIn("omega <= chi", report["holdout_survivors"])
        self.assertIn("nu <= tau", report["holdout_survivors"])
        self.assertIn("alpha + tau = n", report["holdout_survivors"])
        self.assertFalse(report["lean_verified"])
        self.assertFalse(report["theorem_proven"])


if __name__ == "__main__":
    unittest.main()
