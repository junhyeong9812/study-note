# python/syntax/06-strings-bytes-unicode — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 11개 = 답 11개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 단 **`sys.getsizeof` 의 숫자와 예외 문구는 구현 세부사항**이라 다른 구현·다른 버전에서는 달라진다(6·10번 답).

## 정답

### 1. `len()` 은 코드 포인트를 센다 — 넷 다 다른 이유

**출력**

```text
2 1 5 2
6
👨‍👩
['0x1f468', '0x200d', '0x1f469', '0x200d', '0x1f467']
```

**왜 그런가**

문서의 정의 한 줄이 답이다 —\
*"Strings are immutable **sequences of Unicode code points**."*\
`len` 은 그 열의 **길이**이므로 **코드 포인트 수**다.

```text
 "한글"    [ 44620 , 44544 ]                      -> 2
 "👍"      [ 128077 ]                             -> 1
 "👨‍👩‍👧"   [ 128104, 8205, 128105, 8205, 128103 ]  -> 5   ★ 사이에 ZWJ 가 둘
 "🇰🇷"      [ 127472, 127479 ]                     -> 2   ★ 지역 표시 기호 둘
```

| 문자열 | `len` | 왜 |
|---|---|---|
| `"한글"` | 2 | 글자 둘 |
| `"👍"` | 1 | 코드 포인트 하나짜리 이모지 |
| `"👨‍👩‍👧"` | 5 | 사람 셋 + **ZWJ 둘**(`U+200D`, 보이지 않는 접착제) |
| `"🇰🇷"` | 2 | 국기는 **지역 표시 기호 두 개**의 조합이다 |

- 둘째 줄 `6` 은 **바이트 수**다. utf-8 에서 한글 한 글자가 3바이트라 `2 × 3`.
- 셋째 줄에서 가족 이모지를 3에서 자르니 **부부**가 됐다. 5까지 잘라야 가족이다.\
  ★ **잘린 게 아니라 다른 그림이 됐다** — 조용한 실패다.

★ **자바스크립트와 다른 자리** — JS 의 `"👍".length` 는 **2** 다(UTF-16 코드 유닛을 센다).\
파이썬은 코드 포인트를 세므로 1 이다. 「이모지는 길이 2」라는 지식을 그대로 옮기면 틀린다.

### 2. `==` 는 정규화를 보지 않는다

**출력**

```text
é é 1 2
False
못 찾음 2
True
'IV'
```

**왜 그런가**

```text
 a = "\u00e9"        b = "e\u0301"
   [ 233 ]             [ 101, 769 ]
      é                   e  +  ́
   len = 1             len = 2

   화면에는 둘 다 é.   ★ == 는 코드 포인트 열을 그대로 비교한다 -> False
```

- **`==` 가 `False`** 다. 정규화라는 개념 자체를 보지 않는다.
- 그래서 **`dict` 가 못 찾고 `set` 이 둘로 센다.** `hash` 가 코드 포인트 열에서 나오기 때문이다.
- `unicodedata.normalize("NFC", b)` 를 거치면 `[233]` 이 되어 같아진다.

**마지막 줄이 성격이 다른 이유**

문서가 두 무리로 갈라 둔다.

| 형태 | 무엇을 모으나 | `'Ⅳ'` 에 대한 답 | 글자가 바뀌나 |
|---|---|---|---|
| NFC / NFD | **표준 동치**(canonical) — 같은 글자의 다른 적는 법 | `'Ⅳ'` 그대로 | ✗ |
| NFKC / NFKD | **호환 동치**(compatibility) — 호환용으로 따로 들어온 글자를 원래 글자로 | `'IV'` | **✓ 길이가 1 에서 2 로** |

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

★ **NFKC 는 「모으는」 게 아니라 「갈아치우는」 것**이다.\
검색 색인에는 쓸 만하고 **원본 보존에는 쓰면 안 된다.** 문서가 `U+2160`(ROMAN NUMERAL ONE)을 예로 들며 *"is really the same thing as U+0049"* 라고 적는다.

### 3. `bytes` 는 인덱싱하면 정수다

**출력**

