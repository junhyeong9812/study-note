#!/usr/bin/env python3
"""curriculum.md → cs/<area>/README.md (또는 기존 컬렉션과 이름이 겹치면 cs/<area>/curriculum.md) 생성.
생성물은 직접 고치지 않는다 — curriculum.md를 고친 뒤 재실행한다. (cs-restructure 2026-09-28)
--check: 쓰지 않고 현재 파일과 비교만 한다 — 다른 파일을 출력하고 exit 1.
(2026-10-08 rules-checker: docs/plans/2026-09-28/cs-restructure/에서 이동, metadata.md 없는 노트 폴더는 실패)"""
import os, re, glob, sys
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
CUR = os.path.join(R, 'docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md')
COLLIDE = {'algorithm', 'data-structure', 'domain-modeling', 'api-design'}   # 기존 컬렉션 README 보존

def load():
    s = open(CUR, encoding='utf-8').read()
    heads = [(m.start(), m.group(1), m.group(2), m.group(3)) for m in
             re.finditer(r'^## (\d+[a-z]?)\. (.+?) \(`([a-z-]+)/`\)(.*)$', s, flags=re.M)]
    ends = [m.start() for m in re.finditer(r'^## ', s, flags=re.M)]
    out = []
    for st, num, title, area in heads:
        en = min([e for e in ends if e > st] + [len(s)])
        out.append((num, title, area, s[st:en]))
    return out

def resolve(p):
    p = p.strip().rstrip('/')
    p = re.sub(r'^(cs/)?foundations/languages', 'languages', p)
    p = re.sub(r'^(cs/)?foundations/web-api', 'languages/web-api', p)
    p = re.sub(r'^(cs/)?foundations/python-basics', 'languages/python/basics', p)
    for c in ([p] if p.startswith(('languages', 'issue', 'cs/', 'project', 'lab', 'history', 'opensource')) else ['cs/' + p, p]):
        if os.path.exists(os.path.join(R, c)):
            return c
        g = glob.glob(os.path.join(R, c + '-*'))
        if len(g) == 1:
            return os.path.relpath(g[0], R)
    return None

def notes(exist):
    if exist.startswith('신규'):
        return []
    head = re.split(r'\(?연결', exist)[0]
    res = []
    for p in re.findall(r'`([^`]+)`', head):
        x = resolve(p)
        if x and x not in res:
            res.append(x)
    return res

STAGE = re.compile(r'^\| 단계 \| (\S+) \|', flags=re.M)

def stage_of(dd):
    """노트 폴더의 metadata.md 「단계」 칸 → 원고·초안·검수·학습. 없으면 실패(옛 표식 폴백 없음, 2026-10-08)."""
    m = os.path.join(dd, 'metadata.md')
    if not os.path.exists(m):
        raise SystemExit(f'metadata.md 없음: {os.path.relpath(dd, R)}')   # 조용한 폴백 금지
    rows = STAGE.findall(open(m, encoding='utf-8').read())
    if len(rows) != 1 or rows[0] not in ('원고', '초안', '검수', '학습'):
        raise SystemExit(f'metadata.md 단계 칸 오류: {m} → {rows}')   # 조용한 폴백 금지
    return rows[0]

def status(paths):
    """노트 폴더마다 metadata.md의 단계를 읽는다: 검수·학습 → 검수 완료 · 초안 → 초안(Claude) · 원고 → 원고 있음."""
    if not paths:
        return '미작성'
    reviewed, drafts = [], []
    for p in paths:
        d = os.path.join(R, p)
        if not os.path.isdir(d):
            continue
        dirs = [d] if os.path.exists(os.path.join(d, '1-question.md')) else sorted(
            os.path.dirname(x) for x in glob.glob(os.path.join(d, '*', '1-question.md')))   # 컬렉션 폴더
        for dd in dirs:
            st = stage_of(dd)
            reviewed.append(st in ('검수', '학습'))
            drafts.append(st == '초안')
    if reviewed and all(reviewed):
        return '검수 완료'
    if any(drafts):
        return '초안(Claude)'
    return '원고 있음'

def render(num, title, area, body, outdir):
    intro = [l for l in body.split('\n')[1:12] if l.startswith('>')]
    lines = [f'# {title} — `cs/{area}/` 커리큘럼', '',
             '> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §' + num +
             '에서 `scripts/notes/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.',
             '> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.',
             ''] + intro + ['']
    cnt = {'미작성': 0, '원고 있음': 0, '초안(Claude)': 0, '검수 완료': 0}
    secs = re.split(r'^(?=### )', body, flags=re.M)
    groups = [('주제 목록', secs[0])] + [(x.split('\n', 1)[0][4:], x) for x in secs[1:]]
    for h, sec in groups:
        rows = []
        for l in sec.split('\n'):
            if re.match(r'^\| \d{2}-', l):
                c = [x.strip() for x in l.split('|')]
                ps = notes(c[8])
                leaf = f'cs/{area}/{c[1]}'   # 새 커리큘럼 노트(cs/<area>/NN-slug/)는 폴더 존재로 찾는다
                if os.path.exists(os.path.join(R, leaf, '1-question.md')):
                    ps = [leaf] + [p for p in ps if p != leaf]   # 새 leaf가 있으면 먼저, 원고는 뒤에 링크 유지
                st = status(ps); cnt[st] += 1
                links = ' · '.join(f'[{os.path.relpath(os.path.join(R, p), outdir)}]({os.path.relpath(os.path.join(R, p), outdir)}{"/" if os.path.isdir(os.path.join(R, p)) else ""})' for p in ps) or '—'
                rows.append((c[1], f'| {c[1][:2]} | `{c[1][3:]}` | {c[2]} | {c[7]} | {st} | {links} |'))
        if not rows:
            continue
        lines += [f'## {h}', '', '| # | 주제 | 요지 | 등급 | 상태 | 노트 |', '|---|---|---|---|---|---|']
        lines += [r for _, r in sorted(rows)] + ['']
    lines.insert(4, '> 현황: ' + ' · '.join(f'{k} {v}' for k, v in cnt.items()))
    return '\n'.join(lines).rstrip() + '\n', cnt

if __name__ == '__main__':
    args = sys.argv[1:]
    if args not in ([], ['--check']):
        sys.exit('사용법: gen_area_readme.py [--check]')
    check = args == ['--check']
    outs = []   # 전부 렌더링한 뒤에 쓴다 — 중간 실패(metadata 없음 등) 때 일부만 갱신되지 않게
    for num, title, area, body in load():
        outdir = os.path.join(R, 'cs', area)
        fn = 'curriculum.md' if area in COLLIDE else 'README.md'
        txt, cnt = render(num, title, area, body, outdir)
        outs.append((f'cs/{area}/{fn}', os.path.join(outdir, fn), txt, cnt))
    if check:
        stale = []
        for name, out, txt, _ in outs:
            cur = open(out, encoding='utf-8').read() if os.path.exists(out) else None
            if cur != txt:
                stale.append(name)
                print(f'다름: {name}' + (' (파일 없음)' if cur is None else ''))
        print(f'== 생성 문서 {len(stale)}개가 생성기 출력과 다름 — 커리큘럼을 고친 뒤 python3 scripts/notes/gen_area_readme.py 재실행'
              if stale else '== 생성 문서 전부 생성기 출력과 같음')
        sys.exit(1 if stale else 0)
    total = {}
    for name, out, txt, cnt in outs:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, 'w', encoding='utf-8').write(txt)
        for k, v in cnt.items():
            total[k] = total.get(k, 0) + v
        print(name, cnt)
    print('TOTAL', total)
