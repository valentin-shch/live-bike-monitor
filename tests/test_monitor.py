from datetime import datetime, timedelta, timezone

import pandas as pd

from collector.monitor import (
    RUN_COLUMNS,
    collection_events,
    coverage,
    read_runs,
    window_report,
    write_run,
)

START = datetime(2026, 11, 12, 8, 0, tzinfo=timezone.utc)


def t(hhmm):
    return START.replace(hour=int(hhmm[:2]), minute=int(hhmm[3:]))


def runs(*rows):
    """rows: (started "HH:MM", outcome). The window is the started time floored to 15 min."""
    records = []
    for started, outcome in rows:
        at = t(started)
        window = at.replace(minute=at.minute - at.minute % 15)
        records.append(
            {"started_at": at, "window_utc": window, "outcome": outcome, "detail": "",
             "stations": 545, "weather": "not_due", "duration_s": 3.0}
        )
    return pd.DataFrame(records, columns=RUN_COLUMNS)


def test_runs_are_appended_not_replaced(tmp_path):
    for record in runs(("08:04", "ok"), ("08:19", "ok")).to_dict("records"):
        write_run(record, tmp_path)

    assert len(read_runs(tmp_path)) == 2


def test_report_shows_ok_failed_and_missed_windows():
    report = window_report(
        runs(("08:04", "ok"), ("08:19", "feed_down"), ("08:49", "ok")), t("08:00"), t("08:45")
    )

    assert report["status"].tolist() == ["ok", "failed", "missed", "ok"]
    assert report["delay_min"].tolist()[:2] == [4.0, 4.0]


def test_a_very_late_run_leaves_its_own_window_empty():
    # The 08:04 run started at 08:17: it lands in the 08:15 window, and so does the
    # 08:19 run. 08:00 has no data although nothing was "skipped".
    report = window_report(runs(("08:17", "ok"), ("08:19", "ok")), t("08:00"), t("08:15"))

    assert report["status"].tolist() == ["missed", "ok"]


def test_a_manual_rerun_decides_its_window():
    report = window_report(runs(("08:04", "schema_error"), ("08:11", "ok")), t("08:00"), t("08:00"))

    assert report["status"].tolist() == ["ok"]


def test_coverage_counts():
    report = window_report(runs(("08:04", "ok"), ("08:19", "crashed")), t("08:00"), t("08:45"))

    assert coverage(report) == {"expected": 4, "ok": 1, "failed": 1, "missed": 2}


def test_one_failed_run_is_a_blip():
    assert collection_events(runs(("08:04", "ok"), ("08:19", "schema_error"), ("08:34", "ok"))).empty


def test_two_failed_runs_in_a_row_are_a_schema_change_event():
    events = collection_events(
        runs(("08:04", "ok"), ("08:19", "schema_error"), ("08:34", "schema_error"))
    )

    assert events[["scope", "subject", "state"]].values.tolist() == [["feed", "collection", "schema_error"]]
    assert events["started_at"].item() == t("08:15")
    assert pd.isna(events["ended_at"].item())
