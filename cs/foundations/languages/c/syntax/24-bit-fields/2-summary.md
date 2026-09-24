# c/syntax/24 — 비트필드: 「**폭은 내가 정하고 자리는 컴파일러가 정한다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — Bit-fields (C)](https://en.cppreference.com/w/c/language/bit_field) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html) · [GCC 13 Structure-Packing Pragmas / C Implementation-defined behavior](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Structures-unions-enumerations-and-bit-fields-implementation.html) · [Clang Diagnostic flags](https://clang.llvm.org/docs/DiagnosticsReference.html)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값·바이트·진단·종료 코드는 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과\
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★★ **배치가 걸린 실험은 「컴파일러 2 × 최적화 3」 여섯 벌**을 돌렸다 — 한 벌만 돌리면 **반대 결론이 난다**(아래 (4)).
> **버전** — 비트필드는 **C89 부터** 있고 규칙이 바뀐 적이 없다.\
> ★ `_Bool` 비트필드는 **C99 부터**, `_Alignof` 는 **C11 부터**(철자 `alignof` 는 C23부터 — [08번 형제](../08-sizeof-alignment-and-offsetof/)가 정본).\
> ★ **`-std=` 를 바꿔도 이 주제의 결론은 안 바뀐다.** 이 문서는 `-std=c17` 로 고정했다.
> ★★ **경계** — **마스크와 시프트로 손수 비트를 다루는 법**은 [11번 형제](../11-bitwise-operations-and-shifts/)가 정본이다.\
> 그쪽은 「**손으로**」, 여기는 「**선언으로**」다 — 같은 일을 문법이 대신해 주는 대신 **자리 보장을 잃는다.**\
> ★ **정수 승격 규칙 자체**는 [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)가 정본이다. 여기서는 「**비트필드도 승격을 받는다**」만.\
> ★ **플래그를 담는 다른 방식**(열거 상수 + 마스크)은 [07번 형제](../07-enum-and-enumeration-constants/)가 정본이다.\
> ★ **패딩·정렬 규칙**은 [22번 형제](../22-struct-padding-and-alignment/), **`sizeof`·`_Alignof`·`offsetof` 라는 도구**는 [08번 형제](../08-sizeof-alignment-and-offsetof/)가 정본이다.\
> ★ **구조체 선언·초기화**는 [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/), **`union`** 은 [23번 형제](../23-union-and-the-boundary-of-type-punning/).
> 선행 — [11번 형제](../11-bitwise-operations-and-shifts/) · [22번 형제](../22-struct-padding-and-alignment/) · [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/).
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**비트필드는 「서랍 하나를 칸막이로 나눠 쓰는 것」이다.**

책상 서랍이 하나 있다고 하자. 서랍은 **통째로만 사고팔 수 있다** — 반 칸짜리 서랍은 없다.\
그래서 안에 **칸막이를 세워** 1칸짜리·3칸짜리 자리를 만든다. 여기까지가 내가 정하는 것이다.

★ 그런데 **칸막이를 왼쪽부터 세울지 오른쪽부터 세울지는 가구공이 정한다.**\
★★ 그리고 **칸막이를 다 세우고 남은 자리**에 무엇이 굴러다니는지는 **아무도 책임지지 않는다.**

| 비유 | 실체 | 층 |
|---|---|---|
| 서랍 한 개 | **할당 단위**(allocation unit) — 여기서는 4바이트 | **구현 정의** |
| 칸막이로 나눈 1칸·3칸 | `unsigned ready : 1;` · `unsigned kind : 3;` | **표준**(폭은 내가 정한다) |
| 칸막이를 **어느 쪽부터** 세우나 | 낮은 비트부터냐 높은 비트부터냐 | ★★ **구현 정의** |
| 서랍 하나에 안 들어가면 새 서랍을 쓰나 | 할당 단위 경계를 **걸칠 수 있는가** | ★★ **구현 정의** |
| 칸막이 없이 남은 자리 | **미사용 비트** | ★★★ **미명시 (본체)** |
| 3칸짜리에 9개를 밀어 넣기 | `f.kind = 9` → `1` 로 잘린다 | **표준**(UB 아님, **변환**이다) |
| 서랍 한 칸의 **주소**를 달라고 하기 | `&s.a` | **표준 — 컴파일 에러** |
| 「`int` 칸은 음수도 담나」 | `int x : 3` 의 부호 | ★★ **구현 정의** |
| 일부러 서랍을 새로 여는 것 | 폭 0 비트필드 `unsigned : 0;` | **표준** |

```text
   struct Flags { unsigned ready:1; dirty:1; locked:1; kind:3; prio:2; };
   -> sizeof = 4 (서랍 하나 = 32비트)

   비트 번호   31 .................... 8    7  6  5  4  3  2  1  0
             +----------------------------+--+--+--+--+--+--+--+--+
             |      아무도 안 쓰는 자리      |prio |  kind  |lo|di|re|
             +----------------------------+--+--+--+--+--+--+--+--+
                        ^                              ^        ^
              ★ 미명시 (24비트)              ★ 낮은 비트부터 채운다
                                               = 이 구현의 선택

   ready=1 dirty=0 locked=1 kind=5 prio=2 를 넣으면 첫 바이트는
             1 0 1 0 1 1 0 1  =  0xAD
             ^^^ prio=2  ^^^^^ kind=5(101)  ^ locked=1  ^ dirty=0  ^ ready=1
```

- ★★★ **이 주제는 「구현 정의」 칸이 본체**다. 내가 정하는 것은 **폭 하나뿐**이고, **자리·방향·단위·부호**가 전부 구현에 맡겨져 있다.
- ★★ 두 번째 무게중심은 「**미명시**」다 — **어느 멤버도 아닌 비트**의 값. 아래 (3)·(4)에서 **여섯 벌**로 흔들어 본다.
- ★ **UB 칸은 얇다.** 폭을 넘는 값을 넣는 것은 UB 가 **아니라 변환**이다 — 이 자리를 헷갈리면 안 된다.

> **비트필드(bit-field)** — 구조체 멤버에 **비트 단위 폭**을 지정한 것.\
> 예: `unsigned kind : 3;` 은 `kind` 에 **3비트만** 준다. 담을 수 있는 값은 `0`\~`7` 이다.

> **할당 단위(allocation unit)** — 컴파일러가 비트필드를 담으려고 잡는 **한 덩어리의 저장 공간**.\
> 예: 이 구현에서 `unsigned` 비트필드의 단위는 4바이트다. 그래서 8비트만 써도 `sizeof` 가 **4** 다.

> **미사용 비트(unused bit)** — 할당 단위 안에서 **어느 멤버에도 속하지 않는** 비트.\
> 예: 8비트만 선언한 32비트 단위에는 **24비트**가 남는다. 그 값이 무엇인지는 **정해져 있지 않다.**

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **비트필드로 무엇을 얻고 무엇을 잃나** — `sizeof` 가 줄어드는 대신 **무엇을 못 쓰게 되나.**
2. ★★★ **어느 멤버도 아닌 비트는 어떻게 되나** — 그리고 **그것이 컴파일러마다 갈리나 최적화 수준마다 갈리나.**
3. ★★ **`signed`·`unsigned` 를 안 적으면 무슨 일이 나나** — 그리고 **그 선택을 플래그로 되돌릴 수 있나.**

## 동작 방식

### (1) ★★ 비트필드는 「선언으로 하는 마스크·시프트」다

**언제 쓰나** — 1\~4비트짜리 상태값을 여러 개 한 구조체에 담고 싶을 때.

[11번 형제](../11-bitwise-operations-and-shifts/)에서 손으로 하던 일이 그대로 문법이 된 것이다.

