# cpp/syntax/11 — 매개변수 전달 방식 고르기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 함수 선언과 매개변수](https://en.cppreference.com/w/cpp/language/function) · [`std::string_view`](https://en.cppreference.com/w/cpp/string/basic_string_view) · [`std::span`](https://en.cppreference.com/w/cpp/container/span) · [`std::move`](https://en.cppreference.com/w/cpp/utility/move) · [교체 가능한 `operator new`](https://en.cppreference.com/w/cpp/memory/new/operator_new) · [Clang — `-Wdangling-gsl`](https://clang.llvm.org/docs/DiagnosticsReference.html#wdangling-gsl)
> **실행 검증** — 이 문서의 모든 출력·진단·기계어는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **GNU objdump 2.42** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`pass01.cpp` \~ `pass06.cpp`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 긴 출력은 **거르는 명령을 배너에 적어 두었다**(ASan 은 `| grep -E '…'`).\
> 그러니 실린 것은 「생략한 일부」가 아니라 **그 명령의 전체 출력**이다.
> **버전** — 값·`const&` 는 **C++98부터**. `T&&` 와 `std::move`·`std::forward` 는 **C++11부터**,\
> `std::string_view` 는 **C++17부터**, `std::span` 은 **C++20부터**다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.
> ★★★ **08 → 09 → 11 은 한 사슬이다** — 08 이 **범주**(lvalue·prvalue·xvalue)를 정하고,\
> 09 가 **그 범주를 만드는 법**(`std::move`·`std::forward`)을 주고,\
> **여기 11 이 「그래서 매개변수를 무엇으로 받을까」에 답한다.** 세 문서는 같은 격자를 다시 쓴다.\
> **경계** — 「값 범주」의 정본은 [목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/), 「`std::move`·`std::forward`·참조 축약」은 [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/),\
> 「`const` 정확성」은 [목록의 **10번 주제**](../10-const-correctness/)다. 여기서는 **그 규칙을 다시 설명하지 않고 결론만 쓴다.**\
> 「참조가 무엇인가」는 형제 [`07번`](../07-references-vs-pointers/), 「오버로드 해석 순서」는 형제 [`01번`](../01-function-overloading-and-overload-resolution/),\
> 「`std::string` 과 `string_view` 자체」는 목록의 **46번 주제**, 「이동 후 상태」는 [목록의 **17번 주제**](../17-move-constructor-assignment-and-moved-from-state/),\
> 「댕글링과 수명 연장 규칙」은 [목록의 **30번 주제**](../30-dangling-references-and-lifetime-extension/), 「`noexcept` 와 이동」은 목록의 **53번 주제**가 정본이다.\
> 배열이 함수 매개변수에서 포인터로 감쇠하는 것은 C 갈래\
> [`16-array-pointer-decay-and-function-parameters/`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/)가 정본이다.
> ★★★ **이 문서는 벤치마크를 하지 않았다.** 근거는 **복사·이동 호출 횟수**, **힙 할당 횟수**, **생성된 명령어 열** 셋뿐이다.\
> 「몇 배 빠르다」는 문장은 **한 줄도 없다** — 그것은 **재야 하는 것**이고 이 문서는 재지 않았다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 의 **주소**(`0x504000000010`)·**PID**(`==981129==`)·`pc`/`bp`/`sp` | ★★ **`heap-use-after-free` 라는 진단 종류** · **`pass04.cpp:12`** · **`run exit=1`** |
> | 기계어 덤프의 **주소·오프셋**(`0:` · `54:`)과 `nopl` 정렬 패딩 | ★★★ **명령어 열 자체**(`lea` · `movdqu`×4 · `movups`×4 · `sub $0x48,%rsp` · `jmp`) |
> | 두 컴파일러의 **진단 문구** | ★★★ **복사·이동 호출 횟수** · **`new` 호출 횟수** — 이 주제의 답 자체다 |
> | 실행 시간(이 문서는 **재지 않았다**) | **`cc exit` 와 `run exit`**(갈라 적었다) · **경고 개수**(g++ 0 · clang 1) |

## 한눈에 — 쉽게 말하면

**책을 건네는 방법은 네 가지다 — 복사해 준다 · 보여만 준다 · 줘 버린다 · 서가 위치만 알려 준다.**

| 비유 | 매개변수 | 받는 쪽이 할 수 있는 것 |
|---|---|---|
| **복사본을 만들어 건넨다** | `void f(T p)` | 마음대로 고치고 **가져도 된다** |
| **펼쳐서 보여만 준다** | `void f(const T& p)` | **읽기만** 한다. 원본은 그대로 |
| ★ **「이제 네 거다」 하고 넘긴다** | `void f(T&& p)` | **훔쳐 간다.** 원본은 껍데기만 남는다 |
| ★★ **서가 몇 번 칸인지만 알려 준다** | `void f(std::string_view p)` · `void f(std::span<const T> p)` | **읽기만** 한다. ★ 그런데 **책이 치워지면 끊긴다** |

> **싱크 매개변수(sink parameter)** — 받은 값을 **자기 안에 보관하는** 매개변수.\
> 예: `void set_name(std::string s) { name_ = std::move(s); }` — 받은 것을 멤버로 삼는다.

> **뷰(view)** — 소유하지 않고 **가리키기만** 하는 타입. `std::string_view` · `std::span`.\
> 예: `std::string_view sv = s;` 는 `s` 의 글자를 **한 자도 복사하지 않는다**.

- ★★★ **고르는 기준은 「크기」가 아니라 「그 값으로 무엇을 할 것인가」다** — 읽기만 하나, 보관하나, 훔치나.
- ★★★ **그 답은 세어야 나온다.** 이 문서는 **복사·이동 생성자에 로그를 심어** 방식마다 몇 번 도는지 센다((2)(3)).
- ★★ **뷰는 공짜가 아니다** — 할당은 사라지지만 **수명 책임이 호출하는 쪽으로 옮겨 간다**((6)).

