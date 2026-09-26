# cpp/syntax/43 — 이터레이터 범주와 무효화 규칙 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 「**무효화 규칙은 표가 정하고, 무효가 된 것을 쓰면 UB 라 도구가 말해 줘야 한다 — 그런데 도구마다 보는 자리가 다르다**」 하나를 따라가는 것이다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · libstdc++ 13(★ clang 도 같은 라이브러리 — `_GLIBCXX_DEBUG` 는 한 검사기) · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex`. ASan 은 `-O0 -fsanitize=address -g`.
> ★★★ **이 주제의 본체는 `_GLIBCXX_DEBUG` 와 ASan(1번)이다** — 무효가 된 것을 쓴 칸의 **값은 UB 의 한 결과라 묻지 않는다.** 묻는 것은 **명세가 무효라고 하나 · 도구가 잡나**다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 컨테이너 다섯 × 연산 일곱 (예측)

```cpp
/* inv01.cpp */
// 무효화 탐침 — ./a.out <컨테이너 1..5> <연산 1..7>. 원소 0 1 2 3 을 넣고 「2」를 가리키는 이터레이터와 참조를 잡은 뒤
// 연산을 하나 하고, -DUSE_ITER 이면 이터레이터를, 아니면 참조를 쓴다. 찍는 것은 표준 오류로
#include <cstdio>
#include <cstdlib>
#include <deque>
#include <iterator>
#include <list>
#include <map>
#include <unordered_map>
#include <vector>

[[noreturn]] void not_applicable() { std::fprintf(stderr, "부적용\n"); std::exit(3); }

template <class Seq> int probe_seq(int op, bool is_vector) {
    Seq c;
    if constexpr (requires { c.reserve(1); }) c.reserve(op == 2 ? 4 : 8);
    for (int i = 0; i < 4; ++i) c.push_back(i);
    auto it = std::next(c.begin(), 2);
    int& r = *it;
    (void)r;
    switch (op) {
    case 1: c.push_back(9); break;                                   // 끝에 추가 — 용량 안
    case 2: if (!is_vector) not_applicable(); c.push_back(9); break;  // 끝에 추가 — 용량 초과
    case 3: c.insert(std::next(c.begin()), 9); break;                // 가운데 삽입 — 잡은 원소 앞
    case 4: c.erase(c.begin()); break;                               // 첫 원소 지우기 — 잡은 원소 앞
    case 5: c.erase(std::prev(c.end())); break;                      // 마지막 원소 지우기 — 잡은 원소 뒤
    case 6: if constexpr (requires { c.reserve(1); }) c.reserve(100); else not_applicable(); break;
    case 7: c.clear(); break;
    }
#ifdef USE_ITER
    return *it;
#else
    return r;
#endif
}

template <class Map> int probe_map(int op, bool is_unordered) {
    Map c;
    if constexpr (requires { c.rehash(1); }) { if (op != 2) c.reserve(100); }
    for (int i = 0; i < 4; ++i) c.emplace(i, i);
    auto it = c.find(2);
    int& r = it->second;
    (void)r;
    switch (op) {
    case 1: c.emplace(10, 10); break;
    case 2:
        if (!is_unordered) not_applicable();
        if constexpr (requires { c.bucket_count(); }) {
            auto b = c.bucket_count();
            for (int k = 10; c.bucket_count() == b; ++k) c.emplace(k, k);   // rehash 가 일어날 때까지 넣는다
            std::fprintf(stderr, "bucket_count %zu -> %zu\n", b, c.bucket_count());
        }
        break;
    case 3: not_applicable();
    case 4: c.erase(0); break;
    case 5: c.erase(3); break;
    case 6:
        if constexpr (requires { c.rehash(1); }) {
            auto b = c.bucket_count();
            c.rehash(1000);
            std::fprintf(stderr, "bucket_count %zu -> %zu\n", b, c.bucket_count());
        } else not_applicable();
        break;
    case 7: c.clear(); break;
    }
#ifdef USE_ITER
    return it->second;
#else
    return r;
#endif
}

int main(int argc, char** argv) {
    if (argc != 3) return 2;
    int cont = std::atoi(argv[1]), op = std::atoi(argv[2]);
    int v = 0;
    switch (cont) {
    case 1: v = probe_seq<std::vector<int>>(op, true); break;
    case 2: v = probe_seq<std::deque<int>>(op, false); break;
    case 3: v = probe_seq<std::list<int>>(op, false); break;
    case 4: v = probe_map<std::map<int, int>>(op, false); break;
    case 5: v = probe_map<std::unordered_map<int, int>>(op, true); break;
    }
    std::fprintf(stderr, "썼다\n");
    return v == 2 ? 0 : 1;
}
```

