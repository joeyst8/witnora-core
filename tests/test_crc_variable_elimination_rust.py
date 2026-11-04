"""R-096 source-exact bounded variable-elimination differential tests."""
import random
import unittest

from witnora_core.crc_boundary import _normalized_clauses
from witnora_core.crc_variable_elimination import count_component_by_elimination

try:
    from witnora_ve import crc_variable_eliminate_native
except ImportError:
    crc_variable_eliminate_native = None


@unittest.skipUnless(crc_variable_eliminate_native is not None, "native wheel unavailable")
class ExactVariableEliminationRust(unittest.TestCase):
    def compare(self, rows, variables, width=8, operations=100000):
        kwargs = dict(max_factor_variables=width, max_operations=operations)
        self.assertEqual(count_component_by_elimination(rows, variables, **kwargs),
                         count_component_by_elimination(rows, variables, backend="rust", **kwargs))

    def test_360_seeded_signed_sources(self):
        rng = random.Random(96196)
        for _ in range(360):
            n = rng.randrange(1,10)
            variables = list(range(1,n+1))
            rng.shuffle(variables)
            universe = tuple(variables)
            source = []
            for _ in range(rng.randrange(0,13)):
                selected = rng.sample(variables, rng.randrange(1,min(4,n)+1))
                source.append([v if rng.randrange(2) else -v for v in selected])
            normalized = _normalized_clauses(source, universe)
            self.compare(normalized, universe, width=9)

    def test_work_caps_and_edge_cases(self):
        variables = tuple(range(1,9))
        rows = _normalized_clauses([[1,2,3],[-1,2],[-2,3]], variables)
        for width in (1,2,3,4,8):
            for budget in (1,2,10,50,1000):
                self.compare(rows, variables, width, budget)
        self.compare((), variables)
        self.compare(((0,0),), variables)
        self.compare(((1<<128,0),), (129,))
        self.compare(((1<<256,0),), (257,), width=2)

    def test_invalid_masks(self):
        for rows, vars in ((((1,1),), (1,)), (((2,0),), (1,)),
                           (((-1,0),), (1,)), ((), (1,1))):
            for backend in ("python", "rust"):
                with self.assertRaises(ValueError):
                    count_component_by_elimination(rows, vars, backend=backend)


if __name__ == "__main__":
    unittest.main()
