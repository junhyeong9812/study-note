# cpp/syntax/04 — `{}` 균일 초기화·좁히기·`initializer_list` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 목록 초기화](https://en.cppreference.com/w/cpp/language/list_initialization) · [집합체 초기화](https://en.cppreference.com/w/cpp/language/aggregate_initialization) · [`std::initializer_list`](https://en.cppreference.com/w/cpp/utility/initializer_list) · [값 초기화](https://en.cppreference.com/w/cpp/language/value_initialization) · [`auto` 자리표시자](https://en.cppreference.com/w/cpp/language/auto) · [GCC 13 Warning Options — `-Wnarrowing`](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html) · [Clang Diagnostic Reference — `-Wc++11-narrowing`](https://clang.llvm.org/docs/DiagnosticsReference.html)
> **실행 검증** — 이 문서의 모든 출력·경고·에러는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **gcc 13.3.0**(C 대비용) · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`brace01.cpp` \~ `brace14.cpp` · `desig01.c`) — 그래야 기계가 소스와 진단을 짝지을 수 있다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 컴파일 진단과 실행 출력이 한 블록에 같이 있으면 **진단이 먼저, 실행 출력이 나중**이다(서로 다른 프로세스라 순서가 고정된다).
> **버전** — `{}` 목록 초기화 · 좁히기 금지 · `std::initializer_list` 는 **C++11부터**.\
> **`auto x{1}` 이 `int` 가 되는 것은 C++17부터**(그 전에는 `initializer_list<int>` 였다).\
> **지정 초기자는 C++20부터**이고, **괄호로 하는 집합체 초기화도 C++20부터**다((11)).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> **경계** — 「구조체 집합체 초기화와 C99 지정 초기자」의 정본은 C 갈래다.\
> 아직 폴더가 없어 링크를 걸지 못한다 — C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **21번**\
> (구조체 선언·초기화·지정 초기자)이 그 자리다. 여기서는 **C++ 가 C 와 갈리는 지점만** 쓴다((10)).\
> 「정수 승격과 통상 산술 변환」은 C 갈래 [`03번`](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/)이 정본이고,\
> 좁히기 판정이 「**정수 승격 뒤의 값이 들어가는가**」를 묻는 자리에서 그 규칙을 쓴다((3)).\
> 「`sizeof`·정렬」은 C 갈래 [`08번`](../../../c/syntax/08-sizeof-alignment-and-offsetof/)이다.\
> 「오버로드 해석의 일반 규칙」은 형제 [`01번`](../01-function-overloading-and-overload-resolution/)이 정본이다 —\
> 여기는 그 규칙 **위에 `initializer_list` 가 얹히는 한 겹**만 쓴다((6)).
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 컴파일 시간 · 실행 파일 크기 | **진단 본문** · `파일:줄:칸` · 캐럿 줄 |
> | 초기화하지 않은 변수의 값(이 문서는 **싣지 않았다**) | **`cc exit` 와 `run exit`**(갈라 적었다) |
> | — | **경고 이름**(`-Wnarrowing` · `-Wvexing-parse` · `-Wc++11-narrowing`) |
> | — | **에러/경고 건수**(`grep -c 'warning:'` 로 세었다) |
> | — | 프로그램 출력 전부 — 이 주제에는 미정의 동작이 **없다** |

## 한눈에 — 쉽게 말하면

**C++11 이 중괄호를 「어디에나 쓸 수 있는 초기화 문법」으로 만들었다.
그런데 그 중괄호는 괄호와 같은 일을 하지 않는다.**

비유 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **「인원 3명, 좌석 0번」이라고 적은 신청서** | `std::vector<int> v(3, 0)` — **인자 두 개**로 읽는다 |
| **「3번 손님, 0번 손님」이라고 적은 명단** | `std::vector<int> v{3, 0}` — **원소 목록**으로 읽는다 |
| 명단 양식이 있으면 **무조건 명단으로 읽는다** | `initializer_list` 생성자가 있으면 **먼저 뽑힌다**((6)) |
| 명단이 **비어 있으면** 신청서로 되돌아간다 | 빈 `{}` 는 **기본 생성자**다((6)) |
| ★ **값을 깎아 적으면 접수 거부** | **좁히기 변환은 표준이 금지한다**((3)) |
| ★ 그런데 **접수원이 봐주는 창구가 있다** | ★★ **g++ 는 일부를 경고로 통과시킨다**((4)) |

- ★★★ **`()` 와 `{}` 가 갈리는 조건은 하나다** — 「`initializer_list` 생성자가 후보인가」.\
  후보가 아니면 **둘은 같은 일을 한다**((2)). `std::vector<std::string> v(3, "ha")` 와 `v{3, "ha"}` 가 그렇다.
- ★★ **`{}` 만이 좁히기를 막는다.** 같은 값을 괄호로 넣으면 **조용히 잘린다** — C++20 이 집합체에도\
  괄호 초기화를 허용하면서 그 자리가 **하나 더 늘었다**((11)).
- ★ **`{}` 는 「가장 성가신 파싱」도 지운다**((8)) — `T t();` 는 변수가 아니라 **함수 선언**이지만 `T t{};` 는 변수다.

```text
   int x( 3.9 );      "괄호"  — 함수 호출처럼 읽는다. 좁히기 검사 없음 → 3 으로 잘린다
   int x{ 3.9 };      "중괄호" — 목록 초기화. 좁히기 검사 있음 → 컴파일 에러

   W w( 1, 2 );       생성자 오버로드 해석                → W(int,int)
   W w{ 1, 2 };       ① initializer_list 가 있으면 그것부터  → W(init_list)
                      ② 없으면 그때 나머지 생성자로 간다
                      ③ 비어 있으면({})  기본 생성자로 간다

   ┌── 중괄호가 하는 일 넷 ────────────────────────────────┐
   │ ① 원소 목록을 만든다      std::initializer_list<T>   │
   │ ② 집합체를 멤버 순서대로 채운다   P p{1, 2, 3}       │
   │ ③ 빈 것은 값 초기화        int i{} → 0                │
   │ ④ 좁히기를 거부한다        char c{300} → 에러         │
   └──────────────────────────────────────────────────────┘
```

> **목록 초기화(list-initialization)** — 중괄호로 하는 초기화 전부.\
> `T t{...}`(직접) 와 `T t = {...}`(복사) 두 꼴이 있다.

> **좁히기 변환(narrowing conversion)** — 값을 잃을 수 있는 변환.\
> **표준이 네 가지로 목록을 정해 두었고**, 목록 초기화 안에서는 **ill-formed**(문법 위반)다.

> **`std::initializer_list<T>`** — 중괄호 안의 원소들을 담아 생성자에 넘기는 **읽기 전용 배열 뷰**.\
> `<initializer_list>` 헤더에 있고, **컴파일러가 특별 대우한다**(오버로드에서 먼저 본다).

> **집합체(aggregate)** — 사용자 선언 생성자·private 멤버·가상 함수가 없는 클래스/배열.\
> 중괄호로 **멤버를 순서대로** 채울 수 있다.

> **값 초기화(value-initialization)** — `T t{}` 가 하는 일. 기본 타입은 **0**, 포인터는 **`nullptr`**.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **`()` 와 `{}` 는 언제 갈리고 언제 안 갈리나** — 조건을 **한 문장**으로 댈 수 있나((1)·(2)).
2. **좁히기는 무엇인가** — 어느 변환이 좁히기인지 **네 갈래로** 말하고,\
   **상수식이면 통과하는 것**과 **상수식이어도 안 되는 것**을 가를 수 있나((3)).
3. **「컴파일됐다」가 「표준에 맞다」인가** — 아니다((4)). 그것을 **종료 코드로** 보일 수 있나.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| **실행 출력** | `()` 와 `{}` 가 **실제로 다른 객체**를 만든다는 것 | (1)·(2)·(11)·(12) |
| **컴파일 진단** | 좁히기 판정 · 가장 성가신 파싱 · 지정 초기자 규칙 | (3)·(8)·(10) |
| ★ **종료 코드 + 플래그별 경고 수** | ★★ **같은 소스가 g++ 에서 통과하고 clang 에서 막힌다** | (4)·(5) |
| ★ **의도적 타입 에러**(`TypeOf<T>`) | `auto` 가 **무슨 타입을 골랐는지** 컴파일러 입으로 | (9) |

★ **네 번째 창을 왜 이것으로 골랐나.** `auto x{1}` 과 `auto x = {1}` 의 차이는
**출력으로는 절대 안 보인다** — 둘 다 아무것도 찍지 않는다.
**정의 없는 템플릿에 그 타입을 넣어 에러를 받으면** 컴파일러가 자기 입으로 타입을 말한다.

```text
template <class T> struct TypeOf;   // 선언만 — 정의가 없다
TypeOf<decltype(x)> probe;          // error: ... TypeOf<int> ... incomplete type
```

이 창은 형제 [**05번**](../05-auto-and-decltype-type-deduction/)에서 **주력 도구**가 된다.

★ **세 번째 창이 이 주제의 값이다.** 「돌아갔다」는 아무것도 증명하지 못한다 —
**표준이 ill-formed 라고 한 코드가 g++ 에서 `cc exit=0` 으로 빌드된다**((4)).

### (1) `()` 와 `{}` 가 갈리는 자리

**언제 쓰나** — 컨테이너를 만들 때마다. 이 주제에서 가장 자주 무는 자리다.

