from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Location(db.Model):
    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)

    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100))

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

class WeatherObservation(db.Model):
    __tablename__ = "weather_observations"

    id = db.Column(db.Integer, primary_key=True)

    location_id = db.Column(
        db.Integer,
        db.ForeignKey("locations.id")
    )

    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    rainfall = db.Column(db.Float)
    wind_speed = db.Column(db.Float)

class ClimateRisk(db.Model):
    __tablename__ = "climate_risks"

    id = db.Column(db.Integer, primary_key=True)

    observation_id = db.Column(
        db.Integer,
        db.ForeignKey("weather_observations.id")
    )

    flood_risk = db.Column(db.Float)
    heat_risk = db.Column(db.Float)
    wildfire_risk = db.Column(db.Float)
    cyclone_risk = db.Column(db.Float)
    drought_risk = db.Column(db.Float)

class ClimateEvent(db.Model):
    __tablename__ = "climate_events"

    id = db.Column(db.Integer, primary_key=True)

    location_id = db.Column(
        db.Integer,
        db.ForeignKey("locations.id")
    )

    event_type = db.Column(db.String(50))
    severity = db.Column(db.Float)

    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

class EngineeredFeature(db.Model):
    __tablename__ = "engineered_features"

    id = db.Column(db.Integer, primary_key=True)

    observation_id = db.Column(
        db.Integer,
        db.ForeignKey("weather_observations.id")
    )

    rainfall_7day_avg = db.Column(db.Float)
    humidity_trend = db.Column(db.Float)
    temperature_anomaly = db.Column(db.Float)
