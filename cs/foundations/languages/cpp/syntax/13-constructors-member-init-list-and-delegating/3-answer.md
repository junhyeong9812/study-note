# cpp/syntax/13 — 생성자·멤버 초기화 리스트·위임 생성자 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이므로 **출력을 싣는 블록마다 그 출력을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — **진단 문구**와 **초기화되지 않은 멤버의 값**은 흔들리는 칸이다.\
> 근거로 쓰는 것은 **호출 횟수 · 로그 순서 · 에러냐 경고냐 · `cc exit` · 경고 개수**다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「몇 배 빠르다」는 문장이 **한 줄도 없다**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 리스트는 **한 번**, 본문은 **두 번** — 값 싱크에서는 2 대 3

**출력**

```text
===== 소스: ctor01.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -pedantic ctor01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[A] lvalue 하나를 멤버로 들인다
  list  m(p)             기본 0 · 복사 1 · 이동 0 · 복사대입 0 · 이동대입 0
  body  m = p            기본 1 · 복사 0 · 이동 0 · 복사대입 1 · 이동대입 0
[B] 값으로 받아 옮긴다
  list  m(std::move(p))  기본 0 · 복사 1 · 이동 1 · 복사대입 0 · 이동대입 0
  body  m = std::move(p) 기본 1 · 복사 1 · 이동 0 · 복사대입 0 · 이동대입 1
[C] 아무것도 안 적으면
  = default              기본 1 · 복사 0 · 이동 0 · 복사대입 0 · 이동대입 0
```

**왜 그런가**

| 쓴 방식 | 기본 | 복사 | 이동 | 복사대입 | 이동대입 | 합 |
|---|---|---|---|---|---|---|
| `: m(p)` | 0 | **1** | 0 | 0 | 0 | ★ **1** |
| `{ m = p; }` | ★★ **1** | 0 | 0 | **1** | 0 | ★★ **2** |
| `: m(std::move(p))` | 0 | 1 | 1 | 0 | 0 | 2 |
| `{ m = std::move(p); }` | ★★ **1** | 1 | 0 | 0 | 1 | ★★ **3** |
| `= default` | **1** | 0 | 0 | 0 | 0 | 1 |

- ★★★ **본문이 더 내는 것은 정확히 「기본 생성 1회」다.** 본문이 시작될 때 **멤버는 이미 지어져 있기** 때문에,\
  본문의 `m = p;` 는 **이미 있는 것을 덮어쓰는 것**이다.
- ★★ **값으로 받는 두 줄에서 복사 1회는 둘이 같다** — 그것은 **매개변수를 만드는 복사**이지 멤버 초기화가 아니다.\
  갈리는 것은 여기서도 **기본 생성 1회**뿐이다(2 대 3).
- ★ **`= default` 가 1 인 이유** — 멤버 `Probe` 에 기본 생성자가 있고, **그것이 돈다.**\
  「아무것도 안 적었다」가 「아무 일도 안 한다」는 뜻이 아니다.
- ★ **이 표에 시간은 없다.** `Probe` 는 `int` 하나라 **횟수 차이가 곧 비용 차이라고 말할 수 없다.**

### 2. ★★★ `a` 가 먼저, `b` 가 나중 — **선언 순서**가 이긴다

**출력**

```text
===== 소스: ctor02.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -pedantic ctor02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
ctor02.cpp: In constructor ‘Order::Order()’:
ctor02.cpp:12:9: warning: ‘Order::b’ will be initialized after [-Wreorder]
   12 |     Log b{"b — 나중 선언"};
      |         ^
ctor02.cpp:11:9: warning:   ‘Log Order::a’ [-Wreorder]
   11 |     Log a{"a — 먼저 선언"};
      |         ^
ctor02.cpp:13:5: warning:   when initialized here [-Wreorder]
   13 |     Order() : b("b — 리스트에 먼저 적음"), a("a — 리스트에 나중 적음") {}
      |     ^~~~~
  리스트에는 b, a 순으로 적었다
    [생성] a — 리스트에 나중 적음
    [생성] b — 리스트에 먼저 적음
    [파괴] b — 리스트에 먼저 적음
    [파괴] a — 리스트에 나중 적음
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic ctor02.cpp -o ex (cc exit=0) =====
ctor02.cpp:13:15: warning: field 'b' will be initialized after field 'a' [-Wreorder-ctor]
   13 |     Order() : b("b — 리스트에 먼저 적음"), a("a — 리스트에 나중 적음") {}
      |               ^~~~~~~~~~~~~~~~~~~~~~~~~~~  ~~~~~~~~~~~~~~~~~~~~~~~~~~~
      |               a("a — 리스트에 나중 적음")  b("b — 리스트에 먼저 적음")
1 warning generated.
```

