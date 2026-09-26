# cpp/syntax/01 — 함수 오버로딩과 오버로드 해석 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — Overload resolution](https://en.cppreference.com/w/cpp/language/overload_resolution) · [cppreference — Implicit conversions](https://en.cppreference.com/w/cpp/language/implicit_conversion) · [cppreference — Unqualified name lookup](https://en.cppreference.com/w/cpp/language/unqualified_lookup) · [GCC 13 C++ Dialect Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/C_002b_002b-Dialect-Options.html)
> **실행 검증** — 이 문서의 모든 출력·에러·심볼은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex` 이고, 소스 파일 이름은 **전부 `ex.cpp`** 로 고정했다.\
> **진단의 줄 번호는 그 파일 기준**이라, 진단을 싣는 블록마다 **그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 `capture.sh` 가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.
> **버전** — 함수 오버로딩과 오버로드 해석은 **C++98부터** 있고 이 문서가 쓰는 규칙은 그때와 같다.\
> `__PRETTY_FUNCTION__` 은 **표준이 아니라 gcc·clang 확장**이다(표준의 `__func__` 는 이름만 준다 — 서명이 없다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> **경계** — 「정수 승격·통상 산술 변환」의 정본은 C 갈래의\
> [`03-integer-promotion-and-usual-arithmetic-conversions/`](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/)다.\
> 여기는 **그 승격이 오버로드 해석의 한 계단으로 쓰이는 자리**까지만 쓴다.\
> 「이름이 어느 네임스페이스에서 찾아지나(ADL)」는 [목록의 **06번 주제**](../06-namespaces-and-adl/), 「값 범주가 `T&`/`T&&` 를 가르는 것」은 [목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/),\
> 「`const` 정확성의 설계」는 [목록의 **10번 주제**](../10-const-correctness/), 「템플릿 인자 추론」은 목록의 **31번 주제**가 정본이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸** — 제출 전 재대조를 한 줄에 판정하려고 미리 갈라 둔다.
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 컴파일 시간 · 오브젝트 파일의 타임스탬프 | **진단 본문** · `파일:줄:칸` · 캐럿 줄의 물결 개수 |
> | 없음 — 이 주제에는 주소도 난수도 안 나온다 | **종료 코드**(`cc exit` 과 `run exit` 을 갈라 적었다) |
> | — | `__PRETTY_FUNCTION__` 문자열 · **맹글링된 심볼 이름**(`_Z4pickc`) |
> | — | 후보가 **몇 개 나열되는지**와 **그 순서** |

## 한눈에 — 쉽게 말하면

**오버로드 해석은 「같은 이름의 창구 여럿 중 어디로 갈지」를 컴파일러가 정하는 절차다.**

여기가 C 와 갈리는 첫 자리다. C 에는 창구가 하나뿐이라 고를 일이 없다.\
C++ 는 창구를 여럿 두는 대신, **어느 창구로 가는지를 표준이 순서까지 정해 놓았다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 같은 간판을 단 **창구 여럿** | 같은 이름의 함수 여럿 — `f(int)` · `f(double)` · `f(char)` |
| **안내판을 보고 후보를 적는다** | **1단계 이름 탐색** — 이름이 있는 스코프를 찾으면 **거기서 멈춘다** |
| 적힌 창구 중 **오늘 여는 곳만** 남긴다 | **2단계 실행 가능 후보** — 인자 개수가 맞고 변환이 존재하는 것만 |
| 남은 곳을 **가까운 순으로 줄 세운다** | **3단계 최적 후보** — 정확 일치 → 승격 → 표준 변환 → 사용자 정의 변환 |
| **1등이 둘이면 줄을 안 선다** | **모호 에러** — 컴파일러가 고르지 않고 후보를 나열하고 멈춘다 |
| 간판에 적힌 **취급 품목**이 다르면 다른 창구 | 매개변수 **타입**이 다르면 다른 오버로드 |
| 간판 **아래 작은 글씨**(영수증 양식)는 창구를 안 가른다 | **반환 타입**은 오버로드를 못 가른다 — 에러다 |

- ★★ **이 절차는 「순서까지 표준이 정한 알고리즘」이다.** C 의 승격·산술 변환이 「무엇으로 올리나」를 정했다면, 여기는 **「여럿 중 무엇을 고르나」를 단계별로** 정한다.
- ★★ **세 단계는 순서대로 진행하고 되돌아오지 않는다.** 1단계에서 후보에 못 들어온 함수는 **3단계에서 아무리 잘 맞아도 안 뽑힌다**((1)).
- ★ **컴파일러가 못 고르면 「대충 고르기」를 하지 않는다** — 에러를 내고 **후보 목록을 찍어 준다**. 그 목록이 이 주제의 교재다((4)).

```text
   f(c);  ← 인자 하나, 이름은 f

   [1단계] 이름 탐색 — 후보 집합을 만든다
        스코프를 바깥으로 훑다가 f 를 처음 찾은 곳에서 멈춘다
        +-----------------------------+
        | f(char) f(int) f(double)    |   ← 후보 집합
        +-----------------------------+

   [2단계] 실행 가능 후보만 남긴다
        · 인자 개수가 맞나
        · 인자마다 「암묵 변환 순서열」이 있나
        +-----------------------------+
        | f(char) f(int) f(double)    |   ← 못 남으면 여기서 탈락
        +-----------------------------+

   [3단계] 최적 후보 — 인자마다 변환 순위를 비교한다
        정확 일치  >  승격  >  표준 변환  >  사용자 정의 변환  >  ...
        +---------+
        | f(char) |   ← 뽑혔다
        +---------+

        1등이 둘이면 -> error: call of overloaded 'f(...)' is ambiguous
