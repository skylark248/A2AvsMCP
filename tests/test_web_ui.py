import io
import os
import sys
import zipfile
import unittest
from unittest.mock import patch
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("A2A_VS_MCP_ARTIFACT_ROOT", str(PROJECT_ROOT / ".tmp" / "test_artifacts"))
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastapi.testclient import TestClient

from a2a_vs_mcp.web import app


class WebUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_index_page_loads_react_app(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("A2A vs MCP Frontend", response.text)
        self.assertIn('id="root"', response.text)

    def test_learning_page_loads_react_app(self) -> None:
        response = self.client.get("/learn")
        self.assertEqual(response.status_code, 200)
        self.assertIn("A2A vs MCP Frontend", response.text)
        self.assertIn('id="root"', response.text)
    def test_legacy_index_page_remains_available(self) -> None:
        response = self.client.get("/legacy")
        self.assertEqual(response.status_code, 200)
        self.assertIn("A2A vs MCP Demo UI", response.text)
        self.assertIn("Run Comparison", response.text)
        self.assertIn("Saved Report Trends", response.text)

    def test_run_endpoint_renders_results(self) -> None:
        response = self.client.post(
            "/legacy/run",
            data={"scenario": "order_status", "mode": "all", "runtime": "mock", "query": "", "customer_id": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Comparison Table", response.text)
        self.assertIn("Execution Timelines", response.text)
        self.assertIn("baseline", response.text.lower())
        self.assertIn("Report Scorecard", response.text)

    def test_run_endpoint_accepts_failure_toggles(self) -> None:
        response = self.client.post(
            "/legacy/run",
            data={
                "scenario": "delay_and_billing",
                "mode": "hybrid",
                "runtime": "mock",
                "query": "",
                "customer_id": "",
                "db_down": "1",
                "disable_agent": "policy_or_billing_agent",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Failures", response.text)
        self.assertIn("delay and billing", response.text.lower())

    def test_run_form_shows_profile_and_log_controls(self) -> None:
        response = self.client.get("/legacy")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Config Profile", response.text)
        self.assertIn('name="profile"', response.text)
        self.assertIn("MCP Transport Override", response.text)
        self.assertIn('name="mcp_transport"', response.text)
        self.assertIn('option value="http"', response.text)
        self.assertIn('name="export_logs"', response.text)
        self.assertIn("Profile default", response.text)

    def test_run_endpoint_accepts_mcp_transport_selection(self) -> None:
        response = self.client.post(
            "/legacy/run",
            data={
                "scenario": "setup_error",
                "mode": "mcp",
                "runtime": "mock",
                "mcp_transport": "stdio",
                "query": "",
                "customer_id": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Comparison Table", response.text)
        self.assertIn('"requested_transport": "stdio"', response.text)
        self.assertIn('"mcp_transport": "stdio"', response.text)


    def test_run_endpoint_uses_profile_defaults_for_logs(self) -> None:
        response = self.client.post(
            "/legacy/run",
            data={
                "profile": "demo",
                "scenario": "order_status",
                "mode": "baseline",
                "runtime": "",
                "mcp_transport": "",
                "query": "",
                "customer_id": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("External log:", response.text)
        self.assertIn("test_artifacts", response.text)
        self.assertIn("logs", response.text)

    def test_api_run_returns_summary_results_and_scorecard(self) -> None:
        response = self.client.post(
            "/api/run",
            json={"scenario": "enterprise_delay_refund", "mode": "all", "runtime": "mock", "save_report": True},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["results"]), 4)
        self.assertTrue(payload["report_name"])
        self.assertIn("talking_points", payload["summary"])
        self.assertIn("scorecard", payload["summary"])
        self.assertEqual(len(payload["summary"]["scorecard"]["mode_scorecards"]), 4)
        self.assertIn("recommended_demo_mode", payload["summary"]["scorecard"])
        self.assertGreaterEqual(payload["summary"]["scorecard"]["mode_scorecards"][0]["overall_score"], 0)

    def test_api_run_profile_can_enable_report_and_external_logs(self) -> None:
        response = self.client.post(
            "/api/run",
            json={"profile": "demo", "scenario": "order_status", "mode": "baseline"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["report_name"])
        self.assertTrue(payload["results"][0]["external_log_path"])

    def test_api_scenarios_include_metadata(self) -> None:
        response = self.client.get("/api/scenarios")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        scenario = next(item for item in payload["scenarios"] if item["key"] == "enterprise_setup_replacement")
        self.assertEqual(scenario["difficulty"], "advanced")
        self.assertIn("enterprise", scenario["tags"])

    def test_export_report_route_renders_html(self) -> None:
        run_response = self.client.post(
            "/api/run",
            json={"scenario": "order_status", "mode": "all", "runtime": "mock", "save_report": True},
        )
        report_name = run_response.json()["report_name"]
        response = self.client.get(f"/reports/{report_name}/export")
        self.assertEqual(response.status_code, 200)
        self.assertIn("A2A vs MCP Presentation Report", response.text)
        self.assertIn("Shipment Status Check", response.text)
        self.assertIn("Mode Scorecards", response.text)
        self.assertIn("Metric Charts", response.text)
        self.assertIn("Visual Scorecards", response.text)
        self.assertIn("Presentation Snapshot", response.text)
        self.assertIn("Printable takeaway", response.text)

    def test_export_report_route_renders_pdf(self) -> None:
        run_response = self.client.post(
            "/api/run",
            json={"scenario": "order_status", "mode": "all", "runtime": "mock", "save_report": True},
        )
        report_name = run_response.json()["report_name"]
        response = self.client.get(f"/reports/{report_name}/export.pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF-1.4"))

    def test_export_report_route_renders_evidence_bundle(self) -> None:
        run_response = self.client.post(
            "/api/run",
            json={"scenario": "order_status", "mode": "all", "runtime": "mock", "save_report": True},
        )
        report_name = run_response.json()["report_name"]
        response = self.client.get(f"/reports/{report_name}/evidence.zip")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/zip")
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            names = set(archive.namelist())
        self.assertIn("manifest.json", names)
        self.assertIn("evidence/summary.json", names)
        self.assertIn("evidence/scenario.json", names)
        self.assertIn("evidence/traces/baseline.json", names)

    def test_api_report_includes_export_urls(self) -> None:
        run_response = self.client.post(
            "/api/run",
            json={"scenario": "double_charge", "mode": "all", "runtime": "mock", "save_report": True},
        )
        report_name = run_response.json()["report_name"]
        response = self.client.get(f"/api/reports/{report_name}")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["export_url"].endswith("/export"))
        self.assertTrue(payload["pdf_export_url"].endswith("/export.pdf"))
        self.assertTrue(payload["evidence_export_url"].endswith("/evidence.zip"))

    def test_api_report_accepts_sorting(self) -> None:
        run_response = self.client.post(
            "/api/run",
            json={"scenario": "double_charge", "mode": "all", "runtime": "mock", "save_report": True},
        )
        report_name = run_response.json()["report_name"]
        response = self.client.get(f"/api/reports/{report_name}?score_sort=mode&score_dir=asc&result_sort=mode&result_dir=desc")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["sorting"]["score_sort"], "mode")
        score_modes = [item["mode"] for item in payload["summary"]["scorecard"]["mode_scorecards"]]
        self.assertEqual(score_modes, sorted(score_modes))


    def test_api_report_trends_aggregates_saved_runs(self) -> None:
        self.client.post("/api/run", json={"scenario": "order_status", "mode": "all", "runtime": "mock", "save_report": True})
        self.client.post("/api/run", json={"scenario": "double_charge", "mode": "all", "runtime": "mock", "save_report": True})
        response = self.client.get("/api/reports/trends")
        self.assertEqual(response.status_code, 200)
        payload = response.json()["trends"]
        self.assertGreaterEqual(payload["total_reports"], 2)
        self.assertTrue(payload["mode_trends"])
        self.assertTrue(payload["narrative"])
        self.assertIn("mode", payload["mode_trends"][0])
        self.assertIn("local", payload["a2a_transport_counts"])

    def test_api_report_trends_can_be_filtered(self) -> None:
        self.client.post("/api/run", json={"scenario": "order_status", "mode": "all", "runtime": "mock", "save_report": True})
        self.client.post("/api/run", json={"scenario": "double_charge", "mode": "all", "runtime": "mock", "save_report": True})
        response = self.client.get("/api/reports/trends?scenario=order_status")
        self.assertEqual(response.status_code, 200)
        payload = response.json()["trends"]
        self.assertGreaterEqual(payload["total_reports"], 1)
        self.assertTrue(all(item["scenario"] == "order_status" for item in payload["scenario_counts"]))
        self.assertEqual(payload["applied_filters"]["scenario"], "order_status")

    def test_api_report_trends_accepts_sorting(self) -> None:
        self.client.post("/api/run", json={"scenario": "order_status", "mode": "all", "runtime": "mock", "save_report": True})
        self.client.post("/api/run", json={"scenario": "double_charge", "mode": "all", "runtime": "mock", "save_report": True})
        response = self.client.get("/api/reports/trends?mode_sort=mode&mode_dir=asc&report_sort=report&report_dir=asc")
        self.assertEqual(response.status_code, 200)
        payload = response.json()["trends"]
        self.assertEqual(payload["applied_sorting"]["mode_sort"], "mode")
        self.assertEqual(payload["applied_sorting"]["report_sort"], "report")
        mode_names = [item["mode"] for item in payload["mode_trends"]]
        self.assertEqual(mode_names, sorted(mode_names))


    def test_trend_view_renders_in_results_panel(self) -> None:
        self.client.post("/api/run", json={"scenario": "order_status", "mode": "all", "runtime": "mock", "save_report": True})
        self.client.post("/api/run", json={"scenario": "double_charge", "mode": "all", "runtime": "mock", "save_report": True})
        response = self.client.get("/legacy/trends")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Cross-Run Trend View", response.text)
        self.assertIn("Mode Trend Table", response.text)
        self.assertIn("Recent Reports", response.text)

    def test_trend_view_contains_drilldown_actions(self) -> None:
        self.client.post("/api/run", json={"scenario": "order_status", "mode": "all", "runtime": "mock", "save_report": True})
        self.client.post("/api/run", json={"scenario": "double_charge", "mode": "all", "runtime": "mock", "save_report": True})
        response = self.client.get("/legacy/trends")
        self.assertEqual(response.status_code, 200)
        self.assertIn('/legacy/trends?scenario=', response.text)
        self.assertIn('/legacy/trends?recommended_mode=', response.text)
        self.assertIn('/legacy/reports/', response.text)

    def test_trend_view_accepts_filters(self) -> None:
        self.client.post("/api/run", json={"scenario": "order_status", "mode": "all", "runtime": "mock", "save_report": True})
        self.client.post("/api/run", json={"scenario": "double_charge", "mode": "all", "runtime": "mock", "save_report": True})
        response = self.client.get("/legacy/trends?scenario=order_status")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Trend Filters", response.text)
        self.assertIn("Order Status", response.text)

    def test_trend_view_shows_active_filter_chips(self) -> None:
        self.client.post("/api/run", json={"scenario": "order_status", "mode": "all", "runtime": "mock", "save_report": True})
        self.client.post("/api/run", json={"scenario": "double_charge", "mode": "all", "runtime": "mock", "save_report": True})
        response = self.client.get("/legacy/trends?scenario=order_status")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Active Filters", response.text)
        self.assertIn("Clear All Filters", response.text)
        self.assertIn("Scenario: Order Status", response.text)

    def test_trend_view_shows_sort_controls(self) -> None:
        self.client.post("/api/run", json={"scenario": "order_status", "mode": "all", "runtime": "mock", "save_report": True})
        self.client.post("/api/run", json={"scenario": "double_charge", "mode": "all", "runtime": "mock", "save_report": True})
        response = self.client.get("/legacy/trends")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Sort Mode Trends", response.text)
        self.assertIn("Sort Reports", response.text)
        self.assertIn("Sort Scenarios", response.text)



    def test_api_supports_user_scoped_reports_and_telemetry(self) -> None:
        user_id = "alice-tests"
        other_user_id = "bob-tests"
        run_response = self.client.post(
            "/api/run",
            headers={"X-Demo-User": user_id},
            json={"profile": "demo", "scenario": "order_status", "mode": "baseline", "runtime": "mock", "save_report": True},
        )
        self.assertEqual(run_response.status_code, 200)
        report_name = run_response.json()["report_name"]

        own_reports = self.client.get("/api/reports", headers={"X-Demo-User": user_id}).json()["reports"]
        other_reports = self.client.get("/api/reports", headers={"X-Demo-User": other_user_id}).json()["reports"]
        self.assertIn(report_name, {item["report_name"] for item in own_reports})
        self.assertNotIn(report_name, {item["report_name"] for item in other_reports})

        detail = self.client.get(f"/api/reports/{report_name}", headers={"X-Demo-User": user_id}).json()
        self.assertIn("user_id=alice-tests", detail["evidence_export_url"])
        export_response = self.client.get(detail["evidence_export_url"])
        self.assertEqual(export_response.status_code, 200)
        self.assertEqual(export_response.headers["content-type"], "application/zip")

        telemetry = self.client.get("/api/telemetry", headers={"X-Demo-User": user_id}).json()
        self.assertGreaterEqual(telemetry["total_runs"], 1)
        self.assertIn("baseline", telemetry["mode_counts"])
        self.assertIn("local", telemetry["a2a_transport_counts"])

    def test_api_exposes_remote_mcp_registry(self) -> None:
        response = self.client.get("/api/mcp/registry")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["servers"])
        self.assertIn("db_url", payload["servers"][0])
        self.assertIn("docs_url", payload["servers"][0])
    def test_api_exposes_remote_a2a_registry(self) -> None:
        response = self.client.get("/api/a2a/registry")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["agents"])
        self.assertIn("role", payload["agents"][0])
        self.assertIn("url", payload["agents"][0])

    def test_api_remote_urls_reject_external_hosts_by_default(self) -> None:
        with patch.dict("os.environ", {"A2A_VS_MCP_ALLOW_EXTERNAL_REMOTE_URLS": ""}, clear=False):
            response = self.client.post(
                "/api/run",
                json={
                    "scenario": "order_status",
                    "mode": "a2a",
                    "a2a_transport": "remote",
                    "remote_a2a_customer_url": "https://example.com/a2a",
                },
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("external host", response.json()["detail"])

    def test_api_a2a_health_accepts_override_urls(self) -> None:
        response = self.client.get("/api/a2a/health?customer_url=http://127.0.0.1:1")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["agents"]), 1)
        self.assertEqual(payload["agents"][0]["role"], "customer_data")
        self.assertEqual(payload["agents"][0]["status"], "unavailable")

    def test_api_health_reports_backend_status(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("dev", payload["profiles"])
        self.assertGreater(payload["scenarios"], 0)
        self.assertTrue(payload["artifacts_dir"].endswith("artifacts"))
        self.assertIn(payload["mcp_transport_default"], {"in_process", "stdio", "http", "remote_http"})
        self.assertEqual(payload["a2a_transport_default"], "local")

    def test_api_run_rejects_invalid_enums(self) -> None:
        response = self.client.post("/api/run", json={"scenario": "order_status", "mode": "bogus"})
        self.assertEqual(response.status_code, 422)
        error_text = response.text
        self.assertIn("baseline", error_text)
        self.assertIn("hybrid", error_text)

    def test_api_run_returns_404_for_missing_scenario(self) -> None:
        response = self.client.post("/api/run", json={"scenario": "missing_scenario", "mode": "baseline"})
        self.assertEqual(response.status_code, 404)
        self.assertIn("Scenario not found", response.json()["detail"])

    def test_api_report_returns_404_for_missing_report(self) -> None:
        response = self.client.get("/api/reports/missing-report.json")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Report not found", response.json()["detail"])

    def test_api_report_rejects_unsafe_report_names(self) -> None:
        response = self.client.get("/api/reports/%2e%2e%2Fsecret.json")
        self.assertIn(response.status_code, {400, 404})

    def test_openapi_contains_contract_schemas(self) -> None:
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        schemas = payload["components"]["schemas"]
        self.assertIn("/api/health", payload["paths"])
        self.assertIn("ApiRunRequest", schemas)
        self.assertIn("RunResponse", schemas)
        self.assertIn("RemoteA2AHealthResponse", schemas)
        mode_schema = schemas["ApiRunRequest"]["properties"]["mode"]
        self.assertEqual(mode_schema["enum"], ["baseline", "mcp", "a2a", "hybrid", "all"])
        transport_schema = schemas["ApiRunRequest"]["properties"]["mcp_transport"]["anyOf"][0]
        self.assertEqual(transport_schema["enum"], ["in_process", "stdio", "http", "remote_http"])
        for failure_toggle in [
            "remote_a2a_timeout",
            "remote_a2a_bad_auth",
            "remote_a2a_missing_capability",
            "remote_a2a_malformed_response",
            "remote_a2a_task_failure",
        ]:
            self.assertIn(failure_toggle, schemas["ApiRunRequest"]["properties"])
        a2a_transport_schema = schemas["ApiRunRequest"]["properties"]["a2a_transport"]["anyOf"][0]
        self.assertEqual(a2a_transport_schema["enum"], ["local", "remote"])
if __name__ == "__main__":
    unittest.main()








