# cpp/syntax/15 — RAII: 자원을 타입으로 묶기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·어셈블리 수치는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이므로 **출력을 싣는 블록마다 그 출력을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — **ASan 의 PID·주소**와 **어셈블리의 레지스터 이름**은 흔들리는 칸이다.\
> 근거로 쓰는 것은 **살아 있는 자원 개수 · 샌 바이트와 객체 수 · 명령·분기·`call` 개수 ·\
> 예외 표 절 수 · `sizeof` · `cc exit`/`run exit` · 경고 개수**다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「몇 배 빠르다」는 문장이 **한 줄도 없다** —\
> (8)이 센 것은 **명령·분기·`call` 개수까지**다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 세 판 모두 **0개** — 놓음 로그가 한 글자도 같다

**출력**

```text
===== 소스: raii01.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -pedantic raii01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(0) mode=0
    [잡음] 메모리 64바이트
    [잡음] 파일 /dev/null
    [잡음] 플래그
    끝까지 간다
    [놓음] 플래그
    [놓음] 파일
    [놓음] 메모리
    살아 있는 자원 0개 · 플래그 풀림
(1) mode=1
    [잡음] 메모리 64바이트
    [잡음] 파일 /dev/null
    [잡음] 플래그
    조기 반환한다
    [놓음] 플래그
    [놓음] 파일
    [놓음] 메모리
    살아 있는 자원 0개 · 플래그 풀림
(2) mode=2
    [잡음] 메모리 64바이트
    [잡음] 파일 /dev/null
    [잡음] 플래그
    던진다
    [놓음] 플래그
    [놓음] 파일
    [놓음] 메모리
    [catch] 한가운데에서
    살아 있는 자원 0개 · 플래그 풀림
```

**왜 그런가**

| mode | 어떻게 나가나 | `[놓음]` | 살아 있는 자원 | 플래그 |
|---|---|---|---|---|
| 0 | 끝까지 간다 | 플래그 → 파일 → 메모리 | ★ **0** | 풀림 |
| 1 | 조기 반환 | 플래그 → 파일 → 메모리 | ★ **0** | 풀림 |
| 2 | 예외 | 플래그 → 파일 → 메모리 | ★★★ **0** | 풀림 |

- ★★★ **세 판의 놓음 로그가 같다.** 경로가 셋인데 **해제 코드는 소멸자 셋에 한 번씩**만 있다.
- ★★★ **놓는 순서는 잡은 역순**이다 — 메모리 → 파일 → 플래그로 잡았고, 플래그 → 파일 → 메모리로 놓았다.\
  [14번](../14-destructors-and-deterministic-destruction/) (1)의 **선언 역순** 규칙 그대로이고,\
  ★ **나중에 잡은 것이 먼저 풀리는 것**이 **락 순서·의존 순서와 정확히 맞는다.**
- ★★ **`[catch]` 는 `[놓음]` 들의 뒤**다 — 되감기가 먼저 끝난다([14번](../14-destructors-and-deterministic-destruction/) (2)).
- ★★★ **`work` 본문에 해제 코드가 0줄이다.** 이것이 이 주제의 값 전부이고, (8)에서 **수로 다시 센다.**

### 2. ★★★ 0 · 3 · **6** — 그리고 ASan 은 **2**라고 한다

**출력**

```text
===== 소스: raii02.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -pedantic raii02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(0) mode=0
    [잡음] 메모리
    [잡음] 파일
    [잡음] 플래그
    끝까지 간다
    [놓음] 플래그
    [놓음] 파일
    [놓음] 메모리
    살아 있는 자원 0개 · 플래그 풀림
(1) mode=1
    [잡음] 메모리
    [잡음] 파일
    [잡음] 플래그
    조기 반환한다
    살아 있는 자원 3개 · 플래그 잡힘
(2) mode=2
    [잡음] 메모리
    [잡음] 파일
    [잡음] 플래그
    던진다
    [catch] 한가운데에서
    살아 있는 자원 6개 · 플래그 잡힘
```

**ASan 을 붙이면**

```text
===== g++ -std=c++20 -Wall -Wextra -fsanitize=address -g -ffile-prefix-map="$PWD"=. raii02.cpp -o exa && ./exa | grep -E '^(==|SUMMARY|Direct|Indirect)' (cc exit=0 · run exit=1) =====
=================================================================
==1330338==ERROR: LeakSanitizer: detected memory leaks
Direct leak of 128 byte(s) in 2 object(s) allocated from:
SUMMARY: AddressSanitizer: 128 byte(s) leaked in 2 allocation(s).
```

**왜 그런가**

- ★★★ **`mode=1` 에서 3개, `mode=2` 에서 6개**다. 셋이 아니라 여섯인 이유는\
  **`alive` 가 프로그램 전체에 걸친 누적**이라, **앞 판(`mode=1`)에서 샌 3개가 그대로 쌓여 있기** 때문이다.\
  ★ **「이번 판에서 몇 개 샜나」가 아니라 「쌓인다」가 보이는 것**이 계수기를 두는 이유다.
- ★★★ **ASan 은 `Direct leak of 128 byte(s) in 2 object(s)`** 라고 한다 — `malloc(64)` **두 번**이다.
- ★★★ **`alive` 6과 ASan 2가 다른 이유는 세는 대상이 다르기 때문**이다.\
  `alive` 는 **메모리·파일·플래그를 전부** 세고, **ASan 은 힙 할당만** 센다.\
  ★★ **파일 핸들과 락은 ASan 이 안 본다** — 그래서 두 창이 **둘 다** 필요하다.
- ★ **소스는 1번과 똑같은 순서로 똑같은 일을 한다.** 갈리는 것은 **해제 코드를 어디에 적었나**뿐이다.

### 3. ★★ 네 줄은 **풀림 · 잡힘 · 풀림 · 풀림**

**출력**

