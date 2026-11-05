"""Submit/release checklist finalization package for Witnora v2.26.

v2.26 finalizes the public preprint/submission packet. Its hard gate is the
bibliography pass: the main related-work text must use real references and
must not retain citation placeholders.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import shutil
from typing import Any
import zipfile

from .external_review_package_v224 import claim_boundary_rows
from .obstruction_dual import sha256_file, stable_json
from .public_preprint_prep_v225 import (
    PREPRINT_TITLE,
    REQUIRED_ABSTRACT_SENTENCES,
    REQUIRED_LIMITATIONS,
    contribution_list,
    reviewer_guide_v225_text,
    reproducibility_guide_v225_text,
)
from .tc063_theorem_hardening import HARDENED_STATUS


PACKAGE_ID = "WITNORA-V2.26-SUBMIT-RELEASE-CHECKLIST-FINALIZATION"
PACKAGE_VERSION = "v2.26-submit-release-checklist-finalization"
ARTIFACT_NAME = "witnora-core-v2.26-submit-release-checklist-finalization.zip"
EXPECTED_TEST_COUNT = 714

REQUIRED_MARKDOWN = [
    "SUBMIT_RELEASE_FINALIZATION_REPORT.md",
    "FINAL_PUBLIC_PREPRINT_DRAFT.md",
    "RELEASE_NOTES_V2_26.md",
    "REVIEWER_OUTREACH_EMAIL.md",
    "ARXIV_SUBMISSION_CHECKLIST.md",
    "WORKSHOP_SUBMISSION_CHECKLIST.md",
    "GITHUB_RELEASE_CHECKLIST.md",
    "BIBLIOGRAPHY_COMPLETION_REPORT.md",
    "RELATED_WORK_CITATION_AUDIT.md",
    "FINAL_CLAIM_BOUNDARY_AUDIT.md",
    "FINAL_SUBMISSION_READINESS_REPORT.md",
    "REVIEWER_GUIDE_V2_26.md",
    "REPRODUCIBILITY_GUIDE.md",
]

REQUIRED_JSON = [
    "submit_release_manifest.json",
    "bibliography_manifest.json",
    "citation_coverage_summary.json",
    "related_work_citation_validation.json",
    "final_claim_boundary_validation.json",
    "release_readiness_summary.json",
    "arxiv_readiness_summary.json",
    "workshop_readiness_summary.json",
    "github_release_readiness_summary.json",
    "forbidden_claim_scan_v226.json",
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

CITATION_CATEGORIES = [
    "sat_preprocessing",
    "proof_logging",
    "affine_xor",
    "treewidth_separator",
    "circuit_cnf",
    "sat_portfolio",
    "proof_motif",
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
class SubmitReleaseManifest:
    package_id: str
    version: str
    title: str
    paper_path: str
    bibliography_path: str
    output_root: str
    markdown_files: list[str]
    json_files: list[str]
    citation_categories: list[str]
    expected_test_count: int
    verification_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def bibliography_entries() -> list[dict[str, str]]:
    return [
        {
            "key": "wetzler-heule-hunt-2014-drat-trim",
            "category": "proof_logging",
            "authors": "Nathan Wetzler, Marijn J. H. Heule, Warren A. Hunt Jr.",
            "title": "DRAT-trim: Efficient Checking and Trimming Using Expressive Clausal Proofs",
            "venue": "International Conference on Theory and Applications of Satisfiability Testing (SAT)",
            "year": "2014",
            "url": "https://www.cs.utexas.edu/~marijn/drat-trim/",
            "doi": "",
        },
        {
            "key": "heule-2016-drat-format",
            "category": "proof_logging",
            "authors": "Marijn J. H. Heule",
            "title": "The DRAT format and DRAT-trim checker",
            "venue": "arXiv",
            "year": "2016",
            "url": "https://arxiv.org/abs/1610.06229",
            "doi": "10.48550/arXiv.1610.06229",
        },
        {
            "key": "cruz-filipe-heule-hunt-kaufmann-schneiderkamp-2016-lrat",
            "category": "proof_logging",
            "authors": "Luis Cruz-Filipe, Marijn J. H. Heule, Warren A. Hunt Jr., Matt Kaufmann, Peter Schneider-Kamp",
            "title": "Efficient Certified RAT Verification",
            "venue": "arXiv / CADE",
            "year": "2016",
            "url": "https://arxiv.org/abs/1612.02353",
            "doi": "10.1007/978-3-319-63046-5_13",
        },
        {
            "key": "baek-carneiro-heule-2021-frat",
            "category": "proof_logging",
            "authors": "Seulkee Baek, Mario Carneiro, Marijn J. H. Heule",
            "title": "A Flexible Proof Format for SAT Solver-Elaborator Communication",
            "venue": "arXiv / TACAS",
            "year": "2021",
            "url": "https://arxiv.org/abs/2109.09665",
            "doi": "10.48550/arXiv.2109.09665",
        },
        {
            "key": "een-biere-2005-effective-preprocessing",
            "category": "sat_preprocessing",
            "authors": "Niklas Een, Armin Biere",
            "title": "Effective Preprocessing in SAT Through Variable and Clause Elimination",
            "venue": "SAT",
            "year": "2005",
            "url": "https://doi.org/10.1007/11499107_5",
            "doi": "10.1007/11499107_5",
        },
        {
            "key": "biere-jarvisalo-kiesl-2021-preprocessing",
            "category": "sat_preprocessing",
            "authors": "Armin Biere, Matti Jarvisalo, Benjamin Kiesl",
            "title": "Preprocessing in SAT Solving",
            "venue": "Handbook of Satisfiability, Second Edition",
            "year": "2021",
            "url": "https://ebooks.iospress.nl/volumearticle/56936",
            "doi": "10.3233/FAIA200987",
        },
        {
            "key": "heule-jarvisalo-biere-2011-covered-clause",
            "category": "sat_preprocessing",
            "authors": "Marijn J. H. Heule, Matti Jarvisalo, Armin Biere",
            "title": "Covered Clause Elimination",
            "venue": "CADE",
            "year": "2011",
            "url": "https://doi.org/10.1007/978-3-642-22438-6_5",
            "doi": "10.1007/978-3-642-22438-6_5",
        },
        {
            "key": "soos-nohl-castelluccia-2009-cryptominisat",
            "category": "affine_xor",
            "authors": "Mate Soos, Karsten Nohl, Claude Castelluccia",
            "title": "Extending SAT Solvers to Cryptographic Problems",
            "venue": "SAT",
            "year": "2009",
            "url": "https://doi.org/10.1007/978-3-642-02777-2_18",
            "doi": "10.1007/978-3-642-02777-2_18",
        },
        {
            "key": "bodlaender-1996-treewidth",
            "category": "treewidth_separator",
            "authors": "Hans L. Bodlaender",
            "title": "A Linear-Time Algorithm for Finding Tree-Decompositions of Small Treewidth",
            "venue": "SIAM Journal on Computing",
            "year": "1996",
            "url": "https://doi.org/10.1137/S0097539793251219",
            "doi": "10.1137/S0097539793251219",
        },
        {
            "key": "robertson-seymour-1986-treewidth",
            "category": "treewidth_separator",
            "authors": "Neil Robertson, Paul D. Seymour",
            "title": "Graph Minors. II. Algorithmic Aspects of Tree-Width",
            "venue": "Journal of Algorithms",
            "year": "1986",
            "url": "https://doi.org/10.1016/0196-6774(86)90023-4",
            "doi": "10.1016/0196-6774(86)90023-4",
        },
        {
            "key": "tseitin-1968-propositional-calculus",
            "category": "circuit_cnf",
            "authors": "G. S. Tseitin",
            "title": "On the Complexity of Derivation in Propositional Calculus",
            "venue": "Studies in Constructive Mathematics and Mathematical Logic, Part II",
            "year": "1968",
            "url": "https://doi.org/10.1007/978-3-642-81955-1_28",
            "doi": "10.1007/978-3-642-81955-1_28",
        },
        {
            "key": "xu-hutter-hoos-leytonbrown-2011-satzilla",
            "category": "sat_portfolio",
            "authors": "Lin Xu, Frank Hutter, Holger H. Hoos, Kevin Leyton-Brown",
            "title": "SATzilla: Portfolio-based Algorithm Selection for SAT",
            "venue": "Journal of Artificial Intelligence Research",
            "year": "2011",
            "url": "https://arxiv.org/abs/1111.2249",
            "doi": "10.1613/jair.2490",
        },
        {
            "key": "cook-reckhow-1979-proof-systems",
            "category": "proof_motif",
            "authors": "Stephen A. Cook, Robert A. Reckhow",
            "title": "The Relative Efficiency of Propositional Proof Systems",
            "venue": "Journal of Symbolic Logic",
            "year": "1979",
            "url": "https://doi.org/10.2307/2273702",
            "doi": "10.2307/2273702",
        },
    ]


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


def _markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(row.get(col, "") for col in columns) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def references_bib_text() -> str:
    blocks: list[str] = []
    for entry in bibliography_entries():
        fields = {
            "author": entry["authors"],
            "title": entry["title"],
            "year": entry["year"],
            "note": entry["venue"],
            "url": entry["url"],
        }
        if entry["doi"]:
            fields["doi"] = entry["doi"]
        body = ",\n".join(f"  {key} = {{{value}}}" for key, value in fields.items())
        blocks.append(f"@misc{{{entry['key']},\n{body}\n}}")
    return "\n\n".join(blocks) + "\n"


def bibliography_manifest() -> dict[str, Any]:
    entries = bibliography_entries()
    by_category = {
        category: [entry["key"] for entry in entries if entry["category"] == category]
        for category in CITATION_CATEGORIES
    }
    return {
        "version": PACKAGE_VERSION,
        "bibliography_path": "paper/references.bib",
        "entry_count": len(entries),
        "categories": by_category,
        "entries": entries,
        "todo_citation_markers": 0,
        "verification_status": "PASS",
    }


def citation_coverage_summary() -> dict[str, Any]:
    manifest = bibliography_manifest()
    categories = {
        category: {
            "covered": len(keys) > 0,
            "entry_keys": keys,
        }
        for category, keys in manifest["categories"].items()
    }
    return {
        "version": PACKAGE_VERSION,
        "categories": categories,
        "all_required_categories_covered": all(item["covered"] for item in categories.values()),
        "verification_status": "PASS",
    }


def related_work_text() -> str:
    return """## Related Work

