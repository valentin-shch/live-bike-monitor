"""Read-only API over the collected history.

Run locally:  uvicorn api.main:app --port 8000   then open http://localhost:8000/docs
It reads API_DATA_DIR if set (a folder with the data branch checked out), else data/.
"""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import AwareDatetime

from api.data import Repository, as_records, station_order
from api.models import (
    EmptyByHour,
    Event,
    EventState,
    Health,
    HourShare,
    Page,
    Problem,
    Station,
    StationDetail,
    StationState,
)
from collector.config import DATA_DIR, DISPLAY_TZ

# Runs are every 15 minutes and GitHub often starts them late. Two missed windows plus
# a late start still counts as fresh; beyond that, something is wrong with the collector.
FRESH_FOR = timedelta(minutes=45)

Limit = Annotated[int, Query(ge=1, le=200, description="Items per page")]
Offset = Annotated[int, Query(ge=0, description="Items to skip")]


def _page(frame, limit, offset):
    return {
        "items": as_records(frame.iloc[offset : offset + limit]),
        "total": len(frame),
        "limit": limit,
        "offset": offset,
    }


def _station(row, as_of):
    return {
        "station_id": row["station_id"],
        "name": row.get("name"),
        "lat": row.get("lat"),
        "lon": row.get("lon"),
        "capacity": row.get("capacity"),
        "state": row["state"],
        "bikes": row["num_vehicles_available"],
        "docks": row["num_docks_available"],
        "last_reported": row["last_reported"],
        "as_of_utc": as_of,
    }


def create_app(data_dir=None, clock=lambda: datetime.now(timezone.utc)):
    repo = Repository(Path(data_dir or os.environ.get("API_DATA_DIR") or DATA_DIR))
    app = FastAPI(
        title="Live bike monitor API",
        version="1.0.0",
        description="Read-only access to Barcelona Bicing station history collected every "
        "15 minutes. Station data: Bicing, Ajuntament de Barcelona.",
    )

    @app.get("/health", response_model=Health, summary="Is the API up, and is the data fresh?")
    def health():
        snapshot = repo.latest_snapshot()
        events = repo.events()
        ongoing = int(events["ended_at"].isna().sum())
        if snapshot is None:
            return Health(status="ok", data="no_data", last_snapshot_utc=None,
                          minutes_since_last_snapshot=None, stations=0, ongoing_events=ongoing)
        fetched = pd.Timestamp(snapshot["fetched_at"].max()).to_pydatetime()
        age = clock() - fetched
        return Health(
            status="ok",
            data="fresh" if age <= FRESH_FOR else "stale",
            last_snapshot_utc=fetched,
            minutes_since_last_snapshot=round(age.total_seconds() / 60, 1),
            stations=len(snapshot),
            ongoing_events=ongoing,
        )

    @app.get("/stations", response_model=Page[Station], summary="Current state of every station")
    def list_stations(state: StationState | None = None, limit: Limit = 50, offset: Offset = 0):
        stations = repo.current_stations()
        if stations is None:
            return Page[Station](items=[], total=0, limit=limit, offset=offset)
        if state is not None:
            stations = stations[stations["state"] == state]
        stations = stations.sort_values("station_id", key=station_order)
        page = _page(stations, limit, offset)
        page["items"] = [_station(row, row["window_utc"]) for row in page["items"]]
        return page

    @app.get(
        "/stations/{station_id}",
        response_model=StationDetail,
        responses={404: {"model": Problem, "description": "Not seen in the last 24 h of data"}},
        summary="One station now, plus its last 24 h",
    )
    def get_station(station_id: str):
        found = repo.recent()
        rows = None if found is None else found[0][found[0]["station_id"] == station_id]
        if rows is None or rows.empty:
            raise HTTPException(status_code=404, detail=f"station {station_id} not found")
        recent, latest = found

        rows = rows.sort_values("window_utc")
        info = repo.station_info()
        info = info[info["station_id"] == station_id]
        current = as_records(rows.tail(1).merge(info, on="station_id", how="left"))[0]
        if current["window_utc"] != latest:
            current["state"] = "unknown"  # seen recently, but not in the latest snapshot
        detail = _station(current, latest)
        detail["history"] = [
            {"window_utc": r["window_utc"], "bikes": r["num_vehicles_available"],
             "docks": r["num_docks_available"], "state": r["state"]}
            for r in as_records(rows)
        ]
        return detail

    @app.get("/events", response_model=Page[Event], summary="Episodes, newest first")
    def list_events(
        type_: Annotated[EventState | None, Query(alias="type", description="Event state")] = None,
        station: Annotated[str | None, Query(description="Only this station's events")] = None,
        since: Annotated[
            AwareDatetime | None,
            Query(description="Only episodes still going on at or after this time, "
                  "with a timezone, e.g. 2026-11-12T08:00Z"),
        ] = None,
        limit: Limit = 50,
        offset: Offset = 0,
    ):
        events = repo.events()
        if type_ is not None:
            events = events[events["state"] == type_]
        if station is not None:
            events = events[(events["scope"] == "station") & (events["subject"] == station)]
        if since is not None:
            events = events[events["ended_at"].isna() | (events["ended_at"] >= since)]
        return _page(events.sort_values("started_at", ascending=False), limit, offset)

    @app.get("/stats/empty-by-hour", response_model=EmptyByHour,
             summary="How often stations are empty, by hour of day")
    def empty_by_hour():
        hourly = repo.hourly()
        empty_hours = [HourShare(hour=h, empty_share=None, station_hours=0) for h in range(24)]
        if hourly.empty:
            return EmptyByHour(timezone=DISPLAY_TZ, days=0, first_day=None, last_day=None,
                               hours=empty_hours)
        # Only station-hours that were renting the whole hour: a closed station with 0 bikes
        # is not "empty" for a rider (the stage 1 denominator lesson).
        renting = hourly[hourly["renting_share"] == 1]
        local_hour = renting["hour_utc"].dt.tz_convert(DISPLAY_TZ).dt.hour
        stats = renting.groupby(local_hour)["empty_share"].agg(["mean", "count"])
        days = hourly["hour_utc"].dt.date
        return EmptyByHour(
            timezone=DISPLAY_TZ,
            days=days.nunique(),
            first_day=days.min(),
            last_day=days.max(),
            hours=[
                HourShare(hour=h, empty_share=round(float(stats.at[h, "mean"]), 4),
                          station_hours=int(stats.at[h, "count"]))
                if h in stats.index else empty_hours[h]
                for h in range(24)
            ],
        )

    return app


app = create_app()
