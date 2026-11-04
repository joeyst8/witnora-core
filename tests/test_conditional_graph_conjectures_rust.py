"""R-091: native equality for bounded conditional graph experiments."""
import unittest

from witnora_core.conditional_graph_conjectures import run_experiment

try:
    from witnora_ve import conditional_graph_conjectures_run_native
except ImportError:
    conditional_graph_conjectures_run_native = None


@unittest.skipUnless(conditional_graph_conjectures_run_native is not None,
                     "native Rust wheel unavailable")
class ConditionalGraphConjecturesRust(unittest.TestCase):
    def test_complete_experiments(self):
        for count in (1, 12, 55, 120):
            with self.subTest(count=count):
                self.assertEqual(run_experiment(holdout_each=count),
                                 run_experiment(holdout_each=count, backend="rust"))

    def test_empty_input(self):
        considered, candidates, surviving, rejected = conditional_graph_conjectures_run_native([], [])
        self.assertEqual((considered, candidates), (58, 2))
        self.assertEqual(len(surviving), 2)
        self.assertEqual(rejected, [])


if __name__ == "__main__":
    unittest.main()
