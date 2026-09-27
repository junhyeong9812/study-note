# c/syntax/38 — 소유권 관례를 코드로 표현하기: 「**C 의 타입은 「누가 놓나」를 말하지 않는다 — 이름·주석·문서가 말하고, 도구는 그 말을 들을 때만 돕는다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · gcc-12 12.4.0 · clang 18.1.3 · glibc 2.39 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **선언만 보고 판정이 서나**(표준 함수 · 내 API) ② **관례를 어기면 무엇이 잡나**(보통 빌드 · ASan 두 판 · 컴파일 경고)
> ③ **관례를 컴파일러가 읽게 하기**(gcc 속성 · 그 한계 · C++·Rust).
> ★★★ **본체는 판정표** — 1번은 **칸마다 「놓나 · 무엇으로 · 근거」** 를 적어야 답이다. ★ 근거 칸에 「타입이 그렇다」는 쓸 수 없다고 생각되면, **그 생각 자체가 답의 절반**이다.
> 선행 — [37번 형제](../37-malloc-calloc-realloc-free/).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **3번은 경우마다 세 칸**(보통 빌드 · gcc ASan · clang ASan)을 적어라 — 칸마다 **종류 이름**까지.
- ★★ **「적법하지만 누수」와 「UB」를 갈라** 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 포인터를 받은 쪽이 놓아야 한다는 사실은 어디에 적혀 있나**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 선언 열 개 — 호출자가 놓나 (예측) ★★★ 이 주제의 축

```c
/* s38sig.h */
#include <stddef.h>
#include <stdio.h>

typedef struct buf buf;

char       *strdup(const char *s);
char       *getenv(const char *name);
char       *strerror(int errnum);
char       *strtok(char *s, const char *delim);
void       *realloc(void *ptr, size_t size);
FILE       *fopen(const char *path, const char *mode);
buf        *buf_create(size_t cap);
const char *buf_peek(const buf *b);
int         buf_get(const buf *b, char **out);
void        buf_sink(buf *b);
```

★ `buf` 의 네 함수는 아래 헤더의 것이다(3번에서 쓴다).

```c
/* s38buf.h */
#ifndef S38BUF_H
#define S38BUF_H
#include <stddef.h>

/* 소유권 표기 규칙 (이 헤더의 약속)
 *   _create        : 새 객체를 만든다 — 호출자가 소유하고 짝인 _destroy 로 놓는다
 *   _destroy       : 소유한 것을 놓는다 — NULL 이면 아무것도 안 한다
 *   _peek          : 빌려준다 — 객체가 살아 있고 바뀌지 않는 동안만 유효, 놓지 않는다
 *   char **out     : 성공(0)이면 *out 은 호출자 소유 — free 로 놓는다 · 실패면 *out 은 NULL
 *   _sink          : 인자를 가져간다 — 부른 뒤 호출자는 그 포인터를 쓰지도 놓지도 않는다
 */
typedef struct buf buf;

void buf_destroy(buf *b);

#if defined(__GNUC__) && !defined(__clang__) && __GNUC__ >= 11
#define BUF_OWNED __attribute__((malloc, malloc(buf_destroy, 1)))
#else
#define BUF_OWNED
#endif

BUF_OWNED buf *buf_create(size_t cap);
const char    *buf_peek(const buf *b);
int            buf_get(const buf *b, char **out);
void           buf_sink(buf *b);

#endif
```

- ★★★ 각 선언의 반환(또는 출력)을 호출자가 **놓는가**? 놓는다면 **무엇으로**?
- ★★★ 그 판정의 **근거**는 각각 어디에 있는가?
- ★★ **반환 타입만으로** 판정이 서는 칸은 몇 개인가?
- ★ `buf_peek` 의 `const` 는 판정을 **보장**하는가?

### 2. `-std=c17` 에서 `strdup` 부르기 (예측) ★★

```c
/* s38s.c */
#include <stdlib.h>
#include <string.h>

int main(void) {
    char *s = strdup("hello");
    int ok = s != NULL;
    free(s);
    return !ok;
}
```

- ★★ gcc-12 · gcc · clang 을 `-std=c17` · `-std=c2x` · `-std=gnu17` 로 컴파일하면 각 칸의 **`exit` · 경고 · 에러 수**는?
- ★★ gcc `-std=c17` 판의 두 경고는 무엇을 말하는가? 그 바이너리를 **실행해 봐도 되는가**?
- ★ `-pedantic-errors` 를 주면 gcc 는?

### 3. 관례를 어기는 여섯 경우 (예측) ★★★

```c
/* s38v.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "s38buf.h"

int main(int argc, char **argv) {
    setvbuf(stdout, NULL, _IONBF, 0);
    int k = argc > 1 ? atoi(argv[1]) : 0;
    buf *b = buf_create(8);
    if (!b) return 1;
    char *s = NULL;
    switch (k) {
    case 0:                                   /* 헤더의 약속대로 */
        if (buf_get(b, &s) == 0) { printf("[0] %s\n", s); free(s); }
        printf("[0] %s\n", buf_peek(b));
        buf_destroy(b);
        break;
    case 1:                                   /* _get 의 *out 을 놓지 않는다 */
        if (buf_get(b, &s) == 0) printf("[1] %s\n", s);
        buf_destroy(b);
        break;
    case 2:                                   /* _sink 뒤에 _destroy */
        buf_sink(b);
        buf_destroy(b);
        break;
    case 3: {                                 /* getenv 결과를 free */
        char *home = getenv("PATH");
        printf("[3] getenv 가 NULL 인가 %d\n", home == NULL);
        free(home);
        buf_destroy(b);
        break;
    }
    case 4:                                   /* _create 의 결과를 free */
        free(b);
        break;
    case 5: {                                 /* _peek 결과를 _destroy 뒤에 */
        const char *v = buf_peek(b);
        buf_destroy(b);
        printf("[5] %d\n", v[0] == 'h');
        break;
    }
    case 6: {                                 /* strerror 결과를 free */
        char *m = strerror(2);
        printf("[6] strerror 가 NULL 인가 %d\n", m == NULL);
        free(m);
        buf_destroy(b);
        break;
    }
    }
    return 0;
}
```

