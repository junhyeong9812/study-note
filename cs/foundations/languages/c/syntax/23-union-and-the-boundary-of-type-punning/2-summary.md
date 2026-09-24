# c/syntax/23 — `union` 과 타입 펀닝의 경계: 「**union 은 동시에 담는 상자가 아니라 같은 바이트를 겹쳐 보는 창이다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — union declaration](https://en.cppreference.com/w/c/language/union) · [cppreference — 객체와 앨리어싱](https://en.cppreference.com/w/c/language/object) · [GCC 13 Optimize Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Optimize-Options.html) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html)\
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙의 진술은 위 문서로, **값·바이트·진단·종료 코드는 전부 실행으로** 접지했다.
> **실행 검증** — 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과 **clang 18.1.3** ·\
> **g++ 13.3.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★★ **엄격한 앨리어싱 실험은 한 수준만 돌리지 않았다** — `-O0`·`-O1`·`-O2`·`-O3` 와 `-fno-strict-aliasing` 까지 **열 벌**이다.\
> ★ 덤프를 결정적으로 만들려고 `s23e.c`·`s23f.c` 는 **`memset` 으로 먼저 채운 뒤** 멤버를 썼다.
> **버전** — `union` 자체는 **C89부터**. **지정 초기자로 멤버를 고르는 것은 C99부터**(`.i = …`).\
> ★ **`union` 을 통한 타입 펀닝이 「허용된다」고 못 박힌 것은 C99 의 결함 보고 처리 이후**이고 **C11\~C17 에도 그대로 있다**.\
> ★★ **C++ 는 이 대목이 다르다** — 이 문서는 그 차이를 **산문 한 줄과 실측 한 벌**로 갈라 둔다.
> ★★ **경계** — **엄격한 앨리어싱 규칙 전체**는 목록의 **55번 주제**가 정본이다.\
> 여기서는 「**`union` 은 되고 포인터 캐스트는 안 되는 경계**」까지만 본다.\
> **`memcpy`·`memcmp` 의 계약**은 목록의 **50번 주제**, **2진 표현·IEEE 754·엔디언 자체**는\
> [`data-representation/`](../../../../data-representation/)가 정본이다 — 여기는 **C 문법이 그것을 어떻게 드러내나**만.\
> **캐스트가 「비트를 바꾸는가 해석을 바꾸는가」** 는 [05번 형제](../05-explicit-casts-and-pointer-conversions/)가 정본이다.\
> **구조체 선언·초기화**는 [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/),\
> **패딩·정렬**은 [22번 형제](../22-struct-padding-and-alignment/), **비트필드**는 [24번 형제](../24-bit-fields/)다.\
> **`restrict` 가 컴파일러에게 무엇을 약속하나**는 목록의 **33번 주제**다.
> 선행 — [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/) · [08번 형제](../08-sizeof-alignment-and-offsetof/) · [05번 형제](../05-explicit-casts-and-pointer-conversions/).

## 한눈에 — 쉽게 말하면

**`union` 은 「여러 개를 한꺼번에 담는 상자」가 아니다.**\
바이트는 **한 벌뿐**이고, 멤버들은 그 한 벌을 **각자의 안경으로 들여다보는 창**이다.

그래서 이 주제의 질문은 늘 둘이다 — 「**지금 그 바이트를 누가 마지막으로 썼나**」와\
「**다른 창으로 들여다보는 것이 허용되나**」.

| 비유 | 실체 |
|---|---|
| **한 칸짜리 방을 여러 사람이 번갈아 쓴다** | `union` — 멤버들이 **같은 바이트를 공유**한다 |
| 방에 **마지막으로 들어간 사람**만 주인이다 | **마지막에 쓴 멤버**만 뜻이 있다 |
| 방 크기는 **가장 덩치 큰 사람**에 맞춘다 | `sizeof` 는 가장 큰 멤버를 담을 만큼 |
| 문틀 규격은 **가장 까다로운 사람**에 맞춘다 | `_Alignof` 는 가장 엄한 멤버의 정렬 |
| 같은 방을 **다른 창으로 들여다본다** | **타입 펀닝** — 같은 바이트를 다른 타입으로 읽기 |
| 창으로 보는 것은 되는데 **벽을 뚫으면 안 된다** | `union` 을 거치면 되고 **포인터 캐스트는 UB** |
| 벽을 뚫어도 **경비원은 대개 안 온다** | 경고도 sanitizer 도 **거의 침묵한다** |

```text
   struct S { int i; char c[4]; double d; };      sizeof 16
   +--------+--------+----------------+
   |   i    |  c[4]  |       d        |     i@0  c@4  d@8
   +--------+--------+----------------+
   0        4        8                16

   union U { int i; char c[4]; double d; };       sizeof 8
   +----------------+
   |       d        |     d 는 여덟 칸 전부를 본다
   +--------+-------+
   |   i    |       |     i 는 앞 네 칸만
   +--------+-------+
   |  c[4]  |       |     c 도 앞 네 칸만
   +--------+-------+
   0        4       8     ★ 셋 다 offset 0 에서 시작한다
```

- **struct 는 자리를 나눠 갖고, union 은 자리를 겹쳐 쓴다.** 그림의 차이가 전부다.
- 그래서 union 에서는 **`offsetof` 가 전부 0** 이고, **한 멤버에 쓰면 다른 멤버가 바뀐다.**

> **타입 펀닝(type punning)** — 같은 바이트를 **선언된 타입이 아닌 다른 타입으로** 읽어 보는 것.\
> 예: `float` 로 쓴 네 바이트를 `uint32_t` 로 읽어 지수·가수 비트를 보는 것.

> **활성 멤버(active member)** — 「지금 그 바이트를 차지하고 있는 멤버」라는 모형.\
> 예: `u.f = 1.5f` 를 하면 활성 멤버는 `f` 다. ★ **C 에는 이 말이 없고 C++ 에 있다** — 그 차이가 이 주제의 끝자락이다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `union` 의 **크기와 정렬**은 누가 어떤 규칙으로 정하고, **멤버들은 어디서 시작**하는가.
2. **마지막에 쓴 멤버가 아닌 멤버를 읽으면** 무엇이 나오고, 그것이 C 에서 **허용되는가.**
3. 같은 일을 **포인터 캐스트로 하면** 무엇이 달라지는가 — **어디서 갈리고, 도구는 무엇을 말해 주는가.**

## 동작 방식

### (1) ★★ 크기·정렬·오프셋 — 같은 멤버를 struct 로 두었을 때와 대 본다

**언제 쓰나** — union 을 선언할 때마다. 「이 상자가 몇 바이트짜리인가」를 먼저 알아야 한다.

