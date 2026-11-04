"""R-060: exact native/Python finite graph family comparison."""
import os
import unittest

from witnora_core.targeted_graph_theorems import (
    cycle, wheel, complete_bipartite, mycielski_c5, graph_family_rust,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in Rust CI")
class TargetedGraphFamiliesRustTests(unittest.TestCase):
    def test_cycle_and_wheel(self):
        for n in range(3, 100):
            self.assertEqual(graph_family_rust("cycle", n), cycle(n))
        for n in range(4, 100):
            self.assertEqual(graph_family_rust("wheel", n), wheel(n))

    def test_bipartite_and_mycielski(self):
        for a in range(1, 15):
            for b in range(1, 15):
                self.assertEqual(graph_family_rust("bipartite", a, b),
                                 complete_bipartite(a, b))
        self.assertEqual(graph_family_rust("mycielski_c5"), mycielski_c5())

    def test_invalid_inputs_fail_closed(self):
        for family, a, b in (("cycle", 2, 0), ("wheel", 3, 0),
                             ("bipartite", 0, 2), ("unknown", 5, 0)):
            with self.subTest(family=family, a=a, b=b):
                with self.assertRaises(ValueError):
                    graph_family_rust(family, a, b)


if __name__ == "__main__":
    unittest.main()
