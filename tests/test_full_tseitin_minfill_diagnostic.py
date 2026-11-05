import tempfile
import unittest
from pathlib import Path

from witnora_core.public_benchmarks import UNSAT_DRAT_EXPORTED_VERIFIED, UNSAT_XOR_NATIVE_ONLY
from witnora_core.xor_drat_diagnostic import (
    FULL_TSEITIN_CAP_PROFILES,
    FULL_TSEITIN_MATRIX,
    best_matrix_rows,
    cap_profile_summary_rows,
    drat_verification_summary,
    failures_or_skips,
    family_summary_rows,
    make_zip,
    proof_size_rows,
    public_category_counts,
    report_markdown,
    stable_json,
    summary,
    verified_c_values,
    write_table_csv,
)


def sample_rows():
    return [
        {
            "instance_id": "tseitin_10",
            "family": "tseitin",
            "c": 2,
            "cap_profile": "default",
            "xor_elim_order": "sparse-min-fill",
            "public_category": UNSAT_DRAT_EXPORTED_VERIFIED,
            "xor_drat_status": "VERIFIED",
            "row_width": 8,
            "row_width_peak": 8,
            "peak_row_width": 8,
            "sparse_row_width_peak": 8,
            "proof_clause_count_actual": 10143,
            "proof_file_size_bytes": 388389,
            "drat_trim_runtime_seconds": 0.31,
            "skip_reason": None,
            "external_checker_verified": True,
            "false_drat_claim": False,
            "proof_drat_path": "certs/tseitin_10/proof.drat",
        },
        {
            "instance_id": "tseitin_10",
            "family": "tseitin",
            "c": 3,
            "cap_profile": "default",
            "xor_elim_order": "sparse-min-fill",
            "public_category": UNSAT_DRAT_EXPORTED_VERIFIED,
            "xor_drat_status": "VERIFIED",
            "row_width": 8,
            "row_width_peak": 8,
            "peak_row_width": 8,
            "sparse_row_width_peak": 8,
            "proof_clause_count_actual": 10143,
            "proof_file_size_bytes": 388389,
            "drat_trim_runtime_seconds": 0.31,
            "skip_reason": None,
            "external_checker_verified": True,
            "false_drat_claim": False,
            "proof_drat_path": "certs/tseitin_10_c3/proof.drat",
        },
        {
            "instance_id": "tseitin_10",
            "family": "tseitin",
            "c": 4,
            "cap_profile": "default",
            "xor_elim_order": "sparse-min-fill",
            "public_category": UNSAT_DRAT_EXPORTED_VERIFIED,
            "xor_drat_status": "VERIFIED",
            "row_width": 8,
            "row_width_peak": 8,
            "peak_row_width": 8,
            "sparse_row_width_peak": 8,
            "proof_clause_count_actual": 10143,
            "proof_file_size_bytes": 388389,
            "drat_trim_runtime_seconds": 0.31,
            "skip_reason": None,
            "external_checker_verified": True,
            "false_drat_claim": False,
            "proof_drat_path": "certs/tseitin_10_c4/proof.drat",
        },
        {
            "instance_id": "tseitin_15",
            "family": "tseitin",
            "c": 2,
            "cap_profile": "default",
            "xor_elim_order": "sparse-min-fill",
            "public_category": UNSAT_DRAT_EXPORTED_VERIFIED,
            "xor_drat_status": "VERIFIED",
            "row_width": 8,
            "row_width_peak": 8,
            "peak_row_width": 8,
            "sparse_row_width_peak": 8,
            "proof_clause_count_actual": 3999,
            "proof_file_size_bytes": 124485,
            "drat_trim_runtime_seconds": 0.27,
            "skip_reason": None,
            "external_checker_verified": True,
            "false_drat_claim": False,
            "proof_drat_path": "certs/tseitin_15/proof.drat",
        },
        {
            "instance_id": "tseitin_20",
            "family": "tseitin",
            "c": 2,
            "cap_profile": "default",
            "xor_elim_order": "sparse-min-fill",
            "public_category": UNSAT_XOR_NATIVE_ONLY,
            "xor_drat_status": "SKIPPED_PROOF_SIZE_CAP",
            "row_width": 10,
            "row_width_peak": 10,
            "peak_row_width": 10,
            "sparse_row_width_peak": 10,
            "proof_clause_count_actual": None,
            "proof_file_size_bytes": None,
            "drat_trim_runtime_seconds": None,
            "skip_reason": "proof clause cap exceeded",
            "external_checker_verified": False,
            "false_drat_claim": False,
            "proof_drat_path": "",
        },
    ]


