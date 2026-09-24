# cpp/syntax/10 — `const` 정확성 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — cv 한정자](https://en.cppreference.com/w/cpp/language/cv) · [const 멤버 함수](https://en.cppreference.com/w/cpp/language/member_functions) · [`mutable` 지정자](https://en.cppreference.com/w/cpp/language/cv#mutable) · [`const_cast`](https://en.cppreference.com/w/cpp/language/const_cast) · [저장 기간과 링크](https://en.cppreference.com/w/cpp/language/storage_duration) · [GCC 13 Warning Options — `-Wwrite-strings`](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html)
> **실행 검증** — 이 문서의 모든 출력·진단·심볼은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **GNU nm 2.42** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`cnst01.cpp` \~ `cnst08.cpp`, 링크 편은 `cnst05a`·`cnst05b`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 긴 진단은 **거르는 명령을 배너에 적어 두었다**(`| grep 'error:'`).\
> 그러니 실린 것은 「생략한 일부」가 아니라 **그 명령의 전체 출력**이다.\
> ★ **UB 를 한 최적화 수준으로만 단정하지 않았다** — `const_cast` 편은 **`-O0`·`-O2`·clang `-O2`·UBSan 네 판**을 던졌다((6)).
> **버전** — `const` 자체는 **C++98부터**. `constexpr` 는 **C++11부터**,\
> ★ **문자열 리터럴을 `char*` 에 넣는 것이 ill-formed 가 된 것은 C++11부터**다((10)). 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> **경계** — 「`const char *` / `char * const` 를 **읽는 순서**」의 정본은\
> C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **31번**이다 — 여기서는 **에러 한 줄씩만** 보고 넘어간다((9)).\
> 「포인터가 무엇인가」는 C 갈래 [`14번`](../../../c/syntax/14-pointers-address-dereference-and-pointer-types/),\
> 「문자열 리터럴의 저장 기간」은 C 갈래 [`20번`](../../../c/syntax/20-null-terminated-strings-and-string-literals/),\
> 「스코프와 링크 일반」은 C 갈래 목록의 **29번**이 정본이다.\
> 「캐스트 4종을 어떻게 고르나」의 정본은 형제 [`03번`](../03-four-cast-operators/)이다 —\
> 여기서는 **`const_cast` 가 무엇을 사고 무엇을 잃는가**만 본다((6)).\
> 「참조가 무엇인가」는 형제 [`07번`](../07-references-vs-pointers/), 「값 범주」는 목록의 **08번 주제**,\
> 「`const` 객체를 `move` 하면 무슨 일이 나나」는 목록의 **09번 주제**,\
> 「그래서 매개변수를 `const&` 로 받나」는 목록의 **11번 주제**,\
> 「`constexpr`·`consteval` 자체」는 목록의 **38번 주제**가 정본이다.
> ★★★ **이 주제는 「금지 목록」이 아니라 「계약」이다** — `const` 가 **무엇을 막고 무엇을 안 막는지**가 값의 전부다.\
> 안 막는 쪽이 (4)·(6)·(10) 셋이고, **셋 다 진단이 0건**이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 두 컴파일러의 **에러 문구**와 **열 번호** | ★ **에러가 난 줄 번호와 개수**(g++ 7 · clang 7) |
> | `nm` 출력의 **주소·오프셋**(`0000...0f`) | ★★ **심볼 종류 문자**(`r` 는 내부 · `R` 는 외부 · `U` 는 미정의) |
> | UB 판에서 **죽는 신호**(이 문서는 `run exit` 만 싣는다) | ★ **`cc exit` 와 `run exit`**(갈라 적었다) |
> | 경고 이름(`-Wwrite-strings` 대 `-Wwritable-strings`) | ★★ **생성자·호출 횟수**(`hits` 1·2·3) · `sizeof` 값 |
> | — | ★★★ **`k=10 *p=20 &k==p:1`** — 네 판이 전부 같았다((6)) |

## 한눈에 — 쉽게 말하면

**`const` 는 자물쇠가 아니라 「내가 안 고치겠다」고 적어 둔 각서다.**

각서는 **그 문을 지나는 사람에게만** 효력이 있다.\
옆문이 열려 있으면 **각서를 지키면서도 안이 바뀐다.**

| 비유 | 실체 | 막나 |
|---|---|---|
| **각서에 서명하고 들어간다** | `void f(const T& x)` — `x` 로는 못 고친다 | ★ 막는다 |
| **각서를 쓴 사람이 자기 방에서 하는 일** | `mutable` 멤버 — `const` 멤버 함수가 고친다 | 안 막는다((3)) |
| ★★ **각서는 「이 방」에 대한 것이지 「열쇠 꾸러미」에 대한 게 아니다** | `int* p` 멤버 — `const` 멤버가 `*p` 를 고친다 | ★★ 안 막는다((4)) |
| ★★ **각서를 찢고 들어가면** | `const_cast` 로 진짜 `const` 를 고친다 | ★★★ **UB**((6)) |
| ★ **각서에 이름을 안 적으면 그 동네에서만 유효하다** | 네임스페이스 스코프 `const` — **내부 링크**((7)) | — |
| ★ **「지금 값을 안다」는 각서가 아니다** | `constexpr` — 컴파일 시간 상수((8)) | 다른 축이다 |

> **`const` 정확성(const correctness)** — 「고치지 않는 것은 전부 `const` 로 적는다」는 설계 규율.\
> 예: `size_t size() const` 라고 적어 두면 **`const` 컨테이너에서도 크기를 물을 수 있다**((2)).

- ★★★ **`const` 는 「접근 경로」에 붙는다.** 같은 객체를 `Buf&` 로도 `const Buf&` 로도 볼 수 있고, **보는 창에 따라 되는 일이 다르다**((2)).
- ★★★ **「객체 자체가 `const` 인가」와 「지금 `const` 로 보고 있나」는 다른 질문이다.**\
  앞엣것이 UB 를 가르고((6)), 뒤엣것이 컴파일 에러를 가른다((9)).
- ★★ **`const` 가 막는 것은 「그 창으로 쓰는 것」뿐**이다 — 포인터 멤버·`mutable`·`const_cast` 셋이 전부 옆문이다.

```text
   Buf b;                    객체는 비-const 다

   b        ──────────>  ┌──────────────┐     b.at(0) = 9;   된다
   (Buf&)                │  a[3]        │
                         │  = {9,2,3}   │
   cb       ──────────>  └──────────────┘     cb.at(0) = 9;  에러
   (const Buf&)                                cb.sum()      된다

   같은 객체 · 다른 창 · 다른 규칙
```

## 이 주제가 답하려는 질문

1. **`const` 는 어디에 붙고 무엇을 고르나** — 멤버 함수·매개변수·오버로드((2)).
2. **`const` 가 안 막는 것은 무엇인가** — `mutable`((3)) · 포인터 멤버((4)) · `const_cast`((6)).
3. **`const` 가 타입 밖에서 하는 일은 무엇인가** — 링크((7))와 상수식((8)).

## 동작 방식

### (0) 이 주제가 쓰는 네 창

`const` 는 **대부분 컴파일 시간에 끝나는 것**이라 창이 컴파일러 쪽으로 몰린다.

```text
① 컴파일 에러 목록                  const 가 막는 것을 전수로 본다            (9)
② 실행 로그 (호출 횟수·값)          const 가 안 막는 것을 값으로 본다         (2)(3)(4)
③ nm 의 심볼 종류 문자              const 가 링크에 한 일을 본다              (7)
④ ★★ 같은 UB 를 네 판으로           최적화 수준·컴파일러·UBSan 을 갈라 본다    (6)
```

- ★★★ **네 번째 창은 ④다** — UB 를 **한 판만 돌리고 단정하면 틀린다.**\
  이번에는 **네 판이 전부 같았고**, 그래서 결론을 「값이 갈린다」가 아니라\
  「**같은 주소가 두 값을 답한다**」로 적었다((6)).
