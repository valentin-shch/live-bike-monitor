from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from collector import run as run_module
from collector.fetch import SchemaError
from collector.http import HttpError
from collector.monitor import read_runs
from collector.storage import read_events, read_snapshots

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 11, 12, 1, 43, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    """Every test here: no weather call (tested on its own) and no real notifier,
    whatever happens to be set on the machine running the tests."""
    monkeypatch.setattr(run_module, "update_weather", lambda client, now, data_dir: "not_due")
    for name in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "SLACK_WEBHOOK_URL", "WEBHOOK_URL", "WEBHOOK_SECRET"):
        monkeypatch.delenv(name, raising=False)


def recorded_feeds():
    return [
        (FIXTURES / "gbfs_v3.json").read_bytes(),
        (FIXTURES / "station_information_v3.json").read_bytes(),
        (FIXTURES / "station_status_v3.json").read_bytes(),
    ]


def test_run_writes_snapshot_stations_and_a_run_record(make_client, tmp_path):
    client, adapter, sleeps = make_client(recorded_feeds())

    record = run_module.run(client, tmp_path, NOW)

    assert len(read_snapshots(date(2026, 11, 12), tmp_path)) == 504
    assert len(pd.read_parquet(tmp_path / "stations" / "2026-11-12.parquet")) == 504
    assert record["outcome"] == "ok" and record["stations"] == 504
    assert read_runs(tmp_path)["outcome"].tolist() == ["ok"]


def test_two_runs_save_the_confirmed_station_events(make_client, tmp_path):
    for minutes in (0, 15):
        client, adapter, sleeps = make_client(recorded_feeds())
        run_module.run(client, tmp_path, NOW + timedelta(minutes=minutes))

    events = read_events(tmp_path)

    retired = events[events["state"] == "retired"]
    assert sorted(retired["subject"], key=int) == ["56", "245", "323", "366"]
    assert events["ended_at"].isna().all()  # nothing has recovered yet


def test_failed_collections_are_recorded_and_become_an_event(monkeypatch, tmp_path):
    def schema_changed(client, data_dir, now):
        raise SchemaError("station_status: 504 of 504 stations invalid")

    monkeypatch.setattr(run_module, "collect", schema_changed)
    for minutes in (0, 15):
        record = run_module.run(None, tmp_path, NOW + timedelta(minutes=minutes))

    assert record["outcome"] == "schema_error"
    assert read_runs(tmp_path)["outcome"].tolist() == ["schema_error", "schema_error"]
    events = read_events(tmp_path)
    assert events[["subject", "state"]].values.tolist() == [["collection", "schema_error"]]


def test_a_bug_is_recorded_as_crashed_instead_of_vanishing(monkeypatch, tmp_path):
    def buggy(client, data_dir, now):
        raise KeyError("num_vehicles_available")

    monkeypatch.setattr(run_module, "collect", buggy)

    assert run_module.run(None, tmp_path, NOW)["outcome"] == "crashed"
    assert "KeyError" in read_runs(tmp_path)["detail"].item()


def test_main_exits_with_1_when_the_feed_is_down(monkeypatch, tmp_path):
    def feed_down(client, data_dir, now):
        raise HttpError("https://feed.example/gbfs.json", 503, 5)

    monkeypatch.setattr(run_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(run_module, "collect", feed_down)

    assert run_module.main() == 1
    assert read_runs(tmp_path)["outcome"].tolist() == ["feed_down"]


def test_main_exits_with_0_on_success(monkeypatch, tmp_path):
    monkeypatch.setattr(run_module, "DATA_DIR", tmp_path)
    monkeypatch.setattr(run_module, "collect", lambda client, data_dir, now: {"stations": 504, "weather": "ok"})

    assert run_module.main() == 0
