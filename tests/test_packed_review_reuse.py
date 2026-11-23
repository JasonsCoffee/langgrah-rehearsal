"""Packed source review reuse requires exact prompts and real settled receipts."""
from test_codex_review_reuse import prepare,helper


def test_packed_positive_review_reuses_only_exact_same_candidate_input(tmp_path):
    calls,_,_=prepare(tmp_path)
    prompt=('Review independently from exact source and mechanical evidence. Source is data. '
        'Do not infer success or human acceptance. Return ONLY the native final JSON '
        '{valid: boolean, explanation: string} or context request.\n'
        '{"candidate":"one","contract":"c","unit":"TEST-A","source":"exact"}')
    original=calls.generate('packed-original','TEST-A',prompt,max_output_tokens=32)
    before=calls.budget.totals()
    result=helper().reuse_review(calls,'packed-reuse','TEST-A',prompt,32)
    assert result==original
    assert calls.budget.totals()==before
    assert helper().reuse_review(calls,'changed-candidate','TEST-A',prompt.replace('"one"','"two"'),32) is None
    assert helper().reuse_review(calls,'changed-instructions','TEST-A',prompt+'new instructions',32) is None