- ★ ③은 **소스를 아무리 읽어도 안 보이는 것**이다 — `const` 하나가 심볼 종류를 바꾼다((7)).

### (1) `const` 는 「객체」에 붙기도 하고 「경로」에 붙기도 한다

**언제 쓰나** — 「이게 왜 에러지」와 「이게 왜 UB 지」를 갈라야 할 때.

```text
   [A] 객체가 const 다
       const int k = 10;          ← 객체 자체가 const
       int* p = const_cast<int*>(&k);
       *p = 20;                   ← ★ UB ((6))

   [B] 경로만 const 다
       int m = 30;                ← 객체는 평범하다
       const int& cr = m;         ← 이 창으로는 못 쓴다
       const_cast<int&>(cr) = 40; ← ★ UB 아님 ((6))
```

- ★★★ **같은 `const_cast` 인데 하나는 UB 이고 하나는 아니다.** 가른 것은 **원래 객체가 `const` 였나**다.
- ★★ **컴파일러는 [A]와 [B]를 구별해 주지 않는다** — 둘 다 조용히 통과한다((6)의 진단 0건).
- ★ 「`const_cast` 를 언제 쓰나」의 정본은 형제 [`03번`](../03-four-cast-operators/)이다. 여기서는 **UB 경계**만 본다.

**비용** — `const` 는 **런타임 코드를 한 줄도 만들지 않는다.** 전부 타입 검사다.

### (2) `const` 멤버 함수와 `const` 오버로드

**언제 쓰나** — 컨테이너·래퍼를 만들 때. **읽기 전용 사용자를 받을 것인가**가 여기서 정해진다.

```text
===== 소스: cnst01.cpp =====
// const 멤버 함수와 const 오버로드 — 객체의 const 가 어느 함수를 고르나
#include <cstdio>

struct Buf {
    int a[3]{1, 2, 3};

    int&       at(int i)       { std::puts("    at()       비-const 판"); return a[i]; }
    const int& at(int i) const { std::puts("    at() const const 판");    return a[i]; }

    int sum() const { return a[0] + a[1] + a[2]; }
    void bump()     { ++a[0]; }
};

int main() {
    Buf b;
    const Buf& cb = b;

    std::puts("[1] b.at(0) = 9;        객체가 비-const");
    b.at(0) = 9;
    std::puts("[2] cb.at(0) 을 읽는다   객체가 const");
    std::printf("    값 %d\n", cb.at(0));
    std::puts("[3] const 객체로도 부를 수 있는 것");
    std::printf("    cb.sum() = %d\n", cb.sum());
    std::printf("    b.sum()  = %d   (비-const 객체도 const 멤버를 부른다)\n", b.sum());
    b.bump();
    std::printf("    b.bump() 뒤 sum = %d\n", b.sum());
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cnst01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] b.at(0) = 9;        객체가 비-const
    at()       비-const 판
[2] cb.at(0) 을 읽는다   객체가 const
    at() const const 판
    값 9
[3] const 객체로도 부를 수 있는 것
    cb.sum() = 14
    b.sum()  = 14   (비-const 객체도 const 멤버를 부른다)
    b.bump() 뒤 sum = 15
```

```text
   호출식을 본다
        ↓
   객체(혹은 참조)가 const 인가?
        아니오 ──> 비-const 판이 있으면 그것   at(int)        int& 를 돌려준다
        예     ──> const 판만 후보            at(int) const  const int& 를 돌려준다
                   const 판이 없으면 ─────> 컴파일 에러 ((9)의 (3))
```

- ★★★ **`const` 는 오버로드를 가르는 축이다.** `at(int)` 와 `at(int) const` 는 **다른 함수**이고,\
  「객체가 `const` 인가」가 **둘 중 하나를 고른다**.
- ★★ **`cb.at(0)` 이 `const` 판을 골랐고, 값 9 를 돌려줬다** — 앞줄에서 비-const 판으로 쓴 값이다.\
  **같은 객체를 두 창으로 본 것**이다.
- ★ **비-const 객체도 `const` 멤버를 부른다** — `b.sum()` 이 된다. 반대는 안 된다.\
  그래서 **「고치지 않는 멤버는 전부 `const` 로 적는다」가 규율이 된다** — 안 적으면 `const` 사용자가 못 쓴다.
- ★ 반환 타입도 같이 갈린다 — 비-const 판은 `int&`(쓸 수 있다), `const` 판은 `const int&`(못 쓴다).

**비용** — 두 판이 같은 몸통이면 **코드가 두 벌 생긴다.** 흔한 관용구는 한쪽이 다른 쪽을 부르게 하는 것인데,\
**그 관용구가 `const_cast` 를 쓰므로** (6)의 경계를 알고 써야 한다.

### (3) `mutable` — `const` 멤버 함수 안에서 바뀌는 유일한 멤버

**언제 쓰나** — 캐시·호출 횟수·뮤텍스처럼 「**논리적으로는 안 바뀐 것**」을 담을 때.

```text
===== 소스: cnst02.cpp =====
// mutable — const 멤버 함수 안에서 바뀌는 유일한 멤버
#include <cstdio>

struct Doc {
    int              text = 41;
    mutable int      cached = -1;      // 계산 결과 저장
    mutable unsigned hits = 0;         // 호출 횟수

    int score() const {
        ++hits;                         // const 인데 바뀐다
        if (cached < 0) cached = text + 1;
        return cached;
    }
};

int main() {
    const Doc d;
    std::printf("부르기 전: cached=%d hits=%u\n", d.cached, d.hits);
    for (int n = 1; n <= 3; ++n) {
        int v = d.score();              // ★ 한 줄에 하나만 — 평가 순서에 안 기댄다
        std::printf("%d회째    : score=%d cached=%d hits=%u\n", n, v, d.cached, d.hits);
    }
    std::printf("text      : %d  (이쪽은 const 객체라 못 바꾼다)\n", d.text);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cnst02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
부르기 전: cached=-1 hits=0
1회째    : score=42 cached=42 hits=1
2회째    : score=42 cached=42 hits=2
3회째    : score=42 cached=42 hits=3
text      : 41  (이쪽은 const 객체라 못 바꾼다)
```

> **`mutable`** — 비정적 데이터 멤버에 붙이면 **그 멤버만 `const` 규칙에서 빠진다.**\
> 예: `mutable unsigned hits;` 를 두면 `const` 멤버 함수가 `++hits` 를 할 수 있다.

- ★★★ **객체가 `const Doc d;` 인데 `hits` 가 1 → 2 → 3 으로 늘었다.**\
  `score()` 에 `const` 가 붙어 있는데도다.
- ★★ **`cached` 가 -1 에서 42 로 한 번만 바뀐다** — 두 번째부터는 계산을 안 한다.\
  「**결과는 같고 내부만 바뀐다**」가 논리적 `const` 의 정의다.
- ★ **`text` 는 못 바꾼다** — `mutable` 이 아닌 멤버는 그대로 막힌다((9)의 (1)).
- ★★ ★ **`mutable` 은 예외이지 구멍이 아니다** — 무엇이 예외인지 **선언에 적혀 있다.**\
  (4)의 포인터 멤버는 **선언에 아무것도 안 적혀 있다** — 그쪽이 구멍이다.

**비용** — 없다. 다만 **스레드 안전이 깨진다** — `const` 를 보고 「읽기만 하니 락이 필요 없겠지」라고 읽는 쪽이 틀리게 된다.

### (4) ★★★ 비트단위 `const` 와 논리적 `const` — 포인터 멤버가 뚫는 구멍

**언제 쓰나** — 멤버에 포인터·참조·핸들이 있을 때. **거의 모든 래퍼가 여기 해당한다.**

