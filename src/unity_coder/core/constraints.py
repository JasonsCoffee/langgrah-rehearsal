"""Accepted-only managed constraints."""
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Protocol, TypedDict, cast

START = b'<!-- unity-coder:constraints:start -->'
END = b'<!-- unity-coder:constraints:end -->'


class ReviewState(Protocol):
    def state(self) -> dict[str, object]: ...


class Provenance(TypedDict):
    confirmed: int
    criterion: str
    evidence_ref: str
    candidate_revision: str


class ConstraintRecord(TypedDict):
    key: str
    statement: str
    confirmed: int
    provenance: list[Provenance]

@dataclass(frozen=True)
class LearnedConstraint:
    statement: str
    confirmed: int
    criterion: str
    evidence_ref: str

def _key(statement: str) -> str:
    return sha256(' '.join(statement.split()).casefold().encode()).hexdigest()


def _split(content: bytes) -> tuple[bytes, bytes, bytes | None]:
    if START not in content and END not in content:
        return content, b'', None
    if content.count(START) != 1 or content.count(END) != 1:
        raise ValueError('Ambiguous managed constraint markers')
    start, end = content.index(START), content.index(END)
    if end < start:
        raise ValueError('Invalid managed constraint marker order')
    return content[:start], content[end+len(END):], content[start+len(START):end]


def read_constraints(content: bytes) -> tuple[list[ConstraintRecord], list[ConstraintRecord]]:
    """Read only our bounded managed block; reject corruption rather than replace it."""
    _, _, payload = _split(content)
    if payload is None:
        return [], []
    try:
        data = json.loads(payload)
        if set(data) != {'format_version', 'active', 'archive'} or data['format_version'] != 1:
            raise ValueError('Unsupported managed constraints format')
        active, archive = data['active'], data['archive']
        if not isinstance(active, list) or not isinstance(archive, list) or len(active) > 40:
            raise ValueError('Invalid managed constraint collections')
        seen = set()
        for entry in active + archive:
            if (not isinstance(entry['statement'], str) or not entry['statement'].strip()
                or entry['key'] != _key(entry['statement']) or entry['key'] in seen
                or type(entry['confirmed']) is not int or entry['confirmed'] < 1
                or not isinstance(entry['provenance'], list) or not entry['provenance']):
                raise ValueError('Invalid managed constraint provenance')
            for proof in entry['provenance']:
                if (type(proof['confirmed']) is not int or not 1 <= proof['confirmed'] <= entry['confirmed']
                    or any(not isinstance(proof[k], str) or not proof[k].strip()
                           for k in ('criterion', 'evidence_ref', 'candidate_revision'))):
                    raise ValueError('Invalid confirmation evidence')
            seen.add(entry['key'])
        return cast(list[ConstraintRecord], active), cast(list[ConstraintRecord], archive)
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError('Malformed managed constraints') from error


def accepted_constraints(review: ReviewState, *, candidate_revision: str,
                         contract_version: int, original: bytes,
                         entries: tuple[LearnedConstraint, ...]) -> bytes:
    """Prepare metadata only; the trusted coordinator commits the approved parent.

    This function has no filesystem effects. ReviewGate is the production source
    of authenticated approval; neither a coder nor its notes may supply that state.
    """
    state = review.state()
    request = cast(dict[str, object], state.get('request', {}))
    files = cast(dict[str, str], state.get('files', {}))
    expected = files.get('AGENTS.md')
    if (state.get('decision') != 'accept' or not state.get('reviewer')
        or request.get('candidate_revision') != candidate_revision
        or request.get('contract_version') != contract_version
        or state.get('contract_version') != contract_version
        or (expected != sha256(original).hexdigest() if expected is not None else bool(original))):
        raise ValueError('Constraints require exact-candidate human approval and unchanged original')
    active, archive = read_constraints(original)
    if not entries:
        return original
    records = {entry['key']: entry for entry in active + archive}
    for entry in entries:
        if (not entry.statement.strip() or not entry.criterion.strip()
            or type(entry.confirmed) is not int or entry.confirmed != contract_version
            or entry.evidence_ref not in state.get('evidence_refs', ())
            or any(marker in entry.statement.encode() for marker in (START, END))):
            raise ValueError('Constraint lacks approved confirmation provenance')
        key = _key(entry.statement)
        proof: Provenance = dict(confirmed=entry.confirmed, criterion=entry.criterion,
                                 evidence_ref=entry.evidence_ref, candidate_revision=candidate_revision)
        if key not in records:
            records[key] = dict(key=key, statement=' '.join(entry.statement.split()),
                                confirmed=entry.confirmed, provenance=[])
        record = records[key]
        if record['confirmed'] > contract_version:
            raise ValueError('Constraint confirmation cannot move backwards')
        record['confirmed'] = entry.confirmed
        if proof not in record['provenance']:
            record['provenance'].append(proof)
    ordered = sorted(records.values(), key=lambda value: (-value['confirmed'], value['key']))
    payload = json.dumps(dict(format_version=1, active=ordered[:40], archive=ordered[40:]),
                         sort_keys=True, indent=2).encode()
    prefix, suffix, old = _split(original)
    if old is None and prefix and not prefix.endswith(b'\n'):
        prefix += b'\n'
    return prefix + START + b'\n' + payload + b'\n' + END + suffix
