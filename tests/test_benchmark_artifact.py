import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from witnora_core.benchmark_artifact import (
    create_artifact_zip,
    selected_instances_text,
    strict_verification_summary,
    write_benchmark_artifact,
)
from witnora_core.public_benchmarks import (
    PUBLIC_CATEGORIES,
    SAT_ASSIGNMENT_VERIFIED,
    UNSAT_DRAT_EXPORTED_VERIFIED,
    UNSAT_NOT_EXTERNALLY_VERIFIED,
)


def sample_benchmark_data():
    return {
        "version": "0.8.2",
        "benchmark_kind": "public",
        "c_parameter": 2,
        "timeout_seconds": 30,
        "max_width_search_vars": 28,
        "strict_unsat_external": True,
        "strict_unsat_external_pass": False,
        "strict_unsat_external_failures": ["unsat_unverified"],
        "cases": [
            {
                "instance_name": "sat_case",
                "source_suite": "fixture",
                "family": "sat",
                "source": "test",
            },
            {
                "instance_name": "unsat_verified",
                "source_suite": "fixture",
                "family": "unsat",
                "source": "test",
            },
            {
                "instance_name": "unsat_unverified",
                "source_suite": "fixture",
                "family": "unsat",
                "source": "test",
            },
        ],
        "per_case_results": [
            {
                "instance_name": "sat_case",
                "source_suite": "fixture",
                "family": "sat",
                "public_category": SAT_ASSIGNMENT_VERIFIED,
                "status": "SAT",
                "final_class": "EMPTY",
                "c_parameter": 2,
                "strict_unsat_external_pass": True,
            },
            {
                "instance_name": "unsat_verified",
                "source_suite": "fixture",
                "family": "unsat",
                "public_category": UNSAT_DRAT_EXPORTED_VERIFIED,
                "status": "UNSAT",
                "final_class": "CONFLICT",
                "c_parameter": 2,
                "strict_unsat_external_pass": True,
                "drat_export_status": "EXPORTED",
                "external_checker": "DRAT_TRIM",
                "external_checker_ran": True,
                "external_checker_verified": True,
            },
            {
                "instance_name": "unsat_unverified",
                "source_suite": "fixture",
                "family": "unsat",
                "public_category": UNSAT_NOT_EXTERNALLY_VERIFIED,
                "status": "UNSAT",
                "final_class": "CONFLICT",
                "c_parameter": 2,
                "strict_unsat_external_pass": False,
                "drat_export_status": "EXPORTED",
                "external_checker": "NOT_RUN",
                "external_checker_ran": False,
                "external_checker_verified": False,
            },
        ],
        "summary": {
            "total_cases": 3,
            "category_counts": {
                category: (
                    1
                    if category
                    in {
                        SAT_ASSIGNMENT_VERIFIED,
                        UNSAT_DRAT_EXPORTED_VERIFIED,
                        UNSAT_NOT_EXTERNALLY_VERIFIED,
                    }
                    else 0
                )
                for category in PUBLIC_CATEGORIES
            },
            "strict_unsat_external_pass": False,
            "strict_unsat_external_failures": ["unsat_unverified"],
            "unsat_total": 2,
            "externally_verified_unsat_count": 1,
            "unverified_unsat_count": 1,
            "unsupported_drat_count": 0,
            "timeout_count": 0,
            "error_count": 0,
            "average_collapse_path_length": 1,
            "average_clause_reduction_pct": 0,
            "average_variable_reduction_pct": 0,
        },
    }


class BenchmarkArtifactTest(unittest.TestCase):
    def test_public_artifact_schema(self):
        data = sample_benchmark_data()
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "outputs" / "v0.8.2-public-benchmark"
            write_benchmark_artifact(
                artifact,
                data,
                config={"c_parameter": 2},
                sources_not_run=[{"suite": "SATLIB", "reason": "directory not provided"}],
                benchmark_commands=["python -m witnora_core.benchmark ..."],
            )
            required = [
                "README.md",
                "benchmark_manifest.json",
                "config.json",
                "results.csv",
                "results.json",
                "REPORT.md",
                "version.txt",
                "selected_instances.txt",
                "environment.txt",
                "strict_verification_summary.json",
                "drat_logs",
                "certs",
                "generated_dimacs",
                "raw_outputs",
            ]
            for name in required:
                self.assertTrue((artifact / name).exists(), name)
        print("PUBLIC_ARTIFACT_SCHEMA_PASS")

    def test_strict_verification_summary(self):
        summary = strict_verification_summary(sample_benchmark_data())
        self.assertFalse(summary["strict_unsat_external_pass"])
        self.assertEqual(summary["drat_trim_verified_unsat_count"], 1)
        self.assertEqual(summary["unverified_unsat_count"], 1)
        self.assertEqual(summary["uncertified_unsat_instances"][0]["instance_name"], "unsat_unverified")
        print("STRICT_VERIFICATION_SUMMARY_PASS")

    def test_selected_instances_file(self):
        text = selected_instances_text(sample_benchmark_data())
        self.assertIn("instance_name\tsource_suite\tfamily\tsource_type", text)
        self.assertIn("sat_case\tfixture\tsat\t\ttest\t\t\tSAT_ASSIGNMENT_VERIFIED\tSAT", text)
        print("SELECTED_INSTANCES_FILE_PASS")

    def test_benchmark_artifact_zip(self):
        data = sample_benchmark_data()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "outputs" / "v0.8.2-public-benchmark"
            write_benchmark_artifact(artifact, data, config={"c_parameter": 2})
            zip_path = root / "witnora-core-v0.8.2-public-benchmark.zip"
            create_artifact_zip(artifact, zip_path)
            self.assertTrue(zip_path.exists())
            with zipfile.ZipFile(zip_path) as archive:
                names = set(archive.namelist())
            self.assertIn("outputs/v0.8.2-public-benchmark/README.md", names)
            self.assertIn("outputs/v0.8.2-public-benchmark/results.csv", names)
            self.assertIn("outputs/v0.8.2-public-benchmark/strict_verification_summary.json", names)
        print("BENCHMARK_ARTIFACT_ZIP_PASS")


if __name__ == "__main__":
    unittest.main()
