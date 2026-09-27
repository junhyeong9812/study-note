# cpp/syntax/20 — 가상 소멸자와 다형적 삭제 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「누가 `delete` 식을 쓰고, 그때 어떤 타입을 들고 있나」를 맞히는 것**이 절반이다 —
> 「스마트 포인터니까 안전하다」로 뭉개지 말고 **삭제자가 기억한 타입**을 따라가야 한다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 본체는 「호출 로그」다**(1번) — `shared_ptr` 대 `unique_ptr` 에 같은 객체를 맡긴다.
> ★★ **짝은 `<type_traits>` 격자다**(4번) — [18번](../18-rule-of-zero-three-five-default-delete/)의 형식 그대로.
> ★ **「부적용인 창」이 있다** — `-O2` 어셈블리 세기. 이 주제에는 **잴 비용이 없다.**
> ★★★ **[19번](../19-inheritance-virtual-functions-override-final/)이 잰 것은 다시 묻지 않는다** — `~DerNV` 0회 · 128바이트 · `new-delete-type-mismatch`(16 대 8) · 「경고의 스위치는 기반이 다형적인가」.
> 여기서 묻는 것은 **「무엇이 미정의인가」의 층**과 **「언제 가상으로 둘까」의 판단**이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 가상 소멸자가 없는 기반을 다섯 가지로 맡기면 (예측)

```cpp
/* vdtor01.cpp */
// 소멸자가 가상이 아닌 기반 — shared_ptr 와 unique_ptr 에 같은 파생 객체를 맡긴다
#include <cstdio>
#include <memory>

struct Base {                                       // ★ 소멸자가 가상이 아니다
    ~Base() { std::printf("      ~Base\n"); }
};
struct Derived : Base {
    ~Derived() { std::printf("      ~Derived\n"); }
};

int main() {
    std::printf("(1) shared_ptr<Base>(new Derived)\n");
    { std::shared_ptr<Base> p(new Derived); }

    std::printf("(2) shared_ptr<Base> = make_shared<Derived>()\n");
    { std::shared_ptr<Base> p = std::make_shared<Derived>(); }

    std::printf("(3) Base* 로 먼저 받은 뒤 shared_ptr<Base>(raw)\n");
    { Base* raw = new Derived; std::shared_ptr<Base> p(raw); }

    std::printf("(4) unique_ptr<Base>(new Derived)\n");
    { std::unique_ptr<Base> p(new Derived); }

    std::printf("(5) unique_ptr<Derived> 를 unique_ptr<Base> 로 옮긴다\n");
    { std::unique_ptr<Base> p = std::make_unique<Derived>(); }

    std::printf("(6) sizeof  shared_ptr<Base> %zu · unique_ptr<Base> %zu\n",
                sizeof(std::shared_ptr<Base>), sizeof(std::unique_ptr<Base>));
}
```

- `(1)`\~`(5)` 각각에서 **어느 소멸자가 몇 번** 도나?
- ★★★ `(1)` 과 `(3)` 은 **둘 다 `shared_ptr<Base>`** 인데 결과가 같은가 — 다르다면 무엇이 갈랐나?
- ★★ `(5)` 는 `make_unique<Derived>` 로 만들었다 — 그래도 `(4)` 와 같은가?
- ★ `(6)` 의 두 `sizeof` 는 각각 얼마인가?

### 2. ★★★ ASan 스택이 삭제자의 정체를 보여 준다 (왜)

- ★★★ `shared_ptr<Base>(new Derived)` 가 가상 소멸자 없이도 `~Derived` 를 부르는 것은 **구현의 호의인가 표준의 보장인가**?
- ★★ 같은 대비를 ASan 에게 물으면 `r`(raw `Base*` 를 거친 `shared_ptr`)의 스택에 **어떤 템플릿 이름**이 찍히나 — 그 이름이 무엇을 증명하나?
- ★ `s`(`shared_ptr<Base>(new Derived)`)에서 ASan 이 침묵하는 것은 「경로를 안 밟아서」인가?

### 3. ★★★ 선을 긋는다 — 다섯 줄 중 UB 는 어느 것인가 (경계)

