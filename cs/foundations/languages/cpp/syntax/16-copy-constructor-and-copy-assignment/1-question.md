# cpp/syntax/16 — 복사 생성자와 복사 대입 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **수로 답하는 것**이 절반이다 — 「복사된다」로 뭉개지 말고
> **어느 특수 멤버가 몇 번 불렸는지**를 숫자로 맞혀야 한다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 본체는 「호출 계수 로그」다**(1번·2번). 특수 멤버 다섯에 로그를 심고 전수로 센다.
> ★ **「부적용인 창」이 있다** — `-O2` 어셈블리 세기. 복사만 따로 재면 **비교 대상이 없어** 수가 뜻을 못 만든다.
> **「안 쟀다」가 아니라 「여기서는 잴 것이 없다」다** — 그 창은 [목록의 **17번 주제**](../17-move-constructor-assignment-and-moved-from-state/)가 복사판과 이동판을 나란히 놓고 쓴다.
> ★★ **「못 잰 것」은 또 다르다** — C++ 에는 **런타임 할당 계수기가 표준에 없다.**
> 그래서 3번은 **소스에 계수기를 손으로 심었고**, 7번은 **ASan 의 누수 리포트**로 바꿔 물었다.
> 선행 — [15번](../15-raii-resources-as-types/) (4)의 「복사를 안 막은 래퍼」가 이 주제의 출발점이다. 거기는 막는 쪽, 여기는 **제대로 만드는 쪽**이다.
> 대비 — Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **9번**([`09-copy-clone-and-drop/`](../../../rust/syntax/09-copy-clone-and-drop/))이 **기본값이 정반대인 판**이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 열 가지 문맥에 무엇이 불리나 (예측)

```cpp
/* copy01.cpp */
// 특수 멤버 다섯에 전부 로그를 심고 — 어느 상황이 무엇을 부르나 전수로 센다
#include <cstdio>
#include <utility>

struct Loud {
    int id;
    static int n;
    Loud()                      : id(++n) { std::printf("    기본 생성자  #%d\n", id); }
    Loud(const Loud& o)         : id(++n) { std::printf("    복사 생성자  #%d <- #%d\n", id, o.id); }
    Loud(Loud&& o)     noexcept : id(++n) { std::printf("    이동 생성자  #%d <- #%d\n", id, o.id); }
    Loud& operator=(const Loud& o)         { std::printf("    복사 대입    #%d <- #%d\n", id, o.id); return *this; }
    Loud& operator=(Loud&& o)     noexcept { std::printf("    이동 대입    #%d <- #%d\n", id, o.id); return *this; }
    ~Loud() {}
};
int Loud::n = 0;

void by_value(Loud x)        { (void)x; }
void by_const_ref(const Loud& x) { (void)x; }

int main() {
    Loud a, b;                                   // #1 #2
    std::printf("(1) Loud c = b;        — 선언과 함께 = 을 썼다\n");   { Loud c = b;            (void)c; }
    std::printf("(2) Loud c(b);         — 괄호로 썼다\n");             { Loud c(b);             (void)c; }
    std::printf("(3) Loud c{b};         — 중괄호로 썼다\n");           { Loud c{b};             (void)c; }
    std::printf("(4) a = b;             — 이미 있는 것에 = 을 썼다\n"); a = b;
    std::printf("(5) Loud c = std::move(b);\n");                       { Loud c = std::move(b); (void)c; }
    std::printf("(6) a = std::move(b);\n");                            a = std::move(b);
    std::printf("(7) by_value(b);       — 값으로 받는 함수에 넘긴다\n"); by_value(b);
    std::printf("(8) by_const_ref(b);   — const 참조로 받는 함수에\n"); by_const_ref(b);
    std::printf("(9) by_value(std::move(b));\n");                      by_value(std::move(b));
    std::printf("(10) 지금까지 만들어진 객체 수 %d개\n", Loud::n);
}
```

