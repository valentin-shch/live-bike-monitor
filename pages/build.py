"""Builds the static status page from the collected history:  python -m pages.build

Writes _site/ (index.html plus its assets), which the workflow publishes to GitHub Pages.
It reads the same files as the API, through the same Repository.
"""
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape
from plotly.offline import get_plotlyjs

from api.data import Repository, station_order
from collector.config import DATA_DIR, DISPLAY_TZ, FRESH_FOR, REPO_ROOT
from collector.monitor import coverage, read_runs, window_report
from collector.storage import window_start

HERE = Path(__file__).parent
OUT_DIR = REPO_ROOT / "_site"
TZ = ZoneInfo(DISPLAY_TZ)
UPTIME_DAYS = 7
MAX_CARDS = 40

# One letter per station per window keeps the 24-hour time-lapse small:
# 545 stations x 96 windows is about 52 KB of letters instead of megabytes of JSON.
# "u" = unknown: the station had no row in that window (like the nightly 41).
STATE_CODES = {"ok": "o", "empty": "e", "full": "f", "offline": "x", "retired": "r"}

FEED_NAMES = {
    "freshness": "Bicing feed",
    "station_list": "Station list",
    "collection": "Collector",
    "weather": "Weather feed",
}
STATE_WORDS = {
    "empty": "empty",
    "full": "full",
    "offline": "offline",
    "stale": "not updating",
    "missing": "missing stations",
    "feed_down": "not answering",
    "schema_error": "changed format",
    "crashed": "crashing",
    "weather_down": "not answering",
}


# ---------- small formatting helpers ----------

