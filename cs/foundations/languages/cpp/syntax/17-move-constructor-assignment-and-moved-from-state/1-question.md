# cpp/syntax/17 — 이동 생성자·이동 대입·이동 후 상태 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **수로 답하는 것**이 절반이다 — 「옮겨진다」로 뭉개지 말고
> **`malloc` 이 몇 번 났는지**, **이동 로그인지 복사 로그인지**를 맞혀야 한다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · rustc 1.92.0 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 본체는 「계수 로그 + 할당 횟수 계수기」다**(2번·3번).
> ★★ **네 번째 창은 「어셈블리 세기」다**(7번) — [16번](../16-copy-constructor-and-copy-assignment/)에서 부적용이던 창이 **여기서 성립한다.**
> 같은 타입의 **복사판과 이동판을 한 파일에 넣어야** 수가 근거가 되기 때문이다.
> ★★★ **「제5의 상태」가 4번에 있다** — 「이동 후 원본이 무엇이 되나」는 **관찰로 답이 안 난다.**
> 세 창이 전부 정상인데 틀린 것은 값이 아니라 「**그 값이 보장인가**」다.
> ★★★ **이 편은 도구가 가장 조용하다** — 9번의 탐침 여섯이 **전부 0건**이고 **ASan 도 0건**이다.
> 선행 — [16번](../16-copy-constructor-and-copy-assignment/) (1)의 전수 격자와 (2)의 생략 실측이 이 주제의 토대다.
> 대비 — ★★★ Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **8번**([`08-ownership-and-move/`](../../../rust/syntax/08-ownership-and-move/))이 **직접 대비**다(8번 문항).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ `std::move(a);` 만 적으면 (예측)

```cpp
/* move01.cpp */
// std::move 는 아무것도 옮기지 않는다 — 캐스트일 뿐임을 로그와 타입으로 보인다
#include <cstdio>
#include <type_traits>
#include <utility>

struct L {
    int id;
    static int n;
    L()                   : id(++n) { std::printf("    기본 생성자  #%d\n", id); }
    L(const L& o)         : id(++n) { std::printf("    복사 생성자  #%d <- #%d\n", id, o.id); }
    L(L&& o)     noexcept : id(++n) { std::printf("    이동 생성자  #%d <- #%d\n", id, o.id); }
    ~L() {}
};
int L::n = 0;

int main() {
    L a;
    std::printf("(1) std::move(a); 만 적는다 — 아래에 로그가 몇 줄 찍히나\n");
    (void)std::move(a);
    std::printf("(2) 그 결과를 초기화에 쓴다  L b = std::move(a);\n");
    L b = std::move(a);
    std::printf("(3) std::move(a) 의 타입은 무엇인가\n");
    std::printf("    decltype(std::move(a)) 가 L&&      인가: %d\n",
                (int)std::is_same_v<decltype(std::move(a)), L&&>);
    L&& r = std::move(a);                      // 이름을 붙여 주소를 물어본다
    std::printf("    &a 와 &r 이 같은 주소인가          : %d\n", (int)(&a == &r));
    std::printf("(4) 만들어진 객체 수 %d개 — (1)에서는 하나도 안 늘었다\n", L::n);
    (void)b;
}
```

- `(1)` 아래에 로그가 **몇 줄** 찍히나?
- ★★ `decltype(std::move(a))` 는 무엇이고 `&a == &r` 은 **0 인가 1 인가**?
- ★ 마지막 줄의 **만들어진 객체 수**는 몇인가?

### 2. ★★★ 복사판과 이동판의 `malloc` 횟수 (예측)

