"""Production Python DFS labels must satisfy Lean graph-edge invariants."""
import unittest

from scripts.generate_g14_dfs_labels_lean import emit_dfs_labels


class PythonDFSLeanTests(unittest.TestCase):
    def test_reproducible_23_case_label_evidence(self):
        source, counts = emit_dfs_labels(16)
        self.assertEqual((source, counts), emit_dfs_labels(16))
        self.assertEqual(counts["cases"], 23)
        self.assertGreater(counts["source_variables"], 20)
        self.assertEqual(counts["negative_label_tests"], 2)
        self.assertIn("checkGraphEdgeLabels", source)
        self.assertIn("checkAllVariablesLabeled", source)
        self.assertNotIn("sorry", source)

    def test_invalid_case_counts_rejected(self):
        for count in (-1, 65):
            with self.assertRaises(ValueError):
                emit_dfs_labels(count)


if __name__ == "__main__":
    unittest.main()
