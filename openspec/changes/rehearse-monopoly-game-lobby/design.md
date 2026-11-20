# Design

## Context

The approved `proposal.md` is the behavior and rehearsal-configuration baseline. The original documents provide 143 functional items covered by 119 stories. Their historical empty-project observations have been superseded by current source inspection.

`Runtime/Script/Monopoly.cs` implements EnterAsync, ResumeAsync and OnLaunchRequestAsync through PrepareMatchEntryAsync. `Runtime/Script/MonopolyRootScene.cs` supplies root preparation, Navigator binding, portrait dimensions, framework camera registration and cleanup. Entry integration must reuse these lifecycle facilities and route the rehearsal to the lobby.

The independent module and trusted state are external to Unity imports. The trusted overlay has preserved 81,134 baseline files through an original-art import roundtrip. Its existing roots are `Runtime/Script/UI/LobbyRehearsal/`, the matching scene/prefab/image resource directories, `Editor/Script/LobbyRehearsal/` and `Tests/Runtime/Script/LobbyRehearsal/`. All paths below are relative to the game module unless explicitly identified as planning or trusted-state artifacts.

## Goals / Non-Goals

The implementation boundaries are a reusable VVMP client, injected fake platform/game ports, a shared clock and per-account durable fake-service state. The reviewer enters through the current game's dedicated entry and observes exact candidate behavior, including match handoff, abandonment and simulated completion.

Production service connectivity, production economy validation, final art and framework runtime development remain separate scopes. Detailed preservation policy applies to shared Unity content and previous runs.

## Decisions

### Cycle 2: observable client adapters and preparation feedback

Cycle 3 addresses the subsequent real v2 rework dossier without weakening coverage. A new TEST-HARNESS test-author unit supplies only shared Editor test scaffolding: actual preview-scene loading, actual prefab/configuration instances, in-memory storage and observation-only UI/lifecycle ports. It must not implement business behavior or manufacture coordinator state. Consumer test authors depend on its declared API and receive its actual implementation in context. The independent judge reviews each unit against its explicit subset of test links and source clauses; the aggregate LOBBY criterion is a schema-level label, not a demand that the first suite duplicate every other suite's assertions. All 119 stories remain in the full selection, with one additional harness-readiness test.

Cycle 1 produced test source but exhausted independent preparation review. No behavioral tests were frozen and no implementation ran. The judge identified missing rendered-state, safe-area, existing-entry and lifecycle assertions. The rehearsal host also discarded its detailed feedback; that wiring now forwards the actual independent explanation. Full prepared asset paths must be supplied, including the configuration asset under the prefab `Art/` directory. The approved product behavior is unchanged.

Before cycle 2, prepare nonfunctional API hooks in the existing owned shells: `LobbyShellBindings.EntryPort`, `BindView`, `UnbindView`, `BindStreet`, `ConfigureViewport` and `ShutdownAsync`, plus `Monopoly.ConfigureLobbyRehearsal(shell, accountId)`. Define the protected `ILobbyEntryPort` signature beside ILobbyUiPort. The production adapter must use the same hooks as tests: tests inject a recording lifecycle port and bind real prepared prefab instances without constructing a framework ViewModel outside Injector. Existing EnterAsync/ResumeAsync/OnLaunchRequestAsync must route the configured shell; LeaveAsync/ExitAsync/OnDestroy must shut it down. Production constructs this session using the existing Root/Navigator/scene/camera services. The override is instance-owned, never unmanaged static state.

`EntryPort.EnterRootAsync` and `LeaveRootAsync` pair the Root lifecycle; `LoadStreetAsync` and `UnloadStreetAsync` pair the prepared street. Repeated enter/resume does not duplicate resources. Shell ExitAsync is the approved fake platform-home navigation; ShutdownAsync releases the complete game session. BindView attaches exactly one set of listeners to the actual serialized controls and UnbindView removes it. BindStreet operates on the prepared 3D scene. ConfigureViewport accepts pixel width, height and safe-area Rect, uses the 1080×2160 portrait reference, and updates only runtime instance geometry. These signatures are testability contracts, not handwritten behavior.

The UI command protocol uses the exact serialized action names. Lobby `Appearance` is the central display hit target, `Chat` is the smiley and `Invite` opens Friends/partners. `Menu` reveals menu rows in order Friends, day ranking, history, Shop, Settings, Chat. Rows use `Row0`…`Row9`, their item/account ID as value, and the current screen/tab supplies meaning; Secondary/Avatar actions retain their serialized names. `Tab0`…`Tab2` switch only the current page's documented tabs. `Input` is the input-field change event, not a button, and `Send` receives a draft or reads the bound input. Confirmation uses Confirm/Decline; initial Abandon/return only opens confirmation and charges no new fee. The existing Back/Coins/Ingots/Primary/Cancel/Previous/Next/Copy/Paste/Vip/Rules/About/Support/Music/Effects/Quality/Report/Complete/Reconnect/TierN/Start actions keep their source meaning. Do not invent Smiley, Display or MenuEntry aliases.

