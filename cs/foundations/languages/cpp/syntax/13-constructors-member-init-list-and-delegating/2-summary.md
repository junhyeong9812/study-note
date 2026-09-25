# cpp/syntax/13 — 생성자·멤버 초기화 리스트·위임 생성자 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 생성자와 멤버 초기화 리스트](https://en.cppreference.com/w/cpp/language/constructor) · [기본 멤버 초기자](https://en.cppreference.com/w/cpp/language/data_members) · [`explicit`](https://en.cppreference.com/w/cpp/language/explicit) · [`=default`](https://en.cppreference.com/w/cpp/language/function#Function_definition) · [`=delete`](https://en.cppreference.com/w/cpp/language/function#Deleted_functions) · [GCC — `-fpermissive`](https://gcc.gnu.org/onlinedocs/gcc/C_002b_002b-Dialect-Options.html)
> **실행 검증** — 이 문서의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`ctor01.cpp` \~ `ctor13.cpp`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.
> **버전** — 초기화 리스트·`explicit` 은 **C++98부터**. **위임 생성자·기본 멤버 초기자·`=default`·`=delete` 는 C++11부터**,\
> **`explicit` 을 `{}` 초기화에 적용하는 규칙(P0960 등)은 C++17\~20 에서 다듬였다.** 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.
> ★★★ **12 → 13 → 14 → 15 는 한 사슬이다** — [12번](../12-class-basics-members-access-and-this/)이 **그릇**을 만들고,\
> **여기 13 이 「그 그릇을 어떻게 채우나」에 답한다.** [14번](../14-destructors-and-deterministic-destruction/)이 **비우는 시점**을,\
> [15번](../15-raii-resources-as-types/)이 **그 시점을 자원 관리에 쓰는 법**을 답한다.\
> ★★ **[12번](../12-class-basics-members-access-and-this/) (6)의 `lazy` 가 여기서 풀린다** — 이름은 찾아졌는데 값이 없던 그 자리다.
> **경계** — 「`{}` 초기화와 좁히기」는 형제 [`04번`](../04-brace-initialization-narrowing-and-initializer-list/),\
> 「복사·이동이 무엇을 옮기나」는 형제 [`09번`](../09-rvalue-references-move-and-forward/)과 목록의 **16·17번 주제**,\
> 「어떤 매개변수로 받을까」는 형제 [`11번`](../11-choosing-parameter-passing/)이 정본이다.\
> 「0/3/5의 법칙」은 목록의 **18번 주제**, 「`explicit` 과 변환 생성자」의 넓은 판은 목록의 **24번 주제**가 정본이다.\
> 여기서는 「**초기화가 언제 몇 번 일어나나**」만 센다.
> ★★★ **이 문서는 시간을 재지 않았다.** 근거는 **생성자·대입 호출 횟수**와 **컴파일러 진단** 둘뿐이다.\
> 「몇 배 빠르다」는 문장은 **한 줄도 없다**.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★ **초기화되지 않은 멤버의 값**(`Trap::n`) — **-O0 과 -O2 에서 달랐다** | ★★★ **약속이 깨졌다는 비교 결과**(`n == m*2` 가 **0**) |
> | 두 컴파일러의 **진단 문구**와 경고 이름 | ★★★ **생성자·대입 호출 횟수** — 이 주제의 답 자체다 |
> | 객체의 주소값 | ★★ **로그가 찍힌 순서** · **에러냐 경고냐 통과냐** · **`cc exit`** · **경고 개수** |

## 한눈에 — 쉽게 말하면

**초기화 리스트는 「처음부터 그 값으로 짓는 것」이고, 본문 대입은 「빈 것을 짓고 나서 덮어쓰는 것」이다.**

이사를 떠올린다.

| 비유 | 코드 | 몇 번 손대나 |
|---|---|---|
| **처음부터 원하는 가구를 들여놓는다** | `Widget() : m(p) {}` | ★ **한 번** |
| **아무 가구나 들여놓고 나중에 바꾼다** | `Widget() { m = p; }` | ★★ **두 번**(기본 생성 + 대입) |
| **못 바꾸는 가구(붙박이장)** | `const` 멤버 · 참조 멤버 | ★★★ **리스트로만** 들여놓을 수 있다 |
| **다른 집 계약을 그대로 쓴다** | 위임 생성자 `Widget() : Widget(0,"") {}` | 본체가 먼저, 위임 쪽 본문이 나중 |
| **계약서에 미리 적어 둔 기본 사양** | 기본 멤버 초기자 `int n = 1;` | 리스트가 적히면 **그쪽이 이긴다** |

> **멤버 초기화 리스트(member initializer list)** — 생성자 이름 뒤 `:` 부터 본문 `{` 까지.\
> 예: `Widget(int w) : w_(w), area_(w*w) {}` — 본문이 돌기 전에 멤버가 지어진다.

> **기본 멤버 초기자(default member initializer)** — 클래스 안에서 멤버 선언에 바로 붙인 초기값.\
> 예: `int n = 1;` — 어느 생성자도 `n` 을 리스트에 안 적으면 이 값이 쓰인다.

