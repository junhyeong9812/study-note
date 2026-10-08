#!/usr/bin/env python3
"""옛 형식(과제 이식) 노트 → check_new 형식 전환. 인자: 노트 폴더(여러 개). 내용은 건드리지 않고 표기만 바꾼다.
규칙(명세 §1):
  1-question: `#### N. 제목` → `N. 제목`, `- Ck. …` → `M. (Ck) …`(M = 마지막 번호 다음부터). `### A./B./C.` 유지.
  3-answer  : `#### N. …` → `### N. …`, `- Ck. 질문\\` + 들여쓴 답 → `### M. (Ck) 질문` + 답(2칸 내어쓰기),
              그룹 소제목 `### A./B./C. …` → `**A. …**`.
  2-summary : `## 쓰이는 곳` → `## 쓰이는 자료구조·알고리즘`.
  metadata  : 표 끝에 `| 형식 | 과제 이식 |`.
"""
import os, re, sys

FENCE = re.compile(r'^\s*(```|~~~)')
GROUP = re.compile(r'^### ([A-Z])\. (.*)$')
CQ = re.compile(r'^- C(\d+)\. (.*)$')
META_ROW = '| 형식 | 과제 이식 |'


def walk(lines):
    """(line, in_fence) — 펜스 줄 자체는 in_fence=True로 돌려 변환 대상에서 뺀다."""
    inside = False
    for l in lines:
        if FENCE.match(l):
            inside = not inside
            yield l, True
            continue
        yield l, inside


def q_numbers(lines):
    nums = []
    for l, f in walk(lines):
        if f:
            continue
        if l.startswith('## 복습 기록'):
            break
        m = re.match(r'^#### (\d+)\. ', l) or re.match(r'^(\d+)\. ', l)
        if m:
            nums.append(int(m.group(1)))
    return nums


def conv_question(text):
    L = text.split('\n')
    nums = q_numbers(L)
    nxt = max(nums) + 1
    out, done = [], False
    for l, f in walk(L):
        if not f and not done:
            if l.startswith('## 복습 기록'):
                done = True
            m = re.match(r'^#### (\d+\. .*)$', l)
            if m:
                l = m.group(1)
            m = CQ.match(l)
            if m:
                l = f'{nxt}. (C{m.group(1)}) {m.group(2)}'
                nxt += 1
        out.append(l)
    return '\n'.join(out), nums


def conv_answer(text, qmax):
    L = text.split('\n')
    nxt = qmax + 1
    out, in_c = [], False
    for l, f in walk(L):
        if f:
            if in_c and l.startswith('  '):
                l = l[2:]
            out.append(l)
            continue
        if re.match(r'^#{1,6} ', l):
            in_c = False
        m = CQ.match(l)
        if m:
            q = m.group(2)
            if q.endswith('\\'):
                q = q[:-1].rstrip()
            out.append(f'### {nxt}. (C{m.group(1)}) {q}')
            nxt += 1
            in_c = True
            continue
        m = GROUP.match(l)
        if m:
            out.append(f'**{m.group(1)}. {m.group(2)}**')
            continue
        m = re.match(r'^#### (\d+\. .*)$', l)
        if m:
            out.append('### ' + m.group(1))
            continue
        if in_c and l.startswith('  '):
            l = l[2:]
        out.append(l)
    return '\n'.join(out)


def conv_summary(text):
    return re.sub(r'^## 쓰이는 곳[ \t]*$', '## 쓰이는 자료구조·알고리즘', text, flags=re.M)


def conv_meta(text):
    if META_ROW in text:
        return text
    L = text.split('\n')
    last = max(i for i, l in enumerate(L) if l.startswith('|'))
    L.insert(last + 1, META_ROW)
    return '\n'.join(L)


def rw(p, fn):
    t = open(p, encoding='utf-8').read()
    n = fn(t)
    if n != t:
        open(p, 'w', encoding='utf-8').write(n)


def main(folder):
    folder = folder.rstrip('/')
    qp = os.path.join(folder, '1-question.md')
    nums = []

    def fq(t):
        n, ns = conv_question(t)
        nums.extend(ns)
        return n
    rw(qp, fq)
    rw(os.path.join(folder, '3-answer.md'), lambda t: conv_answer(t, max(nums)))
    rw(os.path.join(folder, '2-summary.md'), conv_summary)
    rw(os.path.join(folder, 'metadata.md'), conv_meta)
    print('converted', folder)


if __name__ == '__main__':
    for d in sys.argv[1:]:
        main(d)
