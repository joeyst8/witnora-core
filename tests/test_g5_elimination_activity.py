"""Research diagnostics for live G5 elimination-derived separator hints."""

import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.g5_elimination_activity import (
    activity_from_g5_operations,
    ranked_pair_candidates,
)
from witnora_core.operator_genesis import gaussian_eliminate_gf2
from witnora_core.separator_affine_family_theorem import (
    primal_graph,
    _components_after_removing,
    recognize_separator_affine_family,
    SEPARATOR_AFFINE_FAMILY_RECOGNIZED,
)
from witnora_core.separator_structural_priority import articulation_vertices
from witnora_core.xor import canonical_xor_cnf_clauses


def two_bridge_equations():
    # A six-cycle: 9--1--2--10--4--3--9.
    # Neither 9 nor 10 alone disconnects the graph; together they leave
    # two disconnected residual components {1,2} and {3,4}.
    return [
        {"variables": [9, 1], "parity_bit": 0},
        {"variables": [10, 2], "parity_bit": 0},
        {"variables": [1, 2], "parity_bit": 0},
        {"variables": [9, 3], "parity_bit": 0},
        {"variables": [10, 4], "parity_bit": 0},
        {"variables": [3, 4], "parity_bit": 0},
    ]


class G5EliminationActivityTest(unittest.TestCase):
    def test_six_cycle_exposes_two_variable_separator_without_articulation(self):
        equations = two_bridge_equations()
        raw = [
            clause
            for equation in equations
            for clause in canonical_xor_cnf_clauses(
                equation["variables"], equation["parity_bit"]
            )
        ]
        cnf = CNFFormula.from_raw_clauses(raw)
        graph = primal_graph(cnf)
        self.assertEqual(articulation_vertices(graph), ())
        self.assertEqual(
            _components_after_removing(graph, {9, 10}), [[1, 2], [3, 4]]
        )

        elimination = gaussian_eliminate_gf2(equations)
        self.assertGreater(len(elimination["row_operations"]), 0)
        activity = activity_from_g5_operations(
            elimination["row_operations"], cnf.variables
        )
        self.assertEqual(activity["status"], "DIAGNOSTIC_ONLY")
        self.assertEqual(set(activity["top_pair"]), {9, 10})
        self.assertEqual(
            set(ranked_pair_candidates(activity)[0]), {9, 10}
        )
        self.assertEqual(
            len(ranked_pair_candidates(activity)),
            len(cnf.variables) * (len(cnf.variables) - 1) // 2
        )

    def test_opt_in_g14_search_reuses_live_activity_but_checks_components(self):
        equations = two_bridge_equations()
        raw = [
            clause
            for equation in equations
            for clause in canonical_xor_cnf_clauses(
                equation["variables"], equation["parity_bit"]
            )
        ]
        formula = CNFFormula.from_raw_clauses(raw)
        elimination = gaussian_eliminate_gf2(equations)
        activity_result = recognize_separator_affine_family(
            formula,
            c=2,
            r=2,
            priority="g5_activity",
            g5_operations=elimination["row_operations"],
        )
        graph_result = recognize_separator_affine_family(
            formula, c=2, r=2, priority="structural"
        )
        self.assertEqual(activity_result["status"], SEPARATOR_AFFINE_FAMILY_RECOGNIZED)
        self.assertEqual(activity_result["status"], graph_result["status"])
        first_pair = next(
            row["separator"] for row in activity_result["trace"]
            if len(row["separator"]) == 2
        )
        self.assertEqual(set(first_pair), {9, 10})
        self.assertEqual(set(activity_result["separator_variables"]), {9, 10})
        self.assertLessEqual(
            activity_result["candidates_examined"],
            graph_result["candidates_examined"]
        )
        with self.assertRaises(ValueError):
            recognize_separator_affine_family(
                formula, c=2, r=2, priority="g5_activity"
            )

    def test_operation_order_does_not_change_activity_count(self):
        result = gaussian_eliminate_gf2(two_bridge_equations())
        operations = result["row_operations"]
        forward = activity_from_g5_operations(operations, [1, 2, 3, 4, 9, 10])
        reversed_result = activity_from_g5_operations(
            reversed(operations), [1, 2, 3, 4, 9, 10]
        )
        self.assertEqual(forward, reversed_result)

    def test_tampered_internal_hint_data_fails_closed(self):
        operations = [
            {
                "operation": "ADD_ROW_XOR",
                "before": {"coefficients": [1, 1]},
                "source": {"coefficients": [1, 2]},
            }
        ]
        with self.assertRaises(ValueError):
            activity_from_g5_operations(operations, [1, 2])
        operations[0]["before"] = {"coefficients": [1]}
        operations[0]["source"] = {"coefficients": [1, 3]}
        with self.assertRaises(ValueError):
            activity_from_g5_operations(operations, [1, 2])
        with self.assertRaises(ValueError):
            activity_from_g5_operations(
                [{"operation": "UNSUPPORTED"}], [1, 2]
            )

    def test_empty_trace_cannot_claim_a_proof(self):
        result = activity_from_g5_operations([], [1, 2, 9])
        self.assertEqual(result["status"], "DIAGNOSTIC_ONLY")
        self.assertEqual(result["xor_operations"], 0)
        self.assertEqual(result["touches"], {1: 0, 2: 0, 9: 0})
        self.assertEqual(ranked_pair_candidates(result, limit=0), ())
        with self.assertRaises(ValueError):
            ranked_pair_candidates(result, limit=-1)


if __name__ == "__main__":
    unittest.main()
