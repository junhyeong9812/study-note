# c/syntax/02 — 기본 타입·크기·고정폭 정수: 표준은 최소만 정한다 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — Arithmetic types (C)](https://en.cppreference.com/w/c/language/arithmetic_types) · [GCC 13 — Implementation-defined behavior](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/C-Implementation.html)
> **실행 검증** — 이 문서의 모든 수치·출력은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · x86-64 Linux(LP64) 에서 실제로 돌려 얻은 것이다.\
> 기본 플래그는 `-std=c17 -Wall -Wextra` 이고, 다른 표준을 쓴 블록은 그 자리에 밝혔다.\
> gcc 13 에는 `-std=c23` 이 **없다** — C23 확인은 전부 `-std=c2x`(`__STDC_VERSION__ = 202000L`).
> ★ **이 문서의 수치는 대부분 「이 환경의 값」이지 「C 의 값」이 아니다.** 그 경계가 이 주제의 본체다.
> **버전** — `<stdint.h>`·`_Bool` 은 C99 부터. `bool`/`true`/`false` 키워드화는 **C23 부터**.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> **경계** — 「2진 표현·2의 보수·엔디언」은 [`../../../../data-representation/`](../../../../data-representation/) 가 정본이다.\
> 여기는 **C 에서 어떤 타입을 고르나**만 쓴다.

## 한눈에 — 쉽게 말하면

**C 의 기본 타입은 옷 사이즈이지 줄자 눈금이 아니다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 「M 사이즈는 가슴둘레 **최소** 95cm 이상」 | 표준이 정한 것 — `int` 는 `-32767\~32767` 을 **담을 수 있어야** 한다 |
| 이 가게의 M 은 실제로 98cm | 이 환경의 실제 값 — `int` 는 4바이트, `INT_MAX = 2147483647` |
| 가게가 붙여 놓은 치수표 | `<limits.h>` — 구현이 **문서화 의무를 지는** 자리 |
| 「가슴둘레 정확히 98cm」라고 못박은 옷 | `<stdint.h>` 의 `int32_t` — 폭이 정확히 그 값이거나 **아예 없다** |
| 「최소 98cm 이상이면 아무거나, 제일 편한 걸로」 | `int_fast32_t` — 구현이 빠른 쪽을 고른다 |

- 「M 사이즈」를 산다고 **가슴둘레 98cm 이 보장되지는 않는다.**\
  가게마다 다르고, 보장은 「최소 95cm」뿐이다.
- 그래서 `sizeof(int)` 가 4 라는 것은 **이 가게의 치수**이지 옷 규격이 아니다.
- 치수가 정확히 필요하면 사이즈가 아니라 **숫자로 된 옷**(`int32_t`)을 사야 한다.\
  그런데 그런 옷이 **없는 가게도 있다** — `int32_t` 는 「있으면 정확히 32비트」이지 「언제나 있다」가 아니다.

```text
  표준이 보장하는 것              이 환경(x86-64 LP64)의 실제

  char   >= 8 비트                char        1 바이트 (8 비트)
  short  >= 16 비트               short       2 바이트
  int    >= 16 비트   <- 32 아님!  int         4 바이트
  long   >= 32 비트               long        8 바이트
  llong  >= 64 비트               long long   8 바이트

  + 크기 순서만 보장: char <= short <= int <= long <= long long
```

실무에서 이게 터지는 자리는 **파일 포맷·네트워크 프로토콜·공유 메모리**다.\
`struct { long len; }` 를 그대로 write 한 파일은 LP64 리눅스(8바이트)와 LLP64 윈도우(4바이트)에서 **길이 필드가 다르게 읽힌다.**

> **LP64 / LLP64** — 64비트 환경에서 어느 타입을 64비트로 할지 고른 관례.\
> 예: 리눅스·macOS 는 LP64(`long` 과 포인터가 8바이트), 윈도우는 LLP64(`long` 이 4바이트, `long long` 과 포인터가 8바이트).\
> **표준이 정한 게 아니라 플랫폼이 고른 것**이다.

> **바이트(byte)** — C 에서 바이트는 「8비트」가 아니라 「**`char` 하나가 차지하는 크기**」로 정의된다.\
> 예: 그래서 `sizeof(char)` 는 **어느 환경에서나 1** 이고, 한 바이트가 몇 비트인지는 `CHAR_BIT` 이 말해 준다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `int` 가 4바이트라는 것은 **누가 보장하는가** — 표준인가, 이 컴파일러인가, 이 CPU 인가.
2. 폭이 꼭 필요할 때 `<stdint.h>` 의 **세 가족**(`int32_t`·`int_least32_t`·`int_fast32_t`) 중 무엇을 고르는가.
3. `sizeof` 의 결과·16진 리터럴·`char` 의 부호가 **부호 없음(unsigned)으로 새는 자리**는 어디인가.