```

> **오버로드(overload)** — 같은 이름에 **매개변수가 다른** 함수를 여럿 두는 것.\
> 「어느 것을 부를지」는 호출하는 쪽이 아니라 **컴파일러가 인자를 보고** 정한다.

> **오버로드 해석(overload resolution)** — 그 「정하는 절차」. 위 세 단계다.\
> ★ 전부 **컴파일 시간**에 끝난다. 실행 중에 고르는 일은 없다(그것은 가상 함수의 일이다 — [목록의 **19번 주제**](../19-inheritance-virtual-functions-override-final/)).

> **후보 집합(candidate set)** — 1단계가 만든 목록. 이름 탐색이 찾아낸 것 전부.

> **실행 가능 후보(viable function)** — 후보 중 **인자 개수가 맞고 인자마다 변환이 존재하는** 것.

> **암묵 변환 순서열(implicit conversion sequence)** — 인자 하나를 매개변수 타입으로 바꾸는 변환의 묶음.\
> 이 순서열에 **순위**가 매겨지고, 그 순위 비교가 3단계다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **어느 것이 뽑혔나를 어떻게 증명하나** — 「아마 이게 뽑혔겠지」가 아니라 **출력으로** 보이는 방법이 무엇인가.
2. **순위는 무슨 계단인가** — 정확 일치·승격·표준 변환·사용자 정의 변환을 **각각 고립시킨 예제**로 보일 수 있나.
3. **컴파일러가 못 고르면 무엇을 주나** — 모호 에러 전문에서 **후보 목록**을 읽어 원인을 짚을 수 있나.

★ C 갈래의 [`03-integer-promotion-and-usual-arithmetic-conversions/`](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/)가
「`char` 와 `short` 는 연산 전에 `int` 로 올라간다」를 정본으로 못 박았다면,
여기는 **그 승격이 「계단 하나」로 등급이 매겨져 다른 변환과 겨루는 자리**다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 비용 |
|---|---|---|
| **컴파일 진단** | 막히는 자리와 **왜 막혔는지** — 모호·비실행가능·재정의 | 컴파일만 |
| **실행 출력** | 뽑힌 함수가 **자기 이름을 찍는다** — `__PRETTY_FUNCTION__` | 컴파일 + 실행 |
| **sanitizer** | ★ **이 주제에는 쓸 자리가 없다** — 전부 컴파일 시간 문제다 | — |
| ★ **오브젝트 파일의 미정의 심볼** | 컴파일러가 **어느 서명에 묶었는지를 파일에 적어 둔 것** — `nm -uC` | 컴파일(`-c`) + `nm` |

★ **네 번째 창을 왜 이것으로 골랐나.** `__PRETTY_FUNCTION__` 은 「뽑힌 함수가 스스로 말하는 것」이라
**그 함수의 몸통을 내가 썼다**는 약점이 있다. 몸통을 안 쓰고도 증명할 방법이 필요하다.

**정의를 아예 두지 않고 선언만 두면** 컴파일은 통과하고, 오브젝트 파일에는
**호출 지점이 묶인 맹글링된 이름**이 미정의 심볼로 남는다((8)).
이것은 **런타임이 없고, 내가 쓴 문자열이 아니고, 독자가 자기 머신에서 그대로 재현한다.**

★ **sanitizer 칸을 비워 둔다.** 이 주제가 만드는 문제는 전부 컴파일 시간에 결판나고,
**런타임 도구가 볼 것이 없다.** C 갈래의 [`07-enum-and-enumeration-constants/`](../../../c/syntax/07-enum-and-enumeration-constants/)가
같은 이유로 sanitizer 를 안 쓴 것과 같은 모양이다.

### (1) 1단계 — 후보 집합: 이름 탐색이 먼저 멈춘다

**언제 쓰나** — 「분명히 그 오버로드가 있는데 왜 안 뽑히지?」가 나오는 자리는 거의 전부 여기다.

이름 탐색은 **스코프를 바깥으로 훑다가 그 이름을 처음 찾은 곳에서 멈춘다.**
파생 클래스에 같은 이름이 하나라도 있으면 **기반 클래스의 같은 이름은 후보 집합에 아예 안 들어온다.**

```text
===== 소스: ex.cpp =====
// 1단계는 이름 탐색이다 — 한 스코프에서 이름을 찾으면 거기서 멈춘다
#include <cstdio>
#define WHO std::puts(__PRETTY_FUNCTION__)

struct Base {
    void f(int)    { WHO; }
    void f(double) { WHO; }
};

struct Derived : Base {
    void f(const char*) { WHO; }   // 이름이 같으면 기반의 f 가 후보 집합에 안 들어온다
};

