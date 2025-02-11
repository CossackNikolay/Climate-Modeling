-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;

-- Weather Data Table
CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    location VARCHAR(100) NOT NULL,
    temperature FLOAT,
    humidity FLOAT,
    pressure FLOAT,
    wind_speed FLOAT,
    wind_direction FLOAT,
    precipitation FLOAT
);

-- Historical Events Table
CREATE TABLE IF NOT EXISTS historical_events (
    id SERIAL PRIMARY KEY,
    event_date TIMESTAMP NOT NULL,
    location_name VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    severity INTEGER NOT NULL,
    temperature FLOAT,
    humidity FLOAT,
    pressure FLOAT,
    wind_speed FLOAT,
    precipitation FLOAT,
    damage_estimate FLOAT,
    affected_population INTEGER,
    description TEXT
);

-- Event Probabilities Table
CREATE TABLE IF NOT EXISTS event_probabilities (
    id SERIAL PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    prediction_date TIMESTAMP NOT NULL,
    probability FLOAT NOT NULL,
    confidence_level FLOAT NOT NULL,
    prediction_horizon INTEGER,
    model_version VARCHAR(50),
    parameters JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Climate Zones Table
CREATE TABLE IF NOT EXISTS climate_zones (
    id SERIAL PRIMARY KEY,
    climate_zone VARCHAR(10),
    sub_zone VARCHAR(10),
    description TEXT,
    geometry GEOMETRY(Polygon, 4326)
);

-- Temperature Thresholds Table
CREATE TABLE IF NOT EXISTS temperature_thresholds (
    id SERIAL PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL,
    moderate_threshold FLOAT,
    high_threshold FLOAT,
    severe_threshold FLOAT,
    extreme_threshold FLOAT,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    CONSTRAINT unique_active_threshold 
        UNIQUE (location_name, valid_until)
);

-- Create all necessary indexes
CREATE INDEX IF NOT EXISTS idx_weather_location ON weather_data(location);
CREATE INDEX IF NOT EXISTS idx_weather_timestamp ON weather_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_historical_location ON historical_events(location_name);
CREATE INDEX IF NOT EXISTS idx_historical_event_type ON historical_events(event_type);
CREATE INDEX IF NOT EXISTS idx_historical_date ON historical_events(event_date);
CREATE INDEX IF NOT EXISTS idx_prob_location ON event_probabilities(location_name);
CREATE INDEX IF NOT EXISTS idx_prob_event_type ON event_probabilities(event_type);
CREATE INDEX IF NOT EXISTS climate_zones_geometry_idx ON climate_zones USING GIST (geometry);

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO weather_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO weather_user;