**왜 그런가**

- ★★★ **생성은 `a` → `b`, 파괴는 `b` → `a`** 다. 리스트에 `b, a` 로 적은 것은 **아무 영향이 없다.**
- ★★★ **선언 순서로 정한 이유**는 **파괴 순서를 결정적으로 만들기 위해서**다.\
  생성자마다 리스트 순서가 다르면 **어느 순서로 파괴해야 할지 정할 수 없다** — 그 결론은 [14번](../14-destructors-and-deterministic-destruction/)에서 다시 쓰인다.
- ★★ **경고 개수는 g++ 3건 · clang 1건**이다.\
  g++ 는 한 사건을 **세 줄로 쪼개** 말하고(「`b` 가 나중」 · 「`a` 다」 · 「여기서 초기화했다」),\
  clang 은 **한 줄로 말하고 캐럿 아래에 고칠 순서를 그려** 준다.
- ★ 경고 이름도 다르다 — g++ **`-Wreorder`** · clang **`-Wreorder-ctor`**.
- ★★ **그래서 「경고 N건」은 컴파일러를 밝히지 않으면 뜻이 없다.**

### 3. ★★ `m == 10` 은 **1**, `n == m*2` 는 **0** — 약속이 깨진다

**출력**

```text
===== 소스: ctor03.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -pedantic ctor03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
ctor03.cpp: In constructor ‘Trap::Trap(int)’:
ctor03.cpp:6:9: warning: ‘Trap::m’ will be initialized after [-Wreorder]
    6 |     int m;                                  // 나중 선언
      |         ^
ctor03.cpp:5:9: warning:   ‘int Trap::n’ [-Wreorder]
    5 |     int n;                                  // 먼저 선언
      |         ^
ctor03.cpp:7:14: warning:   when initialized here [-Wreorder]
    7 |     explicit Trap(int k) : m(k), n(m * 2) {}   // n 을 m 으로 초기화한다
      |              ^~~~
ctor03.cpp:7:36: warning: member ‘Trap::m’ is used uninitialized [-Wuninitialized]
    7 |     explicit Trap(int k) : m(k), n(m * 2) {}   // n 을 m 으로 초기화한다
      |                                    ^
ctor03.cpp: In constructor ‘Trap::Trap(int)’:
ctor03.cpp:7:36: warning: ‘*this.Trap::m’ is used uninitialized [-Wuninitialized]
    7 |     explicit Trap(int k) : m(k), n(m * 2) {}   // n 을 m 으로 초기화한다
      |                                    ^
  m == 10 인가        : 1
  약속대로 n == m*2 인가: 0
  (n 의 값 자체는 미정이라 싣지 않는다)
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 ctor03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
ctor03.cpp: In constructor ‘Trap::Trap(int)’:
ctor03.cpp:6:9: warning: ‘Trap::m’ will be initialized after [-Wreorder]
    6 |     int m;                                  // 나중 선언
      |         ^
ctor03.cpp:5:9: warning:   ‘int Trap::n’ [-Wreorder]
    5 |     int n;                                  // 먼저 선언
      |         ^
ctor03.cpp:7:14: warning:   when initialized here [-Wreorder]
    7 |     explicit Trap(int k) : m(k), n(m * 2) {}   // n 을 m 으로 초기화한다
      |              ^~~~
ctor03.cpp:7:36: warning: member ‘Trap::m’ is used uninitialized [-Wuninitialized]
    7 |     explicit Trap(int k) : m(k), n(m * 2) {}   // n 을 m 으로 초기화한다
      |                                    ^
ctor03.cpp: In constructor ‘Trap::Trap(int)’:
ctor03.cpp:7:36: warning: ‘*this.Trap::m’ is used uninitialized [-Wuninitialized]
    7 |     explicit Trap(int k) : m(k), n(m * 2) {}   // n 을 m 으로 초기화한다
      |                                    ^
  m == 10 인가        : 1
  약속대로 n == m*2 인가: 0
  (n 의 값 자체는 미정이라 싣지 않는다)
```

