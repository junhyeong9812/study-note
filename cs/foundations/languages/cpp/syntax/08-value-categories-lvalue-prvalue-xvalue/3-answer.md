# cpp/syntax/08 — 값 범주 — lvalue·prvalue·xvalue — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이라 질문 쪽 발췌와 어긋날 수 있다 —\
> 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★★ 이 주제의 **주력 창은 의도적 타입 에러**(`TypeOf<T>`)다. 읽을 것은 **꺾쇠 안**이고 그 줄이 곧 답이다.
> **읽는 법** — 진단의 **열 번호와 문구는 흔들리는 칸**이다. 근거로 쓰는 것은 **꺾쇠 안의 타입**과\
> **생성자·소멸자 호출 횟수**와 **`cc exit`/`run exit`** 다.\
> ★ UB 는 이 주제에 **없다** — 범주 위반은 전부 컴파일 에러였다. 9번만 **플래그로 낮춘** 자리다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `int` 면 prvalue · `int&` 면 lvalue · `int&&` 면 xvalue

**출력**

```text
===== 소스: vcat01.cpp =====
// decltype((식)) 로 값 범주를 직접 묻는다 — T 면 prvalue, T& 면 lvalue, T&& 면 xvalue
#include <utility>

template <class T> struct TypeOf;   // 선언만 — 정의가 없다

struct S { int m; };

int  byval();     // 값을 돌려준다
int& bylref();    // lvalue 참조를 돌려준다
int&& byrref();   // rvalue 참조를 돌려준다

int main() {
    int i = 0, j = 0;
    int arr[3]{};
    S s{0};

    TypeOf<decltype((42))>                  v01;   // 정수 리터럴
    TypeOf<decltype(("abc"))>               v02;   // 문자열 리터럴
    TypeOf<decltype(('c'))>                 v03;   // 문자 리터럴
    TypeOf<decltype((i))>                   v04;   // 변수 이름
    TypeOf<decltype((i + 1))>               v05;   // 계산 식
    TypeOf<decltype((++i))>                 v06;   // 전위 증가
    TypeOf<decltype((i++))>                 v07;   // 후위 증가
    TypeOf<decltype((byval()))>             v08;   // 값 반환 호출
    TypeOf<decltype((bylref()))>            v09;   // T& 반환 호출
    TypeOf<decltype((byrref()))>            v10;   // T&& 반환 호출
    TypeOf<decltype((std::move(i)))>        v11;   // std::move
    TypeOf<decltype((static_cast<int&&>(i)))> v12; // 같은 캐스트를 손으로
    TypeOf<decltype((arr))>                 v13;   // 배열 이름
    TypeOf<decltype((arr[0]))>              v14;   // 첨자
    TypeOf<decltype((s.m))>                 v15;   // lvalue 의 멤버
    TypeOf<decltype((S{}))>                 v16;   // 임시 객체
    TypeOf<decltype((S{}.m))>               v17;   // prvalue 의 멤버
    TypeOf<decltype((std::move(s).m))>      v18;   // xvalue 의 멤버
    TypeOf<decltype((i ? i : j))>           v19;   // 조건 식
    TypeOf<decltype(("abc"[0]))>            v20;   // 문자열 리터럴의 첨자
}
===== g++ -std=c++20 -Wall -Wextra -pedantic vcat01.cpp -o ex 2>&1 | grep 'incomplete type' (cc exit=1) =====
vcat01.cpp:17:45: error: aggregate ‘TypeOf<int> v01’ has incomplete type and cannot be defined
vcat01.cpp:18:45: error: aggregate ‘TypeOf<const char (&)[4]> v02’ has incomplete type and cannot be defined
vcat01.cpp:19:45: error: aggregate ‘TypeOf<char> v03’ has incomplete type and cannot be defined
vcat01.cpp:20:45: error: aggregate ‘TypeOf<int&> v04’ has incomplete type and cannot be defined
vcat01.cpp:21:45: error: aggregate ‘TypeOf<int> v05’ has incomplete type and cannot be defined
vcat01.cpp:22:45: error: aggregate ‘TypeOf<int&> v06’ has incomplete type and cannot be defined
vcat01.cpp:23:45: error: aggregate ‘TypeOf<int> v07’ has incomplete type and cannot be defined
vcat01.cpp:24:45: error: aggregate ‘TypeOf<int> v08’ has incomplete type and cannot be defined
vcat01.cpp:25:45: error: aggregate ‘TypeOf<int&> v09’ has incomplete type and cannot be defined
vcat01.cpp:26:45: error: aggregate ‘TypeOf<int&&> v10’ has incomplete type and cannot be defined
vcat01.cpp:27:45: error: aggregate ‘TypeOf<int&&> v11’ has incomplete type and cannot be defined
vcat01.cpp:28:47: error: aggregate ‘TypeOf<int&&> v12’ has incomplete type and cannot be defined
vcat01.cpp:29:45: error: aggregate ‘TypeOf<int (&)[3]> v13’ has incomplete type and cannot be defined
vcat01.cpp:30:45: error: aggregate ‘TypeOf<int&> v14’ has incomplete type and cannot be defined
vcat01.cpp:31:45: error: aggregate ‘TypeOf<int&> v15’ has incomplete type and cannot be defined
vcat01.cpp:32:45: error: aggregate ‘TypeOf<S> v16’ has incomplete type and cannot be defined
vcat01.cpp:33:45: error: aggregate ‘TypeOf<int&&> v17’ has incomplete type and cannot be defined
vcat01.cpp:34:45: error: aggregate ‘TypeOf<int&&> v18’ has incomplete type and cannot be defined
vcat01.cpp:35:45: error: aggregate ‘TypeOf<int&> v19’ has incomplete type and cannot be defined
vcat01.cpp:36:45: error: aggregate ‘TypeOf<const char&> v20’ has incomplete type and cannot be defined
```

**왜 그런가**

| 줄 | 식 | 찍힌 타입 | 범주 | 규칙 |
|---|---|---|---|---|
| v01 | `42` | `int` | prvalue | 리터럴은 값이다 |
| v02 | `"abc"` | ★ `const char (&)[4]` | ★ **lvalue** | **문자열 리터럴만 객체다**(4번) |
| v03 | `'c'` | `char` | prvalue | — |
| v04 | `i` | `int&` | lvalue | 이름 있는 객체 |
| v05 | `i + 1` | `int` | prvalue | 계산해서 나온 값 |
| v06 | `++i` | `int&` | lvalue | 그 자리를 돌려준다 |
| v07 | `i++` | `int` | prvalue | **복사본**을 돌려준다 |
| v08 | `byval()` | `int` | prvalue | 값 반환 |
| v09 | `bylref()` | `int&` | lvalue | `T&` 반환 |
| v10 | `byrref()` | ★ `int&&` | ★ **xvalue** | `T&&` 반환 |
| v11 | `std::move(i)` | `int&&` | xvalue | ★ v10·v12 와 **같다** |
| v12 | `static_cast<int&&>(i)` | `int&&` | xvalue | ★ `std::move` 가 하는 일이 이것뿐이다 |
| v13 | `arr` | `int (&)[3]` | lvalue | ★ **감쇠하지 않는다** |
| v14 | `arr[0]` | `int&` | lvalue | 첨자는 그 자리 |
| v15 | `s.m` | `int&` | lvalue | lvalue 의 멤버 |
| v16 | `S{}` | `S` | prvalue | 임시 객체 |
| v17 | ★ `S{}.m` | ★ `int&&` | ★ **xvalue** | **prvalue 의 멤버는 xvalue** |
| v18 | `std::move(s).m` | `int&&` | xvalue | xvalue 의 멤버도 xvalue |
| v19 | `i ? i : j` | `int&` | lvalue | 양쪽이 같은 lvalue 면 lvalue |
| v20 | `"abc"[0]` | `const char&` | lvalue | 배열의 첨자 |

