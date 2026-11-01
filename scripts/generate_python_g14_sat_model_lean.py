"""Generate Lean-checkable SAT residual-model evidence from real Python G14 output.

This uses Witnora's production CNF conditioning/component routines. It does
not assert universal CPython-to-Lean refinement; every emitted instance is
independently evaluated by the Lean kernel, including adversarial mutations.
"""
from pathlib import Path

from witnora_core.cnf import CNFFormula
from witnora_core.separator_affine_family_theorem import (
    _all_assignments,
    _component_dicts,
    _condition_by_separator,
)
from witnora_core.python_g14_lean_artifact import lean_cnf, lean_branch


RAW = [[1, 2], [-1, 3], [4]]
SEPARATOR = (1,)


def emit_sat_model_transfer() -> str:
    formula = CNFFormula.from_raw_clauses(RAW)
    component_specs = _component_dicts(formula, list(SEPARATOR))
    assignments = _all_assignments(SEPARATOR)
    if [lean_branch(a) for a in assignments] != ["[(1, false)]", "[(1, true)]"]:
        raise ValueError("unexpected Python separator enumeration")
    component_values = []
    for assignment in assignments:
        residual, parts, errors = _condition_by_separator(
            formula, assignment, component_specs
        )
        if errors or len(parts) != 2:
            raise ValueError(f"invalid Python components: {errors}")
        expected = sorted(tuple(c) for c in residual.to_clause_lists())
        actual = sorted(
            tuple(c) for part in parts.values() for c in part.to_clause_lists()
        )
        if expected != actual:
            raise ValueError("Python residual clause loss or duplication")
        component_values.append("[" + ", ".join(lean_cnf(p) for p in parts.values()) + "]")

    a_false, a_true = (lean_branch(a) for a in assignments)
    # The source CNF and the two distinct residuals come from Python,
    # not from a duplicated hand-authored Lean sample.
    lines = [
        "import Witnora.G14ConcreteBridge",
        "namespace Witnora.GeneratedPythonG14Sat",
        "open Witnora.Concrete",
        "open Witnora.FiniteXor",
        "open Witnora.Extraction",
        "open Witnora.G5Extraction",
        "open Witnora.Conditioning",
        "open Witnora.ComponentPartition",
        "open Witnora.SeparatorAssignments",
        f"def source : CNF := {lean_cnf(formula)}",
        "def pythonComponents (branch : List (Nat × Bool)) : List CNF :=",
        f"  if branch == {a_false} then {component_values[0]}",
        f"  else if branch == {a_true} then {component_values[1]} else []",
        """theorem python_partitions_pass :
    ∀ branch ∈ enumerate [1],
      checkPartition
        (conditionCNF (fixedOf branch) source)
        (pythonComponents branch) = true := by
  intro branch hb
  have hcases : branch = [(1, false)] ∨ branch = [(1, true)] := by
    simpa [enumerate] using hb
  rcases hcases with hf | ht
  · subst branch
    decide
  · subst branch
    decide""",
        """theorem python_residual_models_iff
    (branch : List (Nat × Bool)) (hb : branch ∈ enumerate [1])
    (a : Nat → Bool) (hag : agreesWith (fixedOf branch) a) :
    CNFHolds source a ↔
      (pythonComponents branch).all
        (fun component => component.all
          (fun clause => clause.any (signedLitTrue a))) = true := by
  exact conditioned_partition_correct
    (fixedOf branch) source (pythonComponents branch)
    (python_partitions_pass branch hb) a hag""",
        """def validWitness (v : Nat) : Bool := v == 2 || v == 4

theorem python_valid_source_model :
    CNFHolds source validWitness := by
  simp [CNFHolds, source, validWitness, signedLitTrue]""",
        """theorem python_valid_false_branch_model :
    CNFHolds ((pythonComponents [(1, false)]).flatten)
      validWitness := by
  simp [CNFHolds, pythonComponents, validWitness, signedLitTrue]""",
        """def wrongBranchWitness (v : Nat) : Bool :=
  v == 1 || v == 3 || v == 4

theorem python_wrong_branch_counterexample :
    CNFHolds source wrongBranchWitness ∧
    ¬ CNFHolds ((pythonComponents [(1, false)]).flatten)
      wrongBranchWitness := by
  simp [CNFHolds, source, pythonComponents,
    wrongBranchWitness, signedLitTrue]""",
        """theorem python_swapped_branch_rejected :
    checkPartition
      (conditionCNF (fixedOf [(1, false)]) source)
      (pythonComponents [(1, true)]) = false := by decide""",
        """theorem python_missing_component_rejected :
    checkPartition
      (conditionCNF (fixedOf [(1, false)]) source)
      ((pythonComponents [(1, false)]).take 1) = false := by decide""",
        "#print axioms Witnora.GeneratedPythonG14Sat.python_residual_models_iff",
        "#print axioms Witnora.GeneratedPythonG14Sat.python_wrong_branch_counterexample",
        "end Witnora.GeneratedPythonG14Sat",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    target = Path("formal/Witnora/GeneratedPythonG14Sat.lean")
    target.write_text(emit_sat_model_transfer(), encoding="utf-8")
    print(f"Emitted {target}")


if __name__ == "__main__":
    main()