**왜 그런가**

- ★★★ **`n` 이 먼저 선언됐으므로 `n(m * 2)` 가 먼저 돈다.** 그 시점에 `m` 은 **아직 초기화 전**이다.\
  그래서 `n` 은 **미정 값**을 갖고, `n == m*2` 가 **0** 이 된다.
- ★★★ **`n` 의 값 자체를 싣지 않는 이유** — **미정이라 흔들린다.**\
  이 문서가 실을 수 있는 것은 「**약속이 깨졌다**」는 비교 결과이고, 그 결과는 **`-O0` 과 `-O2` 에서 똑같이 0**이었다.\
  ★ **같았던 것은 비교 결과, 달랐던 것은 값** — 그래서 **값이 아니라 결과를 싣는다.**
- ★★ **이 함정의 지문은 `-Wreorder` 와 `-Wuninitialized` 가 함께 나오는 것**이다.\
  `-Wreorder` 만 나오면 스타일 문제일 수 있지만, **둘이 함께 나오면 실제 버그**다.
- ★ 같은 UB 를 **기본 멤버 초기자**에서 쓰면 **g++ 는 침묵한다** — [12번](../12-class-basics-members-access-and-this/) (6)이 그 자리다.

### 4. ★★ 본체 → 위임 본문 순서 · 던지면 **소멸자가 돈다**

**출력**

```text
===== 소스: ctor05.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -pedantic ctor05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 기본 생성자가 본체에 위임하면
    [본체 생성자] 1x1 (위임받은 기본값)
    [위임 생성자 본문] 여기는 본체 뒤다
    [소멸자] 1x1 (위임받은 기본값)
(2) 위임 뒤 본문에서 던지면 — 소멸자가 도나
    [본체 생성자] 200x200 (정사각형)
    [위임 생성자 본문] side=200
    [소멸자] 200x200 (정사각형)
    [catch] 너무 크다
```

**왜 그런가**

- ★★★ **`(1)` 의 순서는 「본체 생성자 → 위임 생성자 본문 → 소멸자」다**.\
  위임은 **다른 생성자에게 초기화를 통째로 맡기는 것**이라, 그것이 끝나야 위임한 쪽 본문이 돈다.
- ★★★ **`(2)` 에서 소멸자가 돈다**(`[소멸자] 200x200`). 근거 한 문장 —\
  **위임받은 생성자가 완주한 순간 객체는 「지어진 것」이 되고, 지어진 객체는 되감기에서 파괴된다.**
- ★★ **[15번](../15-raii-resources-as-types/)의 「생성자에서 던지면 소멸자가 안 돈다」와 모순이 아니다.**\
  기준은 늘 「**그 객체의 생성자가 완주했나**」다.\
  일반 생성자는 본문에서 던지면 **완주하지 못한 것**이고, 위임 생성자는 **본체가 완주한 시점**에 이미 참이다.\
  ★ 그래서 두 문장은 **같은 규칙의 양쪽 끝**이다.
- ★ **이미 지어진 멤버는 어느 경우에도 파괴된다** — 그것이 [15번](../15-raii-resources-as-types/)의 처방이 되는 자리다.

### 5. ★ 리스트가 이긴다 — 기본 멤버 초기자는 **평가조차 안 된다**

**출력**

```text
===== 소스: ctor06.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -pedantic ctor06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 리스트가 비면 기본 멤버 초기자가 쓰인다
    Count(100)
    n=1 c.v=100 untouched=42
(2) 리스트가 적으면 리스트가 이긴다
    Count(7)
    n=7 c.v=7 untouched=42
```

**왜 그런가**

- ★★★ **`(1)` 에서 `Count(100)`, `(2)` 에서 `Count(7)`** — **각각 한 번씩**이다.\
  `(2)` 에서 `Count(100)` 이 **안 찍힌다** — 리스트가 적히면 기본 멤버 초기자는 **쓰이지도, 평가되지도 않는다.**
- ★★ **`untouched` 는 두 판 모두 42** 다. 리스트에 안 적힌 멤버는 기본 멤버 초기자가 맡는다.\
  **둘을 섞어 쓰는 것이 정상**이고, 그것이 기본 멤버 초기자의 값이다.
