# Status

Last updated 2026-10-18.

## Done

- Baseline: Copilot vs maintainer inline review comments on the 40 shared PRs, with hand labels
  (`labels.json`, `copilot_labels.json`) and the analysis scripts.
- Held-out set of 8 `tool`-scope PRs frozen before any guidance was written (`heldout.json`).
- Evaluation plan fixed before any held-out replay (`PREREGISTRATION.md`).
- Replay tooling (`replay.py`) with a dry-run default, token redaction and a `--prs` filter.

## Pending

- The held-out replay needs GitHub Copilot code review enabled on the account that owns the
  sandbox repo. Pilot sandbox PRs exist for 1362 (baseline and guided, one run each) but have
  no Copilot review yet.
- Until Copilot access is available, the guidance in the upstream PR is judged on the baseline
  data only; no claim is made about its effect.

## If the replay has to be reduced

A single run per condition (16 reviews instead of 32) is the smallest change that keeps the
design. It would be recorded here as a deviation from `PREREGISTRATION.md`, not applied
silently, and the decision rule would stay as written.

## Deviation: manual replay in VS Code (2026-10-18)

Copilot code review on github.com is not available on this account's plan. Every replay request
since 2026-10-14 returned "the user who requested the review has reached their quota limit", and
support ticket #4872248 is open. The held-out replay is therefore run by hand with Copilot's review
in VS Code (`manual_replay.py`, set `manual`). The set, the conditions, the runs, the guidance
version, the labelling and the decision rule are unchanged from `PREREGISTRATION.md`.

What differs, and has to be stated with any result:

- **Reviewer:** this is Copilot in VS Code, not the github.com PR reviewer. The model, the context
  and the way instruction files are loaded may differ, so the result says how the guidance
  changes VS Code reviews. It is indicative for github.com reviews, not a measurement of them.
- **Model:** the model used for all 32 runs: _fill in_.
- **Guided runs where the instructions file was not listed as used:** _list here, or "none"_.
- **Transcription:** comments are copied from VS Code into `manual/outputs/` by hand.

If github.com review becomes available, the replay is rerun as originally planned and both
results are reported.
