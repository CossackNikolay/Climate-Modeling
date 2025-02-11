"""
Atmospheric Dynamics and Climate Monitoring System
Version: 2.0.0
Author: CossackNikolay
Created: 2025-02-10 03:43:12
"""

import psycopg2
import requests
from datetime import datetime
import logging
import time
import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt

# Database Configuration
DB_CONFIG = {
    "dbname": "weather_monitor",
    "user": "weather_user",
    "password": "Graphnile2025",
    "host": "localhost",
    "port": "5432"
}

# Open-Meteo API Configuration
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
LOCATIONS = [
    {
        "name": "London",
        "latitude": 51.5074,
        "longitude": -0.1278
    },
    {
        "name": "New York",
        "latitude": 40.7128,
        "longitude": -74.0060
    }
]

class AtmosphericSystem:
    def __init__(self):
        self.setup_logging()
        self.db_params = DB_CONFIG
        self.api_url = WEATHER_API_URL
        self.locations = LOCATIONS
        
        # Atmospheric model parameters
        self.sigma = 10.0  # Prandtl number
        self.rho = 28.0    # Rayleigh number
        self.beta = 8.0/3  # Physical parameter
        
        logging.info("Atmospheric System initialized")

    def setup_logging(self):
        """Configure logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='atmospheric_system.log'
        )

    def connect_to_db(self):
        """Establish database connection"""
        try:
            conn = psycopg2.connect(**self.db_params)
            logging.info("Database connection established")
            return conn
        except Exception as e:
            logging.error(f"Database connection failed: {e}")
            raise

    def get_weather_data(self, location):
        """Fetch weather data from Open-Meteo API"""
        try:
            params = {
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current_weather": True,
                "hourly": "temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,wind_direction_10m,precipitation"
            }
            
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            current = data["current_weather"]
            hourly = data["hourly"]
            current_hour_index = 0  # Get current hour's data
            
            return {
                "temperature": current["temperature"],
                "wind_speed": current["windspeed"],
                "wind_direction": current["winddirection"],
                "humidity": hourly["relative_humidity_2m"][current_hour_index],
                "pressure": hourly["pressure_msl"][current_hour_index],
                "precipitation": hourly["precipitation"][current_hour_index]
            }
        except Exception as e:
            logging.error(f"Failed to fetch weather data: {e}")
            return None

    def store_weather_data(self, location, weather_data):
        """Store weather data in database"""
        conn = self.connect_to_db()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO weather_data 
                (timestamp, location, temperature, humidity, pressure, 
                 wind_speed, wind_direction, precipitation)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                datetime.now(),
                f"{location['name']}",
                weather_data["temperature"],
                weather_data["humidity"],
                weather_data["pressure"],
                weather_data["wind_speed"],
                weather_data["wind_direction"],
                weather_data["precipitation"]
            ))
            conn.commit()
            logging.info(f"Stored weather data for {location['name']}")
        except Exception as e:
            logging.error(f"Failed to store weather data: {e}")
            conn.rollback()
        finally:
            conn.close()

    def lorenz_system(self, state, t):
        """Lorenz system equations for atmospheric modeling"""
        x, y, z = state
        dx = self.sigma * (y - x)
        dy = x * (self.rho - z) - y
        dz = x * y - self.beta * z
        return [dx, dy, dz]

    def simulate_atmospheric_dynamics(self, initial_state, t_span, dt):
        """Simulate atmospheric dynamics using the Lorenz system"""
        t = np.arange(0, t_span, dt)
        solution = odeint(self.lorenz_system, initial_state, t)
        
        # Store simulation results
        conn = self.connect_to_db()
        try:
            cursor = conn.cursor()
            for i in range(len(t)):
                cursor.execute("""
                    INSERT INTO simulation_results 
                    (timestamp, x_value, y_value, z_value)
                    VALUES (%s, %s, %s, %s)
                """, (
                    datetime.now() + time.timedelta(seconds=t[i]),
                    solution[i, 0],
                    solution[i, 1],
                    solution[i, 2]
                ))
            conn.commit()
            logging.info("Stored simulation results")
        except Exception as e:
            logging.error(f"Failed to store simulation results: {e}")
            conn.rollback()
        finally:
            conn.close()
        
        return t, solution

    def run_monitoring_cycle(self):
        """Run a single monitoring cycle"""
        for location in self.locations:
            try:
                weather_data = self.get_weather_data(location)
                if weather_data:
                    self.store_weather_data(location, weather_data)
                    
                    # Use weather data to initialize simulation
                    initial_state = [
                        weather_data["temperature"] / 10,  # Normalized temperature
                        weather_data["wind_speed"],
                        weather_data["pressure"] / 100     # Normalized pressure
                    ]
                    
                    # Run simulation for next 24 hours
                    t, solution = self.simulate_atmospheric_dynamics(
                        initial_state=initial_state,
                        t_span=24*3600,  # 24 hours in seconds
                        dt=300          # 5-minute intervals
                    )
                    
                    logging.info(f"Completed simulation for {location['name']}")
                
            except Exception as e:
                logging.error(f"Error processing location {location['name']}: {e}")

    def run_continuous_monitoring(self):
        """Main monitoring loop"""
        logging.info("Starting continuous atmospheric monitoring")
        while True:
            try:
                self.run_monitoring_cycle()
                time.sleep(1800)  # Wait 30 minutes before next cycle
            except KeyboardInterrupt:
                logging.info("Monitoring stopped by user")
                break
            except Exception as e:
                logging.error(f"Monitoring cycle failed: {e}")
                time.sleep(300)  # Wait 5 minutes before retry

if __name__ == "__main__":
    system = AtmosphericSystem()
    system.run_continuous_monitoring()