```text
b'\xea\xb0\x80' 3
234 int
b'\xea' bytes
[234, 176, 128] ['가']
가 str
```

**왜 그런가**

문서가 이것을 따로 못 박는다 —\
*"Since bytes objects are sequences of integers (akin to a tuple), for a bytes object b, `b[0]` will be an integer, while `b[0:1]` will be a bytes object of length 1. **(This contrasts with text strings, where both indexing and slicing will produce a string of length 1)**"*

```text
     str "가"                       bytes b'\xea\xb0\x80'
  +---------+                    +-----+-----+-----+
  |  44032  |                    | 234 | 176 | 128 |
  +---------+                    +-----+-----+-----+
    len = 1                          len = 3

  s[0]    -> '가'  (str)          b[0]    -> 234      (int)   ★ 여기서 갈린다
  s[0:1]  -> '가'  (str)          b[0:1]  -> b'\xea'  (bytes)
  list(s) -> ['가']               list(b) -> [234,176,128]
```

**갈라지는 연산은 「원소 하나를 꺼내는 것」 하나다.**

| 연산 | `str` | `bytes` |
|---|---|---|
| `x[0]` | 길이 1짜리 `str` | **`int`** |
| `x[0:1]` | 길이 1짜리 `str` | 길이 1짜리 `bytes` |
| `for c in x` | `str` 이 나온다 | **`int`** 가 나온다 |
| `len(x)` | 코드 포인트 수 | 바이트 수 |

**여기서 틀리는 자리**

```python
for c in b"a1b":
    print(c, type(c).__name__)
```

```text
97 int
49 int
98 int
```

`c.isdigit()` 을 부르면 `AttributeError: 'int' object has no attribute 'isdigit'` 이다.\
**글자 판정을 하려면 먼저 `decode`** 하거나, `b"a1b"[1:2]` 처럼 **슬라이스로** 꺼낸다.

### 4. 섞으면 — 넷은 터지고 셋은 조용하다

**출력**

```text
b"a" + "a" -> TypeError
"a" + b"a" -> TypeError
b"a" < "a" -> TypeError
"abc" in b"abc" -> TypeError
False True
True
b'abc'
```

**왜 그런가**

```text
 str 과 bytes 를 섞었을 때

  +   -> TypeError: can't concat str to bytes
  <   -> TypeError: '<' not supported between instances of 'bytes' and 'str'
  in  -> TypeError: a bytes-like object is required, not 'str'
        ★ 시끄럽다. CI 에서 바로 잡힌다.

  ==  -> False        ★ 조용하다.
  !=  -> True         ★ 조용하다.
  str(b) -> "b'abc'"  ★ 조용하다. 디코딩이 아니라 repr 이다.
```

**에러가 안 나는 줄이 왜 더 위험한가**

```python
header = b"content-type"          # 소켓·HTTP 라이브러리가 준 것
if header == "content-type":      # 사람이 쓴 것
    print("맞다")
else:
    print("안 맞다")
```

```text
안 맞다
```

★ **조건이 언제나 거짓**이 된다. 예외도 로그도 없다.\
테스트가 `bytes` 를 안 쓰면 통과해 버리고, 운영에서만 조용히 틀린다.

`bytearray(b"ab") == b"ab"` 가 **`True`** 인 것과 대비하면 규칙이 보인다 —\
**바이너리끼리는 내용을 비교하고, `str` 과의 사이만 「다른 것」으로 친다.**

**★ 그 조용한 자리를 켜는 스위치가 있다**

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

★ **경고도 출력이다 — 따로 물어야 보인다.** `-b` 는 경고, `-bb` 는 **예외**.\
파이썬 2 에서 옮긴 코드의 테스트를 `-bb` 로 한 번 돌리면 이 부류가 전부 드러난다.

- `str(b"abc")` 가 `b'abc'` 로 보이는 것은 **다섯 글자짜리 문자열**이다. 디코딩하려면 `str(b, "utf-8")` 또는 `b.decode()`.

### 5. 서로게이트 — 담기는데 부쳐지지 않는다

**출력**

