# cpp/syntax/08 — 값 범주 — lvalue·prvalue·xvalue — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 값 범주](https://en.cppreference.com/w/cpp/language/value_category) · [`decltype` 지정자](https://en.cppreference.com/w/cpp/language/decltype) · [임시 객체의 물질화](https://en.cppreference.com/w/cpp/language/implicit_conversion#Temporary_materialization) · [복사 생략](https://en.cppreference.com/w/cpp/language/copy_elision) · [GCC 13 — `-fpermissive`](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/C_002b_002b-Dialect-Options.html)
> **실행 검증** — 이 문서의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`vcat01.cpp` \~ `vcat10.cpp`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 긴 진단은 **거르는 명령을 배너에 적어 두었다**(`| grep 'incomplete type'`).\
> 그러니 실린 것은 「생략한 일부」가 아니라 **그 명령의 전체 출력**이다.
> **버전** — lvalue·rvalue 의 구분은 **C++98부터**. **xvalue 와 `T&&` 는 C++11부터**이고,\
> **prvalue 가 「물질화」로 다시 정의된 것은 C++17부터**다(아래 (6)). 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> **경계** — 「참조가 무엇인가」의 정본은 형제 [`07번`](../07-references-vs-pointers/),\
> 「`decltype` 이 이름과 식을 어떻게 가르나」의 정본은 형제 [`05번`](../05-auto-and-decltype-type-deduction/)이다.\
> 여기서는 **05 의 창(`decltype((식))`)을 빌려 쓰되 그 규칙을 다시 설명하지 않는다.**\
> 「`std::move`·`std::forward`」는 [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/), 「`const` 정확성」은 [목록의 **10번 주제**](../10-const-correctness/),\
> 「매개변수를 무엇으로 받나」는 [목록의 **11번 주제**](../11-choosing-parameter-passing/), 「오버로드 해석의 전체 순서」는 형제 [`01번`](../01-function-overloading-and-overload-resolution/),\
> 「임시의 수명 연장과 댕글링」은 [목록의 **30번 주제**](../30-dangling-references-and-lifetime-extension/)가 정본이다.
> ★★★ **08 → 09 → 11 은 한 사슬이다** — 여기서 **범주**를 정하고, 09 가 **그 범주를 만드는 법**(`std::move`)을 주고,\
> 11 이 **그래서 무엇으로 받을지**를 고른다. 세 문서는 같은 격자를 다시 쓴다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단의 **열 번호**(g++ 45 · clang 45 가 같은 자리를 다르게 센다) | ★ **`TypeOf<...>` 꺾쇠 안의 타입** — 이 주제의 답 자체다 |
> | 두 컴파일러의 **에러 문구**와 **에러를 몇 개로 세는가** | **진단 이름**(`-fpermissive` · `-Wunevaluated-expression`) |
> | 같은 리터럴이 합쳐졌는지(`a == b`) — ★ **미명시**다 | ★ **생성자·소멸자 호출 횟수와 순서** |
> | 객체 주소·`%p` (이 문서는 **싣지 않았다**) | **`cc exit` 와 `run exit`**(갈라 적었다) · `sizeof` 값 |

## 한눈에 — 쉽게 말하면

**모든 식에는 「이름이 있느냐」와 「훔쳐 가도 되느냐」 두 개의 표가 붙어 있다.**

세 범주는 그 두 표의 조합이다.

| 비유 | 실체 | 표 |
|---|---|---|
| **이름표가 붙은 물건** — 주인이 계속 쓴다 | `i` · `arr[0]` · `s.m` · `"abc"` | **lvalue** |
| ★ **방금 나온 물건** — 아직 아무 데도 안 놓였다 | `42` · `i + 1` · `f()`(값 반환) · `S{}` | **prvalue** |
| ★★ **이름표는 붙었는데 「가져가도 된다」 딱지가 붙은 물건** | `std::move(i)` · `g()`(`T&&` 반환) · `S{}.m` | **xvalue** |

> **값 범주(value category)** — 식 하나하나에 붙는 분류. 타입과는 **다른 축**이다.\
> 예: `int i;` 에서 `i` 와 `i + 1` 은 **타입이 둘 다 `int`** 인데 **범주가 다르다**(lvalue / prvalue).

- ★★★ **범주는 값이 아니라 「식」의 성질이다.** 같은 변수라도 `i` 는 lvalue, `std::move(i)` 는 xvalue다 — **변수가 바뀐 게 아니라 식이 다른 것**이다.
- ★★ **「훔쳐도 되느냐」가 오버로드를 가른다** — `f(T&)` 와 `f(T&&)` 중 무엇이 뽑히는지가 전부 여기서 결정된다((8)).
- ★★ **「이름이 있느냐」가 참조 묶기를 가른다** — `int& r = 42;` 가 막히는 이유가 그것이다((9)).

