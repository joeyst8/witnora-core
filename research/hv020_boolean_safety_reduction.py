#!/usr/bin/env python3
"""HV-020: dependency-free Boolean identity audit, not a reachability proof.

The node equations below are transcribed from the SHA-pinned original BTOR2
source in HV-010/HV-019. This program does not read or rehash that source.
"""

import itertools
import json


PINNED_SOURCE_SHA256 = (
    "93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49"
)
MASK23 = (1 << 23) - 1


def main() -> None:
    truth_table_rows = 0
    independent_prestate_cases = 0
    full_concat_cases = 0
    deliberately_wrong_mismatches = 0

    # Upper 23 bits of each concatenation cannot affect the low-bit slice.
    upper_words = (0, 1, 1 << 22, MASK23)
    for full_n, fsm_bit5, result_reg in itertools.product((0, 1), repeat=3):
        write_enable = full_n & fsm_bit5  # Source 25-31, low-bit slice.
        expected = full_n & fsm_bit5 & (1 ^ result_reg)

        # Source 273-277: s43'=(!write_enable)|result_reg; s45'=!s43'.
        next_s43 = (1 ^ write_enable) | result_reg
        next_s45 = 1 ^ next_s43
        next_bad = next_s45 & (1 ^ next_s43)  # Source 47-48 applied at t+1.
        assert next_bad == expected
        assert next_s45 == (1 ^ next_s43)
        truth_table_rows += 1

        if ((write_enable | (1 ^ result_reg)) != expected):
            deliberately_wrong_mismatches += 1

        for old_s43, old_s45 in itertools.product((0, 1), repeat=2):
            assert old_s43 in (0, 1) and old_s45 in (0, 1)
            # Independence of arbitrary original latch values is deliberate.
            assert next_bad == expected
            independent_prestate_cases += 1

            for first_upper, second_upper in itertools.product(upper_words, repeat=2):
                concat26 = (first_upper << 1) | full_n
                concat28 = (second_upper << 1) | fsm_bit5
                node29 = concat26 & concat28
                node30 = node29 & 1
                node31 = 1 if node30 else 0
                assert node31 == write_enable
                assert ((1 ^ node31) | result_reg) == next_s43
                full_concat_cases += 1

    assert truth_table_rows == 8
    assert independent_prestate_cases == 32
    assert full_concat_cases == 512
    assert deliberately_wrong_mismatches > 0
    print(json.dumps({
        "experiment": "HV-020",
        "scope": "one-step structural identity over three source-derived Boolean inputs",
        "upstream_sha256_from_prior_verification": PINNED_SOURCE_SHA256,
        "source_rehashed_this_run": False,
        "fresh_upstream_btor2_bytes_read_this_run": False,
        "exact_node_equations_as_transcribed": True,
        "boolean_truth_table_cases_passed": truth_table_rows,
        "arbitrary_prestate_cases_passed": independent_prestate_cases,
        "two_24bit_concat_cases_passed": full_concat_cases,
        "positive_control_deliberately_false_equation_mismatches": deliberately_wrong_mismatches,
        "proven_identity_under_transcribed_equations": (
            "bad(t+1) == full_n(t) & FSM_bit5(t) & !result_reg(t)"
        ),
        "unbounded_original_safety": "UNKNOWN; not proved by this audit",
        "full_chip_certificate": "NOT_RUN",
        "novel_algorithm": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
