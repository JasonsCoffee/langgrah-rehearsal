"""Trusted Architect-only baseline import, compile and asset construction."""

from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time

from overlay_host import OverlayHost
from unity_coder.adapters.unity.transport import local_http
from unity_coder.core.storage import atomic_write
from unity_coder.core.verification import VerificationRequest
from unity_coder.core.workspaces import git


def publish(root: Path, name: str, payload: dict) -> None:
    atomic_write(root, name + ".json", json.dumps(payload, ensure_ascii=False, indent=2).encode())


def reconcile_import(host: OverlayHost, source: Path) -> str:
    for attempt in range(3):
        candidate = git(source, "rev-parse", "HEAD").decode().strip()
        metadata = host.materialize(source, candidate)
        if not metadata:
            host.overlay.assert_ready(candidate)
            return candidate
        for path, content in metadata.items():
            relative = path.removeprefix("Assets/JJGame/monopoly/")
            target = source / relative
            if target.exists() and target.read_bytes() != content:
                raise ValueError("Import metadata differs from coordinator source")
            atomic_write(source, relative, content)
            git(source, "add", "--", relative)
        git(source, "-c", "user.name=Lobby Rehearsal", "-c", "user.email=rehearsal@example.invalid",
            "commit", "-m", "Reconcile Unity preparation metadata")
    raise ValueError("Import metadata did not stabilize in three rounds")


def compile_shells(host: OverlayHost, source: Path) -> None:
    candidate = reconcile_import(host, source)
    identity = sha256(b"architect-preparation-only:" + candidate.encode()).hexdigest()
    request = VerificationRequest("lobby-preparation-compile-" + candidate[:12], "monopoly-game-lobby",
                                  1, identity, candidate, identity, identity, identity, (), False)
    host.overlay.assert_ready(candidate)
    try:
        evidence = host.transport.compile(request)
    finally:
        host.overlay.assert_ready(candidate)
    publish(host.state, "prepared-shell-compile", {"stage": "architect-preparation",
            "execution_contract_frozen": False, "candidate": candidate, "evidence": asdict(evidence)})
    if evidence.compilation is None or not evidence.compilation.passed or evidence.compilation.operational_error:
        raise ValueError("Preparation compile failed; inspect prepared-shell-compile.json")
    print("PASS preparation compile", candidate, flush=True)


def prepared_inventory() -> set[str]:
    resource = "Assets/JJGame/monopoly/Runtime/Resource/monopoly/"
    prefabs = resource + "UI/Prefabs/LobbyRehearsal/"
    art = prefabs + "Art/"
    screens = ("Lobby", "Appearance", "Friends", "Shop", "Records", "Chat", "Recharge", "Settings", "Handoff", "PlatformHome")
    paths = {prefabs + screen + "View_placeHolder.prefab" for screen in screens}
    materials = ["Stone", "Brick", "Navy", "Glass", "Road", "Brass", "Rubber"]
    materials += ["Outfit" + str(index) for index in range(6)]
    materials += ["Paint" + str(index) for index in range(4)]
    paths.update(art + name + "_placeHolder.mat" for name in materials)
    paths.update(art + name + "_placeHolder.asset" for name in ("LobbyFont", "LobbyConfiguration"))
    paths.add(art + "CharacterActions_placeHolder.controller")
    paths.update(art + name + "_placeHolder.anim" for name in ("Idle", "Wave", "Celebrate"))
    for kind, count in (("Skin", 6), ("Vehicle", 4)):
        for index in range(count):
            name = kind + str(index) + "_placeHolder"
            paths.add(art + name + ".prefab")
            paths.add(resource + "UI/Images/LobbyRehearsal/" + name + ".png")
    paths.add(resource + "Scenes/LobbyRehearsal/LobbyStreet_placeHolder.unity")
    return paths


