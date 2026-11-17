"""Offline schema-subset and corpus invariants; standard library only.

The published JSON Schema uses only the keywords implemented below. For arbitrary
third-party schemas use a full JSON Schema validator instead.
"""
import hashlib,json,re
from collections import Counter
from pathlib import Path
from common import ROOT,ABILITIES,SPLITS,read_jsonl

def require(ok,message):
    if not ok:raise ValueError(message)

def node(value,spec,path='$'):
    kind=spec['type']
    types={'object':lambda x:isinstance(x,dict),'array':lambda x:isinstance(x,list),
           'string':lambda x:isinstance(x,str),'integer':lambda x:type(x) is int,
           'boolean':lambda x:type(x) is bool}
    require(types[kind](value),f'{path}: expected {kind}')
    if 'enum' in spec:require(value in spec['enum'],f'{path}: unexpected enum value')
    if kind=='object':
        require(set(spec.get('required',[]))<=set(value),f'{path}: required keys missing')
        if spec.get('additionalProperties') is False:require(set(value)<=set(spec['properties']),f'{path}: unknown keys')
        for k,v in value.items():
            if k in spec['properties']:node(v,spec['properties'][k],path+'.'+k)
    elif kind=='array':
        require(len(value)>=spec.get('minItems',0),f'{path}: array too short')
        if spec.get('uniqueItems'):require(len({json.dumps(v,sort_keys=True,ensure_ascii=False) for v in value})==len(value),f'{path}: duplicates')
        for i,v in enumerate(value):node(v,spec['items'],f'{path}[{i}]')
    elif kind=='string':
        require(len(value)>=spec.get('minLength',0),f'{path}: empty string')
        if 'pattern' in spec:require(re.search(spec['pattern'],value) is not None,f'{path}: pattern mismatch')
    elif kind=='integer':
        require(value>=spec.get('minimum',-10**100) and value<=spec.get('maximum',10**100),f'{path}: out of range')

def validate(items=None):
    items=items if items is not None else read_jsonl(ROOT/'data/items.jsonl')
    schema=json.loads((ROOT/'schema/item.schema.json').read_text(encoding='utf8'))
    require(bool(items),'empty benchmark')
    ids=set();families={};questions=set()
    registry=read_jsonl(ROOT/'sources/exercise_index.jsonl')
    by_source={r['exercise']:r for r in registry}
    require(len(registry)==451 and len(by_source)==451,'source index must have 451 unique numbered exercises')
    references=json.loads((ROOT/'sources/mathematical_references.json').read_text(encoding='utf8'))
    for q in items:
        node(q,schema,q.get('id','$'))
        key=q['id'];require(key not in ids,'duplicate ID');ids.add(key)
        normalized=re.sub(r'\s+','',q['question_latex'])
        require(normalized not in questions,'duplicate statement');questions.add(normalized)
        require(q['split'] in SPLITS,'invalid split')
        family=q['family_id'];require(family not in families or families[family]==q['split'],'family leakage across splits');families[family]=q['split']
        rubric=q['scoring_rubric'];require(sum(c['points'] for c in rubric)==4,'rubric must total 4')
        require(len({c['id'] for c in rubric})==len(rubric),'duplicate criterion')
        require(set(q['ability_tags'])=={c['ability'] for c in rubric},'ability tags must match rubric')
        require(set(q['ability_tags'])<=set(ABILITIES),'unknown ability')
        require(len(q['reference_solution'])>=40,'reference solution too short for this corpus')
        for token in ['TODO','待补充','参见答案','略去证明']:
            require(token not in q['reference_solution'],'unresolved reference placeholder')
        require(q['review']['human_reviewed'] is False,'human certification not supported by this release')
        require(q['review']['external_comparison']==bool(q['source']['external_answer_checks']),'external comparison flag mismatch')
        require(set(q['review']['primary_reference_ids'])<=set(references),'unknown mathematical reference')
        require(q['review']['status']=='model_assisted_itemwise_audit','missing itemwise mathematical review')
        profile=q['difficulty_profile']
        level=1+sum(profile[k] for k in ['method_discovery','reasoning_depth','technical_control'])
        require(q['difficulty']==level,'difficulty does not match structural axes')
        require(q['question']==q['question_latex'],'question text and LaTeX diverged')
        numbers=[q['source']['exercise']]+q['source']['equivalent_exercises']
        for number in numbers:require(number in by_source and key in by_source[number]['canonical_ids'],'broken source mapping')
        require(q['source']['pdf_page']==by_source[q['source']['exercise']]['pdf_page'],'wrong PDF locator')
        require(q['source']['printed_page']==q['source']['pdf_page']-24,'printed/PDF page mismatch')
        require(q['assets']==[],'this text core has no required figures')
    require({q['difficulty'] for q in items}==set(range(1,9)),'core must cover all 8 provisional levels')
    require({q['difficulty'] for q in items if q['split']=='test'}==set(range(1,9)),'test must cover all 8 provisional levels')
    for r in registry:
        require(set(r['canonical_ids'])<=ids,'unknown canonical ID in registry')
        require(bool(r['canonical_ids'])==(r['selection_status']=='selected_or_equivalent'),'registry selection mismatch')
    for split in SPLITS:
        selected=[q for q in items if q['split']==split]
        require(selected==read_jsonl(ROOT/f'data/splits/{split}.jsonl'),'stale split export')
        safe=[{k:q[k] for k in ['id','question','question_latex','assets']} for q in selected]
        require(safe==read_jsonl(ROOT/f'data/inputs/{split}.jsonl'),'unsafe/stale solver input')
    checksums=json.loads((ROOT/'data/checksums.json').read_text(encoding='utf8'))
    for path,expected in checksums.items():
        require(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,f'checksum mismatch: {path}')
    summary=json.loads((ROOT/'data/summary.json').read_text(encoding='utf8'))
    require(summary['n_items']==len(items)==81,'release count mismatch')
    require(summary['fully_solved']==len(items),'solution count mismatch')
    require(summary['external_answer_compared']==sum(q['review']['external_comparison'] for q in items),'comparison count mismatch')
    require(summary['difficulty']==dict(sorted(Counter(f"L{q['difficulty']}" for q in items).items())),'difficulty summary mismatch')
    require(summary['itemwise_mathematical_reviewed']==len(items),'mathematical review count mismatch')
    print(f'Validated {len(items)} tasks; 451 source locators; all solutions, rubrics, families and solver exports consistent.')

if __name__=='__main__':validate()
