import psycopg2
import logging
from datetime import datetime
import time
import random
import math
import sys
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class WeatherAlert:
    type: str
    threshold: float
    current_value: float
    location: str
    severity: str
    timestamp: datetime

@dataclass
class WeatherStation:
    name: str
    latitude: float
    longitude: float
    last_update: Optional[datetime] = None
    alert_thresholds: Dict[str, Dict[str, float]] = None

    def __post_init__(self):
        self.alert_thresholds = {
            'temperature': {'high': 30.0, 'low': 0.0},
            'humidity': {'high': 85.0, 'low': 20.0},
            'wind_speed': {'high': 20.0},
            'air_quality_index': {'high': 150.0},
            'uv_index': {'high': 8.0},
            'pressure': {'high': 1030.0, 'low': 980.0}
        }

class AtmosphericDynamics:
    def __init__(self):
        self.setup_logging()
        self.db_connection = None
        self.user_login = 'CossackNikolay'
        self.start_time = datetime.utcnow()
        
        self.stations = [
            WeatherStation('United States', 38.8977, -77.0365),
            WeatherStation('Canada', 45.4215, -75.6972),
            WeatherStation('United Kingdom', 51.5074, -0.1278)
        ]
        
        self.db_params = {
            'dbname': 'weather_monitor',
            'user': 'weather_user',
            'password': 'Graphnile2025',
            'host': 'localhost',
            'port': '5432'
        }

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('atmospheric_dynamics_v14.log')
            ]
        )
        self.logger = logging.getLogger('atmospheric_dynamics_v14')

    def connect_database(self):
        try:
            self.db_connection = psycopg2.connect(**self.db_params)
            self.logger.info("Database connection established")
        except Exception as e:
            self.logger.error(f"Database connection error: {str(e)}")
            raise

    def setup_database_tables(self):
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("""
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
                        timestamp TIMESTAMP WITH TIME ZONE,
                        user_login VARCHAR(100)
                    );

                    CREATE TABLE IF NOT EXISTS atmospheric_state (
                        id SERIAL PRIMARY KEY,
                        location_name VARCHAR(100),
                        timestamp TIMESTAMP WITH TIME ZONE,
                        temperature FLOAT,
                        pressure FLOAT,
                        wind_u FLOAT,
                        wind_v FLOAT,
                        humidity FLOAT,
                        user_login VARCHAR(100)
                    );

                    CREATE TABLE IF NOT EXISTS system_status (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP WITH TIME ZONE,
                        location_name VARCHAR(100),
                        status VARCHAR(50),
                        last_update TIMESTAMP WITH TIME ZONE,
                        user_login VARCHAR(100),
                        update_count INTEGER DEFAULT 0,
                        system_uptime INTEGER,
                        data_quality_score FLOAT
                    );
                    
                    CREATE TABLE IF NOT EXISTS weather_alerts (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP WITH TIME ZONE,
                        location_name VARCHAR(100),
                        alert_type VARCHAR(50),
                        current_value FLOAT,
                        threshold_value FLOAT,
                        severity VARCHAR(20),
                        user_login VARCHAR(100)
                    );
                """)
                self.db_connection.commit()
                self.logger.info("Database tables initialized successfully")
        except Exception as e:
            self.logger.error(f"Table setup error: {str(e)}")
            self.db_connection.rollback()
            raise

    def check_alerts(self, station: WeatherStation, weather_data: dict) -> List[WeatherAlert]:
        alerts = []
        current_time = datetime.utcnow()

        for metric, value in weather_data.items():
            if metric in station.alert_thresholds:
                thresholds = station.alert_thresholds[metric]
                
                if 'high' in thresholds and value > thresholds['high']:
                    alerts.append(WeatherAlert(
                        type=f"high_{metric}",
                        threshold=thresholds['high'],
                        current_value=value,
                        location=station.name,
                        severity="critical",
                        timestamp=current_time
                    ))
                
                if 'low' in thresholds and value < thresholds['low']:
                    alerts.append(WeatherAlert(
                        type=f"low_{metric}",
                        threshold=thresholds['low'],
                        current_value=value,
                        location=station.name,
                        severity="warning",
                        timestamp=current_time
                    ))
        
        return alerts

    def save_alerts(self, alerts: List[WeatherAlert]):
        try:
            with self.db_connection.cursor() as cursor:
                for alert in alerts:
                    cursor.execute("""
                        INSERT INTO weather_alerts 
                        (timestamp, location_name, alert_type, current_value, 
                        threshold_value, severity, user_login)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        alert.timestamp, alert.location, alert.type,
                        alert.current_value, alert.threshold,
                        alert.severity, self.user_login
                    ))
                self.db_connection.commit()
        except Exception as e:
            self.logger.error(f"Error saving alerts: {str(e)}")
            self.db_connection.rollback()

    def generate_weather_data(self, station: WeatherStation) -> dict:
        hour = datetime.utcnow().hour
        season_factor = math.sin(2 * math.pi * (datetime.utcnow().timetuple().tm_yday / 365.25))
        
        temp_base = 20 + 5 * season_factor + 5 * math.sin(2 * math.pi * hour / 24)
        humid_base = 60 + 20 * math.sin(2 * math.pi * (hour - 6) / 24)
        
        return {
            'temperature': temp_base + random.uniform(-2.0, 2.0),
            'humidity': max(min(humid_base + random.uniform(-5.0, 5.0), 100), 0),
            'wind_speed': random.uniform(0.0, 15.0),
            'air_quality_index': random.uniform(0.0, 150.0),
            'uv_index': max(0, min(11, 8 * math.sin(2 * math.pi * (hour - 12) / 24) + random.uniform(-1, 1))),
            'precipitation': random.uniform(0.0, 25.0) if random.random() < 0.3 else 0.0,
            'pressure': 1013.25 + random.uniform(-20.0, 20.0),
            'wind_u': random.uniform(-10.0, 10.0),
            'wind_v': random.uniform(-10.0, 10.0),
            'data_quality_score': random.uniform(0.8, 1.0)
        }

    def update_weather_data(self, station: WeatherStation):
        try:
            weather_data = self.generate_weather_data(station)
            current_time = datetime.utcnow()
            
            # Check for alerts
            alerts = self.check_alerts(station, weather_data)
            if alerts:
                self.save_alerts(alerts)
            
            with self.db_connection.cursor() as cursor:
                # Insert into weather_metrics
                cursor.execute("""
                    INSERT INTO weather_metrics 
                    (location_name, latitude, longitude, temperature, humidity, 
                    wind_speed, air_quality_index, uv_index, precipitation, 
                    timestamp, user_login)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    station.name, station.latitude, station.longitude,
                    weather_data['temperature'], weather_data['humidity'],
                    weather_data['wind_speed'], weather_data['air_quality_index'],
                    weather_data['uv_index'], weather_data['precipitation'],
                    current_time, self.user_login
                ))

                # Insert into atmospheric_state
                cursor.execute("""
                    INSERT INTO atmospheric_state 
                    (location_name, timestamp, temperature, pressure, wind_u, 
                    wind_v, humidity, user_login)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    station.name, current_time,
                    weather_data['temperature'], weather_data['pressure'],
                    weather_data['wind_u'], weather_data['wind_v'],
                    weather_data['humidity'], self.user_login
                ))

                # Update system status
                uptime = int((current_time - self.start_time).total_seconds())
                cursor.execute("""
                    INSERT INTO system_status 
                    (timestamp, location_name, status, last_update, user_login,
                    update_count, system_uptime, data_quality_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    current_time, station.name, 'Active', current_time,
                    self.user_login, 1, uptime, weather_data['data_quality_score']
                ))

                self.db_connection.commit()
                station.last_update = current_time
                self.logger.info(f"Metrics saved for location: {station.name}")

        except Exception as e:
            self.logger.error(f"Data update error for {station.name}: {str(e)}")
            self.db_connection.rollback()

    def run(self):
        try:
            self.connect_database()
            self.setup_database_tables()
            
            self.logger.info(f"Atmospheric Dynamics v14 initialized by {self.user_login}")
            self.logger.info(f"Start time (UTC): {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("Starting weather monitoring system...")
            
            while True:
                current_time = datetime.utcnow()
                self.logger.info(f"Updating metrics at {current_time}")
                
                for station in self.stations:
                    self.update_weather_data(station)
                
                time.sleep(60)
                
        except KeyboardInterrupt:
            self.logger.info("Stopping weather monitoring...")
            if self.db_connection:
                self.db_connection.close()
                self.logger.info("Database connection closed")
        except Exception as e:
            self.logger.error(f"System initialization error: {str(e)}")
            if self.db_connection:
                self.db_connection.close()

def main():
    weather_system = AtmosphericDynamics()
    weather_system.run()

if __name__ == "__main__":
    main()