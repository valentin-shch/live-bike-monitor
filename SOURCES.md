# Data sources

Both sources are public, need no key, and are called by an unattended job every 15 minutes
(bikes) and about once an hour (weather).

## Bicing station data (Barcelona)

- **What:** live station status (bikes and docks available, renting or not) and station
  facts (name, location, capacity), in the GBFS 3.0 format.
- **URL:** https://barcelona.publicbikesystem.net/customer/gbfs/v3.0/gbfs.json
  (the discovery file; the station feeds are read from the links it lists).
- **Licence:** the feed has no licence field. Under the GBFS 3.0 specification, feeds that
  omit it are CC0 1.0. Ajuntament de Barcelona also publishes Bicing station data on its
  open data portal (https://opendata-ajuntament.barcelona.cat/) under CC BY 4.0, so we
  attribute it anyway.
- **Attribution:** "Station data: Bicing, Ajuntament de Barcelona."
- **Rate limits:** none published. We make 3 requests every 15 minutes (about 290 a day),
  with timeouts, backoff with jitter and a single identifying User-Agent.

## Open-Meteo weather

- **What:** hourly temperature (°C), precipitation (mm) and wind speed (km/h) for one point in central Barcelona
  (41.387, 2.170). The API answers for the nearest model grid cell (about 41.415, 2.225),
  so it is a city-wide "rain or dry" signal, not a street-level measurement.
- **URL:** https://api.open-meteo.com/v1/forecast
- **Terms:** free for non-commercial use, which this project is. https://open-meteo.com/en/terms
- **Licence:** CC BY 4.0.
- **Attribution:** "Weather data by Open-Meteo.com" (https://open-meteo.com/).
- **Rate limits (free tier):** 10,000 calls a day, 5,000 an hour, 600 a minute. We make
  about 24 a day: a call is made only when the last finished hour is not stored yet.
- **Note:** past hours come from the forecast API's `past_days` (model values, not station
  observations). One call can reach back up to 92 days, which is how missing weather is
  filled after an outage.

## Map

Everything the map needs is served from this site: the visitor's browser makes no request to
a map, font or code host, so no third party receives visitors' IP addresses.

- **Map data:** © OpenStreetMap contributors, https://www.openstreetmap.org/copyright.
  Licence: Open Database License (ODbL). The file `map/barcelona.pmtiles` is a Barcelona
  extract (bbox 2.04,41.31 to 2.27,41.49, zoom 0–14) of the Protomaps basemap daily build
  of 2026-11-22 (https://build.protomaps.com/20261122.pmtiles), which Protomaps distributes
  as an ODbL Produced Work; it also contains Natural Earth data (public domain). The credit is
  shown on the map and in the page footer.
- **Map design:** Protomaps basemaps 5.7.2, "black" flavour, with our own land, sea and label
  colours (`build/make_style.mjs`). Design CC0, code BSD-3-Clause
  (`map/LICENSE-basemaps.md`). https://github.com/protomaps/basemaps
- **Fonts:** Noto Sans (Regular, Medium, Italic) glyphs from protomaps/basemaps-assets,
  SIL Open Font License 1.1 (`map/fonts/OFL.txt`). Only the Latin ranges are included.
- **Icons:** the "black" sprite from protomaps/basemaps-assets, derived from tangrams/icons,
  MIT (`map/sprites/LICENSE-icons.md`).
- **Code:** MapLibre GL JS 6.17.0 (BSD-3-Clause), pmtiles 4.5.0 (BSD-3-Clause, bundles fflate,
  MIT). Licence texts in `vendor/`.
- **Rebuilding the map file:** `pmtiles extract https://build.protomaps.com/YYYYMMDD.pmtiles
  pages/static/map/barcelona.pmtiles --bbox=2.04,41.31,2.27,41.49 --maxzoom=14` with the
  go-pmtiles CLI (v1.31.2 was used; BSD-3-Clause). It downloads only the needed parts.
- Plotly.js (MIT licence), used for the heatmap, is served from this site itself, copied from
  the pinned Python package at build time.