```text
'\ud800' 1 0xd800
encode: UnicodeEncodeError
b'\xed\xa0\x80'
'\udcea\udcb0'
True
```

**왜 그런가**

```text
 유니코드 코드 포인트 공간
  0x0000 ....... 0xD7FF | 0xD800 ~ 0xDFFF | 0xE000 ....... 0x10FFFF
        쓸 수 있는 글자     서로게이트 구간      쓸 수 있는 글자
                              ^
                              UTF-16 이 큰 글자를 두 조각으로
                              나눌 때 쓰려고 비워 둔 자리 = "글자가 아니다"

  파이썬 str:   담긴다.  len 도 1, ord 도 답한다.
  encode:       거부한다. utf-8 / utf-16 / utf-32 전부.
```

```python
s = "\ud800"
for enc in ("utf-8", "utf-16", "utf-32"):
    try:
        print(f"{enc}:", s.encode(enc))
    except UnicodeEncodeError as e:
        print(f"{enc}:", e)
```

```text
utf-8: 'utf-8' codec can't encode character '\ud800' in position 0: surrogates not allowed
utf-16: 'utf-16' codec can't encode character '\ud800' in position 0: surrogates not allowed
utf-32: 'utf-32' codec can't encode character '\ud800' in position 0: surrogates not allowed
```

**어느 단계에서 문제가 되나**

```text
 [읽기] decode(errors="surrogateescape")     깨진 바이트가 '\udcea' 로 숨는다
    |                                         ★ 여기서는 조용하다
    v
 [처리] len·슬라이스·비교 전부 정상으로 돈다    ★ 여기서도 조용하다
    |
    v
 [쓰기] json.dumps / 파일 저장 / 로그          ★ 여기서 터진다
        UnicodeEncodeError: surrogates not allowed
```

★ **사고가 만든 자리에서 안 나고 저 멀리 출력 자리에서 난다.**\
스택 트레이스를 봐도 어느 입력이 원인인지 안 나온다 — 이것이 이 값의 고약한 점이다.

**`surrogateescape` 가 왕복하는 것**

```text
b'\xea\xb0'  --decode(surrogateescape)-->  '\udcea\udcb0'
b'\xea\xb0'  <--encode(surrogateescape)--  '\udcea\udcb0'    ★ 같은 바이트로 돌아온다
```

문서가 그렇게 약속한다 — *"This code will then be turned back into the same byte when the `'surrogateescape'` error handler is used when encoding the data."*(PEP 383)\
**표의 여덟 핸들러 중 왕복이 보장되는 것은 이것 하나뿐**이다.

### 6. 글자 수가 같은데 크기가 다르다 — PEP 393

**출력**

```text
51 78 100
52 80 104
141 460
61 59 60
```

**왜 그런가**

★ 먼저 문서가 물러선 자리를 읽는다 —\
*"Return the size of an object in bytes... this does not have to hold true for third-party extensions as it is **implementation specific**."*\
**아래 숫자는 전부 「이 판의 관찰」이지 언어 보장이 아니다.**

```text
 10글자 -> 11글자 로 갈 때 늘어나는 바이트

   'a' * n     51 -> 52    +1 바이트/글자
   '한' * n    78 -> 80    +2 바이트/글자
   '👍' * n   100 -> 104   +4 바이트/글자

 ★ 파이썬은 문자열마다 "가장 큰 코드 포인트" 를 보고
   1 / 2 / 4 바이트 칸 중 하나를 고른다 (PEP 393).
```

| 최대 코드 포인트 | 칸 폭 | 예 |
|---|---|---|
| `0`\~`0x7F` | 1바이트 | `"abc"` |
| `0x80`\~`0xFFFF` | 2바이트 | `"한글"` · `"é"` |
| `0x10000` 이상 | 4바이트 | `"👍"` |

**한 글자만 섞여도 전체가 넓어진다**

```text
 'a' * 100            -> 141   (1바이트 x 100 + 헤더)
 'a' * 99 + '👍'      -> 460   (4바이트 x 100 + 헤더)

  ★ 99개가 ASCII 인데도 이모지 하나 때문에 전부 4바이트 칸이 된다.
    칸 폭은 글자마다가 아니라 문자열 전체에 한 번 정해진다.
```

