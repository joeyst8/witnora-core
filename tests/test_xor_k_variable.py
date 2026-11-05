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
    XOR_PATTERN_SKIPPED_MAX_K,
    XorEquation,
    XorSystem,
    canonical_xor_cnf_clauses,
    detect_cnf_xor_patterns,
    parse_xor_lines,
    verify_xor_assignment,
)


def signed_xor_encoding(literals: list[int], rhs: int) -> list[list[int]]:
    variables = tuple(sorted({abs(lit) for lit in literals}))
    clauses: list[list[int]] = []
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


class XorKVariableTest(unittest.TestCase):
    def _detect_single(self, k: int, rhs: int = 0, max_k: int = 6):
        formula = CNFFormula.from_raw_clauses(canonical_xor_cnf_clauses(range(1, k + 1), rhs))
        detected = detect_cnf_xor_patterns(formula, max_k=max_k)
        equations = [(eq.variables, eq.rhs) for eq in detected.equations]
        self.assertIn((tuple(range(1, k + 1)), rhs), equations)
        equation = next(eq for eq in detected.equations if eq.variables == tuple(range(1, k + 1)))
        self.assertEqual(equation.pattern_size, k)
        self.assertTrue(equation.exact_full_encoding)
        self.assertEqual(len(equation.source_clauses), 1 << (k - 1))
        self.assertFalse(equation.source_clauses_removed)
        return formula, detected, equation

    def test_k4_pattern_detect(self):
        self._detect_single(4, 0)
        print("XOR_K4_PATTERN_DETECT_PASS")

    def test_k5_pattern_detect(self):
        self._detect_single(5, 0)
        print("XOR_K5_PATTERN_DETECT_PASS")

    def test_k6_pattern_detect(self):
        self._detect_single(6, 0)
        print("XOR_K6_PATTERN_DETECT_PASS")

    def test_k4_rhs_parity(self):
        for rhs in (0, 1):
            self._detect_single(4, rhs)
        print("XOR_K4_RHS_PARITY_PASS")

    def test_k_polarity_normalization(self):
        formula = CNFFormula.from_raw_clauses(signed_xor_encoding([-1, 2, -3, 4], 0))
        detected = detect_cnf_xor_patterns(formula, max_k=6)
        self.assertIn(((1, 2, 3, 4), 0), [(eq.variables, eq.rhs) for eq in detected.equations])

        formula = CNFFormula.from_raw_clauses(signed_xor_encoding([-1, 2, 3, 4], 0))
        detected = detect_cnf_xor_patterns(formula, max_k=6)
        self.assertIn(((1, 2, 3, 4), 1), [(eq.variables, eq.rhs) for eq in detected.equations])
        print("XOR_K_POLARITY_NORMALIZATION_PASS")

    def test_k_incomplete_reject(self):
        clauses = sorted(canonical_xor_cnf_clauses(range(1, 5), 0))
        formula = CNFFormula.from_raw_clauses(clauses[:-1])
        detected = detect_cnf_xor_patterns(formula, max_k=6)
        self.assertEqual(detected.equations, ())
        print("XOR_K_INCOMPLETE_REJECT_PASS")

    def test_k_extra_clause_safe(self):
        clauses = list(canonical_xor_cnf_clauses(range(1, 5), 0))
        clauses.append((1,))
        formula = CNFFormula.from_raw_clauses(clauses)
        detected = detect_cnf_xor_patterns(formula, max_k=6)
        equation = next(eq for eq in detected.equations if eq.variables == (1, 2, 3, 4))
        self.assertIn((1,), equation.extra_clauses_touching_variables)
        self.assertFalse(equation.source_clauses_removed)

        path = solve_with_xor(formula, c=4, detect_cnf_xor=True, detect_xor_max_k=6)
        self.assertEqual(path.status, SAT)
        self.assertTrue(formula_satisfied(formula, path.reconstructed_original_assignment))
        self.assertTrue(verify_xor_assignment(detected, path.reconstructed_original_assignment))
        print("XOR_K_EXTRA_CLAUSE_SAFE_PASS")

    def test_k_max_cap_skip(self):
        formula = CNFFormula.from_raw_clauses(canonical_xor_cnf_clauses(range(1, 8), 0))
        detected = detect_cnf_xor_patterns(formula)
        self.assertEqual(detected.equations, ())
        self.assertTrue(any(item.get("reason") == XOR_PATTERN_SKIPPED_MAX_K for item in detected.diagnostics))
        print("XOR_K_MAX_CAP_SKIP_PASS")

    def test_k_independent_checker(self):
        formula = CNFFormula.from_raw_clauses(canonical_xor_cnf_clauses(range(1, 5), 1))
        path = solve_with_xor(formula, c=2, detect_cnf_xor=True, detect_xor_max_k=6)
        self.assertEqual(path.status, SAT)
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "xor_k4.wcert"
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
        self.assertEqual(equation["pattern_size"], 4)
        self.assertTrue(equation["exact_full_encoding"])
        self.assertTrue(independent["verified"])
        self.assertTrue(independent["checks"]["sat_assignment"])
        print("XOR_K_INDEPENDENT_CHECKER_PASS")

    def test_k_unsat_native_no_drat(self):
        formula = CNFFormula.from_raw_clauses(canonical_xor_cnf_clauses(range(1, 5), 0))
        sidecar = parse_xor_lines("xor 1 2 3 4 = 1\n")
        path = solve_with_xor(
            formula,
            c=2,
            xor_system=sidecar,
            detect_cnf_xor=True,
            detect_xor_max_k=6,
        )
        self.assertEqual(path.status, XOR_UNSAT_NATIVE)
        self.assertFalse(path.xor_data["xor_status"]["external_drat"])
        self.assertEqual(path.xor_data["xor_status"]["drat_claim"], "NOT_EXPORTED")
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "xor_k_unsat.wcert"
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
        print("XOR_K_UNSAT_NATIVE_NO_DRAT_PASS")


if __name__ == "__main__":
    unittest.main()