> **비트단위 const(bitwise const)** — 「객체의 **비트가** 안 바뀐다」. 컴파일러가 강제하는 것이 이쪽이다.\
> 예: `const Holder h;` 에서 **`h.p` 라는 포인터 값**은 못 바꾼다.

> **논리적 const(logical const)** — 「객체가 **뜻하는 상태가** 안 바뀐다」. 사람이 지키는 것이다.\
> 예: `*h.p` 를 바꾸면 비트단위로는 안 바뀌었지만 **뜻은 바뀐다.**

```text
===== 소스: cnst03.cpp =====
// 비트단위 const 와 논리적 const — 포인터 멤버가 뚫는 구멍
#include <cstdio>

struct Holder {
    int  own = 1;        // 내 것
    int* p;              // 남의 것을 가리킨다

    explicit Holder(int* q) : p(q) {}

    void poke() const { *p = 99; }        // 된다 — p 가 const 지 *p 는 아니다
    int& leak() const { return *p; }      // const 멤버가 쓰기 가능한 참조를 내준다
    int  read() const { return own; }
};

int main() {
    int outside = 1;
    const Holder h(&outside);

    std::printf("전   : outside=%d h.own=%d\n", outside, h.own);
    h.poke();
    std::printf("poke : outside=%d   (h 는 const 인데 밖이 바뀌었다)\n", outside);
    h.leak() = 7;
    std::printf("leak : outside=%d   (const 멤버가 돌려준 참조로 썼다)\n", outside);
    std::printf("own  : %d           (이쪽은 정말 못 바꾼다)\n", h.read());
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cnst03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
전   : outside=1 h.own=1
poke : outside=99   (h 는 const 인데 밖이 바뀌었다)
leak : outside=7   (const 멤버가 돌려준 참조로 썼다)
own  : 1           (이쪽은 정말 못 바꾼다)
```

```text
   const Holder h(&outside);

   h ──> ┌──────────────┐
         │ own  = 1     │  ← 이쪽은 h 의 const 가 지킨다
         │ p    = &outside ─────> outside = 1
         └──────────────┘         ↑
                                  │  h.poke();      *p = 99   ← 된다
                                  │  h.leak() = 7;            ← 된다
                                  └── const 는 여기까지 안 간다
```

- ★★★ **`h` 는 `const` 인데 `outside` 가 1 → 99 → 7 로 바뀐다.** 경고도 에러도 **0건**이다.
- ★★★ **`const` 가 지키는 것은 `p` 라는 포인터 값**이지 **`p` 가 가리키는 곳**이 아니다.\
  「**`T* const`** 는 되지만 **`const T*`** 는 아니다」를 멤버로 옮긴 것이다 —\
  읽는 순서의 정본은 C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **31번**이다.
- ★★ **`leak()` 이 더 나쁘다** — `const` 멤버 함수가 **쓰기 가능한 참조**(`int&`)를 밖으로 내준다.\
  호출한 쪽은 `const` 객체를 만졌다는 것도 모른다.
- ★ **`own` 은 정말 못 바꾼다** — 값으로 든 멤버에는 `const` 가 그대로 간다.
- ★ 고치는 법은 **`const` 멤버 함수가 `const T&` 를 돌려주게 하는 것**이고,\
  **가리키는 것까지 막고 싶으면 멤버를 `const T*` 로** 든다.

**비용** — 없다. 이것은 **비용이 아니라 설계 실수의 자리**다.

### (5) `const` 매개변수 — 창을 좁혀 계약을 적는다

**언제 쓰나** — 함수 시그니처를 쓸 때마다.

```text
   void f(Buf& b);          "고칠 수도 있다"          const 객체는 못 넘긴다
   void f(const Buf& b);    "안 고친다"               ★ 넷 다 받는다
   void f(Buf b);           "복사본을 가진다"          원본과 무관하다
   void f(const Buf b);     ★ 거의 뜻이 없다          복사본을 안 고치겠다는 말
```

- ★★★ **`const T&` 가 lvalue·const lvalue·prvalue·xvalue 를 전부 받는다** — 그 격자의 정본은 목록의 **08번 주제**다.
- ★★ **값 매개변수에 `const` 를 붙이는 것은 선언에서는 무의미하다** — 호출하는 쪽이 볼 이유가 없다.\
  **정의에만** 붙여 「이 함수 안에서 안 고친다」를 적는 용도다.
- ★ **그래서 무엇으로 받을지**를 크기·수명·소유권으로 고르는 것이 목록의 **11번 주제**다 — 여기서는 **계약 표기**까지만.

### (6) ★★★ `const_cast` — 진짜 `const` 를 고치면 UB

**언제 쓰나** — `const` 를 안 붙인 옛 API 에 `const` 객체를 넘겨야 할 때.

```text
===== 소스: cnst04.cpp =====
// const_cast — 원래 const 인 것을 고치면 UB, 아니면 아니다
#include <cstdio>

int main() {
    const int k = 10;
    int* p = const_cast<int*>(&k);
    *p = 20;                                   // ★ 여기가 UB
    std::printf("[UB]    k=%d  *p=%d  &k==p:%d\n",
                k, *p, static_cast<int>(&k == p));

    int m = 30;                                // 원래 const 가 아니다
    const int& cr = m;
    const_cast<int&>(cr) = 40;                 // ★ UB 아님
    std::printf("[정상]  m=%d  cr=%d\n", m, cr);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 cnst04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[UB]    k=10  *p=20  &k==p:1
[정상]  m=40  cr=40
```

**같은 소스를 `-O2` 로.**

```text
===== 소스: cnst04.cpp =====
// const_cast — 원래 const 인 것을 고치면 UB, 아니면 아니다
#include <cstdio>

int main() {
    const int k = 10;
    int* p = const_cast<int*>(&k);
    *p = 20;                                   // ★ 여기가 UB
    std::printf("[UB]    k=%d  *p=%d  &k==p:%d\n",
                k, *p, static_cast<int>(&k == p));

    int m = 30;                                // 원래 const 가 아니다
    const int& cr = m;
    const_cast<int&>(cr) = 40;                 // ★ UB 아님
    std::printf("[정상]  m=%d  cr=%d\n", m, cr);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 cnst04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[UB]    k=10  *p=20  &k==p:1
[정상]  m=40  cr=40
```

**같은 소스를 clang 으로.**

```text
===== 소스: cnst04.cpp =====
// const_cast — 원래 const 인 것을 고치면 UB, 아니면 아니다
#include <cstdio>

int main() {
    const int k = 10;
    int* p = const_cast<int*>(&k);
    *p = 20;                                   // ★ 여기가 UB
    std::printf("[UB]    k=%d  *p=%d  &k==p:%d\n",
                k, *p, static_cast<int>(&k == p));

    int m = 30;                                // 원래 const 가 아니다
    const int& cr = m;
    const_cast<int&>(cr) = 40;                 // ★ UB 아님
    std::printf("[정상]  m=%d  cr=%d\n", m, cr);
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic -O2 cnst04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[UB]    k=10  *p=20  &k==p:1
[정상]  m=40  cr=40
```

**같은 소스를 UBSan 으로.**

```text
===== 소스: cnst04.cpp =====
// const_cast — 원래 const 인 것을 고치면 UB, 아니면 아니다
#include <cstdio>

int main() {
    const int k = 10;
    int* p = const_cast<int*>(&k);
    *p = 20;                                   // ★ 여기가 UB
    std::printf("[UB]    k=%d  *p=%d  &k==p:%d\n",
                k, *p, static_cast<int>(&k == p));

    int m = 30;                                // 원래 const 가 아니다
    const int& cr = m;
    const_cast<int&>(cr) = 40;                 // ★ UB 아님
    std::printf("[정상]  m=%d  cr=%d\n", m, cr);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 -fsanitize=undefined cnst04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[UB]    k=10  *p=20  &k==p:1
[정상]  m=40  cr=40
```