```text
              「이름이 있나?」(glvalue)
                   예            아니오
                ┌──────────┬──────────────┐
  「훔쳐도   예 │  xvalue  │   prvalue    │  ← 둘을 묶어 rvalue
    되나?」     │ move(i)  │  42  S{}     │
   (rvalue)     ├──────────┼──────────────┤
            아니│  lvalue  │   (없다)     │
                │  i  "ab" │              │
                └──────────┴──────────────┘
                   ↑
              둘을 묶어 glvalue

     lvalue  = glvalue 이면서 rvalue 가 아닌 것
     xvalue  = glvalue 이면서 rvalue 인 것      ← C++11 에 새로 생긴 칸
     prvalue = rvalue 이면서 glvalue 가 아닌 것
```

> **glvalue(generalized lvalue)** — 「어딘가에 있는 객체를 가리키는 식」. lvalue + xvalue.\
> 예: `i` 도 `std::move(i)` 도 **같은 객체 하나**를 가리킨다.

> **rvalue** — 「훔쳐 가도 되는 식」. prvalue + xvalue.\
> 예: `f(42)` 와 `f(std::move(i))` 는 **같은 오버로드**(`f(T&&)`)로 간다((8)).

## 이 주제가 답하려는 질문

1. **어떤 식이 어느 범주인가** — 그리고 그것을 **컴파일러에게 직접 물을** 수 있나((2)·(3)).
2. **범주가 무엇을 가르나** — 참조 묶기((9))와 오버로드 선택((8)).
3. **prvalue 는 객체인가** — C++17 에서 답이 바뀌었다((6)).

## 동작 방식

### (0) 이 주제가 쓰는 네 창

같은 「범주」를 네 가지 방법으로 본다. **하나만 쓰면 답이 안 갈린다.**

```text
① decltype((식)) + 정의 없는 템플릿   컴파일 에러 문구에 범주가 타입으로 찍힌다   (2)
② type_traits 로 판정해 실행 출력      같은 격자를 한 표로 본다                  (3)
③ 오버로드 후보를 여럿 두고 호출       무엇이 뽑혔는지 로그로 본다                (8)
④ 생성자·소멸자 로그                   임시가 언제 생기고 언제 죽는지 센다        (6)(7)
```

- ★★★ **네 번째 창은 ①이다** — `decltype(e)` 가 `T` 면 prvalue, `T&` 면 lvalue, `T&&` 면 xvalue다.\
  **이 대응이 곧 범주의 정의를 타입으로 옮긴 것**이라 지어낼 여지가 없다.
- ★ 그 창을 만든 것은 형제 [`05번`](../05-auto-and-decltype-type-deduction/)이다 — **여기서는 창만 빌려 쓰고 `decltype` 규칙 자체는 거기서 읽는다.**

### (1) 세 범주 — 격자로 한 번

**언제 쓰나** — 코드를 읽다가 「이 식을 `T&&` 로 받을 수 있나」가 걸릴 때마다.

```text
   식을 하나 고른다
        ↓
   ① 이 식이 가리키는 객체가 「어딘가에 있나」?
        아니오 ──────────────────> prvalue   (42 · i+1 · f() · S{})
        예
        ↓
   ② 그 객체를 「훔쳐 가도 된다」고 표시돼 있나?
        아니오 ──────────────────> lvalue    (i · arr[0] · s.m · "abc")
        예    ──────────────────> xvalue    (move(i) · g() · S{}.m)
```

- ★ ①의 「어딘가에 있나」는 **주소를 얻을 수 있나**로 바꿔 물어도 대부분 맞다 — `&42` 는 에러이고 `&"abc"` 는 된다((4)).
- ★★ ②는 **「그 식의 문법 모양」이 정한다.** `std::move` 를 거쳤거나 `T&&` 를 돌려주는 함수를 불렀거나, **rvalue 의 멤버**를 꺼냈거나.

**비용** — 판정 자체는 컴파일 시간에 끝난다. **런타임 비용은 0**이다.

### (2) ★★★ 컴파일러에게 직접 묻기 — `decltype((식))`

**언제 쓰나** — 「이게 xvalue 인가 prvalue 인가」가 헷갈릴 때. **추측하지 말고 던진다.**

정의가 없는 템플릿에 넣으면 **불완전 타입 에러가 타입을 찍어 준다.**

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

- ★★★ **읽을 것은 `TypeOf<...>` 의 꺾쇠 안**이다. `int` = prvalue · `int&` = lvalue · `int&&` = xvalue.
- ★★ **`"abc"` 만 `const char (&)[4]`** — 참조다. **문자열 리터럴은 lvalue**((4)).
- ★★ **`S{}.m` 이 `int&&`** — prvalue 의 멤버를 꺼내면 **xvalue** 가 된다. 「임시가 물질화됐다」는 뜻이다((6)).
- ★ **`byrref()` 와 `std::move(i)` 가 같은 `int&&`** — **`T&&` 를 돌려주는 함수 호출이 곧 xvalue** 다.
- ★ **`++i` 는 `int&`, `i++` 는 `int`** — 전위는 그 자리를 돌려주고 후위는 **복사본을 만들어** 돌려준다.

