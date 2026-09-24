#!/usr/bin/env python3
r"""캡처 재대조에서 **흔들리는 칸**을 정규화해 「고칠 것」만 남긴다.

왜 필요한가 — 제출 전 재대조(`capture.sh` 재실행 → `diff -rq`)는 두 종류의 차이를 함께 뱉는다.

  · **설계상 불일치** — 주소·PID·시간처럼 **다시 돌리면 당연히 달라지는 칸**
  · **고칠 것** — 옮겨 적기 사고, 잘못된 값, 누락·덧붙임

섞여 나오면 사람이 한 줄씩 봐야 한다. 이 스크립트가 앞쪽을 지워 **뒤쪽만 남긴다.**
★ 실측 — 한 배치에서 원문 `diff` 가 8파일에서 갈렸는데, 정규화하니 **12파일 전부 불일치 0** 이었다.
배치마다 같은 규칙을 다시 만들고 있어서 도구로 올린다.

쓰는 법 — 두 캡처 디렉토리를 견준다.

    normalize-shaky.py <블록디렉토리A> <블록디렉토리B>
    normalize-shaky.py --show <파일>        # 한 파일이 어떻게 정규화되는지 보기

★★ **정규화는 「무엇이 흔들려도 되는가」의 선언이다.** 규칙을 늘리면 그만큼 눈을 감는 것이므로,
   **머리말의 「흔들리는 칸」 표와 같은 목록**이어야 한다. 표에 없는 것을 여기서 지우지 마라.
★ 기본 규칙 넷은 갈래를 가리지 않고 나왔던 것들이다. 갈래 고유의 칸은 `--rule` 로 더한다.
"""
import argparse
import pathlib
import re
import sys

# 갈래를 가리지 않고 반복해서 나온 「흔들리는 칸」 넷.
RULES = [
    # 주소 — ASLR·힙 주소·`%p`·스택 주소. 5자리 이상 16진수만 잡아 상수와 구분한다.
    (re.compile(r'0x[0-9a-fA-F]{5,}'), '0x<addr>'),
    # sanitizer 리포트의 PID — `==1021616==`
    (re.compile(r'==\d+=='), '==<pid>=='),
    # 패닉·스레드 id — rustc 1.92 의 `thread 'main' (3084354) panicked`
    (re.compile(r"(thread '[^']*') \(\d+\)"), r'\1 (<tid>)'),
    # 경과 시간 — `12.3ms` · `1.234s` · `1234 ns/op`
    (re.compile(r'\b\d+(?:\.\d+)?\s*(ms|µs|us|ns|s)\b'), '<time>\\1'),
]


def normalize(text: str, extra=()) -> str:
    for pat, rep in list(RULES) + list(extra):
        text = pat.sub(rep, text)
    return text


def main() -> None:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--show', action='store_true')
    ap.add_argument('--rule', action='append', default=[],
                    help='정규식=대체 를 규칙으로 더한다 (갈래 고유의 흔들리는 칸)')
    ap.add_argument('-h', '--help', action='store_true')
    a = ap.parse_args()
    if a.help or not a.paths:
        sys.exit(__doc__.strip())

    extra = []
    for r in a.rule:
        if '=' not in r:
            sys.exit('--rule 은 정규식=대체 꼴이라야 한다: %s' % r)
        pat, _, rep = r.partition('=')
        extra.append((re.compile(pat), rep))

    if a.show:
        for p in a.paths:
            sys.stdout.write(normalize(pathlib.Path(p).read_text(encoding='utf-8'), extra))
        return

    if len(a.paths) != 2:
        sys.exit('디렉토리 둘을 주거나 --show 로 한 파일을 봐라.')
    A, B = (pathlib.Path(x) for x in a.paths)
    names = sorted({p.name for p in A.iterdir() if p.is_file()} |
                   {p.name for p in B.iterdir() if p.is_file()})
    same = soft = diff = missing = 0
    for n in names:
        fa, fb = A / n, B / n
        if not (fa.exists() and fb.exists()):
            missing += 1
            print('  ★한쪽에만 있다  %s' % n)
            continue
        ra = fa.read_text(encoding='utf-8', errors='replace')
        rb = fb.read_text(encoding='utf-8', errors='replace')
        if ra == rb:
            same += 1
        elif normalize(ra, extra) == normalize(rb, extra):
            soft += 1
            print('  흔들린 칸      %s' % n)
        else:
            diff += 1
            print('  ★고칠 것       %s' % n)
    print('[재대조] 블록 %d개 · 동일 %d · 흔들린 칸 %d · ★고칠 것 %d · 한쪽에만 %d'
          % (len(names), same, soft, diff, missing))
    sys.exit(1 if (diff or missing) else 0)


if __name__ == '__main__':
    main()