- `(1)`\~`(3)` 에서 불리는 것은 **복사 생성자인가 복사 대입인가** — 셋이 같은가 다른가?
- ★★★ `(4)` 는 `(1)` 과 **같은 `=` 를 썼는데** 왜 다른 것이 불리나?
- ★★ `(7)` 과 `(8)` 중 **아무 로그도 안 찍히는 쪽**은 어느 것인가?
- ★ 마지막 줄의 **만들어진 객체 수**는 몇인가?

### 2. ★★ 생략을 끄면 총계가 얼마나 바뀌나 (예측)

```cpp
/* copy02.cpp */
// 생략(copy elision)이 계수를 바꾸는 자리 — 의무인 것과 선택인 것을 가른다
#include <cstdio>

struct L {
    int id;
    static int n;
    L()                   : id(++n) { std::printf("    기본 생성자  #%d\n", id); }
    L(const L& o)         : id(++n) { std::printf("    복사 생성자  #%d <- #%d\n", id, o.id); }
    L(L&& o)     noexcept : id(++n) { std::printf("    이동 생성자  #%d <- #%d\n", id, o.id); }
    ~L() {}
};
int L::n = 0;

L prvalue()          { return L(); }        // 이름 없는 임시를 돌려준다
L named()            { L t; return t; }     // 이름 있는 지역을 돌려준다
void by_value(L x)   { (void)x; }

int main() {
    std::printf("(1) prvalue 를 받는다      L a = prvalue();\n");   { L a = prvalue(); (void)a; }
    std::printf("(2) 이름 있는 지역을 받는다 L b = named();\n");     { L b = named();   (void)b; }
    std::printf("(3) 임시를 값 인자로        by_value(L());\n");     by_value(L());
    std::printf("(4) 변수를 값 인자로        by_value(c);\n");       { L c; by_value(c); }
    std::printf("(5) 만들어진 객체 수 %d개\n", L::n);
}
```

- 기본 명령으로 돌리면 `(1)`\~`(4)` 각각에 **몇 줄**이 찍히고 **총계**는 몇인가?
- ★★★ `-fno-elide-constructors` 를 붙이면 **어느 줄이 늘어나나** — 그리고 **안 늘어나는 자리는 왜 안 늘어나나**?
- ★ 늘어난 그 줄은 **복사 생성자인가 이동 생성자인가**?

### 3. ★★ 깊은 복사 뒤에 무엇을 확인해야 하나 (예측)

```cpp
/* copy03.cpp */
// 14·15편이 실측한 「얕은 복사 -> 이중 해제」를 고치는 쪽 — 깊은 복사를 손으로 쓴다
#include <cstdio>
#include <cstdlib>
#include <cstring>

static int allocs = 0, frees = 0;

struct Buf {
    char*       p;
    std::size_t n;

    explicit Buf(const char* s) : p(nullptr), n(std::strlen(s) + 1) {
        p = static_cast<char*>(std::malloc(n)); ++allocs;
        std::memcpy(p, s, n);
    }
    ~Buf() { std::free(p); ++frees; }

    Buf(const Buf& o) : p(static_cast<char*>(std::malloc(o.n))), n(o.n) {   // 깊은 복사 — 생성
        ++allocs;
        std::memcpy(p, o.p, n);
    }
    Buf& operator=(const Buf& o) {                                          // 깊은 복사 — 대입
        if (this == &o) return *this;                                       // 자기 대입을 먼저 막는다
        char* q = static_cast<char*>(std::malloc(o.n)); ++allocs;           // 새것을 먼저 얻고
        std::memcpy(q, o.p, o.n);
        std::free(p); ++frees;                                              // 그다음에 옛것을 놓는다
        p = q; n = o.n;
        return *this;
    }
};

int main() {
    Buf a("가나다");
    Buf b = a;                                   // 복사 생성
    std::printf("(1) 복사 생성 뒤\n");
    std::printf("    두 객체가 같은 주소를 드나: %d\n", (int)(a.p == b.p));
    std::printf("    두 객체의 내용이 같나      : %d\n", (int)(std::strcmp(a.p, b.p) == 0));
    std::memcpy(b.p, "라마바", 10);
    std::printf("(2) b 만 고친 뒤\n");
    std::printf("    a = \"%s\"  b = \"%s\"\n", a.p, b.p);
    Buf c("짧다");
    c = a;                                       // 복사 대입
    std::printf("(3) 복사 대입 뒤  c = \"%s\"  (a 와 같은 주소인가: %d)\n", c.p, (int)(c.p == a.p));
    std::printf("(4) 지금까지 malloc %d회 · free %d회 (블록을 나가면 free 가 3회 더)\n", allocs, frees);
}
```

