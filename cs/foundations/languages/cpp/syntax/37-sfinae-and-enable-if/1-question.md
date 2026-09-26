# cpp/syntax/37 — SFINAE 와 `enable_if` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 「**선언에 치환하다 실패하면 조용히 빠지고, 그 밖의 실패는 하드 에러**」 하나를 칸마다 따라가는 것이다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · libstdc++ 13(★ clang 도 같은 라이브러리) · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex`.
> ★★★ **이 주제의 본체는 두 컴파일러의 골라진 오버로드·하드 에러(1\~6번)와 진단 세기 격자(1번)다.**
> ★ **「부적용인 창」이 있다** — ASan · 어셈블리(탈락한 후보는 코드를 만들지 않는다).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 같은 의도 다섯 판 (예측)

```cpp
/* sf01.cpp */
// 같은 의도 — 「.size() 가 있는 타입만 받는 count_of」 — 를 다섯 판으로. -DFORM=0..4 로 하나만 켠다.
// -DFALLBACK 이면 무엇이든 받는 count_of(...) 를 하나 더 둔다. -DARG=<타입> 으로 인자를 고른다
#include <cstddef>
#include <cstdio>
#include <string>
#include <type_traits>
#include <utility>

struct Plain {
    int v;
};

template <class T, class = void> struct has_size : std::false_type {};
template <class T> struct has_size<T, std::void_t<decltype(std::declval<const T&>().size())>> : std::true_type {};

#if FORM == 0
template <class T> std::size_t count_of(const T& t) { return t.size(); }
#elif FORM == 1
template <class T> std::enable_if_t<has_size<T>::value, std::size_t> count_of(const T& t) { return t.size(); }
#elif FORM == 2
template <class T, std::enable_if_t<has_size<T>::value, int> = 0> std::size_t count_of(const T& t) { return t.size(); }
#elif FORM == 3
template <class T, class = std::void_t<decltype(std::declval<const T&>().size())>>
std::size_t count_of(const T& t) { return t.size(); }
#elif FORM == 4
template <class T>
    requires requires(const T& t) { t.size(); }
std::size_t count_of(const T& t) { return t.size(); }
#endif

#ifdef FALLBACK
int count_of(...) { return -1; }
#endif

int main() {
    ARG x{};
    std::printf("%d\n", static_cast<int>(count_of(x)));
}
```

- ★★★ `-DFORM=0..4` × `-DARG=std::string · int · Plain` × `-DFALLBACK` 유무로 컴파일하면 각 칸은 통과(무엇을 찍나)인가 에러인가?
- ★★★ 에러 칸에서 첫 `error:` 는 몇 행을 가리키나 — 호출 줄(37행)인가?

### 2. ★★★ 반환 타입을 적은 판과 추론하게 둔 판 (예측)

```cpp
/* imm01.cpp */
// 즉시 문맥 — 반환 타입을 decltype 으로 적은 판(기본) 대 auto 로 추론하게 둔 판(-DDEDUCED).
// 둘 다 무엇이든 받는 대안 count_of(...) 가 있다
#include <cstdio>

#ifdef DEDUCED
template <class T> auto count_of(const T& t) { return t.size(); }
#else
template <class T> auto count_of(const T& t) -> decltype(t.size()) { return t.size(); }
#endif
int count_of(...) { return -1; }

int main() { std::printf("%d\n", static_cast<int>(count_of(42))); }
```

- ★★★ 기본과 `-DDEDUCED` 에서 각각 컴파일되나 — 되면 무엇을 찍나?

### 3. ★★★ 기본 템플릿 인자가 읽는 자리 (예측)

```cpp
/* imm02.cpp */
// 즉시 문맥 — 기본 템플릿 인자에서 T::value_type 을 직접 읽는 판(기본) 대
// 보조 클래스 Inner<T> 의 몸통이 읽게 한 판(-DNESTED). 둘 다 대안 kind(...) 가 있다
#include <cstdio>

template <class T> struct Inner {
    using type = typename T::value_type;
};

#ifdef NESTED
template <class T, class = typename Inner<T>::type> const char* kind(T) { return "template"; }
#else
template <class T, class = typename T::value_type> const char* kind(T) { return "template"; }
#endif
const char* kind(...) { return "fallback"; }

int main() { std::printf("%s\n", kind(42)); }
```

- ★★★ 기본과 `-DNESTED` 에서 각각 컴파일되나 — 되면 무엇을 찍나?