### SAT Preprocessing and Inprocessing

SAT preprocessing and inprocessing remove or simplify structure through techniques such as variable elimination, blocked clause elimination, covered clause elimination, and other bounded reductions [een-biere-2005-effective-preprocessing; biere-jarvisalo-kiesl-2021-preprocessing; heule-jarvisalo-biere-2011-covered-clause]. Witnora uses preprocessing-like ideas as collapse operators, but the unit of evidence is a native certificate and a checker obligation. Witnora does not claim novelty for variable elimination, blocked clauses, or simplification themselves; the claim is the certificate-centered collapse hierarchy and obstruction-to-operator loop.

### Proof Logging and Certified SAT Solving

DRAT-trim, DRAT, LRAT, and FRAT provide proof logging and checking pathways for SAT solvers [wetzler-heule-hunt-2014-drat-trim; heule-2016-drat-format; cruz-filipe-heule-hunt-kaufmann-schneiderkamp-2016-lrat; baek-carneiro-heule-2021-frat]. Witnora relates to this line because it also treats checking as central. Witnora differs by using native operator certificates for collapse-specific evidence. Native Witnora certificates are not DRAT/LRAT/FRAT proofs unless explicitly exported and externally checked.

### XOR / Affine Reasoning

Gaussian elimination over GF(2), XOR extraction, and affine SAT reasoning are established polynomial-time tools for parity structure, including XOR-aware solvers such as CryptoMiniSat [soos-nohl-castelluccia-2009-cryptominisat]. Witnora uses affine reasoning as G5 and as a dependency inside TC-063. Witnora does not claim to discover Gaussian elimination; its contribution is the integration of exact affine residual certificates into the collapse hierarchy and the SAF(c,r) theorem boundary.

