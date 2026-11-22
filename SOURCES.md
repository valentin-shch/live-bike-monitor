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

- **What:** hourly temperature (°C) and precipitation (mm) for one point in central Barcelona
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
