# Exact remaining message content and report oracles

MsgAssertNoRichTextRendered must first require a real ScrollRect and non-null
Scroll.content. Inspect parsed/rendered TMP output ONLY below that history
content. There is no whole-view or null-scroll fallback. Exclude the input and
its descendants and associate the observation with the delivered message row.
An unrelated status, title, marquee or input label cannot establish delivery.

Classify graphics by actual serialized/runtime roles and references. Known row
background targetGraphic references and actual avatar binding references are
permitted; ordinary TMP text and input graphics remain valid. Inspect Image AND
RawImage content. An otherwise unknown graphic in message content must not be
accepted merely because a name/sprite contains 'icon', 'row', 'bubble', or similar
words. Use the actual row/avatar bindings and independently supplied avatar data
where needed. Unknown attachment graphics must fail the plain-text content check.
Do not replace role checks with another English-name blacklist or whitelist.

For EACH cancellation and confirmation branch in Story_L13_13, the named mapped
test must drive this sequence: timed message pointer hold/release, observe the
usable Report entry, dispatch the actual pointer click to Report, observe the
confirmation, then click Decline or Confirm. A geometry/existence assertion for
Report is not an activation. Do not treat the initial hold as if it directly
opened confirmation. Keep fresh per-operation notice baselines and report counts.

Preserve all valid delivery, pending, draft, Unicode, cooldown, friendship,
controlled-clock and literal-rendering assertions. Correct invalid fallbacks and
over-broad allowances. Keep private helper signatures used by read-only partials;
renaming/removing an owned helper must not break those callers.
