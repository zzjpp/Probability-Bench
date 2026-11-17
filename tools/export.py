"""Rebuild solver-only inputs, splits, catalog, LaTeX and SHA256 manifest."""
import hashlib,json
from collections import Counter
from common import ROOT,SPLITS,read_jsonl,dump,jsonl

def rebuild():
    items=read_jsonl(ROOT/'data/items.jsonl')
    registry=read_jsonl(ROOT/'sources/exercise_index.jsonl')
    summary=json.loads((ROOT/'data/summary.json').read_text(encoding='utf8'))
    summary.update(n_items=len(items),fully_solved=len(items),
        n_source_exercises_selected=sum(bool(r['canonical_ids']) for r in registry),
        difficulty=dict(sorted(Counter(f"L{q['difficulty']}" for q in items).items())),
        subjects=dict(sorted(Counter(q['subject'] for q in items).items())),
        splits=dict(sorted(Counter(q['split'] for q in items).items())),
        human_verified=sum(q['review']['human_reviewed'] for q in items),
        external_answer_compared=sum(q['review']['external_comparison'] for q in items),
        itemwise_mathematical_reviewed=sum(q['review']['status']=='model_assisted_itemwise_audit' for q in items),
        difficulty_basis='structural_three_axis_v1_not_empirically_calibrated')
    dump('data/summary.json',summary)
    for split in SPLITS:
        selected=[q for q in items if q['split']==split]
        jsonl(f'data/splits/{split}.jsonl',selected)
        jsonl(f'data/inputs/{split}.jsonl',[{k:q[k] for k in ['id','question','question_latex','assets']} for q in selected])
    jsonl('data/inputs/all.jsonl',[{k:q[k] for k in ['id','question','question_latex','assets']} for q in items])
    lines=['# 题目目录','', '题面和解答均内嵌于 `data/items.jsonl`。L1–L8 已按三个结构维度逐题复核，仍待实测校准。','',
           '| ID | 原书题号 | PDF页 | 难度 | 主题 | Split |','|---|---|---:|---|---|---|']
    lines += [f"| {q['id']} | {q['source']['exercise']} | {q['source']['pdf_page']} | L{q['difficulty']} | {q['subject']} | {q['split']} |" for q in items]
    (ROOT/'docs/catalog.md').write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    review=['# 逐题校核依据','',
            '81道题均按当前题面核对定义、全部子问、推导、最终结果、定理条件、边界及评分目标。以下是模型辅助的逐题论证核查记录，不是独立专家审定或形式化证明。', '',
            'D/R/T依次表示方法发现(0–3)、论证深度(0–2)、技术控制(0–2)；等级L=1+D+R+T。分值只是工作性结构规则，未用真实作答数据校准。详见 [难度说明](difficulty.md)。', '',
            '| ID / 原题号 | 等级 | D/R/T | 关键核对结论 |',
            '|---|---|---|---|']
    for q in items:
        p=q['difficulty_profile'];reason=q['review']['mathematical_rationale'].replace('|','&#124;')
        review.append(f"| {q['id']} / {q['source']['exercise']} | L{q['difficulty']} | {p['method_discovery']}/{p['reasoning_depth']}/{p['technical_control']} | {reason} |")
    review+=['','主要外部理论参照：','']
    refs=json.loads((ROOT/'sources/mathematical_references.json').read_text(encoding='utf8'))
    for v in refs.values():review.append(f"- [{v['title']}]({v['url']})，{v['locator']}。{v['scope']}")
    (ROOT/'docs/review.md').write_text('\n'.join(review)+'\n',encoding='utf8',newline='\n')
    # Source only; no claim that a PDF was compiled or visually inspected.
    tex=[r'\documentclass[UTF8]{ctexart}',r'\usepackage{amsmath,amssymb}',r'\begin{document}',r'\section*{Probability-Bench：核心习题}']
    for q in items:
        tex += [r'\subsection*{'+q['id']+f"（L{q['difficulty']}，原书 {q['source']['exercise']}）"+'}',q['question_latex'],'']
    tex += [r'\end{document}']
    (ROOT/'data/questions.tex').write_text('\n'.join(tex)+'\n',encoding='utf8',newline='\n')
    paths=sorted([p for root in ['data','sources','schema'] for p in (ROOT/root).rglob('*') if p.is_file() and p.name!='checksums.json'])
    dump('data/checksums.json',{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    print(f'Exported {len(items)} tasks, splits={dict(Counter(q["split"] for q in items))}')

if __name__=='__main__':rebuild()
