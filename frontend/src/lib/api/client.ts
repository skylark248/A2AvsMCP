import type {
  ApiRunRequest,
  RemoteMCPRegistryResponse,
  RemoteA2ARegistryResponse,
  RemoteA2AHealthResponse,
  ReportDetailResponse,
  ReportsResponse,
  RunResponse,
  ScenarioOption,
  TelemetrySnapshot,
  TrendsResponse,
} from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

function stringifyApiDetail(detail: unknown): string | null {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }
        return JSON.stringify(item);
      })
      .filter(Boolean)
      .join(" ");
  }
  if (detail && typeof detail === "object") {
    return JSON.stringify(detail);
  }
  return null;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    const body = await response.text();
    if (body) {
      try {
        const parsed = JSON.parse(body) as { detail?: unknown; message?: unknown };
        message = stringifyApiDetail(parsed.detail ?? parsed.message) ?? message;
      } catch {
        message = body.slice(0, 500);
      }
    }
    throw new Error(message);
  }

  return (await response.json()) as T;
}

export async function fetchScenarios(): Promise<ScenarioOption[]> {
  const payload = await requestJson<{ scenarios: ScenarioOption[] }>("/api/scenarios");
  return payload.scenarios;
}

export async function runDemo(payload: ApiRunRequest): Promise<RunResponse> {
  return requestJson<RunResponse>("/api/run", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchReports(): Promise<ReportsResponse> {
  return requestJson<ReportsResponse>("/api/reports");
}

export async function fetchReportDetail(reportName: string): Promise<ReportDetailResponse> {
  return requestJson<ReportDetailResponse>(`/api/reports/${encodeURIComponent(reportName)}`);
}

export async function fetchTrends(filters?: {
  scenario?: string;
  runtime?: string;
  recommended_mode?: string;
  mode_sort?: string;
  mode_dir?: string;
  report_sort?: string;
  report_dir?: string;
  scenario_sort?: string;
  scenario_dir?: string;
}): Promise<TrendsResponse> {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        params.set(key, value);
      }
    });
  }
  const query = params.toString();
  return requestJson<TrendsResponse>(`/api/reports/trends${query ? `?${query}` : ""}`);
}

export async function fetchTelemetry(allUsers = false): Promise<TelemetrySnapshot> {
  return requestJson<TelemetrySnapshot>(`/api/telemetry${allUsers ? "?all_users=true" : ""}`);
}

export async function fetchRemoteMcpRegistry(): Promise<RemoteMCPRegistryResponse> {
  return requestJson<RemoteMCPRegistryResponse>("/api/mcp/registry");
}
export async function fetchRemoteA2aRegistry(): Promise<RemoteA2ARegistryResponse> {
  return requestJson<RemoteA2ARegistryResponse>("/api/a2a/registry");
}

export async function fetchRemoteA2aHealth(urls?: {
  customer_url?: string;
  documentation_url?: string;
  policy_url?: string;
}): Promise<RemoteA2AHealthResponse> {
  const params = new URLSearchParams();
  if (urls?.customer_url) params.set("customer_url", urls.customer_url);
  if (urls?.documentation_url) params.set("documentation_url", urls.documentation_url);
  if (urls?.policy_url) params.set("policy_url", urls.policy_url);
  const query = params.toString();
  return requestJson<RemoteA2AHealthResponse>(`/api/a2a/health${query ? `?${query}` : ""}`);
}
