import json
import os
import socket
import subprocess
import sys
import time
from urllib import request
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("A2A_VS_MCP_ARTIFACT_ROOT", str(PROJECT_ROOT / ".tmp" / "test_artifacts"))
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from a2a_vs_mcp.a2a.broker import A2ABroker
from a2a_vs_mcp.agents.base import AgentContext
from a2a_vs_mcp.dataset import DemoRepository
from a2a_vs_mcp.identity import base_artifact_root, user_artifact_root
from a2a_vs_mcp.platform import DemoPlatform
from a2a_vs_mcp.schemas import A2AMessage, AgentCard, AgentResult, FailureConfig
from a2a_vs_mcp.trace import TraceRecorder


class FlakyHandler:
    def __init__(self) -> None:
        self.calls = 0

    def handle_task(self, message: A2AMessage) -> AgentResult:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("temporary failure")
        return AgentResult(agent_id="flaky_agent", summary="Recovered after retry.", details={"attempt": self.calls})


class DemoModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.platform = DemoPlatform(PROJECT_ROOT, runtime="mock")

    def test_artifact_root_override_is_respected(self) -> None:
        absolute_root = PROJECT_ROOT / ".tmp" / "custom_artifacts"
        with patch.dict(os.environ, {"A2A_VS_MCP_ARTIFACT_ROOT": str(absolute_root)}):
            self.assertEqual(base_artifact_root(PROJECT_ROOT), absolute_root)
            self.assertEqual(user_artifact_root(PROJECT_ROOT, "alice tests"), absolute_root / "users" / "alice_tests")
            self.assertEqual(user_artifact_root(PROJECT_ROOT, None), absolute_root)

        with patch.dict(os.environ, {"A2A_VS_MCP_ARTIFACT_ROOT": ".tmp/relative_artifacts"}):
            self.assertEqual(base_artifact_root(PROJECT_ROOT), PROJECT_ROOT / ".tmp" / "relative_artifacts")

    def test_all_modes_return_answers(self) -> None:
        ticket = self.platform.get_ticket("order_status", None, None)
        for mode in ("baseline", "mcp", "a2a", "hybrid"):
            result = self.platform.run(mode, ticket)
            self.assertTrue(result.final_answer)
            self.assertEqual(result.metrics.mode, mode)

    def test_mcp_mode_uses_tool_calls(self) -> None:
        ticket = self.platform.get_ticket("setup_error", None, None)
        result = self.platform.run("mcp", ticket)
        self.assertGreater(result.metrics.tool_calls, 0)
        self.assertIn("search_docs", result.tools_used)

    def test_mcp_stdio_transport_can_run_when_requested(self) -> None:
        platform = DemoPlatform(PROJECT_ROOT, runtime="mock", mcp_transport="stdio")
        ticket = platform.get_ticket("setup_error", None, None)
        result = platform.run("mcp", ticket)
        self.assertGreater(result.metrics.tool_calls, 0)
        discovery_event = next(event for event in result.trace if event["event_type"] == "tool_discovery")
        self.assertEqual(discovery_event["requested_transport"], "stdio")

    def test_mcp_http_transport_can_run_when_requested(self) -> None:
        platform = DemoPlatform(PROJECT_ROOT, runtime="mock", mcp_transport="http")
        ticket = platform.get_ticket("setup_error", None, None)
        result = platform.run("mcp", ticket)
        self.assertGreater(result.metrics.tool_calls, 0)
        discovery_event = next(event for event in result.trace if event["event_type"] == "tool_discovery")
        self.assertFalse(result.failures)
        self.assertEqual(discovery_event["requested_transport"], "http")
        self.assertEqual(discovery_event["transport"], "http")


    def test_remote_http_transport_falls_back_without_urls(self) -> None:
        platform = DemoPlatform(PROJECT_ROOT, runtime="mock", mcp_transport="remote_http")
        ticket = platform.get_ticket("setup_error", None, None)
        result = platform.run("mcp", ticket)
        discovery_event = next(event for event in result.trace if event["event_type"] == "tool_discovery")
        fallback_event = next(event for event in result.trace if event["event_type"] == "tool_transport_fallback")
        self.assertEqual(discovery_event["requested_transport"], "remote_http")
        self.assertEqual(discovery_event["transport"], "in_process")
        self.assertEqual(fallback_event["requested_transport"], "remote_http")
    def test_demo_profile_applies_defaults(self) -> None:
        platform = DemoPlatform(PROJECT_ROOT, profile_name="demo")
        self.assertEqual(platform.profile.name, "demo")
        self.assertEqual(platform.runtime, "mock")
        self.assertEqual(platform.mcp_transport, "http")
        self.assertTrue(platform.export_logs)

    def test_export_logs_writes_ndjson_records(self) -> None:
        platform = DemoPlatform(PROJECT_ROOT, profile_name="demo")
        ticket = platform.get_ticket("order_status", None, None)
        result = platform.run("baseline", ticket)
        self.assertTrue(result.external_log_path)
        log_path = Path(result.external_log_path)
        self.assertTrue(log_path.exists())
        lines = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertGreater(len(lines), 0)
        first = json.loads(lines[0])
        self.assertIn("run", first)
        self.assertIn("event", first)
        self.assertEqual(first["run"]["profile"], "demo")

    def test_a2a_mode_uses_messages_without_tools(self) -> None:
        ticket = self.platform.get_ticket("double_charge", None, None)
        result = self.platform.run("a2a", ticket)
        self.assertGreater(result.metrics.a2a_messages, 0)
        self.assertEqual(result.metrics.tool_calls, 0)

    def test_hybrid_mode_combines_both_protocols(self) -> None:
        ticket = self.platform.get_ticket("warranty_return", None, None)
        result = self.platform.run("hybrid", ticket)
        self.assertGreater(result.metrics.a2a_messages, 0)
        self.assertGreater(result.metrics.tool_calls, 0)

    def test_hybrid_mode_honors_mcp_transport_selection(self) -> None:
        platform = DemoPlatform(PROJECT_ROOT, runtime="mock", mcp_transport="http")
        ticket = platform.get_ticket("setup_error", None, None)
        result = platform.run("hybrid", ticket)
        discovery_event = next(event for event in result.trace if event["event_type"] == "tool_discovery")
        self.assertFalse(result.failures)
        self.assertEqual(discovery_event["requested_transport"], "http")
        self.assertEqual(discovery_event["transport"], "http")

    def test_agent_context_reuses_shared_mcp_clients(self) -> None:
        class FakeMCPClient:
            def __init__(self, *args, **kwargs) -> None:
                self.args = args
                self.kwargs = kwargs
                self.closed = 0

            def close(self) -> None:
                self.closed += 1

        context = AgentContext(
            DemoRepository(PROJECT_ROOT),
            TraceRecorder(mode="hybrid", runtime="mock", task_id="pool-test"),
            "mock",
            "http",
            PROJECT_ROOT,
            FailureConfig(),
        )
        with patch("a2a_vs_mcp.mcp.client.MCPClient", FakeMCPClient):
            first = context.get_mcp_client("a2a_vs_mcp.mcp_servers.db_server", db_path="demo.db")
            second = context.get_mcp_client("a2a_vs_mcp.mcp_servers.db_server", db_path="demo.db")
            third = context.get_mcp_client("a2a_vs_mcp.mcp_servers.docs_server", docs_dir="docs")

        self.assertIs(first, second)
        self.assertIsNot(first, third)
        context.close_mcp_clients()
        self.assertEqual(first.closed, 1)
        self.assertEqual(third.closed, 1)
        self.assertEqual(context.mcp_clients, {})
    def test_a2a_trace_includes_protocol_shaped_payloads(self) -> None:
        ticket = self.platform.get_ticket("warranty_return", None, None)
        result = self.platform.run("a2a", ticket)

        register_event = next(event for event in result.trace if event.get("message_type") == "agent_register")
        self.assertEqual(register_event["a2a_protocol_version"], "1.0")
        self.assertEqual(register_event["a2a_agent_card"]["protocolVersion"], "1.0")
        self.assertTrue(register_event["a2a_agent_card"]["skills"])

        request_event = next(event for event in result.trace if event.get("message_type") == "task_request")
        self.assertEqual(request_event["a2a_method"], "message/send")
        self.assertEqual(request_event["a2a_message"]["role"], "ROLE_USER")
        self.assertEqual(request_event["a2a_message"]["parts"][0]["kind"], "data")

        status_event = next(event for event in result.trace if event.get("event_type") == "task_status" and event.get("status") == "completed")
        self.assertEqual(status_event["a2a_state"], "completed")
        self.assertEqual(status_event["a2a_task_event"]["kind"], "status-update")
        self.assertTrue(status_event["a2a_task_event"]["final"])

        artifact_event = next(event for event in result.trace if event.get("event_type") == "a2a_task_artifact")
        self.assertEqual(artifact_event["a2a_artifact_event"]["kind"], "artifact-update")
        self.assertEqual(artifact_event["a2a_artifact_event"]["artifact"]["parts"][0]["kind"], "text")

    def test_trace_enrichment_phase_field_on_all_events(self) -> None:
        """Every trace event carries a 'phase' field valued 'discovery' or 'execution' (TRACE-03)."""
        ticket = self.platform.get_ticket("order_status", None, None)
        result = self.platform.run("mcp", ticket)
        valid_phases = {"discovery", "execution"}
        for event in result.trace:
            self.assertIn(
                "phase", event,
                msg=f"Event {event['event_type']} missing 'phase' field"
            )
            self.assertIn(
                event["phase"], valid_phases,
                msg=f"Event {event['event_type']} has invalid phase={event['phase']!r}"
            )

    def test_trace_enrichment_step_index_on_tool_calls(self) -> None:
        """tool_call events carry sequential step_index; non-action events do not (TRACE-01)."""
        ticket = self.platform.get_ticket("order_status", None, None)
        result = self.platform.run("mcp", ticket)
        tool_call_events = [e for e in result.trace if e["event_type"] == "tool_call"]
        self.assertGreater(len(tool_call_events), 0, "Expected at least one tool_call event in mcp mode")
        step_indices = [e["step_index"] for e in tool_call_events]
        # step_index must be present on all tool_call events
        for idx, event in enumerate(tool_call_events):
            self.assertIn("step_index", event, msg=f"tool_call event #{idx} missing step_index")
            self.assertIsInstance(event["step_index"], int)
        # step_index must be sequential starting at 1
        self.assertEqual(step_indices, list(range(1, len(step_indices) + 1)),
            msg=f"step_index not sequential: {step_indices}")
        # non-action events must NOT have step_index
        non_action_types = {"a2a_message", "task_status", "agent_reasoning", "agent_register"}
        for event in result.trace:
            if event["event_type"] in non_action_types:
                self.assertNotIn(
                    "step_index", event,
                    msg=f"Event type '{event['event_type']}' should not have step_index"
                )

    def test_send_tasks_parallel_emits_batch_fields(self) -> None:
        """send_tasks_parallel() emits task_submit events with parallel_batch_id and timing (TRACE-02, TRACE-04)."""
        trace = TraceRecorder(mode="a2a", runtime="mock", task_id="parallel-test")
        broker = A2ABroker(trace, max_retries=0, timeout_ms=5000)
        self.assertEqual(broker.timeout_ms, 5000, "timeout_ms default must be 5000 (TRACE-04)")

        # Register two fake specialist handlers
        class AgentAHandler:
            def handle_task(self, message: A2AMessage) -> AgentResult:
                return AgentResult(agent_id="agent_a", summary="agent_a done", details={})

        class AgentBHandler:
            def handle_task(self, message: A2AMessage) -> AgentResult:
                return AgentResult(agent_id="agent_b", summary="agent_b done", details={})

        card_a = AgentCard(agent_id="agent_a", name="Agent A", capabilities=["cap_a"], description="test agent a")
        card_b = AgentCard(agent_id="agent_b", name="Agent B", capabilities=["cap_b"], description="test agent b")
        broker.register(card_a, AgentAHandler())
        broker.register(card_b, AgentBHandler())

        msg_a = A2AMessage(
            message_type="task_request",
            sender_agent="triage",
            target_agent="agent_a",
            capability="cap_a",
            payload={"query": "do cap_a"},
            task_id="task-a",
        )
        msg_b = A2AMessage(
            message_type="task_request",
            sender_agent="triage",
            target_agent="agent_b",
            capability="cap_b",
            payload={"query": "do cap_b"},
            task_id="task-b",
        )

        results = broker.send_tasks_parallel([msg_a, msg_b])
        self.assertEqual(len(results), 2)

        # Verify task_submit events
        submit_events = [e for e in trace.events if e["event_type"] == "task_submit"]
        self.assertEqual(len(submit_events), 2, "Expected 2 task_submit events from 2 parallel tasks")

        # All share same batch_id
        batch_ids = {e["parallel_batch_id"] for e in submit_events}
        self.assertEqual(len(batch_ids), 1, "All task_submit events must share the same parallel_batch_id")
        batch_id = batch_ids.pop()
        self.assertEqual(len(batch_id), 12, f"parallel_batch_id must be 12 hex chars, got: {batch_id!r}")

        # step_index present on all task_submit events
        for event in submit_events:
            self.assertIn("step_index", event, "task_submit event missing step_index")
            self.assertIsInstance(event["step_index"], int)

        # started_at present and is a positive epoch ms int
        for event in submit_events:
            self.assertIn("started_at", event)
            self.assertGreater(event["started_at"], 0)

        # task_complete events carry completed_at >= started_at
        complete_events = [e for e in trace.events if e["event_type"] == "task_complete"]
        self.assertEqual(len(complete_events), 2)
        for event in complete_events:
            self.assertIn("completed_at", event)
            self.assertIn("started_at", event)
            self.assertGreaterEqual(event["completed_at"], event["started_at"])

    def test_triage_deduplicates_overlapping_summaries(self) -> None:
        ticket = self.platform.get_ticket("warranty_return", None, None)
        result = self.platform.run("hybrid", ticket)
        self.assertEqual(result.final_answer.count("The product is still under standard warranty"), 1)
        self.assertIn("Internal contributions:", result.final_answer)

    def test_broker_retries_after_transient_failure(self) -> None:
        trace = TraceRecorder(mode="a2a", runtime="mock", task_id="retry-test")
        broker = A2ABroker(trace, max_retries=1, timeout_ms=1000)
        handler = FlakyHandler()
        broker.register(AgentCard("flaky_agent", "Flaky Agent", ["customer_data"], "retry demo"), handler)
        message = A2AMessage(
            message_type="task_request",
            sender_agent="triage_agent",
            target_agent="flaky_agent",
            capability="customer_data",
            payload={"ticket": {"ticket_id": "retry-test", "customer_id": "CUST-001", "query": "help"}},
            task_id="retry-test",
        )
        result = broker.send_task(message)
        self.assertEqual(result.summary, "Recovered after retry.")
        retry_events = [event for event in trace.events if event.get("message_type") == "task_retry"]
        self.assertEqual(len(retry_events), 1)

    def test_multi_step_scenario_mentions_multiple_concerns(self) -> None:
        ticket = self.platform.get_ticket("delay_and_billing", None, None)
        result = self.platform.run("hybrid", ticket)
        self.assertIn("duplicate-charge", result.final_answer)
        self.assertIn("Order ORD-1002", result.final_answer)
        self.assertEqual(result.final_answer.count("duplicate-charge"), 1)

    def test_setup_and_warranty_reads_more_naturally(self) -> None:
        ticket = self.platform.get_ticket("setup_and_warranty", None, None)
        result = self.platform.run("hybrid", ticket)
        self.assertIn("troubleshooting guidance", result.final_answer)
        self.assertIn("warranty", result.final_answer)

    def test_scen03_talking_point_on_ticket(self) -> None:
        """SCEN-03: device_failure_warranty_refund ticket carries talking_point from seed."""
        ticket = self.platform.get_ticket("device_failure_warranty_refund", None, None)
        self.assertIsNotNone(ticket.talking_point, "talking_point must not be None for device_failure_warranty_refund")
        self.assertIn("headline", ticket.talking_point)
        self.assertIn("sentence", ticket.talking_point)
        self.assertIn("callout", ticket.talking_point)

    def test_scen03_talking_point_on_vip_ticket(self) -> None:
        """SCEN-03: vip_parallel_escalation ticket carries talking_point from seed."""
        ticket = self.platform.get_ticket("vip_parallel_escalation", None, None)
        self.assertIsNotNone(ticket.talking_point, "talking_point must not be None for vip_parallel_escalation")
        self.assertIn("headline", ticket.talking_point)
        self.assertIn("sentence", ticket.talking_point)
        self.assertIn("callout", ticket.talking_point)

    def test_failure_toggle_records_db_outage(self) -> None:
        ticket = self.platform.get_ticket("double_charge", None, None)
        result = self.platform.run("mcp", ticket, failure_config=FailureConfig(db_down=True))
        self.assertGreater(result.metrics.failures, 0)
        self.assertTrue(any("database outage" in failure.lower() for failure in result.failures))

    def test_failure_toggle_records_unavailable_agent(self) -> None:
        ticket = self.platform.get_ticket("warranty_return", None, None)
        result = self.platform.run("a2a", ticket, failure_config=FailureConfig(unavailable_agents=["policy_or_billing_agent"]))
        self.assertGreater(result.metrics.failures, 0)
        self.assertTrue(any("policy_billing" in failure or "No agent registered" in failure for failure in result.failures))

    def test_remote_a2a_bad_auth_records_failure(self) -> None:
        platform = DemoPlatform(
            PROJECT_ROOT,
            runtime="mock",
            a2a_transport="remote",
            remote_a2a_urls={"customer_data": "http://127.0.0.1:1", "documentation": "http://127.0.0.1:2", "policy_billing": "http://127.0.0.1:3"},
        )
        ticket = platform.get_ticket("warranty_return", None, None)
        result = platform.run("a2a", ticket, failure_config=FailureConfig(remote_a2a_bad_auth=True))
        self.assertTrue(any("authentication" in failure or "No remote agent" in failure for failure in result.failures))
        self.assertTrue(any(event["event_type"] == "a2a_remote_failure" for event in result.trace))
    def test_deeper_scenarios_are_available(self) -> None:
        ticket = self.platform.get_ticket("enterprise_setup_replacement", None, None)
        self.assertEqual(ticket.title, "Enterprise Setup and Replacement Review")
        self.assertIn("enterprise", ticket.tags)
        result = self.platform.run("hybrid", ticket)
        self.assertIn("warranty", result.final_answer)
        self.assertIn("troubleshooting guidance", result.final_answer)


    def test_remote_a2a_transport_can_run_with_hosted_specialists(self) -> None:
        ports = [self._open_port() for _ in range(3)]
        roles = ["customer_data", "documentation", "policy_billing"]
        processes = []
        env = {**os.environ, "PYTHONPATH": str(SRC)}
        try:
            for role, port in zip(roles, ports):
                processes.append(
                    subprocess.Popen(
                        [
                            sys.executable,
                            "-m",
                            "a2a_vs_mcp.a2a.remote_server",
                            "--role",
                            role,
                            "--port",
                            str(port),
                            "--project-root",
                            str(PROJECT_ROOT),
                        ],
                        cwd=str(PROJECT_ROOT),
                        env=env,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                )
            for port in ports:
                self._wait_for_remote_health(port)
            platform = DemoPlatform(
                PROJECT_ROOT,
                runtime="mock",
                a2a_transport="remote",
                remote_a2a_urls={
                    "customer_data": f"http://127.0.0.1:{ports[0]}",
                    "documentation": f"http://127.0.0.1:{ports[1]}",
                    "policy_billing": f"http://127.0.0.1:{ports[2]}",
                },
            )
            ticket = platform.get_ticket("warranty_return", None, None)
            result = platform.run("a2a", ticket)
            self.assertTrue(result.final_answer)
            self.assertEqual(result.a2a_transport, "remote")
            self.assertTrue(any(event["event_type"] == "a2a_remote_discovery" for event in result.trace))
            self.assertTrue(any(event["event_type"] == "a2a_remote_artifact" for event in result.trace))
        finally:
            for process in processes:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)

    def test_scen02_parallel_emits_shared_batch_id(self) -> None:
        """SCEN-02: all task_submit events for vip_parallel_escalation share one parallel_batch_id."""
        ticket = self.platform.get_ticket("vip_parallel_escalation", None, None)
        result = self.platform.run("a2a", ticket)
        submits = [e for e in result.trace if e["event_type"] == "task_submit"]
        self.assertGreater(len(submits), 0, "Expected task_submit events in a2a parallel run")
        batch_ids = {e.get("parallel_batch_id") for e in submits}
        self.assertEqual(len(batch_ids), 1, f"All task_submit events must share one batch_id, got: {batch_ids}")
        self.assertIsNotNone(list(batch_ids)[0], "parallel_batch_id must not be None")

    def test_scen02_parallel_produces_no_failures(self) -> None:
        """SCEN-02: zero task_failed events under mock runtime for vip_parallel_escalation."""
        ticket = self.platform.get_ticket("vip_parallel_escalation", None, None)
        result = self.platform.run("a2a", ticket)
        failures = [e for e in result.trace if e["event_type"] == "task_failed"]
        self.assertEqual(len(failures), 0, f"Expected no task_failed events, got {len(failures)}: {failures}")

    def test_scen02_parallel_triggers_three_specialists(self) -> None:
        """SCEN-02: exactly 3 task_submit events — one per specialist — in vip_parallel_escalation a2a trace."""
        ticket = self.platform.get_ticket("vip_parallel_escalation", None, None)
        result = self.platform.run("a2a", ticket)
        submits = [e for e in result.trace if e["event_type"] == "task_submit"]
        self.assertGreaterEqual(len(submits), 3, f"Expected >= 3 task_submit events, got {len(submits)}")

    def _open_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def _wait_for_remote_health(self, port: int) -> None:
        deadline = time.time() + 10
        last_error = None
        while time.time() < deadline:
            try:
                with request.urlopen(f"http://127.0.0.1:{port}/health", timeout=0.5) as response:
                    if response.status == 200:
                        return
            except Exception as exc:
                last_error = exc
                time.sleep(0.1)
        raise AssertionError(f"Remote A2A server on {port} did not become healthy: {last_error}")