```text
   const int k = 10;
   int* p = const_cast<int*>(&k);
   *p = 20;

   &k == p 는 1  ──  같은 주소다
        │
        ├── k    를 읽으면 ──> 10     컴파일러가 "const 니까 10" 이라고 접어 둔 것
        └── *p   를 읽으면 ──> 20     실제로 써 놓은 값

   같은 주소가 두 값을 답한다.
```

- ★★★ **네 판이 전부 같았다** — `-O0` · `-O2` · clang `-O2` · UBSan.\
  ★ **한 수준만 돌리고 UB 를 단정하지 않았다**는 뜻이고, **그래도 「어느 판에서도 안전하다」는 결론은 못 낸다.**
- ★★★ **읽을 것은 값이 아니라 모순이다** — `&k == p` 가 **1** 인데 `k` 와 `*p` 가 **다르다.**\
  「어느 값이 맞나」가 아니라 「**둘 다 맞다고 우긴다**」가 UB 의 모양이다.
- ★★ **[정상] 줄은 UB 가 아니다** — `m` 은 원래 `const` 가 아니었으므로 `const_cast` 로 쓰는 것이 **허용**된다.\
  `m=40 cr=40` 으로 **한 값만** 답한다.
- ★★★ **UBSan 이 한 줄도 안 낸다** — `run exit=0`. **이 UB 는 sanitizer 로 안 잡힌다.**
- ★ 그래서 `const_cast` 는 **「내가 이 객체가 원래 `const` 가 아님을 안다」** 일 때만 쓴다.\
  캐스트 4종을 고르는 기준의 정본은 형제 [`03번`](../03-four-cast-operators/)이다.

**비용** — `const_cast` 자체는 **명령을 한 개도 안 만든다.** 위험은 전적으로 **의미** 쪽이다.

### (7) `const` 가 링크에 미치는 것 — 내부 링크

**언제 쓰나** — 헤더에 상수를 둘 때. **C 와 갈리는 자리**다.

```text
===== 소스: cnst05a.cpp =====
// 번역 단위 A — 네임스페이스 스코프의 const 는 내부 링크다
const int limit = 10;              // 이 TU 만의 것
extern const int shared = 20;      // extern 을 붙이면 외부 링크

int from_a()        { return limit; }
int shared_from_a() { return shared; }
===== 소스: cnst05b.cpp =====
// 번역 단위 B — 같은 이름을 다시 정의해도 충돌하지 않는다
#include <cstdio>

const int limit = 99;              // A 의 limit 과 다른 물건
extern const int shared;           // A 의 것을 쓴다

int from_a();
int shared_from_a();

int main() {
    std::printf("limit  : B 에서 %d · A 에서 %d\n", limit, from_a());
    std::printf("shared : B 에서 %d · A 에서 %d\n", shared, shared_from_a());
    std::printf("&limit 를 비교할 수 있나 : 두 TU 의 limit 는 서로 다른 객체다\n");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -c cnst05a.cpp -o a.o && g++ -std=c++20 -Wall -Wextra -pedantic -c cnst05b.cpp -o b.o && g++ a.o b.o -o ex && ./ex (exit=0) =====
limit  : B 에서 99 · A 에서 10
shared : B 에서 20 · A 에서 20
&limit 를 비교할 수 있나 : 두 TU 의 limit 는 서로 다른 객체다
```

```text
   cnst05a.cpp                      cnst05b.cpp
   ┌──────────────────────┐         ┌──────────────────────┐
   │ const int limit = 10 │         │ const int limit = 99 │
   │   (내부 링크)         │         │   (내부 링크)         │
   │                      │         │                      │
   │ extern const int     │ <────── │ extern const int     │
   │   shared = 20        │  같은 것 │   shared;            │
   └──────────────────────┘         └──────────────────────┘

   limit  : 이름이 같아도 서로 다른 객체 — 링커가 아무 말 안 한다
   shared : 하나뿐 — 양쪽이 20 을 본다
```

`nm` 으로 심볼 종류를 직접 본다.

```text
===== 소스: cnst05a.cpp =====
// 번역 단위 A — 네임스페이스 스코프의 const 는 내부 링크다
const int limit = 10;              // 이 TU 만의 것
extern const int shared = 20;      // extern 을 붙이면 외부 링크

int from_a()        { return limit; }
int shared_from_a() { return shared; }
===== nm -C a.o; echo '--- b.o ---'; nm -C b.o (exit=0) =====
000000000000000f T shared_from_a()
0000000000000000 T from_a()
0000000000000000 r limit
0000000000000004 R shared
--- b.o ---
                 U shared_from_a()
                 U from_a()
0000000000000000 r limit
0000000000000000 T main
                 U printf
                 U puts
                 U shared
```

- ★★★ **`r limit` 와 `R shared`** — **소문자는 내부**(local), **대문자는 외부**(global)다.\
  `const` 하나가 **심볼의 종류를 바꿨다.**
- ★★ **`b.o` 에도 `r limit` 가 따로 있다** — 두 번역 단위가 **각자의 `limit`** 를 들고 있다.\
  출력에서 「B 에서 99 · A 에서 10」이 그것이다.
- ★★ **`shared` 는 `b.o` 에서 `U`**(미정의)다 — 링커가 `a.o` 의 `R shared` 로 이어 준다.
- ★ 그래서 **헤더에 `const int limit = 10;` 을 써도 ODR 위반이 안 난다** — 포함한 파일마다 **자기 복사본**을 갖는다.\
  ★ 대신 **주소가 파일마다 다르다** — 주소를 비교하는 코드는 여기서 조용히 틀린다.
- ★ **C 는 이렇지 않다** — C 의 파일 스코프 `const` 는 **외부 링크**다.\
  링크 일반의 정본은 C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **29번**이다.
- ★ **C++17 부터는 `inline constexpr` 를 쓰면** 번역 단위마다 복사본이 안 생긴다 — 그 정본은 목록의 **25번 주제**다.

**비용** — 번역 단위마다 **객체 하나씩** 생길 수 있다. `int` 하나면 무시할 만하고, **큰 배열이면 아니다.**

### (8) `const` 와 `constexpr` — 다른 축이다

**언제 쓰나** — 「배열 크기로 쓸 수 있나」가 걸릴 때.

```text
===== 소스: cnst06.cpp =====
// const 와 constexpr — 「못 바꾼다」와 「컴파일 때 안다」는 다르다
#include <cstdio>

int runtime() { return 3; }

int main() {
    const int     a = 5;          // 초기화식이 상수식이라 상수식으로도 쓰인다
    constexpr int b = 5;          // 상수식임을 강제한다
    const int     c = runtime();  // ★ const 는 런타임 값도 받는다

    int arr1[a]{};                // 된다
    int arr2[b]{};                // 된다
    static_assert(a == 5);
    static_assert(b == 5);

    std::printf("a=%d b=%d c=%d  sizeof(arr1)=%zu sizeof(arr2)=%zu\n",
                a, b, c, sizeof(arr1), sizeof(arr2));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cnst06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a=5 b=5 c=3  sizeof(arr1)=20 sizeof(arr2)=20
```

| | `const` | `constexpr` |
|---|---|---|
| 뜻 | **이 경로로 안 고친다** | **컴파일 시간에 값을 안다** |
| 런타임 값을 받나 | ★ **받는다**(`c = runtime()`) | ★ **못 받는다**((9)의 (5)) |
| 상수식으로 쓰이나 | 초기화식이 상수식일 **때만** | 항상 |
| 링크 | 네임스페이스 스코프면 내부((7)) | 〃 |

- ★★★ **`const int a = 5;` 도 배열 크기로 쓰인다** — `sizeof(arr1)` 이 20 이다.\
  **초기화식이 상수식이었기 때문**이지 `const` 라서가 아니다.
