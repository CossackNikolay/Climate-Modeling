"""
PostgreSQL Setup Verification Script
Author: CossackNikolay
Created: 2025-02-10
"""

import psycopg2
from datetime import datetime

def test_database():
    # Connection parameters
    params = {
        "dbname": "weather_monitor",
        "user": "weather_user",
        "password": "Graphnile2025",
        "host": "localhost",
        "port": "5432"
    }
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        
        # Test inserting data
        print("Testing data insertion...")
        cursor.execute("""
            INSERT INTO weather_data 
            (timestamp, location, temperature, humidity, pressure, wind_speed, wind_direction, precipitation)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            datetime.now(),
            'Test Location',
            20.5,  # temperature
            65.0,  # humidity
            1013.25,  # pressure
            5.5,   # wind_speed
            180.0, # wind_direction
            0.0    # precipitation
        ))
        
        # Commit the transaction
        conn.commit()
        
        # Verify the insertion
        print("Verifying data...")
        cursor.execute("SELECT * FROM weather_data")
        data = cursor.fetchone()
        
        if data:
            print("\n✅ Database setup successful!")
            print("\nTest record:")
            print(f"Location: {data[2]}")
            print(f"Temperature: {data[3]}°C")
            print(f"Humidity: {data[4]}%")
            print(f"Pressure: {data[5]} hPa")
            
        # Close connection
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("\nTesting PostgreSQL Setup")
    print("=" * 50)
    test_database()