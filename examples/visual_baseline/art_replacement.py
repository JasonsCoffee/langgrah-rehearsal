"""Separate synthetic artist deliveries; never a coding-cycle operation."""
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

import live
from unity_coder.core.contracts import ArtifactRef, Interface
from unity_coder.core.presentation import ArtistAsset, Presentation
from unity_coder.adapters.unity.preparation import PreparedBaseline, freeze_prepared
from unity_coder.adapters.unity.presentation import ImportReport, validate_unity

ROOT = Path(os.environ['ART_REPLACEMENT_ROOT']).resolve()
EVIDENCE = live.SOURCE/'openspec/changes/formalize-unity-feature-delivery/live-evidence/art-replacement'
OLD = live.SOURCE/'openspec/changes/formalize-unity-feature-delivery/live-evidence/visual-review/baseline-v2/presentation.v2.json'
LAKE = os.environ.get('ART_REPLACEMENT_REVISION') == 'lake'
if LAKE:
    OLD = EVIDENCE/'presentation.json'
    EVIDENCE = EVIDENCE/'lake'


def save(name: str, value: object) -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE/(name+'.json')).write_text(json.dumps(value,indent=2),encoding='utf-8')


def original() -> Presentation:
    raw=json.loads(OLD.read_text())
    return Presentation(raw['revision'],tuple(ArtifactRef(**v) for v in raw['files']),
        tuple(Interface(**v) for v in raw['interfaces']),tuple(raw['entries']),
        tuple(map(tuple,raw['mutations'])),tuple(ArtistAsset(**v) for v in raw['assets']),
        tuple(raw['reused']),raw['instructions'])


def command(operation: str) -> dict[str, object]:
    reply=live.command('FrameworkArtReplacement',operation=operation)
    if reply.get('status')!='success':raise ValueError(str(reply))
    return json.loads(str(reply['data']))


def main() -> None:
    if ROOT==live.HOST or live.HOST in ROOT.parents:
        raise ValueError('Art snapshot must be outside Unity imports')
    action=sys.argv[1]
    old=original()
    if action=='install':
        old.validate(live.GAME)
        live.copy_new(live.SOURCE/'unity/Editor/FrameworkArtReplacement.cs',
            'Editor/Script/FrameworkVisualPreparation/FrameworkArtReplacement.cs')
        live.refresh()
    elif action=='prepare':
        old.validate(live.GAME)
        save('deliveries',command('prepare-lake' if LAKE else 'prepare'))
    elif action=='incompatible':
        old.validate(live.GAME)
        result=command(action)
        assert not result['compatible'] and not result['applied'] and result['unchanged']
        old.validate(live.GAME)
        save(action,result)
    elif action=='compatible':
        old.validate(live.GAME)
        result=command('lake' if LAKE else action)
        assert result['compatible'] and result['references_preserved']
        save(action,result)
    elif action=='export':
        reply=live.command('FrameworkPrepareVisual',operation='inspect')
        if reply.get('status')!='success':raise ValueError(str(reply))
        raw=json.loads(str(reply['data']))
        raw['revision']='art-compatible-lake-1' if LAKE else 'art-compatible-1'
        observed=PreparedBaseline(raw['revision'],tuple(map(tuple,raw['files'])),tuple(raw['entries']),
            tuple(raw['missing_scripts']),tuple(raw['unresolved_bindings']),tuple(map(tuple,raw['asset_ids'])),
            tuple(map(tuple,raw['bindings'])),tuple(raw['hierarchy']),raw['launchable'],
            tuple(map(tuple,raw['serialized_asset_ids'])))
        manifest=freeze_prepared(live.GAME,observed,interfaces=old.interfaces,mutations=old.mutations,
            assets=old.assets,reused=old.reused,instructions=old.instructions)
        changed=[ref.path for ref in manifest.files if ref not in old.files]
        assert changed==[old.assets[0].path],changed
        scripts={ref.path:(live.GAME/ref.path).read_bytes() for ref in manifest.files if ref.path.endswith('.cs')}
        errors=validate_unity(manifest,live.GAME,scripts,ImportReport(manifest.identity,observed.launchable,
            observed.missing_scripts,observed.unresolved_bindings,observed.entries,observed.asset_ids,
            observed.serialized_asset_ids),placeholder_suffix='_placeHolder')
        if errors:raise ValueError(str(errors))
        guards=[]
        for key in ('separate_change','compatible','reviewed','references_preserved'):
            flags=dict(separate_change=True,compatible=True,reviewed=True,references_preserved=True)
            flags[key]=False
            try:old.replacement(old.assets[0].id,**flags)
            except ValueError:guards.append(key)
            else:raise AssertionError('Replacement guard failed: '+key)
        try:old.validate(live.GAME)
        except ValueError:guards.append('old_manifest_rejects_new_bytes')
        else:raise AssertionError('Old manifest accepted replacement')
        manifest.distribute(live.GAME,ROOT/'baseline')
        save('presentation',asdict(manifest));save('editor-report',raw)
        save('manifest-checks',dict(identity=manifest.identity,changed_files=changed,guards=guards,
            protected_files=len(manifest.files),review_decision='pending'))
        (EVIDENCE/'replacement-preview.png').write_bytes((live.GAME/old.assets[0].path).read_bytes())
    elif action=='verify':
        os.environ['VISUAL_REVIEW_ROOT']=str(ROOT)
        import review_rehearsal as review
        review.RUN='art-compatible-lake-1' if LAKE else 'art-compatible-1'
        review.REPO_EVIDENCE=EVIDENCE
        result=review.verify(1,'art-compatible',review.TESTS+(review.CORAL_TEST,))
        if result.status!='passed':raise ValueError('Replacement demo tests failed')
        save('candidate',dict(identity=review.identity(review.candidate_files()),decision='pending',
            separate_change=True,existing_game_tests_executed=False))
    elif action=='accept':
        # Trusted operator imports an actual chat reply; this is not an authenticator.
        receipt=json.loads((EVIDENCE/'human-review.json').read_text(encoding='utf-8-sig'))
        candidate=json.loads((EVIDENCE/'candidate.json').read_text())
        result=json.loads((EVIDENCE/'compatible.json').read_text())
        evidence=json.loads((EVIDENCE/'art-compatible.json').read_text())
        os.environ['VISUAL_REVIEW_ROOT']=str(ROOT)
        import review_rehearsal as review
        current=review.identity(review.candidate_files())
        if receipt.get('decision')!='accept' or receipt.get('candidate_revision')!=current or candidate['identity']!=current:
            raise ValueError('An explicit approval of the current candidate is required')
        if evidence['status']!='passed' or evidence['request']['candidate_revision']!=current:
            raise ValueError('Passing evidence does not name the current candidate')
        raw=json.loads((EVIDENCE/'presentation.json').read_text())
        for item in raw['files']:
            if sha256((live.GAME/item['path']).read_bytes()).hexdigest()!=item['sha256']:
                raise ValueError('Presentation changed after inspection')
        old.replacement(old.assets[0].id,separate_change=result['separate_change'],
            references_preserved=result['references_preserved'],compatible=result['compatible'],reviewed=True)
        save('acceptance',dict(candidate_revision=current,decision='accept',reviewer=receipt['reviewer'],
            human_receipt='human-review.json',verification='art-compatible.json',manifest='presentation.json',
            separate_change=True,references_preserved=True,existing_game_tests_executed=False))
    else:raise ValueError('Unknown action')


if __name__=='__main__':main()
