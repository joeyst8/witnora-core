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

SAT_LEVEL_NOT_SAT = "NOT_SAT"
SAT_LEVEL_RECONSTRUCTED = "RECONSTRUCTED_ASSIGNMENT_VERIFIED_ORIGINAL"
SAT_LEVEL_INDEPENDENT_RAW = "INDEPENDENT_RAW_CHECKER_VERIFIED"

UNSAT_LEVEL_NOT_UNSAT = "NOT_UNSAT"
UNSAT_LEVEL_EXPLICIT_EMPTY = "EXPLICIT_EMPTY_CLAUSE"
UNSAT_LEVEL_2SAT_SCC = "INDEPENDENT_2SAT_SCC"
UNSAT_LEVEL_INTERNAL_REPLAY = "INTERNAL_REPLAY_ONLY"
UNSAT_LEVEL_EXTERNAL_STANDARD = "EXTERNAL_DRAT_LRAT_FRAT_VERIFIED"
UNSAT_LEVEL_LRAT_FRAT_NOT_IMPLEMENTED = "LRAT_FRAT_NOT_IMPLEMENTED"

PROOF_TRACE_SAT = "SAT_ASSIGNMENT_RECONSTRUCTION"
PROOF_TRACE_UNSAT_EMPTY = "UNSAT_EXPLICIT_EMPTY_CLAUSE"
PROOF_TRACE_UNSAT_2SAT = "UNSAT_2SAT_SCC_CONTRADICTION"
PROOF_TRACE_UNSAT_INTERNAL = "UNSAT_INTERNAL_REPLAY_ONLY"
PROOF_TRACE_NO_COLLAPSE = "NO_COLLAPSE_REPORT"

NATIVE_UNSAT_TRACE_FORMAT = "WITNORA_NATIVE_UNSAT_TRACE_V1"


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


def sat_certification_level(
    status: str,
    original_verification: bool,
    *,
    independent_raw_checker_verified: bool = False,
) -> str:
    if status != SAT:
        return SAT_LEVEL_NOT_SAT
    if independent_raw_checker_verified:
        return SAT_LEVEL_INDEPENDENT_RAW
    if original_verification:
        return SAT_LEVEL_RECONSTRUCTED
    return SAT_LEVEL_NOT_SAT


def _contains_logged_empty_clause(steps: list["CollapseStep"]) -> bool:
    return any(clause == [] for step in steps for clause in step.added_clauses)


def unsat_certification_level_from_steps(status: str, steps: list["CollapseStep"]) -> str:
    if status != UNSAT:
        return UNSAT_LEVEL_NOT_UNSAT
    if _contains_logged_empty_clause(steps):
        return UNSAT_LEVEL_EXPLICIT_EMPTY
    if any(
        step.type == "2SAT_SOLVE" and step.details.get("status") == "UNSAT"
        for step in steps
    ):
        return UNSAT_LEVEL_2SAT_SCC
    return UNSAT_LEVEL_INTERNAL_REPLAY


def proof_trace_class_from_status(status: str, unsat_level: str) -> str:
    if status == SAT:
        return PROOF_TRACE_SAT
    if status == UNSAT:
        if unsat_level == UNSAT_LEVEL_EXPLICIT_EMPTY:
            return PROOF_TRACE_UNSAT_EMPTY
        if unsat_level == UNSAT_LEVEL_2SAT_SCC:
            return PROOF_TRACE_UNSAT_2SAT
        return PROOF_TRACE_UNSAT_INTERNAL
    return PROOF_TRACE_NO_COLLAPSE


def _scc_for_literal(sccs: list[list[int]], literal: int) -> list[int]:
    for component in sccs:
        if literal in component:
            return list(component)
    return []


def native_unsat_trace_from_steps(status: str, steps: list["CollapseStep"]) -> dict[str, Any] | None:
    level = unsat_certification_level_from_steps(status, steps)
    if level == UNSAT_LEVEL_EXPLICIT_EMPTY:
        for step in steps:
            if [] not in step.added_clauses:
                continue
            trace_step: dict[str, Any]
            if step.type == "VE":
                generated_empty = next(
                    (
                        item
                        for item in step.details.get("generated_resolvents", [])
                        if item.get("resolvent") == []
                    ),
                    {},
                )
                trace_step = {
                    "type": "VE_EMPTY_RESOLVENT",
                    "source_step_id": step.step_id,
                    "eliminated_variable": step.details.get("eliminated_variable"),
                    "positive_clause": list(generated_empty.get("positive_clause", [])),
                    "negative_clause": list(generated_empty.get("negative_clause", [])),
                    "derived_empty_clause": [],
                }
            else:
                shortened = step.details.get("shortened_clauses", [])
                conflict_clause: list[int] = []
                for item in shortened:
                    if item.get("to") == []:
                        conflict_clause = list(item.get("from", []))
                        break
                trace_step = {
                    "type": "UNIT_PROPAGATION_CONFLICT",
                    "source_step_id": step.step_id,
                    "unit_literal": step.assigned_literals[0]
                    if step.assigned_literals
                    else step.details.get("assigned_literal"),
                    "conflicting_clause": conflict_clause,
                    "derived_empty_clause": [],
                }
            return {
                "proof_trace_format": NATIVE_UNSAT_TRACE_FORMAT,
                "unsat_reason": UNSAT_LEVEL_EXPLICIT_EMPTY,
                "depends_on_replayed_collapse_path": True,
                "steps": [trace_step],
                "external_standard": "NONE",
                "lrat_frat_status": "NOT_EXPORTED",
            }
    if level == UNSAT_LEVEL_2SAT_SCC:
        for step in steps:
            if step.type != "2SAT_SOLVE" or step.details.get("status") != "UNSAT":
                continue
            variable = int(step.details.get("conflict_variable", 0))
            sccs = [list(component) for component in step.details.get("sccs", [])]
            return {
                "proof_trace_format": NATIVE_UNSAT_TRACE_FORMAT,
                "unsat_reason": UNSAT_LEVEL_2SAT_SCC,
                "depends_on_replayed_collapse_path": True,
                "source_step_id": step.step_id,
                "variable": variable,
                "positive_literal_scc": _scc_for_literal(sccs, variable),
                "negative_literal_scc": _scc_for_literal(sccs, -variable),
                "implication_edges": [
                    [int(src), int(dst)]
                    for src, dst in step.details.get("edges", [])
                ],
                "external_standard": "NONE",
                "lrat_frat_status": "NOT_EXPORTED",
            }
    return None


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

    @property
    def sat_certification_level(self) -> str:
        return sat_certification_level(self.status, self.original_verification)

    @property
    def unsat_certification_level(self) -> str:
        return unsat_certification_level_from_steps(self.status, self.steps)

    @property
    def proof_trace_class(self) -> str:
        return proof_trace_class_from_status(self.status, self.unsat_certification_level)

    @property
    def native_proof_trace(self) -> dict[str, Any] | None:
        return native_unsat_trace_from_steps(self.status, self.steps)

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
            "sat_certification_level": self.sat_certification_level,
            "unsat_certification_level": self.unsat_certification_level,
            "proof_trace_class": self.proof_trace_class,
            "native_proof_trace": self.native_proof_trace,
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
            "sat_certification_level": self.sat_certification_level,
            "unsat_certification_level": self.unsat_certification_level,
            "proof_trace_class": self.proof_trace_class,
            "native_proof_trace": self.native_proof_trace,
            "stats": self.stats,
        }
