# python/syntax/07-string-methods — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 11개 = 답 11개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 단 **「같은 객체를 돌려주나」와 `center` 의 여분 칸 방향은 구현 세부사항**이라 다른 구현·다른 버전에서는 달라진다(6·10번 답).

## 정답

### 1. `strip` 은 문자 집합을 깎고 `removeprefix` 는 덩어리를 뗀다

**출력**

```text
'example'
'hell'
'ssiss'
'c' 'c'
'aa' ''
'example.com'
```

**왜 그런가**

문서가 직접 못 박는다 —\
*"The chars argument is a string specifying the **set of characters** to be removed... The chars argument is **not a prefix or suffix**; rather, all combinations of its values are stripped."*

```text
 "hello.com".rstrip(".com")   ->  집합은 { '.', 'c', 'o', 'm' }

  h  e  l  l  o  .  c  o  m
                          ^  'm' 있다 -> 깎는다
                       ^     'o' 있다 -> 깎는다
                    ^        'c' 있다 -> 깎는다
                 ^           '.' 있다 -> 깎는다
              ^              'o' 있다 -> ★ 이것까지 깎는다
           ^                 'l' 없다 -> 멈춘다

  결과 'hell'
```

**첫 줄이 「맞은 것처럼」 보이는 이유**

```text
 "example.com".strip(".com")

  e  x  a  m  p  l  e  .  c  o  m
                             ...  뒤에서 '.com' 을 다 깎고
                       ^          'e' 를 만난다 -> 'e' 는 집합에 없다 -> 멈춘다
  앞에서도 'e' 에서 바로 멈춘다

  결과 'example'   ★ 우연히 맞았다.
```

★ **끝 글자가 마침 집합 밖이라 멈췄을 뿐**이다.\
`"hello.com"` 은 끝이 `o` 라서 한 글자를 더 먹었다. **한 판의 테스트로는 이 버그가 안 드러난다.**

| | `strip(x)` | `removeprefix(x)` / `removesuffix(x)` |
|---|---|---|
| `x` 를 무엇으로 읽나 | **문자 집합** | **덩어리 하나** |
| 몇 번 지우나 | 더 못 지울 때까지 | **딱 한 번** |
| 안 맞으면 | 안 맞는 글자에서 멈춘다 | **원본 그대로** |
| 순서가 의미 있나 | ✗ (`"ab"` 과 `"ba"` 가 같다) | ✓ |

- 넷째 줄 `'c' 'c'` 가 **순서 무의미**의 증거다.
- 다섯째 줄에서 `removeprefix("a")` 는 `'aa'`(한 번), `lstrip("a")` 는 `''`(전부)다.
- 여섯째 줄 — 접미사가 안 맞으니 **원본 그대로**. `strip(".org")` 이었다면 `'example.c'` 가 됐을 것이다.

> **PEP 616** 이 이 메서드를 넣은 이유가 정확히 이 오해다. 제안서가 `"Bar.txt".rstrip(".txt")` 가 `'Ba'` 가 되는 것을 예로 든다.

### 2. `split()` 과 `split(sep)` 은 다른 알고리즘이다

**출력**

```text
['a', 'b'] ['', '', 'a', '', 'b', '', '']
[] ['']
['a', '', 'b']
['a', 'b', ''] ['a', 'b']
('kv', '', '') ('a', '=', 'b=c')
```

**왜 그런가**

문서가 **두 알고리즘**이라고 적는다 —\
*"If sep is not specified or is `None`, a **different splitting algorithm** is applied: runs of consecutive whitespace are regarded as a single separator, and the result will contain no empty strings at the start or end..."*

```text
 "  a  b  "

 split()              공백 덩어리를 하나로 보고, 양 끝은 버린다
   -> ['a', 'b']

 split(' ')           ' ' 하나하나가 전부 경계다
   -> ['', '', 'a', '', 'b', '', '']
      ^^^^^^^^      ^^        ^^^^^^^^
      앞 공백 2개가   사이 공백 2개    뒤 공백 2개가
      빈 칸 2개       중 하나가 빈 칸   빈 칸 2개
```

**「공백으로 나눈다」가 두 뜻인 이유**

| 뜻 | 도구 | 빈 칸이 나오나 |
|---|---|---|
| 「**단어들**을 뽑아라」 | `split()` | ✗ |
| 「**이 글자**를 경계로 잘라라」 | `split(" ")` | ✓ |

- ★ **빈 문자열에서 가장 크게 갈린다** — `[]` 대 `['']`.\
  문서도 따로 적는다 — *"splitting an empty string ... with a `None` separator returns `[]`."*