class TraceRecorderEnrichmentTests(unittest.TestCase):
    """Phase 2 Task 1 — TDD tests for step_index and phase enrichment."""

    def _make_recorder(self) -> TraceRecorder:
        return TraceRecorder(mode="a2a", runtime="mock", task_id="test-enrich")

    # Test 1: tool_call increments step_index starting at 1
    def test_tool_call_gets_step_index_starting_at_1(self) -> None:
        t = self._make_recorder()
        t.record("tool_call", tool="get_order")
        self.assertEqual(t.events[0]["step_index"], 1)

    # Test 2: second tool_call gets step_index 2
    def test_second_tool_call_gets_step_index_2(self) -> None:
        t = self._make_recorder()
        t.record("tool_call", tool="get_order")
        t.record("tool_call", tool="get_policy")
        self.assertEqual(t.events[1]["step_index"], 2)

    # Test 2b: task_submit shares the same counter as tool_call
    def test_task_submit_shares_step_counter_with_tool_call(self) -> None:
        t = self._make_recorder()
        t.record("tool_call", tool="get_order")
        t.record("task_submit", task_id="t1")
        self.assertEqual(t.events[0]["step_index"], 1)
        self.assertEqual(t.events[1]["step_index"], 2)

    # Test 3: a2a_message does NOT get step_index
    def test_a2a_message_has_no_step_index(self) -> None:
        t = self._make_recorder()
        t.record("a2a_message", message_type="task_request")
        self.assertNotIn("step_index", t.events[0])

    # Test 4: agent_register gets phase="discovery"
    def test_agent_register_gets_discovery_phase(self) -> None:
        t = self._make_recorder()
        t.record("agent_register", sender="triage")
        self.assertEqual(t.events[0]["phase"], "discovery")

    # Test 5: capability_advertise gets phase="discovery"
    def test_capability_advertise_gets_discovery_phase(self) -> None:
        t = self._make_recorder()
        t.record("capability_advertise", sender="triage")
        self.assertEqual(t.events[0]["phase"], "discovery")

    # Test 6: tool_call gets phase="execution"
    def test_tool_call_gets_execution_phase(self) -> None:
        t = self._make_recorder()
        t.record("tool_call", tool="get_order")
        self.assertEqual(t.events[0]["phase"], "execution")

    # Test 7: unknown event type defaults to phase="execution"
    def test_unknown_event_type_defaults_to_execution_phase(self) -> None:
        t = self._make_recorder()
        t.record("unknown_future_type")
        self.assertEqual(t.events[0]["phase"], "execution")

    # Test 8: fresh recorder starts step_counter at 0 (first tool_call = step_index 1)
    def test_fresh_recorder_step_counter_starts_at_zero(self) -> None:
        t = self._make_recorder()
        t.record("tool_call", tool="first")
        self.assertEqual(t.events[0]["step_index"], 1)


