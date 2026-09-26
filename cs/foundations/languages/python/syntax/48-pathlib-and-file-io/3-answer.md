# python/syntax/48-pathlib-and-file-io — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 11개 = 답 11개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 과 `python3.11` **3.11.15**(Linux, x86_64), 그리고 `go1.27.1` 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했고, **스크립트마다 빈 디렉토리에서** 던져 경로는 전부 상대 경로다. ★ **시간·처리량은 한 번도 재지 않았다.**

## 정답

### 1. 두 상태가 갈린 칸 `21 / 30` — `w`·`w+` 는 있는 파일도 연 순간 `b''` · `r+` 는 `b'Zbc'` · `a` 계열은 `b'abcZ'` · `a+` 의 `read()` 는 `''`

**출력**

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

```text
===== python3 - <e48_modes.py =====
mode file  open                  read()                write Z
r    none  FileNotFoundError     -                     -
r    abc   opened, disk b'abc'   'abc'                 UnsupportedOperation, disk b'abc'
w    none  opened, disk b''      UnsupportedOperation  disk b'Z'
w    abc   opened, disk b''      UnsupportedOperation  disk b'Z'
a    none  opened, disk b''      UnsupportedOperation  disk b'Z'
a    abc   opened, disk b'abc'   UnsupportedOperation  disk b'abcZ'
x    none  opened, disk b''      UnsupportedOperation  disk b'Z'
x    abc   FileExistsError       -                     -
r+   none  FileNotFoundError     -                     -
r+   abc   opened, disk b'abc'   'abc'                 disk b'Zbc'
w+   none  opened, disk b''      ''                    disk b'Z'
w+   abc   opened, disk b''      ''                    disk b'Z'
a+   none  opened, disk b''      ''                    disk b'Z'
a+   abc   opened, disk b'abc'   ''                    disk b'abcZ'
x+   none  opened, disk b''      ''                    disk b'Z'
x+   abc   FileExistsError       -                     -
rb   none  FileNotFoundError     -                     -
rb   abc   opened, disk b'abc'   b'abc'                UnsupportedOperation, disk b'abc'
ab   none  opened, disk b''      UnsupportedOperation  disk b'Z'
ab   abc   opened, disk b'abc'   UnsupportedOperation  disk b'abcZ'
modes whose open() leaves an existing 'abc' file empty: w, w+
cells where the two states give different results: 21 / 30
(exit 0)
```

**왜 그런가**

* ★★★ **`'w'` 는 여는 순간 자른다** — 아무것도 안 쓰고 닫아도 `b''`. 그래서 `w` 행은 있는 파일과 없는 파일이 **세 칸 다 같다.** `w+` 도 자른다(문서 — *"Modes `'w+'` and `'w+b'` open and truncate the file"*).
* ★★★ **`r+` 는 안 자르고 위치 0 에서 덮어쓴다** — `Zbc`. **`a` 계열은 끝에 붙는다** — `abcZ`. `a+` 는 **끝에서 시작**하니 바로 `read()` 하면 `''`.
* ★★ **`x`·`x+` 는 있으면 `FileExistsError`**, **`r`·`r+`·`rb` 는 없으면 `FileNotFoundError`** — 나머지 여섯 모드는 없는 파일을 만든다.
* ★ `+` 가 없으면 **반대쪽 연산이 `UnsupportedOperation`** — 여는 것은 된다.

### 2. `a+` 는 `seek(0)` 뒤에도 끝에 쓴다(`'abcZ'`, `tell()` `4`) · `r+` 는 `seek` 한 자리에 덮어쓴다(`'a-cZ!'`)

**출력**

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

```text
===== python3 - <e48_append_seek.py =====
[1] tell() right after open : 3
[2] read() after seek(0)    : 'abc'
[3] tell() after seek(0)    : 0
[4] tell() after write      : 4
[5] file content            : 'abcZ'
[6] r+ with seek, content   : 'a-cZ!'
(exit 0)
```

