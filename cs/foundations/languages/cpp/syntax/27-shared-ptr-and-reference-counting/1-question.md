# cpp/syntax/27 — `shared_ptr` 와 참조 계수 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「장부(제어 블록)에 지금 몇 줄이 적혀 있나」를 맞히는 것**이 절반이다 — 「스마트 포인터가 알아서 지운다」로 뭉개지 말고
> **강한 계수와 약한 계수가 각각 언제 0 이 되나**를 따라가야 한다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · libstdc++ 13 · x86-64 Linux · 대비 rustc 1.92.0 · Python 3.12.3.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 본체는 「할당 계수기」다**(1·4번) — 전역 `operator new`/`delete` 를 가로챘다. ★★ 짝은 **ASan(3번)과 `-O2` 어셈블리(6번).**
> ★ **「부적용인 창」이 있다** — 경고 격자. 순환도 원자 비용도 **규칙대로 된 코드**다. ★ **시간은 한 번도 재지 않았다.**
> ★★★ **20편이 잰 것은 다시 묻지 않는다** — 가상 소멸자 없이 `~Derived` · `_Sp_counted_ptr<Base*>` · `sizeof` 16 대 8.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 전역 `operator new` 를 가로채 다섯 가지 만드는 법을 센다 (예측)

```cpp
/* sptr01.cpp */
// 전역 operator new 를 가로채 할당 횟수를 센다 — make_shared 대 shared_ptr(new T) 대 unique_ptr
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <new>

static int allocs = 0;
static std::size_t bytes = 0;

void* operator new(std::size_t n) {
    ++allocs; bytes += n;
    if (void* p = std::malloc(n)) return p;
    throw std::bad_alloc();
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

struct T { long a = 1, b = 2; };           // 16바이트

template <class F>
void count(const char* label, F make) {
    allocs = 0; bytes = 0;
    {
        auto p = make();
        std::printf("%-34s 할당 %d회 · %2zu바이트\n", label, allocs, bytes);
    }
}

int main() {
    std::printf("sizeof(T) = %zu\n", sizeof(T));
    count("(1) std::make_shared<T>()",        [] { return std::make_shared<T>(); });
    count("(2) std::shared_ptr<T>(new T)",    [] { return std::shared_ptr<T>(new T); });
    count("(3) std::make_unique<T>()",        [] { return std::make_unique<T>(); });
    count("(4) std::shared_ptr<T>(make_unique)", [] { return std::shared_ptr<T>(std::make_unique<T>()); });
    count("(5) 복사 한 번 더",                 [] { auto a = std::make_shared<T>(); auto b = a; return b; });
}
```

- ★★★ `(1)`\~`(5)` 각각의 **할당 횟수와 바이트**는?
- ★★ `(1)` 과 `(2)` 의 바이트 차이는 **무엇의 크기**인가?
- ★ `-O2` 나 clang 으로 바꾸면 수가 움직이나?

### 2. ★★ `use_count()` 를 한 줄씩 찍는다 (예측)

```cpp
/* sptr02.cpp */
// use_count() 가 어느 동작에서 움직이나 — 한 줄씩 찍는다
#include <cstdio>
#include <memory>
#include <utility>

struct T { ~T() { std::printf("      ~T\n"); } };

int main() {
    auto a = std::make_shared<T>();
    std::printf("(1) auto a = make_shared<T>()        a.use_count()=%ld\n", a.use_count());
    auto b = a;
    std::printf("(2) auto b = a                        a.use_count()=%ld\n", a.use_count());
    auto c = std::move(b);
    std::printf("(3) auto c = std::move(b)             a.use_count()=%ld · b 가 비었나 %d\n", a.use_count(), (int)(b == nullptr));
    std::weak_ptr<T> w = a;
    std::printf("(4) weak_ptr<T> w = a                 a.use_count()=%ld · w.use_count()=%ld\n", a.use_count(), w.use_count());
    {
        auto l = w.lock();
        std::printf("(5) auto l = w.lock()   (블록 안)     a.use_count()=%ld\n", a.use_count());
    }
    std::printf("(6) l 이 블록을 나간 뒤               a.use_count()=%ld\n", a.use_count());
    const auto& r = a;
    std::printf("(7) const auto& r = a                 a.use_count()=%ld\n", r.use_count());
    c.reset();
    std::printf("(8) c.reset()                         a.use_count()=%ld\n", a.use_count());
    a.reset();
    std::printf("(9) a.reset()                         w.use_count()=%ld · w.expired()=%d\n", w.use_count(), (int)w.expired());
    auto l2 = w.lock();
    std::printf("(10) auto l2 = w.lock()               l2 가 비었나 %d\n", (int)(l2 == nullptr));
}
```

- ★★ `(1)`\~`(8)` 의 `use_count()` 는 각각 얼마인가?
- ★★★ `~T` 는 **몇 번째 줄 뒤에** 찍히나 — 그때 `w` 는 아직 살아 있나?
- ★ `(10)` 의 `l2` 는 비었나?

