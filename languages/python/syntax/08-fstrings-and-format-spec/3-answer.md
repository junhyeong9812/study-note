# python/syntax/08-fstrings-and-format-spec — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 11개 = 답 11개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 단 **바이트코드 명령 이름과 `%` 포맷이 접히는 것은 구현 세부사항**이라 다른 구현·다른 버전에서는 달라진다(2·11번 답).

## 정답

### 1. f-string 은 그 줄에서 이미 만들어진다

**출력**

```text
x 는 1
x 는 2
기본 2
```

**왜 그런가**

문서의 정의 한 줄이 답이다 —\
*"While other string literals always have a constant value, formatted strings are really **expressions evaluated at run time**."*

```text
 x = 1
 s = f"x 는 {x}"   <- ★ 이 줄에서 x 를 읽고 문자열을 만들어 버린다.  s = "x 는 1"
 t = "x 는 {x}"    <- 이것은 그냥 문자열. 아직 아무것도 안 읽었다
 x = 2
 print(s)          -> "x 는 1"   (이미 만들어진 것)
 print(t.format(x=x)) -> "x 는 2" (쓰는 순간 읽는다)
```

**셋째 줄이 `기본 2` 인 이유**

```text
 x = 2            <- 여기까지 왔을 때 x 는 2
 def f(v=f"기본 {x}"):   <- ★ def 문을 "만날 때" 기본값이 한 번 평가된다 -> "기본 2"
     ...
 x = 99           <- 이 뒤에 바꿔도 소용없다
 f()              -> "기본 2"
```

**`99` 가 아니다.** 기본 인자는 **함수가 정의될 때 한 번** 평가된다 — [20번 주제](../20-mutable-default-args/2-summary.md)의 그 규칙이고,
f-string 이 「식」이라는 성질과 맞물려 여기서 겹쳐 나타난다.

**세 도구의 평가 시점**

| | 언제 평가되나 | 템플릿을 변수에 담을 수 있나 |
|---|---|---|
| f-string | **그 줄을 지날 때 한 번** | ✗ |
| `str.format` | `.format()` 을 부를 때 | ✓ |
| `string.Template` | `.substitute()` 를 부를 때 | ✓ |

### 2. `dis` — `%` 포맷이 f-string 과 같은 명령으로 접힌다

**출력**

```text
r = f"{a}-{b}"             ['FORMAT_VALUE', 'FORMAT_VALUE', 'BUILD_STRING']
r = "%s-%s" % (a, b)       ['FORMAT_VALUE', 'FORMAT_VALUE', 'BUILD_STRING']
r = "{}-{}".format(a, b)   ['LOAD_ATTR', 'CALL']
```

**왜 그런가 — 둘이 같은 이유**

★ **컴파일러가 `%` 포맷을 통째로 접었다.** `BINARY_OP %` 가 **아예 없다.**

```text
 소스                        컴파일된 것
 "%s-%s" % (a, b)     ->     LOAD_NAME a
                             FORMAT_VALUE (str)
                             LOAD_CONST '-'
                             LOAD_NAME b
                             FORMAT_VALUE (str)
                             BUILD_STRING 3

  ★ 나머지 연산자(%)도, 튜플도 만들지 않는다.
    f-string 과 명령 구성이 같다.
```

`str.format` 만 **메서드 호출**로 남는다(`LOAD_ATTR` + `CALL`) — 문자열 객체의 메서드라 컴파일러가 접을 수 없다.

**★ 그런데 아무 `%` 나 접히는 것이 아니다**

```python
import dis
cases = {
  '"%s" % (a,)': 'r = "%s" % (a,)',   '"%r" % (a,)': 'r = "%r" % (a,)',
  '"%a" % (a,)': 'r = "%a" % (a,)',   '"%d" % (a,)': 'r = "%d" % (a,)',
  '"%s" % a': 'r = "%s" % a',         '"%s" % t': 'r = "%s" % t',
  '"%(k)s" % d': 'r = "%(k)s" % d',
}
for label, src in cases.items():
    ops = [i.opname for i in dis.get_instructions(compile(src, "<x>", "exec"))
           if i.opname in ("FORMAT_VALUE", "BINARY_OP", "BUILD_TUPLE")]
    print(f"{label:16} {ops}")
```