**왜 그런가**

* ★★ `a+` 는 연 직후 `tell()` 이 `3` — 끝에서 시작한다. `seek(0)` 으로 **읽기 위치**는 0 이 되지만 **쓰기는 끝으로 간다.**
  ★ 문서는 이것을 *"on some Unix systems"* 로 **한정**해 적는다 — 이 머신(Linux)의 관찰이다.
* ★ `r+` 는 `seek` 이 쓰기에도 듣는다 — 끝에 `!`, 자리 1 에 `-`. 덮어쓰기라 **길이는 `!` 만큼만** 늘었다.

### 3. `LANG=C` 는 UTF-8 모드가 켜져 한글 쓰기 `ok` · 깨지는 것은 `PYTHONUTF8=0` 두 행(`2 / 8`) · 3.11 과 3.12 차이 `0 / 8` · 경고는 12·20·24행

**출력**

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

```text
===== cd e48_env && bash e48_env_grid.sh =====
environment                                    ver;utf8_mode;getpreferredencoding;getencoding;f.encoding;write;read;warnings
LANG=ko_KR.UTF-8                               3.11;0;UTF-8;UTF-8;UTF-8;ok;ok;-
LANG=ko_KR.UTF-8                               3.12;0;UTF-8;UTF-8;UTF-8;ok;ok;-
LANG=C                                         3.11;1;utf-8;UTF-8;utf-8;ok;ok;-
LANG=C                                         3.12;1;utf-8;UTF-8;utf-8;ok;ok;-
LC_ALL=C                                       3.11;1;utf-8;ANSI_X3.4-1968;utf-8;ok;ok;-
LC_ALL=C                                       3.12;1;utf-8;ANSI_X3.4-1968;utf-8;ok;ok;-
LC_ALL=C PYTHONUTF8=0                          3.11;0;ANSI_X3.4-1968;ANSI_X3.4-1968;ANSI_X3.4-1968;UnicodeEncodeError(ascii);UnicodeDecodeError(ascii);-
LC_ALL=C PYTHONUTF8=0                          3.12;0;ANSI_X3.4-1968;ANSI_X3.4-1968;ANSI_X3.4-1968;UnicodeEncodeError(ascii);UnicodeDecodeError(ascii);-
LC_ALL=C PYTHONCOERCECLOCALE=0 PYTHONUTF8=0    3.11;0;ANSI_X3.4-1968;ANSI_X3.4-1968;ANSI_X3.4-1968;UnicodeEncodeError(ascii);UnicodeDecodeError(ascii);-
LC_ALL=C PYTHONCOERCECLOCALE=0 PYTHONUTF8=0    3.12;0;ANSI_X3.4-1968;ANSI_X3.4-1968;ANSI_X3.4-1968;UnicodeEncodeError(ascii);UnicodeDecodeError(ascii);-
LC_ALL=C PYTHONUTF8=0 -X utf8                  3.11;1;utf-8;ANSI_X3.4-1968;utf-8;ok;ok;-
LC_ALL=C PYTHONUTF8=0 -X utf8                  3.12;1;utf-8;ANSI_X3.4-1968;utf-8;ok;ok;-
LC_ALL=C PYTHONUTF8=1                          3.11;1;utf-8;ANSI_X3.4-1968;utf-8;ok;ok;-
LC_ALL=C PYTHONUTF8=1                          3.12;1;utf-8;ANSI_X3.4-1968;utf-8;ok;ok;-
LANG=ko_KR.UTF-8 -X warn_default_encoding      3.11;0;UTF-8;UTF-8;UTF-8;ok;ok;EncodingWarning@line12,EncodingWarning@line20,EncodingWarning@line24
LANG=ko_KR.UTF-8 -X warn_default_encoding      3.12;0;UTF-8;UTF-8;UTF-8;ok;ok;EncodingWarning@line12,EncodingWarning@line20,EncodingWarning@line24
rows where writing the Korean word without encoding= fails (3.12): 2 / 8
rows where 3.11 and 3.12 differ (version column excluded): 0 / 8
(exit 0)
```

