import json
import re
from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from pages.build import (
    build,
    event_cards,
    format_duration,
    local_time,
    safe_json,
    status,
    timelapse,
)

NOW = datetime(2026, 11, 12, 9, 55, tzinfo=timezone.utc)  # 10:55 in Madrid


def ago(minutes):
    return NOW - timedelta(minutes=minutes)


def events(*rows):
    return pd.DataFrame(rows, columns=["scope", "subject", "state", "started_at", "ended_at"])


@pytest.mark.parametrize(
    "minutes, expected",
    [(25, "25m"), (100, "1h 40m"), (60, "1h 0m"), (3 * 24 * 60 + 90, "3d 1h"), (0, "0m")],
)
def test_format_duration(minutes, expected):
    assert format_duration(timedelta(minutes=minutes)) == expected


def test_local_time_adds_the_day_only_when_it_is_not_today():
    assert local_time(ago(100), NOW) == "09:15"
    assert local_time(ago(24 * 60), NOW) == "Wed 10:55"
    assert local_time(ago(10 * 24 * 60), NOW) == "02 Nov 10:55"


# ---------- event cards ----------

def test_card_reads_like_the_brief():
    cards, more = event_cards(events(("station", "142", "empty", ago(100), None)), {"142": "C/ Pujades, 1"}, NOW)

    assert cards == [
        {"text": "Station 142 empty since 09:15", "duration": "1h 40m",
         "place": "C/ Pujades, 1", "state": "empty", "ongoing": True}
    ]
    assert more == 0


def test_ongoing_feed_problems_are_pinned_and_retired_stations_left_out():
    cards, _ = event_cards(
        events(
            ("station", "7", "full", ago(10), None),
            ("feed", "freshness", "stale", ago(60), None),
            ("station", "366", "retired", ago(10), None),
        ),
        {},
        NOW,
    )

    assert [c["text"] for c in cards] == ["Bicing feed not updating since 09:55", "Station 7 full since 10:45"]


def test_finished_episodes_from_the_last_24_hours_only():
    cards, _ = event_cards(
        events(
            ("station", "12", "offline", ago(300), ago(200)),
            ("station", "13", "offline", ago(3000), ago(2000)),  # ended 33 h ago
        ),
        {},
        NOW,
    )

    assert [c["text"] for c in cards] == ["Station 12 was offline 05:55–07:35"]
    assert cards[0]["duration"] == "1h 40m" and not cards[0]["ongoing"]


def test_cards_are_limited_and_the_rest_counted():
    rows = [("station", str(i), "empty", ago(i + 1), None) for i in range(45)]

    cards, more = event_cards(events(*rows), {}, NOW, limit=40)

    assert len(cards) == 40 and more == 5
    assert cards[0]["text"].startswith("Station 0 ")  # newest change first


# ---------- time-lapse data ----------

def test_timelapse_marks_a_missing_window_as_unknown():
    w1, w2 = ago(30), ago(15)
    recent = pd.DataFrame(
        {
            "station_id": ["1", "1", "2"],
            "window_utc": [w1, w2, w2],  # station 2 has no row in the first window
            "state": ["empty", "ok", "full"],
            "num_vehicles_available": [0, 4, 20],
        }
    )
    info = pd.DataFrame(
        {"station_id": ["1", "2", "3"], "name": ["A", "B", "C"], "lat": [41.38, 41.39, None],
         "lon": [2.17, 2.18, 2.19], "capacity": [20, 20, 20]}
    )

    lapse = timelapse(recent, info)

    assert [s["id"] for s in lapse["stations"]] == ["1", "2"]  # 3 has no position
    assert lapse["states"] == ["eo", "uf"]
    assert lapse["bikes"] == [[0, 4], [None, 20]]


# ---------- header ----------

def snapshot(fetched):
    return pd.DataFrame({"fetched_at": [fetched], "state": ["ok"]})


NO_RUNS = pd.DataFrame(columns=["started_at", "window_utc", "outcome"])
NO_EVENTS = events()


def test_status_levels():
    assert status(snapshot(ago(6)), NO_EVENTS, NO_RUNS, NOW)["level"] == "live"
    assert status(snapshot(ago(60)), NO_EVENTS, NO_RUNS, NOW)["level"] == "down"
    stale = events(("feed", "freshness", "stale", ago(30), None))
    assert status(snapshot(ago(6)), stale, NO_RUNS, NOW)["label"] == "Bicing feed not updating"
    assert status(None, NO_EVENTS, NO_RUNS, NOW)["label"] == "No data yet"


# ---------- the page ----------

def test_a_station_name_cannot_break_out_of_the_script_tag():
    text = safe_json({"name": "</script><script>alert(1)</script>"})

    assert "</script>" not in text
    assert json.loads(text)["name"] == "</script><script>alert(1)</script>"


def test_build_with_no_data_still_makes_a_page(tmp_path):
    page = build(tmp_path / "data", tmp_path / "site", now=NOW)

    html = page.read_text(encoding="utf-8")
    assert "No data collected yet." in html
    assert (tmp_path / "site" / "plotly.min.js").stat().st_size > 1_000_000


def test_build_embeds_data_the_script_can_read(tmp_path, monkeypatch):
    from collector.fetch import StationInfo, StationStatus, _parse_stations, info_frame, status_frame
    from collector.storage import write_snapshot, write_stations
    from tests.test_api import load

    info = _parse_stations(StationInfo, load("station_information_v3.json"), "i")
    status_ = _parse_stations(StationStatus, load("station_status_v3.json"), "s")
    data = tmp_path / "data"
    write_stations(info_frame(info), ago(5), data)
    write_snapshot(status_frame(status_, ago(20)), ago(20), data)
    write_snapshot(status_frame(status_, ago(5)), ago(5), data)

    html = build(data, tmp_path / "site", now=NOW).read_text(encoding="utf-8")

    embedded = json.loads(re.search(r'<script type="application/json" id="site-data">(.*?)</script>', html, re.S).group(1))
    assert len(embedded["windows"]) == 2
    assert len(embedded["stations"]) == len(embedded["states"]) == len(embedded["bikes"])
    assert "working stations have no bikes" in html
