# c/syntax/44 — 헤더와 분할 컴파일: 「**헤더는 include 한 모든 번역 단위에 그대로 복사된다 — 그래서 헤더에는 복사돼도 정의가 하나로 남는 것만 둔다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · gcc-12 12.4.0 · clang 18.1.3 · g++ 13.3.0 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **헤더에 무엇을 두면 링크가 깨지나**(선언 · 정의 · `static` · `const` · 타입) ② **두 번 들어오는 것을 무엇이 막나**(guard 대 `#pragma once` · 경로가 다른 같은 파일)
> ③ **헤더끼리의 순환과 재컴파일**(전방 선언 · `-H` · `-MMD`).
> ★★★ **본체 창은 링크 결과 + `nm`** — 1번은 **칸마다 「링크 성공 / `multiple definition` / `undefined reference`」** 와 `nm` 글자를 적어야 답이다.
> 선행 — [29번 형제](../29-scope-and-linkage-static-extern/) · [41번 형제](../41-preprocessor-directives-and-conditional-compilation/).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **1번은 행마다 「이 줄이 두 `.o` 에 무엇을 남기나(정의 · 참조 · 없음)」를 먼저 적고** 그다음 링크 결과를 적어라.
- ★★ **「컴파일 에러」와 「링크 에러」를 갈라** 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 정의는 프로그램에 몇 개인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 헤더 배치 격자 — 헤더 내용 열넷 × 빌드 다섯 (예측) ★★★ 이 주제의 축

```c
/* s44h.h */
#if K == 1 || K == 2
int hf(int x);
#elif K == 3
int hf(int x) { return x + 1; }
#elif K == 4
static int hf(int x) { return x + 1; }
#elif K == 5
static inline int hf(int x) { return x + 1; }
#elif K == 6 || K == 7
extern int hv;
#elif K == 8
int hv = 0;
#elif K == 9
int hv;
#elif K == 10
static int hv = 0;
#elif K == 11
const int hv = 5;
#elif K == 12
struct hs { int v; };
#elif K == 13
enum he { HE_ONE = 1 };
#elif K == 14
typedef int ht;
#endif
```

```c
/* s44a.c */
#include "s44h.h"

#if K == 2
int hf(int x) { return x + 1; }
#elif K == 7
int hv = 0;
#endif

int use_a(void) {
#if K <= 5
    return hf(1);
#elif K <= 11
    return hv;
#elif K == 12
    struct hs s = { 1 };
    return s.v;
#elif K == 13
    return HE_ONE;
#else
    ht t = 1;
    return t;
#endif
}
```

```c
/* s44b.c */
#include "s44h.h"

int use_a(void);

int use_b(void) {
#if K <= 5
    return hf(2);
#elif K <= 11
    return hv;
#elif K == 12
    struct hs s = { 2 };
    return s.v;
#elif K == 13
    return HE_ONE;
#else
    ht t = 2;
    return t;
#endif
}

int main(void) { return use_a() + use_b() == 0; }
```

칸 = `$CC -O0 -Wall -Wextra -DK=<행>` 으로 `s44a.c`·`s44b.c` 를 **따로 `-c`** 한 뒤 두 `.o` 를 링크한 결과.
빌드 다섯은 **gcc · gcc-12 · clang(`-std=c17`) · gcc `-std=c17 -fcommon` · g++ `-x c++ -std=c++17`**.
`K` 1·2 는 헤더가 같고 2 만 `s44a.c` 에 `hf` 정의가 있다. `K` 6·7 도 같다(7 만 `int hv = 0;`).

- ★★★ `K` = 1\~14 의 gcc 칸은 각각 무엇인가? **깨지는 행**은 몇 개이고 두 종류로 나누면?
- ★★★ gcc · gcc-12 · clang 이 **서로 갈리는 행**이 있는가?
- ★★ `-fcommon` 칸과 g++ 칸이 gcc 칸과 **다른 행**은 각각 어느 것인가?
- ★★ gcc `-O0` 의 `nm s44a.o` / `nm s44b.o` 에서 `hf`·`hv` 의 글자는 행마다 무엇인가?

### 2. 헤더의 `static` 을 두 파일이 쓰면 (예측) ★★★

```c
/* s44s.h */
static int hcount;
static int hbump(void) { return ++hcount; }
```

```c
/* s44sa.c */
#include "s44s.h"

typedef int (*bump_fn)(void);

int a_bump(void) { return hbump(); }
bump_fn a_fn(void) { return hbump; }
```

```c
/* s44sb.c */
#include <stdio.h>
#include "s44s.h"

typedef int (*bump_fn)(void);

int a_bump(void);
bump_fn a_fn(void);

int main(void) {
    int a1 = a_bump();
    int a2 = a_bump();
    int b1 = hbump();
    printf("a_bump() -> %d, %d · hbump() -> %d · a_fn() == hbump : %d\n",
           a1, a2, b1, a_fn() == hbump);
    return 0;
}
```

- ★★★ 이 프로그램은 무엇을 찍는가? `a_fn() == hbump` 는?
- ★★ `nm s44sa.o s44sb.o` 에서 `hbump`·`hcount` 는 몇 번, 어떤 글자로 나오는가?

### 3. 쓰지 않는 헤더 함수 (예측) ★★

```c
/* s44i.h */
static inline int hinc(int x) { return x + 1; }
```

```c
/* s44u.c */
#include "s44s.h"
#include "s44i.h"

int nothing(void) { return 0; }
```

- ★★ `gcc`·`clang -std=c17 -Wall -Wextra -pedantic -c s44u.c` 는 각각 무엇을 경고하는가? `hinc` 에 대해서는?

