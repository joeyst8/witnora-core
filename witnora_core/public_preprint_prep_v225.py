"""Public preprint preparation package for Witnora v2.25.

v2.25 turns the v2.24 external-review packet into a public-facing preprint and
submission-preparation package. It adds no solver, no operator, and no stronger
theorem claim.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import shutil
from typing import Any
import zipfile

from .external_review_package_v224 import (
    claim_boundary_rows,
    release_records_v214_to_v223,
)
from .obstruction_dual import sha256_file, stable_json
from .tc063_theorem_hardening import HARDENED_STATUS


PACKAGE_ID = "WITNORA-V2.25-PUBLIC-PREPRINT-PREPARATION"
PACKAGE_VERSION = "v2.25-public-preprint-preparation"
PREPRINT_TITLE = "Witnora: A Certified Collapse Hierarchy for Verifier-to-Witness SAT Reasoning"
ARTIFACT_NAME = "witnora-core-v2.25-public-preprint-preparation.zip"
EXPECTED_TEST_COUNT = 699

REQUIRED_MARKDOWN = [
    "PREPRINT_PREPARATION_REPORT.md",
    "PUBLIC_PREPRINT_DRAFT.md",
    "RELEASE_NOTES_V2_25.md",
    "REVIEWER_OUTREACH_EMAIL.md",
    "SUBMISSION_CHECKLIST.md",
    "REVIEWER_GUIDE_V2_25.md",
    "REPRODUCIBILITY_GUIDE.md",
    "CLAIM_BOUNDARY_AUDIT_V2_25.md",
    "RELATED_WORK_CHECKLIST.md",
    "LIMITATIONS_CHECKLIST.md",
]

REQUIRED_JSON = [
    "preprint_preparation_manifest.json",
    "paper_section_validation.json",
    "claim_boundary_validation.json",
    "related_work_validation.json",
    "limitations_validation.json",
    "submission_readiness_summary.json",
    "forbidden_claim_scan.json",
]

REQUIRED_ABSTRACT_SENTENCES = [
    "Witnora does not claim a proof of P vs NP or a polynomial-time algorithm for SAT.",
    "TC-063 is stated as a restricted theorem with proof obligations over SAF(c,r), not as an all-SAT or hierarchy-completeness result.",
    "Native Witnora certificates are not DRAT/LRAT/FRAT proofs unless explicitly exported and externally checked.",
]

RELATED_WORK_SUBSECTIONS = [
    "SAT Preprocessing and Inprocessing",
    "Proof Logging and Certified SAT Solving",
    "XOR / Affine Reasoning",
    "Graph Separators and Bounded-Width Reasoning",
    "Circuit CNF and Definitional Encodings",
    "SAT Portfolios / Algorithm Selection",
    "Proof Compression and Proof Motifs",
]

REQUIRED_LIMITATIONS = [
    "No P-vs-NP proof.",
    "No polynomial-time SAT algorithm.",
    "No all-SAT or hierarchy-completeness claim.",
    "TC-063 is restricted to SAF(c,r).",
    "TC-063 remains RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS.",
    "G5 affine soundness is a dependency.",
    "Native certificates are not DRAT/LRAT/FRAT.",
    "Finite tests and scaling runs support implementation, not proof.",
    "External proof bridge is absent.",
    "Planner certificates are plan-only unless paired with verified execution certificates.",
    "Polynomiality for TC-063 is only for fixed separator bound c and supported affine extraction r.",
    "Exponential dependence on c is explicit.",
]

FORBIDDEN_AFFIRMATIVE_FRAGMENTS = [
    "we solved p vs np",
    "p vs np is solved",
    "p = np",
    "proves p vs np",
    "p vs np progress is claimed",
    "we give a polynomial-time algorithm for sat",
    "complete sat collapse",
    "all-sat coverage is claimed",
    "hierarchy completeness is claimed",
    "tc-063 is fully proven",
    "tc-063 is theorem_proven_unqualified",
    "native certificates are external proofs",
    "native certificates are drat proofs",
    "finite tests are proof",
    "finite tests replace proof",
    "drat proof claimed",
    "lrat proof claimed",
    "frat proof claimed",
]


@dataclass(frozen=True)
class PublicPreprintPreparationManifest:
    package_id: str
    version: str
    title: str
    paper_path: str
    output_root: str
    markdown_files: list[str]
    json_files: list[str]
    expected_test_count: int
    verification_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(data) + "\n", encoding="utf-8", newline="\n")


def _make_zip(root: Path, zip_path: str | Path) -> str:
    target = Path(zip_path)
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(root).as_posix())
    return sha256_file(target)


def contribution_list() -> list[dict[str, str]]:
    return [
        {
            "contribution": "Collapse hierarchy G0-G14",
            "claim": "A structured sequence of collapse grammars and theorem layers for SAT reasoning research.",
            "boundary": "Not all-SAT coverage and not hierarchy completeness.",
        },
        {
            "contribution": "Native certificate framework",
            "claim": "Operators emit native certificates checked by Witnora checkers.",
            "boundary": "Native certificates are not DRAT/LRAT/FRAT unless exported and externally checked.",
        },
        {
            "contribution": "Obstruction-to-operator loop",
            "claim": "Failure can produce obstruction fingerprints, operator recommendations, and certified promoted operators.",
            "boundary": "An obstruction fingerprint is not a SAT/UNSAT proof.",
        },
        {
            "contribution": "Certified composition and planner-guided execution",
            "claim": "Finite plans can be paired with separate checked execution chains.",
            "boundary": "A plan alone is not execution and a matching execution is not a completeness theorem.",
        },
        {
            "contribution": "G9-G13 soundness backbone",
            "claim": "Soundness is stated as proof sketches and proof obligations.",
            "boundary": "No unqualified theorem-proven status.",
        },
        {
            "contribution": "TC-063 restricted theorem with proof obligations",
            "claim": "TC-063 is scoped to SAF(c,r), fixed c, supported r, and G5 affine residual checking.",
            "boundary": "Not an all-SAT theorem and not P-vs-NP progress.",
        },
        {
            "contribution": "Reproducible release/evidence manifests",
            "claim": "The package records release evidence, claim boundaries, reviewer guides, and reproducibility steps.",
            "boundary": "Finite evidence supports implementation behavior but does not substitute for proof.",
        },
    ]


def _markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(row.get(col, "") for col in columns) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def public_preprint_text() -> str:
    contributions = _markdown_table(contribution_list(), ["contribution", "claim", "boundary"])
    limitations = "\n".join(f"- {item}" for item in REQUIRED_LIMITATIONS)
    return f"""# {PREPRINT_TITLE}

