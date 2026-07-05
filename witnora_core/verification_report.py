"""Reusable verification-report and trust-card helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from .claim_boundary import scan_text_for_claim_boundary
from .proof import verify_certificate_bundle

VERDICT_VERIFIED = "VERIFIED"
VERDICT_PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
VERDICT_NOT_VERIFIED = "NOT_VERIFIED"
VERDICT_OVERCLAIM = "OVERCLAIM"

DEFAULT_ALLOWED_CLAIMS = [
    "Witnora reports only scoped certification levels supported by evidence.",
    "Externally verified UNSAT requires an accepted proof artifact and checker record.",
    "Native-only results are separated from externally verified results.",
]

DEFAULT_FORBIDDEN_CLAIMS = [
    "parity support",
    "broad XOR extraction",
    "CryptoMiniSat-style extraction",
    "competitive SAT solving",
    "industrial benchmark performance",
    "full DRAT/RAT/LRAT/FRAT support",
    "P vs NP progress",
    "HARD or UNKNOWN status claims",
]


@dataclass
class VerificationReport:
    claim: str
    logical_status: str
    discovery_route: str
    certification_level: str
    public_category: str
    evidence_files: list[str] = field(default_factory=list)
    external_checkers: list[str] = field(default_factory=list)
    checker_results: list[dict[str, Any]] = field(default_factory=list)
    artifact_hashes: dict[str, str] = field(default_factory=dict)
    reproducibility_status: str = "NOT_ASSESSED"
    allowed_claims: list[str] = field(default_factory=lambda: list(DEFAULT_ALLOWED_CLAIMS))
    forbidden_claims: list[str] = field(default_factory=lambda: list(DEFAULT_FORBIDDEN_CLAIMS))
    risk_flags: list[str] = field(default_factory=list)
    verdict: str = VERDICT_NOT_VERIFIED

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "logical_status": self.logical_status,
            "discovery_route": self.discovery_route,
            "certification_level": self.certification_level,
            "public_category": self.public_category,
            "evidence_files": self.evidence_files,
            "external_checkers": self.external_checkers,
            "checker_results": self.checker_results,
            "artifact_hashes": self.artifact_hashes,
            "reproducibility_status": self.reproducibility_status,
            "allowed_claims": self.allowed_claims,
            "forbidden_claims": self.forbidden_claims,
            "risk_flags": self.risk_flags,
            "verdict": self.verdict,
        }


def stable_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def sha256_file(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def render_verification_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Witnora Verification Report",
        "",
        "## Claim Being Audited",
        "",
        str(report.get("claim", "")),
        "",
        "## Evidence Provided",
        "",
    ]
    for item in report.get("evidence_files", []):
        lines.append(f"- `{item}`")
    if not report.get("evidence_files"):
        lines.append("- none")
    lines.extend(["", "## Checks Performed", ""])
    for result in report.get("checker_results", []):
        name = result.get("checker", result.get("check", "checker"))
        passed = result.get("passed", result.get("verified", False))
        lines.append(f"- `{name}`: {'pass' if passed else 'fail'}")
    lines.extend(["", "## External Verification", ""])
    for checker in report.get("external_checkers", []):
        lines.append(f"- `{checker}`")
    if not report.get("external_checkers"):
        lines.append("- none recorded")
    lines.extend(["", "## Artifact Hashes", ""])
    for name, digest in sorted(report.get("artifact_hashes", {}).items()):
        lines.append(f"- `{name}`: `{digest}`")
    lines.extend(["", "## Certification Level", "", f"`{report.get('certification_level', '')}`"])
    lines.extend(["", "## Allowed Claims", ""])
    for claim in report.get("allowed_claims", []):
        lines.append(f"- {claim}")
    lines.extend(["", "## Forbidden Claims", ""])
    for claim in report.get("forbidden_claims", []):
        lines.append(f"- {claim}")
    lines.extend(["", "## Risk Flags", ""])
    for flag in report.get("risk_flags", []):
        lines.append(f"- {flag}")
    if not report.get("risk_flags"):
        lines.append("- none")
    lines.extend(["", "## Final Verdict", "", f"`{report.get('verdict', '')}`", ""])
    return "\n".join(lines)


def write_report_files(report: dict[str, Any], json_path: str | Path, markdown_path: str | Path) -> None:
    Path(json_path).write_text(stable_json(report), encoding="utf-8")
    Path(markdown_path).write_text(render_verification_report_markdown(report), encoding="utf-8")


def verification_report_for_certificate(path: str | Path) -> dict[str, Any]:
    cert_path = Path(path)
    checker_result = verify_certificate_bundle(cert_path)
    verified = bool(checker_result.get("verified", False))
    risk_flags: list[str] = []
    if not verified:
        risk_flags.append(str(checker_result.get("failed_check", "certificate_verification_failed")))
    result = VerificationReport(
        claim="Witnora certificate bundle is internally consistent and independently replay-checkable.",
        logical_status=str(checker_result.get("status", "NOT_VERIFIED")),
        discovery_route="CERTIFICATE_BUNDLE_CHECK",
        certification_level="CERTIFICATE_BUNDLE_VERIFIED" if verified else "NOT_VERIFIED",
        public_category="CERTIFICATE_VERIFIED" if verified else "CERTIFICATE_NOT_VERIFIED",
        evidence_files=[str(cert_path)],
        external_checkers=[],
        checker_results=[{"checker": "witnora_certificate_bundle_verifier", **checker_result}],
        artifact_hashes={str(cert_path): sha256_file(cert_path)} if cert_path.is_file() else {},
        reproducibility_status="CERTIFICATE_REPLAYED" if verified else "CERTIFICATE_REPLAY_FAILED",
        risk_flags=risk_flags,
        verdict=VERDICT_VERIFIED if verified else VERDICT_NOT_VERIFIED,
    )
    return result.to_dict()


def parse_manifest_hash_table(text: str) -> dict[str, str]:
    hashes: dict[str, str] = {}
    row_pattern = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`?([A-Fa-f0-9]{64})`?\s*\|", re.MULTILINE)
    for match in row_pattern.finditer(text):
        hashes[match.group(1)] = match.group(2).upper()
    return hashes


def _manifest_lookup(path: Path, manifest_hashes: dict[str, str]) -> str | None:
    candidates = [str(path), path.name, str(path).replace("\\", "/")]
    for candidate in candidates:
        if candidate in manifest_hashes:
            return manifest_hashes[candidate]
    return None


def verification_report_for_release(
    *,
    source_zip: str | Path,
    diagnostic_zip: str | Path,
    manifest: str | Path,
) -> dict[str, Any]:
    source_path = Path(source_zip)
    diagnostic_path = Path(diagnostic_zip)
    manifest_path = Path(manifest)
    evidence = [str(source_path), str(diagnostic_path), str(manifest_path)]
    artifact_hashes = {str(path): sha256_file(path) for path in [source_path, diagnostic_path, manifest_path]}
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest_hashes = parse_manifest_hash_table(manifest_text)

    checker_results: list[dict[str, Any]] = []
    risk_flags: list[str] = []
    for path in [source_path, diagnostic_path]:
        actual = artifact_hashes[str(path)]
        expected = _manifest_lookup(path, manifest_hashes)
        if expected is None:
            risk_flags.append(f"manifest_missing_hash:{path.name}")
            checker_results.append({"checker": "sha256_manifest_match", "path": str(path), "passed": False, "error": "not listed in manifest"})
        elif expected != actual:
            risk_flags.append(f"hash_mismatch:{path.name}")
            checker_results.append({"checker": "sha256_manifest_match", "path": str(path), "passed": False, "expected": expected, "actual": actual})
        else:
            checker_results.append({"checker": "sha256_manifest_match", "path": str(path), "passed": True, "sha256": actual})

    claim_scan = scan_text_for_claim_boundary(manifest_text)
    checker_results.append({"checker": "claim_boundary_scan", "passed": bool(claim_scan.get("passed")), "details": claim_scan})
    if not claim_scan.get("passed"):
        risk_flags.append("forbidden_affirmative_claim")

    external_checkers = []
    if "drat-trim" in manifest_text or "drat_trim" in manifest_text:
        external_checkers.append("drat-trim")
    if "188 tests" in manifest_text:
        external_checkers.append("unit test suite")
    if "SHA256" in manifest_text:
        external_checkers.append("SHA256 archive checks")

    all_hash_checks_passed = all(
        result.get("passed") is True
        for result in checker_results
        if result.get("checker") == "sha256_manifest_match"
    )
    if risk_flags and not all_hash_checks_passed:
        verdict = VERDICT_PARTIALLY_VERIFIED
        reproducibility = "ARTIFACTS_HASHED_WITH_MANIFEST_GAPS"
    elif risk_flags:
        verdict = VERDICT_OVERCLAIM
        reproducibility = "CLAIM_BOUNDARY_FAILED"
    else:
        verdict = VERDICT_VERIFIED
        reproducibility = "SOURCE_AND_DIAGNOSTIC_HASHES_VERIFIED"

    return VerificationReport(
        claim=(
            "Witnora-Core release package supports the scoped public preprint claim "
            "with source, diagnostic artifact, manifest hashes, and recorded external checks."
        ),
        logical_status="RELEASE_ARTIFACT_AUDIT",
        discovery_route="RELEASE_MANIFEST_AND_HASH_CHECK",
        certification_level="RELEASE_EVIDENCE_VERIFIED" if verdict == VERDICT_VERIFIED else "RELEASE_EVIDENCE_PARTIAL",
        public_category="PUBLIC_RELEASE_VERIFICATION",
        evidence_files=evidence,
        external_checkers=external_checkers,
        checker_results=checker_results,
        artifact_hashes=artifact_hashes,
        reproducibility_status=reproducibility,
        risk_flags=risk_flags,
        verdict=verdict,
    ).to_dict()


def trust_card_from_report(report: dict[str, Any], *, project: str = "Witnora-Core") -> dict[str, Any]:
    verdict = str(report.get("verdict", "NOT_VERIFIED"))
    if verdict == VERDICT_VERIFIED:
        trust_verdict = "VERIFIED_WITH_SCOPE_LIMITS"
    elif verdict == VERDICT_PARTIALLY_VERIFIED:
        trust_verdict = "PARTIALLY_VERIFIED_WITH_RISK_FLAGS"
    elif verdict == VERDICT_OVERCLAIM:
        trust_verdict = "OVERCLAIM_DETECTED"
    else:
        trust_verdict = "NOT_VERIFIED"
    return {
        "project": project,
        "claim": report.get("claim", ""),
        "verified_by": report.get("external_checkers", []) + [
            result.get("checker", "checker") for result in report.get("checker_results", [])
        ],
        "certification_level": report.get("certification_level", ""),
        "not_claimed": report.get("forbidden_claims", []),
        "reproducibility": report.get("reproducibility_status", ""),
        "risk_flags": report.get("risk_flags", []),
        "verdict": trust_verdict,
    }


def render_trust_card_markdown(card: dict[str, Any]) -> str:
    lines = [
        "# Witnora Trust Card",
        "",
        f"**Project:** {card.get('project', '')}",
        "",
        "## Claim",
        "",
        str(card.get("claim", "")),
        "",
        "## Verified By",
        "",
    ]
    for item in card.get("verified_by", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Certification Level", "", f"`{card.get('certification_level', '')}`"])
    lines.extend(["", "## Not Claimed", ""])
    for item in card.get("not_claimed", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Reproducibility", "", str(card.get("reproducibility", ""))])
    lines.extend(["", "## Verdict", "", f"`{card.get('verdict', '')}`", ""])
    return "\n".join(lines)
