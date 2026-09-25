# cpp/syntax/15 — RAII: 자원을 타입으로 묶기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — RAII](https://en.cppreference.com/w/cpp/language/raii) · [cppreference — `std::unique_ptr`](https://en.cppreference.com/w/cpp/memory/unique_ptr) · [cppreference — `std::lock_guard`](https://en.cppreference.com/w/cpp/thread/lock_guard) · [cppreference — 소멸자](https://en.cppreference.com/w/cpp/language/destructor) · [GCC 13 Optimize Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Optimize-Options.html) · [AddressSanitizer](https://github.com/google/sanitizers/wiki/AddressSanitizer)
> **실행 검증** — 이 문서의 모든 출력·진단·어셈블리 수치는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`raii01.cpp` \~ `raii13.cpp`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 배너도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
> ★★★ **ASan 을 붙인 블록은 마커를 `stderr` 로 찍었다.** sanitizer 가 `abort()` 로 죽이면\
> **버퍼에 남은 표준 출력이 통째로 사라지기 때문**이다((4)의 소스에 그렇게 적혀 있다).\
> ★★ **리포트를 자른 블록은 자르는 명령을 배너에 적었다** — 실린 것이 「생략한 일부」가 아니라 「**그 명령의 전체 출력**」이다.
> **버전** — RAII 관용구 자체는 **C++98부터**. **`= delete` 와 이동 생성자는 C++11부터**,\
> `std::unique_ptr`·`std::lock_guard` 도 **C++11부터**다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.
> ★★★ **12 → 13 → 14 → 15 는 한 사슬의 끝이다** — [14번](../14-destructors-and-deterministic-destruction/)이 「**언제 파괴되나**」를 전수로 찍었고,\
> **여기 15 는 「그 시점에 무엇을 얹나」에 답한다.** 이 주제의 모든 것이 **[14번](../14-destructors-and-deterministic-destruction/) (2)의 되감기** 위에 서 있다.
> **경계** — 「**RAII 가 무엇을 못 지우는가**」(UAF·순환 참조)의 논증은 [`c-cpp-csharp.md`](../../../c-cpp-csharp.md)가 정본이고,\
> 여기는 **어떻게 만드나**만 본다.\
> 「`unique_ptr` 의 API 전모」는 목록의 **26번**, 「`shared_ptr`」은 **27번**, 「`weak_ptr` 와 순환」은 **28번**,\
> 「이동 후 상태」는 **17번**, 「0/3/5의 법칙」은 **18번**, 「예외 안전 보장 4단계」는 **52번 주제**가 정본이다.\
> ★ 여기서는 **자원 하나를 감싸는 타입을 직접 써 보는 것**까지다.
> **대비** — ★★★ C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **13번**([`13-goto-cleanup-idiom/`](../../../c/syntax/13-goto-cleanup-idiom/))이 **직접 대비**다.\
> 그쪽은 **소멸자가 없는 언어**가 같은 문제를 라벨로 푸는 법이고, (7)에서 **같은 방식으로 재어 나란히 놓는다.**\
> Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **9번**([`09-copy-clone-and-drop/`](../../../rust/syntax/09-copy-clone-and-drop/))은 **RAII 를 언어가 강제하는 판**이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 리포트의 **PID**(`==1140768==`)·주소·스택 프레임 줄 | ★★★ **살아 있는 자원 개수**(`alive`) — 이 주제의 답 자체다 |
> | 어셈블리의 **레지스터 이름**과 명령 배치 | ★★★ **ASan 이 샌 바이트 수와 객체 수**(`128 byte(s) in 2 object(s)`) |
> | 두 컴파일러의 **진단 문구** · 실행 시간 | ★★ **어셈블리의 명령·분기·`call` 개수** · **예외 표 절 수** |
> | 객체의 주소값 | ★★ **`cc exit`/`run exit`** · **경고 개수** · **소스 줄 수와 해제 호출 개수** |
> | — | ★ **`sizeof`**(래퍼가 원시 포인터보다 커지는가) |

## 한눈에 — 쉽게 말하면

**RAII 는 「빌린 물건을 가방에 넣는 것」이다.** 가방을 놓는 순간 물건이 저절로 반납된다.

도서관에서 책을 빌린다고 하자.\
손에 들고 다니면 **돌아가는 길이 여러 갈래일 때마다** 「반납했나?」를 챙겨야 한다 —\
정문으로 나가든, 옆문으로 나가든, 화재 경보가 울려 뛰어나가든.

대신 **반납구가 달린 가방**에 넣어 두면, 어느 문으로 나가든 가방이 알아서 반납한다.\
**챙길 자리가 하나도 없어진다.**

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 가방에 넣는다 | ★★★ **생성자가 자원을 잡는다** | (1) |
| 가방을 놓으면 반납된다 | ★★★ **소멸자가 놓는다** | (1) |
| 어느 문으로 나가도 된다 | ★★★ **정상·조기 반환·예외 세 경로가 같은 코드로 덮인다** | (1)(2) |
| ★★ **가방을 복사하면 책이 하나인데 반납이 두 번** | ★★ **복사를 막지 않으면 이중 해제** | (4) |
| 가방을 넘겨주는 것은 된다 | ★★ **이동 — 원본은 빈 껍데기가 된다** | (4) |
| ★★★ **가방을 다 못 쌌는데 불이 나면** | ★★★ **생성자에서 던지면 소멸자가 안 돈다** | (6) |
| 도서관이 주는 표준 가방 | ★ **`unique_ptr`·`lock_guard`** | (5) |

> **RAII(Resource Acquisition Is Initialization)** — **자원의 수명을 객체의 수명에 묶는 것**.\
> 예: `{ File f("a.txt"); }` — 블록을 나가는 순간 `~File` 이 `fclose` 한다.

> **이중 해제(double free)** — 같은 자원을 두 번 놓는 것. **UB** 다.\
> 예: (4)에서 포인터만 베껴 간 두 객체가 각자 `free` 를 불렀다.

```text
   손으로                                RAII 로

   잡는다                                 잡는다  (생성자)
     |                                      |
     +-- 정상 경로 ---> 놓는다                +-- 정상 경로 -----+
     |                                      |                  |
     +-- 조기 반환 ---> ??? 빠뜨렸다          +-- 조기 반환 -----+--> 소멸자가
     |                                      |                  |    한 자리에서 놓는다
     +-- 예외     ---> ??? 지나가 버렸다      +-- 예외 ---------+
                                            ^^^^^^^^^^^^^^^^^^
   해제 코드를 경로마다 적어야 한다           경로가 몇 개든 해제 코드는 한 곳이다
```

- ★★★ **이 그림의 오른쪽이 성립하는 유일한 근거가 [14번](../14-destructors-and-deterministic-destruction/) (2)다** —\
  **되감기에서도 소멸자가 전부 돈다**는 것. 그 보장이 없으면 RAII 는 관용구가 아니라 희망이다.

