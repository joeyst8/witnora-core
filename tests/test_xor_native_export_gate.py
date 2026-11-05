"""R-153/R-154: opt-in Rust candidates never bypass verification gates."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from witnora_core.cnf import CNFFormula
from witnora_core.certificate import XOR_UNSAT_NATIVE
from witnora_core.xor import canonical_xor_cnf_clauses
from witnora_core.xor_drat import export_xor_drat_for_path


class NativeXorExportGateTests(unittest.TestCase):
    @staticmethod
    def fixture():
        equations = []
        for rhs in (0,1):
            clauses = canonical_xor_cnf_clauses([1],rhs)
            equations.append({"source":"detected_cnf_pattern", "variables":[1],
                              "rhs":rhs,"source_clauses":[list(c) for c in clauses],
                              "exact_full_encoding":True,"safe_use":True})
        path = SimpleNamespace(status=XOR_UNSAT_NATIVE,
                               xor_data={"xor_system":{"equations":equations}})
        return CNFFormula([[1],[-1]]),path

    def test_invalid_backend_rejected(self):
        formula,path = self.fixture()
        with self.assertRaisesRegex(ValueError,"unknown XOR proof backend"):
            export_xor_drat_for_path(formula,path,drat_trim_path=None,
                                     proof_backend="unsupported")

    def test_both_orderings_require_external_checker(self):
        formula,path = self.fixture()
        for order in ("gaussian","sparse-min-fill"):
            with self.subTest(order=order):
                results=[]
                for backend in ("python","rust"):
                    with patch("witnora_core.xor_drat.run_drat_trim",
                               return_value={"external_checker_verified":False,
                                             "error":"test checker unavailable"}) as checker:
                        result=export_xor_drat_for_path(formula,path,
                            drat_trim_path="not-real-in-test",xor_elim_order=order,
                            proof_backend=backend,timeout_seconds=None)
                    self.assertEqual(checker.call_count,1)
                    self.assertFalse(result.xor_status.get("external_drat",False))
                    self.assertEqual(result.xor_status["xor_drat_status"],"DRAT_TRIM_FAILED")
                    results.append(result.xor_status["xor_drat_status"])
                self.assertEqual(results[0],results[1])


if __name__ == "__main__":
    unittest.main()
