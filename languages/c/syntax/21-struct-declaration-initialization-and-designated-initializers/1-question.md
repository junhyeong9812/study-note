# c/syntax/21 — 구조체 선언·초기화·지정 초기자: 「**구조체는 값이고, 배열은 값이 아니다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **「값인가 아닌가」**(구조체는 대입되고 배열은 안 된다) ② **「안 적은 멤버는 무엇이 되나」**
> ③ **「이 객체는 언제 죽나」**(복합 리터럴의 저장 기간).
> ★★★ **이 주제는 「표준」이 본체**다 — 초기화·대입 규칙은 어느 구현에서도 같다.
> 무게가 실리는 칸은 **UB** 하나뿐이고 그것이 **복합 리터럴의 수명**이다.
> ★ **「죽었다 / 안 죽었다」가 답이 아니다** — 어느 층이라서 그렇게 되는지를 답해라.
> ★ **한 벌만 돌리고 답하지 마라** — 6번은 `-O0` 과 `-O2` 가 갈리고, 11번은 **여덟 벌**을 돌려야 답이 보인다.
> 선행 — [01번 형제](../01-declaration-syntax-and-reading/) · [16번 형제](../16-array-pointer-decay-and-function-parameters/) · [20번 형제](../20-null-terminated-strings-and-string-literals/).
> 다음 — [22번 형제](../22-struct-padding-and-alignment/)가 **이 구조체의 바이트**를 연다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 구조체를 통째로 대입한 뒤 한쪽만 고치면 (예측) ★★★ 이 주제의 축

```c
/* s21a.c */
#include <stdio.h>
#include <string.h>

struct Rec {
    int  id;
    char name[8];      /* ★ 배열 멤버 */
    double rate;
};

int main(void) {
    struct Rec a = { 7, "kim", 1.5 };     /* 선언 + 초기화 */
    struct Rec b;                          /* 선언만 — 불확정 */
    b = a;                                 /* ★ 구조체 대입 */

    b.id = 9;
    b.name[0] = 'L';

    printf("a = { %d, \"%s\", %.1f }\n", a.id, a.name, a.rate);
    printf("b = { %d, \"%s\", %.1f }\n", b.id, b.name, b.rate);
    printf("a.name 과 b.name 은 같은 메모리인가 : %d  (0 이면 다른 메모리)\n",
           a.name == b.name);
    printf("배열 멤버가 따라왔나 : memcmp(a.name+1, b.name+1, 7) = %d\n",
           memcmp(a.name + 1, b.name + 1, 7));

    char x[8] = "kim", y[8];
    /* y = x;  <- 배열은 대입이 안 된다. 아래 블록에서 던진다 */
    memcpy(y, x, sizeof y);
    printf("맨 배열은 memcpy 로만 : y = \"%s\"\n", y);
    return 0;
}
```

- `a` 와 `b` 는 각각 어떻게 찍히는가?
- `a.name == b.name` 은 무엇을 묻는 식이고, 답은 무엇인가?
- ★ `memcmp(a.name + 1, b.name + 1, 7)` 은 얼마인가 — 그 수가 **무엇을 증명하는가**?
- ★★ 같은 파일의 마지막 두 줄에서 `y = x;` 를 쓰지 않고 `memcpy` 를 쓴 이유는?
- ★ 구조체 안에 `char *` 멤버가 있었다면 **무엇이 달라지는가**?

### 2. 같은 구조체를 네 꼴로 초기화하면 (예측) ★★★

```c
/* s21b.c */
#include <stdio.h>

struct Cfg { int port; int retry; char host[8]; double t; };

static void dump(const char *tag, struct Cfg c) {
    printf("%-14s port=%d retry=%d host=\"%s\" t=%.1f\n",
           tag, c.port, c.retry, c.host, c.t);
}

int main(void) {
    struct Cfg z = {0};                              /* 전부 0 */
    struct Cfg p = { 80 };                           /* 부분 초기화 */
    struct Cfg d = { .retry = 3, .host = "a" };      /* 지정 초기자 (C99) */
    struct Cfg m = { 8080, .t = 0.5 };               /* 섞어 쓰기 */

    dump("= {0}", z);
    dump("= { 80 }", p);
    dump(".retry .host", d);
    dump("8080, .t", m);

    printf("\n안 적은 멤버는 정적 초기화 규칙을 따른다 — 0 / 0.0 / '\\0'\n");
    printf("d.port = %d · d.t = %.1f · d.host[1] = %d\n", d.port, d.t, d.host[1]);
    return 0;
}
```