```cpp
/* move02.cpp */
// 「훔쳤다」를 무엇으로 보이나 — 원본 포인터가 널이 된 것 + 할당 횟수 계수기
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <utility>

static int allocs = 0, frees = 0;

struct Box {
    char*       p;
    std::size_t n;
    explicit Box(const char* s) : p(nullptr), n(std::strlen(s) + 1) {
        p = static_cast<char*>(std::malloc(n)); ++allocs;
        std::memcpy(p, s, n);
    }
    ~Box() { if (p) { std::free(p); ++frees; } }

    Box(const Box& o) : p(static_cast<char*>(std::malloc(o.n))), n(o.n) {   // 복사 — 새로 잡는다
        ++allocs;
        std::memcpy(p, o.p, n);
    }
    Box& operator=(const Box& o) {
        if (this == &o) return *this;
        char* q = static_cast<char*>(std::malloc(o.n)); ++allocs;
        std::memcpy(q, o.p, o.n);
        if (p) { std::free(p); ++frees; }
        p = q; n = o.n;
        return *this;
    }
    Box(Box&& o) noexcept : p(o.p), n(o.n) {                                // 이동 — 훔친다
        o.p = nullptr; o.n = 0;                                             // ★ 원본을 빈 껍데기로
    }
    Box& operator=(Box&& o) noexcept {
        if (this != &o) {
            if (p) { std::free(p); ++frees; }
            p = o.p; n = o.n;
            o.p = nullptr; o.n = 0;
        }
        return *this;
    }
};

int main() {
    std::printf("(1) 복사판\n");
    {
        allocs = frees = 0;
        Box a("훔칠 것이 여기 있다");
        Box b = a;
        std::printf("    a.p 가 널인가 %d · b.p 가 널인가 %d · 같은 주소인가 %d\n",
                    (int)(a.p == nullptr), (int)(b.p == nullptr), (int)(a.p == b.p));
        std::printf("    malloc %d회\n", allocs);
    }
    std::printf("    블록을 나온 뒤 free %d회\n", frees);

    std::printf("(2) 이동판\n");
    {
        allocs = frees = 0;
        Box a("훔칠 것이 여기 있다");
        char* before = a.p;
        Box b = std::move(a);
        std::printf("    a.p 가 널인가 %d · b.p 가 원래 주소 그대로인가 %d\n",
                    (int)(a.p == nullptr), (int)(b.p == before));
        std::printf("    malloc %d회\n", allocs);
    }
    std::printf("    블록을 나온 뒤 free %d회  ★ 원본의 소멸자는 돌았지만 놓을 것이 없었다\n", frees);
}
```

- `(1)` 과 `(2)` 의 **`malloc` 횟수**는 각각 몇인가?
- ★★★ `(2)` 의 `a.p 가 널인가` 와 `b.p 가 원래 주소 그대로인가` 는 각각 **0 인가 1 인가**?
- ★★★ `(2)` 에서 블록을 나온 뒤 **`free` 는 몇 회**인가 — 그리고 `a` 의 소멸자는 **돌았나 안 돌았나**?

### 3. ★★★ `noexcept` 한 낱말을 빼면 (예측)

```cpp
/* move03.cpp */
// noexcept 한 낱말이 vector 재할당에서 이동과 복사를 가른다
#include <cstdio>
#include <type_traits>
#include <vector>

struct Yes {                                     // 이동 생성자에 noexcept 가 있다
    int id; static int n;
    Yes()                     : id(++n) { std::printf("      기본 #%d\n", id); }
    Yes(const Yes& o)         : id(++n) { std::printf("      복사 #%d <- #%d\n", id, o.id); }
    Yes(Yes&& o)     noexcept : id(++n) { std::printf("      이동 #%d <- #%d\n", id, o.id); }
    ~Yes() {}
};
struct No {                                      // 한 낱말만 뺐다
    int id; static int n;
    No()                   : id(++n) { std::printf("      기본 #%d\n", id); }
    No(const No& o)        : id(++n) { std::printf("      복사 #%d <- #%d\n", id, o.id); }
    No(No&& o)             : id(++n) { std::printf("      이동 #%d <- #%d\n", id, o.id); }
    ~No() {}
};
int Yes::n = 0; int No::n = 0;

template <class T>
void grow(const char* tag) {
    std::printf("  [%s] is_nothrow_move_constructible = %d\n",
                tag, (int)std::is_nothrow_move_constructible_v<T>);
    std::vector<T> v;
    v.reserve(2);
    std::printf("    자리 둘을 잡아 두고 둘을 넣는다 (capacity=%zu)\n", v.capacity());
    v.emplace_back();
    v.emplace_back();
    std::printf("    ★ 세 번째를 넣어 재할당을 일으킨다 — 있던 둘이 무엇으로 옮겨지나\n");
    v.emplace_back();
    std::printf("    capacity %zu · size %zu\n", v.capacity(), v.size());
}

int main() {
    std::printf("(1) noexcept 가 있는 타입\n"); grow<Yes>("Yes");
    std::printf("(2) noexcept 가 없는 타입\n"); grow<No>("No");
}
```