- `'a,,b'.split(',')` 이 `['a','','b']` 인 것도 같은 규칙 — *"consecutive delimiters ... are deemed to delimit empty strings."*
- 넷째 줄 — **`split("\n")` 은 끝에 빈 칸을 남기고 `splitlines` 는 안 남긴다.** 줄 수를 세면 하나가 어긋난다.
- 다섯째 줄 — `partition` 은 **못 찾아도 3칸**이다.

```text
 split(sep, 1)                partition(sep)
  못 찾으면 원소 1개             못 찾아도 3칸
  k, v = s.split("=", 1)       k, _, v = s.partition("=")
     ^ ValueError 가 날 수 있다    ^ 언제나 안전하다
```

### 3. `find` 의 반환값을 진릿값으로 쓰면 거꾸로다

**출력**

```text
'hello' 0 False True
'world' 6 True True
'zz' -1 True False
'' 0 False True
index: ValueError substring not found
2 5
```

**왜 그런가**

```text
 찾았다 (0번 자리)  ->  0   -> bool(0)  = False  ★
 찾았다 (6번 자리)  ->  6   -> bool(6)  = True
 못 찾았다         -> -1   -> bool(-1) = True   ★

  두 ★ 이 서로 반대다.
```

**어느 두 줄이 반대 답을 내나 — 첫 줄과 셋째 줄이다.**

| 줄 | 상황 | `find` | `bool(find)` | `in` | 어느 쪽이 맞나 |
|---|---|---|---|---|---|
| 1 | 0번 자리에서 **찾았다** | `0` | **`False`** | `True` | `in` |
| 2 | 6번 자리에서 찾았다 | `6` | `True` | `True` | 둘 다 |
| 3 | **못 찾았다** | `-1` | **`True`** | `False` | `in` |
| 4 | 빈 문자열(언제나 있다) | `0` | `False` | `True` | `in` |

★ **테스트 데이터가 앞자리를 피하면 통과해 버린다.** `"hello world"` 에서 `"world"` 를 찾는 예제만 쓰면 2번 줄만 보게 된다.

문서도 이 자리에 주를 단다 —\
*"The `find()` method should be used only if you need to know the position of sub. To check if sub is a substring or not, **use the `in` operator**."*

**`index` 는 흐름을 끊는다**

```text
 find  -> 값으로 돌려준다        -> if 로 감싸야 한다 (그리고 == -1 로 비교해야 한다)
 index -> 예외를 던진다          -> try 로 감싸거나, 없으면 버그인 곳에 쓴다
```

**마지막 줄 — `count` 는 겹치는 것을 안 센다**

```text
 "aaaa".count("aa")
   aaaa
   ^^      1개 찾고, 그 뒤부터 다시 본다
     ^^    2개
   -> 2   (겹쳐 세면 3인데)

 "aaaa".count("")
   _a_a_a_a_   글자 사이 3곳 + 양 끝 2곳 = 5
```

### 4. 세 검사는 포함 관계이고, `int()` 와는 다른 집합이다

**출력**

```text
'7' True True True True 7
'٧' True True True False 7
'²' False True True False ValueError
'½' False False True False ValueError
'Ⅳ' False False True False ValueError
'-7' False False False True -7
'7.5' False False False True ValueError
```

**왜 그런가**

```text
                 isnumeric  (가장 넓다 — 유니코드 numeric 속성)
      +--------------------------------------+
      |   ½  Ⅳ  〇  一  万                      |
      |   +------------------------------+   |
      |   |  isdigit  (digit 속성)         |   |
      |   |    ²  ³                       |   |
      |   |   +----------------------+   |   |
      |   |   | isdecimal (decimal)  |   |   |
      |   |   |   7   ٧               |   |   |
      |   |   +----------------------+   |   |
      |   +------------------------------+   |
      +--------------------------------------+

  ★ int() 가 받는 집합은 이 그림 어디에도 안 맞는다 —
    '٧' 은 받고 '²' 는 안 받고 '-7' 은 받는다.
```

문서의 세 정의가 그대로 근거다.

| 메서드 | 문서의 말 |
|---|---|
| `isdecimal` | *"Decimal characters are those that can be used to form numbers in base 10"* |
| `isdigit` | *"Digits include decimal characters and digits that need special handling, such as the compatibility superscript digits"* |
| `isnumeric` | *"all characters that have the **Unicode numeric value property**"* |

`unicodedata` 가 그 근거를 직접 답한다.

```python
import unicodedata
for c in ("7", "٧", "²", "½", "Ⅳ"):
    print(f"{c!r:6} {unicodedata.name(c):32} decimal={unicodedata.decimal(c, None)} digit={unicodedata.digit(c, None)} numeric={unicodedata.numeric(c, None)}")
```

