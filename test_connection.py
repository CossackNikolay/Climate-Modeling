"""
PostgreSQL Connection Test
Created: 2025-02-10
Author: CossackNikolay
"""
import psycopg2
from weather_integration import WeatherIntegrationSystem

def test_database_connection():
    """Test the database connection"""
    try:
        # Create system instance
        system = WeatherIntegrationSystem()
        
        # Test connection
        session = system.SessionLocal()
        session.execute("SELECT 1")
        session.close()
        
        print("✅ Database connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_database_connection()