### 3. ★★★ 부모와 자식이 서로를 `shared_ptr` 로 든다 (예측)

```cpp
/* sptr03.cpp */
// 부모와 자식이 서로를 가리킨다 — 기본은 둘 다 shared_ptr, -DASK_WEAK 이면 자식→부모를 weak_ptr 로
// 마커는 표준 오류로 찍는다 — sanitizer 가 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>
#include <memory>

struct Parent;
struct Child {
#ifdef ASK_WEAK
    std::weak_ptr<Parent>   parent;
#else
    std::shared_ptr<Parent> parent;
#endif
    ~Child() { std::fprintf(stderr, "      ~Child\n"); }
};
struct Parent {
    std::shared_ptr<Child> child;
    ~Parent() { std::fprintf(stderr, "      ~Parent\n"); }
};

__attribute__((noinline)) void link_pair() {
    auto p = std::make_shared<Parent>();
    auto c = std::make_shared<Child>();
    p->child = c;
    c->parent = p;
    std::fprintf(stderr, "(1) 서로 이은 직후  p.use_count()=%ld · c.use_count()=%ld\n", p.use_count(), c.use_count());
}

int main() {
    link_pair();
    std::fprintf(stderr, "(2) link_pair() 에서 돌아왔다\n");
}
```

- ★★ `(1)` 의 두 `use_count()` 는?
- ★★★ g++ + ASan 으로 돌리면 `~Parent`·`~Child` 가 찍히나 — ASan 은 **어떤 종류의 누수 몇 건**을 보고하나?
- ★★ `-DASK_WEAK` 판은?

### 4. ★★★ `weak_ptr` 하나가 남으면 메모리는 언제 풀리나 (예측)

```cpp
/* sptr06.cpp */
// weak_ptr 하나가 남으면 메모리는 언제 풀리나 — make_shared 판과 shared_ptr(new T) 판
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <new>

// 할당한 블록의 크기를 기억해 두었다가 해제할 때 몇 바이트가 돌아갔는지 센다
static void*       live_p[16];
static std::size_t live_n[16];
static int frees = 0;
static std::size_t freed = 0;

void* operator new(std::size_t n) {
    void* p = std::malloc(n);
    if (!p) throw std::bad_alloc();
    for (int i = 0; i < 16; ++i) if (!live_p[i]) { live_p[i] = p; live_n[i] = n; break; }
    return p;
}
void operator delete(void* p) noexcept {
    for (int i = 0; i < 16; ++i) if (live_p[i] == p) { ++frees; freed += live_n[i]; live_p[i] = nullptr; }
    std::free(p);
}
void operator delete(void* p, std::size_t) noexcept { operator delete(p); }

struct Big {
    char buf[1000] = {};
    ~Big() { std::printf("      ~Big\n"); }
};

static void report(const char* what) { std::printf("    %-24s 해제 %d회 · %4zu바이트\n", what, frees, freed); }

int main() {
    std::printf("(M) make_shared<Big>()\n");
    frees = 0; freed = 0;
    {
        std::weak_ptr<Big> w;
        {
            auto s = std::make_shared<Big>();
            w = s;
        }
        report("마지막 shared_ptr 이 죽었다");
    }
    report("weak_ptr 도 죽었다");

    std::printf("(N) shared_ptr<Big>(new Big)\n");
    frees = 0; freed = 0;
    {
        std::weak_ptr<Big> w;
        {
            std::shared_ptr<Big> s(new Big);
            w = s;
        }
        report("마지막 shared_ptr 이 죽었다");
    }
    report("weak_ptr 도 죽었다");
}
```

- ★★★ `(M)` 에서 **마지막 `shared_ptr` 가 죽은 직후**의 해제 횟수·바이트는 — `~Big` 은 이미 돌았나?
- ★★ `(N)` 에서는 같은 시점에 무엇이 풀리나?
- ★ 두 판의 **최종 합계 바이트**가 다른 이유는?

### 5. ★★ `shared_from_this()` 를 세 자리에서 부른다 (예측)

```cpp
/* sptr04.cpp */
// enable_shared_from_this — shared_ptr 가 맡은 객체와 안 맡은 객체에서 shared_from_this() 를 부른다
#include <cstdio>
#include <memory>

struct Job : std::enable_shared_from_this<Job> {
    std::shared_ptr<Job> self() { return shared_from_this(); }
};

int main() {
    auto owned = std::make_shared<Job>();
    auto again = owned->self();
    std::printf("(1) shared_ptr 가 맡은 객체   owned.use_count()=%ld · 같은 객체인가 %d\n",
                owned.use_count(), (int)(owned == again));

    Job local;
    std::printf("(2) 지역 변수에서 부른다\n");
    try {
        auto p = local.self();
        std::printf("    반환됨 p==nullptr %d\n", (int)(p == nullptr));
    } catch (const std::exception& e) {
        std::printf("    catch: %s\n", e.what());
    }

    Job* raw = new Job;
    std::printf("(3) new 로 만들고 아직 안 맡겼다\n");
    try {
        auto p = raw->self();
        std::printf("    반환됨 p==nullptr %d\n", (int)(p == nullptr));
    } catch (const std::exception& e) {
        std::printf("    catch: %s\n", e.what());
    }
    delete raw;

#if __cplusplus >= 201703L
    std::printf("(4) weak_from_this() — 안 맡긴 객체\n");
    std::printf("    expired=%d\n", (int)local.weak_from_this().expired());
#endif
}
```

