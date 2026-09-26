# cpp/syntax/18 — 0/3/5의 법칙 · `=default`/`=delete` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **격자의 0/1 을 맞히는 것**이 절반이다 — 「생긴다」로 뭉개지 말고
> **어느 칸이 0 이고 어느 칸이 1 인지**를 맞혀야 한다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 본체는 앞 두 편과 다르다** — **`<type_traits>` 격자**다(1번·3번·5번).
> 「자동 생성됐나」는 **호출 로그로는 안 보인다.** 안 만들어진 것은 **불리지도 않기 때문**이다.
> ★★★ **「제5의 상태」가 2번에 있다** — **격자가 답을 못 주는 칸**이 있다.
> `is_move_constructible` 은 두 타입에 **둘 다 1** 을 준다. **같은 질문을 다른 창으로 바꿔 물어야** 답이 나온다.
> ★ **「부적용인 창」이 있다** — `-O2` 어셈블리 세기. 이 편의 질문은 **선언의 유무**이고
> 그것은 **어셈블리가 아니라 트레이트가 답한다**. **「안 쟀다」가 아니라 「잴 것이 없다」다.**
> 선행 — ★★★ [16번](../16-copy-constructor-and-copy-assignment/) → [17번](../17-move-constructor-assignment-and-moved-from-state/) → **이 편**이 한 사슬이고 **이 편이 결론**이다.
> 대비 — Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **9번**([`09-copy-clone-and-drop/`](../../../rust/syntax/09-copy-clone-and-drop/))은 기본값이 「**아무것도 안 준다**」인 판이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 아홉 타입의 격자를 채워 보라 (예측)

```cpp
/* rule01.cpp */
// 컴파일러가 무엇을 자동 생성했나 — 특수 멤버 다섯을 격자로 찍는다
#include <cstdio>
#include <memory>
#include <string>
#include <type_traits>
#include <vector>

struct S0 { int x; };                                     // 아무것도 안 썼다
struct S1 { int x; ~S1() {} };                            // 소멸자만 썼다
struct S2 { int x; S2(const S2&) = default; };            // 복사 생성자만 선언했다
struct S3 { int x; S3(S3&&) = default; };                 // 이동 생성자만 선언했다
struct S4 { int x;                                        // 다섯을 전부 = default
            S4() = default; ~S4() = default;
            S4(const S4&) = default; S4& operator=(const S4&) = default;
            S4(S4&&) = default;      S4& operator=(S4&&) = default; };
struct S5 { int x; S5(const S5&) = delete; };             // 복사 생성자를 지웠다
struct S6 { std::unique_ptr<int> p; std::vector<int> v; };// 0의 법칙 — 자원을 남에게 맡겼다
struct S7 { std::string s; };                             // 무거운 멤버 하나, 아무것도 안 썼다
struct S8 { std::string s; ~S8() {} };                     // 같은 멤버 + 소멸자 한 줄

template <class T> void row(const char* name) {
    std::printf("%-3s |  %d   %d   %d   %d   %d  |   %d\n", name,
        (int)std::is_default_constructible_v<T>,
        (int)std::is_copy_constructible_v<T>,
        (int)std::is_copy_assignable_v<T>,
        (int)std::is_move_constructible_v<T>,
        (int)std::is_move_assignable_v<T>,
        (int)std::is_nothrow_move_constructible_v<T>);
}

int main() {
    std::printf("타입 | 기본 복사생 복사대 이동생 이동대 | 이동이 noexcept 인가\n");
    row<S0>("S0"); row<S1>("S1"); row<S2>("S2"); row<S3>("S3");
    row<S4>("S4"); row<S5>("S5"); row<S6>("S6"); row<S7>("S7"); row<S8>("S8");
}
```

