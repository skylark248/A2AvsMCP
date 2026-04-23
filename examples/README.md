# Curated Example Outputs

These files are deterministic sample outputs for public readers who want to inspect the project without running it first.

- `setup_and_warranty_report.json`: four-mode report for the `setup_and_warranty` scenario
- `setup_and_warranty_a2a_trace.json`: A2A-style task lifecycle trace with Agent Cards, message/send payloads, status updates, and artifact updates
- `setup_and_warranty_hybrid_trace.json`: hybrid trace with both A2A-shaped task events and MCP tool calls
- `warranty_return_remote_a2a_bad_auth_trace.json`: hosted remote A2A failure trace showing registry endpoints, simulated auth failures, and remote failure reporting
- `warranty_return_remote_a2a_bad_auth_report.json`: matching single-mode report for the remote A2A bad-auth path

The examples are intentionally small and safe to commit. Runtime-generated artifacts remain ignored under `artifacts/`.

For a short presenter flow that uses the remote A2A bad-auth examples, see `../docs/05-remote-a2a-presentation.md`.
