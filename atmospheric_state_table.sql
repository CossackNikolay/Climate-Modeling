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