- ★★★ **`v10`·`v11`·`v12` 가 한 글자도 다르지 않다.** 「`std::move` 는 캐스트일 뿐」의 첫 증거이고,\
  그 정본은 [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)다.
- ★★ **`v16` 과 `v17` 이 갈린다** — `S{}` 자체는 prvalue 인데 **멤버를 꺼내는 순간 물질화**되어 xvalue 가 된다.\
  ★ 「물질화」의 근거는 5번에 있다.
- ★★ **`v02` 만 참조로 찍혔다** — 리터럴 중 **문자열만 lvalue** 다.
- ★ **`v13` 이 `int (&)[3]`** — `decltype` 은 배열을 **포인터로 감쇠시키지 않는다**. 그 규칙의 정본은 형제 [`05번`](../05-auto-and-decltype-type-deduction/)이다.

같은 소스를 clang 으로 던진 것도 **판정이 한 칸도 다르지 않다.**

```text
===== 소스: vcat01.cpp =====
// decltype((식)) 로 값 범주를 직접 묻는다 — T 면 prvalue, T& 면 lvalue, T&& 면 xvalue
#include <utility>

template <class T> struct TypeOf;   // 선언만 — 정의가 없다

struct S { int m; };

int  byval();     // 값을 돌려준다
int& bylref();    // lvalue 참조를 돌려준다
int&& byrref();   // rvalue 참조를 돌려준다

int main() {
    int i = 0, j = 0;
    int arr[3]{};
    S s{0};

    TypeOf<decltype((42))>                  v01;   // 정수 리터럴
    TypeOf<decltype(("abc"))>               v02;   // 문자열 리터럴
    TypeOf<decltype(('c'))>                 v03;   // 문자 리터럴
    TypeOf<decltype((i))>                   v04;   // 변수 이름
    TypeOf<decltype((i + 1))>               v05;   // 계산 식
    TypeOf<decltype((++i))>                 v06;   // 전위 증가
    TypeOf<decltype((i++))>                 v07;   // 후위 증가
    TypeOf<decltype((byval()))>             v08;   // 값 반환 호출
    TypeOf<decltype((bylref()))>            v09;   // T& 반환 호출
    TypeOf<decltype((byrref()))>            v10;   // T&& 반환 호출
    TypeOf<decltype((std::move(i)))>        v11;   // std::move
    TypeOf<decltype((static_cast<int&&>(i)))> v12; // 같은 캐스트를 손으로
    TypeOf<decltype((arr))>                 v13;   // 배열 이름
    TypeOf<decltype((arr[0]))>              v14;   // 첨자
    TypeOf<decltype((s.m))>                 v15;   // lvalue 의 멤버
    TypeOf<decltype((S{}))>                 v16;   // 임시 객체
    TypeOf<decltype((S{}.m))>               v17;   // prvalue 의 멤버
    TypeOf<decltype((std::move(s).m))>      v18;   // xvalue 의 멤버
    TypeOf<decltype((i ? i : j))>           v19;   // 조건 식
    TypeOf<decltype(("abc"[0]))>            v20;   // 문자열 리터럴의 첨자
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 vcat01.cpp -o ex 2>&1 | grep -E 'undefined template|warning:|generated' (cc exit=1) =====
vcat01.cpp:17:45: error: implicit instantiation of undefined template 'TypeOf<int>'
vcat01.cpp:18:45: error: implicit instantiation of undefined template 'TypeOf<const char (&)[4]>'
vcat01.cpp:19:45: error: implicit instantiation of undefined template 'TypeOf<char>'
vcat01.cpp:20:45: error: implicit instantiation of undefined template 'TypeOf<int &>'
vcat01.cpp:21:45: error: implicit instantiation of undefined template 'TypeOf<int>'
vcat01.cpp:22:21: warning: expression with side effects has no effect in an unevaluated context [-Wunevaluated-expression]
vcat01.cpp:22:45: error: implicit instantiation of undefined template 'TypeOf<int &>'
vcat01.cpp:23:21: warning: expression with side effects has no effect in an unevaluated context [-Wunevaluated-expression]
vcat01.cpp:23:45: error: implicit instantiation of undefined template 'TypeOf<int>'
vcat01.cpp:24:45: error: implicit instantiation of undefined template 'TypeOf<int>'
vcat01.cpp:25:45: error: implicit instantiation of undefined template 'TypeOf<int &>'
vcat01.cpp:26:45: error: implicit instantiation of undefined template 'TypeOf<int &&>'
vcat01.cpp:27:45: error: implicit instantiation of undefined template 'TypeOf<int &&>'
vcat01.cpp:28:47: error: implicit instantiation of undefined template 'TypeOf<int &&>'
vcat01.cpp:29:45: error: implicit instantiation of undefined template 'TypeOf<int (&)[3]>'
vcat01.cpp:30:45: error: implicit instantiation of undefined template 'TypeOf<int &>'
vcat01.cpp:31:45: error: implicit instantiation of undefined template 'TypeOf<int &>'
vcat01.cpp:32:45: error: implicit instantiation of undefined template 'TypeOf<S>'
vcat01.cpp:33:45: error: implicit instantiation of undefined template 'TypeOf<int &&>'
vcat01.cpp:34:45: error: implicit instantiation of undefined template 'TypeOf<int &&>'
vcat01.cpp:35:45: error: implicit instantiation of undefined template 'TypeOf<int &>'
vcat01.cpp:36:45: error: implicit instantiation of undefined template 'TypeOf<const char &>'
2 warnings and 20 errors generated.
```

- ★★ **clang 만 경고 2건** — `++i`·`i++` 를 `decltype` 안에 넣은 자리다(`-Wunevaluated-expression`).\
  **g++ 는 0건**이다. 7번이 그 경고가 옳다는 것을 실행으로 보인다.
- ★ **clang 은 기본 20개에서 멈춘다** — 스무 줄을 다 보려고 `-ferror-limit=0` 을 붙였고, 그 명령이 배너에 있다.

