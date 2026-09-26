# cpp/syntax/19 — 상속·가상 함수·`override`/`final` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **javac 21.0.5** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이므로 **출력을 싣는 블록마다 그 출력을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **ASan 의 PID·주소** · **g++ vtable 덤프의 주소** · **진단 문구** ·\
> **`typeid(...).name()` 의 꾸밈 형식**이다.\
> 근거로 쓰는 것은 다음이다 — **어느 함수가 불렸나** · **소멸자 호출 횟수와 놓은 바이트** ·\
> **vtable 항목 수와 그 자리의 이름** · **`sizeof`** · **`cc exit`/`run exit`** · **경고·에러 개수**.
> ★★★ **이 문서는 시간을 재지 않았다.** 「가상 호출이 느리다」는 문장이 **한 줄도 없다** —\
> 8번이 본 것은 **구조**이지 비용이 아니다. 비용의 정본은 목록의 **21번 주제**다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **다르다** — `1B` 와 `1D` 이고, `(3)` 과 `(4)` 는 **이름이 답을 정한다**

**출력**

```cpp
/* virt01.cpp */
// 정적 타입 대 동적 타입 — typeid 와 호출 결과를 나란히 찍는다
#include <cstdio>
#include <typeinfo>

struct B {
    virtual void who() const { std::printf("      B::who   (가상)\n"); }
    void plain()       const { std::printf("      B::plain (비가상)\n"); }
    virtual ~B() = default;
};
struct D : B {
    void who() const override { std::printf("      D::who   (가상)\n"); }
    void plain()       const { std::printf("      D::plain (비가상)\n"); }
};

int main() {
    D d;
    B& r = d;                                  // 정적 타입 B& · 동적 타입 D
    B* p = &d;
    D* q = &d;

    std::printf("(1) 이름이 말하는 타입과 물건이 말하는 타입\n");
    std::printf("    typeid(decltype(r)) — 정적 타입 : %s\n", typeid(decltype(r)).name());
    std::printf("    typeid(r)           — 동적 타입 : %s\n", typeid(r).name());
    std::printf("    typeid(*p)                      : %s\n", typeid(*p).name());
    std::printf("    typeid(p)  — 포인터 자신        : %s\n", typeid(p).name());

    std::printf("(2) 가상 함수를 기반 참조로 부른다 — 어느 쪽이 도나\n");
    r.who();
    std::printf("(3) 비가상 함수를 기반 참조로 부른다\n");
    r.plain();
    std::printf("(4) 같은 비가상 함수를 파생 포인터로 부른다\n");
    q->plain();
    std::printf("(5) 같은 물건인가: &r == &d 는 %d · p == q 는 %d\n",
                (int)(&r == &d), (int)(p == static_cast<B*>(q)));
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic virt01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 이름이 말하는 타입과 물건이 말하는 타입
    typeid(decltype(r)) — 정적 타입 : 1B
    typeid(r)           — 동적 타입 : 1D
    typeid(*p)                      : 1D
    typeid(p)  — 포인터 자신        : P1B
(2) 가상 함수를 기반 참조로 부른다 — 어느 쪽이 도나
      D::who   (가상)
(3) 비가상 함수를 기반 참조로 부른다
      B::plain (비가상)
(4) 같은 비가상 함수를 파생 포인터로 부른다
      D::plain (비가상)
(5) 같은 물건인가: &r == &d 는 1 · p == q 는 1
```

**왜 그런가**

- ★★★ **`typeid(decltype(r))` 는 `1B`, `typeid(r)` 은 `1D`** 다.\
  ★ 앞엣것은 **타입을 묻는 것**(컴파일 시간)이라 **정적 타입**을,\
  뒤엣것은 **다형적 타입의 객체를 묻는 것**이라 **동적 타입**을 답한다. **같은 `r` 인데 답이 둘**이다.
- ★★ **`typeid(*p)` 는 `1D`** 다 — 역참조하면 객체이므로 동적 타입이 나온다.\
  ★ **`typeid(p)` 는 `P1B`**(= `B*`)다. **포인터 자신은 다형적 타입이 아니다.**
- ★★★ **`(2)` 는 `D::who`, `(3)` 은 `B::plain`, `(4)` 는 `D::plain`** 이다.
  - `(2)` — **가상 함수**라 동적 타입이 고른다.
  - `(3)`·`(4)` — **비가상 함수**라 **정적 타입**이 고른다. `B&` 로 부르면 `B`, `D*` 로 부르면 `D`.
- ★★★ **`(3)` 과 `(4)` 는 같은 객체다** — `(5)` 가 주소로 확인한다(`1` · `1`).\
  ★ **객체는 하나인데 결과가 둘**이다. 「무엇을 통해 불렀나」가 답을 정하기 때문이다.
- ★ **`1B`·`1D` 는 Itanium ABI 의 꾸민 이름**이다. 근거는 「**둘이 다르다**」는 사실이지 그 글자가 아니다.
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic virt01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 이름이 말하는 타입과 물건이 말하는 타입
    typeid(decltype(r)) — 정적 타입 : 1B
    typeid(r)           — 동적 타입 : 1D
    typeid(*p)                      : 1D
    typeid(p)  — 포인터 자신        : P1B
(2) 가상 함수를 기반 참조로 부른다 — 어느 쪽이 도나
      D::who   (가상)
(3) 비가상 함수를 기반 참조로 부른다
      B::plain (비가상)
(4) 같은 비가상 함수를 파생 포인터로 부른다
      D::plain (비가상)
(5) 같은 물건인가: &r == &d 는 1 · p == q 는 1
```

### 2. ★★★ **에러 4건**이다 — `override` 를 지우면 **③만 남고 셋은 통과**한다

**출력**

```cpp
/* virt02.cpp */
// override 가 잡는 실수 넷 — const 다름 · 인자 다름 · 반환 다름 · 이름 오타
struct B {
    virtual void f() const {}
    virtual void g(int) {}
    virtual int  h() { return 0; }
    virtual void name() {}
    virtual ~B() = default;
};
struct D : B {
    void f() override {}              // 1. const 를 빠뜨렸다
    void g(long) override {}          // 2. 인자 타입이 다르다
    long h() override { return 0; }   // 3. 반환 타입이 다르다
    void nane() override {}           // 4. 이름을 잘못 적었다
};
int main() { D d; (void)d; }
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 virt02.cpp -o ex (cc exit=1) =====
virt02.cpp:10:10: error: ‘void D::f()’ marked ‘override’, but does not override
   10 |     void f() override {}              // 1. const 를 빠뜨렸다
      |          ^
virt02.cpp:11:10: error: ‘void D::g(long int)’ marked ‘override’, but does not override
   11 |     void g(long) override {}          // 2. 인자 타입이 다르다
      |          ^
virt02.cpp:12:10: error: conflicting return type specified for ‘virtual long int D::h()’
   12 |     long h() override { return 0; }   // 3. 반환 타입이 다르다
      |          ^
virt02.cpp:5:18: note: overridden function is ‘virtual int B::h()’
    5 |     virtual int  h() { return 0; }
      |                  ^
virt02.cpp:13:10: error: ‘void D::nane()’ marked ‘override’, but does not override
   13 |     void nane() override {}           // 4. 이름을 잘못 적었다
      |          ^~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 virt02.cpp -o ex (cc exit=1) =====
virt02.cpp:10:14: error: non-virtual member function marked 'override' hides virtual member function
   10 |     void f() override {}              // 1. const 를 빠뜨렸다
      |              ^
virt02.cpp:3:18: note: hidden overloaded virtual function 'B::f' declared here: different qualifiers ('const' vs unqualified)
    3 |     virtual void f() const {}
      |                  ^
virt02.cpp:11:18: error: non-virtual member function marked 'override' hides virtual member function
   11 |     void g(long) override {}          // 2. 인자 타입이 다르다
      |                  ^
virt02.cpp:4:18: note: hidden overloaded virtual function 'B::g' declared here: type mismatch at 1st parameter ('int' vs 'long')
    4 |     virtual void g(int) {}
      |                  ^
