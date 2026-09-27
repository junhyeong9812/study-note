# cpp/syntax/39 — 람다와 캡처 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 「**람다는 캡처를 멤버로 든 객체다 — 참조를 들었으면 대상의 수명을 넘지 못한다**」 하나를 칸마다 따라가는 것이다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · libstdc++ 13(★ clang 도 같은 라이브러리) · GNU nm 2.42 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex`. ASan 은 `-O0 -fsanitize=address -g`.
> ★★★ **이 주제의 본체는 ASan(1번)이다** — 댕글링 칸의 **값은 UB 의 한 결과라 묻지 않는다.** 묻는 것은 **리포트가 나오나 · 무슨 이름인가**다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 캡처 일곱 × 부르는 때 셋 (예측)

```cpp
/* cap01.cpp */
// 캡처 일곱(-DCAP=1..7) × 부르는 때 셋(-DWHEN=1..3). 캡처 대상은 42 로 만들고,
// WHEN=1 은 만든 뒤 대상을 7 로 바꾸고 부른다. 값은 표준 오류로 찍는다
#include <cstdio>
#include <functional>
#include <memory>
#include <utility>

struct Counter {
    int v = 42;
    auto by_this() { return [this] { return v; }; }
    auto by_copy() { return [*this] { return v; }; }
};

#if CAP == 1
#define SETUP int x = 42;
#define LAMBDA [x] { return x; }
#define CHANGE x = 7;
#elif CAP == 2
#define SETUP int x = 42;
#define LAMBDA [&x] { return x; }
#define CHANGE x = 7;
#elif CAP == 3
#define SETUP int x = 42;
#define LAMBDA [=] { return x; }
#define CHANGE x = 7;
#elif CAP == 4
#define SETUP int x = 42;
#define LAMBDA [&] { return x; }
#define CHANGE x = 7;
#elif CAP == 5
#define SETUP Counter c;
#define LAMBDA c.by_this()
#define CHANGE c.v = 7;
#elif CAP == 6
#define SETUP Counter c;
#define LAMBDA c.by_copy()
#define CHANGE c.v = 7;
#elif CAP == 7
#define SETUP auto p = std::make_unique<int>(42);
#define LAMBDA [p = std::move(p)] { return *p; }
#define CHANGE
#endif

#if WHEN == 1
int call_now() {
    SETUP
    auto f = LAMBDA;
    CHANGE
    return f();
}
#elif WHEN == 2
auto make() {
    SETUP
    return LAMBDA;
}
#endif

int main() {
#if WHEN == 1
    std::fprintf(stderr, "%d\n", call_now());
#elif WHEN == 2
    auto f = make();
    std::fprintf(stderr, "%d\n", f());
#elif WHEN == 3
    std::function<int()> keep;
    {
        SETUP
        keep = LAMBDA;
    }
    std::fprintf(stderr, "%d\n", keep());
#endif
}
```

- ★★★ 21칸(`CAP=1..7` × `WHEN=1..3`)을 두 컴파일러의 `-O0` ASan 으로 돌리면, 어느 칸이 값을 찍고(무슨 값을) 어느 칸이 ASan 리포트(무슨 이름)로 멈추나? 컴파일이 안 되는 칸이 있나?
- ★★ 같은 바이너리를 `ASAN_OPTIONS=detect_stack_use_after_return=0` 으로 돌리면 어느 칸의 리포트가 사라지나?
- ★★ `-Wall -Wextra` 경고는 리포트가 나는 칸 중 몇 칸에서 나나?

### 2. ★★★ 멤버 함수 안의 `[=]` (예측)

```cpp
/* thiscap.cpp */
// 멤버 함수 안의 람다 — 캡처 목록 세 모양(-DFORM=1..3). 멤버 v 를 읽는다
#include <cstdio>

struct Widget {
    int v = 42;
    int read() {
#if FORM == 1
        auto f = [=] { return v; };
#elif FORM == 2
        auto f = [=, this] { return v; };
#elif FORM == 3
        auto f = [=, *this] { return v; };
#endif
        return f();
    }
};

int main() { std::printf("%d\n", Widget{}.read()); }
```

- ★★★ `FORM=1..3` × `-std=c++14 · c++17 · c++20` × 두 컴파일러에서 각 칸은 침묵 · 경고 · 에러 중 무엇인가?

### 3. ★★ 값 캡처를 람다 안에서 올린다 (예측)

```cpp
/* mut01.cpp */
// 값 캡처한 n 을 람다 안에서 올린다 — -DMUT 이면 mutable. 원본 n 과 람다의 복사본을 함께 찍는다
#include <cstdio>

int main() {
    int n = 0;
#ifdef MUT
    auto inc = [n]() mutable { return ++n; };
#else
    auto inc = [n]() { return ++n; };
#endif
    std::printf("call 1 -> %d\n", inc());
    std::printf("call 2 -> %d\n", inc());
    auto copy = inc;
    std::printf("copy   -> %d\n", copy());
    std::printf("inc    -> %d\n", inc());
    std::printf("outer n = %d\n", n);
}
```