## 이 주제가 답하려는 질문

1. **세 경로(정상·조기 반환·예외)가 정말 한 코드로 덮이나** — **수로** 보일 수 있나((1)(2)(3)).
2. **래퍼를 쓸 때 무엇을 막아야 하나** — 복사? 이동? **막으면 무엇이 달라지나**((4)).
3. **RAII 가 안 되는 자리는 어디인가**((6)).
4. **그 값을 무엇으로 치르나** — C 의 `goto cleanup` 과 **나란히 재면 어떻게 갈리나**((7)).

## 동작 방식

### (0) 이 주제가 쓰는 네 창

「해제가 정말 됐나」는 눈에 안 보인다. 창 넷을 갈라 쓴다.

```text
① 자원 계수 로그          살아 있는 자원이 몇 개인가             (1)(2)(3)(4)(5)
② ASan 리포트             샌 바이트와 객체 수 · 이중 해제        (2)(4)(6)(8)
③ 컴파일 진단             복사를 막으면 무엇이 컴파일에서 걸리나  (4)(8)
④ 어셈블리 세기            명령·분기·call·예외 표 개수           (7)
```

- ★★★ **주력 창은 ①이다.** 「RAII 가 낫다」를 **말로 하면 어디까지 참인지 모른다** — **세면 안다.**\
  (1)(2)는 같은 함수를 **세 경로로 세 번** 돌려 **`alive` 개수**를 찍는다.
- ★★ **네 번째 창은 ④다.** C 갈래 13번이 **같은 창으로 결론을 냈고**, (7)에서 **그 방식을 그대로 이어받아** 잰다.\
  ★ 다만 **결론은 그쪽과 다르다** — 거기는 「분기가 아니라 중복을 줄인다」였고, 여기는 **중복이 아예 0이 되는 대신 되감기 표를 산다**이다.
- ★★★ **②가 없으면 (2)(6)은 「출력이 이상하다」에서 멈춘다.** `alive` 개수는 **내가 센 것**이고,\
  **ASan 의 `Direct leak of 128 byte(s) in 2 object(s)` 는 할당기가 센 것**이다. 둘을 갈라 봐야 한다.
- ★ 「**부적용인 창**」 — **진단의 `(행,열)`.** RAII 는 **파싱 우선순위가 걸리는 문법이 아니라 타입 설계 관용구**라\
  열로 가를 것이 없다. **「안 쟀다」가 아니라 「잴 것이 없다」다.**
- ★★ **「못 잰 것」은 또 다르다** — **런타임 할당 계수기**가 C++ 표준에 없다.\
  C# 갈래가 `GC.GetAllocatedBytesForCurrentThread()` 로 바로 묻는 것을, 여기서는 **ASan 의 누수 리포트**로 바꿔 물었다.\
  **같은 질문에 다른 창을 쓴 것**이지 안 물어본 것이 아니다.

### (1) ★★★ 자원 셋을 타입으로 묶으면 — 세 경로가 같은 코드로 덮인다

**언제 쓰나** — 함수 하나가 자원을 둘 이상 잡을 때마다. **이 절이 이 주제의 중심이다.**

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

| mode | 어떻게 나가나 | 놓음 로그 | 살아 있는 자원 | 플래그 |
|---|---|---|---|---|
| 0 | 끝까지 간다 | 플래그 → 파일 → 메모리 | ★ **0개** | 풀림 |
| 1 | ★ **조기 반환** | 플래그 → 파일 → 메모리 | ★ **0개** | 풀림 |
| 2 | ★★ **예외** | 플래그 → 파일 → 메모리 | ★★★ **0개** | 풀림 |

- ★★★ **세 경로의 놓음 로그가 한 글자도 같다.** 「비슷하다」가 아니라 **같다.**\
  해제 코드는 **소멸자 셋에 한 번씩** 적혀 있고, 함수 본문에는 **한 줄도 없다.**
- ★★★ **놓는 순서는 잡은 역순**이다(플래그 → 파일 → 메모리). [14번](../14-destructors-and-deterministic-destruction/) (1)의 규칙이 **그대로 자원 관리 규칙**이 된다 —\
  **나중에 잡은 것이 먼저 풀린다**는 것이 **락 순서·의존 순서와 정확히 맞는다.**
- ★★ **예외 판에서 `[catch]` 가 놓음 로그 뒤에 찍혔다** — 되감기가 먼저 끝난다([14번](../14-destructors-and-deterministic-destruction/) (2)).
- ★ **세 래퍼가 전부 복사를 `= delete` 로 막았다** — 왜 그래야 하는지는 (4).

**비용** — 타입 하나당 **생성자·소멸자·복사 차단 네 줄**. 그 값은 (7)에서 잰다.

### (2) ★★★ 손으로 잡고 놓으면 — 세 경로 중 둘이 샌다

**언제 쓰나** — (1)을 안 쓴 코드를 읽을 때. **똑같은 일을 똑같은 순서로 하는데 결과가 다르다.**

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

| mode | 어떻게 나가나 | 놓음 로그 | 살아 있는 자원 | 플래그 |
|---|---|---|---|---|
| 0 | 끝까지 간다 | 셋 다 | 0개 | 풀림 |
| 1 | ★★ **조기 반환** | ★★★ **없다** | ★★★ **3개** | ★★ **잡힘** |
| 2 | ★★★ **예외** | ★★★ **없다** | ★★★ **6개**(앞판의 3개가 남아 있다) | ★★ **잡힘** |

- ★★★ **조기 반환 한 줄에 자원 셋이 통째로 샌다.** `return -1;` 앞에 해제 세 줄을 **적어야 하는데 안 적었다.**
- ★★★ **예외 판은 더 나쁘다** — `alive` 가 **6**이다. 앞 판에서 샌 3개가 **그대로 쌓여 있다.**\
  ★ **이것이 계수기를 두는 이유다.** 「이번 판에서 3개가 샜다」가 아니라 「**쌓인다**」가 보인다.
- ★★ **플래그(= 락 흉내)가 잡힌 채로 남았다.** 메모리 누수보다 이쪽이 **더 빨리 죽는 사고**다 — (3)에서 진짜 `mutex` 로 던져 본다.

★★ **ASan 은 「내가 센 것」과 다른 것을 센다.**

```text
===== g++ -std=c++20 -Wall -Wextra -fsanitize=address -g -ffile-prefix-map="$PWD"=. raii02.cpp -o exa && ./exa | grep -E '^(==|SUMMARY|Direct|Indirect)' (cc exit=0 · run exit=1) =====
=================================================================
==1330338==ERROR: LeakSanitizer: detected memory leaks
Direct leak of 128 byte(s) in 2 object(s) allocated from:
SUMMARY: AddressSanitizer: 128 byte(s) leaked in 2 allocation(s).
```

