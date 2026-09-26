# c/syntax/30 — 초기화 규칙과 불확정 값: 「**0 은 누가 보장하고, 안 보장된 자리에서는 무엇이 읽히나**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **무엇이 0 이고 무엇이 불확정인가**(저장 기간 · 초기자 유무) ② **도구 여섯이 어디서 침묵하나**(판 격자)
> ③ **불확정 값을 읽는 것이 언제 UB 인가**(주소 · 비값 표현 · 미명시 값).
> ★★★ **본체 창은 둘** — **`readelf -S`·`size`**(1번)와 **`-O0` 대 `-O2`**(4번).
> ★★★ **4번은 48칸 격자**다 — 「경고가 난다」로 답하지 마라. **칸마다** 적어라.
> ★ **불확정 값을 숫자로 예측하지 마라** — 이 편의 어느 문항도 쓰레기 숫자를 답으로 요구하지 않는다.
> 선행 — [28번 형제](../28-choosing-among-four-storage-durations/).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **4번은 「답한 칸 N / 48」까지** 적어야 답이다. ★ 그리고 **Valgrind 칸은 왜 없나**도.
- ★★ **5·6번은 판 격자**다 — gcc·clang × `-O0`/`-O2` 네 벌을 다 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 0 은 보장인가 관찰인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 400000 바이트짜리 정적 배열 두 개 — 섹션과 파일 크기 (예측) ★★★ 이 주제의 축

```c
/* s30a.c */
static int zero_implicit;             /* 초기자 없음 */
static int zero_explicit = 0;         /* 0 을 직접 적음 */
static int nonzero = 5;               /* 0 이 아닌 값 */
static int big_zero[100000];          /* 400000 바이트 — 전부 0 */
static const int ro = 7;              /* const — 값 있음 */

int use(int k) {
    return zero_implicit + zero_explicit + nonzero + big_zero[k] + ro;
}
```

```c
/* s30b.c */
static int zero_implicit;
static int zero_explicit = 0;
static int nonzero = 5;
static int big_one[100000] = {1};     /* ★ 첫 원소만 1 — 나머지 99999 개는 0 */
static const int ro = 7;

int use(int k) {
    return zero_implicit + zero_explicit + nonzero + big_one[k] + ro;
}
```

- ★★★ `readelf -S` 에서 `s30a.o` 의 `.bss` 와 `.data` 는 **각각 몇 바이트**이고, `s30b.o` 는?
- ★★★ `.bss` 의 섹션 타입은 무엇이고 **그 낱말이 무엇을 뜻하는가**?
- ★★ 두 오브젝트 파일의 **바이트 수**는 대략 얼마씩인가? 왜 그렇게 차이 나는가?
- ★★ `zero_explicit = 0` 은 `.bss` 인가 `.data` 인가?
- ★ `static const int ro = 7` 은 `nm -S` 에서 **gcc 와 clang 이 같게** 나오는가?
- ★ `.bss` 는 **표준의 말**인가?

### 2. 자동 저장 기간의 부분 초기화 (예측) ★★★

```c
/* s30c.c */
#include <stdio.h>

struct Cfg { int port; int retries; const char *name; double ratio; };

static void dirty(void) {                /* 스택을 먼저 더럽혀 둔다 — 「원래 0 이었다」를 막으려고 */
    volatile int junk[64];
    for (int k = 0; k < 64; k++) junk[k] = -1;
}

static void show(void) {
    int a[8] = {1};                      /* 첫 칸만 적었다 */
    int b[8] = {[5] = 9};                /* 지정 초기자 — 여섯째 칸만 적었다 */
    struct Cfg c = {.retries = 3};       /* 멤버 하나만 적었다 */

    printf("a =");
    for (int k = 0; k < 8; k++) printf(" %d", a[k]);
    printf("\nb =");
    for (int k = 0; k < 8; k++) printf(" %d", b[k]);
    printf("\nc = { port=%d  retries=%d  name=%s  ratio=%.1f }\n",
           c.port, c.retries, c.name == NULL ? "NULL" : "(NULL 아님)", c.ratio);
}

int main(void) {
    dirty();
    show();                              /* ★ 전부 자동 저장 기간이다 */
    return 0;
}
```

