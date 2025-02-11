#!/usr/bin/env python3
"""
Weather Integration System
Author: CossackNikolay
Created: 2025-02-10
Description: Main integration module for weather monitoring system with OpenMeteo API
            and AtmosphericDynamicsModule support.
"""

import requests
import pandas as pd
import psycopg2
from datetime import datetime
import time
import schedule
import json
import logging
from typing import Dict, Optional, List
import numpy as np
from atmospheric_dynamics import AtmosphericDynamicsModule

# Configure logging
logging.basicConfig(
    filename='weather_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class WeatherMonitor:
    """Main class for weather monitoring and data integration."""
    
    def __init__(self, 
                 db_user: str = "your_username",
                 db_password: str = "your_password",
                 db_host: str = "localhost",
                 db_port: str = "5432",
                 db_name: str = "weather_monitor"):
        """
        Initialize WeatherMonitor with database configuration and locations.
        
        Args:
            db_user (str): Database username
            db_password (str): Database password
            db_host (str): Database host address
            db_port (str): Database port
            db_name (str): Database name
        """
        self.db_params = {
            "dbname": db_name,
            "user": db_user,
            "password": db_password,
            "host": db_host,
            "port": db_port
        }
        
        # Default locations to monitor
        self.locations = [
            {"name": "New York", "lat": 40.7128, "lon": -74.0060},
            {"name": "London", "lat": 51.5074, "lon": -0.1278},
            {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503}
        ]
        
        self.api_url = "https://api.open-meteo.com/v1/forecast"
        self.atmospheric_dynamics = AtmosphericDynamicsModule()
        self.logger = logging.getLogger(__name__)

    def init_database(self) -> None:
        """Initialize database tables if they don't exist."""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_params)
            with conn.cursor() as cur:
                # Create weather measurements table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS weather_measurements (
                        id SERIAL PRIMARY KEY,
                        location_name VARCHAR(100),
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        temperature DECIMAL(5,2),
                        humidity DECIMAL(5,2),
                        wind_speed DECIMAL(5,2),
                        precipitation_prob INTEGER,
                        atmospheric_stability VARCHAR(20),
                        coriolis_force DECIMAL(10,6),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create locations table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS locations (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100),
                        latitude DECIMAL(10,6),
                        longitude DECIMAL(10,6),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                self.logger.info("Database tables initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Database initialization error: {e}")
        finally:
            if conn:
                conn.close()

    def fetch_weather_data(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Fetch weather data from OpenMeteo API.
        
        Args:
            latitude (float): Location latitude
            longitude (float): Location longitude
            
        Returns:
            Optional[Dict]: Weather data dictionary or None if fetch fails
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": True,
            "hourly": "temperature_2m,relativehumidity_2m,windspeed_10m,"
                     "precipitation_probability,pressure_msl,temperature_80m,temperature_120m"
        }
        
        try:
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Add atmospheric dynamics calculations
            if data:
                temp_profile = [
                    data['hourly']['temperature_2m'][0],
                    data['hourly']['temperature_80m'][0],
                    data['hourly']['temperature_120m'][0]
                ]
                height_profile = [2, 80, 120]
                
                stability = self.atmospheric_dynamics.calculate_atmospheric_stability(
                    temp_profile,
                    height_profile
                )
                
                coriolis = self.atmospheric_dynamics.calculate_coriolis_force(
                    data['current_weather']['windspeed'],
                    latitude
                )
                
                data['atmospheric_dynamics'] = {
                    'stability': stability,
                    'coriolis_force': coriolis
                }
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching weather data: {e}")
            return None

    def save_weather_data(self, location_name: str, weather_data: Dict) -> bool:
        """
        Save weather data to database.
        
        Args:
            location_name (str): Name of the location
            weather_data (Dict): Weather data to save
            
        Returns:
            bool: True if save successful, False otherwise
        """
        if not weather_data:
            return False
        
        conn = None
        try:
            conn = psycopg2.connect(**self.db_params)
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO weather_measurements 
                    (location_name, temperature, humidity, wind_speed, 
                     precipitation_prob, atmospheric_stability, coriolis_force)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    location_name,
                    weather_data['current_weather']['temperature'],
                    weather_data['hourly']['relativehumidity_2m'][0],
                    weather_data['current_weather']['windspeed'],
                    weather_data['hourly']['precipitation_probability'][0],
                    weather_data['atmospheric_dynamics']['stability'],
                    weather_data['atmospheric_dynamics']['coriolis_force']
                ))
                conn.commit()
                self.logger.info(f"Weather data saved for {location_name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error saving weather data: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def update_all_locations(self) -> None:
        """Update weather data for all configured locations."""
        for location in self.locations:
            weather_data = self.fetch_weather_data(location['lat'], location['lon'])
            if weather_data:
                self.save_weather_data(location['name'], weather_data)
        self.logger.info("Completed update for all locations")

    def run(self, update_interval: int = 30) -> None:
        """
        Main run function to start the weather monitoring system.
        
        Args:
            update_interval (int): Update interval in minutes (default: 30)
        """
        self.logger.info("Starting Weather Monitor")
        self.init_database()
        
        # Initial update
        self.update_all_locations()
        
        # Schedule regular updates
        schedule.every(update_interval).minutes.do(self.update_all_locations)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            self.logger.info("Weather Monitor stopped by user")
        except Exception as e:
            self.logger.error(f"Weather Monitor error: {e}")

if __name__ == "__main__":
    # Create and run the weather monitor
    monitor = WeatherMonitor(
        db_user="your_username",      # Replace with your database username
        db_password="your_password",  # Replace with your database password
        db_host="localhost",
        db_port="5432",
        db_name="weather_monitor"
    )
    
    try:
        monitor.run()
    except Exception as e:
        logging.error(f"Application error: {e}")