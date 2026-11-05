import unittest

from witnora_core.tc063_theorem_hardening import (
    FORBIDDEN_STATUSES,
    build_hardening_record,
    check_tc063_hardening,
)


class TC063ClaimBoundariesTest(unittest.TestCase):
    def test_no_theorem_proven_unqualified(self):
        record = build_hardening_record().to_dict()
        self.assertNotEqual(record["hardened_status"], "THEOREM_PROVEN_UNQUALIFIED")
        self.assertEqual(check_tc063_hardening(record)["errors"], [])
        print("TC063_NO_THEOREM_PROVEN_UNQUALIFIED_PASS")

    def test_no_completeness_pnp_all_sat_or_fake_drat_claim(self):
        record = build_hardening_record().to_dict()
        joined = "\n".join(record["nonclaims"])
        self.assertIn("Does not prove P vs NP", joined)
        self.assertIn("Does not prove all SAT", joined)
        self.assertIn("Does not prove hierarchy completeness", joined)
        self.assertIn("DRAT", joined)
        print("TC063_NO_COMPLETENESS_CLAIM_PASS")
        print("TC063_NO_PNP_CLAIM_PASS")
        print("TC063_NO_FAKE_DRAT_PASS")
        print("TC063_NO_ALL_SAT_CLAIM_PASS")

    def test_no_hard_unknown_status(self):
        record = build_hardening_record().to_dict()
        statuses = []

        def walk(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in {"status", "checker_status", "validation_status", "hardened_status"} and isinstance(item, str):
                        statuses.append(item)
                    walk(item)
            elif isinstance(value, list):
                for item in value:
                    walk(item)

        walk(record)
        self.assertFalse(set(statuses) & FORBIDDEN_STATUSES)
        self.assertEqual(check_tc063_hardening(record)["errors"], [])
        print("TC063_NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
