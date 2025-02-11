import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_batch
from typing import Dict, List, Tuple, Optional
import logging
from scipy.stats import norm
import json
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weather_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AtmosphericDynamics:
    def __init__(self, db_params: Dict[str, str]):
        """
        Initialize the AtmosphericDynamics system with database connection parameters.
        
        Args:
            db_params (dict): Database connection parameters including:
                - host: database host
                - database: database name
                - user: username
                - password: password
                - port: port number
        """
        self.db_params = db_params
        self.conn = None
        self.cursor = None
        self.connect_to_db()

    def connect_to_db(self) -> None:
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**self.db_params)
            self.cursor = self.conn.cursor()
            logger.info("Successfully connected to the database")
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise

    def close_connection(self) -> None:
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def calculate_pressure_gradient(self, pressure_data: List[float], distance: float) -> float:
        """
        Calculate pressure gradient from pressure measurements.
        
        Args:
            pressure_data (List[float]): List of pressure measurements in hPa
            distance (float): Distance over which gradient is calculated in km
            
        Returns:
            float: Pressure gradient in hPa/km
        """
        try:
            if len(pressure_data) < 2:
                raise ValueError("Need at least two pressure measurements")
            
            gradient = (max(pressure_data) - min(pressure_data)) / distance
            return round(gradient, 3)
        except Exception as e:
            logger.error(f"Error calculating pressure gradient: {str(e)}")
            return 0.0

    def predict_temperature_change(
        self, 
        current_temp: float, 
        pressure_gradient: float, 
        wind_speed: float
    ) -> Tuple[float, float]:
        """
        Predict temperature change based on atmospheric conditions.
        
        Args:
            current_temp (float): Current temperature in Celsius
            pressure_gradient (float): Pressure gradient in hPa/km
            wind_speed (float): Wind speed in m/s
            
        Returns:
            Tuple[float, float]: Predicted temperature change and confidence level
        """
        try:
            # Basic temperature change prediction
            temp_change = (
                0.5 * pressure_gradient + 
                0.3 * wind_speed + 
                np.random.normal(0, 0.1)
            )
            
            # Calculate confidence level based on input parameters
            confidence = min(
                0.95,
                0.7 + 0.1 * (1 - abs(pressure_gradient)/10) + 
                0.1 * (1 - wind_speed/15) + 
                0.1 * (1 - abs(current_temp)/30)
            )
            
            return round(temp_change, 2), round(confidence, 2)
        except Exception as e:
            logger.error(f"Error in temperature prediction: {str(e)}")
            return 0.0, 0.0

    def calculate_event_probability(
        self, 
        event_type: str, 
        conditions: Dict[str, float]
    ) -> Tuple[float, float]:
        """
        Calculate probability of weather events based on current conditions.
        
        Args:
            event_type (str): Type of weather event
            conditions (dict): Current weather conditions
            
        Returns:
            Tuple[float, float]: Event probability and confidence level
        """
        try:
            # Define threshold values for different events
            thresholds = {
                'storm': {
                    'pressure_gradient': 5.0,
                    'wind_speed': 15.0,
                    'humidity': 70.0
                },
                'heat_wave': {
                    'temperature': 35.0,
                    'humidity': 60.0
                },
                'frost': {
                    'temperature': 0.0,
                    'humidity': 80.0
                }
            }
            
            if event_type not in thresholds:
                raise ValueError(f"Unknown event type: {event_type}")
                
            # Calculate basic probability based on thresholds
            if event_type == 'storm':
                prob = (
                    0.4 * (conditions.get('pressure_gradient', 0) / thresholds[event_type]['pressure_gradient']) +
                    0.4 * (conditions.get('wind_speed', 0) / thresholds[event_type]['wind_speed']) +
                    0.2 * (conditions.get('humidity', 0) / thresholds[event_type]['humidity'])
                )
            elif event_type == 'heat_wave':
                prob = (
                    0.6 * (conditions.get('temperature', 0) / thresholds[event_type]['temperature']) +
                    0.4 * (conditions.get('humidity', 0) / thresholds[event_type]['humidity'])
                )
            else:  # frost
                prob = (
                    0.7 * (1 - conditions.get('temperature', 0) / thresholds[event_type]['temperature']) +
                    0.3 * (conditions.get('humidity', 0) / thresholds[event_type]['humidity'])
                )
                
            # Normalize probability
            prob = max(0, min(1, prob))
            
            # Calculate confidence based on data completeness and threshold proximity
            confidence = 0.8  # Base confidence
            for key in conditions:
                if conditions[key] is not None:
                    confidence += 0.05  # Increase confidence for each available parameter
                    
            confidence = min(0.95, confidence)
            
            return round(prob, 2), round(confidence, 2)
        except Exception as e:
            logger.error(f"Error calculating event probability: {str(e)}")
            return 0.0, 0.0

    def save_weather_data(
        self, 
        location: str, 
        temperature: float, 
        humidity: float, 
        pressure: float, 
        wind_speed: float, 
        wind_direction: float, 
        precipitation: float
    ) -> bool:
        """
        Save weather data to database.
        
        Args:
            location (str): Location name
            temperature (float): Temperature in Celsius
            humidity (float): Relative humidity percentage
            pressure (float): Atmospheric pressure in hPa
            wind_speed (float): Wind speed in m/s
            wind_direction (float): Wind direction in degrees
            precipitation (float): Precipitation amount in mm
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            query = """
                INSERT INTO weather_data 
                (timestamp, location, temperature, humidity, pressure, 
                 wind_speed, wind_direction, precipitation)
                VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (
                location, temperature, humidity, pressure,
                wind_speed, wind_direction, precipitation
            ))
            self.conn.commit()
            logger.info(f"Weather data saved for location: {location}")
            return True
        except Exception as e:
            logger.error(f"Error saving weather data: {str(e)}")
            self.conn.rollback()
            return False

    def save_event_probability(
        self, 
        location: str, 
        event_type: str, 
        probability: float, 
        confidence: float,
        parameters: Dict
    ) -> bool:
        """
        Save event probability prediction to database.
        
        Args:
            location (str): Location name
            event_type (str): Type of weather event
            probability (float): Calculated probability
            confidence (float): Confidence level
            parameters (dict): Parameters used in calculation
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            query = """
                INSERT INTO event_probabilities 
                (location_name, event_type, prediction_date, probability, 
                 confidence_level, parameters)
                VALUES (%s, %s, NOW(), %s, %s, %s)
            """
            self.cursor.execute(query, (
                location, 
                event_type, 
                probability, 
                confidence, 
                json.dumps(parameters)
            ))
            self.conn.commit()
            logger.info(f"Event probability saved for {event_type} at {location}")
            return True
        except Exception as e:
            logger.error(f"Error saving event probability: {str(e)}")
            self.conn.rollback()
            return False

    def update_temperature_thresholds(
        self, 
        location: str, 
        historical_data: pd.DataFrame
    ) -> bool:
        """
        Update temperature thresholds based on historical data.
        
        Args:
            location (str): Location name
            historical_data (pd.DataFrame): DataFrame with historical temperature data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Calculate thresholds using percentiles
            temps = historical_data['temperature'].dropna()
            if len(temps) < 100:
                raise ValueError("Insufficient historical data for threshold calculation")
                
            thresholds = {
                'moderate': float(np.percentile(temps, 75)),
                'high': float(np.percentile(temps, 85)),
                'severe': float(np.percentile(temps, 95)),
                'extreme': float(np.percentile(temps, 99))
            }
            
            # Insert new thresholds
            query = """
                INSERT INTO temperature_thresholds 
                (location_name, moderate_threshold, high_threshold, 
                 severe_threshold, extreme_threshold, valid_until)
                VALUES (%s, %s, %s, %s, %s, NOW() + INTERVAL '7 days')
            """
            self.cursor.execute(query, (
                location,
                thresholds['moderate'],
                thresholds['high'],
                thresholds['severe'],
                thresholds['extreme']
            ))
            self.conn.commit()
            logger.info(f"Temperature thresholds updated for {location}")
            return True
        except Exception as e:
            logger.error(f"Error updating temperature thresholds: {str(e)}")
            self.conn.rollback()
            return False

    def get_historical_events(
        self, 
        location: str, 
        event_type: Optional[str] = None, 
        start_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Retrieve historical weather events for analysis.
        
        Args:
            location (str): Location name
            event_type (str, optional): Type of weather event
            start_date (datetime, optional): Start date for historical data
            
        Returns:
            pd.DataFrame: DataFrame containing historical events
        """
        try:
            query = """
                SELECT * FROM historical_events 
                WHERE location_name = %s
            """
            params = [location]
            
            if event_type:
                query += " AND event_type = %s"
                params.append(event_type)
                
            if start_date:
                query += " AND event_date >= %s"
                params.append(start_date)
                
            query += " ORDER BY event_date DESC"
            
            return pd.read_sql_query(query, self.conn, params=params)
        except Exception as e:
            logger.error(f"Error retrieving historical events: {str(e)}")
            return pd.DataFrame()

    def analyze_trends(
        self, 
        location: str, 
        parameter: str, 
        days: int = 30
    ) -> Dict[str, float]:
        """
        Analyze trends in weather parameters.
        
        Args:
            location (str): Location name
            parameter (str): Weather parameter to analyze
            days (int): Number of days to analyze
            
        Returns:
            Dict[str, float]: Dictionary containing trend analysis results
        """
        try:
            query = f"""
                SELECT timestamp, {parameter}
                FROM weather_data
                WHERE location = %s
                AND timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp
            """
            
            df = pd.read_sql_query(
                query, 
                self.conn, 
                params=[location, days]
            )
            
            if df.empty:
                raise ValueError("No data available for trend analysis")
                
            # Calculate basic statistics
            stats = {
                'mean': float(df[parameter].mean()),
                'std': float(df[parameter].std()),
                'min': float(df[parameter].min()),
                'max': float(df[parameter].max()),
                'trend': float(np.polyfit(
                    range(len(df)), 
                    df[parameter].values, 
                    1
                )[0])
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error analyzing trends: {str(e)}")
            return {}

def main():
    """Main function to demonstrate usage."""
    # Database connection parameters
    db_params = {
        'dbname': 'weather_monitor',
        'user': 'weather_user',
        'password': 'weather123',  # In production, use environment variables
        'host': 'localhost',
        'port': '5432'
    }

    try:
        # Initialize the system
        weather_system = AtmosphericDynamics(db_params)

        # Example usage
        location = "New York"
        
        # Save some weather data
        weather_system.save_weather_data(
            location=location,
            temperature=25.5,
            humidity=65.0,
            pressure=1013.2,
            wind_speed=5.2,
            wind_direction=180.0,
            precipitation=0.0
        )

        # Calculate and save event probability
        conditions = {
            'temperature': 25.5,
            'humidity': 65.0,
            'pressure_gradient': 2.5,
            'wind_speed': 5.2
        }
        
        prob, conf = weather_system.calculate_event_probability('storm', conditions)
        weather_system.save_event_probability(
            location=location,
            event_type='storm',
            probability=prob,
            confidence=conf,
            parameters=conditions
        )

        # Analyze trends
        trends = weather_system.analyze_trends(location, 'temperature')
        logger.info(f"Temperature trends for {location}: {trends}")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
    finally:
        weather_system.close_connection()

if __name__ == "__main__":
    main()