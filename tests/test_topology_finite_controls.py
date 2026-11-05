"""Finite, non-asymptotic falsification of topology-alone model-count claims."""

import unittest

from scripts.benchmark_topology_finite_controls import audit


class FiniteTopologyControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit()

    def test_complete_seven_edge_universe(self):
        self.assertEqual(self.result["all_labeled_seven_edge_graphs"], 6435)
        self.assertEqual(self.result["connected_graphs"], 5700)

    def test_separator_two_matched_topology_groups(self):
        rows = {row["flag_beta1_mod2"]: row
                for row in self.result["groups"] if row["separator_order_le2"] == 2}
        self.assertEqual(set(rows), {1, 2})
        self.assertEqual(rows[1]["labeled_graphs"], 360)
        self.assertEqual(rows[2]["labeled_graphs"], 360)
        self.assertEqual(rows[1]["unlabeled_classes_if_separator_two"], 1)
        self.assertEqual(rows[2]["unlabeled_classes_if_separator_two"], 2)
        self.assertEqual((rows[1]["min_models"], rows[1]["max_models"]), (16, 16))
        self.assertEqual((rows[2]["min_models"], rows[2]["max_models"]), (17, 17))

    def test_signed_polarities_falsify_count_determination(self):
        first, second = self.result["signed_negative_controls"]
        self.assertEqual(first["signings"], 16_384)
        self.assertEqual(second["signings"], 16_384)
        self.assertEqual(first["minimum_models"], 1)
        self.assertEqual(first["maximum_models"], 16)
        self.assertEqual(second["minimum_models"], 1)
        self.assertEqual(second["maximum_models"], 17)
        self.assertTrue(set(first["distinct_model_counts"]) &
                        set(second["distinct_model_counts"]))


if __name__ == "__main__":
    unittest.main()
