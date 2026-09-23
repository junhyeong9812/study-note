# c/syntax/11 — 비트 연산과 시프트: 자리를 다루는 법과 **넘으면 안 되는 선** — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — Bitwise arithmetic operators (C)](https://en.cppreference.com/w/c/language/operator_arithmetic) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html) · [Clang Diagnostic flags](https://clang.llvm.org/docs/DiagnosticsReference.html)
> **실행 검증** — 이 문서의 모든 출력·경고·sanitizer 진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과\
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★ UB 가 걸린 실험은 **`-O0`·`-O1`·`-O2`·`-O3`·`-Os` 다섯 벌**을 전부 돌렸다.
> **버전** — `& | ^ ~ << >>` 의 규칙은 **C89 이후 바뀐 적이 없다.** C23 이 2진 리터럴 `0b1011` 을 표준에 넣었다.\
> ★ **gcc 13.3.0 에는 `-std=c23` 이 없다**(`-std=c2x` 뿐). clang 18 은 둘 다 받는다 — 아래 (10)에서 실측한다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★ **경계** — 비트 트릭·응용(popcount·비트마스크 DP 등)은 [`algorithm/29-bit-manipulation/`](../../../../../algorithm/29-bit-manipulation/)이 정본이다.\
> 여기는 「**C 의 타입 규칙과 UB**」만 다룬다. 2진 표현·2의 보수 자체는 [`data-representation/`](../../../../data-representation/)이 정본이다.\
> 어떻게 **묶이나**는 [09번 형제](../09-operator-precedence-and-associativity/), 승격 규칙 자체는 [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)가 정본이다.
> 선행 — [02번 형제](../02-basic-types-sizes-and-fixed-width-integers/) · [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/).

## 한눈에 — 쉽게 말하면

**비트 연산은 「스위치가 32개 달린 배전반」을 다루는 것이다.**

집 배전반에 차단기가 32개 있다고 하자.\
「3번만 올려라」(`|=`) · 「3번만 내려라」(`&= ~`) · 「3번을 반대로」(`^=`) · 「3번이 올라가 있나」(`&`) —\
**한 번에 하나씩 손대는 네 가지 동작**이 전부다.

그런데 **배전반을 통째로 옆으로 미는 동작**(`<<` `>>`)이 하나 더 있고, **여기서 사고가 난다.**\
판이 32칸인데 **35칸을 밀면** 어떻게 되는지, **왼쪽 끝 칸(부호 비트)을 넘겨 밀면** 어떻게 되는지를\
C 는 **정해 주지 않는다.** 「모르는 값이 된다」가 아니라 「**그런 조작이 아니다**」라고 말한다.

| 비유 | 실체 | 층 |
|---|---|---|
| 차단기 하나만 올린다 | `flags \| MASK` | **표준** |
| 차단기 하나만 내린다 | `flags & ~MASK` | **표준** |
| 차단기 하나를 반대로 | `flags ^ MASK` | **표준** |
| 차단기가 올라가 있나 | `(flags & MASK) != 0` | **표준** |
| 판을 **판 크기보다 많이** 민다 | `v << 32`(32비트 `int`) | ★ **UB** |
| 판을 **뒤로** 민다 | `v << -1` | ★ **UB** |
| **왼쪽 끝 칸을 넘겨** 민다 | `1 << 31`·`(1<<30) << 2` | ★ **UB**(부호 있는 타입) |
| 음수를 오른쪽으로 민다 | `-1 >> 1` | ★ **구현 정의**(gcc·clang 은 산술 시프트) |
| 작은 타입을 뒤집는다 | `unsigned char c=0xFF; ~c` | **표준** — 단 **`int` 로 승격된 뒤** 뒤집힌다 |

```text
   unsigned char perm = 0000 0011      (읽기·쓰기 켜짐)

   perm |= (1u<<2)    설정      0000 0111
   perm &= ~(1u<<1)   해제      0000 0101
   perm ^= (1u<<0)    토글      0000 0100
   perm &  (1u<<2)    검사      0000 0100  -> 0 이 아니다 -> 켜져 있다

   ★ 네 동작 전부 "한 자리만" 건드린다. 나머지 자리는 그대로다.
```

- ★★ **이 주제의 본체는 UB 다.** 바로 앞 [10번 형제](../10-evaluation-order-and-sequence-points/)가 **「미명시」가 본체**였다면 여기는 정반대다 —\
  **UBSan 이 세 번 말을 한다.** 같은 도구가 10번에서는 한 줄도 안 냈다.
- ★ 그리고 **구현 정의**(`-1 >> 1`)와 **UB**(`1 << 31`)가 **한 주제 안에 나란히** 있다. 둘을 가르는 것이 이 문서다.

> **마스크(mask)** — 관심 있는 비트만 1 로 세운 값. 다른 자리를 가리는 **가면**이라는 뜻이다.\
> 예: `1u << 2` 는 `0000 0100` — 2번 자리만 보게 해 준다.

> **부호 비트(sign bit)** — 부호 있는 정수에서 **맨 왼쪽 비트.** 여기가 1 이면 음수다.\
> 예: 32비트 `int` 에서 `1 << 31` 은 이 자리를 켜려는 시도이고, 그래서 UB 다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★ **시프트에서 무엇이 UB 이고 무엇이 구현 정의인가** — 셋과 하나를 가를 수 있나.
2. ★★ **작은 타입에 비트 연산을 하면 무슨 일이 나는가** — `unsigned char` 를 뒤집었는데 왜 `-256` 인가.
3. ★ **도구가 어디까지 봐 주는가** — 경고는 상수만 보고, sanitizer 는 같은 자리를 한 번만 본다.

## 동작 방식

### (1) 네 연산자와 자리 그림 — 한 자리만 건드린다

**언제 쓰나** — 플래그·권한·상태를 한 정수에 모아 둘 때. C 에서 가장 흔한 비트 사용처다.

```text
===== 소스: ex.c (11-a) =====
#include <stdio.h>
static void bits(const char *tag, unsigned v) {
    printf("%-12s ", tag);
    for (int i = 7; i >= 0; i--) putchar((v >> i) & 1 ? '1' : '0');
    printf("   0x%02X  %u\n", v & 0xFFu, v & 0xFFu);
}
int main(void) {
    unsigned flags = 0x0Au;            /* 0000 1010 */
    unsigned MASK  = 0x04u;            /* 0000 0100 : 2번 비트(0부터) */
    bits("flags", flags);
    bits("MASK", MASK);
    bits("set  |=", flags | MASK);
    bits("clear &=~", flags & ~MASK);
    bits("toggle ^=", flags ^ MASK);
    printf("test (flags & MASK) != 0 : %d\n", (flags & MASK) != 0);
    printf("test (flags & 0x02) != 0 : %d\n", (flags & 0x02u) != 0);
    bits("~flags(low8)", ~flags);
    printf("~flags whole = %u  (0x%08X)\n", ~flags, ~flags);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
flags        00001010   0x0A  10
MASK         00000100   0x04  4
set  |=      00001110   0x0E  14
clear &=~    00001010   0x0A  10
toggle ^=    00001110   0x0E  14
test (flags & MASK) != 0 : 0
test (flags & 0x02) != 0 : 1
~flags(low8) 11110101   0xF5  245
~flags whole = 4294967285  (0xFFFFFFF5)
exit=0
```

```text
   자리         7 6 5 4 3 2 1 0
   flags        0 0 0 0 1 0 1 0      MASK = 2번 자리 하나
   MASK         0 0 0 0 0 1 0 0
                          |
        |  (OR)  -> 그 자리를 1 로      0 0 0 0 1 1 1 0   "없으면 켠다"
        &~ (AND NOT) -> 그 자리를 0 으로 0 0 0 0 1 0 1 0   "있으면 끈다" (원래 0 이라 그대로)
        ^  (XOR) -> 그 자리를 뒤집는다   0 0 0 0 1 1 1 0
        &  (AND) -> 그 자리만 남긴다     0 0 0 0 0 0 0 0   -> 0 -> 꺼져 있다
```

