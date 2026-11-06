"""Full preregistered W027 end-to-end solver comparison (not phase-1 smoke).

All SAT algorithms remain Rust/Kissat/CryptoMiniSat. Python generates the
unchanged source inputs, audits models/certificates, and times processes.
No experimental outcome is used to choose the precommitted instance set.
"""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import statistics
import tempfile

from scripts import benchmark_w027_smoke as shared
from scripts.benchmark_w022_vlsat import download, independent_dimacs_check
from scripts.w027_full_decoys import SPECS, clauses_for_spec, dimacs_bytes, freeze_manifest
from tests.test_mixed_xor_recovery_rust import SAT, UNSAT, core, fingerprint, make_noise
from tests.test_w027_precheck import write_dimacs


CAP_SECONDS = 30.0
REPEATS = 3
ARMS = ("kissat", "witnora_plus_kissat", "cryptominisat")
shared.CAP_SECONDS = CAP_SECONDS


def source_cases(directory):
    """Verify all 192 W026 + all 8 W022 + 4 frozen adversarial CNFs."""
    cases = []
    archive = json.loads(Path("research/results/w026_mixed_xor_recovery.json").read_text())
    assert archive["case_count"] == len(archive["cases"]) == 96
    for frozen in archive["cases"]:
        d, r = frozen["noise"], frozen["replicate"]
        assert d in (0, 32, 256, 1024, 4096, 8192) and 0 <= r < 16
        seed, noise = make_noise(d, r)
        assert seed == frozen["seed"]
        assert fingerprint(noise) == frozen["noise_fingerprint_fnv64"]
        for rhs, expected in ((SAT, "SAT"), (UNSAT, "UNSAT")):
            name = f"w026_d{d}_r{r}_{expected.lower()}"
            filename = directory / f"{name}.cnf"
            clauses = core(rhs) + noise
            write_dimacs(filename, clauses)
            assert len(clauses) == d + 20
            cases.append((name, expected, filename, clauses,
                          "synthetic_xor", 64))

    external = json.loads(Path("research/results/w022_external_vlsat2.json").read_text())
    assert len(external["cases"]) == 8
    for source in external["cases"]:
        name, expected = source["id"], source["publisher_label"]
        assert expected in ("SAT", "UNSAT")
        raw, compressed_sha = download(name)
        assert compressed_sha == source["compressed_sha256"]
        assert hashlib.sha256(raw).hexdigest() == source["cnf_sha256"]
        independent_dimacs_check(raw, name)
        filename = directory / f"{name}.cnf"
        filename.write_bytes(raw)
        nvars, clauses = shared.parse_dimacs(filename)
        cases.append((name, expected, filename, clauses,
                      "external_vlsat2", nvars))

    manifest = json.loads(Path("research/results/w027_full_decoy_manifest.json").read_text())
    assert manifest == freeze_manifest(), "uncommitted change in decoy generator or manifest"
    for spec, frozen in zip(SPECS, manifest["entries"]):
        name = spec[0]
        assert frozen["case_id"] == name and frozen["expected"] == "SAT"
        clauses = clauses_for_spec(spec)
        raw = dimacs_bytes(clauses)
        assert hashlib.sha256(raw).hexdigest() == frozen["cnf_sha256"]
        assert len(clauses) == frozen["clauses"]
        # Independent algebraic negative-control audit. A mere repeated
        # triple support or a mixed quartet is not an exact 3-XOR.
        patterns = defaultdict(set)
        for clause in clauses:
            key = tuple(sorted(map(abs, clause)))
            corner = sum(1 << j for j, v in enumerate(key)
                         if next(lit for lit in clause if abs(lit) == v) < 0)
            patterns[key].add(corner)
            assert any(lit < 0 for lit in clause), "planted all-false SAT witness"
        for occupied in patterns.values():
            for parity in (0, 1):
                needed = {v for v in range(8) if v.bit_count() % 2 == parity}
                assert not needed.issubset(occupied), "accidental full XOR quartet"
        filename = directory / f"{name}.cnf"
        filename.write_bytes(raw)
        cases.append((name, "SAT", filename, clauses,
                      "near_xor_adversarial", frozen["variables"]))

    assert len(cases) == 96 * 2 + 8 + len(SPECS) == 204
    assert len({entry[0] for entry in cases}) == len(cases)
    return cases