**왜 그런가**

* ★★★ **로캘이 `C` 면 UTF-8 모드가 저절로 켜진다**(PEP 540 · 문서 — *"enabled if the LC_CTYPE locale is `C` or `POSIX` at Python startup"*). `LANG=C` 행은 **로캘 강제 변환**(PEP 538)까지 되어 `getencoding` 도 `UTF-8`.
* ★★★ **`LC_ALL=C` 는 강제 변환을 막지만**(`getencoding` 이 `ANSI_X3.4-1968`) **UTF-8 모드는 켜져** `f.encoding` 이 `utf-8` — `getencoding` 은 **UTF-8 모드를 무시한다.**
* ★★★ **`PYTHONUTF8=0` 을 줘야** 로캘의 ASCII 로 떨어져 쓰기 `UnicodeEncodeError(ascii)` · 읽기 `UnicodeDecodeError(ascii)`. `-X utf8` 은 그것을 다시 켰다.
* ★★ **두 판이 한 칸도 안 갈렸다**(`0 / 8`) — 다음 경계는 **3.15 의 UTF-8 기본**(PEP 686 · 문서).
* ★★ **`-X warn_default_encoding`** 행 — 경고가 탐침 **파일의 12행**(`open` 쓰기) · **20행**(`open` 읽기) · **24행**(`getpreferredencoding(False)`)에서 났다. 셋째가 `open` 이 아닌 것에 주의.

### 4. `None` 은 `\r\n`·`\r` 을 `\n` 으로(리눅스에서도) · `''` 는 끊되 안 바꾼다 · 쓰기는 `None`·`''`·`'\n'` 이 같은 `b'a\nb'` · 왕복하면 `same bytes : False`

**출력**

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

```text
===== python3 - <e48_newline.py =====
[0] bytes on disk : b'one\r\ntwo\rthree\nfour' | os.linesep : '\n'
[1] reading, text mode
    newline=None   readlines ['one\n', 'two\n', 'three\n', 'four']    newlines ('\r', '\n', '\r\n')
    newline=''     readlines ['one\r\n', 'two\r', 'three\n', 'four']  newlines ('\r', '\n', '\r\n')
    newline='\n'   readlines ['one\r\n', 'two\rthree\n', 'four']      newlines None
    newline='\r\n' readlines ['one\r\n', 'two\rthree\nfour']          newlines None
    newline='\r'   readlines ['one\r', '\ntwo\r', 'three\nfour']      newlines None
    binary 'rb'   readlines [b'one\r\n', b'two\rthree\n', b'four']
    Path.read_text()         'one\ntwo\nthree\nfour'
[2] writing 'a\nb' in text mode, then the bytes on disk
    newline=None   -> b'a\nb'
    newline=''     -> b'a\nb'
    newline='\n'   -> b'a\nb'
    newline='\r\n' -> b'a\r\nb'
    newline='\r'   -> b'a\rb'
[3] read with default newline, write back with default newline
    before : b'one\r\ntwo\rthree\nfour'
    after  : b'one\ntwo\nthree\nfour'
    same bytes : False
(exit 0)
```

**왜 그런가**

* ★★★ **읽기 변환은 플랫폼과 무관하다** — `newline=None` 은 유니버설 개행이라 세 줄 끝을 전부 알아보고 `\n` 으로 바꾼다. 문서 — *"all the processing is done by Python itself, and is therefore platform-independent"*.
* ★★ **`''` 는 끊는 규칙이 같고 바꾸지만 않는다.** `'\n'`·`'\r\n'`·`'\r'` 은 **그 문자열에서만** 끊는다. `f.newlines` 는 유니버설일 때만 튜플이다.
* ★★★ **쓰기의 `None` 은 `\n` 을 `os.linesep`(이 머신 `'\n'`)으로 바꾼다** — 바꿀 것이 없어 `''`·`'\n'` 과 같다.
* ★★★ **`[3]`** — 기본값으로 읽어 기본값으로 쓰면 원래 줄 끝이 **`\n` 으로 굳는다.** `rb` 로 다시 읽어야 보인다.