- `(1)` 의 두 줄은 각각 **0 인가 1 인가**?
- ★★ `(3)` 에서 `c.p == a.p` 는 **0 인가 1 인가**?
- ★ `(4)` 의 `malloc` 횟수와 `free` 횟수는 각각 몇인가?

### 4. ★★★ 자기 자신을 대입하면 (예측)

```cpp
/* copy04.cpp */
// 자기 대입을 안 막은 naive 구현 — 마커를 표준 오류로 찍는다(ASan 이 죽여도 남게)
// ★ 상한 내용은 판마다 다르므로 값 자체를 찍지 않는다. 「상했나」만 묻는다.
#include <cstdio>
#include <cstdlib>
#include <cstring>

struct Naive {
    char*       p;
    std::size_t n;
    explicit Naive(const char* s) : p(nullptr), n(std::strlen(s) + 1) {
        p = static_cast<char*>(std::malloc(n));
        std::memcpy(p, s, n);
    }
    ~Naive() { std::free(p); }
    Naive(const Naive& o) : p(static_cast<char*>(std::malloc(o.n))), n(o.n) { std::memcpy(p, o.p, n); }
    Naive& operator=(const Naive& o) {          // 놓고 나서 잡는다 — 자기 대입을 안 막았다
        std::free(p);                           // ① 내 것을 먼저 놓는다
        n = std::strlen(o.p) + 1;               // ② 그런데 o 가 나 자신이면 방금 놓은 것을 읽는다
        p = static_cast<char*>(std::malloc(n));
        std::memcpy(p, o.p, n);
        return *this;
    }
};

int main() {
    std::fprintf(stderr, "(1) 서로 다른 둘을 대입한다  a = b;\n");
    Naive a("가나다"), b("라마바");
    a = b;
    std::fprintf(stderr, "    a 가 \"라마바\" 인가: %d\n", (int)(std::strcmp(a.p, "라마바") == 0));
    std::fprintf(stderr, "(2) 자기 자신을 대입한다  a = a;\n");
    a = a;
    std::fprintf(stderr, "    a 가 아직 \"라마바\" 인가: %d\n", (int)(std::strcmp(a.p, "라마바") == 0));
}
```

- `(2)` 의 마지막 줄은 **0 인가 1 인가**?
- ★★★ 이 프로그램은 **터지나 안 터지나** — `run exit` 는 몇인가? 경고는 몇 건인가?
- ★★ 같은 소스를 `-fsanitize=address` 로 돌리면 **사고 이름**이 무엇으로 붙고, **어느 줄 세 개**를 가리키나?
- ★ 이 소스가 마커를 `stderr` 로 찍은 이유는?

### 5. ★★★ copy-and-swap 에 자기 대입과 예외를 함께 던지면 (예측)