OpenAsync screen names match prepared screen names exactly. Targets are lowercase: Appearance `skins`, `vehicles`, `actions`; Friends `friends`, `partners`, `requests`; Chat `world` or a synthetic peer ID; Records `day`, `week`, `history` or a match ID; Recharge `ingots`, `coins`, `cards`, `vip`; Settings default or `rules`, `about`, `support`. Appearance/actions presents Idle, Wave and Celebrate on the first three rows, using Animator's prepared Action parameter 0, 1 and 2. Back restores caller, tab, selection, paging and scroll. Tests must bind actual views and assert exact visible strings/counts, control effects, instance layout and 3D state; fake-port logs additionally establish entry/exit pairing. Review the native adapter itself and verify real entry visually before human review.

The current token policy is explicitly amended to 3,000,000 input and 900,000 output, preserving all usage and the same run. Three cycles and two added units remain the structural limits. The model identities/provider pins and explicit settings remain configured locally. The otherwise-unconfigured coder effort uses its advertised non-thinking mode because live diagnostics proved all completion tokens were spent reasoning and a numeric reasoning cap was ignored; the independent judge keeps its configured medium effort. Framework runtime and trusted overlay code remain unchanged.

### Source authority and coverage

Retain original source IDs and SHA-256 identities in the portable context export. The approved proposal supersedes specific source ambiguities for this rehearsal. Preserve a story-to-requirement-to-scenario-to-runtime-test mapping for every story, recording whether its behavior is client UI, fake-service simulation, a cross-cutting constraint or a documented exclusion.

All 119 story IDs remain visible in coverage, including the excluded cross-game invitation story. Test selection includes the complete declared lobby suite. Original game tests have separate historical results and require separate selection authorization.

### Existing entry and Root lifecycle

Use `Runtime/Script/Monopoly.cs` as the proposed existing-file ownership exception. Add `Runtime/Script/UI/LobbyRehearsal/Monopoly.LobbyRehearsal.cs` for the lobby lifecycle partial implementation. Verify the actual dedicated entry chain before freezing these claims. Any additional existing file requires explicit inclusion in the bounded entry inventory and its source hash before execution.

Route fake entry, resume and launch consistently to the lobby. Pair exit, cancellation, destruction, subscriptions, camera registrations and temporary dimension changes with cleanup. Reuse PrepareRootSceneAsync and the framework's Navigator/ICameraService. A loaded lobby returns immediately to the simulated platform home, whose re-entry action invokes the same entry. Fake services supply the lobby's platform/game interactions. Ensure the rehearsal route issues zero live protocol or payment requests.

Load `Runtime/Resource/monopoly/Scenes/LobbyRehearsal/LobbyStreet_placeHolder.unity` through the framework scene facilities while retaining the Root UI lifecycle. A dedicated world camera renders the street and preview character through the existing camera service. The Root binding and framework BaseCamera remain lifecycle-owned. Preserve original scene/asset identity and avoid duplicating EventSystem or AudioListener objects.

The prior separate-entry alternative creates a second launch path and is superseded by the user's current-entry choice. A pure 2D backdrop is superseded by the approved 3D Western street.

### Trusted overlay extension

Keep the original baseline manifest immutable. Add an externally stored, exact-path entry-exception register containing the original hash, permitted replacement ownership and first replacement receipt for `Runtime/Script/Monopoly.cs`. Registration must verify that current host bytes still match the original baseline and must retain that baseline identity.

Materialization accepts complete committed snapshots only within existing new-feature roots and the registered exact entry path. Existing entry metadata stays protected. Reject undeclared baseline overlap, aliases, changed unrelated files, stale candidates, path collisions and deletions. Candidate history binds identities to byte hashes. An interrupted installation remains a reconciliation stop.

Hold the host lease across materialization, refresh, import capture and each blocking ladder. Compare all protected baseline and candidate hashes around import and verification. New scoped metadata is returned verbatim to the coordinator, committed into a new candidate and reconciled before testing. Editor preparation can also create the explicitly enumerated new scene/prefab assets. Adopt those only through a dedicated preparation receipt, before contract freeze, after checking all unrelated baseline bytes. Runtime import capture remains metadata-only.

The original additive overlay stays in use. This exception-register extension is rehearsal host wiring. Changes under `src/unity_coder/` are outside this design.

### Presentation baseline

Prepare original geometric street facades, pavement, lighting, character rigs and vehicles. Assets reside under the existing scene/prefab/image LobbyRehearsal roots. Use a resource-root subdirectory for materials, meshes, animation and configuration assets so materialization remains bounded by those roots.

Freeze these entries and their imported metadata:

| Entry | Prepared content |
| --- | --- |
| `Scenes/LobbyRehearsal/LobbyStreet_placeHolder.unity` | Western street, world-camera binding, character/vehicle preview anchors and lighting |
| `UI/Prefabs/LobbyRehearsal/LobbyView_placeHolder.prefab` | Safe-area header, wallet, menu, central hit region, marquee, tier carousel, party row and primary action |
| `UI/Prefabs/LobbyRehearsal/AppearanceView_placeHolder.prefab` | Preview anchors, skin/vehicle tabs, scrolling catalog and equip/acquire actions |
| `UI/Prefabs/LobbyRehearsal/FriendsView_placeHolder.prefab` | Cooperation partners, requests/recommendations, ID controls and invitation overlays |
| `UI/Prefabs/LobbyRehearsal/ShopView_placeHolder.prefab` | Shared catalog data, preview, confirmed purchase and recharge recovery |
| `UI/Prefabs/LobbyRehearsal/RecordsView_placeHolder.prefab` | Ranked lists with pinned self row, history and expandable totals |
| `UI/Prefabs/LobbyRehearsal/ChatView_placeHolder.prefab` | World/private lists, avatar actions, input, reporting and keyboard-safe layout |
| `UI/Prefabs/LobbyRehearsal/RechargeView_placeHolder.prefab` | Exchange, card and ingot tabs, wallet, simulated payment and VIP overlays |
| `UI/Prefabs/LobbyRehearsal/SettingsView_placeHolder.prefab` | Audio, quality, rules, about and simulated support |
| `UI/Prefabs/LobbyRehearsal/HandoffView_placeHolder.prefab` | Tier/fee, 24 seats, factions, abandonment and simulated completion |
| `UI/Prefabs/LobbyRehearsal/PlatformHomeView_placeHolder.prefab` | Fake exit destination and re-entry action |

Resource entries in this table are relative to `Runtime/Resource/monopoly/`. Compilable View/VM/Presenter shells, serialized references and control/action bindings are prepared before contract freeze. Inspect imported objects for missing scripts, unresolved references and duplicate event/camera facilities. Freeze hierarchy, GUIDs, fileIDs, layout, art identities and API signatures in the presentation manifest. Implementation units receive an explicit list of permitted state/action changes.

The six-skin/four-vehicle catalog plus no-vehicle entry uses configured permanent/default and timed ownership. Idle, Wave and Celebrate are original placeholder animations. Later artist replacement must preserve declared asset type, dimensions where applicable, pivots, rig/binding contracts and identities, with renewed candidate review for changed presentation.

### Client and service boundaries

All screens use ViewModel → Presenter → View with Navigator/ViewLoader routing and framework-managed UI pooling. Commands modify service state, then publish observable updates. Preserve caller return routes, selection and scroll state where required.

Architect-prepared `LobbyPorts.cs`, `LobbyDtos.cs` and `LobbyConfiguration.cs` define frozen service interfaces, DTOs and typed configuration. Fake service implementations belong to delegated units. Shared state is injected and instance-owned. Runtime uses the target's account storage, filesystem, schedule, sound, quality and resource abstractions through verified APIs.

| Port | Ownership and behavior |
| --- | --- |
| Platform account/wallet | Synthetic platform ID, persisted balances, atomic exchange/checkout, cards and supplied VIP state |
| Game appearance | Catalog IDs, unlocks, expiry, equipped skin/vehicle and default fallback |
| Game match | Queue membership, party tier, invitation arbitration, 24 seats, factions, fees, disconnect/reconnect, settlement and result fixtures |
| Platform friends | Friend limit, mutations, request idempotency/expiry and status |
| Game chat/moderation | Delivery, cooldown, length validation, friend permission, draft-safe failure and report receipt |
| Records | Shared income/result data, ranking snapshots, history totals and partner/opponent recommendations |
| Shared unread | Separate world, private and request counters with conversation aggregation |
| Clock and persistence | UTC instants, Asia/Shanghai calendar rules and account-isolated durable service state |

Use Unicode scalar values for the 200-character limit, treating a surrogate pair as one character. This is an Architect implementation interpretation of Unicode characters. Render chat content as plain text with rich-text escaping. Independent tests cover supplementary characters, whitespace messages, rejection feedback and draft retention.

### Transaction and time behavior

Fake wallet, ownership, match fees, exchange, payment callbacks and settlement use operation/order identities. Repeated actions return the existing result. Failure leaves consistent state, and restart recovery preserves completed identities. Debit each party member once at start after validating all balances and seat/faction assignments. Retain selected tier/party on queue cancellation. Preserve disconnected seats and distinguish abandonment from reconnectable disconnection per seat.

Clock advances drive invitation/request expiry, appearance fallback, matchmaking deadlines, card rewards and ranking snapshots. Expiry is evaluated against the same authoritative fake clock. Exactly-once card grants have durable due-slot identities. Repeated card purchases extend a single entitlement timeline from max(expiry, now), preserving its existing grant cadence. Calendar months for VIP use Asia/Shanghai, while card days/weeks and ranking windows use elapsed durations.

