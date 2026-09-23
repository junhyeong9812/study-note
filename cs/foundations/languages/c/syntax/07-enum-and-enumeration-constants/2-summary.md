# c/syntax/07 — `enum` 과 열거 상수: 이름이 붙은 정수일 뿐이다 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — Enumerations (C)](https://en.cppreference.com/w/c/language/enum) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html) · [GCC 13 Code Gen Options — `-fshort-enums`](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Code-Gen-Options.html)
> **실행 검증** — 이 문서의 모든 출력·경고·에러는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> **표준 버전이 갈리는 자리는 `-std=c17`·`-std=c2x` 로 나눠 돌렸고, `-pedantic` 유무까지 나눠 세었다.**\
> `gdb`·`clang 18.1.3` 을 쓴 자리는 그 자리에 밝혔다. 기본 플래그는 `-std=c17 -Wall -Wextra`.
> **버전** — `enum` 은 C89 부터 있다. **열거 상수가 `int` 범위를 넘어도 되는 것**과\
> **고정 기반 타입**(`enum E : unsigned char`)은 **C23부터**다.\
> ★ **이 gcc 에 `-std=c23` 은 없다** — `-std=c2x` 뿐이고 그때 `__STDC_VERSION__` 이 `202000L` 이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> **경계** — 「정수 승격·부호 비교」의 정본은 [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)다.\
> 여기는 **`enum` 이 그 규칙에 어떻게 걸리나**까지만 쓴다. 「`switch` 문법」은 [목록의 **12번 주제**](../12-control-flow-and-switch/)가 정본이다.

## 한눈에 — 쉽게 말하면

**`enum` 은 이름이 붙은 정수 상수 묶음이다. 「그 값들만 들어간다」는 보장은 어디에도 없다.**

다른 언어의 열거형을 생각하고 오면 **세 번 놀란다** —\
값을 아무거나 넣어도 되고, 크기가 안 정해져 있고, **부호가 있는지도 안 정해져 있다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 좌석에 **번호 대신 이름표**를 붙인다 | `enum Color { RED, GREEN, BLUE };` — 0·1·2 에 이름을 붙인 것 |
| 이름표는 **좌석을 지키지 않는다** | `enum Color c = 999;` 가 **경고 없이** 통과한다 |
| 이름표 자체는 **종이 한 장**(`int`) | 열거 상수의 타입은 C17 에서 **`int`** 다 |
| 좌석의 **크기**는 극장이 정한다 | `sizeof(enum E)` 는 **구현 정의** |
| ★ 좌석에 **음수 표가 없으면** 매표소가 음수를 아예 안 판다 | 음수 열거자가 없으면 gcc 는 **`unsigned int`** 를 고른다 |
| **C23 부터는 좌석 규격을 지정**할 수 있다 | `enum E : unsigned char` |

```text
   enum Color { RED, GREEN, BLUE };

   내가 기대한 것                     C 가 준 것
   +------------------------+        +------------------------+
   | RED/GREEN/BLUE 중 하나  |        | ★ 그냥 정수다           |
   | 다른 값은 못 넣는다      |        | 999 도 들어간다         |
   | 크기는 정해져 있다       |        | 크기는 구현 정의        |
   | 당연히 부호가 있다       |        | ★ 여기선 unsigned 다    |
   +------------------------+        +------------------------+
```

- 그래서 `enum` 은 타입이라기보다 「**`#define` 묶음에 이름과 디버거 지원을 얹은 것**」에 가깝다.
- 대신 얻는 것이 셋 있다 — **`switch` 경고**, **디버거 표시**, **정수 상수식**.

> **열거 상수(enumeration constant)** — `enum` 의 중괄호 안에 적은 이름. `RED`·`GREEN`.\
> 예: C17 에서 이들의 타입은 **`int`** 다. `enum Color` 가 아니다.

> **열거 타입(enumerated type)** — `enum Color` 자체. 어떤 정수 타입과 **호환**되는데,\
> 예: 어느 타입과 호환되는지는 **구현 정의**다. 이 gcc 는 값이 전부 음수가 아니면 `unsigned int` 를 골랐다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `enum` 에서 **타입이 셋**(상수·열거 타입·연산 결과)인데 각각 무엇이고 왜 갈리는가.
2. `sizeof(enum E)` 와 **부호**는 누가 정하는가 — 값 범위를 바꾸면 달라지는가.
3. C23 이 바꾼 것은 정확히 무엇이고, **이 컴파일러에서 확인되는가.**

## 동작 방식

### (1) ★ 타입이 셋이다 — 상수 · 열거 타입 · 연산 결과

**언제 쓰나** — `enum` 값을 비교하거나 빼기 전에 언제나.

