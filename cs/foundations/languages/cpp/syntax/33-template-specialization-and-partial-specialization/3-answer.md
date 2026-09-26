# cpp/syntax/33 — 특수화와 부분 특수화 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · GNU nm 2.42 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 소스는 질문 파일과 같다(출력 블록의 배너에 파일 이름이 있다). 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **진단 문구 · 열 번호 · `std::_Bit_reference` 라는 이름**이다.\
> 근거로 쓰는 것은 다음이다 — **`cc exit` · 격자 칸 · 「갈린 칸 N / M」 · 실행 출력 · `nm` 의 글자와 기호 이름 · `is_reference` 의 0/1**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **`int`→`<int>` · `int*`→`<T*>` · `const int*`→`<T*>` · `int* const`→`<const T>` · `const int`→`<const T>` · `char[3]`→`<T[N]>` · `const char[3]`→error · `double`→기본 · `const int* const`→`<const T>`** — **갈린 칸 0 / 9 · error 1 / 9**

**출력**

```text
===== bash spec-grid.sh (exit=0) =====
인자	g++	clang++
int	full <int>	full <int>
int*	partial <T*>	partial <T*>
const int*	partial <T*>	partial <T*>
int* const	partial <const T>	partial <const T>
const int	partial <const T>	partial <const T>
char[3]	partial <T[N]>	partial <T[N]>
const char[3]	error	error
double	primary	primary
const int* const	partial <const T>	partial <const T>
g++ 대 clang++ 가 갈린 칸 0 / 9 · error 인 행 1 / 9
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic '-DARG=const char[3]' spec01.cpp -o ex (cc exit=1) =====
spec01.cpp: In function ‘int main()’:
spec01.cpp:12:24: error: ambiguous template instantiation for ‘struct Pick<const char [3]>’
   12 |     std::puts(Pick<ARG>::which);
      |                        ^~
spec01.cpp:8:27: note: candidates are: ‘template<class T> struct Pick<const T> [with T = char [3]]’
    8 | template <class T> struct Pick<const T> { static constexpr const char* which = "partial <const T>"; };
      |                           ^~~~~~~~~~~~~
spec01.cpp:9:42: note:                 ‘template<class T, long unsigned int N> struct Pick<T [N]> [with T = const char; long unsigned int N = 3]’
    9 | template <class T, std::size_t N> struct Pick<T[N]> { static constexpr const char* which = "partial <T[N]>"; };
      |                                          ^~~~~~~~~~
spec01.cpp:12:26: error: incomplete type ‘Pick<const char [3]>’ used in nested name specifier
   12 |     std::puts(Pick<ARG>::which);
      |                          ^~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic '-DARG=const char[3]' spec01.cpp -o ex (cc exit=1) =====
spec01.cpp:12:15: error: ambiguous partial specializations of 'Pick<const char[3]>'
   12 |     std::puts(Pick<ARG>::which);
      |               ^
spec01.cpp:8:27: note: partial specialization matches [with T = char[3]]
    8 | template <class T> struct Pick<const T> { static constexpr const char* which = "partial <const T>"; };
      |                           ^
spec01.cpp:9:42: note: partial specialization matches [with T = const char, N = 3]
    9 | template <class T, std::size_t N> struct Pick<T[N]> { static constexpr const char* which = "partial <T[N]>"; };
      |                                          ^
1 error generated.
```

**왜 그런가**

- ★★★ **맞는 특수화 중 가장 좁은 것 · 없으면 기본** — `double` 은 아무 특수화에도 안 맞는다.
- ★★★ **`const char[3]` 은 `<const T>`(`T = char[3]`)와 `<T[N]>`(`T = const char, N = 3`)에 다 맞고, 어느 쪽도 더 좁지 않다** — 두 컴파일러가 같은 두 후보를 적고 멈췄다.

### 2. ★★★ **받지 않는다 — 5행 선언에서 두 컴파일러 다 에러**(호출과 무관)

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic spec02.cpp -o ex (cc exit=1) =====
spec02.cpp:5:25: error: non-class, non-variable partial specialization ‘name<T*>’ is not allowed
    5 | template <class T> void name<T*>(T*) { std::puts("pointer"); }
      |                         ^~~~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic spec02.cpp -o ex (cc exit=1) =====
spec02.cpp:5:25: error: function template partial specialization is not allowed
    5 | template <class T> void name<T*>(T*) { std::puts("pointer"); }
      |                         ^   ~~~~
1 error generated.
```

**왜 그런가**

- ★★★ **부분 특수화는 클래스·변수 템플릿에만 있다** — g++ 문구가 그 범위를 그대로 적는다(`non-class, non-variable`).

### 3. ★★ **`primary` · `pointer overload` × 3**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic spec03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
primary
pointer overload
pointer overload
pointer overload
===== clang++ -std=c++20 -Wall -Wextra -pedantic spec03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
primary
pointer overload
pointer overload
pointer overload
```

