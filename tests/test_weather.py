import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from collector.fetch import SchemaError
from collector.weather import (
    fetch_weather,
    is_due,
    past_days_needed,
    store_weather,
    update_weather,
    weather_days,
)

FIXTURES = Path(__file__).parent / "fixtures"
# The recorded answer covers 2026-11-20 00:00 to 2026-11-22 23:00 UTC (72 hours).
NOW = datetime(2026, 11, 22, 10, 20, tzinfo=timezone.utc)


def recorded():
    return (FIXTURES / "open_meteo_v1.json").read_bytes()


@pytest.fixture
def weather(make_client):
    client, adapter, sleeps = make_client([recorded()])
    return fetch_weather(client, past_days=2)


def test_recorded_answer_parses_into_72_utc_hours(weather):
    assert len(weather) == 72
    assert str(weather["hour_utc"].dt.tz) == "UTC"
    assert weather["hour_utc"].iloc[0] == pd.Timestamp("2026-11-20 00:00", tz="UTC")
    assert list(weather.columns) == ["hour_utc", "temperature_c", "precipitation_mm", "wind_kmh"]
    assert weather[["temperature_c", "precipitation_mm", "wind_kmh"]].notna().all().all()


def test_only_finished_hours_are_stored(weather, tmp_path):
    store_weather(weather, NOW, tmp_path)

    # At 10:20 the 09:00-10:00 hour is the last finished one; 10:00 onwards is forecast.
    assert weather_days(tmp_path) == [date(2026, 11, 20), date(2026, 11, 21), date(2026, 11, 22)]
    today = pd.read_parquet(tmp_path / "weather" / "2026-11-22.parquet")
    assert len(today) == 10
    assert today["hour_utc"].max() == pd.Timestamp("2026-11-22 09:00", tz="UTC")


def test_storing_again_replaces_instead_of_duplicating(weather, tmp_path):
    store_weather(weather, NOW, tmp_path)
    store_weather(weather, NOW.replace(hour=12), tmp_path)

    today = pd.read_parquet(tmp_path / "weather" / "2026-11-22.parquet")
    assert len(today) == 12  # 00:00 to 11:00, each hour once
    assert today["hour_utc"].is_unique


def test_lists_of_different_length_are_a_schema_error(make_client):
    payload = json.loads(recorded())
    payload["hourly"]["precipitation"].pop()
    client, adapter, sleeps = make_client([json.dumps(payload).encode()])

    with pytest.raises(SchemaError, match="different lengths"):
        fetch_weather(client, past_days=2)


def test_due_about_once_an_hour(weather, tmp_path):
    assert is_due(NOW, tmp_path)  # nothing stored yet

    store_weather(weather, NOW, tmp_path)

    assert not is_due(NOW.replace(minute=50), tmp_path)   # 09:00 hour already stored
    assert is_due(NOW.replace(hour=11, minute=4), tmp_path)  # 10:00 hour now finished


def test_first_backfill_reaches_the_first_bike_day(tmp_path):
    (tmp_path / "snapshots" / "2026-11-12").mkdir(parents=True)

    assert past_days_needed(date(2026, 11, 20), tmp_path) == 8


def test_after_an_outage_the_backfill_reaches_over_the_gap(weather, tmp_path):
    store_weather(weather, NOW, tmp_path)  # last stored day: 2026-11-22

    assert past_days_needed(date(2026, 11, 22), tmp_path) == 0
    assert past_days_needed(date(2026, 11, 25), tmp_path) == 3  # three days of weather down


def test_backfill_is_capped_at_the_api_limit(tmp_path):
    (tmp_path / "snapshots" / "2026-01-01").mkdir(parents=True)

    assert past_days_needed(date(2026, 11, 20), tmp_path) == 92


def test_weather_down_does_not_raise_and_stores_nothing(make_client, tmp_path):
    client, adapter, sleeps = make_client([503] * 5)

    assert update_weather(client, NOW, tmp_path) == "failed"
    assert weather_days(tmp_path) == []
    assert len(adapter.calls) == 5  # retried like any GET


def test_update_asks_for_the_needed_past_days(make_client, tmp_path):
    (tmp_path / "snapshots" / "2026-11-20").mkdir(parents=True)
    client, adapter, sleeps = make_client([recorded()])

    assert update_weather(client, NOW, tmp_path) == "ok"
    assert "past_days=2" in adapter.calls[0].url
    assert "timeformat=unixtime" in adapter.calls[0].url