```text
"%s" % (a,)      ['FORMAT_VALUE']
"%r" % (a,)      ['FORMAT_VALUE']
"%a" % (a,)      ['FORMAT_VALUE']
"%d" % (a,)      ['BUILD_TUPLE', 'BINARY_OP']
"%s" % a         ['BINARY_OP']
"%s" % t         ['BINARY_OP']
"%(k)s" % d      ['BINARY_OP']
```

```text
 접히는 조건 (3.12 관찰)
   왼쪽이 리터럴  +  오른쪽이 "리터럴 튜플"  +  변환이 %s/%r/%a 뿐
   -> FORMAT_VALUE

   %d·%x  ·  오른쪽이 변수  ·  %(name)s
   -> BINARY_OP % 로 남는다
```

**★ 「같다」고 하면 한 칸이 틀린다 — 인자가 다르다**

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

★ **`"%s" % (a,)` 는 `f"{a!s}"` 와 같고 `f"{a}"` 와는 다르다.**\
`%s` 는 **언제나 `str()`**, f-string 의 기본은 **`__format__`**. 3번 답이 그 차이를 값으로 보여 준다.

★★ **이것은 전부 「이 판의 관찰」이다.** 문서 어디에도 `%` 포맷이 접힌다는 말이 없다.\
「`%` 는 연산자 호출이라 느리다」라는 흔한 설명이 **3.12 에서는 틀리는데**, 그렇다고 「빠르다」를 보장으로 적어도 틀린다.

### 3. `{p}` 는 `__format__` 을 부른다

**출력**

```text
format 판(spec='')
str 판
repr 판
format 판(spec='>8')
      repr 판
str 판
```

**왜 그런가**

```text
 f"{p}"        ->  format(p, "")        ->  P.__format__(p, "")
 f"{p!s}"      ->  str(p)               ->  P.__str__(p)        ★ __format__ 을 건너뛴다
 f"{p!r}"      ->  repr(p)              ->  P.__repr__(p)
 f"{p:>8}"     ->  format(p, ">8")      ->  P.__format__(p, ">8")
 f"{p!r:>12}"  ->  repr(p) 먼저, 그 문자열에 ">12" 를 건다
 "%s" % (p,)   ->  str(p)               ->  P.__str__(p)
```

★ **`{p}` 가 `str(p)` 라는 것이 이 주제 최대의 오해다.** `__format__` 이 먼저다.

**변환이 스펙보다 먼저다**

```text
 f"{p!r:>12}"
      ^^  ^^^^
      |    +--- 2단계: 그 문자열에 스펙을 건다 -> str.__format__ 이 받는다
      +-------- 1단계: repr(p) 로 문자열을 만든다

  결과 '      repr 판'  (12칸 오른쪽 정렬)
  ★ P.__format__ 은 한 번도 안 불렸다.
```

문법이 그 순서를 고정한다 — `"{" f_expression ["="] ["!" conversion] [":" format_spec] "}"`.

**마지막 줄은 첫 줄이 아니라 둘째 줄과 같다**

| 쓴 것 | 부르는 것 | 출력 |
|---|---|---|
| `f"{p}"` | `__format__` | `format 판(spec='')` |
| `f"{p!s}"` | `__str__` | `str 판` |
| **`"%s" % (p,)`** | **`__str__`** | **`str 판`** |

2번 답의 `dis` 가 이미 그렇게 말하고 있었다 — `"%s" % (a,)` 는 `FORMAT_VALUE(str)`, `f"{a}"` 는 `FORMAT_VALUE()`.\
★ **바이트코드에 찍힌 인자와 실행 결과가 같은 말을 한다.**

### 4. 포맷 스펙 조각들

**출력**

```text
'-       42' '-000000042'
'1,234,567' '-1,234.57'
'-1.23e+03' 'abc'
'0x000000ff' '가'
'        42' 'ab        ' '         1'
```

**왜 그런가**

```text
  f"{값:*^+#010_.2f}"
       |||||||||||
       ||||||||||+- type      f  : 고정 소수점
       |||||||||+-- precision .2
       ||||||||+--- grouping  _
       |||||||+---- width     10
       ||||||+----- 0            : 부호 인식 0 채우기
       |||||+------ #            : 진법 접두사
       ||||+------- z            : -0.0 -> 0.0  (3.11+)
       |||+-------- sign      +
       ||+--------- align     ^
       |+---------- fill      *
       +----------- :            : 여기부터 스펙
```

