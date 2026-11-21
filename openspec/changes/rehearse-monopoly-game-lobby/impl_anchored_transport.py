"""Small delegated edits over exact current or previously paid implementation bases."""
from __future__ import annotations
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING
from unity_coder.core.ai_models import ModelError
from unity_coder.core.local_executor import WorkerPatch
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git
from unity_coder.adapters.unity import UnityAdapter
if TYPE_CHECKING:
    from lobby_production_host import ContextWorkers
    from unity_coder.core.contracts import Unit


def admit(text: str,owned: tuple[str,...],bases: dict[str,bytes],current: dict[str,bytes],
          restored: tuple[str,...]) -> dict[str,bytes]:
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('Duplicate implementation transport key')
            result[key]=value
        return result
    data=json.loads(text,object_pairs_hook=unique)
    if (not isinstance(data,dict) or set(data)!={'files','edits','reason','accept_bases'}
        or not isinstance(data['accept_bases'],list)
        or any(not isinstance(path,str) for path in data['accept_bases'])
        or sorted(data['accept_bases'])!=sorted(restored)
        or not data['edits'] or set(bases)!=set(owned) or set(current)!=set(owned)
        or any(not p.startswith('Runtime/Script/') or not p.endswith('.cs') for p in owned)):
        raise ValueError('Complete owned bases, explicit restoration acceptance and concrete edits required')
    accepted=data.pop('accept_bases')
    spec=importlib.util.spec_from_file_location('impl_anchor_parser',Path(__file__).with_name('anchored_author.py'))
    parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
    patch,_=parser.parse_anchored_patch(json.dumps(data),owned,{p:v.decode('utf-8') for p,v in bases.items()})
    result={p:bases[p] for p in accepted if bases[p]!=current[p]}
    result.update(patch)
    if not any(patch.get(p,current[p])!=current[p] for p in patch):
        raise ValueError('Implementation repair cannot be an unchanged proposal')
    return result


def code(workers: ContextWorkers,unit: Unit,files: dict[str,str],feedback: str,operation: str) -> WorkerPatch:
    from full_baseline_restoration import descriptor
    if (unit.role!='impl' or unit.id!='SHELL' or workers.contract.contract_version<70
        or not workers.services.tdd.frozen):
        raise ValueError('Implementation anchors require the existing frozen SHELL unit')
    workers.services.tdd.assert_frozen()
    state=workers.coder.calls.budget.root;plan=descriptor(state,workers.contract.contract_version)
    if not plan or unit.id not in plan['owned']:raise ValueError('Paid restoration provenance required')
    current={p:(workers.root/p).read_bytes() for p in unit.owns};bases=dict(current);restored=[]
    for path in unit.owns:
        baseline=git(workers.root,'show',plan['baseline']+':'+path)
        if current[path]!=baseline:continue
        raw=git(workers.root,'show',plan['retained_candidate']+':'+path)
        if sha256(raw).hexdigest()!=plan['retained_proposals'][unit.id][path]:raise ValueError('Paid base identity changed')
        if raw!=current[path]:bases[path]=raw;restored.append(path)
    context=workers.context(unit,files)
    for path,raw in bases.items():
        context[path]=raw.decode('utf-8')
        context.pop('readonly-retained-proposal/'+path,None)
    hashes={p:sha256(v).hexdigest() for p,v in bases.items()}
    protocol=('Return exactly one JSON object with files, edits, accept_bases, reason. '
        'files is empty for this C#-only unit. edits contains {path,base_sha256,replacements:[{old,new}]}. '
        'Every old anchor must occur exactly once in the supplied exact base; use enough surrounding source '
        'to distinguish repeated catches. Replacements must not overlap. No full-file values, fences, ellipses '
        'or prose instructions to the host. All new code must be in your replacement text. '
        'accept_bases must exactly repeat restore_paths, explicitly accepting reapplication of those exact '
        'previously paid complete sources. The host will apply your edits to those bases and submit the full '
        'owned files through normal admission. Existing functional code must remain. At least one concrete '
        'owned-source edit is required; an incomplete proposal or a reason-only repair is invalid. '
        'In particular, the active analyzer rejects logically equivalent negated-is catch filters; satisfy '
        'its supported syntax without changing cancellation/completion behavior. Tests are frozen and read-only.')
    provenance={'contract_sha256':workers.contract.sha256,'operation':operation,'unit':unit.id,
        'current_sha256':{p:sha256(v).hexdigest() for p,v in current.items()},'base_sha256':hashes,
        'restore_paths':restored,'retained_candidate':plan['retained_candidate'],'human_accepted':False}
    atomic_write(state,'impl-anchors/'+operation+'.intent.json',json.dumps(provenance,indent=2).encode())
    rejected='';calls=[]
    for attempt in range(2):
        call=operation+('-impl-format-1' if attempt else '');calls.append(call)
        job={'stage':'green','owns':list(unit.owns),'criteria':list(unit.acceptance),'files':context,
            'source_sha256':hashes,'restore_paths':restored,'instructions':unit.instructions+'\n'+protocol,
            'feedback':feedback,'rejected_transport':rejected}
        prompt='Repair the delegated implementation with exact hash-bound edits.\n'+json.dumps(job,ensure_ascii=False,sort_keys=True)
        prompt+='\nFINAL REQUIRED TASK:\n'+unit.instructions+'\n'+protocol+'\n'+feedback
        if len(prompt.encode())>workers.max_context_bytes:raise ModelError('Implementation anchor context exceeds the approved host bound')
        # Direct native accounting avoids prompt-only lexical changes to anchor bytes.
        reply=workers.coder.calls.generate(call,unit.id,prompt,max_output_tokens=workers.token_budgets.green)
        try:
            patch=admit(reply.text,unit.owns,bases,current,tuple(restored))
            violations=UnityAdapter().parse_check(patch)
            if violations:raise ValueError('Implementation edit has C# syntax errors: '+str(violations))
        except ValueError as error:
            rejected=reply.text;feedback+='\nTRANSPORT REJECTION: '+str(error)+'. No proposal was admitted. Repair against the same supplied exact base.'
            continue
        workers.services.tdd.assert_frozen()
        atomic_write(state,'impl-anchors/'+operation+'.complete.json',json.dumps(provenance|{
            'actual_calls':calls,'model_reply_sha256':sha256(reply.text.encode()).hexdigest(),
            'file_sha256':{p:sha256(v).hexdigest() for p,v in patch.items()}},indent=2).encode())
        return WorkerPatch(patch,'Exact paid-source restoration plus actual model-authored hash-bound implementation edits')
    raise ModelError('Bounded implementation anchor transport failed; all paid calls remain recorded')