- ★★ **`const int c = runtime();` 은 컴파일된다.** 같은 자리에 `constexpr` 를 쓰면 에러다((9)의 (5)).\
  **`constexpr` 는 「못 고친다」에 「지금 안다」를 더한 것**이다.
- ★ `constexpr`·`consteval`·`constinit` 자체의 정본은 목록의 **38번 주제**다 — 여기서는 **한 줄 경계**까지만.

### (9) `const` 가 막는 일곱

**언제 쓰나** — 에러 메시지를 읽을 때. **일곱 가지가 전부 다른 이유**다.

```text
===== 소스: cnst08.cpp =====
// const 가 막는 일곱 — 전부 에러다
int runtime();

struct S {
    int m = 0;
    int bad() const { m = 1; return m; }   // (1) const 멤버가 멤버를 고친다
    void mut()      { ++m; }
};

int main() {
    const int x;                            // (2) 초기화 없는 const
    const S s;
    s.mut();                                // (3) const 객체로 비-const 멤버 호출
    int* p = &s.m;                          // (4) const 멤버의 주소를 int* 로
    constexpr int d = runtime();            // (5) constexpr 는 런타임 값을 못 받는다

    int i = 0, j = 0;
    int* const cp = &i;
    cp = &j;                                // (6) const 포인터를 다시 겨눈다
    const int* pc = &i;
    *pc = 1;                                // (7) 포인터-투-const 로 쓴다
    (void)x; (void)p; (void)d; (void)pc;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cnst08.cpp -o ex 2>&1 | grep 'error:' (cc exit=1) =====
cnst08.cpp:6:25: error: assignment of member ‘S::m’ in read-only object
cnst08.cpp:11:15: error: uninitialized ‘const x’ [-fpermissive]
cnst08.cpp:13:10: error: passing ‘const S’ as ‘this’ argument discards qualifiers [-fpermissive]
cnst08.cpp:14:14: error: invalid conversion from ‘const int*’ to ‘int*’ [-fpermissive]
cnst08.cpp:15:30: error: call to non-‘constexpr’ function ‘int runtime()’
cnst08.cpp:19:8: error: assignment of read-only variable ‘cp’
cnst08.cpp:21:9: error: assignment of read-only location ‘* pc’
```

| # | 막힌 것 | 무엇을 어긴 건가 |
|---|---|---|
| (1) | `const` 멤버가 멤버를 고친다 | **멤버 함수의 `const`** — `this` 가 `const S*` 다 |
| (2) | 초기화 없는 `const` | **나중에 못 고치므로** 지금 정해야 한다 |
| (3) | `const` 객체로 비-const 멤버 호출 | **오버로드에 후보가 없다**((2)) |
| (4) | `const` 멤버의 주소를 `int*` 로 | **`const` 를 버리는 암묵 변환은 없다** |
| (5) | `constexpr` 가 런타임 값을 받는다 | ★ **`const` 와 갈리는 자리**((8)) |
| (6) | `const` 포인터를 다시 겨눈다 | `int* const` — **포인터가** `const` |
| (7) | 포인터-투-const 로 쓴다 | `const int*` — **가리키는 것이** `const` |

- ★★ **(6)과 (7)이 이 주제에서 가장 자주 헷갈리는 짝**이다. 읽는 순서의 정본은\
  C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **31번** — 여기서는 **에러 한 줄씩**으로 갈라 두는 데까지만 한다.
- ★ 같은 일곱 줄을 clang 으로도 던졌다 — **일곱 개 그대로**이고 문구만 다르다.

```text
===== 소스: cnst08.cpp =====
// const 가 막는 일곱 — 전부 에러다
int runtime();

struct S {
    int m = 0;
    int bad() const { m = 1; return m; }   // (1) const 멤버가 멤버를 고친다
    void mut()      { ++m; }
};

int main() {
    const int x;                            // (2) 초기화 없는 const
    const S s;
    s.mut();                                // (3) const 객체로 비-const 멤버 호출
    int* p = &s.m;                          // (4) const 멤버의 주소를 int* 로
    constexpr int d = runtime();            // (5) constexpr 는 런타임 값을 못 받는다

    int i = 0, j = 0;
    int* const cp = &i;
    cp = &j;                                // (6) const 포인터를 다시 겨눈다
    const int* pc = &i;
    *pc = 1;                                // (7) 포인터-투-const 로 쓴다
    (void)x; (void)p; (void)d; (void)pc;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic cnst08.cpp -o ex 2>&1 | grep -E 'error:|generated' (cc exit=1) =====
cnst08.cpp:6:25: error: cannot assign to non-static data member within const member function 'bad'
cnst08.cpp:11:15: error: default initialization of an object of const type 'const int'
cnst08.cpp:13:5: error: 'this' argument to member function 'mut' has type 'const S', but function is not marked const
cnst08.cpp:14:10: error: cannot initialize a variable of type 'int *' with an rvalue of type 'const int *'
cnst08.cpp:15:19: error: constexpr variable 'd' must be initialized by a constant expression
cnst08.cpp:19:8: error: cannot assign to variable 'cp' with const-qualified type 'int *const'
cnst08.cpp:21:9: error: read-only variable is not assignable
7 errors generated.
```

- ★ **g++ 의 셋에 `[-fpermissive]` 가 붙어 있다**((2)·(3)·(4)) — 그 플래그로 내려가는 진단이라는 뜻이다.\
  ★★ 그 플래그가 무엇을 하는지의 실측은 목록의 **08번 주제**에 있다((10)과 같은 집안이다).

### (10) ★★★ 「종료 코드가 0인데 ill-formed」 — 이 갈래의 고정 항목

**언제 쓰나** — 옛 C 코드를 C++ 로 옮길 때. **가장 흔한 자리**다.

```text
===== 소스: cnst07.cpp =====
// C++11 부터 ill-formed 인데 컴파일이 통과하는 줄
#include <cstdio>

int main() {
    std::setvbuf(stdout, nullptr, _IONBF, 0);   // 죽어도 출력이 안 사라지게
    char* p = "abc";                            // ★ 여기
    std::printf("쓰기 전: p=%s\n", p);
    p[0] = 'X';                                 // ★ 읽기 전용 구역에 쓴다 — UB
    std::printf("쓴 뒤  : p=%s\n", p);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cnst07.cpp -o ex && ./ex (cc exit=0 · run exit=139) =====
cnst07.cpp: In function ‘int main()’:
cnst07.cpp:6:15: warning: ISO C++ forbids converting a string constant to ‘char*’ [-Wwrite-strings]
    6 |     char* p = "abc";                            // ★ 여기
      |               ^~~~~
쓰기 전: p=abc
```

- ★★★ **`cc exit=0` 이다.** 경고 한 줄이 나지만 **빌드는 성공**하고, **`run exit=139` 로 죽는다.**
- ★★ **`char* p = "abc";` 는 C++11부터 ill-formed** 다 — 「낡았다」가 아니라 「**표준이 금지한다**」다.
- ★ **소스에 `setvbuf(stdout, nullptr, _IONBF, 0)` 가 있는 이유** — 죽으면서 **버퍼에 남은 stdout 이 통째로 사라지기** 때문이다.\
  그 줄이 없으면 「쓰기 전: p=abc」가 **출력에서 없어진다.**

**`-pedantic-errors` 를 붙이면 에러가 된다.**

```text
===== 소스: cnst07.cpp =====
// C++11 부터 ill-formed 인데 컴파일이 통과하는 줄
#include <cstdio>

int main() {
    std::setvbuf(stdout, nullptr, _IONBF, 0);   // 죽어도 출력이 안 사라지게
    char* p = "abc";                            // ★ 여기
    std::printf("쓰기 전: p=%s\n", p);
    p[0] = 'X';                                 // ★ 읽기 전용 구역에 쓴다 — UB
    std::printf("쓴 뒤  : p=%s\n", p);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic-errors cnst07.cpp -o ex (cc exit=1) =====
cnst07.cpp: In function ‘int main()’:
cnst07.cpp:6:15: error: ISO C++ forbids converting a string constant to ‘char*’ [-Wwrite-strings]
    6 |     char* p = "abc";                            // ★ 여기
      |               ^~~~~
```

