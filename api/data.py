"""Reads the collected files for the API. Nothing here writes: the API looks at the data,
it is not part of producing it."""
from datetime import timedelta

import pandas as pd

from collector.detect import classify
from collector.storage import read_events, read_snapshots


def station_order(ids):
    """Sort key: numeric ids as numbers (2 before 10), so pages are stable and readable."""
    return pd.to_numeric(ids, errors="coerce")


def as_records(frame):
    """DataFrame rows as dicts, with pandas' missing values (NaN, NaT) turned into None,
    which is what JSON and Pydantic understand."""
    return frame.astype(object).where(frame.notna(), None).to_dict("records")


class Repository:
    def __init__(self, data_dir):
        self.data_dir = data_dir

    def _snapshot_files(self):
        # Folder and file names are YYYY-MM-DD/HHMM, so sorting the paths sorts by time.
        return sorted((self.data_dir / "snapshots").glob("*/*.parquet"))

    def latest_snapshot(self):
        files = self._snapshot_files()
        return classify(pd.read_parquet(files[-1])) if files else None

    def station_info(self):
        files = sorted((self.data_dir / "stations").glob("*.parquet"))
        if not files:
            return pd.DataFrame(columns=["station_id", "name", "lat", "lon", "capacity"])
        return pd.read_parquet(files[-1])[["station_id", "name", "lat", "lon", "capacity"]]

    def current_stations(self):
        """Every station in the latest snapshot, with its name and place."""
        snapshot = self.latest_snapshot()
        if snapshot is None:
            return None
        return snapshot.merge(self.station_info(), on="station_id", how="left")

    def recent(self, hours=24):
        """All snapshots in the last `hours` of DATA (not of the clock): if the collector
        stopped yesterday, this is still yesterday's last day, not nothing."""
        files = self._snapshot_files()
        if not files:
            return None
        latest = pd.read_parquet(files[-1])["window_utc"].iloc[0]
        days = {(latest - timedelta(hours=hours)).date(), latest.date()}
        frames = [read_snapshots(day, self.data_dir) for day in sorted(days)]
        recent = pd.concat([f for f in frames if not f.empty], ignore_index=True)
        recent = recent[recent["window_utc"] > latest - timedelta(hours=hours)]
        return classify(recent), latest

    def events(self):
        events = read_events(self.data_dir)
        for col in ("started_at", "ended_at"):
            events[col] = pd.to_datetime(events[col], utc=True)
        return events

    def hourly(self):
        files = sorted((self.data_dir / "hourly").glob("*.parquet"))
        if not files:
            return pd.DataFrame()
        return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
