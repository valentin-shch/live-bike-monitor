import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.export import OPENAPI_PATH, openapi_text
from api.main import create_app
from api.models import EmptyByHour, Page, Station, StationDetail
from collector.fetch import StationInfo, StationStatus, _parse_stations, info_frame, status_frame
from collector.storage import write_atomically, write_events, write_snapshot, write_stations

FIXTURES = Path(__file__).parent / "fixtures"
FIRST = datetime(2026, 11, 12, 1, 34, tzinfo=timezone.utc)   # window 01:30
LATEST = datetime(2026, 11, 12, 1, 49, tzinfo=timezone.utc)  # window 01:45
GONE = "1"  # in the first snapshot, absent from the latest (like the nightly 41)


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def data_dir(tmp_path_factory):
    data = tmp_path_factory.mktemp("data")
    info = _parse_stations(StationInfo, load("station_information_v3.json"), "station_information")
    status = _parse_stations(StationStatus, load("station_status_v3.json"), "station_status")
    frame = status_frame(status, FIRST)

    write_stations(info_frame(info), LATEST, data)
    write_snapshot(frame, FIRST, data)
    write_snapshot(frame[frame["station_id"] != GONE].assign(fetched_at=LATEST), LATEST, data)

    day = datetime(2026, 11, 11, tzinfo=timezone.utc)
    write_events(
        pd.DataFrame(
            [
                ("station", "12", "offline", day - timedelta(hours=12), None),
                ("station", "142", "empty", day + timedelta(hours=8), day + timedelta(hours=9)),
                ("feed", "freshness", "stale", day + timedelta(hours=3), day + timedelta(hours=4)),
            ],
            columns=["scope", "subject", "state", "started_at", "ended_at"],
        ),
        data,
    )
    # One hourly day. 07:00 UTC = 08:00 Madrid: two renting stations, one empty all hour,
    # one never empty -> 0.5. A third was not renting the whole hour and must not count.
    hour = lambda h: pd.Timestamp(day + timedelta(hours=h))  # noqa: E731
    hourly = pd.DataFrame(
        {
            "hour_utc": [hour(7), hour(7), hour(7), hour(8)],
            "station_id": ["7", "8", "9", "7"],
            "empty_share": [1.0, 0.0, 1.0, 0.25],
            "renting_share": [1.0, 1.0, 0.5, 1.0],
        }
    )
    write_atomically(hourly, data / "hourly" / "2026-11-11.parquet")
    return data


@pytest.fixture
def api(data_dir):
    return TestClient(create_app(data_dir, clock=lambda: LATEST + timedelta(minutes=10)))


# ---------- /health ----------

def test_health_reports_fresh_data(api):
    body = api.get("/health").json()

    assert body["status"] == "ok" and body["data"] == "fresh"
    assert body["minutes_since_last_snapshot"] == 10.0
    assert body["stations"] == 503
    assert body["ongoing_events"] == 1


def test_health_says_stale_but_still_answers_200(data_dir):
    late = TestClient(create_app(data_dir, clock=lambda: LATEST + timedelta(hours=2)))

    response = late.get("/health")

    assert response.status_code == 200
    assert response.json()["data"] == "stale"


def test_health_with_no_data_at_all(tmp_path):
    response = TestClient(create_app(tmp_path)).get("/health")

    assert response.status_code == 200
    assert response.json()["data"] == "no_data"


# ---------- /stations: filters and pagination ----------

def test_first_page_of_stations_matches_the_model(api):
    response = api.get("/stations")

    assert response.status_code == 200
    page = Page[Station].model_validate(response.json())
    assert (page.total, page.limit, page.offset, len(page.items)) == (503, 50, 0, 50)
    ids = [int(s.station_id) for s in page.items]
    assert ids == sorted(ids)  # stable order, numbers sorted as numbers


def test_filter_by_state(api):
    body = api.get("/stations", params={"state": "retired", "limit": 200}).json()

    assert [s["station_id"] for s in body["items"]] == ["56", "245", "323", "366"]