- ★★ `-DMUT` 없이 컴파일되나? `-DMUT` 로 돌리면 다섯 줄에 무엇이 찍히나?

### 4. ★★★ 옮겨 받은 `unique_ptr` 을 담는다 (예측)

```cpp
/* mo01.cpp */
// 초기화 캡처로 unique_ptr 을 옮겨 받은 람다를 담는다 — 기본 std::function, -DMOF 이면 std::move_only_function
#include <cstdio>
#include <functional>
#include <memory>
#include <utility>

int main() {
    auto p = std::make_unique<int>(42);
    auto f = [p = std::move(p)] { return *p; };
#ifdef MOF
    std::move_only_function<int()> g = std::move(f);
#else
    std::function<int()> g = std::move(f);
#endif
    std::printf("%d %d\n", g(), p == nullptr);
}
```

- ★★★ 기본(`std::function`)과 `-DMOF`(`std::move_only_function`)를 `-std=c++23` 으로 컴파일하면 각각? `-DMOF` 를 `-std=c++20` 으로는?

### 5. ★ 제네릭 람다와 템플릿 람다 (예측)

```cpp
/* gen01.cpp */
// 제네릭 람다(auto) 대 템플릿 람다(C++20 []<typename T>). 템플릿 람다는 vector 만 받는다.
// -DBAD 이면 템플릿 람다에 int 를 넘긴다
#include <cstdio>
#include <vector>

int main() {
    auto twice = [](auto x) { return x + x; };
    auto first = []<typename T>(const std::vector<T>& v) { return v.front(); };
    std::printf("%d %.1f\n", twice(21), twice(1.25));
    std::printf("%d %.1f\n", first(std::vector<int>{7, 8}), first(std::vector<double>{2.5}));
#ifdef BAD
    std::printf("%d\n", first(42));
#endif
}
```

- ★ 기본으로 돌리면 두 줄에 무엇이 찍히나? `-DBAD` 는 컴파일되나? `nm -C` 로 보면 `twice` 의 호출 연산자는 몇 벌인가?

### 6. ★ 람다의 타입과 크기 (예측)

```cpp
/* type01.cpp */
// 람다 타입은 고유한가 — 글자가 같은 두 람다 · 캡처에 따른 크기 · 캡처 없는 람다의 함수 포인터 변환
#include <cstdio>
#include <type_traits>

int main() {
    int x = 1;
    double d = 2.0;
    auto a = [] { return 1; };
    auto b = [] { return 1; };
    auto c = [x] { return x; };
    auto e = [&x] { return x; };
    auto g = [x, d] { return x + d; };
    auto h = [&x, &d] { return x + d; };
    std::printf("same type a b     = %d\n", std::is_same_v<decltype(a), decltype(b)>);
    std::printf("sizeof []         = %zu\n", sizeof(a));
    std::printf("sizeof [x]        = %zu\n", sizeof(c));
    std::printf("sizeof [&x]       = %zu\n", sizeof(e));
    std::printf("sizeof [x, d]     = %zu\n", sizeof(g));
    std::printf("sizeof [&x, &d]   = %zu\n", sizeof(h));
    int (*fp)() = a;
    std::printf("fp()              = %d\n", fp());
}
```

- ★ 일곱 줄에 무엇이 찍히나?

### 7. ★★★ `[=]` 와 `this` (왜)

- ★★★ 2번의 `[=]` 가 멤버 `v` 를 쓸 때 실제로 캡처되는 것은 무엇인가 — 1번 격자의 어느 행과 같은 위험이고, C++20 은 이 꼴을 어떻게 취급하나?

### 8. ★★★ `std::function` 과 복사 (왜)

- ★★★ 4번의 두 래퍼가 그 람다를 다르게 다루는 까닭을 `unique_ptr` 부터 사슬로 말해 보라.

### 9. ★★ 경고 0 · ASan 침묵 (경계)

- ★★ 1번 같은 격자에서 어떤 칸이 경고 0 이고 `detect_stack_use_after_return=0` 인 판에서 리포트도 없다면, 그 칸은 「안전하다」고 말할 수 있나?

### 10. ★★ 참조 캡처의 크기 (경계)

- ★★ 6번의 `sizeof [&x]` 값으로 「참조 캡처는 포인터 하나로 저장된다」가 언어 보장이라고 말할 수 있나?

### 11. 다른 주제와 잇기 (연결)

- ★★ C# 의 `for` 루프에서 람다가 `3 3 3` 을 찍는 자리에서, C++ 의 `[&i]` 는 무엇을 하나(`loop01.cpp`)?
- ★★ Rust 는 1번의 「돌려준 뒤」 참조 캡처를 어느 단계에서 막나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
