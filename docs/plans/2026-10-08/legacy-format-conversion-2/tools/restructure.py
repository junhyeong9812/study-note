#!/usr/bin/env python3
"""T2 2-summary 재구성 — 인자: 2-summary.md 경로, plan.json 경로. 파일을 제자리에서 다시 쓴다.
plan.json:
  {"pre": "7절 이름" | null,            # H1과 첫 `## ` 사이 머리말을 옮길 곳(null=머리말 없을 때만)
   "map": [["원래 ## 헤딩 텍스트", "7절 이름" | "="], ...],   # 순서 = 7절 안 배치 순서. "=" 는 같은 이름 7절에 내용 그대로(헤딩 없이)
           ["원래 ## 헤딩>>원래 ### 하위 헤딩", "7절 이름", "새 ### 헤딩(선택)"]   # (v2) 하위 절 하나만 빼서 옮기기(결정 3)
   "supp": {"7절 이름": "보충 마크다운"}, # 7절 맨 앞
   "supp_end": {"7절 이름": "..."}}       # 7절 맨 뒤
보충 앞에는 HTML 주석 + 보이는 표식 `*(Claude 보충 — 노트 본문 요약)*`이 자동으로 붙는다(이미 표식으로 시작하면 생략).
원래 `## X`는 `### X`로, 그 안 헤딩은 한 단계씩 내린다(코드 펜스 안은 손대지 않음).
하위 절 빼기: `### Y`(와 그 아래 ####…)를 부모에서 떼어 `### Y`(또는 지정한 새 헤딩 — 원래 Y 문자열을 포함해야 함)로 둔다. 하위 단계는 원래 단계 그대로.
원래 ## 절이 map에 하나라도 빠지거나 7절이 비면 에러로 멈춘다.
v2(2026-10-08): 펜스 판별 CommonMark식(검사기와 같음) · 보이는 보충 표식 · `>>` 하위 절 빼기. v1 계획 파일은 그대로 동작."""
import json, re, sys

SK = ['해결하는 문제', '동작·원리', '쓰이는 자료구조·알고리즘', '적용 — 풀어나가는 법',
      '장애 시나리오와 대처', '핵심 문장', '관련 주제·근거']
MARK = '<!-- 보충: 노트 본문 요약·참조 (legacy-format-conversion-2) -->'
VMARK = '*(Claude 보충 — 노트 본문 요약)*'

def fence_flags(lines):
    """줄마다 '펜스 안(여닫는 줄 포함)' 여부."""
    out, fence = [], None
    for l in lines:
        m = re.match(r'^\s*(`{3,}|~{3,})(.*)$', l)
        if m and fence is None:
            fence = m.group(1); out.append(True); continue
        if fence and m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not m.group(2).strip():
            fence = None; out.append(True); continue
        out.append(fence is not None)
    return out

def split(text):
    L = text.split('\n'); F = fence_flags(L)
    h1 = None; pre = []; secs = []; cur = None
    for l, inside in zip(L, F):
        if not inside and h1 is None and l.startswith('# '):
            h1 = l; continue
        if not inside and l.startswith('## '):
            cur = [l[3:].strip(), []]; secs.append(cur); continue
        (cur[1] if cur else pre).append(l)
    return h1, pre, secs

def demote(lines):
    out = []
    for l, inside in zip(lines, fence_flags(lines)):
        if not inside and re.match(r'^#{1,5} ', l):
            l = '#' + l
        elif not inside and re.match(r'^###### ', l):
            sys.exit(f'헤딩 6단계를 더 내릴 수 없음: {l}')
        out.append(l)
    return out

def cut_sub(content, sub):
    """content(## 절 본문)에서 `### sub` 블록을 떼어 (남은 것, 뗀 블록 본문) 반환."""
    F = fence_flags(content)
    idx = [i for i, (l, f) in enumerate(zip(content, F)) if not f and l.startswith('### ') and l[4:].strip() == sub]
    if len(idx) != 1:
        sys.exit(f'하위 절 "{sub}" 를 정확히 하나 찾지 못함({len(idx)})')
    i = idx[0]; j = len(content)
    for k in range(i + 1, len(content)):
        if not F[k] and re.match(r'^#{1,3} ', content[k]):
            j = k; break
    return content[:i] + content[j:], content[i + 1:j]

def trim(lines):
    while lines and not lines[0].strip(): lines = lines[1:]
    while lines and not lines[-1].strip(): lines = lines[:-1]
    return lines

def supp_block(v):
    v = v.strip('\n')
    return [MARK] + ([] if v.startswith(VMARK) else [VMARK, '']) + v.split('\n')

def main(path, plan_path):
    plan = json.load(open(plan_path, encoding='utf-8'))
    text = open(path, encoding='utf-8').read()
    h1, pre, secs = split(text)
    sec = {s[0]: s[1] for s in secs}
    names = [s[0] for s in secs]
    if len(set(names)) != len(names): sys.exit(f'원래 ## 헤딩 중복: {names}')
    mapped = [m[0] for m in plan['map'] if '>>' not in m[0]]
    if sorted(names) != sorted(mapped):
        sys.exit(f'map 불일치\n원래: {names}\nmap: {mapped}')
    # 하위 절 먼저 떼기
    cut = {}
    for m in plan['map']:
        if '>>' in m[0]:
            parent, sub = [x.strip() for x in m[0].split('>>', 1)]
            if parent not in sec: sys.exit(f'부모 절 없음: {parent}')
            sec[parent], cut[m[0]] = cut_sub(sec[parent], sub)
    body = {k: [] for k in SK}
    if trim(pre):
        if not plan.get('pre'):
            sys.exit('머리말이 있는데 pre 미지정')
        body[plan['pre']].append(trim(pre))
    for m in plan['map']:
        name, tgt = m[0], m[1]
        if '>>' in name:
            sub = name.split('>>', 1)[1].strip()
            head = m[2] if len(m) > 2 else sub
            if sub not in head: sys.exit(f'새 헤딩은 원래 하위 헤딩 문자열을 포함해야 함: {head}')
            body[tgt].append(['### ' + head, ''] + trim(cut[name]))
            continue
        content = sec[name]
        if tgt == '=':
            if name not in SK: sys.exit(f'"=" 는 7절 이름과 같은 절만: {name}')
            body[name].append(trim(content))
        else:
            body[tgt].append(['### ' + name, ''] + trim(demote(content)))
    for k, v in plan.get('supp', {}).items():
        body[k].insert(0, supp_block(v))
    for k, v in plan.get('supp_end', {}).items():
        body[k].append(supp_block(v))
    out = [h1, '']
    for k in SK:
        if not any(trim(b) for b in body[k]): sys.exit(f'7절 비어 있음: {k} — 보충 필요')
        out += ['## ' + k, '']
        for blk in body[k]:
            if trim(blk): out += blk + ['']
    open(path, 'w', encoding='utf-8').write('\n'.join(out).rstrip('\n') + '\n')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
