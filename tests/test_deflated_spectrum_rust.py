"""Independent Python mathematics and gauge checks for W-CROSSDOMAIN-023."""
import json
import math
import os
import subprocess
import unittest
from pathlib import Path


def normalize(values):
    length = math.sqrt(sum(x*x for x in values))
    return [x/length for x in values] if length else None


def independent_features(n, clauses):
    positive = [0]*n
    negative = [0]*n
    for clause in clauses:
        for lit in clause:
            if lit > 0:
                positive[abs(lit)-1] += 1
            else:
                negative[abs(lit)-1] += 1
    degree = [p+m for p, m in zip(positive, negative)]
    g = normalize([(positive[v]-negative[v])/math.sqrt(degree[v])
                   if degree[v] else 0.0 for v in range(n)])
    if g is None:
        return (None, None)

    def times_btb(x):
        out = [0.0]*n
        for clause in clauses:
            if not clause:
                continue
            z = 0.0
            for lit in clause:
                v = abs(lit)-1
                z += (1 if lit > 0 else -1)*x[v]/math.sqrt(len(clause)*degree[v])
            for lit in clause:
                v = abs(lit)-1
                out[v] += (1 if lit > 0 else -1)*z/math.sqrt(len(clause)*degree[v])
        return out

    def inner(a,b):
        return sum(x*y for x,y in zip(a,b))

    def project(x):
        alpha = inner(x,g)
        return normalize([xv-alpha*gv for xv,gv in zip(x,g)])

    gauge_defect = max(0.0, min(1.0, 1.0-inner(g,times_btb(g))))
    x = project([gv*((v%5)-2) for v,gv in enumerate(g)])
    if x is None:
        x = project([gv*((v%7)-3) for v,gv in enumerate(g)])
    if x is None:
        return (gauge_defect, None)
    for _ in range(12):
        y = project(times_btb(x))
        if y is None:
            break
        x = y
    return (gauge_defect, max(0.0,min(1.0,inner(x,times_btb(x)))))


class DeflatedRustDifferential(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        binary = os.environ.get("WITNORA_RUST_DEFLATED_BIN")
        if not binary or not Path(binary).exists():
            raise unittest.SkipTest("W023 compiled binary missing")
        cls.binary = binary

    def run_case(self,n,clauses):
        raw = f"c independent control\np cnf {n} {len(clauses)}\n"
        raw += "".join(" ".join(str(lit) for lit in c)+" 0\n" for c in clauses)
        result = subprocess.run([self.binary],input=raw,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        return json.loads(result.stdout)

    def test_numerical_replay(self):
        source = [
            (4,[[1,-2,3],[-1,2,4],[1,3],[-2,-4],[2,3,4]]),
            (5,[[1,2,-3],[2,3,4],[-1,4],[-2,-4,5],[1,-5],[-5]]),
            (3,[[1,2,3],[1,2],[2,3]]),
            (2,[[1,2],[-1,-2],[1,-2],[-1,2]]),
        ]
        for n,clauses in source:
            with self.subTest(n=n,clauses=clauses):
                expected = independent_features(n,clauses)
                observed = self.run_case(n,clauses)
                for key,target in zip(("gauge_frustration","deflated_rayleigh"),expected):
                    if target is None:
                        self.assertIsNone(observed[key])
                    else:
                        self.assertAlmostEqual(observed[key],target,places=10)

    def test_independent_gauge_invariance(self):
        source = [[1,-2,3],[-1,2,4],[1,3],[-2,-4],[2,3,4]]
        base = self.run_case(4,source)
        for var in range(1,5):
            flipped = [[-lit if abs(lit)==var else lit for lit in c] for c in source]
            report = self.run_case(4,flipped)
            for key in ("gauge_frustration","deflated_rayleigh","spectral_rayleigh"):
                self.assertAlmostEqual(base[key],report[key],places=10)


if __name__ == "__main__":
    unittest.main()