| 스펙 | 결과 | 왜 |
|---|---|---|
| `{-42:=10}` | `'-       42'` | **`=` 는 부호 뒤·숫자 앞에** 채운다 — *"placed after the sign but before the digits"* |
| `{-42:010}` | `'-000000042'` | `0`+width 는 **`=` 정렬 + `0` 채우기**와 같다 |
| `{1234567:,}` | `'1,234,567'` | 천 단위 구분 |
| `{-1234.5678:,.2f}` | `'-1,234.57'` | grouping 과 precision 을 같이 |
| `{-1234.5678:.3}` | `'-1.23e+03'` | **타입이 없으면 `g`** — 유효숫자 3개 |
| `{'abcdef':.3s}` | `'abc'` | **문자열에서 precision 은 최대 길이**(자르기) |
| `{255:#010x}` | `'0x000000ff'` | `0x` 접두사까지 10칸 |
| `{44032:c}` | `'가'` | 정수를 그 코드 포인트의 글자로 — `chr` 과 같다 |

**마지막 줄 — 정렬의 기본값이 타입에 달렸다**

```text
 문서:  '<' 는 "the default for most objects"
        '>' 는 "the default for numbers"

  f"{42:10}"    -> '        42'   숫자 -> 오른쪽
  f"{'ab':10}"  -> 'ab        '   문자열 -> 왼쪽
  f"{True:10}"  -> '         1'   ★ bool 은 숫자다. '1' 로 찍히고 오른쪽 정렬
```

★ **`True` 가 `'True'` 가 아니라 `'1'`** 이다. `bool` 이 `int` 의 하위 클래스라 `int.__format__` 을 쓴다([04번](../04-numeric-types-and-division/2-summary.md)).\
빈 스펙 `f"{True}"` 는 `'True'` 다 — **스펙을 주는 순간 숫자가 된다.**

```python
print(f"{True}", "|", f"{True:10}", "|", f"{True:d}", "|", f"{True:05.1f}")
```

```text
True |          1 | 1 | 001.0
```

### 5. `__format__` 이 없으면 스펙을 못 받는다

**출력**

```text
int      |        42|
str      |ab        |
float    |       3.5|
NoneType TypeError: unsupported format string passed to NoneType.__format__
list     TypeError: unsupported format string passed to list.__format__
내 str
```

**왜 그런가**

```text
 f"{x:스펙}"  ->  format(x, "스펙")  ->  type(x).__format__(x, "스펙")
                                              |
                          정의 안 했으면 object.__format__ 이 쓰인다
                                              |
                       +----------------------+----------------------+
                       |                                             |
                  스펙이 "" 이다                             스펙이 비어 있지 않다
                       |                                             |
                  str(self) 를 돌려준다                     ★ TypeError 를 던진다
```

**마지막 줄은 되는데 `f"{o:>10}"` 은 안 되는 이유**

```python
class OnlyStr:
    def __str__(self): return "내 str"
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

`object.__format__` 은 **빈 스펙일 때만** `str(self)` 를 돌려주고, 스펙이 있으면 「**나는 그것을 해석할 줄 모른다**」고 던진다.\
`None`·`list` 가 터진 것도 같은 이유다 — 둘 다 자기 `__format__` 이 없다.

**고치는 법 둘**

```python
v = None
print(f"[{v!s:>10}]")          # 먼저 str 로 만든 뒤 정렬한다

class Money:
    def __init__(self, won): self.won = won
    def __format__(self, spec): return format(self.won, spec or ",") + "원"
print(f"{Money(1234567)}", "|", f"{Money(1234567):>15,}")
```

```text
[      None]
1,234,567원 |       1,234,567원
```

★ **도메인 타입은 `__format__` 을 정의해 스펙을 자기 뜻으로** 쓸 수 있다.\
`datetime` 이 그 자리를 `strftime` 형식으로 쓰는 것이 표준 라이브러리의 대표 사례다.

```python
import datetime
print(f"{datetime.date(2026, 9, 23):%Y년 %m월 %d일}")
```

```text
2026년 09월 23일
```

**세 메서드의 기본값 사슬**

```text
  __format__ 없음 -> object.__format__ -> str(self)   ★ 빈 스펙일 때만
  __str__    없음 -> object.__str__    -> repr(self)
  __repr__   없음 -> object.__repr__   -> '<...object at 0x...>'

  ★ __repr__ 하나만 정의해도 세 자리가 다 채워진다.
    반대로 __str__ 만 정의하면 로그의 repr 자리가 비어 있다.
```

### 6. `=` 는 식의 텍스트를 그대로 옮긴다

**출력**

```text
x=42
x = 42
x=00042
name='값'
 x  +  1 = 43
