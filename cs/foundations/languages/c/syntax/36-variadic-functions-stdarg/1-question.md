# c/syntax/36 — 가변 인자 함수 `<stdarg.h>`: 「**`...` 뒤에서는 타입이 사라지고, 승격된 것만 남는다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · gcc-12 12.4.0 · clang 18.1.3 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **승격된 인자를 무엇으로 꺼내나**(두 컴파일러의 컴파일 · 실행 · sanitizer) ② **타입과 개수는 누가 검사하나**(`printf` 대 내 함수 · 속성)
> ③ **`va_list` 의 규칙**(`va_copy` · `va_end` · C23).
> ★★★ **본체 창은 승격 격자** — 2번은 **칸마다 경고 · 종료 코드 · 값이 같나**를 적어야 답이다.
> ★★ **UB 의 값은 「같나」 참/거짓으로만** 적어라 — 쓰레기 값 자체를 맞히는 문항이 아니다.
> 선행 — [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/) · [34번 형제](../34-function-declarations-definitions-and-prototypes/).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **1·2번은 두 컴파일러를 따로** 적어라 — 같은 경고를 내고도 **실행이 정반대**일 수 있다.
- ★★ **3·4번은 「컴파일러가 아는 것」과 「모르는 것」을 갈라** 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 인자가 `...` 를 지나며 무슨 타입이 됐나**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `float` 을 넘기고 `double` · `float` 으로 꺼내기 (예측) ★★★

```c
/* s36a.c */
#include <stdarg.h>
#include <stdio.h>

static double get_double(int n, ...) {
    va_list ap;
    va_start(ap, n);
    double v = va_arg(ap, double);
    va_end(ap);
    return v;
}

static double get_float(int n, ...) {
    va_list ap;
    va_start(ap, n);
    float v = va_arg(ap, float);
    va_end(ap);
    return v;
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    float f = 1.5f;
    printf("[1] va_arg(ap, double) -> %g\n", get_double(1, f));
    printf("[2] va_arg(ap, float)  -> %g\n", get_float(1, f));
    return 0;
}
```

- ★★★ 두 컴파일러는 `get_float` 에 **무엇이라고** 경고하는가? `cc exit` 는?
- ★★★ 실행하면 두 컴파일러에서 **각각** 무엇이 찍히고 **`run exit`** 는?
- ★★ gcc `-O2` 의 `get_float` 어셈블리 끝에는 **무슨 명령**이 있는가?
- ★★ ASan·UBSan 을 켜면 결과가 바뀌는가?

### 2. 승격 격자 — 넘긴 타입과 꺼낸 타입 (예측) ★★★ 이 주제의 축

```c
/* s36b.c */
#include <stdarg.h>
#include <stdio.h>

#ifndef PASS                       /* 격자는 -DPASS=… -DPULL=… -DVAL=… 로 바꿔 끼운다 */
#define PASS char
#define PULL char
#define VAL  'A'
#endif

static int same(int n, ...) {
    va_list ap;
    va_start(ap, n);
    PASS got = (PASS)va_arg(ap, PULL);
    va_end(ap);
    return got == (PASS)VAL;
}

int main(void) {
    printf("%d\n", same(1, (PASS)VAL));
    return 0;
}
```

격자는 `-DPASS=… -DPULL=… -DVAL=…` 로 `char`·`unsigned char`·`short`·`_Bool`·`float` 을 넘기고, **같은 타입** 또는 **승격된 타입**(`int`·`double`)으로 꺼낸다.

- ★★★ **승격된 타입으로 꺼낸 줄**은 gcc/clang × `-O0`/`-O2` 에서 어떻게 되는가?
- ★★★ **같은 타입으로 꺼낸 줄**은? 두 컴파일러가 **갈리는가**? 갈린다면 **몇 줄**인가?
- ★★ clang 에서 **값이 맞아 보이는** 줄이 있다면 어느 것이고, 왜 그것이 **가장 위험한** 칸인가?
- ★ `-O0` 과 `-O2` 사이에 움직인 칸이 있는가?

### 3. `printf` · 내 로그 함수 · 속성을 붙인 로그 함수 (예측) ★★

```c
/* s36c.c */
#include <stdarg.h>
#include <stdio.h>

static void my_log(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vprintf(fmt, ap);
    va_end(ap);
}

__attribute__((format(printf, 1, 2)))
static void my_log_checked(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vprintf(fmt, ap);
    va_end(ap);
}

int main(void) {
    printf("printf         : %d\n", 3.0);
    my_log("my_log         : %d\n", 3.0);
    my_log_checked("my_log_checked : %d\n", 3.0);
    return 0;
}
```

- ★★★ 세 줄 중 **어느 줄에** 경고가 나는가? 두 컴파일러가 같은가?
- ★★ 경고가 **나지 않는** 줄이 있다면 왜인가?
- ★ `printf("%d\n", 3.0)` 을 10 번 돌리면 `3` 이 몇 번 찍히는가? 그 수가 흔들린다면 무엇을 대신 적는가?

### 4. 끝을 알리는 두 방법 — 센티널과 개수 인자 (예측) ★★

```c
/* s36d.c */
#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>

__attribute__((sentinel))
static int count_until_null(const char *first, ...) {
    va_list ap;
    int n = 0;
    va_start(ap, first);
    for (const char *s = first; s != NULL; s = va_arg(ap, const char *)) n++;
    va_end(ap);
    return n;
}

static int sum_n(int n, ...) {
    va_list ap;
    int total = 0;
    va_start(ap, n);
    for (int i = 0; i < n; i++) total += va_arg(ap, int);
    va_end(ap);
    return total;
}

int main(void) {
    printf("%d\n", count_until_null("a", "b", "c", (char *)NULL));
    printf("%d\n", count_until_null("a", "b", "c"));
    printf("%d\n", sum_n(3, 10, 20, 30));
    printf("%d\n", sum_n(8, 10, 20, 30));
    return 0;
}
```

