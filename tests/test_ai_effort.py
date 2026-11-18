from test_ai_models import config, response
from unity_coder.core.ai_models import load_ai_config, ModelClient


def test_explicit_judge_effort_is_preserved(tmp_path):
    path=config(tmp_path)
    path.write_text(path.read_text().replace('[judge]','[judge]\neffort="medium"'))
    settings=load_ai_config(path)
    seen=[]
    def send(url,key,payload,timeout):
        seen.append(payload); return response()
    ModelClient(settings.judge,transport=send).generate('Review',max_output_tokens=512)
    assert seen[0]['reasoning']=={'effort':'medium'}
    assert seen[0]['temperature']==0
