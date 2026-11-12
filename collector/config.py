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

RAW_RETENTION_DAYS = 14
