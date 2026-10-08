#!/usr/bin/env python3
"""cs 노트 검증기 — 인자: 노트 폴더(여러 개) 또는 --all(cs/ 아래 1-question.md가 있는 폴더 전부).
error(exit 1): 7절 골격 순서 · Q/A 번호 일치(6~10) · 빈 절/빈 불릿 0 · 새 상대 링크 실존 · metadata.md 단계·날짜 ·
  제목 형식 · 제목 아래 머리말 없음 · 코드 펜스 언어 태그 · 리프 md만.
warning(출력만, exit code 불변): 장애 항목 3~6 · 핵심 문장 3~6 · 펜스 밖 '항상·반드시·절대'.
  metadata `형식 | 과제 이식`·`원고 이관` 노트는 warning 제외.
(2026-10-08 rules-checker: docs/plans/2026-09-30/network-writing/check_new.py에서 이동)"""
import datetime, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

SK = ['해결하는 문제', '동작·원리', '쓰이는 자료구조·알고리즘', '적용 — 풀어나가는 법',
      '장애 시나리오와 대처', '핵심 문장', '관련 주제·근거']

def strip_fences(text):
    """코드 펜스 안 줄은 빈 줄로(줄 번호 유지) — `# 주석`을 헤딩으로 오인하지 않게."""
    out, fence = [], None   # 2026-10-08: 닫는 펜스는 여는 펜스와 같은 문자·길이 이상, 뒤에 정보 문자열 없음(CommonMark)
    for l in text.split('\n'):
        m = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', l)
        if m and fence is None:
            fence = m.group(1); out.append(l); continue
        if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not m.group(2).strip():
            fence = None; out.append(l); continue
        out.append('' if fence else l)
    return '\n'.join(out)

def untagged_fences(text):
    """정보 문자열(언어 태그) 없는 여는 펜스의 줄 번호(1부터). 닫는 펜스 판정은 strip_fences와 같다."""
    bad, fence = [], None
    for i, l in enumerate(text.split('\n'), 1):
        m = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', l)
        if m and fence is None:
            fence = m.group(1)
            if not m.group(2).strip():
                bad.append(i)
            continue
        if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not m.group(2).strip():
            fence = None
    return bad

KIND = {'1-question.md': '질문', '2-summary.md': '정리', '3-answer.md': '정답'}

def title_error(f, title, rel):
    """제목 = `# <cs/ 기준 폴더 경로> — …`, 마지막 ` — ` 조각이 질문/정리/정답(파일별)으로 시작."""
    pre = f'# {rel} — '
    if not title.startswith(pre):
        return f'{f}: 제목이 `{pre}…` 형식이 아님 ({title.strip()[:60]})'
    if not title[len(pre):].split(' — ')[-1].startswith(KIND[f]):
        return f'{f}: 제목 끝 조각이 `{KIND[f]}`로 시작하지 않음 ({title.strip()[:60]})'
    return None

STAGES = ('원고', '초안', '검수', '학습')

def metadata_errors(mt):
    """단계 칸 정확히 하나 · 초안·검수·학습 칸은 각 하나, 값은 `—` 또는 `YYYY-MM-DD`(뒤에 ` (…)` 허용) ·
    현재 단계의 날짜 칸은 채워져 있고, 그 뒤 단계의 날짜 칸은 `—`."""
    errs = []
    rows = re.findall(r'^\| 단계 \| (\S+) \|', mt, flags=re.M)   # 생성기와 같은 파서
    if len(rows) != 1 or rows[0] not in STAGES:
        return [f'metadata.md: 단계 칸은 원고·초안·검수·학습 중 정확히 하나 ({rows})']
    st = rows[0]
    dated = {}
    for k in STAGES[1:]:
        v = re.findall(r'^\| ' + k + r' \| (.*?) \|\s*$', mt, flags=re.M)
        if len(v) != 1:
            errs.append(f'metadata.md: {k} 칸이 정확히 하나가 아님 ({len(v)})'); continue
        v = v[0].strip()
        if v == '—':
            dated[k] = False; continue
        m = re.match(r'^(\d{4}-\d{2}-\d{2})( \(.+\))?$', v)
        try:
            ok = bool(m) and datetime.date.fromisoformat(m.group(1))
        except ValueError:
            ok = False
        if not ok:
            errs.append(f'metadata.md: {k} 칸은 `—` 또는 `YYYY-MM-DD` ({v})')
        dated[k] = True
    if errs:
        return errs
    i = STAGES.index(st)
    if st != '원고' and not dated[st]:
        errs.append(f'metadata.md: 단계가 {st}인데 {st} 날짜 칸이 `—`')
    for k in STAGES[i + 1:]:
        if dated[k]:
            errs.append(f'metadata.md: 단계가 {st}인데 뒤 단계 {k} 날짜가 있음')
    return errs

def section(text, name):
    m = re.search(r'^## ' + re.escape(name) + r'\s*$(.*?)(?=^## |\Z)', text, flags=re.M | re.S)
    return m.group(1) if m else ''

