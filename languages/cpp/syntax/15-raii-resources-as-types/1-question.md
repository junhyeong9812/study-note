# cpp/syntax/15 — RAII: 자원을 타입으로 묶기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **수로 답하는 것**이 절반이다 — 「해제된다」로 뭉개지 말고
> **살아 있는 자원이 몇 개인지**, **`free` 가 몇 번 불렸는지**를 숫자로 맞혀야 한다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★ **네 번째 창은 「어셈블리 세기」다**(8번) — 명령·분기·`call`·예외 표 개수.
> ★ **「부적용인 창」이 있다** — 진단의 `(행,열)`. RAII 는 **파싱 우선순위가 걸리는 문법이 아니라
> 타입 설계 관용구**라 열로 가를 것이 없다. **「안 쟀다」가 아니라 「잴 것이 없다」다.**
> ★★ **「못 잰 것」은 또 다르다** — C++ 에는 **런타임 할당 계수기가 표준에 없다.**
> C# 갈래가 `GC.GetAllocatedBytesForCurrentThread()` 로 묻는 것을 여기서는 **ASan 누수 리포트**로 바꿔 물었다.
> 선행 — [14번](../14-destructors-and-deterministic-destruction/)이 이 주제의 **토대**다. 되감기 보장이 없으면 여기 전부가 무너진다.
> 대비 — C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **13번**([`13-goto-cleanup-idiom/`](../../../c/syntax/13-goto-cleanup-idiom/))이 **직접 대비**다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 세 경로로 빠져나가면 (예측)

```cpp
/* raii01.cpp */
// 자원 셋을 타입으로 묶는다 — 정상·조기 반환·예외 세 경로를 같은 코드가 덮는다
#include <cstdio>
#include <cstdlib>
#include <stdexcept>

static int alive = 0;

struct Mem {                                   // ① 메모리
    void* p;
    explicit Mem(std::size_t n) : p(std::malloc(n)) {
        if (!p) throw std::bad_alloc();
        ++alive; std::printf("    [잡음] 메모리 %zu바이트\n", n);
    }
    ~Mem() { std::free(p); --alive; std::printf("    [놓음] 메모리\n"); }
    Mem(const Mem&) = delete;
    Mem& operator=(const Mem&) = delete;
};

struct File {                                  // ② 파일
    std::FILE* f;
    File(const char* path, const char* mode) : f(std::fopen(path, mode)) {
        if (!f) throw std::runtime_error("파일을 못 열었다");
        ++alive; std::printf("    [잡음] 파일 %s\n", path);
    }
    ~File() { std::fclose(f); --alive; std::printf("    [놓음] 파일\n"); }
    File(const File&) = delete;
    File& operator=(const File&) = delete;
};

struct Flag {                                  // ③ 「잠금」 흉내 — 플래그 하나
    bool& held;
    explicit Flag(bool& b) : held(b) {
        held = true; ++alive; std::printf("    [잡음] 플래그\n");
    }
    ~Flag() { held = false; --alive; std::printf("    [놓음] 플래그\n"); }
    Flag(const Flag&) = delete;
    Flag& operator=(const Flag&) = delete;
};

static bool g_flag = false;

int work(int mode) {
    Mem m(64);
    File f("/dev/null", "wb");
    Flag g(g_flag);
    if (mode == 1) { std::printf("    조기 반환한다\n"); return -1; }
    if (mode == 2) { std::printf("    던진다\n"); throw std::runtime_error("한가운데에서"); }
    std::printf("    끝까지 간다\n");
    return 0;
}

int main() {
    for (int mode = 0; mode < 3; ++mode) {
        std::printf("(%d) mode=%d\n", mode, mode);
        try { work(mode); } catch (const std::exception& e) { std::printf("    [catch] %s\n", e.what()); }
        std::printf("    살아 있는 자원 %d개 · 플래그 %s\n", alive, g_flag ? "잡힘" : "풀림");
    }
}
```

- `mode=0`·`1`·`2` 각각에서 **`살아 있는 자원`** 은 몇 개인가?
- ★★ **`[놓음]` 세 줄의 순서**는 세 판에서 같은가 다른가 — 그리고 **잡은 순서와 어떤 관계**인가?
- ★ `mode=2` 에서 `[catch]` 는 `[놓음]` 들의 **앞인가 뒤인가**?
- ★ 함수 `work` 본문에 **해제 코드가 몇 줄** 적혀 있는가?

### 2. ★★★ 같은 일을 손으로 하면 (예측)