```text
'7'    DIGIT SEVEN                      decimal=7 digit=7 numeric=7.0
'٧'    ARABIC-INDIC DIGIT SEVEN         decimal=7 digit=7 numeric=7.0
'²'    SUPERSCRIPT TWO                  decimal=None digit=2 numeric=2.0
'½'    VULGAR FRACTION ONE HALF         decimal=None digit=None numeric=0.5
'Ⅳ'    ROMAN NUMERAL FOUR               decimal=None digit=None numeric=4.0
```

**세 메서드는 이 세 속성을 되묻는 것**이다. 유니코드 DB 가 정본이고 파이썬은 조회만 한다.

**입력 검증에 무엇을 쓰나 — 셋 다 아니다**

★ 세 가지가 동시에 뒤집힌다.

1. **`'٧'`(아랍-인도 숫자 7)은 `isdecimal` 이 참이고 `int()` 도 `7` 을 준다.**\
   「ASCII 숫자만」이라는 검증을 `isdecimal` 로 짰으면 **통과한다.**
2. **`'-7'` 은 세 검사가 전부 거짓인데 `int()` 는 된다.** 부호를 안 본다.
3. **`'7.5'` 도 전부 거짓**이다. 실수는 이 계열로 못 받는다.

| 물으려는 것 | 쓸 것 |
|---|---|
| 「ASCII 숫자 글자만인가」 | `s.isdecimal() and s.isascii()` |
| 「정수로 쓸 수 있나」 | `try: int(s) except ValueError:` |
| 「실수로 쓸 수 있나」 | `try: float(s)` (또는 `Decimal(s)`) |
| 「돈 계산에 쓸 값인가」 | `Decimal(s)` 를 `InvalidOperation` 으로 감싼다([목록의 **50번 주제**](../50-decimal-float-precision-and-round/)) |

```text
 세 is* 검사                       int() 로 바꿀 수 있나
  글자 하나하나의 성질을 본다         부호·전후 공백까지 포함한 "문장" 을 본다
       |                                |
       +-- '٧' 통과, '-7' 탈락          +-- '٧' 통과, '-7' 통과
                                          ★ 두 집합이 포함 관계가 아니다
```

**한 줄로**: **형태를 물을 때만 `is*` 를 쓰고, 값으로 쓸 거면 변환을 시도한다.**

### 5. `casefold` 는 `lower` 의 강화판이 아니다

**출력**

```text
False
True
1 2 'ss'
1 2
'οδος' 'οδοσ'
"O'Neill"
```

**왜 그런가**

```text
 독일어 ß

   "straße"                     "STRASSE"
   .lower()  -> "straße"        .lower()  -> "strasse"
        +------- != -------+                  ★ lower 로는 안 맞는다

   .casefold() -> "strasse"     .casefold() -> "strasse"
        +------- == -------+                  ★ casefold 로는 맞는다
```

문서 —\
*"Casefolding is similar to lowercasing but **more aggressive** because it is intended to remove all case distinctions in a string."*

**셋째·넷째 줄 — 길이가 양쪽 방향으로 바뀐다**

```text
 'ß'          len 1  --upper-->  'SS'   len 2      ★ 커지면서 늘어난다
 'ß'.upper().lower() -> 'ss'                       ★ 왕복이 안 된다 (원 글자가 사라졌다)

 'İ'          len 1  --lower-->  'i' + 결합 점  len 2   ★ 작아지면서도 늘어난다
```

「대소문자 변환은 길이를 안 바꾼다」가 **양방향 모두 틀린다.**

**다섯째 줄이 「강화판이 아니다」의 핵심이다**

```text
 "ΟΔΟΣ"  (그리스어 대문자)

  .lower()    -> 'οδος'   ★ 마지막 시그마를 ς (final sigma) 로 바꾼다 = 문맥을 본다
  .casefold() -> 'οδοσ'   ★ 그 구분을 없앤다 = 비교용 정규형

  결과: σ.casefold() == ς.casefold()  -> True
        σ.lower()    == ς.lower()     -> False
```

| | `lower` | `casefold` |
|---|---|---|
| 목적 | **사람이 읽을 소문자** | **비교용 정규형** |
| 문맥 | 본다(단어 끝 시그마) | 안 본다 |
| `'ß'` | `'ß'` 그대로 | `'ss'` |
| 표시에 쓰나 | ✓ | ✗ (사람이 읽는 글이 아니다) |

★ **둘은 세기 차이가 아니라 목적 차이다.** 화면에 찍을 것은 `lower`, `dict` 키·비교는 `casefold`.\
그리고 [06번](../06-strings-bytes-unicode/2-summary.md)의 **정규화까지 같이 걸어야** 진짜 정규형이 된다.

**여섯째 줄 — `title()` 의 한계**