The deterministic completion fixture must provide final placement, income entries, expenses and ending cash with consistent totals. Wallet settlement and history/ranking projection are idempotent. Abandoned matches have profit equal to negative entry fee and expenses equal to income plus entry fee. The client displays supplied record totals and final ranks.

### Delegated ownership and test responsibility

Use five implementation units with disjoint exact-file ownership. These paths are planned claims and must be replaced by the actual shell inventory before contract freeze.

| Unit | Owned implementation paths | Scope |
| --- | --- | --- |
| SHELL | `Runtime/Script/Monopoly.cs`, `Runtime/Script/UI/LobbyRehearsal/Monopoly.LobbyRehearsal.cs`, `LobbyShellBindings.cs` in the same UI root, `Runtime/Script/UI/LobbyRehearsal/LobbyRehearsalPanel.cs` | Existing entry, lifecycle, binding, platform home and Editor controls |
| ECON | `Runtime/Script/UI/LobbyRehearsal/LobbyEconomy.cs` | Wallet, catalog/appearance, clock/persistence, checkout, cards and fake VIP |
| MATCH | `Runtime/Script/UI/LobbyRehearsal/LobbyMatch.cs` | Parties, invitations, matching, bot fill, handoff and results |
| SOCIAL | `Runtime/Script/UI/LobbyRehearsal/LobbySocial.cs` | Friends, chat, moderation and unread state |
| RECORDS | `Runtime/Script/UI/LobbyRehearsal/LobbyRecordsSettings.cs` | Shared income records, ranking snapshots, history, recommendations, settings/support |
| TESTS | `Tests/Runtime/Script/LobbyRehearsal/LobbyPresentationTests.cs`, `LobbyEconomyTests.cs`, `LobbyMatchTests.cs`, `LobbySocialTests.cs`, `LobbyRecordsSettingsTests.cs`, `LobbyJourneyTests.cs` in the same test root | Test authorship and preparation repairs before global freeze |

Interface/configuration/presentation files and assembly definitions remain Architect-protected. Test selection and configuration freeze with test sources and metadata. Implementation units never own tests or presentation inputs. Shared journey tests map to all participating units. Runtime contract criterion strings must satisfy the current loader's shared-test mapping rules. Detailed source story/scenario mapping remains in the exported coverage register.

Freeze shared interfaces first so coding units can proceed against compilable peers. Runtime test links, declared dependency relationships and shared groups determine scheduling. The existing framework supplies model workers, ownership enforcement, TDD, the blocking verification ladder and review.

### Trusted host composition and budget

Keep run ID `monopoly-game-lobby` and the amended persisted policy of 3,000,000 input tokens, 900,000 output tokens, six total cycles and two added units per rework. A ledger cycle requires the validated contract identity. Retain prior receipts and uncertain reservations. Contract version is the cycle number.

Compose ArchitectBoundary, ProductionExecutor, WorkspaceManager, a held RunLease, BudgetLedger, LocalExecutionServices, configured coder/judge ModelCalls, the overlay materializer, Unity ladder and ReviewGate. Invoke through `unity_coder.cli.invoke_local(boundary, executor)`. Review authentication accepts an explicit human decision through the trusted operator path. Coding workers cannot access that path.

Bound worker prompt context to the unit's owned files, frozen interfaces, relevant test files, approved spec and required coding rules. Preserve configured models, roles and operation identities. Use a rehearsal-only context wrapper if the default full-context worker exceeds the existing budget. Estimate reservations before dispatch and report inability to fit within the existing ceiling. All calls use the same ModelCalls accounting.

### Verification and review

Perform independent test review, behavioral Red and global freeze before model implementation. Baseline compile/setup errors are preparation failures. Existing satisfied assertions require independent coverage review. Run the declared focused tests sequentially, then the complete integrated selection after Green/Refactor. Durable receipts include requested, discovered and executed test IDs, outcome counts, candidate, contract and presentation identities.

Review exact scene behavior at 18:9, 19.5:9 and 20:9, safe areas, keyboard layout, model/vehicle preview and all entry/back paths. The Editor panel switches synthetic accounts, advances time and drives synthetic-peer messages, invitations, acceptance and disconnect. Exact runtime tests and manual visual checks receive distinct evidence records.

After spec compliance review and code quality review, publish `verification.md` with criteria met/unmet, frozen hashes and exact receipts. End at `awaiting_human_review` with launch/review instructions. Planning task acceptance reconciliation follows the framework's human-review rules.

## Risks / Trade-offs

