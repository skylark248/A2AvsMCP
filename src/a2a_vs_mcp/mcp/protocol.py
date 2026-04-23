from __future__ import annotations

from typing import Any
import json
import sys


def read_message() -> dict[str, Any] | None:
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line)



def write_message(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()
