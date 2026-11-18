"""Architect exports observed Unity preparation, never inferred import success."""
from dataclasses import replace
from hashlib import sha256

import pytest

from unity_coder.adapters.unity.preparation import PreparedBaseline, freeze_prepared
from unity_coder.core.contracts import Interface
from unity_coder.core.presentation import ArtistAsset


@pytest.fixture
def prepared(tmp_path):
    files = {'UI/Demo.prefab': b'prefab', 'UI/Demo.prefab.meta': b'guid: prefab',
             'UI/Demo.unity': b'scene', 'UI/Demo.unity.meta': b'guid: scene',
             'UI/art_placeHolder.png': b'art', 'UI/art_placeHolder.png.meta': b'guid: art',
             'design.md': b'brief', 'View.cs': b'class View { public int count; }'}
    for name, data in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    baseline = PreparedBaseline('v1', tuple((p, sha256(b).hexdigest()) for p,b in files.items()),
        ('UI/Demo.unity', 'UI/Demo.prefab'), (), (),
        (('UI/Demo.unity','scene'), ('UI/Demo.prefab','prefab'), ('UI/art_placeHolder.png','art')),
        (('View.count','Root/Counter'),), ('Root', 'Root/Counter'), True)
    asset = ArtistAsset('art','UI/art_placeHolder.png','expedition illustration','design.md',
        (640,320),False,('normal',),('Sprite Single; sRGB; no mipmaps',),
        ('UI/Demo.prefab',),('Preserve dimensions, GUID and references',))
    return tmp_path, baseline, asset


def freeze(prepared):
    root, baseline, asset = prepared
    return freeze_prepared(root, baseline, interfaces=(Interface('View.count','public int count'),),
        mutations=(('View.count','text'),), assets=(asset,), reused=(),
        instructions='Open UI/Demo.unity; review layout before coding.')


def test_preparation_exports_identical_protected_baseline(prepared, tmp_path):
    manifest = freeze(prepared)
    manifest.distribute(prepared[0], tmp_path / 'unit')
    manifest.validate(tmp_path / 'unit')
    assert manifest.entries == prepared[1].entries
    assert manifest.assets[0].id == 'art'


@pytest.mark.parametrize('field,value', [('launchable',False), ('missing_scripts',('Missing',)),
    ('unresolved_bindings',('View.count',)), ('bindings',()), ('hierarchy',('Root',)),
    ('asset_ids',()), ('entries',())])
def test_unusable_preparation_cannot_freeze(prepared, field, value):
    root, baseline, asset = prepared
    with pytest.raises(ValueError):
        freeze((root, replace(baseline, **{field:value}), asset))


def test_changed_bytes_cannot_be_adopted_as_new_evidence(prepared):
    (prepared[0] / 'UI/Demo.prefab').write_bytes(b'changed after editor inspection')
    with pytest.raises(ValueError):
        freeze(prepared)


def test_paths_cannot_escape_preparation_root(prepared):
    root, baseline, asset = prepared
    with pytest.raises(ValueError):
        freeze((root, replace(baseline, files=baseline.files + (('../foreign', '0'*64),)), asset))


def test_duplicate_bindings_cannot_hide_conflicting_targets(prepared):
    root, baseline, asset = prepared
    with pytest.raises(ValueError):
        freeze((root, replace(baseline, bindings=baseline.bindings * 2), asset))
