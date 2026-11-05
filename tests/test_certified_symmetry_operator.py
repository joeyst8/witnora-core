import tempfile
import unittest
from pathlib import Path

from witnora_core.collapse_theory import (
    NO_COLLAPSE_FOUND,
    SAT_ASSIGNMENT_VERIFIED,
    SYMMETRY_DIAGNOSTIC_ONLY,
    SYMMETRY_SAT_WITNESS_RECONSTRUCTED,
    build_family_instances,
    build_symmetry_certificate,
    run_symmetry_lab,
)


class CertifiedSymmetryOperatorTest(unittest.TestCase):
    def test_graph_coloring_symmetry_cert(self):
        instance = next(item for item in build_family_instances(["graph-coloring"]) if item.instance_id == "cycle_4_3color")
        cert = build_symmetry_certificate(instance)
        self.assertEqual(cert.status, SYMMETRY_SAT_WITNESS_RECONSTRUCTED)
        self.assertEqual(cert.checker_status, "PASS")
        self.assertEqual(cert.sbp_type, "ORBIT_REPRESENTATIVE")
        print("GRAPH_COLORING_SYMMETRY_CERT_PASS")

    def test_pigeonhole_exact_orbit_signal(self):
        instance = build_family_instances(["pigeonhole"])[0]
        cert = build_symmetry_certificate(instance)
        self.assertEqual(cert.status, SYMMETRY_DIAGNOSTIC_ONLY)
        self.assertEqual(cert.automorphism_validation_status, "VALIDATED")
        self.assertGreaterEqual(max(len(orbit) for orbit in cert.variable_orbits), 4)
        print("PIGEONHOLE_EXACT_ORBIT_SIGNAL_PASS")

    def test_symmetry_lab_operator_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_symmetry_lab(
                families=["symmetric-toy", "graph-coloring", "pigeonhole", "near-symmetry"],
                out_root=Path(tmp) / "symmetry",
            )
            report = (Path(tmp) / "symmetry" / "CERTIFIED_SYMMETRY_COLLAPSE_REPORT.md").read_text(encoding="utf-8")
        rows = result["symmetry_result_summary"]
        cycle = next(row for row in rows if row["instance_id"] == "cycle_4_3color")
        pigeon = next(row for row in rows if row["family"] == "pigeonhole")
        self.assertEqual(cycle["g2_public_category"], SAT_ASSIGNMENT_VERIFIED)
        self.assertEqual(cycle["g2_symmetry_status"], SYMMETRY_SAT_WITNESS_RECONSTRUCTED)
        self.assertEqual(pigeon["g2_public_category"], NO_COLLAPSE_FOUND)
        self.assertIn("does not claim P vs NP progress", report)
        print("OPERATOR_DELTA_SUMMARY_PASS")


if __name__ == "__main__":
    unittest.main()
