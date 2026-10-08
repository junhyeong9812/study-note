#!/usr/bin/env python3
"""보충 질문·답 1쌍 추가 — 인자: 노트 폴더, JSON 파일 [{"tag":"(경계)","q":"질문 본문","a":"답 마크다운"}, ...].
번호는 기존 질문 마지막 번호+1부터. 질문은 마지막 번호 질문 블록 뒤(## 복습 기록 앞), 답은 정답 ## 절 끝(다음 ## 앞)에 넣는다.
질문 줄: `N. *(Claude 보충 — 노트 본문 요약)* (태그) 본문` · 답: `### N. (태그)` + 주석 + 표식 + 본문."""
import json, re, sys
VM = '*(Claude 보충 — 노트 본문 요약)*'
MARK = '<!-- 보충: 노트 본문 요약·참조 (legacy-format-conversion-2) -->'
folder, items = sys.argv[1].rstrip('/'), json.load(open(sys.argv[2], encoding='utf-8'))
qp, ap = f'{folder}/1-question.md', f'{folder}/3-answer.md'
Q = open(qp, encoding='utf-8').read().split('\n')
end = next((i for i, l in enumerate(Q) if l.startswith('## 복습 기록')), len(Q))
nums = [int(re.match(r'^(\d+)\. ', l).group(1)) for l in Q[:end] if re.match(r'^(\d+)\. ', l)]
n0 = max(nums)
while end > 0 and not Q[end - 1].strip(): end -= 1
newq = [f'{n0 + k + 1}. {VM} {it["tag"]} {it["q"]}' for k, it in enumerate(items)]
qi = [i for i in range(end) if re.match(r'^\d+\. ', Q[i])]
blank = len(qi) > 1 and not Q[qi[1] - 1].strip()
add = []
for q in newq: add += ([''] if blank else []) + [q]
Q = Q[:end] + add + Q[end:]
open(qp, 'w', encoding='utf-8').write('\n'.join(Q))
A = open(ap, encoding='utf-8').read().split('\n')
start = next(i for i, l in enumerate(A) if re.match(r'^### \d+\. ', l))
stop = next((i for i in range(start, len(A)) if A[i].startswith('## ')), len(A))
while stop > 0 and not A[stop - 1].strip(): stop -= 1
blk = []
for k, it in enumerate(items):
    blk += ['', f'### {n0 + k + 1}. {it["tag"]}', '', MARK, VM, ''] + it['a'].strip('\n').split('\n')
A = A[:stop] + blk + ([''] if stop < len(A) else []) + A[stop:]
open(ap, 'w', encoding='utf-8').write('\n'.join(A))
print('added', [n0 + k + 1 for k in range(len(items))])
