# Graph Report - A2AvsMCP  (2026-04-27)

## Corpus Check
- 95 files · ~66,632 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 663 nodes · 1665 edges · 22 communities detected
- Extraction: 58% EXTRACTED · 42% INFERRED · 0% AMBIGUOUS · INFERRED: 705 edges (avg confidence: 0.68)
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
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 31|Community 31]]

## God Nodes (most connected - your core abstractions)
1. `DemoPlatform` - 71 edges
2. `AgentResult` - 47 edges
3. `A2AMessage` - 44 edges
4. `DemoModeTests` - 43 edges
5. `DemoRepository` - 41 edges
6. `A2ABroker` - 41 edges
7. `TraceRecorder` - 39 edges
8. `FailureConfig` - 37 edges
9. `ReportService` - 37 edges
10. `AgentContext` - 37 edges

## Surprising Connections (you probably didn't know these)
- `FlakyHandler` --uses--> `DemoPlatform`  [INFERRED]
  tests/test_demo_modes.py → src/a2a_vs_mcp/platform.py
- `DemoModeTests` --uses--> `A2ABroker`  [INFERRED]
  tests/test_demo_modes.py → src/a2a_vs_mcp/a2a/broker.py
- `DemoModeTests` --uses--> `AgentContext`  [INFERRED]
  tests/test_demo_modes.py → src/a2a_vs_mcp/agents/base.py
- `DemoModeTests` --uses--> `DemoRepository`  [INFERRED]
  tests/test_demo_modes.py → src/a2a_vs_mcp/dataset.py
