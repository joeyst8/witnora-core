import unittest

from witnora_core.submit_release_finalize_v226 import (
    bibliography_entries,
    bibliography_manifest,
    references_bib_text,
)


class BibliographyV226Test(unittest.TestCase):
    def test_bibliography_exists(self):
        entries = bibliography_entries()
        self.assertGreaterEqual(len(entries), 12)
        self.assertTrue(all(entry["title"] for entry in entries))
        self.assertTrue(all(entry["authors"] for entry in entries))
        print("BIBLIOGRAPHY_EXISTS_PASS")

    def test_no_todo_citations(self):
        bib = references_bib_text()
        self.assertNotIn("TODO citation", bib)
        self.assertNotIn("CITATION_NEEDED_NOT_CLAIMED", bib)
        self.assertIn("DRAT-trim", bib)
        self.assertIn("SATzilla", bib)
        print("BIBLIOGRAPHY_NO_TODO_CITES_PASS")

    def test_manifest_status(self):
        manifest = bibliography_manifest()
        self.assertEqual(manifest["verification_status"], "PASS")
        self.assertEqual(manifest["todo_citation_markers"], 0)


if __name__ == "__main__":
    unittest.main()