**왜 그런가**

- ★★ **`f(T)` 와 `f(T*)` 가 둘 다 맞으면 더 좁은 `f(T*)`** — 오버로드는 해석에 **참가**하므로 부분 순서로 갈린다. `"hi"` 는 `T*` 꼴에서 감쇠해 맞는다.

### 4. ★★★ **기본 순서 `(c) f<>(int*)` · `-DSPEC_FIRST` `(b) f(T*)`** — 기호는 **`T void f<int>(int*)`** 대 **`T void f<int*>(int*)` + `W void f<int>(int*)`**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic spec04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(c) f<>(int*)
===== g++ -std=c++20 -Wall -Wextra -pedantic -DSPEC_FIRST spec04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(b) f(T*)
===== clang++ -std=c++20 -Wall -Wextra -pedantic spec04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(c) f<>(int*)
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DSPEC_FIRST spec04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(b) f(T*)
```

```text
===== bash spec-nm.sh (exit=0) =====
== g++ (기본 순서)
 T void f<int>(int*)
== g++ -DSPEC_FIRST
 T void f<int*>(int*)
 W void f<int>(int*)
== clang++ (기본 순서)
 T void f<int>(int*)
== clang++ -DSPEC_FIRST
 T void f<int*>(int*)
 W void f<int>(int*)
```

**왜 그런가**

- ★★★ **(c) 는 선언하는 순간 보이는 기본 템플릿 중 가장 좁은 것에 붙는다** — 기본 순서면 (b)(`T = int` → `f<int>`), `SPEC_FIRST` 면 (a)(`T = int*` → `f<int*>`).
- ★★★ **호출은 먼저 (a)·(b) 중 (b) 를 고르고, (b) 에 붙은 특수화만 본다** — `SPEC_FIRST` 판에서는 (b) 에 특수화가 없으니 (b) 의 암묵 인스턴스(`W f<int>`)가 불린다.

### 5. ★★ **`bool* pb = &vb[0];` 만 에러 — g++ 2건 · clang 2건**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic spec05.cpp -o ex (cc exit=1) =====
spec05.cpp: In function ‘int main()’:
spec05.cpp:9:21: error: taking address of rvalue [-fpermissive]
    9 |     bool* pb = &vb[0];
      |                 ~~~~^
spec05.cpp:9:16: error: cannot convert ‘std::vector<bool>::reference*’ to ‘bool*’ in initialization
    9 |     bool* pb = &vb[0];
      |                ^~~~~~
      |                |
      |                std::vector<bool>::reference*
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic spec05.cpp -o ex (cc exit=1) =====
spec05.cpp:9:16: error: taking the address of a temporary object of type 'reference' (aka 'std::_Bit_reference') [-Waddress-of-temporary]
    9 |     bool* pb = &vb[0];
      |                ^~~~~~
spec05.cpp:9:11: error: cannot initialize a variable of type 'bool *' with an rvalue of type 'reference *' (aka 'std::_Bit_reference *')
    9 |     bool* pb = &vb[0];
      |           ^    ~~~~~~
2 errors generated.
```

**왜 그런가**

- ★★ **`vb[0]` 은 `bool&` 이 아니라 `vector<bool>::reference` 라는 임시 대리 객체**다 — 임시의 주소는 못 얻고, 얻어도 `bool*` 가 아니다.

### 6. ★★ **`char` · `std::_Bit_reference` · `0` · `1`**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic spec06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
decltype(vc[0])                    char
decltype(vb[0])                    std::_Bit_reference
is_reference of decltype(vb[0])    0
is_reference of decltype(vc[0])    1
===== clang++ -std=c++20 -Wall -Wextra -pedantic spec06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
decltype(vc[0])                    char
decltype(vb[0])                    std::_Bit_reference
is_reference of decltype(vb[0])    0
is_reference of decltype(vc[0])    1
```

**왜 그런가**

- ★★ **`vector<char>::operator[]` 는 참조(`is_reference` 1), `vector<bool>` 은 값(0)** — 표준 라이브러리가 `vector<bool>` 을 **특수화**해 비트로 담기 때문이다.
- ★ `decltype(vc[0])` 이 `char` 로 찍힌 것은 **`typeid` 가 참조를 떼기** 때문이다 — 그래서 `is_reference` 를 따로 물었다.

### 7. ★★★ **`const int*` 는 「`const int` 를 가리키는 포인터」라 `T*` 꼴에 `T = const int` 로 맞고, `int* const` 는 「`const` 인 포인터」라 `const T` 꼴에 `T = int*` 로 맞는다**

- ★★ `const` 가 **가리키는 쪽**에 붙었나 **포인터 자체**에 붙었나가 꼴을 가른다.

### 8. ★★★ **특수화는 오버로드 해석의 후보 목록에 들어가지 않는다** — 후보는 **비템플릿과 기본 템플릿**뿐이고, 고른 **기본 템플릿에 붙은** 특수화만 그다음에 본다. `SPEC_FIRST` 판의 (c) 는 **고르지 않은 (a)** 에 붙어 있었다

- ★ cppreference — 「The specializations are not overloads and are not considered.」

### 9. ★★ **실행 출력은 「무엇이 불렸나」만 말하고, 「(c) 가 어느 기본 템플릿의 특수화인가」는 말하지 않는다** — 기호 이름의 템플릿 인자(`f<int>` 대 `f<int*>`)가 그것을 말했다

- ★★ `SPEC_FIRST` 판에서는 (c) 가 **정의되고도 안 불린 `T f<int*>`** 로, 불린 쪽은 **암묵 인스턴스 `W f<int>`** 로 따로 보였다.

### 10. ★★ **달라지지 않는다 — 순서를 바꾼 판(`spec07.cpp`)도 두 컴파일러 다 같은 모호 에러** · 4번은 **함수 템플릿의 특수화가 선언 시점에 보이는 기본 템플릿에 붙는** 문제라 순서가 들어간다

```cpp
/* spec07.cpp */
// spec01.cpp 의 두 부분 특수화 <const T> 와 <T[N]> 의 선언 순서만 바꾼 판
#include <cstddef>
#include <cstdio>

