# c/syntax/35 — 함수 포인터와 콜백 테이블: 「**함수 이름은 주소가 되고, 테이블은 재배치를 기다린다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · x86-64 Linux · glibc · 기본 `-std=c17 -Wall -Wextra -pedantic` · **이 판의 기본 빌드는 PIE**.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **테이블이 어디에 놓이나**(섹션 · 재배치) ② **콜백이 틀리면 무엇이 나오고 누가 잡나**(비교자 · 서명 불일치)
> ③ **함수 포인터의 선언과 값**(이름이 포인터가 되는 자리 · `signal` 모양 · `void *` 경계).
> ★★★ **본체 창은 `objdump -t` 의 섹션 칸** — 3번은 **섹션 이름까지** 적어야 답이다.
> ★ **시간은 묻지 않는다** — 간접 호출의 비용은 재지 않았다.
> 선행 — [06번 형제](../06-typedef-and-type-aliases/) · [14번 형제](../14-pointers-address-dereference-and-pointer-types/).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **3번은 판 격자**다 — 컴파일러 2 × 플래그 3. 한 칸으로 답하지 마라.
- ★★ **5번은 컴파일 단계와 실행 단계를 갈라** 적어라 — 두 컴파일러가 **다른 단계**에서 말할 수 있다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 포인터로 부르는 함수의 진짜 서명은 무엇인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `twice` · `&twice` · `*twice` · `**twice` (예측) ★★

```c
/* s35a.c */
#include <stdio.h>

static int twice(int x) { return 2 * x; }

int main(void) {
    int (*p1)(int) = twice;
    int (*p2)(int) = &twice;
    int (*p3)(int) = *twice;
    int (*p4)(int) = **twice;
    printf("p1 == p2 : %d   p1 == p3 : %d   p1 == p4 : %d\n", p1 == p2, p1 == p3, p1 == p4);
    printf("p1(5) = %d   (*p1)(5) = %d   (**p1)(5) = %d   (***p1)(5) = %d\n",
           p1(5), (*p1)(5), (**p1)(5), (***p1)(5));
    printf("sizeof p1 = %zu\n", sizeof p1);
    return 0;
}
```

- ★★ 세 비교(`p1 == p2` · `p1 == p3` · `p1 == p4`)의 값은? 네 호출의 값은?
- ★ `*twice` 가 **컴파일되는** 이유를 「함수 지시자」라는 낱말로 설명할 수 있는가?

### 2. `sizeof` 를 함수에 (예측) ★★

```c
/* s35b.c */
#include <stdio.h>

static int twice(int x) { return 2 * x; }

int main(void) {
    printf("sizeof twice  = %zu\n", sizeof twice);
    printf("sizeof &twice = %zu\n", sizeof &twice);
    return 0;
}
```

- ★★ 두 컴파일러는 `-pedantic` 에서 **`cc exit`** 는? 경고는?
- ★★ 실행하면 두 줄은 무엇을 찍는가?
- ★ `-pedantic-errors` 로 올리면? 이 코드는 **표준의 어느 층**에 걸리는가?

### 3. 디스패치 테이블이 놓이는 섹션 (예측) ★★★ 이 주제의 축

```c
/* s35c.c */
static int op_add(int a, int b) { return a + b; }
static int op_sub(int a, int b) { return a - b; }
static int op_mul(int a, int b) { return a * b; }

int (*table_rw[3])(int, int)       = { op_add, op_sub, op_mul };
int (*const table_ro[3])(int, int) = { op_add, op_sub, op_mul };

int call_rw(int i, int a, int b) { return table_rw[i](a, b); }
int call_ro(int i, int a, int b) { return table_ro[i](a, b); }
```

- ★★★ `table_rw` 와 `table_ro` 는 **gcc/clang × 기본 · `-fno-PIE` · `-fPIC`** 에서 각각 **어느 섹션**에 놓이는가?
- ★★★ `table_ro` 가 `.rodata` 가 **아닌** 칸이 있다면, 그 이유를 `objdump -r` 의 무엇으로 보이는가?
- ★★ `call_rw` 와 `call_ro` 의 `-O2` 어셈블리는 다른가?

### 4. `const` 테이블에 캐스트로 쓰면 (예측) ★★

```c
/* s35c2.c */
#include <stdio.h>

static int op_add(int a, int b) { return a + b; }
static int op_sub(int a, int b) { return a - b; }

int (*table_rw[2])(int, int)       = { op_add, op_sub };
int (*const table_ro[2])(int, int) = { op_add, op_sub };

int main(void) {
    table_rw[0] = op_sub;
    fprintf(stderr, "[1] after writing table_rw[0]\n");
    *(int (**)(int, int))&table_ro[0] = op_sub;   /* const 를 캐스트로 떼고 쓴다 */
    fprintf(stderr, "[2] after writing table_ro[0]\n");
    return table_ro[0](1, 2);
}
```

