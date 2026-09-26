# c/syntax/02 — 기본 타입·크기·고정폭 정수: 표준은 최소만 정한다 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · x86-64 Linux(LP64) 에서 실제로 돌려 얻은 것이다.\
> 기본 플래그는 `-std=c17 -Wall -Wextra` 이고, 다른 표준·플래그를 쓴 블록은 그 자리에 밝혔다.\
> gcc 13 에는 `-std=c23` 이 없어 C23 확인은 전부 `-std=c2x` 로 했다.
> ★ **수치 옆의 괄호가 「누가 보장하나」다.** 그것 없이 값만 외우면 이 주제를 배운 게 아니다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 환경의 실제 크기

**출력**

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
```

**왜 그런가**

```text
  값                 누가 보장하나
  -----------------  ------------------------------------------
  sizeof(char) = 1   ★ 표준     — 어느 환경에서나 1 (바이트의 정의)
  CHAR_BIT = 8         구현 정의 — 표준은 "최소 8"만 정한다
  sizeof(short) = 2    구현 정의
  sizeof(int) = 4      구현 정의 — 표준 보장은 "16비트 이상"
  sizeof(long) = 8     구현 정의 — LP64 관례. 윈도우(LLP64)는 4
  sizeof(long long)=8  구현 정의
  sizeof(void*) = 8    구현 정의
  sizeof(size_t) = 8   구현 정의
  CHAR_MIN = -128      구현 정의 — ★ char 의 부호가 구현 정의라서
  INT_MAX = 2147483647 구현 정의 — 표준 보장은 ">= 32767"
```

**어느 환경에서도 같은 것**

- **`sizeof(char) == 1` 하나뿐이다.**
- 나머지 열한 개는 전부 이 환경의 값이다.
- 「순서」는 보장된다 — `char <= short <= int <= long <= long long`. 하지만 **같아도 된다.**

**`long` 과 `long long` 이 같아도 되는가**

- **된다.** 표준은 순서만 정한다. 이 환경이 그 예다(둘 다 8바이트).
- 보장되는 것은 **각각의 최소 범위**다 — `long` 은 32비트 이상, `long long` 은 64비트 이상.\
  `long` 이 이미 64비트면 `long long` 이 더 클 이유가 없다.

### 2. 표준이 보장하는 최소는 어디까지인가

**보장 범위**

- **`-32767\~32767`** 이다. 32767 쪽이 맞다.
- `65535` 가 아닌 이유: `int` 는 **부호 있는** 타입이라 범위가 0을 중심으로 갈린다.
- `2147483647` 이 아닌 이유: 그건 **32비트일 때의 값**이고, 표준은 16비트 `int` 를 허용한다.
- 음수 쪽이 `-32768` 이 아니라 `-32767` 인 것도 의도적이다 —\
  표준은 2의 보수 말고 다른 부호 표현도 허용했었기 때문에(C23 에서 2의 보수로 못박혔다) **대칭 범위만 보장**한다.

**`sizeof(char)` 가 1 인 이유**

- **정의의 결과**다. C 에서 「바이트」는 8비트가 아니라 「**`char` 하나가 차지하는 크기**」로 정의된다.
- 그래서 `sizeof` 의 단위가 곧 `char` 의 크기이고, `sizeof(char)` 는 자기 자신을 자기 단위로 잰 것이라 **언제나 1**이다.
- 한 바이트가 몇 비트인지는 별개의 질문이고 **`CHAR_BIT`** 이 답한다.

**`CHAR_BIT` 이 8 이 아닐 수 있는가**

- **있다.** 표준 보장은 **최소 8**이다. 9비트·16비트·32비트 바이트를 쓰는 DSP 가 실제로 있다.\
  (이 머신은 8이다 — 다른 값은 **여기서 확인 못 했다**.)
- 그래서 `sizeof(int) * 8` 로 비트 수를 계산하는 코드는 이식성이 없다. `sizeof(int) * CHAR_BIT` 이 맞다.

**가정을 빌드 실패로 바꾸는 법**

```c
_Static_assert(sizeof(int) == 4,  "this platform's int is 4 bytes");
_Static_assert(CHAR_BIT == 8,     "this platform's byte is 8 bits");
```

일부러 깨 보면 이렇게 멈춘다.

```text
ex2.c:1:1: error: static assertion failed: "this platform's int is 8 bytes"
    1 | _Static_assert(sizeof(int) == 8, "this platform's int is 8 bytes");
      | ^~~~~~~~~~~~~~