같은 소스를 clang 으로도 던졌다. **판정은 한 칸도 다르지 않고, 문구와 경고만 다르다.**

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

- ★★ **clang 만 내는 경고 둘** — `++i`·`i++` 를 `decltype` 안에 넣은 자리다.\
  **`decltype` 은 식을 평가하지 않으므로** 그 증가는 **일어나지 않는다**((3) 의 마지막 줄이 `i=0` 으로 그것을 보인다).\
  **g++ 는 이 자리에 아무 말도 하지 않는다.**
- ★ **clang 은 기본 20개에서 멈춘다** — 스무 줄을 다 보려고 `-ferror-limit=0` 을 붙였다. 배너에 적어 두었다.

### (3) 같은 격자를 실행으로 — 한 표

**언제 쓰나** — 에러 문구 없이 **표 하나로** 보고 싶을 때. 근거의 종류가 ②로 바뀐다.

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

- ★★ **①(에러)과 ②(실행)가 한 칸도 다르지 않다** — 판정이 서로를 뒷받침한다.
- ★★★ **마지막 줄이 `i=0 j=0 arr[0]=0`** 이다. `SHOW(++i)` 를 두 번이나 썼는데 **`i` 가 안 늘었다** —\
  「**`decltype` 은 식을 평가하지 않는다**」가 그래서 출력으로 증명된다.

### (4) 리터럴 — 문자열만 lvalue다

**언제 쓰나** — `const char*` 와 `std::string` 사이에서 임시가 생기는 자리를 셀 때([목록의 **11번 주제**](../11-choosing-parameter-passing/)로 이어진다).

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

- ★★ **문자열 리터럴은 「어딘가에 있는 배열」이다** — `sizeof` 가 **4**(널 종료 포함)이고 **주소가 있고** `const char (&)[4]` 에 묶인다.
- ★ **`a == b` 가 1** — 같은 리터럴 둘이 **한 덩어리로 합쳐졌다.** ★★ 그런데 **이것은 미명시**다.\
  표준은 「같은 리터럴이 구별되는 객체인지 정하지 않는다」 — **근거로 쓰면 안 되는 칸**이다.
- ★ 나머지 리터럴(`42`·`'c'`·`1.5`)은 전부 **prvalue** 라 주소가 없다((9) 의 (5)번 에러).
- ★ **문자열 리터럴을 `char*` 에 넣는 것은 C++11부터 ill-formed** 인데 **컴파일이 통과한다** — 그 정본은 [목록의 **10번 주제**](../10-const-correctness/)다.

### (5) 함수 반환값 — 셋을 갈라 본다

**언제 쓰나** — API 의 반환 타입을 고를 때. **반환 타입이 곧 호출식의 범주**다.

```text
   int  byval();     f()  ->  prvalue     값을 새로 만들어 준다
   int& bylref();    g()  ->  lvalue      원래 있던 것을 가리킨다
   int&& byrref();   h()  ->  xvalue      원래 있던 것인데 "가져가라"
```

(2)의 격자에서 세 줄이 각각 `int` · `int&` · `int&&` 로 찍혔다.

- ★★ **`T&&` 를 돌려주는 함수는 새 객체를 만들지 않는다** — `std::move` 가 정확히 그 모양이다([목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)).
- ★ **`byval()` 이 prvalue 라는 것이 (6)의 전제**다 — prvalue 라서 **물질화될 때까지 객체가 없다.**

### (6) ★★★ prvalue 는 객체가 아니다 — C++17 의 「물질화」

**언제 쓰나** — 「값 반환이 복사를 낳나」를 따질 때. **C++17 에서 답이 바뀌었다.**

> **물질화(temporary materialization)** — prvalue 를 **실제 객체로 바꾸는 변환**.\
> C++17 부터 prvalue 는 **그 자체로는 객체가 아니고**, 참조에 묶거나 멤버를 꺼내는 등\
> **객체가 필요해지는 순간에만** 물질화된다.\
> 예: `Noisy n = make();` 에서 **`make()` 의 결과가 곧 `n`** 이다 — 옮길 임시가 아예 없다.

생성자 로그로 센다.

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

- ★★★ **`Noisy(Noisy(Noisy(2)))` 가 `ctor` 한 번**이다. 괄호를 세 겹 씌웠는데도 객체는 하나다.
- ★★ **함수 인자로 넘겨도 한 번**이고, 그 임시는 **함수가 끝나는 자리**에서 죽는다(`dtor(3)`).

여기서 **「복사 생략」이라는 이름이 더 이상 맞지 않는다**는 것을 던져서 확인한다.\
복사를 끄는 플래그를 붙여도 **출력이 한 글자도 안 바뀐다.**

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

- ★★★ **`-fno-elide-constructors` 가 아무 일도 안 한다.** 생략할 복사가 **애초에 없기** 때문이다.
- ★ 이것이 「**C++17 부터는 생략이 아니라, 그런 복사가 아예 없다**」의 실측 근거다.