- ★★★ **`Direct leak of 128 byte(s) in 2 object(s)`** — `malloc(64)` 두 번이다.\
  ★ **`alive` 는 6이라고 했는데 ASan 은 2라고 한다** — **세는 대상이 다르다.**\
  `alive` 는 **메모리·파일·플래그를 전부 센 것**이고, ASan 은 **힙 할당만** 센다.\
  **파일 핸들과 락은 ASan 이 안 본다.**
- ★★ **그래서 두 창이 다 필요하다.** 「128바이트가 샜다」만 보면 **락이 잡힌 채라는 사실이 통째로 빠진다.**

**비용** — 손으로 놓는 판은 **경로 하나가 늘 때마다 해제 코드를 한 벌 더** 적어야 한다. (7)에서 그 개수를 센다.

### (3) ★★ `lock_guard` 없이 `mutex` 를 직접 쓰면

**언제 쓰나** — 임계 구역을 쓸 때. **RAII 를 안 쓰면 「데드락」으로 나타난다.**

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

| 함수 | 예외 없음 | 예외 있음 |
|---|---|---|
| `hand()` — `lock()`/`unlock()` 직접 | 락이 풀려 있다 | ★★★ **락이 아직 잡혀 있다** |
| `guarded()` — `lock_guard` | 락이 풀려 있다 | ★★ **락이 풀려 있다** |

```text
   hand(true)                              guarded(true)

   by_hand.lock();                         lock_guard g(by_guard);   <- 생성자가 잡는다
   if (boom) throw;   ----+                if (boom) throw;   ----+
   by_hand.unlock();      |  ★ 지나갈                            |
   ^^^^^^^^^^^^^^^^^      |    길이 없다   }  <- ~lock_guard ◄---+  ★ 되감기가 부른다
                          v                                          -> 락이 풀린다
                     락이 잡힌 채 남는다
```

- ★★★ **예외 한 번에 락이 영구히 잡힌다.** `by_hand.unlock()` 은 `throw` **다음 줄**이라 **지나갈 길이 없다.**\
  ★ 다음에 이 락을 기다리는 스레드는 **영원히 기다린다** — 누수와 달리 **프로그램이 멈춘다.**
- ★★ **`lock_guard` 는 예외 판에서도 풀었다.** 그 이유가 (1)과 한 글자도 같다 — **되감기가 소멸자를 부른다.**
- ★ **`sizeof(std::lock_guard<std::mutex>) = 8`** — **참조 하나**뿐이다. 「RAII 는 객체가 하나 더 생겨 무겁다」가\
  **여기서는 참이 아니다.** (5)에서 표준 래퍼들의 크기를 전수로 잰다.
- ★ **이 절은 락을 「풀렸나」로만 본다** — `try_lock()` 이 성공하면 풀린 것이다.\
  **스레드를 띄워 데드락을 실제로 재현하지는 않았다**(그러면 이 문서가 멈춘다).

**비용** — `lock_guard` 는 **참조 하나**. 실행 비용은 **재지 않았다.**

### (4) ★★ 복사를 막아야 하는 것 — 막으면 무엇이 달라지나

**언제 쓰나** — 래퍼를 만들 때마다. **가장 먼저 결정해야 하는 것**이다.

★★★ **복사를 막지 않으면 이중 해제다.**

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

```text
   복사를 안 막으면                        복사를 막고 이동만 열면

   a.p ──┐                                a.p ── nullptr   (빈 껍데기)
         ├──> [ 32바이트 ]                                 [ 32바이트 ]
   b.p ──┘        ^                       b.p ─────────────────┘
                  |
   ~a 가 free · ~b 가 또 free              ~a 는 "놓을 것이 없다" · ~b 만 free
   -> ★ double-free                        -> ★ free 호출 1회
```

- ★★★ **`두 객체가 같은 주소를 든다: 1`** — 컴파일러가 만든 복사 생성자는 **포인터를 베끼기만** 한다.
- ★★★ **`[놓음] Loose` 가 두 줄**이고, 그다음 ASan 이 **`double-free`** 로 죽인다(`run exit=1`).\
  ★ [14번](../14-destructors-and-deterministic-destruction/) (5)(6)의 `new-delete-type-mismatch`·`bad-free` 와 **또 다른 이름**이다.
- ★★ **컴파일은 아무 말도 안 했다** — `cc exit=0`, 경고 0건. **소멸자를 적었는데 복사를 안 막은 것**이\
  **0/3/5의 법칙**(목록의 **18번 주제**)이 말하는 바로 그 자리다.

★★ **복사를 막고 이동만 열면.**

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

- ★★★ **`free` 가 정확히 한 번**이다. 옮긴 뒤 원본은 **`[놓음] 빈 껍데기 — 놓을 것이 없다`** 를 찍는다.
- ★★★ **원본의 소멸자는 여전히 돈다** — **파괴가 사라지는 것이 아니라 「놓을 것이 없어지는」 것**이다.\
  ★★ **그래서 이동 생성자에서 `o.p = nullptr` 을 해야 하고, 소멸자가 널을 견뎌야 한다.**\
  ★ 러스트는 이 자리를 언어가 막는다 — Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **9번**([`09-copy-clone-and-drop/`](../../../rust/syntax/09-copy-clone-and-drop/)).
- ★ **함수에서 돌려받는 판도 `free` 1회**다 — 복사 생략이 있어 **이동조차 안 일어난다.**

★ **막아 두면 복사하려는 코드가 컴파일에서 걸린다.**

```text
===== 소스: raii06.cpp =====
// 복사를 막아 두면 복사하려는 코드가 컴파일에서 걸린다
#include <cstdlib>
struct Tight {
    void* p;
    explicit Tight(std::size_t n) : p(std::malloc(n)) {}
    ~Tight() { std::free(p); }
    Tight(const Tight&) = delete;
    Tight& operator=(const Tight&) = delete;
};
void by_value(Tight t) { (void)t; }
int main() {
    Tight a(32);
    Tight b = a;        // 복사 생성
    Tight c(16);
    c = a;              // 복사 대입
    by_value(a);        // 값으로 넘기기
    (void)b;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic raii06.cpp -o ex (cc exit=1) =====
raii06.cpp: In function ‘int main()’:
raii06.cpp:13:15: error: use of deleted function ‘Tight::Tight(const Tight&)’
   13 |     Tight b = a;        // 복사 생성
      |               ^
raii06.cpp:7:5: note: declared here
    7 |     Tight(const Tight&) = delete;
      |     ^~~~~
raii06.cpp:15:9: error: use of deleted function ‘Tight& Tight::operator=(const Tight&)’
   15 |     c = a;              // 복사 대입
      |         ^
raii06.cpp:8:12: note: declared here
    8 |     Tight& operator=(const Tight&) = delete;
      |            ^~~~~~~~
raii06.cpp:16:13: error: use of deleted function ‘Tight::Tight(const Tight&)’
   16 |     by_value(a);        // 값으로 넘기기
      |     ~~~~~~~~^~~
raii06.cpp:7:5: note: declared here
    7 |     Tight(const Tight&) = delete;
      |     ^~~~~
raii06.cpp:10:21: note:   initializing argument 1 of ‘void by_value(Tight)’
   10 | void by_value(Tight t) { (void)t; }
      |               ~~~~~~^
```