- Existing entry replacement can invalidate preservation guarantees → Exact-path exceptions retain original hashes, original baseline and replacement receipts, with unrelated-file drift checks.
- Editor asset generation can create files outside the candidate → Enumerate prepared destinations and reconcile only those files before freeze.
- Full worker context can exceed the persistent budget → Scope context and preflight reservations through the same configured workers and ledger.
- Fake clock catch-up can duplicate rewards or settlement → Persist due-slot/order identities and verify restart/retry cases.
- Source dependency diagrams contain UI navigation cycles → Treat them as shared scenario relationships and freeze interfaces before computing executable unit dependencies.
- Device/production integrations have different readiness → Report live Editor, offline, manual visual and production-integration evidence according to actual coverage.

## Migration Plan

Continue the external module baseline branch. Preserve the current seed and historical receipts. Export the approved planning context and original-source identities into `specs/monopoly-game-lobby/`. Prepare scenes/shells, register the exact entry exception, then freeze the presentation and contract.

Only the coordinator integrates coding worktrees and the verification worker materializes their exact committed candidate. Recovery uses durable receipts and explicit operational reconciliation. A rejected candidate remains available for inspection. Restoration of a registered entry uses its preserved original bytes and recorded candidate history through trusted host reconciliation.

## Acceptance mapping


The original story acceptance clauses remain applicable to client behavior and fake-service simulations except where the approved proposal and explicit scenarios above supersede them. Production-server implementation is represented by fake-service acceptance. Full in-match gameplay is represented by the approved handoff/result fixtures. US-L4-07 is checked as the documented cross-game invitation exclusion.

The following register maps every source story to its functional IDs, proposed test owner file and stable method name. The test author must expand each mapped story into meaningful assertions, including its non-overridden source clauses and approved decisions. The runtime contract must freeze the actual discovered test IDs and record every source-to-test mapping. A row here is planned coverage, not execution evidence.

