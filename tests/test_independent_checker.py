import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from witnora_core.independent_check import (
    canonicalize_formula_raw,
    check_2sat_result_raw,
    check_bce_step_raw,
    check_component_decomposition_raw,
    check_ve_step_raw,
    compute_certificate_hash_raw,
    hash_formula_raw,
    stable_json_raw,
    verify_wcert_raw,
)
from witnora_core.runner import main as runner_main


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def export_cert(example_name, c, cert_path):
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        runner_main(
            [
                str(EXAMPLES / example_name),
                "--c",
                str(c),
                "--export-cert",
                str(cert_path),
            ]
        )
    return json.loads(stdout.getvalue())


def rewrite_manifest_hashes(cert_path):
    manifest_path = cert_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name in manifest["files"]:
        manifest["files"][name]["sha256"] = hash_text((cert_path / name).read_text(encoding="utf-8"))
    manifest_path.write_text(stable_json_raw(manifest), encoding="utf-8")


def hash_text(text):
    from hashlib import sha256

    return sha256(text.encode("utf-8")).hexdigest()


def sync_certificate_hash(cert_path, result):
    new_hash = compute_certificate_hash_raw(result)
    result["certificate_hash"] = new_hash
    (cert_path / "result.json").write_text(stable_json_raw(result), encoding="utf-8")
    (cert_path / "certificate_hash.txt").write_text(new_hash + "\n", encoding="utf-8")
    manifest_path = cert_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["certificate_hash"] = new_hash
    manifest["status"] = result["status"]
    manifest["final_class"] = result["final_class"]
    manifest_path.write_text(stable_json_raw(manifest), encoding="utf-8")
    rewrite_manifest_hashes(cert_path)