```python
print("o'neill".title(), "mcdonald's".title())
```

```text
O'Neill Mcdonald'S
```

아포스트로피 뒤를 **새 단어의 시작**으로 본다. 문서도 이 한계를 적고 정규식으로 대신하는 예를 싣는다.

### 6. 문자열은 불변 — 그런데 「언제나 새 객체」는 아니다

**출력**

```text
False
True
False
True
aaaa
baba
```

**왜 그런가**

```text
 s = "hello"

 s.replace("l","L")   바꿀 것이 있다  -> 새 문자열을 만든다   -> is s 가 False
 s.replace("z","Z")   바꿀 것이 없다  -> ★ 원본을 그대로 준다 -> is s 가 True
 s.upper().lower()    값은 같지만      -> 새 문자열 둘을 거쳤다 -> is s 가 False
 s[:]                 전체 슬라이스    -> ★ 원본을 그대로 준다 -> is s 가 True
```

- 값이 같다고 같은 객체가 되지는 않는다 — 셋째 줄이 그 증거다([02번](../02-is-vs-eq-interning/2-summary.md)).
- `s[0] = "H"` 는 `TypeError: 'str' object does not support item assignment` 다. **불변이라는 것이 여기서 드러난다.**

> ★ `is`/`id()` 가 답하는 것은 「**같은 객체인가**」이지 「어디에 있는가」가 아니다.
> `id()` 의 값이 메모리 주소라는 것은 CPython 구현 세부사항이다([02번](../02-is-vs-eq-interning/2-summary.md) 정본).

**어느 줄이 구현 세부사항인가 — 둘째와 넷째다**

| 줄 | 사실 | 층 |
|---|---|---|
| 1 | 바꾼 결과가 새 객체다 | **언어 보장**(불변이니 그럴 수밖에 없다) |
| 2 | **바꿀 것이 없으면 원본을 그대로 준다** | **구현 세부사항** — 문서가 약속하지 않는다 |
| 3 | 값이 같아도 다른 객체일 수 있다 | 언어 보장(인터닝은 보장이 아니다) |
| 4 | **`s[:]` 가 원본을 그대로 준다** | **구현 세부사항** |
| 5·6 | `replace` 는 순차, `translate` 는 한 번에 | **언어 보장**(정의가 그렇다) |

★ **`x is y` 가 참이 되는 것에 기대는 코드를 쓰면 안 된다.** PyPy·다음 판에서 달라질 수 있다.

**다섯째·여섯째 줄 — 맞바꾸기**

```text
 "abab" 에서 a 와 b 를 맞바꾸려면

  replace 두 번                        translate 한 번
   .replace("a","b") -> "bbbb"          maketrans("ab","ba")
      ★ 여기서 이미 정보가 사라졌다        한 번 훑으며 각 글자를 동시에 바꾼다
   .replace("b","a") -> "aaaa"          -> "baba"
```

### 7. `join` 이 왜 문자열의 메서드인가 (왜)

**핵심 한 줄**: **구분자 쪽에 두면 구현이 하나로 끝나고, 어떤 이터러블이든 받을 수 있다.**

```text
  리스트의 메서드였다면            문자열의 메서드라서
  ["a","b"].join(",")             ",".join(["a","b"])
       |                                |
   list·tuple·set·dict·            어떤 이터러블이든 받는다.
   제너레이터·range 가 각자          구분자 쪽에 구현 하나면 끝.
   join 을 구현해야 한다
```

```python
print(repr(",".join(["a", "b"])))
print(repr("-".join(str(i) for i in range(3))))
print(repr("-".join({"a": 1, "b": 2})))
print(repr("-".join("abc")))
print(b",".join([b"a", b"b"]))
```

```text
'a,b'
'0-1-2'
'a-b'
'a-b-c'
b'a,b'
```

- **제너레이터**도 받는다 — 리스트를 먼저 만들 필요가 없다.
- **dict** 를 주면 키가 나온다(`dict` 를 도는 것이 키를 도는 것이므로).
- **문자열**을 주면 글자가 나온다(`str` 도 이터러블이다).
- `bytes` 쪽에도 같은 메서드가 있고 **원소도 `bytes` 여야** 한다.

**어떤 인자를 거부하나**

```python
for bad in (["a", 1], [b"a"], ["a", None]):
    try:
        ",".join(bad)
    except TypeError as e:
        print(f"{bad!r:14} -> {e}")
```

```text
['a', 1]       -> sequence item 1: expected str instance, int found
[b'a']         -> sequence item 0: expected str instance, bytes found
['a', None]    -> sequence item 1: expected str instance, NoneType found
```

