#!/usr/bin/env python3
"""문법·API 주제 문서에서 실행 블록을 뽑는다 — 「옮겨 적은 게 맞는가」를 검사하기 위한 도구.

왜 필요한가
-----------
「모든 출력을 실제로 재현했는가」 체크리스트로는 **안 걸리는** 사고가 있다:
출력을 실제로 받아 놓고 **문서로 옮겨 적는 과정에서** 틀리는 것.
SQL 60주제 작업에서 이 유형이 4건 나왔고, 넷 다 **손으로 좌우 배치(side-by-side)로
재배열한 블록 또는 그 인접 블록**에서 났다. 값이 그럴듯해서 눈으로는 안 잡힌다.

쓰는 법
-------
    python3 extract-exec-blocks.py <파일...>        # 블록을 뽑아 출력
    (뽑은 질의를 두 엔진에 다시 던지고 토큰 다중집합으로 문서와 대조한다)

설계 판단 — 질의를 자동 실행하지 않는다
--------------------------------------
문서는 질의를 `...` 나 `<연결>` 로 줄여 놓은 곳이 많아 어떤 파서도 복원할 수 없다.
그래서 이 파서는 **「블록 + 줄번호 + 엔진 + 좌우배치 여부」만** 내고 질의 복원은 사람이 한다.
대신 **커버리지 검사**(아래 `missed`)로 누락만 기계가 막는다 — 파서를 믿지 않기 위한 장치다.

실행 쪽 함정
-----------
- `docker exec` 에 heredoc 을 쓰려면 **`-i`** 가 필요하다. 없으면 stdin 이 안 붙어 조용히 아무것도 안 돈다.
- MySQL 은 **`--table`** 을 줘야 문서와 같은 `+---+` 표가 나온다. 안 주면 탭 구분이라 대조가 안 된다.
- 여러 질의를 한 번에 보낼 때 구분자는 PG `\\echo ==마크`, MySQL `SELECT '==마크' AS mark;`
  (MySQL 에는 `\\echo` 가 없다).
- 세션 설정에 기대는 실험(`SET statement_timeout`, `SET SESSION cte_max_recursion_depth`)은
  `docker exec` 이 매번 새 세션이므로 **한 호출에 `SET …; <질의>` 로 묶어야** 효력이 있다.

어긋남으로 세지 않는 것
----------------------
- psql 의 `LINE n: ...` 말줄임(터미널 폭에 따라 달라진다)
- MySQL 에러의 `at line N`(질의를 몇 줄로 보냈는지에 달렸다)
- 한글 칸 패딩(문서는 표시 폭 2칸, mysql 클라이언트는 바이트 기준)
- 문서가 「테두리를 지웠다」·「칸을 생략했다」고 명시한 축약
- 실행 계획의 `cost=`·`rows=` 추정치 — 연산자 이름·트리 모양·`Index Cond`/`Filter` 가 같으면 통과
"""
import re, sys, pathlib

FENCE  = re.compile(r'^\s*```')
SQLHDR = re.compile(r'^\s*#{2,3} SQL:')
BANNER = re.compile(r'-{2,3}\s*(PG 18\.6|MySQL 8\.4\.10)\b[^-]*-{2,3}')
QUOTE  = re.compile(r'^\s*>\s?')     # 인용 블록 안에 든 코드펜스도 실행 블록이다


def _strip_quote(line):
    """`> ` 인용 표지를 벗긴다. 전수 검사에서 이 한 줄이 빠져 블록 하나를 통째로 놓쳤었다."""
    return QUOTE.sub('', line, count=1)


def blocks(path):
    lines = [_strip_quote(l)
             for l in pathlib.Path(path).read_text(encoding='utf-8').splitlines()]
    out, i = [], 0
    while i < len(lines):
        if FENCE.match(lines[i]):
            start = i; i += 1; body = []
            while i < len(lines) and not FENCE.match(lines[i]):
                body.append(lines[i]); i += 1
            if any(SQLHDR.match(b) or BANNER.search(b) for b in body):
                engines, sbs = set(), False
                for b in body:
                    hits = BANNER.findall(b)
                    engines.update(hits)
                    if len(hits) > 1:        # 한 줄에 배너 둘 = 좌우 배치 = 사고가 잦은 자리
                        sbs = True
                out.append(dict(file=str(path), start=start + 1, end=i + 1,
                                engines=sorted(engines), side_by_side=sbs,
                                body="\n".join(body)))
        i += 1
    return out


