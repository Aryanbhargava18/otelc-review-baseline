**Is your feature request related to a problem? Please describe.**

Following up on @kakkoyun's note on Slack about an agentic review skill to make Copilot reviews more accurate. Before proposing anything I wanted a baseline, so I compared Copilot's inline review comments with maintainer inline review comments from 2026-05-03 to 2026-09-28 (1,723 comments). The data, scripts and my labels are here: <GIST_OR_REPO_LINK>.

In short: Copilot reviews few PRs, and on the PRs it does review it misses most of what maintainers go on to flag.

| | |
|---|---|
| PRs opened May–Aug that got a Copilot review | 71 / 540 (13%); 8% in August |
| PRs where both Copilot and maintainers left inline comments | 40 (Copilot reviewed first on 25) |
| Maintainer comments on those PRs, hand-labelled | 180 → 129 concrete defects, 46 design/scope questions, 5 lint findings CI already catches |
| Concrete defects where Copilot commented on the same file within ±10 lines | 32 / 129 (25%) |
| On the 25 PRs Copilot reviewed first: defects maintainers still found in spots Copilot never commented on | 69 |
| Copilot comments that got no reply | 85 / 187 (45%) |

The defects Copilot missed cluster in a few areas:

- **Stream and span lifecycle:** unsynchronized `done` and spans that never end when the body isn't closed (#604); an unbounded line buffer (#604); streaming spans missing usage attributes (#689).
- **Semconv:** `gen_ai.*` attributes that aren't in the registry (#604).
- **Rule and setup semantics:** multi-root `$root` expansion, `-C`/`-overlay` flag handling (#629), and module path resolution (#617).
- **Docs drift:** `docs/rules.md` not updated alongside rule changes (#629, #562).

Copilot also spends comments on things that don't apply here, e.g. loop-variable capture on #561, where we're on Go 1.25 and `copyloopvar` is enabled.

There's no `.github/copilot-instructions.md`, `.github/instructions/`, or review skill in the repo today. `AGENTS.md` covers contributing but not reviewing.

**Describe the solution you'd like**

A measured iteration:

1. **Agree on the baseline:** maintainers spot-check my labels (`labels.json`), and I label Copilot's comments as useful / noise / wrong.
2. **Add review guidance:**
   - `.github/copilot-instructions.md` for repo-wide review priorities;
   - path-scoped `.github/instructions/*.instructions.md` for `tool/internal/setup`, `tool/internal/instrument` and GenAI instrumentation, which is where most maintainer comments land;
   - a `.github/skills/code-review/SKILL.md`, which Copilot code review loads and other agents that support skills can use as well.

   Target the missed categories above, and tell the reviewer to skip what CI already enforces (lint, license headers, conventional commits, bundle verification).
3. **Measure:** tune on part of the PRs, then replay a held-out set of ~15 PR diffs on a fork with and without the guidance. Report defect recall, the share of useful Copilot comments, and noise per PR.
4. Keep what moves the numbers and drop what doesn't. If nothing moves, close this.

Non-goals: changing CI gating, enabling auto-review (that's the settings issue already being chased), or adding any bot that comments on PRs.

I'd like to work on this if the direction sounds right.

**Describe alternatives you've considered**

- **Writing instructions without measuring.** opentelemetry-java-instrumentation did this (open-telemetry/opentelemetry-java-instrumentation#20252, open-telemetry/opentelemetry-java-instrumentation#20283). It's a good structural reference, but there's no way to tell whether it helped.
- **Only fixing auto-review coverage.** That's needed, but on the PRs Copilot already reviews, three quarters of maintainer-found defects are still missed.

**Additional context**

Method caveats: "commented nearby" means the same file within ±10 lines, so it can miss the same finding raised on a different line and can count unrelated comments that happen to be nearby. The labels are mine and need checking. Details are in the README.

Questions for maintainers:

- Is replaying historical PR diffs on a fork an acceptable way to measure, or is there a preferred approach?
- Which areas would you most want caught before you review?