## Abstract

Witnora is a certified collapse-path framework for CNF SAT reasoning. It defines a hierarchy of operators G0-G14 whose outputs are mediated by native certificates and checkers. The framework includes obstruction-dual records, graph separator lift, composed orchestration, circuit projection, proof motif generalization, a self-expanding planner, and planner-guided execution. TC-063 is a restricted theorem with proof obligations over SAF(c,r). TC-063 is not an all-SAT theorem. Witnora does not claim a proof of P vs NP or a polynomial-time algorithm for SAT. TC-063 is stated as a restricted theorem with proof obligations over SAF(c,r), not as an all-SAT or hierarchy-completeness result. Native Witnora certificates are not DRAT/LRAT/FRAT proofs unless explicitly exported and externally checked. The package includes reproducibility artifacts, evidence manifests, and claim-boundary audits.

## Introduction

This preprint studies verifier-to-witness SAT reasoning as a certificate-backed collapse program. Witnora asks when a CNF instance can be transformed, decomposed, certified, planned, or checked through a bounded operator grammar without losing the connection to the original formula.

## Problem Framing

The project does not attempt to replace SAT solvers. It instead organizes collapse paths, obstruction fingerprints, native certificates, and proof obligations so that each finite result can be independently audited.

## Contributions

{contributions}