| Story | Source title | Functional IDs | Planned test method |
| --- | --- | --- | --- |
| US-L1-01 | 从 JJ 大厅加载主界面并返回 | L1-1, L1-3 | LobbyPresentationTests.Story_L1_01 |
| US-L1-02 | 主界面场景背景与角色展示位 | L1-2 | LobbyPresentationTests.Story_L1_02 |
| US-L1-03 | 上下文菜单 | L1-4 | LobbyPresentationTests.Story_L1_03 |
| US-L1-04 | 跑马灯与局部未读数 | L1-5 | LobbyPresentationTests.Story_L1_04 |
| US-L1-05 | 底部功能按钮 | L1-6 | LobbyPresentationTests.Story_L1_05 |
| US-L2-01 | 货币余额展示与格式化 | L2-1, L2-2, L2-3 | LobbyPresentationTests.Story_L2_01 |
| US-L2-02 | 货币点击跳转与「+」按钮 | L2-4, L2-5, L2-6 | LobbyPresentationTests.Story_L2_02 |
| US-L3-01 | 形象设置入口与页签 | L3-1, L3-2 | LobbyEconomyTests.Story_L3_01 |
| US-L3-02 | 模型预览区与动作切换 | L3-3 | LobbyEconomyTests.Story_L3_02 |
| US-L3-03 | 皮肤列表与定帧预览图 | L3-4, L3-12 | LobbyEconomyTests.Story_L3_03 |
| US-L3-04 | 使用中标识与默认选中 | L3-5, L3-6 | LobbyEconomyTests.Story_L3_04 |
| US-L3-05 | 新账号默认形象随机 | L3-7 | LobbyEconomyTests.Story_L3_05 |
| US-L3-06 | 切换选中与「使用」 | L3-8 | LobbyEconomyTests.Story_L3_06 |
| US-L3-07 | 未获得形象的「去获得」 | L3-9 | LobbyEconomyTests.Story_L3_07 |
| US-L3-08 | 有效期显示 | L3-10 | LobbyEconomyTests.Story_L3_08 |
| US-L3-09 | 过期回落 | L3-11 | LobbyEconomyTests.Story_L3_09 |
| US-L3-10 | 座驾页签与表现约束 | L3-13, L3-14 | LobbyEconomyTests.Story_L3_10 |
| US-L3-11 | 形象数据源与解锁配置 | L3-15 | LobbyEconomyTests.Story_L3_11 |
| US-L4-01 | 好友入口与页签结构 | L4-1, L4-3 | LobbySocialTests.Story_L4_01 |
| US-L4-02 | 我的玩家 ID 与复制 | L4-2 | LobbySocialTests.Story_L4_02 |
| US-L4-03 | 好友行信息与头像来源 | L4-4 | LobbySocialTests.Story_L4_03 |
| US-L4-04 | 好友三态与跨游戏展现 | L4-5 | LobbySocialTests.Story_L4_04 |
| US-L4-05 | 好友私聊入口 | L4-6 | LobbySocialTests.Story_L4_05 |
| US-L4-06 | 邀请加入队伍与满员提示 | L4-7 | LobbySocialTests.Story_L4_06 |
| US-L4-07 | 跨端邀请（本期不做） | L4-8 | LobbySocialTests.Story_L4_07 |
| US-L4-08 | 好友列表翻页 | L4-9 | LobbySocialTests.Story_L4_08 |
| US-L4-09 | 好友上限与平台一致 | L4-10 | LobbySocialTests.Story_L4_09 |
| US-L4-10 | 好友双向同步 | L4-11 | LobbySocialTests.Story_L4_10 |
| US-L4-11 | 好友空态 | L4-12 | LobbySocialTests.Story_L4_11 |
| US-L4-12 | 删除好友 | L4-13 | LobbySocialTests.Story_L4_12 |
| US-L4-13 | 添加好友页签与来历 | L4-14, L4-15 | LobbySocialTests.Story_L4_13 |
| US-L4-14 | 历史合伙人与历史对手 | L4-16, L4-17 | LobbySocialTests.Story_L4_14 |
| US-L4-15 | 同意 / 拒绝好友申请 | L4-18 | LobbySocialTests.Story_L4_15 |
| US-L4-16 | 申请超时自动拒绝 | L4-19 | LobbySocialTests.Story_L4_16 |
| US-L4-17 | 发送好友申请与幂等 | L4-20, L4-21 | LobbySocialTests.Story_L4_17 |
| US-L4-18 | 按 ID 添加好友 | L4-22 | LobbySocialTests.Story_L4_18 |
| US-L4-19 | 组队入口跳转 | L4-23 | LobbySocialTests.Story_L4_19 |
| US-L5-01 | 排行榜入口与双页签 | L5-1, L5-2 | LobbyRecordsSettingsTests.Story_L5_01 |
| US-L5-02 | 榜单指标定义（收入流水） | L5-3 | LobbyRecordsSettingsTests.Story_L5_02 |
| US-L5-03 | 逐笔流水落库与日周聚合 | L5-4 | LobbyRecordsSettingsTests.Story_L5_03 |
| US-L5-04 | 榜单行内容与前三名样式 | L5-5 | LobbyRecordsSettingsTests.Story_L5_04 |
| US-L5-05 | 同额排序 | L5-6 | LobbyRecordsSettingsTests.Story_L5_05 |
| US-L5-06 | 周榜时间窗 | L5-7 | LobbyRecordsSettingsTests.Story_L5_06 |
| US-L5-07 | 日榜时间窗 | L5-8 | LobbyRecordsSettingsTests.Story_L5_07 |
| US-L5-08 | 分页与 100 名上限 | L5-9 | LobbyRecordsSettingsTests.Story_L5_08 |
| US-L5-09 | 自身行常驻 | L5-10 | LobbyRecordsSettingsTests.Story_L5_09 |
| US-L5-10 | 未上榜显示 100+ | L5-11 | LobbyRecordsSettingsTests.Story_L5_10 |
| US-L5-11 | 战报流水联动 | L5-12 | LobbyRecordsSettingsTests.Story_L5_11 |
| US-L6-01 | 历史入口与记录列表 | L6-1, L6-2, L6-4 | LobbyRecordsSettingsTests.Story_L6_01 |
| US-L6-02 | 利润计算口径 | L6-3 | LobbyRecordsSettingsTests.Story_L6_02 |
| US-L6-03 | 放弃局显示 | L6-5 | LobbyRecordsSettingsTests.Story_L6_03 |
| US-L6-04 | 收入 / 支出展开 | L6-6 | LobbyRecordsSettingsTests.Story_L6_04 |
| US-L6-05 | 放弃局的支出推导口径 | L6-7 | LobbyRecordsSettingsTests.Story_L6_05 |
| US-L6-06 | 名次口径 | L6-8 | LobbyRecordsSettingsTests.Story_L6_06 |
| US-L7-01 | 商城范围与入口 | L7-1, L7-2 | LobbyEconomyTests.Story_L7_01 |
| US-L7-02 | 页签与商品枚举 | L7-3, L7-4 | LobbyEconomyTests.Story_L7_02 |
| US-L7-03 | 选中与预览 | L7-5 | LobbyEconomyTests.Story_L7_03 |
| US-L7-04 | 二次确认购买 | L7-6 | LobbyEconomyTests.Story_L7_04 |
| US-L7-05 | 购买后换装询问 | L7-7 | LobbyEconomyTests.Story_L7_05 |
| US-L7-06 | 排序规则与「只排一次」 | L7-8, L7-9 | LobbyEconomyTests.Story_L7_06 |
| US-L7-07 | 形象页跳转定位 | L7-10 | LobbyEconomyTests.Story_L7_07 |
| US-L7-08 | 金币不足处理 | L7-11 | LobbyEconomyTests.Story_L7_08 |
| US-L7-09 | 座驾购买 | L7-12 | LobbyEconomyTests.Story_L7_09 |
| US-L7-10 | 无活动 / 无打折约束 | L7-13 | LobbyEconomyTests.Story_L7_10 |
| US-L7-11 | 商品表结构与数据 | L7-14 | LobbyEconomyTests.Story_L7_11 |
| US-L8-01 | 设置入口与局内外复用 | L8-1, L8-2 | LobbyRecordsSettingsTests.Story_L8_01 |
| US-L8-02 | 音乐与音效开关 | L8-3, L8-4 | LobbyRecordsSettingsTests.Story_L8_02 |
| US-L8-03 | 画面质量两档 | L8-5 | LobbyRecordsSettingsTests.Story_L8_03 |
| US-L8-04 | 客服帮助跳转 | L8-6 | LobbyRecordsSettingsTests.Story_L8_04 |
| US-L8-05 | 玩法说明 | L8-7 | LobbyRecordsSettingsTests.Story_L8_05 |
| US-L8-06 | 关于我们 | L8-8 | LobbyRecordsSettingsTests.Story_L8_06 |
| US-L9-01 | 场次表与金额公式 | L9-1, L9-2 | LobbyMatchTests.Story_L9_01 |
| US-L9-02 | 默认选中与上次记忆 | L9-3 | LobbyMatchTests.Story_L9_02 |
| US-L9-03 | 入场费校验与金币不足 | L9-4, L9-5 | LobbyMatchTests.Story_L9_03 |
| US-L9-04 | 轮播切换 | L9-6 | LobbyMatchTests.Story_L9_04 |
| US-L9-05 | 开始匹配 | L9-7 | LobbyMatchTests.Story_L9_05 |
| US-L9-06 | 队伍带入与组队加号 | L9-8, L9-9 | LobbyMatchTests.Story_L9_06 |
| US-L10-01 | 心跳匹配循环 | L10-1 | LobbyMatchTests.Story_L10_01 |
| US-L10-02 | 匹配队列按场次分流 | L10-2 | LobbyMatchTests.Story_L10_02 |
| US-L10-03 | 禁止中途加入 | L10-3 | LobbyMatchTests.Story_L10_03 |
| US-L10-04 | 允许中途退出且不可重加 | L10-4 | LobbyMatchTests.Story_L10_04 |
| US-L10-05 | 入场扣费与货币转换 | L10-5 | LobbyMatchTests.Story_L10_05 |
| US-L10-06 | 匹配超时与机器人补足 | L10-6 | LobbyMatchTests.Story_L10_06 |
| US-L10-07 | 整队入场同阵营 | L10-7 | LobbyMatchTests.Story_L10_07 |
| US-L11-01 | 队伍创建与上限 | L11-1, L11-2 | LobbyMatchTests.Story_L11_01 |
| US-L11-02 | 强制同阵营 | L11-3 | LobbyMatchTests.Story_L11_02 |
| US-L11-03 | 流程顺序（先组队 → 再选场次 → 进匹配） | L11-4 | LobbyMatchTests.Story_L11_03 |
| US-L11-04 | 邀请弹窗 | L11-5 | LobbyMatchTests.Story_L11_04 |
| US-L11-05 | 已满提示 | L11-6 | LobbyMatchTests.Story_L11_05 |
| US-L11-06 | 离队 | L11-7 | LobbyMatchTests.Story_L11_06 |
| US-L11-07 | 开局前的阵营校验 | L11-8 | LobbyMatchTests.Story_L11_07 |
| US-L12-01 | 充值页结构 | L12-1 | LobbyEconomyTests.Story_L12_01 |
| US-L12-02 | 金币兑换 6 档 | L12-2 | LobbyEconomyTests.Story_L12_02 |
| US-L12-03 | 元宝不足弹窗 | L12-3 | LobbyEconomyTests.Story_L12_03 |
| US-L12-04 | 金币卡 3 档 | L12-4 | LobbyEconomyTests.Story_L12_04 |
| US-L12-05 | 元宝充值 6 档 | L12-5 | LobbyEconomyTests.Story_L12_05 |
| US-L12-06 | VIP 权益弹窗与等级切换 | L12-6, L12-7 | LobbyEconomyTests.Story_L12_06 |
| US-L12-07 | VIP=0 特例 | L12-8 | LobbyEconomyTests.Story_L12_07 |
| US-L12-08 | VIP 进度与升级规则 | L12-9, L12-10 | LobbyEconomyTests.Story_L12_08 |
| US-L12-09 | 权益文案复用 | L12-11 | LobbyEconomyTests.Story_L12_09 |
| US-L12-10 | 充值链路与双单号 | L12-12 | LobbyEconomyTests.Story_L12_10 |
| US-L12-11 | VIP 数据只读 | L12-13 | LobbyEconomyTests.Story_L12_11 |
| US-L13-01 | 聊天展开与双频道 | L13-1, L13-2 | LobbySocialTests.Story_L13_01 |
| US-L13-02 | 私聊未读角标 | L13-3 | LobbySocialTests.Story_L13_02 |
| US-L13-03 | 消息行与右对齐 | L13-4 | LobbySocialTests.Story_L13_03 |
| US-L13-04 | 一屏行数 | L13-5 | LobbySocialTests.Story_L13_04 |
| US-L13-05 | 头像加好友 | L13-6 | LobbySocialTests.Story_L13_05 |
| US-L13-06 | 输入框与发送校验 | L13-7 | LobbySocialTests.Story_L13_06 |
| US-L13-07 | 私聊对象选择 | L13-8 | LobbySocialTests.Story_L13_07 |
| US-L13-08 | 私聊仅限好友 | L13-9 | LobbySocialTests.Story_L13_08 |
| US-L13-09 | 私聊未读数 | L13-10 | LobbySocialTests.Story_L13_09 |
| US-L13-10 | 跳好友系统 | L13-11 | LobbySocialTests.Story_L13_10 |
| US-L13-11 | 进入会话 | L13-12 | LobbySocialTests.Story_L13_11 |
| US-L13-12 | 纯文本约束 | L13-13 | LobbySocialTests.Story_L13_12 |
| US-L13-13 | 世界频道风控 | L13-14 | LobbySocialTests.Story_L13_13 |
| US-NFR-01 | 竖屏与分辨率适配 | Cross-cutting | LobbyPresentationTests.Story_NFR_01 |
| US-NFR-02 | 界面路由与 Prefab 路径一致 | Cross-cutting | LobbyPresentationTests.Story_NFR_02 |
| US-NFR-03 | 未读数统一聚合入口 | Cross-cutting | LobbyPresentationTests.Story_NFR_03 |
| US-NFR-04 | 多账号本地记忆隔离 | Cross-cutting | LobbyPresentationTests.Story_NFR_04 |