```cpp
/* raii02.cpp */
// 손으로 잡고 놓으면 세 경로 중 둘이 샌다
#include <cstdio>
#include <cstdlib>
#include <stdexcept>

static int alive = 0;
static bool g_flag = false;

int work(int mode) {
    void* m = std::malloc(64);           ++alive; std::printf("    [잡음] 메모리\n");
    std::FILE* f = std::fopen("/dev/null", "wb"); ++alive; std::printf("    [잡음] 파일\n");
    g_flag = true;                       ++alive; std::printf("    [잡음] 플래그\n");

    if (mode == 1) { std::printf("    조기 반환한다\n"); return -1; }   // 놓는 코드를 빠뜨렸다
    if (mode == 2) { std::printf("    던진다\n"); throw std::runtime_error("한가운데에서"); }

    std::printf("    끝까지 간다\n");
    g_flag = false; --alive; std::printf("    [놓음] 플래그\n");
    std::fclose(f); --alive; std::printf("    [놓음] 파일\n");
    std::free(m);   --alive; std::printf("    [놓음] 메모리\n");
    return 0;
}

int main() {
    for (int mode = 0; mode < 3; ++mode) {
        std::printf("(%d) mode=%d\n", mode, mode);
        try { work(mode); } catch (const std::exception& e) { std::printf("    [catch] %s\n", e.what()); }
        std::printf("    살아 있는 자원 %d개 · 플래그 %s\n", alive, g_flag ? "잡힘" : "풀림");
    }
}
```

- `mode=0`·`1`·`2` 각각에서 **`살아 있는 자원`** 은 몇 개인가?
- ★★★ `mode=2` 의 숫자가 **3이 아닌** 이유는?
- ★★ ASan 을 붙이면 **몇 바이트가 몇 개 객체에서** 샜다고 나오는가?
- ★★★ 그 숫자가 **내가 센 `살아 있는 자원` 과 다른** 이유는?

### 3. ★★ `lock_guard` 없이 `mutex` 를 쓰면 (예측)

```cpp
/* raii03.cpp */
// lock_guard 없이 mutex 를 직접 쓰면 — 예외 경로에서 락이 남는다
#include <cstdio>
#include <mutex>
#include <stdexcept>

static std::mutex by_hand, by_guard;

void hand(bool boom) {
    by_hand.lock();
    if (boom) throw std::runtime_error("터진다");     // unlock 을 못 지나간다
    by_hand.unlock();
}

void guarded(bool boom) {
    std::lock_guard<std::mutex> g(by_guard);
    if (boom) throw std::runtime_error("터진다");
}

static void report(const char* tag, std::mutex& m) {
    if (m.try_lock()) { std::printf("  %-28s 락이 풀려 있다\n", tag); m.unlock(); }
    else              { std::printf("  %-28s 락이 아직 잡혀 있다\n", tag); }
}

int main() {
    try { hand(false); }    catch (...) {}
    report("hand      / 예외 없음", by_hand);
    try { hand(true); }     catch (...) {}
    report("hand      / 예외 있음", by_hand);
    try { guarded(false); } catch (...) {}
    report("lock_guard/ 예외 없음", by_guard);
    try { guarded(true); }  catch (...) {}
    report("lock_guard/ 예외 있음", by_guard);
    std::printf("  sizeof(std::lock_guard<std::mutex>) = %zu\n", sizeof(std::lock_guard<std::mutex>));
}
```

- 네 줄의 「**락이 풀려 있다 / 락이 아직 잡혀 있다**」를 맞힐 수 있는가?
- ★★ `hand()` 에서 `unlock()` 이 **지나가지 못하는 이유**를 한 줄로 말할 수 있는가?
- ★ `sizeof(std::lock_guard<std::mutex>)` 는 얼마인가?
- ★ 이 실험이 **데드락 자체를 재현하지 않은** 이유는?

### 4. ★★ 복사를 안 막은 래퍼를 복사하면 (예측)

```cpp
/* raii04.cpp */
// 복사를 막지 않은 래퍼를 복사하면 — 마커를 표준 오류로 찍는다(ASan 이 죽여도 남게)
#include <cstdio>
#include <cstdlib>

struct Loose {
    void* p;
    explicit Loose(std::size_t n) : p(std::malloc(n)) {
        std::fprintf(stderr, "  [잡음] %zu바이트\n", n);
    }
    ~Loose() { std::fprintf(stderr, "  [놓음] Loose\n"); std::free(p); }
};

int main() {
    std::fprintf(stderr, "(1) 복사 생성자를 막지 않았다\n");
    Loose a(32);
    Loose b = a;                       // 포인터만 베껴 간다
    std::fprintf(stderr, "  두 객체가 같은 주소를 든다: %d\n", (int)(a.p == b.p));
    std::fprintf(stderr, "(2) 블록이 끝나면 둘 다 놓는다\n");
}
```

- `두 객체가 같은 주소를 든다` 의 값은 **0 인가 1 인가**?
- ★★ `[놓음] Loose` 는 **몇 줄** 찍히는가?
- ★★★ ASan 은 이것을 **무엇이라고 부르는가** — `run exit` 은?
- ★★ 이 소스를 **경고 없이** 컴파일할 수 있는가?