```text
--- 열거 상수 자체의 타입 ---
S_A            -> int
B_A (INT_MAX)  -> int
H_A (INT_MAX+1)-> unsigned int
N_A (-1)       -> int
--- 열거 타입 변수의 타입 ---
enum Small 변수 -> unsigned int
enum Huge  변수 -> unsigned int
enum Neg   변수 -> int
enum Tiny  변수 -> unsigned int
```

```text
   enum Color { RED, GREEN, BLUE };
   enum Color r = RED;

   ① 열거 상수 RED          -> ★ int          (C17 의 규칙)
   ② 변수 r 의 타입          -> ★ unsigned int (이 구현의 선택)
   ③ 식 r - 1 의 타입        -> ★ unsigned int (승격해도 unsigned 가 이긴다)
       식 RED - 1 의 타입     -> int

   -> 같은 "빼기 1" 인데 ①로 쓰면 int, ②로 쓰면 unsigned
```

실제로 물어봤다.

```text
변수 r 의 타입          -> unsigned int
식 r - 1 의 타입        -> unsigned int
상수 RED - 1 의 타입    -> int
r - 1 을 %d 로 : -1
r - 1 을 %u 로 : 4294967295
r - 1 < 0 인가  : 0
RED - 1 < 0 인가: 1
```

그림 해설 (한 단계씩):

- ★★ **`r - 1 < 0` 은 거짓이고 `RED - 1 < 0` 은 참이다.** 같은 모양의 식인데 답이 반대다.
- `%d` 로 찍으면 **둘 다 `-1`** 로 보인다. `%u` 로 찍어야 `4294967295` 가 드러난다.\
  **화면만 보면 구별이 안 된다** — [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)의 `-1 < 1u` 와 같은 사고다.
- gcc 가 `-Wextra` 에서 잡아 준다.

```text
arith.c:11:44: warning: comparison of unsigned expression in ‘< 0’ is always false [-Wtype-limits]
```

```text
[] 0
[-Wall] 0
[-Wextra] 1
[-Wall -Wextra] 1
```

- ★ **`-Wall` 은 0건, `-Wextra` 가 1건**이다. [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)의 `-Wsign-compare` 와 같은 자리다.
- **clang 18.1.3 은 `-Wall -Wextra` 로 0건**이었다(같은 값을 냈다). 컴파일러에 따라 안 보인다.

비용 — 없다. `enum` 값을 뺄 때 **`(int)` 로 먼저 올리면** 된다.

### (2) `sizeof(enum E)` 와 부호는 누가 정하나

**언제 쓰나** — `enum` 을 구조체 멤버나 파일 형식에 넣을 때.

값 범위를 다섯 벌로 바꿔 가며 쟀다.

```text
--- sizeof ---
sizeof(enum Small)=4 Neg=4 Big=4 Huge=4 Tiny=4  (int=4)
```

- ★ **값 범위를 바꿔도 전부 4다.** `enum Tiny { 0, 255 }` 도 4다.
- 「작은 값만 쓰면 작아지겠지」는 **이 컴파일러에서 재현되지 않는다.**

그런데 **플래그 하나로 바뀐다.**

```text
--- sizeof ---
sizeof(enum Small)=1 Neg=1 Big=4 Huge=4 Tiny=1  (int=4)
```

```text
   기본                              -fshort-enums
   +--------------------------+     +--------------------------+
   | 전부 4 (int 폭)           |     | Small 1  Neg  1  Tiny 1  |
   |                          |     | Big   4  Huge 4          |
   +--------------------------+     +--------------------------+
        범위와 무관                     ★ 범위에 맞춰 줄인다

   -> "구현 정의" 가 말뿐이 아니라는 증거. 같은 컴파일러도 답이 둘이다.
```

그림 해설 (한 단계씩):

- **`-fshort-enums` 는 ABI 를 바꾼다.** 이 플래그로 빌드한 라이브러리와 아닌 라이브러리를 링크하면 조용히 깨진다.\
  (ARM 의 어떤 ABI 는 이쪽이 기본이다 — **이 머신에서는 확인 못 했다.**)
- 부호도 구현 정의다 — (1)에서 본 대로 **음수 열거자가 있으면 `int`, 없으면 `unsigned int`** 를 골랐다.
- **`sizeof` 를 재고 부호를 물어보는 것**이 유일한 확인 방법이다. 외우면 안 된다.

비용 — 없다. 다만 **파일·네트워크 형식에 `enum` 을 직접 쓰면 안 되는 이유**가 이것이다.

### (3) 값 규칙 — 이어붙기·중복·범위 밖

**언제 쓰나** — 열거자에 값을 직접 지정할 때.

```c
enum E { A, B = 10, C, D = 10, E_ = -1, F };   /* C, F 는 앞값+1 */
```