def format_duration(delta):
    """1h 40m, 25m, 2d 3h: the shape the brief asks for, short enough for a phone."""
    minutes = max(0, int(delta.total_seconds() // 60))
    days, rest = divmod(minutes, 24 * 60)
    hours, mins = divmod(rest, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def local_time(moment, now):
    """Madrid time. The day is added only when it is not today, so most cards stay short."""
    local, today = moment.astimezone(TZ), now.astimezone(TZ)
    if local.date() == today.date():
        return local.strftime("%H:%M")
    if (today.date() - local.date()).days < 7:
        return local.strftime("%a %H:%M")
    return local.strftime("%d %b %H:%M")


# ---------- the sections ----------

def event_cards(events, names, now, window=timedelta(hours=24), limit=MAX_CARDS):
    """Plain-language log entries, newest change first.

    Ongoing feed problems are pinned on top: they explain everything below them.
    Retired stations are left out: a station dead for months is a fact, not news.
    Returns (cards, how many more there were).
    """
    events = events[events["state"].isin(STATE_WORDS.keys())].copy()
    ongoing = events["ended_at"].isna()
    recent = ongoing | (events["ended_at"] >= now - window)
    events = events[recent].assign(
        last_change=events["ended_at"].fillna(events["started_at"]),
        pinned=ongoing & (events["scope"] == "feed"),
    )
    events = events.sort_values(["pinned", "last_change"], ascending=[False, False])

    cards = []
    for e in events.itertuples(index=False):
        is_station = e.scope == "station"
        who = f"Station {e.subject}" if is_station else FEED_NAMES.get(e.subject, e.subject)
        word = STATE_WORDS[e.state]
        if pd.isna(e.ended_at):
            text = f"{who} {word} since {local_time(e.started_at, now)}"
            took = format_duration(now - e.started_at)
        else:
            text = f"{who} was {word} {local_time(e.started_at, now)}–{local_time(e.ended_at, now)}"
            took = format_duration(e.ended_at - e.started_at)
        cards.append(
            {
                "text": text,
                "duration": took,
                "place": names.get(e.subject) if is_station else None,
                "state": e.state,
                "ongoing": pd.isna(e.ended_at),
            }
        )
    return cards[:limit], max(0, len(cards) - limit)


def timelapse(recent, info):
    """Everything the map needs, in a compact shape: one entry per station, one letter
    and one bike count per window."""
    windows = sorted(recent["window_utc"].unique())
    placed = info.dropna(subset=["lat", "lon"]).set_index("station_id")
    # Only stations we can place on the map; same order as the API (numbers as numbers).
    ids = pd.Series(sorted(set(recent["station_id"]) & set(placed.index)))
    ids = ids.sort_values(key=station_order).tolist()

    states = recent.pivot(index="station_id", columns="window_utc", values="state").reindex(
        index=ids, columns=windows
    )
    bikes = recent.pivot(index="station_id", columns="window_utc", values="num_vehicles_available").reindex(
        index=ids, columns=windows
    )
    return {
        "windows": [pd.Timestamp(w).isoformat() for w in windows],
        "stations": [
            {
                "id": sid,
                "name": placed.at[sid, "name"],
                "lat": round(float(placed.at[sid, "lat"]), 5),
                "lon": round(float(placed.at[sid, "lon"]), 5),
                "capacity": None if pd.isna(placed.at[sid, "capacity"]) else int(placed.at[sid, "capacity"]),
            }
            for sid in ids
        ],
        "states": ["".join(STATE_CODES.get(s, "u") if isinstance(s, str) else "u" for s in row) for row in states.to_numpy()],
        "bikes": [[None if pd.isna(b) else int(b) for b in row] for row in bikes.to_numpy()],
    }


def status(snapshot, events, runs, now):
    """The header: is it live, how fresh, how reliable over the last 7 days."""
    if snapshot is None:
        return {"level": "down", "label": "No data yet", "last_fetch_utc": None, "uptime": None}

    last_fetch = pd.Timestamp(snapshot["fetched_at"].max()).to_pydatetime()
    ongoing_feed = events[(events["scope"] == "feed") & events["ended_at"].isna()]
    serious = ongoing_feed[ongoing_feed["subject"].isin(["freshness", "collection"])]
    if now - last_fetch > FRESH_FOR:
        level, label = "down", "Not updating"
    elif not serious.empty:
        level, label = "degraded", f"{FEED_NAMES[serious['subject'].iloc[0]]} {STATE_WORDS[serious['state'].iloc[0]]}"
    else:
        level, label = "live", "Live"

    uptime = None
    if not runs.empty:
        end = window_start(now)
        start = max(window_start(now - timedelta(days=UPTIME_DAYS)), runs["window_utc"].min())
        counts = coverage(window_report(runs, start, end))
        uptime = {
            **counts,
            "share": counts["ok"] / counts["expected"] if counts["expected"] else None,
            "since": local_time(pd.Timestamp(start).to_pydatetime(), now),
            "full_week": start <= window_start(now - timedelta(days=UPTIME_DAYS)),
        }
    return {
        "level": level,
        "label": label,
        "last_fetch_utc": last_fetch.isoformat(),
        "last_fetch_local": local_time(last_fetch, now),
        "uptime": uptime,
    }


def headline(snapshot):
    """The finding for the first screen: how many working stations are empty or full now."""
    if snapshot is None:
        return None
    working = snapshot[snapshot["state"] != "retired"]
    counts = working["state"].value_counts()
    return {
        "working": len(working),
        "empty": int(counts.get("empty", 0)),
        "full": int(counts.get("full", 0)),
        "offline": int(counts.get("offline", 0)),
        "retired": len(snapshot) - len(working),
    }


# ---------- putting it together ----------

def safe_json(value):
    """JSON that can sit inside a <script> tag. A station name containing "</script>"
    would otherwise end the tag early and let the rest run as HTML: a classic injection."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def site_context(data_dir, now):
    repo = Repository(data_dir)
    snapshot = repo.latest_snapshot()
    events = repo.events()
    runs = read_runs(data_dir)
    info = repo.station_info()
    names = dict(zip(info["station_id"], info["name"]))

    found = repo.recent(hours=24)
    data = {"fresh_for_ms": int(FRESH_FOR.total_seconds() * 1000)}
    if found is not None:
        data.update(timelapse(found[0], info))
    head = status(snapshot, events, runs, now)
    data["last_fetch_utc"] = head["last_fetch_utc"]
    cards, more = event_cards(events, names, now)
    return {
        "status": head,
        "headline": headline(snapshot),
        "cards": cards,
        "more_cards": more,
        "built_local": local_time(now, now),
        "data_json": safe_json(data),
    }


def render(context):
    env = Environment(
        loader=FileSystemLoader(HERE / "templates"),
        # Every value is HTML-escaped unless marked safe: a station called "<b>" stays text.
        autoescape=select_autoescape(["html"]),
    )
    return env.get_template("index.html").render(**context)


def build(data_dir=DATA_DIR, out_dir=OUT_DIR, now=None):
    now = now or datetime.now(timezone.utc)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(render(site_context(data_dir, now)), encoding="utf-8")
    for asset in ("site.css", "site.js"):
        shutil.copy(HERE / "static" / asset, out_dir / asset)
    # Served from our own site: same version as the Python package, and no third-party
    # request from the visitor's browser.
    (out_dir / "plotly.min.js").write_text(get_plotlyjs(), encoding="utf-8")
    return out_dir / "index.html"


if __name__ == "__main__":
    print(f"wrote {build()}")