## 동작 방식

### (1) 이 환경의 실제 값 — 찍어서 확인한다

**언제 쓰나** — 새 환경에 들어갔을 때 맨 먼저. 외우지 말고 물어본다.

```text
CHAR_BIT = 8
char                  1
signed char           1
short                 2
int                   4
long                  8
long long             8
float                 4
double                8
long double          16
void *                8
size_t                8
ptrdiff_t             8
intptr_t              8
_Bool                 1
--- limits.h ---
CHAR_MIN=-128 CHAR_MAX=127
SCHAR_MIN=-128 SCHAR_MAX=127 UCHAR_MAX=255
SHRT_MIN=-32768 SHRT_MAX=32767 USHRT_MAX=65535
INT_MIN=-2147483648 INT_MAX=2147483647 UINT_MAX=4294967295
LONG_MIN=-9223372036854775808 LONG_MAX=9223372036854775807 ULONG_MAX=18446744073709551615
LLONG_MIN=-9223372036854775808 LLONG_MAX=9223372036854775807 ULLONG_MAX=18446744073709551615
--- stdint.h ---
int8_t=1 int16_t=2 int32_t=4 int64_t=8
int_fast8_t=1 int_fast16_t=8 int_fast32_t=8 int_fast64_t=8
int_least8_t=1 int_least16_t=2 int_least32_t=4 int_least64_t=8
SIZE_MAX=18446744073709551615 PTRDIFF_MAX=9223372036854775807 INTPTR_MAX=9223372036854775807
```

그림 해설 (한 단계씩):

- `long` 과 `long long` 이 **둘 다 8바이트**다 — 순서 보장(`long <= long long`)만 지키면 같아도 된다.
- **`int_fast16_t` 가 8바이트**다. 「16비트면 충분하다」고 했는데 glibc 가 `long` 을 골랐다.\
  이름에 16이 들어 있다고 2바이트가 아니다 — **`fast` 는 「빠른 쪽」이지 「작은 쪽」이 아니다.**
- `long double` 이 16바이트인데 유효 비트는 64뿐이다([`04-floating-point-types-and-conversions/`](../04-floating-point-types-and-conversions/)).
- `size_t`·`ptrdiff_t`·`intptr_t` 가 전부 8바이트다 — **이 환경에서** 그렇다는 것이지 규칙이 아니다.

비용 — 없다. `printf("%zu", sizeof(T))` 한 줄이다.

### (2) 표준이 보장하는 것 — `_Static_assert` 로 못박는다

**언제 쓰나** — 이식성이 걸린 코드를 쓸 때. 「가정」을 **컴파일 에러로 바꾸는** 방법이다.

```c
/* 어느 환경에서도 참이어야 하는 것 */
_Static_assert(sizeof(char) == 1,            "sizeof(char) 는 언제나 1");
_Static_assert(CHAR_BIT >= 8,                "바이트는 최소 8비트");
_Static_assert(SCHAR_MAX >= 127,             "signed char 최소 범위");
_Static_assert(SHRT_MAX  >= 32767,           "short 최소 범위");
_Static_assert(INT_MAX   >= 32767,           "int 최소 범위는 32767 — 65535 가 아니다");
_Static_assert(LONG_MAX  >= 2147483647L,     "long 최소 범위");
_Static_assert(LLONG_MAX >= 9223372036854775807LL, "long long 최소 범위");
_Static_assert(sizeof(short) <= sizeof(int), "크기 순서");
_Static_assert(sizeof(int)  <= sizeof(long), "크기 순서");

/* 이 환경에서만 참인 것 — 다른 환경에서 깨지라고 일부러 둔다 */
_Static_assert(sizeof(int) == 4,  "이 환경의 int 는 4바이트");
_Static_assert(sizeof(long) == 8, "이 환경(LP64)의 long 은 8바이트");
```

전부 통과했다.

```text
전부 통과. int 의 표준 최소 범위는 32767, 이 환경의 실제 범위는 2147483647
```

일부러 깨 보면 이렇게 나온다.

```text
ex2.c:1:1: error: static assertion failed: "this platform's int is 8 bytes"
    1 | _Static_assert(sizeof(int) == 8, "this platform's int is 8 bytes");
      | ^~~~~~~~~~~~~~
```

그림 해설 (한 단계씩):

- 위쪽 덩어리는 **어느 환경에서도 통과해야 한다.** 안 통과하면 표준을 안 지키는 구현이다.
- 아래쪽 덩어리는 **일부러 깨지라고 둔 것**이다. 16비트 `int` 환경으로 옮기면 빌드가 여기서 멈춘다.
- 이 방식의 값어치: **가정이 주석이 아니라 빌드 실패가 된다.**\
  「`int` 는 4바이트겠지」를 머릿속에 두는 대신 컴파일러가 대신 기억한다.

