# Bicing live: a bike-share monitor that runs without me

When do Barcelona's Bicing stations run out of bikes, and would anyone notice if the feed broke?
On a Thursday evening (12 Nov 2026, 19:45) 120 of 545 stations had no bikes, and overnight 41
stations had dropped out of the feed entirely, which is why "missing" here means "missing compared
with the last 24 hours". <!-- TODO: replace with the heatmap's finding once there are 4+ weeks of data -->

**Live status page:** https://valentin-shch.github.io/live-bike-monitor/ ·
[API reference](https://valentin-shch.github.io/live-bike-monitor/api.html) ·
![tests](https://github.com/valentin-shch/live-bike-monitor/actions/workflows/tests.yml/badge.svg)

## How it runs without me

- **Trigger:** a GitHub Actions schedule, every 15 minutes at :04, :19, :34 and :49 (off the busy
  top of the hour). Each run fetches the Bicing GBFS feed, stores a Parquet snapshot on the `data`
  branch, fetches weather about once an hour, detects events, sends alerts and rebuilds the page.
- **On failure:** HTTP calls retry with backoff and jitter; a failed run still writes a run record
  and turns red; two failures in a row become an event and an alert ("feed changed shape",
  "feed not answering", "collector crashing"). If the job stops altogether, the published page
  notices on its own: it compares its data's age with the visitor's clock and turns red after 45 min.
- **Re-runs are safe:** a snapshot's file name is its 15-minute window, so a re-run replaces it
  instead of duplicating it. Events are recomputed from the raw data each run, and each alert is
  recorded per channel after sending, so a re-run does not send it twice.
- **Housekeeping:** raw snapshots are kept 14 days, after an hourly summary is written; the `data`
  branch is squashed weekly so git history does not grow forever.

GitHub disables scheduled workflows in public repositories after 60 days without repository
activity. If that happens, the page turns red; re-enable it under Actions → collect →
"Enable workflow". I do not count on the robot's data commits keeping it alive.

## Run it locally

```
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Python 3.14
python -m collector.run          # one collection run, writes data/
python -m pages.build            # builds _site/index.html from data/
python -m pytest                 # tests use saved responses, never the network
uvicorn api.main:app --port 8000 # the API, docs at http://localhost:8000/docs
```

The API reads `data/`, or the folder in `API_DATA_DIR` (for example a worktree of the `data`
branch). In Docker: `docker build -t bike-monitor-api .` then
`docker run --rm -p 8000:8000 -v "${PWD}/data:/app/data:ro" bike-monitor-api`.

Alerts are off unless configured: Telegram (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`), Slack
(`SLACK_WEBHOOK_URL`) and a signed webhook (`WEBHOOK_URL`, `WEBHOOK_SECRET`). In Actions they are
repository secrets; locally, environment variables (see `.env.example`). `demo/receiver.py` is a
small receiver that checks the webhook's HMAC signature, timestamp and duplicates.

## Key decisions

- **Files, not a database:** one Parquet file per window, partitioned by day, on a git branch.
  Free, inspectable, and the window is a natural key.
- **States are debounced:** a station counts as empty, full or offline only after two snapshots
  in a row, both going in and coming out, so one odd reading does not send an alert.
- **Stale feed vs quiet night:** unchanged numbers at 03:00 are normal. The check is whether
  the feed's own clocks (its `last_updated` and the newest station report) still move.
- **Empty share counts renting stations only:** a closed station with no bikes is closed, not empty.
- **Alerts at least once:** sent first, recorded after. A crash between the two can repeat a
  message; the other order could lose one.
- **No map tiles:** the free dark tiles now need an API key, so stations are drawn on plain
  black. Their dots draw the city well enough.

## Honest limits

- A few weeks of data give a hint about weekly patterns, not proof.
- The scheduler is best-effort: runs start late (often several minutes) and some windows have
  no data. The health section shows every gap instead of filling it.
- Weather is one model grid cell about 5 km from the centre: fine for rain or dry, not for streets.
- Stations retired from service but still listed as renting are counted in the hourly shares
  (four of about 545).
- The API reads files on every request and has no authentication or rate limit yet.

## Next steps

API keys and a rate limiter for the API; a `/v1` prefix before anyone else depends on it;
a cache for the API; a smaller Plotly bundle; street tiles from a keyless provider. Out of scope
on purpose: OAuth, a database, hosting the API.

Data: Bicing station data, Ajuntament de Barcelona. Weather data by Open-Meteo.com.
Details, licences and limits in [SOURCES.md](SOURCES.md).
