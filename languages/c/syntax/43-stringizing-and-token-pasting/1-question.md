# c/syntax/43 — 문자열화 `#` 와 토큰 붙이기 `##`: 「**`#`·`##` 에 붙은 인자는 먼저 펼쳐지지 않는다 — 그래서 펼친 결과가 필요하면 한 겹 더 감싼다**」 — 질문

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **1·2번은 칸마다 「이 매개변수는 `#`/`##` 에 붙어 있나」를 먼저 적고** 그다음 결과를 적어라.
- ★★ **「에러」와 「미정의」를 갈라** 적어라 — 누가 그것을 정했나.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 이름은 매크로인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 감싸기 격자 — 인자 아홉 × `STR`/`XSTR` (예측) ★★★ 이 주제의 축

```c
/* s43a.c */
#include <stdio.h>

#define STR(x) #x
#define XSTR(x) STR(x)
#define VERSION 3
#define ROW "%-14s\t%s\t%s\n"

int main(void) {
    printf(ROW, "arg", "STR", "XSTR");
    printf(ROW, "__LINE__",    STR(__LINE__),    XSTR(__LINE__));
    printf(ROW, "VERSION",     STR(VERSION),     XSTR(VERSION));
    printf(ROW, "VERSION + 1", STR(VERSION + 1), XSTR(VERSION + 1));
    printf(ROW, "a b",         STR(a b),         XSTR(a b));
    printf(ROW, "a    b",      STR(a    b),      XSTR(a    b));
    printf(ROW, "\"q\"",       STR("q"),         XSTR("q"));
    printf(ROW, "'\\n'",       STR('\n'),        XSTR('\n'));
    printf(ROW, "__FILE__",    STR(__FILE__),    XSTR(__FILE__));
    printf(ROW, "__func__",    STR(__func__),    XSTR(__func__));
    return 0;
}
```

- ★★★ 아홉 행의 `STR` 열과 `XSTR` 열은 각각 무엇을 찍는가?
- ★★ 두 열이 **갈리는 행**은 몇 개이고, 그 행들의 공통점은?
- ★ gcc 와 clang 의 출력은 같은가?

### 2. `##` 로 붙이기 (예측) ★★★

```c
/* s43b.c */
#define CAT(a, b) a ## b
#define XCAT(a, b) CAT(a, b)
#define N 7

CAT(x, y)
CAT(x, N)
XCAT(x, N)
CAT(tmp_, __LINE__)
XCAT(tmp_, __LINE__)
CAT(+, +)
CAT(-, >)
CAT(1, 2)
CAT(, z)
```

- ★★★ `gcc -std=c17 -pedantic -E -P s43b.c` 는 아홉 줄에 무엇을 찍는가?
- ★★ 파일 안에서 **줄마다 다른 이름**을 만들려면 `CAT` 과 `XCAT` 중 어느 쪽인가?

### 3. 잘못된 토큰 (예측) ★★

```c
/* s43c.c */
#define CAT(a, b) a ## b

CAT(., x)
CAT(+, -)
CAT(x, +)
```

- ★★ `gcc -std=c17 -E -P s43c.c -o /dev/null` 과 clang 은 무엇이라 하는가? 종료 코드는?
- ★ 에러를 버리고(`2>/dev/null`) 표준 출력만 보면 gcc 는 무엇을 남기는가?

### 4. 한 목록에서 두 선언 (예측) ★★

```c
/* s43d.c */
#include <stdio.h>

#define COLORS(X) X(RED) X(GREEN) X(BLUE)

#define AS_ENUM(n) COLOR_##n,
#define AS_NAME(n) #n,

enum color { COLORS(AS_ENUM) COLOR_COUNT };
static const char *const color_names[] = { COLORS(AS_NAME) };

int main(void) {
    for (int i = 0; i < COLOR_COUNT; i++)
        printf("%d %s\n", i, color_names[i]);
    return 0;
}
```

- ★★ 무엇이 찍히는가? `-E -P` 로 보면 `enum color` 와 `color_names` 줄은 어떻게 펼쳐지는가?