**같은 소스를 C++14 로 던지면** 그 복사가 돌아온다 — **표준판이 갈리는 자리**다.

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

- ★★★ **`[2]` 에서 `move` 가 세 번** 돈다. C++14 에서는 **괄호 한 겹이 이동 한 번**이었다.
- ★★ C++14 라도 **플래그를 안 붙이면** 출력이 C++20 과 같다((6)의 첫 블록과 대조) — **그때는** 「**허용된 최적화**」였고, 지금은 **규칙**이다.

**비용** — C++17 이후 값 반환은 **추가 복사·이동이 0**이다. 「값으로 돌려주면 느리다」는 여기서 끊긴다.

### (7) 수명 — prvalue 는 늘어나고 xvalue 는 늘 것이 없다

**언제 쓰나** — 임시를 참조로 받아 두는 코드를 읽을 때.

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

```text
   [A] const Noisy& r = make(1);     ctor ─ 블록 안 ─ dtor      블록 끝까지 산다
   [B] Noisy&&      r = make(2);     ctor ─ 블록 안 ─ dtor      같다
   [C] make(3);                      ctor ─ dtor ─ 다음 문장     문장 끝에 죽는다
   [D] Noisy&& r = static_cast<Noisy&&>(local);
                                     ctor ─ 블록 안 ─ dtor      local 의 수명 그대로
```

- ★★ **[A]와 [B]가 같다** — 수명 연장은 **`const T&` 만의 특권이 아니다.** `T&&` 도 똑같이 늘린다.
- ★★★ **[D]는 늘린 게 아니다.** `&r == &local` 이 **1** 이다 — **xvalue 는 이미 있는 객체를 가리킬 뿐**이라 늘릴 임시가 없다.
- ★ 「그래서 무엇이 댕글링되나」의 정본은 [목록의 **30번 주제**](../30-dangling-references-and-lifetime-extension/)다. 여기서는 **[C]와 [D]의 차이**까지만 본다.
- ★ 「`const T&` 가 임시를 받는다」 자체의 정본은 형제 [`07번`](../07-references-vs-pointers/)이다.

**비용** — 수명 연장은 **코드를 한 줄도 더 만들지 않는다.** 소멸자가 불리는 **자리만** 바뀐다.

### (8) ★★ 범주가 오버로드를 가른다

**언제 쓰나** — `f(T&)` · `f(const T&)` · `f(T&&)` 를 같이 두었을 때.

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

| 부른 식 | 범주 | 후보 셋 | 후보 둘(`const&`·`&&`) | 후보 하나(`const&`) |
|---|---|---|---|---|
| `f(i)` | lvalue | `f(int&)` | `g(const int&)` | `h(const int&)` |
| `f(ci)` | const lvalue | `f(const int&)` | — | — |
| `f(42)` | prvalue | ★ `f(int&&)` | `g(int&&)` | `h(const int&)` |
| `f(std::move(i))` | xvalue | ★ `f(int&&)` | `g(int&&)` | `h(const int&)` |
| `f(std::move(ci))` | const xvalue | ★ `f(const int&)` | — | — |

- ★★★ **prvalue 와 xvalue 가 같은 칸으로 간다** — 둘을 묶은 이름이 **rvalue** 이고, **`T&&` 가 그 칸을 받는다.**
- ★★★ **`const` 를 붙이면 rvalue 라도 `T&&` 로 못 간다** — `std::move(ci)` 가 `f(const int&)` 로 떨어진다.\
  **이것이 [목록의 09번 주제](../09-rvalue-references-move-and-forward/)에서 「`const` 를 `move` 하면 복사가 된다」로 이어지는 바로 그 자리**다.
- ★ **`const T&` 는 셋 다 받는다** — 그래서 「하나만 둘 거면 `const T&`」가 기본값이 된다([목록의 **11번 주제**](../11-choosing-parameter-passing/)).
- ★ 오버로드 해석의 **전체 순서**(정확 일치 → 승격 → 변환)는 형제 [`01번`](../01-function-overloading-and-overload-resolution/)이 정본이다.

### (9) 범주가 막는 것 — 그리고 안 막는 것

**언제 쓰나** — 「왜 이 참조가 안 묶이지」가 뜰 때.

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

```text
                    lvalue    const lvalue   prvalue   xvalue
   T&         <-      OK          X            X         X
   const T&   <-      OK          OK           OK        OK
   T&&        <-      X           X            OK        OK
   const T&&  <-      X           X            OK        OK
```

- ★★★ **`const T&` 가 유일하게 네 칸을 다 받는다.** 그 대가는 「**훔칠 수 없다**」는 것이다.
- ★ 같은 여섯 줄을 clang 으로도 던졌다 — **여섯 개 그대로**이고 문구만 다르다.

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

그런데 **「rvalue 에는 대입을 못 한다」는 반만 맞다.** 클래스는 받는다.

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

