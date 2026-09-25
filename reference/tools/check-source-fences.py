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

★★ **대상은 「소스 언어로 태그된 펜스」뿐이다.** `text`·`console` 같은 출력 블록과 ASCII 그림은
애초에 대조할 실파일이 없으므로 **대상에서 뺀다** — 그것까지 「배너 없음」으로 세면
**「배너 없어 건너뜀 0」이 원리상 성립하지 않는 기준**이 된다(실측에서 펜스 421개 중 대조 대상은 178개뿐이었다).
읽을 수치는 **「배너 없는 소스 펜스」** — 그만큼이 손으로 적혀 검증이 안 된 코드다.

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
# 언어별 한 줄 주석 꼴 — `// a.kt` · `# a.py` · `/* a.c */` · `-- a.sql` · `<!-- a.html -->`
# ★ HTML·XML 주석 꼴을 빠뜨리면 그 갈래는 **「배너 없는 소스 펜스 0」이 원리상 성립하지 않는다**(실측).
BANNER = re.compile(r'^\s*(?://|\#|--)\s*([\w.\-]+\.\w+)\s*$'
                    r'|^\s*/\*\s*([\w.\-]+\.\w+)\s*\*/\s*$'
                    r'|^\s*<!--\s*([\w.\-]+\.\w+)\s*-->\s*$')
# 실파일과 대조할 수 있는 펜스의 언어 태그. 그 밖(text·console·없음)은 출력·그림이라 대상이 아니다.
SOURCE_LANGS = {
    'py', 'python', 'kt', 'kotlin', 'rs', 'rust', 'c', 'h', 'cpp', 'c++', 'cc',
    'go', 'ts', 'typescript', 'js', 'javascript', 'java', 'cs', 'csharp',
    'sql', 'sh', 'bash', 'html', 'css',
}
FENCE = re.compile(r'^```([A-Za-z0-9_+-]*)\n(.*?)\n```$', re.S | re.M)


def index_sources(root: pathlib.Path):
    """파일명 -> 경로. ★ 같은 이름이 둘 이상이면 **고르지 않는다.**

    조용히 첫 번째를 쓰면 블록 58개가 전부 `ex.rs` 인 갈래에서
    **하나의 파일과 58번 대조**해 대량 오탐이 난다(실측). 어느 것과 대조할지
    모르는 것은 「불일치」가 아니라 **「판정 불가」**이므로 그렇게 보고한다.
    """
    idx, dupes = {}, {}
    for p in root.rglob('*'):
        if p.is_file():
            if p.name in idx:
                dupes.setdefault(p.name, [idx[p.name]]).append(p)
            else:
                idx[p.name] = p
    for name in dupes:
        idx.pop(name, None)
    return idx, dupes


def main() -> None:
    argv = sys.argv[1:]
    if '--root' not in argv:
        sys.exit(__doc__.strip().split('사용:')[-1].strip())
    i = argv.index('--root')
    root = pathlib.Path(argv[i + 1])
    del argv[i:i + 2]
    if not argv:
        sys.exit(__doc__.strip().split('사용:')[-1].strip())
    idx, dupes = index_sources(root)

    checked = missing = bad = nobanner = nonsource = ambiguous = 0
    for md in argv:
        p = pathlib.Path(md)
        text = p.read_text(encoding='utf-8')
        for m in FENCE.finditer(text):
            lang = m.group(1).lower()
            if lang not in SOURCE_LANGS:
                nonsource += 1            # 출력 블록·그림 — 대조할 실파일이 없다
                continue
            body = m.group(2)
            first = body.split('\n', 1)[0]
            bm = BANNER.match(first)
            if not bm:
                nobanner += 1
                print('  배너 없는 소스 펜스 %-12s <- %s' % ('```' + lang, md))
                continue
            name = bm.group(1) or bm.group(2) or bm.group(3)
            if name in dupes:
                ambiguous += 1
                print('  ★판정 불가 — `%s` 라는 이름의 파일이 %d개다 (%s)  <- %s'
                      % (name, len(dupes[name]), md,
                         ', '.join(str(x) for x in dupes[name][:3])))
                continue
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

    print('[소스 펜스] 대조 %d개 · 불일치 %d건 · 파일 못 찾음 %d건 · ★판정 불가 %d건 · '
          '★배너 없는 소스 펜스 %d개 · 출력·그림 펜스 %d개(대상 아님)'
          % (checked, bad, missing, ambiguous, nobanner, nonsource))
    sys.exit(1 if (bad or missing or ambiguous) else 0)


if __name__ == '__main__':
    main()
