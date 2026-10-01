"""Replay PR diffs in a sandbox repo so Copilot can review them with and without guidance.

Each replay is two synthetic commits: a snapshot of the PR's merge base and a snapshot of the
commit maintainers first reviewed, so the sandbox PR shows exactly the diff they saw. Snapshots
carry neutral commit messages, so nothing referencing upstream issues is pushed.
`.github/workflows` is renamed in every snapshot so the sandbox doesn't run otelc's CI.

Dry run by default. Pass --push to create branches and PRs, --request-review to ask Copilot.

  python3 replay.py --set pilot --clone ../opentelemetry-go-compile-instrumentation \\
      --guidance-ref chore/copilot-review-instructions --repo OWNER/otelc-review-replay
"""
import argparse, json, os, shutil, subprocess, sys, tempfile

D = os.path.dirname(os.path.abspath(__file__))
GUIDANCE = ['.github/copilot-instructions.md', '.github/instructions/tool.instructions.md']
# Tuning PRs used only to check the mechanics and the cost before the held-out run.
PILOT = [1362, 674, 612]


def git(clone, *args, env=None, inp=None):
    r = subprocess.run(['git', '-C', clone, *args], capture_output=True, text=True,
                       env={**os.environ, **(env or {})}, input=inp)
    if r.returncode:
        msg = f'git {" ".join(args)} failed: {r.stderr.strip()}'
        tok = os.environ.get('GH_TOKEN')
        sys.exit(msg.replace(tok, '***') if tok else msg)
    return r.stdout.strip()


def gh(*args):
    r = subprocess.run(['gh', *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f'gh {" ".join(args)} failed: {r.stderr.strip()}')
    return r.stdout.strip()


def pilot_entries(prs=None):
    """Base and reviewed commits for the pilot PRs, from the comment data (same rule as heldout)."""
    import glob
    rows = [c for f in glob.glob(f'{D}/data/rc_*.json') for c in json.load(open(f))]
    maint = {'amazingakai', 'darccio', 'NameHaibinZhang', 'ralf0131', 'kakkoyun',
             'pdelewski', 'txabman42', 'y1yang0'}
    out = []
    for n in PILOT:
        cs = [c for c in rows if c['pull_request_url'].endswith(f'/{n}')
              and c['user']['login'] in maint and not c.get('in_reply_to_id')]
        sha = min(cs, key=lambda c: c['created_at'])['original_commit_id']
        mb = gh('api', f'repos/open-telemetry/opentelemetry-go-compile-instrumentation/compare/main...{sha}',
                '--jq', '.merge_base_commit.sha')
        out.append({'pr': n, 'base_commit': mb, 'review_commit': sha})
    return out


def snapshot(clone, commit, extra_blobs, parent=None, msg='snapshot'):
    """Commit the tree of `commit` with workflows renamed and `extra_blobs` added."""
    tmp = tempfile.mkdtemp()
    env = {'GIT_INDEX_FILE': os.path.join(tmp, 'index')}
    try:
        git(clone, 'read-tree', f'{commit}^{{tree}}', env=env)
        for line in git(clone, 'ls-files', '-s', '--', '.github/workflows', env=env).splitlines():
            meta, path = line.split('\t', 1)
            mode, blob, _ = meta.split()
            git(clone, 'update-index', '--force-remove', path, env=env)
            new = path.replace('.github/workflows', '.github/workflows.disabled', 1)
            git(clone, 'update-index', '--add', '--cacheinfo', f'{mode},{blob},{new}', env=env)
        for path, blob in extra_blobs.items():
            git(clone, 'update-index', '--add', '--cacheinfo', f'100644,{blob},{path}', env=env)
        tree = git(clone, 'write-tree', env=env)
    finally:
        shutil.rmtree(tmp)
    args = ['commit-tree', tree, '-m', msg] + (['-p', parent] if parent else [])
    return git(clone, *args, env={'GIT_AUTHOR_NAME': 'replay', 'GIT_AUTHOR_EMAIL': 'replay@invalid',
                                  'GIT_COMMITTER_NAME': 'replay', 'GIT_COMMITTER_EMAIL': 'replay@invalid'})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--set', choices=['pilot', 'heldout'], required=True)
    ap.add_argument('--scope', default='tool', help='heldout scope to replay (tool or instrumentation)')
    ap.add_argument('--clone', required=True, help='local otelc clone with an "upstream" remote')
    ap.add_argument('--guidance-ref', required=True, help='branch in --clone holding the guidance files')
    ap.add_argument('--repo', required=True, help='sandbox repo OWNER/NAME (not a fork)')
    ap.add_argument('--runs', type=int, default=1)
    ap.add_argument('--prs', type=int, nargs='*', help='limit to these upstream PR numbers')
    ap.add_argument('--push', action='store_true')
    ap.add_argument('--request-review', action='store_true')
    a = ap.parse_args()

    if a.push and json.loads(gh('api', f'repos/{a.repo}', '--jq', '{f:.fork}'))['f']:
        sys.exit('refusing: sandbox repo is a fork, PRs could target upstream')

    entries = pilot_entries() if a.set == 'pilot' else [
        p for p in json.load(open(f'{D}/heldout.json'))['picked'] if p['scope'] == a.scope]
    if a.prs:
        entries = [e for e in entries if e['pr'] in a.prs]
    blobs = {p: git(a.clone, 'rev-parse', f'{a.guidance_ref}:{p}') for p in GUIDANCE}
    tok = os.environ.get('GH_TOKEN')
    url = f'https://x-access-token:{tok}@github.com/{a.repo}.git' if tok else f'https://github.com/{a.repo}.git'
    log = []
    for e in entries:
        git(a.clone, 'fetch', '-q', 'upstream', e['base_commit'], e['review_commit'])
        for cond in ('baseline', 'guided'):
            extra = blobs if cond == 'guided' else {}
            for run in range(1, a.runs + 1):
                base = snapshot(a.clone, e['base_commit'], extra)
                head = snapshot(a.clone, e['review_commit'], extra, parent=base, msg='change')
                bb, hb = f"r/{e['pr']}/{cond}/{run}/base", f"r/{e['pr']}/{cond}/{run}/head"
                rec = {'pr': e['pr'], 'condition': cond, 'run': run, 'base_branch': bb, 'head_branch': hb}
                diff = git(a.clone, 'diff', '--shortstat', base, head)
                print(f"{e['pr']} {cond} r{run}: {diff}")
                if a.push:
                    git(a.clone, 'push', '-q', url, f'{base}:refs/heads/{bb}', f'{head}:refs/heads/{hb}')
                    num = gh('api', '-X', 'POST', f'repos/{a.repo}/pulls', '-f', f'title=replay {e["pr"]} {cond} r{run}',
                             '-f', f'head={hb}', '-f', f'base={bb}', '-f', 'body=Evaluation replay.', '--jq', '.number')
                    rec['sandbox_pr'] = int(num)
                    if a.request_review:
                        gh('api', '-X', 'POST', f'repos/{a.repo}/pulls/{num}/requested_reviewers',
                           '-f', 'reviewers[]=copilot-pull-request-reviewer[bot]')
                log.append(rec)
    out = f'{D}/replay_{a.set}.json'
    json.dump({'guidance_ref': a.guidance_ref, 'guidance_blobs': blobs, 'runs': log}, open(out, 'w'), indent=1)
    print(('pushed' if a.push else 'dry run,') + f' {len(log)} replays -> {out}')


if __name__ == '__main__':
    main()