### 5. `write()` 는 글자 수 `3` · 섞으면 `TypeError` 둘 · `'rb'` + `encoding=` 은 `ValueError` · `tell()` `3` · `seek(1)` 뒤 `UnicodeDecodeError` · `SEEK_CUR` 는 텍스트만 거절

**출력**

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

```text
===== python3 - <e48_text_binary.py =====
[1] write() returned            : 3
[2] text read  : type str   len 3
    binary read: type bytes len 7  b'\xed\x95\x9c\xea\xb8\x80A'
[3] crossing the two modes
    binary file .write('x')            -> TypeError: a bytes-like object is required, not 'str'
    text file .write(b'x')             -> TypeError: write() argument must be str, not bytes
    open('k.txt', 'rb', encoding=...)  -> ValueError: binary mode doesn't take an encoding argument
[4] seek / tell in text mode
    tell() after read(1)               -> 3
    seek(1) then read()                -> UnicodeDecodeError: 'utf-8' codec can't decode byte 0x95 in position 0: invalid start byte
    seek(1, io.SEEK_CUR)               -> UnsupportedOperation: can't do nonzero cur-relative seeks
    seek(0, io.SEEK_END)               -> 7
    binary: seek(1, io.SEEK_CUR)       -> 1
(exit 0)
```

**왜 그런가**

* ★★ **텍스트 모드는 `str`, 바이너리는 `bytes`** 만 받는다 — 서로를 `TypeError` 로 거절한다. 바이너리엔 인코딩이 없으니 `encoding=` 자체가 `ValueError`.
* ★★★ **텍스트의 `tell()` 은 글자 수가 아니다** — 한 글자 읽고 `3`. 문서가 약속하는 것은 *"opaque number"* 뿐이고, **바이트 자리와 같았던 것은 이 판의 관찰**이다. 그 숫자가 아닌 곳으로 `seek` 하면 글자 한가운데라 `UnicodeDecodeError`.
* ★ 텍스트 모드는 **현재 위치 기준 0 아닌 이동**을 거절한다(`can't do nonzero cur-relative seeks`) — 바이너리는 `1`.

### 6. `Path('a') / '/b'` 는 `'/b'` · `..` 은 안 줄인다 · `suffix` 는 `.gz` 하나 · 점 없는 접미사는 `ValueError` · 링크가 끼면 `normpath` 와 `resolve` 가 갈린다

**출력**

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

```text
===== python3 - <e48_path.py =====
[1] joining
    Path('a') / 'b' / 'c.txt'            -> 'a/b/c.txt'
    Path('a') / '/b'                     -> '/b'
    Path('a', '/b', 'c')                 -> '/b/c'
    'a' + '/' + '/b'                     -> 'a//b'
    Path('a//b/./c/')                    -> 'a/b/c'
    Path('a/../b')                       -> 'a/../b'
    Path('') == Path('.')                -> True
[2] name parts of 'data/archive.tar.gz'
    .name                                -> 'archive.tar.gz'
    .stem                                -> 'archive.tar'
    .suffix                              -> '.gz'
    .suffixes                            -> ['.tar', '.gz']
    .parent                              -> 'data'
    .with_suffix('.zip')                 -> 'data/archive.tar.zip'
    .with_suffix('')                     -> 'data/archive.tar'
    .with_name('b.txt')                  -> 'data/b.txt'
    .with_suffix('zip')                  -> ValueError: Invalid suffix 'zip'
[3] resolve() -- printed relative to the working directory
    Path('x/../y').resolve()             -> 'y'
    Path('x/../y').exists()              -> False
    Path('x/../y').is_absolute()         -> False
    Path('x').resolve().is_absolute()    -> True
    os.path.normpath('link/..')          -> '.'
    Path('link/..').resolve()            -> 'x'
[4] mkdir
    Path('d/e').mkdir()                  -> FileNotFoundError: [Errno 2] No such file or directory: 'd/e'
    Path('d/e').mkdir(parents=True)      -> None
    Path('d/e').mkdir(parents=True)      -> FileExistsError: [Errno 17] File exists: 'd/e'
    ... exist_ok=True                    -> None
[5] write_text / read_text / iterdir
    sorted(Path('d').iterdir())          -> ['d/a.txt', 'd/b.txt', 'd/c.txt', 'd/e']
    Path('d/a.txt').read_text(...)       -> 'A.TXT'
    sorted(Path('d').glob('*.txt'))      -> ['a.txt', 'b.txt', 'c.txt']
(exit 0)
```

