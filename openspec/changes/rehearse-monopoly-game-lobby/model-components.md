# Rehearsal AI components

Display the role first; model names identify its configuration. Exact historical
receipt identities and model IDs remain unchanged. Actual request logs report
the resolved effort after scoped policy and explicit-setting precedence.

| Component | Model / route | Effective effort |
|---|---|---|
| Judge: test review and defect judgment | GPT-6.1 Sol / OpenRouter | medium |
| Coder: TEST-HARNESS authoring | DS4.1 Flash / OpenRouter, Alibaba | low |
| Coder: TEST-CHAT-MSG authoring | DS4.1 Flash / OpenRouter, Alibaba | low, explicitly approved |
| Coder: TEST-CHAT authoring | DS4.1 Flash / OpenRouter, Alibaba | low, explicitly approved |
| Coder: TEST-CARDS authoring | DS4.1 Flash / OpenRouter, Alibaba | low, explicitly approved |
| Coder: TEST-RECORDS authoring | DS4.1 Flash / OpenRouter, Alibaba | low, explicitly approved |
| Coder: other test authoring | DS4.1 Flash / OpenRouter, Alibaba | none |
| Coder: Green and Refactor | DS4.1 Flash / OpenRouter, Alibaba | none |

Explicit configured effort wins. Coder temperature remains zero; Judge retains
provider temperature policy. Per-request completion allocations remain 65,536
for Coder stages and 32,768 for Judge stages, with the configured 180-second
deadline. Persistent limits remain 75m input / 12m output / sixty cycles.
Verified direct connections only; no credential output or model substitution.