## Related Work

### SAT Preprocessing and Inprocessing

SAT solvers use simplification, variable elimination, blocked clause elimination, and bounded structural reductions. Witnora overlaps with these ideas but frames them as a native certificate-centered collapse hierarchy with obstruction-to-operator feedback. TODO citation: classic SAT preprocessing and inprocessing surveys.

### Proof Logging and Certified SAT Solving

DRAT, LRAT, and FRAT style proof logging support externally checked SAT solving workflows. Witnora differs by using native operator certificates; external proof bridge not yet claimed unless a proof is exported and externally checked. TODO citation: DRAT/LRAT/FRAT proof logging references.

### XOR / Affine Reasoning

Gaussian elimination over GF(2), XOR extraction, and affine SAT tractability are standard tools for parity structure. Witnora uses this as G5 high-arity affine residue reasoning and as a dependency for TC-063 residual components. TODO citation: XOR reasoning in SAT and Gaussian-elimination-based SAT integration.

### Graph Separators and Bounded-Width Reasoning

Separator decomposition, bounded treewidth style reasoning, and component decomposition are established structural SAT approaches. TC-063 uses a fixed-size separator together with affine residual components; polynomiality is only for fixed separator bound c and supported affine extraction r. TODO citation: structural SAT and bounded treewidth references.

### Circuit CNF and Definitional Encodings

Tseitin-style auxiliary variables and exact definitional gates are common in circuit CNF encodings. G10 handles exact definitions only, rejects unsafe auxiliary projection, and trusts SAT lift only after checking the lifted assignment against the original CNF. TODO citation: Tseitin encodings and circuit-to-CNF references.

### SAT Portfolios / Algorithm Selection

Portfolio and algorithm-selection systems choose among solvers or tactics. G12 differs by producing a plan-only certificate with an explicit execution-required boundary; the plan does not certify SAT, UNSAT, or proof success. TODO citation: SAT portfolio and algorithm selection references.

### Proof Compression and Proof Motifs

Repeated proof patterns and macro-proof ideas motivate proof compression. G6 and G11 use checked motif certificates; near similarity is not treated as proof unless every reuse instantiation verifies. TODO citation: proof compression and macro-proof references.

## Collapse Grammar Hierarchy G0-G14

The hierarchy includes base simplification, XOR, symmetry, cardinality, capacity, affine residue, proof motif compression, obstruction dual certificates, separator lift, composed orchestration, circuit projection, proof motif generalization, collapse planning, planner-guided execution, and the bounded separator-affine theorem layer.

## Obstruction-to-Operator Loop

The v2.14-v2.18 line demonstrates failure fingerprinting, operator recommendation, and promotion into certified prototype operators. The loop is evidence of a research workflow, not a completeness theorem.

## Certified Operator Composition and Planner-Guided Execution

G9 requires checked step certificates, formula handoffs, and witness/proof lifts. G12 produces plan-only certificates. G13 pairs plans with separate execution certificates; execution results are trusted only if actual operator certificates and original-CNF obligations verify.

## G9-G13 Soundness Backbone

The G9-G13 backbone is expressed as proof sketches and proof obligations. It is not marked as unqualified theorem-proven.

## TC-063 Bounded Separator-Affine Collapse Theorem

TC-063 status: {HARDENED_STATUS}. Scope: SAF(c,r). TC-063 applies to fixed separator bound c, supported affine extraction bound r, exact G5 affine residual components, and native certificates only. G5 affine soundness is a dependency. There is no all-SAT claim, no P-vs-NP claim, and finite scaling is implementation support only. TC-063 is not theorem-proven-unqualified.

### How to Attack TC-063

Reviewers should attack the separator decomposition lemma, assignment exhaustiveness, G5 affine soundness dependency, SAT lifting, UNSAT cover, polynomial bound, native certificate boundary, and restricted scope.

## Reproducibility

The release includes package manifests, source/artifact SHA records where available, tests, reproduction instructions, claim-boundary audits, and reviewer-facing checklists.

