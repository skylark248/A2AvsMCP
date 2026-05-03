from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import html as _html_mod
import ipaddress
from io import BytesIO
import json
import os
import time as _ws_time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse
import uuid
import zipfile

from fastapi import FastAPI, Form, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, field_validator

from .api_schemas import (
    ApiRunRequest,
    HealthResponse,
    ProfileName,
    RemoteMCPRegistryResponse,
    RemoteA2ARegistryResponse,
    RemoteA2AHealthResponse,
    ReportDetailResponse,
    ReportsResponse,
    RunResponse,
    RuntimeMode,
    ScenariosResponse,
    TelemetrySnapshotResponse,
    TransportMode,
    TrendsResponse,
)
from .config import PROFILES, default_profile_name, resolve_profile
from .identity import base_artifact_root, normalize_user_id
from .platform import DemoPlatform
from .persistence import PlatformStore
from .remote_registry import RemoteMCPRegistry
from .a2a.registry import RemoteA2ARegistry
from .race.config import OG_LAYOUT_VERSION  # noqa: F401
from .race.heatmap import get_heatmap
from .race.og import (
    OG_DIR,
    OG_RENDER_LOCK,
    cleanup_stale,
    og_cache_path,
    og_lifespan,
    render_heatmap_png,
    render_og_png,
)
from .race.harness import run_race
from .race.replay import load_run, _validate_run_id
from .race.runs import RUNS_DIR
from .race.tasks import TASK_CONFIGS
from .race.types import HardnessProfile, HardnessType, TaskSpec
from .race.ws import MANAGER, HEARTBEAT_S
from .trace import TraceRecorder
from .reporting import ReportService
from .schemas import FailureConfig


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
REPORTS = ReportService(PROJECT_ROOT)
STORE = PlatformStore(PROJECT_ROOT)
REMOTE_REGISTRY = RemoteMCPRegistry(PROJECT_ROOT, STORE)
REMOTE_A2A_REGISTRY = RemoteA2ARegistry(PROJECT_ROOT)
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"
FRONTEND_ASSETS = FRONTEND_DIST / "assets"

app = FastAPI(title="A2A vs MCP Demo UI", lifespan=og_lifespan)
app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static")
if FRONTEND_ASSETS.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_ASSETS)), name="frontend-assets")

DEFAULT_TREND_SORTING = {
    "mode_sort": "overall",
    "mode_dir": "desc",
    "scenario_sort": "count",
    "scenario_dir": "desc",
    "report_sort": "recent",
    "report_dir": "desc",
}
DEFAULT_REPORT_SORTING = {
    "score_sort": "overall",
    "score_dir": "desc",
    "result_sort": "latency",
    "result_dir": "asc",
}

LOCAL_REMOTE_HOSTS = {"localhost", "host.docker.internal"}

_VALID_LANES: frozenset[str] = frozenset({"pure_mcp", "pure_a2a", "hybrid"})


class RaceRunRequest(BaseModel):
    task_ids: list[str]
    lanes: list[str] = ["pure_mcp", "pure_a2a", "hybrid"]
    n: int = 1

    @field_validator("lanes")
    @classmethod
    def validate_lanes(cls, v: list[str]) -> list[str]:
        bad = [ln for ln in v if ln not in _VALID_LANES]
        if bad:
            raise ValueError(f"unknown lanes: {bad!r}")
        return v

    @field_validator("task_ids")
    @classmethod
    def validate_task_ids(cls, v: list[str]) -> list[str]:
        bad = [t for t in v if t not in TASK_CONFIGS]
        if bad:
            raise ValueError(f"unknown task_ids: {bad!r}")
        return v

    @field_validator("n")
    @classmethod
    def validate_n(cls, v: int) -> int:
        if v < 1:
            raise ValueError("n must be >= 1")
        return v





def app_version() -> str:
    try:
        return version("a2a-vs-mcp-demo")
    except PackageNotFoundError:
        return "0.4.0"



def request_user_id(request: Request | None = None, explicit: str | None = None) -> str:
    if explicit:
        return normalize_user_id(explicit)
    if request is not None:
        return normalize_user_id(request.headers.get("X-Demo-User") or request.query_params.get("user_id"))
    return normalize_user_id(None)


def report_service(user_id: str | None = None) -> ReportService:
    return ReportService(PROJECT_ROOT, user_id=user_id)
