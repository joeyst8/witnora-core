import unittest

from witnora_core.public_preprint_prep_v225 import (
    RELATED_WORK_SUBSECTIONS,
    public_preprint_text,
)


class PublicPreprintRelatedWorkV225Test(unittest.TestCase):
    def test_related_work_present(self):
        text = public_preprint_text()
        self.assertIn("## Related Work", text)
        self.assertIn("TODO citation", text)
        print("PUBLIC_PREPRINT_RELATED_WORK_PASS")

    def test_related_work_subsections(self):
        text = public_preprint_text()
        for subsection in RELATED_WORK_SUBSECTIONS:
            self.assertIn("### " + subsection, text)
        print("PUBLIC_PREPRINT_RELATED_WORK_SUBSECTIONS_PASS")

    def test_related_work_boundaries(self):
        text = public_preprint_text()
        self.assertIn("native operator certificates; external proof bridge not yet claimed", text)
        self.assertIn("plan-only certificate with an explicit execution-required boundary", text)


if __name__ == "__main__":
    unittest.main()