### 2. ★★ prvalue 와 xvalue 가 같은 칸으로 간다 — `const` 가 붙으면 안 간다

**출력**

```text
===== 소스: vcat02.cpp =====
// 값 범주가 오버로드를 가른다 — 같은 이름에 세 후보를 두고 다섯 가지 식으로 부른다
#include <cstdio>
#include <utility>

void f(int&)       { std::puts("f(int&)"); }
void f(const int&) { std::puts("f(const int&)"); }
void f(int&&)      { std::puts("f(int&&)"); }

void g(const int&) { std::puts("g(const int&)"); }
void g(int&&)      { std::puts("g(int&&)"); }

void h(const int&) { std::puts("h(const int&)"); }

int main() {
    int i = 0;
    const int ci = 0;

    std::puts("[1] 후보 셋: f(int&) / f(const int&) / f(int&&)");
    std::printf("  %-26s -> ", "f(i)          lvalue");        f(i);
    std::printf("  %-26s -> ", "f(ci)         const lvalue");  f(ci);
    std::printf("  %-26s -> ", "f(42)         prvalue");       f(42);
    std::printf("  %-26s -> ", "f(move(i))    xvalue");        f(std::move(i));
    std::printf("  %-26s -> ", "f(move(ci))   const xvalue");  f(std::move(ci));

    std::puts("[2] 후보 둘: g(const int&) / g(int&&)");
    std::printf("  %-26s -> ", "g(i)          lvalue");        g(i);
    std::printf("  %-26s -> ", "g(42)         prvalue");       g(42);
    std::printf("  %-26s -> ", "g(move(i))    xvalue");        g(std::move(i));

    std::puts("[3] 후보 하나: h(const int&)");
    std::printf("  %-26s -> ", "h(i)          lvalue");        h(i);
    std::printf("  %-26s -> ", "h(42)         prvalue");       h(42);
    std::printf("  %-26s -> ", "h(move(i))    xvalue");        h(std::move(i));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic vcat02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] 후보 셋: f(int&) / f(const int&) / f(int&&)
  f(i)          lvalue       -> f(int&)
  f(ci)         const lvalue -> f(const int&)
  f(42)         prvalue      -> f(int&&)
  f(move(i))    xvalue       -> f(int&&)
  f(move(ci))   const xvalue -> f(const int&)
[2] 후보 둘: g(const int&) / g(int&&)
  g(i)          lvalue       -> g(const int&)
  g(42)         prvalue      -> g(int&&)
  g(move(i))    xvalue       -> g(int&&)
[3] 후보 하나: h(const int&)
  h(i)          lvalue       -> h(const int&)
  h(42)         prvalue      -> h(const int&)
  h(move(i))    xvalue       -> h(const int&)
```

**왜 그런가**

| 부른 식 | 범주 | `[1]` 후보 셋 | `[2]` 후보 둘 | `[3]` 후보 하나 |
|---|---|---|---|---|
| `f(i)` | lvalue | `f(int&)` | `g(const int&)` | `h(const int&)` |
| `f(ci)` | const lvalue | `f(const int&)` | — | — |
| `f(42)` | prvalue | ★ `f(int&&)` | `g(int&&)` | `h(const int&)` |
| `f(std::move(i))` | xvalue | ★ `f(int&&)` | `g(int&&)` | `h(const int&)` |
| `f(std::move(ci))` | const xvalue | ★ `f(const int&)` | — | — |

- ★★★ **`f(42)` 와 `f(std::move(i))` 가 같은 줄로 간다.** 둘을 묶은 이름이 **rvalue** 이고 **`T&&` 가 그 칸을 받는다.**
- ★★★ **`f(std::move(ci))` 가 `f(const int&)` 로 떨어진다.** `std::move(ci)` 의 타입이 `const int&&` 라\
  **`int&&` 후보가 아예 후보가 못 된다.**\
  ★ 클래스 타입이면 이 자리가 **조용한 복사**가 된다 — 실측은 [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)에 있다.
- ★★ **`[3]` 은 셋 다 받는다** — `const T&` 가 네 칸을 다 받는 유일한 손이다(3번의 격자).\
  그래서 **오버로드를 하나만 둘 거면 `const T&`** 가 기본값이 된다([목록의 **11번 주제**](../11-choosing-parameter-passing/)).
- ★ 오버로드 해석의 **전체 순서**는 형제 [`01번`](../01-function-overloading-and-overload-resolution/)이 정본이다. 여기서는 **범주가 후보를 거르는 한 겹**만 봤다.

### 3. ★ 여섯 개 — g++ 도 clang 도 여섯

**출력**

```text
===== 소스: vcat03.cpp =====
// 범주가 막는 것 — 여섯 줄이 전부 에러다(주석의 OK 줄은 통과한다)
#include <utility>

int main() {
    int i = 0;
    const int ci = 0;

    const int& ok1 = 42;              // OK — const lvalue 참조는 prvalue 를 받는다
    int&&      ok2 = std::move(i);    // OK — rvalue 참조는 xvalue 를 받는다
    auto*      ok3 = &"abc";          // OK — 문자열 리터럴은 lvalue 라 주소가 있다
    (void)ok1; (void)ok2; (void)ok3;

    int&  e1 = 42;                    // (1) 비-const lvalue 참조 <- prvalue
    int&& e2 = i;                     // (2) rvalue 참조 <- lvalue
    int&  e3 = ci;                    // (3) const 를 버린다
    int&& e4 = std::move(ci);         // (4) int&& <- const int&&
    int*  e5 = &42;                   // (5) prvalue 의 주소
    42 = i;                           // (6) prvalue 에 대입
    (void)e1; (void)e2; (void)e3; (void)e4; (void)e5;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic vcat03.cpp -o ex 2>&1 | grep 'error:' (cc exit=1) =====
vcat03.cpp:13:16: error: cannot bind non-const lvalue reference of type ‘int&’ to an rvalue of type ‘int’
vcat03.cpp:14:16: error: cannot bind rvalue reference of type ‘int&&’ to lvalue of type ‘int’
vcat03.cpp:15:16: error: binding reference of type ‘int&’ to ‘const int’ discards qualifiers
vcat03.cpp:16:25: error: binding reference of type ‘int&&’ to ‘std::remove_reference<const int&>::type’ {aka ‘const int’} discards qualifiers
vcat03.cpp:17:17: error: lvalue required as unary ‘&’ operand
vcat03.cpp:18:5: error: lvalue required as left operand of assignment
```

**왜 그런가**

```text
                    lvalue    const lvalue   prvalue   xvalue
   T&         <-      OK          X            X         X
   const T&   <-      OK          OK           OK        OK     ★ 넷 다
   T&&        <-      X           X            OK        OK
   const T&&  <-      X           X            OK        OK
```