```text
A=0 B=10 C=11 D=10 E_=-1 F=0
B == D ? 1
```

```text
   A      값 없음 -> 0 (첫 번째는 0)
   B = 10         -> 10
   C      값 없음 -> ★ 앞값 + 1 = 11
   D = 10         -> 10   ★ B 와 같은 값 — 허용된다
   E_ = -1        -> -1
   F      값 없음 -> ★ -1 + 1 = 0   ★ A 와 같은 값
```

- **중복이 허용된다.** `B == D` 가 참이고 경고는 **0건**(`-pedantic` 까지 켜도 0건)이다.
- 「값을 안 쓰면 이어진다」는 **직전 값 + 1** 이지 「순서 번호」가 아니다.
- 그래서 **음수를 중간에 넣으면 그 뒤가 앞으로 되감긴다**(`F` 가 0이 됐다).

범위 밖 값을 넣어도 막지 않는다.

```text
c = 999, d = -5
sizeof(c) = 4
c+1 = 1000
```

```text
[] 0
[-Wall] 0
[-Wextra] 0
[-Wall -Wextra] 0
[-Wall -Wextra -Wconversion] 0
[-Wall -Wextra -pedantic] 0
```

- ★ **여섯 플래그 조합에서 전부 0건**이다. gcc 는 아무 말도 안 한다.
- **clang 에는 검사가 있다.**

```text
range.c:4:20: warning: integer constant not in range of enumerated type 'enum Color' [-Wassign-enum]
```

  단 **`-Wall -Wextra` 로는 안 나오고**(0건) `-Wassign-enum` 을 **명시**해야 나온다.\
  그리고 **gcc 에는 그 플래그가 아예 없다** — `gcc: error: unrecognized command-line option ‘-Wassign-enum’`.

비용 — 없다. **`enum` 값을 외부 입력으로 받으면 직접 검사해야 한다**는 뜻이다.

### (4) `switch` 가 주는 것 — `enum` 의 진짜 이득 하나

**언제 쓰나** — `enum` 을 쓸지 `#define` 을 쓸지 고를 때.

```c
switch (c) {
case RED:   return "red";
case GREEN: return "green";
}                                    /* ★ BLUE 가 빠졌다 */
```

```text
sw.c:4:5: warning: enumeration value ‘BLUE’ not handled in switch [-Wswitch]
red green ?
```

```text
[] 0
[-Wall] 1
[-Wextra] 0
[-Wall -Wextra] 1
[-Wswitch] 1
[-Wall -Wswitch-enum] 1
```

`default:` 를 넣으면 갈린다.

```text
[-Wall] 0
[-Wall -Wswitch-enum] 1
```

```text
sw2.c:4:5: warning: enumeration value ‘BLUE’ not handled in switch [-Wswitch-enum]
```

```text
   -Wswitch        (-Wall 에 포함)
     default: 가 있으면 ★ 침묵한다
     -> "나머지는 default 가 받는다" 는 뜻으로 읽는다

   -Wswitch-enum   (따로 켠다)
     default: 가 있어도 ★ 말한다
     -> "열거자를 전부 적어라" 는 뜻으로 읽는다
```

그림 해설 (한 단계씩):

- **`-Wswitch` 는 `-Wall` 에 있다.** (1)의 `-Wtype-limits` 가 `-Wextra` 에 있던 것과 다르다 —\
  **플래그마다 소속이 다르므로 세어서 확인해야 한다.**
- 열거자를 늘렸을 때 **처리 안 한 자리를 컴파일러가 찾아 주는 것**이 `enum` 의 가장 큰 실익이다.
- 그러려면 **`default:` 를 안 쓰거나 `-Wswitch-enum` 을 켜야 한다.** `default:` 는 그 이득을 끈다.

비용 — 열거자를 늘릴 때마다 `switch` 를 고쳐야 한다. **그게 목적이다.**

### (5) 익명 `enum` 대 `#define` — 디버거로 갈린다

**언제 쓰나** — 정수 상수가 필요할 때.

```c
enum { BUFSZ = 256, MAXN = 10 };     /* 익명 enum — 타입 있는 정수 상수 */
#define DBUFSZ 256
```

```text
sizeof a=256 b=256
BUFSZ 의 타입 -> int
sizeof(BUFSZ)=4
```

둘 다 **정수 상수식**이라 배열 크기·`case` 라벨·비트필드 폭·`_Static_assert` 에 쓸 수 있다.

```text
N=4 sizeof arr=16 비트필드 폭 4
```

갈리는 곳은 **디버거**다. `gdb` 로 물어봤다.

```text
Breakpoint 1, main () at dbg.c:7
7	    printf("%d %d\n", (int)c, d);
$1 = GREEN
$2 = 0
$3 = RED
No symbol "DRED" in current context.
```

