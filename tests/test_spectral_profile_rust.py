"""Independent tiny-case control for W-CROSSDOMAIN-022's Rust CLI."""
import json
import math
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


def reference(variables, clauses):
    positive = [0] * variables
    negative = [0] * variables
    edges = sum(map(len, clauses))
    for clause in clauses:
        for lit in clause:
            (positive if lit > 0 else negative)[abs(lit)-1] += 1
    degree = [a+b for a, b in zip(positive, negative)]
    conflict = 2 * sum(min(a, b) for a, b in zip(positive, negative)) / edges if edges else 0.0
    x = [(positive[i]-negative[i])/math.sqrt(degree[i]) if degree[i] else 0.0
         for i in range(variables)]

    def normalize(values):
        z = math.sqrt(sum(a*a for a in values))
        return [a/z for a in values] if z else None

    x = normalize(x)
    if x is None:
        x = normalize([1.0 if i % 2 == 0 else -1.0 for i in range(variables)]) or []

    def multiply(vec):
        result = [0.0] * variables
        for clause in clauses:
            if not clause:
                continue
            z = sum((1 if lit > 0 else -1) * vec[abs(lit)-1] /
                    math.sqrt(len(clause) * degree[abs(lit)-1]) for lit in clause)
            for lit in clause:
                v = abs(lit)-1
                result[v] += ((1 if lit > 0 else -1) * z /
                              math.sqrt(len(clause) * degree[v]))
        return result

    for _ in range(8):
        y = normalize(multiply(x))
        if y is None:
            break
        x = y
    rayleigh = sum(a*b for a, b in zip(x, multiply(x)))
    ipr = sum(a**4 for a in x)
    return (edges, conflict, rayleigh, ipr)


class RustSpectralProfileControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cli = os.environ.get("WITNORA_RUST_SPECTRAL_BIN")
        if not cli or not Path(cli).exists():
            raise unittest.SkipTest("W022 Rust executable unavailable")
        cls.cli = cli

    def call(self, raw):
        return subprocess.run([self.cli], input=raw, text=True, capture_output=True, check=False)

    def test_tiny_numeric_controls(self):
        cases = [
            (3, [[1,-2,3],[-1,2],[]]),
            (4, [[1,-2],[-1,2],[3,4],[-4,3],[1,-1,-3]]),
            (3, [[1,-2,3],[1,-2,3],[-2],[2]]),
            (0, []),
        ]
        for variables, clauses in cases:
            with self.subTest(variables=variables, clauses=clauses):
                raw = f"c independent W022 fixture\np cnf {variables} {len(clauses)}\n"
                raw += "".join(" ".join(map(str, clause)) + " 0\n" for clause in clauses)
                process = self.call(raw)
                self.assertEqual(process.returncode, 0, process.stderr)
                data = json.loads(process.stdout)
                self.assertEqual(data["variables"], variables)
                self.assertEqual(data["clauses"], len(clauses))
                edges, conflict, rayleigh, ipr = reference(variables, clauses)
                self.assertEqual(data["literal_occurrences"], edges)
                self.assertAlmostEqual(data["polarity_conflict_fraction"], conflict, places=10)
                self.assertAlmostEqual(data["spectral_rayleigh"], rayleigh, places=10)
                self.assertAlmostEqual(data["spectral_inverse_participation"], ipr, places=10)
                self.assertEqual(data["iterations"], 8)

    def test_file_input_and_invalid_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            good = Path(folder) / "case.cnf"
            good.write_text("p cnf 2 2\n1 0\n-2 0\n", encoding="utf-8")
            result = subprocess.run([self.cli, str(good)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["literal_occurrences"], 2)
        for bad in ["p cnf 2 1\n3 0\n", "p cnf 2 2\n1 0\n",
                    "p cnf 2 1\n1 0\n-1 0\n", "p cnf 2 1\n1\n"]:
            with self.subTest(bad=bad):
                self.assertNotEqual(self.call(bad).returncode, 0)


if __name__ == "__main__":
    unittest.main()