| 줄 | 왜 막히나 |
|---|---|
| `int& e1 = 42;` | 비-const lvalue 참조는 **rvalue 를 못 받는다** |
| `int&& e2 = i;` | rvalue 참조는 **lvalue 를 못 받는다** |
| `int& e3 = ci;` | `const` 를 **버리게 된다** |
| `int&& e4 = std::move(ci);` | ★ `std::move` 는 **`const` 를 떼지 않는다** — `const int&&` 가 나온다 |
| `int* e5 = &42;` | prvalue 에는 **주소가 없다** |
| `42 = i;` | prvalue 는 **대입의 왼쪽**에 못 온다 |

- ★★ **`ok3`(`&"abc"`)이 통과하는 것이 대조군**이다 — 같은 「리터럴」인데 **문자열만 주소가 있다**(4번).
- ★★★ **`const T&` 만 네 칸을 다 받는다.** 그 대가는 「**훔칠 수 없다**」는 것이고, 그래서 11번이 필요해진다.

clang 도 **여섯 개 그대로**다. 문구만 다르다.

```text
===== 소스: vcat03.cpp =====
// 범주가 막는 것 — 여섯 줄이 전부 에러다(주석의 OK 줄은 통과한다)
#include <utility>

int main() {
    int i = 0;
    const int ci = 0;

    const int& ok1 = 42;              // OK — const lvalue 참조는 prvalue 를 받는다
    int&&      ok2 = std::move(i);    // OK — rvalue 참조는 xvalue 를 받는다
    auto*      ok3 = &"abc";          // OK — 문자열 리터럴은 lvalue 라 주소가 있다
    (void)ok1; (void)ok2; (void)ok3;

    int&  e1 = 42;                    // (1) 비-const lvalue 참조 <- prvalue
    int&& e2 = i;                     // (2) rvalue 참조 <- lvalue
    int&  e3 = ci;                    // (3) const 를 버린다
    int&& e4 = std::move(ci);         // (4) int&& <- const int&&
    int*  e5 = &42;                   // (5) prvalue 의 주소
    42 = i;                           // (6) prvalue 에 대입
    (void)e1; (void)e2; (void)e3; (void)e4; (void)e5;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic vcat03.cpp -o ex 2>&1 | grep -E 'error:|generated' (cc exit=1) =====
vcat03.cpp:13:11: error: non-const lvalue reference to type 'int' cannot bind to a temporary of type 'int'
vcat03.cpp:14:11: error: rvalue reference to type 'int' cannot bind to lvalue of type 'int'
vcat03.cpp:15:11: error: binding reference of type 'int' to value of type 'const int' drops 'const' qualifier
vcat03.cpp:16:11: error: binding reference of type 'int' to value of type 'typename std::remove_reference<const int &>::type' (aka 'const int') drops 'const' qualifier
vcat03.cpp:17:16: error: cannot take the address of an rvalue of type 'int'
vcat03.cpp:18:8: error: expression is not assignable
6 errors generated.
```

### 4. ★ `sizeof` 는 4 · `a == b` 는 1 — 그런데 뒤엣것은 근거가 아니다

**출력**

```text
===== 소스: vcat04.cpp =====
// 문자열 리터럴만 lvalue 다 — 주소가 있고, 배열 참조에 묶이고, 크기가 있다
#include <cstdio>

int main() {
    const char* a = "abc";
    const char* b = "abc";
    const char (&r)[4] = "abc";       // 배열 참조에 묶인다 — lvalue 라는 증거

    std::printf("sizeof(\"abc\")   = %zu\n", sizeof("abc"));
    std::printf("&\"abc\" 를 얻는다 : %s\n", (&"abc") ? "된다" : "안 된다");
    std::printf("a == b          : %d   (같은 리터럴이 한 덩어리로 합쳐졌나 — 미명시)\n",
                static_cast<int>(a == b));
    std::printf("&r[0] == a      : %d\n", static_cast<int>(&r[0] == a));
    std::printf("r[0] r[1] r[2]  = %c %c %c\n", r[0], r[1], r[2]);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic vcat04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof("abc")   = 4
&"abc" 를 얻는다 : 된다
a == b          : 1   (같은 리터럴이 한 덩어리로 합쳐졌나 — 미명시)
&r[0] == a      : 1
r[0] r[1] r[2]  = a b c
```

**왜 그런가**

- ★★ **`sizeof("abc")` 가 4** — 문자열 리터럴은 **`const char[4]` 배열**이다(널 종료 문자 포함).\
  「배열이다」의 정본은 C 갈래 [`20-null-terminated-strings-and-string-literals/`](../../../c/syntax/20-null-terminated-strings-and-string-literals/)다.
- ★★ **배열이니 객체이고, 객체이니 lvalue 다.** `const char (&)[4]` 에 묶이는 것이 그 증거이고,\
  `&"abc"` 가 되는 것도 같은 이유다.
- ★★★ **`a == b` 가 1 이지만 이 칸은 미명시다.** 표준은 「같은 내용의 리터럴이 구별되는 객체인지」를 **정하지 않는다.**\
  ★ 그래서 이 문서는 그 칸을 머리말의 **흔들리는 칸**에 넣었다 — **출력이 1 이라고 「합쳐진다」로 적지 않는다.**
- ★ 나머지 리터럴(`42`·`'c'`)은 전부 prvalue 라 **주소가 없다**(3번의 `e5`).
- ★ **`char* p = "abc";` 는 C++11 부터 ill-formed** 인데 컴파일이 **통과한다** — 그 정본은 [목록의 **10번 주제**](../10-const-correctness/)다.

### 5. ★★ 셋 다 `ctor` 한 번 — 그리고 플래그가 아무 일도 안 한다

**출력**

```text
===== 소스: vcat05.cpp =====
// prvalue 는 객체가 아니다 — C++17 의 「물질화」를 생성자 로그로 센다
#include <cstdio>

struct Noisy {
    int id;
    explicit Noisy(int i) : id(i) { std::printf("    ctor(%d)\n", id); }
    Noisy(const Noisy& o) : id(o.id) { std::printf("    copy(%d)\n", id); }
    Noisy(Noisy&& o) noexcept : id(o.id) { std::printf("    move(%d)\n", id); }
    ~Noisy() { std::printf("    dtor(%d)\n", id); }
};

Noisy make(int i) { return Noisy(i); }

int main() {
    std::puts("[1] Noisy a = make(1);");
    Noisy a = make(1);
    std::puts("[2] Noisy b = Noisy(Noisy(Noisy(2)));");
    Noisy b = Noisy(Noisy(Noisy(2)));
    std::puts("[3] Noisy c = make(3); 를 인자로 넘기면");
    [](Noisy) { std::puts("    함수 안"); }(make(3));
    std::puts("[4] main 끝 — 여기서 a, b 가 죽는다");
    (void)a; (void)b;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic vcat05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] Noisy a = make(1);
    ctor(1)
[2] Noisy b = Noisy(Noisy(Noisy(2)));
    ctor(2)
[3] Noisy c = make(3); 를 인자로 넘기면
    ctor(3)
    함수 안
    dtor(3)
[4] main 끝 — 여기서 a, b 가 죽는다
    dtor(2)
    dtor(1)
```