- ★★ 두 컴파일러는 `count_until_null("a", "b", "c")` 에 무엇을 말하는가?
- ★★ `sum_n(8, 10, 20, 30)` 에는?
- ★ 이 소스의 실행 결과를 싣지 **않은** 이유는?

### 5. 셋을 넘기고 여덟을 읽으면 — sanitizer (예측) ★★

```c
/* s36e.c */
#include <stdarg.h>
#include <stdio.h>

static int sum_n(int n, ...) {
    va_list ap;
    unsigned total = 0;                  /* 쓰레기 값을 더해도 넘침(UB)이 안 나게 unsigned 로 */
    va_start(ap, n);
    for (int i = 0; i < n; i++) total += (unsigned)va_arg(ap, int);
    va_end(ap);
    return (int)total;
}

int main(void) {
    fprintf(stderr, "[1] sum_n(3, ...) == 60 ? %d\n", sum_n(3, 10, 20, 30) == 60);
    volatile int got = sum_n(8, 10, 20, 30);  /* 셋을 넘기고 여덟을 읽는다 */
    (void)got;
    fprintf(stderr, "[2] after sum_n(8, ...)\n");
    return 0;
}
```

- ★★ gcc ASan·UBSan, clang ASan·UBSan·MSan 중 **리포트를 내는 것**은?
- ★ 모두 침묵한다면, 그것은 이 코드가 **안전하다는 뜻**인가?

### 6. `va_list` 를 두 번 쓰기 (예측) ★★

```c
/* s36f.c */
#include <stdarg.h>
#include <stdio.h>

static int sum(int n, va_list ap) {
    int t = 0;
    for (int i = 0; i < n; i++) t += va_arg(ap, int);
    return t;
}

static void twice_plain(int n, ...) {
    va_list ap;
    va_start(ap, n);
    int a = sum(n, ap);
    int b = sum(n, ap);                   /* 같은 ap 를 한 번 더 */
    va_end(ap);
    printf("twice_plain : first == 60 ? %d   second == 60 ? %d\n", a == 60, b == 60);
}

static void twice_copy(int n, ...) {
    va_list ap, ap2;
    va_start(ap, n);
    va_copy(ap2, ap);
    int a = sum(n, ap);
    int b = sum(n, ap2);
    va_end(ap2);
    va_end(ap);
    printf("twice_copy  : first == 60 ? %d   second == 60 ? %d\n", a == 60, b == 60);
}

int main(void) {
    printf("sizeof(va_list) = %zu\n", sizeof(va_list));
    twice_plain(3, 10, 20, 30);
    twice_copy(3, 10, 20, 30);
    return 0;
}
```

- ★★ `sizeof(va_list)` 는? `twice_plain` 과 `twice_copy` 의 두 번째 합은 각각 `60` 인가?
- ★★ `twice_plain` 의 두 번째가 틀렸다면 표준은 그 `ap` 를 **무엇이라고** 부르는가?
- ★ `va_list` 가 **배열처럼** 동작한다는 것이 결과를 어떻게 설명하는가?

### 7. `va_end` 를 안 부르면 (경계) ★★

- ★★ `with_end` 와 `without_end` 의 어셈블리는 네 벌에서 얼마나 다른가?
- ★★ 그 결과를 근거로 「`va_end` 는 빼도 된다」고 적어도 되는가? 표준은 무엇이라고 하는가?
- ★ 실행으로 이 질문에 답하기 어려운 이유는?

### 8. C23 의 `va_start(ap)` 와 `f(...)` (경계) ★★

- ★★★ 두 형태는 **gcc-12 · gcc 13 · clang 18** × `-std=c17`/`-std=c2x` 에서 각각 받아들여지는가?
- ★★ clang 이 C23 에서 받으면서도 경고를 낸다면, 그 경고는 **옳은 말**인가? 무엇을 근거로 판정하는가?

### 9. 34 → 36 — 같은 규칙, 두 자리 (왜) ★★★

- ★★★ 34편의 **빈 괄호 호출**과 이 편의 **`...` 호출**에 공통인 규칙은? 34편 어셈블리의 **`cvtss2sd` 와 `al`** 은 이 편과 어떻게 이어지는가?
- ★★ C23 에서 그 규칙이 걸리는 자리는 **몇 곳**으로 줄었나?

### 10. 다른 언어의 가변 인자 (연결) ★

- ★ Go 의 `func sum(xs ...float32)` 안에서 `xs` 의 타입은? `float32` 는 승격되는가?
- ★ C++ 은 가변 인자 함수 대신 **무엇**을 쓰는가(C++ 갈래 목록의 몇 번)?

### 11. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / 구현 정의 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- ★★★ **`va_arg` 불일치를 잡은 도구**는 무엇이었고, 못 잡은 것은?
- ★★ gcc 의 `ud2` 는 **보장**인가 **선택**인가?
- ★★ 이 편에 「**종료 코드 0인데 ill-formed**」 새 항목이 있는가? 없다면 **대신 무엇이** 많은가?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

- **정수 승격**과 **`float` 변환**은 각각 어느 형제가 정본인가?
- **`printf` 형식 문자열**은 목록의 몇 번 주제인가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