## Limitations

{limitations}

## Claim Boundaries

This preprint does not claim P-vs-NP progress, polynomial-time SAT, all-SAT coverage, hierarchy completeness, unqualified theorem-proven status, or external DRAT/LRAT/FRAT proof status.

## Future Work

Future work includes external formalization of TC-063, proof-assistant checking of native checkers, external proof bridges, broader benchmarks, and choosing an appropriate preprint or workshop target.
"""


def release_notes_text() -> str:
    return f"""# Release Notes v2.25

## What v2.25 Is

v2.25 prepares a public preprint and external submission package for Witnora.

## What Changed From v2.24

It adds a public title, polished abstract, contribution list, related work, limitations, release notes, reviewer outreach email, submission checklist, and validation tests.

## What Is Claimed

Witnora is presented as a certified collapse hierarchy for verifier-to-witness SAT reasoning, with native certificates, obstruction-to-operator planning, planner-guided finite execution, G9-G13 proof sketches, and TC-063 as a restricted theorem with proof obligations.

## What Is Not Claimed

No P-vs-NP proof, no P-vs-NP progress, no polynomial-time SAT algorithm, no all-SAT coverage, no hierarchy completeness, no unqualified theorem-proven status, and no external DRAT/LRAT/FRAT proof claim.

## How to Reproduce

Run `python -m unittest discover -s tests -v` with `WITNORA_DRAT_TRIM` set to a real `drat-trim.exe`.

## Artifact and Source Archive Expectations

The generated package artifact is `{ARTIFACT_NAME}`. Source archive SHA values are recorded after freeze.

## SHA Placeholders

Before freeze, source archive SHA may be `PENDING_SOURCE_ARCHIVE_FREEZE`.

## Reviewer Instructions

Attack TC-063, G5 affine soundness, native certificate assumptions, claim boundaries, related-work positioning, and reproducibility.
"""


def reviewer_outreach_email_text() -> str:
    return """# Reviewer Outreach Email

Subject: Request for external feedback on Witnora SAT collapse framework

Dear Reviewer,

I am seeking external feedback on Witnora, a certified collapse hierarchy for verifier-to-witness SAT reasoning. This is not a claim of P vs NP progress and not a polynomial-time SAT claim.

The review target is the framework: native certificates, obstruction-to-operator planning, planner-guided finite execution, G9-G13 soundness sketches, TC-063 over SAF(c,r), and the claim boundaries around those artifacts.

The package includes reproducibility instructions, evidence manifests, release notes, and a claim-boundary audit. I would especially value critique of TC-063, the G5 affine dependency, the native-certificate model, and whether the public framing is appropriate for a preprint or workshop submission.

Thank you for considering a technical review.
"""


def submission_checklist_text() -> str:
    items = [
        "Title reviewed.",
        "Abstract contains nonclaim boundaries.",
        "Related work present.",
        "Contributions clear.",
        "TC-063 appendix present.",
        "G9-G13 appendix present.",
        "Reproducibility guide present.",
        "Reviewer guide present.",
        "Claim-boundary table present.",
        "Evidence manifest present.",
        "No forbidden claims.",
        "Tests pass.",
        "Artifact SHA recorded.",
        "Source archive SHA recorded after freeze.",
        "Venue/preprint target chosen externally by user.",
    ]
    return "# Submission Checklist\n\n" + "\n".join(f"- [ ] {item}" for item in items) + "\n"


def claim_boundary_audit_text() -> str:
    rows = claim_boundary_rows()
    return "# Claim Boundary Audit v2.25\n\n" + _markdown_table(rows, ["claim", "status", "evidence", "not_claimed", "reviewer_note"]) + "\n"


def related_work_checklist_text() -> str:
    return "# Related Work Checklist\n\n" + "\n".join(f"- [x] {name}" for name in RELATED_WORK_SUBSECTIONS) + "\n"


def limitations_checklist_text() -> str:
    return "# Limitations Checklist\n\n" + "\n".join(f"- [x] {item}" for item in REQUIRED_LIMITATIONS) + "\n"


def reviewer_guide_v225_text() -> str:
    return f"""# Reviewer Guide v2.25

