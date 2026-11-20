"""Trusted context requirements and exact supplied-text provenance."""
from collections.abc import Mapping
from hashlib import sha256
import re

from .ai_models import ModelError
from .ownership import portable_path


def context_policy(requirements: Mapping[str, Mapping[str, str]],
                   unit_ids: set[str]) -> dict[str, dict[str, str]]:
    """Copy and validate host requirements before composing paid workers."""
    result: dict[str, dict[str, str]] = {}
    for unit, paths in requirements.items():
        if unit not in unit_ids:
            raise ValueError('Context policy names an unknown active unit')
        result[unit] = {}
        for path, digest in paths.items():
            portable_path(path)
            if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
                raise ValueError('Context requirement needs an exact SHA256')
            result[unit][path] = digest
    return result


def context_manifest(files: Mapping[str, str], required: Mapping[str, str],
                     contract_sha256: str) -> dict[str, object]:
    """Validate the supplied prompt text; do not read or infer extra files."""
    hashes: dict[str, str] = {}
    for path, text in files.items():
        portable_path(path)
        if not isinstance(text, str):
            raise ModelError('Prompt context must contain text')
        hashes[path] = sha256(text.encode('utf-8')).hexdigest()
    if any(hashes.get(path) != digest for path, digest in required.items()):
        raise ModelError('Required prompt context is missing or changed')
    return {'contract_sha256': contract_sha256, 'files': hashes}
