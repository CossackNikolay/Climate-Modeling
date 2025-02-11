"""
Team Grafiti Climate Model - Atmospheric Dynamics Module
Version: 3.0
Date: 2025-02-10
Project Lead: CossackNikolay
Last Update: 2025-02-10 07:26:58 UTC

Project Philosophy:
- Modular climate model with specialized components
- Well-defined inputs/outputs for each module
- Central orchestration of data flow
- Robust validation and error handling
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
import psycopg2
from psycopg2.extras import execute_batch
from typing import Dict, List, Tuple, Optional, Any
import logging
import json
import warnings
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    handlers=[
        logging.FileHandler('climate_model.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AtmosphericDynamics:
    """
    Core Atmospheric Dynamics Module
    Handles: 
    - Atmospheric state calculations
    - Data persistence
    - Grafana visualization integration
    - Real-time monitoring
    """
    
    def __init__(self, db_params: Dict[str, str], config: Optional[Dict] = None):
        """Initialize the atmospheric dynamics system"""
        self.db_params = db_params
        self.config = config or self.get_default_config()
        self.conn = None
        self.cursor = None
        self.running = False
        
        # Initialize system components
        self.connect_to_db()
        self.setup_tables()
        self.setup_grafana_outputs()
        
        logger.info("Atmospheric Dynamics module initialized by %s", "CossackNikolay")

    def get_default_config(self) -> Dict:
        """Default configuration for the system"""
        return {
            'locations': [
                {'name': 'United States', 'latitude': 38.8977, 'longitude': -77.0365},
                {'name': 'Canada', 'latitude': 45.4215, 'longitude': -75.6972},
                {'name': 'United Kingdom', 'latitude': 51.5074, 'longitude': -0.1278}
            ],
            'update_interval': 60,  # seconds
            'simulation': {
                'temperature_base': 20,
                'humidity_base': 60,
                'wind_speed_base': 5,
                'aqi_base': 50,
                'uv_base': 5
            }
        }

    def connect_to_db(self) -> None:
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.db_params)
            self.cursor = self.conn.cursor()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise

    def setup_tables(self) -> None:
        """Initialize database tables"""
        try:
            queries = [
                """
                CREATE TABLE IF NOT EXISTS atmospheric_state (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP WITH TIME ZONE,
                    location_name VARCHAR(100),
                    temperature FLOAT,
                    pressure FLOAT,
                    wind_u FLOAT,
                    wind_v FLOAT,
                    humidity FLOAT
                )
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_atmospheric_timestamp 
                ON atmospheric_state(timestamp)
                """
            ]
            
            for query in queries:
                self.cursor.execute(query)
            self.conn.commit()
            logger.info("Database tables initialized")
        except Exception as e:
            logger.error(f"Table setup error: {str(e)}")
            self.conn.rollback()
            raise

    def setup_grafana_outputs(self) -> None:
        """Setup Grafana visualization tables"""
        try:
            queries = [
                """
                CREATE TABLE IF NOT EXISTS weather_metrics (
                    id SERIAL PRIMARY KEY,
                    location_name VARCHAR(100),
                    latitude FLOAT,
                    longitude FLOAT,
                    temperature FLOAT,
                    humidity FLOAT,
                    wind_speed FLOAT,
                    air_quality_index FLOAT,
                    uv_index FLOAT,
                    precipitation FLOAT,
                    timestamp TIMESTAMP WITH TIME ZONE
                )
                """
            ]
            
            for query in queries:
                self.cursor.execute(query)
            self.conn.commit()
            logger.info("Grafana visualization tables created")
        except Exception as e:
            logger.error(f"Grafana table setup error: {str(e)}")
            self.conn.rollback()

    def simulate_weather_data(self, location: Dict) -> Dict:
        """
        Generate simulated weather data for a location
        """
        sim = self.config['simulation']
        return {
            'name': location['name'],
            'latitude': location['latitude'],
            'longitude': location['longitude'],
            'temperature': sim['temperature_base'] + np.random.normal(0, 2),
            'humidity': sim['humidity_base'] + np.random.normal(0, 5),
            'wind_speed': sim['wind_speed_base'] + np.random.normal(0, 1),
            'air_quality_index': sim['aqi_base'] + np.random.normal(0, 10),
            'uv_index': sim['uv_base'] + np.random.normal(0, 1),
            'precipitation': max(0, np.random.normal(0, 2))
        }

    def save_metrics_for_grafana(self, data: Dict) -> bool:
        """Save weather metrics in Grafana-compatible format"""
        try:
            query = """
                INSERT INTO weather_metrics (
                    location_name, latitude, longitude, temperature, 
                    humidity, wind_speed, air_quality_index, 
                    uv_index, precipitation, timestamp
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            self.cursor.execute(query, (
                data['name'],
                data['latitude'],
                data['longitude'],
                data['temperature'],
                data['humidity'],
                data['wind_speed'],
                data['air_quality_index'],
                data['uv_index'],
                data['precipitation'],
                datetime.now(timezone.utc)
            ))
            
            self.conn.commit()
            logger.info(f"Metrics saved for location: {data['name']}")
            return True
        except Exception as e:
            logger.error(f"Error saving metrics: {str(e)}")
            self.conn.rollback()
            return False

    def run_monitoring(self) -> None:
        """Main monitoring loop"""
        self.running = True
        logger.info("Starting weather monitoring system...")
        
        try:
            while self.running:
                current_time = datetime.now(timezone.utc)
                logger.info(f"Updating metrics at {current_time}")
                
                for location in self.config['locations']:
                    data = self.simulate_weather_data(location)
                    self.save_metrics_for_grafana(data)
                
                time.sleep(self.config['update_interval'])
        except KeyboardInterrupt:
            logger.info("Stopping weather monitoring...")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {str(e)}")
        finally:
            self.running = False
            self.close_connection()

    def close_connection(self) -> None:
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

def main():
    """Main entry point for the climate monitoring system"""
    db_params = {
        'dbname': 'weather_monitor',
        'user': 'weather_user',
        'password': 'Graphnile2025',  # Use environment variables in production
        'host': 'localhost',
        'port': '5432'
    }

    try:
        system = AtmosphericDynamics(db_params)
        system.run_monitoring()
    except Exception as e:
        logger.error(f"System initialization error: {str(e)}")

if __name__ == "__main__":
    main()