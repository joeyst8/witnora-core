import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from witnora_core.proof import (
    collapse_path_from_result_dict,
    stable_json,
    update_manifest_hashes_for_directory,
    verify_certificate_bundle,
)
from witnora_core.runner import main as runner_main


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def run_export(example_name, c, cert_path):
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        code = runner_main(
            [
                str(EXAMPLES / example_name),
                "--c",
                str(c),
                "--export-cert",
                str(cert_path),
            ]
        )
    return code, json.loads(stdout.getvalue())


class CertificateExportTest(unittest.TestCase):
    def test_cert_export_sat(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "bce.wcert"
            code, result = run_export("bce_demo.dimacs", 2, cert)
            self.assertEqual(code, 0)
            verified = verify_certificate_bundle(cert)
        self.assertEqual(result["status"], "SAT")
        self.assertTrue(verified["verified"], verified)
        print("CERT_EXPORT_SAT_PASS")

    def test_cert_export_unsat(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "unsat.wcert"
            code, result = run_export("unsat_demo.dimacs", 2, cert)
            self.assertEqual(code, 0)
            verified = verify_certificate_bundle(cert)
        self.assertEqual(result["status"], "UNSAT")
        self.assertTrue(verified["verified"], verified)
        print("CERT_EXPORT_UNSAT_PASS")

    def test_cert_export_components(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "components.wcert"
            code, result = run_export("multi_component_demo.dimacs", 2, cert)
            self.assertEqual(code, 0)
            verified = verify_certificate_bundle(cert)
        self.assertEqual(result["final_class"], "COMPONENTS_SOLVED")
        self.assertTrue(verified["verified"], verified)
        print("CERT_EXPORT_COMPONENTS_PASS")

    def test_cert_hash_tamper_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "bce.wcert"
            run_export("bce_demo.dimacs", 2, cert)
            (cert / "certificate_hash.txt").write_text("0" * 64 + "\n", encoding="utf-8")
            verified = verify_certificate_bundle(cert)
        self.assertFalse(verified["verified"])
        print("CERT_HASH_TAMPER_REJECT_PASS")

    def test_collapse_path_tamper_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "bce.wcert"
            run_export("bce_demo.dimacs", 2, cert)
            collapse_path = json.loads((cert / "collapse_path.json").read_text(encoding="utf-8"))
            collapse_path["steps"][0]["removed_clauses"] = [[1, 2]]
            (cert / "collapse_path.json").write_text(stable_json(collapse_path), encoding="utf-8")
            update_manifest_hashes_for_directory(cert)
            verified = verify_certificate_bundle(cert)
        self.assertFalse(verified["verified"])
        print("COLLAPSE_PATH_TAMPER_REJECT_PASS")

    def test_assignment_tamper_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert = Path(tmp) / "bce.wcert"
            run_export("bce_demo.dimacs", 2, cert)

            result = json.loads((cert / "result.json").read_text(encoding="utf-8"))
            result["reconstructed_original_assignment"] = {
                "1": False,
                "2": False,
                "3": False,
            }
            path = collapse_path_from_result_dict(result)
            new_hash = path.certificate_hash
            result["certificate_hash"] = new_hash
            (cert / "result.json").write_text(stable_json(result), encoding="utf-8")

            trace = json.loads((cert / "reconstruction_trace.json").read_text(encoding="utf-8"))
            trace["reconstructed_original_assignment"] = result["reconstructed_original_assignment"]
            (cert / "reconstruction_trace.json").write_text(stable_json(trace), encoding="utf-8")
            (cert / "certificate_hash.txt").write_text(new_hash + "\n", encoding="utf-8")

            manifest = json.loads((cert / "manifest.json").read_text(encoding="utf-8"))
            manifest["certificate_hash"] = new_hash
            (cert / "manifest.json").write_text(stable_json(manifest), encoding="utf-8")
            update_manifest_hashes_for_directory(cert)

            verified = verify_certificate_bundle(cert)
        self.assertFalse(verified["verified"])
        self.assertEqual(verified["failed_check"], "collapse_replay")
        print("ASSIGNMENT_TAMPER_REJECT_PASS")

    def test_cert_determinism(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.wcert"
            second = Path(tmp) / "second.wcert"
            run_export("bce_demo.dimacs", 2, first)
            run_export("bce_demo.dimacs", 2, second)
            first_hash = (first / "certificate_hash.txt").read_text(encoding="utf-8")
            second_hash = (second / "certificate_hash.txt").read_text(encoding="utf-8")
            self.assertEqual(first_hash, second_hash)
            for name in json.loads((first / "manifest.json").read_text(encoding="utf-8"))["files"]:
                self.assertEqual(
                    (first / name).read_text(encoding="utf-8"),
                    (second / name).read_text(encoding="utf-8"),
                )
        print("CERT_DETERMINISM_PASS")


if __name__ == "__main__":
    unittest.main()