### 5. ★★ 복사를 막고 이동만 열면 (예측)

```cpp
/* raii05.cpp */
// 복사는 막고 이동만 연다
#include <cstdio>
#include <cstdlib>
#include <utility>

static int frees = 0;

struct Tight {
    void* p;
    explicit Tight(std::size_t n) : p(std::malloc(n)) { std::printf("    [잡음] %zu바이트\n", n); }
    ~Tight() {
        if (p) { std::free(p); ++frees; std::printf("    [놓음] 들고 있던 것을 놓는다\n"); }
        else   { std::printf("    [놓음] 빈 껍데기 — 놓을 것이 없다\n"); }
    }
    Tight(const Tight&) = delete;
    Tight& operator=(const Tight&) = delete;
    Tight(Tight&& o) noexcept : p(o.p) { o.p = nullptr; }
    Tight& operator=(Tight&& o) noexcept {
        if (this != &o) { if (p) { std::free(p); ++frees; } p = o.p; o.p = nullptr; }
        return *this;
    }
};

Tight make() { return Tight(16); }

int main() {
    std::printf("(1) 옮기면\n");
    { Tight a(32); Tight b = std::move(a); (void)b; }
    std::printf("    free 호출 %d회\n", frees);
    std::printf("(2) 함수에서 돌려받으면\n");
    frees = 0;
    { Tight c = make(); (void)c; }
    std::printf("    free 호출 %d회\n", frees);
}
```

- `(1)` 에서 `free 호출` 은 **몇 회**인가 — 그리고 `[놓음]` 줄은 **몇 줄**인가?
- ★★★ 옮긴 뒤 **원본의 소멸자가 도는가 안 도는가**?
- ★★ `(2)` 의 `free 호출` 은 몇 회이고, `[잡음]`/`[놓음]` 줄 수가 `(1)` 과 다른 이유는?
- ★ 이동 생성자에서 `o.p = nullptr` 을 **안 하면** 무엇이 되는가?

### 6. ★★★ 생성자가 한가운데에서 던지면 (예측)

```cpp
/* raii08.cpp */
// 생성자가 터지면 소멸자가 도나 — 마커는 표준 오류로
#include <cstdio>
#include <cstdlib>
#include <stdexcept>

struct Res {
    const char* tag;
    explicit Res(const char* t) : tag(t) { std::fprintf(stderr, "    [잡음] %s\n", tag); }
    ~Res() { std::fprintf(stderr, "    [놓음] %s\n", tag); }
};

struct Raw {                                  // 자원을 손으로 잡는다
    Res* a = nullptr;
    Res* b = nullptr;
    Raw() {
        a = new Res("Raw 의 a");
        throw std::runtime_error("생성자 한가운데에서");
        b = new Res("Raw 의 b");
    }
    ~Raw() { std::fprintf(stderr, "    [소멸자] ~Raw 가 도나?\n"); delete a; delete b; }
};

struct Wrapped {                              // 멤버가 이미 RAII 다
    Res a{"Wrapped 의 a"};
    Res b{"Wrapped 의 b"};
    Wrapped() { throw std::runtime_error("생성자 한가운데에서"); }
    ~Wrapped() { std::fprintf(stderr, "    [소멸자] ~Wrapped 가 도나?\n"); }
};

int main() {
    std::fprintf(stderr, "(1) 손으로 잡다가 터지면\n");
    try { Raw r; (void)r; } catch (const std::exception& e) { std::fprintf(stderr, "    [catch] %s\n", e.what()); }
    std::fprintf(stderr, "(2) 멤버가 RAII 이면\n");
    try { Wrapped w; (void)w; } catch (const std::exception& e) { std::fprintf(stderr, "    [catch] %s\n", e.what()); }
}
```

- `(1)` 에서 **`[소멸자] ~Raw 가 도나?`** 는 찍히는가?
- ★★★ `(2)` 에서 **`[놓음]` 줄이 몇 개** 찍히는가 — 그리고 `~Wrapped` 는 도는가?
- ★★ 두 판이 갈리는 이유를 **한 문장**으로 말할 수 있는가?
- ★★ ASan 은 **몇 바이트**가 샜다고 하는가 — 어느 쪽에서 샌 것인가?

### 7. ★ 표준 래퍼는 얼마나 무거운가 (경계)

- `sizeof(unique_ptr<FILE, 상태 없는 함수 객체>)` 와 `sizeof(FILE*)` 중 **큰 쪽**은?
- ★★★ `unique_ptr` 의 `sizeof` 가 **두 배가 되는 딱 한 자리**는 어디인가 — 왜인가?
- ★ `shared_ptr` 이 `unique_ptr` 보다 큰 이유는? `unique_lock` 이 `lock_guard` 보다 큰 이유는?
- ★★ **빈 `unique_ptr` 을 파괴하면** 사용자 정의 deleter 가 불리는가?
- ★ `release()` 와 `reset()` 은 deleter 를 각각 **몇 번** 부르는가?