- `S1`(소멸자만) 의 여섯 칸은 `S0`(아무것도 안 씀) 과 **어디가 다른가**?
- ★★★ `S3`(이동 생성자만) 의 **복사 두 칸**은 0 인가 1 인가 — 왜 그런가?
- ★★ `S5`(복사 생성자 `= delete`) 의 복사 생성 칸과 복사 대입 칸은 **같은가 다른가**?
- ★★★ `S7`(`string` 멤버) 과 `S8`(`string` 멤버 + 소멸자 한 줄)이 **갈리는 칸은 몇 개**인가?

### 2. ★★★ 소멸자 한 줄을 더하면 (예측)

```cpp
/* rule02.cpp */
// 소멸자 한 줄을 더하면 이동이 조용히 사라진다 — 격자가 아니라 계수 로그가 답한다
#include <cstdio>
#include <type_traits>
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

struct Zero { Tr t; };                           // 0의 법칙 — 다섯을 하나도 안 썼다
struct Dtor { Tr t; ~Dtor() {} };                // 소멸자 한 줄만 더했다

int main() {
    std::printf("(1) Zero — 아무것도 안 쓴 타입\n");
    { Zero a; Zero b = std::move(a); Zero c; c = std::move(b); }
    std::printf("(2) Dtor — 소멸자 한 줄만 더한 타입\n");
    { Dtor a; Dtor b = std::move(a); Dtor c; c = std::move(b); }

    std::printf("(3) 격자는 무엇이라고 답하나\n");
    std::printf("    is_move_constructible          Zero=%d  Dtor=%d   ← 둘 다 1이라 안 갈린다\n",
                (int)std::is_move_constructible_v<Zero>, (int)std::is_move_constructible_v<Dtor>);
    std::printf("    is_nothrow_move_constructible  Zero=%d  Dtor=%d   ← 여기서 갈린다\n",
                (int)std::is_nothrow_move_constructible_v<Zero>,
                (int)std::is_nothrow_move_constructible_v<Dtor>);

    std::printf("(4) 그래서 vector 재할당이 갈린다\n");
    {
        std::printf("    [Zero] ");  std::printf("자리 둘을 잡고 둘을 넣은 뒤 셋째를 넣는다\n");
        std::vector<Zero> v; v.reserve(2); v.emplace_back(); v.emplace_back(); v.emplace_back();
    }
    {
        std::printf("    [Dtor] ");  std::printf("자리 둘을 잡고 둘을 넣은 뒤 셋째를 넣는다\n");
        std::vector<Dtor> v; v.reserve(2); v.emplace_back(); v.emplace_back(); v.emplace_back();
    }
}
```

- `(1)` 과 `(2)` 에 각각 **무슨 로그**가 찍히나 — 소스 차이는 **무엇 하나**인가?
- ★★★ `(3)` 에서 `is_move_constructible` 은 두 타입에 **각각 무엇**이라고 답하나?
- ★★★ 그렇다면 「이동이 사라졌다」를 **무엇으로 보여야** 하나?
- ★★ `(4)` 의 `vector` 재할당은 두 타입에서 **어떻게 갈리나** — 그것이 몇 번 주제의 어느 절과 같은가?

### 3. ★★ `= default` 와 빈 본문 `{}` (예측)

```cpp
/* rule03.cpp */
// = default 는 빈 본문 {} 과 다르다 — trivial 인가로 갈린다
#include <cstdio>
#include <type_traits>

struct T0 { int x; };                                  // 아무것도 안 썼다
struct T1 { int x; T1() = default; };                  // 기본 생성자 = default
struct T2 { int x; T2() {} };                          // 기본 생성자 빈 본문
struct T3 { int x; ~T3() = default; };                 // 소멸자 = default
struct T4 { int x; ~T4() {} };                         // 소멸자 빈 본문
struct T5 { int x; T5(const T5&) = default; };         // 복사 생성자 = default
struct T6 { int x; T6(const T6& o) : x(o.x) {} };      // 복사 생성자를 손으로 썼다
struct T7 { int x; ~T7(); };                           // 선언만 하고
T7::~T7() = default;                                   // ★ 클래스 밖에서 = default

template <class T> void row(const char* name) {
    std::printf("%-3s |   %d     %d     %d     %d   |  %zu\n", name,
        (int)std::is_trivially_default_constructible_v<T>,
        (int)std::is_trivially_copyable_v<T>,
        (int)std::is_trivially_destructible_v<T>,
        (int)std::is_trivial_v<T>,
        sizeof(T));
}

int main() {
    std::printf("타입 | t기본 t복사 t소멸 trivial | sizeof\n");
    row<T0>("T0"); row<T1>("T1"); row<T2>("T2"); row<T3>("T3");
    row<T4>("T4"); row<T5>("T5"); row<T6>("T6"); row<T7>("T7");
}
```

