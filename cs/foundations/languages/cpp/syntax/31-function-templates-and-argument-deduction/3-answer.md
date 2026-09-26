# cpp/syntax/31 — 함수 템플릿과 인자 추론 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · x86-64 Linux · rustc 1.92.0 에서 실제로 돌려 얻은 것이다.\
> 소스는 질문 파일과 같다(출력 블록의 배너에 파일 이름이 있다). 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **타입의 철자(공백 · `long int` 대 `long`)와 진단 문구**다.\
> 근거로 쓰는 것은 다음이다 — **공백을 지운 `T` · 「다른 칸 N / 24」 · 에러 줄과 개수 · 인스턴스 수 · Rust 에러 코드**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **`T = int`**(`const int` 를 넘겼는데) · **`T = const char*`**(`"hi"` 를 넘겼는데) · 에러 **2 · 2** — g++ 는 `[with T = …]` 와 `is_same_v<…>`, clang 은 `requirement '…'` 와 `'probe<…>'`

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic tmpl01.cpp -o ex (cc exit=1) =====
tmpl01.cpp: In instantiation of ‘void probe(T) [with T = int]’:
tmpl01.cpp:11:10:   required from here
tmpl01.cpp:6:24: error: static assertion failed: T 를 보여 달라
    6 |     static_assert(std::is_same_v<T, void>, "T 를 보여 달라");
      |                   ~~~~~^~~~~~~~~~~~~~~~~~
tmpl01.cpp:6:24: note: ‘std::is_same_v<int, void>’ evaluates to false
tmpl01.cpp: In instantiation of ‘void probe(T) [with T = const char*]’:
tmpl01.cpp:12:10:   required from here
tmpl01.cpp:6:24: error: static assertion failed: T 를 보여 달라
tmpl01.cpp:6:24: note: ‘std::is_same_v<const char*, void>’ evaluates to false
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic tmpl01.cpp -o ex (cc exit=1) =====
tmpl01.cpp:6:19: error: static assertion failed due to requirement 'std::is_same_v<int, void>': T 를 보여 달라
    6 |     static_assert(std::is_same_v<T, void>, "T 를 보여 달라");
      |                   ^~~~~~~~~~~~~~~~~~~~~~~
tmpl01.cpp:11:5: note: in instantiation of function template specialization 'probe<int>' requested here
   11 |     probe(ci);
      |     ^
tmpl01.cpp:6:19: error: static assertion failed due to requirement 'std::is_same_v<const char *, void>': T 를 보여 달라
    6 |     static_assert(std::is_same_v<T, void>, "T 를 보여 달라");
      |                   ^~~~~~~~~~~~~~~~~~~~~~~
tmpl01.cpp:12:5: note: in instantiation of function template specialization 'probe<const char *>' requested here
   12 |     probe("hi");
      |     ^
2 errors generated.
```

**왜 그런가**

- ★★★ **값 매개변수 `T` 는 최상위 `const` 를 떨어뜨리고 배열을 감쇠시킨다** — 05편의 `auto` 와 같은 규칙.
- ★★ **`static_assert` 가 `T` 에 의존하므로 인스턴스마다 한 번씩** 실패한다 — 그 진단에 컴파일러가 **`T` 를 적는다.**

### 2. ★★★ **`T` 열에서만 감쇠(`*` 3칸) · `T&&` 열에서만 `T` 가 참조(`&` 6칸)** · `const int` 는 **`T&` 에서 `const int`, `const T&` 에서 `int`** · 두 컴파일러가 다른 칸 **0 / 24**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic tmpl02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
arg               T                     T&                    const T&              T&&                   
int arr[3]        int*                  int [3]               int [3]               int (&)[3]            
const int ci      int                   const int             int                   const int&            
int& ri           int                   int                   int                   int&                  
const int& cri    int                   const int             int                   const int&            
"hi"              const char*           const char [3]        char [3]              const char (&)[3]     
void func(int)    void (*)(int)         void(int)             void(int)             void (&)(int)         
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic tmpl02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
arg               T                     T&                    const T&              T&&                   
int arr[3]        int *                 int[3]                int[3]                int (&)[3]            
const int ci      int                   const int             int                   const int &           
int& ri           int                   int                   int                   int &                 
const int& cri    int                   const int             int                   const int &           
"hi"              const char *          const char[3]         char[3]               const char (&)[3]     
void func(int)    void (*)(int)         void (int)            void (int)            void (&)(int)         
```

