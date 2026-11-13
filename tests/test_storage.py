from datetime import date, datetime, timedelta, timezone

import pandas as pd
import pytest

from collector.storage import read_snapshots, window_start, write_snapshot, write_stations

UTC = timezone.utc
MADRID_WINTER = timezone(timedelta(hours=1))


def small_snapshot(bikes):
    """Three hand-made stations; `bikes` sets station 1's count so runs can be told apart."""
    return pd.DataFrame(
        {
            "station_id": ["1", "2", "3"],
            "num_vehicles_available": [bikes, 0, 7],
            "num_docks_available": [10, 15, 3],
            "is_renting": [True, True, False],
        }
    )


@pytest.mark.parametrize(
    "moment, expected",
    [
        (datetime(2026, 11, 12, 1, 43, tzinfo=UTC), datetime(2026, 11, 12, 1, 30, tzinfo=UTC)),
        (datetime(2026, 11, 12, 1, 45, tzinfo=UTC), datetime(2026, 11, 12, 1, 45, tzinfo=UTC)),
        (datetime(2026, 11, 12, 1, 59, 59, tzinfo=UTC), datetime(2026, 11, 12, 1, 45, tzinfo=UTC)),
        # 02:43 in Madrid is 01:43 UTC: the window is always a UTC one.
        (datetime(2026, 11, 12, 2, 43, tzinfo=MADRID_WINTER), datetime(2026, 11, 12, 1, 30, tzinfo=UTC)),
    ],
)
def test_window_start_rounds_down_to_the_utc_quarter_hour(moment, expected):
    assert window_start(moment) == expected


def test_naive_timestamp_is_refused():
    with pytest.raises(ValueError):
        window_start(datetime(2026, 11, 12, 1, 43))


def test_snapshot_goes_to_day_folder_and_window_file(tmp_path):
    path = write_snapshot(small_snapshot(5), datetime(2026, 11, 12, 1, 43, tzinfo=UTC), tmp_path)

    assert path == tmp_path / "snapshots" / "2026-11-12" / "0130.parquet"


def test_late_evening_utc_stays_in_the_utc_day(tmp_path):
    # 23:50 UTC is already 00:50 on the 13th in Madrid; the folder follows UTC.
    path = write_snapshot(small_snapshot(5), datetime(2026, 11, 12, 23, 50, tzinfo=UTC), tmp_path)

    assert path.parent.name == "2026-11-12"


def test_rerun_in_the_same_window_replaces_instead_of_duplicating(tmp_path):
    write_snapshot(small_snapshot(5), datetime(2026, 11, 12, 1, 43, tzinfo=UTC), tmp_path)
    write_snapshot(small_snapshot(9), datetime(2026, 11, 12, 1, 44, tzinfo=UTC), tmp_path)

    stored = read_snapshots(date(2026, 11, 12), tmp_path)

    assert len(stored) == 3
    assert stored.loc[stored["station_id"] == "1", "num_vehicles_available"].item() == 9


def test_two_windows_give_two_snapshots(tmp_path):
    write_snapshot(small_snapshot(5), datetime(2026, 11, 12, 1, 43, tzinfo=UTC), tmp_path)
    write_snapshot(small_snapshot(9), datetime(2026, 11, 12, 1, 52, tzinfo=UTC), tmp_path)

    stored = read_snapshots(date(2026, 11, 12), tmp_path)

    assert len(stored) == 6
    assert stored["window_utc"].nunique() == 2


def test_leftover_tmp_file_is_ignored_by_the_reader(tmp_path):
    write_snapshot(small_snapshot(5), datetime(2026, 11, 12, 1, 43, tzinfo=UTC), tmp_path)
    (tmp_path / "snapshots" / "2026-11-12" / "0145.tmp").write_bytes(b"half-written")

    assert len(read_snapshots(date(2026, 11, 12), tmp_path)) == 3


def test_reading_a_day_with_no_data_gives_an_empty_table(tmp_path):
    assert read_snapshots(date(2026, 11, 12), tmp_path).empty


def test_stations_file_is_one_per_utc_day(tmp_path):
    path = write_stations(small_snapshot(5), datetime(2026, 11, 12, 23, 50, tzinfo=UTC), tmp_path)

    assert path == tmp_path / "stations" / "2026-11-12.parquet"