```

**왜 그런가**

문서 —\
*"When the equal sign `'='` is provided, the output will have the expression text, the `'='` and the evaluated value. **Spaces after the opening brace `'{'`, within the expression and after the `'='` are all retained** in the output."*(3.8+)

```text
 f"{x=}"          ->  "x" + "=" + repr(42)   -> "x=42"
 f"{x = }"        ->  공백까지 그대로          -> "x = 42"
 f"{x=:05d}"      ->  ★ 스펙이 있으면 repr 대신 스펙 -> "x=00042"
 f"{name=}"       ->  ★ 기본이 !r 이라 따옴표가 붙는다 -> "name='값'"
 f"{ x  +  1 = }" ->  식 텍스트를 한 글자도 안 다듬는다 -> " x  +  1 = 43"
```

| 쓰는 법 | 변환 | 결과 |
|---|---|---|
| `f"{name=}"` | **`!r`**(기본) | `name='값'` |
| `f"{name=!s}"` | `!s` | `name=값` |
| `f"{x=:05d}"` | 스펙(변환 없음) | `x=00042` |

★ **`=` 의 기본이 `!r` 인 것**이 이 표기의 값이다 — `''` 와 `None` 과 `'None'` 이 구별된다.

```python
for v in ("", None, "None", 0, "0"):
    print(f"{v=}")
```

```text
v=''
v=None
v='None'
v=0
v='0'
```

**왜 쓰나** — 이름을 두 번 안 써도 되므로 **오타로 어긋날 수가 없다.**

```text
 print("x =", x)        <- 이름을 두 곳에 적는다. 하나만 고치면 거짓말이 된다
 print(f"{x=}")         <- 한 곳. 식을 고치면 라벨도 같이 바뀐다
```

### 7. 3.12 가 푼 것들 (PEP 701)

**출력**

```text
값
['a', 'b']
2
f"{}" -> f-string: valid expression required before '}'
f"{x!z}" -> f-string: invalid conversion character 'z': expected 's', 'r', or 'a'
```

**왜 그런가**

| 3.11 까지 | 3.12(PEP 701) |
|---|---|
| 바깥과 **같은 따옴표**를 안에서 못 쓴다 | 쓸 수 있다 |
| 식 안에 **백슬래시** 금지 | 허용 |
| 식 안에 **주석**·줄바꿈 금지 | 허용 |
| 중첩 깊이 제한 | 제한 없음 |

문서가 셋 다 *"Changed in version 3.12"* 로 적는다.

**3.11 에서는 어디서 멈추나 — 첫 줄에서, 그것도 실행이 아니라 컴파일에서다**

```text
 3.11 로 이 파일을 읽으면

   print(f"{d["key"]}")
              ^
   SyntaxError: f-string: unmatched '['   (또는 그 비슷한 것)

  ★ 파일 전체가 컴파일되지 않으므로 "첫 줄만 실패" 가 아니라
    아무 줄도 실행되지 않는다. import 하는 쪽까지 같이 죽는다.
```

★ **이것이 3.12 문법을 쓸 때의 진짜 비용이다.** 런타임 에러가 아니라 **컴파일 에러**라서
`try`/`except` 로 감쌀 수도, 기능 감지로 우회할 수도 없다.

**왜 이렇게 바뀌었나 — 토크나이저가 바뀐 것이다**

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
3.11 까지는 f-string 도 `STRING` 토큰 하나였고 **파서가 그 안을 따로 다시 파싱**했다 — 그 별도 파서가 따옴표와 백슬래시를 못 다뤘던 것이다.
3.12 가 그것을 **정식 문법으로** 끌어올렸다.

★ **바이트코드는 안 바뀌었다.** PEP 701 은 **앞단(토크나이저·문법)만** 고쳤다.

**오류 메시지도 그 덕에 구체적이다**

```text
 3.11:  SyntaxError: f-string: expecting '}'          (어디가 문제인지 모른다)
 3.12:  SyntaxError: f-string: valid expression required before '}'
        SyntaxError: f-string: invalid conversion character 'z': expected 's', 'r', or 'a'
```

(왼쪽은 이 머신에 3.11 이 없어 **실행 검증하지 않았다** — 오른쪽만 실측이다.)

### 8. `%` 포맷의 오른쪽 (왜)

**핵심 한 줄**: **오른쪽이 튜플이면 「인자 목록」으로 풀리고, 그 밖이면 「값 하나」다.**

```python
t = (1, 2)
print("'%s' % 'abc' =", "%s" % "abc")
try:
    print("'%s' % t    =", "%s" % t)