### 8. ★★★ C 의 `goto cleanup` 과 나란히 재면 (경계)

```cpp
/* raii09.cpp */
// 같은 일을 세 가지로 적는다 — 소스와 기계어를 나란히 잰다
#include <cstdio>
#include <cstdlib>

int sink(void*, void*, std::FILE*);

int with_goto(const char* path, int n) {
    int rc = -1;
    void* a = std::malloc(static_cast<std::size_t>(n));
    if (!a) goto out;
    {
        void* b = std::malloc(static_cast<std::size_t>(n) * 2);
        if (!b) goto out_a;
        {
            std::FILE* f = std::fopen(path, "rb");
            if (!f) goto out_b;
            rc = sink(a, b, f);
            std::fclose(f);
        }
    out_b:
        std::free(b);
    }
out_a:
    std::free(a);
out:
    return rc;
}

int with_dup(const char* path, int n) {
    void* a = std::malloc(static_cast<std::size_t>(n));
    if (!a) return -1;
    void* b = std::malloc(static_cast<std::size_t>(n) * 2);
    if (!b) { std::free(a); return -1; }
    std::FILE* f = std::fopen(path, "rb");
    if (!f) { std::free(b); std::free(a); return -1; }
    int rc = sink(a, b, f);
    std::fclose(f);
    std::free(b);
    std::free(a);
    return rc;
}

struct Mem {
    void* p;
    explicit Mem(std::size_t n) : p(std::malloc(n)) {}
    ~Mem() { std::free(p); }
    Mem(const Mem&) = delete;
    Mem& operator=(const Mem&) = delete;
};

struct File {
    std::FILE* f;
    File(const char* path, const char* mode) : f(std::fopen(path, mode)) {}
    ~File() { if (f) std::fclose(f); }
    File(const File&) = delete;
    File& operator=(const File&) = delete;
};

int with_raii(const char* path, int n) {
    Mem a(static_cast<std::size_t>(n));
    if (!a.p) return -1;
    Mem b(static_cast<std::size_t>(n) * 2);
    if (!b.p) return -1;
    File f(path, "rb");
    if (!f.f) return -1;
    return sink(a.p, b.p, f.f);
}
```

- 세 함수의 **본문 줄 수**와 **소스에 적힌 해제 호출 개수**는 각각 얼마인가?
- ★★★ `-O2` 에서 **분기(`j*`) 가 가장 많은 판**은 어디인가 — 「RAII 가 분기를 줄인다」는 참인가?
- ★★★ RAII 판에만 생기는 **`.cold` 조각**은 무엇인가?
- ★★★ **`-fno-exceptions`** 로 던지면 세 판의 순위가 어떻게 바뀌는가?
- ★★ `.gcc_except_table` 절 수와 `.LEHB` 개수는 **예외를 켠 판과 끈 판**에서 각각 얼마인가?
- ★★ **`-O0` 과 `-Os`** 에서는 결론이 유지되는가?
- ★ C 갈래 13번의 결론(「분기가 아니라 중복을 줄인다」)과 **어디가 같고 어디가 다른가**?

### 9. ★★ 경고를 누가 보나 (경계)

- RAII 를 안 쓴 자리 여섯을 심고 `-Wall -Wextra -pedantic` 으로 물으면 **몇 건**이 나오는가?
- ★★★ 그 프로그램을 ASan 으로 돌리면 **몇 바이트가 몇 개 할당에서** 샜다고 나오는가?
- ★★ ASan 이 **못 보는** 자원 두 가지는 무엇인가?
- ★ 이 주제에서 **컴파일 시간으로 올라오는 것**은 무엇 하나인가?

### 10. 다른 주제와 잇기 (연결)

- **RAII 가 성립하는 유일한 근거**는 몇 번 주제의 어느 절인가?
- 「**소멸자를 적었으면 복사도 결정하라**」의 정본은 몇 번 주제인가?
- **`unique_ptr`·`shared_ptr`·`weak_ptr`** 의 정본은 각각 몇 번인가?
- ★★ **위임 생성자 뒤에 던지면 소멸자가 도는데** 여기 6번에서는 안 돈다 — **같은 규칙**임을 설명할 수 있는가? 어느 주제 어느 절인가?
- ★★ **러스트의 `Drop`** 이 이 주제의 어느 수고를 없애 주는가 — 어느 갈래 몇 번인가?
- ★ **GC 가 있는 언어**는 같은 문제를 무엇으로 푸는가 — 어느 갈래 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
