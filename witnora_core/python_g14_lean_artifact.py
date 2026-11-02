"""Emit Lean source from Witnora Python's actual G14 conditioning routines.

This is a bounded two-branch integration fixture, not a general G14
certificate emitter or a formal proof of Python implementation refinement.
"""
from __future__ import annotations

from .cnf import CNFFormula
from .separator_affine_family_theorem import (
    _all_assignments, _component_dicts, _condition_by_separator,
)
from .separator_affine_family_theorem import (
    _guarded_xor_equation, make_separator_affine_instance,
)
from .operator_genesis import (
    AffineResidueInstance, build_affine_residue_certificate,
    AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED,
    AFFINE_RESIDUE_CERTIFICATE_VERIFIED,
    AFFINE_RESIDUE_SAT_WITNESS_VERIFIED,
)
from .lean_g5_gate import _compile_dag, _serialize_rows


SOURCE_ROWS = tuple(
    tuple(row)
    for parity in (0, 1)
    for active in (False, True)
    for row in _guarded_xor_equation(1, active, (2, 3), parity)
)
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


def actual_python_g14_artifacts(instance_id=None):
    formula = (
        CNFFormula.from_raw_clauses(SOURCE_ROWS)
        if instance_id is None
        else make_separator_affine_instance(instance_id).formula
    )
    components = _component_dicts(formula, list(SEPARATOR))
    result = []
    for assignment in _all_assignments(SEPARATOR):
        residual, parts, errors = _condition_by_separator(
            formula, assignment, components)
        if errors or not parts:
            raise ValueError("Python conditioning/partition rejected")
        chosen = None
        certificate = None
        for candidate in parts.values():
            native_instance = AffineResidueInstance(
                instance_id=f"g14_branch_{int(assignment[1])}",
                equations=(), formula=candidate,
            )
            candidate_cert = build_affine_residue_certificate(
                native_instance, max_arity=2)
            if (candidate_cert.status == AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED
                    and candidate_cert.checker_status == AFFINE_RESIDUE_CERTIFICATE_VERIFIED):
                chosen = candidate
                certificate = candidate_cert
                break
        if chosen is None or certificate is None:
            raise ValueError("no native G5 contradiction covering branch")
        trace = certificate.gaussian_elimination_trace
        if (not trace or trace[0].get("type") != "INITIAL_ROWS"
                or not certificate.row_operations):
            raise ValueError("native G5 trace missing initial rows or operations")
        result.append((assignment, residual, list(parts.values()),
                       chosen, certificate))
    return formula, tuple(result)