Shared LobbyJourneyTests must additionally cover entry → recharge → party matching → completion/abandonment → history/rankings, plus expiry/restart/account isolation. Declare their exact test IDs and participating units before contract freeze.

### Authorized abandonment recovery follow-up

The user authorized a narrow runtime recovery extension after the third cycle exhausted. Use RecoveryGrant and recover_abandoned_run with authenticated session provenance, exact previous result hash, held run lease, reconciled workers and retained Git candidate. Archive original evidence and preserve every paid call, uncertain reservation and lineage; publish the amended ledger last. Start contract version 4 and retain versions 1–3. Token ceilings stay unchanged. All normal stage calls use token-policy.json; previous paid identities remain immutable. Other runtime redesign stays outside scope.

## Cycle-ceiling amendment — 2026-11-19

The user explicitly extended the same run to twelve total contract cycles, retaining all usage, configured models, the trusted overlay, frozen-test rules and independent review. Token ceilings remain 3,000,000 input / 900,000 output. The consecutive recovery starts at contract version 7 and preserves versions 1–6 and their abandonment evidence. Product requirements are unchanged.

## Explicit token amendment — 2026-11-19

The user approved total token ceilings of 6,000,000 input / 1,800,000 output while preserving every charge and reservation. The total cycle ceiling remains twelve. Apply the amendment only at a reconciled terminal boundary through a result-bound TokenRecoveryGrant. No product requirement, configured model, trusted overlay or frozen-test rule changes.

