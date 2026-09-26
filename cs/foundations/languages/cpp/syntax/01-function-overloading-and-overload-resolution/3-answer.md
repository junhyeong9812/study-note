# cpp/syntax/01 — 함수 오버로딩과 오버로드 해석 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·심볼은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex` 이고 파일 이름은 **전부 `ex.cpp`** 다.\
> **진단의 줄 번호는 그 파일 기준**이라 질문 쪽 발췌와 어긋날 수 있다.\
> 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 `capture.sh` 가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★★ 이 주제의 네 번째 창은 **오브젝트 파일의 미정의 심볼**(6번)이다.
> **읽는 법** — 블록 안의 `(cc exit=N · run exit=M)` 은 **컴파일 종료 코드와 실행 종료 코드**를 갈라 적은 것이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 네 줄이 네 계단을 하나씩 밟는다

**출력**

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

**왜 그런가**

인자마다 매겨지는 **암묵 변환 순서열의 순위**가 이 순서로 줄 세워져 있기 때문이다.

| 줄 | 후보 둘 | 인자 | 뽑힌 것 | 계단 |
|---|---|---|---|---|
| (1) | `f(char)` \| `f(int)` | `char` | `step1::f(char)` | **정확 일치** — 변환이 아예 없다 |
| (2) | `f(int)` \| `f(double)` | `char` | `step2::f(int)` | **승격** — `char`→`int` |
| (3) | `f(double)` \| `f(S)` | `int` | `step3::f(double)` | **표준 변환** — `int`→`double` |
| (4) | `f(S)` 하나 | `int` | `step4::f(S)` | **사용자 정의 변환** — `S(int)` |

- **(2)에서 한쪽이 이기는 이유** — `char`→`int` 는 **승격**이고 `char`→`double` 은 **표준 변환**이다.\
  승격이 표준 변환보다 **좋은 계단**이므로 `f(int)` 가 이긴다.\
  승격 규칙 자체의 정본은 [C 의 03번 형제](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/)다.
- **(3)에서 `f(S)` 가 지는 이유** — **사용자 정의 변환은 계단의 맨 아래**다.\
  표준 변환으로 갈 수 있는 후보가 하나라도 있으면 그쪽이 이긴다.\
  ★ **「정확히 맞는 생성자가 있다」는 근거가 안 된다** — 계단이 더 낮기 때문이다.
- **(4)** 가 보여 주는 것은 사용자 정의 변환이 **맨 아래이되 수단이기는 하다**는 것이다.\
  경쟁자가 없으면 그것이 뽑힌다.
- **네 계단을 좋은 순서로** — 정확 일치 → 승격 → 표준 변환 → 사용자 정의 변환.
- **`__PRETTY_FUNCTION__` 은 표준이 아니다.** gcc·clang 확장이고, 표준의 `__func__` 는 **이름만** 주므로\
  오버로드를 구별하지 못한다. 그래서 6번의 심볼 창이 따로 필요하다.

### 2. ★★ 두 번째 호출이 막힌다 — 기반의 `f(int)` 는 **후보가 아니었다**

**출력**

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

clang 은 문구가 다르되 **같은 자리에서 같은 성격으로** 막는다.

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

**왜 그런가**

- **막히는 것은 `d.f(1)`** 이고 **에러**다(`cc exit=1`). 경고가 아니다.
- **진단이 짚는 함수는 파생의 `Derived::f(const char*)`** 다.\
  `Base::f(int)` 는 언급조차 안 된다 — ★ **후보 집합에 없기 때문이다.**
- 이것이 말하는 것은 **1단계(이름 탐색)에 대한 것**이다.\
  이름 탐색은 **그 이름을 처음 찾은 스코프에서 멈춘다.** 파생에 `f` 가 하나라도 있으면\
  **기반의 `f` 는 전부 가려진다.** 3단계는 그 뒤에 **후보 집합 안에서만** 돈다.
- 고치는 줄은 **`using Base::f;`** 하나다. 고치면 세 호출이 각각 다른 곳으로 간다.

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

- **문구는 다르다.** g++ 는 `invalid conversion from 'int' to 'const char*' [-fpermissive]`,\
  clang 은 `cannot initialize a parameter of type 'const char *' with an rvalue of type 'int'` 다.\
  ★ **clang 쪽에만 `1 error generated.` 꼬리 줄이 있다.**