```text
   11번 편의 방식 — 손으로                 24번 편의 방식 — 선언으로
   ---------------------------            ---------------------------
   unsigned v = 0;                        struct Flags { unsigned ready:1;
   v |= 1u << 0;        /* ready */                       unsigned kind :3; };
   v |= (5u & 7u) << 3; /* kind  */       struct Flags f;
   unsigned kind = (v >> 3) & 7u;         f.ready = 1;  f.kind = 5;
                                          unsigned kind = f.kind;
   ★ 자리(<<3)와 마스크(&7)를 내가 쓴다     ★ 컴파일러가 대신 써 준다
   ★ 그래서 자리가 보장된다                  ★ 그래서 ★ 자리가 보장되지 않는다
```

★ **거래는 정확히 하나다** — 손으로 쓰는 수고를 주고 **자리 보장을 잃는다.**\
그래서 **외부 포맷(파일·패킷)에는 비트필드를 쓰지 않는다.** 그쪽은 11번 편의 방식이다.

```c
/* s24a.c */
#include <stdio.h>
#include <string.h>

struct Flags {                     /* 여덟 개의 플래그를 비트로 */
    unsigned ready : 1;
    unsigned dirty : 1;
    unsigned locked: 1;
    unsigned kind  : 3;            /* 0~7 */
    unsigned prio  : 2;            /* 0~3 */
};
struct Plain { unsigned char ready, dirty, locked, kind, prio; };

int main(void) {
    printf("struct Flags sizeof=%zu _Alignof=%zu   (비트 합 = 1+1+1+3+2 = 8)\n",
           sizeof(struct Flags), _Alignof(struct Flags));
    printf("struct Plain sizeof=%zu _Alignof=%zu\n",
           sizeof(struct Plain), _Alignof(struct Plain));

    struct Flags f;
    memset(&f, 0, sizeof f);
    f.ready = 1; f.dirty = 0; f.locked = 1; f.kind = 5; f.prio = 2;
    printf("\nready=%u dirty=%u locked=%u kind=%u prio=%u\n",
           f.ready, f.dirty, f.locked, f.kind, f.prio);

    const unsigned char *b = (const unsigned char *)&f;
    printf("바이트 :");
    for (size_t k = 0; k < sizeof f; k++) printf(" %02x", b[k]);
    printf("\n첫 바이트를 비트로 : ");
    for (int k = 7; k >= 0; k--) putchar((b[0] >> k) & 1 ? '1' : '0');
    printf("   <- 오른쪽이 bit0\n");

    f.kind = 9;                    /* 3비트에 9(1001) 를 넣으면 */
    printf("\nkind 에 9 를 넣고 읽으면 = %u   <- 3비트라 잘린다\n", f.kind);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24a.c -o x ; ./x (cc exit=0 · run exit=0) =====
struct Flags sizeof=4 _Alignof=4   (비트 합 = 1+1+1+3+2 = 8)
struct Plain sizeof=5 _Alignof=1

ready=1 dirty=0 locked=1 kind=5 prio=2
바이트 : ad 00 00 00
첫 바이트를 비트로 : 10101101   <- 오른쪽이 bit0

kind 에 9 를 넣고 읽으면 = 1   <- 3비트라 잘린다
```

그림 해설 (한 단계씩):

- **여덟 비트를 선언했는데 `sizeof` 는 4** 다. 서랍은 통째로만 잡힌다(할당 단위 = 4바이트).
- 같은 뜻을 `unsigned char` 다섯 개로 쓰면 **`sizeof` 가 5** 이고 `_Alignof` 는 **1** 이다.\
  ★ **비트필드가 항상 작은 것이 아니다** — 여기서는 4 대 5 로 **한 바이트 차이**뿐이다.\
  ★ 멤버가 더 많아질수록 벌어진다. **여덟 개를 각각 `unsigned char` 로 쓰면 8 대 4** 가 된다.
- **첫 바이트가 `0xAD` = `10101101`** 이다. 오른쪽이 bit0 이므로 **선언 순서대로 낮은 비트부터** 채워졌다.\
  ★★ 이 방향은 **구현 정의**다. 다른 ABI 에서는 반대로 채운다.
- ★ `_Alignof` 는 **4** 다 — 비트필드 구조체의 정렬은 **할당 단위**를 따른다.

비용 — 메모리를 아끼고 **자리 보장·주소·`sizeof` 를 잃는다.**

### (2) ★★ 폭을 넘는 값은 UB 가 아니라 **변환**이다

**언제 쓰나** — 「3비트에 9 를 넣으면 터지나」를 판단할 때.

```text
   f.kind = 9;          9 = 1001 (네 자리)
                              ^
                              여기가 3비트 밖이다

   +--+--+--+--+                +--+--+--+
   | 1| 0| 0| 1|   ->  잘라서   | 0| 0| 1|   = 1
   +--+--+--+--+                +--+--+--+
    8  4  2  1                   4  2  1

   ★ 죽지 않는다. ★ 진단은 난다. ★ 값이 조용히 1 이 된다.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24a.c -o x (cc exit=0) =====
s24a.c: In function ‘main’:
s24a.c:32:14: warning: unsigned conversion from ‘int’ to ‘unsigned char:3’ changes value from ‘9’ to ‘1’ [-Woverflow]
   32 |     f.kind = 9;                    /* 3비트에 9(1001) 를 넣으면 */
      |              ^
```

그림 해설 (한 단계씩):

- **값은 `1` 이 된다.** 「미정의」가 아니라 **정수 변환**이다 — 9 를 3비트 폭에 넣은 결과다.
- ★ **gcc 가 `-Woverflow` 로 잡아 준다.** 다만 **상수를 넣을 때만**이다 — 변수를 넣으면 한 마디도 안 한다\
  ([11번 형제](../11-bitwise-operations-and-shifts/)의 「`-Wshift-*` 는 상수만 본다」와 같은 모양이다).
- ★★ **진단 문구를 읽어라** — 선언은 `unsigned` 인데 gcc 는 `unsigned char:3` 이라고 적는다.\
  **컴파일러가 속으로 잡은 단위 타입이 진단에 새어 나온 것**이고, 그 자체가 **구현 정의라는 증거**다.

비용 — **잘린다는 사실을 컴파일러가 늘 말해 주지는 않는다.** 범위 검사는 **내 몫**이다.

### (3) ★★★ 미사용 비트 — **이 편의 본체**

**언제 쓰나** — 비트필드 구조체를 **바이트로 읽거나 `memcmp` 로 비교**하려 할 때.

12비트만 선언한 32비트 단위에서, **나머지 20비트가 어떻게 되는지**를 두 실험으로 흔든다.

**실험 ①** — 먼저 `memset(0xFF)` 로 전부 1 로 만들고 두 멤버를 대입한다.

```c
/* s24b.c */
#include <stdio.h>
#include <string.h>

struct B { unsigned a : 8; unsigned b : 4; };   /* 12비트만 쓴다 */

int main(void) {
    struct B v;
    memset(&v, 0xFF, sizeof v);      /* 먼저 전부 1 로 */
    v.a = 0xD3;
    v.b = 0x8;
    const unsigned char *p = (const unsigned char *)&v;
    printf("sizeof=%zu  memset(0xFF) 뒤 a=0xD3, b=0x8 을 대입했다\n", sizeof v);
    printf("바이트 :");
    for (size_t k = 0; k < sizeof v; k++) printf(" %02x", p[k]);
    printf("\n비트   :");
    for (size_t k = 0; k < sizeof v; k++) {
        putchar(' ');
        for (int j = 7; j >= 0; j--) putchar((p[k] >> j) & 1 ? '1' : '0');
    }
    printf("\n★ 12~31 비트는 어느 멤버도 아니다 — 그 자리가 어떻게 되는지는 구현에 달렸다\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24b.c -o x ; ./x (cc exit=0 · run exit=0) =====
sizeof=4  memset(0xFF) 뒤 a=0xD3, b=0x8 을 대입했다
바이트 : d3 f8 ff ff
비트   : 11010011 11111000 11111111 11111111
★ 12~31 비트는 어느 멤버도 아니다 — 그 자리가 어떻게 되는지는 구현에 달렸다
```