**마지막 줄이 규칙을 어기는 것처럼 보이는 이유**

```text
 61   59   60
  ^
  1글자가 2글자보다 크다 ?
```

```python
print("chr(0xe9) 가 같은 객체인가 :", chr(0xe9) is chr(0xe9))
print("chr(0xac00) 한글 한 글자   :", chr(0xac00) is chr(0xac00))
print("chr(97) ascii 한 글자      :", chr(97) is chr(97))
```

```text
chr(0xe9) 가 같은 객체인가 : True
chr(0xac00) 한글 한 글자   : False
chr(97) ascii 한 글자      : True
```

★ **코드 포인트 `0`\~`255` 짜리 한 글자 문자열은 인터프리터가 미리 만들어 두고 돌려쓰는 싱글턴**이고,
그 싱글턴에는 utf-8 표현이 이미 캐시돼 있어 3바이트를 더 먹는다.\
`chr(0xac00)`(한글)은 그 범위 밖이라 **매번 새 객체**다.

[02번](../02-is-vs-eq-interning/2-summary.md)이 정리한 **두 기계**(한 컴파일 단위의 상수 합치기 · 식별자 모양의 자동 인터닝)와 **또 다른 세 번째 기계**다.
그쪽 둘은 **리터럴**에만 걸리는데, 이것은 **실행 중에 만든 한 글자짜리**까지 걸린다.

★ **그래서 크기 실험은 두 글자 이상으로 해야 한다.** 한 글자만 재고 결론을 세웠으면 틀렸을 자리다.

### 7. `latin-1` 이 에러를 안 내는 이유 (왜)

**핵심 한 줄**: `latin-1` 은 바이트 `0`\~`255` 를 코드 포인트 `0`\~`255` 에 **일대일로 그냥 얹는** 인코딩이라, **거부할 바이트가 없다.**

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

```text
 utf-8 로 적힌 '가'                latin-1 이 읽는 방식
  +------+------+------+           바이트 하나 = 글자 하나
  | 0xEA | 0xB0 | 0x80 |    ->     'ê'  '°'  '\x80'
  +------+------+------+           ★ 세 글자가 됐다. 그런데 에러는 없다.
   "이 셋이 한 글자다"
   라는 약속을 무시했다
```

**왜 근거가 못 되나 — 세 가지가 겹친다.**

1. **거부 기준이 없는 코덱이다.** 「에러 없음」이 「맞음」의 정보를 전혀 담지 않는다.\
   `euc-kr` 은 터졌고 **터진 쪽이 나은 경우**다 — 에러가 정보였다.
2. **되돌릴 수 있다는 것도 안심의 근거가 아니다.** 위에서 왕복이 `True` 인데, 그 사이에
   `len`·슬라이스·`upper` 를 한 번이라도 걸면 **바이트가 어긋나 복원이 깨진다.**
3. **화면이 말해 주지 않는다.** `'ê°\x80…'` 이 DB 에 들어가도 조회는 정상적으로 돌아간다.\
   사람이 그 칸을 눈으로 보기 전에는 아무도 모른다.

> **조용한 실패(silent failure)** — 에러 없이 정상처럼 끝나는데 결과만 틀린 것.\
> 이 주제에서는 `latin-1` 디코딩과 `b"a" == "a"` 둘이 대표다.

★ **「돌아갔다」는 「맞다」가 아니다.** 인코딩은 **밖에서 알려 주는 정보**(HTTP 헤더·BOM·파일 규약)로 정해야 하고, 추측해야 한다면 그 추측을 기록에 남긴다.

### 8. 어느 에러 핸들러를 고르나 (경계)

**되돌릴 수 있는 것은 `surrogateescape` 하나다.**

