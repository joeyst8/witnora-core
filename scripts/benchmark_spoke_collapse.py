"""Reproducible, non-promotional timing comparison for spoke-collapse research.

Times are workload-specific, not claims of superior asymptotic complexity.
The dedicated matcher is compared with a general GF(2) Gaussian eliminator
and, when installed, a SAT solver on the exact same generated CNF.
"""
from __future__ import annotations

from statistics import median
from time import perf_counter

from witnora_core.spoke_collapse import collapse_spokes, make_spoke_family
from witnora_core.xor import XorEquation, XorSystem, solve_xor_system_gaussian


def median_seconds(fn, repetitions=5):
    samples = []
    for _ in range(repetitions):
        start = perf_counter()
        fn()
        samples.append(perf_counter() - start)
    return median(samples)


def run():
    try:
        from pysat.solvers import Glucose3
    except ImportError:
        Glucose3 = None

    print("spokes,clauses,collapse_ms,gaussian_ms,glucose_ms")
    for n in (10, 100, 500):
        formula, spokes = make_spoke_family(n, contradictory=True)
        equations = XorSystem(
            eq for spoke in spokes for eq in (
                XorEquation((1, spoke.middle), spoke.left),
                XorEquation((spoke.middle, 2), spoke.right),
            )
        )
        def direct():
            result = collapse_spokes(formula, spokes)
            assert result["status"] == "UNSAT_BY_SPOKE_SYNDROME"

        def gaussian():
            result = solve_xor_system_gaussian(equations)
            assert result["status"] == "UNSAT"

        def glucose():
            with Glucose3(bootstrap_with=formula.to_clause_lists()) as solver:
                assert not solver.solve()

        ours = median_seconds(direct) * 1000
        gauss = median_seconds(gaussian) * 1000
        gl = median_seconds(glucose) * 1000 if Glucose3 else float("nan")
        print(f"{n},{formula.num_clauses},{ours:.3f},{gauss:.3f},{gl:.3f}")


if __name__ == "__main__":
    run()
