"""Run the manual held-out replay with the Copilot CLI, one fresh non-interactive session per run.

Each run reviews the staged diff in its worktree (see manual_replay.py) read-only: file writes,
network access and state-changing git/shell commands are denied, and the worktree is checked
to be unchanged afterwards. The reply goes to manual/outputs/<run>.md for `manual_replay.py
ingest`; the raw reply, the model `auto` resolved to and the AI credits used go to manual/raw/.

  python3 cli_review.py                 # every run whose output file is still the template
  python3 cli_review.py --only 1326-guided-r1
"""
import argparse, glob, json, os, re, subprocess, sys

import manual_replay

D = os.path.dirname(os.path.abspath(__file__))
RAW = f'{D}/manual/raw'
PROMPT = ('Review the staged changes in this repository (git diff --cached) as a pull request review. '
          'Do not modify any files. Report each finding as a line `### path:line` followed by the '
          'comment on the next lines. If you have no findings, reply with exactly NO COMMENTS.')
DENY = ['write', 'url', 'shell(git push)', 'shell(git commit)', 'shell(git reset)', 'shell(git checkout)',
        'shell(git stash)', 'shell(git restore)', 'shell(git add)', 'shell(git rm)', 'shell(git apply)',
        'shell(git clean)', 'shell(git switch)', 'shell(rm:*)', 'shell(mv:*)', 'shell(cp:*)', 'shell(go:*)',
        'shell(make:*)', 'shell(curl:*)', 'shell(wget:*)', 'shell(npm:*)', 'shell(pip:*)', 'shell(touch:*)',
        'shell(tee:*)']


def state(wt):
    staged = subprocess.run(['git', '-C', wt, 'diff', '--cached'], capture_output=True, text=True).stdout
    other = subprocess.run(['git', '-C', wt, 'status', '--porcelain'], capture_output=True, text=True).stdout
    return staged, [l for l in other.splitlines() if not re.match(r'^[MADR] ', l)]


def resolved_model(session):
    events = os.path.expanduser(f'~/.copilot/session-state/{session}/events.jsonl')
    if not os.path.exists(events):
        return ''
    found = re.findall(r'"model(?:Id)?":"([^"]+)"', open(events).read())
    return ', '.join(sorted({m for m in found if m != 'auto'}))


def run(r, timeout):
    rid, wt = r['sandbox_pr'], r['worktree']
    before = state(wt)
    cmd = ['copilot', '-C', wt, '-p', PROMPT, '--model', 'auto', '--allow-all-tools', '--disallow-temp-dir']
    for d in DENY:
        cmd += ['--deny-tool', d]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    out = p.stdout
    log, _, tail = out.partition('\nChanges ')
    # stdout is the tool log followed by the final answer; keep only what follows the last tool block
    lines = log.splitlines()
    last = max([i for i, l in enumerate(lines) if l.startswith(('  └', '  │', '● ', '/ ', '✗ '))], default=-1)
    reply = '\n'.join(lines[last + 1:])
    stats = tail + '\n' + p.stderr  # the CLI prints its usage stats on stderr
    credits = (re.search(r'AI Credits\s+([\d.]+)', stats) or [None, ''])[1]
    session = (re.search(r'--resume=([0-9a-f-]+)', stats) or [None, ''])[1]
    model = resolved_model(session) if session else ''
    os.makedirs(RAW, exist_ok=True)
    json.dump({'run': rid, 'returncode': p.returncode, 'model': model, 'ai_credits': credits, 'session': session,
               'stdout': out, 'stderr': p.stderr[-4000:]}, open(f'{RAW}/{rid}.json', 'w'), indent=1)
    after = state(wt)
    if after != before:
        return rid, 'CHANGED THE WORKTREE, not recorded', model, credits
    if p.returncode or not reply.strip():
        return rid, f'failed (exit {p.returncode}), not recorded', model, credits
    reply = reply.strip()
    body = 'NO COMMENTS' if '### ' not in reply and 'NO COMMENTS' in reply else reply
    if '### ' not in body and body != 'NO COMMENTS':
        return rid, 'reply not in the requested format, kept in manual/raw only', model, credits
    open(f'{manual_replay.OUT}/{rid}.md', 'w').write(
        f'<!-- {rid}: Copilot CLI, model auto -> {model or "?"}, {credits or "?"} AI credits, session {session} -->\n'
        f'{body}\n')
    n = len(manual_replay.parse(body) or [])
    used_go = bool(re.search(r'^● [^\n]*\n\s*│ go (test|build|vet|run)', log, re.M))  # ✗ = blocked
    return rid, f'{n} comments' + (' (ran go despite deny!)' if used_go else ''), model, credits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--timeout', type=int, default=900)
    a = ap.parse_args()
    runs = json.load(open(f'{D}/replay_manual.json'))['runs']
    todo = [r for r in runs if (a.only and r['sandbox_pr'] in a.only) or
            (not a.only and manual_replay.parse(open(f'{manual_replay.OUT}/{r["sandbox_pr"]}.md').read()) is None)]
    print(f'{len(todo)} runs to do', flush=True)
    for r in todo:
        try:
            rid, status, model, credits = run(r, a.timeout)
        except subprocess.TimeoutExpired:
            rid, status, model, credits = r['sandbox_pr'], 'timed out, not recorded', '', ''
        print(f'{rid}: {status} | model {model or "?"} | credits {credits or "?"}', flush=True)


if __name__ == '__main__':
    main()
