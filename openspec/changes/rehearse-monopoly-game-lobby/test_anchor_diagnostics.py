"""Frozen diagnostics checks; this helper never applies or changes model edits."""
import json
from hashlib import sha256


def test_reports_exact_ambiguous_replacement_without_mutating_source():
    from anchor_diagnostics import diagnose_anchors
    source='Start();\nStart();\n';sources={'a.cs':source}
    reply=json.dumps({'edits':[{'path':'a.cs','base_sha256':sha256(source.encode()).hexdigest(),
        'replacements':[{'old':'Start();','new':'Next();'}]}]})
    result=diagnose_anchors(reply,sources)
    assert result==[{'edit':0,'replacement':0,'path':'a.cs','base_hash_matches':True,
        'original_occurrences':2,'normalized_occurrences':2}]
    assert sources=={'a.cs':source}


def test_distinguishes_line_endings_without_normalizing_applied_source():
    from anchor_diagnostics import diagnose_anchors
    source='A\r\nB';reply=json.dumps({'edits':[{'path':'a.cs','base_sha256':'wrong',
        'replacements':[{'old':'A\nB','new':'C'}]}]})
    result=diagnose_anchors(reply,{'a.cs':source})
    assert result[0]['original_occurrences']==0 and result[0]['normalized_occurrences']==1
    assert result[0]['base_hash_matches'] is False


def test_invalid_json_diagnostic_never_echoes_unparsed_text():
    from anchor_diagnostics import diagnose_anchors
    assert diagnose_anchors('secret-value',{})==[{'kind':'invalid_json'}]
