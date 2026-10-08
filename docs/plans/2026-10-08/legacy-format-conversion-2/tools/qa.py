#!/usr/bin/env python3
"""T2 질문·답 번호 정렬 — 인자: 노트 폴더. 1-question/3-answer 를 제자리에서 고친다(마크업만).
질문: `**N. (태그)** 본문` → `N. **(태그)** 본문` (`**N.** 본문` → `N. 본문`). 이미 `N. ` 이면 그대로.
답(파일 안에 `**N.` 줄이 있으면 굵은 모드, 없으면 목록 모드):
  `**N. 제목**`(뒤 본문 없음)      → `### N. 제목`
  `**N. (태그)** 본문`               → `### N. (태그)` + 빈 줄 + `본문`
  `**N.** 본문` / `N. 본문`          → `### N. (질문의 태그)` + 빈 줄 + `본문` (목록 모드는 이어지는 3칸 들여쓰기 줄을 3칸 내어씀)
질문 태그 = 질문 줄 머리 `(…)`/`[…]`. 없으면 멈춘다(--tag N=텍스트 로 지정).
답 번호 목록이 질문 번호 목록과 다르면 아무것도 쓰지 않고 멈춘다(--allow-mismatch 로 무시하고 쓰기)."""
import re, sys

def fence_flags(lines):
    out, fence = [], None
    for l in lines:
        m = re.match(r'^\s*(`{3,}|~{3,})(.*)$', l)
        if m and fence is None:
            fence = m.group(1); out.append(True); continue
        if fence and m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not m.group(2).strip():
            fence = None; out.append(True); continue
        out.append(fence is not None)
    return out

def main(folder, extra):
    tags = {}
    for e in extra:
        if e.startswith('--tag='):
            n, t = e[6:].split('=', 1); tags[int(n)] = t
    qp, ap = f'{folder}/1-question.md', f'{folder}/3-answer.md'
    Q = open(qp, encoding='utf-8').read().split('\n'); F = fence_flags(Q)
    out = []; qs = []; stop = False
    for l, f in zip(Q, F):
        if l.startswith('## 복습 기록'): stop = True
        if not f and not stop:
            m = re.match(r'^\*\*(\d+)\.\s*(.*?)\*\*(.*)$', l)
            if m:
                l = f'{m.group(1)}. **{m.group(2)}**{m.group(3)}' if m.group(2) else f'{m.group(1)}. {m.group(3).lstrip()}'
            m = re.match(r'^(\d+)\. (?:\*\*)?(\([^)]*\)|\[[^\]]*\])', l)
            if re.match(r'^(\d+)\. ', l):
                n = int(l.split('.')[0]); qs.append(n)
                if m and n not in tags: tags[n] = m.group(2)
        out.append(l)
    A = open(ap, encoding='utf-8').read().split('\n'); FA = fence_flags(A)
    bold = any(re.match(r'^\*\*\d+\.', l) for l, f in zip(A, FA) if not f)
    res = []; ans = []; dedent = False
    for l, f in zip(A, FA):
        if not f or dedent:
            m1 = re.match(r'^\*\*(\d+)\.\s*(.*?)\*\*(.*)$', l) if bold and not f else None
            m2 = re.match(r'^(\d+)\. (.*)$', l) if not bold and not f else None
            if (m1 or m2) and res and res[-1].strip():
                res.append('')
            if m1:
                n, x, rest = int(m1.group(1)), m1.group(2).strip(), m1.group(3).strip()
                if x and not rest:
                    res += [f'### {n}. {x}']
                elif x:
                    res += [f'### {n}. {x}', '', rest]
                else:
                    if n not in tags: sys.exit(f'질문 {n} 태그 없음 — --tag={n}=…')
                    res += [f'### {n}. {tags[n]}', '', rest]
                ans.append(n); continue
            if m2:
                n = int(m2.group(1))
                if n not in tags: sys.exit(f'질문 {n} 태그 없음 — --tag={n}=…')
                res += [f'### {n}. {tags[n]}', '', m2.group(2)]
                ans.append(n); dedent = True; continue
            if dedent and not f and (l.startswith('#') or (l.strip() and not l.startswith('   '))):
                dedent = False
            if dedent and l.startswith('   '):
                l = l[3:]
        res.append(l)
    if ans != qs and '--allow-mismatch' not in extra:
        sys.exit(f'번호 불일치 q={qs} a={ans} — 쓰지 않음')
    open(qp, 'w', encoding='utf-8').write('\n'.join(out))
    open(ap, 'w', encoding='utf-8').write('\n'.join(res))
    print(f'OK {folder}: q={qs} a={ans}')

if __name__ == '__main__':
    main(sys.argv[1].rstrip('/'), sys.argv[2:])
