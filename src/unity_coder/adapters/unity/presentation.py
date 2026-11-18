"""Unity-specific presentation reporting."""
from dataclasses import dataclass
from collections.abc import Mapping
from pathlib import Path
import re

from . import UnityAdapter
from ...core.evidence import Violation
from ...core.ownership import confined_path
from ...core.presentation import Presentation

@dataclass(frozen=True)
class ImportReport:
    identity: str
    launchable: bool
    missing_scripts: tuple[str, ...]
    unresolved_bindings: tuple[str, ...]
    loaded_entries: tuple[str, ...]
    asset_ids: tuple[tuple[str, str], ...]
    serialized_asset_ids: tuple[tuple[str, str], ...] = ()


def imported_identity_matches(raw: str, canonical: str | None, serialized: str | None) -> bool:
    """Encoded metadata requires a mapping observed by the trusted editor worker.

    The worker must check GUIDToAssetPath round-trip before supplying this mapping.
    Frozen metadata hashes still bind the observation to the actual bytes.
    """
    if serialized is None:
        return raw == canonical
    return raw == serialized and isinstance(canonical, str) and re.fullmatch(r'[a-f0-9]{32}', canonical) is not None

def validate_unity(manifest: Presentation, root: Path, scripts: Mapping[str, str | bytes],
                   report: ImportReport, *, placeholder_suffix: str) -> tuple[Violation, ...]:
    """Validate structural inputs plus evidence supplied by the trusted worker.

    This function does not fabricate editor evidence or establish live readiness.
    """
    errors: list[Violation] = []
    def reject(message: str, path: str = "") -> None:
        errors.append(Violation("presentation", path, "", message))
    try:
        manifest.validate(root)
    except (ValueError, OSError) as exc:
        reject(str(exc))
        return tuple(errors)
    adapter = UnityAdapter()
    errors.extend(adapter.parse_check(scripts))
    errors.extend(adapter.check_interfaces(scripts, manifest.interfaces))
    if report.identity != manifest.identity or not report.launchable:
        reject("Missing or stale launch evidence")
    if report.missing_scripts or report.unresolved_bindings:
        reject("Unresolved scripts or bindings")
    if not set(manifest.entries).issubset(report.loaded_entries):
        reject("Review entry was not loaded")
    protected = {ref.path for ref in manifest.files}
    ids = dict(report.asset_ids)
    serialized_ids = dict(report.serialized_asset_ids)
    seen_ids: set[str] = set()
    if len(ids) != len(report.asset_ids):
        reject("Duplicate imported identity entries")
    if len(serialized_ids) != len(report.serialized_asset_ids) or not set(serialized_ids).issubset(ids):
        reject("Invalid serialized identity mapping")
    for path in (*manifest.entries, *(asset.path for asset in manifest.assets)):
        sidecar = path + ".meta"
        if sidecar not in protected:
            reject("Missing protected asset metadata", path)
            continue
        match = re.search(r"(?m)^guid:\s*(\S+)\s*$", confined_path(root, sidecar).read_text())
        if match is None or not imported_identity_matches(match.group(1), ids.get(path), serialized_ids.get(path)):
            reject("Imported asset identity mismatch", path)
        elif ids[path] in seen_ids:
            reject("Duplicate asset identity", path)
        else:
            seen_ids.add(ids[path])
    for asset in manifest.assets:
        if not placeholder_suffix or not Path(asset.path).stem.endswith(placeholder_suffix):
            reject("Placeholder violates target naming rule", asset.path)
    return tuple(errors)
