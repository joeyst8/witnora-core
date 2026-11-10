"""Checks that WU-016 only accepts complete, typed measurement records."""

import unittest

from scripts.wu016_profile_xorcle import decode_output, last_profile, PROFILE_KEYS


class TestProfilerParse(unittest.TestCase):
    def test_complete_record(self):
        text = "WU016_PROFILE stage=progress " + " ".join(f"{key}=1" for key in PROFILE_KEYS)
        result = last_profile("noise\n" + text + "\n")
        self.assertEqual(result["profile_stage"], "progress")
        self.assertEqual(result["probe_ns"], 1)

    def test_incomplete_rejected(self):
        with self.assertRaises(ValueError):
            last_profile("WU016_PROFILE stage=progress attempts=5\n")

    def test_timeout_bytes_decoded(self):
        self.assertEqual(decode_output(b"WU016_PROFILE stage=progress"),
                         "WU016_PROFILE stage=progress")


if __name__ == "__main__":
    unittest.main()
