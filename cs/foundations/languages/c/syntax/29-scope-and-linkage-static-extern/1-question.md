# c/syntax/29 — 스코프와 링크(`static`·`extern`): 「**이 이름은 어디까지 보이고, 다른 파일의 같은 이름과 같은 것인가**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · gcc-12 12.4.0 · clang 18.1.3 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **`static` 이 자리마다 무엇을 바꾸나**(링크 대 저장 기간) ② **`nm` 의 글자가 무엇을 말하고 무엇을 못 말하나**
> ③ **같은 이름이 두 파일에 있을 때 어느 단계에서 무엇이 죽나**(컴파일 · 링크 · 판).
> ★★★ **본체 창은 `nm`** 이다 — 2·4·5·6번은 **심볼의 글자**까지 적어야 답이다.
> ★★★ **4번과 6번은 판 격자**다 — 한 칸으로 답하지 마라.
> ★ **종료 코드는 단계별로** 적어라 — 「컴파일 `exit` / 링크 `exit`」.
> 선행 — [28번 형제](../28-choosing-among-four-storage-durations/) · [25번 형제](../25-incomplete-types-and-opaque-struct/).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 출력·심볼·종료 코드를 적어 본 뒤** 답을 연다.
- ★★★ **2번은 「외부/내부」로 끝내면 답이 아니다** — **`nm` 의 글자 한 개씩**과 **심볼이 아예 없는 줄**까지.
- ★★ **4번은 컴파일러 셋 × 플래그 셋**이다 — 판 경계(GCC 10 · Clang 11)는 **이 머신에서 잴 수 있나**도 답해라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 이름은 몇 개의 물건을 가리키나**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 겹으로 가린 `x` 와 블록 안의 `extern` (예측) ★★

```c
/* s29g.c */
#include <stdio.h>

int x = 1;                               /* 파일 스코프 */

int main(void) {
    printf("파일 스코프         x = %d\n", x);
    int x = 2;                           /* 블록 스코프 — 파일의 x 를 가린다 */
    printf("main 블록           x = %d\n", x);
    {
        int x = 3;                       /* 더 안쪽 블록 — 또 가린다 */
        printf("안쪽 블록           x = %d\n", x);
        {
            extern int x;                /* ★ 가려진 파일 스코프 x 를 다시 부른다 */
            printf("extern 으로 부른    x = %d\n", x);
        }
    }
    for (int x = 4; x < 5; x++)          /* for 의 첫 칸도 블록 스코프다 */
        printf("for 머리            x = %d\n", x);
    printf("다시 main 블록      x = %d\n", x);
    return 0;
}
```

- 여섯 줄은 각각 무엇을 찍는가?
- ★★★ `extern int x;` 줄은 **바로 바깥의 `x = 3`** 을 가리키는가, 다른 것을 가리키는가? 왜?
- ★★ `-Wall -Wextra -pedantic` 에서 경고는 몇 건인가? **`-Wshadow` 를 더하면**?
- ★ `-Wshadow` 가 경고하는 줄에 **`extern` 줄이 들어가는가**?
- ★ `for (int x = 4; …)` 의 `x` 는 루프가 끝난 뒤에도 보이는가?

### 2. 한 파일의 선언 열 개가 `nm` 에서 무엇으로 나오나 (예측) ★★★ 이 주제의 축

```c
/* s29a.c */
int        g_def = 1;          /* 외부 링크 · 정의 · 값 있음 */
int        g_zero = 0;         /* 외부 링크 · 정의 · 0 */
static int s_def = 2;          /* 내부 링크 · 정의 · 값 있음 */
static int s_zero;             /* 내부 링크 · 정의 · 0 */
extern int e_used;             /* 외부 링크 · 선언만 — 쓴다 */
extern int e_unused;           /* 외부 링크 · 선언만 — 안 쓴다 */

static int helper(void) { return s_def + s_zero; }   /* 내부 링크 함수 */

int api(void) {                                      /* 외부 링크 함수 */
    static int calls;          /* ★ 링크 없음 · 정적 저장 기간 */
    int        local = 0;      /* ★ 링크 없음 · 자동 저장 기간 */
    calls++;
    local++;
    return helper() + g_def + g_zero + e_used + calls + local;
}
```

- ★★★ `gcc -c` 뒤 `nm` 에서 **각 이름의 글자**는 무엇인가? (`D`/`d`/`B`/`b`/`T`/`t`/`U`)
- ★★★ **심볼이 아예 안 생기는 이름**이 둘 있다 — 무엇이고 왜인가?
- ★★ `g_zero = 0` 은 `D` 인가 `B` 인가?
- ★★ 함수 안 `static int calls` 는 **어떤 이름**으로 나오는가? ★ **gcc 와 clang 이 같은가**?
- ★★ `readelf -s` 의 `Bind` 칸은 `nm` 의 대소문자와 어떻게 대응하는가?
- ★ `nm` 의 **주소 칸**을 근거로 써도 되는가?