```text
===== 소스: brace01.cpp =====
// () 와 {} 가 갈리는 자리 — vector 네 가지
#include <cstdio>
#include <vector>

int main() {
    std::vector<int> a(3, 0);
    std::vector<int> b{3, 0};
    std::vector<int> c(3);
    std::vector<int> d{3};
    std::printf("a(3,0) size=%zu  a[0]=%d\n", a.size(), a[0]);
    std::printf("b{3,0} size=%zu  b[0]=%d b[1]=%d\n", b.size(), b[0], b[1]);
    std::printf("c(3)   size=%zu  c[0]=%d\n", c.size(), c[0]);
    std::printf("d{3}   size=%zu  d[0]=%d\n", d.size(), d[0]);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a(3,0) size=3  a[0]=0
b{3,0} size=2  b[0]=3 b[1]=0
c(3)   size=3  c[0]=0
d{3}   size=1  d[0]=3
```

| 쓴 것 | 뽑힌 생성자 | 결과 |
|---|---|---|
| `v(3, 0)` | `vector(size_type, const T&)` | **0 이 세 개** |
| `v{3, 0}` | `vector(initializer_list<int>)` | ★ **원소가 `3` 과 `0`, 크기 2** |
| `v(3)` | `vector(size_type)` | 0 이 세 개 |
| `v{3}` | `vector(initializer_list<int>)` | ★ **원소가 `3` 하나** |

- ★★★ **중괄호는 「크기」가 아니라 「내용」으로 읽힌다.** `std::vector<int> v{3}` 이 **크기 3 이 아니라 값 3** 인 것이\
  이 주제 전체에서 가장 자주 나는 사고다.
- ★ 규칙은 하나다 — **`initializer_list` 생성자가 후보이면 다른 생성자보다 먼저 본다.** 정본은 (6)이다.

### (2) 갈리지 않는 자리 — 조건을 정확히 짚는다

**언제 쓰나** — 「중괄호는 위험하다」를 **규칙이 아니라 조건**으로 바꿀 때.

```text
===== 소스: brace02.cpp =====
// 같은 두 인자를 string 으로 바꾸면 — initializer_list 가 후보가 아니게 된다
#include <cstdio>
#include <string>
#include <vector>

int main() {
    std::vector<std::string> a(3, "ha");
    std::vector<std::string> b{3, "ha"};
    std::printf("a(3,\"ha\") size=%zu a[0]=%s\n", a.size(), a[0].c_str());
    std::printf("b{3,\"ha\"} size=%zu b[0]=%s\n", b.size(), b[0].c_str());
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a(3,"ha") size=3 a[0]=ha
b{3,"ha"} size=3 b[0]=ha
```

- ★★ **완전히 같다.** 원소 타입이 `std::string` 이면 `3` 을 `std::string` 으로 만들 수 없어\
  **`initializer_list<std::string>` 이 애초에 후보가 아니다.** 그래서 `(size, value)` 생성자로 간다.
- ★ 그러므로 외울 것은 「중괄호는 다르다」가 아니라\
  「**`initializer_list` 가 후보일 때만 다르다**」다.
- ★ 뒤집으면 — **`initializer_list<T>` 생성자가 없는 타입에서는 `{}` 와 `()` 의 차이를 걱정할 필요가 없다.**\
  그때 남는 `{}` 의 값은 **좁히기 차단**과 **가장 성가신 파싱 회피**다((3)·(8)).

### (3) 좁히기 — 표준이 목록으로 정한 네 가지

**언제 쓰나** — 「이건 좁히기인가?」를 손으로 판정할 때. **외울 것은 네 갈래다.**

```text
  표준이 좁히기로 정한 것 (목록 초기화 안에서 ill-formed)

  ① 부동소수점 → 정수                   예외 없음
  ② 더 넓은 부동 → 더 좁은 부동          상수식이고 표현 범위 안이면 예외
  ③ 정수/무범위 열거형 → 부동소수점       상수식이고 왕복이 정확하면 예외
  ④ 정수 → 「원래 값 전부를 담지 못하는」 정수
                                        상수식이고 승격 뒤 값이 들어가면 예외

  ★ ①만 「상수식 예외가 없다」 — 그래서 int x{3.0} 도 에러다.
```

```text
===== 소스: brace03.cpp =====
// 좁히기 아홉 줄 — 무엇이 에러이고 무엇이 통과하나
int main() {
    int      a{3.9};      // (1) double -> int, 비상수가 아니라 리터럴
    int      b{3.0};      // (2) double -> int, 상수식이고 값도 정확하다
    char     c{65};       // (3) int -> char, 상수식이고 들어간다
    char     d{300};      // (4) int -> char, 상수식인데 안 들어간다
    int n = 65;
    char     e{n};        // (5) int -> char, 비상수
    double   f{1};        // (6) int -> double, 상수식
    int m = 1;
    double   g{m};        // (7) int -> double, 비상수
    unsigned u{-1};       // (8) 음수 상수 -> unsigned
    long long big = 1;
    double   h{big};      // (9) long long -> double, 비상수
    (void)a; (void)b; (void)c; (void)d; (void)e;
    (void)f; (void)g; (void)u; (void)h;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace03.cpp -o ex (cc exit=1) =====
brace03.cpp: In function ‘int main()’:
brace03.cpp:3:16: error: narrowing conversion of ‘3.8999999999999999e+0’ from ‘double’ to ‘int’ [-Wnarrowing]
    3 |     int      a{3.9};      // (1) double -> int, 비상수가 아니라 리터럴
      |                ^~~
brace03.cpp:4:16: error: narrowing conversion of ‘3.0e+0’ from ‘double’ to ‘int’ [-Wnarrowing]
    4 |     int      b{3.0};      // (2) double -> int, 상수식이고 값도 정확하다
      |                ^~~
brace03.cpp:6:16: error: narrowing conversion of ‘300’ from ‘int’ to ‘char’ [-Wnarrowing]
    6 |     char     d{300};      // (4) int -> char, 상수식인데 안 들어간다
      |                ^~~
brace03.cpp:8:16: warning: narrowing conversion of ‘n’ from ‘int’ to ‘char’ [-Wnarrowing]
    8 |     char     e{n};        // (5) int -> char, 비상수
      |                ^
brace03.cpp:11:16: warning: narrowing conversion of ‘m’ from ‘int’ to ‘double’ [-Wnarrowing]
   11 |     double   g{m};        // (7) int -> double, 비상수
      |                ^
brace03.cpp:12:16: error: narrowing conversion of ‘-1’ from ‘int’ to ‘unsigned int’ [-Wnarrowing]
   12 |     unsigned u{-1};       // (8) 음수 상수 -> unsigned
      |                ^~
brace03.cpp:14:16: warning: narrowing conversion of ‘big’ from ‘long long int’ to ‘double’ [-Wnarrowing]
   14 |     double   h{big};      // (9) long long -> double, 비상수
      |                ^~~
```

| 줄 | 변환 | 상수식인가 | g++ 의 답 | 왜 |
|---|---|---|---|---|
| (1) `int a{3.9}` | `double`→`int` | 상수 | **에러** | ①에는 예외가 없다 |
| (2) `int b{3.0}` | `double`→`int` | 상수·값 정확 | ★ **에러** | ★ ①에는 예외가 없다 — **값이 정확해도** 막힌다 |
| (3) `char c{65}` | `int`→`char` | 상수·들어감 | **통과**(진단 0) | ④의 예외 |
| (4) `char d{300}` | `int`→`char` | 상수·안 들어감 | **에러** | ④, 예외에 못 든다 |
| (5) `char e{n}` | `int`→`char` | **비상수** | ★ **경고** | ④, 예외에 못 든다 — (4)에서 다시 본다 |
| (6) `double f{1}` | `int`→`double` | 상수·왕복 정확 | **통과**(진단 0) | ③의 예외 |
| (7) `double g{m}` | `int`→`double` | **비상수** | ★ **경고** | ③, 예외에 못 든다 |
| (8) `unsigned u{-1}` | `int`→`unsigned` | 상수·음수 | **에러** | ④ — 부호가 갈린다 |
| (9) `double h{big}` | `long long`→`double` | **비상수** | ★ **경고** | ③ |

- ★★★ **(2)가 이 절의 핵심이다.** 「상수식이면 통과한다」를 규칙으로 외우면 여기서 틀린다 —\
  **부동→정수에는 상수식 예외가 없다.** `int b{3.0}` 은 값이 정확히 3 인데도 막힌다.
- ★★ **(3)과 (5)를 가르는 것은 「상수식인가」뿐**이다. 같은 `int`→`char` 인데 하나는 진단 0건, 하나는 걸린다.
- ★ **(6)과 (7)도 같은 짝**이다. `int`→`double` 은 이 머신에서 **값을 잃지 않는데도**(`double` 의 가수가 53비트)\
  표준은 「**상수식이 아니면 좁히기**」로 본다 — 규칙이 **값이 아니라 타입으로** 쓰여 있기 때문이다.
- ★ (8)의 「승격 뒤 값이 들어가는가」가 정수 승격 규칙을 쓰는 자리다. 정본은\
  C 갈래 [`03번`](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/)이다.

clang 은 같은 아홉 줄을 이렇게 본다.

