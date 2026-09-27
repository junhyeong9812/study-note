# cpp/syntax/09 — rvalue 참조·`std::move`·`std::forward` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — `std::move` 가 **무엇을 하고 무엇을 안 하는지**,
> 그리고 **한 낱말이 빠졌을 때 무엇이 조용히 달라지는지**를 맞힐 수 있는지 묻는다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · x86-64 Linux · `objdump`/`nm`(GNU Binutils 2.42) · ASan.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **「복사인가 이동인가」는 읽어서 답하지 말고 로그로 센다.** 이 문서의 근거가 전부 그것이다.
> ★ **네 번째 창은 생성자·소멸자 로그**이고, 보조로 `objdump`·`nm`·ASan 을 쓴다.
> 선행 — [목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/)(값 범주) · 형제 [`07번`](../07-references-vs-pointers/)(참조) · 형제 [`01번`](../01-function-overloading-and-overload-resolution/)(오버로드 해석).
> 이 주제는 [목록의 **11번 주제**](../11-choosing-parameter-passing/)로 이어지는 사슬의 가운데 칸이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ `std::move` 에 넣으면 무엇이 나오나 (예측)

```cpp
/* mvsem01.cpp */
// std::move 는 캐스트다 — 타입으로 확인한다
#include <type_traits>
#include <string>
#include <utility>

template <class T> struct TypeOf;

int main() {
    int i = 0;
    const int ci = 0;
    std::string s = "hi";

    TypeOf<decltype(std::move(i))>              m1;
    TypeOf<decltype(static_cast<int&&>(i))>     m2;
    TypeOf<decltype(std::move(ci))>             m3;   // ★ const 가 붙어 나온다
    TypeOf<decltype(std::move(s))>              m4;
    TypeOf<decltype(std::move(std::move(i)))>   m5;   // 두 번 걸어도
    static_assert(std::is_same_v<decltype(std::move(i)),
                                 decltype(static_cast<int&&>(i))>);
}
```

- `m1`\~`m5` 의 꺾쇠 안에 **무엇이 찍히는가**?
- `m1` 과 `m2` 는 **같은가 다른가** — 그것이 무엇을 뜻하는가?
- `m3`(`std::move(ci)`)이 **다른 넷과 어떻게 다른가**?
- 맨 아래 `static_assert` 는 **통과하는가**?

### 2. ★★★ 캐스트 세 개의 기계어 (예측)

```cpp
/* mvsem02.cpp */
// std::move 가 낳는 코드 — 손으로 쓴 캐스트와 같은가
#include <utility>

int&& via_move(int& x) { return std::move(x); }
int&& via_cast(int& x) { return static_cast<int&&>(x); }
int&  no_cast (int& x) { return x; }
```

- `-O0` 으로 컴파일해 역어셈블하면 **세 함수의 명령어 열이 같은가**?
- 셋 중 하나에만 있는 명령이 있다면 **무엇인가**?
- `-O2` 로 올리면 답이 **바뀌는가**?
- `nm -C` 로 심볼을 보면 `-O0` 과 `-O2` 가 **무엇이 다른가**?

### 3. ★ 세 장면의 로그 (예측)

```cpp
/* mvsem03.cpp */
// 복사와 이동을 로그로 가른다
#include <cstdio>
#include <utility>

struct Noisy {
    int id;
    explicit Noisy(int i) : id(i) { std::printf("    ctor(%d)\n", id); }
    Noisy(const Noisy& o) : id(o.id) { std::printf("    copy(%d)\n", id); }
    Noisy(Noisy&& o) noexcept : id(o.id) { std::printf("    move(%d)\n", id); o.id = -1; }
    ~Noisy() { std::printf("    dtor(%d)\n", id); }
};

int main() {
    std::puts("[1] Noisy a(1); Noisy b = a;");
    { Noisy a(1); Noisy b = a;
      std::printf("    a.id=%d b.id=%d\n", a.id, b.id); }
    std::puts("[2] Noisy c(2); Noisy d = std::move(c);");
    { Noisy c(2); Noisy d = std::move(c);
      std::printf("    c.id=%d d.id=%d\n", c.id, d.id); }
    std::puts("[3] std::move 만 하고 아무 데도 안 쓰면");
    { Noisy e(3); (void)std::move(e);
      std::printf("    e.id=%d  — 아무 일도 안 일어났다\n", e.id); }
    std::puts("[4] main 끝");
}
```