```

- **런타임 코드가 하나도 안 생긴다.** 컴파일 시간에 끝난다.
- 메시지는 **ASCII 로 쓴다** — 한글을 넣으면 gcc 가 8진 이스케이프로 뱉는다(「더 들어가면」).
- 정본은 목록의 **53번 주제**.

### 3. `(char)200` 은 무엇인가

**출력**

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

**세 값**

- `CHAR_MIN` = **-128** · `c` = **-56** · `(unsigned char)200` = **200**.
- `-56` 이 나오는 이유: 200 을 8비트 2의 보수로 보면 `0xC8` 이고, 최상위 비트가 1이라 음수다.\
  `200 - 256 = -56`.

**어느 층인가**

- **구현 정의**다.
  - 표준이 정한 것 ✗ — `char` 가 부호 있는지는 표준이 안 정했다.
  - **구현 정의 ✓** — 구현이 고르고 **문서에 적을 의무가 있다.** `<limits.h>` 의 `CHAR_MIN` 이 그 문서다.
  - 미명시 ✗ — 문서화 의무가 있으므로.
  - UB ✗ — 아무 일이나 일어나지 않는다. 두 가능성 중 하나다.

**답을 뒤집는 플래그**

- **`-funsigned-char`**(반대는 `-fsigned-char`).
- 그때 값은 `CHAR_MIN = 0` · `c = 200` · `(unsigned char)200 = 200`.
- **같은 소스·같은 컴파일러·같은 머신인데 답이 갈린다.**\
  「x86 에서 돌려 보니 `-56` 이더라」는 근거가 아니라 관찰이다.
- 덤으로 `__CHAR_UNSIGNED__` 매크로가 정의되었다가 사라진다 — 코드에서 분기할 수 있다는 뜻이다.

**실무 결론**

- **바이트는 `unsigned char`, 문자는 `char`.**
- `char`·`signed char`·`unsigned char` 는 **서로 다른 세 타입**이다.\
  값 범위가 둘 중 하나와 같더라도 타입 호환성은 별개다.

### 4. 리터럴의 타입

**출력** (`_Generic` 으로 실제 타입을 찍었다)

```text
1                      -> int
1u                     -> unsigned int
1L                     -> long
1UL                    -> unsigned long
1LL                    -> long long
2147483648             -> long
0x7fffffff             -> int
0x80000000             -> unsigned int
0xffffffff             -> unsigned int
4294967295             -> long
'a'                    -> int
1.0                    -> double
1.0f                   -> float
1.0L                   -> long double
sizeof(int)            -> unsigned long
```

**아홉 개의 타입**

| 리터럴 | 타입 |
|---|---|
| `1` | `int` |
| `1u` | `unsigned int` |
| `1L` | `long` |
| `'a'` | **`int`** (C 에서 문자 상수는 `int` 다 — C++ 와 다른 자리) |
| `0x7fffffff` | `int` (들어간다) |
| `0x80000000` | **`unsigned int`** |
| `0xffffffff` | **`unsigned int`** |
| `2147483648` | `long` |
| `4294967295` | **`long`** |
| `sizeof(int)` | `unsigned long` (= `size_t`) |

**`0xffffffff` 와 `4294967295`**

- **값은 같은데 타입이 다르다.** 앞은 `unsigned int`, 뒤는 `long`.

**왜 갈리는가**

```text
  10진 리터럴 (접미사 없음)          16진/8진 리터럴 (접미사 없음)

    int                                int
     |  안 들어가면                     |  안 들어가면
     v                                 v
    long                             unsigned int   ★ 여기가 다르다
     |                                 |
     v                                 v
    long long                        long -> unsigned long -> ...
