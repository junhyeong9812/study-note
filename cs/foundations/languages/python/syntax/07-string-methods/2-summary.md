# python/syntax/07-string-methods — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [String Methods](https://docs.python.org/3.12/library/stdtypes.html#string-methods) — 메서드 전수의 정본
> - [Text Sequence Type — str](https://docs.python.org/3.12/library/stdtypes.html#text-sequence-type-str) — `str` 의 정의
> - [`unicodedata`](https://docs.python.org/3.12/library/unicodedata.html) — `decimal`/`digit`/`numeric` 의 정의
> - [PEP 616 — String methods to remove prefixes and suffixes](https://peps.python.org/pep-0616/) — `removeprefix`/`removesuffix`(3.9+)
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> **버전** — 대부분 Python 3 전체 공통. **`removeprefix`/`removesuffix` 는 3.9+**.
> `isdecimal`/`isnumeric` 의 답은 **유니코드 DB 판**에 달렸다(이 설치본은 `15.0.0`).
> **선행** — [06-strings-bytes-unicode](../06-strings-bytes-unicode/2-summary.md) — 「`str` 은 코드 포인트 열」이 이 주제의 절반을 설명한다.

## 한눈에 — 쉽게 말하면

**문자열 메서드에서 나는 사고는 거의 전부 「무엇을 인자로 받는가」를 잘못 읽은 것이다.**

```text
  사람이 읽는 방식                     메서드가 실제로 읽는 방식
  ----------------------------------  --------------------------------------
  "example.com".strip(".com")          ".com" 이라는 "글자 4개의 집합"
     -> ".com 을 떼라"                    { '.', 'c', 'o', 'm' }
                                          양 끝에서 이 집합에 드는 글자를
                                          "없어질 때까지" 계속 깎는다

  "hello.com".rstrip(".com")   ->  'hell'      ★ 'o' 까지 먹혔다
  "hello.com".removesuffix(".com") -> 'hello'  ★ 이쪽이 "떼라" 다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 「이 글자들이면 계속 깎아라」 | `strip`/`lstrip`/`rstrip` 의 인자 | `"mississippi".strip("mip")` 이 `'ssiss'` |
| 「이 덩어리면 딱 한 번 떼라」 | `removeprefix`/`removesuffix` | `"aaa".removeprefix("a")` 가 `'aa'` |
| 못 찾았을 때 손드는 사람 | `index` | `ValueError` 를 던진다 |
| 못 찾았을 때 `-1` 이라 적고 넘어가는 사람 | `find` | 진릿값으로 쓰면 **거꾸로** 판정된다 |
| 「공백들을 한 덩어리로 보라」 | `split()`(인자 없음) | 빈 문자열이 안 나온다 |
| 「이 글자 하나를 경계로」 | `split(' ')` | 빈 문자열이 **나온다** |
| 풀칠은 접착제가 한다 | `join` 이 구분자의 메서드인 것 | 어떤 이터러블이든 받는다 |

**똑같은 구조다** — 로그 파싱·CSV 정리·파일 확장자 떼기에서 이 오해가 매번 나온다.\
`strip` 으로 확장자를 떼려다 파일 이름 끝 글자를 먹고, `split(' ')` 로 공백을 나누려다 빈 칸이 섞이고,
`if line.find("ERROR"):` 로 검사하다 **0번 자리에 있는 것을 놓친다.**

> **문자 집합(character set)** — 「이 문자열에 들어 있는 글자들 각각」.\
> `".com"` 을 집합으로 읽으면 `{'.', 'c', 'o', 'm'}` 이고 **순서도 개수도 의미가 없다.**

## 이 주제가 답하려는 질문

1. **`strip` 이 무엇을 지우는가** — 부분 문자열인가 문자 집합인가. 가장 흔한 오해가 여기다.
2. **실패했을 때 무엇이 돌아오는가** — `find` 는 `-1`, `index` 는 예외. 그 차이가 코드 모양을 바꾼다.
3. **「숫자인가」·「같은 글자인가」를 무엇으로 판정하는가** — `isdigit` 세 형제와 `casefold` 가 갈리는 자리.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### 1. ★ `strip` 은 부분 문자열이 아니라 문자 집합을 깎는다

**언제 쓰나** — 확장자·접두사·따옴표를 떼려 할 때. **이 주제 최대의 사고 지점**이다.

문서가 직접 못 박는다 —\
*"The chars argument is a string specifying the **set of characters** to be removed... The chars argument is **not a prefix or suffix**; rather, all combinations of its values are stripped."*

```text
 "hello.com".rstrip(".com")

  h  e  l  l  o  .  c  o  m
                          ^  'm' 이 집합에 있다 -> 깎는다
                       ^     'o' 이 집합에 있다 -> 깎는다
                    ^        'c' 이 집합에 있다 -> 깎는다
                 ^           '.' 이 집합에 있다 -> 깎는다
              ^              'o' 이 집합에 있다 -> ★ 이것도 깎는다
           ^                 'l' 은 집합에 없다 -> 멈춘다

  결과: 'hell'      ★ 'o' 를 잃었다.
```

```python
print(repr("hello.com".rstrip(".com")))
print(repr("example.com".strip(".com")))
print(repr("mississippi".strip("mip")))
print(repr("abcba".strip("ab")), repr("abcba".strip("ba")))
print(repr("  hi  ".strip()), repr("\t\n hi \r\n".strip()))
print(repr("  hi  ".strip("")))
```

```text
'hell'
'example'
'ssiss'
'c' 'c'
'hi' 'hi'
'  hi  '
```

그림 해설.

- ★ **`"example.com".strip(".com")` 은 `'example'` 을 준다 — 맞은 것처럼 보인다.**\
  우연히 `'e'` 가 집합에 없어서 멈췄을 뿐이다. **테스트 한 판으로는 이 버그가 안 드러난다.**
- `"mississippi".strip("mip")` 이 `'ssiss'` 다. 양 끝에서 `m`·`i`·`p` 를 **더 못 깎을 때까지** 깎았다.
- `strip("ab")` 과 `strip("ba")` 이 같다 — **순서가 의미 없다**는 증거다.
- 인자가 없으면 **공백류**를 깎는다(`\t`·`\n`·`\r` 포함). 인자가 `""` 면 **아무것도 안 깎는다.**

**★ `removeprefix`/`removesuffix`(3.9+)가 그 오해를 푼다**

```python
print(repr("hello.com".removesuffix(".com")))
print(repr("mississippi".removeprefix("mip")))
print(repr("example.com".removesuffix(".org")))
print(repr("aaa".removeprefix("a")), "  <- 한 번만")
print(repr("aaa".lstrip("a")),       "  <- strip 은 다 깎는다")
print(repr("abc".removeprefix("")))
```

```text
'hello'
'mississippi'
'example.com'
'aa'   <- 한 번만
''   <- strip 은 다 깎는다
'abc'
```

문서가 두 메서드를 **조건문으로** 정의한다 —\
*"If the string starts with the prefix string, return `string[len(prefix):]`. Otherwise, return a copy of the original string."*

| | `strip(x)` | `removeprefix(x)` / `removesuffix(x)` |
|---|---|---|
| `x` 를 무엇으로 읽나 | **문자 집합** | **덩어리 하나** |
| 몇 번 지우나 | 더 못 지울 때까지 | **딱 한 번** |
| 안 맞으면 | 안 맞는 글자에서 멈춘다 | **원본 그대로** |
| 순서가 의미 있나 | ✗ | ✓ |

> **PEP 616** 이 이 메서드를 넣은 이유가 정확히 이 오해다. 제안서가 `"Bar.txt".rstrip(".txt")` 가 `'Ba'` 가 되는 것을 예로 든다.

**비용** — `strip` 은 「양 끝의 지저분한 글자 떼기」를 한 번에 해 준다(공백·따옴표·구두점).\
대신 **「덩어리 떼기」로 읽으면 조용히 글자를 먹는다.** 3.9 이상이면 그 용도에는 `removesuffix` 를 쓴다.

### 2. 찾기 — `find` 와 `index` 는 **실패할 때만** 다르다

**언제 쓰나** — 부분 문자열의 위치가 필요할 때. 그리고 「있나」만 물을 때.

```text
 찾았을 때                        못 찾았을 때
  find  -> 인덱스                  find  -> -1        ★ 값으로 돌려준다
  index -> 인덱스                  index -> ValueError ★ 흐름을 끊는다
   (둘이 완전히 같다)
```

```python
s = "hello world"
print("find('o')   =", s.find("o"), "  rfind('o') =", s.rfind("o"))
print("find('zz')  =", s.find("zz"))
try:
    s.index("zz")
except ValueError as e:
    print("index('zz') ->", type(e).__name__, e)
print("find('')    =", s.find(""), "  ''.find('') =", "".find(""))
print("범위 인자   :", s.find("o", 5), s.find("o", 5, 7), s.find("o", 0, 4))
```

```text
find('o')   = 4   rfind('o') = 7
find('zz')  = -1
index('zz') -> ValueError substring not found
find('')    = 0   ''.find('') = 0
범위 인자   : 7 -1 -1
```

**★ `find` 의 반환값을 진릿값으로 쓰면 거꾸로 판정된다**

```python
s = "hello world"
for needle in ("hello", "zz", ""):
    print(f"{needle!r:8} find={s.find(needle):3}  if s.find(n): -> {bool(s.find(needle))}")
```

```text
'hello'  find=  0  if s.find(n): -> False
'zz'     find= -1  if s.find(n): -> True
''       find=  0  if s.find(n): -> False
```

```text
 찾았다(0번 자리)  ->  0   -> 거짓 !
 못 찾았다        -> -1   -> 참 !

  ★ 완전히 뒤집혀 있다. 그런데 "hello world" 에서
    "world" 를 찾으면 6 이라 참이 되므로
    테스트 데이터가 앞자리를 피하면 통과해 버린다.
```

문서도 이 자리에 주를 단다 — *"The `find()` method should be used only if you need to know the position of sub. To check if sub is a substring or not, use the `in` operator."*

**`count` 는 겹치는 것을 안 센다**

```python
print("'aaaa'.count('aa') =", "aaaa".count("aa"))
print("'aaaa'.count('')   =", "aaaa".count(""))
```

```text
'aaaa'.count('aa') = 2
'aaaa'.count('')   = 5
```

- `'aaaa'` 에 `'aa'` 는 겹쳐 세면 3 인데 **2** 다. 찾으면 그 뒤에서 다시 시작한다.
- 빈 문자열은 **글자 사이사이 + 양 끝**이라 `len + 1` 이다.

**비용** — `find` 는 예외 비용이 없어 루프 안에서 반복해 쓰기 좋다(`find(sub, pos)` 로 이어 찾기).\
대신 **반환값이 인덱스라 진릿값으로 쓸 수 없다.** 「있나」만 물으려면 `in` 을 쓴다.

### 3. 나누기 — `split()` 과 `split(' ')` 은 다른 알고리즘이다

**언제 쓰나** — 로그·CSV·명령행 파싱. 「공백으로 나눈다」가 두 가지 뜻이라 갈린다.

문서가 **두 알고리즘**이라고 적는다 —\
*"If sep is not specified or is `None`, a **different splitting algorithm** is applied: runs of consecutive whitespace are regarded as a single separator, and the result will contain no empty strings at the start or end..."*

```text
 "  a  b  "

 split()              공백 덩어리를 하나로 보고, 양 끝은 버린다
   -> ['a', 'b']

 split(' ')           ' ' 하나하나가 전부 경계다
   -> ['', '', 'a', '', 'b', '', '']
      ^^          ^^        ^^  ^^
      앞의 공백 2개가       사이 2개 중  뒤의 공백 2개가
      빈 칸 2개를 만든다    하나가 빈 칸  빈 칸 2개
```

```python
line = "  a  b  "
print("split()       =", line.split())
print("split(' ')    =", line.split(" "))
print("''.split()    =", "".split())
print("''.split(' ') =", "".split(" "))
print("'a,,b'.split(',') =", "a,,b".split(","))
print("maxsplit      =", "a:b:c".split(":", 1), "a:b:c".rsplit(":", 1))
try:
    "abc".split("")
except ValueError as e:
    print("split('')     ->", type(e).__name__, e)
```

```text
split()       = ['a', 'b']
split(' ')    = ['', '', 'a', '', 'b', '', '']
''.split()    = []
''.split(' ') = ['']
'a,,b'.split(',') = ['a', '', 'b']
maxsplit      = ['a', 'b:c'] ['a:b', 'c']
split('')     -> ValueError empty separator
```

그림 해설.

- ★ **빈 문자열에서도 갈린다** — `"".split()` 은 `[]`, `"".split(" ")` 은 `['']`.\
  문서가 이것을 따로 적는다 — *"splitting an empty string or a string consisting of just whitespace with a `None` separator returns `[]`."*
- `'a,,b'.split(',')` 이 `['a', '', 'b']` 인 것도 같은 규칙이다 — **구분자를 주면 빈 칸이 생긴다.**\
  문서의 표현: *"consecutive delimiters are not grouped together and are deemed to delimit empty strings."*
- **`split("")` 은 에러다.** 「글자별로 나누기」는 `list(s)` 로 한다.

**`partition` 은 언제나 3칸을 준다**

```python
print("'k=v'.partition('=')   =", "k=v".partition("="))
print("'kv'.partition('=')    =", "kv".partition("="))
print("'a=b=c'.partition('=') =", "a=b=c".partition("="))
print("'a=b=c'.rpartition('=')=", "a=b=c".rpartition("="))
```

```text
'k=v'.partition('=')   = ('k', '=', 'v')
'kv'.partition('=')    = ('kv', '', '')
'a=b=c'.partition('=') = ('a', '=', 'b=c')
'a=b=c'.rpartition('=')= ('a=b', '=', 'c')
```

```text
 split(sep, 1)                 partition(sep)
  못 찾으면 원소 1개짜리         못 찾아도 3칸
  -> 길이가 그때그때 다르다       -> 언제나 (앞, 구분자, 뒤)
  -> 언패킹이 터질 수 있다        -> k, _, v = s.partition('=') 이 안전하다
```

★ **구분자 자체가 결과에 남는 것**도 `partition` 의 특징이다. 「찾았나」를 가운데 칸으로 판정할 수 있다.

**`splitlines` 는 줄바꿈을 11가지로 본다**

```python
names = {"\n": "\\n LF", "\r": "\\r CR", "\r\n": "\\r\\n CRLF", "\v": "\\v 수직탭",
         "\f": "\\f 폼피드", "\x1c": "\\x1c 파일 구분자", "\x1d": "\\x1d 그룹 구분자",
         "\x1e": "\\x1e 레코드 구분자", "\x85": "\\x85 NEL", "\u2028": "\\u2028 줄 구분자",
         "\u2029": "\\u2029 문단 구분자", "\t": "\\t 탭(비교용)"}
for ch, nm in names.items():
    s = "a" + ch + "b"
    print(f"{nm:24} splitlines={s.splitlines()!r:16} split('\\n')={s.split(chr(10))!r}")
```

```text
\n LF                    splitlines=['a', 'b']       split('\n')=['a', 'b']
\r CR                    splitlines=['a', 'b']       split('\n')=['a\rb']
\r\n CRLF                splitlines=['a', 'b']       split('\n')=['a\r', 'b']
\v 수직탭                   splitlines=['a', 'b']       split('\n')=['a\x0bb']
\f 폼피드                   splitlines=['a', 'b']       split('\n')=['a\x0cb']
\x1c 파일 구분자              splitlines=['a', 'b']       split('\n')=['a\x1cb']
\x1d 그룹 구분자              splitlines=['a', 'b']       split('\n')=['a\x1db']
\x1e 레코드 구분자             splitlines=['a', 'b']       split('\n')=['a\x1eb']
\x85 NEL                 splitlines=['a', 'b']       split('\n')=['a\x85b']
\u2028 줄 구분자             splitlines=['a', 'b']       split('\n')=['a\u2028b']
\u2029 문단 구분자            splitlines=['a', 'b']       split('\n')=['a\u2029b']
\t 탭(비교용)                splitlines=['a\tb']         split('\n')=['a\tb']
```

★ **11가지가 전부 줄바꿈이다.** 문서가 표로 싣는다 — `\n`·`\r`·`\r\n`·`\v`·`\f`·`\x1c`·`\x1d`·`\x1e`·`\x85`·`\u2028`·`\u2029`.\
탭만이 아니다. **사용자가 붙여넣은 텍스트에 `\x85`(NEL)나 `\u2028` 이 들어 있으면 줄이 쪼개진다** — JSON 에서 실제로 문제가 되는 자리다.

**끝 줄바꿈에서도 갈린다**

```python
print("'a\\nb\\n'.splitlines() =", "a\nb\n".splitlines())
print("'a\\nb\\n'.split('\\n')  =", "a\nb\n".split("\n"))
print("''.splitlines()        =", "".splitlines())
print("'\\n'.splitlines()      =", "\n".splitlines())
print("keepends=True          =", "a\nb\r\nc".splitlines(True))
```

```text
'a\nb\n'.splitlines() = ['a', 'b']
'a\nb\n'.split('\n')  = ['a', 'b', '']
''.splitlines()        = []
'\n'.splitlines()      = ['']
keepends=True          = ['a\n', 'b\r\n', 'c']
```

★ **`split("\n")` 은 마지막에 빈 칸을 남기고 `splitlines` 는 안 남긴다.** 파일을 읽어 줄 수를 셀 때 하나가 어긋나는 자리다.

**★ `bytes` 쪽은 목록이 더 짧다**

```python
for ch in (b"\n", b"\r", b"\x0b", b"\x0c", b"\x1c"):
    s = b"a" + ch + b"b"
    print(f"{ch!r:8} bytes -> {s.splitlines()!r:18}  str -> {s.decode('latin-1').splitlines()!r}")
```

```text
b'\n'    bytes -> [b'a', b'b']        str -> ['a', 'b']
b'\r'    bytes -> [b'a', b'b']        str -> ['a', 'b']
b'\x0b'  bytes -> [b'a\x0bb']         str -> ['a', 'b']
b'\x0c'  bytes -> [b'a\x0cb']         str -> ['a', 'b']
b'\x1c'  bytes -> [b'a\x1cb']         str -> ['a', 'b']
```

**`bytes.splitlines` 는 `\n`·`\r`·`\r\n` 만** 줄바꿈으로 본다. 유니코드 줄 구분자는 바이트 세계에 없기 때문이다.\
★ 그래서 **파일을 바이너리로 읽느냐 텍스트로 읽느냐에 따라 줄 수가 달라질 수 있다.**

**비용** — `split()` 은 지저분한 공백을 한 번에 정리해 준다.\
대신 **「구분자가 하나」인 데이터(TSV·CSV)에는 못 쓴다** — 빈 칸이 사라지면 열이 밀린다.

### 4. `join` 은 왜 문자열의 메서드인가

**언제 쓰나** — 여러 조각을 이어 붙일 때. `+=` 루프의 대안이다.

문서의 한 줄 —\
*"Return a string which is the concatenation of the strings in iterable... **The separator between elements is the string providing this method.**"*

```text
  리스트의 메서드였다면            문자열의 메서드라서
  ["a","b"].join(",")             ",".join(["a","b"])
       |                                |
   리스트·튜플·집합·dict·           어떤 이터러블이든 받는다.
   제너레이터마다 따로                구분자 쪽에 메서드 하나면 끝.
   구현해야 한다
```

```python
print("','.join(['a','b'])   =", repr(",".join(["a", "b"])))
print("제너레이터            =", repr("-".join(str(i) for i in range(3))))
print("dict 를 주면 키       =", repr("-".join({"a": 1, "b": 2})))
print("문자열을 주면 글자    =", repr("-".join("abc")))
try:
    ",".join(["a", 1])
except TypeError as e:
    print("숫자가 섞이면 ->", type(e).__name__, e)
try:
    ",".join([b"a"])
except TypeError as e:
    print("bytes 가 섞이면 ->", type(e).__name__, e)
print("bytes 쪽 join        :", b",".join([b"a", b"b"]))
```

```text
','.join(['a','b'])   = 'a,b'
제너레이터            = '0-1-2'
dict 를 주면 키       = 'a-b'
문자열을 주면 글자    = 'a-b-c'
숫자가 섞이면 -> TypeError sequence item 1: expected str instance, int found
bytes 가 섞이면 -> TypeError sequence item 0: expected str instance, bytes found
bytes 쪽 join        : b'a,b'
```

그림 해설.

- **구분자 쪽에 메서드가 있으면 구현이 하나**로 끝난다. 리스트 쪽이었다면 모든 이터러블 타입이 각자 구현해야 한다.
- ★ **문서가 `bytes` 를 명시적으로 거부 목록에 넣는다** — *"A TypeError will be raised if there are any non-string values in iterable, **including bytes objects**."*\
  [06번](../06-strings-bytes-unicode/2-summary.md)의 벽이 여기서도 서 있다.
- 숫자를 섞으면 **몇 번째 원소인지까지** 알려 준다(`sequence item 1`).

**왜 `+=` 루프보다 나은가**

문자열은 불변이라 `s += x` 는 **매번 새 문자열을 만든다.** 조각이 n 개면 총 비용이 n² 에 가깝다.\
문서가 시퀀스 일반에 대해 같은 말을 한다 — *"building up a sequence by repeated concatenation will have a **quadratic runtime cost** in the total sequence length."*\
`join` 은 **전체 길이를 먼저 재고 한 번에** 만든다.

**비용** — `join` 은 이터러블을 한 번 다 훑어야 하므로 **제너레이터를 주면 내부에서 리스트로 물질화**한다(길이를 알아야 하니까).\
대신 이어 붙이기가 O(n) 한 번에 끝난다.

### 5. 검사 — `isdecimal` · `isdigit` · `isnumeric` 은 **다른 셋**이다

**언제 쓰나** — 입력 검증. 「숫자만 들어왔나」를 물을 때.

문서가 세 정의를 갈라 둔다.

| 메서드 | 문서의 정의 | 무엇까지 참인가 |
|---|---|---|
| `isdecimal` | *"Decimal characters are those that can be used to form numbers in base 10"* | 10진 자릿수만 |
| `isdigit` | *"Digits include decimal characters and digits that need special handling, such as the **compatibility superscript digits**"* | + 위첨자 등 |
| `isnumeric` | *"all characters that have the **Unicode numeric value property**"* | + 분수·로마 숫자·한자 수 |

```text
                 isnumeric  (가장 넓다)
      +--------------------------------------+
      |   ½  Ⅳ  〇  一  万   (숫자 값이 있는 글자)  |
      |   +------------------------------+   |
      |   |  isdigit                     |   |
      |   |    ²  ³  (위첨자 등)            |   |
      |   |   +----------------------+   |   |
      |   |   | isdecimal            |   |   |
      |   |   |   7   ٧  (10진 자릿수)  |   |   |
      |   |   +----------------------+   |   |
      |   +------------------------------+   |
      +--------------------------------------+
```

```python
print(f"{'글자':6} {'isdecimal':>10} {'isdigit':>8} {'isnumeric':>10}   int() 되나")
for c in ("7", "٧", "²", "½", "Ⅳ", "〇", "一", "", " ", "7.5", "-7"):
    try:
        iv = repr(int(c))
    except ValueError:
        iv = "ValueError"
    print(f"{c!r:8} {str(c.isdecimal()):>10} {str(c.isdigit()):>8} {str(c.isnumeric()):>10}   {iv}")
```

```text
글자      isdecimal  isdigit  isnumeric   int() 되나
'7'            True     True       True   7
'٧'            True     True       True   7
'²'           False     True       True   ValueError
'½'           False    False       True   ValueError
'Ⅳ'           False    False       True   ValueError
'〇'           False    False       True   ValueError
'一'           False    False       True   ValueError
''            False    False      False   ValueError
' '           False    False      False   ValueError
'7.5'         False    False      False   ValueError
'-7'          False    False      False   -7
```

★ **세 가지가 동시에 뒤집힌다.**

1. **`'٧'`(아랍-인도 숫자 7)은 `isdecimal` 이 참이고 `int()` 도 `7` 을 준다.**\
   「ASCII 숫자만 받겠다」는 검증을 `isdecimal` 로 짰으면 **통과해 버린다.**
2. **`'-7'` 은 세 검사가 전부 거짓인데 `int()` 는 된다.** 부호를 검사 함수가 안 본다.
3. **`'7.5'` 도 세 검사가 전부 거짓**이다. 실수를 받으려면 이 계열로는 안 된다.

**그래서 세 검사 어느 것도 「int 로 바꿀 수 있나」의 답이 아니다**

```text
 세 is* 검사                       int() 로 바꿀 수 있나
  글자 하나하나의 성질을 본다         부호·공백까지 포함한 "문장" 을 본다
       |                                |
       +-- '٧' 통과, '-7' 탈락          +-- '٧' 통과, '-7' 통과
                                          ★ 두 집합이 서로 포함 관계가 아니다
```

**「ASCII 숫자만」을 물으려면 검사가 하나 더 필요하다**

```python
for s in ("7", "٧", "-7", "07"):
    print(f"{s!r:6} isdecimal={s.isdecimal()!s:6} ascii 만={s.isdecimal() and s.isascii()!s:6} 정수 변환={'된다' if s.lstrip('-').isdecimal() else '안 된다'}")
```

```text
'7'    isdecimal=True   ascii 만=True   정수 변환=된다
'٧'    isdecimal=True   ascii 만=False  정수 변환=된다
'-7'   isdecimal=False  ascii 만=False  정수 변환=된다
'07'   isdecimal=True   ascii 만=True   정수 변환=된다
```

★ **`str.isascii()`(3.7+)를 같이 물어야** 「ASCII 숫자만」이 된다.\
★ 그런데 셋째 열과 넷째 열이 **`'-7'` 에서 또 갈린다** — `isdecimal` 계열로는 부호를 절대 못 받는다.\
**세 열 중 어느 것도 「정수로 쓸 수 있나」의 답이 아니다.**

**`unicodedata` 가 그 갈림의 근거를 직접 답한다**

```python
import unicodedata
for c in ("7", "٧", "²", "½", "Ⅳ", "一"):
    print(f"{c!r:6} name={unicodedata.name(c):32} decimal={unicodedata.decimal(c, None)} digit={unicodedata.digit(c, None)} numeric={unicodedata.numeric(c, None)}")
```

```text
'7'    name=DIGIT SEVEN                      decimal=7 digit=7 numeric=7.0
'٧'    name=ARABIC-INDIC DIGIT SEVEN         decimal=7 digit=7 numeric=7.0
'²'    name=SUPERSCRIPT TWO                  decimal=None digit=2 numeric=2.0
'½'    name=VULGAR FRACTION ONE HALF         decimal=None digit=None numeric=0.5
'Ⅳ'    name=ROMAN NUMERAL FOUR               decimal=None digit=None numeric=4.0
'一'    name=CJK UNIFIED IDEOGRAPH-4E00       decimal=None digit=None numeric=1.0
```

**세 `is*` 메서드는 이 세 속성을 그대로 되묻는 것**이다. 유니코드 DB 가 정본이고 파이썬은 조회만 한다.

**비용** — 한 줄로 형태 검증이 된다.\
대신 **「받고 싶은 숫자」의 정의가 유니코드의 정의와 다르다.** 입력 검증에는 `int()`/`Decimal()` 을 `try` 로 감싸는 쪽이 정확하다.

### 6. 대소문자 — `casefold` 와 `lower` 가 갈리는 자리

**언제 쓰나** — 로그인 아이디·검색어를 대소문자 무시하고 비교할 때.

문서의 정의 —\
*"Return a casefolded copy of the string. Casefolded strings may be used for **caseless matching**. Casefolding is similar to lowercasing but **more aggressive** because it is intended to remove all case distinctions in a string."*

```text
 독일어 ß (에스체트)

   "straße"                     "STRASSE"
      |                             |
   .lower()  -> "straße"         .lower()  -> "strasse"
      |                             |
      +--------- != --------------- +     ★ lower 로는 안 맞는다

   .casefold() -> "strasse"      .casefold() -> "strasse"
      |                             |
      +--------- == --------------- +     ★ casefold 로는 맞는다
```

```python
a, b = "straße", "STRASSE"
print("a.lower()    =", repr(a.lower()),    " b.lower()    =", repr(b.lower()),    " 같나:", a.lower() == b.lower())
print("a.casefold() =", repr(a.casefold()), " b.casefold() =", repr(b.casefold()), " 같나:", a.casefold() == b.casefold())
print("a.upper()    =", repr(a.upper()), " len:", len(a), "->", len(a.upper()))
print("ß.upper().lower() =", repr("ß".upper().lower()), " <- 왕복이 안 된다")
```

```text
a.lower()    = 'straße'  b.lower()    = 'strasse'  같나: False
a.casefold() = 'strasse'  b.casefold() = 'strasse'  같나: True
a.upper()    = 'STRASSE'  len: 6 -> 7
ß.upper().lower() = 'ss'  <- 왕복이 안 된다
```

★ **`upper()` 가 길이를 바꾼다.** `'ß'` 한 글자가 `'SS'` 두 글자가 된다.\
★ **왕복이 안 된다** — `'ß'.upper().lower()` 가 `'ss'` 다. 원래 글자가 사라졌다.

```python
for s in ("ß", "ﬁ", "ǰ", "İ"):
    print(f"{s!r:6} len={len(s)}  upper={s.upper()!r} len={len(s.upper())}  lower={s.lower()!r} len={len(s.lower())}  casefold={s.casefold()!r}")
```

```text
'ß'    len=1  upper='SS' len=2  lower='ß' len=1  casefold='ss'
'ﬁ'    len=1  upper='FI' len=2  lower='ﬁ' len=1  casefold='fi'
'ǰ'    len=1  upper='J̌' len=2  lower='ǰ' len=1  casefold='ǰ'
'İ'    len=1  upper='İ' len=1  lower='i̇' len=2  casefold='i̇'
```

★ **`'İ'`(점 있는 터키어 대문자 I)는 `lower()` 가 길이를 1 에서 2 로 늘린다.**\
「대소문자 변환은 길이를 안 바꾼다」가 **양쪽 방향 모두 틀린다.**

**★ 그리스어 시그마 — `lower` 는 자리를 보고 `casefold` 는 안 본다**

```python
print(repr("ΟΔΟΣ".lower()), repr("ΟΔΟΣ".casefold()))
print("σ 와 ς:  casefold 로", "σ".casefold() == "ς".casefold(), " | lower 로", "σ".lower() == "ς".lower())
```

```text
'οδος' 'οδοσ'
σ 와 ς:  casefold 로 True  | lower 로 False
```

- `lower()` 는 **단어 끝이면 `ς`(final sigma)로** 바꾼다 — 문맥을 본다.
- `casefold()` 는 그 구분을 **없앤다** — 그래서 `σ` 와 `ς` 가 같아진다.
- ★ **「`casefold` 는 `lower` 를 더 세게 한 것」이 아니다.** 목적이 다르다 —
  `lower` 는 **사람이 읽을 소문자**를, `casefold` 는 **비교용 정규형**을 만든다.

**그 밖의 자리**

```python
print("'hello world'.title() =", repr("hello world".title()))
print("\"o'neill\".title()     =", repr("o'neill".title()))
print("capitalize            =", repr("hELLO wORLD".capitalize()))
print("swapcase              =", repr("Hello".swapcase()))
print("한글에는 대소문자가 없다 :", "가나".upper() == "가나")
```

```text
'hello world'.title() = 'Hello World'
"o'neill".title()     = "O'Neill"
capitalize            = 'Hello world'
swapcase              = 'hELLO'
한글에는 대소문자가 없다 : True
```

★ **`title()` 은 아포스트로피 뒤를 대문자로 만든다.** 사람 이름에 쓰면 `O'Neill` 이 되는데 `Mcdonald's` 는 `Mcdonald'S` 가 된다.\
문서도 이 한계를 적고 정규식으로 대신하는 예를 싣는다.

**비용** — `casefold` 는 「같은 글자인가」를 언어에 가깝게 판정해 준다.\
대신 **원본이 아니다.** 저장은 원본으로 하고 **비교용 키만 `casefold`** 로 따로 만든다.
그리고 [06번](../06-strings-bytes-unicode/2-summary.md)의 정규화와 **둘 다** 거쳐야 진짜 정규형이 된다.

### 7. 바꾸기 — `replace` 는 한 번에 하나, `translate` 는 한 번에 전부

**언제 쓰나** — 치환. 두 개 이상을 바꿀 때 순서가 문제가 된다.

```python
print(repr("aaaa".replace("a", "b", 2)))
print(repr("abc".replace("", "-")))
print(repr("aaa".replace("aa", "b")))
```

```text
'bbaa'
'-a-b-c-'
'ba'
```

- 셋째 인자가 **최대 횟수**다.
- 빈 문자열로 바꾸면 **글자 사이사이에** 낀다(2번 절의 `count('')` 와 같은 규칙).
- `'aaa'.replace('aa','b')` 가 `'ba'` 다 — 왼쪽부터 **겹치지 않게** 찾는다.

**★ `replace` 두 번으로는 「맞바꾸기」가 안 된다**

```text
 "abab" 에서 a 와 b 를 맞바꾸려면

  replace 두 번                        translate 한 번
   "abab".replace("a","b")              str.maketrans("ab","ba")
      -> "bbbb"     ★ 여기서 이미 망했다     -> 한 번 훑으며 각 글자를 동시에 바꾼다
   .replace("b","a")
      -> "aaaa"                            -> "baba"
```

```python
t = str.maketrans("ab", "ba")
print("translate  :", repr("abab".translate(t)))
print("replace 두 번:", repr("abab".replace("a", "b").replace("b", "a")))
print("maketrans 가 만든 것:", str.maketrans("abc", "xyz"))
print("지우기:", repr("beautiful".translate(str.maketrans("", "", "aeiou"))))
print("dict 로:", repr("abc".translate(str.maketrans({"a": "[에이]", 0x62: None}))))
```

```text
translate  : 'baba'
replace 두 번: 'aaaa'
maketrans 가 만든 것: {97: 120, 98: 121, 99: 122}
지우기: 'btfl'
dict 로: '[에이]c'
```

그림 해설.

- ★ **`maketrans` 가 만드는 것은 「코드 포인트 → 무엇」 dict** 다. 키가 정수인 것이 보인다.\
  [06번](../06-strings-bytes-unicode/2-summary.md)의 「`str` 은 코드 포인트 열」이 여기서 그대로 드러난다.
- 값이 `None` 이면 **지운다.** 셋째 인자로 넘긴 글자들도 전부 `None` 이 된다.
- 값이 **여러 글자여도 된다**(`"[에이]"`). 1:N 치환이 된다.
- `translate` 는 **한 번만 훑으므로** 치환 결과가 다시 치환되는 일이 없다.

**비용** — `translate` 는 글자 단위 치환을 O(n) 한 번에 끝낸다.\
대신 **글자 하나 단위**라 `replace("hello", "hi")` 같은 덩어리 치환은 못 한다.

### 8. 문자열은 불변이다 — 그런데 「언제나 새 객체」는 아니다

**언제 쓰나** — 메서드가 원본을 바꿀 거라 착각할 때. 그리고 `is` 로 확인하려 할 때.

```text
 s = "hello"
 t = s.replace("l", "L")

  +---------+          +---------+
  | "hello" | <- s     | "heLLo" | <- t
  +---------+          +---------+
      ^                    ^
      원본은 그대로다        새 문자열 객체가 하나 더 생겼다
```

```python
s = "hello"
print("replace 결과가 같은 객체인가:", s.replace("l", "L") is s)
print("바꿀 게 없으면              :", s.replace("z", "Z") is s, repr(s.replace("z", "Z")))
print("upper().lower()             :", s.upper().lower() is s)
print("s[:]                        :", s[:] is s)
print("s 는 그대로                  :", s)
try:
    s[0] = "H"
except TypeError as e:
    print("s[0] = 'H' ->", type(e).__name__, e)
```

```text
replace 결과가 같은 객체인가: False
바꿀 게 없으면              : True 'hello'
upper().lower()             : False
s[:]                        : True
s 는 그대로                  : hello
s[0] = 'H' -> TypeError 'str' object does not support item assignment
```

그림 해설.

- ★ **「모든 메서드가 새 객체를 준다」가 두 자리에서 틀린다** —\
  `replace` 가 **바꿀 것을 못 찾으면 원본을 그대로** 돌려주고, `s[:]` 도 원본을 그대로 돌려준다.
- `upper().lower()` 는 값이 같아도 **다른 객체**다. 값이 같다고 같은 객체가 되지는 않는다([02번](../02-is-vs-eq-interning/2-summary.md)).
- ★ **이것은 CPython 의 최적화이지 언어 보장이 아니다.** 「같은 객체를 돌려준다」에 기대는 코드를 쓰면 안 된다.
- `s[0] = "H"` 는 `TypeError` 다 — **불변이라는 것이 여기서 드러난다.**

> ★ `is`/`id()` 가 답하는 것은 「**같은 객체인가**」이지 「어디에 있는가」가 아니다.
> `id()` 의 값이 메모리 주소라는 것은 CPython 구현 세부사항이다([02번](../02-is-vs-eq-interning/2-summary.md) 정본).

**비용** — 불변이라 dict 키·집합 원소가 되고 여러 곳에서 공유해도 안전하다.\
대신 **조각을 이어 붙일 때마다 새 객체**다. 그래서 4번 절의 `join` 이 필요하다.

### 9. ★ 채우기 — `center` 와 포맷 스펙 `^` 가 **다른 답을 낸다**

**언제 쓰나** — 표·영수증·로그를 정렬할 때.

```python
print(f"{'문자열':4} {'width':>5} {'center':>10} {'format ^':>10}  같나")
for s in ("a", "ab", "abc"):
    for w in range(len(s) + 1, len(s) + 5):
        c = s.center(w, "*"); f = format(s, "*^" + str(w))
        print(f"{s!r:6} {w:5} {c!r:>10} {f!r:>10}  {c == f}")
```

```text
문자열  width     center   format ^  같나
'a'        2       'a*'       'a*'  True
'a'        3      '*a*'      '*a*'  True
'a'        4     '*a**'     '*a**'  True
'a'        5    '**a**'    '**a**'  True
'ab'       3      '*ab'      'ab*'  False
'ab'       4     '*ab*'     '*ab*'  True
'ab'       5    '**ab*'    '*ab**'  False
'ab'       6   '**ab**'   '**ab**'  True
'abc'      4     'abc*'     'abc*'  True
'abc'      5    '*abc*'    '*abc*'  True
'abc'      6   '*abc**'   '*abc**'  True
'abc'      7  '**abc**'  '**abc**'  True
```

```text
 남는 칸이 홀수일 때 여분을 어느 쪽에 두나

  len(s) 가 짝수 & width 가 홀수  ->  center 는 왼쪽,  format ^ 는 오른쪽
                                      ★ 여기서만 갈린다

  'ab'.center(3, '*')     -> '*ab'
  format('ab', '*^3')     -> 'ab*'
```

★ **문서 어느 쪽도 「여분을 어느 쪽에 두는가」를 정하지 않는다.**\
`str.center` 는 *"Return centered in a string of length width"* 까지고,
포맷 스펙의 `'^'` 는 *"Forces the field to be centered within the available space"* 까지다.\
**그래서 이 갈림은 「언어 보장」이 아니라 「이 판의 관찰」이다.** 표를 두 방법으로 섞어 그리면 한 칸이 어긋난다.

**나머지 채우기 메서드**

```python
print(repr("42".zfill(5)), repr("-42".zfill(5)), repr("+42".zfill(5)), repr("ab".zfill(5)))
print(repr("ab".ljust(6, ".")), repr("ab".rjust(6, ".")))
print(repr("abcdef".center(3)), " <- 이미 길면 그대로")
print(repr("a\tb".expandtabs(4)), repr("ab\tc".expandtabs(4)))
print(repr("가나".ljust(6, ".")), "len =", len("가나".ljust(6, ".")))
```

```text
'00042' '-0042' '+0042' '000ab'
'ab....' '....ab'
'abcdef'  <- 이미 길면 그대로
'a   b' 'ab  c'
'가나....' len = 6
```

- ★ **`zfill` 은 부호를 안다** — `'-42'` 가 `'-0042'` 다. `rjust(5, "0")` 이었다면 `'00-42'` 가 됐을 것이다.
- `expandtabs(4)` 는 **탭 스톱**이다. `'a\tb'` 는 3칸, `'ab\tc'` 는 2칸을 채운다 — 고정 폭이 아니다.
- ★ **한글은 `len` 으로 1 인데 터미널에서 2칸**이라 `ljust` 로 만든 표가 어긋난다([06번](../06-strings-bytes-unicode/2-summary.md)의 「몇 글자인가」 네 답).

**비용** — 한 줄로 정렬이 된다.\
대신 **여분 칸의 방향이 두 도구에서 다르고**, 동아시아 문자 폭을 안 본다.

## 문법 — 형태와 규칙

```python
# 찾기
s.find(sub[, start[, end]])      # 없으면 -1
s.index(sub[, start[, end]])     # 없으면 ValueError
s.rfind(sub) / s.rindex(sub)     # 오른쪽부터
sub in s                         # "있나" 만 물을 때는 이것
s.count(sub)                     # 겹치는 것은 안 센다
s.startswith(prefix) / s.endswith(suffix)   # 튜플을 받는다

# 자르기
s.strip([chars]) / s.lstrip / s.rstrip      # chars 는 "문자 집합"
s.removeprefix(p) / s.removesuffix(x)       # 3.9+ — "덩어리 하나"

# 나누기 / 붙이기
s.split([sep[, maxsplit]])       # sep 없으면 "다른 알고리즘"
s.rsplit / s.partition(sep) / s.rpartition(sep)
s.splitlines([keepends])         # 줄바꿈 11가지
sep.join(iterable)               # 구분자 쪽의 메서드

# 바꾸기
s.replace(old, new[, count])
s.translate(table)               # table = str.maketrans(...)

# 검사
s.isdecimal() / s.isdigit() / s.isnumeric()
s.isalpha() / s.isalnum() / s.isspace() / s.isascii()   # isascii 는 3.7+
s.isupper() / s.islower() / s.istitle()

# 대소문자
s.lower() / s.upper() / s.casefold() / s.title() / s.capitalize() / s.swapcase()

# 채우기
s.ljust(w[, fill]) / s.rjust / s.center / s.zfill(w) / s.expandtabs(n)
```

규칙은 여덟이다.

1. **`strip` 의 인자는 문자 집합**이다. 덩어리를 떼려면 `removeprefix`/`removesuffix`(3.9+).
2. **`find` 는 `-1`, `index` 는 예외**를 낸다. **`find` 의 결과를 진릿값으로 쓰면 거꾸로 판정**된다.
3. **`split()` 과 `split(sep)` 은 다른 알고리즘**이다. 앞엣것만 공백 덩어리를 하나로 본다.
4. **`partition` 은 언제나 3칸**을 준다. 언패킹이 안전하다.
5. **`splitlines` 는 11가지를 줄바꿈으로** 본다(`bytes` 쪽은 3가지).
6. **`join` 은 구분자의 메서드**이고 원소가 전부 `str` 이어야 한다(`bytes` 도 거부).
7. **`isdecimal`·`isdigit`·`isnumeric` 은 포함 관계**이고 셋 다 **`int()` 와는 다른 집합**이다.
8. **문자열은 불변**이라 모든 메서드가 새 값을 돌려준다 — 단 **바뀔 것이 없으면 원본을 그대로** 돌려주기도 한다(구현 세부사항).

## 어디서 틀리나

### (1) `strip` 으로 확장자를 뗀다

```python
print(repr("hello.com".rstrip(".com")))      # 'hell'
print(repr("example.com".strip(".com")))     # 'example'   <- 맞은 것처럼 보인다
```

**한 판으로는 안 드러난다.** `removesuffix(".com")` 를 쓴다.

### (2) `if s.find(x):` 로 있나를 검사한다

```python
line = "ERROR: 실패"
print(bool(line.find("ERROR")))    # False   <- 0번 자리에 있어서
print(bool(line.find("WARN")))     # True    <- 없는데 참
```

**완전히 뒤집혀 있다.** `"ERROR" in line` 을 쓴다.

### (3) `split(' ')` 로 공백을 나눈다

```python
print("  a  b  ".split(" "))   # ['', '', 'a', '', 'b', '', '']
```

인자를 빼면 `['a', 'b']` 다. **로그 파싱에서 열이 밀리는 원인**이다.

### (4) `split("\n")` 으로 줄을 센다

```python
print(len("a\nb\n".split("\n")), len("a\nb\n".splitlines()))   # 3 2
```

끝 줄바꿈이 빈 칸을 하나 남긴다.

### (5) `isdigit()` 로 「숫자만」을 검증한다

```python
print("٧".isdigit(), int("٧"))     # True 7
print("-7".isdigit(), int("-7"))   # False -7
```

**둘 다 틀렸다.** ASCII 숫자만 받으려면 `s.isdecimal() and s.isascii()`, 값으로 쓸 거면 `int()` 를 `try` 로 감싼다.

### (6) `lower()` 로 대소문자 무시 비교를 한다

```python
print("straße".lower() == "STRASSE".lower())       # False
print("straße".casefold() == "STRASSE".casefold()) # True
```

비교에는 `casefold`, 그리고 [06번](../06-strings-bytes-unicode/2-summary.md)의 정규화까지 같이 건다.

### (7) `replace` 두 번으로 맞바꾼다

```python
print("abab".replace("a", "b").replace("b", "a"))   # aaaa
```

**첫 치환의 결과가 두 번째 치환의 입력**이 된다. `translate` 를 쓴다.

### (8) `title()` 로 이름을 예쁘게 만든다

```python
print("o'neill".title(), "mcdonald's".title())   # O'Neill Mcdonald'S
```

아포스트로피 뒤를 새 단어로 본다. 문서도 이 한계를 적는다.

### (9) `+=` 루프로 문자열을 쌓는다

```python
out = ""
for i in range(3):
    out += str(i)         # 매번 새 문자열
print(out)                # 012
```

문자열은 불변이라 **조각 수의 제곱에 가까운 비용**이 든다. `"".join(...)` 을 쓴다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」이 두껍다** — 메서드 의미는 문서가 하나하나 정한다. 관찰 층은 **여분 칸의 방향**과 **객체 재사용** 둘이다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 라이브러리 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 + `is` 로 확인 |
| **이 판의 관찰** | 3.12.3 에서 그랬을 뿐 | 「관찰」로 명기 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| `strip` 의 인자는 **문자 집합**이고 접두사·접미사가 아니다 | String Methods — *"not a prefix or suffix"* |
| `removeprefix`/`removesuffix` 는 **조건 하나**로 정의된다(맞으면 한 번 잘라내고 아니면 복사본) | String Methods (3.9+, PEP 616) |
| `find` 는 못 찾으면 `-1`, `index` 는 `ValueError` | String Methods |
| 「있나」만 물으려면 `in` 을 써야 한다 | String Methods 의 `find` 주석 |
| `split()` 은 **다른 알고리즘**이고 빈 문자열을 안 남긴다 | String Methods — *"a different splitting algorithm is applied"* |
| `split(sep)` 은 **연속 구분자를 묶지 않고** 빈 문자열을 만든다 | String Methods |
| `splitlines` 가 줄바꿈으로 보는 **11가지** 목록 | String Methods 의 표 |
| `join` 은 **구분자가 그 메서드를 제공하는 문자열**이고 `bytes` 를 포함한 비-`str` 은 `TypeError` | String Methods |
| `isdecimal` ⊂ `isdigit` ⊂ `isnumeric` 의 정의 | String Methods 각 항목 |
| `casefold` 는 `lower` 보다 **더 공격적**이고 caseless matching 용이다 | String Methods |
| `center` 는 `width` 가 `len(s)` 이하면 **원본을 돌려준다** | String Methods |
| 불변 열을 반복 이어 붙이면 **제곱 비용**이 든다 | Common Sequence Operations |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| `replace` 가 **바꿀 것을 못 찾으면 원본 객체를 그대로** 돌려준다 | `s.replace("z","Z") is s` 가 `True` |
| `s[:]` 가 **원본 객체를 그대로** 돌려준다 | `s[:] is s` 가 `True` |
| `str.maketrans` 가 만드는 것이 **코드 포인트를 키로 하는 dict** 다 | `str.maketrans("abc","xyz")` 가 `{97: 120, 98: 121, 99: 122}` |
| `join` 의 `TypeError` 가 **몇 번째 원소인지**를 알려 준다 | `sequence item 1: expected str instance, int found` |

### 이 판(3.12.3)의 관찰 — 버전이 오르면 다시 찍어야 한다

| 관찰 | 어디가 흔들리나 |
|---|---|
| **`center` 는 여분 칸을 왼쪽에, 포맷 스펙 `^` 는 오른쪽에 둔다**(`len` 짝수 & `width` 홀수일 때) | **문서가 어느 쪽도 정하지 않는다.** 두 도구가 갈린다는 사실 자체가 관찰이다 |
| `isdecimal`/`isdigit`/`isnumeric` 의 각 글자에 대한 답 | **유니코드 DB 판**(`unidata_version` = `15.0.0`)에 달렸다 |
| `'ΟΔΟΣ'.lower()` 가 `'οδος'`(final sigma) | 유니코드의 특수 케이스 매핑 표에 달렸다 |
| `'İ'.lower()` 가 길이 2 가 되는 것 | 〃 |
| 예외 문구 전부(`empty separator`·`substring not found` 등) | 예외 종류는 명세지만 문구는 아니다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「`strip(".com")` 은 `.com` 을 뗀다」\
  ○ **`{'.','c','o','m'}` 에 드는 글자를 양 끝에서 계속 깎는다.** 문서가 *"not a prefix or suffix"* 라고 못 박는다.
- ✗ 「`find` 가 0 이 아니면 찾은 것이다」\
  ○ `0` 이 「**0번 자리에서 찾았다**」이고 `-1` 이 「못 찾았다」다. 진릿값으로 쓰면 거꾸로다.
- ✗ 「`split()` 과 `split(' ')` 은 같다」\
  ○ **다른 알고리즘**이다. 빈 문자열에서부터 답이 갈린다.
- ✗ 「`splitlines` 는 `\n` 과 `\r\n` 을 나눈다」\
  ○ **11가지**다. `\v`·`\f`·`\x1c`·`\x85`·`\u2028` 까지 전부.
- ✗ 「`isdigit()` 이면 `int()` 로 바꿀 수 있다」\
  ○ **두 집합이 포함 관계가 아니다.** `'²'` 는 `isdigit` 인데 `int()` 가 안 되고, `'-7'` 은 반대다.
- ✗ 「`casefold` 는 `lower` 를 더 세게 한 것이다」\
  ○ **목적이 다르다.** `lower` 는 문맥을 보고(final sigma) `casefold` 는 비교용 정규형을 만든다.
- ✗ 「문자열 메서드는 언제나 새 객체를 돌려준다」\
  ○ **바뀔 것이 없으면 원본을 그대로** 돌려주기도 한다. 단 그것은 **구현 세부사항**이라 기대면 안 된다.
- ✗ 「`center(n)` 과 `format(s, '^n')` 은 같다」\
  ○ **여분 칸의 방향이 갈린다.** 문서가 정하지 않은 자리다.

**판정 기준 한 줄**: 어떤 메서드에 **문자열을 인자로 넘기고 있다면**, 그 인자가 **덩어리인지 문자 집합인지** 먼저 확인하라. 이 주제 사고의 절반이 거기다.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| `in` | 「있나」만 물을 때 — **`find` 를 쓰지 않는다** |
| `find` | 위치가 정말 필요할 때, 그리고 루프로 이어 찾을 때 |
| `index` | 없으면 버그인 상황 — 예외로 멈추는 게 맞을 때 |
| `removeprefix`/`removesuffix` | 접두사·접미사 **덩어리**를 뗄 때 (3.9+) |
| `strip()` | 양 끝 공백 정리. 인자 없이 쓰는 것이 가장 안전하다 |
| `split()` | 공백으로 나눌 때 — **인자를 주지 않는다** |
| `split(sep)` | TSV·CSV 처럼 **구분자가 정확히 하나**인 데이터 |
| `partition` | `key=value` 처럼 **처음 한 번만** 나눌 때. 언패킹이 안전하다 |
| `splitlines` | 줄 나누기 — **`split("\n")` 을 쓰지 않는다** |
| `join` | 조각 이어 붙이기 — **`+=` 루프를 쓰지 않는다** |
| `translate` | 글자 단위 다중 치환·삭제. 맞바꾸기 |
| `casefold` | 대소문자 무시 **비교**. 저장은 원본으로 |
| `startswith`/`endswith` | 튜플을 줘서 여러 후보를 한 번에 |

**정규식을 꺼내는 선**은 이렇다.

| 이걸로 된다 | 정규식이 필요하다 |
|---|---|
| 고정 문자열 찾기·바꾸기 | **패턴**(숫자 3자리, 단어 경계) |
| 구분자 하나로 나누기 | **여러 구분자**·구분자가 패턴 |
| 접두·접미 판정 | 중간의 그룹을 **뽑아내기** |
| 글자 단위 치환(`translate`) | 문맥에 따른 치환 |

★ **문자열 메서드가 되는 일은 정규식보다 빠르고 읽기 쉽다.** 정규식은 「패턴」이 필요할 때만 꺼낸다(목록의 **46번 주제**).

## 핵심 문장

- **`strip` 의 인자는 문자 집합이다.** 문서가 *"not a prefix or suffix"* 라고 못 박았는데도 이 오해가 가장 흔하다. 덩어리는 `removesuffix`.
- **`find` 는 `-1`, `index` 는 예외.** `find` 의 결과를 진릿값으로 쓰면 **찾았을 때 거짓, 못 찾았을 때 참**이 된다.
- **`split()` 과 `split(' ')` 은 다른 알고리즘**이다. 빈 문자열에서 `[]` 와 `['']` 로 갈린다.
- **`splitlines` 는 11가지를 줄바꿈으로 본다** — `bytes` 쪽은 3가지다. 붙여넣은 텍스트에서 줄이 쪼개지는 원인.
- **`join` 이 구분자의 메서드인 것은 이터러블 전부를 한 구현으로 받기 위해서**다. 그리고 `+=` 루프의 제곱 비용을 없앤다.
- **`isdecimal`·`isdigit`·`isnumeric` 은 포함 관계이고, 셋 다 `int()` 와는 다른 집합**이다. `'٧'` 은 통과하고 `'-7'` 은 탈락한다.
- **`casefold` 는 `lower` 의 강화판이 아니다.** `lower` 는 문맥을 보고(final sigma) `casefold` 는 그 구분을 없앤다.
- **`center` 와 포맷 스펙 `^` 가 여분 칸을 반대쪽에 둔다** — 문서가 정하지 않은 자리라 **관찰**이다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **07번**
- 선행: [06-strings-bytes-unicode](../06-strings-bytes-unicode/2-summary.md) — 「`str` 은 코드 포인트 열」이 `maketrans` 의 정수 키, `isdecimal` 의 유니코드 근거, `join` 의 `bytes` 거부를 전부 설명한다.
- 이어지는 곳: [08-fstrings-and-format-spec](../08-fstrings-and-format-spec/2-summary.md) — 9번 절의 `center` 대 `^` 가 거기서 이어진다. 채우기는 포맷 스펙 쪽이 더 넓다.
- 이어지는 곳: [09-sequence-ops-and-slicing](../09-sequence-ops-and-slicing/2-summary.md) — `s[:]`·`in`·`count`·`index` 는 **시퀀스 공통 연산**이라 거기가 정본이다.
- 이어지는 곳: [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md) — 8번 절의 「같은 객체인가」의 정본.
- 이어지는 곳: [05-truthiness-and-short-circuit](../05-truthiness-and-short-circuit/2-summary.md) — 2번 절의 「`find` 를 진릿값으로」가 거기 규칙과 맞물린다.
- 이어지는 곳: 목록의 **46번 주제** 「`re`」 — 정규식을 꺼내는 선. 위 표가 그 경계다.
- 이어지는 곳: 목록의 **43번 주제** 「`collections`」 — `Counter` 로 글자 세기.
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/) — 문자열 메서드를 「이렇게 쓴다」까지 다룬다.\
  **경계**: 그쪽은 호출 예시까지, 여기는 「**인자를 무엇으로 읽는가**」부터다.
- 연혁은 여기가 아니다: [`history/python/`](../../../../../../history/python/)
- 공식 문서: [String Methods](https://docs.python.org/3.12/library/stdtypes.html#string-methods) · [PEP 616](https://peps.python.org/pep-0616/) · [`unicodedata`](https://docs.python.org/3.12/library/unicodedata.html)

## 용어 풀이

- **문자 집합(character set) 인자**: `strip`·`lstrip`·`rstrip` 이 인자를 읽는 방식.\
  `".com"` 은 `{'.','c','o','m'}` 이고 **순서도 개수도 의미가 없다.**
- **`removeprefix` / `removesuffix`**: 접두사·접미사 **덩어리**를 딱 한 번 떼는 메서드(3.9+, PEP 616).\
  안 맞으면 원본 그대로를 돌려준다.
- **`find` 대 `index`**: 찾으면 둘이 같고 **못 찾을 때만** 갈린다. `-1` 대 `ValueError`.
- **줄바꿈(line boundary)**: `splitlines` 가 경계로 보는 글자.\
  `str` 은 11가지(`\n`·`\r`·`\r\n`·`\v`·`\f`·`\x1c`·`\x1d`·`\x1e`·`\x85`·`\u2028`·`\u2029`), `bytes` 는 3가지.
- **`partition`**: 처음 나오는 구분자에서 한 번 나눠 **(앞, 구분자, 뒤)** 3칸을 돌려주는 메서드.\
  못 찾아도 3칸이라 언패킹이 안전하다.
- **`str.maketrans`**: `translate` 가 쓸 표를 만드는 정적 메서드.\
  결과는 **코드 포인트를 키로 하는 dict** 이고 값이 `None` 이면 삭제다.
- **`isdecimal` / `isdigit` / `isnumeric`**: 유니코드의 `decimal`·`digit`·`numeric` 속성을 각각 되묻는 검사.\
  이 순서로 **넓어지고**, 셋 다 `int()` 가 받는 집합과는 다르다.
- **`casefold`**: 대소문자 구분을 **없앤 정규형**을 만드는 메서드. 비교용이지 표시용이 아니다.\
  `'ß'` 가 `'ss'` 가 되고 그리스어 `σ`/`ς` 가 합쳐진다.
- **caseless matching**: 대소문자를 무시한 일치 판정. 유니코드가 정의하는 절차이고 `casefold` 가 그 앞단이다.
- **탭 스톱(tab stop)**: `expandtabs(n)` 이 쓰는 기준. 탭을 **다음 `n` 의 배수 칸까지** 채운다 — 고정 개수가 아니다.
- **제곱 비용(quadratic cost)**: 불변 열을 반복해 이어 붙일 때 드는 비용.\
  문서가 *"quadratic runtime cost in the total sequence length"* 라고 적는다. `join` 이 그 해법이다.

## 더 들어가면

- **`str.format_map`** 은 `format(**d)` 와 달리 dict 를 **복사하지 않는다.** `defaultdict` 를 넘겨 빠진 키를 채우는 관용구가 여기서 나온다(08번 주제와 이어진다).
- **`str.maketrans` 로 서로게이트·제어문자를 한 번에 털 수 있다.** 출력 직전 방어선으로 쓸 수 있다([06번](../06-strings-bytes-unicode/2-summary.md)).
- **`bytes` 쪽에도 같은 이름의 메서드가 대부분 있다** — `b.split`·`b.strip`·`b.replace`. 다만 인자도 `bytes` 여야 하고 `splitlines` 의 목록이 짧다.
- **`str.encode` 이후의 정규화는 소용없다.** 정규화는 `str` 위에서만 뜻이 있다.
- **`re.split` 은 빈 매치에서 3.7 부터 동작이 바뀌었다.** 문자열 메서드에는 그런 판 차이가 거의 없다는 것이 이 계열의 장점이다(목록의 **46번 주제**).