- ★★ `(1)` 의 `use_count()` 는?
- ★★ `(2)`·`(3)` 에서는 무엇이 일어나나?
- ★★★ `-std=c++14` 로 던지면 `(2)`·`(3)` 의 결과가 바뀌나 — 바뀌지 않는다면 그것은 C++14 의 보장인가?

### 6. ★★★ 복사 대입 한 줄을 `-O2` 로 어셈블한다 (예측)

```cpp
/* sptr07.cpp */
// 복사·이동 한 번이 무슨 명령이 되나 — -DASK_SHARED · -DASK_UNIQUE · -DASK_RAW 로 한 함수만 남긴다
#include <memory>

#if defined(ASK_SHARED)
std::shared_ptr<int> keep;
void store(const std::shared_ptr<int>& p) { keep = p; }       // shared_ptr 복사 대입
#elif defined(ASK_UNIQUE)
std::unique_ptr<int> keep;
void store(std::unique_ptr<int>& p)       { keep = std::move(p); }  // unique_ptr 이동 대입
#elif defined(ASK_RAW)
int* keep;
void store(int* p)                         { keep = p; }       // 원시 포인터 복사
#endif
```

- ★★★ `SHARED` · `UNIQUE` · `RAW` 판의 **`lock` 접두 명령 수**는 각각 — 두 컴파일러에서 같은가?
- ★★ `lock` 명령 옆에 **같은 수만큼** 나오는 다른 것이 있나 — 그것은 무엇을 가르는가?

### 7. ★★ 멤버를 가리키는 `shared_ptr` (경계)

```cpp
/* sptr05.cpp */
// 별칭 생성자 — 멤버를 가리키는 shared_ptr 가 객체 전체를 살려 두나
#include <cstdio>
#include <memory>

struct Pair {
    int first = 1, second = 2;
    ~Pair() { std::printf("      ~Pair\n"); }
};

int main() {
    auto whole = std::make_shared<Pair>();
    std::shared_ptr<int> part(whole, &whole->second);      // 별칭 생성자
    std::printf("(1) part.get()==&whole->second %d · *part=%d · use_count=%ld\n",
                (int)(part.get() == &whole->second), *part, whole.use_count());
    whole.reset();
    std::printf("(2) whole.reset() 뒤  *part=%d · part.use_count()=%ld\n", *part, part.use_count());
    part.reset();
    std::printf("(3) part.reset() 뒤\n");
}
```

- ★★ `whole.reset()` 뒤에 `*part` 를 읽어도 되나 — `~Pair` 는 언제 찍히나?
- ★ `part.get()` 과 `part` 가 살려 두는 것은 같은 객체인가?

### 8. ★★ 같은 순환을 clang + ASan 으로 (경계)

- ★★★ 3번의 순환 판을 clang + ASan 으로 10번 돌리면 **10번 다 보고**하나?
- ★★ 「ASan 이 조용했다」에서 무엇을 결론 내면 안 되나 — ASan 이 **원리상** 못 보는 순환은 어떤 것인가?

### 9. ★★ 참조 계수 포인터를 다른 스레드로 넘긴다 (경계)

- ★★ Rust 에서 `Rc<i32>` 를 `thread::spawn` 의 `move` 클로저로 넘기면? · `Arc` 면?
- ★★ C++ 에서 `shared_ptr<int>` 를 `std::thread` 에 캡처로 넘기면 — 그러면 C++ 이 더 안전한가?

### 10. ★★ CPython 의 참조 계수 (연결)

- ★ `sys.getrefcount(a)` 가 이름 하나일 때 1 이 아니라 2 인 이유는?
- ★★★ 순환을 만들고 이름을 지우면 CPython 은 어떻게 회수하나 — C++ `shared_ptr` 에는 그것이 있나?

### 11. ★★★ `shared_ptr` 을 기본값으로 쓰면 안 되는 이유 (왜)

- ★★★ **시간을 재지 않고** 댈 수 있는 근거를 넷 대라 — 각각 이 편의 몇 번에서 셌나?
- ★ 팩토리는 무엇을 돌려주는 것이 좋은가 — 받는 쪽이 공유가 필요하면 무엇을 치르나?

### 12. 다른 주제와 잇기 (연결)

- ★★★ 26편의 「소유권이 타입에 있다」와 이 편의 「제어 블록」은 각각 **삭제자를 어디에** 두나?
- ★★ 순환을 `weak_ptr` 로 끊는 설계의 정본은 몇 번 주제인가?
- ★ 「RAII 가 그대로 두는 것」 목록에 `shared_ptr` 순환을 올린 문서는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
