"""Independent W027 source-clause audit of the Rust parity precheck."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tests.test_mixed_xor_recovery_rust import SAT, UNSAT, core, make_noise


def write_dimacs(path, clauses, n=64):
    contents = [f"p cnf {n} {len(clauses)}"]
    contents.extend(" ".join(map(str, clause)) + " 0" for clause in clauses)
    path.write_text("\n".join(contents) + "\n", encoding="ascii")


def verify_certificate(clauses, result):
    rows = result.get("contradiction_certificate_rows")
    if not rows:
        return False
    variables_xor = set()
    rhs_xor = 0
    for row in rows:
        triple = row["variables"]
        source = [clauses[i] for i in row["source_clause_indices_zero_based"]]
        assert len(triple) == len(set(triple)) == 3
        assert len(source) == 4
        sign_patterns = set()
        for clause in source:
            assert sorted(map(abs, clause)) == triple
            signs = tuple(1 if next(x for x in clause if abs(x) == v) > 0 else -1 for v in triple)
            sign_patterns.add(signs)
            assert (signs[0] * signs[1] * signs[2] > 0) == row["rhs"]
        assert len(sign_patterns) == 4
        rhs_xor ^= int(row["rhs"])
        for v in triple:
            if v in variables_xor:
                variables_xor.remove(v)
            else:
                variables_xor.add(v)
    return not variables_xor and rhs_xor == 1


class W027PrecheckTests(unittest.TestCase):
    def test_soundness_and_noise_controls(self):
        binary = os.environ.get("WITNORA_W027_PRECHECK_BIN")
        self.assertTrue(binary and Path(binary).is_file(), "set WITNORA_W027_PRECHECK_BIN")
        with tempfile.TemporaryDirectory(prefix="witnora-w027-") as folder:
            path = Path(folder) / "case.cnf"
            for noise_size, replicate in ((0, 0), (256, 1), (8192, 15)):
                _, noise = make_noise(noise_size, replicate)
                for parity, expected in ((SAT, "NO_CERTIFICATE"), (UNSAT, "UNSAT_CERTIFIED")):
                    clauses = core(parity) + noise
                    write_dimacs(path, clauses)
                    result = subprocess.run([binary, str(path)], capture_output=True, text=True, check=True)
                    data = json.loads(result.stdout)
                    with self.subTest(noise=noise_size, replicate=replicate, status=expected):
                        self.assertEqual(data["status"], expected)
                        self.assertEqual(data["recovered_xor_equations"], 5)
                        self.assertEqual(data["clauses"], noise_size + 20)
                        self.assertEqual(data["unsigned_triple_supports"], noise_size + 5)
                        self.assertEqual(bool(data["contradiction_certificate_rows"]), parity == UNSAT)
                        if parity == UNSAT:
                            self.assertTrue(verify_certificate(clauses, data))
                        else:
                            planted = lambda lit: (abs(lit) == 7) == (lit > 0)
                            self.assertTrue(all(any(planted(l) for l in c) for c in clauses))

    def test_incomplete_quartets_are_ignored(self):
        binary = os.environ["WITNORA_W027_PRECHECK_BIN"]
        with tempfile.TemporaryDirectory(prefix="witnora-w027-decoy-") as folder:
            path = Path(folder) / "decoy.cnf"
            clauses = [[1, 2, 3], [-1, -2, 3], [1, -2, -3]]
            write_dimacs(path, clauses, n=3)
            data = json.loads(subprocess.run([binary, str(path)], capture_output=True, text=True, check=True).stdout)
            self.assertEqual(data["status"], "NO_CERTIFICATE")
            self.assertEqual(data["recovered_xor_equations"], 0)


if __name__ == "__main__":
    unittest.main()
