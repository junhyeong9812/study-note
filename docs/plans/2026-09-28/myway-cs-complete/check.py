#!/usr/bin/env python3
"""myway-cs-complete 검증기 — 노트 폴더 인자(여러 개). 기준 = BASE 커밋의 옛 버전.
보존(옛 본문 줄 ⊆ 새 본문 줄, 다중집합) · 헤딩 텍스트 보존 · 2-summary 골격 7절 순서 · C절 번호 일치 · 빈 곳 0."""
import os, re, subprocess, sys, collections

BASE = '2c54fd70'
R = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True).stdout.strip()
SK_DS = ['해결하는 문제', '동작·원리', '쓰이는 곳', '적용 — 풀어나가는 법', '장애 시나리오와 대처', '핵심 문장', '관련 주제·근거']
SK_OT = ['해결하는 문제', '동작·원리', '쓰이는 자료구조·알고리즘', '적용 — 풀어나가는 법', '장애 시나리오와 대처', '핵심 문장', '관련 주제·근거']

def old(path):
    r = subprocess.run(['git', 'show', f'{BASE}:{path}'], cwd=R, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None

def body_lines(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    out = []
    for l in text.split('\n'):
        s = l.rstrip()
        if not s.strip() or re.match(r'^\s*-\s*$', s) or re.match(r'^#{1,6} ', s):
            continue
        out.append(s)
    return out

def heads(text):
    return [re.sub(r'^#{1,6} ', '', l).strip() for l in text.split('\n') if re.match(r'^#{1,6} ', l)]

def empty_sections(text):
    L = text.split('\n')
    hs = [(i, len(m.group(1)), l) for i, l in enumerate(L) for m in [re.match(r'^(#{1,6}) ', l)] if m]
    bad = []
    for k, (i, lv, h) in enumerate(hs):
        j = len(L)
        for i2, lv2, _ in hs[k + 1:]:
            if lv2 <= lv:
                j = i2; break
        b = '\n'.join(L[i + 1:j])
        b = re.sub(r'<!--.*?-->', '', b, flags=re.S)
        b = re.sub(r'^#{1,6} .*$', '', b, flags=re.M)
        b = re.sub(r'^\s*-\s*$', '', b, flags=re.M)
        b = re.sub(r'^\|[\s|:-]*\|$', '', b, flags=re.M)
        if not b.strip() and '복습 기록' not in h:
            bad.append(h.strip())
    return bad

def check(folder):
    folder = folder.rstrip('/')
    rel = os.path.relpath(os.path.abspath(folder), R)
    coll_ds = rel.startswith('cs/data-structure') or rel.startswith('cs/algorithm')
    errs = []
    for f in ('1-question.md', '2-summary.md', '3-answer.md'):
        p = os.path.join(R, rel, f)
        new = open(p, encoding='utf-8').read()
        o = old(f'{rel}/{f}')
        if o is None:
            errs.append(f'{f}: 옛 버전 없음'); continue
        miss = collections.Counter(body_lines(o)) - collections.Counter(body_lines(new))
        if miss:
            errs.append(f'{f}: 옛 본문 줄 {sum(miss.values())}개 누락 — 예: {list(miss)[0][:80]!r}')
        hm = collections.Counter(heads(o)) - collections.Counter(heads(new))
        if hm:
            errs.append(f'{f}: 옛 헤딩 누락 {list(hm)[:3]}')
        e = empty_sections(new)
        if e:
            errs.append(f'{f}: 빈 절 {e[:3]}')
        if re.search(r'^\s*-\s*$', new, flags=re.M):
            errs.append(f'{f}: 빈 불릿 줄')
        if f == '2-summary.md':
            top = [re.sub(r'^## ', '', l).strip() for l in new.split('\n') if l.startswith('## ')]
            want = SK_DS if coll_ds else SK_OT
            if top != want:
                errs.append(f'2-summary: 최상위 헤딩 {top} != {want}')
            if '2026-09-28: 통일 골격' not in new:
                errs.append('2-summary: 헤더 표시 줄 없음')
    q = open(os.path.join(R, rel, '1-question.md'), encoding='utf-8').read()
    a = open(os.path.join(R, rel, '3-answer.md'), encoding='utf-8').read()
    cq = sorted(set(re.findall(r'\bC(\d+)\b', q.split('### C. 통일 골격')[-1]))) if '### C. 통일 골격' in q else []
    ca = sorted(set(re.findall(r'\bC(\d+)\b', a.split('### C. 통일 골격')[-1]))) if '### C. 통일 골격' in a else []
    if not cq:
        errs.append('1-question: C절 없음')
    if cq != ca:
        errs.append(f'C 번호 불일치 q={cq} a={ca}')
    elif not (4 <= len(cq) <= 6):
        errs.append(f'C 질문 수 {len(cq)} (4~6 권장)')
    return rel, errs

if __name__ == '__main__':
    bad = 0
    for d in sys.argv[1:]:
        rel, errs = check(d)
        if errs:
            bad += 1
            print('FAIL', rel)
            for e in errs:
                print('   ', e)
        else:
            print('PASS', rel)
    print(f'== {len(sys.argv) - 1 - bad} PASS / {bad} FAIL')
    sys.exit(1 if bad else 0)