def prepare_assets(host: OverlayHost, source: Path) -> None:
    candidate = git(source, "rev-parse", "HEAD").decode().strip()
    receipt = json.loads((host.state / "prepared-shell-compile.json").read_bytes())
    if receipt["candidate"] != candidate or not receipt["evidence"]["compilation"]["passed"]:
        raise ValueError("Asset preparation requires the compiled exact shell baseline")
    host.overlay.assert_ready(candidate)
    intent = host.state / "asset-preparation-intent.json"
    if intent.exists():
        raise ValueError("Prior preparation intent requires receipt reconciliation; no implicit replay")
    assets = prepared_inventory()
    publish(host.state, "asset-preparation-intent", {"candidate": candidate, "assets": sorted(assets)})
    report_root = host.state / "presentation"
    try:
        reply = local_http(host.port, "POST", "/execute", {"command": "PrepareMonopolyLobby", "reportRoot": str(report_root)}, 10)
    except OSError:
        # A timed-out HTTP response does not establish failure of the editor effect.
        reply = {"status": "uncertain", "reason": "Response unavailable; reconcile durable report"}
    publish(host.state, "asset-preparation-submission", reply)
    report_path = report_root / "presentation-preparation.json"
    deadline = time.monotonic() + 240
    while not report_path.exists() and time.monotonic() < deadline:
        if reply.get("status") == "error":
            raise ValueError(str(reply.get("message", "Asset preparation rejected")))
        time.sleep(1)
        if reply.get("taskId"):
            status = local_http(host.port, "GET", "/task/" + str(reply["taskId"]), None, 5)
            publish(host.state, "asset-preparation-task", status)
            if status.get("status") == "error":
                raise ValueError("Asset preparation task failed; inspect its durable receipt")
    if not report_path.exists():
        raise TimeoutError("Asset preparation receipt missing; reconcile intent before retry")
    reconcile_assets(host, source)


def reconcile_assets(host: OverlayHost, source: Path) -> None:
    intent = json.loads((host.state / "asset-preparation-intent.json").read_bytes())
    candidate = git(source, "rev-parse", "HEAD").decode().strip()
    if intent["candidate"] != candidate:
        raise ValueError("Preparation reconciliation requires the original source candidate")
    assets = prepared_inventory()
    if set(intent["assets"]) != assets:
        raise ValueError("Preparation intent inventory changed")
    report_path = host.state / "presentation/presentation-preparation.json"
    report = json.loads(report_path.read_bytes())
    if set(report["createdAssets"]) != assets:
        raise ValueError("Editor asset report differs from the trusted construction inventory")
    declared = assets | {path + ".meta" for path in assets}
    resource = "Assets/JJGame/monopoly/Runtime/Resource/monopoly/"
    declared |= {resource + path for path in ("UI/Prefabs/LobbyRehearsal.meta",
                 "UI/Prefabs/LobbyRehearsal/Art.meta", "Scenes/LobbyRehearsal.meta")}
    host.restore_preparation_effects("asset-preparation-" + candidate)
    captured = host.overlay.capture_preparation(candidate, tuple(sorted(declared)))
    for path, content in captured.items():
        relative = path.removeprefix("Assets/JJGame/monopoly/")
        atomic_write(source, relative, content)
        git(source, "add", "--", relative)
    git(source, "-c", "user.name=Lobby Rehearsal", "-c", "user.email=rehearsal@example.invalid",
        "commit", "-m", "Prepare original Western lobby scene and view prefabs")
    final = reconcile_import(host, source)
    publish(host.state, "asset-preparation-complete", {"candidate": final, "prepared_files": len(captured), "report": report})
    print("PASS imported 3D presentation baseline", final, flush=True)


def main() -> None:
    source = Path(os.environ.get("LOBBY_PREPARATION_SOURCE", str(Path(os.environ["LOBBY_RUN_ROOT"]).resolve() / "module"))).resolve()
    host = OverlayHost(architect_preparation=True)
    host.lease.acquire(owner_alive=lambda _: True)
    try:
        host.preflight()
        if sys.argv[1:] == ["compile"]:
            compile_shells(host, source)
        elif sys.argv[1:] == ["prepare-assets"]:
            prepare_assets(host, source)
        elif sys.argv[1:] == ["reconcile-assets"]:
            reconcile_assets(host, source)
        else:
            raise ValueError("Use compile or prepare-assets")
    finally:
        host.lease.release()


if __name__ == "__main__":
    main()