비용 — 컴파일 시간뿐. 런타임 코드가 안 생긴다. 정본은 목록의 **53번 주제**.

> **`_Static_assert`** — 컴파일 시간에 조건을 검사해 거짓이면 컴파일을 실패시키는 선언(C11).\
> 예: `_Static_assert(sizeof(int) == 4, "메시지");` 는 조건이 참이면 아무 코드도 안 만들고, 거짓이면 그 메시지로 컴파일이 멈춘다.\
> C23 부터는 `static_assert` 라는 철자를 헤더 없이 쓸 수 있다(아래 (6)).

### (3) `char` 는 세 타입이다 — 부호는 구현 정의

**언제 �나** — 바이트를 다룰 때마다. 이 주제에서 사고가 가장 잦은 자리다.

```text
  C 의 문자 타입은 셋이고 서로 다른 타입이다.

  char           <- 부호 있는지 없는지 ★ 구현 정의
  signed char    <- 반드시 부호 있음
  unsigned char  <- 반드시 부호 없음

  char 는 signed char 와도 unsigned char 와도 다른 "제3의 타입"이다.
  (값 범위는 둘 중 하나와 같지만 타입 호환성은 별개다)
```

이 환경에서 찍어 봤다. 그리고 **플래그 하나로 뒤집힌다.**

```text
===== gcc (기본) =====
CHAR_MIN = -128, CHAR_MAX = 127
char 는 부호 있음
(char)200 을 int 로 승격하면 -56
(unsigned char)200 -> 200
char/signed char/unsigned char 는 서로 다른 타입인가: __CHAR_UNSIGNED__ 미정의
===== gcc -funsigned-char =====
CHAR_MIN = 0, CHAR_MAX = 255
char 는 부호 없음
(char)200 을 int 로 승격하면 200
(unsigned char)200 -> 200
char/signed char/unsigned char 는 서로 다른 타입인가: __CHAR_UNSIGNED__ 정의됨
```

그림 해설 (한 단계씩):

- **같은 소스, 같은 컴파일러, 플래그 하나 차이로 `(char)200` 이 `-56` 과 `200` 으로 갈렸다.**
- `CHAR_MIN` 이 답을 준다 — **음수면 부호 있음**이다. 외울 필요 없이 물어보면 된다.
- x86 리눅스는 부호 있고, **ARM 리눅스는 부호 없다**(널리 알려진 관례다 — 이 머신에서는 확인 못 했다).
- 실무 결론: **바이트를 다룰 때는 `unsigned char` 를 쓴다.**\
  `char` 는 「문자」용이고, 「바이트」용이 아니다.

비용 — 없다. 타입 선택의 문제다.

> **구현 정의 동작(implementation-defined behavior)** — 구현마다 다르되 **문서에 적을 의무가 있는** 것.\
> 예: `char` 의 부호. gcc 문서와 `<limits.h>` 의 `CHAR_MIN` 이 답을 준다.

### (4) 고정폭 정수 세 가족 — 무엇을 보장하나

**언제 쓰나** — 파일·네트워크·하드웨어 레지스터처럼 **폭이 계약인 자리**.

```text
  int32_t          정확히 32비트 · 패딩 없음 · 2의 보수
                   ★ 그런 타입이 없으면 이 이름 자체가 제공되지 않는다 (선택 사항)

  int_least32_t    "최소 32비트인 것 중 가장 작은 것"
                   ★ 언제나 제공된다

  int_fast32_t     "최소 32비트인 것 중 구현이 빠르다고 보는 것"
                   ★ 언제나 제공된다 · 크기는 구현 마음
```

이 환경의 실제 배정이다(`gcc -E` 로 전처리 결과에서 뽑았다).

```text
typedef __int32_t int32_t;              -> signed int    (4바이트)
typedef __int_least32_t int_least32_t;  -> signed int    (4바이트)
typedef long int int_fast32_t;          -> long          (8바이트)  ★
typedef long int int_fast16_t;          -> long          (8바이트)  ★
typedef signed char int_fast8_t;        -> signed char   (1바이트)
```

그림 해설 (한 단계씩):

- **`int_fast32_t` 가 `long`(8바이트)이다.** 4바이트가 아니다.\
  x86-64 에서 64비트 연산이 32비트보다 느리지 않고 부호 확장이 없어 편하다는 판단이다 — **glibc 의 선택**이다.
- **`int_fast8_t` 만 1바이트**다. 같은 `fast` 가족 안에서도 판단이 갈린다.
- `int32_t` 와 `int_least32_t` 는 여기서 같은 타입이지만 **보장이 다르다.**\
  앞은 「정확히 32」, 뒤는 「32 이상 중 최소」다.

고르는 규칙.

