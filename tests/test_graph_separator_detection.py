import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.graph_separator_lift import (
    GRAPH_SEPARATOR_CERTIFICATE_FAILED,
    GRAPH_SEPARATOR_STRUCTURE_DETECTED,
    check_graph_separator_certificate,
    detect_separator,
    make_graph_separator_instance,
)


class GraphSeparatorDetectionTest(unittest.TestCase):
    def test_graph_separator_detection(self):
        instance = make_graph_separator_instance("separator_sat_pair")
        detection = detect_separator(instance.formula)
        self.assertEqual(detection["status"], GRAPH_SEPARATOR_STRUCTURE_DETECTED)
        self.assertEqual(detection["separator_variables"], [1])
        print("GRAPH_SEPARATOR_DETECTION_PASS")

    def test_graph_separator_decomposition(self):
        instance = make_graph_separator_instance("separator_sat_pair")
        detection = detect_separator(instance.formula)
        components = detection["components"]
        self.assertEqual(len(components), 2)
        self.assertEqual([component["variables"] for component in components], [[2, 3], [4, 5]])
        self.assertTrue(all(component["clause_ids"] for component in components))
        print("GRAPH_SEPARATOR_DECOMPOSITION_PASS")

    def test_graph_separator_invalid_cross_clause_reject(self):
        formula = CNFFormula.from_raw_clauses([[1, 2], [1, 4], [2, 4]])
        bad_cert = {
            "type": "GRAPH_SEPARATOR_LIFT_CERTIFICATE",
            "instance_id": "bad_cross",
            "formula_hash": formula.formula_hash,
            "graph_model": "PRIMAL",
            "separator_variables": [1],
            "components": [
                {"component_id": "C1", "variables": [2], "clause_ids": [1], "boundary_separator_variables": [1]},
                {"component_id": "C2", "variables": [4], "clause_ids": [2], "boundary_separator_variables": [1]},
            ],
            "separator_assignments": [
                {"assignment_id": "S0", "assignment": {"1": False}},
                {"assignment_id": "S1", "assignment": {"1": True}},
            ],
            "mode": "SAT_WITNESS_LIFT",
            "component_results": [],
            "sat_lift": {"chosen_separator_assignment": {"assignment_id": "S0", "assignment": {"1": False}}, "component_witnesses": {}, "combined_assignment": {"1": False, "2": True, "4": True}, "combined_assignment_verified_against_original_cnf": False},
            "unsat_cover": None,
            "compression_or_delta_summary": {},
            "checker_status": "NOT_RUN",
            "status": "GRAPH_SEPARATOR_STRUCTURE_DETECTED",
            "public_category": "SAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED",
            "certification_level": "GRAPH_SEPARATOR_SAT_WITNESS_LIFTED",
            "drat_claim": "GRAPH_SEPARATOR_DRAT_NOT_CLAIMED",
            "claim_boundary": "native graph-separator certificate only; no DRAT proof claimed; no theorem claim, no completeness claim, no lower-bound claim, and no P vs NP claim",
        }
        result = check_graph_separator_certificate(formula, bad_cert)
        self.assertEqual(result["checker_status"], GRAPH_SEPARATOR_CERTIFICATE_FAILED)
        self.assertTrue(any("INVALID_CROSS_COMPONENT_CLAUSE" in error for error in result["errors"]))
        print("GRAPH_SEPARATOR_INVALID_CROSS_CLAUSE_REJECT_PASS")


if __name__ == "__main__":
    unittest.main()