class FullTseitinMinfillDiagnosticTest(unittest.TestCase):
    def test_full_tseitin_minfill_diagnostic_schema(self):
        rows = sample_rows()
        root = Path(tempfile.mkdtemp())
        (root / "manifest.json").write_text(stable_json({"matrix_pairs": FULL_TSEITIN_MATRIX}), encoding="utf-8")
        (root / "public_category_summary.json").write_text(stable_json(public_category_counts(rows)), encoding="utf-8")
        write_table_csv(root / "per_family_summary.csv", family_summary_rows(rows))
        write_table_csv(root / "proof_size_summary.csv", proof_size_rows(rows))
        write_table_csv(root / "cap_profile_summary.csv", cap_profile_summary_rows(rows))
        (root / "best_matrix_public_category_summary.json").write_text(
            stable_json(public_category_counts(best_matrix_rows(rows))), encoding="utf-8"
        )
        (root / "drat_verification_summary.json").write_text(stable_json(drat_verification_summary(rows)), encoding="utf-8")
        (root / "failures_or_skips.json").write_text(stable_json({"rows": failures_or_skips(rows)}), encoding="utf-8")
        (root / "FULL_TSEITIN_MINFILL_DIAGNOSTIC_REPORT.md").write_text(
            report_markdown(rows, summary(rows)), encoding="utf-8"
        )
        digest = make_zip(root, root.parent / "sample-full-tseitin.zip")
        self.assertTrue(digest)
        for name in [
            "manifest.json",
            "public_category_summary.json",
            "per_family_summary.csv",
            "proof_size_summary.csv",
            "cap_profile_summary.csv",
            "best_matrix_public_category_summary.json",
            "drat_verification_summary.json",
            "failures_or_skips.json",
            "FULL_TSEITIN_MINFILL_DIAGNOSTIC_REPORT.md",
        ]:
            self.assertTrue((root / name).exists(), name)
        print("FULL_TSEITIN_MINFILL_DIAGNOSTIC_PASS")

    def test_tseitin10_all_c_values_verified(self):
        self.assertEqual(verified_c_values(sample_rows(), "tseitin_10"), [2, 3, 4])
        print("TSEITIN_10_ALL_C_VALUES_VERIFIED_PASS")

    def test_tseitin15_c2_verified_regression(self):
        self.assertIn(2, verified_c_values(sample_rows(), "tseitin_15"))
        print("TSEITIN_15_C2_VERIFIED_REGRESSION_PASS")

    def test_native_only_no_false_drat(self):
        native_rows = [row for row in sample_rows() if row["public_category"] == UNSAT_XOR_NATIVE_ONLY]
        self.assertTrue(native_rows)
        self.assertTrue(all(not row["false_drat_claim"] for row in native_rows))
        self.assertTrue(all(not row["external_checker_verified"] for row in native_rows))
        print("TSEITIN_NATIVE_ONLY_NO_FALSE_DRAT_PASS")

    def test_public_category_summary(self):
        counts = public_category_counts(sample_rows())
        best_counts = public_category_counts(best_matrix_rows(sample_rows()))
        self.assertEqual(counts[UNSAT_DRAT_EXPORTED_VERIFIED], 4)
        self.assertEqual(counts[UNSAT_XOR_NATIVE_ONLY], 1)
        self.assertEqual(best_counts[UNSAT_DRAT_EXPORTED_VERIFIED], 4)
        self.assertEqual(best_counts[UNSAT_XOR_NATIVE_ONLY], 1)
        self.assertEqual(FULL_TSEITIN_CAP_PROFILES["default"]["max_row_width"], 8)
        self.assertEqual(FULL_TSEITIN_CAP_PROFILES["medium-v098"]["max_row_width"], 10)
        self.assertEqual(FULL_TSEITIN_CAP_PROFILES["high-v098"]["max_row_width"], 12)
        print("FULL_TSEITIN_PUBLIC_CATEGORY_SUMMARY_PASS")


if __name__ == "__main__":
    unittest.main()
