import contextlib
import io
import json
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path

from witnora_core.independent_check import (
    compute_certificate_hash_raw,
    stable_json_raw,
    verify_unsat_certificate_end_to_end_raw,
    verify_wcert_raw,
)
from witnora_core.runner import main as runner_main


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


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
            ]
        )
    return code, json.loads(stdout.getvalue())


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def hash_text(text):
    return sha256(text.encode("utf-8")).hexdigest()


def rewrite_manifest_hashes(cert_path):
    manifest_path = cert_path / "manifest.json"
    manifest = read_json(manifest_path)
    for name in sorted(manifest["files"]):
        manifest["files"][name]["sha256"] = hash_text(
            (cert_path / name).read_text(encoding="utf-8")
        )
    manifest_path.write_text(stable_json_raw(manifest), encoding="utf-8")


def write_synced_result(cert_path, result, collapse_payload=None):
    if collapse_payload is None:
        collapse_payload = read_json(cert_path / "collapse_path.json")
    result["certificate_hash"] = compute_certificate_hash_raw(result)
    (cert_path / "result.json").write_text(stable_json_raw(result), encoding="utf-8")
    (cert_path / "collapse_path.json").write_text(
        stable_json_raw(collapse_payload),
        encoding="utf-8",
    )
    (cert_path / "certificate_hash.txt").write_text(
        result["certificate_hash"] + "\n",
        encoding="utf-8",
    )
    manifest_path = cert_path / "manifest.json"
    manifest = read_json(manifest_path)
    manifest["certificate_hash"] = result["certificate_hash"]
    manifest["status"] = result["status"]
    manifest["final_class"] = result["final_class"]
    manifest["sat_certification_level"] = result["sat_certification_level"]
    manifest["unsat_certification_level"] = result["unsat_certification_level"]
    manifest["proof_trace_class"] = result["proof_trace_class"]
    manifest_path.write_text(stable_json_raw(manifest), encoding="utf-8")
    rewrite_manifest_hashes(cert_path)


def set_step(result, collapse_payload, step_index, updater):
    updater(result["collapse_path"][step_index])
    updater(collapse_payload["steps"][step_index])


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