★ **문서가 `bytes` 를 명시적으로 거부 목록에 넣는다** —\
*"A TypeError will be raised if there are any non-string values in iterable, **including bytes objects**."*\
[06번](../06-strings-bytes-unicode/2-summary.md)의 벽이 여기서도 서 있다. 그리고 **몇 번째 원소인지**까지 알려 준다.

**그리고 `+=` 루프의 제곱 비용을 없앤다**

```text
 out = ""
 for x in items:              문자열은 불변이라
     out += x                 매번 새 문자열을 만들고 앞부분을 통째로 복사한다
                              -> 조각 수의 제곱에 가까운 비용

 "".join(items)               전체 길이를 먼저 재고 한 번에 만든다
                              -> O(전체 길이)
```

문서가 시퀀스 일반에 대해 같은 말을 한다 — *"building up a sequence by repeated concatenation will have a **quadratic runtime cost** in the total sequence length."*

### 8. `splitlines` 가 줄로 보는 것 (경계)

**`str` 은 11가지, `bytes` 는 3가지다.**

```python
names = {"\n": "\\n LF", "\r": "\\r CR", "\v": "\\v 수직탭", "\f": "\\f 폼피드",
         "\x1c": "\\x1c 파일 구분자", "\x85": "\\x85 NEL", "\t": "\\t 탭(비교용)"}
for ch, nm in names.items():
    s = "a" + ch + "b"
    b = ("a" + ch + "b").encode("utf-8")
    print(f"{nm:20} str={s.splitlines()!r:16} bytes={b.splitlines()!r}")
```

```text
\n LF                str=['a', 'b']       bytes=[b'a', b'b']
\r CR                str=['a', 'b']       bytes=[b'a', b'b']
\v 수직탭               str=['a', 'b']       bytes=[b'a\x0bb']
\f 폼피드               str=['a', 'b']       bytes=[b'a\x0cb']
\x1c 파일 구분자          str=['a', 'b']       bytes=[b'a\x1cb']
\x85 NEL             str=['a', 'b']       bytes=[b'a\xc2\x85b']
\t 탭(비교용)            str=['a\tb']         bytes=[b'a\tb']
```

| | `str.splitlines` | `bytes.splitlines` |
|---|---|---|
| 목록 | **11가지** — `\n` `\r` `\r\n` `\v` `\f` `\x1c` `\x1d` `\x1e` `\x85` `\u2028` `\u2029` | **3가지** — `\n` `\r` `\r\n` |
| 왜 | 유니코드가 정한 줄바꿈 전부 | 바이트 세계에는 유니코드 줄 구분자가 없다 |

**어떤 코드에서 드러나나 — 세 자리다.**

1. **같은 파일을 텍스트/바이너리로 읽으면 줄 수가 달라진다.**\
   `open(p, "rb").read().splitlines()` 와 `open(p).read().splitlines()` 가 다른 답을 낼 수 있다.
2. **사용자가 붙여넣은 텍스트에 `\x85`·`\u2028` 이 섞여 있으면** 한 줄이 두 줄로 쪼개진다.\
   JSON 은 `\u2028` 을 그대로 통과시키므로 웹 폼에서 실제로 들어온다.
3. **`split("\n")` 과 `splitlines` 의 끝 처리가 다르다.**

```python
print("a\nb\n".split("\n"), "a\nb\n".splitlines())
print("".splitlines(), "".split("\n"))
print("a\nb\r\nc".splitlines(True))
```

```text
['a', 'b', ''] ['a', 'b']
[] ['']
['a\n', 'b\r\n', 'c']
```

★ **줄을 세려면 `splitlines`, 바이트를 다룰 때는 그 목록이 짧다는 것을 기억한다.**\
`keepends=True` 는 **어느 줄바꿈이었는지**까지 보존한다 — CRLF/LF 를 구분해야 할 때 쓴다.

### 9. `translate` 가 `replace` 두 번과 다른 자리 (왜)

**핵심 한 줄**: **`replace` 는 결과를 다시 훑고, `translate` 는 한 번만 훑는다.**

```text
 "abab" 에서 a <-> b

 replace 두 번                        translate 한 번
  "abab"                               "abab"
   |  .replace("a","b")                  |  한 글자씩 표를 보며 동시에 바꾼다
   v                                     v
  "bbbb"   ★ 원래 b 였던 것과            "baba"
           새로 b 가 된 것이
           구별이 안 된다
   |  .replace("b","a")
   v
  "aaaa"
```

```python
print(repr("abab".replace("a", "b").replace("b", "a")))
print(repr("abab".translate(str.maketrans("ab", "ba"))))
```

```text
'aaaa'
'baba'
```

★ **첫 치환의 결과가 두 번째 치환의 입력**이 된다. 정보가 한 번 뭉개지면 되돌릴 수 없다.

