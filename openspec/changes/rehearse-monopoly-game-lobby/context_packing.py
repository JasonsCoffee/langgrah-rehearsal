"""Lossless packing of exact source bytes with relationship-preserving references."""
from evidence_packet import Packet,assert_packet,canonical


def pack(packet: Packet,selected: dict[str,list[list[int]]] | None=None) -> str:
    assert_packet(packet)
    bodies={};refs=[];body_ids={}
    for source in packet.sources:
        if selected is not None and source.id not in selected:continue
        ranges=selected[source.id] if selected is not None else [[0,len(source.content.encode())]]
        raw=source.content.encode()
        chunks=[raw[start:end].decode('utf-8') for start,end in ranges]
        from hashlib import sha256
        content=''.join(chunks);key=sha256(content.encode()).hexdigest()
        identity=body_ids.setdefault(key,'b'+str(len(body_ids)));bodies[identity]=(key,content)
        refs.append({'id':source.id,'path':source.path,'source_sha256':source.sha256,
            'body':identity,'ranges':ranges,'kind':source.kind,'dependencies':list(source.dependencies)})
    return canonical({'format_version':2,'identity':packet.identity,'criteria':packet.criteria,'spec':packet.spec,
        'ownership':packet.ownership,'mechanical':packet.mechanical,
        'bodies':{name:{'sha256':digest,'bytes':len(value.encode())} for name,(digest,value) in bodies.items()},
        'sources':refs,'canonical_sha256':packet.canonical_sha256})+'\nEXACT SOURCE DATA\n'+''.join(
            'BEGIN '+name+' '+str(len(value.encode()))+'\n'+value+'\nEND '+name+'\n' for name,(_,value) in bodies.items())
