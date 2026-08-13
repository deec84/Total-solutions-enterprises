# Native parking experience

The native parking feature requests one foreground location only after a user
action. Android requests fine or coarse foreground permission; iOS requests
When In Use permission. Neither platform enables background location, stores
coordinates, records a location history, nor logs location values.

The clients submit accuracy, timestamp, and consent to the versioned parking
decision endpoint. They display only the typed backend result, reasons, and
available provenance and freshness evidence. They do not calculate parking
eligibility, cache decisions, infer coverage, or turn an unavailable result
into a parking recommendation.

`PARK` is displayed only when returned by the backend. All other outcomes and
coverage states include an instruction to review current signs. Network and
service failures do not expose server internals; an invalid session returns to
the signed-out access flow.
