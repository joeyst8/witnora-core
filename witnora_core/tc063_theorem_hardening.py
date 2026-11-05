"""TC-063 hardening artifacts for Witnora v2.23.

This module hardens the bounded separator-affine theorem record without
upgrading it to an unqualified proven theorem. It records formal lemma
statements, proof obligations, dependency boundaries, a structural SAF(c,r)
membership validator, and scaling evidence that remains implementation support
only.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Iterable
import zipfile

from .cnf import CNFFormula
from .obstruction_dual import sha256_file, stable_json
from .operator_genesis import AFFINE_RESIDUE_CERTIFICATE_VERIFIED, check_affine_residue_certificate
from .separator_affine_family_theorem import (
    DIAGNOSTIC_ONLY,
    SAT_CERTIFIED,
    UNSAT_CERTIFIED,
    _affine_component_certificate,
    _affine_source_clause_coverage,
    _all_assignments,
    _component_dicts,
    _condition_by_separator,
    build_separator_affine_certificate,
    check_separator_affine_certificate,
    make_separator_affine_instance,
    recognize_separator_affine_family,
)


VERSION = "2.23"
THEOREM_ID = "TC-063"
PRIOR_STATUS = "RESTRICTED_FAMILY_THEOREM_PROOF_SKETCH"
HARDENED_STATUS = "RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS"
FALLBACK_STATUS = "RESTRICTED_FAMILY_THEOREM_PROOF_SKETCH_HARDENED"

TC063_THEOREM_HARDENING_VERIFIED = "TC063_THEOREM_HARDENING_VERIFIED"
TC063_THEOREM_HARDENING_FAILED = "TC063_THEOREM_HARDENING_FAILED"
SAF_MEMBER_VERIFIED = "SAF_MEMBER_VERIFIED"
SAF_MEMBER_REJECTED = "SAF_MEMBER_REJECTED"
SAF_DIAGNOSTIC_ONLY = "SAF_DIAGNOSTIC_ONLY"

ALLOWED_HARDENED_STATUSES = {HARDENED_STATUS, FALLBACK_STATUS}
FORBIDDEN_STATUSES = {
    "THEOREM_PROVEN_UNQUALIFIED",
    "COMPLETE",
    "PNP_PROGRESS",
    "ALL_SAT",
    "HARD",
    "UNKNOWN",
}
FORBIDDEN_CLAIM_FRAGMENTS = {
    "claims p vs np progress",
    "proves p vs np progress",
    "claims polynomial-time sat",
    "proves polynomial-time sat",
    "claims all sat",
    "proves all sat",
    "claims hierarchy completeness",
    "proves hierarchy completeness",
    "theorem proven unqualified",
    "drat proof claimed",
}

SAF_DEFINITION_TEXT = (
    "SAF(c,r) is the restricted family of CNF formulas with a variable separator "
    "S of size at most fixed c such that every total assignment to S leaves "
    "independent residual components, and every residual component is an exact "
    "GF(2) affine CNF accepted by G5 under supported affine bound r."
)


@dataclass(frozen=True)
class SAFMembershipValidation:
    formula_hash: str
    separator_bound_c: int
    affine_bound_r: int
    separator_variables: list[int]
    separator_size: int
    components: list[dict[str, Any]]
    separator_assignment_count: int
    every_assignment_localized: bool
    every_component_affine_verified: bool
    invalid_reason: str | None
    validation_status: str
    polynomial_bound_record: dict[str, Any]
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LemmaRecord:
    lemma_id: str
    lemma_name: str
    formal_statement: str
    assumptions: list[str]
    proof_sketch: str
    proof_obligations: list[str]
    dependency_on_modules: list[str]
    status: str
    may_not_be_claimed_as_fully_proven: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TC063TheoremHardeningRecord:
    type: str
    theorem_id: str
    prior_status: str
    hardened_status: str
    saf_definition_hash: str
    lemmas: list[dict[str, Any]]
    proof_obligation_matrix: list[dict[str, Any]]
    dependency_matrix: list[dict[str, Any]]
    polynomial_bound_summary: dict[str, Any]
    structural_validator_summary: dict[str, Any]
    scaling_evidence_summary: dict[str, Any]
    claim_boundary_audit: list[dict[str, Any]]
    reviewer_objection_updates: list[dict[str, Any]]
    nonclaims: list[str]
    checker_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(data) + "\n", encoding="utf-8", newline="\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _make_zip(root: str | Path, zip_path: str | Path) -> str:
    source = Path(root)
    target = Path(zip_path)
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source).as_posix())
    return sha256_file(target)


def _definition_hash() -> str:
    return hashlib.sha256(SAF_DEFINITION_TEXT.encode("utf-8")).hexdigest()


def _status_values(data: Any) -> list[str]:
    values: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in {"status", "checker_status", "validation_status", "hardened_status"} and isinstance(value, str):
                values.append(value)
            values.extend(_status_values(value))
    elif isinstance(data, list):
        for item in data:
            values.extend(_status_values(item))
    return values


def validate_saf_membership(
    formula: CNFFormula,
    *,
    c: int = 1,
    r: int = 2,
    separator_variables: list[int] | None = None,
) -> SAFMembershipValidation:
    """Validate structural membership in SAF(c,r) without claiming SAT/UNSAT."""

    invalid: list[str] = []
    if separator_variables is None:
        recognized = recognize_separator_affine_family(formula, c=c, r=r)
        separator = list(recognized.get("separator_variables", []))
        if recognized.get("status") != "SEPARATOR_AFFINE_FAMILY_RECOGNIZED":
            invalid.append("NO_SEPARATOR_AFFINE_STRUCTURE_RECOGNIZED")
    else:
        separator = [int(var) for var in separator_variables]
    if len(separator) > c:
        invalid.append("SEPARATOR_SIZE_OVER_BOUND")
    if any(var not in formula.variables for var in separator):
        invalid.append("SEPARATOR_VARIABLE_NOT_IN_FORMULA")

    components = _component_dicts(formula, separator) if separator and not any("SEPARATOR_VARIABLE" in item for item in invalid) else []
    assignments = _all_assignments(separator) if separator else []
    every_localized = True
    every_affine = True

    for assignment in assignments:
        _residual_formula, component_formulas, localization_errors = _condition_by_separator(formula, assignment, components)
        if localization_errors:
            every_localized = False
            invalid.extend(localization_errors)
        for component in components:
            cid = str(component["component_id"])
            component_formula = component_formulas[cid]
            affine_cert = _affine_component_certificate(f"tc063_validation_{cid}", component_formula, max_arity=r)
            affine_check = check_affine_residue_certificate(component_formula, affine_cert, max_arity=r)
            covered_clause_ids = _affine_source_clause_coverage(affine_cert)
            expected_clause_ids = set(range(1, len(component_formula.clauses) + 1))
            if affine_check["status"] != AFFINE_RESIDUE_CERTIFICATE_VERIFIED or covered_clause_ids != expected_clause_ids:
                every_affine = False
                invalid.append(f"COMPONENT_NOT_EXACT_AFFINE:{cid}")

    if not separator:
        every_localized = False
        every_affine = False
    status = SAF_MEMBER_VERIFIED if not invalid and every_localized and every_affine else SAF_MEMBER_REJECTED
    return SAFMembershipValidation(
        formula_hash=formula.formula_hash,
        separator_bound_c=c,
        affine_bound_r=r,
        separator_variables=separator,
        separator_size=len(separator),
        components=components,
        separator_assignment_count=2 ** len(separator) if separator else 0,
        every_assignment_localized=every_localized,
        every_component_affine_verified=every_affine,
        invalid_reason=";".join(dict.fromkeys(invalid)) if invalid else None,
        validation_status=status,
        polynomial_bound_record={
            "separator_enumeration": "O(n^c), polynomial only for fixed c.",
            "assignment_enumeration": "2^c separator assignments; exponential dependence on c is explicit.",
            "affine_dependency": "Residual affine checking depends on G5 soundness and supported affine bound r.",
            "finite_tests_are_support_only": True,
        },
        claim_boundary=(
            "SAF membership validation only; not SAT/UNSAT certification, not DRAT, "
            "not all SAT, not hierarchy completeness, and not P-vs-NP progress."
        ),
    )


def lemma_records() -> list[LemmaRecord]:
    return [
        LemmaRecord(
            "TC063-L1",
            "Separator Decomposition Lemma",
            "If S is a valid primal-graph variable separator and alpha assigns S, then every residual clause belongs to one component or is satisfied/removed.",
            ["Primal graph reconstructed from the original CNF.", "Separator variables are removed before component computation."],
            "A residual clause spanning two components would induce a primal edge after removing S; the checker rejects such clauses.",
            [
                "primal graph reconstructed correctly",
                "separator variables removed correctly",
                "clauses containing separator literals substituted correctly",
                "residual cross-component clauses rejected",
            ],
            ["separator_affine_family_theorem"],
            "FORMALIZED_PROOF_SKETCH",
        ),
        LemmaRecord(
            "TC063-L2",
            "Separator Assignment Exhaustiveness Lemma",
            "Every total assignment of F restricts to exactly one alpha in {0,1}^S, and every alpha is enumerated.",
            ["S is finite and explicitly encoded.", "Assignment enumeration is deterministic."],
            "The checker enumerates the Boolean product over sorted separator variables, producing exactly 2^|S| assignments.",
            ["all 2^|S| assignments enumerated", "no duplicate/omitted alpha", "assignment encoding deterministic"],
            ["separator_affine_family_theorem"],
            "FORMALIZED_PROOF_SKETCH",
        ),
        LemmaRecord(
            "TC063-L3",
            "Affine Component Soundness Lemma",
            "Every residual component accepted as exact affine is certified SAT or UNSAT by the G5 affine checker.",
            ["G5 affine checker soundness is assumed as a dependency.", "Exact source-clause coverage is checked."],
            "The validator and certificate checker call G5, require verified status, and require extracted affine clauses to cover the whole residual component.",
            [
                "G5 checker soundness assumed or externally formalized",
                "exact affine extraction verified",
                "polluted/incomplete affine components rejected",
                "SAT component witness checked",
                "UNSAT affine contradiction checked",
            ],
            ["operator_genesis", "separator_affine_family_theorem"],
            "PROOF_OBLIGATION_REMAINS",
        ),
        LemmaRecord(
            "TC063-L4",
            "SAT Lifting Lemma",
            "If one separator assignment makes every residual component SAT, then alpha plus component witnesses satisfies F when verified against the original CNF.",
            ["Component variable sets are disjoint outside S.", "No residual cross-component clause remains."],
            "The lifted assignment is constructed from alpha and component witnesses, then checked directly against the original CNF.",
            [
                "component variable sets disjoint outside S",
                "component witnesses agree with alpha",
                "no cross-component residual clause",
                "final original-CNF witness verification passes",
            ],
            ["separator_affine_family_theorem", "cnf"],
            "FORMALIZED_PROOF_SKETCH",
        ),
        LemmaRecord(
            "TC063-L5",
            "UNSAT Cover Lemma",
            "If every alpha in {0,1}^S has at least one verified affine-UNSAT residual component, then F is UNSAT.",
            ["Separator assignments are exhaustive.", "UNSAT component certificates are sound under G5."],
            "A satisfying assignment would restrict to some alpha, but that alpha is covered by an UNSAT component, contradiction.",
            [
                "all alpha covered",
                "for each alpha, at least one verified UNSAT component",
                "no uncovered separator assignment",
                "no diagnostic-only component used as proof",
            ],
            ["separator_affine_family_theorem", "operator_genesis"],
            "FORMALIZED_PROOF_SKETCH",
        ),
        LemmaRecord(
            "TC063-L6",
            "Polynomial Bound Lemma",
            "For fixed c and supported affine bound r, recognition, construction, certificate size, and checking are polynomial in |F|.",
            ["c is fixed.", "G5 affine checking is polynomial under supported r."],
            "Separator enumeration is O(n^c), assignment enumeration is 2^c, and residual component processing is polynomial for fixed c and supported r.",
            [
                "separator enumeration O(n^c)",
                "assignment enumeration 2^c",
                "total residual component processing polynomial",
                "affine solving/checking polynomial under G5 assumptions",
                "certificate size bound stated explicitly",
                "exponential dependence on c disclosed",
            ],
            ["separator_affine_family_theorem", "operator_genesis"],
            "PROOF_OBLIGATION_REMAINS",
        ),
        LemmaRecord(
            "TC063-L7",
            "Native Certificate Boundary Lemma",
            "A TC-063 native certificate is Witnora-checkable but is not DRAT/LRAT/FRAT unless exported and externally checked.",
            ["No external proof bridge is present in v2.23."],
            "Claim-boundary tests reject fake DRAT wording and document native-vs-external proof status.",
            ["no fake DRAT claim", "native-vs-external boundary stated", "external proof bridge listed as future work"],
            ["separator_affine_family_theorem"],
            "FORMALIZED_PROOF_SKETCH",
        ),
        LemmaRecord(
            "TC063-L8",
            "Restricted Scope Lemma",
            "TC-063 applies only to SAF(c,r), not all SAT, arbitrary separators, unbounded c, or affine-looking non-exact formulas.",
            ["SAF(c,r) validator rejects non-members.", "Claim scanner rejects broad claims."],
            "Controls reject non-SAF structures and forbidden claim/status payloads.",
            [
                "non-SAF inputs rejected or diagnostic-only",
                "fake completeness/P-vs-NP/all-SAT claims rejected",
                "HARD/UNKNOWN statuses rejected",
            ],
            ["tc063_theorem_hardening", "separator_affine_family_theorem"],
            "FORMALIZED_PROOF_SKETCH",
        ),
    ]


def proof_obligation_matrix(lemmas: Iterable[LemmaRecord] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lemma in lemmas or lemma_records():
        for index, obligation in enumerate(lemma.proof_obligations, start=1):
            rows.append(
                {
                    "theorem_id": THEOREM_ID,
                    "lemma_id": lemma.lemma_id,
                    "obligation_id": f"{lemma.lemma_id}-O{index}",
                    "obligation": obligation,
                    "current_status": "FORMAL_PROOF_SKETCH_ONLY"
                    if lemma.status == "FORMALIZED_PROOF_SKETCH"
                    else "PROOF_OBLIGATION_REMAINS",
                    "dependency": ", ".join(lemma.dependency_on_modules),
                    "missing_work": "External formalization or checker soundness proof remains required.",
                }
            )
    return rows


def dependency_matrix() -> list[dict[str, Any]]:
    return [
        {
            "dependency": "G5 affine checker soundness",
            "used_by": ["TC063-L3", "TC063-L5", "TC063-L6"],
            "status": "PROOF_OBLIGATION_REMAINS",
        },
        {
            "dependency": "formula serialization and formula hash exactness",
            "used_by": ["SAFMembershipValidation", "TC063 certificate checker"],
            "status": "FORMALIZED_PROOF_SKETCH",
        },
        {
            "dependency": "native certificate checker soundness",
            "used_by": ["TC063-L7"],
            "status": "PROOF_OBLIGATION_REMAINS",
        },
        {
            "dependency": "external DRAT/LRAT/FRAT bridge",
            "used_by": [],
            "status": "ABSENT_NOT_CLAIMED",
        },
    ]


def claim_boundary_audit() -> list[dict[str, Any]]:
    return [
        {
            "claim": "TC-063 status",
            "allowed": HARDENED_STATUS,
            "forbidden": "THEOREM_PROVEN_UNQUALIFIED",
            "reason": "Lemmas still depend on G5/checker soundness and external formalization obligations.",
        },
        {
            "claim": "scope",
            "allowed": "Restricted to SAF(c,r).",
            "forbidden": "All SAT, arbitrary separator formulas, or hierarchy completeness.",
            "reason": "Validator rejects non-SAF controls and the theorem statement is family-scoped.",
        },
        {
            "claim": "polynomiality",
            "allowed": "Polynomial only for fixed c and supported r.",
            "forbidden": "Polynomial-time SAT for arbitrary formulas.",
            "reason": "O(n^c) and 2^c dependence are explicit.",
        },
        {
            "claim": "certificate boundary",
            "allowed": "Native Witnora certificate.",
            "forbidden": "DRAT/LRAT/FRAT unless externally exported and checked.",
            "reason": "No external proof bridge is implemented in v2.23.",
        },
        {
            "claim": "scaling evidence",
            "allowed": "Implementation support only.",
            "forbidden": "Finite tests replace proof.",
            "reason": "n=64/n=128 tests exercise implementation behavior, not theorem proof.",
        },
    ]


def reviewer_objection_updates() -> list[dict[str, Any]]:
    return [
        {
            "objection": "TC-063 is still not a fully mechanized theorem.",
            "response": "Correct; v2.23 hardens lemmas and obligations and keeps the status as restricted with proof obligations.",
        },
        {
            "objection": "G5 affine checker soundness is assumed.",
            "response": "Correct; the dependency matrix makes G5 soundness explicit rather than hiding it.",
        },
        {
            "objection": "n=128 scaling does not prove the family theorem.",
            "response": "Correct; scaling evidence is implementation support only.",
        },
        {
            "objection": "Native certificates are not external proofs.",
            "response": "Correct; DRAT/LRAT/FRAT is not claimed without an external proof bridge.",
        },
    ]


def run_scaling_evidence() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for family in ["saf_sat_chain", "saf_unsat_cover", "saf_balanced_sat"]:
        for n in [64, 128]:
            instance_id = f"{family}_{n}"
            instance = make_separator_affine_instance(instance_id)
            cert = build_separator_affine_certificate(instance)
            check = check_separator_affine_certificate(instance.formula, cert)
            rows.append(
                {
                    "instance_id": instance_id,
                    "family": family,
                    "n": n,
                    "checker_status": check["checker_status"],
                    "final_result": check["final_result"],
                    "separator_assignment_count": check["separator_assignment_count"],
                    "claim_boundary": "Scaling evidence supports implementation only; it does not substitute for proof.",
                }
            )
    return {
        "rows": rows,
        "n_values": [64, 128],
        "families": ["saf_sat_chain", "saf_unsat_cover", "saf_balanced_sat"],
        "passed": sum(1 for row in rows if row["checker_status"] == "SEPARATOR_AFFINE_CERTIFICATE_VERIFIED"),
        "total": len(rows),
        "evidence_boundary": "Scaling tests support implementation only and do not prove TC-063.",
    }


def build_hardening_record() -> TC063TheoremHardeningRecord:
    lemmas = lemma_records()
    obligations = proof_obligation_matrix(lemmas)
    valid = validate_saf_membership(make_separator_affine_instance("saf_sat_chain_8").formula, c=1, r=2, separator_variables=[1])
    invalid = validate_saf_membership(make_separator_affine_instance("non_affine_component").formula, c=1, r=2, separator_variables=[1])
    scaling = run_scaling_evidence()
    record = TC063TheoremHardeningRecord(
        type="TC063_THEOREM_HARDENING_RECORD",
        theorem_id=THEOREM_ID,
        prior_status=PRIOR_STATUS,
        hardened_status=HARDENED_STATUS,
        saf_definition_hash=_definition_hash(),
        lemmas=[lemma.to_dict() for lemma in lemmas],
        proof_obligation_matrix=obligations,
        dependency_matrix=dependency_matrix(),
        polynomial_bound_summary={
            "separator_enumeration": "O(n^c)",
            "assignment_enumeration": "2^c",
            "fixed_c_polynomiality": True,
            "supported_affine_bound_r_required": True,
            "exponential_dependence_on_c_explicit": True,
            "g5_affine_soundness_dependency": True,
        },
        structural_validator_summary={
            "valid_fixture": valid.to_dict(),
            "invalid_fixture": invalid.to_dict(),
            "validator_status": "SAF_VALIDATOR_EXERCISED",
        },
        scaling_evidence_summary=scaling,
        claim_boundary_audit=claim_boundary_audit(),
        reviewer_objection_updates=reviewer_objection_updates(),
        nonclaims=[
            "Does not prove P vs NP.",
            "Does not prove all SAT.",
            "Does not prove hierarchy completeness.",
            "Does not prove polynomial-time SAT for arbitrary formulas.",
            "Does not claim DRAT/LRAT/FRAT unless externally checked.",
            "Does not upgrade TC-063 to THEOREM_PROVEN_UNQUALIFIED.",
        ],
        checker_status="NOT_RUN",
    )
    checked = check_tc063_hardening(record)
    return TC063TheoremHardeningRecord(**{**record.to_dict(), "checker_status": checked["checker_status"]})


def check_tc063_hardening(record: TC063TheoremHardeningRecord | dict[str, Any]) -> dict[str, Any]:
    data = record.to_dict() if isinstance(record, TC063TheoremHardeningRecord) else dict(record)
    errors: list[str] = []
    if data.get("type") != "TC063_THEOREM_HARDENING_RECORD":
        errors.append("BAD_RECORD_TYPE")
    if data.get("theorem_id") != THEOREM_ID:
        errors.append("BAD_THEOREM_ID")
    if data.get("prior_status") != PRIOR_STATUS:
        errors.append("BAD_PRIOR_STATUS")
    if data.get("hardened_status") not in ALLOWED_HARDENED_STATUSES:
        errors.append("BAD_HARDENED_STATUS")
    if data.get("hardened_status") == "THEOREM_PROVEN_UNQUALIFIED":
        errors.append("UNQUALIFIED_THEOREM_PROVEN_FORBIDDEN")
    if data.get("saf_definition_hash") != _definition_hash():
        errors.append("SAF_DEFINITION_HASH_MISMATCH")
    lemmas = data.get("lemmas", [])
    if len(lemmas) != 8:
        errors.append("LEMMA_COUNT_MISMATCH")
    if any(lemma.get("may_not_be_claimed_as_fully_proven") is not True for lemma in lemmas):
        errors.append("LEMMA_FULLY_PROVEN_FLAG_MISSING")
    if not data.get("proof_obligation_matrix"):
        errors.append("PROOF_OBLIGATION_MATRIX_EMPTY")
    dependency_text = stable_json(data.get("dependency_matrix", [])).lower()
    if "g5 affine checker soundness" not in dependency_text:
        errors.append("G5_DEPENDENCY_MISSING")
    poly = data.get("polynomial_bound_summary", {})
    if poly.get("fixed_c_polynomiality") is not True or poly.get("exponential_dependence_on_c_explicit") is not True:
        errors.append("POLYNOMIAL_BOUND_NOT_FIXED_C_SCOPED")
    validator = data.get("structural_validator_summary", {})
    if validator.get("valid_fixture", {}).get("validation_status") != SAF_MEMBER_VERIFIED:
        errors.append("VALID_FIXTURE_NOT_VERIFIED")
    if validator.get("invalid_fixture", {}).get("validation_status") != SAF_MEMBER_REJECTED:
        errors.append("INVALID_FIXTURE_NOT_REJECTED")
    scaling = data.get("scaling_evidence_summary", {})
    if scaling.get("passed") != scaling.get("total") or scaling.get("total", 0) < 6:
        errors.append("SCALING_EVIDENCE_INCOMPLETE")
    if "support implementation only" not in str(scaling.get("evidence_boundary", "")).lower():
        errors.append("SCALING_BOUNDARY_MISSING")
    joined = stable_json(data).lower()
    for fragment in FORBIDDEN_CLAIM_FRAGMENTS:
        if fragment in joined:
            errors.append("FORBIDDEN_CLAIM:" + fragment.upper().replace(" ", "_"))
    forbidden_statuses = sorted(set(_status_values(data)) & FORBIDDEN_STATUSES)
    if forbidden_statuses:
        errors.append("FORBIDDEN_STATUS:" + ",".join(forbidden_statuses))
    status = TC063_THEOREM_HARDENING_VERIFIED if not errors else TC063_THEOREM_HARDENING_FAILED
    return {
        "checker_status": status,
        "status": status,
        "errors": errors,
        "lemma_count": len(lemmas),
        "proof_obligation_count": len(data.get("proof_obligation_matrix", [])),
        "hardened_status": data.get("hardened_status"),
    }


def _lemma_markdown(lemma: LemmaRecord) -> str:
    lines = [
        f"# {lemma.lemma_name}",
        "",
        f"Status: `{lemma.status}`",
        "",
        "This lemma is part of TC-063 hardening. It is not an unqualified proven theorem.",
        "",
        "## Formal Statement",
        "",
        lemma.formal_statement,
        "",
        "## Assumptions",
        "",
    ]
    lines.extend(f"- {item}" for item in lemma.assumptions)
    lines.extend(["", "## Proof Sketch", "", lemma.proof_sketch, "", "## Proof Obligations", ""])
    lines.extend(f"- {item}" for item in lemma.proof_obligations)
    lines.extend(["", "## Dependencies", ""])
    lines.extend(f"- {item}" for item in lemma.dependency_on_modules)
    lines.append("")
    return "\n".join(lines)


def _report(record: dict[str, Any], check: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# TC-063 Theorem Hardening Report",
            "",
            "v2.23 hardens TC-063 without upgrading it to an unqualified proven theorem.",
            "",
            f"Hardened status: `{record['hardened_status']}`",
            f"Checker status: `{check['checker_status']}`",
            f"Lemmas: {len(record['lemmas'])}",
            f"Proof obligations: {len(record['proof_obligation_matrix'])}",
            "",
            "Scaling evidence is implementation support only. Native certificates are not external proofs.",
            "",
            "No P-vs-NP, all-SAT, hierarchy-completeness, polynomial-time arbitrary SAT, fake DRAT, or HARD/UNKNOWN claim is made.",
            "",
        ]
    )


def run_tc063_theorem_hardening(
    out_root: str | Path,
    *,
    strict: bool = False,
    zip_path: str | Path | None = "witnora-core-v2.23-harden-tc063-separator-affine-theorem.zip",
) -> dict[str, Any]:
    root = Path(out_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)

    record = build_hardening_record()
    data = record.to_dict()
    check = check_tc063_hardening(data)
    lemmas = lemma_records()

    _write_json(root / "tc063_theorem_hardening.json", data)
    _write_json(root / "tc063_lemma_summary.json", {"lemmas": data["lemmas"]})
    _write_json(root / "tc063_proof_obligation_matrix.json", {"rows": data["proof_obligation_matrix"]})
    _write_json(root / "saf_membership_validation_summary.json", data["structural_validator_summary"])
    _write_json(root / "tc063_polynomial_bound_summary.json", data["polynomial_bound_summary"])
    _write_json(root / "tc063_scaling_evidence_summary.json", data["scaling_evidence_summary"])
    _write_json(root / "tc063_dependency_matrix.json", {"dependencies": data["dependency_matrix"]})
    _write_json(root / "tc063_claim_boundary_audit.json", {"rows": data["claim_boundary_audit"]})
    _write_json(root / "tc063_reviewer_objection_updates.json", {"rows": data["reviewer_objection_updates"]})
    _write_text(root / "TC063_THEOREM_HARDENING_REPORT.md", _report(data, check))

    if strict and check["checker_status"] != TC063_THEOREM_HARDENING_VERIFIED:
        raise RuntimeError("TC-063 theorem hardening failed: " + ";".join(check["errors"]))
    digest = _make_zip(root, zip_path) if zip_path else ""
    return {
        "out_root": str(root),
        "zip": str(zip_path) if zip_path else "",
        "zip_sha256": digest,
        "record": data,
        "check": check,
        "lemmas": [lemma.to_dict() for lemma in lemmas],
    }


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _cmd_run(args: argparse.Namespace) -> int:
    result = run_tc063_theorem_hardening(args.out_root, strict=args.strict, zip_path=args.zip)
    print(
        stable_json(
            {
                "out_root": result["out_root"],
                "zip": result["zip"],
                "zip_sha256": result["zip_sha256"],
                "checker_status": result["check"]["checker_status"],
                "hardened_status": result["record"]["hardened_status"],
            }
        )
    )
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    result = check_tc063_hardening(_load_json(args.hardening))
    print(stable_json(result))
    return 0 if result["checker_status"] == TC063_THEOREM_HARDENING_VERIFIED else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m witnora_core.tc063_theorem_hardening")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("--out-root", default="outputs/v2.23-harden-tc063-separator-affine-theorem")
    run.add_argument("--strict", action="store_true")
    run.add_argument("--zip", default="witnora-core-v2.23-harden-tc063-separator-affine-theorem.zip")
    run.set_defaults(func=_cmd_run)
    check = sub.add_parser("check")
    check.add_argument("--hardening", required=True)
    check.set_defaults(func=_cmd_check)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