```text
   enum                              #define
   +--------------------------+     +--------------------------+
   | (gdb) print c  -> GREEN  |     | (gdb) print d  -> 0      |
   | (gdb) print RED -> RED   |     | (gdb) print DRED         |
   |                          |     |   -> ★ No symbol         |
   +--------------------------+     +--------------------------+
     ★ 값이 이름으로 보인다            전처리기가 이미 지워 버렸다
```

그림 해설 (한 단계씩):

- **`print c` 가 `GREEN` 이라고 답한다.** 값이 아니라 이름이다.
- `print DRED` 는 「**그런 심볼 없음**」이다 — 전처리기 단계에서 사라져 디버그 정보에 안 남는다.
- **스코프도 다르다.** `enum` 상수는 블록 스코프를 따르고 `#define` 은 파일 끝까지 간다.
- 반대로 `#define` 만 되는 것도 있다 — **`#if` 조건에 쓰는 것**(전처리기는 `enum` 을 모른다).\
  이 문서에서는 **던져 보지 않았다.**

비용 — 없다. **정수 상수에는 익명 `enum` 이 기본**이다.

### (6) 비트 플래그로 쓸 때 생기는 일

**언제 쓰나** — `P_READ | P_WRITE` 같은 플래그 묶음을 만들 때.

```text
P_READ | P_WRITE 의 타입 -> int
enum Perm 변수의 타입     -> unsigned int
both = 3, 이름은 없다
show(both) = 다른 것
P_READ|P_WRITE 가 열거 상수 중 하나인가? 0
```

```text
   enum Perm { P_READ = 1, P_WRITE = 2, P_EXEC = 4 };

   P_READ | P_WRITE
      = int(1) | int(2)      <- 상수는 int 다
      = int(3)               <- ★ 결과가 enum Perm 이 아니다
      -> enum Perm 에 넣을 수는 있다 (경고 0건)
      -> 그런데 3 은 ★ 어떤 열거자와도 같지 않다
         switch 의 case 로 못 받고
         디버거도 이름을 못 붙인다
```

```text
[-Wall -Wextra] 0
[-Wall -Wextra -Wconversion] 0
```

그림 해설 (한 단계씩):

- **`|` 의 결과 타입은 `int`** 다. 열거 타입이 아니다.
- 그것을 `enum Perm` 변수에 넣어도 **경고가 0건**이다(clang 의 `-Wassign-enum` 은 말한다 —\
  `integer constant not in range of enumerated type 'enum Perm'`).
- **`switch` 의 `case` 로 받을 수 없다.** `3` 이라는 열거자가 없기 때문이다.
- 그래서 비트 플래그는 관례가 둘이다.
  - **열거자에 조합값도 넣는다** — `P_RW = 3` 처럼. `switch` 와 디버거가 살아난다.
  - **타입은 `unsigned` 로 두고 값만 `enum` 으로 만든다** — `unsigned flags = P_READ | P_WRITE;`.

비용 — 없다. 「**플래그 묶음은 열거 타입이 아니다**」를 인정하면 된다.

### (7) C23 이 바꾼 것 — 던져서 확인했다

**언제 쓰나** — 「C23 에서 `enum` 이 바뀌었다」는 말을 들었을 때.

**바뀐 것 ①** — 열거자가 `int` 범위를 넘어도 된다.

```text
huge.c:1:19: warning: ISO C restricts enumerator values to range of ‘int’ before C2X [-Wpedantic]
    1 | enum Huge { H_A = 2147483648u };
      |                   ^~~~~~~~~~~
```

```text
[] c17: 0
[-Wall] c17: 0
[-Wextra] c17: 0
[-Wall -Wextra] c17: 0
[-Wall -Wextra -pedantic] c17: 1
[-Wall -Wextra -pedantic] c2x: 0
```

- ★ **gcc 의 문구가 「before C2X」라고 직접 말해 준다.** 기억이 아니라 **컴파일러가 알려 준 변화**다.
- `-std=c2x -pedantic` 에서 **0건**이 된다.

**바뀐 것 ②** — 고정 기반 타입(`enum E : unsigned char`).

```c
enum Byte : unsigned char { B_ZERO = 0, B_MAX = 255 };
```

```text
__STDC_VERSION__ = 202000L
sizeof(enum Byte) = 1
변수의 타입   -> unsigned char
상수 B_MAX 의 타입 -> unsigned char
B_MAX = 255
```

