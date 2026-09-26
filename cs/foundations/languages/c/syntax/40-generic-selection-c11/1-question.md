# c/syntax/40 — `_Generic` 타입 제네릭 선택 (C11): 「**`_Generic` 은 식을 평가하지 않고 타입만 본다 — 그 타입은 한정자를 벗고 배열을 포인터로 바꾼 뒤의 것이다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · gcc-12 12.4.0 · clang 18.1.3 · g++ 13.3.0 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **제어식의 어떤 타입을 보고 고르나**(한정자 · 배열 · 문자 상수 · 연산 결과) ② **고르지 않은 것은 어떻게 되나**(평가 · 맞는 분기가 없을 때)
> ③ **매크로와 묶었을 때의 한계**(새 타입 · 인자 수 · `<tgmath.h>` 의 실제 구현).
> ★★★ **본체 창은 선택 격자** — 1번은 **인자마다 「고른 분기의 이름」** 과 **컴파일러·판 사이에 갈리나**를 적어야 답이다.
> 선행 — 목록의 **41번 주제**.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **1번은 인자마다 「제어식이 변환된 뒤의 타입」을 먼저 적고** 그다음 목록과 맞춰라.
- ★★ **「에러로 멈춘다」와 「적법하게 조용하다」를 갈라** 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 식은 실제로 평가되나**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 인자 열넷 — 고른 분기 (예측) ★★★ 이 주제의 축

```c
/* s40a.c */
#include <stdio.h>

#define T(x) _Generic((x),                                         \
    char: "char", signed char: "signed char",                      \
    unsigned char: "unsigned char", short: "short",                \
    int: "int", const int: "const int", long: "long",              \
    char *: "char *", const char *: "const char *",                \
    int *: "int *", const int *: "const int *",                    \
    int (*)[3]: "int (*)[3]", double: "double",                    \
    default: "default")

#define P(e) printf("%-10s\t%s\n", #e, T(e))

int main(void) {
    char c = 'x';
    short s = 1;
    const int ci = 2;
    int a[3] = {0};
    const int ca[2] = {0};
    char *pc = &c;
    const char *pcc = "k";
    P(c);  P('a');  P(s);  P(ci);  P(a);  P(&a);  P(ca);
    P(pc);  P(pcc);  P("abc");  P(+c);  P(c + c);  P((char)1);  P(1.0f);
    return 0;
}
```

격자는 이 파일을 **gcc 13 · gcc-12 · clang 18** × **`-std=c11`/`-std=c17`** 로 빌드해 돌린다.

- ★★★ `c` · `'a'` · `s` · `ci` · `a` · `&a` · `ca` 는 각각 어느 분기를 고르는가?
- ★★★ `pc` · `pcc` · `"abc"` · `+c` · `c + c` · `(char)1` · `1.0f` 는?
- ★★ 여섯 빌드 사이에 **고른 분기가 갈리는 칸**이 있는가?
- ★★ 여섯 빌드의 **경고 수**는 같은가?

### 2. 맞는 분기가 없고 `default` 도 없으면 (예측) ★★

```c
/* s40b.c */
int pick(float f) {
    return _Generic(f, int: 1, double: 2);
}
```

- ★★ gcc 와 clang 은 무엇이라고 말하고 `cc exit` 는?
- ★ `float` 은 `double` 칸으로 가는가?

### 3. 제어식과 분기의 부작용 (예측) ★★

```c
/* s40c.c */
#include <stdio.h>

static int calls;
static int bump(void) { return ++calls; }

int main(void) {
    int i = 0;
    int r1 = _Generic(i++, int: 10, default: bump());
    printf("r1 = %d · i = %d · calls = %d\n", r1, i, calls);
    int r2 = _Generic(1.5, int: bump(), double: 20, default: bump());
    printf("r2 = %d · calls = %d\n", r2, calls);
    return 0;
}
```

- ★★ 두 줄에 찍히는 `r1` · `i` · `r2` · `calls` 는?
- ★ gcc 와 clang 중 이 코드에 **경고하는 쪽**은?

### 4. `ABS` 매크로에 `short` 와 사용자 타입 (예측) ★★

```c
/* s40d.c */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define ABS(x) _Generic((x), int: abs, long: labs, double: fabs)(x)

struct money { long cents; };

int main(void) {
    printf("%d %ld %.1f\n", ABS(-3), ABS(-4L), ABS(-2.5));
#ifdef USE_SHORT
    short sh = -7;
    printf("%d\n", ABS(sh));
#endif
#ifdef USE_MONEY
    struct money m = { -500 };
    printf("%ld\n", ABS(m).cents);
#endif
    return 0;
}
```

