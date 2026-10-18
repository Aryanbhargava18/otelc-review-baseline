"""Compare the human blind labels (score_manual_human.csv) with the AI labels (score_manual.csv),
then score the replay with the human labels.

  python3 compare_labels.py
"""
import csv, collections, os, subprocess, shutil, sys

D = os.path.dirname(os.path.abspath(__file__))
ai = {r['id']: r for r in csv.DictReader(open(f'{D}/score_manual.csv'))}
hu = {r['id']: r for r in csv.DictReader(open(f'{D}/score_manual_human.csv'))}
todo = [i for i, r in hu.items() if not r['label']]
if todo:
    sys.exit(f'{len(todo)} rows in score_manual_human.csv still have no label, e.g. {todo[:5]}')
same = sum(ai[i]['label'] == hu[i]['label'] for i in hu)
cop = [i for i in hu if hu[i]['kind'] == 'copilot']
match_same = sum(set(ai[i]['matches'].split()) == set(hu[i]['matches'].split()) for i in cop)
print(f'label agreement: {same}/{len(hu)} ({same/len(hu):.0%}); copilot match agreement: {match_same}/{len(cop)}')
for i in hu:
    if ai[i]['label'] != hu[i]['label'] or (i in cop and set(ai[i]['matches'].split()) != set(hu[i]['matches'].split())):
        print(f'  differs {i}: AI {ai[i]["label"]} [{ai[i]["matches"]}]  human {hu[i]["label"]} [{hu[i]["matches"]}]')
# score with the human labels
shutil.copy(f'{D}/score_manual.csv', f'{D}/score_manual_ai.csv')
shutil.copy(f'{D}/score_manual_human.csv', f'{D}/score_manual.csv')
print('\nscore with human labels:', flush=True)
subprocess.run([sys.executable, f'{D}/evaluate.py', 'score', '--set', 'manual'])
print('\n(AI labels kept in score_manual_ai.csv)')