- ★ 그래서 기본 멤버 초기자에 **비싼 초기화**를 적어도, 모든 생성자가 그 멤버를 리스트에서 덮으면 **비용은 0**이다.

### 6. ★★ 에러 **셋** — 본문에서 대입을 지워도 **둘은 남는다**

**출력**

```text
===== 소스: ctor04.cpp =====
// const 멤버와 참조 멤버는 본문 대입으로 못 만든다
struct Holder {
    const int limit;
    int& alias;
    int store;
    Holder() {
        limit = 10;        // const 멤버에 대입
        alias = store;     // 참조 멤버에 대입
    }
};
int main() { Holder h; (void)h; }
===== g++ -std=c++20 -Wall -Wextra -pedantic ctor04.cpp -o ex (cc exit=1) =====
ctor04.cpp: In constructor ‘Holder::Holder()’:
ctor04.cpp:6:5: error: uninitialized const member in ‘const int’ [-fpermissive]
    6 |     Holder() {
      |     ^~~~~~
ctor04.cpp:3:15: note: ‘const int Holder::limit’ should be initialized
    3 |     const int limit;
      |               ^~~~~
ctor04.cpp:6:5: error: uninitialized reference member in ‘int&’ [-fpermissive]
    6 |     Holder() {
      |     ^~~~~~
ctor04.cpp:4:10: note: ‘int& Holder::alias’ should be initialized
    4 |     int& alias;
      |          ^~~~~
ctor04.cpp:7:15: error: assignment of read-only member ‘Holder::limit’
    7 |         limit = 10;        // const 멤버에 대입
      |         ~~~~~~^~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic ctor04.cpp -o ex (cc exit=1) =====
ctor04.cpp:6:5: error: constructor for 'Holder' must explicitly initialize the const member 'limit'
    6 |     Holder() {
      |     ^
ctor04.cpp:3:15: note: declared here
    3 |     const int limit;
      |               ^
ctor04.cpp:6:5: error: constructor for 'Holder' must explicitly initialize the reference member 'alias'
    6 |     Holder() {
      |     ^
ctor04.cpp:4:10: note: declared here
    4 |     int& alias;
      |          ^
ctor04.cpp:7:15: error: cannot assign to non-static data member 'limit' with const-qualified type 'const int'
    7 |         limit = 10;        // const 멤버에 대입
      |         ~~~~~ ^
ctor04.cpp:3:15: note: non-static data member 'limit' declared const here
    3 |     const int limit;
      |     ~~~~~~~~~~^~~~~
3 errors generated.
```

**왜 그런가**

- ★★★ **에러 셋**은 ① `const` 멤버 미초기화 ② 참조 멤버 미초기화 ③ `const` 멤버에 대입이다.
- ★★★ **①②는 본문의 대입과 무관하다.** 대입 줄을 지워도 **생성자가 끝날 때까지 초기화되지 않았다**는 사실은 그대로이므로 남는다.\
  **막히는 것은 「대입을 했다」가 아니라 「초기화를 안 했다」다**.
- ★★★ **본문이 시작될 때 멤버는 이미 전부 지어져 있다.**\
  `const` 는 지어진 뒤 못 바꾸고, 참조는 **재결합되지 않는다**(형제 [`07번`](../07-references-vs-pointers/)).\
  그러니 값을 넣을 수 있는 자리는 **초기화 리스트(또는 기본 멤버 초기자)뿐**이다.
- ★★ **`const` 멤버를 두면 복사 대입·이동 대입이 자동으로 지워진다** — `const` 를 대입할 수 없기 때문이다.\
  **그 타입은 `std::vector` 의 원소로 넣는 순간 막힌다.**
- ★ **g++ 의 앞 두 에러에 `[-fpermissive]` 가 붙어 있다** — 8번 문항이 그 꼬리표를 던져 본 결과다.

### 7. ★★★ **이동 1 · 복사 1 · 복사 1 · 복사 1 · 이동 1**

**출력**