- ★★ 그냥 빌드하면 무엇이 찍히는가?
- ★★ `-DUSE_SHORT` 와 `-DUSE_MONEY` 로 컴파일하면 각각 무엇이 나오는가?
- ★ gcc 와 clang 은 **어느 줄을 먼저** 짚는가?

### 5. 인자가 둘인 함수를 목록에 (예측) ★★

```c
/* s40d2.c */
#include <stdio.h>
#include <stdlib.h>

struct scaled { long v; };
long scaled_abs(struct scaled s, int unit) { return labs(s.v) / unit; }

#define ABS(x) _Generic((x), int: abs, long: labs, struct scaled: scaled_abs)(x)

int main(void) {
    struct scaled q = { -900 };
    printf("%d %ld\n", ABS(-3), ABS(-4L));
    printf("%ld\n", ABS(q));
    return 0;
}
```

- ★★ 이 파일은 컴파일되는가? 안 된다면 **어느 호출**에서 무엇이라고 하는가?
- ★ `ABS(-3)` 줄은 왜 에러가 아닌가?

### 6. `<tgmath.h>` 의 `sqrt` (예측) ★★

```c
/* s40e.c */
#include <stdio.h>
#include <tgmath.h>

#define NAME(x) _Generic((x), float: "float", double: "double", \
                         long double: "long double", default: "other")

int main(void) {
    float f = 2.0f;
    int n = 2;
    printf("sqrt(f)    -> %s\n", NAME(sqrt(f)));
    printf("sqrt(n)    -> %s\n", NAME(sqrt(n)));
    printf("sqrt(2.0L) -> %s\n", NAME(sqrt(2.0L)));
    return 0;
}
```

- ★★ 세 줄에 찍히는 타입 이름은? gcc 와 clang 이 같은가?
- ★★★ `gcc -E` 와 `clang -E` 결과에서 `_Generic` 은 **몇 번** 나오고, `sqrt` 는 **무엇으로** 풀리는가?

### 7. `const int:` 칸 (왜) ★★

- ★★ 1번의 `const int:` 연관을 고르게 만드는 식이 **있는가**? 표준의 문장으로 이유를 말하면?
- ★ `const` 로 가르고 싶다면 **어디에 붙은** `const` 로 가를 수 있는가(1번의 `ca` · `pcc`)?

### 8. `_Generic` 과 승격 (경계) ★★

- ★★ 1번의 `c` · `+c` · `(char)1` 세 칸을 **승격 규칙**으로 설명하면?
- ★ 함수 호출 `abs(sh)` 와 4번의 `ABS(sh)` 가 다르게 다뤄진다면 그 이유는?

### 9. 36편 가변 인자와 대비 (연결) ★★★

- ★★★ 가변 인자 `...` 와 `_Generic` 은 **타입을 언제** 아는가?
- ★★ 작은 타입(`char`·`float`)을 대하는 방식은 어떻게 반대인가?
- ★★ 타입이 틀렸을 때 **무슨 일이** 나는가 — 두 편의 결과로?

### 10. C++ 의 오버로드 (연결) ★★

```cpp
// s40x.cpp
#include <cstdio>
#include <cstdlib>

struct Money { long cents; };

int    my_abs(int x)    { return std::abs(x); }
long   my_abs(long x)   { return std::labs(x); }
double my_abs(double x) { return x < 0 ? -x : x; }
Money  my_abs(Money m)  { return Money{ std::labs(m.cents) }; }   // 새 타입은 여기에 한 벌 더

int main() {
    short sh = -7;
    std::printf("%d %ld %.1f %d %ld\n", my_abs(-3), my_abs(-4L), my_abs(-2.5), my_abs(sh), my_abs(Money{-500}).cents);
    return 0;
}
```

- ★★ 이 프로그램은 무엇을 찍는가? `my_abs(sh)` 는 어느 함수를 고르는가?
- ★ 새 타입을 받는 비용이 `_Generic` 매크로와 **어떻게 다른가**?

### 11. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / 컴파일러 구현** 칸에 각각 무엇이 들어가는가? **UB** 칸은?
- ★★★ 선택 격자가 **한 칸도 안 갈린** 이유는?
- ★★ gcc 로만 빌드하면 **안 보이는 것** 둘은?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

- **`typedef` 와 `two compatible types`** · **`NULL` 의 타입**은 어느 형제가 이미 보였는가?
- **매크로의 규칙**은 목록의 몇 번 주제인가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
