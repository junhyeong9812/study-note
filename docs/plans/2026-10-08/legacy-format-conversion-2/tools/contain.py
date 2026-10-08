#!/usr/bin/env python3
"""T2 무손실 대조 — 인자: 노트 폴더(저장소 기준 상대경로, 예 cs/systems/thrashing) 여러 개.
폴더의 각 *.md(HEAD에 있던 파일)마다 HEAD 토큰 다중집합이 작업 트리 파일 다중집합에 포함되는지 검사.
토큰화: 줄마다 `**` 제거 → 줄 머리의 헤딩 `#`, 목록 기호 `- `/`* `/`+ `, 번호 `N. ` 반복 제거 → 공백 분리.
줄 보조 검사: 같은 정규화를 한 비어 있지 않은 원래 줄(공백 정리)도 새 파일에 다중집합으로 모두 있어야 한다.
출력: OK/FAIL 파일 · 빠진 토큰(FAIL 시) · 추가 토큰 수. -v 면 추가 토큰 목록.
환경변수 REPO(기본 /home/jun/project/study-note), BASE(기본 HEAD)."""
import os, re, subprocess, sys
from collections import Counter

REPO = os.environ.get('REPO', '/home/jun/project/study-note')
BASE = os.environ.get('BASE', 'HEAD')
HEAD_RE = re.compile(r'^\s*(?:#{1,6}\s+)?(?:(?:[-*+]|\d+\.)\s+)*')

def toks(text):
    c = Counter()
    for line in text.split('\n'):
        s = line.replace('**', '')
        s = HEAD_RE.sub('', s, count=1)
        c.update(s.split())
    return c

def lines(text):
    """줄 단위 보조 검사 — 정규화한 비어 있지 않은 줄 다중집합(보충이 같은 단어를 다시 써서 삭제를 가리는 것 방지)."""
    c = Counter()
    for line in text.split('\n'):
        s = ' '.join(HEAD_RE.sub('', line.replace('**', ''), count=1).split())
        s = re.sub(r'^(\([^)]{1,40}\)|\[[^\]]{1,40}\])\s*', '', s)   # v2: 줄 머리 질문 태그 (…)/[…] 무시 — 태그는 토큰 검사가 지킴
        if s: c[s] += 1
    return c

def head_files(folder):
    out = subprocess.run(['git', '-C', REPO, 'ls-tree', '--name-only', BASE, folder.rstrip('/') + '/'],
                         capture_output=True, text=True, check=True).stdout.split()
    return [p for p in out if p.endswith('.md')]

def main(args):
    verbose = '-v' in args
    dirs = [a for a in args if a != '-v']
    bad = 0; total_add = 0
    for d in dirs:
        files = head_files(d)
        if not files:
            print(f'FAIL {d}: HEAD에 md 없음'); bad += 1; continue
        for p in files:
            old = subprocess.run(['git', '-C', REPO, 'show', f'{BASE}:{p}'], capture_output=True,
                                 text=True, check=True).stdout
            fp = os.path.join(REPO, p)
            if not os.path.exists(fp):
                print(f'FAIL {p}: 작업 트리에 없음'); bad += 1; continue
            new = open(fp, encoding='utf-8').read()
            a, b = toks(old), toks(new)
            missing = a - b
            lmiss = lines(old) - lines(new)
            added = b - a
            n_add = sum(added.values()); total_add += n_add
            if missing or lmiss:
                bad += 1
                print(f'FAIL {p}: 빠진 토큰 {sum(missing.values())}개 {list(missing.items())[:20]} · 빠진 줄 {sum(lmiss.values())}개 {list(lmiss)[:5]} · 추가 {n_add}')
            else:
                print(f'OK   {p}: 추가 토큰 {n_add}')
            if verbose and added:
                print('     추가:', ' '.join(t for t, n in added.items() for _ in range(n)))
    print(f'== FAIL {bad} · 추가 토큰 합계 {total_add}')
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main(sys.argv[1:])
