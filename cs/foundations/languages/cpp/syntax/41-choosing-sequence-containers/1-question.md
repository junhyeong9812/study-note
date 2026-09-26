# cpp/syntax/41 — 순차 컨테이너 선택 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 「**컨테이너를 고르는 것은 원소를 어디에 세워 두나 고르는 것이다 — 할당 · 연속 · 움직이나**」 하나를 따라가는 것이다.
> **환경** — g++ 13.3.0 · g++-12 12.4.0 · clang 18.1.3 · libstdc++ 13(★ clang 도 같은 라이브러리) · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex`.
> ★★★ **이 주제의 본체는 할당 계수기와 주소 비교(1번)다** — 시간은 묻지 않는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 원소 16 개를 넣을 때의 네 칸 (예측)

```cpp
/* seq01.cpp */
// 순차 컨테이너에 원소 N 개(기본 16)를 넣으며 센다(-DC=1..7) — operator new 횟수 · sizeof · 연속인가 · 처음 넣은 원소의 주소가 그대로인가
#include <array>
#include <cstdio>
#include <cstdlib>
#include <deque>
#include <forward_list>
#include <list>
#include <memory>
#include <new>
#include <vector>

static int g_news = 0;
void* operator new(std::size_t n) {
    ++g_news;
    if (void* p = std::malloc(n)) return p;
    throw std::bad_alloc{};
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

#ifndef N
#define N 16
#endif

// 이웃한 두 원소의 주소 차이가 원소 하나 크기인가 — 전 구간에서
template <class Cont> bool contiguous(Cont& c) {
    auto it = c.begin();
    const int* prev = std::addressof(*it);
    for (++it; it != c.end(); ++it) {
        const int* cur = std::addressof(*it);
        if (cur != prev + 1) return false;
        prev = cur;
    }
    return true;
}

int main() {
    int before = g_news;
#if C == 1 || C == 2
    std::vector<int> c;
#if C == 2
    c.reserve(N);
#endif
    c.push_back(0);
    const int* first = &c.front();
    for (int i = 1; i < N; ++i) c.push_back(i);
    bool kept = (first == &c.front());
#elif C == 3
    std::array<int, N> c{};
    const int* first = &c.front();
    for (int i = 0; i < N; ++i) c[i] = i;
    bool kept = (first == &c.front());
#elif C == 4 || C == 5
    std::deque<int> c;
    c.push_back(0);
    const int* first = &c.front();
    for (int i = 1; i < N; ++i) {
#if C == 4
        c.push_back(i);
#else
        c.push_front(i);
#endif
    }
#if C == 4
    bool kept = (first == &c.front());
#else
    bool kept = (first == &c.back());
#endif
#elif C == 6
    std::list<int> c;
    c.push_back(0);
    const int* first = &c.front();
    for (int i = 1; i < N; ++i) c.push_back(i);
    bool kept = (first == &c.front());
#elif C == 7
    std::forward_list<int> c;
    c.push_front(0);
    const int* first = &c.front();
    for (int i = 1; i < N; ++i) c.push_front(i);
    int last = 0;
    const int* lastp = nullptr;
    for (int& v : c) { last = v; lastp = &v; }
    (void)last;
    bool kept = (first == lastp);
#endif
    int news = g_news - before;
    std::printf("%zu\t%d\t%s\t%s\n", sizeof(c), news, contiguous(c) ? "예" : "아니오", kept ? "예" : "아니오");
}
```

- ★★★ 여덟 행(`vector` · `vector`+`reserve(16)` · `array` · `deque` 뒤 · `deque` 앞 · `deque` 뒤 ×200 · `list` · `forward_list`)에서 **`operator new` 횟수**는 각각 몇인가?
- ★★★ **「연속인가」** 와 **「처음 원소 주소가 그대로인가」** 가 「아니오」인 행은 어느 것인가?
- ★ `sizeof` 가 원소 수에 따라 커지는 것은 어느 것인가?

### 2. ★★ `capacity` 가 바뀌는 순간 (예측)

```cpp
/* capseq01.cpp */
// vector 에 하나씩 1000 개를 넣으며 capacity 가 바뀌는 순간만 찍는다
#include <cstdio>
#include <vector>

int main() {
    std::vector<int> v;
    std::printf("처음 capacity %zu\n", v.capacity());
    std::size_t last = v.capacity();
    int changes = 0;
    for (int i = 0; i < 1000; ++i) {
        v.push_back(i);
        if (v.capacity() != last) {
            std::printf("size %4zu 에서 capacity %4zu\n", v.size(), v.capacity());
            last = v.capacity();
            ++changes;
        }
    }
    std::printf("바뀐 횟수 %d\n", changes);
}
```

- ★★ 무엇이 찍히나 — 처음 capacity 와 바뀐 횟수는? g++ 13 · clang 18 · g++-12 세 판이 같은가?

### 3. ★★★ 세 타입의 재할당 (예측)

```cpp
/* mif01.cpp */
// std::move_if_noexcept 가 무엇을 돌려주나 · vector 재할당이 무엇으로 옮기나 — 타입 셋
#include <cstdio>
#include <type_traits>
#include <utility>
#include <vector>

struct NoexceptMove {
    NoexceptMove() = default;
    NoexceptMove(const NoexceptMove&) { std::printf("copy "); }
    NoexceptMove(NoexceptMove&&) noexcept { std::printf("move "); }
};
struct ThrowingMove {
    ThrowingMove() = default;
    ThrowingMove(const ThrowingMove&) { std::printf("copy "); }
    ThrowingMove(ThrowingMove&&) { std::printf("move "); }
};
struct MoveOnlyThrowing {                     // 복사가 없고 이동은 noexcept 가 아니다
    MoveOnlyThrowing() = default;
    MoveOnlyThrowing(const MoveOnlyThrowing&) = delete;
    MoveOnlyThrowing(MoveOnlyThrowing&&) { std::printf("move "); }
};

template <class T> void probe(const char* name) {
    T x;
    constexpr bool rv = std::is_rvalue_reference_v<decltype(std::move_if_noexcept(x))>;
    std::printf("%-17s nothrow_move=%d copyable=%d move_if_noexcept->%s | 재할당: ", name,
                (int)std::is_nothrow_move_constructible_v<T>, (int)std::is_copy_constructible_v<T>,
                rv ? "T&&" : "const T&");
    std::vector<T> v;
    v.reserve(2);
    v.emplace_back();
    v.emplace_back();
    v.emplace_back();                         // capacity 2 를 넘긴다 — 있던 둘을 옮긴다
    std::printf("\n");
}

int main() {
    probe<NoexceptMove>("NoexceptMove");
    probe<ThrowingMove>("ThrowingMove");
    probe<MoveOnlyThrowing>("MoveOnlyThrowing");
}
```

- ★★★ 세 줄의 `move_if_noexcept->` 칸과 `재할당:` 칸에 무엇이 찍히나?

### 4. ★★★ `deque` 의 「연속인가」 (경계)

- ★★★ 1번의 `deque push_back`(16 개) 행이 「연속인가 = 예」였다면, 「`deque` 는 원소를 연속으로 둔다」고 말할 수 있나? 무엇으로 반증하나?

### 5. ★★★ `capacity` 수열의 지위 (경계)

- ★★★ 2번의 수열로 「`std::vector` 는 용량을 두 배로 늘린다」를 표준 보장이라고 말할 수 있나? 표준이 `push_back` 에 대해 약속하는 것은 무엇인가?

### 6. ★★ 셋째 타입 (왜)

- ★★ 3번의 `MoveOnlyThrowing` 은 이동이 `noexcept` 가 아닌데도 재할당이 이동으로 간다. 왜인가 — 그 대가로 `vector` 가 잃는 것은 무엇인가?

### 7. ★★ `deque` 와 `vector` 의 주소 안정성 (왜)

- ★★ `deque` 는 `push_front` 를 해도 처음 원소의 주소가 그대로인데 `vector` 는 `push_back` 만 해도 바뀐다. 두 구조의 무엇이 그 차이를 만드나?

### 8. ★★ 기본값 (왜)

- ★★ 이 문서가 **결정적으로 보인 칸만으로** 「기본값이 `vector` 인 이유」를 세 가지 대 보라. 그리고 `vector` 를 버려야 하는 조건 하나는?

### 9. ★ 지역성 (경계)

- ★ 「연속인가 = 예」는 「캐시에 잘 맞는다」와 같은 말인가? 이 문서의 창이 못 보는 것은 무엇인가?

### 10. 다른 주제와 잇기 (연결)

- ★★ 17번 (3)이 이미 보인 것과 3번이 새로 보인 것은 각각 무엇인가?
- ★ Rust 38번은 `Vec` 의 배수에 대해 무엇이라고 결론 냈나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
