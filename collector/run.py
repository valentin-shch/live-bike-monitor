"""One scheduled run: python -m collector.run"""
import logging
import sys
import time
from datetime import datetime, timezone

import pandas as pd

from collector.config import DATA_DIR
from collector.detect import EVENT_COLUMNS, detect_events, merge_events
from collector.fetch import SchemaError, fetch_feeds, info_frame, status_frame
from collector.http import HttpClient, HttpError
from collector.monitor import collection_events, read_runs, write_run
from collector.notify import configured_notifiers, pending_alerts, send_alerts
from collector.storage import (
    maintain,
    read_alerts_sent,
    read_all_snapshots,
    read_events,
    window_start,
    write_alerts_sent,
    write_events,
    write_snapshot,
    write_stations,
)
from collector.weather import update_weather

log = logging.getLogger("collector")


def collect(client, data_dir, now):
    info, status = fetch_feeds(client)
    write_stations(info_frame(info), now, data_dir)
    path = write_snapshot(status_frame(status, now), now, data_dir)
    log.info("wrote %s", path)

    for station_id, reason in info.rejected + status.rejected:
        log.warning("skipped station %s: %s", station_id, reason)

    # After the snapshot is safely written, so a maintenance problem cannot cost us this window.
    for day in maintain(now, data_dir):
        log.info("removed raw snapshots for %s (hourly roll-up kept)", day)

    weather = update_weather(client, now, data_dir)
    return {"stations": len(status.stations), "weather": weather}


def run(client, data_dir, now):
    """Collect, record what happened, then update events and alerts.

    The record and the events happen even when collection fails: a schema change must
    reach the run log and the alerts while it is going on, not after it is fixed.
    """
    started = time.monotonic()
    record = {
        "started_at": now, "window_utc": window_start(now), "outcome": "ok",
        "detail": "", "stations": 0, "weather": "skipped",
    }
    try:
        record.update(collect(client, data_dir, now))
    except HttpError as exc:
        record.update(outcome="feed_down", detail=str(exc))
    except SchemaError as exc:
        record.update(outcome="schema_error", detail=str(exc))
    except Exception as exc:
        # A bug, not a feed problem. Still recorded, so the run log has no silent holes.
        # log.exception also prints the traceback into the Actions log.
        log.exception("collection crashed")
        record.update(outcome="crashed", detail=repr(exc))
    if record["outcome"] != "ok":
        log.error("collection failed (%s): %s", record["outcome"], record["detail"])

    record["duration_s"] = round(time.monotonic() - started, 2)
    write_run(record, data_dir)
    update_events(client, data_dir, now)
    return record


def update_events(client, data_dir, now):
    snapshots = read_all_snapshots(data_dir)
    runs = read_runs(data_dir)
    # Everything is recomputed from the oldest raw window on; older history comes from the file.
    raw_start = snapshots["window_utc"].min() if not snapshots.empty else runs["window_utc"].min()
    runs = runs[runs["window_utc"] >= raw_start]

    parts = [p for p in (detect_events(snapshots), collection_events(runs)) if not p.empty]
    fresh = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=EVENT_COLUMNS)
    events = merge_events(read_events(data_dir), fresh, raw_start)
    write_events(events, data_dir)
    log.info("events: %d total, %d ongoing", len(events), events["ended_at"].isna().sum())

    notifiers = configured_notifiers(client)
    if notifiers:
        sent = read_alerts_sent(data_dir)
        new = send_alerts(pending_alerts(events, now), notifiers, sent, now)
        write_alerts_sent(pd.concat([sent, new], ignore_index=True), now, data_dir)
        log.info("alerts: %d sent via %s", len(new), ", ".join(n.name for n in notifiers))


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    record = run(HttpClient(), DATA_DIR, datetime.now(timezone.utc))
    # A non-zero exit turns the scheduled run red, so a failure is also seen on GitHub.
    # Weather problems do not count: the run log shows them, the bike data is fine.
    return 0 if record["outcome"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
