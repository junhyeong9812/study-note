# cpp/syntax/05 — `auto`·`decltype` 과 타입 추론 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — `auto` 자리표시자](https://en.cppreference.com/w/cpp/language/auto) · [`decltype`](https://en.cppreference.com/w/cpp/language/decltype) · [템플릿 인자 추론](https://en.cppreference.com/w/cpp/language/template_argument_deduction) · [함수 반환 타입 추론](https://en.cppreference.com/w/cpp/language/function#Return_type_deduction) · [`std::vector<bool>`](https://en.cppreference.com/w/cpp/container/vector_bool) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html)
> **실행 검증** — 이 문서의 모든 타입·출력·경고·에러는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`dedu01.cpp` \~ `dedu10.cpp`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 타입을 찍는 블록은 **긴 진단에서 타입 줄만 남기는 필터**를 배너에 적어 두었다(`| grep 'incomplete type'`).\
> 그러니 실린 것은 「생략한 일부」가 아니라 **그 명령의 전체 출력**이다.
> **버전** — `auto`·`decltype` 은 **C++11부터**. **`decltype(auto)` 와 일반 함수의 반환 타입 추론은 C++14부터**.\
> **`auto x{1}` 이 `int` 인 것은 C++17부터**. **매개변수 `auto`(축약 템플릿)는 C++20부터**((10)).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 타입은 컴파일러 진단으로 접지했다.
> **경계** — 「템플릿 인자 추론」의 정본은 목록의 **31번 주제**다.\
> `auto` 의 규칙은 그것과 **거의 같지만 한 곳이 다르고**(중괄호 목록), 여기서는 **`auto` 쪽만** 쓴다((2)).\
> 「값 범주(lvalue·xvalue·prvalue)」는 목록의 **08번 주제**, 「전달 참조와 `std::forward`」는 목록의 **09번 주제**,\
> 「댕글링과 수명」은 목록의 **30번 주제**가 정본이다.\
> 「배열이 포인터로 감쇠하는 것」은 C 갈래 [`16번`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/)이 정본이다((4)).\
> 「참조가 무엇인가」는 형제 [`07번`](../07-references-vs-pointers/)이다.\
> 「`auto x{1}` 대 `auto x = {1}`」의 정본은 형제 [`04번`](../04-brace-initialization-narrowing-and-initializer-list/)이고 여기서는 **되짚기만** 한다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 컴파일 시간 | ★ **`TypeOf<...>` 꺾쇠 안의 타입 이름** — 이 주제의 답 자체다 |
> | 댕글링 참조가 **읽은 값**(이 문서는 **싣지 않았다**) | **진단 본문** · `파일:줄:칸` · **경고 이름** |
> | UB 로 죽을 때 셸이 찍는 신호 메시지 | **`cc exit` 와 `run exit`**(갈라 적었다 — 댕글링 판은 `run exit=139`) |
> | — | `sizeof` 값 · 복사 생성자가 **몇 번** 불렸나 |

## 한눈에 — 쉽게 말하면

**`auto` 는 「컴파일러야 타입 좀 적어 줘」가 아니다. 「이 값을 함수 매개변수처럼 받아라」다.**

그래서 **함수 매개변수가 하는 일을 그대로 한다** — **복사할 때 `const` 와 참조를 떼어 버린다.**\
`decltype` 은 정반대다 — **식을 글자 그대로 베낀다.** 참조도 `const` 도 남긴다.

| 비유 | 실체 |
|---|---|
| **「사본을 한 장 떠 드릴게요」** — 원본의 열람 제한·보관함 위치는 안 따라온다 | `auto x = ...` — **`const` 와 참조가 떨어진다** |
| **「원본 서류함을 가리키는 쪽지」** | `auto& x = ...` · `const auto& x = ...` |
| **「사무실 상황에 맞춰 원본이든 사본이든」** | `auto&& x = ...` — 전달 참조 |
| ★ **「저 칸에 뭐라고 적혀 있는지 그대로 읽어 주세요」** | `decltype(식)` — **참조도 `const` 도 그대로** |
| ★★ **괄호를 치면 「그 칸」이 아니라 「그 칸을 가리키는 식」이 된다** | `decltype((i))` 가 **`int&`** 다((2)) |

- ★★★ **`auto` 의 규칙은 「함수 매개변수 추론」과 같다.** `auto x = e;` 는\
  `template <class T> void f(T x);` 에 `e` 를 넘긴 것과 **같은 추론**을 한다.\
  그래서 **`const`·참조가 떨어지고, 배열과 함수는 포인터로 감쇠한다**((1)·(4)).
- ★★ **`decltype` 은 추론이 아니라 조회다.** 괄호 하나가 **이름**을 **식**으로 바꾸면서 답이 `T` 에서 `T&` 로 바뀐다((2)).
- ★★ **`auto` 가 늘 복사하는 것은 아니다** — `vector<bool>` 처럼 **프록시를 돌려주는 타입**에서는\
  `auto` 가 **프록시를 복사**하므로 원본을 계속 보게 된다((5)).

```text
   auto x = e;        "함수 매개변수처럼 받아라"
                       ├─ 맨 위 const/volatile 을 뗀다      const int   -> int
                       ├─ 참조를 뗀다                       const int&  -> int
                       ├─ 배열/함수를 감쇠시킨다            int[3] -> int*,  int(double) -> int(*)(double)
                       └─ 가리키는 곳의 const 는 남긴다     const int*  -> const int*

   auto&  x = e;      참조를 붙인다 — const 는 따라온다
   auto&& x = e;      전달 참조 — lvalue 면 T&, rvalue 면 T&&

   decltype(이름)     그 실체의 선언 타입을 그대로       int, const int, int[3], int(double)
   decltype(식)       식의 타입 + 값 범주
                       ├─ lvalue 식   -> T&      decltype((i)) == int&
                       ├─ xvalue 식   -> T&&
                       └─ prvalue 식  -> T       decltype(i + 1) == int

   decltype(auto)     "auto 자리에 decltype 규칙을 써라" (C++14)
```

> **`auto`** — 초기값에서 타입을 **추론**하는 자리표시자. **템플릿 매개변수 추론과 같은 규칙**을 쓴다.

> **`decltype(e)`** — 식 `e` 의 타입을 **조회**한다. 추론이 아니다. `e` 를 **평가하지 않는다**.

> **`decltype(auto)`**(C++14) — 초기값·반환값에 **`decltype` 규칙**으로 타입을 정한다.\
> **참조와 `const` 를 그대로 남기고 싶을 때** 쓴다.

> **전달 참조(forwarding reference)** — 추론되는 자리의 `auto&&`/`T&&`.\
> lvalue 를 받으면 `T&`, rvalue 를 받으면 `T&&` 가 된다. 정본은 목록의 **09번 주제**.

