"""Trusted rehearsal host entry. Machine locations come from environment selectors."""

import json
import os
from pathlib import Path
import sys
import time
from hashlib import sha256

from unity_coder.adapters.unity.transport import BridgeTransport, local_http
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.workspaces import git
from unity_coder.core.storage import atomic_write
from trusted_overlay import TrustedOverlay


ROOTS = tuple("Assets/JJGame/monopoly/" + path for path in (
    "Runtime/Script/UI/LobbyRehearsal",
    "Runtime/Resource/monopoly/Scenes/LobbyRehearsal",
    "Runtime/Resource/monopoly/UI/Prefabs/LobbyRehearsal",
    "Runtime/Resource/monopoly/UI/Images/LobbyRehearsal",
    "Tests/Runtime/Script/LobbyRehearsal",
    "Editor/Script/LobbyRehearsal",
))


class OverlayHost:
    def __init__(self, *, architect_preparation: bool = False) -> None:
        self.host = Path(os.environ["UNITY_HOST"]).resolve(strict=True)
        self.state = Path(os.environ["LOBBY_RUN_ROOT"]).resolve(strict=True) / "trusted-state"
        self.port = int(os.environ.get("UNITY_BRIDGE_PORT", "49166"))
        self.overlay = TrustedOverlay(self.host, self.state / "host-overlay", ROOTS)
        self.lease = RunLease(self.host, "monopoly-game-lobby", "lobby-overlay-" + str(os.getpid()))
        self.transport = BridgeTransport(self.host, ports=(self.port,))
        self.architect_preparation = architect_preparation

    def restore_preparation_effects(self, operation: str) -> None:
        """Restore proven editor preparation effects. Production gates stay strict."""
        if not self.architect_preparation:
            raise ValueError("Editor-output restoration is restricted to Architect preparation")
        proof_path = self.state / "restoration-proof.json"
        if not proof_path.exists():
            return
        proof = json.loads(proof_path.read_bytes())
        recorded = json.loads((self.state / "preparation-drift.json").read_bytes())
        known = {row["path"]: row["actual"] for row in recorded["changed"]}
        baseline = self.overlay.read()["baseline"]
        restored = []
        for row in proof:
            path = row["path"]
            if not row["verified"] or row["sha256"] != baseline[path]:
                raise ValueError("Unverified editor restoration input")
            original = (self.state / "baseline-restoration-candidates" / path).read_bytes()
            if sha256(original).hexdigest() != baseline[path]:
                raise ValueError("Restoration copy changed")
            current = (self.host / path).read_bytes()
            identity = sha256(current).hexdigest()
            if identity == baseline[path]:
                continue
            if path.endswith("AssetReferenceDB.asset"):
                footer = original.rfind(b"  m_version:")
                if footer < 0 or not current.startswith(original[:footer]) or not current.endswith(original[footer:]):
                    raise ValueError("Generated cache changed beyond append-only references")
            elif identity != known[path]:
                raise ValueError("New shared-font or settings change requires explicit reconciliation: " + path)
            atomic_write(self.state, "preparation-effects/" + identity + ".bin", current)
            atomic_write(self.host, path, original)
            restored.append({"path": path, "observed_sha256": identity, "restored_sha256": baseline[path]})
        if restored:
            token = sha256((operation + json.dumps(restored, sort_keys=True)).encode()).hexdigest()
            atomic_write(self.state, "preparation-effects/" + token + ".json",
                         json.dumps({"operation": operation, "files": restored}).encode())

    def preflight(self) -> None:
        self.lease.assert_held()
        reply = local_http(self.port, "GET", "/", None, 5)
        if reply.get("status") != "ok" or Path(reply.get("projectPath", "")).resolve() != self.host:
            raise ValueError("Bridge project identity mismatch")
        if reply.get("isPlaying"):
            raise ValueError("Host must be idle in Edit Mode")
        response = local_http(self.port, "POST", "/execute", {"command": "FrameworkVerifyCapabilities"}, 5)
        capabilities = json.loads(response.get("data", "{}"))
        if (response.get("status") != "success" or capabilities.get("protocol") != 1
                or capabilities.get("command") != "FrameworkVerify"
                or not {"compile", "tests"} <= set(capabilities.get("modes", []))
                or not capabilities.get("ready") or capabilities.get("active_ticket")):
            raise ValueError("Verification host unavailable or busy")

    def verify(self, request, ladder, contract, source, patches, files, frozen_paths):
        self.preflight()
        if git(source, "rev-parse", "HEAD").decode().strip() != request.candidate_revision:
            raise ValueError("Verification revision differs from committed candidate")
        required = {link.test_id for link in contract.test_links}
        selected = set(request.test_selection)
        if not selected or not selected <= required or (request.full_suite and selected != required):
            raise ValueError("Test selection differs from declared lobby acceptance")
        self.overlay.assert_ready(request.candidate_revision)
        try:
            return ladder.verify(request, contract, source, patches, files, frozen_paths=frozen_paths)
        finally:
            self.overlay.assert_ready(request.candidate_revision)

    def materialize(self, source: Path, candidate: str) -> dict[str, bytes]:
        """Return new metadata for the coordinator to commit before verification."""
        self.preflight()
        if git(source, "rev-parse", "HEAD").decode().strip() != candidate:
            raise ValueError("Materialization requires the committed candidate")
        paths = git(source, "ls-tree", "-r", "--name-only", "-z", candidate).decode().split("\0")
        contents = {}
        for relative in filter(None, paths):
            target = "Assets/JJGame/monopoly/" + relative
            if not self.overlay.allowed(target):
                continue
            content = git(source, "show", candidate + ":" + relative)
            if (source / relative).read_bytes() != content:
                raise ValueError("Working candidate differs from committed bytes")
            contents[target] = content
        self.overlay.materialize(candidate, contents)
        # A successful HTTP enqueue is followed by main-thread readiness checks.
        reply = local_http(self.port, "POST", "/execute", {"command": "RefreshAssetDatabase"}, 5)
        if reply.get("status") == "error":
            raise ValueError("Unity rejected import refresh")
        deadline = time.monotonic() + 180
        stable = 0
        while time.monotonic() < deadline:
            time.sleep(1)
            try:
                self.preflight()
                stable += 1
                if stable == 3:
                    if self.architect_preparation:
                        self.restore_preparation_effects("import-" + candidate)
                    return self.overlay.capture_import(candidate)
            except (OSError, ValueError):
                stable = 0
        raise TimeoutError("Unity import did not settle; reconcile before retry")


def main() -> None:
    host = OverlayHost()
    host.lease.acquire(owner_alive=lambda _: True)
    try:
        host.preflight()
        if sys.argv[1:] == ["capture-baseline"]:
            identity = host.overlay.capture_baseline()
            print(json.dumps({"baseline_sha256": identity, "files": len(host.overlay.read()["baseline"])}))
        elif sys.argv[1:] == ["check-baseline"]:
            host.overlay.check(host.overlay.read())
            print("PASS dedicated-host baseline unchanged")
        else:
            raise ValueError("Use capture-baseline or check-baseline")
    finally:
        host.lease.release()


if __name__ == "__main__":
    main()
