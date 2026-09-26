# cpp/syntax/16 — 복사 생성자와 복사 대입 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 복사 생성자](https://en.cppreference.com/w/cpp/language/copy_constructor) · [cppreference — 복사 대입 연산자](https://en.cppreference.com/w/cpp/language/copy_assignment) · [cppreference — 복사 생략](https://en.cppreference.com/w/cpp/language/copy_elision) · [GCC 13 C++ Dialect Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/C_002b_002b-Dialect-Options.html) · [AddressSanitizer](https://github.com/google/sanitizers/wiki/AddressSanitizer)
> **실행 검증** — 이 문서의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`copy01.cpp` \~ `copy09.cpp`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 배너도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
> ★★★ **ASan 을 붙인 블록은 마커를 `stderr` 로 찍었다.** sanitizer 가 `abort()` 로 죽이면\
> **버퍼에 남은 표준 출력이 통째로 사라지기 때문**이다((4)의 소스에 그렇게 적혀 있다).\
> ★★ **리포트를 자른 블록은 자르는 명령을 배너에 적었다** — 실린 것이 「생략한 일부」가 아니라 「**그 명령의 전체 출력**」이다.
> **버전** — 복사 생성자·복사 대입은 **C++98부터**. **`= delete` 는 C++11부터**,\
> **prvalue 의 복사 생략이 의무가 된 것은 C++17부터**다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.
> ★★★ **16 → 17 → 18 은 한 사슬이고 18 이 결론이다.** 여기 16 은 「**복사란 무엇을 부르는 것인가**」를 수로 고정하고,\
> **17번**이 그 위에 「훔치기」를 얹고, **18번**이 「**그래서 다섯 중 무엇을 적을 것인가**」로 닫는다.
> **경계** — 「**얕은 복사와 깊은 복사가 무엇인가**」라는 개념은 [`variables-and-memory/`](../../../../variables-and-memory/) §2 가 정본이고,\
> 여기는 **C++ 의 특수 멤버를 어떻게 구현하나**만 본다.\
> 「값 범주」는 [8번](../08-value-categories-lvalue-prvalue-xvalue/), 「`std::move`」는 [9번](../09-rvalue-references-move-and-forward/),\
> 「이동 연산」은 [목록의 **17번**](../17-move-constructor-assignment-and-moved-from-state/), 「0/3/5의 법칙」은 **18번**, 「예외 안전 보장 4단계」는 **52번 주제**가 정본이다.\
> ★ (5)의 copy-and-swap 은 **자기 대입을 푸는 도구로서만** 다룬다 — 강한 보장의 전모는 52번이다.
> **대비** — Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **9번**([`09-copy-clone-and-drop/`](../../../rust/syntax/09-copy-clone-and-drop/)) — 러스트는 **복사가 기본이 아니고** `Clone` 을 손으로 부른다.\
> C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **2번**([`02-struct-vs-class-choosing/`](../../../csharp/syntax/02-struct-vs-class-choosing/)) — 값 타입이냐 참조 타입이냐로 **복사의 뜻 자체가 갈리는** 판이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 리포트의 **PID**(`==2613344==`)·주소·스택 프레임 줄 | ★★★ **어느 특수 멤버가 몇 번 불렸나**(계수 로그) — 이 주제의 답 자체다 |
> | 두 컴파일러의 **진단 문구** · 실행 시간 | ★★★ **만들어진 객체 수**(`#N`) · **`malloc`/`free` 횟수** |
> | 객체의 주소값 · 해제된 메모리에서 읽힌 값 | ★★ **`cc exit`/`run exit`** · **경고 개수** · **에러 개수** |
> | — | ★ **진단의 `(행,열)`** · **ASan 이 붙인 사고 이름**(`heap-use-after-free`) |
>
> ★ **(4)는 해제된 메모리를 읽는 판이라 「상한 값」이 판마다 다르다.**\
> 그래서 소스가 **값을 아예 안 찍고** 「**아직 원래 값인가**」만 묻는다 — 그 답(`0`)은 15판을 돌려 전부 같았다.

## 한눈에 — 쉽게 말하면

**복사는 「서류를 한 부 더 만드는 것」이다.** 문제는 **무엇을 한 부 더 만드느냐**다.

사무실에서 서류함 열쇠를 복사한다고 하자.\
**열쇠만 복사하면** 서류함은 하나인데 열쇠가 둘이다 — 한 사람이 서류함을 치우면 다른 사람의 열쇠가 허공을 연다.\
**서류함째 복사하면** 두 사람이 각자의 서류함을 갖는다 — 아무도 남의 것을 건드리지 않는다.

C++ 의 컴파일러는 **아무 말이 없으면 열쇠만 복사한다**(멤버별 복사).\
포인터 멤버가 있으면 그것이 곧 **이중 해제**다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 열쇠만 복사 | ★★★ **컴파일러가 만든 멤버별 복사**(얕은 복사) | (3) |
| 서류함째 복사 | ★★★ **손으로 쓴 깊은 복사** | (3) |
| 서류를 **만들면서** 한 부 뜬다 | ★★★ **복사 생성자** — 새 객체가 생긴다 | (1) |
| 이미 있는 서류를 **갈아 끼운다** | ★★★ **복사 대입** — 옛것을 먼저 버려야 한다 | (1)(4) |
| 갈아 끼울 것이 **자기 자신**이면 | ★★★ **자기 대입** — 버린 것을 읽게 된다 | (4) |
| 새것을 먼저 만들고 **맞바꾼다** | ★★ **copy-and-swap** | (5) |
| 복사할 필요가 없으면 **안 뜬다** | ★★ **복사 생략** | (2) |

> **특수 멤버 함수(special member function)** — 컴파일러가 필요하면 **스스로 만들어 주는 여섯 개**.\
> 기본 생성자 · 소멸자 · 복사 생성자 · 복사 대입 · 이동 생성자 · 이동 대입.

> **얕은 복사(shallow copy)** — 멤버를 **그대로 베끼는 것**. 포인터면 **주소가 베껴진다.**\
> 예: [15번](../15-raii-resources-as-types/) (4)에서 두 객체가 같은 주소를 들고 각자 `free` 를 불러 ASan 이 `double-free` 로 죽였다.

```text
   얕은 복사                              깊은 복사

   a ──┐                                  a ──> [ 가나다 ]
       ├──> [ 가나다 ]                     
   b ──┘                                  b ──> [ 가나다 ]   <- 새로 잡은 것

   a 가 죽으면 free              a 가 죽어도 b 의 것은 그대로
   b 가 죽으면 또 free  <- 이중 해제       b 가 죽을 때 자기 것을 놓는다
```

- ★★★ **왼쪽이 [15번](../15-raii-resources-as-types/) (4)가 실측한 자리**다 — `[놓음]` 두 줄과 ASan 의 `double-free`.\
  **거기는 「복사를 막는 쪽」으로 풀었고, 여기 16 은 「복사를 제대로 만드는 쪽」으로 푼다.**

## 이 주제가 답하려는 질문