그림 해설 (한 단계씩):

- **`|` 는 「없으면 켠다」** — 이미 켜져 있으면 아무 일도 안 난다. **여러 번 해도 같다.**
- **`& ~` 는 「있으면 끈다」** — `~MASK` 가 그 자리만 0 이고 나머지가 전부 1 인 값이라 **다른 자리를 보존**한다.
- **`^` 는 「뒤집는다」** — 두 번 하면 원래대로 돌아온다. 그래서 토글이다.
- **`&` 는 「그 자리만 남긴다」** — 결과가 0 이냐 아니냐로 검사한다.\
  ★ **`(flags & MASK) != 0` 의 괄호는 필수다** — [09번 형제](../09-operator-precedence-and-associativity/)에서 `&` 가 `!=` 보다 **약하다**는 것을 봤다.
- ★ `~flags` 는 하위 8비트만 보면 `1111 0101` 이지만 **전체는 `0xFFFFFFF5`** 다. `~` 는 **타입 전체**를 뒤집는다.

비용 — 전부 CPU 명령 한 개. **다른 자리를 건드리지 않는다**는 것이 값어치다.

### (2) 마스크 관용구 — 이름을 붙여 쓴다

**언제 쓰나** — 플래그가 두 개를 넘어가는 순간. 숫자 상수를 그대로 쓰면 다음 주에 못 읽는다.

```text
===== 소스: ex.c (11-b) =====
#include <stdio.h>
#define F_READ  (1u << 0)
#define F_WRITE (1u << 1)
#define F_EXEC  (1u << 2)
int main(void) {
    unsigned char perm = F_READ | F_WRITE;      /* 0000 0011 */
    printf("perm            = 0x%02X\n", perm);
    perm |= F_EXEC;
    printf("perm |= F_EXEC  = 0x%02X\n", perm);
    perm &= ~F_WRITE;                            /* ~F_WRITE 는 상위가 전부 1 */
    printf("perm &= ~F_WRITE= 0x%02X\n", perm);
    printf("~F_WRITE        = 0x%08X (int, %d)\n", (unsigned)~F_WRITE, (int)~F_WRITE);
    perm ^= F_READ;
    printf("perm ^= F_READ  = 0x%02X\n", perm);
    printf("has EXEC ? %d\n", (perm & F_EXEC) != 0);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
(경고 없음)
perm            = 0x03
perm |= F_EXEC  = 0x07
perm &= ~F_WRITE= 0x05
~F_WRITE        = 0xFFFFFFFD (int, -3)
perm ^= F_READ  = 0x04
has EXEC ? 1
exit=0
```

```text
[gcc -Wall] 0 건 exit=0
[gcc -Wall -Wextra] 0 건 exit=0
[gcc -Wall -Wextra -pedantic] 0 건 exit=0
[gcc -Wall -Wextra -Wconversion] ★ 1 건 exit=0
```

```text
ex.c: In function ‘main’:
ex.c:10:13: warning: conversion from ‘unsigned int’ to ‘unsigned char’ changes the value of ‘4294967293’ [-Wconversion]
   10 |     perm &= ~F_WRITE;                            /* ~F_WRITE 는 상위가 전부 1 */
      |             ^
```

그림 해설 (한 단계씩):

- **`1u << n` 으로 마스크를 만든다.** `u` 가 붙은 이유는 (5)에서 본다.
- ★ **`~F_WRITE` 는 `0xFFFFFFFD` 다** — 32비트짜리다. 그것을 `unsigned char` 에 대입하면 **상위 24비트가 잘린다.**
- **결과는 맞다**(`0x05`). 잘린 자리가 전부 1 이었고 `&` 라서 하위 8비트만 쓰였기 때문이다.
- ★★ **그런데 `-Wconversion` 은 이것을 경고한다.** 「맞는 코드인데 경고가 나는」 자리이고,\
  `perm &= (unsigned char)~F_WRITE;` 로 **의도를 적어 주면** 사라진다.
- ★ **기본 플래그 셋으로는 0건**이다 — `-Wall -Wextra -pedantic` 을 다 켜도 안 보인다.

비용 — 없다. **플래그 타입을 `unsigned` 로 맞추면** 이 자리가 통째로 사라진다.

### (3) ★★ 승격이 여기서 문제를 만든다 — `unsigned char c = 0xFF; ~c`

**언제 쓰나** — `char`·`short` 에 비트 연산을 할 때. **거의 언제나** 걸린다.

```text
===== 소스: ex.c (11-c) =====
#include <stdio.h>
#include <limits.h>
int main(void) {
    unsigned char c = 0xFF;
    printf("sizeof c        = %zu\n", sizeof c);
    printf("sizeof (~c)     = %zu\n", sizeof (~c));
    printf("~c              = %d   (0x%X)\n", ~c, (unsigned)~c);
    printf("(unsigned char)~c = %u (0x%X)\n", (unsigned char)~c, (unsigned char)~c);
    printf("~c == 0 ? %d   /  (unsigned char)~c == 0 ? %d\n", ~c == 0, (unsigned char)~c == 0);
    unsigned short s = 0xFFFF;
    printf("~s              = %d\n", ~s);
    printf("c << 8          = %d\n", c << 8);
    printf("(unsigned char)(c << 8) = %u\n", (unsigned char)(c << 8));
    printf("CHAR_BIT=%d  sizeof(int)=%zu  INT_MAX=%d  UINT_MAX=%u\n", CHAR_BIT, sizeof(int), INT_MAX, UINT_MAX);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
ex.c: In function ‘main’:
ex.c:9:66: warning: promoted bitwise complement of an unsigned value is always nonzero [-Wsign-compare]
    9 |     printf("~c == 0 ? %d   /  (unsigned char)~c == 0 ? %d\n", ~c == 0, (unsigned char)~c == 0);
      |                                                                  ^~
sizeof c        = 1
sizeof (~c)     = 4
~c              = -256   (0xFFFFFF00)
(unsigned char)~c = 0 (0x0)
~c == 0 ? 0   /  (unsigned char)~c == 0 ? 1
~s              = -65536
c << 8          = 65280
(unsigned char)(c << 8) = 0
CHAR_BIT=8  sizeof(int)=4  INT_MAX=2147483647  UINT_MAX=4294967295
exit=0
```

```text
   unsigned char c = 0xFF            8비트 :            1111 1111

   ★ ~c 를 계산하기 전에 c 가 int 로 승격된다  (03번의 정수 승격)
                                     32비트 : 0000 0000 0000 0000 0000 0000 1111 1111
   그 32비트를 뒤집는다
                                     32비트 : 1111 1111 1111 1111 1111 1111 0000 0000
                                              = 0xFFFFFF00 = ★ -256   (sizeof 는 4)

   "8비트를 뒤집으면 0" 이라고 기대하면 틀린다 —
   ★ 0 이 되는 것은 (unsigned char)~c 로 다시 8비트로 잘랐을 때다.
```

그림 해설 (한 단계씩):

- **`sizeof c` 는 1 인데 `sizeof (~c)` 는 4 다.** `~` 의 피연산자가 **먼저 `int` 로 승격**되기 때문이다([03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)).
- **`~c` 는 `-256`** 이다. `0` 이 아니고, **부호 있는 값**이다.
- ★ **`if (~c)` 는 언제나 참이다.** gcc 가 이것을 **`-Wsign-compare` 로 말해 준다** —\
  「promoted bitwise complement of an unsigned value is always nonzero」. ★ 그 플래그는 **`-Wextra` 에만** 있다(`-Wall` 단독 0건).
- **`c << 8` 은 `65280`** 이다. 8비트 타입인데 **값이 8비트 밖으로 나간다** — 승격됐기 때문에 잘리지 않는다.
- ★ **고치는 법은 두 가지** — ① 결과를 원래 폭으로 **다시 캐스트**(`(unsigned char)~c`) ②

  애초에 **`unsigned` 로 선언**한다.

비용 — 없다. 다만 **작은 타입에 비트 연산을 하는 코드는 전부 이 자리를 지난다.**

