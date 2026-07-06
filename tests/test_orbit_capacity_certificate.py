import unittest

from witnora_core.operator_genesis import (
    G4_ORBIT_CAPACITY_NATIVE_CERTIFIED,
    HALL_DEFICIT_NATIVE_UNSAT,
    ORBIT_CAPACITY_NATIVE_CERTIFIED,
    ORBIT_COUNTING_DRAT_NOT_CLAIMED,
    UNSAT_ORBIT_CAPACITY_NATIVE_CERTIFIED,
    build_orbit_capacity_certificate,
    make_orbit_capacity_instance,
)


class OrbitCapacityCertificateTest(unittest.TestCase):
    def test_orbit_capacity_cert_schema(self):
        cert = build_orbit_capacity_certificate(make_orbit_capacity_instance("hall_local_4_3"))
        data = cert.to_dict()
        for key in [
            "type",
            "assignment_variables",
            "demand_subset",
            "neighborhood_resources",
            "resource_capacities",
            "alo_clause_ids_by_item",
            "capacity_constraint_ids_by_resource",
            "demand_count",
            "capacity_count",
            "claim_boundary",
        ]:
            self.assertIn(key, data)
        self.assertEqual(data["type"], "ORBIT_CAPACITY_DEFICIT_CONTRADICTION")
        print("ORBIT_CAPACITY_CERT_SCHEMA_PASS")

    def test_local_hall_deficit_unsat(self):
        cert = build_orbit_capacity_certificate(make_orbit_capacity_instance("hall_local_4_3"))
        self.assertEqual(cert.status, HALL_DEFICIT_NATIVE_UNSAT)
        self.assertEqual(cert.public_category, UNSAT_ORBIT_CAPACITY_NATIVE_CERTIFIED)
        self.assertEqual(cert.certification_level, ORBIT_CAPACITY_NATIVE_CERTIFIED)
        self.assertEqual(cert.g4_delta_status, G4_ORBIT_CAPACITY_NATIVE_CERTIFIED)
        self.assertGreater(cert.demand_count, cert.capacity_count)
        print("LOCAL_HALL_DEFICIT_UNSAT_PASS")

    def test_orbit_capacity_no_fake_drat(self):
        cert = build_orbit_capacity_certificate(make_orbit_capacity_instance("hall_local_4_3"))
        self.assertEqual(cert.drat_claim, ORBIT_COUNTING_DRAT_NOT_CLAIMED)
        self.assertNotIn("DRAT", cert.public_category)
        print("ORBIT_CAPACITY_NO_FAKE_DRAT_PASS")


if __name__ == "__main__":
    unittest.main()