def summarize(rows, available):
    medians = []
    pairs = defaultdict(list)
    order = list(dict.fromkeys((x["case_id"], x["stratum"]) for x in rows))
    for name, stratum in order:
        by_arm = {}
        for arm in available:
            subset = [r for r in rows if r["case_id"] == name and r["arm"] == arm]
            assert len(subset) == REPEATS
            solved = [r["full_pipeline_wall_ns"] for r in subset
                      if r["verdict"] in ("SAT", "UNSAT")]
            median = int(statistics.median(solved)) if solved else None
            by_arm[arm] = median if len(solved) == REPEATS else None
            medians.append({"case_id": name, "stratum": stratum, "arm": arm,
                            "solved_repetitions": len(solved),
                            "timeout_repetitions": sum(r["verdict"] == "TIMEOUT" for r in subset),
                            "median_solved_wall_ns": median})
        if by_arm.get("kissat") and by_arm.get("witnora_plus_kissat"):
            pairs[stratum].append(by_arm["kissat"] / by_arm["witnora_plus_kissat"])
    strata = sorted({r["stratum"] for r in rows})
    aggregate = []
    for stratum in strata:
        part = [r for r in rows if r["stratum"] == stratum]
        ratios = pairs[stratum]
        aggregate.append({"stratum": stratum, "cases": len({r["case_id"] for r in part}),
                          "paired_complete_cases": len(ratios),
                          "median_kissat_over_witnora_ratio": statistics.median(ratios) if ratios else None,
                          "paired_witnora_wins": sum(r > 1 for r in ratios),
                          "by_arm": {arm: {
                              "solved_invocations": sum(r["verdict"] in ("SAT", "UNSAT") for r in part if r["arm"] == arm),
                              "timeouts": sum(r["verdict"] == "TIMEOUT" for r in part if r["arm"] == arm),
                              "errors": sum(r["verdict"] == "ERROR" for r in part if r["arm"] == arm),
                          } for arm in available}})
    return medians, aggregate


def run():
    precheck = Path(os.environ["W027_PRECHECK_BIN"])
    kissat = Path(os.environ["W027_KISSAT_BIN"])
    cms_string = os.environ.get("W027_CMS_BIN")
    cms = Path(cms_string) if cms_string else None
    if cms is not None and not cms.is_file():
        cms = None
    available = [arm for arm in ARMS if arm != "cryptominisat" or cms is not None]
    rows = []

    with tempfile.TemporaryDirectory(prefix="witnora-w027-full-") as folder:
        cases = source_cases(Path(folder))
        for i, (name, expected, filename, clauses, stratum, nvars) in enumerate(cases):
            source_hash = hashlib.sha256(filename.read_bytes()).hexdigest()
            for repeat in range(REPEATS):
                shift = (i + repeat) % len(available)
                for arm in available[shift:] + available[:shift]:
                    record = shared.run_arm(arm, filename, clauses, expected,
                                            precheck, kissat, cms)
                    record.update(case_id=name, stratum=stratum, expected=expected,
                                  cnf_sha256=source_hash, variables=nvars,
                                  clauses=len(clauses), repeat=repeat)
                    if stratum == "near_xor_adversarial" and arm == "witnora_plus_kissat":
                        assert record.get("precheck_blocks") == 0
                        assert record.get("precheck_status") == "NO_CERTIFICATE"
                    rows.append(record)
            print("W027 FULL case", i + 1, "/", len(cases), name,
                  "verdicts", ",".join(r["verdict"] for r in rows[-REPEATS * len(available):]),
                  flush=True)

    medians, aggregate = summarize(rows, available)
    report = {
        "study": "W-CROSSDOMAIN-027", "phase": "full_preregistered_protocol",
        "protocol": "docs/W_CROSSDOMAIN_027_COST_INCLUSIVE_SOLVER_PROTOCOL.md",
        "decoy_manifest": "research/results/w027_full_decoy_manifest.json",
        "case_count": 204, "repetitions_per_arm": REPEATS,
        "wall_cap_seconds": CAP_SECONDS, "memory_cap_bytes": shared.MEMORY_BYTES,
        "arm_availability": {a: a in available for a in ARMS},
        "kissat_source_sha": os.environ["W027_KISSAT_SHA"],
        "cms_source_sha": os.environ.get("W027_CMS_SHA"),
        "witnora_source_sha": os.environ.get("GITHUB_SHA"),
        "host_context": {k: os.environ.get(k) for k in
                         ("W027_RUNNER_OS", "W027_RUSTC", "W027_CC", "W027_CPU")},
        "rows": rows, "per_case_arm_medians": medians,
        "by_stratum": aggregate,
        "claim_scope": "full cost-inclusive 204-case W027; source-XOR benchmark is synthetic-favorable, not P=NP",
    }
    output = Path(os.environ["W027_REPORT_PATH"])
    output.write_text(json.dumps(report, separators=(",", ":"), sort_keys=True) + "\n")
    print("W027 FULL COMPLETE", len(rows), "timed solver invocations", flush=True)
    print("W027 STRATUM SUMMARY", json.dumps(aggregate, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    run()
