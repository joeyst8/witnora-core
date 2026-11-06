"""Independent Python source-clause audit for the new Rust W030 prefix engine."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tests.test_mixed_xor_recovery_rust import SAT, UNSAT, core, make_noise
from tests.test_w027_precheck import verify_certificate, write_dimacs


def invoke(binary, path):
    return json.loads(subprocess.run([binary, str(path)], check=True,
                                     capture_output=True, text=True).stdout)


class PrefixXorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = os.environ.get("WITNORA_W030_PREFIX_BIN")
        if not cls.binary or not Path(cls.binary).is_file():
            raise RuntimeError("set WITNORA_W030_PREFIX_BIN to the compiled Rust binary")

    def test_matched_controls_and_real_source_proof(self):
        with tempfile.TemporaryDirectory(prefix="witnora-w030-") as folder:
            path = Path(folder) / "case.cnf"
            for noise_size, seed in ((0, 0), (256, 1), (8192, 15)):
                _, noise = make_noise(noise_size, seed)
                for parity in (SAT, UNSAT):
                    clauses = core(parity) + noise
                    write_dimacs(path, clauses)
                    report = invoke(self.binary, path)
                    with self.subTest(noise_size=noise_size, parity=parity):
                        self.assertEqual(report["status"], "UNSAT_CERTIFIED" if parity == UNSAT else "NO_CERTIFICATE")
                        self.assertEqual(report["clauses"], 20 + noise_size)
                        if parity == UNSAT:
                            self.assertLessEqual(report["read_clauses"], 20)
                            self.assertTrue(verify_certificate(clauses, report))
                        else:
                            self.assertEqual(report["read_clauses"], 20 + noise_size)
                            self.assertIsNone(report["contradiction_certificate_rows"])

    def test_late_core_requires_late_evidence(self):
        with tempfile.TemporaryDirectory(prefix="witnora-w030-late-") as folder:
            path = Path(folder) / "case.cnf"
            _, noise = make_noise(256, 2)
            clauses = noise + core(UNSAT)
            write_dimacs(path, clauses)
            report = invoke(self.binary, path)
            self.assertEqual(report["status"], "UNSAT_CERTIFIED")
            self.assertGreater(report["read_clauses"], 256)
            self.assertTrue(verify_certificate(clauses, report))

    def test_exhaustive_cube_corners_and_provenance(self):
        with tempfile.TemporaryDirectory(prefix="witnora-w030-cube-") as folder:
            path = Path(folder) / "case.cnf"
            for mask in range(256):
                clauses = [
                    [-(i + 1) if corner & (1 << i) else i + 1 for i in range(3)]
                    for corner in range(8) if mask & (1 << corner)
                ]
                if clauses:
                    clauses.append(clauses[0][:])
                clauses.reverse()
                write_dimacs(path, clauses, n=3)
                report = invoke(self.binary, path)
                satisfiable = any(
                    all(any(bool(bits & (1 << (abs(lit) - 1))) == (lit > 0)
                            for lit in clause) for clause in clauses)
                    for bits in range(8)
                )
                with self.subTest(corner_mask=mask):
                    self.assertEqual(report["status"], "NO_CERTIFICATE" if satisfiable else "UNSAT_CERTIFIED")
                    if not satisfiable:
                        self.assertTrue(verify_certificate(clauses, report))


if __name__ == "__main__":
    unittest.main()