virt02.cpp:12:10: error: virtual function 'h' has a different return type ('long') than the function it overrides (which has return type 'int')
   12 |     long h() override { return 0; }   // 3. 반환 타입이 다르다
      |     ~~~~ ^
virt02.cpp:5:18: note: overridden virtual function is here
    5 |     virtual int  h() { return 0; }
      |             ~~~  ^
virt02.cpp:13:17: error: only virtual member functions can be marked 'override'
   13 |     void nane() override {}           // 4. 이름을 잘못 적었다
      |                 ^~~~~~~~
4 errors generated.
```

**왜 그런가**

| 심은 실수 | 무엇이 다른가 | `override` 를 지우면 |
|---|---|---|
| ① `void f() override` | ★★ **`const` 를 빠뜨렸다** | **새 비가상 함수가 생긴다**(컴파일된다) |
| ② `void g(long) override` | ★★ **인자 타입이 `int` → `long`** | **새 가상 함수가 생긴다**(컴파일된다) |
| ③ `long h() override` | ★★ **반환 타입이 `int` → `long`** | ★★★ **여전히 에러다** — 반환 타입 충돌은 별도 규칙 |
| ④ `void nane() override` | ★★ **이름 오타** | **새 함수가 생긴다**(컴파일된다) |

- ★★★ **두 컴파일러 다 네 건을 전부 짚고 `cc exit=1`** 이다.
- ★★★ **`override` 를 지우면 ①②④가 조용히 통과한다.** 그것이 (12)의 탐침 1\~4번이 실측한 것이다.\
  ★ **③만 예외**다 — 같은 시그니처인데 반환 타입만 다른 것은 **`override` 없이도 ill-formed** 다.

★★★ **같은 파일에서 `override` 만 전부 지우면 무엇이 남나.**

```cpp
/* virt15.cpp */
// virt02.cpp 에서 override 만 전부 지웠다 — 몇 개가 통과하나
struct B {
    virtual void f() const {}
    virtual void g(int) {}
    virtual int  h() { return 0; }
    virtual void name() {}
    virtual ~B() = default;
};
struct D : B {
    void f() {}                       // 1. const 를 빠뜨렸다
    void g(long) {}                   // 2. 인자 타입이 다르다
    long h() { return 0; }            // 3. 반환 타입이 다르다
    void nane() {}                    // 4. 이름을 잘못 적었다
};
int main() { D d; (void)d; }
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 virt15.cpp -o ex (cc exit=1) =====
virt15.cpp:12:10: error: conflicting return type specified for ‘virtual long int D::h()’
   12 |     long h() { return 0; }            // 3. 반환 타입이 다르다
      |          ^
virt15.cpp:5:18: note: overridden function is ‘virtual int B::h()’
    5 |     virtual int  h() { return 0; }
      |                  ^
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 virt15.cpp -o ex (cc exit=1) =====
virt15.cpp:12:10: error: virtual function 'h' has a different return type ('long') than the function it overrides (which has return type 'int')
   12 |     long h() { return 0; }            // 3. 반환 타입이 다르다
      |     ~~~~ ^
virt15.cpp:5:18: note: overridden virtual function is here
    5 |     virtual int  h() { return 0; }
      |             ~~~  ^
virt15.cpp:10:10: warning: 'D::f' hides overloaded virtual function [-Woverloaded-virtual]
   10 |     void f() {}                       // 1. const 를 빠뜨렸다
      |          ^
virt15.cpp:3:18: note: hidden overloaded virtual function 'B::f' declared here: different qualifiers ('const' vs unqualified)
    3 |     virtual void f() const {}
      |                  ^
virt15.cpp:11:10: warning: 'D::g' hides overloaded virtual function [-Woverloaded-virtual]
   11 |     void g(long) {}                   // 2. 인자 타입이 다르다
      |          ^
virt15.cpp:4:18: note: hidden overloaded virtual function 'B::g' declared here: type mismatch at 1st parameter ('int' vs 'long')
    4 |     virtual void g(int) {}
      |                  ^
2 warnings and 1 error generated.
```

- ★★★ **에러가 넷에서 하나로 줄어든다.** 남는 것은 **③(반환 타입)** 뿐이다 —\
  **같은 시그니처인데 반환 타입만 다른 것은 `override` 없이도 ill-formed** 이기 때문이다.
- ★★★ **①②④는 통과한다** — `override` 가 **넷 중 셋을 혼자 잡고 있었다**는 뜻이다.
- ★★ **두 컴파일러가 갈린다** — clang 은 ①②에 `-Woverloaded-virtual` **경고 2건**을 더 내는데 **g++ 는 이 파일에서 0건**이다.\
  ★ g++ 가 그 경고를 못 내는 것은 아니다 — **③을 지운 판에서는 g++ 도 경고 2건**이었다(같은 플래그).\
  **에러가 있는 번역 단위에서 그 경고를 안 내는 것**으로 보인다. ★ 근거는 **두 판의 경고 개수 2 대 0**이다.
- ★★ **clang 이 이유를 더 짚어 준다** — ①에 `different qualifiers ('const' vs unqualified)`,\
  ②에 `type mismatch at 1st parameter ('int' vs 'long')`.\
  ★ g++ 는 ①②④에 **같은 문구**를 쓴다. **진단 문구는 구현 정의**이므로 근거는 **에러 개수**와 진단의 `(행,열)` 둘이다.
- ★★★ **그래서 규칙은 하나다** — **재정의하면 반드시 `override` 를 적는다.**

### 3. ★★★ 이름은 **언제나 `D::f`** 인데 `x` 는 **1 · 2 · 1 · 9 · 2**

**출력**

```cpp
/* virt03.cpp */
// 기본 인자는 정적 타입이 정하고, 함수 본체는 동적 타입이 정한다
#include <cstdio>

struct B {
    virtual void f(int x = 1) { std::printf("      B::f  x=%d\n", x); }
    virtual ~B() = default;
};
struct D : B {
    void f(int x = 2) override { std::printf("      D::f  x=%d\n", x); }
};

int main() {
    D d;
    B* p = &d;
    D* q = &d;
    B& r = d;
    std::printf("(1) B* 로 부른다   p->f();\n");  p->f();
    std::printf("(2) D* 로 부른다   q->f();\n");  q->f();
    std::printf("(3) B& 로 부른다   r.f();\n");   r.f();
    std::printf("(4) 인자를 직접 준다 p->f(9);\n"); p->f(9);
    std::printf("(5) 파생 객체로 직접  d.f();\n");  d.f();
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic virt03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) B* 로 부른다   p->f();
      D::f  x=1
(2) D* 로 부른다   q->f();
      D::f  x=2
(3) B& 로 부른다   r.f();
      D::f  x=1
(4) 인자를 직접 준다 p->f(9);
      D::f  x=9
(5) 파생 객체로 직접  d.f();
      D::f  x=2
```

**왜 그런가**

| 호출 | 찍히는 이름 | `x` | 무엇이 정했나 |
|---|---|---|---|
| `p->f()`(`B*`) | `D::f` | **1** | 이름은 **동적 타입**, 인자는 **정적 타입 `B`** |
| `q->f()`(`D*`) | `D::f` | **2** | 인자는 **정적 타입 `D`** |
| `r.f()`(`B&`) | `D::f` | **1** | 인자는 **정적 타입 `B`** |
| `p->f(9)` | `D::f` | **9** | 직접 줬다 |
| `d.f()`(`D`) | `D::f` | **2** | 인자는 **정적 타입 `D`** |

- ★★★ **한 호출에서 두 타입이 각각 일한다.** **본체는 동적 타입이, 기본 인자는 정적 타입이** 정한다.
- ★★★ **기본 인자는 컴파일 시간에 호출 자리에 끼워 넣어진다.**\
  ★ 8번의 vtable 덤프가 그것을 확인해 준다 — **vtable 에는 함수 주소만** 있고 **기본 인자는 없다.**
- ★★★ **처방은 하나다** — **가상 함수에 기본 인자를 주지 않는다.**\
  ★ 꼭 필요하면 **비가상 함수가 기본 인자를 갖고** 가상 함수를 부르게 한다.
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic virt03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) B* 로 부른다   p->f();
      D::f  x=1
(2) D* 로 부른다   q->f();
      D::f  x=2
(3) B& 로 부른다   r.f();
      D::f  x=1
(4) 인자를 직접 준다 p->f(9);
      D::f  x=9
(5) 파생 객체로 직접  d.f();
      D::f  x=2
```