### 4. ★★★ 조건만 다른 두 오버로드 (예측)

```cpp
/* redecl.cpp */
// 조건만 다른 두 오버로드 — 기본 템플릿 인자로 enable_if 를 거는 두 모양. -DNTTP 이면 「enable_if_t<…, int> = 0」
#include <cstdio>
#include <type_traits>

#ifdef NTTP
template <class T, std::enable_if_t<std::is_integral_v<T>, int> = 0> const char* kind(T) { return "integral"; }
template <class T, std::enable_if_t<std::is_floating_point_v<T>, int> = 0> const char* kind(T) { return "floating"; }
#else
template <class T, class = std::enable_if_t<std::is_integral_v<T>>> const char* kind(T) { return "integral"; }
template <class T, class = std::enable_if_t<std::is_floating_point_v<T>>> const char* kind(T) { return "floating"; }
#endif

int main() { std::printf("%s %s\n", kind(1), kind(1.5)); }
```

- ★★★ 기본과 `-DNTTP` 에서 각각 컴파일되나 — 에러면 첫 에러는 무엇을 말하나?

### 5. ★★ `if constexpr` 두 자리 (예측)

```cpp
/* ifc01.cpp */
// 오버로드 두 벌 대신 함수 하나 — if constexpr 로 가지를 고른다(has_size 는 void_t 탐지)
#include <cstddef>
#include <cstdio>
#include <string>
#include <type_traits>
#include <utility>

template <class T, class = void> struct has_size : std::false_type {};
template <class T> struct has_size<T, std::void_t<decltype(std::declval<const T&>().size())>> : std::true_type {};

template <class T> std::size_t measure(const T& t) {
    if constexpr (has_size<T>::value) {
        return t.size();
    } else {
        return sizeof(t);
    }
}

int main() { std::printf("%zu %zu\n", measure(std::string("abc")), measure(1.0)); }
```

```cpp
/* ifc02.cpp */
// 템플릿이 아닌 함수의 if constexpr — 버린 가지에 선언 없는 이름을 둔다
int f() {
    if constexpr (false) {
        return no_such_function();
    }
    return 0;
}

int main() { return f(); }
```

- ★★ `ifc01.cpp` 는 무엇을 찍나? `ifc02.cpp` 는 컴파일되나?

### 6. ★ 탐지 관용구의 표준 이름 (예측)

```cpp
/* detect01.cpp */
// 탐지 관용구의 표준 이름 — -DSTD 이면 std::is_detected_v, 아니면 std::experimental::is_detected_v
#include <cstdio>
#include <experimental/type_traits>
#include <string>
#include <utility>

template <class T> using size_expr = decltype(std::declval<const T&>().size());

#ifdef STD
using std::is_detected_v;
#else
using std::experimental::is_detected_v;
#endif

int main() { std::printf("%d %d\n", is_detected_v<size_expr, std::string>, is_detected_v<size_expr, int>); }
```

- ★ 기본(`-std=c++20`)과 `-DSTD`(`-std=c++23`)에서 각각 컴파일되나?

### 7. ★★★ 대안 오버로드와 판 0 (왜)

- ★★★ 1번에서 `-DFALLBACK` 으로 `count_of(...)` 를 두고 `int` 를 넘길 때, 판 0 과 판 1\~4 는 같은 결과를 내나 — 갈린다면 무엇이 가르나?

### 8. ★★★ `= 0` 한 글자 (왜)

- ★★★ 4번의 두 꼴(`class = enable_if_t<…>` · `enable_if_t<…, int> = 0`)에서 컴파일러가 보는 두 오버로드의 「템플릿 서명」은 각각 어떻게 되나?

### 9. ★★ `enable_if<false, …>` 를 읽는 법 (경계)

- ★★ 1번 판 1 의 g++ 에러에서 `no type named ‘type’ in ‘struct std::enable_if<false, long unsigned int>’` 가 나오면, 무엇이 거짓이었는지는 진단의 어느 줄에서 찾나?

### 10. ★★ 줄 수로 판을 고르기 (경계)

- ★★ 1번 격자에서 g++ 판 2·3 이 11줄, 판 1·4 가 17줄이었다. 이것으로 「판 2 가 더 나은 에러를 낸다」고 말할 수 있나?

### 11. 다른 주제와 잇기 (연결)

- ★★ 1번의 `has_size` 는 33편의 어떤 장치에 기대나?
- ★★ 4번의 재선언 함정을 36편의 컨셉으로 되돌려 쓰면 왜 사라지나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
