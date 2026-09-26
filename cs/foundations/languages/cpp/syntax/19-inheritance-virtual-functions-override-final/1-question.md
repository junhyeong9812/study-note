# cpp/syntax/19 — 상속·가상 함수·`override`/`final` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「어느 쪽이 불리나」를 맞히는 것**이 절반이다 — 「파생 것이 불린다」로 뭉개지 말고
> **정적 타입이 정하는 자리와 동적 타입이 정하는 자리**를 갈라야 한다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · javac 21.0.5 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 본체는 「호출 로그 + `typeid`」다**(1번). 정적/동적 타입과 호출 결과를 **나란히** 찍는다.
> ★★ **네 번째 창은 「vtable 덤프」다**(8번) — `-fdump-lang-class`(g++)·`-fdump-vtable-layouts`(clang).
> ★ **「부적용인 창」이 있다** — `-O2` 어셈블리 세기.
> **가상 호출 비용은 이 문서가 재지 않는다.** 간접 호출 하나를 세는 것으로는 인라인 불가·분기 예측·캐시가 빠져 근거가 안 선다.
> **「안 쟀다」가 아니라 「여기서 잴 것이 아니다」다** — 정본은 목록의 **21번 주제**다.
> ★★★ **이 편은 16\~18 과 다른 축이다** — 저쪽이 「값이 어떻게 옮겨지나」라면 여기는 「호출이 어디로 가나」다.
> 겹치는 자리는 6번 하나이고, **[14번](../14-destructors-and-deterministic-destruction/) (5)가 남긴 「경고 0건」의 정본이 그것**이다.
> 대비 — ★★ C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **12번**([`12-class-fields-constructors-this-base/`](../../../csharp/syntax/12-class-fields-constructors-this-base/))과 Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **9번**([`09-inheritance-overriding/`](../../../java/syntax/09-inheritance-overriding/))을 7번·8번에서 던진다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 같은 객체에 네 가지 이름을 붙이면 (예측)

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

- `typeid(decltype(r))` 와 `typeid(r)` 은 **같은가 다른가** — 왜 그런가?
- ★★ `typeid(*p)` 와 `typeid(p)` 는 각각 무엇인가?
- ★★★ `(2)`·`(3)`·`(4)` 에서 각각 **어느 쪽 함수**가 도나 — `(3)` 과 `(4)` 는 **같은 객체**인데 왜 갈리나?

### 2. ★★★ `override` 가 잡는 실수 넷 (예측)

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

- 네 줄 각각에서 **무엇이 실수**인가 — 그리고 **몇 건의 에러**가 나나?
- ★★★ `override` 를 **전부 지우면** 이 파일은 컴파일되나 — 안 되는 것이 하나 있다면 어느 것인가?
- ★ 두 컴파일러 중 **이유를 더 짚어 주는 쪽**은 어디인가?

### 3. ★★★ 기본 인자가 다른 가상 함수 (예측)

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

- `(1)`\~`(5)` 에 각각 **무슨 이름**이 찍히고 **`x` 는 몇**인가?
- ★★★ 찍히는 이름과 `x` 가 **서로 다른 것에 따라 정해진다** — 각각 무엇이 정하나?
- ★ 그래서 **처방**은 무엇인가?

### 4. ★★ 이름 숨김 (예측)

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

- `(1)` 의 `d.f(1)` 은 **어디로 가나** — 에러인가 아닌가?
- ★★ `(2)`·`(3)` 에서 `E` 는 `D` 와 어떻게 다른가 — **무엇 한 줄** 때문인가?
- ★★★ 이 예제의 `f` 들 중 **가상인 것이 몇 개**인가 — 이 현상이 `virtual` 과 관계가 있나?

```cpp
/* virt05.cpp */
// 이름 숨김이 에러가 되는 자리 — 문자열은 double 로 안 바뀐다
struct B { void f(int); void f(const char*); };
struct D : B { void f(double); };
int main() { D d; d.f("x"); }
```

- 이 파일의 에러는 기반의 `f(const char*)` 를 **언급하나** — 왜 그런가?

### 5. ★ `final` 과 추상 클래스 (경계)

