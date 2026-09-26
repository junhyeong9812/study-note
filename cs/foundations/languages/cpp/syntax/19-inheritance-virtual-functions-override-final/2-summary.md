# cpp/syntax/19 — 상속·가상 함수·`override`/`final` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 가상 함수](https://en.cppreference.com/w/cpp/language/virtual) · [cppreference — `override`](https://en.cppreference.com/w/cpp/language/override) · [cppreference — `final`](https://en.cppreference.com/w/cpp/language/final) · [cppreference — 추상 클래스](https://en.cppreference.com/w/cpp/language/abstract_class) · [Itanium C++ ABI](https://itanium-cxx-abi.github.io/cxx-abi/abi.html) · [GCC 13 Developer Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Developer-Options.html)
> **실행 검증** — 이 문서의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **javac 21.0.5** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`virt01.cpp` \~ `virt14.cpp` · `Virt.java`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 배너도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
> ★★★ **ASan 을 붙인 블록은 마커를 `stderr` 로 찍었다.** sanitizer 가 `abort()` 로 죽이면\
> **버퍼에 남은 표준 출력이 통째로 사라지기 때문**이다((8)의 소스에 그렇게 적혀 있다).\
> ★★ **리포트를 자른 블록은 자르는 명령을 배너에 적었다** — 실린 것이 「생략한 일부」가 아니라 「**그 명령의 전체 출력**」이다.
> **버전** — 가상 함수·순수 가상·추상 클래스는 **C++98부터**. **`override`·`final` 은 C++11부터**다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.
> ★★★ **이 편은 16\~18 과 다른 축이다.** 16\~18 이 「**값이 어떻게 옮겨지나**」였다면 여기는 「**호출이 어디로 가나**」다.\
> 겹치는 자리는 하나다 — (8)의 **가상 소멸자 없는 다형적 삭제**이고, **여기가 그 자리의 정본**이다.
> **경계** — 「캡슐화·IS-A·다형성의 개념」은 [`oop-basics/`](../../../../oop-basics/) §14\~18 이 정본이고,\
> 여기는 **C++ 의 가상 디스패치 규칙**만 본다.\
> 「가상 소멸자와 다형적 삭제의 전모」는 [목록의 **20번**](../20-virtual-destructors-and-polymorphic-deletion/), 「추상 클래스·vtable 비용」은 **21번**,\
> 「연산자 오버로딩」은 **22번**, 「오버로드 해결」은 [1번](../01-function-overloading-and-overload-resolution/)이 정본이다.\
> ★ (8)은 **14번이 「경고 0건」으로 남겨 둔 자리를 계수와 ASan 으로 닫는 것**까지다.
> **대비** — ★★ C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **12번**([`12-class-fields-constructors-this-base/`](../../../csharp/syntax/12-class-fields-constructors-this-base/)) — **생성자 속 가상 호출이 C++ 과 정반대로 위험하다.**\
> **그 편이 양쪽을 나란히 실측했고**, (9)에서 그 결과를 인용한다.\
> Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **9번**([`09-inheritance-overriding/`](../../../java/syntax/09-inheritance-overriding/)) — **자바는 기본 가상**이다. (10)에서 던져 본다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 리포트의 **PID**·주소·스택 프레임 줄 | ★★★ **어느 함수가 불렸나**(호출 로그) — 이 주제의 답 자체다 |
> | **g++ vtable 덤프의 주소**(`(0x0x724f…)`) | ★★★ **vtable 항목 수와 그 자리에 무엇이 있나** |
> | 두 컴파일러의 **진단 문구** · 실행 시간 | ★★ **소멸자 호출 횟수와 놓은 바이트 수** · **`sizeof`** |
> | `typeid(...).name()` 의 **꾸밈 형식**(`1B`·`1D`) | ★★ **`cc exit`/`run exit`** · **경고·에러 개수** · **진단의 `(행,열)`** |
>
> ★ **`typeid(...).name()` 이 `1B`·`1D` 로 나오는 것은 Itanium ABI 의 꾸민 이름**이다.\
> **근거로 쓰는 것은 「정적 타입 자리와 동적 타입 자리가 다르다」는 사실**이지 그 글자가 아니다.

## 한눈에 — 쉽게 말하면

**정적 타입은 「명찰」이고 동적 타입은 「사람」이다.**

회사에서 방문증을 받으면 거기 「**방문객**」이라고 적혀 있다 — 그것이 **정적 타입**이다.\
그런데 그 방문증을 들고 있는 사람은 실제로 **소방서장**일 수도 있다 — 그것이 **동적 타입**이다.

「**화재경보가 울리면 어떻게 하세요?**」라고 물었을 때,\
**명찰대로 답하면**(비가상) 「대피합니다」라는 방문객 매뉴얼이 나오고,\
**사람에게 물으면**(가상) 「지휘합니다」라는 소방서장의 답이 나온다.

C++ 은 **기본이 명찰**이다. `virtual` 을 적어야 사람에게 묻는다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 명찰에 적힌 것 | ★★★ **정적 타입** — 컴파일러가 아는 타입 | (1) |
| 실제 사람 | ★★★ **동적 타입** — 런타임의 진짜 타입 | (1) |
| 명찰대로 답한다 | ★★★ **비가상 호출** — 기본값이다 | (1) |
| 사람에게 묻는다 | ★★★ **가상 호출** — `virtual` 을 적어야 한다 | (1) |
| ★★★ **질문지는 명찰이 고르고 답은 사람이 한다** | ★★★ **기본 인자는 정적 타입 · 본체는 동적 타입** | (3) |
| 같은 이름의 명찰을 새로 달면 옛것이 안 보인다 | ★★ **이름 숨김** | (4) |
| 「이 자리는 더 못 바꿔」 | ★ **`final`** | (6) |
| 방문객 매뉴얼만 보고 내보낸다 | ★★★ **가상 소멸자 없는 다형적 삭제** | (8) |

> **정적 타입(static type)** — **선언이 말하는 타입**. 컴파일러가 컴파일 시간에 아는 것.\
> 예: (1)에서 `B& r = d;` 의 `r` 은 정적 타입이 `B` 다.

> **동적 타입(dynamic type)** — **실제로 거기 있는 객체의 타입**.\
> 예: 같은 `r` 의 동적 타입은 `D` 이고, `typeid(r)` 이 그것을 답한다.

