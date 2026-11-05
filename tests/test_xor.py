import json
import tempfile
import unittest
from pathlib import Path

from witnora_core.certificate import SAT, XOR_UNSAT_NATIVE
from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.independent_check import verify_wcert_raw
from witnora_core.proof import export_certificate_bundle
from witnora_core.runner import solve_with_xor
from witnora_core.xor import (
    XorEquation,
    XorSystem,
    detect_cnf_xor_patterns,
    parse_xor_lines,
    reconstruct_assignment,
    solve_xor_system_gaussian,
    verify_xor_assignment,
)


def xor3_clauses(rhs: int):
    clauses = []
    for bits in [(0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1), (1, 0, 0), (1, 0, 1), (1, 1, 0), (1, 1, 1)]:
        if (bits[0] ^ bits[1] ^ bits[2]) == rhs:
            continue
        clauses.append([(-var if bit else var) for var, bit in zip([1, 2, 3], bits)])
    return clauses


def signed_xor_clauses(literals: list[int], rhs: int):
    variables = sorted({abs(lit) for lit in literals})
    clauses = []
    for mask in range(1 << len(variables)):
        assignment = {
            var: bool((mask >> index) & 1)
            for index, var in enumerate(variables)
        }
        parity = 0
        for lit in literals:
            value = assignment[abs(lit)]
            if lit < 0:
                value = not value
            parity ^= int(value)
        if parity == rhs:
            continue
        clause = []
        for var in variables:
            value = assignment[var]
            clause.append(-var if value else var)
        clauses.append(clause)
    return clauses