```text
   읽기만 하나?  ──예──>  값이 작고 복사가 싼가?
        │                    ├─예─> 값 전달        void f(int x)
        │                    └─아니> const T&       void f(const Big& b)
        │                            (문자열·연속 배열이면 뷰)
        │                                          void f(std::string_view s)
        │                                          void f(std::span<const int> s)
        └─아니(보관한다)──>  호출하는 쪽이 늘 임시를 주나?
                             ├─예─> T&&            void set(T&& x)
                             └─섞임>  값 + std::move  void set(T x) { m = std::move(x); }
                                      (또는 const T& / T&& 오버로드 쌍)
```

## 이 주제가 답하려는 질문

1. **전달 방식마다 복사·이동이 몇 번 도나** — 그리고 **읽기만 할 때와 보관할 때 답이 다른가**((2)(3)).
2. **값 전달이 오버로드 쌍을 대신할 수 있나** — 코드는 절반인데 값은 같은가((4)).
3. **뷰가 없애는 것과 새로 만드는 것은 각각 무엇인가**((5)(6)(9)).

## 동작 방식

### (0) 이 주제가 쓰는 네 창

「어느 쪽이 나은가」는 **의견이 아니라 계수**로 답해야 한다. 창 넷을 갈라 쓴다.

```text
① 복사·이동 생성자에 로그를 심는다     방식마다 몇 번 도는지 센다        (2)(3)
② operator new 를 갈아 끼운다          힙 할당이 몇 번 나는지 센다       (4)(5)(9)
③ objdump -d 로 생성된 코드를 본다     작은 타입이 어떻게 실려 가는지    (7)(8)
④ AddressSanitizer                     빌린 것이 언제 끊기는지           (6)
```

- ★★★ **주력 창은 ①이다.** 「값 전달이 복사를 낳는다」를 **말로 하면 어디까지 참인지 모른다** — **세면 안다.**
- ★★ **네 번째 창은 ④ ASan 이다.** 앞의 셋이 **전부 조용한 자리**가 하나 있고((6)) 그것만 잡는다.
- ★ ②는 **`operator new` 를 프로그램이 직접 교체**해서 센다 — 표준이 허용하는 자리라 **라이브러리를 고치지 않아도** 된다.
- ★★ ③은 **수치가 아니라 명령어 열**을 근거로 쓴다. 시간을 재는 것이 아니다((8)에서 그 선을 긋는다).

### (1) 전달 방식 다섯 — 무엇이 달라지나

**언제 쓰나** — 함수 시그니처를 쓰기 직전마다.

```text
   Probe lv(1);              // 이름 있는 객체 하나

   void f(Probe p)        ──>  p 는 새 객체다.   lv 은 그대로
   void f(const Probe& p) ──>  p 는 lv 의 별명.  못 고친다
   void f(Probe&& p)      ──>  p 는 별명인데 "훔쳐도 된다"  ← 08 의 xvalue 칸
   template<class T>
   void f(T&& p)          ──>  준 것이 lvalue 면 별명, rvalue 면 훔쳐도 되는 별명
   void f(std::string_view p) ──> p 는 (포인터, 길이) 두 칸.  글자는 안 옮긴다
```

- ★★ **`const T&` 와 `T&&` 는 「별명」이라는 점이 같다** — 다른 것은 **훔쳐도 되느냐**뿐이다([목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/)).
- ★ **`T&&` 가 템플릿 매개변수일 때만 전달 참조**가 된다 — 그 규칙의 정본은 [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)다.

**비용** — 시그니처를 고르는 것 자체는 비용이 0이다. **비용은 호출 지점에서 난다** — 그것을 (2)(3)에서 센다.

### (2) ★★★ 읽기만 할 때 — 복사를 센다

**언제 쓰나** — 「이 함수는 인자를 읽기만 한다」가 확실할 때.

복사·이동 생성자에 로그를 심은 `Probe` 를 만들고, 호출마다 계수기를 0으로 되돌려 센다.

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

먼저 `[A]` 네 줄만 읽는다.

| 호출 | 인자의 범주 | copy | move | 읽는 법 |
|---|---|---|---|---|
| `read_value(lv)` | lvalue | ★ **1** | 0 | 매개변수를 만드느라 **복사 한 번** |
| `read_value(Probe(2))` | prvalue | 0 | 0 | ★★ **임시가 곧 매개변수**다 — 08 의 「물질화」 |
| `read_cref(lv)` | lvalue | 0 | 0 | 별명만 붙었다 |
| `read_cref(Probe(2))` | prvalue | 0 | 0 | 별명만 붙었다 |

- ★★★ **읽기만 하는 함수에 값 전달을 쓰면 lvalue 인자에서 복사 한 번을 그냥 잃는다.**
- ★★ **prvalue 를 값으로 받으면 복사가 0이다** — C++17 물질화 덕분이고, 그 정본은 [목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/)다.\
  ★ 그래서 「값 전달은 항상 복사한다」는 **틀렸다** — **인자의 범주에 달렸다.**
- ★ `const T&` 는 **네 칸 모두 0** 이다 — 읽기만 할 거면 **비교가 끝난다**(작은 내장 타입만 예외 — (7)).

**비용** — 읽기만 하는 함수: `const T&` 가 **0회**, 값 전달이 **lvalue 에서 1회**.

### (3) ★★★ 받아서 보관할 때 — 같은 격자, 다른 답

**언제 쓰나** — 받은 값을 **멤버나 컨테이너에 넣을** 때. (2)와 답이 갈린다.

