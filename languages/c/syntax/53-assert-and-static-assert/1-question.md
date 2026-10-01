# c/syntax/53 — `assert` 와 `static_assert`: 「**`assert` 는 `NDEBUG` 하나에 식째 사라지는 매크로이고, `static_assert` 는 컴파일러가 대신 멈춰 주는 선언이다**」 — 질문

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「단언이 참이었나」와 「식이 평가됐나」를 따로** 적어라 — 둘은 다른 질문이다.
- ★★ **「표준이 정한 것」과 「glibc·컴파일러가 정한 것」을 갈라** 적어라 — 메시지 형식이 특히 그렇다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 줄은 컴파일러에게 도착하기나 하나**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 부작용이 있는 단언 × `NDEBUG` (예측) ★★★ 이 주제의 축

```c
/* s53a.c */
#include <assert.h>
#include <stdio.h>

int main(int argc, char **argv) {
    (void)argv;
    int x = argc;                          /* 인자 없이 돌리면 1 */
    assert(x++ > 0);
    printf("x = %d\n", x);
    return 0;
}
```

격자는 gcc/clang × `-O0`/`-O2` × (`-DNDEBUG` 없음 · 있음) 여덟 빌드를 `./x` 로 돌린다.

- ★★★ 여덟 칸의 `x` 는 각각 얼마인가? **최적화 수준**이 답을 바꾸는가?
- ★★ 어느 칸에서든 단언이 **실패**하는가?

### 2. 실패하는 단언 (예측) ★★★

```c
/* s53b.c */
#include <assert.h>
#include <stdio.h>

int take(int count) {
    assert(count > 0);
    return 100 / count;
}

int main(int argc, char **argv) {
    (void)argv;
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("start\n");
    int r = take(argc - 1);                /* 인자 없이 돌리면 0 */
    printf("r = %d\n", r);
    return 0;
}
```

- ★★★ gcc `-O0` 빌드를 `./x` 로 돌리면 stdout 과 stderr 에 각각 무엇이 나오고 `run exit` 는?
- ★★ clang `-O2` 빌드의 stderr 한 줄은 gcc 의 것과 **어느 칸이** 다른가?
- ★★★ `-DNDEBUG` 빌드를 같은 방법으로 돌리면 `run exit` 는? stderr 는?
- ★★ 여덟 빌드의 오브젝트에서 `__assert_fail` 재배치는 각각 몇 개인가?

### 3. `static_assert` 여섯 꼴 × `-std` 셋 (예측) ★★★

```c
/* s53c1.c */
_Static_assert(sizeof(int) == 4, "m");
```

```c
/* s53c2.c */
#include <assert.h>
static_assert(sizeof(int) == 4, "m");
```

```c
/* s53c3.c */
static_assert(sizeof(int) == 4, "m");
```

```c
/* s53c4.c */
_Static_assert(sizeof(int) == 4);
```

```c
/* s53c5.c */
#include <assert.h>
static_assert(sizeof(int) == 4);
```

```c
/* s53c6.c */
static_assert(sizeof(int) == 4);
```

격자는 여섯 파일 × gcc/clang × `-std=c11`/`c17`/`c2x` 를 `-Wall -pedantic -c` 로 컴파일해 **`ok` · `warning` · `error`** 로 가른다.

- ★★★ 서른여섯 칸을 채우면? **`c11` 과 `c2x` 가 다른 줄**은 열두 줄 중 몇 줄인가?
- ★★ `s53c5.c` 에서 **두 컴파일러가 다른 답**을 내는가?
- ★ `s53c3.c` 를 `-std=c11` 로 컴파일한 gcc 의 첫 진단은?

### 4. 레이아웃 가정 검사 (예측) ★★

```c
/* s53d.c */
#include <stddef.h>
#include <stdint.h>

struct Header { uint8_t tag; uint32_t len; uint16_t kind; };

_Static_assert(sizeof(uint32_t) == 4, "wire format needs 4-byte len");
_Static_assert(offsetof(struct Header, len) == 4, "len must start at byte 4");
_Static_assert(sizeof(struct Header) == 7, "header must be 7 bytes");

int f(int n) {
    _Static_assert(n == 4, "n");
    return n;
}
```

