# Effective friend-page capacity

The rehearsal Friends page uses ten accounts per page, matching its prepared
Row0 through Row9 bindings. This is the effective page size, not the number of
currently visible or occupied reusable row objects. Hide unoccupied row slots on
the last page; keep Previous hidden on the first page and Next hidden on the last.
The client requests the same ten-item slice from the fake social service.

Arrange enough eligible friends to exercise at least three pages, including a
partial last page. Independently arrange the expected sorted account sequence,
verify complete rendered membership with no omissions/duplicates and service
page slices, and navigate forward and backward. Do not assume five arranged
friends exceed the ten-item capacity or derive expected IDs from service output.
Keep all previously reviewed ordering, return-state and visibility assertions.

Invitation arbitration must establish the exact successful party membership
before the later acceptance, then prove it remains unchanged after rejection.
The unsuccessful later accepter remains outside that party. A full-party notice
alone does not prove membership preservation. Keep immediate closure of remaining
pending invitations and recipient-local feedback observations.
