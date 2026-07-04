import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from witnora_core.drat_check import check_drat_files
from witnora_core.independent_check import verify_wcert_raw
from witnora_core.runner import main as runner_main


def write_dimacs(path, clauses, num_vars):
    lines = [f"p cnf {num_vars} {len(clauses)}"]
    for clause in clauses:
        lines.append(" ".join(str(lit) for lit in clause) + " 0")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_cert(dimacs_path, c, cert_path):
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        code = runner_main(
            [
                str(dimacs_path),
                "--c",
                str(c),
                "--export-cert",
                str(cert_path),
                "--export-drat",
            ]
        )
    return code, json.loads(stdout.getvalue())


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def full_3var_unsat_clauses():
    return [
        [1, 2, 3],
        [1, 2, -3],
        [1, -2, 3],
        [1, -2, -3],
        [-1, 2, 3],
        [-1, 2, -3],
        [-1, -2, 3],
        [-1, -2, -3],
    ]


def connected_bce_then_ve_unsat_clauses():
    return full_3var_unsat_clauses() + [
        [4, 5, 6],
        [-4, -5],
        [-4, -6],
        [3, 4],
    ]


class DRATBridgeTest(unittest.TestCase):
    def test_drat_export_empty_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "unit_unsat.dimacs"
            write_dimacs(dimacs, [[1], [-1]], 1)
            cert = root / "unit.wcert"
            code, result = export_cert(dimacs, 2, cert)
            status = read_json(cert / "drat_status.json")
            proof_exists = (cert / "proof.drat").exists()
            checked = check_drat_files(cert / "original.dimacs", cert / "proof.drat")
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assertTrue(proof_exists)
        self.assertEqual(status["drat_export_status"], "EXPORTED")
        self.assertTrue(status["internal_drat_checker_verified"])
        self.assertTrue(checked["verified"], checked)
        self.assertTrue(checked["empty_clause_derived"])
        print("DRAT_EXPORT_EMPTY_CONFLICT_PASS")

    def test_drat_export_ve_unsat(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "ve_unsat.dimacs"
            write_dimacs(dimacs, full_3var_unsat_clauses(), 3)
            cert = root / "ve.wcert"
            code, result = export_cert(dimacs, 2, cert)
            status = read_json(cert / "drat_status.json")
            checked = check_drat_files(cert / "original.dimacs", cert / "proof.drat")
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assertEqual(status["drat_export_status"], "EXPORTED")
        self.assertTrue(status["internal_drat_checker_verified"])
        self.assertTrue(checked["verified"], checked)
        print("DRAT_EXPORT_VE_UNSAT_PASS")

    def test_drat_export_2sat_scc(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "scc_unsat.dimacs"
            write_dimacs(dimacs, [[1, 2], [1, -2], [-1, 2], [-1, -2]], 2)
            cert = root / "scc.wcert"
            code, result = export_cert(dimacs, 2, cert)
            status = read_json(cert / "drat_status.json")
            proof_exists = (cert / "proof.drat").exists()
            checked = check_drat_files(cert / "original.dimacs", cert / "proof.drat")
            native_checked = verify_wcert_raw(cert)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assertEqual(status["drat_export_status"], "EXPORTED")
        self.assertEqual(status["supported_reason"], "2SAT_SCC_TO_DRAT_EXPORTED")
        self.assertTrue(proof_exists)
        self.assertTrue(checked["verified"], checked)
        self.assertTrue(native_checked["verified"], native_checked)
        print("DRAT_2SAT_SCC_EXPORTED_PASS")

    def test_drat_tamper_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "unit_unsat.dimacs"
            write_dimacs(dimacs, [[1], [-1]], 1)
            cert = root / "unit.wcert"
            export_cert(dimacs, 2, cert)
            (cert / "proof.drat").write_text("1 0\n", encoding="utf-8")
            checked = check_drat_files(cert / "original.dimacs", cert / "proof.drat")
        self.assertFalse(checked["verified"])
        self.assertEqual(checked["checker"], "witnora_internal_rup_subset_checker_v0.9.1")
        print("DRAT_TAMPER_REJECT_PASS")

    def test_drat_status_no_false_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "unit_unsat.dimacs"
            write_dimacs(dimacs, [[1], [-1]], 1)
            cert = root / "unit.wcert"
            export_cert(dimacs, 2, cert)
            manifest = read_json(cert / "manifest.json")
            status = read_json(cert / "drat_status.json")
        self.assertIs(manifest["external_lrat_frat"], False)
        self.assertIs(manifest["verification_levels"]["external_lrat_frat"], False)
        self.assertEqual(status["external_checker"], "NOT_RUN")
        self.assertIs(status["external_checker_verified"], False)
        self.assertNotIn("LRAT", status["supported_reason"])
        print("DRAT_STATUS_NO_FALSE_CLAIM_PASS")

    def test_drat_cert_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "unit_unsat.dimacs"
            write_dimacs(dimacs, [[1], [-1]], 1)
            cert = root / "unit.wcert"
            export_cert(dimacs, 2, cert)
            manifest = read_json(cert / "manifest.json")
            checked = verify_wcert_raw(cert)
        self.assertIn("proof.drat", manifest["files"])
        self.assertIn("drat_status.json", manifest["files"])
        self.assertTrue(manifest["external_drat"])
        self.assertEqual(manifest["drat_export_status"], "EXPORTED")
        self.assertTrue(checked["verified"], checked)
        self.assertTrue(checked["checks"]["drat_proof_present"])
        self.assertTrue(checked["checks"]["internal_drat_checker_verified"])
        print("DRAT_CERT_BUNDLE_PASS")

    def test_drat_end_to_end_empty_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "unit_unsat.dimacs"
            write_dimacs(dimacs, [[1], [-1]], 1)
            cert = root / "unit.wcert"
            code, result = export_cert(dimacs, 2, cert)
            status = read_json(cert / "drat_status.json")
            proof = (cert / "proof.drat").read_text(encoding="utf-8")
            checked = check_drat_files(cert / "original.dimacs", cert / "proof.drat")
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assertEqual(proof, "0\n")
        self.assertTrue(checked["verified"], checked)
        self.assertEqual(checked["checked_against"], "original.dimacs")
        self.assertEqual(status["proof_scope"], "END_TO_END_FROM_ORIGINAL_CNF")
        print("DRAT_END_TO_END_EMPTY_CONFLICT_PASS")

    def test_drat_end_to_end_ve_unsat(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "ve_unsat.dimacs"
            write_dimacs(dimacs, full_3var_unsat_clauses(), 3)
            cert = root / "ve.wcert"
            code, result = export_cert(dimacs, 2, cert)
            proof = (cert / "proof.drat").read_text(encoding="utf-8")
            status = read_json(cert / "drat_status.json")
            checked = check_drat_files(cert / "original.dimacs", cert / "proof.drat")
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assertIn("-3 -2 0", proof)
        self.assertIn("d -3 -2 -1 0", proof)
        self.assertTrue(checked["verified"], checked)
        self.assertEqual(checked["checked_against"], "original.dimacs")
        self.assertEqual(status["proof_scope"], "END_TO_END_FROM_ORIGINAL_CNF")
        print("DRAT_END_TO_END_VE_UNSAT_PASS")

    def test_drat_rejects_final_state_only_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "ve_unsat.dimacs"
            write_dimacs(dimacs, full_3var_unsat_clauses(), 3)
            cert = root / "ve.wcert"
            export_cert(dimacs, 2, cert)
            (cert / "proof.drat").write_text("0\n", encoding="utf-8")
            checked = check_drat_files(cert / "original.dimacs", cert / "proof.drat")
        self.assertFalse(checked["verified"])
        self.assertEqual(checked["checked_against"], "original.dimacs")
        self.assertEqual(checked["failed_line"], 1)
        self.assertEqual(checked["error"], "addition is not RUP-checkable")
        print("DRAT_REJECTS_FINAL_STATE_ONLY_PROOF_PASS")

    def test_drat_ve_resolvent_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "ve_unsat.dimacs"
            write_dimacs(dimacs, full_3var_unsat_clauses(), 3)
            cert = root / "ve.wcert"
            export_cert(dimacs, 2, cert)
            lines = (cert / "proof.drat").read_text(encoding="utf-8").splitlines()
        first_delete = min(i for i, line in enumerate(lines) if line.startswith("d "))
        first_resolvents = ["-3 -2 0", "-3 2 0", "-2 3 0", "2 3 0"]
        for resolvent in first_resolvents:
            self.assertLess(lines.index(resolvent), first_delete)
        print("DRAT_VE_RESOLVENT_ORDER_PASS")

    def test_drat_bce_deletion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "bce_ve_unsat.dimacs"
            write_dimacs(dimacs, connected_bce_then_ve_unsat_clauses(), 6)
            cert = root / "bce_ve.wcert"
            code, result = export_cert(dimacs, 2, cert)
            proof = (cert / "proof.drat").read_text(encoding="utf-8")
            checked = check_drat_files(cert / "original.dimacs", cert / "proof.drat")
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assertIn("d 4 5 6 0", proof)
        self.assertTrue(checked["verified"], checked)
        self.assertEqual(checked["checked_against"], "original.dimacs")
        print("DRAT_BCE_DELETION_PASS")

    def test_drat_status_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "ve_unsat.dimacs"
            write_dimacs(dimacs, full_3var_unsat_clauses(), 3)
            cert = root / "ve.wcert"
            export_cert(dimacs, 2, cert)
            status = read_json(cert / "drat_status.json")
        self.assertEqual(status["drat_export_status"], "EXPORTED")
        self.assertEqual(status["proof_scope"], "END_TO_END_FROM_ORIGINAL_CNF")
        self.assertEqual(status["checked_against"], "original.dimacs")
        self.assertTrue(status["internal_rup_subset_checker_verified"])
        self.assertFalse(status["requires_external_checker"])
        print("DRAT_STATUS_SCOPE_PASS")

    def test_drat_scc_now_exported_still_native(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "scc_unsat.dimacs"
            write_dimacs(dimacs, [[1, 2], [1, -2], [-1, 2], [-1, -2]], 2)
            cert = root / "scc.wcert"
            code, result = export_cert(dimacs, 2, cert)
            status = read_json(cert / "drat_status.json")
            proof_exists = (cert / "proof.drat").exists()
            native_checked = verify_wcert_raw(cert)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assertTrue(proof_exists)
        self.assertEqual(status["drat_export_status"], "EXPORTED")
        self.assertEqual(status["supported_reason"], "2SAT_SCC_TO_DRAT_EXPORTED")
        self.assertEqual(status["proof_scope"], "END_TO_END_FROM_ORIGINAL_CNF")
        self.assertTrue(native_checked["verified"], native_checked)
        print("DRAT_SCC_EXPORTED_STILL_NATIVE_PASS")


if __name__ == "__main__":
    unittest.main()