**왜 그런가**

- ★★★ **`Noisy(Noisy(Noisy(2)))` 가 생성자 한 번**이다. C++17 부터 **prvalue 는 객체가 아니라** 「**초기화하는 방법**」이라,\
  괄호를 몇 겹 씌워도 **초기화될 객체는 하나**뿐이다.
- ★★ **`[3]` 의 `dtor(3)` 은 함수가 끝난 뒤**에 찍힌다 — 인자로 만든 임시는 **그 문장 끝**에 죽는다.
- ★ **`[4]` 뒤에 `dtor(2) dtor(1)`** — 지역은 **선언의 역순**으로 죽는다.

같은 프로그램에 **복사를 끄는 플래그**를 붙여도 출력이 **한 글자도 안 바뀐다.**

```text
===== 소스: vcat05.cpp =====
// prvalue 는 객체가 아니다 — C++17 의 「물질화」를 생성자 로그로 센다
#include <cstdio>

struct Noisy {
    int id;
    explicit Noisy(int i) : id(i) { std::printf("    ctor(%d)\n", id); }
    Noisy(const Noisy& o) : id(o.id) { std::printf("    copy(%d)\n", id); }
    Noisy(Noisy&& o) noexcept : id(o.id) { std::printf("    move(%d)\n", id); }
    ~Noisy() { std::printf("    dtor(%d)\n", id); }
};

Noisy make(int i) { return Noisy(i); }

int main() {
    std::puts("[1] Noisy a = make(1);");
    Noisy a = make(1);
    std::puts("[2] Noisy b = Noisy(Noisy(Noisy(2)));");
    Noisy b = Noisy(Noisy(Noisy(2)));
    std::puts("[3] Noisy c = make(3); 를 인자로 넘기면");
    [](Noisy) { std::puts("    함수 안"); }(make(3));
    std::puts("[4] main 끝 — 여기서 a, b 가 죽는다");
    (void)a; (void)b;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -fno-elide-constructors vcat05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] Noisy a = make(1);
    ctor(1)
[2] Noisy b = Noisy(Noisy(Noisy(2)));
    ctor(2)
[3] Noisy c = make(3); 를 인자로 넘기면
    ctor(3)
    함수 안
    dtor(3)
[4] main 끝 — 여기서 a, b 가 죽는다
    dtor(2)
    dtor(1)
```

- ★★★ **`-fno-elide-constructors` 가 무력하다.** 생략할 복사가 **애초에 없기** 때문이다.\
  「복사 생략(copy elision)」이라는 이름이 **C++17 이후로는 이 자리에 안 맞는다.**

**같은 소스를 `-std=c++14` 로 던지면** 그 복사가 돌아온다.

```text
===== 소스: vcat05.cpp =====
// prvalue 는 객체가 아니다 — C++17 의 「물질화」를 생성자 로그로 센다
#include <cstdio>

struct Noisy {
    int id;
    explicit Noisy(int i) : id(i) { std::printf("    ctor(%d)\n", id); }
    Noisy(const Noisy& o) : id(o.id) { std::printf("    copy(%d)\n", id); }
    Noisy(Noisy&& o) noexcept : id(o.id) { std::printf("    move(%d)\n", id); }
    ~Noisy() { std::printf("    dtor(%d)\n", id); }
};

Noisy make(int i) { return Noisy(i); }

int main() {
    std::puts("[1] Noisy a = make(1);");
    Noisy a = make(1);
    std::puts("[2] Noisy b = Noisy(Noisy(Noisy(2)));");
    Noisy b = Noisy(Noisy(Noisy(2)));
    std::puts("[3] Noisy c = make(3); 를 인자로 넘기면");
    [](Noisy) { std::puts("    함수 안"); }(make(3));
    std::puts("[4] main 끝 — 여기서 a, b 가 죽는다");
    (void)a; (void)b;
}
===== g++ -std=c++14 -Wall -Wextra -pedantic -fno-elide-constructors vcat05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] Noisy a = make(1);
    ctor(1)
    move(1)
    dtor(1)
    move(1)
    dtor(1)
[2] Noisy b = Noisy(Noisy(Noisy(2)));
    ctor(2)
    move(2)
    move(2)
    move(2)
    dtor(2)
    dtor(2)
    dtor(2)
[3] Noisy c = make(3); 를 인자로 넘기면
    ctor(3)
    move(3)
    dtor(3)
    move(3)
    함수 안
    dtor(3)
    dtor(3)
[4] main 끝 — 여기서 a, b 가 죽는다
    dtor(2)
    dtor(1)
```

- ★★★ **`[2]` 에서 `move` 가 세 번** 돈다 — C++14 에서는 **괄호 한 겹이 이동 한 번**이었다.
- ★★ **`[1]` 은 `move` 두 번**(반환용 한 번, 초기화용 한 번)이다.
- ★★ C++14 라도 **플래그를 안 붙이면** 출력이 C++20 과 같다 — **그때는** 「**허용된 최적화**」였고 지금은 **규칙**이다.\
  ★ 그래서 **「복사가 몇 번 나느냐」를 표준판 없이 말하면 반쪽**이다.

### 6. ★★ A·B 는 블록 끝 · C 는 문장 끝 · D 는 늘린 게 아니다

**출력**

```text
===== 소스: vcat06.cpp =====
// prvalue 를 참조에 묶으면 수명이 늘고, xvalue 를 묶으면 늘 것이 없다
#include <cstdio>

struct Noisy {
    int id;
    explicit Noisy(int i) : id(i) { std::printf("    ctor(%d)\n", id); }
    ~Noisy() { std::printf("    dtor(%d)\n", id); }
};

Noisy make(int i) { return Noisy(i); }

int main() {
    std::puts("[A] const Noisy& r = make(1);   prvalue 를 묶는다");
    { const Noisy& r = make(1); std::printf("    블록 안 r.id=%d\n", r.id); }
    std::puts("[B] Noisy&& r = make(2);        prvalue 를 rvalue 참조에");
    { Noisy&& r = make(2); std::printf("    블록 안 r.id=%d\n", r.id); }
    std::puts("[C] make(3);                    묶지 않는다");
    { make(3); std::puts("    다음 문장"); }
    std::puts("[D] Noisy local(4); Noisy&& r = static_cast<Noisy&&>(local);  xvalue");
    { Noisy local(4); Noisy&& r = static_cast<Noisy&&>(local);
      std::printf("    블록 안 r.id=%d  &r==&local:%d\n",
                  r.id, static_cast<int>(&r == &local)); }
    std::puts("[E] main 끝");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic vcat06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[A] const Noisy& r = make(1);   prvalue 를 묶는다
    ctor(1)
    블록 안 r.id=1
    dtor(1)
[B] Noisy&& r = make(2);        prvalue 를 rvalue 참조에
    ctor(2)
    블록 안 r.id=2
    dtor(2)
[C] make(3);                    묶지 않는다
    ctor(3)
    dtor(3)
    다음 문장
[D] Noisy local(4); Noisy&& r = static_cast<Noisy&&>(local);  xvalue
    ctor(4)
    블록 안 r.id=4  &r==&local:1
    dtor(4)
[E] main 끝
```

