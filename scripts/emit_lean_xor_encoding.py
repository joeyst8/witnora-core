"""Emit independent Lean truth-table checks of Python's canonical XOR CNF.

The main Lean theorem is symbolic and universal. These bounded checks connect
the *actual Python encoder output* to its semantics for small arities and
include a deliberately omitted-clause negative control.
"""
from pathlib import Path
from itertools import product
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


def lean_int_lists(clauses):
    return "[" + ", ".join(
        "[" + ", ".join(map(str, clause)) + "]" for clause in clauses
    ) + "]"


def canonical_ordered_python_clauses(raw_variables, rhs):
    # The real Python encoder returns a set. Reconstruct the deterministic
    # least-significant-bit-first order used by Lean's allBits, without
    # regenerating the expected set from an untrusted checker verdict.
    actual = canonical_xor_cnf_clauses(raw_variables, rhs)
    odd = {}
    for var in raw_variables:
        odd[var] = odd.get(var, 0) ^ 1
    normalized = sorted(var for var, bit in odd.items() if bit)
    ordered = []
    for mask in range(1 << len(normalized)):
        bits = [(mask >> i) & 1 for i in range(len(normalized))]
        if sum(bits) % 2 != rhs:
            clause = tuple(sorted(
                -var if bit else var
                for var, bit in zip(normalized, bits)
            ))
            if clause not in actual:
                raise RuntimeError("Python encoder omitted a required clause")
            ordered.append(clause)
    if set(ordered) != actual or len(ordered) != len(actual):
        raise RuntimeError("Python encoder generated an unexpected clause")
    return normalized, ordered


def main():
    lines = [
        "import Witnora.Extraction",
        "import Witnora.FiniteXor",
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
            lines.append(
                f"example : {header}{lean_cnf(clauses)} == "
                f"(Witnora.FiniteXor.canonicalFinite {arity} {lean_bool(rhs)} bits)) "
                "= true := by decide"
            )
            if arity == 4 and rhs == 1:
                lines.append(
                    f"example : {header}{lean_cnf(clauses[1:])} == ({condition})) "
                    "= false := by decide"
                )
            count += 1
    # Independently verify variable-ID mapping and modulo-2 duplicate
    # cancellation against the same formal finite reference.
    for raw_variables, rhs in (
        ([2, 5], 0),
        ([2, 5, 7], 1),
        ([2, 2, 5], 1),
        ([2, 5, 2], 0),
    ):
        odd = {}
        for var in raw_variables:
            odd[var] = odd.get(var, 0) ^ 1
        effective = sorted(v for v, bit in odd.items() if bit)
        original_clauses = list(canonical_xor_cnf_clauses(raw_variables, rhs))
        bound = max(raw_variables, default=0)
        projection = "[" + ", ".join(
            f"Witnora.Concrete.readVar bits {var}" for var in effective
        ) + "]"
        lines.append(
            f"example : (Witnora.Concrete.allBits {bound}).all "
            f"(fun bits => Witnora.Concrete.cnfTrue bits {lean_cnf(original_clauses)} == "
            f"(Witnora.FiniteXor.canonicalFinite {len(effective)} "
            f"{lean_bool(rhs)} {projection})) = true := by decide"
        )
    # Directly feed real Python-generated normalized supports and signed
    # integer clauses into the executable Lean-verified acceptance checker.
    # These are finite regression instances, not a universal Python theorem.
    cases = (
        ([], 0), ([], 1), ([2], 0), ([2], 1),
        ([3, 1, 3, 2, 1, 5], 1),
        ([1, 1], 0), ([1, 1], 1),
        ([2, 5], 0), ([2, 5, 7], 1),
        ([2, 2, 5], 1), ([2, 5, 2], 0),
        ([9, 4, 9, 7, 4, 3], 1),
        ([1, 5, 3, 5, 2, 4], 0),
    )
    for raw_variables, rhs in cases:
        normalized, clauses = canonical_ordered_python_clauses(
            raw_variables, rhs
        )
        raw_expr = "[" + ", ".join(map(str, raw_variables)) + "]"
        normalized_expr = "[" + ", ".join(map(str, normalized)) + "]"
        clause_expr = lean_int_lists(clauses)
        lines.append(
            "example : Witnora.FiniteXor.checkPythonEncodingOutput "
            f"{raw_expr} {normalized_expr} {lean_bool(rhs)} "
            f"{clause_expr} = true := by decide"
        )
        if len(clauses) > 0:
            lines.append(
                "example : Witnora.FiniteXor.checkPythonEncodingOutput "
                f"{raw_expr} {normalized_expr} {lean_bool(rhs)} "
                f"{lean_int_lists(clauses[:-1])} = false := by decide"
            )
    lines.extend(["", "end Witnora.XorGenerated", ""])
    destination = Path("formal/Witnora/XorGenerated.lean")
    destination.write_text("\n".join(lines), encoding="utf-8")
    print(f"Emitted {count} canonical XOR encoding equivalence checks")


if __name__ == "__main__":
    main()