### (4) ★★★ 시프트의 UB 셋 — sanitizer 가 각각 말한다

**언제 쓰나** — 시프트량이 **변수**일 때. 상수일 때는 (7)에서 보듯 컴파일러가 먼저 말해 준다.

```text
===== 소스: ex.c (11-d) =====
#include <stdio.h>
int main(void) {
    int w = 32;
    volatile int n = -1;      /* 음수 시프트량 */
    volatile int m = 32;      /* 폭 이상 */
    volatile int v = 1;
    printf("v << n (n=-1) = %d\n", v << n);
    printf("v << m (m=32) = %d\n", v << m);
    volatile int big = 1073741824;   /* 2^30 */
    printf("big << 2      = %d\n", big << 2);   /* 부호 비트를 넘긴다 */
    volatile int neg = -8;
    printf("neg >> 1      = %d\n", neg >> 1);
    printf("w             = %d\n", w);
    return 0;
}
```

```text
===== gcc -std=c17 -fsanitize=undefined (recover 허용 — 셋을 다 본다) =====
ex.c:7:38: runtime error: shift exponent -1 is negative
ex.c:8:38: runtime error: shift exponent 32 is too large for 32-bit type 'int'
ex.c:10:40: runtime error: left shift of 1073741824 by 2 places cannot be represented in type 'int'
v << n (n=-1) = -2147483648
v << m (m=32) = 1
big << 2      = 0
neg >> 1      = -4
w             = 32
exit=0
```

```text
===== gcc -std=c17 -fsanitize=undefined -fno-sanitize-recover=all =====
ex.c:7:38: runtime error: shift exponent -1 is negative
exit=1
★ 첫 건에서 멈춘다 — 나머지 둘은 보이지 않는다.

===== clang -std=c17 -fsanitize=undefined (recover 허용) =====
ex.c:7:38: runtime error: shift exponent -1 is negative
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior ex.c:7:38 
ex.c:8:38: runtime error: shift exponent 32 is too large for 32-bit type 'int'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior ex.c:8:38 
ex.c:10:40: runtime error: left shift of 1073741824 by 2 places cannot be represented in type 'int'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior ex.c:10:40 
exit=0
```

```text
   ★ UB 셋을 그림으로

   ① 음수 시프트량        v << -1
      32칸 판을 "-1 칸" 민다  -> 뜻이 없다
      관찰된 값 -2147483648   (x86 이 시프트량을 5비트로 가려 31 이 된 결과)

   ② 폭 이상              v << 32      (int 는 32비트)
      판이 32칸인데 32칸을 민다 -> 전부 밀려 나가야 할 것 같지만
      관찰된 값 1            (x86 이 32 & 31 = 0 으로 가렸다 — 안 민 것이다)

   ③ 부호 비트를 넘김      (2^30) << 2
      1 이 30번 자리에 있다. 2칸 밀면 32번 자리 — 판 밖이다.
      관찰된 값 0

   ★ 세 값 전부 "하드웨어가 우연히 그렇게 한 것" 이지 C 의 답이 아니다.
```

그림 해설 (한 단계씩):

- **세 가지가 각각 다른 문구**로 나온다 — `shift exponent ... is negative` / `... is too large for 32-bit type` /\
  `left shift of ... cannot be represented in type 'int'`. **어느 UB 인지를 도구가 이름으로 말해 준다.**
- ★★ **`-fno-sanitize-recover=all` 을 쓰면 첫 건에서 죽는다.** 셋을 다 보려면 **recover 를 허용**해야 한다.\
  **「UBSan 이 한 건만 냈다」는 「UB 가 하나뿐이다」가 아니다.**
- ★ **`>>` 로 음수를 미는 것(`neg >> 1`)은 UB 가 아니다** — UBSan 이 그 줄에 대해 아무 말도 안 했다. (6)에서 본다.
- **세 줄 다 `volatile` 을 붙였다.** 안 붙이면 컴파일러가 상수로 접어 (7)의 컴파일 타임 경고로 넘어가 버린다.

비용 — 시프트량을 **`0 <= n < 폭`** 으로 보장하는 검사 한 줄. 그게 전부다.

### (5) `1 << 31` 과 `1u << 31` — 한 글자가 UB 를 가른다

**언제 쓰나** — **맨 위 비트**를 마스크로 쓸 때. 32비트 플래그에서 반드시 만난다.

```text
===== 소스: ex.c (11-e) =====
#include <stdio.h>
#include <limits.h>
int main(void) {
    printf("1 << 31        = %d\n", 1 << 31);
    printf("1u << 31       = %u\n", 1u << 31);
    printf("(int)(1u<<31)  = %d\n", (int)(1u << 31));
    printf("1u << 31 == INT_MIN ? %d\n", (int)(1u << 31) == INT_MIN);
    printf("1 << 30        = %d\n", 1 << 30);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
(경고 0 건)
1 << 31        = -2147483648
1u << 31       = 2147483648
(int)(1u<<31)  = -2147483648
1u << 31 == INT_MIN ? 1
1 << 30        = 1073741824
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -Wshift-overflow=2 =====
ex.c:4:39: warning: result of ‘1 << 31’ requires 33 bits to represent, but ‘int’ only has 32 bits [-Wshift-overflow=]
    4 |     printf("1 << 31        = %d\n", 1 << 31);
      |                                       ^~

===== gcc -std=c17 -fsanitize=undefined =====
ex.c:4:39: runtime error: left shift of 1 by 31 places cannot be represented in type 'int'

===== clang -std=c17 -Wall -Wextra =====
(경고 0 건)
```

```text
   1 << 31   (int 는 부호 있는 32비트)
   자리       31 30 ...  1  0
   결과        1  0 ...  0  0     <- 31번은 ★ 부호 비트다
   int 가 담을 수 있는 최대는 2^31 - 1 인데 결과는 2^31 -> ★ UB

   1u << 31  (unsigned 는 부호가 없다)
   자리       31 30 ...  1  0
   결과        1  0 ...  0  0     <- 31번도 그냥 값의 자리다
   unsigned 의 최대는 2^32 - 1 -> ★ 완전히 정의된 동작. 값은 2147483648
```

그림 해설 (한 단계씩):

- **`1 << 31` 은 UB 다.** 부호 있는 `int` 에 **표현할 수 없는 값**을 만들려 하기 때문이다.
- ★★ **그런데 `-Wall -Wextra -pedantic` 이 0건이다.** gcc 도 clang 도 말이 없다.\
  **`-Wshift-overflow=2` 를 따로 켜야** 말해 준다 — 기본은 레벨 1 이고, 레벨 1 은 **`1 << 31` 을 봐준다.**
- ★ **UBSan 은 잡는다.** 컴파일 타임 침묵과 런타임 진단이 **엇갈리는 대표 자리**다.
- **`1u << 31` 은 완전히 안전하다.** `u` 한 글자 차이다. 값도 `2147483648` 로 곧게 나온다.
- **캐스트로 되돌리면 `INT_MIN`** 이다 — `(int)(1u << 31) == INT_MIN` 이 `1` 이었다.\
  ★ 그 변환은 **UB 가 아니라 구현 정의**다(범위 밖 값을 부호 있는 타입으로 바꾸는 것 — [05번 형제](../05-explicit-casts-and-pointer-conversions/)).

비용 — `u` 한 글자. **마스크는 언제나 `unsigned` 로 만든다**가 규칙이 된다.

### (6) `-1 >> 1` 은 구현 정의 — UB 가 아니다

**언제 쓰나** — 음수를 2 로 나누는 대신 시프트하고 싶을 때. **그 대체가 성립하지 않는다**는 것이 결론이다.

