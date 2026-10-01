# Evaluation plan (written before any held-out replay)

This fixes how the held-out evaluation is run and judged, so the result can't be shaped after
seeing it. Whatever the outcome, it gets reported.

## Set

The 8 `tool`-scope PRs in `heldout.json`, frozen before any guidance was written. Each is replayed
in a sandbox repo twice per condition:

- `baseline`: the PR's reviewed state with no review guidance added;
- `guided`: the same state with the guidance files added on both sides of the diff.

The exact guidance version is recorded in `replay_heldout.json` (`guidance_blobs`). The guidance is
not changed between the first and last held-out run.

## Labelling

1. `evaluate.py sheet` shuffles Copilot comments from all runs and hides the condition in
   `score_heldout_key.json`, which is not opened until every row is labelled.
2. Maintainer comments: `defect`, `question/design` or `lint (CI)`, as in `labels.json`.
3. Copilot comments: `useful`, `noise` or `wrong`, as in `copilot_labels.json`.
4. A Copilot comment "matches" a maintainer defect when it raises the same underlying problem,
   judged from the text and the code, not from location alone.
5. A second person independently labels a random 20% of rows (seed 1411). Agreement is reported.

## Metrics

- **Primary: defect recall.** For each run, the share of maintainer-found defects matched by at
  least one Copilot comment in that run. Reported per run and as the mean of the two runs per
  condition.
- **Secondary:** share of Copilot comments labelled `useful`; `noise` + `wrong` comments per PR;
  total comments per PR.

## Decision rule

The guidance counts as an improvement only if mean defect recall rises by at least 2 defects in
absolute terms **and** the `useful` share drops by no more than 10 percentage points. Anything else
is reported as no measurable effect at this sample size.

## Failures

A replay whose Copilot review doesn't run is retried once. If it still fails it is reported as
missing, not replaced.

## Known limits

Eight PRs is a small sample and Copilot's output varies between runs, so results are directional.
The labellers know the guidance, so guided comments may be recognisable despite blinding; the
second labeller and the agreement figure are there to check that.
