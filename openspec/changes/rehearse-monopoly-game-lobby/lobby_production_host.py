"""Trusted composition for this rehearsal; no framework-runtime modifications."""
from dataclasses import asdict, fields, replace
from hashlib import sha256
from datetime import datetime, timezone
import hmac
import json
import os
from pathlib import Path
import re
from threading import Semaphore

from unity_coder.cli import invoke_local
from unity_coder.core.ai_models import load_ai_config, ModelClient, ModelError
from unity_coder.core.architect_boundary import ArchitectBoundary, discover_context
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.coding_workers import ModelCodingWorkers, StageTokenBudgets
from unity_coder.core.contracts import load_contract
from unity_coder.core.executor import ProductionExecutor
from unity_coder.core.lifecycle import RunLease, RunLifecycle
from unity_coder.core.local_executor import LocalExecutionServices, TestReviewRejected, WorkerPatch
from unity_coder.core.model_calls import ModelCalls
from unity_coder.core.model_workers import parse_patch
from unity_coder.core.review import ReviewGate, ReviewPackage
from unity_coder.core.storage import atomic_write
from unity_coder.core.target_profiles import load_profile
from unity_coder.core.verification import VerificationLadder
from unity_coder.core.workspaces import WorkspaceManager, git
from unity_coder.adapters.unity import UnityAdapter
from overlay_host import OverlayHost
from rehearsal_model_transport import RehearsalTransport
from scoped_context import test_excerpt, refactor_context
from compact_context import compact_author_context
from prompt_guidance import late_guidance, framework_api_for_test
from guarded_author import authored_repair
from operational_transport import retained_transport_failure, retained_key_limit_failure
from anchored_author import parse_anchored_patch
from anchor_diagnostics import diagnose_anchors
from noop_transport import normalize_identity_edits

RUN_ID='monopoly-game-lobby'
SPEC='specs/monopoly-game-lobby/'

def load_token_policy(path: Path) -> tuple[StageTokenBudgets, int]:
    """Require explicit allocations; never infer a new persistent run budget."""
    data=json.loads(path.read_bytes())
    if not isinstance(data,dict) or set(data)!={'stage_output_tokens','max_context_bytes'}:
        raise ValueError('Invalid rehearsal token policy fields')
    stages=data['stage_output_tokens']
    if not isinstance(stages,dict) or set(stages)!={f.name for f in fields(StageTokenBudgets)}:
        raise ValueError('Every paid stage requires an explicit output allocation')
    context_limit=data['max_context_bytes']
    if type(context_limit) is not int or context_limit<1:
        raise ValueError('Context byte ceiling must be a positive integer')
    return StageTokenBudgets(**stages),context_limit

class Utf8Calls:
    """Preserve JSON meaning while avoiding ASCII expansion of Chinese context."""
    def __init__(self, calls):
        self.calls,self.client=calls,calls.client

    def generate(self,call_id,unit_id,prompt,*,max_output_tokens):
        def literal(match):
            value=int(match.group(1),16)
            return chr(value) if value>=128 and not 0xD800<=value<=0xDFFF else match.group(0)
        # Only JSON-safe non-ASCII characters become literals. ASCII escapes and
        # surrogate pairs are preserved. Native ModelCalls still reserves and
        # records the exact final prompt before contacting the same provider.
        normalized=re.sub(r'(?<!\\)\\u([0-9a-fA-F]{4})',literal,prompt)
        # Large code contexts previously buried actionable judge findings ahead
        # of the old file body. Repeat the actual task/repair instructions last.
        try:
            payload=json.loads(normalized.partition('\n')[2])
            if payload.get('stage') in ('test_authoring','green','refactor'):
                normalized+='\nFINAL TASK INSTRUCTIONS:\n'+payload['instructions']
                if payload.get('feedback'):
                    normalized+='\nREQUIRED REPAIR FINDINGS (address every item in the returned files):\n'+payload['feedback']
        except (ValueError,KeyError,TypeError):
            pass
        if self.client.config.provider=='codex' and len(normalized)>1048576:
            from prompt_lexical_compaction import compact_prompt
            normalized=compact_prompt(normalized)
        if self.client.config.provider=='codex' and self.client.config.role=='judge':
            from codex_review_reuse import reuse_review
            reviewed=reuse_review(self.calls,call_id,unit_id,normalized,max_output_tokens)
            if reviewed is not None:return reviewed
        return self.calls.generate(call_id,unit_id,normalized,max_output_tokens=max_output_tokens)

