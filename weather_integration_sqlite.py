#!/usr/bin/env python3
"""
Weather Integration System - SQLite Version
Author: CossackNikolay
Created: 2025-02-10
Description: Simplified weather monitoring system using SQLite database
"""

import requests
import sqlite3
from datetime import datetime
import time
import schedule
import logging
import os
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    filename='weather_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class WeatherMonitor:
    """Main class for weather monitoring and data integration."""
    
    def __init__(self, db_path: str = "weather_data.db"):
        """
        Initialize WeatherMonitor with SQLite database.
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        
        # Default locations to monitor
        self.locations = [
            {"name": "New York", "lat": 40.7128, "lon": -74.0060},
            {"name": "London", "lat": 51.5074, "lon": -0.1278},
            {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503}
        ]
        
        self.api_url = "https://api.open-meteo.com/v1/forecast"
        self.logger = logging.getLogger(__name__)

    def init_database(self) -> None:
        """Initialize SQLite database and create tables if they don't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            # Create weather measurements table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS weather_measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_name TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    temperature REAL,
                    humidity REAL,
                    wind_speed REAL,
                    precipitation_prob INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization error: {e}")
        finally:
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
            "hourly": "temperature_2m,relativehumidity_2m,windspeed_10m,precipitation_probability"
        }
        
        try:
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Error fetching weather data: {e}")
            return None

    def save_weather_data(self, location_name: str, weather_data: Dict) -> bool:
        """
        Save weather data to SQLite database.
        
        Args:
            location_name (str): Name of the location
            weather_data (Dict): Weather data to save
            
        Returns:
            bool: True if save successful, False otherwise
        """
        if not weather_data:
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO weather_measurements 
                (location_name, temperature, humidity, wind_speed, precipitation_prob)
                VALUES (?, ?, ?, ?, ?)
            """, (
                location_name,
                weather_data['current_weather']['temperature'],
                weather_data['hourly']['relativehumidity_2m'][0],
                weather_data['current_weather']['windspeed'],
                weather_data['hourly']['precipitation_probability'][0]
            ))
            
            conn.commit()
            self.logger.info(f"Weather data saved for {location_name}")
            return True
                
        except Exception as e:
            self.logger.error(f"Error saving weather data: {e}")
            return False
        finally:
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
    monitor = WeatherMonitor()
    
    try:
        monitor.run()
    except Exception as e:
        logging.error(f"Application error: {e}")