```

- 한 문장으로: **10진은 부호 있는 타입만 타고 올라가고, 16진·8진은 각 단계에서 부호 없는 쪽을 먼저 들른다.**
- `4294967295` 는 `int` 에 안 들어가니 다음은 `long`(8바이트라 들어간다).
- `0xffffffff` 는 `int` 에 안 들어가니 다음은 **`unsigned int`**(4바이트, 들어간다).

**다음 주제로 어떻게 이어지나**

```c
if (x < 0xffffffff) { ... }   /* x 가 int 면 x 가 unsigned 로 끌려간다 */
```

- `0xffffffff` 가 `unsigned int` 라서 **비교가 통째로 부호 없는 쪽으로 간다.**\
  `x` 가 `-1` 이면 `4294967295` 로 읽혀 조건이 뒤집힌다.
- 같은 마스크를 `4294967295` 로 쓰면 `long` 이라 `x` 가 `long` 으로 승격되어 **부호가 보존된다.**\
  **같은 값을 다르게 적었을 뿐인데 의미가 갈린다.**
- 전모는 [`03-integer-promotion-and-usual-arithmetic-conversions/`](../03-integer-promotion-and-usual-arithmetic-conversions/).

### 5. `sizeof(int) - 5`

**출력**

```text
sizeof(boom()) = 4  <- 위에 boom 이 안 찍혔으면 sizeof 는 피연산자를 평가하지 않은 것
sizeof 의 결과 타입은 부호 없음: (sizeof(int) - 5) = 18446744073709551615
```

**무엇이 찍히나**

- **`18446744073709551615`** 다. `-1` 이 아니다.
- `4 - 5` 가 부호 없는 64비트 산술로 계산되어 `ULONG_MAX` 가 됐다.

**`sizeof` 의 결과 타입**

- **`size_t`** 이고, 이 환경에서는 `unsigned long`(8바이트)이다.
- **부호가 없다는 것이 핵심**이다. 타입이 `size_t` 라는 것은 표준이 정한 것이고, 그게 몇 바이트인지는 구현 정의다.

**`sizeof(boom())` 이 `boom` 을 실행하는가**

- **안 한다.** 위 출력에서 `boom` 이 부르는 `puts` 가 **한 글자도 안 찍혔다.**
- `sizeof` 는 피연산자의 **타입만** 보고 크기를 낸다 — 컴파일 시간에 끝난다.
- 예외는 VLA 다. `sizeof` 가 런타임에 계산되는 유일한 자리이고, 정본은 [목록의 **08번 주제**](../08-sizeof-alignment-and-offsetof/)·[목록의 **18번 주제**](../18-variable-length-arrays-vla/).

### 6. `int_fast16_t` 는 몇 바이트인가

**출력**

```text
int8_t=1 int16_t=2 int32_t=4 int64_t=8
int_fast8_t=1 int_fast16_t=8 int_fast32_t=8 int_fast64_t=8
int_least8_t=1 int_least16_t=2 int_least32_t=4 int_least64_t=8
```

`gcc -E` 로 typedef 실체도 확인했다.

```text
typedef signed char int_fast8_t;
typedef long int int_fast16_t;
typedef long int int_fast32_t;
typedef long int int_fast64_t;
typedef __int32_t int32_t;              (-> signed int)
typedef __int_least32_t int_least32_t;  (-> signed int)
```

**네 값**

- `int_fast8_t` = **1** · `int_fast16_t` = **8** · `int_least16_t` = **2** · `int32_t` = **4**.

**`int_fast16_t` 가 8인 이유**

- **`fast` 는 「빠른 쪽」이지 「작은 쪽」이 아니다.**\
  x86-64 에서 64비트 레지스터 연산이 16비트보다 느리지 않고 부호·영 확장이 안 필요해 편하다 — **glibc 의 판단**이다.
- 판단이 가족 안에서도 갈린다 — `int_fast8_t` 만 1바이트다.
- 이름에 16이 들어 있다고 2바이트가 아니다. **보장은 「16비트 이상」뿐**이다.

**`int_fast16_t buf[1000000]`**

- **8,000,000 바이트**(약 8MB)다. 2MB 를 기대했다면 **4배**다.
- 실무 규칙: **배열·구조체 멤버에는 `int_least*` 나 고정폭**, `fast` 는 지역 변수·루프 인덱스용.

**없을 수도 있는 것**

- **`int32_t`** 다. `<stdint.h>` 의 **정확폭 타입은 선택 사항**이고, 그런 폭이 없는 환경에서는 이름 자체가 제공되지 않는다.
- `int_least32_t`·`int_fast32_t`·`intmax_t` 는 **언제나 제공된다.**

```text
  int32_t        정확히 32비트 · 패딩 없음 · 2의 보수   ★ 없을 수 있다
  int_least32_t  32비트 이상 중 가장 작은 것            언제나 있다
  int_fast32_t   32비트 이상 중 구현이 빠르다는 것       언제나 있다 · 크기 보장 없음
