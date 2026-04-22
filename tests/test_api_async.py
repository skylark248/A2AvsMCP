"""Async FastAPI integration tests — exercises ASGI app in-process via httpx."""
from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from a2a_vs_mcp.web import app


async def test_api_mcp_mode_end_to_end_async() -> None:
    """Full request path for MCP mode through the FastAPI ASGI app without a real server."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/run",
            json={"scenario": "setup_error", "mode": "mcp", "runtime": "mock"},
        )
    assert response.status_code == 200
    payload = response.json()
    mcp_result = next(r for r in payload["results"] if r["mode"] == "mcp")
    assert mcp_result["final_answer"], "MCP mode returned empty final_answer"
    assert mcp_result["metrics"]["tool_calls"] > 0, "MCP mode made zero tool calls"


async def test_api_fake_llm_runtime_returns_canned_answer() -> None:
    """FakeReasoningEngine produces a non-empty answer for all modes without OPENAI_API_KEY."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/run",
            json={"scenario": "order_status", "mode": "all", "runtime": "fake_llm"},
        )
    assert response.status_code == 200
    payload = response.json()
    for result in payload["results"]:
        assert result["final_answer"], f"Empty final_answer for mode={result['mode']}"
