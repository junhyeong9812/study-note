#!/usr/bin/env python3
r"""원고의 `@@이름@@` 줄을 캡처 파일 내용으로 치환해 최종 `.md` 를 만든다.

왜 필요한가 — **사람이 출력을 복사하는 한 옮겨 적기 사고는 재발한다.**
실측에서 이 유형이 지배적이었다:

  · `javap` 덤프의 **두 줄이 통째로 빠지고 오프셋 숫자가 14→10 으로 고쳐** 적힘
    (폭 검사로는 안 잡히고 재실행 diff 로만 잡혔다)
  · 진단 블록의 **꼬리 줄 누락 3건 · 없는 줄 덧붙임 2건** — 빈도가 같았다
  · `size_of` 두 줄을 **뒤바꿔** 옮김 · `char` 크기를 윗줄 값에 끌려 **9** 로 적음
  · 문서 어디에도 없는 출력(`E end`)을 표의 근거 칸에 **유령 인용**

쓰는 법 — 네 단계다.

  1. `capture.sh` 가 문서에 실을 블록을 **전부 파일로** 받는다.
     한 파일 = 소스 배너 + 명령 배너 + 출력 + `(exit N)` 까지 한 덩어리.
  2. 원고에는 `@@블록이름@@` **한 줄만** 쓴다.
  3. 이 스크립트가 그 줄을 파일 내용으로 치환해 최종 `.md` 를 만든다.
  4. 제출 전 **캡처를 처음부터 다시 돌려 `diff -rq`** 한다.
     달라진 파일이 곧 「흔들리는 칸」이고, 그 밖의 차이는 전부 「고칠 것」이다.

실측 — 한 배치에서 82블록 중 **81블록의 동일성을 기계로 증명**했고,
남은 1블록(`by lazy` 멀티스레드 관찰)은 문서에 성질로 선언해 둔 것과 정확히 일치했다.
「배포본 == 조립본」 대조도 같은 스크립트로 언제든 다시 된다.

★ 블록 이름은 `[\w.-]+` 만 쓴다. 줄 전체가 `@@이름@@` 일 때만 치환하므로
  본문 중간의 `@@` 는 건드리지 않는다.

사용:
    assemble-blocks.py <원고.md.in> <결과.md> [--blocks <디렉토리>]
    (또는 환경변수 BLOCKS 로 디렉토리 지정. 기본값은 원고 옆의 `blocks/`)
"""
import os
import pathlib
import re
import sys

PAT = re.compile(r'@@([\w.-]+)@@')


def assemble(src: pathlib.Path, dst: pathlib.Path, blocks: pathlib.Path) -> list:
    out, used = [], []
    for n, line in enumerate(src.read_text(encoding='utf-8').split('\n'), 1):
        m = PAT.fullmatch(line)
        if not m:
            # ★ 왼쪽 끝에 붙은 줄만 치환한다. 들여쓴 `@@이름@@` 을 치환하면
            #   블록이 왼쪽 끝에 붙어 리스트·인용 구조가 깨진다(치환 안 하고 알린다).
            if PAT.search(line):
                print('  ※ 줄 왼쪽 끝이 아니라 치환하지 않았다 %s:%d: %s'
                      % (src.name, n, line.strip()[:60]), file=sys.stderr)
            out.append(line)
            continue
        f = blocks / (m.group(1) + '.txt')
        if not f.exists():
            sys.exit('블록 없음: %s  (%s:%d)' % (f, src.name, n))
        body = f.read_text(encoding='utf-8')
        if body.endswith('\n'):
            body = body[:-1]
        # ★ 캡처가 이미 펜스째 뱉은 블록을 원고가 한 번 더 감싸면 이중 펜스가 된다.
        #   렌더 검사도 소스 펜스 검사도 못 잡았고 덤프를 세다가 발견됐다(실측) — 조립 때 막는다.
        if out and out[-1].startswith('```') and body.startswith('```'):
            print('  ★ 이중 펜스 — 원고의 여는 펜스 바로 아래에 펜스째 캡처된 블록이 들어갔다 %s:%d: %s'
                  % (src.name, n, m.group(1)), file=sys.stderr)
        out.append(body)
        used.append(m.group(1))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text('\n'.join(out), encoding='utf-8')
    return used


def main() -> None:
    argv = [a for a in sys.argv[1:]]
    blocks_arg = None
    if '--blocks' in argv:
        i = argv.index('--blocks')
        blocks_arg = argv[i + 1]
        del argv[i:i + 2]
    if len(argv) != 2:
        sys.exit(__doc__.strip().split('사용:')[-1].strip())
    src, dst = pathlib.Path(argv[0]), pathlib.Path(argv[1])
    blocks = pathlib.Path(blocks_arg or os.environ.get('BLOCKS')
                          or src.resolve().parent / 'blocks')
    used = assemble(src, dst, blocks)
    print('%s <- 블록 %d개: %s' % (dst, len(used), ' '.join(used)))


if __name__ == '__main__':
    main()
