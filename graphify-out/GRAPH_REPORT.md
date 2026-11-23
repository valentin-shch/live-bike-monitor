# Graph Report - live-bike-monitor  (2026-11-23)

## Corpus Check
- 44 files · ~31,666 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 3, .example 1, .css 1)

## Summary
- 499 nodes · 1390 edges · 19 communities (12 shown, 7 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7c39dc9d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_detect.py
- fetch.py
- HttpError
- write_snapshot
- pandas
- Bicing live: a bike-share monitor that runs without me
- test_skeleton.py
- test_api.py
- Repository
- test_notify.py
- weather.py
- site.js
- test_pages.py
- isolated

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
- `test_station_detail_has_its_history()` --uses--> `StationDetail`  [INFERRED]
  tests/test_api.py → api/models.py
- `test_empty_by_hour_uses_madrid_hours_and_renting_stations_only()` --uses--> `EmptyByHour`  [INFERRED]
  tests/test_api.py → api/models.py
- `test_empty_station_list_rejects_the_snapshot()` --uses--> `SchemaError`  [INFERRED]
  tests/test_fetch.py → collector/fetch.py
- `test_field_renamed_everywhere_rejects_the_snapshot()` --uses--> `SchemaError`  [INFERRED]
  tests/test_fetch.py → collector/fetch.py

## Import Cycles
- None detected.

## Communities (19 total, 7 thin omitted)

### Community 0 - "test_detect.py"
Cohesion: 0.13
Nodes (35): confirmed_episodes(), _episodes(), feed_checks(), as_tuples(), at(), check_states(), event(), feed_snapshots() (+27 more)

### Community 1 - "fetch.py"
Cohesion: 0.12
Nodes (31): Discovery, DiscoveryData, _english(), Envelope, _feed_url(), FeedLink, FeedResult, fetch_feeds() (+23 more)

### Community 2 - "HttpError"
Cohesion: 0.09
Nodes (12): HttpClient, HttpError, FakeAdapter, make_client(), _make(), test_404_is_not_retried(), test_backoff_waits_stay_between_half_and_full_ceiling(), test_each_wait_is_at_least_as_long_as_the_previous() (+4 more)

### Community 3 - "write_snapshot"
Cohesion: 0.13
Nodes (30): collect(), apply_retention(), hourly_path(), maintain(), raw_days(), read_snapshots(), roll_up_day(), snapshot_path() (+22 more)

### Community 4 - "pandas"
Cohesion: 0.08
Nodes (42): station_order(), detect_events(), merge_events(), collection_events(), coverage(), _last_run_per_window(), read_runs(), runs_path() (+34 more)

### Community 5 - "Bicing live: a bike-share monitor that runs without me"
Cohesion: 0.17
Nodes (10): Bicing live: a bike-share monitor that runs without me, Honest limits, How it runs without me, Key decisions, Next steps, Run it locally, Bicing station data (Barcelona), Data sources (+2 more)

### Community 8 - "test_api.py"
Cohesion: 0.07
Nodes (31): as_records(), renting_hours(), main(), openapi_text(), create_app(), empty_by_hour(), get_station(), health() (+23 more)

### Community 9 - "Repository"
Cohesion: 0.17
Nodes (3): Repository, classify(), test_classify_picks_the_first_matching_state()

### Community 10 - "test_notify.py"
Cohesion: 0.06
Nodes (38): _batches(), configured_notifiers(), _event(), message(), pending_alerts(), send_alerts(), sign(), SlackNotifier (+30 more)

### Community 11 - "weather.py"
Cohesion: 0.12
Nodes (24): SchemaError, bike_days(), fetch_weather(), Forecast, Hourly, is_due(), last_complete_hour(), past_days_needed() (+16 more)

### Community 12 - "site.js"
Cohesion: 0.39
Nodes (6): ago(), checkAge(), showFrame(), showStation(), sparkline(), text()

### Community 13 - "test_pages.py"
Cohesion: 0.08
Nodes (38): api_reference(), build(), empty_heatmap(), event_cards(), format_duration(), headline(), health_section(), local_time() (+30 more)

## Knowledge Gaps
- **8 isolated node(s):** `How it runs without me`, `Run it locally`, `Key decisions`, `Honest limits`, `Next steps` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 135 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `HttpError` connect `HttpError` to `test_notify.py`, `weather.py`, `pandas`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `create_app()` (e.g. with `Event` and `Page`) actually correct?**
  _`create_app()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `How it runs without me`, `Run it locally`, `Key decisions` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_detect.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13170731707317074 - nodes in this community are weakly interconnected._
- **Why does `Repository` connect `Repository` to `test_api.py`, `pandas`, `test_pages.py`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `HttpError` (e.g. with `send_alerts()` and `run()`) actually correct?**
  _`HttpError` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Should `fetch.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11923076923076924 - nodes in this community are weakly interconnected._