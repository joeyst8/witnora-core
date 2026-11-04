"""R-072 source-CNF parity across all independent unfamiliar SAT families."""
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.ood_sat_families import (
    pigeonhole, graph_coloring, tseitin_k4, tseitin_complete_graph,
    n_queens, random_planted_3cnf, out_of_distribution_cases,
    larger_unseen_cases,
)


class OODFamiliesRustTests(unittest.TestCase):
    def setUp(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")

    def assert_source_equal(self, python, native):
        self.assertEqual(native.to_clause_lists(), python.to_clause_lists())
        self.assertEqual(native.formula_hash, python.formula_hash)

    def test_all_deterministic_source_grids(self):
        for p in range(1, 8):
            for h in range(1, 6):
                with self.subTest(kind="pigeonhole", p=p, h=h):
                    self.assert_source_equal(pigeonhole(p, h), pigeonhole(p, h, backend="rust"))
        rng = random.Random(72072)
        for trial in range(80):
            n, colors = rng.randrange(1, 9), rng.randrange(1, 6)
            edges = [(u, v) for u in range(1, n + 1)
                     for v in range(u + 1, n + 1) if rng.randrange(2)]
            with self.subTest(kind="coloring", trial=trial):
                self.assert_source_equal(graph_coloring(n, edges, colors),
                                         graph_coloring(n, edges, colors, backend="rust"))
        for n in range(1, 9):
            with self.subTest(kind="queens", n=n):
                self.assert_source_equal(n_queens(n), n_queens(n, backend="rust"))
        for n in range(3, 8):
            for contradictory in (False, True):
                with self.subTest(kind="tseitin", n=n, parity=contradictory):
                    self.assert_source_equal(
                        tseitin_complete_graph(n, contradictory=contradictory),
                        tseitin_complete_graph(n, contradictory=contradictory, backend="rust"))
        for contradictory in (False, True):
            self.assert_source_equal(tseitin_k4(contradictory=contradictory),
                                     tseitin_k4(contradictory=contradictory, backend="rust"))

    def test_200_seeded_planted_sources_and_witness(self):
        for seed in range(200):
            n = 3 + seed % 29
            count = (seed * 7) % 121
            with self.subTest(seed=seed):
                self.assert_source_equal(
                    random_planted_3cnf(n, count, seed),
                    random_planted_3cnf(n, count, seed, backend="rust"))
        # Native path checks that source assembly preserves the planted witness,
        # not merely the final hash. Independent satisfiability is already
        # checked exhaustively on smaller reference instances.
        planted = random_planted_3cnf(3, 0, 19, backend="rust")
        self.assertEqual(planted, CNFFormula())

    def test_named_case_bundles_and_rejection(self):
        for seed in (0, 1, 3, 11, 101, 401):
            for build in (out_of_distribution_cases, larger_unseen_cases):
                py = build(seed)
                rs = build(seed, backend="rust")
                self.assertEqual([(kind, name, truth) for kind, name, _, truth in py],
                                 [(kind, name, truth) for kind, name, _, truth in rs])
                for (_, _, a, _), (_, _, b, _) in zip(py, rs):
                    self.assert_source_equal(a, b)
        with self.assertRaises(ValueError):
            pigeonhole(0, 2, backend="rust")
        with self.assertRaises(ValueError):
            graph_coloring(3, [(1, 1)], 2, backend="rust")
        with self.assertRaises(ValueError):
            tseitin_complete_graph(8, contradictory=True, backend="rust")
        with self.assertRaises(ValueError):
            random_planted_3cnf(3, -1, 0, backend="rust")


if __name__ == "__main__":
    unittest.main()