- ★★★ 35 칸(`./a.out 1..5 1..7`) 중 부적용이 아닌 칸에서, **명세상 이터레이터가 무효인 칸**과 **참조가 무효인 칸**은 각각 어느 것인가? 두 수가 다른 까닭이 되는 칸은?
- ★★★ `-D_GLIBCXX_DEBUG -DUSE_ITER` 빌드가 **명세와 다르게 답하는 칸**이 있나? ASan 빌드(참조를 씀)는?
- ★★ `-D_GLIBCXX_SANITIZE_VECTOR` 를 더한 ASan 빌드는 어느 칸을 더 잡나?

### 2. ★★★ 돌면서 짝수 지우기 (예측)

```cpp
/* erase01.cpp */
// 순회 중 짝수 지우기 — 네 꼴(-DFORM=1..4)과 map 한 꼴(-DFORM=5). 결과와 크기를 표준 오류로 찍는다
#include <algorithm>
#include <cstdio>
#include <map>
#include <vector>

int main() {
#if FORM == 5
    std::map<int, int> m{{1, 1}, {2, 2}, {3, 3}, {4, 4}, {5, 5}, {6, 6}};
    for (auto it = m.begin(); it != m.end();) {
        if (it->first % 2 == 0) it = m.erase(it);
        else ++it;
    }
    for (const auto& kv : m) std::fprintf(stderr, "%d ", kv.first);
    std::fprintf(stderr, "| size %zu\n", m.size());
#else
    std::vector<int> v{1, 2, 3, 4, 5, 6};
#if FORM == 1
    for (auto it = v.begin(); it != v.end(); ++it)          // 지운 뒤에도 ++it
        if (*it % 2 == 0) v.erase(it);
#elif FORM == 2
    for (auto it = v.begin(); it != v.end();) {             // erase 가 돌려준 것을 받는다
        if (*it % 2 == 0) it = v.erase(it);
        else ++it;
    }
#elif FORM == 3
    v.erase(std::remove_if(v.begin(), v.end(), [](int x) { return x % 2 == 0; }), v.end());
#elif FORM == 4
    auto n = std::erase_if(v, [](int x) { return x % 2 == 0; });
    std::fprintf(stderr, "erase_if 가 돌려준 수 %zu\n", n);
#endif
    for (int x : v) std::fprintf(stderr, "%d ", x);
    std::fprintf(stderr, "| size %zu\n", v.size());
#endif
}
```

- ★★★ `FORM=1` 을 `-D_GLIBCXX_DEBUG` 로 돌리면 무엇이 찍히고 종료 코드는? 같은 꼴을 ASan 으로 돌리면 리포트 이름과 `파일:줄` 은?
- ★★ `FORM=2..5` 는 각각 무엇을 찍나?

### 3. ★★★ 범위 `for` 안의 `push_back` (예측)

```cpp
/* rfor01.cpp */
// 범위 기반 for 안에서 같은 vector 에 push_back — 처음 원소 셋, capacity 3
#include <cstdio>
#include <vector>

int main() {
    std::vector<int> v{1, 2, 3};
    std::fprintf(stderr, "capacity %zu\n", v.capacity());
    for (int x : v) {
        if (x == 1) v.push_back(4);
        std::fprintf(stderr, "x = %d\n", x);
    }
    std::fprintf(stderr, "size %zu\n", v.size());
}
```

