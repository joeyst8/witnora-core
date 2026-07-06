"""Restricted G0 width/treewidth vs G1 XOR strictness proof kernel.

v2.9 intentionally targets a restricted theorem object. It does not claim a
lower bound against every G0_BASE route. The certified finite records here show
that a bounded-width subroute rejects selected formulas while G1 exact XOR
reasoning accepts them with a native GF(2) certificate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .cnf import CNFFormula, formula_satisfied
from .primal import graph_edges, primal_graph
from .treewidth_audit import bounded_elimination_order_audit
from .xor import (
    XOR_SAT,
    XOR_UNSAT,
    canonical_xor_cnf_clauses,
    detect_cnf_xor_patterns,
    reconstruct_assignment,
    solve_xor_system_gaussian,
    verify_xor_assignment,
)


WIDTH_OBSTRUCTION_VERIFIED = "WIDTH_OBSTRUCTION_VERIFIED"
WIDTH_OBSTRUCTION_NOT_VERIFIED = "WIDTH_OBSTRUCTION_NOT_VERIFIED"
WIDTH_EXCEEDS_CAP_VERIFIED = "WIDTH_EXCEEDS_CAP_VERIFIED"
WIDTH_OBSTRUCTION_FAILED = "WIDTH_OBSTRUCTION_FAILED"
WIDTH_NOT_CERTIFIED = "WIDTH_NOT_CERTIFIED"
RESTRICTED_G0_WIDTH_ROUTE_REJECTED = "RESTRICTED_G0_WIDTH_ROUTE_REJECTED"
G1_XOR_UPPER_BOUND_VERIFIED = "G1_XOR_UPPER_BOUND_VERIFIED"
RESTRICTED_STRICTNESS_PROOF_SKETCH = "RESTRICTED_STRICTNESS_PROOF_SKETCH"
RESTRICTED_STRICTNESS_THEOREM_CANDIDATE = "RESTRICTED_STRICTNESS_THEOREM_CANDIDATE"
PROVEN_RESTRICTED_THEOREM = "PROVEN_RESTRICTED_THEOREM"
FAILED_PROOF_OBLIGATION = "FAILED_PROOF_OBLIGATION"
FULL_G0_STRICTNESS_NOT_CLAIMED = "FULL_G0_STRICTNESS_NOT_CLAIMED"
SCALABLE_FAMILY_PROOF_OBLIGATION = "SCALABLE_FAMILY_PROOF_OBLIGATION"
FORMAL_PROOF_SKETCH = "FORMAL_PROOF_SKETCH"
EMPIRICAL_EVIDENCE_NOT_THEOREM = "EMPIRICAL_EVIDENCE_NOT_THEOREM"


@dataclass(frozen=True)
class WidthObstructionCertificate:
    instance_id: str
    formula_hash: str
    graph_type: str
    width_parameter: str
    cap_c: int
    certified_lower_bound: int | None
    exact_or_bounded_method: str
    obstruction_status: str
    checker_status: str
    assumptions: list[str]
    num_vars: int
    num_clauses: int
    primal_edges: int
    clique_lower_bound: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class XorUpperBoundCertificate:
    instance_id: str
    formula_hash: str
    extracted_equations: list[dict[str, Any]]
    extraction_verified: bool
    elimination_certificate: dict[str, Any]
    sat_or_unsat_result: str
    checker_status: str
    certification_level: str
    proof_or_native_certificate_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StrictnessProofRecord:
    theorem_id: str
    restricted_prior_grammar: str
    stronger_grammar: str
    witness_family: str
    witness_instance: str
    width_obstruction_certificate: dict[str, Any]
    xor_upper_bound_certificate: dict[str, Any]
    strictness_status: str
    forbidden_interpretations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stable_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(data) + "\n", encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def make_zip(root: Path | str, zip_path: Path | str) -> str:
    root = Path(root)
    zip_path = Path(zip_path)
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(root).as_posix())
    return sha256_file(zip_path)


def _xor_formula(equations: Iterable[tuple[Iterable[int], int]]) -> CNFFormula:
    clauses: list[tuple[int, ...]] = []
    for variables, rhs in equations:
        clauses.extend(sorted(canonical_xor_cnf_clauses(tuple(variables), rhs)))
    return CNFFormula.from_raw_clauses(clauses)


def strictness_witness_formula(instance_id: str) -> tuple[str, CNFFormula, str]:
    """Return finite strictness witnesses with exact high-width XOR encodings."""

    witness_equations: dict[str, tuple[str, list[tuple[tuple[int, ...], int]], str]] = {
        "tseitin_10": (
            "tseitin",
            [
                ((1, 2, 3, 4, 5, 6), 0),
                ((1, 2, 3, 4, 5, 7), 0),
                ((6, 7), 1),
            ],
            "finite Tseitin-style affine obstruction fixture; exact full-CNF XOR groups, not a scalable expander theorem",
        ),
        "tseitin_12": (
            "tseitin",
            [
                ((1, 2, 3, 4, 5, 6), 0),
                ((4, 5, 6, 7, 8, 9), 0),
                ((7, 8, 9, 10, 11, 12), 0),
                ((1, 2, 3, 10, 11, 12), 1),
            ],
            "finite Tseitin-style width fixture with chained arity-6 affine constraints; not a scalable family theorem",
        ),
        "tseitin_14": (
            "tseitin",
            [
                ((1, 2, 3, 4, 5, 6), 0),
                ((4, 5, 6, 7, 8, 9), 0),
                ((7, 8, 9, 10, 11, 12), 0),
                ((1, 2, 3, 10, 11, 12), 1),
                ((9, 10, 11, 12, 13, 14), 0),
            ],
            "finite Tseitin-style witness with additional exact affine component; not an expander lower-bound theorem",
        ),
        "xor_chain_unsat_n5": (
            "xor-chain",
            [
                ((1, 2, 3, 4, 5, 6), 0),
                ((1, 2, 3, 4, 5, 7), 0),
                ((6, 7), 1),
            ],
            "finite high-width XOR-chain strictness fixture for G0_WIDTH_C vs G1_XOR",
        ),
        "xor_chain_unsat_n7": (
            "xor-chain",
            [
                ((1, 2, 3, 4, 5, 6), 0),
                ((2, 3, 4, 5, 6, 7), 0),
                ((1, 7), 1),
            ],
            "finite arity-6 XOR-chain witness with a checked native GF(2) contradiction",
        ),
        "xor_chain_unsat_n9": (
            "xor-chain",
            [
                ((1, 2, 3, 4, 5, 6), 0),
                ((4, 5, 6, 7, 8, 9), 0),
                ((1, 2, 3, 7, 8, 9), 1),
            ],
            "finite arity-6 overlapping XOR-chain witness with exact width obstruction",
        ),
    }
    if instance_id in witness_equations:
        family, equations, description = witness_equations[instance_id]
        return (
            family,
            _xor_formula(equations),
            description,
        )
    raise ValueError(f"unsupported v2.9 strictness witness: {instance_id}")


def restricted_grammar_definitions(cap_c: int) -> list[dict[str, Any]]:
    return [
        {
            "name": "G0_WIDTH_C",
            "cap_c": cap_c,
            "operators": ["bounded treewidth terminal", "VE width cap c", "exact width obstruction checker"],
            "disabled": ["XOR", "symmetry", "cardinality", "orbit-capacity", "affine residue over cap", "proof motif"],
            "claim_boundary": "restricted width/treewidth subroute only; not full G0_BASE",
        },
        {
            "name": "G0_WIDTH_C_WITH_SAFE_PREPROCESS",
            "cap_c": cap_c,
            "operators": ["G0_WIDTH_C plus only preprocessors proven stable for the witness family"],
            "status": "not used for theorem claim in v2.9",
            "claim_boundary": "safe preprocessing is a proof obligation unless separately proven.",
        },
        {
            "name": "G1_XOR_FOR_STRICTNESS",
            "cap_c": cap_c,
            "operators": ["G0_WIDTH_C", "exact XOR extraction", "GF(2) elimination", "native XOR certificate"],
            "claim_boundary": "upper-bound route only; not a full hierarchy strictness theorem.",
        },
    ]


def build_width_obstruction_certificate(formula: CNFFormula, *, instance_id: str, cap_c: int) -> WidthObstructionCertificate:
    graph = primal_graph(formula)
    order = bounded_elimination_order_audit(graph, cap_c, timeout_seconds=30.0)
    clique_lower_bound = max((len(clause.variables) - 1 for clause in formula.clauses), default=0)
    verified = order is None and clique_lower_bound > cap_c
    if verified:
        obstruction_status = WIDTH_EXCEEDS_CAP_VERIFIED
        checker_status = WIDTH_OBSTRUCTION_VERIFIED
        certified_lower_bound: int | None = clique_lower_bound
    elif order is None:
        obstruction_status = WIDTH_EXCEEDS_CAP_VERIFIED
        checker_status = WIDTH_OBSTRUCTION_VERIFIED
        certified_lower_bound = cap_c + 1
    else:
        obstruction_status = WIDTH_OBSTRUCTION_FAILED
        checker_status = WIDTH_OBSTRUCTION_NOT_VERIFIED
        certified_lower_bound = None
    return WidthObstructionCertificate(
        instance_id=instance_id,
        formula_hash=formula.formula_hash,
        graph_type="PRIMAL",
        width_parameter="INDUCED_WIDTH",
        cap_c=cap_c,
        certified_lower_bound=certified_lower_bound,
        exact_or_bounded_method="EXHAUSTIVE_BOUNDED_ELIMINATION_SEARCH_PLUS_CLIQUE_LOWER_BOUND",
        obstruction_status=obstruction_status,
        checker_status=checker_status,
        assumptions=[
            "Only the restricted G0_WIDTH_C bounded-width route is rejected.",
            "No claim is made about UP, PLE, SUB, BCE, components, 2SAT, or full G0_BASE non-collapse.",
            "Clique lower bound and exhaustive no-order-under-cap search are finite-instance evidence.",
        ],
        num_vars=formula.num_vars,
        num_clauses=formula.num_clauses,
        primal_edges=len(graph_edges(graph)),
        clique_lower_bound=clique_lower_bound,
    )


def build_xor_upper_bound_certificate(formula: CNFFormula, *, instance_id: str, max_k: int = 6) -> XorUpperBoundCertificate:
    detected = detect_cnf_xor_patterns(formula, max_k=max_k)
    solution = solve_xor_system_gaussian(detected)
    extraction_verified = bool(detected.equations) and all(eq.exact_full_encoding and eq.safe_use for eq in detected.equations)
    status = str(solution.get("status"))
    checker_ok = extraction_verified and status in {XOR_SAT, XOR_UNSAT}
    if status == XOR_SAT:
        assignment = reconstruct_assignment(solution)
        checker_ok = checker_ok and verify_xor_assignment(detected, assignment) and formula_satisfied(formula, assignment)
        certification_level = "XOR_SAT_NATIVE_CERTIFIED"
    elif status == XOR_UNSAT:
        checker_ok = checker_ok and bool(solution.get("contradiction"))
        certification_level = "XOR_UNSAT_NATIVE_CERTIFIED"
    else:
        certification_level = "XOR_CERTIFICATE_FAILED"
    return XorUpperBoundCertificate(
        instance_id=instance_id,
        formula_hash=formula.formula_hash,
        extracted_equations=[eq.to_dict() for eq in detected.equations],
        extraction_verified=extraction_verified,
        elimination_certificate={
            "status": status,
            "rank": solution.get("rank", 0),
            "pivot_variables": solution.get("pivot_variables", []),
            "contradiction": solution.get("contradiction"),
            "elimination_trace": solution.get("elimination_trace", []),
        },
        sat_or_unsat_result=status,
        checker_status=G1_XOR_UPPER_BOUND_VERIFIED if checker_ok else "G1_XOR_UPPER_BOUND_NOT_VERIFIED",
        certification_level=certification_level,
        proof_or_native_certificate_path="native_xor_elimination_certificate_embedded",
    )


def build_strictness_record(
    *,
    family: str,
    instance_id: str,
    width_certificate: WidthObstructionCertificate,
    xor_certificate: XorUpperBoundCertificate,
) -> StrictnessProofRecord:
    width_ok = width_certificate.checker_status == WIDTH_OBSTRUCTION_VERIFIED
    xor_ok = xor_certificate.checker_status == G1_XOR_UPPER_BOUND_VERIFIED
    strictness_status = RESTRICTED_STRICTNESS_PROOF_SKETCH if width_ok and xor_ok else FAILED_PROOF_OBLIGATION
    return StrictnessProofRecord(
        theorem_id="RESTRICTED_G0_WIDTH_C_VS_G1_XOR",
        restricted_prior_grammar="G0_WIDTH_C",
        stronger_grammar="G1_XOR_FOR_STRICTNESS",
        witness_family=family,
        witness_instance=instance_id,
        width_obstruction_certificate=width_certificate.to_dict(),
        xor_upper_bound_certificate=xor_certificate.to_dict(),
        strictness_status=strictness_status,
        forbidden_interpretations=[
            FULL_G0_STRICTNESS_NOT_CLAIMED,
            "No full G0_BASE strictness theorem is claimed.",
            "No scalable Tseitin/expander theorem is marked proven.",
            "No hierarchy completeness claim.",
            "No P vs NP progress claim.",
            "Native XOR certificates are not DRAT unless a DRAT proof is exported and checked.",
        ],
    )


def theorem_candidate_payload(cap_c: int, records: list[StrictnessProofRecord]) -> dict[str, Any]:
    return {
        "theorem_id": "RESTRICTED_G0_WIDTH_C_VS_G1_XOR",
        "cap_c": cap_c,
        "level_1": {
            "name": "WIDTH_OBSTRUCTION_THEOREM",
            "status": FORMAL_PROOF_SKETCH,
            "statement": "If exhaustive bounded-width checking verifies no elimination ordering of width <= c for F, then F is rejected by the restricted G0_WIDTH_C route.",
        },
        "level_2": {
            "name": "XOR_UPPER_BOUND_THEOREM",
            "status": FORMAL_PROOF_SKETCH,
            "statement": "If exact XOR equations are extracted and the GF(2) native certificate verifies, then F is accepted by G1_XOR_FOR_STRICTNESS.",
        },
        "level_3": {
            "name": "RESTRICTED_G0_G1_STRICTNESS_CANDIDATE",
            "status": FORMAL_PROOF_SKETCH,
            "statement": "There exists a finite witnessed F rejected by G0_WIDTH_C due to width obstruction and accepted by G1_XOR due to verified XOR certificate.",
        },
        "records": [record.to_dict() for record in records],
        "full_g0_base_status": FULL_G0_STRICTNESS_NOT_CLAIMED,
        "scalable_family_status": SCALABLE_FAMILY_PROOF_OBLIGATION,
        "forbidden_interpretations": [
            "not full G0_BASE strictness",
            "not hierarchy completeness",
            "not P vs NP progress",
            "not a lower bound against all G0 operators",
        ],
    }


def strictness_report(
    *,
    cap_c: int,
    records: list[StrictnessProofRecord],
    theorem_candidate: dict[str, Any],
) -> str:
    lines = [
        "# Restricted G0-vs-G1 Strictness Proof Kernel",
        "",
        "v2.9 attempts the first restricted strictness proof object: `G0_WIDTH_C` versus `G1_XOR_FOR_STRICTNESS`.",
        "",
        "This is a restricted theorem candidate/proof sketch unless explicitly marked proven.",
        "This does not prove full G0_BASE strictness.",
        "This does not prove P vs NP.",
        "This does not prove hierarchy completeness.",
        "",
        f"- Cap c: `{cap_c}`",
        f"- Full G0 status: `{theorem_candidate['full_g0_base_status']}`",
        f"- Scalable family status: `{theorem_candidate['scalable_family_status']}`",
        "",
        "## Restricted Grammars",
        "",
        "`G0_WIDTH_C` contains the bounded-width/treewidth route only. `G1_XOR_FOR_STRICTNESS` adds exact XOR extraction and native GF(2) elimination.",
        "",
        "## Finite Witness Records",
        "",
    ]
    for record in records:
        width = record.width_obstruction_certificate
        xor = record.xor_upper_bound_certificate
        lines.extend(
            [
                f"### {record.witness_instance}",
                "",
                f"- Family: `{record.witness_family}`",
                f"- Width obstruction: `{width['checker_status']}` with lower bound `{width['certified_lower_bound']}`",
                f"- G1 XOR upper bound: `{xor['checker_status']}` with result `{xor['sat_or_unsat_result']}`",
                f"- Strictness status: `{record.strictness_status}`",
                "",
            ]
        )
    lines.extend(
        [
            "## What Is Proven",
            "",
            "The finite records prove only the checked bounded-width rejection and checked G1 XOR acceptance for the generated witnesses.",
            "",
            "## What Is Not Proven",
            "",
            "- No full G0_BASE lower bound.",
            "- No scalable Tseitin expander theorem.",
            "- No hierarchy completeness theorem.",
            "- No P vs NP progress.",
            "- No native-certificate-as-DRAT claim.",
            "",
            "## Proof Obligations Remaining",
            "",
            "- Show every full G0_BASE operator cannot lower the selected family into a collapsible form.",
            "- Replace finite bounded-width evidence with scalable graph-theoretic proof for expander/Tseitin families.",
            "- Add DRAT bridges only when proof export against the original CNF is checked.",
            "",
        ]
    )
    return "\n".join(lines)


def proof_obligation_updates(cap_c: int) -> list[dict[str, Any]]:
    return [
        {
            "obligation_id": "V29-PO-001",
            "type": "WIDTH_TREEWIDTH_FINITE_AUDIT",
            "status": "SATISFIED_BY_EXACT_FINITE_CHECK",
            "cap_c": cap_c,
            "missing_work": "Scale from finite fixture to graph-family proof.",
        },
        {
            "obligation_id": "V29-PO-002",
            "type": "FULL_G0_BASE_NON_COLLAPSE",
            "status": "OPEN",
            "missing_work": "Prove UP, PLE, SUB, BCE, components, 2SAT, and VE/preprocessing cannot evade the width obstruction for the selected family.",
        },
        {
            "obligation_id": "V29-PO-003",
            "type": "SCALABLE_TSEITIN_FAMILY",
            "status": SCALABLE_FAMILY_PROOF_OBLIGATION,
            "missing_work": "Supply graph-theoretic treewidth/proof-complexity proof before marking a scalable family theorem proven.",
        },
    ]


def run_strictness_proof(
    *,
    instances: Iterable[str] = ("tseitin_10", "xor_chain_unsat_n5"),
    cap_c: int = 4,
    out_root: str | Path = "outputs/v2.9-restricted-g0-g1-strictness",
    strict: bool = False,
    zip_path: str | Path = "witnora-core-v2.9-restricted-g0-g1-strictness.zip",
) -> dict[str, Any]:
    root = Path(out_root)
    root.mkdir(parents=True, exist_ok=True)
    width_certs: list[dict[str, Any]] = []
    xor_certs: list[dict[str, Any]] = []
    records: list[StrictnessProofRecord] = []
    audit_summary: list[dict[str, Any]] = []
    for instance_id in instances:
        family, formula, description = strictness_witness_formula(instance_id)
        width = build_width_obstruction_certificate(formula, instance_id=instance_id, cap_c=cap_c)
        xor = build_xor_upper_bound_certificate(formula, instance_id=instance_id)
        record = build_strictness_record(family=family, instance_id=instance_id, width_certificate=width, xor_certificate=xor)
        width_certs.append(width.to_dict() | {"description": description})
        xor_certs.append(xor.to_dict())
        records.append(record)
        audit_summary.append(
            {
                "instance_id": instance_id,
                "cap_c": cap_c,
                "num_vars": formula.num_vars,
                "num_clauses": formula.num_clauses,
                "width_checker_status": width.checker_status,
                "certified_lower_bound": width.certified_lower_bound,
                "restricted_route_result": RESTRICTED_G0_WIDTH_ROUTE_REJECTED if width.checker_status == WIDTH_OBSTRUCTION_VERIFIED else FAILED_PROOF_OBLIGATION,
            }
        )
    theorem_candidate = theorem_candidate_payload(cap_c, records)
    payloads = {
        "width_obstruction_certificates.json": {"width_obstruction_certificates": width_certs},
        "xor_upper_bound_certificates.json": {"xor_upper_bound_certificates": xor_certs},
        "strictness_proof_records.json": {"strictness_proof_records": [record.to_dict() for record in records]},
        "exact_width_audit_summary.json": {"exact_width_audit_summary": audit_summary},
        "restricted_g0_g1_theorem_candidate.json": theorem_candidate,
        "proof_obligation_updates.json": {"proof_obligation_updates": proof_obligation_updates(cap_c)},
        "restricted_grammar_definitions.json": {"restricted_grammar_definitions": restricted_grammar_definitions(cap_c)},
    }
    for name, payload in payloads.items():
        _write_json(root / name, payload)
    (root / "RESTRICTED_G0_G1_STRICTNESS_REPORT.md").write_text(
        strictness_report(cap_c=cap_c, records=records, theorem_candidate=theorem_candidate),
        encoding="utf-8",
        newline="\n",
    )
    digest = make_zip(root, zip_path) if zip_path else ""
    return {
        "out_root": str(root),
        "zip": str(zip_path) if zip_path else "",
        "zip_sha256": digest,
        "strict": strict,
        "width_obstruction_certificates": width_certs,
        "xor_upper_bound_certificates": xor_certs,
        "strictness_proof_records": [record.to_dict() for record in records],
        "exact_width_audit_summary": audit_summary,
        "restricted_g0_g1_theorem_candidate": theorem_candidate,
        "proof_obligation_updates": proof_obligation_updates(cap_c),
        "restricted_grammar_definitions": restricted_grammar_definitions(cap_c),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Restricted G0 width/treewidth vs G1 XOR strictness proof kernel")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--instances", nargs="+", default=["tseitin_10", "xor_chain_unsat_n5"])
    run.add_argument("--cap-c", type=int, default=4)
    run.add_argument("--out-root", default="outputs/v2.9-restricted-g0-g1-strictness")
    run.add_argument("--strict", action="store_true")
    run.add_argument("--zip", default="witnora-core-v2.9-restricted-g0-g1-strictness.zip")
    args = parser.parse_args(argv)
    if args.command == "run":
        result = run_strictness_proof(
            instances=args.instances,
            cap_c=args.cap_c,
            out_root=args.out_root,
            strict=args.strict,
            zip_path=args.zip,
        )
        print(
            stable_json(
                {
                    "out_root": result["out_root"],
                    "zip": result["zip"],
                    "zip_sha256": result["zip_sha256"],
                    "summary": {
                        "records": len(result["strictness_proof_records"]),
                        "cap_c": args.cap_c,
                        "full_g0_claim": FULL_G0_STRICTNESS_NOT_CLAIMED,
                        "scalable_family_status": SCALABLE_FAMILY_PROOF_OBLIGATION,
                    },
                }
            )
        )
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