int main() {
    Derived d;
    d.f("hi");
    d.f(1);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp: In function ‘int main()’:
ex.cpp:17:9: error: invalid conversion from ‘int’ to ‘const char*’ [-fpermissive]
   17 |     d.f(1);
      |         ^
      |         |
      |         int
ex.cpp:11:12: note:   initializing argument 1 of ‘void Derived::f(const char*)’
   11 |     void f(const char*) { WHO; }   // 이름이 같으면 기반의 f 가 후보 집합에 안 들어온다
      |            ^~~~~~~~~~~
```

**g++ 의 진단은 「변환이 안 된다」고만 말한다.** 그런데 `Base::f(int)` 가 있는데도 그것을 후보로
말하지 않는다 — 그것이 **후보 집합에 없다는 뜻**이다. clang 도 같은 자리에서 같은 성격으로 막는다.

```text
===== 소스: ex.cpp =====
// 1단계는 이름 탐색이다 — 한 스코프에서 이름을 찾으면 거기서 멈춘다
#include <cstdio>
#define WHO std::puts(__PRETTY_FUNCTION__)

struct Base {
    void f(int)    { WHO; }
    void f(double) { WHO; }
};

struct Derived : Base {
    void f(const char*) { WHO; }   // 이름이 같으면 기반의 f 가 후보 집합에 안 들어온다
};

int main() {
    Derived d;
    d.f("hi");
    d.f(1);
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp:17:9: error: cannot initialize a parameter of type 'const char *' with an rvalue of type 'int'
   17 |     d.f(1);
      |         ^
ex.cpp:11:23: note: passing argument to parameter here
   11 |     void f(const char*) { WHO; }   // 이름이 같으면 기반의 f 가 후보 집합에 안 들어온다
      |                       ^
1 error generated.
```

고치는 법은 **`using` 선언 한 줄**이다. 그 한 줄이 후보 집합을 바꾼다.

```text
===== 소스: ex.cpp =====
// using 선언 한 줄로 기반의 오버로드를 후보 집합에 도로 넣는다
#include <cstdio>
#define WHO std::puts(__PRETTY_FUNCTION__)

struct Base {
    void f(int)    { WHO; }
    void f(double) { WHO; }
};

struct Derived : Base {
    using Base::f;                 // 이 한 줄이 후보 집합을 바꾼다
    void f(const char*) { WHO; }
};

int main() {
    Derived d;
    d.f("hi");
    d.f(1);
    d.f(1.5);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
void Derived::f(const char*)
void Base::f(int)
void Base::f(double)
```

- ★★ **세 호출이 각각 다른 곳으로 갔다** — `Derived::f(const char*)` · `Base::f(int)` · `Base::f(double)`.
- ★ **오버로드 해석 이전에 이름 탐색이 있다**는 것이 이 절의 전부다. 3단계는 **후보 집합 안에서만** 돈다.
- ★ 같은 성질이 네임스페이스에서도 나온다 — 그쪽 정본은 [목록의 **06번 주제**](../06-namespaces-and-adl/)다.

### (2) 2단계 — 실행 가능 후보: 탈락 사유를 컴파일러에게 나열시킨다

**언제 쓰나** — 「후보는 셋인데 왜 하나도 안 되지」를 읽을 때.

실행 가능하려면 둘을 만족해야 한다 — **인자 개수가 맞을 것**, **인자마다 암묵 변환 순서열이 존재할 것**.
하나라도 빠지면 그 후보는 3단계에 못 간다.

★★ **여기서 두 컴파일러가 크게 갈린다.** clang 은 **후보 전부를 탈락 사유와 함께** 나열한다.

```text
===== 소스: ex.cpp =====
// 2단계 — 후보 집합에서 「실행 가능」만 남긴다. 탈락 사유를 컴파일러에게 나열시킨다
struct Big {};

void h(int, int) {}   // 인자 개수가 안 맞는다
void h(char*)    {}   // int -> char* 변환이 없다
void h(Big)      {}   // int -> Big 변환이 없다

int main() {
    h(1);
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp:9:5: error: no matching function for call to 'h'
    9 |     h(1);
      |     ^
ex.cpp:5:6: note: candidate function not viable: no known conversion from 'int' to 'char *' for 1st argument
    5 | void h(char*)    {}   // int -> char* 변환이 없다
      |      ^ ~~~~~
ex.cpp:6:6: note: candidate function not viable: no known conversion from 'int' to 'Big' for 1st argument
    6 | void h(Big)      {}   // int -> Big 변환이 없다
      |      ^ ~~~
ex.cpp:4:6: note: candidate function not viable: requires 2 arguments, but 1 was provided
    4 | void h(int, int) {}   // 인자 개수가 안 맞는다
      |      ^ ~~~~~~~~
1 error generated.
```

**세 후보 각각에 사유가 붙었다** — `requires 2 arguments, but 1 was provided`(개수) ·
`no known conversion from 'int' to 'char *'`(변환 없음) × 2.
**이 세 줄이 2단계의 정의 그대로다.**

g++ 는 같은 소스에서 **후보를 나열하지 않는다.** 하나를 골라 「그것으로의 변환이 안 된다」고만 말한다.

```text
===== 소스: ex.cpp =====
// 2단계 — 후보 집합에서 「실행 가능」만 남긴다. 탈락 사유를 컴파일러에게 나열시킨다
struct Big {};

void h(int, int) {}   // 인자 개수가 안 맞는다
void h(char*)    {}   // int -> char* 변환이 없다
void h(Big)      {}   // int -> Big 변환이 없다

int main() {
    h(1);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp: In function ‘int main()’:
ex.cpp:9:7: error: invalid conversion from ‘int’ to ‘char*’ [-fpermissive]
    9 |     h(1);
      |       ^
      |       |
      |       int
ex.cpp:5:8: note:   initializing argument 1 of ‘void h(char*)’
    5 | void h(char*)    {}   // int -> char* 변환이 없다
      |        ^~~~~
```

- ★★ **후보 집합을 읽고 싶으면 clang 으로도 한 번 던져라.** 같은 코드인데 **교재의 양이 다르다.**
- ★ g++ 가 `-fpermissive` 를 언급하는 것은 「이 변환은 확장으로 봐줄 수도 있는 종류」라는 뜻이지 **후보 목록이 아니다.**

### (3) 3단계 — 최적 후보: 변환 순위 네 계단

**언제 쓰나** — 「왜 저게 아니라 이게 뽑혔지」를 설명할 때.

인자마다 변환 순서열의 **순위**를 비교한다. 이 문서가 다루는 범위에서 계단은 넷이다.

```text
   좋다 ←───────────────────────────────────────────────→ 나쁘다

   ① 정확 일치        ② 승격            ③ 표준 변환        ④ 사용자 정의 변환
   char -> char       char -> int       int -> double     int -> S (S(int) 생성자)
   (변환 없음)        (C 의 정수 승격)   (정수<->부동 등)   (내가 쓴 생성자·변환 연산자)
```

네 계단을 **각각 고립시켜** 한 파일에서 던진다. 각 네임스페이스에 후보를 둘씩만 두고
**뽑힌 쪽이 자기 이름을 찍게** 한다.

```text
===== 소스: ex.cpp =====
// 오버로드 해석의 네 단계를 각각 고립시킨다 — 뽑힌 후보가 자기 이름을 찍는다
#include <cstdio>
#define WHO std::puts(__PRETTY_FUNCTION__)

struct S { S(int) {} };                  // int 를 받는 변환 생성자

namespace step1 { void f(char)   { WHO; } void f(int)    { WHO; } }
namespace step2 { void f(int)    { WHO; } void f(double) { WHO; } }
namespace step3 { void f(double) { WHO; } void f(S)      { WHO; } }
namespace step4 { void f(S)      { WHO; } }

int main() {
    char c = 'a';
    std::puts("(1) 정확 일치 대 승격");         step1::f(c);
    std::puts("(2) 승격 대 표준 변환");          step2::f(c);
    std::puts("(3) 표준 변환 대 사용자 정의");    step3::f(1);
    std::puts("(4) 사용자 정의 변환뿐일 때");     step4::f(1);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 정확 일치 대 승격
void step1::f(char)
(2) 승격 대 표준 변환
void step2::f(int)
(3) 표준 변환 대 사용자 정의
void step3::f(double)
(4) 사용자 정의 변환뿐일 때
void step4::f(S)
```

읽는 법은 이렇다.

| 단계 | 후보 둘 | 인자 | 뽑힌 것 | 왜 |
|---|---|---|---|---|
| (1) | `f(char)` \| `f(int)` | `char` | **`f(char)`** | 정확 일치가 승격을 이긴다 |
| (2) | `f(int)` \| `f(double)` | `char` | **`f(int)`** | 승격(`char`→`int`)이 표준 변환(`char`→`double`)을 이긴다 |
| (3) | `f(double)` \| `f(S)` | `int` | **`f(double)`** | 표준 변환이 사용자 정의 변환을 이긴다 |
| (4) | `f(S)` 하나 | `int` | **`f(S)`** | 사용자 정의 변환은 마지막 수단이되 **수단이기는 하다** |

★ (2)가 C 갈래와 맞물리는 자리다. `char` → `int` 가 **「승격」이라는 이름을 가진 한 계단**인 이유는
C 의 정수 승격 규칙이 그것을 「자연스러운 확장」으로 정해 뒀기 때문이다 —
규칙 자체의 정본은 [C 의 03번 형제](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/)다.

산술 타입 일곱을 **같은 후보 넷**에 던지면 계단이 표로 보인다.

```text
===== 소스: ex.cpp =====
// 산술 타입 일곱 개를 같은 후보 넷에 던진다 — 승격과 변환이 갈리는 표를 실행으로 만든다
#include <cstdio>
#define WHO std::puts(__PRETTY_FUNCTION__)

void f(char)   { WHO; }
void f(int)    { WHO; }
void f(long)   { WHO; }
void f(double) { WHO; }

int main() {
    char          c  = 'a';
    signed char   sc = 1;
    unsigned char uc = 1;
    short         s  = 1;
    bool          b  = true;
    int           i  = 1;
    float         fl = 1.0f;
    std::puts("char");          f(c);
    std::puts("signed char");   f(sc);
    std::puts("unsigned char"); f(uc);
    std::puts("short");         f(s);
    std::puts("bool");          f(b);
    std::puts("int");           f(i);
    std::puts("float");         f(fl);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
char
void f(char)
signed char
void f(int)
unsigned char
void f(int)
short
void f(int)
bool
void f(int)
int
void f(int)
float
void f(double)
```

| 인자 타입 | 뽑힌 것 | 무슨 계단인가 |
|---|---|---|
| `char` | `f(char)` | 정확 일치 |
| `signed char` | `f(int)` | **승격** — `char` 와 `signed char` 는 다른 타입이다 |
| `unsigned char` | `f(int)` | 승격 |
| `short` | `f(int)` | 승격 |
| `bool` | `f(int)` | 승격 — `bool` 도 승격 대상이다 |
| `int` | `f(int)` | 정확 일치 |
| `float` | `f(double)` | **승격** — `float`→`double` 은 「부동소수 승격」이다 |

- ★★ **`char` · `signed char` · `unsigned char` 는 서로 다른 세 타입**이고, 오버로드 해석이 그것을 그대로 드러낸다. `char` 만 `f(char)` 로 가고 나머지 둘은 `f(int)` 로 갔다.
- ★ **`float` → `double` 도 「승격」이다.** 그래서 `f(long)` 을 제치고 `f(double)` 이 뽑힌다.

### (4) 순위가 같으면 — 모호 에러 전문

**언제 쓰나** — 컴파일러가 **고르기를 거부한** 자리. 후보 목록이 같이 나오므로 **읽을 값이 가장 많은 진단**이다.

`unsigned int` 를 `char`·`int`·`long`·`double` 넷에 던지면 **넷이 전부 같은 계단**(표준 변환)에 선다.
`unsigned int` → `int` 도, → `long` 도, → `double` 도 전부 「변환」이고 **그 안에서 더 낫고 못한 것이 없다.**

```text
===== 소스: ex.cpp =====
// 3단계 — 실행 가능 후보가 넷인데 순위가 같다. 네 개가 전부 나열된다
void pick(char);
void pick(int);
void pick(long);
void pick(double);

int main() {
    unsigned u = 1u;
    pick(u);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp: In function ‘int main()’:
ex.cpp:9:9: error: call of overloaded ‘pick(unsigned int&)’ is ambiguous
    9 |     pick(u);
      |     ~~~~^~~
ex.cpp:2:6: note: candidate: ‘void pick(char)’
    2 | void pick(char);
      |      ^~~~
ex.cpp:3:6: note: candidate: ‘void pick(int)’
    3 | void pick(int);
      |      ^~~~
ex.cpp:4:6: note: candidate: ‘void pick(long int)’
    4 | void pick(long);
      |      ^~~~
ex.cpp:5:6: note: candidate: ‘void pick(double)’
    5 | void pick(double);
      |      ^~~~
```

- ★★ **후보 넷이 전부 나열됐다.** (2)의 `h` 예제에서 g++ 가 후보를 안 나열한 것과 다르다 — **모호할 때는 g++ 도 전부 나열한다.**
- ★ 진단이 인자를 `pick(unsigned int&)` 라고 적는다. **참조 꼴로 적히는 것**은 g++ 의 표기 습관이다(인자는 `unsigned int` 값이다).
- ★ 캐럿 줄의 `~~~~^~~` 는 「이름 부분」과 「호출 부분」을 같이 짚은 것이다.

clang 은 같은 자리를 **더 짧게** 말한다 — 후보는 넷 다 나열하되 사유를 안 붙인다.

```text
===== 소스: ex.cpp =====
// 3단계 — 실행 가능 후보가 넷인데 순위가 같다. 네 개가 전부 나열된다
void pick(char);
void pick(int);
void pick(long);
void pick(double);

int main() {
    unsigned u = 1u;
    pick(u);
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp:9:5: error: call to 'pick' is ambiguous
    9 |     pick(u);
      |     ^~~~
ex.cpp:2:6: note: candidate function
    2 | void pick(char);
      |      ^
ex.cpp:3:6: note: candidate function
    3 | void pick(int);
      |      ^
ex.cpp:4:6: note: candidate function
    4 | void pick(long);
      |      ^
ex.cpp:5:6: note: candidate function
    5 | void pick(double);
      |      ^
1 error generated.
```

★ **`1 error generated.` 줄이 clang 에는 있고 g++ 에는 없다.** 진단을 옮겨 적을 때 가장 자주 빠지는 줄이다.

**고치는 법은 셋이다** — ① 호출 쪽에서 캐스트해 계단을 하나로 만든다(`pick(static_cast<int>(u))`) ·
② `pick(unsigned)` 오버로드를 추가해 **정확 일치**를 만든다 · ③ 오버로드를 줄인다.

### (5) `const` 가 가르는 자리와 못 가르는 자리

**언제 쓰나** — 읽기 전용 경로와 쓰기 경로를 한 이름으로 내놓을 때.

```text
===== 소스: ex.cpp =====
// const 가 오버로드를 가르는 자리와 못 가르는 자리
#include <cstdio>
#define WHO std::puts(__PRETTY_FUNCTION__)

struct Box {
    int v = 0;
    int&       at()       { WHO; return v; }
    const int& at() const { WHO; return v; }
};

void g(int&)       { WHO; }
void g(const int&) { WHO; }

int main() {
    Box b; const Box cb;
    b.at();
    cb.at();

    int x = 1; const int cx = 1;
    g(x);
    g(cx);
    g(42);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
int& Box::at()
const int& Box::at() const
void g(int&)
void g(const int&)
void g(const int&)
```

읽는 법.

| 호출 | 뽑힌 것 | 왜 |
|---|---|---|
| `b.at()` (비const 객체) | `int& Box::at()` | 비const 객체에는 **비const 멤버가 정확 일치** |
| `cb.at()` (const 객체) | `const int& Box::at() const` | const 객체에서는 **const 멤버만 실행 가능** |
| `g(x)` (비const lvalue) | `void g(int&)` | `int&` 가 더 적게 변환한다 |
| `g(cx)` (const lvalue) | `void g(const int&)` | `int&` 는 **실행 가능 후보가 아니다** |
| `g(42)` (임시) | `void g(const int&)` | 비const lvalue 참조는 임시에 못 묶인다 |

- ★★ **멤버 함수의 `const` 는 「숨은 `this` 의 const」다.** `Box::at()` 은 `Box*`, `Box::at() const` 는 `const Box*` 를 받는 것이라 **매개변수가 다른 두 함수**가 된다.
- ★ 「그래서 인터페이스를 어떻게 설계하나」의 정본은 [목록의 **10번 주제**](../10-const-correctness/)다. 여기서는 **해석이 어떻게 갈리나**까지만 쓴다.

### (6) 오버로드가 **아닌** 것 — 반환 타입과 최상위 `const`

**언제 쓰나** — 「분명 다르게 썼는데 재정의라고 한다」가 나올 때.

오버로드를 가르는 것은 **매개변수 목록**이다. 반환 타입은 거기 없다.

```text
===== 소스: ex.cpp =====
// 반환 타입만 다른 것은 오버로드가 아니다
int  f(int x) { return x; }
long f(int x) { return x; }

int main() { return 0; }
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp:3:6: error: ambiguating new declaration of ‘long int f(int)’
    3 | long f(int x) { return x; }
      |      ^
ex.cpp:2:6: note: old declaration ‘int f(int)’
    2 | int  f(int x) { return x; }
      |      ^
```

clang 은 **한 문장으로** 말해 준다 — 이 문장이 이 절의 요약이다.

```text
===== 소스: ex.cpp =====
// 반환 타입만 다른 것은 오버로드가 아니다
int  f(int x) { return x; }
long f(int x) { return x; }

int main() { return 0; }
===== clang++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp:3:6: error: functions that differ only in their return type cannot be overloaded
    3 | long f(int x) { return x; }
      | ~~~~ ^
ex.cpp:2:6: note: previous definition is here
    2 | int  f(int x) { return x; }
      | ~~~  ^
1 error generated.
```

★ **왜 안 되는가**는 한 줄로 설명된다 — `f(1);` 처럼 **반환값을 안 쓰는 호출**이 있으면 컴파일러가 고를 근거가 사라진다.
해석은 **인자만 보고** 하기 때문이다.

매개변수의 **최상위 `const`** 도 오버로드를 못 가른다. 값으로 받는 것은 어차피 복사라 호출 쪽에서 차이가 없다.

```text
===== 소스: ex.cpp =====
// 매개변수의 최상위 const 는 오버로드를 못 가른다 — 같은 함수의 재정의가 된다
void h(int)       {}
void h(const int) {}

int main() {}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp:3:6: error: redefinition of ‘void h(int)’
    3 | void h(const int) {}
      |      ^
ex.cpp:2:6: note: ‘void h(int)’ previously defined here
    2 | void h(int)       {}
      |      ^
```

- ★ **`void h(const int)` 는 `void h(int)` 의 재선언**이다 — 정의가 둘이면 재정의 에러가 된다.
- ★ **`const int&` 나 `const int*` 는 다르다**((5)) — 저것은 최상위가 아니라 **가리키는 대상의 const** 다.

### (7) 기본 인자와 오버로드가 부딪히면

**언제 쓰나** — 편의로 기본값을 붙였다가 기존 오버로드와 겹치는 자리.

```text
===== 소스: ex.cpp =====
// 기본 인자와 오버로드가 부딪히면 — 선언 자리에서는 안 걸리고 호출 자리에서 걸린다
#include <cstdio>
#define WHO std::puts(__PRETTY_FUNCTION__)

void f(int a, int b = 0) { WHO; (void)a; (void)b; }
void f(int a)            { WHO; (void)a; }

int main() { f(1); }
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp: In function ‘int main()’:
ex.cpp:8:15: error: call of overloaded ‘f(int)’ is ambiguous
    8 | int main() { f(1); }
      |              ~^~~
ex.cpp:5:6: note: candidate: ‘void f(int, int)’
    5 | void f(int a, int b = 0) { WHO; (void)a; (void)b; }
      |      ^
ex.cpp:6:6: note: candidate: ‘void f(int)’
    6 | void f(int a)            { WHO; (void)a; }
      |      ^
```

- ★★ **선언 자리에서는 아무 말도 안 한다.** `void f(int, int = 0)` 과 `void f(int)` 는 **서명이 달라 둘 다 합법**이다.
- ★★ 터지는 것은 **호출 자리**다 — `f(1)` 에 대해 둘 다 실행 가능하고 **둘 다 정확 일치**다.
- ★ 그래서 이 사고는 **호출이 생겨야 드러난다.** 라이브러리에 기본 인자를 추가하면 **쓰는 쪽에서 깨진다.**

clang 도 같은 자리에서 같은 성격으로 막는다.

```text
===== 소스: ex.cpp =====
// 기본 인자와 오버로드가 부딪히면 — 선언 자리에서는 안 걸리고 호출 자리에서 걸린다
#include <cstdio>
#define WHO std::puts(__PRETTY_FUNCTION__)

void f(int a, int b = 0) { WHO; (void)a; (void)b; }
void f(int a)            { WHO; (void)a; }

int main() { f(1); }
===== clang++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp:8:14: error: call to 'f' is ambiguous
    8 | int main() { f(1); }
      |              ^
ex.cpp:5:6: note: candidate function
    5 | void f(int a, int b = 0) { WHO; (void)a; (void)b; }
      |      ^
ex.cpp:6:6: note: candidate function
    6 | void f(int a)            { WHO; (void)a; }
      |      ^
1 error generated.
```

### (8) 네 번째 창 — 오브젝트 파일이 답을 적어 둔다

**언제 쓰나** — 「뽑힌 함수가 스스로 말한 것」 말고 **바깥 증거**가 필요할 때.

정의를 **두지 않고 선언만** 두면 컴파일은 통과한다. 그리고 오브젝트 파일에는
호출 지점이 묶인 서명이 **맹글링된 이름**으로 남는다.

```text
===== 소스: ex.cpp =====
// 정의를 두지 않는다 — 오브젝트 파일의 미정의 심볼이 「무엇을 불렀나」를 이름으로 말한다
void pick(char);
void pick(int);
void pick(long);
void pick(double);

int main() {
    char  c = 'a';
    short s = 1;
    float f = 1.0f;
    pick(c);
    pick(s);
    pick(f);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -c ex.cpp -o ex.o && nm -uC ex.o (cc exit=0 · run exit=0) =====
                 U pick(char)
                 U pick(double)
                 U pick(int)
```

- ★★ **호출은 셋인데 선언은 넷이다.** `pick(long)` 은 **한 번도 안 나온다** — 아무 호출도 거기 묶이지 않았다는 뜻이다.
- ★ `char` → `pick(char)` · `short` → `pick(int)` · `float` → `pick(double)` 로 (3)의 표와 **정확히 같다.**

맹글링을 풀지 않으면 이렇게 보인다. **타입이 이름에 박혀 있다** — 이것이 오버로드가 링크 단계에서 충돌하지 않는 이유다.

```text
===== 소스: ex.cpp =====
// 정의를 두지 않는다 — 오브젝트 파일의 미정의 심볼이 「무엇을 불렀나」를 이름으로 말한다
void pick(char);
void pick(int);
void pick(long);
void pick(double);

int main() {
    char  c = 'a';
    short s = 1;
    float f = 1.0f;
    pick(c);
    pick(s);
    pick(f);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -c ex.cpp -o ex.o && nm -u ex.o (cc exit=0 · run exit=0) =====
                 U _Z4pickc
                 U _Z4pickd
                 U _Z4picki
```

★ `_Z4pickc` 의 꼬리 `c` 가 `char`, `i` 가 `int`, `d` 가 `double` 이다.
**맹글링 규칙 자체는 이 플랫폼의 C++ ABI 가 정한다** — 표준이 아니다(아래 다섯 층 표).

### (9) 다섯 층 — 무엇이 표준이고 무엇이 도구인가

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** C 갈래가 굳혀 놓은 다섯 층을 그대로 쓴다.\
★★ **이 주제는 「표준」 칸이 압도적으로 두껍다.** C 에서 구현 정의였을 법한 것이 여기서는 **순서까지 표준에 적혀 있다.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | **세 단계의 순서** · **이름 탐색이 한 스코프에서 멈추는 것** · **변환 순위 네 계단** · 반환 타입이 오버로드를 못 가르는 것 · 최상위 `const` 가 못 가르는 것 · const 멤버와 비const 멤버가 다른 오버로드인 것 · 임시가 비const lvalue 참조에 안 묶이는 것 · **모호하면 에러인 것** | 두 컴파일러가 **같은 선택**을 했다(7건 전부) · 에러가 나는 자리가 같았다 | — |
| **조건부 표준** | 매크로·옵션이 있을 때만 | **해당 없음** — 이 주제에 조건부 보장은 없다 | — | — |
| **구현 정의** | 문서화 의무가 있다 | **맹글링된 이름의 철자**(`_Z4pickc`) — 플랫폼 ABI 가 정한다 · `__PRETTY_FUNCTION__` 문자열의 형식 | `nm -u` 와 `nm -uC` 를 갈라 찍음 | 경고가 한 건도 안 난다 |
| **미명시** | 몇 가지 중 하나 | **해당 없음** | — | — |
| **UB** | 아무 일이나 | ★ **해당 없음** — 이 주제가 만드는 실패는 **전부 컴파일 에러**다 | — | ★ sanitizer 가 **볼 것이 없다** |

**「도구가 못 보는 것」을 층마다 — 전용 표**

| 사실 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | 실행 | `nm -uC` |
|---|---|---|---|---|
| 기반의 오버로드가 가려진 것 | **에러**(변환 실패로) | **에러**(변환 실패로) | 못 본다 | 못 본다 |
| ★ **후보 전수와 탈락 사유** | **안 나열한다** | ★ **셋 전부 사유와 함께** | 못 본다 | 못 본다 |
| 모호한 호출 | **에러 + 후보 4** | **에러 + 후보 4** | 못 본다 | 못 본다 |
| ★ **어느 오버로드가 뽑혔나(성공한 호출)** | **0건 — 아무 말도 안 한다** | **0건** | ★ 찍는다 | ★ **심볼로 남는다** |
| 기본 인자와 오버로드가 겹친 선언 | **0건**(호출이 있어야 걸린다) | **0건** | — | — |

- ★★ **성공한 호출에 대해서는 컴파일러가 한마디도 안 한다.** 「의도한 창구로 갔나」는 **경고로 잡히지 않는다.** 그래서 이 주제는 **실행 출력과 심볼표가 유일한 검사**다.
- ★ **`-Wall -Wextra -pedantic` 은 이 주제에서 경고를 한 건도 내지 않았다.** 이 문서의 모든 실패는 `cc exit=1` 인 **에러**다 — 「경고 0건」이 통과의 증거가 못 되는 전형이다.

## 문법 — 형태와 규칙

### 형태

```cpp
/* ex.cpp */
// 오버로드 해석의 네 단계를 각각 고립시킨다 — 뽑힌 후보가 자기 이름을 찍는다
#include <cstdio>
#define WHO std::puts(__PRETTY_FUNCTION__)

struct S { S(int) {} };                  // int 를 받는 변환 생성자

namespace step1 { void f(char)   { WHO; } void f(int)    { WHO; } }
namespace step2 { void f(int)    { WHO; } void f(double) { WHO; } }
namespace step3 { void f(double) { WHO; } void f(S)      { WHO; } }
namespace step4 { void f(S)      { WHO; } }

int main() {
    char c = 'a';
    std::puts("(1) 정확 일치 대 승격");         step1::f(c);
    std::puts("(2) 승격 대 표준 변환");          step2::f(c);
    std::puts("(3) 표준 변환 대 사용자 정의");    step3::f(1);
    std::puts("(4) 사용자 정의 변환뿐일 때");     step4::f(1);
}
```

규칙 불릿.

- 오버로드를 가르는 것은 **매개변수의 개수와 타입**이다. 이름이 같고 **매개변수 목록이 다르면** 다른 함수다.
- **반환 타입은 안 가른다** — 같은 매개변수에 다른 반환 타입은 **에러**다((6)).
- 매개변수의 **최상위 `const`** 도 안 가른다. `const T&`·`const T*` 는 최상위가 아니므로 **가른다**.
- **멤버 함수의 `const`** 는 가른다 — 숨은 `this` 의 타입이 다르기 때문이다((5)).
- 해석은 **인자만 보고** 한다. 대입 대상의 타입·문맥은 안 본다.
- **1등이 둘이면 에러**다. 컴파일러가 임의로 고르지 않는다.
- 인자가 여럿이면 **인자마다 순위를 비교**하고, 「모든 인자에서 나쁘지 않고 적어도 하나에서 더 좋아야」 이긴다.

### 금지 사례 — 던져서 받은 넷

| 쓴 것 | 컴파일러 | 무엇이 나오나 |
|---|---|---|
| `int f(int); long f(int);` | g++ | `error: ambiguating new declaration of 'long int f(int)'` |
| 〃 | clang | `error: functions that differ only in their return type cannot be overloaded` |
| `void h(int); void h(const int);` (정의 둘) | g++ | `error: redefinition of 'void h(int)'` |
| `f(1)` 에 `f(int,int=0)` 과 `f(int)` | g++ | `error: call of overloaded 'f(int)' is ambiguous` |
| `pick(u)` (`unsigned`) 에 후보 넷 | g++ | `error: call of overloaded 'pick(unsigned int&)' is ambiguous` + **후보 4** |

### 고를 것을 손으로 돌리는 순서

1. **이 이름이 어느 스코프에서 찾아지나** — 파생 클래스·안쪽 네임스페이스에 같은 이름이 있으면 **바깥은 안 본다.**
2. 찾아낸 후보 중 **인자 개수가 맞는 것**만 남긴다.
3. 남은 것마다 **인자별 변환 계단**을 매긴다 — 정확 일치 / 승격 / 표준 변환 / 사용자 정의 변환.
4. 모든 인자에서 나쁘지 않고 **적어도 한 인자에서 더 좋은** 후보가 있으면 그것이 답이다.
5. 없으면 **모호**다 — 에러 전문의 후보 목록을 읽고 2\~3번으로 돌아간다.

## 어디서 틀리나

### 1. ★★ 「기반 클래스의 오버로드도 당연히 후보다」

아니다. **파생에 같은 이름이 하나라도 있으면 기반의 같은 이름은 전부 가려진다**((1)).\
진단은 「변환이 안 된다」고만 말하고 **가려졌다는 말을 안 한다** — 그래서 읽기 어렵다.\
처방은 `using Base::f;` 한 줄이다.

### 2. ★★ 「반환 타입이 다르면 다른 함수다」

아니다. **에러**다((6)). clang 의 문장이 그대로 답이다 —
`functions that differ only in their return type cannot be overloaded`.\
해석이 **인자만 보기** 때문이고, `f(1);` 처럼 반환값을 버리는 호출을 생각하면 왜인지 바로 보인다.

### 3. ★★ 「모호하면 컴파일러가 알아서 가까운 걸 고른다」

안 고른다. **후보를 나열하고 멈춘다**((4)). 그리고 **그 목록이 이 주제에서 가장 정보가 많은 출력**이다.

### 4. ★★ 「`unsigned` 를 넘기면 `int` 가 뽑히겠지」

`unsigned int` → `int`·`long`·`double`·`char` 가 **전부 같은 계단**이라 후보가 여럿이면 **모호**다((4)).\
「비슷하게 생겼으니 가까울 것」이라는 직관이 안 통하는 대표 자리다.

### 5. ★ 「`char` 랑 `signed char` 는 같은 거 아닌가」

**서로 다른 세 타입**(`char`·`signed char`·`unsigned char`)이고, 오버로드 해석이 그것을 그대로 드러낸다((3)).\
`f(char)` 와 `f(int)` 만 있을 때 `signed char` 는 **`f(int)` 로 간다.**

### 6. ★ 「매개변수에 `const` 를 붙이면 오버로드가 하나 더 생긴다」

값 매개변수의 **최상위 `const`** 는 안 생긴다 — **재선언**이다((6)).\
`const T&` 로 받으면 생긴다. 둘의 차이는 「**복사본이 const 인가**」와 「**원본을 안 건드린다는 약속인가**」다.

### 7. ★ 「기본 인자는 공짜다」

기존 오버로드와 **호출 자리에서** 부딪힌다((7)). 선언 자리에서는 조용하므로
**라이브러리에 기본 인자를 추가하는 변경은 쓰는 쪽을 깨뜨릴 수 있다.**

### 8. ★ 「`__PRETTY_FUNCTION__` 은 표준이다」

아니다. **gcc·clang 확장**이다. 표준의 `__func__` 는 **이름만** 주므로 오버로드를 구별하지 못한다.\
이식이 필요하면 **오브젝트 파일의 심볼**((8)) 쪽이 더 단단하다.

### 9. ★ 「g++ 가 후보를 안 보여 주니 못 보는 것이다」

**컴파일러 문제다** — 같은 코드를 clang 에 던지면 **후보 전수와 탈락 사유**가 나온다((2)).\
진단이 부족하면 **다른 컴파일러에도 던져 보는 것**이 이 갈래의 기본기다.

### 10. 「사용자 정의 변환이 있으니 아무 타입이나 넘겨도 된다」

사용자 정의 변환은 **한 번만** 끼어들 수 있고 **계단의 맨 아래**다((3)).\
표준 변환으로 갈 수 있는 후보가 하나라도 있으면 **그쪽이 이긴다.**

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| **세 단계의 순서**(이름 탐색 → 실행 가능 → 최적) | **언어.** 표준이 알고리즘으로 적어 두었다 |
| **변환 순위 네 계단**과 그 대소 | **언어** |
| **파생이 기반의 같은 이름을 가리는 것** | **언어** |
| **모호하면 에러**인 것 | **언어** |
| 반환 타입·최상위 `const` 가 오버로드를 못 가르는 것 | **언어** |
| ★ **진단에 후보가 몇 개 나열되나** | **컴파일러 구현.** clang 은 탈락 사유까지, g++ 는 모호할 때만 |
| ★ **진단 문구**(`ambiguating new declaration` 대 `differ only in their return type`) | **컴파일러 구현** |
| ★ **맹글링된 심볼의 철자**(`_Z4pickc`) | **플랫폼 ABI.** 표준이 아니다 |
| `__PRETTY_FUNCTION__` 의 존재와 형식 | **gcc·clang 확장** |
| `nm` 이 `U` 로 찍는 것·`-C` 가 풀어 주는 것 | **binutils 구현** |
| ★ **두 컴파일러가 같은 오버로드를 골랐다는 것** | ★ **관찰이면서 보장**이다 — 선택 규칙은 표준이고, **같았다는 사실 자체는 관찰**이다 |

## 언제 쓰고 언제 안 쓰나

**쓴다.**

- **같은 일을 다른 타입에** 하는 함수 — `print(int)` · `print(const std::string&)`.
- **읽기 경로와 쓰기 경로**를 한 이름으로 — `at()` 과 `at() const`((5)).
- 편의 오버로드 — 인자를 덜 받는 판을 **별도 함수로** 두는 것(기본 인자보다 안전하다((7))).

**안 쓴다.**

- **하는 일이 다른데** 이름만 같은 것. 이름은 **무엇을 하나**를 말해야 한다.
- **암묵 변환에 기대어** 오버로드를 늘리는 것 — 모호가 늘고 진단이 길어진다.
- **기본 인자와 오버로드를 같이** — 부딪히면 호출 자리에서 터진다((7)).
- 산술 타입 전부를 덮으려고 `char`·`short`·`int`·`long`·`float`·`double` 을 다 쓰는 것. **승격이 대신 해 준다**((3)).

## 핵심 문장

1. **오버로드 해석은 세 단계다** — 이름 탐색으로 후보를 만들고, 실행 가능한 것만 남기고, 변환 순위로 하나를 고른다.
2. **1단계에서 빠진 함수는 3단계에서 아무리 잘 맞아도 안 뽑힌다** — 파생 클래스의 이름 가리기가 그 전형이다.
3. **순위는 네 계단이다** — 정확 일치 → 승격 → 표준 변환 → 사용자 정의 변환.
4. **1등이 둘이면 컴파일러는 고르지 않고 후보를 나열한다** — 그 목록이 원인이다.
5. **반환 타입은 오버로드를 못 가른다** — 해석이 인자만 보기 때문이다.
6. **어느 것이 뽑혔는지는 경고로 안 나온다** — 실행 출력이나 오브젝트 파일의 심볼로만 보인다.

## 관련 자료

- [C 갈래 `03-integer-promotion-and-usual-arithmetic-conversions/`](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/) —\
  **정수 승격·통상 산술 변환의 정본.** 그쪽은 「무엇이 무엇으로 올라가나」까지, **여기는 「그 승격이 한 계단으로 등급이 매겨져 겨루는 자리」부터.**
- [C 갈래 `05-explicit-casts-and-pointer-conversions/`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/) —\
  캐스트로 **계단을 손수 하나로 만드는** 처방이 거기 있다. C++ 의 캐스트 문법은 [**03번 형제**](../03-four-cast-operators/)다.
- [**02번 형제**](../02-enum-class-and-scoped-enumerations/) — `enum class` 가 **암묵 변환을 끊어 오버로드 후보를 줄이는** 자리.
- [**04번 형제**](../04-brace-initialization-narrowing-and-initializer-list/) —\
  `{}` 를 쓰면 **`initializer_list` 생성자가 다른 생성자를 이기는** 규칙이 붙는다. 그쪽은 **생성자 해석의 특칙**이다.
- [목록의 **06번 주제**](../06-namespaces-and-adl/)(네임스페이스와 ADL) — 후보 집합이 **네임스페이스에서** 어떻게 불어나나.
- [목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/)(값 범주) — `T&` 와 `T&&` 오버로드를 **무엇이 가르나**.
- [목록의 **10번 주제**](../10-const-correctness/)(`const` 정확성) — (5)의 갈래를 **설계로** 쓰는 법.
- [목록의 **19번 주제**](../19-inheritance-virtual-functions-override-final/)(가상 함수) — 이 문서의 선택은 **컴파일 시간**이고, 그쪽은 **실행 시간**이다.
- 목록의 **31번 주제**(함수 템플릿) — 템플릿이 후보에 섞이면 규칙이 한 겹 늘어난다.

## 용어 풀이

> **오버로드(overload)** — 같은 이름에 매개변수가 다른 함수를 여럿 두는 것.

> **오버로드 해석(overload resolution)** — 호출 하나에 대해 그중 하나를 고르는 **컴파일 시간 절차**.

> **후보 집합(candidate set)** — 이름 탐색이 찾아낸 함수 전부. **여기 못 들어오면 끝이다.**

> **실행 가능 후보(viable function)** — 인자 개수가 맞고 인자마다 변환이 존재하는 후보.

> **암묵 변환 순서열(implicit conversion sequence)** — 인자 하나를 매개변수 타입으로 만드는 변환의 묶음. **순위가 매겨진다.**

> **정확 일치(exact match)** — 변환이 없거나 「없는 것과 같은」 것(lvalue→rvalue 등). 가장 좋은 계단.

> **승격(promotion)** — `char`·`short`·`bool` → `int`, `float` → `double` 처럼 **폭을 넓히는 자연스러운 확장.**\
> 규칙의 정본은 [C 의 03번 형제](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/)다.

> **표준 변환(standard conversion)** — 정수↔부동, 폭 줄이기, 포인터 변환 등 **언어가 정해 둔 나머지 변환.** 승격보다 나쁜 계단.

> **사용자 정의 변환(user-defined conversion)** — 내가 쓴 **변환 생성자**나 **변환 연산자**가 끼어드는 것. **한 번만** 끼어들 수 있고 가장 나쁜 계단.

> **이름 가리기(name hiding)** — 안쪽 스코프의 같은 이름이 바깥 스코프의 **그 이름 전부**를 가리는 것.

> **맹글링(name mangling)** — 컴파일러가 함수의 **매개변수 타입까지 넣어** 링커용 이름을 만드는 것.\
> `_Z4pickc` 의 꼬리 `c` 가 `char` 다. 철자는 **플랫폼 ABI** 소관이다.

> **`__PRETTY_FUNCTION__`** — gcc·clang 확장. **서명 전체**를 문자열로 준다. 표준의 `__func__` 는 이름만 준다.

## 더 들어가면

- **인자가 여럿일 때의 비교 규칙** — 「모든 인자에서 나쁘지 않고 적어도 하나에서 더 좋아야」 이긴다.\
  그래서 **한 인자에서 이기고 다른 인자에서 지면 모호**가 된다. 이 문서는 인자 하나짜리만 던졌다.
- **참조 바인딩의 순위** — `T&` 대 `const T&` 대 `T&&` 는 (5)보다 규칙이 깊다. 정본은 [목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/)다.
- **템플릿이 섞이면** — 비템플릿이 템플릿과 동점이면 **비템플릿이 이긴다.** 템플릿끼리는 **더 특수한 쪽**이 이긴다. 목록의 **31번 주제**.
- **ADL 이 후보를 늘리는 것** — 인자의 타입이 사는 네임스페이스가 **후보 집합에 얹힌다.** [목록의 **06번 주제**](../06-namespaces-and-adl/).
- **`=delete` 로 후보를 죽이는 것** — 후보에는 들어오되 **뽑히면 에러**가 된다. 「그 타입으로는 부르지 마라」를 진단으로 만드는 수법이다. [목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/).
- **`-fdump-lang-all` 로 컴파일러 내부를 보기** — g++ 에 있지만 **이 주제에서는 `nm` 쪽이 훨씬 읽기 쉬웠다**(내부 덤프는 후보 목록을 그대로 내놓지 않는다). 그래서 (8)의 창을 골랐다.
