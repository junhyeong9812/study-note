# c/syntax/23 — `union` 과 타입 펀닝의 경계: 「**union 은 동시에 담는 상자가 아니라 같은 바이트를 겹쳐 보는 창이다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · g++ 13.3.0 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **바이트 격자**(`44 43 42 41` 이 무슨 차례인가) ② **어느 벌에서 갈렸나**(`-O0`\~`-O3` 와 컴파일러)
> ③ **그 사실이 다섯 층 중 어느 칸인가**(허용인가 미명시인가 UB 인가).
> ★★★ **이 주제의 본체는 「같은 일인데 층이 다른」 두 형태다** — `union` 을 거치면 허용,
> **포인터 캐스트면 UB**. 소스가 거의 똑같이 생겼다는 것이 이 주제의 어려움이다.
> ★ **「돌려 봤더니 같더라」가 근거가 못 되는 자리**가 있다 — 3번과 8번이 그렇다.
> **값이 같은 것이 당연하고, 갈리는 것은 규칙**이기 때문이다.
> ★★ **한 벌만 돌리고 답하지 마라** — 4번은 **열 벌**을 돌려야 답이 하나로 모이지 않는다는 것이 답이다.
> 선행 — [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/) ·
> [08번 형제](../08-sizeof-alignment-and-offsetof/) · [05번 형제](../05-explicit-casts-and-pointer-conversions/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 멤버 셋을 union 과 struct 에 넣고 재면 (예측) ★★★ 이 주제의 축

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

- `union U` 와 `struct S` 의 `sizeof` 는 각각 얼마인가?
- 두 타입의 `_Alignof` 는 각각 얼마인가?
- `offsetof` 세 개는 union 쪽에서 각각 얼마이고, struct 쪽에서는 얼마인가?
- `u.i = 0x41424344` 를 쓴 뒤 `u.c[0]` 과 `u.c[3]` 은 각각 어떤 글자인가?
- 그 네 바이트를 16진수로 찍으면 어떤 차례로 보이나? ★ 그 차례를 **무엇이라 부르고 어느 층**인가?
- 이어서 `u.d = 1.0` 을 쓰면 `u.i` 는 얼마가 되나? ★ **왜 그 값**인가?

### 2. `float` 한 값을 넣고 정수 멤버로 읽으면 (예측) ★★★ 이 주제의 본체

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

- `v.f = 1.5f` 를 넣고 `v.u` 로 읽으면 16진수로 얼마인가?
- 그 비트를 부호·지수·가수로 갈라 적으면? ★ 지수 칸의 값이 **왜 그 수**인가?
- 같은 네 바이트를 `memcpy` 로 옮겨 읽은 값은 union 과 **같은가 다른가**?
- 거꾸로 `v.u = 0x40490fdb` 를 넣고 `v.f` 로 읽으면 무엇이 나오나?
- `0x7fc00000` 을 넣고 `f` 로 읽으면 무엇이 나오나?
- ★ 이 프로그램은 **경고가 몇 건**이고 **종료 코드는 얼마**인가?

### 3. 같은 일을 `memcpy` 로 하면 무엇이 달라지나 (경계) ★★

- 2번에서 union 으로 읽은 값과 `memcpy` 로 읽은 값이 **같았다.** 그런데도 둘을 **가르는 이유**는 무엇인가?
- **C 에서** 둘 중 무엇이 허용되나 — 하나인가 둘 다인가?
- **C++ 에서는** 어떻게 갈리나?
- ★ 「돌려 봤더니 같더라」가 이 자리에서 **근거가 못 되는 이유**를 한 줄로 대면?
- 두 언어에서 같이 쓸 헤더에는 **어느 쪽**을 쓰나?

### 4. 같은 칸을 두 타입의 포인터로 건드리고 여러 수준으로 돌리면 (예측) ★★★ 본체

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

- `gcc -O0`·`-O1`·`-O2`·`-O3` 네 벌의 **반환값**은 각각 얼마인가?
- `clang -O0`·`-O1`·`-O2`·`-O3` 네 벌은 각각 얼마인가? ★ **두 컴파일러가 갈리는 지점이 같은가?**
- 열 벌 전부에서 **「메모리의 실제 값」** 은 얼마였나?
- `-fno-strict-aliasing` 을 주면 무엇이 바뀌나?
- ★ 컴파일러가 **무엇을 믿었기에** 그 값이 나왔는지 한 문장으로 대면?
- ★★ 1번·2번의 union 과 **소스가 거의 같은데 층이 다른** 이유는?

### 5. 그 위험을 컴파일러와 sanitizer 에게 물어보면 (경계) ★★★

- `gcc -Wstrict-aliasing=2` 를 `-O0` 과 `-O2` 로 각각 주면 경고가 **몇 건**인가?
- 같은 플래그를 `clang` 에 주면 `-O0`·`-O2` 에서 각각 몇 건인가?
- ★★ **가장 일찍 깨지는 컴파일러**와 **가장 말이 많은 컴파일러**가 같은가?
- `-fsanitize=undefined,address` 로 돌리면 무엇이 나오고 **`run exit`** 은 얼마인가?
- ★ sanitizer 가 못 잡는 이유를 **한 문장**으로 대면?
- ★ 그렇다면 이 위반을 **볼 수 있는 유일한 창**은 무엇인가?

### 6. 앞머리가 같은 두 구조체를 한 union 에 넣으면 (예측) ★★

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

- `a` 로 쓰고 `v.b.tag` 를 읽으면 얼마인가? ★ 그것이 **허용되는 이름**은 무엇인가?
- `b` 로 쓰고 `v.a.tag` 를 읽으면 얼마인가?
- `b` 로 쓴 뒤 `v.a.x` 를 읽으면 얼마인가? ★ 그 자리는 `struct B` 에서 **무엇**인가?
- `sizeof A`·`sizeof B`·`sizeof V` 는 각각 얼마이고, `offsetof(B, y)` 는 얼마인가?
- ★ `int tag` 와 `short tag` 였다면 같은 규칙이 서나?
- ★★ 이 규칙이 서려면 **무엇이 보여야** 하나?

### 7. union 을 네 가지 방식으로 만들면 (예측) ★★

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

- `union U a = { 'A' };` 는 **어느 멤버**를 초기화하나? 여덟 바이트는 어떻게 보이나?
- `{ .i = 0x41424344 }` 의 여덟 바이트는? ★ 앞 네 칸의 **차례**가 왜 그런가?
- `{ 0 }` 의 여덟 바이트는?
- 0xAA 로 채운 뒤 `d.c = 'A'` 만 쓴 여덟 바이트는? ★ 뒤 일곱 칸이 **어느 층**인가?
- ★ `a`·`b`·`c` 에서 뒤가 0 으로 보이는 것은 **보장인가 관찰인가**?

### 8. 같은 펀닝을 C++ 로 옮기면 (경계) ★★

- `g++ -std=c++17 -O2` 로 돌린 값이 C 와 **같은가 다른가**?
- 그렇다면 두 언어가 갈리는 것은 **무엇**인가?
- C++ 의 union 모형을 부르는 이름은? ★ C 에 그 말이 있나?
- `std::string` 을 멤버로 가진 union 을 g++ 에 던지면 **`cc exit`** 이 얼마이고 **어떤 진단** 두 갈래가 나오나?
- ★ 그 진단이 **C 에서는 나올 수 없는 이유**는?

### 9. union 의 `sizeof` 가 가장 큰 멤버보다 클 수 있는 이유 (왜) ★

- `union { char c[5]; int i; }` 의 `sizeof` 는 5 가 아니다 — 왜인가?
- 그 규칙은 구조체의 **어느 규칙**과 같은 것인가? 정본은 어느 형제인가?
- ★ union 의 `_Alignof` 는 무엇이 정하나?

### 10. 다섯 층과 무게중심 (연결) ★★★

- 이 주제에서 **표준**이 보장하는 것 다섯 가지를 대면?
- **구현 정의** 칸에 들어가는 것 셋은?
- **미명시** 칸에 들어가는 것은? ★ 그것을 **보이는 창**은 무엇인가?
- **UB** 칸에서 이 주제의 본체 하나는?
- ★ **조건부 표준** 칸은 채워지나?
- ★★ 층마다 **도구가 못 보는 것**을 한 줄씩 대면?

### 11. 경계 — 어디까지가 이 주제인가 (연결) ★

- **엄격한 앨리어싱 규칙 전체**는 어느 주제가 정본인가?
- **`memcpy`·`memcmp` 의 계약**은 어느 주제가 정본인가?
- **엔디언과 IEEE 754 자체**는 어느 갈래가 정본인가?
- **패딩 값이 미명시라는 것**은 어느 형제가 정본인가?
- 이 주제가 **끝까지 책임지는 것** 셋을 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