| 핸들러 | 어느 방향 | 무엇을 하나 | 되돌릴 수 있나 |
|---|---|---|---|
| `strict` | 둘 다 | 예외(기본값) | — (애초에 안 넘어간다) |
| `ignore` | 둘 다 | **말없이 버린다** | ✗ **데이터가 사라진다** |
| `replace` | 둘 다 | encode 는 `?`, decode 는 `\ufffd` | ✗ 원래 값이 안 남는다 |
| `backslashreplace` | 둘 다 | `\xhh`·`\uxxxx` 로 | ✗ (사람이 읽을 수는 있다) |
| `xmlcharrefreplace` | **encode 만** | `&#44032;` | ✗ |
| `namereplace` | **encode 만** | `\N{HANGUL SYLLABLE GA}` | ✗ |
| `surrogateescape` | 둘 다 | 못 읽은 바이트를 `U+DC80`\~`U+DCFF` 로 | **✓ 왕복한다**(PEP 383) |
| `surrogatepass` | 둘 다 | 서로게이트를 그대로 통과 | ✓ (utf-8/16/32 한정) |

```python
t = "가nb👍"
for h in ("strict", "ignore", "replace", "xmlcharrefreplace", "backslashreplace", "namereplace"):
    try:
        print(f"{h:20}", t.encode("ascii", h))
    except UnicodeEncodeError as e:
        print(f"{h:20}", type(e).__name__)
```

```text
strict               UnicodeEncodeError
ignore               b'nb'
replace              b'?nb?'
xmlcharrefreplace    b'&#44032;nb&#128077;'
backslashreplace     b'\\uac00nb\\U0001f44d'
namereplace          b'\\N{HANGUL SYLLABLE GA}nb\\N{THUMBS UP SIGN}'
```

★ **`ignore` 가 이 표에서 가장 위험하다.** `b'nb'` 만 남았다 — 한글과 이모지가 **로그 한 줄 없이** 사라졌다.

**`strict` 가 아닌 것을 쓸 때 기록해 둘 것**

1. **어디서 썼나** — 읽기 경계인가 쓰기 경계인가. 둘의 손실 성격이 다르다.
2. **무엇을 잃을 수 있나** — `ignore` 는 글자, `replace` 는 원래 값, `backslashreplace` 는 **길이**까지 바뀐다.
3. **몇 번 걸렸나** — 핸들러는 통계를 안 남긴다. 세고 싶으면 `codecs.register_error` 로 직접 만든다.
4. **되돌릴 계획이 있나** — 없으면 그 데이터는 **거기서 끝**이라는 것을 문서에 적는다.

### 9. `ord`/`chr` 의 경계 (경계)

**범위는 `0`\~`sys.maxunicode`(`0x10FFFF` = 1114111)다.**

```python
import sys
print("sys.maxunicode:", sys.maxunicode, hex(sys.maxunicode))
print("chr(0x10FFFF):", repr(chr(0x10FFFF)), ord(chr(0x10FFFF)))
for bad in (0x110000, -1):
    try:
        chr(bad)
    except ValueError as e:
        print(f"chr({bad}) ->", type(e).__name__, e)
for bad in ("ab", ""):
    try:
        ord(bad)
    except TypeError as e:
        print(f"ord({bad!r}) ->", type(e).__name__, e)
print("ord(b'a') =", ord(b"a"))
```

```text
sys.maxunicode: 1114111 0x10ffff
chr(0x10FFFF): '\U0010ffff' 1114111
chr(1114112) -> ValueError chr() arg not in range(0x110000)
chr(-1) -> ValueError chr() arg not in range(0x110000)
ord('ab') -> TypeError ord() expected a character, but string of length 2 found
ord('') -> TypeError ord() expected a character, but string of length 0 found
ord(b'a') = 97
```

**예외 종류가 갈리는 이유 — 무엇이 틀렸느냐가 다르다**

```text
 chr(0x110000)             ord("ab")
  타입은 맞다 (int)          타입은 맞다 (str)
  값이 범위 밖이다            길이가 규약을 어겼다
       |                          |
       v                          v
   ValueError                 TypeError
```

