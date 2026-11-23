"""Pydantic response models. They are the contract: FastAPI checks every answer against
them and writes them into the OpenAPI document."""
from datetime import date, datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

# "unknown": seen in the last 24 h but not in the latest snapshot (the nightly 41).
StationState = Literal["ok", "empty", "full", "offline", "retired", "unknown"]
EventState = Literal[
    "empty", "full", "offline", "retired", "stale", "missing", "feed_down", "schema_error", "crashed",
    "weather_down",
]

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """One page of a longer list. total says how many there are in all."""

    items: list[T]
    total: int = Field(description="Number of items across all pages")
    limit: int
    offset: int


class Health(BaseModel):
    status: Literal["ok"] = Field(description="The API itself is answering")
    data: Literal["fresh", "stale", "no_data"] = Field(
        description="Whether the collector is keeping the data up to date"
    )
    last_snapshot_utc: datetime | None
    minutes_since_last_snapshot: float | None
    stations: int
    ongoing_events: int


class Station(BaseModel):
    station_id: str
    name: str | None
    lat: float | None
    lon: float | None
    capacity: int | None
    state: StationState
    bikes: int | None
    docks: int | None
    last_reported: datetime | None
    as_of_utc: datetime = Field(description="Window of the snapshot these numbers come from")


class HistoryPoint(BaseModel):
    window_utc: datetime
    bikes: int
    docks: int
    state: StationState


class StationDetail(Station):
    history: list[HistoryPoint] = Field(description="Every snapshot of the last 24 h of data")


class Event(BaseModel):
    scope: Literal["station", "feed"]
    subject: str = Field(
        description="Station id, or the feed check: freshness, station_list, collection, weather"
    )
    state: EventState
    started_at: datetime
    ended_at: datetime | None = Field(description="Missing while the episode is still going on")
    ended_by: Literal["change", "gap"] | None = Field(
        default=None,
        description='"change": the state was seen changing. "gap": our data stopped for over an '
        "hour, so ended_at is the last reading that still showed this state",
    )


class HourShare(BaseModel):
    hour: int = Field(ge=0, le=23, description="Hour of day in Madrid time")
    empty_share: float | None = Field(description="Share of renting station-hours that were empty")
    station_hours: int


class EmptyByHour(BaseModel):
    timezone: str
    days: int
    first_day: date | None
    last_day: date | None
    hours: list[HourShare]


class Problem(BaseModel):
    detail: str
