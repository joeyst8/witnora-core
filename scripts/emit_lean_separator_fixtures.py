"""Emit Lean claims for independent finite CNF-branch checking.

Python serializes the original formula and its actual G14-conditioned
components. Lean independently checks equivalence by exhaustive evaluation.
This bounded regression test is not a proof about every Python execution.
"""
from pathlib import Path
from witnora_core.separator_affine_family_theorem import (
    _all_assignments, _component_dicts, _condition_by_separator,
    make_separator_affine_instance, build_separator_affine_certificate,
    check_separator_affine_certificate, SAT_CERTIFIED, UNSAT_CERTIFIED,
)

CASES = ("saf_sat_chain_2", "saf_unsat_cover_2", "saf_balanced_sat_2")

def lean_bool(value):
    return "true" if value else "false"

def lean_cnf(formula):
    rows = []
    for clause in formula.to_clause_lists():
        lits = [f"({abs(lit)}, {lean_bool(lit > 0)})" for lit in clause]
        rows.append("[" + ", ".join(lits) + "]")
    return "[" + ", ".join(rows) + "]"

def lean_partial_assignment(assignment):
    """Render a closed Lean function, with no Python-controlled Lean syntax."""
    body = "none"
    for var in sorted(assignment, reverse=True):
        body = f"(if v == {var} then some {lean_bool(assignment[var])} else {body})"
    return "(fun v : Nat => " + body + ")"


def main():
    out = [
        "import Witnora.Concrete",
        "import Witnora.Verdict",
        "import Witnora.ComponentPartition",
        "import Witnora.SeparatorAssignments",
        "import Witnora.SignedSerialization",
        "",
        "/- Actual G14 Python conditioning outputs; independent Lean claims. -/",
        "namespace Witnora.Generated",
    ]
    count = 0
    for name in CASES:
        instance = make_separator_affine_instance(name)
        n = max(instance.formula.variables, default=0)
        if n > 10:
            raise RuntimeError("bounded fixture too large")
        cert = build_separator_affine_certificate(instance)
        # Exact integer-to-polarity correspondence for original Python CNF.
        out.append(
            "example : Witnora.SignedSerialization.decodeCNF "
            f"{instance.formula.to_clause_lists()} = {lean_cnf(instance.formula)} := by decide"
        )
        check = check_separator_affine_certificate(instance.formula, cert)
        if check["checker_status"] != "SEPARATOR_AFFINE_CERTIFICATE_VERIFIED":
            raise RuntimeError(f"{name}: Python certificate rejected")
        if cert.final_result == SAT_CERTIFIED:
            predicate = "isSat"
        elif cert.final_result == UNSAT_CERTIFIED:
            predicate = "isUnsat"
        else:
            raise RuntimeError(f"{name}: no certified result")
        out.append(
            f"example : Witnora.Concrete.{predicate} {n} "
            f"{lean_cnf(instance.formula)} = true := by decide"
        )
        claimed_sat = lean_bool(cert.final_result == SAT_CERTIFIED)
        out.append(
            f"example : Witnora.Verdict.accepts {n} "
            f"{lean_cnf(instance.formula)} {claimed_sat} = true := by decide"
        )
        comps = _component_dicts(instance.formula, instance.separator_variables)
        assignments = _all_assignments(instance.separator_variables)
        ordered_vars = sorted(instance.separator_variables)
        serialized_patterns = "[" + ", ".join(
            "[" + ", ".join(f"({v}, {lean_bool(a[v])})" for v in ordered_vars) + "]"
            for a in assignments
        ) + "]"
        out.append(
            "example : Witnora.SeparatorAssignments.enumerate "
            f"{ordered_vars} = {serialized_patterns} := by decide"
        )
        for a in assignments:
            _, parts, errors = _condition_by_separator(instance.formula, a, comps)
            if errors:
                raise RuntimeError(f"{name}: unexpected conditioning errors {errors}")
            fixed = "[" + ", ".join(
                f"({v}, {lean_bool(a[v])})" for v in sorted(a)
            ) + "]"
            component_list = "[" + ", ".join(
                lean_cnf(parts[c["component_id"]]) for c in comps
            ) + "]"
            for component in comps:
                component_formula = parts[component["component_id"]]
                out.append(
                    "example : Witnora.SignedSerialization.decodeCNF "
                    f"{component_formula.to_clause_lists()} = "
                    f"{lean_cnf(component_formula)} := by decide"
                )
            out.append(
                f"example : Witnora.Concrete.checkBranch {n} "
                f"{lean_cnf(instance.formula)} {fixed} {component_list} = true := by decide"
            )
            # Independently evaluate the universally proved conditioning and
            # multiset partition checker on the real Python residual clauses.
            partition_check = (
                "Witnora.ComponentPartition.checkPartition "
                "(Witnora.Conditioning.conditionCNF "
                f"{lean_partial_assignment(a)} {lean_cnf(instance.formula)}) "
            )
            out.append(f"example : {partition_check}{component_list} = true := by decide")
            out.append(f"example : {partition_check}[] = false := by decide")
            if name == "saf_sat_chain_2" and not any(a.values()):
                out.append(
                    f"example : Witnora.Concrete.checkBranch {n} "
                    f"{lean_cnf(instance.formula)} {fixed} [] = false := by decide"
                )
            count += 1
    out.extend(["", "end Witnora.Generated", ""])
    target = Path("formal/Witnora/Generated.lean")
    target.write_text("\n".join(out), encoding="utf-8")
    print(f"Emitted {count} Lean checks to {target}")

if __name__ == "__main__":
    main()
