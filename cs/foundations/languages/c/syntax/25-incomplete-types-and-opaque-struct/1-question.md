# c/syntax/25 — 불완전 타입과 opaque struct: 「**도면 없이 열쇠만 받은 방**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **컴파일 에러 문구**(무엇이 왜 막히나) ② **종료 코드**(`cc exit=0` 인가 `1` 인가)
> ③ **그 사실이 다섯 층 중 어느 칸인가**(표준인가 확장인가 UB 인가).
> ★★★ **이 주제는 「표준」 칸이 본체**다 — [22번 형제](../22-struct-padding-and-alignment/)·[24번 형제](../24-bit-fields/)와 **정반대**로 구현 정의·미명시 칸이 거의 비어 있다.
> 두 번째가 **UB** 인데 **자리가 하나뿐**이고, ★★ **그 하나를 보는 도구가 없다**(6번).
> ★★ **「경고 몇 건」만 세지 마라** — 이 주제에는 **경고가 났는데 `cc exit=0`** 인 자리가 세 군데다.
> 선행 — [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/) · 목록의 **44번 주제**.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1·3·4·5·6·8)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **5번과 6번은 「되나 안 되나」가 아니라 「종료 코드가 얼마인가」를 적어야 답이다.**
  「경고가 난다」까지만 적으면 **절반만 맞은 것**이다.
- ★★ **6번은 한 벌로 답하지 마라** — **네 벌**(gcc · clang · `-flto` · ASan+UBSan)을 다 적어야 한다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 컴파일 시간에 드러나나 실행 시간에 드러나나**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 선언만 해 둔 구조체로 여섯 가지를 해 보면 (예측) ★★★ 이 주제의 축

```c
/* s25a.c */
#include <stdio.h>

struct Hidden;                      /* 선언만 했다 — 불완전 타입 */

struct Hidden *make(void);          /* (가) 포인터는 된다 */
void use(struct Hidden *p);         /* (나) 매개변수로도 된다 */

int main(void) {
    struct Hidden *p = make();      /* OK */
    use(p);                         /* OK */

    struct Hidden v;                /* (1) 변수로 못 만든다 */
    struct Hidden a[3];             /* (2) 배열 원소로 못 쓴다 */
    printf("%zu\n", sizeof(struct Hidden));   /* (3) 크기를 못 묻는다 */
    printf("%d\n", p->x);           /* (4) 멤버를 못 만진다 */

    (void)v; (void)a;
    return 0;
}
```

- 위 `(가)`·`(나)` 두 선언은 통과하는가?
- `(1)`\~`(4)` 는 각각 통과하는가, 아니면 무엇이라고 하는가?
- ★ `cc exit` 는 얼마인가?
- ★★ 네 가지가 막히는 이유를 **한 문장**으로 묶으면?
- ★ gcc 와 clang 이 **덧붙이는 것**이 서로 다르다 — 무엇이 다른가?
- ★ 이 중 **실행 시간까지 새어 나가는 것**이 있는가?

### 2. 경계는 왜 하필 거기인가 (왜) ★★

- 왜 **포인터**는 되고 **변수**는 안 되는가?
- ★ `struct Hidden *p;` 는 되는데 `struct Hidden a[3];` 는 안 되는 이유는?
- ★★ 불완전 타입이 「**그 지점에서의 상태**」라는 말은 무슨 뜻인가?
- ★ 불완전 타입을 만드는 방법은 몇 가지인가? 각각을 **완성하는 법**은?
- ★★ 그중 **영원히 완성할 수 없는 것**은 무엇이고, 왜인가?

### 3. 헤더에 이름만 두고 셋으로 나눠 빌드하면 (예측) ★★★

```c
/* s25b.h */
#ifndef S25B_H
#define S25B_H

/* ★ 여기에 있는 것은 「이름」뿐이다 — 멤버가 무엇인지 쓰여 있지 않다 */
typedef struct Counter Counter;

Counter *ctr_new(long step);
void     ctr_tick(Counter *c);
long     ctr_get(const Counter *c);
void     ctr_free(Counter *c);

#endif
```