### 3. 두 파일에 같은 이름을 정의하고, 그다음 `static` 을 붙이면 (예측) ★★

```c
/* s29b1.c */
int shared = 1;                /* ★ 외부 링크 정의 */
int from_b1(void) { return shared; }
```

```c
/* s29b2.c */
#include <stdio.h>

int shared = 2;                /* ★ 같은 이름의 외부 링크 정의 — 두 번째 */
int from_b1(void);

int main(void) {
    printf("b1 쪽 shared = %d · b2 쪽 shared = %d\n", from_b1(), shared);
    return 0;
}
```

- 두 파일을 `-c` 로 컴파일하면 각각 `exit` 는?
- ★★★ 링크하면 무슨 일이 나는가? **진단 첫 줄**을 적으면? ★ **gcc 와 clang 의 진단은 어디가 같고 어디가 다른가**?
- ★★ 두 파일의 `shared` 앞에 `static` 을 붙이면(`s29c1.c`·`s29c2.c`) 링크와 출력은 어떻게 되는가?
- ★★ 그때 `nm` 의 글자는?
- ★ 「`static` 을 붙여 링크 오류를 없앴다」가 **틀린 처방이 되는 경우**는?

### 4. `int t;` 를 두 파일에 두면 — 판 격자 (예측) ★★★

```c
/* s29t1.c */
int t;                         /* ★ 잠정 정의(tentative definition) — 초기자 없음 */
int get_t1(void) { return t; }
```

```c
/* s29t2.c */
#include <stdio.h>

int t;                         /* ★ 같은 이름의 잠정 정의 — 두 번째 파일 */
int get_t1(void);

int main(void) {
    t = 5;
    printf("t2 쪽 t = %d · t1 쪽 t = %d\n", t, get_t1());
    return 0;
}
```

```c
/* s29u1.c */
int t = 0;                     /* ★ 초기자가 있다 — 잠정 정의가 아니라 정의 */
int get_t1(void) { return t; }
```

- ★★★ **gcc-12 · gcc 13 · clang 18 × (기본) · `-fno-common` · `-fcommon`** 아홉 칸의 **컴파일 `exit` · 링크 `exit` · 출력**은?
- ★★★ `-fcommon` 칸에서 `t1 쪽 t` 는 **얼마**로 찍히는가? 그것이 무엇을 뜻하는가?
- ★★ **한쪽에 `int t = 0;`**(`s29u1.c`)을 두면 결과가 바뀌는가?
- ★★ `nm` 에서 `-fcommon` 판과 기본 판의 **`t` 의 글자**는?
- ★★★ 「GCC 10 · Clang 11 부터 기본값이 바뀌었다」는 **이 머신에서 잰 것인가**?
- ★★ **표준은 두 파일의 잠정 정의를 무엇으로 보는가**? `-fcommon` 의 병합은 **어느 층**인가?

### 5. `static` 함수를 다른 파일에서 부르면 — 단계별로 (예측) ★★

```c
/* s29d1.c */
static int helper(void) { return 7; }   /* ★ 내부 링크 */
int use_helper(void) { return helper(); }
```

```c
/* s29d2.c */
#include <stdio.h>

int helper(void);              /* ★ 외부 링크로 선언 — 다른 파일의 static 을 부르려 한다 */

int main(void) {
    printf("helper() = %d\n", helper());
    return 0;
}
```

- ★★★ **① `s29d1.c` 컴파일 · ② `s29d2.c` 컴파일 · ③ 링크** 의 `exit` 는 각각?
- ★★ 링커 진단의 **핵심 한 줄**은?
- ★★★ `nm` 에서 `helper` 는 두 파일에서 **각각 어떤 글자**인가? 그것이 링크 실패를 **어떻게 설명하는가**?
- ★ 링커 진단은 「**정의가 없다**」와 「**있는데 안 보인다**」를 **가르는가**?
- ★ 컴파일 단계만 도는 검사로 이것을 잡을 수 있는가?

### 6. C99 `inline` — 파일 셋 × 컴파일러 둘 × 최적화 둘 (예측) ★★

```c
/* s29f.c */
#include <stdio.h>

inline int twice(int x) { return 2 * x; }   /* ★ inline 만 — 외부 정의가 아니다 */

int main(void) {
    printf("twice(21) = %d\n", twice(21));
    return 0;
}
```

```c
/* s29f2.c */
#include <stdio.h>

inline int twice(int x) { return 2 * x; }
extern inline int twice(int x);             /* ★ 이 한 줄이 이 파일에 외부 정의를 만든다 */

int main(void) {
    printf("twice(21) = %d\n", twice(21));
    return 0;
}
```

```c
/* s29f3.c */
#include <stdio.h>

static inline int twice(int x) { return 2 * x; }   /* ★ 내부 링크 — 필요하면 이 파일에 사본을 만든다 */

int main(void) {
    printf("twice(21) = %d\n", twice(21));
    return 0;
}
```