class IndependentCheckerTest(unittest.TestCase):
    def test_independent_cert_sat(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "bce.wcert"
            export_cert("bce_demo.dimacs", 2, cert)
            result = verify_wcert_raw(cert)
        self.assertTrue(result["verified"], result)
        self.assertEqual(result["status"], "SAT")
        print("INDEPENDENT_CERT_SAT_PASS")

    def test_independent_cert_components(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "components.wcert"
            export_cert("multi_component_demo.dimacs", 2, cert)
            result = verify_wcert_raw(cert)
        self.assertTrue(result["verified"], result)
        self.assertEqual(result["status"], "SAT")
        print("INDEPENDENT_CERT_COMPONENTS_PASS")

    def test_independent_cert_unsat_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "unsat.wcert"
            export_cert("unsat_demo.dimacs", 2, cert)
            result = verify_wcert_raw(cert)
        self.assertTrue(result["verified"], result)
        self.assertEqual(result["status"], "UNSAT")
        self.assertTrue(result["checks"]["unsat_contradiction"])
        print("INDEPENDENT_CERT_UNSAT_EXPLICIT_PASS")

    def test_independent_bce_check(self):
        formula = canonicalize_formula_raw([[1, 2, 3], [-1, -2], [-1, -3]])
        output = canonicalize_formula_raw([[-1, -2], [-1, -3]])
        valid = {
            "type": "BCE",
            "input_formula_hash": hash_formula_raw(formula),
            "output_formula_hash": hash_formula_raw(output),
            "removed_clauses": [[1, 2, 3]],
            "details": {
                "blocked_literal": 1,
                "opposite_clauses": [[-3, -1], [-2, -1]],
                "checked_resolvents": [
                    {
                        "against_clause": [-3, -1],
                        "resolvent": [-3, 2, 3],
                        "tautological": True,
                    },
                    {
                        "against_clause": [-2, -1],
                        "resolvent": [-2, 2, 3],
                        "tautological": True,
                    },
                ],
            },
        }
        self.assertEqual(check_bce_step_raw(formula, valid), output)
        for bad in [
            {**valid, "details": {**valid["details"], "blocked_literal": 2}},
            {**valid, "removed_clauses": [[1, 2]]},
            {**valid, "details": {**valid["details"], "opposite_clauses": [[-3, -1]]}},
            {
                **valid,
                "details": {
                    **valid["details"],
                    "checked_resolvents": valid["details"]["checked_resolvents"][:1],
                },
            },
            {**valid, "output_formula_hash": "0" * 64},
        ]:
            with self.assertRaises(ValueError):
                check_bce_step_raw(formula, bad)
        non_blocked = canonicalize_formula_raw([[1, 2, 3], [-1, 4], [-2, -3]])
        with self.assertRaises(ValueError):
            check_bce_step_raw(non_blocked, valid)
        print("INDEPENDENT_BCE_CHECK_PASS")

    def test_independent_ve_check(self):
        formula = canonicalize_formula_raw([[1, 2], [-1, 3]])
        output = canonicalize_formula_raw([[2, 3]])
        valid = {
            "type": "VE",
            "output_formula_hash": hash_formula_raw(output),
            "removed_clauses": [[-1, 3], [1, 2]],
            "added_clauses": [[2, 3]],
            "details": {"eliminated_variable": 1},
            "reconstruction_data": {"eliminated_variable": 1},
        }
        self.assertEqual(check_ve_step_raw(formula, valid, 2), output)
        for bad in [
            {**valid, "added_clauses": []},
            {**valid, "added_clauses": [[2, 3], [4]]},
            {**valid, "reconstruction_data": {"eliminated_variable": 2}},
            {**valid, "removed_clauses": [[1, 2]]},
        ]:
            with self.assertRaises(ValueError):
                check_ve_step_raw(formula, bad, 2)
        with self.assertRaises(ValueError):
            check_ve_step_raw(formula, valid, 1)
        print("INDEPENDENT_VE_CHECK_PASS")

    def test_independent_component_check(self):
        formula = canonicalize_formula_raw([[1, 2], [3, 4]])
        valid = {
            "type": "CD",
            "output_formula_hash": hash_formula_raw(formula),
            "details": {
                "component_count": 2,
                "incidence_edges": [[1, 0], [2, 0], [3, 1], [4, 1]],
                "components": [
                    {
                        "component_id": "0",
                        "formula_hash": hash_formula_raw(canonicalize_formula_raw([[1, 2]])),
                        "variables": [1, 2],
                        "clauses": [[1, 2]],
                        "clause_indices": [0],
                    },
                    {
                        "component_id": "1",
                        "formula_hash": hash_formula_raw(canonicalize_formula_raw([[3, 4]])),
                        "variables": [3, 4],
                        "clauses": [[3, 4]],
                        "clause_indices": [1],
                    },
                ],
            },
        }
        self.assertEqual(len(check_component_decomposition_raw(formula, valid)), 2)
        fake = json.loads(json.dumps(valid))
        fake["details"]["component_count"] = 1
        with self.assertRaises(ValueError):
            check_component_decomposition_raw(formula, fake)
        cross = json.loads(json.dumps(valid))
        cross["details"]["components"][0]["clauses"] = [[1, 2], [3, 4]]
        with self.assertRaises(ValueError):
            check_component_decomposition_raw(formula, cross)
        print("INDEPENDENT_COMPONENT_CHECK_PASS")

    def test_independent_2sat_check(self):
        sat_formula = canonicalize_formula_raw([[1, 2], [-1, 2]])
        sat_log = {
            "output_formula_hash": hash_formula_raw(sat_formula),
            "details": {"status": "SAT", "assignment": {"1": True, "2": True}},
        }
        self.assertFalse(check_2sat_result_raw(sat_formula, sat_log)[1])
        unsat_formula = canonicalize_formula_raw([[1], [-1]])
        unsat_log = {
            "output_formula_hash": hash_formula_raw(unsat_formula),
            "details": {"status": "UNSAT"},
        }
        self.assertTrue(check_2sat_result_raw(unsat_formula, unsat_log)[1])
        fake_sat = {
            "output_formula_hash": hash_formula_raw(sat_formula),
            "details": {"status": "SAT", "assignment": {"1": False, "2": False}},
        }
        with self.assertRaises(ValueError):
            check_2sat_result_raw(sat_formula, fake_sat)
        print("INDEPENDENT_2SAT_CHECK_PASS")

    def test_independent_tamper_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "bce.wcert"
            export_cert("bce_demo.dimacs", 2, cert)
            result = json.loads((cert / "result.json").read_text(encoding="utf-8"))
            result["reconstructed_original_assignment"] = {
                "1": False,
                "2": False,
                "3": False,
            }
            trace = json.loads((cert / "reconstruction_trace.json").read_text(encoding="utf-8"))
            trace["reconstructed_original_assignment"] = result["reconstructed_original_assignment"]
            (cert / "reconstruction_trace.json").write_text(stable_json_raw(trace), encoding="utf-8")
            sync_certificate_hash(cert, result)
            checked = verify_wcert_raw(cert)
        self.assertFalse(checked["verified"])
        print("INDEPENDENT_TAMPER_REJECT_PASS")

    def test_independent_unsat_limitation(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "bce.wcert"
            export_cert("bce_demo.dimacs", 2, cert)
            result = json.loads((cert / "result.json").read_text(encoding="utf-8"))
            result["status"] = "UNSAT"
            result["final_class"] = "CONFLICT"
            result["original_verification"] = False
            trace = json.loads((cert / "reconstruction_trace.json").read_text(encoding="utf-8"))
            trace["proof_trace_class"] = "UNSAT_INTERNAL_REPLAY"
            collapse = json.loads((cert / "collapse_path.json").read_text(encoding="utf-8"))
            collapse["proof_trace_class"] = "UNSAT_INTERNAL_REPLAY"
            (cert / "reconstruction_trace.json").write_text(stable_json_raw(trace), encoding="utf-8")
            (cert / "collapse_path.json").write_text(stable_json_raw(collapse), encoding="utf-8")
            sync_certificate_hash(cert, result)
            checked = verify_wcert_raw(cert)
        self.assertFalse(checked["verified"])
        self.assertEqual(checked["failed_check"], "unsat_external_certification")
        print("INDEPENDENT_UNSAT_LIMITATION_PASS")


if __name__ == "__main__":
    unittest.main()
