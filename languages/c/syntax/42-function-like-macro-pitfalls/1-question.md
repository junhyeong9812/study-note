# c/syntax/42 — 함수형 매크로의 함정: 「**매크로는 인자를 값이 아니라 글자로 받는다 — 괄호도 평가 횟수도 문장 경계도 대신 지켜 주지 않는다**」 — 질문

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **1번은 칸마다 치환된 글자를 먼저 적고**(`1+2 * 1+2` 처럼) 그다음 우선순위로 계산하라.
- ★★ **미정의 동작의 칸은 값을 적지 마라** — 「무엇이 그것을 알려 주나」를 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**인자가 몇 번 실행되나**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 함정 격자 — 매크로 셋 × 인자 셋 × 쓰는 자리 넷 (예측) ★★★ 이 주제의 축

```c
/* s42a.c */
#include <stdio.h>

#define SQ1(x) x * x
#define SQ2(x) (x) * (x)
#define SQ3(x) ((x) * (x))

static int sq(int x) { return x * x; }

#define ROW "%-12s\t%d\t%d\t%d\t%d\n"

int main(void) {
    printf("%-12s\t%s\t%s\t%s\t%s\n", "expr", "SQ1", "SQ2", "SQ3", "sq()");
    printf(ROW, "SQ(3)",       SQ1(3),        SQ2(3),        SQ3(3),        sq(3));
    printf(ROW, "SQ(1+2)",     SQ1(1+2),      SQ2(1+2),      SQ3(1+2),      sq(1+2));
    printf(ROW, "SQ(-3)",      SQ1(-3),       SQ2(-3),       SQ3(-3),       sq(-3));
    printf(ROW, "100/SQ(3)",   100/SQ1(3),    100/SQ2(3),    100/SQ3(3),    100/sq(3));
    printf(ROW, "100/SQ(1+2)", 100/SQ1(1+2),  100/SQ2(1+2),  100/SQ3(1+2),  100/sq(1+2));
    printf(ROW, "100/SQ(-3)",  100/SQ1(-3),   100/SQ2(-3),   100/SQ3(-3),   100/sq(-3));
    printf(ROW, "~SQ(3)",      ~SQ1(3),       ~SQ2(3),       ~SQ3(3),       ~sq(3));
    printf(ROW, "~SQ(1+2)",    ~SQ1(1+2),     ~SQ2(1+2),     ~SQ3(1+2),     ~sq(1+2));
    printf(ROW, "~SQ(-3)",     ~SQ1(-3),      ~SQ2(-3),      ~SQ3(-3),      ~sq(-3));
    printf(ROW, "!SQ(3)",      !SQ1(3),       !SQ2(3),       !SQ3(3),       !sq(3));
    printf(ROW, "!SQ(1+2)",    !SQ1(1+2),     !SQ2(1+2),     !SQ3(1+2),     !sq(1+2));
    printf(ROW, "!SQ(-3)",     !SQ1(-3),      !SQ2(-3),      !SQ3(-3),      !sq(-3));
    return 0;
}
```

- ★★★ `SQ1` · `SQ2` · `SQ3` 열의 12행 값은 각각 무엇인가? `sq()` 열과 **다른 칸**은 몇 개인가(매크로마다)?
- ★★ `SQ(-3)` 행과 `!SQ(3)` 행은 **틀린 매크로로도 맞는가**?
- ★★ gcc 와 clang 의 출력은 같은가? 경고는 몇 줄인가?

### 2. 부작용이 있는 인자 (예측) ★★★

```c
/* s42b.c */
#include <stdio.h>

#define SQ3(x) ((x) * (x))

static int sq(int x) { return x * x; }

int main(void) {
    int i = 2;
    int r = SQ3(i++);
    (void)r;

    int j = 2;
    int s = sq(j++);
    printf("sq(j++) = %d · j = %d\n", s, j);
    return 0;
}
```

- ★★★ `SQ3(i++)` 에 대해 gcc 와 clang 은 `-Wall -Wextra -pedantic` 으로 무엇을 말하는가? (`r` 의 값을 적지 말고 **진단**을 적어라.)
- ★★★ `-fsanitize=undefined` 로 빌드해 돌리면 두 컴파일러의 UBSan 은 무엇을 찍는가?
- ★★ 프로그램의 표준 출력은?

### 3. 함수 호출을 인자로 (예측) ★★★

```c
/* s42c.c */
#include <stdio.h>

#define SQ3(x) ((x) * (x))
#define SQ4(x) ({ __typeof__(x) v_ = (x); v_ * v_; })

static int calls;
static int next(void) { calls++; return 3; }
static int sq(int x) { return x * x; }

int main(void) {
    int r3 = SQ3(next());
    printf("SQ3(next()) = %d · calls = %d\n", r3, calls);
    calls = 0;
    int r4 = SQ4(next());
    printf("SQ4(next()) = %d · calls = %d\n", r4, calls);
    calls = 0;
    int rf = sq(next());
    printf("sq(next())  = %d · calls = %d\n", rf, calls);
    return 0;
}
```