def warnings(files):
    """warning 후보 — 출력만. 장애 항목 = `###` 헤딩 수, 없으면 `**1.`·`**1)`·`**①` 굵은 번호 줄 수.
    핵심 문장 = 그 절의 최상위 목록 항목(`- `·`1. `) 수. 금지어 = 세 파일 펜스 밖 '항상·반드시·절대'."""
    w = []
    s = strip_fences(files['2-summary.md'])
    j = section(s, '장애 시나리오와 대처')
    n = len(re.findall(r'^### ', j, flags=re.M)) or len(re.findall(r'^\*\*(\d+[.)]|[①-⑳])', j, flags=re.M))
    if not 3 <= n <= 6:
        w.append(f'장애 항목 {n}개 (3~6)')
    k = len(re.findall(r'^(- |\d+\. )', section(s, '핵심 문장'), flags=re.M))
    if not 3 <= k <= 6:
        w.append(f'핵심 문장 {k}개 (3~6)')
    for f, t in files.items():
        hits = re.findall(r'항상|반드시|절대', strip_fences(t))
        if hits:
            w.append(f'{f}: 단정어 {len(hits)}회 (' + ' · '.join(f'{x} {hits.count(x)}' for x in ('항상', '반드시', '절대') if x in hits) + ')')
    return w

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
    """(errors, warnings)를 돌려준다."""
    folder = folder.rstrip('/')
    errs, warns = [], []
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
        return errs, warns
    s = files['2-summary.md']
    top = [re.sub(r'^## ', '', l).strip() for l in strip_fences(s).split('\n') if l.startswith('## ')]
    if top != SK:
        errs.append(f'2-summary 최상위 헤딩 {top} != {SK}')
    # 2026-10-01 header-cleanup: 상태는 metadata.md, 제목 아래 인용문 머리말 금지
    mp = os.path.join(folder, 'metadata.md')
    legacy = False
    if not os.path.exists(mp):
        errs.append('metadata.md 없음')
    else:
        mt = open(mp, encoding='utf-8').read()
        legacy = bool(re.search(r'^\| 형식 \| (과제 이식|원고 이관) \|', mt, flags=re.M))
        errs += metadata_errors(mt)
    rel = os.path.relpath(os.path.abspath(folder), os.path.join(ROOT, 'cs')).replace(os.sep, '/')
    for f, t in files.items():
        L = t.split('\n')
        s = 0
        h = next((i for i in range(s, len(L)) if L[i].strip()), None)   # 첫 비어 있지 않은 줄 = H1이어야 한다
        if h is None or not L[h].startswith('# '):
            errs.append(f'{f}: 첫 줄이 H1이 아님')
        else:
            te = title_error(f, L[h], rel)
            if te:
                errs.append(te)
            j = h + 1
            while j < len(L) and L[j].strip() == '':
                j += 1
            if j < len(L) and (L[j].startswith('>') or re.search(r'Claude 초안|✅ 검수 완료', L[j])):
                errs.append(f'{f}: 제목 아래 머리말·표식')
        e = empty_sections(t)
        if e:
            errs.append(f'{f}: 빈 절 {e[:3]}')
        if re.search(r'^\s*-\s*$', t, flags=re.M):
            errs.append(f'{f}: 빈 불릿')
        bl = links(folder, strip_fences(t))   # 2026-10-08: 코드 펜스 안 `[a..b]` 오탐 제외
        if bl:
            errs.append(f'{f}: 깨진 링크 {bl[:3]}')
        uf = untagged_fences(t)
        if uf:
            errs.append(f'{f}: 언어 태그 없는 코드 펜스 {len(uf)}개 (줄 {uf[:5]})')
    q = [int(m) for m in re.findall(r'^(\d+)\. ', files['1-question.md'].split('## 복습 기록')[0], flags=re.M)]
    a = [int(m) for m in re.findall(r'^### (\d+)\. ', files['3-answer.md'], flags=re.M)]
    if q != a:
        errs.append(f'Q/A 번호 불일치 q={q} a={a}')
    elif not (6 <= len(q) and (len(q) <= 10 or legacy)):   # 2026-10-08: metadata `형식 | 과제 이식`·`원고 이관`(질문 무손실 이관)은 상한만 면제
        errs.append(f'질문 수 {len(q)} (6~10)')
    if not legacy:
        warns = warnings(files)
    return errs, warns

def all_leaves():
    """cs/ 아래 1-question.md가 있는 폴더 전부(저장소 루트 기준 상대 경로, 정렬)."""
    out = []
    for dp, dn, fn in os.walk(os.path.join(ROOT, 'cs')):
        if '1-question.md' in fn:
            out.append(os.path.relpath(dp, ROOT))
    return sorted(out)

if __name__ == '__main__':
    args = sys.argv[1:]
    if args == ['--all']:
        os.chdir(ROOT)
        args = all_leaves()
    elif not args or '--all' in args:
        sys.exit('사용법: check_notes.py <노트 폴더>... | --all')
    bad = nw = 0
    for d in args:
        e, w = check(d)
        print(('FAIL ' if e else 'PASS ') + d)
        for x in e:
            print('    ', x)
        for x in w:
            print('     WARN', x)
        bad += bool(e)
        nw += len(w)
    print(f'== {len(args) - bad} PASS / {bad} FAIL · WARN {nw}건(exit code 무관)')
    sys.exit(1 if bad else 0)