```c
/* s23a.c */
#include <stdio.h>
#include <stddef.h>

union U { int i; char c[4]; double d; };
struct S { int i; char c[4]; double d; };   /* 같은 멤버를 struct 로 */

int main(void) {
    printf("union  sizeof=%zu _Alignof=%zu   offsets: i=%zu c=%zu d=%zu\n",
           sizeof(union U), _Alignof(union U),
           offsetof(union U, i), offsetof(union U, c), offsetof(union U, d));
    printf("struct sizeof=%zu _Alignof=%zu   offsets: i=%zu c=%zu d=%zu\n",
           sizeof(struct S), _Alignof(struct S),
           offsetof(struct S, i), offsetof(struct S, c), offsetof(struct S, d));

    union U u;
    u.i = 0x41424344;                       /* 마지막에 쓴 멤버 = i */
    printf("\nu.i = 0x%08x 를 쓴 뒤 바이트를 보면 : ", u.i);
    for (int k = 0; k < 4; k++) printf("%02x ", (unsigned char)u.c[k]);
    printf("  <- ★ 엔디언이 드러난다\n");
    printf("u.c[0]='%c' u.c[3]='%c'\n", u.c[0], u.c[3]);

    u.d = 1.0;                              /* 이제 마지막에 쓴 멤버 = d */
    printf("\nu.d = 1.0 을 쓰고 나면 u.i 는 %d (0x%08x) — i 는 더 이상 의미가 없다\n",
           u.i, (unsigned)u.i);
    printf("전체 8바이트 : ");
    const unsigned char *b = (const unsigned char *)&u;
    for (size_t k = 0; k < sizeof u; k++) printf("%02x ", b[k]);
    printf("\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s23a.c -o x ; ./x (cc exit=0 · run exit=0) =====
union  sizeof=8 _Alignof=8   offsets: i=0 c=0 d=0
struct sizeof=16 _Alignof=8   offsets: i=0 c=4 d=8

u.i = 0x41424344 를 쓴 뒤 바이트를 보면 : 44 43 42 41   <- ★ 엔디언이 드러난다
u.c[0]='D' u.c[3]='A'

u.d = 1.0 을 쓰고 나면 u.i 는 0 (0x00000000) — i 는 더 이상 의미가 없다
전체 8바이트 : 00 00 00 00 00 00 f0 3f 
```

```text
   union U 에 u.i = 0x41424344 를 쓴 직후

   offset  0    1    2    3    4    5    6    7
         +----+----+----+----+----+----+----+----+
         | 44 | 43 | 42 | 41 | ?? | ?? | ?? | ?? |
         +----+----+----+----+----+----+----+----+
          'D'  'C'  'B'  'A'   <- ★ 리틀 엔디언이라 거꾸로 보인다
         |<----- i 가 보는 네 칸 ----->|
         |<----- c[4] 가 보는 네 칸 -->|
         |<--------------- d 가 보는 여덟 칸 --------------->|
```

그림 해설 (한 단계씩).

- **`sizeof(union U)` 는 8** 이다 — 가장 큰 멤버 `double` 을 담을 만큼. 같은 멤버를 struct 로 두면 **16** 이다.
- **`_Alignof` 는 8** 이다 — 가장 엄한 멤버의 정렬을 따른다.
- ★ **모든 멤버의 `offsetof` 가 0** 이다. struct 쪽은 `0 / 4 / 8` 로 갈린다.
- ★★ **`0x41424344` 를 넣고 바이트를 보면 `44 43 42 41`** 이다 — **엔디언이 여기서 드러난다.**\
  `u.c[0]` 이 `'D'` 이고 `u.c[3]` 이 `'A'` 다. 이것은 **구현 정의**이지 표준이 정한 것이 아니다.
- ★★ 그 뒤 **`u.d = 1.0` 을 쓰면 `u.i` 가 0** 이 된다. `1.0` 의 여덟 바이트가 `00 00 00 00 00 00 f0 3f` 라\
  **앞 네 칸이 전부 0 이 되었기 때문**이다. **`i` 라는 멤버가 사라진 것이 아니라 바이트가 덮인 것**이다.

비용 — 공간은 **가장 큰 멤버 하나 몫**만 쓴다. 대신 **「지금 누가 유효한가」를 프로그램이 따로 기억**해야 한다.

### (2) ★★★ 타입 펀닝 — `float` 의 비트를 눈으로 본다

**언제 쓰나** — 부동소수의 비트 패턴을 보거나, 파일·패킷의 네 바이트를 수로 해석할 때.

```c
/* s23b.c */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

union FB { float f; uint32_t u; };

static void bits(uint32_t u) {
    for (int k = 31; k >= 0; k--) {
        putchar((u >> k) & 1 ? '1' : '0');
        if (k == 31 || k == 23) putchar(' ');
    }
}

int main(void) {
    union FB v = { .f = 1.5f };            /* float 를 넣고 */
    printf("f = %.6f  ->  u = 0x%08x\n", v.f, v.u);   /* uint32 로 읽는다 */
    printf("  부호 지수      가수\n  ");
    bits(v.u);
    printf("\n");

    uint32_t m;
    memcpy(&m, &v.f, sizeof m);            /* 같은 일을 memcpy 로 */
    printf("memcpy 로 읽으면 : 0x%08x   (union 과 같은가: %d)\n", m, m == v.u);

    v.u = 0x40490fdb;                      /* 거꾸로 — 비트를 넣고 float 로 읽는다 */
    printf("\nu = 0x40490fdb  ->  f = %.7f\n", v.f);

    union FB nan = { .u = 0x7fc00000 };
    printf("u = 0x7fc00000 ->  f = %f\n", nan.f);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s23b.c -o x ; ./x (cc exit=0 · run exit=0) =====
f = 1.500000  ->  u = 0x3fc00000
  부호 지수      가수
  0 01111111 10000000000000000000000
memcpy 로 읽으면 : 0x3fc00000   (union 과 같은가: 1)

u = 0x40490fdb  ->  f = 3.1415927
u = 0x7fc00000 ->  f = nan
```

```text
   union FB { float f; uint32_t u; };      v.f = 1.5f

     부호   지수 (8)      가수 (23)
     +---+ +--------+ +-----------------------+
     | 0 | |01111111| |1000…0                 |      = 0x3fc00000
     +---+ +--------+ +-----------------------+
      ^      ^          ^
      양수   127 = 지수 0    1.1(2진) = 1.5

   같은 네 바이트를 두 창으로 본다
   +----+----+----+----+
   | 00 | 00 | c0 | 3f |      <- 메모리 (리틀 엔디언)
   +----+----+----+----+
     f 로 보면 1.5
     u 로 보면 0x3fc00000
```

그림 해설 (한 단계씩).

- **`f` 에 쓰고 `u` 로 읽었다.** 이것이 **union 을 통한 타입 펀닝**이고 **C 에서는 허용된다.**
- ★ **거꾸로도 된다** — `u = 0x40490fdb` 를 넣고 `f` 로 읽으면 **3.1415927** 이다.
- ★ `u = 0x7fc00000` 은 **`nan`** 으로 읽힌다. 「수가 아닌 비트 패턴」도 그대로 들어간다.
- ★★ **같은 일을 `memcpy` 로 해도 값이 같았다** — 블록의 `(union 과 같은가: 1)` 이 그 대조다.

### (3) ★★ `memcpy` 와의 차이 — **값은 같고 규칙이 다르다**

**언제 쓰나** — 「union 으로 할까 `memcpy` 로 할까」를 고를 때.

