"""Collect Copilot's replay reviews, build a blind scoring sheet, and compute the metrics.

  python3 evaluate.py collect --set pilot --repo OWNER/otelc-review-replay
  python3 evaluate.py sheet   --set pilot      # writes score_pilot.csv (condition hidden)
  # fill in the `label` and `matches` columns, then:
  python3 evaluate.py score   --set pilot

Sheet columns:
  maintainer rows: label = defect | question/design | lint (CI)
  copilot rows:    label = useful | noise | wrong
                   matches = space-separated maintainer row ids this comment raises the same issue as
"""
import argparse, csv, glob, json, os, random, subprocess, sys, collections

D = os.path.dirname(os.path.abspath(__file__))
MAINT = {'amazingakai', 'darccio', 'NameHaibinZhang', 'ralf0131', 'kakkoyun',
         'pdelewski', 'txabman42', 'y1yang0'}


def gh_json(path):
    r = subprocess.run(['gh', 'api', '--paginate', '--slurp', path], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f'gh api {path} failed: {r.stderr.strip()}')
    return [x for page in json.loads(r.stdout) for x in page]


def collect(a):
    runs = json.load(open(f'{D}/replay_{a.set}.json'))
    out = f'{D}/data/replay/{a.set}'
    os.makedirs(out, exist_ok=True)
    for r in runs:
        n = r['sandbox_pr']
        reviews = gh_json(f'repos/{a.repo}/pulls/{n}/reviews?per_page=100')
        comments = gh_json(f'repos/{a.repo}/pulls/{n}/comments?per_page=100')
        if not any('copilot' in rv['user']['login'].lower() for rv in reviews):
            print(f'sandbox PR {n} ({r["pr"]} {r["condition"]} r{r["run"]}): no Copilot review yet')
        json.dump({'reviews': reviews, 'comments': comments}, open(f'{out}/{n}.json', 'w'), indent=1)
    print(f'collected {len(runs)} sandbox PRs into {out}')


def sheet(a):
    runs = json.load(open(f'{D}/replay_{a.set}.json'))
    rows = [c for f in glob.glob(f'{D}/data/rc_*.json') for c in json.load(open(f))]
    rng = random.Random(f'{a.set}-blind')
    items, key = [], {}
    for pr in sorted({r['pr'] for r in runs}):
        for c in sorted((c for c in rows if c['pull_request_url'].endswith(f'/{pr}')
                         and c['user']['login'] in MAINT and not c.get('in_reply_to_id')),
                        key=lambda c: c['created_at']):
            items.append({'kind': 'maintainer', 'pr': pr, 'id': f'M{c["id"]}', 'path': c['path'],
                          'line': c.get('original_line') or '', 'text': ' '.join(c['body'].split()),
                          'label': '', 'matches': ''})
        cop = []
        for r in (r for r in runs if r['pr'] == pr):
            data = json.load(open(f'{D}/data/replay/{a.set}/{r["sandbox_pr"]}.json'))
            for c in data['comments']:
                if 'copilot' in c['user']['login'].lower() and not c.get('in_reply_to_id'):
                    cop.append((c, r))
        rng.shuffle(cop)
        for i, (c, r) in enumerate(cop):
            cid = f'C{pr}-{i}'
            key[cid] = {'condition': r['condition'], 'run': r['run']}
            items.append({'kind': 'copilot', 'pr': pr, 'id': cid, 'path': c['path'],
                          'line': c.get('original_line') or c.get('line') or '',
                          'text': ' '.join(c['body'].split()), 'label': '', 'matches': ''})
    with open(f'{D}/score_{a.set}.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(items[0]))
        w.writeheader()
        w.writerows(items)
    json.dump(key, open(f'{D}/score_{a.set}_key.json', 'w'), indent=1)
    print(f'wrote score_{a.set}.csv ({len(items)} rows). Do not open score_{a.set}_key.json until labelling is done.')


def score(a):
    runs = json.load(open(f'{D}/replay_{a.set}.json'))
    key = json.load(open(f'{D}/score_{a.set}_key.json'))
    items = list(csv.DictReader(open(f'{D}/score_{a.set}.csv')))
    missing = [i['id'] for i in items if not i['label']]
    if missing:
        sys.exit(f'{len(missing)} rows still unlabelled, e.g. {missing[:5]}')
    defects = {i['id']: i for i in items if i['kind'] == 'maintainer' and i['label'] == 'defect'}
    conds = sorted({(r['condition'], r['run']) for r in runs})
    prs = {r['pr'] for r in runs}
    print(f'{len(prs)} PRs, {len(defects)} maintainer-found defects\n')
    print(f'{"condition":<14}{"recall":>14}{"comments":>10}{"useful":>9}{"noise":>8}{"wrong":>8}{"noise+wrong/PR":>16}')
    for cond, run in conds:
        cs = [i for i in items if i['kind'] == 'copilot' and key[i['id']] == {'condition': cond, 'run': run}]
        found = {m for i in cs for m in i['matches'].split() if m in defects}
        lab = collections.Counter(i['label'] for i in cs)
        n = len(cs) or 1
        print(f'{cond + " r" + str(run):<14}{len(found):>6}/{len(defects):<3}({len(found)/max(1, len(defects)):.0%})'
              f'{len(cs):>10}{lab["useful"]/n:>9.0%}{lab["noise"]/n:>8.0%}{lab["wrong"]/n:>8.0%}'
              f'{(lab["noise"] + lab["wrong"]) / len(prs):>16.1f}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['collect', 'sheet', 'score'])
    ap.add_argument('--set', choices=['pilot', 'heldout'], required=True)
    ap.add_argument('--repo')
    a = ap.parse_args()
    {'collect': collect, 'sheet': sheet, 'score': score}[a.cmd](a)
