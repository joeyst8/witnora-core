"""Generate Lean checks of real Python G5 Gaussian trace payloads.

Lean replays the actual SWAP_ROWS/ADD_ROW_XOR operations and checks a bounded
UNSAT oracle over the *original* CNF. This is not a universal Python proof.
"""
from pathlib import Path

from witnora_core.operator_genesis import (
    AFFINE_RESIDUE_CERTIFICATE_VERIFIED,
    AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED,
    build_affine_residue_certificate,
    make_affine_residue_instance,
)

CASES = ("parity_arity_7_unsat", "parity_arity_8_unsat")


def lean_bool(x):
    return "true" if x else "false"


def lean_cnf(formula):
    return "[" + ", ".join(
        "[" + ", ".join(
            f"({abs(lit)}, {lean_bool(lit > 0)})" for lit in clause
        ) + "]" for clause in formula.to_clause_lists()
    ) + "]"


def lean_rows(rows):
    return "[" + ", ".join(
        "{ coefficients := [" + ", ".join(map(str, row["coefficients"])) +
        "], rhs := " + lean_bool(bool(row["rhs"])) + " }"
        for row in rows
    ) + "]"


def lean_steps(operations):
    chunks = []
    for op in operations:
        if op["operation"] == "SWAP_ROWS":
            chunks.append(f".swap {op['row_a']} {op['row_b']}")
        elif op["operation"] == "ADD_ROW_XOR":
            chunks.append(f".addXor {op['target_row']} {op['source_row']}")
        else:
            raise RuntimeError(f"unrecognized operation: {op}")
    return "[" + ", ".join(chunks) + "]"


def main():
    lines = ["import Witnora.G5Trace", "set_option maxRecDepth 16384", "set_option maxHeartbeats 0", "", "namespace Witnora.G5Generated"]
    for name in CASES:
        instance = make_affine_residue_instance(name)
        cert = build_affine_residue_certificate(instance)
        if (cert.checker_status != AFFINE_RESIDUE_CERTIFICATE_VERIFIED
                or cert.status != AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED):
            raise RuntimeError(f"{name}: not a Python-verified G5 UNSAT certificate")
        trace = cert.gaussian_elimination_trace
        if trace[0].get("type") != "INITIAL_ROWS" or trace[-1].get("type") != "FINAL_ROWS":
            raise RuntimeError(f"{name}: malformed trace envelope")
        n = instance.formula.max_var
        if n > 8:
            raise RuntimeError("fixture exceeds exhaustive Lean budget")
        prefix = (
            f"Witnora.G5Trace.acceptsUnsat {n} "
            f"{lean_cnf(instance.formula)} "
            f"{lean_rows(trace[0]['rows'])} "
            f"{lean_steps(cert.row_operations)} "
        )
        lines.append(f"example : {prefix}{lean_rows(trace[-1]['rows'])} = true := by decide")
        lines.append(f"example : {prefix}[] = false := by decide")
        lines.append(
            f"example : {prefix}[{{ coefficients := [0], rhs := true }}] "
            "= false := by decide"
        )
        lines.append(
            f"example : {prefix}[{{ coefficients := [1, 1], rhs := true }}] "
            "= false := by decide"
        )
    lines.extend(["", "end Witnora.G5Generated", ""])
    dest = Path("formal/Witnora/G5Generated.lean")
    dest.write_text("\n".join(lines), encoding="utf-8")
    print(f"Emitted {len(CASES)} Python G5 trace replay certificates and negative controls")


if __name__ == "__main__":
    main()
