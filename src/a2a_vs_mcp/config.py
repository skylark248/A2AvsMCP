from __future__ import annotations

from dataclasses import asdict, dataclass
import os


@dataclass
class ProfileConfig:
    name: str
    runtime: str
    mcp_transport: str
    save_report: bool
    export_logs: bool
    description: str
    a2a_transport: str = "local"

    def to_dict(self) -> dict[str, str | bool]:
        return asdict(self)


PROFILES: dict[str, ProfileConfig] = {
    "dev": ProfileConfig(
        name="dev",
        runtime="mock",
        mcp_transport="in_process",
        a2a_transport="local",
        save_report=False,
        export_logs=False,
        description="Fast local development defaults with minimal persistence.",
    ),
    "demo": ProfileConfig(
        name="demo",
        runtime="mock",
        mcp_transport="http",
        a2a_transport="local",
        save_report=True,
        export_logs=True,
        description="Presentation-friendly defaults with realistic transport and persisted outputs.",
    ),
    "llm": ProfileConfig(
        name="llm",
        runtime="llm",
        mcp_transport="http",
        a2a_transport="local",
        save_report=True,
        export_logs=True,
        description="Live LLM profile with persisted reports and structured external logs.",
    ),
}


def default_profile_name() -> str:
    return os.getenv("A2A_VS_MCP_PROFILE", "dev")


def resolve_profile(
    profile_name: str | None = None,
    *,
    runtime: str | None = None,
    mcp_transport: str | None = None,
    a2a_transport: str | None = None,
    save_report: bool | None = None,
    export_logs: bool | None = None,
) -> ProfileConfig:
    active_name = profile_name or default_profile_name()
    base = PROFILES.get(active_name, PROFILES["dev"])
    return ProfileConfig(
        name=base.name,
        runtime=runtime or base.runtime,
        mcp_transport=mcp_transport or base.mcp_transport,
        a2a_transport=a2a_transport or os.getenv("A2A_TRANSPORT") or base.a2a_transport,
        save_report=base.save_report if save_report is None else save_report,
        export_logs=base.export_logs if export_logs is None else export_logs,
        description=base.description,
    )