```text
===== 소스: ex.c (11-f) =====
#include <stdio.h>
int main(void) {
    volatile int n = -1;
    volatile int m = -8;
    volatile unsigned u = 0xFFFFFFFFu;
    printf("-1 >> 1   = %d\n", n >> 1);
    printf("-8 >> 1   = %d\n", m >> 1);
    printf("-8 >> 2   = %d\n", m >> 2);
    printf("-8 / 2    = %d\n", m / 2);
    printf("-8 / 4    = %d\n", m / 4);
    printf("0xFFFFFFFFu >> 1 = 0x%08X\n", u >> 1);
    volatile int neg7 = -7;
    printf("-7 >> 1   = %d   (-7/2 = %d)\n", neg7 >> 1, neg7 / 2);
    return 0;
}
```

```text
===== gcc -O0 / gcc -O2 / clang -O2 — 세 벌이 같다 =====
-1 >> 1   = -1
-8 >> 1   = -4
-8 >> 2   = -2
-8 / 2    = -4
-8 / 4    = -2
0xFFFFFFFFu >> 1 = 0x7FFFFFFF
-7 >> 1   = -4   (-7/2 = -3)
===== gcc UBSan(-fno-sanitize-recover=all) =====
exit=0   (진단 0줄)
```

```text
===== gcc -O2 -S -masm=intel (int sh(int v){ return v >> 1; }) =====
sh:
	endbr64
	mov	eax, edi
	sar	eax
	ret
```

```text
   -1 을 한 칸 오른쪽으로 밀면 빈 왼쪽 칸을 무엇으로 채우나?

   산술 시프트 (arithmetic)        논리 시프트 (logical)
   1111 1111 -> 1111 1111          1111 1111 -> 0111 1111
   부호 비트를 복사한다              0 을 채운다
   결과 -1                         결과 2147483647

   ★ C 는 "둘 중 하나" 라고만 한다 (구현 정의).
     gcc·clang 은 산술 시프트다 — 어셈블리의 sar 가 그 증거다
     (논리 시프트였다면 shr 였을 것이다).
```

그림 해설 (한 단계씩):

- **`-1 >> 1` 은 `-1`** 이었다. 빈 자리를 **부호 비트로 채웠다**는 뜻이고, 어셈블리 `sar`(shift arithmetic right)가 그것을 직접 보여 준다.
- ★ **UBSan 이 한 줄도 안 낸다.** **UB 가 아니라 구현 정의**이기 때문이다 — 같은 줄에서 (4)의 셋은 다 잡혔다.
- ★★ **그래서 「시프트는 나눗셈과 같다」가 틀린다.** `-7 >> 1` 은 **`-4`** 인데 `-7 / 2` 는 **`-3`** 이다.\
  시프트는 **아래로**(−∞ 방향) 내리고 나눗셈은 **0 쪽으로** 자른다. **음수에서만 갈린다.**
- **`unsigned` 를 오른쪽으로 미는 것은 구현 정의가 아니다** — 언제나 0 을 채운다(`0x7FFFFFFF`).

비용 — 없다. 다만 **부호 있는 값을 시프트로 나누지 마라.** 컴파일러가 `/` 를 알아서 시프트로 바꾼다.

### (7) `-Wshift-*` 는 상수만 본다 — 변수는 한 건도 못 본다 ★★

**언제 쓰나** — 「경고를 켰으니 괜찮겠지」라고 생각한 순간.

```text
===== 소스: ex.c (11-g) =====
#include <stdio.h>
int main(void) {
    int a = 1 << -1;          /* 상수: 음수 시프트량 */
    int b = 1 << 32;          /* 상수: 폭 이상 */
    int c = 1073741824 << 2;  /* 상수: 부호 비트를 넘긴다 */
    int d = 1 << 31;          /* 상수: 부호 비트 자리 */
    printf("%d %d %d %d\n", a, b, c, d);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
ex.c: In function ‘main’:
ex.c:3:15: warning: left shift count is negative [-Wshift-count-negative]
    3 |     int a = 1 << -1;          /* 상수: 음수 시프트량 */
      |               ^~
ex.c:4:15: warning: left shift count >= width of type [-Wshift-count-overflow]
    4 |     int b = 1 << 32;          /* 상수: 폭 이상 */
      |               ^~
ex.c:5:24: warning: result of ‘1073741824 << 2’ requires 34 bits to represent, but ‘int’ only has 32 bits [-Wshift-overflow=]
    5 |     int c = 1073741824 << 2;  /* 상수: 부호 비트를 넘긴다 */
      |                        ^~
exit=0
-2147483648 0 0 -2147483648
```

```text
상수로 쓴 판 (ex.c 11-g)
[gcc                      ] 3 건 exit=0     ★ 플래그를 하나도 안 줘도 3 건
[gcc -Wall                ] 3 건 exit=0
[gcc -Wextra              ] 3 건 exit=0
[gcc -Wall -Wextra        ] 3 건 exit=0
[gcc -Wall -Wextra -pedantic] 3 건 exit=0
[gcc -Wall -Wno-shift-count-negative] 2 건 exit=0
[gcc -Wall -Wextra -Wno-shift-overflow] 2 건 exit=0

같은 것을 변수로 쓴 판 (ex.c 11-d)
[gcc -Wall                ] ★ 0 건 exit=0
[gcc -Wall -Wextra        ] ★ 0 건 exit=0
[gcc -Wall -Wextra -pedantic] ★ 0 건 exit=0
[gcc -O2 -Wall -Wextra    ] ★ 0 건 exit=0
```

```text
===== clang -std=c17 -Wall -Wextra (상수 판) =====
ex.c:5:24: warning: signed shift result (0x100000000) requires 34 bits to represent, but 'int' only has 32 bits [-Wshift-overflow]
    5 |     int c = 1073741824 << 2;  /* 상수: 부호 비트를 넘긴다 */
      |             ~~~~~~~~~~ ^  ~
ex.c:3:15: warning: shift count is negative [-Wshift-count-negative]
    3 |     int a = 1 << -1;          /* 상수: 음수 시프트량 */
      |               ^  ~~
ex.c:4:15: warning: shift count >= width of type [-Wshift-count-overflow]
    4 |     int b = 1 << 32;          /* 상수: 폭 이상 */
      |               ^  ~~
3 warnings generated.
```

그림 해설 (한 단계씩):

- **상수면 세 건 전부 잡힌다** — 그것도 **플래그를 하나도 안 줘도** 잡는다. `-Wshift-*` 계열은 기본으로 켜져 있다.
- ★★ **같은 UB 를 변수로 쓰면 네 플래그 조합 전부 0건**이다. `-O2` 를 켜도 0건이다.\
  **컴파일러가 시프트량을 모르기 때문**이고, 이 자리는 **UBSan 말고는 볼 도구가 없다.**
- ★ **`1 << 31`(위 `d`)은 상수인데도 0건이다** — (5)에서 본 대로 `-Wshift-overflow=2` 가 필요하다.
- clang 은 **문구가 다르고 순서도 다르다**(`signed shift result (0x100000000)` 로 **값까지** 보여 준다).

비용 — 없다. 다만 **「경고 0건」이 「UB 없음」이 아니라는 것**이 이 절의 결론이다.

### (8) ★★ 「안 터졌다」는 「안전하다」가 아니다 — 최적화 수준이 답을 바꾼 자리

**언제 쓰나** — UB 를 한 번 돌려 보고 「값이 나오네」라고 넘어가려 할 때.

```text
===== 소스: ex.c (11-h) =====
#include <stdio.h>
static int sum_bits(int n) {
    int s = 0;
    for (int i = 0; i < n; i++) s += (1 << i);    /* i >= 31 이면 UB */
    return s;
}
int main(void) {
    printf("sum_bits(4)  = %d\n", sum_bits(4));
    printf("sum_bits(40) = %d\n", sum_bits(40));
    return 0;
}
```

```text
gcc   -O0 : sum_bits(4)  = 15   sum_bits(40) = 254
gcc   -O1 : sum_bits(4)  = 15   sum_bits(40) = 254
gcc   -O2 : sum_bits(4)  = 15   sum_bits(40) = 254
gcc   -O3 : sum_bits(4)  = 15   sum_bits(40) = 254
gcc   -Os : sum_bits(4)  = 15   sum_bits(40) = 254
clang -O0 : sum_bits(4)  = 15   sum_bits(40) = 254
clang -O2 : sum_bits(4)  = 15   sum_bits(40) = ★ 1
(gcc 경고: -O2 -Wall -Wextra -pedantic 에서 0 건)
```

