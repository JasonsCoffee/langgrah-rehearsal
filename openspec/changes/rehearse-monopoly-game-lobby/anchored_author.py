"""Mechanically apply model-authored, hash-bound edits to unfrozen test source."""
from collections.abc import Mapping
from hashlib import sha256
import json
from unity_coder.core.model_workers import parse_patch

def parse_anchored_patch(text: str, owned: tuple[str,...], sources: Mapping[str,str]) -> tuple[dict[str,bytes],str]:
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('Duplicate transport key')
            result[key]=value
        return result
    data=json.loads(text,object_pairs_hook=unique)
    if not isinstance(data,dict) or set(data)!={'files','edits','reason'}:
        raise ValueError('Invalid anchored transport schema')
    if not isinstance(data['files'],dict) or not isinstance(data['edits'],list):
        raise ValueError('Invalid anchored files or edits')
    patch=dict(data['files'])
    if any(not isinstance(path,str) or path.endswith('.cs') for path in patch):
        raise ValueError('C# repairs must use hash-bound anchors, not full replacements')
    edited=set()
    for edit in data['edits']:
        if not isinstance(edit,dict) or set(edit)!={'path','base_sha256','replacements'}:
            raise ValueError('Invalid anchored edit')
        path=edit['path']
        if (not isinstance(path,str) or path not in owned or path not in sources
            or path in edited or path in patch or not path.endswith('.cs')):
            raise ValueError('Edit source is absent, repeated, or unowned')
        source=sources[path]
        if sha256(source.encode()).hexdigest()!=edit['base_sha256']:
            raise ValueError('Anchored source identity changed')
        replacements=edit['replacements']
        if not isinstance(replacements,list) or not replacements:raise ValueError('Missing delegated replacements')
        ranges=[]
        for replacement in replacements:
            if (not isinstance(replacement,dict) or set(replacement)!={'old','new'}
                or not all(isinstance(replacement[k],str) for k in ('old','new'))):
                raise ValueError('Invalid replacement')
            old,new=replacement['old'],replacement['new']
            if not old or old==new or source.count(old)!=1:raise ValueError('Anchor is absent, ambiguous or unchanged')
            start=source.index(old);end=start+len(old)
            if any(start<other_end and other_start<end for other_start,other_end,_ in ranges):
                raise ValueError('Delegated replacements overlap')
            ranges.append((start,end,new))
        value=source
        for start,end,new in sorted(ranges,reverse=True):value=value[:start]+new+value[end:]
        patch[path]=value;edited.add(path)
    return parse_patch(json.dumps({'files':patch,'reason':data['reason']}),owned)
