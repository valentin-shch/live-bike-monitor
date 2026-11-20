import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from collector.detect import (
    EVENT_COLUMNS,
    classify,
    confirmed_episodes,
    detect_events,
    feed_checks,
    merge_events,
)
from collector.fetch import StationStatus, _parse_stations, status_frame

FIXTURES = Path(__file__).parent / "fixtures"
START = datetime(2026, 11, 12, 8, 0, tzinfo=timezone.utc)


def t(hhmm):
    return START.replace(hour=int(hhmm[:2]), minute=int(hhmm[3:]))


def states_table(states, station_id="142"):
    """One row per 15-minute window from 08:00, with the given states."""
    return pd.DataFrame(
        {
            "station_id": station_id,
            "window_utc": [START + timedelta(minutes=15 * i) for i in range(len(states))],
            "state": states,
        }
    )


def as_tuples(episodes):
    return [
        (row.state, row.started_at, None if pd.isna(row.ended_at) else row.ended_at)
        for row in episodes.itertuples()
    ]


# ---------- classify: one state per row ----------

def one_row(bikes=5, docks=5, installed=True, renting=True, silent_minutes=1):
    feed_time = START
    return pd.DataFrame(
        {
            "station_id": ["1"],
            "num_vehicles_available": [bikes],
            "num_docks_available": [docks],
            "is_installed": [installed],
            "is_renting": [renting],
            "last_reported": [feed_time - timedelta(minutes=silent_minutes)],
            "feed_last_updated": [feed_time],
        }
    )


@pytest.mark.parametrize(
    "row, expected",
    [
        (one_row(), "ok"),
        (one_row(bikes=0), "empty"),
        (one_row(docks=0), "full"),
        (one_row(bikes=0, renting=False), "offline"),        # closed beats empty
        (one_row(bikes=12, silent_minutes=9 * 60), "offline"),  # station 320
        (one_row(silent_minutes=60), "ok"),                    # exactly 60 min is not silent yet
        (one_row(installed=False, silent_minutes=13 * 30 * 24 * 60), "retired"),  # station 245
    ],
)
def test_classify_picks_the_first_matching_state(row, expected):
    assert classify(row)["state"].item() == expected


def test_classify_on_the_real_snapshot_matches_the_stage_1_findings():
    payload = json.loads((FIXTURES / "station_status_v3.json").read_text(encoding="utf-8"))
    frame = status_frame(_parse_stations(StationStatus, payload, "station_status"), START)

    states = classify(frame).set_index("station_id")["state"]

    assert sorted(states[states == "retired"].index, key=int) == ["56", "245", "323", "366"]
    assert sorted(states[states == "offline"].index, key=int) == ["12", "320", "333", "573"]
    assert (states == "empty").sum() == 78


# ---------- confirmed_episodes: the 2-snapshot rule ----------

def test_single_empty_snapshot_is_a_flicker_and_ignored():
    states = states_table(["ok", "empty", "ok", "ok"])

    assert confirmed_episodes(states).empty


def test_briefing_example_gives_one_episode():
    states = states_table(["ok", "empty", "ok", "empty", "empty", "ok", "ok"])

    assert as_tuples(confirmed_episodes(states)) == [("empty", t("08:45"), t("09:15"))]


def test_one_ok_blip_does_not_split_an_episode():
    states = states_table(["empty", "empty", "ok", "empty", "empty", "ok", "ok"])

    assert as_tuples(confirmed_episodes(states)) == [("empty", t("08:00"), t("09:15"))]


def test_ongoing_episode_has_no_end():
    states = states_table(["ok", "ok", "empty", "empty", "empty"])

    assert as_tuples(confirmed_episodes(states)) == [("empty", t("08:30"), None)]


def test_empty_straight_to_full_gives_two_episodes():
    states = states_table(["empty", "empty", "full", "full", "ok", "ok"])

    assert as_tuples(confirmed_episodes(states)) == [
        ("empty", t("08:00"), t("08:30")),
        ("full", t("08:30"), t("09:00")),
    ]


def test_offline_and_back_online():
    states = states_table(["ok", "ok", "offline", "offline", "offline", "ok", "ok"])

    assert as_tuples(confirmed_episodes(states)) == [("offline", t("08:30"), t("09:15"))]


def test_skipped_run_does_not_break_a_streak():
    states = states_table(["ok", "ok", "empty", "empty"]).drop(index=2)  # 08:30 never ran

    assert as_tuples(confirmed_episodes(states)) == []

    states = states_table(["ok", "ok", "empty", "empty", "empty"]).drop(index=3)  # 08:45 missing

    assert as_tuples(confirmed_episodes(states)) == [("empty", t("08:30"), None)]


def test_stations_are_detected_independently():
    states = pd.concat(
        [
            states_table(["empty", "empty", "ok", "ok"], station_id="142"),
            states_table(["ok", "ok", "full", "full"], station_id="7"),
        ]
    )

    episodes = confirmed_episodes(states)

    assert sorted(zip(episodes["station_id"], episodes["state"])) == [("142", "empty"), ("7", "full")]


