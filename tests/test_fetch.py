import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from collector.fetch import (
    SchemaError,
    StationInfo,
    StationStatus,
    _parse_stations,
    fetch_feeds,
    info_frame,
    status_frame,
)

FIXTURES = Path(__file__).parent / "fixtures"
FETCHED_AT = datetime(2026, 11, 12, 1, 43, tzinfo=timezone.utc)


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture
def status_payload():
    # A fresh copy for every test, so one test's edits never leak into another.
    return load("station_status_v3.json")


def test_real_status_fixture_is_fully_valid(status_payload):
    result = _parse_stations(StationStatus, status_payload, "station_status")

    assert len(result.stations) == 504
    assert result.rejected == []


def test_status_frame_finds_the_83_empty_stations(status_payload):
    result = _parse_stations(StationStatus, status_payload, "station_status")
    frame = status_frame(result, FETCHED_AT)

    assert (frame["num_vehicles_available"] == 0).sum() == 83


def test_stations_without_post_code_are_kept():
    result = _parse_stations(StationInfo, load("station_information_v3.json"), "station_information")
    frame = info_frame(result)

    assert len(frame) == 504
    assert frame["post_code"].isna().sum() == 3


@pytest.mark.parametrize(
    "field, bad_value",
    [
        ("num_vehicles_available", -1),
        ("is_renting", "maybe"),
        ("last_reported", "yesterday"),
    ],
)
def test_one_bad_station_is_skipped_and_the_rest_kept(status_payload, field, bad_value):
    status_payload["data"]["stations"][0][field] = bad_value

    result = _parse_stations(StationStatus, status_payload, "station_status")

    assert len(result.stations) == 503
    assert result.rejected[0][0] == "1"
    assert field in result.rejected[0][1]


def test_field_renamed_everywhere_rejects_the_snapshot(status_payload):
    for station in status_payload["data"]["stations"]:
        station["num_bikes_available"] = station.pop("num_vehicles_available")

    with pytest.raises(SchemaError, match="504 of 504"):
        _parse_stations(StationStatus, status_payload, "station_status")


def test_removing_a_field_we_do_not_use_changes_nothing(status_payload):
    for station in status_payload["data"]["stations"]:
        del station["num_vehicles_disabled"]

    result = _parse_stations(StationStatus, status_payload, "station_status")

    assert len(result.stations) == 504


def test_fetch_feeds_follows_the_discovery_urls(make_client):
    client, adapter, sleeps = make_client(
        [
            (FIXTURES / "gbfs_v3.json").read_bytes(),
            (FIXTURES / "station_information_v3.json").read_bytes(),
            (FIXTURES / "station_status_v3.json").read_bytes(),
        ]
    )

    info, status = fetch_feeds(client, discovery_url="https://feed.example/gbfs.json")

    assert [call.url.rsplit("/", 1)[-1] for call in adapter.calls] == [
        "gbfs.json",
        "station_information",
        "station_status",
    ]
    assert len(info.stations) == 504
    assert len(status.stations) == 504
