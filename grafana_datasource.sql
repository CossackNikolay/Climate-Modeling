-- Run these commands in PostgreSQL to create a read-only Grafana user
CREATE USER grafana_reader WITH PASSWORD 'grafana123';
GRANT CONNECT ON DATABASE weather_monitor TO grafana_reader;
GRANT USAGE ON SCHEMA public TO grafana_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafana_reader;