```c
/* s25b.c */
#include <stdlib.h>
#include "s25b.h"

struct Counter {                    /* ★ 정의는 이 번역 단위에만 있다 */
    long n;
    long step;
};

Counter *ctr_new(long step) {
    Counter *c = malloc(sizeof *c); /* 크기를 아는 것은 여기뿐이다 */
    if (c) { c->n = 0; c->step = step; }
    return c;
}
void ctr_tick(Counter *c)       { c->n += c->step; }
long ctr_get(const Counter *c)  { return c->n; }
void ctr_free(Counter *c)       { free(c); }
```

```c
/* s25b_main.c */
#include <stdio.h>
#include "s25b.h"

int main(void) {
    Counter *c = ctr_new(5);
    ctr_tick(c); ctr_tick(c); ctr_tick(c);
    printf("ctr_get = %ld\n", ctr_get(c));
    printf("포인터 크기는 안다 : sizeof(Counter *) = %zu\n", sizeof(Counter *));
    ctr_free(c);
    return 0;
}
```

- `gcc -c` 로 두 `.c` 를 따로 번역하고 링크하면 성공하는가?
- 실행하면 `ctr_get` 은 얼마를 돌려주는가?
- ★★ 쓰는 쪽이 **알 수 있는 크기**는 무엇이고 그 값은 얼마인가?
- ★★ `sizeof *c` 를 쓰는 곳이 **프로그램 전체에서 몇 군데**인가? 그것이 무엇을 가능하게 하나?
- ★ 헤더에 `ctr_free` 가 **반드시 있어야 하는 이유**는?
- ★ `struct` 를 안 쓰고 `Counter` 라고만 적을 수 있는 이유는?

### 4. 쓰는 쪽에서 값으로 품거나 스택에 놓으면 (예측) ★★

```c
/* s25c.c */
#include <stdio.h>
#include "s25b.h"

struct Job {
    Counter c;          /* (1) 값으로 품을 수 없다 */
    int id;
};

int main(void) {
    Counter local;              /* (2) 스택에 못 놓는다 */
    Counter *p = ctr_new(1);
    printf("%ld\n", p->n);      /* (3) 멤버를 못 읽는다 */
    printf("%zu\n", sizeof *p); /* (4) 크기를 못 묻는다 */
    (void)local;
    return 0;
}
```

- 네 줄은 각각 통과하는가, 무엇이라고 하는가?
- ★ 진단이 그 타입을 무엇이라고 부르는가 — **`struct` 라고 하는가 별칭으로 부르는가**?
- ★★ 네 에러의 **원인이 하나**다. 그것은 무엇인가?
- ★★ 이 대가 때문에 opaque 객체는 **거의 언제나 어느 저장 기간**에 놓이게 되는가?
- ★ 이 대가가 **컴파일 시간에 다 드러나는가**, 아니면 실행 시간에 남는 것이 있는가?

### 5. `sizeof(void)` 를 묻고 `void *` 에 1 을 더하면 (예측) ★★★

```c
/* s25d.c */
#include <stdio.h>

int main(void) {
    /* void 는 ★ 영원히 완성되지 않는 불완전 타입이다 */
    printf("sizeof(void)  = %zu\n", sizeof(void));

    int a[4] = {10, 20, 30, 40};
    void *vp = a;
    printf("vp        = %p\n", (void *)vp);
    printf("vp + 1    = %p   <- 몇 바이트 갔나?\n", (void *)(vp + 1));
    printf("차이      = %td 바이트\n", (char *)(vp + 1) - (char *)vp);
    return 0;
}
```