```text
   (가) union 을 거친다                 (나) memcpy 로 옮긴다
   +----------------+                  +--------+        +--------+
   | union FB { f;u }|                 |  float |  복사  | uint32 |
   +----------------+                  +--------+ -----> +--------+
   같은 바이트를 두 이름으로 본다          바이트를 ★ 다른 객체로 옮긴다

   C   : (가) 허용 · (나) 허용
   C++ : (가) ★ 활성 멤버가 아닌 것을 읽는 것 · (나) 허용
   어느 언어든 (나)는 안전하다  ->  이식할 코드에는 (나)
```

- ★ **실측에서 두 값은 같았다**(`0x3fc00000`). **차이는 출력이 아니라 규칙에 있다.**
- ★★ **그래서 「돌려 봤더니 같더라」가 근거가 못 되는 자리**다 — 같은 것이 당연하고, 갈리는 것은 **언어가 무엇을 약속했나**다.
- 최적화가 지워 주므로 `memcpy` 쪽이 **느리지도 않다**(그 확인은 이 문서에서 **재지 않았다**).

### (4) ★★★ 포인터 캐스트는 다르다 — **최적화 수준에서 갈린다** (이 주제의 본체)

**언제 쓰나** — `*(float *)&x` 같은 코드를 보거나 쓸 때.

```c
/* s23d.c */
#include <stdio.h>
#include <stdint.h>

/* 같은 메모리를 unsigned 와 float 두 타입으로 접근한다 — 엄격한 앨리어싱 위반 */
static unsigned punned(unsigned *u, float *f) {
    *u = 1;
    *f = 0.0f;        /* 위의 *u 와 같은 바이트를 덮어쓴다 */
    return *u;        /* 컴파일러가 「안 겹친다」고 믿으면 1 을 그대로 돌려준다 */
}

int main(void) {
    unsigned x = 0;
    unsigned r = punned(&x, (float *)&x);
    printf("반환값 = %u · 메모리의 실제 값 = %u\n", r, x);
    return 0;
}
```

```text
===== 엄격한 앨리어싱 위반을 최적화 수준별로 — 한 줄 = 한 벌 (exit=0) =====
gcc   -O0                    : 반환값 = 0 · 메모리의 실제 값 = 0
gcc   -O1                    : 반환값 = 0 · 메모리의 실제 값 = 0
gcc   -O2                    : 반환값 = 1 · 메모리의 실제 값 = 0
gcc   -O3                    : 반환값 = 1 · 메모리의 실제 값 = 0
gcc   -O2 -fno-strict-aliasing : 반환값 = 0 · 메모리의 실제 값 = 0
clang -O0                    : 반환값 = 0 · 메모리의 실제 값 = 0
clang -O1                    : 반환값 = 1 · 메모리의 실제 값 = 0
clang -O2                    : 반환값 = 1 · 메모리의 실제 값 = 0
clang -O3                    : 반환값 = 1 · 메모리의 실제 값 = 0
clang -O2 -fno-strict-aliasing : 반환값 = 0 · 메모리의 실제 값 = 0
```

```text
   punned(&x, (float *)&x)

   소스가 시키는 것                   컴파일러가 믿는 것 (엄격한 앨리어싱)
   +---------------------+            +------------------------------+
   | *u = 1;             |            | u 와 f 는 타입이 다르다       |
   | *f = 0.0f;  (같은 칸)|            | -> ★ 겹칠 리 없다             |
   | return *u;          |            | -> *u 는 아직 1 이다          |
   +---------------------+            +------------------------------+
            |                                       |
            v                                       v
      메모리의 실제 값 0                        반환값 ★ 1

   gcc   : -O0 0 · -O1 0 · ★ -O2 부터 1
   clang : -O0 0 · ★ -O1 부터 1
   둘 다 : -fno-strict-aliasing 이면 0 으로 돌아온다
```

그림 해설 (한 단계씩).

- **메모리의 실제 값은 열 벌 전부 0** 이다. 갈린 것은 **반환값**뿐이다.
- ★★ **갈리는 자리가 컴파일러마다 다르다** — gcc 는 `-O2` 부터, **clang 은 `-O1` 부터** 1 이 된다.\
  「`-O2` 에서만 조심하면 된다」가 **틀렸다는 실측**이다.
- ★ **`-fno-strict-aliasing` 을 주면 둘 다 0** 으로 돌아온다. **플래그로 끌 수 있는 최적화**라는 뜻이고,\
  **끄지 않은 코드는 UB 를 깔고 있다**는 뜻이기도 하다.
- ★★★ **여기가 `union` 과 갈리는 자리다.** 같은 「네 바이트를 두 타입으로 본다」인데,\
  **union 을 거치면 허용**이고 **포인터 캐스트는 UB** 다. 정본은 목록의 **55번 주제**.

### (4-나) ★★ 그 위험을 도구에게 물어보면 — **거의 침묵한다**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -Wstrict-aliasing=2 -O2 s23d.c -o x (cc exit=0) =====
s23d.c: In function ‘main’:
s23d.c:13:38: warning: dereferencing type-punned pointer will break strict-aliasing rules [-Wstrict-aliasing]
   13 |     unsigned r = punned(&x, (float *)&x);
      |                                      ^~
```

```text
===== 도구가 잡나 — 경고 수(grep -c 'warning:')와 sanitizer 실행 결과 (exit=0) =====
gcc   -O0 -Wstrict-aliasing=2 : warning: 0건
gcc   -O2 -Wstrict-aliasing=2 : warning: 1건
clang -O0 -Wstrict-aliasing=2 : warning: 0건
clang -O2 -Wstrict-aliasing=2 : warning: 0건
gcc   -O2 -fsanitize=undefined,address : 반환값 = 1 · 메모리의 실제 값 = 0 (run exit=0)
```

그림 해설.

- ★ **gcc 는 `-Wstrict-aliasing=2` 로 `-O2` 에서만 1건**을 낸다 — **`-O0` 에서는 0건**이다.\
  **경고가 최적화 분석 위에 얹혀 있어** 최적화를 안 켜면 볼 수가 없다.
- ★★★ **clang 은 `-O0`·`-O2` 둘 다 0건**이다. **정작 `-O1` 부터 깨지는 쪽이 clang 이다** —\
  「**가장 일찍 깨지는 컴파일러가 가장 조용하다**」.
- ★★★ **UBSan + ASan 을 둘 다 켜도 아무 말이 없다**(`run exit=0`). 출력은 **깨진 값 1 그대로**다.\
  **엄격한 앨리어싱 위반은 실행 시점에 「잘못된 주소」도 「잘못된 값의 연산」도 아니기 때문**이다.

### (5) ★★ 공통 초기 시퀀스 — 앞머리가 같으면 건너 읽어도 된다

**언제 쓰나** — 태그를 앞에 둔 여러 구조체를 한 union 으로 묶어 「태그를 먼저 읽는」 형태를 쓸 때.

```c
/* s23e.c */
#include <stdio.h>
#include <string.h>

struct A { int tag; int    x; };       /* 앞머리 int tag 가 공통 */
struct B { int tag; double y; };
union V { struct A a; struct B b; };   /* ★ 한 union 안에 보여야 규칙이 선다 */

