# python/syntax/48-pathlib-and-file-io — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 1번은 **스무 행을 전부** 적고, 마지막 줄의 수까지 세어야 맞은 것이다.
> ★★ 이 주제는 **속도·처리량을 묻지 않는다** — 한 번도 재지 않았다.
>
> 실행 환경: `python3` **3.12.3** · Linux · 이 머신의 로캘 `LANG=ko_KR.UTF-8`(3번은 `python3.11` 3.11.15 도 함께 — `env -i` 로 행마다 환경 전체를 준다). 던지는 형태는 `python3 - <파일` 이고, **스크립트마다 빈 디렉토리에서** 던졌다.
> ★ 선행 — [06](../06-strings-bytes-unicode/1-question.md)(`encode`/`decode`) · [28](../28-context-managers-and-with/1-question.md)(`with`) · [26](../26-eafp-vs-lbyl/1-question.md)(경쟁 조건).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 모드 열 개 × 파일이 없을 때와 있을 때 (예측)

```python
# e48_modes.py
import os

MODES = ["r", "w", "a", "x", "r+", "w+", "a+", "x+", "rb", "ab"]
STATES = ["none", "abc"]
NAME = "t.txt"


def setup(state):
    if os.path.exists(NAME):
        os.remove(NAME)
    if state == "abc":
        with open(NAME, "wb") as f:
            f.write(b"abc")


def disk():
    if not os.path.exists(NAME):
        return "(no file)"
    with open(NAME, "rb") as f:
        return repr(f.read())


def cell_open(mode, state):
    setup(state)
    try:
        f = open(NAME, mode)
    except OSError as e:
        return type(e).__name__
    f.close()
    return "opened, disk " + disk()


def cell_read(mode, state):
    setup(state)
    try:
        f = open(NAME, mode)
    except OSError as e:
        return "-"
    try:
        return repr(f.read())
    except Exception as e:
        return type(e).__name__
    finally:
        f.close()


def cell_write(mode, state):
    setup(state)
    try:
        f = open(NAME, mode)
    except OSError as e:
        return "-"
    data = b"Z" if "b" in mode else "Z"
    try:
        f.write(data)
    except Exception as e:
        f.close()
        return type(e).__name__ + ", disk " + disk()
    f.close()
    return "disk " + disk()


COLS = [("open", cell_open), ("read()", cell_read), ("write Z", cell_write)]
FMT = "%-4s %-5s %-21s %-21s %s"
print(FMT % ("mode", "file", "open", "read()", "write Z"))
rows = {}
for m in MODES:
    for s in STATES:
        cells = [fn(m, s) for _, fn in COLS]
        rows[(m, s)] = cells
        assert len(cells) == len(COLS)
        print(FMT % tuple([m, s] + cells))

split = sum(rows[(m, "none")][i] != rows[(m, "abc")][i]
            for m in MODES for i in range(len(COLS)))
total = len(MODES) * len(COLS)
emptied = [m for m in MODES if rows[(m, "abc")][0] == "opened, disk b''"]
print("modes whose open() leaves an existing 'abc' file empty:", ", ".join(emptied))
print("cells where the two states give different results: %d / %d" % (split, total))
```

### 2. ★★ 덧붙이기 모드에서 앞으로 돌아가 쓰면 (예측)

```python
# e48_append_seek.py
with open("log.txt", "w", encoding="utf-8") as f:
    f.write("abc")

with open("log.txt", "a+", encoding="utf-8") as f:
    print("[1] tell() right after open :", f.tell())
    f.seek(0)
    print("[2] read() after seek(0)    :", repr(f.read()))
    f.seek(0)
    print("[3] tell() after seek(0)    :", f.tell())
    f.write("Z")
    print("[4] tell() after write      :", f.tell())

with open("log.txt", encoding="utf-8") as f:
    print("[5] file content            :", repr(f.read()))

with open("log.txt", "r+", encoding="utf-8") as f:
    f.seek(0, 2)
    f.write("!")
    f.seek(1)
    f.write("-")
with open("log.txt", encoding="utf-8") as f:
    print("[6] r+ with seek, content   :", repr(f.read()))
```

### 3. ★★★ 인코딩 없이 연 파일 — 환경 여덟 가지 × 두 판 (예측)