- `a`·`b`·`c` 세 줄은 무엇을 찍는가?
- ★★★ **스택을 먼저 `-1` 로 더럽혔는데도** 나머지 칸이 0 인가? 그것은 **보장인가 관찰인가**?
- ★★ gcc·clang × `-O0`/`-O2` **네 벌의 출력**은 같은가?
- ★ `c.name` 과 `c.ratio` 는 무엇이 되는가 — 「0 비트」인가 「그 타입의 0」인가?

### 3. `= {}` 를 판 넷으로 (예측) ★★

```c
/* s30d.c */
#include <stdio.h>

int main(void) {
    int a[4] = {};                       /* ★ 빈 중괄호 — C23 에서 들어온 문법 */
    struct { int x; double y; } s = {};
    printf("a = %d %d %d %d · s = { %d, %.1f }\n", a[0], a[1], a[2], a[3], s.x, s.y);
    return 0;
}
```

- ★★★ gcc·clang × `-std=c17` · `-std=c17 -pedantic` · `-std=c17 -pedantic-errors` · `-std=c2x -pedantic-errors` **여덟 칸의 `cc exit` 와 경고 수**는?
- ★★ 두 컴파일러의 **경고 문구와 플래그 이름**은 같은가?
- ★★★ 이 격자에서 「**종료 코드 0인데 ill-formed**」 칸은 어느 것인가?
- ★ `-std=c2x` 에서의 출력은?

### 4. 불확정 값 탐침 8 × 도구 6 (예측) ★★★ 본체

탐침 여덟 개(`s30p1.c`\~`s30p8.c`)는 **같은 `main`** 을 쓴다. `probe` 만 보인다.

```c
/* s30p1.c */
#include <stdio.h>
#include <stdlib.h>

static int probe(int c) {
    (void)c;
    int a;                               /* P1 — 한 번도 안 쓰고 읽는다 */
    return a;
}

int main(int argc, char **argv) {
    (void)argv;
    int v = probe(argc);                 /* argc = 1 로 돌린다 */
    if (v == 12345) puts("12345");       /* ★ 그 값으로 분기한다 — MSan 은 여기서 본다 */
    else puts("12345 가 아니다");
    return 0;
}
```

```text
P2  int a;  if (c > 5) a = 1;  return a;                 한쪽 가지에서만 쓴다
P3  int sum;  for (i = 0; i < c; i++) sum += i;           누산기를 0 으로 안 둔다
P4  int a;  fill(&a, c);  return a;                      fill 은 c > 5 일 때만 쓴다
P5  int arr[4];  arr[0] = c;  return arr[2];              한 칸만 쓴다
P6  struct Pair s;  s.x = c;  return s.y;                 멤버 하나만 쓴다
P7  int *p = malloc(sizeof *p);  int v = *p;              쓰기 전에 읽는다
P8  int a;  switch (c) { case 2: … case 3: … }  return a;  default 가 없다
```

- ★★★ **gcc `-O0` · gcc `-O2` · clang `-O0` · clang `-O2` · gcc `-fanalyzer` · clang MSan** 여섯 열에서 **각 탐침은 답하나 침묵하나**?
- ★★★ **48칸 중 답한 칸**은 몇인가?
- ★★★ **`-O0` 에서 침묵하고 `-O2` 에서 경고하는 칸**은 어느 것인가? ★ **반대로 `-O2` 에서도 침묵하는 gcc 칸** 중 **이유가 특별한 것**은?
- ★★ **clang 의 `-O0` 열과 `-O2` 열**은 같은가? 왜?
- ★★ **정적 도구 다섯이 전부 침묵하는 탐침**은?
- ★ **Valgrind 열이 없는 이유**는? 그것은 「안 쟀다」인가 「못 쟀다」인가?

### 5. 패딩 바이트 — 초기화 형태 다섯 × 네 벌 (예측) ★★