static void dump(const char *tag, const union V *v) {
    const unsigned char *b = (const unsigned char *)v;
    printf("%-14s", tag);
    for (size_t k = 0; k < sizeof *v; k++) printf(" %02x", b[k]);
    printf("\n");
}

int main(void) {
    union V v;
    memset(&v, 0, sizeof v);                       /* 덤프를 결정적으로 */
    v.a = (struct A){ .tag = 7, .x = 42 };
    dump("a 로 쓴 뒤", &v);
    printf("a 로 쓰고 b 로 읽기 : v.b.tag = %d   <- ★ 공통 초기 시퀀스라 허용된다\n", v.b.tag);

    memset(&v, 0, sizeof v);
    v.b = (struct B){ .tag = 9, .y = 2.5 };
    dump("b 로 쓴 뒤", &v);
    printf("b 로 쓰고 a 로 읽기 : v.a.tag = %d\n", v.a.tag);
    printf("v.a.x 를 읽으면 = %d  <- 공통 부분이 아니다 (B 에서는 패딩 자리다)\n", v.a.x);

    printf("\nsizeof A=%zu B=%zu V=%zu · offsetof(B,y)=%zu\n",
           sizeof(struct A), sizeof(struct B), sizeof(union V),
           (size_t)((char *)&v.b.y - (char *)&v.b));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s23e.c -o x ; ./x (cc exit=0 · run exit=0) =====
a 로 쓴 뒤  07 00 00 00 2a 00 00 00 00 00 00 00 00 00 00 00
a 로 쓰고 b 로 읽기 : v.b.tag = 7   <- ★ 공통 초기 시퀀스라 허용된다
b 로 쓴 뒤  09 00 00 00 00 00 00 00 00 00 00 00 00 00 04 40
b 로 쓰고 a 로 읽기 : v.a.tag = 9
v.a.x 를 읽으면 = 0  <- 공통 부분이 아니다 (B 에서는 패딩 자리다)

sizeof A=8 B=16 V=16 · offsetof(B,y)=8
```

```text
   union V { struct A a; struct B b; };

   struct A { int tag; int    x; }      struct B { int tag; double y; }
   +------+------+                      +------+------+----------------+
   | tag  |  x   |                      | tag  | 패딩 |       y        |
   +------+------+                      +------+------+----------------+
   0      4      8                      0      4      8               16
   |<-공통->|                            |<-공통->|

   ★ 앞머리가 「같은 타입이 같은 차례로」 있는 만큼이 공통 초기 시퀀스다
   ★ 그 union 선언이 보이는 곳에서만 규칙이 선다
```

그림 해설 (한 단계씩).

- **`a` 로 쓰고 `b.tag` 를 읽어 7 이 나왔다.** 거꾸로 `b` 로 쓰고 `a.tag` 를 읽어 9 가 나왔다.\
  ★ 이것이 **공통 초기 시퀀스 규칙**이고, **마지막에 쓴 멤버가 아닌 것을 읽는데도 뜻이 있는 유일한 자리**다.
- ★ **공통이 아닌 자리는 다르다** — `b` 로 쓴 뒤 `v.a.x` 는 0 이었다.\
  `struct B` 에서 그 네 바이트는 **`y` 를 8 에 놓으려고 생긴 패딩**이기 때문이다(`offsetof(B,y)=8`).\
  **패딩 자리를 읽은 값에는 뜻이 없다.** 패딩 이야기의 정본은 [22번 형제](../22-struct-padding-and-alignment/)다.
- ★ **`int tag` 와 `short tag` 는 공통 초기 시퀀스가 아니다.** 「앞에 있다」가 아니라 **「같은 타입이 같은 차례로」** 다.
- ★★ **규칙이 서려면 그 union 선언이 보여야 한다.** 두 구조체만 따로 알고 포인터로 건너뛰는 것은 이 규칙이 아니다.

### (6) ★ 초기화 — 첫 멤버가 기본이고, 나머지 바이트는 미명시다

**언제 쓰나** — union 을 선언과 동시에 채울 때.

```c
/* s23f.c */
#include <stdio.h>
#include <string.h>

union U { char c; int i; double d; };

static void dump(const char *tag, const union U *u) {
    const unsigned char *b = (const unsigned char *)u;
    printf("%-16s", tag);
    for (size_t k = 0; k < sizeof *u; k++) printf(" %02x", b[k]);
    printf("\n");
}

int main(void) {
    union U a = { 'A' };              /* 첫 멤버가 초기화된다 */
    union U b = { .i = 0x41424344 };  /* 지정 초기자로 고른다 */
    union U c = { 0 };
    union U d;
    memset(&d, 0xAA, sizeof d);
    d.c = 'A';                        /* 멤버 하나만 쓴다 */

    printf("sizeof(union U) = %zu · _Alignof = %zu\n\n", sizeof a, _Alignof(union U));
    dump("a = { 'A' }", &a);
    dump("b = { .i = X }", &b);
    dump("c = { 0 }", &c);
    dump("d: memset+d.c", &d);
    printf("\n★ d 의 뒤 7바이트는 「미명시」다 — 멤버 하나를 써도 나머지는 정해지지 않는다\n");
    printf("a.c = '%c' · b.i = 0x%08x · c.c = %d\n", a.c, b.i, c.c);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s23f.c -o x ; ./x (cc exit=0 · run exit=0) =====
sizeof(union U) = 8 · _Alignof = 8

a = { 'A' }      41 00 00 00 00 00 00 00
b = { .i = X }   44 43 42 41 00 00 00 00
c = { 0 }        00 00 00 00 00 00 00 00
d: memset+d.c    41 aa aa aa aa aa aa aa

★ d 의 뒤 7바이트는 「미명시」다 — 멤버 하나를 써도 나머지는 정해지지 않는다
a.c = 'A' · b.i = 0x41424344 · c.c = 0
```

```text
   union U { char c; int i; double d; };          sizeof 8

   a = { 'A' }        41 | 00 00 00 00 00 00 00     ★ 첫 멤버 c 가 초기화된다
   b = { .i = … }     44 43 42 41 | 00 00 00 00     ★ 지정 초기자로 i 를 고른다
   c = { 0 }          00 00 00 00 00 00 00 00
   d  memset(0xAA) 뒤 d.c = 'A'
                      41 | aa aa aa aa aa aa aa     ★ 뒤 일곱 칸은 「미명시」다
                       ^   ^^^^^^^^^^^^^^^^^^^^
                       쓴 자리   안 쓴 자리 — 값이 정해지지 않는다
```

그림 해설 (한 단계씩).

- **초기자를 하나만 쓰면 첫 멤버**가 초기화된다. `a = { 'A' }` 가 `c` 를 채운 것이 그것이다.
- ★ **다른 멤버를 고르려면 지정 초기자**가 필요하다(`{ .i = … }`). **C99부터**다.
- ★★ **`d` 의 뒤 일곱 칸이 `aa` 로 남았다** — 멤버 하나를 썼다고 나머지가 0 이 되지 않는다.\
  **「미명시」 층**이다. `a`·`b`·`c` 에서 뒤가 0 으로 보이는 것은 **이 컴파일러가 그렇게 한 것**이지 보장이 아니다.

### (7) ★★ C++ 와 갈리는 자리 — 실행이 아니라 **모형**이 다르다

**언제 쓰나** — 같은 헤더를 C 와 C++ 양쪽에서 쓸 때.

```cpp
/* s23g.cpp */
#include <cstdio>
#include <cstdint>

union FB { float f; std::uint32_t u; };

int main() {
    FB v;
    v.f = 1.5f;                 /* 활성 멤버는 f 다 */
    std::printf("v.u = 0x%08x   <- C++ 에서는 비활성 멤버 읽기다\n", v.u);
    return 0;
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -O2 s23g.cpp -o x ; ./x (cc exit=0 · run exit=0) =====
v.u = 0x3fc00000   <- C++ 에서는 비활성 멤버 읽기다
```

- ★ **값은 C 와 똑같이 `0x3fc00000`** 이 나왔다(g++ `-O2`). **실행 결과로는 안 갈린다.**
- ★★ **갈린 것은 규칙이다.** C 는 「**다른 멤버를 읽으면 바이트를 그 타입으로 다시 해석한다**」고 정해 두었고,\
  C++ 는 「**union 에는 활성 멤버가 하나뿐**」이라는 모형이라 **활성이 아닌 멤버를 읽는 것이 UB** 다.
- ★★ **그 모형이 실제로 강제되는 것**은 다른 자리에서 보인다 — **자명하지 않은 타입을 멤버로 넣어 보면** 된다.

```cpp
/* s23h.cpp */
#include <string>

union U {
    int i;
    std::string s;      /* 자명하지 않은 생성자를 가진 멤버 */
};

int main() { U u; u.i = 1; return u.i; }
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic s23h.cpp -o x (cc exit=1) =====
s23h.cpp: In function ‘int main()’:
s23h.cpp:8:16: error: use of deleted function ‘U::U()’
    8 | int main() { U u; u.i = 1; return u.i; }
      |                ^
s23h.cpp:3:7: note: ‘U::U()’ is implicitly deleted because the default definition would be ill-formed:
    3 | union U {
      |       ^
s23h.cpp:5:17: error: union member ‘U::s’ with non-trivial ‘std::__cxx11::basic_string<_CharT, _Traits, _Alloc>::basic_string() [with _CharT = char; _Traits = std::char_traits<char>; _Alloc = std::allocator<char>]’
    5 |     std::string s;      /* 자명하지 않은 생성자를 가진 멤버 */
      |                 ^
s23h.cpp:8:16: error: use of deleted function ‘U::~U()’
    8 | int main() { U u; u.i = 1; return u.i; }
      |                ^
s23h.cpp:3:7: note: ‘U::~U()’ is implicitly deleted because the default definition would be ill-formed:
    3 | union U {
      |       ^
s23h.cpp:5:17: error: union member ‘U::s’ with non-trivial ‘std::__cxx11::basic_string<_CharT, _Traits, _Alloc>::~basic_string() [with _CharT = char; _Traits = std::char_traits<char>; _Alloc = std::allocator<char>]’
    5 |     std::string s;      /* 자명하지 않은 생성자를 가진 멤버 */
      |                 ^
```

```text
   C 의 모형                              C++ 의 모형
   +--------------------------+           +----------------------------+
   | 바이트가 한 벌 있다       |           | ★ 활성 멤버가 하나 있다      |
   | 멤버는 그 바이트를        |           | 다른 멤버로 바꾸려면         |
   | 다시 해석하는 이름이다    |           | 수명을 끝내고 시작해야 한다  |
   +--------------------------+           +----------------------------+
   -> 펀닝이 허용된다                      -> 생성자·소멸자가 필요해지고
                                              자명하지 않으면 ★ 컴파일이 막힌다
```

- ★★★ **g++ 는 `cc exit=1` 로 막는다.** 「`use of deleted function ‘U::U()’`」와\
  「`union member ‘U::s’ with non-trivial …`」 두 갈래다. **C 에는 이런 진단이 있을 수 없다** — 생성자가 없으니까.
- ★ **C++ 의 `union`·활성 멤버·`std::bit_cast` 는 C++ 갈래가 정본이다.**\
  여기서는 **「C 에서 허용되는 것이 C++ 에서 자동으로 허용되지는 않는다」** 한 줄만 못 박는다.

## 문법 — 형태와 규칙

### 형태

```text
/* 선언 */
union U { int i; char c[4]; double d; };

/* 초기화 — 초기자가 하나면 첫 멤버 */
union U a = { 5 };
union U b = { .d = 1.5 };          /* C99 — 지정 초기자로 멤버를 고른다 */
union U z = { 0 };

/* 쓰고 읽기 — 마지막에 쓴 멤버가 유효하다 */
a.i = 7;
printf("%d\n", a.i);

/* 타입 펀닝 — C 에서 허용되는 형태 */
union { float f; uint32_t u; } v;
v.f = 1.5f;
uint32_t bits = v.u;               /* 다른 멤버로 읽는다 */

/* 이식 가능한 형태 — 어느 언어에서도 안전하다 */
uint32_t bits2;
memcpy(&bits2, &v.f, sizeof bits2);

/* 태그를 앞에 둔 묶음 — 공통 초기 시퀀스 */
struct A { int tag; int    x; };
struct B { int tag; double y; };
union  V { struct A a; struct B b; };
```

### 금지 사례 — 어느 것이 무슨 층인가

```text
/* (1) UB — 포인터 캐스트로 다른 타입처럼 읽기 (엄격한 앨리어싱 위반) */
unsigned x = 1;
float f = *(float *)&x;

/* (2) 미명시 — 작은 멤버를 쓴 뒤 남은 바이트를 읽고 판단에 쓰기 */
union U u;
u.c = 'A';
memcmp(&u, &other, sizeof u);      /* 안 쓴 일곱 칸이 끼어든다 */

/* (3) 구현 정의 — 바이트 차례에 기대기 */
union { uint32_t u; unsigned char b[4]; } e = { .u = 1 };
if (e.b[0] == 1) { /* 리틀 엔디언 — 이 머신에서는 참이지만 보장이 아니다 */ }

/* (4) 컴파일 에러 — union 에도 == 는 없다 */
/* if (a == b) {}       error: invalid operands to binary == */

/* (5) C 에서는 되고 C++ 에서는 막히는 것 */
/* union { int i; std::string s; };   g++ 가 생성자·소멸자를 지워 cc exit=1 */
```

### 규칙 불릿

- **모든 멤버가 offset 0** 에서 시작한다. `sizeof` 는 **가장 큰 멤버를 담을 만큼**, `_Alignof` 는 **가장 엄한 멤버**를 따른다.
- **`sizeof` 가 가장 큰 멤버보다 클 수 있다** — 정렬의 배수여야 하므로 **끝에 패딩**이 붙는다.
- **초기자 목록이 하나면 첫 멤버**를 초기화한다. **다른 멤버는 지정 초기자로**(C99부터).
- **마지막에 쓴 멤버**가 유효하다. **다른 멤버를 읽는 것은 바이트를 그 타입으로 다시 해석하는 것**이고 **C 는 허용**한다.
- **공통 초기 시퀀스**는 예외다 — 같은 union 이 보이는 곳에서 **앞머리가 같은 타입·같은 차례인 만큼**은 건너 읽어도 된다.
- **포인터 캐스트로 같은 일을 하면 UB** 다. 이식할 코드에는 **`memcpy`** 를 쓴다.
- **union 에 `==` 는 없다.** struct 와 같다 — 비교하려면 **지금 유효한 멤버를 골라** 비교한다.
- **`union` 은 「어느 멤버가 유효한지」를 기억하지 않는다.** 그것은 **프로그램이 태그로 따로 들고 있어야** 한다.

## 어디서 틀리나

### 1. ★★★ 「union 이니까 두 값을 같이 담을 수 있겠지」

- **바이트가 한 벌뿐**이다. `u.i` 를 쓰고 `u.d` 를 쓰면 **`u.i` 는 덮인다.**
- 실측에서 `u.d = 1.0` 뒤 `u.i` 가 **0** 이 되었다. **사라진 것이 아니라 덮인 것**이다.
- ★ 두 값을 같이 담고 싶으면 **struct** 다. union 은 **「둘 중 하나」** 를 담는 도구다.

### 2. ★★★ 「union 이든 포인터 캐스트든 같은 일 아닌가」

- **아니다.** union 은 허용되고 **포인터 캐스트는 UB** 다.
- 실측에서 포인터 캐스트 쪽은 **gcc `-O2`·clang `-O1` 부터 반환값이 갈렸다.**\
  **메모리의 실제 값은 열 벌 전부 0** 인데 **반환값만 1** 이 되었다.
- ★ 「내 코드에서는 잘 돌던데」는 **`-O` 를 하나만 돌려 본 것**이다.

### 3. ★★★ 「경고가 없으니 안전하겠지」

- **clang 은 `-Wstrict-aliasing=2` 를 줘도 0건**이었다 — **가장 일찍 깨지는 쪽이 가장 조용하다.**
- **gcc 도 `-O0` 에서는 0건**이다. **경고를 보려면 최적화를 켜야** 한다.
- ★★ **UBSan + ASan 도 아무 말이 없다.** 이 위반은 **실행 시점에 관찰할 사건이 없다** — 컴파일러가 이미 다르게 번역했다.

### 4. ★★ 「멤버 하나를 썼으니 나머지는 0 이겠지」

- 실측에서 0xAA 로 채운 union 에 `d.c = 'A'` 만 쓰자 **뒤 일곱 칸이 `aa` 로 남았다.**
- 「**미명시**」 층이라 **컴파일러가 0 으로 만들어 줄 의무가 없다.**
- ★ 0 이 필요하면 **`= { 0 }` 이나 `memset`** 을 직접 쓴다.

### 5. ★★ 「`memcmp` 로 두 union 을 비교하면 되겠지」

- **안 쓴 바이트가 끼어든다.** 위의 `d` 처럼 뒤 일곱 칸이 `aa` 면 **멤버가 같아도 다르다고 나온다.**
- 구조체에서 같은 함정을 [22번 형제](../22-struct-padding-and-alignment/)가 **패딩으로** 보여 준다 — 원인은 같다.
- ★ **지금 유효한 멤버를 골라** 비교한다.

### 6. ★★ 「앞머리가 같으니 건너 읽어도 되겠지」

- **「앞에 있다」가 아니라 「같은 타입이 같은 차례로」** 다. `int tag` 와 `short tag` 는 공통 초기 시퀀스가 **아니다.**
- 실측에서 `b` 로 쓰고 `v.a.x` 를 읽으니 0 이었는데, 그 자리는 **`struct B` 의 패딩**이다. **뜻이 없다.**
- ★ 규칙이 서려면 **그 union 선언이 보이는 곳**이어야 한다.

### 7. ★★ 「C 에서 되니 C++ 에서도 되겠지」

- **실행 결과는 같았지만**(g++ `-O2` 도 `0x3fc00000`) **규칙이 다르다.**
- C++ 는 **활성 멤버 모형**이라 자명하지 않은 타입을 멤버로 넣으면 **컴파일이 막힌다**(실측 `cc exit=1`).
- ★ 두 언어에서 같이 쓸 코드에는 **`memcpy`** 를 쓴다.

### 8. ★ 「`b[0] == 1` 로 엔디언을 보면 되니 그 가정을 코드에 박아도 되겠지」

- **엔디언은 구현 정의**다. 검사 자체는 union 으로 할 수 있지만 **결과에 기대어 배치를 박으면 이식이 깨진다.**
- ★ 바이트 차례가 걸린 곳에서는 **한 바이트씩 조립·분해**한다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 UB 와 구현 정의가 맞닿는 자리가 본체다** — **같은 「네 바이트를 두 타입으로 보기」가\
union 을 거치면 허용이고 포인터 캐스트면 UB** 다. 그 경계가 이 편의 전부다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | **모든 멤버가 offset 0** · `sizeof` 는 **가장 큰 멤버를 담을 만큼** · `_Alignof` 는 **가장 엄한 멤버** · 초기자 하나면 **첫 멤버** · **지정 초기자로 멤버 선택**(C99) · **공통 초기 시퀀스 규칙** · ★ **union 을 통해 다른 멤버를 읽는 것이 허용되는 것**(C) · union 에 `==` 가 없는 것 | `offsetof` 셋 다 0 · `sizeof` 8 대 struct 16 · `v.b.tag` 가 7·9 · 초기화 네 벌의 바이트 격자 | — |
| **조건부 표준** | 매크로가 정의될 때만 | ★ **해당 없음** — union 과 펀닝에는 매크로로 켜고 끄는 보장이 없다 | — | — |
| **구현 정의** | 문서화 의무가 있다 | **바이트 차례**(`44 43 42 41`) · `float` 가 **IEEE 754 단정밀도**인 것 · `sizeof(union U)`=8·`_Alignof`=8 · `double 1.0` 이 `00 … f0 3f` 인 것 · `struct B` 의 `tag` 뒤 4바이트 패딩 | 바이트 덤프 · 비트 격자 · `offsetof(B,y)=8` | ★ **경고가 한 건도 없다.** 바이트 차례를 **찍어 봐야만** 안다 |
| **미명시** | 몇 가지 중 하나 · 문서화 의무도 없다 | ★★ **쓴 멤버보다 뒤에 남은 바이트의 값** · 초기자로 채우지 않은 칸 · 트랩 표현을 읽었을 때 | 0xAA 뒤 `d.c='A'` → **`41 aa aa aa aa aa aa aa`** | ★★ **sanitizer 가 원리상 못 잡는다.** 경고도 0건 |
| ★★★ **UB (본체)** | 아무 일이나 | ★★★ **포인터 캐스트로 다른 타입처럼 읽기**(엄격한 앨리어싱) · 트랩 표현을 값으로 읽기(★ **던지지 않았다**) · ★★ **C++ 에서 활성이 아닌 멤버 읽기** | 열 벌 실측 — **gcc `-O2` 부터 · clang `-O1` 부터 반환값 1** · `-fno-strict-aliasing` 이면 0 · g++ 는 자명하지 않은 멤버에 **`cc exit=1`** | ★★★ **UBSan+ASan 둘 다 0건**(`run exit=0`) · **clang 은 경고도 0건** |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| **표준** | ★ 볼 것이 없다 — 표준이 허용하는 것에 진단할 이유가 없다. **union 펀닝에 경고 0건**인 것이 정상이다 |
| **조건부 표준** | ★ **해당 없음** |
| **구현 정의** | ★ **컴파일러는 「이 머신은 리틀 엔디언입니다」라고 말하지 않는다.** `union` 으로 **직접 찍어 봐야** 보인다 |
| **미명시** | ★★ **안 쓴 바이트가 무엇인지 말해 주는 도구가 없다.** 바이트를 한 칸씩 찍는 것이 유일한 창이다 |
| ★★★ **UB** | ★★★ **gcc 의 `-Wstrict-aliasing=2` 는 `-O2` 에서만 1건**이고 `-O0` 에서는 0건이라 **최적화를 안 켜면 못 본다.** ★★★ **clang 은 `-O0`·`-O2` 둘 다 0건**인데 **정작 `-O1` 부터 깨진다.** ★★★ **UBSan 과 ASan 을 같이 켜도 `run exit=0`** — 실행 시점에 관찰할 사건이 없다 |

- ★★ **이 표의 결론 네 줄**
  - ★★★ **가장 조용한 자리는 「union 이면 허용, 캐스트면 UB」의 경계**다 — **소스가 거의 똑같이 생겼는데 층이 다르다.**
  - ★★★ **가장 일찍 깨지는 컴파일러가 가장 조용하다**(clang). **경고 수로 컴파일러를 고르면 안 된다.**
  - ★★ **sanitizer 가 못 잡는 UB 가 있다.** 「ASan·UBSan 을 켰으니 UB 는 없다」가 **틀린 자리**다.
  - ★ **union 은 진단 도구가 아니라 관찰 도구다** — 엔디언·비트 패턴을 **보여 주는** 데 쓴다.

### 이 주제의 네 번째 창 — **최적화 수준을 흔드는 것**

- **컴파일 진단**은 앨리어싱 위반에 거의 침묵한다(clang 0건 · gcc 는 `-O2` 에서만).
- **실행 출력**은 `-O0` 에서 **정상으로 보인다** — 「돌려 봤더니 맞던데」가 여기서 나온다.
- **sanitizer** 는 `run exit=0` 을 준다 — **초록 신호**다.
- ★★ **그래서 창을 둘 더 썼다.**
  - ★★★ **같은 소스를 네 최적화 수준으로 빌드해 나란히 찍는 것.** UB 는 **여기서만 드러났다.**
  - ★★ **`-fno-strict-aliasing` 을 켜 보는 것.** 값이 돌아오면 **「최적화가 만든 차이」였다는 증거**다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 둘 중 하나만 담기 | `union` + **태그 필드** | 태그 없는 `union` |
| 둘 다 담기 | `struct` | `union` |
| 비트 패턴 보기 (C 전용) | `union` 을 통한 펀닝 | `*(uint32_t *)&f` |
| 비트 패턴 보기 (C·C++ 공용) | **`memcpy`** | `union` 펀닝 |
| 엔디언 확인 | `union` 으로 **찍어 보기** | 매크로로 가정하기 |
| 태그를 앞에 둔 묶음 | **공통 초기 시퀀스**(같은 union 안에) | 구조체 포인터를 서로 캐스트 |
| union 비교 | **유효한 멤버**끼리 비교 | `memcmp` |
| union 을 0 으로 | `= { 0 }` 또는 `memset` | 멤버 하나만 쓰고 기대하기 |
| 패킷·파일 매핑 | **바이트를 `memcpy` 로 옮기기** | union 을 그대로 덮어 읽기 |
| C++ 와 공유할 헤더 | **`memcpy`** · 태그 있는 구조체 | 펀닝용 `union` |

판단 규칙 두 줄.

- ★★ **「이 바이트를 마지막에 누가 썼나」를 프로그램이 대답할 수 있으면 union 이고, 못 하면 설계가 틀린 것이다.**
- ★★ **이식할 코드에는 `memcpy`.** union 펀닝은 **C 안에서만** 안전하다.

## 핵심 문장

- ★★★ **`union` 은 동시에 담는 상자가 아니다.** `u.d = 1.0` 을 쓰자 `u.i` 가 **0** 이 되었다 — 바이트가 덮인 것이다.
- ★★★ **모든 멤버의 `offsetof` 가 0** 이고 `sizeof` 는 **가장 큰 멤버를 담을 만큼**이다.\
  같은 멤버를 struct 로 두면 **16**, union 으로 두면 **8** 이었다.
- ★★★ **C 는 `union` 을 통한 타입 펀닝을 허용한다.** `float 1.5f` 를 넣고 읽은 값이 **`0x3fc00000`** 이었다.
- ★★★ **포인터 캐스트로 같은 일을 하면 UB** 다. **gcc 는 `-O2` 부터, clang 은 `-O1` 부터** 반환값이 **1** 로 갈렸고\
  **메모리의 실제 값은 열 벌 전부 0** 이었다. `-fno-strict-aliasing` 이면 둘 다 0 이다.
- ★★★ **도구가 거의 침묵한다** — **clang 은 `-Wstrict-aliasing=2` 로도 0건** · gcc 는 **`-O2` 에서만 1건** ·\
  **UBSan + ASan 은 `run exit=0`** 으로 통과시킨다.
- ★★ **`memcpy` 는 값이 같고 규칙이 다르다.** 실측에서 union 과 같은 `0x3fc00000` 을 냈고,\
  **어느 언어에서도 안전한 쪽은 `memcpy`** 다.
- ★★ **공통 초기 시퀀스는 예외다** — 같은 union 이 보이는 곳에서 **앞머리가 같은 타입·같은 차례인 만큼**은 건너 읽어도 된다.\
  ★ `int tag` 와 `short tag` 는 **공통이 아니다.**
- ★★ **쓴 멤버보다 뒤에 남은 바이트는 미명시**다. 0xAA 로 채운 뒤 `d.c = 'A'` 만 쓰니 **`41 aa aa aa aa aa aa aa`** 였다.
- ★★ **C++ 는 활성 멤버 모형이라 다르다.** 실행 값은 같았지만(`0x3fc00000`)\
  **자명하지 않은 타입을 멤버로 넣으면 g++ 가 `cc exit=1` 로 막는다.**
- ★ **엔디언은 union 이 보여 준다.** `0x41424344` 가 **`44 43 42 41`** 로 보였다 — **구현 정의**다.
- ★ **union 에 `==` 는 없다.** 구조체와 같다.

## 관련 자료

- [`../README.md`](../README.md) — C 문법·API 주제 목록(이 주제는 23번)
- [`21-struct-declaration-initialization-and-designated-initializers/`](../21-struct-declaration-initialization-and-designated-initializers/) — ★ **선언·초기화·지정 초기자의 정본.**\
  그쪽은 「구조체를 어떻게 만들고 채우나」까지, **여기는 「같은 바이트를 여럿이 나눠 볼 때」부터**
- [`22-struct-padding-and-alignment/`](../22-struct-padding-and-alignment/) — ★★ **패딩과 「패딩 값은 미명시」의 정본.**\
  `struct B` 의 `tag` 뒤 4바이트가 왜 뜻이 없는지는 그쪽이 답한다
- [`24-bit-fields/`](../24-bit-fields/) — ★ **한 바이트 안을 더 잘게 쪼개는 쪽.** 배치가 구현 정의인 것은 같은 집안이다
- [`08-sizeof-alignment-and-offsetof/`](../08-sizeof-alignment-and-offsetof/) — ★ **`sizeof`·`_Alignof`·`offsetof` 라는 도구의 정본**
- [`05-explicit-casts-and-pointer-conversions/`](../05-explicit-casts-and-pointer-conversions/) — ★★ **캐스트가 「비트를 바꾸는가 해석을 바꾸는가」의 정본.**\
  `(float *)&x` 가 무엇을 하는 표현인지는 그쪽
- [`../../../data-representation/`](../../../../data-representation/) — ★ **2진 표현·IEEE 754·엔디언 자체의 정본.**\
  여기는 **C 문법이 그것을 어떻게 드러내나**만
- 목록의 **55번 주제** (엄격한 앨리어싱 규칙) — ★★★ **앨리어싱 규칙 전체의 정본.**\
  여기는 **「union 은 되고 캐스트는 안 된다」는 경계**까지
- 목록의 **50번 주제** (`<string.h>` 메모리 함수) — `memcpy`·`memcmp` 의 계약
- 목록의 **33번 주제** (`restrict` 와 앨리어싱 계약) — **「안 겹친다」를 사람이 약속하는 쪽**
- 목록의 **58번 주제** (UB 를 잡는 도구) — ★ **이 주제가 「도구로 안 잡히는 UB」의 사례**로 인용되는 자리
- 목록의 **25번 주제** (불완전 타입과 opaque struct) · 목록의 **26번 주제** (유연 배열 멤버) — 같은 집합체 갈래의 이웃

## 용어 풀이

- **`union`** — 멤버들이 **같은 바이트를 공유**하는 집합체. 예: `union U { int i; double d; };` 는 8바이트 하나를 `i` 와 `d` 가 나눠 본다.
- **활성 멤버(active member)** — 「지금 그 바이트를 차지한 멤버」라는 모형. ★ **C++ 의 말**이고 C 에는 없다.
- **타입 펀닝(type punning)** — 같은 바이트를 **선언된 타입이 아닌 타입으로** 읽는 것.\
  예: `float` 네 바이트를 `uint32_t` 로 읽어 지수 비트를 보는 것.
- **엄격한 앨리어싱(strict aliasing)** — 「서로 다른 타입의 포인터는 같은 객체를 가리키지 않는다」고 컴파일러가 믿어도 된다는 규칙.\
  예: `*(float *)&x` 로 `unsigned x` 를 읽으면 이 규칙을 어긴다.
- **공통 초기 시퀀스(common initial sequence)** — 한 union 안의 구조체들이 **앞머리에 같은 타입을 같은 차례로** 가진 부분.\
  예: `struct A { int tag; int x; }` 와 `struct B { int tag; double y; }` 에서는 `tag` 하나다.
- **엔디언(endianness)** — 여러 바이트짜리 값을 메모리에 놓는 **바이트 차례**.\
  예: `0x41424344` 가 `44 43 42 41` 로 보이면 **리틀 엔디언**이다. ★ **구현 정의**다.
- **지정 초기자(designated initializer)** — 초기자에서 **멤버를 이름으로 고르는** 문법. 예: `union U u = { .d = 1.5 };` (C99부터).
- **트랩 표현(trap representation)** — 그 타입의 어떤 값도 나타내지 않는 비트 패턴. 읽으면 UB 다.\
  ★ **이 문서는 던지지 않았다** — x86-64 의 정수·부동소수에는 만들기 어렵다.
- **미명시 동작(unspecified behavior)** — 표준이 **여러 가능성 중 하나**를 허용하고 **문서화도 요구하지 않는** 것.\
  예: 멤버 하나를 쓴 뒤 남은 바이트의 값.
- **구현 정의 동작(implementation-defined behavior)** — 구현이 고르되 **문서화 의무가 있는** 것. 예: 엔디언.
- **미정의 동작(undefined behavior, UB)** — 표준이 **아무 요구도 하지 않는** 것. 예: 포인터 캐스트로 다른 타입처럼 읽기.
- **`-fno-strict-aliasing`** — 엄격한 앨리어싱을 **가정하지 말라**고 컴파일러에게 이르는 플래그.\
  예: 실측에서 이 플래그를 주자 반환값이 1 에서 0 으로 돌아왔다.
- **`-Wstrict-aliasing=2`** — gcc 가 앨리어싱 위반을 **의심될 때까지** 진단하게 하는 수준.\
  ★ 실측에서 **`-O2` 에서만 1건**이었고 **clang 에서는 0건**이었다.

---

## 더 들어가면

- ★ **「C 가 union 펀닝을 허용한다」는 진술의 힘**이 어디까지인지는 이 문서가 **실행으로 증명할 수 없다.**\
  허용된다는 것은 **「깨지지 않는다」는 보장**이고, **깨지지 않는 것을 관찰해도 보장을 확인한 것은 아니다.**\
  ★ **규칙의 출처는 문서**이고, 이 문서가 한 일은 **캐스트 쪽이 실제로 깨지는 것을 보인 것**이다.
- ★★ **clang 이 `-O1` 부터 갈린 이유**는 못 가른다 — 앨리어싱 분석을 언제 켜는지가 **컴파일러 내부 사정**이다.\
  ★ **`-fno-strict-aliasing` 으로 되돌아온 것**까지가 이 문서가 말할 수 있는 전부다.
- ★★ **UBSan 에 앨리어싱 검사가 아예 없는지**는 확인하지 않았다.\
  실측은 **「`-fsanitize=undefined,address` 로 돌렸더니 `run exit=0` 이었다」** 까지다.
- ★ **트랩 표현은 던지지 않았다.** x86-64 의 정수에는 트랩 표현이 없고 부동소수도 만들기 어렵다 —\
  **「미명시」 칸의 그 항목은 관찰로 채우지 못했다.**
- ★ **`memcpy` 가 최적화로 사라지는지**는 **재지 않았다.** 어셈블리를 찍어야 하는 일이고 이 문서의 축이 아니다.
- ★ **비트필드가 든 union** 은 던지지 않았다. **배치가 구현 정의인 층이 하나 더 겹치는** 자리라\
  [24번 형제](../24-bit-fields/)와 묶어 보는 것이 맞다.
- ★ **익명 union**(`union { int i; float f; };` 을 구조체 멤버로)은 [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/)가\
  **익명 구조체**로 다룬 것과 같은 규칙이다 — 여기서는 따로 던지지 않았다.
- ★★ **C++ 의 `std::bit_cast`** 가 이 주제의 C++ 쪽 답이지만 **C 에는 없다.**\
  C++ 갈래(`../../cpp/syntax/`)가 정본이고, 지금은 그 주제가 아직 없다.