- 네 줄 `z` · `p` · `d` · `m` 은 각각 어떻게 찍히는가?
- ★ `d` 는 `.retry` 와 `.host` 만 적었다. **`d.port` 와 `d.t` 는 얼마인가**?
- ★ `m` 처럼 위치 초기자와 지정 초기자를 **섞어 써도 되는가**?
- 마지막 줄의 `d.host[1]` 은 얼마이고, 그 값은 **어느 규칙에서 나오는가**?
- ★★ 이 네 꼴에서 **초기자를 아예 안 줬다면** 무엇이 달라지는가 — 그것은 어느 주제가 정본인가?

### 3. 지정 초기자를 선언 순서와 다르게 쓰면 (예측) ★★

```c
/* s21c.c */
#include <stdio.h>

struct P { int a, b, c; };

int main(void) {
    struct P s = { .c = 3, .a = 1 };        /* ★ 순서 밖 — C 는 된다 */
    struct P t = { .a = 1, .a = 9 };        /* ★ 같은 멤버를 두 번 */
    int arr[6] = { [4] = 40, [1] = 10 };    /* 배열 지정 초기자 */

    printf("s = { %d, %d, %d }\n", s.a, s.b, s.c);
    printf("t = { %d, %d, %d }   <- 뒤엣것이 이긴다\n", t.a, t.b, t.c);
    printf("arr =");
    for (int i = 0; i < 6; i++) printf(" %d", arr[i]);
    printf("\n");
    return 0;
}
```

- `s` 는 어떻게 찍히는가 — **적은 순서**대로인가 **선언 순서**대로인가?
- ★ `t` 는 `.a` 를 두 번 적었다. **어느 쪽이 남는가**?
- `arr` 여섯 칸은 각각 얼마인가?
- ★★ 이 세 줄 중 **경고가 붙는 줄**은 몇 개이고 어느 줄인가?
- 경고가 붙었다면 **`cc exit`** 는 얼마인가?

### 4. 중첩과 익명을 한 구조체에 섞으면 (예측) ★★

```c
/* s21d.c */
#include <stdio.h>
#include <stddef.h>

struct Outer {
    int tag;
    struct Inner { int x, y; } in;   /* 중첩 — 안쪽 태그도 바깥 스코프에 생긴다 */
    struct { int u, v; };            /* ★ 익명 구조체 멤버 (C11) */
};

int main(void) {
    struct Outer o = { .tag = 1, .in = { .y = 20 }, .u = 5 };
    struct Inner i = { 7, 8 };       /* 바깥에서도 쓸 수 있다 */

    o.in.x = 9;
    o.v = 6;                         /* ★ 한 단계 없이 바로 */

    printf("o.tag=%d o.in={%d,%d} o.u=%d o.v=%d\n", o.tag, o.in.x, o.in.y, o.u, o.v);
    printf("i={%d,%d}\n", i.x, i.y);
    printf("offsetof: tag=%zu in=%zu in.x=%zu u=%zu v=%zu  sizeof=%zu\n",
           offsetof(struct Outer, tag), offsetof(struct Outer, in),
           offsetof(struct Outer, in.x), offsetof(struct Outer, u),
           offsetof(struct Outer, v), sizeof(struct Outer));
    return 0;
}
```

- 첫 두 줄은 어떻게 찍히는가?
- ★ `struct Inner i = { 7, 8 };` 이 **바깥 함수에서 되는** 이유는?
- ★★ `o.v = 6;` 처럼 **한 단계를 건너뛰는** 것이 되는 이유는?
- `offsetof` 다섯 값과 `sizeof` 는 각각 얼마인가?
- ★ 이 소스를 `-std=c99 -pedantic` 으로 던지면 **무엇이 나오는가**?