**왜 그런가**

```text
   [A] const Noisy& r = make(1);   ctor ─ "블록 안" ─ dtor     ★ 수명이 r 까지 늘어난다
   [B] Noisy&&      r = make(2);   ctor ─ "블록 안" ─ dtor     ★ 같다
   [C] make(3);                    ctor ─ dtor ─ "다음 문장"   문장 끝에 죽는다
   [D] Noisy local(4);
       Noisy&& r = cast(local);    ctor ─ "블록 안" ─ dtor     local 의 수명 그대로
```

- ★★ **[A]와 [B]가 같다.** 수명 연장은 **`const T&` 의 특권이 아니다** — `T&&` 도 똑같이 늘린다.\
  ★ 늘어나는 조건은 「**참조를 prvalue 로 직접 초기화**」다.
- ★★★ **[D]는 늘린 것이 아니다.** `&r == &local` 이 **1** 이다 —\
  **xvalue 는 이미 있는 객체를 가리킬 뿐**이라 **늘릴 임시가 없다.**\
  ★ 「`std::move` 로 받아 두면 살아남는다」는 생각이 여기서 깨진다.
- ★ **[C]가 갈리는 한 글자는** 「**참조에 묶었느냐**」다. 안 묶으면 **그 문장 끝**이다.
- ★ 수명 연장이 **안 되는** 자리(반환·멤버 저장·범위 for)의 정본은 [목록의 **30번 주제**](../30-dangling-references-and-lifetime-extension/)다.

### 7. ★ 둘은 근거의 종류가 다르다 — 그리고 `i` 가 안 변한 것이 답이다

**출력**

```text
===== 소스: vcat07.cpp =====
// 같은 격자를 실행으로 — 세 범주를 타입 특성으로 판정해 한 표에 찍는다
#include <cstdio>
#include <type_traits>
#include <utility>

struct S { int m; };

int  byval();
int& bylref();
int&& byrref();

template <class T>
const char* cat() {
    if constexpr (std::is_lvalue_reference_v<T>)      return "lvalue";
    else if constexpr (std::is_rvalue_reference_v<T>) return "xvalue";
    else                                              return "prvalue";
}

#define SHOW(e) std::printf("  %-26s %s\n", #e, cat<decltype((e))>())

int main() {
    int i = 0, j = 0;
    int arr[3]{};
    S s{0};

    std::puts("  expr                       category");
    SHOW(42);
    SHOW("abc");
    SHOW(i);
    SHOW(i + 1);
    SHOW(++i);
    SHOW(i++);
    SHOW(byval());
    SHOW(bylref());
    SHOW(byrref());
    SHOW(std::move(i));
    SHOW(arr);
    SHOW(arr[0]);
    SHOW(s.m);
    SHOW(S{});
    SHOW(S{}.m);
    SHOW(std::move(s).m);
    SHOW(i ? i : j);
    SHOW("abc"[0]);

    std::printf("(부수 효과 확인 i=%d j=%d arr[0]=%d)\n", i, j, arr[0]);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic vcat07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  expr                       category
  42                         prvalue
  "abc"                      lvalue
  i                          lvalue
  i + 1                      prvalue
  ++i                        lvalue
  i++                        prvalue
  byval()                    prvalue
  bylref()                   lvalue
  byrref()                   xvalue
  std::move(i)               xvalue
  arr                        lvalue
  arr[0]                     lvalue
  s.m                        lvalue
  S{}                        prvalue
  S{}.m                      xvalue
  std::move(s).m             xvalue
  i ? i : j                  lvalue
  "abc"[0]                   lvalue
(부수 효과 확인 i=0 j=0 arr[0]=0)
```

**왜 그런가**

- ★★ **1번은** 「**컴파일러가 타입으로 답한 것**」이고 이것은 「**프로그램이 판정해 찍은 것**」이다.\
  둘 다 같은 표준 규칙을 보지만 **경로가 다르다** — 1번은 컴파일 시간 진단, 이쪽은 `<type_traits>` 판정 + 실행 출력.\
  ★ **한 칸도 다르지 않다**는 것이 그래서 뜻이 있다.
- ★★★ **마지막 줄이 `i=0 j=0 arr[0]=0`** 이다. `SHOW(++i)` 와 `SHOW(i++)` 를 넣었는데 **`i` 가 0 이다** —\
  「**`decltype` 은 식을 평가하지 않는다**」가 출력으로 증명된 것이다.\
  ★ 1번에서 **clang 만 내던 경고**(`-Wunevaluated-expression`)가 정확히 이 사실을 가리킨다.
- ★ 두 창을 다 쓰는 이유 — **에러 창은 타입을 정확히 주지만 표로 못 읽고**,\
  **실행 창은 표로 읽히지만 「컴파일러가 어떻게 부르는지」를 안 준다**(`const char (&)[4]` 같은 것).

### 8. ★★ 클래스는 받는다 — 내장 타입만 왼쪽을 가린다

**출력**

```text
===== 소스: vcat08.cpp =====
// 「prvalue 에는 대입이 안 된다」는 내장 타입 이야기다 — 클래스 prvalue 는 받는다
#include <cstdio>
#include <string>

struct S { int m; };

struct Guarded {
    int m;
    Guarded& operator=(const Guarded&) & = default;   // ★ lvalue 에만 허용
};

int main() {
    S s{1};
    S{} = s;                       // (a) 된다 — 임시에 대입한다
    std::string t("a");
    std::string("x") += "y";       // (b) 된다

    Guarded g{1};
    Guarded h{2};
    g = h;                         // (c) 된다 — 왼쪽이 lvalue

    std::printf("s.m=%d t=%s g.m=%d — 여기까지 전부 컴파일된다\n",
                s.m, t.c_str(), g.m);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic vcat08.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
s.m=1 t=a g.m=2 — 여기까지 전부 컴파일된다
```

**왜 그런가**

- ★★★ **`S{} = s;` 가 컴파일된다.** 클래스의 대입은 **멤버 함수 호출**이고, 멤버 함수는 **rvalue 에서도 부를 수 있다**(기본값).
- ★★ **`std::string("x") += "y";` 도 마찬가지**다 — 표준 라이브러리도 이 자리를 막지 않는다.
- ★ **막고 싶으면 `&` 한정자**를 단다: `Guarded& operator=(const Guarded&) &`.\
  그러면 **lvalue 에서만** 불린다 — 아래에서 확인된다.