| 무엇을 하나 | 고를 것 | 왜 |
|---|---|---|
| 파일·네트워크·하드웨어 레지스터 | **`int32_t`** 계열 | 폭이 계약이다. 없으면 빌드가 깨지는 게 낫다 |
| 값 범위만 보장되면 되는 계산 | **`int_least32_t`** | 어디서나 있고 메모리를 아낀다 |
| 핫 루프의 인덱스·누적 변수 | **`int_fast32_t`** | 구현이 빠른 폭을 고른다 |
| 배열 크기·인덱스 | **`size_t`** | `sizeof` 의 타입이고 객체 크기를 담도록 되어 있다 |
| 두 포인터의 차 | **`ptrdiff_t`** | 포인터 뺄셈의 결과 타입이다 |
| 포인터를 정수로 보관 | **`intptr_t`/`uintptr_t`** | 왕복이 보장되는 유일한 정수 타입(선택 사항) |
| 그냥 수 세기 | **`int`** | 이유 없이 고정폭을 쓰면 읽는 비용만 는다 |

비용 — `int_fast*` 는 메모리를 더 쓸 수 있다(배열로 쓰면 8배). **배열에는 `int_least*` 나 고정폭을 쓴다.**

### (5) 리터럴의 타입 — 10진과 16진이 다른 길을 간다

**언제 쓰나** — `0xFFFFFFFF` 같은 마스크를 쓸 때마다.

```text
  10진 리터럴 (접미사 없음)          16진/8진 리터럴 (접미사 없음)

    int                                int
     |  안 들어가면                     |  안 들어가면
     v                                 v
    long                             unsigned int   ★ 부호 없는 쪽으로 샌다
     |                                 |
     v                                 v
    long long                        long
                                       |
                                       v
                                     unsigned long ...
```

`_Generic` 으로 실제 타입을 찍었다.

```text
1                      -> int
1u                     -> unsigned int
1L                     -> long
1UL                    -> unsigned long
1LL                    -> long long
2147483648             -> long
0x7fffffff             -> int
0x80000000             -> unsigned int      ★
0xffffffff             -> unsigned int      ★
4294967295             -> long              ★ 같은 값인데 다른 타입
'a'                    -> int
1.0                    -> double
1.0f                   -> float
1.0L                   -> long double
sizeof(int)            -> unsigned long     ★
```

그림 해설 (한 단계씩):

- `0xffffffff` 와 `4294967295` 는 **같은 값인데 타입이 다르다.**\
  앞은 `unsigned int`, 뒤는 `long`. 16진은 `unsigned` 단계를 거치고 10진은 안 거친다.
- 이것이 왜 문제인가: `0xffffffff` 가 `unsigned` 라서 **비교·연산이 전부 부호 없는 쪽으로 끌려간다.**\
  정본은 [`03-integer-promotion-and-usual-arithmetic-conversions/`](../03-integer-promotion-and-usual-arithmetic-conversions/).
- **`'a'` 는 `char` 가 아니라 `int`** 다. C 에서 문자 상수의 타입은 `int` 다(C++ 와 다른 자리).
- **`sizeof` 의 결과는 `unsigned long`**(= `size_t`)이다. 이것이 다음 주제 사고의 출발점이다.

비용 — 없다. 다만 **마스크를 쓸 때 `u` 접미사를 명시**하면 의도가 드러난다.

### (6) `_Bool` 과 `bool` — C23 에서 키워드가 됐다

**언제 쓰나** — 참·거짓을 담을 때.

```text
  C99 ~ C17                          C23
  ---------                          ---
  _Bool           키워드              _Bool          (남아 있다)
  bool            <stdbool.h> 의 매크로  bool          ★ 키워드
  true / false    <stdbool.h> 의 매크로  true / false  ★ 키워드 (타입은 bool)
```

던져서 확인했다.

```text
sizeof(_Bool) = 1
_Bool b = 5   -> 1
_Bool b = 0.5 -> 1
_Bool b = NULL-> 0
_Bool + _Bool 의 타입 폭: 4

c17  헤더 없이 bool: ex2.c:2:18: error: unknown type name ‘bool’
c2x  헤더 없이 bool: 1 1
c17 + stdbool.h    : 1 1
```

그림 해설 (한 단계씩):

- `_Bool` 로의 변환은 **절단이 아니라** 「**0인가 아닌가**」다.\
  `0.5` 는 `int` 로는 `0` 이 되지만 `_Bool` 로는 **`1`** 이다. 다른 타입과 규칙이 다르다.
- `_Bool + _Bool` 의 폭이 4 — **정수 승격으로 `int` 가 된다.**\
  `_Bool` 도 승격 대상이다([`03`](../03-integer-promotion-and-usual-arithmetic-conversions/)).