### 3. ★★ 모호 — 후보 **넷**이 전부 나열된다

**출력**

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

**왜 그런가**

- 에러의 첫 줄은 **`error: call of overloaded 'pick(unsigned int&)' is ambiguous`** 다(`cc exit=1`).
- **후보는 넷 전부** 나열된다. `unsigned int` 에서 `char`·`int`·`long`·`double` 로 가는 변환이\
  **전부 「표준 변환」이라는 같은 계단**이고, 그 안에서 더 낫고 못함이 정해져 있지 않기 때문이다.\
  ★ 「`unsigned int` 니까 `int` 가 가깝겠지」는 **규칙이 아니라 직관**이다.
- **g++ 는 인자를 `pick(unsigned int&)` 라고 적는다** — 소스에는 `pick(u)` 라고 썼다.\
  진단이 **인자를 참조 꼴로 표기**하는 g++ 의 습관이다. 실제 인자는 `unsigned int` 값이다.
- clang 은 같은 자리를 더 짧게 말하되 후보는 **넷 다** 나열한다.

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

- ★ **clang 에만 있는 마지막 줄은 `1 error generated.`** 다. 진단을 옮겨 적을 때 가장 자주 빠지는 줄이고,\
  이 문서가 조립기를 쓰는 이유이기도 하다.
- **고치는 방법 셋** — ① 호출 쪽에서 캐스트해 계단을 하나로(`pick(static_cast<int>(u))`) ·\
  ② `pick(unsigned)` 를 추가해 **정확 일치**를 만든다 · ③ 후보를 줄인다.

### 4. ★★ 다섯 호출이 셋으로 갈린다 — 그리고 최상위 `const` 는 오버로드가 아니다

**출력**

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

**왜 그런가**

| 호출 | 뽑힌 것 | 이유 |
|---|---|---|
| `b.at()` | `int& Box::at()` | 비const 객체에서 비const 멤버가 **정확 일치** |
| `cb.at()` | `const int& Box::at() const` | 비const 멤버는 **실행 가능 후보가 아니다** |
| `g(x)` | `void g(int&)` | 비const lvalue 에 `int&` 가 더 적게 변환한다 |
| `g(cx)` | `void g(const int&)` | `int&` 는 const 를 못 벗긴다 — 후보에서 탈락 |
| `g(42)` | `void g(const int&)` | 임시는 **비const lvalue 참조에 못 묶인다** |

- **`cb.at()` 이 무엇을 보고 떨어뜨리나** — 인자는 없지만 **숨은 `this`** 가 있다.\
  `Box::at()` 은 `Box*`, `Box::at() const` 는 `const Box*` 를 받는다.\
  `const Box` 객체에서 `Box*` 를 만들려면 **const 를 벗겨야** 하고 그런 암묵 변환은 없다.\
  ★ 그래서 **멤버의 `const`** 는 「매개변수가 다른 두 함수」를 만든다.
- **`g(42)` 가 `g(int&)` 로 못 가는 이유** — `42` 는 이름 없는 임시(prvalue)이고\
  **비const lvalue 참조에는 묶이지 않는다.** `const int&` 는 묶인다.\
  값 범주가 참조 오버로드를 가르는 규칙의 정본은 [목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/)다.
- **`void h(int)` 와 `void h(const int)` 를 둘 다 정의하면 재정의 에러**다.

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

  clang 은 같은 자리를 이렇게 말한다.

```text
===== 소스: ex.cpp =====
// 매개변수의 최상위 const 는 오버로드를 못 가른다 — 같은 함수의 재정의가 된다
void h(int)       {}
void h(const int) {}

int main() {}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp:3:6: error: redefinition of 'h'
    3 | void h(const int) {}
      |      ^
ex.cpp:2:6: note: previous definition is here
    2 | void h(int)       {}
      |      ^
1 error generated.
```

### 5. ★ 선언은 통과하고 **호출 줄**에서 모호해진다

**출력**

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

**왜 그런가**

- **걸리는 곳은 호출 줄**(`f(1)`)이지 선언 줄이 아니다.
- **두 선언 자체는 합법**이다 — `void f(int, int)` 와 `void f(int)` 는 **매개변수 개수가 다른** 서로 다른 함수다.\
  기본 인자는 서명의 일부가 아니라 **호출 자리에서 인자를 채워 주는 장치**다.
