import unittest

from witnora_core.reproducibility_package import NOT_RECORDED, release_sha_manifest


class ReleaseManifestTest(unittest.TestCase):
    def test_release_sha_manifest(self):
        manifest = release_sha_manifest()
        records = manifest["records"]
        tags = {record["tag"] for record in records}
        for tag in [
            "v2.0-collapse-theory-lab",
            "v2.1-collapse-theory-frontier",
            "v2.2-certified-symmetry-collapse",
            "v2.3-pigeonhole-cardinality-collapse",
            "v2.4-operator-genesis",
            "v2.5-orbit-capacity-counting",
            "v2.6-affine-residue-collapse",
            "v2.7-proof-motif-compression",
            "v2.8-collapse-hierarchy-theoremization",
            "v2.9-restricted-g0-g1-strictness",
            "v2.10-finite-strictness-certificate",
            "v2.11-finite-edge-delta-g1-g2",
        ]:
            self.assertIn(tag, tags)
        v211 = next(record for record in records if record["tag"] == "v2.11-finite-edge-delta-g1-g2")
        self.assertEqual(v211["artifact_sha256"], "9AFB64684B07534F7B844902800E3B4064BB379BD2C93CA98F358C345FD9BB49")
        self.assertTrue(any(record["source_sha256"] == NOT_RECORDED for record in records))
        print("RELEASE_SHA256_MANIFEST_PASS")


if __name__ == "__main__":
    unittest.main()