- C17 에서 `bool` 은 **키워드가 아니다.** `<stdbool.h>` 가 `#define bool _Bool` 을 해 줄 뿐이다.
- C23(`-std=c2x`)에서는 **헤더 없이 통과**한다. `<stdbool.h>` 는 호환을 위해 남아 있다.

비용 — 1바이트. 구조체에 여럿 넣으면 패딩이 붙는다(목록의 **22번 주제**).

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### 형태 — 타입 이름을 쓰는 자리

```c
#include <limits.h>   /* CHAR_BIT · INT_MAX · LONG_MIN ... */
#include <stdint.h>   /* int32_t · int_fast32_t · SIZE_MAX · intptr_t ... */
#include <stddef.h>   /* size_t · ptrdiff_t · NULL */
#include <stdbool.h>  /* C17 까지: bool · true · false */

signed char   sc;   /* 부호 있는 1바이트 — "작은 정수" */
unsigned char uc;   /* 부호 없는 1바이트 — "바이트" */
char          c;    /* 문자 — 부호는 구현 정의 */
int32_t       i32;  /* 정확히 32비트 (없을 수도 있다) */
size_t        n;    /* 객체 크기·인덱스 */
ptrdiff_t     d;    /* 포인터 차 */
```

### 금지 사례 — 서식 지정자를 틀리는 것

```c
size_t n = 10;
printf("%d\n", n);        /* 틀림 — size_t 는 %zu */
int64_t v = 1;
printf("%ld\n", v);       /* 이식성 없음 — int64_t 는 %" PRId64 " */
```

`-Wall -Wextra` 가 두 줄을 잡는데 **`%ld` 쪽은 잡지 않는다.**

```text
ex.c:8:14: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘size_t’ {aka ‘long unsigned int’} [-Wformat=]
ex.c:10:14: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘ptrdiff_t’ {aka ‘long int’} [-Wformat=]
--- 실행 ---
10
1
2
10 2
```

- `%ld` 에 경고가 없는 이유는 **이 환경에서 `int64_t` 가 진짜 `long` 이기 때문**이다.\
  LLP64 윈도우로 옮기면 `int64_t` 가 `long long` 이라 같은 줄이 경고가 된다.\
  **경고가 없다는 것이 이식성의 근거가 아니다.**
- 그리고 경고가 난 `%d` 두 줄도 **출력은 멀쩡하다**(`10`·`2`). x86-64 에서 작은 값이라 우연히 맞았을 뿐이다.\
  이 갈래의 제1 규칙 — 「안 터졌다」는 「안전하다」가 아니다.
- `size_t` 는 **`%zu`**, `ptrdiff_t` 는 `%td`, `intmax_t` 는 `%jd`.
- 고정폭 타입은 `<inttypes.h>` 의 매크로를 쓴다 — `printf("%" PRId64 "\n", v);`\
  정본은 목록의 **47번 주제**.

### 규칙 불릿

- **`sizeof(char)` 는 어느 환경에서나 1** 이다. 이것이 「바이트」의 정의다.
- **`CHAR_BIT` 이 8이라는 보장은 없다.** 최소 8이다(이 환경은 8).
- 표준이 보장하는 것은 **최소 범위와 크기 순서**뿐이다.
- `int` 의 표준 최소 범위는 **`-32767\~32767`** 이다 — 65535 도 2147483647 도 아니다.
- `sizeof` 의 결과 타입은 **`size_t`(부호 없음)** 이다.
- 문자 상수 `'a'` 의 타입은 **`int`** 다.
- 16진·8진 리터럴은 값이 안 들어가면 **`unsigned` 로 샌다**.
- `_Bool` 로의 변환은 절단이 아니라 「**0인가 아닌가**」다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. **넷 다 에러 없이 통과한다.**

### 1. `int` 가 32비트라고 가정한다

```text
왼쪽 — x86-64 리눅스에서 짠 코드             오른쪽 — 16비트 int 환경 (임베디드)
+-----------------------------------+      +-----------------------------------+
| int count = 0;                    |      | int count = 0;                    |
| for (...) count++;   // 10만 번    |      | for (...) count++;   // 10만 번    |
|                                   |      |                                   |
| INT_MAX = 2147483647              |      | INT_MAX = 32767                   |
| 문제 없음                          |      | 32768번째에 ★ 부호 있는 오버플로    |
|                                   |      | = UB                              |
+-----------------------------------+      +-----------------------------------+
```

- 표준이 보장하는 `int` 의 범위는 **`-32767\~32767`** 뿐이다.
- 「10만은 `int` 에 들어가겠지」는 **이 환경에서만 참**이다.
- 막는 법: `int32_t` 를 쓰거나 `_Static_assert(INT_MAX >= 100000, "...")` 를 박는다.

### 2. `char` 로 바이트를 다룬다

