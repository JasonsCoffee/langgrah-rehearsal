"""JSON-normalized native effect identity must survive recovery."""
from test_lobby_context_recovery import Effects,module


def test_request_tuples_match_the_native_json_receipt():
    identity={'request':{'test_selection':('A','B')},'unit':'SHELL'}
    persisted={'request':{'test_selection':['A','B']},'unit':'SHELL'}
    effects=Effects({'identity':persisted});calls=[]
    def judge():calls.append('actual');return 'implementation','real reason'
    module().recover_judge_effect(effects,'judge-current',identity,False,judge)
    assert calls==['actual']
    assert effects.record['identity']==persisted
