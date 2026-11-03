"""Independent CDCL proof acceptance for dense non-affine random 3-CNFs.

Each UNSAT benchmark uses exactly-three-literal random clauses, a complete
primal co-occurrence graph (hence no nontrivial small variable separator),
and Glucose DRUP proof. Native elaboration is only a proposal: generated Lean
checks remain the authority. Deterministic planted-SAT controls demonstrate
the source family itself is not intrinsically inconsistent.

This is a frozen diagnostic, NOT an industrial benchmark or runtime claim.
"""
from __future__ import annotations

from random import Random

from scripts.generate_general_resolution_lean import lean_signed
from scripts.generate_glucose_drup_rup_lean import (
    lean_ascii_example,
    lean_example,
)
from witnora_core.rup_witness_import import annotate_drup, verify_native_witness


def random_three_cnf(nvars: int, nclauses: int, seed: int, *, planted: bool) -> list[list[int]]:
    if nvars < 3 or nclauses < 1:
        raise ValueError("need at least three variables and one clause")
    rng = Random(seed)
    rows: set[tuple[int, ...]] = set()
    for _ in range(100 * nclauses):
        vs = sorted(rng.sample(range(1, nvars + 1), 3))
        clause = tuple(v if rng.getrandbits(1) else -v for v in vs)
        if planted and not any(lit > 0 for lit in clause):
            continue  # all-true assignment satisfies every accepted clause
        rows.add(clause)
        if len(rows) == nclauses:
            break
    if len(rows) != nclauses:
        raise AssertionError("failed to sample enough unique 3-clauses")
    return [list(row) for row in sorted(rows)]


def complete_primal_graph(source: list[list[int]], nvars: int) -> bool:
    pairs = set()
    for clause in source:
        if len(clause) != 3 or len({abs(lit) for lit in clause}) != 3:
            return False
        for i in range(3):
            for j in range(i + 1, 3):
                pairs.add(tuple(sorted((abs(clause[i]), abs(clause[j])))))
    return all((i, j) in pairs for i in range(1, nvars + 1)
               for j in range(i + 1, nvars + 1))


def find_case(nvars: int, nclauses: int, *, planted: bool,
              max_attempts: int = 256) -> tuple[list[list[int]], dict]:
    from pysat.solvers import Glucose3

    for attempt in range(max_attempts):
        seed = 630000 + 1000 * nvars + attempt + (100000 if planted else 0)
        source = random_three_cnf(nvars, nclauses, seed, planted=planted)
        if not complete_primal_graph(source, nvars):
            continue
        with Glucose3(bootstrap_with=source, with_proof=not planted) as solver:
            verdict = solver.solve()
            raw_proof = solver.get_proof() if not planted else []
        if planted:
            if verdict is True and all(any(lit > 0 for lit in row) for row in source):
                return source, {"seed": seed, "status": "SAT_CONTROL", "proof": None}
            continue
        if verdict is not False or not raw_proof:
            continue
        try:
            info = annotate_drup(source, raw_proof, max_additions=250)
        except (ValueError, RuntimeError):
            continue
        if not verify_native_witness(source, info["additions"]):
            raise AssertionError("unexpected native witness replay failure")
        if info["unit_witness_literals"] > 2500:
            continue
        return source, {"seed": seed, "status": "LEAN_CHECK_PENDING", "proof": info}
    raise AssertionError(f"could not find bounded dense 3-CNF control: {nvars}/{nclauses}, planted={planted}")


def lean_sat_model(source: list[list[int]]) -> None:
    raw = "[" + ", ".join(lean_signed(row) for row in source) + "]"
    print("example : Witnora.SignedSerialization.signedCNFHolds")
    print(f"    ({raw} : List (List Int)) (fun _ => true) := by")
    print("  unfold Witnora.SignedSerialization.signedCNFHolds")
    print("  decide")
    print("example : checkRup (Witnora.SignedSerialization.decodeCNF")
    print(f"    ({raw} : List (List Int)))")
    print("    [{clause := [], units := []}] = false := by decide")


def main() -> None:
    print("import Witnora.GeneralRUPAscii")
    print("open Witnora.GeneralRUP")
    print("open Witnora.GeneralRUPAscii")
    print("set_option maxRecDepth 65536")
    print("set_option maxHeartbeats 8000000")
    for nvars, nclauses in [(8, 54), (10, 66), (12, 84)]:
        unsat, info = find_case(nvars, nclauses, planted=False)
        proof = info["proof"]
        assert proof is not None
        print(f"-- Dense complete-primal 3-CNF UNSAT {nvars}/{nclauses}, seed={info['seed']}, " +
              f"RUP additions={len(proof['additions'])}, units={proof['unit_witness_literals']}.")
        lean_example(unsat, proof)
        if nvars == 8:
            lean_ascii_example(unsat, proof)
        sat, control = find_case(nvars, nclauses, planted=True)
        print(f"-- Dense complete-primal SAT control {nvars}/{nclauses}, seed={control['seed']}.")
        lean_sat_model(sat)


if __name__ == "__main__":
    main()