```c
char c = getbyte();        /* 0xC8 = 200 을 받았다 */
if (c > 127) { ... }       /* 이 환경에서는 절대 안 탄다 — c 는 -56 이다 */
int idx = c;               /* -56 -> 배열 인덱스로 쓰면 배열 밖 */
```

- `char` 의 부호가 **구현 정의**라 이 코드는 **환경에 따라 동작이 갈린다.**
- x86 리눅스에서는 `c == -56`, `-funsigned-char` 나 ARM 리눅스에서는 `c == 200`.
- `<ctype.h>` 의 `isalpha` 계열에 `char` 를 그대로 넘기는 것이 같은 사고다 —\
  음수를 넘기면 **UB** 다(정본은 목록의 **52번 주제**).
- 막는 법: **바이트는 `unsigned char`.** 한 줄이다.

### 3. `size_t` 를 `int` 와 섞는다

```c
int n = -1;
if (n < sizeof(arr)/sizeof(arr[0])) { ... }   /* 거짓이 된다 */
```

- `sizeof` 의 결과가 `size_t`(부호 없음)라 `n` 이 **`18446744073709551615`** 로 읽힌다.
- 이 주제에서 씨앗이 뿌려지고 다음 주제에서 꽃이 핀다 —\
  전모는 [`03-integer-promotion-and-usual-arithmetic-conversions/`](../03-integer-promotion-and-usual-arithmetic-conversions/).

```text
sizeof 의 결과 타입은 부호 없음: (sizeof(int) - 5) = 18446744073709551615
```

- `sizeof(int)` 는 4 인데 5 를 빼면 `-1` 이 아니라 `ULONG_MAX` 다.

### 4. `int_fast16_t` 를 「작은 타입」으로 읽는다

```c
int_fast16_t buf[1000000];    /* 2MB 를 기대했는데 8MB */
```

```text
int_fast8_t=1 int_fast16_t=8 int_fast32_t=8 int_fast64_t=8
```

- **`fast` 는 「빠른 쪽」이고 크기 보장이 없다.** 이 환경에서 8바이트다.
- 배열에 쓰면 기대의 **4배 메모리**를 먹는다.
- 막는 법: **배열·구조체 멤버에는 `int_least*` 나 고정폭**을 쓴다. `fast` 는 지역 변수·루프 인덱스용이다.

## 구현 세부사항 대 언어 보장

C 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 네 층을 갈라야 한다.\
**이 주제는 거의 전부가 가운데 두 층이다** — 그래서 「이 환경의 값」과 「C 의 값」을 가르는 게 본체다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| **표준이 정한 것** | 어느 구현에서도 같다 | `sizeof(char) == 1` · `CHAR_BIT >= 8` · 각 타입의 **최소 범위** · 크기 순서(`char <= short <= int <= long <= long long`) · `sizeof` 의 결과 타입이 `size_t` · `'a'` 의 타입이 `int` · `int32_t` 는 「있으면 정확히 32비트·패딩 없음·2의 보수」 · `_Bool` 변환이 「0인가 아닌가」 | `_Static_assert` 전수 통과 · `_Generic` 타입 출력 |
| **구현 정의** | 구현마다 다르되 **문서화 의무가 있다** | `sizeof(int)`=4 · `sizeof(long)`=8(LP64) · `CHAR_BIT`=8 · **`char` 의 부호**(여기선 있음) · `int_fast*` 의 실제 폭 · `size_t`/`ptrdiff_t`/`intptr_t` 의 폭 · `int32_t` 등이 **존재하는지 여부** | `sizeof` 출력 · `<limits.h>` 매크로 · `gcc -E` 로 본 typedef · `-funsigned-char` 로 **뒤집어 봄** |
| **미명시** | 몇 가지 중 하나, 문서화 의무 없음 | (이 주제에는 거의 없다 — 타입 크기는 전부 문서화 의무가 있는 쪽이다) | — |
| **UB** | 아무 일이나 일어날 수 있다 | 타입 **선언**에는 없다. **값이 범위를 넘는 연산**에서 시작된다 — 그것은 [`03`](../03-integer-promotion-and-usual-arithmetic-conversions/) 의 주제 | — |

### 「구현 정의」를 뒤집어 본 증거

구현 정의는 **말로 주장하면 안 되고 뒤집어 보여야** 한다. `char` 의 부호가 그 사례다.

```text
===== gcc (기본) =====          ===== gcc -funsigned-char =====
CHAR_MIN = -128                 CHAR_MIN = 0
(char)200 -> -56                (char)200 -> 200
__CHAR_UNSIGNED__ 미정의         __CHAR_UNSIGNED__ 정의됨
```

- **같은 소스·같은 컴파일러인데 답이 갈린다.**\
  「x86 에서 돌려 보니 `-56` 이더라」는 근거가 아니라 관찰이다.