같은 블록의 `[B]` 열 줄을 읽는다.

| 호출 | 인자의 범주 | copy | move | 합 |
|---|---|---|---|---|
| `by_value(lv)` | lvalue | 1 | 1 | ★ **2** |
| `by_value(Probe(2))` | prvalue | 0 | 1 | 1 |
| `by_cref(lv)` | lvalue | 1 | 0 | 1 |
| `by_cref(Probe(2))` | prvalue | ★★ **1** | 0 | 1 |
| `by_rref(std::move(lv))` | xvalue | 0 | 1 | 1 |
| `by_rref(Probe(2))` | prvalue | 0 | 1 | 1 |
| `by_pair(lv)` | lvalue | 1 | 0 | 1 |
| `by_pair(Probe(2))` | prvalue | 0 | 1 | 1 |
| `by_fwd(lv)` | lvalue | 1 | 0 | 1 |
| `by_fwd(Probe(2))` | prvalue | 0 | 1 | 1 |

- ★★★ **`const T&` 는 임시를 받아도 복사한다**(`by_cref(Probe(2))` 가 copy 1).\
  **훔쳐도 되는 값을 받아 놓고 못 훔치는 것** — 이것이 `const T&` 싱크의 값이다.
- ★★★ **값 전달 싱크는 lvalue 에서 이동을 한 번 더 쓴다**(copy 1 + move 1).\
  ★ 그런데 **복사 횟수는 오버로드 쌍과 같다** — 더 드는 것은 **이동 한 번**이다.
- ★★ **오버로드 쌍(`by_pair`)과 전달 참조(`by_fwd`)가 한 칸도 다르지 않다.**\
  `std::forward` 가 하는 일이 정확히 「**받은 범주 그대로 넘긴다**」이기 때문이다([목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)).
- ★ **`T&&` 만 두면 lvalue 를 아예 못 받는다** — `by_rref(lv)` 는 컴파일되지 않는다([목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/)의 묶기 격자).\
  위 표의 `by_rref` 행이 **`std::move(lv)`** 인 이유가 그것이다.

**비용** — 보관하는 함수: `const T&` 는 **prvalue 를 받아도 복사 1회**, 나머지 셋은 **1회**,\
값 전달만 **lvalue 에서 2회**(복사 1 + 이동 1)다.

### (4) ★★ 싱크 매개변수 — 값 전달이 오버로드 쌍을 대신한다

**언제 쓰나** — 세터·생성자처럼 **받은 것을 그대로 보관**할 때.

(3)은 **호출 횟수**를 셌다. 이번에는 **힙 할당**을 센다 — `operator new` 를 갈아 끼운다.

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

| 세터 | lvalue | 임시 | 리터럴 | 코드 줄 |
|---|---|---|---|---|
| `SetCref`(`const&` 하나) | 1 | ★★ **2** | ★★ **2** | 1줄 |
| `SetPair`(`const&` + `&&`) | 1 | 1 | 1 | ★ **2줄** |
| `SetVal`(값 + `std::move`) | 1 | 1 | 1 | ★★★ **1줄** |

- ★★★ **값 전달 세터가 오버로드 쌍과 같은 수를 내면서 코드가 절반이다.** 이것이 이 주제의 결론 하나다.
- ★★ **`const&` 하나만 두면 임시·리터럴에서 할당이 두 번** 난다 —\
  **① 임시 문자열을 만들고 ② 그것을 멤버에 복사**한다. **훔칠 수 있었던 것을 복사한 것**이다.
- ★ **리터럴 열이 임시 열과 같다** — 리터럴을 `const std::string&` 에 넘기면 **그 자리에서 임시 `std::string` 이 생기기** 때문이다((5)에서 다시 본다).
- ★★ 다만 (3)이 보인 대로 **값 전달은 lvalue 에서 이동을 한 번 더** 쓴다.\
  ★ `std::string` 의 이동은 **포인터 몇 개를 옮기는 것**이라 **할당이 늘지 않는다** — 위 표의 lvalue 열이 셋 다 **1** 인 것이 그 실측이다.\
  ★★★ **「그래서 얼마나 손해인가」는 이 문서가 재지 않았다** — 재려면 벤치마크가 필요하다.

**비용** — 할당 기준: 오버로드 쌍 = 값 전달 < `const&` 하나. **코드 양은 값 전달이 가장 적다.**

### (5) `string_view` — 리터럴에서 할당이 사라진다

**언제 쓰나** — 문자열을 **읽기만** 하는 함수를 만들 때.

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

| 넘긴 것 | `const std::string&` | `std::string_view` |
|---|---|---|
| 리터럴 `"0123…"` | ★★ **new 1회** | ★★★ **0회** |
| `const char*` | ★★ **new 1회** | ★★★ **0회** |
| `std::string` | 0회 | 0회 |
| 부분 문자열 | 0회(★ 아래 주의) | 0회 |

- ★★★ **`const std::string&` 에 리터럴을 넘기면 그 자리에서 `std::string` 임시가 만들어진다.**\
  **읽기만 할 건데 힙을 한 번 쓴 것**이다. `string_view` 는 **(포인터, 길이)** 두 칸만 만든다.
- ★★ **마지막 두 줄은 조심해서 읽어라.** `take_cref(s.substr(0, 5))` 가 **0회**인 것은\
  **`const&` 가 공짜라서가 아니라 잘라 낸 5자가 짧은 문자열 최적화(SSO) 안에 들어갔기 때문**이다.\
  ★ **그러니 이 두 줄은 「뷰가 낫다」의 근거가 아니다** — 근거는 **위 두 줄**(리터럴·`const char*`)이다.

