"""Tuanjie serialized GUIDs need explicit trusted editor mapping."""
from dataclasses import replace
from hashlib import sha256

import pytest

from unity_coder.adapters.unity.preparation import PreparedBaseline, freeze_prepared
from unity_coder.adapters.unity.presentation import ImportReport, validate_unity


def test_encoded_identity_requires_observed_serialized_mapping(tmp_path):
    (tmp_path/'Demo.unity').write_bytes(b'scene')
    (tmp_path/'Demo.unity.meta').write_bytes(b'guid: encoded/identity=\n')
    files = tuple((p.name,sha256(p.read_bytes()).hexdigest()) for p in tmp_path.iterdir())
    args = dict(interfaces=(),mutations=(),assets=(),reused=(),instructions='Open Demo.unity')
    observed = PreparedBaseline('v1',files,('Demo.unity',),(),(),
        (('Demo.unity','a'*32),),(),('.',),True,
        serialized_asset_ids=(('Demo.unity','encoded/identity='),))
    manifest = freeze_prepared(tmp_path,observed,**args)
    report = ImportReport(manifest.identity,True,(),(),manifest.entries,observed.asset_ids,
        serialized_asset_ids=observed.serialized_asset_ids)
    assert not validate_unity(manifest,tmp_path,{},report,placeholder_suffix='_placeHolder')
    with pytest.raises(ValueError):
        freeze_prepared(tmp_path,replace(observed,serialized_asset_ids=()),**args)
    assert validate_unity(manifest,tmp_path,{},replace(report,serialized_asset_ids=()),placeholder_suffix='_placeHolder')
    with pytest.raises(ValueError):
        freeze_prepared(tmp_path,replace(observed,serialized_asset_ids=(('Demo.unity','stale'),)),**args)
    with pytest.raises(ValueError):
        freeze_prepared(tmp_path,replace(observed,asset_ids=(('Demo.unity','not-a-guid'),)),**args)