except TypeError as e:
    print("'%s' % t    ->", type(e).__name__, e)
print("'%s' % (t,)  =", "%s" % (t,))
print("'%s' % [1,2] =", "%s" % [1, 2])
try:
    "%s %s" % ("a",)
except TypeError as e:
    print("모자라면 ->", type(e).__name__, e)
```

```text
'%s' % 'abc' = abc
'%s' % t    -> TypeError not all arguments converted during string formatting
'%s' % (t,)  = (1, 2)
'%s' % [1,2] = [1, 2]
모자라면 -> TypeError not enough arguments for format string
```

```text
 "%s" % X 에서 X 가

   튜플이면   ->  ★ 풀린다. 원소 개수 = 자리 수 여야 한다
   리스트면   ->  안 풀린다. 통째로 값 하나
   dict 면    ->  %(name)s 가 있으면 매핑, 없으면 값 하나
   그 밖이면  ->  통째로 값 하나

  ★ 그래서 "값 하나를 넣는다" 는 코드가 그 값의 타입에 따라 동작이 갈린다.
```

**왜 이런 설계인가**

`%` 포맷은 C 의 `printf` 를 본떴고, **여러 인자를 넘기는 문법이 튜플 하나**다.\
그래서 「자리가 여럿일 때의 인자 목록」과 「자리가 하나이고 그 값이 우연히 튜플일 때」가 **구별되지 않는다.**

**없애는 습관 — 오른쪽을 언제나 튜플로 감싼다**

```python
def log_value(x):
    return "값: %s" % (x,)          # ★ 언제나 (x,)

for v in ((1, 2), [1, 2], "abc", None):
    print(log_value(v))
```

```text
값: (1, 2)
값: [1, 2]
값: abc
값: None
```

★ **`(x,)` 로 감싸면 `x` 의 타입과 무관하게 「값 하나」다.**\
그리고 이 습관은 2번 답의 **컴파일 때 접기**에도 들어맞는다 — 리터럴 튜플이어야 접힌다.

★ 더 나은 답은 **`f"값: {x}"`** 다. 이 함정 자체가 없다.

### 9. 로그에 f-string 을 쓰면 (경계)

**갈라 말하면 — 지연되는 것은 「포맷 치환」뿐이고 「인자를 만드는 식」은 아니다.**

```python
import logging, sys
logging.basicConfig(level=logging.WARNING, stream=sys.stdout, format="  [찍힘] %(message)s")
log = logging.getLogger("t")

class Loud:
    def __str__(self):
        print("  >>> __str__ 이 불렸다 (= 실제 포맷이 일어났다)")
        return "값"

print("[A] f-string:")
log.debug(f"{Loud()}")
print("[B] % 스타일:")
log.debug("%s", Loud())
print("[C] 레벨을 올리면:")
log.setLevel(logging.DEBUG)
log.debug("%s", Loud())
```

```text
[A] f-string:
  >>> __str__ 이 불렸다 (= 실제 포맷이 일어났다)
[B] % 스타일:
[C] 레벨을 올리면:
  >>> __str__ 이 불렸다 (= 실제 포맷이 일어났다)
  [찍힘] 값
```

★ **[B] 에서 아무 출력이 없는 것**이 「포맷이 지연됐다」의 증거다. **「출력 없음」이 여기서 가장 강한 근거**다.

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
print("[3] isEnabledFor 가드:")
if log.isEnabledFor(logging.DEBUG):
    log.debug("값은 %s", expensive())
```

```text
[1] f-string:
  >>> 비싼 계산이 돌았다
[2] % 스타일:
  >>> 비싼 계산이 돌았다
[3] isEnabledFor 가드:
```

★ **[1] 과 [2] 가 똑같이 돈다.** `expensive()` 는 **함수 호출의 인자**라서
`log.debug` 에 들어가기 **전에** 평가된다 — 단축 평가도 지연도 없다([01번](../01-object-and-name-binding/2-summary.md)의 인자 평가 규칙).

| 무엇이 지연되나 | f-string | `%` 스타일 인자 | `isEnabledFor` 가드 | 지연 객체 |
|---|---|---|---|---|
| 인자를 만드는 식(`expensive()`) | ✗ | **✗** | ✓ | ✓ |
| 포맷 치환(`__str__`·`%` 적용) | ✗ | ✓ | ✓ | ✓ |
| 코드가 지저분해지나 | ✗ | ✗ | **✓**(if 한 줄) | 조금 |