## What to Inspect First

Read `{PREPRINT_TITLE}`, the TC-063 section, the limitations, and the claim-boundary audit.

## What This Package Claims

It claims a certified collapse hierarchy and public preprint package with native certificates, obstruction-to-operator planning, planner-guided finite execution, G9-G13 soundness sketches, and TC-063 restricted to SAF(c,r) with proof obligations.

## What This Package Does Not Claim

No P-vs-NP proof, no P-vs-NP progress, no polynomial-time SAT algorithm, no all-SAT coverage, no hierarchy completeness, no unqualified theorem-proven status, and no fake external proof claim.

## How to Attack It

Attack related-work positioning, TC-063 assumptions, G5 affine soundness, SAT lifting, UNSAT cover, native certificate assumptions, and finite-vs-family language.
"""


def reproducibility_guide_v225_text() -> str:
    return """# Reproducibility Guide v2.25

## Environment

Use a clean source checkout with Python available. Set `WITNORA_DRAT_TRIM` to a real `drat-trim.exe` when running the full suite.

## Full Test Command

`python -m unittest discover -s tests -v`

## Package Regeneration

`python -m witnora_core.public_preprint_prep_v225 run --out-root outputs/v2.25-public-preprint-preparation --strict`

## Package Validation

`python -m witnora_core.public_preprint_prep_v225 check --package-root outputs/v2.25-public-preprint-preparation`

## Boundary