```c
/* s30e.c */
#include <stdio.h>
#include <string.h>

struct S { char c; int i; };             /* 바이트 1~3 이 패딩이다 */

static struct S st;                      /* ★ 정적 — 초기자 없음 */

static void dirty(void) {                /* 같은 깊이의 스택을 0xAA 로 더럽힌다 */
    volatile unsigned char buf[64];
    for (int k = 0; k < 64; k++) buf[k] = 0xAA;
}

static void dump(const char *tag, const struct S *p) {
    const unsigned char *b = (const unsigned char *)p;
    printf("%-20s", tag);
    for (size_t k = 0; k < sizeof *p; k++)
        printf(k >= 1 && k <= 3 ? " [%02x]" : "  %02x ", b[k]);
    printf("\n");
}

static void auto_zero(void)   { struct S v = {0};         dump("auto = {0}", &v); }
static void auto_desig(void)  { struct S v = {.i = 2};    dump("auto = {.i = 2}", &v); }
static void auto_full(void)   { struct S v = {1, 2};      dump("auto = {1, 2}", &v); }
static void auto_assign(void) { struct S v; v.c = 1; v.i = 2; dump("auto member-assign", &v); }

int main(void) {
    printf("[ ] 안이 패딩 바이트다\n");
    dump("static (no init)", &st);
    dirty(); auto_zero();
    dirty(); auto_desig();
    dirty(); auto_full();
    dirty(); auto_assign();
    return 0;
}
```

- ★★★ 다섯 줄의 **패딩 세 바이트**(`[ ]` 안)는 네 벌에서 각각 무엇인가?
- ★★★ 그중 **표준이 0 을 보장하는 줄**은 어느 것인가?
- ★★ `auto = {0}` 의 `00` 은 **보장인가**?
- ★★ **`aa` 가 보이는 칸**은 어디이고, 그것이 무엇을 뜻하는가?
- ★ [22번 형제](../22-struct-padding-and-alignment/)의 관찰과 **같은가**? 다르면 그것이 무엇을 말하는가?

### 6. `bool` 에 바이트 `2` 를 넣으면 (예측) ★★★

```c
/* s30g.c */
#include <stdio.h>
#include <string.h>
#include <stdbool.h>

int main(void) {
    bool b;
    unsigned char two = 2;
    memcpy(&b, &two, 1);                 /* ★ 0 도 1 도 아닌 바이트를 bool 에 넣는다 */
    printf("b 의 바이트    = %d\n", *(unsigned char *)&b);
    printf("b  ? 참 : 거짓 = %s\n", b ? "참" : "거짓");
    printf("!b ? 참 : 거짓 = %s\n", !b ? "참" : "거짓");
    printf("b == true      = %d\n", b == true);
    printf("(int)b         = %d\n", (int)b);
    return 0;
}
```

- ★★★ gcc·clang × `-O0`/`-O2` **네 벌에서 둘째\~다섯째 줄**(`b ?`·`!b ?`·`b == true`·`(int)b`)은 각각?
- ★★★ 「**참이면서 참**」이 나오는 칸이 있는가?
- ★★ UBSan(`-fsanitize=undefined`)은 **무엇이라고** 몇 번 말하는가? `run exit` 는?
- ★★ **`memcpy` 로 넣는 것**과 **`bool` 로 읽는 것** 중 어디가 UB 인가?
- ★ 어느 바이트 패턴이 비값 표현인지는 **누가 정하는가**?

### 7. 「초기화 안 한 변수를 읽으면 UB」는 어디까지 맞나 (경계) ★★★

- ★★★ 표준이 **무조건 UB** 라고 하는 자리는 **어떤 조건**을 가진 객체인가? 탐침 중 어느 것이 여기 드는가?
- ★★★ 그 밖에서 불확정 표현을 읽으면 **무엇이 층을 정하는가**?
- ★★ **미명시 값**과 **비값 표현**은 각각 무엇인가? C17 까지 비값 표현을 **무엇이라 불렀나**?
- ★★ `unsigned char` 로 불확정 바이트를 읽는 것은 **UB 인가**?
- ★ 「UB 가 아니면 읽어도 된다」가 **왜 틀린가**?

