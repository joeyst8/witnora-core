"""Emit Lean source from Witnora Python's actual G14 conditioning routines.

This is a bounded two-branch integration fixture, not a general G14
certificate emitter or a formal proof of Python implementation refinement.
"""
from __future__ import annotations

from .cnf import CNFFormula
from .separator_affine_family_theorem import (
    _all_assignments, _component_dicts, _condition_by_separator,
)
from .xor import XorEquation, XorSystem, solve_xor_system_gaussian, XOR_UNSAT


SOURCE_ROWS = ((1, 2), (-1, 2), (-2,))
SEPARATOR = (1,)


def lean_nat(values):
    return "[" + ", ".join(map(str, values)) + "]"


def lean_int_rows(rows):
    return "[" + ", ".join(lean_nat(row) for row in rows) + "]"


def lean_cnf(formula):
    return "[" + ", ".join(
        "[" + ", ".join(f"({abs(lit)}, {'true' if lit > 0 else 'false'})"
                        for lit in clause)
        + "]" for clause in formula.to_clause_lists()
    ) + "]"


def lean_branch(assignment):
    return "[" + ", ".join(
        f"({v}, {'true' if assignment[v] else 'false'})"
        for v in sorted(assignment)
    ) + "]"


def actual_python_g14_artifacts():
    formula = CNFFormula.from_raw_clauses(SOURCE_ROWS)
    components = _component_dicts(formula, list(SEPARATOR))
    result = []
    for assignment in _all_assignments(SEPARATOR):
        residual, parts, errors = _condition_by_separator(
            formula, assignment, components)
        if errors or len(parts) != 1:
            raise ValueError("Python conditioning/partition rejected")
        chosen = next(iter(parts.values()))
        if chosen != residual:
            raise ValueError("selected component does not match residual")
        units = chosen.to_clause_lists()
        if len(units) != 2 or any(len(row) != 1 for row in units):
            raise ValueError("expected two unit clauses")
        if units[0][0] != -units[1][0]:
            raise ValueError("expected opposite unit literals")
        equations = [
            XorEquation((abs(row[0]),), int(row[0] > 0))
            for row in units
        ]
        # Invoke the actual Python GF(2) solver as an independent diagnostic.
        native = solve_xor_system_gaussian(XorSystem(equations))
        if native["status"] != XOR_UNSAT:
            raise ValueError("Python GF(2) solver did not find contradiction")
        result.append((assignment, residual, list(parts.values()), chosen, units))
    return formula, tuple(result)


def emit_python_g14_lean():
    formula, branches = actual_python_g14_artifacts()
    data = formula.canonical_dimacs().encode("ascii")
    token_stream = [lit for clause in formula.to_clause_lists()
                    for lit in (*clause, 0)]
    raw = lean_int_rows(formula.to_clause_lists())
    branch_patterns = [lean_branch(assignment) for assignment, *_ in branches]
    if branch_patterns != ["[(1, false)]", "[(1, true)]"]:
        raise ValueError("unexpected Python branch coverage")

    def branch_definition(name, codomain, values, default):
        expression = default
        for pattern, value in reversed(list(zip(branch_patterns, values))):
            expression = f"(if branch == {pattern} then {value} else {expression})"
        return f"def {name} (branch : List (Nat × Bool)) : {codomain} :=\n  {expression}"

    cs = ["[" + ", ".join(lean_cnf(c) for c in parts) + "]"
          for _, _, parts, _, _ in branches]
    selected = [lean_cnf(chosen) for _, _, _, chosen, _ in branches]
    bounds = [str(chosen.max_var + 1) for _, _, _, chosen, _ in branches]
    row_values = []
    for _, _, _, _, units in branches:
        row_values.append("[" + ", ".join(
            "{ coefficients := [" + str(abs(row[0])) + "], rhs := " +
            ("true" if row[0] > 0 else "false") + " }"
            for row in units) + "]")
    steps = ["[(0, 1)]"] * len(branches)

    lines = [
        "import Witnora.G14ConcreteBridge",
        "namespace Witnora.GeneratedPythonG14",
        "open Witnora.Concrete",
        "open Witnora.G14ConcreteBridge",
        "open Witnora.G5Extraction",
        "open Witnora.ComponentPartition",
        "open Witnora.Conditioning",
        "open Witnora.SeparatorAssignments",
        "open Witnora.SignedSerialization",
        "open Witnora.SparseBridge",
        "open Witnora.DIMACSDocument",
        "open Witnora.DIMACSTokens",
        "set_option maxRecDepth 8192",
        "set_option maxHeartbeats 4000000",
        f"def pythonSourceBytes : List Nat := {lean_nat(data)}",
        f"def pythonTokens : List Int := {lean_nat(token_stream)}",
        f"def pythonClauses : List (List Int) := {raw}",
        branch_definition("pythonComponents", "List CNF", cs, "[]"),
        branch_definition("pythonSelected", "CNF", selected, "[]"),
        branch_definition("pythonBound", "Nat", bounds, "0"),
        branch_definition("pythonRows", "List Witnora.G5Trace.Row", row_values, "[]"),
        branch_definition("pythonSteps", "List Witnora.G5Dag.XorRef", steps, "[]"),
        """theorem python_document_passes :
    checkDocument pythonSourceBytes pythonTokens = true := by
  decide""",
        """theorem python_stream_passes :
    checkStream pythonTokens pythonClauses = true := by
  decide""",
    ]

    def premise(name, goal):
        return f"""theorem {name} :
    {goal} := by
  intro branch hb
  have hcases : branch = [(1, false)] ∨ branch = [(1, true)] := by
    simpa [enumerate] using hb
  rcases hcases with hfalse | htrue
  · subst branch
    decide
  · subst branch
    decide"""

    lines.append(premise("python_partitions_pass",
        """∀ branch ∈ enumerate [1],
      checkPartition
        (conditionCNF (fixedOf branch) (decodeCNF pythonClauses))
        (pythonComponents branch) = true"""))
    lines.append(premise("python_selected_pass",
        """∀ branch ∈ enumerate [1],
      pythonSelected branch ∈ pythonComponents branch"""))
    lines.append(premise("python_g5_pass",
        """∀ branch ∈ enumerate [1],
      checkG5Closed (pythonBound branch) (pythonSelected branch)
        (pythonRows branch) (pythonSteps branch) = true"""))
    lines.extend([
        """theorem python_g14_g5_dimacs_unsat :
    parseDocument pythonSourceBytes = some (serialize pythonClauses) ∧
    ¬ ∃ a, signedCNFHolds pythonClauses a := by
  exact checked_ascii_dimacs_g14_unsat
    pythonSourceBytes pythonTokens pythonClauses
    python_document_passes python_stream_passes
    [1] pythonComponents python_partitions_pass
    pythonSelected python_selected_pass
    pythonBound pythonRows pythonSteps python_g5_pass""",
        "#print axioms Witnora.GeneratedPythonG14.python_g14_g5_dimacs_unsat",
        "end Witnora.GeneratedPythonG14",
        "",
    ])
    return "\n".join(lines)
