# cpp/syntax/11 — 매개변수 전달 방식 고르기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·기계어는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **GNU objdump 2.42** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이라 질문 쪽 발췌와 어긋날 수 있다 —\
> 그래서 **출력을 싣는 블록마다 그 출력을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★★ 이 주제의 주력 창은 **복사·이동 생성자 로그**(1·2번)와 **교체한 `operator new`**(3·4·8번)이고,\
> **네 번째 창은 AddressSanitizer**(5번)다.
> **읽는 법** — ASan 리포트의 **주소·PID·`pc`/`bp`/`sp`** 와 기계어 덤프의 **주소·오프셋**은 **흔들리는 칸**이다.\
> 근거로 쓰는 것은 **복사·이동 횟수 · `new` 횟수 · 명령어 열 · 진단 종류 · 종료 코드**다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「몇 배 빠르다」는 문장이 **한 줄도 없다**(7번이 그 이유다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 값 전달은 **lvalue 에서만** 복사한다 — `const&` 는 넷 다 0

**출력**

```text
===== 소스: pass01.cpp =====
// 전달 방식마다 복사·이동이 몇 번 도는지 센다
#include <cstdio>
#include <utility>

static int cp = 0, mv = 0;

struct Probe {
    int id;
    explicit Probe(int i = 0) : id(i) {}
    Probe(const Probe& o) : id(o.id) { ++cp; }
    Probe(Probe&& o) noexcept : id(o.id) { ++mv; }
    Probe& operator=(const Probe& o) { id = o.id; ++cp; return *this; }
    Probe& operator=(Probe&& o) noexcept { id = o.id; ++mv; return *this; }
};

static Probe keep;                                   // 받은 것을 여기 보관한다

void by_value(Probe p)         { keep = std::move(p); }
void by_cref (const Probe& p)  { keep = p; }
void by_rref (Probe&& p)       { keep = std::move(p); }
void by_pair (const Probe& p)  { keep = p; }
void by_pair (Probe&& p)       { keep = std::move(p); }
template <class T> void by_fwd(T&& p) { keep = std::forward<T>(p); }

void read_value(Probe p)        { keep.id += p.id * 0; }
void read_cref (const Probe& p) { keep.id += p.id * 0; }

#define RUN(label, call) do { cp = mv = 0; call; \
    std::printf("  %-34s copy %d · move %d\n", label, cp, mv); } while (0)

int main() {
    Probe lv(1);

    std::puts("[A] 읽기만 한다");
    RUN("read_value(lv)        by value", read_value(lv));
    RUN("read_value(Probe(2))  by value", read_value(Probe(2)));
    RUN("read_cref(lv)         const&", read_cref(lv));
    RUN("read_cref(Probe(2))   const&", read_cref(Probe(2)));

    std::puts("[B] 받아서 보관한다");
    RUN("by_value(lv)          by value", by_value(lv));
    RUN("by_value(Probe(2))    by value", by_value(Probe(2)));
    RUN("by_cref(lv)           const&", by_cref(lv));
    RUN("by_cref(Probe(2))     const&", by_cref(Probe(2)));
    RUN("by_rref(move(lv))     &&", by_rref(std::move(lv)));
    RUN("by_rref(Probe(2))     &&", by_rref(Probe(2)));
    RUN("by_pair(lv)           overloads", by_pair(lv));
    RUN("by_pair(Probe(2))     overloads", by_pair(Probe(2)));
    RUN("by_fwd(lv)            T&&", by_fwd(lv));
    RUN("by_fwd(Probe(2))      T&&", by_fwd(Probe(2)));

    std::printf("(보관소 id=%d)\n", keep.id);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic pass01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[A] 읽기만 한다
  read_value(lv)        by value     copy 1 · move 0
  read_value(Probe(2))  by value     copy 0 · move 0
  read_cref(lv)         const&       copy 0 · move 0
  read_cref(Probe(2))   const&       copy 0 · move 0
[B] 받아서 보관한다
  by_value(lv)          by value     copy 1 · move 1
  by_value(Probe(2))    by value     copy 0 · move 1
  by_cref(lv)           const&       copy 1 · move 0
  by_cref(Probe(2))     const&       copy 1 · move 0
  by_rref(move(lv))     &&           copy 0 · move 1
  by_rref(Probe(2))     &&           copy 0 · move 1
  by_pair(lv)           overloads    copy 1 · move 0
  by_pair(Probe(2))     overloads    copy 0 · move 1
  by_fwd(lv)            T&&          copy 1 · move 0
  by_fwd(Probe(2))      T&&          copy 0 · move 1
(보관소 id=2)
```

**왜 그런가**

`[A]` 네 줄만 떼어 읽는다.

| 호출 | 인자의 범주 | copy | move |
|---|---|---|---|
| `read_value(lv)` | lvalue | ★ **1** | 0 |
| `read_value(Probe(2))` | prvalue | ★★ **0** | 0 |
| `read_cref(lv)` | lvalue | 0 | 0 |
| `read_cref(Probe(2))` | prvalue | 0 | 0 |

- ★★★ **「값 전달은 복사한다」는 반만 맞다.** 복사가 나는 것은 **lvalue 를 줬을 때**뿐이다.
- ★★ **prvalue 를 값으로 받으면 임시가 곧 매개변수가 된다** — 옮길 것이 애초에 없다.\
  C++17 의 **물질화** 규칙이고, 정본은 [목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/)다.
- ★ **`const T&` 는 네 칸 모두 0** 이다 — **읽기만 할 거면 비교가 여기서 끝난다.**\
  ★ 예외는 **`int` 처럼 작은 내장 타입**뿐이고, 그것은 횟수가 아니라 **명령어 열**로 갈린다(6번).
- ★ 계수기를 **호출마다 0으로 되돌린다**(`RUN` 매크로의 `cp = mv = 0;`) — 그래서 **줄마다 그 호출만의 수**다.

### 2. ★★★ 보관하면 답이 갈린다 — `const&` 는 임시도 복사하고, 값 전달만 합이 2다

**출력**

1번과 **같은 블록**의 `[B]` 절이다(위 출력을 다시 읽는다).

**왜 그런가**

| 호출 | 인자의 범주 | copy | move | 합 |
|---|---|---|---|---|
| `by_value(lv)` | lvalue | 1 | 1 | ★★★ **2** |
| `by_value(Probe(2))` | prvalue | 0 | 1 | 1 |
| `by_cref(lv)` | lvalue | 1 | 0 | 1 |
| `by_cref(Probe(2))` | prvalue | ★★★ **1** | 0 | 1 |
| `by_rref(std::move(lv))` | xvalue | 0 | 1 | 1 |
| `by_rref(Probe(2))` | prvalue | 0 | 1 | 1 |
| `by_pair(lv)` | lvalue | 1 | 0 | 1 |
| `by_pair(Probe(2))` | prvalue | 0 | 1 | 1 |
| `by_fwd(lv)` | lvalue | 1 | 0 | 1 |
| `by_fwd(Probe(2))` | prvalue | 0 | 1 | 1 |

- ★★★ **`by_cref(Probe(2))` 가 copy 1** 이다. **훔쳐도 되는 임시를 받아 놓고 복사했다** —\
  `const Probe&` 안에서는 그 값이 **`const` 인 lvalue** 라 이동을 고를 수가 없다.\
  ★ 「`const` 를 `move` 해도 복사가 된다」와 **같은 자리**이고, 정본은 [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)다.
- ★★★ **`by_value(lv)` 만 합이 2** 다 — **매개변수를 만드느라 복사 1**, **멤버로 옮기느라 이동 1**.\
  ★ **복사 횟수는 오버로드 쌍과 같다.** 더 드는 것은 **이동 한 번**이다.
- ★★ **`by_pair` 네 줄과 `by_fwd` 네 줄이 한 칸도 다르지 않다.**\
  `std::forward<T>(p)` 가 하는 일이 「**받은 범주 그대로 넘긴다**」이므로,\
  **전달 참조 하나가 오버로드 두 개와 같은 결과**를 낸다(정본은 [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)).
- ★ **`by_rref` 행이 `std::move(lv)`** 인 이유 — `by_rref(lv)` 는 **컴파일되지 않는다.**\
  `T&&` 는 lvalue 를 못 받는다(묶기 격자의 정본은 [목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/)).
- ★ `Probe` 의 이동은 **`noexcept`** 로 달아 두었다. 컨테이너가 이동 대신 복사로 도는 함정\
  (`vector` 재할당)의 정본은 목록의 **53번 주제**다 — **이 문서는 그 자리를 던지지 않았다.**

### 3. ★★ 값 전달 세터가 오버로드 쌍과 **같은 수**를 낸다 — 코드는 절반

**출력**

```text
===== 소스: pass02.cpp =====
// 싱크 매개변수 — 세터를 세 가지로 짜고 힙 할당 횟수를 센다
#include <cstdio>
#include <cstdlib>
#include <new>
#include <string>
#include <utility>

static int allocs = 0;
void* operator new(std::size_t n) {
    ++allocs;
    void* p = std::malloc(n ? n : 1);
    if (!p) throw std::bad_alloc();
    return p;
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

struct SetCref { std::string v; void set(const std::string& s) { v = s; } };
struct SetPair { std::string v;
                 void set(const std::string& s) { v = s; }
                 void set(std::string&& s) { v = std::move(s); } };
struct SetVal  { std::string v; void set(std::string s) { v = std::move(s); } };

#define LONG "0123456789012345678901234567890123456789"
#define RUN(label, stmt) do { allocs = 0; { stmt; } \
    std::printf("  %-28s new %d회\n", label, allocs); } while (0)

int main() {
    std::string lv = LONG;
    std::puts("인자 세 가지 x 세터 세 가지 (문자열은 40자 — SSO 밖)");
    RUN("SetCref::set(lvalue)",   SetCref t; t.set(lv));
    RUN("SetCref::set(temporary)",     SetCref t; t.set(std::string(LONG)));
    RUN("SetCref::set(literal)",   SetCref t; t.set(LONG));
    RUN("SetPair::set(lvalue)",   SetPair t; t.set(lv));
    RUN("SetPair::set(temporary)",     SetPair t; t.set(std::string(LONG)));
    RUN("SetPair::set(literal)",   SetPair t; t.set(LONG));
    RUN("SetVal::set(lvalue)",    SetVal  t; t.set(lv));
    RUN("SetVal::set(temporary)",      SetVal  t; t.set(std::string(LONG)));
    RUN("SetVal::set(literal)",    SetVal  t; t.set(LONG));
    std::printf("(원본은 그대로 %zu자)\n", lv.size());
}
===== g++ -std=c++20 -Wall -Wextra -pedantic pass02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
인자 세 가지 x 세터 세 가지 (문자열은 40자 — SSO 밖)
  SetCref::set(lvalue)         new 1회
  SetCref::set(temporary)      new 2회
  SetCref::set(literal)        new 2회
  SetPair::set(lvalue)         new 1회
  SetPair::set(temporary)      new 1회
  SetPair::set(literal)        new 1회
  SetVal::set(lvalue)          new 1회
  SetVal::set(temporary)       new 1회
  SetVal::set(literal)         new 1회
(원본은 그대로 40자)
```

**왜 그런가**

| 세터 | lvalue | 임시 | 리터럴 | 세터 코드 |
|---|---|---|---|---|
| `SetCref`(`const&` 하나) | 1 | ★★ **2** | ★★ **2** | 1줄 |
| `SetPair`(`const&` + `&&`) | 1 | 1 | 1 | **2줄** |
| `SetVal`(값 + `std::move`) | 1 | 1 | 1 | ★★★ **1줄** |

- ★★★ **`SetVal` 과 `SetPair` 의 아홉 숫자가 전부 같다.** 그런데 `SetVal` 은 **세터가 한 줄**이다.\
  이것이 「**싱크는 값으로 받아 `std::move` 한다**」는 관용구의 근거다.
- ★★★ **`SetCref` 의 임시·리터럴 열이 2회**인 이유 — **① 임시 `std::string` 을 만들고**\
  **② 그것을 멤버에 복사**한다. `const&` 안에서는 ①을 **훔칠 수가 없다**(2번과 같은 이유).
- ★★ **리터럴 열이 임시 열과 같은 숫자**다. 리터럴을 `const std::string&` 자리에 주면\
  **그 자리에서 임시 `std::string` 이 만들어지기** 때문이다(4번에서 다시 본다).
- ★ **문자열을 40자로 잡은 이유** — 짧으면 **SSO** 에 들어가 **힙을 아예 안 써서** 셀 것이 없다.\
  ★ **40자가 힙으로 간다는 것은 이 구현(libstdc++)에서 확인한 값**이지 표준값이 아니다.
- ★ 값 전달이 **이동 한 번을 더 쓴다**는 것은 2번에서 셌다.\
  ★★ 여기 할당 수가 같은 것은 **`std::string` 의 이동이 할당을 안 하기 때문**이고, **그것도 구현 사실**이다.\
  ★★★ **「그 이동 한 번이 얼마나 손해인가」는 이 문서가 재지 않았다.**

### 4. ★★ 리터럴·`const char*` 에서 `const std::string&` 만 `new` 를 한다

**출력**

```text
===== 소스: pass03.cpp =====
// const std::string& 과 std::string_view — 리터럴을 넘길 때 갈린다
#include <cstdio>
#include <cstdlib>
#include <new>
#include <string>
#include <string_view>

static int allocs = 0;
void* operator new(std::size_t n) {
    ++allocs;
    void* p = std::malloc(n ? n : 1);
    if (!p) throw std::bad_alloc();
    return p;
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

static std::size_t total = 0;
void take_cref(const std::string& s) { total += s.size(); }
void take_view(std::string_view s)   { total += s.size(); }

#define LONG "0123456789012345678901234567890123456789"
#define RUN(label, stmt) do { allocs = 0; { stmt; } \
    std::printf("  %-30s new %d회\n", label, allocs); } while (0)

int main() {
    std::string s = LONG;
    const char* cstr = LONG;

    RUN("take_cref(literal)",   take_cref(LONG));
    RUN("take_view(literal)",   take_view(LONG));
    RUN("take_cref(const char*)", take_cref(cstr));
    RUN("take_view(const char*)", take_view(cstr));
    RUN("take_cref(std::string)", take_cref(s));
    RUN("take_view(std::string)", take_view(s));
    RUN("take_cref(s.substr)",  take_cref(s.substr(0, 5)));
    RUN("take_view(view.substr)", take_view(std::string_view(s).substr(0, 5)));
    std::printf("(합계 %zu — 최적화로 호출이 사라지지 않게)\n", total);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic pass03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  take_cref(literal)             new 1회
  take_view(literal)             new 0회
  take_cref(const char*)         new 1회
  take_view(const char*)         new 0회
  take_cref(std::string)         new 0회
  take_view(std::string)         new 0회
  take_cref(s.substr)            new 0회
  take_view(view.substr)         new 0회
(합계 250 — 최적화로 호출이 사라지지 않게)
```

**왜 그런가**

| 넘긴 것 | `const std::string&` | `std::string_view` |
|---|---|---|
| 리터럴 | ★★ **1회** | ★★★ **0회** |
| `const char*` | ★★ **1회** | ★★★ **0회** |
| `std::string` | 0회 | 0회 |
| 부분 문자열 | 0회 | 0회 |

- ★★★ **`take_cref(LONG)` 에서 생기는 것은 「임시 `std::string`」이다.**\
  읽기만 할 건데 **힙을 한 번 쓰고 바로 버린다.** `string_view` 는 **(포인터, 길이)** 만 만든다.
- ★★★ **마지막 두 줄은 이 결론의 근거가 아니다.**\
  `take_cref(s.substr(0, 5))` 가 **0회**인 것은 **잘라 낸 5자가 SSO 안에 들어갔기** 때문이지\
  **`const&` 가 공짜라서가 아니다.** ★ 근거로 쓰는 것은 **위 두 줄**이다.
- ★ **`std::string_view` 를 값으로 받는 이유** — 포인터와 길이 두 칸뿐이라 **참조로 받을 이유가 없다.**\
  `const std::string_view&` 는 **간접만 하나 더 만든다**(6번의 `const int&` 와 같은 집안).
- ★ 마지막 줄의 합계(`250`)는 **호출이 최적화로 사라지지 않게** 결과를 쌓아 둔 것이다 —\
  **근거가 아니라 실험이 실제로 돌았다는 표시**다.

### 5. ★★★ g++ 는 **0건** · clang 은 **1건** · 둘 다 `cc exit=0` — ASan 만 잡는다

**출력**

```text
===== 소스: pass04.cpp =====
// string_view 는 빌려 볼 뿐이다 — 임시에 붙이면 문장 끝에 끊긴다
#include <cstdio>
#include <string>
#include <string_view>

std::string make() { return std::string("0123456789012345678901234567890123456789"); }

int main() {
    std::string_view sv = make();          // ★ 임시는 이 문장 끝에 죽는다
    std::fprintf(stderr, "[마커] 여기까지는 산다 — size=%zu\n", sv.size());
    std::fprintf(stderr, "[마커] 이제 sv[0] 를 읽는다\n");
    char c = sv[0];
    std::fprintf(stderr, "[마커] sv[0]=%c\n", c);
}
===== echo "g++   경고 $(g++ -std=c++20 -Wall -Wextra -pedantic pass04.cpp -o ex 2>&1 | grep -c 'warning:')"; echo 'clang:'; clang++ -std=c++20 -Wall -Wextra -pedantic pass04.cpp -o ex 2>&1 | grep -E 'warning:|generated' (exit=0) =====
g++   경고 0
clang:
pass04.cpp:9:27: warning: object backing the pointer will be destroyed at the end of the full-expression [-Wdangling-gsl]
1 warning generated.
```

같은 소스를 AddressSanitizer 로 돌린다.

```text
===== 소스: pass04.cpp =====
// string_view 는 빌려 볼 뿐이다 — 임시에 붙이면 문장 끝에 끊긴다
#include <cstdio>
#include <string>
#include <string_view>

std::string make() { return std::string("0123456789012345678901234567890123456789"); }

int main() {
    std::string_view sv = make();          // ★ 임시는 이 문장 끝에 죽는다
    std::fprintf(stderr, "[마커] 여기까지는 산다 — size=%zu\n", sv.size());
    std::fprintf(stderr, "[마커] 이제 sv[0] 를 읽는다\n");
    char c = sv[0];
    std::fprintf(stderr, "[마커] sv[0]=%c\n", c);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 -g -ffile-prefix-map="$PWD"=. -fsanitize=address pass04.cpp -o ex && ./ex 2>&1 | grep -E '\[마커\]|ERROR: AddressSanitizer|READ of size|#0 |freed by thread|is located|allocated by thread|SUMMARY' (cc exit=0 · run exit=1) =====
[마커] 여기까지는 산다 — size=40
[마커] 이제 sv[0] 를 읽는다
==1022002==ERROR: AddressSanitizer: heap-use-after-free on address 0x504000000010 at pc 0x5aeefc54e809 bp 0x7ffd2a796490 sp 0x7ffd2a796480
READ of size 1 at 0x504000000010 thread T0
    #0 0x5aeefc54e808 in main pass04.cpp:12
0x504000000010 is located 0 bytes inside of 41-byte region [0x504000000010,0x504000000039)
freed by thread T0 here:
    #0 0x72514beff5e8 in operator delete(void*, unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:164
previously allocated by thread T0 here:
    #0 0x72514befe548 in operator new(unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:95
SUMMARY: AddressSanitizer: heap-use-after-free pass04.cpp:12 in main
```

**왜 그런가**

- ★★★ **g++ 13.3.0 은 경고가 0건**이고 **clang 18 만** `-Wdangling-gsl` 로 잡는다.\
  ★★ **둘 다 `cc exit=0`** 이다 — **컴파일러 하나는 완전히 침묵한다.**
- ★★★ **이 프로그램은 ill-formed 가 아니다.** 표준상 **적법한 프로그램**이고,\
  위반한 것은 **문법이 아니라 수명**이다. 그래서 **`-pedantic-errors` 로도 잡을 것이 없다.**\
  ★ 「`cc exit=0` 인데 ill-formed」인 정본 사례는 [목록의 **10번 주제**](../10-const-correctness/)에 있다.
- ★★★ **`sv.size()` 는 통과하고 `sv[0]` 에서 터진다.**\
  길이는 뷰가 **자기 안에** 들고 있고 글자만 **남의 것**이라 — **「반쯤 살아 있는」 상태**다.\
  ASan 이 짚은 줄이 **`pass04.cpp:12`**, 즉 `char c = sv[0];` 줄이다.
- ★★ **마커를 `fprintf(stderr, …)` 로 찍은 이유** — ASan 은 `abort()` 로 죽인다.\
  그러면 **표준 출력 버퍼에 남은 줄이 통째로 사라진다**(순서가 밀리는 게 아니라 **없어진다**).\
  표준 오류는 버퍼링을 안 하므로 **마커 두 줄이 리포트 앞에 그대로 남았다.**
- ★ **`cc exit=0 · run exit=1`** — 컴파일은 성공했고 **실행에서만** 걸렸다.
- ★ ASan 리포트에서 **근거로 쓰는 것**은 `heap-use-after-free` 라는 **종류**, `pass04.cpp:12` 라는 **자리**,\
  `41-byte region` 이라는 **크기**다. **주소·PID·`pc`/`bp`/`sp` 는 흔들리는 칸**이다.

### 6. ★ `add_val` 은 `lea` 한 줄 · `add_cref` 는 메모리를 두 번 읽는다

**출력**

```text
===== 소스: pass05.cpp =====
// 작은 타입은 값이 낫다 — 생성된 코드로 확인한다
struct Big { double d[8]; };                       // 64바이트

int add_val (int a, int b)                { return a + b; }
int add_cref(const int& a, const int& b)  { return a + b; }

double sum_val (Big b)        { return b.d[0] + b.d[7]; }
double sum_cref(const Big& b) { return b.d[0] + b.d[7]; }

double call_val (const Big& b) { return sum_val(b); }   // 복사가 여기서 난다
double call_cref(const Big& b) { return sum_cref(b); }
===== g++ -std=c++20 -O2 -c pass05.cpp -o p5.o && objdump -d --no-show-raw-insn p5.o | sed -n '/>:/,$p' (exit=0) =====
0000000000000000 <_Z7add_valii>:
   0:	endbr64
   4:	lea    (%rdi,%rsi,1),%eax
   7:	ret
   8:	nopl   0x0(%rax,%rax,1)

0000000000000010 <_Z8add_crefRKiS0_>:
  10:	endbr64
  14:	mov    (%rsi),%eax
  16:	add    (%rdi),%eax
  18:	ret
  19:	nopl   0x0(%rax)

0000000000000020 <_Z7sum_val3Big>:
  20:	endbr64
  24:	movsd  0x8(%rsp),%xmm0
  2a:	addsd  0x40(%rsp),%xmm0
  30:	ret
  31:	data16 cs nopw 0x0(%rax,%rax,1)
  3c:	nopl   0x0(%rax)

0000000000000040 <_Z8sum_crefRK3Big>:
  40:	endbr64
  44:	movsd  (%rdi),%xmm0
  48:	addsd  0x38(%rdi),%xmm0
  4d:	ret
  4e:	xchg   %ax,%ax

0000000000000050 <_Z8call_valRK3Big>:
  50:	endbr64
  54:	movsd  0x38(%rdi),%xmm0
  59:	addsd  (%rdi),%xmm0
  5d:	ret
  5e:	xchg   %ax,%ax

0000000000000060 <_Z9call_crefRK3Big>:
  60:	endbr64
  64:	movsd  (%rdi),%xmm0
  68:	addsd  0x38(%rdi),%xmm0
  6d:	ret
```

**왜 그런가**

| 함수 | 명령어 열 |
|---|---|
| `add_val(int, int)` | `lea (%rdi,%rsi,1),%eax` — ★★ **값이 이미 레지스터에 있다** |
| `add_cref(const int&, const int&)` | `mov (%rsi),%eax` + `add (%rdi),%eax` — ★★ **주소를 받아 메모리를 두 번 읽는다** |
| `sum_val(Big)` | `movsd 0x8(%rsp)` + `addsd 0x40(%rsp)` — 64바이트라 **스택으로 온다** |
| `sum_cref(const Big&)` | `movsd (%rdi)` + `addsd 0x38(%rdi)` — 주소 하나만 온다 |

- ★★★ **`const int&` 로 받으면 「복사를 피한 것」이 아니라 「간접을 하나 더 만든 것」이다.**\
  `int` 는 **주소보다 작거나 같다** — 감출 복사가 애초에 없다.
- ★ **`Big`(64바이트)은 반대**다. 받는 쪽만 보면 `sum_cref` 는 주소 하나로 끝난다.
- ★★ **여기서 멈춰야 한다.** 「그래서 큰 타입은 `const&` 가 빠르다」로 건너뛰면 **7번에 걸린다.**
- ★ 읽을 것은 **명령어 열**이다. **주소·오프셋(`0:` · `54:`)과 `nopl` 정렬 패딩은 흔들리는 칸**이다.

### 7. ★★★ 컴파일러가 인라인해서 복사를 **아예 만들지 않았다**

**출력**

6번 블록의 `call_val` 은 `movsd` 두 줄로 끝났다. 인라인을 끄고 다시 뜬다.

```text
===== 소스: pass05.cpp =====
// 작은 타입은 값이 낫다 — 생성된 코드로 확인한다
struct Big { double d[8]; };                       // 64바이트

int add_val (int a, int b)                { return a + b; }
int add_cref(const int& a, const int& b)  { return a + b; }

double sum_val (Big b)        { return b.d[0] + b.d[7]; }
double sum_cref(const Big& b) { return b.d[0] + b.d[7]; }

double call_val (const Big& b) { return sum_val(b); }   // 복사가 여기서 난다
double call_cref(const Big& b) { return sum_cref(b); }
===== g++ -std=c++20 -O2 -fno-inline -c pass05.cpp -o p5n.o && objdump -d --no-show-raw-insn p5n.o | sed -n '/_Z8call_valRK3Big>:/,$p' (exit=0) =====
0000000000000050 <_Z8call_valRK3Big>:
  50:	endbr64
  54:	sub    $0x48,%rsp
  58:	movdqu (%rdi),%xmm1
  5c:	movdqu 0x10(%rdi),%xmm2
  61:	movdqu 0x20(%rdi),%xmm3
  66:	movdqu 0x30(%rdi),%xmm4
  6b:	movups %xmm1,(%rsp)
  6f:	movups %xmm2,0x10(%rsp)
  74:	movups %xmm3,0x20(%rsp)
  79:	movups %xmm4,0x30(%rsp)
  7e:	call   83 <_Z8call_valRK3Big+0x33>
  83:	add    $0x48,%rsp
  87:	ret
  88:	nopl   0x0(%rax,%rax,1)

0000000000000090 <_Z9call_crefRK3Big>:
  90:	endbr64
  94:	jmp    40 <_Z8sum_crefRK3Big>
```

**왜 그런가**

```text
   -O2              call_val:  movsd / addsd / ret          복사 없음(인라인됨)
   -O2 -fno-inline  call_val:  sub  $0x48,%rsp
                               movdqu ×4   (원본 64바이트를 읽고)
                               movups ×4   (스택에 쓴다)
                               call  …                      ← 복사 여덟 줄이 보인다
                    call_cref: jmp  _Z8sum_crefRK3Big        ← 주소 하나, 꼬리 점프
```

- ★★★ **같은 소스·같은 `-O2` 인데 플래그 하나로 결론이 뒤집힌다.**\
  인라인되면 **전달 방식의 차이 자체가 없어진다.**
- ★★★ **그래서 「값 전달이 복사 때문에 느리다」를 이 실험만으로 단정하면 안 된다.**\
  차이가 남는 자리는 **번역 단위를 넘는 호출**과 **인라인이 안 되는 큰 함수**다.
- ★★★ **이 문서가 시간을 한 번도 재지 않은 이유** — 한 문장으로:\
  **「전달 방식의 비용은 호출 지점의 최적화에 달렸고, 그것은 시그니처를 보고는 알 수 없다.」**\
  근거로 쓴 것은 **① 복사·이동 횟수 ② 할당 횟수 ③ 명령어 열** 셋뿐이고, 셋 다 **다시 돌리면 같은 값**이다.
- ★ **복사를 보이게 하는 법**은 인라인을 막는 것이다 — `-fno-inline`, 또는 **정의를 다른 번역 단위에** 두는 것.\
  ★ **이 문서는 `-fno-inline` 만 던졌다**(다른 번역 단위 판은 안 돌렸다).

### 8. ★★ `const std::vector&` 는 C 배열에서 `new` 1회 · `span` 은 0회

**출력**

```text
===== 소스: pass06.cpp =====
// std::span — 「연속된 것이면 무엇이든」 받는다
#include <array>
#include <cstdio>
#include <cstdlib>
#include <new>
#include <span>
#include <vector>

static int allocs = 0;
void* operator new(std::size_t n) {
    ++allocs;
    void* p = std::malloc(n ? n : 1);
    if (!p) throw std::bad_alloc();
    return p;
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

static long total = 0;
void sum_span(std::span<const int> s)        { for (int x : s) total += x; }
void sum_vec (const std::vector<int>& v)     { for (int x : v) total += x; }

#define RUN(label, stmt) do { allocs = 0; { stmt; } \
    std::printf("  %-28s new %d회\n", label, allocs); } while (0)

int main() {
    std::vector<int> v{1, 2, 3};
    int carr[3]{1, 2, 3};
    std::array<int, 3> arr{1, 2, 3};

    RUN("sum_vec(vector)",   sum_vec(v));
    RUN("sum_span(vector)",  sum_span(v));
    RUN("sum_span(C array)", sum_span(carr));
    RUN("sum_span(std::array)", sum_span(arr));
    RUN("sum_vec(C array)",  sum_vec(std::vector<int>(carr, carr + 3)));
    std::printf("(합계 %ld)\n", total);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic pass06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  sum_vec(vector)              new 0회
  sum_span(vector)             new 0회
  sum_span(C array)            new 0회
  sum_span(std::array)         new 0회
  sum_vec(C array)             new 1회
(합계 30)
```

**왜 그런가**

| 넘긴 것 | `const std::vector<int>&` | `std::span<const int>` |
|---|---|---|
| `std::vector<int>` | 0회 | 0회 |
| C 배열 `int[3]` | ★★★ **1회** | ★★★ **0회** |
| `std::array<int,3>` | ★ **못 받는다**(이 문서는 던지지 않았다) | 0회 |

- ★★★ **`const std::vector<int>&` 로 C 배열을 받으려면 벡터를 하나 만들어야 한다** —\
  소스에 `std::vector<int>(carr, carr + 3)` 이라고 **적혀 있고**, 그것이 `new` 1회다.\
  **읽기만 할 건데 힙을 쓴 것**이다.
- ★★ **`span` 은 컨테이너 종류를 묻지 않는다.** 요구하는 것은 「**연속 메모리 + 길이**」뿐이라\
  `vector`·C 배열·`std::array` 셋을 **0회**로 받는다.
- ★ **`std::span<const int>` 와 `std::span<int>`** — 앞은 **읽기 전용**, 뒤는 **고칠 수 있다.**\
  「고칠 수 있음」을 **타입으로** 말하는 자리라 형제 [`07번`](../07-references-vs-pointers/)의 「없음을 타입으로」와 같은 집안이다.
- ★ **배열을 매개변수에 그냥 쓰면 포인터로 감쇠해 길이가 사라진다.**\
  정본은 C 갈래 [`16-array-pointer-decay-and-function-parameters/`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/)이고,\
  **`span` 은 그 감쇠에 길이를 다시 붙인 것**으로 읽으면 된다.
- ★ `sum_vec` 에 `std::array` 를 넘기는 판은 **던지지 않았다**(컴파일 에러가 날 자리로 읽되, 출력이 없으므로 단정하지 않는다).

### 9. 「크기」가 아니라 「**그 값으로 무엇을 하나**」로 고른다

**출력** — 이 문항은 출력이 없다. 앞 여덟 문항에서 센 수치를 표로 접는다.

| 무엇을 하나 | 무엇으로 받나 | 근거 |
|---|---|---|
| 읽기만 · 작은 내장 타입 | **값** | 6번 `lea` 한 줄 대 메모리 두 번 |
| 읽기만 · 큰 타입 | **`const T&`** | 1번 네 칸 모두 copy 0 |
| 읽기만 · 문자열 | **`std::string_view`** | 4번 리터럴·`const char*` 에서 1회 → 0회 |
| 읽기만 · 연속 배열 | **`std::span<const T>`** | 8번 C 배열에서 1회 → 0회 |
| 보관 · 호출이 임시 위주 | **`T&&`** | 2번 copy 0 · move 1 |
| 보관 · lvalue 와 임시가 섞임 | **값 + `std::move`** | 3번 오버로드 쌍과 같은 할당 수 · 코드 절반 |
| 보관 · 이동이 비싼 타입 | **오버로드 쌍** | 2번 값 전달만 lvalue 에서 이동 1회를 더 쓴다 |
| 그대로 넘긴다 | **`T&&` + `std::forward`** | 2번 `by_fwd` 가 오버로드 쌍과 동일 |

- **읽기만 할 때 값을 고르는 자리** — `int`·포인터처럼 **레지스터에 들어가는** 타입(6번).
- **읽기만 할 때 `const T&` 를 고르는 자리** — 크고 복사가 비싼 타입(1번).
- **값 + `std::move` 가 오버로드 쌍을 대신할 수 있는 조건** — **이동이 싼 타입**일 때.\
  `std::string` 은 그래서 된다(3번에서 할당 수가 같았다).
- **대신할 수 없는 조건** — **이동이 비싼 타입.** 그 한 번이 그대로 비용이 된다.
- **`string_view` 를 쓰면 안 되는 자리 둘** — ★ **저장할 때**(멤버·컨테이너 — 5번) ·\
  ★ **널 종료가 필요한 C API 에 넘길 때**(뷰는 끝에 `\0` 이 있다는 보장이 없다).
- ★★★ **기준은 「크기」가 아니라 「그 값으로 무엇을 할 것인가」다** — 읽기만 하나, 보관하나, 훔치나.

### 10. 이 주제의 지도

- **lvalue·prvalue·xvalue** 의 정본 — [목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/).\
  1번의 `read_value(Probe(2))` 가 copy 0 인 이유(물질화)가 거기 있다.
- **`std::move` 가 아무것도 옮기지 않는다**는 것의 정본 — [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/).\
  2번의 `by_rref` 가 move 1 인 것은 **본문에 `std::move` 가 한 번 더** 있기 때문이다.
- **`std::forward` 와 전달 참조** 의 정본 — [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/).\
  2번에서 `by_fwd` 가 오버로드 쌍과 같은 답을 낸 근거다.
- **죽은 임시를 가리키는 뷰가 왜 UB 인가** 의 정본 — [목록의 **30번 주제**](../30-dangling-references-and-lifetime-extension/)(수명 연장 규칙).
- **`std::string` 과 `string_view` 자체** 의 정본 — 목록의 **46번 주제**.
- **배열의 포인터 감쇠** — C 갈래 [`16-array-pointer-decay-and-function-parameters/`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/).
- **`const` 를 어디에 붙이나** — [목록의 **10번 주제**](../10-const-correctness/). ★ 값 매개변수의 `const` 는 **시그니처의 일부가 아니다.**
- **이동 생성자에 `noexcept` 가 없으면 `vector` 가 복사하는 것** — 목록의 **53번 주제**.\
  ★ 이 문서의 `Probe` 는 이동을 `noexcept` 로 달아 **그 변수를 고정해 두었다.**

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 명령으로 돌렸나 |
|---|---|---|
| `pass01.cpp` 전달 방식 계수 | ★★★ `[A]` 읽기 4줄 · `[B]` 보관 10줄 — **copy/move 28개 수치** | g++ |
| `pass02.cpp` 싱크 세터 | ★★★ `SetCref` 1/2/2 · `SetPair` 1/1/1 · `SetVal` 1/1/1 | g++ |
| `pass03.cpp` 뷰 대 `const&` | ★★ 리터럴·`const char*` 에서 **1회 대 0회** | g++ |
| `pass04.cpp` 댕글링 경고 | ★★★ **g++ 0건 · clang 1건**(`-Wdangling-gsl`) · 둘 다 `cc exit=0` | g++ · clang |
| 〃 ASan | ★★★ `heap-use-after-free` · `pass04.cpp:12` · **`run exit=1`** | g++ `-O0 -g -fsanitize=address` |
| `pass05.cpp` 기계어 | ★★ `add_val` **`lea` 한 줄** 대 `add_cref` **메모리 2회** | g++ `-O2 -c` + `objdump` |
| 〃 인라인 끄기 | ★★★ `call_val` 에 **`movdqu`×4 + `movups`×4 + `sub $0x48,%rsp`** 가 나타난다 | g++ `-O2 -fno-inline -c` + `objdump` |
| `pass06.cpp` `span` | ★★ C 배열에서 **벡터 1회 대 span 0회** | g++ |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · libstdc++ · binutils 2.42)에서만** 그렇다.