**`maketrans` 가 만드는 표의 키는 코드 포인트(정수)다**

```python
print(str.maketrans("abc", "xyz"))
print(str.maketrans({"a": "[에이]", 0x62: None}))
print(str.maketrans("", "", "aeiou"))
```

```text
{97: 120, 98: 121, 99: 122}
{97: '[에이]', 98: None}
{97: None, 101: None, 105: None, 111: None, 117: None}
```

★ **키가 `'a'` 가 아니라 `97` 이다.** [06번](../06-strings-bytes-unicode/2-summary.md)의 「`str` 은 코드 포인트 열」이 여기서 그대로 드러난다.

| 값 | 뜻 |
|---|---|
| 정수 | 그 코드 포인트의 글자로 바꾼다 |
| 문자열 | 그 문자열로 바꾼다 — **여러 글자여도 된다**(1:N) |
| `None` | **지운다** |

```python
print(repr("beautiful".translate(str.maketrans("", "", "aeiou"))))
print(repr("abc".translate(str.maketrans({"a": "[에이]", 0x62: None}))))
```

```text
'btfl'
'[에이]c'
```

**비용 비교**

| | `replace` | `translate` |
|---|---|---|
| 단위 | **부분 문자열**(여러 글자 가능) | **글자 하나**(키가 코드 포인트다) |
| 여러 개 | 호출을 여러 번 — **결과가 다시 입력이 된다** | 표 하나로 한 번에 |
| 삭제 | `replace(x, "")` | 값을 `None` 으로 |
| 훑는 횟수 | 호출 수만큼 | **한 번** |

★ **덩어리 치환은 `replace`, 글자 단위 다중 치환·삭제·맞바꾸기는 `translate`** 다.

### 10. 세 층 가르기 (경계)

**언어 보장** — 문서 문장으로 확인한 것.

| 사실 | 근거 |
|---|---|
| `strip` 의 인자는 **문자 집합**이고 접두사·접미사가 아니다 | String Methods — *"not a prefix or suffix"* |
| `removeprefix`/`removesuffix` 는 **조건 하나**로 정의된다 | String Methods (3.9+, PEP 616) |
| `find` 는 못 찾으면 `-1`, `index` 는 `ValueError` | String Methods |
| 「있나」만 물으려면 `in` 을 쓰라 | String Methods 의 `find` 주석 |
| `split()` 은 **다른 알고리즘**이고 빈 문자열을 안 남긴다 | String Methods |
| `split(sep)` 은 연속 구분자를 묶지 않는다 | String Methods |
| `splitlines` 가 줄바꿈으로 보는 **11가지** 목록 | String Methods 의 표 |
| `join` 은 구분자의 메서드이고 `bytes` 를 포함한 비-`str` 은 `TypeError` | String Methods |
| `isdecimal` ⊂ `isdigit` ⊂ `isnumeric` | String Methods 각 항목 + 유니코드 속성 |
| `casefold` 는 **caseless matching** 용이고 `lower` 보다 공격적 | String Methods |
| `center` 는 `width` 가 `len(s)` 이하면 **원본을 돌려준다** | String Methods |
| 불변 열을 반복 이어 붙이면 **제곱 비용** | Common Sequence Operations |

**CPython 구현 세부사항** — 실행으로 확인한 것.

| 사실 | 어떻게 확인했나 |
|---|---|
| `replace` 가 **바꿀 것을 못 찾으면 원본 객체를 그대로** 돌려준다 | `s.replace("z","Z") is s` 가 `True` |
| `s[:]` 가 **원본 객체를 그대로** 돌려준다 | `s[:] is s` 가 `True` |
| `maketrans` 의 결과가 **코드 포인트를 키로 하는 dict** 다 | `{97: 120, 98: 121, 99: 122}` |
| `join` 의 `TypeError` 가 **몇 번째 원소인지** 알려 준다 | `sequence item 1: ...` |

**이 판(3.12.3)의 관찰** — 버전이 오르면 다시 찍어야 하는 것.

| 관찰 | 어디가 흔들리나 |
|---|---|
| **`center` 는 여분 칸을 왼쪽에, 포맷 스펙 `^` 는 오른쪽에 둔다** | **문서가 어느 쪽도 정하지 않는다** |
| `isdecimal`/`isdigit`/`isnumeric` 의 글자별 답 | **유니코드 DB 판**(`15.0.0`)에 달렸다 |
| `'ΟΔΟΣ'.lower()` 가 final sigma 를 쓰는 것 | 유니코드의 특수 케이스 매핑 표 |
| `'İ'.lower()` 가 길이 2 가 되는 것 | 〃 |
| 예외 문구 전부 | 예외 종류는 명세지만 문구는 아니다 |

**그 관찰을 다시 재 본 것**

