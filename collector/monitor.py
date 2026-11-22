"""Self-monitoring: what every run did, and which windows have no data."""
import pandas as pd

from collector.config import DATA_DIR, WINDOW_MINUTES
from collector.detect import EVENT_COLUMNS, confirmed_episodes
from collector.storage import write_atomically

# outcome: ok, feed_down (HttpError), schema_error (SchemaError) or crashed (a bug).
RUN_COLUMNS = ["started_at", "window_utc", "outcome", "detail", "stations", "weather", "duration_s"]


def runs_path(day, data_dir=DATA_DIR):
    return data_dir / "runs" / f"{day:%Y-%m-%d}.parquet"


def write_run(record, data_dir=DATA_DIR):
    """Add one row per run. Runs are events, not state: every run is kept, a manual rerun
    in the same window too. (Snapshots are the other way round: one per window.)"""
    path = runs_path(record["started_at"], data_dir)
    row = pd.DataFrame([record], columns=RUN_COLUMNS)
    if path.exists():
        row = pd.concat([pd.read_parquet(path), row], ignore_index=True)
    write_atomically(row, path)
    return path


def read_runs(data_dir=DATA_DIR):
    files = sorted((data_dir / "runs").glob("*.parquet"))
    if not files:
        return pd.DataFrame(columns=RUN_COLUMNS)
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def _last_run_per_window(runs):
    # A manual rerun usually fixes something, so the last run in a window decides
    # (the same rule as snapshot files: last write wins).
    return runs.sort_values("started_at").drop_duplicates("window_utc", keep="last")


def window_report(runs, start, end):
    """One row per expected window from start to end: ok, failed, or missed.

    "missed" means no run at all. GitHub's scheduler is best-effort: a run can be skipped,
    or start so late that it lands in the NEXT window, which leaves this one empty.
    """
    expected = pd.date_range(start, end, freq=f"{WINDOW_MINUTES}min")
    last = _last_run_per_window(runs).set_index("window_utc")
    report = pd.DataFrame(index=pd.Index(expected, name="window_utc")).join(
        last[["outcome", "started_at"]]
    )
    report["status"] = report["outcome"].map(lambda o: "ok" if o == "ok" else "failed")
    report.loc[report["outcome"].isna(), "status"] = "missed"
    # Minutes between the window opening and the run starting. Cron says :04, so 4 is on time.
    delay = pd.to_datetime(report["started_at"], utc=True) - report.index.to_series()
    report["delay_min"] = (delay.dt.total_seconds() / 60).round(1)
    return report.reset_index()[["window_utc", "status", "outcome", "delay_min"]]


def collection_events(runs):
    """Failed collections as feed events (subject "collection"), with the same debounce as
    everything else: one failed run is a blip, two in a row is an episode.

    This is where a schema change becomes visible. A failed run writes no snapshot, so
    detect.py never sees it; only the run log knows.
    """
    if runs.empty:
        return pd.DataFrame(columns=EVENT_COLUMNS)
    last = _last_run_per_window(runs)
    states = pd.DataFrame(
        {"check": "collection", "window_utc": last["window_utc"], "state": last["outcome"]}
    )
    episodes = confirmed_episodes(states, key="check")
    return episodes.rename(columns={"check": "subject"}).assign(scope="feed")[EVENT_COLUMNS]


def weather_events(runs):
    """Failed weather calls as a feed event (subject "weather", state "weather_down").

    Only runs that actually called Open-Meteo count: "not_due" and "skipped" rows say
    nothing about the weather service, so they are left out, like a skipped run.
    No alert: the bikes are still collected and the gap heals itself. The site shows it.
    """
    called = runs[runs["weather"].isin(["ok", "failed"])]
    if called.empty:
        return pd.DataFrame(columns=EVENT_COLUMNS)
    last = _last_run_per_window(called)
    states = pd.DataFrame(
        {
            "check": "weather",
            "window_utc": last["window_utc"],
            "state": last["weather"].map({"ok": "ok", "failed": "weather_down"}),
        }
    )
    episodes = confirmed_episodes(states, key="check")
    return episodes.rename(columns={"check": "subject"}).assign(scope="feed")[EVENT_COLUMNS]


def coverage(report):
    """Counts for the health section: how many windows we expected and what happened."""
    counts = report["status"].value_counts()
    return {
        "expected": len(report),
        **{status: int(counts.get(status, 0)) for status in ("ok", "failed", "missed")},
    }
