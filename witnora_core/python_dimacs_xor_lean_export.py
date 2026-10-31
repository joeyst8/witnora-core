"""Generate actual Python XOR-CNF DIMACS bytes for Lean's document checker.

Python's public canonical_xor_cnf_clauses returns a set. For source fidelity
we first obtain that exact set, then serialize it in Lean's deterministic
enumeration order, refusing to invent or omit clauses. This ordering remains
an audited emission convention, not a universal CPython refinement theorem.
"""
from __future__ import annotations

from itertools import product
import re

from .xor import XorEquation, canonical_xor_cnf_clauses


def checked_python_clauses(raw: tuple[int, ...], rhs: int):
    equation = XorEquation(raw, rhs)
    variables = equation.variables
    produced = canonical_xor_cnf_clauses(raw, rhs)
    ordered = []
    # Lean allBits prepends successive low-index Boolean bits. Consequently
    # enumerate bit vectors by reversed-tuple key, rather than Python's
    # default lexicographic ordering.
    patterns = sorted(product((0, 1), repeat=len(variables)),
                      key=lambda bits: bits[::-1])
    for bits in patterns:
        if sum(bits) % 2 == equation.rhs:
            continue
        clause = tuple(sorted(-v if b else v
                              for v, b in zip(variables, bits)))
        if clause not in produced:
            raise AssertionError("Python XOR generator omitted expected clause")
        ordered.append(clause)
    if set(ordered) != produced or len(ordered) != len(produced):
        raise AssertionError("Python XOR generator had extra/duplicate clauses")
    return equation, tuple(ordered)


def dimacs_bytes(raw: tuple[int, ...], rhs: int):
    equation, clauses = checked_python_clauses(raw, rhs)
    var_bound = max(equation.variables, default=0)
    rows = [f"p cnf {var_bound} {len(clauses)}"]
    for clause in clauses:
        rows.append(" ".join([*(str(lit) for lit in clause), "0"]))
    data = ("\n".join(rows) + "\n").encode("ascii")
    return equation, clauses, data


def lean_int_rows(clauses) -> str:
    return "[" + ", ".join("[" + ", ".join(map(str, row)) + "]"
                           for row in clauses) + "]"


def lean_nat_list(values) -> str:
    return "[" + ", ".join(map(str, values)) + "]"


def default_xor_cases():
    return (
        ("positiveUnit", (1,), 1),
        ("evenPair", (1, 2), 0),
        ("oddTriple", (1, 2, 3), 1),
        ("duplicateNormalize", (3, 1, 3, 2, 1), 1),
        ("emptyTautology", (), 0),
        ("emptyContradiction", (1, 1), 1),
    )


def emit_python_dimacs_lean(cases=None) -> str:
    if cases is None:
        cases = default_xor_cases()
    names = [case[0] for case in cases]
    if len(names) != len(set(names)):
        raise ValueError("duplicate certificate name")
    lines = [
        "import Witnora.DimacsXorDocument",
        "namespace Witnora.GeneratedPythonDimacsXor",
        "open Witnora.DimacsXorDocument",
        "open Witnora.DIMACSDocument",
        "open Witnora.DIMACSTokens",
        "open Witnora.FiniteXor",
        "open Witnora.SignedSerialization",
        "open Witnora.Extraction",
        "set_option maxRecDepth 8192",
        "set_option maxHeartbeats 4000000",
    ]
    for name, raw, rhs in cases:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name):
            raise ValueError("invalid Lean identifier")
        equation, clauses, data = dimacs_bytes(tuple(raw), rhs)
        altered = bytes([120]) + data[1:]  # Invalidate the initial 'p'.
        raw_list = lean_nat_list(raw)
        normalized = lean_nat_list(equation.variables)
        rows = lean_int_rows(clauses)
        bit = "true" if equation.rhs else "false"
        lines.extend([
            "",
            f"def {name}DocumentBytes : List Nat := {lean_nat_list(data)}",
            f"def {name}AlteredBytes : List Nat := {lean_nat_list(altered)}",
            f"def {name}SubmittedClauses : List (List Int) := {rows}",
            f"""theorem {name}DocumentPasses :
    checkXorDocument {name}DocumentBytes
      {raw_list} {normalized} {bit} {name}SubmittedClauses = true := by
  decide""",
            f"""theorem {name}DocumentAlteredRejects :
    checkXorDocument {name}AlteredBytes
      {raw_list} {normalized} {bit} {name}SubmittedClauses = false := by
  decide""",
            f"""theorem {name}ExactModelEquivalence :
    ∀ a : Nat → Bool,
      signedCNFHolds {name}SubmittedClauses a ↔
        parityVars {raw_list} a = {bit} := by
  intro a
  exact checked_xor_document_iff_original
    {name}DocumentBytes {raw_list} {normalized} {bit}
    {name}SubmittedClauses {name}DocumentPasses a""",
            f"#print axioms {name}ExactModelEquivalence",
        ])
    lines.extend(["", "end Witnora.GeneratedPythonDimacsXor", ""])
    return "\n".join(lines)
