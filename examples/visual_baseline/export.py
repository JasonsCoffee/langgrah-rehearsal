"""Export observed, validated presentation bytes into an external module snapshot."""
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path

from unity_coder.adapters.unity.preparation import PreparedBaseline, freeze_prepared
from unity_coder.adapters.unity.presentation import ImportReport, validate_unity
from unity_coder.core.contracts import Interface

from unity_coder.core.presentation import ArtistAsset


def main() -> None:
    version=int(os.environ.get('VISUAL_BASELINE_VERSION','1'))
    if version not in (1,2): raise ValueError('Unsupported demo baseline version')
    host = Path(os.environ['UNITY_HOST']).resolve()
    game = host/'Assets/JJGame/monopoly'
    destination = Path(os.environ['VISUAL_BASELINE_ROOT']).resolve()
    if destination == host or host in destination.parents or destination == game:
        raise ValueError('Preparation checkout must be outside Unity imports')
    report_name='editor-report.json' if version==1 else 'editor-report.v2.json'
    raw = json.loads((host/'.agent/visual-baseline'/report_name).read_text())
    observed = PreparedBaseline(raw['revision'], tuple(map(tuple, raw['files'])), tuple(raw['entries']),
        tuple(raw['missing_scripts']), tuple(raw['unresolved_bindings']), tuple(map(tuple,raw['asset_ids'])),
        tuple(map(tuple,raw['bindings'])), tuple(raw['hierarchy']), raw['launchable'],
        tuple(map(tuple,raw['serialized_asset_ids'])))
    resource = 'Runtime/Resource/monopoly/'
    prefab = resource+'UI/Prefabs/FrameworkVisualDemo/ExpeditionBriefing.prefab'
    symbol = 'FrameworkVisualDemo.ExpeditionPreviewShell.'
    interfaces = tuple(Interface(symbol+name, kind+' '+name) for name,kind in (
        ('confirmButton','Button'),('resetButton','Button'),('statusText','Text'),('heroImage','Image')))
    artist = ArtistAsset('expedition-landscape', resource+'UI/Images/FrameworkVisualDemo/expedition_placeHolder.png',
        'Northern Ridge geometric landscape', 'Editor/ArtSource~/FrameworkVisualDemo/design.md', (768,480), False,
        ('normal',), ('Sprite Single; sRGB; no mipmaps; uncompressed; centered pivot; 100 PPU',), (prefab,),
        ('Preserve GUID, dimensions, crop, references and import settings; separate reviewed change',))
    manifest = freeze_prepared(game, observed, interfaces=interfaces,
        mutations=((symbol+'statusText','text'),(symbol+'statusText','color')), assets=(artist,), reused=(),
        instructions='Open the VisualBaseline scene in the dedicated host. Select portrait Game view, enter Play Mode, '
        'review layout, click Preview ready state then Reset preview. No game bootstrap or gameplay is attached. '
        'Approval is pending and must name this manifest identity.')
    scripts = {ref.path:(game/ref.path).read_bytes() for ref in manifest.files if ref.path.endswith('.cs')}
    errors = validate_unity(manifest, game, scripts, ImportReport(manifest.identity, observed.launchable,
        observed.missing_scripts, observed.unresolved_bindings, observed.entries, observed.asset_ids, observed.serialized_asset_ids),
        placeholder_suffix='_placeHolder')
    if errors:
        raise ValueError(str(errors))
    manifest.distribute(game, destination)
    manifest.validate(destination)
    output = destination/'specs/visual-baseline'
    output.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(asdict(manifest), indent=2).encode()
    for name, content in [(f'presentation.v{version}.json',payload), ('editor-report.json',json.dumps(raw,indent=2).encode())]:
        target = output/name
        if target.exists() and target.read_bytes()!=content:
            raise ValueError('Existing exported baseline differs; choose a new preparation revision')
        target.write_bytes(content)
    evidence = Path('openspec/changes/archive/2026-11-18-formalize-unity-feature-delivery/live-evidence') / (
        'visual-baseline' if version==1 else 'visual-review/baseline-v2')
    evidence.mkdir(parents=True,exist_ok=True)
    (evidence/f'presentation.v{version}.json').write_bytes(payload)
    (evidence/'editor-report.json').write_text(json.dumps(raw,indent=2))
    for stage in (('red','green','compile') if version==1 else ()):
        result = json.loads((host/f'.agent/visual-baseline/{stage}.json').read_text())
        # Keep selection/results; omit unrelated discovery inventory.
        if result['tests'] is not None:
            result['tests'].pop('discovered',None)
        (evidence/f'{stage}.json').write_text(json.dumps(result,indent=2))
    review = {'manifest_identity':manifest.identity, 'presentation_sha256':sha256(payload).hexdigest(),
        'decision':'pending', 'baseline_revision':manifest.revision, 'source':'isolated synthetic design',
        'protected_file_count':len(manifest.files), 'existing_game_tests_executed':False,
        'manual_preview':'Recorded separately by the reviewer; never inferred by export',
        'automated_playmode_acceptance':False}
    (evidence/'review.json').write_text(json.dumps(review,indent=2))
    print(json.dumps(review,indent=2))


if __name__ == '__main__':
    main()
