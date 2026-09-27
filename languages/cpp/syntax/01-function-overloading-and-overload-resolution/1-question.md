# cpp/syntax/01 — 함수 오버로딩과 오버로드 해석 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 문법을 아는지가 아니라 **컴파일러가 어느 오버로드를 고르는지**,
> 못 고를 때 **어느 문구로 거부하는지**를 맞힐 수 있는지 묻는다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · x86-64 Linux. 기본 명령은
> `g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex`.
> ★ 답을 모르겠으면 **던져 보라.** 이 주제는 **컴파일만 해도 절반이 나온다.**
> ★★ **이 주제에는 UB 가 없다.** sanitizer 가 할 일이 없고, **경고도 한 건도 안 난다** —
> 실패는 전부 `cc exit=1` 인 **에러**다. 그래서 「경고 0건」이 아무 뜻도 없는 주제다.
> 선행 — C 갈래의 [`03-integer-promotion-and-usual-arithmetic-conversions/`](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/)(정수 승격).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 후보를 둘씩 둔 네 묶음에 같은 인자를 던지면 (예측)

```cpp
/* ex.cpp */
// 오버로드 해석의 네 단계를 각각 고립시킨다 — 뽑힌 후보가 자기 이름을 찍는다
#include <cstdio>
#define WHO std::puts(__PRETTY_FUNCTION__)

struct S { S(int) {} };                  // int 를 받는 변환 생성자

namespace step1 { void f(char)   { WHO; } void f(int)    { WHO; } }
namespace step2 { void f(int)    { WHO; } void f(double) { WHO; } }
namespace step3 { void f(double) { WHO; } void f(S)      { WHO; } }
namespace step4 { void f(S)      { WHO; } }

int main() {
    char c = 'a';
    std::puts("(1) 정확 일치 대 승격");         step1::f(c);
    std::puts("(2) 승격 대 표준 변환");          step2::f(c);
    std::puts("(3) 표준 변환 대 사용자 정의");    step3::f(1);
    std::puts("(4) 사용자 정의 변환뿐일 때");     step4::f(1);
}
```

- 네 줄이 각각 어느 후보를 부르는가?
- `step2::f(c)` 에서 `char` 는 `int` 로도 `double` 로도 갈 수 있다. 왜 한쪽이 이기는가?
- `step3::f(1)` 에서 `S` 는 `int` 하나로 만들 수 있다. 그런데 왜 그쪽이 아닌가?
- 이 네 줄이 보여 주는 「계단」의 이름을 좋은 순서대로 넷 댈 수 있는가?
- `__PRETTY_FUNCTION__` 은 표준인가?

### 2. ★★ 파생 클래스에 같은 이름이 하나 있을 때 (예측)

```cpp
/* ex.cpp */
// 1단계는 이름 탐색이다 — 한 스코프에서 이름을 찾으면 거기서 멈춘다
#include <cstdio>
#define WHO std::puts(__PRETTY_FUNCTION__)

struct Base {
    void f(int)    { WHO; }
    void f(double) { WHO; }
};

struct Derived : Base {
    void f(const char*) { WHO; }   // 이름이 같으면 기반의 f 가 후보 집합에 안 들어온다
};

int main() {
    Derived d;
    d.f("hi");
    d.f(1);
}
```

- 두 호출 중 어느 것이 막히는가? 에러인가 경고인가?
- 막힌 쪽의 진단은 **어느 함수를 짚는가** — 기반의 것인가 파생의 것인가?
- 그 사실이 오버로드 해석의 **몇 단계**에 대해 무엇을 말하는가?
- 한 줄을 더해 고칠 수 있는가? 고친 뒤 세 호출은 각각 어디로 가는가?
- g++ 와 clang 의 진단 문구가 같은가?

### 3. ★★ 같은 후보 넷에 `unsigned int` 를 던지면 (예측)

```cpp
/* ex.cpp */
// 3단계 — 실행 가능 후보가 넷인데 순위가 같다. 네 개가 전부 나열된다
void pick(char);
void pick(int);
void pick(long);
void pick(double);

int main() {
    unsigned u = 1u;
    pick(u);
}
```

- 컴파일되는가? 안 되면 에러의 첫 줄을 적을 수 있는가?
- 진단에 후보가 **몇 개** 나열되는가? 왜 그 개수인가?
- g++ 가 인자 타입을 무엇이라고 적는가 — 소스에 쓴 그대로인가?
- clang 의 출력에는 있고 g++ 에는 없는 **마지막 줄**이 무엇인가?
- 고치는 방법을 셋 댈 수 있는가?

### 4. ★★ `const` 가 붙은 세 자리 (예측)

```cpp
/* ex.cpp */
// const 가 오버로드를 가르는 자리와 못 가르는 자리
#include <cstdio>
#define WHO std::puts(__PRETTY_FUNCTION__)

struct Box {
    int v = 0;
    int&       at()       { WHO; return v; }
    const int& at() const { WHO; return v; }
};

void g(int&)       { WHO; }
void g(const int&) { WHO; }

int main() {
    Box b; const Box cb;
    b.at();
    cb.at();

    int x = 1; const int cx = 1;
    g(x);
    g(cx);
    g(42);
}
```