- `T1`(`= default`) 과 `T2`(`{}`) 의 **`trivial` 칸**은 각각 0 인가 1 인가?
- ★★★ `T4`(빈 소멸자 `{}`) 의 **네 칸**은 몇 개가 0 인가?
- ★★★ `T7`(**클래스 밖** `= default`) 은 `T3`(클래스 안 `= default`) 과 같은가 — 다르면 어느 타입과 같아지나?
- ★ 여덟 타입의 **`sizeof`** 는 갈리나?

### 4. ★★ `= delete` 가 오버로드 해결에 참여한다 (예측)

```cpp
/* rule04.cpp */
// = delete 는 후보에서 빠지는 것이 아니라 뽑힌 뒤 거부된다
#include <cstdio>
void f(int)    { std::printf("f(int)\n"); }
void f(double) = delete;                       // 실수로 double 로 부르는 것을 막고 싶다

struct M {
    int x;
    M() : x(0) {}
    M(const M&) = default;
    M(M&&)      = delete;                      // 이동은 지우고 복사만 남긴다
};

int main() {
    f(1);                                      // int 는 정확히 맞는다
    f(1.0f);                                   // float -> double 이 float -> int 보다 나은 변환이다
    M a;
    M b = a;                                   // 복사 — 된다
    M c = static_cast<M&&>(a);                 // 이동이 뽑힌 뒤 거부된다
    (void)b; (void)c;
}
```

- `f(1)` 과 `f(1.0f)` 중 **어느 쪽이 에러**인가 — 그리고 **`f(double) = delete;` 를 아예 안 썼다면** 어떻게 됐을까?
- ★★★ `M c = static_cast<M&&>(a);` 는 **복사 생성자가 있는데도** 왜 에러인가?
- ★ 두 컴파일러의 에러 **개수**는 몇인가?

### 5. ★★★ 0의 법칙이 얻는 것 (예측)

