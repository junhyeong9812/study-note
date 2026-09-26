# cpp/syntax/40 — `std::function`·함수 객체·호출 가능 타입 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 「**여러 호출 가능을 한 자리로 받는 법이 셋(함수 포인터 · `std::function` · 템플릿)이고, 각자 받는 것과 치르는 값이 다르다**」 하나를 따라가는 것이다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · libstdc++ 13(★ clang 도 같은 라이브러리) · GNU objdump 2.42 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex`.
> ★★★ **이 주제의 본체는 할당 계수기(3번)와 역어셈블(4번)이다** — 시간은 묻지 않는다. 묻는 것은 **`new` 가 몇 번인가 · 간접 분기가 남았나**다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 호출 가능 일곱 × 받는 자리 넷 (예측)

```cpp
/* hold01.cpp */
// 호출 가능 일곱(-DCALLABLE=1..7) × 받는 자리 넷(-DRECV=1..4). 서명은 모두 int(Obj&, int)
#include <cstdio>
#include <functional>
#include <memory>
#include <utility>

struct Obj {
    int base = 1;
    int add(int x) { return base + x; }
};
int add_free(Obj& o, int x) { return o.base + x; }
struct Adder {
    int operator()(Obj& o, int x) const { return o.base + x; }
};

using FnPtr = int (*)(Obj&, int);
int recv_ptr(FnPtr f, Obj& o, int x) { return f(o, x); }
int recv_function(std::function<int(Obj&, int)> f, Obj& o, int x) { return f(o, x); }
template <class F> int recv_template(F&& f, Obj& o, int x) { return f(o, x); }
template <class F> int recv_invoke(F&& f, Obj& o, int x) { return std::invoke(std::forward<F>(f), o, x); }

int main() {
    Obj o;
    int k = 1;
    auto p = std::make_unique<int>(1);
    (void)k; (void)p;
#if CALLABLE == 1
    auto c = &add_free;
#elif CALLABLE == 2
    auto c = [](Obj& ob, int x) { return ob.base + x; };
#elif CALLABLE == 3
    auto c = [k](Obj& ob, int x) { return ob.base + x + k - 1; };
#elif CALLABLE == 4
    auto c = Adder{};
#elif CALLABLE == 5
    auto c = &Obj::add;
#elif CALLABLE == 6
    auto c = std::bind(add_free, std::placeholders::_1, std::placeholders::_2);
#elif CALLABLE == 7
    auto c = [q = std::move(p)](Obj& ob, int x) { return ob.base + x + *q - 1; };
#endif
#if RECV == 1
    std::printf("%d\n", recv_ptr(std::move(c), o, 41));
#elif RECV == 2
    std::printf("%d\n", recv_function(std::move(c), o, 41));
#elif RECV == 3
    std::printf("%d\n", recv_template(std::move(c), o, 41));
#elif RECV == 4
    std::printf("%d\n", recv_invoke(std::move(c), o, 41));
#endif
}
```

- ★★★ 28칸(`CALLABLE=1..7` × `RECV=1..4`)을 두 컴파일러로 빌드하면, 받는 자리마다 몇 가지가 컴파일되나? 어느 칸이 막히나?
- ★★ 두 컴파일러가 서로 다른 칸에서 막히는 행이 있나?

### 2. ★★ 막힌 두 칸의 첫 에러 (예측)

- ★★ 1번의 `CALLABLE=3 RECV=1`(캡처 있는 람다 → 함수 포인터)과 `CALLABLE=5 RECV=3`(멤버 함수 포인터 → 템플릿)에서, 첫 `error:` 줄이 가리키는 곳은 각각 **호출 줄**인가 **템플릿 몸통**인가?

### 3. ★★★ `std::function` 에 담을 때의 `new` 횟수 (예측)

```cpp
/* sbo01.cpp */
// std::function 에 담을 때 operator new 가 몇 번 불리나 — 담는 것의 크기와 종류를 바꿔 가며 센다
#include <array>
#include <cstdio>
#include <cstdlib>
#include <functional>
#include <new>
#include <type_traits>

static int g_news = 0;
void* operator new(std::size_t n) {
    ++g_news;
    if (void* p = std::malloc(n)) return p;
    throw std::bad_alloc{};
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

struct Loud {                       // 8 바이트 · 복사 생성자를 직접 썼다
    long v = 1;
    Loud() = default;
    Loud(const Loud& o) : v(o.v) {}
};
int plain(int x) { return x + 1; }

template <class F>
void row(const char* name, F f) {
    int before = g_news;
    std::function<int(int)> fn = f;
    int made = g_news - before;
    before = g_news;
    std::function<int(int)> copy = fn;
    int copied = g_news - before;
    std::printf("%s\t%zu\t%d\t%d\t%d\t%d\n",
                name, sizeof(F), (int)std::is_trivially_copyable_v<F>, made, copied, copy(1));
}

int main() {
    std::printf("sizeof(std::function<int(int)>) = %zu\n", sizeof(std::function<int(int)>));
    std::printf("담는 것\tsizeof\ttrivially_copyable\tnew(담기)\tnew(복사)\tcall\n");
    std::array<char, 8> a8{};
    std::array<char, 16> a16{};
    std::array<char, 17> a17{};
    std::array<char, 24> a24{};
    std::array<char, 64> a64{};
    Loud loud;
    auto big = [a64](int x) { return x + a64[0] + 1; };
    row("함수 포인터", &plain);
    row("캡처 없는 람다", [](int x) { return x + 1; });
    row("캡처 8 바이트", [a8](int x) { return x + a8[0] + 1; });
    row("캡처 16 바이트", [a16](int x) { return x + a16[0] + 1; });
    row("캡처 17 바이트", [a17](int x) { return x + a17[0] + 1; });
    row("캡처 24 바이트", [a24](int x) { return x + a24[0] + 1; });
    row("캡처 64 바이트", big);
    row("캡처 Loud(8 바이트)", [loud](int x) { return x + (int)loud.v; });
    row("std::ref(64 바이트 람다)", std::ref(big));
}
```

