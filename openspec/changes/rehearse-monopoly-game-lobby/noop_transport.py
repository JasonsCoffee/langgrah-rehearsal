"""Omit only disjoint exact identity replacements; strict parsing still follows."""
from hashlib import sha256
import json


def normalize_identity_edits(text: str, sources: dict[str,str]) -> tuple[str,list[dict]]:
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('Duplicate transport key')
            result[key]=value
        return result
    data=json.loads(text,object_pairs_hook=unique)
    if not isinstance(data,dict) or set(data)!={'files','edits','reason'} or not isinstance(data['edits'],list):
        raise ValueError('Invalid anchored transport schema')
    kept=[];removed=[];seen=set()
    for ei,edit in enumerate(data['edits']):
        if not isinstance(edit,dict) or set(edit)!={'path','base_sha256','replacements'}:raise ValueError('Invalid anchored edit')
        path=edit['path']
        if not isinstance(path,str) or path not in sources or path in seen:raise ValueError('Absent or duplicate source')
        seen.add(path);source=sources[path]
        if sha256(source.encode()).hexdigest()!=edit['base_sha256']:raise ValueError('Anchored source identity changed')
        if not isinstance(edit['replacements'],list) or not edit['replacements']:raise ValueError('Missing replacements')
        ranges=[];replacements=[]
        for ri,replacement in enumerate(edit['replacements']):
            if (not isinstance(replacement,dict) or set(replacement)!={'old','new'}
                or not all(isinstance(replacement[k],str) for k in ('old','new'))):raise ValueError('Invalid replacement')
            old,new=replacement['old'],replacement['new']
            if not old or source.count(old)!=1:raise ValueError('Anchor is absent or ambiguous')
            start=source.index(old);end=start+len(old)
            if any(start<b and a<end for a,b in ranges):raise ValueError('Original replacements overlap')
            ranges.append((start,end))
            if old==new:removed.append({'edit':ei,'replacement':ri})
            else:replacements.append(replacement)
        if replacements:kept.append(edit|{'replacements':replacements})
    if not kept:raise ValueError('Identity-only response cannot constitute a C# repair')
    if not removed:return text,[]
    return json.dumps(data|{'edits':kept},ensure_ascii=False),removed
