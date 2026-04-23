from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec


REMOTE_A2A_BINDING = "a2a-vs-mcp-demo-jsonrpc"
REMOTE_A2A_BINDING_VERSION = "1"
REMOTE_A2A_PROTOCOL_VERSION = "1.0"
OFFICIAL_A2A_SDK_PIN = "0.3.25"
OFFICIAL_A2A_SDK_SPEC_VERSION = "0.3"


@dataclass(frozen=True)
class A2ASDKStatus:
    available: bool
    package: str = "a2a-sdk"
    note: str = ""


def sdk_status() -> A2ASDKStatus:
    if find_spec("a2a") is None:
        return A2ASDKStatus(
            available=False,
            note=(
                f"Official a2a-sdk {OFFICIAL_A2A_SDK_PIN} is not installed. Remote A2A is using the "
                "versioned demo HTTP binding."
            ),
        )
    return A2ASDKStatus(
        available=True,
        note=(
            f"Official a2a-sdk import is available; the optional extra is pinned to {OFFICIAL_A2A_SDK_PIN}, "
            f"which implements A2A spec {OFFICIAL_A2A_SDK_SPEC_VERSION}. This project still routes "
            "through sdk_compat until SDK 1.0 support is stable enough for the public wire contract."
        ),
    )


def remote_binding_metadata() -> dict[str, str | bool]:
    status = sdk_status()
    return {
        "protocolVersion": REMOTE_A2A_PROTOCOL_VERSION,
        "binding": REMOTE_A2A_BINDING,
        "bindingVersion": REMOTE_A2A_BINDING_VERSION,
        "officialSdkAvailable": status.available,
        "officialSdkPinnedVersion": OFFICIAL_A2A_SDK_PIN,
        "officialSdkSpecVersion": OFFICIAL_A2A_SDK_SPEC_VERSION,
        "sdkNote": status.note,
    }