```text
   memset(0xFF) 로 채운 뒤 a=0xD3, b=0x8 을 넣었다

   비트  31 .............. 12 | 11 10  9  8 |  7  6  5  4  3  2  1  0
        +--------------------+-------------+------------------------+
        | 1 1 1 1 ... 1 1 1 1| 1  0  0  0  | 1 1 0 1 0 0 1 1        |
        +--------------------+-------------+------------------------+
          ★ 미사용 20비트        b = 8          a = 0xD3

   바이트로 보면  d3 f8 ff ff
                     ^^ 여기 위쪽 니블 f 가 ★ 미사용 비트다
```

- **`a` 와 `b` 가 든 자리만 바뀌고 나머지 20비트는 `1` 그대로**다.\
  ★ 즉 이 벌에서는 **컴파일러가 「멤버 비트만 갈아 끼웠다」.**
- ★ 이 벌은 gcc·clang 과 `-O0`·`-O2` **네 벌이 전부 같았다.** 대조군으로 쓴다.

**실험 ②** — 이번에는 **초기화를 안 하고** 두 멤버만 대입한다(앞서 스택을 `0xFF` 로 더럽혀 둔다).

```c
/* s24b2.c */
#include <stdio.h>

struct B { unsigned a : 8; unsigned b : 4; };   /* 12비트만 쓴다 */

static void dirty(void) {
    volatile unsigned char buf[64];
    for (int k = 0; k < 64; k++) buf[k] = 0xFF;
    if (buf[0] != 0xFF) printf("!");
}

static struct B make(void) {       /* 초기화 없이 두 멤버만 대입한다 */
    volatile unsigned char guard[8] = {0};
    struct B v;
    v.a = 0xD3;
    v.b = 0x8;
    (void)guard;
    return v;
}

int main(void) {
    dirty();
    struct B v = make();
    const unsigned char *p = (const unsigned char *)&v;
    printf("초기화 없이 a=0xD3, b=0x8 만 대입했다 (앞서 스택을 0xFF 로 더럽혔다)\n");
    printf("바이트 :");
    for (size_t k = 0; k < sizeof v; k++) printf(" %02x", p[k]);
    printf("\n");
    return 0;
}
```

```text
===== 초기화 없이 두 멤버만 대입했을 때의 바이트 — 네 벌 (exit=0) =====
gcc   -O0 : 바이트 : d3 f8 ff ff
gcc   -O2 : 바이트 : d3 08 00 00
clang -O0 : 바이트 : d3 f8 ff ff
clang -O2 : 바이트 : d3 08 00 00
```

```text
   같은 프로그램 · 같은 대입 · 다른 빌드

   -O0  ->  d3 ★f8 ★ff ★ff     멤버 비트만 갈아 끼웠다 (주변이 살아남았다)
   -O2  ->  d3 ★08 ★00 ★00     할당 단위를 ★ 통째로 새로 썼다

   ★ 「미사용 비트」는 값이 아니라 ★ 컴파일러가 고른 코드 모양의 부산물이다.
```

그림 해설 (한 단계씩):

- ★★★ **같은 소스가 `-O0` 과 `-O2` 에서 다른 바이트를 낸다.** 멤버 값은 둘 다 `a=0xD3 b=0x8` 로 같다.
- **`-O0`** 은 멤버마다 **읽고-고치고-쓰기**를 해서 **주변 비트를 건드리지 않는다.**
- **`-O2`** 는 두 대입을 합쳐 **32비트 상수 하나를 통째로 쓴다.** 그래서 나머지가 `0` 이 된다.
- ★★ **gcc 와 clang 은 각 수준에서 한 글자도 같았다.** 갈린 축은 **컴파일러가 아니라 최적화 수준**이다.
- ★ **같은 바이너리를 15번 돌려 격자가 한 가지였다.** 흔들린 것은 **빌드**이지 **실행**이 아니다.

비용 — **비트필드 구조체를 `memcmp` 로 비교하거나 바이트째 직렬화하면 그 자리에서 갈린다.**\
([22번 형제](../22-struct-padding-and-alignment/)의 패딩 바이트와 **정확히 같은 성격**이다 — 다만 이쪽은 **비트 단위**다.)

### (4) ★★★ 앞 배치의 실측을 여섯 벌로 다시 던졌다 — **전제가 뒤집힌 자리**

**언제 쓰나** — 「이 배치는 gcc 와 clang 이 갈린다」는 문장을 근거로 쓰려 할 때.

[11번 형제](../11-bitwise-operations-and-shifts/)는 **같은 소스에서 gcc 가 `D3 78 00 00`, clang 이 `D3 08 00 00`** 을 냈다고 적었고,\
그것을 「**gcc 와 clang 이 갈린다**」로 읽었다. ★ 그 구조체를 **여섯 벌로** 다시 던졌다.

```c
/* s24b3.c */
#include <stdio.h>

/* 11번 편이 「gcc 와 clang 이 갈린다」고 적은 그 구조체를 그대로 다시 던진다 */
struct Flags {
    unsigned a : 1;
    unsigned b : 3;
    signed   c : 4;
    int      d : 4;
};

int main(void) {
    struct Flags f = { 1, 5, -3, 7 };
    f.b = 9;                       /* 3비트에 9 는 안 들어간다 */
    f.d = 8;                       /* int : 4 에 8 */
    printf("a=%u b=%u c=%d d=%d  ", f.a, f.b, f.c, f.d);
    const unsigned char *p = (const unsigned char *)&f;
    printf("바이트 = %02X %02X %02X %02X\n", p[0], p[1], p[2], p[3]);
    return 0;
}
```

```text
===== 11번 편의 구조체를 여섯 벌로 — 컴파일러 2 × 최적화 3 (exit=0) =====
gcc   -O0 : a=1 b=1 c=-3 d=-8  바이트 = D3 78 00 00
gcc   -O1 : a=1 b=1 c=-3 d=-8  바이트 = D3 08 00 00
gcc   -O2 : a=1 b=1 c=-3 d=-8  바이트 = D3 08 00 00
clang -O0 : a=1 b=1 c=-3 d=-8  바이트 = D3 08 00 00
clang -O1 : a=1 b=1 c=-3 d=-8  바이트 = D3 08 00 00
clang -O2 : a=1 b=1 c=-3 d=-8  바이트 = D3 08 00 00
```

```text
   11번 편이 본 것              여기서 본 것
   -------------------        ------------------------------------------
   gcc   -> D3 ★78 00 00      gcc  -O0 -> D3 ★78 00 00   ← 재현됐다
   clang -> D3 ★08 00 00      gcc  -O1 -> D3 ★08 00 00   ← ★ gcc 가 clang 과 같아진다
                              gcc  -O2 -> D3 ★08 00 00
                              clang -O0/-O1/-O2 -> D3 ★08 00 00

   ★ 갈린 축은 「컴파일러」가 아니라 「할당 단위를 통째로 쓰느냐」였다.
   ★ gcc 는 -O 하나로 그 선택을 바꾼다. clang 은 -O0 부터 통째로 쓴다.
```

그림 해설 (한 단계씩):

- ★★ **11번 편의 수치는 재현됐다** — 다만 **`-O0` 에서만**이다. 그 편은 `-O` 를 안 적었고 기본이 `-O0` 이었다.
- ★★★ **`-O1` 로 한 칸만 올리면 gcc 가 clang 과 같아진다.** 그러므로 「gcc 는 78, clang 은 08」은 **컴파일러의 성질이 아니다.**
- ★ (3)의 실험 ②와 **결론이 같다** — 갈리는 것은 「**멤버 비트만 갈아 끼우나, 단위를 통째로 쓰나**」 하나다.\
  프로그램에 따라 그 선택이 **컴파일러로 갈리기도 하고 `-O` 로 갈리기도 한다.**
- ★★ **그래서 「무엇이 갈리는가」를 한 축으로 단정하면 안 된다.** 던져야 할 것은 **격자 두 개가 아니라 여섯 개**다.
- ★ **못 잰 것** — gcc `-O0` 이 남긴 `7` 이라는 니블이 **어디서 온 값인지**는 이 실험만으로 못 가른다.\
  역어셈블을 보면 `-O0` 이 멤버마다 읽고-고치고-쓰기를 하며 **그 니블을 한 번도 안 건드린다**는 것까지는 보이지만,\
  **그 자리에 원래 무엇이 있었는지**는 이 프로그램 밖의 일이다.