- ★★ **짧은 문자열 최적화(SSO)의 경계** — 40자는 힙으로 갔고 5자는 안 갔다(3·4번).\
  **표준이 요구하는 것이 아니다.** 다른 구현에서는 경계가 다르다.
- ★★ **`std::string` 의 이동이 힙을 안 쓰는 것** — 3번에서 lvalue 열이 셋 다 1회인 근거.
- ★ **`Big`(64바이트)이 스택으로 실려 가는 것** — x86-64 SysV ABI 의 결과다.
- ★ **기계어 덤프의 주소·오프셋·`nopl` 정렬 패딩** — 흔들리는 칸이다.
- ★ **`-Wdangling-gsl` 이 clang 에만 있는 것** · 진단 문구 전부.
- ★ **인라인 여부**(7번) — 최적화기가 정한다. **미명시**다.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **값 매개변수가 복사·이동 생성자를 부르는** 것.
- **prvalue 인자를 값으로 받으면 복사가 0인** 것(C++17부터).
- **`const T&` 가 임시를 받되 그것을 훔칠 수 없는** 것.
- **`T&&` 가 lvalue 를 받지 못하는** 것.
- **`std::forward` 가 받은 범주를 보존하는** 것.
- **`std::string_view`·`std::span` 이 대상을 소유하지 않는** 것.
- ★ **죽은 객체를 가리키는 뷰를 읽는 것이 UB** 인 것.

