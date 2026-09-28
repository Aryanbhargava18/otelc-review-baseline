"""Recompute co-location using hand labels (labels.json) and review ordering (data/reviews)."""
import json, glob, os, collections

D = os.path.dirname(os.path.abspath(__file__))
COPILOT = {'Copilot', 'copilot-pull-request-reviewer[bot]'}
MAINT = {'amazingakai', 'darccio', 'NameHaibinZhang', 'ralf0131', 'kakkoyun',
         'pdelewski', 'txabman42', 'y1yang0'}

labels = json.load(open(f'{D}/labels.json'))
copilot_first = {}
for f in glob.glob(f'{D}/data/reviews/*.json'):
    rv = json.load(open(f))
    c = [r['submitted_at'] for r in rv if r['user']['login'] in COPILOT]
    m = [r['submitted_at'] for r in rv if r['user']['login'] in MAINT]
    copilot_first[int(os.path.basename(f)[:-5])] = bool(c and m and min(c) < min(m))

print('labels:', dict(collections.Counter(l['label'] for l in labels)))
d = [l for l in labels if l['label'] == 'defect']
near = sum(l['near_copilot'] for l in d)
print(f'concrete defects: {len(d)}, Copilot commented nearby: {near} ({near/len(d):.0%})')
cf = [l for l in d if copilot_first.get(l['pr'])]
print(f'PRs where Copilot reviewed first: {sum(copilot_first.values())}/{len(copilot_first)}; '
      f'defects maintainers still raised there: {len(cf)}, in spots Copilot never touched: '
      f'{sum(not l["near_copilot"] for l in cf)}')