- ★★★ `sizeof(std::function<int(int)>)` 는? 아홉 행 중 `new(담기)` 가 0 이 아닌 행은 어느 것인가?
- ★★ `new(복사)` 는 `new(담기)` 와 같은가?
- ★ `-O0`·`-O2` 와 두 컴파일러, 네 판에서 이 숫자들이 갈리나?

### 4. ★★★ `-O2` 에서 간접 분기가 남는 함수 (예측)

```cpp
/* ind01.cpp */
// 같은 「두 배」를 세 가지 자리로 받는다 — 템플릿 · std::function · 함수 포인터. -O2 -c 로 빌드해 역어셈블한다
#include <functional>

template <class F> int apply_tpl(F&& f, int x) { return f(x); }

int use_tpl(int x) { return apply_tpl([](int v) { return v * 2; }, x); }
int use_function(const std::function<int(int)>& f, int x) { return f(x); }
int use_ptr(int (*f)(int), int x) { return f(x); }
int use_local(int x) {
    std::function<int(int)> f = [](int v) { return v * 2; };
    return f(x);
}
```

- ★★★ `g++ -std=c++20 -O2 -c ind01.cpp` 를 `objdump -dr` 로 보면, 네 함수 중 몸통에 `call *` 또는 `jmp *` 가 남는 것은 어느 것인가? clang 은?
- ★★ `std::__throw_bad_function_call` 은 어느 함수에 보이나 — `-d` 만으로도 그 이름이 보이나?

### 5. ★★ 비어 있는 `std::function` 을 부르면 (예측)

```cpp
/* empty01.cpp */
// 비어 있는 std::function 을 부르면 — 기본은 잡아서 찍고, -DUNCAUGHT 이면 잡지 않는다. 찍는 것은 표준 오류로
#include <cstdio>
#include <functional>

int main() {
    std::function<int(int)> f;
    std::fprintf(stderr, "bool(f) = %d\n", static_cast<bool>(f));
#ifdef UNCAUGHT
    return f(1);
#else
    try {
        f(1);
    } catch (const std::bad_function_call& e) {
        std::fprintf(stderr, "잡은 예외 what() = %s\n", e.what());
    }
    f = nullptr;
    std::fprintf(stderr, "nullptr 대입 후 bool(f) = %d\n", static_cast<bool>(f));
#endif
}
```

- ★★ 기본 판과 `-DUNCAUGHT` 판은 각각 무엇을 찍고 종료 코드는 무엇인가?

### 6. ★★★ 멤버 함수 포인터를 받는 자리 (왜)

- ★★★ `std::function` 과 `std::invoke` 는 멤버 함수 포인터를 받는데, `f(o, x)` 로 부르는 템플릿은 왜 못 받나? 그 템플릿을 7 / 7 로 만들려면 몸통을 어떻게 바꾸나?

### 7. ★★ `Loud` 행 (왜)

- ★★ 3번의 `Loud` 캡처는 16 바이트보다 작은데 왜 `new` 가 1 회인가 — 이 판의 libstdc++ 는 무엇을 보고 안쪽 칸에 넣을지를 정하나?

### 8. ★★★ 문턱은 누구의 것인가 (경계)

- ★★★ 3번의 결과로 「`std::function` 은 16 바이트 이하의 람다에 힙을 쓰지 않는다」를 **언어 보장**이라고 말할 수 있나? 이 표 중 **보장인 행**은 어느 것인가?

### 9. ★★ `use_local` 의 관찰 (경계)

- ★★ 4번의 `use_local` 결과로 「`std::function` 은 인라인된다」라고 말할 수 있나? 어떤 조건이 바뀌면 이 관찰이 무너질 수 있나?

### 10. ★★ 「느리다」 (경계)

- ★★ 이 문서의 블록만으로 「`std::function` 은 템플릿보다 느리다」를 말할 수 있나? 이 문서가 대신 센 것은 무엇인가?

### 11. 다른 주제와 잇기 (연결)

- ★★ C 식 `void (*cb)(int, void*)` 콜백과 `std::function<void(int)>` 콜백은 **상태를 어디에 두나**(`ctx01.cpp`)? C 식 자리에 들어갈 수 있는 람다는 어떤 것인가?
- ★ Rust 에서 「갈래마다 다른 클로저」를 한 타입으로 돌려줄 때 쓰는 것은 C++ 의 무엇에 해당하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
