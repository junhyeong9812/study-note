# cpp/syntax/04 — `{}` 균일 초기화·좁히기·`initializer_list` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 같은 값을 `()` 로 넣을 때와 `{}` 로 넣을 때
> **무엇이 달라지는지**, 그리고 **어느 변환이 거부되는지**를 맞힐 수 있는지 묻는다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · gcc 13.3.0(C 대비) · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★ **이 주제는 두 컴파일러가 실제로 갈린다.** 3번과 7번이 그 자리다 —
> 「g++ 로 빌드됐다」를 근거로 쓰지 않는 연습이다.
> ★ **좁히기는 표준이 목록으로 정한 규칙**이다. 「컴파일러가 알아서 잡아 준다」가 아니다.
> 선행 — 없음. 형제로 [`01번`](../01-function-overloading-and-overload-resolution/)(오버로드 해석)과
> [`02번`](../02-enum-class-and-scoped-enumerations/)이 붙는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 같은 두 인자를 괄호와 중괄호로 (예측)

```cpp
/* brace01.cpp */
// () 와 {} 가 갈리는 자리 — vector 네 가지
#include <cstdio>
#include <vector>

int main() {
    std::vector<int> a(3, 0);
    std::vector<int> b{3, 0};
    std::vector<int> c(3);
    std::vector<int> d{3};
    std::printf("a(3,0) size=%zu  a[0]=%d\n", a.size(), a[0]);
    std::printf("b{3,0} size=%zu  b[0]=%d b[1]=%d\n", b.size(), b[0], b[1]);
    std::printf("c(3)   size=%zu  c[0]=%d\n", c.size(), c[0]);
    std::printf("d{3}   size=%zu  d[0]=%d\n", d.size(), d[0]);
}
```

- 네 줄의 `size()` 가 각각 무엇인가?
- `b` 의 원소는 무엇인가?
- 갈리는 이유를 **한 문장**으로 댈 수 있는가?
- 원소 타입을 `std::string` 으로 바꾸고 `(3, "ha")` 와 `{3, "ha"}` 를 나란히 놓으면 **여전히 갈리는가**?

### 2. ★★★ 좁히기 아홉 줄 (예측)

```cpp
/* brace03.cpp */
// 좁히기 아홉 줄 — 무엇이 에러이고 무엇이 통과하나
int main() {
    int      a{3.9};      // (1) double -> int, 비상수가 아니라 리터럴
    int      b{3.0};      // (2) double -> int, 상수식이고 값도 정확하다
    char     c{65};       // (3) int -> char, 상수식이고 들어간다
    char     d{300};      // (4) int -> char, 상수식인데 안 들어간다
    int n = 65;
    char     e{n};        // (5) int -> char, 비상수
    double   f{1};        // (6) int -> double, 상수식
    int m = 1;
    double   g{m};        // (7) int -> double, 비상수
    unsigned u{-1};       // (8) 음수 상수 -> unsigned
    long long big = 1;
    double   h{big};      // (9) long long -> double, 비상수
    (void)a; (void)b; (void)c; (void)d; (void)e;
    (void)f; (void)g; (void)u; (void)h;
}
```

- 아홉 줄 중 **에러**는 몇 개이고 **경고**는 몇 개인가?
- (2)는 상수식이고 값도 정확한데 통과하는가?
- (3)과 (4)를 가르는 것은 무엇인가?
- (6)과 (7)을 가르는 것은 무엇인가?
- clang 의 답은 g++ 와 **같은가**?

### 3. ★★★ 비상수 둘만 남기면 (예측)

```cpp
/* brace04.cpp */
// 좁히기 중 「비상수」인 둘만 남긴 판 — g++ 는 이것을 통과시킨다
int main() {
    int n = 65;
    char   e{n};
    int m = 1;
    double g{m};
    (void)e; (void)g;
}
```

- `g++ -std=c++20 -Wall -Wextra -pedantic` 의 **종료 코드**는 무엇인가?
- clang 의 종료 코드는?
- 표준이 정한 답은 **어느 쪽**인가?
- g++ 에서 표준 쪽 답을 받으려면 **어떤 플래그**를 주어야 하는가 — `-pedantic` 으로 되는가?

### 4. ★★ `initializer_list` 가 언제 이기나 (예측)

```cpp
/* brace05.cpp */
// initializer_list 가 다른 생성자를 이기는 것 — 그리고 빈 {} 는 안 이긴다
#include <cstdio>
#include <initializer_list>

struct W {
    W()                             { std::printf("W()\n"); }
    W(int, int)                     { std::printf("W(int,int)\n"); }
    W(std::initializer_list<int> l) { std::printf("W(init_list) size=%zu\n", l.size()); }
};

int main() {
    W a(1, 2);      // ① 괄호 — 생성자 오버로드 해석
    W b{1, 2};      // ② 중괄호 — initializer_list 가 먼저다
    W c{};          // ③ 빈 중괄호 — 기본 생성자다
    W d({});        // ④ 빈 중괄호를 「인자로」 넘기면
    W e{1, 2, 3};   // ⑤ 셋이면 (int,int) 는 후보도 아니다
    (void)a; (void)b; (void)c; (void)d; (void)e;
}
```

