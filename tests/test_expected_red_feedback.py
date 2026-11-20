"""Expected baseline Red is not a repair verdict against the new proposal."""
from test_lobby_compile_attribution import module


def test_expected_red_does_not_duplicate_every_baseline_failure_into_repair():
    state={'verification':{'request':{'contract_sha256':'same','request_id':'v65-step2-red'},
        'gate':'tests','status':'failed','behavioral':True,'test_result':{'messages':['expected stub failure']}}}
    assert module().mechanical_feedback(state,'same')==''


def test_real_green_assertion_messages_are_forwarded():
    state={'verification':{'request':{'contract_sha256':'same','request_id':'v65-step5-verify'},
        'gate':'tests','status':'failed','behavioral':True,'test_result':{'messages':['actual wallet assertion']}}}
    assert 'actual wallet assertion' in module().mechanical_feedback(state,'same')