@pytest.mark.parametrize(
    "params",
    [{"state": "banana"}, {"limit": 0}, {"limit": 201}, {"offset": -1}, {"limit": "ten"}],
)
def test_bad_query_parameters_are_422(api, params):
    response = api.get("/stations", params=params)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][0] == "query"  # says WHERE the problem is


def test_last_page_is_short_and_past_the_end_is_empty(api):
    last = api.get("/stations", params={"limit": 50, "offset": 500}).json()
    beyond = api.get("/stations", params={"limit": 50, "offset": 600})

    assert len(last["items"]) == 3
    assert beyond.status_code == 200
    assert beyond.json()["items"] == [] and beyond.json()["total"] == 503


def test_pages_do_not_overlap(api):
    first = api.get("/stations", params={"limit": 100}).json()["items"]
    second = api.get("/stations", params={"limit": 100, "offset": 100}).json()["items"]

    assert not {s["station_id"] for s in first} & {s["station_id"] for s in second}


# ---------- /stations/{id} ----------

def test_station_detail_has_its_history(api):
    response = api.get("/stations/12")

    assert response.status_code == 200
    detail = StationDetail.model_validate(response.json())
    assert detail.state == "offline"
    assert detail.name
    assert [p.window_utc.strftime("%H:%M") for p in detail.history] == ["01:30", "01:45"]


def test_station_missing_from_the_latest_snapshot_is_unknown_not_404(api):
    body = api.get(f"/stations/{GONE}").json()

    assert body["state"] == "unknown"
    assert len(body["history"]) == 1  # only the earlier snapshot had it


def test_unknown_station_is_404(api):
    response = api.get("/stations/99999")

    assert response.status_code == 404
    assert response.json() == {"detail": "station 99999 not found"}


# ---------- /events ----------

def test_events_newest_first(api):
    body = api.get("/events").json()

    assert body["total"] == 3
    assert [e["subject"] for e in body["items"]] == ["142", "freshness", "12"]


def test_events_filters(api):
    assert [e["subject"] for e in api.get("/events", params={"type": "stale"}).json()["items"]] == ["freshness"]
    assert api.get("/events", params={"station": "142"}).json()["total"] == 1
    # Still going on at or after 08:30 on the 11th: the 142 episode (ends 09:00) and the ongoing one.
    since = api.get("/events", params={"since": "2026-11-11T08:30:00Z"}).json()
    assert sorted(e["subject"] for e in since["items"]) == ["12", "142"]


def test_no_matching_events_is_an_empty_200(api):
    response = api.get("/events", params={"station": "99999"})

    assert response.status_code == 200
    assert response.json()["items"] == []


def test_since_without_a_timezone_is_422(api):
    # Same rule as storage: a time without a timezone is ambiguous, so it is refused.
    assert api.get("/events", params={"since": "2026-11-11T08:30:00"}).status_code == 422


# ---------- /stats/empty-by-hour ----------

def test_empty_by_hour_uses_madrid_hours_and_renting_stations_only(api):
    stats = EmptyByHour.model_validate(api.get("/stats/empty-by-hour").json())

    assert len(stats.hours) == 24 and stats.days == 1
    assert (stats.hours[8].empty_share, stats.hours[8].station_hours) == (0.5, 2)
    assert stats.hours[9].empty_share == 0.25
    assert stats.hours[3].empty_share is None and stats.hours[3].station_hours == 0


def test_empty_by_hour_with_no_history(tmp_path):
    stats = TestClient(create_app(tmp_path)).get("/stats/empty-by-hour").json()

    assert stats["days"] == 0 and all(h["empty_share"] is None for h in stats["hours"])


# ---------- the published contract ----------

def test_openapi_file_is_up_to_date():
    assert OPENAPI_PATH.exists(), "run: python -m api.export"
    assert OPENAPI_PATH.read_text(encoding="utf-8") == openapi_text(), "run: python -m api.export"