### 4. ★★ **`D::f(double)` 로 간다** — 에러가 아니라 **변환되어 통과**한다

**출력**

```cpp
/* virt04.cpp */
// 이름 숨김 — 파생이 같은 이름을 하나만 선언해도 기반의 오버로드가 통째로 가려진다
#include <cstdio>

struct B {
    void f(int)         { std::printf("      B::f(int)\n"); }
    void f(const char*) { std::printf("      B::f(const char*)\n"); }
};
struct D : B {                         // 기반의 f 둘이 가려진다
    void f(double) { std::printf("      D::f(double)\n"); }
};
struct E : B {                         // using 으로 되살린다
    using B::f;
    void f(double) { std::printf("      E::f(double)\n"); }
};

int main() {
    D d; E e;
    std::printf("(1) D 에 정수를 준다      d.f(1);\n");   d.f(1);
    std::printf("(2) E 에 정수를 준다      e.f(1);\n");   e.f(1);
    std::printf("(3) E 에 문자열을 준다    e.f(\"x\");\n"); e.f("x");
    std::printf("(4) D 에 double 을 준다   d.f(1.5);\n"); d.f(1.5);
    std::printf("(5) 가려진 것을 이름으로 불러낸다 d.B::f(1);\n"); d.B::f(1);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic virt04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) D 에 정수를 준다      d.f(1);
      D::f(double)
(2) E 에 정수를 준다      e.f(1);
      B::f(int)
(3) E 에 문자열을 준다    e.f("x");
      B::f(const char*)
(4) D 에 double 을 준다   d.f(1.5);
      D::f(double)
(5) 가려진 것을 이름으로 불러낸다 d.B::f(1);
      B::f(int)
```

**왜 그런가**

- ★★★ **이름 조회는 「찾으면 멈춘다」.** `D` 에서 `f` 를 찾았으므로 **기반은 안 본다.**\
  ★ **그다음에** 오버로드 해결이 돌지만 **후보가 `D::f(double)` 하나뿐**이다.\
  `1` 이 `double` 로 변환되어 **조용히 통과한다.** 에러가 아니라서 더 나쁘다.
- ★★ **`using B::f;` 한 줄**이 기반의 둘을 파생의 오버로드 집합에 끌어온다.\
  그래서 `E` 에서는 `e.f(1)` 이 `B::f(int)`, `e.f("x")` 가 `B::f(const char*)` 로 제대로 갈린다.
- ★★★ **이 예제의 `f` 들 중 가상인 것은 하나도 없다.**\
  ★ **이름 숨김은 `virtual` 과 무관하다** — 이름 조회는 디스패치보다 **앞 단계**에서 일어나는 일이다.\
  정본은 [1번](../01-function-overloading-and-overload-resolution/).
- ★★ `(5)` 처럼 **이름으로 직접 부를 수도 있다**(`d.B::f(1)`) — 다만 그것은 **가상 디스패치를 끄는 것**이기도 하다.

**변환이 안 되면 에러가 된다**

```cpp
/* virt05.cpp */
// 이름 숨김이 에러가 되는 자리 — 문자열은 double 로 안 바뀐다
struct B { void f(int); void f(const char*); };
struct D : B { void f(double); };
int main() { D d; d.f("x"); }
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 virt05.cpp -o ex (cc exit=1) =====
virt05.cpp: In function ‘int main()’:
virt05.cpp:4:23: error: cannot convert ‘const char [2]’ to ‘double’
    4 | int main() { D d; d.f("x"); }
      |                       ^~~
      |                       |
      |                       const char [2]
virt05.cpp:3:23: note:   initializing argument 1 of ‘void D::f(double)’
    3 | struct D : B { void f(double); };
      |                       ^~~~~~
```

- ★★★ **진단이 기반의 `f(const char*)` 를 아예 언급하지 않는다.**\
  `초기화 인자 1` 로 가리키는 것이 **`void D::f(double)` 하나뿐**이다 — **기반은 후보에 없다.**\
  ★ 「왜 있는 함수를 못 찾지?」의 답이 여기 있다.

### 5. ★ **각 2건**씩이다 — 「파생이니까 괜찮다」가 틀린다

**출력**

```cpp
/* virt06.cpp */
// final 이 막는 것 둘 — 클래스를 더 못 물려받는 것과 함수를 더 못 덮는 것
struct Sealed final { };
struct Try : Sealed { };                       // 1. final 클래스를 상속했다

struct B { virtual void f() final {} virtual ~B() = default; };
struct D : B { void f() override {} };         // 2. final 함수를 덮었다
int main() { }
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 virt06.cpp -o ex (cc exit=1) =====
virt06.cpp:3:8: error: cannot derive from ‘final’ base ‘Sealed’ in derived type ‘Try’
    3 | struct Try : Sealed { };                       // 1. final 클래스를 상속했다
      |        ^~~
virt06.cpp:6:21: error: virtual function ‘virtual void D::f()’ overriding final function
    6 | struct D : B { void f() override {} };         // 2. final 함수를 덮었다
      |                     ^
virt06.cpp:5:25: note: overridden function is ‘virtual void B::f()’
    5 | struct B { virtual void f() final {} virtual ~B() = default; };
      |                         ^
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 virt06.cpp -o ex (cc exit=1) =====
virt06.cpp:3:14: error: base 'Sealed' is marked 'final'
    3 | struct Try : Sealed { };                       // 1. final 클래스를 상속했다
      |              ^
virt06.cpp:2:8: note: 'Sealed' declared here
    2 | struct Sealed final { };
      |        ^      ~~~~~
virt06.cpp:6:21: error: declaration of 'f' overrides a 'final' function
    6 | struct D : B { void f() override {} };         // 2. final 함수를 덮었다
      |                     ^
virt06.cpp:5:25: note: overridden virtual function is here
    5 | struct B { virtual void f() final {} virtual ~B() = default; };
      |                         ^
2 errors generated.
```

```cpp
/* virt07.cpp */
// 순수 가상과 추상 클래스 — 무엇을 못 만드나
#include <cstdio>

struct Shape {
    virtual double area() const = 0;               // 순수 가상 — 본체가 없다
    virtual void   name() const { std::printf("      Shape\n"); }   // 가상이지만 본체가 있다
    virtual ~Shape() = default;
};
struct Sq : Shape {
    double s;
    explicit Sq(double v) : s(v) {}
    double area() const override { return s * s; }
};
struct Half : Shape { };                           // area 를 구현하지 않았다

int main() {
    Sq q(3);
    Shape& r = q;
    std::printf("area=%.1f\n", r.area());
    r.name();
    Shape s;                                       // 1. 추상 클래스를 직접 만들었다
    Half h;                                        // 2. 여전히 추상인 파생을 만들었다
    (void)s; (void)h;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 virt07.cpp -o ex (cc exit=1) =====
virt07.cpp: In function ‘int main()’:
virt07.cpp:21:11: error: cannot declare variable ‘s’ to be of abstract type ‘Shape’
   21 |     Shape s;                                       // 1. 추상 클래스를 직접 만들었다
      |           ^
virt07.cpp:4:8: note:   because the following virtual functions are pure within ‘Shape’:
    4 | struct Shape {
      |        ^~~~~
virt07.cpp:5:20: note:     ‘virtual double Shape::area() const’
    5 |     virtual double area() const = 0;               // 순수 가상 — 본체가 없다
      |                    ^~~~
virt07.cpp:22:10: error: cannot declare variable ‘h’ to be of abstract type ‘Half’
   22 |     Half h;                                        // 2. 여전히 추상인 파생을 만들었다
      |          ^
virt07.cpp:14:8: note:   because the following virtual functions are pure within ‘Half’:
   14 | struct Half : Shape { };                           // area 를 구현하지 않았다
      |        ^~~~
virt07.cpp:5:20: note:     ‘virtual double Shape::area() const’
    5 |     virtual double area() const = 0;               // 순수 가상 — 본체가 없다
      |                    ^~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 virt07.cpp -o ex (cc exit=1) =====
virt07.cpp:21:11: error: variable type 'Shape' is an abstract class
   21 |     Shape s;                                       // 1. 추상 클래스를 직접 만들었다
      |           ^
virt07.cpp:5:20: note: unimplemented pure virtual method 'area' in 'Shape'
    5 |     virtual double area() const = 0;               // 순수 가상 — 본체가 없다
      |                    ^
virt07.cpp:22:10: error: variable type 'Half' is an abstract class
   22 |     Half h;                                        // 2. 여전히 추상인 파생을 만들었다
      |          ^
virt07.cpp:5:20: note: unimplemented pure virtual method 'area' in 'Half'
    5 |     virtual double area() const = 0;               // 순수 가상 — 본체가 없다
      |                    ^
2 errors generated.
```