**왜 그런가**

* ★★★ **절대 경로 조각은 앞 조각을 버린다** — `'/b'` · `'/b/c'`. 문자열 `+` 는 그냥 붙여 `'a//b'`. 문서 — *"If a segment is an absolute path, all previous segments are ignored"*.
* ★★ **`Path` 는 `//`·`.`·끝 `/` 는 정리하고 `..` 은 둔다** — `link/..` 을 글자로 줄이면 `.`, 실제로 따라가면 `x`. 둘이 다른 것이 `..` 을 안 줄이는 이유다.
* ★★ `with_suffix('.zip')` 는 **마지막 접미사 하나만** 바꾼다 — `archive.tar.zip`.
* ★ `mkdir` — 부모 없음 `FileNotFoundError` · 두 번째 `FileExistsError` · `exist_ok=True` 라야 조용. `iterdir` 은 **임의 순서**라 `sorted` 로 찍었다.

### 7. `exists()` + `'w'` 는 둘 다 「없다」를 보고 `'from B'` 가 남는다(에러 없음) · `'x'` 는 B 가 `FileExistsError` — 검사와 생성이 `open` 한 번 안에 있다

**출력**

```python
# e48_exclusive.py
import errno
import os

NAME = "report.txt"

print("[1] exists() then open('w') -- two writers, interleaved")
a_saw = os.path.exists(NAME)
b_saw = os.path.exists(NAME)
print("    A saw exists():", a_saw, "| B saw exists():", b_saw)
if not a_saw:
    with open(NAME, "w", encoding="utf-8") as f:
        f.write("from A")
if not b_saw:
    with open(NAME, "w", encoding="utf-8") as f:
        f.write("from B")
with open(NAME, encoding="utf-8") as f:
    print("    content:", repr(f.read()))

os.remove(NAME)
print("[2] open('x') -- the same two writers")
for who in ("A", "B"):
    try:
        with open(NAME, "x", encoding="utf-8") as f:
            f.write("from " + who)
        print("    %s: created" % who)
    except FileExistsError as e:
        print("    %s: %s %s" % (who, type(e).__name__, errno.errorcode[e.errno]))
with open(NAME, encoding="utf-8") as f:
    print("    content:", repr(f.read()))
```

```text
===== python3 - <e48_exclusive.py =====
[1] exists() then open('w') -- two writers, interleaved
    A saw exists(): False | B saw exists(): False
    content: 'from B'
[2] open('x') -- the same two writers
    A: created
    B: FileExistsError EEXIST
    content: 'from A'
(exit 0)
```

**왜 그런가**