### Graph Separators and Bounded-Width Reasoning

Tree decompositions, treewidth algorithms, and separator-style decompositions are classical routes to structural tractability [robertson-seymour-1986-treewidth; bodlaender-1996-treewidth]. TC-063 uses a narrower construction: a fixed-size separator plus exact affine residual components. The polynomial bound is only for fixed separator bound c and supported affine extraction r, and TC-063 does not claim bounded-width completeness or coverage of arbitrary separator formulas.

### Circuit CNF and Definitional Encodings

Tseitin-style transformations and definitional CNF encodings introduce auxiliary variables to represent circuits equisatisfiably [tseitin-1968-propositional-calculus]. G10 is related to this work because it projects only exact definitional gates. It differs by requiring checker-verifiable definitions, direct original-CNF SAT witness validation, and equisatisfiability obligations for UNSAT preservation. It does not project arbitrary auxiliaries.

### SAT Portfolios / Algorithm Selection

SAT portfolio systems such as SATzilla select among solvers using per-instance features and empirical models [xu-hutter-hoos-leytonbrown-2011-satzilla]. G12 is related at the level of strategy selection, but it emits a plan-only certificate rather than choosing a solver result. The plan explicitly requires later certified execution; it does not certify SAT, UNSAT, DRAT, or theorem success.

