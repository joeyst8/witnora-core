"""R-118: compare native ANF geometry reports with the Python reference."""
import unittest

from scripts.generate_glucose_dense_3sat_lean import random_three_cnf
from witnora_core.geometry_aware_parity import geometry_aware_sparse_sketch
from witnora_core.violation_image_anf import analyze_parity_anf


class AnfGeometryNativeRustTests(unittest.TestCase):
    def test_seeded_geometries(self):
        for n in range(3, 15):
            for index in range(18):
                source = random_three_cnf(n, n+2, 20261129+n*100+index,
                                          planted=index % 2 == 0)
                sketch = geometry_aware_sparse_sketch(source, n)
                with self.subTest(n=n, index=index):
                    self.assertEqual(analyze_parity_anf(source, sketch, backend="rust"),
                                     analyze_parity_anf(source, sketch))


if __name__ == "__main__":
    unittest.main()
