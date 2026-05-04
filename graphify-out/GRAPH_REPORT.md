# Graph Report - A2AvsMCP  (2026-05-05)

## Corpus Check
- 219 files · ~131,455 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1637 nodes · 4439 edges · 39 communities detected
- Extraction: 48% EXTRACTED · 52% INFERRED · 0% AMBIGUOUS · INFERRED: 2315 edges (avg confidence: 0.62)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 120|Community 120]]

## God Nodes (most connected - your core abstractions)
1. `TraceRecorder` - 192 edges
2. `TaskSpec` - 106 edges
3. `RaceResult` - 95 edges
4. `DemoPlatform` - 92 edges
5. `HardnessType` - 92 edges
6. `HardnessProfile` - 90 edges
7. `ScoreCard` - 72 edges
8. `FailureConfig` - 55 edges
9. `ReportService` - 55 edges
10. `AgentResult` - 54 edges

## Surprising Connections (you probably didn't know these)
- `D-30 hardness coverage matrix: each v1 HardnessType in >=2 of 3 tasks (RACE-01).` --uses--> `HardnessType`  [INFERRED]
  tests/race/test_hardness_coverage.py → src/a2a_vs_mcp/race/types.py
- `D-30 locked matrix: every HardnessType -> exact set of tasks.` --uses--> `HardnessType`  [INFERRED]
  tests/race/test_hardness_coverage.py → src/a2a_vs_mcp/race/types.py
- `D-30: every HardnessType appears in >= 2 of 3 v1 tasks.` --uses--> `HardnessType`  [INFERRED]
  tests/race/test_hardness_coverage.py → src/a2a_vs_mcp/race/types.py
- `Trace schema field-presence + ndjson round-trip + per-lane turn_index (TRC-01, T` --uses--> `TraceRecorder`  [INFERRED]
  tests/race/test_trace_schema.py → src/a2a_vs_mcp/trace.py
