"""Partitioned files and retention."""
import os
from datetime import timezone

import pandas as pd

from collector.config import DATA_DIR, WINDOW_MINUTES


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


def _write_atomically(frame, path):
    # Write beside the target, then rename in one step. A job killed mid-write leaves
    # a stray .tmp that readers ignore, never a half-written .parquet.
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    frame.to_parquet(tmp, index=False)
    os.replace(tmp, path)
