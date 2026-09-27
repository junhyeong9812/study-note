# python/syntax/48-pathlib-and-file-io — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만(문서 원본 `.rst` 를 받아 문장을 찾았다).
> - [`open()`(3.12)](https://docs.python.org/3.12/library/functions.html#open) — 모드 표 · *"`'w'` for writing (truncating the file if it already exists), `'x'` for exclusive creation, and `'a'` for appending (which on some Unix systems, means that all writes append to the end of the file regardless of the current seek position)"* ·
>   *"Modes `'w+'` and `'w+b'` open and truncate the file. Modes `'r+'` and `'r+b'` open the file with no truncation."* · `newline` 절 전문(읽기·쓰기 두 불릿) ·
>   *"Python doesn't depend on the underlying operating system's notion of text files; all the processing is done by Python itself, and is therefore platform-independent."*
> - [`io` — Text Encoding](https://docs.python.org/3.12/library/io.html#text-encoding) · *Opt-in EncodingWarning*(3.10) · `TextIOWrapper` 의 *"The default encoding is now `locale.getpreferredencoding(False)`"*(3.3)
> - [`os` — Python UTF-8 Mode](https://docs.python.org/3.12/library/os.html#utf8-mode) — *"The Python UTF-8 Mode is enabled if the LC_CTYPE locale is `C` or `POSIX` at Python startup"* · *"`open()`, `io.open()`, and `codecs.open()` use the UTF-8 encoding by default"*
> - [`PYTHONCOERCECLOCALE`](https://docs.python.org/3.12/using/cmdline.html#envvar-PYTHONCOERCECLOCALE) — 강제 변환은 *"the `LC_ALL` locale override environment variable is also not set"* 일 때만
> - [`locale.getencoding`](https://docs.python.org/3.12/library/locale.html#locale.getencoding) — *"except this function ignores the Python UTF-8 Mode"*(3.11)
> - [`pathlib`(3.12)](https://docs.python.org/3.12/library/pathlib.html) — *"If a segment is an absolute path, all previous segments are ignored (like `os.path.join`)"* · `iterdir` 의 *"The children are yielded in arbitrary order"* · `relative_to` 의 `walk_up`(3.12)
> - [PEP 686](https://peps.python.org/pep-0686/) · [What's New 3.15](https://docs.python.org/3.15/whatsnew/3.15.html) — *"Python now uses UTF-8 as the default encoding, independent of the system's environment."* ★ **3.15 는 이 머신에 없다 — 문서 인용만.**
>
> **실행 검증** — 이 문서에 실린 출력은 전부 이 머신(Linux)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> 판은 `python3` **3.12.3** 이 본판이고, 판 경계를 위해 `python3.11` **3.11.15** 로 두 블록(판 격자 · 환경 격자)을 더 던졌다. 교차 갈래 대비로 `go1.27.1` 한 블록.\
> ★★ **파일은 전부 스크립트마다 새로 만든 빈 디렉토리 안에서** 만들었다 — 출력의 경로는 전부 그 디렉토리 기준 **상대 경로**다(`resolve()` 결과도 `relative_to(Path.cwd())` 로 찍었다).\
> ★★★ **이 문서는 시간·바이트 처리량을 한 번도 재지 않았다** — 「바이너리 모드가 빠르다」 같은 말은 하지 않는다.\
> **버전** — `EncodingWarning`·`encoding="locale"` **3.10** · `locale.getencoding` **3.11** · `Path.walk`·`relative_to(walk_up=)` **3.12** · UTF-8 모드 **3.7**(PEP 540) · UTF-8 기본 **3.15**(PEP 686 — 문서만).\
> ★ **구현 대 언어 보장 한 줄** — 모드 표·`newline` 규칙·UTF-8 모드의 켜지는 조건이 **라이브러리 보장**이고, 예외 **문구**와 `tell()` 이 돌려주는 **숫자의 뜻**은 CPython 의 것이다. **로캘 환경**(이 머신 `LANG=ko_KR.UTF-8`)은 관찰이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | 머신의 로캘이 바뀌면 **아무 환경변수도 안 준 행**(그래서 환경 격자는 `env -i` 로 **행마다 환경 전체**를 적었다) | ★★ 격자 마지막 줄 **「… N / M」** · 디스크 바이트(`rb` 로 다시 읽은 것) |
> | 판이 오르면 예외 **문구**(3.11 과 3.12 의 `relative_to` 문구가 이미 다르다 — 동작 8) | 예외 **타입** · `(exit N)` · 경로 문자열(상대) |
> | — (주소·시간·`set` 출력·`iterdir` 날것의 순서를 한 곳도 안 찍었다 — `iterdir` 은 `sorted` 로 찍었다) | `errno` 는 **이름**(`EEXIST`)으로 찍었다 · `[Errno 17]` 은 문구 안의 것 |
>
> **선행** — [06-strings-bytes-unicode](../06-strings-bytes-unicode/2-summary.md)(★★★ **텍스트 모드는 안에서 `decode`/`encode` 를 해 준다 — 그때 쓰는 인코딩이 이 주제의 절반이다**) ·
> [28-context-managers-and-with](../28-context-managers-and-with/2-summary.md)(`with open(...)` — 닫는 것은 그쪽이 정본) ·
> [16-iterator-protocol](../16-iterator-protocol/2-summary.md)(파일 객체는 자기 자신의 이터레이터).

## 한눈에 — 쉽게 말하면

**파일을 여는 것은 「창고 출입증」을 받는 것이다.** 증의 종류(모드)가 **들어가자마자 무엇이 일어나는지**를 정한다.

* `'r'` — **열람증.** 창고가 없으면 입구에서 막힌다.
* `'w'` — **「비우고 새로 채우기」증.** 들어가는 순간 선반을 **전부 비운다** — 아직 아무것도 안 놓았어도.
* `'a'` — **「맨 끝에만 덧붙이기」증.** 어디를 가리키든 놓는 자리는 끝이다.
* `'x'` — **「빈 터에만 새로 짓기」증.** 이미 창고가 있으면 입구에서 막힌다.
* `+` — 위 증에 **열람도 겸하게** 해 준다. 비우는 증은 `+` 를 붙여도 여전히 비운다.
* ★ **텍스트 모드는 창구에 통역사**(인코딩)가 앉아 있고, **바이너리 모드는 상자째** 주고받는다. 통역사는 **줄바꿈 기호도 한 가지로 통일해** 건넨다(`newline=None`).

```text
   같은 창고(t.txt, 안에 "abc")에 증 종류만 바꿔 들어간 직후 — 선반에 남은 것

   'r'   abc     'r+'  abc      'a'  abc      'a+'  abc
   'w'   (빈 칸)  'w+'  (빈 칸)   'x'  입구에서 막힘(FileExistsError)
                 ★ 아무것도 쓰기 전에 이미 비었다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 출입증의 종류 | `open` 의 `mode` 문자열 | 모드 격자(동작 1) |
| 들어가자마자 선반을 비운다 | `'w'`·`'w+'` 의 **자르기(truncate)** | 연 직후 디스크 바이트 `b''` |
| 놓는 자리는 끝뿐 | `'a'` 계열 — **`seek` 을 무시하는 쓰기** | `seek(0)` 뒤에 써도 끝에 붙는다(동작 2) |
| 빈 터에만 짓는다 | `'x'` — **없으면 만들기를 한 번에** | 둘째 사람이 `FileExistsError`(동작 3) |
| 창구의 통역사 | 텍스트 모드의 **인코딩** | 환경 격자(동작 4) |
| 통역사가 줄바꿈을 통일한다 | `newline=None` 의 **유니버설 개행** | `\r\n` 이 `\n` 으로 온다(동작 5) |
| 상자째 주고받기 | 바이너리 모드 `'b'` | `bytes` 가 온다 · 변환 없음(동작 6) |
| 창고 주소 쪽지 | `pathlib.Path` | 조립 규칙(동작 7) |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**설정 파일을 고치려고 `open(path, 'w')` 로 열었다가 예외가 나서 파일이 빈 채로 남았다**」·
「**내 노트북에서는 되는데 서버·컨테이너에서 한글이 깨진다**」·
「**윈도에서 만든 CSV 를 읽어 다시 썼더니 줄 끝 바이트가 바뀌었다**」가 그것이다.\
첫째는 **`'w'` 가 여는 순간 비운다**는 것이고, 둘째는 **`encoding` 을 안 줘서 로캘을 따라간** 것이고, 셋째는 **통역사가 줄바꿈을 통일한** 것이다.

> **텍스트 모드(text mode)** — 파일의 바이트를 **인코딩으로 풀어 `str`** 로 주고받는 모드. 기본값이다.\
> 예: `open('a.txt').read()` 는 `str` 을 준다([06번](../06-strings-bytes-unicode/2-summary.md)의 `decode` 를 대신 해 주는 것).

> **바이너리 모드(binary mode)** — 모드에 `'b'` 를 붙여 **`bytes` 를 그대로** 주고받는 모드.\
> 예: `open('a.png', 'rb').read()` 는 `bytes` 를 준다.

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 ① `open` 모드 격자다.** 모드 10개 × 파일이 **없을 때 / 있을 때** × (열리나 · 읽으면 · 쓰면) 을 한 표로 찍고, **두 상태에서 결과가 갈린 칸을 스크립트가 센다.**
그리고 ② **디스크 바이트 창**(`rb` 로 다시 읽기)이 텍스트 모드가 **몰래 한 일**을 보인다.

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **모드 격자** | 모드마다 **열리나 · 비우나 · 어디에 붙나** | — |
| ② ★★★ **디스크 바이트 창**(`rb` 로 다시 읽기) | 텍스트 모드가 **바꾼 바이트** · 자르기 | — |
| ③ ★★★ **환경 × 판 격자**(`env -i` + 두 인터프리터) | `encoding` 을 안 주면 **무엇이 되나** | 윈도의 코드 페이지 |
| ④ ★★ **경고 창**(`-X warn_default_encoding` + `warnings`) | `encoding` 을 **어디서 빠뜨렸나**(줄 번호) | — |
| ⑤ ★ **판 격자**(3.11 대 3.12) | `pathlib` 의 새 API | 3.13 이후 |
| ⑥ ★ **교차 갈래 창**(Go 한 블록) | 텍스트 모드가 **없는 언어**는 같은 파일을 어떻게 읽나 | — |
| ★ **부적용인 창** — 쓰기 쪽 `\n` → `os.linesep` 변환 | — | ★★★ 이 머신의 `os.linesep` 이 `'\n'` 이라 **바꿀 것이 없다** — 「재 봤더니 같았다」가 아니라 **「잴 것이 없다」**(동작 5) |
| ★ **제5의 상태** — 윈도의 쓰기 변환 | 같은 질문을 **`newline='\r\n'` 을 손으로 줘서** 물었다 — 윈도가 기본으로 할 일을 리눅스에서 흉내 낸 것 | ★ 그 창은 **「윈도의 `os.linesep` 이 정말 `'\r\n'` 인가」는 못 본다** — 그건 문서의 말이다 |
| ★ **못 잰 것** — 3.15 의 UTF-8 기본 | — | 이 머신에 3.15 가 없다 — 문서 인용만 |
| ★ **부적용** — 시간·처리량 | — | 한 번도 재지 않았다 |

★★ **②가 이 주제의 네 번째 창이다.** 텍스트 모드로 쓰고 텍스트 모드로 읽으면 **통역사가 양쪽에 있어** 바뀐 것이 안 보인다.
`\r\n` 파일을 읽어 그대로 다시 쓴 뒤 **`rb` 로 열어 봐야** 바이트가 바뀐 것이 드러난다(동작 5 의 `[3]` — `same bytes : False`).

## 이 주제가 답하려는 질문

1. ★★★ **`open` 의 모드는 들어가자마자 무엇을 하나** — 없는 파일 · 있는 파일에서 **열리나, 비우나, 쓰면 어디에 붙나.** 그리고 「없으면 만들기」를 한 번에 하는 모드는 무엇인가.
2. ★★★ **`encoding` 을 안 주면 무엇이 되나** — 로캘 · `LANG=C` · UTF-8 모드 · 판(3.11 대 3.12) · 3.15.
3. ★★ **텍스트 모드는 바이트를 어떻게 바꾸나** — `newline` 다섯 값 · 바이너리 모드 · 그리고 `Path` 가 경로 문자열을 어떻게 조립하나.

★ 첫째가 이 주제의 인출 목표다.
**「`'w'` 는 쓰기 전에 이미 비운다 · `'a'` 는 `seek` 을 무시한다 · `'x'` 는 검사와 생성이 한 번이다」 세 문장으로 모드 격자의 갈린 칸을 설명할 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ `open` 모드 격자 — 모드 10개 × 없는 파일 / 있는 파일

**언제 쓰나** — 모드 글자를 고를 때마다. 특히 「있는 파일을 고치려는데 무슨 모드로 여나」.

```text
   한 칸을 채우는 법 — 칸마다 파일을 처음 상태로 되돌린 뒤 따로 연다(칸끼리 안 샌다)

   none : 파일이 없다         abc : 파일에 b"abc" 가 있다

   open     -> 열리나? 열리면 닫은 직후 디스크 바이트 (★ 아무것도 안 썼다)
   read()   -> 열고 바로 read()        write Z -> 열고 "Z" 한 번 쓰고 닫은 뒤 디스크 바이트
```

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

그림 해설.

* ★★★ **마지막 줄 — 두 상태에서 결과가 갈린 칸 `21 / 30`.** 안 갈린 칸이 곧 **「파일이 있든 없든 똑같이 하는」** 칸이다.
  ★ **`w` 행은 세 칸 다 안 갈렸다** — 있던 `abc` 가 **연 순간 `b''`** 이고, 쓰면 `b'Z'` 로 **없던 파일과 구별이 안 된다.** `w+` 도 같다.
  스크립트가 그 둘을 뽑아 적었다 — `modes whose open() leaves an existing 'abc' file empty: w, w+`.
  ★ 문서 — *"`'w'` for writing (truncating the file if it already exists)"* · *"Modes `'w+'` and `'w+b'` open and truncate the file."*
* ★★★ **`r+` 는 안 비우고 앞에서부터 덮어쓴다** — `abc` 에 `Z` 를 쓰면 **`b'Zbc'`**. 「읽고 쓰기」라 해서 끝에 붙는 것이 아니다.
* ★★ **`a`·`a+`·`ab` 는 끝에 붙는다** — `b'abcZ'`. 그리고 **`a+` 로 열어 바로 `read()` 하면 `''`** — 위치가 **이미 끝**이다(동작 2).
* ★★ **`x`·`x+` 는 있는 파일에서 `FileExistsError`**, **`r`·`r+`·`rb` 는 없는 파일에서 `FileNotFoundError`** — 나머지 여섯은 없는 파일을 **만든다**.
* ★ **`+` 없는 쓰기 모드에서 `read()` 는 `UnsupportedOperation`**, `r`·`rb` 에서 쓰기도 `UnsupportedOperation` 이다 — 둘 다 **여는 것은 됐다.** 막히는 것은 연산이다.

**비용** — `'w'` 는 **예외가 나도 되돌리지 않는다.** 여는 순간 비웠으니, 쓰는 도중에 터지면 **빈 파일(또는 반쪽)** 이 남는다. 안전하게 바꾸려면 **다른 이름으로 쓰고 바꿔치는**(`os.replace`) 쪽이다 — 이 문서는 그것을 재지 않았다(「더 들어가면」).

> **자르기(truncate)** — 파일 길이를 0 으로 만드는 것. `'w'` 가 **여는 순간** 한다.\
> 예: `open('t.txt', 'w')` 를 열고 아무것도 안 쓰고 닫아도 `t.txt` 는 0 바이트다.

### 2. ★★ `'a'` 는 `seek` 을 무시한다 — 쓰기는 늘 끝

**언제 쓰나** — 로그처럼 **덧붙이기만** 하는 파일. 그리고 `a+` 로 열어 앞부분을 읽은 뒤 쓸 때.

```text
   a+ 로 연 "abc"
      tell() 3 ─ seek(0) ─▶ tell() 0 ─ read() ─▶ 'abc'
                            seek(0) ─▶ tell() 0 ─ write("Z") ─▶ ★ 끝에 붙는다 ─▶ tell() 4
   r+ 로 연 "abcZ"
      seek(0, 2) write("!") ─▶ 끝에 "!"   ·   seek(1) write("-") ─▶ ★ 1 자리에 덮어쓴다
```

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

그림 해설.

* ★★ **`[1]` 연 직후 `tell()` 이 `3`** — `a+` 는 **끝에서 시작**한다. 그래서 동작 1 의 `a+` 에서 `read()` 가 `''` 였다.
* ★★ **`[3]`·`[4]`** — `seek(0)` 으로 **위치가 0 이 됐는데**(`tell() after seek(0) : 0`) `write("Z")` 는 **끝에 붙고** `tell()` 이 `4` 가 됐다. `[5]` 가 `'abcZ'`.
  ★ 문서 — *"which on some Unix systems, means that all writes append to the end of the file regardless of the current seek position"*. **「some Unix systems」** 라는 한정이 붙어 있다 — 이 머신(Linux)에서 그랬다는 것이 관찰이다.
* ★ **`[6]`** — `r+` 는 `seek` 이 **듣는다.** 끝으로 가서 `!`, 1 자리로 가서 `-` 를 쓰니 `'a-cZ!'` — **덮어쓰기**다(글자 수가 안 늘었다).

**비용** — `a` 로는 **파일 중간을 못 고친다.** 중간을 고치려면 `r+` 인데, 그건 **덮어쓰기**라 길이가 바뀌는 수정에는 안 맞는다.

### 3. ★★ `'x'` — 「없으면 만들기」를 한 번에 (26번의 실무 자리)

**언제 쓰나** — 「**이미 있으면 건드리지 말고, 없을 때만 새로 만들어라**」 — 잠금 파일·결과 파일·「두 번 돌면 안 되는 작업」의 표시.

[26번](../26-eafp-vs-lbyl/2-summary.md) 동작 2 는 **읽기**에서 「검사 뒤의 틈」을 보였다(`exists()` 뒤에 지워지면 `FileNotFoundError`).
여기는 **만들기**의 틈이다 — 두 작업자가 **같은 틈**에 들어오는 순서를 코드로 고정했다(스레드 없이 — 26번과 같은 방법).

```text
   exists() 뒤에 open('w')                         open('x')
   A: exists() -> False                            A: open('x') -> 만들었다
   B: exists() -> False  ★ 둘 다 「없다」를 봤다       B: open('x') -> FileExistsError
   A: open('w') 쓰기 "from A"                       ★ 검사와 만들기가 한 번의 open 안에 있다
   B: open('w') 쓰기 "from B"  ★ A 의 것을 비우고 덮었다
```

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

그림 해설.

* ★★★ **`[1]` — 둘 다 `exists(): False` 를 보고 둘 다 `'w'` 로 열었다.** 남은 것은 **`'from B'`** — A 가 쓴 것은 **B 의 `'w'` 가 여는 순간 비웠다**(동작 1). 에러가 **없다.**
* ★★★ **`[2]` — `'x'` 는 B 에게 `FileExistsError EEXIST`** 를 준다. 남은 것은 **`'from A'`**.
  **검사(있나?)와 만들기가 `open` 한 번 안에** 들어 있어서 틈이 없다 — 26번의 EAFP 처방(「일단 하고 예외를 받는다」)이 **모드 글자 하나**로 들어온 것이다.
* ★ `errno` 는 **숫자가 아니라 이름**(`errno.errorcode`)으로 찍었다 — 숫자는 플랫폼마다 다를 수 있다.

**비용** — `'x'` 는 **있는 파일을 못 고친다.** 「없으면 만들고 있으면 이어 쓰기」는 `'a'` 의 일이다.

> **경쟁 조건(race condition)** — 결과가 **두 작업의 순서**에 달린 것. 검사와 실행 사이에 틈이 있으면 생긴다.\
> 예: 둘 다 「없다」를 보고 둘 다 만들면 나중 것이 이긴다([26번](../26-eafp-vs-lbyl/2-summary.md)).

### 4. ★★★ `encoding` 을 안 주면 — 환경 × 판 격자

**언제 쓰나** — `open(path)` 처럼 **`encoding` 을 빼고** 쓸 때. 그리고 그 코드가 **다른 환경**(서버·컨테이너·CI)에서 돌 때.

```text
   open("x.txt", "w")   # encoding 없음
          │
          ▼
   UTF-8 모드가 켜져 있나? ──예──▶ utf-8
          │ 아니오
          ▼
   로캘의 인코딩 (LC_CTYPE)  ──▶ ko_KR.UTF-8 이면 UTF-8 · 순수 C 이면 ANSI_X3.4-1968(=ASCII)

   UTF-8 모드가 켜지는 자리 — PYTHONUTF8=1 · -X utf8 · ★ 시작할 때 LC_CTYPE 이 C/POSIX 이면 저절로
   끄는 자리 — PYTHONUTF8=0 (또는 -X utf8=0)
```

같은 탐침(한 줄, ASCII 만 찍는다)을 **환경 여덟 가지 × 인터프리터 둘**에 던진다.
★ **`env -i` 로 환경을 비우고 행마다 로캘 환경 전체를 적었다** — 이 머신의 `LANG` 이 섞이지 않게.

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

그림 해설.

* ★★★ **`LANG=C` 행은 한글 쓰기가 `ok` 다** — `utf8_mode` 가 **`1`** 이다. 「`LANG=C` 로 띄우면 한글이 깨진다」는 **이 판에서는 틀렸다.**
  두 장치가 겹쳐서다 — **로캘 강제 변환**(PEP 538: `C` 를 `C.UTF-8` 같은 UTF-8 로캘로 바꾼다 — 그래서 `getencoding` 이 `UTF-8`)과 **UTF-8 모드 자동 켜짐**(PEP 540).
  ★ 문서 — *"The Python UTF-8 Mode is enabled if the LC_CTYPE locale is `C` or `POSIX` at Python startup"*.
* ★★★ **`LC_ALL=C` 행은 `getencoding` 이 `ANSI_X3.4-1968`(ASCII)인데도 쓰기가 `ok`** 다 — 로캘 강제 변환은 안 됐지만(`LC_ALL` 이 이긴다) **UTF-8 모드가 켜져서** `f.encoding` 이 `utf-8` 이다.
  ★ `getencoding` 은 **UTF-8 모드를 무시한다**(문서 — *"except this function ignores the Python UTF-8 Mode"*). 그래서 **`getencoding` 과 `f.encoding` 이 다른 행**이 생긴다.
* ★★★ **깨지는 것은 `PYTHONUTF8=0` 을 더한 두 행뿐** — `UnicodeEncodeError(ascii)` · 읽기는 `UnicodeDecodeError(ascii)`. 스크립트의 집계 — **`2 / 8`**.
  **UTF-8 모드를 명시적으로 꺼야** ASCII 로 떨어진다.
* ★★ **`-X utf8` 이 `PYTHONUTF8=0` 을 이겼다** — `LC_ALL=C PYTHONUTF8=0 -X utf8` 행이 `ok`(이 격자의 관찰).
* ★★ **3.11 과 3.12 는 한 칸도 안 갈렸다** — `rows where 3.11 and 3.12 differ … : 0 / 8`. 이 격자에서 **판 경계는 없다.** 다음 경계는 **3.15**(PEP 686 — UTF-8 모드가 기본) — ★ **문서의 말이다**(못 잰 것).
* ★★ **마지막 행 — `-X warn_default_encoding`** 이 `EncodingWarning` 을 **세 번** 냈다 — 탐침 파일의 **12행**(`open("plain.txt", "w")`) · **20행**(`open("utf8.txt")`) · **24행**(`locale.getpreferredencoding(False)`).
  ★ 셋째는 `open` 이 아니다 — **`getpreferredencoding` 자체도 경고 대상**이다(UTF-8 모드에 휘둘리는 함수라서). 문서의 권고가 **`locale.getencoding()` 을 쓰라**는 이유다.
  ★ 줄 번호는 **파일의 줄**이다 — 위 소스 펜스는 첫 줄에 배너(`# e48_enc_probe.py`)가 하나 더 있어 **펜스 안에서는 한 줄씩 밀린다.**

**비용** — `encoding` 을 빼면 **코드가 아니라 환경이 인코딩을 고른다.** 이 머신에서 두 행을 깨려면 환경변수를 **둘**(`LC_ALL=C PYTHONUTF8=0`) 줘야 했지만, 윈도의 로캘 인코딩은 대개 UTF-8 이 아니다 — 문서가 그 예를 직접 든다(*"This causes bugs because the locale encoding is not UTF-8 for most Windows users"*). **`encoding="utf-8"` 을 늘 적는다.**

> **UTF-8 모드(UTF-8 Mode)** — 로캘을 무시하고 파일·표준 입출력·파일 이름의 기본 인코딩을 UTF-8 로 두는 인터프리터 설정(3.7+, PEP 540).\
> 예: `PYTHONUTF8=1 python3 …` · `python3 -X utf8 …` · 그리고 로캘이 `C` 면 저절로 켜진다.

> **로캘 강제 변환(locale coercion)** — 로캘이 `C` 일 때 인터프리터가 시작하면서 `C.UTF-8` 같은 UTF-8 로캘로 **바꿔 버리는** 것(3.7+, PEP 538). `LC_ALL` 이 정해져 있으면 안 한다.\
> 예: `LANG=C` 행의 `getencoding` 이 `UTF-8` 인 이유.

### 5. ★★★ `newline` — 리눅스에서도 `\r\n` 은 `\n` 이 된다

**언제 쓰나** — 윈도·옛 맥에서 온 파일(`\r\n`·`\r`)을 읽을 때. CSV 를 읽고 쓸 때.

```text
   디스크 바이트   o n e \r \n t w o \r t h r e e \n f o u r
                         ~~~~~        ~~            ~~
   newline=None  (기본)   세 종류를 전부 줄 끝으로 알아보고 ★ 전부 \n 으로 바꿔 건넨다
   newline=''             세 종류를 전부 줄 끝으로 알아보되 ★ 그대로 건넨다
   newline='\n'           \n 만 줄 끝 · 그대로        newline='\r\n'  \r\n 만 · 그대로
   newline='\r'           \r 만 줄 끝 · 그대로
```

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

그림 해설.

* ★★★ **`newline=None` 은 리눅스에서도 `\r\n`·`\r` 을 `\n` 으로 바꿨다** — `['one\n', 'two\n', 'three\n', 'four']`. 「줄바꿈 변환은 윈도에서만」은 **쓰기 쪽 이야기**다.
  ★ 문서 — *"if newline is `None`, universal newlines mode is enabled. Lines in the input can end in `'\n'`, `'\r'`, or `'\r\n'`, and these are translated into `'\n'`"* · 그리고 *"all the processing is done by Python itself, and is therefore platform-independent"*.
* ★★ **`newline=''` 은 줄은 똑같이 끊고 끝은 안 바꾼다** — `['one\r\n', 'two\r', 'three\n', 'four']`. `csv` 모듈이 이 값을 요구하는 이유다(「더 들어가면」).
* ★★ **`f.newlines`** — 유니버설 모드(`None`·`''`)에서만 **만난 줄 끝 종류**를 튜플로 준다. 나머지 셋은 `None`.
* ★ **`'rb'` 는 아무것도 안 바꾼다** — 줄은 **`\n` 에서만** 끊는다(`b'two\rthree\n'` 이 한 줄). `Path.read_text()` 는 `open` 기본값과 같다(`\n` 으로 바뀜).
* ★★★ **`[2]` 쓰기 — `None`·`''`·`'\n'` 세 칸이 전부 `b'a\nb'`** 다. `None` 은 `\n` 을 **`os.linesep` 으로** 바꾸는데 이 머신의 `os.linesep` 이 `'\n'`(`[0]`)이라 **바꿀 것이 없다.**
  ★ **이것은 「재 봤더니 같았다」가 아니라 「잴 것이 없다」**(부적용)다 — 창 표의 그 칸. 윈도라면 `None` 칸이 달라질 **것이라는 말은 문서의 말**이다.
  ★ **제5의 상태** — 같은 질문을 **`newline='\r\n'` 을 손으로 줘서** 물었다 → `b'a\r\nb'`. 「윈도의 기본 쓰기」가 **바이트로 무엇이 되나**는 이 칸이 답한다.
* ★★★ **`[3]` 왕복 — `same bytes : False`** — 기본값으로 읽고 기본값으로 쓰면 `\r\n`·`\r` 이 **`\n` 으로 굳는다.** 텍스트로만 보면 안 보인다 — **`rb` 로 다시 읽어야**(네 번째 창) 보인다.

**교차 갈래 — 텍스트 모드가 없는 언어.** 같은 바이트를 Go 로 읽었다. Go 는 파일을 **바이트로만** 읽는다(Go 갈래 [README](../../../go/syntax/README.md) — 파일 I/O 주제는 그 목록에 없다).

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

* ★★ **`os.ReadFile` 은 바이트 그대로** — `\r\n` 이 살아 있다. `strings.Split(s, "\n")` 은 **`"one\r"`** 를 남긴다 — 파이썬의 `newline='\n'` 칸과 같은 모양이다.
* ★ **`bufio.Scanner` 는 줄 끝의 `\r\n` 은 벗기고 외톨이 `\r` 은 안 벗긴다** — `"two\rthree"` 가 한 줄. 파이썬의 기본(`None`)은 **외톨이 `\r` 도 줄 끝**으로 봤다. **같은 파일의 줄 수가 3 대 4** 로 갈린다.

**비용** — 기본값은 **읽을 때 정보를 잃는다**(어느 줄 끝이었는지). 바이트를 지켜야 하면 `newline=''`(줄 끝 보존) 또는 `'rb'`.

> **유니버설 개행(universal newlines)** — `\n`·`\r`·`\r\n` 을 전부 줄 끝으로 알아보는 읽기 방식. `newline=None`·`''` 에서 켜진다.\
> 예: `newline=None` 은 알아본 뒤 전부 `\n` 으로 바꾸고, `newline=''` 는 안 바꾼다.

### 6. ★★ 텍스트 대 바이너리 — 섞으면 `TypeError`, `tell()` 은 글자 수가 아니다

**언제 쓰나** — 한 파일을 두 모드로 다룰 때. 텍스트 파일에서 `seek`/`tell` 로 자리를 옮길 때.

```text
   "한글A"  ─ encode utf-8 ─▶  ed 95 9c | ea b8 80 | 41      (7 바이트)
            텍스트로 읽으면 len 3          바이너리로 읽으면 len 7

   read(1) 뒤 tell()  -> 3   ★ 글자 1개를 읽었는데 3 — 바이트 쪽 자리다
   seek(1)            -> "한" 의 둘째 바이트 한가운데 ─▶ read() 가 UnicodeDecodeError
```

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

그림 해설.

* ★★ **`[1]` `write()` 는 `3`** — 텍스트 모드의 `write` 는 **글자 수**를 돌려준다. 디스크에는 **7 바이트**(`[2]`).
* ★★★ **`[3]` 두 모드는 서로의 타입을 거절한다** — 바이너리에 `str` 을 쓰면 `a bytes-like object is required, not 'str'`, 텍스트에 `bytes` 를 쓰면 `write() argument must be str, not bytes`. 그리고 **`'rb'` 에 `encoding=` 을 주면 `ValueError`** — 바이너리엔 통역사가 없다.
* ★★★ **`[4]` `tell()` 이 `3`** — 한 글자를 읽었는데 3. 텍스트 모드의 `tell()` 은 **글자 수가 아니다.** `seek(1)` 로 **글자 한가운데**에 서면 `read()` 가 **`UnicodeDecodeError`**.
  ★ 텍스트 모드는 **현재 위치 기준 이동(`seek(1, SEEK_CUR)`)을 거절한다**(`can't do nonzero cur-relative seeks`) — 바이너리는 된다(`1`).
  ★ `tell()` 이 돌려주는 숫자의 **뜻**은 문서가 *"opaque number"* 로만 약속한다 — **바이트 자리와 같았다는 것은 이 판의 관찰**이다(「구현 세부사항」).

**비용** — 텍스트 모드의 자리 이동은 **`tell()` 로 받은 값으로만** 돌아가는 것이 안전하다.

파일 객체를 **도는 것**은 [16번](../16-iterator-protocol/2-summary.md)이 정본이다(`iter(f) is f` · 두 번째 `for` 는 빈다 · `seek(0)` 이 되감기). 여기서는 같은 사실을 파일로 한 번 더 찍었다 — `with` 를 나온 뒤는 **닫힌 파일**이다([28번](../28-context-managers-and-with/2-summary.md)).

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

* ★ **`[3]` 둘째 `for` 는 `[]`**, `[4]` 끝에서 `readline()` 은 **`''`** — 에러가 아니라 빈 것이다. `[5]` `seek(0)` 뒤에는 다시 나온다.
* ★ **`[7]` 닫힌 파일의 `read()` 는 `ValueError`** — `I/O operation on closed file.`
* ★ 줄마다 **`'\n'` 이 붙어 온다**(`[2]`) — 떼려면 `rstrip("\n")`([15번](../15-generator-expressions-lazy-eval/2-summary.md)의 「파일을 그냥 돌기」가 이 모양이다).

### 7. ★★★ `Path` 조작 — 절대 경로가 이긴다

**언제 쓰나** — 경로를 **문자열 `+` 대신** 조립할 때. 확장자·이름을 바꿀 때.

```text
   Path('a') / 'b' / 'c.txt'   ─▶  a/b/c.txt
   Path('a') / '/b'            ─▶  /b        ★ 오른쪽이 절대 경로면 왼쪽을 버린다
   'a' + '/' + '/b'            ─▶  a//b      (문자열은 그냥 붙인다)

   data/archive.tar.gz
   ├ name      archive.tar.gz        ├ suffix    .gz        (★ 마지막 하나)
   ├ stem      archive.tar           └ suffixes  ['.tar', '.gz']
   └ with_suffix('.zip') ─▶ data/archive.tar.zip   ★ .gz 하나만 바뀐다
```

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

그림 해설.

* ★★★ **`Path('a') / '/b'` 는 `'/b'`** — 오른쪽이 **절대 경로면 왼쪽을 통째로 버린다.** `Path('a', '/b', 'c')` 도 `'/b/c'`.
  ★ 문서 — *"If a segment is an absolute path, all previous segments are ignored (like `os.path.join`)"*.
  **사용자 입력을 `/` 로 붙이면** 입력이 `/` 로 시작하는 순간 **기준 디렉토리를 벗어난다** — 에러가 없다.
* ★★ **`Path` 는 `//`·`.`·끝의 `/` 를 정리하지만 `..` 은 안 건드린다** — `'a/b/c'` 대 `'a/../b'`. `..` 은 **심볼릭 링크가 끼면** 뜻이 바뀌기 때문이다.
  ★ `[3]` 이 그 증거다 — `link` 가 `x/inner` 를 가리킬 때 **글자로 줄이면**(`os.path.normpath('link/..')`) `'.'` 인데, **실제로 따라가면**(`resolve()`) `'x'` 다.
* ★★ **`suffix` 는 마지막 하나뿐** — `with_suffix('.zip')` 는 `archive.tar.zip`. `.tar.gz` 를 통째로 바꾸려면 `suffixes` 를 보고 직접 한다. **점 없는 `'zip'` 은 `ValueError`**.
* ★ **`resolve()` 는 절대 경로를 준다**(`is_absolute()` 가 `True`) — 이 문서는 그것을 **작업 디렉토리 기준으로 되돌려** 찍었다. 없는 경로(`x/../y`)도 에러 없이 푼다.
* ★ **`mkdir`** — 부모가 없으면 `FileNotFoundError`, 두 번 만들면 `FileExistsError`, **`parents=True, exist_ok=True`** 라야 둘 다 조용하다.
* ★ **`iterdir()`·`glob()` 은 `sorted` 로 찍었다** — 문서가 *"The children are yielded in arbitrary order"* 라고 적는다. 날것의 순서는 싣지 않는다.

**비용** — `Path` 는 **글자를 조립할 뿐 파일 시스템을 안 본다**(`resolve`·`exists`·`mkdir` 같은 메서드만 본다). `Path('a') / '/b'` 가 위험한 이유가 그것이다 — 조립 단계에서는 아무도 안 말린다.

### 8. ★ 판 격자 — `pathlib` 의 3.12 새 API

**언제 쓰나** — 3.11 에서도 도는 코드에 `pathlib` 새 기능을 쓸 때.

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

* ★★ **`Path.walk`·`with_segments`·`is_junction` 은 3.11 에 없다**(`False`) — 대조로 찍은 `read_text` 는 둘 다 `True`.
* ★★ **`relative_to(…, walk_up=True)`** — 3.12 는 `../b`, 3.11 은 **`TypeError … unexpected keyword argument 'walk_up'`**.
* ★ **같은 `ValueError` 의 문구가 두 판에서 다르다** — 3.11 은 `… OR one path is relative and the other is absolute.` 가 더 붙는다. **문구는 구현이다** — 타입(`ValueError`)만 근거로 쓴다.

## 문법 — 형태와 규칙

**형태**

```text
open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, ...)

mode = 기본 글자 하나  r | w | a | x          (+ 를 붙이면 읽기·쓰기 겸용)
     + 형식 글자 하나  t(기본) | b            예: 'r'  'w+'  'ab'  'x+b'
encoding = 텍스트 모드에서만 — 'utf-8' 을 늘 적는다 · 'locale' 은 로캘 인코딩(3.10+)
newline  = None | '' | '\n' | '\r' | '\r\n'   — 텍스트 모드에서만

Path('base') / 'sub' / 'f.txt'       # 오른쪽이 절대 경로면 왼쪽을 버린다
p.read_text(encoding='utf-8') · p.write_text(s, encoding='utf-8')
p.with_suffix('.bak') · p.with_name('x') · p.stem · p.suffixes · p.resolve()
p.mkdir(parents=True, exist_ok=True)
```

규칙 열.

1. ★★★ **`'w'`·`'w+'` 는 여는 순간 자른다** — 모드 격자에서 **있는 파일과 없는 파일이 한 칸도 안 갈린 행**이 이 둘이다.
2. ★★★ **`'x'` 는 있으면 `FileExistsError`** — 검사와 생성이 **한 번**이다(`exists()` + `'w'` 는 두 번이라 틈이 있다).
3. ★★ **`'a'` 계열은 `seek` 을 무시하고 끝에 쓴다**(이 머신에서) · **`'r+'` 는 자르지 않고 그 자리에 덮어쓴다.**
4. ★★★ **`encoding` 을 늘 적는다** — 안 적으면 UTF-8 모드 여부와 로캘이 고른다. `LANG=C` 는 **UTF-8 모드를 켠다**(PEP 540), 끄려면 `PYTHONUTF8=0`.
5. ★★★ **`newline=None`(기본)은 읽을 때 `\r\n`·`\r` 을 `\n` 으로 바꾼다 — 리눅스에서도.** 보존하려면 `newline=''` 또는 `'rb'`.
6. ★★ **텍스트와 바이너리는 서로의 타입을 거절한다** · 텍스트의 `tell()` 은 글자 수가 아니다.
7. ★★ **`Path` 는 `..` 을 글자로 안 줄인다** — `resolve()` 가 파일 시스템을 보고 푼다.

## 어디서 틀리나

### (1) ★★★ 있는 파일을 고치려고 `'w'` 로 연다

**여는 순간 비운다**(동작 1). 읽고 나서 고치려던 내용이 **이미 없다.** 쓰는 도중 예외가 나면 **빈 파일**이 남는다.

### (2) ★★★ `exists()` 로 확인하고 `'w'` 로 만든다

**틈이 있다**(동작 3) — 둘 다 「없다」를 보면 **나중 것이 앞의 것을 비우고 덮는다.** 에러가 없다. `'x'` 로 연다.

### (3) ★★★ `encoding` 을 빼고 「내 머신에서 됐으니」 믿는다

**환경이 고른다**(동작 4). 이 머신은 `LANG=C` 에서도 됐지만 그건 **UTF-8 모드가 저절로 켜져서**다. `PYTHONUTF8=0` 인 환경·윈도에서는 `UnicodeEncodeError`.

### (4) ★★★ 「`LANG=C` 면 한글이 깨진다」로 외운다

**3.7 이후로는 아니다**(동작 4) — `C` 로캘에서 UTF-8 모드가 켜진다. 깨지는 것은 **UTF-8 모드를 끈** 경우다. 그리고 그 환경을 재현하려면 `LC_ALL=C PYTHONUTF8=0` 까지 줘야 했다.

### (5) ★★ `locale.getencoding()` 으로 `open` 의 기본값을 알아낸다

**UTF-8 모드를 무시한다**(동작 4 — `LC_ALL=C` 행에서 `ANSI_X3.4-1968` 인데 `f.encoding` 은 `utf-8`). 열린 파일의 **`f.encoding`** 을 본다.

### (6) ★★★ 「줄바꿈 변환은 윈도에서만」이라 믿고 기본값으로 읽어 다시 쓴다

**읽기 변환은 모든 플랫폼**이다(동작 5) — `\r\n` 파일이 **`\n` 으로 굳는다**(`same bytes : False`).

### (7) ★★ 텍스트 파일에서 `seek(n)` 으로 n 번째 글자로 간다

`tell()`·`seek()` 의 숫자는 **글자 수가 아니다**(동작 6) — 한가운데 서면 `UnicodeDecodeError`.

### (8) ★★★ 사용자 입력을 `base / name` 으로 붙인다

`name` 이 `/` 로 시작하면 **`base` 가 사라진다**(동작 7). 에러가 없다.

### (9) ★ `with_suffix` 로 `.tar.gz` 를 바꾼다

**마지막 `.gz` 만** 바뀐다(`archive.tar.zip`).

### (10) ★ `iterdir()` 결과를 그대로 늘어놓는다

순서는 **임의**다(문서). `sorted` 로.

### (11) ★ 3.11 코드에서 `relative_to(walk_up=True)`·`Path.walk` 를 쓴다

**`TypeError` · 속성 없음**(동작 8).

## 구현 세부사항 대 언어 보장

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **라이브러리 보장** | `open`·`io`·`os`·`pathlib` 문서가 정한 것 | 문서 문장을 열어서 인용 |
| **CPython 구현** | 예외 문구 · `tell()` 숫자의 뜻 | 실행 |
| **이 판(3.12.3 · 3.11.15)·이 머신의 관찰** | 이 판·이 로캘에서 그랬을 뿐 | 출력 |
| ★ **못 잰 것** | 3.15 의 UTF-8 기본 · 윈도의 `os.linesep` | 판·플랫폼이 없다 |
| ★ **부적용** | 쓰기 쪽 `\n` → `os.linesep`(이 머신은 `'\n'`) · 시간 | 잴 것이 없다 · 재지 않았다 |

### 라이브러리 보장

| 사실 | 근거 |
|---|---|
| `'w'` 는 자른다 · `'x'` 는 있으면 실패 · `'w+'` 는 자르고 `'r+'` 는 안 자른다 | `open` 모드 표와 그 아래 문장 |
| `'a'` 가 `seek` 과 상관없이 끝에 쓰는 것은 **"some Unix systems"** | `open` — ★ 보장이 아니라 **플랫폼 한정 서술** |
| `newline=None` 은 읽을 때 세 줄 끝을 `\n` 으로 · 쓸 때 `\n` 을 `os.linesep` 으로 | `open`·`TextIOWrapper` 의 `newline` 절 |
| 텍스트 처리는 파이썬이 하므로 **플랫폼과 무관** | `open` 의 note |
| UTF-8 모드는 `LC_CTYPE` 이 `C`/`POSIX` 면 켜지고, 그때 `open` 기본은 UTF-8 | `os` — Python UTF-8 Mode |
| `locale.getencoding` 은 UTF-8 모드를 무시한다 | `locale` |
| `-X warn_default_encoding` 은 기본 인코딩을 쓰는 자리에서 `EncodingWarning`(3.10) | `io` — Opt-in EncodingWarning |
| 경로 조립에서 **절대 경로 조각이 앞을 버린다** · `iterdir` 은 **임의 순서** | `pathlib` |
| 3.15 부터 UTF-8 이 기본 | PEP 686 · What's New 3.15 — ★ 이 머신에서 못 잰다 |

★ **문서끼리 어긋나는 자리가 하나 있다** — 3.12 `open` 절은 *"if encoding is not specified … `locale.getencoding` is called"* 라고 적는데, `locale.getencoding` 은 **UTF-8 모드를 무시한다**고 `locale` 절이 적고, `os` 의 UTF-8 모드 절은 **그때 `open` 이 UTF-8 을 쓴다**고 적는다.
**실행은 뒤쪽 편이었다** — `LC_ALL=C` 행의 `getencoding` 은 `ANSI_X3.4-1968`, `f.encoding` 은 `utf-8`(동작 4). `TextIOWrapper` 절의 *"The default encoding is now `locale.getpreferredencoding(False)`"*(3.3) 이 관찰과 맞는다. 이 문서는 **실행과 `os` 절을 기준**으로 삼았다.

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| 예외 **문구** 전부 — `can't do nonzero cur-relative seeks` · `binary mode doesn't take an encoding argument` · `Invalid suffix 'zip'` · `relative_to` 의 문구(3.11 과 3.12 가 다르다) | 실행 |
| 텍스트 모드 `tell()` 이 **바이트 자리와 같은 숫자**(`3`) — 문서는 *"opaque number"* 라고만 한다 | 실행(동작 6) |
| `f.newlines` 튜플의 **원소 순서** | 실행(동작 5) |

### 이 판(3.12.3)의 관찰

- **`'a'` 가 `seek(0)` 뒤에도 끝에 쓴 것** — Linux 에서 그랬다(문서는 「some Unix systems」).
- **환경 격자 여덟 행이 3.11 과 3.12 에서 한 칸도 안 갈린 것**(`0 / 8`).
- **이 머신의 기본 로캘이 `ko_KR.UTF-8` 이고 `os.linesep` 이 `'\n'` 인 것** — 그래서 쓰기 변환 칸이 부적용이다.
- **`[Errno 17]`·`[Errno 2]`** — 문구 안의 숫자는 플랫폼의 것이다. 본문은 `errno` **이름**(`EEXIST`)을 근거로 썼다.

### 그래서 이렇게 적으면 틀린다

* ✗ 「`LANG=C` 로 띄우면 한글 쓰기가 `UnicodeEncodeError`」\
  ○ **UTF-8 모드가 저절로 켜져 `ok`** 다(3.11 · 3.12). 깨지려면 `PYTHONUTF8=0` 까지 줘야 했다.
* ✗ 「텍스트 모드의 줄바꿈 변환은 윈도에서만 일어난다」\
  ○ **읽기 변환은 리눅스에서도 일어났다**(`\r\n` → `\n`). 윈도에서만 달라지는 것은 **쓰기** 쪽(`os.linesep`)이고, 그건 이 머신에서 **잴 것이 없었다.**
* ✗ 「`open` 의 기본 인코딩은 `locale.getencoding()` 이다」\
  ○ **UTF-8 모드에서는 아니다** — 둘이 다른 행이 격자에 있다.
* ✗ 「`'a'` 는 어떤 시스템에서도 `seek` 을 무시한다」\
  ○ 문서는 **「some Unix systems」** 라고 한정한다 — 이 머신의 관찰이다.
* ✗ 「바이너리 모드가 빠르다」\
  ○ **시간은 재지 않았다.** 잰 것은 **바이트가 바뀌었나**다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 읽기만 | `'r'` + `encoding='utf-8'` | 없으면 `FileNotFoundError` — 조용히 만들지 않는다 |
| 새로 쓰기(있으면 갈아엎어도 된다) | `'w'` | 여는 순간 자른다 |
| 이미 있으면 **안 된다** | `'x'` | 검사와 생성이 한 번 — 경쟁 조건이 없다 |
| 로그처럼 덧붙이기 | `'a'` | `seek` 과 상관없이 끝에 쓴다 |
| 그 자리 덮어쓰기(길이 불변) | `'r+'` | 자르지 않는다 |
| 이미지·압축·해시 입력 | `'rb'`·`'wb'` | 변환이 없다 |
| 줄 끝을 보존 · CSV | `newline=''` | 끊기는 하되 안 바꾼다 |
| 경로 조립 | `Path` 와 `/` | 단, **입력이 절대 경로면 기준을 버린다** — 입력은 따로 검사 |
| 짧은 파일 통째로 | `Path.read_text`/`write_text`(`encoding=` 과 함께) | `with open` 을 대신 써 준다 |

## 핵심 문장

1. **`'w'` 는 쓰기 전에 이미 비운다** — 모드 격자에서 두 상태가 갈린 칸 **21 / 30**, `w`·`w+` 행만 한 칸도 안 갈렸다.
2. **`'x'` 는 「없으면 만들기」를 한 번에 한다** — `exists()` + `'w'` 는 둘 다 「없다」를 보고 나중 것이 이긴다.
3. **`encoding` 을 안 주면 환경이 고른다** — `LANG=C` 는 UTF-8 모드를 켜서 한글이 되고, `PYTHONUTF8=0` 까지 줘야 깨졌다(**2 / 8**, 3.11 과 3.12 차이 **0 / 8**). 3.15 는 UTF-8 기본(문서).
4. **`newline=None` 은 리눅스에서도 `\r\n` 을 `\n` 으로 바꾼다** — 쓰기 쪽 `os.linesep` 변환은 이 머신에서 잴 것이 없다.
5. **`Path('a') / '/b'` 는 `/b`** — 절대 경로 조각이 앞을 버린다. `..` 은 글자로 줄이지 않는다.

## 관련 자료

* 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **48번**
* 선행: [06-strings-bytes-unicode](../06-strings-bytes-unicode/2-summary.md) — ★★★ **경계**: `encode`/`decode`·오류 처리기·서로게이트는 그쪽이 정본. 여기는 **`open` 이 그 일을 언제 어떤 인코딩으로 대신 하나**부터(06번 723행이 넘긴 자리).
* 선행: [28-context-managers-and-with](../28-context-managers-and-with/2-summary.md) — `with` 계약과 닫기는 그쪽. 여기는 **`with open(...)` 의 인자**(모드·`encoding`·`newline`)다.
* 선행: [26-eafp-vs-lbyl](../26-eafp-vs-lbyl/2-summary.md) — ★ **경계**: 읽기의 경쟁 조건(`exists()` 뒤 삭제)은 그쪽. 여기는 **만들기의 경쟁 조건과 `'x'`**(동작 3).
* 함께 보는 곳: [16-iterator-protocol](../16-iterator-protocol/2-summary.md) — 파일 객체가 자기 이터레이터(`iter(f) is f`)인 것은 그쪽이 정본. [15-generator-expressions-lazy-eval](../15-generator-expressions-lazy-eval/2-summary.md) — 파일을 그냥 돌기.
* 다른 갈래: Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md)) — 파일 I/O 주제가 **그 목록에 없다**. 동작 5 의 Go 블록은 이 문서가 직접 던진 것이다.
* 공식 문서: [`open()`](https://docs.python.org/3.12/library/functions.html#open) · [`io`](https://docs.python.org/3.12/library/io.html) · [Python UTF-8 Mode](https://docs.python.org/3.12/library/os.html#utf8-mode) · [`pathlib`](https://docs.python.org/3.12/library/pathlib.html) · [PEP 538](https://peps.python.org/pep-0538/) · [PEP 540](https://peps.python.org/pep-0540/) · [PEP 597](https://peps.python.org/pep-0597/) · [PEP 686](https://peps.python.org/pep-0686/)

## 용어 풀이

* **모드(mode)**: `open` 의 둘째 인자. 기본 글자(`r`·`w`·`a`·`x`) + 선택 `+` + 형식(`t`·`b`).\
  예: `'r+b'` 는 읽기·쓰기 겸용 바이너리, 자르지 않는다.
* **자르기(truncate)**: 파일 길이를 0 으로 만드는 것. `'w'`·`'w+'` 가 여는 순간 한다.\
  예: 열고 닫기만 해도 0 바이트.
* **배타적 생성(exclusive creation)**: 파일이 **없을 때만** 만들고 있으면 실패하는 것. 모드 `'x'`.\
  예: 둘째 작업자는 `FileExistsError`.
* **텍스트 모드 / 바이너리 모드**: 인코딩으로 풀어 `str` 을 주고받는가 / `bytes` 를 그대로 주고받는가.\
  예: `'r'` 은 `str`, `'rb'` 는 `bytes`.
* **로캘 인코딩(locale encoding)**: 운영체제 로캘(`LC_CTYPE`)이 정한 문자 인코딩.\
  예: `ko_KR.UTF-8` 이면 UTF-8, 순수 `C` 면 ASCII(`ANSI_X3.4-1968`).
* **UTF-8 모드(UTF-8 Mode)**: 로캘을 무시하고 기본 인코딩을 UTF-8 로 두는 설정(3.7+).\
  예: `PYTHONUTF8=1`·`-X utf8`, 로캘이 `C` 면 저절로 켜진다.
* **로캘 강제 변환(locale coercion)**: `C` 로캘을 시작 때 UTF-8 로캘로 바꾸는 것(PEP 538).\
  예: `LANG=C` 에서 `getencoding()` 이 `UTF-8`.
* **`EncodingWarning`**: 기본 인코딩을 쓰는 자리에서 나는 경고. `-X warn_default_encoding` 으로 켠다(3.10+).\
  예: `open(path)` 한 줄마다 한 번.
* **유니버설 개행(universal newlines)**: `\n`·`\r`·`\r\n` 을 전부 줄 끝으로 알아보는 읽기. `newline=None` 은 `\n` 으로 바꾸고 `''` 는 그대로 둔다.\
  예: 리눅스에서도 `\r\n` 파일이 `\n` 으로 읽힌다.
* **`os.linesep`**: 이 플랫폼의 줄 끝 문자열. `newline=None` 쓰기가 `\n` 을 이것으로 바꾼다.\
  예: 이 머신은 `'\n'`.
* **`Path`**: 경로를 객체로 다루는 `pathlib` 의 클래스. `/` 로 조립한다.\
  예: `Path('a') / 'b'` 는 `a/b`, `Path('a') / '/b'` 는 `/b`.
* **`resolve()`**: 심볼릭 링크와 `..` 을 **파일 시스템을 보고** 풀어 절대 경로를 주는 메서드.\
  예: `link/..` 이 `x` 가 된다(글자로 줄이면 `.`).

## 더 들어가면

* ★ **안전한 교체** — `'w'` 가 여는 순간 비우므로, 설정 파일 같은 것은 **임시 이름으로 다 쓴 뒤 `os.replace(tmp, path)`** 로 바꿔치는 것이 관용구다. 그 원자성은 **이 문서의 창(디스크 바이트) 밖**이다.
* ★ **`csv` 문서는 파일을 `newline=''` 로 열라고 적는다**(*"it should be opened with `newline=''`"*). 동작 5 의 `''` 칸 — 끊되 안 바꾼다 — 이 그 까닭과 맞닿는다.
* ★ **`encoding="locale"`**(3.10+) — 문서의 말로 *"can be used to specify the current locale's encoding explicitly"*. 「로캘 인코딩이 의도다」를 코드에 적는 값이다.
* ★ **3.15 를 설치하게 되면 다시 돌릴 것** — 동작 4 의 환경 격자. 문서대로면 `LC_ALL=C PYTHONUTF8=0` 행만 깨지고 **아무것도 안 준 행의 기본이 UTF-8** 이 된다 — ★ **예측이지 측정이 아니다.**
* ★ **윈도에서 다시 돌릴 것** — 동작 5 의 `[2]` `None` 칸이 `b'a\r\nb'` 가 **될 것이라는 말은 문서의 말**이다. 이 머신은 리눅스라 그 칸은 부적용이었다.