```cpp
/* copy05.cpp */
// copy-and-swap — 자기 대입과 예외 안전을 한 구현이 동시에 푼다
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <new>
#include <utility>

static bool armed = false;                       // 다음 할당을 실패시킨다
static void* xalloc(std::size_t n) {
    if (armed) { armed = false; throw std::bad_alloc(); }
    return std::malloc(n);
}

struct Safe {
    char*       p;
    std::size_t n;
    explicit Safe(const char* s) : p(nullptr), n(std::strlen(s) + 1) {
        p = static_cast<char*>(xalloc(n));
        std::memcpy(p, s, n);
    }
    ~Safe() { std::free(p); }
    Safe(const Safe& o) : p(static_cast<char*>(xalloc(o.n))), n(o.n) { std::memcpy(p, o.p, n); }
    friend void swap(Safe& x, Safe& y) noexcept { std::swap(x.p, y.p); std::swap(x.n, y.n); }
    Safe& operator=(Safe o) {                    // ★ 값으로 받는다 — 복사는 여기서 이미 끝났다
        swap(*this, o);                          // ★ 맞바꾸기만 한다 (noexcept)
        return *this;                            // ★ o 가 옛것을 들고 나가 파괴된다
    }
};

struct Naive {                                   // 대조군 — 놓고 나서 잡는다
    char*       p;
    std::size_t n;
    explicit Naive(const char* s) : p(nullptr), n(std::strlen(s) + 1) {
        p = static_cast<char*>(xalloc(n));
        std::memcpy(p, s, n);
    }
    ~Naive() { std::free(p); }
    Naive(const Naive& o) : p(static_cast<char*>(xalloc(o.n))), n(o.n) { std::memcpy(p, o.p, n); }
    Naive& operator=(const Naive& o) {
        if (this == &o) return *this;
        std::free(p);                            // ① 먼저 놓고
        p = static_cast<char*>(xalloc(o.n));     // ② 여기서 던지면 p 는 해제된 주소 그대로다
        n = o.n;
        std::memcpy(p, o.p, n);
        return *this;
    }
};

int main() {
    std::printf("(1) copy-and-swap 에 자기 대입\n");
    Safe a("가나다");
    a = a;
    std::printf("    a = \"%s\"   (자기 대입 검사 한 줄도 없다)\n", a.p);

    std::printf("(2) 대입 도중 할당이 실패하면 — copy-and-swap\n");
    Safe s1("원본은 살아남나"), s2("새 값");
    armed = true;
    try { s1 = s2; } catch (const std::bad_alloc&) { std::printf("    [catch] bad_alloc\n"); }
    std::printf("    s1 = \"%s\"  ★ 원본 그대로다\n", s1.p);

    std::printf("(3) 같은 일을 naive 구현에 — 포인터가 어떻게 되나\n");
    Naive n1("원본은 살아남나"), n2("새 값");
    char* before = n1.p;
    armed = true;
    try { n1 = n2; } catch (const std::bad_alloc&) { std::printf("    [catch] bad_alloc\n"); }
    std::printf("    n1.p 가 대입 전과 같은 주소인가: %d  ★ 그 주소는 이미 free 된 것이다\n",
                (int)(n1.p == before));
    n1.p = nullptr;                              // 소멸자가 이중 해제하지 않도록 치운다
}
```

- `(1)` — 자기 대입 검사가 **한 줄도 없는데** `a` 가 온전한가?
- ★★★ `(2)` 에서 대입 도중 `bad_alloc` 이 나면 `s1` 은 **무엇이 되나**?
- ★★★ `(3)` 의 마지막 줄은 **0 인가 1 인가** — 그것이 왜 사고인가?
- ★ copy-and-swap 이 **공짜가 아닌 자리**는 어디인가?

### 6. ★ 복사 생성자를 값으로 받으면 (예측)

```cpp
/* copy06.cpp */
// 복사 생성자를 const T& 가 아니라 T 로 받으면 — 컴파일러가 먼저 막는다
struct C {
    int x;
    C() : x(0) {}
    C(C o) { x = o.x; }                 // 값으로 받는 복사 생성자
};
struct A {
    int x;
    A() : x(0) {}
    A(const A&) = default;
    A& operator=(A o) { x = o.x; return *this; }   // 값으로 받는 복사 대입은 합법이다
};
int main() { A a, b; a = b; (void)a; }
```

- 이 파일은 **컴파일되나** — 된다면 `C c1; C c2 = c1;` 에서 무엇이 일어나나?
- ★★ 같은 파일의 `A& operator=(A o)` 는 **왜 막히지 않나**?

### 7. ★★ 경고를 누가 보나 (경계)

