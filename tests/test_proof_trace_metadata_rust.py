"""R-062: independent native metadata predicate differential controls."""
import os
import random
import unittest

from witnora_core.proof_trace import (
    is_supported_native_unsat_trace, is_supported_native_unsat_trace_rust,
)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in Rust CI")
class NativeProofTraceMetadataRustTests(unittest.TestCase):
    def test_random_and_single_field_tamper(self):
        valid = {
            "proof_trace_format": "WITNORA_NATIVE_UNSAT_TRACE_V1",
            "depends_on_replayed_collapse_path": True,
            "external_standard": "NONE",
            "lrat_frat_status": "NOT_EXPORTED",
            "unsat_reason": "EXPLICIT_EMPTY_CLAUSE",
        }
        rng = random.Random(6202026)
        options = [None, "", False, True, 4, "WRONG", [], {},
                   "INDEPENDENT_2SAT_SCC", "EXPLICIT_EMPTY_CLAUSE"]
        for reason in ("EXPLICIT_EMPTY_CLAUSE", "INDEPENDENT_2SAT_SCC"):
            row = dict(valid, unsat_reason=reason)
            self.assertTrue(is_supported_native_unsat_trace_rust(row))
            self.assertTrue(is_supported_native_unsat_trace(row))
        for _ in range(600):
            trace = dict(valid)
            for key in rng.sample(list(valid), rng.randrange(1, 6)):
                trace[key] = rng.choice(options)
            self.assertEqual(is_supported_native_unsat_trace_rust(trace),
                             is_supported_native_unsat_trace(trace))
        self.assertFalse(is_supported_native_unsat_trace_rust(None))


if __name__ == "__main__":
    unittest.main()
