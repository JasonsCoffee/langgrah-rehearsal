# Prepared fake-platform inputs and focused social authors

The user requires fake platform functionality, a platform-supplied configurable
friend limit, platform avatar display/fallback and client/platform friendship
synchronization. The exhausted source review exposed references without matching
prepared data inputs. These declarations supply that boundary; they implement no
business behavior. The configured coder implements all service and UI effects.

`LobbyWorld.PlatformAvatarOverride` is an optional `Func<string, UnityEngine.Sprite>`.
When supplied, the fake platform provides that account's sprite; a null result or
failure uses an eligible original default avatar. Do not change the supplied
sprite or mistake a transparent button background for a rendered avatar.

`PlatformFriendLimit` is a nullable integer override. Null resolves to the existing
fake-platform configuration `Configuration.FriendLimit` (default 100); a supplied
override is authoritative. UI availability and fake-platform validation use the
same resolved value, including updates while the page is active.

`PlatformFriends` is an independent fake-platform friendship map. Explicit map
entries are authoritative platform snapshots; absent entries initially fall back
to persisted account friendship data. Accepted game-side additions/deletions
update both directions and the client projection. Platform-side changes are
imported on the fake service tick. `PlatformRemoveFriendAllowed` defaults to true;
false simulates platform rejection and must preserve both stores and the visible
row, with failure feedback. No production platform connection is introduced.

The original nineteen methods are partitioned mechanically into ten friend UI,
five request and four recommendation tests. All bodies are byte-identical before
delegated repair. Shared partial helpers remain with the primary author. Pointer
helpers in a different fixture class are examples, not callable APIs: the primary
author must provide its own observation-only event/raycast helpers. No fallback
direct command may stand in for a missing actual pointer hit target. Keep sentinel
sprite rectangles within the actual source texture dimensions.

Recommendation eligibility fixtures must arrange actual entry-time friendships,
seat factions and final ranks through the fake match boundary. The existing
`MatchCompletionSnapshot(matchId, accountId)` can supply consistent final data per
participant. Do not seed preclassified Partners/TopOpponents lists as proof of
the classification under test. Derive the eligible historical data from actual
match facts and prove cooperation/partner/opponent ordering independently. Actual
board locomotion/gameplay remains deferred; fake result and financial ownership
behavior remains required. No service result or rendering observation may be
manufactured by a test adapter.