- ★★★ **`S{} = s;` 와 `std::string("x") += "y";` 가 컴파일된다.** 내장 타입만 왼쪽 자리를 lvalue 로 요구한다.
- ★ **막고 싶으면 `&` 한정자**를 단다 — `Guarded& operator=(const Guarded&) &`.

막히는 쪽 넷도 같이 던졌다.

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

- ★★ **`S{}.m = 7` 이 에러**다. `S{}.m` 은 **xvalue** 이고 xvalue 는 **rvalue** 라, 내장 대입의 왼쪽에 못 온다.\
  ★ **(2)에서 `int&&` 로 찍힌 바로 그 식**이다 — 「참조 타입으로 찍혔다」가 「lvalue 다」를 뜻하지 않는다.
- ★ **비트필드 lvalue 는 `int&` 에 못 묶인다** — 범주는 맞는데 **다른 이유로** 막히는 칸이다.

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

### (10) ★★ 규칙을 플래그로 낮추면 — 「종료 코드가 0인데 ill-formed」

**언제 쓰나** — 남의 빌드에 `-fpermissive` 가 붙어 있을 때.

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

**같은 소스에 `-fpermissive` 를 붙이면 경고로 내려간다.**

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

- ★★★ **`cc exit=0` 이고 프로그램이 돈다.** 그런데 **`s.m` 이 1** 이다 — **7 은 물질화된 임시에 쓰였고 그 임시는 바로 죽었다.**
- ★★★ **`-pedantic-errors` 로도 안 돌아온다** — 아래가 그 확인이다.

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

- ★★ 이것이 이 갈래의 **고정 항목**이다 — 「**종료 코드가 0인데 ill-formed**」.\
  ★ 다만 **이번 판은 한 겹 더 나쁘다** — 다른 사례들은 `-pedantic-errors` 로 되살아나는데 **이것은 안 산다.**\
  `-fpermissive` 는 「**표준 위반을 경고로 낮춘다**」가 아니라 「**그 진단을 경고로 고정한다**」에 가깝다.

### (11) 다섯 층 — 무엇이 표준이고 무엇이 도구인가

★★ **이 주제는 「표준」 칸이 압도적으로 두껍다.** 값 범주는 **표준이 격자로 정해 놓은 것**이라\
구현이 고를 여지가 거의 없다 — 두 컴파일러의 판정이 **한 칸도 다르지 않았다**(20 + 6 + 4 = 30칸).

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | **세 범주의 정의와 판정** · **참조 묶기 격자**((9)) · **오버로드 선택**((8)) · **문자열 리터럴이 lvalue**((4)) · **`S{}.m` 이 xvalue**((2)) · **`const T&`·`T&&` 가 prvalue 의 수명을 늘리는 것**((7)) · **`&` 한정자가 임시를 막는 것**((9)) | g++·clang **30칸 전부 일치** · `decltype` 창 + 실행 창 **양쪽** | ★ **「참조 타입으로 찍혔다」가 「대입할 수 있다」를 뜻하지 않는다**((9)) |
| **조건부 표준** | 표준판이 있을 때만 | ★ **xvalue·`T&&` 자체가 C++11부터** · ★★ **prvalue 물질화는 C++17부터** — `-fno-elide-constructors` 가 **C++20 에서는 무력**하고 **C++14 에서는 복사를 되살린다**((6)) | 같은 소스를 `-std=c++20` 과 `-std=c++14` 로 두 번 | ★ **`-std=` 만으로는 안 보인다** — **플래그를 붙여 비교해야** 갈린다 |
| **구현 정의** | 문서화 의무가 있다 | 진단 문구 · **에러를 몇 개로 세는가** · clang 의 `-Wunevaluated-expression` **2건**(g++ 는 0건) · clang 의 기본 에러 상한 **20** | 두 컴파일러 대조 | — |
| **미명시** | 몇 가지 중 하나 | ★★ **같은 문자열 리터럴이 한 덩어리로 합쳐지는지**((4) 의 `a == b` 가 1) · 임시 객체를 **어디에 두는지** | 실행 1판 | ★★ **출력이 「1」이라 근거처럼 보인다** — 이 칸은 **미명시라고 적어야** 안 쓰인다 |
| **UB** | 아무 일이나 | ★ **이 주제에는 없다.** 범주 위반은 **전부 컴파일 에러**였다(30칸 중 30) | — | ★ 수명이 끝난 임시를 읽는 쪽이 UB 이고 **그 정본은 [목록의 30번 주제](../30-dangling-references-and-lifetime-extension/)다** |

**「도구가 못 보는 것」을 층마다 — 전용 표**