- 이 프로그램은 컴파일되는가? ★ `cc exit` 는 얼마인가?
- 실행되면 `sizeof(void)` 는 얼마를 찍는가?
- `vp + 1` 은 **몇 바이트** 간 것인가?
- ★★ `-pedantic` 을 `-pedantic-errors` 로 바꾸면 **무엇이 바뀌고 무엇이 그대로인가**?
- ★★★ 「`-pedantic` 을 붙였으니 표준으로 검증했다」가 여기서 **왜 깨지는가**?
- ★ 이 출력 중 **실행마다 바뀌는 칸**은 어느 것이고, **안 바뀌는 칸**은 어느 것인가?

### 6. 두 `.c` 가 같은 태그를 다르게 정의하면 (예측) ★★★ 본체

```c
/* s25e.c */
#include <stdlib.h>

struct Counter { long n; long step; };      /* ★ 이쪽의 정의 */

struct Counter *cnew(long step) { struct Counter *c = malloc(sizeof *c); c->n = 0; c->step = step; return c; }
void ctick(struct Counter *c)   { c->n += c->step; }
long cget(const struct Counter *c) { return c->n; }
void cfree(struct Counter *c)   { free(c); }
```

```c
/* s25e_main.c */
#include <stdio.h>

struct Counter { char tag; long n; };       /* ★ 저쪽과 다른 정의 — 헤더를 안 쓰고 손으로 적었다 */

struct Counter *cnew(long step);
void ctick(struct Counter *c);
long cget(const struct Counter *c);
void cfree(struct Counter *c);

int main(void) {
    struct Counter *c = cnew(3);
    ctick(c); ctick(c);
    printf("저쪽 함수로 읽으면 cget = %ld\n", cget(c));
    printf("이쪽 정의로 읽으면 tag = %d · n = %ld\n", c->tag, c->n);
    cfree(c);
    return 0;
}
```

- 이것은 컴파일되는가? 링크되는가? 실행되는가?
- ★★★ **네 벌**(gcc · clang · `-flto` · `-fsanitize=address,undefined`)에서 **경고가 몇 건**씩 나오는가?
- 실행하면 `cget` 과 `tag`·`n` 은 각각 얼마를 찍는가?
- ★★ 그 숫자들이 **어디서 온 값**인가? 바이트 그림으로 설명하면?
- ★★★ 아무도 안 잡는 **원리상의 이유**는 무엇인가?
- ★ 이 사고를 **막는 방법**은 무엇인가 — 도구인가 규율인가?

### 7. `-flto` 는 무엇을 보고 무엇을 못 보나 (경계) ★★★

```c
/* s25f_main.c */
#include <stdio.h>

void ctick(int x);          /* ★ 이번에는 ★ 시그니처 ★ 가 어긋난다 */

int main(void) { ctick(1); printf("done\n"); return 0; }
```

- 이번에는 **시그니처**가 어긋난다. `-flto` 없이 컴파일하면 무슨 일이 나는가?
- `-flto` 를 켜면 무엇이 나오는가? **플래그 이름**은?
- ★★ 그때 `cc exit` 는 얼마인가? 그 진단이 **무엇이라고까지 적는가**?
- ★★★ 6번(구조체 정의 불일치)은 왜 `-flto` 로도 안 잡히는가?
- ★ 그래서 이 주제의 「**네 번째 창**」은 무엇인가?

### 8. 함수 선언의 괄호 안에서 `struct` 가 처음 나오면 (예측) ★★

```c
/* s25g.c */
#include <stdio.h>

void show(struct Point *p);         /* ★ struct Point 가 여기서 처음 나온다 */

struct Point { int x, y; };         /* 그 뒤에 정의한다 */

void show(struct Point *p) { printf("(%d,%d)\n", p->x, p->y); }

int main(void) { struct Point q = {1, 2}; show(&q); return 0; }
```

- 컴파일되는가? 무슨 진단이 몇 줄 나오는가?
- ★★★ 에러의 두 줄이 **글자까지 같은데** 왜 충돌이라고 하는가?
- ★ 그 이유를 알려 주는 줄은 **에러인가 경고인가**? 어디에 있는가?
- ★ 고치는 법을 **한 줄**로 대면?
- ★ 이 함정은 조용히 지나갈 수 있는가?

