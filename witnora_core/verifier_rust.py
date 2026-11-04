"""R-030 strictly scoped Rust replay of local deterministic CNF proof steps."""
from __future__ import annotations

from witnora_core.certificate import CollapseStep
from witnora_core.cnf import CNFFormula

SUPPORTED = frozenset({"UP", "PLE", "SUB", "BCE", "VE", "2SAT_SOLVE", "TREEWIDTH_SOLVE"})


def replay_local_certificate_in_rust(
    original: CNFFormula,
    steps: list[CollapseStep],
    width_cap: int,
    final_formula_hash: str,
) -> tuple[bool, CNFFormula, str | None]:
    """Replay non-component deterministic CNF, treewidth and two-SAT steps.

    This checks local proof transitions, not overall SAT/UNSAT certification.
    """
    from witnora_ve import replay_local_certificate_native

    packed = []
    for step in steps:
        if step.type not in SUPPORTED:
            raise ValueError(f"unsupported native local replay step {step.type}")
        if step.details.get("component_id") is not None:
            raise ValueError("native local replay does not support component contexts")
        packed.append((
            step.type, int(step.step_id),
            step.input_formula_hash, step.output_formula_hash,
            list(step.assigned_literals),
            [list(c) for c in step.removed_clauses],
            [list(c) for c in step.added_clauses],
            (
                list(step.details.get("subsuming_clause", [])),
                int(step.details.get("blocked_literal", 0)),
                str(step.details.get("proof_digest", "")),
                int(step.reconstruction_data.get("eliminated_variable", 0)),
            ),
            (
                [int(var) for var in step.details.get("elimination_order", [])],
                [tuple(int(v) for v in edge) for edge in
                 step.details.get("primal_edges", [])],
                str(step.details.get("status", "")),
                [(int(var), bool(value)) for var, value in
                 step.details.get("assignment", {}).items()],
            ),
        ))
    ok, clauses, error = replay_local_certificate_native(
        original.to_clause_lists(), packed, int(width_cap), final_formula_hash,
    )
    return bool(ok), CNFFormula.from_raw_clauses(clauses), error


def verify_cd_step_in_rust(
    step: CollapseStep, current: CNFFormula,
) -> tuple[bool, dict[str, CNFFormula], str | None]:
    """Verify a CD step in Rust and materialize only authenticated children.

    Opt-in, non-recursive: the trusted Python verifier remains the default
    for certificate DAGs and final SAT/UNSAT outcomes.
    """
    if step.type != "CD":
        raise ValueError("native CD verifier only accepts CD steps")
    from witnora_ve import verify_cd_children_native

    details = step.details
    verified, children, error = verify_cd_children_native(
        current.to_clause_lists(), step.output_formula_hash,
        int(details.get("component_count", 0)),
        [tuple(int(v) for v in edge)
         for edge in details.get("incidence_edges", [])],
        [
            (
                int(record["component_id"]), str(record["formula_hash"]),
                [int(v) for v in record.get("variables", [])],
                [[int(v) for v in clause] for clause in record.get("clauses", [])],
                [int(idx) for idx in record.get("clause_indices", [])],
            )
            for record in details.get("components", [])
        ],
    )
    return bool(verified), {
        component_id: CNFFormula.from_raw_clauses(clauses)
        for component_id, clauses in children
    }, error
