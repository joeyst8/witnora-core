import tempfile
import unittest
from pathlib import Path

from witnora_core.external_review_package_v224 import (
    UNKNOWN_METADATA_NOT_CLAIMED,
    release_records_v214_to_v223,
    run_external_review_package,
)


class ExternalReviewManifestV224Test(unittest.TestCase):
    def test_evidence_manifest_release_metadata(self):
        records = {record["version"]: record for record in release_records_v214_to_v223()}
        self.assertEqual(records["v2.14"]["source_sha256"], UNKNOWN_METADATA_NOT_CLAIMED)
        expected = {
            "v2.15": "852E3C515892F9EA1757D2CE0895AEC6DB5F38EC09EA46330E81AF1EC06BA04D",
            "v2.16": "D4C5C458A799827A1B4AE7DD27CB41377708F41390C82D18E0F9070C84AAE2B8",
            "v2.17": "D75711609F08910D50591E6B1BEC7D553A3B1882DB8CAE291E836C5FE2D23C2D",
            "v2.18": "5AEC097DB6FC58BD1D7C480FCF162F8C23F95E184EF08FB769C3A55CCB6E2832",
            "v2.19": "F1509FB6F3FD28CFCBA2DEF5E122F184A38336648DA3F5D90F86404CD89FC9B9",
            "v2.20": "07969B56E9F9BA131FD6299877ACEA90D42391FDF88C3231AC6E2E38AB686900",
            "v2.21": "DE79621FAD4CFAF836E095C552C3D08063F24503B9B0FAFF384E83F79964EDF1",
            "v2.22": "C06382CA8A8E9217FEC0CC16CBAFBA80140437735DE8E567CD251F290C22E278",
            "v2.23": "04EEBFF728A914912C5D5B6787E5B7258A95804A970915D97C5E3B5B1F5AF30F",
        }
        for version, sha in expected.items():
            self.assertEqual(records[version]["source_sha256"], sha)
        print("EXTERNAL_REVIEW_EVIDENCE_MANIFEST_PASS")

    def test_sha_manifest_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pkg"
            run_external_review_package(root, strict=True, zip_path=None)
            self.assertTrue((root / "artifact_sha_manifest.json").is_file())
            print("EXTERNAL_REVIEW_SHA_MANIFEST_PASS")


if __name__ == "__main__":
    unittest.main()
