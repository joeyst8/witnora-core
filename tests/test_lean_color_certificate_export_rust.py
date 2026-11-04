"""R-095: byte-exact Lean color source and clique-search parity."""
import random
import unittest

from witnora_core.lean_color_certificate_export import (
    _fin_values, emit_lean, find_matching_clique, generate_default_cases,
)

try:
    from witnora_ve import lean_color_emit_native
except ImportError:
    lean_color_emit_native = None


@unittest.skipUnless(lean_color_emit_native is not None, "native wheel unavailable")
class LeanColorExporterRust(unittest.TestCase):
    def test_full_source_exact(self):
        cases = list(generate_default_cases())
        for count in range(len(cases)+1):
            selected = tuple(cases[:count])
            self.assertEqual(emit_lean(selected), emit_lean(selected, backend="rust"))
        for rotation in range(len(cases)):
            selected = tuple(cases[rotation:]+cases[:rotation])
            self.assertEqual(emit_lean(selected), emit_lean(selected, backend="rust"))

    def test_fin_values_randomized(self):
        rng = random.Random(95095)
        for _ in range(180):
            n = rng.randrange(1,17)
            codomain = rng.randrange(1,9)
            values = [rng.randrange(codomain) for _ in range(n)]
            self.assertEqual(_fin_values("paint","v",n,codomain,values),
                             _fin_values("paint","v",n,codomain,values,backend="rust"))

    def test_clique_search(self):
        rng = random.Random(19595)
        for _ in range(150):
            n = rng.randrange(1,11)
            edges = tuple((u,v) for u in range(n) for v in range(u+1,n)
                          if rng.randrange(2))
            size = rng.randrange(n+2)
            self.assertEqual(find_matching_clique(n,edges,size),
                             find_matching_clique(n,edges,size,backend="rust"))

    def test_invalid_cases(self):
        case = generate_default_cases()[0]
        for selected in ((case,case), (("bad-name",1,(),[0],(0,)),),
                         (("bad",2,((0,1),),[0,0],(0,1)),)):
            for backend in ("python","rust"):
                with self.assertRaises(ValueError):
                    emit_lean(selected,backend=backend)


if __name__ == "__main__":
    unittest.main()