## Thirty-cycle continuation — 2026-11-19

The user explicitly authorized thirty total cycles and approved total token ceilings of 12,000,000 input / 3,600,000 output. Recover the actual version-twelve abandonment through the authenticated TokenRecoveryGrant into consecutive version thirteen. Preserve every earlier charge, uncertain reservation, model identity, contract, retained candidate and terminal record. Keep the trusted overlay, two-added-unit limit, independent judge, Red/global-freeze ordering and sequential Unity verification. Product scope and acceptance criteria are unchanged; human acceptance remains pending.

### Approved handoff scope clarification

The already approved fake match handoff replaces full playable in-match gameplay in this rehearsal. US-L3-10 retains complete lobby vehicle behavior and in-match equip rejection; actual walking/driving locomotion and dismount rendering remain a real-match integration disposition, not claimed execution. Preserve this disposition explicitly when exporting raw source clauses to test authors and judge. The source-required dedicated Shop entry is now supplied as serialized Lobby action `Shop`; its absence was a preparation defect, not an excluded requirement.

### Catalog disposition and visual verification allocation

The user explicitly chose "Use rehearsal catalog; defer production integration" for US-L7-11. Verify the game-owned catalog's complete fields and shared Appearance/Shop source; record production Luban/AssetGraph integration as deferred. Framework D-26 keeps visual fidelity and complete experience at candidate-bound human review. Retain automated functional/state/geometry/visibility/lifecycle checks and all 125 IDs; map qualitative transition fidelity and visual clutter to explicit pending review steps, without claiming automated visual acceptance or removing product requirements.