1. **어떤 문장이 복사 생성자를 부르고 어떤 문장이 복사 대입을 부르나** — **전수로 셀 수 있나**((1)).
2. **그 계수가 컴파일러의 재량으로 달라지는 자리는 어디인가**((2)).
3. **깊은 복사를 자기 대입에 안전하게 쓰려면 무엇이 필요한가** — 그리고 **안 하면 무엇이 출력되나**((3)(4)(5)).
4. **복사에서 틀린 것을 컴파일러가 말해 주나**((6)(7)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ①이다

★★★ **이 주제의 본체는 ① 호출 계수 로그다.** 「복사된다」는 말로는 **몇 번 무엇이 불렸는지 모른다** — 세면 안다.

```text
① 호출 계수 로그        특수 멤버 다섯에 로그를 심고 전수로 센다      (1)(2)(3)(5)
② 두 컴파일러 대조      생략 · 진단 문구 · 경고 개수                  (2)(6)(7)
③ ASan 리포트           자기 대입이 만든 use-after-free               (4)(7)
④ `-O2` 어셈블리        ★ 부적용 — 17번이 정본이다                    —
⑤ 경고 격자             탐침 여섯 중 몇이 답하나                      (7)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ★★★ **① 호출 계수 로그** | ★★★ **본체** — (1)의 전수 격자가 이 편의 답이다 | **쓴다** |
| ② 두 컴파일러 대조 | 생략의 의무·재량 · 값으로 받는 복사 생성자의 진단 | **쓴다** |
| ③ ASan 리포트 | 자기 대입이 **해제한 메모리를 읽는** 것 | **쓴다** |
| ④ `-O2` 어셈블리 세기 | ★ **부적용** — 복사와 이동을 **나란히 세는 것**이 뜻이 있고, 그것은 [목록의 **17번 주제**](../17-move-constructor-assignment-and-moved-from-state/)가 한다 | **안 쓴다** |
| ⑤ 경고 격자 | 탐침 여섯 중 **하나만** 답했다 | **쓴다** |

- ★★ **④를 「안 쟀다」가 아니라 「여기서는 잴 것이 없다」로 적는다.** 복사만 따로 재면 **비교 대상이 없어** 수가 뜻을 못 만든다.\
  17번이 **같은 타입의 복사판과 이동판을 한 파일에 넣어** 재면 그 수가 비로소 근거가 된다.
- ★★★ **「못 잰 것」은 또 다르다** — **런타임 할당 계수기**가 C++ 표준에 없다.\
  그래서 (3)은 **소스에 계수기를 손으로 심어** `malloc`/`free` 횟수를 셌고, (7)은 **ASan 의 누수 리포트**로 바꿔 물었다.\
  ★ 바꾼 창이 못 보는 것도 있다 — **ASan 은 힙만 본다.** 파일 핸들·락은 안 잡힌다([15번](../15-raii-resources-as-types/) (8)).

### (1) ★★★ 어느 문장이 무엇을 부르나 — 전수 격자

**언제 쓰나** — 「이 줄에서 복사가 나나?」가 궁금할 때마다. **이 절이 이 주제의 중심이다.**

특수 멤버 다섯에 **전부 로그를 심고**, 열 가지 문맥을 차례로 던진다.

```cpp
/* copy01.cpp */
// 특수 멤버 다섯에 전부 로그를 심고 — 어느 상황이 무엇을 부르나 전수로 센다
#include <cstdio>
#include <utility>

struct Loud {
    int id;
    static int n;
    Loud()                      : id(++n) { std::printf("    기본 생성자  #%d\n", id); }
    Loud(const Loud& o)         : id(++n) { std::printf("    복사 생성자  #%d <- #%d\n", id, o.id); }
    Loud(Loud&& o)     noexcept : id(++n) { std::printf("    이동 생성자  #%d <- #%d\n", id, o.id); }
    Loud& operator=(const Loud& o)         { std::printf("    복사 대입    #%d <- #%d\n", id, o.id); return *this; }
    Loud& operator=(Loud&& o)     noexcept { std::printf("    이동 대입    #%d <- #%d\n", id, o.id); return *this; }
    ~Loud() {}
};
int Loud::n = 0;

void by_value(Loud x)        { (void)x; }
void by_const_ref(const Loud& x) { (void)x; }

int main() {
    Loud a, b;                                   // #1 #2
    std::printf("(1) Loud c = b;        — 선언과 함께 = 을 썼다\n");   { Loud c = b;            (void)c; }
    std::printf("(2) Loud c(b);         — 괄호로 썼다\n");             { Loud c(b);             (void)c; }
    std::printf("(3) Loud c{b};         — 중괄호로 썼다\n");           { Loud c{b};             (void)c; }
    std::printf("(4) a = b;             — 이미 있는 것에 = 을 썼다\n"); a = b;
    std::printf("(5) Loud c = std::move(b);\n");                       { Loud c = std::move(b); (void)c; }
    std::printf("(6) a = std::move(b);\n");                            a = std::move(b);
    std::printf("(7) by_value(b);       — 값으로 받는 함수에 넘긴다\n"); by_value(b);
    std::printf("(8) by_const_ref(b);   — const 참조로 받는 함수에\n"); by_const_ref(b);
    std::printf("(9) by_value(std::move(b));\n");                      by_value(std::move(b));
    std::printf("(10) 지금까지 만들어진 객체 수 %d개\n", Loud::n);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic copy01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
    기본 생성자  #1
    기본 생성자  #2
(1) Loud c = b;        — 선언과 함께 = 을 썼다
    복사 생성자  #3 <- #2
(2) Loud c(b);         — 괄호로 썼다
    복사 생성자  #4 <- #2
(3) Loud c{b};         — 중괄호로 썼다
    복사 생성자  #5 <- #2
(4) a = b;             — 이미 있는 것에 = 을 썼다
    복사 대입    #1 <- #2
(5) Loud c = std::move(b);
    이동 생성자  #6 <- #2
(6) a = std::move(b);
    이동 대입    #1 <- #2
(7) by_value(b);       — 값으로 받는 함수에 넘긴다
    복사 생성자  #7 <- #2
(8) by_const_ref(b);   — const 참조로 받는 함수에
(9) by_value(std::move(b));
    이동 생성자  #8 <- #2
(10) 지금까지 만들어진 객체 수 8개
```

```text
   Loud c = b;     선언과 함께 =        ->  복사 생성자   (새 객체가 생긴다)
   Loud c(b);      괄호                 ->  복사 생성자
   Loud c{b};      중괄호               ->  복사 생성자
   a = b;          이미 있는 것에 =      ->  복사 대입     (옛것을 버려야 한다)
                   ^^^^^^^^^^^^^
                   ★ 같은 `=` 인데 무엇이 불리는지가 다르다
```

- ★★★ **`=` 는 두 가지 일을 한다.** **선언과 함께 쓰면 초기화**(복사 생성자)이고, **이미 있는 것에 쓰면 대입**(복사 대입)이다.\
  ★ 출력에서 `(1)`\~`(3)` 은 **새 번호**(`#3`·`#4`·`#5`)가 붙고, `(4)` 는 **`#1` 이 그대로** `#2` 를 받는다.
- ★★ **괄호·중괄호·등호 셋이 같은 것을 부른다**(`(1)`\~`(3)`). 여기서는 형태가 갈리지 않는다.
- ★★★ **값으로 받는 함수 인자는 복사다**(`(7)`). `by_value(b)` 에는 **복사라는 글자가 없다.**\
  ★ `const&` 로 받으면 **한 줄도 안 찍힌다**(`(8)`) — 아무것도 안 만들어진다.
- ★★ **`std::move` 를 씌우면 같은 자리에서 이동이 뽑힌다**(`(5)`·`(6)`·`(9)`). 정본은 [목록의 **17번 주제**](../17-move-constructor-assignment-and-moved-from-state/)다.
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic copy01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
    기본 생성자  #1
    기본 생성자  #2
(1) Loud c = b;        — 선언과 함께 = 을 썼다
    복사 생성자  #3 <- #2
(2) Loud c(b);         — 괄호로 썼다
    복사 생성자  #4 <- #2
(3) Loud c{b};         — 중괄호로 썼다
    복사 생성자  #5 <- #2
(4) a = b;             — 이미 있는 것에 = 을 썼다
    복사 대입    #1 <- #2
(5) Loud c = std::move(b);
    이동 생성자  #6 <- #2
(6) a = std::move(b);
    이동 대입    #1 <- #2
(7) by_value(b);       — 값으로 받는 함수에 넘긴다
    복사 생성자  #7 <- #2
(8) by_const_ref(b);   — const 참조로 받는 함수에
(9) by_value(std::move(b));
    이동 생성자  #8 <- #2
(10) 지금까지 만들어진 객체 수 8개
```

### (2) ★★ 생략이 계수를 바꾼다 — 의무인 것과 재량인 것

**언제 쓰나** — 「복사 생성자를 적었는데 왜 안 불리지?」에서.

**복사 생략(copy elision)** 은 컴파일러가 **복사·이동을 아예 안 하고 목적지에 바로 짓는 것**이다.\
C++17 부터 **일부는 의무**이고, 나머지는 **재량**이다. `-fno-elide-constructors` 로 재량 쪽을 끌 수 있다.

```cpp
/* copy02.cpp */
// 생략(copy elision)이 계수를 바꾸는 자리 — 의무인 것과 선택인 것을 가른다
#include <cstdio>

struct L {
    int id;
    static int n;
    L()                   : id(++n) { std::printf("    기본 생성자  #%d\n", id); }
    L(const L& o)         : id(++n) { std::printf("    복사 생성자  #%d <- #%d\n", id, o.id); }
    L(L&& o)     noexcept : id(++n) { std::printf("    이동 생성자  #%d <- #%d\n", id, o.id); }
    ~L() {}
};
int L::n = 0;

L prvalue()          { return L(); }        // 이름 없는 임시를 돌려준다
L named()            { L t; return t; }     // 이름 있는 지역을 돌려준다
void by_value(L x)   { (void)x; }

int main() {
    std::printf("(1) prvalue 를 받는다      L a = prvalue();\n");   { L a = prvalue(); (void)a; }
    std::printf("(2) 이름 있는 지역을 받는다 L b = named();\n");     { L b = named();   (void)b; }
    std::printf("(3) 임시를 값 인자로        by_value(L());\n");     by_value(L());
    std::printf("(4) 변수를 값 인자로        by_value(c);\n");       { L c; by_value(c); }
    std::printf("(5) 만들어진 객체 수 %d개\n", L::n);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic copy02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) prvalue 를 받는다      L a = prvalue();
    기본 생성자  #1
(2) 이름 있는 지역을 받는다 L b = named();
    기본 생성자  #2
(3) 임시를 값 인자로        by_value(L());
    기본 생성자  #3
(4) 변수를 값 인자로        by_value(c);
    기본 생성자  #4
    복사 생성자  #5 <- #4
(5) 만들어진 객체 수 5개
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fno-elide-constructors copy02.cpp -o ex2 && ./ex2 (cc exit=0 · run exit=0) =====
(1) prvalue 를 받는다      L a = prvalue();
    기본 생성자  #1
(2) 이름 있는 지역을 받는다 L b = named();
    기본 생성자  #2
    이동 생성자  #3 <- #2
(3) 임시를 값 인자로        by_value(L());
    기본 생성자  #4
(4) 변수를 값 인자로        by_value(c);
    기본 생성자  #5
    복사 생성자  #6 <- #5
(5) 만들어진 객체 수 6개
```

```text
                        기본            -fno-elide-constructors
   L a = prvalue();      기본 1          기본 1              <- ★ 안 바뀐다 (C++17 의무)
   L b = named();        기본 1          기본 1 + 이동 1     <- ★ 바뀐다   (NRVO 는 재량)
   by_value(L());        기본 1          기본 1              <- ★ 안 바뀐다 (C++17 의무)
   by_value(c);          기본 1 + 복사 1  기본 1 + 복사 1     <- 생략과 무관한 진짜 복사
   ─────────────────────────────────────────────────────────
   만들어진 객체 수         5개             6개
```

- ★★★ **총계가 5 대 6 으로 갈린다** — 그런데 **갈린 자리는 하나뿐**이다.
- ★★★ **`prvalue` 를 돌려받는 자리와 임시를 값 인자로 넘기는 자리는 플래그를 꺼도 안 바뀐다.**\
  C++17 이 **그 두 자리의 생략을 의무로 못 박았기 때문**이다 — 「생략」이 아니라 **애초에 임시가 안 생긴다**로 읽어야 한다.
- ★★ **이름 있는 지역을 돌려주는 자리(NRVO)만 바뀐다.** 이쪽은 **여전히 재량**이다.\
  ★ 끈 판에서 나온 것이 **이동 생성자**라는 데 주의하라 — 복사가 아니다. `return t;` 의 `t` 는 **먼저 rvalue 로 취급**된다.
- ★★ **clang 도 같은 5 대 6 이었다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -fno-elide-constructors copy02.cpp -o ex2 && ./ex2 (cc exit=0 · run exit=0) =====
(1) prvalue 를 받는다      L a = prvalue();
    기본 생성자  #1
(2) 이름 있는 지역을 받는다 L b = named();
    기본 생성자  #2
    이동 생성자  #3 <- #2
(3) 임시를 값 인자로        by_value(L());
    기본 생성자  #4
(4) 변수를 값 인자로        by_value(c);
    기본 생성자  #5
    복사 생성자  #6 <- #5
(5) 만들어진 객체 수 6개
```

- ★ **이 절이 다섯 층 중 「미명시」 칸의 실측이다** — **어디까지 생략할지는 몇 가지 중 하나**이고, 의무인 자리만 표준이 고정한다.

### (3) ★★ 얕은 복사가 만든 사고를 고치는 쪽 — 깊은 복사

**언제 쓰나** — 포인터·핸들 멤버가 있는 타입을 쓸 때마다.

★★★ **얕은 복사가 이중 해제를 만드는 것은 [15번](../15-raii-resources-as-types/) (4)가 이미 실측했다** —\
`[놓음]` 이 **두 줄**이고 ASan 이 **`double-free`** 로 죽였다. **여기서는 다시 재지 않고 고치는 쪽을 쓴다.**

```cpp
/* copy03.cpp */
// 14·15편이 실측한 「얕은 복사 -> 이중 해제」를 고치는 쪽 — 깊은 복사를 손으로 쓴다
#include <cstdio>
#include <cstdlib>
#include <cstring>

static int allocs = 0, frees = 0;

struct Buf {
    char*       p;
    std::size_t n;

    explicit Buf(const char* s) : p(nullptr), n(std::strlen(s) + 1) {
        p = static_cast<char*>(std::malloc(n)); ++allocs;
        std::memcpy(p, s, n);
    }
    ~Buf() { std::free(p); ++frees; }

    Buf(const Buf& o) : p(static_cast<char*>(std::malloc(o.n))), n(o.n) {   // 깊은 복사 — 생성
        ++allocs;
        std::memcpy(p, o.p, n);
    }
    Buf& operator=(const Buf& o) {                                          // 깊은 복사 — 대입
        if (this == &o) return *this;                                       // 자기 대입을 먼저 막는다
        char* q = static_cast<char*>(std::malloc(o.n)); ++allocs;           // 새것을 먼저 얻고
        std::memcpy(q, o.p, o.n);
        std::free(p); ++frees;                                              // 그다음에 옛것을 놓는다
        p = q; n = o.n;
        return *this;
    }
};

int main() {
    Buf a("가나다");
    Buf b = a;                                   // 복사 생성
    std::printf("(1) 복사 생성 뒤\n");
    std::printf("    두 객체가 같은 주소를 드나: %d\n", (int)(a.p == b.p));
    std::printf("    두 객체의 내용이 같나      : %d\n", (int)(std::strcmp(a.p, b.p) == 0));
    std::memcpy(b.p, "라마바", 10);
    std::printf("(2) b 만 고친 뒤\n");
    std::printf("    a = \"%s\"  b = \"%s\"\n", a.p, b.p);
    Buf c("짧다");
    c = a;                                       // 복사 대입
    std::printf("(3) 복사 대입 뒤  c = \"%s\"  (a 와 같은 주소인가: %d)\n", c.p, (int)(c.p == a.p));
    std::printf("(4) 지금까지 malloc %d회 · free %d회 (블록을 나가면 free 가 3회 더)\n", allocs, frees);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic copy03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 복사 생성 뒤
    두 객체가 같은 주소를 드나: 0
    두 객체의 내용이 같나      : 1
(2) b 만 고친 뒤
    a = "가나다"  b = "라마바"
(3) 복사 대입 뒤  c = "가나다"  (a 와 같은 주소인가: 0)
(4) 지금까지 malloc 4회 · free 1회 (블록을 나가면 free 가 3회 더)
```

```text
   복사 대입의 순서 — 잡고 나서 놓는다

   ① if (this == &o) return *this;      자기 대입을 먼저 막는다
   ② q = malloc(o.n); memcpy(q, ...)    ★ 새것을 먼저 얻는다 (여기서 던져도 옛것이 멀쩡하다)
   ③ free(p)                            그다음에 옛것을 놓는다
   ④ p = q; n = o.n

   뒤집으면 — ③ -> ② 순서가 되면 (4)의 자기 대입 사고가 열린다
```

- ★★★ **깊은 복사의 증거는 「주소가 다르고 내용이 같다」 두 줄이다**(`0` 과 `1`).\
  ★ 한쪽만 고쳐도 다른 쪽이 안 바뀐다 — **독립이라는 뜻**이다.
- ★★ **복사 대입은 세 가지 일을 한다** — ① 자기 대입을 막고 ② 새것을 잡고 ③ **그다음에** 옛것을 놓는다.\
  ★ **순서가 규칙이다.** ②와 ③을 뒤집으면 (4)가 된다.
- ★★ **`malloc` 4회 · `free` 1회**다. 복사 생성 1 · 대입에서 1 · 원래 둘 = 4 이고, 대입이 놓은 것이 1 이다.\
  ★ 나머지 3회의 `free` 는 **블록을 나가면서** 돈다 — 소멸자가 센다.

### (4) ★★★ 자기 대입이 naive 구현을 망가뜨린다

**언제 쓰나** — 복사 대입을 손으로 쓸 때마다. **이 절이 (3)의 짝이다.**

「놓고 나서 잡는」 순서로 쓰면 **`a = a;` 한 줄에 무너진다.**

```cpp
/* copy04.cpp */
// 자기 대입을 안 막은 naive 구현 — 마커를 표준 오류로 찍는다(ASan 이 죽여도 남게)
// ★ 상한 내용은 판마다 다르므로 값 자체를 찍지 않는다. 「상했나」만 묻는다.
#include <cstdio>
#include <cstdlib>
#include <cstring>

struct Naive {
    char*       p;
    std::size_t n;
    explicit Naive(const char* s) : p(nullptr), n(std::strlen(s) + 1) {
        p = static_cast<char*>(std::malloc(n));
        std::memcpy(p, s, n);
    }
    ~Naive() { std::free(p); }
    Naive(const Naive& o) : p(static_cast<char*>(std::malloc(o.n))), n(o.n) { std::memcpy(p, o.p, n); }
    Naive& operator=(const Naive& o) {          // 놓고 나서 잡는다 — 자기 대입을 안 막았다
        std::free(p);                           // ① 내 것을 먼저 놓는다
        n = std::strlen(o.p) + 1;               // ② 그런데 o 가 나 자신이면 방금 놓은 것을 읽는다
        p = static_cast<char*>(std::malloc(n));
        std::memcpy(p, o.p, n);
        return *this;
    }
};

int main() {
    std::fprintf(stderr, "(1) 서로 다른 둘을 대입한다  a = b;\n");
    Naive a("가나다"), b("라마바");
    a = b;
    std::fprintf(stderr, "    a 가 \"라마바\" 인가: %d\n", (int)(std::strcmp(a.p, "라마바") == 0));
    std::fprintf(stderr, "(2) 자기 자신을 대입한다  a = a;\n");
    a = a;
    std::fprintf(stderr, "    a 가 아직 \"라마바\" 인가: %d\n", (int)(std::strcmp(a.p, "라마바") == 0));
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic copy04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 서로 다른 둘을 대입한다  a = b;
    a 가 "라마바" 인가: 1
(2) 자기 자신을 대입한다  a = a;
    a 가 아직 "라마바" 인가: 0
```

```text
   a = a;   에서 벌어지는 일

   ① free(p)            내 버퍼를 놓는다
   ② strlen(o.p)        그런데 o 는 나 자신이다 — 방금 놓은 것을 읽는다  <- use-after-free
   ③ malloc(n)          n 은 쓰레기에서 나온 길이다
   ④ memcpy(p, o.p, n)  또 놓은 것에서 복사한다
```

- ★★★ **터지지 않는다.** `cc exit=0`·`run exit=0` 이고 **경고도 0건**이다. **값만 조용히 상한다.**
- ★★★ **ASan 에게 물으면 이름이 붙는다** — `heap-use-after-free`.

```text
===== g++ -std=c++20 -Wall -Wextra -fsanitize=address -g -ffile-prefix-map="$PWD"=. copy04.cpp -o exa && ./exa | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=1) =====
(1) 서로 다른 둘을 대입한다  a = b;
    a 가 "라마바" 인가: 1
(2) 자기 자신을 대입한다  a = a;
=================================================================
==2613344==ERROR: AddressSanitizer: heap-use-after-free on address 0x502000000050 at pc 0x77c20907d96f bp 0x7ffc7a5d5080 sp 0x7ffc7a5d4828
READ of size 2 at 0x502000000050 thread T0
    #0 0x77c20907d96e in strlen ../../../../src/libsanitizer/sanitizer_common/sanitizer_common_interceptors.inc:391
    #1 0x618e397d184b in Naive::operator=(Naive const&) copy04.cpp:18
    #2 0x618e397d1543 in main copy04.cpp:31

0x502000000050 is located 0 bytes inside of 10-byte region [0x502000000050,0x50200000005a)
freed by thread T0 here:
    #0 0x77c2090fc4d8 in free ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:52
    #1 0x618e397d181b in Naive::operator=(Naive const&) copy04.cpp:17
    #2 0x618e397d1543 in main copy04.cpp:31

previously allocated by thread T0 here:
    #0 0x77c2090fd9c7 in malloc ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:69
    #1 0x618e397d188c in Naive::operator=(Naive const&) copy04.cpp:19
    #2 0x618e397d1468 in main copy04.cpp:28

SUMMARY: AddressSanitizer: heap-use-after-free ../../../../src/libsanitizer/sanitizer_common/sanitizer_common_interceptors.inc:391 in strlen
```

- ★★★ **리포트가 세 지점을 가리킨다** — `READ` 가 **18번 줄**(`strlen`), `freed by` 가 **17번 줄**(`free`), `previously allocated` 가 **19번 줄**.\
  ★ **줄 번호가 이 사고의 전부**다. 「놓은 줄」과 「읽은 줄」이 **같은 함수 안에 한 줄 간격으로** 있다.
- ★★ **`run exit=1`** 이다 — ASan 이 `abort()` 했다. ASan 을 안 붙인 판은 `run exit=0` 이었다.
- ★★ **마커를 `stderr` 로 찍은 이유가 이 블록에 보인다.** `(1)`·`(2)` 두 줄이 리포트 **앞에 남아 있다**.\
  표준 출력으로 찍었으면 `abort()` 가 버퍼째 지워 **한 줄도 안 남았을 것**이다(규칙 19-A).

### (5) ★★★ copy-and-swap — 자기 대입과 예외 안전을 한 구현이 푼다

**언제 쓰나** — 복사 대입을 쓰기로 했을 때의 **기본형**.

(3)은 `if (this == &o) return *this;` **한 줄로** 자기 대입을 막았다.\
copy-and-swap 은 **그 줄조차 없이** 푼다 — 그리고 **덤으로 예외 안전까지** 얻는다.

```cpp
/* copy05.cpp */
// copy-and-swap — 자기 대입과 예외 안전을 한 구현이 동시에 푼다
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <new>
#include <utility>

static bool armed = false;                       // 다음 할당을 실패시킨다
static void* xalloc(std::size_t n) {
    if (armed) { armed = false; throw std::bad_alloc(); }
    return std::malloc(n);
}

struct Safe {
    char*       p;
    std::size_t n;
    explicit Safe(const char* s) : p(nullptr), n(std::strlen(s) + 1) {
        p = static_cast<char*>(xalloc(n));
        std::memcpy(p, s, n);
    }
    ~Safe() { std::free(p); }
    Safe(const Safe& o) : p(static_cast<char*>(xalloc(o.n))), n(o.n) { std::memcpy(p, o.p, n); }
    friend void swap(Safe& x, Safe& y) noexcept { std::swap(x.p, y.p); std::swap(x.n, y.n); }
    Safe& operator=(Safe o) {                    // ★ 값으로 받는다 — 복사는 여기서 이미 끝났다
        swap(*this, o);                          // ★ 맞바꾸기만 한다 (noexcept)
        return *this;                            // ★ o 가 옛것을 들고 나가 파괴된다
    }
};

struct Naive {                                   // 대조군 — 놓고 나서 잡는다
    char*       p;
    std::size_t n;
    explicit Naive(const char* s) : p(nullptr), n(std::strlen(s) + 1) {
        p = static_cast<char*>(xalloc(n));
        std::memcpy(p, s, n);
    }
    ~Naive() { std::free(p); }
    Naive(const Naive& o) : p(static_cast<char*>(xalloc(o.n))), n(o.n) { std::memcpy(p, o.p, n); }
    Naive& operator=(const Naive& o) {
        if (this == &o) return *this;
        std::free(p);                            // ① 먼저 놓고
        p = static_cast<char*>(xalloc(o.n));     // ② 여기서 던지면 p 는 해제된 주소 그대로다
        n = o.n;
        std::memcpy(p, o.p, n);
        return *this;
    }
};

int main() {
    std::printf("(1) copy-and-swap 에 자기 대입\n");
    Safe a("가나다");
    a = a;
    std::printf("    a = \"%s\"   (자기 대입 검사 한 줄도 없다)\n", a.p);

    std::printf("(2) 대입 도중 할당이 실패하면 — copy-and-swap\n");
    Safe s1("원본은 살아남나"), s2("새 값");
    armed = true;
    try { s1 = s2; } catch (const std::bad_alloc&) { std::printf("    [catch] bad_alloc\n"); }
    std::printf("    s1 = \"%s\"  ★ 원본 그대로다\n", s1.p);

    std::printf("(3) 같은 일을 naive 구현에 — 포인터가 어떻게 되나\n");
    Naive n1("원본은 살아남나"), n2("새 값");
    char* before = n1.p;
    armed = true;
    try { n1 = n2; } catch (const std::bad_alloc&) { std::printf("    [catch] bad_alloc\n"); }
    std::printf("    n1.p 가 대입 전과 같은 주소인가: %d  ★ 그 주소는 이미 free 된 것이다\n",
                (int)(n1.p == before));
    n1.p = nullptr;                              // 소멸자가 이중 해제하지 않도록 치운다
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic copy05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) copy-and-swap 에 자기 대입
    a = "가나다"   (자기 대입 검사 한 줄도 없다)
(2) 대입 도중 할당이 실패하면 — copy-and-swap
    [catch] bad_alloc
    s1 = "원본은 살아남나"  ★ 원본 그대로다
(3) 같은 일을 naive 구현에 — 포인터가 어떻게 되나
    [catch] bad_alloc
    n1.p 가 대입 전과 같은 주소인가: 1  ★ 그 주소는 이미 free 된 것이다
```

```text
   Safe& operator=(Safe o)      <- ★ 값으로 받는다. 복사는 여기서 이미 끝났다
   {
       swap(*this, o);          <- ★ 맞바꾸기만 한다 (noexcept — 던질 것이 없다)
       return *this;            <- ★ o 가 옛것을 들고 나가 파괴된다
   }

   a = a;   ->  o 는 a 의 복사본이다. 맞바꿔도 a 는 제 값을 그대로 갖는다.
   던지면?  ->  던지는 자리는 「값으로 받는」 순간뿐이다. 그때 *this 는 아직 안 건드렸다.
```

- ★★★ **자기 대입 검사 한 줄이 없는데 `a = a;` 가 안전하다.** 값으로 받는 순간 **이미 딴 물건**이기 때문이다.
- ★★★ **할당이 실패해도 원본이 그대로다** — `s1` 이 `"원본은 살아남나"` 로 남았다. 이것이 **강한 보장**이다.
- ★★★ **같은 실패를 naive 구현에 주면 포인터가 해제된 주소를 든 채 남는다** — `n1.p 가 대입 전과 같은 주소인가: 1`.\
  ★ 그 뒤 소멸자가 돌면 **이중 해제**다. 그래서 예제가 `n1.p = nullptr;` 로 치웠다.
- ★★ **대가가 있다** — 자기 대입에서도 **복사가 한 번 일어난다**(`(1)` 에서 `Safe` 하나가 더 만들어졌다).\
  ★ 「같은 것을 대입하는 일이 잦다」면 (3)의 검사 한 줄이 싸다. **둘 다 맞고 상황이 고른다.**
- ★ **강한 보장의 전모와 4단계 분류는 목록의 52번 주제**가 정본이다. 여기는 **자기 대입을 푸는 도구로서만** 봤다.

### (6) ★ `const T&` 가 아니라 `T` 로 받으면 — 컴파일러가 먼저 막는다

**언제 쓰나** — 복사 생성자의 **인자 형태**를 고를 때.

「값으로 받는 복사 생성자」는 **자기를 부르려면 먼저 복사해야 하고, 그 복사가 또 자기를 부른다.**\
무한 재귀가 될 텐데 — **실제로는 컴파일이 안 된다.**

```cpp
/* copy06.cpp */
// 복사 생성자를 const T& 가 아니라 T 로 받으면 — 컴파일러가 먼저 막는다
struct C {
    int x;
    C() : x(0) {}
    C(C o) { x = o.x; }                 // 값으로 받는 복사 생성자
};
struct A {
    int x;
    A() : x(0) {}
    A(const A&) = default;
    A& operator=(A o) { x = o.x; return *this; }   // 값으로 받는 복사 대입은 합법이다
};
int main() { A a, b; a = b; (void)a; }
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 copy06.cpp -o ex (cc exit=1) =====
copy06.cpp:5:5: error: invalid constructor; you probably meant ‘C (const C&)’
    5 |     C(C o) { x = o.x; }                 // 값으로 받는 복사 생성자
      |     ^
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 copy06.cpp -o ex (cc exit=1) =====
copy06.cpp:5:9: error: copy constructor must pass its first argument by reference
    5 |     C(C o) { x = o.x; }                 // 값으로 받는 복사 생성자
      |         ^
      |         const &
1 error generated.
```

- ★★★ **실행이 아니라 컴파일에서 걸린다.** 스택 오버플로를 볼 기회가 없다 — 표준이 **그 선언 자체를 금지**한다.
- ★★ **두 컴파일러가 서로 다른 문구로 같은 것을 말한다** — g++ 는 `invalid constructor; you probably meant ‘C (const C&)’`,\
  clang 은 `copy constructor must pass its first argument by reference` 에 **고칠 문자열까지** 붙여 준다.
- ★★★ **복사 대입은 값으로 받아도 된다**(`A& operator=(A o)`) — 그것이 (5)의 copy-and-swap 이다.\
  ★ **대입은 이미 있는 객체에 하는 것**이라 「자기를 만들려고 자기를 부르는」 고리가 안 생긴다.
- ★ **`const` 를 붙이는 이유는 따로 있다** — 안 붙이면 **const 객체와 임시를 복사할 수 없다**((문법)의 금지 사례 3번).

### (7) 경고를 누가 보나 — 탐침 여섯

「경고가 안 났다」를 산문으로 적으면 **안 물어본 것과 물었는데 조용한 것이 구분되지 않는다.**\
그래서 **복사에서 틀리는 자리 여섯 개**를 한 파일에 심고 두 컴파일러에 똑같이 물었다.

```cpp
/* copy07.cpp */
// 복사에서 틀리는 자리 여섯을 심었다 — 컴파일러가 몇 군데에서 말하는지 센다
#include <cstdio>
#include <cstdlib>
#include <cstring>

struct P1 {                                   // 1. 소멸자만 쓰고 복사를 안 막았다 (얕은 복사)
    char* p;
    P1() : p(static_cast<char*>(std::malloc(8))) {}
    ~P1() { std::free(p); }
};
struct P2 {                                   // 2. 복사 생성자만 쓰고 복사 대입은 안 썼다
    char* p;
    P2() : p(static_cast<char*>(std::malloc(8))) {}
    P2(const P2& o) : p(static_cast<char*>(std::malloc(8))) { (void)o; }
};
struct P3 {                                   // 3. 복사 생성자가 멤버 하나를 빠뜨렸다
    int a, b;
    P3() : a(0), b(0) {}
    P3(const P3& o) : a(o.a) {}
};
struct P4 {                                   // 4. 복사 대입이 *this 를 안 돌려준다
    int a;
    P4() : a(0) {}
    void operator=(const P4& o) { a = o.a; }
};
struct P5 {                                   // 5. 자기 대입을 안 막은 대입 연산자
    char* p; std::size_t n;
    P5() : p(static_cast<char*>(std::malloc(8))), n(8) {}
    ~P5() { std::free(p); }
    P5(const P5& o) : p(static_cast<char*>(std::malloc(o.n))), n(o.n) { std::memcpy(p, o.p, n); }
    P5& operator=(const P5& o) {
        std::free(p);
        n = o.n;
        p = static_cast<char*>(std::malloc(n));
        std::memcpy(p, o.p, n);
        return *this;
    }
};
struct P6 {                                   // 6. 복사 대입이 멤버를 하나도 안 옮긴다
    int a;
    P6() : a(0) {}
    P6& operator=(const P6&) { return *this; }
};

int main() {
    P1 a; P1 b(a); (void)b;                   // 얕은 복사 — 소멸자 둘이 같은 포인터를 놓는다
    P2 c; P2 d(c); c = d;                     // 암묵 복사 대입을 쓴다
    P3 e; P3 f(e); (void)f;
    P4 g, h; g = h;
    P5 i, j; i = j;
    P6 k, l; k = l;
    std::printf("여섯 자리 전부 컴파일됐다\n");
    a.p = nullptr; b.p = nullptr;             // 이중 해제를 피해 치운다
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic copy07.cpp -o ex (cc exit=0) =====
copy07.cpp: In function ‘int main()’:
copy07.cpp:47:24: warning: implicitly-declared ‘constexpr P2& P2::operator=(const P2&)’ is deprecated [-Wdeprecated-copy]
   47 |     P2 c; P2 d(c); c = d;                     // 암묵 복사 대입을 쓴다
      |                        ^
copy07.cpp:14:5: note: because ‘P2’ has user-provided ‘P2::P2(const P2&)’
   14 |     P2(const P2& o) : p(static_cast<char*>(std::malloc(8))) { (void)o; }
      |     ^~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic copy07.cpp -o ex (cc exit=0) =====
copy07.cpp:14:5: warning: definition of implicit copy assignment operator for 'P2' is deprecated because it has a user-provided copy constructor [-Wdeprecated-copy-with-user-provided-copy]
   14 |     P2(const P2& o) : p(static_cast<char*>(std::malloc(8))) { (void)o; }
      |     ^
copy07.cpp:47:22: note: in implicit copy assignment operator for 'P2' first required here
   47 |     P2 c; P2 d(c); c = d;                     // 암묵 복사 대입을 쓴다
      |                      ^
1 warning generated.
```

```text
===== echo "copy07 탐침 여섯  g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic copy07.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
copy07 탐침 여섯  g++ 경고 1
===== echo "copy07 탐침 여섯  clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic copy07.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
copy07 탐침 여섯  clang 경고 1
===== echo "copy07 을 ASan 으로 돌리면: $(g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. copy07.cpp -o exa 2>/dev/null; ./exa >/dev/null 2>asan16.txt; grep -cE 'ERROR: (Address|Leak)Sanitizer' asan16.txt) 건" (exit=0) =====
copy07 을 ASan 으로 돌리면: 1 건
===== echo "그 리포트의 요약: $(grep -hE '^SUMMARY' asan16.txt | head -1 | grep . || echo 리포트 없음)" (exit=0) =====
그 리포트의 요약: SUMMARY: AddressSanitizer: 24 byte(s) leaked in 3 allocation(s).
```

```text
   무엇이 이 여섯을 보나

   컴파일러  ──> 「형태가 틀린 것」만 본다        탐침 2번 하나
   ASan      ──> 「그 경로를 실제로 밟은 것」만   탐침 1·3번의 누수 (24바이트)
   계수 로그 ──> 「몇 번 불렸나」                (1)~(3) 이 그 창이다
   ─────────────────────────────────────────────
   아무도 안 보는 것: 자기 대입 · 멤버 누락 · 아무 일도 안 하는 대입
```

| 심은 것 | g++ | clang | 실제로는 |
|---|---|---|---|
| 1. 소멸자만 쓰고 복사를 안 막았다 | 0 | 0 | ★★★ **얕은 복사 → 이중 해제**([15번](../15-raii-resources-as-types/) (4)) |
| 2. 복사 생성자만 쓰고 복사 대입은 안 썼다 | ★ **1** | ★ **1** | ★★ **암묵 복사 대입이 deprecated** — 유일하게 답한 자리 |
| 3. 복사 생성자가 멤버 하나를 빠뜨렸다 | 0 | 0 | ★★ `b` 가 **초기화되지 않은 채** 복사된다 |
| 4. 복사 대입이 `*this` 를 안 돌려준다 | 0 | 0 | ★ `a = b = c;` 가 컴파일 안 된다(쓰기 전엔 모른다) |
| 5. 자기 대입을 안 막은 대입 연산자 | 0 | 0 | ★★★ **(4)의 use-after-free** |
| 6. 복사 대입이 멤버를 하나도 안 옮긴다 | 0 | 0 | ★★ **대입이 아무 일도 안 한다** |

- ★★★ **탐침 여섯 중 답한 것 1, 침묵한 것 5다.** **`cc exit=0`** 이고 프로그램은 끝까지 돈다.
- ★★★ **답한 그 하나가 정확히 18번 주제의 예고다** — 「복사 생성자를 썼으면 **복사 대입도 결정하라**」.\
  ★ 두 컴파일러가 **같은 자리에서만** 말했다. 경고 이름은 다르다(`-Wdeprecated-copy` 대 `-Wdeprecated-copy-with-user-provided-copy`).
- ★★★ **ASan 은 컴파일러가 침묵한 자리에서 말한다** — `24 byte(s) leaked in 3 allocation(s)`.\
  ★ 그런데 **그 셋은 「복사가 틀렸다」가 아니라 「소멸자가 없다」는 사고**다. **ASan 도 복사의 논리는 못 본다.**
- ★★ **5번(자기 대입)은 컴파일러도 ASan 도 이 파일에서는 못 잡았다** — `i = j` 는 **서로 다른 객체**라 사고가 안 난다.\
  ★ **(4)처럼 `a = a` 를 실제로 써야** ASan 이 말한다. **「탐침을 심었다」와 「그 경로를 밟았다」는 다른 것**이다.

## 문법 — 형태와 규칙

### 형태

```cpp
/* copy08.cpp */
// 복사 한 벌의 형태 — 3의 법칙을 지킨 타입. 이 파일은 그대로 컴파일된다
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <new>
#include <utility>

class Text {
public:
    explicit Text(const char* s) : n_(std::strlen(s) + 1), p_(alloc(n_)) {   // ① 잡는다
        std::memcpy(p_, s, n_);
    }
    ~Text() { std::free(p_); }                                               // ② 놓는다

    Text(const Text& o) : n_(o.n_), p_(alloc(o.n_)) {                        // ③ 깊은 복사 — 생성
        std::memcpy(p_, o.p_, n_);
    }
    Text& operator=(Text o) {                                                // ④ 값으로 받는다 = copy-and-swap
        swap(*this, o);
        return *this;
    }
    friend void swap(Text& a, Text& b) noexcept {                            // ⑤ 맞바꾸기는 noexcept
        std::swap(a.p_, b.p_);
        std::swap(a.n_, b.n_);
    }
    const char* c_str() const noexcept { return p_; }

private:
    static char* alloc(std::size_t n) {
        char* q = static_cast<char*>(std::malloc(n));
        if (!q) throw std::bad_alloc();
        return q;
    }
    std::size_t n_;                       // ★ 선언 순서가 초기화 순서다 — n_ 이 먼저다
    char*       p_;
};

int main() {
    Text a("가나다");
    Text b = a;                           // 복사 생성
    Text c("짧다");
    c = a;                                // 복사 대입
    c = c;                                // 자기 대입 — 검사 한 줄 없이 안전하다
    std::printf("a=\"%s\" b=\"%s\" c=\"%s\"\n", a.c_str(), b.c_str(), c.c_str());
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic copy08.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a="가나다" b="가나다" c="가나다"
```

### 규칙

- **복사 생성자는 `T(const T&)`** 이고 **복사 대입은 `T& operator=(const T&)`** 다.\
  ★ **복사 생성자를 `T(T)` 로 쓸 수 없다**((6)) — 복사 대입은 `T& operator=(T)` 로 써도 된다.
- **복사 대입은 `*this` 를 참조로 돌려준다.** 안 돌려주면 `a = b = c;` 가 막힌다.
- **손으로 쓸 때는 세 가지를 순서대로** — ① 자기 대입을 막고 ② **새것을 먼저 잡고** ③ 그다음에 옛것을 놓는다.
- ★★★ **copy-and-swap 은 그 셋을 한 형태로 푼다** — 값으로 받고, `swap` 하고, 돌려준다((5)).
- **`swap` 은 `noexcept` 여야** 그 형태가 성립한다. 멤버를 맞바꾸기만 하므로 던질 것이 없다.
- **멤버 초기화 순서는 선언 순서다** — 형태 예제가 `n_` 을 먼저 선언한 것이 그 때문이다([13번](../13-constructors-member-init-list-and-delegating/)).
- **복사를 쓸 이유가 없으면 쓰지 않는다** — 자원을 `unique_ptr`·`vector`·`string` 에 맡기면 **한 줄도 안 쓴다**([목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/)).

### 금지 사례 — 세 줄이 각각 막힌다

```cpp
/* copy09.cpp */
// 복사가 컴파일에서 막히는 세 줄 — 이유가 각각 다르다
struct ConstMember { const int k = 1; int v = 0; };                  // const 멤버가 있다
struct RefMember   { int& r; explicit RefMember(int& x) : r(x) {} }; // 참조 멤버가 있다
struct NonConstCopy { int v; NonConstCopy() : v(0) {} NonConstCopy(NonConstCopy&) : v(0) {} };

int main() {
    ConstMember a, b;
    a = b;                          // 1. const 멤버가 있어 복사 대입이 지워졌다

    int x = 1, y = 2;
    RefMember c(x), d(y);
    c = d;                          // 2. 참조 멤버가 있어 복사 대입이 지워졌다

    const NonConstCopy e;
    NonConstCopy f(e);              // 3. 복사 생성자가 const 를 안 받는다
    (void)f;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 copy09.cpp -o ex (cc exit=1) =====
copy09.cpp: In function ‘int main()’:
copy09.cpp:8:9: error: use of deleted function ‘ConstMember& ConstMember::operator=(const ConstMember&)’
    8 |     a = b;                          // 1. const 멤버가 있어 복사 대입이 지워졌다
      |         ^
copy09.cpp:2:8: note: ‘ConstMember& ConstMember::operator=(const ConstMember&)’ is implicitly deleted because the default definition would be ill-formed:
    2 | struct ConstMember { const int k = 1; int v = 0; };                  // const 멤버가 있다
      |        ^~~~~~~~~~~
copy09.cpp:2:8: error: non-static const member ‘const int ConstMember::k’, cannot use default assignment operator
copy09.cpp:12:9: error: use of deleted function ‘RefMember& RefMember::operator=(const RefMember&)’
   12 |     c = d;                          // 2. 참조 멤버가 있어 복사 대입이 지워졌다
      |         ^
copy09.cpp:3:8: note: ‘RefMember& RefMember::operator=(const RefMember&)’ is implicitly deleted because the default definition would be ill-formed:
    3 | struct RefMember   { int& r; explicit RefMember(int& x) : r(x) {} }; // 참조 멤버가 있다
      |        ^~~~~~~~~
copy09.cpp:3:8: error: non-static reference member ‘int& RefMember::r’, cannot use default assignment operator
copy09.cpp:15:20: error: binding reference of type ‘NonConstCopy&’ to ‘const NonConstCopy’ discards qualifiers
   15 |     NonConstCopy f(e);              // 3. 복사 생성자가 const 를 안 받는다
      |                    ^
copy09.cpp:4:68: note:   initializing argument 1 of ‘NonConstCopy::NonConstCopy(NonConstCopy&)’
    4 | struct NonConstCopy { int v; NonConstCopy() : v(0) {} NonConstCopy(NonConstCopy&) : v(0) {} };
      |                                                                    ^~~~~~~~~~~~~
```

- ★★★ **세 에러의 이유가 전부 다르다.**
  - **`const` 멤버** — 기본 복사 대입이 **ill-formed 라 암묵적으로 지워진다.** 「대입할 수 없는 멤버」가 있기 때문이다.
  - **참조 멤버** — 같은 이유다. **참조는 재결합되지 않는다**([7번](../07-references-vs-pointers/)).
  - **`const` 를 안 받는 복사 생성자** — `const` 객체를 복사할 수 없다. **그래서 `const T&` 가 기본형**이다.
- ★★ **앞의 둘은 「복사 생성」은 그대로 된다** — 지워지는 것은 **대입 쪽뿐**이다.\
  ★ 이 비대칭이 [목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/)의 격자에서 다시 나온다.

## 어디서 틀리나

### 1. ★★★ 「복사 생성자를 적었으니 복사는 안전하다」

**복사 대입은 따로다.** 탐침 2번이 그 자리이고, **두 컴파일러가 유일하게 말해 준 자리**이기도 하다((7)).\
하나를 쓰면 **나머지도 따져야 한다** — 그것이 [목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/)다.

### 2. ★★★ 「자기 대입은 이상한 코드라 안 일어난다」

`v[i] = v[j]` 에서 `i == j` 이면 일어난다. **이름이 다르다고 딴 물건이 아니다.**\
(4)가 보인 것은 **경고 0건 · `run exit=0` · 값만 조용히 상함**이다.

### 3. ★★★ 「복사 생성자를 적었으면 불리겠지」

(2)의 `prvalue` 판에서는 **한 번도 안 불린다.** C++17 부터 **그 자리의 생략은 의무**다.\
★ 「복사 생성자에 로그를 심어 호출 횟수로 무언가를 세는 코드」는 **그래서 틀린다.**

### 4. ★★ 「`=` 는 대입이다」

**선언과 함께 쓴 `=` 는 초기화**이고 복사 **생성자**를 부른다((1)의 `(1)`).\
★ 「기본 생성자 뒤에 대입이 한 번 더」라고 읽으면 계수가 안 맞는다.

### 5. ★★ 「값으로 넘기는 건 복사가 아니다」

(1)의 `(7)` 이 그 자리다 — `by_value(b)` 한 줄에 복사 생성자가 돈다.\
★ **복사를 `= delete` 하면 그때 드러난다**([15번](../15-raii-resources-as-types/)의 금지 사례 세 번째).

### 6. ★★ 「깊은 복사는 `new` 를 한 번 더 하는 것」

그것만으로는 **자기 대입에서 무너진다**((4)). **순서가 규칙**이다 — 잡고 나서 놓는다.

### 7. ★ 「컴파일러가 경고해 주겠지」

**탐침 여섯 중 하나만 답했다**((7)). 나머지 다섯은 **`cc exit=0` 에 경고 0건**이다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「미명시」 칸이 특히 크다** — (2)의 생략이 통째로 거기 있다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **선언과 함께 쓴 `=` 는 복사 생성자, 이미 있는 것에 쓴 `=` 는 복사 대입**((1)) · **값 인자는 복사**((1)) · ★★★ **`T(T)` 는 ill-formed**((6)) · **`const`·참조 멤버가 있으면 복사 대입이 지워지는 것**((문법)) · **컴파일러가 만드는 복사는 멤버별 복사**((3)) | 계수 로그 · 진단 전문 + `cc exit` | ★★★ 「**이 복사가 깊은가 얕은가**」 — 주소를 찍기 전에는 안 보인다((3)) |
| **조건부 표준** | 특정 조건에서만 보장 | ★★★ **prvalue 의 생략은 C++17부터 의무**((2)) · **`= delete` 는 C++11부터** · **`-Wdeprecated-copy` 가 가리키는 「deprecated」는 C++11부터** | `-std=c++20` 으로만 돌렸다 | ★ **C++14 이하 판으로는 안 돌려 봤다**(거기서는 (2)의 `(1)`·`(3)` 도 갈릴 수 있다) |
| **구현 정의** | 문서화 의무가 있다 | ★ **진단 문구와 경고 이름**(`-Wdeprecated-copy` 대 `-Wdeprecated-copy-with-user-provided-copy`) · **ASan 이 사고에 붙이는 이름** | 두 컴파일러 전문 | ★★ **다른 컴파일러는 다른 이름을 쓴다** |
| **미명시** | 몇 가지 중 하나 | ★★★ **NRVO 를 할지 말지**((2)의 `(2)`) — 표준은 **허용할 뿐 강제하지 않는다** | `-fno-elide-constructors` 대조 | ★★★ **최적화 수준마다 또 달라질 수 있다** — 이 문서는 기본값만 봤다 |
| **UB** | 아무 일이나 | ★★★ **둘이다** — ① **자기 대입 뒤의 use-after-free**((4)) ② **얕은 복사 뒤의 이중 해제**([15번](../15-raii-resources-as-types/) (4)) | ASan 리포트 이름 · 줄 번호 | ★★★ **둘 다 컴파일 시간에는 아무 흔적도 없다 — 설계로만 막는다** |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | ASan | 계수 로그 |
|---|---|---|---|---|---|
| `T(T)` 로 쓴 복사 생성자 | 표준 | **error** | **error** | — | — |
| `const`·참조 멤버의 복사 대입 | 표준 | **error** | **error** | — | — |
| 복사 생성자만 쓰고 복사 대입을 안 씀 | 조건부 | ★ **warning 1** | ★ **warning 1** | — | — |
| ★★★ **자기 대입을 안 막은 대입** | UB | ★★★ **0건** | ★★★ **0건** | ★★★ **그 경로를 밟아야만 잡는다**((4)) | ★ 값이 상한다 |
| ★★★ **얕은 복사(소멸자만 씀)** | UB | ★★★ **0건** | ★★★ **0건** | ★ **`double-free`**([15번](../15-raii-resources-as-types/)) | ★ 놓음 2줄 |
| 복사 생성자가 멤버를 빠뜨림 | — | ★★★ **0건** | ★★★ **0건** | ★★★ **못 본다** | ★★★ **값을 찍어야만** |
| 생략이 일어났는지 | 미명시 | 0건 | 0건 | — | ★★ **계수 로그만**((2)) |

- ★★ **이 표의 결론 세 줄**
  - **복사의 「형태」가 틀린 것은 전부 컴파일에서 걸린다** — 첫 두 줄.
  - **복사의 「논리」가 틀린 것은 하나도 안 걸린다** — 자기 대입·멤버 누락·아무 일도 안 하는 대입.
  - ★★★ **ASan 도 「그 경로를 밟아야」 말한다.** 탐침 파일에 심어만 두면 **침묵한다**((7)).

### ★ 진단이 0줄인 것도 블록으로 받았다

(7)이 그 자리다. **탐침 여섯 중 답한 것 1, 침묵한 것 5**이고 **`cc exit=0`** 이다.\
그 침묵을 메우는 것이 **(4)의 ASan 리포트**와 **(1)\~(3)의 계수 로그**다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 자원을 직접 들지 않는 타입 | ★★★ **아무것도 안 쓴다** | 컴파일러가 만든 멤버별 복사가 맞다([목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/)) |
| 자원을 `unique_ptr`·`vector`·`string` 에 맡겼다 | ★★★ **아무것도 안 쓴다** | 멤버가 알아서 깊게 복사한다 |
| 포인터·핸들을 직접 든다 | ★★ **깊은 복사를 쓰거나 복사를 `= delete`** | 얕은 복사는 이중 해제([15번](../15-raii-resources-as-types/)) |
| 복사 대입을 쓰기로 했다 | ★★★ **copy-and-swap** | 자기 대입과 강한 보장을 한 형태로((5)) |
| 자기 대입이 잦은 것이 확실하다 | ★ **`if (this == &o)` 한 줄** | copy-and-swap 은 그 경우에도 복사를 한다((5)) |
| 복사가 뜻이 없는 타입(락·소켓) | ★★ **`= delete`** | 「복사할 수 없다」를 타입으로 말한다 |
| 함수에 넘기기만 한다 | ★★ **`const T&`** | (1)의 `(8)` — 아무것도 안 만들어진다([목록의 **11번 주제**](../11-choosing-parameter-passing/)) |
| 큰 것을 돌려준다 | ★ **그냥 값으로 돌려준다** | (2) — 생략이 의무인 자리가 있다 |

- ★ **「복사를 쓰지 마라」가 아니라 「복사를 손으로 쓸 이유를 먼저 없애라」가 기본값이다.**

## 핵심 문장

- **선언과 함께 쓴 `=` 는 복사 생성자**, **이미 있는 것에 쓴 `=` 는 복사 대입**이다 — 같은 기호가 다른 것을 부른다.
- **값으로 받는 함수 인자도 복사**다. `const&` 로 받으면 **아무것도 안 만들어진다.**
- **컴파일러가 만드는 복사는 멤버별 복사**이고, 포인터 멤버가 있으면 그것이 곧 **이중 해제의 경로**다.
- **깊은 복사는 「잡고 나서 놓는다」가 규칙**이다 — 순서를 뒤집으면 자기 대입에서 use-after-free 다.
- **copy-and-swap 은 자기 대입 검사 한 줄 없이 자기 대입과 강한 보장을 동시에 푼다.**
- **복사 생성자는 `T(T)` 로 쓸 수 없고** 복사 대입은 **`T& operator=(T)` 로 써도 된다.**
- **복사의 논리가 틀린 것은 어떤 컴파일러도 경고하지 않는다** — 탐침 여섯 중 답한 것은 **하나**뿐이었다.

## 관련 자료

- [15번](../15-raii-resources-as-types/) — **이 주제의 직전.** (4)의 「복사를 안 막은 래퍼가 `[놓음]` 2줄 + `double-free`」가 **여기 (3)의 출발점**이다.\
  ★ 그쪽은 **막는 쪽**, 여기는 **제대로 만드는 쪽**이다.
- [14번](../14-destructors-and-deterministic-destruction/) — **놓는 시점.** (4)의 「값만 상하고 안 터진다」가 성립하는 이유가 거기 있다.
- [13번](../13-constructors-member-init-list-and-delegating/) — **멤버 초기화 순서는 선언 순서.** (문법)의 형태가 그 규칙 위에 서 있다.
- [8번](../08-value-categories-lvalue-prvalue-xvalue/)·[9번](../09-rvalue-references-move-and-forward/) — **값 범주와 `std::move`.** (2)의 「`return t;` 의 `t` 가 먼저 rvalue 로 취급된다」가 거기가 정본이다.
- [11번](../11-choosing-parameter-passing/) — **무엇으로 받을 것인가.** (1)의 `(7)`·`(8)` 이 그 선택의 계수판이다.
- [`variables-and-memory/`](../../../../variables-and-memory/) §2 — **얕은/깊은 복사의 개념.** 여기는 **C++ 특수 멤버의 구현**까지.
- [목록의 **17번 주제**](../17-move-constructor-assignment-and-moved-from-state/) — 이동. (1)의 `(5)`·`(6)`·`(9)` 가 거기가 정본이다.
- [목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/) — **0/3/5의 법칙.** (7)의 탐침 2번이 답한 그 경고가 **그 주제의 예고**다.
- 목록의 **52번 주제** — 예외 안전 보장 4단계. (5)가 보인 것은 **강한 보장의 한 사례**다.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **9번**([`09-copy-clone-and-drop/`](../../../rust/syntax/09-copy-clone-and-drop/)) — **러스트는 복사가 기본이 아니다.**\
  ★ `Clone` 을 **손으로 불러야** 깊은 복사가 되고, `Copy` 는 **비트 복사가 안전한 타입에만** 붙는다.\
  ★ C++ 의 「아무 말이 없으면 멤버별 복사」와 **기본값이 정반대**다.
- C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **2번**([`02-struct-vs-class-choosing/`](../../../csharp/syntax/02-struct-vs-class-choosing/)) — **값 타입이냐 참조 타입이냐가 복사의 뜻을 정한다.**\
  ★ C++ 은 **타입마다 복사의 뜻을 저자가 정한다** — 그 권한이 이 주제의 값이자 비용이다.

## 용어 풀이

> **복사 생성자(copy constructor)** — **없던 객체를 있는 객체에서 만드는 것**. `T(const T&)`.\
> 예: (1)의 `(1)`\~`(3)` — 셋 다 새 번호가 붙었다.

> **복사 대입 연산자(copy assignment operator)** — **이미 있는 객체의 내용을 갈아 끼우는 것**. `T& operator=(const T&)`.\
> 예: (1)의 `(4)` — `#1` 이 그대로 있고 내용만 바뀌었다.

> **얕은 복사(shallow copy)** — 멤버를 그대로 베끼는 것. 포인터면 **주소가 베껴진다.**\
> 예: (7)의 탐침 1번 · [15번](../15-raii-resources-as-types/) (4)의 `double-free`.

> **깊은 복사(deep copy)** — 가리키는 것까지 새로 만드는 것.\
> 예: (3)에서 `a.p == b.p` 가 **0**, `strcmp(a.p, b.p) == 0` 이 **1** 이었다.

> **자기 대입(self-assignment)** — `a = a` 또는 `v[i] = v[j]` 에서 `i == j` 인 것.\
> 예: (4)에서 naive 구현이 **놓은 메모리를 읽었다**(`heap-use-after-free`).

> **copy-and-swap** — 값으로 받아 복사를 끝내 놓고 **맞바꾸기만** 하는 대입 형태.\
> 예: (5)의 `Safe& operator=(Safe o) { swap(*this, o); return *this; }`.

> **복사 생략(copy elision)** — 복사·이동을 **아예 안 하고 목적지에 바로 짓는 것**.\
> 예: (2)에서 `prvalue()` 판이 `-fno-elide-constructors` 를 켜도 **안 바뀌었다**(C++17 의무).

> **NRVO(named return value optimization)** — **이름 있는 지역 변수**를 돌려줄 때의 생략. **재량**이다.\
> 예: (2)의 `(2)` — 끄니까 **이동 생성자**가 한 번 더 돌았다.

> **강한 보장(strong guarantee)** — 연산이 실패해도 **아무것도 안 바뀐 것처럼** 남는 것.\
> 예: (5)의 `(2)` — 할당이 실패했는데 `s1` 이 원본 그대로였다. 정본은 목록의 **52번 주제**.

> **use-after-free** — 놓은 메모리를 다시 읽거나 쓰는 것. **UB** 다.\
> 예: (4)에서 ASan 이 `READ of size 2` 라고 불렀다.

## 더 들어가면

- **`operator=` 의 ref-qualifier**(`T& operator=(const T&) &`) — 임시에 대입하는 코드를 막는 문법. 이 문서는 안 건드렸다.
- **할당자(allocator)를 가진 타입의 복사 대입** — `propagate_on_container_copy_assignment` 가 **무엇을 복사할지 정한다.** 표준 컨테이너의 층이다.
- **`std::swap` 의 ADL 관용구**(`using std::swap; swap(a, b);`) — (5)의 `friend void swap` 이 그 관용구를 받으려고 있는 것이다([6번](../06-namespaces-and-adl/)).
- **`-Wdeprecated-copy` 가 무엇을 deprecate 했나** — C++11 이 「복사 생성자를 쓰면 암묵 복사 대입을 deprecate」로 못 박았다. 정본은 [목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/).
- **복사 생략이 관찰 가능한 부작용을 지우는 것** — 생성자에 `printf` 를 넣은 이 문서의 예제가 바로 그 「관찰」이다. 표준이 **그 관찰의 소멸을 허용한다.**
