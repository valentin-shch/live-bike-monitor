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

from api.data import Repository, renting_hours, station_order
from collector.config import DATA_DIR, DISPLAY_TZ, FRESH_FOR, REPO_ROOT
from collector.monitor import coverage, read_runs, window_report
from collector.storage import window_start

HERE = Path(__file__).parent
OUT_DIR = REPO_ROOT / "_site"
API_DIR = REPO_ROOT / "api"
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
            if getattr(e, "ended_by", "change") == "gap":
                text += ", then no data"  # the last reading we have, not a recovery
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


WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def empty_heatmap(hourly):
    """Share of working stations empty, by Madrid weekday (rows) and hour (columns).

    The title states the finding (the peak), and the caption says how many days each
    weekday rests on: with a few weeks of data, one odd Tuesday moves a whole row.
    """
    if hourly.empty:
        return None
    rows = renting_hours(hourly)
    if rows.empty:
        return None
    grid = rows.pivot_table(index="weekday", columns="local_hour", values="empty_share", aggfunc="mean")
    grid = grid.reindex(index=range(7), columns=range(24))
    days = rows.groupby("weekday")["local_day"].nunique().reindex(range(7), fill_value=0)

    cells = grid.stack().dropna()
    (peak_day, peak_hour), peak = cells.idxmax(), cells.max()
    (low_day, low_hour), low = cells.idxmin(), cells.min()
    covered = days[days > 0]
    return {
        "title": f"Stations run dry most on {WEEKDAYS[peak_day]}s around {peak_hour:02d}:00",
        "caption": (
            f"{peak:.0%} of working stations empty then, against {low:.0%} on "
            f"{WEEKDAYS[low_day]}s at {low_hour:02d}:00. "
            f"Based on {rows['local_day'].nunique()} days: each weekday rests on "
            f"{covered.min()}–{covered.max()} of them, so this is a hint, not proof."
        ),
        "z": [[None if pd.isna(v) else round(float(v) * 100, 1) for v in row] for row in grid.to_numpy()],
        "weekdays": [d[:3] for d in WEEKDAYS],
        "peak": {"weekday": int(peak_day), "hour": int(peak_hour), "value": round(float(peak) * 100, 1)},
        "max": round(float(peak) * 100, 1),
    }


