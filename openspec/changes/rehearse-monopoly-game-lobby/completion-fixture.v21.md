# Fake match outcome seam

`LobbyWorld.MatchCompletionSnapshot` is an optional fake-match result supplier:
`Func<string, string, LobbyMatchRecord>` receives match ID and account ID before
completion. It supplies result data only; it performs no wallet, record, ranking,
UI or persistence effects. Null hook uses the normal deterministic fake match
result. A supplied snapshot must be validated and projected through the same
completion path, with no client-side recomputation of the supplied final rank.

This declaration closes the actual cycle-twenty independent-oracle gap. Arrange
explicit outcome data before invoking completion, independent of implementation
output. Verify exact wallet settlement, history, rankings, duplicate operation
handling and persistence restart from that data. Do not calculate expected amounts
from a post-completion seat or implementation-produced record. Use distinct valid
outcomes for different accounts to detect accidental shared settlement ownership.

Source identities and formulas remain binding: ending cash includes any prize,
profit = ending cash minus entry fee = total income minus total expenses; expenses
include entry fee. The normal fake result must be deterministic and internally
consistent. This is not permission to assert production prize-pool execution or
to implement full board gameplay. All functional behavior remains delegated.
