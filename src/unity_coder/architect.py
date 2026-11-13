"""The Architect boundary.

LangGraph owns deterministic orchestration; the Architect owns planning. Keeping
the boundary here means you can run the loop unattended later without touching
graph code.

Three implementations ship:

- ``ManualArchitect``    writes a rework request, waits for you to drop in a
                         response. Works today with CodeBuddy + OpenSpec.
- ``SubprocessArchitect`` placeholder for a headless CodeBuddy/OpenSpec run.
- ``StaticArchitect``    replays units unchanged; useful for graph smoke tests.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Protocol

from .contract import validate_units
from .state import UnitContract

STATE_DIR = ".unity_coder"


class ArchitectProvider(Protocol):
    def request_rework(
        self, dossier: dict, units: list[UnitContract], project_root: str
    ) -> list[UnitContract]: ...


def _state_dir(project_root: str) -> Path:
    path = Path(project_root) / STATE_DIR
    path.mkdir(exist_ok=True)
    return path


class ManualArchitect:
    """Human-in-the-loop Architect.

    Drops ``rework_request.json`` in ``<project>/.unity_coder/`` and polls for
    ``rework_response.json``. The dossier plus the original spec is everything
    CodeBuddy needs; nothing else crosses the boundary.
    """

    def __init__(self, timeout_s: int = 1800, poll_s: int = 5):
        self.timeout_s = timeout_s
        self.poll_s = poll_s

    def request_rework(
        self, dossier: dict, units: list[UnitContract], project_root: str
    ) -> list[UnitContract]:
        state = _state_dir(project_root)
        request = state / "rework_request.json"
        response = state / "rework_response.json"

        request.write_text(
            json.dumps({"dossier": dossier, "current_units": units}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        response.unlink(missing_ok=True)

        print(f"\n[architect] rework requested -> {request}")
        print("[architect] feed this dossier to CodeBuddy, then write the revised units to")
        print(f"[architect]   {response}")
        print("[architect] format: {\"units\": [ ...same shape as your contract... ]}")

        deadline = time.time() + self.timeout_s
        while time.time() < deadline:
            if response.exists():
                data = json.loads(response.read_text(encoding="utf-8"))
                revised = data.get("units", data)
                validate_units(revised)
                return revised  # type: ignore[return-value]
            time.sleep(self.poll_s)

        raise TimeoutError(
            f"no Architect response after {self.timeout_s}s. Rerun with a larger "
            "--architect-timeout, or the run is recoverable from the checkpoint."
        )


class SubprocessArchitect:
    """Placeholder for headless Architect invocation.

    Fill in once you confirm your local agent exposes a non-interactive mode.
    The contract is: read the request JSON on argv, write the response JSON.
    """

    def __init__(self, command: list[str]):
        self.command = command

    def request_rework(
        self, dossier: dict, units: list[UnitContract], project_root: str
    ) -> list[UnitContract]:
        raise NotImplementedError(
            "Headless Architect not wired yet. Use ManualArchitect (default) or "
            "implement request_rework() against your agent's CLI."
        )


class StaticArchitect:
    """Returns the units unchanged. For smoke-testing the graph only."""

    def request_rework(
        self, dossier: dict, units: list[UnitContract], project_root: str
    ) -> list[UnitContract]:
        return units