- ★★ 기본 빌드와 `-no-pie -fno-PIE` 에서 **`run exit`** 와 표준 오류에 찍히는 마커는?
- ★★ 두 빌드의 결과가 같다면, **같은 결과에 이르는 길**도 같은가?
- ★ 이 결과를 「`const` 테이블은 쓰면 죽는다」는 **규칙**으로 적어도 되는가?

### 5. 서명이 다른 함수 포인터로 부르기 (예측) ★★★

```c
/* s35e.c */
#include <stdio.h>

static int take_int(int x) { return x + 1; }

typedef int (*FnLong)(long);

int main(void) {
    FnLong g = (FnLong)take_int;          /* 서명이 다른 타입으로 캐스트 */
    fprintf(stderr, "[1] before the call\n");
    int r = g(41L);
    fprintf(stderr, "[2] after the call, r = %d\n", r);
    return 0;
}
```

- ★★★ **컴파일 단계** — gcc 와 clang 은 각각 무엇을 말하는가? 경고가 있다면 **어느 플래그**가 켠 것인가?
- ★★★ **실행 단계** — `-fsanitize=undefined` · `-fsanitize=function` 을 두 컴파일러에 주면?
- ★★ `r` 의 값은? 그 값을 근거로 「이 캐스트는 안전하다」고 할 수 있는가?

### 6. `qsort` 비교자 둘 (예측) ★★★

```c
/* s35d.c */
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

static int cmp_sub(const void *pa, const void *pb) {
    int a = *(const int *)pa, b = *(const int *)pb;
    return a - b;
}

static int cmp_rel(const void *pa, const void *pb) {
    int a = *(const int *)pa, b = *(const int *)pb;
    return (a > b) - (a < b);
}

static void run(const char *tag, int (*cmp)(const void *, const void *)) {
    int v[] = { 3, INT_MIN, 1, INT_MAX, -2, 0 };
    size_t n = sizeof v / sizeof v[0];
    qsort(v, n, sizeof v[0], cmp);
    int sorted = 1;
    for (size_t i = 1; i < n; i++) if (v[i - 1] > v[i]) sorted = 0;
    printf("%-8s", tag);
    for (size_t i = 0; i < n; i++) printf(" %d", v[i]);
    printf("   | sorted? %s\n", sorted ? "yes" : "no");
}

int main(void) {
    run("cmp_sub", cmp_sub);
    run("cmp_rel", cmp_rel);
    return 0;
}
```

- ★★★ `cmp_sub` 와 `cmp_rel` 의 `sorted?` 는 **gcc/clang × `-O0`/`-O2`** 에서?
- ★★★ UBSan 은 무엇을 **어느 줄 어느 칸**으로 말하는가? 프로그램은 **거기서 멈추는가**?
- ★★ `cmp_sub` 줄에 찍힌 숫자의 순서 자체는 근거로 쓸 수 있는 칸인가?

### 7. `signal` 모양의 선언 (왜) ★★

`void (*set_raw(int sig, void (*fn)(int)))(int);` 와 `typedef void (*Handler)(int); Handler set_td(int, Handler);`.

- ★★ `set_raw` 를 **안쪽 → 바깥으로** 읽어 말로 옮기면?
- ★★ 두 선언이 **같은 타입**이라는 것을 컴파일러로 어떻게 확인하는가?

### 8. 함수 포인터 ↔ `void *` (경계) ★★

- ★★ gcc 와 clang 은 `-pedantic` · `-pedantic-errors` 에서 각각 무엇을 말하는가?
- ★★ 표준 문서에서 이것은 **제약 위반**인가? 그렇지 않다면 어느 층인가?
- ★ gcc 의 문구 「**ISO C forbids**」와 표준 문서 사이에 틈이 있다면 무엇인가?

### 9. 다섯 층과 무게중심 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / 구현 정의 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- ★★★ **섹션 이름**은 어느 층인가? 그것이 본체 창이라는 것은 무엇을 뜻하는가?
- ★★ 이 편의 **「종료 코드 0인데 ill-formed」** 새 항목은?
- ★★ **두 컴파일러가 서로 다른 창에서 말한** 자리는?

### 10. 다른 언어의 호출 가능 타입 (연결) ★

- ★ Rust 에서 **무언가 잡은 클로저**를 `fn(i32) -> i32` 에 담으면? C 의 함수 포인터와 무엇이 같고 무엇이 다른가?
- ★ C++ 의 `std::function` 은 C 의 함수 포인터에 **무엇을** 더한 것인가(C++ 갈래 목록의 몇 번)?

### 11. 경계 — 어디까지가 이 주제인가 (연결) ★

- **선언 읽기**와 **`typedef` 로 자르기**는 각각 어느 형제가 정본인가?
- 함수 포인터 → `void *` 의 **첫 실측**은 어느 형제에 있나?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
