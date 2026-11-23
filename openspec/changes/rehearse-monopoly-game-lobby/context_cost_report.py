"""End-to-end cost math with explicitly unknown subscription cash rates."""


def cost_report(*,canonical_input: int,delivered_input: int,selector_input: int=0,selector_output: int=0,
                judge_output: int=0,extra_judge_input: int=0,judge_input_rate: float | None=None,
                judge_output_rate: float | None=None,selector_input_rate: float=0,selector_output_rate: float=0,
                canonical_output: int=0) -> dict:
    values=(canonical_input,delivered_input,selector_input,selector_output,judge_output,extra_judge_input,canonical_output)
    if any(type(v) is not int or v<0 for v in values):raise ValueError('Nonnegative actual/estimated token counts required')
    known=judge_input_rate is not None and judge_output_rate is not None
    baseline=(canonical_input*judge_input_rate+canonical_output*judge_output_rate)/1000000 if known else None
    optimized=(selector_input*selector_input_rate+selector_output*selector_output_rate+
        (delivered_input+extra_judge_input)*judge_input_rate+judge_output*judge_output_rate)/1000000 if known else None
    return {'canonical_input':canonical_input,'delivered_input':delivered_input,
        'input_reduction':1-delivered_input/max(1,canonical_input),'selector_tokens':[selector_input,selector_output],
        'extra_judge_input':extra_judge_input,'canonical_cost':baseline,'optimized_cost':optimized,
        'monetary_savings_verified':known,'net_saving':baseline-optimized if known else None,
        'monetary_limit':None if known else 'Judge subscription cash rate is unknown; token reduction is not cash savings'}
