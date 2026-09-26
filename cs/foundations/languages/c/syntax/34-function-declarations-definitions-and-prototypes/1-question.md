# c/syntax/34 — 함수 선언·정의·프로토타입: 「**빈 괄호는 C17 에서 「모른다」, C23 에서 「없다」**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · **gcc-12 12.4.0** · clang 18.1.3 · x86-64 Linux · 기본 `-Wall -Wextra -pedantic`. C23 은 **`-std=c2x`** 로 부른다.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **빈 괄호의 뜻이 판마다 다르다**(C17 대 C23 — 그리고 컴파일러 판) ② **프로토타입이 없으면 검사가 사라지고 승격이 일어난다**
> ③ **선언 없이 부르기**가 판마다 무엇이 되나.
> ★★★ **본체 창은 판 격자의 `cc exit`** — 1·2·4번은 **칸마다 `exit` 를** 적어야 답이다.
> ★★ **「경고냐 에러냐」를 가르는 것은 컴파일러 · 판 · 강도(`-pedantic` / `-pedantic-errors`) 셋**이다.
> 선행 — [01번 형제](../01-declaration-syntax-and-reading/).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **1·2·4번은 판 격자**다 — 한 컴파일러 한 판으로 답하지 마라.
- ★★ **5번은 「값이 맞나」와 「도구가 말하나」를 갈라** 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 줄에서 컴파일러가 아는 매개변수 정보는 무엇인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 빈 괄호 선언 뒤에 인자 둘로 부르기 — `-std=c17` 대 `-std=c2x` (예측) ★★★ 이 주제의 축

```c
/* s34a.c */
#include <stdio.h>

int f();                          /* 괄호 안이 비었다 */

int main(void) {
    printf("f(1, 2) = %d\n", f(1, 2));
    return 0;
}

int f(int a, int b) { return a + b; }
```

```c
/* s34v.c */
#include <stdio.h>

int f(void);                      /* void 를 적었다 */

int main(void) {
    printf("f() = %d\n", f());
    return 0;
}

int f(void) { return 42; }
```

- ★★★ `s34a.c` 를 **gcc-12 · gcc 13 · clang 18** × **`-std=c17` · `-std=c2x`**(`-Wall -Wextra -pedantic -c`)로 컴파일하면 칸마다 `cc exit` 는?
- ★★ `-std=c17` 에서 **gcc 는 경고를 몇 개** 내는가? clang 은?
- ★★ gcc 13 의 `-std=c2x` 진단은 `f` 의 타입을 **무엇이라고** 적는가?
- ★★ `s34v.c` 는 판에 따라 갈리는가?
- ★ gcc-12 의 `-std=c2x` 를 **`-pedantic-errors`** 로 올리면?

### 2. 옛(K&R) 정의 (예측) ★★★

```c
/* s34b.c */
#include <stdio.h>

int g(a, b)                       /* 매개변수 이름만 적고 */
    int a;                        /* 타입은 괄호 밖에서 */
    int b;
{
    return a * b;
}

int main(void) {
    printf("g(3, 4) = %d\n", g(3, 4));
    return 0;
}
```

- ★★★ gcc 13 과 clang 18 은 `-std=c17` · `-std=c2x` 에서 각각 무엇을 하는가? `cc exit` 는?
- ★★ gcc 13 `-std=c2x` 를 `-pedantic-errors` 로 올리면?
- ★★ 두 컴파일러의 C23 진단이 **다른 모양**이라면, 각각 그 문법을 **무엇으로** 다루는 것인가?

### 3. 빈 괄호 선언 뒤의 `float` 매개변수 정의 (예측) ★★

```c
/* s34c.c */
double half();                    /* 괄호 안이 비었다 */

double half(float x) { return x / 2; }
```

- ★★ `-std=c17` 에서 두 컴파일러는? gcc 는 **이유를 무엇이라고** 적는가?
- ★★ `-std=c2x` 에서도 결과가 같은가? **이유도** 같은가?

### 4. 선언 없이 부르기 — 판 격자 (예측) ★★★

```c
/* s34d.c */
#include <stdio.h>

int main(void) {
    printf("sq(3) = %d\n", sq(3));  /* 이 줄 위에 sq 의 선언이 없다 */
    return 0;
}

int sq(int x) { return x * x; }
```

- ★★★ **gcc-12 · gcc 13 · clang 18** × **`c89`/`c99`/`c17`/`c2x`** × **`-pedantic`/`-pedantic-errors`** 의 `cc exit` 는?
- ★★ C89 에서 경고가 난다면 그 경고는 **어느 플래그**가 켠 것인가? C89 에서 이 코드는 **합법**인가?
- ★★ clang 의 `-std=c17` 과 `-std=c2x` 진단 문구는 **같은가**?
- ★ 「gcc 14 는 이것을 에러로 올렸다」는 말을 이 환경에서 확인할 수 있는가?

