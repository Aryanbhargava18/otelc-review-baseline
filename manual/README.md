# Manual held-out replay (VS Code)

32 runs: 8 held-out `tool` PRs × 2 conditions × 2 runs. Each PR/condition is a worktree in
`../manual-replay/<pr>-<condition>`. The PR's diff is staged in it. In `guided` worktrees the
guidance files are already committed, so they are present but not part of the diff.

## Set up once
1. Pick one Copilot model in VS Code and use it for all 32 runs. Write its name in `STATUS.md`.
2. Use the same review action every time. Preferred: Source Control view → Copilot code review of
   the uncommitted (staged) changes. If you have to fall back to a chat prompt, use exactly:
   `Review the staged changes in this repository as a pull request review. Leave each finding as file:line plus the comment.`

## Each run (32 times)
1. `File → Open Folder…` → `../manual-replay/<pr>-<condition>` (new window).
2. Start a fresh review. No earlier chat in the window, and don't add anything else to the context.
3. **Guided runs only:** check that Copilot lists `.github/instructions/…instructions.md` among the
   references or instructions it used. If it doesn't, write that down in `STATUS.md`. The run still
   counts, but the guidance didn't reach the model.
4. Copy every comment into `manual/outputs/<pr>-<condition>-r<run>.md` like this:

   ```
   ### tool/internal/setup/args.go:42
   comment text, as Copilot wrote it
   ```

   If there are no comments, put the single line `NO COMMENTS`.
5. For run 2, close the window and repeat from step 1.

Don't edit the code in the worktrees. If you change something by accident, run
`git -C <worktree> stash` and then `git -C <worktree> stash drop`.

## When all 32 are filled in
```
python3 manual_replay.py ingest         # lists anything still missing
python3 evaluate.py sheet --set manual  # blind sheet; don't open score_manual_key.json yet
# label score_manual.csv (labels and matches as in PREREGISTRATION.md), then:
python3 evaluate.py score --set manual
```