- ★★ 네 단언 중 컴파일을 멈추는 것은? gcc 와 clang 은 **메시지에 무엇을** 더 적는가?
- ★ `f` 안의 단언에 두 컴파일러는 각각 무엇이라고 말하는가?

### 5. `assert` 를 함수처럼 (예측) ★★

```c
/* s53e.c */
#include <assert.h>

int main(void) {
    void (*check)(int) = assert;
    (void)check;
    return 0;
}
```

- ★★ gcc 와 clang 은 무엇이라고 말하는가? 두 진단의 **「고친 제안」** 은 맞는 제안인가?

### 6. 쉼표가 든 단언과 `-std=c2x` (예측) ★★

```c
/* s53f.c */
#include <assert.h>

struct P { int x, y; };

int main(void) {
    assert((struct P){ 1, 2 }.x == 1);
    return 0;
}
```

- ★★ `-std=c17` 과 `-std=c2x` 에서 각각 컴파일되는가? 두 컴파일러의 진단은?
- ★ 표준(C23)은 `assert` 를 어떤 모양의 매크로로 정의하라고 하는가? 이 판의 결과와 맞는가?

### 7. `#define NDEBUG` 를 `#include` 뒤에 (경계) ★★

- ★★ `#include <assert.h>` **다음 줄**에 `#define NDEBUG` 를 두면, 그 아래의 `assert(x == 1)`(`x` 는 0)은 사라지는가? 근거가 되는 표준 문장은?

### 8. 재배치 수를 함수 목록으로 읽기 (왜) ★★

- ★★ 2번의 재배치 수를 오브젝트에 들어 있는 **함수 목록**과 나란히 두면 무엇이 설명되는가?
- ★ gcc `-O2` 오브젝트에 **`take.part.0`** 이 생긴 것은 무엇을 뜻하는가?

### 9. 층 — 표준 · glibc · 컴파일러 (경계) ★★★

- ★★★ 실패 메시지의 **형식**은 누가 정하는가? 메시지에 **반드시 들어가야 하는 칸**은?
- ★★ C23 의 가변 인자 `assert` · `static_assert` 키워드는 **누가** 구현해야 하는가 — 컴파일러인가, C 라이브러리인가?

### 10. 41 · 42 · 43번 형제와 이어서 (연결) ★★

- ★★ `gcc -E -P` 로 `assert(x++ > 0)` 을 펼치면 `NDEBUG` 가 없을 때와 있을 때 각각 무엇이 남는가? ([41번 형제](../41-preprocessor-directives-and-conditional-compilation/))
- ★ 메시지의 `` `x++ > 0' `` 은 어떤 전처리 연산으로 만들어지는가? ([43번 형제](../43-stringizing-and-token-pasting/))

### 11. 다른 갈래의 단언과 (연결) ★★

- ★★ Rust 의 `assert!` 와 `debug_assert!` 는 `-O` 에서 각각 어떻게 되는가([Rust 갈래 23번](../../../rust/syntax/23-panic-vs-result/))? C 의 `assert` 는 어느 쪽에 가까운가?
- ★ Kotlin 의 `assert` 는 무엇이 켜야 울리는가([Kotlin 갈래 51번](../../../kotlin/syntax/51-preconditions-require-check-error-todo/))? C 의 `NDEBUG` 와 **무엇이 반대**인가?

### 12. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- 이 주제에서 **표준 / 구현 정의 / 컴파일러·glibc 구현 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- ★★★ 이 편의 **네 번째 창**은 무엇이고, 그 창이 **못 보는 것**은?

## 실행 환경

**환경** — gcc 13.3.0 · clang 18.1.3 · glibc 2.39 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic` · 캡처 셸 `LC_ALL=C`.

★★★ **본체 창은 `NDEBUG` 격자** — 1번은 **칸마다 `x` 의 값**을 적어야 답이다.
★★ **전처리기 자체는 묻지 않는다** — [41번 형제](../41-preprocessor-directives-and-conditional-compilation/)가 정본이다.
선행 — [41번 형제](../41-preprocessor-directives-and-conditional-compilation/).

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