```text
===== 소스: brace03.cpp =====
// 좁히기 아홉 줄 — 무엇이 에러이고 무엇이 통과하나
int main() {
    int      a{3.9};      // (1) double -> int, 비상수가 아니라 리터럴
    int      b{3.0};      // (2) double -> int, 상수식이고 값도 정확하다
    char     c{65};       // (3) int -> char, 상수식이고 들어간다
    char     d{300};      // (4) int -> char, 상수식인데 안 들어간다
    int n = 65;
    char     e{n};        // (5) int -> char, 비상수
    double   f{1};        // (6) int -> double, 상수식
    int m = 1;
    double   g{m};        // (7) int -> double, 비상수
    unsigned u{-1};       // (8) 음수 상수 -> unsigned
    long long big = 1;
    double   h{big};      // (9) long long -> double, 비상수
    (void)a; (void)b; (void)c; (void)d; (void)e;
    (void)f; (void)g; (void)u; (void)h;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic brace03.cpp -o ex 2>&1 | grep -v '^ ' (cc exit=1) =====
brace03.cpp:3:16: error: type 'double' cannot be narrowed to 'int' in initializer list [-Wc++11-narrowing]
brace03.cpp:3:16: note: insert an explicit cast to silence this issue
brace03.cpp:3:16: warning: implicit conversion from 'double' to 'int' changes value from 3.9 to 3 [-Wliteral-conversion]
brace03.cpp:4:16: error: type 'double' cannot be narrowed to 'int' in initializer list [-Wc++11-narrowing]
brace03.cpp:4:16: note: insert an explicit cast to silence this issue
brace03.cpp:6:16: error: constant expression evaluates to 300 which cannot be narrowed to type 'char' [-Wc++11-narrowing]
brace03.cpp:6:16: note: insert an explicit cast to silence this issue
brace03.cpp:8:16: error: non-constant-expression cannot be narrowed from type 'int' to 'char' in initializer list [-Wc++11-narrowing]
brace03.cpp:8:16: note: insert an explicit cast to silence this issue
brace03.cpp:11:16: error: non-constant-expression cannot be narrowed from type 'int' to 'double' in initializer list [-Wc++11-narrowing]
brace03.cpp:11:16: note: insert an explicit cast to silence this issue
brace03.cpp:12:16: error: constant expression evaluates to -1 which cannot be narrowed to type 'unsigned int' [-Wc++11-narrowing]
brace03.cpp:12:16: note: insert an explicit cast to silence this issue
brace03.cpp:14:16: error: non-constant-expression cannot be narrowed from type 'long long' to 'double' in initializer list [-Wc++11-narrowing]
brace03.cpp:14:16: note: insert an explicit cast to silence this issue
brace03.cpp:6:16: warning: implicit conversion from 'int' to 'char' changes value from 300 to 44 [-Wconstant-conversion]
2 warnings and 7 errors generated.
```

- ★★ **판정은 같고 심각도가 다르다.** (5)·(7)·(9)를 clang 은 **error** 로, g++ 는 **warning** 으로 낸다.\
  그 갈림을 다음 절에서 **종료 코드로** 본다.
- ★ clang 은 `note: insert an explicit cast to silence this issue` 로 **고치는 코드까지** 보여 준다.

### (4) ★★ 표준과 구현이 갈리는 자리 — g++ 는 통과시킨다

**언제 쓰나** — 「빌드됐으니 맞다」를 의심할 때. **이 주제에서 가장 중요한 절이다.**

비상수 좁히기 둘만 남긴 파일이다.

```text
===== 소스: brace04.cpp =====
// 좁히기 중 「비상수」인 둘만 남긴 판 — g++ 는 이것을 통과시킨다
int main() {
    int n = 65;
    char   e{n};
    int m = 1;
    double g{m};
    (void)e; (void)g;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace04.cpp -o ex (cc exit=0) =====
brace04.cpp: In function ‘int main()’:
brace04.cpp:4:14: warning: narrowing conversion of ‘n’ from ‘int’ to ‘char’ [-Wnarrowing]
    4 |     char   e{n};
      |              ^
brace04.cpp:6:14: warning: narrowing conversion of ‘m’ from ‘int’ to ‘double’ [-Wnarrowing]
    6 |     double g{m};
      |              ^
```

**`cc exit=0`** — 경고 두 줄을 내고 **빌드가 끝났다.** 같은 파일을 clang 에 던지면:

```text
===== 소스: brace04.cpp =====
// 좁히기 중 「비상수」인 둘만 남긴 판 — g++ 는 이것을 통과시킨다
int main() {
    int n = 65;
    char   e{n};
    int m = 1;
    double g{m};
    (void)e; (void)g;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic brace04.cpp -o ex (cc exit=1) =====
brace04.cpp:4:14: error: non-constant-expression cannot be narrowed from type 'int' to 'char' in initializer list [-Wc++11-narrowing]
    4 |     char   e{n};
      |              ^
brace04.cpp:4:14: note: insert an explicit cast to silence this issue
    4 |     char   e{n};
      |              ^
      |              static_cast<char>( )
brace04.cpp:6:14: error: non-constant-expression cannot be narrowed from type 'int' to 'double' in initializer list [-Wc++11-narrowing]
    6 |     double g{m};
      |              ^
brace04.cpp:6:14: note: insert an explicit cast to silence this issue
    6 |     double g{m};
      |              ^
      |              static_cast<double>( )
2 errors generated.
```

- ★★★ **표준이 정한 답은 clang 쪽**이다 — 목록 초기화 안의 좁히기는 **ill-formed** 이고,\
  구현은 진단을 낼 의무가 있을 뿐 **거부할 의무는 없다.** g++ 는 그 재량을 「경고」로 쓴다.
- ★★ **그래서 「경고 0건」도 「g++ 에서 빌드됨」도 근거가 못 된다.** 이 주제의 다섯 층 표에서\
  「도구가 못 보는 것」의 자리가 바로 여기다((13)).

g++ 에서 표준 쪽 답을 받으려면 **`-pedantic` 으로는 안 되고** `-pedantic-errors` 나 `-Werror=narrowing` 이라야 한다.

```text
===== 소스: brace04.cpp =====
// 좁히기 중 「비상수」인 둘만 남긴 판 — g++ 는 이것을 통과시킨다
int main() {
    int n = 65;
    char   e{n};
    int m = 1;
    double g{m};
    (void)e; (void)g;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic-errors brace04.cpp -o ex (cc exit=1) =====
brace04.cpp: In function ‘int main()’:
brace04.cpp:4:14: error: narrowing conversion of ‘n’ from ‘int’ to ‘char’ [-Wnarrowing]
    4 |     char   e{n};
      |              ^
brace04.cpp:6:14: error: narrowing conversion of ‘m’ from ‘int’ to ‘double’ [-Wnarrowing]
    6 |     double g{m};
      |              ^
```

### (5) 경고를 플래그별로 세기 — 종료 코드와 함께

**언제 쓰나** — 「경고 몇 건」을 기록할 때. **종료 코드를 같이 안 보면 뜻이 없다.**

```text
===== 소스: count04.sh =====
# 경고를 플래그별로 센다 — 종료 코드와 함께 봐야 뜻이 있다
for f in '-Wall -Wextra' '-Wall -Wextra -pedantic' \
         '-Wall -Wextra -pedantic-errors' '-Wall -Wextra -Werror=narrowing'; do
  o=$(g++ -std=c++20 $f brace04.cpp -o ex 2>&1)
  echo "g++     [$f] cc exit=$? · warning:=$(printf '%s' "$o" | grep -c 'warning:') · error:=$(printf '%s' "$o" | grep -c 'error:')"
done
for f in '-Wall -Wextra' '-Wall -Wextra -pedantic'; do
  o=$(clang++ -std=c++20 $f brace04.cpp -o ex 2>&1)
  echo "clang++ [$f] cc exit=$? · warning:=$(printf '%s' "$o" | grep -c 'warning:') · error:=$(printf '%s' "$o" | grep -c 'error:')"
done
===== bash count04.sh (exit=0) =====
g++     [-Wall -Wextra] cc exit=0 · warning:=2 · error:=0
g++     [-Wall -Wextra -pedantic] cc exit=0 · warning:=2 · error:=0
g++     [-Wall -Wextra -pedantic-errors] cc exit=1 · warning:=0 · error:=2
g++     [-Wall -Wextra -Werror=narrowing] cc exit=1 · warning:=0 · error:=2
clang++ [-Wall -Wextra] cc exit=1 · warning:=0 · error:=2
clang++ [-Wall -Wextra -pedantic] cc exit=1 · warning:=0 · error:=2
```

| 컴파일러·플래그 | `cc exit` | `warning:` | `error:` |
|---|---|---|---|
| g++ `-Wall -Wextra` | **0** | 2 | 0 |
| g++ `-Wall -Wextra -pedantic` | **0** | 2 | 0 |
| g++ `-Wall -Wextra -pedantic-errors` | **1** | 0 | **2** |
| g++ `-Wall -Wextra -Werror=narrowing` | **1** | 0 | **2** |
| clang++ `-Wall -Wextra` | **1** | 0 | **2** |
| clang++ `-Wall -Wextra -pedantic` | **1** | 0 | **2** |

- ★★ **`-pedantic` 은 이 자리에서 아무것도 안 바꾼다.** 표준 준수를 주장하려면 **`-pedantic-errors`** 라야 한다.\
  C 갈래에서 「`-std=` 는 강제가 아니라 기본값 선택」으로 정리된 것과 **같은 집안**이다.
- ★ 세는 법 — `grep -c 'warning:'` 이다. `grep -c warning` 은 clang 의 `2 warnings generated.` 요약 줄까지 세어\
  진단 수와 어긋난다.

