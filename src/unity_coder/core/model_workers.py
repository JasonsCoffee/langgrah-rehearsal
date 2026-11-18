"""Validated model outputs; callers retain ownership and verification authority."""
import json
from .ownership import portable_path


def _object(text: str, fields: set[str]) -> dict[str, object]:
    def unique(pairs):
        result = {}
        for key,value in pairs:
            if key in result:
                raise ValueError('Duplicate model output key')
            result[key]=value
        return result
    try:
        result=json.loads(text,object_pairs_hook=unique)
        if not isinstance(result,dict) or set(result)!=fields:
            raise ValueError
        return result
    except (ValueError,TypeError):
        raise ValueError('Model output does not match required JSON schema') from None


def parse_patch(text: str, owned: tuple[str, ...]) -> tuple[dict[str, bytes], str]:
    result=_object(text,{'files','reason'})
    files,reason=result['files'],result['reason']
    if not isinstance(files,dict) or not isinstance(reason,str) or not reason.strip():
        raise ValueError('Patch requires full file contents and a reason')
    patch={}
    for path,content in files.items():
        if portable_path(path) not in owned or not isinstance(content,str):
            raise ValueError('Model patch contains unowned path or invalid content')
        patch[path]=content.encode()
    return patch,reason


def parse_judgement(text: str) -> tuple[str, str]:
    result=_object(text,{'defect_class','explanation'})
    classification,explanation=result['defect_class'],result['explanation']
    if classification not in ('implementation','contract') or not isinstance(explanation,str) or not explanation.strip():
        raise ValueError('Judge must classify a defect with an explanation')
    return classification,explanation