| 사실 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | 비고 |
|---|---|---|---|
| 스무 식의 범주((2)) | **에러 20** | **에러 20 + 경고 2** | ★ 판정은 같고 **clang 만 `-Wunevaluated-expression`** |
| 참조 묶기 여섯((9)) | **에러 6** | **에러 6** | 문구만 다르다 |
| 대입 넷((9)) | **에러 4** | **에러 4** | 〃 |
| ★★ **`-fpermissive` 를 붙인 `S{}.m = 7`**((10)) | ★★★ **경고 1 · `cc exit=0`** | (던지지 않았다) | ★★★ **`-pedantic-errors` 로도 에러가 안 된다** |
| 리터럴이 합쳐졌는지((4)) | — | — | ★ **컴파일러가 말해 주지 않는다** — 실행해서 비교해야 보이고, **그래도 미명시**다 |
| C++17 물질화((6)) | — | — | ★ **생성자 로그로만 보인다.** 경고도 진단도 없다 |

- ★★★ **이 주제에서 「도구가 못 보는 것」은 대부분 「도구가 말해 줄 이유가 없는 것」이다** —\
  범주 위반은 **이미 하드 에러**라 조용히 지나갈 자리가 (10) 하나뿐이었다.

## 문법 — 형태와 규칙

### 형태 — 범주를 만드는 식들

```text
   prvalue 를 만드는 것
     리터럴           42 · 'c' · 1.5 · true · nullptr       ※ 문자열 리터럴은 빼고
     계산 식          i + 1 · i * 2 · !flag
     후위 증감        i++ · i--
     값 반환 호출     byval()
     임시 객체        S{} · S(1) · T()
     람다 식          [](){}                                 (이 문서는 안 던졌다)

   lvalue 를 만드는 것
     변수·멤버 이름   i · s.m · ns::g
     전위 증감        ++i · --i
     첨자             arr[0] · v[0] · "abc"[0]
     역참조           *p
     T& 반환 호출     bylref()
     문자열 리터럴    "abc"                                  ★ 리터럴 중 유일

   xvalue 를 만드는 것
     std::move        std::move(i)
     rvalue 참조 캐스트 static_cast<T&&>(i)
     T&& 반환 호출    byrref()
     rvalue 의 멤버   S{}.m · std::move(s).m
```

### 형태 — 「그래서 무엇으로 받나」

```text
   void f(T&);          lvalue 만            "고치겠다"
   void f(const T&);    ★ 넷 다              "읽기만 하겠다"
   void f(T&&);         prvalue · xvalue     "가져가겠다"
   template <class T>
   void f(T&&);         ★ 전달 참조 — 규칙이 다르다 ([목록의 **09번 주제**](../09-rvalue-references-move-and-forward/))
```

- ★★ **마지막 줄만 값 범주 규칙이 아니라 템플릿 추론 규칙으로 움직인다.** 그 정본은 [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)다.

### 금지 사례 — 던져서 받은 열

| 쓴 것 | g++ 의 첫 마디 | 어디서 |
|---|---|---|
| `int& e1 = 42;` | `cannot bind non-const lvalue reference ... to an rvalue` | (9) |
| `int&& e2 = i;` | `cannot bind rvalue reference ... to lvalue` | (9) |
| `int& e3 = ci;` | `binding reference ... discards qualifiers` | (9) |
| `int&& e4 = std::move(ci);` | 〃 | (9) |
| `int* e5 = &42;` | `lvalue required as unary '&' operand` | (9) |
| `42 = i;` | `lvalue required as left operand of assignment` | (9) |
| `S{}.m = 7;` | `using rvalue as lvalue [-fpermissive]` | (9)(10) |
| `Guarded{} = g;` | `passing 'Guarded' as 'this' argument discards qualifiers` | (9) |
| `int& br = x.b;`(비트필드) | `cannot bind bit-field ... to 'int&'` | (9) |
| `int arr2[3] = arr;`류 | (이 문서는 안 던졌다 — 형제 [`05번`](../05-auto-and-decltype-type-deduction/)의 배열 감쇠) | — |

### 고를 것을 손으로 돌리는 순서

```text
   1. 이 식에 이름이 있나?               없으면 prvalue 에서 끝
   2. std::move / T&& 반환 / rvalue 의 멤버를 거쳤나?   거쳤으면 xvalue
   3. 아니면 lvalue
   4. 확신이 안 서면 -> decltype((식)) 을 TypeOf 에 넣어 던진다   ((2))
```

## 어디서 틀리나

### 1. ★★★ 「rvalue 는 임시고 lvalue 는 변수다」

**틀렸다.** `std::move(i)` 는 **변수 `i` 그 자체**인데 rvalue(xvalue)다((7)의 [D]에서 `&r == &local` 이 **1**).\
반대로 `"abc"` 는 **리터럴인데 lvalue** 다((4)).\
★ **범주는** 「**무엇을 가리키나**」가 아니라 「**그 식이 무엇으로 쓰이기로 표시됐나**」다.

### 2. ★★★ 「`T&&` 로 선언된 것은 rvalue 다」

**틀렸다.** `void f(Noisy&& p)` 안에서 **`p` 는 lvalue** 다 — 이름이 있으니까.\
그래서 09 가 `std::forward`/`std::move` 를 한 번 더 쓴다.\
★ (2)에서 `S{}.m` 이 `int&&` 로 찍혔는데 (9)에서 **대입이 막히는 것**이 같은 함정의 뒷면이다.