> **짧은 문자열 최적화(SSO, small string optimization)** — 짧은 문자열을 힙 대신\
> `std::string` 객체 **안쪽 공간**에 담는 구현 기법. ★ **표준이 요구하는 것이 아니다.**\
> 예: 이 실험에서 **40자는 힙**으로 가고 **5자는 안 갔다**.

**비용** — 읽기만 하는 문자열 함수: 뷰가 **리터럴·`const char*` 에서 할당 1회를 없앤다.**

### (6) ★★ 빌린 것은 갚아야 한다 — `string_view` 댕글링

**언제 쓰나** — 뷰를 **변수에 담거나 멤버로 저장**할 때. 매개변수로만 쓰면 이 함정이 거의 안 난다.

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

- ★★★ **g++ 13.3.0 은 경고가 0건**이다. **clang 18 만** `-Wdangling-gsl` 로 잡는다.
- ★★ **둘 다 `cc exit=0`** 이다 — **이 프로그램은 ill-formed 가 아니다.** 표준상 **적법한 프로그램**이고,\
  **틀린 것은 문법이 아니라 수명**이다. 그래서 컴파일러가 **말해 줄 의무가 없다.**

그래서 **실행해서** 잡는다.

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

```text
   std::string_view sv = make();
        │
        │  make() 가 돌려준 임시 std::string        [힙 41바이트]
        │  sv 는 그 안의 글자를 가리킨다  ─────────────> 0x5040…10
        │
        ▼  이 문장이 끝나는 세미콜론에서 임시가 죽는다
           [힙 41바이트]  해제됨
        │
        ▼  sv[0] 를 읽는다
           heap-use-after-free  ← ASan 이 여기서 멈춘다
```

- ★★★ **`sv.size()` 는 통과하고 `sv[0]` 에서 터진다.** 길이는 뷰가 **자기 안에** 들고 있고,\
  글자만 **남의 것**이기 때문이다 — **「반쯤 살아 있는」 상태**라 더 나쁘다.
- ★★ **마커를 표준 출력이 아니라 표준 오류로 찍었다.**\
  ASan 은 `abort()` 로 죽이는데, 그러면 **표준 출력 버퍼에 남은 줄이 통째로 사라진다**(순서가 밀리는 게 아니라 없어진다).\
  표준 오류는 버퍼링을 안 하므로 **마커 두 줄이 리포트 앞에 그대로 남는다.**
- ★ **`run exit=1`** 이다 — 컴파일은 성공했고(`cc exit=0`) 실행에서만 걸렸다.
- ★ 「임시의 수명이 어디까지인가」의 정본은 [목록의 **30번 주제**](../30-dangling-references-and-lifetime-extension/), 「`string_view` 자체」는 목록의 **46번 주제**다.

**비용** — 뷰는 **할당을 없애는 대신 수명 책임을 호출하는 쪽에 넘긴다.** 그 값을 **저장하면** 그 책임이 남는다.

### (7) 작은 타입은 값이 낫다 — 명령어 열로

**언제 쓰나** — `int`·포인터처럼 **레지스터에 들어가는** 타입을 받을 때.

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

| 함수 | 명령어 열 | 읽는 법 |
|---|---|---|
| `add_val(int, int)` | `lea (%rdi,%rsi,1),%eax` | ★★ **값이 이미 레지스터에 있다.** 한 줄 |
| `add_cref(const int&, const int&)` | `mov (%rsi),%eax` + `add (%rdi),%eax` | ★★ **주소를 받아 메모리를 두 번 읽는다** |
| `sum_val(Big)` | `movsd 0x8(%rsp)` + `addsd 0x40(%rsp)` | 64바이트라 **스택으로 온다** |
| `sum_cref(const Big&)` | `movsd (%rdi)` + `addsd 0x38(%rdi)` | 주소 하나만 온다 |

- ★★★ **`const int&` 로 받으면 「복사를 피한 것」이 아니라 「간접을 하나 더 만든 것」이다.**\
  `int` 는 **주소보다 작거나 같다** — 감출 복사가 없다.
- ★ **`Big`(64바이트)은 반대**다. 받는 쪽만 보면 `sum_cref` 가 주소 하나로 끝난다.
- ★★ 그런데 **「그래서 값 전달이 느리다」로 건너뛰면 안 된다** — 다음 절이 그 이유다.

### (8) ★★★ 같은 블록이 「재지 않은 주장」을 막는다

**언제 쓰나** — 「값 전달은 복사가 난다」를 **단정하기 직전**.

(7)의 블록에서 **`call_val` 을 다시 보라.** 64바이트를 값으로 넘기는 호출인데\
**복사하는 명령이 한 줄도 없다** — `movsd` 두 줄로 끝난다.

- ★★★ **컴파일러가 `sum_val` 을 인라인해서 복사를 아예 만들지 않았다.**
- ★ **복사를 보려면 인라인을 꺼야 한다.**

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

```text
   -O2            call_val:  movsd / addsd / ret             복사 없음(인라인됨)
   -O2 -fno-inline call_val: sub $0x48,%rsp
                             movdqu ×4   (원본 64바이트를 읽고)
                             movups ×4   (스택에 쓴다)
                             call …                          ← 복사 8줄이 보인다
                   call_cref: jmp  _Z8sum_crefRK3Big          ← 주소 하나, 꼬리 점프
```

- ★★★ **같은 소스·같은 `-O2` 인데 플래그 하나로 결론이 뒤집힌다.**\
  **한 판만 돌려 놓고 「이쪽이 느리다」라고 쓰면 그 문장은 거짓이 될 수 있다.**
- ★★★ **그래서 이 문서는 시간을 한 번도 재지 않았고, 「몇 배」라는 말을 쓰지 않는다.**\
  근거로 쓰는 것은 **① 복사·이동 횟수 ② 할당 횟수 ③ 명령어 열** 셋뿐이고,\
  셋 다 **다시 돌리면 같은 값이 나오는 것**이다.