**값을 만드는 것까지 미루려면 객체로 감싼다**

```python
class Lazy:
    def __init__(self, fn): self.fn = fn
    def __str__(self): return str(self.fn())

log.setLevel(logging.WARNING)
print("[4] Lazy:")
log.debug("값은 %s", Lazy(expensive))
print("[5] 레벨을 올리면:")
log.setLevel(logging.DEBUG)
log.debug("값은 %s", Lazy(expensive))
```

```text
[4] Lazy:
[5] 레벨을 올리면:
  >>> 비싼 계산이 돌았다
  [찍힘] 값은 결과
```

**판정 기준**

```text
 인자가 이미 있는 값인가?        -> %s 스타일이면 충분하다 (포맷만 미루면 된다)
 인자를 만드는 것이 비싼가?      -> isEnabledFor 가드 또는 지연 객체
 어느 쪽도 아닌가?              -> f-string 이 제일 읽기 좋다
```

★ **무조건 「로그에 f-string 금지」가 아니다.** 인자가 이미 있는 값이면 비용 차이는 포맷 한 번이다.\
비싼 것은 **그 자리에서 무언가를 계산·직렬화·조회하는** 경우다.

### 10. 사용자가 준 템플릿 (연결)

**`str.format` 은 템플릿을 변수로 받을 수 있고 f-string 은 못 한다. 그 「못 함」이 공격을 막는다.**

```python
SECRET = "비밀번호-1234"
class User:
    def __init__(self, name): self.name = name

def render(template, user):
    return template.format(user=user)

u = User("준")
print("정상:", render("안녕 {user.name}", u))
print("공격:", render("{user.__init__.__globals__[SECRET]}", u))
```

```text
정상: 안녕 준
공격: 비밀번호-1234
```

```text
 str.format 의 치환 필드는 두 가지를 허용한다

   {user.name}          속성 접근   ->  .__init__ · .__globals__ 로 타고 갈 수 있다
   {user[0]}            인덱싱      ->  dict 조회까지

  ★ 그래서 사용자가 템플릿을 주면 모듈 전역·환경변수·설정이 새어 나온다.
    이것을 format string attack 이라 부른다.
```

**f-string 은 왜 원리적으로 못 하나**

```text
 f-string 은 "리터럴에 붙는 접두사" 다.
 소스에 적힌 그 자리에서 컴파일된다.

   t = input()        <- 사용자 입력
   f t                <- ★ 이런 문법이 없다
   t 를 f-string 으로 만들 방법이 아예 없다

 ★ 사용자 입력이 "식" 이 될 수 있는 경로가 없다.
   (eval 을 쓰면 되지만 그건 f-string 의 문제가 아니라 eval 의 문제다.)
```

**대안 — `string.Template`**

```python
import string
print("Template        :", string.Template("안녕 $name").substitute(name="준"))
print("safe_substitute :", string.Template("$a $b").safe_substitute(a="1"))
try:
    string.Template("$a $b").substitute(a="1")
except KeyError as e:
    print("substitute 는 빠진 키에 KeyError:", e)
```

```text
Template        : 안녕 준
safe_substitute : 1 $b
substitute 는 빠진 키에 KeyError: 'b'
```

| | 속성 접근 | 인덱싱 | 사용자 템플릿에 |
|---|---|---|---|
| f-string | (임의의 식) | (임의의 식) | **불가능하므로 안전** |
| `str.format` | ✓ | ✓ | **위험** |
| `string.Template` | ✗ | ✗ | **안전** |

★ **셋의 표현력 순서가 안전성 순서의 정확히 반대**다.\
그래서 고르는 기준은 「무엇이 편한가」가 아니라 「**템플릿을 누가 쓰는가**」다.

```text
 템플릿을 내가 소스에 적나?     -> f-string
 템플릿이 내 설정 파일에 있나?   -> str.format  (내가 쓴 것이므로)
 템플릿을 사용자가 주나?         -> string.Template (또는 전용 템플릿 엔진)
```

### 11. 세 층 가르기 (경계)

**언어 보장** — 문서 문장으로 확인한 것.