```text
===== gcc -fsanitize=undefined (recover 허용) =====
ex.c:4:41: runtime error: left shift of 1 by 31 places cannot be represented in type 'int'
sum_bits(4)  = 15
sum_bits(40) = 254
exit=0
★ 진단이 ★ 한 줄뿐이다 — 루프가 i=31..39 로 아홉 번 UB 를 지나는데도.
```

```text
   같은 소스 · 같은 표준 · 같은 함수

   여섯 벌   -> 254
   clang -O2 -> ★ 1

   ★ "다섯 수준에서 값이 같았다" 를 근거로 삼았다면
     여섯 번째에서 뒤집혔을 것이다.
     ★ UB 는 값이 아니라 "컴파일러가 무엇을 가정하나" 의 문제다.
```

그림 해설 (한 단계씩):

- **여섯 벌이 `254` 로 같았고 clang `-O2` 하나가 `1` 이었다.** 컴파일러가 다른 게 아니라 **같은 컴파일러의 최적화 수준**이 갈랐다.
- ★★ **한 수준만 돌리고 「이 값이 나온다」고 적으면 그 문장이 틀린다.** 이 주제에서 다섯 벌을 돌린 이유다.
- ★ **UBSan 이 같은 소스 위치를 한 번만 보고한다** — 아홉 번 지나간 UB 가 **한 줄**로 요약됐다.\
  **진단 줄 수는 UB 횟수가 아니다.**
- ★ 그리고 진단이 말한 것은 **`by 31`**(부호 비트 넘김)뿐이다. `i >= 32` 의 **「폭 이상」은 같은 줄이라 보고되지 않았다.**

비용 — 컴파일 몇 번. **UB 가 의심되면 최적화 수준을 바꿔 가며 돌린다**가 규칙이다.

### (9) 비트필드 — 있다는 것과 「구현 정의가 많다」까지

**언제 쓰나** — 구조체에 1\~4비트짜리 값을 여러 개 담고 싶을 때. **레이아웃에 기대면 안 된다.**

```text
===== 소스: ex.c (11-i) =====
#include <stdio.h>
struct Flags {
    unsigned a : 1;
    unsigned b : 3;
    signed   c : 4;
    int      d : 4;
};
int main(void) {
    struct Flags f = { 1, 5, -3, 7 };
    printf("sizeof(struct Flags) = %zu\n", sizeof(struct Flags));
    printf("a=%u b=%u c=%d d=%d\n", f.a, f.b, f.c, f.d);
    f.b = 9;                       /* 3비트에 9 는 안 들어간다 */
    printf("b = 9 를 넣으면 b=%u\n", f.b);
    f.d = 8;                       /* int : 4 에 8 */
    printf("d = 8 을 넣으면 d=%d\n", f.d);
    unsigned char *p = (unsigned char *)&f;
    printf("바이트 = %02X %02X %02X %02X\n", p[0], p[1], p[2], p[3]);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
ex.c: In function ‘main’:
ex.c:12:11: warning: unsigned conversion from ‘int’ to ‘unsigned char:3’ changes value from ‘9’ to ‘1’ [-Woverflow]
   12 |     f.b = 9;                       /* 3비트에 9 는 안 들어간다 */
      |           ^
ex.c:14:11: warning: overflow in conversion from ‘int’ to ‘signed char:4’ changes value from ‘8’ to ‘-8’ [-Woverflow]
   14 |     f.d = 8;                       /* int : 4 에 8 */
      |           ^
sizeof(struct Flags) = 4
a=1 b=5 c=-3 d=7
b = 9 를 넣으면 b=1
d = 8 을 넣으면 d=-8
바이트 = D3 78 00 00
```

```text
===== clang -std=c17 -Wall -Wextra =====
ex.c:12:9: warning: implicit truncation from 'int' to bit-field changes value from 9 to 1 [-Wbitfield-constant-conversion]
ex.c:14:9: warning: implicit truncation from 'int' to bit-field changes value from 8 to -8 [-Wbitfield-constant-conversion]
2 warnings generated.
sizeof(struct Flags) = 4
a=1 b=5 c=-3 d=7
b = 9 를 넣으면 b=1
d = 8 을 넣으면 d=-8
바이트 = D3 08 00 00
```

```text
   같은 구조체 · 같은 값 · 같은 플래그인데

   gcc   -> 바이트 = D3 ★78 00 00
   clang -> 바이트 = D3 ★08 00 00

   필드 값은 양쪽 다 a=1 b=5 c=-3 d=-8 로 같다.
   ★ 다른 것은 "아무도 안 쓰는 자리" 에 남은 비트다.
   -> 구조체를 바이트로 읽어 프로토콜·파일 포맷에 쓰면 그 자리에서 갈린다.
```

그림 해설 (한 단계씩):

- **필드 값은 이식 가능하다** — `a=1 b=5 c=-3` 이 양쪽에서 같다.
- ★★ **바이트 배치는 아니다.** **같은 소스에서 gcc 와 clang 의 두 번째 바이트가 달랐다**(`78` ↔ `08`).\
  비트필드의 **할당 순서·패딩·미사용 비트**가 구현에 맡겨져 있다는 뜻이다.
- **넘치는 값을 넣으면 조용히 잘린다** — `b = 9` 가 `1` 이 되고 `d = 8` 이 `-8` 이 된다.\
  ★ **상수를 넣을 때만 경고가 난다.** 변수를 넣으면 (7)과 같은 이유로 안 보인다.
- ★ **`int x : 4` 의 부호는 구현 정의다.** 여기서는 **부호 있는 것으로** 잡혔다(`d = 8` → `-8`, gcc 의 진단도 `signed char:4` 라고 적었다).\
  **`signed`·`unsigned` 를 명시하지 않으면 이식되지 않는다.**

비용 — 메모리는 아낀다. **대신 레이아웃 보장을 잃는다.** 외부 포맷에는 **시프트와 마스크로 직접** 조립한다.

### (10) ★ `-std=` 는 강제가 아니다 — C23 문법이 `-std=c89` 를 통과한다

**언제 쓰나** — 「`-std=c17` 로 돌렸으니 C17 코드다」라고 말하려 할 때.

```text
===== 소스: ex.c (11-j) =====
#include <stdio.h>
int main(void) {
    unsigned mask = 0b1011;        /* C23 의 2진 리터럴 */
    printf("0b1011 = %u\n", mask);
    return 0;
}
```

```text
[gcc -std=c89 -Wall -Wextra          ] 경고 ★ 0 건  exit=0
[gcc -std=c89 -Wall -Wextra -pedantic] 경고   1 건  exit=0
[gcc -std=c99 -Wall -Wextra          ] 경고 ★ 0 건  exit=0
[gcc -std=c99 -Wall -Wextra -pedantic] 경고   1 건  exit=0
[gcc -std=c17 -Wall -Wextra          ] 경고 ★ 0 건  exit=0
[gcc -std=c17 -Wall -Wextra -pedantic] 경고   1 건  exit=0
[gcc -std=c23 -Wall -Wextra          ] 경고 ★ 0 건  ★ exit=1
[gcc -std=c23 -Wall -Wextra -pedantic] 경고 ★ 0 건  ★ exit=1
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic 이 하는 말 =====
ex.c: In function ‘main’:
ex.c:3:21: warning: binary constants are a C2X feature or GCC extension
    3 |     unsigned mask = 0b1011;        /* C23 의 2진 리터럴 */
      |                     ^~~~~~
0b1011 = 11

===== gcc -std=c23 =====
gcc: error: unrecognized command-line option ‘-std=c23’; did you mean ‘-std=c2x’?
exit=1

===== gcc -std=c2x -Wall -Wextra -pedantic =====
(경고 0 건) exit=0
0b1011 = 11
```

그림 해설 (한 단계씩):