```text
===== 소스: raii03.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -pedantic raii03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  hand      / 예외 없음    락이 풀려 있다
  hand      / 예외 있음    락이 아직 잡혀 있다
  lock_guard/ 예외 없음    락이 풀려 있다
  lock_guard/ 예외 있음    락이 풀려 있다
  sizeof(std::lock_guard<std::mutex>) = 8
```

**왜 그런가**

- ★★★ **`hand()` 의 예외 판만 락이 잡힌 채로 남았다.**\
  `by_hand.unlock()` 은 `throw` **다음 줄**이라 **지나갈 길이 없다.**
- ★★ **`lock_guard` 는 예외 판에서도 풀었다** — 되감기가 `~lock_guard` 를 부르기 때문이다.\
  **1번과 한 글자도 같은 이유**다.
- ★ **`sizeof(std::lock_guard<std::mutex>) = 8`** — **참조 하나**뿐이다.\
  「RAII 는 객체가 하나 더 생겨 무겁다」가 **여기서는 참이 아니다**(7번에서 전수로 잰다).
- ★ **데드락 자체를 재현하지 않은 이유** — 재현하려면 **스레드를 띄워 그 락을 기다리게** 해야 하는데,\
  그러면 **이 문서를 만드는 프로그램이 멈춘다.** 대신 `try_lock()` 으로 **「풀렸나」만** 물었다 —\
  **결정적이고, 같은 사실을 보인다.**

### 4. ★★ 값은 **1** · `[놓음]` 은 **두 줄** · ASan 은 **`double-free`**

**출력**

```text
===== 소스: raii04.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -fsanitize=address -g -ffile-prefix-map="$PWD"=. raii04.cpp -o exa && ./exa | grep -E '^(\(|  \[|  두|==|SUMMARY)' (cc exit=0 · run exit=1) =====
(1) 복사 생성자를 막지 않았다
  [잡음] 32바이트
  두 객체가 같은 주소를 든다: 1
(2) 블록이 끝나면 둘 다 놓는다
  [놓음] Loose
  [놓음] Loose
=================================================================
==1330382==ERROR: AddressSanitizer: attempting double-free on 0x503000000040 in thread T0:
SUMMARY: AddressSanitizer: double-free ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:52 in free
==1330382==ABORTING
```

**왜 그런가**

- ★★★ **`두 객체가 같은 주소를 든다: 1`** — 컴파일러가 만들어 주는 복사 생성자는 **포인터를 베끼기만** 한다.\
  **가리키는 곳은 하나인데 소유자가 둘**이 됐다.
- ★★★ **`[놓음] Loose` 가 두 줄**이고, 두 번째 `free` 에서 ASan 이\
  `attempting double-free on 0x…` 로 죽인다 — **`run exit=1`**(`ABORTING`).\
  ★ [14번](../14-destructors-and-deterministic-destruction/) (5)의 `new-delete-type-mismatch`, (6)의 `bad-free` 와 **또 다른 이름**이다.
- ★★★ **이 소스는 경고 없이 컴파일된다**(`cc exit=0`). **소멸자를 적었는데 복사를 안 막은 것**이\
  **0/3/5의 법칙**([목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/))이 말하는 자리이고, **컴파일러는 아무 말도 하지 않는다**(9번).

### 5. ★★ `free` 는 **한 번** — 원본의 소멸자는 **여전히 돈다**

**출력**

```text
===== 소스: raii05.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -pedantic raii05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 옮기면
    [잡음] 32바이트
    [놓음] 들고 있던 것을 놓는다
    [놓음] 빈 껍데기 — 놓을 것이 없다
    free 호출 1회
(2) 함수에서 돌려받으면
    [잡음] 16바이트
    [놓음] 들고 있던 것을 놓는다
    free 호출 1회
```

**왜 그런가**

- ★★★ **`(1)` 의 `free 호출` 은 1회**이고 **`[놓음]` 은 두 줄**이다.\
  한 줄은 `들고 있던 것을 놓는다`, 다른 한 줄은 **`빈 껍데기 — 놓을 것이 없다`** 다.
- ★★★ **옮긴 뒤에도 원본의 소멸자는 돈다.** **파괴가 사라지는 것이 아니라 「놓을 것이 없어지는」 것**이다.\
  ★★ 그래서 ① 이동 생성자에서 **`o.p = nullptr`** 을 해야 하고 ② 소멸자가 **널을 견뎌야** 한다.
- ★★ **`(2)` 의 `free 호출` 도 1회**인데 **`[놓음]` 은 한 줄**뿐이다 —\
  `make()` 가 돌려주는 prvalue 는 **복사 생략**으로 `c` 자리에 바로 지어져서 **이동조차 일어나지 않았다.**\
  ★ 「빈 껍데기」가 아예 안 생긴 것이고, 이것은 **미명시 구간**이다(정본은 형제 [`08번`](../08-value-categories-lvalue-prvalue-xvalue/)).
- ★ **`o.p = nullptr` 을 안 하면** 4번과 같은 **이중 해제**가 된다 — 둘이 같은 포인터를 들고 각자 놓는다.

### 6. ★★★ `~Raw` 는 **안 돈다**(그래서 샌다) · `Wrapped` 는 멤버 둘이 **역순으로** 파괴된다

**출력**

```text
===== 소스: raii08.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -pedantic raii08.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 손으로 잡다가 터지면
    [잡음] Raw 의 a
    [catch] 생성자 한가운데에서
(2) 멤버가 RAII 이면
    [잡음] Wrapped 의 a
    [잡음] Wrapped 의 b
    [놓음] Wrapped 의 b
    [놓음] Wrapped 의 a
    [catch] 생성자 한가운데에서
```

**ASan 을 붙이면**