def health_section(runs, events, now, days=UPTIME_DAYS):
    """Expected vs actual runs, the gaps, how late GitHub starts us, and feed incidents."""
    if runs.empty:
        return None
    end = window_start(now)
    start = max(window_start(now - timedelta(days=days)), runs["window_utc"].min())
    report = window_report(runs, start, end)
    local = report["window_utc"].dt.tz_convert(TZ)
    report = report.assign(local_day=local.dt.date, slot=local.dt.hour * 4 + local.dt.minute // 15)

    letters = {"ok": "o", "failed": "f", "missed": "m"}
    strips = []
    for day, rows in report.groupby("local_day"):
        # 96 slots per Madrid day, placed by clock time, so a partial first day lines up.
        # On the two daylight-saving days a slot can hold two windows; the later one shows.
        cells = ["n"] * 96
        for slot, status_ in zip(rows["slot"], rows["status"]):
            cells[slot] = letters[status_]
        ok = int((rows["status"] == "ok").sum())
        strips.append({"label": pd.Timestamp(day).strftime("%a %d"), "cells": cells, "ok": ok, "expected": len(rows)})

    # Gaps: runs of consecutive windows that were not collected.
    bad = report["status"] != "ok"
    gap_id = (bad != bad.shift()).cumsum()
    gaps = []
    for _, rows in report[bad].groupby(gap_id[bad]):
        first, last = rows["window_utc"].iloc[0], rows["window_utc"].iloc[-1]
        missed, failed = int((rows["status"] == "missed").sum()), int((rows["status"] == "failed").sum())
        reasons = ", ".join(p for p in (f"{missed} missed" if missed else "", f"{failed} failed" if failed else "") if p)
        gaps.append(
            {
                "when": f"{local_time(first.to_pydatetime(), now)}–{local_time((last + timedelta(minutes=15)).to_pydatetime(), now)}",
                "windows": len(rows),
                "reasons": reasons,
                "start": first,
            }
        )
    gaps = sorted(gaps, key=lambda g: (g["windows"], g["start"]), reverse=True)[:5]

    # Cron says :04, :19, :34, :49, so a run 4 minutes into its window is on time.
    late = (report.loc[report["status"] == "ok", "delay_min"] - 4).clip(lower=0)
    incidents, more = event_cards(events[events["scope"] == "feed"], {}, now, window=timedelta(days=days), limit=10)
    counts = coverage(report)
    return {
        "strips": strips,
        "gaps": gaps,
        "counts": counts,
        "late_median": None if late.empty else round(float(late.median())),
        "late_p90": None if late.empty else round(float(late.quantile(0.9))),
        "incidents": incidents,
        "more_incidents": more,
    }


# ---------- the API reference page ----------

# One real request per endpoint; the answers are saved from a local run into api/examples/.
EXAMPLES = {
    "/health": ("/health", "health.json"),
    "/stations": ("/stations?state=empty&limit=5", "stations_empty.json"),
    "/stations/{station_id}": ("/stations/12", "station_12.json"),
    "/events": ("/events?type=missing&limit=5", "events_missing.json"),
    "/stats/empty-by-hour": ("/stats/empty-by-hour", "empty_by_hour.json"),
}
SAMPLE_LINES = 40


def type_label(schema):
    """A short human type for a parameter, from its OpenAPI schema."""
    if "anyOf" in schema:
        return " or ".join(type_label(s) for s in schema["anyOf"] if s.get("type") != "null")
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if "enum" in schema:
        return " | ".join(str(v) for v in schema["enum"])
    return schema.get("format", schema.get("type", "any"))


def rules(schema):
    low, high = schema.get("minimum"), schema.get("maximum")
    if low is not None and high is not None:
        return f"{low}–{high}"
    if low is not None:
        return f"≥ {low}"
    return ""


def api_reference(openapi, examples_dir):
    endpoints = []
    for path, methods in openapi["paths"].items():
        for method, op in methods.items():
            query, sample_file = EXAMPLES.get(path, (path, None))
            sample = None
            if sample_file and (examples_dir / sample_file).exists():
                pretty = json.dumps(
                    json.loads((examples_dir / sample_file).read_text(encoding="utf-8")),
                    indent=2, ensure_ascii=False,
                ).splitlines()
                sample = "\n".join(pretty[:SAMPLE_LINES] + (["  …"] if len(pretty) > SAMPLE_LINES else []))
            endpoints.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "summary": op.get("summary", ""),
                    "params": [
                        {
                            "name": p["name"],
                            "where": p["in"],
                            "type": type_label(p["schema"]),
                            "rules": rules(p["schema"]),
                            "required": p.get("required", False),
                            "description": p.get("description", p["schema"].get("description", "")),
                        }
                        for p in op.get("parameters", [])
                    ],
                    "responses": [(code, r.get("description", "")) for code, r in op["responses"].items()],
                    "curl": f'curl "http://localhost:8000{query}"',
                    "sample": sample,
                }
            )
    return {"title": openapi["info"]["title"], "version": openapi["info"]["version"], "endpoints": endpoints}


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
    heatmap = empty_heatmap(repo.hourly())
    data["heatmap"] = heatmap
    cards, more = event_cards(events, names, now)
    return {
        "status": head,
        "headline": headline(snapshot),
        "cards": cards,
        "more_cards": more,
        "heatmap": heatmap,
        "health": health_section(runs, events, now),
        "built_local": local_time(now, now),
        "data_json": safe_json(data),
    }


def render(template, context):
    env = Environment(
        loader=FileSystemLoader(HERE / "templates"),
        # Every value is HTML-escaped unless marked safe: a station called "<b>" stays text.
        autoescape=select_autoescape(["html"]),
    )
    return env.get_template(template).render(**context)


def build(data_dir=DATA_DIR, out_dir=OUT_DIR, now=None, api_dir=API_DIR):
    now = now or datetime.now(timezone.utc)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(render("index.html", site_context(data_dir, now)), encoding="utf-8")

    openapi = json.loads((api_dir / "openapi.json").read_text(encoding="utf-8"))
    reference = api_reference(openapi, api_dir / "examples")
    (out_dir / "api.html").write_text(render("api.html", {**reference, "built_local": local_time(now, now)}), encoding="utf-8")
    shutil.copy(api_dir / "openapi.json", out_dir / "openapi.json")

    for asset in ("site.css", "site.js"):
        shutil.copy(HERE / "static" / asset, out_dir / asset)
    # Served from our own site: same version as the Python package, and no third-party
    # request from the visitor's browser.
    (out_dir / "plotly.min.js").write_text(get_plotlyjs(), encoding="utf-8")
    return out_dir / "index.html"


if __name__ == "__main__":
    print(f"wrote {build()}")
