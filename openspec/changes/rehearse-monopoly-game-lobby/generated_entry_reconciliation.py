"""Identify one observed lifecycle insertion; advance only to delegated source."""
from __future__ import annotations
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from typing import TYPE_CHECKING
from tree_sitter import Language, Parser
import tree_sitter_c_sharp
from unity_coder.core.evidence import Violation
from unity_coder.core.ownership import confined_path,portable_path
from unity_coder.core.storage import atomic_write,file_guard
from unity_coder.core.verification import VerificationRequest,VerificationResult
from unity_coder.core.workspaces import git
if TYPE_CHECKING:
    from overlay_host import OverlayHost

ENTRY='Assets/JJGame/monopoly/Runtime/Script/Monopoly.cs'
RELATIVE='Runtime/Script/Monopoly.cs'
OLD_CANDIDATE='d6304a1b906bb340eeedccb01c57dc1393d02fe3'
OLD_ENTRY_SHA='35a9f72e602f60d511d9b39da9f84d4104040298d83827028151692473ba2f00'
PROOF='recovery-authorizations/generated-entry-v68.json'


def generated_insertion(before: bytes,after: bytes) -> bytes:
    start=0
    while start<min(len(before),len(after)) and before[start]==after[start]:start+=1
    suffix=len(before)-start
    if suffix and after[-suffix:]!=before[start:]:raise ValueError('Not a single generated insertion')
    insertion=after[start:len(after)-suffix if suffix else len(after)]
    expected=b'#region GeneratedBreak\n        Context.Break();\n#endregion'
    if (len(after)<=len(before) or insertion.replace(b'\r',b'').strip()!=expected
        or not re.search(rb'public\s+void\s+OnDestroy\s*\(\s*\)\s*\{\s*$',before[:start])):
        raise ValueError('Only the exact observed OnDestroy generated block is recognized')
    return insertion


def validate_snapshot(expected: dict[str,str],actual: dict[str,str],old: str,observed: str) -> None:
    if (set(expected)!=set(actual) or expected.get(ENTRY)!=old or actual.get(ENTRY)!=observed
        or [p for p,h in expected.items() if actual[p]!=h]!=[ENTRY]):
        raise ValueError('Unrelated baseline, import or candidate drift cannot be reconciled')


def validate_lifecycle(source: bytes) -> None:
    tree=Parser(Language(tree_sitter_c_sharp.language())).parse(source)
    methods=[]
    def visit(node) -> None:
        name=node.child_by_field_name('name')
        if node.type=='method_declaration' and name is not None and name.text==b'OnDestroy':methods.append(node)
        for child in node.children:visit(child)
    visit(tree.root_node)
    if tree.root_node.has_error or len(methods)!=1:raise ValueError('Stable OnDestroy declaration required')
    body=methods[0].child_by_field_name('body')
    if body is None:raise ValueError('OnDestroy body required')
    text=body.text
    if not re.search(rb'^\s*#region\s+GeneratedBreak\s*$',text,re.M) or b'Context.Break();' not in text:
        raise ValueError('The delegated repair must preserve the generated region inside OnDestroy')


def report(host: OverlayHost,source: Path,request: VerificationRequest,tests: dict[str,str]) -> VerificationResult:
    value=host.overlay.read();before=git(source,'show',OLD_CANDIDATE+':'+RELATIVE)
    observed=(host.host/ENTRY).read_bytes();insertion=generated_insertion(before,observed)
    old=sha256(before).hexdigest();actual=sha256(observed).hexdigest()
    if request.candidate_revision!=OLD_CANDIDATE or value['candidate']!=OLD_CANDIDATE or old!=OLD_ENTRY_SHA:
        raise ValueError('Different entry drift requires separate reconciliation')
    expected=value['baseline']|value['managed']|value['pending']
    snapshot=host.overlay.scan();validate_snapshot(expected,snapshot,old,actual)
    diagnostics=[];log=Path(os.environ['LOCALAPPDATA'])/'Tuanjie/Editor/Editor.log'
    if log.exists():
        latest=log.read_text(encoding='utf-8',errors='replace').rsplit('## Output:',1)[-1]
        for line in latest.splitlines():
            if line.startswith('Assets\\JJGame\\monopoly\\Runtime\\Script\\UI\\LobbyRehearsal\\LobbyShellBindings.cs(') and 'error JJCK0011:' in line:
                line=line.replace('\\','/')
                if line not in diagnostics:diagnostics.append(line)
    proof={'state':'observed','old_candidate':OLD_CANDIDATE,'request_id':request.request_id,
        'old_entry_sha256':old,'observed_entry_sha256':actual,'insertion_hex':insertion.hex(),
        'only_known_entry_changed':True,'all_other_baseline_and_candidate_files_checked':len(snapshot)-1,
        'frozen':tests,'observed_import_compiler_messages':diagnostics,
        'compiler_messages_are_not_a_dedicated_verification_receipt':True,'human_accepted':False}
    atomic_write(host.state,'recovery-authorizations/generated-entry-v68.observed.bin',observed)
    atomic_write(host.state,PROOF,json.dumps(proof,indent=2).encode())
    message=('Import changed the committed Monopoly.cs by inserting a GeneratedBreak / Context.Break() region at the beginning of OnDestroy. '
        'The candidate moved its existing generated region into DestroyOrdinaryService. Preserve the SDK-generated lifecycle region inside OnDestroy and keep import idempotent; do not disable generation or drift checks. '
        'Only SHELL owns this source. The observed host bytes are archived; this is a real import-drift failure, not a test result. '
        'Original SHA256 '+old+'; observed SHA256 '+actual+'.')
    return VerificationResult(request,'ownership','failed',('SHELL',),(Violation('import_drift',ENTRY,'Monopoly.OnDestroy',message),))