* ★★★ **`exists()` 와 `open('w')` 는 두 번의 동작**이라 사이에 틈이 있다. 둘 다 틈에서 「없다」를 봤고, B 의 `'w'` 가 **여는 순간 A 의 것을 잘랐다**(1번). 에러가 없어 **조용히 하나가 사라진다.**
* ★★★ **`'x'` 는 「없나?」와 「만들기」를 한 번에** 한다 — 틈이 없으니 둘째가 `FileExistsError`. [26번](../26-eafp-vs-lbyl/2-summary.md)의 **EAFP**(일단 하고 예외를 받는다)가 **모드 글자 하나**로 들어온 모양이다.
* ★ 순서는 **코드로 고정**했다(스레드 없음) — 26번과 같은 방법이라 매번 같은 출력이다.

### 8. 이 머신의 `os.linesep` 이 `'\n'` 이라 `None` 칸은 바꿀 것이 없다 — 「잴 것이 없다」(부적용) · `newline='\r\n'` 을 손으로 줘서 물었다(제5의 상태)

**왜 그런가**

* ★★★ `None` 쓰기는 `\n` 을 **`os.linesep` 으로** 바꾸는데 이 머신에서 그것이 **`'\n'`**(4번 `[0]`)이다. 그래서 `None`·`''` 가 같은 `b'a\nb'` 인 것은 **변환이 안 일어나서가 아니라 바꿔도 같은 글자라서**다 — 이 칸으로는 「변환이 있나」를 **원리상 못 가른다.**
* ★★ 그래서 「재 봤더니 같았다」가 아니라 **「잴 것이 없다」**(제4의 상태 — 부적용)로 적는다. 「윈도에서는 `b'a\r\nb'` 가 된다」는 **문서의 말**이다.
* ★★ **다른 창** — `newline='\r\n'` 을 **명시**하면 윈도의 기본이 할 일을 리눅스에서 바이트로 볼 수 있다(4번 `[2]` 의 `b'a\r\nb'`). 이 창이 못 보는 것은 「윈도의 `os.linesep` 이 정말 그 값인가」다.

### 9. 3.11 은 `Path.walk` 가 없고(`False`) `walk_up=` 은 `TypeError` · 같은 `ValueError` 의 문구가 두 판에서 다르다 — 타입을 근거로

**출력**

```python
# e48_version.py
import sys
from pathlib import Path, PurePosixPath

print("python", "%d.%d" % sys.version_info[:2])
for name in ("walk", "with_segments", "is_junction", "read_text"):
    print("    %-32s : %s" % ("hasattr(Path, %r)" % name, hasattr(Path, name)))
try:
    r = PurePosixPath("a/b").relative_to("a/c", walk_up=True)
    print("    relative_to('a/c', walk_up=True) ->", r)
except TypeError as e:
    print("    relative_to('a/c', walk_up=True) -> TypeError:", e)
try:
    PurePosixPath("a/b").relative_to("a/c")
except ValueError as e:
    print("    relative_to('a/c')               -> ValueError:", e)
```

```text
===== python3 - <e48_version.py =====
python 3.12
    hasattr(Path, 'walk')            : True
    hasattr(Path, 'with_segments')   : True
    hasattr(Path, 'is_junction')     : True
    hasattr(Path, 'read_text')       : True
    relative_to('a/c', walk_up=True) -> ../b
    relative_to('a/c')               -> ValueError: 'a/b' is not in the subpath of 'a/c'
(exit 0)
```

```text
===== python3.11 - <e48_version_py311.py =====
python 3.11
    hasattr(Path, 'walk')            : False
    hasattr(Path, 'with_segments')   : False
    hasattr(Path, 'is_junction')     : False
    hasattr(Path, 'read_text')       : True
    relative_to('a/c', walk_up=True) -> TypeError: PurePath.relative_to() got an unexpected keyword argument 'walk_up'
    relative_to('a/c')               -> ValueError: 'a/b' is not in the subpath of 'a/c' OR one path is relative and the other is absolute.
(exit 0)
```

(3.11 블록의 소스는 위와 **한 글자도 같다** — 파일 이름만 `e48_version_py311.py` 다.)

**왜 그런가**