- ★★ **읽을 것은 「무엇이 사라질 수 있나」다** — 인라인되면 **전달 방식의 차이 자체가 없어진다.**\
  ★ 차이가 남는 자리는 **번역 단위를 넘는 호출**과 **인라인이 안 되는 큰 함수**다.

**비용** — 이 절의 결론은 수치가 아니다: 「**전달 방식의 비용은 호출 지점의 최적화에 달렸다**」는 것.

### (9) `std::span` — 연속된 것이면 무엇이든

**언제 쓰나** — 정수 배열처럼 **연속된 것**을 읽기만 할 때.

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

| 넘긴 것 | `const std::vector<int>&` | `std::span<const int>` |
|---|---|---|
| `std::vector<int>` | 0회 | 0회 |
| C 배열 `int[3]` | ★★★ **new 1회** | ★★★ **0회** |
| `std::array<int,3>` | ★ (이 문서는 던지지 않았다) | ★ **0회** |

- ★★★ **`const std::vector&` 로 C 배열을 받으려면 벡터를 하나 만들어야 한다** — **읽기만 할 건데 힙을 쓴다.**
- ★★ **`span` 은 컨테이너 종류를 안 묻는다.** 「**연속 메모리 + 길이**」만 요구한다.
- ★ **`span<const int>` 로 받으면 읽기 전용**이 된다 — `span<int>` 로 받으면 고칠 수 있다.\
  ★ 「고칠 수 있음」을 **타입으로** 말하는 자리라 형제 [`07번`](../07-references-vs-pointers/)의 「없음을 타입으로」와 같은 집안이다.
- ★ 배열을 그냥 매개변수로 쓰면 **포인터로 감쇠해 길이가 사라진다** — 그 정본은 C 갈래\
  [`16-array-pointer-decay-and-function-parameters/`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/)다.\
  **`span` 은 그 감쇠에 길이를 다시 붙인 것**으로 읽으면 쉽다.

**비용** — 읽기만 하는 연속 데이터: `span` 이 **C 배열에서 할당 1회를 없애고**, 받을 수 있는 타입을 넓힌다.

### (10) 고르는 기준 — 표 하나

★★★ **이 표의 「근거」 칸은 전부 위에서 센 수치다.** 취향이 아니다.

| 무엇을 하나 | 무엇으로 받나 | 근거(이 문서에서 센 것) |
|---|---|---|
| 읽기만 · 작은 내장 타입(`int`·포인터) | ★ **값** | (7) `lea` 한 줄 대 메모리 두 번 |
| 읽기만 · 큰 타입 | ★ **`const T&`** | (2) 네 칸 모두 copy 0 |
| 읽기만 · 문자열 | ★★ **`std::string_view`** | (5) 리터럴·`const char*` 에서 new 1회 → 0회 |
| 읽기만 · 연속 배열 | ★★ **`std::span<const T>`** | (9) C 배열에서 new 1회 → 0회 |
| 보관한다 · 호출이 임시 위주 | **`T&&`** | (3) copy 0 · move 1 |
| 보관한다 · lvalue 와 임시가 섞인다 | ★★★ **값 + `std::move`** | (4) 오버로드 쌍과 같은 할당 수 · 코드 절반 |
| 보관한다 · 이동이 비싼 타입 | **`const T&` / `T&&` 오버로드 쌍** | (3) 값 전달만 lvalue 에서 이동 1회를 더 쓴다 |
| 인자 그대로 다른 함수에 넘긴다 | **`T&&` + `std::forward`** | (3) `by_fwd` 가 오버로드 쌍과 동일 |
| 받은 것을 **고쳐서 돌려준다** | **`T&`** | ★ 이 문서는 **던지지 않았다**(형제 [`07번`](../07-references-vs-pointers/)이 정본) |

- ★★ **줄 하나로 줄이면**: 「**읽기만 하면 빌리고, 보관하면 값으로 받아 옮긴다.**」
- ★ **예외는 두 개뿐**이다 — **작은 내장 타입**(값이 낫다)과 **이동이 비싼 타입**(오버로드 쌍).

### (11) 다섯 층 — 무엇이 표준이고 무엇이 도구인가

★★ **이 주제는 「표준」과 「관용구」가 섞여 있다.** 참조 묶기·오버로드 선택은 표준이 정하지만,\
**「그래서 무엇으로 받나」는 표준이 정해 주지 않는다** — 그래서 **세어서** 정한다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | **값 매개변수가 복사·이동 생성자를 부른다는 것** · **`const T&` 가 임시를 받는다는 것** · **`T&&` 가 lvalue 를 못 받는다는 것** · **prvalue 인자가 매개변수로 물질화된다는 것**((2)) · **`std::forward` 가 범주를 보존한다는 것**((3)) · **`span`·`string_view` 가 소유하지 않는다는 것** | 복사·이동 로그 14줄 · 할당 계수 22줄 | ★★★ **「그래서 무엇으로 받아야 하나」는 표준에 없다** — 그것이 이 주제가 「관용구」인 이유다 |
| **조건부 표준** | 표준판이 있을 때만 | ★ **`T&&`·`std::move`·`std::forward` 는 C++11부터** · ★ **`std::string_view` 는 C++17부터** · ★ **`std::span` 은 C++20부터** · ★★ **prvalue 를 값 매개변수로 넘길 때 복사가 0인 것은 C++17부터**(그 전에는 「허용된 생략」) | `-std=c++20` 으로 전부 빌드 · 물질화의 판 차이는 [목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/)에서 `-std=c++14` 와 대조했다 | ★ **`-std=` 를 낮추면 (2)의 `copy 0` 이 보장이 아니게 된다** — 이 문서는 C++20 만 던졌다 |
| **구현 정의** | 문서화 의무가 있다 | ★★ **짧은 문자열 최적화(SSO)의 경계** — 40자는 힙, 5자는 아니었다((5)) · **`std::string` 의 이동이 할당을 안 하는 것** · **ABI 상 `Big` 이 스택으로 실려 가는 것**((7)) · 진단 문구 · `-Wdangling-gsl` 이 clang 에만 있는 것 | 할당 계수 · `objdump` | ★★ **SSO 경계는 라이브러리가 정한다** — 실험의 40자는 **그 경계 밖이라고 확인한 값**이지 표준값이 아니다 |
| **미명시** | 몇 가지 중 하나 | ★ **인라인 여부**((8)) — 같은 `-O2` 인데 `-fno-inline` 하나로 복사가 나타났다 사라졌다 한다 | `-O2` 와 `-O2 -fno-inline` **두 판** | ★★★ **한 판만 돌리면 정반대 결론이 나온다** |
| **UB** | 아무 일이나 | ★★★ **죽은 임시를 가리키는 `string_view` 를 읽는 것**((6)) | ASan `heap-use-after-free` · `run exit=1` | ★★★ **g++ 는 경고 0건** · **clang 만 1건** · **둘 다 `cc exit=0`** |