```text
   ① delete (Base*)new Derived;              Base 소멸자 비가상
   ② delete (Base*)new Derived;              Base 소멸자 가상
   ③ std::shared_ptr<Base>(new Derived)      Base 소멸자 비가상
   ④ std::unique_ptr<Base>(new Derived)      Base 소멸자 비가상
   ⑤ Base* b = new Derived[3]; delete[] b;   Base 소멸자 가상
```

- 다섯 줄 각각이 **보장**인가 **UB** 인가?
- ★★ ⑤는 소멸자가 가상인데도 왜 그런가?

### 4. ★★ `has_virtual_destructor` 격자 (예측)

```cpp
/* vdtor03.cpp */
// has_virtual_destructor 격자 — 소멸자를 어떻게 선언했나에 따라 무엇이 갈리나
#include <cstdio>
#include <string>
#include <type_traits>

struct NV    { std::string s; ~NV() {} };                        // 비가상 소멸자
struct V     { std::string s; virtual ~V() = default; };         // 가상 소멸자 = default
struct V5    { std::string s; virtual ~V5() = default;           // 가상 소멸자 + 이동을 되살렸다
               V5() = default;
               V5(const V5&) = default;            V5& operator=(const V5&) = default;
               V5(V5&&) noexcept = default;        V5& operator=(V5&&) noexcept = default; };
struct PV    { std::string s; virtual void f() {} protected: ~PV() = default; };  // protected 비가상
struct Fin final { std::string s; virtual void f() {} ~Fin() = default; };        // final + 비가상
struct Zero  { std::string s; };                                 // 아무것도 안 썼다
struct DerV  : V { };                                            // 가상 소멸자를 물려받았다

template <class T> void row(const char* name) {
    std::printf("%-5s |  %d    %d   |  %d    %d   |  %d    %d   |  %2zu\n", name,
        (int)std::has_virtual_destructor_v<T>,
        (int)std::is_polymorphic_v<T>,
        (int)std::is_destructible_v<T>,
        (int)std::is_trivially_destructible_v<T>,
        (int)std::is_move_constructible_v<T>,
        (int)std::is_nothrow_move_constructible_v<T>,
        sizeof(T));
}

int main() {
    std::printf("타입  | 가상소멸 다형 | 소멸가능 trivial | 이동생 noexcept | sizeof\n");
    row<Zero>("Zero"); row<NV>("NV"); row<V>("V"); row<V5>("V5");
    row<PV>("PV"); row<Fin>("Fin"); row<DerV>("DerV");
}
```

- ★★ `V`(`virtual ~V() = default;`)의 **`noexcept` 이동 칸**은 0 인가 1 인가 — `V5` 와 같은가?
- ★★★ `PV`(`protected` 소멸자)의 **소멸가능 칸과 이동생 칸**은 각각 무엇인가 — 이동 생성자는 멀쩡히 있는데 왜 그런가?
- ★ `DerV` 의 가상소멸 칸은? · `Fin` 의 다형 칸은?

### 5. ★★★ 습관처럼 적은 `virtual ~VB() = default;` (예측)

```cpp
/* vdtor04.cpp */
// virtual ~B() = default; 한 줄이 이동을 지운다 — 18편의 「소멸자를 쓰면 이동이 사라진다」와 같은 규칙인가
#include <cstdio>
#include <utility>
#include <vector>

struct Tr {                                      // 멤버 — 무엇이 불렸는지 말한다
    Tr() {}
    Tr(const Tr&)          { std::printf("      멤버: 복사\n"); }
    Tr(Tr&&)      noexcept { std::printf("      멤버: 이동\n"); }
    Tr& operator=(const Tr&)          { std::printf("      멤버: 복사 대입\n"); return *this; }
    Tr& operator=(Tr&&)      noexcept { std::printf("      멤버: 이동 대입\n"); return *this; }
    ~Tr() {}
};

struct Zero { Tr t; };                                      // 아무것도 안 썼다
struct VB   { Tr t; virtual ~VB() = default; };             // ★ 가상 소멸자 = default 한 줄
struct VB5  { Tr t; virtual ~VB5() = default;               // 이동을 = default 로 되살렸다
              VB5() = default;
              VB5(const VB5&) = default;         VB5& operator=(const VB5&) = default;
              VB5(VB5&&) noexcept = default;     VB5& operator=(VB5&&) noexcept = default; };

template <class T> void probe(const char* name) {
    std::printf("(%s) std::move 로 만들고 std::move 로 대입한다\n", name);
    { T a; T b = std::move(a); T c; c = std::move(b); }
    std::printf("(%s) vector 재할당 — 자리 둘에 셋째를 넣는다\n", name);
    { std::vector<T> v; v.reserve(2); v.emplace_back(); v.emplace_back(); v.emplace_back(); }
}

int main() {
    probe<Zero>("Zero");
    probe<VB>("VB");
    probe<VB5>("VB5");
}
```