- `chr` 은 **정수를 받는 것이 맞고 그 값이 범위 밖**이다 → 값의 문제 → `ValueError`.
- `ord` 는 **「길이 1 짜리 문자열」이라는 것이 인자의 타입 규약**이다. 길이 2 는 그 규약을 어긴 것이라
  CPython 은 이것을 **타입 문제로** 다룬다 → `TypeError`.\
  ★ 문구가 *"expected a character"* 다 — `str` 이 아니라 **`character`** 를 기대했다는 표현이 그 사정을 말한다.
- ★ **`ord` 는 `bytes` 도 받는다.** `ord(b"a")` 가 `97` 이다. 길이 1 짜리면 `str` 이든 `bytes` 든 된다.

**서로게이트는 범위 안이다**

```python
print(hex(ord("\ud800")), repr(chr(0xd800)))
```

```text
0xd800 '\ud800'
```

`ord`/`chr` 은 서로게이트를 막지 않는다. **막는 것은 `encode` 뿐**이다(5번 답).

### 10. 세 층 가르기 (경계)

**언어 보장** — 문서 문장으로 확인한 것.

| 사실 | 근거 |
|---|---|
| `str` 은 **코드 포인트의 불변 열** | *"immutable sequences of Unicode code points"* |
| `bytes` 는 **단일 바이트의 불변 열**, `bytearray` 는 그 **가변 짝** | Binary Sequence Types |
| `b[0]` 은 정수, `b[0:1]` 은 길이 1짜리 `bytes` | Binary Sequence Types 의 주 |
| bytes 리터럴에는 **ASCII 만** (소스 인코딩과 무관) | Binary Sequence Types |
| `sys.maxunicode` 는 `1114111` | `sys.maxunicode` |
| 에러 핸들러 여덟 종의 의미와 **방향 제한** | codecs — Error Handlers |
| `surrogateescape` 는 **같은 바이트로 되돌아온다** | codecs(PEP 383) |
| NFC/NFD 는 표준 동치, NFKC/NFKD 는 **호환 동치** | `unicodedata.normalize` |
| `sys.getsizeof` 는 **구현에 달렸다** | `sys.getsizeof` — *"implementation specific"* |

**CPython 구현 세부사항** — 실행으로 확인한 것.

| 사실 | 어떻게 확인했나 |
|---|---|
| 문자열이 최대 코드 포인트에 따라 **1·2·4 바이트 칸**을 쓴다(PEP 393) | 10글자 대 11글자의 증가분이 1·2·4 |
| ASCII 99 + 이모지 1 이면 **전체가 4바이트 칸** | 141 대 460 |
| 코드 포인트 `0`\~`255` 한 글자는 **싱글턴**이고 utf-8 이 캐시돼 있다 | `chr(0xe9) is chr(0xe9)` 가 `True`, 크기가 61 |
| `BytesWarning` 은 `-b`/`-bb` 로만 켜진다 | 같은 파일을 세 방식으로 돌려 비교 |
| `str.encode` 의 기본이 utf-8 인 것 | `sys.getdefaultencoding()` 이 `'utf-8'` |

**이 판(3.12.3)의 관찰** — 버전이 오르면 다시 찍어야 하는 것.

| 관찰 | 어디가 흔들리나 |
|---|---|
| `getsizeof` 의 구체적 수(41·51·60·64·141·460…) | 헤더 크기·정렬·캐시 정책 |
| 한 글자 latin-1 이 61바이트인 것 | 싱글턴에 utf-8 이 미리 들었느냐 |
| 예외 문구 전부(`surrogates not allowed` 등) | 예외 종류는 명세지만 문구는 아니다 |
| `unicodedata.unidata_version` 이 `15.0.0` | 파이썬 판마다 올라간다 — **`normalize` 의 답이 바뀔 수 있다** |
| `euc-kr` 과 `cp949` 가 `"가A"` 에 같은 바이트를 낸 것 | 겹치는 구간이라 같았을 뿐 |
| 이 머신의 `locale.getpreferredencoding()` 이 `UTF-8` | **머신·환경변수에 달렸다.** `open()` 의 기본값이 여기 달렸으므로 윈도에서는 다른 답이 나온다 |

**그래서 이렇게 적으면 틀린다**

- ✗ 「파이썬 문자열은 유니코드로 저장된다」\
  ○ **코드 포인트 열**이다. 「유니코드」는 인코딩 이름이 아니다.