### 3. ★★ 「prvalue 는 객체다」

C++17 부터 **아니다**((6)).\
`Noisy(Noisy(Noisy(2)))` 가 **생성자 한 번**이고, `-fno-elide-constructors` 가 **아무 일도 안 한다.**\
★ C++14 로 같은 소스를 던지면 `move` 가 **세 번** 나온다 — **판을 밝히지 않은 「복사가 몇 번 난다」는 전부 반쪽**이다.

### 4. ★★ 「값으로 돌려주면 복사가 난다」

C++17 부터 **안 난다**((6)의 `[1]`: `ctor` 하나).\
★ 이것이 [목록의 **11번 주제**](../11-choosing-parameter-passing/)에서 「싱크 매개변수는 값으로 받아도 된다」로 이어진다.

### 5. ★★ 「`const T&` 로 받으면 손해가 없다」

범주 면에서는 **네 칸을 다 받는** 가장 넓은 손이 맞다((9)).\
★ 그런데 「**훔칠 수 없다**」는 대가가 있고, 그 값을 보관하려면 **복사가 한 번 더** 난다.\
숫자는 [목록의 **11번 주제**](../11-choosing-parameter-passing/)가 센다 — 여기서 **추측으로 적지 않는다.**

### 6. ★★ 「`std::move(ci)` 는 이동한다」

**안 한다.** `const int&&` 가 되어 **`const T&` 오버로드로 떨어진다**((8)의 다섯째 줄).\
★ 클래스 타입이면 **조용히 복사 생성자가 불린다** — 경고 한 줄 없다. 실측은 [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)에 있다.

### 7. ★★ 「rvalue 에는 대입을 못 한다」

**내장 타입만** 그렇다((9)).\
`S{} = s;` 와 `std::string("x") += "y";` 는 **컴파일된다.**\
★ 막고 싶으면 **`&` 한정자**를 단다.

### 8. ★ 「`decltype(x)` 와 `decltype((x))` 는 같다」

**다르다** — 괄호 한 겹이 「이름」을 「식」으로 바꾼다.\
★ 그 규칙 자체의 정본은 형제 [`05번`](../05-auto-and-decltype-type-deduction/)이다.\
여기서는 **그 차이를 범주를 묻는 창으로 쓴다**((2)).

### 9. ★ 「`decltype` 안에 쓴 식은 실행된다」

**안 된다.** (3)의 마지막 줄이 `i=0` 이다 — `++i` 를 두 번 넣었는데 `i` 가 안 늘었다.\
★ **clang 만 그 자리에 경고를 준다**(`-Wunevaluated-expression`). g++ 는 조용하다.

### 10. ★ 「같은 문자열 리터럴은 같은 주소다」

**이 판에서는 그랬다**((4)의 `a == b` 가 1). **그런데 미명시다.**\
★ 「돌려 봤더니 1 이더라」를 **보장으로 적지 않는다** — 이 문서는 그 칸을 **흔들리는 칸**으로 선언했다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 정하나 | 근거 |
|---|---|---|
| 어떤 식이 어느 범주인가 | ★★★ **표준** | (2)(3) — 두 컴파일러 30칸 일치 |
| `T&`·`const T&`·`T&&` 가 무엇을 받나 | ★★★ **표준** | (9) |
| 오버로드가 어느 쪽으로 가나 | ★★★ **표준** | (8) |
| prvalue 가 복사 없이 초기화하는 것(C++17\~) | ★★ **표준**(판이 정한다) | (6) — `-fno-elide-constructors` 무력 |
| `const T&`·`T&&` 가 임시의 수명을 늘리는 것 | ★★ **표준** | (7) |
| 같은 리터럴이 합쳐지는지 | ★★ **미명시** | (4) — `a == b` 가 1 이었을 **뿐** |
| 임시를 스택 어디에 놓는지 | **미명시** | 이 문서는 주소를 **싣지 않았다** |
| 진단 문구·에러 개수·경고 이름 | **구현 정의** | g++ 대 clang |
| `-fpermissive` 가 범주 위반을 경고로 낮추는 것 | ★★★ **도구**(표준 아님) | (10) |

## 언제 쓰고 언제 안 쓰나

- **매일 쓴다** — 오버로드를 둘 이상 둘 때, 참조를 매개변수로 받을 때, 「이 임시가 언제 죽나」를 따질 때.
- ★ **`decltype((식))` 창은 막혔을 때만 쓴다** — 평소 코드에 넣는 물건이 아니라 **진단 도구**다.
- ★★ **`-fpermissive` 는 쓰지 않는다.** 옛 코드를 컴파일하려고 붙이는 순간 (10) 같은 자리가 **조용히 통과한다.**
- ★ **「이 식이 xvalue 인가」를 외워서 답하려 하지 마라** — 격자를 **다시 그려서** 답한다(위 (1)).

## 핵심 문장