### 8. P2 는 왜 gcc `-O2` 에서도 침묵하나 (왜) ★★★

- ★★★ gcc `-O2` 의 **`main` 어셈블리**에 무엇이 남아 있고 무엇이 없는가?
- ★★★ gcc 는 불확정인 `a` 를 **무엇으로 접었나**? 그러면 `v == 12345` 는 어떻게 되는가?
- ★★ 그것이 **경고가 사라진 이유**를 어떻게 설명하는가?
- ★★ clang 은 같은 탐침을 **어느 단계에서** 잡고, 그래서 무엇이 다른가?
- ★ 「gcc 는 `a` 를 1 로 만든다」라고 적으면 무엇이 틀리는가?

### 9. `malloc` 대 `calloc` — 그리고 `-O2` 가 지운 것 (왜) ★★

```c
/* s30f.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

static int count_eq(const unsigned char *p, size_t from, size_t to, unsigned char v) {
    int n = 0;
    for (size_t k = from; k < to; k++) n += (p[k] == v);
    return n;
}

int main(void) {
    unsigned char *p = malloc(64);
    if (!p) return 1;
    memset(p, 0xAB, 64);                 /* 0xAB 로 채운 뒤 */
    uintptr_t old = (uintptr_t)p;
    free(p);                             /* 돌려준다 */

    unsigned char *q = malloc(64);       /* ★ 같은 크기를 다시 빌린다 — 새로 쓰기 전에 읽는다 */
    if (!q) return 1;
    printf("malloc : 방금 돌려준 조각이 다시 왔나 = %s\n", (uintptr_t)q == old ? "예" : "아니오");
    printf("malloc : 바이트 16~63 중 0xAB 그대로 = %d / 48\n", count_eq(q, 16, 64, 0xAB));
    free(q);

    unsigned char *r = calloc(64, 1);    /* ★ calloc */
    if (!r) return 1;
    printf("calloc : 바이트  0~63 중 0x00       = %d / 64\n", count_eq(r, 0, 64, 0x00));
    free(r);
    return 0;
}
```

- ★★ `-O0` 의 두 컴파일러에서 **다시 받은 조각의 바이트 16\~63** 은 어떤가?
- ★★★ **`-O2` 에서 `0 / 48`** 이 나오는 이유를 **`call` 목록**으로 설명하면?
- ★★ clang `-O2` 의 「다시 왔나 = 아니오」는 왜인가?
- ★ **바이트 0\~15 를 세지 않은 이유**는? · ★ 해제된 포인터를 **어떻게 안 읽었나**?

### 10. 다른 언어는 어떻게 막나 (연결) ★★

- ★★ Rust 는 초기화 안 된 읽기를 **어느 단계에서** 막는가? **에러 코드**는?
- ★★ Go 는 무엇으로 이 문제를 **없애는가**? C 의 어느 규칙을 **모든 변수에** 적용한 것과 같은가?
- ★ C 가 둘 다 하지 않는 **대가**는 이 편의 어느 격자에 드러나는가?

### 11. 다섯 층과 무게중심 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / 구현 정의 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- ★★★ **가장 정밀하게 갈라야 하는 칸**은 무엇이고 왜인가?
- ★★ **비어 있는 칸**이 있는가? 있다면 **정말 비었나, 안 던졌나**?
- ★★ **도구가 침묵하는 자리**를 층마다 하나씩 대면?
- ★★★ 이 편의 「**종료 코드 0인데 ill-formed**」 항목은?
- ★ 이 편의 **제5의 상태**(같은 질문을 다른 창으로)는 무엇이고, **바꾼 창이 못 보는 것**은?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

- **저장 기간 자체**는 어느 형제가 정본인가?
- **지정 초기자 문법**과 **패딩이 어디 생기나**는 각각 어느 형제인가?
- **`malloc`/`calloc` 의 API 계약**과 **sanitizer 사용법**은 각각 목록의 몇 번 주제인가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
