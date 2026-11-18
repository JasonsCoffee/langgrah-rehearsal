"""Run-wide pre-dispatch reservations with conservative uncertain accounting."""
from collections.abc import Mapping
import json
from pathlib import Path
from .journal import run_prefix
from .storage import atomic_write, file_guard
from .ownership import confined_path

class BudgetExhausted(ValueError):
    def __init__(self, input_tokens: int, output_tokens: int) -> None:
        super().__init__('Run token budget exhausted')
        self.input_tokens, self.output_tokens = input_tokens, output_tokens

def _amounts(input_tokens: int, output_tokens: int) -> None:
    if any(type(n) is not int or n < 0 for n in (input_tokens,output_tokens)):
        raise ValueError('Token amounts must be nonnegative integers')

class BudgetLedger:
    def __init__(self, root: Path, run_id: str, *, input_limit: int, output_limit: int,
                 max_cycles: int, max_added_units: int) -> None:
        values=(input_limit,output_limit,max_cycles,max_added_units)
        if any(type(n) is not int or n < 1 for n in values):
            raise ValueError('Budget limits must be positive integers')
        self.root=root
        prefix=run_prefix(run_id)
        self.path=prefix+'/budget.json'
        self.guard=prefix+'/budget.guard'
        self.limits=list(values)

    def _read(self) -> dict:
        path=confined_path(self.root,self.path)
        if not path.exists():
            return {'limits':self.limits,'cycles':{},'calls':{}}
        state=json.loads(path.read_bytes())
        if state['limits']!=self.limits:
            raise ValueError('Run budget limits cannot change on resume')
        return state

    def _save(self,state: dict) -> None:
        atomic_write(self.root,self.path,json.dumps(state,sort_keys=True).encode())

    @staticmethod
    def _totals(state: dict, units: tuple[str,...] | None = None) -> tuple[int,int]:
        calls=[c for c in state['calls'].values() if units is None or c['unit'] in units]
        return (sum(c.get('actual',c['reserved'])[0] for c in calls),
                sum(c.get('actual',c['reserved'])[1] for c in calls))

    def totals(self) -> tuple[int,int]:
        with file_guard(self.root,self.guard):
            return self._totals(self._read())

    def unit_totals(self,unit_id: str) -> tuple[int,int]:
        with file_guard(self.root,self.guard):
            state=self._read()
            latest=state['cycles'][str(len(state['cycles']))]
            if unit_id not in latest['lineages']:
                raise ValueError('Unknown budget lineage')
            return self._totals(state,tuple(latest['lineages'][unit_id]))

    def begin_cycle(self,contract_version: int,contract_sha256: str,
                    lineages: Mapping[str,tuple[str,...]]) -> None:
        if type(contract_version) is not int or not contract_sha256 or not lineages:
            raise ValueError('Cycle identity and unit lineage required')
        normalized={u:list(history) for u,history in lineages.items()}
        if any(not u or not history or history[-1]!=u or len(history)!=len(set(history))
               or any(not member for member in history) for u,history in normalized.items()):
            raise ValueError('Invalid lineage')
        with file_guard(self.root,self.guard):
            state=self._read();cycles=state['cycles']
            value={'sha256':contract_sha256,'lineages':normalized}
            key=str(contract_version)
            if key in cycles:
                if cycles[key]!=value:
                    raise ValueError('Cycle identity was changed')
                return
            if state.get('stopped'):
                raise ValueError('Stopped run cannot begin another cycle')
            if contract_version!=len(cycles)+1 or contract_version>self.limits[2]:
                raise ValueError('Cycle budget exceeded or version skipped')
            prior=cycles[str(len(cycles))]['lineages'] if cycles else {}
            if prior and (not prior.keys()<=normalized.keys() or len(normalized.keys()-prior.keys())>self.limits[3]):
                raise ValueError('Unit history removed or growth exceeded')
            if any(normalized[u]!=history for u,history in prior.items()):
                raise ValueError('Existing lineage cannot reset')
            for u,history in normalized.items():
                if any(member not in normalized for member in history):
                    raise ValueError('Unknown predecessor')
                for member in history[:-1]:
                    if not set(normalized[member])<=set(history):
                        raise ValueError('Transitive lineage missing')
            cycles[key]=value;self._save(state)

    def reserve(self,call_id: str,unit_id: str,input_tokens: int,output_tokens: int) -> None:
        _amounts(input_tokens,output_tokens)
        if not call_id:
            raise ValueError('Call identity required')
        with file_guard(self.root,self.guard):
            state=self._read();version=len(state['cycles'])
            if state.get('stopped'):
                raise ValueError('Run budget is stopped; reconcile existing usage only')
            if not version or unit_id not in state['cycles'][str(version)]['lineages']:
                raise ValueError('Unknown unit/cycle')
            value={'unit':unit_id,'version':version,'reserved':[input_tokens,output_tokens]}
            if call_id in state['calls']:
                prior=state['calls'][call_id]
                if any(prior[k]!=v for k,v in value.items()):
                    raise ValueError('Call identity reused')
                return
            used=self._totals(state)
            if used[0]+input_tokens>self.limits[0] or used[1]+output_tokens>self.limits[1]:
                raise BudgetExhausted(input_tokens,output_tokens)
            state['calls'][call_id]=value;self._save(state)

    def reconcile(self,call_id: str,input_tokens: int,output_tokens: int) -> None:
        _amounts(input_tokens,output_tokens)
        with file_guard(self.root,self.guard):
            state=self._read()
            if call_id not in state['calls']:
                raise ValueError('No pre-dispatch reservation')
            call=state['calls'][call_id];actual=[input_tokens,output_tokens]
            if 'actual' in call and call['actual']!=actual:
                raise ValueError('Conflicting usage reconciliation')
            # Charge overruns truthfully; all later reservations see exhaustion.
            call['actual']=actual;self._save(state)

    def stop_for_budget(self, *, input_tokens: int = 0, output_tokens: int = 0,
                        cycle_exhausted: bool = False) -> tuple[int, int]:
        """Atomically stop further dispatch and retain the exhaustion snapshot."""
        _amounts(input_tokens,output_tokens)
        with file_guard(self.root,self.guard):
            state=self._read()
            if state.get('stopped'):
                return tuple(state['stopped']['used'])
            used=self._totals(state)
            if cycle_exhausted and len(state['cycles']) < self.limits[2]:
                raise ValueError('Cycle allowance remains')
            if (not cycle_exhausted and used[0]<self.limits[0] and used[1]<self.limits[1]
                and used[0]+input_tokens<=self.limits[0] and used[1]+output_tokens<=self.limits[1]):
                raise ValueError('Available allowance cannot be reported as exhaustion')
            state['stopped']={'reason':'budget','used':list(used)}
            self._save(state)
            return used
