import psycopg2
import logging
from datetime import datetime
import time
import random
import math
import sys
import os

class WeatherStation:
    def __init__(self, name, latitude, longitude):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.last_update = None

class AtmosphericDynamics:
    def __init__(self):
        # Configure logging
        self.setup_logging()
        
        # Initialize class variables
        self.db_connection = None
        self.user_login = 'CossackNikolay'
        self.start_time = datetime.utcnow()
        
        # Weather stations configuration
        self.stations = [
            WeatherStation('United States', 38.8977, -77.0365),
            WeatherStation('Canada', 45.4215, -75.6972),
            WeatherStation('United Kingdom', 51.5074, -0.1278)
        ]
        
        # Database configuration
        self.db_params = {
            'dbname': 'weather_monitor',
            'user': 'weather_user',
            'password': 'Graphnile2025',
            'host': 'localhost',
            'port': '5432'
        }

    def setup_logging(self):
        """Configure logging settings"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        )
        self.logger = logging.getLogger('atmospheric_dynamics_v13')

    def connect_database(self):
        """Establish database connection"""
        try:
            self.db_connection = psycopg2.connect(**self.db_params)
            self.logger.info("Database connection established")
        except Exception as e:
            self.logger.error(f"Database connection error: {str(e)}")
            raise

    def setup_database_tables(self):
        """Create necessary database tables"""
        try:
            with self.db_connection.cursor() as cursor:
                # Create tables for weather metrics and system status
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
                """)
                self.db_connection.commit()
                self.logger.info("Database tables initialized successfully")
        except Exception as e:
            self.logger.error(f"Table setup error: {str(e)}")
            self.db_connection.rollback()
            raise

    def generate_weather_data(self, station):
        """Generate simulated weather data with realistic patterns"""
        hour = datetime.utcnow().hour
        season_factor = math.sin(2 * math.pi * (datetime.utcnow().timetuple().tm_yday / 365.25))
        
        # Base values with daily and seasonal variations
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

    def update_weather_data(self, station):
        """Update weather data for a specific station"""
        try:
            weather_data = self.generate_weather_data(station)
            current_time = datetime.utcnow()
            
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
        """Main method to run the weather monitoring system"""
        try:
            # Initialize database connection
            self.connect_database()
            
            # Setup database tables
            self.setup_database_tables()
            
            self.logger.info(f"Atmospheric Dynamics v13 initialized by {self.user_login}")
            self.logger.info(f"Start time (UTC): {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("Starting weather monitoring system...")
            
            # Main monitoring loop
            while True:
                current_time = datetime.utcnow()
                self.logger.info(f"Updating metrics at {current_time}")
                
                # Update data for each station
                for station in self.stations:
                    self.update_weather_data(station)
                
                # Wait for 60 seconds before next update
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
    """Entry point of the application"""
    weather_system = AtmosphericDynamics()
    weather_system.run()

if __name__ == "__main__":
    main()