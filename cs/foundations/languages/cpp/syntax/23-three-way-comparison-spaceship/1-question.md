# cpp/syntax/23 — 3방향 비교 `<=>`(C++20) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「이 비교 식이 어느 함수를 부르나」를 맞히는 것**이 절반이다 — 「`<=>` 를 썼으니 다 된다」로 뭉개지 말고
> **관계 넷 · `==`·`!=` · 뒤집힌 판**을 갈라야 한다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 본체는 「호출 로그」다**(1·2·5번) — `<=>` 와 `==` 에 로그를 심어 **재작성을 출력으로** 증명한다.
> ★ **「부적용인 창」이 있다** — ASan(메모리 오류가 없다).
> ★★★ **[22번](../22-operator-overloading/) (1)의 「`1 + a` 가 막힌다」와 한 사슬이다** — 5번이 그 급소다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ `<=>` 만 손으로 쓴 타입 (예측)

```cpp
/* cmp03.cpp */
// <=> 를 손으로 쓰면(= default 가 아니면) — 관계 연산자는 그것으로 다시 써지나, == 도 생기나
#include <algorithm>
#include <compare>
#include <cstdio>

struct Id {
    int v;
    std::strong_ordering operator<=>(const Id& o) const {      // ★ 손으로 썼다 — < 는 안 썼다
        std::printf("      Id::operator<=>  (%d, %d)\n", v, o.v);
        return v <=> o.v;
    }
};

int main() {
    Id a{1}, b{2};
    std::printf("(1) a < b\n");          std::printf("    결과 %d\n", (int)(a < b));
    std::printf("(2) a >= b\n");         std::printf("    결과 %d\n", (int)(a >= b));
    std::printf("(3) std::max(a, b)\n"); std::printf("    결과 %d\n", std::max(a, b).v);
#ifdef ASK_EQ
    bool eq = (a == b);                                     // 4. 같음 연산자
    (void)eq;
#endif
}
```

- ★★★ `(1)`·`(2)`·`(3)` 에서 각각 **무엇이 불리나** — `operator<` 가 없는데 `a < b` 가 되나?
- ★★★ `-DASK_EQ` 로 4번(`a == b`)을 켜면 **컴파일되나**?
- ★ 파이썬의 `max` 는 `__gt__` 를 부른다 — C++ 의 `std::max` 는 무엇에 기대나?

### 2. ★★★ `= default` 인 `<=>` 가 딸려 주는 `==` (예측)

```cpp
/* cmp02.cpp */
// = default 인 <=> 가 == 를 어디서 가져오나 — 멤버의 <=> 와 == 에 각각 로그를 심는다
#include <compare>
#include <cstdio>

struct Part {
    int v;
    std::strong_ordering operator<=>(const Part& o) const {
        std::printf("      Part::operator<=>\n");  return v <=> o.v;
    }
    bool operator==(const Part& o) const {
        std::printf("      Part::operator==\n");   return v == o.v;
    }
};

struct Whole {
    Part p;
    auto operator<=>(const Whole&) const = default;   // == 는 적지 않았다
};

int main() {
    Whole a{{1}}, b{{2}};
    std::printf("(1) a <  b\n");   (void)(a <  b);
    std::printf("(2) a >= b\n");   (void)(a >= b);
    std::printf("(3) a == b\n");   (void)(a == b);
    std::printf("(4) a != b\n");   (void)(a != b);
}
```

- ★★★ `(3) a == b` 에서 **`Part::operator<=>` 와 `Part::operator==` 중 무엇이** 찍히나?
- ★★ `(4) a != b` 는?
- ★ `Whole` 에는 `==` 를 안 적었다 — 그런데 왜 `a == b` 가 컴파일되나?

### 3. ★★ `auto` 반환의 범주 (예측)