> **프록시 타입(proxy type)** — 「그 자리를 대신 가리키는 임시 객체」.\
> `std::vector<bool>::reference` 가 대표다. `auto` 로 받으면 **값이 아니라 그 대리인이 복사된다**((5)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **`auto` 는 무엇을 떨어뜨리나** — `const`·참조·배열/함수 감쇠를 **하나씩** 댈 수 있나((1)·(4)).
2. **`decltype` 은 무엇을 남기나** — 「이름」과 「식」이 다른 답을 내는 이유를 말하고,\
   **괄호 하나가 바꾸는 것**을 보일 수 있나((2)).
3. **`auto` 가 「복사」가 아닐 때가 있나** — 있다((5)). 그것을 **실행 출력으로** 보일 수 있나.

## 동작 방식

### (0) 이 주제가 쓰는 세 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **의도적 타입 에러**(`TypeOf<T>`) | ★ **추론 결과 그 자체** — 이 주제의 답은 전부 타입이다 | (1)\~(4)·(7) |
| **실행 출력** | 프록시가 무는 것 · 복사 횟수 · `decltype(auto)` 가 남긴 참조 | (5)·(6)·(8) |
| **컴파일 진단 + 종료 코드** | `auto` 가 못 쓰이는 자리 · 댕글링 경고 · 표준판 차이 | (7)·(9)·(10) |

★★★ **첫 번째 창이 이 주제의 전부다.** 타입은 **실행 출력으로 안 보인다** —
`auto a = ci;` 와 `auto& b = ci;` 는 둘 다 컴파일되고 아무것도 안 찍는다.

```text
   template <class T> struct TypeOf;    // 선언만 — 정의가 없다
   TypeOf<decltype(a)> probe;           // 정의가 없으니 «불완전 타입» 에러가 난다
                                        // 그 에러 문구에 g++ 가 T 를 적어 준다:
                                        //   error: aggregate 'TypeOf<const int&> probe'
                                        //          has incomplete type and cannot be defined
```

- ★ **왜 `typeid(x).name()` 을 안 쓰나** — 그쪽은 **`const` 와 참조를 지워서 답한다.**\
  이 주제가 묻는 것이 정확히 그 둘이므로 **쓸 수 없는 도구**다.
- ★ clang 은 같은 사실을 `implicit instantiation of undefined template 'TypeOf<const int &>'` 로 말한다 —\
  **문구는 다르고 타입은 같다**((1)).

### (1) `auto` 가 떨어뜨리는 것 — 아홉 줄

**언제 쓰나** — `auto` 를 쓸 때마다. **외울 것은 세 가지를 뗀다는 것**이다.

```text
===== 소스: dedu01.cpp =====
// auto 가 무엇을 떨어뜨리나 — 아홉 줄
template <class T> struct TypeOf;   // 선언만 — 정의가 없다

int main() {
    int        i  = 0;
    const int  ci = 0;
    const int& cr = i;
    const int* cp = &i;
    int* const pc = &i;

    auto a1 = ci;         // ① 맨 위 const
    auto a2 = cr;         // ② 참조 + const
    auto a3 = cp;         // ③ 가리키는 곳의 const
    auto a4 = pc;         // ④ 포인터 자신의 const
    auto& b1 = ci;        // ⑤ auto&
    const auto& b2 = i;   // ⑥ const auto&
    auto&& c1 = i;        // ⑦ 전달 참조에 lvalue
    auto&& c2 = 1;        // ⑧ 전달 참조에 rvalue
    auto  d1 = cr + 0;    // ⑨ 식의 결과

    TypeOf<decltype(a1)> t1; TypeOf<decltype(a2)> t2; TypeOf<decltype(a3)> t3;
    TypeOf<decltype(a4)> t4; TypeOf<decltype(b1)> t5; TypeOf<decltype(b2)> t6;
    TypeOf<decltype(c1)> t7; TypeOf<decltype(c2)> t8; TypeOf<decltype(d1)> t9;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu01.cpp -o ex 2>&1 | grep 'incomplete type' (cc exit=1) =====
dedu01.cpp:21:26: error: aggregate ‘TypeOf<int> t1’ has incomplete type and cannot be defined
dedu01.cpp:21:51: error: aggregate ‘TypeOf<int> t2’ has incomplete type and cannot be defined
dedu01.cpp:21:76: error: aggregate ‘TypeOf<const int*> t3’ has incomplete type and cannot be defined
dedu01.cpp:22:26: error: aggregate ‘TypeOf<int*> t4’ has incomplete type and cannot be defined
dedu01.cpp:22:51: error: aggregate ‘TypeOf<const int&> t5’ has incomplete type and cannot be defined
dedu01.cpp:22:76: error: aggregate ‘TypeOf<const int&> t6’ has incomplete type and cannot be defined
dedu01.cpp:23:26: error: aggregate ‘TypeOf<int&> t7’ has incomplete type and cannot be defined
dedu01.cpp:23:51: error: aggregate ‘TypeOf<int&&> t8’ has incomplete type and cannot be defined
dedu01.cpp:23:76: error: aggregate ‘TypeOf<int> t9’ has incomplete type and cannot be defined
```

| 줄 | 쓴 것 | 추론된 타입 | 무엇이 떨어졌나 |
|---|---|---|---|
| ① | `auto a1 = ci;`(`const int`) | **`int`** | 맨 위 `const` |
| ② | `auto a2 = cr;`(`const int&`) | **`int`** | 참조 + `const` |
| ③ | `auto a3 = cp;`(`const int*`) | ★ **`const int*`** | ★ **아무것도** — 가리키는 곳의 `const` 는 타입의 일부다 |
| ④ | `auto a4 = pc;`(`int* const`) | **`int*`** | 맨 위 `const`(포인터 자신의 것) |
| ⑤ | `auto& b1 = ci;` | **`const int&`** | — `auto&` 는 `const` 를 떼지 않는다 |
| ⑥ | `const auto& b2 = i;` | **`const int&`** | — 직접 붙였다 |
| ⑦ | `auto&& c1 = i;`(lvalue) | ★ **`int&`** | 전달 참조 — lvalue 라 `T&` |
| ⑧ | `auto&& c2 = 1;`(rvalue) | ★ **`int&&`** | 전달 참조 — rvalue 라 `T&&` |
| ⑨ | `auto d1 = cr + 0;` | **`int`** | 식의 결과는 이미 prvalue `int` 다 |

- ★★★ **규칙을 한 문장으로** — 「**`auto x = e;` 는 `template <class T> void f(T x)` 에 `e` 를 넘긴 것과 같은 추론이다.**」\
  그러니 **맨 위 `cv` 한정자와 참조가 떨어진다.**
- ★★ **③과 ④를 가르는 것은** 「`const` 가 어디에 붙었나」다. `const int*` 의 `const` 는\
  **가리키는 대상**에 붙어 있어 **타입의 일부**이고, `int* const` 의 `const` 는 **포인터 자신**에 붙어 있어 **맨 위**다.\
  맨 위 것만 떨어진다. 선언을 읽는 규칙의 정본은 C 갈래 [`01번`](../../../c/syntax/01-declaration-syntax-and-reading/)이다.
- ★ **⑦/⑧은 전달 참조**다. `auto&&` 는 `&&` 가 아니라 「**받은 대로**」를 뜻한다 — 정본은 목록의 **09번 주제**.

clang 도 **같은 타입**을 답한다(문구만 다르다).

```text
===== 소스: dedu01.cpp =====
// auto 가 무엇을 떨어뜨리나 — 아홉 줄
template <class T> struct TypeOf;   // 선언만 — 정의가 없다

int main() {
    int        i  = 0;
    const int  ci = 0;
    const int& cr = i;
    const int* cp = &i;
    int* const pc = &i;

    auto a1 = ci;         // ① 맨 위 const
    auto a2 = cr;         // ② 참조 + const
    auto a3 = cp;         // ③ 가리키는 곳의 const
    auto a4 = pc;         // ④ 포인터 자신의 const
    auto& b1 = ci;        // ⑤ auto&
    const auto& b2 = i;   // ⑥ const auto&
    auto&& c1 = i;        // ⑦ 전달 참조에 lvalue
    auto&& c2 = 1;        // ⑧ 전달 참조에 rvalue
    auto  d1 = cr + 0;    // ⑨ 식의 결과

    TypeOf<decltype(a1)> t1; TypeOf<decltype(a2)> t2; TypeOf<decltype(a3)> t3;
    TypeOf<decltype(a4)> t4; TypeOf<decltype(b1)> t5; TypeOf<decltype(b2)> t6;
    TypeOf<decltype(c1)> t7; TypeOf<decltype(c2)> t8; TypeOf<decltype(d1)> t9;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic dedu01.cpp -o ex 2>&1 | grep 'implicit instantiation' (cc exit=1) =====
dedu01.cpp:21:26: error: implicit instantiation of undefined template 'TypeOf<int>'
dedu01.cpp:21:51: error: implicit instantiation of undefined template 'TypeOf<int>'
dedu01.cpp:21:76: error: implicit instantiation of undefined template 'TypeOf<const int *>'
dedu01.cpp:22:26: error: implicit instantiation of undefined template 'TypeOf<int *>'
dedu01.cpp:22:51: error: implicit instantiation of undefined template 'TypeOf<const int &>'
dedu01.cpp:22:76: error: implicit instantiation of undefined template 'TypeOf<const int &>'
dedu01.cpp:23:26: error: implicit instantiation of undefined template 'TypeOf<int &>'
dedu01.cpp:23:51: error: implicit instantiation of undefined template 'TypeOf<int &&>'
dedu01.cpp:23:76: error: implicit instantiation of undefined template 'TypeOf<int>'
```

### (2) `decltype` — 이름과 식이 다른 답을 낸다

**언제 쓰나** — 「저 식이 무슨 타입이지?」를 코드로 적을 때. **괄호를 조심한다.**

```text
===== 소스: dedu02.cpp =====
// decltype 은 「식을 그대로 베낀다」 — 괄호 하나가 답을 바꾼다
#include <vector>

template <class T> struct TypeOf;

struct S { int m; };
int  f(double);
int& g();

int main() {
    int i = 0;
    const int ci = 0;
    S s{0};
    int arr[3]{};
    std::vector<int> v{1, 2, 3};

    TypeOf<decltype(i)>      y1;   // 이름
    TypeOf<decltype((i))>    y2;   // 괄호를 씌운 식
    TypeOf<decltype(ci)>     y3;
    TypeOf<decltype((ci))>   y4;
    TypeOf<decltype(s.m)>    y5;   // 멤버 이름
    TypeOf<decltype((s.m))>  y6;
    TypeOf<decltype(f)>      y7;   // 함수 이름
    TypeOf<decltype(f(1.0))> y8;   // 호출 식
    TypeOf<decltype(g())>    y9;   // 참조를 돌려주는 호출
    TypeOf<decltype(arr)>    ya;   // 배열
    TypeOf<decltype(v[0])>   yb;   // 첨자 식
    TypeOf<decltype(i + 1)>  yc;   // 계산 식
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu02.cpp -o ex 2>&1 | grep 'incomplete type' (cc exit=1) =====
dedu02.cpp:17:30: error: aggregate ‘TypeOf<int> y1’ has incomplete type and cannot be defined
dedu02.cpp:18:30: error: aggregate ‘TypeOf<int&> y2’ has incomplete type and cannot be defined
dedu02.cpp:19:30: error: aggregate ‘TypeOf<const int> y3’ has incomplete type and cannot be defined
dedu02.cpp:20:30: error: aggregate ‘TypeOf<const int&> y4’ has incomplete type and cannot be defined
dedu02.cpp:21:30: error: aggregate ‘TypeOf<int> y5’ has incomplete type and cannot be defined
dedu02.cpp:22:30: error: aggregate ‘TypeOf<int&> y6’ has incomplete type and cannot be defined
dedu02.cpp:23:30: error: aggregate ‘TypeOf<int(double)> y7’ has incomplete type and cannot be defined
dedu02.cpp:24:30: error: aggregate ‘TypeOf<int> y8’ has incomplete type and cannot be defined
dedu02.cpp:25:30: error: aggregate ‘TypeOf<int&> y9’ has incomplete type and cannot be defined
dedu02.cpp:26:30: error: aggregate ‘TypeOf<int [3]> ya’ has incomplete type and cannot be defined
dedu02.cpp:27:30: error: aggregate ‘TypeOf<int&> yb’ has incomplete type and cannot be defined
dedu02.cpp:28:30: error: aggregate ‘TypeOf<int> yc’ has incomplete type and cannot be defined
```

| 쓴 것 | 타입 | 규칙 |
|---|---|---|
| `decltype(i)` | `int` | **이름** — 선언 타입 그대로 |
| `decltype((i))` | ★ **`int&`** | ★ **식** — `i` 는 lvalue 라 `T&` |
| `decltype(ci)` | `const int` | 이름 — `const` 가 남는다 |
| `decltype((ci))` | `const int&` | 식 — lvalue 라 `T&` |
| `decltype(s.m)` | `int` | **멤버 이름**도 이름이다 |
| `decltype((s.m))` | ★ **`int&`** | 괄호를 치면 식 |
| `decltype(f)` | `int(double)` | 함수 이름 — **함수 타입 자체**, 감쇠하지 않는다 |
| `decltype(f(1.0))` | `int` | **호출 식** — 반환 타입이 prvalue |
| `decltype(g())` | ★ **`int&`** | `g` 가 `int&` 를 돌려주므로 lvalue 식 |
| `decltype(arr)` | ★ **`int [3]`** | 배열 이름 — **감쇠하지 않는다** |
| `decltype(v[0])` | ★ **`int&`** | `vector<int>::operator[]` 가 `int&` 를 돌려준다 |
| `decltype(i + 1)` | `int` | prvalue 식 |

- ★★★ **괄호 하나가 「이름」을 「식」으로 바꾼다.** 이름이면 **선언 타입**, 식이면 **타입 + 값 범주**다.\
  값 범주와 `&`/`&&` 의 대응 규칙은 목록의 **08번 주제**가 정본이다.
- ★★ **`decltype` 은 식을 평가하지 않는다** — `decltype(f(1.0))` 은 `f` 를 **부르지 않는다.**\
  그래서 `f` 는 **선언만 있고 정의가 없어도** 된다(이 소스가 그렇다 — 링크까지 가지 않는다).
- ★★ **`auto` 와의 대비가 핵심이다** — `auto` 는 떨어뜨리고 `decltype` 은 남긴다.\
  `decltype(v[0])` 가 `int&` 인데 `auto x = v[0];` 는 `int` 다.

### (3) `decltype(auto)` — 둘을 잇는 것

**언제 쓰나** — **받은 것을 그대로 돌려주는 래퍼**를 쓸 때.

```text
===== 소스: dedu05.cpp =====
// 반환 타입 — auto 는 참조를 떨어뜨리고 decltype(auto) 는 남긴다
#include <cstdio>
#include <vector>

std::vector<int> g_v{10, 20, 30};

auto           f1(int i) { return g_v[i]; }
decltype(auto) f2(int i) { return g_v[i]; }

int main() {
    f2(0) = 99;
    std::printf("g_v[0] = %d  (f2 로 고쳤다)\n", g_v[0]);
    std::printf("f1(0)  = %d  (복사본이다)\n", f1(0));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
g_v[0] = 99  (f2 로 고쳤다)
f1(0)  = 99  (복사본이다)
```

- **`auto f1(int i) { return g_v[i]; }`** — `auto` 규칙이라 **참조가 떨어져 `int`** 다. **복사본**을 돌려준다.
- **`decltype(auto) f2(int i) { return g_v[i]; }`** — `decltype` 규칙이라 **`int&`** 다. 그래서 `f2(0) = 99;` 가 된다.

`f1` 쪽에 같은 대입을 하면 이렇게 막힌다.

```text
===== 소스: dedu06.cpp =====
// auto 반환에는 대입할 수 없다
#include <vector>

std::vector<int> g_v{10, 20, 30};
auto f1(int i) { return g_v[i]; }

int main() { f1(0) = 99; }
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu06.cpp -o ex (cc exit=1) =====
dedu06.cpp: In function ‘int main()’:
dedu06.cpp:7:16: error: lvalue required as left operand of assignment
    7 | int main() { f1(0) = 99; }
      |              ~~^~~
```

- ★ ``error: lvalue required as left operand of assignment`` — 「복사본이니 왼쪽에 못 놓는다」는 뜻이다.
- ★★ **래퍼를 쓸 때 `auto` 를 쓰면 조용히 복사본이 된다.** 성능만의 문제가 아니라 **의미가 바뀐다** —\
  `wrapper(v, 0) = 99;` 가 원본을 못 고치게 된다.

### (4) 배열과 함수 — `auto` 는 감쇠시키고 `auto&` 는 안 시킨다

**언제 쓰나** — 배열을 `auto` 로 받을 때. **크기가 사라진다.**

```text
===== 소스: dedu03.cpp =====
// 배열과 함수 — auto 는 감쇠시키고 auto& 는 안 시킨다
template <class T> struct TypeOf;

int f(double);

int main() {
    int arr[3]{};
    auto  a = arr;
    auto& b = arr;
    auto  c = f;
    auto& d = f;
    TypeOf<decltype(a)> t1; TypeOf<decltype(b)> t2;
    TypeOf<decltype(c)> t3; TypeOf<decltype(d)> t4;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu03.cpp -o ex 2>&1 | grep 'incomplete type' (cc exit=1) =====
dedu03.cpp:12:25: error: aggregate ‘TypeOf<int*> t1’ has incomplete type and cannot be defined
dedu03.cpp:12:49: error: aggregate ‘TypeOf<int (&)[3]> t2’ has incomplete type and cannot be defined
dedu03.cpp:13:25: error: aggregate ‘TypeOf<int (*)(double)> t3’ has incomplete type and cannot be defined
dedu03.cpp:13:49: error: aggregate ‘TypeOf<int (&)(double)> t4’ has incomplete type and cannot be defined
```

| 쓴 것 | 타입 |
|---|---|
| `auto a = arr;`(`int[3]`) | ★ **`int*`** — 크기가 사라졌다 |
| `auto& b = arr;` | ★ **`int (&)[3]`** — 크기가 남았다 |
| `auto c = f;`(`int(double)`) | **`int (*)(double)`** — 함수 포인터로 감쇠 |
| `auto& d = f;` | **`int (&)(double)`** — 함수 참조 |

- ★★ **이것이 「매개변수처럼 받는다」의 직접적인 결과**다. 함수 매개변수에서 배열이 포인터가 되는 것과\
  **같은 규칙**이고, 그 정본은 C 갈래 [`16-array-pointer-decay-and-function-parameters/`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/)다.
- ★ **크기를 지키려면 `auto&`**(또는 `std::array`·`std::span`)다. `std::span` 의 정본은 목록의 **46번 주제** 쪽이다.

### (5) ★★ `auto` 가 「복사」가 아닌 자리 — 프록시

**언제 쓰나** — `auto x = 컨테이너[i];` 를 쓸 때마다. **`vector<bool>` 이 대표다.**

```text
===== 소스: dedu04.cpp =====
// auto 가 「값을 복사한다」가 아닌 자리 — vector<bool> 의 프록시
#include <cstdio>
#include <vector>

int main() {
    std::vector<bool> vb{true, false, true};
    std::vector<char> vc{'a', 'b', 'c'};
    auto b0 = vb[0];
    auto c0 = vc[0];
    vb[0] = false;       // 원본을 건드린다
    vc[0] = 'z';
    std::printf("b0 = %d   (vb[0] = %d)\n", static_cast<int>(b0), static_cast<int>(vb[0]));
    std::printf("c0 = %c   (vc[0] = %c)\n", c0, vc[0]);
    std::printf("sizeof(b0) = %zu   sizeof(c0) = %zu\n", sizeof(b0), sizeof(c0));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
b0 = 0   (vb[0] = 0)
c0 = a   (vc[0] = z)
sizeof(b0) = 16   sizeof(c0) = 1
```

- ★★★ **`b0` 은 값이 아니라 대리인이다.** `vb[0] = false;` 로 원본을 바꿨더니 **`b0` 도 따라 바뀌었다.**\
  같은 줄을 `vector<char>` 로 하면 `c0` 은 **`'a'` 그대로**다.
- ★★ **`sizeof(b0) = 16`** 이 증거다. `bool` 하나가 16바이트일 리 없다 —\
  `std::vector<bool>::reference` 라는 **프록시 객체**(포인터 + 비트 마스크)가 복사된 것이다.
- ★ **`std::vector<bool>` 은 `bool` 을 비트로 눌러 담는 특수화**라 `operator[]` 가 **`bool&` 를 못 돌려준다.**\
  그래서 대리인을 돌려주고, `auto` 는 **그 대리인의 타입을 그대로 추론한다.**
- ★★ **고치는 법은 타입을 못 박는 것**이다 — `bool b0 = vb[0];` 또는 `auto b0 = static_cast<bool>(vb[0]);`.\
  ★ 「거의 언제나 `auto`」라는 조언의 **가장 큰 예외**가 여기다.
- ★ clang 도 **같은 답**이다.

```text
===== 소스: dedu04.cpp =====
// auto 가 「값을 복사한다」가 아닌 자리 — vector<bool> 의 프록시
#include <cstdio>
#include <vector>

int main() {
    std::vector<bool> vb{true, false, true};
    std::vector<char> vc{'a', 'b', 'c'};
    auto b0 = vb[0];
    auto c0 = vc[0];
    vb[0] = false;       // 원본을 건드린다
    vc[0] = 'z';
    std::printf("b0 = %d   (vb[0] = %d)\n", static_cast<int>(b0), static_cast<int>(vb[0]));
    std::printf("c0 = %c   (vc[0] = %c)\n", c0, vc[0]);
    std::printf("sizeof(b0) = %zu   sizeof(c0) = %zu\n", sizeof(b0), sizeof(c0));
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic dedu04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
b0 = 0   (vb[0] = 0)
c0 = a   (vc[0] = z)
sizeof(b0) = 16   sizeof(c0) = 1
```

### (6) ★★ 괄호 하나가 만드는 댕글링 — `decltype(auto)` 의 값

**언제 쓰나** — `decltype(auto)` 반환을 쓸 때. **`return (x);` 를 쓰지 마라.**

```text
===== 소스: dedu07.cpp =====
// decltype(auto) 가 참조를 남긴다는 것은 댕글링도 남긴다는 뜻이다
int make() { return 42; }

decltype(auto) leak() {
    int local = make();
    return (local);          // 괄호 하나 때문에 int& 가 된다
}

int main() { return leak(); }
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu07.cpp -o ex (cc exit=0) =====
dedu07.cpp: In function ‘decltype(auto) leak()’:
dedu07.cpp:6:13: warning: reference to local variable ‘local’ returned [-Wreturn-local-addr]
    6 |     return (local);          // 괄호 하나 때문에 int& 가 된다
      |            ~^~~~~~
dedu07.cpp:5:9: note: declared here
    5 |     int local = make();
      |         ^~~~~
```

- ★★★ **`return (local);` 의 괄호 때문에 반환 타입이 `int&` 가 된다**((2)의 규칙 그대로).\
  `return local;` 이면 `int` 였다. **괄호 하나가 지역 변수 참조 반환을 만든다.**
- ★★ **경고일 뿐이다 — `cc exit=0` 이다.** `-Wreturn-local-addr` 이 이름이고, 빌드는 그냥 된다.

clang 은 같은 자리를 이렇게 말한다.

```text
===== 소스: dedu07.cpp =====
// decltype(auto) 가 참조를 남긴다는 것은 댕글링도 남긴다는 뜻이다
int make() { return 42; }

decltype(auto) leak() {
    int local = make();
    return (local);          // 괄호 하나 때문에 int& 가 된다
}

int main() { return leak(); }
===== clang++ -std=c++20 -Wall -Wextra -pedantic dedu07.cpp -o ex 2>&1 | cat (cc exit=0) =====
dedu07.cpp:6:13: warning: reference to stack memory associated with local variable 'local' returned [-Wreturn-stack-address]
    6 |     return (local);          // 괄호 하나 때문에 int& 가 된다
      |             ^~~~~
1 warning generated.
```

UBSan 은 **묶는 순간**을 잡아 준다.

```text
===== 소스: dedu07.cpp =====
// decltype(auto) 가 참조를 남긴다는 것은 댕글링도 남긴다는 뜻이다
int make() { return 42; }

decltype(auto) leak() {
    int local = make();
    return (local);          // 괄호 하나 때문에 int& 가 된다
}

int main() { return leak(); }
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 -fsanitize=undefined dedu07.cpp -o ex && ./ex (cc exit=0 · run exit=139) =====
dedu07.cpp: In function ‘decltype(auto) leak()’:
dedu07.cpp:6:13: warning: reference to local variable ‘local’ returned [-Wreturn-local-addr]
    6 |     return (local);          // 괄호 하나 때문에 int& 가 된다
      |            ~^~~~~~
dedu07.cpp:5:9: note: declared here
    5 |     int local = make();
      |         ^~~~~
dedu07.cpp:6:18: runtime error: reference binding to null pointer of type 'int'
dedu07.cpp:9:26: runtime error: load of null pointer of type 'int'
```

- ★★ **`runtime error: reference binding to null pointer of type 'int'` 두 줄**이 나오고\
  **`run exit=139`**(SIGSEGV)로 죽는다. 이 주제의 UB 는 **도구가 본다** —\
  형제 [`03번`](../03-four-cast-operators/)의 UB(앨리어싱·`const` 벗기기)가 **아무 도구에도 안 걸린 것과 반대**다.
- ★ **UB 가 만든 값 자체는 이 문서에 싣지 않았다** — 흔들리는 칸이다.\
  근거로 쓰는 것은 「**경고가 났다**」와 「**UBSan 이 두 줄을 냈다**」와 「**`run exit=139`**」다.

### (7) 범위 for 에서 `auto` 를 어떻게 쓰느냐

**언제 쓰나** — 루프를 쓸 때마다. **복사가 몇 번인지 눈으로 센다.**

```text
===== 소스: dedu08.cpp =====
// 범위 for 에서 auto 를 어떻게 쓰느냐 — 복사가 몇 번 일어나나
#include <cstdio>
#include <vector>

struct Loud {
    int v;
    Loud(int x) : v(x) {}
    Loud(const Loud& o) : v(o.v) { std::printf("  복사 %d\n", v); }
};

int main() {
    std::printf("[벡터를 만든다]\n");
    std::vector<Loud> vs{Loud(1), Loud(2)};
    std::printf("[for (auto x : vs)]\n");
    for (auto x : vs) { (void)x; }
    std::printf("[for (auto& x : vs)]\n");
    for (auto& x : vs) { (void)x; }
    std::printf("[for (const auto& x : vs)]\n");
    for (const auto& x : vs) { (void)x; }
    std::printf("[끝]\n");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu08.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[벡터를 만든다]
  복사 1
  복사 2
[for (auto x : vs)]
  복사 1
  복사 2
[for (auto& x : vs)]
[for (const auto& x : vs)]
[끝]
```

| 루프 | 복사 횟수 | 왜 |
|---|---|---|
| `for (auto x : vs)` | ★ **2** | 원소마다 **복사 생성자**가 불린다 |
| `for (auto& x : vs)` | **0** | 참조로 묶는다 |
| `for (const auto& x : vs)` | **0** | 〃 — 읽기만 할 때의 기본값 |

- ★ **루프 전의 복사 2번은 루프가 아니라 `initializer_list` 가 낸 것**이다 —\
  `std::vector<Loud> vs{Loud(1), Loud(2)};` 가 목록의 원소를 **복사해** 벡터에 넣는다.\
  `initializer_list` 원소가 `const` 라 **옮길 수 없기 때문**이고, 그 정본은 형제 [`04번`](../04-brace-initialization-narrowing-and-initializer-list/)이다.
- ★★ **읽기만 하면 `const auto&`** 가 기본값이다. 고칠 거면 `auto&`.
- ★ **`auto`(값)가 오히려 맞는 때**도 있다 — 원소가 `int` 처럼 작을 때, 그리고 **루프 안에서 사본을 망가뜨릴 때**.
- ★ 프록시 컨테이너에서는 `auto&` 가 **안 된다**(프록시가 prvalue 라서). `auto&&` 를 쓴다.

### (8) `auto` 가 못 쓰이는 자리

**언제 쓰나** — 「여기도 `auto` 되나?」 할 때.

```text
===== 소스: dedu09.cpp =====
// auto 가 못 쓰이는 자리 넷
struct S {
    auto m = 0;                  // ① 비정적 멤버
};

auto g;                          // ② 초기화 없는 변수

void take(auto x);               // ③ C++20 축약 템플릿 — 이건 된다
auto h();                        // ④ 정의 없이 선언만 한 반환 타입 추론 함수

int main() { return h(); }
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu09.cpp -o ex 2>&1 | grep -E 'error:|warning:' (cc exit=1) =====
dedu09.cpp:3:5: error: non-static data member declared with placeholder ‘auto’
dedu09.cpp:6:1: error: declaration of ‘auto g’ has no initializer
dedu09.cpp:11:22: error: use of ‘auto h()’ before deduction of ‘auto’
```

| 쓴 것 | 결과 |
|---|---|
| `struct S { auto m = 0; };` | **에러** — 비정적 데이터 멤버에는 못 쓴다 |
| `auto g;` | **에러** — 초기값이 없으면 추론할 것이 없다 |
| `void take(auto x);` | ★ **된다** — C++20 축약 템플릿 |
| `auto h();` 를 정의 없이 호출 | **에러** — 추론 전에는 못 쓴다 |

```text
===== 소스: dedu09.cpp =====
// auto 가 못 쓰이는 자리 넷
struct S {
    auto m = 0;                  // ① 비정적 멤버
};

auto g;                          // ② 초기화 없는 변수

void take(auto x);               // ③ C++20 축약 템플릿 — 이건 된다
auto h();                        // ④ 정의 없이 선언만 한 반환 타입 추론 함수

int main() { return h(); }
===== clang++ -std=c++20 -Wall -Wextra -pedantic dedu09.cpp -o ex 2>&1 | grep -E 'error:|warning:|generated' (cc exit=1) =====
dedu09.cpp:3:5: error: 'auto' not allowed in non-static struct member
dedu09.cpp:6:6: error: declaration of variable 'g' with deduced type 'auto' requires an initializer
dedu09.cpp:11:21: error: function 'h' with deduced return type cannot be used before it is defined
3 errors generated.
```

- ★★ **`auto h();` 가 에러인 이유가 반환 타입 추론의 값이다** — **정의를 봐야 타입을 안다.**\
  그래서 **헤더에 선언만 두고 `.cpp` 에 정의를 두는 배치가 깨진다.** 라이브러리 경계에서 `auto` 반환을 피하는 근거다.
- ★ 비정적 멤버에 못 쓰는 이유도 같은 집안이다 — **클래스 레이아웃이 정의 시점에 정해져야** 한다.

### (9) C++20 축약 템플릿 — 매개변수 `auto`

**언제 쓰나** — 짧은 제네릭 함수를 쓸 때.

```text
===== 소스: dedu10.cpp =====
// C++20 축약 템플릿 — auto 매개변수
#include <cstdio>

void show(auto x) { std::printf("sizeof = %zu\n", sizeof(x)); }

int main() {
    show(1);
    show(1.0);
    show('c');
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu10.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof = 4
sizeof = 8
sizeof = 1
```

`-std=c++17` 로 던지면 **에러가 아니라 경고**다 — GCC 확장으로 받아 준다.

```text
===== 소스: dedu10.cpp =====
// C++20 축약 템플릿 — auto 매개변수
#include <cstdio>

void show(auto x) { std::printf("sizeof = %zu\n", sizeof(x)); }

int main() {
    show(1);
    show(1.0);
    show('c');
}
===== g++ -std=c++17 -Wall -Wextra -pedantic dedu10.cpp -o ex 2>&1 | grep -E 'error:|warning:' (cc exit=0) =====
dedu10.cpp:4:11: warning: use of ‘auto’ in parameter declaration only available with ‘-std=c++20’ or ‘-fconcepts’
```

- ★★ **`cc exit=0` 이다.** 「`-std=c++17` 로 돌렸다」가 「C++17 로 검증했다」가 아니라는 사례가 또 나왔다 —\
  **표준 준수를 주장하려면 `-pedantic-errors`** 가 필요하다(형제 [`04번`](../04-brace-initialization-narrowing-and-initializer-list/)의 (5)와 같은 결론).
- ★ `void show(auto x)` 는 `template <class T> void show(T x)` 의 **다른 표기일 뿐**이다.\
  그래서 추론 규칙도 (1)과 **같다.**

### (10) 다섯 층 — 무엇이 표준이고 무엇이 도구인가

★★ **이 주제는 「표준」 칸이 거의 전부다.** 타입 추론은 **표준이 규칙으로 정한 것**이고,
구현이 고를 여지가 없다 — 두 컴파일러가 **한 자리도 다르지 않았다.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | **`auto` 가 맨 위 `cv`·참조를 떼는 것** · **배열/함수 감쇠** · **`auto&&` 가 전달 참조인 것** · **`decltype(이름)` 과 `decltype((식))` 이 다른 것** · **`decltype` 이 식을 평가하지 않는 것** · **`decltype(auto)` 가 참조를 남기는 것** · `auto` 를 **비정적 멤버·초기값 없는 변수**에 못 쓰는 것 · **정의 전에 `auto` 반환 함수를 못 쓰는 것** | ★ `TypeOf<T>` 로 **두 컴파일러에서 같은 타입**을 받았다 | ★★ **타입은 실행 출력에 안 나온다** — `typeid().name()` 도 `const`·참조를 **지워서** 답한다 |
| **조건부 표준** | 표준판이 있을 때만 | **`decltype(auto)`·일반 함수 반환 타입 추론은 C++14부터** · **`auto x{1}` 이 `int` 인 것은 C++17부터** · **매개변수 `auto` 는 C++20부터** | `-std=c++17` 로 던져 확인((9)) | ★ g++ 는 C++17 에서 매개변수 `auto` 를 **경고로 받아 준다**(`cc exit=0`) |
| **구현 정의** | 문서화 의무가 있다 | 진단 문구(`incomplete type` 대 `implicit instantiation of undefined template`) · **`std::vector<bool>::reference` 의 크기 16** · 그 프록시의 구체 구현 | 두 컴파일러 대조 · `sizeof` | — |
| **미명시** | 몇 가지 중 하나 | **`vector<bool>` 이 프록시를 돌려준다는 것은 표준이다** — 그 **프록시의 레이아웃·크기**만 구현이다 | `sizeof(b0) = 16` | — |
| **UB** | 아무 일이나 | ★ **`decltype(auto)` 로 지역을 돌려준 뒤 읽기**((6)) | `-Wreturn-local-addr` 경고 + UBSan 2줄 + `run exit=139` | ★ **경고는 나지만 `cc exit=0`** — 빌드는 그냥 된다 |

**「도구가 못 보는 것」을 층마다 — 전용 표**

| 사실 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | UBSan | 비고 |
|---|---|---|---|---|
| 추론된 타입 자체 | ★ **아무 말도 안 한다** | 〃 | — | ★ `TypeOf<T>` 를 억지로 넣어야 나온다 |
| `auto` 가 프록시를 잡은 것((5)) | ★★ **0건** | ★★ **0건** | — | ★ **컴파일되고 실행되고 값만 틀리다** |
| 범위 for 의 불필요한 복사((7)) | **0건** | **0건** | — | 복사 생성자에 출력을 넣어야 보인다 |
| `decltype(auto)` 댕글링((6)) | **경고 1**(`-Wreturn-local-addr`) · `cc exit=0` | **경고 1**(`-Wreturn-stack-address`) | ★ **2줄** · `run exit=139` | ★ 이 주제의 UB 는 **도구가 본다** |
| `auto` 가 못 쓰이는 자리((8)) | **에러 3** | **에러 3** | — | 판정이 같다 |
| 매개변수 `auto` 를 C++17 에서 | ★ **경고 1 · `cc exit=0`** | — | — | ★ `-pedantic` 으로도 안 막힌다 |

- ★★★ **이 주제에서 가장 조용한 사고는 (5)의 프록시다.** 컴파일 통과 · 경고 0건 · 실행 정상 ·\
  **값만 틀리다.** 도구가 아니라 **`sizeof` 를 찍어 보는 습관**으로만 걸린다.

## 문법 — 형태와 규칙

### 형태

```cpp
/* dedu01.cpp */
// auto 가 무엇을 떨어뜨리나 — 아홉 줄
template <class T> struct TypeOf;   // 선언만 — 정의가 없다

int main() {
    int        i  = 0;
    const int  ci = 0;
    const int& cr = i;
    const int* cp = &i;
    int* const pc = &i;

    auto a1 = ci;         // ① 맨 위 const
    auto a2 = cr;         // ② 참조 + const
    auto a3 = cp;         // ③ 가리키는 곳의 const
    auto a4 = pc;         // ④ 포인터 자신의 const
    auto& b1 = ci;        // ⑤ auto&
    const auto& b2 = i;   // ⑥ const auto&
    auto&& c1 = i;        // ⑦ 전달 참조에 lvalue
    auto&& c2 = 1;        // ⑧ 전달 참조에 rvalue
    auto  d1 = cr + 0;    // ⑨ 식의 결과

    TypeOf<decltype(a1)> t1; TypeOf<decltype(a2)> t2; TypeOf<decltype(a3)> t3;
    TypeOf<decltype(a4)> t4; TypeOf<decltype(b1)> t5; TypeOf<decltype(b2)> t6;
    TypeOf<decltype(c1)> t7; TypeOf<decltype(c2)> t8; TypeOf<decltype(d1)> t9;
}
```

규칙 불릿.

- **`auto x = e;`** — `e` 를 **함수 매개변수처럼** 받는다. **맨 위 `cv` 한정자와 참조를 뗀다.**\
  **배열은 포인터로, 함수는 함수 포인터로 감쇠한다.**
- **`auto& x = e;`** — 참조를 붙인다. **`const` 는 따라온다.** 배열·함수는 **감쇠하지 않는다.**
- **`auto&& x = e;`** — 전달 참조. lvalue 면 `T&`, rvalue 면 `T&&`.
- **`decltype(이름)`** — 그 실체의 **선언 타입** 그대로(`const`·배열 크기·함수 타입 포함).
- **`decltype(식)`** — 식의 타입 + 값 범주. **lvalue 면 `T&`**, xvalue 면 `T&&`, prvalue 면 `T`.\
  **`decltype((이름))` 은 식이다** — 괄호 하나가 답을 바꾼다.
- **`decltype(auto)`**(C++14) — `auto` 자리에 **`decltype` 규칙**을 쓴다. 참조를 남긴다.
- **`auto` 반환 함수는 정의를 봐야 쓸 수 있다.** 헤더에 선언만 둘 수 없다.
- **매개변수 `auto`**(C++20)는 **템플릿의 다른 표기**다.
- ★ **`auto x{1}` 은 `int`(C++17부터), `auto x = {1}` 은 `initializer_list<int>`** —\
  정본은 형제 [`04번`](../04-brace-initialization-narrowing-and-initializer-list/).

### 금지 사례 — 던져서 받은 다섯

| 쓴 것 | 컴파일러 | 무엇이 나오나 |
|---|---|---|
| `struct S { auto m = 0; };` | g++ | ``error: non-static data member declared with placeholder `auto` `` |
| `auto g;`(초기값 없음) | g++ | ``error: declaration of `auto g` has no initializer`` |
| `auto h();` 를 정의 전에 호출 | g++ | ``error: use of `auto h()` before deduction of `auto` `` |
| `f1(0) = 99`(`auto` 반환) | g++ | `error: lvalue required as left operand of assignment` |
| `return (local);`(`decltype(auto)`) | g++ | ★ **에러가 아니라 경고** — ``warning: reference to local variable `local` returned  [-Wreturn-local-addr]`` |
| 매개변수 `auto` 를 `-std=c++17` 로 | g++ | ★ **경고** — ``warning: use of `auto` in parameter declaration only available with `-std=c++20` or `-fconcepts` `` |

### 고를 것을 손으로 돌리는 순서

1. **읽기만 하나?** → `const auto&`.
2. **고칠 것인가?** → `auto&`.
3. **진짜 사본이 필요한가?** → `auto`.\
   ★ 단 **프록시 컨테이너인지 확인한다**((5)) — `vector<bool>` 이면 **타입을 못 박는다.**
4. **받은 것을 그대로 돌려주는 래퍼인가?** → **`decltype(auto)`**((3)).\
   ★ 그때 **`return (x);` 를 쓰지 않는다**((6)).
5. **제네릭 코드에서 무엇이 올지 모르나?** → `auto&&` + `std::forward`(목록의 **09번 주제**).
6. **라이브러리 경계(헤더에 선언만)인가?** → **`auto` 반환을 피한다**((8)).

## 어디서 틀리나

### 1. ★★★ 「`auto` 는 그냥 타입을 적어 주는 것이다」

아니다. **함수 매개변수 추론과 같은 규칙**이라 **맨 위 `const` 와 참조를 뗀다**((1)).\
`const int& cr` 를 `auto a = cr;` 로 받으면 **`int` 사본**이다.

### 2. ★★★ 「`decltype(x)` 와 `decltype((x))` 는 같다」

**다르다**((2)). 괄호를 치면 **이름이 식이 되고**, lvalue 식은 **`T&`** 다.\
★ 그래서 `decltype(auto) f() { return (local); }` 가 **지역 참조 반환**이 된다((6)).

### 3. ★★★ 「`auto x = v[i];` 는 언제나 복사다」

**프록시 컨테이너에서는 아니다**((5)). `vector<bool>` 에서 `auto b0 = vb[0];` 는\
**대리인을 복사**해서 원본을 계속 본다. `sizeof(b0)` 가 **16** 이다.

### 4. ★★ 「`auto&` 면 `const` 도 떨어진다」

아니다((1)의 ⑤). `auto&` 는 **참조만 붙이고 `const` 는 그대로 둔다** — `const int&` 가 된다.

### 5. ★★ 「`auto a = cp;` 에서 `const` 가 떨어진다」

**안 떨어진다**((1)의 ③). `const int*` 의 `const` 는 **가리키는 대상**에 붙어 타입의 일부다.\
떨어지는 것은 **맨 위**(`int* const` 의 `const`)뿐이다.

### 6. ★★ 「`decltype(arr)` 는 `int*` 다」

**`int [3]`** 이다((2)). `decltype` 은 **감쇠시키지 않는다.**\
감쇠하는 쪽은 `auto a = arr;`(→ `int*`)다((4)).

### 7. ★★ 「`decltype(f(1.0))` 은 `f` 를 부른다」

**안 부른다**((2)). `decltype` 은 **식을 평가하지 않는다** — 정의가 없어도 된다.

### 8. ★ 「`auto` 반환은 헤더에 선언만 둬도 된다」

**안 된다**((8)). `auto h();` 를 정의 전에 부르면 ``error: use of `auto h()` before deduction of `auto` `` 다.

### 9. ★ 「범위 for 의 `auto` 는 공짜다」

원소마다 **복사 생성자**가 불린다((7)). 읽기만 하면 **`const auto&`**.

### 10. 「`-std=c++17` 로 돌렸으니 C++17 코드다」

아니다((9)). 매개변수 `auto` 가 **경고 한 줄로 통과**해 `cc exit=0` 이 된다.\
★ 형제 [`04번`](../04-brace-initialization-narrowing-and-initializer-list/)의 좁히기와 **같은 집안**이다 — `-pedantic-errors` 가 필요하다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| `auto` 가 **맨 위 `cv`·참조를 떼는** 것 | **언어** |
| `auto` 에서 **배열·함수가 감쇠**하고 `auto&` 에서는 안 하는 것 | **언어** |
| `auto&&` 가 **전달 참조**인 것 | **언어** |
| `decltype(이름)` 과 `decltype((식))` 이 **다른** 것 | **언어** |
| `decltype` 이 **식을 평가하지 않는** 것 | **언어** |
| `decltype(auto)` 가 **참조를 남기는** 것 | **언어**(C++14부터) |
| `auto` 를 **비정적 멤버·초기값 없는 변수**에 못 쓰는 것 | **언어** |
| **정의 전에 `auto` 반환 함수를 못 쓰는** 것 | **언어** |
| `std::vector<bool>` 이 **프록시를 돌려준다**는 것 | **언어**(표준이 그 특수화를 규정한다) |
| ★ **그 프록시의 크기가 16 바이트**인 것 | ★ **구현**(libstdc++ 13) |
| 진단 문구 · 경고 이름(`-Wreturn-local-addr` 대 `-Wreturn-stack-address`) | **컴파일러 구현** |
| ★ 매개변수 `auto` 를 C++17 에서 **경고로 받아 주는** 것 | ★ **GCC 확장** |
| ★ 댕글링 참조가 **읽은 값** | ★ **UB 의 결과** — 이 문서는 **싣지 않았다** |

## 언제 쓰고 언제 안 쓰나

**`auto` 를 쓰는 이유 둘**\
① **타입이 이름으로 못 적히는 자리**(람다·이터레이터·템플릿 결과)에서 **유일한 방법**이다.\
② **`const`·부호·너비가 어긋나 생기는 조용한 변환을 막는다** — 직접 적으면 `size_t` 를 `int` 로 받는 실수가 난다.

**`auto` 가 숨기는 것 둘**\
① **프록시**((5)) — 값인 줄 알았는데 대리인이다.\
② **복사 비용** — `auto x = 큰객체` 가 한 줄에 숨는다((7)).

**안 쓰는 자리**\
★ **라이브러리 경계의 반환 타입**((8)) — 헤더에 선언만 둘 수 없고, 반환 타입이 **계약**인데 코드에 안 적힌다.\
★ **프록시가 걸린 첨자 접근** — 타입을 못 박는다.\
★ **독자가 타입을 알아야 읽히는 자리** — 「타입이 문서」인 코드.

**`decltype(auto)`** — **받은 것을 그대로 돌려주는 래퍼**에만. 그 외에는 `auto` 가 더 안전하다((6)).

## 핵심 문장

1. **`auto` 는 「함수 매개변수처럼 받아라」다** — 맨 위 `const` 와 참조를 뗀다.
2. **`decltype` 은 추론이 아니라 조회다** — 참조도 `const` 도 그대로 남긴다.
3. **괄호 하나가 이름을 식으로 바꾼다** — `decltype((i))` 는 `int&` 다.
4. **`decltype(auto)` 는 참조를 남기고, 그래서 댕글링도 남긴다** — `return (x);` 를 쓰지 마라.
5. **`auto` 가 늘 복사인 것은 아니다** — 프록시는 대리인째 복사된다. `sizeof` 를 찍어 보라.
6. **`auto` 반환은 정의를 봐야 쓸 수 있다** — 라이브러리 경계에서 값을 치른다.

## 관련 자료

- [**04번 형제**](../04-brace-initialization-narrowing-and-initializer-list/) —\
  `auto x{1}` 대 `auto x = {1}` 의 정본. `TypeOf<T>` 창도 거기서 처음 나왔다.
- [**07번 형제**](../07-references-vs-pointers/) — `auto&`·`auto&&` 의 `&` 가 **무엇인지**가 거기다.
- 목록의 **08번 주제**(값 범주) — `decltype(식)` 이 `T`/`T&`/`T&&` 중 무엇이 되는지를 **가르는 규칙**.
- 목록의 **09번 주제**(rvalue 참조·`forward`) — `auto&&` 가 왜 「전달 참조」인지.
- 목록의 **31번 주제**(함수 템플릿과 인자 추론) — ★ **`auto` 규칙의 본체.**\
  여기는 「그래서 `auto` 를 어떻게 읽나」까지고, **템플릿 쪽 규칙 전부**는 거기다.
- 목록의 **30번 주제**(댕글링 참조와 수명) — (6)의 사고를 **수명 쪽에서** 본다.
- 목록의 **41번 주제**(순차 컨테이너) — `std::vector<bool>` 이 **왜 특수화인지**는 거기.
- 목록의 **39번 주제**(람다) — **타입을 이름으로 못 적는** 가장 흔한 자리.
- C 갈래 [`16-array-pointer-decay-and-function-parameters/`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/) —\
  (4)의 감쇠 규칙의 정본.
- C 갈래 [`01-declaration-syntax-and-reading/`](../../../c/syntax/01-declaration-syntax-and-reading/) —\
  「`const` 가 맨 위인가 아닌가」를 읽는 규칙((1)의 ③④).

## 용어 풀이

> **`auto`** — 초기값에서 타입을 추론하는 자리표시자. **템플릿 매개변수 추론과 같은 규칙**을 쓴다.

> **맨 위 `cv` 한정자(top-level cv-qualifier)** — 그 객체 **자신**에 붙은 `const`/`volatile`.\
> `int* const` 의 `const` 는 맨 위이고, `const int*` 의 `const` 는 아니다.

> **감쇠(decay)** — 배열이 포인터로, 함수가 함수 포인터로 바뀌는 것.

> **`decltype(e)`** — 식 `e` 의 타입을 **조회**한다. **평가하지 않는다.**

> **`decltype(auto)`**(C++14) — `auto` 자리에 `decltype` 규칙을 쓴다.

> **전달 참조(forwarding reference)** — 추론되는 자리의 `auto&&`/`T&&`.

> **프록시 타입(proxy type)** — 실제 값 대신 그 자리를 대리하는 임시 객체.\
> `std::vector<bool>::reference` 가 대표다.

> **축약 함수 템플릿(abbreviated function template)**(C++20) — 매개변수에 `auto` 를 쓰는 표기.\
> `void f(auto x)` 는 `template <class T> void f(T x)` 와 같다.

## 더 들어가면

- **`auto` 와 템플릿 추론이 갈리는 한 곳** — **중괄호 목록**이다.\
  `auto x = {1, 2};` 는 `initializer_list<int>` 가 되지만, `template <class T> void f(T x);` 에\
  `f({1, 2})` 를 넘기면 **추론이 실패한다.** ★ **이 문서는 템플릿 쪽을 안 던졌다** — 정본은 목록의 **31번 주제**다.
- **`decltype(auto)` 를 변수에 쓰기** — `decltype(auto) x = e;` 도 된다. 이 문서는 **반환 타입 쪽만** 던졌다.
- **후행 반환 타입**(`auto f() -> decltype(...)`) — C++11 에서 `decltype` 이 매개변수를 볼 수 있게 하려고 나온 문법.\
  C++14 의 반환 타입 추론이 대부분을 대신한다. ★ 이 문서는 안 던졌다.
- **컨셉으로 제약한 `auto`**(`std::integral auto x = ...`) — C++20. 정본은 목록의 **36번 주제**.
- **`auto` 와 구조적 바인딩**(`auto [a, b] = pair;`) — 추론 규칙이 한 겹 더 있다. 정본은 목록의 **48번 주제**.
- **프록시가 `auto` 를 무는 다른 사례** — 표현식 템플릿(Eigen 류)이 같은 모양이다.\
  ★ 이 문서는 **표준 라이브러리 안의 사례 하나만**(`vector<bool>`) 던졌다.
