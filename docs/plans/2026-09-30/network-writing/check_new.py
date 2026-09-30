#!/usr/bin/env python3
"""새 커리큘럼 노트 검증기 — 인자: 노트 폴더(여러 개).
7절 골격 순서 · Q/A 번호 일치(6~10) · 빈 절/빈 불릿 0 · 새 상대 링크 실존 · 초안 표기 · 리프 md만."""
import os, re, sys

SK = ['해결하는 문제', '동작·원리', '쓰이는 자료구조·알고리즘', '적용 — 풀어나가는 법',
      '장애 시나리오와 대처', '핵심 문장', '관련 주제·근거']

def strip_fences(text):
    """코드 펜스 안 줄은 빈 줄로(줄 번호 유지) — `# 주석`을 헤딩으로 오인하지 않게."""
    out, inside = [], False
    for l in text.split('\n'):
        if re.match(r'^\s*(```|~~~)', l):
            inside = not inside; out.append(l); continue
        out.append('' if inside else l)
    return '\n'.join(out)

def empty_sections(text):
    text = strip_fences(text)
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

def links(folder, text):
    bad = []
    for t in re.findall(r'\]\(\s*<?([^)\s>]+)', re.sub(r'`[^`\n]*`', '', text)):
        if re.match(r'^[a-z]+:', t) or t.startswith(('#', '/')):
            continue
        p = t.split('#')[0].split('?')[0]
        if p and not os.path.exists(os.path.normpath(os.path.join(folder, p))):
            bad.append(t)
    return bad

def check(folder):
    folder = folder.rstrip('/')
    errs = []
    files = {}
    for f in ('1-question.md', '2-summary.md', '3-answer.md'):
        p = os.path.join(folder, f)
        if not os.path.exists(p):
            errs.append(f'{f} 없음'); continue
        files[f] = open(p, encoding='utf-8').read()
    for x in os.listdir(folder):
        if not x.endswith('.md'):
            errs.append(f'비-md 파일 {x}')
    if len(files) < 3:
        return errs
    s = files['2-summary.md']
    top = [re.sub(r'^## ', '', l).strip() for l in strip_fences(s).split('\n') if l.startswith('## ')]
    if top != SK:
        errs.append(f'2-summary 최상위 헤딩 {top} != {SK}')
    for f, t in files.items():
        if 'Claude 초안' not in t and '✅ 검수 완료' not in t:
            errs.append(f'{f}: 초안/검수 표기 없음')
        e = empty_sections(t)
        if e:
            errs.append(f'{f}: 빈 절 {e[:3]}')
        if re.search(r'^\s*-\s*$', t, flags=re.M):
            errs.append(f'{f}: 빈 불릿')
        bl = links(folder, t)
        if bl:
            errs.append(f'{f}: 깨진 링크 {bl[:3]}')
    q = [int(m) for m in re.findall(r'^(\d+)\. ', files['1-question.md'].split('## 복습 기록')[0], flags=re.M)]
    a = [int(m) for m in re.findall(r'^### (\d+)\. ', files['3-answer.md'], flags=re.M)]
    if q != a:
        errs.append(f'Q/A 번호 불일치 q={q} a={a}')
    elif not (6 <= len(q) <= 10):
        errs.append(f'질문 수 {len(q)} (6~10)')
    return errs

if __name__ == '__main__':
    bad = 0
    for d in sys.argv[1:]:
        e = check(d)
        print(('FAIL ' if e else 'PASS ') + d)
        for x in e:
            print('    ', x)
        bad += bool(e)
    print(f'== {len(sys.argv) - 1 - bad} PASS / {bad} FAIL')
    sys.exit(1 if bad else 0)
