# c/syntax/50 — `<string.h>` 메모리 함수: 「**`memcpy` 는 겹치지 않는다는 약속 위에 서고, `memset`·`memcmp` 는 값이 아니라 바이트를 다룬다**」 — 질문

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「결과」 칸과 「ASan」 칸을 따로** 적어라 — 결과를 **적어서는 안 되는 칸**이 있다.
- ★★ **「표준이 약속한 것」과 「이 판의 컴파일러·glibc 가 한 것」을 갈라** 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**지금 비교·복사하는 것이 값인가, 바이트인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 함수 둘 × 겹침 셋 × 크기 둘 — 겹침 격자 (예측) ★★★ 이 주제의 축

```c
/* s50a.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char buf[32];

int main(int argc, char **argv) {
    setvbuf(stdout, NULL, _IONBF, 0);
    if (argc < 4) return 2;
    int fn = argv[1][0] == 'c';            /* c = memcpy, m = memmove */
    int mode = atoi(argv[2]);              /* 0 = none, 1 = dst after src, 2 = dst before src */
    int fixed = argv[3][0] == 'k';         /* k = constant 8, r = size read at run time */
    volatile size_t n = 8;
    strcpy(buf, "ABCDEFGHIJKLMNOP");
    char *d = mode == 0 ? buf + 8 : mode == 1 ? buf + 2 : buf;
    char *s = mode == 2 ? buf + 2 : buf;
    if (fn && fixed)       memcpy(d, s, 8);
    else if (fn)           memcpy(d, s, n);
    else if (fixed)        memmove(d, s, 8);
    else                   memmove(d, s, n);
    printf("%s\n", buf);
    return 0;
}
```

격자는 `./x c|m 0|1|2 r|k` 열두 가지를 **ASan 없는 gcc `-O0`** 한 벌과 **ASan 빌드 다섯 벌**(gcc `-O0` · gcc `-O2` · gcc `-O2 -U_FORTIFY_SOURCE` · clang `-O0` · clang `-O2`)에서 돌린다.

- ★★★ `memmove` 의 두 겹침 줄(`dst > src` · `dst < src`)은 각각 어떤 16 글자를 찍는가?
- ★★★ `memcpy` 의 겹침 줄 넷에서 「결과」 칸에 **무엇을 적어야 하는가**?
- ★★★ ASan 다섯 벌은 `memcpy` 겹침을 **전부** 잡는가? 크기가 **실행 시 값**인 줄과 **상수 8** 인 줄이 같은 답을 내는가?
- ★ `memcpy` 겹침 없음 줄에서 ASan 이 말하는 것이 있는가?

### 2. `memcpy` 는 호출로 남는가 (예측) ★★

```c
/* s50f.c */
#include <string.h>

void copy8(void *d, const void *s) { memcpy(d, s, 8); }
void copy32(void *d, const void *s) { memcpy(d, s, 32); }
void copyn(void *d, const void *s, size_t n) { memcpy(d, s, n); }
void move8(void *d, const void *s) { memmove(d, s, 8); }
```

- ★★ gcc·clang 을 `-O0`·`-O2` 로 컴파일하면 네 함수 중 **`memcpy` 호출이 남는 것**은?
- ★★ ASan 을 켜면 `copy8` 의 몸통은 무엇이 되는가? 그것을 **1번 격자**와 이어서 설명하면?
- ★ 이 격자로 「`memcpy` 가 `memmove` 보다 빠르다」를 말할 수 있는가?

### 3. 글자로 보이는 겹침 (예측) ★★

```c
/* s50g.c */
#include <string.h>

static char buf[32] = "ABCDEFGHIJKLMNOP";

void shift_right(void) { memcpy(buf + 2, buf, 8); }
void shift_left(void) { memcpy(buf, buf + 2, 8); }
void shift_var(char *d, const char *s) { memcpy(d, s, 8); }
```

- ★★ gcc 와 clang 은 세 함수 중 어느 것에 경고를 내는가? 경고 이름은?
- ★ `shift_var(buf + 2, buf)` 로 부르면 그 호출에 경고가 나는가?

### 4. 멤버 `==` 와 `memcmp` (예측) ★★★

```c
/* s50b.c */
#include <math.h>
#include <stdio.h>
#include <string.h>

struct D { double v; };

static const char *eq(struct D a, struct D b) { return a.v == b.v ? "same" : "diff"; }
static const char *mc(struct D a, struct D b) { return memcmp(&a, &b, sizeof a) == 0 ? "same" : "diff"; }

int main(void) {
    struct D p = { 0.0 }, q = { -0.0 };
    struct D x = { NAN }, y = x;
    printf("{0.0} vs {-0.0}   member == : %s   memcmp : %s\n", eq(p, q), mc(p, q));
    printf("{NAN} vs copy     member == : %s   memcmp : %s\n", eq(x, y), mc(x, y));
    return 0;
}
```