- ★★ **C23 문법이 `-std=c89` 에서 경고 0건으로 통과한다.** `-std=` 는 **강제가 아니라 기본값 선택**이다.\
  **표준 준수를 주장하려면 `-pedantic` 이 필요하다.**
- ★★★ **마지막 두 줄이 이 절의 진짜 교훈이다** — `-std=c23` 은 **경고 0건**인데 **`exit=1`** 이다.\
  **gcc 13.3.0 에 그런 옵션이 없어서 컴파일 자체가 실패한 것**이고, 경고만 세었다면 **「0건 통과」로 기록됐을 것**이다.
- ★ **그래서 경고를 셀 때는 종료 코드를 같이 본다.** [09번 형제](../09-operator-precedence-and-associativity/)가 `-Wprecedence` 로 같은 사고를 재현했다.
- gcc 13 에서 C23 을 쓰려면 **`-std=c2x`** 다. clang 18 은 `-std=c23` 을 받는다.

비용 — 플래그 한 개(`-pedantic`)와 **출력 한 줄 더 보기**(종료 코드).

## 문법 — 형태와 규칙

### 형태 — 여섯 연산자와 마스크 관용구

```c
/* ===== 여섯 연산자 ===== */
a & b      /* 비트 AND  : 둘 다 1 이면 1 */
a | b      /* 비트 OR   : 하나라도 1 이면 1 */
a ^ b      /* 비트 XOR  : 다르면 1 */
~a         /* 비트 NOT  : 전부 뒤집는다 (★ 단항 — 승격이 먼저 일어난다) */
a << n     /* 왼쪽 시프트  : 2^n 배 */
a >> n     /* 오른쪽 시프트 : 2^n 로 나눈 몫 (★ 음수는 구현 정의) */

/* ===== 마스크 관용구 넷 ===== */
flags |=  MASK;              /* 설정 */
flags &= ~MASK;              /* 해제 */
flags ^=  MASK;              /* 토글 */
if ((flags & MASK) != 0) ;   /* 검사 — ★ 괄호 필수 (09번) */

/* ===== 마스크 만들기 ===== */
#define F_READ  (1u << 0)    /* ★ u 를 붙인다 — 31번 자리에서 UB 가 갈린다 */
#define MASK_LOW4  0x0Fu
```

### 금지 사례 — 어느 것이 무슨 층인가

```c
int v = 1, n;

/* (1) 시프트량이 음수 -> ★ UB */
n = -1;  v << n;

/* (2) 시프트량이 타입 폭 이상 -> ★ UB */
n = 32;  v << n;              /* int 가 32비트일 때 */

/* (3) 부호 있는 타입에서 부호 비트를 넘기는 좌시프트 -> ★ UB */
1 << 31;
1073741824 << 2;

/* (4) 음수의 우시프트 -> ★ 구현 정의 (UB 아님) */
-1 >> 1;                      /* gcc·clang 은 -1 (산술 시프트) */

/* (5) 작은 타입의 ~ -> ★ 표준이되 승격된다 */
unsigned char c = 0xFF;
~c;                           /* int 로 승격되어 -256. 0 이 아니다 */
if (~c) { }                   /* ★ 언제나 참 */

/* (6) 비교보다 약한 것을 잊는다 -> ★ 값이 틀린다 (UB 아님, 09번) */
if (flags & MASK != 0) { }    /* flags & (MASK != 0) 으로 묶인다 */

/* (7) 안전한 형태 */
1u << 31;                     /* unsigned 면 31번 자리도 그냥 값이다 */
(unsigned)v >> 1;             /* 논리 시프트가 보장된다 */
```

- (1)·(2)·(3)은 **UBSan 이 각각 다른 문구로 잡는다.** 단 **시프트량이 상수일 때만** 컴파일 타임 경고가 난다.
- (4)는 **어느 도구도 말하지 않는다** — 말할 것이 없다. **구현이 문서화하는 층**이다.
- (5)는 `-Wextra` 의 **`-Wsign-compare`** 가 비교 자리에서만 말해 준다.

### 규칙 불릿

- **`& | ^ ~` 는 피연산자를 먼저 정수 승격**시킨다 — `char`·`short` 는 **언제나 `int` 로 올라간 뒤** 계산된다([03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)).
- **`<<` `>>` 는 좌우를 각각 승격**시킨다. ★ **통상 산술 변환이 아니다** — 오른쪽 피연산자가 왼쪽 타입에 영향을 주지 않는다.
- ★ **시프트량은 `0 <= n < (승격된 왼쪽 타입의 비트 폭)`** 이어야 한다. 벗어나면 **UB**다.
- ★ **부호 있는 타입의 좌시프트는 결과가 그 타입에 표현 가능해야** 한다. 아니면 **UB**다. `unsigned` 에는 이 제약이 없다(모듈로 2^N).
- ★ **음수의 우시프트는 구현 정의**다. gcc·clang 은 **산술 시프트**(부호 비트 복사) — 어셈블리 `sar` 로 확인했다.
- **`unsigned` 의 우시프트는 언제나 0 을 채운다.**
- **`~` 의 결과 타입은 승격된 타입**이다 — `sizeof (~c)` 가 4 였다.
- **비트 연산자 셋(`&`·`^`·`|`)은 비교 연산자보다 약하다** — 괄호가 필수다([09번 형제](../09-operator-precedence-and-associativity/)).
- **비트필드의 레이아웃·`int x:n` 의 부호는 구현 정의**다. 값은 이식되고 **바이트는 이식되지 않는다.**

## 어디서 틀리나

### 1. ★★ 「`unsigned char` 를 뒤집으면 `unsigned char` 가 되겠지」

```text
   unsigned char c = 0xFF;
   ~c  ->  ★ -256 (int)     sizeof (~c) = 4
   (unsigned char)~c -> 0
```

- **승격 때문이다.** 작은 타입은 연산 전에 **`int` 로 올라간다.**
- `if (~c)` 가 **언제나 참**이고, gcc 가 `-Wextra` 에서 「always nonzero」라고 말해 준다.
- 막는 법: **결과를 원래 폭으로 캐스트**하거나 **처음부터 `unsigned` 로 선언**한다.

### 2. ★★ 「`1 << 31` 로 맨 위 비트 마스크를 만든다」

- **`1 << 31` 은 UB 다.** `1u << 31` 이라야 한다.
- **`-Wall -Wextra -pedantic` 이 0건**이다 — `-Wshift-overflow=2` 를 켜야 보인다. UBSan 은 잡는다.
- 막는 법: **마스크는 언제나 `1u << n`.**

### 3. ★★ 「시프트량 검사는 경고가 잡아 주겠지」

```text
   상수 : 1 << 32   -> 플래그 없이도 3 건
   변수 : v << m    -> -Wall -Wextra -pedantic -O2 ★ 전부 0 건
```

- **컴파일러가 값을 모르면 말해 줄 수 없다.** 실무의 시프트량은 대부분 변수다.
- 막는 법: **시프트 직전에 범위를 검사**하거나 **UBSan 을 CI 에 건다.**

### 4. 「시프트는 2 로 나누는 것과 같다」 ★

```text
   -7 >> 1  = ★ -4        (아래로 내린다)
   -7 / 2   = ★ -3        (0 쪽으로 자른다)
```

- **음수에서만 갈린다.** 양수에서는 같아서 테스트를 통과해 버린다.
- 막는 법: **나눗셈은 `/` 로 쓴다.** 최적화는 컴파일러가 한다.

### 5. ★ 「경고 0건이니까 UB 가 없다」

- (7)의 변수 판이 **0건**이고 (5)의 `1 << 31` 도 **0건**이다.
- ★ **`-std=c23` 은 0건이면서 `exit=1`**(컴파일 실패)이었다 — **세는 것만으로는 구분이 안 된다.**
- 막는 법: **종료 코드를 같이 본다** + **UBSan 을 돌린다** + **최적화 수준을 바꿔 본다.**

### 6. ★★ 「UBSan 이 한 줄 냈으니 UB 가 하나다」

