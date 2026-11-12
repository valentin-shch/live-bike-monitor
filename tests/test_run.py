from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from collector import run as run_module
from collector.http import HttpError
from collector.storage import read_snapshots

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 11, 12, 1, 43, tzinfo=timezone.utc)


def recorded_feeds():
    return [
        (FIXTURES / "gbfs_v3.json").read_bytes(),
        (FIXTURES / "station_information_v3.json").read_bytes(),
        (FIXTURES / "station_status_v3.json").read_bytes(),
    ]


def test_run_writes_snapshot_and_stations(make_client, tmp_path):
    client, adapter, sleeps = make_client(recorded_feeds())

    run_module.run(client, tmp_path, NOW)

    assert len(read_snapshots(date(2026, 11, 12), tmp_path)) == 504
    stations = pd.read_parquet(tmp_path / "stations" / "2026-11-12.parquet")
    assert len(stations) == 504


def test_main_exits_with_1_when_the_feed_is_down(monkeypatch):
    def feed_down(client, data_dir, now):
        raise HttpError("https://feed.example/gbfs.json", 503, 5)

    monkeypatch.setattr(run_module, "run", feed_down)

    assert run_module.main() == 1


def test_main_exits_with_0_on_success(monkeypatch, tmp_path):
    monkeypatch.setattr(run_module, "run", lambda client, data_dir, now: tmp_path / "x.parquet")

    assert run_module.main() == 0
