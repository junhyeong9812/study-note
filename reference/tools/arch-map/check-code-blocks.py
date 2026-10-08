#!/usr/bin/env python3
r"""아키텍처 지도 문서의 코드 블록이 **고정한 태그의 소스와 한 글자도 같은지** 검사한다.

왜 필요한가 — 지도 문서(`opensource/<도구>/architecture/`)는 함수마다 실제 코드를 인용한다.
워커가 기억으로 코드를 옮기거나 줄 범위를 착각하면 문서는 그럴듯한데 소스와 다르다.
MySQL 지도(코드 블록 598개)를 쓸 때 이 검사가 작성 직후·검증 직후·병합 전마다 돌았고,
동명 파일(plugin/x 아래의 같은 헤더)을 잘못 고른 블록을 잡았다.

계약 — 코드 펜스(cpp·c·h·java·sql)의 **첫 줄이 `// <파일> L<시작>-L<끝>`**(sql 은 `--`)이면 그 범위와 대조한다.

    ```cpp
    // connection_handler_per_thread.cc L246-L250
    static void *handle_connection(void *arg) {
      ...
      // ... (L260-L270 생략: 이유)
    ```

- 블록의 각 줄(생략 표시 `// ...` 제외)이 소스 범위 안에 **순서대로** 있어야 통과한다.
- `<파일>` 은 파일명 또는 `dir/file` 꼴. 레포에서 유일하지 않으면 같은 문서의
  GitHub blob 링크(`github.com/<org>/<repo>/blob/<sha>/<경로>`)에 있는 경로로 고른다.
- 첫 줄이 이 꼴이 아닌 소스 펜스는 NOHEADER 로 센다 — 손으로 적혀 검증되지 않은 코드다.

★ 소스 레포는 문서가 고정한 태그로 체크아웃되어 있어야 한다(로컬 클론의 HEAD 를 그대로 읽는다).

사용:
    check-code-blocks.py <소스 레포 루트> <파일.md 또는 디렉터리> [...]
    끝에 `blocks=N bad=M` 을 찍고, bad 가 있으면 exit 1.
"""
import glob
import os
import re
import subprocess
import sys

FENCE = re.compile(r"^```(cpp|c|h|java|sql)\s*$")
HEADER = re.compile(r"^(?://|--)\s*(\S+)\s+L(\d+)(?:-L?(\d+))?")
LINKED = re.compile(r"github\.com/[^/\s]+/[^/\s]+/blob/[0-9a-f]+/([^#)\s]+)")
ELIDED = re.compile(r"^\s*(?://|--)\s*\.\.\.")


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    root, targets = argv[1], argv[2:]
    files = subprocess.run(["git", "-C", root, "ls-files"],
                           capture_output=True, text=True, check=True).stdout.split("\n")

    def resolve(name):
        return [f for f in files if f == name or f.endswith("/" + name)]

    mds = []
    for t in targets:
        mds += glob.glob(t + "/**/*.md", recursive=True) if os.path.isdir(t) else [t]

    total = bad = 0
    for md in sorted(mds):
        raw = open(md, encoding="utf-8").read()
        lines = raw.split("\n")
        linked = set(LINKED.findall(raw))
        i = 0
        while i < len(lines):
            if not FENCE.match(lines[i]):
                i += 1
                continue
            j = i + 1
            block = []
            while j < len(lines) and not lines[j].startswith("```"):
                block.append(lines[j])
                j += 1
            i = j + 1
            if not block:
                continue
            total += 1
            h = HEADER.match(block[0])
            if not h:
                print(f"NOHEADER {md}: {block[0][:60]}")
                bad += 1
                continue
            name, x = h.group(1), int(h.group(2))
            y = int(h.group(3) or h.group(2))
            cands = resolve(name)
            if len(cands) > 1:
                cands = [f for f in cands if f in linked] or cands
            if len(cands) != 1:
                print(f"AMBIG/MISSING {md}: {name} -> {cands[:3]}")
                bad += 1
                continue
            src = open(os.path.join(root, cands[0]), encoding="utf-8",
                       errors="replace").read().split("\n")[x - 1:y]
            k = 0
            for line in block[1:]:
                if ELIDED.match(line) or line.strip() == "...":
                    continue
                while k < len(src) and src[k].rstrip() != line.rstrip():
                    k += 1
                if k >= len(src):
                    print(f"MISMATCH {md}: {name} L{x}-{y}: {line.strip()[:70]!r}")
                    bad += 1
                    break
                k += 1
    print(f"blocks={total} bad={bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