- ★★★ 열두 칸의 **링크 `exit`** 는? ★ **최적화 수준이 링크 결과를 바꾸는 칸**이 있는가?
- ★★★ `-O0` 으로 컴파일한 세 오브젝트에서 `nm` 의 **`twice` 글자**는 각각 무엇인가?
- ★★ `-O2` 에서 `s29f` 가 통과하는 이유는 무엇이고, 그것은 **보장인가**?
- ★ 인라인 정의와 외부 정의가 **둘 다 있으면** 어느 쪽이 불리는가 — 표준은 무엇이라 하는가?
- ★ C++ 의 `inline` 과 **같은 뜻인가**?

### 7. `static` 한 낱말이 두 가지를 바꾼다 — 그런데 `nm` 은 (왜) ★★★

- ★★★ **파일 스코프 `static`** 은 링크와 저장 기간 중 **무엇을 바꾸는가**? 다른 하나는 원래 무엇이었나?
- ★★★ **함수 안 `static`** 은 무엇을 바꾸는가? 다른 하나는?
- ★★★ `nm` 에서 두 경우의 글자는 **같은가 다른가**? 왜 그런가 — ELF 에는 무슨 칸이 **없는가**?
- ★★ 그럼 `nm` 에서 둘을 **무엇으로** 가를 수 있는가? 그것은 **표준의 보장**인가?
- ★ 「`nm` 에 소문자면 내부 링크다」는 몇 할이 맞는가?

### 8. `extern int val;` 인데 정의는 `double` 이면 — 누가 잡나 (경계) ★★

```c
/* s29e1.c */
double val = 3.5;              /* ★ 정의는 double */
```

```c
/* s29e2.c */
#include <stdio.h>

extern int val;                /* ★ 선언은 int — 타입이 다르다 */

int main(void) {
    printf("val 을 int 로 읽으면 = %d\n", val);
    return 0;
}
```

- ★★★ **gcc · gcc `-flto` · clang · clang `-flto` · ASan+UBSan 두 벌** 여섯 벌 중 **무엇이라도 말하는 것**은 몇 벌인가?
- ★★ 그 한 벌의 **진단 플래그**와 **`cc exit`** 는?
- ★★ **ASan·UBSan 이 원리상 못 보는 이유**는?
- ★★ 출력 `0` 은 **어떻게 읽어야 하는가**?
- ★ [25번 형제](../25-incomplete-types-and-opaque-struct/)의 `-flto` 결과와 **이어 보면** gcc `-flto` 가 보는 것은 **어디까지**인가?
- ★ 「`-flto` 가 잡는다」를 **플래그의 성질**로 적으면 무엇이 틀리는가?

### 9. 괄호 안에서 처음 나온 `struct Point` (왜) ★

```c
/* s29h.c */
void take(struct Point *p);              /* ★ struct Point 가 여기서 처음 나온다 */

struct Point { int x, y; };              /* 파일 스코프의 struct Point — 다른 타입이다 */

void take(struct Point *p) { (void)p; }

int main(void) { return 0; }
```

- ★★ 1행의 `struct Point` 는 **어느 스코프**에 선언되는가?
- ★★ 그래서 5행과 무슨 일이 나는가? `cc exit` 는?
- ★★ gcc 의 `conflicting types` 진단이 **두 타입을 어떤 글자로** 찍는가? 그것을 **근거로 쓰면** 왜 막히는가?
- ★ 처방 한 줄은?

### 10. C++ 은 같은 문제를 어떻게 푸나 (연결) ★★

- ★★ C 의 **파일 스코프 `static`** 자리를 C++ 에서는 **무엇이** 맡는가? `nm` 에서 무엇으로 나오는가?
- ★★★ C++17 **`inline` 변수**를 두 파일에 두면 링크되는가? **C 의 3번과 무엇이 다른가**?
- ★★ 그 `inline` 변수의 `nm` 글자는 **g++ 와 clang++ 가 같은가**?
- ★ C 의 `-fcommon` 과 C++ 의 `inline` 변수는 **같은 일을 어느 층에서** 하는가?

### 11. 다섯 층과 무게중심 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / 구현 정의 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- ★★★ **조건부 표준 칸**에 들어가는 것은 무엇이고, 그것이 **다른 편들과 다른 점**은?
- ★★ **가장 두꺼운 칸**과 **두 번째로 두꺼운 칸**은?
- ★★ **도구가 침묵하는 자리**를 층마다 하나씩 대면?
- ★★ 이 편에 「**종료 코드 0인데 ill-formed**」 새 항목이 있는가? 없다면 **대신 무엇이** 있는가?
- ★ 이 편에서 **쓰지 않은 창**(부적용)은 무엇이고, 왜 「안 쟀다」가 아니라 「잴 것이 없다」인가?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

- **링커가 심볼을 해석하는 방식** 일반은 어느 주제가 정본인가?
- **저장 기간**과 **파일 스코프 `const` 의 링크**는 각각 어느 형제가 정본인가?
- **`inline` 규칙 전체** · **헤더에 무엇을 두나** · **링크 오류 거꾸로 읽기**는 각각 목록의 몇 번 주제인가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
