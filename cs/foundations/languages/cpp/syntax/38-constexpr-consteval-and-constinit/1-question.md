# cpp/syntax/38 — `constexpr` · `consteval` · `constinit` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 「**컴파일 시간 평가를 강제하는 것은 함수 표시가 아니라 부르는 자리다**」 하나를 칸마다 따라가는 것이다.
> **환경** — g++ 13.3.0 · g++-12 12.4.0 · clang 18.1.3 · libstdc++ 13(g++-12 는 12) · GNU objdump·nm 2.42 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex`.
> ★★★ **이 주제의 본체는 두 컴파일러의 에러(1\~6번)와 역어셈블·기호표(1·5번)다.**
> ★★★ **시간은 한 번도 재지 않았다** — 「빠르다」를 묻는 질문은 없다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 함수 셋 × 부르는 자리 다섯 (예측)

```cpp
/* cx01.cpp */
// 함수 셋(-DFN=1 constexpr · 2 consteval · 3 보통) × 부르는 자리 다섯(-DSITE=1..5)
template <int N> struct Tag {
    static constexpr int value = N;
};

#if FN == 1
constexpr int sq(int x) { return x * x; }
#elif FN == 2
consteval int sq(int x) { return x * x; }
#elif FN == 3
int sq(int x) { return x * x; }
#endif

int probe([[maybe_unused]] int n) {
#if SITE == 1
    constexpr int v = sq(7);
    return v;
#elif SITE == 2
    static_assert(sq(7) == 49);
    return 0;
#elif SITE == 3
    return sq(n);
#elif SITE == 4
    return Tag<sq(7)>::value;
#elif SITE == 5
    int v = sq(7);
    return v;
#endif
}

int main(int argc, char**) { return probe(argc) == 49; }
```

- ★★★ `-DFN=1..3` × `-DSITE=1..5` 의 15칸을 `-O0` 으로 컴파일하면 어느 칸이 에러인가?
- ★★★ 통과한 칸에서 `probe(int)` 의 역어셈블에 `sq` 호출이 남는 칸은 어디인가 — 두 컴파일러가 갈리는 칸이 있나?

### 2. ★★ 넓어진 것 넷 × 판 둘 (예측)

```cpp
/* cx20.cpp */
// C++20 에서 넓어진 것 넷 — -DCASE=1..4 로 하나만 켠다. 전부 상수 평가(static_assert) 안에서 쓴다
#include <vector>

#if CASE == 1
struct Shape {
    virtual constexpr int sides() const { return 0; }
};
struct Tri : Shape {
    constexpr int sides() const override { return 3; }
};
constexpr int count() {
    Tri t;
    const Shape& s = t;
    return s.sides();
}
#elif CASE == 2
constexpr int count() {
    int* p = new int(3);
    int v = *p;
    delete p;
    return v;
}
#elif CASE == 3
constexpr int count() {
    std::vector<int> v{1, 2, 3};
    return static_cast<int>(v.size());
}
#elif CASE == 4
constexpr int count() {
    try {
        return 3;
    } catch (...) {
        return 0;
    }
}
#endif

static_assert(count() == 3);
int main() {}
```

- ★★ `-DCASE=1..4` 를 `-std=c++17` 과 `-std=c++20` 으로 컴파일하면 각각 통과 · 경고 · 에러 중 무엇인가?

### 3. ★★★ 상수 평가 안의 `new` (예측)

```cpp
/* leak01.cpp */
// 상수 평가 안의 new — delete 를 빼먹은 판
constexpr int count() {
    int* p = new int(3);
    return *p;
}

static_assert(count() == 3);
int main() {}
```

- ★★★ 컴파일되나 — 안 되면 진단은 어느 줄을 가리키나?

### 4. ★★★ 넘침 — 상수 평가와 런타임 (예측)

```cpp
/* ub01.cpp */
// 부호 있는 덧셈 — 상수 평가(-DCONST) 대 런타임. 런타임 판은 값을 찍지 않고 다 돌았다는 표시만 찍는다
#include <climits>
#include <cstdio>

constexpr int add(int a, int b) { return a + b; }

int main([[maybe_unused]] int argc, char**) {
#ifdef CONST
    constexpr int v = add(INT_MAX, 1);
    return v;
#else
    volatile int v = add(INT_MAX, argc);
    (void)v;
    std::fprintf(stderr, "done\n");
#endif
}
```

- ★★★ `-DCONST` 는 컴파일되나?
- ★★ `-DCONST` 없이 컴파일해 돌리면 무엇이 찍히고 종료 코드는? `-fsanitize=undefined` 를 붙이면?

### 5. ★★ 전역 초기화 세 모양 (예측)

```cpp
/* cinit01.cpp */
// 전역 변수 초기화 세 모양 — constinit + 상수 식(기본) · constinit + 보통 함수(-DDYNAMIC) · constinit 없이 보통 함수(-DPLAIN)
#include <cstdio>

constexpr int base() { return 40; }
int runtime_base() { return 40; }

#if defined(DYNAMIC)
constinit int counter = runtime_base();
#elif defined(PLAIN)
int counter = runtime_base();
#else
constinit int counter = base();
#endif

int main() {
    counter += 2;
    std::printf("%d\n", counter);
}
```

- ★★ 기본 · `-DDYNAMIC` · `-DPLAIN` 중 컴파일되는 것은? 되는 판에서 `nm -C` 가 `counter` 에 붙이는 글자와 초기화 함수 기호의 유무는?

### 6. ★ `if consteval` (예측)

```cpp
/* ifcv01.cpp */
// if consteval(C++23) — 같은 함수를 상수 평가와 런타임에서 부른다
#include <cstdio>

constexpr int where() {
    if consteval {
        return 1;
    } else {
        return 2;
    }
}

int main() {
    constexpr int a = where();
    int b = where();
    std::printf("%d %d\n", a, b);
}
```

- ★ `-std=c++23` 으로 돌리면 무엇을 찍나? `-std=c++20` 으로는?

### 7. ★★★ 런타임 인자 칸 (왜)

- ★★★ 1번의 런타임 인자 칸(`sq(n)`)에서 `constexpr` 함수와 `consteval` 함수는 각각 어떻게 다뤄지나 — 왜 그렇게 갈리나?

### 8. ★★★ `-O2` 의 상수 (경계)

- ★★★ `-O2` 로 1번 격자를 다시 돌려 보통 함수의 `int v = sq(7)` 칸에서도 상수 49 가 보였다면, 그것으로 「컴파일 시간 계산이 일어났다」를 말할 수 있나?

### 9. ★★ 두 컴파일러가 갈린 칸 (경계)

- ★★ 1번에서 두 컴파일러가 갈린 칸이 있었다면 어느 쪽이 표준을 어긴 것인가 — 그 칸은 어떤 자리인가?

### 10. ★★ 경고 한 줄과 `exit 0` (경계)

- ★★ 2번의 어떤 칸이 `-std=c++17` 인데 경고 한 줄만 내고 `exit 0` 이었다면, 그 코드는 C++17 코드인가 — 무엇으로 확인하나?

### 11. 다른 주제와 잇기 (연결)

- ★★ Rust 의 `const fn` 은 1번의 `constexpr` 함수와 어떤 점에서 같은 모양인가?
- ★★ 4번의 런타임 판을 30편의 방식으로 물으면 무엇이 달라지나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