- ★★★ **「한 번이냐 두 번이냐」는 의견이 아니라 계수다** — 이 문서는 **생성자·대입에 로그를 심어 센다**((1)).
- ★★★ **멤버는 「리스트에 적은 순서」가 아니라 「선언한 순서」로 초기화된다**((2)). 이 하나가 이 주제의 함정 전부를 만든다.
- ★★ **위임 생성자는 「본체가 끝나면 객체는 지어진 것」이라는** 경계를 만든다 — 그 뒤에 던지면 **소멸자가 돈다**((4)).

```text
   초기화 리스트                       본문 대입
   Widget(const Probe& p)             Widget(const Probe& p)
     : m(p)     <- 복사 생성 1회        { m = p; }   <- 기본 생성 1회
   { }                                              + 복사 대입 1회

   +---------+                        +---------+        +---------+
   |  m = p  |  한 번에 지어진다       |  m = 0  |  ----> |  m = p  |
   +---------+                        +---------+        +---------+
                                       기본 생성          덮어쓰기
```

## 이 주제가 답하려는 질문

1. **초기화 리스트와 본문 대입은 몇 번씩 손대나** — 그리고 **왜 그 차이가 나나**((1)).
2. **멤버 초기화 순서는 무엇이 정하나** — 그것을 어기면 **무엇이 출력되나**((2)(3)).
3. **위임 생성자는 어디까지를 「지어진 것」으로 보나**((4)).
4. **컴파일러가 특수 멤버를 언제 안 만들어 주나** — 그것을 **어떻게 확인하나**((7)).

## 동작 방식

### (0) 이 주제가 쓰는 네 창

「초기화가 몇 번 일어났나」는 눈에 안 보인다. 창 넷을 갈라 쓴다.

```text
① 생성자·대입에 로그를 심는다   방식마다 몇 번 도는지 센다        (1)(7)
② 생성 순서를 로그로 찍는다     선언 순서인가 리스트 순서인가     (2)(4)(5)
③ 컴파일러 진단                리스트로만 되는 것 · 지워진 것    (3)(6)(7)
④ 경고를 플래그별로 센다       같은 함정을 누가 보나             (2)(3)(8)
```

- ★★★ **주력 창은 ①이다.** 「초기화 리스트가 더 낫다」를 **말로 하면 어디까지 참인지 모른다** — **세면 안다.**\
  ★ 이 계수 방식은 형제 [`11번`](../11-choosing-parameter-passing/)의 `Probe` 를 그대로 이어받은 것이다.
- ★★ **네 번째 창은 ④다.** 이 주제의 함정 둘(초기화 순서·암묵 변환)은 **에러가 아니라 경고**로만 나오고,\
  **컴파일러마다 개수가 다르다**((8)). 개수를 세 두지 않으면 「조용했다」와 「안 물어봤다」가 구분되지 않는다.
- ★ **「부적용인 창」** — **`sizeof`**. 초기화 방식이 달라도 객체 크기는 같다. 「재 봤더니 같았다」가 아니라 「**잴 것이 없다**」다.

### (1) ★★★ 리스트와 본문 — 몇 번 손대나

**언제 쓰나** — 생성자를 쓸 때마다. 멤버를 `:` 뒤에 둘지 `{}` 안에 둘지 고르는 그 자리다.

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

| 쓴 방식 | 기본 | 복사 | 이동 | 복사대입 | 이동대입 | 합 |
|---|---|---|---|---|---|---|
| `: m(p)` 리스트 | 0 | ★ **1** | 0 | 0 | 0 | ★ **1** |
| `{ m = p; }` 본문 | ★★ **1** | 0 | 0 | ★★ **1** | 0 | ★★ **2** |
| `: m(std::move(p))` 리스트 | 0 | 1 | 1 | 0 | 0 | 2 |
| `{ m = std::move(p); }` 본문 | ★★ **1** | 1 | 0 | 0 | 1 | ★★ **3** |
| `= default` | 1 | 0 | 0 | 0 | 0 | 1 |

그림 해설 (한 단계씩):

- ★★★ **본문 대입은 멤버를 두 번 손댄다** — **기본 생성 1회 + 대입 1회**. 리스트는 **한 번**이다.
- ★★★ **값으로 받아 옮기는 싱크에서는 차이가 하나 더 벌어진다**(2회 대 3회) —\
  **값 매개변수를 만드는 복사 1회는 둘이 같고**, 본문 쪽만 **기본 생성 1회**를 더 낸다.\
  ★ 「값으로 받을까 `const&` 로 받을까」 자체는 형제 [`11번`](../11-choosing-parameter-passing/)이 정본이다.
- ★★ **`= default` 도 기본 생성 1회를 낸다** — **「아무것도 안 쓴 것」이 「아무 일도 안 하는 것」은 아니다.**\
  멤버에 기본 생성자가 있으면 그것이 돈다.
- ★ **이 표에 시간은 없다.** `Probe` 는 `int` 하나뿐이라 **횟수의 차이가 곧 비용의 차이라고 말할 수 없다** —\
  이 문서가 센 것은 **호출 횟수까지**다.

**비용** — 본문 대입은 멤버 하나당 **기본 생성 1회**를 더 낸다. **멤버가 기본 생성할 수 없으면 아예 컴파일되지 않는다**((3)).

### (2) ★★★ 초기화 순서 — 리스트 순서가 아니라 선언 순서다

**언제 쓰나** — 멤버가 둘 이상일 때마다. 특히 **한 멤버가 다른 멤버를 참고할 때.**

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

