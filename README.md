# Copilot vs maintainer review baseline — opentelemetry-go-compile-instrumentation

Compares GitHub Copilot's inline review comments with maintainer inline review comments
on `open-telemetry/opentelemetry-go-compile-instrumentation`, 2026-05-03 to 2026-09-28.

## Reproduce

```sh
gh auth login
./fetch.sh                  # ~60 API calls, writes data/
python3 analyze.py          # counts, co-location, themes
python3 analyze_labels.py   # metrics from the hand labels
```

## Method

- Source: `GET /repos/{repo}/pulls/comments` (all inline review comments). Top-level review
  bodies and conversation comments are not included.
- "Maintainer" = the Maintainers list in the repo README. "Copilot" = the Copilot review bot.
- Only top-level inline comments are counted as findings; replies are used for the response signals.
- **Co-location (recall proxy):** a maintainer comment counts as co-located if, on the same PR,
  Copilot commented on the same file within ±10 lines. Only PRs where both left inline comments.
- **Response signals:** first reply to a Copilot comment matched against "fixed/done/good catch/…"
  (accepted) or "not an issue/no need/intentional/…" (pushed back).
- **Themes:** keyword buckets over comment bodies; a comment can fall in several.

## Caveats

- Co-location undercounts the same finding raised on a different line, and overcounts
  unrelated comments that happen to be nearby.
- Keyword themes and reply classification are noisy; ~45 replied Copilot comments are unclassified.
- Hand labels (below) cover maintainer comments only. Copilot's own comments are not yet
  labelled as useful / noise / wrong.
- Copilot coverage in this window is limited, partly because auto-review was not consistently running.

## Hand labels

`labels.json` holds the 180 maintainer comments on the 40 shared PRs, each labelled
`defect` (a concrete issue findable from the diff and repo), `question/design` (scope, design
or knowledge outside the diff) or `lint (CI)` (already caught by CI). Labels are one person's
judgement; corrections welcome. `python3 analyze_labels.py` recomputes the metrics from them.

Review ordering and low-confidence comments come from `data/reviews/` (fetched by `fetch.sh`).
Copilot's suppressed low-confidence comments were negligible (6 across 4 PRs) and are not counted.

## Copilot comment labels

`copilot_labels.json` labels all 187 Copilot inline comments `useful` (correct and worth raising),
`noise` (correct but not worth a reviewer's attention: nits, PR-description remarks, out-of-scope)
or `wrong` (incorrect or doesn't apply). `basis` says whether the label rests on the reply thread
(`reply`) or on my reading of the code (`judged`).

Result: 145 useful (78%), 25 noise (13%), 17 wrong (9%). Copilot's comments are mostly right;
the gap is what it doesn't comment on.

## Held-out evaluation set

`heldout.json` holds 15 PRs frozen before any guidance was written (seed 1411; criteria inside).
They are PRs maintainers reviewed that have no Copilot inline comments and are not in the tuning set.
Their review comments are not read until the guidance is frozen. `scope` splits them into `tool`
(8) and `instrumentation` (7) by changed file paths.

`guidance_trace.md` maps every rule in the review guidance to the tuning comments and repo
docs it comes from.

## Replay evaluation

`replay.py` replays PR diffs in a sandbox repo (not a fork) so Copilot reviews the same diff with
and without the guidance. Each replay is a pair of snapshot commits: the PR's merge base and the
commit maintainers first reviewed. Guidance files are added to both sides in the guided condition,
so they never appear in the diff. Snapshots use neutral commit messages (nothing references upstream
issues) and rename `.github/workflows` so the sandbox doesn't run otelc's CI. It is a dry run unless
`--push` is passed.

`evaluate.py collect` downloads the reviews, `evaluate.py sheet` writes a blind scoring sheet
(Copilot comments from both conditions shuffled, condition hidden in a separate key file), and
`evaluate.py score` reports defect recall, comment precision and noise per PR per condition.

## Results (2026-09-28 snapshot)

| Metric | Value |
|---|---|
| Inline review comments (all) | 1,723 |
| Maintainer top-level comments | 788 on 199 PRs |
| Copilot top-level comments | 187 on 56 PRs |
| PRs opened May–Aug with a Copilot review (search `reviewed-by:`) | 71 / 540 (13%); Aug: 19 / 229 |
| PRs with inline comments from both | 40 (Copilot reviewed first on 25) |
| Maintainer comments on those PRs | 180: 129 defect, 46 question/design, 5 lint |
| Defects with a Copilot comment on the same file within ±10 lines | 32 / 129 (25%) |
| Defects raised on Copilot-first PRs in spots Copilot never touched | 69 / 90 |
| Copilot comments with no reply | 85 / 187 (45%) |
| Replied Copilot comments marked fixed/accepted | 54 / 102 |

Monthly Copilot review coverage (PRs opened / reviewed by Copilot): May 66/15, Jun 52/9,
Jul 193/28, Aug 229/19.