```

### 7. `_Bool b = 0.5;`

**출력**

```text
sizeof(_Bool) = 1
_Bool b = 5   -> 1
_Bool b = 0.5 -> 1
_Bool b = NULL-> 0
_Bool + _Bool 의 타입 폭: 4
```

**다섯 값**

- `b1` = **1** · `b2` = **1** · `b3` = **0** · `sizeof(_Bool)` = **1** · `sizeof(b1 + b1)` = **4**.

**`int i = 0.5;` 는 0 인데 `_Bool` 은 왜 1 인가**

```text
  double 0.5 를 담을 때

  -> int     : 소수부를 버린다(절단)        0.5 -> 0
  -> _Bool   : "0 과 같은가"만 본다          0.5 -> 0 이 아니다 -> 1
```

- `_Bool` 로의 변환은 **절단이 아니다.** 「0(또는 널 포인터)과 비교해서 같으면 0, 아니면 1」이다.
- 그래서 `0.5`·`-0.0001`·`1e-300` 이 전부 **1** 이 된다. 던져서 확인했다.

```text
0.0 -> 0   -0.0 -> 0   1e-300 -> 1   -0.0001 -> 1
```

- `-0.0` 도 **0** 이다 — 부동소수점의 음의 0 은 `0.0` 과 같다고 비교되기 때문이다\
  ([`04-floating-point-types-and-conversions/`](../04-floating-point-types-and-conversions/) 에서 다시 본다).
- 널 포인터도 0 이다 — `b3` 이 그 예다.

**`sizeof(b1 + b1)` 이 1 이 아닌 이유**

- **정수 승격**이다. `_Bool` 도 `int` 보다 좁으므로 연산 전에 `int` 로 올라간다.
- `+` 의 결과 타입은 `int`(4바이트)다.
- `_Bool` 이 승격 대상이라는 것은 [`03-integer-promotion-and-usual-arithmetic-conversions/`](../03-integer-promotion-and-usual-arithmetic-conversions/) 의 표에도 있다.

### 8. `bool` 은 언제부터 키워드인가

**출력**

```text
c17  헤더 없이 bool: ex2.c:2:18: error: unknown type name ‘bool’
    2 | int main(void) { bool b = true; printf("%d %zu\n", b, sizeof(bool)); return 0; }
c2x  헤더 없이 bool: 1 1
c17 + stdbool.h    : 1 1
```

**왜 그런가**

```text
  C99 ~ C17                             C23
  ---------                             ---
  _Bool          키워드                  _Bool         (남아 있다)
  bool           <stdbool.h> 의 매크로    bool          ★ 키워드
  true / false   <stdbool.h> 의 매크로    true / false  ★ 키워드 (타입은 bool)
```

- `-std=c17` 에서 `bool` 은 **키워드가 아니다** — `error: unknown type name ‘bool’`.
- `-std=c2x` 는 **헤더 없이 통과**한다.
- C17 에서 `<stdbool.h>` 가 하는 일은 `#define bool _Bool` · `#define true 1` · `#define false 0` 이다.\
  **매크로일 뿐**이라 `#undef bool` 도 된다.
- C23 에서 `<stdbool.h>` 는 **사라지지 않았다.** 호환을 위해 남아 있고, 포함해도 아무 해가 없다.
- 다만 **`true` 의 타입이 다르다.** `_Generic` 으로 찍어 확인했다.

```text
c17 + stdbool.h : true 의 타입: int
c2x 헤더 없이   : true 의 타입: _Bool
c2x + stdbool.h : true 의 타입: _Bool
```

- C17 의 `true` 는 **`int` 상수 `1`** 이고, C23 의 `true` 는 **`bool` 값**이다.\
  `-std=c2x` 에서는 `<stdbool.h>` 를 포함하든 말든 `_Bool` 로 같았다 — 헤더가 키워드를 덮지 않는다는 뜻이다.

### 9. 어느 타입을 고르나

