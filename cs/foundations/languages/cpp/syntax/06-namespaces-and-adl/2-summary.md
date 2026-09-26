# cpp/syntax/06 — 네임스페이스와 ADL — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 인자 의존 탐색(ADL)](https://en.cppreference.com/w/cpp/language/adl) · [이름 없는 네임스페이스](https://en.cppreference.com/w/cpp/language/namespace) · [`using` 선언](https://en.cppreference.com/w/cpp/language/using_declaration) · [`using` 지시](https://en.cppreference.com/w/cpp/language/namespace#Using-directives) · [`std::ranges::swap`](https://en.cppreference.com/w/cpp/utility/ranges/swap) · [Itanium C++ ABI — Name mangling](https://itanium-cxx-abi.github.io/cxx-abi/abi.html#mangling)
> **실행 검증** — 이 문서의 모든 출력·진단·심볼은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **GNU nm 2.42** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`ns01.cpp` \~ `ns12.cpp`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 표준 헤더가 끼어드는 진단은 **`#include` 사슬 줄만 지우는 필터**를 배너에 적어 두었다.\
> 그러니 실린 것은 「생략한 일부」가 아니라 **그 명령의 전체 출력**이다.
> **버전** — 네임스페이스·ADL·익명 네임스페이스는 **C++98부터**. **`inline namespace` 는 C++11부터**.\
> **`std::ranges::swap` 같은 사용자 지정 지점 객체는 C++20부터**((9)).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> **경계** — 「후보 중 누가 이기나」(정확 일치 → 승격 → 변환 → 모호)의 정본은\
> 형제 [`01번`](../01-function-overloading-and-overload-resolution/)이다.\
> 여기는 그 **앞 단계** — **후보 집합이 어떻게 만들어지나**만 쓴다((1)·(5)).\
> 「번역 단위·내부 링크·ODR」은 목록의 **55번 주제**가 정본이고, C 쪽 `static` 의 정본은\
> C 갈래 [29번 「스코프와 링크(`static`·`extern`)」](../../../c/syntax/29-scope-and-linkage-static-extern/2-summary.md)이다.\
> 「`friend` 의 접근 제어 쪽 의미」는 목록의 **12번 주제**, 「연산자 오버로딩을 어디에 두나」는 목록의 **22번 주제**다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 오브젝트 파일의 **심볼 주소**(`0000000000000021` 같은 것) | ★ **심볼 이름**과 **`T`/`t` 표시**(전역 대 내부 링크) |
> | 표준 헤더의 **줄 번호**(`stl_algobase.h:257`) — 판마다 움직인다 | **진단 본문** · 내 파일의 `파일:줄:칸` |
> | 컴파일 시간 | **`cc exit` 와 `run exit`**(갈라 적었다) · 프로그램 출력 전부 |
> | — | **맹글링된 이름**(`_ZN3api2v26latestEv`) — ABI 가 고정한다 |

## 한눈에 — 쉽게 말하면

**네임스페이스는 「이름을 넣어 두는 서랍」이고, ADL 은 「인자를 보고 서랍을 하나 더 열어 보는 규칙」이다.**

| 비유 | 실체 |
|---|---|
| **서랍에 넣어 이름 충돌을 막는다** | `namespace lib { ... }` |
| **「lib 서랍의 touch」라고 또박또박 말하기** | `lib::touch(w)` — 한정 이름 |
| ★ **「touch 좀」이라고만 했는데, 건네준 물건에 `lib` 라고 적혀 있어서 그 서랍도 열어 본다** | **ADL** — 인자의 타입이 사는 네임스페이스가 **후보에 얹힌다**((1)) |
| **서랍을 통째로 쏟아 책상에 올려놓기** | `using namespace lib;` — ★ 헤더에서 하면 **남의 책상까지 어지럽힌다**((7)) |
| **필요한 물건 하나만 꺼내 놓기** | `using lib::touch;` — `using` 선언 |
| ★ **물건에 붙어 다니는 라벨** | **숨은 `friend`** — 그 타입으로만 찾아진다((3)) |

- ★★★ **ADL 은 「못 찾을 때 더 찾아보는 것」이 아니다.** 보통의 탐색과 **동시에** 일어나 **후보 집합에 얹힌다.**\
  그래서 **전역에 같은 이름이 있어도 ADL 후보가 이길 수 있다**((5)) — 그리고 **아무 경고도 안 난다.**
- ★★ **ADL 이 없으면 `std::cout << x` 가 안 된다.** `operator<<` 는 `std` 안에 있는데\
  우리는 `std::operator<<(std::cout, x)` 라고 적지 않는다.
- ★★ **ADL 은 「인자가 있어야」 돈다** — 인자가 없거나 타입이 무관하면 안 돈다((2)).
- ★ **익명 네임스페이스는 C 의 `static` 자리**다. 오브젝트 파일에서 **`t`**(내부 링크)로 나온다((6)).

```text
   한정 없이 적은 f(x) 의 후보 집합 = ① + ②

   ① 보통의 이름 탐색            블록 -> 둘러싼 네임스페이스 -> ... -> 전역
                                 ★ 「처음 찾은 스코프」에서 멈춘다 (그 위는 안 본다)
   ② 인자 의존 탐색(ADL)         인자 타입마다 "연관 네임스페이스"를 모아 거기서도 찾는다
                                  · 클래스        -> 그 클래스가 사는 네임스페이스 + 기반 클래스들
                                  · 포인터/참조   -> 가리키는 타입의 것
                                  · 템플릿 인스턴스 -> 템플릿 인자들의 것도  (vector<lib::Box> -> std + lib)
                                  · 열거형        -> 그 열거형이 사는 네임스페이스
                                  ★ 숨은 friend 는 ②로만 찾아진다

   그 다음에 오버로드 해석이 돈다  -> 정본은 형제 01번

   ADL 이 꺼지는 경우
     · 한정 이름 lib::f(x)
     · 괄호를 씌운 (f)(x)
     · 그 이름이 「함수가 아닌 것」으로 먼저 찾힌 경우 (지역 변수·클래스 멤버)
```

> **인자 의존 탐색(ADL, argument-dependent lookup)** — 한정 없이 부른 함수의 후보에\
> **인자 타입의 네임스페이스**를 더하는 규칙. 「쾨니그 탐색」이라고도 한다.

> **연관 네임스페이스(associated namespace)** — ADL 이 열어 보는 서랍들.\
> 인자 타입이 사는 네임스페이스 · 기반 클래스의 것 · 템플릿 인자의 것.

> **숨은 `friend`(hidden friend)** — 클래스 **안에 정의한** `friend` 함수.\
> 그 네임스페이스의 멤버가 **아니고**, **ADL 로만** 찾아진다((3)).

