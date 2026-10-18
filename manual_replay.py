"""Manual fallback for the held-out replay: Copilot review run by hand in VS Code.

Copilot code review on github.com is not available on the account's plan, so each replay is a
local worktree that holds the PR's reviewed diff as staged changes on top of its merge base, with
the guidance files committed on both sides for the `guided` condition (same trees as replay.py).
You run Copilot's review in VS Code and paste its comments into the matching output file;
`ingest` turns those files into the layout evaluate.py reads (set `manual`).

  python3 manual_replay.py prepare --clone ../opentelemetry-go-compile-instrumentation \\
      --guidance-ref chore/copilot-review-instructions --dest ../manual-replay
  # review each worktree in VS Code, fill in manual/outputs/*.md
  python3 manual_replay.py ingest
  python3 evaluate.py sheet --set manual    # then label, then: evaluate.py score --set manual
"""
import argparse, glob, json, os, re, subprocess, sys

import replay

D = os.path.dirname(os.path.abspath(__file__))
OUT = f'{D}/manual/outputs'
RUNS = 2  # per condition, as in PREREGISTRATION.md

TEMPLATE = """<!-- {rid}: PR {pr}, {cond}, run {run}. Worktree: {wt}
Paste every comment Copilot leaves in this run as:

### path/to/file.go:LINE
comment text

Use a fresh review each run. If Copilot leaves no comments, replace this whole file with
the single line NO COMMENTS. Leave the file untouched if the run could not be done. -->
"""


def prepare(a):
    entries = [p for p in json.load(open(f'{D}/heldout.json'))['picked'] if p['scope'] == a.scope]
    blobs = {p: replay.git(a.clone, 'rev-parse', f'{a.guidance_ref}:{p}') for p in replay.GUIDANCE}
    source_blobs = dict(blobs)
    if a.strip_exclude_agent:
        # The CLI counts as the coding/cloud agent, so `excludeAgent: "cloud-agent"` hides the files
        # from it. Same text, minus that line, so the CLI loads them like github.com code review does.
        for p, b in blobs.items():
            text = replay.git(a.clone, 'cat-file', 'blob', b) + '\n'
            text = ''.join(l for l in text.splitlines(True) if not l.startswith('excludeAgent:'))
            blobs[p] = replay.git(a.clone, 'hash-object', '-w', '--stdin', inp=text)
    dest = os.path.abspath(a.dest)
    os.makedirs(OUT, exist_ok=True)
    runs = []
    for e in entries:
        for cond in ('baseline', 'guided'):
            extra = blobs if cond == 'guided' else {}
            base = replay.snapshot(a.clone, e['base_commit'], extra)
            head = replay.snapshot(a.clone, e['review_commit'], extra, parent=base, msg='change')
            wt = f"{dest}/{e['pr']}-{cond}"
            if not os.path.exists(wt):
                replay.git(a.clone, 'worktree', 'add', '-q', '--detach', wt, base)
                # Stage the reviewed state so the PR diff is exactly the uncommitted change.
                replay.git(wt, 'read-tree', '-m', '-u', head)
            stat = replay.git(wt, 'diff', '--cached', '--shortstat')
            print(f"{e['pr']} {cond}: {wt} ({stat})")
            for run in range(1, RUNS + 1):
                rid = f"{e['pr']}-{cond}-r{run}"
                path = f'{OUT}/{rid}.md'
                if not os.path.exists(path):
                    open(path, 'w').write(TEMPLATE.format(rid=rid, pr=e['pr'], cond=cond, run=run, wt=wt))
                runs.append({'pr': e['pr'], 'condition': cond, 'run': run, 'worktree': wt,
                             'sandbox_pr': rid})
    json.dump({'guidance_ref': a.guidance_ref, 'guidance_blobs': source_blobs, 'guidance_blobs_used': blobs,
               'strip_exclude_agent': a.strip_exclude_agent, 'mode': a.mode,
               'runs': runs}, open(f'{D}/replay_manual.json', 'w'), indent=1)
    print(f'{len(runs)} runs -> replay_manual.json, output templates in {OUT}')


def parse(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S).strip()
    if not text:
        return None
    if text == 'NO COMMENTS':
        return []
    out = []
    for block in re.split(r'^### ', text, flags=re.M)[1:]:
        head, _, body = block.partition('\n')
        path, _, line = head.strip().rpartition(':')
        if not path or not line.strip().isdigit():
            path, line = head.strip(), ''
        out.append({'path': path, 'line': int(line) if line.strip().isdigit() else None, 'body': body.strip()})
    return out


def ingest(a):
    runs = json.load(open(f'{D}/replay_manual.json'))['runs']
    os.makedirs(f'{D}/data/replay/manual', exist_ok=True)
    missing = []
    for r in runs:
        rid = r['sandbox_pr']
        comments = parse(open(f'{OUT}/{rid}.md').read())
        if comments is None:
            missing.append(rid)
            comments = []
        bad = [c for c in comments if not c['body']]
        if bad:
            sys.exit(f'{rid}: a "### path:line" heading has no comment text under it')
        data = {'reviews': [{'user': {'login': 'copilot-vscode'}}] if rid not in missing else [],
                'comments': [{'id': f'{rid}-{i}', 'user': {'login': 'copilot-vscode'}, 'path': c['path'],
                              'line': c['line'], 'original_line': c['line'], 'body': c['body']}
                             for i, c in enumerate(comments)]}
        json.dump(data, open(f'{D}/data/replay/manual/{rid}.json', 'w'), indent=1)
        print(f"{rid}: {'MISSING' if rid in missing else str(len(comments)) + ' comments'}")
    if missing:
        print(f'\n{len(missing)} runs not done yet: {" ".join(missing)}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['prepare', 'ingest'])
    ap.add_argument('--scope', default='tool')
    ap.add_argument('--clone', help='local otelc clone with an "upstream" remote (prepare)')
    ap.add_argument('--guidance-ref', help='branch in --clone holding the guidance files (prepare)')
    ap.add_argument('--dest', default=f'{D}/../manual-replay', help='where to put the worktrees (prepare)')
    ap.add_argument('--strip-exclude-agent', action='store_true',
                    help='drop the excludeAgent line from the guidance copies (needed for the Copilot CLI)')
    ap.add_argument('--mode', default='vscode-manual', help='how the reviews are run, recorded in replay_manual.json')
    a = ap.parse_args()
    if a.cmd == 'prepare' and not (a.clone and a.guidance_ref):
        ap.error('prepare needs --clone and --guidance-ref')
    {'prepare': prepare, 'ingest': ingest}[a.cmd](a)