class ContextWorkers:
    """Supply frozen context deliberately; all paid calls use native accounting."""
    def __init__(self, contract, coder, judge, root, *, token_budgets=None, max_context_bytes=None):
        self.contract,self.coder,self.judge_calls,self.root=contract,coder,judge,root
        if token_budgets is None or max_context_bytes is None:
            defaults,context_limit=load_token_policy(Path(__file__).with_name('token-policy.json'))
            token_budgets=defaults if token_budgets is None else token_budgets
            max_context_bytes=context_limit if max_context_bytes is None else max_context_bytes
        self.token_budgets,self.max_context_bytes=token_budgets,max_context_bytes
        self.admission=Semaphore(1)
        self.full_file_authoring={'TEST-FRIEND-REQUESTS'} if getattr(contract,'contract_version',0)>=37 else set()
        if getattr(contract,'contract_version',0)>=38:self.full_file_authoring.add('TEST-PARTNER-RECS')
        if getattr(contract,'contract_version',0)>=39:self.full_file_authoring.update(('TEST-CHAT','TEST-CHAT-MSG','TEST-CHAT-STATE'))

    def context(self, unit, files):
        key=unit.id.removeprefix('TEST-')
        if key in ('QUEUE','PARTY'):
            key='MATCH'
        key={'VIP':'CARDS','CHAT':'SOCIAL','CHAT-MSG':'SOCIAL','CHAT-STATE':'SOCIAL','FRIEND-REQUESTS':'SOCIAL','PARTNER-RECS':'SOCIAL'}.get(key,key)
        group={'HARNESS':(),'SHELL':('L1','L2','NFR'),'ECON':('L3','L7','L12'),
               'APPEAR':('L3','L7'),'CARDS':('L12',),
               'MATCH':('L9','L10','L11'),'SOCIAL':('L4','L13'),'RECORDS':('L5','L6','L8'),
               'PRES-CORE':('L1','L2'),'PRES-NFR':('NFR',)}[key]
        content={p:v for p,v in files.items() if p in unit.owns or p.endswith(('LobbyDtos.cs','LobbyPorts.cs','LobbyUiPort.cs','LobbyWorld.cs','LobbyConfiguration.cs','LobbyRehearsalViewBase.cs','LobbyRehearsalVMBase.cs','LobbyShellBindings.cs','Monopoly.LobbyRehearsal.cs','LobbyHarness.cs')) or p==self.contract.spec.path}
        if key=='SOCIAL' and unit.role=='test' and self.contract.contract_version>=36:
            content.update({p:v for p,v in files.items() if p.endswith('/LobbySocial.cs')})
        if unit.id in ('TEST-SHELL','TEST-PRES-CORE','TEST-PRES-NFR','TEST-APPEAR','TEST-CARDS'):
            content.update({p:v for p,v in files.items() if p in ('Runtime/Script/Monopoly.cs','Runtime/Script/MonopolyRootScene.cs','package.json')})
        suite={'HARNESS':'LobbyHarnessTests','SHELL':'LobbyPresentationTests','ECON':'LobbyEconomyTests','MATCH':'LobbyMatchTests','SOCIAL':'LobbySocialTests','RECORDS':'LobbyRecordsSettingsTests',
               'APPEAR':'LobbyEconomyTests','CARDS':'LobbyEconomyTests',
               'PRES-CORE':'LobbyPresentationCoreTests','PRES-NFR':'LobbyPresentationNfrTests'}[key]
        content.update({p:v for p,v in files.items() if p.endswith(suite+'.cs')})
        if key in ('APPEAR','CARDS') and unit.role=='test':
            evidence={}
            for p,v in files.items():
                if not p.endswith(('LobbyEconomyTests.cs','LobbyEconomyRechargeTests.cs','LobbyEconomyVipTests.cs')):continue
                content[p]=v if p in unit.owns else test_excerpt(v,set(unit.acceptance))
                evidence[p]=sha256(v.encode()).hexdigest()
            content[SPEC+'partial-test-evidence.json']=json.dumps({'source_sha256':evidence,
                'mapped_test_ids':list(unit.acceptance),'note':'Other partial-file test methods omitted from the prompt only; all shared helpers and full actual verification files remain.'})
        if (key=='SOCIAL' and unit.role=='test' and self.contract.contract_version>=23
            and (self.root/'Tests/Runtime/Script/LobbyRehearsal/LobbySocialChatTests.cs').exists()):
            evidence={}
            for p,v in files.items():
                if not p.endswith(('LobbySocialTests.cs','LobbySocialChatTests.cs','LobbySocialRequestsTests.cs','LobbySocialPartnersTests.cs','LobbyChatMessageTests.cs','LobbyChatStateTests.cs')):continue
                content[p]=v if p in unit.owns else test_excerpt(v,set(unit.acceptance))
                evidence[p]=sha256(v.encode()).hexdigest()
            content[SPEC+'partial-social-test-evidence.json']=json.dumps({'source_sha256':evidence,
                'mapped_test_ids':list(unit.acceptance),'note':'Shared partial helpers remain read-only and all full execution files are retained; only unrelated test methods are omitted from the prompt.'})
        if (key=='MATCH' and unit.role=='test' and self.contract.contract_version>=21
            and (self.root/'Tests/Runtime/Script/LobbyRehearsal/LobbyMatchQueueTests.cs').exists()):
            evidence={}
            for p,v in files.items():
                if not p.endswith(('LobbyMatchTests.cs','LobbyMatchQueueTests.cs','LobbyMatchPartyTests.cs')):
                    continue
                content[p]=v if p in unit.owns else test_excerpt(v,set(unit.acceptance))
                evidence[p]=sha256(v.encode()).hexdigest()
            content[SPEC+'partial-match-test-evidence.json']=json.dumps({'source_sha256':evidence,
                'mapped_test_ids':list(unit.acceptance),'note':'All shared helpers remain read-only across partials; only unrelated test bodies are omitted from the prompt. Full selected execution files remain unchanged.'})
        if unit.role=='impl':
            # UI assertions call shared economy/social/match functions too.
            # Supply the complete frozen acceptance source to every implementer
            # while retaining its exclusive write scope.
            content.update({p:v for p,v in files.items() if p.startswith('Tests/Runtime/Script/LobbyRehearsal/') and p.endswith(('.cs','.acceptance.md'))})
            if (self.root/SPEC/'test-author-plan.v6.md').exists():
                selected={link.test_id for link in self.contract.test_links if unit.id in link.implementing_units}
                originals={p:sha256(v.encode()).hexdigest() for p,v in content.items() if p.startswith('Tests/') and p.endswith('.cs')}
                for p in originals:content[p]=test_excerpt(content[p],selected)
                content[SPEC+'read-only-test-excerpts.json']=json.dumps({'source_sha256':originals,
                    'mapped_test_ids':sorted(selected),'note':'Prompt excerpts omit unrelated test methods and comments only. Helpers are retained. Full frozen files and the complete execution selection remain unchanged.'})
        policy=files['AGENTS.md']
        content['AGENTS.md']=policy[policy.index('## 2.'):policy.index('## 3.')]+policy[policy.index('## 5.'):]
        if unit.role=='test':
            content['AGENTS.md']=policy[policy.index('## 2.'):policy.index('## 3.')]+policy[policy.index('## 5.'):policy.index('## 6.')]
        for name in ('proposal.md','story-test-map.json','presentation-context.md','presentation-observation.json','binding-protocol.v2.md','acceptance-conditions.v2.json','test-harness-api.v3.txt','test-harness-api.v5.txt','test-preparation-findings.v4.json','test-preparation-guidance.v5.md','presentation-observation.v5.json','test-author-plan.v6.md','focused-repair.v7.md','focused-repair.v8.md'):
            if name=='focused-repair.v7.md' and (self.root/SPEC/'focused-repair.v8.md').exists():
                continue
            if name in ('presentation-observation.json','test-harness-api.v3.txt') and (self.root/SPEC/'test-preparation-guidance.v5.md').exists():
                continue
            if not (self.root/SPEC/name).exists():
                continue
            if name=='presentation-observation.json' and key!='SHELL':
                continue
            selected_name=name
            if (self.root/SPEC/'approved-rehearsal-scope.v15.md').exists():
                selected_name={'acceptance-conditions.v2.json':'acceptance-conditions.v15.json','presentation-observation.v5.json':'presentation-observation.v15.json'}.get(name,name)
            if (self.root/SPEC/'verification-strategy.v16.md').exists() and name=='acceptance-conditions.v2.json':
                selected_name='acceptance-conditions.v16.json'
            if (self.root/SPEC/'test-author-plan.v6.md').exists():
                selected_name={'story-test-map.json':'story-test-map.v6.json','acceptance-conditions.v2.json':'acceptance-conditions.v6.json'}.get(selected_name,selected_name)
            if name=='acceptance-conditions.v2.json' and (self.root/SPEC/'acceptance-conditions.v39.json').exists():
                selected_name='acceptance-conditions.v39.json'
            text=(self.root/SPEC/selected_name).read_text(encoding='utf-8')
            if name=='test-preparation-findings.v4.json':
                text=json.dumps({unit.id:json.loads(text).get(unit.id,[])},ensure_ascii=False)
            if name=='story-test-map.json':
                text=json.dumps([r for r in json.loads(text) if r['test'] in unit.acceptance],ensure_ascii=False)
            if name=='acceptance-conditions.v2.json':
                text=json.dumps([r for r in json.loads(text) if r['test'] in unit.acceptance],ensure_ascii=False)
            if name=='presentation-observation.json':
                observed=json.loads(text)
                text=json.dumps({'scene':observed['scene'],'sceneGuid':observed['sceneGuid'],
                    'created_assets':observed['createdAssets'],
                    'views':[{k:v for k,v in view.items() if k!='controls'} for view in observed['views']],
                    'action_names':sorted({c for view in observed['views'] for c in view['controls']})},ensure_ascii=False)
            content[SPEC+name]=text
        scope=self.root/SPEC/'approved-rehearsal-scope.v15.md'
        if scope.exists():
            content[SPEC+'approved-rehearsal-scope.v15.md']=scope.read_text(encoding='utf-8')
            if (unit.role=='test' and key in ('APPEAR','CARDS','SOCIAL','MATCH','RECORDS')
                and not (self.contract.contract_version>=17 and key in ('APPEAR','CARDS'))):
                hashes={}
                for p,v in files.items():
                    if p.endswith(('LobbyPresentationCoreTests.cs','LobbyPresentationNfrTests.cs')):
                        content[p]=test_excerpt(v,set());hashes[p]=sha256(v.encode()).hexdigest()
                content[SPEC+'read-only-observation-examples.json']=json.dumps({'source_sha256':hashes,
                    'note':'Independently source-reviewed observation helpers only. Private helpers are reference mechanics, not callable public APIs; reuse mechanics within owned fixtures without invoking NUnit tests or fabricating business outcomes.'})
        for name in ('approved-rehearsal-scope.v16.md','verification-strategy.v16.md','review-rubric.v16.json','payment-api.v18.md','completion-fixture.v21.md','platform-inputs.v30.md','social-fixture-guidance.v31.md','social-planning-evidence.v31.json','seat-randomness.v32.md','seat-oracle.v34.md','social-pages.v35.md','request-observation.v36.md','notification-trace.v37.md','chat-authoring.v39.md','preparation-order.v41.md','message-oracles.v42.md','gesture-clock.v43.md','message-content.v44.md'):
            path=self.root/SPEC/name
            if path.exists():content[SPEC+name]=path.read_text(encoding='utf-8')
        content.update(late_guidance(self.root,SPEC))
        content.update(getattr(self,'supplemental_context',{}).get(unit.id,{}))
        if unit.id=='SHELL' and self.contract.contract_version==68:
            from generated_entry_reconciliation import context as import_context
            content.update(import_context(self.coder.calls.budget.root))
        if unit.id in ('TEST-CARDS','TEST-VIP'):
            for name in ('architect-findings.v22.md','catalog-consistency.v23.json'):
                path=self.root/SPEC/name
                if path.exists():content[SPEC+name]=path.read_text(encoding='utf-8')
        diagnostics=self.root/SPEC/'mechanical-compile-errors.v16.json'
        if diagnostics.exists():
            content[SPEC+'mechanical-compile-errors.v16.json']=json.dumps(json.loads(diagnostics.read_bytes()).get(unit.id,[]),ensure_ascii=False)
        stories=(self.root/SPEC/'sources/大赢家局外主界面-用户故事.md').read_text(encoding='utf-8-sig')
        chunks=re.split(r'(?=^### US-)',stories,flags=re.M)
        content[SPEC+'selected-original-stories.md']='\n'.join(re.split(r'^## ',chunk,maxsplit=1,flags=re.M)[0] for chunk in chunks if any(chunk.startswith('### US-'+g+'-') for g in group))
        if key in ('SHELL','PRES-CORE','PRES-NFR','APPEAR','CARDS','RECORDS') or (unit.role=='test' and key=='MATCH' and self.contract.contract_version>=21):
            api=(self.root/SPEC/'framework-context.md').read_text(encoding='utf-8')
            if unit.role=='test' and key in ('PRES-CORE','PRES-NFR','APPEAR','CARDS','MATCH','RECORDS'):
                api=framework_api_for_test(api,key)
            if unit.role=='test' and not (self.root/SPEC/'test-preparation-guidance.v5.md').exists():
                api='Pure coordinator tests use ILobbyUiPort, not the real Navigator or Injector. Inspect protected assets with AssetDatabase.'
            api=re.sub(r'(?m)^\s*///.*\n','',api)
            api=re.sub(r'(?m)^\s*//.*\n','',api)
            content[SPEC+'framework-context.md']=re.sub(r'\n\s*\n','\n',api)
            for p,v in files.items():
                if p.endswith(('Presenter.cs','View.cs','VM.cs')) and '/LobbyRehearsal/' in p:
                    if self.contract.contract_version>=17 and key in ('APPEAR','CARDS') and unit.role=='test':
                        stem=Path(p).stem
                        screen=re.sub(r'(Presenter|View|VM)$','',stem)
                        owned_text='\n'.join(files.get(path,'') for path in unit.owns if path.endswith('.cs'))
                        if not any(re.search(r'\b'+re.escape(screen+suffix)+r'\b',owned_text) for suffix in ('View','VM','Presenter')):
                            continue
                    content[p]=v
        if unit.role=='test':
            required={
                'HARNESS':('Test harness preparation',),
                'SHELL':('Existing entry','Original 3D','Portrait navigation','Wallet and','Reporting and shared','Durable account','Editor rehearsal'),
                'ECON':('Wallet and','Appearance catalog','Shop ordering','Simulated checkout','Coin-card','Informational platform VIP','Durable account'),
                'APPEAR':('Existing entry','Original 3D','Portrait navigation','Wallet and','Appearance catalog','Shop ordering','Durable account','Editor rehearsal'),
                'CARDS':('Wallet and','Simulated checkout','Coin-card','Informational platform VIP','Durable account'),
                'MATCH':('Configured tiers','Party and','Queue start','Handoff and','Abandonment','Durable account'),
                'SOCIAL':('Platform friends','Responsive world','Reporting and shared','Durable account'),
                'RECORDS':('Rolling rankings','History and','Settings and','Durable account'),
                'PRES-CORE':('Existing entry','Original 3D','Portrait navigation','Wallet and','Reporting and shared','Durable account','Editor rehearsal'),
                'PRES-NFR':('Existing entry','Original 3D','Portrait navigation','Reporting and shared','Durable account','Settings and'),
            }[key]
            sections=re.split(r'(?=^### Requirement:)',content[self.contract.spec.path],flags=re.M)
            content[self.contract.spec.path]='# Exact excerpts from the frozen specification for this unit\n'+''.join(s for s in sections if any(s.startswith('### Requirement: '+title) for title in required))
            # One representative binding shows the common prepared structure;
            # all ten names and asset GUIDs remain in the observation excerpt.
            for p in tuple(content):
                if p.endswith(('Presenter.cs','View.cs')) and '/LobbyRehearsal/' in p and not p.endswith(('LobbyPresenter.cs','LobbyView.cs')) and not (self.root/SPEC/'test-preparation-guidance.v5.md').exists():
                    content.pop(p)
        content[SPEC+'current-unit-scope.json']=json.dumps({'unit':asdict(unit),
            'test_links':[asdict(link) for link in self.contract.test_links if link.author_unit==unit.id or unit.id in link.implementing_units],
            'scope_note':'Review this test author against its mapped source clauses, not stories assigned to other authors. LOBBY is the mechanical shared criterion required by the frozen schema; source-clause mappings remain substantive. Full acceptance uses all suites. Observation-only harness behavior is not game business behavior.'},ensure_ascii=False)
        if unit.role=='test' and (self.root/SPEC/'focused-repair.v7.md').exists():
            content=compact_author_context(unit.id,unit.owns,content)
        if unit.role=='impl' and self.coder.client.config.provider==self.judge_calls.client.config.provider=='codex':
            from implementation_context_scope import scoped
            content=scoped(unit.id,content)
        size=len(json.dumps(content,ensure_ascii=False).encode())
        print('CONTEXT',unit.id,size,'UTF-8 bytes',flush=True)
        from codex_context_recovery import enforce_context_limit
        enforce_context_limit(size,self.max_context_bytes,
                              self.coder.client.config.provider,self.judge_calls.client.config.provider)
        return content

    def worker(self,limit=None):
        # Historical one-time recovery IDs retain their recorded allowances.
        # Normal stages always use the explicit policy; changing an old paid
        # identity must still fail closed in ModelCalls.
        if limit is not None:
            return ModelCodingWorkers(self.contract,self.coder,self.judge_calls,max_output_tokens=limit)
        return ModelCodingWorkers(self.contract,self.coder,self.judge_calls,token_budgets=self.token_budgets)

    def anchored_code(self,unit,context,feedback,operation_id):
        services=getattr(self,'services',None)
        if unit.role!='test' or services is None or services.tdd.frozen:
            raise ValueError('Anchored repairs are restricted to unfrozen test authors')
        context=dict(context)
        # The native read-only context uses read_text; transport anchors instead
        # bind the actual UTF-8 bytes so CRLF outside model edits is preserved.
        originals={p:(self.root/p).read_bytes().decode('utf-8') for p in unit.owns
            if p.endswith('.cs') and (self.root/p).is_file()}
        context.update(originals)
        if len(json.dumps(context,ensure_ascii=False).encode())>self.max_context_bytes:
            raise ValueError('Raw anchored source exceeds the existing context guard')
        hashes={p:sha256(v.encode()).hexdigest() for p,v in originals.items()}
        if (self.contract.contract_version==24 and unit.id=='TEST-APPEAR'
            and os.environ.get('LOBBY_RESUME_ANCHOR_V24')=='1'):
            feedback+='\nDiagnosed prior transport failure: AssertVisibleTextContains is NOT declared in your owned LobbyEconomyTests.cs. It is a read-only partial helper. Do not anchor a declaration from another file or from imagined intermediate edits. If a new helper is necessary, insert it using an existing unique anchor from your actual owned source, and change its callers using separate original-source anchors. Keep all independent judge findings and effective assertions. No previous rejected patch was applied.'
        protocol=('Use the host anchored repair transport: return exactly files, edits, reason. '
            'Return one strict JSON object, never YAML, fences or a file listing. '
            'files maps only changed/new owned non-C# notes/metadata to full contents; omit unchanged historical notes. '
            'The supplied owns list is exclusive. Ignore any historical instruction naming an unowned note; never invent another repair-vN note. Update an existing owned acceptance map instead. '
            'C# full-file values are forbidden. Repair only the necessary original-source blocks. '
            'edits is a list of objects {path,base_sha256,replacements:[{old,new}]}. Each old string must '
            'match exactly once in the original supplied file; use nonoverlapping replacements, no ellipses. '
            'Use the supplied source hashes. Preserve every unmodified source byte and all effective assertions. '
            'Only the actual model-authored replacement text is applied. Do not write business implementation. '
            'This transport supersedes historical full-file output hints; acceptance requirements are unchanged. ')
        if self.contract.contract_version==68:
            from approved_test_reconciliation import SCOPE
            if unit.id in SCOPE:
                protocol+=' The user explicitly approved correcting the identified contradictory assertions inside the named method only. Preserve all other coverage and every byte outside that body; the current unit instructions define the exact exception. '
        state=self.coder.calls.budget.root
        proof={'contract_sha256':self.contract.sha256,'unit':unit.id,'operation':operation_id,
            'source_sha256':hashes,'transport_sha256':sha256(Path(__file__).with_name('anchored_author.py').read_bytes()).hexdigest(),
            'bounded_format_retries':1,'human_accepted':False}
        atomic_write(state,'anchored-author/'+operation_id+'.intent.json',json.dumps(proof,indent=2).encode())
        rejected=getattr(self,'rejected_transport',{}).get(unit.id,'')
        diagnostics=('\nPrior completed paid response was rejected without applying files. Repair its transport against the original source. Anchor diagnostics: '+json.dumps(diagnose_anchors(rejected,originals))) if rejected else ''
        calls=[]
        for attempt in range(2):
            call=operation_id+('-anchor-format-1' if attempt else '')
            job={'stage':'test_authoring','owns':list(unit.owns),'criteria':list(unit.acceptance),
                'instructions':unit.instructions+'\nFINAL REQUIRED SERIALIZATION (supersedes earlier full-file hints):\n'+protocol,
                'files':context,'feedback':feedback+diagnostics,'source_sha256':hashes,
                'required_new_files':[p for p in unit.owns if not (self.root/p).is_file()]}
            if rejected:job['rejected_transport']=rejected
            prompt='Repair the delegated unfrozen test unit using strict hash-bound edits.\n'+json.dumps(job,sort_keys=True,ensure_ascii=False)
            if len(prompt.encode())>self.max_context_bytes:
                raise ModelError('Rejected-response recovery exceeds the existing context guard; no request sent')
            reply=self.coder.generate(call,unit.id,prompt,max_output_tokens=self.token_budgets.test_authoring);calls.append(call)
            try:
                canonical,removed_identities=normalize_identity_edits(reply.text,originals)
                patch,reason=parse_anchored_patch(canonical,unit.owns,originals)
                if not any(p.endswith('.cs') for p in patch):raise ValueError('Required C# repair omitted')
                if any(not (self.root/p).is_file() and p not in patch for p in unit.owns):
                    raise ValueError('Required new owned note or metadata omitted')
                if self.contract.contract_version==68:
                    from approved_test_reconciliation import SCOPE,validate_patch
                    if unit.id in SCOPE:validate_patch(unit.id,patch,self.root)
                violations=UnityAdapter().parse_check({p:v for p,v in patch.items() if p.endswith('.cs')})
                if violations:raise ValueError('C# syntax errors: '+str(violations))
            except ValueError as error:
                rejected=reply.text
                diagnostics='\nTransport rejection (no files applied): '+str(error)+'. Anchor diagnostics: '+json.dumps(diagnose_anchors(reply.text,originals))+'. Repair the supplied rejected transport using unique larger original-source anchors. Return corrected strict JSON; all behavioral requirements and effective assertions remain.\n'
                try:
                    candidate_files=json.loads(reply.text).get('files',{})
                    diagnostics+=' Unowned file paths that MUST be omitted: '+json.dumps([p for p in candidate_files if p not in unit.owns])+'.'
                except (ValueError,AttributeError,TypeError):pass
                continue
            atomic_write(state,'anchored-author/'+operation_id+'.complete.json',json.dumps(proof|{
                'actual_calls':calls,'identity_replacements_removed':removed_identities,
                'canonical_transport_sha256':sha256(canonical.encode()).hexdigest(),
                'file_sha256':{p:sha256(v).hexdigest() for p,v in patch.items()}},indent=2).encode())
            return WorkerPatch(patch,reason)
        raise ModelError('Bounded anchored transport requires owner reconciliation; all actual calls retained')

    def approved_review(self,unit):
        services=getattr(self,'services',None)
        if (unit.role!='test' or services is None or services.tdd.state(unit.id).stage!='test_reviewed'
            or unit.id not in services.tdd._reviews):
            return None
        state=self.coder.calls.budget.root
        relative='reviewed-tests/v'+str(self.contract.contract_version)+'/'+unit.id+'.json'
        path=state/relative
        explanation=services.tdd._reviews[unit.id]
        if path.exists():
            record=json.loads(path.read_bytes())
        else:
            saved=json.loads((state/services.prefix/'state.json').read_bytes())
            candidate=saved['candidate_revision']
            receipts=state/'.agent/runs'/RUN_ID/'model-calls'
            proof=[]
            for receipt in receipts.glob('*.json'):
                data=json.loads(receipt.read_bytes())
                if data['identity']['role']!='judge' or data['identity']['unit_id']!=unit.id or 'reply' not in data:
                    continue
                try: decision=json.loads(data['reply']['text'])
                except ValueError: continue
                if decision.get('valid') is True and decision.get('explanation')==explanation:
                    proof.append(data['identity']['call_id'])
            if not proof: raise ValueError('Reviewed-state cache lacks actual independent judge evidence')
            hashes={p:sha256(git(self.root,'show',candidate+':'+p)).hexdigest() for p in unit.owns}
            record={'contract_sha256':self.contract.sha256,'candidate':candidate,'hashes':hashes,
                'explanation':explanation,'actual_judge_calls':proof,'human_accepted':False}
            atomic_write(state,relative,json.dumps(record,indent=2).encode())
        if record['contract_sha256']!=self.contract.sha256 or record['explanation']!=explanation:
            raise ValueError('Independent test review identity changed')
        if any(sha256((self.root/p).read_bytes()).hexdigest()!=identity for p,identity in record['hashes'].items()):
            raise ValueError('Independently reviewed test bytes changed')
        return explanation

    def code(self,unit,stage,files,feedback,operation_id):
        if stage=='test_authoring' and self.contract.contract_version==68:
            from approved_test_reconciliation import SCOPE,author_paths,validate_patch
            if unit.id in SCOPE:
                if self.services.tdd.frozen:raise ModelError('Reconciled tests are already frozen')
                actual=replace(unit,owns=author_paths(unit.id),instructions=unit.instructions+' Only the three explicitly writable paths may change. In the existing C# file, change only the approved method body. Keep every other byte, method, attribute and signature unchanged. Write the two new reconciliation note/metadata files; omit all older notes.')
                with self.admission:
                    print('Authoring approved test reconciliation',unit.id,flush=True)
                    patch=self.anchored_code(actual,self.context(unit,files),feedback,operation_id)
                    validate_patch(unit.id,patch.files,self.root)
                    return patch
        restored_note=getattr(self,'restored_baseline_note','')
        if stage=='green' and restored_note:
            from full_baseline_restoration import coding_note
            restored_note=coding_note(self.coder.calls.budget.root,self.contract.contract_version,unit.id,self.root,restored_note)
        if stage=='test_authoring' and restored_note and self.approved_review(unit):
            return WorkerPatch({},'Retain exact unchanged test files with their actual positive independent source review after baseline-only runtime restoration')
        if stage=='test_authoring' and getattr(self,'carried_tests',()):
            if self.contract.contract_version>=68:
                from doubled_budget_continuation import reusable_source
                frozen={p:sha256((self.root/p).read_bytes()).hexdigest() for p in self.carried_tests}
                if reusable_source(unit.owns,frozen,frozen):
                    return WorkerPatch({},'Retain unaffected frozen test source; independent review remains required')
            if self.contract.contract_version==67:
                from doubled_budget_continuation import reusable_source
                from full_baseline_restoration import descriptor
                value=descriptor(self.coder.calls.budget.root,67)
                if value and value.get('recovery_id')=='lobby-double-v66':
                    actual={p:sha256((self.root/p).read_bytes()).hexdigest() for p in unit.owns}
                    if reusable_source(unit.owns,actual,value['tests']):
                        return WorkerPatch({},'Retain exact frozen authored source; obtain actual independent source review in this cycle')
            allowed=getattr(self,'supplemental_authoring',{}).get(unit.id)
            if allowed:
                from supplemental_frozen_coverage import new_author_paths
                writable=new_author_paths(unit.owns,{p:'' for p in self.carried_tests},list(allowed))
                actual=replace(unit,owns=writable,instructions=unit.instructions+' Write only the explicitly new owned files. Every original file is frozen and read-only; do not rewrite existing helpers, assertions or maps.')
                with self.admission:
                    print('Authoring supplementary coverage',unit.id,'new files',len(writable),flush=True)
                    return self.worker().code(actual,stage,self.context(unit,files),feedback,operation_id)
            raise ModelError('Budget continuation cannot reauthor globally frozen tests; reconcile the independent review finding with the Architect')
        if stage=='green' and getattr(self,'services',None) is not None:
            from compile_repair_context import mechanical_feedback
            feedback+=mechanical_feedback(self.services.state,self.contract.sha256)
            feedback+=restored_note
        recovered=getattr(self,'reconciled_worker_patch',None)
        if recovered and stage=='test_authoring' and recovered['unit']==unit.id and recovered['operation']==operation_id:
            if unit.role!='test' or self.services.tdd.frozen:
                raise ValueError('Reconciled author patch cannot change frozen tests')
            if any(sha256((self.root/p).read_bytes()).hexdigest()!=h for p,h in recovered['source_sha256'].items()):
                raise ValueError('Reconciled author source changed')
            return WorkerPatch(recovered['files'],recovered['reason'])
        reuse=getattr(self,'zero_http_reuse',None)
        if reuse and stage=='test_authoring' and reuse['unit']==unit.id and reuse['operation']==operation_id:
            if any(sha256((self.root/p).read_bytes()).hexdigest()!=h for p,h in reuse['hashes'].items()):
                raise ValueError('Zero-HTTP admitted source changed')
            return WorkerPatch({},'Reuse exact admitted coder source after proven pre-HTTP failure; actual independent review remains required')
        if (os.environ.get('LOBBY_RESUME_ZERO_TLS_V25')=='1' and self.contract.contract_version==25
            and unit.id=='TEST-VIP' and stage=='test_authoring' and operation_id=='v25-step5-prepare-TEST-VIP-TEST-VIP'):
            from resume_schannel_v25 import verify_author
            verify_author(self.coder.calls.budget.root,self.root,zero=True)
            return WorkerPatch({},'Retain admitted VIP coder patch after proven zero-HTTP TLS setup failure; obtain independent review')
        if ((os.environ.get('LOBBY_RESUME_DIRECT_SCHANNEL_V25')=='1' or os.environ.get('LOBBY_RESUME_DIRECT_PRECONNECT_V25')=='1') and self.contract.contract_version==25
            and unit.id=='TEST-APPEAR' and stage=='test_authoring'
            and operation_id==('v25-step4-prepare-TEST-APPEAR-TEST-APPEAR' if os.environ.get('LOBBY_RESUME_DIRECT_PRECONNECT_V25')=='1' else 'v25-step3-prepare-TEST-APPEAR-TEST-APPEAR')):
            from resume_schannel_v25 import verify_author
            verify_author(self.coder.calls.budget.root,self.root)
            return WorkerPatch({},'Retain exact admitted paid coder patch after direct TLS handshake failure; independent Sol review still required')
        if ((os.environ.get('LOBBY_RESUME_SOL_REVIEW_V24')=='1' or os.environ.get('LOBBY_RESUME_SOL_SCHANNEL_V24')=='1')
            and self.contract.contract_version==24 and unit.id=='TEST-APPEAR'
            and stage=='test_authoring' and operation_id==('v24-step6-prepare-TEST-APPEAR-TEST-APPEAR' if os.environ.get('LOBBY_RESUME_SOL_SCHANNEL_V24')=='1' else 'v24-step5-prepare-TEST-APPEAR-TEST-APPEAR')):
            from resume_sol_review_v24 import verify_admitted_author
            verify_admitted_author(self.coder.calls.budget.root,self.root)
            return WorkerPatch({},'Reuse exact admitted step-four coder patch after unknown judge connection failure; independent review still required')
        if stage=='test_authoring' and self.approved_review(unit):
            return WorkerPatch({},'Retain the actual independently reviewed, hash-pinned test unit unchanged')
        if stage=='test_authoring' and feedback.startswith('Independent judge findings'):
            # Native prepare retains one shared feedback string across units.
            # Reuse only this author's actual rejection, not a peer's findings.
            receipts=self.coder.calls.budget.root/'.agent/runs'/RUN_ID/'model-calls'
            own=[]
            for path in receipts.glob('*.json'):
                data=json.loads(path.read_bytes())
                identity=data['identity']
                if (identity['role']=='judge' and identity['unit_id']==unit.id
                    and identity['call_id'].startswith('v'+str(self.contract.contract_version)+'-') and 'reply' in data):
                    try: decision=json.loads(data['reply']['text'])
                    except ValueError: continue
                    if decision.get('valid') is False:own.append((path.stat().st_mtime,decision['explanation']))
            feedback='Independent judge findings for '+unit.id+': '+max(own)[1] if own else ''
        elif stage!='test_authoring' and feedback.startswith('Independent judge findings'):
            feedback=''
        if stage not in ('test_authoring','green','refactor'):
            raise ValueError('Unsupported coding stage')
        if stage=='test_authoring':
            feedback+=getattr(self,'authoring_clarifications',{}).get(unit.id,'')
        limit=getattr(self.token_budgets,stage)
        with self.admission:
            print('Preparing',unit.id,stage,'reservation output',limit,flush=True)
            context=self.context(unit,files)
            prior=getattr(getattr(self,'services',None),'state',{}).get('verification') or {}
            if stage=='green' and unit.role=='impl' and unit.id in prior.get('related_units',()):
                from compile_failure_context import curate
                context=curate(prior.get('gate',''),prior.get('status',''),context,unit.owns)
            if stage=='test_authoring' and unit.id in getattr(self,'blocked_author_notes',set()):
                if self.services.tdd.frozen:raise ModelError('Frozen author cannot record a preparation blocker')
                notes=tuple(p for p in unit.owns if p.endswith('.md'))
                actual=replace(unit,owns=notes,instructions='The configured independent judge found a compilation defect in a read-only peer-owned helper. You cannot repair that peer file. Record this unresolved ownership/dependency blocker truthfully in an existing owned note. Return JSON files and reason; write only one of the supplied owned Markdown paths, with no C# or metadata changes. Preserve every test. Do not claim validity or progress. The actual independent judge must review the unchanged source and native bounded failures must return a contract dossier. The next Architect contract will schedule the owning message author before Social.')
                patch=self.worker().code(actual,stage,context,feedback,operation_id)
                if not patch.files or any(p not in notes for p in patch.files):raise ModelError('Blocked author may only document its actual blocker')
                return patch
            if stage=='test_authoring' and unit.id=='TEST-RECORDS' and self.contract.contract_version>=54:
                focused=replace(unit,instructions=unit.instructions+'\nRECORDS OUTPUT DISCIPLINE: emit all 24 mapped [Test] methods FIRST, followed by a small finite set of assertion helpers and necessary recording-adapter interface members. Reuse the supplied harness. At most twelve new assertion helpers; no recursive wrapper chains, repeated suffixes or invented adapters/APIs. Assertions must be substantive, expected to fail against stubs; no business behavior or fabricated results. Preserve every mapped source clause and truthful notes. Follow the final strict hash-bound edit serialization, with actual model-authored C# replacement blocks.')
                return self.anchored_code(focused,context,feedback,operation_id)
            if stage=='test_authoring' and unit.id in getattr(self,'full_file_authoring',set()):
                originals={p:files.get(p,'').encode() for p in unit.owns if p.endswith('.cs')}
                if not originals or self.services.tdd.frozen:
                    raise ModelError('Focused full-file recovery scope changed')
                if sum(map(len,originals.values()))>65536:
                    return self.anchored_code(unit,context,feedback+'\nOwned source now exceeds the small-file threshold; use the final hash-bound edit protocol, preserving the complete supplied source.',operation_id)
                actual=replace(unit,instructions=unit.instructions+'\nFINAL OUTPUT OVERRIDE FOR THIS SMALL FOCUSED RECOVERY: Return strict JSON with files and reason, with the complete repaired owned C# file in files, plus changed owned notes. Do not use anchored edits. All behavioral findings, ownership and effective assertions remain required.')
                patch=authored_repair(lambda details,call:self.worker().code(actual,stage,context,details,call),feedback,operation_id,originals,True)
                if not any(p in patch.files and patch.files[p]!=v for p,v in originals.items()):
                    raise ModelError('Focused recovery returned no changed C# source')
                return patch
            if stage=='refactor' and (self.root/SPEC/'test-author-plan.v6.md').exists():
                context=refactor_context(context,self.contract.spec.path)
            if stage=='test_authoring' and ((unit.id=='TEST-APPEAR' and self.contract.contract_version>=15)
                or (unit.id=='TEST-PRES-NFR' and self.contract.contract_version>=16)
                or (unit.id=='TEST-CARDS' and self.contract.contract_version>=18)
                or (unit.id in ('TEST-MATCH','TEST-QUEUE','TEST-PARTY') and self.contract.contract_version>=21)
                or (unit.id in ('TEST-VIP','TEST-CHAT','TEST-SOCIAL') and self.contract.contract_version>=23)):
                return self.anchored_code(unit,context,feedback,operation_id)
            if stage=='test_authoring' and unit.id in ('TEST-FRIEND-REQUESTS','TEST-PARTNER-RECS') and self.contract.contract_version>=30:
                return self.anchored_code(unit,context,feedback,operation_id)
            if stage=='test_authoring' and (self.root/SPEC/'focused-repair.v7.md').exists():
                services=getattr(self,'services',None)
                if services is not None and services.tdd.frozen:
                    raise ValueError('Frozen tests cannot return to authoring')
                originals={p:files.get(p,'').encode() for p in unit.owns if p.endswith('.cs')}
                must_change=unit.id=='TEST-PRES-CORE' or not any('[Test' in v.decode() for v in originals.values())
                return authored_repair(lambda details,call:self.worker().code(unit,stage,context,details,call),
                    feedback,operation_id,originals,must_change)
            return self.worker().code(unit,stage,context,feedback,operation_id)

    def review_tests(self,unit,files,operation_id):
        prior=self.approved_review(unit)
        if prior:return prior
        with self.admission:
            print('Reviewing',unit.id,'test validity and coverage',flush=True)
            try:
                return self.worker().review_tests(unit,self.context(unit,files),operation_id)
            except TestReviewRejected:
                # Native worker retains the paid structured reply but throws a
                # generic rejection. Forward the real judge findings to the
                # next author attempt instead of repeating an opaque prompt.
                calls=self.judge_calls.calls
                path=calls.budget.root/(calls.prefix+'/'+sha256(operation_id.encode()).hexdigest()+'.json')
                record=json.loads(path.read_bytes())
                try:
                    reply=json.loads(record['reply']['text'])
                    explanation=reply.get('explanation')
                    if not isinstance(explanation,str) or not explanation.strip():
                        raise ValueError('No actionable explanation')
                except (ValueError,KeyError,TypeError):
                    raise TestReviewRejected('Independent judge returned invalid structured preparation evidence; return a valid decision and actionable explanation') from None
                raise TestReviewRejected('Independent judge findings for '+unit.id+': '+explanation) from None

    def judge(self,unit,evidence,files,operation_id):
        with self.admission:
            print('Reviewing',unit.id,evidence.gate,flush=True)
            context=self.context(unit,files)
            if unit.role=='impl':
                from compile_failure_context import curate
                context=curate(evidence.gate,evidence.status,context,unit.owns)
            return self.worker().judge(unit,evidence,context,operation_id)

