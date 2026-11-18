"""Durable reservations must bound parallel calls before dispatch."""
from concurrent.futures import ThreadPoolExecutor
import pytest
from unity_coder.core.budget import BudgetLedger

def ledger(root):
    return BudgetLedger(root,'run',input_limit=100,output_limit=50,max_cycles=3,max_added_units=2)

def start(root):
    b=ledger(root)
    b.begin_cycle(1,'hash1',{'A':('A',)})
    return b

def test_reservations_survive_restart_and_uncertain_usage(tmp_path):
    b=start(tmp_path)
    b.reserve('call1','A',80,40)
    with pytest.raises(ValueError): ledger(tmp_path).reserve('call2','A',21,1)
    assert ledger(tmp_path).totals()==(80,40)

def test_parallel_reservation_cannot_overspend(tmp_path):
    start(tmp_path)
    def claim(i):
        try: ledger(tmp_path).reserve(str(i),'A',60,30); return True
        except ValueError: return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(claim,range(2)))==1

def test_actual_usage_reconciles_once_and_releases_unused_allowance(tmp_path):
    b=start(tmp_path);b.reserve('c','A',80,40)
    b.reconcile('c',30,10)
    b.reconcile('c',30,10)
    assert ledger(tmp_path).totals()==(30,10)
    with pytest.raises(ValueError): b.reconcile('c',31,10)
    b.reserve('d','A',70,40)
    assert b.totals()==(100,50)

def test_observed_overrun_is_charged_and_stops_new_work(tmp_path):
    b=start(tmp_path);b.reserve('c','A',80,40);b.reconcile('c',110,55)
    assert b.totals()==(110,55)
    with pytest.raises(ValueError): b.reserve('next','A',1,1)

def test_cycle_and_migration_preserve_usage_and_call_identity(tmp_path):
    b=start(tmp_path);b.reserve('c','A',20,10)
    b.begin_cycle(2,'hash2',{'A':('A',),'B':('A','B')})
    assert ledger(tmp_path).unit_totals('B')==(20,10)
    with pytest.raises(ValueError): b.reserve('c','B',20,10)
    assert b.totals()==(20,10)

def test_cycles_growth_and_lineage_cannot_reset(tmp_path):
    b=start(tmp_path)
    with pytest.raises(ValueError): b.begin_cycle(3,'hash3',{'A':('A',)})
    with pytest.raises(ValueError): b.begin_cycle(1,'changed',{'A':('A',)})
    with pytest.raises(ValueError): b.begin_cycle(2,'hash2',{'A':('A',),'B':('B',),'C':('C',),'D':('D',)})
    with pytest.raises(ValueError): b.begin_cycle(2,'hash2',{'B':('B',)})
    b.begin_cycle(2,'hash2',{'A':('A',)})
    b.begin_cycle(3,'hash3',{'A':('A',)})
    with pytest.raises(ValueError): b.begin_cycle(4,'hash4',{'A':('A',)})

def test_resume_cannot_raise_limits(tmp_path):
    start(tmp_path)
    with pytest.raises(ValueError):
        BudgetLedger(tmp_path,'run',input_limit=200,output_limit=50,max_cycles=3,max_added_units=2).totals()

@pytest.mark.parametrize('values',[(-1,1),(1,-1),(True,1)])
def test_invalid_reservations_are_rejected(tmp_path,values):
    b=start(tmp_path)
    with pytest.raises(ValueError): b.reserve('c','A',*values)
