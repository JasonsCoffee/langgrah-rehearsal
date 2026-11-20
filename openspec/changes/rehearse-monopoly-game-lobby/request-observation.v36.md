# Friend request and input observation boundaries

LobbySocial now actually declares `int RequestFriendInvocations { get; private
set; }`. This nonfunctional observation property starts at zero. Its delegated
implementation increments once at the beginning of every real RequestFriend
service entry, including duplicate, invalid and rejected calls. Only the social
service writes it. It is an invocation count, independent of persisted request
count. A reopened client submission must increase it while backend deduplication
preserves one pending request. The test must observe deltas around the actual
client action, not increment this property or manufacture a backend response.

The disabled sent button must retain a raw pointer feedback path supplied by
SHELL, independently of Button.onClick's interactability guard. The real pointer
hit dispatches a bound feedback handler, emits a fresh sent notice and performs
no second send while disabled. Do not call onClick.Invoke to bypass that guard.
SHELL may bind an instance-owned pointer event component at runtime; test setup
must not install a fake handler that emits the expected result. After reopening,
the normal enabled submit path reaches the fake backend again.

World.PlatformKeyboardRequested is a prepared optional Action<string,string>:
active synthetic account ID, then input action ID `Input`. SHELL requests this
fake-platform input-method boundary when a real bound text-field pointer/focus
event activates input. The callback only records that request; it must not set
the draft, focus flag or business result. Keep actual TMP input activation and
assert bound input-change events by editing the real field, rather than issuing
CommandAsync to manufacture typing. Test paste through the actual serialized
Paste button and the configured clipboard port.

EditMode automation establishes pointer focus, platform keyboard-request intent,
bound text-change behavior and submission. It cannot establish physical mobile
keyboard presentation. Exact-candidate human review must click the field, type,
paste and submit on the review device and check keyboard/input placement. The
review package records that limitation; never claim a callback proves a physical
keyboard was shown. Production input activation remains required.

Use recipient-local and applicant-local notification baselines. Clear accumulated
observations on the shared recording port at an account boundary or create a
fresh recording UI session over the same world. Preserve legitimate recipient
notices while proving no new applicant delivery or applicant UI rejection notice.
The configured author owns these observation-only fixture changes.
