from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any
import json
import textwrap

from .identity import normalize_user_id, user_artifact_root
from .schemas import ModeScorecard, ReportScorecard, ReportSummary, SupportTicket


class ReportService:
    def __init__(self, project_root: Path, user_id: str | None = None) -> None:
        self.project_root = project_root
        self.user_id = normalize_user_id(user_id)
        self.artifact_root = user_artifact_root(project_root, self.user_id)
        self.report_dir = self.artifact_root / "reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def resolve_report_path(self, report_name: str, *, must_exist: bool = True) -> Path:
        if not report_name.endswith(".json"):
            raise ValueError("Report name must end with .json")
        if Path(report_name).name != report_name:
            raise ValueError("Report name must not include path separators")
        report_path = (self.report_dir / report_name).resolve()
        report_root = self.report_dir.resolve()
        if report_path.parent != report_root:
            raise ValueError("Report path escapes the reports directory")
        if must_exist and not report_path.exists():
            raise FileNotFoundError(report_name)
        return report_path

    def list_reports(self) -> list[dict[str, str]]:
        reports: list[dict[str, str]] = []
        for path in sorted(self.report_dir.glob("*.json"), reverse=True):
            reports.append({"name": path.name, "path": str(path)})
        return reports

    def list_report_summaries(self) -> list[ReportSummary]:
        summaries: list[ReportSummary] = []
        for entry in self.list_reports():
            payload = self.load_report(entry["name"])
            summaries.append(self.summarize(entry["name"], payload))
        return summaries

    def build_trend_view(
        self,
        scenario: str | None = None,
        runtime: str | None = None,
        recommended_mode: str | None = None,
        mode_sort: str = "overall",
        mode_dir: str = "desc",
        scenario_sort: str = "count",
        scenario_dir: str = "desc",
        report_sort: str = "recent",
        report_dir: str = "desc",
    ) -> dict[str, Any]:
        reports = self.list_reports()
        applied_filters = {"scenario": scenario or "", "runtime": runtime or "", "recommended_mode": recommended_mode or ""}
        applied_sorting = {
            "mode_sort": mode_sort,
            "mode_dir": mode_dir,
            "scenario_sort": scenario_sort,
            "scenario_dir": scenario_dir,
            "report_sort": report_sort,
            "report_dir": report_dir,
        }
        if not reports:
            return {
                "total_reports": 0,
                "scenario_counts": [],
                "runtime_counts": {},
                "recommended_mode_counts": [],
                "average_totals": {"tool_calls": 0.0, "a2a_messages": 0.0, "failures": 0.0},
                "mode_trends": [],
                "a2a_transport_counts": {},
                "recent_reports": [],
                "narrative": ["No saved reports yet. Run and save a few demos to unlock trend analysis."],
                "available_filters": {"scenarios": [], "runtimes": [], "recommended_modes": []},
                "applied_filters": applied_filters,
                "applied_sorting": applied_sorting,
            }

        scenario_counts: dict[str, int] = {}
        runtime_counts: dict[str, int] = {}
        recommended_mode_counts: dict[str, int] = {}
        mode_accumulator: dict[str, dict[str, float]] = {}
        a2a_transport_counts: dict[str, int] = {}
        total_tool_calls = 0
        total_a2a_messages = 0
        total_failures = 0
        recent_reports: list[dict[str, Any]] = []

        available_scenarios: set[str] = set()
        available_runtimes: set[str] = set()
        available_recommended_modes: set[str] = set()

        for entry in reports:
            payload = self.load_report(entry["name"])
            summary = self.summarize(entry["name"], payload)
            available_scenarios.add(summary.scenario)
            available_runtimes.add(summary.runtime)
            if summary.scorecard is not None:
                available_recommended_modes.add(summary.scorecard.recommended_demo_mode)
            if scenario and summary.scenario != scenario:
                continue
            if runtime and summary.runtime != runtime:
                continue
            if recommended_mode and (summary.scorecard is None or summary.scorecard.recommended_demo_mode != recommended_mode):
                continue
            recent_reports.append(summary.to_dict())
            scenario_counts[summary.scenario] = scenario_counts.get(summary.scenario, 0) + 1
            runtime_counts[summary.runtime] = runtime_counts.get(summary.runtime, 0) + 1
            total_tool_calls += summary.total_tool_calls
            total_a2a_messages += summary.total_a2a_messages
            total_failures += summary.total_failures
            if summary.scorecard is None:
                continue
            recommended = summary.scorecard.recommended_demo_mode
            recommended_mode_counts[recommended] = recommended_mode_counts.get(recommended, 0) + 1
            for result in payload:
                transport = result.get("a2a_transport", "local")
                a2a_transport_counts[transport] = a2a_transport_counts.get(transport, 0) + 1
            raw_by_mode = {item["mode"]: item["metrics"] for item in payload}
            for card in summary.scorecard.mode_scorecards:
                bucket = mode_accumulator.setdefault(card.mode, {"appearances": 0, "overall": 0.0, "presentation": 0.0, "resilience": 0.0, "latency": 0.0, "tools": 0.0, "a2a": 0.0, "recommended": 0.0})
                metrics = raw_by_mode.get(card.mode, {})
                bucket["appearances"] += 1
                bucket["overall"] += card.overall_score
                bucket["presentation"] += card.presentation_score
                bucket["resilience"] += card.resilience_score
                bucket["latency"] += float(metrics.get("latency_ms", 0.0))
                bucket["tools"] += float(metrics.get("tool_calls", 0.0))
                bucket["a2a"] += float(metrics.get("a2a_messages", 0.0))
                if card.mode == recommended:
                    bucket["recommended"] += 1

        report_count = len(recent_reports)
        if report_count == 0:
            return {
                "total_reports": 0,
                "scenario_counts": [],
                "runtime_counts": {},
                "recommended_mode_counts": [],
                "average_totals": {"tool_calls": 0.0, "a2a_messages": 0.0, "failures": 0.0},
                "mode_trends": [],
                "a2a_transport_counts": {},
                "recent_reports": [],
                "narrative": ["No saved reports match the current filters."],
                "available_filters": {
                    "scenarios": sorted(available_scenarios),
                    "runtimes": sorted(available_runtimes),
                    "recommended_modes": sorted(available_recommended_modes),
                },
                "applied_filters": applied_filters,
                "applied_sorting": applied_sorting,
            }

        mode_trends = []
        for mode, stats in sorted(mode_accumulator.items()):
            appearances = int(stats["appearances"]) or 1
            mode_trends.append({
                "mode": mode,
                "appearances": appearances,
                "recommended_count": int(stats["recommended"]),
                "avg_overall_score": round(stats["overall"] / appearances, 2),
                "avg_presentation_score": round(stats["presentation"] / appearances, 2),
                "avg_resilience_score": round(stats["resilience"] / appearances, 2),
                "avg_latency_ms": round(stats["latency"] / appearances, 3),
                "avg_tool_calls": round(stats["tools"] / appearances, 2),
                "avg_a2a_messages": round(stats["a2a"] / appearances, 2),
            })

        scenario_rows = [{"scenario": s, "count": c} for s, c in scenario_counts.items()]
        recommended_rows = [{"mode": m, "count": c} for m, c in sorted(recommended_mode_counts.items(), key=lambda item: (-item[1], item[0]))]
        averages = {"tool_calls": round(total_tool_calls / report_count, 2), "a2a_messages": round(total_a2a_messages / report_count, 2), "failures": round(total_failures / report_count, 2)}

        mode_trends = self._sort_mode_trends(mode_trends, mode_sort, mode_dir)
        scenario_rows = self._sort_scenario_rows(scenario_rows, scenario_sort, scenario_dir)
        recent_reports = self._sort_recent_reports(recent_reports, report_sort, report_dir)

        top_mode = mode_trends[0]["mode"] if mode_trends else "baseline"
        top_scenario = scenario_rows[0]["scenario"] if scenario_rows else "custom"
        narrative = [
            f"{top_mode.upper()} has been the strongest all-around mode across saved reports by average overall score.",
            f"{top_scenario.replace('_', ' ').title()} is the most frequently saved scenario so far.",
            f"Across saved reports, the average run produces {averages['tool_calls']} tool calls and {averages['a2a_messages']} A2A messages.",
        ]
        if recommended_rows:
            narrative.append(f"{recommended_rows[0]['mode'].upper()} has been recommended most often for presentation use across saved reports.")
        return {
            "total_reports": report_count,
            "scenario_counts": scenario_rows,
            "runtime_counts": runtime_counts,
            "recommended_mode_counts": recommended_rows,
            "average_totals": averages,
            "mode_trends": mode_trends,
            "a2a_transport_counts": a2a_transport_counts,
            "recent_reports": recent_reports[:5],
            "narrative": narrative,
            "available_filters": {
                "scenarios": sorted(available_scenarios),
                "runtimes": sorted(available_runtimes),
                "recommended_modes": sorted(available_recommended_modes),
            },
            "applied_filters": applied_filters,
            "applied_sorting": applied_sorting,
        }

    def save_report(self, ticket: SupportTicket, payload: list[dict[str, Any]]) -> Path:
        report_path = self.report_dir / f"{ticket.ticket_id}_report.json"
        report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return report_path

    def load_report(self, report_name: str) -> list[dict[str, Any]]:
        report_path = self.resolve_report_path(report_name)
        return json.loads(report_path.read_text(encoding="utf-8"))

    def summarize(self, report_name: str, payload: list[dict[str, Any]], generated_at: str | None = None) -> ReportSummary:
        first = payload[0] if payload else {}
        ticket = first.get("ticket", {})
        metrics = [item.get("metrics", {}) for item in payload]
        runtime = first.get("runtime", "mock")
        generated_at = generated_at or self._report_generated_at(report_name)
        scenario = ticket.get("scenario", "custom")
        title = ticket.get("title") or scenario.replace("_", " ").title()
        total_tool_calls = sum(int(item.get("tool_calls", 0)) for item in metrics)
        total_a2a_messages = sum(int(item.get("a2a_messages", 0)) for item in metrics)
        total_failures = sum(int(item.get("failures", 0)) for item in metrics)
        scorecard = self._build_scorecard(payload)
        talking_points = self._talking_points(payload, scorecard)
        return ReportSummary(
            report_name=report_name,
            scenario=scenario,
            title=title,
            runtime=runtime,
            generated_at=generated_at,
            mode_count=len(payload),
            total_tool_calls=total_tool_calls,
            total_a2a_messages=total_a2a_messages,
            total_failures=total_failures,
            talking_points=talking_points,
            scorecard=scorecard,
        )

    def _report_generated_at(self, report_name: str) -> str:
        report_path = self.report_dir / report_name
        if report_path.exists():
            return datetime.fromtimestamp(report_path.stat().st_mtime, tz=timezone.utc).isoformat()
        return datetime.now(timezone.utc).isoformat()

    def _sort_mode_trends(self, rows: list[dict[str, Any]], sort_by: str, direction: str) -> list[dict[str, Any]]:
        sorters = {
            "mode": lambda item: item["mode"],
            "overall": lambda item: float(item["avg_overall_score"]),
            "presentation": lambda item: float(item["avg_presentation_score"]),
            "resilience": lambda item: float(item["avg_resilience_score"]),
            "latency": lambda item: float(item["avg_latency_ms"]),
            "tools": lambda item: float(item["avg_tool_calls"]),
            "a2a": lambda item: float(item["avg_a2a_messages"]),
            "recommended": lambda item: int(item["recommended_count"]),
        }
        reverse = direction == "desc"
        return sorted(rows, key=sorters.get(sort_by, sorters["overall"]), reverse=reverse)

    def _sort_scenario_rows(self, rows: list[dict[str, Any]], sort_by: str, direction: str) -> list[dict[str, Any]]:
        sorters = {
            "scenario": lambda item: item["scenario"],
            "count": lambda item: int(item["count"]),
        }
        reverse = direction == "desc"
        return sorted(rows, key=sorters.get(sort_by, sorters["count"]), reverse=reverse)

    def _sort_recent_reports(self, rows: list[dict[str, Any]], sort_by: str, direction: str) -> list[dict[str, Any]]:
        sorters = {
            "recent": lambda item: item["generated_at"],
            "report": lambda item: item["report_name"],
            "scenario": lambda item: item["scenario"],
            "runtime": lambda item: item["runtime"],
            "recommended": lambda item: (item.get("scorecard") or {}).get("recommended_demo_mode", ""),
            "tools": lambda item: int(item.get("total_tool_calls", 0)),
            "failures": lambda item: int(item.get("total_failures", 0)),
        }
        reverse = direction == "desc"
        return sorted(rows, key=sorters.get(sort_by, sorters["recent"]), reverse=reverse)

    def export_html(self, report_name: str, payload: list[dict[str, Any]]) -> str:
        summary = self.summarize(report_name, payload)
        scorecard = summary.scorecard or ReportScorecard("baseline", "baseline", "baseline", "baseline", "baseline")
        ticket = payload[0]["ticket"] if payload else {"query": "", "customer_id": ""}

        rows = []
        for result in payload:
            metrics = result["metrics"]
            rows.append(
                "".join(
                    [
                        "<tr>",
                        f"<td><span class=\"mode-pill\">{escape(result['mode'].upper())}</span></td>",
                        f"<td>{escape(str(metrics['latency_ms']))} ms</td>",
                        f"<td>{escape(str(metrics['tool_calls']))}</td>",
                        f"<td>{escape(str(metrics['a2a_messages']))}</td>",
                        f"<td>{escape(str(metrics['failures']))}</td>",
                        f"<td>{escape(result['final_answer'])}</td>",
                        "</tr>",
                    ]
                )
            )

        score_rows = []
        score_highlights = []
        for card in scorecard.mode_scorecards:
            score_rows.append(
                "".join(
                    [
                        "<tr>",
                        f"<td><span class=\"mode-pill\">{escape(card.mode.upper())}</span></td>",
                        f"<td>{card.overall_score}</td>",
                        f"<td>{card.responsiveness_score}</td>",
                        f"<td>{card.tooling_score}</td>",
                        f"<td>{card.collaboration_score}</td>",
                        f"<td>{card.resilience_score}</td>",
                        f"<td>{card.presentation_score}</td>",
                        f"<td>{escape(card.headline)}</td>",
                        "</tr>",
                    ]
                )
            )
            score_highlights.append(
                f"""
                <article class="highlight-card">
                  <div class="highlight-head">
                    <span class="mode-pill">{escape(card.mode.upper())}</span>
                    <strong>{card.overall_score}/100</strong>
                  </div>
                  <p>{escape(card.headline)}</p>
                  <div class="mini-grid">
                    <span>Responsive {card.responsiveness_score}</span>
                    <span>Tooling {card.tooling_score}</span>
                    <span>Collaboration {card.collaboration_score}</span>
                    <span>Resilience {card.resilience_score}</span>
                    <span>Presentation {card.presentation_score}</span>
                  </div>
                </article>
                """
            )

        metric_charts = self._metric_chart_html(payload)
        radar_rows = []
        for card in scorecard.mode_scorecards:
            radar_rows.append(
                f"""
                <div class="radar-card">
                  <div class="radar-head">
                    <strong>{escape(card.mode.upper())}</strong>
                    <span>{card.overall_score}/100</span>
                  </div>
                  {self._score_bar('Responsiveness', card.responsiveness_score)}
                  {self._score_bar('Tooling', card.tooling_score)}
                  {self._score_bar('Collaboration', card.collaboration_score)}
                  {self._score_bar('Resilience', card.resilience_score)}
                  {self._score_bar('Presentation', card.presentation_score)}
                </div>
                """
            )

        points = "".join(f"<li>{escape(point)}</li>" for point in summary.talking_points)
        note_items = "".join(f"<li>{escape(note)}</li>" for note in scorecard.notes)

        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{escape(summary.title)} Report</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #102033;
      --muted: #5b6b7c;
      --paper: #f4efe6;
      --panel: #fffdf9;
      --line: #d8d0c2;
      --accent: #b85c38;
      --accent-soft: #f7e0d5;
      --deep: #17475f;
      --sea: #2d6f7d;
      --sand: #ecd9c2;
      --shadow: 0 16px 40px rgba(30, 25, 10, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Georgia, 'Times New Roman', serif; color: var(--ink); background: linear-gradient(180deg, #f8f4ec, #efe7d7); }}
    .page {{ max-width: 1180px; margin: 0 auto; padding: 40px 28px 56px; }}
    .hero {{ background: linear-gradient(135deg, rgba(23, 71, 95, 0.96), rgba(184, 92, 56, 0.9)); color: #fffdf8; border-radius: 28px; padding: 34px; box-shadow: var(--shadow); }}
    .hero-grid {{ display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 22px; align-items: end; }}
    .eyebrow {{ text-transform: uppercase; letter-spacing: 0.16em; font-size: 12px; color: inherit; opacity: 0.8; margin: 0 0 8px; }}
    h1 {{ margin: 0 0 8px; font-size: 42px; }}
    h2 {{ margin: 0; font-size: 24px; }}
    p {{ line-height: 1.6; }}
    .hero-copy {{ max-width: 720px; }}
    .summary {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-top: 22px; }}
    .pill {{ background: rgba(255, 250, 243, 0.14); border-radius: 18px; padding: 16px; border: 1px solid rgba(255,255,255,0.18); backdrop-filter: blur(2px); }}
    .pill strong {{ display: block; font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 6px; }}
    .hero-note {{ background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.16); border-radius: 20px; padding: 18px; }}
    .hero-note ul {{ margin: 10px 0 0; padding-left: 18px; }}
    .section {{ margin-top: 24px; background: var(--panel); border: 1px solid var(--line); border-radius: 24px; padding: 22px 24px; box-shadow: var(--shadow); }}
    .score-grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin-top: 18px; }}
    .score-box {{ background: #f8f2ea; border: 1px solid var(--line); border-radius: 18px; padding: 16px; }}
    .score-box strong {{ display: block; color: var(--deep); font-size: 12px; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 6px; }}
    .highlight-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-top: 18px; }}
    .highlight-card {{ border: 1px solid var(--line); border-radius: 18px; padding: 16px; background: linear-gradient(180deg, #fffaf3, #f8f1e6); }}
    .highlight-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 10px; }}
    .mode-pill {{ display: inline-flex; align-items: center; padding: 6px 10px; border-radius: 999px; background: var(--accent-soft); color: var(--deep); font-size: 12px; letter-spacing: 0.08em; font-weight: 700; }}
    .mini-grid {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
    .mini-grid span {{ border-radius: 999px; background: #fffdf9; border: 1px solid var(--line); padding: 6px 10px; font-size: 12px; color: var(--muted); }}
    .chart-grid {{ display: grid; grid-template-columns: 1.05fr 0.95fr; gap: 18px; margin-top: 18px; }}
    .chart-card {{ background: linear-gradient(180deg, #fffaf3, #f8f1e6); border: 1px solid var(--line); border-radius: 20px; padding: 18px; }}
    .metric-group {{ margin-bottom: 16px; }}
    .metric-group:last-child {{ margin-bottom: 0; }}
    .metric-title {{ display: flex; justify-content: space-between; gap: 16px; margin-bottom: 10px; font-size: 13px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }}
    .bar-stack {{ display: grid; gap: 8px; }}
    .bar-row {{ display: grid; grid-template-columns: 92px 1fr 56px; align-items: center; gap: 10px; font-size: 14px; }}
    .track {{ height: 10px; border-radius: 999px; background: var(--sand); overflow: hidden; }}
    .fill {{ height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--accent), var(--sea)); }}
    .radar-stack {{ display: grid; gap: 12px; }}
    .radar-card {{ border: 1px solid var(--line); border-radius: 16px; padding: 14px; background: #fffdf9; }}
    .radar-head {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px; }}
    .mini-bar {{ display: grid; grid-template-columns: 110px 1fr 38px; gap: 8px; align-items: center; font-size: 13px; margin-top: 6px; }}
    .mini-track {{ height: 8px; background: #e8dccd; border-radius: 999px; overflow: hidden; }}
    .mini-fill {{ height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--deep), var(--accent)); }}
    .print-grid {{ display: grid; grid-template-columns: 0.95fr 1.05fr; gap: 16px; margin-top: 18px; }}
    .print-card {{ border: 1px solid var(--line); border-radius: 18px; background: #fffaf3; padding: 16px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 12px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ font-size: 13px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); }}
    tbody tr:nth-child(odd) {{ background: rgba(248, 242, 234, 0.45); }}
    ul {{ margin: 12px 0 0; padding-left: 20px; }}
    .dense-columns {{ columns: 2; column-gap: 28px; }}
    .dense-columns li {{ break-inside: avoid; margin-bottom: 8px; }}
    code {{ font-family: Consolas, monospace; font-size: 0.95em; }}
    .print-note {{ color: var(--muted); font-size: 13px; margin-top: 8px; }}
    @page {{ margin: 12mm; }}
    @media print {{
      body {{ background: #fff; color: #111; font-size: 10.5pt; }}
      .page {{ max-width: none; padding: 0; }}
      .hero {{ color: #111; background: #fff; border: 1px solid #bbb; box-shadow: none; padding: 18px 20px; }}
      .hero-grid, .chart-grid, .print-grid {{ grid-template-columns: 1fr; gap: 12px; }}
      .pill, .hero-note, .section, .chart-card, .radar-card, .print-card, .highlight-card {{ background: #fff !important; box-shadow: none; border-color: #bbb; page-break-inside: avoid; }}
      .section {{ margin-top: 14px; padding: 14px 16px; }}
      .summary {{ gap: 8px; margin-top: 14px; }}
      .dense-columns {{ columns: 2; }}
      th, td {{ padding: 7px 6px; font-size: 9pt; }}
      h1 {{ font-size: 24pt; }}
      h2 {{ font-size: 15pt; }}
      .mode-pill, .mini-grid span {{ border: 1px solid #bbb; background: #fff; color: #111; }}
    }}
    @media (max-width: 900px) {{
      .hero-grid, .chart-grid, .print-grid, .summary, .score-grid {{ grid-template-columns: 1fr; }}
      .dense-columns {{ columns: 1; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">A2A vs MCP Presentation Report</p>
          <h1>{escape(summary.title)}</h1>
          <p>{escape(ticket.get('query', ''))}</p>
          <div class="summary">
            <div class="pill"><strong>Scenario</strong>{escape(summary.scenario)}</div>
            <div class="pill"><strong>Runtime</strong>{escape(summary.runtime)}</div>
            <div class="pill"><strong>Tool Calls</strong>{summary.total_tool_calls}</div>
            <div class="pill"><strong>A2A Messages</strong>{summary.total_a2a_messages}</div>
          </div>
        </div>
        <aside class="hero-note">
          <strong>Presentation Snapshot</strong>
          <ul>
            <li>Recommended mode: {escape(scorecard.recommended_demo_mode.upper())}</li>
            <li>Fastest mode: {escape(scorecard.fastest_mode.upper())}</li>
            <li>Resilience anchor: {escape(scorecard.most_resilient_mode.upper())}</li>
            <li>Customer: {escape(ticket.get('customer_id', ''))}</li>
            <li>Report: {escape(summary.report_name)}</li>
          </ul>
        </aside>
      </div>
    </section>
    <section class="section">
      <p class="eyebrow">Scorecard</p>
      <h2>Demo Recommendations</h2>
      <div class="score-grid">
        <div class="score-box"><strong>Fastest</strong>{escape(scorecard.fastest_mode.upper())}</div>
        <div class="score-box"><strong>Tooling</strong>{escape(scorecard.most_tool_heavy_mode.upper())}</div>
        <div class="score-box"><strong>Collaboration</strong>{escape(scorecard.most_collaborative_mode.upper())}</div>
        <div class="score-box"><strong>Resilience</strong>{escape(scorecard.most_resilient_mode.upper())}</div>
        <div class="score-box"><strong>Recommended</strong>{escape(scorecard.recommended_demo_mode.upper())}</div>
      </div>
      <div class="highlight-grid">{''.join(score_highlights)}</div>
      <ul class="dense-columns">{note_items}</ul>
    </section>
    <section class="section">
      <p class="eyebrow">Visual Scorecards</p>
      <h2>Metric Charts</h2>
      <div class="chart-grid">
        <div class="chart-card">{metric_charts}</div>
        <div class="chart-card"><div class="radar-stack">{''.join(radar_rows)}</div></div>
      </div>
    </section>
    <section class="section">
      <p class="eyebrow">Presenter Notes</p>
      <h2>Talking Points</h2>
      <div class="print-grid">
        <div class="print-card">
          <strong>Audience-ready narrative</strong>
          <ul class="dense-columns">{points}</ul>
        </div>
        <div class="print-card">
          <strong>Printable takeaway</strong>
          <p class="print-note">This report is designed to work both onscreen and on paper. The scorecard and comparison tables below use denser print spacing so they remain useful in a leave-behind handout.</p>
        </div>
      </div>
    </section>
    <section class="section">
      <p class="eyebrow">Mode Scorecards</p>
      <table>
        <thead>
          <tr>
            <th>Mode</th>
            <th>Overall</th>
            <th>Responsive</th>
            <th>Tooling</th>
            <th>Collaboration</th>
            <th>Resilience</th>
            <th>Presentation</th>
            <th>Headline</th>
          </tr>
        </thead>
        <tbody>
          {''.join(score_rows)}
        </tbody>
      </table>
    </section>
    <section class="section">
      <p class="eyebrow">Mode Comparison</p>
      <table>
        <thead>
          <tr>
            <th>Mode</th>
            <th>Latency</th>
            <th>Tools</th>
            <th>A2A</th>
            <th>Failures</th>
            <th>Answer</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>"""

    def export_pdf_bytes(self, report_name: str, payload: list[dict[str, Any]]) -> bytes:
        summary = self.summarize(report_name, payload)
        lines = self._pdf_lines(summary, payload)
        return self._build_simple_pdf(lines)

    def export_pdf(self, report_name: str, payload: list[dict[str, Any]]) -> Path:
        report_path = self.resolve_report_path(report_name, must_exist=False)
        path = report_path.with_suffix(".pdf")
        path.write_bytes(self.export_pdf_bytes(report_name, payload))
        return path

    def _talking_points(self, payload: list[dict[str, Any]], scorecard: ReportScorecard) -> list[str]:
        points: list[str] = []
        if payload:
            recommended_card = next((card for card in scorecard.mode_scorecards if card.mode == scorecard.recommended_demo_mode), None)
            if recommended_card is not None:
                points.append(
                    f"{scorecard.recommended_demo_mode.upper()} is the recommended presentation mode with an overall score of {recommended_card.overall_score}."
                )
        if any(item.get("mode") == "mcp" for item in payload):
            mcp_result = next(item for item in payload if item.get("mode") == "mcp")
            points.append(
                f"MCP mode made {mcp_result['metrics']['tool_calls']} structured tool calls and is the clearest external-capability story in this run."
            )
        if any(item.get("mode") == "a2a" for item in payload):
            a2a_result = next(item for item in payload if item.get("mode") == "a2a")
            points.append(
                f"A2A mode exchanged {a2a_result['metrics']['a2a_messages']} agent messages, making delegation behavior easy to narrate."
            )
        if any(item.get("mode") == "hybrid" for item in payload):
            hybrid_result = next(item for item in payload if item.get("mode") == "hybrid")
            points.append(
                f"Hybrid mode combined {hybrid_result['metrics']['tool_calls']} tool calls and {hybrid_result['metrics']['a2a_messages']} agent messages, which makes it the most enterprise-shaped comparison path."
            )
        if any(item.get("metrics", {}).get("failures", 0) for item in payload):
            points.append(
                f"{scorecard.most_resilient_mode.upper()} is the strongest resilience talking point for this run because it retained the best resilience score under failure pressure."
            )
        else:
            points.append(
                f"{scorecard.fastest_mode.upper()} is the cleanest opener for a happy-path demo because it finished with the lowest latency."
            )
        return points

    def _build_scorecard(self, payload: list[dict[str, Any]]) -> ReportScorecard:
        metric_values = {
            "latency": [float(item["metrics"]["latency_ms"]) for item in payload],
            "tool_calls": [int(item["metrics"]["tool_calls"]) for item in payload],
            "a2a_messages": [int(item["metrics"]["a2a_messages"]) for item in payload],
            "failures": [int(item["metrics"]["failures"]) for item in payload],
            "retries": [int(item["metrics"]["retries"]) for item in payload],
        }
        cards = [self._mode_scorecard(item, metric_values) for item in payload]
        fastest = min(payload, key=lambda item: float(item["metrics"]["latency_ms"]))["mode"]
        most_tool_heavy = max(payload, key=lambda item: int(item["metrics"]["tool_calls"]))["mode"]
        most_collaborative = max(payload, key=lambda item: int(item["metrics"]["a2a_messages"]))["mode"]
        most_resilient = max(cards, key=lambda card: (card.resilience_score, card.overall_score, card.presentation_score)).mode
        recommended = max(cards, key=lambda card: (card.overall_score, card.presentation_score, card.resilience_score)).mode
        notes = [
            f"{recommended.upper()} is the best all-around demo mode for this run because it blended explanation quality, architecture signal, and resilience most effectively.",
            f"{fastest.upper()} is the quickest entry point for a live walkthrough because it posted the strongest responsiveness score.",
            f"{most_collaborative.upper()} gives the clearest delegation story, while {most_tool_heavy.upper()} gives the clearest MCP tool-boundary story.",
        ]
        if any(int(item["metrics"]["failures"]) for item in payload):
            notes.append(f"{most_resilient.upper()} is the best fallback narrative because it held the top resilience score in a non-happy-path run.")
        else:
            notes.append("This run stayed on the happy path, so the scorecard emphasizes clarity, structure, and demo readability over recovery behavior.")
        return ReportScorecard(
            fastest_mode=fastest,
            most_tool_heavy_mode=most_tool_heavy,
            most_collaborative_mode=most_collaborative,
            most_resilient_mode=most_resilient,
            recommended_demo_mode=recommended,
            mode_scorecards=cards,
            notes=notes,
        )

    def _mode_scorecard(self, result: dict[str, Any], metric_values: dict[str, list[float]]) -> ModeScorecard:
        metrics = result["metrics"]
        agent_count = len(result.get("agents_used", []))
        strengths = len(metrics.get("strengths", []))
        weaknesses = len(metrics.get("weaknesses", []))
        complexity_bonus = {"low": 0, "medium": 6, "high": 12}.get(metrics.get("complexity", "medium"), 0)

        responsiveness = self._inverse_normalized_score(float(metrics["latency_ms"]), metric_values["latency"], floor=35)
        tooling = self._normalized_score(int(metrics["tool_calls"]), metric_values["tool_calls"], floor=18) + (8 if int(metrics["tool_calls"]) > 0 else 0)
        collaboration = self._normalized_score(int(metrics["a2a_messages"]), metric_values["a2a_messages"], floor=12) + min(18, max(0, agent_count - 1) * 6)
        failure_penalty = self._inverse_normalized_score(int(metrics["failures"]), metric_values["failures"], floor=55)
        retry_penalty = self._inverse_normalized_score(int(metrics["retries"]), metric_values["retries"], floor=70)
        resilience = max(20, min(100, int(round((failure_penalty * 0.7) + (retry_penalty * 0.3)))))
        presentation = max(30, min(100, 52 + strengths * 9 - weaknesses * 4 + complexity_bonus + min(12, agent_count * 2)))

        overall = int(
            round(
                (responsiveness * 0.21)
                + (tooling * 0.19)
                + (collaboration * 0.19)
                + (resilience * 0.24)
                + (presentation * 0.17)
            )
        )
        headline = self._headline(result["mode"], tooling, collaboration, resilience, presentation)
        return ModeScorecard(
            mode=result["mode"],
            overall_score=overall,
            responsiveness_score=max(0, min(100, responsiveness)),
            tooling_score=max(0, min(100, tooling)),
            collaboration_score=max(0, min(100, collaboration)),
            resilience_score=max(0, min(100, resilience)),
            presentation_score=max(0, min(100, presentation)),
            headline=headline,
        )

    def _headline(self, mode: str, tooling: int, collaboration: int, resilience: int, presentation: int) -> str:
        if mode == "baseline":
            return "Best for a quick baseline narrative with minimal moving parts."
        dominant = max(
            [
                ("tooling", tooling),
                ("collaboration", collaboration),
                ("resilience", resilience),
                ("presentation", presentation),
            ],
            key=lambda item: item[1],
        )[0]
        if dominant == "tooling":
            return "Strongest when the demo needs crisp tool boundaries and structured external capability access."
        if dominant == "collaboration":
            return "Strongest when the demo needs visible specialist coordination and delegation."
        if dominant == "resilience":
            return "Best fit when the story emphasizes fallback behavior and operational robustness."
        return "Strongest when the audience needs a polished, balanced explanation of the architecture tradeoffs."

    def _metric_chart_html(self, payload: list[dict[str, Any]]) -> str:
        groups = [
            ("Latency Advantage", self._chart_rows(payload, "latency_ms", inverse=True, suffix=" ms")),
            ("Tool Usage", self._chart_rows(payload, "tool_calls")),
            ("A2A Coordination", self._chart_rows(payload, "a2a_messages")),
            ("Reliability", self._chart_rows(payload, "failures", inverse=True)),
        ]
        sections = []
        for title, rows in groups:
            sections.append(
                f"<div class=\"metric-group\"><div class=\"metric-title\"><span>{escape(title)}</span><span>Relative</span></div><div class=\"bar-stack\">{''.join(rows)}</div></div>"
            )
        return "".join(sections)

    def _chart_rows(self, payload: list[dict[str, Any]], metric_key: str, inverse: bool = False, suffix: str = "") -> list[str]:
        values = [float(item["metrics"][metric_key]) for item in payload]
        rows = []
        for item in payload:
            raw = float(item["metrics"][metric_key])
            score = self._inverse_normalized_score(raw, values, floor=25) if inverse else self._normalized_score(raw, values, floor=20)
            width = max(8, min(100, score))
            label_value = f"{item['metrics'][metric_key]}{suffix}" if suffix else f"{item['metrics'][metric_key]}"
            rows.append(
                f"<div class=\"bar-row\"><span>{escape(item['mode'].upper())}</span><div class=\"track\"><div class=\"fill\" style=\"width:{width}%\"></div></div><span>{escape(label_value)}</span></div>"
            )
        return rows

    def _score_bar(self, label: str, score: int) -> str:
        width = max(6, min(100, score))
        return f"<div class=\"mini-bar\"><span>{escape(label)}</span><div class=\"mini-track\"><div class=\"mini-fill\" style=\"width:{width}%\"></div></div><span>{score}</span></div>"

    def _normalized_score(self, value: float, series: list[float], floor: int = 0) -> int:
        minimum = min(series)
        maximum = max(series)
        if maximum == minimum:
            return max(floor, 70)
        normalized = (value - minimum) / (maximum - minimum)
        return int(round(floor + normalized * (100 - floor)))

    def _inverse_normalized_score(self, value: float, series: list[float], floor: int = 0) -> int:
        minimum = min(series)
        maximum = max(series)
        if maximum == minimum:
            return max(floor, 85)
        normalized = (maximum - value) / (maximum - minimum)
        return int(round(floor + normalized * (100 - floor)))

    def _pdf_lines(self, summary: ReportSummary, payload: list[dict[str, Any]]) -> list[str]:
        scorecard = summary.scorecard or self._build_scorecard(payload)
        ticket = payload[0]["ticket"] if payload else {"query": "", "customer_id": ""}
        lines = [
            "A2A vs MCP Presentation Report",
            "",
            f"Title: {summary.title}",
            f"Scenario: {summary.scenario}",
            f"Customer: {ticket.get('customer_id', '')}",
            f"Runtime: {summary.runtime}",
            f"Report: {summary.report_name}",
            "",
            "Scorecard",
            f"Fastest mode: {scorecard.fastest_mode}",
            f"Most tool-heavy mode: {scorecard.most_tool_heavy_mode}",
            f"Most collaborative mode: {scorecard.most_collaborative_mode}",
            f"Most resilient mode: {scorecard.most_resilient_mode}",
            f"Recommended demo mode: {scorecard.recommended_demo_mode}",
            "",
            "Talking points",
        ]
        lines.extend(f"- {point}" for point in summary.talking_points)
        lines.append("")
        lines.append("Mode scorecards")
        for card in scorecard.mode_scorecards:
            lines.append(
                f"- {card.mode.upper()}: overall {card.overall_score}, responsive {card.responsiveness_score}, tooling {card.tooling_score}, collaboration {card.collaboration_score}, resilience {card.resilience_score}, presentation {card.presentation_score}"
            )
            lines.append(f"  {card.headline}")
        lines.append("")
        lines.append("Mode answers")
        for item in payload:
            metrics = item["metrics"]
            lines.append(
                f"- {item['mode'].upper()}: latency {metrics['latency_ms']} ms, tools {metrics['tool_calls']}, A2A {metrics['a2a_messages']}, failures {metrics['failures']}"
            )
            lines.extend(textwrap.wrap(item["final_answer"], width=92, initial_indent="  ", subsequent_indent="  "))
            lines.append("")
        return lines

    def _build_simple_pdf(self, lines: list[str]) -> bytes:
        page_width = 612
        page_height = 792
        margin_x = 54
        margin_top = 54
        line_height = 15
        max_lines = 44
        pages = [lines[index:index + max_lines] for index in range(0, len(lines), max_lines)] or [[""]]

        objects: list[bytes] = []

        def add_object(data: bytes) -> int:
            objects.append(data)
            return len(objects)

        font_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        page_ids: list[int] = []
        pages_id_placeholder = len(objects) + 1

        for page_lines in pages:
            commands = [b"BT", b"/F1 11 Tf"]
            y = page_height - margin_top
            for raw in page_lines:
                safe = self._escape_pdf_text(raw)
                commands.append(f"1 0 0 1 {margin_x} {y} Tm ({safe}) Tj".encode("latin-1", "replace"))
                y -= line_height
            commands.append(b"ET")
            stream = b"\n".join(commands)
            content_id = add_object(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream")
            page_obj = (
                f"<< /Type /Page /Parent {pages_id_placeholder} 0 R /MediaBox [0 0 {page_width} {page_height}] ".encode("ascii")
                + f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>".encode("ascii")
            )
            page_ids.append(add_object(page_obj))

        kids = b" ".join(f"{page_id} 0 R".encode("ascii") for page_id in page_ids)
        pages_id = add_object(b"<< /Type /Pages /Kids [ " + kids + b" ] /Count " + str(len(page_ids)).encode("ascii") + b" >>")
        catalog_id = add_object(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("ascii"))

        output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for index, obj in enumerate(objects, start=1):
            offsets.append(len(output))
            output.extend(f"{index} 0 obj\n".encode("ascii"))
            output.extend(obj)
            output.extend(b"\nendobj\n")
        xref_pos = len(output)
        output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        output.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        output.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
        )
        return bytes(output)

    def _escape_pdf_text(self, value: str) -> str:
        cleaned = value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        return "".join(ch if 32 <= ord(ch) <= 126 else "?" for ch in cleaned)


