"""Proof motif generalization checker prototype.

v2.18 promotes the v2.14 PROOF_MOTIF_NEAR_MISS recommendation into a
bounded native checker. The checker never treats similarity as proof: a
near-motif row is certified only when every generalized reuse expands into
valid concrete proof steps over clauses in the original CNF.

This is not DRAT, not a theorem, not a proof-motif completeness claim, and
not a P-vs-NP result.
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

from .cnf import CNFFormula, Clause, formula_from_json, resolvent
from .dimacs import load_dimacs
from .obstruction_dual import sha256_file, stable_json


VERSION = "2.18"

G11_GRAMMAR = "G11_PROOF_MOTIF_GENERALIZATION_CHECKER_PROTOTYPE"
SOURCE_RECOMMENDATION = "PROOF_MOTIF_NEAR_MISS"
PROMOTED_RECOMMENDATION = "PROOF_MOTIF_GENERALIZATION_CHECKER"

PROOF_MOTIF_NEAR_STRUCTURE_DETECTED = "PROOF_MOTIF_NEAR_STRUCTURE_DETECTED"
PROOF_MOTIF_GENERALIZED_TEMPLATE_CREATED = "PROOF_MOTIF_GENERALIZED_TEMPLATE_CREATED"
PROOF_MOTIF_GENERALIZATION_VERIFIED = "PROOF_MOTIF_GENERALIZATION_VERIFIED"
PROOF_MOTIF_GENERALIZATION_FAILED = "PROOF_MOTIF_GENERALIZATION_FAILED"
PROOF_MOTIF_GENERALIZATION_DIAGNOSTIC_ONLY = "PROOF_MOTIF_GENERALIZATION_DIAGNOSTIC_ONLY"
PROOF_MOTIF_GENERALIZED_REUSE_VERIFIED = "PROOF_MOTIF_GENERALIZED_REUSE_VERIFIED"
PROOF_MOTIF_GENERALIZED_NATIVE_CERTIFIED = "PROOF_MOTIF_GENERALIZED_NATIVE_CERTIFIED"
PROOF_MOTIF_GENERALIZED_UNSAT_CERTIFIED = "PROOF_MOTIF_GENERALIZED_UNSAT_CERTIFIED"
PROOF_MOTIF_GENERALIZED_NO_NEW_DELTA = "PROOF_MOTIF_GENERALIZED_NO_NEW_DELTA"
PROOF_MOTIF_GENERALIZED_DRAT_NOT_CLAIMED = "PROOF_MOTIF_GENERALIZED_DRAT_NOT_CLAIMED"
G11_PROOF_MOTIF_GENERALIZATION_NATIVE_CERTIFIED = "G11_PROOF_MOTIF_GENERALIZATION_NATIVE_CERTIFIED"

UNSAT_PROOF_MOTIF_GENERALIZATION_NATIVE_CERTIFIED = "UNSAT_PROOF_MOTIF_GENERALIZATION_NATIVE_CERTIFIED"

FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED = "FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED"

NEAR_MOTIF_SIMILARITY = "NEAR_MOTIF_SIMILARITY"
TEMPLATE_ABSTRACTION = "TEMPLATE_ABSTRACTION"
PARAMETRIC_GENERALIZATION = "PARAMETRIC_GENERALIZATION"

CONCRETE_INSTANTIATION_CHECKED = "CONCRETE_INSTANTIATION_CHECKED"
PARAMETRIC_TEMPLATE_CHECKED = "PARAMETRIC_TEMPLATE_CHECKED"
DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"

RESOLUTION_TEMPLATE = "RESOLUTION_TEMPLATE"
UNIT_PROPAGATION_TEMPLATE = "UNIT_PROPAGATION_TEMPLATE"
CONTRADICTION_TEMPLATE = "CONTRADICTION_TEMPLATE"

VARIANT_TWO_LITERAL = "TWO_LITERAL_CONFLICT"
VARIANT_SELECTOR = "SELECTOR_CONFLICT"
SUPPORTED_VARIANTS = {VARIANT_TWO_LITERAL, VARIANT_SELECTOR}

FORBIDDEN_STATUS_VALUES = {"HARD", "UNKNOWN"}
FORBIDDEN_CLAIM_FRAGMENTS = {
    "proves p vs np",
    "p vs np progress",
    "polynomial-time sat",
    "proof motif generalization solves all",
    "arbitrary proof-pattern learning",
    "strictness theorem",
    "drat verified",
    "completeness claim",
}


@dataclass(frozen=True)
class NearMotifSite:
    site_id: str
    variant: str
    variables: tuple[int, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProofMotifGeneralizationInstance:
    instance_id: str
    family: str
    motif_sites: tuple[NearMotifSite, ...]
    prior_g0_g10_result: str
    duplicate_of_g6: bool
    diagnostic_only: bool
    description: str
    formula_override: CNFFormula | None = None

    @property
    def formula(self) -> CNFFormula:
        if self.formula_override is not None:
            return self.formula_override
        clauses: list[tuple[int, ...]] = []
        for site in self.motif_sites:
            clauses.extend(_site_source_clauses(site))
        return CNFFormula.from_raw_clauses(clauses)

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "family": self.family,
            "formula_hash": self.formula.formula_hash,
            "motif_sites": [site.to_dict() for site in self.motif_sites],
            "prior_g0_g10_result": self.prior_g0_g10_result,
            "duplicate_of_g6": self.duplicate_of_g6,
            "diagnostic_only": self.diagnostic_only,
            "description": self.description,
        }


@dataclass(frozen=True)
class ProofMotifGeneralizationCertificate:
    type: str
    instance_id: str
    formula_hash: str
    detection_mode: str
    certification_mode: str
    base_motifs: list[dict[str, Any]]
    generalized_templates: list[dict[str, Any]]
    reuse_sites: list[dict[str, Any]]
    fallback_expansions: list[dict[str, Any]]
    compression_summary: dict[str, Any]
    final_macro_proof: dict[str, Any]
    checker_status: str
    status: str
    public_category: str
    certification_level: str
    drat_claim: str
    evidence_grade: str
    source_recommendation: str
    promoted_recommendation: str
    g11_delta_status: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(data), encoding="utf-8", newline="\n")


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


def _clause_from_literals(literals: Iterable[int]) -> Clause:
    clause = Clause.from_literals(literals)
    if clause is None:
        raise ValueError("tautological clause is not valid in a proof motif")
    return clause


def _canonical_clause(literals: Iterable[int]) -> list[int]:
    return list(_clause_from_literals(literals).literals)


def _empty_clause() -> Clause:
    return _clause_from_literals([])


def _site_source_clauses(site: NearMotifSite) -> list[tuple[int, ...]]:
    variables = tuple(site.variables)
    if site.variant == VARIANT_TWO_LITERAL:
        x, y = variables
        return [(x, y), (-x,), (-y,)]
    if site.variant == VARIANT_SELECTOR:
        x, y, selector = variables
        return [(x, y, selector), (-x,), (-y,), (-selector,)]
    raise ValueError(f"unsupported motif site variant: {site.variant}")


def _site_substitution(site: NearMotifSite) -> dict[str, int]:
    if site.variant == VARIANT_TWO_LITERAL:
        x, y = site.variables
        return {"x": x, "y": y}
    if site.variant == VARIANT_SELECTOR:
        x, y, selector = site.variables
        return {"x": x, "y": y, "selector": selector}
    raise ValueError(f"unsupported motif site variant: {site.variant}")


def _clause_id_lookup(formula: CNFFormula) -> dict[tuple[int, ...], int]:
    return {clause.literals: idx for idx, clause in enumerate(formula.clauses, start=1)}


def _clause_by_id(formula: CNFFormula) -> dict[int, tuple[int, ...]]:
    return {idx: clause.literals for idx, clause in enumerate(formula.clauses, start=1)}


def _proof_steps_for_variant(variant: str, variables: dict[str, int]) -> list[dict[str, Any]]:
    x = int(variables["x"])
    y = int(variables["y"])
    if variant == VARIANT_TWO_LITERAL:
        return [
            {"step_id": "r1", "kind": "RESOLUTION", "parents": ["c1", "c2"], "pivot": x, "result": [y]},
            {"step_id": "r2", "kind": "RESOLUTION", "parents": ["r1", "c3"], "pivot": y, "result": []},
        ]
    if variant == VARIANT_SELECTOR:
        selector = int(variables["selector"])
        return [
            {"step_id": "r1", "kind": "RESOLUTION", "parents": ["c1", "c2"], "pivot": x, "result": [y, selector]},
            {"step_id": "r2", "kind": "RESOLUTION", "parents": ["r1", "c3"], "pivot": y, "result": [selector]},
            {"step_id": "r3", "kind": "RESOLUTION", "parents": ["r2", "c4"], "pivot": selector, "result": []},
        ]
    raise ValueError(f"unsupported variant: {variant}")


def _source_labels_for_variant(variant: str) -> list[str]:
    if variant == VARIANT_TWO_LITERAL:
        return ["c1", "c2", "c3"]
    if variant == VARIANT_SELECTOR:
        return ["c1", "c2", "c3", "c4"]
    raise ValueError(f"unsupported variant: {variant}")


def _source_clause_payload(site: NearMotifSite) -> list[dict[str, Any]]:
    return [
        {"label": label, "clause": list(clause)}
        for label, clause in zip(_source_labels_for_variant(site.variant), _site_source_clauses(site))
    ]


def _steps_hash(steps: list[dict[str, Any]]) -> str:
    return hashlib.sha256(stable_json(steps).encode("utf-8")).hexdigest()


def _verify_resolution_expansion(source_clauses: dict[str, list[int]], steps: list[dict[str, Any]]) -> tuple[bool, list[str], list[int]]:
    errors: list[str] = []
    env: dict[str, Clause] = {}
    for label, clause in source_clauses.items():
        try:
            env[str(label)] = _clause_from_literals(clause)
        except ValueError as exc:
            errors.append(f"SOURCE_CLAUSE_INVALID:{label}:{exc}")
    last_result: Clause | None = None
    for step in steps:
        step_id = str(step.get("step_id", ""))
        if step.get("kind") != "RESOLUTION":
            errors.append(f"STEP_KIND_UNSUPPORTED:{step_id}")
            continue
        try:
            parent_a = env[str(step["parents"][0])]
            parent_b = env[str(step["parents"][1])]
            pivot = int(step["pivot"])
            derived = resolvent(parent_a, parent_b, pivot)
            if derived is None:
                errors.append(f"RESOLUTION_TAUTOLOGY:{step_id}")
                continue
            expected = _clause_from_literals(step.get("result", []))
            if derived != expected:
                errors.append(f"STEP_RESULT_MISMATCH:{step_id}")
            env[step_id] = derived
            last_result = derived
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"STEP_INVALID:{step_id}:{exc}")
    if last_result != _empty_clause():
        errors.append("EXPANSION_DOES_NOT_DERIVE_EMPTY")
    return not errors, errors, list(last_result.literals) if last_result is not None else []


def make_proof_motif_generalization_instance(instance_id: str) -> ProofMotifGeneralizationInstance:
    def sites(count: int, *, start: int = 1, selector_every: int = 2) -> tuple[NearMotifSite, ...]:
        result: list[NearMotifSite] = []
        next_var = start
        for idx in range(1, count + 1):
            if idx % selector_every == 0:
                result.append(NearMotifSite(f"site_{idx}", VARIANT_SELECTOR, (next_var, next_var + 1, next_var + 2)))
                next_var += 3
            else:
                result.append(NearMotifSite(f"site_{idx}", VARIANT_TWO_LITERAL, (next_var, next_var + 1)))
                next_var += 2
        return tuple(result)

    specs: dict[str, dict[str, Any]] = {
        "ladder_near_4": {"sites": sites(4), "family": "ladder-near", "description": "Four near motifs alternating binary and selector conflicts."},
        "ladder_near_8": {"sites": sites(8), "family": "ladder-near", "description": "Eight near motifs with checked generalized reuse."},
        "chain_near_6": {"sites": sites(6, selector_every=3), "family": "chain-near", "description": "Six chain-like near motifs with local variants."},
        "gadget_variants": {"sites": sites(5), "family": "gadget-variants", "description": "Controlled gadget variants requiring generalized template checking."},
        "proof_motif_near_miss": {"sites": sites(5, selector_every=2), "family": "obstruction-dual-near-miss", "description": "v2.14 proof-motif near-miss recommendation row."},
        "exact_motif_duplicate_control": {
            "sites": tuple(NearMotifSite(f"site_{idx}", VARIANT_TWO_LITERAL, (2 * idx - 1, 2 * idx)) for idx in range(1, 5)),
            "family": "duplicate-g6-control",
            "duplicate_of_g6": True,
            "description": "Exact repeated motif already handled by G6; not a novel G11 delta.",
        },
        "bad_generalization_control": {"sites": sites(3), "family": "negative-control", "description": "Used by tests to tamper generalized template data."},
        "bad_substitution_reject": {"sites": sites(3), "family": "negative-control", "description": "Used by tests to tamper substitution maps."},
        "tamper_reject": {"sites": sites(3), "family": "negative-control", "description": "Used by tests to tamper certificate hash."},
        "fake_drat_reject": {"sites": sites(3), "family": "negative-control", "description": "Used by tests to inject a false DRAT claim."},
        "loose_similarity_reject": {
            "sites": tuple(),
            "family": "loose-similarity-control",
            "diagnostic_only": True,
            "formula_override": CNFFormula.from_raw_clauses([[1, 2], [-1, 3], [-3], [4, 5], [-4]]),
            "description": "Syntactically similar clauses without a valid instantiated proof expansion.",
        },
    }
    if instance_id not in specs:
        raise ValueError(f"unsupported proof-motif generalization instance id: {instance_id}")
    spec = specs[instance_id]
    duplicate = bool(spec.get("duplicate_of_g6", False))
    diagnostic = bool(spec.get("diagnostic_only", False))
    prior = "DUPLICATE_OF_G6_PROOF_MOTIF_PATTERN" if duplicate else "G0_G10_NO_CERTIFIED_NEAR_MOTIF_COLLAPSE"
    if diagnostic:
        prior = "LOWER_REPLAY_NO_COLLAPSE_WITH_LOOSE_SIMILARITY"
    return ProofMotifGeneralizationInstance(
        instance_id=instance_id,
        family=str(spec["family"]),
        motif_sites=tuple(spec.get("sites", tuple())),
        prior_g0_g10_result=prior,
        duplicate_of_g6=duplicate,
        diagnostic_only=diagnostic,
        description=str(spec["description"]),
        formula_override=spec.get("formula_override"),
    )


def _base_motif_for_site(site: NearMotifSite, formula: CNFFormula) -> dict[str, Any]:
    clause_lookup = _clause_id_lookup(formula)
    source_payload = _source_clause_payload(site)
    source_ids = [clause_lookup[tuple(item["clause"])] for item in source_payload]
    variables = _site_substitution(site)
    steps = _proof_steps_for_variant(site.variant, variables)
    source_map = {str(item["label"]): list(item["clause"]) for item in source_payload}
    verified, errors, derived = _verify_resolution_expansion(source_map, steps)
    return {
        "motif_id": site.site_id,
        "motif_type": RESOLUTION_TEMPLATE,
        "variant": site.variant,
        "source_clause_ids": source_ids,
        "steps": steps,
        "derived_lemma": derived,
        "verified": verified,
        "errors": errors,
    }


def detect_near_motifs(instance: ProofMotifGeneralizationInstance) -> dict[str, Any]:
    if instance.diagnostic_only or not instance.motif_sites:
        return {
            "status": PROOF_MOTIF_GENERALIZATION_DIAGNOSTIC_ONLY,
            "detection_mode": NEAR_MOTIF_SIMILARITY,
            "message": "Near motif similarity was detected, but no valid generalized proof template is certified.",
            "base_motifs": [],
            "generalized_templates": [],
            "reuse_sites": [],
            "similarity_is_proof": False,
        }
    base_motifs = [_base_motif_for_site(site, instance.formula) for site in instance.motif_sites]
    variants = sorted({site.variant for site in instance.motif_sites})
    generalized_template = {
        "generalized_template_id": "near_resolution_conflict_generalization",
        "covered_motif_ids": [site.site_id for site in instance.motif_sites],
        "parameters": ["x", "y", "selector_optional", "variant"],
        "parameter_constraints": {
            "allowed_variants": variants,
            "variables_distinct": True,
            "selector_required_for": [VARIANT_SELECTOR],
            "source_clauses_must_exist": True,
            "instantiated_resolution_steps_must_verify": True,
        },
        "generalized_steps": [
            {"schema_step": "resolve wide positive clause with negative x"},
            {"schema_step": "resolve remaining derived clause with negative y"},
            {"schema_step": "if selector variant, resolve selector unit"},
        ],
        "generalized_derived_lemma_schema": [],
        "template_checker_status": "PENDING_CHECK",
    }
    reuse_sites = []
    clause_lookup = _clause_id_lookup(instance.formula)
    for site in instance.motif_sites:
        variables = _site_substitution(site)
        steps = _proof_steps_for_variant(site.variant, variables)
        source_clause_ids = [clause_lookup[tuple(clause)] for clause in _site_source_clauses(site)]
        reuse_sites.append(
            {
                "reuse_id": f"reuse_{site.site_id}",
                "generalized_template_id": generalized_template["generalized_template_id"],
                "concrete_source_clause_ids": source_clause_ids,
                "substitution_map": {key: value for key, value in variables.items()},
                "parameter_assignment": {"variant": site.variant, "site_id": site.site_id},
                "instantiated_steps_hash": _steps_hash(steps),
                "instantiated_derived_lemma": [],
                "reuse_checker_status": "PENDING_CHECK",
            }
        )
    return {
        "status": PROOF_MOTIF_NEAR_STRUCTURE_DETECTED,
        "detection_mode": PARAMETRIC_GENERALIZATION if len(variants) > 1 else TEMPLATE_ABSTRACTION,
        "message": "Near motifs detected; generalized template must be checked by expanding every reuse.",
        "base_motifs": base_motifs,
        "generalized_templates": [generalized_template],
        "reuse_sites": reuse_sites,
        "similarity_is_proof": False,
    }


def build_proof_motif_generalization_certificate(
    instance: ProofMotifGeneralizationInstance,
) -> ProofMotifGeneralizationCertificate:
    detection = detect_near_motifs(instance)
    base_motifs = list(detection["base_motifs"])
    templates = list(detection["generalized_templates"])
    reuse_sites = list(detection["reuse_sites"])
    fallback_expansions: list[dict[str, Any]] = []
    for site, reuse in zip(instance.motif_sites, reuse_sites):
        variables = _site_substitution(site)
        fallback_expansions.append(
            {
                "reuse_id": reuse["reuse_id"],
                "variant": site.variant,
                "source_clauses": _source_clause_payload(site),
                "instantiated_steps": _proof_steps_for_variant(site.variant, variables),
                "derived_lemma": [],
            }
        )
    concrete_steps = sum(len(expansion["instantiated_steps"]) for expansion in fallback_expansions)
    template_steps = len(templates[0]["generalized_steps"]) if templates else 0
    checked_instantiations = len(reuse_sites)
    compressed_steps = template_steps + checked_instantiations if reuse_sites else 0
    compression_ratio = round(concrete_steps / compressed_steps, 4) if compressed_steps else 0.0
    compression_summary = {
        "concrete_expanded_steps": concrete_steps,
        "generalized_template_steps": template_steps,
        "checked_instantiations": checked_instantiations,
        "compression_ratio": compression_ratio,
    }
    final_macro_proof = {
        "macro_steps": [
            {"macro_step_id": f"macro_{idx + 1}", "reuse_id": reuse["reuse_id"], "lemma": reuse["instantiated_derived_lemma"]}
            for idx, reuse in enumerate(reuse_sites)
        ],
        "final_contradiction": bool(reuse_sites),
        "verified": False,
    }
    certification_mode = PARAMETRIC_TEMPLATE_CHECKED if reuse_sites and detection["detection_mode"] == PARAMETRIC_GENERALIZATION else CONCRETE_INSTANTIATION_CHECKED
    if detection["status"] == PROOF_MOTIF_GENERALIZATION_DIAGNOSTIC_ONLY:
        certification_mode = DIAGNOSTIC_ONLY
    status = PROOF_MOTIF_GENERALIZATION_DIAGNOSTIC_ONLY if certification_mode == DIAGNOSTIC_ONLY else PROOF_MOTIF_GENERALIZED_UNSAT_CERTIFIED
    public_category = "NO_COLLAPSE_FOUND" if certification_mode == DIAGNOSTIC_ONLY else UNSAT_PROOF_MOTIF_GENERALIZATION_NATIVE_CERTIFIED
    certification_level = "NOT_CERTIFIED" if certification_mode == DIAGNOSTIC_ONLY else PROOF_MOTIF_GENERALIZED_NATIVE_CERTIFIED
    g11_delta_status = PROOF_MOTIF_GENERALIZED_NO_NEW_DELTA if instance.duplicate_of_g6 else "PENDING_CHECK"
    if certification_mode == DIAGNOSTIC_ONLY:
        g11_delta_status = PROOF_MOTIF_GENERALIZATION_DIAGNOSTIC_ONLY
    cert = ProofMotifGeneralizationCertificate(
        type="PROOF_MOTIF_GENERALIZATION_CERTIFICATE",
        instance_id=instance.instance_id,
        formula_hash=instance.formula.formula_hash,
        detection_mode=str(detection["detection_mode"]),
        certification_mode=certification_mode,
        base_motifs=base_motifs,
        generalized_templates=templates,
        reuse_sites=reuse_sites,
        fallback_expansions=fallback_expansions,
        compression_summary=compression_summary,
        final_macro_proof=final_macro_proof,
        checker_status="NOT_RUN",
        status=status,
        public_category=public_category,
        certification_level=certification_level,
        drat_claim=PROOF_MOTIF_GENERALIZED_DRAT_NOT_CLAIMED,
        evidence_grade=FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
        source_recommendation=SOURCE_RECOMMENDATION,
        promoted_recommendation=PROMOTED_RECOMMENDATION,
        g11_delta_status=g11_delta_status,
        claim_boundary="native proof-motif generalization certificate only; no DRAT proof claimed",
    )
    data = cert.to_dict()
    if instance.instance_id == "bad_generalization_control" and data["generalized_templates"]:
        data["generalized_templates"][0]["parameter_constraints"]["instantiated_resolution_steps_must_verify"] = False
    if instance.instance_id == "bad_substitution_reject" and data["reuse_sites"]:
        data["reuse_sites"][0]["substitution_map"]["y"] = data["reuse_sites"][0]["substitution_map"]["x"]
    if instance.instance_id == "tamper_reject":
        data["formula_hash"] = "0" * 64
    if instance.instance_id == "fake_drat_reject":
        data["drat_claim"] = "DRAT_VERIFIED"
    check = check_proof_motif_generalization_certificate(instance.formula, data)
    data["checker_status"] = check["status"]
    if check["status"] == PROOF_MOTIF_GENERALIZATION_VERIFIED:
        data["status"] = PROOF_MOTIF_GENERALIZED_UNSAT_CERTIFIED
        data["certification_level"] = PROOF_MOTIF_GENERALIZED_NATIVE_CERTIFIED
        data["public_category"] = UNSAT_PROOF_MOTIF_GENERALIZATION_NATIVE_CERTIFIED
        data["generalized_templates"] = [{**template, "template_checker_status": PROOF_MOTIF_GENERALIZATION_VERIFIED} for template in data["generalized_templates"]]
        data["reuse_sites"] = [{**reuse, "reuse_checker_status": PROOF_MOTIF_GENERALIZED_REUSE_VERIFIED} for reuse in data["reuse_sites"]]
        data["final_macro_proof"] = {**data["final_macro_proof"], "verified": True}
        data["g11_delta_status"] = PROOF_MOTIF_GENERALIZED_NO_NEW_DELTA if instance.duplicate_of_g6 else G11_PROOF_MOTIF_GENERALIZATION_NATIVE_CERTIFIED
    elif check["status"] == PROOF_MOTIF_GENERALIZATION_DIAGNOSTIC_ONLY:
        data["status"] = PROOF_MOTIF_GENERALIZATION_DIAGNOSTIC_ONLY
        data["public_category"] = "NO_COLLAPSE_FOUND"
        data["certification_level"] = "NOT_CERTIFIED"
        data["g11_delta_status"] = PROOF_MOTIF_GENERALIZATION_DIAGNOSTIC_ONLY
    else:
        data["status"] = PROOF_MOTIF_GENERALIZATION_FAILED
        data["public_category"] = "NO_COLLAPSE_FOUND"
        data["certification_level"] = "NOT_CERTIFIED"
        data["g11_delta_status"] = PROOF_MOTIF_GENERALIZATION_FAILED
    return ProofMotifGeneralizationCertificate(**data)


def _template_constraints_ok(template: dict[str, Any], assignment: dict[str, Any], substitution: dict[str, int]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    constraints = template.get("parameter_constraints", {})
    variant = str(assignment.get("variant", ""))
    allowed = set(constraints.get("allowed_variants", []))
    if variant not in SUPPORTED_VARIANTS:
        errors.append("PARAMETER_VARIANT_UNSUPPORTED")
    if allowed and variant not in allowed:
        errors.append("PARAMETER_VARIANT_NOT_ALLOWED")
    expected_keys = {"x", "y", "selector"} if variant == VARIANT_SELECTOR else {"x", "y"}
    if set(substitution) != expected_keys:
        errors.append("SUBSTITUTION_KEY_SET_INVALID")
    if constraints.get("variables_distinct", False) and len(set(substitution.values())) != len(substitution.values()):
        errors.append("SUBSTITUTION_VARIABLES_NOT_DISTINCT")
    if variant == VARIANT_SELECTOR and "selector" not in substitution:
        errors.append("SELECTOR_REQUIRED")
    return not errors, errors


def check_proof_motif_generalization_certificate(
    formula: CNFFormula,
    certificate: ProofMotifGeneralizationCertificate | dict[str, Any],
) -> dict[str, Any]:
    data = certificate.to_dict() if isinstance(certificate, ProofMotifGeneralizationCertificate) else dict(certificate)
    errors: list[str] = []
    warnings: list[str] = []
    if data.get("type") != "PROOF_MOTIF_GENERALIZATION_CERTIFICATE":
        errors.append("CERTIFICATE_TYPE_MISMATCH")
    if str(data.get("formula_hash", "")).lower() != formula.formula_hash.lower():
        errors.append("FORMULA_HASH_MISMATCH")
    if data.get("drat_claim") != PROOF_MOTIF_GENERALIZED_DRAT_NOT_CLAIMED:
        errors.append("FAKE_DRAT_CLAIM")
    if "DRAT" in str(data.get("public_category", "")):
        errors.append("PUBLIC_CATEGORY_FAKE_DRAT")
    payload_text = stable_json(data).lower()
    for fragment in FORBIDDEN_CLAIM_FRAGMENTS:
        if fragment in payload_text:
            errors.append(f"FORBIDDEN_CLAIM_FRAGMENT:{fragment}")
    for value in data.values():
        if isinstance(value, str) and value in FORBIDDEN_STATUS_VALUES:
            errors.append(f"FORBIDDEN_STATUS:{value}")
    if data.get("certification_mode") == DIAGNOSTIC_ONLY:
        if data.get("public_category") != "NO_COLLAPSE_FOUND":
            errors.append("DIAGNOSTIC_ONLY_CERTIFIES_RESULT")
        return {
            "status": PROOF_MOTIF_GENERALIZATION_DIAGNOSTIC_ONLY if not errors else PROOF_MOTIF_GENERALIZATION_FAILED,
            "checker_status": PROOF_MOTIF_GENERALIZATION_DIAGNOSTIC_ONLY if not errors else PROOF_MOTIF_GENERALIZATION_FAILED,
            "errors": errors,
            "warnings": warnings,
            "verified_reuse_count": 0,
            "final_contradiction_verified": False,
            "claim_boundary": "Diagnostic-only near motifs cannot certify SAT/UNSAT.",
        }
    templates = {str(template.get("generalized_template_id")): template for template in data.get("generalized_templates", [])}
    if not templates:
        errors.append("NO_GENERALIZED_TEMPLATE")
    for template_id, template in templates.items():
        constraints = template.get("parameter_constraints", {})
        if not constraints.get("instantiated_resolution_steps_must_verify", False):
            errors.append(f"TEMPLATE_DOES_NOT_REQUIRE_EXPANSION_CHECK:{template_id}")
        if not template.get("generalized_steps"):
            errors.append(f"TEMPLATE_HAS_NO_STEPS:{template_id}")
    clause_by_id = _clause_by_id(formula)
    base_motif_ids: set[str] = set()
    for motif in data.get("base_motifs", []):
        motif_id = str(motif.get("motif_id", ""))
        base_motif_ids.add(motif_id)
        source_ids = [int(clause_id) for clause_id in motif.get("source_clause_ids", [])]
        source_labels = _source_labels_for_variant(str(motif.get("variant", "")))
        source_map = {label: list(clause_by_id.get(clause_id, tuple())) for label, clause_id in zip(source_labels, source_ids)}
        ok, motif_errors, derived = _verify_resolution_expansion(source_map, list(motif.get("steps", [])))
        if not ok:
            errors.extend([f"BASE_MOTIF_INVALID:{motif_id}:{error}" for error in motif_errors])
        if _canonical_clause(motif.get("derived_lemma", [])) != derived:
            errors.append(f"BASE_MOTIF_DERIVED_LEMMA_MISMATCH:{motif_id}")
    verified_reuses: dict[str, list[int]] = {}
    for reuse in data.get("reuse_sites", []):
        reuse_id = str(reuse.get("reuse_id", ""))
        template = templates.get(str(reuse.get("generalized_template_id", "")))
        if template is None:
            errors.append(f"REUSE_TEMPLATE_MISSING:{reuse_id}")
            continue
        try:
            substitution = {str(key): int(value) for key, value in reuse.get("substitution_map", {}).items()}
            assignment = dict(reuse.get("parameter_assignment", {}))
            constraints_ok, constraint_errors = _template_constraints_ok(template, assignment, substitution)
            if not constraints_ok:
                errors.extend([f"REUSE_PARAMETER_INVALID:{reuse_id}:{error}" for error in constraint_errors])
            variant = str(assignment.get("variant", ""))
            source_ids = [int(clause_id) for clause_id in reuse.get("concrete_source_clause_ids", [])]
            expected_source_count = 4 if variant == VARIANT_SELECTOR else 3
            if len(source_ids) != expected_source_count:
                errors.append(f"REUSE_SOURCE_COUNT_INVALID:{reuse_id}")
            pseudo_site = NearMotifSite(str(assignment.get("site_id", reuse_id)), variant, tuple(substitution[key] for key in (["x", "y", "selector"] if variant == VARIANT_SELECTOR else ["x", "y"])))
            expected_clauses = _site_source_clauses(pseudo_site)
            for expected, clause_id in zip(expected_clauses, source_ids):
                if clause_by_id.get(clause_id) != expected:
                    errors.append(f"REUSE_SOURCE_CLAUSE_MISMATCH:{reuse_id}:{clause_id}")
            steps = _proof_steps_for_variant(variant, substitution)
            if reuse.get("instantiated_steps_hash") != _steps_hash(steps):
                errors.append(f"REUSE_STEPS_HASH_MISMATCH:{reuse_id}")
            source_map = {label: list(clause_by_id.get(clause_id, tuple())) for label, clause_id in zip(_source_labels_for_variant(variant), source_ids)}
            ok, proof_errors, derived = _verify_resolution_expansion(source_map, steps)
            if not ok:
                errors.extend([f"REUSE_EXPANSION_INVALID:{reuse_id}:{error}" for error in proof_errors])
            if _canonical_clause(reuse.get("instantiated_derived_lemma", [])) != derived:
                errors.append(f"REUSE_DERIVED_LEMMA_MISMATCH:{reuse_id}")
            if not errors or reuse_id not in verified_reuses:
                verified_reuses[reuse_id] = derived
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"REUSE_INVALID:{reuse_id}:{exc}")
    for expansion in data.get("fallback_expansions", []):
        reuse_id = str(expansion.get("reuse_id", ""))
        source_map = {str(item.get("label")): list(item.get("clause", [])) for item in expansion.get("source_clauses", [])}
        ok, proof_errors, derived = _verify_resolution_expansion(source_map, list(expansion.get("instantiated_steps", [])))
        if not ok:
            errors.extend([f"FALLBACK_EXPANSION_INVALID:{reuse_id}:{error}" for error in proof_errors])
        if _canonical_clause(expansion.get("derived_lemma", [])) != derived:
            errors.append(f"FALLBACK_DERIVED_LEMMA_MISMATCH:{reuse_id}")
    final = data.get("final_macro_proof", {})
    macro_steps = list(final.get("macro_steps", []))
    final_empty = False
    for step in macro_steps:
        reuse_id = str(step.get("reuse_id", ""))
        lemma = _canonical_clause(step.get("lemma", []))
        if reuse_id not in verified_reuses:
            errors.append(f"MACRO_REUSE_NOT_VERIFIED:{reuse_id}")
        elif verified_reuses[reuse_id] != lemma:
            errors.append(f"MACRO_LEMMA_MISMATCH:{reuse_id}")
        elif lemma == []:
            final_empty = True
    if data.get("public_category") == UNSAT_PROOF_MOTIF_GENERALIZATION_NATIVE_CERTIFIED:
        if final.get("final_contradiction") is not True or not final_empty:
            errors.append("FINAL_CONTRADICTION_NOT_VERIFIED")
    compression = data.get("compression_summary", {})
    concrete = int(compression.get("concrete_expanded_steps", 0))
    template_steps = int(compression.get("generalized_template_steps", 0))
    checked = int(compression.get("checked_instantiations", 0))
    if checked != len(data.get("reuse_sites", [])):
        errors.append("CHECKED_INSTANTIATION_COUNT_MISMATCH")
    expected_ratio = round(concrete / (template_steps + checked), 4) if template_steps + checked else 0.0
    if float(compression.get("compression_ratio", 0.0)) != expected_ratio:
        errors.append("COMPRESSION_RATIO_MISMATCH")
    if len(data.get("reuse_sites", [])) >= 4 and expected_ratio <= 1.0:
        errors.append("COMPRESSION_RATIO_NOT_MEANINGFUL")
    if data.get("certification_mode") == PARAMETRIC_TEMPLATE_CHECKED:
        variants = {str(reuse.get("parameter_assignment", {}).get("variant", "")) for reuse in data.get("reuse_sites", [])}
        if len(variants) < 2:
            errors.append("PARAMETRIC_TEMPLATE_DID_NOT_COVER_NEAR_VARIANTS")
    status = PROOF_MOTIF_GENERALIZATION_VERIFIED if not errors and verified_reuses and final_empty else PROOF_MOTIF_GENERALIZATION_FAILED
    return {
        "status": status,
        "checker_status": status,
        "errors": errors,
        "warnings": warnings,
        "verified_template_count": len(templates),
        "verified_reuse_count": len(verified_reuses) if not errors else 0,
        "final_contradiction_verified": final_empty and not errors,
        "claim_boundary": "Native proof-motif generalization only; every reuse expands into checked concrete proof steps and no DRAT proof is claimed.",
    }


def proof_motif_generalization_report(rows: list[dict[str, Any]], delta: dict[str, Any]) -> str:
    lines = [
        "# Proof Motif Generalization Report",
        "",
        "## Executive Summary",
        "",
        "v2.18 promotes the v2.14 PROOF_MOTIF_NEAR_MISS recommendation into G11_PROOF_MOTIF_GENERALIZATION_CHECKER_PROTOTYPE. Near motif similarity is not proof: rows are certified only when the generalized template and every reuse instantiation expand into checked native proof steps over the original CNF.",
        "",
        "## Target Rows",
        "",
        "| instance | prior G0-G10 result | mode | checker | reuse sites | compression | delta |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['instance_id']}` | `{row['prior_g0_g10_result']}` | `{row['certification_mode']}` | `{row['checker_status']}` | {row['reuse_count']} | {row['compression_ratio']} | `{row['g11_delta_status']}` |"
        )
    lines.extend(
        [
            "",
            "## Soundness Boundary",
            "",
            "Similarity is diagnostic until the checker verifies concrete expansions. Diagnostic-only motifs cannot certify SAT or UNSAT. Exact G6 motif duplicates are retained as controls and excluded from novel G11 deltas.",
            "",
            "## Operator Delta Summary",
            "",
            stable_json(delta),
            "## Forbidden Claims",
            "",
            "- no P vs NP progress claim",
            "- no polynomial-time SAT claim",
            "- no proof motif generalization completeness claim",
            "- no arbitrary proof-pattern learning claim",
            "- no DRAT verification claim",
            "- no theorem or strictness theorem claim",
            "- no HARD or UNKNOWN statuses",
            "",
        ]
    )
    return "\n".join(lines)


def run_proof_motif_generalization_lab(
    *,
    instances: Iterable[str],
    out_root: str | Path,
    strict: bool = False,
    zip_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(out_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    cert_root = root / "certificates"
    cnf_root = root / "original_cnf"
    cert_root.mkdir(parents=True, exist_ok=True)
    cnf_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    certificates: list[dict[str, Any]] = []
    detection_traces: list[dict[str, Any]] = []
    template_summaries: list[dict[str, Any]] = []
    reuse_summaries: list[dict[str, Any]] = []
    compression_summaries: list[dict[str, Any]] = []
    for instance_id in instances:
        instance = make_proof_motif_generalization_instance(instance_id)
        detection = detect_near_motifs(instance)
        certificate = build_proof_motif_generalization_certificate(instance)
        check = check_proof_motif_generalization_certificate(instance.formula, certificate)
        cert_path = cert_root / f"{instance_id}_proof_motif_generalization_certificate.json"
        cnf_path = cnf_root / f"{instance_id}.cnf"
        _write_json(cert_path, certificate.to_dict())
        _write_text(cnf_path, instance.formula.canonical_dimacs())
        novel_delta = (
            check["status"] == PROOF_MOTIF_GENERALIZATION_VERIFIED
            and not instance.duplicate_of_g6
            and certificate.public_category == UNSAT_PROOF_MOTIF_GENERALIZATION_NATIVE_CERTIFIED
            and certificate.certification_mode != DIAGNOSTIC_ONLY
        )
        row = {
            "instance_id": instance_id,
            "family": instance.family,
            "prior_g0_g10_result": instance.prior_g0_g10_result,
            "g11_grammar": G11_GRAMMAR,
            "status": certificate.status,
            "public_category": certificate.public_category,
            "certification_mode": certificate.certification_mode,
            "certification_level": certificate.certification_level,
            "checker_status": check["status"],
            "detection_mode": certificate.detection_mode,
            "reuse_count": len(certificate.reuse_sites),
            "compression_ratio": certificate.compression_summary.get("compression_ratio", 0.0),
            "g11_delta_status": certificate.g11_delta_status,
            "novel_g11_delta": novel_delta,
            "duplicate_of_g6": instance.duplicate_of_g6,
            "diagnostic_only": certificate.certification_mode == DIAGNOSTIC_ONLY,
            "drat_claim": certificate.drat_claim,
            "certificate_path": str(cert_path),
            "cnf_path": str(cnf_path),
        }
        rows.append(row)
        certificates.append(certificate.to_dict())
        detection_traces.append({"instance_id": instance_id, "detection": detection, "instance": instance.to_dict()})
        template_summaries.append({"instance_id": instance_id, "templates": certificate.generalized_templates})
        reuse_summaries.append({"instance_id": instance_id, "reuse_sites": certificate.reuse_sites, "checker": check})
        compression_summaries.append({"instance_id": instance_id, "compression_summary": certificate.compression_summary, "final_macro_proof": certificate.final_macro_proof})

    delta = {
        "operator_added": G11_GRAMMAR,
        "source_recommendation": SOURCE_RECOMMENDATION,
        "promoted_recommendation": PROMOTED_RECOMMENDATION,
        "instances_total": len(rows),
        "native_certified": sum(1 for row in rows if row["checker_status"] == PROOF_MOTIF_GENERALIZATION_VERIFIED),
        "novel_g11_delta_count": sum(1 for row in rows if row["novel_g11_delta"]),
        "duplicate_exact_motif_controls": sum(1 for row in rows if row["duplicate_of_g6"]),
        "diagnostic_only_rows": sum(1 for row in rows if row["diagnostic_only"]),
        "max_compression_ratio": max((float(row["compression_ratio"]) for row in rows), default=0.0),
        "evidence_grade": FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
        "fake_drat_claims": sum(
            1
            for row in rows
            if row["drat_claim"] != PROOF_MOTIF_GENERALIZED_DRAT_NOT_CLAIMED
            and row["checker_status"] == PROOF_MOTIF_GENERALIZATION_VERIFIED
        ),
        "fake_drat_rejected_controls": sum(
            1
            for row in rows
            if row["drat_claim"] != PROOF_MOTIF_GENERALIZED_DRAT_NOT_CLAIMED
            and row["checker_status"] == PROOF_MOTIF_GENERALIZATION_FAILED
        ),
        "claim_boundary": "Finite empirical G11 edge-delta evidence only; no theorem, lower-bound, DRAT, completeness, or P-vs-NP claim.",
        "strict": strict,
    }
    checker_summary = [
        {
            "instance_id": row["instance_id"],
            "checker_status": row["checker_status"],
            "certification_mode": row["certification_mode"],
            "reuse_count": row["reuse_count"],
            "final_contradiction_verified": next((summary["checker"]["final_contradiction_verified"] for summary in reuse_summaries if summary["instance_id"] == row["instance_id"]), False),
        }
        for row in rows
    ]
    _write_json(root / "proof_motif_generalization_certificates.json", certificates)
    _write_json(root / "proof_motif_generalization_checker_summary.json", checker_summary)
    _write_json(root / "near_motif_detection_trace.json", detection_traces)
    _write_json(root / "generalized_template_summary.json", template_summaries)
    _write_json(root / "reuse_site_verification_summary.json", reuse_summaries)
    _write_json(root / "compression_generalization_summary.json", compression_summaries)
    _write_json(root / "g11_operator_delta_summary.json", delta)
    _write_text(root / "PROOF_MOTIF_GENERALIZATION_REPORT.md", proof_motif_generalization_report(rows, delta))
    zip_sha = None
    if zip_path is not None:
        zip_sha = _make_zip(root, zip_path)
    return {
        "out_root": str(root),
        "rows": rows,
        "proof_motif_generalization_certificates": certificates,
        "proof_motif_generalization_checker_summary": checker_summary,
        "near_motif_detection_trace": detection_traces,
        "generalized_template_summary": template_summaries,
        "reuse_site_verification_summary": reuse_summaries,
        "compression_generalization_summary": compression_summaries,
        "g11_operator_delta_summary": delta,
        "artifact_zip": str(zip_path) if zip_path is not None else None,
        "artifact_sha256": zip_sha,
    }


def _cmd_run(args: argparse.Namespace) -> int:
    result = run_proof_motif_generalization_lab(
        instances=args.instances,
        out_root=args.out_root,
        strict=args.strict,
        zip_path=args.zip,
    )
    print(stable_json({"out_root": result["out_root"], "artifact_zip": result["artifact_zip"], "artifact_sha256": result["artifact_sha256"], "delta": result["g11_operator_delta_summary"]}))
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    formula = load_dimacs(args.cnf)
    data = json.loads(Path(args.certificate).read_text(encoding="utf-8"))
    result = check_proof_motif_generalization_certificate(formula, data)
    print(stable_json(result))
    return 0 if result["status"] == PROOF_MOTIF_GENERALIZATION_VERIFIED else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m witnora_core.proof_motif_generalization")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--instances", nargs="+", required=True)
    run.add_argument("--out-root", required=True)
    run.add_argument("--strict", action="store_true")
    run.add_argument("--zip")
    run.set_defaults(func=_cmd_run)
    check = sub.add_parser("check")
    check.add_argument("--cnf", required=True)
    check.add_argument("--certificate", required=True)
    check.set_defaults(func=_cmd_check)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