막히는 쪽 넷:

```text
===== 소스: vcat09.cpp =====
// 그래도 막히는 넷 — 범주가 왼쪽 자리와 참조 묶기를 가른다
struct S { int m; };
struct Guarded { int m; Guarded& operator=(const Guarded&) & = default; };
struct Bits { int b : 3; };

int main() {
    S s{1};
    Guarded g{1};
    Bits x{1};

    S{}.m = 7;          // (1) xvalue 인 스칼라 멤버에 대입
    42 = 1;             // (2) prvalue 에 대입
    Guarded{} = g;      // (3) & 한정자를 단 operator= 는 임시를 거부한다
    int& br = x.b;      // (4) 비트필드 lvalue 는 int& 에 못 묶는다
    (void)s; (void)br;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic vcat09.cpp -o ex 2>&1 | grep 'error:' (cc exit=1) =====
vcat09.cpp:11:9: error: using rvalue as lvalue [-fpermissive]
vcat09.cpp:12:5: error: lvalue required as left operand of assignment
vcat09.cpp:13:17: error: passing ‘Guarded’ as ‘this’ argument discards qualifiers [-fpermissive]
vcat09.cpp:14:17: error: cannot bind bit-field ‘x.Bits::b’ to ‘int&’
```

| 줄 | 왜 막히나 |
|---|---|
| `S{}.m = 7;` | ★ `S{}.m` 은 **xvalue** = rvalue — **내장 대입의 왼쪽**에 못 온다 |
| `42 = 1;` | prvalue — 같은 이유 |
| `Guarded{} = g;` | ★ **`&` 한정자**가 임시에서의 호출을 막는다 |
| `int& br = x.b;` | ★ **비트필드**는 범주와 무관하게 `int&` 에 못 묶는다 |

- ★★★ **1번에서 `S{}.m` 이 `int&&` 로 찍혔는데 대입이 막힌다.**\
  **「참조 타입으로 찍혔다」는 「lvalue 다」가 아니다** — `T&&` 는 **xvalue** 의 표시다.\
  ★ 이 한 줄이 08 에서 가장 자주 틀리는 자리다.
- ★ **비트필드**는 격자 밖의 제약이다. 정본은 C 갈래 [`24-bit-fields/`](../../../c/syntax/24-bit-fields/).

clang 도 **넷 그대로**다.

```text
===== 소스: vcat09.cpp =====
// 그래도 막히는 넷 — 범주가 왼쪽 자리와 참조 묶기를 가른다
struct S { int m; };
struct Guarded { int m; Guarded& operator=(const Guarded&) & = default; };
struct Bits { int b : 3; };

int main() {
    S s{1};
    Guarded g{1};
    Bits x{1};

    S{}.m = 7;          // (1) xvalue 인 스칼라 멤버에 대입
    42 = 1;             // (2) prvalue 에 대입
    Guarded{} = g;      // (3) & 한정자를 단 operator= 는 임시를 거부한다
    int& br = x.b;      // (4) 비트필드 lvalue 는 int& 에 못 묶는다
    (void)s; (void)br;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic vcat09.cpp -o ex 2>&1 | grep -E 'error:|generated' (cc exit=1) =====
vcat09.cpp:11:11: error: expression is not assignable
vcat09.cpp:12:8: error: expression is not assignable
vcat09.cpp:13:15: error: no viable overloaded '='
vcat09.cpp:14:10: error: non-const reference cannot bind to bit-field 'b'
4 errors generated.
```

### 9. ★★ `-fpermissive` 를 붙이면 `cc exit=0` 이고, `-pedantic-errors` 로도 안 돌아온다

**출력** — 먼저 붙이지 않은 판.

```text
===== 소스: vcat10.cpp =====
// -fpermissive 는 범주 규칙을 경고로 낮춘다 — 쓴 값은 그대로 사라진다
#include <cstdio>

struct S { int m; };

int main() {
    S s{1};
    S{}.m = 7;                    // ★ 표준으로는 ill-formed
    std::printf("s.m=%d — 7 은 어디로도 가지 않았다\n", s.m);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic vcat10.cpp -o ex (cc exit=1) =====
vcat10.cpp: In function ‘int main()’:
vcat10.cpp:8:9: error: using rvalue as lvalue [-fpermissive]
    8 |     S{}.m = 7;                    // ★ 표준으로는 ill-formed
      |     ~~~~^
```

**붙인 판.**

```text
===== 소스: vcat10.cpp =====
// -fpermissive 는 범주 규칙을 경고로 낮춘다 — 쓴 값은 그대로 사라진다
#include <cstdio>

struct S { int m; };

int main() {
    S s{1};
    S{}.m = 7;                    // ★ 표준으로는 ill-formed
    std::printf("s.m=%d — 7 은 어디로도 가지 않았다\n", s.m);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -fpermissive vcat10.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
vcat10.cpp: In function ‘int main()’:
vcat10.cpp:8:9: warning: using rvalue as lvalue [-fpermissive]
    8 |     S{}.m = 7;                    // ★ 표준으로는 ill-formed
      |     ~~~~^
s.m=1 — 7 은 어디로도 가지 않았다
```

**`-pedantic-errors` 까지 붙인 판.**

```text
===== 소스: vcat10.cpp =====
// -fpermissive 는 범주 규칙을 경고로 낮춘다 — 쓴 값은 그대로 사라진다
#include <cstdio>

struct S { int m; };

int main() {
    S s{1};
    S{}.m = 7;                    // ★ 표준으로는 ill-formed
    std::printf("s.m=%d — 7 은 어디로도 가지 않았다\n", s.m);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic-errors -fpermissive vcat10.cpp -o ex (cc exit=0) =====
vcat10.cpp: In function ‘int main()’:
vcat10.cpp:8:9: warning: using rvalue as lvalue [-fpermissive]
    8 |     S{}.m = 7;                    // ★ 표준으로는 ill-formed
      |     ~~~~^
```

**왜 그런가**

- ★★★ **`cc exit` 이 1 → 0 으로 바뀌고 프로그램이 돈다.** 그런데 **`s.m` 이 1** 이다 —\
  **7 은 물질화된 임시에 쓰였고 그 임시는 그 문장 끝에 죽었다.** **아무 데도 안 간 쓰기**다.
- ★★★ **`-pedantic-errors` 를 붙여도 경고 그대로**다(`cc exit=0`).\
  ★ 다른 「exit 0 인데 ill-formed」 사례들은 `-pedantic-errors` 로 되살아나는데 **이것은 안 산다** —\
  `-fpermissive` 는 「표준 위반을 경고로 낮춘다」가 아니라 「**그 진단을 경고로 고정한다**」에 가깝다.
- ★★ 그래서 이 자리가 이 갈래의 **고정 항목**이다 — 「**종료 코드가 0인데 ill-formed**」.\
  **경고 0건을 셀 게 아니라 `cc exit` 과 **플래그 목록**을 같이 봐야** 뜻이 생긴다.