```text
===== bash tmpl-grid.sh (exit=0) =====
두 컴파일러가 다른 T 를 낸 칸 0 / 24
T 에 & 가 들어간 칸 6 / 24 · T 에 * 가 생긴 칸 3 / 24
```

**왜 그런가**

- ★★★ **`T` 는 「매개변수로 복사될 값」의 타입**이라 배열·함수는 감쇠하고, 최상위 `const` 와 참조는 복사본에 의미가 없어 떨어진다.
- ★★★ **`T&` 는 인자에 그대로 묶이므로** 인자의 모양(`int[3]` · `const int`)이 `T` 로 남는다.
- ★★ **`const T&` 는 틀에 이미 `const` 가 있어** 인자의 `const` 를 틀이 맡는다 — `T` 는 `int` · `char[3]`.
- ★★ **`T&&` 에 lvalue 가 오면 `T` 가 lvalue 참조**가 되고 참조 축약으로 매개변수도 lvalue 참조(09편).
- ★ 철자는 다르지만(`int*` 대 `int *`) **공백을 지우면 24칸 전부 같다.**

### 3. ★★★ **다섯 줄 전부 에러 · 두 컴파일러 같은 줄**(각 5건) · 1. 은 **`int` 와 `double` 두 후보** · 5. 는 **2. 와 같다**(`couldn’t deduce`)

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 tmpl03.cpp -o ex (cc exit=1) =====
tmpl03.cpp: In function ‘int main()’:
tmpl03.cpp:11:11: error: no matching function for call to ‘max_of(int, double)’
   11 |     max_of(1, 2.0);          // 1. int 와 double
      |     ~~~~~~^~~~~~~~
tmpl03.cpp:5:22: note: candidate: ‘template<class T> T max_of(T, T)’
    5 | template <class T> T max_of(T a, T b) { return a < b ? b : a; }
      |                      ^~~~~~
tmpl03.cpp:5:22: note:   template argument deduction/substitution failed:
tmpl03.cpp:11:11: note:   deduced conflicting types for parameter ‘T’ (‘int’ and ‘double’)
   11 |     max_of(1, 2.0);          // 1. int 와 double
      |     ~~~~~~^~~~~~~~
tmpl03.cpp:12:9: error: no matching function for call to ‘make()’
   12 |     make();                  // 2. 인자 없이
      |     ~~~~^~
tmpl03.cpp:6:22: note: candidate: ‘template<class T> T make()’
    6 | template <class T> T make() { return T{}; }
      |                      ^~~~
tmpl03.cpp:6:22: note:   template argument deduction/substitution failed:
tmpl03.cpp:12:9: note:   couldn’t deduce template parameter ‘T’
   12 |     make();                  // 2. 인자 없이
      |     ~~~~^~
tmpl03.cpp:13:9: error: no matching function for call to ‘take(<brace-enclosed initializer list>)’
   13 |     take({1, 2, 3});         // 3. 중괄호 목록
      |     ~~~~^~~~~~~~~~~
tmpl03.cpp:7:25: note: candidate: ‘template<class T> void take(T)’
    7 | template <class T> void take(T) {}
      |                         ^~~~
tmpl03.cpp:7:25: note:   template argument deduction/substitution failed:
tmpl03.cpp:13:9: note:   couldn’t deduce template parameter ‘T’
   13 |     take({1, 2, 3});         // 3. 중괄호 목록
      |     ~~~~^~~~~~~~~~~
tmpl03.cpp:14:10: error: no matching function for call to ‘exact(int)’
   14 |     exact(1);                // 4. type_identity_t<T> 매개변수
      |     ~~~~~^~~
tmpl03.cpp:8:25: note: candidate: ‘template<class T> void exact(std::type_identity_t<T>)’
    8 | template <class T> void exact(std::type_identity_t<T>) {}
      |                         ^~~~~
