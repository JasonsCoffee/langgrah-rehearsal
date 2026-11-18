"""Immutable presentation inputs."""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path

from .contracts import ArtifactRef, Interface
from .ownership import confined_path
from .storage import atomic_write

@dataclass(frozen=True)
class ArtistAsset:
    id: str
    path: str
    purpose: str
    reference: str
    dimensions: tuple[int, int]
    transparency: bool
    variants: tuple[str, ...]
    import_requirements: tuple[str, ...]
    usage: tuple[str, ...]
    acceptance: tuple[str, ...]

@dataclass(frozen=True)
class Presentation:
    revision: str
    files: tuple[ArtifactRef, ...]
    interfaces: tuple[Interface, ...]
    entries: tuple[str, ...]
    mutations: tuple[tuple[str, str], ...]
    assets: tuple[ArtistAsset, ...]
    reused: tuple[str, ...]
    instructions: str

    @property
    def identity(self) -> str:
        return sha256(json.dumps(asdict(self), sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def validate(self, root: Path) -> None:
        paths = {ref.path for ref in self.files}
        if not self.revision or not self.instructions.strip() or not self.entries or len(paths) != len(self.files):
            raise ValueError("Incomplete presentation manifest")
        if not set((*self.entries, *self.reused)).issubset(paths):
            raise ValueError("Entry/reused content is not protected")
        for ref in self.files:
            if sha256(confined_path(root, ref.path).read_bytes()).hexdigest() != ref.sha256:
                raise ValueError(f"Frozen presentation changed: {ref.path}")
        symbols = {interface.symbol for interface in self.interfaces}
        if any(binding not in symbols or not action.strip() for binding, action in self.mutations):
            raise ValueError("Undeclared runtime binding")
        ids: set[str] = set()
        for asset in self.assets:
            if not asset.id or asset.id in ids or not asset.purpose.strip():
                raise ValueError("Invalid asset identity or purpose")
            ids.add(asset.id)
            if asset.path not in paths or asset.reference not in paths or not set(asset.usage).issubset(paths):
                raise ValueError("Asset/reference/usage is not protected")
            if len(asset.dimensions) != 2 or any(type(n) is not int or n <= 0 for n in asset.dimensions):
                raise ValueError("Positive asset dimensions required")
            if type(asset.transparency) is not bool:
                raise ValueError("Transparency requirement missing")
            for requirement in (asset.variants, asset.import_requirements, asset.usage, asset.acceptance):
                if not requirement or any(not value.strip() for value in requirement):
                    raise ValueError("Incomplete artist delivery requirements")

    def distribute(self, source: Path, target: Path) -> None:
        self.validate(source)
        contents = {ref.path: confined_path(source, ref.path).read_bytes() for ref in self.files}
        for path, content in contents.items():
            destination = confined_path(target, path)
            if destination.exists() and destination.read_bytes() != content:
                raise ValueError("Baseline distribution would overwrite different content")
        for path, content in contents.items():
            atomic_write(target, path, content)
        self.validate(target)

    def allow_mutation(self, binding: str, operation: str) -> None:
        if (binding, operation) not in self.mutations:
            raise ValueError("Runtime mutation needs a revised contract")

    def replacement(self, asset: str, *, separate_change: bool, references_preserved: bool,
                    compatible: bool, reviewed: bool) -> None:
        """Validate supplied replacement evidence; never edits a frozen baseline."""
        if asset not in {entry.id for entry in self.assets}:
            raise ValueError("Unknown replaceable asset")
        if not all((separate_change, references_preserved, compatible, reviewed)):
            raise ValueError("Replacement requires a compatible separate reviewed change")