비용 — **한 벌짜리 실험은 여기서 반대 결론을 준다.** 배치를 근거로 쓰려면 **축을 두 개 흔들어야** 한다.

### (5) ★★ `int x : n` 의 부호는 구현 정의다

**언제 쓰나** — 비트필드를 선언할 때마다. **`signed`·`unsigned` 를 적을지 말지.**

```c
/* s24c.c */
#include <stdio.h>

struct S {
    int          plain : 3;   /* ★ 부호가 구현 정의다 */
    signed int   sgn   : 3;
    unsigned int uns   : 3;
};

int main(void) {
    struct S s;
    s.plain = 7; s.sgn = 7; s.uns = 7;     /* 셋 다 비트는 111 */
    printf("셋 다 111 을 넣었다\n");
    printf("  int      x:3  ->  %d\n", s.plain);
    printf("  signed   x:3  ->  %d\n", s.sgn);
    printf("  unsigned x:3  ->  %u\n", s.uns);
    printf("\nint x:3 이 음수로 읽히면 이 구현에서는 ★ 부호 있는 것이다\n");
    printf("판정 : %s\n", s.plain < 0 ? "signed (이 구현)" : "unsigned (이 구현)");

    s.plain = 3; s.sgn = 3; s.uns = 3;
    printf("\n3 을 넣으면 셋 다 %d %d %u — 부호 비트가 안 켜지면 차이가 안 보인다\n",
           s.plain, s.sgn, s.uns);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24c.c -o x ; ./x (cc exit=0 · run exit=0) =====
셋 다 111 을 넣었다
  int      x:3  ->  -1
  signed   x:3  ->  -1
  unsigned x:3  ->  7

int x:3 이 음수로 읽히면 이 구현에서는 ★ 부호 있는 것이다
판정 : signed (이 구현)

3 을 넣으면 셋 다 3 3 3 — 부호 비트가 안 켜지면 차이가 안 보인다
```

```text
   비트는 셋 다 111 이다. 읽는 법이 다를 뿐이다.

   +--+--+--+                       +--+--+--+
   | 1| 1| 1|  unsigned x:3  -> 7   | 1| 1| 1|  signed x:3  -> -1
   +--+--+--+                       +--+--+--+
    4  2  1                          ^ 부호 비트로 읽는다

   int x:3 은 ★ 둘 중 무엇으로 읽을지 구현이 정한다.
   이 구현(gcc 13 / clang 18, x86-64)에서는 ★ signed 로 잡혔다.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24c.c -o x (cc exit=0) =====
s24c.c: In function ‘main’:
s24c.c:11:15: warning: overflow in conversion from ‘int’ to ‘signed char:3’ changes value from ‘7’ to ‘-1’ [-Woverflow]
   11 |     s.plain = 7; s.sgn = 7; s.uns = 7;     /* 셋 다 비트는 111 */
      |               ^
s24c.c:11:26: warning: overflow in conversion from ‘int’ to ‘signed char:3’ changes value from ‘7’ to ‘-1’ [-Woverflow]
   11 |     s.plain = 7; s.sgn = 7; s.uns = 7;     /* 셋 다 비트는 111 */
      |                          ^
```

그림 해설 (한 단계씩):

- ★★ **`int x : 3` 에 7 을 넣으면 `-1` 이 읽힌다** — 이 구현에서는 **부호 있는 것**으로 잡혔다.
- ★ **진단이 `signed char:3` 이라고 적는다.** (2)에서 `unsigned` 가 `unsigned char:3` 이라 불린 것과 짝이다.
- ★ **3 을 넣으면 셋 다 `3`** 이다. **부호 비트가 안 켜지면 차이가 안 보인다** — 이것이 이 함정이 오래 숨는 이유다.
- ★★ **clang 의 진단은 이름이 다르다** — `-Wbitfield-constant-conversion` 이다(아래 (5-나)).

**(5-나) 그 선택을 플래그로 되돌릴 수 있나 — 한쪽만 된다**

```text
===== int 비트필드의 부호 — 컴파일러와 -funsigned-bitfields 를 바꿔 가며 (exit=0) =====
gcc   (기본)             : int x:3 에 7 을 넣으면 -1
gcc   -funsigned-bitfields : int x:3 에 7 을 넣으면 7
clang (기본)             : int x:3 에 7 을 넣으면 -1
clang -funsigned-bitfields : int x:3 에 7 을 넣으면 -1
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -Wunused-command-line-argument -funsigned-bitfields s24c.c -o x (cc exit=0) =====
clang: warning: the clang compiler does not support '-funsigned-bitfields'
s24c.c:11:13: warning: implicit truncation from 'int' to bit-field changes value from 7 to -1 [-Wbitfield-constant-conversion]
   11 |     s.plain = 7; s.sgn = 7; s.uns = 7;     /* 셋 다 비트는 111 */
      |             ^ ~
s24c.c:11:24: warning: implicit truncation from 'int' to bit-field changes value from 7 to -1 [-Wbitfield-constant-conversion]
   11 |     s.plain = 7; s.sgn = 7; s.uns = 7;     /* 셋 다 비트는 111 */
      |                        ^ ~
2 warnings generated.
```

- ★★ **gcc 는 `-funsigned-bitfields` 로 바뀐다** — `-1` 이 `7` 이 된다.
- ★★★ **clang 은 안 바뀐다.** 그리고 `the clang compiler does not support '-funsigned-bitfields'` 라고 **말은 해 준다** —\
  다만 그 말은 `-Wunused-command-line-argument` 를 켜야 보이고, **빌드는 `cc exit=0` 으로 통과한다.**
- ★ 그래서 **「플래그로 맞추면 된다」는 이식 전략이 아니다.** 답은 하나다 — **`signed`·`unsigned` 를 직접 적는 것.**

비용 — 한 낱말을 안 적어서 **부호가 플랫폼마다 갈린다.** 적는 것은 공짜다.

### (6) `&` 와 `sizeof` 가 안 된다 — 에러 전문

**언제 쓰나** — 비트필드를 함수에 넘기거나 배열처럼 다루려 할 때.

```c
/* s24d.c */
#include <stdio.h>

struct S { unsigned a : 3; unsigned b : 5; };

int main(void) {
    struct S s = { 1, 2 };
    unsigned *p = &s.a;              /* (1) 비트필드는 주소를 못 잡는다 */
    printf("%zu\n", sizeof s.a);     /* (2) sizeof 도 안 된다 */
    printf("%zu\n", _Alignof(s.b));  /* (3) _Alignof 도 안 된다 */
    return p != 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24d.c -o x (cc exit=1) =====
s24d.c: In function ‘main’:
s24d.c:7:19: error: cannot take address of bit-field ‘a’
    7 |     unsigned *p = &s.a;              /* (1) 비트필드는 주소를 못 잡는다 */
      |                   ^
s24d.c:8:28: error: ‘sizeof’ applied to a bit-field
    8 |     printf("%zu\n", sizeof s.a);     /* (2) sizeof 도 안 된다 */
      |                            ^
s24d.c:9:21: warning: ISO C does not allow ‘_Alignof (expression)’ [-Wpedantic]
    9 |     printf("%zu\n", _Alignof(s.b));  /* (3) _Alignof 도 안 된다 */
      |                     ^~~~~~~~
s24d.c:9:21: error: ‘__alignof’ applied to a bit-field
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s24d.c -o x (cc exit=1) =====
s24d.c:7:19: error: address of bit-field requested
    7 |     unsigned *p = &s.a;              /* (1) 비트필드는 주소를 못 잡는다 */
      |                   ^~~~
s24d.c:8:30: error: invalid application of 'sizeof' to bit-field
    8 |     printf("%zu\n", sizeof s.a);     /* (2) sizeof 도 안 된다 */
      |                              ^
s24d.c:9:21: warning: '_Alignof' applied to an expression is a GNU extension [-Wgnu-alignof-expression]
    9 |     printf("%zu\n", _Alignof(s.b));  /* (3) _Alignof 도 안 된다 */
      |                     ^
s24d.c:9:29: error: invalid application of 'alignof' to bit-field
    9 |     printf("%zu\n", _Alignof(s.b));  /* (3) _Alignof 도 안 된다 */
      |                             ^~~~~
1 warning and 3 errors generated.
```

