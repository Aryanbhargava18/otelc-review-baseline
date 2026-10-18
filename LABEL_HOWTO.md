# Blind labelling (about 20 minutes)

Open `score_manual_human.csv` in a spreadsheet. Fill in two columns, and don't look at `score_manual.csv` or `score_manual_key.json` first.

**`label`**
- Maintainer rows (`M…`):
  - `defect`: a real bug or behavior problem.
  - `question/design`: a design question, preference, nit or merge conflict.
  - `lint (CI)`: something a linter or formatter would catch.
- Copilot rows (`C…`):
  - `useful`: correct and worth raising.
  - `noise`: correct but not worth a reviewer's time.
  - `wrong`: incorrect, or doesn't apply. The `.github/workflows.disabled` comments are an artifact of the replay, so they're `wrong`.

**`matches`** (Copilot rows only): the maintainer row ids (`M…`) whose problem this comment raises. Separate several with spaces. Leave it empty if there are none.

Then run `python3 compare_labels.py`. It prints agreement with the first-pass labels, every row where you differ, and the final score using your labels.