```python
for s in ("a", "ab", "abc"):
    for w in range(len(s) + 1, len(s) + 5):
        c, f = s.center(w, "*"), format(s, "*^" + str(w))
        if c != f:
            print(f"{s!r} width={w}: center={c!r}  format^={f!r}")
```

```text
'ab' width=3: center='*ab'  format^='ab*'
'ab' width=5: center='**ab*'  format^='*ab**'
```

★ **`len(s)` 가 짝수이고 `width` 가 홀수일 때만 갈린다.** 표를 두 도구로 섞어 그리면 한 칸이 어긋난다.

**그래서 이렇게 적으면 틀린다**

- ✗ 「`strip(".com")` 은 `.com` 을 뗀다」 → ○ **문자 집합을 양 끝에서 계속 깎는다.**
- ✗ 「`find` 가 0 이 아니면 찾은 것이다」 → ○ `0` 이 「**0번 자리에서 찾았다**」다.
- ✗ 「`split()` 과 `split(' ')` 은 같다」 → ○ **다른 알고리즘**이다.
- ✗ 「`splitlines` 는 `\n` 과 `\r\n` 을 나눈다」 → ○ **11가지**다(`bytes` 는 3가지).
- ✗ 「`isdigit()` 이면 `int()` 가 된다」 → ○ **포함 관계가 아니다.**
- ✗ 「`casefold` 는 `lower` 의 강화판」 → ○ **목적이 다르다.**
- ✗ 「문자열 메서드는 언제나 새 객체를 준다」 → ○ 바뀔 것이 없으면 원본을 준다 — **구현 세부사항**이다.
- ✗ 「`center(n)` 과 `format(s,'^n')` 은 같다」 → ○ **여분 칸의 방향이 갈린다.**

> **구현 세부사항(implementation detail)** — 언어 명세가 보장하지 않고 특정 구현이 그렇게 만들어 둔 것.\
> 여기서는 객체 재사용과 여분 칸 방향이 그것이다.

**판정 기준 한 줄**

**메서드에 문자열을 인자로 넘기고 있다면, 그것이 「덩어리」인지 「문자 집합」인지부터 확인하라.**

### 11. 정규식을 꺼내는 선 (연결)

**기준 한 줄**: **찾는 것이 「고정된 글자」면 메서드, 「모양」이면 정규식이다.**

| 이걸로 된다 | 정규식이 필요하다 |
|---|---|
| 고정 문자열 찾기(`in`·`find`) | **패턴**(숫자 3자리·단어 경계·대소문자 무시 매칭) |
| 구분자 하나로 나누기(`split`) | **여러 구분자**·구분자가 패턴 |
| 접두·접미 판정(`startswith` 튜플) | 접두사가 패턴 |
| 글자 단위 치환(`translate`) | 문맥에 따른 치환·역참조 |
| 덩어리 치환(`replace`) | 매치의 일부를 **뽑아 쓰는** 치환 |

**메서드별로 넘어가는 구체적 조건**

```text
 strip(chars)
   된다: 양 끝의 "이 글자들" 을 깎는다
   넘어간다: 양 끝의 "패턴" 을 떼야 한다 (예: 끝의 숫자 몇 자리)
             -> re.sub(r"\d+$", "", s)

 split(sep)
   된다: 구분자가 글자 하나 또는 고정 문자열 하나
   넘어간다: 구분자가 여럿이거나 (",", ";", 공백 전부)
             구분자 자체가 모양이다
             -> re.split(r"[,;\s]+", s)

 replace(old, new)
   된다: 바꿀 것이 고정 문자열
   넘어간다: 바꿀 것이 모양이거나, 바꾼 결과가 원래 값에 달렸다
             -> re.sub(r"(\d{4})-(\d{2})", r"\2/\1", s)
```

**★ 그런데 먼저 물어야 할 것이 하나 더 있다**

```text
 "이 데이터에 이미 파서가 있나?"

   CSV      -> csv 모듈       (따옴표 안의 쉼표를 split 은 모른다)
   JSON     -> json 모듈
   URL      -> urllib.parse
   HTML     -> 파서 라이브러리 (정규식으로 하면 안 된다)
   이메일   -> email 모듈
   경로     -> pathlib

  ★ 정규식은 "파서가 없을 때" 의 도구다. 있으면 그것을 쓴다.
```

```python
line = 'a,"b,c",d'
print("split 으로:", line.split(","))
import csv, io
print("csv 로    :", next(csv.reader(io.StringIO(line))))
```

```text
split 으로: ['a', '"b', 'c"', 'd']
csv 로    : ['a', 'b,c', 'd']
```

★ **따옴표 안의 쉼표에서 `split` 이 무너진다.** 정규식으로도 제대로 하기 어렵다 — **파서를 쓴다.**

