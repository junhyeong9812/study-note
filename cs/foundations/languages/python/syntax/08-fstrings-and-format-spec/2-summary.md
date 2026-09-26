# python/syntax/08-fstrings-and-format-spec — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [2.4.3. f-strings](https://docs.python.org/3.12/reference/lexical_analysis.html#f-strings) — 언어 레퍼런스의 정의와 문법
> - [Format Specification Mini-Language](https://docs.python.org/3.12/library/string.html#format-specification-mini-language) — 포맷 스펙 문법(EBNF)
> - [Format String Syntax](https://docs.python.org/3.12/library/string.html#format-string-syntax) — `str.format` 의 치환 필드
> - [printf-style String Formatting](https://docs.python.org/3.12/library/stdtypes.html#printf-style-string-formatting) — `%` 포맷
> - [PEP 701 — Syntactic formalization of f-strings](https://peps.python.org/pep-0701/) (3.12)
> - [`dis`](https://docs.python.org/3.12/library/dis.html) — 바이트코드 명령
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> **버전** — f-string 자체는 3.6+. **`=` 디버그 표기는 3.8+**, **`z` 옵션은 3.11+**,
> **PEP 701(중첩 따옴표·백슬래시·주석 허용)은 3.12+**.
> 바이트코드 명령 이름(`FORMAT_VALUE`·`BUILD_STRING`)은 **3.12 의 것**이다.
> **선행** — [06-strings-bytes-unicode](../06-strings-bytes-unicode/2-summary.md)(만들어지는 것이 `str` 이다) ·
> [01-object-and-name-binding](../01-object-and-name-binding/2-summary.md)(평가 시점과 이름 바인딩).

## 한눈에 — 쉽게 말하면

**f-string 은 「문자열」이 아니라 「문자열을 만드는 식」이다. 소스에 적힌 모양과 컴파일된 것이 다르다.**

```text
 소스에 적은 것                     컴파일러가 만든 것 (3.12)

  f"a{x}b"          ------->        LOAD_CONST   'a'
                                    LOAD_NAME    x
                                    FORMAT_VALUE
                                    LOAD_CONST   'b'
                                    BUILD_STRING 3

  ★ 문자열 리터럴이 아니다. 조각을 쌓아 만드는 식이다.
    그래서 "만들어질 때" 값이 굳는다 — 나중에 x 를 바꿔도 안 따라온다.
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 붕어빵 틀이 아니라 **즉석에서 구워 낸 붕어빵** | f-string | 만든 뒤 재료를 바꿔도 안 변한다 |
| 다시 구울 수 있는 **틀** | `str.format` · `string.Template` | 템플릿을 변수에 담아 나중에 쓴다 |
| 재료를 어떻게 다듬어 넣을지 적은 쪽지 | 포맷 스펙(`:>10.2f`) | 콜론 뒤가 전부 쪽지다 |
| 「날것으로 넣을까 포장해 넣을까」 | `!s` · `!r` · `!a` | 느낌표 뒤 한 글자 |
| 재료 쪽에 붙은 「나를 이렇게 다듬어라」 | `__format__` | 쪽지를 받는 것은 객체 자신이다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
**로깅**이다. `log.debug(f"...")` 는 로그 레벨이 막든 말든 **문자열을 먼저 만든다.**
f-string 이 「틀」이 아니라 「구워 낸 것」이기 때문이다.

> **치환 필드(replacement field)** — f-string 안의 `{...}` 한 덩어리.\
> 문법은 `{식 [=] [!변환] [:포맷스펙]}` 이고 네 부분이 순서까지 고정돼 있다.

## 이 주제가 답하려는 질문

1. **f-string 은 언제 평가되는가** — 그리고 그것이 로깅에서 왜 문제가 되는가.
2. **`dis` 로 보면 무엇으로 컴파일되는가** — 3.12 에서 `%` 포맷과 f-string 이 같은 바이트코드가 되는 자리.
3. **포맷 스펙을 누가 해석하는가** — `__format__`·`__str__`·`__repr__` 셋의 관계.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### 1. f-string 은 리터럴이 아니라 식이다

**언제 쓰나** — 문자열을 만드는 모든 자리. 그리고 「왜 값이 안 바뀌지?」를 물을 때.

문서의 정의 한 줄이 전부다 —\
*"A formatted string literal or f-string is a string literal that is prefixed with `'f'` or `'F'`... While other string literals always have a constant value, **formatted strings are really expressions evaluated at run time**."*

```text
 x = 1
 s = f"x 는 {x}"      <- 이 줄에서 x 를 읽고 문자열을 만들어 버린다
 x = 2
 print(s)             <- 이미 만들어진 문자열. "x 는 1"

 t = "x 는 {x}"       <- 이것은 그냥 문자열이다. 아직 아무것도 안 읽었다
 print(t.format(x=x)) <- 쓰는 순간 x 를 읽는다. "x 는 2"
```

```python
x = 1
s = f"x 는 {x}"
x = 2
print(s, " <- 나중에 x 를 바꿔도 안 따라온다")
t = "x 는 {x}"
print(t.format(x=x), " <- str.format 은 쓸 때 평가한다")

def f(v=f"기본 {x}"):
    return v
x = 99
print("기본 인자도 def 를 만날 때 한 번:", f())
```

```text
x 는 1  <- 나중에 x 를 바꿔도 안 따라온다
x 는 2  <- str.format 은 쓸 때 평가한다
기본 인자도 def 를 만날 때 한 번: 기본 2
```

그림 해설.

- **f-string 은 그 줄을 지날 때 한 번 평가된다.** 이름 바인딩 모델 그대로다([01번](../01-object-and-name-binding/2-summary.md)).
- 기본 인자에 쓴 f-string 도 **`def` 문을 만날 때 한 번**이다([20번](../20-mutable-default-args/2-summary.md)의 그 규칙이다).
- 문서가 평가 순서까지 적는다 — *"Each expression is evaluated in the context where the formatted string literal appears, **in order from left to right**."*

**비용** — 중괄호 안에 임의의 식을 쓸 수 있고 이름이 그 자리에서 풀린다(오타가 `NameError` 로 바로 잡힌다).\
대신 **지연시킬 수가 없다.** 그것이 8번 절의 주제다.

### 2. ★ `dis` — 소스에 적은 것과 컴파일된 것이 다르다

**언제 쓰나** — 「f-string 이 느리냐」를 물을 때. 그리고 3.12 가 무엇을 바꿨는지 확인할 때.

```python
import dis
dis.dis(compile('r = f"{x}"', "<f>", "exec"))
```

```text
  0           0 RESUME                   0

  1           2 LOAD_NAME                0 (x)
              4 FORMAT_VALUE             0
              6 STORE_NAME               1 (r)
              8 RETURN_CONST             0 (None)
```

```python
dis.dis(compile('r = f"a{x}b"', "<f>", "exec"))
```

```text
  0           0 RESUME                   0

  1           2 LOAD_CONST               0 ('a')
              4 LOAD_NAME                0 (x)
              6 FORMAT_VALUE             0
              8 LOAD_CONST               1 ('b')
             10 BUILD_STRING             3
             12 STORE_NAME               1 (r)
             14 RETURN_CONST             2 (None)
```

```text
 명령                     무슨 일인가
 ----------------------  -------------------------------------------
 LOAD_CONST 'a'          고정 조각은 상수다 (컴파일 때 이미 정해졌다)
 LOAD_NAME x             중괄호 안의 식만 실행 시에 평가한다
 FORMAT_VALUE 0          그 값을 format(value, '') 으로 다듬는다
 LOAD_CONST 'b'          고정 조각
 BUILD_STRING 3          스택의 세 조각을 이어 하나로 만든다
```

★ **`+` 도 `str.join` 도 호출이 없다.** 전용 명령 두 개로 끝난다 — 그래서 빠르다.

**변환과 스펙이 붙으면 인자가 달라진다**

```python
dis.dis(compile('r = f"{x!r:>10}"', "<f>", "exec"))
```

```text
  0           0 RESUME                   0

  1           2 LOAD_NAME                0 (x)
              4 LOAD_CONST               0 ('>10')
              6 FORMAT_VALUE             6 (repr, with format)
              8 STORE_NAME               1 (r)
             10 RETURN_CONST             1 (None)
```

`FORMAT_VALUE` 의 인자가 **어떤 변환을 쓸지 + 스펙이 있는지**를 담는다.\
`'>10'` 은 **상수**다 — 스펙 자체는 컴파일 때 굳는다(단 중첩 중괄호를 쓰면 그것도 실행 시에 만든다, 7번 절).

**★ PEP 701 이 바꾼 것은 바이트코드가 아니라 토크나이저다**

```python
import tokenize, io
for t in tokenize.generate_tokens(io.StringIO('f"a{x!r:>10}b"').readline):
    if t.type in (4, 0):
        continue
    print(f"{tokenize.tok_name[t.type]:14} {t.string!r}")
```

```text
FSTRING_START  'f"'
FSTRING_MIDDLE 'a'
OP             '{'
NAME           'x'
OP             '!'
NAME           'r'
OP             ':'
FSTRING_MIDDLE '>10'
OP             '}'
FSTRING_MIDDLE 'b'
FSTRING_END    '"'
```

```python
for t in tokenize.generate_tokens(io.StringIO('"abc"').readline):
    if t.type in (4, 0):
        continue
    print(f"{tokenize.tok_name[t.type]:14} {t.string!r}")
```

```text
STRING         '"abc"'
```

★ **보통 문자열은 토큰 하나인데 f-string 은 여러 토큰으로 쪼개진다.**\
3.11 까지는 f-string 도 **`STRING` 토큰 하나**였고 파서가 그 안을 따로 다시 파싱했다.
3.12 가 그것을 **정식 문법으로 끌어올렸다**(PEP 701) — 이 토큰 목록이 그 증거다.

**그래서 3.12 에서 전에 안 되던 것이 된다**

```python
d = {"key": "값"}
print(f"바깥 큰따옴표 안에 {d["key"]} 를 그대로")
print(f"줄바꿈을 식 안에서: {'a\nb'.split('\n')}")
print(f"""여러 줄 식 + 주석: {
    d["key"]    # 여기 주석이 들어간다
}""")
print(f"{f"{f"{1+1}"}"}")
print(f"{"중첩"!r}")
```

```text
바깥 큰따옴표 안에 값 를 그대로
줄바꿈을 식 안에서: ['a', 'b']
여러 줄 식 + 주석: 값
2
'중첩'
```

| 3.11 까지 | 3.12(PEP 701) |
|---|---|
| 바깥과 **같은 따옴표**를 안에서 못 쓴다 | 쓸 수 있다 |
| 식 안에 **백슬래시** 금지 | 허용 |
| 식 안에 **주석**·줄바꿈 금지(작은따옴표 f-string) | 허용 |
| 중첩 깊이 제한 있음 | 제한 없음 |

문서가 셋 다 *"Changed in version 3.12"* 로 적는다.

**오류 메시지도 훨씬 구체적이다**

```python
for src in ('f"{}"', 'f"{ }"', 'f"{x!z}"', 'f"{x;}"'):
    try:
        compile(src, "<x>", "eval")
        print(f"{src:12} -> 컴파일됨")
    except SyntaxError as e:
        print(f"{src:12} -> SyntaxError: {e.msg}")
```

```text
f"{}"        -> SyntaxError: f-string: valid expression required before '}'
f"{ }"       -> SyntaxError: f-string: valid expression required before '}'
f"{x!z}"     -> SyntaxError: f-string: invalid conversion character 'z': expected 's', 'r', or 'a'
f"{x;}"      -> SyntaxError: f-string: expecting '=', or '!', or ':', or '}'
```

**비용** — 전용 바이트코드라 호출이 없고, 3.12 부터 따옴표·백슬래시 제약이 사라졌다.\
대신 **문법이 더 복잡해졌고**, 같은 따옴표를 겹쳐 쓴 코드는 **3.11 에서 안 돈다.**

### 3. 포맷 스펙 — 콜론 뒤의 작은 언어

**언제 쓰나** — 표·영수증·로그·보고서를 만들 때.

문서의 EBNF 가 정본이다.

```text
 format_spec ::= [[fill]align][sign]["z"]["#"]["0"][width][grouping]["." precision][type]

   fill      ::= 아무 글자 하나
   align     ::= "<" | ">" | "=" | "^"
   sign      ::= "+" | "-" | " "
   grouping  ::= "," | "_"
   type      ::= b c d e E f F g G n o s x X %
```

```text
  f"{값:*^+#010_.2f}"
       |||||||||||
       ||||||||||+- type      f  : 고정 소수점
       |||||||||+-- precision .2 : 소수 둘째 자리까지
       ||||||||+--- grouping  _  : 천 단위 구분
       |||||||+---- width     10 : 최소 10칸
       ||||||+----- 0            : 부호 인식 0 채우기
       |||||+------ #            : 진법 접두사 (0b/0o/0x)
       ||||+------- z            : -0.0 을 0.0 으로 (3.11+)
       |||+-------- sign      +  : 양수에도 부호
       ||+--------- align     ^  : 가운데 정렬
       |+---------- fill      *  : 남는 칸을 * 로
       +----------- :            : 여기부터가 스펙이다
```

```python
rows = [
    ("{:10}",   f"{42:10}"),      ("{:<10}|", f"{42:<10}|"),
    ("{:>10}|", f"{42:>10}|"),    ("{:^10}|", f"{42:^10}|"),
    ("{:*^10}|", f"{42:*^10}|"),  ("{:=10}",  f"{-42:=10}"),
    ("{:010}",  f"{-42:010}"),    ("{:+d}",   f"{42:+d}"),
    ("{: d}",   f"{42: d}"),      ("{:-d}",   f"{42:-d}"),
    ("{:,}",    f"{1234567:,}"),  ("{:_}",    f"{1234567:_}"),
    ("{:.2f}",  f"{-1234.5678:.2f}"),  ("{:,.2f}", f"{-1234.5678:,.2f}"),
    ("{:.3}",   f"{-1234.5678:.3}"),   ("{:.3s}",  f"{'abcdef':.3s}"),
    ("{:e}",    f"{-1234.5678:e}"),    ("{:g}",    f"{-1234.5678:g}"),
    ("{:%}",    f"{0.1234:%}"),        ("{:.1%}",  f"{0.1234:.1%}"),
    ("{:b}",    f"{10:b}"),            ("{:#b}",   f"{10:#b}"),
    ("{:x} {:X} {:#x}", f"{255:x} {255:X} {255:#x}"),
    ("{:#010x}", f"{255:#010x}"),      ("{:c}",    f"{44032:c}"),
]
for spec, out in rows:
    print(f"{spec:20} -> {out!r}")
```

```text
{:10}                -> '        42'
{:<10}|              -> '42        |'
{:>10}|              -> '        42|'
{:^10}|              -> '    42    |'
{:*^10}|             -> '****42****|'
{:=10}               -> '-       42'
{:010}               -> '-000000042'
{:+d}                -> '+42'
{: d}                -> ' 42'
{:-d}                -> '42'
{:,}                 -> '1,234,567'
{:_}                 -> '1_234_567'
{:.2f}               -> '-1234.57'
{:,.2f}              -> '-1,234.57'
{:.3}                -> '-1.23e+03'
{:.3s}               -> 'abc'
{:e}                 -> '-1.234568e+03'
{:g}                 -> '-1234.57'
{:%}                 -> '12.340000%'
{:.1%}               -> '12.3%'
{:b}                 -> '1010'
{:#b}                -> '0b1010'
{:x} {:X} {:#x}      -> 'ff FF 0xff'
{:#010x}             -> '0x000000ff'
{:c}                 -> '가'
```

그림 해설.

- ★ **`=` 는 부호와 숫자 사이에 채운다.** `'-       42'` — 회계 표기에 쓴다.\
  문서가 *"Forces the padding to be placed after the sign (if any) but before the digits"* 라고 적는다.
- ★ **`0` 을 width 앞에 두면 `=` 정렬이 기본이 된다.** `f"{-42:010}"` 이 `'-000000042'` 다.\
  문서 — *"This is equivalent to a fill character of `'0'` with an alignment type of `'='`."*
- **`.3` 에 타입이 없으면 `g`** 로 간다 — `'-1.23e+03'`. 유효숫자 3개다.
- **`.3s`** 는 **자르기**다 — 문자열에서 precision 은 최대 길이다.
- **`#010x`** 는 `0x` 접두사까지 10칸 안에 넣는다.
- **`c`** 는 정수를 그 코드 포인트의 글자로 바꾼다 — `chr` 과 같다([06번](../06-strings-bytes-unicode/2-summary.md)).

**★ 정렬의 기본값이 타입마다 다르다**

```python
for v in (42, "ab", True, 3.5, None, [1]):
    try:
        print(f"  {type(v).__name__:8} |{v:10}|")
    except TypeError as e:
        print(f"  {type(v).__name__:8} TypeError: {e}")
```

```text
  int      |        42|
  str      |ab        |
  bool     |         1|
  float    |       3.5|
  NoneType TypeError: unsupported format string passed to NoneType.__format__
  list     TypeError: unsupported format string passed to list.__format__
```

```text
 문서:  '<' 는 "the default for most objects"
        '>' 는 "the default for numbers"

  숫자  -> 오른쪽 정렬   (표에서 자릿수가 맞는다)
  문자열 -> 왼쪽 정렬
  bool  -> ★ 숫자다. True 가 '1' 로 찍히고 오른쪽 정렬된다
  None·list -> ★ 스펙을 못 받는다. TypeError
```

★ **`f"{True:10}"` 이 `'         1'` 이다.** `bool` 이 `int` 의 하위 클래스라 `int` 의 `__format__` 을 쓴다([04번](../04-numeric-types-and-division/2-summary.md)).\
★ **`None` 과 `list` 는 스펙을 주면 터진다.** 빈 스펙(`f"{None}"`)은 된다 — 5번 절이 그 이유다.

**`z` 옵션(3.11+)은 음수 0 을 지운다**

```python
print("z 있음:", f"{-0.0:z.1f}", "| z 없음:", f"{-0.0:.1f}")
print("반올림돼 0 이 된 것도:", f"{-0.0001:z.2f}", "|", f"{-0.0001:.2f}")
```

```text
z 있음: 0.0 | z 없음: -0.0
반올림돼 0 이 된 것도: 0.00 | -0.00
```

보고서에 `-0.00` 이 찍히는 것을 막는 옵션이다.

**비용** — 한 줄로 정렬·자릿수·천단위·진법이 다 된다.\
대신 **스펙이 타입마다 뜻이 다르다**(`.3` 이 숫자에서는 유효숫자, 문자열에서는 길이).

### 4. `!r`·`!s`·`!a` 와 `=` — 변환은 스펙보다 먼저다

**언제 쓰나** — 로그·디버그 출력. 값이 무엇인지 헷갈릴 때.

```text
 f"{x!r:>12}"
      ^^  ^^^^
      |    +--- 2단계: 그 문자열에 포맷 스펙을 건다
      +-------- 1단계: 먼저 repr(x) 로 문자열을 만든다

  ★ 순서가 고정이다. 문법도 {식 [=] [!변환] [:스펙]} 순서다.
```

```python
class P:
    def __str__(self):  return "str 판"
    def __repr__(self): return "repr 판"
    def __format__(self, spec): return f"format 판(spec={spec!r})"

p = P()
print(f"기본     : {p}")
print(f"!s       : {p!s}")
print(f"!r       : {p!r}")
print(f"스펙 있음 : {p:>8}")
print(f"!r + 스펙: {p!r:>12}")
```

```text
기본     : format 판(spec='')
!s       : str 판
!r       : repr 판
스펙 있음 : format 판(spec='>8')
!r + 스펙:       repr 판
```

★ **`{p}` 는 `__str__` 이 아니라 `__format__` 을 부른다.** 이것이 이 주제 최대의 오해다.\
★ **`!s` 를 붙이면 그때서야 `__str__`** 이다. 그리고 그 뒤 `__format__` 은 **안 불린다** — 이미 `str` 이 됐으니 `str.__format__` 이 스펙을 받는다.

| 변환 | 무엇을 부르나 | 언제 쓰나 |
|---|---|---|
| (없음) | `format(x, spec)` → `type(x).__format__` | 보통 |
| `!s` | `str(x)` | `__format__` 을 우회하고 싶을 때 |
| `!r` | `repr(x)` | **로그**. 값이 `''` 인지 `None` 인지 구별해야 할 때 |
| `!a` | `ascii(x)` | 비-ASCII 를 이스케이프로 보고 싶을 때 |

```python
s = "가나다"
print(f"!a  : {s!a}")
print("ascii():", ascii(s))
```

```text
!a  : '\uac00\ub098\ub2e4'
ascii(): '\uac00\ub098\ub2e4'
```

**`=` 는 식의 텍스트를 그대로 옮긴다 (3.8+)**

```python
x = 42
name = "값"
print(f"{x=}")
print(f"{x = }")
print(f"{x=:05d}")
print(f"{name=}")
print(f"{x+1=}")
print(f"{ x  +  1 = }")
```

```text
x=42
x = 42
x=00042
name='값'
x+1=43
 x  +  1 = 43
```

그림 해설.

- ★ **`=` 는 기본이 `!r`** 이다. `f"{name=}"` 이 `name='값'` 으로 **따옴표까지** 찍힌다.
- ★ **스펙을 붙이면 `!r` 이 아니라 그 스펙**을 쓴다. `f"{x=:05d}"` 가 `x=00042`.
- ★ **공백까지 그대로 옮긴다.** 문서 — *"Spaces after the opening brace `'{'`, within the expression and after the `'='` are all retained in the output."*

**비용** — `print(f"{x=}")` 한 줄이 `print("x =", repr(x))` 를 대신한다. 이름을 두 번 쓸 일이 없어 **오타로 어긋날 수가 없다.**\
대신 3.8 미만에서는 안 돈다.

### 5. `__format__` 과 `__str__`/`__repr__` 의 관계

**언제 쓰나** — 직접 만든 클래스를 f-string 에 넣을 때. 그리고 `TypeError` 가 날 때.

```text
 f"{x}"  ->  format(x, "")  ->  type(x).__format__(x, "")
                                        |
                       정의 안 했으면 object.__format__ 이 쓰인다
                                        |
                       +----------------+----------------+
                       |                                 |
                  spec 이 빈 문자열                  spec 이 비어 있지 않다
                       |                                 |
                  str(self) 를 돌려준다              ★ TypeError 를 던진다
```

```python
class OnlyStr:
    def __str__(self):  return "내 str"
    def __repr__(self): return "내 repr"

o = OnlyStr()
print("빈 스펙:", f"{o}")
try:
    print(f"{o:>10}")
except TypeError as e:
    print("스펙을 주면 ->", type(e).__name__, e)
```

```text
빈 스펙: 내 str
스펙을 주면 -> TypeError unsupported format string passed to OnlyStr.__format__
```

★ **3번 절에서 `f"{None:10}"` 이 터진 것과 같은 이유다.** `None` 도 `__format__` 을 따로 안 갖고 있다.

**다섯 경로가 같은 곳으로 모인다**

```python
print("format(o)      =", format(o))
print("format(o, '')  =", format(o, ""))
print("str(o)         =", str(o))
print("'{}'.format(o) =", "{}".format(o))
print("'%s' % o       =", "%s" % o)
print("'%r' % o       =", "%r" % o)
```

```text
format(o)      = 내 str
format(o, '')  = 내 str
str(o)         = 내 str
'{}'.format(o) = 내 str
'%s' % o       = 내 str
'%r' % o       = 내 repr
```

**`__repr__` 만 있으면 `__str__` 도 그것을 쓴다**

```python
class OnlyRepr:
    def __repr__(self): return "오직 repr"

r = OnlyRepr()
print(str(r), "|", format(r), "|", f"{r}")
```

```text
오직 repr | 오직 repr | 오직 repr
```

```text
 세 메서드의 기본값 사슬

  __format__ 없음 -> object.__format__ -> str(self)   (빈 스펙일 때만)
  __str__    없음 -> object.__str__    -> repr(self)
  __repr__   없음 -> object.__repr__   -> '<...object at 0x...>'

  ★ 그래서 __repr__ 하나만 정의해도 세 자리가 다 채워진다.
    반대로 __str__ 만 정의하면 로그의 repr 자리가 비어 있다.
```

**내장 타입은 스펙을 자기 식으로 쓴다**

```python
import datetime
d = datetime.date(2026, 9, 23)
print("date 의 스펙은 strftime 형식:", f"{d:%Y년 %m월 %d일}", "| 빈 스펙:", f"{d}")
print("int 의 __format__ 직접 호출  :", (255).__format__("#x"))
print("bool 은 int 의 것을 쓴다      :", f"{True:d}", f"{True:05.1f}")
```

```text
date 의 스펙은 strftime 형식: 2026년 09월 23일 | 빈 스펙: 2026-09-23
int 의 __format__ 직접 호출  : 0xff
bool 은 int 의 것을 쓴다      : 1 001.0
```

★ **포맷 스펙 미니 언어는 「기본 해석」일 뿐 규약이 아니다.** `datetime` 은 그 자리를 `strftime` 형식으로 쓴다.\
직접 만든 클래스도 `__format__` 을 정의하면 스펙을 **아무 뜻으로나** 쓸 수 있다.

**비용** — 객체가 자기 포맷을 정할 수 있어 `f"{money:,.2f}"` 같은 표현이 도메인 타입에서도 된다.\
대신 **`{x}` 가 `str(x)` 라는 착각**이 생기고, `__format__` 을 안 만든 타입에 스펙을 주면 터진다.

### 6. ★ `%` 포맷·`str.format`·f-string — `dis` 가 셋을 가른다

**언제 쓰나** — 「무엇을 쓸까」를 고를 때. 그리고 성능 이야기가 나올 때.

```python
import dis
cases = {
  '"%s-%s" % (a, b)': 'r = "%s-%s" % (a, b)',
  '"{}-{}".format(a, b)': 'r = "{}-{}".format(a, b)',
  'f"{a}-{b}"': 'r = f"{a}-{b}"',
}
for label, src in cases.items():
    ops = [i.opname + (f"({i.argrepr})" if i.argrepr else "")
           for i in dis.get_instructions(compile(src, "<x>", "exec")) if i.opname != "RESUME"]
    print(f"{label:22} {ops}")
```

```text
"%s-%s" % (a, b)       ['LOAD_NAME(a)', 'FORMAT_VALUE(str)', "LOAD_CONST('-')", 'LOAD_NAME(b)', 'FORMAT_VALUE(str)', 'BUILD_STRING', 'STORE_NAME(r)', 'RETURN_CONST(None)']
"{}-{}".format(a, b)   ["LOAD_CONST('{}-{}')", 'LOAD_ATTR(NULL|self + format)', 'LOAD_NAME(a)', 'LOAD_NAME(b)', 'CALL', 'STORE_NAME(r)', 'RETURN_CONST(None)']
f"{a}-{b}"             ['LOAD_NAME(a)', 'FORMAT_VALUE', "LOAD_CONST('-')", 'LOAD_NAME(b)', 'FORMAT_VALUE', 'BUILD_STRING', 'STORE_NAME(r)', 'RETURN_CONST(None)']
```

★★ **`%` 포맷이 f-string 과 거의 같은 바이트코드가 됐다.** `BINARY_OP %` 가 **아예 없다.**\
컴파일러가 `%` 를 통째로 접어 버린 것이다. 「`%` 는 연산자 호출이라 느리다」가 이 판에서는 틀린다.

**★ 그런데 아무 `%` 나 접히는 것이 아니다**

```python
cases = {
  '"%s" % (a,)': 'r = "%s" % (a,)',    '"%r" % (a,)': 'r = "%r" % (a,)',
  '"%a" % (a,)': 'r = "%a" % (a,)',    '"%d" % (a,)': 'r = "%d" % (a,)',
  '"%x" % (a,)': 'r = "%x" % (a,)',    '"%s" % a': 'r = "%s" % a',
  '"%s" % t': 'r = "%s" % t',          '"%(k)s" % d': 'r = "%(k)s" % d',
  '"100%% %s" % (a,)': 'r = "100%% %s" % (a,)',
}
for label, src in cases.items():
    ops = [i.opname for i in dis.get_instructions(compile(src, "<x>", "exec"))
           if i.opname in ("FORMAT_VALUE", "BINARY_OP", "BUILD_STRING", "BUILD_TUPLE")]
    print(f"{label:20} {ops}")
```

```text
"%s" % (a,)          ['FORMAT_VALUE']
"%r" % (a,)          ['FORMAT_VALUE']
"%a" % (a,)          ['FORMAT_VALUE']
"%d" % (a,)          ['BUILD_TUPLE', 'BINARY_OP']
"%x" % (a,)          ['BUILD_TUPLE', 'BINARY_OP']
"%s" % a             ['BINARY_OP']
"%s" % t             ['BINARY_OP']
"%(k)s" % d          ['BINARY_OP']
"100%% %s" % (a,)    ['FORMAT_VALUE', 'BUILD_STRING']
```

```text
 접히는 조건 (3.12 관찰)

   왼쪽이 리터럴이고
   오른쪽이 "리터럴 튜플" 이고
   변환이 %s / %r / %a 뿐일 때
        -> FORMAT_VALUE 로 접힌다

   %d · %x · 튜플이 아닌 오른쪽 · %(name)s
        -> BINARY_OP % 로 남는다
```

**★ 접힌 것이 f-string 과 「같다」고 하면 한 칸이 틀린다**

```python
for label, src in {'f"{a}"': 'r = f"{a}"', 'f"{a!s}"': 'r = f"{a!s}"', '"%s" % (a,)': 'r = "%s" % (a,)'}.items():
    ops = [f"{i.opname}({i.argrepr})" for i in dis.get_instructions(compile(src, "<x>", "exec")) if i.opname == "FORMAT_VALUE"]
    print(f"{label:14} {ops}")
```

```text
f"{a}"         ['FORMAT_VALUE()']
f"{a!s}"       ['FORMAT_VALUE(str)']
"%s" % (a,)    ['FORMAT_VALUE(str)']
```

```python
class P:
    def __str__(self): return "str 판"
    def __format__(self, spec): return "format 판"
p = P()
print('f"{p}"      ->', f"{p}")
print('"%s" % (p,) ->', "%s" % (p,))
print('f"{p!s}"    ->', f"{p!s}")
```

```text
f"{p}"      -> format 판
"%s" % (p,) -> str 판
f"{p!s}"    -> str 판
```

★ **`"%s" % (a,)` 는 `f"{a!s}"` 와 같고 `f"{a}"` 와는 다르다.**\
`%s` 는 **언제나 `str()`** 이고 f-string 의 기본은 **`__format__`** 이다.
바이트코드에 그 차이가 **인자로 그대로 찍혀 있다.**

**`%` 의 튜플 함정**

```python
t = (1, 2)
print("'%s' % 'abc' =", "%s" % "abc")
try:
    print("'%s' % t    =", "%s" % t)
except TypeError as e:
    print("'%s' % t    ->", type(e).__name__, e)
print("'%s' % (t,)  =", "%s" % (t,))
print("'%s' % [1,2] =", "%s" % [1, 2], "  <- 리스트는 안 풀린다")
try:
    "%s %s" % ("a",)
except TypeError as e:
    print("모자라면 ->", type(e).__name__, e)
```

```text
'%s' % 'abc' = abc
'%s' % t    -> TypeError not all arguments converted during string formatting
'%s' % (t,)  = (1, 2)
'%s' % [1,2] = [1, 2]   <- 리스트는 안 풀린다
모자라면 -> TypeError not enough arguments for format string
```

```text
 "%s" % X 에서 X 가

   튜플이면   -> ★ 풀린다. 원소 개수가 자리 수와 맞아야 한다
   리스트면   -> 안 풀린다. 통째로 하나의 값
   그 밖이면  -> 통째로 하나의 값

  ★ 값이 튜플일 수 있으면 "%s" % (x,) 로 감싸야 한다.
    변수 하나를 넘기는데 그것이 우연히 튜플이면 터진다 — 타입에 따라 동작이 갈린다.
```

**세 방식 비교표**

| | `%` 포맷 | `str.format` | f-string |
|---|---|---|---|
| 언제부터 | 처음부터 | 2.6+ | **3.6+** |
| 템플릿을 변수에 담을 수 있나 | ✓ | ✓ | **✗** |
| 컴파일 때 접히나 | **`%s`/`%r`/`%a` + 리터럴 튜플일 때만** | ✗ (메서드 호출) | ✓ |
| 기본 변환 | **`str()`**(`%s`) | `__format__` | `__format__` |
| 이름으로 넘기기 | `%(k)s` + dict | `{k}` + 키워드 | 이름이 **그대로 식**이다 |
| 튜플 함정 | **있다** | 없다 | 없다 |
| 사용자 입력을 템플릿으로 | 위험 | **위험**(8번 절) | **불가능**(그래서 안전) |

**비용** — f-string 이 가장 짧고 빠르고 이름 오타가 `NameError` 로 바로 잡힌다.\
대신 **지연이 안 되고 템플릿을 변수에 담을 수 없다.** 그 둘이 필요하면 `str.format` 이나 `string.Template`.

### 7. 중첩 중괄호 — 스펙 자체를 실행 시에 만든다

**언제 쓰나** — 폭·정밀도가 데이터에 달려 있을 때. 표 만들기.

```text
 f"{값:{폭}.{정밀도}f}"
        ^^^^  ^^^^^^^^
        스펙 안의 중괄호도 치환 필드다 -> 실행 시에 스펙 문자열을 만든다
```

```python
w, p = 10, 3
print(f"{3.14159:{w}.{p}f}", "|")
print(f"{3.14159:{'*'}>{w}.{p}f}", "|")
print("{:{w}.{p}f}".format(3.14159, w=10, p=3), "|")
```

```text
     3.142 |
*****3.142 |
     3.142 |
```

**표를 만들 때 실제로 쓰는 모양**

```python
rows = [("사과", 1200), ("바나나킥", 15000), ("수박", 3)]
w = max(len(name) for name, _ in rows)
for name, price in rows:
    print(f"{name:<{w}} {price:>8,}원")
```

```text
사과      1,200원
바나나킥   15,000원
수박          3원
```

★ **한글 폭이 어긋난다** — `len` 이 코드 포인트를 세고 터미널은 2칸을 쓰기 때문이다([06번](../06-strings-bytes-unicode/2-summary.md)의 「몇 글자인가」 네 답).\
포맷 스펙은 이 문제를 **풀어 주지 않는다.** `unicodedata.east_asian_width` 로 직접 세야 한다.

**★ 스펙 안의 중괄호는 「스펙을 만드는 식」이지 스펙이 아니다**

```python
w = 10
print(f"{3.14:{w}}", "|")
print(f"{3.14:{ {0:1}[0] }}", "| <- 안쪽 중괄호는 dict 리터럴이다")
```

```text
      3.14 |
3.14 | <- 안쪽 중괄호는 dict 리터럴이다
```

둘째 줄의 `{ {0:1}[0] }` 은 **식**이고 그 값 `1` 이 스펙(`width=1`)이 된다.\
안쪽 치환 필드는 **자기 스펙을 다시 가질 수 없다** — 문서의 문법이 그렇게 정의돼 있다.

**비용** — 데이터에 맞춰 폭이 정해지는 표를 한 줄로 만든다.\
대신 **스펙이 실행 시에 만들어지므로** 잘못된 스펙이 `ValueError` 로 **실행 중에** 터진다.

```python
w = "q"
try:
    print(f"{3.14:{w}}")
except ValueError as e:
    print("ValueError:", e)
```

```text
ValueError: Unknown format code 'q' for object of type 'float'
```

### 8. f-string 이 못 하는 것 — 지연 평가

**언제 쓰나** — 로깅. 이 주제에서 실무 비용이 가장 큰 자리다.

```text
 log.debug(f"값은 {expensive()}")
              ^^^^^^^^^^^^^^^^^^
              레벨이 WARNING 이어도 이 문자열은 "이미" 만들어진 뒤다.
              로깅 함수는 만들어진 문자열을 받아서 버린다.

 log.debug("값은 %s", obj)
              ^^^^^^^^^^^
              포맷은 로거가 "찍기로 결정한 뒤" 한다.
              ★ 단 obj 를 만드는 식은 여전히 호출 자리에서 평가된다.
```

```python
import logging, sys
logging.basicConfig(level=logging.WARNING, stream=sys.stdout, format="  [찍힘] %(message)s")
log = logging.getLogger("t")

class Loud:
    def __str__(self):
        print("  >>> __str__ 이 불렸다 (= 실제 포맷이 일어났다)")
        return "값"

print("[A] f-string — 포맷이 호출 자리에서 일어난다:")
log.debug(f"{Loud()}")
print("[B] % 스타일 — 레벨이 막으면 포맷 자체가 안 일어난다:")
log.debug("%s", Loud())
print("[C] 레벨을 올리면:")
log.setLevel(logging.DEBUG)
log.debug("%s", Loud())
```

```text
[A] f-string — 포맷이 호출 자리에서 일어난다:
  >>> __str__ 이 불렸다 (= 실제 포맷이 일어났다)
[B] % 스타일 — 레벨이 막으면 포맷 자체가 안 일어난다:
[C] 레벨을 올리면:
  >>> __str__ 이 불렸다 (= 실제 포맷이 일어났다)
  [찍힘] 값
```

★ **[B] 에서 아무 출력이 없는 것**이 「포맷이 지연됐다」의 증거다.

**★ 그런데 「`%` 스타일을 쓰면 지연된다」는 반만 맞다**

```python
def expensive():
    print("  >>> 비싼 계산이 돌았다")
    return "결과"

log.setLevel(logging.WARNING)
print("[1] f-string:")
log.debug(f"값은 {expensive()}")
print("[2] % 스타일:")
log.debug("값은 %s", expensive())
print("[3] 진짜 지연 — 값을 만드는 것 자체를 미룬다:")
if log.isEnabledFor(logging.DEBUG):
    log.debug("값은 %s", expensive())
```

```text
[1] f-string:
  >>> 비싼 계산이 돌았다
[2] % 스타일:
  >>> 비싼 계산이 돌았다
[3] 진짜 지연 — 값을 만드는 것 자체를 미룬다:
```

★ **[1] 과 [2] 가 똑같이 돈다.** `%` 스타일이 지연시키는 것은 **포맷 문자열 치환**이지
**인자를 만드는 식**이 아니다 — 인자는 함수 호출 규칙대로 **먼저 평가된다**([01번](../01-object-and-name-binding/2-summary.md)).

| 무엇이 지연되나 | f-string | `%` 스타일 인자 | `isEnabledFor` 가드 |
|---|---|---|---|
| 인자를 만드는 식(`expensive()`) | ✗ | **✗** | ✓ |
| 포맷 치환(`__str__` 호출) | ✗ | ✓ | ✓ |

**★ 값을 만드는 것까지 미루려면 객체로 감싼다**

```python
class Lazy:
    def __init__(self, fn): self.fn = fn
    def __str__(self): return str(self.fn())

log.setLevel(logging.WARNING)
print("[4] Lazy 로 감싸면:")
log.debug("값은 %s", Lazy(expensive))
print("[5] 레벨을 올리면:")
log.setLevel(logging.DEBUG)
log.debug("값은 %s", Lazy(expensive))
```

```text
[4] Lazy 로 감싸면:
[5] 레벨을 올리면:
  >>> 비싼 계산이 돌았다
  [찍힘] 값은 결과
```

**★ f-string 이 못 하는 또 하나 — 템플릿을 변수에 담을 수 없다. 그리고 그것이 안전장치다**

```python
SECRET = "비밀번호-1234"
class User:
    def __init__(self, name): self.name = name

def render(template, user):
    return template.format(user=user)      # 사용자가 template 를 준다면?

u = User("준")
print("정상:", render("안녕 {user.name}", u))
print("공격:", render("{user.__init__.__globals__[SECRET]}", u))
```

```text
정상: 안녕 준
공격: 비밀번호-1234
```

★ **`str.format` 의 치환 필드는 속성 접근과 인덱싱을 허용한다.** 사용자가 템플릿을 주면
`__globals__` 를 타고 **모듈 전역까지 읽힌다**(format string attack).\
★ **f-string 은 리터럴에만 붙으므로 이 공격이 원리적으로 불가능하다** — 사용자 입력이 식이 될 수 없다.

**대안**

```python
import string
print("string.Template :", string.Template("안녕 $name").substitute(name="준"))
print("safe_substitute :", string.Template("$a $b").safe_substitute(a="1"))
```

```text
string.Template : 안녕 준
safe_substitute : 1 $b
```

`string.Template` 은 **`$name` 치환만** 하고 속성 접근을 못 한다 — 사용자 템플릿에는 이쪽을 쓴다.

**비용** — f-string 은 짧고 빠르고 **사용자 입력이 식이 될 수 없다.**\
대신 **지연이 안 되고 템플릿이 될 수 없다.** 로깅과 국제화(i18n)가 정확히 그 두 자리다.

## 문법 — 형태와 규칙

```python
f"..."  F"..."  f'''...'''  rf"..."  fr"..."     # b 와는 못 섞는다 (bf"..." 는 SyntaxError)

# 치환 필드 문법 (언어 레퍼런스)
#   "{" f_expression ["="] ["!" conversion] [":" format_spec] "}"
f"{x}"            # __format__(x, "")
f"{x!r}"          # repr(x)
f"{x!s}"          # str(x)
f"{x!a}"          # ascii(x)
f"{x=}"           # "x=" + repr(x)      (3.8+)
f"{x=:.2f}"       # "x=" + format(x, ".2f")
f"{{"  f"}}"      # 중괄호 자체

# 포맷 스펙
#   [[fill]align][sign]["z"]["#"]["0"][width][grouping]["." precision][type]
f"{v:>10}"  f"{v:*^10}"  f"{v:=10}"  f"{v:010}"
f"{v:+,.2f}"  f"{v:#x}"  f"{v:.1%}"  f"{v:e}"
f"{v:{w}.{p}f}"   # 중첩 — 스펙을 실행 시에 만든다

# 나머지 둘
"{} {k}".format(a, k=1)        # 템플릿을 변수에 담을 수 있다
"%s %(k)s" % (a,)              # 오른쪽이 튜플이면 풀린다
```

규칙은 여덟이다.

1. **f-string 은 리터럴이 아니라 식**이고 **그 자리에서 왼쪽부터** 평가된다.
2. **`{x}` 는 `__format__` 을 부른다.** `str(x)` 가 아니다 — `!s` 를 붙여야 `str` 이다.
3. **변환(`!r`)이 스펙(`:>10`)보다 먼저** 적용된다. 문법 순서가 그렇게 고정돼 있다.
4. **`=` 는 기본이 `!r`** 이고 **공백까지 그대로** 옮긴다. 스펙을 붙이면 스펙이 이긴다.
5. **포맷 스펙의 기본 정렬은 타입에 달렸다** — 숫자는 오른쪽, 그 밖은 왼쪽.
6. **`__format__` 이 없는 타입에 스펙을 주면 `TypeError`** 다(`None`·`list` 포함).
7. **스펙 안에 중괄호를 넣어 폭·정밀도를 실행 시에** 정할 수 있다. 한 겹까지다.
8. **f-string 은 지연되지 않고 템플릿이 될 수 없다.** 그 대신 사용자 입력이 식이 될 수 없다.

## 어디서 틀리나

### (1) 로그를 f-string 으로 찍는다

```python
log.debug(f"무거운 값: {expensive()}")     # 레벨이 막아도 expensive() 는 돈다
```

`log.debug("무거운 값: %s", obj)` 로 바꾸면 **포맷**은 지연된다.\
**값 자체를 안 만들려면** `isEnabledFor` 가드나 지연 객체가 필요하다.

### (2) `{x}` 가 `str(x)` 라고 믿는다

```python
class P:
    def __str__(self): return "str 판"
    def __format__(self, spec): return "format 판"
print(f"{P()}")        # format 판
print(f"{P()!s}")      # str 판
```

`__format__` 을 정의한 라이브러리 객체(`Decimal`·`datetime`·numpy 스칼라)에서 갈린다.

### (3) `None` 에 포맷 스펙을 준다

```python
v = None
print(f"[{v:>10}]")
```

```text
TypeError: unsupported format string passed to NoneType.__format__
```

`f"[{v!s:>10}]"` 처럼 **먼저 문자열로** 만든 뒤 정렬한다.

### (4) `"%s" % x` 에서 `x` 가 튜플이 된다

```python
x = (1, 2)
print("%s" % x)
```

```text
TypeError: not all arguments converted during string formatting
```

**타입에 따라 동작이 갈린다.** `"%s" % (x,)` 로 언제나 감싼다.

### (5) 사용자에게 받은 문자열을 `str.format` 의 템플릿으로 쓴다

```python
user_template = "{u.__init__.__globals__[SECRET]}"
print(user_template.format(u=obj))     # 모듈 전역이 새어 나온다
```

`string.Template` 을 쓰거나 허용 키를 명시적으로 검사한다.

### (6) 한글 표를 `width` 로 맞춘다

```python
for name in ("사과", "바나나킥"):
    print(f"|{name:<8}|")
```

```text
|사과      |
|바나나킥    |
```

`len` 은 2·4 인데 터미널은 4·8 칸을 쓴다. **오른쪽 세로줄이 안 맞는다.**

### (7) 3.12 문법을 3.11 에 배포한다

```python
d = {"k": 1}
print(f"{d["k"]}")      # 3.12 에서는 되고 3.11 에서는 SyntaxError
```

같은 따옴표 중첩·식 안의 백슬래시는 **PEP 701(3.12) 이후**다.

### (8) `=` 의 결과에 따옴표가 붙는 것을 잊는다

```python
name = "값"
print(f"{name=}")       # name='값'
print(f"{name=!s}")     # name=값
```

`=` 의 기본이 `!r` 이다. 로그를 파싱하는 쪽이 있으면 따옴표가 문제가 된다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 세 층이 가장 뚜렷하다** — 의미는 명세, 바이트코드는 구현, `%` 접기는 이 판의 관찰이다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어·라이브러리 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 + `dis`·`tokenize` |
| **이 판의 관찰** | 3.12.3 에서 그랬을 뿐 | 「관찰」로 명기 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| f-string 은 **실행 시에 평가되는 식**이다 | 언어 레퍼런스 2.4.3 — *"really expressions evaluated at run time"* |
| 각 식은 **왼쪽부터 순서대로** 평가된다 | 〃 — *"in order from left to right"* |
| 치환 필드 문법은 `{식 [=] [!변환] [:스펙]}` **이 순서** | 〃 replacement_field 문법 |
| 변환은 `s`·`r`·`a` 셋뿐이다 | 〃 conversion 문법 |
| `=` 는 **식 텍스트 + `=` + 값**을 내고 **공백을 보존**한다 | 〃 (3.8+) |
| 포맷 스펙 EBNF 와 각 조각의 뜻 | Format Specification Mini-Language |
| `'<'` 는 대부분 객체의 기본, `'>'` 는 **숫자의 기본** | 〃 align 표 |
| `'0'` 을 width 앞에 두면 **`'='` 정렬 + `'0'` 채우기**와 같다 | 〃 |
| PEP 701 의 세 완화(같은 따옴표 중첩·백슬래시·주석)가 **3.12 부터** | 언어 레퍼런스의 *"Changed in version 3.12"* 셋 |
| `%` 의 오른쪽이 **튜플이면 풀리고** 그 밖이면 값 하나다 | printf-style String Formatting |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| f-string 이 `FORMAT_VALUE` + `BUILD_STRING` 으로 컴파일된다 | `dis` |
| 고정 조각이 **`LOAD_CONST`(상수)** 이고 스펙 문자열도 상수다 | `dis` |
| f-string 이 **여러 토큰**(`FSTRING_START`/`MIDDLE`/`END`)으로 쪼개진다 | `tokenize` — 보통 문자열은 `STRING` 하나 |
| `str.format` 은 **메서드 호출**로 남는다(`LOAD_ATTR` + `CALL`) | `dis` |
| `f"{a}"` 는 `FORMAT_VALUE 0`, `f"{a!s}"` 는 `FORMAT_VALUE(str)` | `dis` — 인자에 변환 종류가 찍힌다 |

### 이 판(3.12.3)의 관찰 — 버전이 오르면 다시 찍어야 한다

| 관찰 | 어디가 흔들리나 |
|---|---|
| ★ **`"%s-%s" % (a, b)` 가 `BINARY_OP %` 없이 `FORMAT_VALUE` 로 접힌다** | **컴파일러 최적화다.** 문서 어디에도 없다 |
| 접히는 조건이 「리터럴 + 리터럴 튜플 + `%s`/`%r`/`%a`」인 것 | 〃 — 조건이 판마다 넓어지거나 좁아질 수 있다 |
| 명령 이름 `FORMAT_VALUE`·`BUILD_STRING`·`RETURN_CONST` | **3.13 에서 `FORMAT_VALUE` 가 `CONVERT_VALUE`/`FORMAT_SIMPLE`/`FORMAT_WITH_SPEC` 로 쪼개졌다** |
| `SyntaxError` 문구(`f-string: valid expression required before '}'` 등) | PEP 701 로 크게 바뀐 자리라 계속 다듬어진다 |
| 토큰 이름 `FSTRING_START`/`MIDDLE`/`END` | 3.12 에 새로 생긴 이름이다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「f-string 은 문자열 리터럴이다」\
  ○ **실행 시에 평가되는 식**이다. 문서가 *"really expressions evaluated at run time"* 이라고 적는다.
- ✗ 「`f"{x}"` 는 `str(x)` 와 같다」\
  ○ **`format(x, "")`** 이다. `__format__` 을 정의한 타입에서 갈린다.
- ✗ 「`%` 포맷은 연산자 호출이라 f-string 보다 느리다」\
  ○ **이 판에서는 `%s` 만 쓰고 오른쪽이 리터럴 튜플이면 같은 바이트코드로 접힌다.**\
  단 그것은 **최적화이지 보장이 아니다.**
- ✗ 「`"%s" % (a,)` 는 `f"{a}"` 와 같다」\
  ○ **`f"{a!s}"` 와 같다.** `%s` 는 `str()`, f-string 의 기본은 `__format__`.
- ✗ 「로깅에 `%` 스타일을 쓰면 지연된다」\
  ○ **포맷 치환만** 지연된다. **인자를 만드는 식은 그대로 돈다.**
- ✗ 「PEP 701 이 f-string 을 빠르게 했다」\
  ○ **토크나이저·문법을 바꾼 것**이다. 바이트코드는 그대로다.
- ✗ 「`f"{v:>10}"` 은 아무 값에나 된다」\
  ○ **`__format__` 이 스펙을 안 받으면 `TypeError`** 다(`None`·`list`).

**판정 기준 한 줄**: 어떤 코드가 「**이 문자열을 나중에 쓰겠다**」고 하고 있으면 f-string 은 틀린 도구다. 이미 만들어진 뒤이기 때문이다.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| f-string | **기본값.** 그 자리에서 문자열을 만들 때 |
| `f"{x=}"` | 디버그 출력. 이름과 값을 같이 |
| `f"{x!r}"` | 로그. `''` 와 `None` 과 `'None'` 을 구별해야 할 때 |
| `str.format` | **템플릿을 변수에 담아야** 할 때(설정 파일·i18n) |
| `"%s"` + 로거 인자 | 로깅. 포맷을 로거에게 맡길 때 |
| `string.Template` | **사용자가 준 템플릿**. 속성 접근이 막혀 있다 |
| `__format__` 정의 | 도메인 타입(금액·좌표)이 자기 포맷 스펙을 갖게 할 때 |
| 중첩 중괄호 | 폭·정밀도가 데이터에 달렸을 때 |

**안 쓰는 자리**는 셋이다.\
**로그 호출 안에 f-string 을 쓰지 마라** — 레벨이 막아도 먼저 만들어진다.\
**사용자 입력을 `str.format` 의 템플릿으로 쓰지 마라** — `__globals__` 까지 읽힌다.\
**한글이 섞인 표를 `width` 로 맞추지 마라** — `len` 과 터미널 칸이 다르다.

## 핵심 문장

- **f-string 은 리터럴이 아니라 식이다.** 그 줄을 지날 때 왼쪽부터 평가돼 **이미 만들어진 문자열**이 된다.
- **`dis` 로 보면 `FORMAT_VALUE` + `BUILD_STRING` 두 명령**뿐이다. 호출이 없어서 빠르다.
- **PEP 701 이 바꾼 것은 토크나이저다** — f-string 이 토큰 하나에서 여러 토큰으로 쪼개졌고, 그 결과 같은 따옴표·백슬래시·주석이 풀렸다. 바이트코드는 그대로다.
- ★ **3.12 는 `"%s" % (a, b)` 를 f-string 과 같은 바이트코드로 접는다.** 「`%` 가 느리다」가 이 판에서는 틀린다 — 단 그것은 **관찰이지 보장이 아니다.**
- **`{x}` 는 `__format__` 을 부르고 `%s` 는 `str()` 을 부른다.** 그 차이가 `dis` 인자에 그대로 찍힌다.
- **변환(`!r`)이 스펙(`:>10`)보다 먼저**다. 문법 순서가 고정돼 있다.
- **정렬의 기본값이 타입에 달렸다** — 숫자는 오른쪽, 그 밖은 왼쪽. `bool` 은 숫자다.
- **f-string 은 지연되지 않는다.** 로깅에서 그것이 비용이고, 사용자 템플릿에서는 그것이 안전장치다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **08번**
- 선행: [06-strings-bytes-unicode](../06-strings-bytes-unicode/2-summary.md) — 만들어지는 것이 `str` 이고, `{:c}` 가 `chr` 과 같은 일을 하며, 한글 폭 문제가 거기서 온다. **f-string 에 `b` 접두사는 못 붙는다.**
- 선행: [01-object-and-name-binding](../01-object-and-name-binding/2-summary.md) — 「평가 시점」과 기본 인자의 한 번 평가.
- 이어지는 곳: [07-string-methods](../07-string-methods/2-summary.md) — `str.center` 와 포맷 스펙 `^` 가 **여분 칸을 반대쪽에 둔다**는 관찰이 거기 있다.
- 이어지는 곳: [04-numeric-types-and-division](../04-numeric-types-and-division/2-summary.md) — `bool` 이 `int` 의 하위 클래스라 `f"{True:10}"` 이 `'         1'` 인 것.
- 이어지는 곳: [20-mutable-default-args](../20-mutable-default-args/2-summary.md) — 기본 인자의 f-string 이 `def` 때 한 번 평가되는 것.
- 이어지는 곳: [목록의 **30번 주제**](../30-repr-eq-hash-contracts/) 「`__repr__`·`__eq__`·`__hash__` 계약」 — `__repr__`/`__str__`/`__format__` 의 기본값 사슬.
- 이어지는 곳: [목록의 **50번 주제**](../50-decimal-float-precision-and-round/) 「`decimal`·float 정밀도·`round`」 — `f"{v:.2f}"` 가 반올림에서 무엇을 하나.
- 이어지는 곳: [목록의 **49번 주제**](../49-datetime-and-zoneinfo/) 「`datetime` 과 `zoneinfo`」 — 포맷 스펙 자리를 `strftime` 형식으로 쓰는 대표 사례.
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/) — 문자열 포맷을 「이렇게 쓴다」까지 다룬다.\
  **경계**: 그쪽은 사용 예시까지, 여기는 「**언제 평가되고 무엇으로 컴파일되나**」부터다.
- 연혁은 여기가 아니다: [`history/python/`](../../../../../../history/python/)
- 공식 문서: [f-strings](https://docs.python.org/3.12/reference/lexical_analysis.html#f-strings) · [Format Spec Mini-Language](https://docs.python.org/3.12/library/string.html#format-specification-mini-language) · [printf-style](https://docs.python.org/3.12/library/stdtypes.html#printf-style-string-formatting) · [PEP 701](https://peps.python.org/pep-0701/)

## 용어 풀이

- **f-string (formatted string literal)**: `f` 접두사가 붙은 문자열 리터럴.\
  **리터럴이 아니라 식**이고 그 자리에서 평가된다(3.6+).
- **치환 필드(replacement field)**: `{...}` 한 덩어리.\
  문법은 `{식 [=] [!변환] [:포맷스펙]}` 이고 **네 부분의 순서가 고정**이다.
- **변환(conversion)**: `!s`·`!r`·`!a` 세 가지. 각각 `str()`·`repr()`·`ascii()`.\
  **스펙보다 먼저** 적용된다.
- **포맷 스펙(format specification)**: 콜론 뒤의 작은 언어.\
  `[[fill]align][sign]["z"]["#"]["0"][width][grouping]["." precision][type]`.
- **`__format__`**: `format(x, spec)` 과 `f"{x:spec}"` 이 부르는 메서드.\
  정의 안 하면 `object.__format__` 이 쓰이고 **빈 스펙일 때만** `str(self)` 를 돌려준다.
- **`=` 디버그 표기**: `f"{x=}"` 가 `x=42` 를 만든다(3.8+).\
  **기본 변환이 `!r`** 이고 **공백까지 보존**한다.
- **PEP 701**: 3.12 에서 f-string 을 **정식 문법으로** 끌어올린 제안.\
  같은 따옴표 중첩·백슬래시·주석·무제한 중첩이 풀렸다. **토크나이저가 바뀐 것**이지 바이트코드가 아니다.
- **`FORMAT_VALUE`**: 스택 맨 위의 값을 변환·포맷하는 3.12 의 바이트코드 명령.\
  인자에 **어떤 변환을 쓸지 + 스펙이 있는지**가 담긴다. 3.13 에서 세 명령으로 쪼개졌다.
- **`BUILD_STRING`**: 스택의 여러 문자열 조각을 하나로 잇는 명령.
- **상수 접기(constant folding)** / **컴파일 때 접기**: 컴파일 시점에 계산할 수 있는 것을 미리 해 두는 최적화.\
  3.12 는 `%` 포맷도 조건이 맞으면 접는다 — **관찰이지 보장이 아니다.**
- **format string attack**: 사용자가 준 문자열을 `str.format` 의 **템플릿**으로 쓸 때, 치환 필드의 속성 접근으로 `__globals__` 같은 내부를 읽어 내는 공격.\
  f-string 은 리터럴에만 붙으므로 원리적으로 불가능하다.
- **지연 평가(lazy evaluation)**: 값을 실제로 필요할 때까지 안 만드는 것.\
  f-string 은 못 하고, 로깅의 `%` 스타일은 **포맷만** 미룬다.

## 더 들어가면

- **`str.format_map`** 은 `format(**d)` 와 달리 dict 를 **복사하지 않는다.** `defaultdict` 를 넘겨 빠진 키를 채우는 관용구가 여기서 나온다.
- **`{!r}` 대신 `{!a}` 를 쓰면** 비-ASCII 가 전부 이스케이프로 나온다 — 터미널 인코딩이 불확실한 환경의 로그에 쓸 만하다([06번](../06-strings-bytes-unicode/2-summary.md)).
- **`reprlib.repr`** 은 긴 컨테이너를 잘라서 보여 준다. 로그에 큰 리스트를 `!r` 로 찍는 사고를 막는다.
- **3.14 의 t-string(PEP 750)** 은 「구워 내지 않은 f-string」을 만드는 문법이다 — 이 주제의 8번 절이 그 제안의 동기다. 이 머신에는 3.14 가 없어 **실행 검증하지 않았다.**
- **`logging` 의 `style="{"`/`style="$"`** 로 포맷 스타일을 바꿀 수 있지만, 그것은 **로거의 포맷 문자열**에만 적용되고 `log.debug()` 의 인자 처리는 여전히 `%` 스타일이다.