template <class T> struct Pick { static constexpr const char* which = "primary"; };
template <> struct Pick<int> { static constexpr const char* which = "full <int>"; };
template <class T> struct Pick<T*> { static constexpr const char* which = "partial <T*>"; };
template <class T, std::size_t N> struct Pick<T[N]> { static constexpr const char* which = "partial <T[N]>"; };
template <class T> struct Pick<const T> { static constexpr const char* which = "partial <const T>"; };

int main() {
    std::puts(Pick<ARG>::which);
}
```

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic '-DARG=const char[3]' spec07.cpp -o ex 2>&1 | grep ': error: ' (cc exit=1) =====
spec07.cpp:12:24: error: ambiguous template instantiation for ‘struct Pick<const char [3]>’
spec07.cpp:12:26: error: incomplete type ‘Pick<const char [3]>’ used in nested name specifier
===== clang++ -std=c++20 -Wall -Wextra -pedantic '-DARG=const char[3]' spec07.cpp -o ex 2>&1 | grep ': error: ' (cc exit=1) =====
spec07.cpp:12:15: error: ambiguous partial specializations of 'Pick<const char[3]>'
```

- ★★ **클래스 템플릿의 특수화 선택은 순서가 아니라 좁음으로만 한다** — 두 부분 특수화는 **둘 다 기본 템플릿 `Pick` 의 것**이라 「어디에 붙나」가 순서에 달리지 않는다.

### 11. 다른 주제와 잇기

- ★★ **31편 (2)의 `T` 열 `"hi"` → `const char*`** — 배열이 포인터로 감쇠하는 칸이다. 여기서는 틀이 `T*` 라 `T = const char`.
- ★ **특정 인자의 구현을 손으로 바꿔 끼울 수 있다** — C# 제네릭은 특수화가 없고 참조 타입 인자는 코드를 공유한다(C# 갈래 [24번](../../../csharp/syntax/24-generics-and-type-parameters/) (4)).

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `spec01.cpp` + `spec-grid.sh` | 인자 9 × 컴파일러 2 | ★★★ **갈린 칸 0 / 9 · error 1 / 9** |
| `spec01.cpp` `const char[3]` | 두 컴파일러 | ★★ **모호 — 같은 후보 둘** |
| `spec02.cpp` | 두 컴파일러 | ★★★ **선언에서 거절** |
| `spec03.cpp` | 두 컴파일러 | ★★ **`primary` · `pointer overload` × 3** |
| `spec04.cpp` + `spec-nm.sh` | 두 컴파일러 × 순서 2 | ★★★ **`(c)` → `(b)` · `f<int>` → `f<int*>` + `f<int>`** |
| `spec07.cpp` 순서 바꾼 판 | 두 컴파일러 | ★★ **같은 모호 에러** |
| `spec05.cpp` · `spec06.cpp` | 두 컴파일러 | ★★ **`&vb[0]` 에러 · `is_reference` 0** |

**구현 의존 항목** — 다음은 **이 환경(g++ 13 · clang 18 · libstdc++ 13)에서만** 그렇다.

- ★★ **진단 문구** · **`std::_Bit_reference` 라는 이름**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **격자 9칸** · **모호면 에러** · **함수 부분 특수화 금지** · **특수화는 오버로드 해석 밖** · **`vector<bool>::reference` 는 참조가 아니다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **변수 템플릿 부분 특수화** · **첫 사용 뒤의 특수화** · **보통 함수 오버로드로 (3) 풀기**.
- ★ **「부적용인 창」** — ASan · 경고 격자.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★ **5번** — 진단 문구 · **6번** — 라이브러리 내부 이름.