- 두 타입의 소스 차이는 **무엇 하나**인가?
- ★★★ 세 번째 원소를 넣어 재할당이 일어날 때, 있던 둘이 **무엇으로 옮겨지나** — 두 타입에서 각각?
- ★★ `capacity` 는 두 타입에서 **같게 움직이나 다르게 움직이나**?
- ★ `vector` 는 **무엇을 보고** 그것을 고르나?

### 4. ★★★ 이동당한 원본은 무엇이 되나 (예측)

```cpp
/* move04.cpp */
// 이동 후 상태 — 표준이 보장하는 것과 이 구현이 실제로 두는 것을 갈라 찍는다
#include <cstdio>
#include <memory>
#include <string>
#include <utility>
#include <vector>

int main() {
    std::printf("(1) 표준이 「널」이라고 못 박은 것 — unique_ptr\n");
    std::unique_ptr<int> u1(new int(7));
    std::unique_ptr<int> u2 = std::move(u1);
    std::printf("    u1.get() == nullptr : %d   (표준 보장)\n", (int)(u1.get() == nullptr));
    std::printf("    *u2                 : %d\n", *u2);

    std::printf("(2) 표준이 「유효하되 미지정」이라고만 한 것 — 이 구현이 무엇으로 두나\n");
    std::string s1 = "짧다";
    std::string t1 = std::move(s1);
    std::printf("    짧은 string : size=%zu  empty=%d  capacity=%zu  값=\"%s\"\n",
                s1.size(), (int)s1.empty(), s1.capacity(), s1.c_str());
    std::string s2(64, 'x');
    std::string t2 = std::move(s2);
    std::printf("    긴 string   : size=%zu  empty=%d  capacity=%zu\n",
                s2.size(), (int)s2.empty(), s2.capacity());
    std::vector<int> v1{1, 2, 3};
    std::vector<int> v2 = std::move(v1);
    std::printf("    vector      : size=%zu  capacity=%zu\n", v1.size(), v1.capacity());

    std::printf("(3) 이동당한 원본에 무엇을 해도 되나 — 표준이 허락한 것만\n");
    s1 = "다시 넣는다";                          // 대입은 상태를 안 봐도 된다
    v1.clear();                                  // clear 는 전제조건이 없다
    std::printf("    다시 대입한 뒤 s1 = \"%s\"  ·  clear 뒤 v1.size()=%zu\n", s1.c_str(), v1.size());
    std::printf("    t1=\"%s\" t2.size()=%zu v2.size()=%zu\n", t1.c_str(), t2.size(), v2.size());
}
```

- `(1)` 의 `u1.get() == nullptr` 은 **0 인가 1 인가** — 그리고 그것은 **보장인가 관찰인가**?
- ★★★ `(2)` 의 세 줄에 찍히는 숫자들은 **보장인가 관찰인가**?
- ★★ 짧은 `string` 과 긴 `string` 의 이동 후 `capacity` 가 **같은가 다른가** — 왜 그런가?
- ★ `(3)` 에서 **이동당한 원본에 해도 되는 것 둘**은 무엇인가?

### 5. ★★ 이동이 복사로 되돌아가는 자리 (예측)

```cpp
/* move05.cpp */
// 이동이 복사로 조용히 되돌아가는 자리 셋 — 계수 로그로 증명한다
#include <cstdio>
#include <utility>

struct Tr {                                        // 멤버 — 무엇이 불렸는지 말한다
    Tr() {}
    Tr(const Tr&)          { std::printf("      멤버: 복사\n"); }
    Tr(Tr&&)      noexcept { std::printf("      멤버: 이동\n"); }
    ~Tr() {}
};
struct CopyOnly {                                  // 이동이 없는 멤버
    CopyOnly() {}
    CopyOnly(const CopyOnly&) { std::printf("      멤버: 복사(이동 생성자가 없는 타입)\n"); }
    ~CopyOnly() {}
};

struct Good { Tr t; };                             // 멤버가 이동을 갖췄다
struct Half { Tr t; CopyOnly c; };                 // 멤버 하나가 복사만 된다

int main() {
    std::printf("(1) 멤버가 전부 이동 가능하면\n");
    { Good a; Good b = std::move(a); (void)b; }

    std::printf("(2) 멤버 하나가 복사만 되면 — 그 멤버만 복사되나, 전부 복사되나\n");
    { Half a; Half b = std::move(a); (void)b; }

    std::printf("(3) const 를 move 하면\n");
    { const Tr c; Tr d = std::move(c); (void)d; }

    std::printf("(4) const 를 안 붙이면\n");
    { Tr c; Tr d = std::move(c); (void)d; }
}
```

