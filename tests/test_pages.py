import json
import re
from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from pages.build import (
    api_reference,
    build,
    empty_heatmap,
    event_cards,
    format_duration,
    health_section,
    local_time,
    rules,
    safe_json,
    status,
    timelapse,
    type_label,
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


def test_a_card_cut_by_a_gap_says_so():
    rows = pd.DataFrame(
        [{"scope": "station", "subject": "330", "state": "empty", "started_at": ago(300),
          "ended_at": ago(285), "ended_by": "gap"}]
    )

    cards, _ = event_cards(rows, {}, NOW)

    assert cards[0]["text"] == "Station 330 was empty 05:55–06:10, then no data"


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


# ---------- patterns heatmap ----------

def hourly_rows(rows):
    """rows: (UTC timestamp, empty_share, renting_share)."""
    return pd.DataFrame(
        [{"hour_utc": pd.Timestamp(t), "station_id": "1", "empty_share": e, "renting_share": r} for t, e, r in rows]
    )


def test_heatmap_title_states_the_peak_in_madrid_time():
    wed_8utc = datetime(2026, 11, 11, 8, 0, tzinfo=timezone.utc)  # Wednesday 09:00 in Madrid
    heat = empty_heatmap(
        hourly_rows(
            [
                (wed_8utc, 0.30, 1.0),
                (wed_8utc + timedelta(hours=5), 0.05, 1.0),
                (wed_8utc + timedelta(hours=1), 0.90, 0.5),  # not renting all hour: left out
            ]
        ),
        min_days=1, min_coverage=0,  # this test is about the wording, not the thresholds
    )

    assert heat["title"] == "Stations run dry most on Wednesdays around 09:00"
    assert heat["caption"].startswith("30% of working stations empty then, against 5% on Wednesdays at 14:00.")
    assert "hint, not proof" in heat["caption"]
    assert heat["z"][2][9] == 30.0 and heat["z"][2][10] is None


def test_sparse_history_shows_progress_not_a_finding():
    # What GitHub's schedule gave us: a few readings a day, so each cell rests on one day.
    start = datetime(2026, 11, 16, 0, 0, tzinfo=timezone.utc)
    heat = empty_heatmap(hourly_rows([(start + timedelta(hours=7 * i), 0.2, 1.0) for i in range(20)]))  # 140 h: no hour seen twice

    assert heat["ready"] is False and "title" not in heat
    assert (heat["cells_ready"], heat["cells_needed"]) == (0, 152)


def test_a_cell_from_one_day_cannot_become_the_headline():
    monday = datetime(2026, 11, 2, 0, 0, tzinfo=timezone.utc)
    wed_9_madrid = monday + timedelta(days=2, hours=8)
    two_weeks = [monday + timedelta(hours=h) for h in range(14 * 24)]
    rows = [(h, 0.10, 1.0) for h in two_weeks if (h - wed_9_madrid).total_seconds() % (7 * 86400) != 0]
    rows += [(wed_9_madrid + timedelta(days=14), 0.90, 1.0)]  # one odd Wednesday, one hour

    heat = empty_heatmap(hourly_rows(rows))

    assert heat["ready"] is True
    assert heat["z"][2][9] is None  # one day: not shown at all
    assert "Wednesdays around 09:00" not in heat["title"]


def test_no_history_no_heatmap():
    assert empty_heatmap(pd.DataFrame()) is None


# ---------- collector health ----------

def test_health_strips_gaps_and_lateness():
    from collector.monitor import RUN_COLUMNS

    start = datetime(2026, 11, 12, 8, 0, tzinfo=timezone.utc)  # 09:00 Madrid
    runs = pd.DataFrame(
        [
            {"started_at": start + timedelta(minutes=4), "window_utc": start, "outcome": "ok"},
            # 08:15 and 08:30 UTC: nothing ran
            {"started_at": start + timedelta(minutes=55), "window_utc": start + timedelta(minutes=45), "outcome": "feed_down"},
            {"started_at": start + timedelta(minutes=70), "window_utc": start + timedelta(minutes=60), "outcome": "ok"},
        ],
        columns=RUN_COLUMNS,
    )

    health = health_section(runs, events(), start + timedelta(minutes=65))

    strip = health["strips"][0]
    assert strip["cells"][36:41] == ["o", "m", "m", "f", "o"]  # 09:00 Madrid is slot 36
    assert (strip["ok"], strip["expected"]) == (2, 5)
    assert health["gaps"][0]["when"] == "09:15–10:00"
    assert health["gaps"][0]["reasons"] == "2 missed, 1 failed"
    assert health["late_median"] == 3  # 0 and 6 minutes late


# ---------- API reference ----------

def test_type_labels_and_rules_from_openapi():
    optional_enum = {"anyOf": [{"enum": ["ok", "empty"], "type": "string"}, {"type": "null"}]}

    assert type_label(optional_enum) == "ok | empty"
    assert type_label({"type": "string", "format": "date-time"}) == "date-time"
    assert rules({"type": "integer", "minimum": 1, "maximum": 200}) == "1–200"


def test_api_reference_uses_saved_samples_when_present(tmp_path):
    from api.export import openapi_text

    (tmp_path / "health.json").write_text('{"status": "ok", "data": "fresh"}', encoding="utf-8")

    reference = api_reference(json.loads(openapi_text()), tmp_path)

    by_path = {e["path"]: e for e in reference["endpoints"]}
    assert by_path["/health"]["sample"] == '{\n  "status": "ok",\n  "data": "fresh"\n}'
    assert by_path["/stations"]["sample"] is None  # not saved yet: no invented example
    assert by_path["/stations/{station_id}"]["curl"] == 'curl "http://localhost:8000/stations/12"'
    assert [p["name"] for p in by_path["/events"]["params"]] == ["type", "station", "since", "limit", "offset"]


def test_build_writes_the_api_page_and_openapi_file(tmp_path):
    build(tmp_path / "data", tmp_path / "site", now=NOW)

    assert "GET" in (tmp_path / "site" / "api.html").read_text(encoding="utf-8")
    assert json.loads((tmp_path / "site" / "openapi.json").read_text(encoding="utf-8"))["openapi"]
