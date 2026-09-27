# cpp/syntax/42 — 연관 컨테이너 — 정렬 vs 해시 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 「**정렬 쪽은 비교자 하나를, 해시 쪽은 `hash` 와 `==` 둘을 키에게 요구한다 — 빠지면 컴파일러가, 어기면 아무도 말해 주지 않는다**」 하나를 따라가는 것이다.
> **환경** — g++ 13.3.0 · g++-12 12.4.0 · clang 18.1.3 · libstdc++ 13(★ clang 도 같은 라이브러리) · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex`.
> ★★★ **이 주제의 본체는 커스텀 키 격자(1번)와 버킷 분포(5번)다** — 시간은 묻지 않는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 준 것 여섯 × 컨테이너 넷 (예측)

```cpp
/* key01.cpp */
// 커스텀 키 P 를 연관 컨테이너 넷(-DCONT=1..4)에 넣는다 — P 에 준 것은 여섯 가지(-DGIVE=1..6)
#include <compare>
#include <cstddef>
#include <cstdio>
#include <functional>
#include <map>
#include <set>
#include <unordered_map>
#include <unordered_set>

struct P {
    int x, y;
#if GIVE == 2
    bool operator<(const P& o) const { return x != o.x ? x < o.x : y < o.y; }
#elif GIVE == 3 || GIVE == 5
    bool operator==(const P& o) const { return x == o.x && y == o.y; }
#elif GIVE == 6
    auto operator<=>(const P&) const = default;
#endif
};

#if GIVE == 4 || GIVE == 5
template <> struct std::hash<P> {
    std::size_t operator()(const P& p) const noexcept { return std::hash<int>{}(p.x) * 31 + std::hash<int>{}(p.y); }
};
#endif

int main() {
#if CONT == 1
    std::set<P> c;
    c.insert(P{1, 2});
#elif CONT == 2
    std::map<P, int> c;
    c.emplace(P{1, 2}, 7);
#elif CONT == 3
    std::unordered_set<P> c;
    c.insert(P{1, 2});
#elif CONT == 4
    std::unordered_map<P, int> c;
    c.emplace(P{1, 2}, 7);
#endif
    std::printf("size %zu · find %d\n", c.size(), c.find(P{1, 2}) != c.end());
}
```

- ★★★ 24칸(`GIVE=1..6` × `CONT=1..4`)을 두 컴파일러로 빌드하면 어느 칸이 통과하나?
- ★★ 에러 칸의 첫 `error:` 줄은 `key01.cpp` 를 가리키나, 표준 헤더를 가리키나? 해시 쪽과 정렬 쪽이 다른가?

### 2. ★★ 같은 키 일곱의 순회 순서 (예측)

```cpp
/* order01.cpp */
// 같은 키 일곱을 같은 순서로 넣고 순회 순서를 찍는다 — map 과 unordered_map. bucket_count 도 찍는다
#include <cstdio>
#include <map>
#include <unordered_map>

int main() {
    const int keys[] = {50, 3, 17, 88, 1, 42, 29};
    std::map<int, int> m;
    std::unordered_map<int, int> u;
    for (int k : keys) { m[k] = 0; u[k] = 0; }
    std::printf("map          :");
    for (const auto& kv : m) std::printf(" %d", kv.first);
    std::printf("\nunordered_map:");
    for (const auto& kv : u) std::printf(" %d", kv.first);
    std::printf("\nunordered_map bucket_count = %zu\n", u.bucket_count());
}
```

- ★★ `map` 줄과 `unordered_map` 줄에 무엇이 찍히나?
- ★★ 컴파일러 셋(g++ 13 · clang 18 · g++-12) × `-O0`/`-O2` × 세 번 — 18 판에서 `unordered_map` 줄은 몇 가지가 나오나?

### 3. ★★★ 없는 키를 찾는 네 가지 (예측)

```cpp
/* sub01.cpp */
// map 에서 없는 키를 네 가지로 찾는다 — operator[] · at · find · contains. 매번 size 를 찍는다. -DCONSTMAP 이면 const map 에 []
#include <cstdio>
#include <map>
#include <stdexcept>
#include <string>

