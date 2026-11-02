"""Autonomous graph-separator discovery controls."""
import unittest
import random
from types import SimpleNamespace
from unittest.mock import patch

from witnora_core.cnf import CNFFormula
from witnora_core.autonomous_parity_separator import (
    discover_repaired_separator, full_cnf_groups_separated,
    _cnf_primal_graph, _component_labels_from_graph,
)
from witnora_core.hidden_separator_challenge import make_hidden_separator
from scripts.experiment_autonomous_parity_separator import run_experiment


class AutonomousParitySeparatorTests(unittest.TestCase):
    def test_precomputed_graph_matches_independent_clause_deletion(self):
        rng = random.Random(63119)
        for _ in range(256):
            raw = []
            for _ in range(rng.randrange(0, 16)):
                vars_in_clause = rng.sample(range(1, 13), rng.randrange(0, 5))
                raw.append([v if rng.choice((False, True)) else -v
                            for v in vars_in_clause])
            formula = CNFFormula(raw)
            variables = list(formula.variables)
            removed = set(rng.sample(variables, rng.randrange(len(variables) + 1)))
            cached = _component_labels_from_graph(_cnf_primal_graph(formula), removed)

            # Independent oracle: derive adjacency after deletion from each
            # original clause, then compute undirected reachability.
            graph = {v: set() for v in variables if v not in removed}
            for clause in formula.clauses:
                surviving = set(clause.variables) - removed
                for v in surviving:
                    graph[v].update(surviving - {v})
            oracle = {}
            for start in sorted(graph):
                if start in oracle:
                    continue
                reach = {start}
                while True:
                    expanded = reach | set().union(*(graph[v] for v in reach))
                    if expanded == reach:
                        break
                    reach = expanded
                for v in reach:
                    oracle[v] = min(reach)
            self.assertEqual(set(cached), set(oracle))
            for u in oracle:
                for v in oracle:
                    self.assertEqual(cached[u] == cached[v], oracle[u] == oracle[v])

    def test_budget_does_not_discard_previously_verified_cut(self):
        # Candidate 1 succeeds at trial 1; candidate 2 would exceed budget.
        # A found, audited separator must not be forgotten merely because
        # a later optional candidate cannot be evaluated.
        formula = CNFFormula.from_raw_clauses([[1], [2], [3], [4]])
        candidates = {"candidate_cuts": [
            {"variables": [3], "component_equation_indices": [[0], [1]]},
            {"variables": [4], "component_equation_indices": [[0], [1]]},
        ]}
        equations = SimpleNamespace(equations=[
            SimpleNamespace(variables=(1,), rhs=0),
            SimpleNamespace(variables=(2,), rhs=0),
        ])
        with patch("witnora_core.autonomous_parity_separator.bounded_parity_separators",
                   return_value=candidates), patch(
                       "witnora_core.autonomous_parity_separator.detect_cnf_xor_patterns",
                       return_value=equations):
            result = discover_repaired_separator(formula, max_trials=1)
        self.assertEqual(result["status"], "FOUND")
        self.assertEqual(result["cut"], [3])
        self.assertTrue(result["full_cnf_groups_separated"])
        self.assertTrue(result["budget_exhausted"])

    def test_full_group_audit_rejects_nonxor_bridge(self):
        formula, m = make_hidden_separator(3, width=2, cross_noise=True)
        left = set(m["left_block"])
        right = set(m["right_block"])
        # The exact XOR-variable groups are larger than the printed
        # anchor blocks; the existing cross-noise must still connect them.
        self.assertFalse(full_cnf_groups_separated(
            formula, m["boundary"], [left, right]))
        result = discover_repaired_separator(formula)
        if result["status"] == "FOUND":
            self.assertTrue(result["full_cnf_groups_separated"])

    def test_random_without_xor_pattern_fails_closed(self):
        formula = CNFFormula.from_raw_clauses(
            [[1, 2, 3], [-1, 4, 5], [2, -4, 6]]
        )
        result = discover_repaired_separator(formula)
        self.assertEqual(result["status"], "NO_AUDITED_CANDIDATE")
        self.assertFalse(result["full_cnf_groups_separated"])

    def test_work_budget_fails_closed(self):
        formula, _ = make_hidden_separator(2, width=2, cross_noise=True)
        result = discover_repaired_separator(formula, max_trials=1)
        self.assertNotEqual(result["status"], "FOUND")
        self.assertFalse(result["full_cnf_groups_separated"])

    def test_blind_study_reproducible(self):
        first = run_experiment(seed_count=2)
        self.assertEqual(first, run_experiment(seed_count=2))
        self.assertEqual(first["summary"]["total"], 14)
        self.assertTrue(first["summary"]["ground_truth_not_provided_to_detector"])


if __name__ == "__main__":
    unittest.main()