tmpl03.cpp:8:25: note:   template argument deduction/substitution failed:
tmpl03.cpp:14:10: note:   couldn’t deduce template parameter ‘T’
   14 |     exact(1);                // 4. type_identity_t<T> 매개변수
      |     ~~~~~^~~
tmpl03.cpp:15:17: error: no matching function for call to ‘make()’
   15 |     int n = make();          // 5. int 변수로 받는다
      |             ~~~~^~
tmpl03.cpp:6:22: note: candidate: ‘template<class T> T make()’
    6 | template <class T> T make() { return T{}; }
      |                      ^~~~
tmpl03.cpp:6:22: note:   template argument deduction/substitution failed:
tmpl03.cpp:15:17: note:   couldn’t deduce template parameter ‘T’
   15 |     int n = make();          // 5. int 변수로 받는다
      |             ~~~~^~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 tmpl03.cpp -o ex (cc exit=1) =====
tmpl03.cpp:11:5: error: no matching function for call to 'max_of'
   11 |     max_of(1, 2.0);          // 1. int 와 double
      |     ^~~~~~
tmpl03.cpp:5:22: note: candidate template ignored: deduced conflicting types for parameter 'T' ('int' vs. 'double')
    5 | template <class T> T max_of(T a, T b) { return a < b ? b : a; }
      |                      ^
tmpl03.cpp:12:5: error: no matching function for call to 'make'
   12 |     make();                  // 2. 인자 없이
      |     ^~~~
tmpl03.cpp:6:22: note: candidate template ignored: couldn't infer template argument 'T'
    6 | template <class T> T make() { return T{}; }
      |                      ^
tmpl03.cpp:13:5: error: no matching function for call to 'take'
   13 |     take({1, 2, 3});         // 3. 중괄호 목록
      |     ^~~~
tmpl03.cpp:7:25: note: candidate template ignored: couldn't infer template argument 'T'
    7 | template <class T> void take(T) {}
      |                         ^
tmpl03.cpp:14:5: error: no matching function for call to 'exact'
   14 |     exact(1);                // 4. type_identity_t<T> 매개변수
      |     ^~~~~
tmpl03.cpp:8:25: note: candidate template ignored: couldn't infer template argument 'T'
    8 | template <class T> void exact(std::type_identity_t<T>) {}
      |                         ^
tmpl03.cpp:15:13: error: no matching function for call to 'make'
   15 |     int n = make();          // 5. int 변수로 받는다
      |             ^~~~
tmpl03.cpp:6:22: note: candidate template ignored: couldn't infer template argument 'T'
    6 | template <class T> T make() { return T{}; }
      |                      ^
5 errors generated.
```

**왜 그런가**

- ★★★ **1. 두 인자가 `T` 를 다르게 말하면 추론은 실패**한다 — 변환은 추론 **뒤**의 일이다(8번).
- ★★★ **2. · 5. 추론은 호출의 인자에서만** — 반환 타입도, 받는 변수의 타입도 재료가 아니다.
- ★★ **3. 중괄호 목록은 타입이 없는 식**이라 `T` 로 추론되지 않는다 · **4. `type_identity_t<T>` 는 비추론 문맥**이다.

### 4. ★★ **네 줄 다 통과** · `take` 안의 `T` 는 **`std::initializer_list<int>`**, `exact` 안의 `T` 는 **`long`**(g++ 는 `long int` 로 적는다) · `il` 은 **`std::initializer_list<int>`**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic tmpl04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
max_of<double>(1, 2.0) = 2.0
make<int>() = 0
take<std::initializer_list<int>>({1, 2, 3})
  T inside take                              std::initializer_list<int>
exact<long>(1)
  T inside exact                             long int
auto il = {1, 2, 3};  decltype(il)           std::initializer_list<int>
===== clang++ -std=c++20 -Wall -Wextra -pedantic tmpl04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
max_of<double>(1, 2.0) = 2.0
make<int>() = 0
take<std::initializer_list<int>>({1, 2, 3})
  T inside take                              std::initializer_list<int>
exact<long>(1)
  T inside exact                             long
auto il = {1, 2, 3};  decltype(il)           std::initializer_list<int>
```

**왜 그런가**

