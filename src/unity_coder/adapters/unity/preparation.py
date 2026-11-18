"""Architect-side conversion of trusted editor observations to frozen inputs."""
from dataclasses import dataclass
from pathlib import Path
import re

from ...core.contracts import ArtifactRef, Interface
from ...core.presentation import ArtistAsset, Presentation
from ...core.ownership import confined_path
from .presentation import imported_identity_matches


@dataclass(frozen=True)
class PreparedBaseline:
    revision: str
    files: tuple[tuple[str, str], ...]
    entries: tuple[str, ...]
    missing_scripts: tuple[str, ...]
    unresolved_bindings: tuple[str, ...]
    asset_ids: tuple[tuple[str, str], ...]
    bindings: tuple[tuple[str, str], ...]
    hierarchy: tuple[str, ...]
    launchable: bool
    serialized_asset_ids: tuple[tuple[str, str], ...] = ()


def freeze_prepared(root: Path, observed: PreparedBaseline, *, interfaces: tuple[Interface, ...],
                    mutations: tuple[tuple[str, str], ...], assets: tuple[ArtistAsset, ...],
                    reused: tuple[str, ...], instructions: str) -> Presentation:
    if observed.launchable is not True or observed.missing_scripts or observed.unresolved_bindings:
        raise ValueError('Editor preparation is not launchable or has unresolved bindings')
    bindings = dict(observed.bindings)
    if len(bindings) != len(observed.bindings):
        raise ValueError('Duplicate serialized bindings')
    if any(interface.symbol not in bindings for interface in interfaces):
        raise ValueError('Required interface has no observed binding')
    if any(target not in observed.hierarchy for target in bindings.values()):
        raise ValueError('Binding target is absent from the observed hierarchy')
    manifest = Presentation(observed.revision,
        tuple(ArtifactRef(path, digest) for path, digest in observed.files), interfaces,
        observed.entries, mutations, assets, reused, instructions)
    manifest.validate(root)
    ids = dict(observed.asset_ids)
    serialized_ids = dict(observed.serialized_asset_ids)
    if len(serialized_ids) != len(observed.serialized_asset_ids) or not set(serialized_ids).issubset(ids):
        raise ValueError('Invalid serialized identity mapping')
    if len(ids) != len(observed.asset_ids) or len(set(ids.values())) != len(ids):
        raise ValueError('Duplicate imported asset identities')
    protected = {ref.path for ref in manifest.files}
    for path in (*manifest.entries, *(asset.path for asset in assets)):
        if path + '.meta' not in protected:
            raise ValueError('Missing protected import settings')
        metadata = confined_path(root, path + '.meta').read_text(encoding='utf-8')
        match = re.search(r'(?m)^guid:\s*(\S+)\s*$', metadata)
        if match is None or not imported_identity_matches(match.group(1), ids.get(path), serialized_ids.get(path)):
            raise ValueError('Imported identity differs from the protected asset')
    if any(not Path(asset.path).stem.endswith('_placeHolder') for asset in assets):
        raise ValueError('Placeholder violates target naming rule')
    return manifest