def emit_python_g14_lean(instance_id=None):
    formula, branches = actual_python_g14_artifacts(instance_id)
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
    row_values = [
        _serialize_rows(cert.gaussian_elimination_trace[0]["rows"])
        for _, _, _, _, cert in branches
    ]
    # Obtain native affine-extraction evidence for *every* residual
    # component, not just the branch-selected UNSAT witness.
    all_component_rows = []
    all_component_statuses = []
    for assignment, _residual, parts, chosen, selected_cert in branches:
        branch_rows = []
        branch_statuses = []
        for index, component in enumerate(parts):
            if component is chosen:
                component_cert = selected_cert
            else:
                component_cert = build_affine_residue_certificate(
                    AffineResidueInstance(
                        instance_id=f"g14_all_{instance_id}_{int(assignment[1])}_{index}",
                        equations=(), formula=component,
                    ), max_arity=2,
                )
            trace = component_cert.gaussian_elimination_trace
            if not trace or trace[0].get("type") != "INITIAL_ROWS":
                raise ValueError("component missing native affine initial rows")
            if component_cert.checker_status != AFFINE_RESIDUE_CERTIFICATE_VERIFIED:
                raise ValueError("component missing accepted native affine evidence")
            branch_rows.append(_serialize_rows(trace[0]["rows"]))
            branch_statuses.append(component_cert.status)
        all_component_rows.append("[" + ", ".join(branch_rows) + "]")
        all_component_statuses.append(branch_statuses)

    if instance_id is not None:
        native_statuses = [status for branch in all_component_statuses
                           for status in branch]
        if (AFFINE_RESIDUE_SAT_WITNESS_VERIFIED not in native_statuses
                or AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED not in native_statuses):
            raise ValueError("fixture must cover both SAT and UNSAT affine components")

    steps = [
        _compile_dag(cert.gaussian_elimination_trace[0]["rows"],
                     cert.row_operations)
        for _, _, _, _, cert in branches
    ]

    lines = [
        "import Witnora.G14ConcreteBridge",
        "import Witnora.ExactAffineMembership",
        "import Witnora.TC063CanonicalComplete",
        "namespace Witnora.GeneratedPythonG14",
        "open Witnora.Concrete",
        "open Witnora.G14ConcreteBridge",
        "open Witnora.G5Extraction",
        "open Witnora.ComponentPartition",
        "open Witnora.Conditioning",
        "open Witnora.SeparatorAssignments",
        "open Witnora.SignedSerialization",
        "open Witnora.SparseBridge",
        "open Witnora.ExactAffineMembership",
        "open Witnora.DIMACSDocument",
        "open Witnora.DIMACSTokens",
        "set_option maxRecDepth 8192",
        "set_option maxHeartbeats 4000000",
        f"def pythonSourceBytes : List Nat := {lean_nat(data)}",
        f"def pythonTokens : List Int := {lean_nat(token_stream)}",
        f"def pythonClauses : List (List Int) := {raw}",
        branch_definition("pythonComponents", "List CNF", cs, "[]"),
        branch_definition("pythonSelected", "CNF", selected, "[]"),
        branch_definition("pythonAllRows", "List (List Witnora.G5Trace.Row)", all_component_rows, "[]"),
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
    # Test the stricter clause-permutation criterion separately: native
    # G5 rows may leave redundant clauses in a selected residual component.
    lines.append(premise("python_selected_strict_affine_rejected",
        """∀ branch ∈ enumerate [1],
      checkExactAffine 2 (pythonSelected branch)
        (pythonRows branch) = false"""))
    # Check the full model-equivalence criterion, allowing proved redundancy.
    lines.append(premise("python_selected_semantic_affine_pass",
        """∀ branch ∈ enumerate [1],
      checkSemanticExactAffine 2 (pythonSelected branch)
        (pythonRows branch) = true"""))
    # Turn actual Python-selected G5 rows into a canonical sparse witness
    # using the universal Lean theorem; no assumption about Python row order.
    lines.append("""theorem python_selected_canonical_witness :
    ∀ branch ∈ enumerate [1],
      ∃ (bound : Nat) (rows : List Witnora.G5Trace.Row),
        checkSemanticExactAffine 2 (pythonSelected branch) rows = true ∧
        checkCanonicalRows bound rows = true := by
  intro branch hb
  exact Witnora.TC063CanonicalComplete.canonical_witness_complete 2
    (pythonSelected branch)
    ⟨pythonRows branch, python_selected_semantic_affine_pass branch hb⟩""")
    lines.append(
        "#print axioms Witnora.GeneratedPythonG14.python_selected_canonical_witness"
    )
    # Length equality prevents zipWith from silently skipping a residual.
    lines.append(premise("python_all_component_lengths_pass",
        """∀ branch ∈ enumerate [1],
      (pythonComponents branch).length = (pythonAllRows branch).length"""))
    lines.append(premise("python_all_components_semantic_affine_pass",
        """∀ branch ∈ enumerate [1],
      (List.zipWith (fun component rows =>
        checkSemanticExactAffine 2 component rows)
        (pythonComponents branch) (pythonAllRows branch)).all id = true"""))
    if instance_id is not None:
        lines.extend([
            """theorem python_missing_component_rejected :
    checkPartition
      (conditionCNF (fixedOf [(1, false)]) (decodeCNF pythonClauses))
      [pythonSelected [(1, false)]] = false := by
  decide""",
            """theorem python_invalid_g5_reference_rejected :
    checkG5Closed (pythonBound [(1, false)])
      (pythonSelected [(1, false)]) (pythonRows [(1, false)])
      [(999, 0)] = false := by
  decide""",
        ])
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