- ★★★ **`T` 를 적으면 추론할 것이 없고**, 인자는 적힌 타입으로 **변환**된다(`1` → `double`·`long`).
- ★★ **`auto` 는 중괄호 목록을 `initializer_list` 로 받는다** — 3번의 3. 과 갈리는 자리다.

### 5. ★★★ **1 · 2 · 2** — 두 컴파일러 같다

**출력**

```text
===== bash tmpl-inst.sh (exit=0) =====
g++      by_value 1개 · by_ref 2개 · by_fwd 2개
clang++  by_value 1개 · by_ref 2개 · by_fwd 2개
 W void by_fwd<int const&>(int const&)
 W void by_fwd<int&>(int&)
 W void by_ref<int const>(int const&)
 W void by_ref<int>(int&)
 W void by_value<int>(int)
```

**왜 그런가**

- ★★★ **값 매개변수는 네 인자를 전부 `T = int` 로** 만든다 — 한 벌.
- ★★ **`by_ref` 는 `int` · `int const`**(`const` 가 `T` 에 남는다), **`by_fwd` 는 `int&` · `int const&`**(lvalue 넷이 두 모양).

### 6. ★★ **`E0308` · `E0283`** · 아무 cfg 도 없는 판은 **통과**(`make() -> 0`) — Rust 는 **받는 쪽 타입에서도** 추론한다

**출력**

```text
===== rustc --edition 2021 --cfg mixed infer.rs -o irx (cc exit=1) =====
error[E0308]: mismatched types
  --> infer.rs:12:23
   |
12 |     let m = max_of(1, 2.0);
   |             ------ -  ^^^ expected integer, found floating-point number
   |             |      |
   |             |      expected all arguments to be this integer type because they need to match the type of this parameter
   |             arguments to this function are incorrect
   |
help: the return type of this call is `{float}` due to the type of the argument passed
  --> infer.rs:12:13
   |
12 |     let m = max_of(1, 2.0);
   |             ^^^^^^^^^^---^
   |                       |
   |                       this argument influences the return type of `max_of`
note: function defined here
  --> infer.rs:2:4
   |
 2 | fn max_of<T: PartialOrd>(a: T, b: T) -> T {
   |    ^^^^^^ -              ----  ---- this parameter needs to match the integer type of `a`
   |           |              |
   |           |              `b` needs to match the integer type of this parameter
   |           `a` and `b` both reference this parameter `T`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

```text
===== rustc --edition 2021 --cfg bare infer.rs -o irx (cc exit=1) =====
error[E0283]: type annotations needed
  --> infer.rs:14:9
   |
14 |     let m = make();
   |         ^   ------ type must be known at this point
   |
   = note: cannot satisfy `_: Default`