### 5. 두 번역 단위 — 빈 괄호 선언으로 `float` 을 넘기면 (예측) ★★★

```c
/* s34e1.c */
#include <stdio.h>

double half_f();                  /* 괄호 안이 비었다 */
double half_d();

int main(void) {
    float v = 3.0f;
    printf("half_f(v) == 1.5 ? %s\n", half_f(v) == 1.5 ? "yes" : "no");
    printf("half_d(v) == 1.5 ? %s\n", half_d(v) == 1.5 ? "yes" : "no");
    return 0;
}
```

```c
/* s34e2.c */
double half_f(float x)  { return x / 2; }
double half_d(double x) { return x / 2; }
```

```c
/* s34e3.c */
#include <stdio.h>

double half_f(double);            /* 프로토타입을 적었다 — 정의와 다르게 */
double half_d(double);

int main(void) {
    float v = 3.0f;
    printf("half_f(v) == 1.5 ? %s\n", half_f(v) == 1.5 ? "yes" : "no");
    printf("half_d(v) == 1.5 ? %s\n", half_d(v) == 1.5 ? "yes" : "no");
    return 0;
}
```

- ★★★ `s34e1.c + s34e2.c` 를 실행하면 두 줄은 각각 `yes` 인가 `no` 인가? **gcc/clang × `-O0`/`-O2`** 에서 같은가?
- ★★★ 틀린 줄이 있다면 **넘어간 것은 무슨 타입**이고 **받은 쪽은 무슨 타입**인가?
- ★★ `-flto` 를 켜면 `s34e1` 판과 `s34e3` 판에서 **누가 무엇을** 말하는가?
- ★★ ASan·UBSan 은?

### 6. 호출하는 쪽의 어셈블리 (예측) ★★

```c
/* s34f.c */
double take_np();                 /* 괄호 안이 비었다 */
double take_p(float);             /* 프로토타입 */

double via_np(float v) { return take_np(v); }
double via_p(float v)  { return take_p(v); }
```

- ★★ `-O2` 에서 `via_np` 와 `via_p` 의 명령은 어디가 다른가? 두 컴파일러가 같은가?
- ★ `via_np` 에서 **`al`(또는 `eax`)에 값을 넣는 명령**이 있다면 그것은 무엇을 위한 것인가?

### 7. C++ 에서 빈 괄호 (왜) ★★

- ★★ C++17 에서 `int f();` 뒤의 `f(1, 2)` 는? g++ 와 clang++ 의 말투는 어떻게 다른가?
- ★ C23 의 변경을 「**C 를 어느 쪽으로 옮겼다**」고 말할 수 있는가?

### 8. `static` 함수의 순서 · `main` 의 서명 · noreturn 두 꼴 (경계) ★★

- ★★ 정의가 아래 있는 `static` 함수를 위에서 부르면 **무엇과 무엇이 충돌**하는가? 처방은?
- ★★ `void main(void)` 에 두 컴파일러가 다르게 반응한다면, 표준은 그 자리를 **어느 층**에 두었나?
- ★ `[[noreturn]]` 과 `_Noreturn` 은 C17·C23 에서 각각 무슨 진단을 받는가?

### 9. 34 → 36 의 사슬 — 기본 인자 승격이 걸리는 자리 (연결) ★★★

- ★★★ C17 에서 기본 인자 승격이 걸리는 **자리 둘**은? C23 에서는?
- ★★ 6번의 `al` 이 [36번 형제](../36-variadic-functions-stdarg/)와 어떻게 이어지는가?
- ★ 03·04편의 승격 규칙과 **무엇이 같고 무엇이 다른가**?

### 10. 판 경계와 다섯 층 (연결) ★★★

- ★★★ 이 주제의 **판 경계 표**(C89 · C99\~C17 · C23)에 드는 형태를 대면?
- ★★★ 이 편의 **「종료 코드 0인데 ill-formed」** 는 몇 가지이고, 각각 **무엇으로 드러났나**(강도 · 컴파일러 판)?
- ★★ **UB** 칸에 드는 것과 **도구가 침묵한** 자리는?
- ★ 표준은 제약 위반에 **무엇을** 요구하는가? 그것이 「경고냐 에러냐」의 갈림을 어떻게 설명하는가?

### 11. 경계 — 어디까지가 이 주제인가 (연결) ★

- **선언을 읽는 법**과 **링크**는 각각 어느 형제가 정본인가?
- **가변 인자**와 **헤더 배치**는 목록의 몇 번 주제인가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
