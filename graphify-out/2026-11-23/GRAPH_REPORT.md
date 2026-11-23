# Graph Report - live-bike-monitor  (2026-11-15)

## Corpus Check
- 29 files · ~15,738 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: .example 1, (none) 1)

## Summary
- 205 nodes · 516 edges · 17 communities (6 shown, 11 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 20 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `96206ddd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_detect.py
- fetch.py
- HttpError
- run.py
- test_rollup.py
- write_snapshot
- test_skeleton.py

## God Nodes (most connected - your core abstractions)
1. `write_snapshot()` - 20 edges
2. `_parse_stations()` - 16 edges
3. `confirmed_episodes()` - 15 edges
4. `HttpError` - 15 edges
5. `run()` - 15 edges
6. `roll_up_day()` - 12 edges
7. `states_table()` - 12 edges
8. `StationStatus` - 11 edges
9. `read_snapshots()` - 11 edges
10. `maintain()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `test_classify_on_the_real_snapshot_matches_the_stage_1_findings()` --calls--> `classify()`  [EXTRACTED]
  tests/test_detect.py → collector/detect.py
- `test_empty_station_list_rejects_the_snapshot()` --uses--> `SchemaError`  [INFERRED]
  tests/test_fetch.py → collector/fetch.py
- `test_field_renamed_everywhere_rejects_the_snapshot()` --uses--> `SchemaError`  [INFERRED]
  tests/test_fetch.py → collector/fetch.py
- `test_stations_without_post_code_are_kept()` --uses--> `StationInfo`  [INFERRED]
  tests/test_fetch.py → collector/fetch.py
- `test_classify_on_the_real_snapshot_matches_the_stage_1_findings()` --uses--> `StationStatus`  [INFERRED]
  tests/test_detect.py → collector/fetch.py

## Import Cycles
- None detected.

## Communities (17 total, 11 thin omitted)

### Community 0 - "test_detect.py"
Cohesion: 0.12
Nodes (33): classify(), confirmed_episodes(), detect_events(), _episodes(), feed_checks(), merge_events(), as_tuples(), check_states() (+25 more)

### Community 1 - "fetch.py"
Cohesion: 0.12
Nodes (29): Discovery, DiscoveryData, _english(), Envelope, _feed_url(), FeedLink, FeedResult, fetch_feeds() (+21 more)

### Community 2 - "HttpError"
Cohesion: 0.09
Nodes (14): HttpClient, HttpError, FakeAdapter, make_client(), _make(), test_404_is_not_retried(), test_backoff_waits_stay_between_half_and_full_ceiling(), test_each_wait_is_at_least_as_long_as_the_previous() (+6 more)

### Community 3 - "run.py"
Cohesion: 0.16
Nodes (15): main(), run(), events_path(), maintain(), raw_days(), read_all_snapshots(), read_events(), window_start() (+7 more)

### Community 4 - "test_rollup.py"
Cohesion: 0.31
Nodes (12): apply_retention(), hourly_path(), roll_up_day(), at(), one_station(), test_day_without_snapshots_has_nothing_to_roll_up(), test_full_and_renting_shares(), test_hour_with_a_skipped_run_is_summarised_from_what_exists() (+4 more)

### Community 5 - "write_snapshot"
Cohesion: 0.25
Nodes (12): read_snapshots(), snapshot_path(), write_snapshot(), small_snapshot(), test_late_evening_utc_stays_in_the_utc_day(), test_leftover_tmp_file_is_ignored_by_the_reader(), test_reading_a_day_with_no_data_gives_an_empty_table(), test_rerun_in_the_same_window_replaces_instead_of_duplicating() (+4 more)

## Knowledge Gaps
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `HttpError` connect `HttpError` to `run.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `HttpError` (e.g. with `main()` and `test_404_is_not_retried()`) actually correct?**
  _`HttpError` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_detect.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12173913043478261 - nodes in this community are weakly interconnected._
- **Why does `HttpClient` connect `HttpError` to `run.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Should `fetch.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11740890688259109 - nodes in this community are weakly interconnected._
- **Why does `write_snapshot()` connect `write_snapshot` to `run.py`, `test_rollup.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Should `HttpError` be split into smaller, more focused modules?**
  _Cohesion score 0.08708708708708708 - nodes in this community are weakly interconnected._