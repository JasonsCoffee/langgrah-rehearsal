"""Frozen checks: omit exact identity edits without relaxing strict parsing."""
from hashlib import sha256
import json
import pytest
from anchored_author import parse_anchored_patch


def payload(source,replacements):
    return json.dumps({'files':{},'edits':[{'path':'T.cs','base_sha256':sha256(source.encode()).hexdigest(),
        'replacements':replacements}],'reason':'model-authored'})


def test_identity_removal_preserves_actual_model_text_and_strict_parser():
    from noop_transport import normalize_identity_edits
    source='class C { int A() { return 1; } int B() { return 3; } }'
    raw=payload(source,[{'old':'return 1;','new':'return 2;'}, {'old':'return 3;','new':'return 3;'}])
    with pytest.raises(ValueError):parse_anchored_patch(raw,('T.cs',),{'T.cs':source})
    normalized,removed=normalize_identity_edits(raw,{'T.cs':source})
    files,reason=parse_anchored_patch(normalized,('T.cs',),{'T.cs':source})
    assert files['T.cs'].decode()==source.replace('return 1;','return 2;')
    assert removed==[{'edit':0,'replacement':1}]
    assert json.loads(normalized)['edits'][0]['replacements']==[{'old':'return 1;','new':'return 2;'}]


def test_identity_only_response_cannot_be_admitted():
    from noop_transport import normalize_identity_edits
    source='class C {}'
    with pytest.raises(ValueError):normalize_identity_edits(payload(source,[{'old':source,'new':source}]),{'T.cs':source})


@pytest.mark.parametrize('kind',['ambiguous','overlap','absent','hash'])
def test_other_invalid_edits_are_never_repaired(kind):
    from noop_transport import normalize_identity_edits
    source='class C { int A; int B; }'
    edits=[{'old':'int A;','new':'int A = 1;'}]
    if kind=='ambiguous':edits.append({'old':'int','new':'int'})
    if kind=='overlap':edits.append({'old':source,'new':source})
    if kind=='absent':edits.append({'old':'missing','new':'missing'})
    raw=payload(source,edits)
    if kind=='hash':raw=raw.replace(sha256(source.encode()).hexdigest(),'0'*64)
    with pytest.raises(ValueError):normalize_identity_edits(raw,{'T.cs':source})