```cpp
/* rule05.cpp */
// 0의 법칙 — 자원을 unique_ptr·vector 에 맡기면 다섯을 하나도 안 쓴다
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <string>
#include <type_traits>
#include <utility>
#include <vector>

static int allocs = 0, frees = 0;
void* operator new(std::size_t n) { ++allocs; return std::malloc(n); }
void  operator delete(void* p)              noexcept { if (p) ++frees; std::free(p); }
void  operator delete(void* p, std::size_t) noexcept { if (p) ++frees; std::free(p); }

struct Five {                                    // 5의 법칙 — 손으로 다섯을 다 썼다
    char* p;
    explicit Five(std::size_t n) : p(new char[n]) {}
    ~Five() { delete[] p; }
    Five(const Five&)            = delete;
    Five& operator=(const Five&) = delete;
    Five(Five&& o) noexcept : p(o.p) { o.p = nullptr; }
    Five& operator=(Five&& o) noexcept { if (this != &o) { delete[] p; p = o.p; o.p = nullptr; } return *this; }
};

struct Zero {                                    // 0의 법칙 — 한 줄도 안 썼다
    std::unique_ptr<char[]> p;
    std::vector<int>        v;
    std::string             s;
    explicit Zero(std::size_t n) : p(new char[n]), v(n, 0), s(n, 'x') {}
};

int main() {
    std::printf("타입  | 복사생 복사대 이동생 이동대 | 이동이 noexcept 인가 | 손으로 쓴 특수 멤버\n");
    std::printf("Five  |   %d      %d      %d      %d   |         %d            |        5개\n",
        (int)std::is_copy_constructible_v<Five>, (int)std::is_copy_assignable_v<Five>,
        (int)std::is_move_constructible_v<Five>, (int)std::is_move_assignable_v<Five>,
        (int)std::is_nothrow_move_constructible_v<Five>);
    std::printf("Zero  |   %d      %d      %d      %d   |         %d            |        0개\n",
        (int)std::is_copy_constructible_v<Zero>, (int)std::is_copy_assignable_v<Zero>,
        (int)std::is_move_constructible_v<Zero>, (int)std::is_move_assignable_v<Zero>,
        (int)std::is_nothrow_move_constructible_v<Zero>);

    std::printf("(1) Zero 를 옮긴다 — 할당이 몇 번 더 나나\n");
    {
        allocs = frees = 0;
        Zero a(64);
        int after_ctor = allocs;
        Zero b = std::move(a);
        std::printf("    생성에서 %d회 · 이동에서 %d회\n", after_ctor, allocs - after_ctor);
    }
    std::printf("    블록을 나온 뒤 new %d회 · delete %d회\n", allocs, frees);
}
```

- `Five`(다섯을 손으로) 와 `Zero`(한 줄도 안 씀) 의 격자는 **어디가 다른가**?
- ★★★ `Zero` 를 옮길 때 **할당이 몇 번** 더 나나?
- ★★ 블록을 나온 뒤 `new` 횟수와 `delete` 횟수는 각각 몇인가?
- ★ 이 프로그램은 **런타임 할당을 무엇으로** 셌나 — 왜 그 방법을 썼나?

### 6. ★★ 경고를 누가 보나 (경계)

```cpp
/* rule06.cpp */
// 0/3/5 를 어긴 자리 여섯을 심었다 — 컴파일러가 몇 군데에서 말하는지 센다
#include <cstdio>
#include <cstdlib>
#include <utility>

struct R1 { char* p;                          // 1. 소멸자만 썼다 — 3의 법칙 위반
    R1() : p(static_cast<char*>(std::malloc(8))) {}
    ~R1() { std::free(p); } };
struct R2 { int a;                            // 2. 복사 생성자만 썼다
    R2() : a(0) {}
    R2(const R2& o) : a(o.a) {} };
struct R3 { int a;                            // 3. 이동 생성자만 썼다 — 복사가 지워진다
    R3() : a(0) {}
    R3(R3&& o) noexcept : a(o.a) {} };
struct R4 { char* p;                          // 4. 소멸자 + 복사는 막았는데 이동을 안 열었다
    R4() : p(static_cast<char*>(std::malloc(8))) {}
    ~R4() { std::free(p); }
    R4(const R4&) = delete;
    R4& operator=(const R4&) = delete; };
struct R5 { int a; ~R5(); };                  // 5. 클래스 밖 = default — trivial 이 아니게 된다
R5::~R5() = default;
struct R6 { int a;                            // 6. 복사 대입만 썼다
    R6() : a(0) {}
    R6& operator=(const R6& o) { a = o.a; return *this; } };

int main() {
    R1 a; R1 b(a);                            // 얕은 복사 — 소멸자 둘이 같은 포인터를 놓는다
    R2 c; R2 d(c); c = d;                     // 암묵 복사 대입을 쓴다
    R3 e; R3 f(std::move(e)); (void)f;
    R4 g; (void)g;
    R5 h; R5 i(h); (void)i;
    R6 j, k; j = k; R6 l(j); (void)l;
    std::printf("여섯 자리 전부 컴파일됐다\n");
    a.p = nullptr; b.p = nullptr;             // 이중 해제를 피해 치운다
}
```