def context(state: Path) -> dict[str,str]:
    path=state/PROOF
    if not path.exists():return {}
    value=json.loads(path.read_bytes())
    return {'readonly-import-drift/provenance.json':json.dumps({k:v for k,v in value.items() if k!='frozen'},ensure_ascii=False)}


def advance_materialization(host: OverlayHost,source: Path,candidate: str) -> None:
    """One explicit candidate transition; all source comes from admitted Git bytes."""
    proof_path=host.state/PROOF
    if not proof_path.exists():return
    proof=json.loads(proof_path.read_bytes());value=host.overlay.read()
    if value['candidate']!=OLD_CANDIDATE or candidate==OLD_CANDIDATE:return
    if proof.get('state')!='observed' or proof['old_candidate']!=OLD_CANDIDATE:
        raise ValueError('Generated-entry recovery provenance changed')
    host.preflight()
    if git(source,'rev-parse','HEAD').decode().strip()!=candidate or git(source,'status','--porcelain'):
        raise ValueError('Only a clean admitted candidate may materialize')
    git(source,'merge-base','--is-ancestor',OLD_CANDIDATE,candidate)
    validate_lifecycle((source/RELATIVE).read_bytes())
    for path,digest in proof['frozen'].items():
        if sha256((source/path).read_bytes()).hexdigest()!=digest:raise ValueError('Frozen test drift')
    archive=(host.state/'recovery-authorizations/generated-entry-v68.observed.bin').read_bytes()
    if sha256(archive).hexdigest()!=proof['observed_entry_sha256']:raise ValueError('Observed archive changed')
    generated_insertion(git(source,'show',OLD_CANDIDATE+':'+RELATIVE),archive)
    files={}
    for relative in filter(None,git(source,'ls-tree','-r','--name-only','-z',candidate).decode().split('\0')):
        target='Assets/JJGame/monopoly/'+relative
        if not host.overlay.allowed(target):continue
        portable_path(target);confined_path(host.host,target)
        raw=git(source,'show',candidate+':'+relative)
        if (source/relative).read_bytes()!=raw:raise ValueError('Candidate bytes changed')
        files[target]=raw
    hashes={p:sha256(raw).hexdigest() for p,raw in files.items()}
    with file_guard(host.overlay.state,'overlay.guard'):
        value=host.overlay.read();expected=value['baseline']|value['managed']|value['pending']
        validate_snapshot(expected,host.overlay.scan(),proof['old_entry_sha256'],proof['observed_entry_sha256'])
        if (value['candidate']!=OLD_CANDIDATE or value['pending'] or not set(value['managed'])<=set(files)
            or (set(files)&set(value['baseline']))-set(host.overlay.entry_exceptions())
            or candidate in value['history'] and value['history'][candidate]!=hashes):
            raise ValueError('Candidate advance changed mount scope or existing history')
        intent={'old_candidate':OLD_CANDIDATE,'candidate':candidate,'known_old_entry_drift':proof['observed_entry_sha256'],
            'new_source_hashes':hashes,'full_baseline_checks_required':True,'human_accepted':False}
        atomic_write(host.state,'recovery-authorizations/generated-entry-v68.advance-intent.json',json.dumps(intent,indent=2).encode())
        value['installing']=True;host.overlay.save(value)
        for path,raw in files.items():
            current=host.host/path
            if not current.is_file() or sha256(current.read_bytes()).hexdigest()!=hashes[path]:atomic_write(host.host,path,raw)
        value.update(managed=hashes,pending={},candidate=candidate,installing=False)
        value['history'][candidate]=hashes;host.overlay.save(value)
        host.overlay.check(value)
        atomic_write(host.state,'recovery-authorizations/generated-entry-v68.advance-complete.json',json.dumps(intent,indent=2).encode())