- `f(1)` 에 대해 **둘 다 실행 가능**하고 **둘 다 정확 일치**라 1등이 둘이 된다.
- **라이브러리 저자에게** — 기존 함수에 기본 인자를 **추가하는 변경**은 선언 시점에 조용하고\
  **쓰는 쪽의 호출에서 터진다.** 「기본 인자는 공짜」가 아니다.\
  ★ 편의 판을 내놓고 싶으면 **인자를 덜 받는 별도 오버로드**를 쓰는 쪽이 안전하다.
- clang 도 같은 성격으로 막는다.

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

### 6. ★★ 통과한다 — 그리고 **셋**만 남는다

**출력**

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

**왜 그런가**

- **`-c` 컴파일은 통과한다**(`cc exit=0`). 정의가 없어도 **선언만 있으면 호출을 만들 수 있고**,\
  없는 정의는 링크 단계의 문제다. 그래서 이 창은 **링크를 안 하고** 쓴다.
- **이름은 셋**이다 — `pick(char)` · `pick(double)` · `pick(int)`.\
  호출이 셋이고 각각 **하나의 서명에 묶였기** 때문이다.
- **안 나오는 것은 `pick(long)`** 이다. 아무 호출도 거기 안 묶였다는 뜻 —\
  ★ **「선언했다」와 「쓰였다」가 다르다는 것을 파일이 증명한다.**
- 셋의 짝은 3번·10번 표와 같다 — `char`→`pick(char)`(정확 일치) · `short`→`pick(int)`(승격) ·\
  `float`→`pick(double)`(부동소수 승격).
- 맹글링을 안 풀면 이렇게 보인다.

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

- **꼬리 글자가 매개변수 타입**이다 — `c`=`char`, `i`=`int`, `d`=`double`.\
  오버로드가 링커에서 충돌하지 않는 이유가 이것이다.
- ★ **그 철자는 표준이 정하지 않는다.** **플랫폼의 C++ ABI** 소관이다.\
  같은 소스를 다른 ABI 에서 컴파일하면 철자가 달라질 수 있다 — 이 문서의 「구현 정의」 칸에 있다.

### 7. 해석이 **인자만** 보기 때문이다

**출력**

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

clang 은 이유를 **문장 하나로** 말한다.

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

**왜 그런가**

- g++ — `error: ambiguating new declaration of 'long int f(int)'` + `note: old declaration 'int f(int)'`.
- clang — `error: functions that differ only in their return type cannot be overloaded`.
- **한 줄짜리 반례** — `f(1);` 이라고만 쓰면 반환값을 버린다.\
  그 자리에서 컴파일러가 `int f(int)` 와 `long f(int)` 중 무엇을 골라야 하는지 **근거가 없다.**\
  대입 대상이 없으니 「무엇을 원하는지」를 물어볼 곳이 없다.
- 그래서 이 규칙이 말하는 것은 「**해석은 인자만 보고 한다**」이다.\
  대입 대상의 타입도, 문맥도 안 본다.\
  ★ 예외처럼 보이는 자리가 하나 있다 — **변환 연산자**는 「어느 타입으로 가고 싶은가」가 문맥에서 오지만,\
  그것은 오버로드 해석이 아니라 **변환 함수 선택**이다([목록의 **24번 주제**](../24-explicit-and-converting-constructors/)).

### 8. 참조 쪽만 오버로드가 된다

**왜 그런가**

- **`void h(int)` / `void h(const int)` 는 오버로드가 아니다** — 같은 함수의 재선언이다(4번 블록).
- **`void g(int&)` / `void g(const int&)` 는 오버로드다** — 4번의 출력이 셋으로 갈린 것이 그 증거다.
- **안 되는 쪽의 이유** — 값으로 받는 매개변수는 **어차피 복사본**이다.\
  복사본을 함수 안에서 고치든 말든 **호출하는 쪽에서는 아무 차이가 없다.**\
  그래서 최상위 `const` 는 **서명에서 무시된다.**
- **되는 쪽의 이유** — `const int&` 의 `const` 는 최상위가 아니라 **가리키는 대상**에 붙은 것이다.\
  「원본을 안 건드린다」는 **호출 쪽에 보이는 약속**이라 서명의 일부가 된다.
