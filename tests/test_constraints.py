"""Accepted constraints preserve human text and evidence across capped history."""
from dataclasses import replace
from hashlib import sha256
import json
import pytest
from unity_coder.core.constraints import LearnedConstraint, accepted_constraints, read_constraints


class Review:
    def __init__(self, original=b'Human rules\r\n', decision='accept'):
        self.record = dict(decision=decision, reviewer='human', contract_version=1,
            request={'candidate_revision':'candidate', 'contract_version':1},
            files={'AGENTS.md':sha256(original).hexdigest()}, evidence_refs=['evidence/tests.json'])
    def state(self):
        return self.record


def item(text='Preserve identity', version=1):
    return LearnedConstraint(text, version, 'R1', 'evidence/tests.json')


def render(original, entries, version=1):
    review=Review(original)
    review.record['contract_version']=version
    review.record['request']['contract_version']=version
    return accepted_constraints(review, candidate_revision='candidate',
                               contract_version=version, original=original, entries=entries)


@pytest.mark.parametrize('decision', ['pending','implementation','contract'])
def test_automated_green_and_rework_cannot_flush(decision):
    with pytest.raises(ValueError):
        accepted_constraints(Review(decision=decision), candidate_revision='candidate',
                             contract_version=1, original=b'Human rules\r\n', entries=(item(),))


def test_stale_approval_and_changed_human_text_cannot_flush():
    for candidate, original, version in [('other',b'Human rules\r\n',1),
        ('candidate',b'edited',1), ('candidate',b'Human rules\r\n',2)]:
        with pytest.raises(ValueError):
            accepted_constraints(Review(), candidate_revision=candidate,
                                 contract_version=version, original=original, entries=(item(),))


def test_preserves_unmanaged_bytes_and_reconfirmation_is_idempotent():
    original=b'Human rules\r\n'
    first=render(original,(item(),))
    assert first.startswith(original)
    wrapped=first+b'\r\nHuman footer\r\n'
    second=render(wrapped,(item('  PRESERVE   identity  ',2),),2)
    active, archive=read_constraints(second)
    assert second.startswith(original) and second.endswith(b'\r\nHuman footer\r\n')
    assert len(active)==1 and not archive
    assert active[0]['confirmed']==2
    assert len(active[0]['provenance'])==2
    assert render(second,(item('  PRESERVE   identity  ',2),),2)==second


def test_caps_at_forty_and_archives_oldest_without_loss():
    first=render(b'',tuple(item(f'rule {i}') for i in range(40)))
    second=render(first,(item('rule 40',2),),2)
    active, archive=read_constraints(second)
    assert len(active)==40 and len(archive)==1
    assert {e['statement'] for e in active+archive}=={f'rule {i}' for i in range(41)}
    revived=render(second,(item(archive[0]['statement'],3),),3)
    active2, archive2=read_constraints(revived)
    assert len(active2)==40 and len(archive2)==1
    assert any(e['statement']==archive[0]['statement'] and e['confirmed']==3 for e in active2)


@pytest.mark.parametrize('bad', [LearnedConstraint('',1,'R1','evidence/tests.json'),
    LearnedConstraint('rule',1,'','evidence/tests.json'),
    LearnedConstraint('rule',1,'R1','missing'),
    LearnedConstraint('rule',2,'R1','evidence/tests.json')])
def test_missing_or_unconfirmed_provenance_is_rejected(bad):
    with pytest.raises(ValueError): render(b'',(bad,))


def test_malformed_managed_block_is_not_overwritten():
    first=render(b'Human', (item(),))
    for malformed in (first.replace(b'"active":',b'"broken":'), first+first):
        with pytest.raises(ValueError): render(malformed,(item(),))


def test_empty_constraints_preserve_original_exactly():
    assert render(b'Human rules without newline',())==b'Human rules without newline'