- ★★★ 세 줄에 찍히는 값과 `calls` 는?
- ★★ `-std=c17 -pedantic` 에서 두 컴파일러는 어느 줄에 무엇을 경고하는가? `-std=gnu17` 이면?

### 4. 두 문장 매크로를 `if` 에 (예측) ★★★

```c
/* s42d.c */
#include <stdio.h>

#define TWO1(m) puts("[1] " m); puts("[2] " m)

int main(int argc, char **argv) {
    (void)argv;
    if (argc > 5) TWO1("a");
    puts("end");
    return 0;
}
```

- ★★★ 인자 없이 돌리면(`argc` 는 1) 무엇이 찍히는가?
- ★★ gcc 와 clang 은 각각 경고하는가?

### 5. 중괄호 매크로와 `else` (예측) ★★★

```c
/* s42e.c */
#include <stdio.h>

#define TWO2(m) { puts("[1] " m); puts("[2] " m); }

int main(int argc, char **argv) {
    (void)argv;
    if (argc > 5) TWO2("b"); else puts("[else] b");
    return 0;
}
```

- ★★★ 컴파일되는가? 안 된다면 gcc 와 clang 은 각각 어느 열에서 무엇이라 하는가?
- ★★ `-E -P` 로 보면 **어느 글자**가 문제인가?

### 6. 매크로와 같은 이름의 함수 (예측) ★★

```c
/* s42i.c */
#include <stdio.h>

int max(int a, int b) { return a > b ? a : b; }

#define max(a, b) ((a) > (b) ? (a) : (b))

int main(void) {
    int (*fp)(int, int) = max;
    printf("%d %d %d\n", max(1, 2), (max)(3, 4), fp(5, 6));
    return 0;
}
```

- ★★ 무엇이 찍히는가? `max(1, 2)` · `(max)(3, 4)` · `fp(5, 6)` 중 **매크로로 펼쳐지는 것**은?

### 7. 여러 문장 매크로의 세 모양 (왜) ★★★

- 세 모양(괄호 없음 · `{ … }` · `do { … } while (0)`) 중 **`if` 뒤 · `if`/`else` 사이 어디에 넣어도 문장 하나로 붙는 것**은 무엇이고, 왜 그런가? 「쓰는 쪽이 붙이는 `;`」로 설명하라.
- ★ 그 모양의 치환 목록 끝에 `;` 를 넣으면(`… while (0);`) `if (c) M("e"); else …` 는 어떻게 되는가?

### 8. 문장 식은 ISO 가 아니다 (경계) ★★

- `({ __typeof__(x) v_ = (x); v_ * v_; })` 는 **어느 층**인가? `-pedantic` 과 gnu 모드에서 각각 무엇이 나오나?
- ★ 이 매크로에 `v_` 라는 이름의 변수를 넘기면 왜 위험한가?

### 9. `static inline` 으로 바꾸면 얻는 것과 잃는 것 (왜) ★★

```c
/* s42g.c */
#include <stdio.h>

#define SQ3(x) ((x) * (x))

static inline int sq(int x) { return x * x; }

int main(void) {
    double d = 2.5;
    printf("SQ3(d) = %g\n", SQ3(d));
    printf("sq(d)  = %d\n", sq(d));
    return 0;
}
```

- ★★ 이 프로그램은 무엇을 찍는가? `-Wall -Wextra -pedantic` 은 경고하는가? 무엇을 더 켜야 하는가?
- ★★ 포인터(`int *p`)를 `sq(p)` 와 `SQ3(p)` 에 넘기면 각각 에러인가 경고인가(gcc · clang)?
- ★ 「매크로가 함수보다 빠르다」를 이 편은 쟀는가?

### 10. C++ `constexpr` · Rust `macro_rules!` (연결) ★★

- ★★ C++ 의 `constexpr int sq(int)` 는 `sq(i++)` 에서 무엇을 내는가? `static_assert(sq(1 + 2) == 9)` 는 통과하는가?
- ★★★ Rust `macro_rules! sq { ($x:expr) => { $x * $x }; }` 는 `sq!(1 + 2)` · `100 / sq!(1 + 2)` · `sq!(next())` 의 호출 수에서 **C 의 어느 함정을 풀고 어느 것을 못 푸나**?

### 11. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- 이 주제에서 **표준 / UB / 미명시 / 컴파일러 구현** 칸에 각각 무엇이 들어가는가?
- ★★★ 함정 격자의 틀린 칸을 **어떤 도구가** 말해 주는가?
- ★★ clang 으로만 빌드하면 **안 보이는 것**은?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

- **시퀀스 포인트 자체** · **`static inline` 의 링크 규칙** · **`#`/`##`** 는 각각 몇 번 형제가 정본인가?
- ★ 매크로가 **꼭 필요한** 자리 셋은?

## 실행 환경

**환경** — gcc 13.3.0 · clang 18.1.3 · g++ 13.3.0 · rustc 1.92.0 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.

★★★ **본체 창은 함정 격자** — 1번은 **칸마다 값**과 **함수와 다른 칸의 수**를 적어야 답이다.
선행 — [41번 형제](../41-preprocessor-directives-and-conditional-compilation/).

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
