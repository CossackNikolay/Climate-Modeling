import numpy as np
from datetime import datetime
import logging

class AtmosphericDynamicsModule:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
    def calculate_pressure_gradient(self, pressure_values, distance):
        """Calculate pressure gradient force"""
        try:
            return np.diff(pressure_values) / distance
        except Exception as e:
            self.logger.error(f"Error calculating pressure gradient: {e}")
            return None

    def calculate_coriolis_force(self, wind_speed, latitude):
        """Calculate Coriolis force"""
        try:
            omega = 7.2921e-5  # Earth's angular velocity (rad/s)
            f = 2 * omega * np.sin(np.radians(latitude))  # Coriolis parameter
            return f * wind_speed
        except Exception as e:
            self.logger.error(f"Error calculating Coriolis force: {e}")
            return None

    def calculate_atmospheric_stability(self, temperature_profile, height_profile):
        """Calculate atmospheric stability using temperature lapse rate"""
        try:
            lapse_rate = -np.diff(temperature_profile) / np.diff(height_profile)
            dry_adiabatic_lapse_rate = 0.0098  # °C/m
            
            if np.mean(lapse_rate) < dry_adiabatic_lapse_rate:
                return "Stable"
            elif np.mean(lapse_rate) > dry_adiabatic_lapse_rate:
                return "Unstable"
            else:
                return "Neutral"
        except Exception as e:
            self.logger.error(f"Error calculating atmospheric stability: {e}")
            return None