class XorTest(unittest.TestCase):
    def test_gaussian_solve(self):
        system = XorSystem([XorEquation([1, 2], 1), XorEquation([2, 3], 0)])
        solution = solve_xor_system_gaussian(system)
        assignment = reconstruct_assignment(solution)
        self.assertEqual(solution["status"], "SAT")
        self.assertTrue(verify_xor_assignment(system, assignment))
        self.assertEqual(solution["rank"], 2)
        print("XOR_GAUSSIAN_SOLVE_PASS")

    def test_gaussian_unsat(self):
        system = XorSystem([XorEquation([1], 0), XorEquation([1], 1)])
        solution = solve_xor_system_gaussian(system)
        self.assertEqual(solution["status"], "UNSAT")
        self.assertEqual(solution["contradiction"], {"variables": [], "rhs": 1})
        print("XOR_GAUSSIAN_UNSAT_PASS")

    def test_sidecar_sat(self):
        formula = CNFFormula.from_raw_clauses([[1]])
        system = parse_xor_lines("xor 1 2 = 1\n")
        path = solve_with_xor(formula, c=2, xor_system=system)
        assignment = path.reconstructed_original_assignment
        self.assertEqual(path.status, SAT)
        self.assertTrue(formula_satisfied(formula, assignment))
        self.assertTrue(verify_xor_assignment(system, assignment))
        print("XOR_SIDECAR_SAT_PASS")

    def test_sidecar_unsat_native(self):
        formula = CNFFormula()
        system = parse_xor_lines("xor 1 = 0\nxor 1 = 1\n")
        path = solve_with_xor(formula, c=2, xor_system=system)
        self.assertEqual(path.status, XOR_UNSAT_NATIVE)
        self.assertEqual(path.final_class, "XOR_UNSAT_NATIVE")
        self.assertFalse(path.xor_data["xor_status"]["external_drat"])
        print("XOR_SIDECAR_UNSAT_NATIVE_PASS")

    def test_equivalence_pattern_detect(self):
        formula = CNFFormula.from_raw_clauses([[-1, 2], [1, -2]])
        detected = detect_cnf_xor_patterns(formula, include_3var=False)
        self.assertEqual([(eq.variables, eq.rhs) for eq in detected.equations], [((1, 2), 0)])
        path = solve_with_xor(formula, c=2, detect_cnf_xor=True)
        self.assertEqual(path.status, SAT)
        self.assertTrue(verify_xor_assignment(detected, path.reconstructed_original_assignment))
        print("XOR_EQUIVALENCE_PATTERN_DETECT_PASS")

    def test_disequality_pattern_detect(self):
        formula = CNFFormula.from_raw_clauses([[1, 2], [-1, -2]])
        detected = detect_cnf_xor_patterns(formula, include_3var=False)
        self.assertEqual([(eq.variables, eq.rhs) for eq in detected.equations], [((1, 2), 1)])
        path = solve_with_xor(formula, c=2, detect_cnf_xor=True)
        self.assertEqual(path.status, SAT)
        self.assertTrue(verify_xor_assignment(detected, path.reconstructed_original_assignment))
        print("XOR_DISEQUALITY_PATTERN_DETECT_PASS")

    def test_extra_clause_safe_implied_constraint(self):
        formula = CNFFormula.from_raw_clauses([[1, 2], [-1, -2], [1]])
        detected = detect_cnf_xor_patterns(formula, include_3var=False)
        self.assertEqual(len(detected.equations), 1)
        equation = detected.equations[0]
        self.assertEqual((equation.variables, equation.rhs), ((1, 2), 1))
        self.assertEqual(equation.detection_mode, "IMPLIED_CONSTRAINT_ONLY")
        self.assertFalse(equation.source_clauses_removed)
        self.assertIn((1,), equation.extra_clauses_touching_variables)
        path = solve_with_xor(formula, c=2, detect_cnf_xor=True)
        assignment = path.reconstructed_original_assignment
        self.assertEqual(path.status, SAT)
        self.assertTrue(formula_satisfied(formula, assignment))
        self.assertTrue(verify_xor_assignment(detected, assignment))
        print("XOR_EXTRA_CLAUSE_SAFE_PASS")

    def test_extra_clause_no_replacement_metadata(self):
        formula = CNFFormula.from_raw_clauses([[1, 2], [-1, -2], [1]])
        detected = detect_cnf_xor_patterns(formula, include_3var=False)
        equation = detected.equations[0]
        self.assertEqual(equation.detection_mode, "IMPLIED_CONSTRAINT_ONLY")
        self.assertFalse(equation.source_clauses_removed)
        self.assertEqual(equation.pattern_size, 2)
        self.assertTrue(equation.safe_use)
        self.assertTrue({tuple(clause.literals) for clause in formula.clauses}.issuperset(equation.source_clauses))
        print("XOR_EXTRA_CLAUSE_NO_REPLACEMENT_PASS")

    def test_incomplete_2var_reject(self):
        formula = CNFFormula.from_raw_clauses([[-1, 2]])
        detected = detect_cnf_xor_patterns(formula, include_3var=False)
        self.assertEqual(detected.equations, ())
        print("XOR_INCOMPLETE_2VAR_REJECT_PASS")

    def test_incomplete_3var_reject(self):
        formula = CNFFormula.from_raw_clauses(xor3_clauses(1)[:-1])
        detected = detect_cnf_xor_patterns(formula, include_3var=True)
        self.assertEqual(detected.equations, ())
        print("XOR_INCOMPLETE_3VAR_REJECT_PASS")

    def test_duplicate_clause_safe(self):
        formula = CNFFormula.from_raw_clauses([[-1, 2], [-1, 2]])
        detected = detect_cnf_xor_patterns(formula, include_3var=False)
        self.assertEqual(detected.equations, ())
        print("XOR_DUPLICATE_CLAUSE_SAFE_PASS")

    def test_larger_clause_pollution_reject(self):
        formula = CNFFormula.from_raw_clauses([[-1, 2, 3], [1, -2]])
        detected = detect_cnf_xor_patterns(formula, include_3var=False)
        self.assertEqual(detected.equations, ())
        print("XOR_LARGER_CLAUSE_POLLUTION_REJECT_PASS")

    def test_polarity_normalization_2var(self):
        cases = [
            ([1, 2], 0, 0),
            ([1, 2], 1, 1),
            ([-1, 2], 0, 1),
            ([1, -2], 0, 1),
            ([-1, -2], 0, 0),
        ]
        for literals, literal_rhs, expected_rhs in cases:
            formula = CNFFormula.from_raw_clauses(signed_xor_clauses(literals, literal_rhs))
            detected = detect_cnf_xor_patterns(formula, include_3var=False)
            self.assertIn(((1, 2), expected_rhs), [(eq.variables, eq.rhs) for eq in detected.equations])
        print("XOR_POLARITY_NORMALIZATION_PASS")

    def test_final_assignment_verifies_cnf_and_xor(self):
        formula = CNFFormula.from_raw_clauses([[1, 2], [-1, -2]])
        system = XorSystem([XorEquation([1, 2], 1)])
        path = solve_with_xor(formula, c=2, xor_system=system)
        assignment = path.reconstructed_original_assignment
        self.assertTrue(formula_satisfied(formula, assignment))
        self.assertTrue(verify_xor_assignment(system, assignment))
        self.assertTrue(path.original_verification)
        print("XOR_FINAL_ASSIGNMENT_VERIFIES_CNF_AND_XOR_PASS")

    def test_no_false_drat_claim(self):
        formula = CNFFormula()
        system = parse_xor_lines("xor 1 = 0\nxor 1 = 1\n")
        path = solve_with_xor(formula, c=2, xor_system=system)
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "xor_unsat.wcert"
            export_certificate_bundle(
                formula,
                path,
                cert,
                original_dimacs_text=formula.canonical_dimacs(),
                export_drat=True,
            )
            manifest = json.loads((cert / "manifest.json").read_text(encoding="utf-8"))
            self.assertTrue((cert / "xor_system.json").exists())
            self.assertTrue((cert / "xor_trace.json").exists())
            self.assertTrue((cert / "xor_status.json").exists())
            independent = verify_wcert_raw(cert)
        self.assertFalse(manifest["external_drat"])
        self.assertNotEqual(manifest["drat_export_status"], "EXPORTED")
        self.assertTrue(independent["verified"])
        self.assertTrue(independent["checks"]["xor_native_unsat_not_drat"])
        print("XOR_NO_FALSE_DRAT_CLAIM_PASS")

    def test_cert_source_clauses_verify(self):
        formula = CNFFormula.from_raw_clauses([[1, 2], [-1, -2], [1]])
        path = solve_with_xor(formula, c=2, detect_cnf_xor=True)
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "xor_extra.wcert"
            export_certificate_bundle(
                formula,
                path,
                cert,
                original_dimacs_text=formula.canonical_dimacs(),
                export_drat=True,
            )
            system = json.loads((cert / "xor_system.json").read_text(encoding="utf-8"))
            independent = verify_wcert_raw(cert)
        equation = system["equations"][0]
        self.assertEqual(equation["detection_mode"], "IMPLIED_CONSTRAINT_ONLY")
        self.assertFalse(equation["source_clauses_removed"])
        self.assertEqual(equation["extra_clauses_touching_variables"], [[1]])
        self.assertTrue(independent["verified"])
        print("XOR_CERT_SOURCE_CLAUSES_VERIFY_PASS")

    def test_independent_checker_extra_clause(self):
        formula = CNFFormula.from_raw_clauses([[1, 2], [-1, -2], [1]])
        path = solve_with_xor(formula, c=2, detect_cnf_xor=True)
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "xor_extra.wcert"
            export_certificate_bundle(
                formula,
                path,
                cert,
                original_dimacs_text=formula.canonical_dimacs(),
            )
            independent = verify_wcert_raw(cert)
        self.assertTrue(independent["verified"])
        self.assertTrue(independent["checks"]["sat_assignment"])
        print("XOR_INDEPENDENT_CHECKER_EXTRA_CLAUSE_PASS")

    def test_unsat_native_no_drat_from_cnf_propagation(self):
        formula = CNFFormula.from_raw_clauses([[1, 2], [-1, -2], [1], [2]])
        path = solve_with_xor(formula, c=2, detect_cnf_xor=True)
        self.assertEqual(path.status, XOR_UNSAT_NATIVE)
        self.assertEqual(path.final_class, "XOR_UNSAT_NATIVE")
        self.assertFalse(path.xor_data["xor_status"]["external_drat"])
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "xor_conflict.wcert"
            export_certificate_bundle(
                formula,
                path,
                cert,
                original_dimacs_text=formula.canonical_dimacs(),
                export_drat=True,
            )
            manifest = json.loads((cert / "manifest.json").read_text(encoding="utf-8"))
            independent = verify_wcert_raw(cert)
        self.assertFalse(manifest["external_drat"])
        self.assertNotEqual(manifest["drat_export_status"], "EXPORTED")
        self.assertTrue(independent["verified"])
        self.assertTrue(independent["checks"]["xor_native_unsat_not_drat"])
        print("XOR_UNSAT_NATIVE_NO_DRAT_PASS")

    def test_3var_pattern_detect(self):
        formula = CNFFormula.from_raw_clauses(xor3_clauses(1))
        detected = detect_cnf_xor_patterns(formula, include_3var=True)
        self.assertIn(((1, 2, 3), 1), [(eq.variables, eq.rhs) for eq in detected.equations])
        print("XOR_3VAR_PATTERN_DETECT_PASS")

    def test_3var_rhs_parity(self):
        for rhs in (0, 1):
            formula = CNFFormula.from_raw_clauses(xor3_clauses(rhs))
            detected = detect_cnf_xor_patterns(formula, include_3var=True)
            self.assertIn(((1, 2, 3), rhs), [(eq.variables, eq.rhs) for eq in detected.equations])
        print("XOR_3VAR_RHS_PARITY_PASS")

    def test_3var_polarity_normalization(self):
        formula = CNFFormula.from_raw_clauses(signed_xor_clauses([-1, 2, 3], 0))
        detected = detect_cnf_xor_patterns(formula, include_3var=True)
        self.assertIn(((1, 2, 3), 1), [(eq.variables, eq.rhs) for eq in detected.equations])
        print("XOR_3VAR_POLARITY_NORMALIZATION_PASS")

    def test_3var_pattern_reject_incomplete(self):
        clauses = xor3_clauses(1)
        formula = CNFFormula.from_raw_clauses(clauses[:-1])
        detected = detect_cnf_xor_patterns(formula, include_3var=True)
        self.assertNotIn(((1, 2, 3), 1), [(eq.variables, eq.rhs) for eq in detected.equations])
        print("XOR_3VAR_PATTERN_REJECT_INCOMPLETE_PASS")


if __name__ == "__main__":
    unittest.main()
