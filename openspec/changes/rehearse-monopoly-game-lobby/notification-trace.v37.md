# Account-partitioned notification observation

The real cycle-36 dossier requires a supported account-partitioned delivery trace
that spans the rejection operation. LobbyWorld now declares the optional
`Action<string,string,string> NotificationEmitted` observation callback: target
synthetic account ID, channel, message. It supplies no notification behavior.
SOCIAL and SHELL implement invocation at each actual notification delivery attempt
before dispatch, including background fake-platform delivery attempts and active
UI notices. Channels identify `ui` or `platform`; State.Messages remains the
independent persisted-message observation. Test setup may record callback values
but must never emit the expected event itself or manufacture business outcomes.

Install the recording observation before the recipient's bound rejection action.
Observe the applicant's own target-account events across that action separately
from legitimate recipient events. Compare the applicant baseline to events after
rejection, retaining independent no-message and no-friendship assertions. The
callback records attempted delivery regardless of which account owns the single
active street presentation. This supported account-partitioned delivery trace
proves applicant silence without loading a second street scene concurrently.

Remove the invalid helper that creates an applicant shell while the recipient
still owns its street. If an additional applicant UI inspection is retained,
first shut down the recipient presentation, then retain and shut down the new
applicant shell in cleanup. Merely starting a fresh UI after rejection cannot
observe an immediate applicant delivery during rejection.

All other reviewed request tests, exact expiry, backend counts, raw pointer and
bound input observations remain required. Update notes to describe the actual
sequence. No game delivery implementation or test assertions are supplied here.