- 다섯 호출이 각각 어느 함수로 가는가?
- `cb.at()` 에서 비const 판이 **왜 후보에서 떨어지는가** — 인자가 없는데 무엇을 보고 떨어뜨리는가?
- `g(42)` 가 `void g(int&)` 로 못 가는 이유는 무엇인가?
- `void h(int)` 와 `void h(const int)` 를 **둘 다 정의**하면 어떻게 되는가?

### 5. ★ 기본 인자를 붙인 오버로드 (예측)

```cpp
/* ex.cpp */
// 기본 인자와 오버로드가 부딪히면 — 선언 자리에서는 안 걸리고 호출 자리에서 걸린다
#include <cstdio>
#define WHO std::puts(__PRETTY_FUNCTION__)

void f(int a, int b = 0) { WHO; (void)a; (void)b; }
void f(int a)            { WHO; (void)a; }

int main() { f(1); }
```

- 컴파일되는가? 안 되면 **어느 줄**에서 걸리는가 — 선언 줄인가 호출 줄인가?
- 두 함수의 **선언 자체**는 합법인가?
- 이 사고가 라이브러리 저자에게 뜻하는 것이 무엇인가?

### 6. ★★ 정의를 두지 않고 선언만 둔 뒤 오브젝트 파일을 보면 (예측)

```cpp
/* ex.cpp */
// 정의를 두지 않는다 — 오브젝트 파일의 미정의 심볼이 「무엇을 불렀나」를 이름으로 말한다
void pick(char);
void pick(int);
void pick(long);
void pick(double);

int main() {
    char  c = 'a';
    short s = 1;
    float f = 1.0f;
    pick(c);
    pick(s);
    pick(f);
}
```

- `g++ -c ex.cpp -o ex.o` 가 통과하는가?
- `nm -uC ex.o` 에 **몇 개**의 이름이 나오는가? 선언은 넷인데 왜 그 개수인가?
- 나오지 않는 하나는 무엇이고, 그것이 무슨 뜻인가?
- `nm -u`(풀지 않은 것)의 `_Z4pickc` 에서 꼬리 글자가 뜻하는 것은?
- 그 철자는 표준이 정하는가?

### 7. 반환 타입은 왜 오버로드를 못 가르나 (왜)

- `int f(int)` 와 `long f(int)` 를 같이 두면 컴파일러가 뭐라고 하는가 — g++ 와 clang 각각?
- **한 줄짜리 호출** 하나를 들어 「그래서 안 된다」를 설명할 수 있는가?
- 이 규칙이 「해석은 무엇만 보고 하는가」에 대해 말하는 것은?

### 8. 최상위 `const` 와 `const` 참조의 경계 (경계)

- `void h(int)` / `void h(const int)` 와 `void g(int&)` / `void g(const int&)` — 어느 쪽이 오버로드가 되는가?
- 안 되는 쪽은 **왜** 안 되는가(호출 쪽에서 무엇이 같은가)?
- 멤버 함수 뒤에 붙는 `const` 는 어느 쪽에 가까운가?

### 9. 두 컴파일러의 진단이 갈리는 자리 (경계)

- 「실행 가능 후보가 하나도 없다」일 때 clang 과 g++ 중 어느 쪽이 정보가 많은가? 구체적으로 무엇이 더 나오는가?
- 「모호하다」일 때는 어떤가 — 그때도 갈리는가?
- 이 문서가 **두 컴파일러에 다 던진 이유**를 한 줄로 말할 수 있는가?

### 10. 산술 타입 일곱이 각각 어디로 가나 (경계)

- 후보가 `f(char)`·`f(int)`·`f(long)`·`f(double)` 넷일 때 `char`·`signed char`·`unsigned char`·`short`·`bool`·`int`·`float` 는 각각 어디로 가는가?
- 그중 **정확 일치**는 몇 개인가?
- `f(long)` 이 뽑히게 하려면 무엇을 넘겨야 하는가?
- `float` 가 `f(long)` 이 아니라 `f(double)` 로 가는 이유에 붙은 이름은?

### 11. 다른 주제와 잇기 (연결)

- 이 주제의 선택은 **언제** 일어나는가 — 그리고 **실행 시간**에 일어나는 선택은 목록의 몇 번인가?
- 「정수 승격」 규칙 자체의 정본은 어느 갈래 어느 주제인가?
- 「이름이 어느 네임스페이스에서 찾아지나」는 목록의 몇 번인가?
- `enum class` 가 이 주제의 **후보 집합**에 하는 일은 무엇인가 — 형제 주제 몇 번인가?
- `{}` 로 생성자를 부를 때 붙는 **특칙**은 형제 주제 몇 번에 있는가?
- 이 주제에서 sanitizer 를 한 번도 안 쓴 이유는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