### (6) `initializer_list` 가 이기는 것 — 그리고 안 이기는 것

**언제 쓰나** — 자기 클래스에 `initializer_list` 생성자를 **넣을지 말지** 정할 때.

```text
===== 소스: brace05.cpp =====
// initializer_list 가 다른 생성자를 이기는 것 — 그리고 빈 {} 는 안 이긴다
#include <cstdio>
#include <initializer_list>

struct W {
    W()                             { std::printf("W()\n"); }
    W(int, int)                     { std::printf("W(int,int)\n"); }
    W(std::initializer_list<int> l) { std::printf("W(init_list) size=%zu\n", l.size()); }
};

int main() {
    W a(1, 2);      // ① 괄호 — 생성자 오버로드 해석
    W b{1, 2};      // ② 중괄호 — initializer_list 가 먼저다
    W c{};          // ③ 빈 중괄호 — 기본 생성자다
    W d({});        // ④ 빈 중괄호를 「인자로」 넘기면
    W e{1, 2, 3};   // ⑤ 셋이면 (int,int) 는 후보도 아니다
    (void)a; (void)b; (void)c; (void)d; (void)e;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
W(int,int)
W(init_list) size=2
W()
W(init_list) size=0
W(init_list) size=3
```

| 쓴 것 | 불린 것 | 왜 |
|---|---|---|
| `W a(1, 2)` | `W(int,int)` | 괄호 — **평범한 오버로드 해석**이다 |
| `W b{1, 2}` | ★ `W(init_list)` size=2 | 중괄호 — `initializer_list` 를 **먼저** 본다 |
| `W c{}` | ★ `W()` | ★ **빈 중괄호는 기본 생성자다** — 크기 0 목록이 아니다 |
| `W d({})` | `W(init_list)` size=0 | 빈 중괄호를 **인자로** 넘기면 목록이 된다 |
| `W e{1, 2, 3}` | `W(init_list)` size=3 | `W(int,int)` 는 인자 수가 안 맞아 후보가 아니다 |

- ★★★ **③과 ④의 차이가 규칙의 전부다.** `W c{}` 의 중괄호는 **초기화 문법**이고,\
  `W d({})` 의 안쪽 중괄호는 **인자로 넘기는 목록**이다.
- ★ 규칙을 한 문장으로 — **「중괄호 초기화에서 `initializer_list` 생성자는 다른 모든 생성자보다 먼저 고려된다.\
  단 목록이 비어 있으면 기본 생성자가 먼저다.」**
- ★ 이 우선권은 형제 [`01번`](../01-function-overloading-and-overload-resolution/)의 일반 규칙 **위에 얹히는 한 겹**이다 —\
  후보를 **줄 세우는** 것이 아니라 **먼저 한 번 걸러 본다.**

### (7) 이겨서 에러가 되는 자리 — 우선권이 얼마나 센가

**언제 쓰나** — 「`initializer_list` 가 진다면 언제 지나」를 가를 때. 답은 **거의 안 진다**다.

```text
===== 소스: brace06.cpp =====
// initializer_list 가 「이겨서 에러가 되는」 자리
#include <cstdio>
#include <initializer_list>

struct W {
    W(double, double)               { std::printf("W(double,double)\n"); }
    W(std::initializer_list<int> l) { std::printf("W(init_list) size=%zu\n", l.size()); }
};

int main() {
    W f(1.0, 2.0);   // 괄호 — 정확히 맞는 생성자가 있다
    W g{1.0, 2.0};   // 중괄호 — initializer_list<int> 가 먼저 뽑힌다
    (void)f; (void)g;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace06.cpp -o ex (cc exit=1) =====
brace06.cpp: In function ‘int main()’:
brace06.cpp:12:17: error: narrowing conversion of ‘1.0e+0’ from ‘double’ to ‘int’ [-Wnarrowing]
   12 |     W g{1.0, 2.0};   // 중괄호 — initializer_list<int> 가 먼저 뽑힌다
      |                 ^
```

같은 소스를 clang 으로.

```text
===== 소스: brace06.cpp =====
// initializer_list 가 「이겨서 에러가 되는」 자리
#include <cstdio>
#include <initializer_list>

struct W {
    W(double, double)               { std::printf("W(double,double)\n"); }
    W(std::initializer_list<int> l) { std::printf("W(init_list) size=%zu\n", l.size()); }
};

int main() {
    W f(1.0, 2.0);   // 괄호 — 정확히 맞는 생성자가 있다
    W g{1.0, 2.0};   // 중괄호 — initializer_list<int> 가 먼저 뽑힌다
    (void)f; (void)g;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic brace06.cpp -o ex (cc exit=1) =====
brace06.cpp:12:9: error: type 'double' cannot be narrowed to 'int' in initializer list [-Wc++11-narrowing]
   12 |     W g{1.0, 2.0};   // 중괄호 — initializer_list<int> 가 먼저 뽑힌다
      |         ^~~
brace06.cpp:12:9: note: insert an explicit cast to silence this issue
   12 |     W g{1.0, 2.0};   // 중괄호 — initializer_list<int> 가 먼저 뽑힌다
      |         ^~~
      |         static_cast<int>( )
brace06.cpp:12:14: error: type 'double' cannot be narrowed to 'int' in initializer list [-Wc++11-narrowing]
   12 |     W g{1.0, 2.0};   // 중괄호 — initializer_list<int> 가 먼저 뽑힌다
      |              ^~~
brace06.cpp:12:14: note: insert an explicit cast to silence this issue
   12 |     W g{1.0, 2.0};   // 중괄호 — initializer_list<int> 가 먼저 뽑힌다
      |              ^~~
      |              static_cast<int>( )
2 errors generated.
```

- ★★★ **`W(double,double)` 이 정확히 맞는데도 안 뽑혔다.** `initializer_list<int>` 가 먼저 뽑히고,\
  그 다음에 `1.0` → `int` 가 **좁히기라서** 거부된 것이다.\
  **「더 잘 맞는 생성자가 있으니 그쪽으로 가겠지」가 안 통한다.**
- ★★ 그래서 **`initializer_list` 생성자를 만들 때는 그것이 그 타입의 「기본 해석」이 된다**고 읽어야 한다.\
  `std::vector` 가 정확히 그 값을 치르고 있다((1)).
- ★ clang 은 **두 인자 모두**를 에러로 세고(`2 errors generated.`), g++ 는 **한 줄**만 낸다 —\
  **에러를 몇 개로 세는가는 구현이다.**

### (8) 가장 성가신 파싱 — `{}` 가 지우는 두 번째 함정

**언제 쓰나** — 인자 없는 생성자를 부를 때마다.

```text
===== 소스: brace07.cpp =====
// 가장 성가신 파싱 — T t(); 는 변수가 아니다
#include <cstdio>

struct T {
    int v = 7;
    T() { std::printf("T()\n"); }
};

int main() {
    T t();
    std::printf("t.v = %d\n", t.v);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace07.cpp -o ex (cc exit=1) =====
brace07.cpp: In function ‘int main()’:
brace07.cpp:10:8: warning: empty parentheses were disambiguated as a function declaration [-Wvexing-parse]
   10 |     T t();
      |        ^~
brace07.cpp:10:8: note: remove parentheses to default-initialize a variable
   10 |     T t();
      |        ^~
      |        --
brace07.cpp:10:8: note: or replace parentheses with braces to value-initialize a variable
brace07.cpp:11:33: error: request for member ‘v’ in ‘t’, which is of non-class type ‘T()’
   11 |     std::printf("t.v = %d\n", t.v);
      |                                 ^
```

clang 은 이렇게 말한다.

```text
===== 소스: brace07.cpp =====
// 가장 성가신 파싱 — T t(); 는 변수가 아니다
#include <cstdio>

struct T {
    int v = 7;
    T() { std::printf("T()\n"); }
};

int main() {
    T t();
    std::printf("t.v = %d\n", t.v);
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic brace07.cpp -o ex (cc exit=1) =====
brace07.cpp:10:8: warning: empty parentheses interpreted as a function declaration [-Wvexing-parse]
   10 |     T t();
      |        ^~
brace07.cpp:10:8: note: remove parentheses to declare a variable
   10 |     T t();
      |        ^~
brace07.cpp:11:31: error: base of member reference is a function; perhaps you meant to call it with no arguments?
   11 |     std::printf("t.v = %d\n", t.v);
      |                               ^
      |                                ()
1 warning and 1 error generated.
```

- ★★ **`T t();` 는 「`T` 를 돌려주고 인자가 없는 함수 `t`」의 선언**이다. 변수가 아니다.\
  그래서 `t.v` 가 **`non-class type 'T()'`** 라는 에러를 낸다.
- ★ **두 컴파일러가 같은 경고 이름**(`-Wvexing-parse`)을 쓴다. g++ 는 고침을 **둘** 제안하고\
  (괄호를 지워 기본 초기화 · 중괄호로 바꿔 값 초기화), clang 은 **하나**만 제안한다.
- ★★ **`T t{};` 를 쓰면 이 함정이 없다.** 중괄호는 **선언 문법으로 읽힐 수 없기 때문**이다 —\
  「어디에나 중괄호」를 권하는 가장 실용적인 근거가 이것이다.
- ★ 이 함정은 **인자가 있어도 난다** — `T t(U());` 같은 꼴. 이 문서는 **빈 괄호 판만 던졌다.**

### (9) `auto` 와 중괄호 — 타입을 컴파일러 입으로 찍는다

