from datetime import date, datetime, timezone

import pandas as pd
import pytest

from collector.storage import (
    apply_retention,
    hourly_path,
    maintain,
    roll_up_day,
    write_snapshot,
)

UTC = timezone.utc
DAY = date(2026, 11, 12)


def at(hour, minute, day=DAY):
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=UTC)


def one_station(bikes, docks=10, renting=True):
    return pd.DataFrame(
        {
            "station_id": ["142"],
            "num_vehicles_available": [bikes],
            "num_docks_available": [docks],
            "is_renting": [renting],
        }
    )


def test_hour_with_a_skipped_run_is_summarised_from_what_exists(tmp_path):
    # 08:30 never ran: three snapshots with 0, 2 and 0 bikes.
    for minute, bikes in [(0, 0), (15, 2), (45, 0)]:
        write_snapshot(one_station(bikes), at(8, minute), tmp_path)

    hourly = pd.read_parquet(roll_up_day(DAY, tmp_path))
    row = hourly.iloc[0]

    assert len(hourly) == 1
    assert row["n_snapshots"] == 3
    assert row["bikes_mean"] == pytest.approx(2 / 3)
    assert row["empty_share"] == pytest.approx(2 / 3)
    assert row["bikes_min"] == 0


def test_one_row_per_station_per_hour(tmp_path):
    two_stations = pd.concat([one_station(1), one_station(5).assign(station_id="7")])
    for hour in (8, 9):
        for minute in (0, 15, 30, 45):
            write_snapshot(two_stations, at(hour, minute), tmp_path)

    hourly = pd.read_parquet(roll_up_day(DAY, tmp_path))

    assert len(hourly) == 4
    assert (hourly["n_snapshots"] == 4).all()


def test_full_and_renting_shares(tmp_path):
    write_snapshot(one_station(bikes=12, docks=0, renting=True), at(8, 0), tmp_path)
    write_snapshot(one_station(bikes=12, docks=0, renting=False), at(8, 15), tmp_path)

    row = pd.read_parquet(roll_up_day(DAY, tmp_path)).iloc[0]

    assert row["full_share"] == 1.0
    assert row["renting_share"] == 0.5


def test_day_without_snapshots_has_nothing_to_roll_up(tmp_path):
    assert roll_up_day(DAY, tmp_path) is None


@pytest.mark.parametrize("days_old, kept", [(14, True), (15, False)])
def test_retention_keeps_exactly_fourteen_days(tmp_path, days_old, kept):
    old_day = date(2026, 11, 12)
    write_snapshot(one_station(3), at(8, 0, old_day), tmp_path)
    roll_up_day(old_day, tmp_path)
    today = date.fromordinal(old_day.toordinal() + days_old)

    apply_retention(today, tmp_path)

    assert (tmp_path / "snapshots" / "2026-11-12").exists() == kept


def test_raw_day_is_never_deleted_without_its_hourly_summary(tmp_path):
    write_snapshot(one_station(3), at(8, 0), tmp_path)

    removed = apply_retention(date(2026, 12, 31), tmp_path)

    assert removed == []
    assert (tmp_path / "snapshots" / "2026-11-12").exists()


def test_maintain_rolls_up_finished_days_but_not_today(tmp_path):
    yesterday, today = date(2026, 11, 11), date(2026, 11, 12)
    write_snapshot(one_station(3), at(23, 50, yesterday), tmp_path)
    write_snapshot(one_station(4), at(0, 5, today), tmp_path)

    maintain(at(0, 5, today), tmp_path)

    assert hourly_path(yesterday, tmp_path).exists()
    assert not hourly_path(today, tmp_path).exists()
