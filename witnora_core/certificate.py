"""Structured collapse-path certificate objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any

from .cnf import CNFFormula

SAT = "SAT"
UNSAT = "UNSAT"
NO_COLLAPSE = "NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C"
RECONSTRUCTION_FAILURE = "RECONSTRUCTION_FAILURE"
TIMEOUT = "TIMEOUT"


def _normalise_assignment(assignment: dict[int, bool] | dict[str, bool]) -> dict[str, bool]:
    return {str(int(var)): bool(value) for var, value in sorted(assignment.items(), key=lambda kv: int(kv[0]))}


def _normalise_component_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalised: list[dict[str, Any]] = []
    for result in sorted(results, key=lambda item: str(item.get("component_id", ""))):
        normalised.append(
            {
                "component_id": str(result.get("component_id", "")),
                "status": str(result.get("status", "")),
                "final_class": str(result.get("final_class", "")),
                "formula_hash": str(result.get("formula_hash", "")),
                "assignment": _normalise_assignment(result.get("assignment", {})),
            }
        )
    return normalised


@dataclass
class CollapseStep:
    step_id: int
    type: str
    input_formula_hash: str
    output_formula_hash: str
    details: dict[str, Any] = field(default_factory=dict)
    removed_clauses: list[list[int]] = field(default_factory=list)
    added_clauses: list[list[int]] = field(default_factory=list)
    assigned_literals: list[int] = field(default_factory=list)
    reconstruction_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "type": self.type,
            "input_formula_hash": self.input_formula_hash,
            "output_formula_hash": self.output_formula_hash,
            "details": self.details,
            "removed_clauses": self.removed_clauses,
            "added_clauses": self.added_clauses,
            "assigned_literals": self.assigned_literals,
            "reconstruction_data": self.reconstruction_data,
        }


class StepLogger:
    def __init__(self) -> None:
        self.steps: list[CollapseStep] = []

    def append(
        self,
        step_type: str,
        input_formula: CNFFormula,
        output_formula: CNFFormula,
        *,
        details: dict[str, Any] | None = None,
        removed_clauses: list[list[int]] | None = None,
        added_clauses: list[list[int]] | None = None,
        assigned_literals: list[int] | None = None,
        reconstruction_data: dict[str, Any] | None = None,
    ) -> CollapseStep:
        step = CollapseStep(
            step_id=len(self.steps) + 1,
            type=step_type,
            input_formula_hash=input_formula.formula_hash,
            output_formula_hash=output_formula.formula_hash,
            details=details or {},
            removed_clauses=removed_clauses or [],
            added_clauses=added_clauses or [],
            assigned_literals=assigned_literals or [],
            reconstruction_data=reconstruction_data or {},
        )
        self.steps.append(step)
        return step


@dataclass
class CollapsePath:
    original_formula_hash: str
    c_parameter: int
    steps: list[CollapseStep]
    final_formula_hash: str
    final_class: str
    status: str
    final_assignment: dict[int, bool] = field(default_factory=dict)
    reconstructed_original_assignment: dict[int, bool] = field(default_factory=dict)
    original_verification: bool = False
    component_results: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    def certificate_payload(self) -> dict[str, Any]:
        return {
            "original_formula_hash": self.original_formula_hash,
            "c_parameter": self.c_parameter,
            "collapse_path": [step.to_dict() for step in self.steps],
            "final_class": self.final_class,
            "final_assignment": _normalise_assignment(self.final_assignment),
            "reconstructed_original_assignment": _normalise_assignment(
                self.reconstructed_original_assignment
            ),
            "original_verification": self.original_verification,
            "component_results": _normalise_component_results(self.component_results),
        }

    @property
    def certificate_hash(self) -> str:
        payload = json.dumps(self.certificate_payload(), sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "original_formula_hash": self.original_formula_hash,
            "c_parameter": self.c_parameter,
            "certificate_hash": self.certificate_hash,
            "collapse_path": [step.to_dict() for step in self.steps],
            "final_formula_hash": self.final_formula_hash,
            "final_class": self.final_class,
            "final_assignment": _normalise_assignment(self.final_assignment),
            "reconstructed_original_assignment": _normalise_assignment(
                self.reconstructed_original_assignment
            ),
            "original_verification": self.original_verification,
            "component_results": _normalise_component_results(self.component_results),
            "stats": self.stats,
        }