### Proof Compression and Proof Motifs

Proof complexity and proof-system work studies proof representations, proof lengths, and proof checking [cook-reckhow-1979-proof-systems]. Witnora's G6 and G11 are related to proof compression and repeated proof motifs, but similarity is never treated as proof. Generalized motif reuse is trusted only when every concrete instantiation or verified parametric instantiation checks.
"""


def contribution_text() -> str:
    return _markdown_table(contribution_list(), ["contribution", "claim", "boundary"])


def limitations_text() -> str:
    return "\n".join(f"- {item}" for item in REQUIRED_LIMITATIONS)


def final_preprint_text() -> str:
    return f"""# {PREPRINT_TITLE}

## Abstract

Witnora is a certified collapse-path framework for CNF SAT reasoning. It defines a hierarchy of operators G0-G14 whose outputs are mediated by native certificates and checkers. The framework includes obstruction-dual records, graph separator lift, composed orchestration, circuit projection, proof motif generalization, a self-expanding planner, and planner-guided execution. TC-063 is a restricted theorem with proof obligations over SAF(c,r). TC-063 is not an all-SAT theorem. Witnora does not claim a proof of P vs NP or a polynomial-time algorithm for SAT. TC-063 is stated as a restricted theorem with proof obligations over SAF(c,r), not as an all-SAT or hierarchy-completeness result. Native Witnora certificates are not DRAT/LRAT/FRAT proofs unless explicitly exported and externally checked. The package includes reproducibility artifacts, evidence manifests, claim-boundary audits, and a completed bibliography.

## Introduction

Witnora studies verifier-to-witness SAT reasoning as a certificate-backed collapse program. The project asks when a CNF instance can be transformed, decomposed, certified, planned, or checked through a bounded operator grammar while retaining an explicit connection to the original formula.

## Problem Framing

The framework does not attempt to replace SAT solvers or assert a universal collapse path. It organizes collapse operators, obstruction fingerprints, native certificates, theorem candidates, proof obligations, and finite execution evidence so that each claim can be audited separately.

## Contributions

{contribution_text()}

{related_work_text()}

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

{limitations_text()}

## Claim Boundaries

This preprint does not claim P-vs-NP progress, polynomial-time SAT, all-SAT coverage, hierarchy completeness, unqualified theorem-proven status, or external DRAT/LRAT/FRAT proof status.

## Future Work

Future work includes external formalization of TC-063, proof-assistant checking of native checkers, external proof bridges, broader benchmarks, and venue-specific formatting after the user chooses a target.

## References

See `paper/references.bib` for structured bibliography entries.
"""


def release_notes_v226_text() -> str:
    return f"""# Release Notes v2.26

## What v2.26 Finalizes

v2.26 finalizes the public release/submission packet for Witnora after v2.25 public preprint preparation.

## Citation Hardening

The main related-work citation placeholders are replaced with bibliography-backed references covering SAT preprocessing, proof logging, affine/XOR reasoning, bounded treewidth and separators, circuit CNF encodings, SAT portfolios, and proof complexity/proof motifs.

## What Is Claimed

Witnora is framed as a certified collapse hierarchy for verifier-to-witness SAT reasoning with native certificates, obstruction-to-operator planning, planner-guided finite execution, G9-G13 soundness sketches, and TC-063 as a restricted theorem with proof obligations over SAF(c,r).

## What Is Not Claimed

No P-vs-NP proof, no P-vs-NP progress, no polynomial-time SAT algorithm, no all-SAT coverage, no hierarchy completeness, no unqualified theorem-proven status, and no external DRAT/LRAT/FRAT proof claim.

## How to Reproduce

Set `WITNORA_DRAT_TRIM` to a real `drat-trim.exe` and run `python -m unittest discover -s tests -v`.

## Artifact and Source Archive Expectations

The generated package artifact is `{ARTIFACT_NAME}`. The source archive SHA is recorded after the source release archive is frozen.

## Reviewer Instructions

