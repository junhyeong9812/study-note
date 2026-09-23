#!/usr/bin/env python3
r"""문서에 실린 소스 코드 펜스가 **실제로 돌린 파일과 한 글자도 같은지** 검사한다.

왜 필요한가 — 출력은 캡처해서 붙이면서도 **소스는 손으로 옮겨 적는** 일이 흔하다.
그러면 「이 소스를 돌렸더니 이 출력이 나왔다」의 앞쪽 절반이 검증되지 않는다.
실측에서 이 검사가 **손으로 붙인 소스의 닫는 중괄호 하나가 빠진 것**을 잡았다 —
출력은 맞고 소스만 틀린 자리라 다른 검사는 전부 통과했다.

계약 — 펜스의 **첫 줄이 파일명 주석**이면 그 파일과 대조한다.

    ```kotlin          ```c            ```python        ```rust
    // Ex.kt           /* ex.c */      # ex.py          // ex.rs
    …                  …               …                …
    ```                ```             ```              ```

첫 줄이 배너가 아닌 펜스는 **건너뛰고 개수를 보고**한다(발췌·의사코드가 있으므로).
건너뛴 수가 많으면 그만큼 「소스가 맞다」가 검증 안 된 것이다.

★ 「돌려 봤다」와 「옮겨 적은 게 맞다」는 다른 검사다 — 이 스크립트는 뒤쪽만 본다.

사용:
    check-source-fences.py --root <소스디렉토리> <파일.md> [파일.md ...]
    (--root 아래를 재귀로 뒤져 파일명이 같은 것을 찾는다. 같은 이름이 둘이면 알린다.)
"""
import pathlib
import re
import sys
import difflib

# 언어별 한 줄 주석 꼴 — `// a.kt` · `# a.py` · `/* a.c */` · `-- a.sql`
BANNER = re.compile(r'^\s*(?://|\#|--)\s*([\w.\-]+\.\w+)\s*$'
                    r'|^\s*/\*\s*([\w.\-]+\.\w+)\s*\*/\s*$')
FENCE = re.compile(r'^```([A-Za-z0-9_+-]*)\n(.*?)\n```$', re.S | re.M)


def index_sources(root: pathlib.Path) -> dict:
    idx = {}
    dupes = set()
    for p in root.rglob('*'):
        if p.is_file():
            if p.name in idx:
                dupes.add(p.name)
            idx.setdefault(p.name, p)
    for d in sorted(dupes):
        print('  ※ 같은 이름의 파일이 둘 이상이다 — 첫 번째를 쓴다: %s' % d,
              file=sys.stderr)
    return idx


def main() -> None:
    argv = sys.argv[1:]
    if '--root' not in argv:
        sys.exit(__doc__.strip().split('사용:')[-1].strip())
    i = argv.index('--root')
    root = pathlib.Path(argv[i + 1])
    del argv[i:i + 2]
    if not argv:
        sys.exit(__doc__.strip().split('사용:')[-1].strip())
    idx = index_sources(root)

    checked = missing = bad = skipped = 0
    for md in argv:
        p = pathlib.Path(md)
        text = p.read_text(encoding='utf-8')
        for m in FENCE.finditer(text):
            body = m.group(2)
            first = body.split('\n', 1)[0]
            bm = BANNER.match(first)
            if not bm:
                skipped += 1
                continue
            name = bm.group(1) or bm.group(2)
            f = idx.get(name)
            if f is None:
                missing += 1
                print('  파일 없음 %-20s  <- %s' % (name, md))
                continue
            real = f.read_text(encoding='utf-8').rstrip('\n')
            doc = body.split('\n', 1)[1].rstrip('\n') if '\n' in body else ''
            checked += 1
            if real != doc:
                bad += 1
                print('불일치: %s  <- %s' % (md, f))
                diff = difflib.unified_diff(real.split('\n'), doc.split('\n'),
                                            '실파일', '문서', lineterm='')
                for line in list(diff)[:20]:
                    print('   ' + line)

    print('[소스 펜스] 대조 %d개 · 불일치 %d건 · 파일 못 찾음 %d건 · 배너 없어 건너뜀 %d개'
          % (checked, bad, missing, skipped))
    sys.exit(1 if (bad or missing) else 0)


if __name__ == '__main__':
    main()