```text
탐침 하나를 아래 셸 스크립트가 행마다 두 인터프리터로 던진다. 열여섯 줄과 마지막 두 줄의 수를 적는다.
```

```python
# e48_enc_probe.py
# One line, ASCII only: what does open() pick when no encoding is given?
import locale
import sys
import warnings

word = chr(0xD55C) + chr(0xAE00)
with open("utf8.txt", "w", encoding="utf-8") as f:
    f.write(word)

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    with open("plain.txt", "w") as f:
        enc = f.encoding
        try:
            f.write(word)
            wrote = "ok"
        except UnicodeEncodeError as e:
            wrote = "UnicodeEncodeError(%s)" % e.encoding
    try:
        with open("utf8.txt") as f:
            got = "ok" if f.read() == word else "different text"
    except UnicodeDecodeError as e:
        got = "UnicodeDecodeError(%s)" % e.encoding
    preferred = locale.getpreferredencoding(False)
warned = ["%s@line%d" % (w.category.__name__, w.lineno) for w in caught] or ["-"]

cells = [
    "%d.%d" % sys.version_info[:2],
    str(sys.flags.utf8_mode),
    preferred,
    locale.getencoding(),
    enc,
    wrote,
    got,
    ",".join(warned),
]
print(";".join(cells))
```

```sh
# e48_env_grid.sh
#!/usr/bin/env bash
# The same probe under several environments and two interpreters.
# env -i clears everything, so each row states its whole locale environment.
set -u -o pipefail
ROWS=(
  "LANG=ko_KR.UTF-8"
  "LANG=C"
  "LC_ALL=C"
  "LC_ALL=C PYTHONUTF8=0"
  "LC_ALL=C PYTHONCOERCECLOCALE=0 PYTHONUTF8=0"
  "LC_ALL=C PYTHONUTF8=0 -X utf8"
  "LC_ALL=C PYTHONUTF8=1"
  "LANG=ko_KR.UTF-8 -X warn_default_encoding"
)
HEAD="ver;utf8_mode;getpreferredencoding;getencoding;f.encoding;write;read;warnings"
printf '%-46s %s\n' "environment" "$HEAD"
diff=0
fail=0
for row in "${ROWS[@]}"; do
  envs=(); opts=()
  for w in $row; do
    case $w in -X) opts+=("-X") ;; *=*) envs+=("$w") ;; *) opts+=("$w") ;; esac
  done
  declare -A out=()
  for py in python3.11 python3; do
    d=$(mktemp -d -p .)
    line=$(cd "$d" && env -i PATH="$PATH" "${envs[@]}" "$py" "${opts[@]}" - < ../e48_enc_probe.py 2>&1)
    n=$(awk -F';' '{print NF}' <<<"$line")
    [ "$n" = 8 ] || { echo "column count $n: $line"; exit 1; }
    printf '%-46s %s\n' "$row" "$line"
    out[$py]=${line#*;}
  done
  [ "${out[python3.11]}" = "${out[python3]}" ] || diff=$((diff + 1))
  case ${out[python3]} in *UnicodeEncodeError*) fail=$((fail + 1)) ;; esac
  unset out
done
echo "rows where writing the Korean word without encoding= fails (3.12): $fail / ${#ROWS[@]}"
echo "rows where 3.11 and 3.12 differ (version column excluded): $diff / ${#ROWS[@]}"
```

### 4. ★★★ 줄 끝이 섞인 파일을 다섯 가지 `newline` 으로 (예측)

```python
# e48_newline.py
import os
from pathlib import Path

RAW = b"one\r\ntwo\rthree\nfour"
with open("crlf.txt", "wb") as f:
    f.write(RAW)

print("[0] bytes on disk :", RAW, "| os.linesep :", repr(os.linesep))
print("[1] reading, text mode")
for nl in (None, "", "\n", "\r\n", "\r"):
    with open("crlf.txt", encoding="utf-8", newline=nl) as f:
        lines = f.readlines()
        seen = f.newlines
    print("    newline=%-6r readlines %-40r newlines %r" % (nl, lines, seen))
with open("crlf.txt", "rb") as f:
    print("    binary 'rb'   readlines", f.readlines())
print("    Path.read_text()        ", repr(Path("crlf.txt").read_text(encoding="utf-8")))

print("[2] writing 'a\\nb' in text mode, then the bytes on disk")
for nl in (None, "", "\n", "\r\n", "\r"):
    with open("out.txt", "w", encoding="utf-8", newline=nl) as f:
        f.write("a\nb")
    with open("out.txt", "rb") as f:
        print("    newline=%-6r -> %r" % (nl, f.read()))

print("[3] read with default newline, write back with default newline")
with open("crlf.txt", encoding="utf-8") as f:
    text = f.read()
with open("copy.txt", "w", encoding="utf-8") as f:
    f.write(text)
with open("copy.txt", "rb") as f:
    back = f.read()
print("    before :", RAW)
print("    after  :", back)
print("    same bytes :", back == RAW)
```