```cpp
/* cmp04.cpp */
// <=> = default 의 반환 타입을 auto 로 두면 무엇이 되나 — 멤버 중 가장 약한 것으로 정해지나
#include <cmath>
#include <compare>
#include <cstdio>
#include <type_traits>

struct Nocase {                                   // 대소문자를 무시하는 글자 — weak_ordering
    char c;
    std::weak_ordering operator<=>(const Nocase& o) const {
        auto low = [](char x) { return (x >= 'A' && x <= 'Z') ? char(x + 32) : x; };
        return low(c) <=> low(o.c);
    }
    bool operator==(const Nocase& o) const { return (*this <=> o) == 0; }
};

struct I  { int a; int b;           auto operator<=>(const I&)  const = default; };
struct W  { int a; Nocase n;        auto operator<=>(const W&)  const = default; };
struct D  { int a; double d;        auto operator<=>(const D&)  const = default; };
struct WD { Nocase n; double d;     auto operator<=>(const WD&) const = default; };

static_assert(std::is_same_v<decltype(I{}  <=> I{}),  std::strong_ordering>);
static_assert(std::is_same_v<decltype(W{}  <=> W{}),  std::weak_ordering>);
static_assert(std::is_same_v<decltype(D{}  <=> D{}),  std::partial_ordering>);
static_assert(std::is_same_v<decltype(WD{} <=> WD{}), std::partial_ordering>);
#ifdef WRONG
static_assert(std::is_same_v<decltype(D{} <=> D{}), std::strong_ordering>);   // ★ 일부러 틀리게 적는다
#endif

int main() {
    D x{1, NAN}, y{1, 2.0};
    auto r = x <=> y;
    std::printf("(1) D{1,NaN} <=> D{1,2.0} 가 unordered 인가 : %d\n", (int)(r == std::partial_ordering::unordered));
    std::printf("(2) x < y %d · x > y %d · x == y %d · x != y %d\n",
                (int)(x < y), (int)(x > y), (int)(x == y), (int)(x != y));
    D z{1, NAN};
    std::printf("(3) 같은 NaN 끼리  z == z : %d\n", (int)(z == z));
    W u{1, {'a'}}, v{1, {'A'}};
    std::printf("(4) W{1,'a'} <=> W{1,'A'} 가 equivalent 인가 : %d · u == v : %d\n",
                (int)((u <=> v) == std::weak_ordering::equivalent), (int)(u == v));
}
```

- ★★ 네 `static_assert` 는 **전부 통과**하나 — 즉 `I`·`W`·`D`·`WD` 는 각각 무슨 범주인가?
- ★★★ `(1)`·`(2)` 에서 NaN 이 낀 비교의 결과는 — `x < y`·`x > y`·`x == y`·`x != y` 가 각각 무엇인가?
- ★ `(3)` 같은 NaN 끼리 `z == z` 는?

### 4. ★★ 선언 순서만 바꾼 두 날짜 (예측)

```cpp
/* cmp05.cpp */
// = default 는 멤버를 선언 순서대로 사전식 비교한다 — 선언 순서만 바꾸면 결과가 바뀌나
#include <compare>
#include <cstdio>

struct DateYMD { int year, month, day;  auto operator<=>(const DateYMD&) const = default; };
struct DateDMY { int day, month, year;  auto operator<=>(const DateDMY&) const = default; };   // 순서만 바꿨다

int main() {
    // 같은 두 날짜 — 2024-12-31 과 2025-01-01
    DateYMD a{2024, 12, 31}, b{2025, 1, 1};
    DateDMY c{31, 12, 2024}, d{1, 1, 2025};
    std::printf("(1) year,month,day 순서 — 2024-12-31 < 2025-01-01 : %d\n", (int)(a < b));
    std::printf("(2) day,month,year 순서 — 2024-12-31 < 2025-01-01 : %d\n", (int)(c < d));
}
```

- ★★ `(1)` 과 `(2)` 는 **같은 두 날짜**를 비교한다 — 답이 같은가?

### 5. ★★★ 22편과 같은 모양 — 멤버 `<=>(long)` 에 정수를 왼쪽에 (예측)

```cpp
/* cmp06.cpp */
// 재작성 후보가 대칭까지 해 주나 — 22편의 「1 + a 가 막힌다」와 같은 모양을 <=> 로
#include <compare>
#include <cstdio>

struct Money {
    long won;
    std::strong_ordering operator<=>(long o) const {           // ★ 멤버 — 오른쪽만 long
        std::printf("      Money::operator<=>(long)  this=%ld o=%ld\n", won, o);
        return won <=> o;
    }
    bool operator==(long o) const {                             // ★ 멤버 — 오른쪽만 long
        std::printf("      Money::operator==(long)   this=%ld o=%ld\n", won, o);
        return won == o;
    }
};

int main() {
    Money a{1000};
    std::printf("(1) a < 5000\n");    std::printf("    결과 %d\n", (int)(a < 5000));
    std::printf("(2) 5000 < a\n");    std::printf("    결과 %d\n", (int)(5000 < a));
    std::printf("(3) 1000 == a\n");   std::printf("    결과 %d\n", (int)(1000 == a));
    std::printf("(4) 7 != a\n");      std::printf("    결과 %d\n", (int)(7 != a));
}
```

