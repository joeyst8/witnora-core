import unittest

from witnora_core.operator_genesis import (
    HALL_DEFICIT_NATIVE_UNSAT,
    ORBIT_CAPACITY_DIAGNOSTIC_ONLY,
    find_hall_deficit,
    make_orbit_capacity_instance,
)


class HallDeficitDetectionTest(unittest.TestCase):
    def test_hall_deficit_detection(self):
        instance = make_orbit_capacity_instance("hall_local_4_3")
        deficit = find_hall_deficit(instance)
        self.assertEqual(deficit["status"], HALL_DEFICIT_NATIVE_UNSAT)
        self.assertEqual(deficit["demand_subset"], ["a", "b", "c"])
        self.assertEqual(deficit["neighborhood_resources"], ["r1", "r2"])
        self.assertEqual(deficit["demand_count"], 3)
        self.assertEqual(deficit["capacity_count"], 2)
        print("HALL_DEFICIT_DETECTION_PASS")

    def test_capacity_greater_than_one_detection(self):
        instance = make_orbit_capacity_instance("capacity_deficit_5_over_4")
        deficit = find_hall_deficit(instance)
        self.assertEqual(deficit["status"], HALL_DEFICIT_NATIVE_UNSAT)
        self.assertEqual(deficit["demand_count"], 5)
        self.assertEqual(deficit["capacity_count"], 4)

    def test_balanced_control_has_no_deficit(self):
        instance = make_orbit_capacity_instance("hall_balanced_3_3_sat_control")
        deficit = find_hall_deficit(instance)
        self.assertEqual(deficit["status"], ORBIT_CAPACITY_DIAGNOSTIC_ONLY)


if __name__ == "__main__":
    unittest.main()
