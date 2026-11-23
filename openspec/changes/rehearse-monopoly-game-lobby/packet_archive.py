"""Reload an immutable canonical packet without interpreting source as framing."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from evidence_packet import Packet,Source,make_packet


def read_packet(path: Path,expected_sha256: str) -> Packet:
    raw=path.read_bytes()
    if sha256(raw).hexdigest()!=expected_sha256:raise ValueError('Archived canonical packet hash changed')
    try:
        end=raw.index(b'\n');wire=json.loads(raw[:end]);offset=end+1
        magic=b'EXACT CANONICAL SOURCE DATA\n'
        if wire['format_version']!=1 or raw[offset:offset+len(magic)]!=magic:raise ValueError
        offset+=len(magic);sources=[]
        for item in wire['sources']:
            count=item['utf8_bytes']
            if type(count) is not int or count<0:raise ValueError
            header=('BEGIN '+item['id']+' '+item['sha256']+' '+str(count)+'\n').encode()
            if raw[offset:offset+len(header)]!=header:raise ValueError
            offset+=len(header);body=raw[offset:offset+count];offset+=count
            footer=('\nEND '+item['id']+'\n').encode()
            if raw[offset:offset+len(footer)]!=footer or sha256(body).hexdigest()!=item['sha256']:raise ValueError
            offset+=len(footer)
            sources.append(Source(item['id'],item['path'],body.decode('utf-8'),item['kind'],tuple(item['dependencies'])))
        if offset!=len(raw):raise ValueError
        packet=make_packet(wire['identity'],tuple(sources),tuple(wire['required']),wire['mechanical'],
            wire['ownership'],tuple(wire['criteria']),wire['spec'])
        if packet.canonical_input.encode()!=raw:raise ValueError
        return packet
    except (ValueError,KeyError,TypeError,UnicodeError):
        raise ValueError('Archived packet framing, source bytes or manifest changed') from None
