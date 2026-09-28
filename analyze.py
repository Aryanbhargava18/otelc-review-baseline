import json, glob, re, collections, os, sys

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
MAINT = {'amazingakai', 'darccio', 'NameHaibinZhang', 'ralf0131', 'kakkoyun',
         'pdelewski', 'txabman42', 'y1yang0'}
COPILOT = {'Copilot', 'copilot-pull-request-reviewer[bot]', 'copilot-pull-request-reviewer'}

rows = []
for f in sorted(glob.glob(f'{D}/rc_*.json'), key=lambda p: int(re.findall(r'\d+', p)[-1])):
    d = json.load(open(f))
    if isinstance(d, list):
        rows += d
byid = {c['id']: c for c in rows}
print('total inline review comments:', len(rows),
      'range', rows[0]['created_at'][:10] if rows else '', rows[-1]['created_at'][:10] if rows else '')

def pr(c): return int(c['pull_request_url'].rsplit('/', 1)[1])
def who(c):
    l = c['user']['login']
    return 'copilot' if l in COPILOT else 'maint' if l in MAINT else 'other'
def line(c): return c.get('original_line') or c.get('line') or c.get('original_position') or 0

top = [c for c in rows if not c.get('in_reply_to_id')]
cop = [c for c in top if who(c) == 'copilot']
mnt = [c for c in top if who(c) == 'maint']
oth = [c for c in top if who(c) == 'other']
cop_prs = {pr(c) for c in cop}; mnt_prs = {pr(c) for c in mnt}
both = cop_prs & mnt_prs
if '--shared-prs' in sys.argv:
    print(' '.join(map(str, sorted(both)))); sys.exit()
print(f'top-level: copilot={len(cop)} on {len(cop_prs)} PRs | maintainers={len(mnt)} on {len(mnt_prs)} PRs | others={len(oth)}')
print('PRs with both copilot and maintainer inline comments:', len(both))
print('maintainer comment counts:', collections.Counter(c['user']['login'] for c in mnt).most_common())

# Recall proxy: maintainer comment has a Copilot comment on same file within +-10 lines (same PR)
idx = collections.defaultdict(list)
for c in cop: idx[(pr(c), c['path'])].append(line(c))
m_both = [c for c in mnt if pr(c) in both]
same_file = sum(1 for c in m_both if idx.get((pr(c), c['path'])))
near = sum(1 for c in m_both if any(abs(l - line(c)) <= 10 for l in idx.get((pr(c), c['path']), [])))
print(f'on shared PRs: maintainer comments={len(m_both)}, copilot touched same file={same_file}, same spot(+-10 lines)={near}'
      + (f' -> {near/len(m_both):.0%}' if m_both else ''))

# Replies to Copilot comments
replies = collections.defaultdict(list)
for c in rows:
    if c.get('in_reply_to_id'): replies[c['in_reply_to_id']].append(c)
ACC = re.compile(r'\b(fixed|done|good catch|addressed|updated|applied|nice catch|thanks|changed|resolved|agreed|makes sense)\b', re.I)
REJ = re.compile(r"(not applicable|intentional|false positive|won'?t|n/a|incorrect|no need|by design|not needed|not relevant|ignore|this is fine|not an issue|wrong|doesn'?t apply|not true)", re.I)
acc = rej = unk = none = maint_reply = 0
for c in cop:
    rs = replies.get(c['id'], [])
    if not rs: none += 1; continue
    if any(who(r) == 'maint' for r in rs): maint_reply += 1
    t = ' '.join(r['body'] for r in rs)
    if REJ.search(t): rej += 1
    elif ACC.search(t): acc += 1
    else: unk += 1
print(f'copilot comments: no reply={none}, accepted-ish={acc}, rejected-ish={rej}, unclear={unk}, maintainer replied={maint_reply}')

# Where comments land
def area(p):
    parts = p.split('/')
    return '/'.join(parts[:3]) if parts[0] in ('tool', 'pkg') else '/'.join(parts[:2])
print('maintainer comments by area:', collections.Counter(area(c['path']) for c in mnt).most_common(12))
print('copilot comments by area:   ', collections.Counter(area(c['path']) for c in cop).most_common(12))

# Theme buckets (rough keyword classifier)
THEMES = [
    ('tests', r'\b(test|assert|coverage|golden|e2e|testcase|require\.)'),
    ('nil/panic safety', r'\b(nil|panic|deref|bounds|index out)'),
    ('error handling', r'\b(err\b|error|errors\.|wrap|return err)'),
    ('concurrency', r'\b(race|mutex|lock|goroutine|concurrent|atomic|sync\.)'),
    ('perf/alloc', r'\b(alloc|performance|hot path|benchmark|overhead|cache)'),
    ('semconv/telemetry', r'\b(semconv|attribute|span|metric|otel|semantic)'),
    ('rules/AST/trampoline', r'\b(rule|ast|trampoline|hook|directive|inject|toolexec)'),
    ('naming/style', r'\b(rename|naming|name|style|nit|typo|comment|godoc)'),
    ('scope/design', r'\b(scope|separate pr|split|design|why do we|why not|instead|approach|simpler|unnecessary)'),
    ('deps/build', r'\b(go\.mod|dependency|crosslink|replace|bundle|makefile|version)'),
    ('docs', r'\b(doc|readme|changelog|\.md\b)'),
]
def themes(b):
    return [n for n, rx in THEMES if re.search(rx, b, re.I)] or ['uncategorized']
def dist(cs):
    cnt = collections.Counter(t for c in cs for t in themes(c['body']))
    n = len(cs) or 1
    return {k: f'{v/n:.0%}' for k, v in cnt.most_common()}
print('maintainer themes:', dist(mnt))
print('copilot themes:   ', dist(cop))
print('copilot comments with suggestion blocks:', sum('```suggestion' in c['body'] for c in cop))

# Sample maintainer comments on shared PRs that Copilot missed entirely (same file untouched)
missed = [c for c in m_both if not idx.get((pr(c), c['path']))]
print('\n--- sample maintainer comments Copilot missed (file untouched) ---')
for c in missed[:25]:
    print(f"#{pr(c)} {c['user']['login']} {c['path']}:{line(c)} :: {c['body'][:220]!r}")
print('\n--- sample copilot comments that got rejected-ish replies ---')
k = 0
for c in cop:
    rs = replies.get(c['id'], [])
    t = ' '.join(r['body'] for r in rs)
    if rs and REJ.search(t):
        print(f"#{pr(c)} {c['path']} :: COPILOT {c['body'][:160]!r}\n    REPLY {t[:200]!r}")
        k += 1
        if k >= 12: break