- ✗ 「한글은 3바이트다」 → ○ **utf-8 에서** 3바이트다.
- ✗ 「문자열은 글자당 N바이트다」 → ○ **문자열마다 다르고**, 그 수는 구현 세부사항이다.
- ✗ 「`b"a" == "a"` 는 에러가 난다」 → ○ **`False`** 다.
- ✗ 「눈에 같으면 `==` 로 같다」 → ○ **정규화가 다르면 다르다.**

> **구현 세부사항(implementation detail)** — 언어 명세가 보장하지 않고 특정 구현이 그렇게 만들어 둔 것.\
> 여기서는 `getsizeof` 의 숫자와 한 글자 싱글턴이 그것이다. **문서가 스스로 그렇게 적은 드문 경우**다.

**판정 기준 한 줄**

**「몇 바이트인가」와 「몇 글자인가」를 같은 것으로 쓰고 있으면 그 자리가 버그 후보다.**

### 11. 「몇 글자인가」에 답이 넷이다 (연결)

**네 질문과 네 도구**

```python
import unicodedata
s = "cafe\u0301"
print("① 코드 포인트 수 :", len(s))
print("② 보이는 글자 수 :", sum(1 for c in s if not unicodedata.combining(c)))
print("③ 터미널 칸 수   :", sum(2 if unicodedata.east_asian_width(c) in "WF" else 0 if unicodedata.combining(c) else 1 for c in s))
print("④ utf-8 바이트 수:", len(s.encode("utf-8")))
```

```text
① 코드 포인트 수 : 5
② 보이는 글자 수 : 4
③ 터미널 칸 수   : 4
④ utf-8 바이트 수: 6
```

한글로 재면 ②와 ③이 갈린다.

```python
import unicodedata
t = "한글ab"
print("① len          :", len(t))
print("② 보이는 글자   :", sum(1 for c in t if not unicodedata.combining(c)))
print("③ 터미널 칸     :", sum(2 if unicodedata.east_asian_width(c) in "WF" else 0 if unicodedata.combining(c) else 1 for c in t))
print("④ utf-8 바이트  :", len(t.encode("utf-8")))
```

```text
① len          : 4
② 보이는 글자   : 4
③ 터미널 칸     : 6
④ utf-8 바이트  : 8
```

**어느 자리에 어느 답을 쓰나**

| 자리 | 쓰는 답 | 왜 |
|---|---|---|
| 슬라이스·인덱스 | ① `len` | 인덱스가 코드 포인트 단위다 |
| 「닉네임 10자 제한」 | ② (또는 자소 클러스터) | 사용자가 세는 것이 이것이다 |
| 표 정렬·터미널 폭 맞추기 | ③ `east_asian_width` | `ljust` 는 ①로 세므로 **한글 표가 어긋난다** |
| DB `VARCHAR(n)`·HTTP `Content-Length` | ④ 바이트 | 저장·전송은 바이트가 단위다 |
| 파일 크기·해시 입력 | ④ 바이트 | `hashlib` 는 `bytes` 만 받는다 |

```text
 "한글ab" 에 대해

   len()              4    <- 슬라이스가 쓰는 단위
   보이는 글자         4    <- 사용자가 세는 단위
   터미널 칸          6    <- 표를 그릴 때의 단위
   utf-8 바이트       8    <- 저장·전송의 단위

  ★ 네 개가 전부 다르다. "글자 수" 라는 말만으로는 어느 것인지 정해지지 않는다.
```

**한 문장으로**

**`len` 은 코드 포인트를 센다** — 그것은 네 답 중 **하나**일 뿐이다.\
코드에서 「글자 수」를 쓰고 있다면, **그 줄이 네 질문 중 어느 것을 묻는지** 먼저 정해야 한다.
그리고 ②는 표준 라이브러리만으로는 **결합 문자까지만** 처리된다 — 가족 이모지는 여전히 5로 센다.

---

## 실행 검증

이 파일에 실린 출력은 전부 아래 환경에서 직접 돌려 얻었다.

