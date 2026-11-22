"""Hourly weather from Open-Meteo: fetch, validate, store."""
import logging
from datetime import datetime, timedelta

import pandas as pd
from pydantic import BaseModel, ValidationError, model_validator

from collector.config import DATA_DIR, OPEN_METEO_URL, WEATHER_LAT, WEATHER_LON
from collector.fetch import SchemaError
from collector.http import HttpError
from collector.storage import write_atomically, raw_days

log = logging.getLogger(__name__)
MAX_PAST_DAYS = 92  # Open-Meteo's limit for past_days


class Hourly(BaseModel):
    time: list[datetime]  # asked as Unix seconds, so they arrive as UTC, never naive
    temperature_2m: list[float | None]
    precipitation: list[float | None]
    wind_speed_10m: list[float | None]  # km/h, Open-Meteo's default unit

    @model_validator(mode="after")
    def same_length(self):
        # The hours come as parallel lists. If one list were shorter, every value after the
        # gap would sit next to the wrong hour, and nothing else would notice.
        lengths = {
            len(self.time), len(self.temperature_2m), len(self.precipitation), len(self.wind_speed_10m)
        }
        if len(lengths) != 1:
            raise ValueError(f"hourly lists have different lengths: {sorted(lengths)}")
        return self


class Forecast(BaseModel):
    hourly: Hourly


def weather_path(day, data_dir=DATA_DIR):
    return data_dir / "weather" / f"{day:%Y-%m-%d}.parquet"


def weather_days(data_dir=DATA_DIR):
    return sorted(
        datetime.strptime(p.stem, "%Y-%m-%d").date() for p in (data_dir / "weather").glob("*.parquet")
    )


def bike_days(data_dir=DATA_DIR):
    hourly_days = [
        datetime.strptime(p.stem, "%Y-%m-%d").date() for p in (data_dir / "hourly").glob("*.parquet")
    ]
    return sorted(set(raw_days(data_dir)) | set(hourly_days))


def last_complete_hour(now):
    return now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)


def is_due(now, data_dir=DATA_DIR):
    """Weather is due when the last finished hour is not stored yet: about once an hour,
    not every 15 minutes. Same data, a quarter of the calls."""
    days = weather_days(data_dir)
    if not days:
        return True
    stored = pd.read_parquet(weather_path(days[-1], data_dir))["hour_utc"].max()
    return stored < last_complete_hour(now)


def past_days_needed(today, data_dir=DATA_DIR):
    """How far back to ask. From the last stored weather day (it may be half-filled), or,
    the first time, from the first day of bike data. After an outage this reaches back over
    the gap, so the next success fills it."""
    stored = weather_days(data_dir)
    if stored:
        start = stored[-1]
    else:
        days = bike_days(data_dir)
        start = days[0] if days else today
    return max(0, min(MAX_PAST_DAYS, (today - start).days))


def fetch_weather(client, past_days):
    payload = client.get_json(
        OPEN_METEO_URL,
        params={
            "latitude": WEATHER_LAT,
            "longitude": WEATHER_LON,
            "hourly": "temperature_2m,precipitation,wind_speed_10m",
            "past_days": past_days,
            "forecast_days": 1,
            "timeformat": "unixtime",
            "timezone": "GMT",
        },
    )
    try:
        forecast = Forecast.model_validate(payload)
    except ValidationError as exc:
        raise SchemaError(f"open-meteo: {exc}") from exc
    hourly = forecast.hourly
    return pd.DataFrame(
        {
            "hour_utc": pd.to_datetime(hourly.time, utc=True),
            "temperature_c": pd.array(hourly.temperature_2m, dtype="Float64"),
            "precipitation_mm": pd.array(hourly.precipitation, dtype="Float64"),
            "wind_kmh": pd.array(hourly.wind_speed_10m, dtype="Float64"),
        }
    )


def store_weather(frame, now, data_dir=DATA_DIR):
    """Keep only finished hours (the rest of the answer is a forecast), one file per UTC day.
    A rerun replaces hours it already has, so the hour is a natural key."""
    past = frame[frame["hour_utc"] <= last_complete_hour(now)].assign(fetched_at=now)
    written = []
    for day, rows in past.groupby(past["hour_utc"].dt.date):
        path = weather_path(day, data_dir)
        if path.exists():
            rows = pd.concat([pd.read_parquet(path), rows], ignore_index=True)
        rows = rows.drop_duplicates("hour_utc", keep="last").sort_values("hour_utc")
        write_atomically(rows, path)
        written.append(day)
    return written


def update_weather(client, now, data_dir=DATA_DIR):
    """Returns "not_due", "ok" or "failed". Never raises for a weather problem: the bike
    snapshot matters more, and the next hour's run reaches back over any gap."""
    if not is_due(now, data_dir):
        return "not_due"
    try:
        frame = fetch_weather(client, past_days_needed(now.date(), data_dir))
    except (HttpError, SchemaError) as exc:
        log.warning("weather failed: %s", exc)
        return "failed"
    days = store_weather(frame, now, data_dir)
    log.info("weather: stored %d day(s), up to %s", len(days), last_complete_hour(now))
    return "ok"