- ★★★ ASan 빌드는 몇 줄을 찍은 뒤 어떤 리포트로 멈추나? `freed by` 사슬에는 어느 함수가 보이나?
- ★★ `-D_GLIBCXX_DEBUG` 빌드의 `Error:` 줄은?

### 4. ★★ 컨테이너별 이터레이터 컨셉 (예측)

```cpp
/* cat01.cpp */
// 컨테이너마다 이터레이터가 어느 컨셉(C++20)을 만족하나 — 1 은 만족, 0 은 아님
#include <array>
#include <cstdio>
#include <deque>
#include <forward_list>
#include <iterator>
#include <list>
#include <map>
#include <unordered_map>
#include <vector>

template <class C> void row(const char* name) {
    using It = typename C::iterator;
    std::printf("%s\t%d\t%d\t%d\t%d\n", name, (int)std::forward_iterator<It>, (int)std::bidirectional_iterator<It>,
                (int)std::random_access_iterator<It>, (int)std::contiguous_iterator<It>);
}

int main() {
    std::printf("컨테이너\tforward\tbidirectional\trandom_access\tcontiguous\n");
    row<std::array<int, 4>>("array");
    row<std::vector<int>>("vector");
    row<std::deque<int>>("deque");
    row<std::list<int>>("list");
    row<std::forward_list<int>>("forward_list");
    row<std::map<int, int>>("map");
    row<std::unordered_map<int, int>>("unordered_map");
}
```

- ★★ 일곱 행의 네 열에 무엇이 찍히나?

### 5. ★★★ `list` 를 정렬하는 세 꼴 (예측)

```cpp
/* sort01.cpp */
// list 를 정렬하는 세 꼴(-DFORM=1..3)과 deque 를 std::sort 로(-DFORM=4). 결과를 찍는다
#include <algorithm>
#include <cstdio>
#include <deque>
#include <list>

int main() {
#if FORM == 4
    std::deque<int> c{3, 1, 2};
#else
    std::list<int> c{3, 1, 2};
#endif
#if FORM == 1
    std::sort(c.begin(), c.end());
#elif FORM == 2
    std::ranges::sort(c);
#elif FORM == 3
    c.sort();
#elif FORM == 4
    std::sort(c.begin(), c.end());
#endif
    for (int x : c) std::printf("%d ", x);
    std::printf("\n");
}
```

- ★★★ `FORM=1..4` 중 컴파일이 안 되는 것은? 그 첫 `error:` 줄은 `sort01.cpp` 의 호출 줄을 가리키나?

### 6. ★★★ 두 가지 rehash (왜)

- ★★★ 1번의 `unordered_map` 에서 **넣다가 일어난 rehash** 와 **`rehash(1000)` 직접 호출**은 명세상 둘 다 이터레이터를 무효로 만든다. 디버그 모드가 한쪽만 잡았다면 그 침묵을 어떻게 읽어야 하나?

### 7. ★★★ 가운데 삽입 뒤의 참조와 ASan (왜)

- ★★★ `vector` 가운데 삽입 뒤의 참조는 명세상 무효인데 ASan 이 침묵한다. 왜인가 — ASan 은 무엇을 보는 도구인가?

### 8. ★★ `erase` 의 반환값 (왜)

- ★★ `it = v.erase(it)` 꼴이 `v.erase(it); ++it;` 와 달리 안전한 까닭은? `std::remove_if` 만으로는 왜 크기가 안 줄어드나?

### 9. ★★ 두 에러의 자리 (경계)

- ★★ 5번에서 `std::sort(list)` 와 `std::ranges::sort(list)` 는 에러가 가리키는 자리가 다르다. 그 차이를 만드는 것은 무엇인가?

### 10. ★★ 도구가 침묵한 칸 (경계)

- ★★ 1번에서 무효가 된 참조를 읽었는데 **ASan 도 침묵하고 값도 우연히 맞았다**면, 그 칸은 「이 판에서는 안전하다」고 말할 수 있나?

### 11. 다른 주제와 잇기 (연결)

- ★★ 2번의 틀린 꼴을 Rust · Java · C# 에서 쓰면 각각 어느 단계에서 무엇이 막나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