- ★★ **에러 셋이 서로 다른 자리에서 난다** — 복사 생성 · 복사 대입 · **값으로 넘기기.**\
  ★ 세 번째가 중요하다 — `by_value(a)` 는 **복사라고 안 적었는데 복사**다.
- ★ **런타임 사고가 컴파일 에러로 바뀌었다.** 이것이 「복사를 막는다」의 값 전부다.

**비용** — 네 줄(`= delete` 둘 + 이동 둘). **그 대신 UB 하나가 통째로 사라진다.**

### (5) ★ 표준 래퍼와 직접 만든 것

**언제 쓰나** — 「직접 만들까, `unique_ptr` 을 쓸까」에서.

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

| 타입 | `sizeof` | 읽는 법 |
|---|---|---|
| `FILE*`(원시) | 8 | 기준값 |
| `MyFile`(직접 만든 것) | ★ **8** | **원시 포인터와 같다** |
| `unique_ptr<FILE, FileCloser>` | ★★ **8** | **상태 없는 함수 객체는 공짜다** |
| `unique_ptr<FILE, decltype(람다)>` | ★★ **8** | **상태 없는 람다도 공짜다** |
| `unique_ptr<FILE, int(*)(FILE*)>` | ★★★ **16** | **함수 포인터를 들고 다녀야 한다** |
| `unique_ptr<int>` | 8 | 기본 deleter |
| `shared_ptr<int>` | ★ **16** | 제어 블록 포인터가 하나 더 |
| `lock_guard<mutex>` | 8 | 참조 하나 |
| `unique_lock<mutex>` | ★ **16** | **푼 상태를 기억한다** |

- ★★★ **RAII 래퍼가 원시 포인터보다 커지지 않는다** — 직접 만든 것도, `unique_ptr` 도 **8바이트**다.\
  ★ **「객체로 감싸면 무거워진다」는 이 크기에서는 틀렸다.**
- ★★★ **딱 한 자리에서 두 배가 된다 — deleter 를 함수 포인터로 줄 때.**\
  **상태 없는 함수 객체/람다는 빈 클래스 최적화로 0바이트**인데, **함수 포인터는 값이라 8바이트를 차지한다.**\
  ★ **그래서 `unique_ptr` 의 deleter 는 함수 포인터 말고 함수 객체나 람다로 준다.**
- ★ **`shared_ptr` 이 두 배인 것은 제어 블록 포인터 때문**이다 — 정본은 목록의 **27번 주제**.

★ **사용자 정의 deleter 가 정말 불리는지, 빈 것에도 불리는지 던져 봤다.**

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

- ★★★ **빈 `unique_ptr` 을 파괴하면 deleter 가 아예 안 불린다**(`닫은 횟수 0`).\
  ★ **`Closer` 안의 `else` 가지는 한 번도 안 찍혔다** — `unique_ptr` 이 **널이면 부르지 않는다.**\
  (4)의 「빈 껍데기」와 **같은 규칙을 표준이 대신 해 주는 것**이다.
- ★★ **`release()` 는 소유권을 놓기만 한다** — deleter 가 **0회**다. 놓은 뒤에는 **손으로 닫아야 한다.**
- ★★ **`reset()` 은 그 자리에서 옛것을 닫는다** — `reset` 직후 이미 1회이고, 블록을 나오며 2회가 된다.
- ★ **람다 deleter 는 `decltype(del)` 로 타입을 적고 생성자에 넘긴다** — 상태가 없어도 **넘겨야 한다.**

**비용** — 상태 없는 deleter 는 **0바이트**. 함수 포인터는 **8바이트**. 실행 비용은 **재지 않았다.**

### (6) ★★★ RAII 가 안 되는 자리 — 생성자가 완주하지 못하면

**언제 쓰나** — 생성자가 자원을 **둘 이상** 잡을 때. **이 주제의 유일한 구멍**이다.

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

```text
   Raw()  : a = new Res("a");  throw;  b = new Res("b");
            ^^^^^^^^^^^^^^^^^  ^^^^^^
            잡았다             던졌다
                                  |
                   ★ ~Raw 는 안 돈다 (생성자가 완주하지 못했다)
                      -> a 가 샌다

   Wrapped { Res a; Res b; }   Wrapped() { throw; }
             ^^^^^^^^^^^^^^    ^^^^^^^^^^^^^^^^^^^
             멤버는 이미 지어졌다   본문에서 던졌다
                                  |
                   ★ ~Wrapped 는 안 돌지만
                      ★★ 이미 지어진 멤버는 역순으로 파괴된다  -> 안 샌다
```

- ★★★ **`[소멸자] ~Raw 가 도나?` 가 한 줄도 안 찍혔다.** **생성자가 끝나지 않은 객체는 파괴되지 않는다** —\
  「아직 태어나지 않았으니 죽일 것도 없다」는 규칙이다.
- ★★★ **그래서 `Raw::a` 가 샌다.** 자원을 **생성자 본문에서 손으로 잡으면** 이 구멍에 빠진다.
- ★★★ **`Wrapped` 는 안 샌다.** `~Wrapped` 는 **똑같이 안 도는데**, **이미 지어진 멤버 `a`·`b` 는 역순으로 파괴된다**\
  (`[놓음] b → [놓음] a`). ★★ **멤버마다 소멸자가 따로 있기 때문**이다.
- ★★ **이것이 「자원 하나 = 타입 하나」 규칙의 진짜 이유다.** 자원 둘을 한 타입이 손으로 들면\
  **생성자 중간 실패에서 반드시 샌다.**
- ★ **[13번](../13-constructors-member-init-list-and-delegating/) (4)의 「위임 뒤 본문에서 던지면 소멸자가 돈다」와 정반대로 보이지만 같은 규칙**이다 —\
  기준은 늘 「**생성자가 완주했나**」이고, 위임 생성자는 **본체가 완주한 시점**에 그것이 참이 된다.

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

- ★★ **ASan 이 `Direct leak of 8 byte(s) in 1 object(s)`** 로 확인해 준다 — `new Res("Raw 의 a")` 하나다.\
  ★ **`Wrapped` 쪽은 한 바이트도 안 샜다.** 같은 프로그램 안에서 **둘이 갈린다.**