int main() {
    std::map<std::string, int> m{{"a", 1}};
#ifdef CONSTMAP
    const auto& cm = m;
    std::printf("%d\n", cm["zz"]);
#else
    std::printf("시작          size %zu\n", m.size());
    int v = m["b"];
    std::printf("m[\"b\"] 읽기   size %zu · 값 %d\n", m.size(), v);
    try {
        std::printf("%d\n", m.at("c"));
    } catch (const std::out_of_range& e) {
        std::printf("m.at(\"c\")     size %zu · out_of_range what() = %s\n", m.size(), e.what());
    }
    std::printf("m.find(\"d\")   size %zu · 찾았나 %d\n", m.size(), m.find("d") != m.end());
    std::printf("contains(\"e\") size %zu · 있나 %d\n", m.size(), m.contains("e"));
#endif
}
```

- ★★★ 다섯 줄의 `size` 는 각각 얼마인가? `at` 은 무엇을 찍나?
- ★★ `-DCONSTMAP` 판은 컴파일되나?

### 4. ★★ `<=` 비교자 (예측)

```cpp
/* swo01.cpp */
// 엄격 약순서를 어기는 비교자(<=) — 비교자 자체의 값을 찍고, set 에 같은 키를 두 번 넣고, 같은 비교자로 정렬한다
#include <algorithm>
#include <cstdio>
#include <set>
#include <vector>

struct LessEq {
    bool operator()(int a, int b) const { return a <= b; }
};

int main() {
    LessEq c;
    std::fprintf(stderr, "c(1, 1) = %d · 동치 판정 !c(1,1) && !c(1,1) = %d\n", c(1, 1), !c(1, 1) && !c(1, 1));
    std::set<int, LessEq> s;
    s.insert(1);
    s.insert(1);
    std::fprintf(stderr, "set 에 1 을 두 번 넣었다\n");
    std::vector<int> v{3, 1, 2, 1};
    std::sort(v.begin(), v.end(), LessEq{});
    std::fprintf(stderr, "sort 가 끝났다\n");
}
```

- ★★ 보통 빌드와 `-D_GLIBCXX_DEBUG` 빌드는 각각 몇 줄까지 찍고 어떻게 끝나나? 디버그 모드가 멈추는 자리는 `set` 인가 `sort` 인가?

### 5. ★★ 늘 0 인 해시 (예측)

```cpp
/* hash01.cpp */
// 1..1000 을 unordered_set 에 넣고 버킷 분포를 센다 — std::hash<int> 대 항상 0 을 돌려주는 해시
#include <cstddef>
#include <cstdio>
#include <unordered_set>

struct Zero {
    std::size_t operator()(int) const noexcept { return 0; }
};

template <class Set> void report(const char* name) {
    Set s;
    for (int i = 1; i <= 1000; ++i) s.insert(i);
    std::size_t used = 0, biggest = 0;
    for (std::size_t b = 0; b < s.bucket_count(); ++b) {
        std::size_t n = s.bucket_size(b);
        if (n > 0) ++used;
        if (n > biggest) biggest = n;
    }
    std::printf("%-15s size %zu · bucket_count %zu · 빈 아닌 버킷 %zu · 가장 큰 버킷 %zu · load_factor %.3f\n",
                name, s.size(), s.bucket_count(), used, biggest, s.load_factor());
}

int main() {
    report<std::unordered_set<int>>("std::hash<int>");
    report<std::unordered_set<int, Zero>>("Zero");
}
```

- ★★ 두 줄의 `bucket_count` · 빈 아닌 버킷 · 가장 큰 버킷 · `load_factor` 는?

### 6. ★★★ `hash` 없는 해시 컨테이너의 에러 자리 (왜)

- ★★★ 1번에서 `std::hash<P>` 를 안 준 해시 컨테이너는 `insert` 가 아니라 **선언 줄**에서 에러가 난다. 왜인가 — cppreference 의 어느 문장이 그것을 설명하나?

### 7. ★★ `hash` 만으로는 (왜)

- ★★ `std::hash<P>` 를 줬는데도 `==` 가 없으면 왜 해시 컨테이너가 안 되나? 정렬 컨테이너는 왜 `==` 없이 「같은 키」를 판정하나?

### 8. ★★★ 여러 판의 순회 순서 (경계)

- ★★★ 2번에서 `unordered_map` 순서가 18 판 내내 같았다면 「이 순서는 믿어도 된다」고 말할 수 있나? Go·Rust 는 같은 질문에 무엇을 보였나?

### 9. ★★ 적재율 (경계)

- ★★ 5번의 두 줄에서 `load_factor` 만 보고 해시의 좋고 나쁨을 가를 수 있나? 무엇을 봐야 하나?

### 10. ★★ `set` 과 디버그 모드 (경계)

- ★★ 4번에서 디버그 모드가 `set` 의 두 `insert` 에서 침묵했다면 「`set` 에 `<=` 를 써도 안전하다」고 말할 수 있나?

### 11. 다른 주제와 잇기 (연결)

- ★★ 5번의 bucket 수열(`bucket01.cpp`)에서 칸 수가 바뀌는 순간은 43번의 무효화 격자 어디와 이어지나?
- ★ 정렬 쪽의 원리(트리)와 해시 쪽의 원리(버킷 · 적재율 · 리사이즈)는 이 저장소의 어디가 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
