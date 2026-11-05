import unittest

from witnora_core.operator_genesis import (
    CAPACITY_FLOW_OBSTRUCTION,
    COUNTING_DEFICIT,
    NO_CONFIDENT_FINGERPRINT,
    UNKNOWN_FINGERPRINT_PATTERN_FORBIDDEN,
    extract_fingerprints,
)


class OperatorGenesisFingerprintTest(unittest.TestCase):
    def test_fingerprint_extraction(self):
        fingerprints = extract_fingerprints(["pigeonhole", "random-structured"])
        by_family = {item.family: item for item in fingerprints}
        self.assertIn(COUNTING_DEFICIT, by_family["pigeonhole"].fingerprint_types)
        self.assertIn(CAPACITY_FLOW_OBSTRUCTION, by_family["pigeonhole"].fingerprint_types)
        self.assertIn(NO_CONFIDENT_FINGERPRINT, by_family["random-structured"].fingerprint_types)
        for fingerprint in fingerprints:
            self.assertNotIn(UNKNOWN_FINGERPRINT_PATTERN_FORBIDDEN, fingerprint.fingerprint_types)
            self.assertTrue(fingerprint.reproducibility_hash)
        print("FINGERPRINT_EXTRACTION_PASS")

    def test_obstruction_fingerprint_reproducibility(self):
        first = [item.to_dict() for item in extract_fingerprints(["pigeonhole", "parity", "graph-coloring"])]
        second = [item.to_dict() for item in extract_fingerprints(["pigeonhole", "parity", "graph-coloring"])]
        self.assertEqual(first, second)
        print("OBSTRUCTION_FINGERPRINT_REPRODUCIBILITY_PASS")


if __name__ == "__main__":
    unittest.main()