- ★ **처방은 셋** — ① 멤버를 RAII 타입으로 만든다(`Wrapped`) ② `unique_ptr` 멤버를 쓴다\
  ③ 생성자 안에서 **try 블록**(function-try-block)으로 직접 되돌린다. ★ **이 문서는 ①만 던져 봤다.**

**비용** — 0. **타입을 더 잘게 쪼개는 것**이 전부다.

### (7) ★★★ C 의 `goto cleanup` 과 나란히 재면

**언제 쓰나** — 「RAII 가 정말 싼가」를 말로 하고 싶을 때.\
★ C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **13번**([`13-goto-cleanup-idiom/`](../../../c/syntax/13-goto-cleanup-idiom/))이 **같은 실험을 C 안에서** 했고, 여기서는 **그 세 번째 칸에 RAII 를 넣는다.**

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

```text
   세 판이 파는 것 (g++ -O2)

   +----------------------+  +----------------------+  +----------------------+
   | with_goto            |  | with_dup             |  | with_raii            |
   |----------------------|  |----------------------|  |----------------------|
   | 함수 21줄            |  | 함수 13줄            |  | 함수 ★ 9줄            |
   | 해제 호출 3곳        |  | 해제 호출 ★ 5곳      |  | 해제 호출 ★★★ 0곳     |
   | 라벨 3개             |  | 라벨 0개             |  | 라벨 0개              |
   | 명령 48 · j* 6       |  | 명령 51 · j* 5       |  | 명령 52 · j* 7        |
   | call 7               |  | call ★ 10            |  | call 7  + .cold 8     |
   +----------------------+  +----------------------+  +----------------------+
        (타입 정의 Mem 7줄 + File 7줄 = 14줄은 with_raii 밖에 한 번만 적는다)

   예외를 끄면(-fno-exceptions)
   with_goto 48 · with_dup 51 · with_raii ★★★ 46   <- RAII 판이 가장 작다
```

그림 해설 (한 단계씩):

- ★★★ **RAII 판의 함수 본문에 해제 호출이 0개다.** `goto` 판은 3개, 중복 판은 5개다.\
  **C 갈래 13번의 결론이 「분기가 아니라 중복을 줄인다」였다면, RAII 는 그 중복을 0으로 만든다.**
- ★★★ **분기는 오히려 RAII 판이 가장 많다**(`j*` 7 대 6 대 5). **「RAII 가 분기를 줄인다」는 틀렸다** —\
  C 갈래 13번이 `goto` 에 대해 반증한 것과 **같은 종류의 반증**이다.
- ★★★ **`-O2` 에서 RAII 판만 `.cold` 조각이 따로 생긴다**(명령 8 · `call` 4).\
  ★ 그것이 **되감기 경로**다 — 예외가 날 때만 가는 길이라 컴파일러가 **차가운 구역으로 떼어 놓는다.**
- ★★★ **`-fno-exceptions` 로 예외를 끄면 RAII 판이 46 으로 셋 중 가장 작아진다**(`goto` 48 · 중복 51).\
  **`.cold` 도 사라진다.** ★★ 그러니까 `-O2` 에서의 +4 와 `.cold` 8 은 「RAII 의 값」이 아니라 **「예외 경로의 값」이다**.
- ★★ **`call` 개수가 소스의 해제 호출 개수를 그대로 따라간다** — 중복 판만 10이다(`goto`·RAII 는 7).\
  **소스에 세 번 적은 해제가 기계어에서도 세 번**이다.

★ **예외 표는 몇 절인가.**

- ★★★ **`.gcc_except_table` 이 2절, 되감기 범위 표시(`.LEHB`)가 9개** 생겼고,\
  **`-fno-exceptions` 판에서는 둘 다 0**이다. **RAII 가 사는 값이 이 표다.**

★ **한 최적화 수준만 보고 단정하면 안 된다.**

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

| 수준 | `with_goto` | `with_dup` | `with_raii` |
|---|---|---|---|
| `-O0` | 55 | 63 | ★★★ **91** (+ 생성자·소멸자 함수 61) |
| `-O1` | 48 | 54 | 61 |
| `-O2` | 48 | 51 | ★ **52** (+ `.cold` 8) |
| `-O3` | 48 | 51 | 52 (+ `.cold` 8) |
| `-Os` | ★ **43** | 49 | ★★ **60** |

- ★★★ **`-O0` 에서는 RAII 판이 압도적으로 크다**(91, 게다가 `Mem`·`File` 의 생성자·소멸자가 **함수로 따로 남는다**).\
  ★★ **인라인이 되어야 비로소 같아진다** — `-O1` 에서 61, `-O2` 에서 52다.
- ★★ **`-Os` 에서는 다시 벌어진다**(60 대 43). **크기를 최적화하면 인라인을 덜 하기 때문**이고,\
  **여기서도 「한 수준만 보고 단정하지 마라」가 그대로 성립한다.**
- ★ **C 갈래 13번도 `-O0` 에서 결론이 뒤집혔다**(거기서는 중첩 `if` 판이 더 작았다). **같은 함정이 같은 자리에서 난다.**

**비용** — **정리하면 이렇다.** RAII 는 **분기를 줄이지 않고**, 최적화가 없으면 **오히려 크다.**\
값은 둘이다 — ★★★ **소스에서 해제 호출이 0이 되는 것**과, ★★★ **C 의 `goto` 판이 원리적으로 못 덮는 예외 경로를 덮는 것**((2)(3)(6)).\
그 대가는 분기도 중복도 아니라 **「되감기 표」다**(`.gcc_except_table` 2절 · `.LEHB` 9개).

### (8) 경고를 누가 보나 — 탐침 여섯

「경고가 안 났다」를 산문으로 적으면 **안 물어본 것과 물었는데 조용한 것이 구분되지 않는다.**\
그래서 **RAII 를 안 쓴 자리 여섯 개**를 한 파일에 심고 두 컴파일러에 똑같이 물었다.

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

| 심은 것 | g++ | clang | 실제로는 |
|---|---|---|---|
| 복사를 안 막은 래퍼 | 0 | 0 | ★★★ 이중 해제가 열려 있다((4)) |
| 잡기만 하고 안 놓는 소멸자 | 0 | 0 | ★★ 파일 핸들이 샌다 |
| 생성자에서 손으로 잡다가 던짐 | 0 | 0 | ★★★ **ASan 이 32바이트 누수로 잡는다**((6)) |
| 락을 손으로 잡고 예외 경로 | 0 | 0 | ★★★ 락이 잡힌 채 남는다((3)) |
| 조기 반환에 해제를 안 달았다 | 0 | 0 | ★★ **ASan 이 16바이트 누수로 잡는다**((2)) |
| 옮긴 뒤 원본을 다시 읽는다 | 0 | 0 | ★ 같은 포인터를 둘이 든다 |

