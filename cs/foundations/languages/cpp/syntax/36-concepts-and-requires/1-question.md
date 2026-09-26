# cpp/syntax/36 — 컨셉과 `requires`(C++20) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 「**제약이 맞지 않으면 후보에서 빠진다**」 와 「**더 제약된 것은 원자 제약의 동일성으로만 판단한다**」 두 가지를 칸마다 따라가는 것이다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · libstdc++ 13(★ clang 도 같은 라이브러리) · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex`.
> ★★★ **이 주제의 본체는 두 컴파일러의 통과·에러와 골라진 오버로드다(1\~4번).**
> ★ **「부적용인 창」이 있다** — ASan · 어셈블리(컨셉은 만들어진 코드에 흔적을 남기지 않는다).
> ★★★ **35편이 잰 오류의 줄 수·자리는 다시 묻지 않는다** — 컨셉이면 첫 에러가 호출 줄, 줄 수는 오히려 늘었다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 같은 제약을 적는 네 자리 (예측)

```cpp
/* form01.cpp */
// 같은 제약(std::integral)을 네 가지 표기로 — -DFORM=1..4 로 하나만 켜고, -DARG=<타입> 으로 인자를 고른다
#include <concepts>

struct Meters {
    int v;
};

#if FORM == 1
template <std::integral T> int take(T) { return 1; }
#elif FORM == 2
template <class T>
    requires std::integral<T>
int take(T) { return 1; }
#elif FORM == 3
template <class T> int take(T) requires std::integral<T> { return 1; }
#elif FORM == 4
int take(std::integral auto) { return 1; }
#endif

int main() { return take(ARG{}) - 1; }
```

- ★★★ `-DFORM=1..4` × `-DARG=int · long · bool · char · double · Meters` 를 두 컴파일러로 컴파일하면 각 칸은 통과인가 에러인가?
- ★★ 네 표기 사이에 결과가 갈리는 인자가 있나?

### 2. ★★★ 매개변수가 둘일 때 (예측)

```cpp
/* form02.cpp */
// 매개변수가 둘일 때 — 이름 붙인 T 하나(-DFORM=1) 대 auto 둘(-DFORM=4)
#include <concepts>
#include <cstdio>

#if FORM == 1
template <std::integral T> int take2(T, T) { return 1; }
#elif FORM == 4
int take2(std::integral auto, std::integral auto) { return 4; }
#endif

int main() { std::printf("%d\n", take2(1, 2L)); }
```

- ★★★ `-DFORM=1` 과 `-DFORM=4` 에서 각각 컴파일되나 — 되면 무엇을 찍나?

### 3. ★★★ 겹치는 두 오버로드 (예측)

```cpp
/* sub01.cpp */
// 두 오버로드 — std::integral 대 std::signed_integral. 인자 넷을 넘겨 어느 쪽이 골라지나 찍는다
#include <concepts>
#include <cstdio>

template <std::integral T> const char* pick(T) { return "std::integral"; }
template <std::signed_integral T> const char* pick(T) { return "std::signed_integral"; }

int main() {
    std::printf("int      -> %s\n", pick(1));
    std::printf("unsigned -> %s\n", pick(1u));
    std::printf("bool     -> %s\n", pick(true));
    std::printf("char     -> %s\n", pick('a'));
}
```

- ★★★ 네 줄에 각각 무엇이 찍히나?
- ★★ 같은 소스를 `-funsigned-char` 로 컴파일하면 어느 줄이 바뀌나?

### 4. ★★★ 컨셉 이름 없이 형질 식으로 (예측)

```cpp
/* sub02.cpp */
// 같은 뜻을 컨셉 없이 형질(trait) 식으로 — -DMODE=1 은 두 오버로드 다 식을 직접 쓴다,
// -DMODE=2 는 앞쪽 식을 컨셉 Int 로 한 번 이름 붙이고 두 오버로드가 그 이름을 쓴다
#include <cstdio>
#include <type_traits>

#if MODE == 1
template <class T>
    requires std::is_integral_v<T>
const char* pick(T) { return "A"; }
template <class T>
    requires std::is_integral_v<T> && std::is_signed_v<T>
const char* pick(T) { return "B"; }
#elif MODE == 2
template <class T> concept Int = std::is_integral_v<T>;
template <class T>
    requires Int<T>
const char* pick(T) { return "A"; }
template <class T>
    requires Int<T> && std::is_signed_v<T>
const char* pick(T) { return "B"; }
#endif

int main() {
    std::printf("unsigned -> %s\n", pick(1u));
    std::printf("int      -> %s\n", pick(1));
}
```