**세 단계로 정리하면**

```text
 1단계  파서가 있나?          -> 있으면 그것 (csv·json·urllib·email·pathlib)
 2단계  찾는 것이 고정 글자인가? -> 예: 문자열 메서드
 3단계  모양인가?             -> 예: re  ([목록의 **46번 주제**](../46-re/))
```

**한 문장으로**

**문자열 메서드는 「글자」를 다루고 정규식은 「모양」을 다룬다.**\
그리고 그 위에 **「형식」을 다루는 파서**가 따로 있다 — 셋을 섞으면 각각의 실패 모드가 겹친다.

---

## 실행 검증

이 파일에 실린 출력은 전부 아래 환경에서 직접 돌려 얻었다.

```text
$ python3 --version
Python 3.12.3
$ python3 -c "import unicodedata; print(unicodedata.unidata_version)"
15.0.0
```

| 문항 | 무엇을 돌렸나 | 몇 번 |
|---|---|---|
| 1 | `strip` 6식 + `removeprefix`/`removesuffix` 4식 | 각 1회 |
| 2 | `split`/`splitlines`/`partition` 11식, `split("")` 예외 | 각 1회 |
| 3 | `find` 4개 needle × (값·진릿값·`in`), `index` 예외, `count` 2식 | 각 1회 |
| 4 | 7글자 × (`isdecimal`·`isdigit`·`isnumeric`·`isascii`·`int`), `unicodedata` 3속성 | 각 1회 |
| 5 | `lower`/`casefold` 대조, 길이 변화 4글자, 시그마 2식, `title` 2식 | 각 1회 |
| 6 | `is` 4식, `replace` 2연·`translate` 대조, `s[0]=` 예외 | 각 1회 |
| 7 | `join` 5식 + 거부 3종 | 각 1회 |
| 8 | 줄바꿈 후보 7종을 `str`/`bytes` 양쪽에서, 끝 처리 3식 | 각 1회 |
| 9 | `maketrans` 3형태, `translate` 3식 | 각 1회 |
| 10 | **`center` 대 `format ^` 를 3문자열 × 4폭 = 12조합 전수** | 1회(12조합) |
| 11 | `split` 대 `csv.reader` 대조 | 각 1회 |

**★ 한 판으로 결론이 안 나는 것을 여러 판 던진 자리**

- **1번** — `"example.com".strip(".com")` 하나만 재면 **맞는 것처럼 보인다.**\
  `"hello.com".rstrip(".com")` 을 나란히 놓아야 「문자 집합」이 드러난다.
- **3번** — `"world"`(6번 자리)만으로 재면 `bool(find)` 가 맞게 보인다.\
  **0번 자리에 있는 `"hello"` 와 없는 `"zz"` 를 같이** 넣어야 뒤집힘이 보인다.
- **10번** — `'a'` 로만 재면 `center` 와 `format ^` 가 **네 폭 전부 같다.**\
  `'ab'`(길이 짝수)를 홀수 폭으로 재야 갈린다. **12조합을 전수로 돌려서 찾았다.**
- **5번** — `'ß'` 만 재면 「대소문자가 길이를 늘린다」로 끝난다.\
  `'İ'` 를 같이 재야 **줄이는 쪽으로도 늘어난다**는 것이 보인다.

**「에러가 정보인」 자리**

- 2번 — `split("")` 의 `ValueError: empty separator` 가 「글자별로 쪼개기는 이 메서드가 아니다」의 근거다.
- 7번 — `join` 의 `TypeError` 문구가 **`bytes` 를 명시적으로 거부한다**는 문서 문장의 실행 증거다.
- 6번 — `s[0] = "H"` 의 `TypeError` 가 불변의 증거다.

**구현 의존 항목 — 버전이 오르면 다시 찍을 것**

| 다시 찍을 것 | 왜 |
|---|---|
| 6번의 `is` 결과 2개(`replace` 무변화·`s[:]`) | 문서가 약속하지 않는다 |
| 10번의 `center` 대 `format ^` | 문서가 어느 쪽도 정하지 않는다 |
| 4번의 글자별 판정 | 유니코드 DB 판에 달렸다 |
| 5번의 시그마·`'İ'` 결과 | 〃 |
| 예외 **문구** 전부 | 예외 종류는 명세지만 문구는 아니다 |

나머지(`strip` 의 문자 집합 의미, `find`/`index` 의 실패 동작, `split` 두 알고리즘, `splitlines` 의 목록,
`join` 의 계약, 세 `is*` 의 포함 관계, `casefold` 의 목적, `translate` 의 1회 순회)는 **언어 보장**이므로
어떤 구현에서도 같아야 한다.