- 구현 정의 항목은 **컴파일러 문서·`<limits.h>`·전용 매크로**가 답을 준다.\
  여기서는 `CHAR_MIN` 과 `__CHAR_UNSIGNED__` 둘이 같은 것을 말했다.

### 「표준이 정한 것」을 빌드로 못박는 법

`_Static_assert` 덩어리 하나를 헤더에 두면 **가정이 주석이 아니라 빌드 실패**가 된다.\
이 주제에서 가장 실용적인 결론이다. 위 (2)의 11줄이 그 형태다.

### `int32_t` 가 「없을 수도 있다」는 뜻

- `<stdint.h>` 의 **정확폭 타입은 선택 사항**이다 — 그런 폭이 없으면 이름 자체가 제공되지 않는다.
- 그래서 `#include <stdint.h>` 하고 `int32_t` 를 썼는데 **컴파일이 안 되는 환경**이 원리상 있다.\
  (CHAR_BIT 이 9인 DSP 같은 것. 이 머신에서는 확인 못 했다 — **안 돌려 본 것**이다.)
- 반면 `int_least32_t`·`int_fast32_t`·`intmax_t` 는 **언제나 제공된다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 안 고를 것 |
|---|---|---|
| 일반적인 수 세기·루프 | `int` | 이유 없는 `int32_t` |
| 배열 인덱스·크기 | `size_t` | `int`(큰 배열에서 넘친다) |
| 포인터 뺄셈 결과 | `ptrdiff_t` | `int` |
| 바이트 버퍼 | `unsigned char` | `char`(부호가 구현 정의) |
| 파일·네트워크 필드 | `int32_t`·`uint16_t` | `int`·`long`(폭이 환경마다) |
| 핫 루프 누적 변수 | `int_fast32_t` | — |
| 큰 배열의 원소 | `int_least32_t`·고정폭 | `int_fast*`(8배가 될 수 있다) |
| 참·거짓 | `bool`(C23) / `_Bool` | `int`(0/1 관례만으로 두면 값이 샌다) |

판단 규칙 두 줄.

- **폭이 계약이면 고정폭, 아니면 `int`.** 그 중간은 `size_t`·`ptrdiff_t` 처럼 **역할이 정해진 타입**을 쓴다.
- **바이트는 `unsigned char`, 문자는 `char`.** 이 한 줄이 이 주제 사고의 절반을 막는다.

## 핵심 문장

- 표준이 정한 것은 **최소 범위와 크기 순서**뿐이다 — `int` 의 보장은 `-32767\~32767` 이고 32비트가 아니다.
- **`sizeof(char)` 는 언제나 1** 이다. 그것이 바이트의 정의이고, 한 바이트가 몇 비트인지는 `CHAR_BIT` 이 따로 말한다.
- **`char` 의 부호는 구현 정의**다 — `-funsigned-char` 하나로 `(char)200` 이 `-56` 에서 `200` 으로 뒤집혔다.
- `<stdint.h>` 는 세 가족이다 — **정확폭(없을 수 있다) · least(언제나 있다) · fast(폭 보장 없다)**.\
  이 환경의 `int_fast16_t` 는 **8바이트**다.
- **`sizeof` 의 결과는 `size_t`(부호 없음)** 이고, 16진 리터럴은 값이 안 들어가면 `unsigned` 로 샌다 — 다음 주제 사고의 씨앗이 둘 다 여기 있다.
- 가정을 지키는 유일한 방법은 **`_Static_assert` 로 빌드 실패를 만드는 것**이다.

## 관련 자료

- [`../README.md`](../README.md) — C 문법·API 주제 목록(이 주제는 02번)
- [`../../../../data-representation/`](../../../../data-representation/) — **그쪽은 2진 표현·2의 보수·엔디언까지, 여기는 그 위에서 C 가 어떤 타입을 주고 무엇을 보장하나부터.** 비트가 어떻게 생겼나는 거기
- [`../../../c-cpp-csharp.md`](../../../c-cpp-csharp.md) — **그쪽은 「C 의 타입 모델이 왜 이식성 부담을 개발자에게 넘겼나」라는 논증까지, 여기는 「그래서 어떤 타입을 고르나」부터**
- [`01-declaration-syntax-and-reading/`](../01-declaration-syntax-and-reading/) — 선언자를 다 풀고 나면 남는 것이 이 주제의 기본 타입이다
- [`03-integer-promotion-and-usual-arithmetic-conversions/`](../03-integer-promotion-and-usual-arithmetic-conversions/) — `sizeof` 가 `size_t` 인 것 · 16진 리터럴이 `unsigned` 인 것이 **사고가 되는 곳**
- [`04-floating-point-types-and-conversions/`](../04-floating-point-types-and-conversions/) — `float`/`double`/`long double` 쪽
- 목록의 **07번 주제** (`enum` 과 열거 상수) — 열거 상수의 타입 규칙과 C23 고정 기반 타입
- 목록의 **08번 주제** (`sizeof`·정렬·`offsetof`) — `sizeof` 가 컴파일 시간인 자리와 아닌 자리
- 목록의 **47번 주제** (`<stdio.h>` 서식 출력) — `%zu`·`PRId64` 를 고르는 규칙
- 목록의 **53번 주제** (`assert` 와 `static_assert`) — 이 문서의 `_Static_assert` 덩어리가 정본으로 다뤄지는 곳

