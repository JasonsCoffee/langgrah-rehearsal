"""Offline checks of rehearsal request allocation and diagnostic redaction."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from rehearsal_model_transport import RehearsalTransport

with TemporaryDirectory(prefix='lobby-model-transport-') as temporary:
    root=Path(temporary)
    captured=[]
    def fake_send(url,key,payload,timeout):
        captured.append(payload)
        return {'id':'offline','model':payload['model'],'provider':'alibaba',
            'usage':{'prompt_tokens':10,'completion_tokens':20,'completion_tokens_details':{'reasoning_tokens':12}},
            'choices':[{'finish_reason':'stop','message':{'content':'{"ok":true}','reasoning':'private reasoning text'}}]}
    original={'model':'configured-coder','max_completion_tokens':16000,'temperature':0,
        'provider':{'only':['alibaba'],'allow_fallbacks':False},'messages':[{'role':'user','content':'fixture'}]}
    with patch('rehearsal_model_transport.send_chat',fake_send):
        RehearsalTransport(root,'coder')('unused','secret-key',original,180)
        explicit=original|{'reasoning':{'effort':'medium'}}
        RehearsalTransport(root,'judge')('unused','secret-key',explicit,180)
    assert 'reasoning' not in original
    assert captured[0]['reasoning']=={'effort':'none'}
    assert captured[0]['provider']==original['provider']
    assert captured[0]['model']==original['model']
    assert captured[1]['reasoning']=={'effort':'medium'}
    artifacts='\n'.join(path.read_text(encoding='utf-8') for path in root.rglob('*.json'))
    assert 'secret-key' not in artifacts and 'private reasoning text' not in artifacts
    summaries=[json.loads(p.read_bytes()) for p in root.rglob('*.response.json')]
    assert all(s['choices'][0]['content_characters']==11 for s in summaries)
    assert all(s['usage']['completion_tokens_details']['reasoning_tokens']==12 for s in summaries)
print('PASS configured identities/routing/temperature, explicit judge effort, bounded coder reasoning and credential/reasoning redaction')