- ★★★ `(2) 5000 < a` 는 **컴파일되나** — 22편 (1)의 `1 + a` 와 같은가?
- ★★★ 된다면 로그의 **`this` 와 `o`** 는 각각 무엇인가 — 그것이 무엇을 증명하나?
- ★★ `(3) 1000 == a` 와 `(4) 7 != a` 는 무엇을 부르나?

### 6. ★★ `<` 와 `==` 만 가진 옛 타입을 멤버로 (예측)

```cpp
/* cmp09.cpp */
// 멤버가 <=> 없이 < 와 == 만 가진 옛 타입이면 — auto 는 지워지고, 반환 타입을 적으면 살아나나
#include <compare>
#include <cstdio>

struct Legacy {                                   // C++17 식 — < 와 == 만 있다
    int v;
    bool operator< (const Legacy& o) const { std::printf("      Legacy::operator<\n");  return v <  o.v; }
    bool operator==(const Legacy& o) const { std::printf("      Legacy::operator==\n"); return v == o.v; }
};

struct Named {                                    // ★ 반환 타입을 적었다
    Legacy l;
    std::strong_ordering operator<=>(const Named&) const = default;
};

#ifdef AUTO
struct Guess {                                    // ★ auto 로 두었다
    Legacy l;
    auto operator<=>(const Guess&) const = default;
};
bool try_auto(const Guess& a, const Guess& b) { return a < b; }
#endif

int main() {
    Named a{{1}}, b{{2}};
    std::printf("(1) Named a < b\n");  std::printf("    결과 %d\n", (int)(a < b));
    std::printf("(2) Named b < a\n");  std::printf("    결과 %d\n", (int)(b < a));
}
```

- ★★ `Named`(반환 타입 `std::strong_ordering`)의 `a < b` 는 되나 — 된다면 **로그에 무엇이 어떤 순서로** 찍히나?
- ★★ `-DAUTO` 로 `Guess`(반환 타입 `auto`)를 켜면?
- ★ g++ 는 그때 **처방**을 말해 주나?

### 7. ★ C++17 로 던지면 · `<compare>` 를 빼면 (경계)

- ★★ `auto operator<=>(const Ver&) const = default;` 를 `-std=c++17` 로 던지면 컴파일러는 `<=>` 를 **무엇으로 읽나**?
- ★ `-std=c++20` 인데 `#include <compare>` 를 빼면?

### 8. ★★ `-O2` 에서 `= default` 판과 손으로 쓴 판 (경계)

- ★★ `lt_default`/`lt_hand`, `eq_default`/`eq_hand` 네 쌍(두 연산자 × 두 컴파일러) 중 **글자로 같아진 것**은 몇 쌍인가?
- ★★ 그 결과에서 「`= default` 는 느리다」로 갈 수 있나?

### 9. ★★ `int` 를 돌려주는 `==` 로 `!=` 를 쓰면 (경계)

- ★★ `int operator==(const Tag&) const` 만 두고 `a != b` 를 쓰면 두 컴파일러의 **`cc exit`** 는?
- ★ 1번 줄 `a == b`(직접 호출)는 문제가 되나?

### 10. ★★★ 「`==` 는 따로」 규칙 (왜)

- ★★★ `==` 를 `<=>` 에서 만들지 않는 **이유**는 무엇으로 설명되나?
- ★★ 그러면 「`<=> = default` 가 `==` 도 준다」는 말은 **정확히** 어떻게 고쳐 적어야 하나?

### 11. ★★ 이 주제의 사실이 다섯 층 중 어디에 있나 (경계)

- ★★ 「`5000 < a` 가 `0 < (a <=> 5000)` 으로 다시 써진다」는 어느 층인가?
- ★★ 「`= default` 판과 손 판의 기계어가 다르다」는?
- ★ 「clang 이 `bool` 이 아닌 `==` 재작성을 통과시킨다」는 어느 칸의 무엇인가?

### 12. 다른 주제와 잇기 (연결)

- ★★★ Rust 의 `PartialOrd`·`Ord` 는 C++20 의 어느 범주와 짝이 되나 — **짝이 없는 범주**는?
- ★★ Rust 28편은 **대칭**을 무엇이라 결론냈고, C++20 은 어떻게 다른가?
- ★★ 파이썬은 `__lt__` 하나로 정렬이 되고 `total_ordering` 이 나머지를 채운다 — C++20 에서 그 일을 **누가** 하나?
- ★ 22편의 「대칭 = 비멤버 × 암묵 변환」 표는 **어느 연산자에서** 그대로 남나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