* ★★ `Path.walk`·`with_segments`·`is_junction`·`relative_to(walk_up=)` 는 **3.12** 에 들어왔다 — 3.11 은 속성이 없고 키워드를 모른다(`unexpected keyword argument 'walk_up'`).
* ★ **예외 문구는 구현**이다 — 3.11 의 `ValueError` 에는 `OR one path is relative and the other is absolute.` 가 더 붙어 있다. 판을 건너 근거로 쓸 것은 **타입**(`ValueError`)이다.

### 10. 보장 · 플랫폼 한정 서술 · CPython 구현 · 보장 — 실행은 `os`·`locale` 절 편이었다

**왜 그런가**

| 사실 | 층 | 근거 |
|---|---|---|
| `'w'` 는 자른다 | **라이브러리 보장** | `open` 모드 표 |
| `'a'` 는 `seek` 과 상관없이 끝에 쓴다 | **플랫폼 한정 서술** + 이 머신의 관찰 | `open` — *"on some Unix systems"* |
| 텍스트 `tell()` 이 바이트 자리와 같은 숫자 | **CPython 구현**(이 판의 관찰) | 문서는 *"opaque number"* 만 약속 |
| `LC_CTYPE` 이 `C` 면 UTF-8 모드 | **라이브러리 보장** | `os` — Python UTF-8 Mode |

* ★★★ **어긋나는 문서** — 3.12 `open` 절은 기본 인코딩을 *"`locale.getencoding` is called"* 로 적는데, `locale` 절은 그 함수가 **UTF-8 모드를 무시한다**고, `os` 절은 UTF-8 모드면 `open` 이 **UTF-8** 을 쓴다고 적는다.
  **실행은 뒤쪽 편**이었다 — `LC_ALL=C` 행에서 `getencoding` 은 `ANSI_X3.4-1968`, `f.encoding` 은 `utf-8`(3번).

### 11. 첫 `for` 뒤 둘째는 `[]` · 끝의 `readline()` 은 `''` · `seek(0)` 이 되감기 · `with` 뒤 `read()` 는 `ValueError` / Go 는 바이트 그대로 · `Split` 은 `newline='\n'` 칸과 같은 모양 · `Scanner` 는 `\r\n` 만 벗긴다

**출력**

```python
# e48_iterate.py
with open("lines.txt", "w", encoding="utf-8") as f:
    f.write("a\nb\nc\n")

with open("lines.txt", encoding="utf-8") as f:
    print("[1] iter(f) is f          :", iter(f) is f)
    first = [line for line in f]
    second = [line for line in f]
    print("[2] first pass            :", first)
    print("[3] second pass           :", second)
    print("[4] readline() at the end :", repr(f.readline()))
    f.seek(0)
    print("[5] after seek(0)         :", [line.rstrip("\n") for line in f])
print("[6] closed after with     :", f.closed)
try:
    f.read()
except ValueError as e:
    print("[7] read() after with     :", type(e).__name__, "-", e)
```

```text
===== python3 - <e48_iterate.py =====
[1] iter(f) is f          : True
[2] first pass            : ['a\n', 'b\n', 'c\n']
[3] second pass           : []
[4] readline() at the end : ''
[5] after seek(0)         : ['a', 'b', 'c']
[6] closed after with     : True
[7] read() after with     : ValueError - I/O operation on closed file.
(exit 0)
```

```go
// e48_crlf.go
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

func main() {
	raw := []byte("one\r\ntwo\rthree\nfour")
	if err := os.WriteFile("crlf.txt", raw, 0o644); err != nil {
		panic(err)
	}

	data, err := os.ReadFile("crlf.txt")
	if err != nil {
		panic(err)
	}
	fmt.Printf("[1] os.ReadFile              %q\n", data)
	fmt.Printf("[2] strings.Split(s, \"\\n\")   %q\n", strings.Split(string(data), "\n"))

	f, err := os.Open("crlf.txt")
	if err != nil {
		panic(err)
	}
	defer f.Close()
	var lines []string
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		lines = append(lines, sc.Text())
	}
	fmt.Printf("[3] bufio.Scanner lines      %q\n", lines)
}
```

