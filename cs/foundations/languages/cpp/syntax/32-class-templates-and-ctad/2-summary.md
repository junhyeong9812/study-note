# cpp/syntax/32 — 클래스 템플릿과 CTAD(C++17) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 클래스 템플릿 인자 추론(CTAD)](https://en.cppreference.com/w/cpp/language/class_template_argument_deduction) · [cppreference — 클래스 템플릿](https://en.cppreference.com/w/cpp/language/class_template)\
> ★ 이 배치에서 **위 cppreference 두 쪽을 열어 확인했다** — 「복사 추론 후보(copy deduction candidate)」 · 「템플릿 인자 목록이 있으면 추론하지 않는다」 · 「집합체 추론 후보(C++20)」 · 「`std::vector v2{v1}` 은 `vector<int>`(P0702R1)」 · 「쓰이지 않는 멤버는 인스턴스화되지 않는다」 다섯 문장이다. **값은 전부 두 컴파일러에게 던져 얻었다.**
> **실행 검증** — 이 문서의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **libstdc++ 13**(★ clang 도 같은 libstdc++ 를 쓴다) · GNU nm 2.42 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++17 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이다. ★ **판이 결론을 가르는 블록은 `-std=c++14` / `-std=c++17` / `-std=c++20` 을 배너에 적었다.**\
> 블록마다 **소스 파일 이름이 다르다**(`ctad01.cpp` \~ `ctad06.cpp` · `ctad-grid.sh`). ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. 소스 펜스의 배너도 **캡처가 찍은 것**이다.
> **버전** — 클래스 템플릿은 **C++98부터**, **CTAD 와 사용자 추론 가이드는 C++17부터**, **집합체 CTAD 는 C++20부터**다. 기준은 **C++17**이고 집합체 절만 C++20 이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★★ **[31번](../31-function-templates-and-argument-deduction/)에서 온다 — 31편이 잰 것은 다시 재지 않고 인용한다.**\
> [31번](../31-function-templates-and-argument-deduction/) (2) — **인자 여섯 × 매개변수 꼴 넷 = 24칸의 `T`**(값 매개변수는 감쇠 · 최상위 `const` 제거) · (3) — **`max_of(1, 2.0)` 은 `deduced conflicting types`** · (4) — **명시 지정은 추론을 대신한다** · (5) — **인스턴스는 `nm -C` 로 센다.**\
> ★★ **여기서 새로 묻는 것은 넷이다** — **생성자 인자로 클래스의 `T` 를 정하는 CTAD 격자(선언 11 × 판 2 × 컴파일러 2)** · **추론 가이드 한 줄이 무엇을 바꾸나** · **CTAD 가 안 되는 두 자리(일부만 적기 · C++17 집합체)** · **멤버 함수는 쓰일 때만 만들어진다.**
> **경계** — 「함수 템플릿의 추론 규칙 자체」는 [31번](../31-function-templates-and-argument-deduction/)이, 「특수화」는 [33번](../33-template-specialization-and-partial-specialization/)이, 「헤더에 둘까 `.cpp` 에 둘까」는 [35번](../35-instantiation-header-placement-and-reading-errors/)이, 「컨셉 제약」은 [목록의 **36번 주제**](../36-concepts-and-requires/)가 정본이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단의 **문구**(`missing template arguments` 대 `requires template arguments`) | ★★★ **`cc exit`** · **격자 칸의 타입**(맹글링 이름을 풀어 적은 것) · **「갈린 칸 N / M」** |
> | ★ **타입 이름의 철자** — `c++filt`·`__cxa_demangle` 이 푸는 모양(`char const*` · `3ul` · `std::__cxx11::basic_string<…>`) | ★★ **`nm` 의 글자**(`W`·`T`·`U`)와 **기호가 있나 없나** |
> | ★ **`sizeof(Box<std::string>)` = 32** — libstdc++ 의 `std::string` 크기다 | ★ 두 컴파일러가 **같은 타입을 냈다는 사실**(맹글링 이름은 두 컴파일러가 같은 규칙 — Itanium C++ ABI — 으로 만든다) |

## 한눈에 — 쉽게 말하면

**CTAD 는 「주문서 없이 물건만 보여 주면 상자 크기를 골라 주는 창구」다.**

예전(C++14)에는 상자를 받으려면 **주문서에 크기를 적어야** 했다 — `Box<int> b(1);`.\
C++17 부터는 **넣을 물건(생성자 인자)만 보여 주면** 창구가 상자 크기를 고른다 — `Box b(1);` → `Box<int>`.\
창구가 고르는 규칙은 **함수 템플릿의 추론(31편)을 생성자에 그대로 쓴 것**이다.

- **규칙표에 한 줄을 더 붙일 수 있다** — 추론 가이드. 「문자열 리터럴이 오면 `std::string` 상자로」((3)).
- **주문서에 반만 적으면** 창구는 **아무것도 고르지 않는다** — 반쪽 주문서는 틀린 주문서다((4)).
- **상자에 붙은 기능 중 안 쓴 것은 만들지 않는다** — 멤버 함수는 부를 때 만들어진다((6)).

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 주문서에 크기를 적는다 | ★★ **명시적 템플릿 인자 `Box<int>`** | (1) |
| 물건만 보여 준다 | ★★★ **CTAD — `Box b(1);`** | (1)(2) |
| 창구의 규칙표 | ★★★ **생성자마다 만들어지는 가상의 함수 템플릿(암묵 추론 가이드) + 복사 추론 후보** | (2) |
| 규칙표에 한 줄 더 | ★★ **사용자 추론 가이드 `Box(const char*) -> Box<std::string>;`** | (3) |
| 반쪽 주문서 | ★★★ **`Duo<long> d{1, 2.0};` — 일부만 적으면 추론하지 않는다** | (4) |
| 생성자 없는 상자 | ★★ **집합체 — C++17 은 못 고르고 C++20 은 고른다** | (5) |
| 안 쓴 기능은 안 만든다 | ★★★ **멤버 함수는 쓰일 때만 인스턴스화** | (6) |

```text
   Box b(1);                         Box<int> 를 만든다
      │
      ▼ 생성자마다 가상의 함수 템플릿이 있다고 치고
   template <class T> Box<T> F(T);          ← Box(T x)
   template <class T> Box<T> F(T, T);       ← Box(T x, T)
   template <class T> Box<T> F(Box<T>);     ← 복사 추론 후보
      │
      ▼ F(1) 을 31편의 규칙으로 추론한다 → T = int
   Box<int>
```