- 탐침 **여섯 중 몇 개**에 두 컴파일러가 답하나 — 답한 것들은 **몇 번과 몇 번**인가?
- ★★★ 답한 둘의 **공통점**은 무엇인가 — 그리고 **안 답한 것들의 공통점**은?
- ★★ ASan 은 **몇 바이트**를 잡고, 그것이 **탐침 어느 자리**인가?

### 7. ★★ 종료 코드가 0인데 ill-formed (경계)

```cpp
/* rule07.cpp */
// 종료 코드가 0인데 표준이 금지한 것 둘 — 익명 구조체 멤버와 비-trivially-copyable 의 memcpy
#include <cstdio>
#include <cstring>
#include <string>
#include <type_traits>

struct Pair { struct { int a; int b; }; };      // ① ISO C++ 는 익명 구조체를 금지한다
struct NT   { std::string s; int x; };          // ② trivially copyable 이 아니다

int main() {
    Pair p; p.a = 1; p.b = 2;
    Pair q = p;                                 // 암묵 복사 생성자는 그래도 만들어진다
    std::printf("익명 구조체 멤버를 복사하면  q.a=%d q.b=%d\n", q.a, q.b);

    NT u{"가", 1}, v{"나", 2};
    std::printf("is_trivially_copyable<NT> = %d\n", (int)std::is_trivially_copyable_v<NT>);
    std::memcpy(&v, &u, sizeof(NT));            // ★ 표준이 금지한 것 — UB 다
    std::printf("memcpy 뒤 v.x = %d\n", v.x);
    new (&v) NT{"치운다", 0};                    // 소멸자가 같은 버퍼를 두 번 놓지 않도록 덮어쓴다
}
```

- 두 자리 각각에 g++ 와 clang 은 **경고를 내나 에러를 내나** — `cc exit` 는 몇인가?
- ★★★ `-pedantic` 이 아니라 **`-pedantic-errors`** 를 주면 **몇 건이 에러**가 되나?
- ★★★ 두 컴파일러가 **갈리는 자리**는 어느 쪽인가?
- ★ `is_trivially_copyable<NT>` 가 `0` 이라고 찍혀 있는데 `memcpy` 가 통과한다 — 그것이 왜 문제인가?

### 8. ★ 왜 「법칙」이라고 부르나 (왜)

- 「소멸자를 썼으면 나머지 넷도 결정하라」가 **취향이 아니라 규칙**인 근거는 어느 절의 어느 출력인가?
- ★★ **3의 법칙과 5의 법칙이 갈리는 지점**은 무엇이 달라져서 생겼나?

### 9. ★★ 이 주제의 사실이 다섯 층 중 어디에 있나 (경계)

- 「**소멸자를 선언하면 이동이 안 만들어진다**」는 **표준인가 구현 정의인가**?
- 「**클래스 밖 `= default` 는 trivial 이 아니다**」는 **표준인가**?
- ★★ 「**0/3/5 를 어기는 것**」 자체는 **UB 인가** — 아니라면 왜 경고가 거의 없나?
- ★ (5)의 `new 3회` 는 **보장인가 관찰인가**?

### 10. 다른 주제와 잇기 (연결)

- (2)의 `vector` 재할당이 갈리는 것은 몇 번 주제의 어느 절과 **같은 자리**인가?
- ★★ 이 주제를 **예고한 경고**는 몇 번 주제의 어느 절에서 나왔나?
- ★★ 「**자원을 둘 이상 들면 타입을 쪼갠다**」의 정본은 몇 번 주제의 어느 절인가?
- ★★★ **러스트는 기본값이 정반대다** — 어느 갈래 몇 번이고, 그 대가는 무엇인가?
- ★ **GC 가 있는 언어에 「소멸자를 쓰면 복사가 사라지는」 연쇄가 없는 이유**는 무엇인가 — 어느 갈래 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
