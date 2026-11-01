"""Emit Lean checks of the actual Python G14 primal-graph DFS labels."""
from pathlib import Path

from witnora_core.cnf import CNFFormula
from witnora_core.python_g14_lean_artifact import lean_cnf
from witnora_core.separator_affine_family_theorem import _component_dicts
from scripts.generate_g14_adversarial_matrix_lean import CASES, _random_case


def _lean_labels(labels: dict[int, int]) -> str:
    result = "0"
    for variable, component in sorted(labels.items(), reverse=True):
        result = f"(if v == {variable} then {component} else {result})"
    return f"(fun v : Nat => {result})"


def emit_dfs_labels(random_cases: int = 16) -> tuple[str, dict[str, int]]:
    if not 0 <= random_cases <= 64:
        raise ValueError("unsupported random case count")
    cases = list(CASES) + [_random_case(i) for i in range(random_cases)]
    lines = [
        "import Witnora.G14DFSLabelCheck",
        "namespace Witnora.GeneratedG14DFSLabels",
        "open Witnora.Concrete",
        "open Witnora.G14DFSLabelCheck",
        "set_option maxRecDepth 8192",
        "set_option maxHeartbeats 0",
    ]
    counts = {"cases": 0, "source_variables": 0, "negative_label_tests": 0}
    for idx, (name, raw, separator) in enumerate(cases):
        formula = CNFFormula.from_raw_clauses(raw)
        specs = _component_dicts(formula, list(separator))
        labels: dict[int, int] = {}
        for cid, spec in enumerate(specs, start=1):
            for var in spec["variables"]:
                if var in labels:
                    raise ValueError(f"Python DFS assigned variable {var} twice")
                labels[var] = cid
        expected = set(formula.variables) - set(separator)
        if set(labels) != expected:
            raise ValueError(f"Python DFS missed variable(s) in {name}")
        source = f"source{idx}"
        label = f"label{idx}"
        lines.extend([
            f"-- {name}",
            f"def {source} : CNF := {lean_cnf(formula)}",
            f"def {label} : Nat → Nat := {_lean_labels(labels)}",
            f"example : checkAllVariablesLabeled {source} {list(separator)} "
            f"{sorted(labels)} = true := by decide",
            f"example : checkGraphEdgeLabels {source} {list(separator)} "
            f"{label} = true := by decide",
        ])
        counts["cases"] += 1
        counts["source_variables"] += len(labels)
    # The same checker must reject an actual nonseparator graph edge
    # whose two endpoints receive conflicting labels.
    lines.extend([
        "def adversarial : CNF := [[(3, true), (4, false)]]",
        "example : checkGraphEdgeLabels adversarial [] "
        "(fun v => if v == 3 then 1 else 2) = false := by decide",
        "example : checkAllVariablesLabeled adversarial [] [3] "
        "= false := by decide",
        "#print axioms Witnora.G14DFSLabelCheck.checked_labels_residual_unique",
        "end Witnora.GeneratedG14DFSLabels",
        "",
    ])
    counts["negative_label_tests"] = 2
    return "\n".join(lines), counts


def main() -> None:
    source, counts = emit_dfs_labels()
    path = Path("formal/Witnora/GeneratedG14DFSLabels.lean")
    path.write_text(source, encoding="utf-8")
    print({"path": str(path), **counts})


if __name__ == "__main__":
    main()
