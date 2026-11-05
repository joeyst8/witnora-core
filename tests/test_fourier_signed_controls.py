"""W-CROSSDOMAIN-009 fixed-topology exhaustive syndrome-spectrum controls."""

from __future__ import annotations

import unittest

from scripts.benchmark_fourier_signed_controls import (
    CYCLE, EDGES, NVARS, audit, canonical_gauge_signing, cycle_spectrum,
    flip_source_variable, signed_source,
)
from tests.test_fourier_parity_violation_rust import independent_filtered_profile

try:
    from witnora_ve import aux_fourier_parity_violation_profile_native as native_fourier
except (ImportError, AttributeError):
    native_fourier = None


class SignedTopologyFiniteControls(unittest.TestCase):
    def test_exhaustive_same_graph_counts_and_informational_refinement(self):
        result = audit()
        self.assertEqual(result["signings"], 4 ** len(EDGES))
        self.assertEqual(result["distinct_model_counts"], 16)
        self.assertEqual(result["distinct_energy_profiles"], 80)
        self.assertEqual(result["distinct_cycle_spectra"], 135)
        self.assertEqual(result["energy_profiles_with_multiple_cycle_spectra"], 30)
        self.assertEqual(result["gauge_controls_passed"], result["gauge_controls_total"])
        self.assertEqual(result["gauge_orbits"], 256)
        self.assertEqual(result["gauge_orbit_size_min"], 64)
        self.assertEqual(result["gauge_orbit_size_max"], 64)
        self.assertTrue(result["quotient_matches_full_spectra"])
        self.assertEqual(result["quotient_distinct_cycle_spectra"], 135)

    def test_independent_literal_oracle_validates_matched_witness(self):
        witness = audit()["first_matched_energy_witness"]
        self.assertIsNotNone(witness)
        self.assertEqual(witness["models"], 2)
        self.assertEqual(witness["energy_profile"], [2, 22, 30, 10, 0, 0, 0, 0])
        self.assertNotEqual(witness["cycle_even_a"], witness["cycle_even_b"])
        for tag in ("a", "b"):
            source = witness[f"source_{tag}"]
            self.assertEqual(independent_filtered_profile(source, NVARS,
                                                           [list(CYCLE)], [False]),
                             witness[f"cycle_even_{tag}"])

    def test_variable_flip_is_assignment_bijection(self):
        for signing in (0, 1, 113, 16383):
            for variable in range(1, NVARS + 1):
                with self.subTest(signing=signing, variable=variable):
                    flipped = flip_source_variable(signing, variable)
                    self.assertEqual(cycle_spectrum(signing), cycle_spectrum(flipped))
                    self.assertEqual(canonical_gauge_signing(signing),
                                     canonical_gauge_signing(flipped))
                    self.assertEqual(len(signed_source(flipped)), len(EDGES))


@unittest.skipUnless(native_fourier is not None, "native Rust wheel unavailable")
class RustSignedTopologyWitnessParity(unittest.TestCase):
    def test_native_exact_matched_witness_spectra(self):
        witness = audit()["first_matched_energy_witness"]
        for tag in ("a", "b"):
            source = witness[f"source_{tag}"]
            self.assertEqual(native_fourier(source, NVARS, [], [], NVARS),
                             witness["energy_profile"])
            self.assertEqual(native_fourier(source, NVARS, [list(CYCLE)], [False], NVARS),
                             witness[f"cycle_even_{tag}"])


if __name__ == "__main__":
    unittest.main()