### 9. 크기를 안 적은 `extern` 배열 (경계) ★★

```c
/* s25h.c */
char msg[6] = "hello";              /* ★ 여기서 완성된다 — 크기 6 */
```

```c
/* s25h_main.c */
#include <stdio.h>

extern char msg[];                  /* ★ 크기를 모르는 배열 = 불완전 타입 */

int main(void) {
    printf("msg   = %s\n", msg);    /* 읽기는 된다 (포인터로 감쇠) */
    printf("msg[1]= %c\n", msg[1]); /* 인덱싱도 된다 */
    printf("sizeof= %zu\n", sizeof msg);   /* ★ 크기는 못 묻는다 */
    return 0;
}
```

- 이 두 파일을 같이 컴파일하면 무슨 일이 나는가?
- ★ `msg` 를 **읽는 것**과 `msg[1]` 로 **인덱싱하는 것**은 되는가? 왜인가?
- ★★ 같은 객체인데 **`sizeof` 가 되는 번역 단위와 안 되는 번역 단위**가 갈린다 — 무엇이 그것을 가르는가?
- ★ 진단이 그 타입을 무엇이라고 적는가?
- ★★ 헤더에 `extern char msg[6];` 라고 **크기를 적으면** 무엇을 얻고 무엇을 잃는가?

### 10. 서로를 가리키는 두 구조체 (왜) ★★

```c
/* s25i.c */
#include <stdio.h>

typedef struct Node Node;           /* ① 불완전한 채로 별칭을 만든다 */
typedef struct Node Node;           /* ② 같은 typedef 를 또 쓴다 — C11 부터 허용 */

struct Edge;                        /* ③ 상호 참조를 위한 선언 */
struct Node { int v; struct Edge *out; };
struct Edge { Node *to; int w; };   /* ④ 여기서 Edge 가 완성된다 */

int main(void) {
    Node b = {2, 0};
    struct Edge e = {&b, 7};
    Node a = {1, &e};
    printf("a.v=%d -> w=%d -> v=%d\n", a.v, a.out->w, a.out->to->v);
    printf("sizeof(Node)=%zu sizeof(struct Edge)=%zu\n", sizeof(Node), sizeof(struct Edge));
    return 0;
}
```

- ★★ `struct Node` 안에 `struct Edge *out` 을 쓸 수 있는 이유는?
- ★★ 두 구조체가 서로를 **값으로 품으면** 왜 안 되는가?
- ★ 같은 `typedef` 를 두 번 쓴 것은 **어느 버전부터** 허용되는가?
- ★ `-std=c99 -pedantic` 으로 돌리면 무엇이 나오고 **`cc exit` 는 얼마**인가?
- ★ `sizeof(Node)` 가 그 값이 된 이유는? (어느 형제가 정본인가?)

### 11. 다섯 층과 무게중심 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / 구현 정의 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- **비어 있는 칸**은 무엇인가?
- ★★ **가장 두꺼운 칸**은 무엇이고, [24번 형제](../24-bit-fields/)와 **무엇이 정반대**인가?
- ★★ **도구가 침묵하는 자리**를 층마다 하나씩 대면?
- ★★★ 「**종료 코드가 0인데 ill-formed**」인 자리가 이 주제에 **몇 군데**인가? 각각 무엇인가?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

- **`void *` 라는 포인터를 어떻게 쓰나**는 어느 주제가 정본인가?
- **`sizeof`·`offsetof` 라는 도구**와 **구조체 선언·초기화**는 각각 어느 주제가 정본인가?
- **무엇을 헤더에 두나**와 **`undefined reference` 읽기**는 각각 어느 주제인가?
- ★ **`_new`/`_free` 짝을 시그니처로 표현하는 법**은 어느 주제인가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?
- ★★ **C++ 에서 이 관용구가 한 칸 좁아지는 자리**는 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