**UB 의 결과라 보장이 아닌 것**(관찰로만 읽는다)

- ★ 5번의 **`run exit=1`** 과 ASan 이 찍은 **주소·영역 크기** — 그 판의 결과다.\
  근거로 쓰는 것은 「**ASan 이 `heap-use-after-free` 로 12번 줄을 짚었다**」와\
  「**g++ 는 경고 0건, clang 은 1건이었다**」다.
- ★ **sanitizer 없이 돌린 판은 싣지 않았다** — 「안 터졌다」가 「안전하다」가 아니기 때문이다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **인자가 여럿일 때의 오버로드 조합**(이 문서는 인자 하나짜리만 던졌다) ·\
  ★ **`sum_vec` 에 `std::array` 를 넘기는 판**(8번에서 「못 받는다」로만 적고 에러를 받지 않았다) ·\
  ★ **`std::span` 의 고정 길이 판**(`std::span<const int, 3>`) ·\
  ★ **이동이 비싼 타입**(이 문서의 `Probe`·`std::string` 은 둘 다 이동이 싸다) ·\
  ★ **`vector` 재할당에서 `noexcept` 가 없을 때의 복사**(정본은 목록의 **53번 주제**) ·\
  ★ **정의를 다른 번역 단위에 둔 판**(7번은 `-fno-inline` 만 던졌다) ·\
  ★ **`-O0`·`-O1`·`-O3`·`-Os` 의 기계어**(6·7번은 `-O2` 두 판만 던졌다) ·\
  ★ **`string_view` 를 멤버로 저장한 판**(5번은 지역 변수 판만 던졌다).