**왜 그런가**

- ★★ **`final` 이 막는 것 둘** — **클래스**(더 못 물려받는다)와 **가상 함수**(더 못 덮는다).\
  ★ 두 컴파일러 다 **에러 2건**이고 `cc exit=1` 이다.
- ★★★ **`Half h;` 가 에러인 이유** — `Half` 가 `Shape` 를 물려받기만 하고 **`area()` 를 안 덮었다.**\
  **순수 가상이 하나라도 남아 있으면 파생도 추상**이다. 「파생이니까 구체 클래스」가 아니다.
- ★★ **g++ 는 어느 함수가 순수인지 나열한다**(`because the following virtual functions are pure`).\
  clang 은 `unimplemented pure virtual method 'area'` 로 **한 줄에 짚는다.**\
  ★ 인터페이스가 커지면 그 목록이 **고칠 것의 목록**이 된다.
- ★★ **`name()` 은 순수 가상이 아니다** — **본체가 있는 가상 함수**다.\
  ★ 「순수 가상 = 본체 없음」이 아니라 「**순수 가상 = 파생이 반드시 덮어야 함**」이다.\
  (실제로 순수 가상에도 본체를 줄 수 있다 — 이 문서는 그 형태를 안 던졌다.)

### 6. ★★★ `~DerNV` 가 **0회** — 놓은 바이트 **64 / 192 / 192** 이고 **128바이트가 샌다**

**출력**

```cpp
/* virt08.cpp */
// 가상 소멸자가 없는 다형적 삭제 — 14편의 「경고 0건」 자리를 계수로 다시 묻는다
#include <cstdio>
#include <cstdlib>

static int made = 0, destroyed_base = 0, destroyed_der = 0, freed_bytes = 0;

struct BaseNV {                                    // 소멸자가 가상이 아니다
    char* buf;
    BaseNV() : buf(static_cast<char*>(std::malloc(64))) { ++made; }
    ~BaseNV() { std::free(buf); freed_bytes += 64; ++destroyed_base; }
};
struct DerNV : BaseNV {
    char* extra;
    DerNV() : extra(static_cast<char*>(std::malloc(128))) {}
    ~DerNV() { std::free(extra); freed_bytes += 128; ++destroyed_der; }
};

struct BaseV {                                     // 소멸자가 가상이다
    char* buf;
    BaseV() : buf(static_cast<char*>(std::malloc(64))) { ++made; }
    virtual ~BaseV() { std::free(buf); freed_bytes += 64; ++destroyed_base; }
};
struct DerV : BaseV {
    char* extra;
    DerV() : extra(static_cast<char*>(std::malloc(128))) {}
    ~DerV() override { std::free(extra); freed_bytes += 128; ++destroyed_der; }
};

int main() {
    std::printf("(1) 가상 소멸자가 없는 쪽 — 기반 포인터로 지운다\n");
    destroyed_base = destroyed_der = freed_bytes = 0;
    { BaseNV* p = new DerNV; delete p; }
    std::printf("    ~BaseNV %d회 · ~DerNV %d회 · 놓은 바이트 %d\n",
                destroyed_base, destroyed_der, freed_bytes);

    std::printf("(2) 같은 타입을 파생 포인터로 지운다\n");
    destroyed_base = destroyed_der = freed_bytes = 0;
    { DerNV* p = new DerNV; delete p; }
    std::printf("    ~BaseNV %d회 · ~DerNV %d회 · 놓은 바이트 %d\n",
                destroyed_base, destroyed_der, freed_bytes);

    std::printf("(3) 소멸자를 가상으로 바꾼 쪽 — 기반 포인터로 지운다\n");
    destroyed_base = destroyed_der = freed_bytes = 0;
    { BaseV* p = new DerV; delete p; }
    std::printf("    ~BaseV  %d회 · ~DerV  %d회 · 놓은 바이트 %d\n",
                destroyed_base, destroyed_der, freed_bytes);

    std::printf("(4) sizeof — 가상 함수가 하나라도 있으면 무엇이 붙나\n");
    std::printf("    BaseNV %zu · DerNV %zu · BaseV %zu · DerV %zu (char* 는 %zu)\n",
                sizeof(BaseNV), sizeof(DerNV), sizeof(BaseV), sizeof(DerV), sizeof(char*));
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic virt08.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 가상 소멸자가 없는 쪽 — 기반 포인터로 지운다
    ~BaseNV 1회 · ~DerNV 0회 · 놓은 바이트 64
(2) 같은 타입을 파생 포인터로 지운다
    ~BaseNV 1회 · ~DerNV 1회 · 놓은 바이트 192
(3) 소멸자를 가상으로 바꾼 쪽 — 기반 포인터로 지운다
    ~BaseV  1회 · ~DerV  1회 · 놓은 바이트 192
(4) sizeof — 가상 함수가 하나라도 있으면 무엇이 붙나
    BaseNV 8 · DerNV 16 · BaseV 16 · DerV 24 (char* 는 8)
```

**왜 그런가**

| 판 | `~Base` | `~Der` | 놓은 바이트 |
|---|---|---|---|
| `(1)` 기반 포인터 · 비가상 소멸자 | 1 | ★★★ **0** | ★★★ **64** |
| `(2)` 파생 포인터 · 같은 타입 | 1 | **1** | **192** |
| `(3)` 기반 포인터 · 가상 소멸자 | 1 | **1** | **192** |

- ★★★ **`(1)` 과 `(2)` 는 같은 타입인데 갈린다.** **타입의 문제가 아니라 「무엇으로 지웠나」의 문제**다.\
  ★ 비가상 소멸자는 **정적 타입으로 고른다** — 1번의 `(3)`·`(4)` 와 **정확히 같은 규칙**이다.
- ★★★ **`(3)` 이 처방이다.** 소멸자를 `virtual` 로 바꾸면 **기반 포인터로 지워도 192** 다.
- ★★ **`(4)` 의 `sizeof` 가 그 대가다** — `BaseNV` 8 · `BaseV` 16 · `DerNV` 16 · `DerV` 24.\
  ★ **가상 함수가 하나라도 생기면 vptr 8바이트가 붙는다.** 규칙은 그것 하나다.
- ★★★ **ASan 은 「누수」가 아니라 「크기 불일치」로 먼저 잡는다.**

```cpp
/* virt13.cpp */
// 가상 소멸자가 없는 다형적 삭제를 ASan 에게 물어본다
// 마커는 표준 오류로 찍는다 — sanitizer 가 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>
#include <cstdlib>

struct BaseNV { char* buf; BaseNV() : buf(static_cast<char*>(std::malloc(64))) {} ~BaseNV() { std::free(buf); } };
struct DerNV : BaseNV { char* extra; DerNV() : extra(static_cast<char*>(std::malloc(128))) {} ~DerNV() { std::free(extra); } };

int main() {
    std::fprintf(stderr, "(1) 기반 포인터로 지운다 — 경고는 0건이었다\n");
    BaseNV* p = new DerNV;
    delete p;
    std::fprintf(stderr, "(2) 여기까지 왔다\n");
}
```

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. virt13.cpp -o exa && ./exa | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=1) =====
(1) 기반 포인터로 지운다 — 경고는 0건이었다
=================================================================
==3141801==ERROR: AddressSanitizer: new-delete-type-mismatch on 0x502000000010 in thread T0:
  object passed to delete has wrong type:
  size of the allocated type:   16 bytes;
  size of the deallocated type: 8 bytes.
    #0 0x7f51b90ff5e8 in operator delete(void*, unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:164
    #1 0x5f6b5a3a0313 in main virt13.cpp:12