- `(2)` 에서 멤버 둘은 각각 **이동되나 복사되나** — 「전부 복사」인가 「멤버별로 갈리나」?
- ★★★ `(3)` 과 `(4)` 는 소스가 **한 낱말만** 다르다. 로그는 어떻게 갈리나?
- ★ `(3)` 에서 컴파일러는 **경고를 내나**?

### 6. ★ `return std::move(t);` 를 쓰면 (예측)

```cpp
/* move06.cpp */
// 반환값에 std::move 를 쓰면 — 생략이 막혀 생성자가 한 번 더 돈다
#include <cstdio>
#include <utility>

struct L {
    int id;
    static int n;
    L()                   : id(++n) { std::printf("    기본 생성자  #%d\n", id); }
    L(const L& o)         : id(++n) { std::printf("    복사 생성자  #%d <- #%d\n", id, o.id); }
    L(L&& o)     noexcept : id(++n) { std::printf("    이동 생성자  #%d <- #%d\n", id, o.id); }
    ~L() { std::printf("    소멸자        #%d\n", id); }
};
int L::n = 0;

L plain()  { L t; return t; }                  // 그냥 돌려준다
L moved()  { L t; return std::move(t); }       // std::move 를 붙여 돌려준다

int main() {
    std::printf("(1) return t;\n");            { L a = plain(); (void)a; }
    std::printf("(2) return std::move(t);\n"); { L b = moved(); (void)b; }
    std::printf("(3) 만들어진 객체 수 %d개\n", L::n);
}
```

- `(1)` 과 `(2)` 는 각각 **몇 줄**의 로그를 내나?
- ★★ 늘어난 줄은 무엇이고 **왜 늘어나나**?
- ★ 이 자리에 컴파일러가 **경고를 내나** — 낸다면 이름이 무엇인가?

### 7. ★★ 복사판과 이동판을 `-O2` 로 세면 (경계)

```cpp
/* move08.cpp */
// 복사판과 이동판이 각각 몇 개의 명령으로 컴파일되나 — 개수만 센다(시간은 안 잰다)
#include <cstdlib>
#include <cstring>

struct Box {
    char*         p;
    unsigned long n;
    Box(const Box& o) : p(static_cast<char*>(std::malloc(o.n))), n(o.n) { std::memcpy(p, o.p, n); }
    Box(Box&& o) noexcept : p(o.p), n(o.n) { o.p = nullptr; o.n = 0; }
    ~Box() { std::free(p); }
};

Box make_copy(const Box& a) { return Box(a); }
Box make_move(Box& a)       { return Box(static_cast<Box&&>(a)); }
```

- 두 함수의 **`call` 개수**는 각각 몇인가 — 그리고 그 `call` 은 **무엇을 부르는 것**인가?
- ★★ **명령 개수**는 근거로 쓸 수 있나, 못 쓴다면 왜인가?
- ★★★ 이 절에서 **재지 않은 것**은 무엇인가?

### 8. ★★★ 러스트에 같은 코드를 던지면 (경계)

```rust
// movers.rs
// 러스트는 이동이 기본이고, 이동 후 원본을 컴파일러가 막는다
fn main() {
    let a = String::from("훔칠 것이 여기 있다");
    let b = a;                      // 이동 — clone 이 아니다
    println!("b = {}", b);
    println!("a = {}", a);          // 이동당한 원본을 다시 읽는다
}
```

```cpp
/* move09.cpp */
// 러스트와 같은 코드를 C++ 로 — 이동당한 원본을 다시 읽는다
#include <cstdio>
#include <string>
#include <utility>

int main() {
    std::string a = "훔칠 것이 여기 있다";
    std::string b = std::move(a);          // 이동
    std::printf("b = %s\n", b.c_str());
    std::printf("a = \"%s\"  (size=%zu)\n", a.c_str(), a.size());   // 이동당한 원본을 다시 읽는다
}
```