```text
===== g++ -std=c++20 -Wall -Wextra -fsanitize=address -g -ffile-prefix-map="$PWD"=. raii08.cpp -o exa && ./exa | grep -E '^(==|SUMMARY|Direct|Indirect|\(|    \[)' (cc exit=0 · run exit=1) =====
(1) 손으로 잡다가 터지면
    [잡음] Raw 의 a
    [catch] 생성자 한가운데에서
(2) 멤버가 RAII 이면
    [잡음] Wrapped 의 a
    [잡음] Wrapped 의 b
    [놓음] Wrapped 의 b
    [놓음] Wrapped 의 a
    [catch] 생성자 한가운데에서
=================================================================
==1330481==ERROR: LeakSanitizer: detected memory leaks
Direct leak of 8 byte(s) in 1 object(s) allocated from:
SUMMARY: AddressSanitizer: 8 byte(s) leaked in 1 allocation(s).
```

**왜 그런가**

```text
   Raw()      a = new Res("a");  throw;   -> ~Raw 가 안 돈다  -> a 가 샌다
   Wrapped    Res a; Res b;  (멤버)       -> ~Wrapped 도 안 돈다
              Wrapped() { throw; }           그런데 ★ a·b 는 이미 지어졌으므로
                                             역순으로 파괴된다 -> 안 샌다
```

- ★★★ **`[소멸자] ~Raw 가 도나?` 는 한 줄도 안 찍혔다.** **생성자가 완주하지 못한 객체는 파괴되지 않는다** —\
  「아직 태어나지 않았으니 죽일 것도 없다」는 규칙이다.
- ★★★ **`(2)` 에서는 `[놓음]` 이 두 줄**(`b` → `a`)이고, **`~Wrapped` 는 똑같이 안 돈다.**\
  **이미 지어진 멤버는 역순으로 파괴되기 때문**이다.
- ★★ **한 문장으로** — 「**소멸자가 도는 단위는 객체 하나가 아니라 이미 지어진 부분들 각각**」이다.\
  그래서 **자원을 멤버 타입에 맡기면** 생성자 중간 실패에서도 안 샌다.
- ★★ **ASan 은 `Direct leak of 8 byte(s) in 1 object(s)`** 라고 한다 — `new Res("Raw 의 a")` **하나**다.\
  ★ **`Wrapped` 쪽은 한 바이트도 안 샜다.** 같은 프로그램 안에서 둘이 갈린다.
- ★ **[13번](../13-constructors-member-init-list-and-delegating/) (4)와 정반대로 보이지만 같은 규칙**이다 —\
  기준은 늘 「**생성자가 완주했나**」이고, 위임 생성자는 **본체가 완주한 시점**에 그것이 참이 된다.

### 7. ★ 둘이 **같다**(8바이트) — 두 배가 되는 곳은 **함수 포인터 deleter** 하나뿐이다

**출력**

```text
===== 소스: raii07.cpp =====
// 표준이 주는 래퍼와 직접 만든 래퍼 — 크기와 쓰는 법
#include <cstdio>
#include <memory>
#include <mutex>

struct FileCloser { void operator()(std::FILE* f) const { if (f) std::fclose(f); } };

struct MyFile {                                  // 직접 만든 것
    std::FILE* f;
    MyFile(const char* p, const char* m) : f(std::fopen(p, m)) {}
    ~MyFile() { if (f) std::fclose(f); }
    MyFile(const MyFile&) = delete;
    MyFile& operator=(const MyFile&) = delete;
};

int main() {
    auto lam = [](std::FILE* f) { if (f) std::fclose(f); };
    std::printf("sizeof(FILE*)                                = %zu\n", sizeof(std::FILE*));
    std::printf("sizeof(MyFile)                               = %zu\n", sizeof(MyFile));
    std::printf("sizeof(unique_ptr<FILE, FileCloser>)         = %zu   (상태 없는 함수 객체)\n",
                sizeof(std::unique_ptr<std::FILE, FileCloser>));
    std::printf("sizeof(unique_ptr<FILE, decltype(람다)>)     = %zu   (상태 없는 람다)\n",
                sizeof(std::unique_ptr<std::FILE, decltype(lam)>));
    std::printf("sizeof(unique_ptr<FILE, int(*)(FILE*)>)      = %zu   (함수 포인터)\n",
                sizeof(std::unique_ptr<std::FILE, int (*)(std::FILE*)>));
    std::printf("sizeof(unique_ptr<int>)                      = %zu\n", sizeof(std::unique_ptr<int>));
    std::printf("sizeof(shared_ptr<int>)                      = %zu   (제어 블록 포인터가 하나 더)\n",
                sizeof(std::shared_ptr<int>));
    std::printf("sizeof(lock_guard<mutex>)                    = %zu\n", sizeof(std::lock_guard<std::mutex>));
    std::printf("sizeof(unique_lock<mutex>)                   = %zu   (푼 상태를 기억한다)\n",
                sizeof(std::unique_lock<std::mutex>));

    {
        std::unique_ptr<std::FILE, FileCloser> up(std::fopen("/dev/null", "wb"));
        std::printf("열렸는가(unique_ptr)                         = %d\n", (int)(up != nullptr));
        MyFile mf("/dev/null", "wb");
        std::printf("열렸는가(직접 만든 것)                       = %d\n", (int)(mf.f != nullptr));
    }
    std::printf("블록이 끝났다 — 둘 다 닫혔다\n");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic raii07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof(FILE*)                                = 8
sizeof(MyFile)                               = 8
sizeof(unique_ptr<FILE, FileCloser>)         = 8   (상태 없는 함수 객체)
sizeof(unique_ptr<FILE, decltype(람다)>)     = 8   (상태 없는 람다)
sizeof(unique_ptr<FILE, int(*)(FILE*)>)      = 16   (함수 포인터)
sizeof(unique_ptr<int>)                      = 8
sizeof(shared_ptr<int>)                      = 16   (제어 블록 포인터가 하나 더)
sizeof(lock_guard<mutex>)                    = 8
sizeof(unique_lock<mutex>)                   = 16   (푼 상태를 기억한다)
열렸는가(unique_ptr)                         = 1
열렸는가(직접 만든 것)                       = 1
블록이 끝났다 — 둘 다 닫혔다
```