| 상황 | 고를 것 | 왜 |
|---|---|---|
| 파일에 쓸 길이 필드 | **`uint32_t`/`int64_t`** | 폭이 계약이다. `long` 은 LP64/LLP64 에서 갈린다 |
| 배열 인덱스 | **`size_t`** | `sizeof` 의 타입이고 객체 크기를 담도록 되어 있다 |
| 바이트 버퍼 | **`unsigned char`** | `char` 는 부호가 구현 정의다 |
| 핫 루프 누적 변수 | **`int_fast32_t`** 또는 그냥 `int` | 구현이 빠른 폭을 고른다 |

**`char` 를 바이트 버퍼에 쓰면**

```c
char c = buf[i];       /* 0xC8 을 읽었다 */
if (c > 127) { ... }   /* 이 환경에서는 절대 안 탄다 — c 는 -56 */
int idx = c;           /* -56 을 인덱스로 쓰면 배열 밖 = UB */
```

- `char` 의 부호가 구현 정의라 **같은 코드가 x86 과 ARM 에서 다르게 돈다.**
- `<ctype.h>` 함수에 음수 `char` 를 넘기는 것도 같은 사고다 — 그쪽은 **UB** 다(정본은 목록의 **52번 주제**).
- 덧붙여 **바이트 값을 비교할 때 `> 127` 같은 조건 자체가 냄새**다. `unsigned char` 면 그냥 `>= 0x80` 이다.

**100만 개 배열에 `int_fast32_t`**

- 이 환경에서 **8MB** 다. `int32_t` 로 하면 4MB.
- 캐시 미스가 두 배로 는다 — 「빠르라고」 고른 타입이 배열에서는 느려지는 자리다.
- **`fast` 는 레지스터에 올라갈 값**을 위한 것이다.

### 10. 어느 층에 속하나

| 항목 | 층 | 근거 |
|---|---|---|
| `sizeof(char) == 1` | **표준이 정한 것** | 바이트의 정의 자체. 어느 환경에서도 1 |
| `sizeof(int) == 4` | **구현 정의** | 표준 보장은 「16비트 이상」. 이 환경이 4일 뿐 |
| `char` 가 부호 있는가 | **구현 정의** | `-funsigned-char` 로 뒤집혔고, `CHAR_MIN` 이 답을 준다 |
| `int` 가 `-32767\~32767` 을 담는다 | **표준이 정한 것** | 최소 범위 보장. 더 넓을 수는 있어도 좁을 수 없다 |
| `int32_t` 라는 이름이 존재하는가 | **구현 정의** | 정확폭 타입은 선택 사항. 있으면 문서화되고, 없으면 이름이 안 생긴다 |

```text
        표준이 정한 것        구현 정의           미명시            UB
        ------------------  ----------------  --------------  ---------------
 이 주제  sizeof(char)==1    sizeof(int)       (거의 없다)      (타입 선언에는
         최소 범위           char 의 부호                       없다 — 값이
         sizeof 의 결과 타입  int_fast* 의 폭                    넘치는 연산부터)
         'a' 의 타입         int32_t 의 존재
```

- 이 주제가 **가운데 두 열 사이의 선을 긋는 훈련**인 이유가 이 표다.
- **미명시와 UB 가 비어 있다** — 타입을 「선언」하는 것만으로는 UB 가 안 난다.\
  UB 는 [`03`](../03-integer-promotion-and-usual-arithmetic-conversions/) 부터 시작된다.

### 11. 서식 지정자를 틀리면

**출력**

```text
ex.c:8:14: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘size_t’ {aka ‘long unsigned int’} [-Wformat=]
ex.c:10:14: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘ptrdiff_t’ {aka ‘long int’} [-Wformat=]
--- 실행 ---
10
1
2
10 2
```

**경고가 나는 줄**

- **`%d`+`size_t`** 와 **`%d`+`ptrdiff_t`** 두 줄이다.
- **`%ld`+`int64_t` 는 경고가 없다.**

**경고가 안 나는 줄은 이식성이 있는가**

- **없다.** 이 환경에서 `int64_t` 가 **진짜 `long`** 이라 우연히 맞은 것이다.
- LLP64 윈도우에서는 `int64_t` 가 `long long` 이라 **같은 줄이 경고가 된다.**
- **「경고가 없다」는 이식성의 근거가 아니다.** 이 컴파일러가 이 플랫폼 타입으로 검사했을 뿐이다.

