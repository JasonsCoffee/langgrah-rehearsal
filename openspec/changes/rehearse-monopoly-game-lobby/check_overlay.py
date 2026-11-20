"""Offline destructive probes confined to a temporary fake Unity host."""

from pathlib import Path
from tempfile import TemporaryDirectory

from trusted_overlay import TrustedOverlay


def rejects(action) -> None:
    try:
        action()
    except ValueError:
        return
    raise AssertionError("Unsafe operation was accepted")


with TemporaryDirectory() as temporary:
    root = Path(temporary)
    host = root / "host"
    for name in ("Assets", "Packages", "ProjectSettings"):
        (host / name).mkdir(parents=True)
    original = host / "Assets/existing.txt"
    original.write_bytes(b"user content")
    entry = host / TrustedOverlay.ENTRY_PATH
    entry.parent.mkdir(parents=True)
    entry.write_bytes(b"original entry")
    prefix = "Assets/JJGame/monopoly/Runtime/Script/LobbyRehearsal"
    overlay = TrustedOverlay(host, root / "state", (prefix,))
    overlay.capture_baseline()
    rejects(overlay.capture_baseline)
    rejects(lambda: overlay.materialize("bad", {"Assets/existing.txt": b"overwrite"}))
    rejects(lambda: overlay.materialize("bad", {prefix + "/../escape.cs": b"escape"}))
    files = {prefix + "/Shell.cs": b"shell"}
    overlay.materialize("one", files)
    overlay.assert_ready("one")
    original.write_bytes(b"drift")
    rejects(lambda: overlay.assert_ready("one"))
    original.write_bytes(b"user content")
    metadata = host / (prefix + "/Shell.cs.meta")
    metadata.write_bytes(b"guid: stable")
    rejects(lambda: overlay.assert_ready("one"))
    imported = overlay.capture_import("one")
    rejects(lambda: overlay.materialize("one", files | imported))
    overlay.materialize("two", files | imported)
    overlay.assert_ready("two")
    source = host / (prefix + "/Shell.cs")
    source.write_bytes(b"candidate drift")
    rejects(lambda: overlay.assert_ready("two"))
    source.write_bytes(b"shell")
    metadata.write_bytes(b"metadata drift")
    rejects(lambda: overlay.capture_import("two"))
    metadata.write_bytes(b"guid: stable")
    rejects(lambda: overlay.materialize("three", files))
    rejects(lambda: overlay.materialize("two", files | {metadata.relative_to(host).as_posix(): b"changed"}))
    rejects(lambda: overlay.register_entry("wrong hash"))
    from trusted_overlay import digest
    overlay.register_entry(digest(b"original entry"))
    replaced = files | imported | {TrustedOverlay.ENTRY_PATH: b"replacement entry"}
    overlay.materialize("entry-three", replaced)
    overlay.assert_ready("entry-three")
    assert overlay.read()["baseline"][TrustedOverlay.ENTRY_PATH] == digest(b"original entry")
    rejects(lambda: overlay.materialize("entry-four", replaced | {"Assets/existing.txt": b"forbidden"}))
    prepared_path = prefix + "/Preview.mat"
    (host / prepared_path).write_bytes(b"original material")
    rejects(lambda: overlay.capture_preparation("entry-three", (prefix + "/Other.mat",)))
    prepared = overlay.capture_preparation("entry-three", (prepared_path,))
    rejects(lambda: overlay.assert_ready("entry-three"))
    replaced |= prepared
    overlay.materialize("prepared-four", replaced)
    overlay.assert_ready("prepared-four")
    (host / (prefix + "/unexpected.txt")).write_bytes(b"import mutation")
    rejects(lambda: overlay.capture_import("prepared-four"))
    assert original.read_bytes() == b"user content"
    print("PASS baseline drift, scope escape, additive overlay, import freeze, stale identity, deletion, exact entry exception and enumerated asset preparation")