### 4. include guard 대 `#pragma once` (예측) ★★★

```c
/* s44n.h */
struct gq { int v; };
```

```c
/* s44g.h */
#ifndef S44G_H
#define S44G_H

struct gq { int v; };

#endif
```

```c
/* s44p.h */
#pragma once

struct gq { int v; };
```

```c
/* s44m.c */
#include FIRST
#include SECOND

int main(void) {
    struct gq q = { 0 };
    return q.v;
}
```

`d1/` 에 세 헤더를 두고, 두 번째 include 를 여섯 경로로 준다 —
`d1/`(같은 경로) · `d3/`(`d1` 을 가리키는 **디렉토리 심볼릭 링크**) · `d5/`(**파일 심볼릭 링크**) · `d6/`(**하드 링크**) · `d2/`(`cp -p` **사본 — 같은 mtime**) · `d4/`(사본 — **다른 mtime**).
칸 = `$CC -std=c17 -DFIRST="d1/<헤더>" -DSECOND="<디렉토리>/<헤더>" -c s44m.c` 의 결과(통과 / 재정의 에러).

- ★★★ 헤더 셋 × 경로 여섯 × (gcc · gcc-12 · clang) 54칸은?
- ★★★ gcc 와 clang 이 **갈리는 행**이 있다면 어느 것인가?
- ★★ `gcc -H` 로 보면 `#pragma once` 사본(같은 mtime)과 guard 사본은 각각 **몇 개의 파일을 여나**?

### 5. 서로를 include 하는 두 헤더 (예측) ★★★

```c
/* s44ea.h */
#ifndef S44EA_H
#define S44EA_H

#include "s44eb.h"

struct ea { int id; struct eb inner; };

#endif
```

```c
/* s44eb.h */
#ifndef S44EB_H
#define S44EB_H

#include "s44ea.h"

struct eb { int id; struct ea *owner; };

#endif
```

```c
/* s44e1.c */
#include "s44ea.h"
#include "s44eb.h"

int main(void) {
    struct ea a = { 1, { 2, 0 } };
    a.inner.owner = &a;
    return a.inner.owner->id - 1;
}
```

```c
/* s44e2.c */
#include "s44eb.h"
#include "s44ea.h"

int main(void) {
    struct ea a = { 1, { 2, 0 } };
    a.inner.owner = &a;
    return a.inner.owner->id - 1;
}
```

- ★★★ `s44e1.c` 와 `s44e2.c` 는 각각 컴파일되는가? 안 되는 쪽의 에러(gcc · clang)는?
- ★★ `gcc -std=c17 -E -P` 로 보면 두 파일에서 `struct ea` 와 `struct eb` 는 **어느 순서로** 나오는가?

### 6. include 트리와 의존성 파일 (예측) ★★

```c
/* s44fa.h */
#ifndef S44FA_H
#define S44FA_H

#include "s44fb.h"

struct fa { int id; struct fb inner; };

#endif
```

```c
/* s44fb.h */
#ifndef S44FB_H
#define S44FB_H

struct fa;

struct fb { int id; struct fa *owner; };

#endif
```

```c
/* s44t.c */
#include <stddef.h>
#include "s44fa.h"

size_t fa_size(void) { return sizeof(struct fa); }
```

- ★★ `gcc -std=c17 -H -c s44t.c -o s44t.o` 는 무엇을 찍는가?
- ★★ `-MMD` 와 `-MD` 로 만든 `s44t.d` 는 각각 무엇을 담는가? `s44fb.h` 를 고치면 무엇을 다시 만들어야 하나?

### 7. 헤더에 둬도 되는 것의 공통점 (왜) ★★★

- 1번에서 **gcc 칸이 링크 성공**인 행들의 공통점을 「외부 정의가 프로그램에 몇 개인가」로 설명하라.
- ★★ `static` 정의 행(4·10)을 헤더에 두는 것을 **권하지 않는** 이유는 무엇인가? 2·3번과 이어서 답하라.

### 8. `const` 행의 두 언어 (경계) ★★

- 1번 11행(`const int hv = 5;`)의 gcc 칸과 g++ 칸 결과를 **파일 스코프 `const` 의 링크**로 설명하라. `nm` 글자는 각각 무엇인가?
- ★ C 에서 상수를 헤더에 두는 옳은 방법 셋은?

### 9. 이미 잰 격자 — 29편 · 39편 (연결) ★★

- 1번 9행(`int hv;`)의 결과가 **플래그와 컴파일러 판**에 따라 어떻게 달라지는지 잰 격자는 어느 형제에 있는가? 기본값이 바뀐 판은?
- ★ 헤더의 `extern inline` 은 어떻게 되는가(39편)?

### 10. 명세에 없는 것 · 명세가 허용하는데 안 되는 것 (경계) ★★

- `#pragma once` 는 N3220 에 있는가? 그래서 4번의 `s44p.h` 행들의 결과는 어느 층인가?
- ★★ C23 은 같은 내용의 `struct` 재정의를 어떻게 다루나? 이 판의 gcc · clang `-std=c2x` 는?

### 11. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- 이 주제에서 **표준 / UB / 조건부 표준 / 컴파일러 구현** 칸에 각각 무엇이 들어가는가?
- ★★★ 컴파일 · 링크 · 경고가 **전부 0줄인데 틀린** 자리 둘은?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

- **링커 일반**은 어느 문서가 정본이고, 이 편과의 경계는?
- ★ 링크 에러를 **거꾸로 읽는 법**은 목록의 몇 번 주제인가? **전방 선언 + 포인터**의 다른 쓸모는 몇 번 형제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