- 두 프로그램은 각각 **컴파일되나** — 안 되는 쪽의 **에러 코드**는 무엇인가?
- ★★★ C++ 쪽의 `a` 를 다시 읽는 것은 **UB 인가 아닌가** — 그래서 sanitizer 가 무엇이라고 하나?
- ★★ C++ 쪽에 찍힌 빈 문자열은 **보장인가 관찰인가**?
- ★ 러스트가 치르는 **대가**는 무엇인가?

### 9. ★★ 경고를 누가 보나 (경계)

```cpp
/* move07.cpp */
// 이동에서 틀리는 자리 여섯을 심었다 — 컴파일러가 몇 군데에서 말하는지 센다
#include <cstdio>
#include <string>
#include <utility>
#include <vector>

struct Q1 {                                   // 1. 이동 생성자에 noexcept 를 안 붙였다
    std::string s;
    Q1() {}
    Q1(const Q1& o) : s(o.s) {}
    Q1(Q1&& o) : s(std::move(o.s)) {}
};
struct Q2 {                                   // 2. 이동 생성자가 원본을 비우지 않는다
    int* p;
    Q2() : p(new int(1)) {}
    ~Q2() { delete p; }
    Q2(const Q2& o) : p(new int(*o.p)) {}
    Q2(Q2&& o) noexcept : p(o.p) {}           // o.p 를 널로 안 만들었다 — 이중 해제가 열린다
};

void use_after_move() {                       // 3. 이동한 뒤 원본을 다시 읽는다
    std::string a = "무엇이 남나";
    std::string b = std::move(a);
    std::printf("    이동 뒤 a.size()=%zu b.size()=%zu\n", a.size(), b.size());
}
void move_a_const() {                         // 4. const 객체에 std::move 를 쓴다
    const std::string a = "복사로 되돌아간다";
    std::string b = std::move(a);
    (void)b;
}
void move_into_const_ref() {                  // 5. std::move 의 결과를 const& 로 받는다
    std::string a = "옮겨지지 않는다";
    const std::string& r = std::move(a);
    (void)r;
}
void push_without_reserve() {                 // 6. 이동이 없는 타입을 vector 에 담는다
    std::vector<Q1> v;
    for (int i = 0; i < 4; ++i) v.push_back(Q1());
}

int main() {
    Q1 a; Q1 b = std::move(a); (void)b;
    Q2 c; Q2 d = std::move(c); d.p = nullptr;  // 이중 해제를 피해 치운다
    use_after_move();
    move_a_const();
    move_into_const_ref();
    push_without_reserve();
    std::printf("여섯 자리 전부 컴파일됐다\n");
}
```

- 탐침 **여섯 중 몇 개**에 두 컴파일러가 답하나?
- ★★★ 같은 파일을 ASan 으로 돌리면 **몇 건**이 잡히나 — 그 수가 이 배치의 다른 세 편과 어떻게 다른가?
- ★★★ 이 주제가 유난히 조용한 **이유**는 무엇인가?

### 10. ★★ 이 주제의 사실이 다섯 층 중 어디에 있나 (경계)

- 「**`vector` 재할당이 `noexcept` 이동만 쓴다**」는 **표준인가 구현 정의인가**?
- 「**이동한 `std::string` 의 `size()` 가 0 이다**」는 **표준인가 미명시인가**?
- ★★ **두 컴파일러에서 같은 숫자가 나온 것**이 보장의 근거가 되나 — 안 된다면 왜인가?
- ★ 「**이동한 원본을 다시 읽는 것**」은 **UB 인가**?

### 11. 다른 주제와 잇기 (연결)

- **`std::move` 가 캐스트라는 것**의 정본은 몇 번 주제인가?
- ★★ 6번의 「생략이 막힌다」를 실측한 앞 편은 몇 번의 어느 절인가?
- ★★ **이동한 원본도 파괴된다**는 보장은 몇 번 주제에서 나오나?
- ★★★ **러스트는 이동당한 원본을 컴파일러가 막는다** — 어느 갈래 몇 번이고, C++ 은 왜 안 막나?
- ★ **`noexcept` 의 전모**와 **`vector` 재할당 정책**은 각각 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