- ★★★ **탐침 여섯 중 답한 것 0, 침묵한 것 6이다.** **`cc exit=0` 에 경고도 0건**이다.
- ★★★ **그런데 ASan 은 그 프로그램에서 `48 byte(s) leaked in 2 allocation(s)` 를 잡았다.**\
  **컴파일러가 침묵한 자리에서 sanitizer 가 말한다** — 이 주제에서 **도구를 하나만 쓰면 안 되는 이유**다.
- ★★ **ASan 도 다 보지는 못한다** — 잡힌 것은 **힙 할당 둘**이고, **파일 핸들과 락은 안 잡혔다.**\
  ★ 그 둘은 **(1)(3)의 계수 로그로만** 보인다.

## 문법 — 형태와 규칙

### 형태

```cpp
/* raii11.cpp */
// RAII 래퍼 한 벌의 형태 — 이 파일은 그대로 컴파일된다
#include <cstdio>
#include <cstdlib>
#include <new>
#include <utility>

class Buffer {                                       // 자원 하나 = 타입 하나
public:
    explicit Buffer(std::size_t n) : p_(std::malloc(n)), n_(n) {   // ① 생성이 곧 획득
        if (!p_) throw std::bad_alloc();
    }
    ~Buffer() { std::free(p_); }                                   // ② 파괴가 곧 해제 (p_ 가 널이어도 안전)

    Buffer(const Buffer&)            = delete;                     // ③ 복사는 막는다
    Buffer& operator=(const Buffer&) = delete;

    Buffer(Buffer&& o) noexcept : p_(o.p_), n_(o.n_) {             // ④ 이동은 「빈 껍데기」를 남긴다
        o.p_ = nullptr; o.n_ = 0;
    }
    Buffer& operator=(Buffer&& o) noexcept {
        if (this != &o) { std::free(p_); p_ = o.p_; n_ = o.n_; o.p_ = nullptr; o.n_ = 0; }
        return *this;
    }

    void*       data()  const noexcept { return p_; }              // ⑤ 안쪽을 빌려 주기만 한다
    std::size_t size()  const noexcept { return n_; }

private:
    void*       p_;
    std::size_t n_;
};

int main() {
    Buffer a(64);
    Buffer b = std::move(a);
    std::printf("a.size()=%zu  b.size()=%zu\n", a.size(), b.size());
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic raii11.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a.size()=0  b.size()=64
```

### 규칙

- **생성자가 잡고 소멸자가 놓는다.** 그 사이에 **해제 코드를 한 줄도 적지 않는다.**
- **자원 하나 = 타입 하나.** 둘을 한 타입이 손으로 들면 **생성자 중간 실패에서 샌다**((6)).
- **복사를 막는다**(`= delete`). 안 막으면 **컴파일러가 만든 얕은 복사가 이중 해제**를 만든다((4)).
- **이동을 열면 원본은 「빈 껍데기」로 만든다.** 원본의 소멸자는 **여전히 돌기 때문**이다((4)).
- **소멸자는 널을 견뎌야 한다**(`free(nullptr)`·`if (f)`). 이동한 원본이 그 자리로 온다.
- **소멸자에서 던지지 않는다** — `std::terminate` 다([14번](../14-destructors-and-deterministic-destruction/) (7)).
- **안쪽을 빌려 주기만 한다**(`data()`·`get()`). **소유권을 내주려면 `release()`** 처럼 이름으로 밝힌다.
- **표준이 주는 것이 있으면 그것을 쓴다** — `unique_ptr`·`lock_guard`·`fstream`. 직접 만드는 것은 **표준에 없는 자원**뿐이다.

### 금지 사례 — 세 줄이 각각 막힌다

```text
===== 소스: raii06.cpp =====
// 복사를 막아 두면 복사하려는 코드가 컴파일에서 걸린다
#include <cstdlib>
struct Tight {
    void* p;
    explicit Tight(std::size_t n) : p(std::malloc(n)) {}
    ~Tight() { std::free(p); }
    Tight(const Tight&) = delete;
    Tight& operator=(const Tight&) = delete;
};
void by_value(Tight t) { (void)t; }
int main() {
    Tight a(32);
    Tight b = a;        // 복사 생성
    Tight c(16);
    c = a;              // 복사 대입
    by_value(a);        // 값으로 넘기기
    (void)b;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic raii06.cpp -o ex (cc exit=1) =====
raii06.cpp: In function ‘int main()’:
raii06.cpp:13:15: error: use of deleted function ‘Tight::Tight(const Tight&)’
   13 |     Tight b = a;        // 복사 생성
      |               ^
raii06.cpp:7:5: note: declared here
    7 |     Tight(const Tight&) = delete;
      |     ^~~~~
raii06.cpp:15:9: error: use of deleted function ‘Tight& Tight::operator=(const Tight&)’
   15 |     c = a;              // 복사 대입
      |         ^
raii06.cpp:8:12: note: declared here
    8 |     Tight& operator=(const Tight&) = delete;
      |            ^~~~~~~~
raii06.cpp:16:13: error: use of deleted function ‘Tight::Tight(const Tight&)’
   16 |     by_value(a);        // 값으로 넘기기
      |     ~~~~~~~~^~~
raii06.cpp:7:5: note: declared here
    7 |     Tight(const Tight&) = delete;
      |     ^~~~~
raii06.cpp:10:21: note:   initializing argument 1 of ‘void by_value(Tight)’
   10 | void by_value(Tight t) { (void)t; }
      |               ~~~~~~^
```

- ★ **세 에러가 이 주제의 규칙 하나에 대응한다** — **복사 차단**. 복사 생성 · 복사 대입 · **값으로 넘기기**.
- ★★ **세 번째가 가장 중요하다** — `by_value(a)` 에는 복사라는 글자가 없다. **복사를 막아야 그것이 드러난다.**

## 어디서 틀리나

### 1. ★★★ 「RAII 는 분기를 줄여서 빠르다」

- ★ **틀렸다.** `-O2` 에서 **분기가 오히려 가장 많았다**(`j*` 7 대 6)((7)).
- ★★ 값은 「소스에서 해제 호출이 0이 되는 것」과 **「예외 경로를 덮는 것」이지 분기 절약이 아니다**.

### 2. ★★★ 「소멸자를 적었으니 안전하다」

- ★ **복사를 안 막으면 이중 해제**다((4)). 소멸자를 적는 순간 **복사·이동도 같이 결정해야 한다**(목록의 **18번 주제**).

### 3. ★★★ 「생성자에서 잡으면 소멸자가 놓아 준다」