```text
   C17 의 enum                       C23 의 enum E : unsigned char
   +--------------------------+     +--------------------------+
   | 상수의 타입 = int         |     | 상수의 타입 = ★ unsigned char|
   | 크기 = 구현 정의          |     | 크기 = ★ 1 (내가 정한다)   |
   | 부호 = 구현 정의          |     | 부호 = ★ 내가 정한다       |
   +--------------------------+     +--------------------------+
        (2)의 불확실성 셋이 한꺼번에 사라진다
```

그림 해설 (한 단계씩):

- **상수의 타입까지 바뀐다.** `B_MAX` 가 `int` 가 아니라 `unsigned char` 다 — (1)의 「상수는 `int`」가 C23 에서 무너지는 자리다.
- `sizeof` 가 **1** 이다. (2)의 구현 정의가 **내 손으로 넘어온다.**
- ★★ **그런데 `-std=c17` 로 컴파일해도 그냥 된다.**

```text
__STDC_VERSION__ = 201710L
sizeof(enum Byte) = 1
변수의 타입   -> unsigned char
```

```text
fixed.c:2:6: warning: ISO C does not support specifying ‘enum’ underlying types before C2X [-Wpedantic]
```

- **`-std=c17` 만으로는 C17 코드가 되지 않는다.** gcc 는 확장을 기본으로 켜 둔다.\
  **`-pedantic` 을 붙여야** 표준 밖이라는 말을 듣는다. `-std=c89 -pedantic` 에서도 같은 문구가 나온다.
- ★ **`-std=` 는 「이 표준으로 컴파일해라」이지 「이 표준 밖을 막아라」가 아니다.**

비용 — 이식성. C23 기능은 **다른 컴파일러에서 안 될 수 있다.**

## 문법 — 형태와 규칙

### 형태

```c
enum Color { RED, GREEN, BLUE };            /* 태그 있음 */
enum Color c = RED;

typedef enum { RED, GREEN } Color;          /* typedef 와 함께 (06번 주제) */

enum { BUFSZ = 256 };                       /* 익명 — 정수 상수를 만든다 */

enum E { A = 1, B = 2, C };                 /* 값 지정 — C 는 3 */
enum F { X = 10, Y = 10 };                  /* 중복 허용 */

enum Byte : unsigned char { Z = 0 };        /* ★ C23 — 고정 기반 타입 */

enum Color;                                  /* 불완전 열거 타입 — C23 부터만 */
```

### 금지 사례 — 걸리는 것과 안 걸리는 것

```c
/* (1) 범위 밖 값 -> ★ gcc 는 안 걸린다 */
enum Color c = 999;

/* (2) 비트 OR 결과를 열거 타입에 -> ★ 안 걸린다 */
enum Perm p = P_READ | P_WRITE;

/* (3) 음수가 없는 enum 에 -1 을 넣고 < 0 -> ★ 언제나 거짓 */
enum Color c = (enum Color)-1;  if (c < 0) { }

/* (4) switch 에서 열거자를 빠뜨린다 -> -Wall 이 걸린다 */
switch (c) { case RED: ...; case GREEN: ...; }

/* (5) enum 을 파일·네트워크 형식에 직접 쓴다 -> 크기·부호가 구현 정의 */
fwrite(&c, sizeof c, 1, fp);
```

- (1)\~(3)은 **컴파일러가 안 막는다.** (4)만 `-Wall` 이 잡는다.
- (3)을 gcc 는 **`-Wextra`** 에서 「always false」로 잡아 준다.

### 규칙 불릿

- **열거 상수의 타입은 C17 에서 `int`** 다. `enum Color` 가 아니다.
- **열거 타입 자체가 어느 정수 타입과 호환되는지는 구현 정의**다 — 이 gcc 는 **음수 열거자가 없으면 `unsigned int`** 를 골랐다.
- **`sizeof(enum E)` 는 구현 정의**다. 이 gcc 는 기본이 4이고 `-fshort-enums` 면 1까지 줄어든다.
- 값을 안 쓰면 **직전 값 + 1**. 첫 열거자는 0. **중복이 허용된다.**
- **범위 밖 값을 넣어도 gcc 는 경고하지 않는다.** clang 의 `-Wassign-enum` 만 말한다.
- **`|`·`+` 의 결과는 열거 타입이 아니다** — 정수 승격을 거친 정수다.
- **`-Wswitch` 는 `-Wall` 에 있고 `default:` 가 있으면 침묵**한다. `-Wswitch-enum` 은 침묵하지 않는다.
- **C23부터** 열거자가 `int` 범위를 넘어도 되고, `enum E : 타입` 으로 기반 타입을 지정할 수 있다.\
  그때는 **상수의 타입도 그 기반 타입**이 된다.

## 어디서 틀리나

### 1. 「열거형이니까 그 값들만 들어간다」