> **`using` 선언** — `using lib::touch;` — **이름 하나**를 현재 스코프로 들여온다.

> **`using` 지시** — `using namespace lib;` — 그 네임스페이스의 이름을 **전부** 보이게 한다.

> **익명 네임스페이스** — `namespace { ... }`. 그 번역 단위 안에서만 보인다(**내부 링크**).

> **`inline namespace`**(C++11) — 바깥에서 **한 겹 없는 것처럼** 보이는 네임스페이스. 버전 관리에 쓴다((6)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **한정 없이 적은 이름은 어디서 찾아지나** — 보통 탐색과 ADL을 **갈라** 설명할 수 있나((1)·(2)).
2. **ADL 이 무엇을 조용히 바꾸나** — **에러 없이 다른 함수가 불리는** 판을 만들어 보일 수 있나((5)).
3. **`using namespace` 를 헤더에 두면 안 되는 이유** — 실제로 **무엇이 깨지는지** 던져 볼 수 있나((7)).

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| **실행 출력** | ★ **어느 함수가 실제로 불렸나** — 이 주제의 답 대부분 | (1)·(3)·(4)·(5)·(9) |
| **컴파일 진단** | ADL 이 **안 도는** 자리 · 모호 · ADL 이 **꺼진** 자리 | (2)·(7)·(8) |
| ★ **오브젝트 파일의 심볼**(`nm -C` · `nm`) | ★★ **네임스페이스가 파일에 글자로 남는다** · 내부 링크(`t`) 대 전역(`T`) | (6) |
| **종료 코드** | 「빌드됐다」와 「의도대로다」를 가른다 | (5)·(7) |

★★ **세 번째 창을 왜 골랐나.** 네임스페이스는 **컴파일러 머릿속의 일**처럼 보이지만,
**링커까지 살아남는다** — `nm -C` 를 걸면 `app::exported()`·`api::v2::latest()` 가 **그대로 적혀 있다**((6)).
`inline namespace` 가 **정말로 한 겹인지**도, 익명 네임스페이스가 **정말로 내부 링크인지**도 거기서 확인된다.

★★★ **이 주제의 가장 나쁜 사고는 진단이 안 나는 쪽이다**((5)).
컴파일 통과 · 경고 0건 · 실행 정상 · **불린 함수만 다르다.** 그래서 **실행 출력을 찍어 보는 것**이 유일한 창이다.

### (1) ADL — 한정 없이 적었는데 찾아진다

**언제 쓰나** — 사실 **거의 모든 C++ 코드**가 이것에 기대고 있다(`std::cout << x` 부터).

```text
===== 소스: ns01.cpp =====
// 한정 없이 불렀는데 찾아진다 — 인자 의존 탐색(ADL)
#include <cstdio>

namespace lib {
    struct Widget { int v; };
    void touch(const Widget& w) { std::printf("lib::touch v=%d\n", w.v); }
    void reset()                { std::printf("lib::reset\n"); }
}

int main() {
    lib::Widget w{7};
    touch(w);          // ① 인자의 네임스페이스가 후보에 얹힌다
    lib::reset();      // ② 인자가 없으니 한정 이름으로만
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ns01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
lib::touch v=7
lib::reset
```

- **`touch(w)`** — `w` 의 타입이 `lib::Widget` 이므로 **`lib` 가 연관 네임스페이스**가 되어 `lib::touch` 가 후보에 든다.
- **`reset()`** — **인자가 없다.** 연관 네임스페이스가 없으니 ADL 이 아무것도 안 얹는다. `lib::` 를 붙여야 한다.
- ★★ **ADL 이 없었다면** 연산자를 쓸 수 없다. `a + b` 를 `lib::operator+(a, b)` 로 적어야 하고,\
  `std::cout << x` 도 `std::operator<<(std::cout, x)` 가 된다.

### (2) ADL 이 안 도는 자리 셋

**언제 쓰나** — 「왜 못 찾지?」를 진단으로 읽을 때.

```text
===== 소스: ns02.cpp =====
// ADL 이 도는 자리와 안 도는 자리
namespace lib {
    struct Widget { int v; };
    void reset() {}
    void touch(const Widget&) {}
}

int main() {
    lib::Widget w{1};
    touch(&w);           // ① 포인터를 넘기면 — ADL 은 도는가?
    reset();             // ② 인자가 없다 — 연관 네임스페이스가 없다
    int i = 0;
    touch(i);            // ③ 인자 타입이 무관하다
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ns02.cpp -o ex (cc exit=1) =====
ns02.cpp: In function ‘int main()’:
ns02.cpp:10:11: error: invalid initialization of reference of type ‘const lib::Widget&’ from expression of type ‘lib::Widget*’
   10 |     touch(&w);           // ① 포인터를 넘기면 — ADL 은 도는가?
      |           ^~
ns02.cpp:5:16: note: in passing argument 1 of ‘void lib::touch(const Widget&)’
    5 |     void touch(const Widget&) {}
      |                ^~~~~~~~~~~~~
ns02.cpp:11:5: error: ‘reset’ was not declared in this scope; did you mean ‘lib::reset’?
   11 |     reset();             // ② 인자가 없다 — 연관 네임스페이스가 없다
      |     ^~~~~
      |     lib::reset
ns02.cpp:4:10: note: ‘lib::reset’ declared here
    4 |     void reset() {}
      |          ^~~~~
ns02.cpp:13:5: error: ‘touch’ was not declared in this scope; did you mean ‘lib::touch’?
   13 |     touch(i);            // ③ 인자 타입이 무관하다
      |     ^~~~~
      |     lib::touch
ns02.cpp:5:10: note: ‘lib::touch’ declared here
    5 |     void touch(const Widget&) {}
      |          ^~~~~
```

| 줄 | 쓴 것 | 결과 | 왜 |
|---|---|---|---|
| ① | `touch(&w)` | ★ **「찾았는데 안 맞는다」** | ★★ **포인터도 연관을 만든다** — `lib::touch` 를 **찾아내고** 참조 바인딩에서 실패했다 |
| ② | `reset()` | **「못 찾았다」** | 인자가 없다 |
| ③ | `touch(i)` | **「못 찾았다」** | `int` 는 `lib` 와 무관하다 |

- ★★★ **①의 에러 문구가 증거다.** ``invalid initialization of reference of type `const lib::Widget&` from expression of type `lib::Widget*` `` 는\
  「**`lib::touch` 라는 후보를 이미 찾았다**」는 뜻이다. 못 찾았으면 `was not declared in this scope` 가 나왔을 것이다.\
  → **포인터 인자도 「가리키는 타입」의 네임스페이스를 연관시킨다.**
- ★ ②③은 같은 모양이다 — ``error: `X` was not declared in this scope; did you mean `lib::X`?`` +\
  ``note: `lib::X` declared here``. **g++ 가 한정 이름을 제안해 준다.**
- clang 도 같은 셋을 같은 순서로 말한다(문구는 다르다).

```text
===== 소스: ns02.cpp =====
// ADL 이 도는 자리와 안 도는 자리
namespace lib {
    struct Widget { int v; };
    void reset() {}
    void touch(const Widget&) {}
}

int main() {
    lib::Widget w{1};
    touch(&w);           // ① 포인터를 넘기면 — ADL 은 도는가?
    reset();             // ② 인자가 없다 — 연관 네임스페이스가 없다
    int i = 0;
    touch(i);            // ③ 인자 타입이 무관하다
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ns02.cpp -o ex 2>&1 | grep -E 'error:|note:|generated' (cc exit=1) =====
ns02.cpp:10:5: error: no matching function for call to 'touch'
ns02.cpp:5:10: note: candidate function not viable: no known conversion from 'lib::Widget *' to 'const Widget' for 1st argument; remove &
ns02.cpp:11:5: error: use of undeclared identifier 'reset'; did you mean 'lib::reset'?
ns02.cpp:4:10: note: 'lib::reset' declared here
ns02.cpp:13:5: error: use of undeclared identifier 'touch'; did you mean 'lib::touch'?
ns02.cpp:5:10: note: 'lib::touch' declared here
ns02.cpp:13:11: error: reference to type 'const Widget' could not bind to an lvalue of type 'int'
ns02.cpp:5:29: note: passing argument to parameter here
4 errors generated.
```

### (3) 숨은 `friend` 와 템플릿 인자의 연관

**언제 쓰나** — 연산자를 클래스에 딸려 보낼 때. **현대 C++ 의 권장 배치**다.

```text
===== 소스: ns03.cpp =====
// 숨은 friend 와 템플릿 인자의 연관
#include <cstdio>
#include <vector>

namespace lib {
    struct Box {
        int v;
        friend void poke(const Box& b) { std::printf("숨은 friend poke v=%d\n", b.v); }
    };
    void tag(const std::vector<Box>&) { std::printf("lib::tag — 원소 타입으로 lib 가 연관됐다\n"); }
}

int main() {
    lib::Box b{5};
    poke(b);                        // ① 숨은 friend — ADL 로만 찾아진다
    std::vector<lib::Box> vs{b};
    tag(vs);                        // ② std::vector<lib::Box> 의 연관 네임스페이스에 lib 가 있다
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ns03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
숨은 friend poke v=5
lib::tag — 원소 타입으로 lib 가 연관됐다
```

- **`poke`** 는 `lib::Box` **안에 정의한 `friend`** 다. **`lib` 의 멤버가 아니다** — **ADL 로만** 찾아진다.
- **`tag(vs)`** 에서 `vs` 는 `std::vector<lib::Box>` 다. **템플릿 인자의 네임스페이스도 연관**되므로\
  연관 집합이 **`std` 와 `lib` 둘**이고, 그래서 `lib::tag` 가 찾아진다.

다른 방법으로는 못 부른다.

```text
===== 소스: ns04.cpp =====
// 숨은 friend 를 다른 방법으로 부르려 하면
#include <vector>

namespace lib {
    struct Box { int v; friend void poke(const Box&) {} };
}

int main() {
    lib::Box b{5};
    (poke)(b);        // ① 괄호를 씌우면 ADL 이 꺼진다
    lib::poke(b);     // ② 한정 이름으로는 찾아지나
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ns04.cpp -o ex (cc exit=1) =====
ns04.cpp: In function ‘int main()’:
ns04.cpp:10:6: error: ‘poke’ was not declared in this scope
   10 |     (poke)(b);        // ① 괄호를 씌우면 ADL 이 꺼진다
      |      ^~~~
ns04.cpp:11:10: error: ‘poke’ is not a member of ‘lib’
   11 |     lib::poke(b);     // ② 한정 이름으로는 찾아지나
      |          ^~~~
```

- ★★ **`(poke)(b)`** — 괄호를 씌우면 **ADL 이 꺼진다.** `was not declared in this scope`.
- ★★ **`lib::poke(b)`** — ``error: `poke` is not a member of `lib` ``. **정말로 멤버가 아니다.**
- ★★★ **이것이 숨은 `friend` 의 값이다** — 이름이 **그 타입을 쓸 때만** 보인다.\
  오버로드 후보 집합이 안 부풀고, `using namespace` 로도 새어 나오지 않는다.\
  「연산자를 어디에 두나」의 설계 쪽 정본은 목록의 **22번 주제**다.

### (4) `swap` 2단계 관용구 — ADL 을 **일부러 쓰는** 법

**언제 쓰나** — 제네릭 코드에서 사용자 타입의 맞춤 구현을 쓰고 싶을 때.

```text
===== 소스: ns05.cpp =====
// swap 2단계 관용구 — using std::swap 이 무엇을 바꾸나
#include <cstdio>
#include <utility>

namespace lib {
    struct Box { int v; };
    void swap(Box& a, Box& b) { std::printf("  lib::swap 이 불렸다\n"); std::swap(a.v, b.v); }
}

template <class T> void bad (T& a, T& b) { std::swap(a, b); }
template <class T> void good(T& a, T& b) { using std::swap; swap(a, b); }

int main() {
    lib::Box p{1}, q{2};
    std::printf("bad(p, q):\n");  bad(p, q);
    std::printf("  p=%d q=%d\n", p.v, q.v);
    std::printf("good(p, q):\n"); good(p, q);
    std::printf("  p=%d q=%d\n", p.v, q.v);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ns05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
bad(p, q):
  p=2 q=1
good(p, q):
  lib::swap 이 불렸다
  p=1 q=2
```

| 쓴 것 | 불린 것 | 왜 |
|---|---|---|
| `std::swap(a, b)` | `std::swap` | **한정 이름이라 ADL 이 꺼진다** — `lib::swap` 은 후보도 아니다 |
| `using std::swap; swap(a, b);` | ★ `lib::swap` | **한정 없이 불렀으니 ADL 이 돈다** — `lib::swap` 이 얹히고, 더 잘 맞아서 이긴다 |

- ★★★ `using std::swap;` 이 바꾸는 것은 「**기본값을 후보에 넣는 것**」이다.\
  그러고 나서 **한정 없이** 부르면 ADL 후보와 **같은 자리에서 경쟁**한다.\
  사용자 타입이 있으면 그쪽이 이기고, 없으면 `std::swap` 으로 떨어진다.
- ★★ **`std::swap(a, b)` 로 적으면 안 되는 이유** — `std::` 를 붙이는 순간 **ADL 이 꺼져서**\
  사용자 맞춤 구현을 **영영 못 쓴다.** 출력의 `bad` 쪽이 아무 말 없이 값만 바꾼 것이 그 결과다.
- ★ 같은 모양이 `begin`/`end`/`size` 에도 있다.

### (5) ★★★ ADL 이 **조용히** 이기는 자리

**언제 쓰나** — 전역에 같은 이름의 함수가 있을 때. **이 주제에서 가장 조용한 사고다.**

```text
===== 소스: ns06.cpp =====
// ADL 이 조용히 이기는 자리 — 에러도 경고도 없다
#include <cstdio>

namespace lib {
    struct W { int v; };
    void handle(W&) { std::printf("lib::handle(W&)\n"); }
}
void handle(const lib::W&) { std::printf("::handle(const W&)\n"); }

int main() {
    lib::W w{1};
    handle(w);              // 비const lvalue — 어느 쪽이 이기나
    const lib::W cw{2};
    handle(cw);             // const lvalue — 이쪽은?
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ns06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
lib::handle(W&)
::handle(const W&)
```

| 호출 | 불린 것 | 왜 |
|---|---|---|
| `handle(w)`(비const lvalue) | ★ **`lib::handle(W&)`** | ADL 로 얹힌 후보가 **정확히 맞는다**(`const` 를 안 붙여도 되니 더 낫다) |
| `handle(cw)`(const lvalue) | **`::handle(const W&)`** | `lib::handle(W&)` 는 **`const` 를 못 받아** 후보에서 탈락 |

- ★★★ **경고가 0건이다.** 컴파일 통과 · 실행 정상 · **부른 함수만 다르다.**\
  「내가 쓴 전역 `handle` 이 불린다」고 믿고 있으면 **첫 줄에서 이미 틀렸다.**
- ★★ **갈리는 이유 한 문장** — 「**ADL 은 후보를 「추가」하고, 그 뒤에는 보통의 오버로드 해석이 돈다.\
  그러니 라이브러리 쪽 후보가 더 잘 맞으면 그쪽이 이긴다.**」 순위 규칙의 정본은 형제 [`01번`](../01-function-overloading-and-overload-resolution/)이다.
- ★★ **컴파일러가 잡아 줄 수 있나 — 못 잡는다.** 둘 다 **합법인 호출**이고 모호하지도 않다.\
  ★ 막는 방법은 **한정 이름으로 적는 것**(`::handle(w)`)뿐이다.
- ★ clang 도 같은 답이다.

```text
===== 소스: ns06.cpp =====
// ADL 이 조용히 이기는 자리 — 에러도 경고도 없다
#include <cstdio>

namespace lib {
    struct W { int v; };
    void handle(W&) { std::printf("lib::handle(W&)\n"); }
}
void handle(const lib::W&) { std::printf("::handle(const W&)\n"); }

int main() {
    lib::W w{1};
    handle(w);              // 비const lvalue — 어느 쪽이 이기나
    const lib::W cw{2};
    handle(cw);             // const lvalue — 이쪽은?
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ns06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
lib::handle(W&)
::handle(const W&)
```

### (6) ★ 네 번째 창 — 오브젝트 파일에 네임스페이스가 남는다

**언제 쓰나** — 「이 이름이 링커까지 어떻게 가나」를 볼 때. **`inline namespace` 의 정체도 여기서 드러난다.**

```text
===== 소스: ns09.cpp =====
// 네임스페이스가 심볼에 어떻게 남나
namespace app { void exported() {} }
namespace { void internal() {} }
static void file_static() {}

namespace api {
    inline namespace v2 { void latest() {} }
    namespace v1        { void latest() {} }
}

void use() { internal(); file_static(); api::latest(); api::v1::latest(); }
===== g++ -std=c++20 -Wall -Wextra -pedantic -c ns09.cpp -o ns09.o && nm -C ns09.o | sort -k3 (exit=0) =====
000000000000000b t (anonymous namespace)::internal()
000000000000002c T api::v1::latest()
0000000000000021 T api::v2::latest()
0000000000000000 T app::exported()
0000000000000016 t file_static()
0000000000000037 T use()
```

```text
===== 소스: ns09.cpp =====
// 네임스페이스가 심볼에 어떻게 남나
namespace app { void exported() {} }
namespace { void internal() {} }
static void file_static() {}

namespace api {
    inline namespace v2 { void latest() {} }
    namespace v1        { void latest() {} }
}

void use() { internal(); file_static(); api::latest(); api::v1::latest(); }
===== nm ns09.o | sort -k3 (exit=0) =====
0000000000000037 T _Z3usev
0000000000000016 t _ZL11file_staticv
000000000000000b t _ZN12_GLOBAL__N_18internalEv
000000000000002c T _ZN3api2v16latestEv
0000000000000021 T _ZN3api2v26latestEv
0000000000000000 T _ZN3app8exportedEv
```

| 심볼 | 표시 | 뜻 |
|---|---|---|
| `app::exported()` | **`T`**(대문자) | **전역 링크** — 다른 번역 단위에서 보인다 |
| `(anonymous namespace)::internal()` | ★ **`t`**(소문자) | ★ **내부 링크** — 이 번역 단위 밖에서 안 보인다 |
| `file_static()` | ★ **`t`** | ★ **익명 네임스페이스와 같은 표시**다 |
| `api::v1::latest()` | `T` | 한정 이름 그대로 |
| `api::v2::latest()` | `T` | ★ **`api::latest()` 라고 불렀는데 `v2` 가 붙어 있다** |

- ★★★ **`api::latest()` 를 불렀는데 심볼은 `api::v2::latest()`** 다 —\
  `inline namespace v2` 가 **이름만 투명하고 실체는 안 투명하다**는 증거다.\
  그래서 **버전을 올리면 ABI 가 갈린다**(옛 바이너리는 `v1` 심볼을 계속 찾는다).
- ★★ **익명 네임스페이스와 `static` 은 표시가 같다**(`t`). 다만 맹글링은 다르다 —\
  `_ZN12_GLOBAL__N_18internalEv` 대 `_ZL11file_staticv`.\
  ★ **C++ 에서는 익명 네임스페이스를 쓴다** — `static` 과 달리 **타입·템플릿에도 쓸 수 있기 때문**이다.
- ★ **심볼 주소는 흔들리는 칸**이다(머리말 표). 근거로 쓰는 것은 **이름과 `T`/`t` 표시**다.
- ★ C 쪽 `static`/`extern` 의 정본은 C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **30번**이다 — 아직 폴더가 없다.

### (7) `using namespace std;` 가 무는 자리

**언제 쓰나** — 「편하니까 써도 되지 않나」를 던져 볼 때.

```text
===== 소스: ns07.cpp =====
// using namespace std 가 만드는 모호 호출
#include <algorithm>
using namespace std;

template <class T> T max(T a, T b) { return a < b ? b : a; }

int main() { return max(1, 2); }
===== g++ -std=c++20 -Wall -Wextra -pedantic ns07.cpp -o ex 2>&1 | grep -vE '^( *from |In file included from )' (cc exit=1) =====
ns07.cpp: In function ‘int main()’:
ns07.cpp:7:24: error: call of overloaded ‘max(int, int)’ is ambiguous
    7 | int main() { return max(1, 2); }
      |                     ~~~^~~~~~
ns07.cpp:5:22: note: candidate: ‘T max(T, T) [with T = int]’
    5 | template <class T> T max(T a, T b) { return a < b ? b : a; }
      |                      ^~~
/usr/include/c++/13/bits/stl_algobase.h:257:5: note: candidate: ‘constexpr const _Tp& std::max(const _Tp&, const _Tp&) [with _Tp = int]’
  257 |     max(const _Tp& __a, const _Tp& __b)
      |     ^~~
```

- **`max(1, 2)`** 가 **모호**해졌다. 후보 둘 —\
  ① 내가 쓴 ``T max(T, T) [with T = int]`` · ② `std::max` (``constexpr const _Tp& std::max(const _Tp&, const _Tp&)``).
- ★★ **헤더에서 하면 더 나쁘다.** 그 헤더를 `#include` 한 **모든 번역 단위**가 같은 사고를 물려받고,\
  **사고가 난 파일에는 그 줄이 안 보인다.**
- ★ 표준 라이브러리는 **판마다 이름이 늘어난다** — 오늘 안 부딪힌다고 내일 안 부딪히는 것이 아니다.

★★ **그런데 「전역 오염」은 `using namespace` 탓만이 아니다.** 아래는 `using` 이 **한 줄도 없는** 파일이다.

```text
===== 소스: ns08.cpp =====
// 헤더가 전역에 쏟아 놓는 이름 — using namespace 는 관계가 없다
#include <cmath>

double y1 = 1.0;

int main() { return static_cast<int>(y1); }
===== g++ -std=c++20 -Wall -Wextra -pedantic ns08.cpp -o ex 2>&1 | grep -vE '^( *from |In file included from )' (cc exit=1) =====
ns08.cpp:4:8: error: ‘double y1’ redeclared as different kind of entity
    4 | double y1 = 1.0;
      |        ^~
/usr/include/x86_64-linux-gnu/bits/mathcalls.h:224:1: note: previous declaration ‘double y1(double)’
  224 | __MATHCALL (y1,, (_Mdouble_));
      | ^~~~~~~~~~
ns08.cpp: In function ‘int main()’:
ns08.cpp:6:21: error: invalid ‘static_cast’ from type ‘double(double) noexcept’ to type ‘int’
    6 | int main() { return static_cast<int>(y1); }
      |                     ^~~~~~~~~~~~~~~~~~~~
```

- ★★★ **`<cmath>` 가 전역에 `y1`(POSIX 베셀 함수)을 선언해 놓는다.**\
  ``error: `double y1` redeclared as different kind of entity`` — `using namespace std;` 와 **아무 상관이 없다.**
- ★ 그러니 두 가지를 갈라야 한다 —\
  ① **`using namespace` 가 서랍을 쏟는 것**(내가 만든 문제) ·\
  ② **C 호환 헤더가 애초에 전역에 이름을 쏟아 두는 것**(내가 못 막는 문제).\
  ②의 처방은 **내 이름을 네임스페이스에 넣는 것**뿐이다.

### (8) ADL 을 끄는 것

**언제 쓰나** — 「반드시 이 함수」를 못 박아야 할 때.

```text
===== 소스: ns11.cpp =====
// ADL 을 끄는 것 — 블록 스코프의 「함수가 아닌」 선언
#include <cstdio>

namespace lib {
    struct W { int v; };
    void render(const W&) { std::printf("lib::render\n"); }
}

void off_case() {
    int render = 0;        // 블록 스코프의 변수 선언
    lib::W w{1};
    render(w);             // 이 자리에서 ADL 은 꺼진다
    (void)render;
}

int main() { off_case(); }
===== g++ -std=c++20 -Wall -Wextra -pedantic ns11.cpp -o ex (cc exit=1) =====
ns11.cpp: In function ‘void off_case()’:
ns11.cpp:12:11: error: ‘render’ cannot be used as a function
   12 |     render(w);             // 이 자리에서 ADL 은 꺼진다
      |     ~~~~~~^~~
```

- **`int render = 0;`** 이라는 **블록 스코프의 「함수가 아닌」 선언**이 ADL 을 껐다.\
  ``error: `render` cannot be used as a function``.
- ★★ **규칙** — 한정 없는 이름의 보통 탐색이 **클래스 멤버**나 **블록 스코프의 비함수 선언**을 찾으면 **ADL 이 안 돈다.**\
  ★ 블록 스코프의 **함수 선언**은 ADL 을 끄지 **않는다**(이 문서는 비함수 판만 던졌다).
- ★ **괄호를 씌우는 것**(`(f)(x)`)도 ADL 을 끈다((3)) — 그쪽은 **일부러 끄는 방법**이다.
- ★ 실무에서 ADL 을 끄는 정석은 **한정 이름**(`lib::f(x)` · `::f(x)`)이다.

```text
===== 소스: ns11.cpp =====
// ADL 을 끄는 것 — 블록 스코프의 「함수가 아닌」 선언
#include <cstdio>

namespace lib {
    struct W { int v; };
    void render(const W&) { std::printf("lib::render\n"); }
}

void off_case() {
    int render = 0;        // 블록 스코프의 변수 선언
    lib::W w{1};
    render(w);             // 이 자리에서 ADL 은 꺼진다
    (void)render;
}

int main() { off_case(); }
===== clang++ -std=c++20 -Wall -Wextra -pedantic ns11.cpp -o ex 2>&1 | grep -E 'error:|note:|generated' (cc exit=1) =====
ns11.cpp:12:11: error: called object type 'int' is not a function or function pointer
1 error generated.
```

### (9) 이름을 좁게 들여오는 네 형태

**언제 쓰나** — 「`using namespace` 말고 뭘 쓰지?」 할 때.

```text
===== 소스: ns10.cpp =====
// 이름을 좁게 들여오는 네 가지 형태
#include <cstdio>

namespace outer {
    namespace inner { void ping() { std::printf("outer::inner::ping\n"); } }
    int level = 1;
}
namespace oi = outer::inner;          // ① 네임스페이스 별칭

using outer::level;                   // ② using 선언 — 이름 하나만

int main() {
    oi::ping();                       // ① 로 부른다
    std::printf("level = %d\n", level);
    {
        using namespace outer::inner; // ③ using 지시 — 블록 안으로 한정
        ping();
    }
    outer::inner::ping();             // ④ 한정 이름 — 언제나 확실하다
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ns10.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
outer::inner::ping
level = 1
outer::inner::ping
outer::inner::ping
```

| 형태 | 예 | 성격 |
|---|---|---|
| ① **네임스페이스 별칭** | `namespace oi = outer::inner;` | 이름을 **줄이기만** 한다. 아무것도 들여오지 않는다 |
| ② **`using` 선언** | `using outer::level;` | ★ **이름 하나**만 들여온다 |
| ③ **블록 안 `using` 지시** | `{ using namespace outer::inner; ping(); }` | ★ **그 블록에서만** 산다 |
| ④ **한정 이름** | `outer::inner::ping();` | **언제나 확실하다** |

- ★★ **③이 헤더의 `using namespace` 보다 안전한 이유** — **범위가 닫힌다.**\
  `#include` 한 남의 파일까지 따라가지 않는다.
- ★★ **④가 언제나 옳은 것은 아니다** — (4)의 `swap` 이 반례다.\
  **한정 이름은 ADL 을 끄므로**, 사용자 맞춤 구현이 있어야 하는 자리에서는 **틀린 답**이 된다.\
  ★ 그래서 판단 기준은 「한정이 좋다」가 아니라 「**이 자리에서 맞춤 구현이 불려야 하나**」다.

C++20 은 그 2단계를 **객체 안으로 넣어** 주기도 한다.

```text
===== 소스: ns12.cpp =====
// C++20 의 사용자 지정 지점 객체 — 2단계를 안에서 해 준다
#include <cstdio>
#include <concepts>

namespace lib {
    struct Box { int v; };
    void swap(Box& a, Box& b) { std::printf("  lib::swap 이 불렸다\n"); int t = a.v; a.v = b.v; b.v = t; }
}

int main() {
    lib::Box p{1}, q{2};
    std::printf("std::ranges::swap(p, q):\n");
    std::ranges::swap(p, q);
    std::printf("  p=%d q=%d\n", p.v, q.v);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ns12.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
std::ranges::swap(p, q):
  lib::swap 이 불렸다
  p=2 q=1
```

- ★ **`std::ranges::swap`** 은 **사용자 지정 지점 객체(CPO)** 다 — 한정 이름으로 적었는데도\
  **안에서 ADL 2단계를 해 준다.** 그래서 `lib::swap` 이 불렸다.
- ★ 같은 모양이 `std::ranges::begin`·`end`·`size` 에도 있다. 정본은 목록의 **45번 주제**다.

### (10) 다섯 층 — 무엇이 표준이고 무엇이 도구인가

★★ **이 주제도 「표준」 칸이 거의 전부다** — 탐색 규칙은 표준이 정한다.
구현이 갈리는 곳은 **진단 문구**와 **심볼 이름**뿐이고, **UB 는 없다.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | **ADL 이 후보를 「추가」하는 것** · **연관 네임스페이스의 목록**(클래스·포인터·템플릿 인자·기반 클래스) · **숨은 `friend` 가 ADL 로만 찾아지는 것** · **한정 이름·괄호·블록 스코프 비함수 선언이 ADL 을 끄는 것** · **익명 네임스페이스가 내부 링크인 것** · `inline namespace` 가 **이름만 투명한 것** · `using` 선언과 `using` 지시의 차이 | 두 컴파일러의 실행 출력·진단이 같은 자리 · `nm` | ★★★ **ADL 이 다른 함수를 고른 것을 아무 도구도 말해 주지 않는다**((5)) — **경고 0건** |
| **조건부 표준** | 표준판이 있을 때만 | **`inline namespace` 는 C++11부터** · **`std::ranges::swap`(CPO)은 C++20부터** | `-std=c++20` 으로 실행 확인((9)) | — |
| **구현 정의** | 문서화 의무가 있다 | **맹글링 문자열**(`_ZN3api2v26latestEv` · `_ZN12_GLOBAL__N_18internalEv`) · 진단 문구 · g++ 가 붙이는 `did you mean` 제안 · `<cmath>` 가 전역에 무엇을 쏟는가 | `nm` · 두 컴파일러 대조 | — |
| **미명시** | 몇 가지 중 하나 | **해당 없음** — 이 문서가 만든 것 중에는 없다 | — | — |
| **UB** | 아무 일이나 | ★ **해당 없음**(의도적이다) — 이 주제의 프로그램은 전부 정의된 동작만 한다 | — | — |

**「도구가 못 보는 것」을 층마다 — 전용 표**

| 사실 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | `nm` | 비고 |
|---|---|---|---|---|
| ★★★ **ADL 후보가 전역 후보를 이긴 것**((5)) | ★★ **0건 · `cc exit=0`** | ★★ **0건 · `cc exit=0`** | — | ★ **실행 출력으로만 보인다** |
| `std::swap` 을 한정으로 불러 맞춤 구현을 놓친 것((4)) | **0건** | **0건** | — | ★ 「**잘 도는 느린 코드**」로 남는다 |
| ADL 이 못 찾은 것((2)) | **에러 3 + `did you mean`** | **에러 3** | — | 판정이 같다 |
| 숨은 `friend` 를 한정 이름으로 부른 것((3)) | **에러 2** | **에러 2** | — | 〃 |
| `using namespace std` 충돌((7)) | **에러 1 + 후보 2** | — | — | 부딪힐 때만 난다 |
| 익명 네임스페이스가 내부 링크인 것((6)) | — | — | ★ **`t` 대 `T`** | ★ 소스만 봐서는 「정말 그런가」를 못 본다 |
| `inline namespace` 가 `v2` 로 남는 것((6)) | — | — | ★ **심볼에 글자로** | 〃 |

- ★★★ **이 주제의 위험은 전부 「진단이 안 나는 쪽」에 있다.** (5)와 (4)가 그 둘이고,\
  **둘 다 컴파일도 실행도 정상**이다. 막는 것은 도구가 아니라 **습관**이다 —\
  ① **전역 네임스페이스에 함수를 두지 않는다** · ② **맞춤 구현이 불려야 하는 자리에서는 한정 이름을 쓰지 않는다.**

## 문법 — 형태와 규칙

### 형태

```cpp
/* ns10.cpp */
// 이름을 좁게 들여오는 네 가지 형태
#include <cstdio>

namespace outer {
    namespace inner { void ping() { std::printf("outer::inner::ping\n"); } }
    int level = 1;
}
namespace oi = outer::inner;          // ① 네임스페이스 별칭

using outer::level;                   // ② using 선언 — 이름 하나만

int main() {
    oi::ping();                       // ① 로 부른다
    std::printf("level = %d\n", level);
    {
        using namespace outer::inner; // ③ using 지시 — 블록 안으로 한정
        ping();
    }
    outer::inner::ping();             // ④ 한정 이름 — 언제나 확실하다
}
```

규칙 불릿.

- **`namespace N { ... }`** — 이름을 서랍에 넣는다. **여러 번 열어 이어 쓸 수 있다.**
- **`N::name`** — 한정 이름. **확실하고, ADL 을 끈다.**
- **`namespace A = N::M;`** — 별칭. **아무것도 들여오지 않는다.**
- **`using N::name;`** — `using` 선언. **이름 하나**를 현재 스코프로.
- **`using namespace N;`** — `using` 지시. ★ **헤더·전역에 두지 않는다.** 블록 안이면 낫다.
- **`namespace { ... }`** — 익명 네임스페이스. **내부 링크**(C 의 `static` 자리).
- **`inline namespace V { ... }`**(C++11) — 바깥에서 한 겹 없는 것처럼 보인다. **심볼에는 남는다.**
- **ADL** — 한정 없는 함수 호출의 후보에 **인자 타입의 네임스페이스**를 더한다.
- **숨은 `friend`** — 클래스 안에 정의한 `friend`. **ADL 로만** 찾아진다.
- **2단계 관용구** — `using std::swap; swap(a, b);`. 한정으로 적으면 **맞춤 구현을 못 쓴다.**

### 금지 사례 — 던져서 받은 여섯

| 쓴 것 | 컴파일러 | 무엇이 나오나 |
|---|---|---|
| `reset()`(인자 없음, `lib` 안의 함수) | g++ | ``error: `reset` was not declared in this scope; did you mean `lib::reset`?`` |
| `touch(i)`(`int` 인자) | g++ | ``error: `touch` was not declared in this scope`` |
| `(poke)(b)`(괄호로 ADL 끄기) | g++ | ``error: `poke` was not declared in this scope`` |
| `lib::poke(b)`(숨은 friend) | g++ | ★ ``error: `poke` is not a member of `lib` `` |
| `max(1, 2)` + `using namespace std;` | g++ | ``error: call of overloaded `max(int, int)` is ambiguous`` + 후보 2 |
| `double y1 = 1.0;` + `#include <cmath>` | g++ | ★ ``error: `double y1` redeclared as different kind of entity`` |
| `int render = 0;` 뒤에 `render(w)` | g++ | ``error: `render` cannot be used as a function`` |

### 고를 것을 손으로 돌리는 순서

1. **내 이름은 전부 네임스페이스 안에** 둔다. 전역은 `main` 만.
2. **타입에 딸린 자유 함수·연산자는 숨은 `friend`** 로 그 타입 안에 둔다((3)).\
   후보 집합이 안 부풀고 ADL 로 정확히 찾아진다.
3. **헤더에 `using namespace` 를 쓰지 않는다**((7)). 필요하면 **함수 본문 안**에서.
4. **맞춤 구현이 불려야 하는 자리에서는 2단계로 부른다** — `using std::swap; swap(a, b);`((4)).\
   ★ C++20 이면 **`std::ranges::swap`** 이 그 일을 대신한다((9)).
5. **그 외에는 한정 이름**이 기본값이다 — 특히 **전역에 같은 이름이 있을 수 있는 자리**((5)).
6. **번역 단위 안에서만 쓰는 것은 익명 네임스페이스**에 넣는다((6)).

## 어디서 틀리나

### 1. ★★★ 「한정 없이 적으면 전역에서 찾는다」

**인자 타입의 네임스페이스에서도 찾는다**((1)). 그리고 그 후보가 **이길 수 있다**((5)).\
★ 경고는 **0건**이고, 컴파일도 실행도 정상이다.

### 2. ★★★ 「`std::swap(a, b)` 가 제일 안전하다」

**한정 이름은 ADL 을 끈다**((4)). 사용자 타입의 맞춤 `swap` 이 있어도 **영영 안 불린다.**\
★ 2단계(`using std::swap;` + 한정 없는 호출)나 **C++20 의 `std::ranges::swap`** 을 쓴다((9)).

### 3. ★★ 「ADL 은 못 찾았을 때만 더 찾아보는 것이다」

아니다. **보통 탐색과 나란히 후보를 만든다.** 그래서 **전역에 있는데도 다른 것이 뽑힐 수 있다**((5)).

### 4. ★★ 「`friend` 로 선언했으니 그 네임스페이스의 멤버다」

**클래스 안에 정의한 `friend` 는 멤버가 아니다**((3)). `lib::poke(b)` 가\
``error: `poke` is not a member of `lib` `` 로 막힌다. **ADL 로만** 찾아진다.

### 5. ★★ 「포인터로 넘기면 ADL 이 안 돈다」

**돈다**((2)의 ①). 에러가 「못 찾았다」가 아니라 「**찾았는데 안 맞는다**」인 것이 증거다.

### 6. ★★ 「전역이 더러워지는 건 `using namespace std;` 때문이다」

**절반만 맞다**((7)). `<cmath>` 는 `using` 이 없어도 **전역에 `y1` 을 선언한다.**\
★ 막는 방법은 **내 이름을 네임스페이스에 넣는 것**뿐이다.

### 7. ★★ 「`inline namespace` 는 그냥 이름이 투명해지는 것이다」

**심볼에는 남는다**((6)). `api::latest()` 를 불렀는데 오브젝트 파일에는 **`api::v2::latest()`** 가 적힌다 —\
그래서 **버전을 올리면 ABI 가 갈린다.**

### 8. ★ 「익명 네임스페이스와 `static` 은 다르다」

**링크 측면에서는 같다**((6)) — 둘 다 `nm` 에서 **`t`** 다.\
★ 다른 점은 **익명 네임스페이스는 타입·템플릿에도 쓸 수 있다**는 것이다.

### 9. ★ 「한정 이름으로 적는 게 언제나 옳다」

**아니다**((9)). 2번과 충돌한다 — **맞춤 구현이 불려야 하는 자리**에서는 한정이 틀린 답이다.

### 10. 「블록 안 `using namespace` 도 나쁘다」

**헤더의 그것과 다르다**((9)). **범위가 닫혀** `#include` 한 남에게 안 새어 나간다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| **ADL 이 후보를 「추가」하는** 것 | **언어** |
| **연관 네임스페이스의 목록**(클래스·포인터/참조·템플릿 인자·기반 클래스·열거형) | **언어** |
| **숨은 `friend` 가 그 네임스페이스의 멤버가 아닌** 것 | **언어** |
| **한정 이름·괄호·블록 스코프 비함수 선언이 ADL 을 끄는** 것 | **언어** |
| **익명 네임스페이스가 내부 링크**인 것 | **언어** |
| `inline namespace` 가 **이름만 투명한** 것 | **언어**(C++11부터) |
| `using` 선언과 `using` 지시의 차이 | **언어** |
| `std::ranges::swap` 이 **2단계를 대신하는** 것 | **언어**(C++20부터) |
| ★ **맹글링된 심볼 문자열** | ★ **플랫폼 ABI**(Itanium C++ ABI). 결정적이되 언어 보장은 아니다 |
| ★ **`<cmath>` 가 전역에 `y1` 을 선언하는 것** | ★ **POSIX + 이 구현.** C++ 표준은 `<cmath>` 의 이름이 `std` 에 있다고만 한다 |
| 진단 문구 · `did you mean` 제안 | **컴파일러 구현** |
| ★ 심볼 **주소** | ★ **이 컴파일 단위의 배치** — 흔들리는 칸이다 |

## 언제 쓰고 언제 안 쓰나

**네임스페이스** — **내 이름 전부.** 전역에 두는 것은 `main` 뿐이다.

**숨은 `friend`** — 타입에 딸린 **자유 함수·연산자**. ★ 현대 C++ 의 기본 배치다((3)).

**`using` 선언**(`using lib::f;`) — **이름 하나**가 필요할 때. 헤더에서도 비교적 안전하다.

**`using` 지시**(`using namespace N;`) — ★ **함수 본문 안에서만.**\
헤더·전역에서는 쓰지 않는다((7)). 예외는 **2단계 관용구의 `using std::swap;`** 인데, 그것도 **함수 안**이다.

**익명 네임스페이스** — **이 `.cpp` 안에서만 쓰는 것** 전부. `static` 보다 이쪽((6)).

**`inline namespace`** — **ABI 버전을 가를 때.** ★ 올리면 심볼이 갈린다는 것을 알고 쓴다.

**한정 이름** — 기본값. ★ 단 **맞춤 구현이 불려야 하는 자리**에서는 쓰지 않는다((4)).

## 핵심 문장

1. **ADL 은 후보를 「추가」한다** — 못 찾을 때 더 찾는 것이 아니다.
2. **그래서 전역에 같은 이름이 있어도 라이브러리 쪽이 이길 수 있고, 경고는 0건이다.**
3. **한정 이름은 ADL 을 끈다** — `std::swap(a, b)` 가 맞춤 구현을 못 쓰는 이유.
4. **숨은 `friend` 는 그 네임스페이스의 멤버가 아니다** — ADL 로만 찾아진다.
5. **`using namespace` 는 함수 안에서만** — 헤더에 두면 남의 번역 단위까지 물든다.
6. **네임스페이스는 링커까지 간다** — `nm -C` 가 `api::v2::latest()` 를 글자로 보여 준다.

## 관련 자료

- [**01번 형제**](../01-function-overloading-and-overload-resolution/) — ★ **후보 중 누가 이기나**의 정본.\
  여기는 **그 후보 집합이 어떻게 만들어지나**까지고, (5)의 결과는 거기 규칙이 낸 것이다.
- [**04번 형제**](../04-brace-initialization-narrowing-and-initializer-list/) —\
  `{}` 가 **오버로드 해석에 얹히는 또 다른 한 겹**. 같은 층위의 이야기다.
- 목록의 **12번 주제**(클래스 기본·접근 지정) — `friend` 의 **접근 제어** 쪽 의미.
- 목록의 **22번 주제**(연산자 오버로딩) — 「멤버냐 비멤버냐」를 (3)의 숨은 `friend` 로 푸는 설계.
- 목록의 **31번 주제**(함수 템플릿) — 2단계 관용구가 **템플릿 안에서** 왜 필요한지.
- 목록의 **45번 주제**(범위와 뷰) — `std::ranges::swap`·`begin`·`end` 같은 **사용자 지정 지점 객체**.
- 목록의 **55번 주제**(모듈·ODR·헤더 배치) — 「이름이 어느 번역 단위에 사는가」의 정본.\
  ★ (6)의 내부 링크가 거기 이야기의 한 조각이다.
- C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **30번**(`static`/`extern` 과 링크) —\
  익명 네임스페이스가 **대신하는** 장치. **아직 폴더가 없다.**

## 용어 풀이

> **네임스페이스(namespace)** — 이름을 담는 서랍. **여러 번 열어 이어 쓸 수 있다.**

> **한정 이름(qualified name)** — `N::f` 처럼 서랍을 밝힌 이름. ★ **ADL 을 끈다.**

> **인자 의존 탐색(ADL)** — 한정 없는 함수 호출의 후보에 **인자 타입의 네임스페이스**를 더하는 규칙.

> **연관 네임스페이스(associated namespace)** — ADL 이 열어 보는 서랍들.

> **숨은 `friend`(hidden friend)** — 클래스 안에 정의한 `friend` 함수. **ADL 로만** 찾아진다.

> **`using` 선언 / `using` 지시** — 이름 하나를 들여오기 / 서랍을 통째로 보이게 하기.

> **익명 네임스페이스** — `namespace { }`. **내부 링크**(그 번역 단위 밖에서 안 보인다).

> **`inline namespace`**(C++11) — 바깥에서 한 겹 없는 것처럼 보이는 네임스페이스. **심볼에는 남는다.**

> **맹글링(name mangling)** — 네임스페이스·타입 정보를 섞어 링커용 심볼 이름을 만드는 것.\
> `_ZN3api2v26latestEv` 가 `api::v2::latest()` 다.

> **사용자 지정 지점 객체(CPO)**(C++20) — `std::ranges::swap` 처럼 **안에서 2단계 탐색을 해 주는** 함수 객체.

## 더 들어가면

- **ADL 의 연관 네임스페이스에는 기반 클래스도 들어간다** — 파생 타입을 넘기면 **기반이 사는 서랍**도 열린다.\
  ★ **이 문서는 안 던졌다**(단일 네임스페이스만 실측했다).
- **열거형도 연관을 만든다** — `enum class` 가 사는 네임스페이스가 열린다. ★ 안 던졌다.\
  형제 [`02번`](../02-enum-class-and-scoped-enumerations/)과 이어지는 자리다.
- **`using` 선언과 오버로드** — 같은 이름을 여러 네임스페이스에서 `using` 하면 **후보가 합쳐진다.**\
  ★ 안 던졌다 — 순위 규칙의 정본이 형제 [`01번`](../01-function-overloading-and-overload-resolution/)이라 거기서 볼 일이다.
- **블록 스코프의 「함수」 선언은 ADL 을 끄지 않는다** — (8)은 **비함수 판만** 던졌다.
- **모듈(C++20)에서의 이름 탐색** — `export` 와 ADL 의 상호작용이 한 겹 더 있다.\
  g++ 13 의 모듈 지원이 제한적이라 **이 문서는 안 던졌다.** 정본은 목록의 **55번 주제**다.
- **`inline namespace` + `__attribute__((abi_tag))`** 로 ABI 를 가르는 실무 관용구 — 이 문서는 안 던졌다.