def test_any_key_column_can_be_debounced():
    states = states_table(["ok", "stale", "stale", "ok", "ok"]).rename(columns={"station_id": "check"})

    episodes = confirmed_episodes(states, key="check")

    assert list(episodes.columns) == ["check", "state", "started_at", "ended_at"]
    assert as_tuples(episodes) == [("stale", t("08:15"), t("08:45"))]


# ---------- feed checks ----------

def feed_snapshots(windows):
    """windows: list of (feed clock "HH:MM", station ids) — one entry per 15-minute window."""
    rows = []
    for i, (clock, ids) in enumerate(windows):
        for station_id in ids:
            rows.append(
                {
                    "station_id": station_id,
                    "window_utc": START + timedelta(minutes=15 * i),
                    "feed_last_updated": t(clock),
                    "last_reported": t(clock) - timedelta(minutes=1),
                }
            )
    return pd.DataFrame(rows)


def check_states(snapshots, check):
    checks = feed_checks(snapshots)
    return checks.loc[checks["check"] == check, "state"].tolist()


ALL = ["1", "2", "3"]


def test_quiet_night_is_not_stale_because_the_clock_moves():
    snapshots = feed_snapshots([("08:14", ALL), ("08:29", ALL), ("08:44", ALL)])

    assert check_states(snapshots, "freshness") == ["ok", "ok", "ok"]


def test_clock_that_stops_is_stale():
    snapshots = feed_snapshots([("08:14", ALL), ("08:14", ALL), ("08:14", ALL), ("09:00", ALL)])

    assert check_states(snapshots, "freshness") == ["ok", "stale", "stale", "ok"]


def test_moving_feed_clock_over_frozen_station_reports_is_stale():
    snapshots = feed_snapshots([("08:14", ALL), ("08:29", ALL), ("08:44", ALL)])
    snapshots["last_reported"] = t("08:10")  # no station has reported anything new

    assert check_states(snapshots, "freshness") == ["ok", "stale", "stale"]


def test_station_gone_is_missing_until_it_comes_back():
    snapshots = feed_snapshots(
        [("08:00", ALL), ("08:15", ["1", "2"]), ("08:30", ["1", "2"]), ("08:45", ALL)]
    )

    assert check_states(snapshots, "station_list") == ["ok", "missing", "missing", "ok"]


def test_station_absent_longer_than_the_lookback_is_no_longer_expected():
    snapshots = feed_snapshots([("08:00", ALL), ("08:15", ["1", "2"]), ("08:30", ["1", "2"])])

    checks = feed_checks(snapshots, lookback=timedelta(minutes=15))

    assert checks.loc[checks["check"] == "station_list", "state"].tolist() == ["ok", "missing", "ok"]


def test_detect_events_puts_stations_and_feed_in_one_table():
    rows = []
    for i, clock in enumerate(["08:14", "08:14", "08:14"]):  # frozen feed
        row = one_row(bikes=0).assign(window_utc=START + timedelta(minutes=15 * i))
        rows.append(row.assign(feed_last_updated=t(clock), last_reported=t(clock)))

    events = detect_events(pd.concat(rows, ignore_index=True))

    assert list(events.columns) == EVENT_COLUMNS
    assert sorted(zip(events["scope"], events["subject"], events["state"])) == [
        ("feed", "freshness", "stale"),
        ("station", "1", "empty"),
    ]


# ---------- merge_events: keeping history older than the raw days ----------

def event(subject, state, start, end=None, scope="station"):
    return {"scope": scope, "subject": subject, "state": state, "started_at": start, "ended_at": end}


def frame(*events):
    return pd.DataFrame(list(events), columns=EVENT_COLUMNS)


DAY = timedelta(days=1)


def test_old_finished_episode_survives_retention():
    raw_start = START
    saved = frame(event("142", "empty", START - 3 * DAY, START - 2 * DAY))
    fresh = frame(event("142", "full", START + DAY))

    merged = merge_events(saved, fresh, raw_start)

    assert merged["state"].tolist() == ["empty", "full"]


def test_long_running_episode_keeps_its_real_start():
    # Station 366, retired for months. Raw data only goes back to raw_start, so the
    # recompute says "retired since raw_start". The saved file knows better.
    saved = frame(event("366", "retired", START - 90 * DAY))
    fresh = frame(event("366", "retired", START))

    merged = merge_events(saved, fresh, raw_start=START)

    assert len(merged) == 1
    assert merged.loc[0, "started_at"] == START - 90 * DAY


def test_later_separate_episode_does_not_inherit_an_old_start():
    saved = frame(event("142", "empty", START - DAY, START + timedelta(hours=1)))
    fresh = frame(
        event("142", "empty", START, START + timedelta(hours=1)),
        event("142", "empty", START + timedelta(hours=5)),
    )

    merged = merge_events(saved, fresh, raw_start=START)

    assert merged["started_at"].tolist() == [START - DAY, START + timedelta(hours=5)]


def test_first_run_has_nothing_saved():
    fresh = frame(event("142", "empty", START))

    assert merge_events(frame(), fresh, START).equals(fresh)