| 사실 | 근거 |
|---|---|
| f-string 은 **실행 시에 평가되는 식**이다 | 언어 레퍼런스 2.4.3 |
| 각 식은 **왼쪽부터 순서대로** 평가된다 | 〃 |
| 치환 필드 문법은 `{식 [=] [!변환] [:스펙]}` **이 순서** | 〃 |
| 변환은 `s`·`r`·`a` 셋뿐 | 〃 |
| `=` 는 **식 텍스트 + `=` + 값**을 내고 **공백을 보존**한다(3.8+) | 〃 |
| 포맷 스펙 EBNF 와 각 조각의 뜻 | Format Specification Mini-Language |
| `'<'` 는 대부분 객체의 기본, `'>'` 는 **숫자의 기본** | 〃 |
| `'0'`+width 는 **`'='` 정렬 + `'0'` 채우기**와 같다 | 〃 |
| PEP 701 의 세 완화가 **3.12 부터** | 언어 레퍼런스의 *"Changed in version 3.12"* 셋 |
| `%` 의 오른쪽이 **튜플이면 풀린다** | printf-style String Formatting |

**CPython 구현 세부사항** — 실행으로 확인한 것.

| 사실 | 어떻게 확인했나 |
|---|---|
| f-string 이 `FORMAT_VALUE` + `BUILD_STRING` 으로 컴파일된다 | `dis` |
| 고정 조각과 스펙 문자열이 **상수**다 | `dis` 의 `LOAD_CONST` |
| f-string 이 **여러 토큰**으로 쪼개진다 | `tokenize` — 보통 문자열은 `STRING` 하나 |
| `str.format` 은 **메서드 호출**로 남는다 | `dis` 의 `LOAD_ATTR` + `CALL` |
| `f"{a}"` 는 `FORMAT_VALUE()`, `f"{a!s}"` 는 `FORMAT_VALUE(str)` | `dis` 의 인자 |
| `object.__format__` 이 빈 스펙에만 `str(self)` 를 돌려준다 | `TypeError` 문구 |

**이 판(3.12.3)의 관찰** — 버전이 오르면 다시 찍어야 하는 것.

| 관찰 | 어디가 흔들리나 |
|---|---|
| ★★ **`"%s-%s" % (a, b)` 가 `BINARY_OP %` 없이 접힌다** | **컴파일러 최적화다.** 문서 어디에도 없다 |
| 접히는 조건이 「리터럴 + 리터럴 튜플 + `%s`/`%r`/`%a`」인 것 | 〃 — 조건이 판마다 달라질 수 있다 |
| 명령 이름 `FORMAT_VALUE`·`BUILD_STRING`·`RETURN_CONST` | **3.13 에서 `FORMAT_VALUE` 가 `CONVERT_VALUE`/`FORMAT_SIMPLE`/`FORMAT_WITH_SPEC` 로 쪼개졌다** |
| `SyntaxError`·`TypeError`·`ValueError` 의 **문구** | 예외 종류는 명세지만 문구는 아니다 |
| 토큰 이름 `FSTRING_START`/`MIDDLE`/`END` | 3.12 에 새로 생겼다 |

**그래서 이렇게 적으면 틀린다**

- ✗ 「f-string 은 문자열 리터럴이다」 → ○ **실행 시에 평가되는 식**이다.
- ✗ 「`f"{x}"` 는 `str(x)` 와 같다」 → ○ **`format(x, "")`** 이다.
- ✗ 「`%` 포맷은 연산자 호출이라 f-string 보다 느리다」\
  ○ **이 판에서는 조건이 맞으면 같은 바이트코드로 접힌다.** 단 그것은 **관찰이지 보장이 아니다.**
- ✗ 「`"%s" % (a,)` 는 `f"{a}"` 와 같다」 → ○ **`f"{a!s}"` 와 같다.**
- ✗ 「로깅에 `%` 스타일을 쓰면 지연된다」 → ○ **포맷 치환만** 지연된다.
- ✗ 「PEP 701 이 f-string 을 빠르게 했다」 → ○ **토크나이저·문법만** 바꿨다.
- ✗ 「`f"{v:>10}"` 은 아무 값에나 된다」 → ○ `__format__` 이 스펙을 안 받으면 **`TypeError`**.

> **구현 세부사항(implementation detail)** — 언어 명세가 보장하지 않고 특정 구현이 그렇게 만들어 둔 것.\
> 여기서는 **`%` 포맷이 접히는 것**이 대표다. 「빠르다」를 이 관찰 위에 세우면 다음 판에서 틀린다.

**판정 기준 한 줄**