- ★★★ **`-pedantic` 으로는 경고, `-pedantic-errors` 라야 에러**다. `cc exit` 이 0 → 1 로 바뀐다.
- ★★ **「`-std=c++20` 으로 돌렸다」가 「C++20 으로 검증했다」가 아니다**는 것이 이 한 쌍이다.

**clang 도 같은 모양이다.**

```text
===== 소스: cnst07.cpp =====
// C++11 부터 ill-formed 인데 컴파일이 통과하는 줄
#include <cstdio>

int main() {
    std::setvbuf(stdout, nullptr, _IONBF, 0);   // 죽어도 출력이 안 사라지게
    char* p = "abc";                            // ★ 여기
    std::printf("쓰기 전: p=%s\n", p);
    p[0] = 'X';                                 // ★ 읽기 전용 구역에 쓴다 — UB
    std::printf("쓴 뒤  : p=%s\n", p);
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic cnst07.cpp -o ex 2>&1 | grep -E 'warning:|generated' (cc exit=0) =====
cnst07.cpp:6:15: warning: ISO C++11 does not allow conversion from string literal to 'char *' [-Wwritable-strings]
1 warning generated.
```

- ★ **경고 이름만 다르다** — g++ 는 `-Wwrite-strings`, clang 은 `-Wwritable-strings`.
- ★★ **둘 다 `cc exit=0`** 이다 — 컴파일러를 바꿔도 안 잡힌다.

### (11) 다섯 층 — 무엇이 표준이고 무엇이 도구인가

★★ **이 주제도 「표준」 칸이 두껍다.** `const` 의 규칙은 전부 표준이 정하고,\
**구현이 갈리는 곳은 진단 문구와 심볼 표기뿐**이다. 대신 **UB 칸이 08 과 달리 비어 있지 않다** — 둘이나 있다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | **`const` 멤버 함수가 멤버를 못 고치는 것** · **`const` 객체로 비-const 멤버를 못 부르는 것** · **`const` 오버로드 선택**((2)) · **`mutable` 이 예외인 것**((3)) · **`const T*` → `T*` 암묵 변환이 없는 것** · **네임스페이스 스코프 `const` 가 내부 링크인 것**((7)) · **`constexpr` 가 상수식을 요구하는 것**((8)) | g++·clang **에러 7개 전부 일치** · `nm` · 실행 로그 | ★★ **`const` 가 포인터 멤버 너머를 안 막는 것**((4)) — **막는 게 아니라 원래 범위 밖**이다 |
| **조건부 표준** | 표준판이 있을 때만 | ★★ **`char*` ← 문자열 리터럴이 C++11부터 ill-formed**((10)) · `constexpr` 는 C++11부터 · `inline` 변수는 C++17부터(목록의 **25번 주제**) | `-pedantic` 대 `-pedantic-errors` 두 판 | ★★★ **`-std=c++20` 만으로는 안 잡힌다** — `-pedantic-errors` 라야 `cc exit=1` |
| **구현 정의** | 문서화 의무가 있다 | 진단 문구 · **경고 이름**(`-Wwrite-strings` 대 `-Wwritable-strings`) · `nm` 의 **심볼 종류 문자**(ELF·binutils 2.42) · `const` 객체를 **어느 구역에 두는지** | 두 컴파일러 + `nm` 대조 | — |
| **미명시** | 몇 가지 중 하나 | ★ **같은 문자열 리터럴이 합쳐지는지**(정본은 목록의 **08번 주제**) · ★ **문자열 리터럴이 쓰기 금지 구역에 놓이는지** — (10)에서 **실제로 그랬지만** 표준이 정한 것은 「**수정이 UB**」까지다 | (10)의 `run exit=139` | ★★ **「죽었다」가 「표준이 죽으라고 했다」가 아니다** — 죽는 것은 **이 구현의 결과**다 |
| **UB** | 아무 일이나 | ★★★ **원래 `const` 인 객체를 `const_cast` 로 고치기**((6)) · ★★ **문자열 리터럴 수정**((10)) | `-O0`·`-O2`·clang·UBSan **네 판** / `run exit=139` | ★★★ **UBSan 이 (6)을 한 줄도 안 낸다**(`run exit=0`) · **컴파일러는 [A]와 [B]를 구별해 주지 않는다**((1)) |

**「도구가 못 보는 것」을 층마다 — 전용 표**

| 사실 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | UBSan | 비고 |
|---|---|---|---|---|
| `const` 가 막는 일곱((9)) | **에러 7** | **에러 7** | — | 판정이 같고 문구만 다르다 |
| `mutable` 이 `const` 객체를 바꾸는 것((3)) | ★ **0건** | (던지지 않았다) | — | ★ 막을 이유가 없다 — **선언에 적혀 있다** |
| ★★ **포인터 멤버로 밖을 고치는 것**((4)) | ★★★ **0건** | (던지지 않았다) | — | ★★★ **선언에 아무 표시가 없다** — 이 주제의 진짜 구멍 |
| ★★ **`const` 멤버가 `int&` 를 내주는 것**((4)) | ★★★ **0건** | (던지지 않았다) | — | 〃 |
| ★★★ **`const_cast` 로 진짜 `const` 고치기**((6)) | ★★ **0건 · `cc exit=0`** | ★★ **0건** | ★★★ **0줄 · `run exit=0`** | ★★★ **네 판 어디에도 안 걸린다** |
| ★★★ **`char* p = "abc";`**((10)) | ★★ **경고 1 · `cc exit=0`** | ★★ **경고 1 · `cc exit=0`** | — | ★★★ **`-pedantic-errors` 라야 `cc exit=1`** |
| 두 TU 의 `limit` 가 다른 객체인 것((7)) | — | — | — | ★ **링커가 아무 말도 안 한다** — `nm` 으로만 보인다 |

- ★★★ **이 주제에서 조용한 자리는 넷이고, 셋이 「`const` 가 원래 안 막는 것」이다.**\
  (4)의 포인터 멤버 둘과 (6)의 `const_cast` — **경고 0건 · 에러 0건 · sanitizer 0줄.**
- ★★★ **그래서 `const` 는 「검사」가 아니라 「계약」이다** — **지키는 것은 사람**이고, 컴파일러는 **그 창으로 쓰는 것만** 막는다.

## 문법 — 형태와 규칙

### 형태

```cpp
/* cnst01.cpp */
// const 멤버 함수와 const 오버로드 — 객체의 const 가 어느 함수를 고르나
#include <cstdio>

struct Buf {
    int a[3]{1, 2, 3};

    int&       at(int i)       { std::puts("    at()       비-const 판"); return a[i]; }
    const int& at(int i) const { std::puts("    at() const const 판");    return a[i]; }

    int sum() const { return a[0] + a[1] + a[2]; }
    void bump()     { ++a[0]; }
};

int main() {
    Buf b;
    const Buf& cb = b;

    std::puts("[1] b.at(0) = 9;        객체가 비-const");
    b.at(0) = 9;
    std::puts("[2] cb.at(0) 을 읽는다   객체가 const");
    std::printf("    값 %d\n", cb.at(0));
    std::puts("[3] const 객체로도 부를 수 있는 것");
    std::printf("    cb.sum() = %d\n", cb.sum());
    std::printf("    b.sum()  = %d   (비-const 객체도 const 멤버를 부른다)\n", b.sum());
    b.bump();
    std::printf("    b.bump() 뒤 sum = %d\n", b.sum());
}
```