**언제 쓰나** — `auto` 와 `{}` 를 같이 쓸 때. **두 꼴이 다른 타입**이 된다.

```text
===== 소스: brace08.cpp =====
// auto x{1} 대 auto x = {1} — 타입을 의도적 타입 에러로 찍는다
#include <initializer_list>

template <class T> struct TypeOf;   // 선언만 — 정의가 없다

int main() {
    auto a{1};
    auto b = {1};
    auto c = {1, 2};
    TypeOf<decltype(a)> ta;
    TypeOf<decltype(b)> tb;
    TypeOf<decltype(c)> tc;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace08.cpp -o ex (cc exit=1) =====
brace08.cpp: In function ‘int main()’:
brace08.cpp:10:25: error: aggregate ‘TypeOf<int> ta’ has incomplete type and cannot be defined
   10 |     TypeOf<decltype(a)> ta;
      |                         ^~
brace08.cpp:11:25: error: aggregate ‘TypeOf<std::initializer_list<int> > tb’ has incomplete type and cannot be defined
   11 |     TypeOf<decltype(b)> tb;
      |                         ^~
brace08.cpp:12:25: error: aggregate ‘TypeOf<std::initializer_list<int> > tc’ has incomplete type and cannot be defined
   12 |     TypeOf<decltype(c)> tc;
      |                         ^~
```

| 쓴 것 | 추론된 타입 | 언제부터 |
|---|---|---|
| `auto a{1}` | ★ **`int`** | **C++17부터.** C++11/14 에서는 `initializer_list<int>` 였다 |
| `auto b = {1}` | `std::initializer_list<int>` | C++11부터 그대로 |
| `auto c = {1, 2}` | `std::initializer_list<int>` | 〃 |

clang 의 답도 같다(문구만 다르다).

```text
===== 소스: brace08.cpp =====
// auto x{1} 대 auto x = {1} — 타입을 의도적 타입 에러로 찍는다
#include <initializer_list>

template <class T> struct TypeOf;   // 선언만 — 정의가 없다

int main() {
    auto a{1};
    auto b = {1};
    auto c = {1, 2};
    TypeOf<decltype(a)> ta;
    TypeOf<decltype(b)> tb;
    TypeOf<decltype(c)> tc;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic brace08.cpp -o ex (cc exit=1) =====
brace08.cpp:10:25: error: implicit instantiation of undefined template 'TypeOf<int>'
   10 |     TypeOf<decltype(a)> ta;
      |                         ^
brace08.cpp:4:27: note: template is declared here
    4 | template <class T> struct TypeOf;   // 선언만 — 정의가 없다
      |                           ^
brace08.cpp:11:25: error: implicit instantiation of undefined template 'TypeOf<std::initializer_list<int>>'
   11 |     TypeOf<decltype(b)> tb;
      |                         ^
brace08.cpp:4:27: note: template is declared here
    4 | template <class T> struct TypeOf;   // 선언만 — 정의가 없다
      |                           ^
brace08.cpp:12:25: error: implicit instantiation of undefined template 'TypeOf<std::initializer_list<int>>'
   12 |     TypeOf<decltype(c)> tc;
      |                         ^
brace08.cpp:4:27: note: template is declared here
    4 | template <class T> struct TypeOf;   // 선언만 — 정의가 없다
      |                           ^
3 errors generated.
```

원소가 둘인 **직접** 목록 초기화는 아예 막힌다.

```text
===== 소스: brace09.cpp =====
// auto 의 직접 목록 초기화는 원소가 하나여야 한다
int main() {
    auto c{1, 2};
    (void)c;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace09.cpp -o ex (cc exit=1) =====
brace09.cpp: In function ‘int main()’:
brace09.cpp:3:16: error: direct-list-initialization of ‘auto’ requires exactly one element [-fpermissive]
    3 |     auto c{1, 2};
      |                ^
brace09.cpp:3:16: note: for deduction to ‘std::initializer_list’, use copy-list-initialization (i.e. add ‘=’ before the ‘{’)
brace09.cpp:3:16: error: deducing from brace-enclosed initializer list requires ‘#include <initializer_list>’
  +++ |+#include <initializer_list>
    1 | // auto 의 직접 목록 초기화는 원소가 하나여야 한다
    2 | int main() {
    3 |     auto c{1, 2};
      |                ^
```

- ★★ **`=` 하나가 타입을 바꾼다.** `auto a{1}` 은 값이고 `auto b = {1}` 은 **목록**이다.
- ★ **`TypeOf<T>` 가 없으면 이것을 볼 방법이 없다** — 둘 다 컴파일되고 아무것도 안 찍는다.\
  이 도구의 정본은 형제 [**05번**](../05-auto-and-decltype-type-deduction/)이다.
- ★ g++ 의 `note:` 가 고침을 직접 말해 준다 — **`=` 를 붙이라**고.

### (10) 집합체 초기화와 지정 초기자 — C 와 갈리는 셋

**언제 쓰나** — 설정 구조체·POD 를 채울 때.

```text
===== 소스: brace10.cpp =====
// 집합체 초기화와 지정 초기자(C++20) — 빠진 멤버는 값 초기화된다
#include <cstdio>

struct P { int x; int y; int z; };

int main() {
    P a{1, 2, 3};
    P b{.x = 1, .z = 3};
    P c{1};
    P d{};
    std::printf("a = %d,%d,%d\n", a.x, a.y, a.z);
    std::printf("b = %d,%d,%d\n", b.x, b.y, b.z);
    std::printf("c = %d,%d,%d\n", c.x, c.y, c.z);
    std::printf("d = %d,%d,%d\n", d.x, d.y, d.z);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace10.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
brace10.cpp: In function ‘int main()’:
brace10.cpp:8:23: warning: missing initializer for member ‘P::y’ [-Wmissing-field-initializers]
    8 |     P b{.x = 1, .z = 3};
      |                       ^
brace10.cpp:9:10: warning: missing initializer for member ‘P::y’ [-Wmissing-field-initializers]
    9 |     P c{1};
      |          ^
brace10.cpp:9:10: warning: missing initializer for member ‘P::z’ [-Wmissing-field-initializers]
a = 1,2,3
b = 1,0,3
c = 1,0,0
d = 0,0,0
```

| 쓴 것 | 결과 | 규칙 |
|---|---|---|
| `P a{1, 2, 3}` | `1,2,3` | 멤버 **선언 순서**대로 |
| `P b{.x = 1, .z = 3}` | `1,0,3` | 지정 초기자(C++20) — **빠진 `y` 는 값 초기화** |
| `P c{1}` | `1,0,0` | 뒤가 전부 값 초기화 |
| `P d{}` | `0,0,0` | 전부 값 초기화 |

- ★ `-Wextra` 의 **`-Wmissing-field-initializers`** 가 빠뜨린 멤버를 **경고로** 알려 준다.\
  「0 이 들어가길 바란 것」과 「빠뜨린 것」을 컴파일러는 구별하지 못하므로 **의도라면 `= {}` 를 명시**한다.

C++20 의 지정 초기자는 **C99 의 그것보다 좁다.** 셋을 던져 본다.

```text
===== 소스: brace11.cpp =====
// C 에서 되고 C++ 에서 안 되는 지정 초기자 셋
struct P { int x; int y; int z; };

int main() {
    P a{.z = 3, .x = 1};       // ① 선언 순서를 어긴다
    P b{.x = 1, 2};            // ② 지정과 위치를 섞는다
    int arr[3] = {[1] = 5};    // ③ 배열 지정 초기자
    (void)a; (void)b; (void)arr;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace11.cpp -o ex (cc exit=1) =====
brace11.cpp: In function ‘int main()’:
brace11.cpp:5:23: warning: missing initializer for member ‘P::x’ [-Wmissing-field-initializers]
    5 |     P a{.z = 3, .x = 1};       // ① 선언 순서를 어긴다
      |                       ^
brace11.cpp:5:23: warning: missing initializer for member ‘P::y’ [-Wmissing-field-initializers]
brace11.cpp:5:23: error: designator order for field ‘P::x’ does not match declaration order in ‘P’
brace11.cpp:6:17: error: either all initializer clauses should be designated or none of them should be
    6 |     P b{.x = 1, 2};            // ② 지정과 위치를 섞는다
      |                 ^
brace11.cpp:6:18: warning: missing initializer for member ‘P::z’ [-Wmissing-field-initializers]
    6 |     P b{.x = 1, 2};            // ② 지정과 위치를 섞는다
      |                  ^
brace11.cpp:7:19: warning: ISO C++ does not allow C99 designated initializers [-Wpedantic]
    7 |     int arr[3] = {[1] = 5};    // ③ 배열 지정 초기자
      |                   ^
brace11.cpp:7:26: sorry, unimplemented: non-trivial designated initializers not supported
    7 |     int arr[3] = {[1] = 5};    // ③ 배열 지정 초기자
      |                          ^
```

같은 셋을 C 로 던지면 — **진단이 한 줄도 없다.**

```text
===== 소스: desig01.c =====
/* 같은 셋을 C 로 던지면 */
struct P { int x; int y; int z; };

int main(void) {
    struct P a = {.z = 3, .x = 1};
    struct P b = {.x = 1, 2};
    int arr[3] = {[1] = 5};
    (void)a; (void)b; (void)arr;
    return 0;
}
===== gcc -std=c17 -Wall -Wextra -pedantic desig01.c -o ex (cc exit=0) =====
```

