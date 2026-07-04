import gzip
import json
import tempfile
import unittest
from pathlib import Path

from witnora_core.benchmark_artifact import benchmark_manifest, write_benchmark_artifact
from witnora_core.public_benchmarks import (
    REASON_DIMACS_DIRECTORY_NOT_FOUND,
    REASON_OFFICIAL_CNFGEN_NOT_AVAILABLE,
    SOURCE_OFFICIAL_CNFGEN,
    SOURCE_SATCOMP_DIRECTORY,
    SOURCE_SATLIB_DIRECTORY,
    SUITE_NOT_RUN,
    dimacs_dir_cases,
    missing_suite_data,
    official_cnfgen_cases,
    read_dimacs_text,
    selected_dimacs_paths,
)


class OfficialPublicBenchmarkTest(unittest.TestCase):
    def test_official_cnfgen_missing_not_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases, manifest = official_cnfgen_cases(
                Path(tmp) / "generated_dimacs",
                cnfgen_path=Path(tmp) / "missing-cnfgen",
            )
        self.assertEqual(cases, [])
        self.assertEqual(manifest["suite_status"], SUITE_NOT_RUN)
        self.assertEqual(manifest["not_run_reason"], REASON_OFFICIAL_CNFGEN_NOT_AVAILABLE)
        self.assertIn("pip install cnfgen", manifest["instructions"])
        print("OFFICIAL_CNFGEN_MISSING_NOT_RUN_PASS")

    def test_satlib_missing_not_run(self):
        data = missing_suite_data(
            "satlib",
            REASON_DIMACS_DIRECTORY_NOT_FOUND,
            SOURCE_SATLIB_DIRECTORY,
            2,
            message="DIMACS directory not found",
        )
        self.assertEqual(data["suite_status"], SUITE_NOT_RUN)
        self.assertEqual(data["not_run_reason"], REASON_DIMACS_DIRECTORY_NOT_FOUND)
        self.assertEqual(data["summary"]["total_cases"], 0)
        print("SATLIB_MISSING_NOT_RUN_PASS")

    def test_satcomp_missing_not_run(self):
        data = missing_suite_data(
            "satcomp",
            REASON_DIMACS_DIRECTORY_NOT_FOUND,
            SOURCE_SATCOMP_DIRECTORY,
            2,
            message="DIMACS directory not found",
        )
        self.assertEqual(data["suite_status"], SUITE_NOT_RUN)
        self.assertEqual(data["not_run_reason"], REASON_DIMACS_DIRECTORY_NOT_FOUND)
        self.assertEqual(data["summary"]["total_cases"], 0)
        print("SATCOMP_MISSING_NOT_RUN_PASS")

    def test_benchmark_manifest_schema(self):
        data = missing_suite_data(
            "cnfgen-official",
            REASON_OFFICIAL_CNFGEN_NOT_AVAILABLE,
            SOURCE_OFFICIAL_CNFGEN,
            2,
        )
        config = {
            "witnora_version": "0.8.5",
            "commit": "abc",
            "tag": "v0.8.5",
            "suite_name": "cnfgen-official",
            "suite_source_type": SOURCE_OFFICIAL_CNFGEN,
            "suite_status": SUITE_NOT_RUN,
            "not_run_reason": REASON_OFFICIAL_CNFGEN_NOT_AVAILABLE,
            "c_parameter": 2,
            "timeout_seconds": 300,
            "max_instances": 50,
            "max_width_search_vars": 28,
            "strict_unsat_external": True,
        }
        manifest = benchmark_manifest(data, config, [])
        required = {
            "witnora_version",
            "commit",
            "tag",
            "benchmark_run_id",
            "run_timestamp",
            "suite_name",
            "suite_source_type",
            "suite_status",
            "not_run_reason",
            "instance_count",
            "selected_instances",
            "generation_commands",
            "dimacs_source_paths",
            "drat_trim_path",
            "strict_unsat_external",
            "c_parameter",
            "timeout_seconds",
            "max_instances",
            "max_width_search_vars",
        }
        self.assertTrue(required.issubset(manifest))
        self.assertEqual(manifest["suite_status"], SUITE_NOT_RUN)
        print("BENCHMARK_MANIFEST_SCHEMA_PASS")

    def test_deterministic_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "b.cnf").write_text("p cnf 1 1\n1 0\n", encoding="utf-8")
            (root / "a.cnf").write_text("p cnf 1 1\n1 0\n", encoding="utf-8")
            sub = root / "sub"
            sub.mkdir()
            (sub / "c.cnf").write_text("p cnf 1 1\n1 0\n", encoding="utf-8")
            first = [path.relative_to(root).as_posix() for path in selected_dimacs_paths(root)]
            second = [path.relative_to(root).as_posix() for path in selected_dimacs_paths(root)]
        self.assertEqual(first, second)
        self.assertEqual(first, ["a.cnf", "b.cnf", "sub/c.cnf"])
        print("DETERMINISTIC_SELECTION_PASS")

    def test_cnf_gz_reading(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tiny.cnf.gz"
            with gzip.open(path, "wt", encoding="utf-8") as handle:
                handle.write("p cnf 1 1\n1 0\n")
            text = read_dimacs_text(path)
            cases = dimacs_dir_cases(tmp, source_suite="satlib", source_type=SOURCE_SATLIB_DIRECTORY)
        self.assertEqual(text, "p cnf 1 1\n1 0\n")
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0].dimacs_text, text)
        print("CNF_GZ_READING_PASS")

    def test_official_artifact_layout(self):
        data = missing_suite_data(
            "cnfgen-official",
            REASON_OFFICIAL_CNFGEN_NOT_AVAILABLE,
            SOURCE_OFFICIAL_CNFGEN,
            2,
        )
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "outputs" / "v0.8.5-public-benchmark" / "cnfgen-official"
            write_benchmark_artifact(
                artifact,
                data,
                config={
                    "witnora_version": "0.8.5",
                    "suite_name": "cnfgen-official",
                    "suite_source_type": SOURCE_OFFICIAL_CNFGEN,
                    "suite_status": SUITE_NOT_RUN,
                    "not_run_reason": REASON_OFFICIAL_CNFGEN_NOT_AVAILABLE,
                    "c_parameter": 2,
                },
            )
            required = [
                "README.md",
                "benchmark_manifest.json",
                "config.json",
                "selected_instances.txt",
                "results.csv",
                "results.json",
                "REPORT.md",
                "strict_verification_summary.json",
                "environment.txt",
                "generated_dimacs",
                "certs",
                "drat_logs",
                "raw_outputs",
            ]
            for name in required:
                self.assertTrue((artifact / name).exists(), name)
            manifest = json.loads((artifact / "benchmark_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["suite_status"], SUITE_NOT_RUN)
        print("OFFICIAL_ARTIFACT_LAYOUT_PASS")


if __name__ == "__main__":
    unittest.main()