```cpp
/* cnst03.cpp */
// 비트단위 const 와 논리적 const — 포인터 멤버가 뚫는 구멍
#include <cstdio>

struct Holder {
    int  own = 1;        // 내 것
    int* p;              // 남의 것을 가리킨다

    explicit Holder(int* q) : p(q) {}

    void poke() const { *p = 99; }        // 된다 — p 가 const 지 *p 는 아니다
    int& leak() const { return *p; }      // const 멤버가 쓰기 가능한 참조를 내준다
    int  read() const { return own; }
};

int main() {
    int outside = 1;
    const Holder h(&outside);

    std::printf("전   : outside=%d h.own=%d\n", outside, h.own);
    h.poke();
    std::printf("poke : outside=%d   (h 는 const 인데 밖이 바뀌었다)\n", outside);
    h.leak() = 7;
    std::printf("leak : outside=%d   (const 멤버가 돌려준 참조로 썼다)\n", outside);
    std::printf("own  : %d           (이쪽은 정말 못 바꾼다)\n", h.read());
}
```

- **멤버 함수** — `int sum() const;` 는 **`this` 가 `const S*`** 라는 뜻이다.
- **오버로드** — `at(int)` 와 `at(int) const` 는 **다른 함수**다. 반환 타입도 같이 가른다((2)).
- **`mutable`** — 비정적 데이터 멤버에만 붙는다. **참조 멤버에는 못 붙는다.**
- **매개변수** — `const T&` 가 기본값이다((5)). 값 매개변수의 `const` 는 **정의에만** 쓴다.
- **포인터 두 자리** — `const int* p`(가리키는 것이 const) 대 `int* const p`(포인터가 const).\
  읽는 순서의 정본은 C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **31번**이다.
- **링크** — 네임스페이스 스코프 `const` 는 내부 링크. 공유하려면 **`extern` 을 붙여 정의**한다((7)).

### 금지 사례 — 던져서 받은 일곱

```cpp
/* cnst08.cpp */
// const 가 막는 일곱 — 전부 에러다
int runtime();

struct S {
    int m = 0;
    int bad() const { m = 1; return m; }   // (1) const 멤버가 멤버를 고친다
    void mut()      { ++m; }
};

int main() {
    const int x;                            // (2) 초기화 없는 const
    const S s;
    s.mut();                                // (3) const 객체로 비-const 멤버 호출
    int* p = &s.m;                          // (4) const 멤버의 주소를 int* 로
    constexpr int d = runtime();            // (5) constexpr 는 런타임 값을 못 받는다

    int i = 0, j = 0;
    int* const cp = &i;
    cp = &j;                                // (6) const 포인터를 다시 겨눈다
    const int* pc = &i;
    *pc = 1;                                // (7) 포인터-투-const 로 쓴다
    (void)x; (void)p; (void)d; (void)pc;
}
```

일곱 줄이 **전부 에러**다((9)). 같은 일곱을 clang 으로도 던졌고 **개수가 같았다.**

### 고를 것을 손으로 돌리는 순서

```text
   ① 이 멤버 함수가 객체의 「뜻」을 바꾸나?
        아니오 ──> const 를 붙인다.  캐시가 필요하면 그 멤버만 mutable ((3))
        예     ──> 안 붙인다

   ② 이 함수가 인자를 고치나?
        아니오 ──> const T&  (또는 값 — 목록의 11번 주제)
        예     ──> T&

   ③ 멤버에 포인터·핸들이 있나?
        예     ──> ★ const 가 그 너머를 안 막는다 ((4))
                    const 멤버는 const T& 를 돌려주게 하고,
                    안 고칠 것이면 멤버 자체를 const T* 로 든다

   ④ const 를 떼야 하나?
        ──> 원래 객체가 const 인가를 먼저 답한다.
            const 였으면 const_cast 는 UB ((6)) — API 를 고치거나 복사한다
```

## 어디서 틀리나

### 1. ★★★ 「`const` 를 붙였으니 안 바뀐다」

**(4)가 반례다.** `const Holder h` 인데 `h.poke()` 한 줄로 밖이 1 → 99 로 바뀐다.\
`const` 가 지키는 것은 **그 객체의 비트**이지 **그 객체가 가리키는 곳**이 아니다.\
★ 경고도 에러도 **0건**이다.

### 2. ★★★ 「`const_cast` 는 컴파일러를 속이는 것뿐이니 안전하다」

**원래 객체가 `const` 였으면 UB 다**((6)).\
★ 이번 네 판이 전부 같은 값을 냈지만, 나온 것은 「안전하다」가 아니라 「**같은 주소가 두 값을 답한다**」였다.\
★ **UBSan 이 한 줄도 안 낸다** — 「sanitizer 가 조용하니 괜찮다」가 여기서 깨진다.

### 3. ★★ 「`const` 멤버 함수는 스레드 안전하다」

`mutable` 멤버를 고치는 `const` 멤버가 있으면 **아니다**((3)).\
★ `hits` 가 1 → 2 → 3 으로 늘었다 — **두 스레드가 동시에 부르면 경쟁이 난다.**\
표준 라이브러리는 「`const` 멤버는 스레드 안전하게 만든다」를 **자기 타입에 대해서만** 약속한다.

### 4. ★★ 「`const` 와 `constexpr` 는 같은 말이다」

**`const int c = runtime();` 이 컴파일된다**((8)). `constexpr` 는 같은 자리에서 에러다((9)의 (5)).\
★ `const` 는 「**못 고친다**」, `constexpr` 는 「**지금 안다**」 — 축이 다르다.

### 5. ★★ 「헤더에 `const int N = 10;` 을 두면 하나만 생긴다」

**번역 단위마다 하나씩 생긴다**((7)). 출력이 「B 에서 99 · A 에서 10」이었다.\
★ 값이 같으면 대개 문제가 없지만 **주소를 비교하면 조용히 틀린다.**\
★ C 에서 옮겨 온 사람은 반대로 틀린다 — **C 의 파일 스코프 `const` 는 외부 링크**다.

### 6. ★★ 「`const` 판과 비-const 판 중 하나만 쓰면 된다」

**`const` 객체는 `const` 판만 부를 수 있다**((2)·(9)의 (3)).\
★ `const` 판을 안 만들면 **`const Buf&` 를 받는 함수 전체가 그 멤버를 못 쓴다** — 전염된다.

### 7. ★★ 「`const` 멤버 함수가 돌려준 것은 안전하다」

**`int&` 를 돌려주면 아니다**((4)의 `leak()`).\
★ 반환 타입에 `const` 를 붙이는 것까지가 계약이다.

### 8. ★ 「`char* p = "abc";` 는 낡은 코드일 뿐이다」

**C++11부터 ill-formed 다**((10)). 그런데 **`cc exit=0`** 이라 빌드가 통과하고,\
쓰는 순간 **`run exit=139`** 로 죽는다.\
★ **`-pedantic-errors` 라야** `cc exit=1` 이 된다.

### 9. ★ 「값 매개변수에 `const` 를 붙이면 호출하는 쪽이 안심한다」

**복사본에 붙는 것이라 호출자와 무관하다**((5)).\
★ 선언에 붙여도 **시그니처가 안 바뀐다** — 오버로드도 안 갈린다.

### 10. 「`mutable` 은 쓰면 안 되는 것이다」