def main():
    framework=Path.cwd().resolve()
    root=Path(os.environ['LOBBY_RUN_ROOT']).resolve()
    module=root/'module'
    state=root/'trusted-state'
    policy=json.loads((state/'budget-policy.json').read_bytes())
    if policy.get('run_id') != RUN_ID:
        raise ValueError('Existing budget identity changed')
    limits=policy.get('limits',policy)
    token_budgets,max_context_bytes=load_token_policy(Path(__file__).with_name('token-policy.json'))
    rules=UnityAdapter()
    active_path=state/'current-execution.json'
    active=json.loads(active_path.read_bytes()) if active_path.exists() else {'version':1,'candidate':git(module,'rev-parse','HEAD').decode().strip(),'contract_source':'module'}
    version=active['version']
    contract_source=module if active['contract_source']=='module' else root/'worktrees'/active['contract_source']
    contract=None
    for number in range(1,version+1):
        contract=load_contract((contract_source/SPEC/('contract.v'+str(number)+'.json')).read_bytes(),contract_source,rules,previous=contract,max_cycles=limits['max_cycles'])
    profile=load_profile((contract_source/contract.coding_profile_ref.path).read_bytes(),contract_source,rules=rules,
        allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),
        test_roots=('Tests/Runtime/Script/LobbyRehearsal',))
    profile.validate_contract(contract)
    frozen=tuple(profile.protected_paths)+tuple(SPEC+'contract.v'+str(number)+'.json' for number in range(1,version+1))
    from frozen_budget_continuation import protected_tests
    carried_tests=protected_tests(state,contract_source,version)
    frozen+=carried_tests
    baseline_frozen=frozen
    from full_baseline_restoration import extra_protection,assert_tests,context as restored_context
    additional_protection=extra_protection(state,version)
    frozen+=tuple(p for p in additional_protection if p not in frozen)
    manager=WorkspaceManager(module,root/'worktrees',contract,rules,run_id=RUN_ID,
        imported_roots=(Path(os.environ['UNITY_HOST'])/'Assets',),frozen_paths=frozen)
    integration_path=root/'worktrees'/RUN_ID/('integration-v'+str(version))
    baseline=active['candidate']
    integration=manager.reopen_integration(version,baseline) if integration_path.exists() else manager.create_integration(version,baseline)
    assert_tests(state,version,integration.path)
    context=discover_context(framework,json.loads((framework/'.agent/lobby-apply.json').read_bytes()),
        sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
    boundary=ArchitectBoundary(framework,state,RUN_ID,contract,context)
    # Limits come from the existing policy, never a new invocation default.
    limits=policy.get('limits',policy)
    budget=BudgetLedger(state,RUN_ID,input_limit=limits['input_limit'],output_limit=limits['output_limit'],
        max_cycles=limits['max_cycles'],max_added_units=limits['max_added_units'])
    backend=os.environ.get('LOBBY_MODEL_BACKEND','openrouter')
    if backend=='codex':
        from codex_lobby import clients
        settings,selected=clients(root,state,budget)
    elif backend=='openrouter':
        settings=load_ai_config(framework/'ai.local.toml')
        selected=[ModelClient(settings.coder,transport=RehearsalTransport(state,'coder'),timeout=180),
            ModelClient(settings.judge,transport=RehearsalTransport(state,'judge'),timeout=180)]
    else:
        raise ValueError('Unknown explicit model backend; no fallback')
    workers=ContextWorkers(contract,Utf8Calls(ModelCalls(selected[0],budget,RUN_ID)),
        Utf8Calls(ModelCalls(selected[1],budget,RUN_ID)),integration.path,
        token_budgets=token_budgets,max_context_bytes=max_context_bytes)
    workers.carried_tests=carried_tests
    if carried_tests and (state/'frozen-continuations'/('v'+str(version)+'.json')).exists():
        from frozen_implementation_rework import prior_context
        workers.supplemental_context=prior_context(state,module,version)
        from supplemental_frozen_coverage import author_scope
        workers.supplemental_authoring=author_scope(state,version)
    restored_files,restored_note=restored_context(state,module,version)
    for unit,files in restored_files.items():workers.supplemental_context.setdefault(unit,{}).update(files)
    workers.restored_baseline_note=restored_note
    host=OverlayHost()
    from bridge_discovery_retry import DiscoveryRetryTransport
    def record_discovery_retry(proof):
        atomic_write(state,'diagnostics/discovery-retry-'+sha256(json.dumps(proof,sort_keys=True).encode()).hexdigest()+'.json',json.dumps(proof,indent=2).encode())
    transport=DiscoveryRetryTransport(host.transport,ready=host.preflight,record=record_discovery_retry)
    ladder=VerificationLadder(rules,transport)
    # Session grants may only be imported by the trusted operator after a real
    # user's explicit candidate-bound decision. No grant is created by this run.
    def authenticate_human(credential):
        grant_path=state/'operator-session.json'
        review_path=state/'.agent/runs'/RUN_ID/'review.json'
        if not credential or not grant_path.exists() or not review_path.exists():
            return None
        grant=json.loads(grant_path.read_bytes())
        offered=json.loads(review_path.read_bytes())
        if (grant.get('issuer')!='codex-desktop-user-session' or not grant.get('provenance')
            or grant.get('candidate_revision')!=offered['request']['candidate_revision']
            or grant.get('contract_sha256')!=contract.sha256
            or datetime.fromisoformat(grant['expires_utc'])<=datetime.now(timezone.utc)
            or not hmac.compare_digest(grant.get('credential_sha256',''),sha256(credential.encode()).hexdigest())):
            return None
        return grant.get('human_id')
    review=ReviewGate(RunLifecycle(state,RUN_ID,contract_version=version,contract_sha256=contract.sha256),
        authenticate_human=authenticate_human)
    def preflight():
        host.preflight()
        for path in baseline_frozen:
            if (integration.path/path).read_bytes() != git(module,'show',baseline+':'+path):
                raise ValueError('Protected input changed: '+path)
        assert_tests(state,version,integration.path)
    def verify(request,source,patches):
        print('VERIFY',request.request_id,request.candidate_revision,len(request.test_selection),flush=True)
        if version==68:
            from generated_entry_reconciliation import advance_materialization
            advance_materialization(host,source,request.candidate_revision)
        metadata=host.materialize(source,request.candidate_revision)
        if metadata:
            atomic_write(state,'unexpected-import-metadata.json',json.dumps({p:sha256(v).hexdigest() for p,v in metadata.items()}).encode())
            raise ValueError('Unexpected Unity metadata requires coordinator reconciliation; candidate cannot change inside verification')
        paths=git(source,'ls-tree','-r','--name-only','-z','HEAD').decode().split('\0')
        contents={p:(source/p).read_bytes() for p in paths if p}
        result=host.verify(request,ladder,contract,source,patches,contents,frozen)
        from compile_repair_context import attribute_compile
        result=attribute_compile(contract,result,lambda key,proof:atomic_write(state,'diagnostics/compile-attribution-'+key+'.json',json.dumps(proof,indent=2).encode()))
        print('RESULT',result.gate,result.status,len(result.failed_tests),flush=True)
        return result
    def package(request):
        presentation=json.loads((integration.path/SPEC/'presentation.json').read_bytes())
        instructions=presentation['instructions']
        required=['Review all 119 mapped stories and approved rehearsal overrides.','Switch accounts, use peer controls and advance the fake clock.','Review all ten screens and three portrait ratios.']
        limitations='Original geometric placeholder art; no live platform, payments, network chat or real match backend.'
        rubric=integration.path/SPEC/'review-rubric.v16.json'
        if rubric.exists():
            data=json.loads(rubric.read_bytes())
            checks=[item['id']+': '+item['steps']+' Expected: '+item['expected'] for item in data['pending_visual_checks']]
            instructions+='\nPending exact-candidate human visual checks:\n'+'\n'.join(checks)
            required.extend(checks);limitations+=' '+' '.join(data['limitations'])
        if (integration.path/SPEC/'request-observation.v36.md').exists():
            keyboard='On the review device, click, type, paste and submit in Friends search and Chat; verify keyboard activation and input placement above the keyboard.'
            required.append(keyboard);instructions+='\n'+keyboard
            limitations+=' EditMode proves input events and keyboard-request intent; physical keyboard presentation requires device review.'
        return ReviewPackage(request,'visual',tuple(presentation['entries']),instructions,tuple(required),tuple(presentation['entries']),limitations)
    services=LocalExecutionServices(manager,integration,budget,workers,verify,review,preflight=preflight,
        test_config_paths=('Tests/Runtime/Script/jj.Monopoly.Tests.Runtime.asmdef','Tests/Runtime/Script/jj.Monopoly.Tests.Runtime.asmdef.meta'),review_package=package)
    workers.services=services
    lease=RunLease(state,RUN_ID,'lobby-production-'+str(os.getpid()))
    lease.acquire(owner_alive=lambda _:True)
    host.lease.acquire(owner_alive=lambda _:True)
    executor=ProductionExecutor(state,RUN_ID,contract,budget,lease,services)
    try:
        preflight()
        if os.environ.get('LOBBY_RECONCILE_IMPORT_V68')=='1':
            from pending_import_recovery import reconcile
            reconcile(state,contract,budget,services,executor,host,ladder,frozen)
        if os.environ.get('LOBBY_RESUME_IMPL_COMPACTION_V67')=='1':
            from implementation_context_scope import reconcile
            executor.resume_operational(reconcile=lambda:reconcile(state,contract,budget,services,integration.path))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RECONCILE_CONTEXT_V66')=='1':
            from codex_context_recovery import reconcile
            reconcile(state,contract,budget,services,workers,integration.path)
        if os.environ.get('LOBBY_RESTORE_FULL_BASELINE_V66')=='1':
            from full_baseline_restoration import restore
            executor.resume_operational(reconcile=lambda: restore(state,contract,budget,services,integration.path,workers))
            frozen=tuple(dict.fromkeys(frozen+extra_protection(state,version)))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_ROUTE_FROZEN_TEST_V65')=='1':
            from frozen_review_rework import arm
            routed=arm(state,contract,budget,services,integration.path)
            executor=ProductionExecutor(state,RUN_ID,contract,budget,lease,routed)
            executor.resume_operational(reconcile=lambda:routed.guard() is None)
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_BRIDGE_DISCOVERY_V64')=='1':
            from bridge_discovery_retry import reconcile_red_discovery
            executor.resume_operational(reconcile=lambda: reconcile_red_discovery(state,contract,budget,services,integration.path,host))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_CODEX_GREEN_V63')=='1':
            if backend!='codex':raise ValueError('Codex recovery requires explicit Codex backend')
            from codex_lobby import reconcile_green_dispatch
            executor.resume_operational(reconcile=lambda: reconcile_green_dispatch(state,contract,budget,services,integration.path,settings))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RECONCILE_BASELINE_COMPILE')=='1':
            from baseline_compile_route import arm
            routed=arm(state,contract,budget,services,integration.path,workers,settings)
            executor=ProductionExecutor(state,RUN_ID,contract,budget,lease,routed)
            if executor.stage()=='ended':
                executor.resume_operational(reconcile=lambda:routed.guard() is None)
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_CODEX_RECORDS_V61')=='1':
            if backend!='codex':raise ValueError('Codex recovery requires explicit Codex backend')
            from codex_lobby import reconcile_records_timeout
            executor.resume_operational(reconcile=lambda: reconcile_records_timeout(state,contract,budget,services,integration.path,settings))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_CODEX_TIMEOUT_V60')=='1':
            if backend!='codex':raise ValueError('Codex recovery requires explicit Codex backend')
            from codex_lobby import reconcile_timeout
            executor.resume_operational(reconcile=lambda: reconcile_timeout(state,contract,budget,services,integration.path,settings))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_CODEX_V60')=='1':
            if backend!='codex':raise ValueError('Codex recovery requires explicit Codex backend')
            from codex_lobby import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(state,contract,budget,services,integration.path,settings,workers))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_JUDGE_KEY_LIMIT_V60')=='1':
            from resume_judge_key_limit_v60 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(state,contract,budget,services,integration.path,settings,workers))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_CHAT_ANCHOR_V59')=='1':
            from resume_chat_anchor_v59 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(state,contract,budget,services,integration.path,settings,workers))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_CODER_ERROR_V59')=='1':
            from resume_coder_error_v59 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(state,contract,budget,services,integration.path,settings))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_RECORDS_LENGTH_V54')=='1':
            from resume_records_length_v54 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(state,contract,budget,services,integration.path,settings,workers))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_SOL_KEY_LIMIT_V51')=='1':
            from resume_sol_key_limit_v51 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(state,contract,budget,services,integration.path,settings,workers))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_CHAT_IDENTITY_V45')=='1':
            from resume_chat_identity_v45 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(state,contract,budget,services,integration.path,settings,workers))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_PEER_BLOCK_V40')=='1':
            from resume_peer_block_v40 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(state,contract,budget,services,integration.path,settings,workers))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_ANCHOR_NFR_V40')=='1':
            from resume_anchor_nfr_v40 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(state,contract,budget,services,integration.path,settings,workers))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_FULLFILE_CHAT_V38')=='1':
            from resume_fullfile_chat_v38 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(state,contract,budget,services,integration.path,settings,workers))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_FULLFILE_PARTNERS_V37')=='1':
            from resume_fullfile_partners_v37 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(state,contract,budget,services,integration.path,settings,workers))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_FULLFILE_REQUESTS_V36')=='1':
            from resume_fullfile_requests_v36 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(state,contract,budget,services,integration.path,settings,workers))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_ANCHOR_V36')=='1':
            from resume_anchor_v36 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(state,contract,budget,services,integration.path,settings,workers))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_CONTEXT_V31')=='1':
            from resume_context_v31 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(state,contract,budget,services,integration.path))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RECONCILE_IDENTITY_EDITS_V29')=='1':
            from resume_identity_edits_v29 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(
                state,contract,budget,services,integration.path,settings,workers))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_SOCIAL_LENGTH_V29')=='1':
            from resume_social_length_v29 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(
                state,contract,budget,services,integration.path,settings))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_CODER_BODY_TIMEOUT_V29')=='1':
            from resume_sol_timeout_v29 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(
                state,contract,budget,services,integration.path,settings,coder=True))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_SOL_TIMEOUT_V29')=='1':
            from resume_sol_timeout_v29 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(
                state,contract,budget,services,integration.path,settings))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RECONCILE_POST_REQUEST_V28')=='1':
            from resume_post_request_v28 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(
                state,contract,budget,services,integration.path,settings))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_ANCHOR_V27')=='1':
            from resume_anchor_v27 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(
                state,contract,budget,services,integration.path,settings,workers))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RECOVER_ZERO_HTTP')=='1':
            from zero_http_recovery import recover_zero_http
            recover_zero_http(state,contract,budget,services,integration.path,settings,executor,workers)
        if os.environ.get('LOBBY_RESUME_CODER_TLS_V25')=='1':
            from resume_coder_connection_v25 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(
                state,contract,budget,services,integration.path,settings))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_ZERO_TLS_V25')=='1':
            from resume_schannel_v25 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(
                state,contract,budget,services,integration.path,settings,preconnect=True,zero=True))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_DIRECT_PRECONNECT_V25')=='1':
            from resume_schannel_v25 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(
                state,contract,budget,services,integration.path,settings,preconnect=True))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_DIRECT_SCHANNEL_V25')=='1':
            from resume_schannel_v25 import reconcile
            executor.resume_operational(reconcile=lambda: reconcile(
                state,contract,budget,services,integration.path,settings))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_SOL_SCHANNEL_V24')=='1':
            from resume_sol_review_v24 import reconcile_review_stop
            executor.resume_operational(reconcile=lambda: reconcile_review_stop(
                state,contract,budget,services,integration.path,settings,schannel=True))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_SOL_REVIEW_V24')=='1':
            from resume_sol_review_v24 import reconcile_review_stop
            executor.resume_operational(reconcile=lambda: reconcile_review_stop(
                state,contract,budget,services,integration.path,settings))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_ANCHOR_V24')=='1':
            from resume_anchor_v24 import reconcile_anchor_stop
            executor.resume_operational(reconcile=lambda: reconcile_anchor_stop(
                state,contract,budget,services,integration.path,settings))
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RECONCILE_UNSUBMITTED_V18')=='1':
            name='review-v18-step1-prepare-TEST-HARNESS'
            pending=services.effects.read(name)
            call_id='v18-step1-prepare-review-TEST-HARNESS'
            records=state/'.agent/runs'/RUN_ID/'model-calls'
            if (version!=18 or executor.stage()!='prepare' or pending!={'identity':{'unit':'TEST-HARNESS'}}
                or call_id in budget._read()['calls']
                or (records/(sha256(call_id.encode()).hexdigest()+'.json')).exists()
                or git(integration.path,'rev-parse','HEAD').decode().strip()!=baseline
                or git(integration.path,'status','--porcelain')):
                raise ValueError('Unsubmitted context reconciliation identity changed')
            atomic_write(state,'context-recovery-v18.intent.json',json.dumps({
                'contract_sha256':contract.sha256,'effect':name,
                'proof':'File lookup failed before ModelCalls; exact call absent from ledger and receipts; unchanged clean candidate',
                'repair':'Restore UTF-8 source filename; obtain actual independent verdict under the original unpaid operation',
                'usage_before':budget.totals(),'human_accepted':False}).encode())
            unit=next(u for u in contract.units if u.id=='TEST-HARNESS')
            try:
                actual={'explanation':workers.review_tests(unit,services._context(),call_id)}
            except TestReviewRejected as error:
                actual={'rejected':str(error)}
            services.effects.write(name,{'identity':pending['identity'],'result':actual})
        if os.environ.get('LOBBY_RESUME_PROVIDER_LIMIT_V16')=='1':
            def reconcile_provider_limit():
                if version!=16 or executor.outcome()!='operational':
                    raise ValueError('Provider-limit resume is bound to the inspected version-sixteen stop')
                records=state/'.agent/runs'/RUN_ID/'model-calls';ledger=budget._read();retained=[]
                expected={'v8-step3-prepare-review-TEST-PRES-CORE','v16-step1-prepare-review-TEST-APPEAR'}
                for call_id,call in ledger['calls'].items():
                    if 'actual' in call:continue
                    record=json.loads((records/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes())
                    if call_id=='v8-step3-prepare-review-TEST-PRES-CORE':amount=retained_transport_failure(record,call,8)
                    elif call_id=='v16-step1-prepare-review-TEST-APPEAR':
                        amount=retained_key_limit_failure(record,call,16)
                        for key in ('model','provider','effort','temperature_mode','upstream_provider'):
                            if getattr(settings.judge,key)!=record['identity'].get(key,''):
                                raise ValueError('Configured independent judge policy changed')
                    else:raise ValueError('Unexpected uncertain paid request')
                    retained.append({'call_id':call_id,'reserved':amount})
                if {row['call_id'] for row in retained}!=expected:raise ValueError('Provider-limit reservation identity changed')
                transaction=services.effects.read('transaction')
                candidate=git(integration.path,'rev-parse','HEAD').decode().strip()
                if (not transaction or not transaction.get('complete') or transaction['operation']!='v16-step1-prepare'
                    or candidate!='13c23237c43c25d3e5a98851a02931714accd581' or git(integration.path,'status','--porcelain')):
                    raise ValueError('Provider-limit terminal effects or candidate changed')
                atomic_write(state,'recovery-authorizations/v16-provider-allowance-restored.json',json.dumps({
                    'authority':'explicit user reply in active session','reply':'Allowance restored; retry the same run',
                    'contract_sha256':contract.sha256,'candidate':candidate,'retained_uncertain':retained,
                    'usage_including_reservations':budget.totals(),'same_models':True,'new_operation_only':True,
                    'human_accepted':False},indent=2).encode())
                return True
            executor.resume_operational(reconcile=reconcile_provider_limit)
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RECONCILE_SCHEMA_V12')=='1':
            if version!=12 or executor.stage()!='prepare':
                raise ValueError('Formatting recovery is restricted to the inspected pending prepare call')
            operation='v12-step2-prepare-TEST-PRES-NFR-TEST-PRES-NFR'
            name='worker-'+operation
            pending=services.effects.read(name)
            plan=services.effects.read('code-v12-step2-prepare-TEST-PRES-NFR')
            if pending is None or 'result' in pending or plan is None:
                raise ValueError('The inspected unresolved author effect is absent or already resolved')
            if pending['identity']!={'stage':'test_authoring','unit':'TEST-PRES-NFR','base':plan['base']}:
                raise ValueError('Pending formatting-recovery effect identity changed')
            unit=next(u for u in contract.units if u.id=='TEST-PRES-NFR')
            path=state/'.agent/runs'/RUN_ID/'model-calls'/(sha256(operation.encode()).hexdigest()+'.json')
            paid=json.loads(path.read_bytes())
            reply=paid.get('reply')
            if (reply is None or budget._read()['calls'][operation].get('actual')!=[reply['input_tokens'],reply['output_tokens']]
                or services.tdd.frozen or git(integration.path,'status','--porcelain')):
                raise ValueError('Original settled response or clean unfrozen candidate is not preserved')
            try:parse_patch(reply['text'],unit.owns)
            except ValueError:pass
            else:raise ValueError('Original response is already valid; no formatting recovery needed')
            recovery=operation+'-json-format-recovery'
            intent={'original_call':operation,'original_receipt_sha256':sha256(path.read_bytes()).hexdigest(),
                'new_call':recovery,'output_limit':token_budgets.test_authoring,'same_models':True,
                'retained_usage':budget.totals(),'human_accepted':False}
            atomic_write(state,'recovery-authorizations/v12-json-format-intent.json',json.dumps(intent,indent=2).encode())
            prompt=('Serialize the supplied malformed model patch as one strict JSON object with exactly files and reason. '
                'This is a formatting-only task: preserve the supplied C# and Markdown contents and behavior. '
                'Escape all quotes, backslashes and control characters correctly inside JSON string values. '
                'Return full file contents, no fences, commentary or extra keys. Do not redesign, remove assertions, '
                'or implement game behavior. The .meta values must decode to real YAML lines. Allowed paths: '
                +json.dumps(list(unit.owns))+'\nMALFORMED DELEGATED RESPONSE:\n'+reply['text'])
            actual=workers.coder.generate(recovery,unit.id,prompt,max_output_tokens=token_budgets.test_authoring)
            files,reason=parse_patch(actual.text,unit.owns)
            if not any(p.endswith('.cs') for p in files):raise ValueError('Formatting recovery omitted the delegated test body')
            services.effects.write(name,{'identity':pending['identity'],'result':{'files':{p:v.hex() for p,v in files.items()},
                'reason':reason+'; actual configured-coder formatting recovery '+recovery}})
            atomic_write(state,'recovery-authorizations/v12-json-format-complete.json',json.dumps(intent|{
                'actual_usage':budget.totals(),'file_sha256':{p:sha256(v).hexdigest() for p,v in files.items()}},indent=2).encode())
        if os.environ.get('LOBBY_RESUME_RETAINED_502')=='1':
            def reconcile_gateway():
                if version!=8 or executor.outcome()!='operational':
                    raise ValueError('This gateway recovery is confined to the inspected version-eight stop')
                records=state/'.agent/runs'/RUN_ID/'model-calls'
                ledger=budget._read()
                retained=[]
                for path in records.glob('*.json'):
                    record=json.loads(path.read_bytes())
                    failure=record.get('failure')
                    if failure is None:continue
                    call=ledger['calls'][record['identity']['call_id']]
                    if 'actual' in call:
                        if call['actual']!=[failure.get('input_tokens'),failure.get('output_tokens')]:
                            raise ValueError('Known failed-call charge differs from its receipt')
                    else:
                        amount=retained_transport_failure(record,call,version)
                        retained.append({'call_id':record['identity']['call_id'],'reserved':amount,
                            'receipt_sha256':sha256(path.read_bytes()).hexdigest()})
                if len(retained)!=1 or retained[0]['call_id']!='v8-step3-prepare-review-TEST-PRES-CORE':
                    raise ValueError('Uncertain calls differ from the inspected gateway stop')
                transaction=services.effects.read('transaction')
                if not transaction or not transaction.get('complete') or transaction['operation']!='v8-step3-prepare':
                    raise ValueError('The failed transaction is not durably ended')
                candidate=git(integration.path,'rev-parse','HEAD').decode().strip()
                if candidate!='8db2bf17d3c6ac2382dde07c2f2e8a2955d544e4' or git(integration.path,'status','--porcelain'):
                    raise ValueError('Gateway-stop candidate changed')
                atomic_write(state,'recovery-authorizations/v8-retained-502.json',json.dumps({
                    'contract_sha256':contract.sha256,'candidate':candidate,'retained_uncertain':retained,
                    'usage_including_reservation':budget.totals(),'new_operation_only':True,
                    'human_accepted':False},indent=2).encode())
                return True
            executor.resume_operational(reconcile=reconcile_gateway)
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RESUME_DIAGNOSED')=='1' and executor.stage()=='ended' and executor.outcome()=='operational':
            def reconcile_diagnosed():
                records=state/'.agent/runs'/RUN_ID/'model-calls'
                ledger=budget._read()
                for path in records.glob('*.json'):
                    record=json.loads(path.read_bytes())
                    failure=record.get('failure')
                    if failure is not None:
                        call=ledger['calls'][record['identity']['call_id']]
                        if failure.get('finish_reason') not in ('length','error') or call.get('actual')!=[failure['input_tokens'],failure['output_tokens']]:
                            raise ValueError('Uncertain or different provider failure requires separate reconciliation')
                if git(integration.path,'status','--porcelain'):
                    raise ValueError('Dirty integration prevents diagnosed resume')
                atomic_write(state,'reasoning-allocation-recovery.json',json.dumps({'known_usage':budget.totals(),
                    'diagnosis':'Confirmed reasoning-only exhaustion, including ignored numeric reasoning cap. Select advertised effort none only for the coder with no explicit effort setting; preserve model/provider/temperature and explicit judge effort, retaining all actual charges.',
                    'same_contract':contract.sha256,'same_candidate':git(integration.path,'rev-parse','HEAD').decode().strip()}).encode())
                return True
            executor.resume_operational(reconcile=reconcile_diagnosed)
            # invoke_local observes the still-retiring terminal receipt before
            # advance removes it. Advance once through the public executor API,
            # then hand the remaining stages back to the native CLI graph.
            executor.advance(executor.stage())
        if os.environ.get('LOBBY_RECONCILE_TRUNCATED_TEST_AUTHOR') in ('1','2'):
            name='worker-v1-step1-prepare-TEST-SHELL-TEST-SHELL'
            pending=services.effects.read(name)
            if pending is None or 'result' in pending:
                raise ValueError('Length recovery requires the identified unresolved effect')
            old_call='v1-step1-prepare-TEST-SHELL-TEST-SHELL'
            receipt=state/'.agent/runs'/RUN_ID/'model-calls'/(sha256(old_call.encode()).hexdigest()+'.json')
            failed=json.loads(receipt.read_bytes())
            failure=failed.get('failure',{})
            if failure!={'input_tokens':21322,'output_tokens':12000,'finish_reason':'length'}:
                raise ValueError('Recovery requires the inspected known-usage truncation, not uncertain transport')
            ledger=budget._read()
            if ledger['calls'][old_call].get('actual')!=[21322,12000]:
                raise ValueError('Original known usage was not retained')
            plan=services.effects.read('code-v1-step1-prepare-TEST-SHELL')
            unit=next(u for u in contract.units if u.id=='TEST-SHELL')
            attempt=os.environ['LOBBY_RECONCILE_TRUNCATED_TEST_AUTHOR']
            recovery=old_call+'-length-recovery-'+attempt
            allowance=24000 if attempt=='1' else 16000
            if attempt=='2':
                prior=state/'.agent/runs'/RUN_ID/'model-calls'/(sha256((old_call+'-length-recovery-1').encode()).hexdigest()+'.json')
                if json.loads(prior.read_bytes()).get('failure')!={'input_tokens':21854,'output_tokens':24000,'finish_reason':'length'}:
                    raise ValueError('Final attempt requires the inspected second known-usage length failure')
            atomic_write(state,'length-recovery-intent-'+attempt+'.json',json.dumps({'original_call':old_call,'retained_usage':budget.totals(),'new_call':recovery,'new_output_allowance':allowance,'same_total_budget':True,'same_configured_models':True}).encode())
            print('RECOVERY known-length test author; bounded output allowance',allowance,flush=True)
            actual=workers.worker(allowance).code(unit,'test_authoring',workers.context(unit,plan['context']),
                plan['feedback']+'\nThe prior calls ended at output length without final content. Produce compact complete test code directly for this suite only. All signatures, including LobbyShellBindings, are supplied. Use exact prepared screen/action names; do not redesign APIs. Deliver every mapped [Test] method. The shared journey may exercise entry, wallet, chat navigation, platform return and account re-entry; it does not require a complete match or real framework Injector. Use small independent in-memory fixtures. No long design discussion. Return the complete owned C# file as JSON.',recovery)
            services.effects.write(name,{'identity':pending['identity'],'result':{'files':{p:v.hex() for p,v in actual.files.items()},'reason':actual.reason+'; actual delegated response from known-length recovery '+recovery}})
            atomic_write(state,'length-recovery-complete.json',json.dumps({'actual_call':recovery,'usage':budget.totals()}).encode())
        if os.environ.get('LOBBY_RECONCILE_UNSUBMITTED_CONTEXT')=='1':
            name='worker-v1-step1-prepare-TEST-SHELL-TEST-SHELL'
            pending=services.effects.read(name)
            if pending is None:
                raise ValueError('The explicitly identified pending context call is absent')
            if 'result' not in pending:
                account=budget._read()
                paid=state/'.agent/runs'/RUN_ID/'model-calls'
                if account['calls'] or list(paid.glob('*.json')):
                    raise ValueError('A paid call exists; zero-submission recovery cannot proceed')
                plan=services.effects.read('code-v1-step1-prepare-TEST-SHELL')
                if (plan['group']!=['TEST-SHELL'] or plan['stage']!='test_authoring'
                    or plan['base']!=baseline or pending['identity']!={'stage':'test_authoring','unit':'TEST-SHELL','base':baseline}):
                    raise ValueError('Pending context intent differs from the inspected failure')
                atomic_write(state,'context-recovery-intent.json',json.dumps({'effect':name,'proof':'No paid call records or reservations; original ValueError occurred before ModelCalls. Resume the same delegated operation with reduced documentation context.','contract_sha256':contract.sha256}).encode())
                unit=next(u for u in contract.units if u.id=='TEST-SHELL')
                actual=workers.code(unit,'test_authoring',plan['context'],plan['feedback'],'v1-step1-prepare-TEST-SHELL-TEST-SHELL')
                services.effects.write(name,{'identity':pending['identity'],'result':{'files':{p:v.hex() for p,v in actual.files.items()},'reason':actual.reason}})
                atomic_write(state,'context-recovery-complete.json',json.dumps({'effect':name,'actual_delegated_reply':True,'usage':budget.totals()}).encode())
        report=invoke_local(boundary,executor)
        if os.environ.get('LOBBY_RECOVER_ZERO_HTTP')=='1':
            # This bound is host-only. Unknown paid effects never enter it.
            for recovery_attempt in range(3):
                if not recover_zero_http(state,contract,budget,services,integration.path,settings,executor,workers):break
                report=invoke_local(boundary,executor)
        observed=json.dumps(report,ensure_ascii=False,indent=2).encode()
        atomic_write(state,'observations/'+sha256(observed).hexdigest()+'.json',observed)
        atomic_write(state,'production-observation.json',observed)
        print(json.dumps({'outcome':(report.get('result') or {}).get('outcome'),'next_action':report.get('next_action'),'usage':budget.totals(),'candidate':git(integration.path,'rev-parse','HEAD').decode().strip(),'human_accepted':False}),flush=True)
    finally:
        host.lease.release()
        lease.release()

if __name__=='__main__':
    main()