- (8)에서 루프가 **아홉 번** UB 를 지나는데 진단은 **한 줄**이었다. **같은 소스 위치는 한 번만 보고한다.**
- (4)에서 `-fno-sanitize-recover=all` 을 쓰면 **첫 건에서 죽어** 나머지 둘이 안 보였다.
- 막는 법: **recover 를 허용해 한 번 더 돌린다.** 「전부 보기」와 「빌드를 깨기」는 다른 실행이다.

### 7. 비트필드로 외부 포맷을 그린다

- gcc 와 clang 의 **바이트가 달랐다**(`D3 78 00 00` ↔ `D3 08 00 00`).
- `int x : 4` 의 **부호조차 구현 정의**다.
- 막는 법: 외부 포맷은 **`unsigned` 변수 + 시프트·마스크**로 직접 조립한다.

## 구현 세부사항 대 언어 보장

C 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★ **이 주제는 「UB」 칸이 본체다.** 바로 앞 [10번 형제](../10-evaluation-order-and-sequence-points/)는 **「미명시」가 본체**였고 UB 칸은 도구가 못 봤는데,\
여기서는 **UBSan 이 세 번 말을 한다.** ★ 그리고 이 주제는 **「구현 정의」 칸이 실제로 차는 몇 안 되는 주제**다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | `& \| ^ ~` 의 비트별 동작 · 마스크 관용구 넷 · **피연산자가 정수 승격되는 것**(`sizeof (~c)` = 4) · `unsigned` 의 좌시프트가 **모듈로 2^N** 인 것 · `unsigned` 우시프트가 0 을 채우는 것 · 비트필드의 **값** | 자리 그림과 값 대조 · `sizeof` · gcc·clang 두 벌 | — |
| **조건부 표준** | 매크로가 정의될 때만 | **해당 없음** — 이 주제에 조건부 보장은 없다 | — | — |
| **구현 정의** | 문서화 의무가 있다 | ★ **음수의 우시프트**(`-1 >> 1`) — gcc·clang 은 **산술 시프트**(`sar`) · **`int x : 4` 의 부호** · **비트필드의 바이트 배치·패딩** · `int` 의 폭 자체([02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)) | `-O0`·`-O2`·clang 세 벌 값 일치 + **어셈블리 `sar`** · 비트필드 바이트를 gcc ↔ clang 대조 | ★ **UBSan 이 침묵한다** — UB 가 아니므로 대상이 아니다. **경고도 없다** |
| **미명시** | 몇 가지 중 하나 | ★ **해당 없음** — 비트 연산 자체에는 미명시가 없다. 단 **한 식에 부작용을 둘 넣으면** 그 순서가 미명시가 된다([10번 형제](../10-evaluation-order-and-sequence-points/)) | (10번에서 확인) | — |
| **UB** | 아무 일이나 | ★★ **본체 셋** — **음수 시프트량** · **폭 이상의 시프트량** · **부호 비트를 넘기는 좌시프트**(`1 << 31` 포함) | UBSan 이 **각각 다른 문구**로 진단 · 상수일 때 `-Wshift-count-negative`/`-Wshift-count-overflow`/`-Wshift-overflow=` | ★★ **변수 시프트량은 경고 0건**(`-O2` 포함) · ★ **`1 << 31` 은 `-Wshift-overflow=2` 없이는 0건** · ★ **UBSan 은 같은 위치를 한 번만 보고** |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | gcc `-Wall -Wextra -pedantic` | `-Wshift-overflow=2` | clang `-Wall -Wextra` | UBSan | 무엇이 잡나 |
|---|---|---|---|---|---|---|
| `1 << -1`(상수) | UB | **1건** | 1건 | **1건** | **잡는다** | 컴파일 타임 + 런타임 |
| `1 << 32`(상수) | UB | **1건** | 1건 | **1건** | **잡는다** | 〃 |
| `1073741824 << 2`(상수) | UB | **1건** | 1건 | **1건** | **잡는다** | 〃 |
| ★ `1 << 31`(상수) | UB | **0건** | **1건** | **0건** | **잡는다** | ★ 기본 경고가 봐준다 |
| ★★ `v << n`(변수, `n<0`) | UB | **0건** | 0건 | 0건 | **잡는다** | ★ **UBSan 뿐** |
| ★★ `v << m`(변수, `m>=32`) | UB | **0건** | 0건 | 0건 | **잡는다** | ★ **UBSan 뿐** |
| ★ `-1 >> 1` | **구현 정의** | 0건 | 0건 | 0건 | ★ **0줄** | ★ **아무도 안 잡는다 — 잡을 것이 없다.** 구현 문서를 읽는 것뿐 |
| `~c`(작은 타입) | 표준(승격) | **1건**(`-Wextra` 의 `-Wsign-compare`, **비교 자리에서만**) | 〃 | 0건 | 0줄 | ★ **비교하지 않으면 아무도 말 안 한다** |
| `perm &= ~F_WRITE` 절단 | 표준 | 0건 | 0건 | 0건 | 0줄 | ★ **`-Wconversion` 뿐** |
| 비트필드 바이트 배치 | **구현 정의** | 0건 | 0건 | 0건 | 0줄 | ★ **두 컴파일러의 바이트를 비교하는 것뿐** |
| 루프 안 반복 UB 횟수 | UB | 0건 | 0건 | 0건 | ★ **1줄**(9회인데) | ★ **횟수는 아무도 안 센다** |

- ★★ **이 표의 결론 두 줄**
  - **상수 시프트는 컴파일러가, 변수 시프트는 UBSan 이 잡는다.** 둘 다 없으면 **아무도 안 잡는다.**
  - **구현 정의는 도구가 원리상 침묵한다** — [10번 형제](../10-evaluation-order-and-sequence-points/)의 **미명시**와 **같은 이유**다. 「UB 가 아니라서」다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 플래그 설정 | `flags \|= (1u << n);` | `flags \|= (1 << n);`(n 이 31 이면 UB) |
| 플래그 해제 | `flags &= ~(1u << n);` | `flags &= (1u << n);` |
| 플래그 검사 | `if ((flags & MASK) != 0)` | `if (flags & MASK != 0)` |
| 맨 위 비트 마스크 | `1u << 31` | `1 << 31` |
| 2 의 거듭제곱 곱셈 | `v * 2` 또는 `(unsigned)v << 1` | 부호 있는 `v << 1`(오버플로 자리) |
| 2 의 거듭제곱 나눗셈 | `v / 2` | `v >> 1`(음수에서 값이 다르다) |
| 오른쪽에 0 을 채우고 싶다 | `(unsigned)v >> 1` | `v >> 1`(구현 정의) |
| 작은 타입 뒤집기 | `(unsigned char)~c` | `~c` 를 그대로 비교 |
| 시프트량이 변수 | **범위를 검사한 뒤 시프트** | 그냥 시프트하고 UBSan 도 안 돌림 |
| 외부 포맷(파일·프로토콜) | `unsigned` + 시프트·마스크 | 비트필드 구조체를 바이트로 읽기 |
| 메모리 절약(내부 전용) | 비트필드(값만 쓴다) | 비트필드의 **바이트 배치**에 기대기 |

판단 규칙 두 줄.

- **마스크는 `unsigned`, 시프트량은 검사한다.** 이 두 줄이 UB 셋을 전부 덮는다.
- **경고는 상수만 본다.** 변수는 **UBSan 과 최적화 수준 여러 벌**로만 보인다.

## 핵심 문장

- **비트 연산 넷은 「한 자리만 건드린다」** — 설정 `\|=` · 해제 `&= ~` · 토글 `^=` · 검사 `& … != 0`(괄호 필수).
- ★★ **시프트의 UB 는 셋이다** — **음수 시프트량** · **폭 이상** · **부호 비트를 넘기는 좌시프트**.\
  UBSan 이 **각각 다른 문구**로 잡았고, `-fno-sanitize-recover=all` 로는 **첫 건에서 멈춘다.**
