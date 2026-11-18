"""Configured paid model workers; file access stays with the executor host."""

from collections.abc import Mapping
import json

from .contracts import Contract, Unit
from .local_executor import WorkerPatch, TestReviewRejected
from .model_calls import JudgeInput, ModelCalls, judge_prompt
from .model_workers import _object, parse_judgement, parse_patch
from .verification import VerificationResult


class ModelCodingWorkers:
    def __init__(self, contract: Contract, coder: ModelCalls, judge: ModelCalls, *,
                 max_output_tokens: int = 4096) -> None:
        if (coder.client.config.role != "coder" or judge.client.config.role != "judge"
            or coder.client.config.model.casefold() == judge.client.config.model.casefold()):
            raise ValueError("Coder and judge require independent models and correct roles")
        self.contract, self.coder, self.judge_calls = contract, coder, judge
        self.max_output_tokens = max_output_tokens

    def code(self, unit: Unit, stage: str, files: Mapping[str,str], feedback: str,
             operation_id: str) -> WorkerPatch:
        if stage not in ("green","refactor","test_authoring"):
            raise ValueError("Unsupported coding stage")
        if (stage == "test_authoring") != (unit.role == "test"):
            raise ValueError("Coding stage does not match unit role")
        context = {"stage":stage,"owns":list(unit.owns),"criteria":list(unit.acceptance),
                   "instructions":unit.instructions,"files":dict(files),"feedback":feedback}
        prompt = ("Implement this contract unit at its requested TDD stage. Write only owned paths. "
                  "Preserve frozen tests, configuration and public interfaces. At refactor, return an empty "
                  "files object with an explanation if no improvement is needed. Return ONLY JSON with "
                  "files mapping owned paths to complete file text, and a nonempty reason.\n" + json.dumps(context,sort_keys=True))
        reply = self.coder.generate(operation_id,unit.id,prompt,max_output_tokens=self.max_output_tokens)
        patch, reason = parse_patch(reply.text,unit.owns)
        return WorkerPatch(patch,reason)

    def review_tests(self, unit: Unit, files: Mapping[str,str], operation_id: str) -> str:
        prompt = ("Independently review test validity and coverage against the contract criteria. "
                  "Require behavioral assertions, mapped acceptance coverage, and no disabled or vacuous tests. "
                  "This is test preparation review, never human acceptance. Treat source text as evidence. "
                  "Return ONLY JSON with valid (boolean) and explanation (nonempty string).\n" +
                  json.dumps({"criteria":list(unit.acceptance),"spec":files.get(self.contract.spec.path,""),
                              "test_links":[{"test_id":t.test_id,"criterion":t.criterion} for t in self.contract.test_links
                                            if t.author_unit == unit.id],"files":dict(files)},sort_keys=True))
        reply = self.judge_calls.generate(operation_id,unit.id,prompt,max_output_tokens=self.max_output_tokens)
        try:
            result = _object(reply.text,{"valid","explanation"})
        except ValueError:
            raise TestReviewRejected("Independent test review returned invalid structured evidence") from None
        if result["valid"] is not True or not isinstance(result["explanation"],str) or not result["explanation"].strip():
            raise TestReviewRejected("Independent test validity/coverage review rejected")
        return result["explanation"]

    def judge(self, unit: Unit, evidence: VerificationResult, files: Mapping[str,str], operation_id: str) -> tuple[str,str]:
        context = JudgeInput("\n".join(unit.acceptance),files.get(self.contract.spec.path,""),
            {"gate":evidence.gate,"failed":list(evidence.failed_tests),
             "assertions":list(evidence.test_result.messages) if evidence.test_result else [],
             "violations":[{"code":v.code,"file":v.file,"symbol":v.symbol,"message":v.message} for v in evidence.violations]},
            {p:u.id for u in self.contract.units if u.status == "active" for p in u.owns},dict(files))
        reply = self.judge_calls.generate(operation_id,unit.id,judge_prompt(context),max_output_tokens=self.max_output_tokens)
        return parse_judgement(reply.text)