- **멤버 함수 뒤의 `const` 는 되는 쪽에 가깝다.** 숨은 `this` 가 `Box*` 냐 `const Box*` 냐가 갈리고,\
  그것은 **가리키는 대상의 const** 다.

### 9. 「후보가 없다」일 때 clang 이 압도적이고, 「모호하다」일 때는 비긴다

**출력 — 실행 가능 후보가 하나도 없을 때 (clang)**

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

**출력 — 같은 소스 (g++)**

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

**왜 그런가**

- **clang 이 더 준다.** 후보 **셋 전부**를 나열하고 각각에 **탈락 사유**를 붙인다 —\
  `requires 2 arguments, but 1 was provided`(개수 불일치) ·\
  `no known conversion from 'int' to 'char *' for 1st argument`(변환 없음) ·\
  `no known conversion from 'int' to 'Big' for 1st argument`.\
  ★ **이 세 줄이 「실행 가능 후보」의 정의 그대로다.**
- **g++ 는 후보를 나열하지 않는다.** 하나를 골라 「그것으로의 변환이 안 된다」고만 말한다.\
  `-fpermissive` 를 언급하는 것은 「이 변환은 확장으로 봐줄 수도 있는 종류」라는 뜻이지 **후보 목록이 아니다.**
- **모호할 때는 갈리지 않는다** — 3번에서 둘 다 후보 넷을 전부 나열했다.\
  차이는 clang 이 `1 error generated.` 꼬리를 붙이는 것뿐이다.
- **두 컴파일러에 다 던진 이유** — ★ **진단은 구현이고, 구현마다 보여 주는 양이 다르다.**\
  규칙이 같다는 것은 **둘의 선택이 같았다**는 것으로 확인하고,\
  교재로 쓸 후보 목록은 **더 많이 말해 주는 쪽**에서 얻는다.

### 10. 정확 일치는 **둘**뿐이다

**출력**

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

**왜 그런가**

| 인자 | 뽑힌 것 | 계단 |
|---|---|---|
| `char` | `f(char)` | **정확 일치** |
| `signed char` | `f(int)` | 승격 |
| `unsigned char` | `f(int)` | 승격 |
| `short` | `f(int)` | 승격 |
| `bool` | `f(int)` | 승격 |
| `int` | `f(int)` | **정확 일치** |
| `float` | `f(double)` | 승격(부동소수) |

- **정확 일치는 `char` 와 `int` 둘**이다. 후보에 그 타입이 그대로 있기 때문이다.
- ★★ **`char`·`signed char`·`unsigned char` 는 서로 다른 세 타입**이다.\
  `char` 만 `f(char)` 로 가고 나머지 둘은 **`f(int)` 로 승격**된다.\
  C 갈래가 「`char` 의 부호는 구현 정의」라고 한 것과 **다른 층의 이야기**다 —\
  부호와 무관하게 **타입 자체가 셋**이다.
- **`f(long)` 을 뽑으려면 `long` 을 넘겨야 한다.** 이 일곱 중에는 거기로 가는 것이 하나도 없다.\
  `int`→`long` 은 표준 변환인데 `f(int)` 라는 **정확 일치**가 있어서 진다.
- **`float`→`double` 에 붙은 이름**은 「**부동소수 승격**」이다.\
  승격이라 `f(long)` 으로 가는 표준 변환을 이긴다.

### 11. 이 주제의 지도

**왜 그런가**

- **이 주제의 선택은 컴파일 시간**에 끝난다. 실행 중에 고르는 것은 **가상 함수 디스패치**이고\
  정본은 [목록의 **19번 주제**](../19-inheritance-virtual-functions-override-final/)다. 둘은 **같은 「고르기」라는 낱말을 쓰는 다른 기계**다.
- **정수 승격의 정본**은 C 갈래의\
  [`03-integer-promotion-and-usual-arithmetic-conversions/`](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/)다.\
  여기는 **그 승격이 「한 계단」으로 등급이 매겨져 겨루는 자리**만 다뤘다.
- **네임스페이스 이름 탐색과 ADL** 은 [목록의 **06번 주제**](../06-namespaces-and-adl/)다.\
  이 주제의 1단계가 **클래스 안에서** 한 일을, 그쪽은 **네임스페이스에서** 한다.
