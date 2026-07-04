import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from witnora_core.independent_check import (
    compute_certificate_hash_raw,
    stable_json_raw,
    verify_wcert_raw,
)
from witnora_core.proof import update_manifest_hashes_for_directory
from witnora_core.runner import main as runner_main


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


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
            ]
        )
    return code, json.loads(stdout.getvalue())


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class ProofTraceTest(unittest.TestCase):
    def test_certification_metadata_consistency(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sat_cert = root / "sat.wcert"
            unsat_cert = root / "unsat.wcert"
            no_collapse_cert = root / "no_collapse.wcert"
            export_cert(EXAMPLES / "bce_demo.dimacs", 2, sat_cert)
            export_cert(EXAMPLES / "unsat_demo.dimacs", 2, unsat_cert)
            export_cert(EXAMPLES / "treewidth_demo.dimacs", 1, no_collapse_cert)

            sat_manifest = read_json(sat_cert / "manifest.json")
            sat_result = read_json(sat_cert / "result.json")
            self.assertEqual(sat_result["status"], "SAT")
            self.assertEqual(sat_manifest["unsat_certification_level"], "NOT_UNSAT")
            self.assertEqual(sat_result["unsat_certification_level"], "NOT_UNSAT")
            self.assertEqual(
                sat_result["sat_certification_level"],
                "RECONSTRUCTED_ASSIGNMENT_VERIFIED_ORIGINAL",
            )
            self.assertEqual(
                sat_manifest["proof_trace_class"],
                "SAT_ASSIGNMENT_RECONSTRUCTION",
            )

            unsat_manifest = read_json(unsat_cert / "manifest.json")
            unsat_result = read_json(unsat_cert / "result.json")
            self.assertEqual(unsat_result["status"], "UNSAT")
            self.assertEqual(unsat_manifest["sat_certification_level"], "NOT_SAT")
            self.assertEqual(unsat_result["sat_certification_level"], "NOT_SAT")
            self.assertEqual(
                unsat_result["unsat_certification_level"],
                "EXPLICIT_EMPTY_CLAUSE",
            )

            no_collapse_manifest = read_json(no_collapse_cert / "manifest.json")
            no_collapse_result = read_json(no_collapse_cert / "result.json")
            self.assertEqual(
                no_collapse_result["status"],
                "NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C",
            )
            self.assertEqual(no_collapse_result["sat_certification_level"], "NOT_SAT")
            self.assertEqual(no_collapse_result["unsat_certification_level"], "NOT_UNSAT")
            self.assertEqual(no_collapse_manifest["proof_trace_class"], "NO_COLLAPSE_REPORT")
            self.assertNotIn("proof_trace.json", no_collapse_manifest["files"])
        print("CERTIFICATION_METADATA_CONSISTENCY_PASS")

    def test_native_unsat_trace_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "unsat.wcert"
            export_cert(EXAMPLES / "unsat_demo.dimacs", 2, cert)
            proof_trace = read_json(cert / "proof_trace.json")
            checked = verify_wcert_raw(cert)
        self.assertEqual(proof_trace["proof_trace_format"], "WITNORA_NATIVE_UNSAT_TRACE_V1")
        self.assertEqual(proof_trace["unsat_reason"], "EXPLICIT_EMPTY_CLAUSE")
        self.assertEqual(proof_trace["steps"][0]["derived_empty_clause"], [])
        self.assertTrue(checked["verified"], checked)
        self.assertTrue(checked["checks"]["proof_trace"])
        print("NATIVE_UNSAT_TRACE_EMPTY_PASS")

    def test_native_unsat_trace_2sat(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "scc_unsat.dimacs"
            dimacs.write_text(
                "\n".join(
                    [
                        "p cnf 2 4",
                        "1 2 0",
                        "1 -2 0",
                        "-1 2 0",
                        "-1 -2 0",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            cert = root / "scc_unsat.wcert"
            code, result = export_cert(dimacs, 2, cert)
            proof_trace = read_json(cert / "proof_trace.json")
            checked = verify_wcert_raw(cert)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "UNSAT")
        self.assertEqual(result["unsat_certification_level"], "INDEPENDENT_2SAT_SCC")
        self.assertEqual(proof_trace["unsat_reason"], "INDEPENDENT_2SAT_SCC")
        self.assertEqual(proof_trace["positive_literal_scc"], proof_trace["negative_literal_scc"])
        self.assertTrue(proof_trace["implication_edges"])
        self.assertTrue(checked["verified"], checked)
        self.assertTrue(checked["checks"]["proof_trace"])
        print("NATIVE_UNSAT_TRACE_2SAT_PASS")

    def test_native_unsat_trace_tamper_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "unsat.wcert"
            export_cert(EXAMPLES / "unsat_demo.dimacs", 2, cert)
            proof_trace = read_json(cert / "proof_trace.json")
            proof_trace["steps"][0]["derived_empty_clause"] = [1]
            (cert / "proof_trace.json").write_text(
                stable_json_raw(proof_trace),
                encoding="utf-8",
            )
            update_manifest_hashes_for_directory(cert)
            checked = verify_wcert_raw(cert)
        self.assertFalse(checked["verified"])
        self.assertEqual(checked["failed_check"], "proof_trace")
        print("NATIVE_UNSAT_TRACE_TAMPER_REJECT_PASS")

    def test_proof_trace_cert_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "unsat.wcert"
            export_cert(EXAMPLES / "unsat_demo.dimacs", 2, cert)
            manifest = read_json(cert / "manifest.json")
            result = read_json(cert / "result.json")
            without_trace = dict(result)
            without_trace["native_proof_trace"] = None
        self.assertIn("proof_trace.json", manifest["files"])
        self.assertIn("native_proof_trace", result)
        self.assertNotEqual(
            compute_certificate_hash_raw(without_trace),
            manifest["certificate_hash"],
        )
        print("PROOF_TRACE_CERT_BUNDLE_PASS")

    def test_no_false_lrat_frat_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "unsat.wcert"
            export_cert(EXAMPLES / "unsat_demo.dimacs", 2, cert)
            manifest = read_json(cert / "manifest.json")
            proof_trace = read_json(cert / "proof_trace.json")
        self.assertIs(manifest["external_lrat_frat"], False)
        self.assertIs(manifest["verification_levels"]["external_lrat_frat"], False)
        self.assertEqual(proof_trace["external_standard"], "NONE")
        self.assertEqual(proof_trace["lrat_frat_status"], "NOT_EXPORTED")
        self.assertNotEqual(
            manifest["unsat_certification_level"],
            "LRAT_FRAT_NOT_IMPLEMENTED",
        )
        print("NO_FALSE_LRAT_FRAT_CLAIM_PASS")


if __name__ == "__main__":
    unittest.main()
