# cpp/syntax/13 — 생성자·멤버 초기화 리스트·위임 생성자 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **세어서 답하는 것**이 절반이다 — 「어느 쪽이 나은가」를 **의견으로 답하지 마라.**
> **생성자·대입 호출 횟수**를 숫자로 맞혀야 한다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★ **네 번째 창은 「경고를 플래그·컴파일러별로 센 개수」다**(8번). 같은 사건에 개수가 다르다.
> ★ **「부적용인 창」이 있다** — `sizeof`. 초기화 방식이 달라도 객체 크기는 같아 **잴 것이 없다**.
> 선행 — [12번](../12-class-basics-members-access-and-this/)(클래스 기본)과 형제 [`04번`](../04-brace-initialization-narrowing-and-initializer-list/)·[`09번`](../09-rvalue-references-move-and-forward/)·[`11번`](../11-choosing-parameter-passing/)이 이 주제의 바로 앞이다.
> 이어지는 것 — [14번](../14-destructors-and-deterministic-destruction/)이 **그 역순**을, [15번](../15-raii-resources-as-types/)이 **그 시점의 쓸모**를 답한다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 다섯 가지로 멤버를 채우면 몇 번씩 도나 (예측)

```cpp
/* ctor01.cpp */
#include <cstdio>
#include <utility>

static int dc = 0, cc = 0, mc = 0, ca = 0, ma = 0;

struct Probe {
    int id;
    Probe() : id(0) { ++dc; }                                        // 기본 생성
    explicit Probe(int i) : id(i) {}                                 // 계수하지 않는다(원본용)
    Probe(const Probe& o) : id(o.id) { ++cc; }                       // 복사 생성
    Probe(Probe&& o) noexcept : id(o.id) { ++mc; }                   // 이동 생성
    Probe& operator=(const Probe& o) { id = o.id; ++ca; return *this; }   // 복사 대입
    Probe& operator=(Probe&& o) noexcept { id = o.id; ++ma; return *this; } // 이동 대입
};

struct ByList { Probe m; explicit ByList(const Probe& p) : m(p) {} };
struct ByBody { Probe m; explicit ByBody(const Probe& p) { m = p; } };
struct SinkList { Probe m; explicit SinkList(Probe p) : m(std::move(p)) {} };
struct SinkBody { Probe m; explicit SinkBody(Probe p) { m = std::move(p); } };
struct DefaultOnly { Probe m; DefaultOnly() = default; };

#define RUN(label, decl) do { dc = cc = mc = ca = ma = 0; { decl; } \
    std::printf("  %-22s 기본 %d · 복사 %d · 이동 %d · 복사대입 %d · 이동대입 %d\n", \
                label, dc, cc, mc, ca, ma); } while (0)

int main() {
    Probe src(7);
    std::puts("[A] lvalue 하나를 멤버로 들인다");
    RUN("list  m(p)", ByList x(src); (void)x);
    RUN("body  m = p", ByBody x(src); (void)x);
    std::puts("[B] 값으로 받아 옮긴다");
    RUN("list  m(std::move(p))", SinkList x{Probe(src)}; (void)x);
    RUN("body  m = std::move(p)", SinkBody x{Probe(src)}; (void)x);
    std::puts("[C] 아무것도 안 적으면");
    RUN("= default", DefaultOnly x; (void)x);
}
```

- 다섯 줄의 **기본·복사·이동·복사대입·이동대입** 횟수를 전부 맞힐 수 있는가?
- ★ `list m(p)` 와 `body m = p` 의 **합계 차이**는 몇이고, **무엇이 더 도는가**?
- ★ 값으로 받아 옮기는 두 줄에서는 차이가 **어떻게 달라지는가**?
- ★ `= default` 줄이 **0 이 아닌** 이유는?

### 2. ★★★ 리스트에 b, a 순으로 적으면 (예측)

```cpp
/* ctor02.cpp */
// 멤버는 리스트에 적은 순서가 아니라 선언 순서로 초기화된다
#include <cstdio>

struct Log {
    const char* tag;
    explicit Log(const char* t) : tag(t) { std::printf("    [생성] %s\n", tag); }
    ~Log() { std::printf("    [파괴] %s\n", tag); }
};

struct Order {
    Log a{"a — 먼저 선언"};
    Log b{"b — 나중 선언"};
    Order() : b("b — 리스트에 먼저 적음"), a("a — 리스트에 나중 적음") {}
};

int main() {
    std::printf("  리스트에는 b, a 순으로 적었다\n");
    { Order o; (void)o; }
}
```

