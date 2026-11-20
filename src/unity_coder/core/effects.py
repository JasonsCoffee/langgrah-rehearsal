"""Host-owned apply intents and completed-call receipts for stage recovery."""
from hashlib import sha256
import json
from pathlib import Path
from collections.abc import Callable

from .ai_models import ModelError
from .ownership import confined_path
from .storage import atomic_write, file_guard
from .workspaces import WorkspaceManager, Workspace, WorkspaceCandidate, git


class DurableEffects:
    def __init__(self, root: Path, prefix: str, manager: WorkspaceManager, integration: Workspace) -> None:
        self.root,self.prefix,self.manager,self.integration=root,prefix,manager,integration

    def read(self, name: str) -> dict | None:
        path=confined_path(self.root,self.prefix+'/'+name+'.json')
        return json.loads(path.read_bytes()) if path.exists() else None

    def write(self, name: str, record: dict) -> None:
        atomic_write(self.root,self.prefix+'/'+name+'.json',json.dumps(record,sort_keys=True).encode())

    def call(self, name: str, identity: dict, invoke: Callable[[], dict]) -> dict:
        with file_guard(self.root,self.prefix+'/'+name+'.call.guard'):
            identity=json.loads(json.dumps(identity))
            record=self.read(name)
            if record is not None:
                if record['identity']!=identity:raise ValueError('Effect call identity changed')
                if 'result' not in record:raise ModelError('Interrupted call requires owner/usage reconciliation; no replay')
                return record['result']
            self.write(name,{'identity':identity})
            result=invoke()
            self.write(name,{'identity':identity,'result':result})
            return result

    def reconcile_call(self, name: str, identity: dict, *,
                       reconcile: Callable[[dict], dict | None]) -> None:
        """Resolve an exact pending intent through the trusted owner's validator.

        The callback must reconcile usage/reservations, delegated result bytes and
        candidate identity. Hashes bind its evidence, not its semantic correctness.
        Models cannot select this callback; normal admission and review follow.
        """
        path = self.prefix+'/'+name+'.json'
        identity = json.loads(json.dumps(identity))
        with file_guard(self.root,self.prefix+'/'+name+'.call.guard'):
            target = confined_path(self.root,path)
            original = target.read_bytes()
            record = json.loads(original)
            if record.get('identity') != identity or 'result' in record:
                raise ValueError('Only the exact pending effect can be reconciled')
            resolution = reconcile(json.loads(original))
            if (not isinstance(resolution,dict) or set(resolution) != {'result','evidence'}
                or not isinstance(resolution['result'],dict)
                or not isinstance(resolution['evidence'],dict) or not resolution['evidence']):
                raise ValueError('Owner reconciliation requires result and hashed evidence')
            # Canonicalize before publication; callbacks cannot smuggle mutable
            # non-JSON values into the durable operation receipt.
            resolution = json.loads(json.dumps(resolution,allow_nan=False))
            for evidence, digest in resolution['evidence'].items():
                if sha256(confined_path(self.root,evidence).read_bytes()).hexdigest() != digest:
                    raise ValueError('Owner reconciliation evidence changed')
            if target.read_bytes() != original:
                raise ValueError('Pending effect changed during reconciliation')
            self.write(name,dict(record,result=resolution['result'],reconciliation={
                'pending_sha256':sha256(original).hexdigest(),'evidence':resolution['evidence']}))

    def tree(self, revision: str) -> dict[str,str]:
        paths=git(self.integration.path,'ls-tree','-r','--name-only','-z',revision).decode().split('\0')
        return {p:sha256(git(self.integration.path,'show',revision+':'+p)).hexdigest() for p in paths if p}

    def resolve_apply(self, name: str, record: dict, head: str) -> str:
        if record.get('after'):
            return record['after']
        if head==record['before']:return head
        parents=git(self.integration.path,'rev-list','--parents','-n','1',head).decode().split()
        if parents!=[head,record['before']] or self.tree(head)!=record['expected']:
            raise ValueError('Candidate conflicts with pending apply intent')
        record['after']=head
        self.write(name,record)
        return head

    def reconciles(self, before: str, head: str) -> bool:
        folder=confined_path(self.root,self.prefix)
        records=[(p.stem,json.loads(p.read_bytes())) for p in folder.glob('apply-*.json')] if folder.exists() else []
        current=before
        for _ in range(len(records)+1):
            if current==head:return True
            matches=[(n,r) for n,r in records if r['before']==current and r.get('after')!=current]
            if len(matches)!=1:return False
            name,record=matches[0]
            current=self.resolve_apply(name,record,head)
        return False

    def apply(self, name: str, candidate: WorkspaceCandidate) -> str:
        name='apply-'+name
        head=git(self.integration.path,'rev-parse','HEAD').decode().strip()
        identity={'unit':candidate.unit_id,'contract':candidate.contract_sha256,'base':candidate.base_revision,
                  'dependencies':dict(candidate.dependencies),
                  'changes':{p:v.hex() if v is not None else None for p,v in candidate.changes.items()}}
        record=self.read(name)
        if record:
            if record['identity']!=identity:raise ValueError('Apply intent identity changed')
            after=self.resolve_apply(name,record,head)
            if record.get('after'):
                git(self.integration.path,'merge-base','--is-ancestor',after,head)
                return after
        else:
            expected=self.tree(head)
            for path,value in candidate.changes.items():
                if value is None:expected.pop(path,None)
                else:expected[path]=sha256(value).hexdigest()
            record={'identity':identity,'before':head,'expected':expected}
            self.write(name,record)
        after=self.manager.integrate(self.integration,candidate,candidate.dependencies)
        if self.tree(after)!=record['expected']:raise ValueError('Applied tree differs from intended content')
        record['after']=after
        self.write(name,record)
        return after