- ★ **생성자가 완주하지 못하면 소멸자가 안 돈다**((6)). 자원 둘을 한 생성자에서 손으로 잡으면 **반드시 샌다.**

### 4. ★★ 「옮기면 원본은 사라진다」

- ★ **원본의 소멸자는 여전히 돈다**((4)). **놓을 것이 없어지는 것**이지 파괴가 사라지는 것이 아니다.
- ★ 러스트는 이 자리를 언어가 막는다 — 같은 이름(`move`)이지만 **보장이 다르다.**

### 5. ★★ 「객체로 감싸면 무거워진다」

- ★ **`sizeof` 가 원시 포인터와 같다**((5)). **딱 한 자리에서만 두 배가 된다** — deleter 를 **함수 포인터**로 줄 때.

### 6. ★★ 「최적화가 알아서 없애 준다」

- ★ **`-O0` 에서 RAII 판이 91 명령으로 가장 컸고, `-Os` 에서도 60 대 43 으로 벌어졌다**((7)).\
  **인라인이 되는 수준에서만 같아진다.**

### 7. ★★ 「컴파일러가 경고해 주겠지」

- ★ **탐침 여섯 중 여섯이 침묵했다**((8)). **ASan 을 붙여야 절반이 보이고, 나머지 절반은 계수 로그로만 보인다.**

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★ 이 주제는 「표준」 칸이 **관용구의 뼈대를 통째로 덮는다** — RAII 가 성립하는 이유가 전부 표준이다.\
★★★ **대신 「구현 정의」 칸에 이 주제의 수치가 전부 몰려 있다**((7)의 어셈블리).

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **본체** — **되감기에서 소멸자가 전부 돈다**((1)(2)) · **잡은 역순으로 놓인다**((1)) · **`= delete` 가 복사를 컴파일에서 막는다**((4)) · **이동한 원본도 파괴된다**((4)) · ★★★ **생성자가 완주하지 못하면 소멸자가 안 돌고, 이미 지어진 멤버는 파괴된다**((6)) · **`unique_ptr` 이 널이면 deleter 를 안 부른다**((5)) | 계수 로그 · 진단 전문 + `cc exit` | ★★★ 「**이 함수가 자원을 놓았나**」 — 계수기를 심지 않으면 안 보인다((8)) |
| **조건부 표준** | 특정 조건에서만 보장 | ★ **`= delete`·이동 생성자·`unique_ptr`·`lock_guard` 는 C++11부터** · `-fno-exceptions` 는 **표준이 아니라 구현 확장**이다((7)) | `-std=c++20` 으로만 돌렸다 | ★ **C++98 판으로는 안 돌려 봤다**(그 판에는 이동이 없다) |
| **구현 정의** | 문서화 의무가 있다 | ★★★ **(7)의 수치 전부** — 명령·분기·`call` 개수 · `.cold` 조각의 존재 · `.gcc_except_table` 2절 · `.LEHB` 9개 · **최적화 수준별 표** · **`sizeof` 가 8인 것**(빈 클래스 최적화) · 진단 문구 | `-S -masm=intel` 로 다섯 수준 · `sizeof` 출력 | ★★ **다른 ABI·다른 컴파일러에서는 다른 수가 나온다** |
| **미명시** | 몇 가지 중 하나 | ★ **복사 생략이 어디까지 일어나나**((4)의 `make()` 판에서 이동조차 안 일어났다) | `free` 호출 횟수 | ★ **`-fno-elide-constructors` 판은 안 돌려 봤다** |
| **UB** | 아무 일이나 | ★★ **둘이다** — ① 이중 해제((4)) ② **누수는 UB 가 아니다** — 표준은 「자원을 놓아라」라고 명령하지 않는다((2)(6)) | ASan 리포트 이름 · 누수 바이트 수 | ★★★ **누수는 어떤 컴파일러도 에러로 만들지 않는다 — 설계로만 막는다** |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | ASan | 계수 로그 |
|---|---|---|---|---|---|
| 복사를 `= delete` 로 막은 뒤 복사 시도 | 표준 | **error** | **error** | — | — |
| 복사를 **안 막은** 래퍼 | 표준 | ★★★ **0건** | ★★★ **0건** | ★ **`double-free`** | ★ 놓음 2줄 |
| 조기 반환에서 메모리 누수 | — | ★★★ **0건** | ★★★ **0건** | ★ **잡는다** | ★ 잡는다 |
| ★★ **조기 반환에서 파일·락 누수** | — | ★★★ **0건** | ★★★ **0건** | ★★★ **못 본다** | ★★★ **계수 로그만** |
| 생성자 중간 실패 누수 | 표준 | ★★★ **0건** | ★★★ **0건** | ★ **잡는다** | ★ 잡는다 |
| 해제 호출이 소스에 몇 번 적혔나 | — | 0건 | 0건 | — | ★★ **세기 블록만**((7)) |

- ★★ **이 표의 결론 세 줄**
  - **RAII 를 안 쓴 것 자체는 어떤 컴파일러도 경고하지 않는다** — 탐침 여섯이 전부 0건이다.
  - **ASan 은 힙만 본다** — **파일 핸들과 락은 계수 로그로만** 보인다.
  - **복사를 막는 것만이 컴파일 시간으로 올라온다** — 그래서 **가장 먼저 해야 하는 결정**이다.

### ★ 진단이 0줄인 것도 블록으로 받았다

(8)이 그 자리다. **탐침 여섯 중 답한 것 0, 침묵한 것 6**이고 **`cc exit=0`** 이다.\
그 침묵을 메우는 것이 **ASan 의 `48 byte(s) leaked in 2 allocation(s)`** 와 **(1)\~(3)의 계수 로그**다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 메모리 하나 | **`unique_ptr`** | 직접 만들 이유가 없다 — 정본은 목록의 **26번 주제** |
| 락 | **`lock_guard`/`scoped_lock`** | 예외 경로에서 락이 남는다((3)) |
| 파일 | **`std::fstream`** 또는 `unique_ptr<FILE, D>` | 표준에 있는 것을 먼저 |
| 표준에 없는 자원(소켓·핸들·트랜잭션) | ★ **직접 래퍼를 만든다** | (문법)의 형태 그대로 |
| 소유권을 넘긴다 | **이동만 연다** | 복사는 이중 해제((4)) |
| 소유권을 나눈다 | **`shared_ptr`** | 대신 제어 블록 8바이트 — 목록의 **27번 주제** |
| 자원을 둘 이상 잡는 타입 | ★★★ **타입을 쪼갠다** | 생성자 중간 실패에서 샌다((6)) |
| deleter 를 넘긴다 | ★★ **함수 객체나 람다** | 함수 포인터는 `sizeof` 가 두 배((5)) |
| 예외를 끈 코드베이스 | ★ **RAII 를 그대로 쓴다** | `-fno-exceptions` 판이 셋 중 **가장 작았다**((7)) |