**deleter 가 정말 불리나**

```text
===== 소스: raii12.cpp =====
// unique_ptr 의 사용자 정의 deleter — 정말 그것이 불리나, 빈 것에도 불리나
#include <cstdio>
#include <memory>
#include <cstdlib>

static int closed = 0;

struct Closer {
    void operator()(std::FILE* f) const {
        if (f) { std::fclose(f); ++closed; std::printf("    [Closer] fclose 했다\n"); }
        else   { std::printf("    [Closer] 이 줄은 안 나온다\n"); }
    }
};

int main() {
    std::printf("(1) 함수 객체 deleter\n");
    { std::unique_ptr<std::FILE, Closer> up(std::fopen("/dev/null", "wb")); }
    std::printf("    닫은 횟수 %d\n", closed);

    std::printf("(2) 람다 deleter — 블록을 나가면\n");
    closed = 0;
    { auto del = [](std::FILE* f) { std::fclose(f); ++closed; std::printf("    [람다] fclose 했다\n"); };
      std::unique_ptr<std::FILE, decltype(del)> up(std::fopen("/dev/null", "wb"), del); }
    std::printf("    닫은 횟수 %d\n", closed);

    std::printf("(3) 빈 unique_ptr 을 파괴하면 deleter 가 불리나\n");
    closed = 0;
    { std::unique_ptr<std::FILE, Closer> empty(nullptr); }
    std::printf("    닫은 횟수 %d  (deleter 는 아예 불리지 않았다)\n", closed);

    std::printf("(4) release() 로 놓아 주면\n");
    closed = 0;
    { std::unique_ptr<std::FILE, Closer> up(std::fopen("/dev/null", "wb"));
      std::FILE* raw = up.release();
      std::printf("    release() 뒤 up 은 비었는가: %d\n", (int)(up.get() == nullptr));
      std::fclose(raw); }
    std::printf("    Closer 가 불린 횟수 %d  (손으로 닫았다)\n", closed);

    std::printf("(5) reset() 으로 갈아 끼우면\n");
    closed = 0;
    { std::unique_ptr<std::FILE, Closer> up(std::fopen("/dev/null", "wb"));
      up.reset(std::fopen("/dev/null", "wb"));
      std::printf("    reset 직후까지 닫은 횟수 %d\n", closed); }
    std::printf("    블록을 나온 뒤 닫은 횟수 %d\n", closed);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic raii12.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 함수 객체 deleter
    [Closer] fclose 했다
    닫은 횟수 1
(2) 람다 deleter — 블록을 나가면
    [람다] fclose 했다
    닫은 횟수 1
(3) 빈 unique_ptr 을 파괴하면 deleter 가 불리나
    닫은 횟수 0  (deleter 는 아예 불리지 않았다)
(4) release() 로 놓아 주면
    release() 뒤 up 은 비었는가: 1
    Closer 가 불린 횟수 0  (손으로 닫았다)
(5) reset() 으로 갈아 끼우면
    [Closer] fclose 했다
    reset 직후까지 닫은 횟수 1
    [Closer] fclose 했다
    블록을 나온 뒤 닫은 횟수 2
```

**왜 그런가**

| 타입 | `sizeof` | 왜 |
|---|---|---|
| `FILE*` | 8 | 기준 |
| `MyFile`(직접 만든 것) | ★ **8** | 멤버가 포인터 하나뿐 |
| `unique_ptr<FILE, FileCloser>` | ★★ **8** | ★★★ **상태 없는 함수 객체는 자리를 안 차지한다** |
| `unique_ptr<FILE, decltype(람다)>` | ★★ **8** | 상태 없는 람다도 같다 |
| `unique_ptr<FILE, int(*)(FILE*)>` | ★★★ **16** | ★★★ **함수 포인터는 「값」이라 8바이트를 들고 다닌다** |
| `shared_ptr<int>` | ★ **16** | 제어 블록 포인터가 하나 더 |
| `lock_guard<mutex>` | 8 | 참조 하나 |
| `unique_lock<mutex>` | ★ **16** | **푼 상태를 기억한다**(그래야 `wait()` 가 성립한다) |

- ★★★ **큰 쪽이 없다 — 같다.** RAII 래퍼가 **원시 포인터보다 커지지 않는다.**
- ★★★ **두 배가 되는 딱 한 자리는 deleter 를 함수 포인터로 줄 때**다.\
  **상태 없는 클래스는 빈 클래스 최적화로 0바이트**가 되는데, **함수 포인터는 저장해야 할 값**이다.\
  ★ **그래서 deleter 는 함수 포인터 말고 함수 객체나 람다로 준다.**
- ★★★ **빈 `unique_ptr` 을 파괴하면 deleter 가 아예 안 불린다**(`닫은 횟수 0`).\
  `Closer` 안의 `else` 가지가 **한 줄도 안 찍혔다** — 5번의 「빈 껍데기」를 **표준이 대신 처리해 주는 것**이다.
- ★★ **`release()` 는 deleter 를 0회 부른다**(소유권만 놓는다 — 손으로 닫아야 한다).\
  **`reset()` 은 그 자리에서 1회 부르고**, 블록을 나오며 한 번 더 불러 **총 2회**가 된다.

### 8. ★★★ 분기는 RAII 판이 **가장 많다** — 줄어드는 것은 **소스의 해제 호출**이다

**출력 — 소스**

