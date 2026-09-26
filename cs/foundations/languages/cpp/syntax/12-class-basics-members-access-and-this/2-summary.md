# cpp/syntax/12 — 클래스 기본: 멤버·접근 지정·`this` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 클래스](https://en.cppreference.com/w/cpp/language/classes) · [멤버 접근 지정자](https://en.cppreference.com/w/cpp/language/access) · [`this` 포인터](https://en.cppreference.com/w/cpp/language/this) · [정적 멤버](https://en.cppreference.com/w/cpp/language/static) · [friend 선언](https://en.cppreference.com/w/cpp/language/friend) · [GCC — 크기 0 배열 확장](https://gcc.gnu.org/onlinedocs/gcc/Zero-Length.html)
> **실행 검증** — 이 문서의 모든 출력·진단·심볼은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **GNU nm (binutils 2.42)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`cls01.cpp` \~ `cls12.cpp`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ **소스 펜스의 첫 줄 `/* cls01.cpp */` 도 캡처가 찍은 것**이라 실파일과 한 글자씩 대조된다.
> **버전** — `class`·`struct`·접근 지정자·`this`·`friend`·정적 멤버는 **C++98부터**다.\
> **`static inline` 데이터 멤버는 C++17부터**이고, 그 앞에는 클래스 밖 정의가 필수였다(목록의 **25번 주제**).\
> 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.
> ★★★ **12 → 13 → 14 → 15 는 한 사슬이다** — 여기 12 가 **클래스라는 그릇**을 만들고,\
> [13번](../13-constructors-member-init-list-and-delegating/)이 **그 그릇을 채우는 법**을,\
> [14번](../14-destructors-and-deterministic-destruction/)이 **언제 비워지는가**를,\
> [15번](../15-raii-resources-as-types/)이 **그 시점을 자원 관리에 쓰는 법**을 답한다.
> **경계** — 「캡슐화·정보 은닉이 왜 좋은가」는 [`foundations/oop-basics/`](../../../../oop-basics/)가 정본이다.\
> 여기서는 **C++ 문법이 그것을 어떻게 강제하나**만 쓴다.\
> 「`const` 멤버 함수를 설계에 쓰는 법」은 형제 [`10번`](../10-const-correctness/), 「참조와 포인터」는 형제 [`07번`](../07-references-vs-pointers/),\
> 「구조체 레이아웃·패딩」은 C 갈래 [`22-struct-padding-and-alignment/`](../../../c/syntax/22-struct-padding-and-alignment/)가 정본이다.\
> 「상속·가상 함수」는 목록의 **19번 주제**, 「정적 멤버와 `inline` 변수」는 목록의 **25번 주제**,\
> 「연산자 오버로딩」은 목록의 **22번 주제**가 정본이다.
> ★★★ **이 문서는 시간을 재지 않았다.** 근거는 **컴파일러 진단 · `sizeof` · 심볼 개수 · `static_assert`** 넷뿐이다.\
> 「몇 배 빠르다」는 문장은 **한 줄도 없다**.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 객체의 **주소값** 자체(`&a` 가 몇인지) | ★★★ **주소가 서로 다른가**(`&a != &b`)라는 **비교 결과** |
> | 두 컴파일러의 **진단 문구** | ★★★ **에러냐 경고냐 통과냐** · **진단이 가리킨 줄·열** · **`cc exit`** |
> | `nm` 이 찍는 심볼의 **주소** | ★★ **심볼 개수**(`Counter::bump()` 가 **1개**) |
> | 초기화되지 않은 멤버의 **값**(cls07 의 `lazy`) | ★★ **약속이 깨졌다는 사실**(`lazy == value_+1` 이 **0**) |
> | — | ★★★ **`sizeof` 값**(이 ABI 에서 결정적이다) · **경고 개수** |

## 한눈에 — 쉽게 말하면

**클래스는 「같이 다니는 값들」에 이름을 붙이고, 그 값에 손대는 문을 몇 개 낼지 정하는 것이다.**

사무실을 하나 떠올린다.

| 비유 | 클래스 | 무엇이 달라지나 |
|---|---|---|
| **사무실 안의 책상·서류** | 데이터 멤버 | 사무실을 하나 더 만들면 **책상도 따로 생긴다** |
| **사무실 업무 매뉴얼** | 멤버 함수 | 사무실이 백 개여도 **매뉴얼은 한 권**이다 |
| ★ **「몇 호 사무실이냐」는 쪽지** | **`this`** | 매뉴얼을 펼칠 때 **어느 사무실인지**를 같이 준다 |
| **정문 / 직원 전용문 / 금고** | `public` / `protected` / `private` | 누가 어디까지 들어오나 |
| ★ **감사관 출입증** | **`friend`** | 금고까지 열어 주되 **이름을 적어 둔 사람에게만** |
| **회사 전체가 하나 쓰는 대장** | 정적 멤버 | 사무실이 아니라 **회사에 하나**다 |

> **멤버(member)** — 클래스 안에 적힌 것. 값이면 **데이터 멤버**, 함수면 **멤버 함수**.\
> 예: `struct P { int x; int get() const; };` 에서 `x` 가 데이터 멤버, `get` 이 멤버 함수다.

> **`this`** — 멤버 함수가 **지금 어느 객체를 두고 도는지**를 가리키는 **포인터**.\
> 예: `void bump() { ++this->n; }` 은 `++n;` 과 같은 뜻이다 — `this->` 가 생략돼 있었을 뿐이다.

- ★★★ **데이터는 객체마다 따로, 코드는 하나뿐이다.** 그래서 **멤버 함수를 아무리 늘려도 `sizeof` 가 안 변한다**((2)).
- ★★★ **접근 지정은 「어디에 적혔나」가 아니라 「누가 보나」의 규칙**이다 — 클래스 안에서는 **앞뒤 순서가 자유롭다**((6)).
- ★★ **`class` 와 `struct` 의 차이는 딱 하나**, **기본 접근**이다((1)). 그 밖에는 완전히 같은 문법이다.

```text
   Counter a;   Counter b;   Counter c;        <- 객체 셋: 데이터가 셋
   +-------+    +-------+    +-------+
   | n = 3 |    | n = 1 |    | n = 0 |
   +-------+    +-------+    +-------+
       \            |            /
        \           |           /
         +----------+----------+
                    |
            Counter::bump()                    <- 코드는 하나: 심볼도 하나
            (this 로 어느 것인지 받는다)
```

## 이 주제가 답하려는 질문

1. **`class` 와 `struct` 는 무엇이 다른가** — 그리고 **그 차이가 어디서 드러나나**((1)).
2. **객체 하나에 무엇이 들어 있나** — 멤버 함수는? 정적 멤버는? 빈 클래스는?((2)(3))
3. **`this` 는 무엇이며 `const` 멤버 함수에서는 무엇이 되나**((3)(4)).
4. **접근 지정을 뚫는 문은 무엇이고, 선언 순서는 접근에 영향을 주나**((5)(6)).

## 동작 방식

### (0) 이 주제가 쓰는 네 창

「객체 안에 무엇이 있나」는 눈에 안 보인다. 창 넷을 갈라 쓴다.

```text
① 컴파일러 진단            접근 위반은 에러다 — 막혔는지 뚫렸는지    (1)(4)(5)(6)
② sizeof                   객체에 실제로 들어 있는 것                (2)
③ static_assert + decltype 타입을 출력 없이 증명한다(this 의 타입)   (3)
④ nm 의 심볼 개수          코드가 객체마다 복제되지 않는다는 것      (2)
```

- ★★★ **주력 창은 ①이다.** 이 주제의 규칙은 대부분 「**하면 에러가 난다**」의 형태이고, **에러 메시지가 곧 교재**다.
- ★★ **네 번째 창은 ④ `nm` 이다.** 「멤버 함수는 객체마다 복제되지 않는다」를 `sizeof` 는 **간접적으로만** 보인다 —\
  `sizeof` 가 안 늘었다고 해서 코드가 어디 딴 데 복제되지 않았다는 보장은 아니기 때문이다.\
  **심볼이 하나뿐인 것**을 봐야 끝난다((2)).