### 5. 가변 매크로의 빈 인자 (예측) ★★★

```c
/* s43e.c */
#include <stdio.h>

#if FORM == 1
#define LOG(fmt, ...) printf(fmt "\n", __VA_ARGS__)
#elif FORM == 2
#define LOG(fmt, ...) printf(fmt "\n", ##__VA_ARGS__)
#elif FORM == 3
#define LOG(fmt, ...) printf(fmt "\n" __VA_OPT__(,) __VA_ARGS__)
#endif

int main(void) {
    LOG("n=%d", 1);
    LOG("none");
    return 0;
}
```

칸 = `$CC -std=<판> -Wall -Wextra -pedantic -DFORM=<행> -c s43e.c` 의 `exit` 와 `warning:` 줄 수.

- ★★★ FORM 1 · 2 · 3 × (gcc · gcc-12 · clang) × (`c17` · `c2x`) 18칸은?
- ★★ FORM 1 의 `LOG("none");` 은 `-E -P` 로 어떻게 펼쳐지는가? FORM 2 와 3 은?
- ★★ `c17` 과 `c2x` 가 **갈리는 칸**은 어느 컴파일러에 있는가?

### 6. 호출 자리를 찍는 매크로 (예측) ★★

```c
/* s43f.c */
#include <stdio.h>

#define STR(x) #x
#define TRACE(fmt, ...) \
    printf("%s:%d %s: " fmt "\n", __FILE__, __LINE__, __func__, __VA_ARGS__)

static void load(int n) {
    TRACE("n=%d", n);
}

int main(void) {
    load(4);
    TRACE("%s", STR(__func__));
    return 0;
}
```

- ★★ 두 줄에 찍히는 것은? 둘째 줄의 마지막 조각은?
- ★★ `-E -P` 뒤에 `__FILE__`·`__LINE__`·`__func__` 는 각각 어떻게 남는가?

### 7. `STR` 과 `XSTR` 을 가르는 규칙 (왜) ★★★

- N3220 의 어느 규칙이 `STR(VERSION)` 과 `XSTR(VERSION)` 을 가르는가? 한 문장으로.
- ★★ 반대로 **펼치지 않는 것이 목적**인 자리(단언 메시지 등)에서는 어느 쪽을 쓰나?

### 8. 잘못된 토큰의 층 (경계) ★★★

- `CAT(., x)` 는 **표준으로는** 무엇인가? 두 컴파일러의 에러는 어느 층인가?
- ★ `CAT(+, +)` · `CAT(-, >)` 는 왜 되는가?

### 9. `__func__` 는 무엇인가 (경계) ★★

```c
/* s43g.c */
#include <stdio.h>

void where(void) {
    puts("in " __func__);
}
```

- ★★ 이 파일은 컴파일되는가? `__func__` 가 `__FILE__` 과 다른 점을 「전처리기가 아는가」로 설명하라.

### 10. 가변 인자 함수와 가변 매크로 (연결) ★★

- 36번 형제의 `va_arg` 와 이 편의 `__VA_ARGS__` 는 **언제 · 무엇을** 다루는가?
- ★ `, ##__VA_ARGS__` 와 `__VA_OPT__(,)` 는 각각 어느 층인가? gcc-12 의 경고 문구에서 **이상한 점**은?

### 11. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / UB / 컴파일러 구현** 칸에 각각 무엇이 들어가는가?
- ★★★ `STR(VERSION)` 이 `"VERSION"` 을 만든 사고를 **어떤 도구가** 알려 주는가?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

- **괄호·중복 평가** · **`-E -P` 로 읽는 법** 은 각각 몇 번 형제가 정본인가?
- ★ 36번 형제에는 가변 **매크로**가 있는가?

## 실행 환경

**환경** — gcc 13.3.0 · gcc-12 12.4.0 · clang 18.1.3 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.

★★★ **본체 창은 전처리 결과** — 1번은 **칸마다 만들어진 문자열**과 **두 매크로가 갈린 칸의 수**를 적어야 답이다.
선행 — [42번 형제](../42-function-like-macro-pitfalls/).

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
