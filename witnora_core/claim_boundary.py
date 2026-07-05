"""Claim-boundary scanner for Witnora reports and release text."""

from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from typing import Iterable


FORBIDDEN_AFFIRMATIVE_CLAIMS = [
    "solves SAT",
    "solves Tseitin",
    "solves parity",
    "competitive SAT solver",
    "state of the art",
    "full XOR extraction",
    "CryptoMiniSat-style extraction",
    "industrial benchmark success",
    "industrial benchmark performance",
    "full DRAT/RAT/LRAT/FRAT support",
    "P vs NP",
    "HARD",
    "UNKNOWN",
]

NEGATIVE_CONTEXT_MARKERS = [
    "does not claim",
    "do not claim",
    "not claim",
    "not claimed",
    "no ",
    "not ",
    "without ",
    "never ",
    "forbidden",
    "avoid:",
    "avoid ",
    "limitation",
    "scope",
    "doesn't claim",
    "cannot claim",
    "must not claim",
]


@dataclass(frozen=True)
class ClaimBoundaryFinding:
    phrase: str
    context: str
    severity: str
    allowed_by_negative_context: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "phrase": self.phrase,
            "context": self.context,
            "severity": self.severity,
            "allowed_by_negative_context": self.allowed_by_negative_context,
        }


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _phrase_pattern(phrase: str) -> re.Pattern[str]:
    if phrase in {"HARD", "UNKNOWN"}:
        return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(phrase)}(?![A-Za-z0-9_])")
    return re.compile(re.escape(phrase), re.IGNORECASE)


def _allowed_context(context_before: str, full_context: str) -> bool:
    before = context_before.lower()
    whole = full_context.lower()
    return any(marker in before or marker in whole for marker in NEGATIVE_CONTEXT_MARKERS)


def scan_text_for_claim_boundary(text: str) -> dict[str, object]:
    """Scan text for forbidden affirmative claim phrases.

    The scanner is intentionally conservative and explainable. It does not try
    to infer author intent deeply; it accepts occurrences only when nearby text
    explicitly frames them as negative, forbidden, or limitation context.
    This is a heuristic text safety net, not a proof of absence of overclaims.
    """

    findings: list[ClaimBoundaryFinding] = []
    for phrase in FORBIDDEN_AFFIRMATIVE_CLAIMS:
        for match in _phrase_pattern(phrase).finditer(text):
            start, end = match.span()
            before = text[max(0, start - 400):start]
            context = _normalise(text[max(0, start - 400):min(len(text), end + 120)])
            allowed = _allowed_context(before, context)
            findings.append(
                ClaimBoundaryFinding(
                    phrase=phrase,
                    context=context,
                    severity="allowed_negative_context" if allowed else "forbidden_affirmative",
                    allowed_by_negative_context=allowed,
                )
            )

    flagged = [finding for finding in findings if not finding.allowed_by_negative_context]
    return {
        "passed": not flagged,
        "findings": [finding.to_dict() for finding in findings],
        "flagged_phrases": [finding.to_dict() for finding in flagged],
    }


def scan_files_for_claim_boundary(paths: Iterable[str | Path]) -> dict[str, object]:
    results: dict[str, object] = {}
    all_flagged: list[dict[str, object]] = []
    for raw_path in paths:
        path = Path(raw_path)
        text = path.read_text(encoding="utf-8")
        result = scan_text_for_claim_boundary(text)
        results[str(path)] = result
        for finding in result["flagged_phrases"]:  # type: ignore[index]
            item = dict(finding)
            item["path"] = str(path)
            all_flagged.append(item)
    return {
        "passed": not all_flagged,
        "files": results,
        "flagged_phrases": all_flagged,
    }