- 다섯 줄이 각각 어느 생성자를 부르는가?
- ③과 ④의 차이는 무엇인가?
- 생성자를 `W(double, double)` 과 `initializer_list<int>` 둘로 바꾸고 `W g{1.0, 2.0};` 를 쓰면 무엇이 나오는가?
- 그 결과가 **왜 「이겼다」의 증거**인가?

### 5. ★★ `T t();` 는 무엇을 선언하나 (예측)

```cpp
/* brace07.cpp */
// 가장 성가신 파싱 — T t(); 는 변수가 아니다
#include <cstdio>

struct T {
    int v = 7;
    T() { std::printf("T()\n"); }
};

int main() {
    T t();
    std::printf("t.v = %d\n", t.v);
}
```

- 컴파일되는가? 되지 않으면 **에러 문구**가 무엇을 말하는가?
- 경고 이름은 무엇인가 — g++ 와 clang 이 같은가?
- g++ 가 제안하는 고침이 **둘**인데 각각 무엇인가?
- 이 함정이 **`{}` 를 쓰면 사라지는** 이유는?

### 6. ★ `auto x{1}` 과 `auto x = {1}` (예측)

```cpp
/* brace08.cpp */
// auto x{1} 대 auto x = {1} — 타입을 의도적 타입 에러로 찍는다
#include <initializer_list>

template <class T> struct TypeOf;   // 선언만 — 정의가 없다

int main() {
    auto a{1};
    auto b = {1};
    auto c = {1, 2};
    TypeOf<decltype(a)> ta;
    TypeOf<decltype(b)> tb;
    TypeOf<decltype(c)> tc;
}
```

- 세 변수의 타입이 각각 무엇인가?
- 그것을 **어떻게 알아냈는가** — `TypeOf` 가 왜 필요한가?
- `auto c{1, 2};` 는 어떻게 되는가?
- 이 규칙은 **언제부터**인가?

### 7. 집합체 초기화와 지정 초기자 (경계)

```cpp
/* brace11.cpp */
// C 에서 되고 C++ 에서 안 되는 지정 초기자 셋
struct P { int x; int y; int z; };

int main() {
    P a{.z = 3, .x = 1};       // ① 선언 순서를 어긴다
    P b{.x = 1, 2};            // ② 지정과 위치를 섞는다
    int arr[3] = {[1] = 5};    // ③ 배열 지정 초기자
    (void)a; (void)b; (void)arr;
}
```

- 이 셋이 C++20 에서 각각 **되는가 안 되는가**?
- g++ 와 clang 의 답이 **같은가** — 종료 코드까지?
- 같은 셋을 **C 로** 던지면 어떻게 되는가?
- C++ 가 C 에서 **일부러 뺀 것**은 무엇이고 왜인가?

### 8. ★★ C++20 의 괄호 집합체 초기화 (경계)

- `struct P { int x; int y; int z; };` 에 `P b(1, 2.9, 3);` 를 쓰면 C++20 에서 되는가?
- `y` 에 무엇이 들어가는가 — 진단은 **몇 건**인가?
- 같은 값을 `P b{1, 2.9, 3};` 로 쓰면?
- `-std=c++17` 로 던지면 무엇이 나오는가?
- 이 둘의 차이를 「**`{}` 를 기본으로 쓰라**」는 조언과 어떻게 잇는가?

### 9. `{}` 가 「0 으로 채워라」가 되는 자리 (왜)

- `int i{};` · `int* p{};` · `double d{};` · `A s{};`(집합체) 가 각각 무엇이 되는가?
- 그 동작에 붙은 이름은 무엇인가?
- 집합체에서 **빠뜨린 멤버**는 어떻게 되는가 — `-Wextra` 가 무엇을 말하는가?
- `A t;`(중괄호 없이)와 무엇이 다른가?

### 10. 다른 주제와 잇기 (연결)

- `{}` 가 **오버로드 해석**을 바꾸는 규칙의 정본은 형제 주제 몇 번인가?
- 좁히기 판정에 쓰이는 「정수 승격」의 정본은 **어느 갈래 어느 주제**인가?
- 구조체 집합체 초기화·지정 초기자(C99)의 정본은 **어느 갈래 어느 주제**인가?
- `auto x = {1}` 이 `initializer_list` 가 되는 규칙은 형제 주제 몇 번이 더 판다?
- `std::vector<int> v{3, 0}` 의 함정을 **타입으로** 막는 도구는 목록의 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
