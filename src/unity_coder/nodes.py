"""Node implementations.

Each node is a small function over state. The graph wiring lives in graph.py.
Instances are bound into a ``Nodes`` object so the model and Architect are
injected rather than imported, which keeps the whole thing testable.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from langgraph.types import Send

from . import prompts
from .architect import ArchitectProvider
from .contract import assert_owned, load_contract, validate_units
from .models import ModelClient, extract_json
from .state import UnitContract, UnitPayload, WorkflowState
from .unity import run_verify

STATE_DIR = ".unity_coder"
MAX_CONTEXT_CHARS = 60_000


def _expand_pattern(root: Path, pattern: str) -> list[Path]:
    cleaned = pattern.replace("\\", "/")
    if any(ch in cleaned for ch in "*?[]"):
        return sorted(p for p in root.glob(cleaned) if p.is_file())[:12]
    candidate = root / cleaned
    return [candidate] if candidate.is_file() else []


def _read(path: Path, limit: int) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


class Nodes:
    def __init__(
        self,
        model: ModelClient,
        architect: ArchitectProvider,
        unity_exe: str | None = None,
        commit: bool = False,
    ):
        self.model = model
        self.architect = architect
        self.unity_exe = unity_exe
        self.commit = commit

    # ---- ingress -------------------------------------------------------

    def load_contract(self, state: WorkflowState) -> dict:
        units = load_contract(state["contract_path"])
        return {
            "units": units,
            "cycle": state.get("cycle") or 1,
            "phase": "coding",
            "log": [f"loaded {len(units)} unit(s) from {state['contract_path']}"],
        }

    def partition(self, state: WorkflowState) -> dict:
        """Validate ownership before any token is spent."""
        validate_units(list(state["units"]))
        ids = ", ".join(u["id"] for u in state["units"])
        return {"log": [f"partition ok: {ids}"]}

    def dispatch(self, state: WorkflowState) -> list[Send]:
        conventions = self._conventions(state["project_root"])
        return [
            Send(
                "code_unit",
                UnitPayload(
                    unit=unit,
                    project_root=state["project_root"],
                    cycle=state["cycle"],
                    conventions=conventions,
                ),
            )
            for unit in state["units"]
        ]

    # ---- coding --------------------------------------------------------

    def code_unit(self, payload: UnitPayload) -> dict:
        unit = payload["unit"]
        context = self._unit_context(unit, Path(payload["project_root"]))
        user = prompts.coder_prompt(payload) + f"\nExisting file contents:\n{context}\n"
        if len(user) > MAX_CONTEXT_CHARS:
            user = user[:MAX_CONTEXT_CHARS] + "\n\n[context truncated]\n"

        try:
            raw = self.model.complete(prompts.CODER_SYSTEM, user)
            data = extract_json(raw)
            patches = data.get("patches", []) or []
            ok = bool(data.get("ok", True))
            notes = str(data.get("notes", ""))
        except Exception as exc:  # noqa: BLE001 - a bad unit must not kill the cycle
            patches, ok, notes = [], False, f"coder failed: {exc}"

        for patch in patches:
            patch.setdefault("action", "update")

        return {
            "results": [
                {"unit_id": unit["id"], "cycle": payload["cycle"], "ok": ok, "notes": notes, "patches": patches}
            ],
            "log": [f"unit {unit['id']}: {len(patches)} patch(es), ok={ok}"],
        }

    # ---- integration ---------------------------------------------------

    def integrate(self, state: WorkflowState) -> dict:
        """Fan-in. Writes patches, refusing anything outside declared ownership."""
        root = Path(state["project_root"]).resolve()
        by_id = {u["id"]: u for u in state["units"]}
        current = [r for r in state["results"] if r["cycle"] == state["cycle"]]

        written: list[str] = []
        rejected: list[str] = []

        for result in current:
            unit = by_id.get(result["unit_id"])
            if unit is None:
                rejected.append(f"{result['unit_id']}: unit vanished from contract")
                continue
            if not result.get("ok", True):
                rejected.append(f"{result['unit_id']}: coder reported not-ok ({result.get('notes', '')})")
                continue
            for patch in result["patches"]:
                try:
                    assert_owned(unit, patch["path"])
                except Exception as exc:  # noqa: BLE001
                    rejected.append(str(exc))
                    continue
                target = (root / patch["path"].replace("\\", "/")).resolve()
                if not str(target).startswith(str(root)):
                    rejected.append(f"{patch['path']}: escapes project root")
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(patch["content"], encoding="utf-8")
                written.append(patch["path"])

        if self.commit and written:
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=False, capture_output=True)
            subprocess.run(
                ["git", "-C", str(root), "commit", "-m", f"agent: cycle {state['cycle']} ({len(written)} files)"],
                check=False,
                capture_output=True,
            )

        log = [f"integrate: wrote {len(written)} file(s)"]
        if rejected:
            log.append(f"integrate: rejected {len(rejected)} change(s)")
            log.extend(f"  rejected: {r}" for r in rejected[:10])
        return {"log": log}

    # ---- verification --------------------------------------------------

    def verify(self, state: WorkflowState) -> dict:
        result = run_verify(state["project_root"], self.unity_exe)
        summary = (
            f"verify: compiled={result['compiled']} tests_failed={result['tests_failed']} "
            f"({result['duration_s']}s)"
        )
        return {"verify": result, "phase": "verifying", "log": [summary]}

    # ---- judgement -----------------------------------------------------

    def judge(self, state: WorkflowState) -> dict:
        current = [r for r in state["results"] if r["cycle"] == state["cycle"]]
        user = prompts.judge_prompt(state["units"], state["verify"], current)
        try:
            data = extract_json(self.model.complete(prompts.JUDGE_SYSTEM, user))
        except Exception as exc:  # noqa: BLE001
            data = {
                "passed": False,
                "summary": f"judge failed to produce parseable output: {exc}",
                "failed_units": [],
                "learned_constraints": [],
            }

        dossier = {
            "cycle": state["cycle"],
            "passed": bool(data.get("passed")),
            "summary": str(data.get("summary", "")),
            "failed_units": data.get("failed_units", []) or [],
            "learned_constraints": data.get("learned_constraints", []) or [],
            "budget_remaining": max(0, state.get("max_cycles", 3) - state["cycle"]),
        }
        return {"dossier": dossier, "log": [f"judge: passed={dossier['passed']} — {dossier['summary']}"]}

    def route_after_judge(self, state: WorkflowState) -> str:
        if state["dossier"]["passed"]:
            return "handoff"
        if state["cycle"] >= state.get("max_cycles", 3):
            return "abandon"
        return "rework"

    # ---- rework / exit -------------------------------------------------

    def rework(self, state: WorkflowState) -> dict:
        revised = self.architect.request_rework(
            state["dossier"], state["units"], state["project_root"]
        )
        return {
            "units": revised,
            "cycle": state["cycle"] + 1,
            "dossier": {},
            "phase": "coding",
            "log": [f"rework: architect returned {len(revised)} unit(s) for cycle {state['cycle'] + 1}"],
        }

    def handoff(self, state: WorkflowState) -> dict:
        root = Path(state["project_root"])
        state_dir = root / STATE_DIR
        state_dir.mkdir(exist_ok=True)
        current = [r for r in state["results"] if r["cycle"] == state["cycle"]]
        files = sorted({p["path"] for r in current for p in r["patches"]})
        constraints = "\n".join(
            f"- {c}" for c in state["dossier"].get("learned_constraints", [])
        ) or "- (none)"

        body = [
            f"# Agent cycle {state['cycle']} — passed",
            "",
            f"{state['dossier'].get('summary', '')}",
            "",
            "## Files produced",
            *(f"- `{f}`" for f in files),
            "",
            "## Verification",
            f"- compiled: {state['verify']['compiled']}",
            f"- tests failed: {state['verify']['tests_failed']} / {state['verify']['tests_total']}",
            f"- duration: {state['verify']['duration_s']}s",
            "",
            "## Constraints learned (persist these for the next contract)",
            constraints,
            "",
            "Review the working tree and commit manually unless you ran with --commit.",
        ]
        (state_dir / "handoff.md").write_text("\n".join(body), encoding="utf-8")
        return {"phase": "done", "log": [f"handoff written to {state_dir / 'handoff.md'}"]}

    def abandon(self, state: WorkflowState) -> dict:
        root = Path(state["project_root"])
        state_dir = root / STATE_DIR
        state_dir.mkdir(exist_ok=True)
        (state_dir / "rework_dossier.json").write_text(
            json.dumps(state["dossier"], indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return {
            "phase": "abandoned",
            "log": [
                f"abandoned after {state['cycle']} cycle(s); dossier written to "
                f"{state_dir / 'rework_dossier.json'}"
            ],
        }

    # ---- context helpers -----------------------------------------------

    def _conventions(self, project_root: str) -> str:
        root = Path(project_root)
        for name in ("AGENTS.md", "CLAUDE.md", "README.md"):
            candidate = root / name
            if candidate.is_file():
                return _read(candidate, 6000)
        return ""

    def _unit_context(self, unit: UnitContract, root: Path) -> str:
        chunks: list[str] = []
        budget = 40_000
        for pattern in unit["owns"]:
            for path in _expand_pattern(root, pattern):
                rel = path.relative_to(root).as_posix()
                text = _read(path, min(12_000, budget))
                if not text:
                    continue
                budget -= len(text)
                chunks.append(f"\n--- {rel} ---\n{text}")
                if budget <= 0:
                    return "".join(chunks)
        return "".join(chunks) or "(no existing files under owned paths)"