- `Zero`·`VB`·`VB5` 각각에서 `std::move` 로 만들고 대입하면 멤버가 **이동되나 복사되나**?
- ★★★ `VB` 의 소멸자는 본문도 없는 `= default` 다 — 그래도 18편의 「소멸자를 쓰면 이동이 사라진다」가 걸리나?
- ★ `vector` 재할당은 셋 각각에서 무엇으로 옮기나?

### 6. ★★ `protected` 비가상 소멸자 (예측)

```cpp
/* vdtor05.cpp */
// protected 비가상 소멸자 — 「기반 포인터로 지우지 마라」를 타입으로 말한다
struct Base {
    virtual void f() {}
protected:
    ~Base() = default;                  // ★ 비가상이지만 바깥에서 부를 수 없다
};
struct Derived final : Base {
    void f() override {}
};

int main() {
    Derived* d = new Derived;
    Base* b = d;
    delete d;                           // 1. 파생 포인터로 지운다
    Base* b2 = new Derived;
    delete b2;                          // 2. 기반 포인터로 지운다
    Derived local;                      // 3. 지역 객체
    (void)b; (void)local;
}
```

- 1\~3번 중 **어느 줄이 컴파일 에러**인가 — 에러와 함께 나는 것이 또 있나?
- ★★ 같은 기반을 `std::unique_ptr<Base>` 에 맡기면 에러가 **어느 파일의 어느 줄**에서 나나?
- ★ `Derived` 에 `final` 을 붙인 이유는 무엇인가?

### 7. ★ 소멸자가 가상인데 파생 배열을 기반 포인터로 `delete[]` (예측)

```cpp
/* vdtor07.cpp */
// 파생 배열을 기반 포인터로 delete[] 한다 — 소멸자가 가상이어도 되나
// 마커는 표준 오류로 찍는다 — sanitizer 가 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>

struct Base {
    long id = 0;
    virtual ~Base() {                         // id 가 0~99 밖이면 값 대신 그 사실만 찍는다(주소일 수 있다)
        if (id >= 0 && id < 100) std::fprintf(stderr, "      ~Base  id=%ld\n", id);
        else                     std::fprintf(stderr, "      ~Base  id=(0~99 밖의 값)\n");
    }
};
struct Derived : Base {
    long extra = 7;
    ~Derived() override { std::fprintf(stderr, "      ~Derived id=%ld\n", id); }
};

int main() {
    std::fprintf(stderr, "(1) sizeof Base %zu · Derived %zu\n", sizeof(Base), sizeof(Derived));
    std::fprintf(stderr, "(2) Derived[3] 을 Derived* 로 delete[] — 대조군\n");
    { Derived* d = new Derived[3]; for (long i = 0; i < 3; ++i) d[i].id = i; delete[] d; }
    std::fprintf(stderr, "(3) Derived[3] 을 Base* 로 delete[]\n");
    Base* b = new Derived[3];
    delete[] b;
    std::fprintf(stderr, "(4) 여기까지 왔다\n");
}
```

- g++ 판과 clang 판의 **`run exit`** 는 각각 무엇인가 — `(4)` 는 찍히나?
- ★★ clang 판이 끝까지 간다면 `~Derived` 는 몇 번 돌고 `~Base` 의 `id` 는 무엇이 찍히나?
- ★★ ASan 을 붙이면 두 컴파일러가 각각 무엇이라고 하나?

### 8. ★ `delete p` 가 부르는 `operator delete` 는 누구의 것인가 (예측)