### 5. ★★ 텍스트와 바이너리를 섞고, 텍스트에서 자리를 옮기면 (예측)

```python
# e48_text_binary.py
import io

word = chr(0xD55C) + chr(0xAE00) + "A"
with open("k.txt", "w", encoding="utf-8") as f:
    n = f.write(word)
print("[1] write() returned            :", n)

with open("k.txt", encoding="utf-8") as f:
    s = f.read()
with open("k.txt", "rb") as f:
    b = f.read()
print("[2] text read  : type %-5s len %d" % (type(s).__name__, len(s)))
print("    binary read: type %-5s len %d  %r" % (type(b).__name__, len(b), b))


def attempt(label, fn):
    try:
        print("    %-34s -> %r" % (label, fn()))
    except Exception as e:
        print("    %-34s -> %s: %s" % (label, type(e).__name__, e))


print("[3] crossing the two modes")
with open("k.txt", "ab") as f:
    attempt("binary file .write('x')", lambda: f.write("x"))
with open("k.txt", "a", encoding="utf-8") as f:
    attempt("text file .write(b'x')", lambda: f.write(b"x"))
attempt("open('k.txt', 'rb', encoding=...)", lambda: open("k.txt", "rb", encoding="utf-8"))

print("[4] seek / tell in text mode")
with open("k.txt", encoding="utf-8") as f:
    f.read(1)
    pos = f.tell()
    attempt("tell() after read(1)", lambda: pos)
    attempt("seek(1) then read()", lambda: (f.seek(1), f.read())[1])
    attempt("seek(1, io.SEEK_CUR)", lambda: f.seek(1, io.SEEK_CUR))
    attempt("seek(0, io.SEEK_END)", lambda: f.seek(0, io.SEEK_END))
with open("k.txt", "rb") as f:
    attempt("binary: seek(1, io.SEEK_CUR)", lambda: f.seek(1, io.SEEK_CUR))
```

### 6. ★★★ 경로 조립과 이름 조각 (예측)