- ★ ③은 **출력이 아니라 컴파일 성공 자체**가 근거다 — `static_assert` 가 통과했다는 것은 타입이 그것이라는 뜻이다.
- ★★ **이 주제에 「부적용인 창」이 있다** — **런타임 sanitizer**다. 접근 지정은 **컴파일 시간에만 존재**하고\
  기계어에는 흔적이 남지 않으므로, ASan·UBSan 이 볼 것이 **원리적으로 없다**. 「재 봤더니 조용했다」가 아니라 「**잴 것이 없다**」다.

### (1) ★ `class` 와 `struct` — 다른 것은 기본 접근 하나뿐

**언제 쓰나** — 새 타입을 만들 때 둘 중 무엇으로 열지 고를 때마다.

```text
===== 소스: cls01.cpp =====
// class 와 struct 의 기본 접근을 에러로 가른다
class C { int hidden = 1; };
struct S { int open = 2; };

class CPub { public: int shown = 3; };
struct SPriv { private: int shut = 4; };

int main() {
    C c; S s; CPub cp; SPriv sp;
    int a = s.open;      // struct 의 기본은 public — 된다
    int b = cp.shown;    // class 여도 public 이라고 적으면 된다
    int x = c.hidden;    // class 의 기본은 private — 막힌다
    int y = sp.shut;     // struct 여도 private 이라고 적으면 막힌다
    return a + b + x + y;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cls01.cpp -o ex (cc exit=1) =====
cls01.cpp: In function ‘int main()’:
cls01.cpp:12:15: error: ‘int C::hidden’ is private within this context
   12 |     int x = c.hidden;    // class 의 기본은 private — 막힌다
      |               ^~~~~~
cls01.cpp:2:15: note: declared private here
    2 | class C { int hidden = 1; };
      |               ^~~~~~
cls01.cpp:13:16: error: ‘int SPriv::shut’ is private within this context
   13 |     int y = sp.shut;     // struct 여도 private 이라고 적으면 막힌다
      |                ^~~~
cls01.cpp:6:29: note: declared private here
    6 | struct SPriv { private: int shut = 4; };
      |                             ^~~~
===== clang++ -std=c++20 -Wall -Wextra -pedantic cls01.cpp -o ex (cc exit=1) =====
cls01.cpp:12:15: error: 'hidden' is a private member of 'C'
   12 |     int x = c.hidden;    // class 의 기본은 private — 막힌다
      |               ^
cls01.cpp:2:15: note: implicitly declared private here
    2 | class C { int hidden = 1; };
      |               ^
cls01.cpp:13:16: error: 'shut' is a private member of 'SPriv'
   13 |     int y = sp.shut;     // struct 여도 private 이라고 적으면 막힌다
      |                ^
cls01.cpp:6:29: note: declared private here
    6 | struct SPriv { private: int shut = 4; };
      |                             ^
2 errors generated.
```

- ★★★ **`struct` 는 기본이 `public`, `class` 는 기본이 `private`** 다. 그래서 **같은 멤버 선언이 한쪽에서만 에러**가 된다.
- ★ **그 차이는 적어 주면 사라진다** — `class` 에 `public:` 을 적으면 `struct` 와 똑같고(`CPub`),\
  `struct` 에 `private:` 을 적으면 `class` 와 똑같다(`SPriv`).
- ★★ **두 컴파일러의 문구가 다르고 뜻은 같다** — g++ 는 `is private within this context`, clang 은 `is a private member of 'C'` 다.\
  ★ clang 은 한 걸음 더 나가 **`implicitly declared private here`** 라고 적는다 — **「기본값이었다」는 것까지 말해 준다.**
- **상속의 기본 접근도 같은 규칙으로 갈린다**(`class D : B` 는 private 상속, `struct D : B` 는 public 상속) — 그 정본은 목록의 **19번 주제**다.

**비용** — 런타임 비용 0. 접근 지정은 **컴파일이 끝나면 사라진다.**

### (2) ★★★ 객체 안에 무엇이 들어 있나 — `sizeof` 로 센다

**언제 쓰나** — 「멤버 함수를 늘리면 객체가 커지나?」가 궁금할 때마다.

```text
===== 소스: cls03.cpp =====
// 객체에 무엇이 들어 있나 — sizeof 로 센다
#include <cstdio>
#include <type_traits>

struct Empty {};
struct OneInt { int a; };
struct ThreeFns { int a; void f1(); void f2(); void f3(); static void s1(); };
struct WithStatic { int a; static int shared; };
int WithStatic::shared = 0;
struct EmptyBase : Empty { int a; };
struct TwoBytes { char c; short s; };

int main() {
    std::printf("sizeof(Empty)      = %zu   (멤버가 하나도 없다)\n", sizeof(Empty));
    std::printf("sizeof(OneInt)     = %zu   (int 하나)\n", sizeof(OneInt));
    std::printf("sizeof(ThreeFns)   = %zu   (int 하나 + 멤버 함수 넷)\n", sizeof(ThreeFns));
    std::printf("sizeof(WithStatic) = %zu   (int 하나 + static int 하나)\n", sizeof(WithStatic));
    std::printf("sizeof(EmptyBase)  = %zu   (빈 클래스를 상속 + int 하나)\n", sizeof(EmptyBase));
    std::printf("sizeof(TwoBytes)   = %zu   (char + short)\n", sizeof(TwoBytes));
    Empty arr[3];
    std::printf("sizeof(Empty[3])   = %zu   (빈 객체 셋을 나란히)\n", sizeof(arr));
    std::printf("is_empty_v<Empty>  = %d\n", (int)std::is_empty_v<Empty>);
    std::printf("&arr[0] != &arr[1] = %d   (그래도 주소는 달라야 한다)\n", (int)(&arr[0] != &arr[1]));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cls03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof(Empty)      = 1   (멤버가 하나도 없다)
sizeof(OneInt)     = 4   (int 하나)
sizeof(ThreeFns)   = 4   (int 하나 + 멤버 함수 넷)
sizeof(WithStatic) = 4   (int 하나 + static int 하나)
sizeof(EmptyBase)  = 4   (빈 클래스를 상속 + int 하나)
sizeof(TwoBytes)   = 4   (char + short)
sizeof(Empty[3])   = 3   (빈 객체 셋을 나란히)
is_empty_v<Empty>  = 1
&arr[0] != &arr[1] = 1   (그래도 주소는 달라야 한다)
```

| 클래스 | `sizeof` | 읽는 법 |
|---|---|---|
| `Empty` | ★ **1** | 멤버가 없는데도 0 이 아니다 — **주소가 서로 달라야 하기 때문**이다 |
| `OneInt` | 4 | `int` 하나 |
| `ThreeFns` | ★★★ **4** | **멤버 함수 넷을 더해도 그대로다** |
| `WithStatic` | ★★ **4** | **정적 데이터 멤버는 객체 안에 없다** |
| `EmptyBase` | ★ **4** | 빈 기반 클래스는 **자리를 안 차지한다**(빈 기반 최적화) |
| `TwoBytes` | 4 | `char`+`short` 에 패딩 — 정본은 C 갈래 [`22번`](../../../c/syntax/22-struct-padding-and-alignment/) |
| `Empty[3]` | ★ **3** | 1바이트짜리가 셋 — **`is_empty_v` 는 참인데 자리는 있다** |

```text
   ThreeFns 의 객체                       프로그램 전체에 하나씩만
   +---------+                            +--------------------+
   | a: int  |  <- 4바이트가 전부다        | ThreeFns::f1 코드  |
   +---------+                            | ThreeFns::f2 코드  |
                                          | ThreeFns::f3 코드  |
   객체를 백 개 만들어도                   | ThreeFns::s1 코드  |
   늘어나는 것은 이 4바이트뿐              +--------------------+
```

그림 해설 (한 단계씩):