- `test_coalesce_below_threshold_returns_unchanged()` --calls--> `coalesce()`  [INFERRED]
  tests/test_race_ws.py → src/a2a_vs_mcp/race/ws.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (126): HeatmapBaseline, Frozen pinned-baseline tuple (D-56).      model + seed + task_ids together defin, JSON-friendly view: task_ids tuple -> list., FailureScriptEntry, InjectedFaultError, Raised by _apply_mutation for RATE_LIMIT_429 and PARTIAL_COMMIT_5XX faults., _build_lane_failed_result(), _characteristic_tool_for() (+118 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (101): build_parser(), main(), render_output(), default_profile_name(), ProfileConfig, resolve_profile(), expected_checks(), main() (+93 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (48): AgentContext, BaseAgent, BaseAgent, A2ABroker, Dispatch all messages concurrently. Returns results in submission order (per D-0, Worker: execute one task and record its completion timing., main(), transport_events() (+40 more)

### Community 3 - "Community 3"
Cohesion: 0.04
Nodes (65): get_free_busy(), _load(), propose_time(), Calendar fixture mock. SINGLE FAULT CHOKEPOINT per D-25.  Backs the negotiate_me, Return the free/busy windows for a calendar owner., Compute a mutual free window across owners; returns {start, end, owners}.      N, DetectorState, Per-fault detection state. WAITING is reserved for "no fault scripted yet"; (+57 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (34): card(), build_server(), main(), build_server(), main(), _dispatch_step(), _execute_step_with_on_fault(), a2a_skill_id() (+26 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (62): ApiRunRequest, AppliedTrendFiltersResponse, AppliedTrendSortingResponse, AverageTotalsResponse, ComparisonMetricsResponse, CountByModeResponse, CountByScenarioResponse, HealthResponse (+54 more)

### Community 6 - "Community 6"
Cohesion: 0.04
Nodes (50): Pinned race-demo configuration constants (D-55, D-56, D-57).  HEATMAP_BASELINE i, _build_cells(), _matches_baseline(), _per_run_terminal_tag(), Heatmap aggregator + in-process cache (D-52, D-54, D-55, D-57).  get_heatmap() w, Walk RUNS_DIR; bucket baseline-matching runs by (hardness_type, lane).      Each, D-55 + D-57 filter: run_meta must exist + match model/seed/task_id.      Missing, Map a single run's events to one of the 5 terminal tags.      Mirrors harness._p (+42 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (25): MCPClient, HaikuJudge, JudgeVerdict, Structured verdict returned by HaikuJudge.judge()., Stateless Anthropic Haiku 4.5 judge.      Caller supplies a system_prompt (the r, Run the rubric against the artifact. Returns JudgeVerdict (passed/score, RuntimeError, str (+17 more)

### Community 8 - "Community 8"
Cohesion: 0.05
Nodes (32): fetchRaceReplay(), fetchRemoteA2aHealth(), fetchRemoteA2aRegistry(), fetchRemoteMcpRegistry(), fetchReportDetail(), fetchReports(), fetchScenarios(), fetchTelemetry() (+24 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (29): Detector, Feed one event. Returns True iff state flipped to OBSERVED on this call., Terminal tag at ``done`` event arrival (D-34 + master design §Per-fault, D-34: race_done arrived without a ``done`` for this lane → indeterminate., Stateful per-fault state machine (D-31).      Runner instantiates one Detector p, _detect_and_record(), _detect_and_record(), _detect_and_record() (+21 more)

### Community 10 - "Community 10"
Cohesion: 0.09
Nodes (27): get_heatmap(), invalidate_cache(), Drop the entire heatmap cache (D-54). Called by harness post-race_done., Return {cells, baseline}. Rebuilds from disk on cache miss (D-52, D-54)., _baseline_run_events(), _IsolatedRunsDirMixin, Heatmap aggregator + route tests (D-52..D-57).  Pins all four invariants: 1. Pin, D-52: get_heatmap returns {cells, baseline}; baseline = HEATMAP_BASELINE.to_dict (+19 more)

### Community 11 - "Community 11"
Cohesion: 0.07
Nodes (24): Unit tests for race/ws.py — ConnectionManager + coalesce + constants (Plan 06-07, test_coalesce_above_threshold_keeps_latest_tick_per_lane_task(), test_coalesce_below_threshold_returns_unchanged(), test_coalesce_preserves_never_coalesce_events_verbatim(), test_connect_enforces_per_ip_cap(), test_disconnect_decrements_ip_and_removes_from_run(), test_publish_enqueues_to_all_connections_for_run(), test_publish_no_subscribers_is_noop() (+16 more)

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (27): aggregate_for_classifier(), compute_wasted_tokens(), _find_fault_injected(), _find_fault_observed(), median_delegations(), median_retries(), median_switches(), median_turns_after_fault() (+19 more)

### Community 13 - "Community 13"
Cohesion: 0.1
Nodes (17): _characteristic_event_phrase(), _dominant_tag(), failure_mode_classifier(), _fault_summary(), 6 templates, locked verbatim from master design §failure_mode_classifier.      D, Sixth template (D-35): lane infra failure — judge timeout, broker error, etc., Mode of tags; ties broken by precedence:     recovered > gave_up > kept_going_wi, Per-task short clause used in headlines (master design §failure_mode_classifier) (+9 more)

### Community 14 - "Community 14"
Cohesion: 0.05
Nodes (1): WebUiTests

### Community 15 - "Community 15"
Cohesion: 0.09
Nodes (18): AgentMsgEvent, DoneEvent, ErrorEvent, FaultInjectedEvent, FaultObservedEvent, RaceDoneEvent, Wire-format dataclasses for /api/race/ws (TRC-04, D-06).  Every event carries la, TickEvent (+10 more)

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (18): alignTraces(), compareFields(), deepEqual(), turnIndexOf(), eventBorderColor(), getProtocolColor(), buildTimelineBars(), envelopePayload() (+10 more)

### Community 17 - "Community 17"
Cohesion: 0.14
Nodes (10): TaskConfig, Per-task TARGETS + BINDS registries + per-task scorer wiring (RACE-01, RACE-05,, Per-task scorer composition (D-42, D-43)., D-43 IRON RULE: negotiate_meeting is structural-only — no Haiku import., Each task __init__ exports TARGETS dict + BINDS dict (D-27)., Convention: TARGETS keys are dotted strings ('module.tool_name')., Loader rejects failure_script.target not in TARGETS keys., TestPerTaskScorerWiring (+2 more)

### Community 18 - "Community 18"
Cohesion: 0.12
Nodes (11): _public_def_bodies(), IRON RULE D-25: every public mock callable goes through inject_fault().  Extends, Negative gate: race_*.py servers must NOT load fixtures directly.      Fixture f, Return [(name, body_text)] for every top-level public def in src.      Top-level, Every public callable in race/mocks/{github,calendar,travel}.py     must contain, Every @mcp.tool() in mcp_servers/race_*.py imports + calls into race.mocks.*., The server file must reference the race.mocks package somehow., For every @mcp.tool() function body, the body must reference the         corresp (+3 more)

### Community 19 - "Community 19"
Cohesion: 0.19
Nodes (6): build_reasoner(), FakeReasoningEngine, LLMReasoner, MockReasoner, Deterministic reasoning stub for tests that exercise the LLM path without an API, TicketIntent

### Community 20 - "Community 20"
Cohesion: 0.18
Nodes (9): is_acknowledging_fault(), D-36: regex with negation guard. Sentence boundary = [.!?] or end-of-message., _load_corpus(), is_acknowledging_fault regex tests over the 50-sample corpus (D-36, RACE-04).  A, 50-sample corpus FP rate gate (D-36)., Sanity bound: regex must accept at least half of the ack samples         (the co, D-36 negation guard explicit cases., TestAckRegexCorpus (+1 more)

### Community 21 - "Community 21"
Cohesion: 0.15
Nodes (15): HEAT-03 backend half — /api/race/runs/{run_id}/trace route contract.  Path-trave, Well-formed run_id with no on-disk file → 404., Top-level keys EXACTLY match RaceReplayPayload (client.ts:136-140)., Events carry backend `event_type` key (NOT renamed to `type`) — D-59., Point web.py's RUNS_DIR at an isolated tmp directory.      web.py imports RUNS_D, Write an ndjson run file (one event per line)., Valid existing run returns 200 + {run_id, events, schema_version='1.0'}., Path-traversal-flavored or over-length run_id returns 400. (+7 more)

### Community 22 - "Community 22"
Cohesion: 0.19
Nodes (11): Unit tests for src/a2a_vs_mcp/race/turn.py — per-lane turn-defining events (D-15, test_hybrid_is_set_union_of_tool_call_and_agent_msg(), test_hybrid_tick_is_not_turn_defining(), test_pure_a2a_agent_msg_is_turn_defining(), test_pure_a2a_tool_call_is_not_turn_defining(), test_pure_mcp_agent_msg_is_not_turn_defining(), test_pure_mcp_tool_call_is_turn_defining(), test_unknown_lane_returns_false_no_keyerror() (+3 more)

### Community 23 - "Community 23"
Cohesion: 0.22
Nodes (4): Tests for POST /api/race/run endpoint (B1 gap closure, Phase 14)., Valid body returns 200 with a run_id string., asyncio.create_task is called once per POST., TestRaceRunEndpoint

### Community 24 - "Community 24"
Cohesion: 0.23
Nodes (8): Phase 10 — OG-01..OG-04 PNG + HTML route tests (D-63: mock render fn; no Chromiu, test_both_surfaces_share_invariants(), test_cache_hit_skips_render(), test_cache_miss_renders_once_and_writes(), test_html_route_injects_og_meta_tags(), test_render_exception_returns_503_and_does_not_cache(), test_version_bump_invalidates_and_cleans(), _write_run()

### Community 25 - "Community 25"
Cohesion: 0.27
Nodes (5): D-30 hardness coverage matrix: each v1 HardnessType in >=2 of 3 tasks (RACE-01)., D-30 locked matrix: every HardnessType -> exact set of tasks., D-30: every HardnessType appears in >= 2 of 3 v1 tasks., TestHardnessCoverageMatrix, _types_for()

### Community 26 - "Community 26"
Cohesion: 0.28
Nodes (5): HookCapture(), Inner(), StatefulInner(), useFirstMention(), FirstMentionProbe()

### Community 28 - "Community 28"
Cohesion: 0.48
Nodes (5): allTerminalLanes(), makeIdleLane(), makeLaneFailedLane(), makeStreamingLane(), makeTerminalLane()

### Community 29 - "Community 29"
Cohesion: 0.29
Nodes (1): MockWebSocket

### Community 30 - "Community 30"
Cohesion: 0.38
Nodes (3): buildSnapshotSvg(), escapeXml(), handleDownload()

### Community 31 - "Community 31"
Cohesion: 0.33
Nodes (5): Async FastAPI integration tests — exercises ASGI app in-process via httpx., Full request path for MCP mode through the FastAPI ASGI app without a real serve, FakeReasoningEngine produces a non-empty answer for all modes without OPENAI_API, test_api_fake_llm_runtime_returns_canned_answer(), test_api_mcp_mode_end_to_end_async()

### Community 32 - "Community 32"
Cohesion: 0.33
Nodes (2): 8 wire event types over /api/race/ws (TRC-04)., WsSchemaTests

### Community 33 - "Community 33"
Cohesion: 0.5
Nodes (2): raceReducer(), updateLane()

### Community 34 - "Community 34"
Cohesion: 0.83
Nodes (3): handleChange(), handleChangeCommitted(), toSingleValue()

### Community 38 - "Community 38"
Cohesion: 0.5
Nodes (3): pytest_addoption(), Shared pytest configuration: sys.path setup and test environment variables., Register --update-snapshots flag for hand-rolled fixture-snapshot tests     (HEA

### Community 39 - "Community 39"
Cohesion: 0.67
Nodes (3): build_server(), main(), Race Travel MCP server (RACE-07).  Wraps race.mocks.travel. Three tools: search_

### Community 40 - "Community 40"
Cohesion: 0.67
Nodes (3): build_server(), main(), Race GitHub MCP server (RACE-07).  Wraps race.mocks.github. Three tools: get_rep

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (2): inspect_bundle(), main()

### Community 120 - "Community 120"
Cohesion: 1.0
Nodes (1): When len(buffer) > COALESCE_THRESHOLD, coalesce tick events keeping         late

## Knowledge Gaps
- **117 isolated node(s):** `Async FastAPI integration tests — exercises ASGI app in-process via httpx.`, `Full request path for MCP mode through the FastAPI ASGI app without a real serve`, `FakeReasoningEngine produces a non-empty answer for all modes without OPENAI_API`, `Shared pytest configuration: sys.path setup and test environment variables.`, `Register --update-snapshots flag for hand-rolled fixture-snapshot tests     (HEA` (+112 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 14`** (38 nodes): `setUpClass()`, `WebUiTests`, `.test_api_a2a_health_accepts_override_urls()`, `.test_api_exposes_remote_a2a_registry()`, `.test_api_exposes_remote_mcp_registry()`, `.test_api_health_reports_backend_status()`, `.test_api_remote_urls_reject_external_hosts_by_default()`, `.test_api_report_accepts_sorting()`, `.test_api_report_includes_export_urls()`, `.test_api_report_rejects_unsafe_report_names()`, `.test_api_report_returns_404_for_missing_report()`, `.test_api_report_trends_accepts_sorting()`, `.test_api_report_trends_aggregates_saved_runs()`, `.test_api_report_trends_can_be_filtered()`, `.test_api_run_profile_can_enable_report_and_external_logs()`, `.test_api_run_rejects_invalid_enums()`, `.test_api_run_returns_404_for_missing_scenario()`, `.test_api_run_returns_summary_results_and_scorecard()`, `.test_api_scenarios_include_metadata()`, `.test_api_supports_user_scoped_reports_and_telemetry()`, `.test_export_report_route_renders_evidence_bundle()`, `.test_export_report_route_renders_html()`, `.test_export_report_route_renders_pdf()`, `.test_index_page_loads_react_app()`, `.test_learning_page_loads_react_app()`, `.test_legacy_index_page_remains_available()`, `.test_openapi_contains_contract_schemas()`, `.test_run_endpoint_accepts_failure_toggles()`, `.test_run_endpoint_accepts_mcp_transport_selection()`, `.test_run_endpoint_renders_results()`, `.test_run_endpoint_uses_profile_defaults_for_logs()`, `.test_run_form_shows_profile_and_log_controls()`, `.test_trend_view_accepts_filters()`, `.test_trend_view_contains_drilldown_actions()`, `.test_trend_view_renders_in_results_panel()`, `.test_trend_view_shows_active_filter_chips()`, `.test_trend_view_shows_sort_controls()`, `test_web_ui.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (7 nodes): `useRaceStream.test.ts`, `MockWebSocket`, `.close()`, `.constructor()`, `.simulateClose()`, `.simulateError()`, `.simulateMessage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (6 nodes): `8 wire event types over /api/race/ws (TRC-04).`, `setUpClass()`, `WsSchemaTests`, `.test_handshake_accepts_run_id()`, `.test_wire_event_types_locked()`, `test_ws_schema.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (5 nodes): `raceReducer.ts`, `appendEvent()`, `emptyLane()`, `raceReducer()`, `updateLane()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (3 nodes): `inspect_bundle()`, `main()`, `import_evidence_bundle.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 120`** (1 nodes): `When len(buffer) > COALESCE_THRESHOLD, coalesce tick events keeping         late`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TraceRecorder` connect `Community 0` to `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 15`?**
  _High betweenness centrality (0.150) - this node is a cross-community bridge._
- **Why does `HardnessType` connect `Community 0` to `Community 3`, `Community 5`, `Community 7`, `Community 17`, `Community 25`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `run_race()` connect `Community 0` to `Community 1`, `Community 4`, `Community 7`, `Community 10`, `Community 12`, `Community 13`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 186 inferred relationships involving `TraceRecorder` (e.g. with `FlakyHandler` and `DemoModeTests`) actually correct?**
  _`TraceRecorder` has 186 INFERRED edges - model-reasoned connections that need verification._
- **Are the 103 inferred relationships involving `TaskSpec` (e.g. with `TestHeatmapBaselineSingleton` and `TestRunMetaFirstEvent`) actually correct?**
  _`TaskSpec` has 103 INFERRED edges - model-reasoned connections that need verification._
- **Are the 92 inferred relationships involving `RaceResult` (e.g. with `TestHeatmapBaselineSingleton` and `TestRunMetaFirstEvent`) actually correct?**
  _`RaceResult` has 92 INFERRED edges - model-reasoned connections that need verification._
- **Are the 77 inferred relationships involving `DemoPlatform` (e.g. with `FlakyHandler` and `DemoModeTests`) actually correct?**
  _`DemoPlatform` has 77 INFERRED edges - model-reasoned connections that need verification._