```text
   보통 멤버                        비트필드 멤버
   ------------------------        ------------------------
   &s.x   -> int *        OK       &s.a   -> ★ 컴파일 에러
   sizeof s.x -> 4        OK       sizeof s.a -> ★ 컴파일 에러
   포인터로 넘기기          OK       ★ 값으로만 넘길 수 있다

   ★ 이유는 하나다 — 비트필드는 ★ 바이트 경계에 안 맞을 수 있어 주소가 없다.
```

그림 해설 (한 단계씩):

- ★★ **에러도 출력이다.** 「안 된다」를 외우지 말고 **두 컴파일러의 문구를 나란히** 봐 두면 실전에서 바로 읽힌다.
- gcc 는 `cannot take address of bit-field` · `'sizeof' applied to a bit-field` 다.
- clang 은 `address of bit-field requested` · `invalid application of 'sizeof' to bit-field` 다.
- ★ **`_Alignof(식)` 은 그 자체가 ISO C 가 아니다** — gcc 는 `-Wpedantic` 으로, clang 은 `-Wgnu-alignof-expression` 으로 잡는다.\
  그 **경고와 「비트필드에는 못 쓴다」는 에러가 한 줄에 겹쳐** 나온다.
- ★ **`cc exit=1`** 이다 — 경고가 아니라 **에러**라서 그렇다. 종료 코드까지 같이 읽어야 뜻이 산다.

비용 — 비트필드는 **값으로만** 다룰 수 있다. 주소가 필요하면 **보통 멤버로 빼야** 한다.

### (7) ★ 승격 — 비트필드도 정수 승격을 받는다

**언제 쓰나** — 비트필드를 식에 쓸 때. 특히 **뺄셈과 비교**.

```c
/* s24e.c */
#include <stdio.h>

struct S {
    unsigned small : 3;    /* int 가 다 담을 수 있다 */
    unsigned full  : 32;   /* int 로는 못 담는다 */
};

#define NAME(x) _Generic((x), int: "int", unsigned int: "unsigned int", \
                              long: "long", default: "그 밖")

int main(void) {
    struct S s = { 0, 0 };
    printf("s.small 을 식에 쓰면 타입은 : %s\n", NAME(s.small + 0));
    printf("s.full  을 식에 쓰면 타입은 : %s\n", NAME(s.full + 0));
    printf("맨 unsigned 변수는          : %s\n", NAME((unsigned)0 + 0));

    printf("\n0 에서 1 을 빼 보면\n");
    printf("  s.small - 1 = %d      <- int 로 승격돼 음수가 나온다\n", s.small - 1);
    printf("  s.full  - 1 = %u      <- unsigned 그대로라 감싼다\n", s.full - 1);
    printf("  (s.small - 1 < 0) = %d · (s.full - 1 < 0) = %d\n",
           s.small - 1 < 0, s.full - 1 < 0);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24e.c -o x ; ./x (cc exit=0 · run exit=0) =====
s.small 을 식에 쓰면 타입은 : int
s.full  을 식에 쓰면 타입은 : unsigned int
맨 unsigned 변수는          : unsigned int

0 에서 1 을 빼 보면
  s.small - 1 = -1      <- int 로 승격돼 음수가 나온다
  s.full  - 1 = 4294967295      <- unsigned 그대로라 감싼다
  (s.small - 1 < 0) = 1 · (s.full - 1 < 0) = 0
```

```text
   unsigned small : 3         값의 범위 0..7      -> int 가 전부 담는다  -> ★ int 로 승격
   unsigned full  : 32        값의 범위 0..4294967295 -> int 가 못 담는다 -> ★ unsigned 그대로

   0 - 1 을 해 보면
     small - 1  ->  int 산술      ->  -1
     full  - 1  ->  unsigned 산술 ->  4294967295
                                      ^ 같은 「0 - 1」인데 답이 다르다
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24e.c -o x (cc exit=0) =====
s24e.c: In function ‘main’:
s24e.c:21:40: warning: comparison of unsigned expression in ‘< 0’ is always false [-Wtype-limits]
   21 |            s.small - 1 < 0, s.full - 1 < 0);
      |                                        ^
```

그림 해설 (한 단계씩):

- ★★ **`unsigned` 로 선언했는데 식에서는 `int` 가 된다.** `_Generic` 이 그렇게 답했다.\
  **폭이 좁아 `int` 가 전부 담을 수 있으면 `int` 로 승격**되기 때문이다([03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)가 정본).
- ★★ **폭 32 짜리는 `unsigned int` 그대로**다. `int` 가 그 범위를 못 담기 때문이다.
- ★★★ **그래서 같은 「0 에서 1 빼기」가 `-1` 과 `4294967295` 로 갈린다.** 폭 한 자리 차이로 부호가 바뀐다.
- ★ gcc 가 `full - 1 < 0` 을 `-Wtype-limits` 로 「**항상 거짓**」이라 잡아 준다. **`small - 1 < 0` 쪽은 아무 말도 안 한다** — 그쪽은 참이 될 수 있으니까.

비용 — **선언한 타입과 식의 타입이 다르다.** 비교·뺄셈에서는 **폭을 보고** 판단해야 한다.

### (8) 폭 0 비트필드 — 「다음 서랍을 열어라」

**언제 쓰나** — 비트필드를 **일부러 끊어서** 다음 할당 단위로 밀고 싶을 때.

```c
/* s24f.c */
#include <stdio.h>
#include <string.h>

struct A { unsigned a : 3; unsigned b : 3; };            /* 붙는다 */
struct B { unsigned a : 3; unsigned : 0; unsigned b : 3; };  /* ★ 폭 0 이 끊는다 */
struct C { unsigned a : 3; unsigned : 2; unsigned b : 3; };  /* 이름 없는 폭 2 */

static void dump(const char *tag, const void *p, size_t n) {
    const unsigned char *b = (const unsigned char *)p;
    printf("%-14s sizeof=%zu  바이트 :", tag, n);
    for (size_t k = 0; k < n; k++) printf(" %02x", b[k]);
    printf("\n");
}

int main(void) {
    struct A x; struct B y; struct C z;
    memset(&x, 0, sizeof x); memset(&y, 0, sizeof y); memset(&z, 0, sizeof z);
    x.a = 7; x.b = 7;
    y.a = 7; y.b = 7;
    z.a = 7; z.b = 7;
    dump("A  a:3 b:3", &x, sizeof x);
    dump("B  a:3 :0 b:3", &y, sizeof y);
    dump("C  a:3 :2 b:3", &z, sizeof z);
    printf("\n★ 폭 0 비트필드는 이름을 못 가진다 — 다음 할당 단위로 밀라는 지시다\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24f.c -o x ; ./x (cc exit=0 · run exit=0) =====
A  a:3 b:3     sizeof=4  바이트 : 3f 00 00 00
B  a:3 :0 b:3  sizeof=8  바이트 : 07 00 00 00 07 00 00 00
C  a:3 :2 b:3  sizeof=4  바이트 : e7 00 00 00

★ 폭 0 비트필드는 이름을 못 가진다 — 다음 할당 단위로 밀라는 지시다
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s24f.c -o x ; ./x (cc exit=0 · run exit=0) =====
A  a:3 b:3     sizeof=4  바이트 : 3f 00 00 00
B  a:3 :0 b:3  sizeof=8  바이트 : 07 00 00 00 07 00 00 00
C  a:3 :2 b:3  sizeof=4  바이트 : e7 00 00 00

★ 폭 0 비트필드는 이름을 못 가진다 — 다음 할당 단위로 밀라는 지시다
```