- ★★★ `-DMODE=1` 과 `-DMODE=2` 에서 각각 컴파일되나 — 되면 두 줄에 무엇이 찍히나?

### 5. ★★ `requires` 식 표 (예측)

```cpp
/* req01.cpp */
// requires 식 — 단순 요구 · 타입 요구 · 복합 요구 · 중첩 요구를 타입 넷에 물어 1/0 으로 찍는다
#include <concepts>
#include <cstdio>
#include <string>
#include <vector>

template <class T> concept HasSize = requires(const T& t) { t.size(); };
template <class T> concept HasValueType = requires { typename T::value_type; };
template <class T> concept SizeIsInt = requires(const T& t) {
    { t.size() } -> std::same_as<int>;
};
template <class T> concept BigA = requires { sizeof(T) > 4; };
template <class T> concept BigB = requires { requires sizeof(T) > 4; };

struct Bag {
    int size() const { return 3; }
};

template <class T> void row(const char* name) {
    std::printf("%-18s %7d %12d %9d %4d %4d\n", name, HasSize<T>, HasValueType<T>, SizeIsInt<T>, BigA<T>, BigB<T>);
}

int main() {
    std::printf("%-18s %7s %12s %9s %4s %4s\n", "T", "HasSize", "HasValueType", "SizeIsInt", "BigA", "BigB");
    row<char>("char");
    row<double>("double");
    row<std::string>("std::string");
    row<std::vector<int>>("std::vector<int>");
    row<Bag>("Bag");
}
```

- ★★ 표의 다섯 행 × 다섯 열에 1 과 0 이 어떻게 찍히나? 특히 `BigA` 와 `BigB` 열은?

### 6. ★★ 표준 컨셉 표 (예측)

```cpp
/* stdc01.cpp */
// 표준 컨셉 다섯을 타입 열둘에 물어 1/0 으로 찍는다
#include <concepts>
#include <cstdio>

enum class Color { red };

template <class T> void row(const char* name) {
    std::printf("%-14s %8d %15d %17d %14d %20d\n", name, std::integral<T>, std::signed_integral<T>,
                std::unsigned_integral<T>, std::floating_point<T>, std::convertible_to<T, int>);
}

int main() {
    std::printf("%-14s %8s %15s %17s %14s %20s\n", "T", "integral", "signed_integral", "unsigned_integral",
                "floating_point", "convertible_to<T,int>");
    row<bool>("bool");
    row<char>("char");
    row<signed char>("signed char");
    row<unsigned char>("unsigned char");
    row<char8_t>("char8_t");
    row<wchar_t>("wchar_t");
    row<int>("int");
    row<const int>("const int");
    row<int&>("int&");
    row<unsigned>("unsigned");
    row<double>("double");
    row<Color>("enum class");
}
```

- ★★ `bool` · `char` · `int&` · `double` · `enum class` 행은 각 열이 1 인가 0 인가?

### 7. ★★★ 글자가 같은 두 식 (왜)

- ★★★ 4번의 두 `MODE` 에서 `std::is_integral_v<T>` 는 각각 몇 군데에 · 어떤 자리에 적혀 있나 — 그 차이가 「`B` 가 `A` 보다 더 제약됐나」의 판정에 왜 중요한가?

### 8. ★★ 격자의 0 (경계)

- ★★ 1번 같은 격자에서 「표기 사이 갈린 묶음」이 0 이 나온다면 「네 표기는 언제나 같다」고 말할 수 있나? 그 0 이 진짜 0 인지는 무엇으로 확인하나?

### 9. ★★ 두 컴파일러가 같은 표 (경계)

- ★★ 6번 표가 g++ 와 clang 에서 한 글자도 같았다. 이것으로 「표준 컨셉은 구현마다 같게 정의돼 있다」를 확인했다고 할 수 있나?

### 10. ★ `char` 오버로드 (경계)

- ★ 3번에서 `char` 인자가 어느 오버로드로 가는지에 기대어 코드를 짜면 어떤 위험이 있나?

### 11. 다른 주제와 잇기 (연결)

- ★★ 35편은 컨셉을 걸었을 때 오류의 「자리」와 「줄 수」가 어떻게 바뀐다고 보였나?
- ★★ 5번의 `Bag` 은 `HasSize` 를 만족했다. Rust 의 트레이트 경계라면 같은 모양의 타입이 경계를 넘나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
