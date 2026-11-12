"""Fetch the GBFS feeds, validate them, turn them into tables."""
from dataclasses import dataclass
from datetime import datetime

import pandas as pd
from pydantic import BaseModel, Field, ValidationError

from collector.config import GBFS_DISCOVERY_URL, MAX_INVALID_SHARE


class SchemaError(Exception):
    pass


class FeedLink(BaseModel):
    name: str
    url: str


class DiscoveryData(BaseModel):
    feeds: list[FeedLink]


class Discovery(BaseModel):
    data: DiscoveryData


# Stations stay raw dicts here and are validated one by one, so one bad station
# does not throw away the other 500.
class StationList(BaseModel):
    stations: list[dict]


class Envelope(BaseModel):
    last_updated: datetime
    data: StationList


class LocalizedText(BaseModel):
    text: str
    language: str


# Only the fields we use. The feed sends more; Pydantic ignores them, so dropping
# a field we never read does not break collection.
class StationInfo(BaseModel):
    station_id: str
    name: list[LocalizedText] = Field(min_length=1)
    lat: float
    lon: float
    capacity: int = Field(ge=0)
    post_code: str | None = None


class StationStatus(BaseModel):
    station_id: str
    num_vehicles_available: int = Field(ge=0)
    num_docks_available: int = Field(ge=0)
    is_installed: bool
    is_renting: bool
    is_returning: bool
    last_reported: datetime


@dataclass
class FeedResult:
    last_updated: datetime
    stations: list
    rejected: list  # (station_id, reason) pairs, for the event log


def fetch_feeds(client, discovery_url=GBFS_DISCOVERY_URL):
    discovery = _parse(Discovery, client.get_json(discovery_url), "gbfs")
    urls = {link.name: link.url for link in discovery.data.feeds}

    info_url = _feed_url(urls, "station_information")
    status_url = _feed_url(urls, "station_status")
    info = _parse_stations(StationInfo, client.get_json(info_url), "station_information")
    status = _parse_stations(StationStatus, client.get_json(status_url), "station_status")
    return info, status


def info_frame(info):
    rows = [
        {
            "station_id": s.station_id,
            "name": _english(s.name),
            "lat": s.lat,
            "lon": s.lon,
            "capacity": s.capacity,
            "post_code": s.post_code,
        }
        for s in info.stations
    ]
    return pd.DataFrame(rows)


def status_frame(status, fetched_at):
    frame = pd.DataFrame([s.model_dump() for s in status.stations])
    frame["feed_last_updated"] = status.last_updated
    frame["fetched_at"] = fetched_at
    return frame


def _feed_url(urls, name):
    if name not in urls:
        raise SchemaError(f"gbfs: no {name} feed listed")
    return urls[name]


def _parse(model, payload, feed_name):
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise SchemaError(f"{feed_name}: {exc}") from exc


def _parse_stations(model, payload, feed_name):
    envelope = _parse(Envelope, payload, feed_name)
    raw_stations = envelope.data.stations

    good, rejected = [], []
    for raw in raw_stations:
        try:
            good.append(model.model_validate(raw))
        except ValidationError as exc:
            rejected.append((raw.get("station_id"), _first_problem(exc)))

    if len(rejected) > MAX_INVALID_SHARE * len(raw_stations):
        raise SchemaError(
            f"{feed_name}: {len(rejected)} of {len(raw_stations)} stations invalid, "
            f"first: {rejected[0][1]}"
        )
    return FeedResult(envelope.last_updated, good, rejected)


def _first_problem(exc):
    error = exc.errors()[0]
    field = ".".join(str(part) for part in error["loc"])
    return f"{field}: {error['msg']}"


def _english(names):
    for name in names:
        if name.language == "en":
            return name.text
    return names[0].text