- **값 범주는 타입과 다른 축이다** — 같은 `int` 인 두 식이 다른 칸에 있다.
- **「이름이 있나」와 「훔쳐도 되나」 두 질문이 세 칸을 만든다.**
- **`T&&` 로 선언된 이름은 lvalue 다** — 그래서 09 가 필요하다.
- **C++17 부터 prvalue 는 객체가 아니다** — 생략할 복사가 없다.
- **범주를 모르겠으면 `decltype((식))` 을 던져라** — 컴파일러가 타입으로 답한다.

## 관련 자료

- 형제 [`05-auto-and-decltype-type-deduction/`](../05-auto-and-decltype-type-deduction/) — **`decltype` 이 이름과 식을 가르는 규칙**이 거기 정본이다. 여기는 **그 창으로 범주를 묻는 것**부터.
- 형제 [`07-references-vs-pointers/`](../07-references-vs-pointers/) — **참조가 무엇인가**가 거기. 여기는 **어떤 식에 참조가 묶이나**부터.
- 형제 [`01-function-overloading-and-overload-resolution/`](../01-function-overloading-and-overload-resolution/) — **오버로드 해석의 전체 순서**가 거기. 여기는 **범주가 후보를 가르는 한 겹**만.
- 형제 [`04-brace-initialization-narrowing-and-initializer-list/`](../04-brace-initialization-narrowing-and-initializer-list/) — `S{}` 라는 **임시를 만드는 문법**이 거기.
- [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/) — `std::move`·`std::forward`. **여기서 정한 범주를 만드는 법**이다.
- [목록의 **11번 주제**](../11-choosing-parameter-passing/) — 그래서 **무엇으로 받나**. 08 → 09 → 11 사슬의 끝.
- [목록의 **30번 주제**](../30-dangling-references-and-lifetime-extension/) — 수명 연장이 **안 되는** 자리와 댕글링.
- C 갈래 [`20-null-terminated-strings-and-string-literals/`](../../../c/syntax/20-null-terminated-strings-and-string-literals/) — **문자열 리터럴이 배열이라는 것**은 거기가 정본. 여기는 **그것이 lvalue 라는 것**만.
- 대비 — [`../../../rust/syntax/08-ownership-and-move/`](../../../rust/syntax/08-ownership-and-move/): Rust 는 **이동이 기본**이라 「이 식이 rvalue 인가」를 물을 일이 없다. C++ 는 **기본이 복사**이고 rvalue 는 **식에 붙는 표시**다.

## 용어 풀이

- **값 범주(value category)** — 식에 붙는 분류. 타입과 다른 축이다. 예: `i` 와 `i + 1` 은 타입이 같고 범주가 다르다.
- **lvalue** — 이름이 있고 훔쳐 갈 수 없는 식. 예: `i` · `arr[0]` · `"abc"`.
- **prvalue(pure rvalue)** — 아직 객체가 아닌 식. 예: `42` · `f()` · `S{}`.
- **xvalue(eXpiring value)** — 이름은 있는데 「가져가도 된다」고 표시된 식. 예: `std::move(i)` · `S{}.m`.
- **glvalue** — lvalue + xvalue. 「어딘가에 있는 객체를 가리키는 식」.
- **rvalue** — prvalue + xvalue. 「훔쳐 가도 되는 식」.
- **물질화(temporary materialization)** — prvalue 를 실제 객체로 바꾸는 변환(C++17부터). 예: `const T& r = f();` 에서 일어난다.
- **`decltype((식))`** — 괄호를 한 겹 씌워 **이름이 아니라 식으로** 묻는 형태. 답이 `T`/`T&`/`T&&` 로 나온다.
- **`-fpermissive`** — g++ 가 표준 위반 일부를 **경고로 낮추는** 플래그. 표준의 일부가 아니다.
- **`&` 한정자(ref-qualifier)** — 멤버 함수를 **lvalue 에서만** 부르게 제한하는 표시. 예: `operator=(...) &`.
- **불완전 타입(incomplete type)** — 선언만 있고 정의가 없는 타입. 이 문서는 **에러 문구에 타입을 찍는 용도**로 쓴다.

## 더 들어가면

- **네 번째 범주는 없다** — 격자의 네 번째 칸(「이름이 없는데 훔칠 수 없는 것」)은 **비어 있다.** 그래서 범주가 셋이다.
- ★ **`decltype(auto)`** — 반환 타입에 범주를 그대로 실어 나르는 도구. 정본은 형제 [`05번`](../05-auto-and-decltype-type-deduction/).
- ★ **비트필드는 격자 밖에서 한 번 더 막힌다**((9)) — 범주는 lvalue 인데 `int&` 에 못 묶는다. 정본은 C 갈래 [`24-bit-fields/`](../../../c/syntax/24-bit-fields/).
- ★ **이 문서가 안 던진 것** — 람다 식의 범주 · `co_await`/`co_yield` 식 · 클래스 prvalue 를 `auto&&` 로 받는 것 · `std::forward` 의 범주([목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)).