**「도구가 못 보는 것」을 층마다 — 전용 표**

| 사실 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | ASan | 비고 |
|---|---|---|---|---|
| 전달 방식별 복사·이동 횟수((2)(3)) | — | — | — | ★★★ **로그를 심어야만 보인다.** 진단은 한 줄도 안 난다 |
| 임시 문자열이 생기는 자리((4)(5)) | — | — | — | ★★ **`operator new` 를 갈아 끼워야 보인다** |
| C 배열을 벡터로 만드는 비용((9)) | — | — | — | ★ 코드에 `std::vector<int>(…)` 가 **적혀 있는데도** 진단은 없다 |
| ★★★ **`string_view` 댕글링**((6)) | ★★★ **경고 0건 · `cc exit=0`** | **경고 1건**(`-Wdangling-gsl`) · `cc exit=0` | ★ **`heap-use-after-free` · `run exit=1`** | ★★★ **컴파일러 하나는 완전히 침묵한다** |
| 값 전달이 인라인으로 사라지는 것((8)) | — | — | — | ★★ **`objdump` 로만 보이고, 플래그를 바꿔 두 판을 떠야 보인다** |

- ★★★ **「종료 코드가 0인데 ill-formed」 — 이 갈래의 고정 항목이다.**\
  ★ **그런데 이 주제에서는 그 모양이 나오지 않았다.** 대신 **한 겹 더 나쁜 것**이 나왔다 —\
  (6)의 프로그램은 **ill-formed 조차 아니다.** 표준상 **적법한 프로그램**이고,\
  **`-pedantic-errors` 로도 잡을 것이 없다**(위반한 것이 문법이 아니라 **수명**이기 때문이다).\
  ★★ 「종료 코드가 0인데 ill-formed」는 **`-pedantic-errors` 라는 처방이라도 있지만**,\
  **이쪽은 처방이 「다른 컴파일러를 한 번 더 돌린다」와 「sanitizer 를 켠다」뿐**이다.\
  ★ 「`char* p = "abc";` 가 `cc exit=0` 인데 ill-formed」인 정본 사례는 [목록의 **10번 주제**](../10-const-correctness/)에 있다.

## 문법 — 형태와 규칙

### 형태

```cpp
/* pass01.cpp */
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
```

- 매개변수 자리에 쓸 수 있는 다섯 모양이 위 파일에 다 있다 — `T` · `const T&` · `T&&` · `T&&`(템플릿) · 오버로드 쌍.
- ★ **`static Probe keep;`** 은 「보관한다」를 흉내 내는 자리다. 멤버 대입이 **한 번 더** 세어지므로\
  (2)의 「읽기만」과 (3)의 「보관」이 **같은 프로그램 안에서 갈린다.**

### 뷰로 받는 형태

```cpp
/* pass03.cpp */
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
```

- ★ **`std::string_view` 는 값으로 받는다.** 포인터와 길이 두 칸이라 **`const std::string_view&` 로 받을 이유가 없다.**
- ★★ `operator new` 를 교체한 여덟 줄이 이 문서의 **창 ②**다. 프로그램이 **자기 할당을 직접 센다.**

### 주의 사례 — 컴파일은 되는데 틀린 것

```cpp
/* pass04.cpp */
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
```

- ★★★ **이 파일은 경고 없이 컴파일된다**(g++ 기준). 틀린 것은 **수명**이다((6)).
- ★ 고치는 법은 둘 — **`std::string sv = make();`** 로 소유하거나,\
  **`const std::string& sv = make();`** 로 수명을 늘린다(그 규칙의 정본은 [목록의 **30번 주제**](../30-dangling-references-and-lifetime-extension/)).

### 고를 것을 손으로 돌리는 순서

```text
   1. 이 함수는 인자를 읽기만 하나?
        예  -> 2번으로
        아니(보관한다) -> 5번으로
   2. 타입이 int·포인터만큼 작나?       예 -> 값
   3. 문자열인가?                        예 -> std::string_view
   4. 연속된 배열인가?                   예 -> std::span<const T>
        아니면 -> const T&
   5. 호출이 임시 위주인가?              예 -> T&&
   6. lvalue 와 임시가 섞이나?           예 -> 값 + std::move
   7. 이동이 비싼 타입인가?              예 -> const T& / T&& 오버로드 쌍
```

## 어디서 틀리나

### 1. ★★★ 「값 전달은 항상 복사한다」

