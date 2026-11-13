"""Partitioned files and retention."""
import logging
import os
import shutil
from datetime import date, timezone

import pandas as pd

from collector.config import DATA_DIR, RAW_RETENTION_DAYS, WINDOW_MINUTES

log = logging.getLogger(__name__)


def window_start(moment):
    # Folder and file names come from this, so a local time here would make the
    # October daylight-saving hour write two windows into one file.
    if moment.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware (UTC)")
    moment = moment.astimezone(timezone.utc)
    minute = moment.minute - moment.minute % WINDOW_MINUTES
    return moment.replace(minute=minute, second=0, microsecond=0)


def snapshot_path(window, data_dir=DATA_DIR):
    return data_dir / "snapshots" / f"{window:%Y-%m-%d}" / f"{window:%H%M}.parquet"


def write_snapshot(frame, fetched_at, data_dir=DATA_DIR):
    """Save one window's snapshot. A rerun in the same window replaces the file,
    so the window is a natural key and duplicates cannot happen."""
    window = window_start(fetched_at)
    path = snapshot_path(window, data_dir)
    _write_atomically(frame.assign(window_utc=window), path)
    return path


def write_stations(frame, fetched_at, data_dir=DATA_DIR):
    day = window_start(fetched_at)
    path = data_dir / "stations" / f"{day:%Y-%m-%d}.parquet"
    _write_atomically(frame, path)
    return path


def read_snapshots(day, data_dir=DATA_DIR):
    files = sorted((data_dir / "snapshots" / f"{day:%Y-%m-%d}").glob("*.parquet"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def hourly_path(day, data_dir=DATA_DIR):
    return data_dir / "hourly" / f"{day:%Y-%m-%d}.parquet"


def roll_up_day(day, data_dir=DATA_DIR):
    """Summarise one UTC day of raw snapshots into one row per station per hour."""
    raw = read_snapshots(day, data_dir)
    if raw.empty:
        return None

    raw = raw.assign(
        hour_utc=raw["window_utc"].dt.floor("h"),
        is_empty=raw["num_vehicles_available"] == 0,
        is_full=raw["num_docks_available"] == 0,
    )
    # The mean of a True/False column is the share of True values (True counts as 1).
    hourly = raw.groupby(["hour_utc", "station_id"], as_index=False).agg(
        n_snapshots=("window_utc", "count"),
        bikes_mean=("num_vehicles_available", "mean"),
        bikes_min=("num_vehicles_available", "min"),
        docks_mean=("num_docks_available", "mean"),
        empty_share=("is_empty", "mean"),
        full_share=("is_full", "mean"),
        renting_share=("is_renting", "mean"),
    )
    path = hourly_path(day, data_dir)
    _write_atomically(hourly, path)
    return path


def raw_days(data_dir=DATA_DIR):
    return sorted(date.fromisoformat(p.name) for p in (data_dir / "snapshots").glob("*") if p.is_dir())


def apply_retention(today, data_dir=DATA_DIR, keep_days=RAW_RETENTION_DAYS):
    removed = []
    for day in raw_days(data_dir):
        if (today - day).days <= keep_days:
            continue
        # Raw data is the only copy: never delete it before its summary is safely on disk.
        if not hourly_path(day, data_dir).exists():
            log.warning("keeping raw %s: no hourly roll-up yet", day)
            continue
        shutil.rmtree(data_dir / "snapshots" / f"{day:%Y-%m-%d}")
        removed.append(day)
    return removed


def maintain(now, data_dir=DATA_DIR):
    """Roll up every finished day that has no summary yet, then drop old raw data.

    Today is skipped because more snapshots are still coming. A window always belongs to
    the day of its fetch time, so once the UTC date changes, yesterday cannot get more files.
    """
    today = window_start(now).date()
    for day in raw_days(data_dir):
        if day < today and not hourly_path(day, data_dir).exists():
            roll_up_day(day, data_dir)
    return apply_retention(today, data_dir)


def _write_atomically(frame, path):
    # Write beside the target, then rename in one step. A job killed mid-write leaves
    # a stray .tmp that readers ignore, never a half-written .parquet.
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    frame.to_parquet(tmp, index=False)
    os.replace(tmp, path)