def load_report_or_404(report_name: str, user_id: str | None = None) -> list[dict[str, Any]]:
    try:
        return report_service(user_id).load_report(report_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Report not found: {report_name}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def safe_arcname(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def collect_existing_file(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if path.exists() and path.is_file():
        return path
    return None


def external_remote_urls_allowed() -> bool:
    value = os.getenv("A2A_VS_MCP_ALLOW_EXTERNAL_REMOTE_URLS", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def is_local_remote_host(hostname: str) -> bool:
    normalized = hostname.strip().lower().rstrip(".")
    if normalized in LOCAL_REMOTE_HOSTS:
        return True
    try:
        address = ipaddress.ip_address(normalized)
        return address.is_loopback or address.is_private or address.is_link_local
    except ValueError:
        # Single-label hostnames support Docker Compose service discovery while
        # still rejecting arbitrary external FQDNs by default.
        return "." not in normalized


def validate_remote_url(url: str | None, field_name: str) -> str:
    value = (url or "").strip()
    if not value:
        return ""
    if len(value) > 2048:
        raise HTTPException(status_code=400, detail=f"{field_name} is too long.")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=400, detail=f"{field_name} must be an http(s) URL with a hostname.")
    if parsed.username or parsed.password:
        raise HTTPException(status_code=400, detail=f"{field_name} must not include embedded credentials.")
    if not external_remote_urls_allowed() and not is_local_remote_host(parsed.hostname):
        raise HTTPException(
            status_code=400,
            detail=(
                f"{field_name} points to an external host. Set "
                "A2A_VS_MCP_ALLOW_EXTERNAL_REMOTE_URLS=true only for trusted demo deployments."
            ),
        )
    return value.rstrip("/")


def build_evidence_bundle(report_name: str, payload: list[dict[str, Any]], service: ReportService | None = None) -> bytes:
    active_service = service or REPORTS
    summary = active_service.summarize(report_name, payload).to_dict()
    first = payload[0] if payload else {}
    ticket = first.get("ticket", {})
    manifest = {
        "bundle_type": "a2a_vs_mcp_evidence_bundle",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_name": report_name,
        "scenario": ticket.get("scenario", ""),
        "ticket_id": ticket.get("ticket_id", ""),
        "runtime": first.get("runtime", ""),
        "modes": [item.get("mode", "") for item in payload],
        "files": [],
    }

    report_path = active_service.resolve_report_path(report_name)
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(report_path, safe_arcname(report_path))
        manifest["files"].append(safe_arcname(report_path))

        archive.writestr("evidence/summary.json", json.dumps(summary, indent=2).encode("utf-8"))
        manifest["files"].append("evidence/summary.json")

        archive.writestr("evidence/scenario.json", json.dumps(ticket, indent=2).encode("utf-8"))
        manifest["files"].append("evidence/scenario.json")

        for item in payload:
            mode = item.get("mode", "unknown")
            trace_name = f"evidence/traces/{mode}.json"
            archive.writestr(trace_name, json.dumps(item.get("trace", []), indent=2).encode("utf-8"))
            manifest["files"].append(trace_name)

            log_path = collect_existing_file(item.get("external_log_path"))
            if log_path is not None:
                arcname = safe_arcname(log_path)
                archive.write(log_path, arcname)
                manifest["files"].append(arcname)

            trace_file = None
            for event in item.get("trace", []):
                if event.get("event_type") == "comparison_report":
                    trace_file = collect_existing_file(event.get("trace_file"))
                    break
            if trace_file is not None:
                arcname = safe_arcname(trace_file)
                if arcname not in manifest["files"]:
                    archive.write(trace_file, arcname)
                    manifest["files"].append(arcname)

        archive.writestr("manifest.json", json.dumps(manifest, indent=2).encode("utf-8"))
    return buffer.getvalue()

def build_platform(runtime: str | None, mcp_transport: str | None = None, a2a_transport: str | None = None, profile_name: str | None = None, export_logs: bool | None = None, remote_mcp_urls: dict[str, str] | None = None, remote_a2a_urls: dict[str, str] | None = None, remote_a2a_auth_token: str | None = None, user_id: str | None = None) -> DemoPlatform:
    return DemoPlatform(PROJECT_ROOT, runtime=runtime, mcp_transport=mcp_transport, a2a_transport=a2a_transport, profile_name=profile_name, export_logs=export_logs, remote_mcp_urls=remote_mcp_urls, remote_a2a_urls=remote_a2a_urls, remote_a2a_auth_token=remote_a2a_auth_token, user_id=user_id)


def scenario_options(platform: DemoPlatform) -> list[dict[str, Any]]:
    return [
        {
            "key": key,
            "label": ticket.title or key.replace("_", " ").title(),
            "query": ticket.query,
            "difficulty": ticket.difficulty,
            "tags": ticket.tags,
        }
        for key, ticket in platform.scenarios.items()
    ]


def normalize_results(raw_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "mode": report["mode"],
            "runtime": report.get("runtime", "mock"),
            "ticket": report["ticket"],
            "final_answer": report["final_answer"],
            "metrics": report["metrics"],
            "tools_used": report["tools_used"],
            "agents_used": report["agents_used"],
            "failures": report.get("failures", []),
            "trace": report["trace"],
            "external_log_path": report.get("external_log_path"),
            "a2a_transport": report.get("a2a_transport", "local"),
            "mcp_transport": report.get("mcp_transport"),
        }
        for report in raw_reports
    ]


def sort_results(results: list[dict[str, Any]], sort_by: str, direction: str) -> list[dict[str, Any]]:
    sorters = {
        "mode": lambda item: item["mode"],
        "latency": lambda item: float(item["metrics"]["latency_ms"]),
        "tools": lambda item: int(item["metrics"]["tool_calls"]),
        "a2a": lambda item: int(item["metrics"]["a2a_messages"]),
        "retries": lambda item: int(item["metrics"]["retries"]),
        "failures": lambda item: int(item["metrics"]["failures"]),
    }
    key = sorters.get(sort_by, sorters["latency"])
    reverse = direction == "desc"
    return sorted(results, key=key, reverse=reverse)


def sort_scorecards(cards: list[dict[str, Any]], sort_by: str, direction: str) -> list[dict[str, Any]]:
    sorters = {
        "mode": lambda item: item["mode"],
        "overall": lambda item: int(item["overall_score"]),
        "responsive": lambda item: int(item["responsiveness_score"]),
        "tooling": lambda item: int(item["tooling_score"]),
        "collaboration": lambda item: int(item["collaboration_score"]),
        "resilience": lambda item: int(item["resilience_score"]),
        "presentation": lambda item: int(item["presentation_score"]),
    }
    key = sorters.get(sort_by, sorters["overall"])
    reverse = direction == "desc"
    return sorted(cards, key=key, reverse=reverse)


def build_context(
    request: Request,
    *,
    results: list[dict[str, Any]] | None = None,
    selected: dict[str, Any] | None = None,
    loaded_report: str | None = None,
    trend_view: bool = False,
    trend_filters: dict[str, str] | None = None,
    trend_sorting: dict[str, str] | None = None,
    report_sorting: dict[str, str] | None = None,
) -> dict[str, Any]:
    selected_profile = (selected or {}).get("profile", "dev")
    profile = resolve_profile(
        selected_profile,
        runtime=(selected or {}).get("runtime"),
        mcp_transport=(selected or {}).get("mcp_transport"),
        a2a_transport=(selected or {}).get("a2a_transport"),
        save_report=(selected or {}).get("save_report"),
        export_logs=(selected or {}).get("export_logs"),
    )
    platform = build_platform(runtime=profile.runtime, mcp_transport=profile.mcp_transport, a2a_transport=profile.a2a_transport, profile_name=profile.name, export_logs=profile.export_logs)
    trend_filters = trend_filters or {"scenario": "", "runtime": "", "recommended_mode": ""}
    trend_sorting = {**DEFAULT_TREND_SORTING, **(trend_sorting or {})}
    report_sorting = {**DEFAULT_REPORT_SORTING, **(report_sorting or {})}

    normalized_results = results or []
    report_summary = None
    if normalized_results:
        normalized_results = sort_results(normalized_results, report_sorting["result_sort"], report_sorting["result_dir"])
        report_summary = REPORTS.summarize(loaded_report or "unsaved", normalized_results).to_dict()
        scorecard = report_summary.get("scorecard")
        if scorecard is not None:
            scorecard["mode_scorecards"] = sort_scorecards(scorecard.get("mode_scorecards", []), report_sorting["score_sort"], report_sorting["score_dir"])

    report_trends = REPORTS.build_trend_view(
        scenario=trend_filters.get("scenario") or None,
        runtime=trend_filters.get("runtime") or None,
        recommended_mode=trend_filters.get("recommended_mode") or None,
        mode_sort=trend_sorting["mode_sort"],
        mode_dir=trend_sorting["mode_dir"],
        scenario_sort=trend_sorting["scenario_sort"],
        scenario_dir=trend_sorting["scenario_dir"],
        report_sort=trend_sorting["report_sort"],
        report_dir=trend_sorting["report_dir"],
    )
    return {
        "request": request,
        "results": normalized_results,
        "report_summary": report_summary,
        "report_trends": report_trends,
        "scenario_options": scenario_options(platform),
        "profile_options": [item.to_dict() for item in PROFILES.values()],
        "effective_profile": profile.to_dict(),
        "mode_options": ["baseline", "mcp", "a2a", "hybrid", "all"],
        "runtime_options": ["mock", "llm"],
        "transport_options": ["in_process", "stdio", "http", "remote_http"],
        "a2a_transport_options": ["local", "remote"],
        "agent_options": ["customer_data_agent", "documentation_agent", "policy_or_billing_agent"],
        "saved_reports": REPORTS.list_reports(),
        "selected": selected or {
            "profile": profile.name,
            "scenario": "order_status",
            "mode": "all",
            "runtime": None,
            "customer_id": "",
            "query": "",
            "db_down": False,
            "docs_timeout": False,
            "malformed_task": False,
            "disable_agent": [],
            "mcp_transport": None,
            "a2a_transport": None,
            "save_report": profile.save_report,
            "export_logs": profile.export_logs,
        },
        "loaded_report": loaded_report,
        "trend_view": trend_view,
        "trend_filters": trend_filters,
        "trend_sorting": trend_sorting,
        "report_sorting": report_sorting,
    }


def execute_run(payload: ApiRunRequest, user_id: str | None = None) -> tuple[list[dict[str, Any]], str | None]:
    profile = resolve_profile(payload.profile, runtime=payload.runtime, mcp_transport=payload.mcp_transport, a2a_transport=payload.a2a_transport, save_report=payload.save_report, export_logs=payload.export_logs)
    active_user_id = normalize_user_id(user_id or payload.user_id)
    if payload.remote_mcp_registry_id:
        try:
            remote_mcp_urls = REMOTE_REGISTRY.discover(payload.remote_mcp_registry_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Remote MCP registry entry not found: {payload.remote_mcp_registry_id}") from exc
    else:
        remote_mcp_urls = {"db": payload.remote_mcp_db_url or "", "docs": payload.remote_mcp_docs_url or ""}
    remote_mcp_urls = {
        "db": validate_remote_url(remote_mcp_urls.get("db"), "remote_mcp_db_url"),
        "docs": validate_remote_url(remote_mcp_urls.get("docs"), "remote_mcp_docs_url"),
    }
    remote_a2a_urls = {
        "customer_data": validate_remote_url(payload.remote_a2a_customer_url, "remote_a2a_customer_url"),
        "documentation": validate_remote_url(payload.remote_a2a_documentation_url, "remote_a2a_documentation_url"),
        "policy_billing": validate_remote_url(payload.remote_a2a_policy_url, "remote_a2a_policy_url"),
    }
    if not any(remote_a2a_urls.values()):
        remote_a2a_urls = None
    platform = build_platform(runtime=profile.runtime, mcp_transport=profile.mcp_transport, a2a_transport=profile.a2a_transport, profile_name=profile.name, export_logs=profile.export_logs, remote_mcp_urls=remote_mcp_urls, remote_a2a_urls=remote_a2a_urls, remote_a2a_auth_token=payload.remote_a2a_auth_token, user_id=active_user_id)
    scenario_key = None if payload.query.strip() else payload.scenario
    if scenario_key and scenario_key not in platform.scenarios:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_key}")
    ticket = platform.get_ticket(scenario_key, payload.query.strip() or None, payload.customer_id.strip() or None)
    failure_config = FailureConfig(
        db_down=payload.db_down,
        docs_timeout=payload.docs_timeout,
        malformed_task=payload.malformed_task,
        remote_a2a_timeout=payload.remote_a2a_timeout,
        remote_a2a_bad_auth=payload.remote_a2a_bad_auth,
        remote_a2a_missing_capability=payload.remote_a2a_missing_capability,
        remote_a2a_malformed_response=payload.remote_a2a_malformed_response,
        remote_a2a_task_failure=payload.remote_a2a_task_failure,
        unavailable_agents=payload.disable_agent,
    )
    modes = ["baseline", "mcp", "a2a", "hybrid"] if payload.mode == "all" else [payload.mode]
    raw_reports = []
    for current_mode in modes:
        output = platform.run(current_mode, ticket, failure_config=failure_config)
        result = output.to_dict()
        raw_reports.append(result)
        STORE.record_run_event(user_id=active_user_id, event_type="run_completed", mode=current_mode, scenario=ticket.scenario, runtime=profile.runtime, metrics=result.get("metrics", {}), metadata={"report_saved": bool(profile.save_report), "transport": profile.mcp_transport, "a2a_transport": profile.a2a_transport})
    report_name = None
    if profile.save_report:
        service = report_service(active_user_id)
        report_path = service.save_report(ticket, raw_reports)
        report_name = report_path.name
        summary = service.summarize(report_name, raw_reports).to_dict()
        STORE.record_report(user_id=active_user_id, report_name=report_name, report_path=report_path, summary=summary, modes=[item.get("mode", "unknown") for item in raw_reports])
    return raw_reports, report_name


def render_react_app() -> Response:
    if FRONTEND_INDEX.exists():
        return FileResponse(FRONTEND_INDEX)
    return HTMLResponse(
        "React frontend build not found. Run `npm.cmd run build` from the frontend directory, or use the Vite dev server.",
        status_code=503,
    )


@app.get("/", response_class=HTMLResponse)
def index() -> Response:
    return render_react_app()


@app.get("/learn", response_class=HTMLResponse)
def react_learn() -> Response:
    return render_react_app()


@app.get("/reports", response_class=HTMLResponse)
def react_reports() -> Response:
    return render_react_app()


@app.get("/traces", response_class=HTMLResponse)
def react_traces() -> Response:
    return render_react_app()


@app.get("/presentation", response_class=HTMLResponse)
def react_presentation() -> Response:
    return render_react_app()


@app.get("/reports/{report_name}", response_class=HTMLResponse)
def react_report_detail(report_name: str) -> Response:
    return render_react_app()


@app.get("/trends", response_class=HTMLResponse)
def react_trends() -> Response:
    return render_react_app()


# Phase 10 — OG image + sharing routes (D-61, D-62, D-63, D-66; OG-01..OG-04)
_INDEX_HTML_CACHE: str | None = None


def _read_index_html() -> str:
    """Read frontend/dist/index.html once and cache the bytes string (Risk-9: dev workflow restarts uvicorn after `npm run build`)."""
    global _INDEX_HTML_CACHE
    if _INDEX_HTML_CACHE is None:
        _INDEX_HTML_CACHE = FRONTEND_INDEX.read_text(encoding="utf-8")
    return _INDEX_HTML_CACHE


def _inject_og_meta(html_doc: str, run_id: str, base_url: str) -> str:
    """Insert og:* + twitter:* meta tags immediately before </head> (OG-01).

    All attribute values pass through html.escape(quote=True) to defend against
    attribute-injection attempts in run_id (T-10-02-04).
    """
    title = f"Three-Lane Race · {run_id}"
    description = (
        "How three protocol lanes recover (or don't) from injected faults — A2A vs MCP."
    )
    run_id_esc = _html_mod.escape(run_id, quote=True)
    image_url = f"{base_url}/race/{run_id_esc}/og.png"
    page_url = f"{base_url}/race/{run_id_esc}"
    title_esc = _html_mod.escape(title, quote=True)
    desc_esc = _html_mod.escape(description, quote=True)
    tags = (
        f'<meta property="og:type" content="article">'
        f'<meta property="og:url" content="{page_url}">'
        f'<meta property="og:title" content="{title_esc}">'
        f'<meta property="og:description" content="{desc_esc}">'
        f'<meta property="og:image" content="{image_url}">'
        f'<meta property="og:image:width" content="1200">'
        f'<meta property="og:image:height" content="630">'
        f'<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:title" content="{title_esc}">'
        f'<meta name="twitter:description" content="{desc_esc}">'
        f'<meta name="twitter:image" content="{image_url}">'
    )
    return html_doc.replace("</head>", tags + "</head>", 1)


@app.get("/race", response_class=HTMLResponse)
def race_html() -> HTMLResponse:
    """SPA mount for /race (no run_id) — Risk 7 mitigation: explicit, not catch-all."""
    return HTMLResponse(_read_index_html())


@app.get("/race/{run_id}", response_class=HTMLResponse)
def race_run_html(run_id: str, request: Request) -> HTMLResponse:
    """OG-01: inject og:image + twitter:image meta tags for known run_id; crawler-safe omission for unknown."""
    try:
        _validate_run_id(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid run_id") from exc
    base_url = str(request.base_url).rstrip("/")
    if (RUNS_DIR / f"{run_id}.json").exists():
        html_out = _inject_og_meta(_read_index_html(), run_id, base_url)
    else:
        html_out = _read_index_html()
    return HTMLResponse(html_out)


@app.get("/race/{run_id}/og.png")
async def race_og_png(run_id: str, request: Request) -> Response:
    """OG-04: 404 BEFORE Playwright spawn; D-66 cache pattern; D-61 single-flight; D-62 503 on render failure (no cache write)."""
    try:
        _validate_run_id(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid run_id") from exc
    if not (RUNS_DIR / f"{run_id}.json").exists():
        raise HTTPException(status_code=404, detail="run not found")
    cleanup_stale(run_id, "og")
    cache = og_cache_path(run_id, "og")
    if cache.exists():
        return FileResponse(cache, media_type="image/png")
    async with OG_RENDER_LOCK:
        if cache.exists():
            return FileResponse(cache, media_type="image/png")
        try:
            data = await render_og_png(run_id, request.app.state.og_browser)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=503, detail="og render failed; please retry"
            ) from exc
        OG_DIR.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(data)
        return Response(content=data, media_type="image/png")


@app.get("/race/{run_id}/heatmap.png")
async def race_heatmap_png(run_id: str, request: Request) -> Response:
    """OG-02: heatmap.png surface mirrors og.png shape (single-flight cache + 503 on failure)."""
    try:
        _validate_run_id(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid run_id") from exc
    if not (RUNS_DIR / f"{run_id}.json").exists():
        raise HTTPException(status_code=404, detail="run not found")
    cleanup_stale(run_id, "heatmap")
    cache = og_cache_path(run_id, "heatmap")
    if cache.exists():
        return FileResponse(cache, media_type="image/png")
    async with OG_RENDER_LOCK:
        if cache.exists():
            return FileResponse(cache, media_type="image/png")
        try:
            data = await render_heatmap_png(run_id, request.app.state.og_browser)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=503, detail="heatmap render failed; please retry"
            ) from exc
        OG_DIR.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(data)
        return Response(content=data, media_type="image/png")


@app.get("/legacy", response_class=HTMLResponse)
def legacy_index(request: Request) -> HTMLResponse:
    context = build_context(request)
    return TEMPLATES.TemplateResponse(request, "index.html", context)


@app.get("/legacy/trends", response_class=HTMLResponse)
def load_trends(
    request: Request,
    scenario: str = "",
    runtime: str = "",
    recommended_mode: str = "",
    mode_sort: str = "overall",
    mode_dir: str = "desc",
    scenario_sort: str = "count",
    scenario_dir: str = "desc",
    report_sort: str = "recent",
    report_dir: str = "desc",
) -> HTMLResponse:
    context = build_context(
        request,
        trend_view=True,
        trend_filters={"scenario": scenario, "runtime": runtime, "recommended_mode": recommended_mode},
        trend_sorting={
            "mode_sort": mode_sort,
            "mode_dir": mode_dir,
            "scenario_sort": scenario_sort,
            "scenario_dir": scenario_dir,
            "report_sort": report_sort,
            "report_dir": report_dir,
        },
    )
    return TEMPLATES.TemplateResponse(request, "_results.html", context)




@app.get("/legacy/controls", response_class=HTMLResponse)
def refresh_controls(
    request: Request,
    profile: str = "dev",
    scenario: str = "order_status",
    mode: str = "all",
    runtime: str = "",
    mcp_transport: str = "",
    query: str = "",
    customer_id: str = "",
    save_report: str | None = None,
    export_logs: str | None = None,
    db_down: str | None = None,
    docs_timeout: str | None = None,
    malformed_task: str | None = None,
    disable_agent: list[str] | None = None,
) -> HTMLResponse:
    resolved = resolve_profile(
        profile,
        runtime=runtime or None,
        mcp_transport=mcp_transport or None,
        save_report=True if save_report is not None else None,
        export_logs=True if export_logs is not None else None,
    )
    context = build_context(
        request,
        selected={
            "profile": profile,
            "scenario": scenario,
            "mode": mode,
            "runtime": runtime or None,
            "mcp_transport": mcp_transport or None,
            "customer_id": customer_id,
            "query": query,
            "db_down": db_down is not None,
            "docs_timeout": docs_timeout is not None,
            "malformed_task": malformed_task is not None,
            "disable_agent": disable_agent or [],
            "save_report": resolved.save_report,
            "export_logs": resolved.export_logs,
        },
    )
    return TEMPLATES.TemplateResponse(request, "_control_panel.html", context)

@app.post("/legacy/run", response_class=HTMLResponse)
def run_demo(
    request: Request,
    profile: str = Form("dev"),
    scenario: str = Form("order_status"),
    mode: str = Form("all"),
    runtime: str = Form(""),
    mcp_transport: str = Form(""),
    query: str = Form(""),
    customer_id: str = Form(""),
    save_report: str | None = Form(None),
    export_logs: str | None = Form(None),
    db_down: str | None = Form(None),
    docs_timeout: str | None = Form(None),
    malformed_task: str | None = Form(None),
    disable_agent: list[str] | None = Form(None),
) -> HTMLResponse:
    resolved = resolve_profile(
        profile,
        runtime=runtime or None,
        mcp_transport=mcp_transport or None,
        save_report=True if save_report is not None else None,
        export_logs=True if export_logs is not None else None,
    )
    raw_reports, report_name = execute_run(
        ApiRunRequest(
            profile=profile,
            scenario=scenario,
            mode=mode,
            runtime=runtime or None,
            mcp_transport=mcp_transport or None,
            query=query,
            customer_id=customer_id,
            save_report=True if save_report is not None else None,
            export_logs=True if export_logs is not None else None,
            db_down=db_down is not None,
            docs_timeout=docs_timeout is not None,
            malformed_task=malformed_task is not None,
            disable_agent=disable_agent or [],
        )
    )
    context = build_context(
        request,
        results=normalize_results(raw_reports),
        selected={
            "profile": profile,
            "scenario": scenario,
            "mode": mode,
            "runtime": runtime or None,
            "mcp_transport": mcp_transport or None,
            "customer_id": customer_id,
            "query": query,
            "db_down": db_down is not None,
            "docs_timeout": docs_timeout is not None,
            "malformed_task": malformed_task is not None,
            "disable_agent": disable_agent or [],
            "save_report": resolved.save_report,
            "export_logs": resolved.export_logs,
        },
        loaded_report=report_name,
    )
    return TEMPLATES.TemplateResponse(request, "_results.html", context)


@app.get("/legacy/reports/{report_name}", response_class=HTMLResponse)
def load_report(
    report_name: str,
    request: Request,
    score_sort: str = "overall",
    score_dir: str = "desc",
    result_sort: str = "latency",
    result_dir: str = "asc",
) -> HTMLResponse:
    payload = load_report_or_404(report_name)
    first = payload[0] if payload else {"ticket": {"scenario": "custom"}}
    context = build_context(
        request,
        results=normalize_results(payload),
        selected={
            "profile": "dev",
            "scenario": first["ticket"].get("scenario", "custom"),
            "mode": "all" if len(payload) > 1 else first.get("mode", "baseline"),
            "runtime": first.get("runtime", "mock"),
            "customer_id": first["ticket"].get("customer_id", ""),
            "query": first["ticket"].get("query", ""),
            "db_down": False,
            "docs_timeout": False,
            "malformed_task": False,
            "disable_agent": [],
            "mcp_transport": first.get("trace", [{}])[0].get("mcp_transport"),
            "save_report": True,
            "export_logs": bool(first.get("external_log_path")),
        },
        loaded_report=report_name,
        report_sorting={
            "score_sort": score_sort,
            "score_dir": score_dir,
            "result_sort": result_sort,
            "result_dir": result_dir,
        },
    )
    return TEMPLATES.TemplateResponse(request, "_results.html", context)


@app.get("/reports/{report_name}/export", response_class=HTMLResponse)
def export_report_html(report_name: str, request: Request) -> HTMLResponse:
    user_id = request_user_id(request)
    service = report_service(user_id)
    payload = load_report_or_404(report_name, user_id)
    return HTMLResponse(service.export_html(report_name, payload))


@app.get("/reports/{report_name}/export.pdf")
def export_report_pdf(report_name: str, request: Request) -> Response:
    user_id = request_user_id(request)
    service = report_service(user_id)
    payload = load_report_or_404(report_name, user_id)
    pdf_bytes = service.export_pdf_bytes(report_name, payload)
    headers = {"Content-Disposition": f'inline; filename="{report_name.replace(".json", ".pdf")}"'}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@app.get("/reports/{report_name}/evidence.zip")
def export_evidence_bundle(report_name: str, request: Request) -> Response:
    user_id = request_user_id(request)
    service = report_service(user_id)
    payload = load_report_or_404(report_name, user_id)
    bundle_bytes = build_evidence_bundle(report_name, payload, service)
    filename = f"{Path(report_name).stem}_evidence_bundle.zip"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=bundle_bytes, media_type="application/zip", headers=headers)

@app.get("/api/health", response_model=HealthResponse)
def api_health() -> HealthResponse:
    platform = build_platform(runtime=None, profile_name=default_profile_name())
    return HealthResponse(
        status="ok",
        version=app_version(),
        default_profile=platform.profile.name,
        profiles=sorted(PROFILES.keys()),
        frontend_build_present=FRONTEND_INDEX.exists(),
        frontend_index=str(FRONTEND_INDEX),
        artifacts_dir=str(base_artifact_root(PROJECT_ROOT)),
        reports_dir=str(REPORTS.report_dir),
        scenarios=len(platform.scenarios),
        mcp_transport_default=platform.mcp_transport,
        a2a_transport_default=platform.a2a_transport,
        artifact_isolation_enabled=True,
        telemetry_db=str(STORE.db_path),
    )

@app.get("/api/scenarios", response_model=ScenariosResponse)
def api_scenarios(runtime: RuntimeMode | None = None, mcp_transport: TransportMode | None = None, profile: ProfileName = "dev") -> ScenariosResponse:
    resolved = resolve_profile(profile, runtime=runtime, mcp_transport=mcp_transport)
    platform = build_platform(runtime=resolved.runtime, mcp_transport=resolved.mcp_transport, a2a_transport=resolved.a2a_transport, profile_name=resolved.name, export_logs=resolved.export_logs)
    return ScenariosResponse(scenarios=scenario_options(platform))


@app.post("/api/run", response_model=RunResponse)
def api_run(payload: ApiRunRequest, request: Request) -> RunResponse:
    user_id = request_user_id(request, payload.user_id)
    raw_reports, report_name = execute_run(payload, user_id=user_id)
    summary = report_service(user_id).summarize(report_name or "unsaved", raw_reports)
    return RunResponse(results=normalize_results(raw_reports), report_name=report_name, summary=summary.to_dict())


@app.get("/api/reports", response_model=ReportsResponse)
def api_reports(request: Request) -> ReportsResponse:
    service = report_service(request_user_id(request))
    reports = []
    for entry in service.list_reports():
        payload = service.load_report(entry["name"])
        reports.append(service.summarize(entry["name"], payload).to_dict())
    return ReportsResponse(reports=reports)


@app.get("/api/reports/trends", response_model=TrendsResponse)
def api_report_trends(
    request: Request,
    scenario: str = "",
    runtime: str = "",
    recommended_mode: str = "",
    mode_sort: str = "overall",
    mode_dir: str = "desc",
    scenario_sort: str = "count",
    scenario_dir: str = "desc",
    report_sort: str = "recent",
    report_dir: str = "desc",
) -> TrendsResponse:
    service = report_service(request_user_id(request))
    return TrendsResponse(
        trends=service.build_trend_view(
            scenario=scenario or None,
            runtime=runtime or None,
            recommended_mode=recommended_mode or None,
            mode_sort=mode_sort,
            mode_dir=mode_dir,
            scenario_sort=scenario_sort,
            scenario_dir=scenario_dir,
            report_sort=report_sort,
            report_dir=report_dir,
        )
    )


@app.get("/api/reports/{report_name}", response_model=ReportDetailResponse)
def api_report(
    report_name: str,
    request: Request,
    score_sort: str = "overall",
    score_dir: str = "desc",
    result_sort: str = "latency",
    result_dir: str = "asc",
) -> ReportDetailResponse:
    user_id = request_user_id(request)
    service = report_service(user_id)
    payload = normalize_results(load_report_or_404(report_name, user_id))
    payload = sort_results(payload, result_sort, result_dir)
    summary = service.summarize(report_name, payload).to_dict()
    scorecard = summary.get("scorecard")
    query_suffix = "" if user_id == "default" else f"?user_id={quote(user_id)}"
    if scorecard is not None:
        scorecard["mode_scorecards"] = sort_scorecards(scorecard.get("mode_scorecards", []), score_sort, score_dir)
    return ReportDetailResponse(
        report_name=report_name,
        summary=summary,
        results=payload,
        export_url=f"/reports/{report_name}/export{query_suffix}",
        pdf_export_url=f"/reports/{report_name}/export.pdf{query_suffix}",
        evidence_export_url=f"/reports/{report_name}/evidence.zip{query_suffix}",
        sorting={
            "score_sort": score_sort,
            "score_dir": score_dir,
            "result_sort": result_sort,
            "result_dir": result_dir,
        },
    )


@app.get("/api/telemetry", response_model=TelemetrySnapshotResponse)
def api_telemetry(request: Request, all_users: bool = False) -> TelemetrySnapshotResponse:
    user_id = None if all_users else request_user_id(request)
    return TelemetrySnapshotResponse(**STORE.telemetry_snapshot(user_id).to_dict())


@app.get("/api/mcp/registry", response_model=RemoteMCPRegistryResponse)
def api_remote_mcp_registry() -> RemoteMCPRegistryResponse:
    return RemoteMCPRegistryResponse(servers=REMOTE_REGISTRY.list_servers(enabled_only=False))


@app.post("/api/mcp/registry/sync", response_model=RemoteMCPRegistryResponse)
def api_remote_mcp_registry_sync() -> RemoteMCPRegistryResponse:
    REMOTE_REGISTRY.sync_from_file()
    return RemoteMCPRegistryResponse(servers=REMOTE_REGISTRY.list_servers(enabled_only=False))












@app.get("/api/a2a/registry", response_model=RemoteA2ARegistryResponse)
def api_remote_a2a_registry() -> RemoteA2ARegistryResponse:
    return RemoteA2ARegistryResponse(agents=REMOTE_A2A_REGISTRY.list_agents())


@app.get("/api/a2a/health", response_model=RemoteA2AHealthResponse)
def api_remote_a2a_health(
    customer_url: str = "",
    documentation_url: str = "",
    policy_url: str = "",
) -> RemoteA2AHealthResponse:
    from .a2a.remote_client import RemoteA2AClient

    override_urls = {
        "customer_data": validate_remote_url(customer_url, "customer_url"),
        "documentation": validate_remote_url(documentation_url, "documentation_url"),
        "policy_billing": validate_remote_url(policy_url, "policy_url"),
    }
    if any(override_urls.values()):
        items = [
            {"role": role, "url": url, "enabled": True}
            for role, url in override_urls.items()
            if url
        ]
    else:
        items = REMOTE_A2A_REGISTRY.list_agents()

    results = []
    for item in items:
        client = RemoteA2AClient(item["url"], timeout_s=1.5)
        try:
            health = client.health()
            results.append({**item, "status": health.get("status", "ok"), "detail": health})
        except Exception as exc:
            results.append({**item, "status": "unavailable", "error": str(exc)})
    return RemoteA2AHealthResponse(agents=results)


@app.get("/api/race/heatmap")
def api_race_heatmap() -> dict:
    """Return aggregated heatmap cells + baseline footer (D-52, HEAT-01/02).

    Pinned-baseline filter applied server-side (D-55, D-57): only runs whose
    run_meta event matches HEATMAP_BASELINE contribute cells. Cache rebuilt
    on first GET after race_done (D-54).
    """
    return get_heatmap()


@app.post("/api/race/run")
async def api_race_run(body: RaceRunRequest) -> dict:
    """Start a race in the background; return run_id for WS subscription (B1).

    run_id format: uuid4().hex[:16] — matches _RUN_ID_RE ^[A-Za-z0-9_-]{1,64}$.
    Frontend opens /api/race/ws?run_id=<id> after receiving this response.
    """
    run_id: str = uuid.uuid4().hex[:16]

    # Build TaskSpec list from validated task_ids.
    task_specs: list[TaskSpec] = []
    for tid in body.task_ids:
        cfg, _targets, _binds = TASK_CONFIGS[tid]
        task_specs.append(
            TaskSpec(
                task_id=tid,
                prompt="",  # v1 runners load their own prompt from TASK_CONFIGS — spec.prompt is never read
                allowed_tools=[],
                expected_shape={},
                hardness_profile=HardnessProfile(
                    types=list(cfg.hardness_profile)
                ),
            )
        )

    def _recorder_factory(*, run_id: str, lane: str, task_id: str) -> TraceRecorder:
        return TraceRecorder(mode=lane, runtime="live", task_id=task_id)

    async def _ws_emitter(event: dict) -> None:
        await MANAGER.publish(run_id, event)

    def _sync_ws_emitter(event: dict) -> None:
        # run_race calls ws_emitter synchronously; schedule the coroutine on the running loop.
        loop = asyncio.get_event_loop()
        loop.create_task(_ws_emitter(event))

    async def _do_run() -> None:
        await run_race(
            task_specs=task_specs,
            lanes=body.lanes,
            n=body.n,
            recorder_factory=_recorder_factory,
            ws_emitter=_sync_ws_emitter,
        )

    asyncio.create_task(_do_run())
    return {"run_id": run_id}


@app.get("/api/race/runs/{run_id}/trace")
def api_race_run_trace(run_id: str) -> dict:
    """Replay endpoint — load ndjson trace from disk for /race/<run_id> (HEAT-03).

    Path-traversal guard via _validate_run_id BEFORE any path resolution.
    No live LLM. No event mutation. schema_version is the disk schema (Phase 6 D-03).
    Events shipped verbatim (D-59 — backend `event_type` key NOT renamed).
    Frontend contract: matches RaceReplayPayload at client.ts:136-140.
    """
    try:
        _validate_run_id(run_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        events = load_run(run_id, RUNS_DIR)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="run not found")
    return {"run_id": run_id, "events": events, "schema_version": "1.0"}


@app.websocket("/api/race/ws")
async def race_ws(
    websocket: WebSocket,
    run_id: str = Query(...),
    last_seen_turn_index: int = Query(-1),
) -> None:
    # Path-traversal guard FIRST — before any file resolution or accept().
    try:
        _validate_run_id(run_id)
    except ValueError:
        await websocket.close(code=4400, reason="invalid run_id")
        return

    client_ip = websocket.client.host if websocket.client else "unknown"
    conn = await MANAGER.connect(websocket, run_id, last_seen_turn_index, client_ip)
    if conn is None:
        return  # 5/IP cap exceeded; ws already closed inside connect()

    try:
        # D-07 reconnect replay from disk: stream events with turn_index > last_seen_turn_index.
        if last_seen_turn_index >= 0:
            try:
                for ev in load_run(run_id, RUNS_DIR):
                    if ev.get("turn_index", -1) > last_seen_turn_index:
                        await websocket.send_json(ev)
            except FileNotFoundError:
                pass  # live-only run, no on-disk events yet

        # Live tail loop with 15s heartbeat.
        while True:
            try:
                event = await asyncio.wait_for(conn.queue.get(), timeout=HEARTBEAT_S)
                await websocket.send_json(event)
            except asyncio.TimeoutError:
                await websocket.send_json(
                    {"event_type": "heartbeat", "ts_ms": int(_ws_time.time() * 1000)}
                )
    except WebSocketDisconnect:
        pass
    finally:
        await MANAGER.disconnect(conn)