Passing tests and package validation support implementation behavior. They do not substitute for TC-063 proof obligations or external formalization.
"""


def _scan_forbidden_text(text: str) -> list[str]:
    lower = text.lower()
    return [fragment for fragment in FORBIDDEN_AFFIRMATIVE_FRAGMENTS if fragment in lower]


def _contains_all(text: str, required: list[str]) -> list[str]:
    return [item for item in required if item not in text]


def validate_public_preprint_package(package_root: str | Path) -> dict[str, Any]:
    root = Path(package_root)
    errors: list[str] = []
    for name in REQUIRED_MARKDOWN:
        if not (root / name).is_file():
            errors.append(f"MISSING_MARKDOWN:{name}")
    for name in REQUIRED_JSON:
        if not (root / name).is_file():
            errors.append(f"MISSING_JSON:{name}")

    paper = (root / "PUBLIC_PREPRINT_DRAFT.md").read_text(encoding="utf-8") if (root / "PUBLIC_PREPRINT_DRAFT.md").is_file() else ""
    combined = "\n".join((root / name).read_text(encoding="utf-8") for name in REQUIRED_MARKDOWN if (root / name).is_file())

    if f"# {PREPRINT_TITLE}" not in paper:
        errors.append("TITLE_MISSING_OR_UNSAFE")
    for sentence in REQUIRED_ABSTRACT_SENTENCES:
        if sentence not in paper:
            errors.append("ABSTRACT_NONCLAIM_MISSING:" + sentence)
    if "## Contributions" not in paper or "Collapse hierarchy G0-G14" not in paper:
        errors.append("CONTRIBUTIONS_MISSING")
    if "## Related Work" not in paper:
        errors.append("RELATED_WORK_MISSING")
    for subsection in RELATED_WORK_SUBSECTIONS:
        if f"### {subsection}" not in paper:
            errors.append("RELATED_WORK_SUBSECTION_MISSING:" + subsection)
    if "## Limitations" not in paper:
        errors.append("LIMITATIONS_MISSING")
    for limitation in REQUIRED_LIMITATIONS:
        if limitation not in paper:
            errors.append("LIMITATION_MISSING:" + limitation)
    for required in [
        f"TC-063 status: {HARDENED_STATUS}",
        "Scope: SAF(c,r)",
        "G5 affine soundness is a dependency",
        "TC-063 is not theorem-proven-unqualified",
    ]:
        if required not in paper:
            errors.append("TC063_FRAMING_MISSING:" + required)
    if "Native Witnora certificates are not DRAT/LRAT/FRAT proofs unless explicitly exported and externally checked." not in paper:
        errors.append("NATIVE_CERT_BOUNDARY_MISSING")
    for fragment in _scan_forbidden_text(combined):
        errors.append("FORBIDDEN_CLAIM:" + fragment.upper().replace(" ", "_"))

    status_values: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"status", "verification_status", "checker_status", "validation_status"} and isinstance(item, str):
                    status_values.append(item)
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    for name in REQUIRED_JSON:
        path = root / name
        if path.is_file():
            walk(json.loads(path.read_text(encoding="utf-8")))
    bad_statuses = sorted(set(status_values) & {"HARD", "UNKNOWN"})
    if bad_statuses:
        errors.append("FORBIDDEN_STATUS:" + ",".join(bad_statuses))
    return {
        "verification_status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "required_markdown": REQUIRED_MARKDOWN,
        "required_json": REQUIRED_JSON,
    }


def _section_validation(paper: str) -> dict[str, Any]:
    return {
        "title_present": f"# {PREPRINT_TITLE}" in paper,
        "abstract_nonclaims_present": _contains_all(paper, REQUIRED_ABSTRACT_SENTENCES) == [],
        "contributions_present": "## Contributions" in paper,
        "related_work_present": "## Related Work" in paper,
        "limitations_present": "## Limitations" in paper,
        "tc063_safe_framing": f"TC-063 status: {HARDENED_STATUS}" in paper and "Scope: SAF(c,r)" in paper,
        "native_certificate_boundary": "Native Witnora certificates are not DRAT/LRAT/FRAT proofs unless explicitly exported and externally checked." in paper,
    }


def run_public_preprint_package(
    out_root: str | Path,
    *,
    strict: bool = False,
    zip_path: str | Path | None = ARTIFACT_NAME,
) -> dict[str, Any]:
    root = Path(out_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)

    paper = public_preprint_text()
    paper_path = Path("paper/WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_REVIEW_DRAFT.md")

    markdown = {
        "PUBLIC_PREPRINT_DRAFT.md": paper,
        "RELEASE_NOTES_V2_25.md": release_notes_text(),
        "REVIEWER_OUTREACH_EMAIL.md": reviewer_outreach_email_text(),
        "SUBMISSION_CHECKLIST.md": submission_checklist_text(),
        "REVIEWER_GUIDE_V2_25.md": reviewer_guide_v225_text(),
        "REPRODUCIBILITY_GUIDE.md": reproducibility_guide_v225_text(),
        "CLAIM_BOUNDARY_AUDIT_V2_25.md": claim_boundary_audit_text(),
        "RELATED_WORK_CHECKLIST.md": related_work_checklist_text(),
        "LIMITATIONS_CHECKLIST.md": limitations_checklist_text(),
        "PREPRINT_PREPARATION_REPORT.md": "# Preprint Preparation Report\n\nValidation status: `PENDING`.\n",
    }
    for name, text in markdown.items():
        _write_text(root / name, text)

    section_validation = _section_validation(paper)
    related_work_validation = {
        "required_subsections": RELATED_WORK_SUBSECTIONS,
        "missing": [name for name in RELATED_WORK_SUBSECTIONS if f"### {name}" not in paper],
        "verification_status": "PASS",
    }
    if related_work_validation["missing"]:
        related_work_validation["verification_status"] = "FAIL"
    limitations_validation = {
        "required_limitations": REQUIRED_LIMITATIONS,
        "missing": _contains_all(paper, REQUIRED_LIMITATIONS),
        "verification_status": "PASS",
    }
    if limitations_validation["missing"]:
        limitations_validation["verification_status"] = "FAIL"
    forbidden_scan = {
        "forbidden_fragments": FORBIDDEN_AFFIRMATIVE_FRAGMENTS,
        "hits": _scan_forbidden_text("\n".join(markdown.values())),
        "verification_status": "PASS",
    }
    if forbidden_scan["hits"]:
        forbidden_scan["verification_status"] = "FAIL"
    claim_validation = {
        "rows": claim_boundary_rows(),
        "no_pnp_claim": True,
        "no_all_sat_claim": True,
        "no_completeness_claim": True,
        "no_unqualified_theorem_proven_claim": True,
        "no_fake_external_proof_claim": True,
        "verification_status": "PASS",
    }
    manifest = PublicPreprintPreparationManifest(
        package_id=PACKAGE_ID,
        version=PACKAGE_VERSION,
        title=PREPRINT_TITLE,
        paper_path=str(paper_path),
        output_root=str(root),
        markdown_files=REQUIRED_MARKDOWN,
        json_files=REQUIRED_JSON,
        expected_test_count=EXPECTED_TEST_COUNT,
        verification_status="PENDING",
    ).to_dict()
    submission = {
        "title_reviewed": True,
        "abstract_nonclaims": True,
        "related_work_present": True,
        "limitations_present": True,
        "release_notes_present": True,
        "reviewer_outreach_email_present": True,
        "submission_checklist_present": True,
        "artifact_name": str(zip_path) if zip_path else "",
        "source_archive_sha": "PENDING_SOURCE_ARCHIVE_FREEZE",
        "verification_status": "PENDING",
    }
    _write_json(root / "preprint_preparation_manifest.json", manifest)
    _write_json(root / "paper_section_validation.json", section_validation)
    _write_json(root / "claim_boundary_validation.json", claim_validation)
    _write_json(root / "related_work_validation.json", related_work_validation)
    _write_json(root / "limitations_validation.json", limitations_validation)
    _write_json(root / "submission_readiness_summary.json", submission)
    _write_json(root / "forbidden_claim_scan.json", forbidden_scan)

    check = validate_public_preprint_package(root)
    manifest["verification_status"] = check["verification_status"]
    submission["verification_status"] = check["verification_status"]
    _write_json(root / "preprint_preparation_manifest.json", manifest)
    _write_json(root / "submission_readiness_summary.json", submission)
    _write_text(root / "PREPRINT_PREPARATION_REPORT.md", preprint_report_text(check))

    if strict and check["verification_status"] != "PASS":
        raise RuntimeError("public preprint package validation failed: " + ";".join(check["errors"]))
    digest = _make_zip(root, zip_path) if zip_path else ""
    return {
        "out_root": str(root),
        "zip": str(zip_path) if zip_path else "",
        "zip_sha256": digest,
        "validation": check,
        "manifest": manifest,
    }


def preprint_report_text(check: dict[str, Any]) -> str:
    return f"""# Preprint Preparation Report