| 쓴 것 | C(gcc 13, `-std=c17 -pedantic`) | C++(g++ 13, C++20) | clang++ |
|---|---|---|---|
| `.z = 3, .x = 1`(순서 어김) | **통과**(진단 0) | ★ **에러** | ★ **경고**(`-Wreorder-init-list`) |
| `.x = 1, 2`(지정·위치 혼합) | **통과** | ★ **에러** | ★ **경고**(`-Wc99-designator`) |
| `[1] = 5`(배열 지정 초기자) | **통과** | ★ **에러**(`sorry, unimplemented`) | ★ **경고**(`-Wc99-designator`) |

clang 은 같은 파일에 **경고 5건으로 `cc exit=0`** 을 준다.

```text
===== 소스: brace11.cpp =====
// C 에서 되고 C++ 에서 안 되는 지정 초기자 셋
struct P { int x; int y; int z; };

int main() {
    P a{.z = 3, .x = 1};       // ① 선언 순서를 어긴다
    P b{.x = 1, 2};            // ② 지정과 위치를 섞는다
    int arr[3] = {[1] = 5};    // ③ 배열 지정 초기자
    (void)a; (void)b; (void)arr;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic brace11.cpp -o ex 2>&1 | grep -E 'warning:|error:|note:|generated' (cc exit=0) =====
brace11.cpp:5:22: warning: ISO C++ requires field designators to be specified in declaration order; field 'z' will be initialized after field 'x' [-Wreorder-init-list]
brace11.cpp:5:14: note: previous initialization for field 'z' is here
brace11.cpp:5:23: warning: missing field 'y' initializer [-Wmissing-field-initializers]
brace11.cpp:6:9: warning: mixture of designated and non-designated initializers in the same initializer list is a C99 extension [-Wc99-designator]
brace11.cpp:6:17: note: first non-designated initializer is here
brace11.cpp:6:18: warning: missing field 'z' initializer [-Wmissing-field-initializers]
brace11.cpp:7:19: warning: array designators are a C99 extension [-Wc99-designator]
5 warnings generated.
```

- ★★★ **여기서도 두 컴파일러가 갈린다** — g++ 는 거부, clang 은 통과다. (4)와 **같은 성질의 사고**다.
- ★★ **C++ 가 일부러 뺀 것**은 「순서 어김」과 「혼합」이다. C++ 는 **멤버 파괴가 선언 역순**임을 보장하는데,\
  초기화 순서가 지정 순서를 따라가면 **파괴 순서와 짝이 안 맞는다.** 그래서 **선언 순서만** 허용한다.
- ★ **배열 지정 초기자는 C++ 에 없다.** g++ 의 `sorry, unimplemented` 는 「에러」가 아니라\
  「**GCC 확장인데 이 자리에서는 구현이 없다**」는 뜻이라 문구가 다르다.
- ★ C 쪽 정본(`.x = 1` 로 나머지가 0 이 되는 규칙 전부)은 C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **21번**이다.\
  여기서는 **갈리는 셋만** 실측했다.

### (11) ★★ C++20 의 괄호 집합체 초기화 — 좁히기 검사가 없다

**언제 쓰나** — C++20 으로 올린 코드에서 `{}` 를 `()` 로 바꾸고 싶어질 때. **하지 마라**가 답이다.

```text
===== 소스: brace13.cpp =====
// C++20 괄호 집합체 초기화 — 좁히기 검사가 없다
#include <cstdio>

struct P { int x; int y; int z; };

int main() {
    P a(1, 2, 3);
    P b(1, 2.9, 3);
    std::printf("a = %d,%d,%d\n", a.x, a.y, a.z);
    std::printf("b = %d,%d,%d\n", b.x, b.y, b.z);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace13.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a = 1,2,3
b = 1,2,3
```

**`b.y` 가 `2` 다.** `2.9` 가 **조용히 잘렸고 진단은 0건**이다. 같은 값을 중괄호로 쓰면:

```text
===== 소스: brace14.cpp =====
// 같은 값을 중괄호로 — 이쪽은 좁히기가 걸린다
struct P { int x; int y; int z; };

int main() {
    P b{1, 2.9, 3};
    (void)b;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace14.cpp -o ex (cc exit=1) =====
brace14.cpp: In function ‘int main()’:
brace14.cpp:5:12: error: narrowing conversion of ‘2.8999999999999999e+0’ from ‘double’ to ‘int’ [-Wnarrowing]
    5 |     P b{1, 2.9, 3};
      |            ^~~
```

`-std=c++17` 로 던지면 괄호 쪽이 **아예 안 된다** — 이 기능이 C++20 에서 들어온 것이기 때문이다.

```text
===== 소스: brace13.cpp =====
// C++20 괄호 집합체 초기화 — 좁히기 검사가 없다
#include <cstdio>

struct P { int x; int y; int z; };

int main() {
    P a(1, 2, 3);
    P b(1, 2.9, 3);
    std::printf("a = %d,%d,%d\n", a.x, a.y, a.z);
    std::printf("b = %d,%d,%d\n", b.x, b.y, b.z);
}
===== g++ -std=c++17 -Wall -Wextra -pedantic brace13.cpp -o ex 2>&1 | head -12 (cc exit=1) =====
brace13.cpp: In function ‘int main()’:
brace13.cpp:7:16: error: no matching function for call to ‘P::P(int, int, int)’
    7 |     P a(1, 2, 3);
      |                ^
brace13.cpp:4:8: note: candidate: ‘P::P()’
    4 | struct P { int x; int y; int z; };
      |        ^
brace13.cpp:4:8: note:   candidate expects 0 arguments, 3 provided
brace13.cpp:4:8: note: candidate: ‘constexpr P::P(const P&)’
brace13.cpp:4:8: note:   candidate expects 1 argument, 3 provided
brace13.cpp:4:8: note: candidate: ‘constexpr P::P(P&&)’
brace13.cpp:4:8: note:   candidate expects 1 argument, 3 provided
```

- ★★★ **이것이 이 주제의 가장 날카로운 대비다.** 같은 집합체·같은 값인데\
  **중괄호는 에러, 괄호는 조용한 절단**이다. 그리고 **괄호 쪽은 C++20 에서 새로 생긴 자리**다.
- ★★ **C++20 괄호 집합체 초기화는 좁히기 검사를 하지 않는다** — 함수 호출 인자 변환과 같은 규칙을 쓰기 때문이다.\
  「`()` 와 `{}` 중 아무거나」가 **C++20 에서 더 위험해졌다.**
- ★ clang 도 g++ 와 **같은 답**이다(진단 0건 · `b.y = 2`).

### (12) 값 초기화 — `{}` 가 「0 으로 채워라」가 되는 자리

**언제 쓰나** — 멤버·지역 변수를 선언할 때마다.

```text
===== 소스: brace12.cpp =====
// 값 초기화 — {} 가 「0 으로 채워라」가 되는 자리
#include <cstdio>

struct A { int a; int b; };

int main() {
    int    i{};
    int*   p{};
    double d{};
    A      s{};
    std::printf("i=%d  p=%s  d=%g  s={%d,%d}\n",
                i, p ? "非null" : "nullptr", d, s.a, s.b);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace12.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
i=0  p=nullptr  d=0  s={0,0}
```

- **기본 타입은 0**, **포인터는 `nullptr`**, **집합체는 멤버마다 값 초기화**다.
- ★ `A t;`(중괄호 없이, 지역)는 **기본 초기화**라 멤버 값이 **불확정**이다.\
  ★ **이 문서는 그 값을 싣지 않았다** — 불확정 값은 「흔들리는 칸」이라 근거로 못 쓴다.\
  대신 `-Wuninitialized` 가 그것을 **경고로** 말해 준다는 사실만 적는다(이 문서에서 확인했다).
- ★ 그래서 「**선언하면 `{}` 를 붙인다**」가 이 언어의 기본 습관이 된다.

### (13) 다섯 층 — 무엇이 표준이고 무엇이 도구인가

C 갈래가 굳혀 놓은 다섯 층을 그대로 쓴다.\
★★ **C++ 는 C 보다 「표준이 정하는 것」이 크다** — 이 주제의 좁히기는 **표준이 목록으로 정한 규칙**이라\
「표준」 칸이 압도적으로 두껍고 **「UB」 칸은 비어 있다.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | **좁히기 네 갈래와 그 예외** · `initializer_list` 가 **다른 생성자보다 먼저**인 것 · **빈 `{}` 는 기본 생성자**인 것 · **집합체 멤버가 선언 순서**인 것 · **값 초기화가 0/`nullptr`** 인 것 · `auto x{1}` 이 **`int`**(C++17부터) · `auto x = {1}` 이 **`initializer_list`** · **`T t();` 가 함수 선언**인 것 · 지정 초기자가 **선언 순서만** 허용하는 것 | 두 컴파일러의 실행 출력·진단이 같은 자리 | ★★ **g++ 는 비상수 좁히기를 「경고」로 통과시킨다** — `-Wall -Wextra -pedantic` 으로 **`cc exit=0`** |
| **조건부 표준** | 옵션·표준판이 있을 때만 | **지정 초기자**·**괄호 집합체 초기화**는 **C++20부터** · `auto x{1}` 이 `int` 인 것은 **C++17부터** · **배열 지정 초기자는 C++ 에 없다**(C99 에만) | `-std=c++17` 로 던져 에러 확인((11)) | — |
| **구현 정의** | 문서화 의무가 있다 | 진단 문구 · **에러를 몇 개로 세는가**(같은 줄을 g++ 1건, clang 2건) · **ill-formed 코드의 심각도**(경고인가 에러인가) · `sorry, unimplemented` 같은 확장 문구 | 두 컴파일러 대조 | — |
| **미명시** | 몇 가지 중 하나 | **해당 없음** — 이 문서가 만든 것 중에는 없다 | — | — |
| **UB** | 아무 일이나 | ★ **해당 없음**(의도적이다) — 이 주제의 프로그램은 전부 정의된 동작만 한다. 유일한 접점은 **`{}` 를 안 쓴 기본 초기화의 불확정 값**인데 **이 문서는 안 읽었다** | — | `-Wuninitialized` 가 경고로 말해 준다 |

