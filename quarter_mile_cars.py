"""
quarter_mile_cars.py – Preset vehicle database for the quarter-mile simulation.

Contains default vehicle specifications following the typed schema:
Car -> Vehicle (mass, CdA, wheel_radius_m, rolling_resistance, tire)
    -> Powertrain (type, driving_axles, efficiency, motors, gearbox)
"""

CAR_DATABASE: dict = {
    "Sport Coupe": {
        "name": "Sport Coupe",
        "vehicle": {
            "mass": 1500,
            "CdA": 0.66,
            "wheel_radius_m": 0.335,
            "rolling_resistance": 0.015,
            "tire": {"width_mm": 300, "compound": "summer", "base_mu": 1.10},
        },
        "powertrain": {
            "type": "ICE",
            "driving_axles": "RWD",
            "efficiency": {"engine": 1.0, "driveline": 0.90},
            "motors": [
                {
                    "name": "ICE Engine",
                    "min_rpm": 900,
                    "max_rpm": 7200,
                    "torque_curve_rpm_nm": [
                        [1000, 380],
                        [2000, 570],
                        [3000, 860],
                        [4000, 850],
                        [5000, 850],
                        [6000, 800],
                        [7000, 690],
                        [7300, 650],
                        [8000, 100],
                    ],
                }
            ],
            "gearbox": {
                "type": "manual",
                "gear_ratios": [3.10, 2.10, 1.55, 1.22, 1.00, 0.82],
                "final_drive": 3.73,
                "launch_rpm": 2800,
                "shift_rpm": 6900,
                "shift_time_s": 0.30,
            },
        },
    },
    "Electric Sedan": {
        "name": "Electric Sedan",
        "vehicle": {
            "mass": 2400,
            "CdA": 0.68,
            "wheel_radius_m": 0.350,
            "rolling_resistance": 0.016,
            "tire": {"width_mm": 300, "compound": "summer", "base_mu": 1.05},
        },
        "powertrain": {
            "type": "BEV",
            "driving_axles": "AWD",
            "efficiency": {"motor": 1.0, "inverter": 0.96},
            "motors": [
                {
                    "name": "Combined eMotors",
                    "min_rpm": 0,
                    "max_rpm": 16000,
                    "torque_curve_rpm_nm": [
                        [0, 850],
                        [6000, 850],
                        [7000, 810],
                        [8000, 660],
                        [10000, 520],
                        [12000, 420],
                        [14000, 340],
                        [16000, 290],
                    ],
                }
            ],
            "gearbox": {"type": "single_speed", "ratio": 9.0},
        },
    },
    "Muscle Car": {
        "name": "Muscle Car",
        "vehicle": {
            "mass": 1900,
            "CdA": 0.72,
            "wheel_radius_m": 0.345,
            "rolling_resistance": 0.016,
            "tire": {"width_mm": 315, "compound": "summer", "base_mu": 1.08},
        },
        "powertrain": {
            "type": "ICE",
            "driving_axles": "RWD",
            "efficiency": {"engine": 1.0, "driveline": 0.88},
            "motors": [
                {
                    "name": "V8 Engine",
                    "min_rpm": 700,
                    "max_rpm": 6500,
                    "torque_curve_rpm_nm": [
                        [800, 550],
                        [1500, 700],
                        [2500, 820],
                        [3500, 850],
                        [4500, 830],
                        [5500, 760],
                        [6500, 620],
                        [7000, 400],
                    ],
                }
            ],
            "gearbox": {
                "type": "auto",
                "gear_ratios": [4.17, 2.34, 1.52, 1.14, 0.87, 0.69, 0.55, 0.46],
                "final_drive": 3.31,
                "launch_rpm": 1800,
                "shift_rpm": 6200,
                "shift_time_s": 0.10,
            },
        },
    },
    "Electric Hypercar": {
        "name": "Electric Hypercar",
        "vehicle": {
            "mass": 1350,
            "CdA": 0.55,
            "wheel_radius_m": 0.340,
            "rolling_resistance": 0.014,
            "tire": {"width_mm": 325, "compound": "track", "base_mu": 1.15},
        },
        "powertrain": {
            "type": "BEV",
            "driving_axles": "AWD",
            "efficiency": {"motor": 1.0, "inverter": 0.97},
            "motors": [
                {
                    "name": "Dual Motors",
                    "min_rpm": 0,
                    "max_rpm": 20000,
                    "torque_curve_rpm_nm": [
                        [0, 1250],
                        [5000, 1250],
                        [8000, 1050],
                        [11000, 780],
                        [14000, 580],
                        [17000, 420],
                        [20000, 300],
                    ],
                }
            ],
            "gearbox": {"type": "single_speed", "ratio": 10.5},
        },
    },
    "Performance Wagon": {
        "name": "Performance Wagon",
        "vehicle": {
            "mass": 1780,
            "CdA": 0.70,
            "wheel_radius_m": 0.340,
            "rolling_resistance": 0.015,
            "tire": {"width_mm": 295, "compound": "summer", "base_mu": 1.07},
        },
        "powertrain": {
            "type": "ICE",
            "driving_axles": "AWD",
            "efficiency": {"engine": 1.0, "driveline": 0.88},
            "motors": [
                {
                    "name": "Turbocharged Engine",
                    "min_rpm": 800,
                    "max_rpm": 6800,
                    "torque_curve_rpm_nm": [
                        [1000, 420],
                        [1800, 600],
                        [2500, 680],
                        [3500, 670],
                        [4500, 650],
                        [5500, 610],
                        [6500, 540],
                        [7000, 380],
                    ],
                }
            ],
            "gearbox": {
                "type": "auto",
                "gear_ratios": [3.91, 2.29, 1.55, 1.16, 0.86, 0.73],
                "final_drive": 3.55,
                "launch_rpm": 2200,
                "shift_rpm": 6500,
                "shift_time_s": 0.08,
            },
        },
    },
}
