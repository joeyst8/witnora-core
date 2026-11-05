"""R-171–R-174: experimental native proof options are opt-in end-to-end."""
import tempfile
import unittest
import io
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from witnora_core.runner import main


class XorRunnerOptionsTests(unittest.TestCase):
    def run_cli(self, extra):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/"input.cnf"
            source.write_text("p cnf 1 2\n1 0\n-1 0\n",encoding="utf-8")
            path=SimpleNamespace(to_dict=lambda:{"status":"test"})
            with patch("witnora_core.runner.solve_with_xor",return_value=path), patch(
                 "witnora_core.runner.export_certificate_bundle") as export:
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main([str(source),"--detect-xor","--export-cert",
                        str(Path(directory)/"output.wcert"),"--export-drat","--xor-drat",
                        *extra]),0)
                return export.call_args.kwargs

    def test_default_fallback_options(self):
        args=self.run_cli([])
        self.assertEqual(args["xor_proof_backend"],"python")
        for name in ("xor_require_dual_internal","xor_require_source_identity",
                     "xor_require_dual_source_parser","xor_require_native_proof_audit"):
            self.assertFalse(args[name],name)

    def test_explicit_native_and_integrity_options(self):
        args=self.run_cli(["--xor-proof-backend","rust","--xor-dual-rup",
            "--xor-validate-source","--xor-dual-source-parser",
            "--xor-native-proof-audit"])
        self.assertEqual(args["xor_proof_backend"],"rust")
        for name in ("xor_require_dual_internal","xor_require_source_identity",
                     "xor_require_dual_source_parser","xor_require_native_proof_audit"):
            self.assertTrue(args[name],name)


if __name__ == "__main__":
    unittest.main()
