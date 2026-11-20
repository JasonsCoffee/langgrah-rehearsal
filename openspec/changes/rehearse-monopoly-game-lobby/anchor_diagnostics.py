"""Explain rejected anchors as data; never repair or apply delegated source."""
from hashlib import sha256
import json


def diagnose_anchors(reply: str, sources: dict[str,str]) -> list[dict]:
    try:data=json.loads(reply)
    except ValueError:return [{'kind':'invalid_json'}]
    if not isinstance(data,dict) or not isinstance(data.get('edits'),list):return [{'kind':'invalid_shape'}]
    result=[]
    for ei,edit in enumerate(data['edits']):
        if not isinstance(edit,dict) or edit.get('path') not in sources:continue
        source=sources[edit['path']]
        for ri,replacement in enumerate(edit.get('replacements',[])):
            if not isinstance(replacement,dict) or not isinstance(replacement.get('old'),str):continue
            old=replacement['old'];count=source.count(old) if old else 0
            if count!=1 or old==replacement.get('new'):
                result.append({'edit':ei,'replacement':ri,'path':edit['path'],
                    'base_hash_matches':sha256(source.encode()).hexdigest()==edit.get('base_sha256'),
                    'original_occurrences':count,
                    'normalized_occurrences':source.replace('\r\n','\n').count(old.replace('\r\n','\n')) if old else 0})
    return result