```cpp
/* vdtor08.cpp */
// delete p 가 부르는 operator delete 는 누구의 것인가 — 클래스마다 operator delete 를 두고 로그를 찍는다
#include <cstdio>
#include <cstdlib>
#include <new>

struct Base {
    long a = 0;
    virtual ~Base() {}
    static void* operator new(std::size_t n) { std::printf("      Base::operator new    %zu\n", n); return std::malloc(n); }
    static void  operator delete(void* p, std::size_t n) { std::printf("      Base::operator delete %zu\n", n); std::free(p); }
};
struct Derived : Base {                           // 자기 operator delete 를 둔다
    long b = 0;
    static void* operator new(std::size_t n) { std::printf("      Derived::operator new    %zu\n", n); return std::malloc(n); }
    static void  operator delete(void* p, std::size_t n) { std::printf("      Derived::operator delete %zu\n", n); std::free(p); }
};
struct Plain : Base {                             // 자기 것이 없다 — Base 의 것을 물려받는다
    long c[4] = {};
};

int main() {
    std::printf("(1) Base* p = new Base;    delete p;\n");
    { Base* p = new Base;    delete p; }
    std::printf("(2) Base* p = new Derived; delete p;\n");
    { Base* p = new Derived; delete p; }
    std::printf("(3) Base* p = new Plain;   delete p;\n");
    { Base* p = new Plain;   delete p; }
    std::printf("(4) 지역 객체 Derived d; — operator delete 가 불리나\n");
    { Derived d; }
    std::printf("(5) sizeof Base %zu · Derived %zu · Plain %zu\n", sizeof(Base), sizeof(Derived), sizeof(Plain));
}
```

- `(1)`\~`(3)` 에서 **누구의 `operator delete` 가 몇 바이트로** 불리나?
- ★★ `(3)` 의 `Plain` 은 자기 해제 함수가 없다 — 불리는 함수와 넘어오는 크기가 **같은 클래스의 것**인가?
- ★ `(4)` 의 지역 객체는 `operator delete` 를 부르나?

### 9. ★ 순수 가상 소멸자 (경계)

- ★★ `virtual ~Base() = 0;` 만 적고 정의를 안 주면 **컴파일 에러·링크 에러·런타임 에러** 중 무엇인가?
- ★★ 다른 순수 가상 함수(`f() = 0`)는 정의 없이도 되는데 소멸자만 왜 안 되나?
- ★ `virtual ~Base() = 0 {}` 처럼 한 줄에 쓰면?

### 10. ★★ 다형적 삭제의 탐침 일곱 — 경고를 누가 보나 (경계)

- ★★ 탐침 일곱(다형 기반 `delete` · `final` · `protected` · 배열 `delete[]` · raw 를 거친 `shared_ptr` · `unique_ptr<Poly>` · 가상 소멸자가 지운 이동) 중 **g++ 와 clang 이 각각 몇 개에** 답하나?
- ★★★ 두 컴파일러가 **갈린 탐침**은 어느 것이고, 왜 g++ 에서는 「감싸면 경고가 사라지나」?
- ★ `-Wnon-virtual-dtor` 를 켜면 **답한 탐침 수**가 늘어나나?

### 11. ★★★ 언제 가상으로 둘까 (왜)

- ★★★ 소멸자를 **`public virtual`·`protected` 비가상·`final` 클래스** 중 무엇으로 둘지 가르는 질문 셋은 무엇인가?
- ★★ 「가상 함수가 하나라도 있으면 소멸자도 가상」이라는 어림규칙이 **빠뜨리는 자리**는 어디인가?
- ★ 「`shared_ptr` 로만 쓸 것이니 가상 소멸자는 필요 없다」를 근거로 삼으면 안 되는 이유는?

### 12. 다섯 층과 다른 주제 잇기 (연결)

- ★★ 「`delete[]` 의 소멸자를 가상으로 부를지 직접 부를지」는 **표준·구현 정의·미명시·UB** 중 어디인가?
- ★★ 소멸자가 vtable 에 **두 칸**인 것을 19편은 **어떤 창**으로 봤고, 이 편은 **어떤 창**으로 다시 물었나?
- ★ `virtual ~B() = default` 가 이동을 지우는 규칙의 정본은 몇 번 주제인가?
- ★ `shared_ptr` 가 `unique_ptr` 보다 8바이트 큰 것과 같은 모양을 먼저 찍은 편은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
