"""One scheduled run: python -m collector.run"""
import logging
import sys
from datetime import datetime, timezone

from collector.config import DATA_DIR
from collector.fetch import SchemaError, fetch_feeds, info_frame, status_frame
from collector.http import HttpClient, HttpError
from collector.storage import write_snapshot, write_stations

log = logging.getLogger("collector")


def run(client, data_dir, now):
    info, status = fetch_feeds(client)
    write_stations(info_frame(info), now, data_dir)
    path = write_snapshot(status_frame(status, now), now, data_dir)

    for station_id, reason in info.rejected + status.rejected:
        log.warning("skipped station %s: %s", station_id, reason)
    return path


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        path = run(HttpClient(), DATA_DIR, datetime.now(timezone.utc))
    except (HttpError, SchemaError) as exc:
        # A non-zero exit turns the scheduled run red, so the failure is seen.
        log.error("collection failed: %s", exc)
        return 1
    log.info("wrote %s", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
