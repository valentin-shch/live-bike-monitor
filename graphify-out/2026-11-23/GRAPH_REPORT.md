# Graph Report - live-bike-monitor  (2026-11-23)

## Corpus Check
- 44 files · ~31,500 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 3, .example 1, .css 1)

## Summary
- 498 nodes · 1385 edges · 17 communities (11 shown, 6 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e55dad93`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_detect.py
- fetch.py
- HttpError
- run.py
- pandas
- Bicing live: a bike-share monitor that runs without me
- test_api.py
- Repository
- test_notify.py
- weather.py
- site.js
- test_pages.py

## God Nodes (most connected - your core abstractions)
1. `create_app()` - 24 edges
2. `HttpError` - 24 edges
3. `write_snapshot()` - 24 edges
4. `confirmed_episodes()` - 22 edges
5. `_parse_stations()` - 20 edges
6. `SchemaError` - 18 edges
7. `update_events()` - 16 edges
8. `StationStatus` - 15 edges
9. `pending_alerts()` - 15 edges
10. `send_alerts()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `timelapse()` --indirect_call--> `station_order()`  [INFERRED]
  pages/build.py → api/data.py
- `test_openapi_file_is_up_to_date()` --calls--> `openapi_text()`  [EXTRACTED]
  tests/test_api.py → api/export.py
- `test_station_detail_has_its_history()` --uses--> `StationDetail`  [INFERRED]
  tests/test_api.py → api/models.py
- `test_empty_by_hour_uses_madrid_hours_and_renting_stations_only()` --uses--> `EmptyByHour`  [INFERRED]
  tests/test_api.py → api/models.py
- `schema_changed()` --calls--> `SchemaError`  [EXTRACTED]
  tests/test_run.py → collector/fetch.py

## Import Cycles
- None detected.

## Communities (17 total, 6 thin omitted)

### Community 0 - "test_detect.py"
Cohesion: 0.10
Nodes (39): classify(), confirmed_episodes(), detect_events(), _episodes(), feed_checks(), merge_events(), as_tuples(), at() (+31 more)

### Community 1 - "fetch.py"
Cohesion: 0.12
Nodes (31): Discovery, DiscoveryData, _english(), Envelope, _feed_url(), FeedLink, FeedResult, fetch_feeds() (+23 more)

### Community 2 - "HttpError"
Cohesion: 0.06
Nodes (26): HttpClient, HttpError, read_runs(), main(), run(), FakeAdapter, make_client(), _make() (+18 more)

### Community 3 - "run.py"
Cohesion: 0.11
Nodes (39): update_events(), alerts_sent_path(), apply_retention(), events_path(), hourly_path(), maintain(), raw_days(), read_alerts_sent() (+31 more)

### Community 4 - "pandas"
Cohesion: 0.19
Nodes (17): collection_events(), coverage(), _last_run_per_window(), runs_path(), weather_events(), window_report(), write_run(), runs() (+9 more)

### Community 5 - "Bicing live: a bike-share monitor that runs without me"
Cohesion: 0.17
Nodes (10): Bicing live: a bike-share monitor that runs without me, Honest limits, How it runs without me, Key decisions, Next steps, Run it locally, Bicing station data (Barcelona), Data sources (+2 more)

### Community 8 - "test_api.py"
Cohesion: 0.07
Nodes (30): as_records(), renting_hours(), station_order(), main(), create_app(), empty_by_hour(), get_station(), health() (+22 more)

### Community 10 - "test_notify.py"
Cohesion: 0.06
Nodes (38): _batches(), configured_notifiers(), _event(), message(), pending_alerts(), send_alerts(), sign(), SlackNotifier (+30 more)

### Community 11 - "weather.py"
Cohesion: 0.12
Nodes (23): bike_days(), fetch_weather(), Forecast, Hourly, is_due(), last_complete_hour(), past_days_needed(), store_weather() (+15 more)

### Community 12 - "site.js"
Cohesion: 0.39
Nodes (6): ago(), checkAge(), showFrame(), showStation(), sparkline(), text()

### Community 13 - "test_pages.py"
Cohesion: 0.08
Nodes (41): openapi_text(), api_reference(), build(), empty_heatmap(), event_cards(), format_duration(), headline(), health_section() (+33 more)

## Knowledge Gaps
- **8 isolated node(s):** `How it runs without me`, `Run it locally`, `Key decisions`, `Honest limits`, `Next steps` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 135 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `HttpError` connect `HttpError` to `weather.py`, `test_notify.py`, `run.py`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `create_app()` (e.g. with `Event` and `Page`) actually correct?**
  _`create_app()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `How it runs without me`, `Run it locally`, `Key decisions` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_detect.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10256410256410256 - nodes in this community are weakly interconnected._
- **Why does `Repository` connect `Repository` to `test_api.py`, `test_pages.py`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `HttpError` (e.g. with `send_alerts()` and `run()`) actually correct?**
  _`HttpError` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Should `fetch.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12280701754385964 - nodes in this community are weakly interconnected._