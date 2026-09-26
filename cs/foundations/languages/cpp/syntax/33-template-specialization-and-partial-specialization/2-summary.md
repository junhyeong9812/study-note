# cpp/syntax/33 — 특수화와 부분 특수화 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 명시적(전체) 특수화](https://en.cppreference.com/w/cpp/language/template_specialization) · [cppreference — 부분 특수화](https://en.cppreference.com/w/cpp/language/partial_specialization) · [cppreference — 함수 템플릿](https://en.cppreference.com/w/cpp/language/function_template)\
> ★ 이 배치에서 **위 cppreference 세 쪽을 열어 확인했다** — 「여러 부분 특수화가 맞으면 더 특수한 것, 유일하지 않으면 컴파일할 수 없다」 · 「부분 특수화는 클래스·변수 템플릿용」 · 「**오버로드 해석에는 비템플릿과 기본 템플릿만 참가하고, 특수화는 오버로드가 아니라 고려되지 않는다**」 세 문장이다. **값은 전부 두 컴파일러에게 던져 얻었다.**
> **실행 검증** — 이 문서의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **libstdc++ 13**(두 컴파일러 공용) · GNU nm 2.42 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고, 블록마다 **소스 파일 이름이 다르다**(`spec01.cpp` \~ `spec06.cpp` · `spec-grid.sh` · `spec-nm.sh`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. 소스 펜스의 배너도 **캡처가 찍은 것**이다.
> **버전** — 클래스 템플릿의 전체·부분 특수화, 함수 템플릿의 전체 특수화는 **C++98부터**다. 기준은 **C++20**이다(이 편의 코드는 판에 따라 결론이 갈리지 않는다 — 판 격자는 돌리지 않았다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★★ **[32번](../32-class-templates-and-ctad/)에서 온다** — 32편 (1)의 클래스 템플릿 정의 · (6)의 「`nm -C` 의 `W` 는 암묵 인스턴스」를 그대로 쓴다.\
> [31번](../31-function-templates-and-argument-deduction/) (2) — **`T*` 꼴은 `const int*` 를 받아 `T = const int`** 로 만든다(`T` 열·`T&` 열의 `const` 처리) · [01번](../01-function-overloading-and-overload-resolution/) — 오버로드 해석의 순서.\
> ★★ **여기서 새로 묻는 것은 넷이다** — **어느 특수화가 골라지나 격자(인자 9 × 컴파일러 2)** · **함수 템플릿에 부분 특수화를 쓰면** · **특수화와 오버로드를 섞으면 선언 순서가 결과를 바꾸는 것** · **`std::vector<bool>` 이 특수화라서 생기는 일.**
> **경계** — 「특수화를 고르는 부분 순서의 형식 규칙」은 이 편이 **격자로만** 보인다(조항을 옮기지 않았다). 「조건으로 오버로드를 끄는 법(SFINAE·컨셉)」은 목록의 **37번 주제**·목록의 **36번 주제**, 「`vector` 선택 기준」은 목록의 **41번 주제**가 정본이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단의 **문구**(`ambiguous template instantiation` 대 `ambiguous partial specializations`) · **열 번호** | ★★★ **`cc exit`** · **격자 칸에 찍힌 판 이름**(소스의 문자열이다) · **「갈린 칸 N / M」** |
> | ★ **`std::_Bit_reference`** — libstdc++ 가 붙인 이름이다 | ★★★ **실행 출력 `(b)`·`(c)`** · **`nm` 의 글자**(`T`·`W`)와 **기호 이름**(`f<int>` 대 `f<int*>`) |
> | — | ★★ **`is_reference` 가 0 인가 1 인가** |

## 한눈에 — 쉽게 말하면

**특수화는 「기본 메뉴판 옆에 붙인 특별 메뉴」다.**

기본 템플릿이 **모든 손님용 메뉴**라면, 특수화는 「**이런 손님에게는 이 메뉴**」를 따로 붙인 것이다.

- **전체 특수화** `<int>` — 「**`int` 손님 한 명**」 전용 메뉴.
- **부분 특수화** `<T*>` — 「**포인터 손님 모두**」 전용 메뉴. 손님 중 **한 무리**를 고른다.
- **두 특별 메뉴가 같은 손님을 부르면**(`const char[3]` 은 `const` 이면서 배열이다) — 어느 쪽이 더 좁은지 가릴 수 없으면 **주문을 안 받는다**((1)).
- ★★★ **함수 템플릿은 「무리 전용 메뉴」를 못 붙인다** — 대신 **메뉴판을 하나 더** 건다(오버로드)((2)).
- ★★★ **그리고 함수의 특별 메뉴는 메뉴판을 고른 뒤에야 본다** — 메뉴판(기본 템플릿)을 먼저 고르고, **그 메뉴판에 붙은** 특별 메뉴만 본다((3)).

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 기본 메뉴판 | ★★ **기본 템플릿(primary template)** | (1) |
| 한 손님 전용 | ★★ **전체 특수화 `template <> struct Pick<int>`** | (1) |
| 한 무리 전용 | ★★★ **부분 특수화 `Pick<T*>` · `Pick<const T>` · `Pick<T[N]>`** | (1) |
| 두 특별 메뉴가 같은 손님 | ★★★ **`ambiguous` 에러** | (1) |
| 메뉴판을 하나 더 건다 | ★★★ **함수 템플릿 오버로드 `f(T*)`** | (2) |
| 메뉴판을 먼저 고른다 | ★★★ **특수화는 오버로드 해석에 참가하지 않는다** | (3) |
| 표준이 붙인 특별 메뉴 | ★★ **`std::vector<bool>`** | (4) |

```text
   클래스 템플릿                                  함수 템플릿
   Pick<T>      기본                             f(T)        기본 템플릿 (a)
   Pick<int>    전체 특수화          ○           f<>(int*)   전체 특수화 (c)       ○
   Pick<T*>     부분 특수화          ○           f<T*>(T*)   부분 특수화           ★ ×  에러
                                                 f(T*)       또 하나의 기본 템플릿 (b)  ← 오버로드로 푼다

   ★ 함수 쪽 순서: ① 기본 템플릿 (a)(b) 중에서 고른다 → ② 고른 것에 붙은 특수화만 본다
```

## 이 주제가 답하려는 질문

1. ★★★ **인자 타입마다 어느 판이 골라지나** — 전체·부분 넷·기본, 그리고 **둘이 맞으면**((1)).
2. ★★★ **함수 템플릿에서 「포인터면 따로」를 어떻게 쓰나** — 부분 특수화가 안 되니 오버로드로((2)).
3. ★★★ **함수 템플릿의 특수화와 오버로드를 섞으면** — 선언 순서가 결과를 바꾸는 자리((3)).
4. ★★ **표준 라이브러리의 특수화가 코드를 깨는 자리** — `vector<bool>`((4)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ② 두 컴파일러에게 「어느 판을 골랐나」를 묻는 것이다

★★★ **이 주제의 본체는 ② 두 컴파일러 대조다** — 판마다 **다른 문자열**을 심어 두고 **실행 출력**으로 어느 판이 골라졌는지 읽는다. 에러가 나는 칸은 에러 전문으로.\
★★ **짝이 ④ 대신 기호표(`nm -C`)** 다 — (3)에서 **전체 특수화가 어느 기본 템플릿에 붙었나**는 실행 출력으로는 「무엇이 불렸나」만 보이고, **기호 이름**(`f<int*>` 대 `f<int>`)에서야 보인다(제5의 상태 — 창을 바꿔 답했다).

```text
① 다섯 층 표            고르는 규칙은 표준 · _Bit_reference 이름은 구현             (구현 세부사항 절)
② ★ 두 컴파일러 대조     인자 9 × 컴파일러 2 · 모호 에러 · 부분 특수화 에러           (1)(2)(4)
③ ASan                   —                                                          부적용
④ 어셈블리 → 기호표      nm -C 로 특수화가 붙은 자리 f<int*> 대 f<int>               (3)
⑤ 경고 격자             —                                                          부적용
⑥ <type_traits>·<cxxabi.h> is_reference · __cxa_demangle                          (4)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 다섯 층 표 | ★★ **고르는 규칙은 표준, `std::_Bit_reference` 라는 이름은 libstdc++** | **쓴다** |
| ★★★ **② 두 컴파일러 대조** | ★★★ **본체** — 인자 9칸 중 **갈린 칸 0 / 9 · error 1 / 9** | **쓴다** |
| ③ ASan | ★ **부적용** — 판 고르기는 **컴파일 때 끝난다**(18-B) | **안 쓴다** |
| ★★ **④ → 기호표** | ★★★ `T void f<int*>(int*)` · `W void f<int>(int*)` — **실행 출력이 못 보는 「어디에 붙었나」**(제5의 상태) | **쓴다(바꿔서)** |
| ⑤ 경고 격자 | ★ **부적용** — 통과한 칸은 **경고 0**((2)(3)(4) 배너 · 진단 0줄). 격자 스크립트는 진단을 **보지 않는다**(`2>/dev/null`) | **안 쓴다** |
| ★ ⑥ 타입 도구 | ★★ **`std::is_reference`** — `vb[0]` 이 참조가 **아니다**((4)) | **쓴다** |

### (1) ★★★ 어느 판이 골라지나 — 인자 9 × 컴파일러 2

**언제 쓰나** — 특수화를 둘 이상 둔 클래스 템플릿에서 「이 타입이면 어느 것」을 정할 때.

```cpp
/* spec01.cpp */
// 기본 템플릿 하나 + 특수화 넷. 인자 타입 하나를 -DARG=… 로 골라 어느 판이 골라졌는지 찍는다
#include <cstddef>
#include <cstdio>

template <class T> struct Pick { static constexpr const char* which = "primary"; };
template <> struct Pick<int> { static constexpr const char* which = "full <int>"; };
template <class T> struct Pick<T*> { static constexpr const char* which = "partial <T*>"; };
template <class T> struct Pick<const T> { static constexpr const char* which = "partial <const T>"; };
template <class T, std::size_t N> struct Pick<T[N]> { static constexpr const char* which = "partial <T[N]>"; };

int main() {
    std::puts(Pick<ARG>::which);
}
```

```bash
# spec-grid.sh
# spec-grid.sh — 인자 타입 9개 × 컴파일러 둘. 칸마다 골라진 판 또는 error
args=('int' 'int*' 'const int*' 'int* const' 'const int' 'char[3]' 'const char[3]' 'double' 'const int* const')
cell() {  # $1 컴파일러 $2 인자 타입
  if $1 -std=c++20 -Wall -Wextra -pedantic "-DARG=$2" spec01.cpp -o gx 2>/dev/null; then ./gx; else echo error; fi
}
printf '%s\t%s\t%s\n' "인자" "g++" "clang++" > grid.tsv
for a in "${args[@]}"; do
  printf '%s\t%s\t%s\n' "$a" "$(cell g++ "$a")" "$(cell clang++ "$a")" >> grid.tsv
done
cat grid.tsv
bad=$(awk -F'\t' 'NF != 3' grid.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
rows=$(( $(wc -l < grid.tsv) - 1 ))
split=$(tail -n +2 grid.tsv | awk -F'\t' '$2 != $3' | wc -l)
err=$(tail -n +2 grid.tsv | awk -F'\t' '$2 == "error"' | wc -l)
echo "g++ 대 clang++ 가 갈린 칸 $split / $rows · error 인 행 $err / $rows"
rm -f gx grid.tsv
```

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

- ★★★ **갈린 칸 0 / 9 · error 1 / 9** — 두 컴파일러가 **같은 판을 골랐고, 같은 한 칸에서 멈췄다.**
- ★★★ **`int` → 전체 `<int>`** · **`double` → 기본** — 맞는 특수화가 없으면 기본 템플릿이다.
- ★★★ **`const int*` → `<T*>`**(`T = const int` — 포인터가 가리키는 쪽의 `const` 는 **`T` 안**에 들어간다) · **`int* const` → `<const T>`**(`T = int*` — **포인터 자체가 `const`** 라 「`T*`」 꼴이 아니다) · **`const int* const` → `<const T>`**.
- ★★ **`const int` → `<const T>`** — 전체 특수화 `<int>` 는 **`int` 하나에만** 맞는다. `const int` 는 다른 타입이다.
- ★★★ **`const char[3]` → error** — 아래 블록.

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

- ★★★ **`const char[3]` 은 두 부분 특수화에 다 맞는다** — `<const T>` 에 `T = char[3]` 으로, `<T[N]>` 에 `T = const char, N = 3` 으로. **어느 쪽도 다른 쪽보다 좁지 않아** 두 컴파일러 다 멈췄다(g++ `ambiguous template instantiation` · clang `ambiguous partial specializations`). ★ **두 컴파일러가 후보 둘을 같은 짝으로** 적는다.\
  ★ cppreference — 「더 특수한 것이 유일하지 않으면 **the program cannot be compiled**」.
- ★ g++ 는 에러가 **2건**이다 — 모호해서 `Pick<const char [3]>` 이 **불완전 타입**으로 남고, 그 `::which` 를 읽는 자리가 한 번 더 깨졌다.

★★ **두 부분 특수화의 선언 순서를 바꾸면** —

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

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic '-DARG=const char[3]' spec07.cpp -o ex 2>&1 | grep ': error: ' (cc exit=1) =====
spec07.cpp:12:24: error: ambiguous template instantiation for ‘struct Pick<const char [3]>’
spec07.cpp:12:26: error: incomplete type ‘Pick<const char [3]>’ used in nested name specifier
===== clang++ -std=c++20 -Wall -Wextra -pedantic '-DARG=const char[3]' spec07.cpp -o ex 2>&1 | grep ': error: ' (cc exit=1) =====
spec07.cpp:12:15: error: ambiguous partial specializations of 'Pick<const char[3]>'
```

- ★★ **같은 모호 에러** — 클래스 템플릿의 특수화 선택은 **순서가 아니라 좁음**으로만 한다. (3)의 함수 쪽과 대비된다.

```text
   인자              맞는 판                           고른 판
   int               기본 · <int>                      <int>          ★ 전체가 가장 좁다
   int*              기본 · <T*>(T=int)                <T*>
   const int*        기본 · <T*>(T=const int)          <T*>           ★ 가리키는 쪽 const
   int* const        기본 · <const T>(T=int*)          <const T>      ★ 포인터 자체 const
   char[3]           기본 · <T[N]>                     <T[N]>
   const char[3]     기본 · <const T> · <T[N]>         ★ 모호 — 에러
   double            기본                              기본
```

### (2) ★★★ 함수 템플릿에 부분 특수화를 쓰면 — 그리고 오버로드로 푼다

**언제 쓰나** — 「포인터를 받으면 다르게」를 함수 템플릿에서 하고 싶을 때.

```cpp
/* spec02.cpp */
// 함수 템플릿에 부분 특수화를 시도한다
#include <cstdio>

template <class T> void name(T) { std::puts("primary"); }
template <class T> void name<T*>(T*) { std::puts("pointer"); }

int main() {
    int i = 0;
    name(&i);
}
```

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

- ★★★ **g++ `non-class, non-variable partial specialization ‘name<T*>’ is not allowed` · clang `function template partial specialization is not allowed`** — 두 컴파일러 다 **선언 자체**를 거절한다(호출과 무관하게 5행).
- ★ g++ 문구가 **범위를 적는다** — 「클래스도 변수도 아닌」. 부분 특수화는 **클래스 템플릿과 변수 템플릿(C++14)** 에만 있다(cppreference 부분 특수화 쪽의 첫 문장과 같다).

**같은 의도를 오버로드로** —

```cpp
/* spec03.cpp */
// 같은 의도를 오버로드로 — 두 번째 함수 템플릿을 하나 더 선언한다
#include <cstdio>

template <class T> void name(T) { std::puts("primary"); }
template <class T> void name(T*) { std::puts("pointer overload"); }

int main() {
    int i = 0;
    const int ci = 0;
    name(i);
    name(&i);
    name(&ci);
    name("hi");
}
```

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

- ★★★ **`name(T*)` 를 또 하나의 기본 템플릿으로** 두면 된다 — `&i` · `&ci` · `"hi"` 가 전부 `pointer overload`. **둘 다 맞을 때 더 특수한 쪽**(`T*`)이 이긴다(부분 순서).
- ★★ **`"hi"` 도 `pointer overload`** — `T*` 꼴이 배열 `const char[3]` 을 **감쇠시켜** 받는다(31편 (2)의 `T` 열과 같은 감쇠, 이번엔 틀이 `T*`).

### (3) ★★★ 특수화 + 오버로드 — 선언 순서가 결과를 바꾼다

**언제 쓰나** — 함수 템플릿에 **전체 특수화**를 붙일 일이 생길 때마다. **이 절이 이 주제의 가장 비싼 함정이다.**

```cpp
/* spec04.cpp */
// 선언 세 개 — 기본 템플릿 (a), 포인터 오버로드 (b), int* 전체 특수화 (c).
// -DSPEC_FIRST 이면 (c) 를 (b) 보다 앞에 둔다
#include <cstdio>

template <class T> void f(T) { std::puts("(a) f(T)"); }
#ifdef SPEC_FIRST
template <> void f<>(int*) { std::puts("(c) f<>(int*)"); }
template <class T> void f(T*) { std::puts("(b) f(T*)"); }
#else
template <class T> void f(T*) { std::puts("(b) f(T*)"); }
template <> void f<>(int*) { std::puts("(c) f<>(int*)"); }
#endif

int main() {
    int i = 0;
    f(&i);
}
```

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

- ★★★ **같은 세 선언, 같은 호출 `f(&i)` 인데 결과가 `(c)` → `(b)`** — 두 컴파일러 같다. 바꾼 것은 **(c) 를 (b) 앞에 둔 것 하나**다.
- ★★★ **기본 순서** — (c) `template <> void f<>(int*)` 는 **바로 위의 (b) `f(T*)` 에 `T = int` 로 붙는다.** 오버로드 해석이 (a)·(b) 중 (b) 를 고르고 → **(b) 에 붙은 특수화 (c) 를 본다** → `(c)`.
- ★★★ **`-DSPEC_FIRST`** — (c) 를 선언하는 순간 **보이는 기본 템플릿이 (a) 하나뿐**이라 (c) 는 **(a) 에 `T = int*` 로 붙는다.** 오버로드 해석은 (a)·(b) 중 (b) 를 고르고 → (b) 에는 특수화가 없다 → **`(b)`**. **(c) 는 「정확히 `int*`」인데도 불리지 않는다.**\
  ★ cppreference — 「only non-template and primary template overloads participate in overload resolution. The specializations are not overloads and are not considered.」

**실행 출력은 「무엇이 불렸나」만 말한다 — 「(c) 가 어디에 붙었나」는 기호표가 말한다** —

```bash
# spec-nm.sh
# spec-nm.sh — spec04.cpp 를 선언 순서 두 판으로. f 의 기호가 무엇으로 생기나(T = 보통 함수 정의 · W = 암묵 인스턴스)
for c in g++ clang++; do for d in '' -DSPEC_FIRST; do
  $c -std=c++20 $d -c spec04.cpp -o s4.o
  printf '== %s %s\n' "$c" "${d:-(기본 순서)}"
  nm -C s4.o | grep ' f<' | sed 's/^0*//'
done; done
rm -f s4.o
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

- ★★★ **기본 순서는 `T void f<int>(int*)` 하나** — `f<int>` 의 `T` 가 `int` 라는 것은 (c) 가 **(b) `f(T*)` 의 특수화**라는 뜻이다. **(b) 의 암묵 인스턴스는 없다** — (c) 가 그 자리를 차지했다.
- ★★★ **`-DSPEC_FIRST` 는 `T void f<int*>(int*)` + `W void f<int>(int*)`** — (c) 는 **(a) `f(T)` 의 `T = int*` 특수화**(`f<int*>`)가 되어 **정의만 있고 불리지 않았고**, 실제로 불린 것은 **(b) 의 암묵 인스턴스 `f<int>`**(`W`)다.
- ★★ **`T` 대 `W`** — 전체 특수화는 **보통 함수의 정의**라 `T`(강한 기호), 암묵 인스턴스는 `W`(약한 기호 — 32편 (6)).

```text
   기본 순서                                  -DSPEC_FIRST
   (a) f(T)                                   (a) f(T)
   (b) f(T*)                                  (c) f<>(int*)   ── 보이는 것은 (a) 뿐 → (a) 의 T=int* 특수화
   (c) f<>(int*) ── (b) 의 T=int 특수화        (b) f(T*)

   f(&i): ① (a)·(b) 중 (b)  ② (b) 의 특수화?     f(&i): ① (a)·(b) 중 (b)  ② (b) 의 특수화? 없음
          → (c)                                       → (b) 의 인스턴스      ★ (c) 는 버려진다
   nm: T f<int>(int*)                         nm: T f<int*>(int*) · W f<int>(int*)
```

- ★★ **처방** — 함수 템플릿을 특별하게 다루고 싶으면 **특수화 대신 오버로드**(보통 함수 `void f(int*)` 또는 또 하나의 템플릿)를 쓴다 — 오버로드는 **해석에 참가**하므로 선언 순서에 이렇게 휘둘리지 않는다. ★ 이 문서는 보통 함수 판을 던지지 않았다.

### (4) ★★ `std::vector<bool>` — 표준이 붙인 특수화

**언제 쓰나** — `vector<T>` 를 받는 일반 코드에 `bool` 이 들어올 수 있을 때.

```cpp
/* spec05.cpp */
// vector<bool> 과 vector<char> — 원소 하나의 주소를 bool* / char* 로 받는다
#include <vector>

int main() {
    std::vector<char> vc{1, 0};
    char* pc = &vc[0];
    (void)pc;
    std::vector<bool> vb{true, false};
    bool* pb = &vb[0];
    (void)pb;
}
```

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

- ★★★ **`char* pc = &vc[0];` 는 통과하고 `bool* pb = &vb[0];` 만 에러** — g++ `taking address of rvalue` + `cannot convert ‘std::vector<bool>::reference*’ to ‘bool*’`, clang `taking the address of a temporary object of type 'reference'` + `cannot initialize a variable of type 'bool *'`. **두 컴파일러 다 2건.**
- ★★ **`vb[0]` 이 `bool&` 이 아니라 `std::vector<bool>::reference` 라는 임시 객체**다 — 비트 하나를 가리키는 **대리 객체(프록시)** 다. 주소를 못 얻는다.

```cpp
/* spec06.cpp */
// vector<bool>::operator[] 가 돌려주는 것의 타입과 크기
#include <cstdio>
#include <cstdlib>
#include <cxxabi.h>
#include <type_traits>
#include <typeinfo>
#include <vector>

template <class T> void show(const char* label) {
    int st = 0;
    char* s = abi::__cxa_demangle(typeid(T).name(), nullptr, nullptr, &st);
    std::printf("%-34s %s\n", label, s);
    std::free(s);
}

int main() {
    std::vector<char> vc{1, 0};
    std::vector<bool> vb{true, false};
    show<decltype(vc[0])>("decltype(vc[0])");
    show<decltype(vb[0])>("decltype(vb[0])");
    std::printf("%-34s %d\n", "is_reference of decltype(vb[0])", (int)std::is_reference<decltype(vb[0])>::value);
    std::printf("%-34s %d\n", "is_reference of decltype(vc[0])", (int)std::is_reference<decltype(vc[0])>::value);
}
```

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

- ★★★ **`is_reference of decltype(vb[0])` 가 0, `vc[0]` 은 1** — `vector<char>` 의 `operator[]` 는 **참조**를, `vector<bool>` 은 **값(대리 객체)** 을 돌려준다.
- ★ **`typeid` 는 참조를 떼고 이름을 준다** — 그래서 `decltype(vc[0])` 이 `char&` 가 아니라 `char` 로 찍혔다. 참조인지는 `is_reference` 로 따로 물었다.
- ★ **`std::_Bit_reference`** 는 libstdc++ 가 붙인 이름이다(구현). **「`reference` 가 `bool&` 이 아니다」** 가 표준 쪽 사실이다.

## 문법 — 형태와 규칙

### 형태

```text
   template <class T> struct P { … };                    기본 템플릿
   template <> struct P<int> { … };                      전체(명시적) 특수화
   template <class T> struct P<T*> { … };                부분 특수화 — 클래스·변수 템플릿만
   template <class T, std::size_t N> struct P<T[N]> {…}; 부분 특수화 — 매개변수가 늘어도 된다

   template <class T> void f(T);                          함수 — 기본 템플릿
   template <> void f<>(int*);                            함수 — 전체 특수화 (가까운 기본 템플릿에 붙는다)
   template <class T> void f(T*);                         함수 — ★ 부분 특수화 대신 오버로드
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (1)\~(3)이 **실행한 소스**로 보였다.

### 규칙

- ★★★ **맞는 특수화 중 가장 좁은 것 · 유일하지 않으면 에러 · 없으면 기본**((1)).
- ★★★ **`const T*` 는 `<T*>`, `T* const` 는 `<const T>`** — `const` 가 **어디에 붙었나**가 판을 가른다((1)).
- ★★★ **함수 템플릿에는 부분 특수화가 없다 — 오버로드로 푼다**((2)).
- ★★★ **함수 템플릿의 특수화는 오버로드 해석에 참가하지 않는다** — 고른 기본 템플릿에 붙은 것만 본다. **그래서 선언 순서가 결과를 바꾼다**((3)).
- ★★ **`vector<bool>` 의 원소는 주소를 가질 수 없다** — `operator[]` 가 대리 객체를 돌려준다((4)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | g++ 진단 | clang 진단 | 어디서 |
|---|---|---|---|
| `Pick<const char[3]>` (두 부분 특수화가 맞는다) | `ambiguous template instantiation` | `ambiguous partial specializations` | (1) |
| `template <class T> void name<T*>(T*)` | `non-class, non-variable partial specialization … is not allowed` | `function template partial specialization is not allowed` | (2) |
| `bool* pb = &vb[0];` | `taking address of rvalue` · `cannot convert` | `taking the address of a temporary object` · `cannot initialize` | (4) |

## 어디서 틀리나

### 1. ★★★ 「`int* const` 는 포인터니까 `<T*>` 로 간다」

(1)이 반증이다 — **`<const T>`**(`T = int*`). 포인터 **자체가** `const` 면 `T*` 꼴이 아니다. `const int*` 만 `<T*>` 다.

### 2. ★★★ 「특수화가 둘 맞으면 먼저 선언한 것」

(1)이 반증이다 — **선언 순서와 무관하게 에러**(`const char[3]`). 클래스 템플릿의 특수화 선택은 **좁은 순서**로만 한다.

### 3. ★★★ 「함수 템플릿도 `f<T*>` 로 부분 특수화하면 된다」

(2)가 반증이다 — **두 컴파일러 다 선언에서 거절.** 오버로드 `f(T*)` 로 쓴다.

### 4. ★★★ 「정확히 맞는 전체 특수화가 있으면 그것이 불린다」

(3)이 반증이다 — **`-DSPEC_FIRST` 판에서 `f<>(int*)` 가 정확히 맞는데 `(b)` 가 불렸다.** 특수화는 **오버로드가 아니다.**

### 5. ★★ 「(3)의 두 판은 실행 결과만 다르다」

(3)의 기호표가 반증이다 — **특수화가 붙은 기본 템플릿 자체가 다르다**(`f<int>` 대 `f<int*>`). 실행 출력만 보면 「어느 쪽이 불렸나」밖에 안 보인다.

### 6. ★★ 「`vector<T>` 는 `T` 가 무엇이든 `&v[0]` 이 `T*` 다」

(4)가 반증이다 — **`bool` 에서만 에러.** 표준 라이브러리가 **`vector<bool>` 을 특수화**했다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제는 거의 전부 「표준」 칸이다** — 판 고르기와 오버로드 해석은 **컴파일 때 끝나는 약속**이라 두 컴파일러가 **9칸 전부 같은 판**, (3)의 **네 실행 전부 같은 줄**을 냈다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **격자 9칸**((1)) · **모호하면 에러**((1)) · **함수 부분 특수화 금지**((2)) · **특수화는 오버로드 해석 밖**((3)) · **`vector<bool>::reference` 가 참조가 아님**((4)) | 두 컴파일러 · cppreference 세 문장 | ★★★ **(3)의 두 판은 둘 다 합법이다** — 어느 도구도 「선언 순서가 결과를 바꿨다」고 말하지 않는다 |
| **조건부 표준** | 특정 판에서만 | ★ 이 편은 **판을 바꿔 던지지 않았다**(변수 템플릿 부분 특수화는 C++14 부터 — 던지지 않았다) | — | — |
| **구현 정의** | 문서화 의무 | ★★ **`std::_Bit_reference`** 라는 이름((4)) · `typeid` 가 돌려주는 문자열 | 두 컴파일러 출력(같은 libstdc++) | ★ **libc++ 는 다른 이름일 수 있다** — 던지지 않았다 |
| **미명시** | 몇 가지 중 하나 | ★ 이 주제에는 **해당하는 결론이 없다** | — | — |
| **UB** | 아무 일이나 | ★ **이 주제의 코드는 UB 가 없다** | — | — |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ 컴파일러 | clang 컴파일러 | 실행 도구 |
|---|---|---|---|---|
| ★★★ **정확히 맞는 특수화가 버려진다**((3) `SPEC_FIRST`) | 표준(허용된 코드) | ★★★ **경고 0** | ★★★ **경고 0** | 실행 출력은 `(b)` 만 — **왜** 는 기호표 |
| ★★ **`int* const` 가 `<T*>` 를 비껴간다** | 표준 | **경고 0** | **경고 0** | 부적용 |
| ★★★ **모호 · 함수 부분 특수화 · `&vb[0]`** | ill-formed | ★★★ **에러** | ★★★ **에러** | — |

- ★★ **이 표의 결론** — **틀린 판이 골라져도 아무도 말하지 않는다.** (3)은 `-Wall -Wextra -pedantic` 에서 두 컴파일러 **경고 0** 이다.

### ★ 종료 코드 0인데 ill-formed — 이 편에서는 못 찾았다

- ★ 에러가 난 세 자리는 **두 컴파일러 다 `cc exit=1`** 이었다. (3)은 **ill-formed 가 아니라 합법인데 뜻밖인** 코드다 — 같은 칸에 두면 안 된다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 타입 **한 개**만 다르게 | ★★ **클래스: 전체 특수화 · 함수: 보통 함수 오버로드** | (1)(3) — 함수 쪽 특수화는 순서에 휘둘린다 |
| 타입 **한 무리**(포인터·배열·`const`)를 다르게 | ★★★ **클래스: 부분 특수화 · 함수: 템플릿 오버로드** | (1)(2) |
| 부분 특수화가 둘 이상 겹칠 수 있다 | ★★ **겹치는 칸(`const T[N]` 류)을 격자로 던져 본다** | (1) — 모호하면 에러 |
| 함수 템플릿의 동작을 타입별로 | ★★★ **특수화하지 않는다** | (3) |
| `vector<bool>` 의 원소 주소가 필요하다 | ★★ **`vector<char>` · `std::deque<bool>` · 배열** | (4) — 이 문서는 대안 둘을 던지지 않았다 |

## 핵심 문장

- ★★★ **맞는 특수화 중 가장 좁은 것 — 인자 9칸에서 두 컴파일러가 갈린 칸 0, 모호해서 멈춘 칸 1(`const char[3]`).**
- ★★★ **`const int*` 는 `<T*>`, `int* const` 는 `<const T>`** — `const` 가 붙은 자리가 판을 고른다.
- ★★★ **함수 템플릿의 부분 특수화는 두 컴파일러 다 선언에서 거절한다 — 오버로드 `f(T*)` 로 푼다.**
- ★★★ **함수 템플릿의 특수화는 오버로드 해석에 참가하지 않는다** — 선언 순서만 바꿔 `(c)` → `(b)`, 기호가 `f<int>` → `f<int*>` + `f<int>`.
- ★★ **`vector<bool>` 의 `vb[0]` 은 참조가 아니다(`is_reference` 0)** — `&vb[0]` 이 `bool*` 가 안 된다.

## 관련 자료

- [32번](../32-class-templates-and-ctad/) — ★★★ 클래스 템플릿 정의와 **`nm` 의 `W`**((6)). 여기의 `Pick` 이 그 위에 선 것이다.
- [31번](../31-function-templates-and-argument-deduction/) (2) — `T*` 꼴과 `const` — (1)의 `const int*` 행 · (2)의 `"hi"` 감쇠.
- [01번](../01-function-overloading-and-overload-resolution/) — 오버로드 해석 — (3)의 ① 단계. 특수화는 **그 단계에 안 들어간다.**
- [34번](../34-variadic-templates-and-pack-expansion/) — 팩을 받는 템플릿의 특수화·오버로드(재귀 풀기의 끝 판).
- [35번](../35-instantiation-header-placement-and-reading-errors/) — 특수화도 **헤더에 둬야 하는** 이유(쓰는 번역 단위마다 보여야 한다).
- C# 갈래 [24번](../../../csharp/syntax/24-generics-and-type-parameters/) — C# 제네릭에는 특수화가 없다 · 참조 타입 인자는 **코드를 공유**한다((4) `__Canon`). C++ 은 인자마다 **따로 만들고**, 그중 하나를 **손으로 바꿔 끼울 수** 있다.
- 목록의 **36번 주제**(컨셉) · 목록의 **37번 주제**(SFINAE) — 「이 타입이면 이 오버로드」를 **조건**으로 적는 법. 목록의 **41번 주제** — `vector` 선택.

## 용어 풀이

> **기본 템플릿(primary template)** — 특수화가 아닌 원래 템플릿 선언. 함수 쪽은 **오버로드마다 기본 템플릿이 따로** 있다.\
> 예: (3)의 (a) `f(T)` 와 (b) `f(T*)`.

> **전체(명시적) 특수화(explicit specialization)** — `template <>` 로 **모든 인자를 정한** 판. 클래스·함수 둘 다 된다.\
> 예: (1)의 `Pick<int>` · (3)의 (c).

> **부분 특수화(partial specialization)** — 인자 **일부 모양만** 정한 판(`T*`·`const T`·`T[N]`). **클래스·변수 템플릿만** 된다.\
> 예: (1)의 `Pick<T*>`.

> **부분 순서(partial ordering)** — 둘 이상 맞을 때 **더 좁은 쪽**을 고르는 규칙. 가릴 수 없으면 모호.\
> 예: (1)의 `const char[3]` · (2)의 `f(T)` 대 `f(T*)`.

> **대리 객체(proxy)** — 실제 객체 대신 돌려주는 작은 객체. `vector<bool>` 은 비트 하나를 가리키는 `reference` 를 돌려준다.\
> 예: (4)의 `std::_Bit_reference`.

## 더 들어가면

- **변수 템플릿의 부분 특수화(C++14)** — `template <class T> constexpr bool is_ptr<T*> = true;`. 이 문서는 던지지 않았다.
- **특수화를 첫 사용 뒤에 선언하면** — cppreference 는 「특수화는 **암묵 인스턴스화를 일으킬 첫 사용 전에** 선언해야 한다」고 적는다. 이 문서는 던지지 않았다.
- **멤버 하나만 특수화** — `template <> int Box<int>::get() const { … }`. 클래스 전체를 다시 쓰지 않고 멤버만 바꾼다. 이 문서는 던지지 않았다.
