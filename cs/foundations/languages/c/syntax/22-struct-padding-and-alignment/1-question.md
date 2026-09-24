# c/syntax/22 — 구조체 패딩·정렬: 「**같은 멤버라도 순서가 크기를 바꾸고, 구멍의 값은 아무도 약속하지 않는다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **바이트 격자**(어디가 구멍이고 몇 칸인가) ② **그 구멍 안의 값이 예측 가능한가**
> ③ **그 사실이 다섯 층 중 어느 칸인가**(구현 정의인가 미명시인가).
> ★★★ **이 주제는 「미명시」가 본체**다 — 패딩 바이트의 값이 그것이고, 두 번째가 **구현 정의**(크기와 자리)다.
> ★ **「이 머신에서 16이다」가 답이 아니다** — 어느 층이라서 그 수치를 믿으면 안 되는지를 답해라.
> ★★ **한 벌만 돌리고 답하지 마라** — 2번은 **여섯 벌을 돌리고 한 벌을 20번씩** 반복해야 답이 선다.
> ★ **대조할 것이 숫자가 아닌 칸이 있다** — 패딩 바이트의 실제 값과 `memcmp` 반환값의 **크기**가 그렇다.
> 선행 — ★★ [08번 형제](../08-sizeof-alignment-and-offsetof/)가 **도구의 정본**이다(여기는 규칙 쪽이다) ·
> [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/) · [02번 형제](../02-basic-types-sizes-and-fixed-width-integers/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 멤버 셋을 여섯 가지 순서로 늘어놓으면 (예측) ★★★ 이 주제의 첫 축

```c
/* s22a.c */
#include <stdio.h>
#include <stddef.h>

struct CID { char c; int i; double d; };
struct CDI { char c; double d; int i; };
struct ICD { int i; char c; double d; };
struct IDC { int i; double d; char c; };
struct DCI { double d; char c; int i; };
struct DIC { double d; int i; char c; };

#define ROW(T, m1, m2, m3) \
    printf("%-4s sizeof=%2zu _Alignof=%zu   offsets: %s=%2zu %s=%2zu %s=%2zu\n", \
           #T, sizeof(struct T), _Alignof(struct T), \
           #m1, offsetof(struct T, m1), #m2, offsetof(struct T, m2), \
           #m3, offsetof(struct T, m3))

int main(void) {
    printf("멤버 집합은 여섯 벌 모두 같다 — char 1 + int 4 + double 8 = 13 바이트\n\n");
    ROW(CID, c, i, d);
    ROW(CDI, c, d, i);
    ROW(ICD, i, c, d);
    ROW(IDC, i, d, c);
    ROW(DCI, d, c, i);
    ROW(DIC, d, i, c);
    return 0;
}
```

- 여섯 벌의 `sizeof` 는 각각 얼마인가 — **몇 종류로 갈리는가**?
- 멤버 크기의 합은 13인데, **가장 큰 벌과 가장 작은 벌의 차이**는 몇 바이트인가?
- ★ 「큰 것부터 놓으면 최소가 된다」가 맞다면 **작은 것부터 놓은 벌**은 어떻게 되는가?
- ★★ 손해 보는 벌들의 **공통점** 한 가지를 대면?
- `_Alignof` 는 여섯 벌에서 각각 얼마인가 — 왜 그런가?

### 2. 같은 { 1, 2, 3 } 을 네 가지 방법으로 만들면 (예측) ★★★ 이 편의 본체

```c
/* s22b.c */
#include <stdio.h>
#include <string.h>

struct S { char c; int i; char e; };   /* 구멍: 1~3 과 9~11 */

#define SGN(m) ((m) > 0 ? "+" : (m) < 0 ? "-" : "0")

static void dirty(void) {              /* 스택의 같은 자리를 0xAA 로 더럽힌다 */
    volatile unsigned char buf[64];
    for (int k = 0; k < 64; k++) buf[k] = 0xAA;
    if (buf[0] != 0xAA) printf("!");
}

static struct S make(int how) {        /* dirty 와 같은 깊이·같은 자리 */
    volatile unsigned char guard[8] = {0};
    struct S v;
    if (how == 0) { struct S t = { .c = 1, .i = 2, .e = 3 }; v = t; }
    else if (how == 1) { v.c = 1; v.i = 2; v.e = 3; }
    else { memset(&v, 0, sizeof v); v.c = 1; v.i = 2; v.e = 3; }
    (void)guard;
    return v;
}

static void show(const char *tag, const struct S *p) {
    const unsigned char *b = (const unsigned char *)p;
    printf("%-18s", tag);
    for (size_t k = 0; k < sizeof *p; k++) {
        int pad = (k >= 1 && k <= 3) || (k >= 9 && k <= 11);
        printf(" %s%02x%s", pad ? "[" : " ", b[k], pad ? "]" : " ");
    }
    printf("\n");
}

int main(void) {
    dirty(); struct S a = make(0);   /* 초기자 */
    dirty(); struct S b = make(1);   /* 멤버 대입만 */
    dirty(); struct S c = make(2);   /* memset 뒤 대입 */
    struct S d = a;                  /* 구조체 대입 */

    printf("멤버 값은 넷 다 { 1, 2, 3 } 이다.  [ ] 안이 패딩 바이트\n\n");
    show("a initializer", &a);
    show("b member-assign", &b);
    show("c memset+assign", &c);
    show("d = a  (copy)", &d);
    printf("\n멤버끼리 : a==b %d  a==c %d  a==d %d   (1 이면 같다)\n",
           a.c == b.c && a.i == b.i && a.e == b.e,
           a.c == c.c && a.i == c.i && a.e == c.e,
           a.c == d.c && a.i == d.i && a.e == d.e);
    printf("memcmp   : a,b %s  a,c %s  a,d %s   (부호만 — 크기는 미명시다)\n",
           SGN(memcmp(&a, &b, sizeof a)), SGN(memcmp(&a, &c, sizeof a)),
           SGN(memcmp(&a, &d, sizeof a)));
    return 0;
}
```

- 네 방법 중 **구멍이 `00` 으로 나오는 것**은 몇 개인가?
- ★★ `a` 는 **초기자를 썼다.** 그래도 구멍이 `0xAA` 로 남을 수 있는가 — 왜?
- ★ `d = a` 라는 **구조체 대입**이 구멍까지 복사하는가?
- ★★ 「멤버끼리」 줄과 「`memcmp`」 줄이 **왜 다른 답**을 내는가?
- 이 프로그램이 `memcmp` 의 반환값을 **부호로만 찍는 이유**는 무엇인가?

### 3. 몇 벌을 돌리고 몇 번을 반복해야 결론이 서나 (경계) ★★★

- 위 프로그램을 **gcc `-O0` 한 벌만** 돌리고 「패딩은 0xAA 로 남는다」고 적으면 무엇이 틀리는가?
- ★★ 같은 바이너리를 **20번** 돌렸을 때 격자가 **1가지인 벌**과 **20가지인 벌**은 각각 어느 것인가?
- ★ 그 두 부류에서 **대조할 것**이 각각 무엇으로 달라지는가?
- 이 주제에서 **「세 번 돌려 보고 같았다」가 왜 가장 위험한 근거**인가?
- ★ 문서에 **정본 격자로 실을 벌**을 고른다면 어느 것이고, 그 근거는?

### 4. `memcmp` 가 답하는 것과 답하지 않는 것 (왜) ★★

- `memcmp` 는 **무엇을 비교**하는가 — 멤버인가 바이트인가?
- ★ 반환값의 **부호**와 **크기** 중 표준이 정한 것은 어느 쪽인가?
- 이 머신에서 30번을 돌려 크기가 한 값으로 모였다면, 그것을 **근거로 써도 되는가**?
- ★★ 구조체를 비교하는 **옳은 방법**은 무엇이고, `memset` 은 왜 답이 못 되는가?
- 구조체를 `fwrite`·해시에 통째로 넣는 것이 같은 집안의 사고인 이유는?

### 5. 멤버 하나에 `_Alignas` 를 걸면 (예측) ★★

```c
/* s22d.c */
#include <stdio.h>
#include <stddef.h>

struct A { char c; };
struct B { _Alignas(16) char c; };            /* 멤버 하나를 16 으로 */
struct C { char c; _Alignas(8) int i; };      /* 가운데 멤버를 8 로 */
struct D { char c; int i; };                  /* 대조군 */

#define ROW(T) printf("%-9s sizeof=%2zu _Alignof=%2zu\n", #T, sizeof(struct T), _Alignof(struct T))

int main(void) {
    ROW(A); ROW(B); ROW(C); ROW(D);
    printf("\nstruct C offsets: c=%zu i=%zu   <- 구멍이 3 이 아니라 7 이 된다\n",
           offsetof(struct C, c), offsetof(struct C, i));
    printf("struct D offsets: c=%zu i=%zu\n",
           offsetof(struct D, c), offsetof(struct D, i));
    struct B arr[2];
    printf("\n_Alignas 는 배열에도 따라온다 : (char*)&arr[1] - (char*)&arr[0] = %td\n",
           (char *)&arr[1] - (char *)&arr[0]);
    printf("&arr[0] 가 16 의 배수인가 : %d\n", ((unsigned long)(void *)&arr[0] % 16) == 0);
    return 0;
}
```

- `struct B` 의 `sizeof` 는 얼마인가 — 멤버는 `char` 하나뿐인데?
- `struct C` 와 `struct D` 는 멤버가 같다. `sizeof` 가 갈리는가 — 갈린다면 왜?
- ★ `struct C` 의 `offsetof(i)` 는 4인가 8인가?
- ★★ `_Alignas` 가 **배열의 원소 간격**에도 영향을 주는가?
- 이 지시로 **얻는 것과 잃는 것**을 각각 한 줄로?

### 6. `_Alignas` 가 거절하는 두 가지 (경계) ★

```c
/* s22d2.c */
struct Narrow { _Alignas(1) int i; };      /* 정렬을 줄이려 한다 */
struct Odd    { _Alignas(3) char c; };     /* 2의 거듭제곱이 아닌 값 */
int main(void) { return sizeof(struct Narrow) + sizeof(struct Odd); }
```

- 이 소스는 **경고인가 에러인가** — `cc exit` 은 얼마인가?
- ★ 거절 사유가 **둘**이다. 각각 무엇인가?
- `_Alignas` 로 정렬을 **줄이고 싶으면** C 에서 무엇을 써야 하는가 — 그것은 표준인가?
- ★ 이 주제에서 **컴파일러가 막아 주는 사고**는 이것 말고 또 있는가?

### 7. `pack(1)` 말고 `pack(2)`·`pack(4)` 를 넣으면 (예측) ★★

```c
/* s22e.c */
#include <stdio.h>
#include <string.h>
#include <stddef.h>

struct P0 { char c; int i; double d; };            /* 기본 */
#pragma pack(push, 1)
struct P1 { char c; int i; double d; };
#pragma pack(pop)
#pragma pack(push, 2)
struct P2 { char c; int i; double d; };
#pragma pack(pop)
#pragma pack(push, 4)
struct P4 { char c; int i; double d; };
#pragma pack(pop)

#define ROW(T) printf("%-4s sizeof=%2zu _Alignof=%zu   c=%zu i=%zu d=%2zu\n", \
    #T, sizeof(struct T), _Alignof(struct T), \
    offsetof(struct T, c), offsetof(struct T, i), offsetof(struct T, d))

int main(void) {
    ROW(P0); ROW(P1); ROW(P2); ROW(P4);
    printf("\npack(2) 는 정렬을 「없애는」 것이 아니라 2 로 「깎는」 것이다\n");

    struct P2 v;
    memset(&v, 0, sizeof v);              /* 패딩까지 0 으로 — 덤프를 결정적으로 */
    v.c = 'x'; v.i = 0x41424344; v.d = 1.5;
    const unsigned char *b = (const unsigned char *)&v;
    printf("P2 의 바이트 :");
    for (size_t k = 0; k < sizeof v; k++) printf(" %02x", b[k]);
    printf("\n");

    struct P1 arr[3];
    printf("\npack(1) 배열의 멤버 주소가 정렬을 지키나 (0 이면 지킨 것)\n");
    for (int k = 0; k < 3; k++)
        printf("  arr[%d] : &i %% 4 = %lu · &d %% 8 = %lu\n", k,
               (unsigned long)(void *)&arr[k].i % 4,
               (unsigned long)(void *)&arr[k].d % 8);
    printf("  -> 13 바이트씩 밀리므로 ★ 맞는 자리가 나오는 것은 우연이다\n");
    return 0;
}
```

- 네 구조체의 `sizeof` 는 각각 얼마인가 — **기본과 같은 값이 나오는 벌**이 있는가?
- ★★ `pack(2)` 의 구멍은 **몇 바이트**인가 — 0인가?
- `#pragma pack` 의 인자는 「무엇을 없애라」인가 「무엇을 깎아라」인가?
- ★ `pack(1)` 배열의 세 원소에서 `&arr[k].i % 4` 가 어떻게 나오는가 — **0이 나오는 원소**가 있다면 그것은 무엇인가?
- ★★ clang 의 출력은 gcc 와 같은가 — 같다면 그것은 **보장인가 관찰인가**?

### 8. 유연 배열 멤버의 헤더는 어디서 끝나나 (예측) ★

```c
/* s22f.c */
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>

struct Ba { int  n; char a[]; };    /* 헤더가 4, 원소가 1 */
struct Bb { char n; int  a[]; };    /* 헤더가 1, 원소가 4 */
struct Bc { double d; char a[]; };  /* 헤더가 8, 원소가 1 */

#define ROW(T, m) printf("%-9s sizeof=%zu _Alignof=%zu offsetof(a)=%zu\n", \
                         #T, sizeof(struct T), _Alignof(struct T), offsetof(struct T, m))

int main(void) {
    ROW(Ba, a); ROW(Bb, a); ROW(Bc, a);
    printf("\n★ Bb 는 sizeof 가 4 인데 offsetof(a) 도 4 다 — 헤더 뒤 3바이트가 패딩이다\n");

    size_t n = 5;
    struct Bb *p = malloc(offsetof(struct Bb, a) + n * sizeof p->a[0]);
    if (!p) return 1;
    p->n = 'x';
    for (size_t k = 0; k < n; k++) p->a[k] = (int)k * 10;
    printf("한 번 할당한 크기 = %zu 바이트 (offsetof %zu + 5*%zu)\n",
           offsetof(struct Bb, a) + n * sizeof p->a[0],
           offsetof(struct Bb, a), sizeof p->a[0]);
    printf("p->n='%c'  a =", p->n);
    for (size_t k = 0; k < n; k++) printf(" %d", p->a[k]);
    printf("\n");
    printf("sizeof(*p) + 5*4 로 잡았다면 = %zu 바이트 — ★ 같은 값이지만 우연이다\n",
           sizeof *p + n * sizeof p->a[0]);
    free(p);
    return 0;
}
```

- `struct Bb` 의 `sizeof` 와 `offsetof(a)` 는 각각 얼마인가?
- ★ 멤버는 `char` 하나뿐인데 그 값이 1이 아닌 이유는?
- 할당 크기를 `offsetof` 로 잡은 것과 `sizeof *p` 로 잡은 것이 **같은 값**이 나오는가?
- ★★ 같은 값이 나왔다면 그것이 **옳다는 뜻인가** — 두 식은 각각 무엇을 답하는가?
- 이 주제의 정본은 어느 번호인가?

### 9. 왜 경고가 하나도 안 붙나 (왜) ★★★

- 멤버 순서가 나빠 8바이트를 버린 것 · 구멍에 쓰레기가 남은 것 · `memcmp` 로 비교한 것 —\
  `-Wall -Wextra`·`-pedantic`·UBSan 은 각각 몇 건을 내는가?
- ★★ 패딩 사고를 **sanitizer 가 원리상 못 잡는 이유**는 무엇인가?
- ★ `#pragma pack` 은 표준이 아닌데 **`-pedantic` 이 왜 침묵**하는가?
- 이 주제에서 쓸 수 있는 **유일한 자동 검사**는 무엇이고, 그것이 **못 박지 못하는 것**은 무엇인가?

### 10. 다섯 층과 무게중심 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / 구현 정의 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- **비어 있는 칸**은 무엇인가?
- ★★ 이 주제에서 **가장 두꺼운 칸**과 **두 번째로 두꺼운 칸**은 각각 무엇인가?
- ★ **구현 정의**와 **미명시**를 가르는 기준 한 줄은?
- ★ 「gcc 와 clang 이 같은 답을 냈다」는 어느 칸의 근거가 되는가 — 되기는 하는가?

### 11. 08 편과의 경계 — 어디까지가 이 주제인가 (연결) ★★

- `sizeof`·`_Alignof`·`offsetof`·`_Static_assert` **라는 도구**는 어느 주제가 정본인가?
- `#pragma pack(1)` 의 **UBSan 리포트**와 `__attribute__((packed))` 의 **경고 비대칭**은 어느 쪽인가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?
- **유연 배열 멤버**·**`memcmp` 의 계약**·**엄격한 앨리어싱**은 각각 어느 번호가 정본인가?
- ★ 구조체의 **초기화 규칙**(지정 초기자로 나머지가 0이 되는 것)은 어느 형제가 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