```text
   A { a:3; b:3; }              한 서랍에 붙는다
   비트  ... 7 6 5 4 3 2 1 0
          . . 1 1 1 1 1 1      -> 0x3F   sizeof 4
              ^^^^^ b    ^^^^^ a

   C { a:3; :2; b:3; }          이름 없는 폭 2 가 사이를 벌린다
   비트  ... 7 6 5 4 3 2 1 0
          1 1 1 0 0 1 1 1      -> 0xE7   sizeof 4
          ^^^^^ b  ^^ 빈칸  ^^^^^ a

   B { a:3; :0; b:3; }          ★ 폭 0 이 서랍을 끊는다
   바이트  07 00 00 00 | 07 00 00 00        sizeof ★ 8
           ^ a 의 서랍    ^ b 의 새 서랍
```

그림 해설 (한 단계씩):

- **이름 없는 폭 `n`(`unsigned : 2;`)** 은 그 자리를 **비워 둔다.** `C` 가 `0xE7` 인 것이 그 결과다.
- ★★ **폭 0 은 다르다** — 「여기서 끊고 **다음 할당 단위로 가라**」는 지시다. `B` 의 `sizeof` 가 **8** 이 된다.
- ★ **폭 0 비트필드는 이름을 가질 수 없다.** 담을 비트가 없으니 이름을 줄 이유도 없다.
- ★ **gcc 와 clang 이 한 글자도 같았다.** 다만 이것도 **구현 정의 영역**이라 다른 ABI 에서 같으리라는 보장은 없다.

비용 — 크기가 **늘어난다.** 경계를 맞추려고 일부러 쓰는 것이지 아껴 쓰는 도구가 아니다.

## 문법 — 형태와 규칙

### 형태 — 선언할 수 있는 다섯 가지

```text
struct S {
    unsigned int a : 3;    /* ① 표준이 보장하는 형태. 값 0..7 */
    signed   int b : 3;    /* ② 표준이 보장하는 형태. 값 -4..3 */
    int            c : 3;  /* ③ ★ 부호가 구현 정의다 — 쓰지 마라 */
    _Bool          d : 1;  /* ④ C99부터. 값 0 또는 1 */
    unsigned int     : 2;  /* ⑤ 이름 없는 비트필드 — 자리만 비운다 */
    unsigned int     : 0;  /* ⑥ 폭 0 — 다음 할당 단위로 민다. ★ 이름 금지 */
};
```

### 금지 사례 — 어느 것이 무슨 층인가

```text
struct S { unsigned a : 3; unsigned b : 5; };
struct S s = { 1, 2 };

unsigned *p = &s.a;              /* ★ 컴파일 에러 — 비트필드는 주소가 없다 */
size_t n = sizeof s.a;           /* ★ 컴파일 에러 — sizeof 도 안 된다 */
size_t m = _Alignof(s.b);        /* ★ 컴파일 에러 + _Alignof(식) 자체가 비표준 */

struct T { unsigned a : 40; };   /* ★ 컴파일 에러 — unsigned 의 폭을 넘었다 */
struct U { unsigned : 0 x; };    /* ★ 컴파일 에러 — 폭 0 은 이름을 못 가진다 */

s.a = 9;                         /* ★ UB 아님 — 「변환」이다. 조용히 1 이 된다 */

int flag : 3;                    /* ★ 컴파일 에러 — 비트필드는 구조체 멤버만 된다 */

memcmp(&s, &t, sizeof s);        /* ★★ 미명시에 의지하는 것 — 미사용 비트가 다를 수 있다 */
fwrite(&s, sizeof s, 1, fp);     /* ★★ 배치가 구현 정의 — 다른 빌드가 못 읽는다 */

struct V { int x : 3; };         /* ★★ 구현 정의 — 7 을 넣으면 -1 일 수도 7 일 수도 */
```

### 규칙 불릿

- ★★★ **폭은 내가 정하고 자리는 컴파일러가 정한다.** 이 한 줄이 이 주제 전부다.
- ★★ **표준이 보장하는 비트필드 타입은 `_Bool`·`signed int`·`unsigned int` 셋**이다.\
  `char`·`short`·`long long` 을 받아 주는 것은 **구현의 확장**이다(gcc·clang 은 받아 준다).
- ★★ **`int x : n` 의 부호는 구현 정의**다. **`signed`·`unsigned` 를 반드시 적어라.**
- ★★ **폭이 그 타입의 비트 수를 넘으면 컴파일 에러**다. 넘는 **값**을 넣는 것은 에러가 아니라 **변환**이다.
- ★★★ **`&` 와 `sizeof` 를 비트필드에 적용할 수 없다.** 값으로만 다룬다.
- ★★ **식에 쓰면 정수 승격을 받는다.** 폭이 좁으면 **`int`**, `int` 가 못 담으면 **`unsigned int`** 다.
- ★★★ **어느 멤버도 아닌 비트의 값은 미명시**다. `memcmp`·직렬화에 쓰면 그 자리에서 갈린다.
- ★★ **이름 없는 폭 `n`** 은 자리를 비우고, **폭 0** 은 **다음 할당 단위로 민다**(이름을 못 가진다).
- ★ **`sizeof` 는 할당 단위 단위로 올라간다.** 8비트만 선언해도 `sizeof` 가 **4** 다.
- ★ **비트필드 구조체의 정렬은 할당 단위를 따른다**(여기서는 `_Alignof` = 4).
- ★ **외부 포맷에는 쓰지 마라.** 그쪽은 [11번 형제](../11-bitwise-operations-and-shifts/)의 **마스크·시프트**가 정본이다.

## 어디서 틀리나

### 1. ★★★ 「같은 소스면 바이트도 같겠지」

**갈린다.** (3)과 (4)에서 **같은 소스가 `-O0` 과 `-O2` 에서 다른 바이트**를 냈다.\
멤버 값은 어디서나 같지만 **미사용 비트**는 컴파일러가 고른 코드 모양의 부산물이다.\
★ **파일·패킷에 그대로 쓰면 다른 빌드가 못 읽는다.**

### 2. ★★★ 「gcc 와 clang 이 갈린다더라」

**축이 하나가 아니다.** (4)에서 **`-O1` 로 올리자 gcc 가 clang 과 같아졌다.**\
★ **컴파일러를 두 개 돌려 본 것으로는 모자라다** — **최적화 수준까지** 흔들어야 한다.

### 3. ★★ 「`int x : 3` 이면 0\~7 이겠지」

**이 구현에서는 `-4`\~`3` 이다.** 7 을 넣으면 **`-1`** 이 읽힌다.\
★ **3 이하를 넣는 동안은 차이가 안 보인다** — 그래서 오래 숨는다. **`unsigned` 를 적어라.**

### 4. ★★ 「`-funsigned-bitfields` 로 맞추면 되겠지」

**gcc 에서만 먹는다.** clang 은 **그 옵션을 모른다고 말하면서 빌드를 통과**시킨다(`cc exit=0`).\
★ **「경고가 났으니 반영됐겠지」가 정반대**인 자리다 — 그 경고가 **무시했다는 통보**다.

### 5. ★★ 「비트필드를 쓰면 무조건 작아진다」

(1)에서 **4 대 5** 였다. 멤버가 적으면 **한 바이트밖에 안 줄어든다.**\
★ 그 한 바이트를 위해 **주소·`sizeof`·배치 보장**을 내준다. **배열로 백만 개를 만들 때** 비로소 값이 난다.

### 6. ★★ 「`memcmp` 로 두 플래그 구조체를 비교한다」

[22번 형제](../22-struct-padding-and-alignment/)의 패딩과 **같은 함정**이고, 여기서는 **비트 단위**라 더 촘촘하다.\
★ **멤버끼리 비교**해야 한다. 굳이 한 번에 비교하려면 **`memset` 으로 전부 0 으로 만든 뒤** 멤버를 넣는 규율이 필요하다.

### 7. ★ 「`&s.flag` 를 함수에 넘긴다」

