import type { TraceEvent } from "../types/api";

export function uniqueTraceValues(events: TraceEvent[], pick: (event: TraceEvent) => string | undefined): string[] {
  return Array.from(new Set(events.map(pick).filter((value): value is string => Boolean(value)))).sort();
}

export function traceLabel(event: TraceEvent): string {
  if (event.message_type) {
    return `${event.event_type}:${event.message_type}`;
  }
  return event.event_type;
}

export function isA2AEvent(event: TraceEvent): boolean {
  return (
    event.event_type === "a2a_message" ||
    event.event_type.startsWith("a2a_remote_") ||
    event.event_type === "a2a_task_artifact"
  );
}

export function isTraceFailureEvent(event: TraceEvent): boolean {
  return Boolean(
    event.error ||
    event.event_type === "tool_error" ||
    event.event_type === "a2a_remote_failure" ||
    event.event_type === "triage_warning" ||
    event.message_type === "task_retry" ||
    event.message_type === "task_error" ||
    event.event_type === "a2a_remote_retry",
  );
}

export function traceEventTone(event: TraceEvent): "error" | "warning" | "success" | "info" {
  if (event.error || event.event_type === "tool_error" || event.event_type === "a2a_remote_failure") {
    return "error";
  }
  if (
    event.event_type === "triage_warning" ||
    event.message_type === "task_retry" ||
    event.message_type === "task_error" ||
    event.event_type === "a2a_remote_retry"
  ) {
    return "warning";
  }
  if (event.status === "completed" || event.message_type === "task_result") {
    return "success";
  }
  return "info";
}

export function traceEventActor(event: TraceEvent): string {
  return String(event.agent ?? event.remote_agent ?? event.sender ?? event.target ?? "system");
}

export function traceEventProtocol(event: TraceEvent): string {
  if (event.protocol) {
    return String(event.protocol);
  }
  if (isA2AEvent(event) || event.message_type) {
    return "a2a";
  }
  if (event.tool || event.server) {
    return "mcp";
  }
  return "runtime";
}

export function traceEventSummary(event: TraceEvent): string {
  if (event.error) {
    return String(event.error);
  }
  if (event.tool) {
    return `${event.tool}${event.server ? ` via ${event.server}` : ""}`;
  }
  if (event.status) {
    return `Status changed to ${event.status}`;
  }
  if (event.message_type && event.target) {
    return `${event.message_type} -> ${event.target}`;
  }
  if (event.message_type && event.sender) {
    return `${event.message_type} from ${event.sender}`;
  }
  return traceLabel(event);
}

/**
 * Groups A2A-related events by their task_id for the Protocol Tier accordion.
 * Groups include: a2a_message, a2a_task_artifact, task_status events that carry a task_id.
 * Events without task_id are grouped under "unknown".
 */
export function groupA2AEventsByTaskId(events: TraceEvent[]): Map<string, TraceEvent[]> {
  const groups = new Map<string, TraceEvent[]>();
  for (const event of events) {
    const isGroupable =
      isA2AEvent(event) ||
      event.event_type === "task_status" ||
      event.event_type === "task_submit" ||
      event.event_type === "task_complete";
    if (!isGroupable) continue;
    const taskId = String(
      (event as { task_id?: unknown }).task_id ??
      (event.a2a_task as { id?: unknown } | undefined)?.id ??
      "unknown"
    );
    if (!groups.has(taskId)) groups.set(taskId, []);
    groups.get(taskId)!.push(event);
  }
  return groups;
}