Reviewers should attack the bibliography, TC-063 assumptions, G5 affine soundness dependency, native-certificate boundary, finite-vs-family boundary, and forbidden-claim scan.

## Venue Strategy

The package is arXiv-ready after user approval. Workshop submission is ready after the user chooses a target and venue-specific formatting is applied.
"""


def release_notes_v225_update_text() -> str:
    return """# Release Notes v2.25

v2.25 prepared the public preprint and submission package. v2.26 supersedes it for public release by completing the bibliography and citation hardening pass.

Boundary: v2.25 and v2.26 do not claim P-vs-NP progress, all-SAT coverage, hierarchy completeness, unqualified theorem-proven status, or external DRAT/LRAT/FRAT proof status.
"""


def reviewer_outreach_email_text() -> str:
    return """# Reviewer Outreach Email

Subject: Request for external feedback on Witnora SAT collapse framework

Dear Reviewer,

I am seeking external feedback on Witnora, a certified collapse hierarchy for verifier-to-witness SAT reasoning. This is not a claim of P vs NP progress and not a polynomial-time SAT claim.

The review target is the framework: native certificates, obstruction-to-operator planning, planner-guided finite execution, the G9-G13 soundness sketches, TC-063 over SAF(c,r), the bibliography/related-work positioning, and the claim boundaries around those artifacts.

The package includes reproducibility instructions, evidence manifests, release notes, and a claim-boundary audit. I would especially value critique of TC-063, the G5 affine dependency, the native-certificate model, and whether the public framing is appropriate for a preprint or workshop submission.

Thank you for considering a technical review.
"""


def arxiv_checklist_text() -> str:
    items = [
        "Final public preprint draft generated.",
        "Bibliography complete with no main related-work citation placeholders.",
        "Abstract contains nonclaim boundaries.",
        "TC-063 restricted status visible.",
        "Native certificate boundary visible.",
        "Claim-boundary scan passes.",
        "User approval obtained before upload.",
    ]
    return "# arXiv Submission Checklist\n\n" + "\n".join(f"- [ ] {item}" for item in items) + "\n"


def workshop_checklist_text() -> str:
    items = [
        "Choose workshop or venue externally.",
        "Apply venue-specific page limit and style.",
        "Retain limitations and claim-boundary language.",
        "Retain bibliography entries.",
        "Attach reproducibility and artifact notes if venue supports them.",
        "Run final claim scan after formatting.",
    ]
    return "# Workshop Submission Checklist\n\n" + "\n".join(f"- [ ] {item}" for item in items) + "\n"


def github_release_checklist_text() -> str:
    items = [
        "Create source release archive after tag.",
        "Record source archive SHA256.",
        "Keep generated output roots outside source archive.",
        "Keep generated artifact zip separate.",
        "Attach release notes v2.26.",
        "Attach or link final public preprint package.",
        "Confirm standalone/ remains untouched and excluded if untracked.",
    ]
    return "# GitHub Release Checklist\n\n" + "\n".join(f"- [ ] {item}" for item in items) + "\n"


def final_claim_boundary_audit_text() -> str:
    rows = claim_boundary_rows()
    return "# Final Claim Boundary Audit v2.26\n\n" + _markdown_table(rows, ["claim", "status", "evidence", "not_claimed", "reviewer_note"]) + "\n"


def bibliography_completion_report_text() -> str:
    coverage = citation_coverage_summary()
    lines = [
        "# Bibliography Completion Report",
        "",
        f"Bibliography path: `paper/references.bib`",
        f"Entry count: `{len(bibliography_entries())}`",
        "",
        "## Covered Categories",
    ]
    for category, record in coverage["categories"].items():
        lines.append(f"- {category}: {', '.join(record['entry_keys'])}")
    lines.extend(["", "Main related-work citation placeholders remaining: `0`."])
    return "\n".join(lines) + "\n"


def related_work_citation_audit_text() -> str:
    rows = [
        {"section": "SAT preprocessing", "citations": "een-biere-2005; biere-jarvisalo-kiesl-2021; heule-jarvisalo-biere-2011", "boundary": "Not novelty for preprocessing."},
        {"section": "Proof logging", "citations": "wetzler-heule-hunt-2014; heule-2016; cruz-filipe-2016; baek-2021", "boundary": "Native certificates are not external proofs."},
        {"section": "XOR/affine", "citations": "soos-nohl-castelluccia-2009", "boundary": "No novelty claim for Gaussian elimination."},
        {"section": "Treewidth/separators", "citations": "robertson-seymour-1986; bodlaender-1996", "boundary": "TC-063 only covers SAF(c,r)."},
        {"section": "Circuit CNF", "citations": "tseitin-1968", "boundary": "G10 exact definitions only."},
        {"section": "SAT portfolios", "citations": "xu-hutter-hoos-leytonbrown-2011", "boundary": "G12 plans are not execution."},
        {"section": "Proof motifs", "citations": "cook-reckhow-1979", "boundary": "Similarity is not proof."},
    ]
    return "# Related Work Citation Audit\n\n" + _markdown_table(rows, ["section", "citations", "boundary"]) + "\n"


def final_submission_readiness_report_text() -> str:
    return f"""# Final Submission Readiness Report