- **`enum class`** 는 **암묵 정수 변환을 끊어** 후보 집합에서 엉뚱한 것이 실행 가능해지는 것을 막는다 —\
  [**02번 형제**](../02-enum-class-and-scoped-enumerations/).
- **`{}` 로 생성자를 부를 때의 특칙**(`initializer_list` 가 다른 생성자를 이긴다)은\
  [**04번 형제**](../04-brace-initialization-narrowing-and-initializer-list/)다.
- **sanitizer 를 한 번도 안 쓴 이유** — ★ 이 주제가 만드는 실패는 **전부 컴파일 에러**다.\
  UB 도 없고 런타임 오작동도 없다. **런타임 도구가 볼 것이 없다.**

---

## 실행 검증

| 프로그램 (`ex.cpp`) | 무엇을 확인했나 | 어느 명령으로 돌렸나 |
|---|---|---|
| 네 계단 고립 | `f(char)`/`f(int)`/`f(double)`/`f(S)` — 네 계단이 예상대로 | g++ · clang `-std=c++20 -Wall -Wextra -pedantic` |
| 이름 가리기 | `d.f(1)` 이 **에러** · 기반의 `f(int)` 가 **언급조차 안 됨** | g++ · clang |
| `using Base::f;` | **통과** — 세 호출이 셋으로 갈림 | g++ |
| 실행 가능 후보 없음 | ★ clang 이 **후보 3 + 탈락 사유 3** · g++ 는 **나열 안 함** | g++ · clang |
| 모호(`unsigned`) | **후보 4** 를 둘 다 나열 · clang 만 `1 error generated.` | g++ · clang |
| `const` 세 자리 | 다섯 호출이 **셋**으로 갈림 | g++ |
| 최상위 `const` 정의 둘 | **redefinition 에러** | g++ · clang |
| 반환 타입만 다름 | g++ `ambiguating new declaration` · clang `differ only in their return type` | g++ · clang |
| 기본 인자 충돌 | **선언은 통과 · 호출 줄에서 모호** | g++ · clang |
| ★ `nm -uC` (정의 없음) | **심볼 3개** · `pick(long)` **없음** · `-u` 는 `_Z4pickc`/`_Z4pickd`/`_Z4picki` | g++ `-c` + `nm` |
| 산술 타입 일곱 | 정확 일치 **2**, 나머지 **승격 5** | g++ |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 / clang 18.1.3)에서만** 그렇다.

- **맹글링된 심볼의 철자**(`_Z4pickc`) — 플랫폼의 C++ ABI 소관. 표준이 아니다.
- **진단 문구 전부** — `ambiguating new declaration`·`candidate:`·`candidate function not viable:` 등.
- **후보를 몇 개 나열하나** — clang 은 「후보 없음」에서 전수, g++ 는 「모호」에서만 전수.
- **`1 error generated.` 꼬리 줄** — clang 에만 있다.
- `__PRETTY_FUNCTION__` 의 문자열 형식(`void step1::f(char)`) — gcc·clang 확장.
- `nm` 이 `U` 로 찍는 표기와 `-C` 의 디맹글 결과 — binutils 구현.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- 세 단계의 순서 · 이름 가리기 · 네 계단의 대소 · 모호하면 에러 · 반환 타입과 최상위 `const` 가 서명이 아닌 것.
- ★ **두 컴파일러가 7건 전부 같은 오버로드를 골랐다** — 규칙이 표준이라는 것과 일관된 관찰이다.\
  단 **「같았다」는 관찰이고 「같아야 한다」는 표준이다.** 둘을 같은 것으로 적지 않는다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — 템플릿이 후보에 섞였을 때의 순위(목록의 **31번 주제**) ·\
  ADL 이 후보를 늘리는 것([목록의 **06번 주제**](../06-namespaces-and-adl/)) · `=delete` 로 후보를 죽이는 것 ·\
  인자가 **둘 이상**일 때의 비교 규칙 · 변환 연산자로 만든 사용자 정의 변환(생성자 쪽만 던졌다).
- **못 잰 것** — 다른 ABI(예: MSVC)의 맹글링 철자. 이 머신에는 Itanium ABI 하나뿐이다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- 진단 문구 전부 — 특히 g++ 가 「후보 없음」에서 후보를 나열하게 바뀌었는지.
- clang 의 `1 error generated.` 꼬리와 `note:` 줄 개수.
- `__PRETTY_FUNCTION__` 형식.