- `[1]`·`[2]`·`[3]` 에서 **각각 어떤 줄이 몇 개** 찍히는가?
- `[3]` 의 `e.id` 는 **얼마**인가?
- `[2]` 의 마지막 두 `dtor` 는 **어떤 순서**로 찍히는가?

### 4. ★★ 이동 다음 줄 (예측)

```cpp
/* mvsem04.cpp */
// 이동 후 원본은 어떤 상태인가 — 세 타입을 갈라 찍는다
#include <cstdio>
#include <memory>
#include <string>
#include <utility>
#include <vector>

int main() {
    std::string s1 = "hi";                                   // 짧다(SSO)
    std::string d1 = std::move(s1);
    std::printf("string 짧음 : 원본 size=%zu empty=%d 내용=\"%s\" | 대상=\"%s\"\n",
                s1.size(), static_cast<int>(s1.empty()), s1.c_str(), d1.c_str());

    std::string s2 = "0123456789012345678901234567890123456789";   // 길다(힙)
    std::string d2 = std::move(s2);
    std::printf("string 김   : 원본 size=%zu empty=%d 내용=\"%s\" | 대상 size=%zu\n",
                s2.size(), static_cast<int>(s2.empty()), s2.c_str(), d2.size());

    std::vector<int> v1{1, 2, 3};
    std::vector<int> v2 = std::move(v1);
    std::printf("vector      : 원본 size=%zu empty=%d capacity=%zu | 대상 size=%zu\n",
                v1.size(), static_cast<int>(v1.empty()), v1.capacity(), v2.size());

    std::unique_ptr<int> p1 = std::make_unique<int>(7);
    std::unique_ptr<int> p2 = std::move(p1);
    std::printf("unique_ptr  : 원본 null=%d | 대상 *p2=%d\n",
                static_cast<int>(p1 == nullptr), *p2);

    s1 = "다시 쓴다";                       // 이동 후에도 대입은 된다
    v1.push_back(9);
    std::printf("되살리기    : s1=\"%s\" v1.size=%zu v1[0]=%d\n",
                s1.c_str(), v1.size(), v1[0]);
}
```

- 다섯 줄의 출력을 **각각** 맞힐 수 있는가?
- **짧은 문자열**과 **긴 문자열**의 원본이 **같은 상태**인가?
- `unique_ptr` 의 원본은 어떤 상태이고, 그것은 **관찰인가 보장인가**?
- 마지막 줄(「되살리기」)이 **컴파일되고 돌아가는** 이유는?

### 5. ★★ 한 낱말만 다른 두 클래스 (예측)

```cpp
/* mvsem07.cpp */
// 이동 생성자에 noexcept 가 없으면 vector 는 복사한다
#include <cstdio>
#include <type_traits>
#include <vector>

static int g_copy = 0, g_move = 0;

struct Safe {                                   // 이동이 noexcept
    int id;
    explicit Safe(int i) : id(i) {}
    Safe(const Safe& o) : id(o.id) { ++g_copy; }
    Safe(Safe&& o) noexcept : id(o.id) { ++g_move; }
};

struct Risky {                                  // 같은데 noexcept 만 없다
    int id;
    explicit Risky(int i) : id(i) {}
    Risky(const Risky& o) : id(o.id) { ++g_copy; }
    Risky(Risky&& o) : id(o.id) { ++g_move; }
};

template <class T>
void grow(const char* label) {
    g_copy = g_move = 0;
    std::vector<T> v;
    v.reserve(1);
    for (int i = 0; i < 4; ++i) v.push_back(T(i));
    std::printf("  %-6s nothrow_move=%d  ->  copy %d회 · move %d회  (size=%zu cap=%zu)\n",
                label, static_cast<int>(std::is_nothrow_move_constructible_v<T>),
                g_copy, g_move, v.size(), v.capacity());
}

int main() {
    std::puts("reserve(1) 뒤 push_back 을 네 번 — 재할당이 두 번 일어난다");
    grow<Safe>("Safe");
    grow<Risky>("Risky");
}
```