- ★★★ **멤버 함수는 객체 안에 없다.** 그러니 `sizeof` 가 안 변한다 — **멤버 함수를 늘려 걱정할 일이 아니다.**
- ★★ **「안 늘었다」는 「복제되지 않았다」가 아니다** — 네 번째 창으로 한 번 더 확인한다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic cls04.cpp -o ex && nm -C ex | grep -c 'Counter::bump()' | sed 's/^/Counter::bump() 심볼 수 /' (exit=0) =====
Counter::bump() 심볼 수 1
===== nm -C ex | awk '/Counter::/ { sub(/^[0-9a-f]+ /, ""); print }' (exit=0) =====
W Counter::bump()
W Counter::get() const
```

- ★★★ **`Counter::bump()` 의 심볼이 정확히 하나다.** 객체를 셋 만들어도 **코드는 한 벌**이다.
- ★ `W` 는 약한 심볼(weak)이라는 뜻이다 — 클래스 안에 정의한 멤버 함수는 **암묵적으로 `inline`** 이라 그렇다.\
  여러 번역 단위에 같은 정의가 생겨도 링커가 하나로 합친다(정본은 목록의 **55번 주제**).
- ★ **`const` 멤버 함수는 이름이 다른 심볼**이다(`Counter::get() const`) — `const` 가 **시그니처의 일부**이기 때문이다(형제 [`10번`](../10-const-correctness/)).

**비용** — 객체당 비용은 **데이터 멤버의 합 + 정렬 패딩**뿐이다. 멤버 함수는 **객체당 0바이트**다.

### (3) ★★ `this` — 멤버 함수가 받는 숨은 인자

**언제 쓰나** — 멤버 함수 안에서 이름만 적었는데 그 이름이 어떻게 찾아지나 궁금할 때.

```text
===== 소스: cls04.cpp =====
// this 는 무엇인가 — 타입은 static_assert 로, 개수는 계수기로 증명한다
#include <cstdio>
#include <type_traits>

struct Counter {
    int n = 0;
    Counter& bump() { ++n; return *this; }          // *this 를 돌려주면 이어 쓸 수 있다
    int get() const { return this->n; }             // const 멤버 함수
    void check_nonconst()       { static_assert(std::is_same_v<decltype(this), Counter*>); }
    void check_const()    const { static_assert(std::is_same_v<decltype(this), const Counter*>); }
};