- `enum Color c = 999;` 가 **여섯 플래그 조합에서 전부 0건**으로 통과한다. 값도 999 그대로 들어간다.
- 외부 입력(파일·네트워크·사용자)을 `enum` 에 넣을 때는 **직접 검사**해야 한다.
- clang 의 `-Wassign-enum` 을 교차로 돌려 보는 것이 지금 쓸 수 있는 유일한 자동 검사다.

### 2. `enum` 값을 빼거나 `< 0` 으로 검사한다 ★★

```text
r - 1 을 %d 로 : -1
r - 1 을 %u 로 : 4294967295
r - 1 < 0 인가  : 0
RED - 1 < 0 인가: 1
```

- **변수로 쓰면 `unsigned`, 상수로 쓰면 `int`** 라 같은 식이 다른 답을 낸다.
- `%d` 로 찍으면 **둘 다 `-1`** 로 보인다. **화면으로는 구별이 안 된다.**
- `-Wextra` 의 `-Wtype-limits` 가 잡아 주지만 **clang 은 0건**이다.
- 막는 법: **`(int)` 로 먼저 올린다.** `((int)r - 1) < 0`.

### 3. `sizeof(enum E)` 를 외운다

- 값 범위를 바꿔도 **이 gcc 에서는 전부 4**였다. 「작은 값이면 작아진다」가 **재현되지 않는다.**
- 그런데 `-fshort-enums` 를 붙이면 **1 로 줄어든다.** 같은 컴파일러가 답을 둘 갖고 있다.
- **파일·네트워크 형식에 `enum` 을 직접 쓰지 않는다.** 고정폭 정수로 옮긴다([02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)).

### 4. `default:` 를 습관적으로 넣는다

- `default:` 가 있으면 **`-Wswitch` 가 침묵한다.** 열거자를 늘려도 아무도 말해 주지 않는다.
- `enum` 을 쓰는 가장 큰 이유 하나를 스스로 끈 것이다.
- 「있을 수 없는 값」을 처리해야 하면 **`switch` 밖에서** 하거나 `-Wswitch-enum` 을 켠다.

### 5. 비트 플래그를 열거 타입으로 다룬다

- `P_READ | P_WRITE` 는 **`int`** 이고 그 값 `3` 은 **어떤 열거자도 아니다.**
- `switch` 로 못 받고 디버거가 이름을 못 붙인다.
- 조합값을 쓰려면 **열거자에 그 조합도 적어 넣는다.**

### 6. `-std=c17` 이 C17 을 강제한다고 믿는다 ★

- `enum Byte : unsigned char` 가 **`-std=c17` 에서 경고 없이 컴파일된다.**
- `-pedantic` 을 붙여야 `ISO C does not support ... before C2X` 가 나온다.
- 이식성을 확인하려면 **`-pedantic`(또는 `-pedantic-errors`)까지** 붙인다.

## 구현 세부사항 대 언어 보장

C 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★ **이 주제는 「구현 정의」 칸이 제일 두껍다.** `enum` 의 크기·부호·호환 타입이 전부 거기에 있다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | **열거 상수의 타입이 `int`**(C17) · 값을 안 쓰면 **직전 값 + 1** · 첫 열거자는 0 · **중복 허용** · 열거 상수가 **정수 상수식**인 것 · `\|`·`+` 의 결과가 열거 타입이 아닌 것 · 열거 상수가 **블록 스코프**를 따르는 것 | `_Generic` · 값 출력 · 배열 크기·`case`·비트필드 폭·`_Static_assert` 에 사용 | — |
| **조건부 표준** | 매크로가 정의될 때만 | **해당 없음**(이 주제에 조건부 보장은 없다) | — | — |
| **구현 정의** | 문서화 의무가 있다 | **`sizeof(enum E)`**(여기선 4, `-fshort-enums` 면 1) · **열거 타입이 호환되는 정수 타입**(여기선 음수가 없으면 `unsigned int`) · 그래서 **`enum` 값의 부호** · `int` 범위를 넘는 열거자를 받아 주는지(C17 에서는 확장) | `sizeof` 5벌 · `_Generic` · `-fshort-enums` 로 **뒤집어 봄** · `-pedantic` 으로 **확장임을 확인** | **`-Wall -Wextra` 가 한 건도 말하지 않는다**(`-pedantic` 이 있어야 한다) |
| **미명시** | 몇 가지 중 하나 | **해당 없음** | — | — |
| **UB** | 아무 일이나 | ★ **범위 밖 값을 넣는 것은 UB 가 아니다** — 열거 타입은 호환되는 정수 타입의 범위를 갖고, 999 는 그 안이다. 이 주제에서 만들 수 있는 UB 는 **열거 타입 자체로는 없다** | `-O0`·`-O2`·ubsan 에서 999 가 그대로 나옴 | — |

### 「구현 정의」를 뒤집어서 보이기