**경고가 난 줄의 출력**

- **`10` 과 `2` — 둘 다 맞는 값이 나왔다.**
- x86-64 SysV ABI 에서 작은 정수는 같은 레지스터의 하위 절반에 들어가 있어 `%d` 가 우연히 읽어 낸 것이다.
- **이것이 이 갈래의 제1 규칙이 필요한 이유다** — 「안 터졌다」는 「안전하다」가 아니다.\
  값이 `2^32` 를 넘거나 다른 ABI 로 가면 바로 깨진다.

**올바른 지정자**

| 타입 | 지정자 | 헤더 |
|---|---|---|
| `size_t` | `%zu` | — |
| `ptrdiff_t` | `%td` | — |
| `intmax_t` | `%jd` | — |
| `int64_t` | `"%" PRId64` | `<inttypes.h>` |
| `uint32_t` | `"%" PRIu32` | `<inttypes.h>` |
| `long long` | `%lld` | — |

- 정본은 목록의 **47번 주제**.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 플래그로 돌렸나 |
|---|---|---|
| 타입 크기·`limits.h`·`stdint.h` 덤프 | 15개 `sizeof` · `limits.h` 매크로 전수 · `int_fast*`/`int_least*` 폭 | `-std=c17 -Wall -Wextra` |
| `_Static_assert` 11줄 | 표준 최소 범위·크기 순서 전부 통과 · 일부러 깨서 에러 문구 확인 | `-std=c17 -Wall -Wextra` |
| `char` 부호 | `CHAR_MIN`·`(char)200`·`__CHAR_UNSIGNED__` — **플래그로 뒤집어 봄** | `-std=c17` · `-fsigned-char` · `-funsigned-char` |
| `_Generic` 리터럴 타입표 | 15개 리터럴·식의 실제 타입 | `-std=c17 -Wall -Wextra` |
| `sizeof` 성질 | 결과가 `size_t`(부호 없음) · 피연산자 미평가 | `-std=c17 -Wall -Wextra` |
| `gcc -E` typedef 추출 | `int32_t`·`int_fast16_t`·`int_least32_t` 의 실체 · `INT_MAX` 가 16진 상수 | `-std=c17 -E` |
| `_Bool` 변환 | `5`·`0.5`·`NULL` → `1`/`1`/`0` · `b+b` 의 폭 4 | `-std=c17 -Wall -Wextra` |
| `bool` 키워드화 | C17 에서 `unknown type name` · **C2x 에서 헤더 없이 통과** · `<stdbool.h>` 로 C17 통과 | `-std=c17` · `-std=c2x` |
| 서식 지정자 | `%d`+`size_t`/`ptrdiff_t` 경고 · `%ld`+`int64_t` **무경고** · 출력은 셋 다 맞음 | `-std=c17 -Wall -Wextra` |

**구현 의존 항목** — 이 표의 값 중 다음은 **이 환경(x86-64 Linux · LP64 · glibc · gcc 13.3.0)에서만** 그렇다.

- `sizeof` 값 전부(`char` 의 1 만 예외) · `limits.h` 의 모든 수치.
- `char` 가 부호 있는 것 — **같은 gcc 에서 플래그로 뒤집힌다.**
- `int_fast16_t`/`int_fast32_t` 가 8바이트인 것 — **glibc 의 선택**이고 다른 libc 에서 다를 수 있다.
- `int64_t` 가 `long` 인 것(윈도우는 `long long`) → `%ld` 무경고도 여기서만.
- `%d` 에 `size_t` 를 줘도 값이 맞게 나온 것 — **ABI 우연**이다.

**안 돌려 본 것** (환경이 없어서)

- `CHAR_BIT != 8` 인 환경 · `int32_t` 가 없는 환경 · 16비트 `int` 환경 · ARM 의 `char` 부호.
- C23 `static_assert` 의 메시지 생략 · `_BitInt(N)`.

**버전이 올랐을 때 다시 돌려야 하는 것**

- `-std=c23` 이 생기면 8번(`bool`)과 「더 들어가면」의 C23 항목을 다시 던진다.
- glibc 가 올라가면 `int_fast*` 의 폭을 다시 찍는다 — **보장이 아니라 그 libc 의 선택**이다.
