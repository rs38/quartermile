"""
tests/test_quarter_mile.py – Unit tests for quarter-mile physics, adapter, and facade imports.
"""

import unittest
import numpy as np

from quarter_mile_cars import CAR_DATABASE
import quarter_mile_sim
from sim import (
    make_car,
    simulate_quarter_mile,
    tire_grip_multiplier,
    wheel_rpm_from_speed,
    QUARTER_MILE_M,
)


class TestQuarterMile(unittest.TestCase):
    def test_preset_car_database(self):
        """Verify all 5 database presets are present and follow the schema."""
        expected_presets = [
            "Sport Coupe",
            "Electric Sedan",
            "Muscle Car",
            "Electric Hypercar",
            "Performance Wagon",
        ]
        for preset in expected_presets:
            self.assertIn(preset, CAR_DATABASE)
            spec = CAR_DATABASE[preset]
            self.assertIn("vehicle", spec)
            self.assertIn("powertrain", spec)

    def test_make_car_adapter(self):
        """Verify make_car maps nested specs to valid runtime dicts."""
        for name, spec in CAR_DATABASE.items():
            car = make_car(name, spec)
            self.assertIn("mass", car)
            self.assertIn("mu", car)
            self.assertIn("powertrain_type", car)
            if car["powertrain_type"] == "ICE":
                self.assertIn("ice", car)
                self.assertGreater(len(car["ice"]["gear_ratios"]), 0)
            elif car["powertrain_type"] == "BEV":
                self.assertIn("motor", car)
                self.assertGreater(car["motor"]["single_speed_ratio"], 0)

    def test_tire_grip_multiplier(self):
        """Test tire grip multiplier scaling and compound factors."""
        baseline_summer = tire_grip_multiplier(245, "summer")
        self.assertAlmostEqual(baseline_summer, 1.0, places=2)

        wider_summer = tire_grip_multiplier(300, "summer")
        self.assertGreater(wider_summer, baseline_summer)

        track_compound = tire_grip_multiplier(245, "track")
        self.assertGreater(track_compound, baseline_summer)

    def test_wheel_rpm_from_speed(self):
        """Test wheel RPM calculation from vehicle speed."""
        rpm = wheel_rpm_from_speed(v=10.0, wheel_radius_m=0.335)
        expected = (10.0 / 0.335) * 60.0 / (2.0 * np.pi)
        self.assertAlmostEqual(rpm, expected, places=3)

    def test_simulation_ice(self):
        """Run quarter-mile simulation for an ICE car and check outputs."""
        car = make_car("Sport Coupe", CAR_DATABASE["Sport Coupe"])
        res = simulate_quarter_mile(car)

        self.assertIn("elapsed_time", res)
        self.assertIn("trap_speed", res)
        self.assertGreater(res["elapsed_time"], 8.0)
        self.assertLess(res["elapsed_time"], 20.0)
        self.assertGreater(res["trap_speed"], 30.0)  # > 108 km/h
        self.assertGreaterEqual(res["distance"][-1], QUARTER_MILE_M)

    def test_simulation_bev(self):
        """Run quarter-mile simulation for an Electric Hypercar and check outputs."""
        car = make_car("Electric Hypercar", CAR_DATABASE["Electric Hypercar"])
        res = simulate_quarter_mile(car)

        self.assertIn("elapsed_time", res)
        self.assertIn("trap_speed", res)
        # Hypercar should be very fast (~8-12s ET)
        self.assertGreater(res["elapsed_time"], 7.0)
        self.assertLess(res["elapsed_time"], 12.0)
        self.assertGreater(res["trap_speed"], 60.0)  # > 216 km/h

    def test_facade_imports(self):
        """Ensure quarter_mile_sim facade exposes all public symbols matching sim."""
        self.assertEqual(quarter_mile_sim.QUARTER_MILE_M, QUARTER_MILE_M)
        self.assertEqual(quarter_mile_sim.make_car, make_car)
        self.assertEqual(quarter_mile_sim.simulate_quarter_mile, simulate_quarter_mile)


if __name__ == "__main__":
    unittest.main()