```text
===== 소스: ctor09.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -pedantic ctor09.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
ctor09.cpp: In function ‘int main()’:
ctor09.cpp:23:64: warning: implicitly-declared ‘HasCopyAsn::HasCopyAsn(const HasCopyAsn&)’ is deprecated [-Wdeprecated-copy]
   23 | #define MOVE_TEST(T) do { cp = mv = 0; { T a; T b = std::move(a); (void)b; } \
      |                                                                ^
ctor09.cpp:31:5: note: in expansion of macro ‘MOVE_TEST’
   31 |     MOVE_TEST(HasCopyAsn);
      |     ^~~~~~~~~
ctor09.cpp:17:43: note: because ‘HasCopyAsn’ has user-provided ‘HasCopyAsn& HasCopyAsn::operator=(const HasCopyAsn&)’
   17 | struct HasCopyAsn { Tracer t; HasCopyAsn& operator=(const HasCopyAsn&) { return *this; } };
      |                                           ^~~~~~~~
  Plain        를 옮기면  복사 0 · 이동 1  -> 이동 생성자가 있다
  HasDtor      를 옮기면  복사 1 · 이동 0  -> 이동이 없어 복사로 갔다
  HasCopy      를 옮기면  복사 1 · 이동 0  -> 이동이 없어 복사로 갔다
  HasCopyAsn   를 옮기면  복사 1 · 이동 0  -> 이동이 없어 복사로 갔다
  Defaulted    를 옮기면  복사 0 · 이동 1  -> 이동 생성자가 있다
```

**왜 그런가**

| 클래스 | 적힌 것 | 복사 | 이동 | 읽는 법 |
|---|---|---|---|---|
| `Plain` | 없음 | 0 | **1** | 이동 생성자가 생긴다 |
| `HasDtor` | **소멸자** | ★★★ **1** | 0 | **이동이 안 생겨 복사로 갔다** |
| `HasCopy` | **복사 생성자** | ★ **1** | 0 | 〃 |
| `HasCopyAsn` | **복사 대입** | ★ **1** | 0 | 〃 (+ `-Wdeprecated-copy` 1건) |
| `Defaulted` | 전부 `= default` | 0 | **1** | 이동이 남는다 |

- ★★★ **`std::is_move_constructible_v` 로는 답할 수 없다.** 이동 생성자가 없어도\
  **복사 생성자가 `const T&` 로 rvalue 를 받아 주므로** 그 특성은 **참**이 된다.\
  ★★ **「옮겼는데 복사가 돌았다」는 사실은 계수기로만 드러난다.**
- ★★★ **소멸자 하나를 적으면 이동이 사라지는 이유** — 소멸자를 직접 적었다는 것은\
  **그 타입이 자원을 손수 다룬다는 신호**이고, 그러면 **컴파일러가 만든 멤버별 이동이 옳다는 보장이 없다.**\
  표준이 **안전한 쪽(복사)으로 떨어뜨린다.** 이것이 **0/3/5의 법칙**(목록의 **18번 주제**)의 근거다.
- ★ **경고 1건은 `HasCopyAsn`** 에서 났다 — `implicitly-declared 'HasCopyAsn::HasCopyAsn(const HasCopyAsn&)' is deprecated [-Wdeprecated-copy]`.\
  **표준이 그 조합을 비권장으로 표시**해 둔 자리다.

### 8. ★★★ 경고가 되고 **`cc exit=0`** — `-pedantic-errors` 로도 **안 살아난다**

**출력**

