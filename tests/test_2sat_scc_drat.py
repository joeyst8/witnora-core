import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from witnora_core.certificate import CollapsePath, StepLogger, UNSAT
from witnora_core.cnf import CNFFormula
from witnora_core.drat import export_drat_for_path
from witnora_core.drat_check import check_drat_files, check_drat_text
from witnora_core.drat_trim import find_drat_trim
from witnora_core.runner import main as runner_main
from witnora_core.two_sat import solve_2sat
from witnora_core.two_sat_proof import build_2sat_scc_proof
from witnora_core.ve import eliminate_variable


def write_dimacs(path, clauses, num_vars):
    lines = [f"p cnf {num_vars} {len(clauses)}"]
    for clause in clauses:
        lines.append(" ".join(str(lit) for lit in clause) + " 0")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def minimal_2sat_scc_unsat():
    return [[1, 2], [1, -2], [-1, 2], [-1, -2]]


def ve_to_2sat_scc_unsat():
    clauses = []
    for clause in minimal_2sat_scc_unsat():
        clauses.append([3, *clause])
        clauses.append([-3, *clause])
    return clauses


def export_runner_cert(root, clauses, *, drat_trim_path=None):
    dimacs = root / "case.dimacs"
    cert = root / "case.wcert"
    write_dimacs(dimacs, clauses, max(abs(lit) for clause in clauses for lit in clause))
    args = [
        str(dimacs),
        "--c",
        "2",
        "--export-cert",
        str(cert),
        "--export-drat",
    ]
    if drat_trim_path is not None:
        args.extend(["--drat-trim", str(drat_trim_path)])
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        code = runner_main(args)
    return code, json.loads(stdout.getvalue()), cert


def manual_ve_then_2sat_export():
    formula = CNFFormula.from_raw_clauses(ve_to_2sat_scc_unsat())
    logger = StepLogger()
    status, current, _details = eliminate_variable(formula, 3, 2, logger)
    if status != "OK":
        raise AssertionError(status)
    result = solve_2sat(current, logger)
    if result["status"] != "UNSAT":
        raise AssertionError(result)
    path = CollapsePath(
        original_formula_hash=formula.formula_hash,
        c_parameter=2,
        steps=logger.steps,
        final_formula_hash=current.formula_hash,
        final_class="CONFLICT",
        status=UNSAT,
        stats={},
    )
    return formula, path, export_drat_for_path(formula, path)


class TwoSatSCCDRATTest(unittest.TestCase):
    def test_two_sat_scc_drat_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code, result, cert = export_runner_cert(root, minimal_2sat_scc_unsat())
            status = read_json(cert / "drat_status.json")
            proof = (cert / "proof.drat").read_text(encoding="utf-8")
            checked = check_drat_files(cert / "original.dimacs", cert / "proof.drat")
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assertEqual(status["drat_export_status"], "EXPORTED")
        self.assertEqual(status["supported_reason"], "2SAT_SCC_TO_DRAT_EXPORTED")
        self.assertTrue(status["internal_rup_subset_checker_verified"])
        self.assertTrue(checked["verified"], checked)
        self.assertEqual(proof, "-1 0\n1 0\n0\n")
        print("TWO_SAT_SCC_DRAT_EXPORT_PASS")

    @unittest.skipUnless(
        find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM")),
        "real drat-trim not available on PATH or WITNORA_DRAT_TRIM",
    )
    def test_two_sat_scc_drat_trim(self):
        drat_trim = find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code, result, cert = export_runner_cert(
                root,
                minimal_2sat_scc_unsat(),
                drat_trim_path=drat_trim,
            )
            status = read_json(cert / "drat_status.json")
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assertEqual(status["external_checker"], "DRAT_TRIM")
        self.assertTrue(status["external_checker_ran"])
        self.assertTrue(status["external_checker_verified"], status)
        self.assertIn("VERIFIED", status["external_checker_stdout_excerpt"])
        print("TWO_SAT_SCC_DRAT_TRIM_PASS")

    def test_two_sat_scc_path_extraction(self):
        formula = CNFFormula.from_raw_clauses(minimal_2sat_scc_unsat())
        proof = build_2sat_scc_proof(formula, 1)
        pos_path = [(edge.source, edge.target) for edge in proof.path_pos_to_neg]
        neg_path = [(edge.source, edge.target) for edge in proof.path_neg_to_pos]
        self.assertEqual(pos_path[0][0], 1)
        self.assertEqual(pos_path[-1][1], -1)
        self.assertEqual(neg_path[0][0], -1)
        self.assertEqual(neg_path[-1][1], 1)
        self.assertEqual(proof.derived_clauses[-2:], ((-1,), (1,)))
        print("TWO_SAT_SCC_PATH_EXTRACTION_PASS")

    def test_two_sat_scc_fake_edge_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _code, _result, cert = export_runner_cert(root, minimal_2sat_scc_unsat())
            (cert / "proof.drat").write_text("3 0\n1 0\n0\n", encoding="utf-8")
            checked = check_drat_files(cert / "original.dimacs", cert / "proof.drat")
        self.assertFalse(checked["verified"])
        self.assertEqual(checked["error"], "addition is not RUP-checkable")
        print("TWO_SAT_SCC_FAKE_EDGE_REJECT_PASS")

    def test_two_sat_scc_final_state_only_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _code, _result, cert = export_runner_cert(root, minimal_2sat_scc_unsat())
            (cert / "proof.drat").write_text("0\n", encoding="utf-8")
            checked = check_drat_files(cert / "original.dimacs", cert / "proof.drat")
        self.assertFalse(checked["verified"])
        self.assertEqual(checked["failed_line"], 1)
        print("TWO_SAT_SCC_FINAL_STATE_ONLY_REJECT_PASS")

    def test_two_sat_scc_after_ve_drat(self):
        formula, _path, export = manual_ve_then_2sat_export()
        self.assertEqual(export.status["drat_export_status"], "EXPORTED")
        self.assertEqual(export.status["supported_reason"], "2SAT_SCC_TO_DRAT_EXPORTED")
        self.assertIn("two_sat_scc_proof", export.status)
        self.assertIn("d -3 -2 -1 0", export.proof_text)
        self.assertIn("-1 0", export.proof_text)
        checked = check_drat_text(formula, export.proof_text or "", strict_deletions=True)
        self.assertTrue(checked["verified"], checked)
        drat_trim = find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM"))
        if drat_trim is not None:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                original = root / "original.dimacs"
                proof = root / "proof.drat"
                original.write_text(formula.canonical_dimacs(), encoding="utf-8")
                proof.write_text(export.proof_text or "", encoding="utf-8")
                external = check_drat_files(original, proof, drat_trim=drat_trim)
            self.assertTrue(external["external_checker_verified"], external)
        print("TWO_SAT_SCC_AFTER_VE_DRAT_PASS")

    def test_drat_status_2sat_no_longer_unsupported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _code, _result, cert = export_runner_cert(root, minimal_2sat_scc_unsat())
            status = read_json(cert / "drat_status.json")
        self.assertNotEqual(status.get("unsupported_reason"), "2SAT_SCC_TO_DRAT_NOT_IMPLEMENTED")
        self.assertEqual(status["drat_export_status"], "EXPORTED")
        self.assertEqual(status["proof_scope"], "END_TO_END_FROM_ORIGINAL_CNF")
        print("DRAT_STATUS_2SAT_NO_LONGER_UNSUPPORTED_PASS")


if __name__ == "__main__":
    unittest.main()