## 이 주제가 답하려는 질문

1. ★★★ **어느 선언에서 CTAD 가 무엇을 고르나** — 괄호·중괄호·`=`, 표준 컨테이너, **`vector v{v2}` 가 감싸나 복사하나**((2)).
2. ★★ **추론 가이드는 무엇을 바꾸나** — 한 줄로 결과 타입이 바뀌는 자리((3)).
3. ★★★ **CTAD 가 멈추는 자리** — 일부만 적은 인자 목록 · C++17 의 집합체((4)(5)).
4. ★★ **클래스 템플릿의 멤버는 언제 만들어지나** — 쓰지 않은 멤버의 몸통은 검사되나((6)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ② 두 컴파일러 × 두 판에게 「무슨 타입이냐」를 묻는 것이다

★★★ **이 주제의 본체는 ② 두 컴파일러 대조를 판 격자로 늘린 것이다** — 추론된 `Box<?>` 는 **눈에 안 보인다.** 31편은 `__PRETTY_FUNCTION__` 으로 물었는데, 이번에는 **`typeid(x).name()` 의 맹글링 이름**을 받아 `c++filt -t` 로 푼다.\
★ 왜 바꿨나 — `std::vector` 처럼 기본 인자가 붙은 타입은 **컴파일러마다 적는 모양이 다를 수 있는데**, 맹글링 이름은 **두 컴파일러가 같은 ABI 규칙으로 만든다.** 풀기 전 문자열을 견주면 철자 흔들림 없이 **같은 타입인가**를 기계로 가른다.\
★★ **④ 어셈블리 대신 기호표(`nm -C`)** 로 「멤버가 만들어졌나」를 본다(제5의 상태 — 31편과 같은 바꾼 창).

```text
① 다섯 층 표            CTAD 규칙은 표준 · 이름의 철자·string 크기는 구현          (구현 세부사항 절)
② ★ 두 컴파일러 × 두 판   선언 11 × c++14/17 × g++/clang++ = 44칸                     (1)(2)(4)(5)
③ ASan                   —                                                          부적용
④ 어셈블리 → 기호표      nm -C 로 「쓰지 않은 멤버의 기호가 있나」                     (6)
⑤ 경고 격자             —                                                          부적용
⑥ <typeinfo>·<cxxabi.h> typeid(x).name() + c++filt -t / __cxa_demangle              (2)(3)(5)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 다섯 층 표 | ★★ **추론 규칙은 표준, `char const*`·`3ul` 같은 철자와 `sizeof(std::string)` 은 구현** | **쓴다** |
| ★★★ **② 두 컴파일러 × 판** | ★★★ **본체** — 44칸 중 **판이 가른 칸 20 / 22 · 컴파일러가 가른 칸 0 / 22** | **쓴다** |
| ③ ASan | ★ **부적용** — CTAD 는 **컴파일 때 끝난다**(18-B 「잴 것이 없다」) | **안 쓴다** |
| ★★ **④ → 기호표** | ★★ `W Box<int>::get() const` 는 있고 **`odd` 는 기호가 없다** — 창을 바꿔 답했다(제5의 상태) | **쓴다(바꿔서)** |
| ⑤ 경고 격자 | ★ **부적용** — 통과한 칸은 **경고 0** 이었다((1)(3)(5) 배너 · 진단 0줄). 격자 스크립트는 진단을 **보지 않는다**(`2>/dev/null` — 칸에는 타입 또는 `error` 만 남긴다) | **안 쓴다** |
| ★★ **⑥ 타입 이름** | ★★ **`typeid` + `c++filt -t`**(격자) · **`abi::__cxa_demangle`**(한 줄 출력) | **쓴다** |

### (1) ★★ 클래스 템플릿 — 적은 선언과 안 적은 선언

**언제 쓰나** — 클래스 템플릿을 처음 만들 때. **C++14 코드베이스라면 늘 이 모양**이다.

```cpp
/* ctad01.cpp */
// 클래스 템플릿 하나 — 템플릿 인자를 적은 선언과, -DOMIT 이면 안 적은 선언
#include <cstdio>

template <class T> struct Box {
    T v;
    Box(T x) : v(x) {}
    T get() const { return v; }
};

int main() {
    Box<int> a(1);
    std::printf("a.get() = %d\n", a.get());
#ifdef OMIT
    Box b(2);
    std::printf("b.get() = %d\n", b.get());
#endif
}
```

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic ctad01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a.get() = 1
===== clang++ -std=c++14 -Wall -Wextra -pedantic ctad01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a.get() = 1
```

- ★★ **`Box<int> a(1);` 은 C++14 에서도 된다** — 두 컴파일러 `cc exit=0` · 경고 0줄.

★★★ **`-DOMIT` 로 `Box b(2);` 를 켜고 C++14 로 던지면** —

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic -DOMIT ctad01.cpp -o ex (cc exit=1) =====
ctad01.cpp: In function ‘int main()’:
ctad01.cpp:14:9: error: missing template arguments before ‘b’
   14 |     Box b(2);
      |         ^
ctad01.cpp:15:35: error: ‘b’ was not declared in this scope
   15 |     std::printf("b.get() = %d\n", b.get());
      |                                   ^
```

```text
===== clang++ -std=c++14 -Wall -Wextra -pedantic -DOMIT ctad01.cpp -o ex (cc exit=1) =====
ctad01.cpp:14:5: error: use of class template 'Box' requires template arguments
   14 |     Box b(2);
      |     ^
ctad01.cpp:4:27: note: template is declared here
    4 | template <class T> struct Box {
      | ~~~~~~~~~~~~~~~~~~        ^
1 error generated.
```

- ★★★ **g++ `missing template arguments before ‘b’` · clang `use of class template 'Box' requires template arguments`** — **C++14 에는 클래스의 템플릿 인자를 추론하는 규칙이 없다.** 함수 템플릿(31편)은 C++98 부터 추론했는데 **클래스는 안 했다.**
- ★ g++ 는 에러가 **2건**이다 — 선언이 실패하니 `b` 가 **없는 이름**이 되어 다음 줄도 깨졌다. clang 은 **1건**. 첫 줄만 원인이다.

★★★ **같은 소스를 C++17 로 던지면** —

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -DOMIT ctad01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a.get() = 1
b.get() = 2
===== clang++ -std=c++17 -Wall -Wextra -pedantic -DOMIT ctad01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a.get() = 1
b.get() = 2
```

- ★★★ **두 컴파일러 `cc exit=0` · 경고 0줄 · `b.get() = 2`** — 소스는 한 글자도 안 바꿨다. **판 하나가 결론을 가른다.**

### (2) ★★★ CTAD 격자 — 선언 11 × 판 2 × 컴파일러 2

**언제 쓰나** — 「이 선언에서 무슨 타입이 되나」가 한 번이라도 헷갈릴 때.

```cpp
/* ctad02.cpp */
// 선언 하나를 -DCASE=n 으로 골라 컴파일하고, 추론된 타입의 맹글링 이름을 찍는다
#include <array>
#include <cstdio>
#include <typeinfo>
#include <utility>
#include <vector>

template <class T> struct Box {
    T v;
    Box(T x) : v(x) {}
    Box(T x, T) : v(x) {}
};

template <class T, class U> struct Duo {
    T a;
    U b;
    Duo(T x, U y) : a(x), b(y) {}
};

int main() {
    std::vector<int> v2{1, 2};
    (void)v2;
#if CASE == 1
    Box x{1};
#elif CASE == 2
    Box x(1);
#elif CASE == 3
    Box x = 1;
#elif CASE == 4
    Box x{"hi"};
#elif CASE == 5
    Box x{1, 2.0};
#elif CASE == 6
    Duo x{1, 2.0};
#elif CASE == 7
    std::vector x{1, 2};
#elif CASE == 8
    std::vector x{v2};
#elif CASE == 9
    std::vector x{v2, v2};
#elif CASE == 10
    std::pair x{1, "a"};
#elif CASE == 11
    std::array x{1, 2, 3};
#endif
    std::puts(typeid(x).name());
}
```

```bash
# ctad-grid.sh
# ctad-grid.sh — 선언 11개 × 표준 두 판 × 컴파일러 둘. 칸마다 추론된 타입(c++filt -t) 또는 error
decl=('Box x{1};' 'Box x(1);' 'Box x = 1;' 'Box x{"hi"};' 'Box x{1, 2.0};' 'Duo x{1, 2.0};'
      'std::vector x{1, 2};' 'std::vector x{v2};' 'std::vector x{v2, v2};' 'std::pair x{1, "a"};' 'std::array x{1, 2, 3};')
cell() {  # $1 컴파일러 $2 표준 $3 CASE — 칸 하나를 찍는다
  if $1 -std=$2 -DCASE=$3 ctad02.cpp -o gx 2>/dev/null; then ./gx | c++filt -t; else echo error; fi
}
printf '%s\t%s\t%s\t%s\t%s\n' "선언" "g++ c++14" "g++ c++17" "clang++ c++14" "clang++ c++17" > grid.tsv
for n in $(seq 1 ${#decl[@]}); do
  row="${decl[$((n-1))]}"
  for c in g++ clang++; do for s in c++14 c++17; do row="$row"$'\t'"$(cell $c $s $n)"; done; done
  printf '%s\n' "$row" >> grid.tsv
done
cat grid.tsv
bad=$(awk -F'\t' 'NF != 5' grid.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
rows=$(( $(wc -l < grid.tsv) - 1 ))
std_split=$(tail -n +2 grid.tsv | awk -F'\t' '{ n += ($2 != $3) + ($4 != $5) } END { print n }')
cc_split=$(tail -n +2 grid.tsv | awk -F'\t' '{ n += ($2 != $4) + ($3 != $5) } END { print n }')
echo "c++14 대 c++17 이 갈린 칸 $std_split / $((rows * 2)) · g++ 대 clang++ 가 갈린 칸 $cc_split / $((rows * 2))"
rm -f gx grid.tsv
```

```text
===== bash ctad-grid.sh (exit=0) =====
선언	g++ c++14	g++ c++17	clang++ c++14	clang++ c++17
Box x{1};	error	Box<int>	error	Box<int>
Box x(1);	error	Box<int>	error	Box<int>
Box x = 1;	error	Box<int>	error	Box<int>
Box x{"hi"};	error	Box<char const*>	error	Box<char const*>
Box x{1, 2.0};	error	error	error	error
Duo x{1, 2.0};	error	Duo<int, double>	error	Duo<int, double>
std::vector x{1, 2};	error	std::vector<int, std::allocator<int> >	error	std::vector<int, std::allocator<int> >
std::vector x{v2};	error	std::vector<int, std::allocator<int> >	error	std::vector<int, std::allocator<int> >
std::vector x{v2, v2};	error	std::vector<std::vector<int, std::allocator<int> >, std::allocator<std::vector<int, std::allocator<int> > > >	error	std::vector<std::vector<int, std::allocator<int> >, std::allocator<std::vector<int, std::allocator<int> > > >
std::pair x{1, "a"};	error	std::pair<int, char const*>	error	std::pair<int, char const*>
std::array x{1, 2, 3};	error	std::array<int, 3ul>	error	std::array<int, 3ul>
c++14 대 c++17 이 갈린 칸 20 / 22 · g++ 대 clang++ 가 갈린 칸 0 / 22
```

- ★★★ **c++14 대 c++17 이 갈린 칸 20 / 22** — c++14 열은 **11행 전부 `error`**, c++17 열은 **`Box x{1, 2.0};` 한 행만 `error`**. 갈리지 않은 두 칸이 바로 그 행이다(**두 판 모두 에러**).
- ★★★ **g++ 대 clang++ 가 갈린 칸 0 / 22** — 맹글링 이름이 한 글자도 같다. ★ 단 **clang 도 libstdc++ 13 을 쓴다** — 표준 컨테이너 행은 「두 컴파일러가 같은 라이브러리를 봤다」는 뜻이지 「두 구현이 독립적으로 같았다」가 아니다.
- ★★ **`Box x{1}` · `Box x(1)` · `Box x = 1` 셋이 전부 `Box<int>`** — 괄호·중괄호·`=` 는 **추론 결과를 안 바꾼다.**
- ★★ **`Box x{"hi"}` 는 `Box<char const*>`** — 생성자 `Box(T x)` 가 **값 매개변수**라 배열이 감쇠했다(31편 (2)의 `T` 열 `"hi"` → `const char*` 와 **같은 칸**).
- ★★★ **`Box x{1, 2.0}` 은 c++17 에서도 에러** — 생성자 `Box(T x, T)` 가 두 인자에 **같은 `T`** 를 요구한다(31편 (3)의 `max_of(1, 2.0)` 과 **같은 실패**). 매개변수가 둘인 **`Duo x{1, 2.0}` 은 `Duo<int, double>`**.
- ★★★ **`std::vector x{v2}` 는 `std::vector<int>`** — **감싸지 않고 복사한다.** 원소가 둘인 **`std::vector x{v2, v2}` 만 `vector<vector<int>>`** 다.\
  ★ cppreference 는 이 행을 그대로 싣는다 — 「`std::vector v2{v1}; // std::vector<int>, not std::vector<std::vector<int>> (P0702R1)`」.
- ★ **`std::pair x{1, "a"}` 는 `pair<int, char const*>`** · **`std::array x{1, 2, 3}` 은 `array<int, 3ul>`**(표준 라이브러리가 **자기 추론 가이드**를 둔다 — `array` 는 집합체라 가이드가 없으면 C++17 에서 못 고른다((5))).

**`Box x{1, 2.0}` 의 에러가 창구의 규칙표를 보여 준다** —

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -DCASE=5 ctad02.cpp -o ex (cc exit=1) =====
ctad02.cpp: In function ‘int main()’:
ctad02.cpp:32:17: error: class template argument deduction failed:
   32 |     Box x{1, 2.0};
      |                 ^
ctad02.cpp:32:17: error: no matching function for call to ‘Box(int, double)’
ctad02.cpp:11:5: note: candidate: ‘template<class T> Box(T, T)-> Box<T>’
   11 |     Box(T x, T) : v(x) {}
      |     ^~~
ctad02.cpp:11:5: note:   template argument deduction/substitution failed:
ctad02.cpp:32:17: note:   deduced conflicting types for parameter ‘T’ (‘int’ and ‘double’)
   32 |     Box x{1, 2.0};
      |                 ^
ctad02.cpp:10:5: note: candidate: ‘template<class T> Box(T)-> Box<T>’
   10 |     Box(T x) : v(x) {}
      |     ^~~
ctad02.cpp:10:5: note:   template argument deduction/substitution failed:
ctad02.cpp:32:17: note:   candidate expects 1 argument, 2 provided
   32 |     Box x{1, 2.0};
      |                 ^
ctad02.cpp:8:27: note: candidate: ‘template<class T> Box(Box<T>)-> Box<T>’
    8 | template <class T> struct Box {
      |                           ^~~
ctad02.cpp:8:27: note:   template argument deduction/substitution failed:
ctad02.cpp:32:17: note:   mismatched types ‘Box<T>’ and ‘int’
   32 |     Box x{1, 2.0};
      |                 ^
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -DCASE=5 ctad02.cpp -o ex (cc exit=1) =====
ctad02.cpp:32:9: error: no viable constructor or deduction guide for deduction of template arguments of 'Box'
   32 |     Box x{1, 2.0};
      |         ^
ctad02.cpp:11:5: note: candidate template ignored: deduced conflicting types for parameter 'T' ('int' vs. 'double')
   11 |     Box(T x, T) : v(x) {}
      |     ^
ctad02.cpp:10:5: note: candidate function template not viable: requires single argument 'x', but 2 arguments were provided
   10 |     Box(T x) : v(x) {}
      |     ^   ~~~
ctad02.cpp:8:27: note: candidate function template not viable: requires 1 argument, but 2 were provided
    8 | template <class T> struct Box {
      |                           ^~~
1 error generated.
```

- ★★★ **g++ 가 후보 셋을 전부 적는다** — `template<class T> Box(T, T)-> Box<T>` · `template<class T> Box(T)-> Box<T>` · **`template<class T> Box(Box<T>)-> Box<T>`**. 앞의 둘은 **생성자 두 개**, 셋째는 **생성자로 쓰지 않은 것**이다.\
  ★ 셋째가 cppreference 의 **복사 추론 후보** — 「가상의 생성자 `C(C)` 에서 만든 가상의 함수 템플릿」. **`vector x{v2}` 가 감싸지 않고 복사한 것**이 이 후보가 이긴 결과다.
- ★★ **첫째 후보의 실패 이유가 31편과 같은 문구**다 — `deduced conflicting types for parameter ‘T’ (‘int’ and ‘double’)`. **CTAD 는 함수 템플릿 추론을 생성자에 빌려 쓴 것**이라는 증거다.

```text
   선언                         고른 후보                    결과
   Box x{1}                     Box(T)        T = int        Box<int>
   Box x{"hi"}                  Box(T)        T = const char*  ★ 감쇠 (31편 T 열)
   Box x{1, 2.0}                Box(T, T)     int 대 double   ★ 실패 (31편 max_of)
   std::vector x{v2}            복사 후보 C(C)  T = int        vector<int>        ★ 감싸지 않는다
   std::vector x{v2, v2}        initializer_list 생성자        vector<vector<int>>
```

### (3) ★★ 추론 가이드 — 한 줄로 결과 타입을 바꾼다

**언제 쓰나** — **생성자의 매개변수 모양만으로는 원하는 `T` 가 안 나올 때.** 대표가 「문자열 리터럴 → `std::string`」이다.

```cpp
/* ctad03.cpp */
// 추론 가이드 한 줄 — -DWITH_GUIDE 이면 문자열 리터럴을 std::string 으로 받게 한다
#include <cstdio>
#include <cstdlib>
#include <cxxabi.h>
#include <string>
#include <typeinfo>

template <class T> struct Box {
    T v;
    Box(T x) : v(x) {}
};

#ifdef WITH_GUIDE
Box(const char*) -> Box<std::string>;
#endif

int main() {
    Box x{"hi"};
    int st = 0;
    char* s = abi::__cxa_demangle(typeid(x).name(), nullptr, nullptr, &st);
    std::printf("decltype(x) = %s\n", s);
    std::printf("sizeof(x)   = %zu\n", sizeof(x));
    std::free(s);
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic ctad03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
decltype(x) = Box<char const*>
sizeof(x)   = 8
===== g++ -std=c++17 -Wall -Wextra -pedantic -DWITH_GUIDE ctad03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
decltype(x) = Box<std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > >
sizeof(x)   = 32
===== clang++ -std=c++17 -Wall -Wextra -pedantic ctad03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
decltype(x) = Box<char const*>
sizeof(x)   = 8
===== clang++ -std=c++17 -Wall -Wextra -pedantic -DWITH_GUIDE ctad03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
decltype(x) = Box<std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > >
sizeof(x)   = 32
```

- ★★★ **가이드 없이 `Box<char const*>` · 가이드 한 줄로 `Box<std::__cxx11::basic_string<…>>`**(= `std::string`) — 두 컴파일러 같다. **생성자는 한 글자도 안 바뀌었다** — 바뀐 것은 **「이 인자면 이 타입」이라는 규칙표 한 줄**이다.
- ★★ **가이드는 생성자가 아니다** — `-> Box<std::string>` 은 **결과 타입만** 정한다. 그다음 `Box<std::string>` 의 생성자 `Box(std::string x)` 가 `"hi"` 를 **변환해서** 받는다.
- ★ **`sizeof(x)` 가 8 → 32** — 포인터 하나가 문자열 객체 하나가 됐다. ★ **32 는 libstdc++ 의 `std::string` 크기**다(구현 정의 칸) — 「가이드가 크기를 4배로 만든다」로 읽지 마라. 이 블록이 보인 것은 **타입이 바뀌었다**는 것뿐이다.

### (4) ★★★ 일부만 적으면 — 추론하지 않는다

**언제 쓰나** — 「앞의 인자만 적고 나머지는 추론시키고 싶다」가 떠오를 때.

```cpp
/* ctad04.cpp */
// 템플릿 인자를 일부만 적는다 — 함수 템플릿과 클래스 템플릿
#include <cstdio>

template <class T, class U> struct Duo {
    T a;
    U b;
    Duo(T x, U y) : a(x), b(y) {}
};

template <class T, class U> Duo<T, U> make_duo(T x, U y) { return Duo<T, U>(x, y); }

int main() {
    auto f = make_duo<long>(1, 2.0);   // 함수 템플릿 — T 만 적고 U 는 추론
    std::printf("%zu %zu\n", sizeof(f.a), sizeof(f.b));
#ifdef PARTIAL
    Duo<long> d{1, 2.0};               // 클래스 템플릿 — T 만 적는다
    (void)d;
#endif
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic ctad04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
8 8
===== clang++ -std=c++17 -Wall -Wextra -pedantic ctad04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
8 8
```

- ★★ **함수 템플릿은 된다** — `make_duo<long>(1, 2.0)` 이 `T = long` 을 받고 `U` 를 추론해 `8 8`(`long` · `double`) — 31편 (4)의 명시 지정이 **일부만** 적어도 된다.

★★★ **`-DPARTIAL` 로 클래스 템플릿에 같은 것을 시키면** —

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -DPARTIAL ctad04.cpp -o ex (cc exit=1) =====
ctad04.cpp: In function ‘int main()’:
ctad04.cpp:16:13: error: wrong number of template arguments (1, should be 2)
   16 |     Duo<long> d{1, 2.0};               // 클래스 템플릿 — T 만 적는다
      |             ^
ctad04.cpp:4:36: note: provided for ‘template<class T, class U> struct Duo’
    4 | template <class T, class U> struct Duo {
      |                                    ^~~
ctad04.cpp:16:15: error: scalar object ‘d’ requires one element in initializer
   16 |     Duo<long> d{1, 2.0};               // 클래스 템플릿 — T 만 적는다
      |               ^
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -DPARTIAL ctad04.cpp -o ex (cc exit=1) =====
ctad04.cpp:16:5: error: too few template arguments for class template 'Duo'
   16 |     Duo<long> d{1, 2.0};               // 클래스 템플릿 — T 만 적는다
      |     ^
ctad04.cpp:4:36: note: template is declared here
    4 | template <class T, class U> struct Duo {
      | ~~~~~~~~~~~~~~~~~~~~~~~~~~~        ^
1 error generated.
```

- ★★★ **g++ `wrong number of template arguments (1, should be 2)` · clang `too few template arguments for class template 'Duo'`** — **CTAD 는 인자 목록이 아예 없을 때만 한다.** 하나라도 적으면 「전부 적었다」로 읽고 **모자라다고** 한다.\
  ★ cppreference — 「Class template argument deduction is only performed if no template argument list is present.」
- ★ 브리핑의 전제 「`Box<int,> b` 류 에러」는 **문법 오류라 다른 질문**이다 — 여기서는 **문법상 옳은 일부 지정**(`Duo<long>`)을 던졌다.

### (5) ★★ 생성자가 없는 집합체 — C++17 대 C++20

**언제 쓰나** — `struct { T a; T b; }` 처럼 **생성자를 안 쓴** 템플릿을 중괄호로 만들 때.

```cpp
/* ctad05.cpp */
// 생성자가 없는 집합체 — 중괄호 목록에서 T 를 추론하나
#include <cstdio>
#include <cstdlib>
#include <cxxabi.h>
#include <typeinfo>

template <class T> struct Agg {
    T a;
    T b;
};

int main() {
    Agg x{1, 2};
    int st = 0;
    char* s = abi::__cxa_demangle(typeid(x).name(), nullptr, nullptr, &st);
    std::printf("decltype(x) = %s · a + b = %d\n", s, x.a + x.b);
    std::free(s);
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic ctad05.cpp -o ex (cc exit=1) =====
ctad05.cpp: In function ‘int main()’:
ctad05.cpp:13:15: error: class template argument deduction failed:
   13 |     Agg x{1, 2};
      |               ^
ctad05.cpp:13:15: error: no matching function for call to ‘Agg(int, int)’
ctad05.cpp:7:27: note: candidate: ‘template<class T> Agg()-> Agg<T>’
    7 | template <class T> struct Agg {
      |                           ^~~
ctad05.cpp:7:27: note:   template argument deduction/substitution failed:
ctad05.cpp:13:15: note:   candidate expects 0 arguments, 2 provided
   13 |     Agg x{1, 2};
      |               ^
ctad05.cpp:7:27: note: candidate: ‘template<class T> Agg(Agg<T>)-> Agg<T>’
    7 | template <class T> struct Agg {
      |                           ^~~
ctad05.cpp:7:27: note:   template argument deduction/substitution failed:
ctad05.cpp:13:15: note:   mismatched types ‘Agg<T>’ and ‘int’
   13 |     Agg x{1, 2};
      |               ^
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic ctad05.cpp -o ex (cc exit=1) =====
ctad05.cpp:13:9: error: no viable constructor or deduction guide for deduction of template arguments of 'Agg'
   13 |     Agg x{1, 2};
      |         ^
ctad05.cpp:7:27: note: candidate function template not viable: requires 1 argument, but 2 were provided
    7 | template <class T> struct Agg {
      |                           ^~~
ctad05.cpp:7:27: note: candidate function template not viable: requires 0 arguments, but 2 were provided
1 error generated.
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic ctad05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
decltype(x) = Agg<int> · a + b = 3
===== clang++ -std=c++20 -Wall -Wextra -pedantic ctad05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
decltype(x) = Agg<int> · a + b = 3
```

- ★★★ **C++17 은 두 컴파일러 다 에러, C++20 은 두 컴파일러 다 `Agg<int> · a + b = 3`** — 소스는 같다.
- ★★ **g++ 의 C++17 후보 목록이 이유를 말한다** — 후보가 `Agg()-> Agg<T>` 와 `Agg(Agg<T>)-> Agg<T>`(복사 추론 후보) **둘뿐**이다. **생성자가 없으니 규칙표가 비어 있다.** C++20 은 여기에 **집합체 추론 후보**(멤버 순서대로 `Agg(T, T)`)를 더한다.
- ★ 그래서 (2)의 **`std::array x{1, 2, 3}`** 이 C++17 에서 된 것은 **표준 라이브러리가 가이드를 따로 적어 둔 덕**이다 — 사용자 집합체는 C++17 에서 **직접 가이드를 써야** 한다.

### (6) ★★★ 멤버 함수는 쓰일 때만 만들어진다

**언제 쓰나** — 「`T` 에 따라 컴파일이 안 되는 멤버가 있는데 괜찮나」를 판단할 때.

```cpp
/* ctad06.cpp */
// 클래스 템플릿의 멤버 함수 — 한 멤버는 int 로는 컴파일될 수 없는 몸통을 가졌다
#include <cstdio>

template <class T> struct Box {
    T v;
    T get() const { return v; }
    void odd() const { v.no_such_member(); }
};

int main() {
    Box<int> b{7};
    std::printf("%d\n", b.get());
#ifdef CALL_ODD
    b.odd();
#endif
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c ctad06.cpp -o c6.o && nm -C c6.o (exit=0) =====
0000000000000000 W Box<int>::get() const
                 U __stack_chk_fail
0000000000000000 T main
                 U printf
===== clang++ -std=c++17 -Wall -Wextra -pedantic -c ctad06.cpp -o c6.o && nm -C c6.o (exit=0) =====
0000000000000000 r .L.str
0000000000000000 r .L__const.main.b
0000000000000000 W Box<int>::get() const
0000000000000000 T main
                 U printf
```

- ★★★ **`odd()` 의 몸통 `v.no_such_member()` 는 `int` 로는 성립할 수 없는데 두 컴파일러 다 `exit=0` · 경고 0줄**이다.
- ★★★ **기호표에 `W Box<int>::get() const` 는 있고 `odd` 는 없다** — **쓰지 않은 멤버는 만들어지지 않았다.** cppreference — 「unless the member is used in the program, it is not instantiated」.
- ★ `W` 는 「**약한 기호** — 여러 오브젝트에 있어도 하나로 합쳐라」다(31편 (5)의 `W` 와 같은 글자). [35번](../35-instantiation-header-placement-and-reading-errors/)이 이 글자로 「헤더에 정의해도 다중 정의가 안 나는 이유」를 본다.

★★★ **`-DCALL_ODD` 로 `b.odd();` 를 부르면** —

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -DCALL_ODD ctad06.cpp -o ex (cc exit=1) =====
ctad06.cpp: In instantiation of ‘void Box<T>::odd() const [with T = int]’:
ctad06.cpp:14:10:   required from here
ctad06.cpp:7:26: error: request for member ‘no_such_member’ in ‘((const Box<int>*)this)->Box<int>::v’, which is of non-class type ‘const int’
    7 |     void odd() const { v.no_such_member(); }
      |                        ~~^~~~~~~~~~~~~~
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -DCALL_ODD ctad06.cpp -o ex (cc exit=1) =====
ctad06.cpp:7:25: error: member reference base type 'const int' is not a structure or union
    7 |     void odd() const { v.no_such_member(); }
      |                        ~^~~~~~~~~~~~~~~
ctad06.cpp:14:7: note: in instantiation of member function 'Box<int>::odd' requested here
   14 |     b.odd();
      |       ^
1 error generated.
```

- ★★★ **부르는 순간 에러** — g++ `In instantiation of ‘void Box<T>::odd() const [with T = int]’` + `required from here`(14행), clang `in instantiation of member function 'Box<int>::odd' requested here`(14행).
- ★★ **에러가 가리키는 줄은 7행(몸통)이고, 원인이 된 줄(14행 호출)은 사슬 끝에 붙는다** — 이 읽는 법의 정본은 [35번](../35-instantiation-header-placement-and-reading-errors/) (5)다.
- ★ 이 성질이 Rust 와 정반대다 — Rust 갈래 [31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/) (1)은 **한 번도 안 부른 제네릭 함수의 몸통이 E0599 로 막혔고**, (7)은 **같은 모양의 C++ 템플릿이 두 컴파일러 `exit 0`** 이었다. 이 편은 그것을 **멤버 함수 하나**로 좁혀 기호표까지 봤다.

## 문법 — 형태와 규칙

### 형태

```text
   template <class T> struct Box { Box(T); };      클래스 템플릿
   Box<int> a(1);                                   명시 — 어느 판에서나
   Box b(1);  Box b{1};  Box b = 1;                 CTAD (C++17) — 셋 다 Box<int>
   Box(const char*) -> Box<std::string>;            사용자 추론 가이드 (C++17)
   template <class T> Box(T*) -> Box<T>;            템플릿인 가이드도 된다
   Duo<long> d{1, 2.0};                             ★ 일부만 적기 — CTAD 안 한다 (에러)
   template <class T> struct Agg { T a, b; };  Agg g{1, 2};   집합체 CTAD (C++20)
```

★ 이 그림은 **형태 요약**이다 — 템플릿 가이드 줄(`Box(T*) -> Box<T>`)은 이 문서가 **던지지 않았다.** 나머지 줄의 실제 동작은 (1)\~(5)가 **실행한 소스**로 보였다.

### 규칙

- ★★★ **CTAD 는 생성자마다 가상의 함수 템플릿을 세우고 31편의 추론을 돌린다** — 그래서 감쇠·충돌이 31편과 같다((2)).
- ★★★ **복사 추론 후보가 늘 하나 더 있다** — `vector x{v2}` 가 감싸지 않고 복사한다((2)).
- ★★ **추론 가이드는 결과 타입만 정한다** — 그 뒤 생성자는 따로 고른다((3)).
- ★★★ **템플릿 인자를 하나라도 적으면 추론하지 않는다**((4)).
- ★★ **생성자 없는 집합체는 C++20 부터**((5)).
- ★★★ **멤버 함수는 쓰일 때만 인스턴스화된다** — 안 쓴 멤버의 `T` 의존 몸통은 검사되지 않는다((6)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | g++ 진단 | clang 진단 | 어디서 |
|---|---|---|---|
| `Box b(2);` (`-std=c++14`) | `missing template arguments before` | `requires template arguments` | (1) |
| `Box x{1, 2.0};` (생성자 `Box(T, T)`) | `class template argument deduction failed` | `no viable constructor or deduction guide` | (2) |
| `Duo<long> d{1, 2.0};` | `wrong number of template arguments` | `too few template arguments` | (4) |
| `Agg x{1, 2};` (`-std=c++17`) | `class template argument deduction failed` | `no viable constructor or deduction guide` | (5) |
| 안 쓰는 멤버를 부른다 `b.odd();` | `request for member … non-class type` | `member reference base type 'const int'` | (6) |

## 어디서 틀리나

### 1. ★★★ 「`std::vector x{v2}` 는 벡터를 원소로 갖는 벡터다」

(2)가 반증이다 — **`std::vector<int>`**. 복사 추론 후보가 이긴다. **원소가 둘(`{v2, v2}`)일 때만** `vector<vector<int>>`.

### 2. ★★★ 「`Box x{"hi"}` 는 `Box<std::string>` 이다」

(2)(3)이 반증이다 — 가이드가 없으면 **`Box<char const*>`**(감쇠). 가이드 **한 줄**이 있어야 `std::string` 이 된다.

### 3. ★★★ 「앞쪽 인자만 적고 나머지는 추론시킬 수 있다」

(4)가 반증이다 — **함수 템플릿은 되고 클래스 템플릿은 안 된다.** `Duo<long>` 은 「인자가 모자라다」로 읽힌다.

### 4. ★★ 「CTAD 는 중괄호에서만(혹은 괄호에서만) 된다」

(2)가 반증이다 — **`{}` · `()` · `=` 셋이 전부 `Box<int>`**.

### 5. ★★ 「생성자가 없는 구조체도 C++17 이면 추론된다」

(5)가 반증이다 — **C++17 은 두 컴파일러 다 에러.** C++20 부터다. `std::array` 가 C++17 에서 된 것은 **라이브러리의 가이드** 덕이다.

### 6. ★★★ 「클래스 템플릿을 인스턴스화하면 멤버 함수가 전부 만들어진다(그러니 전부 컴파일돼야 한다)」

(6)이 반증이다 — **안 쓴 `odd()` 는 기호도 없고 에러도 없다.** ★ 단 **명시적 인스턴스화 `template struct Box<int>;`** 는 멤버를 **전부** 만든다 — [35번](../35-instantiation-header-placement-and-reading-errors/) (2)가 같은 `odd()` 로 그 차이를 던졌다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제는 거의 전부 「표준」 칸이다** — CTAD 는 **컴파일 때 끝나는 약속**이라 22칸 중 **컴파일러가 가른 칸 0** 이었다. **갈린 것은 판(c++14/17/20)이다** — 이것은 「조건부 표준」 칸이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **격자의 c++17 열**((2)) · **복사 추론 후보**((2)) · **일부 지정이면 추론 안 함**((4)) · **쓰인 멤버만 인스턴스화**((6)) | 두 컴파일러 · cppreference 다섯 문장 | ★ **표준 컨테이너 행은 두 컴파일러가 같은 libstdc++ 를 봤다** — libc++ 로는 안 던졌다 |
| **조건부 표준** | 특정 판에서만 | ★★★ **CTAD·추론 가이드는 C++17부터**((1)(2)) · **집합체 CTAD 는 C++20부터**((5)) | `-std=` 격자 | ★★ **`-std=c++14` 는 「C++14 로 검증」이 아니다** — 이 문서는 에러가 나는 쪽만 판을 가르는 근거로 썼다 |
| **구현 정의** | 문서화 의무 | ★★ **`typeid(x).name()` 의 문자열**(맹글링 이름 — Itanium ABI) · **`c++filt` 의 철자**(`char const*`·`3ul`) · **`sizeof(std::string)` = 32**((3)) | 두 컴파일러 출력 | ★ 맹글링 이름이 같다는 것은 **이 ABI 에서** 같다는 것이다 |
| **미명시** | 몇 가지 중 하나 | ★ 이 주제에는 **해당하는 결론이 없다** | — | — |
| **UB** | 아무 일이나 | ★ **이 주제의 코드는 UB 가 없다** | — | — |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ 컴파일러 | clang 컴파일러 | 실행 도구 |
|---|---|---|---|---|
| ★★★ **`Box x{"hi"}` 가 `std::string` 이 아니라 포인터를 든다** | 표준(허용된 코드) | ★★★ **경고 0** | ★★★ **경고 0** | 부적용 |
| ★★ **`vector x{v2}` 가 감싸지 않고 복사한다** | 표준 | **경고 0** | **경고 0** | 부적용 |
| ★★ **안 쓰는 멤버의 몸통이 `T` 로는 성립하지 않는다** | 표준(ill-formed 아님 — 인스턴스화 전이다) | **경고 0 · exit 0** | **경고 0 · exit 0** | 기호표만 보인다((6)) |
| ★★★ **일부 지정 · C++17 집합체** | ill-formed | ★★★ **에러** | ★★★ **에러** | — |

- ★★ **이 표의 결론** — CTAD 가 **실패하면 크게 나고, 뜻밖의 타입으로 성공하면 조용하다**(31편의 결론과 같은 모양). 그래서 (2)의 격자처럼 **타입을 직접 묻는 탐침**이 필요하다.

### ★ 종료 코드 0인데 ill-formed — 이 편에서는 못 찾았다

- ★ 에러가 난 칸은 **두 컴파일러 다 `cc exit=1`** 이었다. (6)의 `odd()` 는 **ill-formed 가 아니다** — 인스턴스화되지 않은 멤버의 몸통은 그 `T` 로 검사받지 않는다(cppreference 의 「does not require a definition」 문장과 같은 성질).

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 지역 변수 · 타입이 인자에서 뻔하다 | ★★ **CTAD `Box b(1);`** | (1)(2) — 두 컴파일러 같은 타입 |
| 문자열 리터럴을 `std::string` 으로 받고 싶다 | ★★★ **추론 가이드** 또는 **`Box<std::string>` 을 적는다** | (3) — 가이드가 없으면 포인터 |
| 벡터 **하나를 원소로** 갖는 벡터가 필요하다 | ★★★ **`std::vector<std::vector<int>> x{v2};` 로 적는다** | (2) — CTAD 는 복사를 고른다 |
| 인자 일부만 정하고 싶다 | ★★ **팩토리 함수 템플릿**(`make_duo<long>(…)`) | (4) — 클래스는 안 된다 |
| 생성자 없는 템플릿 구조체 · C++17 | ★ **가이드를 직접 쓴다** 또는 C++20 | (5) |
| `T` 에 따라 안 되는 기능이 있다 | ★ **그 멤버를 안 부르면 된다** — 단 명시적 인스턴스화를 하면 깨진다 | (6) · 35편 (2) |
| 공개 API 의 멤버·반환 타입 | ★ **타입을 적는다** | 읽는 사람이 격자를 머릿속에 돌리지 않게 |

## 핵심 문장

- ★★★ **CTAD 는 생성자마다 세운 가상의 함수 템플릿으로 31편의 추론을 돌린다** — 그래서 `"hi"` 는 감쇠하고 `Box(T, T)` 에 `1, 2.0` 은 충돌한다.
- ★★★ **선언 11 × 판 2 × 컴파일러 2 — 판이 가른 칸 20 / 22, 컴파일러가 가른 칸 0 / 22.**
- ★★★ **`std::vector x{v2}` 는 `vector<int>`** — 복사 추론 후보가 이긴다. `{v2, v2}` 만 감싼다.
- ★★ **추론 가이드 한 줄이 `Box<char const*>` 를 `Box<std::string>` 으로 바꾼다.**
- ★★★ **인자를 하나라도 적으면 추론하지 않는다** · **집합체 CTAD 는 C++20.**
- ★★★ **멤버 함수는 쓰일 때만 만들어진다** — 안 쓴 멤버는 기호도, 에러도 없다.

## 관련 자료

- [31번](../31-function-templates-and-argument-deduction/) — ★★★ **이 편의 규칙 전부가 31편의 추론을 생성자에 빌려 쓴 것이다.** (2) 감쇠 · (3) 충돌 · (4) 명시 지정. 31편은 **함수**, 여기는 **클래스**까지다.
- [33번](../33-template-specialization-and-partial-specialization/) — 클래스 템플릿의 **특수화**(여기서 만든 `Box` 에 `<int>` 판을 따로 두기).
- [35번](../35-instantiation-header-placement-and-reading-errors/) — (6)의 「쓰일 때만 만든다」가 **헤더 배치**에서 무엇을 뜻하나 · 명시적 인스턴스화가 멤버를 **전부** 만드는 것.
- [04번](../04-brace-initialization-narrowing-and-initializer-list/) — `{}` 와 `initializer_list` 생성자 — (2)의 `{v2, v2}` 가 감싼 자리.
- Rust 갈래 [31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/) (1)(7) — **제네릭 몸통을 정의 자리에서 검사하는 쪽**(Rust)과 **인스턴스화 때 검사하는 쪽**(C++) — (6)의 대비.
- Java 갈래 [17번](../../../java/syntax/17-generic-declarations/) (8) — **다이아몬드 `<>` 는 기대 타입(좌변)에서** 추론한다. ★ CTAD 는 **좌변이 비어 있고 인자에서** 추론한다 — 방향이 반대다. [19번](../../../java/syntax/19-type-erasure/) — Java 는 `Box<Integer>` 와 `Box<String>` 이 **한 클래스로 지워지고**, C++ 은 (6)처럼 `Box<int>` 의 기호가 **따로 생긴다.**
- [목록의 **36번 주제**](../36-concepts-and-requires/)(컨셉) — 멤버에 `requires` 를 붙여 「이 `T` 에서는 이 멤버가 없다」를 적는 법.

## 용어 풀이

> **클래스 템플릿(class template)** — `T` 를 받아 클래스를 만드는 틀. `Box<int>` 처럼 인자를 넣은 것이 **특수화(specialization)** 하나다.\
> 예: (1)의 `Box`.

> **CTAD(class template argument deduction)** — C++17. 클래스 템플릿의 인자를 **생성자 인자에서** 추론하는 것.\
> 예: (1)의 `Box b(2);` → `Box<int>`.

> **추론 가이드(deduction guide)** — 「이런 인자면 이 타입」을 적는 선언. 생성자에서 저절로 생기는 **암묵 가이드**와 사람이 쓰는 **사용자 가이드**가 있다.\
> 예: (3)의 `Box(const char*) -> Box<std::string>;`.

> **복사 추론 후보(copy deduction candidate)** — 가상의 생성자 `C(C)` 에서 만든 가이드. 같은 템플릿의 객체를 넘기면 **감싸지 않고 복사**하게 만든다.\
> 예: (2)의 `std::vector x{v2}` · g++ 후보 목록의 `Box(Box<T>)-> Box<T>`.

> **집합체(aggregate)** — 사용자 생성자가 없고 멤버를 중괄호 순서대로 채우는 타입. 집합체 CTAD 는 **C++20**.\
> 예: (5)의 `Agg`.

> **암묵 인스턴스화(implicit instantiation)** — 쓰는 자리에서 컴파일러가 특수화를 만드는 것. 클래스 템플릿의 멤버 함수는 **쓰일 때만** 만들어진다.\
> 예: (6)의 `W Box<int>::get() const` 와 기호가 없는 `odd`.

> **맹글링 이름(mangled name)** — 링커용으로 타입을 문자열로 적은 것. `typeid(x).name()` 이 이것을 돌려주고 `c++filt -t` 가 푼다.\
> 예: (2) 격자의 모든 칸.

## 더 들어가면

- **템플릿인 추론 가이드** — `template <class It> Box(It, It) -> Box<typename std::iterator_traits<It>::value_type>;` 처럼 반복자 쌍에서 원소 타입을 꺼내는 것. 표준 컨테이너가 이렇게 한다. 이 문서는 던지지 않았다.
- **`explicit` 가이드** — `explicit Box(const char*) -> …;` 는 **복사 초기화(`Box b = "hi";`)** 에서 빠진다. 이 문서는 던지지 않았다.
- **별칭 템플릿의 CTAD(C++20)** — `template <class T> using V = std::vector<T>; V v{1, 2};`. 이 문서는 던지지 않았다.
- **CTAD 를 막고 싶을 때** — g++ 는 `-Wctad-maybe-unsupported` 경고를 둔다(**컴파일러의 것**이다). 이 문서는 켜 보지 않았다.
