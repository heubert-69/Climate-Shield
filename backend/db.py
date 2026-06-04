import os
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime

# =========================================================
# DATABASE CONFIG
# =========================================================

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/climate_shield"
)

engine = create_engine(DB_URL, pool_pre_ping=True)

# =========================================================
# INIT SCHEMA (RUN ONCE)
# =========================================================

def init_db():

    with engine.begin() as conn:

        # Locations table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS locations (
            id SERIAL PRIMARY KEY,
            city TEXT,
            state TEXT,
            country TEXT,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            UNIQUE(city, state, country)
        );
        """))

        # Weather observations (time series core)
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS weather_observations (
            id SERIAL PRIMARY KEY,
            location_id INT REFERENCES locations(id),
            timestamp TIMESTAMP,

            temperature FLOAT,
            humidity FLOAT,
            rainfall FLOAT,
            wind_speed FLOAT,
            pressure FLOAT
        );
        """))

        # Engineered features
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS engineered_features (
            id SERIAL PRIMARY KEY,
            location_id INT REFERENCES locations(id),
            timestamp TIMESTAMP,

            rain_24h FLOAT,
            humidity_trend FLOAT,
            temp_anomaly FLOAT,
            heat_index FLOAT
        );
        """))

        # Climate events (for survival models)
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS climate_events (
            id SERIAL PRIMARY KEY,
            location_id INT REFERENCES locations(id),

            event_type TEXT,
            event_start TIMESTAMP,
            event_end TIMESTAMP,
            severity FLOAT
        );
        """))

# =========================================================
# LOCATION UPSERT
# =========================================================

def get_or_create_location(city, state, country, lat, lon):

    with engine.begin() as conn:

        result = conn.execute(text("""
            SELECT id FROM locations
            WHERE city = :city AND state = :state AND country = :country
        """), {
            "city": city,
            "state": state,
            "country": country
        }).fetchone()

        if result:
            return result[0]

        result = conn.execute(text("""
            INSERT INTO locations (city, state, country, latitude, longitude)
            VALUES (:city, :state, :country, :lat, :lon)
            RETURNING id
        """), {
            "city": city,
            "state": state,
            "country": country,
            "lat": lat,
            "lon": lon
        }).fetchone()

        return result[0]

# =========================================================
# INSERT WEATHER OBSERVATION
# =========================================================

def insert_weather(location_id, weather):

    with engine.begin() as conn:

        conn.execute(text("""
            INSERT INTO weather_observations (
                location_id,
                timestamp,
                temperature,
                humidity,
                rainfall,
                wind_speed,
                pressure
            )
            VALUES (
                :location_id,
                :timestamp,
                :temperature,
                :humidity,
                :rainfall,
                :wind_speed,
                :pressure
            )
        """), {
            "location_id": location_id,
            "timestamp": datetime.utcnow(),

            "temperature": weather["temperature"],
            "humidity": weather["humidity"],
            "rainfall": weather["rainfall"],
            "wind_speed": weather["wind_speed"],
            "pressure": weather.get("pressure", 0)
        })

# =========================================================
# BUILD SURVIVAL DATASET (FEATURE ENGINEERING HOOK)
# =========================================================

def get_recent_weather(location_id, hours=24):

    with engine.begin() as conn:

        df = pd.read_sql(text("""
            SELECT *
            FROM weather_observations
            WHERE location_id = :location_id
            AND timestamp >= NOW() - INTERVAL ':hours hours'
            ORDER BY timestamp ASC
        """), conn, params={
            "location_id": location_id,
            "hours": hours
        })

    return df

# =========================================================
# EVENT LOGGING (CRITICAL FOR SURVIVAL MODELS)
# =========================================================

def log_climate_event(location_id, event_type, severity):

    with engine.begin() as conn:

        conn.execute(text("""
            INSERT INTO climate_events (
                location_id,
                event_type,
                event_start,
                severity
            )
            VALUES (
                :location_id,
                :event_type,
                :event_start,
                :severity
            )
        """), {
            "location_id": location_id,
            "event_type": event_type,
            "event_start": datetime.utcnow(),
            "severity": severity
        })
