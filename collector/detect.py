"""Change detection. Pure functions: snapshots in, events out."""
import numpy as np
import pandas as pd

from collector.config import MAX_GAP, MIN_EVENT_SNAPSHOTS, MISSING_LOOKBACK, RETIRED_AFTER, SILENT_AFTER

# ended_by: "change" when we saw the state change, "gap" when the data stopped and we lost
# sight of it, missing while the episode is ongoing.
EVENT_COLUMNS = ["scope", "subject", "state", "started_at", "ended_at", "ended_by"]
EVENT_KEY = ["scope", "subject", "state"]


def classify(snapshots):
    """Give every row exactly one state. The first matching rule wins, so the order matters:
    a closed station with 0 bikes is offline, not empty."""
    silent_for = snapshots["feed_last_updated"] - snapshots["last_reported"]
    closed = ~snapshots["is_installed"] | ~snapshots["is_renting"]

    conditions = [
        silent_for > RETIRED_AFTER,
        closed | (silent_for > SILENT_AFTER),
        snapshots["num_vehicles_available"] == 0,
        snapshots["num_docks_available"] == 0,
    ]
    states = np.select(conditions, ["retired", "offline", "empty", "full"], default="ok")
    return snapshots.assign(state=states)


def feed_checks(snapshots, lookback=MISSING_LOOKBACK):
    """One row per window for each feed-level check, in the same shape as station states,
    so the same debounce turns them into episodes."""
    per_window = snapshots.groupby("window_utc").agg(
        clock=("feed_last_updated", "max"), newest_report=("last_reported", "max")
    ).sort_index()
    clock, newest = per_window["clock"], per_window["newest_report"]
    # A quiet night repeats the station numbers, but the clocks still move. A frozen feed
    # repeats them. Two clocks, because Bicing's last_updated looks stamped at request time
    # (ttl 0, within a minute of our fetch): it could keep moving over frozen data, while the
    # newest station report could not. Assumes both move more often than every 15 minutes.
    # The first window has nothing to compare with (NaT -> False).
    stale = clock.le(clock.shift()) | newest.le(newest.shift())

    last_seen, missing = {}, []
    for window, ids in snapshots.groupby("window_utc", sort=True)["station_id"]:
        present = set(ids)
        gone = [s for s, seen in last_seen.items() if s not in present and window - seen <= lookback]
        missing.append(bool(gone))
        last_seen.update(dict.fromkeys(present, window))

    n = len(clock)
    return pd.DataFrame(
        {
            "check": ["freshness"] * n + ["station_list"] * n,
            "window_utc": list(clock.index) * 2,
            "state": list(np.where(stale, "stale", "ok")) + ["missing" if m else "ok" for m in missing],
        }
    )


def confirmed_episodes(states, key="station_id", min_run=MIN_EVENT_SNAPSHOTS, max_gap=MAX_GAP):
    """Turn per-window states into episodes: subject X was in state Y from A to B.

    `key` names the column that says whose states these are (a station, or a feed check).
    Episodes of "ok" are not returned; ended_at is missing while an episode is ongoing.
    """
    episodes = []
    ordered = states.sort_values([key, "window_utc"])
    for subject, rows in ordered.groupby(key, sort=False):
        episodes += _episodes(
            subject, rows["window_utc"].tolist(), rows["state"].tolist(), min_run, max_gap
        )
    return pd.DataFrame(episodes, columns=[key, "state", "started_at", "ended_at", "ended_by"])


def detect_events(snapshots):
    """Every confirmed episode in the snapshots, stations and feed together."""
    if snapshots.empty:
        return pd.DataFrame(columns=EVENT_COLUMNS)
    stations = confirmed_episodes(classify(snapshots))
    feed = confirmed_episodes(feed_checks(snapshots), key="check")
    events = pd.concat(
        [
            stations.rename(columns={"station_id": "subject"}).assign(scope="station"),
            feed.rename(columns={"check": "subject"}).assign(scope="feed"),
        ],
        ignore_index=True,
    )
    return events[EVENT_COLUMNS]


def merge_events(saved, fresh, raw_start):
    """Combine the saved event history with episodes recomputed from the raw days we keep.

    raw_start is the oldest raw window. The recompute cannot see anything before it, so:
    - saved episodes that ended by raw_start are kept as they are (only the file remembers them);
    - a saved episode that was already running at raw_start shows up in the recompute with a
      late start (the first raw window). Its real start is copied back from the file.
    """
    if saved.empty:
        return fresh.reset_index(drop=True)

    ended_before = saved["ended_at"].notna() & (saved["ended_at"] <= raw_start)
    history = [saved[ended_before]]
    spanning = saved[~ended_before & (saved["started_at"] < raw_start)]

    fresh = fresh.sort_values("started_at", ignore_index=True)
    for old in spanning.itertuples(index=False):
        same = (fresh["scope"] == old.scope) & (fresh["subject"] == old.subject) & (fresh["state"] == old.state)
        first = fresh.index[same].min() if same.any() else None
        # The continuation is the earliest fresh episode of the same kind, and it must overlap
        # the saved one. A later, separate episode must not inherit an old start.
        if first is not None and (pd.isna(old.ended_at) or fresh.at[first, "started_at"] <= old.ended_at):
            fresh.at[first, "started_at"] = old.started_at
        else:
            history.append(pd.DataFrame([old._asdict()]))

    merged = pd.concat([h for h in history if not h.empty] + [fresh], ignore_index=True)
    return merged.sort_values(["started_at", *EVENT_KEY], ignore_index=True)


def _episodes(subject, windows, states, min_run, max_gap):
    # Debounce: a new state only counts once it has been seen min_run times in a row,
    # both going into a state and coming back out of it. Consecutive means consecutive
    # rows we have: a skipped run or two does not break a streak, but a gap longer than
    # max_gap does. Across a long gap we know nothing, so we do not pretend to.
    episodes = []
    confirmed, confirmed_since, last_seen = None, None, None
    candidate, candidate_since, streak = None, None, 0
    previous = None

    for window, state in zip(windows, states):
        if previous is not None and window - previous > max_gap:
            # Close what we saw, at the last reading that showed it, and start from scratch.
            if confirmed not in (None, "ok"):
                episodes.append((subject, confirmed, confirmed_since, last_seen, "gap"))
            confirmed, confirmed_since = None, None
            candidate, streak = None, 0
        previous = window

        if state == candidate:
            streak += 1
        else:
            candidate, candidate_since, streak = state, window, 1

        if candidate != confirmed and streak >= min_run:
            if confirmed not in (None, "ok"):
                episodes.append((subject, confirmed, confirmed_since, candidate_since, "change"))
            confirmed, confirmed_since = candidate, candidate_since
        if state == confirmed:
            last_seen = window

    if confirmed not in (None, "ok"):
        episodes.append((subject, confirmed, confirmed_since, None, None))
    return episodes