- ★★★ **리스트에 `b, a` 순으로 적었는데 `a` 가 먼저 지어졌다.** **선언 순서가 이긴다.**
- ★★★ **파괴는 그 역순**이다(`b` → `a`). 그 규칙의 정본은 [14번](../14-destructors-and-deterministic-destruction/)이다.
- ★★ **g++ 가 `-Wreorder` 로 말해 준다** — 그리고 **한 사건에 `warning:` 줄이 셋**이다\
  (「`b` 가 나중에 초기화된다」 · 「`a` 다」 · 「여기서 초기화했다」). **경고 개수를 셀 때 이 셋이 3건으로 세어진다**((8)).

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic ctor02.cpp -o ex (cc exit=0) =====
ctor02.cpp:13:15: warning: field 'b' will be initialized after field 'a' [-Wreorder-ctor]
   13 |     Order() : b("b — 리스트에 먼저 적음"), a("a — 리스트에 나중 적음") {}
      |               ^~~~~~~~~~~~~~~~~~~~~~~~~~~  ~~~~~~~~~~~~~~~~~~~~~~~~~~~
      |               a("a — 리스트에 나중 적음")  b("b — 리스트에 먼저 적음")
1 warning generated.
```

- ★★ clang 은 같은 사실을 `warning:` **한 줄**로 말하고, 대신 **고쳐야 할 순서를 캐럿 아래 그려 준다.**\
  경고 이름도 다르다(g++ `-Wreorder` · clang `-Wreorder-ctor`).
- ★★★ **그래서 「경고 몇 건」은 컴파일러를 밝히지 않으면 뜻이 없다** — 같은 사건이 g++ 3건 · clang 1건이다.

```text
   class Order {
       Log a;      <- 선언 1번째        초기화: a  ->  b
       Log b;      <- 선언 2번째        파괴  : b  ->  a
       Order() : b(...), a(...) {}
                   ^^^^^^^^^^^^
                   적은 순서는 아무 영향이 없다 (경고만 난다)
   };
```

**비용** — 0. 다만 **이 규칙을 모르면 (3)의 버그를 만든다.**

### (3) ★★ 순서를 거스르면 — 값이 아니라 약속이 깨진다

**언제 쓰나** — 한 멤버를 다른 멤버로 초기화하고 싶을 때.

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

- ★★★ **`n` 이 먼저 선언됐으므로 `n(m * 2)` 가 먼저 돈다.** 그 시점에 `m` 은 **아직 초기화되지 않았다.**\
  그래서 **`n == m*2` 라는 약속이 깨진다**(출력 **0**).
- ★★★ **값 자체는 싣지 않는다.** 미정(indeterminate)이고 **`-O0` 과 `-O2` 에서 달랐다** — 머리말의 「흔들리는 칸」이다.\
  ★ **실을 수 있는 것은 「약속이 깨졌다」는 사실**뿐이고, 그것은 **두 최적화 수준에서 똑같이 0**이었다.
- ★★ **g++ 가 `-Wuninitialized` 로 정확히 짚는다** — `member 'Trap::m' is used uninitialized`.\
  **`-Wreorder` 와 `-Wuninitialized` 가 함께 나오는 것**이 이 함정의 지문이다.
- ★ **[12번](../12-class-basics-members-access-and-this/) (6)의 `lazy` 가 같은 사건**이다. 거기서는 **g++ 가 조용했고**\
  여기서는 말한다 — **기본 멤버 초기자에서는 놓치고 초기화 리스트에서는 잡는다**는 뜻이다.

**비용** — 고치는 법은 공짜다. **선언 순서를 의도한 순서로 바꾸거나**, 계산을 **본문으로 내리거나**, 인자에서 직접 계산한다.

### (4) ★★ 위임 생성자 — 어디까지가 「지어진 것」인가

**언제 쓰나** — 생성자 여럿이 같은 초기화를 되풀이할 때.

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

```text
   Widget(int side) : Widget(side, side, "정사각형") { ... }
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      ① 본체 생성자가 먼저 끝까지 돈다
                         -> 이 순간 객체는 "지어진 것"이 된다
                      ② 그다음 위임 쪽 본문이 돈다
                      ③ 여기서 던지면 -> ★ 소멸자가 돈다
