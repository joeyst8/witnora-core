"""Emit independent Lean truth-table checks of Python's canonical XOR CNF.

The main Lean theorem is symbolic and universal. These bounded checks connect
the *actual Python encoder output* to its semantics for small arities and
include a deliberately omitted-clause negative control.
"""
from pathlib import Path
from witnora_core.xor import canonical_xor_cnf_clauses


def lean_bool(value):
    return "true" if value else "false"


def lean_cnf(clauses):
    return "[" + ", ".join(
        "[" + ", ".join(
            f"({abs(lit)}, {lean_bool(lit > 0)})" for lit in clause
        ) + "]"
        for clause in clauses
    ) + "]"


def main():
    lines = [
        "import Witnora.Extraction",
        "set_option maxRecDepth 8192",
        "set_option maxHeartbeats 0",
        "",
        "namespace Witnora.XorGenerated",
    ]
    count = 0
    for arity in (0, 2, 3, 4, 5):
        variables = list(range(1, arity + 1))
        var_expr = "[" + ", ".join(map(str, variables)) + "]"
        for rhs in (0, 1):
            clauses = list(canonical_xor_cnf_clauses(variables, rhs))
            expected = (rhs if arity == 0 else (1 << (arity - 1)))
            if len(clauses) != expected:
                raise RuntimeError("Python XOR generator did not emit full canonical family")
            condition = (
                f"Witnora.Extraction.parityVars {var_expr} "
                "(fun v => Witnora.Concrete.readVar bits v) == "
                f"{lean_bool(rhs)}"
            )
            header = (
                f"(Witnora.Concrete.allBits {arity}).all "
                "(fun bits => Witnora.Concrete.cnfTrue bits "
            )
            lines.append(
                f"example : {header}{lean_cnf(clauses)} == ({condition})) "
                "= true := by decide"
            )
            if arity == 4 and rhs == 1:
                lines.append(
                    f"example : {header}{lean_cnf(clauses[1:])} == ({condition})) "
                    "= false := by decide"
                )
            count += 1
    lines.extend(["", "end Witnora.XorGenerated", ""])
    destination = Path("formal/Witnora/XorGenerated.lean")
    destination.write_text("\n".join(lines), encoding="utf-8")
    print(f"Emitted {count} canonical XOR encoding equivalence checks")


if __name__ == "__main__":
    main()