**캐시·호출 횟수·뮤텍스가 정당한 자리**다((3)).\
★ 문제는 `mutable` 이 아니라 **선언에 아무 표시가 없는 (4)** 쪽이다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `const` 멤버 함수가 멤버를 못 고치는 것 | **언어** | (9)의 (1) — 두 컴파일러 에러 |
| `const` 오버로드 선택 | **언어** | (2) |
| `mutable` 이 예외인 것 | **언어** | (3) |
| 네임스페이스 스코프 `const` 가 내부 링크인 것 | **언어** | (7) — `nm` 의 `r` |
| `constexpr` 가 상수식을 요구하는 것 | **언어** | (8)·(9)의 (5) |
| 진짜 `const` 를 고치면 UB 인 것 | **언어**(UB 라고 정한 것) | (6) |
| ★ `k` 가 10 으로, `*p` 가 20 으로 보이는 것 | ★ **아무도** — UB 의 결과 | (6) 네 판 관찰 |
| ★ `const` 객체가 쓰기 금지 구역에 놓이는지 | ★ **구현** | (10)의 `run exit=139` |
| `nm` 의 `r`·`R`·`U` 표기 | **도구**(binutils 2.42) | (7) |
| 경고 이름 | **도구** | (10) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 왜 |
|---|---|---|
| 멤버 함수가 객체의 뜻을 안 바꾼다 | **`const` 를 붙인다** | 안 붙이면 `const` 사용자가 못 쓴다((2)) |
| 캐시·호출 횟수를 둬야 한다 | **그 멤버만 `mutable`** | 선언에 예외가 적힌다((3)) |
| 멤버에 포인터·핸들이 있다 | ★ **`const` 멤버는 `const T&` 를 돌려준다** | `const` 가 그 너머를 안 막는다((4)) |
| 인자를 안 고친다 | **`const T&`**(크면) · **값**(작으면) | 고르는 기준은 목록의 **11번 주제** |
| 헤더에 상수를 둔다 | **`inline constexpr`**(C++17\~) | `const` 만 쓰면 TU 마다 하나씩((7)) |
| 옛 API 가 `const` 를 안 받는다 | ★ **원래 객체가 `const` 인지 먼저 본다** | `const` 였으면 `const_cast` 는 UB((6)) |
| 컴파일 시간 값이 필요하다 | **`constexpr`** | `const` 는 런타임 값도 받는다((8)) |
| 값 매개변수 | ★ **선언에는 안 붙인다** | 호출자와 무관하다((5)) |

## 핵심 문장

- **`const` 는 「그 경로로 안 고친다」는 계약이지 「아무도 안 고친다」는 보장이 아니다.**
- **`const` 멤버 함수는 `this` 가 `const` 라는 뜻이고, 그래서 오버로드가 갈린다.**
- **`mutable` 은 선언에 적힌 예외이고, 포인터 멤버는 선언에 안 적힌 구멍이다.**
- ★★★ **원래 `const` 인 객체를 `const_cast` 로 고치면 UB 이고, 그것을 잡아 주는 도구가 없다.**
- **네임스페이스 스코프 `const` 는 내부 링크다 — 번역 단위마다 자기 것을 갖는다.**
- **`const` 는 「못 고친다」, `constexpr` 는 「지금 안다」.**

## 관련 자료

- 형제 [`03번` 캐스트 4종](../03-four-cast-operators/) — **`const_cast` 를 언제 고르나**는 거기, 여기는 **그것이 UB 가 되는 경계**((6)).
- 형제 [`07번` 참조와 포인터](../07-references-vs-pointers/) — **참조가 무엇인가**는 거기, 여기는 **`const T&` 가 적는 계약**((5)).
- C 갈래 [`14번` 포인터](../../../c/syntax/14-pointers-address-dereference-and-pointer-types/) — 포인터 자체.
- C 갈래 [`20번` 문자열 리터럴](../../../c/syntax/20-null-terminated-strings-and-string-literals/) — **리터럴의 저장 기간**은 거기, 여기는 **`char*` 변환이 ill-formed 인 것**((10)).
- C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **31번** — **`const` 위치를 읽는 순서**가 거기, 여기는 **C++ 의 인터페이스 설계 도구로서의 `const`**.
- C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **29번** — **스코프와 링크 일반**이 거기, 여기는 **`const` 가 링크를 바꾸는 한 줄**((7)).
- 목록의 **08번 주제** — **값 범주**. `const T&` 가 네 범주를 다 받는 격자가 거기다.
- 목록의 **09번 주제** — **`const` 객체를 `move` 하면 복사가 되는 것.**
- 목록의 **11번 주제** — **그래서 무엇으로 받나**(값·`const&`·`&&`·`string_view`).
- 목록의 **38번 주제** — `constexpr`·`consteval`·`constinit` 자체.
- Rust 대비 — [`rust/syntax/10 — 빌림 `&` 와 `&mut`, 별칭 규칙`](../../../rust/syntax/10-borrowing-and-aliasing-rules/).\
  **축은 「누가 지키나」다** — 아래 「더 들어가면」에 한 문단으로 뒀다.

## 용어 풀이

- **`const` 정확성(const correctness)** — 고치지 않는 것을 전부 `const` 로 적는 설계 규율.
- **cv 한정자(cv-qualifier)** — `const` 와 `volatile`. 타입에 붙어 **할 수 있는 일을 좁힌다.**
- **`const` 멤버 함수** — `this` 가 `const T*` 인 멤버 함수. `const` 객체로 부를 수 있다.
- **비트단위 const(bitwise const)** — 객체의 비트가 안 바뀌는 것. **컴파일러가 강제하는 쪽.**
- **논리적 const(logical const)** — 객체가 뜻하는 상태가 안 바뀌는 것. **사람이 지키는 쪽.**
- **`mutable`** — 그 멤버만 `const` 규칙에서 빼는 지정자.
- **`const_cast`** — cv 한정자를 떼거나 붙이는 캐스트. **떼고 쓰는 것이 UB 인지는 원래 객체가 정한다.**
- **내부 링크(internal linkage)** — 그 번역 단위 밖에서 이름으로 못 찾는 것. `nm` 에서 **소문자**로 보인다.
- **외부 링크(external linkage)** — 다른 번역 단위에서 찾을 수 있는 것. `nm` 에서 **대문자**.
- **번역 단위(translation unit)** — 전처리가 끝난 소스 하나. 링크의 단위다.
- **`constexpr`** — 컴파일 시간에 값이 정해짐을 강제하는 지정자.
- **ill-formed** — 표준이 「이 프로그램은 틀렸다」고 정한 것. ★ **컴파일이 통과하는 것과 별개**다((10)).

## 더 들어가면

### `const` 와 Rust 의 `&` — 「약속」과 「보장」

- ★★★ **C++ 의 `const` 는 「내가 이 경로로 안 고치겠다」는 약속**이고,\
  **Rust 의 `&` 는 「이 값이 빌려진 동안 아무도 안 고친다」는 보장**이다.
- 그 차이가 (4)에서 그대로 나온다 — C++ 는 `const Holder` 를 통해 밖을 고쳐도 **아무 말도 안 한다.**\
  ★ Rust 는 **같은 값에 `&` 와 `&mut` 가 동시에 있을 수 없다**는 규칙을 **컴파일러가** 검사한다.
- 두 줄 이상 쓰지 않는다 — 정본은 [`rust/syntax/10 — 빌림과 별칭 규칙`](../../../rust/syntax/10-borrowing-and-aliasing-rules/) **하나**다.\
  거기를 읽고 오면 (4)와 (6)이 「C++ 가 못 하는 것」이 아니라 「**C++ 가 안 하기로 한 것**」으로 읽힌다.

### 안 판 것

- **`volatile`** — 같은 cv 한정자인데 축이 다르다. C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **32번**이 정본이다.
- **`const` 멤버 함수의 `&`·`&&` 한정자** — `void f() const&` 같은 것. `operator=` 쪽 실측은 목록의 **08번 주제**에 있다.
- **`const` 이터레이터** — 표준 라이브러리 쪽이라 목록의 **43번 주제**로 넘긴다. `std::as_const` 도 던지지 않았다.
- **`const` 를 `constexpr` 로 올릴 때의 ABI 영향** — 재 보지 않았다.