- `Safe` 와 `Risky` 의 **`copy` · `move` 횟수**를 각각 맞힐 수 있는가?
- 두 클래스의 소스에서 **다른 것은 무엇 하나**인가?
- `nothrow_move` 칸은 각각 **0 인가 1 인가**?
- 컴파일러는 이 차이를 **경고로 알려 주는가**?

### 6. ★★ `const` 가 하나 붙으면 (예측)

```cpp
/* mvsem05.cpp */
// const 객체를 move 하면 — 조용히 복사가 된다
#include <cstdio>
#include <string>
#include <utility>

struct Noisy {
    int id;
    explicit Noisy(int i) : id(i) { std::printf("    ctor(%d)\n", id); }
    Noisy(const Noisy& o) : id(o.id) { std::printf("    copy(%d)\n", id); }
    Noisy(Noisy&& o) noexcept : id(o.id) { std::printf("    move(%d)\n", id); o.id = -1; }
    ~Noisy() { std::printf("    dtor(%d)\n", id); }
};

int main() {
    std::puts("[1] Noisy a(1);       Noisy b = std::move(a);");
    { Noisy a(1); Noisy b = std::move(a); (void)b; }
    std::puts("[2] const Noisy c(2); Noisy d = std::move(c);   ★ const");
    { const Noisy c(2); Noisy d = std::move(c); (void)d; }

    std::puts("[3] std::string 으로 같은 일을");
    const std::string cs = "0123456789012345678901234567890123456789";
    std::string dst = std::move(cs);
    std::printf("    원본 size=%zu (이동이었다면 0 이거나 미명시) 대상 size=%zu\n",
                cs.size(), dst.size());
}
```

- `[1]` 과 `[2]` 에서 **각각 어떤 생성자**가 불리는가?
- `[3]` 의 `cs.size()` 는 **얼마**인가 — 그것이 무엇을 말해 주는가?
- 이 파일을 컴파일하면 **경고가 몇 개** 나오는가?
- 경고를 세는 명령으로 `grep -c warning` 과 `grep -c 'warning:'` 중 **어느 쪽**을 써야 하는가?

### 7. ★ 네 번 불렀는데 (왜)

```cpp
/* mvsem06.cpp */
// 전달 참조와 참조 축약 — T 와 T&& 가 각각 무엇으로 정해지나
#include <utility>

template <class T> struct TypeOf;

template <class T>
void probe(T&& x) {
    TypeOf<T> a;              // 추론된 T
    TypeOf<decltype(x)> b;    // 축약된 매개변수 타입
    (void)x;
}

int main() {
    int i = 0;
    const int ci = 0;
    probe(i);              // lvalue
    probe(ci);             // const lvalue
    probe(42);             // prvalue
    probe(std::move(i));   // xvalue
}
```

- 에러가 **몇 줄** 나오는가 — 왜 호출 횟수와 다른가?
- 각 호출에서 `T` 는 **무엇으로 추론**되고, `decltype(x)` 는 **무엇**인가?
- `probe(42)` 와 `probe(std::move(i))` 가 **같은 답**인 이유는?
- 함수 안에서 `x` 는 **lvalue 인가 rvalue 인가** — 그것이 `std::forward` 가 필요한 이유와 어떻게 이어지는가?

### 8. ★★ 돌려주는 자리에 `std::move` 를 붙이면 (경계)