- ★ **「직접 만들지 마라」가 기본값이다.** 표준 래퍼가 있으면 그것을 쓰고, **직접 만드는 것은 표준에 없는 자원**뿐이다.

## 핵심 문장

- **RAII 는 자원의 수명을 객체의 수명에 묶는 것**이고, 그것이 성립하는 유일한 근거는 **되감기에서도 소멸자가 돈다**는 보장이다.
- **세 경로(정상·조기 반환·예외)가 한 코드로 덮인다** — 손으로 놓는 판은 그중 둘에서 샜다.
- **복사를 막지 않으면 이중 해제**이고, **이동한 원본도 여전히 파괴된다.**
- **생성자가 완주하지 못하면 소멸자가 안 돈다** — 그래서 **자원 하나 = 타입 하나**다.
- **RAII 는 분기를 줄이지 않는다.** 줄이는 것은 **소스의 해제 호출**(3\~5개 → **0개**)이고, 사는 것은 **예외 경로**다.
- **그 대가는 되감기 표다** — `.gcc_except_table` 2절 · `.LEHB` 9개. 예외를 끄면 RAII 판이 **가장 작아진다.**

## 관련 자료

- [14번](../14-destructors-and-deterministic-destruction/) — **이 주제의 토대.** 되감기·파괴 순서·`noexcept` 가 전부 거기서 증명됐다.
- [13번](../13-constructors-member-init-list-and-delegating/) — **위임 생성자와 「지어진 것」의 경계.** (6)이 그 (4)의 짝이다.
- 형제 [`09번`](../09-rvalue-references-move-and-forward/) — `std::move` 가 무엇인가. (4)의 이동이 거기가 정본.
- 형제 [`10번`](../10-const-correctness/) — 래퍼의 `data() const` 같은 인터페이스 설계.
- [`c-cpp-csharp.md`](../../../c-cpp-csharp.md) — **RAII 가 무엇을 못 지우는가**(UAF·순환). 여기는 **어떻게 만드나**까지.
- 목록의 **18번 주제** — 0/3/5의 법칙. (4)의 「소멸자를 적었으면 복사도 결정하라」의 정본.
- 목록의 **26·27·28번 주제** — `unique_ptr`·`shared_ptr`·`weak_ptr` 의 전모. (5)는 크기만 본 것이다.
- 목록의 **52번 주제** — 예외 안전 보장 4단계. (1)의 「세 경로가 같다」는 **기본 보장**의 실측이다.
- ★★★ C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **13번**([`13-goto-cleanup-idiom/`](../../../c/syntax/13-goto-cleanup-idiom/)) — **직접 대비.**\
  그쪽 결론은 「**분기가 아니라 중복을 줄인다**」였고, (7)이 **그 세 번째 칸에 RAII 를 넣은 것**이다.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **9번**([`09-copy-clone-and-drop/`](../../../rust/syntax/09-copy-clone-and-drop/)) — **`Drop` 은 RAII 를 언어가 강제하는 판**이다.\
  ★ 「이동한 값은 원본에서 `drop` 되지 않는다」가 (4)의 「빈 껍데기를 손으로 만들어야 하는 것」을 없앤다.
- C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **37번 주제** — `IDisposable`/`using`.\
  ★ **GC 가 있는 언어가 같은 문제를 푸는 법**이고, **소멸자가 아니라 문법 한 줄로 푼다.**

## 용어 풀이

> **RAII(Resource Acquisition Is Initialization)** — **자원의 수명을 객체의 수명에 묶는 것.**\
> 예: `{ File f("a.txt"); }` — 블록을 나가는 순간 `~File` 이 `fclose` 한다.

> **자원(resource)** — 잡았으면 놓아야 하는 것. **메모리만이 아니다.**\
> 예: 파일 핸들·락·소켓·DB 트랜잭션·GPU 버퍼. ★ (2)에서 ASan 이 본 것은 **그중 메모리뿐**이었다.

> **이중 해제(double free)** — 같은 자원을 두 번 놓는 것. **UB** 다.\
> 예: (4)에서 포인터만 베껴 간 두 객체가 각자 `free` 를 불러 ASan 이 `double-free` 로 죽였다.

> **이동 전용 타입(move-only type)** — 복사를 `= delete` 하고 이동만 연 타입.\
> 예: `std::unique_ptr` · (4)의 `Tight`.

> **빈 껍데기(moved-from state)** — 이동당한 뒤의 원본. **파괴는 되지만 놓을 것이 없는 상태**다.\
> 예: (4)에서 `o.p = nullptr` 로 만들어 두었고, 소멸자가 널을 보고 아무것도 안 했다.

> **deleter** — `unique_ptr` 이 파괴될 때 부를 것.\
> 예: `unique_ptr<FILE, FileCloser>` — ★ **널이면 아예 안 부른다**((5)).

> **빈 클래스 최적화(empty base optimization)** — 멤버가 없는 클래스를 **0바이트로** 접어 넣는 것.\
> 예: (5)에서 `unique_ptr<FILE, FileCloser>` 가 **8바이트**였다 — deleter 가 자리를 안 차지했다.

> **스택 되감기(stack unwinding)** — 예외가 지나가는 길의 지역 객체를 **역순으로 파괴하는 것**.\
> 예: (1)의 mode=2 에서 자원 셋이 전부 놓였다. 정본은 [14번](../14-destructors-and-deterministic-destruction/) (2).

> **`.gcc_except_table`** — 되감기에 필요한 표가 담기는 어셈블리 절.\
> 예: (7)에서 **2절**이 생겼고 `-fno-exceptions` 판에서는 **0절**이었다.

> **`.cold` 조각** — 컴파일러가 **거의 안 가는 길**을 떼어 따로 모아 둔 코드.\
> 예: (7)에서 `_Z9with_raiiPKci.cold` 가 **되감기 경로**였다(명령 8 · `call` 4).

## 더 들어가면

- **function-try-block** — 생성자 전체를 `try` 로 감싸 (6)의 구멍을 손으로 메우는 문법.\
  이 문서는 **멤버를 RAII 로 만드는 처방만** 던졌다.
- **`std::scoped_lock`(C++17)** — 락 **여럿**을 데드락 없이 한 번에 잡는 RAII. (3)은 하나짜리만 봤다.
- **`std::unique_lock` 과 조건 변수** — 푼 상태를 기억해야 `wait()` 가 성립한다((5)의 16바이트가 그 값이다).
- **`finally` 흉내** — `std::experimental::scope_exit`·`gsl::finally`. **임의의 코드를 소멸자에 얹는 도구**다.
- **예외 안전 보장 4단계와 copy-and-swap** — (1)이 보인 것은 **기본 보장**이고, **강한 보장**은 목록의 **52번 주제**다.