- ★ **`-1 >> 1` 은 UB 가 아니라 구현 정의**다. gcc·clang 은 **산술 시프트**이고 어셈블리 `sar` 가 증거다.\
  **UBSan 은 이 자리에서 침묵한다 — 잡을 것이 없기 때문이다.**
- ★★ **`unsigned char c = 0xFF; ~c` 는 `-256`** 이고 `sizeof (~c)` 는 **4** 다. **승격이 먼저 일어난다.**
- ★ **`1 << 31` 은 UB, `1u << 31` 은 안전**하다. `u` 한 글자 차이이고,\
  **기본 경고는 `1 << 31` 을 봐준다**(`-Wshift-overflow=2` 필요).
- ★★ **`-Wshift-*` 계열은 상수만 본다.** 같은 UB 를 변수로 쓰면 `-O2` 를 켜도 **0건**이다.
- ★★ **「여섯 벌에서 값이 같았다」는 안전이 아니다** — 일곱 번째(clang `-O2`)에서 `254` 가 **`1`** 이 됐다.
- ★ **UBSan 은 같은 소스 위치를 한 번만 보고한다** — 아홉 번 지나간 UB 가 한 줄이었다.
- ★ **`-std=c23` 이 경고 0건에 `exit=1`** 이었다. **gcc 13 에는 그 옵션이 없다**(`-std=c2x`). **종료 코드를 같이 봐야 한다.**
- **비트필드는 값만 이식된다.** 바이트 배치가 gcc 와 clang 에서 **달랐다**(`78` ↔ `08`).

## 관련 자료

- [`../README.md`](../README.md) — C 문법·API 주제 목록(이 주제는 11번)
- [`algorithm/29-bit-manipulation/`](../../../../../algorithm/29-bit-manipulation/) — **그쪽은 비트 트릭·응용**(popcount·부분집합 순회), 여기는 **C 의 타입 규칙과 UB**. 트릭의 정확성은 그쪽, 그 트릭이 **어느 타입에서 깨지나**는 여기
- [`data-representation/`](../../../../data-representation/) — **그쪽은 2진 표현·2의 보수 자체**, 여기는 **C 연산자가 그 표현을 어떻게 다루나**
- [`03-integer-promotion-and-usual-arithmetic-conversions/`](../03-integer-promotion-and-usual-arithmetic-conversions/) — ★★ **승격 규칙의 정본.** `~c` 가 `-256` 이 되는 이유가 거기 있고, 여기는 **그것이 비트 연산에서 어떻게 드러나나**까지
- [`02-basic-types-sizes-and-fixed-width-integers/`](../02-basic-types-sizes-and-fixed-width-integers/) — **`int` 의 폭이 고정이 아닌 것.** 「폭 이상의 시프트」가 몇부터인지를 정하는 자리
- [`05-explicit-casts-and-pointer-conversions/`](../05-explicit-casts-and-pointer-conversions/) — `(int)(1u << 31)` 이 **구현 정의**인 것 · **미명시 층을 처음 세운 형제**
- [`09-operator-precedence-and-associativity/`](../09-operator-precedence-and-associativity/) — ★ **`&`·`^`·`\|` 가 비교보다 약한 것.** `flags & MASK != 0` 사고의 정본
- [`10-evaluation-order-and-sequence-points/`](../10-evaluation-order-and-sequence-points/) — ★★ **미명시가 본체인 주제.** 거기서 침묵한 UBSan 이 여기서는 세 번 말한다 — **같은 도구의 두 얼굴**
- [`12-control-flow-and-switch/`](../12-control-flow-and-switch/) — 플래그를 `switch` 로 가를 때 · `case` 가 **정수 상수식**이어야 하는 것 · 이 주제와 **다섯 층의 두께가 정반대**다
- 목록의 **54번 주제** (부호 있는 정수 오버플로) — **부호 비트를 넘기는 좌시프트**와 같은 집안의 UB
- 목록의 **58번 주제** (UB 를 잡는 도구) — ★ **UBSan 의 한계**(한 번만 보고 · recover 옵션 · 기본 검사 집합)의 정본

## 용어 풀이

- **마스크(mask)** — 관심 있는 비트만 1 로 세운 값. 예: `1u << 2` 는 2번 자리만 보게 한다.
- **비트 AND `&`** — 두 값의 같은 자리가 **둘 다 1 일 때만** 1. 예: 검사·자르기에 쓴다.
- **비트 OR `\|`** — 하나라도 1 이면 1. 예: 플래그 설정.
- **비트 XOR `^`** — 다르면 1. 예: 토글(두 번 하면 원래대로).
- **비트 NOT `~`** — 전부 뒤집는다. ★ **단항이라 피연산자가 먼저 `int` 로 승격된다.**
- **정수 승격(integer promotion)** — `char`·`short`·비트필드가 연산 전에 `int`(또는 `unsigned int`)로 올라가는 것. 예: `sizeof (~c)` 가 4.
- **산술 시프트(arithmetic shift)** — 오른쪽으로 밀 때 빈 자리를 **부호 비트로** 채우는 것. 예: `-1 >> 1` 이 `-1`.
- **논리 시프트(logical shift)** — 빈 자리를 **0 으로** 채우는 것. 예: `0xFFFFFFFFu >> 1` 이 `0x7FFFFFFF`.
- **부호 비트(sign bit)** — 부호 있는 정수의 맨 왼쪽 비트. 예: 32비트 `int` 에서 31번 자리.
- **비트필드(bit-field)** — 구조체 멤버에 `: n` 으로 비트 수를 지정한 것. 예: `unsigned b : 3;`. ★ 레이아웃은 구현 정의.
- **미정의 동작(UB)** — 표준이 아무 요구도 하지 않는 것. **그런 프로그램이 아니다**는 뜻이다.
- **구현 정의 동작** — 구현마다 다르되 **문서화 의무가 있는** 것. 예: `-1 >> 1`.
- **UBSan(`-fsanitize=undefined`)** — UB 를 런타임에 잡는 도구. ★ **같은 소스 위치는 한 번만 보고한다.**
- **`-fno-sanitize-recover=all`** — 첫 진단에서 **프로그램을 끝내는** 옵션. 빌드를 깨는 데 쓰고, **전수 관찰에는 쓰지 않는다.**

---

## 더 들어가면

- ★ **`-fsanitize=undefined` 의 기본 집합에 `float-cast-overflow` 가 없다**는 것이 알려져 있다.\
  이 문서는 **시프트 세 항목이 기본 집합에 있다는 것**만 실측했고, **전체 목록을 훑지는 않았다.**\
  목록의 **58번 주제**가 그 정본이 될 자리다.

- **`-fsanitize=shift` 는 `-fsanitize=shift-base` 와 `-fsanitize=shift-exponent` 로 쪼갤 수 있다.**\
  ★ **이 문서에서는 쪼개서 던져 보지 않았다.** (4)의 세 진단이 어느 쪽 소속인지는 확인하지 않았다.

- ★ **`CHAR_BIT` 가 8 이 아닌 구현이 있다.** 이 문서의 「32비트 `int`」·「8비트 `char`」는 전부 **이 환경의 관찰**이고,\
  `CHAR_BIT=8`·`sizeof(int)=4` 를 출력으로 확인해 두었다. **폭에 기대는 코드는 `<limits.h>` 로 물어야 한다.**

- **2의 보수 이외의 표현**(1의 보수·부호-크기)은 **C23 에서 표준이 2의 보수로 못 박았다.**\
  ★ **이 문서에서 그것을 던져 확인하지는 않았다** — 확인할 하드웨어가 없다.

- **비트 회전(rotate)은 C 에 연산자가 없다.** `(v << n) | (v >> (32 - n))` 관용구를 쓰는데\
  ★ **`n == 0` 이면 `v >> 32` 가 되어 UB 다.** 이 함정은 **이 문서에서 던져 보지 않았다** — (4)의 ② 와 같은 집안이다.

- **`_BitInt(N)`(C23)** 은 임의 폭 정수를 준다. 시프트 규칙이 어떻게 적용되는지는\
  ★ **이 문서에서 던져 보지 않았다.**
