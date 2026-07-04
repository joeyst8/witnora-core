import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from witnora_core.cnfgen_matrix import (
    REASON_OFFICIAL_CNFGEN_NOT_AVAILABLE,
    generate_cnfgen_family_cases,
    summarize_matrix_run,
    write_matrix_artifact,
)
from witnora_core.public_benchmarks import (
    NO_COLLAPSE_FOUND,
    PUBLIC_CATEGORIES,
    SAT_ASSIGNMENT_VERIFIED,
    UNSAT_DRAT_EXPORTED_VERIFIED,
)


def sample_public_data():
    return {
        "suite_status": "RUN",
        "not_run_reason": None,
        "summary": {
            "total_cases": 3,
            "category_counts": {
                category: (
                    1
                    if category
                    in {
                        SAT_ASSIGNMENT_VERIFIED,
                        UNSAT_DRAT_EXPORTED_VERIFIED,
                        NO_COLLAPSE_FOUND,
                    }
                    else 0
                )
                for category in PUBLIC_CATEGORIES
            },
            "strict_unsat_external_pass": True,
            "externally_verified_unsat_count": 1,
            "average_collapse_path_length": 2.0,
        },
        "per_case_results": [
            {
                "instance_name": "php_3_2",
                "public_category": UNSAT_DRAT_EXPORTED_VERIFIED,
                "solver_time_seconds": 0.1,
                "drat_trim_time_seconds": 0.02,
            },
            {
                "instance_name": "php_4_3",
                "public_category": SAT_ASSIGNMENT_VERIFIED,
                "solver_time_seconds": 0.2,
                "drat_trim_time_seconds": None,
            },
            {
                "instance_name": "php_5_4",
                "public_category": NO_COLLAPSE_FOUND,
                "solver_time_seconds": 0.3,
                "drat_trim_time_seconds": None,
            },
        ],
    }


class CNFgenMatrixTest(unittest.TestCase):
    def test_matrix_summary_schema(self):
        row = summarize_matrix_run("pigeonhole", 2, sample_public_data())
        required = {
            "family",
            "c_parameter",
            "total_cases",
            "strict_unsat_external_pass",
            "externally_verified_unsat_count",
            "max_instance_solved",
            "first_no_collapse_instance",
            "average_solver_time_seconds",
            "average_drat_trim_time_seconds",
            "average_collapse_path_length",
        }
        self.assertTrue(required.issubset(row))
        for category in PUBLIC_CATEGORIES:
            self.assertIn(category, row)
        print("CNFGEN_MATRIX_SCHEMA_PASS")

    def test_not_run_family(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases, manifest = generate_cnfgen_family_cases(
                "pigeonhole",
                Path(tmp) / "generated_dimacs",
                cnfgen_path=Path(tmp) / "missing-cnfgen",
            )
        self.assertEqual(cases, [])
        self.assertEqual(manifest["not_run_reason"], REASON_OFFICIAL_CNFGEN_NOT_AVAILABLE)
        print("CNFGEN_NOT_RUN_FAMILY_PASS")

    def test_largest_solved_and_first_no_collapse(self):
        row = summarize_matrix_run("pigeonhole", 3, sample_public_data())
        self.assertEqual(row["max_instance_solved"], "php_4_3")
        self.assertEqual(row["first_no_collapse_instance"], "php_5_4")
        print("CNFGEN_LARGEST_SOLVED_PASS")

    def test_diagnostic_artifact_zip(self):
        row = summarize_matrix_run("pigeonhole", 2, sample_public_data())
        summary = {
            "version": "0.9.1",
            "cnfgen_version": "CNFgen (fixture)",
            "cnfgen_path": "fixture-cnfgen",
            "drat_trim_path": "fixture-drat-trim",
            "timeout_seconds": 300,
            "strict_unsat_external": True,
            "c_values": [2],
            "rows": [row],
            "not_run_reasons": {},
            "commands_run": ["cnfgen php 3 2"],
            "config": {"c_values": [2]},
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "outputs" / "v0.9.1-cnfgen-diagnostic"
            zip_path = root / "witnora-core-v0.9.1-cnfgen-diagnostic-benchmark.zip"
            write_matrix_artifact(artifact, summary, zip_path=zip_path)
            self.assertTrue((artifact / "matrix_summary.json").exists())
            self.assertTrue((artifact / "matrix_summary.csv").exists())
            self.assertTrue((artifact / "MATRIX_SUMMARY.md").exists())
            self.assertTrue(zip_path.exists())
            with zipfile.ZipFile(zip_path) as archive:
                names = set(archive.namelist())
            self.assertIn("outputs/v0.9.1-cnfgen-diagnostic/matrix_summary.json", names)
            loaded = json.loads((artifact / "matrix_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(loaded["version"], "0.9.1")
        print("CNFGEN_DIAGNOSTIC_ARTIFACT_PASS")


if __name__ == "__main__":
    unittest.main()