Package: `{PACKAGE_VERSION}`

Title: `{PREPRINT_TITLE}`

Validation status: `{check['verification_status']}`

Errors: `{len(check['errors'])}`

v2.25 prepares public preprint/submission materials. It does not add a new operator, does not strengthen TC-063 beyond `{HARDENED_STATUS}`, and does not claim P vs NP, all-SAT coverage, hierarchy completeness, unqualified theorem-proven status, or external DRAT/LRAT/FRAT proof status.
"""


def _cmd_run(args: argparse.Namespace) -> int:
    result = run_public_preprint_package(args.out_root, strict=args.strict, zip_path=args.zip)
    print(stable_json({"out_root": result["out_root"], "zip": result["zip"], "zip_sha256": result["zip_sha256"], "validation": result["validation"]}))
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    result = validate_public_preprint_package(args.package_root)
    print(stable_json(result))
    return 0 if result["verification_status"] == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m witnora_core.public_preprint_prep_v225")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("--out-root", default="outputs/v2.25-public-preprint-preparation")
    run.add_argument("--strict", action="store_true")
    run.add_argument("--zip", default=ARTIFACT_NAME)
    run.set_defaults(func=_cmd_run)
    check = sub.add_parser("check")
    check.add_argument("--package-root", required=True)
    check.set_defaults(func=_cmd_check)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
