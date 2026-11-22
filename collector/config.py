from datetime import timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"

GBFS_DISCOVERY_URL = "https://barcelona.publicbikesystem.net/customer/gbfs/v3.0/gbfs.json"

# Placa de Catalunya: close to the middle of the station network, and the city is small
# enough that one weather point is fair for a rain / dry split.
WEATHER_LAT = 41.387
WEATHER_LON = 2.170
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# TODO: add the public repo URL once it exists, so the feed owners can see who is calling.
USER_AGENT = "live-bike-monitor/0.1"

# Stored timestamps are UTC; this is only for what people read.
DISPLAY_TZ = "Europe/Madrid"

WINDOW_MINUTES = 15

# Two snapshots in a row = at least 30 minutes. One bad snapshot is too common to alert on,
# and three would hide most of a short morning-peak shortage.
MIN_EVENT_SNAPSHOTS = 2

# "Silent" = feed_last_updated - last_reported. In the first real snapshot 95% of stations
# had reported within 3 minutes and the next group was 5+ hours, so 60 minutes sits in the
# empty space between normal and silent.
SILENT_AFTER = timedelta(minutes=60)
# Separates a station under repair (station 12: 29 hours) from dead ones still listed
# (10 weeks to 17 months).
RETIRED_AFTER = timedelta(days=7)

# A station absent now is "missing" only if we saw it during this period. After that we stop
# expecting it: a station removed for good ends its missing episode a day later.
MISSING_LOOKBACK = timedelta(hours=24)
RAW_RETENTION_DAYS = 14
# Data counts as fresh while the last fetch is at most this old. Runs are every 15 minutes and
# GitHub often starts them late: two missed windows plus a late start is still fresh.
FRESH_FOR = timedelta(minutes=45)
# Only these become messages. Empty and full happen hundreds of times a day: they belong on
# the site, not on a phone. Retired is a fact about a dead station, not news.
ALERT_STATES = frozenset({"offline", "stale", "missing", "feed_down", "schema_error", "crashed"})
# Older starts and ends are history, not news. This also stops a first deploy from sending
# every episode in the file, and gives a failed send about 8 more runs to get through.
ALERT_MAX_AGE = timedelta(hours=2)
# Flood guard: a frozen feed that recovers can bring 500 stations back at once.
MAX_ALERTS_PER_RUN = 10

# A few broken stations are a glitch: skip them and keep the rest. Above 5% (25 of ~500)
# the feed has most likely changed shape, and we reject the whole snapshot.
MAX_INVALID_SHARE = 0.05
