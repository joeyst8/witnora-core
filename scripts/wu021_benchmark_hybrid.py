"""WU-021 paired coordinate/seeded-versus-hybrid native benchmark.

Reuses WU-019's XNF parser, independent SAT-model validation, paired
counter comparison, timeout censoring, and RSS sampling. The `--wide` binary
must be the WU-021 hybrid build; `--baseline` may be WU-019 or WU-020.
"""

from scripts import wu019_benchmark_wide as pilot

HYBRID_METRICS = (
    "hybrid_seed_checks",
    "hybrid_seed_skips",
    "hybrid_seed_rebuilds",
    "hybrid_seed_row_words",
)

def main():
    old_metrics = pilot.METRICS
    try:
        pilot.METRICS = (*old_metrics, *HYBRID_METRICS)
        return pilot.main()
    finally:
        pilot.METRICS = old_metrics

if __name__ == "__main__":
    raise SystemExit(main())