```python
# e48_path.py
import os
from pathlib import Path, PurePosixPath


def attempt(label, fn):
    try:
        print("    %-36s -> %r" % (label, fn()))
    except Exception as e:
        print("    %-36s -> %s: %s" % (label, type(e).__name__, e))


print("[1] joining")
attempt("Path('a') / 'b' / 'c.txt'", lambda: str(Path("a") / "b" / "c.txt"))
attempt("Path('a') / '/b'", lambda: str(Path("a") / "/b"))
attempt("Path('a', '/b', 'c')", lambda: str(Path("a", "/b", "c")))
attempt("'a' + '/' + '/b'", lambda: "a" + "/" + "/b")
attempt("Path('a//b/./c/')", lambda: str(Path("a//b/./c/")))
attempt("Path('a/../b')", lambda: str(Path("a/../b")))
attempt("Path('') == Path('.')", lambda: Path("") == Path("."))

print("[2] name parts of 'data/archive.tar.gz'")
p = PurePosixPath("data/archive.tar.gz")
for attr in ("name", "stem", "suffix", "suffixes", "parent"):
    attempt("." + attr, lambda: str(getattr(p, attr)) if attr == "parent" else getattr(p, attr))
attempt(".with_suffix('.zip')", lambda: str(p.with_suffix(".zip")))
attempt(".with_suffix('')", lambda: str(p.with_suffix("")))
attempt(".with_name('b.txt')", lambda: str(p.with_name("b.txt")))
attempt(".with_suffix('zip')", lambda: str(p.with_suffix("zip")))

print("[3] resolve() -- printed relative to the working directory")
base = Path.cwd()
Path("x").mkdir()
attempt("Path('x/../y').resolve()", lambda: str(Path("x/../y").resolve().relative_to(base)))
attempt("Path('x/../y').exists()", lambda: Path("x/../y").exists())
attempt("Path('x/../y').is_absolute()", lambda: Path("x/../y").is_absolute())
attempt("Path('x').resolve().is_absolute()", lambda: Path("x").resolve().is_absolute())
Path("x/inner").mkdir()
Path("link").symlink_to("x/inner")
attempt("os.path.normpath('link/..')", lambda: os.path.normpath("link/.."))
attempt("Path('link/..').resolve()", lambda: str(Path("link/..").resolve().relative_to(base)))

print("[4] mkdir")
attempt("Path('d/e').mkdir()", lambda: Path("d/e").mkdir())
attempt("Path('d/e').mkdir(parents=True)", lambda: Path("d/e").mkdir(parents=True))
attempt("Path('d/e').mkdir(parents=True)", lambda: Path("d/e").mkdir(parents=True))
attempt("... exist_ok=True", lambda: Path("d/e").mkdir(parents=True, exist_ok=True))

print("[5] write_text / read_text / iterdir")
for n in ("c.txt", "a.txt", "b.txt"):
    (Path("d") / n).write_text(n.upper(), encoding="utf-8")
attempt("sorted(Path('d').iterdir())", lambda: [str(q) for q in sorted(Path("d").iterdir())])
attempt("Path('d/a.txt').read_text(...)", lambda: Path("d/a.txt").read_text(encoding="utf-8"))
attempt("sorted(Path('d').glob('*.txt'))", lambda: [q.name for q in sorted(Path("d").glob("*.txt"))])
```

### 7. ★★★ 「없으면 만들기」 두 가지 (왜)

* `exists()` 로 없는 것을 확인한 뒤 `open(path, 'w')` 로 만드는 코드를 두 작업자가 동시에 돌리면 **무엇이 남나** — 에러는 나나?
* 같은 일을 `open(path, 'x')` 로 하면 무엇이 달라지고, **왜** 그 차이가 생기나 — [26번](../26-eafp-vs-lbyl/2-summary.md)의 어느 처방과 같은 모양인가?

### 8. ★★ 쓰기 쪽 줄바꿈 변환을 이 머신에서 재면 (경계)

* `newline=None` 으로 `'a\nb'` 를 쓴 바이트와 `newline=''` 로 쓴 바이트를 견주면 **이 머신에서** 무엇을 알 수 있고 무엇을 알 수 없나?
* 그 칸을 「재 봤더니 같았다」로 적으면 왜 틀리나 — 그리고 같은 질문을 **다른 창으로** 물으려면 어떻게 하나?

### 9. ★ `pathlib` 의 판 경계 (경계)

* `Path.walk` 와 `relative_to(other, walk_up=True)` 를 `python3.11` 에서 쓰면 각각 무엇이 나나?
* 두 판에서 같은 예외 **타입**이 나는데 문구가 다르다면, 어느 쪽을 근거로 써야 하나?

### 10. 층 가르기 (경계)

* 「`'w'` 는 자른다」·「`'a'` 는 `seek` 과 상관없이 끝에 쓴다」·「텍스트 모드 `tell()` 이 바이트 자리와 같은 숫자를 준다」·「`LC_CTYPE` 이 `C` 면 UTF-8 모드가 켜진다」 —
  각각 **라이브러리 보장 · 플랫폼 한정 서술 · CPython 구현 · 이 판의 관찰** 중 어디인가?
* ★ `open` 절과 `locale`·`os` 절이 **기본 인코딩을 서로 다르게** 적는 자리가 있다 — 실행은 어느 쪽 편이었나?

### 11. 이웃 주제와의 경계 (연결)

* ★ [16번](../16-iterator-protocol/2-summary.md)의 「`iter(f) is f` · 두 번째 `for` 는 빈다」는 파일로 찍으면 어떻게 나오나 — `with` 를 나온 뒤 `read()` 는?
* ★ 텍스트 모드가 **없는** 언어(Go)가 4번과 같은 바이트를 읽으면 `os.ReadFile` · `strings.Split` · `bufio.Scanner` 가 각각 무엇을 주나 — 파이썬의 어느 `newline` 칸과 같은 모양인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
