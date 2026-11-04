"""R-030 strictly scoped Rust replay of local deterministic CNF proof steps."""
from __future__ import annotations

from witnora_core.certificate import CollapseStep
from witnora_core.cnf import CNFFormula

SUPPORTED = frozenset({"UP", "PLE", "SUB", "BCE", "VE"})


def replay_local_certificate_in_rust(
    original: CNFFormula,
    steps: list[CollapseStep],
    width_cap: int,
    final_formula_hash: str,
) -> tuple[bool, CNFFormula, str | None]:
    """Replay only non-component UP/PLE/SUB/BCE/VE source formula steps.

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
        ))
    ok, clauses, error = replay_local_certificate_native(
        original.to_clause_lists(), packed, int(width_cap), final_formula_hash,
    )
    return bool(ok), CNFFormula.from_raw_clauses(clauses), error