```

그림 해설 (한 단계씩):

- ★★★ **본체 생성자가 먼저 끝까지 돌고, 위임한 쪽 본문이 나중에 돈다.** 로그 순서가 그대로 보인다.
- ★★★ **위임 뒤 본문에서 던졌더니 소멸자가 돌았다**(`[소멸자] 200x200`).\
  **위임받은 생성자가 끝난 순간 객체는 완성된 것**으로 치기 때문이다.
- ★★ **이것은 [15번](../15-raii-resources-as-types/)의 「생성자에서 던지면 소멸자가 안 돈다」와 정반대로 보이지만 같은 규칙**이다 —\
  기준은 늘 「**생성자가 완주했나**」이고, 위임 생성자는 **본체가 완주한 시점**에 그것이 참이 된다.
- ★ **위임은 재귀가 되면 안 된다** — `A() : A() {}` 는 UB 이고 컴파일러가 대개 막는다(이 문서는 던지지 않았다).

**비용** — 0. 위임은 **코드 중복을 줄이는 도구**이지 성능 도구가 아니다.

### (5) ★ 기본 멤버 초기자와 리스트가 겹치면

**언제 쓰나** — 멤버 선언에 기본값을 적어 두고 생성자도 여럿 둘 때.

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

- ★★★ **리스트가 이긴다.** `Conf(7)` 에서 `Count(7)` 만 찍히고 **`Count(100)` 은 아예 안 찍힌다** —\
  기본 멤버 초기자는 **쓰이지 않으면 평가조차 되지 않는다.**
- ★★ **리스트에 안 적힌 멤버는 기본 멤버 초기자가 맡는다**(`untouched` 가 두 판 모두 42).\
  **둘을 섞어 쓰는 것이 정상**이고, 그것이 기본 멤버 초기자의 값이다.
- ★ **기본 멤버 초기자도 「선언 순서」 규칙을 그대로 받는다** — [12번](../12-class-basics-members-access-and-this/) (6)이 그 함정이다.

**비용** — 0회. **안 쓰인 기본 멤버 초기자는 아무것도 하지 않는다.**

### (6) ★★ `const` 멤버·참조 멤버 — 리스트로만 된다

**언제 쓰나** — 한 번 정하면 안 바뀌는 멤버를 둘 때.

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

- ★★★ **에러가 셋이다** — ① `const` 멤버를 초기화 안 함 ② 참조 멤버를 초기화 안 함 ③ `const` 멤버에 대입.\
  ★ **①②는 「본문에 대입을 적었다」와 무관하게 난다** — **생성자가 끝나는 시점까지 초기화되지 않으면** 그 자체가 에러다.
- ★★★ **이유는 하나다 — 본문이 시작될 때 멤버는 이미 다 지어져 있다.**\
  `const` 는 지어진 뒤에 못 바꾸고, 참조는 **재결합되지 않는다**(형제 [`07번`](../07-references-vs-pointers/)).\
  **그러니 손댈 수 있는 유일한 자리가 초기화 리스트**다.
- ★★ **clang 이 그것을 문장으로 적는다** — `constructor for 'Holder' must explicitly initialize the const member 'limit'`.
- ★ **g++ 의 앞 두 에러에 `[-fpermissive]` 가 붙어 있다** — **그 플래그를 주면 통과한다**는 뜻이다((8)).

**비용** — 0. 대신 **설계가 좁아진다** — `const`·참조 멤버가 있으면 **복사 대입이 자동으로 지워진다.**

### (7) ★★ 컴파일러가 이동 생성자를 언제 안 만드나

**언제 쓰나** — 「옮겼는데 왜 빠르지 않지?」 싶을 때.

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

| 클래스에 적힌 것 | 이동 생성자가 생기나 | 옮기면 무엇이 도나 |
|---|---|---|
| 아무것도 안 적음 | ★ **생긴다** | 이동 1 |
| **소멸자**를 적음 | ★★★ **안 생긴다** | **복사 1** |
| **복사 생성자**를 적음 | ★★★ **안 생긴다** | **복사 1** |
| **복사 대입**을 적음 | ★★★ **안 생긴다** | **복사 1** |
| 전부 `= default` 로 적음 | ★ **생긴다** | 이동 1 |

- ★★★ **「옮겼는데 복사가 돌았다」가 유일하게 믿을 만한 증거다.** `std::is_move_constructible_v` 는 **이 질문에 답하지 못한다** —\
  이동 생성자가 없어도 **복사 생성자가 rvalue 를 받아 주므로 그 특성은 참**이 되기 때문이다.\
  ★★ 그래서 이 절은 **특성이 아니라 계수**로 답한다.
- ★★ **소멸자 하나를 적었을 뿐인데 이동이 사라진다** — 이것이 **0/3/5의 법칙**이 나온 이유다(목록의 **18번 주제**).
- ★ **복사 대입만 적은 판에서는 경고가 하나 더 난다** — `implicitly-declared ... is deprecated [-Wdeprecated-copy]`.\
  **표준이 그 조합을 「비권장」으로 표시**해 둔 자리다.
- ★ **`= default` 로 적는 것은 「적지 않은 것」과 다르다** — 명시적으로 적으면 **다른 것을 적어도 이동이 남는다.**

**비용** — 이동이 사라지면 **복사가 대신 돈다.** 그 값이 얼마인지는 **타입에 달렸고 이 문서는 재지 않았다.**

### (8) ★★ 종료 코드가 0인데 ill-formed — `-fpermissive`

**언제 쓰나** — 낡은 코드베이스가 `-fpermissive` 를 켜 두었을 때.

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

- ★★★ **기본 플래그에서는 에러(`cc exit=1`)인 두 가지가 `-fpermissive` 를 주면 경고가 되고 `cc exit=0` 이 된다.**
  - **초기화되지 않은 `const` 멤버**((6)의 ①)
  - **`constexpr` 없이 `static const double` 을 클래스 안에서 초기화한 것**
- ★★★ **`-pedantic-errors` 로도 안 살아난다.** `-fpermissive -pedantic-errors` 조합에서도 **`cc exit=0`** 이다 —\
  `-pedantic` 계열은 「**표준이 금지한 확장**」을 다루지, **`-fpermissive` 가 내린 에러를 되돌리지 않는다.**
- ★★ **clang 에는 `-fpermissive` 가 사실상 없다** — 같은 파일을 clang 에 주면 **그대로 에러**다.\
  「한 컴파일러에서 본 것을 플래그의 성질로 일반화하지 마라」가 여기서도 그대로 성립한다.
- ★ 그래서 **「우리 빌드는 통과한다」는 「표준에 맞다」가 아니다.** 빌드 플래그를 먼저 봐야 한다.

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

- ★★★ **같은 사건에 대해 경고 개수가 컴파일러마다 다르다** — `-Wreorder` 는 g++ 3 · clang 1,\
  되짚기 함정은 g++ 5 · clang 2. **「경고 N건」을 컴파일러 없이 인용하면 안 된다.**

**비용** — `-fpermissive` 는 **빌드를 통과시키는 대신 그 프로그램이 무엇인지에 대한 보장을 버린다.**

## 문법 — 형태와 규칙

### 형태

```cpp
/* ctor12.cpp */
// 생성자 한 벌의 형태 — 이 파일은 그대로 컴파일된다
#include <cstdio>
#include <string>
#include <utility>