```text
===== 소스: ctor11.cpp =====
// 종료 코드가 0인데 ill-formed — 초기화를 빼먹은 const 멤버
#include <cstdio>
struct Holder {
    const int limit;          // 초기화하지 않는다
    int store = 5;
    int& alias;
    Holder() : alias(store) {}
};
struct Conf { static const double ratio = 1.5; };   // constexpr 가 필요한 자리
int main() {
    Holder h;
    std::printf("돌아간다. sizeof(Holder) : %zu\n", sizeof h);
    std::printf("Conf::ratio              : %.1f\n", Conf::ratio);
    std::printf("(limit 은 초기화된 적이 없어 읽지 않는다)\n");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ctor11.cpp -o ex (cc exit=1) =====
ctor11.cpp: In constructor ‘Holder::Holder()’:
ctor11.cpp:7:5: error: uninitialized const member in ‘const int’ [-fpermissive]
    7 |     Holder() : alias(store) {}
      |     ^~~~~~
ctor11.cpp:4:15: note: ‘const int Holder::limit’ should be initialized
    4 |     const int limit;          // 초기화하지 않는다
      |               ^~~~~
ctor11.cpp: At global scope:
ctor11.cpp:9:35: error: ‘constexpr’ needed for in-class initialization of static data member ‘const double Conf::ratio’ of non-integral type [-fpermissive]
    9 | struct Conf { static const double ratio = 1.5; };   // constexpr 가 필요한 자리
      |                                   ^~~~~
===== g++ -std=c++20 -Wall -Wextra -fpermissive ctor11.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
ctor11.cpp: In constructor ‘Holder::Holder()’:
ctor11.cpp:7:5: warning: uninitialized const member in ‘const int’ [-fpermissive]
    7 |     Holder() : alias(store) {}
      |     ^~~~~~
ctor11.cpp:4:15: note: ‘const int Holder::limit’ should be initialized
    4 |     const int limit;          // 초기화하지 않는다
      |               ^~~~~
ctor11.cpp: At global scope:
ctor11.cpp:9:35: warning: ‘constexpr’ needed for in-class initialization of static data member ‘const double Conf::ratio’ of non-integral type [-fpermissive]
    9 | struct Conf { static const double ratio = 1.5; };   // constexpr 가 필요한 자리
      |                                   ^~~~~
돌아간다. sizeof(Holder) : 16
Conf::ratio              : 1.5
(limit 은 초기화된 적이 없어 읽지 않는다)
===== g++ -std=c++20 -Wall -Wextra -fpermissive -pedantic-errors ctor11.cpp -o ex (cc exit=0) =====
ctor11.cpp: In constructor ‘Holder::Holder()’:
ctor11.cpp:7:5: warning: uninitialized const member in ‘const int’ [-fpermissive]
    7 |     Holder() : alias(store) {}
      |     ^~~~~~
ctor11.cpp:4:15: note: ‘const int Holder::limit’ should be initialized
    4 |     const int limit;          // 초기화하지 않는다
      |               ^~~~~
ctor11.cpp: At global scope:
ctor11.cpp:9:35: warning: ‘constexpr’ needed for in-class initialization of static data member ‘const double Conf::ratio’ of non-integral type [-fpermissive]
    9 | struct Conf { static const double ratio = 1.5; };   // constexpr 가 필요한 자리
      |                                   ^~~~~
===== clang++ -std=c++20 -Wall -Wextra -fpermissive ctor11.cpp -o ex (cc exit=1) =====
ctor11.cpp:7:5: error: constructor for 'Holder' must explicitly initialize the const member 'limit'
    7 |     Holder() : alias(store) {}
      |     ^
ctor11.cpp:4:15: note: declared here
    4 |     const int limit;          // 초기화하지 않는다
      |               ^
ctor11.cpp:9:35: error: in-class initializer for static data member of type 'const double' requires 'constexpr' specifier [-Wstatic-float-init]
    9 | struct Conf { static const double ratio = 1.5; };   // constexpr 가 필요한 자리
      |                                   ^       ~~~
ctor11.cpp:9:15: note: add 'constexpr'
    9 | struct Conf { static const double ratio = 1.5; };   // constexpr 가 필요한 자리
      |               ^
      |               constexpr 
2 errors generated.
```

**왜 그런가**

| 플래그 | 결과 |
|---|---|
| `g++ -Wall -Wextra -pedantic` | **에러 2건 · `cc exit=1`** |
| `g++ -Wall -Wextra -fpermissive` | ★★★ **경고 2건 · `cc exit=0` · 프로그램이 돈다** |
| `g++ -fpermissive -pedantic-errors` | ★★★ **여전히 `cc exit=0`** |
| `clang++ -Wall -Wextra -fpermissive` | **에러 · `cc exit=1`** |

- ★★★ **`-pedantic-errors` 는 이것을 되돌리지 못한다.** `-pedantic` 계열이 다루는 것은\
  「**표준이 금지한 확장을 쓴 것**」이고, `-fpermissive` 가 낮춘 것은 「**표준이 요구한 진단**」이라 층이 다르다.
- ★★ **clang 에는 `-fpermissive` 가 사실상 없다** — 같은 파일을 주면 그대로 에러다.\
  **한 컴파일러에서 본 것을 플래그의 성질로 일반화하면 안 된다.**