int main() {
    Counter a, b, c;
    a.bump().bump().bump();                          // this 가 포인터라 이어 쓸 수 있다
    b.bump();
    std::printf("a.n=%d  b.n=%d  c.n=%d   (객체마다 데이터가 따로다)\n", a.get(), b.get(), c.get());
    std::printf("&a != &b != &c            : %d\n", (int)(&a != &b && &b != &c));

    int Counter::* pd = &Counter::n;                 // 데이터 멤버 포인터
    Counter& (Counter::* pf)() = &Counter::bump;     // 멤버 함수 포인터
    std::printf("멤버 함수 포인터가 같은가 : %d   (객체를 셋 만들어도 함수는 하나)\n",
                (int)(pf == &Counter::bump));
    std::printf("a.*pd = %d  b.*pd = %d\n", a.*pd, b.*pd);
    std::printf("sizeof(Counter)           = %zu\n", sizeof(Counter));
    std::printf("sizeof(&Counter::n)       = %zu   (데이터 멤버 포인터)\n", sizeof(pd));
    std::printf("sizeof(&Counter::bump)    = %zu   (멤버 함수 포인터)\n", sizeof(pf));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cls04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a.n=3  b.n=1  c.n=0   (객체마다 데이터가 따로다)
&a != &b != &c            : 1
멤버 함수 포인터가 같은가 : 1   (객체를 셋 만들어도 함수는 하나)
a.*pd = 3  b.*pd = 1
sizeof(Counter)           = 4
sizeof(&Counter::n)       = 8   (데이터 멤버 포인터)
sizeof(&Counter::bump)    = 16   (멤버 함수 포인터)
```

```text
   a.bump()  은 사실 이렇게 부른 것과 같다

      Counter::bump(&a)
                  ^^^
                  이 숨은 인자가 this 다

   멤버 함수 안에서            컴파일러가 읽는 것
      ++n;             ->     ++this->n;
      return *this;    ->     return *(&a);
```

그림 해설 (한 단계씩):

- ★★★ **`this` 는 포인터다.** 그래서 `*this` 로 객체 자신을 쓰고, `return *this;` 로 **호출을 이어 쓸 수 있다**(`a.bump().bump()`).
- ★★ **`const` 멤버 함수에서 `this` 는 `const Counter*` 가 된다** — 이것이 `static_assert` 로 증명된다.\
  두 `static_assert` 가 통과했다는 것은 **컴파일러가 그렇게 보고 있다**는 뜻이다.
- ★ **데이터 멤버 포인터는 8바이트, 멤버 함수 포인터는 16바이트**다 — **가상 함수 때문에** 뒤엣것이 두 칸이다(구현 정의).
- ★ **객체 셋의 주소가 서로 다르다** — 이 문서는 **주소값을 싣지 않고 비교 결과만** 싣는다(머리말의 「흔들리는 칸」).

**비용** — `this` 는 **레지스터 하나**다(x86-64 SysV 에서 첫 인자 자리). 멤버 함수 호출이 자유 함수 호출보다 비싼 것이 아니다.

### (4) ★★ `const` 멤버 함수가 막는 것 — `this` 가 `const` 라서 생기는 일

**언제 쓰나** — `const` 를 붙였더니 안 되는 것이 생겼을 때.

```text
===== 소스: cls05.cpp =====
// const 멤버 함수에서 this 가 const Counter* 라는 것을 에러로 본다
struct Counter {
    int n = 0;
    void bump_const() const { ++n; }            // const 멤버 함수가 멤버를 고친다
    void call_nonconst() const { bump(); }      // const 멤버 함수가 비-const 멤버 함수를 부른다
    void bump() { ++n; }
    Counter* escape() const { return this; }    // const Counter* 를 Counter* 로 돌려준다
};
int main() { Counter c; c.bump(); }
===== g++ -std=c++20 -Wall -Wextra -pedantic cls05.cpp -o ex (cc exit=1) =====
cls05.cpp: In member function ‘void Counter::bump_const() const’:
cls05.cpp:4:33: error: increment of member ‘Counter::n’ in read-only object
    4 |     void bump_const() const { ++n; }            // const 멤버 함수가 멤버를 고친다
      |                                 ^
cls05.cpp: In member function ‘void Counter::call_nonconst() const’:
cls05.cpp:5:38: error: passing ‘const Counter’ as ‘this’ argument discards qualifiers [-fpermissive]
    5 |     void call_nonconst() const { bump(); }      // const 멤버 함수가 비-const 멤버 함수를 부른다
      |                                  ~~~~^~
cls05.cpp:6:10: note:   in call to ‘void Counter::bump()’
    6 |     void bump() { ++n; }
      |          ^~~~
cls05.cpp: In member function ‘Counter* Counter::escape() const’:
cls05.cpp:7:38: error: invalid conversion from ‘const Counter*’ to ‘Counter*’ [-fpermissive]
    7 |     Counter* escape() const { return this; }    // const Counter* 를 Counter* 로 돌려준다
      |                                      ^~~~
      |                                      |
      |                                      const Counter*
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic cls05.cpp -o ex (cc exit=1) =====
cls05.cpp:4:31: error: cannot assign to non-static data member within const member function 'bump_const'
    4 |     void bump_const() const { ++n; }            // const 멤버 함수가 멤버를 고친다
      |                               ^ ~
cls05.cpp:4:10: note: member function 'Counter::bump_const' is declared const here
    4 |     void bump_const() const { ++n; }            // const 멤버 함수가 멤버를 고친다
      |     ~~~~~^~~~~~~~~~~~~~~~~~
cls05.cpp:5:34: error: 'this' argument to member function 'bump' has type 'const Counter', but function is not marked const
    5 |     void call_nonconst() const { bump(); }      // const 멤버 함수가 비-const 멤버 함수를 부른다
      |                                  ^~~~
cls05.cpp:6:10: note: 'bump' declared here
    6 |     void bump() { ++n; }
      |          ^
cls05.cpp:7:38: error: cannot initialize return object of type 'Counter *' with an rvalue of type 'const Counter *'
    7 |     Counter* escape() const { return this; }    // const Counter* 를 Counter* 로 돌려준다
      |                                      ^~~~
3 errors generated.
```

- ★★★ **셋이 전부 「`this` 가 `const Counter*` 이기 때문」이라는 한 가지 원인**에서 나온다.
  - `++n` 은 `++this->n` 이고 **읽기 전용 객체**를 고치려 든 것이다.
  - `bump()` 는 `Counter*` 를 요구하는데 `const Counter*` 를 넘긴 것이다 — g++ 가 **`discards qualifiers`** 라고 정확히 말한다.
  - `return this;` 는 **`const Counter*` 를 `Counter*` 로** 돌려주려 한 것이다.
- ★★ **clang 이 첫 진단에서 `cannot assign to non-static data member within const member function` 이라고 적는다** —\
  **「어디서」**(`const` 멤버 함수 안)와 **「무엇을」**(비정적 데이터 멤버)을 한 줄에 담았다.
- ★ 「그래서 `const` 를 인터페이스 설계에 어떻게 쓰나」는 형제 [`10번`](../10-const-correctness/)이 정본이다. 여기서는 **원인이 `this` 라는 것**까지만 쓴다.

**비용** — 0. `const` 멤버 함수도 기계어는 같다. 다만 **오버로드가 갈리므로 심볼은 다르다**((2)).

### (5) ★ `friend` — 접근 지정에 이름을 적어 내는 문

**언제 쓰나** — 두 타입이 한 몸처럼 움직여야 하는데 하나가 다른 쪽의 속을 봐야 할 때.

```text
===== 소스: cls06.cpp =====
// friend 는 무엇을 여나
#include <cstdio>

class Account {
public:
    explicit Account(int won) : balance_(won) {}
private:
    int balance_;
    friend void audit(const Account&);      // 이 함수 하나에만 연다
    friend class Auditor;                   // 이 클래스 전체에 연다
};

void audit(const Account& a) { std::printf("  friend 함수가 본 잔액 : %d\n", a.balance_); }

class Auditor {
public:
    static void look(const Account& a) { std::printf("  friend 클래스가 본 잔액: %d\n", a.balance_); }
};

int main() {
    Account a(1000);
    audit(a);
    Auditor::look(a);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cls06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  friend 함수가 본 잔액 : 1000
  friend 클래스가 본 잔액: 1000
```

```text
===== 소스: cls12.cpp =====
// friend 가 아니면 어디까지 막히나
class Account {
public:
    explicit Account(int won) : balance_(won) {}
private:
    int balance_;
    friend void audit(const Account&);
};

class Stranger {
public:
    static int peek(const Account& a) { return a.balance_; }   // friend 가 아니다
};

struct Derived : Account {
    using Account::Account;
    int peek() const { return balance_; }      // 파생 클래스여도 private 은 못 본다
};

void audit(const Account& a) { (void)a.balance_; }             // 이쪽은 friend 다
int also_audit(const Account& a) { return a.balance_; }        // 이름이 비슷할 뿐 friend 가 아니다

int main() { Account a(1); audit(a); return also_audit(a); }
===== g++ -std=c++20 -Wall -Wextra -pedantic cls12.cpp -o ex (cc exit=1) =====
cls12.cpp: In static member function ‘static int Stranger::peek(const Account&)’:
cls12.cpp:12:50: error: ‘int Account::balance_’ is private within this context
   12 |     static int peek(const Account& a) { return a.balance_; }   // friend 가 아니다
      |                                                  ^~~~~~~~
cls12.cpp:6:9: note: declared private here
    6 |     int balance_;
      |         ^~~~~~~~
cls12.cpp: In member function ‘int Derived::peek() const’:
cls12.cpp:17:31: error: ‘int Account::balance_’ is private within this context
   17 |     int peek() const { return balance_; }      // 파생 클래스여도 private 은 못 본다
      |                               ^~~~~~~~
cls12.cpp:6:9: note: declared private here
    6 |     int balance_;
      |         ^~~~~~~~
cls12.cpp: In function ‘int also_audit(const Account&)’:
cls12.cpp:21:45: error: ‘int Account::balance_’ is private within this context
   21 | int also_audit(const Account& a) { return a.balance_; }        // 이름이 비슷할 뿐 friend 가 아니다
      |                                             ^~~~~~~~
cls12.cpp:6:9: note: declared private here
    6 |     int balance_;
      |         ^~~~~~~~
```

- ★★★ **`friend` 는 「그 이름」에만 열린다.** `audit` 은 되고 **`also_audit` 은 이름이 비슷할 뿐 막힌다.**
- ★★ **파생 클래스도 `private` 은 못 본다**(`Derived::peek`) — 파생이 보는 것은 `protected` 까지다((6)의 표).
- ★ **`friend` 선언은 클래스 안 어디에 적어도 된다** — `private:` 구역에 적어도 **접근 지정의 영향을 받지 않는다.**\
  위 소스에서 `friend` 둘은 `private:` 아래에 있는데도 그대로 동작한다.
- ★ **`friend` 는 상속되지 않고 전이되지도 않는다** — 내 친구의 친구는 내 친구가 아니다.

**비용** — 0(컴파일 시간 규칙). 다만 **설계 비용**은 있다 — `friend` 를 늘리면 「누가 이 불변식을 깰 수 있나」의 목록이 길어진다.

### (6) ★★ 선언 순서 — 이름 찾기는 자유로운데 값은 아니다

**언제 쓰나** — 멤버 함수가 아래에서 선언할 멤버를 써도 되나 헷갈릴 때.

```text
===== 소스: cls07.cpp =====
// 클래스 안에서 선언 순서가 어디까지 자유로운가 — 이름 찾기는 자유롭다
#include <cstdio>

class Later {
public:
    int twice() const { return value_ * 2; }   // 본문이 아래에서 선언할 멤버를 쓴다
    int plus() const { return value_ + helper(); }
    int lazy = value_ + 1;                     // 기본 멤버 초기자도 아래 이름을 찾는다
    class Inner { public: int k = 7; };        // 중첩 클래스
    Inner make() const { return Inner{}; }
    int value() const { return value_; }
private:
    int helper() const { return 3; }           // 위에서 부른 함수를 여기서 선언한다
    int value_ = 10;                           // 위에서 쓴 멤버를 여기서 선언한다
};

int main() {
    Later l;
    std::printf("  twice()  = %d\n", l.twice());
    std::printf("  plus()   = %d\n", l.plus());
    std::printf("  Inner.k  = %d\n", l.make().k);
    std::printf("  value()  = %d\n", l.value());
    std::printf("  lazy 가 value_+1 인가 : %d\n", (int)(l.lazy == l.value() + 1));
    std::printf("  (lazy 의 값 자체는 싣지 않는다 — 13번이 그 이유를 답한다)\n");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cls07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  twice()  = 20
  plus()   = 13
  Inner.k  = 7
  value()  = 10
  lazy 가 value_+1 인가 : 0
  (lazy 의 값 자체는 싣지 않는다 — 13번이 그 이유를 답한다)
```

- ★★★ **클래스 안의 멤버 함수 본문은 「클래스 전체를 다 읽은 뒤」 컴파일된다**(완전 클래스 문맥).\
  그래서 `twice()` 가 **아래에서 선언할 `value_`** 를 쓸 수 있다. **접근 지정도 마찬가지**로 앞뒤를 가리지 않는다.
- ★★★ **그런데 `lazy` 는 값이 없다.** `lazy == value_ + 1` 이 **0** 이다.\
  **이름은 찾아졌는데 그 시점에 `value_` 가 아직 초기화되지 않은 것**이다 —\
  멤버는 **선언 순서로 초기화**되고 `lazy` 가 `value_` 보다 먼저 선언돼 있기 때문이다.\
  ★ **그 규칙의 정본은** [13번](../13-constructors-member-init-list-and-delegating/)이다. 여기서는 「**이름 찾기와 초기화 순서는 다른 규칙**」이라는 것만 못 박는다.
- ★★ **g++ 는 이것을 경고하지 않고 clang 은 경고한다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic cls07.cpp -o ex (cc exit=0) =====
cls07.cpp:8:16: warning: field 'value_' is uninitialized when used here [-Wuninitialized]
    8 |     int lazy = value_ + 1;                     // 기본 멤버 초기자도 아래 이름을 찾는다
      |                ^
cls07.cpp:18:11: note: in implicit default constructor for 'Later' first required here
   18 |     Later l;
      |           ^
cls07.cpp:4:7: note: during field initialization in the implicit default constructor
    4 | class Later {
      |       ^
1 warning generated.
```

- ★★ **같은 「나중 선언」인데 이쪽은 막힌다.**

```text
===== 소스: cls08.cpp =====
// 같은 「나중 선언」인데 한쪽만 막힌다
#include <cstdio>
class Later {
public:
    Alias twice() const { return value_; }     // 반환 타입 — 그 자리에서 이미 알아야 한다
    int lazy = value_;                         // 기본 멤버 초기자 — 이쪽은 어떤가
private:
    using Alias = int;
    int value_ = 10;
};
int main() { Later l; std::printf("%d\n", l.lazy); }
===== g++ -std=c++20 -Wall -Wextra -pedantic cls08.cpp -o ex (cc exit=1) =====
cls08.cpp:5:5: error: ‘Alias’ does not name a type
    5 |     Alias twice() const { return value_; }     // 반환 타입 — 그 자리에서 이미 알아야 한다
      |     ^~~~~
```

- ★★★ **선언 자체에 쓰이는 이름**(반환 타입·매개변수 타입)은 **그 자리에서 이미 알려져 있어야 한다.**\
  본문과 기본 멤버 초기자는 **뒤를 볼 수 있고**, 선언은 **못 본다.** 이 경계를 외우는 것이 이 절의 값이다.

```text
   class Later {
       int twice() const { return value_; }    <- 본문: 뒤를 본다 (완전 클래스 문맥)
       int lazy = value_ + 1;                  <- 기본 멤버 초기자: 이름은 뒤를 본다
                                                  ★ 그런데 초기화는 선언 순서라 값이 없다
       Alias f() const;                        <- 선언: 뒤를 못 본다 -> error
   private:
       using Alias = int;
       int value_ = 10;
   };
```

**비용** — 0. 전부 컴파일 시간 규칙이다.

### (7) ★ 정적 멤버와 중첩 클래스 — 객체가 아니라 클래스에 붙는 것

**언제 쓰나** — 「객체마다가 아니라 타입 전체에 하나」가 필요할 때.

```text
===== 소스: cls09.cpp =====
// 정적 멤버와 중첩 클래스 — 선언과 정의를 갈라 쓴다
#include <cstdio>

class Pool {
public:
    class Handle {                       // 중첩 클래스
    public:
        explicit Handle(int i) : id_(i) {}
        int id() const { return id_; }
    private:
        int id_;
    };

    Pool();                              // 선언만 — 정의는 클래스 밖에
    Handle take();
    static int made();                   // 정적 멤버 함수 — this 가 없다
    static inline int born = 0;          // C++17 부터 클래스 안에서 정의까지 된다

private:
    static int count_;                   // 선언만 — 정의가 클래스 밖에 있어야 한다
    int next_;
};

int Pool::count_ = 0;                    // 정적 데이터 멤버의 정의

Pool::Pool() : next_(1) { ++born; }
Pool::Handle Pool::take() { ++count_; return Handle(next_++); }
int Pool::made() { return count_; }      // 정적 멤버 함수는 정적 멤버만 본다

int main() {
    Pool p, q;
    Pool::Handle h1 = p.take();
    Pool::Handle h2 = p.take();
    Pool::Handle h3 = q.take();
    std::printf("  h1.id=%d h2.id=%d h3.id=%d   (객체마다 next_ 가 따로다)\n",
                h1.id(), h2.id(), h3.id());
    std::printf("  Pool::made() = %d            (count_ 는 둘이 나눠 쓴다)\n", Pool::made());
    std::printf("  Pool::born   = %d            (만들어진 Pool 의 수)\n", Pool::born);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cls09.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  h1.id=1 h2.id=2 h3.id=1   (객체마다 next_ 가 따로다)
  Pool::made() = 3            (count_ 는 둘이 나눠 쓴다)
  Pool::born   = 2            (만들어진 Pool 의 수)
```

```text
===== 소스: cls10.cpp =====
// 정적 멤버 함수에 this 가 없다는 것을 에러로 본다
class Pool {
public:
    static int made() { return next_; }        // 정적 멤버 함수가 비정적 멤버를 본다
    static int addr() { return (int)(long)this; }  // 정적 멤버 함수에서 this 를 쓴다
    static int count_;
private:
    int next_ = 1;
};
int main() { return Pool::made(); }
===== g++ -std=c++20 -Wall -Wextra -pedantic cls10.cpp -o ex (cc exit=1) =====
cls10.cpp: In static member function ‘static int Pool::made()’:
cls10.cpp:4:32: error: invalid use of member ‘Pool::next_’ in static member function
    4 |     static int made() { return next_; }        // 정적 멤버 함수가 비정적 멤버를 본다
      |                                ^~~~~
cls10.cpp:8:9: note: declared here
    8 |     int next_ = 1;
      |         ^~~~~
cls10.cpp: In static member function ‘static int Pool::addr()’:
cls10.cpp:5:43: error: ‘this’ is unavailable for static member functions
    5 |     static int addr() { return (int)(long)this; }  // 정적 멤버 함수에서 this 를 쓴다
      |                                           ^~~~
```

- ★★★ **정적 멤버 함수에는 `this` 가 없다.** 그래서 **비정적 멤버를 이름만으로 못 쓴다** —\
  g++ 가 `invalid use of member ... in static member function` 과 **`'this' is unavailable for static member functions`** 로 두 줄을 갈라 말해 준다.
- ★★ **정적 데이터 멤버는 선언과 정의가 다르다.** `static int count_;` 는 **선언**이고,\
  클래스 밖의 `int Pool::count_ = 0;` 이 **정의**다. 정의를 빠뜨리면 **링커 에러**가 난다(목록의 **25번 주제**).
- ★★ **C++17 의 `static inline` 은 그 짝을 없앤다** — `static inline int born = 0;` 한 줄로 끝난다.
- ★ **중첩 클래스는 이름만 안에 있는 것**이다. `Pool::Handle` 은 **바깥 객체를 자동으로 알지 못한다** —\
  `Handle` 이 `Pool` 의 멤버를 보려면 참조를 따로 들고 있어야 한다.
- ★ 출력의 `h1.id=1 h2.id=2 h3.id=1` 이 그 대비를 그대로 보인다 — **`next_` 는 객체마다 따로**(p 와 q 가 각각 1부터),\
  **`count_` 는 하나**(3회 전부 합산)다.

**비용** — 정적 데이터 멤버는 **객체 크기에 안 들어간다**((2)의 `WithStatic`). 대신 **프로그램 수명 내내 살아 있다**([14번](../14-destructors-and-deterministic-destruction/)이 그 파괴 시점을 다룬다).

### (8) ★★ 종료 코드가 0인데 표준이 금지하는 것

**언제 쓰나** — 「컴파일됐으니 맞는 코드」라고 생각할 때마다.

```text
===== 소스: cls11.cpp =====
// 종료 코드가 0인데 표준이 금지하는 것 둘
#include <cstdio>
struct ZeroArray { int a[0]; };               // ISO C++ 가 금지하는 크기 0 배열
struct Anon { struct { int x; int y; }; };    // ISO C++ 가 금지하는 익명 struct
int main() {
    ZeroArray z; Anon a; a.x = 1; a.y = 2;
    std::printf("sizeof(ZeroArray) = %zu\n", sizeof z);
    std::printf("sizeof(Anon)      = %zu\n", sizeof a);
    std::printf("a.x + a.y         = %d   (이름 없이 바로 쓴다)\n", a.x + a.y);
}
===== g++ -std=c++20 -Wall -Wextra cls11.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof(ZeroArray) = 0
sizeof(Anon)      = 8
a.x + a.y         = 3   (이름 없이 바로 쓴다)
===== g++ -std=c++20 -Wall -Wextra -pedantic cls11.cpp -o ex (cc exit=0) =====
cls11.cpp:3:26: warning: ISO C++ forbids zero-size array ‘a’ [-Wpedantic]
    3 | struct ZeroArray { int a[0]; };               // ISO C++ 가 금지하는 크기 0 배열
      |                          ^
cls11.cpp:3:24: warning: zero-size array member ‘ZeroArray::a’ in an otherwise empty ‘struct ZeroArray’ [-Wpedantic]
    3 | struct ZeroArray { int a[0]; };               // ISO C++ 가 금지하는 크기 0 배열
      |                        ^
cls11.cpp:3:8: note: in the definition of ‘struct ZeroArray’
    3 | struct ZeroArray { int a[0]; };               // ISO C++ 가 금지하는 크기 0 배열
      |        ^~~~~~~~~
cls11.cpp:4:22: warning: ISO C++ prohibits anonymous structs [-Wpedantic]
    4 | struct Anon { struct { int x; int y; }; };    // ISO C++ 가 금지하는 익명 struct
      |                      ^
===== clang++ -std=c++20 -Wall -Wextra cls11.cpp -o ex (cc exit=0) =====
===== clang++ -std=c++20 -Wall -Wextra -pedantic cls11.cpp -o ex (cc exit=0) =====
cls11.cpp:3:26: warning: zero size arrays are an extension [-Wzero-length-array]
    3 | struct ZeroArray { int a[0]; };               // ISO C++ 가 금지하는 크기 0 배열
      |                          ^
cls11.cpp:4:15: warning: anonymous structs are a GNU extension [-Wgnu-anonymous-struct]
    4 | struct Anon { struct { int x; int y; }; };    // ISO C++ 가 금지하는 익명 struct
      |               ^
2 warnings generated.
```

```text
===== echo "cls07 나중 선언 읽기  g++   경고 $(g++ -std=c++20 -Wall -Wextra -pedantic cls07.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
cls07 나중 선언 읽기  g++   경고 0
===== echo "cls07 나중 선언 읽기  clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic cls07.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
cls07 나중 선언 읽기  clang 경고 1
===== echo "g++  -Wall -Wextra          경고 $(g++ -std=c++20 -Wall -Wextra cls11.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
g++  -Wall -Wextra          경고 0
===== echo "g++  -Wall -Wextra -pedantic 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic cls11.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
g++  -Wall -Wextra -pedantic 경고 3
===== echo "clang -Wall -Wextra          경고 $(clang++ -std=c++20 -Wall -Wextra cls11.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
clang -Wall -Wextra          경고 0
===== echo "clang -Wall -Wextra -pedantic 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic cls11.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
clang -Wall -Wextra -pedantic 경고 2
```

- ★★★ **`-Wall -Wextra` 로는 g++ 도 clang 도 진단이 0줄이고 `cc exit=0` 이다.** 그런데 **둘 다 ISO C++ 가 금지한 코드**다.\
  `-pedantic` 을 붙여야 g++ 가 3건, clang 이 2건을 말한다.
- ★★ **`sizeof(ZeroArray)` 가 0 이다.** 표준에서 **완전한 객체의 크기는 1 이상**인데((2)의 `Empty` 가 그 증거다)\
  이 확장은 **그 성질 자체를 깬다.**
- ★ **「`-std=c++20` 으로 돌렸다」는 「C++20 으로 검증했다」가 아니다** — `-std=` 는 **기본값 선택**이지 강제가 아니다.\
  이 사실은 C 갈래에서도 같은 모양으로 나왔다(C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **07번**).
- ★ 진단 이름이 컴파일러마다 다르다 — g++ 는 `-Wpedantic` 하나로, clang 은 **`-Wzero-length-array` 와 `-Wgnu-anonymous-struct` 로 갈라** 말한다.\
  ★ **clang 쪽이 「끄고 켤 단위」가 더 잘게 나뉘어 있다**는 뜻이다.

**비용** — 이 확장들을 쓰면 **다른 컴파일러에서 안 될 수 있다.** `-pedantic` 을 켜 두는 것이 그 대가를 미리 치르는 방법이다.

## 문법 — 형태와 규칙

### 형태

```cpp
/* cls14.cpp */
// 클래스 하나의 형태 — 이 파일은 그대로 컴파일된다
class Widget {
public:                             // 여기부터 public
    Widget();                       // 생성자 선언 (13번 주제)
    ~Widget();                      // 소멸자 선언 (14번 주제)
    int  get() const;               // const 멤버 함수 — this 는 const Widget*
    void set(int v);                // 비-const 멤버 함수 — this 는 Widget*
    static int made();              // 정적 멤버 함수 — this 가 없다
    class Inner { public: int k = 0; };   // 중첩 클래스 — 이름만 안에 있다

protected:                          // 파생 클래스까지 본다
    int helper() const;

private:                            // 자기 자신과 friend 만 본다
    int v_ = 0;                     // 기본 멤버 초기자 (13번 주제)
    static int count_;              // 선언 — 정의는 클래스 밖에
    static inline int born = 0;     // C++17: 여기가 정의이기도 하다

    friend void audit(const Widget&);     // 이 함수에만 연다
    friend class Auditor;                 // 이 클래스 전체에 연다
};

int Widget::count_ = 0;                          // 정적 데이터 멤버의 정의
Widget::Widget() { ++born; ++count_; }
Widget::~Widget() = default;
int  Widget::get() const { return v_; }          // const 를 여기에도 적는다
void Widget::set(int v) { v_ = v; }
int  Widget::made() { return count_; }
int  Widget::helper() const { return v_ + 1; }
void audit(const Widget& w) { (void)w.v_; }
class Auditor { public: static int look(const Widget& w) { return w.v_; } };

int main() { Widget w; w.set(3); return w.get() + Widget::made() + Auditor::look(w) - 7; }
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic cls14.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
```

### 규칙

- **`class` 와 `struct` 의 차이는 기본 접근과 기본 상속 접근 둘뿐**이다. 그 밖에는 완전히 같다.
- **접근 지정자는 다음 지정자를 만날 때까지** 이어진다. 한 클래스 안에서 **몇 번이든 되풀이해도 된다.**
- **멤버 함수 본문·기본 멤버 초기자·예외 명세는 완전 클래스 문맥**이라 **뒤에 선언할 멤버를 본다.**\
  **선언 자체(반환 타입·매개변수 타입)는 못 본다.**
- **`this` 는 비정적 멤버 함수에만 있다.** `const` 멤버 함수에서는 `const T*`, `volatile` 이면 `volatile T*` 다.
- **정적 데이터 멤버는 객체에 없다.** C++17 이전에는 **클래스 밖 정의가 필수**였다.
- **`friend` 는 접근 지정 구역의 영향을 받지 않고, 상속되지 않으며, 전이되지 않는다.**

### 금지 사례 — 다섯 줄이 각각 막힌다

```text
===== 소스: cls15.cpp =====
// 금지 사례를 한 파일에 모았다 — 몇 줄에서 막히나
class C { int hidden = 0; };
struct S { void f() const { ++n; } int n = 0; };
struct T { static int f() { return v; } int v = 0; };
struct U { static int g() { return (int)(long)this; } };
class V { Alias f() const; using Alias = int; };

int main() {
    C c; c.hidden = 1;          // private 을 밖에서
    S s; s.f();                 // const 멤버 함수가 멤버를 고친다
    return T::f() + U::g();     // 정적 멤버 함수가 비정적 멤버와 this 를
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cls15.cpp -o ex (cc exit=1) =====
cls15.cpp: In member function ‘void S::f() const’:
cls15.cpp:3:31: error: increment of member ‘S::n’ in read-only object
    3 | struct S { void f() const { ++n; } int n = 0; };
      |                               ^
cls15.cpp: In static member function ‘static int T::f()’:
cls15.cpp:4:36: error: invalid use of member ‘T::v’ in static member function
    4 | struct T { static int f() { return v; } int v = 0; };
      |                                    ^
cls15.cpp:4:45: note: declared here
    4 | struct T { static int f() { return v; } int v = 0; };
      |                                             ^
cls15.cpp: In static member function ‘static int U::g()’:
cls15.cpp:5:47: error: ‘this’ is unavailable for static member functions
    5 | struct U { static int g() { return (int)(long)this; } };
      |                                               ^~~~
cls15.cpp: At global scope:
cls15.cpp:6:11: error: ‘Alias’ does not name a type
    6 | class V { Alias f() const; using Alias = int; };
      |           ^~~~~
cls15.cpp: In function ‘int main()’:
cls15.cpp:9:12: error: ‘int C::hidden’ is private within this context
    9 |     C c; c.hidden = 1;          // private 을 밖에서
      |            ^~~~~~
cls15.cpp:2:15: note: declared private here
    2 | class C { int hidden = 0; };
      |               ^~~~~~
```

- ★ **다섯 에러가 이 주제의 규칙 다섯에 하나씩 대응한다** — 접근 지정 · `const` 멤버 함수 · 정적 멤버 함수의 비정적 멤버 ·\
  정적 멤버 함수의 `this` · 선언에 쓰인 뒤 이름.
- ★★ **에러 순서가 소스 순서와 다르다** — g++ 는 **클래스 정의를 먼저** 훑고 **`main` 을 나중에** 훑는다.\
  그래서 2번 줄의 위반이 **맨 마지막**에 보고된다. **「첫 에러부터 고친다」가 반드시 「위에서부터」는 아니다.**

## 어디서 틀리나

### 1. ★★ 「멤버 함수를 늘리면 객체가 커진다」

- ★ **틀렸다.** `ThreeFns` 는 멤버 함수를 넷 달고도 `sizeof` 가 **`OneInt` 와 같은 4**다((2)).
- **커지는 것은 가상 함수를 처음 달 때**다(vptr 한 칸) — 그 정본은 목록의 **21번 주제**다.

### 2. ★★★ 「`struct` 는 데이터, `class` 는 객체」

- ★ **문법상 그런 구분은 없다.** 갈리는 것은 **기본 접근 하나**다((1)).
- **관례로는** 불변식을 지킬 것이 없는 단순 묶음에 `struct`, 불변식을 지키는 타입에 `class` 를 쓴다 —\
  **관례이지 규칙이 아니다.**

### 3. ★★ 「`private` 이면 파생 클래스는 볼 수 있다」

- ★ **못 본다.** 파생이 보는 것은 **`protected` 까지**다((5)의 `Derived::peek`).

| 보는 쪽 | `public` | `protected` | `private` |
|---|---|---|---|
| 자기 멤버 함수 | 본다 | 본다 | 본다 |
| **파생 클래스** | 본다 | ★ **본다** | ★ **못 본다** |
| `friend` | 본다 | 본다 | ★ **본다** |
| 그 밖 | 본다 | 못 본다 | 못 본다 |

### 4. ★ 「`this` 는 참조다」

- ★ **포인터다.** 그래서 `this->n` 이고, 객체 자신을 쓰려면 `*this` 로 역참조한다((3)).
- **C++23 의 「명시적 객체 매개변수」**(`this auto&& self`)가 이 모양을 바꾸지만 이 문서의 기준은 C++20 이다.

### 5. ★★ 「클래스 안에서는 위에 선언한 것만 쓸 수 있다」

- ★ **본문과 기본 멤버 초기자는 뒤를 본다**((6)). **선언만 못 본다.**
- ★★ **그런데 「이름을 찾는 것」과 「값이 있는 것」은 다른 문제**다 — `lazy` 가 그 함정이다([13번](../13-constructors-member-init-list-and-delegating/)).

### 6. ★ 「정적 멤버 함수도 객체가 있어야 부른다」

- **`Pool::made()` 처럼 클래스 이름으로 부른다.** 객체로도 부를 수는 있지만(`p.made()`) **객체는 무시된다.**

### 7. ★★ 「컴파일됐으니 표준에 맞는 코드」

- ★ **`-Wall -Wextra` 로 진단 0줄인데 ISO C++ 위반**인 코드가 이 주제에만 둘 있었다((8)).
- **`-pedantic` 이 그 둘을 드러낸다.**

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★ **이 주제는 「표준」 칸이 압도적으로 두껍고 UB 칸이 거의 비어 있다** — 접근 지정과 `this` 는 **전부 컴파일 시간 규칙**이기 때문이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★ **본체** — `class`/`struct` 의 기본 접근 · 접근 지정 셋의 범위 · **완전 클래스 문맥**(본문·기본 멤버 초기자는 뒤를 본다) · `this` 의 타입과 `const` 멤버 함수에서 `const T*` 가 되는 것 · **정적 멤버 함수에 `this` 가 없는 것** · `friend` 가 상속·전이되지 않는 것 · **완전한 객체의 `sizeof` 가 1 이상인 것** | 진단 전문 + `cc exit` · `static_assert` 통과 · `sizeof` 출력 | ★★ **설계가 맞는지** — `friend` 를 열 개 달아도 컴파일러는 **아무 말도 하지 않는다** |
| **조건부 표준** | 특정 조건에서만 보장 | ★ **`static inline` 데이터 멤버는 C++17부터** — 그 앞 판에서는 클래스 밖 정의 필수 | `-std=c++20` 으로만 돌렸다 | ★ **이 문서는 C++14 로 안 돌려 봤다** |
| **구현 정의** | 문서화 의무가 있다 | ★★ **`sizeof` 값 전부** — `int` 4 · 패딩 · **빈 기반 최적화**(`EmptyBase` 가 4) · **멤버 포인터 크기**(데이터 8 · 함수 **16**) · 심볼 이름 맹글링 | `sizeof` 출력 · `nm -C` | ★★ **다른 ABI 에서 다르다** — 이 수치는 **x86-64 Itanium ABI** 의 것이다 |
| **미명시** | 몇 가지 중 하나 | ★ **멤버 함수가 인라인되는지** · **심볼이 약한 심볼이 되는지** | `nm` 의 `W` | ★ 최적화기가 정한다 — 이 문서는 `-O0` 만 돌렸다 |
| **UB** | 아무 일이나 | ★ **하나뿐이다** — (6)의 **초기화 전 멤버를 기본 멤버 초기자에서 읽는 것**(cls07 의 `lazy`) | 약속이 깨졌다는 비교 결과(0) + clang 경고 | ★★★ **g++ 는 `-Wall -Wextra -pedantic` 에서 경고 0건** — **clang 만 본다** |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ `-Wall -Wextra` | `+pedantic` | clang `-Wall -Wextra -pedantic` | 무엇이 잡나 |
|---|---|---|---|---|---|
| 접근 위반 | 표준 | **error** | error | **error** | 컴파일러가 막는다 |
| `const` 멤버 함수가 멤버를 고침 | 표준 | **error** | error | **error** | 컴파일러가 막는다 |
| 정적 멤버 함수의 `this` | 표준 | **error** | error | **error** | 컴파일러가 막는다 |
| 선언에서 뒤 이름 쓰기 | 표준 | **error** | error | **error** | 컴파일러가 막는다 |
| 크기 0 배열 멤버 | **표준 위반** | ★ **0건** | **2건** | 1건 | ★ **`-pedantic` 뿐** |
| 익명 struct 멤버 | **표준 위반** | ★ **0건** | 1건 | 1건 | ★ **`-pedantic` 뿐** |
| 초기화 전 멤버 읽기 | **UB** | ★★★ **0건** | ★★★ **0건** | ★ **1건** | ★★ **clang 만** |
| `friend` 를 남발한 설계 | 표준 | **0건** | **0건** | **0건** | ★★★ **아무 도구도 못 본다** |

- ★★ **이 표의 결론 세 줄**
  - **접근 규칙은 전부 컴파일러가 막아 준다** — 이 주제에서 「조용히 틀리는」 자리는 거의 없다.
  - **예외가 딱 둘이다** — **표준 위반 확장**(`-pedantic` 이 잡는다)과 **초기화 순서**(**clang 만** 잡는다).
  - **설계의 옳고 그름은 어느 도구도 안 본다.** `private` 을 전부 `public` 으로 바꿔도 **경고 0건**이다.

### ★ 진단이 0줄인 것도 블록으로 받았다

「경고가 안 났다」를 산문으로 적으면 **안 물어본 것과 물었는데 조용한 것이 구분되지 않는다.**\
그래서 이 주제는 **플래그마다 물어 개수를 찍었다**((8)의 두 번째 블록).\
**탐침 6개 중 0건이 4개 · 1건 이상이 2개** — 그 「0건」이 곧 위 표의 첫 열이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 불변식이 없는 값 묶음(좌표·설정 덩어리) | **`struct` + 전부 `public`** | 숨길 것이 없으면 숨기는 비용만 든다 |
| 불변식을 지켜야 하는 타입(잔액·핸들) | **`class` + `private` 데이터** | 손댈 문을 세어 둘 수 있다 |
| 파생 클래스에만 열어야 하는 도우미 | **`protected`** | 밖에는 닫고 아래로만 연다 |
| 두 타입이 한 몸처럼 움직인다 | **`friend`**(이름을 적어서) | 접근자를 `public` 으로 열면 **모두에게** 열린다 |
| 타입 전체가 하나 쓰는 값 | **정적 데이터 멤버**(C++17 이면 `static inline`) | 객체 크기를 안 늘린다 |
| 그 타입 안에서만 쓰는 보조 타입 | **중첩 클래스** | 이름 공간이 좁아진다 |
| 객체 상태를 안 쓰는 함수 | **정적 멤버 함수** 또는 **자유 함수** | `this` 가 없으니 계약이 좁아진다 |

- ★ **접근자(`get`/`set`)를 기계적으로 다는 것은 캡슐화가 아니다** — 그 논증의 정본은 [`foundations/oop-basics/`](../../../../oop-basics/)다.
- ★★ **`friend` 는 「public 으로 여는 것」보다 좁다.** 둘 중에 고민된다면 **`friend` 쪽이 범위가 작다.**

## 핵심 문장

- **데이터는 객체마다 따로, 코드는 프로그램에 하나뿐이다** — `sizeof` 가 안 변하고 심볼이 하나다.
- **`class` 와 `struct` 의 차이는 기본 접근 하나**다. 적어 주면 그 차이는 사라진다.
- **`this` 는 포인터이고, `const` 멤버 함수에서는 `const T*` 가 된다** — 이 주제의 에러 절반이 여기서 나온다.
- **클래스 안에서 본문과 기본 멤버 초기자는 뒤를 보고, 선언은 못 본다.**
- **이름이 찾아지는 것과 값이 있는 것은 다른 규칙이다** — 초기화 순서는 [13번](../13-constructors-member-init-list-and-delegating/)이 정본이다.
- **`-Wall -Wextra` 가 조용해도 ISO C++ 위반일 수 있다** — `-pedantic` 이 그것을 드러낸다.

## 관련 자료

- [`foundations/oop-basics/`](../../../../oop-basics/) — **캡슐화·정보 은닉이 왜 좋은가**는 거기. 여기는 **C++ 문법이 그것을 어떻게 강제하나**.
- 형제 [`07번`](../07-references-vs-pointers/) — 참조와 포인터의 차이. `this` 가 **포인터인 이유**를 거기서 읽는다.
- 형제 [`10번`](../10-const-correctness/) — `const` 멤버 함수를 설계에 쓰는 법. 여기는 **`this` 가 `const` 가 된다는 사실**까지.
- [13번](../13-constructors-member-init-list-and-delegating/) — **멤버를 채우는 법**과 **초기화 순서**. (6)의 `lazy` 가 거기서 풀린다.
- [14번](../14-destructors-and-deterministic-destruction/) — **정적 멤버가 언제 파괴되나**((7)의 뒷이야기).
- C 갈래 [`21-struct-declaration-initialization-and-designated-initializers/`](../../../c/syntax/21-struct-declaration-initialization-and-designated-initializers/) — C 의 `struct` 는 **함수를 못 담는다**. 그 대비가 이 주제의 출발점이다.
- C 갈래 [`22-struct-padding-and-alignment/`](../../../c/syntax/22-struct-padding-and-alignment/) — **패딩의 정본**. (2)의 `TwoBytes` 가 4인 이유는 거기에 있다.
- 러스트 갈래 [`16-structs-impl-and-associated-functions/`](../../../rust/syntax/16-structs-impl-and-associated-functions/) — 러스트는 **데이터(`struct`)와 코드(`impl`)를 아예 갈라 적는다.** C++ 이 한 중괄호 안에 넣은 것을 둘로 나눈 판이다.

## 용어 풀이

> **데이터 멤버(data member)** — 객체마다 하나씩 생기는 값.\
> 예: `struct P { int x; };` 의 `x` — `P a, b;` 면 `x` 가 둘이다.

> **멤버 함수(member function)** — 클래스에 속한 함수. 객체를 통해 부른다.\
> 예: `a.bump()` — 숨은 인자로 `&a` 가 `this` 에 들어간다.

> **`this`** — 지금 어느 객체를 두고 도는지 가리키는 포인터.\
> 예: `Counter& bump() { ++n; return *this; }` 에서 `*this` 가 그 객체 자신이다.

> **접근 지정자(access specifier)** — `public`·`protected`·`private`. **누가 이 멤버를 볼 수 있나**를 정한다.\
> 예: `private: int v_;` 는 클래스 자신과 `friend` 만 본다.

> **`friend` 선언** — 특정 함수나 클래스에게 `private`·`protected` 를 여는 선언.\
> 예: `friend void audit(const Account&);` — `audit` 한 함수에만 열린다.

> **정적 멤버(static member)** — 객체가 아니라 **클래스에 하나** 있는 멤버.\
> 예: `static int count_;` — 객체를 백 개 만들어도 `count_` 는 하나다.

> **중첩 클래스(nested class)** — 클래스 안에 선언한 클래스. **이름만 안에 있고** 바깥 객체를 자동으로 알지는 못한다.\
> 예: `Pool::Handle` — `Handle` 을 쓰려면 `Pool::` 을 앞에 붙인다.

> **완전 클래스 문맥(complete-class context)** — 클래스 정의를 **끝까지 읽은 뒤에** 컴파일되는 자리.\
> 예: 멤버 함수 본문 — 그래서 아래에서 선언할 멤버를 쓸 수 있다.

> **빈 기반 최적화(empty base optimization)** — 멤버가 없는 기반 클래스에 자리를 안 주는 것.\
> 예: `struct D : Empty { int a; };` 의 `sizeof` 가 8 이 아니라 **4**다.

> **맹글링(name mangling)** — 오버로드·`const`·네임스페이스를 구분하려고 컴파일러가 심볼 이름을 바꾸는 것.\
> 예: `Counter::get() const` 는 `Counter::get()` 과 **다른 심볼**이 된다.

> **이름 찾기(name lookup)** — 코드에 적힌 이름이 무엇을 가리키는지 정하는 단계.\
> 예: `value_` 가 아래에서 선언됐어도 본문에서는 찾아진다 — **찾는 것과 값이 있는 것은 다른 이야기**다.

## 더 들어가면

- **`this` 를 명시적으로 적어야 하는 자리** — 템플릿 기반 클래스의 멤버를 쓸 때 `this->base_member` 가 필요하다(의존 이름). 정본은 목록의 **35번 주제**다.
- **`friend` 를 클래스 안에 정의하는 관용구**(hidden friend) — `operator<<` 를 클래스 안에 `friend` 로 **정의**하면 ADL 로만 찾아진다. 형제 [`06번`](../06-namespaces-and-adl/)과 목록의 **22번 주제**가 만난다.
- **`[[no_unique_address]]`(C++20)** — 비어 있는 **데이터 멤버**에도 빈 기반 최적화와 같은 일을 해 준다. (2)의 `EmptyBase` 가 4인 것과 짝이 되는 기능이다.
- **명시적 객체 매개변수(C++23)** — `void f(this Self&& self)` 로 `this` 를 **보이는 인자**로 적는다. 이 문서의 기준(C++20)에서는 쓸 수 없다.