**컴파일 에러**다. 비트필드는 바이트 경계에 안 맞을 수 있어 **주소 자체가 없다.**\
★ 주소가 필요하면 그 멤버는 **비트필드가 아니어야** 한다.

### 8. ★ 「비트필드는 선언 순서대로 낮은 비트부터 들어간다」

**이 ABI 에서만 그렇다.** 방향은 **구현 정의**이고, `0xAD` 라는 값은 **이 머신의 답**이다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「구현 정의」 칸이 가장 두껍다** — 자리·방향·단위·부호가 전부 거기 있다.\
★★ 두 번째는 「**미명시**」다 — **미사용 비트의 값**. ★ **UB 칸은 얇다** — 이 주제가 [11번 형제](../11-bitwise-operations-and-shifts/)와 다른 점이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | `_Bool`·`signed int`·`unsigned int` 로 선언할 수 있는 것 · **폭이 타입의 비트 수를 넘으면 에러** · **폭 0 은 이름을 못 가지는 것** · **`&` 와 `sizeof` 를 적용할 수 없는 것** · **식에 쓰면 정수 승격을 받는 것** · 넘는 값을 넣으면 **UB 가 아니라 변환**인 것 · 멤버 값 자체는 이식되는 것 | 컴파일 에러 전문 2벌 · `_Generic` 이 답한 `int` \| `unsigned int` · `9` → `1` · 여섯 벌 전부에서 `a=1 b=1 c=-3 d=-8` 동일 |
| **조건부 표준** | 매크로가 정의될 때만 | ★ **해당 없음** — 비트필드에는 매크로로 켜고 꺼지는 보장이 없다 | — |
| ★★★ **구현 정의 (본체)** | 문서화 의무가 있다 | ★★ **할당 단위 안에서 낮은 비트부터인가 높은 비트부터인가** · **할당 단위의 크기**(여기서는 4바이트) · **단위 경계를 걸칠 수 있는가** · ★★ **`int x : n` 이 부호 있는가** · **`char`·`short` 등을 비트필드 타입으로 허용하는가** · 비트필드 구조체의 **정렬** | 첫 바이트 `0xAD` = `10101101` · `sizeof` 4 · `_Alignof` 4 · `int x:3` 에 7 → **`-1`** · 진단이 적은 `signed char:3` · `unsigned char:3` |
| ★★ **미명시** | 몇 가지 중 하나 · **문서화 의무도 없다** | ★★★ **어느 멤버도 아닌 비트의 값** · 구조체 끝 패딩([22번 형제](../22-struct-padding-and-alignment/)가 정본) | ★ **여섯 벌** — `d3 f8 ff ff` ↔ `d3 08 00 00` ↔ `D3 78 00 00` ↔ `D3 08 00 00`. ★ **같은 바이너리 15번은 한 가지**였다(흔들린 것은 빌드다) |
| **UB** | 아무 일이나 | ★ **이 주제 고유의 UB 는 얇다.** 폭을 넘는 값은 변환이고, 폭을 넘는 **선언**은 에러다. ★ 미사용 비트를 **읽는 것 자체**는 `unsigned char` 로 보면 UB 가 아니다 — **판단에 쓰는 것**이 틀린 것이다. 넓은 UB(타입 펀닝·앨리어싱)는 [23번 형제](../23-union-and-the-boundary-of-type-punning/)와 목록의 **55번 주제**의 몫이다 | — (이 편은 **UB 를 만들지 않는 실험만** 돌렸다) |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| **표준** | ★ 여기는 도구가 잘 본다 — **`&`·`sizeof`·폭 초과·폭 0 이름**은 전부 **컴파일 에러**다(`cc exit=1`). ★ 다만 **넘는 값을 넣는 것은 상수일 때만** 잡는다. 변수를 넣으면 **0건**이다 |
| **조건부 표준** | ★ **해당 없음** — 볼 것이 없으니 도구도 할 말이 없다 |
| **구현 정의** | ★★ **「낮은 비트부터 채웠습니다」라고 말해 주는 경고가 없다.** 바이트를 **직접 찍어야** 보인다. ★★ **`int x:3` 의 부호도 경고가 0건**이다 — **7 을 넣어 `-Woverflow` 가 뜰 때에야** 진단 문구(`signed char:3`)로 새어 나온다 |
| **미명시** | ★★★ **미사용 비트는 어떤 경고·UBSan·ASan 도 안 본다.** 원리상 잡을 것이 없다 — **값이 없는 것이 아니라 정해지지 않은 것**이다. ★★ **한 벌만 빌드하면 「늘 이렇다」로 보인다** — 축을 둘(컴파일러 × `-O`) 흔들어야 갈린다 |
| **UB** | ★ 이 주제에서는 sanitizer 가 할 일이 거의 없다. **잡을 UB 를 만들지 않는 것**이 비트필드의 성질이다 |

- ★★ **이 표의 결론 네 줄**
  - ★★★ **가장 조용한 자리**는 「**미사용 비트**」다 — **컴파일도 통과하고 실행도 되고 값도 맞다.** 갈리는 것은 **바이트**뿐이고, 그것을 보는 유일한 창은 **직접 찍는 것**이다.
  - ★★ **두 번째는 `int x : n` 의 부호**다 — **3 이하만 쓰는 동안은 증상이 없다.**
  - ★★ `-funsigned-bitfields` 는 「**경고가 곧 무시 통보**」인 드문 자리다. 경고를 읽고 **반영됐다고 오해하기 딱 좋다.**
  - ★ **이 주제에서 쓸 수 있는 자동 검사는 `_Static_assert(sizeof(struct S) == 4, "")` 정도**다([08번 형제](../08-sizeof-alignment-and-offsetof/)가 정본). **비트 자리까지는 못 고정한다.**

### 이 주제의 네 번째 창 — **여섯 벌의 바이트 격자**

- **컴파일 진단**은 미사용 비트에 대해 한 마디도 안 한다.
- **실행 출력**(멤버 값)은 **여섯 벌 전부 같다** — 화면만 보면 아무 문제가 없다.
- **UBSan·ASan** 은 여기서 볼 것이 없다 — **접근 위반도 아니고 산술 문제도 아니다.**
- ★★ **그래서 창은 하나뿐이다** — **구조체를 `unsigned char *` 로 읽어 바이트를 찍는 것.**\
  ★ 그리고 **그 창을 한 번만 열면 안 된다.** **컴파일러 2 × 최적화 3 = 여섯 벌**을 열어야 「갈린다」가 보인다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 플래그 여러 개를 한 구조체에 | **비트필드** — 읽고 쓰기가 멤버 접근이라 싸다 | 마스크를 손으로 (여기서는 비트필드가 낫다) |
| **파일·패킷 포맷**을 그리기 | ★★ **마스크와 시프트로 직접 조립**([11번 형제](../11-bitwise-operations-and-shifts/)) | ★★ 비트필드 구조체를 그대로 `fwrite` |
| 부호를 결정하기 | **`signed`/`unsigned` 를 적는다** | `int x : 3` |
| 두 플래그 구조체 비교 | **멤버끼리 비교** | ★★ `memcmp` |
| 크기를 못 박기 | `_Static_assert(sizeof(struct S) == 4, "")` | 주석에 적기 |
| 경계에서 끊기 | **폭 0 비트필드** `unsigned : 0;` | 패딩 멤버를 손으로 세기 |
| 자리를 비우기 | **이름 없는 폭** `unsigned : 2;` | 더미 멤버에 이름 주기 |
| 주소가 필요한 값 | **보통 멤버로 뺀다** | `&s.bitfield` (에러다) |
| 넓은 값(0\~65535 등) | **보통 멤버** `uint16_t` | 폭 16 비트필드(승격 규칙이 꼬인다) |
| 배치를 확인하기 | ★★ **여섯 벌로 바이트를 찍는다** | 한 벌 돌려 보고 단정 |

판단 규칙 두 줄.

- ★★★ **내 프로그램 안에서만 사는 값이면 비트필드, 프로그램 밖으로 나가면 마스크·시프트.**
- ★★ **`signed`/`unsigned` 를 적지 않는 비트필드는 없다.**