```text
===== cd e48_go && go run e48_crlf.go =====
[1] os.ReadFile              "one\r\ntwo\rthree\nfour"
[2] strings.Split(s, "\n")   ["one\r" "two\rthree" "four"]
[3] bufio.Scanner lines      ["one" "two\rthree" "four"]
(exit 0)
```

**왜 그런가**

* ★★ **파일 객체는 자기 자신의 이터레이터**다([16번](../16-iterator-protocol/2-summary.md)이 정본) — 한 번 돌면 위치가 끝이라 둘째는 `[]`, 되감기는 `seek(0)`. `with` 를 나오면 닫혀 `I/O operation on closed file.`
* ★★ **Go 는 텍스트 모드가 없다** — `os.ReadFile` 이 `\r\n` 을 그대로 준다. `strings.Split(s, "\n")` 은 `"one\r"` 를 남겨 파이썬 **`newline='\n'` 칸**(`'one\r\n'` 에서 끊기) 과 같은 곳에서 끊는다.
* ★ **`bufio.Scanner` 는 줄 끝 `\r\n` 은 벗기고 외톨이 `\r` 은 둔다** — `"two\rthree"` 가 한 줄이라 줄 수가 **3**. 파이썬 기본(`None`)은 외톨이 `\r` 도 줄 끝이라 **4**.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 모드 격자 | `python3 - <e48_modes.py` | 3(캡처 + 재대조 + `PYTHONHASHSEED` 바꾼 재캡처) | **21 / 30** · 자르는 모드 `w, w+` |
| `a+` 와 `seek` | `python3 - <e48_append_seek.py` | 3 | `'abcZ'` · `'a-cZ!'` |
| `'x'` 와 경쟁 | `python3 - <e48_exclusive.py` | 3 | `'from B'` / `FileExistsError EEXIST` |
| 환경 × 판 격자 | `cd e48_env && bash e48_env_grid.sh`(`env -i` · `python3.11`·`python3`) | 3 | **2 / 8** 깨짐 · 판 차이 **0 / 8** |
| `newline` | `python3 - <e48_newline.py` | 3 | `None` 이 `\r\n` 을 `\n` 으로 · `same bytes : False` |
| 텍스트 대 바이너리 | `python3 - <e48_text_binary.py` | 3 | `tell()` `3` · `UnicodeDecodeError` |
| 이터레이션 | `python3 - <e48_iterate.py` | 3 | 둘째 `[]` · `ValueError` |
| `Path` | `python3 - <e48_path.py` | 3 | `'/b'` · `link/..` 이 `.` 대 `x` |
| 판 격자 | `python3 - <e48_version.py` · `python3.11 - <e48_version_py311.py` | 3씩 | 3.11 `walk_up` `TypeError` |
| Go 대비 | `cd e48_go && go run e48_crlf.go` | 3 | `\r\n` 그대로 · 줄 수 3 |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ★★ 환경 격자 | **3.15** 에서 UTF-8 이 기본이 된다(PEP 686 — 문서) |
| ★ 판 격자 | `pathlib` 은 판마다 API 가 는다 |
| 예외 **문구** · 텍스트 `tell()` 의 숫자 | 구현이다 |
| ★ 쓰기 쪽 `os.linesep` 칸 | **윈도에서** 다시 돌려야 뜻이 생긴다(이 머신은 부적용) |

★ **안 흔들리는 칸** — 격자의 **「21 / 30」·「2 / 8」·「0 / 8」** · 디스크 바이트 · 예외 타입 · 상대 경로 · `(exit N)`.
★★ **이 주제가 한 번도 안 잰 것** — **시간·처리량**(부적용) · **3.15 · 윈도**(판·플랫폼 없음 — 못 잰 것).
