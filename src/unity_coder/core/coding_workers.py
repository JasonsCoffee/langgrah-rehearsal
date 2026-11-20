"""Configured paid model workers; file access stays with the executor host."""

from collections.abc import Mapping
from dataclasses import dataclass, fields
import json

from .contracts import Contract, Unit
from .local_executor import WorkerPatch, TestReviewRejected
from .model_calls import JudgeInput, ModelCalls, judge_prompt
from .model_workers import _object, parse_judgement, parse_patch
from .verification import VerificationResult


@dataclass(frozen=True)
class StageTokenBudgets:
    """Per-call allocations, not run limits or universal model capability caps."""
    test_authoring: int = 65536
    green: int = 65536
    refactor: int = 65536
    test_review: int = 32768
    defect_judgment: int = 32768

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) is not int or value < 1:
                raise ValueError('Stage output allocations must be positive integers')


class ModelCodingWorkers:
    def __init__(self, contract: Contract, coder: ModelCalls, judge: ModelCalls, *,
                 max_output_tokens: int | None = None,
                 token_budgets: StageTokenBudgets | None = None) -> None:
        if (coder.client.config.role != "coder" or judge.client.config.role != "judge"
            or coder.client.config.model.casefold() == judge.client.config.model.casefold()):
            raise ValueError("Coder and judge require independent models and correct roles")
        self.contract, self.coder, self.judge_calls = contract, coder, judge
        if max_output_tokens is not None and token_budgets is not None:
            raise ValueError('Choose uniform or per-stage output allocations')
        if max_output_tokens is not None:
            token_budgets = StageTokenBudgets(**{f.name: max_output_tokens for f in fields(StageTokenBudgets)})
        self.token_budgets = token_budgets or StageTokenBudgets()

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
        reply = self.coder.generate(operation_id,unit.id,prompt,max_output_tokens=getattr(self.token_budgets, stage))
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
        reply = self.judge_calls.generate(operation_id,unit.id,prompt,max_output_tokens=self.token_budgets.test_review)
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
        reply = self.judge_calls.generate(operation_id,unit.id,judge_prompt(context),max_output_tokens=self.token_budgets.defect_judgment)
        return parse_judgement(reply.text)