- **생성 로그 두 줄**의 순서를 맞힐 수 있는가 — 그리고 **파괴 두 줄**은?
- ★ 무엇이 그 순서를 정하는가?
- ★★ g++ 와 clang 의 **경고 개수**는 각각 몇 건인가 — 왜 다른가?
- 경고 이름은 각각 무엇인가?

### 3. ★★ 한 멤버를 다른 멤버로 초기화하면 (예측)

```cpp
/* ctor03.cpp */
// 선언 순서를 거스르면 무엇을 읽게 되나 — 값이 아니라 약속이 깨진 것을 본다
#include <cstdio>

struct Trap {
    int n;                                  // 먼저 선언
    int m;                                  // 나중 선언
    explicit Trap(int k) : m(k), n(m * 2) {}   // n 을 m 으로 초기화한다
};

int main() {
    Trap t(10);
    std::printf("  m == 10 인가        : %d\n", (int)(t.m == 10));
    std::printf("  약속대로 n == m*2 인가: %d\n", (int)(t.n == t.m * 2));
    std::printf("  (n 의 값 자체는 미정이라 싣지 않는다)\n");
}
```

- 출력 두 줄의 **0/1** 을 맞힐 수 있는가?
- ★ 이 문서가 **`n` 의 값 자체를 싣지 않는 이유**는 무엇인가?
- ★ `-O0` 과 `-O2` 에서 **같았던 것**과 **달랐던 것**은 각각 무엇인가?
- ★ 이 함정의 **경고 지문**(어느 둘이 함께 나오나)은?

### 4. ★★ 위임 생성자 뒤 본문에서 던지면 (예측)

```cpp
/* ctor05.cpp */
// 위임 생성자 — 누가 먼저 돌고, 예외가 나면 소멸자가 도나
#include <cstdio>
#include <stdexcept>

struct Widget {
    int w, h;
    const char* how;
    Widget(int a, int b, const char* tag) : w(a), h(b), how(tag) {
        std::printf("    [본체 생성자] %dx%d (%s)\n", w, h, how);
    }
    Widget() : Widget(1, 1, "위임받은 기본값") {                 // 다른 생성자에 위임한다
        std::printf("    [위임 생성자 본문] 여기는 본체 뒤다\n");
    }
    explicit Widget(int side) : Widget(side, side, "정사각형") {
        std::printf("    [위임 생성자 본문] side=%d\n", side);
        if (side > 100) throw std::runtime_error("너무 크다");
    }
    ~Widget() { std::printf("    [소멸자] %dx%d (%s)\n", w, h, how); }
};

int main() {
    std::printf("(1) 기본 생성자가 본체에 위임하면\n");
    { Widget a; }
    std::printf("(2) 위임 뒤 본문에서 던지면 — 소멸자가 도나\n");
    try { Widget big(200); (void)big; }
    catch (const std::exception& e) { std::printf("    [catch] %s\n", e.what()); }
}
```

- `(1)` 의 로그 **세 줄 순서**를 맞힐 수 있는가?
- ★★ `(2)` 에서 **소멸자가 도는가**? 그 근거를 한 문장으로 말할 수 있는가?
- ★ 그 답은 [15번](../15-raii-resources-as-types/)의 「생성자에서 던지면 소멸자가 안 돈다」와 **모순인가**?

### 5. ★ 기본 멤버 초기자와 리스트가 겹치면 (예측)

```cpp
/* ctor06.cpp */
// 기본 멤버 초기자와 초기화 리스트가 겹치면 누가 이기나
#include <cstdio>

struct Count {
    int v;
    explicit Count(int x) : v(x) { std::printf("    Count(%d)\n", x); }
};

struct Conf {
    int n = 1;                 // 기본 멤버 초기자
    Count c{100};              // 기본 멤버 초기자 — 생성자 호출이 찍힌다
    int untouched = 42;
    Conf() {}                                  // 리스트가 비었다
    explicit Conf(int x) : n(x), c(x) {}       // 리스트가 둘 다 덮어쓴다
};

int main() {
    std::printf("(1) 리스트가 비면 기본 멤버 초기자가 쓰인다\n");
    { Conf a; std::printf("    n=%d c.v=%d untouched=%d\n", a.n, a.c.v, a.untouched); }
    std::printf("(2) 리스트가 적으면 리스트가 이긴다\n");
    { Conf b(7); std::printf("    n=%d c.v=%d untouched=%d\n", b.n, b.c.v, b.untouched); }
}
```