**「도구가 못 보는 것」을 층마다 — 전용 표**

| 사실 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | 비고 |
|---|---|---|---|
| 좁히기(상수식·안 들어감) | **에러** | **에러** | 판정이 같다 |
| ★ 좁히기(**비상수**) | ★★ **경고 2 · `cc exit=0`** | **에러 2 · `cc exit=1`** | ★ 표준은 **clang 쪽**이다 |
| 〃 `-pedantic-errors` 를 주면 | **에러 2 · `cc exit=1`** | 〃 | ★ **`-pedantic` 만으로는 안 바뀐다** |
| ★ 지정 초기자 **순서 어김·혼합** | ★ **에러 · `cc exit=1`** | ★★ **경고 5 · `cc exit=0`** | ★ 이번엔 **반대로** 갈린다 |
| ★ **괄호 집합체 초기화의 절단**(`2.9`→`2`) | ★★ **0건** | ★★ **0건** | ★ **어떤 플래그도 안 말해 준다** |
| `T t();`(가장 성가신 파싱) | 경고 1 + note 2 | 경고 1 + note 1 | 이름은 둘 다 `-Wvexing-parse` |
| 집합체에서 빠뜨린 멤버 | `-Wextra` 로 경고 | 〃 | 의도와 실수를 구별하지 못한다 |

- ★★★ **이 주제의 위험은 UB 가 아니라 「조용한 통과」다.** 갈라 보면 셋이다 —\
  ① g++ 가 ill-formed 를 경고로 넘기는 것 · ② clang 이 지정 초기자 위반을 경고로 넘기는 것 ·\
  ③ **괄호 집합체 초기화가 좁히기를 아무 말 없이 잘라 버리는 것.**\
  ★ ③은 **두 컴파일러가 모두 조용하다** — 도구로는 못 잡고 **코드에서 `()` 를 안 쓰는 것**만이 답이다.

## 문법 — 형태와 규칙

### 형태

```cpp
/* brace05.cpp */
// initializer_list 가 다른 생성자를 이기는 것 — 그리고 빈 {} 는 안 이긴다
#include <cstdio>
#include <initializer_list>

struct W {
    W()                             { std::printf("W()\n"); }
    W(int, int)                     { std::printf("W(int,int)\n"); }
    W(std::initializer_list<int> l) { std::printf("W(init_list) size=%zu\n", l.size()); }
};

int main() {
    W a(1, 2);      // ① 괄호 — 생성자 오버로드 해석
    W b{1, 2};      // ② 중괄호 — initializer_list 가 먼저다
    W c{};          // ③ 빈 중괄호 — 기본 생성자다
    W d({});        // ④ 빈 중괄호를 「인자로」 넘기면
    W e{1, 2, 3};   // ⑤ 셋이면 (int,int) 는 후보도 아니다
    (void)a; (void)b; (void)c; (void)d; (void)e;
}
```

규칙 불릿.

- **`T t{...}`**(직접 목록 초기화) · **`T t = {...}`**(복사 목록 초기화) — 둘 다 좁히기를 막는다.\
  차이는 `explicit` 생성자를 쓸 수 있는지뿐이다.
- **`initializer_list` 생성자가 있으면 다른 모든 생성자보다 먼저 고려한다.** 단 **빈 `{}` 는 기본 생성자**.
- **집합체는 멤버를 선언 순서대로** 채우고, **남은 멤버는 값 초기화**된다.
- **지정 초기자 `{.x = 1}` 는 C++20부터**이고 **선언 순서만** 허용한다. 위치와 **섞을 수 없다.**
- **`T t{}` 는 값 초기화** — 기본 타입 0, 포인터 `nullptr`.
- **`T t();` 는 함수 선언**이다. 변수를 원하면 `T t;` 나 `T t{};`.
- **`auto x{1}` 은 `int`(C++17부터), `auto x = {1}` 은 `std::initializer_list<int>`.**
- **괄호로 하는 집합체 초기화는 C++20부터** — 그리고 **좁히기 검사가 없다.**

### 금지 사례 — 던져서 받은 여섯

| 쓴 것 | 컴파일러 | 무엇이 나오나 |
|---|---|---|
| `int b{3.0}` | g++ | ``error: narrowing conversion of `3.0e+0` from `double` to `int`  [-Wnarrowing]`` |
| 〃 | clang | ``error: type `double` cannot be narrowed to `int` in initializer list  [-Wc++11-narrowing]`` |
| `char d{300}` | clang | ``error: constant expression evaluates to 300 which cannot be narrowed to type `char` `` |
| `char e{n}`(비상수) | g++ | ★ **warning** — 빌드는 된다 |
| 〃 | clang | ``error: non-constant-expression cannot be narrowed from type `int` to `char` in initializer list`` |
| `W g{1.0, 2.0}`(`initializer_list<int>` 가 있다) | g++ | `error: narrowing conversion ...` — **정확히 맞는 생성자가 있어도 안 간다** |
| `auto c{1, 2}` | g++ | ``error: direct-list-initialization of `auto` requires exactly one element`` |
| `T t(); t.v` | g++ | ``error: request for member `v` in `t`, which is of non-class type `T()` `` |
| `P a{.z = 3, .x = 1}` | g++ | ``error: designator order for field `P::x` does not match declaration order in `P` `` |
| 〃 | clang | ★ **warning** — 빌드는 된다 |
| `P b{.x = 1, 2}` | g++ | `error: either all initializer clauses should be designated or none of them should be` |
| `int arr[3] = {[1] = 5}` | g++ | `sorry, unimplemented: non-trivial designated initializers not supported` |
| `P a(1,2,3)` 를 `-std=c++17` 로 | g++ | ``error: no matching function for call to `P::P(int, int, int)` `` |

### 고를 것을 손으로 돌리는 순서

1. **기본은 `{}`** — 좁히기를 막고, 가장 성가신 파싱을 지우고, 값 초기화를 공짜로 준다.
2. **`initializer_list` 생성자가 있는 타입인가?** 있으면 `{}` 가 **원소 목록**으로 읽힌다.\
   「개수와 값」을 넘길 의도면 **괄호를 쓴다**(`std::vector<int> v(3, 0)`).
3. **좁히기 진단을 받았으면 `static_cast` 로 뭉개지 말고 먼저 묻는다** — 그 값이 정말 들어가는가.
4. **자기 클래스에 `initializer_list` 생성자를 넣을지**는 (7)을 보고 정한다 —\
   넣는 순간 **그것이 그 타입의 기본 해석**이 된다.
5. **C++20 이라고 집합체를 괄호로 채우지 않는다**((11)) — 좁히기 검사가 사라진다.
6. **표준 준수를 주장하려면 `-pedantic-errors`**(또는 최소 `-Werror=narrowing`)를 켠다((5)).

## 어디서 틀리나

### 1. ★★★ 「중괄호는 괄호와 같다 — 취향 문제다」

아니다. **`initializer_list` 생성자가 후보일 때 완전히 다른 생성자가 불린다**((1)).\
`std::vector<int> v{3}` 은 **크기 3 이 아니라 값 3** 이다.\
★ 다만 **조건이 하나뿐**이라는 것도 같이 외운다 — `initializer_list` 가 후보가 아니면 **둘은 같다**((2)).

### 2. ★★★ 「좁히기는 상수식이면 통과한다」

**부동→정수에는 상수식 예외가 없다**((3)). `int b{3.0}` 은 값이 정확한데도 **에러**다.\
★ 예외가 있는 것은 ②③④뿐이고, 각각 **「범위 안인가」·「왕복이 정확한가」·「승격 뒤 값이 들어가는가」로** 조건이 다르다.

### 3. ★★★ 「g++ 로 빌드됐으니 표준에 맞다」

**비상수 좁히기는 표준이 ill-formed 라고 정했는데 g++ 는 경고로 통과시킨다**((4)) — `cc exit=0` 이다.\
★ `-pedantic` 으로는 **안 바뀐다.** `-pedantic-errors` 나 `-Werror=narrowing` 이라야 한다((5)).

### 4. ★★ 「더 잘 맞는 생성자가 있으면 그쪽으로 간다」

**`initializer_list` 는 그 앞에서 먼저 뽑힌다**((7)).\
`W(double,double)` 이 있어도 `W g{1.0, 2.0}` 은 `initializer_list<int>` 로 가서 **좁히기 에러**가 된다.

### 5. ★★ 「빈 `{}` 는 원소 0개짜리 목록이다」

아니다. **기본 생성자**다((6)). 원소 0개짜리 목록을 원하면 **`W d({})`** 처럼 인자로 넘겨야 한다.

### 6. ★★ 「C++20 이니까 집합체도 괄호로 채우면 된다」