class A2ABrokerParallelTests(unittest.TestCase):
    """Phase 2 Task 2 — TDD tests for send_tasks_parallel() and timeout_ms default."""

    def _make_broker(self) -> tuple[A2ABroker, TraceRecorder]:
        trace = TraceRecorder(mode="a2a", runtime="mock", task_id="parallel-test")
        broker = A2ABroker(trace)
        return broker, trace

    def _register_echo_agent(self, broker: A2ABroker, agent_id: str, capability: str) -> None:
        class EchoHandler:
            def handle_task(self, message: A2AMessage) -> AgentResult:
                return AgentResult(agent_id=agent_id, summary=f"done-{agent_id}", details={})
        card = AgentCard(agent_id, agent_id, [capability], "echo")
        broker.register(card, EchoHandler())

    # Test 1: default timeout_ms is 5000
    def test_default_timeout_ms_is_5000(self) -> None:
        trace = TraceRecorder(mode="a2a", runtime="mock", task_id="t")
        broker = A2ABroker(trace)
        self.assertEqual(broker.timeout_ms, 5000)

    # Test 7: empty messages list returns []
    def test_send_tasks_parallel_empty_returns_empty(self) -> None:
        broker, _ = self._make_broker()
        result = broker.send_tasks_parallel([])
        self.assertEqual(result, [])

    # Test 2: send_tasks_parallel returns list of results in submission order
    def test_send_tasks_parallel_returns_results_in_order(self) -> None:
        broker, _ = self._make_broker()
        self._register_echo_agent(broker, "agent_a", "cap_a")
        self._register_echo_agent(broker, "agent_b", "cap_b")
        msg_a = A2AMessage(
            message_type="task_request", sender_agent="triage",
            target_agent="agent_a", capability="cap_a",
            payload={}, task_id="task-a",
        )
        msg_b = A2AMessage(
            message_type="task_request", sender_agent="triage",
            target_agent="agent_b", capability="cap_b",
            payload={}, task_id="task-b",
        )
        results = broker.send_tasks_parallel([msg_a, msg_b])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].summary, "done-agent_a")
        self.assertEqual(results[1].summary, "done-agent_b")

    # Test 3: trace contains exactly 2 task_submit events with matching task_ids
    def test_send_tasks_parallel_emits_task_submit_events(self) -> None:
        broker, trace = self._make_broker()
        self._register_echo_agent(broker, "agent_a", "cap_a")
        self._register_echo_agent(broker, "agent_b", "cap_b")
        msg_a = A2AMessage(
            message_type="task_request", sender_agent="triage",
            target_agent="agent_a", capability="cap_a",
            payload={}, task_id="task-a",
        )
        msg_b = A2AMessage(
            message_type="task_request", sender_agent="triage",
            target_agent="agent_b", capability="cap_b",
            payload={}, task_id="task-b",
        )
        broker.send_tasks_parallel([msg_a, msg_b])
        submit_events = [e for e in trace.events if e["event_type"] == "task_submit"]
        self.assertEqual(len(submit_events), 2)
        task_ids = {e["task_id"] for e in submit_events}
        self.assertIn("task-a", task_ids)
        self.assertIn("task-b", task_ids)

    # Test 4: both task_submit events share the same parallel_batch_id (12 hex chars)
    def test_send_tasks_parallel_shared_batch_id(self) -> None:
        broker, trace = self._make_broker()
        self._register_echo_agent(broker, "agent_a", "cap_a")
        self._register_echo_agent(broker, "agent_b", "cap_b")
        msg_a = A2AMessage(
            message_type="task_request", sender_agent="triage",
            target_agent="agent_a", capability="cap_a",
            payload={}, task_id="task-a",
        )
        msg_b = A2AMessage(
            message_type="task_request", sender_agent="triage",
            target_agent="agent_b", capability="cap_b",
            payload={}, task_id="task-b",
        )
        broker.send_tasks_parallel([msg_a, msg_b])
        submit_events = [e for e in trace.events if e["event_type"] == "task_submit"]
        batch_ids = {e["parallel_batch_id"] for e in submit_events}
        self.assertEqual(len(batch_ids), 1)
        batch_id = list(batch_ids)[0]
        self.assertIsInstance(batch_id, str)
        self.assertEqual(len(batch_id), 12)

    # Test 5: each task_submit has started_at and completed_at (from task_complete events)
    def test_send_tasks_parallel_timing_fields(self) -> None:
        broker, trace = self._make_broker()
        self._register_echo_agent(broker, "agent_a", "cap_a")
        msg_a = A2AMessage(
            message_type="task_request", sender_agent="triage",
            target_agent="agent_a", capability="cap_a",
            payload={}, task_id="task-a",
        )
        broker.send_tasks_parallel([msg_a])
        submit_events = [e for e in trace.events if e["event_type"] == "task_submit"]
        complete_events = [e for e in trace.events if e["event_type"] == "task_complete"]
        self.assertEqual(len(submit_events), 1)
        self.assertEqual(len(complete_events), 1)
        self.assertIn("started_at", submit_events[0])
        self.assertIn("completed_at", complete_events[0])
        self.assertGreaterEqual(complete_events[0]["completed_at"], submit_events[0]["started_at"])

    # Test 6: task_submit events have step_index injected by enriched record()
    def test_send_tasks_parallel_step_index_on_submit(self) -> None:
        broker, trace = self._make_broker()
        self._register_echo_agent(broker, "agent_a", "cap_a")
        self._register_echo_agent(broker, "agent_b", "cap_b")
        msg_a = A2AMessage(
            message_type="task_request", sender_agent="triage",
            target_agent="agent_a", capability="cap_a",
            payload={}, task_id="task-a",
        )
        msg_b = A2AMessage(
            message_type="task_request", sender_agent="triage",
            target_agent="agent_b", capability="cap_b",
            payload={}, task_id="task-b",
        )
        broker.send_tasks_parallel([msg_a, msg_b])
        submit_events = [e for e in trace.events if e["event_type"] == "task_submit"]
        step_indices = {e["step_index"] for e in submit_events}
        self.assertIn(1, step_indices)
        self.assertIn(2, step_indices)


if __name__ == "__main__":
    unittest.main()