class Widget {
public:
    Widget() : Widget(0, "이름 없음") {}            // 위임 생성자
    Widget(int w, std::string name)                 // 본체 생성자
        : w_(w),                                    // 초기화 리스트 — 선언 순서로 돈다
          name_(std::move(name)),
          area_(w * w) {}
    explicit Widget(double)  = delete;              // 이 변환은 막는다
    Widget(const Widget&)    = default;             // 컴파일러가 만든 것을 그대로
    Widget(Widget&&) noexcept = default;
    Widget& operator=(const Widget&) = default;
    Widget& operator=(Widget&&) noexcept = default;
    ~Widget() = default;

    int area() const { return area_; }
    const std::string& name() const { return name_; }

private:
    int w_ = 1;                                     // 기본 멤버 초기자
    std::string name_ = "기본값";                   // 리스트가 적히면 진다
    int area_ = 1;
    const int limit_ = 100;                         // const 멤버 — 리스트나 기본값으로만
};

int main() {
    Widget a;
    Widget b(3, "셋짜리");
    std::printf("a=%s(%d)  b=%s(%d)\n",
                a.name().c_str(), a.area(), b.name().c_str(), b.area());
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic ctor12.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a=이름 없음(0)  b=셋짜리(9)
```

### 규칙

- **초기화 리스트는 본문보다 먼저** 돈다. 본문이 시작될 때 **멤버는 이미 전부 지어져 있다.**
- **멤버는 선언 순서로 초기화되고, 파괴는 그 역순**이다. 리스트에 적은 순서는 **아무 영향이 없다.**
- **`const` 멤버·참조 멤버는 초기화 리스트나 기본 멤버 초기자로만** 값을 받는다.
- **리스트에 적힌 멤버는 기본 멤버 초기자를 무시**하고, 기본 멤버 초기자는 **평가되지도 않는다.**
- **위임 생성자는 본체가 끝난 뒤 본문을 돌린다.** 그 시점부터 객체는 **지어진 것**이다.
- **`explicit` 은 암묵 변환과 복사 초기화를 막는다.** 직접 초기화(`T x(a)` · `T x{a}`)는 그대로 된다.
- **사용자가 소멸자·복사 생성자·복사 대입 중 하나라도 적으면 이동 연산은 생성되지 않는다.**

### 금지 사례 — 일곱 줄이 각각 막힌다

```text
===== 소스: ctor13.cpp =====
// 생성자에서 막히는 것을 한 파일에 모았다
#include <string>
struct A { const int c; int& r; int t = 0; A() { c = 1; r = t; } };
struct B { int v; explicit B(int x) : v(x) {} };
struct C { int v; C(C&&) noexcept = default; };
struct D { int v = 0; D(const D&) = delete; };

void takeB(B) {}
void takeD(D) {}

int main() {
    A a;                 // const·참조 멤버를 본문에서 대입
    takeB(3);            // explicit 생성자를 암묵 변환으로
    C c;                 // 이동 생성자를 적었으니 기본 생성자가 없다
    D d1;
    D d2 = d1;           // 복사가 지워져 있다
    (void)a; (void)c; (void)d2;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ctor13.cpp -o ex (cc exit=1) =====
ctor13.cpp: In constructor ‘A::A()’:
ctor13.cpp:3:44: error: uninitialized const member in ‘const int’ [-fpermissive]
    3 | struct A { const int c; int& r; int t = 0; A() { c = 1; r = t; } };
      |                                            ^
ctor13.cpp:3:22: note: ‘const int A::c’ should be initialized
    3 | struct A { const int c; int& r; int t = 0; A() { c = 1; r = t; } };
      |                      ^
ctor13.cpp:3:44: error: uninitialized reference member in ‘int&’ [-fpermissive]
    3 | struct A { const int c; int& r; int t = 0; A() { c = 1; r = t; } };
      |                                            ^
ctor13.cpp:3:30: note: ‘int& A::r’ should be initialized
    3 | struct A { const int c; int& r; int t = 0; A() { c = 1; r = t; } };
      |                              ^
ctor13.cpp:3:52: error: assignment of read-only member ‘A::c’
    3 | struct A { const int c; int& r; int t = 0; A() { c = 1; r = t; } };
      |                                                  ~~^~~
ctor13.cpp: In function ‘int main()’:
ctor13.cpp:13:11: error: could not convert ‘3’ from ‘int’ to ‘B’
   13 |     takeB(3);            // explicit 생성자를 암묵 변환으로
      |           ^
      |           |
      |           int
ctor13.cpp:14:7: error: no matching function for call to ‘C::C()’
   14 |     C c;                 // 이동 생성자를 적었으니 기본 생성자가 없다
      |       ^
ctor13.cpp:5:19: note: candidate: ‘constexpr C::C(C&&)’
    5 | struct C { int v; C(C&&) noexcept = default; };
      |                   ^
ctor13.cpp:5:19: note:   candidate expects 1 argument, 0 provided
ctor13.cpp:15:7: error: no matching function for call to ‘D::D()’
   15 |     D d1;
      |       ^~
ctor13.cpp:6:23: note: candidate: ‘D::D(const D&)’ (deleted)
    6 | struct D { int v = 0; D(const D&) = delete; };
      |                       ^
ctor13.cpp:6:23: note:   candidate expects 1 argument, 0 provided
ctor13.cpp:16:12: error: use of deleted function ‘D::D(const D&)’
   16 |     D d2 = d1;           // 복사가 지워져 있다
      |            ^~
ctor13.cpp:6:23: note: declared here
    6 | struct D { int v = 0; D(const D&) = delete; };
      |                       ^
```

- ★ **일곱 에러가 이 주제의 규칙 넷에 대응한다** — `const`·참조 멤버 · `explicit` · 이동만 적어 사라진 기본 생성자 · `= delete`.
- ★★ **`D d1;` 도 막힌다** — 복사 생성자를 `= delete` 로 **적은 것 자체가** 「사용자가 적은 생성자」라\
  **기본 생성자가 더는 자동으로 생기지 않는다.** 이 한 줄이 0/3/5의 법칙(목록의 **18번 주제**)의 입구다.

## 어디서 틀리나

### 1. ★★★ 「리스트나 본문이나 같다」

- ★ **다르다.** 본문 대입은 **기본 생성 1회를 더** 낸다((1)).
- ★★ **멤버가 기본 생성될 수 없으면**(`const`·참조·기본 생성자가 없는 타입) **본문 대입은 아예 컴파일되지 않는다**((6)).

### 2. ★★★ 「리스트에 적은 순서대로 초기화된다」

- ★ **선언 순서다**((2)). 리스트 순서는 **경고만 낳는다.**
- **고치는 법은 선언 순서를 의도한 순서로 바꾸는 것**이지, 리스트를 다시 배열하는 것이 아니다.

### 3. ★★ 「`-Wreorder` 경고는 스타일 지적이다」

- ★ **(3)의 버그가 바로 그 경고 옆에서 난다.** `-Wreorder` 와 `-Wuninitialized` 가 **함께** 나오면 **실제 버그**다.

### 4. ★ 「`= default` 는 아무 일도 안 한다」

- ★ **멤버의 기본 생성자가 돈다**((1)의 마지막 줄 — 기본 생성 1회).
- **`= default` 를 적는 것과 아예 안 적는 것도 다르다** — 다른 특수 멤버를 적었을 때 **이동이 남느냐**가 갈린다((7)).

### 5. ★★ 「`std::is_move_constructible_v` 가 참이면 이동이 있다」

- ★ **아니다.** 이동이 없어도 **복사 생성자가 rvalue 를 받으므로** 그 특성은 참이 된다((7)).
- ★★ **답은 계수로만 난다** — 옮겨 보고 **복사가 돌았는지** 본다.

### 6. ★ 「`explicit` 은 `{}` 초기화를 막는다」

- ★ **직접 리스트 초기화(`Feet c{5}`)는 된다.** 막히는 것은 **복사 리스트 초기화(`Feet b = {5}`)** 다((문법)의 금지 사례).

### 7. ★★ 「빌드가 통과하니 표준에 맞다」

- ★ **`-fpermissive` 한 줄이 그 전제를 무너뜨린다**((8)). **`-pedantic-errors` 로도 안 살아난다.**

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★ **이 주제도 「표준」 칸이 압도적으로 두껍다** — 초기화 규칙은 **전부 표준이 정해 놓은 것**이고,\
UB 는 **(3) 하나**뿐이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★ **본체** — 리스트가 본문보다 먼저 도는 것 · **선언 순서 초기화** · **`const`·참조 멤버는 리스트로만** · 리스트가 기본 멤버 초기자를 이기는 것(그리고 **평가조차 안 되는 것**) · **위임 생성자의 순서와 「지어진 것」 경계** · `explicit` 이 막는 자리 · **특수 멤버 생성 규칙**(소멸자를 적으면 이동이 안 생긴다) | 로그 순서 · 호출 횟수 · 진단 전문 + `cc exit` | ★★ **의도한 순서인지** — 선언 순서를 바꿔 버그를 만들어도 **경고가 없을 수 있다**(대입 순서를 안 거스르면) |
| **조건부 표준** | 특정 조건에서만 보장 | ★ **위임 생성자·기본 멤버 초기자·`=default`/`=delete` 는 C++11부터** · `explicit` 과 `{}` 의 상호작용은 C++17\~20 에서 다듬였다 | `-std=c++20` 으로만 돌렸다 | ★ **이 문서는 C++98·C++11 로 안 돌려 봤다** |
| **구현 정의** | 문서화 의무가 있다 | ★ **진단 문구와 경고 이름**(g++ `-Wreorder` · clang `-Wreorder-ctor`) · **경고 개수**(같은 사건에 g++ 3 · clang 1) · **`-fpermissive` 의 존재 자체** | 경고 개수 블록((8)) | ★★ **「경고 N건」은 컴파일러를 안 밝히면 뜻이 없다** |
| **미명시** | 몇 가지 중 하나 | ★ **복사 생략이 어디까지 일어나나** — 이 문서의 계수는 **기본 최적화 판**의 것이다 | `-O0` 과 `-O2` 를 (3)에서만 갈라 돌렸다 | ★ 다른 최적화 수준에서 횟수가 달라질 수 있다 |
| **UB** | 아무 일이나 | ★★ **하나뿐이다** — **초기화 전 멤버를 읽는 것**((3), [12번](../12-class-basics-members-access-and-this/) (6)과 같은 사건) | 약속이 깨졌다는 비교 결과(**0**, `-O0`·`-O2` 둘 다) + `-Wuninitialized` | ★★★ **같은 UB 를 기본 멤버 초기자에서 쓰면 g++ 는 침묵한다**([12번](../12-class-basics-members-access-and-this/) (6)) |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | `-fpermissive` | 무엇이 잡나 |
|---|---|---|---|---|---|
| `const`·참조 멤버 미초기화 | 표준 | **error** | **error** | ★★★ **경고 · exit 0** | ★ 기본 플래그만 |
| `static const double` 초기화 | 표준 | **error** | **error** | ★★★ **경고 · exit 0** | ★ 기본 플래그만 |
| 리스트 순서 ≠ 선언 순서 | 표준 | **경고 3건** | **경고 1건** | 경고 | ★ 둘 다 본다(개수만 다르다) |
| 초기화 전 멤버 읽기(리스트) | **UB** | **경고 5건** | **경고 2건** | 경고 | ★ 둘 다 본다 |
| 초기화 전 멤버 읽기(기본 멤버 초기자) | **UB** | ★★★ **0건** | ★ **1건** | 0건 | ★★ **clang 만** |
| `explicit` 을 빠뜨린 설계 | 표준 | **0건** | **0건** | 0건 | ★★★ **아무 도구도 못 본다** |
| 본문 대입으로 두 번 손대는 것 | 표준 | **0건** | **0건** | 0건 | ★★★ **계수기만** |

- ★★ **이 표의 결론 세 줄**
  - **초기화 규칙 위반은 대부분 에러로 막힌다** — 단, **`-fpermissive` 가 그 둘을 통과시킨다.**
  - **초기화 순서 함정은 경고로만 나오고 개수가 컴파일러마다 다르다.**
  - **「두 번 손댔다」는 어떤 컴파일러도 말해 주지 않는다** — **①의 계수기만 본다.**

### ★ 진단이 0줄인 것도 블록으로 받았다

「경고가 안 났다」를 산문으로 적으면 **안 물어본 것과 물었는데 조용한 것이 구분되지 않는다.**\
그래서 플래그·컴파일러마다 물어 개수를 찍었다((8)의 마지막 블록).\
**탐침 5개 중 g++ 3개 · clang 2개**가 답했고, **아무도 답하지 않은 탐침**(본문 대입의 두 번 손대기 · `explicit` 누락)은\
**위 표의 마지막 두 줄**로 따로 적어 두었다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 멤버에 처음부터 값이 있다 | **초기화 리스트** | 한 번에 지어진다((1)) |
| 값을 계산해야 하고 여러 줄이 든다 | **본문**(단, 멤버는 리스트에서 지어 둔다) | 리스트 안에 긴 식을 우겨넣지 않는다 |
| 모든 생성자가 같은 기본값을 쓴다 | **기본 멤버 초기자** | 생성자마다 되풀이하지 않는다((5)) |
| 생성자 여럿이 같은 초기화를 한다 | **위임 생성자** | 중복이 사라진다((4)) |
| 한 번 정하면 안 바뀌는 값 | **`const` 멤버** | 리스트로만 된다 — **대신 복사 대입이 사라진다**((6)) |
| 인자 하나짜리 생성자 | **`explicit`** | 암묵 변환은 **고칠 때가 아니라 읽을 때** 문제가 된다 |
| 특수 멤버를 하나라도 적었다 | **나머지도 명시**(`= default`/`= delete`) | 이동이 조용히 사라지는 것을 막는다((7)) |

- ★ **「리스트가 항상 낫다」가 아니다** — 계산이 길면 **가독성**이 먼저다. 다만 그때도 **멤버는 리스트에서 지어 둔다.**
- ★★ **`const` 멤버는 공짜가 아니다** — 그 타입은 **대입할 수 없는 타입**이 되고, `std::vector` 에 넣으면 그 순간 막힌다.

## 핵심 문장

- **초기화 리스트는 한 번, 본문 대입은 두 번 손댄다** — 세면 나온다.
- **멤버는 선언 순서로 초기화된다.** 리스트 순서는 경고만 낳는다.
- **`const` 멤버와 참조 멤버는 리스트로만 값을 받는다** — 본문이 시작될 때는 이미 늦었다.
- **위임 생성자의 본체가 끝나면 객체는 지어진 것**이고, 그 뒤에 던지면 **소멸자가 돈다.**
- **소멸자 하나를 적으면 이동 연산이 사라진다** — 그 사실은 **특성이 아니라 계수로만** 드러난다.
- **`-fpermissive` 는 ill-formed 를 통과시키고 `-pedantic-errors` 로도 안 살아난다.**

## 관련 자료

- [12번](../12-class-basics-members-access-and-this/) — **클래스라는 그릇**. (6)의 `lazy` 가 여기 (2)에서 풀린다.
- [14번](../14-destructors-and-deterministic-destruction/) — **파괴 순서는 초기화의 역순**이다. (2)의 로그가 거기서 이어진다.
- [15번](../15-raii-resources-as-types/) — **생성자가 완주하지 못하면 소멸자가 안 돈다.** (4)의 경계가 거기서 결론이 된다.
- 형제 [`04번`](../04-brace-initialization-narrowing-and-initializer-list/) — `{}` 초기화와 좁히기. `Feet c{5}` 가 되는 이유는 거기.
- 형제 [`09번`](../09-rvalue-references-move-and-forward/) — `std::move` 가 무엇인가. (1)의 `std::move(p)` 는 거기가 정본.
- 형제 [`11번`](../11-choosing-parameter-passing/) — **`Probe` 계수 방식을 여기서 이어받았다.** 「값으로 받을까」의 정본.
- 러스트 갈래 [`16-structs-impl-and-associated-functions/`](../../../rust/syntax/16-structs-impl-and-associated-functions/) — 러스트에는 **생성자가 없다.**\
  `Struct { a: 1, b: 2 }` 로 **모든 필드를 한 번에 적어야** 하므로 **「초기화 순서」라는 함정이 원리적으로 없다.**
- C 갈래 [`21-struct-declaration-initialization-and-designated-initializers/`](../../../c/syntax/21-struct-declaration-initialization-and-designated-initializers/) — C 의 지정 초기자.\
  **C++20 은 지정 초기자를 선언 순서로만 허용**한다 — 이 주제의 「선언 순서」 규칙이 거기까지 뻗는다.

## 용어 풀이

> **생성자(constructor)** — 객체가 만들어질 때 도는 특수 멤버 함수. 반환 타입이 없다.\
> 예: `Widget(int w) : w_(w) {}`

> **멤버 초기화 리스트(member initializer list)** — 생성자 이름 뒤 `:` 부터 본문 `{` 까지의 목록.\
> 예: `Widget() : a_(1), b_(2) {}` — 본문이 돌기 전에 `a_`·`b_` 가 지어진다.

> **기본 멤버 초기자(default member initializer)** — 멤버 선언에 붙인 초기값.\
> 예: `int n = 1;` — 리스트에 `n` 이 적히면 **이쪽은 평가조차 되지 않는다.**

> **위임 생성자(delegating constructor)** — 초기화 리스트에서 **같은 클래스의 다른 생성자**를 부르는 생성자.\
> 예: `Widget() : Widget(0, "") {}`

> **`explicit`** — 암묵 변환과 복사 초기화를 막는 지정자.\
> 예: `explicit Feet(int)` 이면 `Feet f = 5;` 가 막히고 `Feet f(5);` 는 된다.

> **`= default`** — 컴파일러가 만들어 줄 정의를 **명시적으로 요구**하는 것.\
> 예: `Widget(const Widget&) = default;`

> **`= delete`** — 그 함수를 **부르면 에러가 나도록** 지우는 것.\
> 예: `Widget(const Widget&) = delete;` — 복사하려 들면 컴파일에서 막힌다.

> **특수 멤버 함수(special member function)** — 기본 생성자·복사 생성자·이동 생성자·복사 대입·이동 대입·소멸자 여섯.\
> 예: 소멸자를 적으면 **이동 둘이 생성되지 않는다.**

> **미정 값(indeterminate value)** — 초기화되지 않은 객체가 가진 것. **읽는 것 자체가 UB** 다.\
> 예: (3)의 `Trap::n` — 그래서 이 문서는 그 값을 싣지 않는다.

> **`-fpermissive`** — GCC 가 **일부 ill-formed 코드를 에러가 아닌 경고로 낮추는** 플래그.\
> 예: 초기화되지 않은 `const` 멤버가 경고가 되고 **`cc exit=0`** 이 된다.

## 더 들어가면

- **0/3/5의 법칙** — (7)에서 본 「하나를 적으면 나머지도 따져야 한다」를 규칙으로 세운 것. 정본은 목록의 **18번 주제**.
- **복사 생략(copy elision)과 보장된 생략** — C++17 부터 prvalue 초기화에서 **복사·이동이 아예 일어나지 않는다.** 형제 [`08번`](../08-value-categories-lvalue-prvalue-xvalue/)이 그 정본이고, (1)의 계수가 그 영향을 받는다.
- **집합체 초기화(aggregate initialization)** — 생성자를 하나도 안 적으면 `Widget w{1, 2}` 로 멤버를 직접 채울 수 있다. 형제 [`04번`](../04-brace-initialization-narrowing-and-initializer-list/).
- **`constexpr` 생성자** — 컴파일 시간에 도는 생성자. 정본은 목록의 **38번 주제**.