**아니다.** prvalue 를 넘기면 **copy 0** 이다((2)의 `read_value(Probe(2))`).\
**복사가 나는 것은 lvalue 를 넘길 때**이고, 그 답은 **인자의 범주**가 정한다([목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/)).

### 2. ★★★ 「`const T&` 로 받으면 항상 이득이다」

**아니다.** 두 자리에서 진다.\
① **보관할 때** — 임시를 받아도 **복사한다**((3)의 `by_cref(Probe(2))` 가 copy 1).\
② **작은 내장 타입** — 값이 이미 레지스터에 있는데 **주소를 거치게 만든다**((7)).

### 3. ★★★ 「`string_view` 는 `const std::string&` 의 상위 호환이다」

**아니다.** 할당은 줄지만((5)) **수명 책임이 호출하는 쪽으로 옮겨 간다**((6)).\
★ **g++ 는 그 자리를 경고하지 않는다** — 「**빌리는 타입으로 바꾸는 것은 계약을 바꾸는 것**」이다.

### 4. ★★ 「`T&&` 로 받으면 항상 이동한다」

**아니다.** `T&&` 는 **「이동해도 된다」는 허가**일 뿐이고,\
함수 안에서 **`std::move` 를 다시 쓰지 않으면 이동은 안 일어난다**([목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)).\
★ (3)의 `by_rref` 가 move 1 인 것은 본문에 **`keep = std::move(p);`** 가 있기 때문이다.

### 5. ★★ 「값 전달 싱크는 공짜로 오버로드 쌍을 대신한다」

**대체로 맞지만 공짜는 아니다.** lvalue 인자에서 **이동을 한 번 더** 쓴다((3)).\
★ `std::string` 처럼 **이동이 싼 타입**이면 할당 수가 같아서((4)) 대체가 선다.\
★★ **이동이 비싼 타입이면 그 한 번이 그대로 비용**이다 — 그때는 오버로드 쌍이다.

### 6. ★★ 「`const std::vector<int>&` 면 아무 배열이나 받는다」

**아니다.** C 배열이나 `std::array` 를 주면 **벡터를 새로 만들어야** 하고,\
그것이 **힙 할당 1회**다((9)). `std::span` 은 셋 다 **0회**로 받는다.

### 7. ★★ 「측정했더니 값 전달이 느렸다」

★★★ **이 문서는 시간을 재지 않았다.** 그리고 (8)이 보인 대로 **인라인 하나로 복사가 사라진다.**\
「느리다」를 쓰려면 **벤치마크 하네스**가 필요하고, 그때도 **함수 모양과 호출 지점에 달린 답**이 나온다.

### 8. ★ 「뷰는 매개변수로만 쓰면 안전하다」

**대체로 맞다** — 함수가 도는 동안 실인자의 수명이 살아 있기 때문이다.\
★★ **위험해지는 것은 그 뷰를 「저장할」 때**다 — 지역 변수에 담거나((6)) 멤버로 두거나 컨테이너에 넣을 때.

### 9. ★ 「`std::string_view` 는 널 종료를 보장한다」

**아니다.** 뷰는 **(포인터, 길이)** 라 **끝에 `\0` 이 있다는 보장이 없다.**\
★ C API 에 넘기려면 **`std::string` 으로 한 번 만들어야** 하고, 그러면 (5)에서 없앤 할당이 돌아온다.\
★ 이 문서는 그 자리를 **던지지 않았다** — 정본은 목록의 **46번 주제**다.

### 10. ★ 「매개변수에 `const` 를 붙이면 호출하는 쪽에 의미가 있다」

**`const T&` 는 있고 `const T`(값)는 없다.**\
값 매개변수의 `const` 는 **함수 안에서 못 고친다**는 뜻일 뿐, **시그니처의 일부가 아니다.**\
★ 그래서 `void f(int)` 와 `void f(const int)` 는 **같은 함수**로 읽힌다 — ★ **이 문서는 그 자리를 던지지 않았고**, 정본은 [목록의 **10번 주제**](../10-const-correctness/)다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 이 문서의 근거 |
|---|---|---|
| 값 매개변수가 복사/이동 생성자를 부르는 것 | **언어** | (2)(3) 로그 14줄 |
| prvalue 인자를 값으로 받을 때 copy 0 | **언어**(C++17부터) | (2) `read_value(Probe(2))` |
| `const T&` 가 임시를 받는 것 | **언어** | (3) `by_cref(Probe(2))` |
| `T&&` 가 lvalue 를 못 받는 것 | **언어** | [목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/)의 묶기 격자 |
| `std::forward` 가 범주를 보존하는 것 | **언어** | (3) `by_fwd` 가 오버로드 쌍과 동일 |
| `string_view`·`span` 이 소유하지 않는 것 | **언어** | (5)(9) new 0회 |
| ★ **40자가 힙으로 가는 것**(SSO 경계) | **구현**(libstdc++) | (4)(5) 할당 계수 |
| ★ **`std::string` 이동이 할당을 안 하는 것** | **구현** | (4) lvalue 열이 전부 1회 |
| ★ **`Big`(64바이트)이 스택으로 실리는 것** | **ABI**(x86-64 SysV) | (7) `movsd 0x8(%rsp)` |
| ★★ **인라인 여부** | **최적화기**(미명시) | (8) 두 판 대조 |
| ★ `-Wdangling-gsl` 이 있는 것 | **clang 18 만** | (6) g++ 0건 · clang 1건 |

## 언제 쓰고 언제 안 쓰나