class UnsatPathDependencyTest(unittest.TestCase):
    def test_unsat_rejects_fake_bce_even_with_valid_final_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "bce_plus_scc_unsat.dimacs"
            write_dimacs(
                dimacs,
                [
                    [1, 2, 3],
                    [-1, -2],
                    [-1, -3],
                    [4, 5],
                    [4, -5],
                    [-4, 5],
                    [-4, -5],
                    [3, 4],
                ],
                5,
            )
            cert = root / "case.wcert"
            _code, result = export_cert(dimacs, 2, cert)
            self.assertEqual(result["status"], "UNSAT")

            result = read_json(cert / "result.json")
            collapse = read_json(cert / "collapse_path.json")
            bce_index = next(
                idx
                for idx, step in enumerate(result["collapse_path"])
                if step["type"] == "BCE"
            )

            def corrupt_bce(step):
                step["removed_clauses"] = [[1, 2]]
                step["details"]["removed_clause"] = [1, 2]
                step["reconstruction_data"]["removed_clause"] = [1, 2]

            set_step(result, collapse, bce_index, corrupt_bce)
            write_synced_result(cert, result, collapse)
            checked = verify_unsat_certificate_end_to_end_raw(cert)
        self.assertFalse(checked["verified"])
        self.assertEqual(checked["failed_check"], "collapse_path_replayed_from_original")
        print("UNSAT_REJECTS_FAKE_BCE_EVEN_WITH_VALID_FINAL_TRACE_PASS")

    def test_unsat_rejects_missing_ve_resolvent_even_with_valid_final_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "ve_unsat.dimacs"
            write_dimacs(dimacs, full_3var_unsat_clauses(), 3)
            cert = root / "case.wcert"
            _code, result = export_cert(dimacs, 2, cert)
            self.assertEqual(result["status"], "UNSAT")
            self.assertEqual(result["native_proof_trace"]["steps"][0]["type"], "VE_EMPTY_RESOLVENT")

            result = read_json(cert / "result.json")
            collapse = read_json(cert / "collapse_path.json")
            ve_index = next(
                idx
                for idx, step in enumerate(result["collapse_path"])
                if step["type"] == "VE" and len(step["added_clauses"]) > 1
            )

            def corrupt_ve(step):
                step["added_clauses"] = step["added_clauses"][:-1]
                step["details"]["added_resolvents"] = step["details"]["added_resolvents"][:-1]
                step["reconstruction_data"]["added_resolvents"] = step["reconstruction_data"][
                    "added_resolvents"
                ][:-1]

            set_step(result, collapse, ve_index, corrupt_ve)
            write_synced_result(cert, result, collapse)
            checked = verify_unsat_certificate_end_to_end_raw(cert)
        self.assertFalse(checked["verified"])
        self.assertEqual(checked["failed_check"], "collapse_path_replayed_from_original")
        print("UNSAT_REJECTS_MISSING_VE_RESOLVENT_EVEN_WITH_VALID_FINAL_TRACE_PASS")

    def test_unsat_rejects_fake_2sat_scc_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "sat_2sat.dimacs"
            write_dimacs(dimacs, [[1, 2], [-1, 3], [-2, -3]], 3)
            cert = root / "case.wcert"
            _code, result = export_cert(dimacs, 2, cert)
            self.assertEqual(result["status"], "SAT")

            result = read_json(cert / "result.json")
            collapse = read_json(cert / "collapse_path.json")
            fake_trace = {
                "proof_trace_format": "WITNORA_NATIVE_UNSAT_TRACE_V1",
                "unsat_reason": "INDEPENDENT_2SAT_SCC",
                "depends_on_replayed_collapse_path": True,
                "source_step_id": 1,
                "variable": 1,
                "positive_literal_scc": [1, -1],
                "negative_literal_scc": [1, -1],
                "implication_edges": [[-1, 2], [-2, 1]],
                "external_standard": "NONE",
                "lrat_frat_status": "NOT_EXPORTED",
            }
            result.update(
                {
                    "status": "UNSAT",
                    "final_class": "CONFLICT",
                    "original_verification": False,
                    "reconstructed_original_assignment": {},
                    "sat_certification_level": "NOT_SAT",
                    "unsat_certification_level": "INDEPENDENT_2SAT_SCC",
                    "proof_trace_class": "UNSAT_2SAT_SCC_CONTRADICTION",
                    "native_proof_trace": fake_trace,
                }
            )
            for payload in [result["collapse_path"][0], collapse["steps"][0]]:
                payload["details"]["status"] = "UNSAT"
                payload["details"]["conflict_variable"] = 1
                payload["details"]["sccs"] = [[-1, 1]]
                payload["details"]["edges"] = fake_trace["implication_edges"]
            collapse["proof_trace_class"] = "UNSAT_2SAT_SCC_CONTRADICTION"
            trace = read_json(cert / "reconstruction_trace.json")
            trace["proof_trace_class"] = "UNSAT_2SAT_SCC_CONTRADICTION"
            (cert / "reconstruction_trace.json").write_text(
                stable_json_raw(trace),
                encoding="utf-8",
            )
            (cert / "proof_trace.json").write_text(
                stable_json_raw(fake_trace),
                encoding="utf-8",
            )
            manifest = read_json(cert / "manifest.json")
            manifest["files"]["proof_trace.json"] = {"sha256": ""}
            (cert / "manifest.json").write_text(stable_json_raw(manifest), encoding="utf-8")
            write_synced_result(cert, result, collapse)
            checked = verify_unsat_certificate_end_to_end_raw(cert)
        self.assertFalse(checked["verified"])
        self.assertEqual(checked["failed_check"], "collapse_path_replayed_from_original")
        print("UNSAT_REJECTS_FAKE_2SAT_SCC_TRACE_PASS")

    def test_unsat_rejects_fake_component_split_with_valid_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "components_unsat.dimacs"
            write_dimacs(
                dimacs,
                [
                    [1, 2],
                    [1, -2],
                    [-1, 2],
                    [-1, -2],
                    [3, 4],
                    [3, -4],
                    [-3, 4],
                    [-3, -4],
                ],
                4,
            )
            cert = root / "case.wcert"
            _code, result = export_cert(dimacs, 2, cert)
            self.assertEqual(result["status"], "UNSAT")

            result = read_json(cert / "result.json")
            collapse = read_json(cert / "collapse_path.json")
            cd_index = next(
                idx
                for idx, step in enumerate(result["collapse_path"])
                if step["type"] == "CD"
            )

            def corrupt_cd(step):
                step["details"]["component_count"] = step["details"]["component_count"] + 1

            set_step(result, collapse, cd_index, corrupt_cd)
            write_synced_result(cert, result, collapse)
            checked = verify_unsat_certificate_end_to_end_raw(cert)
        self.assertFalse(checked["verified"])
        self.assertEqual(checked["failed_check"], "collapse_path_replayed_from_original")
        print("UNSAT_REJECTS_FAKE_COMPONENT_SPLIT_WITH_VALID_TRACE_PASS")

    def test_unsat_empty_from_ve_unsupported_or_derived(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dimacs = root / "ve_unsat.dimacs"
            write_dimacs(dimacs, full_3var_unsat_clauses(), 3)
            cert = root / "case.wcert"
            _code, result = export_cert(dimacs, 2, cert)
            checked = verify_unsat_certificate_end_to_end_raw(cert)
        self.assertEqual(result["status"], "UNSAT")
        self.assertEqual(result["native_proof_trace"]["steps"][0]["type"], "VE_EMPTY_RESOLVENT")
        self.assertTrue(checked["verified"], checked)
        self.assertTrue(checked["checks"]["ve_steps_recomputed"])
        self.assertTrue(checked["checks"]["proof_trace_checked_against_replayed_final_state"])
        print("UNSAT_EMPTY_FROM_VE_UNSUPPORTED_OR_DERIVED_PASS")


if __name__ == "__main__":
    unittest.main()