```text
$ python3 --version
Python 3.12.3
$ python3 -c "import sys, unicodedata; print(sys.implementation.name, sys.maxunicode, unicodedata.unidata_version)"
cpython 1114111 15.0.0
```

| 문항 | 무엇을 돌렸나 | 몇 번 |
|---|---|---|
| 1 | 네 문자열의 `len`, utf-8 바이트 수, 가족 이모지 슬라이스와 코드 포인트 분해 | 각 1회 |
| 2 | NFC/NFD 의 `len`·`==`·`dict`·`set`·`sort`, NFKC 네 글자 | 각 1회 |
| 3 | `bytes` 의 인덱싱·슬라이싱·`list`·`for`, `str` 과 대조 | 각 1회 |
| 4 | 섞은 네 연산 + `==`/`!=`/`bytearray` 비교/`str(b)`, **`-b`·`-bb` 로 같은 파일 재실행** | 각 1회 (세 판) |
| 5 | 서로게이트의 `ord`·세 인코딩·`surrogatepass`·`surrogateescape` 왕복 | 각 1회 |
| 6 | `getsizeof` 10·11·100글자 세 종류, latin-1 1\~3글자, `chr` 싱글턴 3종 | 각 1회 |
| 7 | `latin-1` 디코딩과 왕복, `euc-kr` 실패 | 각 1회 |
| 8 | 에러 핸들러 encode 6종 · decode 5종 | 각 1회 |
| 9 | `chr` 범위 밖 2종, `ord` 길이 오류 2종, `ord(b"a")`, 서로게이트 | 각 1회 |
| 11 | `"cafe\u0301"` 과 `"한글ab"` 의 네 가지 세기 | 각 1회 |

**★ 한 판으로 결론이 안 나는 것을 두 판 이상 던진 자리**

- **6번** — `getsizeof` 를 **한 글자로만 재면 규칙이 거꾸로 보인다**(61 > 59). 2·3글자를 같이 재고
  `chr(0xe9) is chr(0xe9)` 로 확인해서야 **싱글턴 + utf-8 캐시**라는 원인이 드러났다.
- **4번** — 기본 실행만 보면 `b"a" == "a"` 는 그냥 `False` 다. **`-b`·`-bb` 로 두 번 더 돌려야**
  「경고가 있는데 꺼져 있다」가 보인다. **따로 물어야 보이는 출력**이었다.
- **7번** — `latin-1` 이 에러를 안 내는 것만으로는 「위험하다」가 안 선다.
  `euc-kr` 이 **터지는 출력**을 나란히 놓아야 「에러가 정보였다」가 근거가 된다.

**「출력 없음」·「에러 없음」이 근거인 자리**

- 4번 — `b"a" == "a"` 에서 **예외가 안 난 것**이 「조용한 구멍」의 증거다.
- 7번 — `latin-1` 디코딩에서 **예외가 안 난 것**이 「거부 기준이 없다」의 증거다.
- 8번 — `ignore` 가 `b'nb'` 만 남기고 **아무 경고도 안 낸 것**이 「손실이 조용하다」의 증거다.

**구현 의존 항목 — 버전이 오르면 다시 찍을 것**

| 다시 찍을 것 | 왜 |
|---|---|
| 6번의 모든 `getsizeof` 수 | 문서가 *"implementation specific"* 이라고 적는다 |
| 6번의 한 글자 싱글턴 | 캐시 범위·utf-8 선반영 여부가 판마다 다르다 |
| 2번의 정규화 결과 | `unidata_version` 이 오르면 달라질 수 있다 |
| 예외 **문구** 전부 | 예외 종류는 명세지만 문구는 아니다 |
| `locale.getpreferredencoding()` 에 딸린 것 | 머신·OS·환경변수에 달렸다 |

나머지(코드 포인트 열이라는 정의, `len` 이 세는 것, `b[0]` 이 정수인 것, `encode`/`decode` 의 방향,
에러 핸들러의 의미, 서로게이트가 `encode` 에서 거부되는 것, `sys.maxunicode`)는 **언어 보장**이므로 어떤 구현에서도 같아야 한다.
