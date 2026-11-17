"""Deterministic family split with test coverage of every represented level.

Run only when intentionally constructing a release, before export.py; this writes
the split column and summary, never labels or reference solutions.
"""
import hashlib,json
from collections import Counter,defaultdict
from common import ROOT,read_jsonl,jsonl,dump

def assign(items):
    groups=defaultdict(list)
    for q in items:groups[q['family_id']].append(q)
    rank=lambda f:hashlib.sha256(('probability-core-v1/'+f).encode()).hexdigest()
    split={}
    for f in groups:
        b=int(rank(f)[:8],16)%10
        split[f]='dev' if b<2 else ('validation' if b<4 else 'test')
    for level in sorted({q['difficulty'] for q in items}):
        if not any(split[f]=='test' and any(q['difficulty']==level for q in qs) for f,qs in groups.items()):
            candidates=[f for f,qs in groups.items() if any(q['difficulty']==level for q in qs)]
            chosen=min(candidates,key=lambda f:(len(groups[f]),rank(f)))
            split[chosen]='test'
    return [dict(q,split=split[q['family_id']]) for q in items]

if __name__=='__main__':
    items=assign(read_jsonl(ROOT/'data/items.jsonl'));jsonl('data/items.jsonl',items)
    summary=json.loads((ROOT/'data/summary.json').read_text(encoding='utf8'))
    summary['splits']=dict(sorted(Counter(q['split'] for q in items).items()))
    dump('data/summary.json',summary)
    print(summary['splits'])