```text
--- sizeof ---
sizeof(enum Small)=4 Neg=4 Big=4 Huge=4 Tiny=4  (int=4)
```

```text
--- sizeof ---
sizeof(enum Small)=1 Neg=1 Big=4 Huge=4 Tiny=1  (int=4)
```

- **같은 소스·같은 컴파일러·플래그 하나 차이**로 크기가 4에서 1이 된다.
- 「구현 정의」가 **말뿐이 아니라는 실증**이다. `-funsigned-char` 로 `char` 의 부호를 뒤집은 것([05번 형제](../05-explicit-casts-and-pointer-conversions/))과 같은 수법이다.

### 「도구가 못 보는 것」을 층마다

| 사실 | gcc `-Wall -Wextra` | gcc `+-pedantic` | clang | 그 밖 |
|---|---|---|---|---|
| 범위 밖 대입(`c = 999`) | **0건** | **0건** | `-Wassign-enum` 으로 1건 | gcc 에는 그 플래그가 **없다** |
| `int` 범위 넘는 열거자 | 0건 | **1건**(「before C2X」) | — | — |
| C23 고정 기반 타입을 C17 에서 | 0건 | **1건** | — | — |
| `enum` 변수의 `< 0` | **1건**(`-Wextra`) | — | **0건** | `-Wall` 만으로는 0건 |
| `switch` 누락 | **1건**(`-Wall`) | — | — | `default:` 가 있으면 0건 |
| 중복 값 | 0건 | 0건 | — | 검사 자체가 없다 |
| `sizeof`·부호 | 0건 | 0건 | — | **찍어서만 안다** |

- ★ **sanitizer 가 등장하지 않는다.** 이 주제에는 UB 가 없어서 **런타임 도구가 볼 것이 없다.**\
  전부 **컴파일 타임 문제**이고, 그래서 **플래그를 세는 것**이 이 주제의 유일한 검사다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 안 고를 것 |
|---|---|---|
| 상태·종류가 몇 개로 닫혀 있다 | **`enum`**(+ `switch`, `default:` 없이) | `#define` 묶음 |
| 정수 상수 하나 | **익명 `enum`** | `#define`(디버거에 안 보인다) |
| `#if` 조건에 쓸 상수 | `#define` | `enum`(전처리기가 모른다) |
| 비트 플래그 | `unsigned` 변수 + `enum` 상수 | 열거 타입 변수 |
| 파일·네트워크 형식 | **고정폭 정수**(`uint8_t` 등) | `enum`(크기·부호가 구현 정의) |
| 구조체 멤버로 크기가 중요 | C23 `enum E : uint8_t` 또는 고정폭 정수 | 맨 `enum` |
| 외부 입력을 담는다 | `enum` + **직접 범위 검사** | `enum` 만 믿기 |
| `enum` 값 빼기·음수 검사 | `((int)e - 1)` | `e - 1`(여기선 `unsigned`) |

판단 규칙 두 줄.

- **`enum` 을 쓰는 값어치는 `switch` 경고와 디버거 표시**다. 둘을 안 쓸 거면 `#define` 과 다를 게 없다.
- **크기·부호가 중요한 자리에는 `enum` 을 안 쓴다.** 둘 다 구현 정의다.

## 핵심 문장

- **열거 상수는 `int` 이고, 열거 타입 변수는 이 gcc 에서 `unsigned int`** 다(음수 열거자가 없을 때).\
  그래서 **`RED - 1 < 0` 은 참이고 `r - 1 < 0` 은 거짓**이다 — `%d` 로는 둘 다 `-1` 로 보인다.
- **`enum Color c = 999;` 가 여섯 플래그 조합에서 0건**으로 통과한다. 「그 값들만 들어간다」는 보장이 없다.
- **`sizeof(enum E)` 는 값 범위를 바꿔도 전부 4**였고, **`-fshort-enums` 하나로 1이 됐다** — 구현 정의다.
- **`-Wswitch` 는 `-Wall` 에 있고 `default:` 가 있으면 침묵**한다. `enum` 의 가장 큰 이득을 습관이 끈다.
- **`|` 의 결과는 `int`** 라 비트 플래그 묶음은 열거 타입이 아니다 — `switch` 로 못 받는다.
- **C23 은 두 가지를 바꿨다** — `int` 범위 밖 열거자 허용과 **고정 기반 타입**. 후자에서는 **상수의 타입도** 바뀐다(`unsigned char`).
- ★ **`-std=c17` 은 C17 을 강제하지 않는다.** C23 문법이 그냥 컴파일된다 — **`-pedantic` 을 붙여야** 안다.

## 관련 자료

