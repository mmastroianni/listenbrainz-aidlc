# Reliability Requirements — u1-skeleton

Derived from `inception/requirements-analysis/requirements.md` (NFR2), the functional design (`construction/u1-skeleton/functional-design/functional-spec.md`, `rules.md`: BR4.1, BR4.2) and contract C2 in `inception/contract-design/contract-summary.md`.

## Availability

There is no uptime target: the app is local and started by hand.

## Requirements

| ID | Requirement | Pass criterion |
|----|-------------|----------------|
| NFR2.1 | The app fails fast at startup when a built file or the manifest is missing, or the format version differs | A test removes each file in turn; startup fails with a message naming the file and the step (BR4.2) |
| NFR2.2 | An interrupted pipeline step leaves the previous good files usable or no manifest | Files are written to temp names and renamed; the manifest is written last (BR4.1) |
| NFR2.3 | Each pipeline step refuses to run when its input step has not run | Message names the missing input and the step that makes it |
| NFR2.4 | Errors at boundaries (file reads, index load, requests) are surfaced, not swallowed | Every failure path logs or returns a clear message; tests cover two failure paths per step |

## Recovery

Rebuilding is the recovery: re-run the steps in order. No backups are needed, because the dumps are the source of truth and are never modified.
