"""R-132: native signed-clause resolvent and tautology filtering."""
import random
import unittest

from witnora_core.xor_drat import _resolve_fast


class XorDratResolutionRustTests(unittest.TestCase):
    def test_seeded_clause_pairs(self):
        rng = random.Random(20261213)
        for trial in range(400):
            n = rng.choice((3, 12, 70, 200))
            a = tuple(sorted(set(rng.choice((-1,1))*v for v in
                            rng.sample(range(1,n+1),rng.randrange(min(n,8)+1)))))
            b = tuple(sorted(set(rng.choice((-1,1))*v for v in
                            rng.sample(range(1,n+1),rng.randrange(min(n,8)+1)))))
            pivot = rng.randint(1,n)
            with self.subTest(trial=trial):
                self.assertEqual(_resolve_fast(a,b,pivot,backend="rust"),
                                 _resolve_fast(a,b,pivot))

    def test_tautology_and_empty(self):
        for a,b,pivot in (((),(),1),((1,2),(-1,-2),1),
                          ((1,),(-1,),1),((1,2),(-1,3),1)):
            self.assertEqual(_resolve_fast(a,b,pivot,backend="rust"),
                             _resolve_fast(a,b,pivot))


if __name__ == "__main__":
    unittest.main()