`./x 0` \~ `./x 6` 을 **보통 빌드 · gcc ASan · clang ASan** 으로 돌린다(`s38buf.c` 와 함께, `-O0`).

- ★★★ 경우 [1]\~[6] 각각에서 **세 칸의 결과**(종료 코드 · 리포트 종류)는?
- ★★★ [2](`buf_sink` 뒤 `buf_destroy`)에서 ASan 이 말하는 **종류 이름**은 `double-free` 인가?
- ★★ [3](`getenv` 결과 `free`)에서 ASan 은 그 주소가 **어디에** 있다고 말하는가?
- ★★ 여섯 경우 × ASan 두 판 = 12 칸 중 **리포트가 없는 칸**이 있는가?

### 4. 짝을 선언한 헤더 — `-Wmismatched-dealloc` (예측) ★★

```c
/* s38m.c */
#define _POSIX_C_SOURCE 200809L
#include <stdlib.h>
#include <string.h>
#include "s38buf.h"

void wrong_pairs(void) {
    buf *b = buf_create(4);
    free(b);                                  /* _create 의 짝이 아닌 것 */
    char *s = strdup("x");
    buf_destroy((buf *)s);                    /* strdup 의 짝이 아닌 것 */
}
```

- ★★ gcc-12 · gcc 13 · clang 은 `s38m.c` 의 **두 줄** 중 어느 줄을 경고하는가?
- ★★ 경고가 안 나는 줄이 있다면, 그 이유를 **헤더에서** 찾으면?
- ★ `-fanalyzer` 와 `clang --analyze` 는?

### 5. 속성을 가드 없이 쓰면 (예측) ★★

```c
/* s38attr.c */
typedef struct buf buf;
void buf_destroy(buf *b);
__attribute__((malloc, malloc(buf_destroy, 1))) buf *buf_create(unsigned long cap);
```

- ★★ gcc 13 과 clang 18 의 `cc exit` 는?
- ★ 그래서 `s38buf.h` 는 속성을 **어떤 조건**에서만 펼치는가?

### 6. C++ 로 같은 이전을 쓰면 (예측) ★★

```cpp
// s38x.cpp
#include <memory>

struct Buf { int n = 0; };

std::unique_ptr<Buf> buf_create() { return std::make_unique<Buf>(); }
void buf_sink(std::unique_ptr<Buf> b) { (void)b; }

int main() {
    auto b = buf_create();
    buf_sink(b);                             // std::move 없이 넘긴다
    return 0;
}
```

- ★★ g++ 는 `buf_sink(b)` 에 무엇이라고 말하는가?
- ★ `std::move(b)` 로 넘긴 뒤 `b == nullptr` 은?

### 7. 이름 접미사 다섯 (왜) ★★

- ★★ `_create`/`_destroy` · `_peek` · `char **out` · `_sink` 는 각각 **어떤 규칙**을 싣는가?
- ★★ 규칙을 **헤더 첫머리에 한 번** 적는 것이 함수마다 흩어 적는 것보다 나은 이유는?

### 8. 출력 매개변수의 실패 (경계) ★★

- ★★ `int buf_get(const buf *b, char **out)` 이 실패했을 때 `*out` 을 `NULL` 로 두는 것은 호출자에게 **무엇을 허락**하는가?
- ★ 반환값 하나로 「실패」와 「소유 이전」을 같이 말하는 설계(`char *` 반환 · 실패 시 `NULL`)와 비교하면?

### 9. 옳은 코드에 분석기 경고 (경계) ★★

```c
/* s38an.c */
#include <stdlib.h>

typedef struct node { int v; } node;
void node_destroy(node *n);
__attribute__((malloc, malloc(node_destroy, 1))) node *node_create(int v);

node *node_create(int v) {                    /* 정의가 같은 번역 단위에 있다 */
    node *n = malloc(sizeof *n);
    if (n) n->v = v;
    return n;
}
void node_destroy(node *n) { free(n); }

int use(void) {
    node *n = node_create(7);
    if (!n) return -1;
    int v = n->v;
    node_destroy(n);                          /* 헤더가 말한 짝으로 놓는다 */
    return v;
}
```

- ★★ gcc `-fanalyzer` 는 이 옳은 코드에 무엇을 말하는가? 왜 그렇게 말하는 것으로 보이는가?
- ★ 그 경고를 **판정**으로 쓰면 무엇이 잘못되는가?

### 10. Rust 는 어디서 막나 (연결) ★★

- ★★ `fn buf_sink(b: Buf)` 를 두 번 부르면 rustc 는 **몇 번 진단**으로 무엇을 말하는가?
- ★ 그 진단 속 문장 중 **C 의 헤더 주석이 하던 말**은 어느 것인가?

### 11. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- 이 주제에서 **표준 / 구현 정의 / 컴파일러 구현 / UB** 칸, 그리고 **층 밖의 관례** 칸에 각각 무엇이 들어가는가?
- ★★★ 「이 포인터를 놓아야 하나」를 **판정하는 도구**가 있었는가?
- ★★ ASan 이 **스스로 죽은** 칸은 어디이고, 그것을 「답했다」로 세는 것은 옳은가?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

- **`free` 의 계약**과 **크기를 숨기는 불투명 타입**은 각각 어느 형제가 정본인가?
- **해제 후 사용의 코드 패턴**은 목록의 몇 번 주제인가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
