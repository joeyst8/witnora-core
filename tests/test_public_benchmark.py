import csv
import os
import tempfile
import unittest
from pathlib import Path

from witnora_core.drat_trim import find_drat_trim
from witnora_core.public_benchmarks import (
    NO_COLLAPSE_FOUND,
    PUBLIC_CSV_COLUMNS,
    SAT_ASSIGNMENT_VERIFIED,
    TIMEOUT,
    UNSAT_DRAT_EXPORTED_VERIFIED,
    UNSAT_NOT_EXTERNALLY_VERIFIED,
    PublicBenchmarkCase,
    generate_public_markdown_report,
    public_suite_cases,
    run_public_benchmark,
    run_public_case,
    write_public_csv,
)


def drat_trim_path():
    return find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM"))


def case_from_dimacs(name, dimacs, family="fixture"):
    return PublicBenchmarkCase(
        instance_name=name,
        source_suite="test-fixtures",
        family=family,
        dimacs_text=dimacs,
        source="test",
    )


class PublicBenchmarkTest(unittest.TestCase):
    def test_public_category_classification(self):
        cases = [
            case_from_dimacs("sat_unit", "p cnf 1 1\n1 0\n", "sat"),
            public_suite_cases("cnfgen-small", max_instances=3)[2],
        ]
        with tempfile.TemporaryDirectory() as tmp:
            data = run_public_benchmark(
                cases,
                2,
                timeout_seconds=30,
                export_certs_dir=Path(tmp) / "certs",
                drat_trim_path=drat_trim_path(),
                timestamp="TEST_TIMESTAMP",
            )
        categories = {item["instance_name"]: item["public_category"] for item in data["per_case_results"]}
        self.assertEqual(categories["sat_unit"], SAT_ASSIGNMENT_VERIFIED)
        self.assertEqual(categories["php_4_3"], NO_COLLAPSE_FOUND)
        print("PUBLIC_CATEGORY_CLASSIFICATION_PASS")

    def test_strict_unsat_external_guard(self):
        unsat = case_from_dimacs("unit_unsat", "p cnf 1 2\n1 0\n-1 0\n", "unsat")
        with tempfile.TemporaryDirectory() as tmp:
            data = run_public_benchmark(
                [unsat],
                2,
                timeout_seconds=30,
                strict_unsat_external=True,
                export_certs_dir=Path(tmp) / "certs",
                timestamp="TEST_TIMESTAMP",
            )
        self.assertFalse(data["strict_unsat_external_pass"])
        self.assertEqual(
            data["per_case_results"][0]["public_category"],
            UNSAT_NOT_EXTERNALLY_VERIFIED,
        )
        with tempfile.TemporaryDirectory() as tmp:
            verified = run_public_benchmark(
                [unsat],
                2,
                timeout_seconds=30,
                strict_unsat_external=True,
                export_certs_dir=Path(tmp) / "certs",
                drat_trim_path=drat_trim_path(),
                timestamp="TEST_TIMESTAMP",
            )
        if drat_trim_path() is not None:
            self.assertTrue(verified["strict_unsat_external_pass"])
            self.assertEqual(
                verified["per_case_results"][0]["public_category"],
                UNSAT_DRAT_EXPORTED_VERIFIED,
            )
        print("STRICT_UNSAT_EXTERNAL_GUARD_PASS")

    def test_public_benchmark_csv_schema(self):
        case = case_from_dimacs("sat_unit", "p cnf 1 1\n1 0\n", "sat")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = run_public_benchmark(
                [case],
                2,
                timeout_seconds=30,
                export_certs_dir=root / "certs",
                timestamp="TEST_TIMESTAMP",
            )
            csv_path = root / "results.csv"
            write_public_csv(data, csv_path)
            with csv_path.open(newline="", encoding="utf-8") as handle:
                reader = csv.reader(handle)
                header = next(reader)
                row = next(reader)
        self.assertEqual(header, PUBLIC_CSV_COLUMNS)
        self.assertEqual(row[header.index("instance_name")], "sat_unit")
        print("PUBLIC_BENCHMARK_CSV_SCHEMA_PASS")

    def test_public_benchmark_report(self):
        cases = [
            case_from_dimacs("sat_unit", "p cnf 1 1\n1 0\n", "sat"),
            public_suite_cases("cnfgen-small", max_instances=1)[0],
        ]
        with tempfile.TemporaryDirectory() as tmp:
            data = run_public_benchmark(
                cases,
                2,
                timeout_seconds=30,
                export_certs_dir=Path(tmp) / "certs",
                drat_trim_path=drat_trim_path(),
                timestamp="TEST_TIMESTAMP",
            )
        report = generate_public_markdown_report(data)
        self.assertIn("## Category Counts", report)
        self.assertIn("## DRAT Verification Summary", report)
        self.assertIn("## Claims Allowed / Claims Forbidden", report)
        print("PUBLIC_BENCHMARK_REPORT_PASS")

    def test_public_benchmark_timeout(self):
        case = case_from_dimacs("timeout_probe", "p cnf 1 1\n1 0\n", "sat")
        result = run_public_case(case, 2, timeout_seconds=0)
        self.assertEqual(result["public_category"], TIMEOUT)
        self.assertEqual(result["status"], TIMEOUT)
        print("PUBLIC_BENCHMARK_TIMEOUT_PASS")

    def test_public_benchmark_cert_paths(self):
        unsat = case_from_dimacs("unit_unsat", "p cnf 1 2\n1 0\n-1 0\n", "unsat")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = run_public_benchmark(
                [unsat],
                2,
                timeout_seconds=30,
                export_certs_dir=root / "certs",
                drat_trim_path=drat_trim_path(),
                timestamp="TEST_TIMESTAMP",
            )
            result = data["per_case_results"][0]
            self.assertTrue(result["wcert_path"])
            self.assertTrue(Path(result["wcert_path"]).exists())
            self.assertTrue(result["proof_drat_path"])
            self.assertTrue(Path(result["proof_drat_path"]).exists())
        print("PUBLIC_BENCHMARK_CERT_PATHS_PASS")


if __name__ == "__main__":
    unittest.main()