- `DemoModeTests` --uses--> `DemoPlatform`  [INFERRED]
  tests/test_demo_modes.py → src/a2a_vs_mcp/platform.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (27): AgentContext, A2ABroker, Dispatch all messages concurrently. Returns results in submission order (per D-0, Worker: execute one task and record its completion timing., DemoRepository, A2AMessage, AgentCard, AgentResult (+19 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (24): build_parser(), main(), render_output(), expected_checks(), main(), parse_csv(), run_eval(), write_csv() (+16 more)

### Community 2 - "Community 2"
Cohesion: 0.1
Nodes (45): default_profile_name(), ProfileConfig, resolve_profile(), base_artifact_root(), normalize_user_id(), user_artifact_root(), api_health(), api_report() (+37 more)

### Community 3 - "Community 3"
Cohesion: 0.1
Nodes (14): BaseAgent, BaseAgent, MCPDataAgent, MCPDocumentationAgent, MCPEnabledMixin, MCPPolicyBillingAgent, DemoPlatform, ComparisonMetrics (+6 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (28): fetchRemoteA2aHealth(), fetchRemoteA2aRegistry(), fetchRemoteMcpRegistry(), fetchReportDetail(), fetchReports(), fetchScenarios(), fetchTelemetry(), fetchTrends() (+20 more)

### Community 5 - "Community 5"
Cohesion: 0.1
Nodes (21): RemoteMCPRegistryResponse, fetchall(), fetchone(), get_customer_profile(), get_order(), get_order_history(), get_payment_issues(), get_policy() (+13 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (7): main(), transport_events(), DemoModeTests, main(), parse_csv(), run_diagnostics(), summarize_transport_events()

### Community 7 - "Community 7"
Cohesion: 0.1
Nodes (18): card(), build_server(), main(), build_server(), main(), A2A vs MCP comparative demo package., a2a_skill_id(), agent_card_payload() (+10 more)

### Community 8 - "Community 8"
Cohesion: 0.05
Nodes (1): WebUiTests

### Community 9 - "Community 9"
Cohesion: 0.12
Nodes (32): ApiRunRequest, AppliedTrendFiltersResponse, AppliedTrendSortingResponse, AverageTotalsResponse, ComparisonMetricsResponse, CountByModeResponse, CountByScenarioResponse, HealthResponse (+24 more)

### Community 10 - "Community 10"
Cohesion: 0.16
Nodes (9): artifact_update_event(), message_payload(), status_update_event(), task_snapshot(), RemoteA2ABroker, agent_card_from_payload(), new_id(), utc_now() (+1 more)

### Community 11 - "Community 11"
Cohesion: 0.14
Nodes (1): MCPClient

### Community 12 - "Community 12"
Cohesion: 0.15
Nodes (6): build_parser(), main(), RemoteA2ARegistry, RemoteA2AClient, api_remote_a2a_health(), api_remote_a2a_registry()

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (10): eventBorderColor(), getProtocolColor(), buildTimelineBars(), envelopePayload(), groupA2AEventsByTaskId(), isA2AEvent(), traceEventProtocol(), traceEventSummary() (+2 more)

### Community 14 - "Community 14"
Cohesion: 0.19
Nodes (6): build_reasoner(), FakeReasoningEngine, LLMReasoner, MockReasoner, Deterministic reasoning stub for tests that exercise the LLM path without an API, TicketIntent

### Community 15 - "Community 15"
Cohesion: 0.5
Nodes (7): emit_component(), inline_object(), literal(), main(), ref_name(), schema_type(), ts_name()

### Community 16 - "Community 16"
Cohesion: 0.38
Nodes (3): buildSnapshotSvg(), escapeXml(), handleDownload()

### Community 17 - "Community 17"
Cohesion: 0.33
Nodes (5): Async FastAPI integration tests — exercises ASGI app in-process via httpx., Full request path for MCP mode through the FastAPI ASGI app without a real serve, FakeReasoningEngine produces a non-empty answer for all modes without OPENAI_API, test_api_fake_llm_runtime_returns_canned_answer(), test_api_mcp_mode_end_to_end_async()

### Community 18 - "Community 18"
Cohesion: 0.53
Nodes (4): load_seed(), main(), validate(), ValidationResult

### Community 20 - "Community 20"
Cohesion: 0.83
Nodes (3): load_json(), main(), validate_presets()

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (2): inspect_bundle(), main()

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (1): Shared pytest configuration: sys.path setup and test environment variables.

## Knowledge Gaps
- **6 isolated node(s):** `Async FastAPI integration tests — exercises ASGI app in-process via httpx.`, `Full request path for MCP mode through the FastAPI ASGI app without a real serve`, `FakeReasoningEngine produces a non-empty answer for all modes without OPENAI_API`, `Shared pytest configuration: sys.path setup and test environment variables.`, `A2A vs MCP comparative demo package.` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 8`** (38 nodes): `setUpClass()`, `WebUiTests`, `.test_api_a2a_health_accepts_override_urls()`, `.test_api_exposes_remote_a2a_registry()`, `.test_api_exposes_remote_mcp_registry()`, `.test_api_health_reports_backend_status()`, `.test_api_remote_urls_reject_external_hosts_by_default()`, `.test_api_report_accepts_sorting()`, `.test_api_report_includes_export_urls()`, `.test_api_report_rejects_unsafe_report_names()`, `.test_api_report_returns_404_for_missing_report()`, `.test_api_report_trends_accepts_sorting()`, `.test_api_report_trends_aggregates_saved_runs()`, `.test_api_report_trends_can_be_filtered()`, `.test_api_run_profile_can_enable_report_and_external_logs()`, `.test_api_run_rejects_invalid_enums()`, `.test_api_run_returns_404_for_missing_scenario()`, `.test_api_run_returns_summary_results_and_scorecard()`, `.test_api_scenarios_include_metadata()`, `.test_api_supports_user_scoped_reports_and_telemetry()`, `.test_export_report_route_renders_evidence_bundle()`, `.test_export_report_route_renders_html()`, `.test_export_report_route_renders_pdf()`, `.test_index_page_loads_react_app()`, `.test_learning_page_loads_react_app()`, `.test_legacy_index_page_remains_available()`, `.test_openapi_contains_contract_schemas()`, `.test_run_endpoint_accepts_failure_toggles()`, `.test_run_endpoint_accepts_mcp_transport_selection()`, `.test_run_endpoint_renders_results()`, `.test_run_endpoint_uses_profile_defaults_for_logs()`, `.test_run_form_shows_profile_and_log_controls()`, `.test_trend_view_accepts_filters()`, `.test_trend_view_contains_drilldown_actions()`, `.test_trend_view_renders_in_results_panel()`, `.test_trend_view_shows_active_filter_chips()`, `.test_trend_view_shows_sort_controls()`, `test_web_ui.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 11`** (24 nodes): `MCPClient`, `._build_server()`, `._build_stdio_params()`, `.call()`, `._call_once_http()`, `._call_once_in_process()`, `._call_once_stdio()`, `.close()`, `._collect_http_process_stderr()`, `._discover_resources_and_prompts()`, `._discover_tools()`, `._find_open_port()`, `.__init__()`, `._list_resources_prompts_http()`, `._list_resources_prompts_in_process()`, `._list_resources_prompts_stdio()`, `._list_tools_http()`, `._list_tools_in_process()`, `._list_tools_stdio()`, `._simulate_failure()`, `._start_http_server()`, `._unwrap_structured()`, `._wait_for_port()`, `._rebuild_sqlite()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (3 nodes): `inspect_bundle()`, `main()`, `import_evidence_bundle.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (2 nodes): `Shared pytest configuration: sys.path setup and test environment variables.`, `conftest.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DemoPlatform` connect `Community 3` to `Community 0`, `Community 1`, `Community 2`, `Community 6`, `Community 7`, `Community 10`, `Community 11`, `Community 12`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `MCPClient` connect `Community 11` to `Community 0`, `Community 3`, `Community 7`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `ReportService` connect `Community 1` to `Community 2`, `Community 3`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 56 inferred relationships involving `DemoPlatform` (e.g. with `FlakyHandler` and `DemoModeTests`) actually correct?**
  _`DemoPlatform` has 56 INFERRED edges - model-reasoned connections that need verification._
- **Are the 45 inferred relationships involving `AgentResult` (e.g. with `FlakyHandler` and `DemoModeTests`) actually correct?**
  _`AgentResult` has 45 INFERRED edges - model-reasoned connections that need verification._
- **Are the 42 inferred relationships involving `A2AMessage` (e.g. with `FlakyHandler` and `DemoModeTests`) actually correct?**
  _`A2AMessage` has 42 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `DemoModeTests` (e.g. with `A2ABroker` and `AgentContext`) actually correct?**
  _`DemoModeTests` has 9 INFERRED edges - model-reasoned connections that need verification._