```cpp
/* mvsem08.cpp */
// return std::move(지역) 은 무엇을 막는가
#include <cstdio>
#include <utility>

struct Noisy {
    int id;
    explicit Noisy(int i) : id(i) { std::printf("    ctor(%d)\n", id); }
    Noisy(const Noisy& o) : id(o.id) { std::printf("    copy(%d)\n", id); }
    Noisy(Noisy&& o) noexcept : id(o.id) { std::printf("    move(%d)\n", id); }
    ~Noisy() { std::printf("    dtor(%d)\n", id); }
};

Noisy by_nrvo()   { Noisy n(1); return n; }                  // 그냥 돌려준다
Noisy by_move()   { Noisy n(2); return std::move(n); }       // ★ 이동을 강요한다
Noisy by_pessim() { return std::move(Noisy(3)); }            // ★ 임시에 move
Noisy by_param(Noisy n) { return std::move(n); }              // ★ 매개변수는 다르다

int main() {
    std::puts("[1] return n;                 (NRVO 가 가능하다)");
    { Noisy a = by_nrvo(); (void)a; }
    std::puts("[2] return std::move(n);");
    { Noisy b = by_move(); (void)b; }
    std::puts("[3] return std::move(Noisy(3));");
    { Noisy c = by_pessim(); (void)c; }
    std::puts("[4] Noisy by_param(Noisy n) { return std::move(n); }");
    { Noisy d = by_param(Noisy(4)); (void)d; }
}
```

- `[1]`\~`[4]` 의 로그가 **각각 몇 줄**인가?
- 컴파일 경고는 **몇 개**이고 **이름이 몇 종류**인가?
- `[4]`(매개변수)가 `[2]`(지역)와 **다른 경고 이름**을 받는 이유는?
- `cc exit` 은 **얼마**인가?

### 9. ★★ 이동한 벡터를 다시 쓰면 (경계)

```cpp
/* mvsem10.cpp */
// 이동 후 원본에 「전제 조건이 있는 연산」을 부르면 — 유효하지만 비어 있는 것이 문제다
#include <cstdio>
#include <vector>
#include <utility>

int main() {
    std::vector<int> v1{1, 2, 3};
    std::vector<int> v2 = std::move(v1);

    std::fprintf(stderr, "[마커] v1.size()=%zu  v1.empty()=%d  — 여기까지는 적법하다\n",
                 v1.size(), static_cast<int>(v1.empty()));
    std::fprintf(stderr, "[마커] 이제 v1.front() 를 부른다\n");
    int x = v1.front();                 // ★ 빈 컨테이너의 front() 는 UB
    std::fprintf(stderr, "[마커] v1.front()=%d\n", x);
    (void)v2;
}
```

- `size()`·`empty()` 를 부르는 것은 **적법한가**?
- `front()` 는 어떤가 — **무엇이 근거**인가?
- `-Wall -Wextra -pedantic` 은 이것을 **경고로 잡는가**?
- 마커를 **표준 출력이 아니라 표준 오류**로 찍은 이유는?

### 10. ★ 헤더를 안 넣었는데 컴파일된다 (경계)

```cpp
/* mvsem09.cpp */
// <utility> 를 안 넣고 std::move 를 쓴다 — 이 구현에서는 통과한다
#include <cstdio>
#include <string>

int main() {
    std::string a = "0123456789012345678901234567890123456789";
    std::string b = std::move(a);          // ★ <utility> 가 없다
    std::printf("a.size=%zu b.size=%zu\n", a.size(), b.size());
}
```

- 이 파일에 `<utility>` 가 없는데 **컴파일되는가**?
- 그렇다면 그것은 **표준이 보장한 것인가**?
- 두 컴파일러에서 모두 통과했다면 **이식된다고 말해도 되는가**?
- 무엇을 찍어 보면 **왜 통과했는지**를 알 수 있는가?

### 11. 다른 주제와 잇기 (연결)

- 「어떤 식이 xvalue 인가」의 정본은 목록의 몇 번인가?
- 「이동 생성자를 어떻게 구현하나」와 「유효하되 미지정」이라는 계약의 정본은 목록의 몇 번인가?
- `noexcept` 가 **계약으로서** 무엇을 뜻하는지의 정본은 목록의 몇 번인가?
- 「그래서 매개변수를 무엇으로 받나」의 정본은 목록의 몇 번인가?
- Rust 에서 이동 후 원본을 쓰면 무슨 일이 나는가 — C++ 와 **무엇이 다른 층**인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