- ★ **UB 는 아니다.** 임시는 제대로 만들어졌고 제대로 죽었다 — 표준이 **금지한 코드가 통과한 것**일 뿐이다.

### 10. 이 주제의 지도

**출력** — 없다(연결 문항).

**왜 그런가**

- `decltype(x)` 대 `decltype((x))` 의 **규칙 자체**는 형제 [`05번`](../05-auto-and-decltype-type-deduction/)이 정본이다.\
  ★ 08 은 **그 창을 빌려** 범주를 물었을 뿐, 규칙을 다시 쓰지 않았다.
- 「참조가 무엇인가」는 형제 [`07번`](../07-references-vs-pointers/)이 정본이다.\
  ★ 07 이 「**참조는 재결합되지 않는다**」까지였다면, 08 은 「**어떤 식이 어느 참조에 묶이나**」를 얹었다(3번의 격자).
- `std::move` 가 xvalue 를 만든다는 것의 정본은 [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)다.\
  ★ 1번의 `v11`·`v12` 가 그 예고편이다.
- 「매개변수를 무엇으로 받나」는 [목록의 **11번 주제**](../11-choosing-parameter-passing/)다.\
  ★ 2번의 표(`const T&` 가 넷을 다 받는다)가 그 표의 첫 줄이 된다.
- 수명 연장이 **안 되는** 자리·댕글링은 [목록의 **30번 주제**](../30-dangling-references-and-lifetime-extension/)다. 6번은 **되는 쪽**만 봤다.
- ★★ **Rust 에는 이 질문이 없다** — [`../../../rust/syntax/08-ownership-and-move/`](../../../rust/syntax/08-ownership-and-move/).\
  Rust 는 **이동이 기본**이라 `let b = a;` 가 이미 이동이고, 「이 식이 rvalue 인가」를 표시할 문법이 필요 없다.\
  C++ 는 **기본이 복사**여서 **식마다 「훔쳐도 된다」는 표시**를 따로 만들어야 했고, 그 표시가 **xvalue** 다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 명령으로 돌렸나 |
|---|---|---|
| `vcat01.cpp` 격자 | ★★★ **스무 식의 타입** — `int`/`int&`/`int&&` | g++ · clang(`-ferror-limit=0`) |
| `vcat02.cpp` 오버로드 | ★★ prvalue·xvalue 가 **같은 칸** · `const` 는 `const&` 로 | g++ |
| `vcat03.cpp` 묶기 | ★ **에러 6 · 두 컴파일러 같다** | g++ · clang |
| `vcat04.cpp` 리터럴 | `sizeof` **4** · `a == b` **1**(★ 미명시) | g++ |
| `vcat05.cpp` 물질화 | ★★★ `ctor` **한 번** · `-fno-elide-constructors` **무력** | g++ `-std=c++20` · 같은 플래그 · `-std=c++14` |
| `vcat06.cpp` 수명 | ★★ A=B · ★★★ D 는 `&r == &local` **1** | g++ |
| `vcat07.cpp` 실행 판정 | ★ 격자 일치 · ★★★ **`i` 가 안 변한다** | g++ |
| `vcat08.cpp` 대입 되는 쪽 | ★ `S{} = s;` **컴파일됨** | g++ |
| `vcat09.cpp` 대입 막히는 쪽 | ★ **에러 4 · 두 컴파일러 같다** | g++ · clang |
| `vcat10.cpp` 플래그 | ★★★ `cc exit` **1 → 0** · `-pedantic-errors` 로도 **0** | g++ 세 판 |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3)에서만** 그렇다.

- ★★ **같은 문자열 리터럴이 합쳐지는 것**(`a == b` 가 1) — **미명시**다. 관찰일 뿐이다.
- 진단 문구 전부 · **에러를 몇 개로 세는가** · clang 의 **기본 에러 상한 20**.
- ★ **clang 만 내는 `-Wunevaluated-expression` 2건** — g++ 는 0건.
- ★★★ **`-fpermissive` 의 동작**(9번) — **표준이 아니라 g++ 의 방언**이다.
- ★ 임시 객체를 **어디에 두는지** — 이 문서는 **주소를 싣지 않았다**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **세 범주의 판정**(1번·7번의 스무 칸).
- **참조 묶기 격자**(3번) · **오버로드 선택**(2번).
- **문자열 리터럴이 lvalue** 이고 나머지 리터럴이 prvalue 인 것.
- **prvalue 의 멤버가 xvalue** 인 것(`S{}.m`).
- **C++17 부터 prvalue 초기화에 복사·이동이 없는 것**(5번).
- **`const T&`·`T&&` 가 prvalue 의 수명을 늘리는 것**(6번의 A·B).
- **`&` 한정자가 임시에서의 호출을 막는 것**(8번).
- **`decltype` 이 식을 평가하지 않는 것**(7번).

**UB 의 결과라 보장이 아닌 것**

- ★ **이 주제에는 없다.** 범주 위반은 30칸 전부 **컴파일 에러**였다.\
  9번은 UB 가 아니라 「**표준이 금지한 코드를 플래그로 통과시킨 것**」이다.\
  수명이 끝난 임시를 읽는 쪽(진짜 UB)의 정본은 [목록의 **30번 주제**](../30-dangling-references-and-lifetime-extension/)다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **람다 식의 범주** · **`co_await`/`co_yield` 식** ·
  **`decltype(auto)` 가 범주를 나르는 것**(정본이 형제 [`05번`](../05-auto-and-decltype-type-deduction/)) ·
  **`std::forward` 의 범주**(정본이 [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)) ·
  **`auto&&` 로 prvalue 를 받는 것**(형제 [`05번`](../05-auto-and-decltype-type-deduction/)) ·
  **`-O1`·`-O2` 에서의 생성자 횟수**(5번은 최적화 없이 돌렸다 — ★ 다만 **C++17 의 보장은 최적화와 무관**하다) ·
  **clang 에 `-fpermissive` 를 주는 것**(그 플래그는 g++ 의 것이다).
- **못 잰 것** — ★ 「**범주 판정이 컴파일을 얼마나 느리게 하나**」.\
  컴파일 시간은 이 하네스로 **잴 수 없다**(한 파일이 너무 작아 잡음이 신호보다 크다).\
  ★ 이 문서는 그래서 **수치를 적지 않았다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★ **`-fno-elide-constructors` 가 C++20 에서 계속 무력한지**(5번) — 여기가 판 사이에서 가장 먼저 움직였다.
- ★ **clang 의 `-Wunevaluated-expression` 이 계속 2건인지**, g++ 가 그 경고를 **갖게 되는지**.
- ★ **`-fpermissive` 가 계속 `S{}.m = 7` 을 통과시키는지**(9번).
- 진단 문구와 **에러 개수**(3번의 6 · 8번의 4) · clang 의 **기본 에러 상한**.