note: required by a bound in `make`
  --> infer.rs:6:12
   |
 6 | fn make<T: Default>() -> T {
   |            ^^^^^^^ required by this bound in `make`
help: consider giving `m` an explicit type
   |
14 |     let m: /* Type */ = make();
   |          ++++++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0283`.
```

```text
===== rustc --edition 2021 infer.rs -o irx && ./irx (cc exit=0 · run exit=0) =====
make() -> 0 · max_of(1, 2) -> 2
```

**왜 그런가**

- ★★★ **C++ 은 호출의 인자에서만 `T` 를 정한다** — `int n = make();` 의 `int` 는 추론 재료가 아니다.
- ★★ **Rust 는 식 전체의 타입 제약을 모아 푼다** — `let m: i64` 가 `make::<i64>` 를 정한다. 재료가 없으면(`let m = make();`) C++ 처럼 멈춘다.

### 7. ★★★ **`T&` 는 인자 전체가 `T` 에 묶여 `const` 가 `T` 의 일부**가 되고, **`const T&` 는 틀이 이미 `const` 를 가져 `T` 에는 나머지만** 남는다 · 그래서 `T&` 로 받은 `const` 인자는 **함수 안에서도 수정할 수 없다**

- ★★★ `by_ref(ci)` 의 매개변수는 `const int&` — `T&` 로 적었어도 **`const` 를 벗길 수 없다.** 5번의 `by_ref<int const>` 가 그 인스턴스다.

### 8. ★★★ **추론 단계에는 변환이 없다** — `T` 를 정한 **뒤에야** 인자를 매개변수로 변환한다. 01편의 오버로드 해석은 **이미 타입이 정해진 후보들 사이에서** 변환의 순위를 따진다

- ★★★ 그래서 `max_of(1, 2.0)` 은 후보 `max_of<?>` 를 **만들지도 못한다** — clang 의 `candidate template ignored` 가 그 말이다.
- ★★ 명시 지정 `max_of<double>` 을 쓰면 후보가 먼저 정해지고, 그때 `1` 이 **변환**된다(4번).

### 9. ★★★ **아무것도 알려 주지 않는다** — 경고 0 · `cc exit=0` · 실행도 멀쩡하다. 그래서 **`T` 를 직접 묻는 탐침**이 필요하다

- ★★★ 2번 격자는 **24칸 모두 경고 0** 으로 컴파일됐다 — 배열이 `int*` 가 되어 **크기를 잃은 칸**도.
- ★★ 뜻밖의 성공은 **나중에 다른 자리에서**(`sizeof`·오버로드 선택) 드러난다 — 원인과 증상이 멀어진다.

### 10. ★★ **`T` 자체는 표준, 철자는 구현** · `__PRETTY_FUNCTION__` 은 **표준 식별자가 아니다** — `-pedantic` 은 **경고 0** 이었다

- ★★ 두 컴파일러가 **같은 `T`** 를 낸 것은 규칙이 같기 때문이고, **다른 철자**는 각자가 타입을 문자열로 바꾸는 방식이다.
- ★ `-pedantic` 이 조용한 것은 **구현이 미리 정의한 이름**이라서다 — ill-formed 가 아니다.

### 11. 다른 주제와 잇기

- ★★ **`int arr[3]` 행의 `T` 칸(`int*`)과 `T&` 칸(`int[3]` → 매개변수 `int (&)[3]`)** — `auto` 는 `T`, `auto&` 는 `T&` 와 같은 규칙이다.
- ★ **인스턴스는 `T` 가 같으면 하나**다 — 09편은 `T = int` 가 두 번 나와 **에러가 한 번만** 났고, 이 편은 호출 넷이 **기호 하나**가 됐다.
- ★ **TS 갈래** — [TS 21번](../../../ts/syntax/21-inference-control-const-and-noinfer/)의 `const probe: null = 무엇인가;`.

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `tmpl01.cpp` 탐침 | 두 컴파일러 | ★★★ **`int` · `const char*`** · 에러 2 · 2 |
| `tmpl02.cpp` + `tmpl-grid.sh` | 두 컴파일러 × 24칸 | ★★★ **다른 칸 0 / 24** · `&` 6 · `*` 3 |
| `tmpl03.cpp` 실패 | 두 컴파일러 | ★★★ **다섯 줄 · 각 5건** |
| `tmpl04.cpp` 명시 지정 | 두 컴파일러 | ★★ **전부 통과** · `long int` 대 `long` |
| `tmpl05.cpp` + `tmpl-inst.sh` | 두 컴파일러 `nm -C` | ★★ **1 · 2 · 2** |
| `infer.rs` | 세 판 | ★★ **E0308 · E0283 · 통과** |

**구현 의존 항목** — 다음은 **이 환경(g++ 13 · clang 18)에서만** 그렇다.

- ★★ **`__PRETTY_FUNCTION__` 의 모양과 철자** · **진단 문구**(`couldn’t deduce` 대 `couldn't infer`) · **기호 이름의 철자**(`int const`).

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **24칸의 `T`** · **추론이 멈추는 다섯 자리** · **명시 지정** · **`auto` 의 중괄호 목록** · **`T` 가 같으면 인스턴스 하나.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **부분 순서(여러 템플릿 중 고르기)** · ★ **매개변수 둘(`T`, `U`)로 1. 풀기** · ★ **컨셉·CTAD**(목록의 **32번 주제** · 목록의 **36번 주제**).
- ★ **「부적용인 창」** — ASan · 경고 격자.
- ★ **cppreference 의 추론 쪽을 이 배치에서 열지 않았다** — 규칙은 **컴파일러가 말한 `T`** 로만 적었다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **4번** — `long int` 대 `long` 같은 철자(흔들리는 칸)가 바뀌어도 규칙은 그대로인지.
- ★ **3번** — 진단 문구.