```text
   D d;  B& r = d;

   명찰(정적 타입)  B        <- 컴파일러가 보는 것.  오버로드 해결 · 이름 조회 · 기본 인자
   사람(동적 타입)  D        <- 런타임이 보는 것.    가상 함수의 본체

   r.who()    가상   ->  D::who     ★ 사람에게 물었다
   r.plain()  비가상 ->  B::plain   ★ 명찰대로 답했다
```

- ★★★ **컴파일러가 하는 일과 런타임이 하는 일이 이 그림에서 갈린다.**\
  (3)의 기본 인자, (4)의 이름 숨김이 전부 **왼쪽 칸에서 벌어지는 일**이다.

## 이 주제가 답하려는 질문

1. **어느 함수가 불릴지를 무엇이 정하나** — **정적 타입인가 동적 타입인가**((1)(3)(4)).
2. **재정의했다고 생각했는데 안 된 것을 컴파일러가 잡아 주나**((2)(6)).
3. **가상 소멸자를 빠뜨리면 실제로 무엇이 안 도나** — **수로** 보일 수 있나((8)).
4. **그 디스패치를 구현이 무엇으로 하나** — **볼 수 있나**((11)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ①이다

★★★ **이 주제의 본체는 ① 호출 로그 + `typeid` 다.** 「어디로 갔나」는 **찍어야 안다.**

```text
① 호출 로그 + typeid       정적/동적 타입과 실제로 불린 함수를 나란히     (1)(3)(4)(8)(9)
② 두 컴파일러 대조          override·final·추상 클래스의 진단 전문        (2)(5)(6)(7)
③ ASan 리포트               가상 소멸자 없는 삭제                         (8)
④ vtable 덤프               구현이 디스패치를 무엇으로 하나               (11)
⑤ 경고 격자                 탐침 여덟 중 몇이 답하나                      (12)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ★★★ **① 호출 로그 + `typeid`** | ★★★ **본체** — (1)이 정적/동적 타입과 호출 결과를 **한 블록에 나란히** 찍는다 | **쓴다** |
| ② 두 컴파일러 대조 | `override` 가 잡는 실수 넷의 진단 전문 · `final` · 추상 클래스 | **쓴다** |
| ③ ASan 리포트 | (8)의 `new-delete-type-mismatch` | **쓴다** |
| ★★ **④ vtable 덤프** | ★★ **`-fdump-lang-class`(g++)·`-fdump-vtable-layouts`(clang)** — **둘 다 됐다** | **쓴다** |
| ⑤ 경고 격자 | 탐침 여덟 중 **하나**가 답했다 | **쓴다** |
| `-O2` 어셈블리 세기 | ★ **부적용** — **가상 호출 비용은 이 문서에서 재지 않는다** | **안 쓴다** |

- ★★★ **`-O2` 어셈블리 세기를 「부적용」으로 둔 이유를 분명히 한다.**\
  「가상 호출이 느리다」는 **이 문서가 하지 않는 주장**이다. 간접 호출 명령 하나를 세는 것으로는\
  **인라인 불가·분기 예측·캐시**가 전부 빠져 근거가 안 선다.\
  ★ **그 논의의 정본은 [목록의 21번 주제](../21-abstract-classes-pure-virtual-and-vtable-cost/)이고**, 거기서 재야 한다. **「안 쟀다」가 아니라 「여기서는 잴 것이 아니다」다.**
- ★★★ 「**없다고 적기 전에 버전 호출을 블록으로 남겼다**」(규칙 26) — (11)의 첫 블록이 그것이다.\
  ★ 앞 배치가 「`javac` 가 없다」고 잘못 적은 사고가 있었으므로 **(10)에도 버전 블록을 뒀다.**

### (1) ★★★ 정적 타입 대 동적 타입 — `typeid` 와 호출 결과를 나란히

**언제 쓰나** — 「이 줄에서 어느 쪽 함수가 불리지?」가 궁금할 때마다. **이 절이 이 주제의 중심이다.**

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

- ★★★ **`typeid(decltype(r))` 는 `1B` 이고 `typeid(r)` 은 `1D` 다.**\
  ★ 앞엣것은 **컴파일 시간에 타입을 묻는 것**이라 정적 타입을 답하고,\
  뒤엣것은 **다형적 타입의 객체를 묻는 것**이라 **동적 타입**을 답한다. **같은 `r` 인데 답이 다르다.**
- ★★ **`typeid(*p)` 도 `1D`** 다 — 포인터를 역참조하면 객체이므로 동적 타입이 나온다.\
  ★ **`typeid(p)` 는 `P1B`**(= `B*`)다. **포인터 자신은 다형적 타입이 아니다.**
- ★★★ **`(2)` 와 `(3)` 이 갈린다.** 같은 `r` 로 불렀는데 가상 함수는 `D::who`, 비가상 함수는 `B::plain` 이다.
- ★★★ **`(4)` 가 함정이다.** 같은 객체를 `D*` 로 부르면 `D::plain` 이 나온다.\
  ★ **비가상 함수는 「무엇을 통해 불렀나」가 답을 정한다** — 객체는 하나인데 **결과가 둘**이다.\
  `(5)` 가 그것이 같은 객체임을 **주소로** 확인한다(`1` 과 `1`).
- ★ **`typeid(...).name()` 의 `1B`·`1D` 는 Itanium ABI 의 꾸민 이름**이다. **근거는 「둘이 다르다」는 사실**이지 그 글자가 아니다.
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

### (2) ★★★ `override` 가 잡는 실수 넷 — 에러 전문

**언제 쓰나** — 파생에서 함수를 재정의할 때마다. **`override` 를 안 적으면 넷 다 조용히 통과한다.**

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

```text
   override 한 낱말이 하는 일

   파생의 선언  ──> 컴파일러가 「기반에 같은 시그니처의 가상 함수가 있나」를 묻는다
                     있다   -> 재정의로 확정
                     없다   -> ★ 에러 (override 가 없으면 여기서 새 함수가 조용히 생긴다)

   const · 인자 · 반환 · 이름 — 네 가지 중 하나만 어긋나도 「없다」가 된다
```

| 심은 실수 | g++ 가 뭐라고 하나 | clang 이 뭐라고 하나 |
|---|---|---|
| ① **`const` 를 빠뜨렸다** | `marked ‘override’, but does not override` | `hides virtual member function` + **`different qualifiers`** |
| ② **인자 타입이 다르다**(`int` → `long`) | 같은 문구 | **`type mismatch at 1st parameter`** 까지 짚는다 |
| ③ **반환 타입이 다르다**(`int` → `long`) | `conflicting return type specified` | `has a different return type` |
| ④ **이름 오타**(`name` → `nane`) | `marked ‘override’, but does not override` | **`only virtual member functions can be marked 'override'`** |

- ★★★ **넷 다 에러다.** 두 컴파일러 모두 `cc exit=1` 이고 **네 건을 전부** 짚는다.
- ★★★ **`override` 를 지우면 ①②④가 통과하고 ③만 에러로 남는다** — 아래 블록이 그것이다.\
  ★ ①②④는 **새 함수가 하나 생길 뿐**이고, ③은 **반환 타입 충돌이라 별도 규칙**으로 걸린다.
- ★★ **clang 이 이유를 더 짚어 준다** — ①에서 `different qualifiers ('const' vs unqualified)`,\
  ②에서 `type mismatch at 1st parameter ('int' vs 'long')`.\
  ★ g++ 는 ①②④에 **같은 문구**를 쓴다. **진단 문구는 구현 정의**이므로 근거는 **에러 개수**와 진단의 `(행,열)` 둘이다.

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
- ★★★ **그래서 규칙은 하나다** — **재정의하면 반드시 `override` 를 적는다.**\
  ★ 「적어도 되고 안 적어도 되는」 것이 아니라 **넷을 잡아 주는 유일한 장치**다.

### (3) ★★★ 기본 인자는 정적 타입이 정하고 본체는 동적 타입이 정한다

**언제 쓰나** — 가상 함수에 기본 인자를 주려 할 때. **이 주제에서 가장 헷갈리는 자리다.**

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

```text
   D d;  B* p = &d;  D* q = &d;      B::f(int x = 1)   D::f(int x = 2)

   p->f();     기본 인자는 B 의 것 -> 1      본체는 D 의 것 -> D::f  x=1
   q->f();     기본 인자는 D 의 것 -> 2      본체는 D 의 것 -> D::f  x=2
   r.f();      기본 인자는 B 의 것 -> 1      본체는 D 의 것 -> D::f  x=1
               ^^^^^^^^^^^^^^^^^^^^^        ^^^^^^^^^^^^^^^^^^^^^^
               컴파일 시간에 끼워 넣는다      런타임에 고른다
```

- ★★★ **한 호출에서 두 타입이 각각 일한다.** 찍히는 이름은 **언제나 `D::f`** 인데 `x` 는 **1 과 2 로 갈린다.**
- ★★★ **기본 인자는 컴파일 시간에 호출 자리에 끼워 넣어진다.** 그래서 **정적 타입이 정한다.**\
  ★ vtable 에는 기본 인자가 안 들어간다 — **함수 주소만** 들어간다((11)에서 확인한다).
- ★★ **`(5)` 의 `d.f()` 는 `x=2`** 다. 정적 타입이 `D` 이기 때문이다.
- ★★★ **처방은 하나다** — **가상 함수에 기본 인자를 주지 않는다.**\
  ★ 꼭 필요하면 **비가상 함수가 기본 인자를 갖고 가상 함수를 부르게** 한다.
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

### (4) ★★ 이름 숨김 — 오버로드가 통째로 가려지고 `using` 으로 되살아난다

**언제 쓰나** — 파생에 기반과 **같은 이름**의 함수를 둘 때.

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

```text
   B { f(int) · f(const char*) }

   D : B { f(double) }              d.f(1)  ->  D::f(double)   ★ int 가 double 로 변환됐다
                                             기반의 f(int) 는 「안 보인다」

   E : B { using B::f; f(double) }  e.f(1)  ->  B::f(int)      ★ 셋이 한 오버로드 집합이 됐다
                                    e.f("x")->  B::f(const char*)
```

- ★★★ **이름 조회는 「찾으면 멈춘다」.** `D` 에서 `f` 를 찾았으므로 **기반은 안 본다.**\
  ★ **그다음에** 오버로드 해결이 돌지만 **후보가 `D::f(double)` 하나뿐**이다.
- ★★★ **그래서 `d.f(1)` 이 `D::f(double)` 로 간다.** 에러가 아니라 **변환되어 통과한다** — 더 나쁘다.
- ★★ **`using B::f;` 한 줄이 기반의 둘을 파생의 오버로드 집합에 끌어온다.** `E` 에서 셋이 제대로 갈린다.
- ★★ **`(5)` 처럼 이름으로 직접 부를 수도 있다**(`d.B::f(1)`) — 다만 그것은 **가상 디스패치를 끄는 것**이기도 하다.
- ★★★ **가상 함수와는 다른 축의 일이다.** 여기 `f` 들은 **하나도 가상이 아니다.**\
  **이름 조회는 `virtual` 과 무관하게** 일어난다.
- ★ **변환이 안 되면 에러가 된다** — 문자열은 `double` 로 안 바뀐다.

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

- ★★ **진단이 기반을 아예 언급하지 않는다.** `B::f(const char*)` 가 **후보에 없기 때문**이다.\
  ★ 「왜 있는 함수를 못 찾지?」의 답이 **여기 있다.**

### (5) ★ `final` 이 막는 것 둘

**언제 쓰나** — 「이 자리는 더 못 바꾼다」를 타입으로 말할 때.

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

- ★★ **`final` 은 두 자리에 붙는다** — **클래스**(더 못 물려받는다)와 **가상 함수**(더 못 덮는다).
- ★★ **두 컴파일러 다 에러 2건**이고 `cc exit=1` 이다.
- ★ **진단 문구는 다르다** — g++ 는 `cannot derive from ‘final’ base`,\
  clang 은 `base 'Sealed' is marked 'final'`. **근거는 에러 개수**와 진단의 `(행,열)` 둘이다.

### (6) ★ 순수 가상과 추상 클래스

**언제 쓰나** — 인터페이스를 정의할 때.

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

- ★★★ **에러가 둘이다** — 추상 클래스 자체(`Shape s;`)와 **구현을 안 한 파생**(`Half h;`).\
  ★ **「파생이니까 괜찮겠지」가 아니다.** 순수 가상을 하나라도 안 덮으면 **파생도 추상**이다.
- ★★ **g++ 는 「어느 함수가 순수인지」까지 나열한다**(`because the following virtual functions are pure`).\
  ★ 인터페이스가 커지면 그 목록이 **고칠 것의 목록**이 된다.
- ★★ **순수 가상에도 본체를 줄 수 있다** — 이 예제의 `name()` 은 순수가 아니라 **본체가 있는 가상 함수**다.\
  ★ 「순수 가상 = 본체 없음」이 아니라 「**순수 가상 = 파생이 반드시 덮어야 함**」이다.
- ★ **전모는 [목록의 21번 주제](../21-abstract-classes-pure-virtual-and-vtable-cost/)다**. 여기서는 **에러 두 개까지**만 본다.

### (7) ★★ 가상 아닌 함수를 「재정의」하면 — 숨겨질 뿐이다

**언제 쓰나** — `virtual` 을 안 적고 같은 이름을 파생에 둘 때.

(1)의 `(3)`·`(4)` 가 이미 그 자리다 — **같은 객체에 `B&` 로 부르면 `B::plain`, `D*` 로 부르면 `D::plain`** 이다.\
★★★ 「재정의」가 아니라 「**숨김**」이고, **어느 쪽이 불릴지는 정적 타입이 정한다.**

- ★★★ **컴파일러는 이 자리를 잡아 주지 않는다** — (12)의 탐침 3번이 **두 컴파일러 다 0건**이다.
- ★★ **다만 기반이 가상일 때는 다르다** — 기반에 `virtual void f() const` 가 있는데 파생이 `void f()` 를 두면\
  **`-Woverloaded-virtual` 이 답한다**((12)의 탐침 1번). **이 주제에서 컴파일러가 답하는 유일한 자리**다.
- ★ **처방은 (2)와 같다** — **재정의할 생각이면 `override` 를 적는다.** 적으면 **숨김이 에러가 된다.**

### (8) ★★★ 가상 소멸자 없는 다형적 삭제 — 14번이 남긴 자리의 정본

**언제 쓰나** — 기반 포인터로 파생 객체를 지울 때. **이 절이 14번과 이어지는 자리다.**

★★★ **[14번](../14-destructors-and-deterministic-destruction/) (5)가 실측한 것**은 「두 컴파일러 다 **경고 0건이고 `run exit=0`**」이었다.\
**여기서는 그 자리에 계수를 붙이고 ASan 을 붙여 닫는다.**

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

```text
   BaseNV* p = new DerNV;  delete p;      (소멸자가 비가상)

   ~DerNV  가 안 돈다   ->  extra 128바이트가 그대로 남는다
   ~BaseNV 만 돈다      ->  buf   64바이트만 놓인다
   ────────────────────────────────────────────
   놓은 바이트 64 / 192      ★ 128바이트가 샌다

   같은 타입을 DerNV* 로 지우면       -> 192  (둘 다 돈다)
   소멸자를 virtual 로 바꾸면         -> 192  (둘 다 돈다)
```

- ★★★ **`~DerNV` 가 0회다.** 그리고 **놓은 바이트가 64** — **128바이트가 샌다.**
- ★★★ **`(2)` 가 대조군이다.** 같은 타입을 **파생 포인터로** 지우면 **둘 다 돌고 192바이트**가 놓인다.\
  ★ **타입의 문제가 아니라 「무엇으로 지웠나」의 문제**다.
- ★★★ **`(3)` 이 처방이다.** 소멸자를 `virtual` 로 바꾸면 **기반 포인터로 지워도 192** 다.
- ★★ **`(4)` 가 그 대가다** — `BaseNV` 8 · `BaseV` 16. **가상 함수가 하나라도 생기면 vptr 8바이트가 붙는다.**\
  ★ `DerNV` 16 · `DerV` 24 도 같은 8 차이다.
- ★★★ **ASan 에게 물으면 이름이 붙는다.**

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

- ★★★ **`new-delete-type-mismatch`** 다. `allocated 16 bytes` 를 `deallocated 8 bytes` 로 놓았다고 짚는다.\
  ★ **누수가 아니라 크기 불일치로 먼저 걸린다** — `operator delete` 에 넘어간 크기가 틀렸기 때문이다.
- ★★★ **그런데 컴파일러는 이 자리에 아무 말도 안 한다.** 그것을 한 파일에서 갈라 본다.

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

```text
   경고가 켜지는 스위치는 「비가상 소멸자」가 아니다

   struct Plain { char* p; ~Plain(); };          가상 함수 0개 -> 다형적이 아니다
        delete (Plain*)new PlainDer;             ★ 어떤 플래그로도 0건

   struct Poly  { virtual void f(); ~Poly(); };  가상 함수 1개 -> 다형적이다
        delete (Poly*)new PolyDer;               ★ 기본 플래그만으로 warning

   ──> 스위치는 「다형적인가」다. 14번이 만난 자리가 위쪽이었다.
```

| 지우는 대상 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | g++ `+ -Wnon-virtual-dtor` |
|---|---|---|---|
| ① **가상 함수가 하나도 없는 기반**(`Plain`) | ★★★ **0건** | ★★★ **0건** | ★★★ **0건** |
| ② **가상 함수가 있는 기반**(`Poly`) | ★★ **warning** | ★★ **warning** | ★★ **warning** (+ 3건 더) |

- ★★★ **①이 [14번](../14-destructors-and-deterministic-destruction/) (5)의 자리다** — **어떤 플래그로도 0건**이다.\
  ★ `-Wdelete-non-virtual-dtor` 는 **「다형적 클래스」일 때만** 발동하고, `Plain` 은 **가상 함수가 없어서 다형적이 아니다.**\
  ★ **그래서 경고의 조건**이 「소멸자가 비가상이다」가 아니라 「**다형적인데 소멸자가 비가상이다**」인 것이다.
- ★★★ **②는 기본 플래그만으로도 두 컴파일러가 다 말해 준다.** 경고 이름은 다르다\
  (`-Wdelete-non-virtual-dtor` 대 `-Wdelete-non-abstract-non-virtual-dtor`).
- ★★ **`-Wnon-virtual-dtor` 를 켜면 선언 자리에서도 셋을 더 말해 준다** — **삭제하는 줄을 안 써도** 잡힌다.\
  ★ 그런데 **①에는 여전히 0건**이다.
- ★★★ **결론** — **상속 계층을 「기반 포인터로 지울 것」으로 설계했다면 소멸자를 가상으로 두는 것이 유일한 방어**다.\
  ★ **가상 함수가 하나도 없는 기반은 도구가 절대 안 도와준다.**
- ★ **전모는 [목록의 20번 주제](../20-virtual-destructors-and-polymorphic-deletion/)다**. 여기서는 **계수와 경고 조건까지**다.

### (9) ★★ 생성자 속 가상 호출 — C# 과 정반대다

**언제 쓰나** — 기반 생성자에서 「초기화 훅」을 부르고 싶을 때.

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

```text
   D d;   를 만들 때

   B 의 생성자가 돈다      -> speak() 가 B::speak 로 간다   ★ 아직 D 가 아니다
   D 의 생성자 본문이 돈다 -> ready = 42
   다 지어진 뒤 d.speak()  -> D::speak  ready=42
   블록을 나간다
   B 의 소멸자가 돈다      -> speak() 가 다시 B::speak 로   ★ 이미 D 가 아니다
```

- ★★★ **생성자·소멸자 안에서는 동적 타입이 「그 시점의 클래스」다.**\
  ★ `B` 의 생성자가 도는 동안 객체는 **아직 `B` 일 뿐**이고, `B` 의 소멸자가 돌 때는 **이미 `B` 로 돌아왔다.**
- ★★★ **그래서 C++ 에서는 「안 터지는 대신 의도한 동작이 조용히 사라진다」.**\
  ★ `D::speak` 가 **한 번도 안 불린다.** 에러도 경고도 없다.
- ★★★ **C# 은 정반대다.** C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **12번**([`12-class-fields-constructors-this-base/`](../../../csharp/syntax/12-class-fields-constructors-this-base/)) (4)가 **양쪽을 나란히 실측했다.**

| | C# | C++ |
|---|---|---|
| 기반 생성자에서 가상 호출이 가는 곳 | ★★★ **파생 것**(`Child.Describe`) | ★★★ **기반 것**(`Parent::describe`) |
| 그때 파생 필드 초기자는 | ★ **이미 돌았다** | ★ **아직 안 돌았다** |
| 그래서 보이는 것 | **절반만 채워진 파생 상태** | **파생 상태를 아예 안 본다** |
| 터지나 | ★★ **`NullReferenceException` 이 날 수 있다** | **안 난다**(다른 함수가 불린다) |

- ★★★ **두 언어가 정반대로 안전하지 않다** — 그 편의 결론을 그대로 인용한다.\
  C# 은 **파생 코드가 미완성 상태를 보고**, C++ 은 **파생 코드가 아예 안 불려 동작이 사라진다.**\
  ★ **둘 다 「생성자에서 가상 함수를 부르지 마라」로 귀결되는데 이유가 다르다.**
- ★ **처방** — **생성이 끝난 뒤 부르는 `Initialize()` 를 따로** 두거나 **`final` 로 막는다.**

### (10) ★ 자바는 기본이 가상이다

**언제 쓰나** — 「`virtual` 을 왜 적어야 하지?」가 궁금할 때.

★ **「도구가 없다」고 적기 전에 버전 호출을 블록으로 남긴다**(규칙 26).

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

- ★★★ **`virtual` 을 아무 데도 안 적었는데 `D.who` 가 불린다.** 자바는 **기본이 가상**이다.
- ★★ **기본값이 반대이므로 「막는 낱말」도 반대다** — 자바는 **`final`** 로 막고, C++ 은 **`virtual`** 로 연다.\
  ★ C++ 의 `final` 은 **이미 가상인 것을 더 못 덮게** 하는 것이라 **같은 낱말이 다른 일**을 한다((5)).
- ★ **정본은 Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 9번**([`09-inheritance-overriding/`](../../../java/syntax/09-inheritance-overriding/))이다.\
  ★ 여기서는 **기본값이 반대라는 것 한 줄**만 실측했다.

### (11) ★★ vtable 을 찍어 본다 — 둘 다 됐다

**언제 쓰나** — 「가상 디스패치가 실제로 무엇으로 되나」를 볼 때.

★ **「없다」고 적기 전에 버전 호출을 블록으로 남긴다**(규칙 26).

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

- ★★★ **두 도구가 같은 것을 다른 말로 보여 준다.** 항목 수는 **둘 다 6개**다.
  - 0번 — `offset_to_top`(g++ 는 `(int (*)(...))0`).
  - 1번 — **RTTI 포인터**. (1)의 `typeid` 가 여기서 온다.
  - 2\~5번 — **함수 주소 넷**.
- ★★★ **`D` 의 vtable 에서 `f` 만 `D::f` 로 바뀌고 `g` 는 `B::g` 그대로**다.\
  ★ **재정의하지 않은 가상 함수는 기반의 주소가 그대로 복사된다.**
- ★★ **소멸자가 두 칸을 쓴다** — clang 이 `[complete]` 와 `[deleting]` 으로 **이름을 붙여 준다.**\
  ★ 뒤엣것이 **`delete p;` 가 부르는 것**이고, (8)의 사고가 **그 자리의 선택**이다.
- ★★★ **기본 인자는 vtable 에 없다** — 함수 주소만 있다. 그래서 (3)이 성립한다.
- ★★ **clang 의 `VTable indices` 가 한 가지를 더 보여 준다** — `B` 는 4개인데 `D` 는 **3개**이고\
  **인덱스 1이 빠져 있다**(`0 · 2 · 3`). **`D` 가 `g` 를 재정의하지 않았기 때문**이다.
- ★ **g++ 덤프에는 주소가 박힌다**(`(0x0x724f…`) — **흔들리는 칸**이다. 근거는 **항목 수와 그 자리의 이름**이다.
- ★★★ **비용은 재지 않았다.** 이 절이 보인 것은 **구조**이지 시간이 아니다 — 정본은 [목록의 **21번 주제**](../21-abstract-classes-pure-virtual-and-vtable-cost/)다.

### (12) 경고를 누가 보나 — 탐침 여덟

「경고가 안 났다」를 산문으로 적으면 **안 물어본 것과 물었는데 조용한 것이 구분되지 않는다.**\
그래서 **상속에서 틀리는 자리 여덟 개**를 한 파일에 심고 두 컴파일러에 똑같이 물었다.

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

| 심은 것 | g++ | clang | 실제로는 |
|---|---|---|---|
| 1. `const` 가 달라 재정의가 아니다 | ★ **1** | ★ **1** | ★★ **`-Woverloaded-virtual`** — 유일하게 답한 자리 |
| 2. 이름 오타(새 함수가 생긴다) | 0 | 0 | ★★★ 기반 것이 계속 불린다 |
| 3. 비가상 함수를 「재정의」 | 0 | 0 | ★★★ 정적 타입이 답을 정한다((1)(7)) |
| 4. 기본 인자가 다르다 | 0 | 0 | ★★★ 호출 자리마다 값이 갈린다((3)) |
| 5. 오버로드가 통째로 가려진다 | 0 | 0 | ★★ 변환되어 조용히 통과한다((4)) |
| 6. 제대로 재정의하는데 `override` 를 안 썼다 | 0 | 0 | ★ 다음 사람이 ①\~④를 못 잡는다 |
| 7. ★★★ **가상 소멸자 없이 다형적 삭제** | ★★★ **0건** | ★★★ **0건** | ★★★ **128바이트가 샌다**((8)) |
| 8. `override` 대신 `virtual` 을 다시 적었다 | 0 | 0 | ★ 재정의는 되지만 ①\~④를 못 잡는다 |

- ★★★ **탐침 여덟 중 답한 것 1, 침묵한 것 7이다.** **`cc exit=0`** 이고 프로그램은 끝까지 돈다.
- ★★★ **답한 그 하나가 `-Woverloaded-virtual` 이다** — **기반이 가상일 때만** 발동한다.\
  ★ 탐침 3번(기반이 비가상)에는 **같은 모양인데 침묵**한다. **조건**은 「**기반이 가상인가**」다.
- ★★★ **탐침 7번이 이 편의 핵심 공백이다** — **경고 0건**인데 **ASan 은 `new-delete-type-mismatch` 로 죽인다.**\
  ★ 그 이유가 (8)에 있다 — `B7` 에 **가상 함수가 하나도 없어서** 경고 조건이 안 맞는다.
- ★★ **`override` 를 적으면 탐침 1·2·4·6·8 이 전부 에러가 된다**((2)).\
  ★ **컴파일러가 안 보는 것을 프로그래머가 한 낱말로 보게 만드는 것**이 `override` 다.

## 문법 — 형태와 규칙

### 형태

```cpp
/* virt14.cpp */
// 상속·가상 함수 한 벌의 형태. 이 파일은 그대로 컴파일된다
#include <cstdio>
#include <memory>
#include <vector>

class Shape {                                    // ① 인터페이스 — 순수 가상 + 가상 소멸자
public:
    virtual ~Shape() = default;                  // ★ 기반 포인터로 지울 것이므로 가상
    virtual double area() const = 0;             // 파생이 반드시 구현한다
    virtual const char* name() const { return "Shape"; }   // 기본 구현이 있는 가상 함수
    double scaled(double k) const { return area() * k; }   // ② 비가상 — 가상 것을 부른다
};

class Square final : public Shape {              // ③ final — 더 물려받지 못하게 막는다
public:
    explicit Square(double s) : s_(s) {}
    double area() const override { return s_ * s_; }       // ★ override 를 반드시 적는다
    const char* name() const override { return "Square"; }
private:
    double s_;
};

class Circle : public Shape {
public:
    explicit Circle(double r) : r_(r) {}
    double area() const override { return 3.14159265358979 * r_ * r_; }
    const char* name() const override { return "Circle"; }
private:
    double r_;
};

int main() {
    std::vector<std::unique_ptr<Shape>> v;       // ④ 다형적 보관은 기반 포인터로
    v.push_back(std::make_unique<Square>(3));
    v.push_back(std::make_unique<Circle>(1));
    for (const auto& s : v)
        std::printf("%-6s area=%.4f  scaled(2)=%.4f\n", s->name(), s->area(), s->scaled(2));
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic virt14.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
Square area=9.0000  scaled(2)=18.0000
Circle area=3.1416  scaled(2)=6.2832
```

### 규칙

- **`virtual` 은 기반에 적고**, 파생에는 **`override` 를 적는다.** 파생의 `virtual` 은 **효과가 없다**((12)의 탐침 8번).
- ★★★ **재정의하면 반드시 `override`** — `const`·인자·반환·이름 넷을 **그 한 낱말이 잡는다**((2)).
- ★★★ **기반 포인터로 지울 것이면 소멸자를 `virtual` 로** — 안 그러면 파생 소멸자가 **안 돈다**((8)).
- **인터페이스는 순수 가상**(`= 0`)으로 정의한다. 하나라도 안 덮으면 **파생도 추상**이다((6)).
- ★★ **가상 함수에 기본 인자를 주지 않는다** — 정적 타입이 정하므로 호출 자리마다 갈린다((3)).
- ★★ **파생에 기반과 같은 이름을 두면 기반의 오버로드가 통째로 가려진다** — 필요하면 **`using B::f;`**((4)).
- **생성자·소멸자에서 가상 함수를 부르지 않는다** — **기반 것이 불린다**((9)).
- ★ **더 못 덮게 하려면 `final`** — 클래스에도 함수에도 붙는다((5)).
- ★ **비가상 함수를 파생에서 같은 이름으로 두지 않는다** — 재정의가 아니라 **숨김**이다((7)).

### 금지 사례 — 네 줄이 각각 막힌다

(2)의 네 에러가 그 자리다. **`override` 한 낱말이 넷을 전부 컴파일 시간으로 끌어올린다.**\
★ 같은 파일을 다시 싣지 않고, **`override` 를 지웠을 때 무엇이 되는지**를 (12)의 탐침 1\~4번이 보인다.

## 어디서 틀리나

### 1. ★★★ 「파생 객체니까 파생 함수가 불린다」

(1)의 `(3)` 이 반증이다 — `B&` 로 부른 **비가상** 함수는 `B::plain` 이다.\
★ **가상 함수만** 동적 타입을 본다. 나머지는 전부 **정적 타입**이다.

### 2. ★★★ 「`override` 는 적어도 되고 안 적어도 되는 것」

(2)가 보인 것은 **넷을 잡아 준다**는 것이고, (12)가 보인 것은 **안 적으면 컴파일러가 침묵한다**는 것이다.

### 3. ★★★ 「가상 함수를 재정의하면 기본 인자도 따라온다」

(3)이 반증이다 — **이름은 `D::f` 인데 `x` 가 1 이다.** 기본 인자는 **컴파일 시간에 끼워진다.**

### 4. ★★★ 「가상 소멸자를 빠뜨리면 메모리가 샌다」

**샌다는 말이 부족하다.** (8)이 보인 것은 **`~DerNV` 가 아예 안 돈다**는 것이다.\
★ 메모리만이 아니라 **파일 핸들·락·트랜잭션이 전부 안 놓인다.** 그리고 **경고는 0건**이다.

### 5. ★★ 「같은 이름을 파생에 두면 오버로드가 늘어난다」

(4)가 반증이다 — **기반 것이 통째로 가려진다.** 그리고 `d.f(1)` 이 **에러가 아니라 변환되어 통과한다.**

### 6. ★★ 「생성자에서 가상 함수를 부르면 파생 것이 불린다」

C++ 에서는 **기반 것이 불린다**((9)). ★ **C# 이 정반대**이므로 두 언어를 오가면 특히 위험하다.

### 7. ★ 「`virtual` 을 파생에도 적어야 한다」

적어도 **효과가 없다**((12)의 탐침 8번). 적을 것은 **`override`** 다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 규칙 전부를 덮고, 「구현 정의」 칸에 vtable 이 통째로 들어간다.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **가상 함수만 동적 타입을 본다**((1)) · ★★★ **기본 인자는 정적 타입이 정한다**((3)) · **이름 조회는 찾으면 멈춘다**((4)) · **`override` 가 잡는 넷**((2)) · **`final` 이 막는 둘**((5)) · **순수 가상을 안 덮으면 파생도 추상**((6)) · **생성자·소멸자에서는 그 시점의 클래스가 동적 타입**((9)) | 호출 로그 · `typeid` · 진단 전문 + `cc exit` | ★★★ 「**이 호출이 가상인가 아닌가**」 — 호출 자리만 보면 안 보인다((1)(7)) |
| **조건부 표준** | 특정 조건에서만 보장 | ★★ **`override`·`final` 은 C++11부터** · `-Woverloaded-virtual`·`-Wdelete-non-virtual-dtor` 는 **컴파일러의 호의**다((12)) | `-std=c++20` 으로만 돌렸다 | ★ **C++98 판으로는 안 돌려 봤다**(거기에는 `override` 가 없다) |
| **구현 정의** | 문서화 의무가 있다 | ★★★ **(11)의 vtable 전부** — 항목 수 6 · RTTI 자리 · **소멸자가 두 칸을 쓰는 것** · `offset_to_top` · **`typeid(...).name()` 의 꾸민 이름**(`1B`) · **vptr 8바이트**((8)의 `sizeof`) · 진단 문구 | 두 덤프 도구 · `sizeof` 출력 | ★★ **다른 ABI 에서는 배치가 다르다** — 이것은 **Itanium C++ ABI** 의 모습이다 |
| **미명시** | 몇 가지 중 하나 | ★ **경고를 낼지 말지** — (12)의 탐침 여덟 중 무엇에 답할지는 **컴파일러가 정한다** | 두 컴파일러 경고 개수 | ★ **다른 컴파일러는 더 잡을 수도 있다** |
| **UB** | 아무 일이나 | ★★★ **가상 소멸자 없이 기반 포인터로 지우는 것**((8)) — **표준이 UB 로 못 박았다** | ASan `new-delete-type-mismatch` · 계수 로그 | ★★★ **가상 함수가 없는 기반에서는 어떤 플래그로도 0건**((8)의 ①) |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | ASan | 호출 로그 |
|---|---|---|---|---|---|
| `override` 를 적고 재정의가 안 됨 | 표준 | **error 4** | **error 4** | — | — |
| `final` 클래스를 상속 · `final` 함수를 덮음 | 표준 | **error 2** | **error 2** | — | — |
| 추상 클래스를 인스턴스화 | 표준 | **error 2** | **error 2** | — | — |
| 기반이 **가상**인데 파생이 숨김 | 조건부 | ★ **warning 1** | ★ **warning 1** | — | ★ 로그 |
| ★★★ **기반이 비가상인데 파생이 숨김** | 표준 | ★★★ **0건** | ★★★ **0건** | ★★★ **0건** | ★★★ **로그만**((1)) |
| ★★★ **기본 인자가 다르다** | 표준 | ★★★ **0건** | ★★★ **0건** | ★★★ **0건** | ★★★ **로그만**((3)) |
| ★★★ **다형적 기반의 비가상 소멸자** | UB | ★★ **warning** | ★★ **warning** | ★ `new-delete-type-mismatch` | ★ 계수 |
| ★★★ **비다형적 기반의 비가상 소멸자** | UB | ★★★ **0건**(`-Wnon-virtual-dtor` 로도) | ★★★ **0건** | ★ `new-delete-type-mismatch` | ★ 계수 |

- ★★ **이 표의 결론 세 줄**
  - **`override`·`final`·추상 클래스는 전부 컴파일 시간에 걸린다** — **적기만 하면 된다.**
  - ★★★ **안 적으면 아무것도 안 걸린다.** 기본 인자·이름 숨김·비가상 재정의가 **전부 0건**이다.
  - ★★★ **가상 소멸자는 「기반이 다형적인가」로 갈린다** — 비다형적 기반은 **도구가 절대 안 도와준다.**

### ★ 진단이 0줄인 것도 블록으로 받았다

(12)가 그 자리다. **탐침 여덟 중 답한 것 1, 침묵한 것 7**이고 **`cc exit=0`** 이다.\
그 침묵을 메우는 것이 **(1)(3)(8)의 호출 로그·계수**와 **ASan 의 `new-delete-type-mismatch`** 다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 인터페이스를 정의한다 | ★★★ **순수 가상 + 가상 소멸자** | 안 덮으면 파생도 추상((6)) · 기반 포인터로 지운다((8)) |
| 파생에서 덮는다 | ★★★ **`override` 를 반드시** | 넷을 잡아 준다((2)) |
| 더 못 덮게 한다 | ★ **`final`** | 함수에도 클래스에도((5)) |
| 기본 인자를 주고 싶다 | ★★★ **가상 함수에는 주지 않는다** | 정적 타입이 정한다((3)) |
| 기반과 같은 이름을 파생에 둔다 | ★★ **`using B::f;` 를 같이** | 안 그러면 통째로 가려진다((4)) |
| 초기화 훅이 필요하다 | ★★★ **생성 후 `Initialize()`** | 생성자 속 가상 호출은 기반 것이 불린다((9)) |
| 기반 포인터로 안 지울 계층이다 | ★★ **소멸자를 `protected` 비가상으로** | 「기반으로 지우지 마라」를 타입으로 말한다 |
| 값 타입이다(상속할 일이 없다) | ★ **`final` 을 붙이거나 상속을 안 쓴다** | vptr 8바이트가 안 붙는다((8)의 `(4)`) |

- ★ **「가상 호출이 비싸니 피하라」는 이 문서의 조언이 아니다** — **비용은 재지 않았다.**\
  ★ 고르는 기준은 「**기반 포인터로 쓸 것인가**」이지 성능이 아니다. 비용 논의의 정본은 [목록의 **21번 주제**](../21-abstract-classes-pure-virtual-and-vtable-cost/)다.

## 핵심 문장

- **정적 타입은 선언이 말하는 것, 동적 타입은 실제 객체의 것**이고, **가상 함수만** 동적 타입을 본다.
- **`override` 는 네 가지 실수를 잡는다** — `const`·인자·반환·이름. **안 적으면 컴파일러가 침묵한다.**
- ★★★ **기본 인자는 정적 타입이, 본체는 동적 타입이 정한다** — 이름은 `D::f` 인데 `x` 가 `1` 이다.
- **파생에 같은 이름을 두면 기반의 오버로드가 통째로 가려지고**, `using` 으로 되살아난다.
- ★★★ **가상 소멸자가 없으면 파생 소멸자가 아예 안 돈다** — 128바이트가 샜고 **경고는 0건**이었다.
- **그 경고는 「기반이 다형적인가」로 갈린다** — 가상 함수가 없는 기반은 **어떤 플래그로도 0건**이다.
- **생성자·소멸자 안에서는 기반 것이 불린다** — **C# 은 정반대**이고, 둘 다 「부르지 마라」로 귀결된다.
- ★★★ **가상 호출의 비용은 이 문서가 재지 않았다.** 센 것은 **vtable 항목 수와 소멸자 호출 횟수까지**다.

## 관련 자료

- [14번](../14-destructors-and-deterministic-destruction/) — **(5)가 남긴 자리의 정본이 여기 (8)이다.**\
  그 편은 「경고 0건에 `run exit=0`」까지 보였고, 여기서 **계수·ASan·경고 조건**으로 닫았다.
- [12번](../12-class-basics-members-access-and-this/) — **클래스 기본.** `this`·접근 지정이 거기가 정본이다.
- [13번](../13-constructors-member-init-list-and-delegating/) — **생성자와 초기화 순서.** ★ **그 편은 상속을 안 다뤘다**(한 클래스 안의 선언 순서만).\
  (9)의 「기반이 먼저 지어진다」는 **여기가 처음 나오는 자리**다.
- [1번](../01-function-overloading-and-overload-resolution/) — **오버로드 해결.** (4)의 이름 숨김은 **그 절차의 앞 단계**인 이름 조회에서 벌어지는 일이다.
- [`oop-basics/`](../../../../oop-basics/) §14\~18 — **상속·다형성의 개념.** 여기는 **C++ 의 디스패치 규칙**까지.
- [목록의 **20번 주제**](../20-virtual-destructors-and-polymorphic-deletion/) — **가상 소멸자와 다형적 삭제의 전모.** (8)은 **계수와 경고 조건까지**다.
- [목록의 **21번 주제**](../21-abstract-classes-pure-virtual-and-vtable-cost/) — **추상 클래스·vtable 비용.** ★ **비용은 거기서 재야 한다** — 이 문서는 **구조만** 봤다.
- [목록의 **22번 주제**](../22-operator-overloading/) — 연산자 오버로딩. 멤버/비멤버 선택이 (4)의 이름 조회와 같은 축이다.
- ★★ C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **12번**([`12-class-fields-constructors-this-base/`](../../../csharp/syntax/12-class-fields-constructors-this-base/)) — **생성자 속 가상 호출이 정반대다.**\
  ★ 그 편 (4)가 **C# 과 C++ 을 나란히 실측했고**, (9)가 그 표를 인용한다.
- C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **16번 주제**(상속·`virtual`/`override`/`sealed`/`new`) — **C# 도 기본 비가상**이다.\
  ★ 다만 **숨기려면 `new` 를 적어야** 하고, 안 적으면 **경고가 난다.** C++ 은 (7)처럼 **조용히 숨긴다.**
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **9번**([`09-inheritance-overriding/`](../../../java/syntax/09-inheritance-overriding/)) — **자바는 기본 가상.** (10)에서 던져 봤다.

## 용어 풀이

> **정적 타입(static type)** — 선언이 말하는 타입. **컴파일 시간**에 정해진다.\
> 예: (1)에서 `typeid(decltype(r))` 가 `1B` 였다.

> **동적 타입(dynamic type)** — 실제 객체의 타입. **런타임**에 정해진다.\
> 예: 같은 `r` 에 대해 `typeid(r)` 이 `1D` 였다.

> **가상 함수(virtual function)** — **동적 타입으로 고르는 함수**. `virtual` 을 적어야 한다.\
> 예: (1)의 `(2)` 에서 `B&` 로 불렀는데 `D::who` 가 돌았다.

> **이름 숨김(name hiding)** — 파생이 같은 이름을 선언하면 **기반의 같은 이름이 전부 안 보이는** 것.\
> 예: (4)에서 `d.f(1)` 이 `D::f(double)` 로 갔다. **`using B::f;` 로 되살린다.**

> **순수 가상 함수(pure virtual function)** — `= 0` 으로 선언한 것. **파생이 반드시 덮어야** 한다.\
> 예: (6)에서 `Half` 가 안 덮어 **여전히 추상**이었다.

> **추상 클래스(abstract class)** — 순수 가상이 하나라도 남은 클래스. **객체를 만들 수 없다.**\
> 예: (6)에서 `Shape s;` 가 에러였다.

> **vtable** — 가상 함수의 주소를 담은 표. **객체마다가 아니라 클래스마다** 하나다.\
> 예: (11)에서 `B` 와 `D` 각각 **6개 항목**이었다. **구현 정의**다.

> **vptr** — 객체가 자기 클래스의 vtable 을 가리키는 포인터. **가상 함수가 하나라도 있으면 붙는다.**\
> 예: (8)의 `(4)` 에서 `BaseNV` 8 · `BaseV` 16 — **8바이트 차이**다.

> **`new-delete-type-mismatch`** — 할당한 크기와 놓는 크기가 다르다고 ASan 이 붙이는 이름.\
> 예: (8)에서 `allocated 16 bytes` 를 `deallocated 8 bytes` 로 놓았다.

## 더 들어가면

- **공변 반환 타입(covariant return type)** — `B* clone()` 을 파생이 `D* clone()` 으로 덮는 것. (2)의 ③이 **그 예외**를 안 건드린 자리다.
- **`dynamic_cast` 와 RTTI** — (11)의 vtable 1번 칸이 그 근거다. 정본은 [3번](../03-four-cast-operators/).
- **비가상 인터페이스(NVI) 관용구** — public 비가상이 protected 가상을 부르는 배치. (형태)의 `scaled()` 가 그 모양이다.
- **다중 상속과 가상 상속** — vtable 에 `offset_to_top` 이 왜 있는지가 거기서 쓰인다. 이 문서는 **단일 상속만** 봤다.
- **`final` 이 여는 최적화** — 정적 타입이 `final` 이면 가상 호출을 직접 호출로 바꿀 수 있다. ★ **이 문서는 그것을 재지 않았다** — [목록의 **21번 주제**](../21-abstract-classes-pure-virtual-and-vtable-cost/)다.