# 배너도 `### SQL:` 도 없지만 실행 결과가 분명한 펜스를 찾기 위한 흔적들.
# ★ 이 목록이 없으면 도구가 조용히 거짓말을 한다 — 실측: 배너를 안 쓰는 편(52-upsert)에서
#   펜스 49개 중 5개만 잡히는데 `missed()` 는 "놓친 것 0" 을 돌려줬다.
TRACE = re.compile(
    r'^\s*(?:\+-{2,}|\(\d+ rows?\)|ERROR[ :]|ERROR \d{4}|INSERT 0 \d|UPDATE \d|DELETE \d|'
    r'MERGE \d|BEGIN;|START TRANSACTION;|ROLLBACK;|COMMIT;|NOTICE:|WARNING:|DETAIL:|HINT:|'
    r'Query OK,|\d+ rows? in set|-> )')


def _fences(path):
    """파일의 모든 코드펜스 구간을 (시작, 끝) 로 돌려준다."""
    lines = [_strip_quote(l)
             for l in pathlib.Path(path).read_text(encoding='utf-8').splitlines()]
    out, i = [], 0
    while i < len(lines):
        if FENCE.match(lines[i]):
            start = i; i += 1
            while i < len(lines) and not FENCE.match(lines[i]):
                i += 1
            out.append((start + 1, i + 1, lines[start + 1:i]))
        i += 1
    return out


def missed(path):
    """파서가 못 본 **실행 블록**.

    두 종류를 나눠 돌려준다.
    - `banner` : 엔진 배너가 있는데 안 잡힌 줄 — **파서 버그다. 반드시 빈 목록이어야 한다.**
    - `trace`  : 배너도 `### SQL:` 도 없지만 실행 흔적이 있는 펜스 — **파서를 고칠 일이 아니라
                 사람이 확인해야 할 목록이다.** 예시 데이터·개념 도식도 여기 섞여 들어오므로
                 「잡아라」가 아니라 「확인했다고 표시하라」로 읽는다.
    """
    covered = set()
    for b in blocks(path):
        covered.update(range(b['start'], b['end'] + 1))
    lines = pathlib.Path(path).read_text(encoding='utf-8').split("\n")
    banner = [(i + 1, l) for i, l in enumerate(lines)
              if BANNER.search(l) and (i + 1) not in covered]
    trace = [(s, e) for s, e, body in _fences(path)
             if s not in covered and any(TRACE.match(b) for b in body)]
    return banner, trace


if __name__ == '__main__':
    allb, bgaps, tgaps = [], [], []
    for p in sys.argv[1:]:
        allb += blocks(p)
        b, t = missed(p)
        bgaps += [(p,) + g for g in b]
        tgaps += [(p,) + g for g in t]
    for b in allb:
        print(f"===== {b['file']}:{b['start']}-{b['end']} "
              f"engines={b['engines']} sbs={b['side_by_side']}")
        print(b['body']); print()
    sys.stderr.write(f"파서가 잡은 실행 블록 {len(allb)}개 · 그중 좌우배치 "
                     f"{sum(1 for b in allb if b['side_by_side'])}개\n")
    if tgaps:
        sys.stderr.write(f"※ 배너 없이 실행 흔적만 있는 펜스 {len(tgaps)}개 "
                         f"— 파서 버그가 아니다. 사람이 확인할 목록이다\n")
        for g in tgaps:
            sys.stderr.write(f"   {g[0]}:{g[1]}-{g[2]}\n")
    if bgaps:
        sys.stderr.write(f"★ 파서가 놓친 배너 {len(bgaps)}건 — 파서를 고쳐라\n")
        for g in bgaps:
            sys.stderr.write(f"   {g[0]}:{g[1]}  {g[2]}\n")
        sys.exit(1)
