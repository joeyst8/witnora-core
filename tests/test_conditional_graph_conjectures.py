"""Independent known-graph tests and strict finite claim boundaries."""
import unittest

from witnora_core.conditional_graph_conjectures import (
    graph_record, holds, run_experiment,
)


class ConditionalGraphConjectureTests(unittest.TestCase):
    def test_known_conditionals_and_transformations(self):
        path = graph_record(4, ((0, 1), (1, 2), (2, 3)))
        triangle = graph_record(3, ((0, 1), (0, 2), (1, 2)))
        self.assertTrue(path["conditions"]["bipartite"])
        self.assertTrue(path["conditions"]["tree"])
        self.assertFalse(triangle["conditions"]["bipartite"])
        self.assertTrue(holds(("conditional", "bipartite", "tau==nu", ""), path))
        self.assertTrue(holds(("cross", "alpha", "omega", "complement"), triangle))
        self.assertTrue(holds(("transform", "delete_vertex_0", "chi", "le"), triangle))
        self.assertFalse(holds(("conditional", "connected", "chi<=2", ""), triangle))

    def test_survivors_unproved(self):
        result = run_experiment(holdout_each=25)
        self.assertIn("if bipartite(G) then tau==nu", result["holdout_survivors"])
        self.assertIn("alpha(G) = omega(complement(G))", result["holdout_survivors"])
        self.assertFalse(result["theorem_proven"])


if __name__ == "__main__":
    unittest.main()