**「이 문자열을 나중에 쓰겠다」고 하고 있으면 f-string 은 틀린 도구다.** 이미 만들어진 뒤이기 때문이다.

---

## 실행 검증

이 파일에 실린 출력은 전부 아래 환경에서 직접 돌려 얻었다.

```text
$ python3 --version
Python 3.12.3
$ python3 -c "import sys; print(sys.implementation.name)"
cpython
```

| 문항 | 무엇을 돌렸나 | 몇 번 |
|---|---|---|
| 1 | f-string 대 `str.format` 평가 시점, 기본 인자 f-string | 각 1회 |
| 2 | **`dis` 로 3방식 + `%` 변형 7종 + `FORMAT_VALUE` 인자 3종** | 각 1회 |
| 3 | `__str__`/`__repr__`/`__format__` 을 다 가진 클래스에 5가지 표기 + `%s` | 각 1회 |
| 4 | 포맷 스펙 조각 24종, `bool` 4형태 | 각 1회 |
| 5 | 5타입 × 스펙, `OnlyStr` 2형태, `Money.__format__`, `date` | 각 1회 |
| 6 | `=` 표기 5형태 + 5값 | 각 1회 |
| 7 | PEP 701 5식, `SyntaxError` 2종, **`tokenize` 2판** | 각 1회 |
| 8 | `%` 오른쪽 5종, 인자 수 불일치 | 각 1회 |
| 9 | **로깅 3판(레벨 WARNING/DEBUG) × 2실험 + 지연 객체** | 각 1회 |
| 10 | format string attack, `string.Template` 3형태 | 각 1회 |

**★ 한 판으로 결론이 안 나는 것을 여러 판 던진 자리**

- **2번** — `"%s-%s" % (a, b)` 하나만 보면 「`%` 도 f-string 과 같다」로 끝난다.\
  **`%d`·`%x`·변수 오른쪽·`%(name)s` 를 같이 던져야** 접히는 조건이 좁다는 것이 드러났다.\
  그리고 `FORMAT_VALUE` 의 **인자까지 봐야** `f"{a}"` 와는 다르다는 것이 보인다.
- **9번** — `Loud.__str__` 만으로 재면 「`%` 스타일이 지연시킨다」로 끝난다.\
  **`expensive()` 를 인자로 넘기는 두 번째 실험**을 해야 「인자는 지연 안 된다」가 드러난다.\
  ★ 여기서 브리핑 전제가 한 칸 좁혀졌다 — 흔히 말하는 「로깅은 `%` 로」는 **포맷 치환에만** 해당한다.
- **7번** — 3.12 에서 되는 것만 보면 「좋아졌다」로 끝난다.\
  **`tokenize` 를 보통 문자열과 나란히 던져야** 「왜」가 나온다(토큰이 하나인가 여럿인가).

**「출력 없음」이 근거인 자리**

- 9번 [B]·[3]·[4] — **아무 줄도 안 찍힌 것**이 지연의 증거다.
- 2번 — `BINARY_OP` 가 **목록에 없는 것**이 「접혔다」의 증거다.

**못 잰 것 — 제3의 상태**

- **7번의 3.11 오류 메시지**는 **이 머신에 3.11 이 없어 잴 수 없었다.** 3.12 쪽만 실측이고
  3.11 쪽은 「같은 코드가 `SyntaxError` 가 된다」는 문서 근거(*"Changed in version 3.12"*)만 있다.\
  본문에 그렇게 밝혔다 — **손으로 지어낸 메시지를 싣지 않았다.**
- **3.14 의 t-string(PEP 750)** 도 같은 이유로 안 실었다.

**구현 의존 항목 — 버전이 오르면 다시 찍을 것**

| 다시 찍을 것 | 왜 |
|---|---|
| 2번의 모든 `dis` 출력 | 명령 이름이 3.13 에서 이미 바뀌었다 |
| 2번의 `%` 접기 조건 | 컴파일러 최적화다 |
| 7번의 `tokenize` 토큰 이름 | 3.12 에 새로 생긴 이름이다 |
| 예외 **문구** 전부 | 예외 종류는 명세지만 문구는 아니다 |

나머지(평가 시점, 치환 필드 문법과 순서, `__format__` 우선, 스펙의 각 조각, `=` 의 의미,
`%` 의 튜플 규칙, PEP 701 이 푼 세 가지)는 **언어 보장**이므로 어떤 구현에서도 같아야 한다.