```cpp
/* virt06.cpp */
// final 이 막는 것 둘 — 클래스를 더 못 물려받는 것과 함수를 더 못 덮는 것
struct Sealed final { };
struct Try : Sealed { };                       // 1. final 클래스를 상속했다

struct B { virtual void f() final {} virtual ~B() = default; };
struct D : B { void f() override {} };         // 2. final 함수를 덮었다
int main() { }
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

- 각 파일에서 **몇 건의 에러**가 나나 — `final` 이 막는 것 **둘**은 무엇인가?
- ★★ 두 번째 파일에서 `Half h;` 가 왜 에러인가 — 「파생이니까 괜찮다」가 왜 틀리나?
- ★ 이 예제의 `name()` 은 **순수 가상인가** — 순수 가상과 무엇이 다른가?

### 6. ★★★ 가상 소멸자가 없으면 무엇이 안 도나 (예측)

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

- `(1)`·`(2)`·`(3)` 에서 **`~Der` 가 몇 번** 돌고 **놓은 바이트**는 각각 몇인가?
- ★★★ `(1)` 과 `(2)` 는 **같은 타입**인데 왜 갈리나?
- ★★ `(4)` 의 네 `sizeof` 는 어떤 규칙으로 갈리나?
- ★★★ 같은 일을 ASan 에게 물으면 **무슨 이름**이 붙나 — 「누수」인가 다른 것인가?

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

- ★★★ 이 파일의 **두 자리** 중 컴파일러가 경고하는 쪽은 어디인가 — 그리고 **`-Wnon-virtual-dtor` 를 켜도 0건인 쪽**은?
- ★★★ 그 경고의 조건은 「소멸자가 비가상이다」인가, 아니면 **다른 무엇**인가?

### 7. ★★ 생성자 안에서 가상 함수를 부르면 (예측)

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

- `(1)` 에서 `speak()` 는 **어느 쪽**이 불리나 — 소멸자에서는?
- ★★★ **C# 은 어느 쪽이 불리나** — 어느 갈래 몇 번이 그것을 실측했나?
- ★ 두 언어가 **각각 다른 이유로 위험한데** 처방은 왜 같은가?

### 8. ★★ vtable 을 찍을 수 있나 (경계)

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

- g++ 와 clang 으로 **vtable 을 찍을 수 있나** — 된다면 명령이 무엇인가?
- ★★ `B` 와 `D` 의 항목 수는 각각 몇이고, **`D` 에서 바뀐 자리**는 어디인가?
- ★★★ **기본 인자가 vtable 에 들어 있나** — 그것이 3번과 어떻게 이어지나?
- ★ 이 절에서 **재지 않은 것**은 무엇인가?

### 9. ★★ 경고를 누가 보나 (경계)

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

- 탐침 **여덟 중 몇 개**에 두 컴파일러가 답하나 — 답한 것은 몇 번인가?
- ★★★ 탐침 **3번**(비가상 재정의)과 **1번**(가상 재정의 실패)은 같은 모양인데 하나만 답한다 — **조건이 무엇**인가?
- ★★ 같은 파일을 ASan 으로 돌리면 무엇이 잡히나 — 그것이 **탐침 어느 자리**인가?

### 10. ★★ 이 주제의 사실이 다섯 층 중 어디에 있나 (경계)

- 「**기본 인자는 정적 타입이 정한다**」는 **표준인가 구현 정의인가**?
- 「**vtable 항목이 6개다**」는 **표준인가 구현 정의인가**?
- ★★ 「**가상 소멸자 없이 기반 포인터로 지우는 것**」은 **UB 인가** — 그렇다면 왜 경고가 없는 자리가 있나?
- ★ `typeid(...).name()` 이 `1B` 로 나오는 것은 어느 층인가?

### 11. 다른 주제와 잇기 (연결)

- **[14번](../14-destructors-and-deterministic-destruction/)이 「경고 0건」으로 남겨 둔 자리**를 여기 어느 절이 닫았나?
- ★★ **이름 숨김**은 오버로드 해결의 **어느 단계**에서 벌어지는 일인가 — 몇 번 주제인가?
- ★★ **생성자 속 가상 호출**의 양쪽 실측은 어느 갈래 몇 번인가?
- ★ **자바는 기본 가상이다** — 어느 갈래 몇 번인가? 그러면 **막는 낱말**은 무엇인가?
- ★★ **가상 호출 비용**은 어느 주제에서 재야 하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