- **못 잰 것** — ★★★ **「어느 전달 방식이 몇 배 빠른가」.**\
  이 문서가 센 것은 **호출 횟수·할당 횟수·명령어 열**까지다.\
  **시간을 재려면 벤치마크 하네스가 따로** 필요하고, 7번이 보인 대로 **인라인 하나로 결론이 뒤집힌다.**\
  ★ 그래서 이 문서에는 **「몇 배」라는 수치가 한 줄도 없다.**
- ★ **「할당 1회」가 「비용 1단위」가 아니다** — `new` 횟수는 **세어진 것**이고,\
  그 한 번이 얼마나 드는지는 **이 문서가 재지 않았다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **g++ 가 `string_view` 댕글링을 경고하기 시작했는지**(5번 — 지금은 **0건**).\
  GCC 가 `-Wdangling-reference` 계열을 넓히는 중이라 **가장 먼저 움직일 칸**이다.
- ★★ **SSO 경계**(3·4번의 40자 · 5자) — 라이브러리 판이 바뀌면 움직인다.
- ★ **`call_val` 이 `-O2` 에서 계속 인라인되는지**(7번) — 최적화기가 바뀌면 움직인다.
- ★ **clang 의 경고 개수와 이름**(지금은 `-Wdangling-gsl` 1건).
- ★ **`p11-01` 의 28개 수치** — 여기가 바뀌면 그것은 **컴파일러 버그이거나 표준 변경**이다.
