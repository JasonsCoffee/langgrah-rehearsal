# Source/catalog consistency observation

The cycle-22 baseline still contains an unsupported literal in
`LobbyEconomyRechargeTests` VIP scenarios and `BaseVipBenefits`: they require
`入场费折扣` in service benefits and rendered text, including Story_L12_09.
The prepared `LobbyConfiguration` localization row
`lobby.vip.entry` instead supplies `入场优惠介绍：演练入场费保持不变。`, with the
category `入场优惠`. No approved source requires the test's literal wording.
The user approved original Monopoly-specific copy and informational VIP with
unchanged fees; all categories remain present in the prepared table.

Do not modify the table or hardcode extra service/UI text to satisfy this test.
Delegate a correction before global freeze: test the actual prepared category,
key and localization value, use a private sentinel mutation to prove this row's
real rendered data path, and retain every valid category, localization provenance,
no-cross-game-copy and unchanged-fee assertion. Preserve the existing test ID and
all other effective assertions. The independent judge must review the repair.

This is an Architect source observation, not a judge verdict, executed test
result or human approval. It is recorded while native cycle-22 preparation is
active; no live contract or test was edited by the Architect.
