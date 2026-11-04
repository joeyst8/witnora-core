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


def replay_root_component_certificate_in_rust(
    original: CNFFormula,
    steps: list[CollapseStep],
    width_cap: int,
    final_formula_hash: str,
) -> tuple[bool, CNFFormula, str | None]:
    """Replay one root CD and later component-local non-CD transitions.

    This deliberately excludes nested CD, component_results, final status and
    SAT/UNSAT soundness checks; Python remains the default full-path verifier.
    """
    if not steps or steps[0].type != "CD":
        raise ValueError("native component replay requires initial root CD")
    root = steps[0]
    if root.step_id != 1 or root.details.get("parent_component_id") is not None:
        raise ValueError("native component replay requires a step-1 root CD")
    if any(step.type == "CD" for step in steps[1:]):
        raise ValueError("native component replay does not support nested CD")
    from witnora_ve import replay_root_component_certificate_native

    details = root.details
    records = [
        (
            int(row["component_id"]), str(row["formula_hash"]),
            [int(var) for var in row.get("variables", [])],
            [[int(var) for var in clause] for clause in row.get("clauses", [])],
            [int(idx) for idx in row.get("clause_indices", [])],
        )
        for row in details.get("components", [])
    ]
    events = []
    for step in steps[1:]:
        if step.type not in SUPPORTED:
            raise ValueError(f"unsupported native local replay step {step.type}")
        cid = step.details.get("component_id")
        events.append((
            str(cid) if cid is not None else None,
            (
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
            ),
        ))
    ok, clauses, error = replay_root_component_certificate_native(
        original.to_clause_lists(), root.input_formula_hash,
        root.output_formula_hash, int(details.get("component_count", 0)),
        [tuple(int(v) for v in edge)
         for edge in details.get("incidence_edges", [])],
        records, events, int(width_cap), final_formula_hash,
    )
    return bool(ok), CNFFormula.from_raw_clauses(clauses), error