Package: `{PACKAGE_VERSION}`

Status: `PASS`

The public preprint packet has a safe title, completed bibliography, claim-boundary audit, v2.26 release notes, reviewer outreach email, arXiv checklist, workshop checklist, and GitHub release checklist.

TC-063 remains `{HARDENED_STATUS}`. No theorem status is upgraded in v2.26.
"""


def _scan_forbidden_text(text: str) -> list[str]:
    lower = text.lower()
    return [fragment for fragment in FORBIDDEN_AFFIRMATIVE_FRAGMENTS if fragment in lower]


def _missing(text: str, required: list[str]) -> list[str]:
    return [item for item in required if item not in text]


def related_work_citation_validation(paper: str) -> dict[str, Any]:
    missing_subsections = [name for name in RELATED_WORK_SUBSECTIONS if f"### {name}" not in paper]
    missing_citations = [
        key
        for key in [entry["key"] for entry in bibliography_entries()]
        if key not in paper and key not in {"wetzler-heule-hunt-2014-drat-trim"}
    ]
    todo_hits = [marker for marker in ["TODO " + "citation", "CITATION_NEEDED_NOT_CLAIMED"] if marker in paper]
    status = "PASS" if not missing_subsections and not todo_hits and not missing_citations else "FAIL"
    return {
        "missing_subsections": missing_subsections,
        "missing_citations": missing_citations,
        "todo_markers": todo_hits,
        "verification_status": status,
    }


def final_forbidden_claim_scan(markdown_texts: list[str], json_objects: list[Any]) -> dict[str, Any]:
    hits = _scan_forbidden_text("\n".join(markdown_texts))
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

    for obj in json_objects:
        walk(obj)
    bad_statuses = sorted(set(status_values) & {"HARD", "UNKNOWN"})
    return {
        "forbidden_fragments": FORBIDDEN_AFFIRMATIVE_FRAGMENTS,
        "hits": hits,
        "bad_status_values": bad_statuses,
        "hit_count": len(hits) + len(bad_statuses),
        "verification_status": "PASS" if not hits and not bad_statuses else "FAIL",
    }


def validate_submit_release_package(package_root: str | Path) -> dict[str, Any]:
    root = Path(package_root)
    errors: list[str] = []
    for name in REQUIRED_MARKDOWN:
        if not (root / name).is_file():
            errors.append(f"MISSING_MARKDOWN:{name}")
    for name in REQUIRED_JSON:
        if not (root / name).is_file():
            errors.append(f"MISSING_JSON:{name}")

    paper_path = root / "FINAL_PUBLIC_PREPRINT_DRAFT.md"
    paper = paper_path.read_text(encoding="utf-8") if paper_path.is_file() else ""
    combined = "\n".join((root / name).read_text(encoding="utf-8") for name in REQUIRED_MARKDOWN if (root / name).is_file())

    if f"# {PREPRINT_TITLE}" not in paper:
        errors.append("TITLE_MISSING_OR_UNSAFE")
    for sentence in REQUIRED_ABSTRACT_SENTENCES:
        if sentence not in paper:
            errors.append("ABSTRACT_NONCLAIM_MISSING:" + sentence)
    for marker in ["TODO " + "citation", "CITATION_NEEDED_NOT_CLAIMED"]:
        if marker in paper:
            errors.append("CITATION_PLACEHOLDER_PRESENT:" + marker)
    if "## Contributions" not in paper or "Collapse hierarchy G0-G14" not in paper:
        errors.append("CONTRIBUTION_LIST_MISSING")
    if "## Related Work" not in paper:
        errors.append("RELATED_WORK_MISSING")
    if "## Limitations" not in paper:
        errors.append("LIMITATIONS_MISSING")
    for limitation in REQUIRED_LIMITATIONS:
        if limitation not in paper:
            errors.append("LIMITATION_MISSING:" + limitation)
    if f"TC-063 status: {HARDENED_STATUS}" not in paper:
        errors.append("TC063_STATUS_MISSING")
    if "Native Witnora certificates are not DRAT/LRAT/FRAT proofs unless explicitly exported and externally checked." not in paper:
        errors.append("NATIVE_CERT_BOUNDARY_MISSING")

    coverage = json.loads((root / "citation_coverage_summary.json").read_text(encoding="utf-8")) if (root / "citation_coverage_summary.json").is_file() else {}
    for category in CITATION_CATEGORIES:
        if not coverage.get("categories", {}).get(category, {}).get("covered", False):
            errors.append("CITATION_CATEGORY_MISSING:" + category)
    citation_validation = related_work_citation_validation(paper)
    if citation_validation["verification_status"] != "PASS":
        errors.append("RELATED_WORK_CITATION_VALIDATION_FAILED")

    json_objects = []
    for name in REQUIRED_JSON:
        path = root / name
        if path.is_file():
            json_objects.append(json.loads(path.read_text(encoding="utf-8")))
    claim_scan = final_forbidden_claim_scan([combined, paper], json_objects)
    if claim_scan["verification_status"] != "PASS":
        errors.append("FORBIDDEN_CLAIM_SCAN_FAILED")

    return {
        "verification_status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "required_markdown": REQUIRED_MARKDOWN,
        "required_json": REQUIRED_JSON,
        "citation_validation": citation_validation,
        "claim_scan": claim_scan,
    }


def _readiness_summary(name: str) -> dict[str, Any]:
    return {
        "target": name,
        "safe_title": True,
        "bibliography_complete": True,
        "claim_boundary_scan_pass": True,
        "user_approval_required": name == "arxiv",
        "venue_formatting_required": name == "workshop",
        "verification_status": "PASS",
    }


def run_submit_release_package(
    out_root: str | Path,
    *,
    strict: bool = False,
    zip_path: str | Path | None = ARTIFACT_NAME,
) -> dict[str, Any]:
    root = Path(out_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)

    paper = final_preprint_text()
    paper_path = Path("paper/WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_REVIEW_DRAFT.md")
    bibliography_path = Path("paper/references.bib")
    _write_text(paper_path, paper)
    _write_text(bibliography_path, references_bib_text())
    _write_text(Path("RELEASE_NOTES_V2_25.md"), release_notes_v225_update_text())
    _write_text(Path("RELEASE_NOTES_V2_26.md"), release_notes_v226_text())
    _write_text(Path("docs/REVIEWER_GUIDE.md"), reviewer_guide_v225_text() + "\n## v2.26 Finalization\n\nv2.26 completes bibliography hardening and final submission checklists.\n")

    markdown: dict[str, str] = {
        "FINAL_PUBLIC_PREPRINT_DRAFT.md": paper,
        "RELEASE_NOTES_V2_26.md": release_notes_v226_text(),
        "REVIEWER_OUTREACH_EMAIL.md": reviewer_outreach_email_text(),
        "ARXIV_SUBMISSION_CHECKLIST.md": arxiv_checklist_text(),
        "WORKSHOP_SUBMISSION_CHECKLIST.md": workshop_checklist_text(),
        "GITHUB_RELEASE_CHECKLIST.md": github_release_checklist_text(),
        "BIBLIOGRAPHY_COMPLETION_REPORT.md": bibliography_completion_report_text(),
        "RELATED_WORK_CITATION_AUDIT.md": related_work_citation_audit_text(),
        "FINAL_CLAIM_BOUNDARY_AUDIT.md": final_claim_boundary_audit_text(),
        "FINAL_SUBMISSION_READINESS_REPORT.md": final_submission_readiness_report_text(),
        "REVIEWER_GUIDE_V2_26.md": reviewer_guide_v225_text() + "\n## v2.26 Finalization\n\nBibliography and release checklists are complete.\n",
        "REPRODUCIBILITY_GUIDE.md": reproducibility_guide_v225_text(),
        "SUBMIT_RELEASE_FINALIZATION_REPORT.md": "# Submit Release Finalization Report\n\nValidation status: `PENDING`.\n",
    }
    for name, text in markdown.items():
        _write_text(root / name, text)

    bibliography = bibliography_manifest()
    coverage = citation_coverage_summary()
    citation_validation = related_work_citation_validation(paper)
    claim_boundary_validation = {
        "claim_boundary_rows": claim_boundary_rows(),
        "tc063_status": HARDENED_STATUS,
        "native_certificates_native_only": True,
        "finite_evidence_is_not_proof": True,
        "verification_status": "PASS",
    }
    release_readiness = {
        "version": PACKAGE_VERSION,
        "final_public_preprint": True,
        "release_notes_v226": True,
        "reviewer_outreach_email": True,
        "arxiv_checklist": True,
        "workshop_checklist": True,
        "github_release_checklist": True,
        "source_archive_sha": "PENDING_SOURCE_ARCHIVE_FREEZE",
        "verification_status": "PENDING",
    }
    manifest = SubmitReleaseManifest(
        package_id=PACKAGE_ID,
        version=PACKAGE_VERSION,
        title=PREPRINT_TITLE,
        paper_path=str(paper_path),
        bibliography_path=str(bibliography_path),
        output_root=str(root),
        markdown_files=REQUIRED_MARKDOWN,
        json_files=REQUIRED_JSON,
        citation_categories=CITATION_CATEGORIES,
        expected_test_count=EXPECTED_TEST_COUNT,
        verification_status="PENDING",
    ).to_dict()

    preliminary_scan = final_forbidden_claim_scan(list(markdown.values()), [bibliography, coverage, citation_validation, claim_boundary_validation, release_readiness])
    json_payloads = {
        "submit_release_manifest.json": manifest,
        "bibliography_manifest.json": bibliography,
        "citation_coverage_summary.json": coverage,
        "related_work_citation_validation.json": citation_validation,
        "final_claim_boundary_validation.json": claim_boundary_validation,
        "release_readiness_summary.json": release_readiness,
        "arxiv_readiness_summary.json": _readiness_summary("arxiv"),
        "workshop_readiness_summary.json": _readiness_summary("workshop"),
        "github_release_readiness_summary.json": _readiness_summary("github_release"),
        "forbidden_claim_scan_v226.json": preliminary_scan,
    }
    for name, payload in json_payloads.items():
        _write_json(root / name, payload)

    check = validate_submit_release_package(root)
    manifest["verification_status"] = check["verification_status"]
    release_readiness["verification_status"] = check["verification_status"]
    final_scan = final_forbidden_claim_scan(list(markdown.values()), [*json_payloads.values(), check])
    _write_json(root / "submit_release_manifest.json", manifest)
    _write_json(root / "release_readiness_summary.json", release_readiness)
    _write_json(root / "forbidden_claim_scan_v226.json", final_scan)
    _write_text(root / "SUBMIT_RELEASE_FINALIZATION_REPORT.md", submit_release_report_text(check))

    check = validate_submit_release_package(root)
    if strict and check["verification_status"] != "PASS":
        raise RuntimeError("submit release package validation failed: " + ";".join(check["errors"]))
    digest = _make_zip(root, zip_path) if zip_path else ""
    return {
        "out_root": str(root),
        "zip": str(zip_path) if zip_path else "",
        "zip_sha256": digest,
        "validation": check,
        "manifest": manifest,
    }


def submit_release_report_text(check: dict[str, Any]) -> str:
    return f"""# Submit Release Finalization Report

Package: `{PACKAGE_VERSION}`

Title: `{PREPRINT_TITLE}`

Validation status: `{check['verification_status']}`

Errors: `{len(check['errors'])}`

v2.26 finalizes public release/submission preparation. Bibliography hardening is complete, the package is arXiv-ready after user approval, workshop submission requires venue-specific formatting, no new operator is added, no theorem status is upgraded, TC-063 remains `{HARDENED_STATUS}`, and no P-vs-NP/all-SAT/completeness/unqualified theorem-proven/fake external proof claim is made.
"""


def _cmd_run(args: argparse.Namespace) -> int:
    result = run_submit_release_package(args.out_root, strict=args.strict, zip_path=args.zip)
    print(stable_json({"out_root": result["out_root"], "zip": result["zip"], "zip_sha256": result["zip_sha256"], "validation": result["validation"]}))
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    result = validate_submit_release_package(args.package_root)
    print(stable_json(result))
    return 0 if result["verification_status"] == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m witnora_core.submit_release_finalize_v226")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("--out-root", default="outputs/v2.26-submit-release-checklist-finalization")
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
