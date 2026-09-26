# cpp/syntax/17 — 이동 생성자·이동 대입·이동 후 상태 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 이동 생성자](https://en.cppreference.com/w/cpp/language/move_constructor) · [cppreference — 이동 대입 연산자](https://en.cppreference.com/w/cpp/language/move_assignment) · [cppreference — `std::move`](https://en.cppreference.com/w/cpp/utility/move) · [cppreference — `std::vector::push_back`](https://en.cppreference.com/w/cpp/container/vector/push_back) · [GCC 13 Optimize Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Optimize-Options.html)
> **실행 검증** — 이 문서의 모든 출력·진단·어셈블리는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **rustc 1.92.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`move01.cpp` \~ `move11.cpp` · `movers.rs`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 배너도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
> **버전** — 이동 생성자·이동 대입·`std::move`·`noexcept` 는 전부 **C++11부터**다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.
> ★★★ **16 → 17 → 18 은 한 사슬이고 18 이 결론이다.** [16번](../16-copy-constructor-and-copy-assignment/)이 「복사가 무엇을 부르나」를 수로 고정했고,\
> **여기 17 은 그 자리에 「훔치기」를 넣으면 수가 어떻게 바뀌는지**를 본다. 닫는 것은 [목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/)다.
> **경계** — 「**`std::move` 가 캐스트다**」의 정본은 [9번](../09-rvalue-references-move-and-forward/)이고,\
> 여기는 **그 캐스트를 받는 쪽(이동 생성자·이동 대입)을 어떻게 쓰나**만 본다.\
> 「값 범주」는 [8번](../08-value-categories-lvalue-prvalue-xvalue/), 「0/3/5의 법칙」은 [목록의 **18번**](../18-rule-of-zero-three-five-default-delete/),\
> 「`noexcept` 의 전모」는 **53번**, 「`unique_ptr` 의 API」는 **26번 주제**가 정본이다.\
> ★ (3)은 `noexcept` 를 **`vector` 재할당을 가르는 한 낱말로서만** 다룬다 — 계약·최적화 힌트의 전모는 53번이다.
> **대비** — ★★★ Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **8번**([`08-ownership-and-move/`](../../../rust/syntax/08-ownership-and-move/))이 **직접 대비**다.\
> **러스트는 이동이 기본이고, 이동당한 원본을 컴파일러가 막는다.** C++ 은 「유효하되 미지정」으로 두고 **안 막는다** — (8)에서 **양쪽에 같은 코드를 던진다.**
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 어셈블리의 **레지스터 이름**과 명령 배치 · 실행 시간 | ★★★ **어느 특수 멤버가 몇 번 불렸나**(계수 로그) — 이 주제의 답 자체다 |
> | 객체의 주소값 | ★★★ **`malloc`/`free` 횟수** · **이동 뒤 원본 포인터가 널인가** |
> | 두 컴파일러의 **진단 문구** | ★★ **어셈블리의 명령 개수와 `call` 개수** · **`capacity`** |
> | ★ **libstdc++ 가 이동 후 원본에 남기는 값**(구현 층 — (4)) | ★★ **`cc exit`/`run exit`** · **경고 개수** · **`is_nothrow_move_constructible`** |
>
> ★★★ **(4)의 「이동 후 상태」는 관찰로 결론이 안 나는 자리다.** 표준이 말한 것은 「유효하되 미지정」뿐이고,\
> `size()=0` 이라는 **값 자체는 libstdc++ 의 선택**이다. 그 줄은 **구현 층**으로만 읽는다.

## 한눈에 — 쉽게 말하면

**이동은 「이사」가 아니라 「명패 바꿔 달기」다.** 짐은 한 발짝도 안 움직인다.

이삿짐 센터를 부르면 짐을 **하나씩 새 집에 옮겨 담는다** — 그것이 **복사**다.\
그런데 집이 통째로 내 것이 되는 경우가 있다. 그때는 **현관 명패만 바꿔 달면 된다** — 그것이 **이동**이다.

다만 명패를 뗀 옛 주인은 **아직 살아 있다.** 그 사람이 나중에 「내 집 정리해야지」 하고 돌아오면 안 되므로,\
**옛 주인의 손에서 열쇠를 확실히 빼앗아** 두어야 한다. 그것이 **`o.p = nullptr`** 한 줄이다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 짐을 하나씩 옮겨 담는다 | **복사** — 새로 할당한다 | (2) |
| ★★★ **명패만 바꿔 단다** | ★★★ **이동** — 포인터만 가져온다 | (2) |
| ★★★ **옛 주인의 열쇠를 빼앗는다** | ★★★ **원본을 널로 만든다** | (2) |
| 옛 주인은 아직 살아 있다 | ★★ **원본의 소멸자는 여전히 돈다** | (2) |
| 「이사 가겠다」고 **말만** 한 것 | ★★★ **`std::move` 는 캐스트일 뿐이다** | (1) |
| 이삿짐이 **떨어뜨려질 수 있으면** 센터가 안 맡는다 | ★★★ **`noexcept` 가 아니면 `vector` 가 복사로 간다** | (3) |
| 옛 집이 **무슨 상태로 남는지**는 계약에 없다 | ★★ 「**유효하되 미지정**」 | (4) |

> **이동(move)** — 자원의 **소유권을 옮기고 원본을 빈 껍데기로 만드는 것**.\
> 예: (2)에서 `malloc` 이 **1회**만 나고 원본의 `p` 가 **널**이 됐다.

> **이동 후 상태(moved-from state)** — 이동당한 원본이 남는 상태. **표준은 「유효하되 미지정」이라고만 한다.**\
> 예: (4)에서 libstdc++ 의 `std::string` 은 `size()=0` 이었지만 **그 값은 표준이 정한 것이 아니다.**

```text
   복사                                   이동

   a ──> [ 훔칠 것이 여기 있다 ]           a ──> (널)          <- ★ 열쇠를 빼앗았다
                                                  
   b ──> [ 훔칠 것이 여기 있다 ]  <- 새로  b ──> [ 훔칠 것이 여기 있다 ]
              잡은 것                              ^^^ 같은 주소 그대로

   malloc 2회 · free 2회                  malloc 1회 · free 1회
                                          ★ a 의 소멸자는 돌았지만 놓을 것이 없었다
```

- ★★★ **오른쪽 그림의 「(널)」이 이 주제의 전부**다. 그것을 안 하면 [15번](../15-raii-resources-as-types/) (4)의 **이중 해제**로 돌아간다.

## 이 주제가 답하려는 질문