```text
===== 소스: raii09.cpp =====
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

**출력 — 소스 쪽 세기**

```text
===== echo "with_goto 함수 본문 줄 수(빈 줄 제외) $(awk "/^int with_goto/,/^}/" raii09.cpp | grep -c .)" (exit=0) =====
with_goto 함수 본문 줄 수(빈 줄 제외) 21
===== echo "with_dup  함수 본문 줄 수(빈 줄 제외) $(awk "/^int with_dup/,/^}/" raii09.cpp | grep -c .)" (exit=0) =====
with_dup  함수 본문 줄 수(빈 줄 제외) 13
===== echo "with_raii 함수 본문 줄 수(빈 줄 제외) $(awk "/^int with_raii/,/^}/" raii09.cpp | grep -c .)" (exit=0) =====
with_raii 함수 본문 줄 수(빈 줄 제외) 9
===== echo "Mem·File 두 타입 정의 줄 수(한 번만 적는다) $(awk "/^struct Mem/,/^};/" raii09.cpp | grep -c .) + $(awk "/^struct File/,/^};/" raii09.cpp | grep -c .)" (exit=0) =====
Mem·File 두 타입 정의 줄 수(한 번만 적는다) 7 + 7
===== echo "with_goto 안에 적힌 해제 호출 $(awk "/^int with_goto/,/^}/" raii09.cpp | grep -c "std::free(\|std::fclose(")" (exit=0) =====
with_goto 안에 적힌 해제 호출 3
===== echo "with_dup  안에 적힌 해제 호출 $(awk "/^int with_dup/,/^}/" raii09.cpp | grep -c "std::free(\|std::fclose(")" (exit=0) =====
with_dup  안에 적힌 해제 호출 5
===== echo "with_raii 안에 적힌 해제 호출 $(awk "/^int with_raii/,/^}/" raii09.cpp | grep -c "std::free(\|std::fclose(")" (exit=0) =====
with_raii 안에 적힌 해제 호출 0
===== echo "with_goto 의 라벨 수 $(awk "/^int with_goto/,/^}/" raii09.cpp | grep -cE "^[[:space:]]*out[a-z_]*:")" (exit=0) =====
with_goto 의 라벨 수 3
```

**출력 — `-O2` 어셈블리 세기(예외 켠 판 / 끈 판)**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 -S -masm=intel raii09.cpp -o raii09.s && awk "/^_Z[0-9A-Za-z_.]+:\$/{fn=\$0;sub(\":\",\"\",fn);i=0;j=0;c=0;t=0;f=1;next} f&&/^[ \t]+[a-z]/{i++;if(\$1~/^j/)j++;if(\$1==\"call\")c++;if(\$1~/^(cmp|test)/)t++} f&&/\.cfi_endproc/{printf \"%-22s 명령 %3d   j* %2d   call %2d   cmp+test %2d\n\",fn,i,j,c,t;f=0}" raii09.s (exit=0) =====
_Z9with_gotoPKci       명령  48   j*  6   call  7   cmp+test  3
_Z8with_dupPKci        명령  51   j*  5   call 10   cmp+test  3
_Z9with_raiiPKci       명령  52   j*  7   call  7   cmp+test  3
_Z9with_raiiPKci.cold  명령   8   j*  0   call  4   cmp+test  0
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 -fno-exceptions -S -masm=intel raii09.cpp -o raii09n.s && awk "/^_Z[0-9A-Za-z_.]+:\$/{fn=\$0;sub(\":\",\"\",fn);i=0;j=0;c=0;t=0;f=1;next} f&&/^[ \t]+[a-z]/{i++;if(\$1~/^j/)j++;if(\$1==\"call\")c++;if(\$1~/^(cmp|test)/)t++} f&&/\.cfi_endproc/{printf \"%-22s 명령 %3d   j* %2d   call %2d   cmp+test %2d\n\",fn,i,j,c,t;f=0}" raii09n.s (exit=0) =====
_Z9with_gotoPKci       명령  48   j*  6   call  7   cmp+test  3
_Z8with_dupPKci        명령  51   j*  5   call 10   cmp+test  3
_Z9with_raiiPKci       명령  46   j*  5   call  7   cmp+test  3
===== echo "예외 표(.gcc_except_table) 절 수 : 있는 판 $(grep -c gcc_except_table raii09.s) · 끈 판 $(grep -c gcc_except_table raii09n.s)" (exit=0) =====
예외 표(.gcc_except_table) 절 수 : 있는 판 2 · 끈 판 0
===== echo "되감기 범위 표시(.LEHB) 수       : 있는 판 $(grep -c LEHB raii09.s) · 끈 판 $(grep -c LEHB raii09n.s)" (exit=0) =====
되감기 범위 표시(.LEHB) 수       : 있는 판 9 · 끈 판 0
```

**출력 — 최적화 수준별**

```text
===== for O in -O0 -O1 -O2 -O3 -Os; do g++ -std=c++20 -Wall -Wextra -pedantic $O -S -masm=intel raii09.cpp -o lv.s; echo "== g++ $O =="; awk "/^_Z[0-9A-Za-z_.]+:\$/{fn=\$0;sub(\":\",\"\",fn);i=0;j=0;c=0;f=1;next} f&&/^[ \t]+[a-z]/{i++;if(\$1~/^j/)j++;if(\$1==\"call\")c++} f&&/\.cfi_endproc/{printf \"  %-22s 명령 %3d   j* %2d   call %2d\n\",fn,i,j,c;f=0}" lv.s; done (exit=0) =====
== g++ -O0 ==
  _Z9with_gotoPKci       명령  55   j*  6   call  7
  _Z8with_dupPKci        명령  63   j*  6   call 10
  _ZN3MemC2Em            명령  15   j*  0   call  1
  _ZN3MemD2Ev            명령  12   j*  0   call  1
  _ZN4FileC2EPKcS1_      명령  18   j*  0   call  1
  _ZN4FileD2Ev           명령  16   j*  1   call  1
  _Z9with_raiiPKci       명령  91   j* 10   call 13
== g++ -O1 ==
  _Z9with_gotoPKci       명령  48   j*  6   call  7
  _Z8with_dupPKci        명령  54   j*  6   call 10
  _Z9with_raiiPKci       명령  61   j*  7   call 11
== g++ -O2 ==
  _Z9with_gotoPKci       명령  48   j*  6   call  7
  _Z8with_dupPKci        명령  51   j*  5   call 10
  _Z9with_raiiPKci       명령  52   j*  7   call  7
  _Z9with_raiiPKci.cold  명령   8   j*  0   call  4
== g++ -O3 ==
  _Z9with_gotoPKci       명령  48   j*  6   call  7
  _Z8with_dupPKci        명령  51   j*  5   call 10
  _Z9with_raiiPKci       명령  52   j*  7   call  7
  _Z9with_raiiPKci.cold  명령   8   j*  0   call  4
== g++ -Os ==
  _Z9with_gotoPKci       명령  43   j*  3   call  7
  _Z8with_dupPKci        명령  49   j*  5   call  9
  _Z9with_raiiPKci       명령  60   j*  7   call 11
```

**왜 그런가**

| | `with_goto` | `with_dup` | `with_raii` |
|---|---|---|---|
| 함수 본문 줄(빈 줄 제외) | 21 | 13 | ★ **9** |
| ★★★ **소스에 적힌 해제 호출** | **3** | **5** | ★★★ **0** |
| 라벨 | 3 | 0 | 0 |
| `-O2` 명령 | 48 | 51 | 52 (+ `.cold` 8) |
| ★★★ **`-O2` 분기 `j*`** | 6 | ★ **5** | ★★★ **7** |
| `-O2` `call` | 7 | ★ **10** | 7 (+ `.cold` 4) |
| ★★★ **`-O2 -fno-exceptions` 명령** | 48 | 51 | ★★★ **46** |

- ★★★ **「RAII 가 분기를 줄인다」는 틀렸다.** `-O2` 에서 **분기가 가장 많은 판이 RAII**(7)다.\
  ★ C 갈래 13번이 `goto` 에 대해 **똑같은 반증**을 냈다 — 거기서도 `goto` 판과 중첩 `if` 판의 분기가 같았다.
- ★★★ **줄어드는 것은 소스의 해제 호출이다** — `goto` 3개 · 중복 5개 → **RAII 0개.**\
  ★ **C 갈래 13번의 결론이 「분기가 아니라 중복을 줄인다」였다면, RAII 는 그 중복을 0으로 만든다.**\
  ★★ 대신 **타입 정의 14줄(`Mem` 7 + `File` 7)을 함수 밖에 한 번** 적는다 — **자원 종류당 한 번**이고, 함수가 늘어도 안 는다.
- ★★★ **`.cold` 조각은 되감기 경로**다(명령 8 · `call` 4). 예외가 날 때만 가는 길이라 컴파일러가 **차가운 구역으로 떼어 놓는다.**
- ★★★ **`-fno-exceptions` 로 던지면 순위가 뒤집힌다** — RAII 판이 **46 으로 셋 중 가장 작다**(`goto` 48 · 중복 51).\
  `.cold` 도 사라진다. ★★ 그러니 `-O2` 의 +4 와 `.cold` 8 은 「RAII 의 값」이 아니라 **「예외 경로의 값」이다**.
- ★★ **`.gcc_except_table` 은 예외 켠 판 2절 · 끈 판 0절**, **`.LEHB` 는 9개 대 0개**다.\
  **RAII 가 사는 것이 정확히 이 표**다.
- ★★ **`-O0` 에서는 RAII 판이 91 로 압도적으로 크고**(게다가 `Mem`·`File` 의 생성자·소멸자가 **함수로 따로 남는다**),\
  **`-Os` 에서도 60 대 43 으로 벌어진다.** **인라인이 되는 수준에서만 같아진다** —\
  ★ C 갈래 13번도 `-O0` 에서 결론이 뒤집혔다. **같은 함정이 같은 자리에서 난다.**
- ★ **C 갈래 13번과 같은 것** — 「관용구가 분기를 줄인다」는 **양쪽 다 반증됐다**, 그리고 **한 최적화 수준만 보면 안 된다.**\
  ★ **다른 것** — 그쪽은 **소스 중복을 줄이는 것**이 값이었고, 여기는 **중복이 0이 되는 데다\
  `goto` 판이 원리적으로 못 덮는 예외 경로까지 덮는다.** 그 대가가 **되감기 표**다.

### 9. ★★ **0건** — 그런데 ASan 은 **48바이트**를 잡는다

**출력**

```text
===== 소스: raii13.cpp =====
// RAII 를 안 쓴 자리 여섯 개를 심었다 — 컴파일러가 몇 군데에서 말하는지 센다
#include <cstdio>
#include <cstdlib>
#include <mutex>
#include <stdexcept>

static std::mutex m;

struct Loose {                       // 1. 복사를 막지 않은 래퍼 — 이중 해제가 열려 있다
    void* p;
    explicit Loose(std::size_t n) : p(std::malloc(n)) {}
    ~Loose() { std::free(p); }
};

struct Half {                        // 2. 잡기만 하고 놓지 않는 소멸자
    std::FILE* f;
    Half() : f(std::fopen("/dev/null", "wb")) {}
    ~Half() {}
};

struct RawInCtor {                   // 3. 생성자에서 손으로 잡다가 던진다
    void* a;
    RawInCtor() : a(std::malloc(32)) { throw std::runtime_error("여기서"); }
    ~RawInCtor() { std::free(a); }
};

void hand_lock(bool boom) {          // 4. 락을 손으로 잡는다
    m.lock();
    if (boom) throw std::runtime_error("여기서");
    m.unlock();
}

void* leak_on_return(bool early) {   // 5. 조기 반환에 해제를 안 달았다
    void* p = std::malloc(16);
    if (early) return nullptr;
    return p;
}

Loose move_then_use() {              // 6. 옮긴 뒤 원본을 다시 읽는다
    Loose a(32);
    Loose b = a;                     // 복사가 열려 있어 둘이 같은 포인터를 든다
    return b;
}

int main() {
    Half h; (void)h;
    try { RawInCtor r; (void)r; } catch (...) {}
    try { hand_lock(true); } catch (...) {}
    (void)leak_on_return(true);
    std::printf("여섯 자리 전부 컴파일됐다\n");
    (void)move_then_use;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic raii13.cpp -o ex (cc exit=0) =====
===== clang++ -std=c++20 -Wall -Wextra -pedantic raii13.cpp -o ex (cc exit=0) =====
```

```text
===== echo "raii13 탐침 여섯  g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic raii13.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
raii13 탐침 여섯  g++ 경고 0
===== echo "raii13 탐침 여섯  clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic raii13.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
raii13 탐침 여섯  clang 경고 0
===== echo "raii13 ASan 을 붙여 돌리면: $(g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raii13.cpp -o exa 2>/dev/null; ./exa >/dev/null 2>asan.txt; grep -c 'ERROR: LeakSanitizer' asan.txt) 건의 누수 리포트" (exit=0) =====
raii13 ASan 을 붙여 돌리면: 1 건의 누수 리포트
===== grep -E '^(Direct|Indirect|SUMMARY)' asan.txt (exit=0) =====
Direct leak of 32 byte(s) in 1 object(s) allocated from:
Direct leak of 16 byte(s) in 1 object(s) allocated from:
SUMMARY: AddressSanitizer: 48 byte(s) leaked in 2 allocation(s).
```

**왜 그런가**

| 심은 것 | g++ | clang | 실제로는 |
|---|---|---|---|
| 복사를 안 막은 래퍼 | 0 | 0 | 이중 해제가 열려 있다(4번) |
| 잡기만 하고 안 놓는 소멸자 | 0 | 0 | 파일 핸들이 샌다 |
| 생성자에서 손으로 잡다가 던짐 | 0 | 0 | ★ **32바이트 누수**(6번) |
| 락을 손으로 잡고 예외 경로 | 0 | 0 | ★★ 락이 잡힌 채 남는다(3번) |
| 조기 반환에 해제를 안 달았다 | 0 | 0 | ★ **16바이트 누수**(2번) |
| 옮긴 뒤 원본을 다시 읽는다 | 0 | 0 | 같은 포인터를 둘이 든다 |

- ★★★ **탐침 여섯 중 답한 것 0, 침묵한 것 6**이다. **`cc exit=0` 에 경고도 0건**이다.
- ★★★ **그 프로그램을 ASan 으로 돌리면 `48 byte(s) leaked in 2 allocation(s)`** 가 나온다\
  (`32` + `16`). **컴파일러가 침묵한 자리에서 sanitizer 가 말한다.**
- ★★ **ASan 이 못 보는 것은 파일 핸들과 락**이다. 그 둘은 **(1)\~(3)의 계수 로그로만** 보인다.
- ★ **컴파일 시간으로 올라오는 것은 하나뿐이다 — 복사 차단**(`= delete`, 4번·(문법)의 금지 사례).\
  **그래서 래퍼를 만들 때 가장 먼저 해야 하는 결정**이다.

### 10. 다른 주제와 잇기

- **RAII 가 성립하는 유일한 근거**는 [14번](../14-destructors-and-deterministic-destruction/) **(2)의 되감기**다 —\
  「예외가 지나가도 지역 객체의 소멸자가 전부 돈다」. 그 보장이 없으면 이 주제 전부가 희망이 된다.
- 「**소멸자를 적었으면 복사도 결정하라**」의 정본은 [목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/)(0/3/5의 법칙)이고,\
  실측은 [13번](../13-constructors-member-init-list-and-delegating/) (7)에 있다.
- **`unique_ptr` 은 26번 · `shared_ptr` 은 27번 · `weak_ptr` 과 순환 참조는 28번 주제**다.\
  ★ 7번은 그중 **`sizeof` 와 deleter 동작만** 본 것이다.
- ★★ **[13번](../13-constructors-member-init-list-and-delegating/) (4)와 여기 6번은 같은 규칙**이다 —\
  기준은 「**생성자가 완주했나**」 하나다. 위임 생성자는 **본체가 완주한 시점**에 객체가 지어진 것이 되어\
  그 뒤 본문에서 던지면 **소멸자가 돌고**, 여기 6번은 **완주 전에 던져서 안 도는 것**이다.
- ★★ **러스트의 `Drop`** 은 **「빈 껍데기를 손으로 만드는 수고」를 없앤다** —\
  이동한 값은 **원본 자리에서 `drop` 되지 않는다**는 것을 컴파일러가 강제하므로\
  5번의 `o.p = nullptr` 과 「널을 견디는 소멸자」가 **필요 없어진다.**\
  Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **9번**([`09-copy-clone-and-drop/`](../../../rust/syntax/09-copy-clone-and-drop/))이 정본이다.
- ★ **GC 가 있는 언어**는 **소멸자가 아니라 문법 한 줄**로 푼다 — `using`/`IDisposable`.\
  C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **37번 주제**가 정본이고,\
  왜 그런 것이 따로 필요한지는 [14번](../14-destructors-and-deterministic-destruction/)의 「한눈에」 그림에 있다.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `raii01.cpp` 래퍼 셋 | g++ 1회(3경로) | ★★★ **세 판 모두 살아 있는 자원 0** · 놓음 로그 동일 |
| `raii02.cpp` 손으로 | g++ 1회 + ASan 1회 | ★★★ **0 · 3 · 6** · ASan **128바이트 · 2객체** |
| `raii03.cpp` `mutex` | g++ 1회 | ★★ `hand` 예외 판만 **락이 잡힌 채** · `sizeof(lock_guard)=8` |
| `raii04.cpp` 복사 | ASan 1회 | ★★★ `[놓음]` **2줄** · **`double-free`** · `run exit=1` |
| `raii05.cpp` 이동 전용 | g++ 1회 | ★★ `free` **1회** · 원본은 **빈 껍데기로 파괴** · 반환 판은 `[놓음]` **1줄** |
| `raii06.cpp` 복사 차단 | g++ 1회 | **에러 3건**(복사 생성·복사 대입·값 전달) |
| `raii07.cpp` 표준 래퍼 | g++ 1회(9줄) | ★★★ **전부 8바이트** · **함수 포인터 deleter 만 16** |
| `raii08.cpp` 생성자 실패 | g++ 1회 + ASan 1회 | ★★★ `~Raw` **0회**(8바이트 누수) · `Wrapped` 멤버 **2개 역순 파괴**(누수 0) |
| `raii09.cpp` 세 판 비교 | g++ **7회**(`-O0`\~`-Os` 5 + `-fno-exceptions` 1 + 세기 1) | ★★★ 해제 호출 **3·5·0** · `-O2` 분기 **6·5·7** · `-fno-exceptions` 명령 **48·51·46** |
| `raii11.cpp` 형태 | g++ 1회 | `a.size()=0  b.size()=64` |
| `raii12.cpp` deleter | g++ 1회(5판) | ★★ 빈 것에는 **0회** · `release()` **0회** · `reset()` **2회** |
| `raii13.cpp` 탐침 여섯 | g++ · clang 각 1회 + ASan 1회 | ★★★ **경고 0 · 0** · ASan **48바이트 · 2할당** |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · libstdc++ · ASan)에서만** 그렇다.

- ★★★ **(8)의 수치 전부** — 명령·분기·`call` 개수 · `.cold` 조각의 존재 · `.gcc_except_table` 2절 · `.LEHB` 9개 · 최적화 수준별 표.
- ★★ **`sizeof` 값 전부** — 빈 클래스 최적화가 되는 것도, `shared_ptr` 이 16인 것도 **이 구현의 선택**이다.
- ★★ **`-fno-exceptions` 는 표준이 아니라 GCC·clang 의 확장**이다.
- ★ **ASan 리포트의 PID·주소·`SUMMARY` 의 소스 경로** · **진단 문구 전부** · `run exit=1`(ASan `ABORTING`).
- ★ **5번 `(2)` 에서 이동이 아예 안 일어난 것** — 복사 생략의 범위는 **미명시**다.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **되감기에서 지역 객체의 소멸자가 전부 도는** 것 — 1번·3번이 여기에 서 있다.
- **잡은 역순으로 놓이는** 것(= 선언 역순 파괴).
- **`= delete` 한 복사를 쓰면 컴파일 에러**인 것 — 값 전달도 포함해서.
- **이동한 원본도 파괴되는** 것 — 그래서 **빈 껍데기를 안전하게 만들어야** 한다.
- ★★★ **생성자가 완주하지 못하면 그 객체의 소멸자가 안 돌고, 이미 지어진 멤버·기반은 역순으로 파괴되는** 것.
- **`unique_ptr` 이 널이면 deleter 를 안 부르는** 것 · **`release()` 가 deleter 를 안 부르는** 것.

**UB 의 결과라 보장이 아닌 것**(관찰로만 읽는다)

- ★★ **4번의 이중 해제.** 근거로 쓰는 것은 「**`[놓음]` 이 두 줄이다**」와 「**ASan 이 `double-free` 라고 불렀다**」뿐이다.
- ★ **누수는 UB 가 아니다.** 표준은 「자원을 놓아라」라고 명령하지 않는다 —\
  그래서 2번·6번·9번의 누수는 **어떤 컴파일러도 에러로 만들지 않는다.** **설계로만 막는다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **`-std=c++98`·`c++11`·`c++17` 판**(전부 `-std=c++20`) ·\
  ★ **clang 으로 (8)의 어셈블리**(g++ 로만 쟀다 — 수치는 컴파일러마다 다르다) ·\
  ★ **스레드를 띄워 데드락을 재현하는 판**(3번은 `try_lock()` 으로 대신했다) ·\
  ★ **function-try-block 으로 (6)을 손으로 메우는 판** · ★ **`-fno-elide-constructors`**(5번의 `(2)` 가 달라질 수 있다) ·\
  ★ **`std::scoped_lock` 으로 락 둘을 잡는 판** · ★ **`shared_ptr` 의 제어 블록 할당 횟수**.
- **못 잰 것** — ★★★ **「RAII 가 실행 시간을 얼마나 더 쓰나」.**\
  이 문서가 센 것은 **명령·분기·`call` 개수까지**다. **명령 수는 시간이 아니다** —\
  캐시·분기 예측·되감기 경로의 실제 빈도가 전부 빠져 있다. **재려면 벤치마크 하네스가 따로 필요하다.**\
  ★★ **런타임 할당 계수기**도 C++ 표준에 없어, C# 갈래가 바로 묻는 질문을 **ASan 누수 리포트로 바꿔** 물었다.
- ★ 「**부적용인 창**」 — **진단의 `(행,열)`.** RAII 는 **파싱 우선순위가 걸리는 문법이 아니라 타입 설계 관용구**라\
  열로 가를 것이 없다. **「안 쟀다」가 아니라 「잴 것이 없다」다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **(8)의 수치 전부** — GCC 가 인라인·`.cold` 분리 정책을 바꾸면 **표가 통째로 움직인다.**
- ★★ **컴파일러가 (9)의 탐침 중 하나라도 경고하기 시작했는지**(지금은 **여섯 다 0건**).
- ★★ **`sizeof(std::shared_ptr<int>)`·`sizeof(std::unique_lock<std::mutex>)`** — 표준 라이브러리 구현이 바뀌면 움직인다.
- ★ **ASan 이 누수를 보고하는 기본값**(`detect_leaks`) — 꺼지면 2번·6번·9번의 근거가 사라진다.
