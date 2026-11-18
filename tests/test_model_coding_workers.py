"""Frozen configured-model composition with deterministic paid-call fakes."""

from types import SimpleNamespace
import pytest
from test_contracts import bundle, load
from unity_coder.core.coding_workers import ModelCodingWorkers


class Calls:
    def __init__(self,role,model,reply):
        self.client=SimpleNamespace(config=SimpleNamespace(role=role,model=model))
        self.reply=reply
        self.prompts=[]
    def generate(self,call_id,unit_id,prompt,*,max_output_tokens):
        self.prompts.append((call_id,unit_id,prompt,max_output_tokens))
        return SimpleNamespace(text=self.reply)


def test_roles_and_independent_model_are_enforced(bundle):
    contract=load(bundle)
    with pytest.raises(ValueError):
        ModelCodingWorkers(contract,Calls("coder","same",""),Calls("judge","same",""))
    with pytest.raises(ValueError):
        ModelCodingWorkers(contract,Calls("judge","one",""),Calls("coder","two",""))


def test_coder_response_is_parsed_and_owned_before_file_tools(bundle):
    contract=load(bundle)
    coder=Calls("coder","one",'{"files":{"shared.txt":"bad"},"reason":"change"}')
    workers=ModelCodingWorkers(contract,coder,Calls("judge","two",""))
    with pytest.raises(ValueError):
        workers.code(contract.units[1],"green",{contract.spec.path:"criterion"},"repair","operation")
    assert coder.prompts[0][0]=="operation"


@pytest.mark.parametrize("reply", ['{"valid":false,"explanation":"No assertion"}', '{"valid":true,"explanation":""}'])
def test_test_review_must_explicitly_validate_coverage(bundle,reply):
    contract=load(bundle)
    judge=Calls("judge","two",reply)
    workers=ModelCodingWorkers(contract,Calls("coder","one",""),judge)
    with pytest.raises(ValueError):
        workers.review_tests(contract.units[0],{contract.spec.path:"criterion"},"review")


def test_independent_test_review_retains_explanation(bundle):
    contract=load(bundle)
    judge=Calls("judge","two",'{"valid":true,"explanation":"Assertions cover the criterion"}')
    workers=ModelCodingWorkers(contract,Calls("coder","one",""),judge)
    assert workers.review_tests(contract.units[0],{contract.spec.path:"criterion"},"review")=="Assertions cover the criterion"
    assert "coder notes" not in judge.prompts[0][2]
