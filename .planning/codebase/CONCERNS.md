# Concerns
_Last updated: 2026-04-21_

## Summary
The codebase is clean, well-structured, and intentionally scoped as an educational demo. Technical debt is minimal. The main concerns are hardcoded localhost URLs in default configs, the absence of coverage tooling, a missing CI pipeline, and a few transport-level gaps in tests. No secrets are committed; security posture is appropriate for a local demo tool.

## Technical Debt

| Severity | Location | Issue |
|----------|----------|-------|
| LOW | `src/a2a_vs_mcp/a2a/registry.py:9-11` | Hardcoded `127.0.0.1` port defaults for remote A2A agents — fine for dev, fragile if ports change |
| LOW | `src/a2a_vs_mcp/remote_registry.py:14-15` | Same pattern for remote MCP URLs — duplicates `.env.example` config |
| LOW | `src/a2a_vs_mcp/mcp/client.py:243,263,267,281` | Multiple hardcoded `127.0.0.1` references for subprocess-spawned MCP servers |
| LOW | `pyproject.toml` | No `[tool.pytest.ini_options]` section — test discovery relies on pytest defaults |
| LOW | `pyproject.toml` | `ruff.lint` selects only `E9, F` (errors + pyflakes) — style rules (isort, naming) not enforced |

## Security Concerns

| Severity | Location | Issue |
|----------|----------|-------|
| LOW | `src/a2a_vs_mcp/web.py:75` | `LOCAL_REMOTE_HOSTS` allowlist for remote URL validation — logic is correct but should be reviewed if project expands to cloud deployment |
| LOW | `src/a2a_vs_mcp/web.py:153` | Credentials in remote URL rejected, but error message may leak URL structure in logs |
| INFO | `.env.example` | `A2A_VS_MCP_ALLOW_EXTERNAL_REMOTE_URLS` defaults off — good; enabling it in untrusted environments would allow SSRF-like remote agent calls |
| INFO | `src/a2a_vs_mcp/reasoning.py:145` | `OPENAI_API_KEY` read from env — correct pattern, no hardcoded key found |

No secrets committed. No SQL injection surface (no raw SQL). No XSS surface (React with JSX, no `dangerouslySetInnerHTML` detected).

## Performance Concerns

| Severity | Location | Issue |
|----------|----------|-------|
| LOW | `src/a2a_vs_mcp/mcp/client.py` | MCP subprocess transport spawns child processes per run — acceptable for demo scale, would not work under concurrent load |
| LOW | Trace system | Trace files written as JSON per run — no pagination or truncation for very large runs |
| INFO | Frontend | No bundle analysis config; MUI + recharts are large dependencies but acceptable for a demo |

## Missing / Incomplete

| Item | Notes |
|------|-------|
| CI/CD pipeline | No `.github/workflows/`, no `Makefile` CI target, no `tox.ini` — tests must be run manually |
| Coverage reporting | No `pytest-cov`, no `c8`/`istanbul` configured |
| `reasoning.py` test coverage | OpenAI integration path has no mock and no test |
| Remote A2A transport tests | Only `local` transport tested; `remote` transport (requires `a2a-sdk[http-server]`) untested |
| MCP transport variant tests | `stdio` and `streamable-http` transports untested; only `in_process` exercised |
| Docker / deployment docs | `README.md` covers local dev; no containerization or cloud deployment guidance |

## Recommendations

1. **Add CI** — a simple GitHub Actions workflow running `pytest tests/` and `cd frontend && npm test` would catch regressions on every push.
2. **Enable coverage** — add `pytest-cov` and a `coverage.xml` artifact; add `c8` to the frontend Vitest run. Even rough numbers help prioritize test gaps.
3. **Consolidate hardcoded localhost URLs** — extract the `127.0.0.1:91xx` registry defaults into a single config constant or a `_defaults.py` so they're maintained in one place.
4. **Expand ruff ruleset** — add `I` (isort) and `N` (naming conventions) to `ruff.lint.select` to enforce import ordering and naming consistency automatically.
5. **Add a mock for `reasoning.py`** — a simple `FakeReasoningEngine` that returns canned responses would allow the LLM integration path to be covered without an API key.