## 핵심 문장

- ★★★ **폭은 내가 정하고 자리는 컴파일러가 정한다.**
- ★★★ **어느 멤버도 아닌 비트의 값은 미명시**다 — 같은 소스가 `-O0` 과 `-O2` 에서 **다른 바이트**를 냈다.
- ★★★ **「gcc 와 clang 이 갈린다」는 축이 하나가 아니다** — `-O1` 로 올리자 gcc 가 clang 과 **같아졌다.**
- ★★ **`int x : n` 의 부호는 구현 정의**다. 이 구현에서는 **`signed`** 로 잡혔다(7 → `-1`).
- ★★ **`-funsigned-bitfields` 는 gcc 에서만 먹고, clang 은 경고만 내고 무시**한다(`cc exit=0`).
- ★★ **폭을 넘는 값은 UB 가 아니라 변환**이다 — 조용히 잘린다. 폭을 넘는 **선언**은 에러다.
- ★★ **`&` 와 `sizeof` 가 안 된다** — 비트필드는 **주소가 없다.**
- ★★ **식에 쓰면 승격된다** — 좁으면 `int`, `int` 가 못 담으면 `unsigned int`. 그래서 `0 - 1` 이 **`-1`** 과 **`4294967295`** 로 갈린다.
- ★ **폭 0 은 다음 할당 단위로 밀라는 지시**이고 **이름을 못 가진다.**
- ★ **비트필드가 항상 작지는 않다** — 여기서는 **4 대 5** 였다.

## 관련 자료

- [11번 형제 — 비트 연산과 시프트](../11-bitwise-operations-and-shifts/) — ★★ **직접 선행.**\
  그쪽은 「**손으로 마스크와 시프트를 쓴다**」, 여기는 「**선언으로 컴파일러에게 시킨다**」다.\
  ★ 그 편의 (9)절이 이 주제를 **「있다」까지** 다루었고, **`D3 78` ↔ `D3 08`** 이라는 실측을 남겼다.\
  ★★ **그 실측을 여기서 여섯 벌로 다시 던져 축을 고쳤다**(위 (4)).
- [03번 형제 — 정수 승격과 통상 산술 변환](../03-integer-promotion-and-usual-arithmetic-conversions/) — ★ 승격 규칙 자체의 정본.\
  여기는 「**비트필드도 그 규칙을 받는다**」와 **폭에 따라 결과 타입이 갈린다**는 것만.
- [07번 형제 — `enum` 과 열거 상수](../07-enum-and-enumeration-constants/) — ★ 플래그를 담는 **다른 방식**.\
  그쪽은 **이름 붙은 상수 + 마스크**, 여기는 **선언된 폭**이다. 외부 포맷에는 그쪽이 맞다.
- [22번 형제 — 구조체 패딩·정렬](../22-struct-padding-and-alignment/) — ★★ **패딩 바이트의 값이 미명시**인 것과\
  **미사용 비트의 값이 미명시**인 것은 **같은 성격**이다. 그쪽은 바이트, 여기는 비트다.
- [08번 형제 — `sizeof`·정렬·`offsetof`](../08-sizeof-alignment-and-offsetof/) — ★ 재는 **도구**와 `_Static_assert` 의 정본.\
  ★ `offsetof` 는 **비트필드 멤버에 쓸 수 없다**(주소가 없으니까).
- [21번 형제 — 구조체 선언·초기화·지정 초기자](../21-struct-declaration-initialization-and-designated-initializers/) — 초기자 문법의 정본.
- [23번 형제 — `union` 과 타입 펀닝의 경계](../23-union-and-the-boundary-of-type-punning/) — ★ **비트필드와 `union` 을 겹쳐 쓰는 관용구**의 위험이 그쪽 결론과 맞물린다.
- 목록의 **55번 주제** — 엄격한 앨리어싱. 구조체를 다른 타입으로 읽는 것은 그쪽이 정본이다.
- [`algorithm/29-bit-manipulation/`](../../../../../algorithm/29-bit-manipulation/) — 비트 기법·응용 자체는 그쪽이 정본이다.

## 용어 풀이

> **비트필드(bit-field)** — 구조체 멤버에 비트 단위 폭을 지정한 것.\
> 예: `unsigned kind : 3;` 은 3비트짜리 멤버다. 값은 `0`\~`7`.

> **할당 단위(allocation unit)** — 비트필드를 담으려고 컴파일러가 잡는 한 덩어리.\
> 예: 이 구현에서 `unsigned` 비트필드의 단위는 4바이트라, 8비트만 써도 `sizeof` 가 4 다.

> **미사용 비트(unused bit)** — 할당 단위 안에서 어느 멤버에도 속하지 않는 비트.\
> 예: 12비트를 선언한 32비트 단위에는 20비트가 남고, **그 값은 미명시**다.

> **구현 정의(implementation-defined)** — 구현이 **고르되 문서로 밝혀야** 하는 것.\
> 예: 비트필드를 낮은 비트부터 채우는지는 ABI 문서에 적혀 있다.

> **미명시(unspecified)** — 몇 가지 중 하나이고 **문서화 의무도 없는** 것.\
> 예: 미사용 비트의 값. 같은 컴파일러가 `-O` 만 바꿔도 달라진다.

> **정수 승격(integer promotion)** — 좁은 정수 타입이 식에서 `int`(또는 `unsigned int`)로 올라가는 규칙.\
> 예: `unsigned x : 3` 은 식에서 `int` 가 된다 — `int` 가 `0`\~`7` 을 전부 담을 수 있으니까.

> **폭 0 비트필드(zero-width bit-field)** — `unsigned : 0;` 처럼 폭이 0 인 이름 없는 비트필드.\
> 예: 다음 멤버를 **새 할당 단위**에서 시작하게 만든다. `sizeof` 가 4 에서 8 로 늘었다.

> **읽고-고치고-쓰기(read-modify-write)** — 한 덩어리를 읽어 일부만 바꾼 뒤 다시 쓰는 것.\
> 예: `-O0` 이 비트필드 대입을 이렇게 처리해서 **주변 비트가 살아남았다.**

## 더 들어가면

- ★★ **비트필드와 `union` 을 겹쳐 쓰는 관용구** — `union { uint32_t raw; struct { unsigned a:8; ... } f; };`\
  「한 번에 읽고 비트로 쪼갠다」는 흔한 형태지만, **`raw` 와 `f` 의 대응이 구현 정의**라 이 편의 (3)·(4)가 그대로 걸린다.\
  ★ [23번 형제](../23-union-and-the-boundary-of-type-punning/)의 「**`union` 을 통한 타입 펀닝은 C 에서 허용된다**」와\
  이 편의 「**배치는 구현 정의다**」는 **다른 이야기**다 — 읽는 것은 합법이고, **무엇이 읽히는지가 안 정해진 것**이다.
- ★ **`_Bool b : 1;`** 은 값이 `0`/`1` 로 제한된다 — `unsigned b : 1;` 과 **폭은 같고 의미가 다르다.**\
  ★ 이 문서는 `_Bool` 비트필드를 **던지지 않았다.**
- ★ **`__attribute__((packed))` 와 비트필드** — 할당 단위 자체를 바꿔 **경계를 걸치게** 만드는 확장이다.\
  ★ 이 문서는 **던지지 않았다.** `#pragma pack` 쪽 실측은 [22번 형제](../22-struct-padding-and-alignment/)와 [08번 형제](../08-sizeof-alignment-and-offsetof/)에 있다.
- ★ **폭이 `int` 보다 넓은 비트필드**(`unsigned long long x : 40;`)는 **확장**이다. 표준이 보장하는 것은 `int` 폭까지다.
- ★ **C23** 은 비트필드 규칙을 바꾸지 않았다. `_BitInt(N)` 이라는 **다른 물건**이 생겼을 뿐이고,\
  ★ 이 문서는 `_BitInt` 를 **던지지 않았다**(gcc 13 지원 범위를 확인하지 않았다).