- `(1)` 과 `(2)` 에서 **`Count(...)` 이 각각 몇 번, 어떤 값으로** 찍히는가?
- ★ 리스트에 적힌 멤버의 기본 멤버 초기자는 **평가되는가**?
- `untouched` 는 두 판에서 각각 얼마인가?

### 6. ★★ `const` 멤버와 참조 멤버를 본문에서 대입하면 (경계)

- **에러는 몇 개**이며 각각 무엇을 짚는가?
- ★ 본문에서 대입을 **지워도** 남는 에러가 있는가 — 왜인가?
- ★ 그 이유를 「**본문이 시작될 때 멤버는 어떤 상태인가**」로 말할 수 있는가?
- `const` 멤버를 두면 **자동으로 사라지는 특수 멤버**는 무엇인가?

### 7. ★★★ 다섯 클래스를 옮기면 무엇이 도나 (예측)

```cpp
/* ctor09.cpp */
// 컴파일러가 이동 생성자를 언제 안 만드나 — 옮겼는데 복사가 돌면 안 만든 것이다
#include <cstdio>
#include <utility>

static int cp = 0, mv = 0;
struct Tracer {
    Tracer() = default;
    Tracer(const Tracer&) { ++cp; }
    Tracer(Tracer&&) noexcept { ++mv; }
    Tracer& operator=(const Tracer&) { ++cp; return *this; }
    Tracer& operator=(Tracer&&) noexcept { ++mv; return *this; }
};

struct Plain      { Tracer t; };
struct HasDtor    { Tracer t; ~HasDtor() {} };
struct HasCopy    { Tracer t; HasCopy() = default; HasCopy(const HasCopy& o) : t(o.t) {} };
struct HasCopyAsn { Tracer t; HasCopyAsn& operator=(const HasCopyAsn&) { return *this; } };
struct Defaulted  { Tracer t; ~Defaulted() = default;
                    Defaulted() = default;
                    Defaulted(Defaulted&&) noexcept = default;
                    Defaulted(const Defaulted&) = default; };

#define MOVE_TEST(T) do { cp = mv = 0; { T a; T b = std::move(a); (void)b; } \
    std::printf("  %-12s 를 옮기면  복사 %d · 이동 %d  -> %s\n", #T, cp, mv, \
                mv ? "이동 생성자가 있다" : "이동이 없어 복사로 갔다"); } while (0)

int main() {
    MOVE_TEST(Plain);
    MOVE_TEST(HasDtor);
    MOVE_TEST(HasCopy);
    MOVE_TEST(HasCopyAsn);
    MOVE_TEST(Defaulted);
}
```

- 다섯 줄의 **복사·이동 횟수**를 맞힐 수 있는가?
- ★★ `std::is_move_constructible_v` 로 이 질문에 답할 수 **없는** 이유는?
- ★ **소멸자 하나만** 적었는데 결과가 달라지는 이유는?
- ★ 경고가 **하나 나온 줄**은 어느 클래스이고 무슨 경고인가?

### 8. ★★★ `-fpermissive` 를 주면 (경계)

- 기본 플래그에서 **에러**였던 둘이 `-fpermissive` 에서 무엇이 되는가 — **`cc exit`** 은?
- ★★ **`-pedantic-errors` 를 함께 주면 살아나는가**?
- ★ clang 에 같은 파일을 주면 어떻게 되는가?
- ★ 그래서 「우리 빌드는 통과한다」가 **무엇을 증명하지 못하는가**?

### 9. 경고를 누가 보나 (경계)

- 「두 번 손댄다」((1))를 경고하는 컴파일러가 있는가?
- ★ `explicit` 을 빠뜨린 설계를 지적하는 도구가 있는가?
- ★★ 같은 UB 를 **초기화 리스트**에서 쓸 때와 **기본 멤버 초기자**에서 쓸 때, g++ 의 반응이 어떻게 다른가?

### 10. 다른 주제와 잇기 (연결)

- 「이름은 찾아지는데 값이 없다」의 짝이 되는 문항은 **몇 번 주제의 몇 절**인가?
- **파괴 순서**의 정본은 몇 번인가?
- `Probe` 로 **호출 횟수를 세는 방식**은 형제 몇 번에서 왔는가?
- **0/3/5의 법칙**의 정본은 몇 번인가?
- ★ 러스트에 **「초기화 순서」 함정이 없는 이유**는 무엇이며, 어느 갈래 어느 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
