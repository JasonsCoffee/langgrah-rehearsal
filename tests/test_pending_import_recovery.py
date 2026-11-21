"""An interrupted import may resolve only its exact unsubmitted verification."""
import importlib.util
from pathlib import Path
import copy
import pytest


def module():
    path=Path('openspec/changes/rehearse-monopoly-game-lobby/pending_import_recovery.py')
    spec=importlib.util.spec_from_file_location('pending_import_recovery',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def fixture():
    m=module();request={'request_id':m.OPERATION,'candidate_revision':m.CANDIDATE,'contract_version':68,'contract_sha256':m.CONTRACT}
    executor={'stage':'verify','pending':m.OPERATION,'contract_version':68,'contract_sha256':m.CONTRACT}
    transaction={'stage':'verify','operation':m.OPERATION,'complete':False}
    return m,executor,transaction,{'identity':{'request':request}}


def test_exact_pending_effect_with_zero_submissions_can_be_reconciled():
    m,executor,transaction,effect=fixture();m.validate_pending(executor,transaction,effect,False)


@pytest.mark.parametrize('bad',['candidate','operation','complete','result','submitted'])
def test_other_effects_and_existing_submissions_are_not_replayed(bad):
    m,executor,transaction,effect=fixture();effect=copy.deepcopy(effect)
    if bad=='candidate':effect['identity']['request']['candidate_revision']='other'
    if bad=='operation':transaction['operation']='other'
    if bad=='complete':transaction['complete']=True
    if bad=='result':effect['result']={}
    with pytest.raises(ValueError):m.validate_pending(executor,transaction,effect,bad=='submitted')