### 5. 복합 리터럴을 인자·대입·전역·블록 네 자리에 두면 (예측) ★★

```c
/* s21e.c */
#include <stdio.h>

struct P { int x, y; };

static int sum(struct P p) { return p.x + p.y; }

static void blockscope(void) {
    for (int k = 0; k < 2; k++) {
        struct P *q = &(struct P){ .x = 1, .y = 2 };   /* 블록 안 복합 리터럴 */
        printf("  %d 바퀴: q->x=%d ", k, q->x);
        q->x = 99;                                     /* ★ 수정 가능한 lvalue */
        printf("-> 고치면 %d\n", q->x);
    }   /* <- 바퀴마다 여기서 수명이 끝나고 다음 바퀴에 다시 만들어진다 */
}

static struct P g = { 0 };
static struct P *gp = &(struct P){ 7, 8 };             /* 파일 스코프 = 정적 저장 기간 */

int main(void) {
    printf("인자로 넘기기 : sum((struct P){3,4}) = %d\n", sum((struct P){ 3, 4 }));
    g = (struct P){ .y = 5 };
    printf("통째로 대입   : g = {%d,%d}\n", g.x, g.y);
    printf("파일 스코프   : gp->x=%d gp->y=%d\n", gp->x, gp->y);
    printf("블록 스코프 — 자동 저장 기간이다\n");
    blockscope();
    return 0;
}
```

- 네 줄은 각각 어떻게 찍히는가?
- ★ `g = (struct P){ .y = 5 };` 뒤의 `g.x` 는 얼마인가 — **왜 그런가**?
- ★★ `blockscope()` 의 두 바퀴는 **각각 무엇으로 시작하는가** — 첫 바퀴에서 99 로 고친 것이 두 번째 바퀴에 남는가?
- `q->x = 99;` 가 **합법인** 이유는 — 복합 리터럴은 상수인가 객체인가?
- ★ 파일 스코프의 `gp` 와 블록 안의 `q` 는 **무엇이 다른가**?

### 6. 함수가 복합 리터럴의 주소를 돌려주면 (예측) ★★★ 본체

```c
/* s21e2.c */
#include <stdio.h>

struct P { int x, y; };

static struct P *make(int v) {
    return &(struct P){ .x = v, .y = v * 10 };   /* ★ 함수가 끝나면 수명이 끝난다 */
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    fprintf(stderr, "--- (가) 복합 리터럴 주소를 반환받는다 ---\n");
    struct P *p = make(3);
    fprintf(stderr, "--- (나) 이제 역참조한다 ---\n");
    printf("p->x = %d p->y = %d\n", p->x, p->y);
    return 0;
}
```

- `gcc -O0` 으로 돌리면 무엇이 찍히는가?
- ★★ `gcc -O2` 로 돌리면 무엇이 찍히는가 — **`-O0` 과 같은가**?
- ★★★ 두 벌의 **`run exit`** 는 각각 얼마인가?
- ASan 으로 돌리면 어떤 진단이 나오고, **그 진단이 가리키는 줄**은 몇 번 줄인가?
- ★ 소스 첫 줄의 `setvbuf(stdout, NULL, _IONBF, 0)` 와 **마커를 `stderr` 로 찍은 것**은 각각 무엇을 막으려는 것인가?

### 7. 배열 대입과 구조체 비교가 왜 에러인가 (왜) ★★

```c
/* s21f.c */
struct P { int x, y; };

int main(void) {
    char a[4] = "abc", b[4];
    struct P s = { 1, 2 }, t = { 1, 2 };
    int arr[3];

    b = a;                      /* (1) 배열은 대입이 안 된다 */
    if (s == t) return 1;       /* (2) 구조체는 == 가 없다 */
    arr = (int[3]){1, 2, 3};    /* (3) 복합 리터럴도 배열이면 마찬가지 */
    return 0;
}
```

- 이 소스에서 **에러는 몇 건**이고 각각 어느 줄인가?
- ★ `b = a;` 와 `arr = (int[3]){1,2,3};` 은 **같은 에러인가 다른 에러인가**?
- ★★ `s == t` 의 에러 문구는 무엇을 말하고 있는가 — 구조체에 `==` 가 **없다**는 뜻인가 **다르다**는 뜻인가?
- 「그럼 `memcmp` 로 비교하면 되겠다」의 함정은 무엇이고, 어느 주제가 정본인가?
- ★ 이 블록 끝의 경고 두 건은 에러와 관계가 있는가 — 그런데 왜 **지우지 않고** 실었는가?