0x502000000010 is located 0 bytes inside of 16-byte region [0x502000000010,0x502000000020)
allocated by thread T0 here:
    #0 0x7f51b90fe548 in operator new(unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:95
    #1 0x5f6b5a3a02e6 in main virt13.cpp:11

SUMMARY: AddressSanitizer: new-delete-type-mismatch ../../../../src/libsanitizer/asan/asan_new_delete.cpp:164 in operator delete(void*, unsigned long)
```

- ★★★ **`new-delete-type-mismatch`** 다 — `allocated 16 bytes` 를 `deallocated 8 bytes` 로 놓았다고 짚는다.\
  ★ **`delete p;` 가 `sizeof(BaseNV)` 인 8을 `operator delete` 에 넘기기 때문**이다.\
  누수를 세기 전에 **그 불일치에서 죽는다.**
- ★★ **마커를 `stderr` 로 찍은 덕에 `(1)` 줄이 리포트 앞에 남아 있다.** 표준 출력이었으면 `abort()` 가 지웠다.

**컴파일러는 어느 쪽에 말해 주나**

```cpp
/* virt12.cpp */
// 가상 소멸자 없는 다형적 삭제 — 경고가 나는 자리와 안 나는 자리를 한 파일에
struct Plain      { char* p; Plain(); ~Plain(); };       // 가상 함수가 하나도 없다
struct PlainDer : Plain { char* q; ~PlainDer(); };

struct Poly       { virtual void f(); ~Poly(); };        // 가상 함수가 있는데 소멸자는 비가상
struct PolyDer  : Poly { char* q; ~PolyDer(); };