## 용어 풀이

- **바이트(byte)** — `char` 하나가 차지하는 크기. 8비트라는 보장은 없고 `CHAR_BIT` 이 말해 준다.
- **`CHAR_BIT`** — 한 바이트의 비트 수. 표준은 **최소 8** 만 보장한다. 이 환경은 8.
- **최소 범위** — 표준이 「이 타입은 적어도 이 범위를 담아야 한다」고 정한 것. `int` 는 `-32767\~32767`.
- **LP64 / LLP64** — 64비트 환경의 타입 폭 관례. 리눅스는 LP64(`long` 8바이트), 윈도우는 LLP64(`long` 4바이트).
- **정확폭 정수(exact-width)** — `int8_t\~uint64_t`. 정확히 그 폭이거나 **아예 제공되지 않는다**.
- **최소폭 정수(minimum-width)** — `int_least8_t\~uint_least64_t`. 「그 폭 이상 중 가장 작은 것」. 언제나 있다.
- **최속 정수(fastest minimum-width)** — `int_fast8_t\~uint_fast64_t`. 「그 폭 이상 중 구현이 빠르다고 보는 것」. 크기 보장 없음.
- **`size_t`** — `sizeof` 의 결과 타입. 부호 없음. 객체 크기를 담을 수 있도록 되어 있다.
- **`ptrdiff_t`** — 두 포인터의 차의 타입. 부호 있음.
- **`intptr_t` / `uintptr_t`** — 포인터를 담았다가 되돌릴 수 있는 정수 타입(선택 사항).
- **`_Static_assert`** — 컴파일 시간 단언(C11). 거짓이면 컴파일이 실패한다. C23 부터 `static_assert` 철자.
- **`_Bool`** — 참·거짓 타입(C99). 변환 규칙이 「0인가 아닌가」라 다른 타입과 다르다.
- **구현 정의 동작** — 구현마다 다르되 문서화 의무가 있는 것. 이 주제 대부분이 여기 속한다.

---

## 더 들어가면

- **`INT_MAX` 는 glibc 에서 16진 상수**로 정의되어 있다. `gcc -E` 로 본 전개 결과다.

```text
int a = 0x7fffffff
              ;
long b = 0x7fffffffffffffffL
                ;
int32_t c =
           (2147483647)
                    ;
```

  `INT32_MAX` 는 10진, `INT_MAX` 는 16진 — **같은 값이라도 소스마다 표기가 다르다.**\
  (5)에서 본 규칙대로라면 `0x7fffffff` 는 `int` 에 들어가므로 `unsigned` 로 새지 않는다. 다행히 안전하다.

- **`_Static_assert` 의 메시지에 한글을 쓰면 gcc 가 8진 이스케이프로 뱉는다.**

```text
error: static assertion failed: "\37777777754\37777777635\37777777664 ..."
```

  메시지는 **ASCII 로 쓰는 게 낫다** — 이 머신에서 실제로 확인했다.

- **C23 의 `static_assert` 는 메시지를 생략할 수 있다.** C17 의 `_Static_assert` 는 메시지가 필수다.\
  이 gcc 의 `-std=c2x` 에서 `static_assert(sizeof(int)==4, "...")` 가 **헤더 없이** 통과하는 것은 확인했고,\
  메시지 생략은 이 문서에서 **안 돌려 봤다.**

- **`_BitInt(N)`**(C23)은 임의 폭 정수다. 「고정폭 세 가족」 위에 네 번째가 생긴 셈인데,\
  이 주제의 범위 밖이고 gcc 13 의 지원 여부도 **이 문서에서는 확인하지 않았다.**

- `sizeof` 는 **피연산자를 평가하지 않는다.** 실측으로 확인했다.

```text
sizeof(boom()) = 4  <- 위에 boom 이 안 찍혔으면 sizeof 는 피연산자를 평가하지 않은 것
```

  `boom()` 이 `puts` 를 부르는데 **아무것도 안 찍혔다.** 타입만 보고 크기를 냈다는 뜻이다.\
  VLA 라는 예외가 있고, 그것은 목록의 **08번 주제**·목록의 **18번 주제**의 몫이다.
