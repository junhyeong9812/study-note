#!/usr/bin/env python3
"""무손실 대조(I1·I2) — 인자: 노트 폴더(여러 개). 저장소 루트에서 실행.
git HEAD 판과 작업 트리 판을 같은 정규화로 토큰열로 만들어 비교한다.
정규화(펜스 밖 줄만): 헤딩 기호 `#…`, 줄 머리 `N. `·`- `·`- Ck. `·`N. (Ck) `, `**`, C 질문 줄 끝 `\\` 제거.
펜스 안 줄은 공백만 무시(내용 그대로 비교).
화이트리스트(정당한 차이): 2-summary `## 쓰이는 곳`→`## 쓰이는 자료구조·알고리즘`, metadata `| 형식 | 과제 이식 |` 행 추가.
추가 검사: 원래 번호(0 포함) 순서 보존 · C 꼬리표 순서 보존 · 1-question과 3-answer의 C 번호 부여 일치."""
import os, re, subprocess, sys
ROOT = os.environ.get('AFTER_ROOT', '.')   # dry-run: 작업 트리 대신 사본 경로

FENCE = re.compile(r'^\s*(```|~~~)')
FILES = ('1-question.md', '2-summary.md', '3-answer.md', 'metadata.md')
META_ROW = '| 형식 | 과제 이식 |'


def norm(text):
    toks, inside = [], False
    for l in text.split('\n'):
        if FENCE.match(l):
            inside = not inside
            toks += l.split(); continue
        if not inside:
            c = bool(re.match(r'^\s*(- C\d+\. |#{1,6} \d+\. \(C\d+\) )', l))
            l = re.sub(r'^\s*#{1,6}\s+', '', l)
            l = re.sub(r'^\s*- C\d+\.\s+', '', l)
            l = re.sub(r'^\s*\d+\.\s+\(C\d+\)\s+', '', l)
            l = re.sub(r'^\s*\d+\.\s+', '', l)
            l = re.sub(r'^\s*-\s+', '', l)
            l = l.replace('**', '')
            if c:
                l = re.sub(r'\\\s*$', '', l)
        toks += l.split()
    return toks


def struct(text):
    """(원래 번호 목록, C 꼬리표 목록, C에 부여된 번호 목록) — 펜스 밖, 복습 기록 앞."""
    nums, cs, cn, inside = [], [], [], False
    for l in text.split('\n'):
        if FENCE.match(l):
            inside = not inside; continue
        if inside:
            continue
        if l.startswith('## 복습 기록'):
            break
        m = re.match(r'^(?:#{3,4} )?(\d+)\. \(C(\d+)\) ', l)
        if m:
            cn.append(int(m.group(1))); cs.append(int(m.group(2))); continue
        m = re.match(r'^- C(\d+)\. ', l)
        if m:
            cs.append(int(m.group(1))); continue
        m = re.match(r'^(?:#{3,4} )?(\d+)\. ', l)
        if m:
            nums.append(int(m.group(1)))
    return nums, cs, cn


def git_head(path):
    return subprocess.run(['git', '-C', '/home/jun/project/study-note', 'show', f'HEAD:{path}'], capture_output=True, text=True, check=True).stdout


def check(folder):
    folder = folder.rstrip('/')
    probs = []
    cnums = {}
    for f in FILES:
        p = f'{folder}/{f}'
        before, after = git_head(p), open(os.path.join(ROOT, p), encoding='utf-8').read()
        if f == '2-summary.md':
            before = re.sub(r'^## 쓰이는 곳[ \t]*$', '## 쓰이는 자료구조·알고리즘', before, flags=re.M)
        if f == 'metadata.md':
            if after.count(META_ROW) != 1:
                probs.append('metadata: 형식 행 수 != 1')
            after = after.replace(META_ROW + '\n', '', 1)
        after = after.replace(']\\(', '](')   # lfc2: 링크 오인 텍스트 `[x](말)` → `[x]\\(말)` 이스케이프는 정당한 차이
        a, b = norm(before), norm(after)
        if a != b:
            i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
            probs.append(f'{f}: 토큰 차이 @{i} before={a[i:i+6]} after={b[i:i+6]} (len {len(a)}→{len(b)})')
        if f in ('1-question.md', '3-answer.md'):
            nb, cb, _ = struct(before)
            na, ca, cn = struct(after)
            if f == '3-answer.md':   # 답 쪽 번호는 헤딩만 센다(본문 번호 목록 제외)
                hb = [int(x) for x in re.findall(r'^#### (\d+)\. ', re.sub(r'(?ms)^```.*?^```', '', before), flags=re.M)]
                ha = [int(x) for x in re.findall(r'^### (\d+)\. (?!\(C)', re.sub(r'(?ms)^```.*?^```', '', after), flags=re.M)]
                nb, na = hb, ha
            if nb != na:
                probs.append(f'{f}: 원래 번호 변화 {nb} → {na}')
            if cb != ca:
                probs.append(f'{f}: C 꼬리표 변화 {cb} → {ca}')
            cnums[f] = cn
    if cnums.get('1-question.md') != cnums.get('3-answer.md'):
        probs.append(f'C 번호 부여 불일치 {cnums}')
    return probs


if __name__ == '__main__':
    bad = 0
    for d in sys.argv[1:]:
        p = check(d)
        print(('DIFF ' if p else 'OK   ') + d)
        for x in p:
            print('    ', x)
        bad += bool(p)
    print(f'== {len(sys.argv) - 1 - bad} OK / {bad} DIFF')
    sys.exit(1 if bad else 0)