된다. 그런데 **좁히기 검사가 없다**((11)). `P b(1, 2.9, 3)` 이 **진단 0건으로 `2.9` 를 잘라** 넣는다.\
★ **두 컴파일러 모두 조용하다** — 도구가 아니라 습관으로만 막힌다.

### 7. ★★ 「지정 초기자는 C 와 같다」

**셋이 다르다**((10)) — 순서 어김 금지 · 위치와 혼합 금지 · 배열 지정 초기자 없음.\
★ 그리고 **g++ 는 에러, clang 은 경고**다. 3번과 **반대 방향으로** 갈린다.

### 8. ★ 「`T t();` 는 기본 생성자를 부른다」

**함수 선언**이다((8)). `-Wvexing-parse` 가 말해 주지만 **경고일 뿐**이고,\
실제로 막히는 것은 그 뒤에 `t.v` 를 쓸 때다.

### 9. ★ 「`auto x{1}` 과 `auto x = {1}` 은 같다」

**타입이 다르다**((9)) — `int` 와 `std::initializer_list<int>`.\
★ **C++11/14 에서는 둘 다 `initializer_list<int>` 였다** — 「언제부터」가 붙는 자리다.

### 10. 「집합체에서 멤버를 빼면 쓰레기가 들어간다」

아니다. **값 초기화**된다((10)·(12)). `P c{1}` 은 `1,0,0` 이다.\
★ 다만 `-Wextra` 가 **경고**를 내므로, 의도라면 코드로 명시하는 편이 낫다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| **좁히기 네 갈래와 그 예외 조건** | **언어**(C++11부터) |
| **부동→정수에 상수식 예외가 없는 것** | **언어** |
| `initializer_list` 생성자가 **먼저 고려되는** 것 | **언어** |
| **빈 `{}` 가 기본 생성자**인 것 | **언어** |
| 집합체 멤버가 **선언 순서**로 채워지고 **남은 것은 값 초기화**인 것 | **언어** |
| `T t();` 가 **함수 선언**인 것 | **언어** |
| `auto x{1}` 이 **`int`** 인 것 | **언어** — 단 **C++17부터**다 |
| 지정 초기자가 **선언 순서만** 허용하는 것 | **언어** — **C++20부터** |
| **괄호 집합체 초기화**가 되는 것 | **언어** — **C++20부터** |
| ★ **괄호 집합체 초기화에 좁히기 검사가 없는 것** | ★ **언어다**(구현 봐주기가 아니다) — 함수 인자 변환 규칙을 쓴다 |
| ★ **비상수 좁히기가 「경고」인 것** | ★★ **g++ 구현의 재량.** 표준은 ill-formed 라고만 하고 **거부를 요구하지 않는다** |
| ★ **지정 초기자 순서 위반이 「경고」인 것** | ★ **clang 구현의 재량.** 같은 성질이다 |
| 진단 문구 · **에러를 몇 개로 세는가** | **컴파일러 구현** |
| `sorry, unimplemented` 라는 표현 | **GCC 의 내부 표현**(확장 미구현) |

## 언제 쓰고 언제 안 쓰나

**`{}`** — **기본값.** 좁히기 차단 · 가장 성가신 파싱 회피 · 값 초기화가 한 번에 온다.

**`()`** — 두 자리에서만.\
① **`initializer_list` 가 있는 타입에 「개수와 값」을 넘길 때**(`std::vector<int> v(3, 0)`) ·\
② 생성자 인자가 **중괄호로 쓰면 목록으로 오해될 때**.\
★ **C++20 에서 집합체를 괄호로 채우는 것은 예외가 아니다** — 좁히기 검사가 사라지므로 **쓰지 않는다**((11)).

**`initializer_list` 생성자를 자기 타입에 넣기** — **「원소들의 모음」이 그 타입의 자연스러운 뜻일 때만.**\
★ 넣는 순간 **그 타입에서 `{}` 의 뜻이 고정된다**((7)) — `std::vector` 가 치르고 있는 값이다.

**지정 초기자** — 멤버가 많고 **대부분 기본값**인 설정 구조체에.\
★ **C 코드를 옮겨 올 때는 순서를 다시 맞춰야 한다**((10)).

## 핵심 문장

1. **`()` 와 `{}` 가 갈리는 조건은 하나다** — `initializer_list` 생성자가 후보인가.
2. **`std::vector<int> v{3}` 은 크기 3 이 아니라 값 3 이다.**
3. **좁히기는 표준이 목록으로 정한 네 갈래다** — 그리고 **부동→정수에는 상수식 예외가 없다.**
4. **「g++ 에서 빌드됐다」는 「표준에 맞다」가 아니다** — 비상수 좁히기가 `cc exit=0` 으로 통과한다.
5. **`initializer_list` 는 더 잘 맞는 생성자를 이기고, 이긴 뒤에 좁히기로 실패한다.**
6. **빈 `{}` 는 기본 생성자다.**
7. **C++20 의 괄호 집합체 초기화는 좁히기를 조용히 자른다** — 두 컴파일러 모두 진단 0건.

## 관련 자료

- [**01번 형제**](../01-function-overloading-and-overload-resolution/)(오버로드 해석) —\
  **후보를 줄 세우는 일반 규칙**은 거기. 여기는 그 위에 **`initializer_list` 가 먼저 걸러지는 한 겹**만((6)).
- [**02번 형제**](../02-enum-class-and-scoped-enumerations/) — `enum class` 의 고정 밑바탕 타입에\
  **중괄호로 값을 넣을 때** 이 주제의 좁히기 규칙이 그대로 걸린다.
- [**05번 형제**](../05-auto-and-decltype-type-deduction/)(`auto`·`decltype`) — (9)의 `TypeOf<T>` 창이 **거기서 주력 도구**가 된다.
- C 갈래 [`03-integer-promotion-and-usual-arithmetic-conversions/`](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/) —\
  좁히기 ④의 「**정수 승격 뒤의 값**」이 무엇인지가 거기 정본이다.
- C 갈래 [`08-sizeof-alignment-and-offsetof/`](../../../c/syntax/08-sizeof-alignment-and-offsetof/) —\
  집합체가 메모리에 어떻게 놓이는지(패딩 포함). 여기는 **무엇으로 채워지나**까지만.
- C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **21번**(구조체 선언·초기화·지정 초기자) —\
  **C99 지정 초기자의 정본.** 여기는 **C++ 가 뺀 셋**만 실측했다((10)).
- 목록의 **41번 주제**(순차 컨테이너) — `std::vector` 의 생성자 목록 자체.
- 목록의 **47번 주제**(`optional`·`variant`) — 「개수 3」과 「값 3」을 **타입으로** 갈라 놓는 방향.

## 용어 풀이

> **목록 초기화(list-initialization)** — 중괄호로 하는 초기화. `T t{...}` 와 `T t = {...}`.

> **좁히기 변환(narrowing conversion)** — 표준이 네 갈래로 정한 「값을 잃을 수 있는 변환」.\
> 목록 초기화 안에서는 **ill-formed**.

> **ill-formed** — 「문법 위반」. 구현은 **진단을 낼 의무**가 있지만 **거부할 의무는 없다** —\
> g++ 가 경고로 통과시키는 근거가 여기다((4)).

> **`std::initializer_list<T>`** — 중괄호 안 원소들의 읽기 전용 뷰. 생성자 오버로드에서 **특별 대우**를 받는다.

> **집합체(aggregate)** — 사용자 선언 생성자·private 비정적 멤버·가상 함수·기반 클래스가 없는 클래스, 또는 배열.

> **지정 초기자(designated initializer)** — `{.x = 1}`. C99 에서 왔고 **C++20부터** 쓸 수 있다(더 좁다).

> **값 초기화(value-initialization)** — `T t{}`. 기본 타입 0, 포인터 `nullptr`, 집합체는 멤버마다.

> **기본 초기화(default-initialization)** — `T t;`. 기본 타입 지역 변수는 **불확정 값**이 된다.

> **가장 성가신 파싱(most vexing parse)** — `T t();` 가 변수가 아니라 **함수 선언**으로 읽히는 것.

## 더 들어가면

- **`initializer_list` 의 수명** — 원소들은 **뒤에 숨은 임시 배열**에 있고, 그 배열의 수명은\
  `initializer_list` 객체와 같다. **멤버로 저장하면 댕글링**이 된다.\
  ★ **이 문서는 안 던졌다** — 정본은 목록의 **30번 주제**(댕글링 참조와 수명)다.
- **`initializer_list` 의 원소는 `const`** 라 **옮길 수 없다.** `std::vector<std::unique_ptr<T>>` 를\
  중괄호로 못 채우는 이유가 그것이다. ★ 이 문서는 안 던졌다.
- **CTAD 와 중괄호** — `std::vector v{1, 2, 3};` 처럼 인자에서 타입을 추론하는 규칙.\
  정본은 목록의 **32번 주제**다.
- **`explicit` 생성자와 복사 목록 초기화** — `T t = {...}` 는 `explicit` 생성자를 쓸 수 없고 `T t{...}` 는 쓸 수 있다.\
  정본은 [목록의 **24번 주제**](../24-explicit-and-converting-constructors/)다.
- **집합체의 조건이 판마다 바뀌었다** — C++11·14·17·20 에서 「집합체인가」의 기준이 계속 좁아졌다\
  (기본 멤버 초기자·상속·`explicit` 기본 생성자). ★ 이 문서는 **C++20 기준 한 판만** 던졌다.
