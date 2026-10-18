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

## Deviation: replay run with the Copilot CLI (2026-10-18)

Copilot code review on github.com is not available on this account's plan. Every replay request
since 2026-10-14 returned "the user who requested the review has reached their quota limit", and
support ticket #4872248 is open. The held-out replay is therefore run with the Copilot CLI
(`manual_replay.py` builds the worktrees, `cli_review.py` runs the reviews, set `manual`). The set,
the conditions, two runs per condition, the guidance text, the labelling and the decision rule are
unchanged from `PREREGISTRATION.md`.

What differs, and has to be stated with any result:

- **Reviewer:** Copilot CLI 1.0.98 in non-interactive mode, one fresh session per run, reviewing the
  staged diff of a local worktree. It is not the github.com PR reviewer, so the result says how the
  guidance changes Copilot CLI reviews and is indicative for github.com reviews, not a measurement
  of them.
- **Model:** named models are not available to this account in the CLI, so every run uses `auto`.
  The model `auto` resolved to is recorded per run in `manual/raw/<run>.json` and reported with the
  result.
- **Guidance frontmatter:** the CLI treats itself as the coding/cloud agent, so the
  `excludeAgent: "cloud-agent"` line in both guidance files hides them from it (checked with
  `copilot instruction list`). The guided worktrees use the same files with that one line removed
  (`--strip-exclude-agent`). The text Copilot reads is otherwise identical to `e975b6a`. Baseline
  worktrees load only `AGENTS.md`, which guided worktrees load too.
- **Prompt:** the same for all runs (in `cli_review.py`). It asks for `### path:line` blocks or
  `NO COMMENTS` so replies can be scored without retyping.
- **Read-only:** file writes, network access, `go`, `make` and state-changing git commands are
  denied. Each worktree is checked to be unchanged after its run. Runs that changed it or failed
  are not recorded, and the PREREGISTRATION failure rule applies (retry once, then report missing).
- An earlier VS Code attempt (one run, 1326 guided) is not used, because the CLI replaced it for
  all 32 runs.

If github.com review becomes available, the replay is rerun as originally planned and both
results are reported.

## Held-out result (Copilot CLI replay, 2026-10-18)

Labels by the author, made on the shuffled sheet with the condition hidden (`score_manual_human.csv`,
now also `score_manual.csv`):

```
8 PRs, 16 maintainer-found defects

condition             recall  comments   useful   noise   wrong  noise+wrong/PR
baseline r1        1/16 (6%)         2      50%      0%     50%             0.1
baseline r2        1/16 (6%)         3      67%      0%     33%             0.1
guided r1          1/16 (6%)         4      50%      0%     50%             0.2
guided r2          1/16 (6%)         3     100%      0%      0%             0.0
```

- **Decision rule (PREREGISTRATION.md): not met.** Mean defect recall is 1/16 in both conditions,
  not +2, so this is reported as **no measurable effect at this sample size**. The `useful` share
  did not drop. Pooled over runs it is 71% guided (5 of 7 comments) vs 60% baseline (3 of 5).
- The one defect each run found is in PR 616. Baseline found "`-mod=vendor` on the command line
  still fails" in both runs. Guided found it in run 1 and "workspace mode not handled" in run 2.
- Both 809 comments (one per condition) claim `ConnectionHost` omits the port. They are labelled
  `wrong` because `ConnectionHost` returns `PortEndpoint`, i.e. `host:port`, in testcontainers-go
  v0.41.0. These two labels were set after comparing with the first pass and checking that source.
- The two 1190 comments about `.github/workflows.disabled` are an artifact of the replay renaming
  workflows, labelled `wrong`.

**Second labelling pass:** an automated first pass (`score_manual_firstpass.csv`, not blind)
agrees with the author's labels on 51 of 58 rows (88%) and on every Copilot `matches` entry.
Differences: 4 maintainer rows lint vs design, 2 maintainer rows defect vs design, and 2 Copilot
rows useful vs noise. Under the first pass's labels the decision is the same (1/18 recall in every
run). The preregistered independent second person did not label a 20% sample.

**Post-hoc note (not part of the decision rule):** 8 of the 16 defects are in `instrumentation/`
(PR 809), which the guidance deliberately doesn't cover (see #1441). On the 8 in-scope defects,
recall is still 1 in every run.

**What the guidance did change (qualitative):** guided runs raised cases the guidance names. On
616, they covered `-mod vendor` as well as `-mod=vendor` (flag forms) and the `-C` directory. These
are not among the maintainer-found defects, so they don't count toward recall.