```cpp
/* copy07.cpp */
// 복사에서 틀리는 자리 여섯을 심었다 — 컴파일러가 몇 군데에서 말하는지 센다
#include <cstdio>
#include <cstdlib>
#include <cstring>

struct P1 {                                   // 1. 소멸자만 쓰고 복사를 안 막았다 (얕은 복사)
    char* p;
    P1() : p(static_cast<char*>(std::malloc(8))) {}
    ~P1() { std::free(p); }
};
struct P2 {                                   // 2. 복사 생성자만 쓰고 복사 대입은 안 썼다
    char* p;
    P2() : p(static_cast<char*>(std::malloc(8))) {}
    P2(const P2& o) : p(static_cast<char*>(std::malloc(8))) { (void)o; }
};
struct P3 {                                   // 3. 복사 생성자가 멤버 하나를 빠뜨렸다
    int a, b;
    P3() : a(0), b(0) {}
    P3(const P3& o) : a(o.a) {}
};
struct P4 {                                   // 4. 복사 대입이 *this 를 안 돌려준다
    int a;
    P4() : a(0) {}
    void operator=(const P4& o) { a = o.a; }
};
struct P5 {                                   // 5. 자기 대입을 안 막은 대입 연산자
    char* p; std::size_t n;
    P5() : p(static_cast<char*>(std::malloc(8))), n(8) {}
    ~P5() { std::free(p); }
    P5(const P5& o) : p(static_cast<char*>(std::malloc(o.n))), n(o.n) { std::memcpy(p, o.p, n); }
    P5& operator=(const P5& o) {
        std::free(p);
        n = o.n;
        p = static_cast<char*>(std::malloc(n));
        std::memcpy(p, o.p, n);
        return *this;
    }
};
struct P6 {                                   // 6. 복사 대입이 멤버를 하나도 안 옮긴다
    int a;
    P6() : a(0) {}
    P6& operator=(const P6&) { return *this; }
};

int main() {
    P1 a; P1 b(a); (void)b;                   // 얕은 복사 — 소멸자 둘이 같은 포인터를 놓는다
    P2 c; P2 d(c); c = d;                     // 암묵 복사 대입을 쓴다
    P3 e; P3 f(e); (void)f;
    P4 g, h; g = h;
    P5 i, j; i = j;
    P6 k, l; k = l;
    std::printf("여섯 자리 전부 컴파일됐다\n");
    a.p = nullptr; b.p = nullptr;             // 이중 해제를 피해 치운다
}
```

- 탐침 **여섯 중 몇 개**에 두 컴파일러가 답하나 — 그리고 **답한 그 하나**는 몇 번인가?
- ★★ 같은 파일을 ASan 으로 돌리면 **몇 바이트**가 잡히고, 그것이 **탐침 어느 자리의 사고**인가?
- ★★★ 탐침 5번(자기 대입)은 **왜 이 파일에서는 ASan 도 침묵**하나?

### 8. ★ `T a = b;` 와 `a = b;` 가 다른 이유 (왜)

- 두 줄의 `=` 가 **같은 기호인데 다른 함수**를 부른다 — 그 경계는 무엇으로 갈리나?
- ★ 그래서 **복사 생성자에 계수기를 심어 「복사 횟수」를 세는 코드**가 틀리는 자리는 어디인가?

### 9. ★★ 이 주제의 사실이 다섯 층 중 어디에 있나 (경계)

- 「**`prvalue` 를 돌려받는 자리에 복사 생성자가 안 불린다**」는 **표준인가 미명시인가** — 어느 버전부터인가?
- 「**`named()` 를 돌려받는 자리에 아무것도 안 불린다**」는 **표준인가 미명시인가**?
- ★★ 「**자기 대입 뒤에 값이 상한다**」는 **보장인가 관찰인가**?

### 10. 다른 주제와 잇기 (연결)

- **얕은 복사가 이중 해제를 만드는 것**을 실측한 것은 몇 번 주제의 어느 절인가?
- 「**복사 생성자를 썼으면 복사 대입도 결정하라**」의 정본은 몇 번 주제인가?
- ★★ `(2)` 의 「`return t;` 의 `t` 가 먼저 rvalue 로 취급된다」의 정본은 몇 번인가?
- ★★ **러스트는 복사가 기본이 아니다** — 어느 갈래 몇 번이고, C++ 과 **기본값이 어떻게 반대**인가?
- ★ **값 타입이냐 참조 타입이냐가 복사의 뜻을 정하는 언어**는 어느 갈래 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
