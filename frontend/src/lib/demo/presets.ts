import type { ApiRunRequest, DemoMode, RuntimeMode, TransportMode } from "../types/api";

export type DemoPreset = {
  id: string;
  title: string;
  description: string;
  scenario: string;
  mode: DemoMode;
  profile: ApiRunRequest["profile"];
  runtime: RuntimeMode;
  mcp_transport: TransportMode;
  failure_toggles: Array<
    | "db_down"
    | "docs_timeout"
    | "malformed_task"
    | "remote_a2a_timeout"
    | "remote_a2a_bad_auth"
    | "remote_a2a_missing_capability"
    | "remote_a2a_malformed_response"
    | "remote_a2a_task_failure"
  >;
};

export const demoPresets: DemoPreset[] = [
  {
    id: "quick_comparison",
    title: "Quick Four-Mode Comparison",
    description: "A short happy-path run for explaining baseline, MCP, A2A, and hybrid differences.",
    scenario: "order_status",
    mode: "all",
    profile: "demo",
    runtime: "mock",
    mcp_transport: "in_process",
    failure_toggles: [],
  },
  {
    id: "mcp_transport_story",
    title: "MCP Transport Boundary",
    description: "A docs-heavy case through the MCP tool boundary.",
    scenario: "setup_error",
    mode: "mcp",
    profile: "demo",
    runtime: "mock",
    mcp_transport: "http",
    failure_toggles: [],
  },
  {
    id: "a2a_delegation_story",
    title: "A2A Specialist Delegation",
    description: "Triage and specialist handoffs without MCP tool usage.",
    scenario: "double_charge",
    mode: "a2a",
    profile: "demo",
    runtime: "mock",
    mcp_transport: "in_process",
    failure_toggles: [],
  },
  {
    id: "hybrid_enterprise_story",
    title: "Hybrid Enterprise Workflow",
    description: "A multi-step enterprise case with A2A delegation and MCP-backed tools.",
    scenario: "enterprise_setup_replacement",
    mode: "hybrid",
    profile: "demo",
    runtime: "mock",
    mcp_transport: "http",
    failure_toggles: [],
  },
  {
    id: "resilience_failure_story",
    title: "Failure and Recovery Narrative",
    description: "A database outage path for showing failure and recovery behavior.",
    scenario: "delay_and_billing",
    mode: "all",
    profile: "demo",
    runtime: "mock",
    mcp_transport: "in_process",
    failure_toggles: ["db_down"],
  },
];

export const guidedStoryModes: DemoMode[] = ["baseline", "mcp", "a2a", "hybrid"];