- ★★★ **그래서 「우리 빌드는 통과한다」는 「표준에 맞다」를 증명하지 못한다.**\
  빌드 플래그를 먼저 봐야 하고, **`-fpermissive` 가 켜져 있으면 그 빌드의 통과는 근거가 아니다.**

### 9. 「두 번 손댄다」와 「`explicit` 누락」은 **아무도 안 본다**

**출력**

```text
===== echo "ctor02 -Wreorder   경고 $(g++ -std=c++20 -Wall -Wextra -pedantic ctor02.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
ctor02 -Wreorder   경고 3
===== echo "ctor03 되짚기      경고 $(g++ -std=c++20 -Wall -Wextra -pedantic ctor03.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
ctor03 되짚기      경고 5
===== echo "ctor09 deprecated  경고 $(g++ -std=c++20 -Wall -Wextra -pedantic ctor09.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
ctor09 deprecated  경고 1
===== echo "ctor02 clang       경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic ctor02.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
ctor02 clang       경고 1
===== echo "ctor03 clang       경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic ctor03.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
ctor03 clang       경고 2
```

**왜 그런가**

- ★★★ **(1)의 「두 번 손댄다」를 경고하는 컴파일러는 없다.** 그것은 **틀린 코드가 아니라 비싼 코드**이기 때문이다.\
  **계수기(①의 창)만이 그것을 본다.**
- ★★★ **`explicit` 을 빠뜨린 설계도 아무 도구가 안 본다.** 암묵 변환은 **표준이 허용하는 동작**이다.
- ★★ **같은 UB 를 두 자리에서 쓰면 g++ 의 반응이 다르다** —\
  **초기화 리스트**에서는 `-Wuninitialized` 로 **5건**을 말하고,\
  **기본 멤버 초기자**에서는 **0건**이다([12번](../12-class-basics-members-access-and-this/) (6)). **clang 은 뒤쪽도 본다(1건).**
- ★ 경고 개수는 컴파일러마다 다르다 — `-Wreorder` g++ **3** · clang **1**, 되짚기 g++ **5** · clang **2**.

### 10. 이어지는 자리

- **「이름은 찾아지는데 값이 없다」의 짝** — [12번](../12-class-basics-members-access-and-this/) **(6)** 의 `lazy`.
- **파괴 순서** — [14번](../14-destructors-and-deterministic-destruction/)이 정본이다. **초기화의 정확한 역순**이다.
- **`Probe` 계수 방식** — 형제 [`11번`](../11-choosing-parameter-passing/)에서 왔다.
- **0/3/5의 법칙** — 목록의 **18번 주제**.
- **러스트에 초기화 순서 함정이 없는 이유** — 러스트에는 **생성자가 없고** `Struct { a: 1, b: 2 }` 로\
  **모든 필드를 한 번에** 적어야 한다. **「아직 안 지어진 필드」라는 상태가 원리적으로 없다.**\
  러스트 갈래 [`16-structs-impl-and-associated-functions/`](../../../rust/syntax/16-structs-impl-and-associated-functions/)가 그 자리다.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `ctor01.cpp` 계수 | g++ 1회(5줄) | ★★★ 리스트 **1** · 본문 **2** · 값 싱크 **2 대 3** · `= default` **1** |
| `ctor02.cpp` 초기화 순서 | g++ · clang 각 1회 | ★★ 생성 `a`→`b` · 파괴 `b`→`a` · 경고 **g++ 3 · clang 1** |
| `ctor03.cpp` 되짚기 | g++ 2회(`-O0`·`-O2`) | ★★★ `n == m*2` 가 **두 판 모두 0** · 경고 **g++ 5 · clang 2** |
| `ctor04.cpp` `const`·참조 멤버 | g++ · clang 각 1회 | 양쪽 **에러 3건 · `cc exit=1`** |
| `ctor05.cpp` 위임 생성자 | g++ 1회 | ★★ 본체 → 위임 본문 · **던진 뒤 소멸자가 돈다** |
| `ctor06.cpp` 기본 멤버 초기자 | g++ 1회 | `Count(100)` 1회 / `Count(7)` 1회 · `untouched` 42 고정 |
| `ctor07.cpp` `explicit` 통과 판 | g++ 1회 | `take_m(3)`·`take_f(3)`·`a.v=b.v=c.v=5` |
| `ctor08.cpp` `explicit` 금지 판 | g++ 1회 | **에러 3건**(인자 변환 · 복사 초기화 · 복사 리스트 초기화) |
| `ctor09.cpp` 암묵 이동 | g++ 1회(5줄) | ★★★ **이동 1 · 복사 1 · 복사 1 · 복사 1 · 이동 1** + `-Wdeprecated-copy` 1건 |
| `ctor10.cpp` `= delete` | g++ 1회 | **에러 4건** |
| `ctor11.cpp` `-fpermissive` | g++ 3회 · clang 1회 | ★★★ 기본 **에러** / `-fpermissive` **경고·exit 0** / **`-pedantic-errors` 로도 exit 0** / clang **에러** |
| `ctor12.cpp` 형태 | g++ 1회 | `a=이름 없음(0)  b=셋짜리(9)` |
| `ctor13.cpp` 금지 사례 | g++ 1회 | **에러 7건** |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · libstdc++)에서만** 그렇다.

