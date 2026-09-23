#!/usr/bin/env python3
"""컴파일러 진단을 싣는 문서가 **재검증 가능한지** 검사하고, 진단 줄을 뽑아 준다.

왜 필요한가
-----------
Rust·C·Kotlin 처럼 **에러 메시지가 교재**인 갈래에서는 진단 전문을 문서에 싣는다.
그런데 「돌려 봤다」와 「옮겨 적은 게 맞다」는 다른 검사다 — 실측에서 이 유형의 사고가 계속 나왔다:

  Rust  8건 — 소스를 줄인 발췌라 에러의 줄 번호가 안 맞음 · `= note:` 아닌 줄을 `= note:` 로 적음 ·
              `true` 를 `false` 로
  Kotlin 4건 — `javap` 출력의 패딩 공백을 폭 맞추려고 손댔다가 93줄이 어긋남 ·
              문서가 보여 준 `grep` 명령의 결과가 실제와 다름
  C      — 무한 루프 `exit 124` 까지 다시 받아 대조

★ 이 도구가 하는 일은 둘이다.
  ① **진단 줄을 뽑아 준다** — 그 줄들을 새 컴파일 출력에 넣어 포함 검사하면 옮겨 적기 사고가 걸린다.
  ② ★★ **재검증이 불가능한 문서를 찍어 준다** — 진단은 실었는데 **그 진단을 낸 소스가 문서에 없으면**
     사람도 기계도 다시 던질 수 없다. 실측에서 잡힌 4건이 전부 「소스를 줄인 블록」이었다.

★★ 이 도구는 **판정하지 않는다.** 컴파일은 사람이 한다 — 어느 파일을 어느 플래그로 돌릴지
   도구가 알 수 없기 때문이다. 판정을 자동화한 척하지 않는다.

쓰는 법
-------
    python3 check-diagnostics.py <문서.md ...>            # 진단 줄 + 재검증 가능 여부
    python3 check-diagnostics.py --lines <문서.md ...>    # 진단 줄만 (새 출력에 포함 검사할 때)

권장 형식 — 진단을 싣는 블록에는 **그 진단을 낸 소스를 같은 자리에** 둔다.

    ```text
    ===== 소스: ex.rs =====
    fn main() { let x: i32 = "a"; }
    ===== rustc --edition 2021 ex.rs =====
    error[E0308]: mismatched types
     --> ex.rs:1:26
    ```
"""
import re, sys, pathlib

# 진단으로 읽히는 줄. 언어마다 모양이 달라 넉넉히 잡고, 걸러내는 것은 사람이 한다.
DIAG = re.compile(
    r'^\s*('
    r'error(\[[A-Z]\d+\])?:'          # rustc · kotlinc
    r'|warning:'
    r'|note:|= note:|help:|= help:'
    r'|thread .* panicked'
    r'|\w+\.(rs|c|kt|h):\d+:\d+:'     # gcc · kotlinc 위치
    r'|-->'                            # rustc 위치
    r'|[A-Za-z_]+Error:'               # python
    r'|runtime error:'                 # sanitizer
    r'|AddressSanitizer'
    r')')

# 「이 진단을 낸 소스가 문서에 있나」를 세 단계로 본다.
#   full    — 전체 소스가 실려 있다. 그대로 다시 컴파일할 수 있다.
#   partial — 진단이 스스로 끼워 보여 주는 발췌만 있다(`3 | let s2 = s1;`).
#             메시지 글자는 대조되지만 **줄 번호는 못 맞춘다** — 실측 사고 4건이 전부 이 모양이었다.
#   none    — 진단만 덩그러니 있다. 사람도 기계도 다시 못 던진다.
SOURCE_MARK = re.compile(r'^\s*(=====\s*소스|```(rust|c|kotlin|kt|python|java)\b|// ex\.|/\* ex\.)')
ECHO = re.compile(r'^\s*\d+\s*\|')      # rustc·gcc 가 끼워 보여 주는 소스 줄
FENCE = re.compile(r'^\s*```')


def scan(path):
    lines = pathlib.Path(path).read_text(encoding='utf-8').split('\n')
    blocks, i = [], 0
    while i < len(lines):
        if not FENCE.match(lines[i]):
            i += 1
            continue
        start = i; i += 1; body = []
        while i < len(lines) and not FENCE.match(lines[i]):
            body.append(lines[i]); i += 1
        i += 1
        diags = [l for l in body if DIAG.match(l)]
        if diags:
            blocks.append(dict(line=start + 1, diags=diags, body=body))
    return blocks


def grade(lines, block):
    """이 진단 블록을 다시 던질 수 있나 — full / partial / none."""
    body = block['body']
    if any(SOURCE_MARK.match(l) for l in body):
        return 'full'
    lo = max(0, block['line'] - 41)
    if any(SOURCE_MARK.match(l) for l in lines[lo:block['line'] - 1]):
        return 'full'
    if any(ECHO.match(l) for l in body):
        return 'partial'
    return 'none'


if __name__ == '__main__':
    only_lines = '--lines' in sys.argv
    files = [a for a in sys.argv[1:] if a != '--lines']
    total_diag = 0
    grades = {'full': 0, 'partial': 0, 'none': 0}
    nones = []
    for f in files:
        lines = pathlib.Path(f).read_text(encoding='utf-8').split('\n')
        for b in scan(f):
            total_diag += len(b['diags'])
            if only_lines:
                for d in b['diags']:
                    print(d.strip())
                continue
            g = grade(lines, b)
            grades[g] += 1
            if g == 'none':
                nones.append((f, b['line'], b['diags'][0].strip()[:70]))
    if only_lines:
        sys.exit(0)
    print('진단 줄 %d개 · 블록 %d개' % (total_diag, sum(grades.values())))
    print('  다시 던질 수 있다(소스 있음)        %d' % grades['full'])
    print('  메시지만 대조 가능(발췌만 실렸다)   %d  ← 줄 번호는 못 맞춘다' % grades['partial'])
    print('  ★ 다시 못 던진다(소스 없음)         %d' % grades['none'])
    for f, ln, d in nones[:15]:
        print('     %s:%d  %s' % (f, ln, d))
    # 조언이지 합격/불합격이 아니다 — 무엇을 컴파일할지는 도구가 모른다.
    sys.exit(0)