### 8. 네 초기화 꼴 중 어디에 경고가 붙나 (경계) ★★★

- 2번 소스의 네 꼴 가운데 **`-Wall -Wextra` 가 경고하는 것은 몇 개**인가?
- ★★ 네 꼴은 **뜻이 전부 같은데** 경고가 갈린 이유는 무엇인가?
- `-Wmissing-field-initializers` 는 **무엇을 보는 경고**인가 — 꼴인가 뜻인가?
- ★★★ 이 사실에서 나오는 **실무 규칙 한 줄**은 무엇인가?
- ★ 「경고 0건이니 초기화를 다 적었다」는 어디가 틀렸는가?

### 9. 같은 초기자를 C++ 컴파일러에 던지면 (경계) ★★★

```cpp
/* s21g.cpp */
#include <cstdio>

struct P { int a, b, c; };

int main() {
    P s = { .c = 3, .a = 1 };     /* C 에서는 되던 순서 밖 지정 초기자 */
    std::printf("%d %d %d\n", s.a, s.b, s.c);
    return 0;
}
```

- `g++ -std=c++17` 로 던지면 **경고와 에러가 각각 몇 건**인가?
- ★★ `-std=c++20` 으로 올리면 **에러가 사라지는가**?
- ★★★ 남는 에러의 문구는 무엇을 요구하고 있는가 — C 는 그것을 요구하는가?
- 두 벌의 **`cc exit`** 는 얼마인가?
- ★ 헤더 하나를 C 와 C++ 양쪽에서 include 하는 프로젝트에서 **무엇이 먼저 깨지는가**?

### 10. 「언제부터인가」를 컴파일러에게 물어보는 법 (경계) ★★

- 익명 구조체 멤버는 **어느 표준부터**이고, 그 사실을 **어떤 명령으로** 확인했는가?
- ★ 빈 중괄호 `= {}` 는 어느 표준부터이고, `-std=c17` 에서 던지면 무엇이 나오는가?
- ★★ 그때 **`cc exit`** 는 얼마인가 — 컴파일은 되는가?
- ★★★ `-pedantic` 을 빼면 두 진단은 어떻게 되는가 — 「`-std=c17` 로 돌렸다」는 「C17 로 검증했다」인가?
- ★ gcc 13 에서 C23 을 켜는 플래그 이름은 무엇인가?

### 11. 댕글링을 도구가 언제 보나 (왜) ★★★

- 6번의 UB 를 **gcc `-O0`** 으로 컴파일하면 경고가 **몇 건**인가?
- ★★ **gcc `-O1`·`-O2`·`-O3`** 은 각각 몇 건인가 — 무슨 진단인가?
- ★★★ **clang 18 은 `-O0`\~`-O3` 에서 각각 몇 건**인가?
- 이 여덟 벌의 **`cc exit`** 는 전부 얼마인가 — 그것을 같이 봐야 하는 이유는?
- ★ 경고를 셀 때 `grep -c warning` 이 아니라 **`grep -c 'warning:'`** 을 쓴 이유는?
- ★★ 이 표에서 나오는 결론 한 줄은 — 경고는 **코드의 성질**인가 **빌드 설정의 성질**인가?

### 12. 다섯 층과 경계 (연결) ★★

- 이 주제에서 **표준 / 조건부 표준 / 구현 정의 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- **비어 있는 칸**은 무엇인가?
- ★★ 이 주제에서 **가장 두꺼운 칸**은 무엇인가 — [20번 형제](../20-null-terminated-strings-and-string-literals/)와 **어느 칸이 정반대**인가?
- ★ 「구조체의 크기와 패딩 자리」는 이 주제인가 다른 주제인가 — 어느 쪽이 정본인가?
- ★ 「복합 리터럴 전반」과 「초기화 안 한 객체」는 각각 어느 주제가 정본인가?
- 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