- ★★ **경고 개수와 경고 이름 전부**(`-Wreorder` 대 `-Wreorder-ctor`, 3건 대 1건).
- ★★ **`-fpermissive` 의 존재와 그 범위** — clang 에는 사실상 없다.
- ★ **진단 문구 전부**.
- ★ **(3)의 `-O0`·`-O2` 에서 `n` 이 가진 값** — 미정이므로 싣지 않았다.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **초기화 리스트가 본문보다 먼저 도는** 것.
- **멤버가 선언 순서로 초기화되고 파괴가 그 역순인** 것.
- **`const` 멤버·참조 멤버는 리스트나 기본 멤버 초기자로만 초기화되는** 것.
- **리스트에 적힌 멤버의 기본 멤버 초기자가 평가되지 않는** 것.
- **위임 생성자의 본체가 끝나면 객체가 「지어진 것」이 되는** 것.
- **사용자가 소멸자·복사 생성자·복사 대입 중 하나라도 적으면 이동이 생성되지 않는** 것.
- **`explicit` 이 암묵 변환과 복사 초기화를 막는** 것.

**UB 의 결과라 보장이 아닌 것**(관찰로만 읽는다)

- ★ (3)의 **`Trap::n` 값** — 미정이다. 근거로 쓰는 것은 「**`n == m*2` 가 두 최적화 수준 모두 0이었다**」와\
  「**`-Wuninitialized` 가 그 줄을 짚었다**」뿐이다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **`-std=c++11`·`c++14`·`c++17` 판**(전부 `-std=c++20` 으로만 돌렸다) ·\
  ★ **`-O1`·`-O3`·`-Os` 에서의 계수**((1)은 기본값 판만 돌렸다) ·\
  ★ **위임이 재귀가 되는 판**(`A() : A() {}`) · ★ **`constexpr` 생성자** ·\
  ★ **집합체 초기화 판**(생성자를 하나도 안 적은 타입) · ★ **이동이 비싼 타입**(이 문서의 `Probe`·`Tracer` 는 둘 다 싸다) ·\
  ★ **`-fno-elide-constructors`** 를 준 판(복사 생략을 끄면 (1)의 수가 달라질 수 있다).
- **못 잰 것** — ★★★ **「초기화 리스트가 몇 배 싼가」.**\
  이 문서가 센 것은 **호출 횟수까지**다. `Probe` 는 `int` 하나뿐이라 **그 한 번이 얼마인지는 재지 않았다.**\
  **재려면 벤치마크 하네스가 따로 필요하다.**
- ★ **「부적용인 창」** — **`sizeof`.** 초기화 방식이 달라도 객체 크기는 같아 **잴 것이 없다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **g++ 가 기본 멤버 초기자의 초기화 전 읽기를 경고하기 시작했는지**(9번 — 지금은 **0건**).
- ★★ **`-fpermissive` 가 이 둘을 계속 통과시키는지**(8번) — GCC 가 범위를 좁히면 **에러로 바뀐다.**
- ★ **경고 개수**(2번의 3건·1건, 3번의 5건·2건) — 진단을 합치거나 쪼개면 움직인다.
- ★ **`-Wdeprecated-copy` 가 계속 1건인지**(7번) — 표준이 그 조합을 제거하면 **에러가 된다.**
