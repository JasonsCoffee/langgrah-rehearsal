"""Immutable evidence manifests; this module never reads arbitrary files."""
from __future__ import annotations
from dataclasses import asdict,dataclass
from hashlib import sha256
import json
from pathlib import PurePosixPath


def canonical(value: object) -> str:
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))


@dataclass(frozen=True)
class Source:
    id: str
    path: str
    content: str
    kind: str
    dependencies: tuple[str,...]=()

    @property
    def sha256(self) -> str:
        return sha256(self.content.encode()).hexdigest()


@dataclass(frozen=True)
class Packet:
    identity: dict
    sources: tuple[Source,...]
    required: tuple[str,...]
    mechanical: dict
    ownership: dict[str,str]
    criteria: tuple[str,...]
    spec: str
    canonical_input: str
    canonical_sha256: str


def make_packet(identity: dict,sources: tuple[Source,...],required: tuple[str,...],mechanical: dict,
                ownership: dict[str,str],criteria: tuple[str,...],spec: str) -> Packet:
    if not {'run','contract','candidate','unit','stage','policy'}<=set(identity):raise ValueError('Full packet identity required')
    ids=set()
    for source in sources:
        if (not source.id or source.id in ids or source.kind in ('coder_notes','secret','reasoning','authorship')
            or '\\' in source.path or ':' in source.path or PurePosixPath(source.path).is_absolute()
            or '..' in PurePosixPath(source.path).parts):raise ValueError('Invalid, duplicate or forbidden evidence source')
        ids.add(source.id)
    if not set(required)<=ids:raise ValueError('Missing required canonical source')
    # Deep copies detach mutable caller dictionaries from the immutable serialized identity.
    frozen_identity=json.loads(canonical(identity));frozen_mechanical=json.loads(canonical(mechanical))
    wire={'identity':frozen_identity,'criteria':list(criteria),'spec':spec,'ownership':dict(ownership),
        'mechanical':frozen_mechanical,'sources':[{k:v for k,v in asdict(s).items() if k!='content'}|
            {'sha256':s.sha256,'utf8_bytes':len(s.content.encode())} for s in sources],
        'required':list(required),'format_version':1}
    text=canonical(wire)+'\nEXACT CANONICAL SOURCE DATA\n'+''.join(
        'BEGIN '+s.id+' '+s.sha256+' '+str(len(s.content.encode()))+'\n'+s.content+'\nEND '+s.id+'\n' for s in sources)
    return Packet(frozen_identity,tuple(sources),tuple(required),frozen_mechanical,dict(ownership),tuple(criteria),
        spec,text,sha256(text.encode()).hexdigest())


def assert_packet(packet: Packet) -> None:
    recreated=make_packet(packet.identity,packet.sources,packet.required,packet.mechanical,packet.ownership,packet.criteria,packet.spec)
    if recreated.canonical_sha256!=packet.canonical_sha256 or recreated.canonical_input!=packet.canonical_input:
        raise ValueError('Canonical packet was mutated')
