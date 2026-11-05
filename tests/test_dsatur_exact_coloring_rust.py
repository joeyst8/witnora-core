"""R-097: exact backtracking color-witness parity with frozen Python order."""
import random
import unittest

from witnora_core.dsatur_adversarial_lab import chromatic_certificate, exact_k_coloring

try:
    from witnora_ve import dsatur_exact_k_coloring_native
except ImportError:
    dsatur_exact_k_coloring_native = None


@unittest.skipUnless(dsatur_exact_k_coloring_native is not None,
                     "native wheel unavailable")
class ExactDSATURColoringRust(unittest.TestCase):
    def test_seeded_color_witnesses(self):
        rng = random.Random(97097)
        for _ in range(360):
            n = rng.randrange(0,11)
            edges = tuple((u,v) for u in range(n) for v in range(u+1,n)
                          if rng.randrange(100)<rng.randrange(0,101))
            k = rng.randrange(n+2)
            self.assertEqual(exact_k_coloring(n,edges,k),
                             exact_k_coloring(n,edges,k,backend="rust"))

    def test_analytic_families_and_certificates(self):
        for n in (1,2,3,4,6,8,12,16):
            families = (tuple((u,v) for u in range(n) for v in range(u+1,n)),
                        tuple((u,u+1) for u in range(n-1)))
            for edges in families:
                for k in (0,1,2,3,n):
                    self.assertEqual(exact_k_coloring(n,edges,k),
                                     exact_k_coloring(n,edges,k,backend="rust"))
                self.assertEqual(chromatic_certificate(n,edges,n),
                                 chromatic_certificate(n,edges,n,backend="rust"))

    def test_invalid_inputs(self):
        for n, edges, k in ((17,(),1),(3,((0,0),),2),(3,((0,3),),2),
                            (3,((0,1),(0,1)),2),(3,(),-1)):
            for backend in ("python","rust"):
                with self.assertRaises(ValueError):
                    exact_k_coloring(n,edges,k,backend=backend)


if __name__ == "__main__":
    unittest.main()