- **값으로 받는다** — `int`·포인터·작은 트리비얼 타입 · **싱크 매개변수**(보관할 때).
- **`const T&` 로 받는다** — 큰 타입을 **읽기만** 할 때 · 이동이 비싼 타입을 오버로드 쌍의 한쪽으로.
- **`T&&` 로 받는다** — 보관하는데 **호출이 늘 임시**일 때 · 오버로드 쌍의 다른 한쪽.
- **`T&&`(템플릿) + `std::forward`** — 받은 것을 **그대로 다른 함수에 넘길** 때(정본은 [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)).
- **`std::string_view` / `std::span<const T>`** — **읽기만** 하고 **저장하지 않을** 때.\
  ★ **저장할 거면 쓰지 않는다** — 그때는 `std::string` · `std::vector` 를 값으로 받는다.
- **안 쓰는 자리** — ★ 뷰를 **멤버로 두는 것**(수명을 스스로 못 지킨다) ·\
  ★ 읽기만 하는 함수에 **값 전달**(lvalue 에서 복사 1회를 잃는다) ·\
  ★ 작은 내장 타입에 **`const T&`**(간접만 늘린다).

## 핵심 문장

- **읽기만 하면 빌리고, 보관하면 값으로 받아 옮긴다.** 나머지는 예외 두 개뿐이다.
- **「값 전달은 복사한다」는 인자의 범주에 달렸다** — prvalue 면 복사가 0이다.
- **`const T&` 싱크는 훔쳐도 되는 값을 받아 놓고 못 훔치는 것**이다.
- **값 전달 싱크는 오버로드 쌍과 할당 수가 같고 코드가 절반**이다. 대가는 **lvalue 에서 이동 한 번**.
- **뷰는 할당을 없애고 수명 책임을 옮긴다.** g++ 는 그 자리를 **경고하지 않는다.**
- ★★★ **전달 방식의 비용은 호출 지점의 최적화에 달렸다** — 한 판만 돌려 놓고 단정하지 않는다.

## 관련 자료

- [목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/)(값 범주) — **그쪽은 「어떤 식이 어느 범주인가」까지, 여기는 「그래서 무엇으로 받나」부터.**
- [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)(`std::move`·`std::forward`) — **그쪽은 「캐스트가 무엇을 하나」까지, 여기는 「매개변수 자리에서 어떻게 쓰나」부터.**
- [목록의 **10번 주제**](../10-const-correctness/)(`const` 정확성) — **그쪽은 「`const` 가 무엇을 막나」까지, 여기는 「`const T&` 를 언제 고르나」부터.**
- 형제 [`07번`](../07-references-vs-pointers/)(참조와 포인터) — **그쪽은 「참조가 무엇을 못 하나」까지, 여기는 「매개변수로 어느 참조를 쓰나」부터.**
- 형제 [`01번`](../01-function-overloading-and-overload-resolution/)(오버로드 해석) — **그쪽은 「후보 중 무엇이 뽑히나」까지, 여기는 「후보를 몇 개 둘까」부터.**
- [목록의 **17번 주제**](../17-move-constructor-assignment-and-moved-from-state/)(이동 후 상태) · 목록의 **46번 주제**(`string`/`string_view`) · [목록의 **30번 주제**](../30-dangling-references-and-lifetime-extension/)(댕글링) · 목록의 **53번 주제**(`noexcept` 와 이동).
- C 갈래 [`16-array-pointer-decay-and-function-parameters/`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/) — **그쪽은 「배열이 포인터가 된다」까지, 여기는 「그래서 `span` 으로 길이를 되돌린다」부터.**

## 용어 풀이

- **매개변수(parameter)** — 함수 선언에 적힌 변수. **인자(argument)** 는 호출할 때 실제로 준 식이다.\
  예: `void f(int p)` 의 `p` 가 매개변수, `f(42)` 의 `42` 가 인자.
- **싱크 매개변수(sink parameter)** — 받은 값을 함수가 **보관하는** 매개변수. 예: 세터·생성자.
- **뷰(view)** — 소유하지 않고 가리키기만 하는 타입. `std::string_view` · `std::span`.
- **전달 참조(forwarding reference)** — 템플릿 매개변수 자리의 `T&&`. 정본은 [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/).
- **짧은 문자열 최적화(SSO)** — 짧은 문자열을 힙 대신 객체 안쪽에 담는 구현 기법. **표준 요구가 아니다.**
- **댕글링(dangling)** — 이미 죽은 객체를 가리키는 상태. 예: (6)의 `sv`.
- **`heap-use-after-free`** — 해제된 힙 메모리를 읽거나 쓴 것. ASan 이 내는 진단 종류.
- **인라인(inlining)** — 호출을 함수 본문으로 바꿔 넣는 최적화. ★ **전달 방식의 차이를 통째로 지울 수 있다**((8)).
- **교체 가능한 `operator new`** — 프로그램이 자기 것으로 갈아 끼울 수 있는 전역 할당 함수. 이 문서의 창 ②.

## 더 들어가면

- ★ **인자가 여럿일 때의 조합 폭발** — `const T&` / `T&&` 오버로드 쌍은 인자 하나에 후보가 두 배가 된다.\
  인자 셋이면 여덟 개다. **값 전달이나 전달 참조가 그 폭발을 막는 이유**가 거기 있다.\
  ★ 이 문서는 **인자 하나짜리만 던졌다.**
- ★ **`std::initializer_list` 와 가변 인자 템플릿** — 정본은 형제 [`04번`](../04-brace-initialization-narrowing-and-initializer-list/)과 [목록의 **34번 주제**](../34-variadic-templates-and-pack-expansion/).
- ★ **`std::span` 의 고정 길이 판**(`std::span<const int, 3>`) — 길이를 타입에 넣는다. **이 문서는 동적 길이만 던졌다.**
- ★ **반환 방식** — 이 문서는 **받는 쪽만** 다뤘다. 돌려주는 쪽(값 반환·NRVO)의 정본은 [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)다.