- [`../README.md`](../README.md) — C 문법·API 주제 목록(이 주제는 07번)
- [`02-basic-types-sizes-and-fixed-width-integers/`](../02-basic-types-sizes-and-fixed-width-integers/) — **그쪽은 「어느 정수 타입을 고르나」까지, 여기는 「`enum` 이 그중 무엇이 되나」부터.** 파일 형식에 고정폭 정수를 쓰는 근거가 거기
- [`03-integer-promotion-and-usual-arithmetic-conversions/`](../03-integer-promotion-and-usual-arithmetic-conversions/) — **`-1 < 1u` 가 거짓인 그 규칙**이 `enum` 변수에서 그대로 재현된다. 승격·부호 비교의 정본
- [`05-explicit-casts-and-pointer-conversions/`](../05-explicit-casts-and-pointer-conversions/) — `(int)e` 로 올려서 고치는 자리 · 「플래그 하나로 구현 정의를 뒤집어 보이는」 수법
- [`06-typedef-and-type-aliases/`](../06-typedef-and-type-aliases/) — `typedef enum { ... } Color;` 의 태그·이름 공간 규칙
- [목록의 **12번 주제**](../12-control-flow-and-switch/) (제어문과 `switch`) — `switch` 문법의 정본. 여기는 **`-Wswitch` 가 `enum` 에 주는 것**까지만
- 목록의 **24번 주제** (비트필드) — 열거 상수를 비트필드 폭으로 쓰는 자리
- 목록의 **41번 주제** (전처리기) — `#define` 쪽의 정본. `#if` 에 `enum` 을 못 쓰는 이유가 거기
- 목록의 **53번 주제** (`assert` 와 `static_assert`) — 열거 상수를 `_Static_assert` 로 못 박는 자리

## 용어 풀이

- **열거 상수(enumeration constant)** — `enum` 중괄호 안의 이름. C17 에서 타입은 **`int`**.
- **열거 타입(enumerated type)** — `enum Color` 자체. 어떤 정수 타입과 **호환**되며 어느 것인지는 **구현 정의**.
- **호환 타입(compatible type)** — 컴파일러가 같은 것으로 취급하는 타입. `_Generic` 으로 물어볼 수 있다.
- **정수 상수식(integer constant expression)** — 컴파일 시간에 값이 정해지는 정수 식. 배열 크기·`case`·비트필드 폭에 쓸 수 있다.
- **고정 기반 타입(fixed underlying type)** — C23 의 `enum E : 타입`. 크기·부호·상수의 타입을 한꺼번에 정한다.
- **`-fshort-enums`** — 열거 타입을 값 범위에 맞춰 줄이는 gcc 플래그. **ABI 를 바꾼다.**
- **`-Wswitch`** — `enum` 을 `switch` 할 때 빠진 열거자를 경고. `-Wall` 에 포함. **`default:` 가 있으면 침묵.**
- **`-Wswitch-enum`** — 같은 것을 `default:` 가 있어도 경고. 따로 켜야 한다.
- **`-Wtype-limits`** — 타입 범위상 언제나 참/거짓인 비교를 경고. **`-Wextra` 에 포함.**
- **`-Wassign-enum`** — 범위 밖 정수를 열거 타입에 넣는 것을 경고하는 **clang 전용** 플래그. gcc 에는 없다.

---

## 더 들어가면

- **불완전 열거 타입**(`enum Color;` 만 선언)은 **C23 부터** 쓸 수 있다.\
  C17 에서는 크기를 알 수 없어 금지였다. 이 문서에서는 **던져 보지 않았다.**

- **`enum` 에 `bool` 이나 `char` 를 기반 타입으로 줄 수 있는지**(C23)는 **확인하지 않았다.**\
  `unsigned char` 만 던져 봤고 되었다.

- ★ **`-fshort-enums` 는 ABI 를 바꾼다.** 이 플래그로 빌드한 오브젝트와 아닌 오브젝트를 링크하면\
  구조체 레이아웃이 어긋나 **조용히 깨진다.** 링커는 말해 주지 않는다.\
  이 문서에서는 **한쪽만 그 플래그로 빌드해 링크해 보지는 않았다.**

- **다른 언어의 열거형과 무엇이 다른가**는 이 갈래 밖이다. C# 의 `enum` 은 기반 타입을 지정할 수 있고\
  Rust 의 `enum` 은 값을 담는 대수적 타입이다. 논증은 [`../../../c-cpp-csharp.md`](../../../c-cpp-csharp.md) 쪽이다.

- **`enum` 이름을 문자열로 얻는 방법**은 C 에 없다. `X-매크로` 관용구로 이름 배열을 같이 만드는 것이 관례인데,\
  그것은 목록의 **43번 주제**(`#`·`##`)의 몫이다. 이 문서에서는 **안 다뤘다.**