1. **`std::move` 는 무엇을 하나** — **로그로 보면 몇 줄인가**((1)).
2. **「훔쳤다」를 무엇으로 보이나** — **수로** 보일 수 있나((2)).
3. **이동이 안 뽑히고 복사로 되돌아가는 자리는 어디인가**((3)(5)(6)).
4. **이동당한 원본에 무엇을 해도 되나** — 표준이 말한 것은 어디까지인가((4)).
5. **그 계약이 없는 언어는 이 문제를 어떻게 푸나**((8)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ①이다

★★★ **이 주제의 본체는 ① 호출 계수 로그 + 할당 횟수 계수기다.**\
「훔쳤다」는 **말로는 증명이 안 된다** — **`malloc` 이 몇 번 났고 원본 포인터가 널인가**를 봐야 한다.

```text
① 호출 계수 로그 + 할당 계수기   이동인가 복사인가 · malloc/free 몇 번       (1)(2)(3)(5)(6)
② 두 컴파일러 대조                재할당 정책 · 이동 후 값 · 경고            (3)(4)(6)(9)
③ ASan 리포트                     ★ 이 편에서는 침묵한다 — 그것이 결론이다   (9)
④ `-O2` 어셈블리 세기             복사판과 이동판을 나란히 — 명령·call 개수  (7)
⑤ 경고 격자                       탐침 여섯 중 몇이 답하나                   (9)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ★★★ **① 계수 로그 + 할당 계수기** | ★★★ **본체** — (2)의 `malloc 1회` 와 「원본이 널인가 1」이 이 편의 답이다 | **쓴다** |
| ② 두 컴파일러 대조 | (3)의 재할당 정책 · (4)의 이동 후 값 · (6)의 경고 | **쓴다** |
| ③ ASan 리포트 | ★★★ **침묵한다**(0건) — [16번](../16-copy-constructor-and-copy-assignment/)·[목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/)와 갈리는 자리다 | **쓴다(결과가 0이다)** |
| ★★ **④ `-O2` 어셈블리 세기** | ★★ **여기서 비로소 성립한다** — **같은 타입의 복사판과 이동판**을 나란히 센다((7)) | **쓴다** |
| ⑤ 경고 격자 | 탐침 여섯 중 **0개**가 답했다 | **쓴다** |

- ★★ **④가 [16번](../16-copy-constructor-and-copy-assignment/)에서 「부적용」이었던 이유가 여기서 풀린다.** 복사만 따로 재면 **비교 대상이 없다.**\
  같은 구조체의 `make_copy` 와 `make_move` 를 **한 파일에 넣어** 재야 수가 근거가 된다.
- ★★★ **다만 센 것은 명령과 `call` 개수까지다.** **시간은 재지 않았다** — 「이동이 빠르다」는 문장은 이 문서에 **한 줄도 없다.**
- ★★★ **「제5의 상태」가 (4)에 있다** — 「이동 후 원본이 무엇이 되나」는 **관찰로 답이 안 난다.**\
  세 창(로그·값·`empty()`)이 전부 정상인데 틀린 것은 값이 아니라 「**그 값이 보장인가**」다.\
  ★ 그래서 (4)는 **표준이 널로 못 박은 것**(`unique_ptr`)과 **미지정인 것**(`string`·`vector`)을 **한 블록에서 갈라** 찍는다.

### (1) ★★★ `std::move` 는 아무것도 안 옮긴다

**언제 쓰나** — 「`std::move` 를 적었는데 왜 안 옮겨졌지?」에서.

```cpp
/* move01.cpp */
// std::move 는 아무것도 옮기지 않는다 — 캐스트일 뿐임을 로그와 타입으로 보인다
#include <cstdio>
#include <type_traits>
#include <utility>

struct L {
    int id;
    static int n;
    L()                   : id(++n) { std::printf("    기본 생성자  #%d\n", id); }
    L(const L& o)         : id(++n) { std::printf("    복사 생성자  #%d <- #%d\n", id, o.id); }
    L(L&& o)     noexcept : id(++n) { std::printf("    이동 생성자  #%d <- #%d\n", id, o.id); }
    ~L() {}
};
int L::n = 0;

int main() {
    L a;
    std::printf("(1) std::move(a); 만 적는다 — 아래에 로그가 몇 줄 찍히나\n");
    (void)std::move(a);
    std::printf("(2) 그 결과를 초기화에 쓴다  L b = std::move(a);\n");
    L b = std::move(a);
    std::printf("(3) std::move(a) 의 타입은 무엇인가\n");
    std::printf("    decltype(std::move(a)) 가 L&&      인가: %d\n",
                (int)std::is_same_v<decltype(std::move(a)), L&&>);
    L&& r = std::move(a);                      // 이름을 붙여 주소를 물어본다
    std::printf("    &a 와 &r 이 같은 주소인가          : %d\n", (int)(&a == &r));
    std::printf("(4) 만들어진 객체 수 %d개 — (1)에서는 하나도 안 늘었다\n", L::n);
    (void)b;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic move01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
    기본 생성자  #1
(1) std::move(a); 만 적는다 — 아래에 로그가 몇 줄 찍히나
(2) 그 결과를 초기화에 쓴다  L b = std::move(a);
    이동 생성자  #2 <- #1
(3) std::move(a) 의 타입은 무엇인가
    decltype(std::move(a)) 가 L&&      인가: 1
    &a 와 &r 이 같은 주소인가          : 1
(4) 만들어진 객체 수 2개 — (1)에서는 하나도 안 늘었다
```

```text
   std::move(a);          <- 캐스트 하나. 로그가 0줄이다.
        |
        +-- 타입만 L 에서 L&& 로 바뀐다
        +-- 주소는 그대로다 (&a == &r 이 1)
        |
   L b = std::move(a);    <- ★ 여기서 비로소 이동 생성자가 뽑힌다
                              「옮기는 것」은 std::move 가 아니라 생성자·대입이다
```

- ★★★ **`(1)` 에 로그가 한 줄도 안 찍힌다.** `std::move(a);` 만 적으면 **아무 일도 안 일어난다.**
- ★★★ **`decltype(std::move(a))` 가 `L&&` 다**(`1`). **타입만 바꾸는 캐스트**라는 뜻이다.
- ★★ **주소가 같다**(`&a == &r` 이 `1`). 새 객체가 안 생겼다.
- ★ **만들어진 객체 수 2개** — `a` 와 `b` 뿐이다. `(1)`·`(3)` 에서는 하나도 안 늘었다.
- ★ 정본은 [9번](../09-rvalue-references-move-and-forward/)이다. 여기서는 **받는 쪽을 보려고 한 번 못 박았을 뿐**이다.

### (2) ★★★ 「훔쳤다」를 무엇으로 보이나 — 널 + 할당 횟수

**언제 쓰나** — 이동 생성자를 손으로 쓸 때마다. **이 절이 이 주제의 중심이다.**

C++ 에는 **런타임 할당 계수기가 표준에 없다.** 그래서 **소스에 계수기를 심어** 센다.

```cpp
/* move02.cpp */
// 「훔쳤다」를 무엇으로 보이나 — 원본 포인터가 널이 된 것 + 할당 횟수 계수기
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <utility>

static int allocs = 0, frees = 0;

struct Box {
    char*       p;
    std::size_t n;
    explicit Box(const char* s) : p(nullptr), n(std::strlen(s) + 1) {
        p = static_cast<char*>(std::malloc(n)); ++allocs;
        std::memcpy(p, s, n);
    }
    ~Box() { if (p) { std::free(p); ++frees; } }

    Box(const Box& o) : p(static_cast<char*>(std::malloc(o.n))), n(o.n) {   // 복사 — 새로 잡는다
        ++allocs;
        std::memcpy(p, o.p, n);
    }
    Box& operator=(const Box& o) {
        if (this == &o) return *this;
        char* q = static_cast<char*>(std::malloc(o.n)); ++allocs;
        std::memcpy(q, o.p, o.n);
        if (p) { std::free(p); ++frees; }
        p = q; n = o.n;
        return *this;
    }
    Box(Box&& o) noexcept : p(o.p), n(o.n) {                                // 이동 — 훔친다
        o.p = nullptr; o.n = 0;                                             // ★ 원본을 빈 껍데기로
    }
    Box& operator=(Box&& o) noexcept {
        if (this != &o) {
            if (p) { std::free(p); ++frees; }
            p = o.p; n = o.n;
            o.p = nullptr; o.n = 0;
        }
        return *this;
    }
};

int main() {
    std::printf("(1) 복사판\n");
    {
        allocs = frees = 0;
        Box a("훔칠 것이 여기 있다");
        Box b = a;
        std::printf("    a.p 가 널인가 %d · b.p 가 널인가 %d · 같은 주소인가 %d\n",
                    (int)(a.p == nullptr), (int)(b.p == nullptr), (int)(a.p == b.p));
        std::printf("    malloc %d회\n", allocs);
    }
    std::printf("    블록을 나온 뒤 free %d회\n", frees);

    std::printf("(2) 이동판\n");
    {
        allocs = frees = 0;
        Box a("훔칠 것이 여기 있다");
        char* before = a.p;
        Box b = std::move(a);
        std::printf("    a.p 가 널인가 %d · b.p 가 원래 주소 그대로인가 %d\n",
                    (int)(a.p == nullptr), (int)(b.p == before));
        std::printf("    malloc %d회\n", allocs);
    }
    std::printf("    블록을 나온 뒤 free %d회  ★ 원본의 소멸자는 돌았지만 놓을 것이 없었다\n", frees);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic move02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 복사판
    a.p 가 널인가 0 · b.p 가 널인가 0 · 같은 주소인가 0
    malloc 2회
    블록을 나온 뒤 free 2회
(2) 이동판
    a.p 가 널인가 1 · b.p 가 원래 주소 그대로인가 1
    malloc 1회
    블록을 나온 뒤 free 1회  ★ 원본의 소멸자는 돌았지만 놓을 것이 없었다
```

- ★★★ **증거가 세 줄이다.**
  - `a.p 가 널인가 1` — **원본에서 열쇠를 빼앗았다.**
  - `b.p 가 원래 주소 그대로인가 1` — **짐은 안 움직였다.**
  - `malloc 1회` — **복사판은 2회였다.**
- ★★★ **`free` 도 1회다.** 원본 `a` 의 소멸자는 **여전히 돌았지만** `p` 가 널이라 **놓을 것이 없었다.**\
  ★ 그래서 소멸자가 **널을 견뎌야** 한다(`if (p)`). 이것이 [15번](../15-raii-resources-as-types/)의 규칙과 같은 것이다.
- ★★★ **원본을 안 비우면 `free` 가 2회가 되고 그것이 이중 해제다** — [15번](../15-raii-resources-as-types/) (4)가 ASan 의 `double-free` 로 실측했다.\
  ★ 「훔치기」는 **가져오는 절반**과 **비우는 절반**으로 이루어진다. **비우는 쪽을 빼먹는 것이 전형적인 사고**다((9)의 탐침 2번).

### (3) ★★★ `noexcept` 한 낱말이 `vector` 재할당을 가른다

**언제 쓰나** — 이동 생성자를 적을 때마다. **이 자리가 이 주제에서 가장 유명하다.**

`vector` 가 자리를 늘릴 때는 **있던 원소를 새 버퍼로 옮겨야** 한다.\
그런데 옮기다가 **던지면 옛 버퍼도 새 버퍼도 온전하지 않다.** 그래서 표준 라이브러리는 **던지지 않는다고 약속한 이동만** 쓴다.

```cpp
/* move03.cpp */
// noexcept 한 낱말이 vector 재할당에서 이동과 복사를 가른다
#include <cstdio>
#include <type_traits>
#include <vector>

struct Yes {                                     // 이동 생성자에 noexcept 가 있다
    int id; static int n;
    Yes()                     : id(++n) { std::printf("      기본 #%d\n", id); }
    Yes(const Yes& o)         : id(++n) { std::printf("      복사 #%d <- #%d\n", id, o.id); }
    Yes(Yes&& o)     noexcept : id(++n) { std::printf("      이동 #%d <- #%d\n", id, o.id); }
    ~Yes() {}
};
struct No {                                      // 한 낱말만 뺐다
    int id; static int n;
    No()                   : id(++n) { std::printf("      기본 #%d\n", id); }
    No(const No& o)        : id(++n) { std::printf("      복사 #%d <- #%d\n", id, o.id); }
    No(No&& o)             : id(++n) { std::printf("      이동 #%d <- #%d\n", id, o.id); }
    ~No() {}
};
int Yes::n = 0; int No::n = 0;

template <class T>
void grow(const char* tag) {
    std::printf("  [%s] is_nothrow_move_constructible = %d\n",
                tag, (int)std::is_nothrow_move_constructible_v<T>);
    std::vector<T> v;
    v.reserve(2);
    std::printf("    자리 둘을 잡아 두고 둘을 넣는다 (capacity=%zu)\n", v.capacity());
    v.emplace_back();
    v.emplace_back();
    std::printf("    ★ 세 번째를 넣어 재할당을 일으킨다 — 있던 둘이 무엇으로 옮겨지나\n");
    v.emplace_back();
    std::printf("    capacity %zu · size %zu\n", v.capacity(), v.size());
}

int main() {
    std::printf("(1) noexcept 가 있는 타입\n"); grow<Yes>("Yes");
    std::printf("(2) noexcept 가 없는 타입\n"); grow<No>("No");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic move03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) noexcept 가 있는 타입
  [Yes] is_nothrow_move_constructible = 1
    자리 둘을 잡아 두고 둘을 넣는다 (capacity=2)
      기본 #1
      기본 #2
    ★ 세 번째를 넣어 재할당을 일으킨다 — 있던 둘이 무엇으로 옮겨지나
      기본 #3
      이동 #4 <- #1
      이동 #5 <- #2
    capacity 4 · size 3
(2) noexcept 가 없는 타입
  [No] is_nothrow_move_constructible = 0
    자리 둘을 잡아 두고 둘을 넣는다 (capacity=2)
      기본 #1
      기본 #2
    ★ 세 번째를 넣어 재할당을 일으킨다 — 있던 둘이 무엇으로 옮겨지나
      기본 #3
      복사 #4 <- #1
      복사 #5 <- #2
    capacity 4 · size 3
```

```text
   capacity 2 에 둘이 차 있다.  세 번째를 넣으면 버퍼를 새로 잡고 둘을 옮긴다.

   Yes (이동 생성자에 noexcept 있음)      No (한 낱말만 뺐음)
     is_nothrow_move_constructible = 1      is_nothrow_move_constructible = 0
            |                                       |
        이동 #4 <- #1                           복사 #4 <- #1
        이동 #5 <- #2                           복사 #5 <- #2
            ^^^^                                    ^^^^
   ★ 소스의 차이는 `noexcept` 낱말 하나뿐인데 옮기는 방법이 통째로 바뀐다
```

- ★★★ **두 타입의 소스 차이는 `noexcept` 한 낱말뿐**인데 **재할당이 이동과 복사로 갈린다.**
- ★★★ **`is_nothrow_move_constructible` 이 그 판정을 그대로 드러낸다**(`1` 대 `0`).\
  `vector` 가 보는 것이 **그 트레이트**다.
- ★★ **`capacity` 는 양쪽 다 2에서 4로 갔다.** **재할당 정책은 같고 옮기는 방법만 갈린다.**
- ★★ **clang 도 한 글자도 같았다** — 표준 라이브러리도 libstdc++ 로 같다.

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic move03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) noexcept 가 있는 타입
  [Yes] is_nothrow_move_constructible = 1
    자리 둘을 잡아 두고 둘을 넣는다 (capacity=2)
      기본 #1
      기본 #2
    ★ 세 번째를 넣어 재할당을 일으킨다 — 있던 둘이 무엇으로 옮겨지나
      기본 #3
      이동 #4 <- #1
      이동 #5 <- #2
    capacity 4 · size 3
(2) noexcept 가 없는 타입
  [No] is_nothrow_move_constructible = 0
    자리 둘을 잡아 두고 둘을 넣는다 (capacity=2)
      기본 #1
      기본 #2
    ★ 세 번째를 넣어 재할당을 일으킨다 — 있던 둘이 무엇으로 옮겨지나
      기본 #3
      복사 #4 <- #1
      복사 #5 <- #2
    capacity 4 · size 3
```

- ★★★ **그래서 이동 생성자·이동 대입에는 `noexcept` 를 붙이는 것이 기본형이다.**\
  ★ 「붙이면 빨라진다」가 아니라 「**안 붙이면 표준 라이브러리가 안 쓴다**」로 외워야 한다.
- ★ `noexcept` 의 전모(계약·`noexcept` 연산자·위반 시 `terminate`)는 목록의 **53번 주제**다.

### (4) ★★ 이동 후 상태 — 표준이 말한 것과 이 구현이 두는 것

**언제 쓰나** — 「이동한 뒤에 그 변수를 써도 되나?」에서.

★★★ **여기가 다섯 층을 갈라 써야 하는 자리다.** 표준이 말한 것은 두 가지뿐이다.

```cpp
/* move04.cpp */
// 이동 후 상태 — 표준이 보장하는 것과 이 구현이 실제로 두는 것을 갈라 찍는다
#include <cstdio>
#include <memory>
#include <string>
#include <utility>
#include <vector>

int main() {
    std::printf("(1) 표준이 「널」이라고 못 박은 것 — unique_ptr\n");
    std::unique_ptr<int> u1(new int(7));
    std::unique_ptr<int> u2 = std::move(u1);
    std::printf("    u1.get() == nullptr : %d   (표준 보장)\n", (int)(u1.get() == nullptr));
    std::printf("    *u2                 : %d\n", *u2);

    std::printf("(2) 표준이 「유효하되 미지정」이라고만 한 것 — 이 구현이 무엇으로 두나\n");
    std::string s1 = "짧다";
    std::string t1 = std::move(s1);
    std::printf("    짧은 string : size=%zu  empty=%d  capacity=%zu  값=\"%s\"\n",
                s1.size(), (int)s1.empty(), s1.capacity(), s1.c_str());
    std::string s2(64, 'x');
    std::string t2 = std::move(s2);
    std::printf("    긴 string   : size=%zu  empty=%d  capacity=%zu\n",
                s2.size(), (int)s2.empty(), s2.capacity());
    std::vector<int> v1{1, 2, 3};
    std::vector<int> v2 = std::move(v1);
    std::printf("    vector      : size=%zu  capacity=%zu\n", v1.size(), v1.capacity());

    std::printf("(3) 이동당한 원본에 무엇을 해도 되나 — 표준이 허락한 것만\n");
    s1 = "다시 넣는다";                          // 대입은 상태를 안 봐도 된다
    v1.clear();                                  // clear 는 전제조건이 없다
    std::printf("    다시 대입한 뒤 s1 = \"%s\"  ·  clear 뒤 v1.size()=%zu\n", s1.c_str(), v1.size());
    std::printf("    t1=\"%s\" t2.size()=%zu v2.size()=%zu\n", t1.c_str(), t2.size(), v2.size());
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic move04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 표준이 「널」이라고 못 박은 것 — unique_ptr
    u1.get() == nullptr : 1   (표준 보장)
    *u2                 : 7
(2) 표준이 「유효하되 미지정」이라고만 한 것 — 이 구현이 무엇으로 두나
    짧은 string : size=0  empty=1  capacity=15  값=""
    긴 string   : size=0  empty=1  capacity=15
    vector      : size=0  capacity=0
(3) 이동당한 원본에 무엇을 해도 되나 — 표준이 허락한 것만
    다시 대입한 뒤 s1 = "다시 넣는다"  ·  clear 뒤 v1.size()=0
    t1="짧다" t2.size()=64 v2.size()=3
```

```text
   표준이 못 박은 것                     표준이 「유효하되 미지정」이라고만 한 것
   ─────────────────────                 ────────────────────────────────────
   unique_ptr : get() == nullptr          string  : ?      <- 값은 구현이 정한다
   (표준이 널이라고 명시한다)              vector  : ?
                                          ^^^^^^^^^^^^^^^^
                                          여기 찍힌 숫자는 libstdc++ 의 선택이다
   양쪽 모두에 허용된 것
   ─────────────────
   · 다시 대입한다            s1 = "다시 넣는다";
   · 전제조건 없는 연산을 부른다  v1.clear();  ·  size()  ·  empty()
   금지된 것
   ─────────
   · 전제조건이 있는 연산      v1.front()  ·  *u1
```

- ★★★ **`unique_ptr` 만 값이 보장된다** — 표준이 「이동 후 `get()` 은 널」이라고 **명시**한다.
- ★★★ **`string`·`vector` 의 숫자는 보장이 아니다.** 여기 찍힌 `size=0`·`capacity=15`·`capacity=0` 은\
  **libstdc++ 가 그렇게 두었다**는 관찰이다. **다른 구현에서는 다를 수 있다.**
- ★★ **짧은 `string` 과 긴 `string` 의 `capacity` 가 둘 다 15 다** — 이것이 **작은 문자열 최적화(SSO)의 흔적**이다.\
  ★ 긴 쪽은 **버퍼를 넘겨주고 자기는 내부 버퍼로 돌아갔다.** 이런 세부가 바로 **구현 층**이다.
- ★★★ **그래서 코드에 쓸 수 있는 규칙은 하나다** — 「**이동한 뒤에는 대입하거나 파괴한다**」.\
  ★ 「비어 있을 것이다」에 기대면 **구현이 바뀌는 날 조용히 깨진다.**
- ★★ **clang 으로 돌려도 같은 숫자다** — 표준 라이브러리가 같기 때문이다.\
  ★★★ **「두 컴파일러에서 같았다」는 보장이 아니다.** 여기서 갈리는 것은 **컴파일러가 아니라 표준 라이브러리**다.

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic move04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 표준이 「널」이라고 못 박은 것 — unique_ptr
    u1.get() == nullptr : 1   (표준 보장)
    *u2                 : 7
(2) 표준이 「유효하되 미지정」이라고만 한 것 — 이 구현이 무엇으로 두나
    짧은 string : size=0  empty=1  capacity=15  값=""
    긴 string   : size=0  empty=1  capacity=15
    vector      : size=0  capacity=0
(3) 이동당한 원본에 무엇을 해도 되나 — 표준이 허락한 것만
    다시 대입한 뒤 s1 = "다시 넣는다"  ·  clear 뒤 v1.size()=0
    t1="짧다" t2.size()=64 v2.size()=3
```

### (5) ★★ 이동이 복사로 조용히 되돌아가는 자리

**언제 쓰나** — 「`std::move` 를 썼는데 왜 느리지?」가 아니라 **「왜 복사 로그가 찍히지?」에서.**

```cpp
/* move05.cpp */
// 이동이 복사로 조용히 되돌아가는 자리 셋 — 계수 로그로 증명한다
#include <cstdio>
#include <utility>

struct Tr {                                        // 멤버 — 무엇이 불렸는지 말한다
    Tr() {}
    Tr(const Tr&)          { std::printf("      멤버: 복사\n"); }
    Tr(Tr&&)      noexcept { std::printf("      멤버: 이동\n"); }
    ~Tr() {}
};
struct CopyOnly {                                  // 이동이 없는 멤버
    CopyOnly() {}
    CopyOnly(const CopyOnly&) { std::printf("      멤버: 복사(이동 생성자가 없는 타입)\n"); }
    ~CopyOnly() {}
};

struct Good { Tr t; };                             // 멤버가 이동을 갖췄다
struct Half { Tr t; CopyOnly c; };                 // 멤버 하나가 복사만 된다

int main() {
    std::printf("(1) 멤버가 전부 이동 가능하면\n");
    { Good a; Good b = std::move(a); (void)b; }

    std::printf("(2) 멤버 하나가 복사만 되면 — 그 멤버만 복사되나, 전부 복사되나\n");
    { Half a; Half b = std::move(a); (void)b; }

    std::printf("(3) const 를 move 하면\n");
    { const Tr c; Tr d = std::move(c); (void)d; }

    std::printf("(4) const 를 안 붙이면\n");
    { Tr c; Tr d = std::move(c); (void)d; }
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic move05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 멤버가 전부 이동 가능하면
      멤버: 이동
(2) 멤버 하나가 복사만 되면 — 그 멤버만 복사되나, 전부 복사되나
      멤버: 이동
      멤버: 복사(이동 생성자가 없는 타입)
(3) const 를 move 하면
      멤버: 복사
(4) const 를 안 붙이면
      멤버: 이동
```

```text
   std::move(x) 를 썼는데 복사가 뽑히는 세 경로

   x 가 const 다          ->  const T&&  ->  T&& 에 안 맞는다  ->  const T& 로 간다 (복사)
   멤버가 이동을 안 갖췄다  ->  그 멤버만  ->  복사 생성자       (나머지 멤버는 이동)
   받는 쪽이 const& 다     ->  묶이기만 한다                    (아무것도 안 옮겨진다)
   ───────────────────────────────────────────────────────────
   셋 다 에러도 경고도 없다. 로그를 찍어야만 보인다.
```

- ★★★ **`(2)` 가 중요하다** — 멤버 하나가 복사만 되면 **그 멤버만 복사**되고 **나머지는 이동**된다.\
  ★ 「전부 복사로 떨어진다」가 아니다. **멤버별로 갈린다.**
- ★★★ **`(3)` 이 가장 조용한 사고다** — `const Tr` 에 `std::move` 를 쓰면 타입이 `const Tr&&` 가 되고,\
  **이동 생성자는 `Tr&&` 를 받으므로 안 맞는다.** 그래서 **복사 생성자가 뽑힌다.**
- ★★ **에러도 경고도 안 난다.** `(3)` 과 `(4)` 는 소스가 `const` 한 낱말만 다른데 **로그가 갈린다.**
- ★ **처방** — 이동을 기대하는 자리에는 **`const` 를 안 붙인다.** 그리고 **로그로 확인한다.**

### (6) ★ 반환값에 `std::move` 를 쓰면 오히려 생성자가 한 번 더 돈다

**언제 쓰나** — 「돌려줄 때 `std::move` 를 붙이면 좋지 않나?」에서.

```cpp
/* move06.cpp */
// 반환값에 std::move 를 쓰면 — 생략이 막혀 생성자가 한 번 더 돈다
#include <cstdio>
#include <utility>

struct L {
    int id;
    static int n;
    L()                   : id(++n) { std::printf("    기본 생성자  #%d\n", id); }
    L(const L& o)         : id(++n) { std::printf("    복사 생성자  #%d <- #%d\n", id, o.id); }
    L(L&& o)     noexcept : id(++n) { std::printf("    이동 생성자  #%d <- #%d\n", id, o.id); }
    ~L() { std::printf("    소멸자        #%d\n", id); }
};
int L::n = 0;

L plain()  { L t; return t; }                  // 그냥 돌려준다
L moved()  { L t; return std::move(t); }       // std::move 를 붙여 돌려준다

int main() {
    std::printf("(1) return t;\n");            { L a = plain(); (void)a; }
    std::printf("(2) return std::move(t);\n"); { L b = moved(); (void)b; }
    std::printf("(3) 만들어진 객체 수 %d개\n", L::n);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic move06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
move06.cpp: In function ‘L moved()’:
move06.cpp:16:35: warning: moving a local object in a return statement prevents copy elision [-Wpessimizing-move]
   16 | L moved()  { L t; return std::move(t); }       // std::move 를 붙여 돌려준다
      |                          ~~~~~~~~~^~~
move06.cpp:16:35: note: remove ‘std::move’ call
(1) return t;
    기본 생성자  #1
    소멸자        #1
(2) return std::move(t);
    기본 생성자  #2
    이동 생성자  #3 <- #2
    소멸자        #2
    소멸자        #3
(3) 만들어진 객체 수 3개
```

- ★★★ **`return t;` 는 로그가 두 줄**(기본 생성 + 소멸)이고 **`return std::move(t);` 는 네 줄**이다.\
  ★ 이동 생성자가 **한 번 더** 돌고 소멸자도 **한 번 더** 돈다.
- ★★★ **이유는 [16번](../16-copy-constructor-and-copy-assignment/) (2)와 같다** — `return t;` 는 **NRVO 대상**이라 생략될 수 있다.\
  `std::move(t)` 는 **더 이상 「이름 있는 지역 변수」가 아니라 식**이라 **그 생략이 성립하지 않는다.**
- ★★ **이 자리는 두 컴파일러가 다 경고한다** — `-Wpessimizing-move`.\
  ★ **이 주제에서 컴파일러가 말해 주는 거의 유일한 자리**다((9)의 탐침 여섯은 전부 침묵한다).

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic move06.cpp -o ex (cc exit=0) =====
move06.cpp:16:26: warning: moving a local object in a return statement prevents copy elision [-Wpessimizing-move]
   16 | L moved()  { L t; return std::move(t); }       // std::move 를 붙여 돌려준다
      |                          ^
move06.cpp:16:26: note: remove std::move call here
   16 | L moved()  { L t; return std::move(t); }       // std::move 를 붙여 돌려준다
      |                          ^~~~~~~~~~ ~
1 warning generated.
```

- ★ **만들어진 객체 수 3개** — `(1)` 이 1개, `(2)` 가 2개다.

### (7) ★★ 복사판과 이동판을 `-O2` 로 나란히 세면

**언제 쓰나** — 「이동이 정말 덜 하나?」를 **수로** 확인할 때.

★★★ **시간은 재지 않는다.** 이 절이 세는 것은 **명령 개수와 `call` 개수까지**다.

```cpp
/* move08.cpp */
// 복사판과 이동판이 각각 몇 개의 명령으로 컴파일되나 — 개수만 센다(시간은 안 잰다)
#include <cstdlib>
#include <cstring>

struct Box {
    char*         p;
    unsigned long n;
    Box(const Box& o) : p(static_cast<char*>(std::malloc(o.n))), n(o.n) { std::memcpy(p, o.p, n); }
    Box(Box&& o) noexcept : p(o.p), n(o.n) { o.p = nullptr; o.n = 0; }
    ~Box() { std::free(p); }
};

Box make_copy(const Box& a) { return Box(a); }
Box make_move(Box& a)       { return Box(static_cast<Box&&>(a)); }
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 -S -masm=intel move08.cpp -o move08.s && sed -n '/^_Z9make_copyRK3Box:/,/\.cfi_endproc/p' move08.s | grep -vE '^\s*\.(cfi|loc|file|size|type|globl|p2align|section|ident|align)' (exit=0) =====
_Z9make_copyRK3Box:
.LFB63:
	endbr64
	push	r12
	mov	r12, rsi
	push	rbp
	push	rbx
	mov	rbp, QWORD PTR 8[rsi]
	mov	rbx, rdi
	mov	rdi, rbp
	call	malloc@PLT
	mov	QWORD PTR 8[rbx], rbp
	mov	rsi, QWORD PTR [r12]
	mov	rcx, rbp
	mov	QWORD PTR [rbx], rax
	mov	rdx, rbp
	mov	rdi, rax
	call	__memcpy_chk@PLT
	mov	rax, rbx
	pop	rbx
	pop	rbp
	pop	r12
	ret
```

```text
===== sed -n '/^_Z9make_moveR3Box:/,/\.cfi_endproc/p' move08.s | grep -vE '^\s*\.(cfi|loc|file|size|type|globl|p2align|section|ident|align)' (exit=0) =====
_Z9make_moveR3Box:
.LFB64:
	endbr64
	mov	rdx, QWORD PTR [rsi]
	mov	rax, rdi
	mov	QWORD PTR [rsi], 0
	mov	QWORD PTR [rdi], rdx
	mov	rdx, QWORD PTR 8[rsi]
	mov	QWORD PTR 8[rsi], 0
	mov	QWORD PTR 8[rdi], rdx
	ret
```

```text
===== echo "복사판  명령 $(sed -n '/^_Z9make_copyRK3Box:/,/\.cfi_endproc/p' move08.s | grep -cE '^[[:space:]][a-z]') · call $(sed -n '/^_Z9make_copyRK3Box:/,/\.cfi_endproc/p' move08.s | grep -c 'call')" (exit=0) =====
복사판  명령 21 · call 2
===== echo "이동판  명령 $(sed -n '/^_Z9make_moveR3Box:/,/\.cfi_endproc/p' move08.s | grep -cE '^[[:space:]][a-z]') · call $(sed -n '/^_Z9make_moveR3Box:/,/\.cfi_endproc/p' move08.s | grep -c 'call')" (exit=0) =====
이동판  명령 9 · call 0
```

| | 복사판 `make_copy` | 이동판 `make_move` |
|---|---|---|
| 명령 개수 | **21** | **9** |
| ★★★ **`call` 개수** | ★★★ **2**(`malloc` · `__memcpy_chk`) | ★★★ **0** |
| 레지스터 저장/복원 | `push`/`pop` **3쌍** | 없음 |

- ★★★ **근거로 쓸 수 있는 것은 `call` 개수다** — **복사판은 힙에 두 번 다녀오고 이동판은 한 번도 안 간다.**
- ★★ **명령 개수 21 대 9 는 구현 정의**다. 다른 컴파일러·다른 최적화 수준에서 움직인다.
- ★★★ **「그래서 이동이 몇 배 빠르다」는 이 문서에 없다.** 명령 수는 시간이 아니다 —\
  캐시·분기 예측·할당기의 상태가 전부 빠져 있다. **재려면 벤치마크 하네스가 따로 필요하다.**
- ★ [15번](../15-raii-resources-as-types/) (7)이 같은 창을 썼고, 거기서도 결론은 **개수까지**였다.

### (8) ★★★ 러스트는 같은 코드를 컴파일에서 막는다

**언제 쓰나** — 「이동당한 원본을 쓰면 안 된다」를 **누가 강제하나**를 볼 때.

같은 모양의 프로그램을 두 언어에 던진다 — **옮긴 다음 원본을 다시 읽는다.**

```text
===== which rustc && rustc --version (exit=0) =====
/home/jun/.cargo/bin/rustc
rustc 1.92.0 (ded5c06cf 2025-12-08)
```

```rust
// movers.rs
// 러스트는 이동이 기본이고, 이동 후 원본을 컴파일러가 막는다
fn main() {
    let a = String::from("훔칠 것이 여기 있다");
    let b = a;                      // 이동 — clone 이 아니다
    println!("b = {}", b);
    println!("a = {}", a);          // 이동당한 원본을 다시 읽는다
}
```

```text
===== rustc --edition 2021 movers.rs -o exr (exit=1) =====
error[E0382]: borrow of moved value: `a`
 --> movers.rs:6:24
  |
3 |     let a = String::from("훔칠 것이 여기 있다");
  |         - move occurs because `a` has type `String`, which does not implement the `Copy` trait
4 |     let b = a;                      // 이동 — clone 이 아니다
  |             - value moved here
5 |     println!("b = {}", b);
6 |     println!("a = {}", a);          // 이동당한 원본을 다시 읽는다
  |                        ^ value borrowed here after move
  |
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider cloning the value if the performance cost is acceptable
  |
4 |     let b = a.clone();                      // 이동 — clone 이 아니다
  |              ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

```cpp
/* move09.cpp */
// 러스트와 같은 코드를 C++ 로 — 이동당한 원본을 다시 읽는다
#include <cstdio>
#include <string>
#include <utility>

int main() {
    std::string a = "훔칠 것이 여기 있다";
    std::string b = std::move(a);          // 이동
    std::printf("b = %s\n", b.c_str());
    std::printf("a = \"%s\"  (size=%zu)\n", a.c_str(), a.size());   // 이동당한 원본을 다시 읽는다
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic move09.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
b = 훔칠 것이 여기 있다
a = ""  (size=0)
```

```text
   같은 코드 · 다른 시점에 걸린다

   Rust   let b = a;   println!("{}", a);
          └──────────────────┘
          ★ 컴파일이 안 된다 — error[E0382]: borrow of moved value: `a`
            rustc 가 「어디서 옮겼고 어디서 다시 썼는지」를 줄 번호로 짚는다

   C++    auto b = std::move(a);   printf("%s", a.c_str());
          └──────────────────────────────────┘
          ★ 컴파일된다 · 경고 0건 · run exit=0 · 빈 문자열이 찍힌다
            표준이 「유효하되 미지정」이라고만 하므로 이것은 UB 도 아니다
```

- ★★★ **러스트는 컴파일에서 막고 C++ 은 안 막는다.** 이 대비가 (4)의 「유효하되 미지정」이 무엇을 뜻하는지 보인다.
- ★★★ **C++ 쪽은 UB 도 아니다.** `a.size()` 를 부르는 것은 **전제조건이 없는 연산**이라 **합법**이다.\
  ★ 그래서 **sanitizer 도 안 잡는다**((9)의 ASan 0건). **잡을 것이 없다** — 규칙 위반이 아니기 때문이다.
- ★★★ **다만 값은 보장이 아니다.** `""` 와 `size=0` 은 **libstdc++ 의 선택**이다((4)).\
  ★ 「비어 있을 것」에 기대 코드를 쓰면 **에러도 경고도 없이 깨질 수 있다.**
- ★★ **러스트가 치르는 대가도 있다** — 옮긴 값을 **다시 쓸 방법이 아예 없다.** C++ 은 **다시 대입하면 쓸 수 있다**((4)의 `(3)`).
- ★ **러스트에는 「빈 껍데기를 손으로 만드는」 수고가 없다** — [15번](../15-raii-resources-as-types/)이 이미 그 대비를 적었다.\
  이동한 값은 **원본 자리에서 `drop` 되지 않으므로** `o.p = nullptr` 이 필요 없다.

### (9) 경고를 누가 보나 — 탐침 여섯

「경고가 안 났다」를 산문으로 적으면 **안 물어본 것과 물었는데 조용한 것이 구분되지 않는다.**\
그래서 **이동에서 틀리는 자리 여섯 개**를 한 파일에 심고 두 컴파일러에 똑같이 물었다.

```cpp
/* move07.cpp */
// 이동에서 틀리는 자리 여섯을 심었다 — 컴파일러가 몇 군데에서 말하는지 센다
#include <cstdio>
#include <string>
#include <utility>
#include <vector>

struct Q1 {                                   // 1. 이동 생성자에 noexcept 를 안 붙였다
    std::string s;
    Q1() {}
    Q1(const Q1& o) : s(o.s) {}
    Q1(Q1&& o) : s(std::move(o.s)) {}
};
struct Q2 {                                   // 2. 이동 생성자가 원본을 비우지 않는다
    int* p;
    Q2() : p(new int(1)) {}
    ~Q2() { delete p; }
    Q2(const Q2& o) : p(new int(*o.p)) {}
    Q2(Q2&& o) noexcept : p(o.p) {}           // o.p 를 널로 안 만들었다 — 이중 해제가 열린다
};

void use_after_move() {                       // 3. 이동한 뒤 원본을 다시 읽는다
    std::string a = "무엇이 남나";
    std::string b = std::move(a);
    std::printf("    이동 뒤 a.size()=%zu b.size()=%zu\n", a.size(), b.size());
}
void move_a_const() {                         // 4. const 객체에 std::move 를 쓴다
    const std::string a = "복사로 되돌아간다";
    std::string b = std::move(a);
    (void)b;
}
void move_into_const_ref() {                  // 5. std::move 의 결과를 const& 로 받는다
    std::string a = "옮겨지지 않는다";
    const std::string& r = std::move(a);
    (void)r;
}
void push_without_reserve() {                 // 6. 이동이 없는 타입을 vector 에 담는다
    std::vector<Q1> v;
    for (int i = 0; i < 4; ++i) v.push_back(Q1());
}

int main() {
    Q1 a; Q1 b = std::move(a); (void)b;
    Q2 c; Q2 d = std::move(c); d.p = nullptr;  // 이중 해제를 피해 치운다
    use_after_move();
    move_a_const();
    move_into_const_ref();
    push_without_reserve();
    std::printf("여섯 자리 전부 컴파일됐다\n");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic move07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
    이동 뒤 a.size()=0 b.size()=16
여섯 자리 전부 컴파일됐다
```

```text
===== echo "move07 탐침 여섯  g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic move07.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
move07 탐침 여섯  g++ 경고 0
===== echo "move07 탐침 여섯  clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic move07.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
move07 탐침 여섯  clang 경고 0
===== echo "move07 을 ASan 으로 돌리면: $(g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. move07.cpp -o exa 2>/dev/null; ./exa >/dev/null 2>asan17.txt; grep -cE 'ERROR: (Address|Leak)Sanitizer' asan17.txt) 건" (exit=0) =====
move07 을 ASan 으로 돌리면: 0 건
===== echo "그 리포트의 요약: $(grep -hE '^SUMMARY' asan17.txt | head -1 | grep . || echo 리포트 없음)" (exit=0) =====
그 리포트의 요약: 리포트 없음
```

| 심은 것 | g++ | clang | ASan | 실제로는 |
|---|---|---|---|---|
| 1. 이동 생성자에 `noexcept` 를 안 붙였다 | 0 | 0 | — | ★★★ `vector` 재할당이 **복사로 간다**((3)) |
| 2. 이동 생성자가 원본을 안 비운다 | 0 | 0 | — | ★★★ **이중 해제가 열린다**((2)) |
| 3. 이동한 뒤 원본을 다시 읽는다 | 0 | 0 | — | ★★ 값은 **미지정**이다((4)) |
| 4. `const` 객체에 `std::move` | 0 | 0 | — | ★★ **복사로 되돌아간다**((5)) |
| 5. `std::move` 의 결과를 `const&` 로 받는다 | 0 | 0 | — | ★ **아무것도 안 옮겨진다** |
| 6. 이동이 `noexcept` 가 아닌 타입을 `vector` 에 담는다 | 0 | 0 | — | ★★★ 자랄 때마다 **복사**다((3)) |

```text
   이 배치 네 편의 「누가 말해 주나」

   16 복사    컴파일러 1 / 6   ASan 24바이트 누수
   17 이동    컴파일러 0 / 6   ASan 0건          <- ★ 여기
   18 법칙    컴파일러 2 / 6   ASan 8바이트 누수
   19 상속    컴파일러 1 / 8   ASan new-delete-type-mismatch
   ────────────────────────────────────────────────
   17 만 sanitizer 까지 침묵한다 — 이동의 사고는 「규칙 위반」이 아니기 때문이다
```

- ★★★ **탐침 여섯 중 답한 것 0, 침묵한 것 6이다.** **`cc exit=0`** 이고 **`run exit=0`** 이다.
- ★★★ **ASan 도 0건이다.** [16번](../16-copy-constructor-and-copy-assignment/)은 **24바이트 누수**를, [목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/)는 **8바이트 누수**를 잡았는데\
  **여기는 리포트가 아예 없다.**
- ★★★ **이 주제가 이 배치에서 가장 조용하다.** 이유가 분명하다 — 이동의 사고는 대부분 **「규칙 위반」이 아니라** 「**기대와 다름**」이기 때문이다.\
  `noexcept` 를 안 붙인 것도, `const` 를 `move` 한 것도 **전부 합법**이다. 그래서 도구가 말할 것이 없다.
- ★★★ **그 자리를 메우는 것이 계수 로그뿐이다** — (3)·(5)가 **복사 로그를 직접 찍어** 보인 것이 유일한 근거다.\
  ★ 예외가 하나 있다 — **(6)의 `-Wpessimizing-move`.** 이 주제에서 컴파일러가 말해 주는 거의 유일한 자리다.

## 문법 — 형태와 규칙

### 형태

```cpp
/* move10.cpp */
// 이동 한 벌의 형태 — 5의 법칙을 지킨 타입. 이 파일은 그대로 컴파일된다
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <new>
#include <utility>

class Buffer {
public:
    explicit Buffer(std::size_t n) : n_(n), p_(alloc(n)) {}
    ~Buffer() { std::free(p_); }                                   // ① 널을 견딘다

    Buffer(const Buffer& o) : n_(o.n_), p_(alloc(o.n_)) {          // ② 복사 — 새로 잡는다
        std::memcpy(p_, o.p_, n_);
    }
    Buffer& operator=(const Buffer& o) {                           // ③ 복사 대입 — 잡고 나서 놓는다
        if (this == &o) return *this;
        char* q = alloc(o.n_);
        std::memcpy(q, o.p_, o.n_);
        std::free(p_);
        p_ = q; n_ = o.n_;
        return *this;
    }
    Buffer(Buffer&& o) noexcept : n_(o.n_), p_(o.p_) {             // ④ 이동 — 훔치고 비운다
        o.p_ = nullptr; o.n_ = 0;                                  //    ★ noexcept 가 계약이다
    }
    Buffer& operator=(Buffer&& o) noexcept {                       // ⑤ 이동 대입
        if (this != &o) {
            std::free(p_);
            p_ = o.p_; n_ = o.n_;
            o.p_ = nullptr; o.n_ = 0;
        }
        return *this;
    }
    std::size_t size() const noexcept { return n_; }

private:
    static char* alloc(std::size_t n) {
        char* q = static_cast<char*>(std::malloc(n));
        if (!q) throw std::bad_alloc();
        return q;
    }
    std::size_t n_;
    char*       p_;
};

int main() {
    Buffer a(64);
    Buffer b = std::move(a);
    Buffer c(8);
    c = std::move(b);
    std::printf("a=%zu b=%zu c=%zu\n", a.size(), b.size(), c.size());
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic move10.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a=0 b=0 c=64
```

### 규칙

- **이동 생성자는 `T(T&&) noexcept`** 이고 **이동 대입은 `T& operator=(T&&) noexcept`** 다.
- ★★★ **`noexcept` 는 장식이 아니다** — 없으면 `vector` 재할당이 **복사로 간다**((3)).
- **훔치기는 두 절반이다** — ① 자원을 **가져오고** ② **원본을 빈 껍데기로 만든다.** ②를 빼먹으면 이중 해제다.
- **소멸자는 널을 견뎌야 한다**(`free(nullptr)`·`if (p)`). 이동당한 원본이 그 자리로 온다.
- **이동 대입도 자기 대입을 막는다**(`if (this != &o)`). 자기를 이동하면 **자기 자원을 놓고 자기에게서 훔치게** 된다.
- ★★ **이동한 뒤 원본에 해도 되는 것은 「대입」과 「전제조건 없는 연산」뿐**이다((4)).
- ★ **`const` 를 `std::move` 하지 않는다** — 조용히 복사로 되돌아간다((5)).
- ★ **`return std::move(t);` 를 쓰지 않는다** — 생략을 막는다((6)).

### 금지 사례 — 세 줄이 각각 막힌다

```cpp
/* move11.cpp */
// 이동에 얽힌 세 줄이 각각 막힌다
#include <memory>
#include <utility>
struct MoveOnly {
    int v = 0;
    MoveOnly() = default;
    MoveOnly(const MoveOnly&)            = delete;
    MoveOnly& operator=(const MoveOnly&) = delete;
    MoveOnly(MoveOnly&&) noexcept        = default;
};
void by_value(MoveOnly m) { (void)m; }

int main() {
    std::unique_ptr<int> u(new int(1));
    std::unique_ptr<int> v = u;      // 1. unique_ptr 은 복사가 지워져 있다

    MoveOnly a;
    by_value(a);                     // 2. 이동 전용 타입은 이름으로 넘길 수 없다

    MoveOnly b;
    MoveOnly&& r = b;                // 3. rvalue 참조는 lvalue 에 못 묶는다
    (void)v; (void)r;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 move11.cpp -o ex (cc exit=1) =====
move11.cpp: In function ‘int main()’:
move11.cpp:15:30: error: use of deleted function ‘std::unique_ptr<_Tp, _Dp>::unique_ptr(const std::unique_ptr<_Tp, _Dp>&) [with _Tp = int; _Dp = std::default_delete<int>]’
   15 |     std::unique_ptr<int> v = u;      // 1. unique_ptr 은 복사가 지워져 있다
      |                              ^
In file included from /usr/include/c++/13/memory:78,
                 from move11.cpp:2:
/usr/include/c++/13/bits/unique_ptr.h:522:7: note: declared here
  522 |       unique_ptr(const unique_ptr&) = delete;
      |       ^~~~~~~~~~
move11.cpp:18:13: error: use of deleted function ‘MoveOnly::MoveOnly(const MoveOnly&)’
   18 |     by_value(a);                     // 2. 이동 전용 타입은 이름으로 넘길 수 없다
      |     ~~~~~~~~^~~
move11.cpp:7:5: note: declared here
    7 |     MoveOnly(const MoveOnly&)            = delete;
      |     ^~~~~~~~
move11.cpp:11:24: note:   initializing argument 1 of ‘void by_value(MoveOnly)’
   11 | void by_value(MoveOnly m) { (void)m; }
      |               ~~~~~~~~~^
move11.cpp:21:20: error: cannot bind rvalue reference of type ‘MoveOnly&&’ to lvalue of type ‘MoveOnly’
   21 |     MoveOnly&& r = b;                // 3. rvalue 참조는 lvalue 에 못 묶는다
      |                    ^
```

- ★★★ **세 에러의 이유가 전부 다르다.**
  - **`unique_ptr` 복사** — 표준이 복사를 `= delete` 했다. **이동 전용 타입**이다.
  - **이동 전용 타입을 값으로 넘기기** — 값 전달은 **복사**다. `by_value(std::move(a))` 라야 한다.
  - **`T&& r = b;`** — rvalue 참조는 **lvalue 에 못 묶는다.** `T&& r = std::move(b);` 라야 한다.
- ★★ **세 번째가 (1)의 짝이다** — `std::move` 는 **그 바인딩을 성립시키는 캐스트**이지 옮기는 동작이 아니다.

## 어디서 틀리나

### 1. ★★★ 「`std::move` 를 썼으니 옮겨졌다」

(1)이 그 자리다 — `std::move(a);` 만 적으면 **로그가 0줄**이다.\
**옮기는 것은 이동 생성자·이동 대입**이고, `std::move` 는 **그것이 뽑히게 하는 캐스트**다.

### 2. ★★★ 「`noexcept` 는 붙이면 좋은 장식이다」

(3)이 보인 것은 **재할당이 이동과 복사로 갈리는 것**이다. **소스 차이는 한 낱말**이었다.\
★ 「붙이면 빨라진다」가 아니라 「**안 붙이면 표준 라이브러리가 이동을 안 쓴다**」로 외운다.

### 3. ★★★ 「이동한 뒤 원본은 비어 있다」

(4)가 보인 것은 **`unique_ptr` 만 보장된다**는 것이다.\
`string`·`vector` 의 숫자는 **libstdc++ 의 선택**이고, 표준이 말한 것은 「유효하되 미지정」뿐이다.

### 4. ★★ 「이동한 원본은 파괴되지 않는다」

(2)의 `free 1회` 가 그 반증이다 — **소멸자는 돌았고 놓을 것이 없었을 뿐**이다.\
★ 그래서 **소멸자가 널을 견뎌야** 한다. 러스트는 **이 수고가 없다**((8)).

### 5. ★★ 「`std::move` 를 쓰면 무조건 이동이다」

(5)의 `(3)` 이 그 자리다 — `const` 를 `move` 하면 **복사가 뽑힌다.** **에러도 경고도 없다.**

### 6. ★★ 「돌려줄 때 `std::move` 를 붙이면 좋다」

(6)이 보인 것은 **생성자가 한 번 더 도는 것**이다. `-Wpessimizing-move` 가 그 자리를 가리킨다.

### 7. ★ 「도구가 잡아 주겠지」

**탐침 여섯이 전부 0건이고 ASan 도 0건**이다((9)). 이 주제는 **이 배치에서 가장 조용하다.**

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「미명시」 칸이 결론 자체다** — (4)의 이동 후 상태가 거기 있다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **`std::move` 는 캐스트**((1)) · **이동한 원본도 파괴된다**((2)) · ★★★ **`vector` 재할당은 `noexcept` 이동만 쓴다**((3)) · ★★★ **`unique_ptr` 의 이동 후 `get()` 은 널**((4)) · **`const` rvalue 에는 이동이 안 뽑힌다**((5)) · **`std::move(t)` 반환은 NRVO 대상이 아니다**((6)) | 계수 로그 · 트레이트 출력 · 진단 + `cc exit` | ★★★ 「**이 줄에서 이동이 뽑혔나 복사가 뽑혔나**」 — 로그를 심기 전에는 안 보인다((5)) |
| **조건부 표준** | 특정 조건에서만 보장 | ★ **이동 연산·`noexcept` 는 전부 C++11부터** · `-Wpessimizing-move` 는 **표준이 아니라 컴파일러의 호의**다((6)) | `-std=c++20` 으로만 돌렸다 | ★ **C++03 판으로는 안 돌려 봤다**(거기에는 이동이 없다) |
| **구현 정의** | 문서화 의무가 있다 | ★★★ **(7)의 명령 개수 21 대 9** · **진단 문구** · **`vector` 의 성장 배수**(2배) | `-S -masm=intel` · 세기 블록 | ★★ **다른 ABI·다른 컴파일러에서는 다른 수가 나온다** |
| **미명시** | 몇 가지 중 하나 | ★★★ **(4)의 숫자 전부** — `string` 의 `size=0`·`capacity=15` · `vector` 의 `capacity=0` 은 **libstdc++ 의 선택**이다 | `-std=c++20` 두 컴파일러 · 같은 표준 라이브러리 | ★★★ **두 컴파일러가 같았다는 것이 보장의 근거가 못 된다** — **같은 libstdc++ 를 썼기 때문**이다 |
| **UB** | 아무 일이나 | ★★ **원본을 안 비운 이동 뒤의 이중 해제**((9)의 탐침 2번 · [15번](../15-raii-resources-as-types/) (4)) | ASan `double-free`(그 편) | ★★★ **「이동한 원본을 읽는 것」은 UB 가 아니다** — 그래서 ASan 이 **아무 말도 안 한다**((9)) |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | ASan | 계수 로그 |
|---|---|---|---|---|---|
| 이동 전용 타입을 복사하려 함 | 표준 | **error** | **error** | — | — |
| `T&& r = lvalue;` | 표준 | **error** | **error** | — | — |
| ★★ **`return std::move(t);`** | 조건부 | ★★ **warning 1** | ★★ **warning 1** | — | ★ 로그 2줄 더 |
| ★★★ **`noexcept` 를 안 붙인 이동** | 표준 | ★★★ **0건** | ★★★ **0건** | ★★★ **0건** | ★★★ **(3)의 복사 로그만** |
| ★★★ **원본을 안 비운 이동** | UB | ★★★ **0건** | ★★★ **0건** | ★ **그 경로를 밟아야 `double-free`** | ★ `free` 2회 |
| ★★★ **`const` 를 `move` 함** | 표준 | ★★★ **0건** | ★★★ **0건** | ★★★ **0건** | ★★★ **(5)의 복사 로그만** |
| 이동한 원본을 다시 읽음 | 미명시 | ★★★ **0건** | ★★★ **0건** | ★★★ **잡을 것이 없다**(UB 가 아니다) | ★ 값이 비어 있다 |

- ★★ **이 표의 결론 세 줄**
  - **이동의 「형태」가 틀린 것만 컴파일에서 걸린다** — 첫 두 줄.
  - ★★★ **이동의 「논리」가 틀린 것은 컴파일러도 ASan 도 하나도 못 본다.** 유일한 예외가 `-Wpessimizing-move` 다.
  - ★★★ **그래서 이 주제는 계수 로그 없이는 아무것도 증명되지 않는다.**

### ★ 진단이 0줄인 것도 블록으로 받았다

(9)가 그 자리다. **탐침 여섯 중 답한 것 0, 침묵한 것 6**이고 **`cc exit=0`** 이다.\
★★★ **ASan 도 0건이다** — 이 배치 네 주제 중 **유일하게 sanitizer 까지 침묵한 편**이다.\
그 침묵을 메우는 것이 **(2)(3)(5)의 계수 로그**와 **(8)의 러스트 진단**이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 자원을 직접 드는 타입 | ★★★ **이동을 열고 `noexcept` 를 붙인다** | 안 붙이면 `vector` 가 복사로 간다((3)) |
| 자원을 `unique_ptr`·`vector` 에 맡겼다 | ★★★ **아무것도 안 쓴다** | 멤버가 알아서 이동한다([목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/)) |
| 복사가 뜻이 없는 타입 | ★★ **복사를 `= delete` 하고 이동만 연다** | 이동 전용 타입 — [15번](../15-raii-resources-as-types/) (4) |
| 큰 것을 돌려준다 | ★ **그냥 `return t;`** | `std::move` 는 생략을 막는다((6)) |
| 컨테이너에 넣는다 | ★★ **`push_back(std::move(x))` 또는 `emplace_back`** | 이름 있는 변수는 lvalue 라 복사로 간다 |
| 두 번 쓸 값이다 | ★★★ **옮기지 않는다** | 옮긴 뒤의 값은 미지정이다((4)) |
| 옮긴 뒤 다시 쓰고 싶다 | ★ **먼저 대입한다** | 대입은 전제조건이 없다((4)의 `(3)`) |
| `const` 로 받은 것을 옮기고 싶다 | ★★ **받는 형태를 고친다** | `const` 를 `move` 하면 복사다((5)) |

- ★ **「이동을 쓰지 마라」가 아니라 「이동이 뽑혔는지 로그로 확인하라」가 기본값이다** — 도구가 안 봐 준다((9)).

## 핵심 문장

- **`std::move` 는 캐스트일 뿐**이고, 실제로 옮기는 것은 **이동 생성자·이동 대입**이다.
- **훔치기는 두 절반**이다 — 자원을 가져오고 **원본을 빈 껍데기로 만든다.** 뒤쪽을 빼먹으면 이중 해제다.
- **이동한 원본도 파괴된다** — 그래서 **소멸자가 널을 견뎌야** 한다.
- ★★★ **`noexcept` 한 낱말이 `vector` 재할당을 이동과 복사로 가른다.**
- 이동 후 상태는 「**유효하되 미지정**」이고, 값이 보장되는 것은 **`unique_ptr`** 뿐이다.
- **`const` 를 `move` 하면 조용히 복사가 뽑히고**, **`return std::move(t);` 는 생략을 막는다.**
- ★★★ **이 주제의 사고는 컴파일러도 sanitizer 도 거의 못 본다** — 탐침 여섯이 **전부 0건**이고 ASan 도 **0건**이다.

## 관련 자료

- [16번](../16-copy-constructor-and-copy-assignment/) — **이 주제의 직전.** (1)의 전수 격자에서 `std::move` 를 씌운 세 자리가 **여기가 정본**이다.\
  ★ 그리고 (2)의 생략 실측이 **여기 (6)의 근거**다.
- [15번](../15-raii-resources-as-types/) — **이동 전용 타입과 빈 껍데기.** (4)(5)가 이 주제의 (2)를 미리 실측했다.
- [14번](../14-destructors-and-deterministic-destruction/) — **이동한 원본도 파괴된다**는 보장이 거기서 나온다.
- [9번](../09-rvalue-references-move-and-forward/) — **`std::move` 는 캐스트다**의 정본. (1)은 그것을 받는 쪽을 보려고 한 번 못 박은 것이다.
- [8번](../08-value-categories-lvalue-prvalue-xvalue/) — **값 범주.** (5)의 `const Tr&&` 가 왜 이동에 안 맞는지가 거기다.
- [목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/) — **0/3/5의 법칙.** (9)의 탐침 1번·2번이 그 주제의 격자에서 다시 나온다.
- 목록의 **26번 주제** — `unique_ptr`. (4)의 「널이 보장되는 유일한 것」의 전모다.
- 목록의 **41번 주제** — 순차 컨테이너. (3)의 `vector` 재할당 정책이 거기가 정본이다.
- 목록의 **52·53번 주제** — 예외 안전 보장과 `noexcept`. (3)의 「왜 던지면 안 되나」가 거기다.
- ★★★ Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **8번**([`08-ownership-and-move/`](../../../rust/syntax/08-ownership-and-move/)) — **직접 대비.**\
  **러스트는 이동이 기본이고 이동당한 원본을 컴파일러가 막는다.** (8)에서 **양쪽에 같은 코드를 던졌다.**
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **9번**([`09-copy-clone-and-drop/`](../../../rust/syntax/09-copy-clone-and-drop/)) — **`Drop` 이 빈 껍데기를 없앤다.**\
  ★ 이동한 값은 원본 자리에서 `drop` 되지 않으므로 `o.p = nullptr` 이 필요 없다.

## 용어 풀이

> **이동 생성자(move constructor)** — `T(T&&)`. **없던 객체를 만들되 자원을 훔쳐 온다.**\
> 예: (2)에서 `malloc` 이 한 번도 안 났다.

> **이동 대입 연산자(move assignment operator)** — `T& operator=(T&&)`. 이미 있는 객체가 **자기 것을 놓고 훔쳐 온다.**\
> 예: (문법)의 형태 — `free(p)` 가 먼저 돈다.

> **빈 껍데기(moved-from state)** — 이동당한 뒤의 원본. **파괴는 되지만 놓을 것이 없는 상태**다.\
> 예: (2)에서 `a.p 가 널인가 1`.

> **유효하되 미지정(valid but unspecified)** — **불변식은 지켜지되 값은 정해지지 않은** 상태.\
> 예: (4)에서 `s1.size()` 를 부르는 것은 **합법**이지만 그 값이 `0` 이라는 **보장은 없다.**

> **`noexcept`** — 「이 함수는 던지지 않는다」는 **계약**. 어기면 `std::terminate` 다.\
> 예: (3)에서 `vector` 가 그 계약을 보고 **이동을 쓸지 복사를 쓸지** 골랐다. 정본은 목록의 **53번 주제**.

> **`is_nothrow_move_constructible`** — 「이동 생성자가 `noexcept` 인가」를 묻는 트레이트.\
> 예: (3)에서 `1` 대 `0` 으로 갈렸고 그것이 재할당 로그와 정확히 일치했다.

> **이동 전용 타입(move-only type)** — 복사를 `= delete` 하고 이동만 연 타입.\
> 예: `std::unique_ptr` · (문법)의 금지 사례 `MoveOnly`.

> **작은 문자열 최적화(SSO)** — 짧은 문자열을 **힙 대신 객체 안에** 두는 구현 기법.\
> 예: (4)에서 짧은 것과 긴 것의 이동 후 `capacity` 가 **둘 다 15** 였다. **libstdc++ 의 선택**이다.

> **`-Wpessimizing-move`** — 「`std::move` 가 생략을 막고 있다」는 경고.\
> 예: (6)에서 **두 컴파일러가 다 냈다** — 이 주제에서 도구가 말해 주는 거의 유일한 자리다.

## 더 들어가면

- **`std::move_if_noexcept`** — (3)의 판정을 **직접 부르는 도구**. `vector` 가 내부에서 하는 일을 손으로 하는 셈이다.
- **`std::exchange`** — 「훔치고 비우기」 두 절반을 **한 줄로** 쓰는 관용구(`p_(std::exchange(o.p_, nullptr))`).
- **이동 대입의 자기 이동(`a = std::move(a)`)** — 표준은 대부분의 타입에 **「유효하되 미지정」만** 보장한다. 이 문서는 안 던졌다.
- **`push_back` 대 `emplace_back`** — (3)은 `emplace_back` 으로만 던졌다. 인자를 만드는 자리가 다르다.
- **`noexcept(expr)` 연산자와 조건부 `noexcept`** — 멤버의 `noexcept` 여부를 물어 전파하는 형태. 정본은 목록의 **53번 주제**.
