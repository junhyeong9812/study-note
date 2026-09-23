# python/syntax/06-strings-bytes-unicode — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [Text Sequence Type — str](https://docs.python.org/3.12/library/stdtypes.html#text-sequence-type-str) — `str` 의 정의
> - [Binary Sequence Types — bytes, bytearray, memoryview](https://docs.python.org/3.12/library/stdtypes.html#binary-sequence-types-bytes-bytearray-memoryview) — `bytes`/`bytearray` 의 정의
> - [codecs — Error Handlers](https://docs.python.org/3.12/library/codecs.html#error-handlers) — 에러 핸들러 표
> - [`unicodedata`](https://docs.python.org/3.12/library/unicodedata.html) — 정규화 네 형태
> - [`sys.getsizeof`](https://docs.python.org/3.12/library/sys.html#sys.getsizeof) · [`sys.maxunicode`](https://docs.python.org/3.12/library/sys.html#sys.maxunicode)
> - [PEP 393 — Flexible String Representation](https://peps.python.org/pep-0393/) — 내부 표현이 세 갈래인 이유
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> **버전** — `str`/`bytes` 의 분리는 Python 3 전체 공통. `sys.getsizeof` 의 **구체적 바이트 수**는 이 판의 관찰이다.
> 유니코드 데이터베이스는 이 설치본에서 `unicodedata.unidata_version` 이 `15.0.0` 이다.
> **선행** — [01-object-and-name-binding](../01-object-and-name-binding/2-summary.md)(이름 바인딩 정본) · [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md)(인터닝 정본 — 문자열이 언제 같은 객체가 되나).

## 한눈에 — 쉽게 말하면

**`str` 은 「글자 번호의 줄」이고 `bytes` 는 「숫자 0\~255 의 줄」이다. 둘 사이를 건너는 다리가 인코딩이다.**

```text
        str                       encode(인코딩)              bytes
  "가A"  = 글자 번호의 줄      ---------------------->    0~255 짜리 숫자의 줄
                              <----------------------
                                 decode(인코딩)

  [ 44032 ,  65 ]              utf-8 로 건너면     [ 234, 176, 128, 65 ]
    '가'     'A'                                     <--- 3개 --->  <1개>
   len = 2                                             len = 4

  ★ 같은 두 글자인데 왼쪽은 2, 오른쪽은 4다.
    "몇 글자인가" 와 "몇 바이트인가" 는 다른 질문이다.
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 글자마다 붙은 만국 공통 번호 | 코드 포인트 | `ord('가')` 가 `44032` |
| 번호를 우편으로 부칠 때 쓰는 봉투 규격 | 인코딩(utf-8·euc-kr…) | 같은 글자가 규격마다 바이트 수가 다르다 |
| 봉투에 담긴 종이 | `bytes` | 원소를 꺼내면 **정수**가 나온다 |
| 봉투를 뜯어 읽은 글 | `str` | 원소를 꺼내면 길이 1짜리 `str` |
| 규격을 잘못 알고 뜯기 | 인코딩 불일치 | 에러가 나거나 **조용히 글자가 바뀐다** |
| 지우개로 고칠 수 있는 종이 | `bytearray` | 원소 대입이 된다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 하나로 굳어 있다.\
파일·소켓·HTTP 본문·DB 드라이버는 전부 **`bytes` 를 준다.** 그것을 `str` 로 받았다고 착각하는 순간
`b'a' + 'a'` 에서 `TypeError` 가 나거나, 더 나쁘게는 `b'a' == 'a'` 가 **에러 없이 `False`** 가 된다.

> **코드 포인트(code point)** — 유니코드가 글자마다 매겨 둔 번호 하나.\
> 예: `'A'` 는 65, `'가'` 는 44032, `'👍'` 는 128077. `ord()` 가 이 번호를 준다.

> **인코딩(encoding)** — 코드 포인트를 실제 바이트로 옮겨 적는 규칙.\
> 예: `'가'` 는 utf-8 에서 3바이트, euc-kr 에서 2바이트, utf-32 에서 4바이트다.

## 이 주제가 답하려는 질문

1. **`len()` 이 무엇을 세는가** — 글자인가 바이트인가 화면에 보이는 칸인가. 셋이 다 다른 답을 낸다.
2. **`str` 과 `bytes` 를 섞으면 무엇이 일어나는가** — 어디서 터지고 어디서 조용히 틀리는가.
3. **눈에 똑같은 두 문자열이 `==` 로 다를 수 있는가** — 정규화가 그 자리다.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### 1. `str` 은 코드 포인트 열이다 — 바이트가 아니다

**언제 쓰나** — 문자열을 다루는 모든 자리. 이 한 문장이 이 주제 전체의 뿌리다.

문서의 정의 한 줄이 전부다 —\
*"Textual data in Python is handled with `str` objects, or strings. Strings are immutable **sequences of Unicode code points**."*

그리고 짝이 되는 정의 —\
*"Bytes objects are immutable sequences of **single bytes**."*

```text
 str "가A"                          bytes b'\xea\xb0\x80A'
  +-------+-------+                  +-----+-----+-----+-----+
  | 44032 |   65  |                  | 234 | 176 | 128 |  65 |
  +-------+-------+                  +-----+-----+-----+-----+
    '가'     'A'                       <--- '가' --->   'A'
  len = 2                             len = 4

  s[0] -> '가'  (길이 1 짜리 str)      b[0] -> 234   (정수!)
                                       b[0:1] -> b'\xea'  (bytes)
```

```python
s = "가A"
b = s.encode("utf-8")
print("s        =", repr(s), "len =", len(s))
print("b        =", b, "len =", len(b))
print("s[0]     =", repr(s[0]), type(s[0]).__name__)
print("b[0]     =", b[0], type(b[0]).__name__)
print("b[0:1]   =", b[0:1], type(b[0:1]).__name__)
print("list(s)  =", list(s))
print("list(b)  =", list(b))
```

```text
s        = '가A' len = 2
b        = b'\xea\xb0\x80A' len = 4
s[0]     = '가' str
b[0]     = 234 int
b[0:1]   = b'\xea' bytes
list(s)  = ['가', 'A']
list(b)  = [234, 176, 128, 65]
```

그림 해설.

- **같은 내용인데 `len` 이 2 와 4 다.** 왼쪽은 글자를 세고 오른쪽은 바이트를 센다.
- ★ **`bytes` 는 인덱싱하면 정수가 나오고 슬라이싱하면 `bytes` 가 나온다.**\
  문서가 이것을 따로 못 박는다 — *"Since bytes objects are sequences of integers (akin to a tuple), for a bytes object b, `b[0]` will be an integer, while `b[0:1]` will be a bytes object of length 1. (This contrasts with text strings, where both indexing and slicing will produce a string of length 1)"*
- `for` 로 `bytes` 를 돌면 **정수가 나온다.** 여기서 `c.isdigit()` 같은 것을 부르면 `AttributeError` 다.

**bytes 리터럴에는 ASCII 만 들어간다**

```python
x = b"가"
```

```text
  File "ex.py", line 1
    x = b"가"
        ^^^^
SyntaxError: bytes can only contain ASCII literal characters
```

문서가 그대로 적는다 — *"Only ASCII characters are permitted in bytes literals (regardless of the declared source code encoding)."*\
한글 바이트를 소스에 쓰려면 `b'\xea\xb0\x80'` 처럼 **이스케이프**로 쓴다.

**비용** — 코드 포인트 열이라서 인덱스가 **글자 단위로** 맞는다. 자바·자바스크립트가 UTF-16 코드 유닛을 세는 것과 다르다.\
대신 **파일·소켓에서 온 것을 쓰려면 반드시 한 번 `decode` 해야 한다.** 그 자리가 이 주제의 사고 지점이다.

### 2. `len()` 이 세는 것 — 코드 포인트다, 보이는 칸이 아니다

**언제 쓰나** — 글자 수 제한·잘라내기·정렬 폭 맞추기. 전부 이 오해 위에서 틀린다.

```text
 "café" 를 만드는 두 방법

 (A) 미리 합쳐진 글자 하나        (B) e + 덧붙이는 악센트
   c   a   f   é                  c   a   f   e   ́
   |   |   |   |                  |   |   |   |   |
  99  97 102 233                 99  97 102 101  769
   len = 4                        len = 5

  화면에는 둘 다 café 로 보인다.        ★ == 는 False 다.
```

```python
import unicodedata
nfc = "caf\u00e9"        # é 하나
nfd = "cafe\u0301"       # e + 결합 악센트
print("보이는 것:", nfc, nfd)
print("len      :", len(nfc), len(nfd))
print("==       :", nfc == nfd)
print("코드포인트:", [hex(ord(c)) for c in nfd])
print("한글:", len("한글"), "| 이모지:", len("👍"), "| 가족:", len("👨‍👩‍👧"), "| 국기:", len("🇰🇷"))
print("가족 이모지 속:", [hex(ord(c)) for c in "👨‍👩‍👧"])
```

```text
보이는 것: café café
len      : 4 5
==       : False
코드포인트: ['0x63', '0x61', '0x66', '0x65', '0x301']
한글: 2 | 이모지: 1 | 가족: 5 | 국기: 2
가족 이모지 속: ['0x1f468', '0x200d', '0x1f469', '0x200d', '0x1f467']
```

그림 해설.

- **한글 `"한글"` 은 2 다.** 바이트로는 utf-8 에서 6 이지만 `len` 은 글자를 센다.
- **이모지 `"👍"` 는 1 이다.** 자바스크립트에서 `"👍".length` 가 2 인 것과 다르다 — 파이썬은 코드 유닛이 아니라 **코드 포인트**를 센다.
- ★ **가족 이모지는 5 다.** 사람 셋 사이에 `U+200D`(ZERO WIDTH JOINER)가 둘 끼어 있다.\
  **화면의 한 칸이 코드 포인트 다섯**이다. `len` 은 이것을 하나로 세지 않는다.
- ★ **국기는 2 다.** 지역 표시 기호 두 개(`🇰` + `🇷`)의 조합이다.

**그래서 자르면 글자가 깨진다**

```python
fam = "👨‍👩‍👧"
print("앞 3 코드포인트:", fam[:3])
print("앞 1 코드포인트:", fam[:1])
print("결합 문자를 자르면:", repr("cafe\u0301"[:4]), "cafe\u0301"[:4])
```

```text
앞 3 코드포인트: 👨‍👩
앞 1 코드포인트: 👨
결합 문자를 자르면: 'cafe' cafe
```

- 가족 이모지를 3에서 자르면 **부부 이모지**가 된다. 5에서 잘라야 가족이다.
- `"cafe\u0301"` 을 4에서 자르면 악센트가 떨어져 `cafe` 가 된다 — **글자가 하나 바뀐 것**이지 잘린 것이 아니다.

**「보이는 칸」을 세려면 파이썬 표준 라이브러리로는 부족하다**

```python
import unicodedata
s = "cafe\u0301"
print("len              :", len(s))
print("결합 문자를 뺀 수  :", sum(1 for c in s if not unicodedata.combining(c)))
print("NFC 로 먼저 모으면 :", len(unicodedata.normalize("NFC", s)))
print("east_asian_width :", [unicodedata.east_asian_width(c) for c in "가aＡ"])
print("한글을 1 로 세면   :", len("가나".ljust(6, ".")), repr("가나".ljust(6, ".")))
```

```text
len              : 5
결합 문자를 뺀 수  : 4
NFC 로 먼저 모으면 : 4
east_asian_width : ['W', 'Na', 'F']
한글을 1 로 세면   : 6 '가나....'
```

★ **세 가지가 전부 다른 질문이다.**

| 묻는 것 | 도구 | `"cafe\u0301"` 의 답 |
|---|---|---|
| 코드 포인트가 몇 개인가 | `len()` | 5 |
| 사람이 보는 글자가 몇 개인가 | `unicodedata.combining` 으로 걸러야 한다 | 4 |
| 터미널에서 몇 칸을 먹는가 | `unicodedata.east_asian_width` | `'W'`/`'F'` 는 2칸 |

`"가나".ljust(6)` 이 터미널에서 **8칸**을 먹는데 파이썬은 6 이라고 답한다 —\
표를 한글로 정렬해 보면 어긋나는 것이 바로 이 자리다.

**비용** — 코드 포인트 세기는 O(1) 이고(길이가 저장돼 있다) 어떤 언어에서든 같은 답이다.\
대신 **「사용자가 세는 글자」와 다르다.** 글자 수 제한·미리보기 자르기를 `len` 으로 하면 이모지에서 깨진다.

### 3. 정규화 — 눈에 같은데 `==` 가 다르다고 한다

**언제 쓰나** — 사용자 입력·파일 이름·검색어를 비교·저장할 때. macOS 에서 온 파일 이름이 대표다.

문서의 정의 —\
*"For each character, there are two normal forms: normal form C and normal form D. Normal form D (NFD) is also known as canonical decomposition... Normal form C (NFC) first applies a canonical decomposition, then composes pre-combined characters again."*

```text
        NFD (풀어 쓴 것)            NFC (합쳐 쓴 것)
          e + ́                        é
        [101, 769]                   [233]
            \                         /
             \      normalize        /
              +---------------------+
                   같아진다

  ★ normalize 를 안 거치면 ==, in, dict, set, sort 가 전부 둘을 다른 것으로 본다.
```

```python
import unicodedata
a = "\u00e9"        # NFC
b = "e\u0301"       # NFD
print("보이는 것:", a, b, "| ==:", a == b, "| len:", len(a), len(b))
print("정규화 후 ==:", unicodedata.normalize("NFC", b) == a)
print("in 도 안 본다:", b in [a], a in [b])
d = {a: "NFC 로 넣은 값"}
print("dict 조회 :", d.get(b, "못 찾음"))
print("set 크기  :", len({a, b}))
print("sort 순서 :", [hex(ord(c)) for c in sorted([b, a])[0]])
```

```text
보이는 것: é é | ==: False | len: 1 2
정규화 후 ==: True
in 도 안 본다: False False
dict 조회 : 못 찾음
set 크기  : 2
sort 순서 : ['0x65', '0x301']
```

그림 해설.

- ★ **`==` 는 정규화를 전혀 보지 않는다.** 코드 포인트 열을 그대로 비교할 뿐이다.
- 그래서 **`dict` 가 못 찾고, `set` 이 중복을 못 걸러내고, `sort` 가 엉뚱한 자리에 놓는다.**\
  위 `sort` 결과에서 NFD 판(`0x65` = `'e'`)이 NFC 판(`0xe9`)보다 앞에 왔다 — **보이는 것은 같은 글자인데** 정렬 순서가 다르다.
- 고치는 법은 **저장·비교 직전에 한쪽 형태로 모으는 것**이다. 웹·리눅스는 보통 NFC 를 쓴다.

**K 가 붙은 두 형태는 글자를 바꿔 버린다**

```python
import unicodedata
for s in ("½", "Ⅳ", "ﬁ", "²"):
    print(f"{s!r:6} NFC={unicodedata.normalize('NFC', s)!r:8} NFKC={unicodedata.normalize('NFKC', s)!r}")
```

```text
'½'    NFC='½'      NFKC='1⁄2'
'Ⅳ'    NFC='Ⅳ'      NFKC='IV'
'ﬁ'    NFC='ﬁ'      NFKC='fi'
'²'    NFC='²'      NFKC='2'
```

문서가 갈라 둔다 — NFC/NFD 는 **표준 동치**(canonical equivalence), NFKC/NFKD 는 **호환 동치**(compatibility equivalence)다.\
★ **NFKC 는 「같은 글자를 모으는」 것이 아니라 「비슷한 글자를 갈아치우는」 것**이다.\
`'Ⅳ'`(로마 숫자 한 글자)가 `'IV'`(라틴 문자 두 개)가 되고 길이가 1 에서 2 로 늘어난다.\
검색 색인에는 쓸 만하지만 **원본 보존에는 쓰면 안 된다.**

**비용** — 정규화하면 비교·조회가 사람의 직관과 맞는다.\
대신 **정규화는 문자열을 새로 만드는 일**이고(O(n)), 어떤 형태를 정본으로 삼을지 **팀이 정해 놓아야** 한다.

### 4. `sys.getsizeof` 가 내부 표현을 드러낸다

**언제 쓰나** — 「왜 같은 글자 수인데 메모리가 다르지?」를 물을 때. 그리고 이 갈래의 「관찰」 층을 배울 때.

★ 먼저 문서가 물러선 자리를 읽는다 —\
*"Return the size of an object in bytes... this does not have to hold true for third-party extensions as it is **implementation specific**."*\
**이 절의 모든 숫자는 「언어 보장」이 아니라 「이 판의 관찰」이다.**

```python
import sys
for n in (10, 11):
    print(f"ascii {n}글자: {sys.getsizeof('a'*n):4}   한글 {n}글자: {sys.getsizeof('한'*n):4}   이모지 {n}글자: {sys.getsizeof('👍'*n):4}")
```

```text
ascii 10글자:   51   한글 10글자:   78   이모지 10글자:  100
ascii 11글자:   52   한글 11글자:   80   이모지 11글자:  104
```

```text
 한 글자 늘릴 때 늘어나는 바이트

   ascii 만 든 문자열   ->  +1 바이트/글자
   한글이 섞인 문자열    ->  +2 바이트/글자
   이모지가 섞인 문자열  ->  +4 바이트/글자

 ★ 파이썬은 문자열마다 "가장 큰 코드 포인트" 를 보고
   1 / 2 / 4 바이트 중 하나를 고른다 (PEP 393).
```

**한 글자만 섞여도 문자열 전체가 넓어진다**

```python
import sys
print("'a'*100        :", sys.getsizeof("a"*100))
print("'a'*99 + '한'   :", sys.getsizeof("a"*99 + "한"))
print("'a'*99 + '👍'   :", sys.getsizeof("a"*99 + "👍"))
```

```text
'a'*100        : 141
'a'*99 + '한'   : 258
'a'*99 + '👍'   : 460
```

그림 해설.

- **100 글자 중 99 개가 ASCII 인데도** 이모지 하나 때문에 460 바이트다. 칸 폭은 **글자마다가 아니라 문자열 전체에 한 번** 정해진다.
- 이것이 PEP 393 의 「유연한 문자열 표현」이다 — 최대 코드 포인트에 따라 `Py_UCS1`/`Py_UCS2`/`Py_UCS4` 중 하나를 고른다.
- ★ **이 숫자들은 전부 CPython 의 것**이다. PyPy·Jython 은 다른 답을 낸다.

**★ 여기서 한 자리가 어긋났다 — 한 글자짜리는 재면 안 된다**

```python
import sys
print("latin1 1글자:", sys.getsizeof("\u00e9"))
print("latin1 2글자:", sys.getsizeof("\u00e9\u00e9"))
print("latin1 3글자:", sys.getsizeof("\u00e9\u00e9\u00e9"))
print()
print("chr(0xe9) 가 같은 객체인가 :", chr(0xe9) is chr(0xe9))
print("chr(0xac00) 한글 한 글자   :", chr(0xac00) is chr(0xac00))
print("chr(97) ascii 한 글자      :", chr(97) is chr(97))
```

```text
latin1 1글자: 61
latin1 2글자: 59
latin1 3글자: 60

chr(0xe9) 가 같은 객체인가 : True
chr(0xac00) 한글 한 글자   : False
chr(97) ascii 한 글자      : True
```

★ **1글자가 2글자보다 크다.** 규칙이 깨진 것처럼 보이지만 원인은 다른 데 있다 —\
**코드 포인트 0\~255 짜리 한 글자 문자열은 인터프리터가 미리 만들어 두고 돌려쓰는 싱글턴**이고,
그 싱글턴에는 utf-8 표현이 이미 캐시돼 있어 3바이트를 더 먹는다.\
`chr(0xac00)`(한글)은 그 범위 밖이라 **매번 새 객체**다.

이것은 [02번](../02-is-vs-eq-interning/2-summary.md)의 「두 기계」와 **또 다른 세 번째 기계**다 — 그쪽은 리터럴을 합치는 이야기고, 이쪽은 **실행 중에 만든 한 글자짜리**까지 걸린다.\
★ 그래서 **크기를 재는 실험은 두 글자 이상으로 해야 한다.** 한 판만 재고 결론을 세웠으면 틀렸을 자리다.

**비용** — PEP 393 덕에 ASCII 문자열이 글자당 1바이트로 저장된다(3.3 이전에는 2 또는 4였다).\
대신 **한 글자 때문에 전체가 4배가 되는** 자리가 생긴다.

### 5. `encode`/`decode` — 다리를 건너는 두 방향

**언제 쓰나** — 파일·소켓·HTTP·DB 를 만나는 모든 경계.

```text
     str                                    bytes
  "가A"  --- .encode("utf-8") ------->  b'\xea\xb0\x80A'
  "가A"  <-- .decode("utf-8") --------  b'\xea\xb0\x80A'

  ★ 방향을 외우는 법:
     str 은 "부호로 바꾼다"(encode) 라서 바이트가 나온다.
     bytes 는 "부호를 푼다"(decode) 라서 글자가 나온다.
```

```python
s = "가A"
for enc in ("utf-8", "utf-16", "utf-16-le", "utf-32-le", "euc-kr", "cp949"):
    print(f"{enc:10} {len(s.encode(enc)):2}바이트 {s.encode(enc)}")
```

```text
utf-8       4바이트 b'\xea\xb0\x80A'
utf-16      6바이트 b'\xff\xfe\x00\xacA\x00'
utf-16-le   4바이트 b'\x00\xacA\x00'
utf-32-le   8바이트 b'\x00\xac\x00\x00A\x00\x00\x00'
euc-kr      3바이트 b'\xb0\xa1A'
cp949       3바이트 b'\xb0\xa1A'
```

그림 해설.

- **같은 두 글자가 3\~8 바이트로 갈린다.** 「한글은 3바이트」는 utf-8 에서만 맞다.
- `utf-16` 이 `utf-16-le` 보다 2바이트 긴 것은 앞에 **BOM**(`b'\xff\xfe'`)이 붙기 때문이다.
- `euc-kr` 은 한글을 2바이트로 담지만 **담을 수 있는 글자가 훨씬 적다.**

**★ 틀린 인코딩으로 읽으면 — 터질 때와 조용히 바뀔 때**

```python
raw = "가나다".encode("utf-8")
print("원본 바이트 :", raw)
print("latin-1 로  :", repr(raw.decode("latin-1")))
print("되돌아가나  :", raw.decode("latin-1").encode("latin-1") == raw)
try:
    raw.decode("euc-kr")
except UnicodeDecodeError as e:
    print("euc-kr 로   :", type(e).__name__, e)
```

```text
원본 바이트 : b'\xea\xb0\x80\xeb\x82\x98\xeb\x8b\xa4'
latin-1 로  : 'ê°\x80ë\x82\x98ë\x8b¤'
되돌아가나  : True
euc-kr 로   : UnicodeDecodeError 'euc_kr' codec can't decode byte 0x80 in position 2: illegal multibyte sequence
```

★ **`latin-1` 은 절대 에러를 내지 않는다.** 0\~255 를 전부 받아 주는 인코딩이라
**아무 바이트나 「읽히긴」 한다.** 그래서 깨진 글자(`ê°\x80…`)가 DB 에 그대로 들어간다.\
`euc-kr` 은 터졌다 — **터진 쪽이 나은 경우**다.

> **조용한 실패(silent failure)** — 에러 없이 정상처럼 끝나는데 결과만 틀린 것.\
> 여기서는 `latin-1` 로 읽은 깨진 글자가 그것이다. 사람이 화면을 보기 전에는 아무도 모른다.

**에러 핸들러 — 「터뜨릴까 넘길까」를 고르는 손잡이**

```python
t = "가nb👍"
for h in ("strict", "ignore", "replace", "xmlcharrefreplace", "backslashreplace", "namereplace"):
    try:
        print(f"{h:20}", t.encode("ascii", h))
    except UnicodeEncodeError as e:
        print(f"{h:20}", type(e).__name__, e)
```

```text
strict               UnicodeEncodeError 'ascii' codec can't encode character '\uac00' in position 0: ordinal not in range(128)
ignore               b'nb'
replace              b'?nb?'
xmlcharrefreplace    b'&#44032;nb&#128077;'
backslashreplace     b'\\uac00nb\\U0001f44d'
namereplace          b'\\N{HANGUL SYLLABLE GA}nb\\N{THUMBS UP SIGN}'
```

```python
broken = "가".encode("utf-8")[:2]        # 3바이트 중 2바이트만 온 것
print("잘린 바이트:", broken)
for h in ("strict", "ignore", "replace", "backslashreplace", "surrogateescape"):
    try:
        print(f"{h:20}", repr(broken.decode("utf-8", h)))
    except UnicodeDecodeError as e:
        print(f"{h:20}", type(e).__name__, e)
print("왕복 복원:", broken.decode("utf-8", "surrogateescape").encode("utf-8", "surrogateescape") == broken)
```

```text
잘린 바이트: b'\xea\xb0'
strict               UnicodeDecodeError 'utf-8' codec can't decode bytes in position 0-1: unexpected end of data
ignore               ''
replace              '�'
backslashreplace     '\\xea\\xb0'
surrogateescape      '\udcea\udcb0'
왕복 복원: True
```

| 핸들러 | 어느 쪽 | 무엇을 하나 | 되돌릴 수 있나 |
|---|---|---|---|
| `strict` | 둘 다 | 예외를 던진다(기본값) | — |
| `ignore` | 둘 다 | **말없이 버린다** | ✗ 데이터가 사라진다 |
| `replace` | 둘 다 | encode 는 `?`, decode 는 `\ufffd` | ✗ |
| `backslashreplace` | 둘 다 | `\xhh`·`\uxxxx` 문자열로 | ✗ (사람이 읽을 수는 있다) |
| `xmlcharrefreplace` | encode 만 | `&#44032;` | ✗ |
| `namereplace` | encode 만 | `\N{HANGUL SYLLABLE GA}` | ✗ |
| `surrogateescape` | 둘 다 | 못 읽은 바이트를 `U+DC80`\~`U+DCFF` 로 숨긴다 | **✓ 왕복한다** |

★ **`ignore` 가 이 표에서 가장 위험하다.** 데이터가 소리 없이 사라지는데 로그도 안 남는다.\
★ **`surrogateescape` 만 왕복이 보장된다**(PEP 383). 파일 이름처럼 **내용을 몰라도 그대로 돌려줘야 하는 것**에 쓴다.

**비용** — 에러 핸들러 덕에 깨진 입력에서도 파이프라인이 안 멈춘다.\
대신 **어느 핸들러든 `strict` 가 아니면 데이터가 바뀐다.** 기본값을 바꿀 때는 그 손실을 적어 둬야 한다.

### 6. 서로게이트 — 만들 수는 있는데 부칠 수가 없다

**언제 쓰나** — 자바·자바스크립트·윈도에서 온 데이터를 받을 때. UTF-16 의 흔적이다.

```text
 유니코드 코드 포인트 공간
  0x0000 ......... 0xD7FF | 0xD800 ~ 0xDFFF | 0xE000 ......... 0x10FFFF
       쓸 수 있는 글자        서로게이트 구간        쓸 수 있는 글자
                              ^
                              |  UTF-16 이 큰 글자를 두 조각으로
                                 나눌 때 쓰려고 비워 둔 자리.
                                 "글자" 가 아니다.

  ★ 파이썬 str 에는 담긴다.  ★ 그런데 encode 가 거부한다.
```

```python
s = "\ud800"
print("만들어지긴 한다:", repr(s), len(s), hex(ord(s)))
for enc in ("utf-8", "utf-16", "utf-32"):
    try:
        print(f"{enc}:", s.encode(enc))
    except UnicodeEncodeError as e:
        print(f"{enc}:", type(e).__name__, e)
print("surrogatepass:", s.encode("utf-8", "surrogatepass"))
print("다시 decode  :", s.encode("utf-8", "surrogatepass").decode("utf-8", "surrogatepass") == s)
```

```text
만들어지긴 한다: '\ud800' 1 0xd800
utf-8: UnicodeEncodeError 'utf-8' codec can't encode character '\ud800' in position 0: surrogates not allowed
utf-16: UnicodeEncodeError 'utf-16' codec can't encode character '\ud800' in position 0: surrogates not allowed
utf-32: UnicodeEncodeError 'utf-32' codec can't encode character '\ud800' in position 0: surrogates not allowed
surrogatepass: b'\xed\xa0\x80'
다시 decode  : True
```

그림 해설.

- **`str` 은 받아 준다.** `len` 도 1 이고 `ord` 도 답한다 — 여기서는 아무 문제가 없다.
- **`encode` 에서만 터진다.** 세 인코딩이 전부 같은 이유로 거부한다.
- ★ 그래서 **사고가 만든 자리에서 안 나고 저 멀리 출력 자리에서 난다.** JSON 응답을 쓰다가, 파일에 저장하다가, 로그를 찍다가 터진다.
- `surrogatepass` 만이 그 바이트를 통과시킨다. 문서가 이 핸들러의 쓰임을 **utf-8/16/32 계열 한정**으로 못 박는다.

**어디서 들어오나** — 5번 절의 `surrogateescape` 가 만든 `'\udcea'` 도 서로게이트다.\
**읽을 때 넘긴 것이 쓸 때 터지는** 구조라서, 두 경계에 같은 핸들러를 써야 한다.

**비용** — 서로게이트를 담을 수 있어서 **깨진 파일 이름을 잃지 않고** 다룰 수 있다.\
대신 **`str` 안에 「인코딩 불가능한 값」이 섞여 다닐 수 있다.** 타입만 보고 안전하다고 믿을 수 없다.

### 7. `str` 과 `bytes` 를 섞으면 — 터지는 자리와 조용한 자리

**언제 쓰나** — 파이썬 2 에서 옮겨 온 코드, 그리고 라이브러리 경계.

```python
try:
    b"a" + "a"
except TypeError as e:
    print("b'a' + 'a'      ->", type(e).__name__, e)
try:
    "a" + b"a"
except TypeError as e:
    print("'a' + b'a'      ->", type(e).__name__, e)
try:
    b"a" < "a"
except TypeError as e:
    print("b'a' < 'a'      ->", type(e).__name__, e)
try:
    "abc" in b"abc"
except TypeError as e:
    print("'abc' in b'abc' ->", type(e).__name__, e)
print("b'a' == 'a'     ->", b"a" == "a", "  <- 에러가 안 난다")
print("b'a' != 'a'     ->", b"a" != "a")
```

```text
b'a' + 'a'      -> TypeError can't concat str to bytes
'a' + b'a'      -> TypeError can only concatenate str (not "bytes") to str
b'a' < 'a'      -> TypeError '<' not supported between instances of 'bytes' and 'str'
'abc' in b'abc' -> TypeError a bytes-like object is required, not 'str'
b'a' == 'a'     -> False   <- 에러가 안 난다
b'a' != 'a'     -> True
```

```text
 섞었을 때 무엇이 나오나

  +  -  <  in   ->  TypeError     (시끄럽다. 바로 잡힌다)
  == !=         ->  False / True  (조용하다. ★ 여기서 사고가 난다)
```

★ **`==` 만 예외적으로 조용하다.** 타입이 다르면 그냥 다른 값으로 친다.\
`if header == b"content-type":` 에 `str` 이 들어오면 **언제나 `False`** 가 되고, 아무도 안 알려준다.

**★ 그 조용한 자리를 켜는 스위치가 있다**

```python
print("b'a' == 'a' ->", b"a" == "a")
print("str(b'a')   ->", str(b"a"))
```

```text
$ python3 ex.py
b'a' == 'a' -> False
str(b'a')   -> b'a'

$ python3 -b ex.py
ex.py:1: BytesWarning: Comparison between bytes and string
  print("b'a' == 'a' ->", b'a' == 'a')
ex.py:2: BytesWarning: str() on a bytes instance
  print("str(b'a')   ->", str(b'a'))
b'a' == 'a' -> False
str(b'a')   -> b'a'

$ python3 -bb ex.py
Traceback (most recent call last):
  File "ex.py", line 1, in <module>
    print("b'a' == 'a' ->", b'a' == 'a')
                            ^^^^^^^^^^^
BytesWarning: Comparison between bytes and string
```

★ **경고도 출력이다 — 따로 물어야 보인다.** `-b` 는 경고를, `-bb` 는 **예외**를 만든다.\
파이썬 2 에서 옮기는 코드의 테스트를 `-bb` 로 돌리면 이 부류가 전부 드러난다.

- `str(b'a')` 가 `"b'a'"` 라는 **문자열 다섯 글자**를 만드는 것도 같은 부류다. 디코딩이 아니다.

**bytes 끼리는 조용하지 않다**

```python
print("bytearray(b'ab') == b'ab' ->", bytearray(b"ab") == b"ab")
print("b'ab' in bytearray(b'xaby') ->", b"ab" in bytearray(b"xaby"))
```

```text
bytearray(b'ab') == b'ab' -> True
b'ab' in bytearray(b'xaby') -> True
```

`bytes` 와 `bytearray` 는 **같은 열이면 같다고 본다.** 갈리는 것은 `str` 과의 사이뿐이다.

**비용** — 타입이 갈려 있어서 「인코딩 모르는 문자열」이 돌아다닐 수 없다(파이썬 2 의 가장 큰 사고 원인을 없앤 설계다).\
대신 **경계마다 `encode`/`decode` 를 명시해야 한다.** 그리고 `==` 하나가 그 방어벽에 난 구멍이다.

### 8. `bytearray` — 가변 쪽

**언제 쓰나** — 큰 바이너리를 조각내어 쌓을 때. 소켓 수신 버퍼가 대표다.

```text
 bytes  b'abc'            bytearray  bytearray(b'abc')
  +---+---+---+            +---+---+---+
  | a | b | c |            | a | b | c |
  +---+---+---+            +---+---+---+
   불변 — 고치려면          가변 — 그 자리에서 고친다
   새로 만들어야 한다        ba[0] = 90  /  ba.append(100)

  해시된다 (dict 키 가능)   해시 안 된다 (dict 키 불가)
```

```python
ba = bytearray(b"abc")
i0 = id(ba)
ba[0] = 90
ba.append(100)
print("바꾼 뒤:", ba, "| 같은 객체인가:", id(ba) == i0)
try:
    b = b"abc"; b[0] = 90
except TypeError as e:
    print("bytes 는 :", type(e).__name__, e)
try:
    ba[0] = b"Z"
except TypeError as e:
    print("원소는 정수만:", type(e).__name__, e)
try:
    ba[0] = 256
except ValueError as e:
    print("범위는 0~255:", type(e).__name__, e)
try:
    hash(bytearray(b"abc"))
except TypeError as e:
    print("해시:", type(e).__name__, e)
```

```text
바꾼 뒤: bytearray(b'Zbcd') | 같은 객체인가: True
bytes 는 : TypeError 'bytes' object does not support item assignment
원소는 정수만: TypeError 'bytes' object cannot be interpreted as an integer
범위는 0~255: ValueError byte must be in range(0, 256)
해시: TypeError unhashable type: 'bytearray'
```

그림 해설.

- **`id` 가 그대로다.** 새 객체를 만드는 게 아니라 그 자리를 고친다([03번](../03-mutability-and-copying/2-summary.md)의 가변·불변 정본이 그대로 적용된다).
- ★ **원소에 넣는 것은 정수다.** `ba[0] = b"Z"` 가 `TypeError` 인 것은 1번 절의 「`bytes` 의 원소는 정수」와 같은 이야기다.
- **가변이라 해시가 안 된다.** `dict` 키·`set` 원소로 못 쓴다 — 이것도 03번의 규칙 그대로다.

**`memoryview` 는 복사 없이 그 자리를 들여다보는 창이다**

```python
mv = memoryview(bytearray(b"abcd"))
mv[0] = 90
print("memoryview 로 바꾼 뒤:", mv.obj)
```

```text
memoryview 로 바꾼 뒤: bytearray(b'Zbcd')
```

**비용** — 조각을 이어 붙일 때 `bytes` 는 매번 새 객체를 만들지만(O(n²)) `bytearray.extend` 는 제자리다.\
대신 **해시가 안 되고, 여러 곳에서 같이 들고 있으면 한쪽 변경이 다른 쪽에 보인다.**

**바이트는 어디서 오나** — 언급만 한다. `open(path, "rb")`·`socket.recv`·`urllib` 의 응답 본문·`hashlib` 의 입력이 전부 `bytes` 다.
텍스트 모드 `open(path, "r")` 은 **안에서 `decode` 를 해 주는 것**이고, 그때 쓰는 인코딩은 인자로 주지 않으면 **로캘에 달렸다**(목록의 **48번 주제**).

## 문법 — 형태와 규칙

```python
s = "가A"                  # str  — 코드 포인트 열
b = b"ab"                  # bytes — ASCII 리터럴만. 그 밖은 \xNN 이스케이프
ba = bytearray(b"ab")      # bytearray — 가변

s.encode("utf-8")          # str  -> bytes
b.decode("utf-8")          # bytes -> str
s.encode("ascii", "ignore")    # 에러 핸들러는 둘째 인자
b.decode("utf-8", "replace")

ord("가")                   # 44032  — 글자 하나 -> 코드 포인트
chr(44032)                 # '가'    — 코드 포인트 -> 글자 하나

import unicodedata
unicodedata.normalize("NFC", s)    # 합쳐 쓴 형태로 모은다
unicodedata.name("가")              # 'HANGUL SYLLABLE GA'
unicodedata.category("가")          # 'Lo'

s[0]                       # 길이 1 짜리 str
b[0]                       # 정수
b[0:1]                     # 길이 1 짜리 bytes
```

규칙은 일곱이다.

1. **`str` 은 코드 포인트의 불변 열, `bytes` 는 바이트의 불변 열**이다. 문서가 그렇게 정의한다.
2. **`len(str)` 은 코드 포인트를 센다** — 바이트도 아니고 「보이는 글자」도 아니다.
3. **둘 사이는 `encode`/`decode` 로만 건넌다.** 암묵 변환은 없다.
4. **`bytes` 는 인덱싱하면 정수, 슬라이싱하면 `bytes`** 다. `str` 은 둘 다 `str` 이다.
5. **섞으면 `TypeError`** 다 — 단 **`==`·`!=` 만 조용히 `False`/`True`** 를 준다. `-b`/`-bb` 로 켤 수 있다.
6. **`ord`/`chr` 의 범위는 `0`\~`sys.maxunicode`(0x10FFFF)** 다. 밖이면 `ValueError`, 인자가 한 글자가 아니면 `TypeError` 다.
7. **서로게이트(`U+D800`\~`U+DFFF`)는 `str` 에 담기지만 `encode` 가 거부한다.** `surrogatepass`/`surrogateescape` 만 통과시킨다.

## 어디서 틀리나

### (1) `len` 으로 글자 수를 제한한다

```python
nickname = "👨‍👩‍👧"
print(len(nickname))          # 5   <- 사용자는 한 글자를 입력했다
print(nickname[:2])           # 👨   <- 2글자로 자르면 아빠만 남는다
```

「닉네임 10자 제한」이 이모지 두 개에서 걸린다. 반대로 한글 10자는 터미널에서 20칸을 먹는다.

### (2) 정규화를 안 하고 비교·저장한다

```python
import unicodedata
a, b = "\u00e9", "e\u0301"
users = {a: "가입됨"}
print(users.get(b, "못 찾음"))       # 못 찾음
print(len({a, b}))                  # 2   <- 중복 제거가 안 된다
```

macOS 가 만든 파일 이름은 NFD 에 가깝고 웹·리눅스는 NFC 다. **경계마다 한 형태로 모은다.**

### (3) `b"..." == "..."` 로 비교한다

```python
header = b"content-type"
print(header == "content-type")     # False   <- 에러가 안 난다
```

소켓·HTTP 라이브러리에서 온 것은 `bytes` 다. **테스트를 `python3 -bb` 로 돌리면 전부 드러난다.**

### (4) `latin-1` 로 읽어 놓고 「에러가 안 났으니 맞다」고 믿는다

```python
raw = "가나다".encode("utf-8")
print(raw.decode("latin-1"))        # ê°\x80ë\x82\x98ë\x8b¤
```

`latin-1` 은 **어떤 바이트도 거부하지 않는다.** 「돌아갔다」가 「맞다」가 아니다.

### (5) `ignore` 핸들러로 깨진 입력을 넘긴다

```python
print("가nb👍".encode("ascii", "ignore"))     # b'nb'
```

한글과 이모지가 **로그 한 줄 없이 사라졌다.** 되돌릴 방법도 없다.

### (6) `bytes` 를 `for` 로 돌며 글자처럼 쓴다

```python
for c in b"abc":
    print(c, type(c).__name__)      # 97 int / 98 int / 99 int
```

`c.isdigit()` 을 부르면 `AttributeError` 다. **글자가 필요하면 먼저 `decode`** 한다.

### (7) `str(b"...")` 로 디코딩하려 한다

```python
print(str(b"abc"))          # b'abc'   <- 다섯 글자짜리 문자열이다
print(str(b"abc", "utf-8")) # abc      <- 인코딩을 줘야 디코딩이다
```

`str(b)` 는 `repr` 을 문자열로 만든다. `-b` 로 돌리면 `BytesWarning` 이 난다.

### (8) 「한글은 3바이트」로 외운다

```python
print(len("가".encode("utf-8")), len("가".encode("euc-kr")), len("가".encode("utf-16-le")))   # 3 2 2
```

**인코딩을 안 말하면 바이트 수는 정해지지 않는다.**

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」과 「관찰」이 뚜렷이 갈린다** — 의미는 명세가 정하고, 크기와 객체 동일성은 구현이 정한다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어·라이브러리 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 + `sys.getsizeof`·`is` 로 확인 |
| **이 판의 관찰** | 3.12.3 에서 그랬을 뿐 | 「관찰」로 명기 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| `str` 은 **유니코드 코드 포인트의 불변 열**이다 | Text Sequence Type — *"immutable sequences of Unicode code points"* |
| `bytes` 는 **단일 바이트의 불변 열**이다 | Binary Sequence Types — *"immutable sequences of single bytes"* |
| `bytearray` 는 `bytes` 의 **가변 짝**이다 | Binary Sequence Types — *"a mutable counterpart to bytes objects"* |
| `b[0]` 은 정수이고 `b[0:1]` 은 길이 1짜리 `bytes` 다 | Binary Sequence Types 의 주 — 문자열과 대비까지 명시 |
| bytes 리터럴에는 **ASCII 만** 쓸 수 있다(소스 인코딩과 무관) | Binary Sequence Types |
| `sys.maxunicode` 는 `1114111`(`0x10FFFF`)이다 | `sys.maxunicode` |
| 에러 핸들러 여덟 종의 의미와 **어느 방향에 쓸 수 있나** | codecs — Error Handlers 표 |
| `surrogateescape` 로 디코딩한 것을 같은 핸들러로 인코딩하면 **같은 바이트로 돌아온다** | codecs — *"turned back into the same byte"*(PEP 383) |
| `surrogatepass` 는 **utf-8/16/32 계열에서만** 쓸 수 있다 | codecs — 코덱별 핸들러 표 |
| NFC/NFD 는 표준 동치, NFKC/NFKD 는 **호환 동치**다 | `unicodedata.normalize` |
| `sys.getsizeof` 는 **구현에 달렸고** 참조하는 객체는 안 센다 | `sys.getsizeof` — *"it is implementation specific"* |

★ 마지막 줄이 이 주제의 안전선이다 — **문서가 스스로 「보장이 아니다」라고 말한 자리**다.

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| 문자열은 최대 코드 포인트에 따라 **글자당 1·2·4 바이트** 중 하나로 저장된다(PEP 393) | `getsizeof` 로 10글자 대 11글자를 재서 증가분이 1·2·4 |
| ASCII 99글자 + 이모지 1글자면 **전체가 4바이트/글자**가 된다 | 141 대 460 |
| 코드 포인트 `0`\~`255` 짜리 **한 글자 문자열은 미리 만들어 둔 싱글턴**이다 | `chr(0xe9) is chr(0xe9)` 가 `True`, `chr(0xac00)` 은 `False` |
| 그 싱글턴에는 utf-8 표현이 캐시돼 있어 **1글자가 2글자보다 크다** | 61 대 59 |
| `BytesWarning` 은 `-b`/`-bb` 로만 켜진다 | 같은 파일을 세 방식으로 돌려 비교 |

### 이 판(3.12.3)의 관찰 — 버전이 오르면 다시 찍어야 한다

| 관찰 | 어디가 흔들리나 |
|---|---|
| `getsizeof` 의 구체적 수(41·60·64·141·460…) | 헤더 크기·정렬·캐시 정책에 달렸다. **다음 판에서 바뀐다** |
| 한 글자 latin-1 문자열이 61바이트인 것 | 싱글턴 표에 utf-8 이 미리 들었느냐에 달렸다 |
| `UnicodeEncodeError`·`UnicodeDecodeError` 의 **문구** | 예외 종류는 명세지만 문구는 아니다 |
| `unicodedata.unidata_version` 이 `15.0.0` 인 것 | 파이썬 판마다 유니코드 DB 가 올라간다. **`normalize` 의 답이 바뀔 수 있다** |
| `euc-kr` 과 `cp949` 가 `"가A"` 에서 같은 바이트를 낸 것 | 겹치는 구간이라 같았을 뿐 — `cp949` 가 더 넓다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「파이썬 문자열은 유니코드로 저장된다」\
  ○ **코드 포인트 열**이다. 「유니코드」는 인코딩 이름이 아니다 — utf-8 도 utf-16 도 유니코드다.
- ✗ 「한글은 3바이트다」\
  ○ **utf-8 에서** 3바이트다. euc-kr 은 2, utf-32 는 4다. **인코딩을 말하지 않으면 답이 없다.**
- ✗ 「`len` 은 글자 수를 센다」\
  ○ **코드 포인트 수**를 센다. 가족 이모지 한 칸이 5다.
- ✗ 「문자열은 한 글자당 몇 바이트다」\
  ○ **문자열마다 다르고**, 그 수는 CPython 의 구현 세부사항이다. 문서가 `getsizeof` 를 *"implementation specific"* 이라고 적는다.
- ✗ 「`b"a" == "a"` 는 타입이 달라서 에러가 난다」\
  ○ **에러가 안 난다.** `False` 다. `-b` 로 켜야 경고가 보인다.
- ✗ 「눈에 같은 문자열은 `==` 로 같다」\
  ○ **정규화가 다르면 다르다.** `==` 는 코드 포인트 열을 그대로 본다.
- ✗ 「`'\ud800'` 같은 건 만들 수 없다」\
  ○ **만들어진다.** `encode` 에서만 터진다.

**판정 기준 한 줄**: 어떤 코드가 **「몇 바이트인가」와 「몇 글자인가」를 같은 것으로 쓰고 있으면** 그 자리가 버그 후보다.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| `str` | 프로그램 **안**에서 도는 모든 텍스트 |
| `bytes` | 파일·소켓·암호화·해시 등 **경계 바깥**으로 나가는 것 |
| `bytearray` | 조각을 이어 붙여 큰 바이너리를 만들 때(수신 버퍼) |
| `memoryview` | 큰 버퍼를 **복사 없이** 잘라 쓸 때 |
| `.encode("utf-8")` / `.decode("utf-8")` | 경계를 건널 때 — **인코딩을 언제나 명시** |
| `unicodedata.normalize("NFC", s)` | 사용자 입력·파일 이름을 **저장·비교하기 직전** |
| `errors="surrogateescape"` | 인코딩을 모르는데 **원본을 그대로 돌려줘야** 할 때(파일 이름) |
| `errors="replace"` | 사람이 볼 로그·화면. 깨진 표가 보이는 게 사라지는 것보다 낫다 |
| `python3 -bb` | `str`/`bytes` 혼용을 **테스트에서 터뜨리고** 싶을 때 |

**안 쓰는 자리**는 셋이다.\
**`errors="ignore"` 를 습관으로 쓰지 마라** — 손실이 조용하다.\
**`latin-1` 을 「일단 읽히게」 쓰지 마라** — 에러를 안 내는 것이지 맞는 것이 아니다.\
**`len` 으로 사용자에게 보이는 글자 수를 재지 마라** — 그 질문에는 표준 라이브러리만으로 답이 안 나온다.

## 핵심 문장

- **`str` 은 코드 포인트 열이고 `bytes` 는 바이트 열이다.** 이 한 문장이 07·08 을 다 설명한다.
- **`len` 은 코드 포인트를 센다.** 바이트도 아니고 화면의 칸도 아니고 사용자가 세는 글자도 아니다 — 넷이 다 다르다.
- **둘 사이는 `encode`/`decode` 로만 건넌다.** 암묵 변환이 없는 것이 파이썬 3 의 설계다.
- 그런데 **`==` 하나가 그 벽에 난 구멍**이다 — `b"a" == "a"` 는 에러 없이 `False` 다. `-bb` 로 켠다.
- **눈에 같은 두 문자열이 `==` 로 다를 수 있다.** 정규화는 비교가 아니라 **저장·입력 경계에서** 해야 한다.
- **서로게이트는 `str` 에 담기고 `encode` 에서 터진다.** 사고가 만든 자리에서 안 나고 출력 자리에서 난다.
- **`getsizeof` 의 숫자는 전부 관찰이다.** 문서가 스스로 *"implementation specific"* 이라고 적는다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **06번**
- 선행: [01-object-and-name-binding](../01-object-and-name-binding/2-summary.md) — 이름 바인딩·불변 객체 모델의 정본. `bytearray` 의 `id` 가 그대로인 것이 그 규칙이다.
- 선행: [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md) — 문자열이 **언제 같은 객체가 되나**의 정본(두 기계). 여기 4번 절의 「한 글자 싱글턴」은 거기에 없는 **세 번째 기계**다.
- 이어지는 곳: [07-string-methods](../07-string-methods/2-summary.md) — 이 코드 포인트 열 위에서 도는 메서드들. `isdecimal`/`isdigit`/`isnumeric` 이 갈리는 이유가 여기 있다.
- 이어지는 곳: [08-fstrings-and-format-spec](../08-fstrings-and-format-spec/2-summary.md) — 그 문자열을 만들어 내는 문법.
- 이어지는 곳: [09-sequence-ops-and-slicing](../09-sequence-ops-and-slicing/2-summary.md) — `str`·`bytes`·`bytearray` 가 **시퀀스로서** 공유하는 연산.
- 이어지는 곳: [03-mutability-and-copying](../03-mutability-and-copying/2-summary.md) — `bytearray` 가 해시 안 되는 이유의 정본.
- 이어지는 곳: 목록의 **46번 주제** 「`re`」 — 정규식이 `str` 패턴과 `bytes` 패턴을 **섞을 수 없는** 것.
- 이어지는 곳: 목록의 **48번 주제** 「`pathlib` 와 파일 I/O」 — `open` 의 `encoding`·`errors`·`newline` 과 텍스트/바이너리 모드.
- 이어지는 곳: 목록의 **47번 주제** 「`json`」 — `ensure_ascii` 가 이 절의 `backslashreplace` 와 같은 일을 한다.
- 기존 노트: [`cs/foundations/data-representation/`](../../../../data-representation/) — 문자 인코딩의 **원리**(ASCII·UTF-8 의 비트 배치).\
  **경계**: 그쪽은 「바이트가 어떻게 생겼나」까지, 여기는 「**파이썬에서 그것을 어떤 타입으로 다루나**」부터다.
- 연혁은 여기가 아니다: [`history/python/`](../../../../../../history/python/) — 파이썬 2 의 `unicode`/`str` 이 3에서 갈라진 이야기.
- 공식 문서: [Text Sequence Type](https://docs.python.org/3.12/library/stdtypes.html#text-sequence-type-str) · [Binary Sequence Types](https://docs.python.org/3.12/library/stdtypes.html#binary-sequence-types-bytes-bytearray-memoryview) · [codecs 에러 핸들러](https://docs.python.org/3.12/library/codecs.html#error-handlers) · [`unicodedata`](https://docs.python.org/3.12/library/unicodedata.html) · [PEP 393](https://peps.python.org/pep-0393/) · [PEP 383](https://peps.python.org/pep-0383/)

## 용어 풀이

- **코드 포인트(code point)**: 유니코드가 글자마다 매긴 번호. `ord()` 가 주고 `chr()` 이 되돌린다.\
  범위는 `0`\~`0x10FFFF` 이고 `sys.maxunicode` 가 그 값을 말한다.
- **인코딩(encoding)**: 코드 포인트를 실제 바이트로 옮겨 적는 규칙.\
  utf-8·utf-16·euc-kr·cp949 등. **같은 글자라도 규격마다 바이트 수가 다르다.**
- **`str`**: 코드 포인트의 불변 열. 인덱싱·슬라이싱이 둘 다 `str` 을 준다.
- **`bytes`**: 단일 바이트의 불변 열. **인덱싱은 정수**, 슬라이싱은 `bytes` 를 준다.
- **`bytearray`**: `bytes` 의 가변 짝. 원소 대입·`append` 가 되고 **해시가 안 된다.**
- **`memoryview`**: 버퍼를 복사하지 않고 들여다보는 창. 쓰기 가능한 버퍼면 그 자리를 고칠 수 있다.
- **BOM (Byte Order Mark)**: utf-16/32 에서 바이트 순서를 알리려고 앞에 붙이는 표식(`b'\xff\xfe'` 등).\
  `utf-16` 은 붙이고 `utf-16-le` 는 안 붙인다.
- **결합 문자(combining character)**: 앞 글자에 덧붙어 한 글자처럼 보이게 하는 글자(`U+0301` 등).\
  `unicodedata.combining()` 이 0 이 아니면 그것이다.
- **ZWJ (ZERO WIDTH JOINER, `U+200D`)**: 이모지 여럿을 한 그림으로 묶는 보이지 않는 글자.\
  가족 이모지가 코드 포인트 5개인 이유다.
- **서로게이트(surrogate)**: `U+D800`\~`U+DFFF` 구간. UTF-16 이 큰 글자를 두 조각으로 쪼갤 때 쓰려고 비워 둔 자리라 **글자가 아니다.**\
  파이썬 `str` 에는 담기지만 `encode` 가 거부한다.
- **정규화(normalization)**: 같은 글자를 나타내는 여러 코드 포인트 열을 한 형태로 모으는 것.\
  NFC(합침)·NFD(풂)는 표준 동치, NFKC·NFKD 는 **호환 동치**라 글자가 바뀐다.
- **모지바케(mojibake)**: 인코딩을 잘못 알고 읽어 글자가 깨진 상태.\
  `latin-1` 처럼 아무 바이트나 받는 인코딩에서 **에러 없이** 생긴다.
- **에러 핸들러(error handler)**: `encode`/`decode` 가 처리 못 하는 자리를 만났을 때의 대처 규칙.\
  `strict`(기본)·`ignore`·`replace`·`surrogateescape` 등. **`ignore` 만 되돌릴 수 없이 데이터를 버린다.**
- **PEP 393 (유연한 문자열 표현)**: 문자열마다 최대 코드 포인트를 보고 글자당 1·2·4 바이트 중 하나를 고르는 CPython 의 저장 방식(3.3+).\
  `getsizeof` 로 드러나지만 **언어 보장이 아니다.**
- **`BytesWarning`**: `str` 과 `bytes` 를 섞었을 때 나는 경고. **기본으로는 꺼져 있고** `-b`/`-bb` 로 켠다.

## 더 들어가면

- **`str.encode` 의 기본 인코딩은 utf-8 로 고정**이다(`sys.getdefaultencoding()` 이 `'utf-8'`). 하지만 **`open()` 의 기본 인코딩은 로캘에 달렸다** — 3.15 부터 utf-8 이 기본이 되는 전환이 진행 중이고, 3.11+ 에서 `PYTHONWARNDEFAULTENCODING=1` 로 경고를 켤 수 있다(PEP 686).
- **`codecs.register_error` 로 에러 핸들러를 직접 만들 수 있다.** 「깨진 자리를 로그에 남기고 건너뛴다」 같은 정책을 표준 인터페이스로 끼워 넣는 방법이다.
- **`str.translate` 로 서로게이트를 한 번에 털어낼 수 있다**(07번 주제). 출력 직전 방어선으로 쓸 수 있다.
- **`sys.intern` 은 `str` 에만 있고 `bytes` 에는 없다**([02번](../02-is-vs-eq-interning/2-summary.md)).
- **이모지의 「한 칸」을 제대로 세려면** 자소 클러스터(grapheme cluster) 분할이 필요하고, 그것은 표준 라이브러리에 없다(`regex`·`grapheme` 같은 서드파티가 한다). 이 문서에서는 실행 검증하지 않았다 — 이 환경에 그 패키지가 없다.