- ★★★ 두 줄에서 `member ==` 와 `memcmp` 는 각각 `same`/`diff` 중 무엇인가?
- ★★ 네 빌드(gcc/clang × `-O0`/`-O2`)가 같은 답을 내는가?

### 5. 패딩이 있는 구조체를 `memcmp` 로 (예측) ★★★

```c
/* s50c.c */
#include <stdio.h>
#include <string.h>

struct S { char c; int i; };               /* 1 byte, 3 bytes of padding, 4 bytes */

static void dirty(void) {
    volatile unsigned char junk[64];
    for (int k = 0; k < 64; k++) junk[k] = (unsigned char)(0xA0 + k);
}

static struct S by_member(void) {
    struct S v;
    v.c = 'x'; v.i = 7;
    return v;
}

static struct S by_memset(void) {
    struct S v;
    memset(&v, 0, sizeof v);
    v.c = 'x'; v.i = 7;
    return v;
}

int main(void) {
    dirty(); struct S a = by_member();
    dirty(); struct S b = by_memset();
    struct S m;
    memset(&m, 0, sizeof m);
    m.c = 'x'; m.i = 7;
    printf("members a,b equal : %d\n", a.c == b.c && a.i == b.i);
    printf("memcmp(a, b)      : %s\n", memcmp(&a, &b, sizeof a) ? "nonzero" : "zero");
    printf("memcmp(b, m)      : %s\n", memcmp(&b, &m, sizeof b) ? "nonzero" : "zero");
    return 0;
}
```

- ★★★ gcc/clang × `-O0`/`-O1`/`-O2` 여섯 빌드를 **20 판씩** 돌리면, `memcmp(a, b)` 가 `nonzero` 인 판은 빌드마다 몇 판인가?
- ★★★ `memcmp(b, m)` — **둘 다 `memset` 으로 지운 뒤** 멤버를 넣었다 — 은 항상 `zero` 인가?
- ★ `members a,b equal` 은?

### 6. `memset` 의 둘째 인자 (예측) ★★

```c
/* s50e.c */
#include <stdio.h>
#include <string.h>

int main(void) {
    int a[4];
    memset(a, 1, sizeof a);
    printf("memset(a, 1)   : %d %d %d %d\n", a[0], a[1], a[2], a[3]);
    memset(a, -1, sizeof a);
    printf("memset(a, -1)  : %d %d %d %d\n", a[0], a[1], a[2], a[3]);
    memset(a, 0x101, sizeof a);
    printf("memset(a, 257) : %d %d %d %d\n", a[0], a[1], a[2], a[3]);
    for (int k = 0; k < 4; k++) a[k] = 1;
    printf("loop a[k] = 1  : %d %d %d %d\n", a[0], a[1], a[2], a[3]);
    return 0;
}
```

- ★★ 네 줄은 각각 무엇을 찍는가?
- ★ `-O2 -Wall -Wextra -pedantic` 은 이 파일에 경고를 내는가?

### 7. 「모든 비트 0」은 무엇의 0 인가 (경계) ★★★

- `memset(&x, 0, sizeof x)` 뒤에 `int` 는 `0` 인가 · 포인터는 널인가 · `double` 은 `0.0` 인가 — **각각 누가 보장하나**?
- ★★ `-0.0` 의 바이트는 `0.0` 과 같은가? 그래서 `memset` 0 이 만드는 것은 어느 쪽인가?

### 8. `gcc -O2 -dM -E` 의 한 줄 (왜) ★★

- ★★ 이 판의 gcc 에서 `-O2` 를 주면 **따로 정의하지 않은 매크로** 하나가 생긴다. 무엇이고, 그것이 1번 격자의 어느 칸을 바꿨는가?
- ★ 그것은 C 표준의 일인가, 컴파일러의 일인가, 배포판의 일인가?

### 9. 33번 형제와 이어서 (연결) ★★

- [33번 형제](../33-restrict-and-the-aliasing-contract/)는 `memcpy` 와 `memmove` 의 **무엇을** 이미 쟀는가?
- ★★ 이 편이 그 위에 더한 칸 둘은?

### 10. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / 구현 정의 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- ★★★ 이 편의 **네 번째 창**은 무엇이고, 그 창이 **못 보는 것**은?

### 11. 경계 — 어디까지가 이 주제인가 (연결) ★

- **패딩 바이트의 덤프**는 어느 형제가 정본인가? **`calloc` 의 0** 은?
- ★ **`strcpy`·`strncpy` 의 경계**는 목록의 몇 번 주제인가?

## 실행 환경

**환경** — gcc 13.3.0 · clang 18.1.3 · glibc 2.39 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.

★★★ **본체 창은 겹침 격자** — 1번은 **칸마다 「ASan 이 무엇을 말했나」** 를 적어야 답이다.
★★ **`restrict` 의 뜻 자체는 묻지 않는다** — 그것은 [33번 형제](../33-restrict-and-the-aliasing-contract/)가 정본이다.
선행 — [33번 형제](../33-restrict-and-the-aliasing-contract/) · [목록의 **49번 주제**](../49-string-functions-and-pitfalls/).

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