int main() {
    Plain* a = new PlainDer;  delete a;                  // ① 비다형 기반으로 지운다
    Poly*  b = new PolyDer;   delete b;                  // ② 다형 기반으로 지운다
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -c virt12.cpp -o /dev/null (cc exit=0) =====
virt12.cpp: In function ‘int main()’:
virt12.cpp:10:31: warning: deleting object of polymorphic class type ‘Poly’ which has non-virtual destructor might cause undefined behavior [-Wdelete-non-virtual-dtor]
   10 |     Poly*  b = new PolyDer;   delete b;                  // ② 다형 기반으로 지운다
      |                               ^~~~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -c virt12.cpp -o /dev/null (cc exit=0) =====
virt12.cpp:10:31: warning: delete called on non-final 'Poly' that has virtual functions but non-virtual destructor [-Wdelete-non-abstract-non-virtual-dtor]
   10 |     Poly*  b = new PolyDer;   delete b;                  // ② 다형 기반으로 지운다
      |                               ^
1 warning generated.
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -Wnon-virtual-dtor -c virt12.cpp -o /dev/null (cc exit=0) =====
virt12.cpp:5:8: warning: ‘struct Poly’ has virtual functions and accessible non-virtual destructor [-Wnon-virtual-dtor]
    5 | struct Poly       { virtual void f(); ~Poly(); };        // 가상 함수가 있는데 소멸자는 비가상
      |        ^~~~
virt12.cpp:6:8: warning: base class ‘struct Poly’ has accessible non-virtual destructor [-Wnon-virtual-dtor]
    6 | struct PolyDer  : Poly { char* q; ~PolyDer(); };
      |        ^~~~~~~
virt12.cpp:6:8: warning: ‘struct PolyDer’ has virtual functions and accessible non-virtual destructor [-Wnon-virtual-dtor]
virt12.cpp: In function ‘int main()’:
virt12.cpp:10:31: warning: deleting object of polymorphic class type ‘Poly’ which has non-virtual destructor might cause undefined behavior [-Wdelete-non-virtual-dtor]
   10 |     Poly*  b = new PolyDer;   delete b;                  // ② 다형 기반으로 지운다
      |                               ^~~~~~~~
```

| 지우는 대상 | g++ 기본 | clang 기본 | g++ `+ -Wnon-virtual-dtor` |
|---|---|---|---|
| ① **가상 함수가 없는 기반**(`Plain`) | ★★★ **0건** | ★★★ **0건** | ★★★ **0건** |
| ② **가상 함수가 있는 기반**(`Poly`) | ★★ **warning** | ★★ **warning** | ★★ **warning**(+ 선언 자리 3건) |

- ★★★ **경고의 조건**은 「소멸자가 비가상이다」가 아니라 「**다형적인데 소멸자가 비가상이다**」이다.\
  `Plain` 은 **가상 함수가 하나도 없어서 다형적이 아니므로** `-Wdelete-non-virtual-dtor` 가 **발동하지 않는다.**
- ★★★ **그것이 [14번](../14-destructors-and-deterministic-destruction/) (5)가 「경고 0건에 `run exit=0`」이라고 적은 자리의 이유다.**\
  ★ 그 편의 `DerNV` 도 **기반에 가상 함수가 없었다.** **여기가 그 자리의 정본**이고, 답은 **조건**이었다.
- ★★ **`-Wnon-virtual-dtor` 를 켜면 선언 자리에서 셋을 더 말해 준다** — **삭제하는 줄을 안 써도** 잡힌다.\
  ★ 그런데 **①에는 여전히 0건**이다. **어떤 플래그로도 안 잡힌다.**
- ★★★ **결론** — **기반 포인터로 지울 계층이면 소멸자를 가상으로 두는 것이 유일한 방어**다.\
  **가상 함수가 하나도 없는 기반은 도구가 절대 안 도와준다.**

### 7. ★★ **기반 것이 불린다** — 생성자에서도 소멸자에서도

**출력**

```cpp
/* virt09.cpp */
// 생성자 안에서 가상 함수를 부르면 — 기반의 것이 불린다(C# 과 정반대다)
#include <cstdio>

struct B {
    B() { std::printf("      B 의 생성자에서 speak() 를 부른다 -> "); speak(); }
    virtual void speak() { std::printf("B::speak\n"); }
    virtual ~B() { std::printf("      B 의 소멸자에서 speak() 를 부른다 -> "); speak(); }
};
struct D : B {
    int ready;
    D() : ready(42) { std::printf("      D 의 생성자 본문 — ready=%d\n", ready); }
    void speak() override { std::printf("D::speak  ready=%d\n", ready); }
};

int main() {
    std::printf("(1) D 를 만든다\n");
    { D d; std::printf("(2) 다 지어진 뒤 부른다 -> "); d.speak(); std::printf("(3) 블록을 나간다\n"); }
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic virt09.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) D 를 만든다
      B 의 생성자에서 speak() 를 부른다 -> B::speak
      D 의 생성자 본문 — ready=42
(2) 다 지어진 뒤 부른다 -> D::speak  ready=42
(3) 블록을 나간다
      B 의 소멸자에서 speak() 를 부른다 -> B::speak
```

**왜 그런가**

- ★★★ **생성자·소멸자 안에서는 동적 타입이 「그 시점의 클래스」다.**\
  `B` 의 생성자가 도는 동안 객체는 **아직 `B` 일 뿐**이고, `B` 의 소멸자가 돌 때는 **이미 `B` 로 돌아왔다.**
- ★★★ **`D::speak` 가 한 번도 안 불린다.** 에러도 경고도 없고 **`ready` 를 볼 기회도 없다.**\
  ★ C++ 에서는 「안 터지는 대신 **의도한 동작이 조용히 사라진다**」.
- ★★★ **C# 은 정반대다.** C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **12번**([`12-class-fields-constructors-this-base/`](../../../csharp/syntax/12-class-fields-constructors-this-base/)) (4)가 **양쪽을 나란히 실측했다.**

| | C# | C++ |
|---|---|---|
| 기반 생성자에서 가상 호출이 가는 곳 | ★★★ **파생 것**(`Child.Describe`) | ★★★ **기반 것**(`Parent::describe`) |
| 그때 파생 필드 초기자는 | ★ **이미 돌았다** | ★ **아직 안 돌았다** |
| 그래서 보이는 것 | **절반만 채워진 파생 상태** | **파생 상태를 아예 안 본다** |
| 터지나 | ★★ **`NullReferenceException` 이 날 수 있다** | **안 난다**(다른 함수가 불린다) |

- ★★★ **두 언어가 정반대로 안전하지 않다.**\
  C# 은 **파생 코드가 미완성 상태를 보고**, C++ 은 **파생 코드가 아예 안 불린다.**\
  ★ **그래서 처방이 같다** — **생성자에서 가상 함수를 부르지 않는다.**\
  둘 다 「생성 중에는 객체가 아직 완성이 아니다」라는 **같은 사실의 서로 다른 얼굴**이기 때문이다.
- ★ **대안** — 생성이 끝난 뒤 부르는 `Initialize()` 를 따로 두거나 **`final` 로 막는다.**

### 8. ★★ **둘 다 찍혔다** — 항목 6개이고 **기본 인자는 없다**

**출력**

```text
===== g++ --version | head -1 (exit=0) =====
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
===== clang++ --version | head -1 (exit=0) =====
Ubuntu clang version 18.1.3 (1ubuntu1)
===== which g++ clang++ (exit=0) =====
/usr/bin/g++
/usr/bin/clang++
```

```cpp
/* virt10.cpp */
// vtable 덤프용 최소 소스 — 기반 하나 · 파생 하나 · 가상 함수 둘
struct B {
    virtual void f();
    virtual void g();
    virtual ~B();
};
struct D : B {
    void f() override;
    void h();
};
void B::f() {}
void B::g() {}
B::~B() {}
void D::f() {}
void D::h() {}
int main() { D d; B* p = &d; p->f(); }
```

```text
===== g++ -std=c++20 -fdump-lang-class=stdout -c virt10.cpp -o /dev/null (exit=0) =====
Vtable for B
B::_ZTV1B: 6 entries
0     (int (*)(...))0
8     (int (*)(...))(& _ZTI1B)
16    (int (*)(...))B::f
24    (int (*)(...))B::g
32    (int (*)(...))B::~B
40    (int (*)(...))B::~B

Class B
   size=8 align=8
   base size=8 base align=8
B (0x0x7ccbe319c420) 0 nearly-empty
    vptr=((& B::_ZTV1B) + 16)

Vtable for D
D::_ZTV1D: 6 entries
0     (int (*)(...))0
8     (int (*)(...))(& _ZTI1D)
16    (int (*)(...))D::f
24    (int (*)(...))B::g
32    (int (*)(...))D::~D
40    (int (*)(...))D::~D

Class D
   size=8 align=8
   base size=8 base align=8
D (0x0x7ccbe300e1a0) 0 nearly-empty
    vptr=((& D::_ZTV1D) + 16)
B (0x0x7ccbe319c540) 0 nearly-empty
      primary-for D (0x0x7ccbe300e1a0)
```

```text
===== clang++ -std=c++20 -Xclang -fdump-vtable-layouts -c virt10.cpp -o /dev/null (exit=0) =====
Vtable for 'B' (6 entries).
   0 | offset_to_top (0)
   1 | B RTTI
       -- (B, 0) vtable address --
   2 | void B::f()
   3 | void B::g()
   4 | B::~B() [complete]
   5 | B::~B() [deleting]

VTable indices for 'B' (4 entries).
   0 | void B::f()
   1 | void B::g()
   2 | B::~B() [complete]
   3 | B::~B() [deleting]

Vtable for 'D' (6 entries).
   0 | offset_to_top (0)
   1 | D RTTI
       -- (B, 0) vtable address --
       -- (D, 0) vtable address --
   2 | void D::f()
   3 | void B::g()
   4 | D::~D() [complete]
   5 | D::~D() [deleting]

VTable indices for 'D' (3 entries).
   0 | void D::f()
   2 | D::~D() [complete]
   3 | D::~D() [deleting]
```

**왜 그런가**

| 자리 | g++ 가 부르는 이름 | clang 이 부르는 이름 |
|---|---|---|
| 0 | `(int (*)(...))0` | `offset_to_top (0)` |
| 1 | `(& _ZTI1B)` | `B RTTI` |
| 2 | `B::f` | `void B::f()` |
| 3 | `B::g` | `void B::g()` |
| 4 | `B::~B` | `B::~B() [complete]` |
| 5 | `B::~B` | `B::~B() [deleting]` |

- ★★★ **항목 수는 둘 다 6개**이고 **같은 것을 다른 말로** 보여 준다.
- ★★★ **`D` 의 vtable 에서 `f` 만 `D::f` 로 바뀌고 `g` 는 `B::g` 그대로**다.\
  ★ **재정의하지 않은 가상 함수는 기반의 주소가 그대로 복사된다.**
- ★★ **소멸자가 두 칸을 쓴다** — clang 이 `[complete]` 와 `[deleting]` 으로 이름을 붙여 준다.\
  ★ 뒤엣것이 **`delete p;` 가 부르는 것**이고, **6번의 사고가 그 자리의 선택**이다.
- ★★★ **기본 인자는 vtable 에 없다** — **함수 주소만** 있다. **그래서 3번이 성립한다.**\
  ★ 기본 인자를 런타임에 고르려면 표에 그 값이 있어야 하는데 **없다.**
- ★★ **clang 의 `VTable indices` 가 한 가지를 더 보여 준다** — `B` 는 4개인데 `D` 는 **3개**이고\
  **인덱스 1이 빠져 있다**(`0 · 2 · 3`). **`D` 가 `g` 를 재정의하지 않았기 때문**이다.
- ★ **g++ 덤프에는 주소가 박힌다**(`(0x0x724f…`) — **흔들리는 칸**이다. 근거는 **항목 수와 그 자리의 이름**이다.
- ★★★ **재지 않은 것은 비용이다.** 이 절이 보인 것은 **구조**다.\
  「가상 호출이 느리다」를 말하려면 **인라인 불가·분기 예측·캐시**를 재야 하고, 정본은 목록의 **21번 주제**다.

### 9. ★★ 탐침 여덟 중 **하나**가 답했다 — **1번**이다

**출력**

```cpp
/* virt11.cpp */
// 상속에서 틀리는 자리 여덟을 심었다 — 컴파일러가 몇 군데에서 말하는지 센다
#include <cstdio>

struct B1 { virtual void f() const {} virtual ~B1() = default; };
struct D1 : B1 { void f() {} };                  // 1. const 가 달라 재정의가 아니다 (override 를 안 붙였다)

struct B2 { virtual void go() {} virtual ~B2() = default; };
struct D2 : B2 { void gо() {} };                 // 2. 이름 오타 — 새 함수가 하나 생긴다

struct B3 { void plain() {} };
struct D3 : B3 { void plain() {} };              // 3. 비가상 함수를 「재정의」했다

struct B4 { virtual void h(int x = 1) { (void)x; } virtual ~B4() = default; };
struct D4 : B4 { void h(int x = 2) { (void)x; } };  // 4. 기본 인자가 다르다

struct B5 { void k(int) {} void k(const char*) {} };
struct D5 : B5 { void k(double) {} };            // 5. 오버로드가 통째로 가려진다

struct B6 { virtual void m() {} virtual ~B6() = default; };
struct D6 : B6 { void m() {} };                  // 6. 제대로 재정의하는데 override 를 안 썼다

struct B7 { char* p; B7() : p(new char[8]) {} ~B7() { delete[] p; } };
struct D7 : B7 { char* q; D7() : q(new char[8]) {} ~D7() { delete[] q; } };
                                                 // 7. 가상 소멸자가 없는데 다형적으로 쓸 모양이다

struct B8 { virtual void n() {} virtual ~B8() = default; };
struct D8 : B8 { virtual void n() {} };          // 8. virtual 을 다시 적었다(override 대신)

int main() {
    D1 a; D2 b; D3 c; D4 d; D5 e; D6 f; D8 g;
    B7* p = new D7; delete p;                    // 다형적 삭제 — 파생 소멸자가 안 돈다
    (void)a; (void)b; (void)c; (void)d; (void)e; (void)f; (void)g;
    std::printf("여덟 자리 전부 컴파일됐다\n");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic virt11.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
virt11.cpp:4:26: warning: ‘virtual void B1::f() const’ was hidden [-Woverloaded-virtual=]
    4 | struct B1 { virtual void f() const {} virtual ~B1() = default; };
      |                          ^
virt11.cpp:5:23: note:   by ‘void D1::f()’
    5 | struct D1 : B1 { void f() {} };                  // 1. const 가 달라 재정의가 아니다 (override 를 안 붙였다)
      |                       ^
여덟 자리 전부 컴파일됐다
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic virt11.cpp -o ex (cc exit=0) =====
virt11.cpp:5:23: warning: 'D1::f' hides overloaded virtual function [-Woverloaded-virtual]
    5 | struct D1 : B1 { void f() {} };                  // 1. const 가 달라 재정의가 아니다 (override 를 안 붙였다)
      |                       ^
virt11.cpp:4:26: note: hidden overloaded virtual function 'B1::f' declared here: different qualifiers ('const' vs unqualified)
    4 | struct B1 { virtual void f() const {} virtual ~B1() = default; };
      |                          ^
1 warning generated.
```

```text
===== echo "virt11 탐침 여덟  g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic virt11.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
virt11 탐침 여덟  g++ 경고 1
===== echo "virt11 탐침 여덟  clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic virt11.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
virt11 탐침 여덟  clang 경고 1
===== echo "virt11 을 ASan 으로 돌리면: $(g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. virt11.cpp -o exa 2>/dev/null; ./exa >/dev/null 2>asan19.txt; grep -cE 'ERROR: (Address|Leak)Sanitizer' asan19.txt) 건" (exit=0) =====
virt11 을 ASan 으로 돌리면: 1 건
===== echo "그 리포트의 요약: $(grep -hE '^SUMMARY' asan19.txt | head -1 | grep . || echo 리포트 없음)" (exit=0) =====
그 리포트의 요약: SUMMARY: AddressSanitizer: new-delete-type-mismatch ../../../../src/libsanitizer/asan/asan_new_delete.cpp:164 in operator delete(void*, unsigned long)
```

**왜 그런가**

| 심은 것 | g++ | clang | 실제로는 |
|---|---|---|---|
| 1. `const` 가 달라 재정의가 아니다 | ★ **1** | ★ **1** | ★★ `-Woverloaded-virtual` |
| 2. 이름 오타 | 0 | 0 | ★★★ 기반 것이 계속 불린다 |
| 3. 비가상 함수를 「재정의」 | 0 | 0 | ★★★ 정적 타입이 답을 정한다(1번) |
| 4. 기본 인자가 다르다 | 0 | 0 | ★★★ 호출 자리마다 값이 갈린다(3번) |
| 5. 오버로드가 통째로 가려진다 | 0 | 0 | ★★ 변환되어 조용히 통과한다(4번) |
| 6. 재정의는 맞는데 `override` 를 안 썼다 | 0 | 0 | ★ 다음 사람이 ①\~④를 못 잡는다 |
| 7. ★★★ **가상 소멸자 없이 다형적 삭제** | ★★★ **0건** | ★★★ **0건** | ★★★ **파생 소멸자가 안 돈다**(6번) |
| 8. `override` 대신 `virtual` 을 다시 적었다 | 0 | 0 | ★ 재정의는 되지만 ①\~④를 못 잡는다 |

- ★★★ **답한 것 1, 침묵한 것 7**이고 `cc exit=0` 이다.
- ★★★ **1번과 3번이 같은 모양인데 하나만 답한다.** 조건은 「**기반이 가상인가**」다.\
  `B1::f` 는 `virtual` 이라 `-Woverloaded-virtual` 이 「가상 함수를 숨겼다」고 말하고,\
  `B3::plain` 은 **비가상**이라 **숨길 「가상 함수」가 없어** 아무 말도 안 한다.\
  ★ **6번의 경고 조건과 같은 집안**이다 — **둘 다 「다형적인가」가 스위치**다.
- ★★ **ASan 은 `new-delete-type-mismatch` 를 잡는다** — **탐침 7번**이다.\
  ★ 컴파일러가 **0건**인 자리를 sanitizer 가 메운다. **도구를 하나만 쓰면 안 되는 이유**다.
- ★★★ **`override` 를 적으면 탐침 1·2·4·6·8 이 전부 에러가 된다**(2번).\
  **컴파일러가 안 보는 것을 프로그래머가 한 낱말로 보게 만드는 것**이 `override` 다.

### 10. ★★ **표준 · 구현 정의 · UB · 구현 정의** 넷으로 갈린다

- 「**기본 인자는 정적 타입이 정한다**」 — ★★★ **표준**이다. 언어 규칙이고 구현의 재량이 아니다.\
  ★ 8번이 그 **구현상의 이유**(vtable 에 값이 없다)를 보여 주지만, **규칙 자체는 표준**이다.
- 「**vtable 항목이 6개다**」 — ★★★ **구현 정의**다. **Itanium C++ ABI** 의 배치이고,\
  `offset_to_top`·RTTI 자리·소멸자가 두 칸을 쓰는 것이 전부 그 ABI 의 결정이다.\
  ★ **다른 ABI(MSVC 등)에서는 다르다.**
- 「**가상 소멸자 없이 기반 포인터로 지우는 것**」 — ★★★ **UB** 다. 표준이 못 박았다.\
  ★ **그런데 경고가 없는 자리가 있는 이유**는 **컴파일러가 경고를 낼 의무가 없기 때문**이다.\
  UB 를 진단하는 것은 **품질의 문제**이지 **표준의 요구**가 아니다. 6번의 ①이 그 자리다.
- 「**`typeid(...).name()` 이 `1B`**」 — ★★★ **구현 정의**다. 표준은 「구현이 정한 문자열」이라고만 한다.\
  ★ 근거로 쓰는 것은 「**둘이 다르다**」는 사실이지 그 글자가 아니다.

### 11. 다른 주제와 잇기

- ★★★ **[14번](../14-destructors-and-deterministic-destruction/) (5)가 「경고 0건에 `run exit=0`」으로 남겨 둔 자리**를 여기 **6번**이 닫았다.\
  ★ 답은 **조건**이었다 — 경고는 「**다형적인데 소멸자가 비가상**」일 때만 나고,\
  그 편의 예제는 **기반에 가상 함수가 없었다.** **어떤 플래그로도 0건**이다.
- ★★ **이름 숨김**은 **오버로드 해결의 앞 단계**인 「**이름 조회**」에서 벌어진다 — 정본은 [1번](../01-function-overloading-and-overload-resolution/).\
  ★ 후보가 정해진 뒤에 벌어지는 일이 아니라 **후보를 모으는 단계**의 일이다.
- ★★ **생성자 속 가상 호출의 양쪽 실측**은 C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **12번**([`12-class-fields-constructors-this-base/`](../../../csharp/syntax/12-class-fields-constructors-this-base/)) (4)다.\
  ★ 그 편이 **C# 과 C++ 을 한 절에 나란히** 돌렸다.
- ★ **자바는 기본 가상**이다 — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **9번**([`09-inheritance-overriding/`](../../../java/syntax/09-inheritance-overriding/)).\
  ★ **막는 낱말은 `final`** 이다. C++ 은 `virtual` 로 **열고**, 자바는 `final` 로 **막는다** — **기본값이 반대다.**

```text
===== set +u; source ~/.sdkman/bin/sdkman-init.sh >/dev/null 2>&1; set -u; which javac && javac -version (exit=0) =====
/home/jun/.sdkman/candidates/java/current/bin/javac
javac 21.0.5
```

```java
// Virt.java
// 자바는 메서드가 기본 가상이다 — 같은 모양을 던져 본다
public class Virt {
    static class B {
        void who() { System.out.println("      B.who"); }
        final void sealed() { System.out.println("      B.sealed"); }
    }
    static class D extends B {
        @Override void who() { System.out.println("      D.who"); }
    }
    public static void main(String[] a) {
        B r = new D();
        System.out.println("(1) 정적 타입 B 로 who() 를 부른다 — virtual 을 아무 데도 안 적었다");
        r.who();
        System.out.println("(2) 이름이 말하는 타입 : " + B.class.getName());
        System.out.println("    물건이 말하는 타입 : " + r.getClass().getName());
        r.sealed();
    }
}
```

```text
===== set +u; source ~/.sdkman/bin/sdkman-init.sh >/dev/null 2>&1; set -u; javac Virt.java && java Virt (exit=0) =====
(1) 정적 타입 B 로 who() 를 부른다 — virtual 을 아무 데도 안 적었다
      D.who
(2) 이름이 말하는 타입 : Virt$B
    물건이 말하는 타입 : Virt$D
      B.sealed
```

- ★★ **가상 호출 비용은 목록의 21번 주제**에서 재야 한다. 이 문서는 **구조만** 봤다.
- ★ **이 편은 [16번](../16-copy-constructor-and-copy-assignment/)\~[목록의 18번 주제](../18-rule-of-zero-three-five-default-delete/)와 다른 축이다.**\
  저쪽이 「값이 어떻게 옮겨지나」라면 여기는 「호출이 어디로 가나」이고,\
  **겹치는 자리는 6번 하나**(소멸자)다.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `virt01.cpp` 정적/동적 타입 | g++ · clang 각 1회 | ★★★ `1B` 대 `1D` · 가상은 `D::who` · 비가상은 **부른 이름이 정한다** · 두 컴파일러 동일 |
| `virt02.cpp` `override` 넷 | g++ · clang 각 1회 | ★★★ **양쪽 에러 4건** · `cc exit=1` · clang 이 이유를 더 짚는다 |
| `virt03.cpp` 기본 인자 | g++ · clang 각 1회 | ★★★ 이름은 **언제나 `D::f`** · `x` 는 **1·2·1·9·2** |
| `virt04.cpp` 이름 숨김 | g++ 1회 | ★★ `d.f(1)` → `D::f(double)` · `using` 으로 `B::f(int)` 되살림 |
| `virt05.cpp` 숨김 에러 | g++ 1회 | ★★ **에러 1건** · 기반의 `f(const char*)` 를 **언급하지 않음** |
| `virt06.cpp` `final` | g++ · clang 각 1회 | ★★ **양쪽 에러 2건** |
| `virt07.cpp` 추상 클래스 | g++ · clang 각 1회 | ★★★ **양쪽 에러 2건**(`Shape s;` · `Half h;`) |
| `virt08.cpp` 가상 소멸자 | g++ · clang 각 1회 | ★★★ `~DerNV` **0회** · 바이트 **64 / 192 / 192** · `sizeof` **8·16·16·24** |
| `virt13.cpp` ASan | g++ + ASan 1회 | ★★★ **`new-delete-type-mismatch`**(16 대 8) · `run exit=1` |
| `virt12.cpp` 경고 조건 | g++ 2회(기본 · `-Wnon-virtual-dtor`) · clang 1회 | ★★★ 비다형 기반 **0건**(세 판 다) · 다형 기반 **warning** |
| `virt09.cpp` 생성자 속 가상 | g++ 1회 | ★★★ `B::speak` 만 · `D::speak` 는 **0회** |
| `virt10.cpp` vtable | g++ 1회 · clang 1회 | ★★ **양쪽 6항목** · `D` 는 `f` 만 바뀜 · clang `VTable indices` **4 대 3** |
| `virt11.cpp` 탐침 여덟 | g++ · clang 각 1회 + ASan 1회 | ★★★ **경고 1 · 1**(탐침 1번) · ASan **`new-delete-type-mismatch`** |
| `Virt.java` 자바 | javac + java 각 1회 | ★★ `virtual` 없이 **`D.who`** — 기본 가상 |
| `virt14.cpp` 형태 | g++ 1회 | `Square area=9.0000` · `Circle area=3.1416` |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · Itanium C++ ABI · ASan)에서만** 그렇다.

- ★★★ **8번의 vtable 배치 전부** — 항목 수 6 · `offset_to_top` · RTTI 자리 · 소멸자 두 칸.
- ★★★ **`typeid(...).name()` 이 `1B`·`1D`·`P1B` 인 것** — 표준은 문자열을 정하지 않는다.
- ★★ **`sizeof` 가 8·16·16·24 인 것**(vptr 8바이트) · **진단 문구와 경고 이름 전부.**
- ★ **ASan 리포트의 PID·주소** · **g++ vtable 덤프의 주소.**

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **가상 함수만 동적 타입으로 고르고**, 나머지는 **정적 타입**이 고르는 것.
- ★★★ **기본 인자는 정적 타입이 정하는** 것.
- **이름 조회가 파생에서 찾으면 멈추는** 것 — 그래서 **오버로드가 통째로 가려지는** 것.
- **`override` 가 재정의 실패를 에러로 만드는** 것(`const`·인자·반환·이름).
- **`final` 이 상속과 재정의를 막는** 것.
- **순수 가상을 안 덮으면 파생도 추상인** 것.
- ★★★ **생성자·소멸자 안에서는 그 시점의 클래스가 동적 타입인** 것.
- ★★★ **가상 소멸자 없이 기반 포인터로 지우면 UB 인** 것.

**UB 의 결과라 보장이 아닌 것**(관찰로만 읽는다)

- ★★★ **6번의 `(1)`.** 근거로 쓰는 것은 「**`~DerNV` 가 0회로 세졌다**」와 「**ASan 이 `new-delete-type-mismatch` 라고 불렀다**」뿐이다.\
  ★ 「항상 128바이트가 샌다」로 적으면 구현 관찰을 표준 보장으로 올린 것이 된다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **다중 상속·가상 상속 판**(8번의 `offset_to_top` 이 쓰이는 자리 — **단일 상속만** 봤다) ·\
  ★ **`dynamic_cast` 를 던지는 판**(정본은 [3번](../03-four-cast-operators/)) ·\
  ★ **순수 가상에 본체를 주는 형태** · ★ **`-std=c++98` 판**(거기에는 `override` 가 없다) ·\
  ★ **clang 으로 `virt04`·`virt09`·`virt14`**(g++ 로만 던졌다) ·\
  ★ **소멸자를 `protected` 비가상으로 두는 형태**(「기반으로 지우지 마라」를 타입으로 말하는 법).
- **못 잰 것** — ★★★ **가상 호출의 비용.**\
  이 문서가 센 것은 **vtable 항목 수·소멸자 호출 횟수·`sizeof` 까지**다.\
  **간접 호출 명령 하나를 세는 것으로는 근거가 안 선다** — 인라인 불가·분기 예측·캐시가 전부 빠진다.\
  ★ **재려면 벤치마크 하네스가 따로 필요하고**, 정본은 목록의 **21번 주제**다.
- ★ 「**부적용인 창**」 — **`-O2` 어셈블리 세기.** **「안 쟀다」가 아니라 「여기서 잴 것이 아니다」다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **9번의 탐침 중 하나라도 더 답하기 시작했는지**(지금은 **여덟 중 하나**).\
  ★ 특히 **탐침 7번**(비다형 기반의 다형적 삭제)에 경고가 붙으면 6번의 결론이 바뀐다.
- ★★★ **8번의 vtable 덤프 형식** — `-fdump-lang-class`·`-fdump-vtable-layouts` 는 **문서화된 안정 인터페이스가 아니다.**
- ★★ **`typeid(...).name()` 의 형식** · **진단 문구.**
- ★ **javac 판이 바뀌었을 때 10번의 출력** — `Virt$B` 같은 중첩 클래스 이름 표기.
