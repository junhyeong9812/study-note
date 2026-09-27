# cpp/syntax/23 — 3방향 비교 `<=>`(C++20) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 기본 비교(default comparisons)](https://en.cppreference.com/w/cpp/language/default_comparisons) · [cppreference — 연산자 오버로딩](https://en.cppreference.com/w/cpp/language/operators) · [cppreference — `<compare>`](https://en.cppreference.com/w/cpp/header/compare)\
> ★ cppreference 「기본 비교」는 2026-09-26 에 열어 **다섯 문장을 확인했다** —\
> ① 「클래스가 `operator==` 를 **명시적으로 선언하지 않았으면**, **`= default` 로 정의된 `operator<=>` 마다** `operator==` 가 암묵 선언된다」 ·\
> ② 그래서 **`= default` 가 아닌 `<=>` 는 `==` 를 주지 않는다** · ③ `auto` 반환은 **`common_comparison_category_t`**(멤버 결과 중 가장 약한 것) ·\
> ④ 비교 순서는 **기반 → 멤버, 선언 순서** · ⑤ 반환 타입이 범주 타입이고 `<=>` 가 없으면 **`==` 와 `<` 로 합성**한다.
> **실행 검증** — 이 문서의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`cmp01.cpp` \~ `cmp12.cpp` · `cmp-asm.sh`). ★ (8)만 **`-std=c++17`** 이고, **배너에 적었다.**\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 배너도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
> **버전** — `<=>`·기본 비교·재작성 후보는 **C++20부터**다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.
> ★★★ **이 편은 [22번](../22-operator-overloading/)과 한 사슬이다** — 그 편 (1)의 「**멤버 연산자로는 `1 + a` 가 막힌다**」를\
> 이 편 (6)이 **비교 연산자에서는 재작성 후보가 푼다**로 닫는다.
> **경계** — 「연산자 오버로딩 일반」은 [22번](../22-operator-overloading/)이, 「오버로드 해결」은 [1번](../01-function-overloading-and-overload-resolution/)이 정본이다.\
> 「비교 계약의 일반론(반사·대칭·추이)」은 Rust·Python 갈래가 계약 위반까지 실측했다 — 여기서는 **C++20 이 무엇을 생성하나**만 본다.
> **대비** — ★★★ Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **28번**([`28-partialeq-eq-partialord-ord-and-hash-contracts/`](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/)) —\
> **`derive(PartialOrd, Ord)` 가 필드 순서 사전식**이고 **대칭은 자동으로 안 생긴다**((10) E0369)는 실측을 (5)(6)에서 인용한다.\
> ★★ Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **31번**([`31-comparison-protocol-and-sortability/`](../../../python/syntax/31-comparison-protocol-and-sortability/)) —\
> **`__lt__` 하나로 `sorted` 가 되고 `total_ordering` 이 나머지를 채우며, `max` 는 `__gt__` 를 부른다**는 실측을 (2)에서 인용한다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 두 컴파일러의 **진단 문구** | ★★★ **어느 연산자 함수가 불렸나**(`<=>` 인가 `==` 인가 · 인자 순서) — 이 주제의 답 자체다 |
> | 지역 레이블 이름(`.L9` · `.LBB0_3`) | ★★★ **`static_assert` 가 통과하나** · **비교 결과 0/1** |
> | — | ★★ **어셈블리 명령 수 · 두 판이 글자로 같은가** · **`cc exit`/`run exit`** · **에러 개수** |

## 한눈에 — 쉽게 말하면

**`<=>` 는 「저울 하나」이고, 여섯 비교 연산자는 그 저울의 눈금을 읽는 법이다.**

옛날 가게에는 「**더 무겁나**」 전용 저울, 「**더 가볍나**」 전용 저울, 「**같나**」 전용 저울이 따로 있었다 — 여섯 개를 **각각 손으로** 맞춰야 했고, 하나라도 어긋나면 가게가 거짓말을 한다.\
C++20 은 **저울 하나**(`<=>`)만 두고, 「더 가볍나?」라고 물으면 **저울 바늘이 0 보다 왼쪽인가**로 읽는다(`(a <=> b) < 0`).

★ 그런데 **「같나」는 저울로 안 잰다.** 무게가 같다고 **같은 물건**은 아니고, 같은지만 볼 거면 **끝까지 저울질할 필요도 없다**(첫 글자가 다르면 끝이다).\
그래서 **`==` 는 따로 만든다** — 저울을 `= default` 로 들이면 **`==` 도 같이 딸려 오고**, 저울을 **손으로 만들면 `==` 는 안 딸려 온다.**

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 저울 하나 | ★★★ **`operator<=>`** | (1) |
| 바늘이 0 보다 왼쪽인가 | ★★★ **재작성** — `a < b` → `(a <=> b) < 0` | (2) |
| 「같나」는 따로 본다 | ★★★ **`==` 는 `<=>` 에서 안 생긴다** — `= default` 일 때만 딸려 온다 | (2)(3) |
| 저울을 반대편에서 봐도 된다 | ★★★ **뒤집힌 재작성** — `1 < a` → `0 < (a <=> 1)` | (6) |
| 「정확히 같음」·「같은 급」·「비교 불가도 있음」 | ★★ **`strong`·`weak`·`partial_ordering`** | (4) |
| 가장 거친 저울에 맞춘다 | ★★ **`auto` 는 멤버 중 가장 약한 범주** | (4) |
| 먼저 적힌 것부터 잰다 | ★★ **선언 순서 사전식** | (5) |

```text
   struct P { int x, y;  auto operator<=>(const P&) const = default; };

   a <  b    ->  (a <=> b) <  0        ★ 관계 넷은 <=> 로 다시 써진다
   a <= b    ->  (a <=> b) <= 0
   a >  b    ->  (a <=> b) >  0
   a >= b    ->  (a <=> b) >= 0
   a == b    ->  operator==(a, b)      ★ = default 인 <=> 가 「암묵 선언」해 준 == — <=> 를 부르지 않는다
   a != b    ->  !(a == b)             ★ != 는 == 로 다시 써진다
```

## 이 주제가 답하려는 질문

1. ★★★ **`<=> = default` 한 줄이 정확히 무엇을 생성하나** — 여섯 연산자가 **어디로 다시 써지나**, 그리고 **`==` 는 어디서 오나**((1)(2)(3)).
2. **반환 타입은 무엇으로 정해지나** — `strong`/`weak`/`partial_ordering`, 그리고 `double` 멤버의 NaN((4)).
3. ★★★ **22편의 대칭 문제를 `<=>` 가 푸나**((6)).
4. **C++17 로는 어떻게 되고, 옛 `<`·`==` 만 가진 멤버는 어떻게 되나**((7)(8)).
5. **`= default` 판과 손으로 쓴 판이 기계어에서 같아지나**((9)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① 호출 로그다

★★★ **이 주제의 본체는 ① 호출 로그다** — 「재작성된다」는 **출력으로 증명할 수 있는 문법 성질**이다.\
★ `<=>` 와 `==` 에 **로그를 심고** `a < b`·`a == b`·`5000 < a` 가 **무엇을 불렀는지** 찍는다.

```text
① ★ 호출 로그           <, ==, 1 < a 가 무엇을 불렀나                    (2)(3)(6)(7)
② 두 컴파일러 대조       == 가 없다 · C++17 · <compare> 없음 · auto 가 지워짐 (2)(7)(8)
③ ASan                   —                                                  부적용
④ -O2 어셈블리           = default 판 대 손으로 쓴 판 — 같아지나            (9)
⑤ 경고 격자              bool 이 아닌 == — clang 만 통과                    (10)
⑥ static_assert 격자     auto 가 무엇이 되나                               (4)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ★★★ **① 호출 로그** | ★★★ **본체** — `Part::operator==` 가 `a == b` 에서 불리고 **`<=>` 는 안 불린다** | **쓴다** |
| ② 두 컴파일러 대조 | `no match for 'operator=='` · C++17 파싱 · `<compare>` 누락 | **쓴다** |
| ③ ASan | ★ **부적용** — 메모리 오류가 없다 | **안 쓴다** |
| ★★ **④ `-O2` 어셈블리** | ★★ **썼다 — 답은 「대체로 같아지지 않았다」**(clang 의 `==` 만 한 글자도 같다) | **쓴다** |
| ⑤ 경고 격자 | `-Wrewrite-not-bool` — **clang 은 경고, g++ 는 에러** | **쓴다** |
| ⑥ `static_assert` 격자 | 네 타입의 `auto` 가 `strong`·`weak`·`partial`·`partial` | **쓴다** |

- ★★ **④ 는 「되면 창, 아니면 부적용」이 아니었다** — 잴 것은 있었고, **잰 결과가 「다르다」였다**. **「다르다」도 답**이다((9)).

### (1) ★★★ `<=> = default` 한 줄 — 여섯 연산자가 다 되나

**언제 쓰나** — 멤버를 차례로 비교하면 되는 값 타입을 만들 때마다.

```cpp
/* cmp01.cpp */
// <=> = default 한 줄 — 여섯 비교 연산자가 전부 되나
#include <compare>
#include <cstdio>

struct Ver {
    int major, minor;
    auto operator<=>(const Ver&) const = default;       // ★ 이 한 줄만 썼다
};

int main() {
    Ver a{1, 2}, b{1, 3};
    std::printf("a={1,2} b={1,3}\n");
    std::printf("  a <  b : %d   a <= b : %d\n", (int)(a < b),  (int)(a <= b));
    std::printf("  a >  b : %d   a >= b : %d\n", (int)(a > b),  (int)(a >= b));
    std::printf("  a == b : %d   a != b : %d\n", (int)(a == b), (int)(a != b));
    std::printf("  (a <=> b) < 0 : %d\n", (int)((a <=> b) < 0));
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic cmp01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a={1,2} b={1,3}
  a <  b : 1   a <= b : 1
  a >  b : 0   a >= b : 0
  a == b : 0   a != b : 1
  (a <=> b) < 0 : 1
```

- ★★★ **여섯이 전부 된다** — 소스에 `<`·`>`·`<=`·`>=`·`==`·`!=` 가 **하나도 없다.**
- ★★ **`(a <=> b) < 0` 이 `a < b` 와 같은 값**이다 — 그 식이 곧 재작성의 결과다((2)).
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic cmp01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a={1,2} b={1,3}
  a <  b : 1   a <= b : 1
  a >  b : 0   a >= b : 0
  a == b : 0   a != b : 1
  (a <=> b) < 0 : 1
```

### (2) ★★★ 재작성 후보 — 손으로 쓴 `<=>` 로 `<` 가 되나, `==` 도 되나

**언제 쓰나** — 비교 규칙이 멤버별 사전식이 아니라서 `<=>` 를 **손으로** 쓸 때. **이 절이 이 주제의 급소다.**

```cpp
/* cmp03.cpp */
// <=> 를 손으로 쓰면(= default 가 아니면) — 관계 연산자는 그것으로 다시 써지나, == 도 생기나
#include <algorithm>
#include <compare>
#include <cstdio>

struct Id {
    int v;
    std::strong_ordering operator<=>(const Id& o) const {      // ★ 손으로 썼다 — < 는 안 썼다
        std::printf("      Id::operator<=>  (%d, %d)\n", v, o.v);
        return v <=> o.v;
    }
};

int main() {
    Id a{1}, b{2};
    std::printf("(1) a < b\n");          std::printf("    결과 %d\n", (int)(a < b));
    std::printf("(2) a >= b\n");         std::printf("    결과 %d\n", (int)(a >= b));
    std::printf("(3) std::max(a, b)\n"); std::printf("    결과 %d\n", std::max(a, b).v);
#ifdef ASK_EQ
    bool eq = (a == b);                                     // 4. 같음 연산자
    (void)eq;
#endif
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic cmp03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) a < b
      Id::operator<=>  (1, 2)
    결과 1
(2) a >= b
      Id::operator<=>  (1, 2)
    결과 0
(3) std::max(a, b)
      Id::operator<=>  (1, 2)
    결과 2
```

- ★★★ **`a < b` 가 `Id::operator<=>` 를 부른다** — `operator<` 는 **어디에도 없다.** 재작성 후보 `(a <=> b) < 0` 이 뽑혔다.
- ★★★ **`a >= b` 도 같다** — 관계 연산자 넷이 **전부 `<=>` 하나**로 간다.
- ★★ **`std::max(a, b)` 도 `<=>` 를 부른다** — `std::max` 는 **`<` 로 비교**하고, 그 `<` 가 다시 `<=>` 로 써졌다.\
  ★★ **파이썬과 대비된다** — Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **31번**([`31-comparison-protocol-and-sortability/`](../../../python/syntax/31-comparison-protocol-and-sortability/)) 2절이 **`max` 가 `__gt__` 를 부르는 것**을 찍었다(CPython 구현).\
  C++ 의 `std::max` 는 **`<` 만** 쓴다(표준이 요구 조건을 `<` 로 적는다). **같은 이름 `max` 가 언어마다 다른 연산자에 기댄다.**

★★★ **같은 파일에서 `a == b` 를 켠다**(`-DASK_EQ`).

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DASK_EQ -fmax-errors=0 cmp03.cpp -o ex (cc exit=1) =====
cmp03.cpp: In function ‘int main()’:
cmp03.cpp:20:18: error: no match for ‘operator==’ (operand types are ‘Id’ and ‘Id’)
   20 |     bool eq = (a == b);                                     // 4. 같음 연산자
      |                ~ ^~ ~
      |                |    |
      |                Id   Id
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DASK_EQ -ferror-limit=0 cmp03.cpp -o ex (cc exit=1) =====
cmp03.cpp:20:18: error: invalid operands to binary expression ('Id' and 'Id')
   20 |     bool eq = (a == b);                                     // 4. 같음 연산자
      |                ~ ^  ~
1 error generated.
```

- ★★★ **`no match for 'operator=='`** — **`<=>` 를 손으로 쓰면 `==` 는 생기지 않는다.**\
  ★ 기준 소스 — `==` 의 암묵 선언은 **`= default` 로 정의된 `<=>`** 에만 붙는다.
- ★★★ **이유** — `==` 를 `<=>` 로 풀면 **끝까지 순서를 매겨야** 한다. 같은지만 알려면 **길이가 다르면 끝**(문자열·벡터)일 수 있는데, `<=>` 는 그 지름길을 모른다.\
  ★ 그래서 C++20 은 **`==` 를 `<=>` 에서 분리**했다 — 이것이 **「`==` 는 따로」 규칙**이다(설계 이유는 이 문서가 **잰 것이 아니다** — 제안서의 논증이다).

```text
   = default 가 아닌 <=> 를 쓰면

   a <  b   ->  (a <=> b) < 0     ★ 된다 — 재작성 후보
   a >= b   ->  (a <=> b) >= 0    ★ 된다
   a == b   ->  ???                ★ 에러 — == 후보가 없다. <=> 로는 다시 쓰지 않는다
   a != b   ->  !(a == b) ???      ★ 에러 — != 는 == 로만 다시 써진다
```

### (3) ★★★ `= default` 인 `<=>` 의 `==` 는 어디서 오나 — 멤버의 `==` 를 부른다

**언제 쓰나** — 「`= default` 면 `==` 도 `<=>` 로 계산하겠지?」를 점검할 때.

```cpp
/* cmp02.cpp */
// = default 인 <=> 가 == 를 어디서 가져오나 — 멤버의 <=> 와 == 에 각각 로그를 심는다
#include <compare>
#include <cstdio>

struct Part {
    int v;
    std::strong_ordering operator<=>(const Part& o) const {
        std::printf("      Part::operator<=>\n");  return v <=> o.v;
    }
    bool operator==(const Part& o) const {
        std::printf("      Part::operator==\n");   return v == o.v;
    }
};

struct Whole {
    Part p;
    auto operator<=>(const Whole&) const = default;   // == 는 적지 않았다
};

int main() {
    Whole a{{1}}, b{{2}};
    std::printf("(1) a <  b\n");   (void)(a <  b);
    std::printf("(2) a >= b\n");   (void)(a >= b);
    std::printf("(3) a == b\n");   (void)(a == b);
    std::printf("(4) a != b\n");   (void)(a != b);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic cmp02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) a <  b
      Part::operator<=>
(2) a >= b
      Part::operator<=>
(3) a == b
      Part::operator==
(4) a != b
      Part::operator==
```

- ★★★ **`a == b` 가 `Part::operator==` 를 부르고 `Part::operator<=>` 는 안 부른다.**\
  ★ `Whole` 에는 `==` 를 **적지 않았는데** `==` 가 있고, 그 `==` 는 **멤버별 `==`** 로 계산된다 — **`<=>` 의 결과를 0 과 견주지 않는다.**
- ★★★ **`a != b` 도 `Part::operator==`** 다 — `!=` 는 **`!(a == b)`** 로 다시 써진다.
- ★★ **`a <`·`a >=` 는 `Part::operator<=>`** 다 — 관계 넷만 `<=>` 로 간다.
- ★★★ **그래서 규칙은 이렇게 적는다** — 「`<=> = default` 가 **`== = default` 를 함께 암묵 선언**하고, 그 `==` 는 **멤버별 `==`** 를 쓴다」.\
  ★ 「`==` 가 `<=>` 에서 생긴다」로 외우면 **(2)의 에러**와 **이 로그**를 둘 다 설명 못 한다.
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic cmp02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) a <  b
      Part::operator<=>
(2) a >= b
      Part::operator<=>
(3) a == b
      Part::operator==
(4) a != b
      Part::operator==
```

```text
   Whole { Part p;  auto operator<=>(const Whole&) const = default; }

   <=> = default  ──┬──>  관계 넷 (<, <=, >, >=)   ->  멤버의 <=>
                    │
                    └──>  (암묵 선언)  bool operator==(const Whole&) const = default;
                                         ->  멤버의 ==     ★ <=> 를 거치지 않는다
                                         ->  != 는 !(==)
```

### (4) ★★ `strong`·`weak`·`partial_ordering` — `auto` 는 가장 약한 것으로

**언제 쓰나** — `double` 멤버나 대소문자를 무시하는 문자열처럼 **「같음」의 뜻이 약한 멤버**가 섞일 때.

```cpp
/* cmp04.cpp */
// <=> = default 의 반환 타입을 auto 로 두면 무엇이 되나 — 멤버 중 가장 약한 것으로 정해지나
#include <cmath>
#include <compare>
#include <cstdio>
#include <type_traits>

struct Nocase {                                   // 대소문자를 무시하는 글자 — weak_ordering
    char c;
    std::weak_ordering operator<=>(const Nocase& o) const {
        auto low = [](char x) { return (x >= 'A' && x <= 'Z') ? char(x + 32) : x; };
        return low(c) <=> low(o.c);
    }
    bool operator==(const Nocase& o) const { return (*this <=> o) == 0; }
};

struct I  { int a; int b;           auto operator<=>(const I&)  const = default; };
struct W  { int a; Nocase n;        auto operator<=>(const W&)  const = default; };
struct D  { int a; double d;        auto operator<=>(const D&)  const = default; };
struct WD { Nocase n; double d;     auto operator<=>(const WD&) const = default; };

static_assert(std::is_same_v<decltype(I{}  <=> I{}),  std::strong_ordering>);
static_assert(std::is_same_v<decltype(W{}  <=> W{}),  std::weak_ordering>);
static_assert(std::is_same_v<decltype(D{}  <=> D{}),  std::partial_ordering>);
static_assert(std::is_same_v<decltype(WD{} <=> WD{}), std::partial_ordering>);
#ifdef WRONG
static_assert(std::is_same_v<decltype(D{} <=> D{}), std::strong_ordering>);   // ★ 일부러 틀리게 적는다
#endif

int main() {
    D x{1, NAN}, y{1, 2.0};
    auto r = x <=> y;
    std::printf("(1) D{1,NaN} <=> D{1,2.0} 가 unordered 인가 : %d\n", (int)(r == std::partial_ordering::unordered));
    std::printf("(2) x < y %d · x > y %d · x == y %d · x != y %d\n",
                (int)(x < y), (int)(x > y), (int)(x == y), (int)(x != y));
    D z{1, NAN};
    std::printf("(3) 같은 NaN 끼리  z == z : %d\n", (int)(z == z));
    W u{1, {'a'}}, v{1, {'A'}};
    std::printf("(4) W{1,'a'} <=> W{1,'A'} 가 equivalent 인가 : %d · u == v : %d\n",
                (int)((u <=> v) == std::weak_ordering::equivalent), (int)(u == v));
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic cmp04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) D{1,NaN} <=> D{1,2.0} 가 unordered 인가 : 1
(2) x < y 0 · x > y 0 · x == y 0 · x != y 1
(3) 같은 NaN 끼리  z == z : 0
(4) W{1,'a'} <=> W{1,'A'} 가 equivalent 인가 : 1 · u == v : 1
```

- ★★★ **네 `static_assert` 가 통과했다** — `I`(int 둘) **`strong`** · `W`(int + `weak` 멤버) **`weak`** · `D`(int + `double`) **`partial`** · `WD`(`weak` + `double`) **`partial`**.\
  ★ 기준 소스 — `auto` 는 **`common_comparison_category_t`**, 곧 **멤버 결과 중 가장 약한 것**이다.
- ★★★ **`double` 이 있으면 `partial_ordering`** — **NaN 은 무엇과도 순서가 없기** 때문이다.\
  `(1)` 에서 `D{1,NaN} <=> D{1,2.0}` 이 **`unordered`** 이고, `(2)` 에서 **`<`·`>`·`==` 가 전부 0 · `!=` 만 1** 이다.
- ★★ **`(3)` 같은 NaN 끼리도 `z == z` 가 0** 이다 — **반사성이 없다.** `strong_ordering` 이 될 수 없는 이유다.
- ★★ **`(4)` 의 `weak` 는 「구별되지만 같은 급」이다** — `'a'` 와 `'A'` 가 **`equivalent`** 다. 값은 다르지만 순서로는 같다.

★★ **`static_assert` 가 정말 검사하는지** — 일부러 틀리게 적는다(`-DWRONG`).

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DWRONG -fmax-errors=0 cmp04.cpp -o ex (cc exit=1) =====
cmp04.cpp:26:20: error: static assertion failed
   26 | static_assert(std::is_same_v<decltype(D{} <=> D{}), std::strong_ordering>);   // ★ 일부러 틀리게 적는다
      |               ~~~~~^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DWRONG -ferror-limit=0 cmp04.cpp -o ex (cc exit=1) =====
cmp04.cpp:26:15: error: static assertion failed due to requirement 'std::is_same_v<std::partial_ordering, std::strong_ordering>'
   26 | static_assert(std::is_same_v<decltype(D{} <=> D{}), std::strong_ordering>);   // ★ 일부러 틀리게 적는다
      |               ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1 error generated.
```

- ★★★ **clang 은 실제 타입을 이름으로 짚는다** — `'std::is_same_v<std::partial_ordering, std::strong_ordering>'`. `D` 의 `<=>` 가 **`partial_ordering`** 이라는 것이 **진단으로** 한 번 더 증명됐다.
- ★ g++ 는 `static assertion failed` 만 낸다.

```text
   Rust 28편                     C++20 (이 편)

   PartialOrd   (NaN 이 끼면)     partial_ordering    ★ f64 · double 이 여기서 멈춘다
   Ord          (전순서)          strong_ordering     ★ i32 · int
   —                              weak_ordering       ★ Rust 표준 트레이트에는 짝이 없다 — 「구별되지만 같은 급」

   derive(PartialOrd)            auto <=> = default   ★ 둘 다 필드 선언 순서 사전식 — (5)
   f64 는 Ord 가 아니다(E0277)    double 멤버 -> partial ★ 둘 다 「타입이 약하면 전체가 약해진다」
```

- ★★★ **짝이 대부분 맞는다** — Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **28번**([`28-partialeq-eq-partialord-ord-and-hash-contracts/`](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/)) (5)가 **`f64` 는 `PartialOrd` 까지만** 오고 `sort()`·`BTreeMap` 이 **`Ord` 를 요구해 막힌다**는 것을 찍었다.\
  ★★ **차이** — Rust 는 **`Ord` 가 필요한 자리에서 컴파일 에러**로 막고, C++ 은 **`partial_ordering` 을 그대로 돌려준다** — `std::sort` 에 NaN 을 넣어도 **컴파일은 된다**(이 문서는 그 실행을 **던지지 않았다**).
- ★ **`weak_ordering` 에 해당하는 Rust 표준 트레이트는 없다** — 이 칸은 **대비가 성립하지 않는 자리**다.

### (5) ★★ 멤버 선언 순서대로 사전식 — 순서를 바꾸면 답이 바뀐다

```cpp
/* cmp05.cpp */
// = default 는 멤버를 선언 순서대로 사전식 비교한다 — 선언 순서만 바꾸면 결과가 바뀌나
#include <compare>
#include <cstdio>

struct DateYMD { int year, month, day;  auto operator<=>(const DateYMD&) const = default; };
struct DateDMY { int day, month, year;  auto operator<=>(const DateDMY&) const = default; };   // 순서만 바꿨다

int main() {
    // 같은 두 날짜 — 2024-12-31 과 2025-01-01
    DateYMD a{2024, 12, 31}, b{2025, 1, 1};
    DateDMY c{31, 12, 2024}, d{1, 1, 2025};
    std::printf("(1) year,month,day 순서 — 2024-12-31 < 2025-01-01 : %d\n", (int)(a < b));
    std::printf("(2) day,month,year 순서 — 2024-12-31 < 2025-01-01 : %d\n", (int)(c < d));
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic cmp05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) year,month,day 순서 — 2024-12-31 < 2025-01-01 : 1
(2) day,month,year 순서 — 2024-12-31 < 2025-01-01 : 0
```

- ★★★ **같은 두 날짜인데 답이 1 과 0 이다** — `DateDMY` 는 **`day` 부터** 비교해 `31 < 1` 이 거짓이 됐다.
- ★★ **`= default` 는 「무엇이 큰가」를 모른다** — **선언 순서**가 곧 비교 순서다(기준 소스 ④). **멤버를 재배치하는 리팩터링이 비교 결과를 조용히 바꾼다.**
- ★★ **Rust 도 같다** — 28편 (8) 「`derive(PartialOrd)`·`derive(Ord)` 는 사전식이다 — 구조체는 **필드 순서**」.
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic cmp05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) year,month,day 순서 — 2024-12-31 < 2025-01-01 : 1
(2) day,month,year 순서 — 2024-12-31 < 2025-01-01 : 0
```

### (6) ★★★ 재작성 후보가 대칭을 푼다 — 22편의 `1 + a` 문제를 비교 연산자에서

**언제 쓰나** — 섞인 타입끼리 비교할 때. **22편 (1)과 같은 모양**이다 — 멤버 연산자, 오른쪽만 `long`.

```cpp
/* cmp06.cpp */
// 재작성 후보가 대칭까지 해 주나 — 22편의 「1 + a 가 막힌다」와 같은 모양을 <=> 로
#include <compare>
#include <cstdio>

struct Money {
    long won;
    std::strong_ordering operator<=>(long o) const {           // ★ 멤버 — 오른쪽만 long
        std::printf("      Money::operator<=>(long)  this=%ld o=%ld\n", won, o);
        return won <=> o;
    }
    bool operator==(long o) const {                             // ★ 멤버 — 오른쪽만 long
        std::printf("      Money::operator==(long)   this=%ld o=%ld\n", won, o);
        return won == o;
    }
};

int main() {
    Money a{1000};
    std::printf("(1) a < 5000\n");    std::printf("    결과 %d\n", (int)(a < 5000));
    std::printf("(2) 5000 < a\n");    std::printf("    결과 %d\n", (int)(5000 < a));
    std::printf("(3) 1000 == a\n");   std::printf("    결과 %d\n", (int)(1000 == a));
    std::printf("(4) 7 != a\n");      std::printf("    결과 %d\n", (int)(7 != a));
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic cmp06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) a < 5000
      Money::operator<=>(long)  this=1000 o=5000
    결과 1
(2) 5000 < a
      Money::operator<=>(long)  this=1000 o=5000
    결과 0
(3) 1000 == a
      Money::operator==(long)   this=1000 o=1000
    결과 1
(4) 7 != a
      Money::operator==(long)   this=1000 o=7
    결과 1
```

- ★★★ **`5000 < a` 가 된다** — 22편 (1)이었다면 **`int` 에게 멤버가 없어 에러**였을 자리다.
- ★★★ **로그가 증거다** — `(2)` 에서 불린 것은 **`this=1000 o=5000`**, 곧 **`a.operator<=>(5000)`** 이다. **인자가 뒤집혔다.**\
  ★ 재작성 후보에는 **뒤집힌 판**이 있다 — `5000 < a` → **`0 < (a <=> 5000)`**. **결과도 부호를 뒤집어 읽는다**(`0 <` 이므로 `a` 가 크면 참).
- ★★★ **`==` 도 뒤집힌다** — `1000 == a` 가 **`a.operator==(1000)`**(`this=1000 o=1000`), `7 != a` 가 **`!(a == 7)`**.
- ★★ **그래서 비교 연산자는 멤버로 둬도 대칭이다** — 22편의 「대칭 = 비멤버 × 암묵 변환」 표가 **비교 연산자에서는 바뀐다.**

```text
   22편 (1)                               23편 (6)
   멤버 operator+(long)                   멤버 operator<=>(long) · operator==(long)

   a + 1      a.operator+(1)       O      a < 5000    (a <=> 5000) < 0         O
   1 + a      1.operator+(a) ?     ✗      5000 < a    0 < (a <=> 5000)   ★ 뒤집힌 재작성  O
                                          1000 == a   a == 1000          ★ 뒤집힌 재작성  O
                                          7 != a      !(a == 7)                           O

   ★ 산술 연산자에는 재작성이 없다 — + 는 여전히 22편의 규칙을 따른다
```

- ★★★ **Rust 와 정반대다** — 28편 (10)이 `Inch(1.0) == Cm(2.54)` 는 되는데 **반대 방향 `Cm(2.54) == Inch(1.0)` 은 E0369** 인 것을 찍었다.\
  ★ Rust 는 「**대칭은 계약이지 문법이 아니다**」 — **`impl` 을 둘 다 써야** 한다. **C++20 은 언어가 뒤집어 준다.**\
  ★★ 대신 C++ 은 **뒤집힌 판과 원래 판이 모호해지는** 자리가 새로 생긴다(두 방향을 다 손으로 쓴 경우 등) — **이 문서는 그 모호성을 던지지 않았다.**
- ★★ **파이썬은 이 자리를 「반사 연산」으로 푼다** — Python 갈래 **31번** 3절이 `a < b` 가 안 되면 **`b.__gt__(a)`** 로 **거꾸로 묻는 것**을 찍었다.\
  ★ 파이썬은 **다른 메서드(`__gt__`)** 로 뒤집고, C++20 은 **같은 `<=>` 의 결과 부호**를 뒤집어 읽는다. **뒤집는 단위가 다르다.**
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic cmp06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) a < 5000
      Money::operator<=>(long)  this=1000 o=5000
    결과 1
(2) 5000 < a
      Money::operator<=>(long)  this=1000 o=5000
    결과 0
(3) 1000 == a
      Money::operator==(long)   this=1000 o=1000
    결과 1
(4) 7 != a
      Money::operator==(long)   this=1000 o=7
    결과 1
```

### (7) ★★ `<` 와 `==` 만 가진 옛 타입이 멤버면 — `auto` 는 지워지고 반환 타입을 적으면 산다

**언제 쓰나** — C++17 식 타입(`<`·`==` 만 있음)을 멤버로 든 새 타입에 `<=> = default` 를 쓸 때.

```cpp
/* cmp09.cpp */
// 멤버가 <=> 없이 < 와 == 만 가진 옛 타입이면 — auto 는 지워지고, 반환 타입을 적으면 살아나나
#include <compare>
#include <cstdio>

struct Legacy {                                   // C++17 식 — < 와 == 만 있다
    int v;
    bool operator< (const Legacy& o) const { std::printf("      Legacy::operator<\n");  return v <  o.v; }
    bool operator==(const Legacy& o) const { std::printf("      Legacy::operator==\n"); return v == o.v; }
};

struct Named {                                    // ★ 반환 타입을 적었다
    Legacy l;
    std::strong_ordering operator<=>(const Named&) const = default;
};

#ifdef AUTO
struct Guess {                                    // ★ auto 로 두었다
    Legacy l;
    auto operator<=>(const Guess&) const = default;
};
bool try_auto(const Guess& a, const Guess& b) { return a < b; }
#endif

int main() {
    Named a{{1}}, b{{2}};
    std::printf("(1) Named a < b\n");  std::printf("    결과 %d\n", (int)(a < b));
    std::printf("(2) Named b < a\n");  std::printf("    결과 %d\n", (int)(b < a));
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic cmp09.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) Named a < b
      Legacy::operator==
      Legacy::operator<
    결과 1
(2) Named b < a
      Legacy::operator==
      Legacy::operator<
    결과 0
```

- ★★★ **반환 타입을 `std::strong_ordering` 으로 적은 `Named` 는 된다** — 로그가 **`Legacy::operator==` → `Legacy::operator<`** 다.\
  ★ 기준 소스 ⑤ — **`a == b ? equal : a < b ? less : greater`** 로 **합성**했다. 로그의 순서가 그 식의 순서다.

```text
   Named { Legacy l;  std::strong_ordering operator<=>(const Named&) const = default; }

   a < b  ->  (a <=> b) < 0
              a <=> b  ->  멤버 l 에 <=> 가 없다  ->  ★ 합성
                           a.l == b.l ?  equal            <- 로그 1줄째  Legacy::operator==
                         : a.l <  b.l ?  less             <- 로그 2줄째  Legacy::operator<
                         :               greater

   auto 로 두면  ->  「어느 범주로 합성할지」를 모른다  ->  <=> 가 지워진다(deleted)
```

★★ **`auto` 로 두면**(`-DAUTO`).

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DAUTO -fmax-errors=0 cmp09.cpp -o ex (cc exit=1) =====
cmp09.cpp: In function ‘bool try_auto(const Guess&, const Guess&)’:
cmp09.cpp:21:60: error: use of deleted function ‘constexpr auto Guess::operator<=>(const Guess&) const’
   21 | bool try_auto(const Guess& a, const Guess& b) { return a < b; }
      |                                                            ^
cmp09.cpp:19:10: note: ‘constexpr auto Guess::operator<=>(const Guess&) const’ is implicitly deleted because the default definition would be ill-formed:
   19 |     auto operator<=>(const Guess&) const = default;
      |          ^~~~~~~~
cmp09.cpp:18:12: error: no match for ‘operator<=>’ (operand types are ‘Legacy’ and ‘Legacy’)
   18 |     Legacy l;
      |            ^
cmp09.cpp:19:10: note: changing the return type from ‘auto’ to a comparison category type will allow the comparison to use ‘operator<’ and ‘operator==’
   19 |     auto operator<=>(const Guess&) const = default;
      |          ^~~~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DAUTO -ferror-limit=0 cmp09.cpp -o ex (cc exit=1) =====
cmp09.cpp:19:10: warning: explicitly defaulted three-way comparison operator is implicitly deleted [-Wdefaulted-function-deleted]
   19 |     auto operator<=>(const Guess&) const = default;
      |          ^
cmp09.cpp:18:12: note: defaulted 'operator<=>' is implicitly deleted because there is no viable three-way comparison function for member 'l'
   18 |     Legacy l;
      |            ^
cmp09.cpp:19:44: note: replace 'default' with 'delete'
   19 |     auto operator<=>(const Guess&) const = default;
      |                                            ^~~~~~~
      |                                            delete
cmp09.cpp:21:58: error: object of type 'const Guess' cannot be compared because its 'operator<=>' is implicitly deleted
   21 | bool try_auto(const Guess& a, const Guess& b) { return a < b; }
      |                                                          ^
cmp09.cpp:19:10: note: explicitly defaulted function was implicitly deleted here
   19 |     auto operator<=>(const Guess&) const = default;
      |          ^
cmp09.cpp:18:12: note: defaulted 'operator<=>' is implicitly deleted because there is no viable three-way comparison function for member 'l'
   18 |     Legacy l;
      |            ^
1 warning and 1 error generated.
```

- ★★★ **`auto` 판은 `<=>` 가 암묵적으로 지워진다** — `Legacy` 에 `<=>` 가 없으니 **범주를 추론할 수 없다.**
- ★★★ **g++ 가 처방까지 말한다** — `changing the return type from 'auto' to a comparison category type will allow the comparison to use 'operator<' and 'operator=='`.
- ★★ **clang 은 선언 자리에서 경고를 먼저 낸다** — `-Wdefaulted-function-deleted` · `replace 'default' with 'delete'`. **쓰기 전에** 알 수 있다.
- ★ **이 합성은 `==` 와 `<` 가 서로 맞는다고 믿는다** — 둘이 어긋나면 **틀린 순서를 그대로** 만든다(계약 위반 실험은 Rust 28편 (3)(4)가 했다).

### (8) ★ C++17 로 던지면 · `<compare>` 를 빼면

```cpp
/* cmp07.cpp */
// 같은 <=> = default 를 -std=c++17 로 던진다
#include <compare>
#include <cstdio>

struct Ver {
    int major, minor;
    auto operator<=>(const Ver&) const = default;
};

int main() {
    Ver a{1, 2}, b{1, 3};
    std::printf("%d\n", (int)(a < b));
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -fmax-errors=0 cmp07.cpp -o ex (cc exit=1) =====
cmp07.cpp:7:10: error: declaration of ‘operator<=’ as non-function
    7 |     auto operator<=>(const Ver&) const = default;
      |          ^~~~~~~~
cmp07.cpp:7:18: error: expected ‘;’ at end of member declaration
    7 |     auto operator<=>(const Ver&) const = default;
      |                  ^~
      |                    ;
cmp07.cpp:7:20: error: expected unqualified-id before ‘>’ token
    7 |     auto operator<=>(const Ver&) const = default;
      |                    ^
cmp07.cpp: In function ‘int main()’:
cmp07.cpp:12:33: error: no match for ‘operator<’ (operand types are ‘Ver’ and ‘Ver’)
   12 |     std::printf("%d\n", (int)(a < b));
      |                               ~ ^ ~
      |                               |   |
      |                               Ver Ver
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -ferror-limit=0 cmp07.cpp -o ex (cc exit=1) =====
cmp07.cpp:7:18: warning: '<=>' is a single token in C++20; add a space to avoid a change in behavior [-Wc++20-compat]
    7 |     auto operator<=>(const Ver&) const = default;
      |                  ^ 
      |                     
cmp07.cpp:7:10: error: 'operator<=' cannot be the name of a variable or data member
    7 |     auto operator<=>(const Ver&) const = default;
      |          ^
cmp07.cpp:7:20: error: expected ';' at end of declaration list
    7 |     auto operator<=>(const Ver&) const = default;
      |                    ^
      |                    ;
cmp07.cpp:12:33: error: invalid operands to binary expression ('Ver' and 'Ver')
   12 |     std::printf("%d\n", (int)(a < b));
      |                               ~ ^ ~
1 warning and 3 errors generated.
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic cmp07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
1
```

- ★★★ **C++17 은 `<=>` 를 한 토큰으로 읽지 않는다** — `<=` 와 `>` 로 쪼개 **`operator<=` 라는 이름의 변수**로 읽는다(g++ `declaration of 'operator<=' as non-function`).

```text
   auto operator<=>(const Ver&) const = default;

   C++20   auto  operator<=>  ( const Ver& ) const = default ;       ★ <=> 가 한 토큰
   C++17   auto  operator<=   >  ( const Ver& ) …                     ★ <= 와 > 두 토큰
                 └ 「operator<= 라는 이름」 뒤에 > 가 와서 함수 선언이 안 된다
```
- ★★ **clang 이 먼저 경고한다** — `'<=>' is a single token in C++20; add a space to avoid a change in behavior`. **토큰화가 판에 따라 바뀐다**는 경고다.
- ★ **같은 파일이 `-std=c++20` 이면 된다**(`1`).

★ **`<compare>` 를 빼면 `-std=c++20` 이어도 안 된다.**

```cpp
/* cmp08.cpp */
// 같은 코드에서 #include <compare> 만 뺐다 — -std=c++20 인데 되나
#include <cstdio>

struct Ver {
    int major, minor;
    auto operator<=>(const Ver&) const = default;
};

int main() {
    Ver a{1, 2}, b{1, 3};
    std::printf("%d\n", (int)(a < b));
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 cmp08.cpp -o ex 2>&1 | sed -n '1,8p' (cc exit=1) =====
cmp08.cpp: In member function ‘constexpr auto Ver::operator<=>(const Ver&) const’:
cmp08.cpp:6:10: error: ‘strong_ordering’ is not a member of ‘std’
    6 |     auto operator<=>(const Ver&) const = default;
      |          ^~~~~~~~
cmp08.cpp:3:1: note: ‘std::strong_ordering’ is defined in header ‘<compare>’; did you forget to ‘#include <compare>’?
    2 | #include <cstdio>
  +++ |+#include <compare>
    3 | 
===== echo "g++ 에러 $(g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 cmp08.cpp -o ex 2>&1 | grep -c 'error:')건" (exit=0) =====
g++ 에러 7건
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 cmp08.cpp -o ex (cc exit=1) =====
cmp08.cpp:6:5: error: cannot default 'operator<=>' because type 'std::strong_ordering' was not found; include <compare>
    6 |     auto operator<=>(const Ver&) const = default;
      |     ^
1 error generated.
```

- ★★ **`<=>` 의 결과 타입(`std::strong_ordering`)은 라이브러리 헤더에 있다** — **언어 기능인데 헤더가 없으면 못 쓴다.**\
  ★ clang 은 한 줄로 **`include <compare>`** 를 권하고, g++ 는 **에러 7건**으로 번진다.
- ★ 다른 표준 헤더(`<string>` 등)가 `<compare>` 를 **끌어오는 판**에서는 우연히 되기도 한다 — **이 문서는 그 경우를 던지지 않았다.**

### (9) ★★ `-O2` 어셈블리 — `= default` 판과 손으로 쓴 판이 같아지나

**언제 쓰나** — 「`= default` 는 손으로 쓴 것보다 느리지 않나?」를 **명령으로** 확인할 때.

```cpp
/* cmp11.cpp */
// <=> = default 판과 손으로 쓴 판 — -O2 어셈블리가 같아지나
#include <compare>

struct P {                                                   // <=> 한 줄
    int a, b, c;
    auto operator<=>(const P&) const = default;
};
struct Q {                                                   // 손으로 쓴 사전식 < 와 ==
    int a, b, c;
    bool operator<(const Q& o) const {
        if (a != o.a) return a < o.a;
        if (b != o.b) return b < o.b;
        return c < o.c;
    }
    bool operator==(const Q& o) const { return a == o.a && b == o.b && c == o.c; }
};

extern "C" {
bool lt_default(const P& x, const P& y) { return x <  y; }
bool lt_hand   (const Q& x, const Q& y) { return x <  y; }
bool eq_default(const P& x, const P& y) { return x == y; }
bool eq_hand   (const Q& x, const Q& y) { return x == y; }
}
```

```bash
# cmp-asm.sh
# <=> = default 판과 손으로 쓴 판 — cmp11.cpp 의 네 함수를 -O2 로 내려 명령 수를 세고 두 판을 글자로 견준다
# 명령 = 탭으로 시작하는 줄 · 분기 = j 로 시작하는 명령 · 비교 = cmp/xor 로 시작하는 명령
# 견줄 때는 .L 로 시작하는 지역 레이블 이름만 .L 로 지운다(이름이 달라도 같은 코드일 수 있다)
set -u -o pipefail
body() { awk -v f="$1:" '$1 == f { on = 1; next } on && /^\.LFE|^\.Lfunc_end/ { exit } on' "$2" | sed -E 's/\.L[A-Za-z0-9_]+/.L/g; s/[[:space:]]*#.*$//'; }
for cc in g++ clang++; do
  echo "[$cc -O2]"
  $cc -std=c++20 -O2 -S -fno-asynchronous-unwind-tables -fcf-protection=none -o cmp11.s cmp11.cpp || exit 1
  awk '
    /^(lt|eq)_[a-z]*:/        { name = $1; sub(":", "", name); n = 0; br = 0; cm = 0; next }
    name == ""                { next }
    /^\t[a-z]/                { n++; if ($1 ~ /^j/) br++; if ($1 ~ /^(cmp|xor)/) cm++ }
    /^\.LFE|^\.Lfunc_end/     { printf "  %-11s 명령 %2d · 분기 %d · 비교/xor %d\n", name, n, br, cm; name = "" }' cmp11.s
  for op in lt eq; do
    if [ "$(body ${op}_default cmp11.s)" = "$(body ${op}_hand cmp11.s)" ]; then v="한 글자도 같다"; else v="다르다"; fi
    echo "  ${op}_default 대 ${op}_hand : $v"
  done
done
rm -f cmp11.s
```

```text
===== bash cmp-asm.sh (exit=0) =====
[g++ -O2]
  lt_default  명령 19 · 분기 3 · 비교/xor 4
  lt_hand     명령 12 · 분기 2 · 비교/xor 3
  eq_default  명령 12 · 분기 1 · 비교/xor 4
  eq_hand     명령 12 · 분기 2 · 비교/xor 4
  lt_default 대 lt_hand : 다르다
  eq_default 대 eq_hand : 다르다
[clang++ -O2]
  lt_default  명령 12 · 분기 2 · 비교/xor 3
  lt_hand     명령 10 · 분기 2 · 비교/xor 3
  eq_default  명령  7 · 분기 0 · 비교/xor 2
  eq_hand     명령  7 · 분기 0 · 비교/xor 2
  lt_default 대 lt_hand : 다르다
  eq_default 대 eq_hand : 한 글자도 같다
```

```text
===== g++ -std=c++20 -O2 -S -fno-asynchronous-unwind-tables -fcf-protection=none -o - cmp11.cpp | awk '/^(lt|eq)_[a-z]*:/{f=1} f{print} /^\.LFE|^\.Lfunc_end/{f=0}' | grep -vE '^\s*\.(size|p2align|type|globl|cfi)|^\.LF[BE]|^\.Lfunc_end|^# %bb|^\s*#' (exit=0) =====
lt_default:
	movl	(%rdi), %edx
	movl	(%rsi), %eax
	cmpl	%eax, %edx
	setl	%cl
	je	.L9
.L1:
	movl	%ecx, %eax
	ret
.L9:
	movl	4(%rdi), %edx
	movl	4(%rsi), %eax
	cmpl	%eax, %edx
	setl	%cl
	jne	.L1
	movl	8(%rsi), %eax
	xorl	%ecx, %ecx
	cmpl	%eax, 8(%rdi)
	je	.L1
	setl	%cl
	movl	%ecx, %eax
	ret
lt_hand:
	movl	(%rsi), %eax
	cmpl	%eax, (%rdi)
	jne	.L14
	movl	4(%rsi), %eax
	cmpl	%eax, 4(%rdi)
	je	.L13
.L14:
	setl	%al
	ret
.L13:
	movl	8(%rsi), %eax
	cmpl	%eax, 8(%rdi)
	setl	%al
	ret
eq_default:
	movl	(%rsi), %ecx
	xorl	%eax, %eax
	cmpl	%ecx, (%rdi)
	jne	.L15
	movl	4(%rsi), %eax
	cmpl	%eax, 4(%rdi)
	movl	8(%rsi), %edx
	sete	%al
	cmpl	%edx, 8(%rdi)
	sete	%dl
	andl	%edx, %eax
.L15:
	ret
eq_hand:
	movl	(%rsi), %edx
	xorl	%eax, %eax
	cmpl	%edx, (%rdi)
	je	.L22
.L18:
	ret
.L22:
	movl	4(%rsi), %ecx
	cmpl	%ecx, 4(%rdi)
	jne	.L18
	movl	8(%rsi), %eax
	cmpl	%eax, 8(%rdi)
	sete	%al
	ret
```

```text
===== clang++ -std=c++20 -O2 -S -fno-asynchronous-unwind-tables -fcf-protection=none -o - cmp11.cpp | awk '/^(lt|eq)_[a-z]*:/{f=1} f{print} /^\.LFE|^\.Lfunc_end/{f=0}' | grep -vE '^\s*\.(size|p2align|type|globl|cfi)|^\.LF[BE]|^\.Lfunc_end|^# %bb|^\s*#' (exit=0) =====
lt_default:                             # @lt_default
	movl	(%rdi), %eax
	cmpl	(%rsi), %eax
	setl	%al
	jne	.LBB0_3
	movl	4(%rdi), %eax
	cmpl	4(%rsi), %eax
	setl	%al
	jne	.LBB0_3
	movl	8(%rdi), %eax
	cmpl	8(%rsi), %eax
	setl	%al
.LBB0_3:
	retq
lt_hand:                                # @lt_hand
	movl	(%rsi), %eax
	cmpl	%eax, (%rdi)
	jne	.LBB1_3
	movl	4(%rsi), %eax
	cmpl	%eax, 4(%rdi)
	jne	.LBB1_3
	movl	8(%rdi), %eax
	cmpl	8(%rsi), %eax
.LBB1_3:
	setl	%al
	retq
eq_default:                             # @eq_default
	movq	(%rdi), %rax
	xorq	(%rsi), %rax
	movl	8(%rdi), %ecx
	xorl	8(%rsi), %ecx
	orq	%rax, %rcx
	sete	%al
	retq
eq_hand:                                # @eq_hand
	movq	(%rdi), %rax
	xorq	(%rsi), %rax
	movl	8(%rdi), %ecx
	xorl	8(%rsi), %ecx
	orq	%rax, %rcx
	sete	%al
	retq
```

| | g++ `-O2` | clang `-O2` |
|---|---|---|
| `<` — `= default` 대 손 | ★★ **명령 19 대 12 · 다르다** | ★★ **12 대 10 · 다르다** |
| `==` — `= default` 대 손 | ★★ **12 대 12 · 다르다** | ★★★ **7 대 7 · 한 글자도 같다** |

- ★★★ **같아진 것은 clang 의 `==` 하나뿐이다** — 두 판 다 **`movq`·`xorq`·`orq`·`sete`** 로 **분기 없이** 비교했다.
- ★★ **`<` 는 두 컴파일러 다 달랐다** — `= default` 판은 **`<=>` 의 결과(음·영·양)를 거쳐** `< 0` 을 보고, 손으로 쓴 판은 `<` 를 **바로** 본다. 최적화가 **그 차이를 다 지우지 못했다.**
- ★★ **g++ 의 `==` 는 분기 모양이 다르다** — `= default` 판은 **분기 1 · 끝의 둘을 `andl` 로** 묶고, 손 판은 `&&` 를 **분기 2** 로 풀었다.
- ★★★ **이 표가 말하는 것은 「명령이 다르다」까지다** — **「그래서 느리다」가 아니다.** 명령 수는 시간이 아니고, **시간은 재지 않았다.**\
  ★ 손으로 쓴 판을 **다르게 쓰면**(예: `std::tie`) 결과가 또 바뀔 수 있다 — 이 표는 **이 한 쌍**에 대한 것이다.

### (10) ★★ 종료 코드 0인데 ill-formed — `bool` 이 아닌 `==` 로 `!=` 를 다시 쓰게 하면

★★ **이 배치의 고정 항목**([14번](../14-destructors-and-deterministic-destruction/) (8) · [18번](../18-rule-of-zero-three-five-default-delete/) (7))의 새 항목이다.

```cpp
/* cmp10.cpp */
// operator== 가 bool 이 아니라 int 를 돌려준다 — 그 == 로 != 를 다시 써 달라고 하면
#include <cstdio>

struct Tag {
    int v;
    int operator==(const Tag& o) const { return v == o.v; }     // ★ 반환 타입이 int
};

int main() {
    Tag a{1}, b{2};
    std::printf("a == b : %d\n", a == b);          // 1. 직접 부른다 — 이것은 문제없다
    std::printf("a != b : %d\n", (int)(a != b));   // 2. != 는 == 로 다시 써진다
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 cmp10.cpp -o ex (cc exit=1) =====
cmp10.cpp: In function ‘int main()’:
cmp10.cpp:12:42: error: return type of ‘int Tag::operator==(const Tag&) const’ is not ‘bool’
   12 |     std::printf("a != b : %d\n", (int)(a != b));   // 2. != 는 == 로 다시 써진다
      |                                        ~~^~~~
cmp10.cpp:12:42: note: used as rewritten candidate for comparison of ‘Tag’ and ‘Tag’
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 cmp10.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
cmp10.cpp:12:42: warning: ISO C++20 requires return type of selected 'operator==' function for rewritten '!=' comparison to be 'bool', not 'int' [-Wrewrite-not-bool]
   12 |     std::printf("a != b : %d\n", (int)(a != b));   // 2. != 는 == 로 다시 써진다
      |                                        ~ ^  ~
cmp10.cpp:6:9: note: declared here
    6 |     int operator==(const Tag& o) const { return v == o.v; }     // ★ 반환 타입이 int
      |         ^
1 warning generated.
a == b : 0
a != b : 1
```

```text
===== echo "clang -pedantic-errors 에러 $(clang++ -std=c++20 -Wall -Wextra -pedantic-errors -ferror-limit=0 cmp10.cpp -o ex 2>&1 | grep -c 'error:')" (exit=0) =====
clang -pedantic-errors 에러 1
```

- ★★★ **두 컴파일러가 갈렸다** — **g++ 는 에러**(`return type of … is not 'bool'` · `used as rewritten candidate`), **clang 은 경고 1건 + `cc exit=0 · run exit=0`** 이고 값도 그럴듯하다(`a != b : 1`).
- ★★★ **clang 의 경고가 스스로 말한다** — `ISO C++20 requires return type of selected 'operator==' function for rewritten '!=' comparison to be 'bool'`. **표준이 요구하는 것을 안 지킨 코드를 통과시켰다.**
- ★★ **`-pedantic-errors` 로 clang 도 에러 1** — 앞 배치들의 항목과 [22번](../22-operator-overloading/) (8)과 **같은 집안**이다.
- ★ **1번 줄(`a == b` 직접)은 문제가 없다** — `int` 를 돌려주는 `==` 자체는 합법이다. **재작성에 쓰일 때만** `bool` 이어야 한다.

## 문법 — 형태와 규칙

### 형태

```cpp
/* cmp12.cpp */
// 3방향 비교 한 벌의 형태. 이 파일은 그대로 컴파일된다
#include <algorithm>
#include <compare>
#include <cstdio>
#include <string>
#include <utility>
#include <vector>

struct Version {                                  // ① 멤버별 사전식이면 = default 한 줄
    int major = 0, minor = 0, patch = 0;          //    ★ 선언 순서가 곧 비교 순서다
    auto operator<=>(const Version&) const = default;   // == 도 같이 생긴다
};

class Tag {                                       // ② 규칙이 다르면 손으로 쓴다 — 대소문자 무시
public:
    explicit Tag(std::string s) : s_(std::move(s)) {}
    std::weak_ordering operator<=>(const Tag& o) const {
        auto low = [](unsigned char c) { return (c >= 'A' && c <= 'Z') ? c + 32 : c; };
        return std::lexicographical_compare_three_way(s_.begin(), s_.end(), o.s_.begin(), o.s_.end(),
            [&](unsigned char a, unsigned char b) { return low(a) <=> low(b); });
    }
    bool operator==(const Tag& o) const { return (*this <=> o) == 0; }   // ★ 손으로 쓴 <=> 는 == 를 안 준다
    const std::string& str() const { return s_; }
private:
    std::string s_;
};

int main() {
    std::vector<Version> v{{1, 10, 0}, {1, 2, 3}, {0, 9, 9}};
    std::sort(v.begin(), v.end());
    for (const auto& x : v) std::printf("%d.%d.%d ", x.major, x.minor, x.patch);
    std::printf("\n");
    Tag a("Hello"), b("hello");
    std::printf("Tag == : %d · Tag < : %d\n", (int)(a == b), (int)(a < b));
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic cmp12.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
0.9.9 1.2.3 1.10.0 
Tag == : 1 · Tag < : 0
```

- ★★ **`std::sort` 가 `<=>` 로 정렬했다**(`0.9.9 1.2.3 1.10.0`) — `1.10.0` 이 `1.2.3` 뒤에 온 것은 **정수 비교**라서다(문자열이면 거꾸로다).
- ★★ **`Tag` 는 `<=>` 를 손으로 썼으므로 `==` 도 손으로 썼다**((2)).
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic cmp12.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
0.9.9 1.2.3 1.10.0 
Tag == : 1 · Tag < : 0
```

### 규칙

- ★★★ **멤버별 사전식이면 `auto operator<=>(const T&) const = default;` 한 줄** — `==` 도 같이 생긴다((1)(3)).
- ★★★ **`<=>` 를 손으로 쓰면 `==` 도 손으로 쓴다** — 안 생긴다((2)).
- ★★ **반환 타입을 `auto` 로 두면 멤버 중 가장 약한 범주** — `double` 이 있으면 **`partial_ordering`**((4)).
- ★★ **비교 순서 = 선언 순서** — 멤버 재배치가 결과를 바꾼다((5)).
- ★★ **옛 타입 멤버가 `<`·`==` 만 가졌으면 반환 타입을 범주로 적는다**((7)).
- ★ **`#include <compare>`** 를 잊지 않는다((8)).
- ★ **재작성에 쓰일 `==` 는 `bool` 을 돌려준다**((10)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | 무엇이 되나 | 어디서 |
|---|---|---|
| 손으로 쓴 `<=>` 만 두고 `a == b` | ★★★ **에러 1 · 1**(`no match for 'operator=='`) | (2) |
| `<`·`==` 만 가진 멤버 + `auto <=> = default` | ★★ **지워진 함수**(g++ 에러 2 · clang 경고 1 + 에러 1) | (7) |
| `-std=c++17` 에서 `operator<=>` | ★★ **에러 4 · 3**(`<=` 와 `>` 로 쪼갠다) | (8) |
| `<compare>` 없이 `<=> = default` | ★ **에러 7 · 1** | (8) |
| `int operator==` 를 `!=` 재작성에 | ★★ **g++ 에러 · clang 경고만(`cc exit=0`)** | (10) |

## 어디서 틀리나

### 1. ★★★ 「`==` 도 `<=>` 에서 만들어진다」

(2)(3)이 반증이다 — **손으로 쓴 `<=>` 는 `==` 를 안 주고**, `= default` 인 `<=>` 가 주는 `==` 도 **멤버의 `==` 를 부르지 `<=>` 를 부르지 않는다.**

### 2. ★★★ 「`<=>` 를 쓰면 `operator<` 를 컴파일러가 만들어 둔다」

(2)가 반증이다 — **`operator<` 라는 함수는 생기지 않는다.** `a < b` 를 풀 때 **재작성 후보**로 `(a <=> b) < 0` 을 고를 뿐이다.

### 3. ★★ 「`<=> = default` 는 늘 `strong_ordering`」

(4)가 반증이다 — **`double` 하나로 `partial_ordering`** 이 되고, NaN 이 끼면 **`<`·`>`·`==` 가 전부 거짓**이다.

### 4. ★★ 「멤버 순서는 스타일이다」

(5)가 반증이다 — **같은 두 날짜의 답이 1 과 0** 으로 갈렸다.

### 5. ★★★ 「비교 연산자도 멤버로 두면 `1 < a` 가 막힌다」

(6)이 반증이다 — **뒤집힌 재작성 후보**가 `0 < (a <=> 1)` 로 푼다. **22편의 규칙은 산술 연산자에만** 그대로 남는다.

### 6. ★★ 「`= default` 는 손으로 쓴 것과 기계어가 같다」

(9)가 반증이다 — **같아진 것은 clang 의 `==` 하나**다. 다만 **「그래서 느리다」도 이 문서의 결론이 아니다.**

### 7. ★ 「`<=>` 는 언어 기능이니 헤더가 필요 없다」

(8)이 반증이다 — **`<compare>` 가 없으면 `-std=c++20` 이어도 에러**다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 규칙 전부를 덮고, 「미명시」 칸에 기계어가 들어간다.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **관계 넷은 `<=>` 로 재작성**((2)) · ★★★ **`==` 는 `= default` 인 `<=>` 에서만 암묵 선언되고 멤버의 `==` 를 쓴다**((2)(3)) · **뒤집힌 재작성**((6)) · **`auto` = 가장 약한 범주**((4)) · **선언 순서**((5)) · **`<` 와 `==` 로 합성**((7)) · **재작성에 쓰일 `==` 는 `bool`**((10)) · **`<compare>` 필요**((8)) | 호출 로그 · `static_assert` · 진단 + `cc exit` | ★★★ 「**이 `a < b` 가 `<=>` 를 부르나**」 — 호출 자리만 보면 **안 보인다**(로그로만) |
| **조건부 표준** | 특정 판에서만 | ★★ **C++20부터** — C++17 은 `<=>` 를 **두 토큰으로** 읽는다((8)) | `-std=c++17`/`c++20` | ★ **C++17 판에서도 컴파일되는 모양을 우연히 만들 수 있다**(clang 경고 `-Wc++20-compat`) |
| **구현 정의** | 문서화 의무 | ★ **진단 문구** · **`strong_ordering` 의 내부 표현** | — | — |
| **미명시** | 몇 가지 중 하나 | ★★ **`= default` 판을 어떤 기계어로 내나**((9) — 두 컴파일러·두 연산자에서 결과가 갈렸다) | `-O2` 어셈블리 · 스크립트 | ★★ **판이 바뀌면 표가 바뀔 수 있다** |
| **UB** | 아무 일이나 | ★ **이 편의 규칙 자체에는 없다** — 다만 **`==` 와 `<` 가 어긋난 타입을 `std::sort` 에 넣는 것**은 표준 알고리즘의 요구 조건 위반이다(이 문서는 **던지지 않았다**) | — | ★ Rust 28편 (3)(4)가 **계약 위반의 결과**를 찍었다 |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | 호출 로그 |
|---|---|---|---|---|
| 손으로 쓴 `<=>` 로 `==` | 표준 | **error 1** | **error 1** | — |
| ★★★ **`= default` 의 `==` 가 `<=>` 를 안 부른다** | 표준 | ★★★ **0건**(물을 수 없다) | ★★★ **0건** | ★★★ **`Part::operator==`** |
| ★★★ **`5000 < a` 가 뒤집혀 `a <=> 5000`** | 표준 | ★★★ **0건** | ★★★ **0건** | ★★★ **`this=1000 o=5000`** |
| ★★ **`double` 멤버로 `partial_ordering`** | 표준 | 0건 | 0건 | `static_assert` · `unordered` 1 |
| ★★ **`bool` 이 아닌 `==` 로 `!=`** | 표준 | ★★ **error 1** | ★★ **warning 1** · `cc exit=0` | 값 `1` |
| ★ **`= default` 대 손 — 기계어** | 미명시 | — | — | ★ 어셈블리로만(스크립트) |

- ★★ **이 표의 결론** — ★★★ **재작성이 일어났다는 사실은 어떤 컴파일러 진단에도 안 나온다.** **로그를 심어야** 보인다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 멤버별 사전식 값 타입 | ★★★ **`auto operator<=>(const T&) const = default;`** | 여섯이 다 되고 `==` 도 딸려 온다((1)(3)) |
| 규칙이 다른 비교(대소문자 무시 등) | ★★ **`<=>` 를 손으로 + `==` 도 손으로** | `==` 가 안 생긴다((2)) |
| 같음만 필요하다 | ★ **`bool operator==(const T&) const = default;` 만** | `!=` 도 생긴다 — `<=>` 는 필요 없다 |
| `double` 멤버가 있다 | ★★ **`partial_ordering` 을 받아들이거나 반환 타입을 정한다** | NaN((4)) |
| 옛 타입을 멤버로 든다 | ★★ **반환 타입을 범주로 적는다** | `auto` 는 지워진다((7)) |
| 섞인 타입과 비교 | ★★ **멤버 `<=>(U)` 와 `==(U)` 하나씩** | 뒤집힌 재작성이 반대 방향을 준다((6)) |

## 핵심 문장

- ★★★ **`a < b` 는 `(a <=> b) < 0` 으로 다시 써진다** — `operator<` 는 어디에도 없는데 **`<=>` 의 로그**가 찍혔다.
- ★★★ **`==` 는 `<=>` 에서 안 생긴다** — 손으로 쓴 `<=>` 는 `==` 를 안 주고(에러), `= default` 인 `<=>` 가 주는 `==` 는 **멤버의 `==`** 를 불렀다.
- ★★ **`auto` 반환은 멤버 중 가장 약한 범주** — `double` 하나로 **`partial_ordering`**, NaN 이면 **`unordered`**.
- ★★ **비교 순서는 선언 순서** — 순서만 바꾼 두 구조체가 **같은 날짜에 1 과 0** 을 냈다.
- ★★★ **뒤집힌 재작성이 22편의 대칭 문제를 푼다** — `5000 < a` 가 **`a.operator<=>(5000)`** 을 불렀다.
- ★★ **`-O2` 에서 `= default` 판과 손 판은 대체로 같아지지 않았다** — 같은 것은 **clang 의 `==` 하나**. 시간은 안 쟀다.
- ★ **`bool` 이 아닌 `==` 로 `!=` 를 다시 쓰게 하면 clang 만 `cc exit=0`** 으로 통과시킨다.

## 관련 자료

- [22번](../22-operator-overloading/) — ★★★ **이 편의 사슬.** 그 편 (1)의 「`1 + a` 가 막힌다」를 이 편 (6)이 **비교 연산자에서는** 풀었다.
- [1번](../01-function-overloading-and-overload-resolution/) — **오버로드 해결.** 재작성 후보는 **후보 집합에 들어가는 방식**이 다를 뿐 그 절차를 탄다.
- ★★★ Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **28번**([`28-partialeq-eq-partialord-ord-and-hash-contracts/`](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/)) —\
  **`PartialOrd` ↔ `partial_ordering` · `Ord` ↔ `strong_ordering`**, 사전식 `derive`, **대칭이 자동이 아닌 것(E0369)** 을 (4)(5)(6)에서 인용했다. **계약 위반 실험은 그 편이 정본**이다.
- ★★ Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **31번**([`31-comparison-protocol-and-sortability/`](../../../python/syntax/31-comparison-protocol-and-sortability/)) — **`__lt__` 하나로 정렬 · `total_ordering` · `max` 가 `__gt__`**.\
  ★ 파이썬은 **`total_ordering` 이라는 라이브러리 데코레이터**가 나머지를 채우고, **C++20 은 언어가 재작성**한다. 같은 갈래 **30번**([`30-repr-eq-hash-contracts/`](../../../python/syntax/30-repr-eq-hash-contracts/))이 `__eq__` 의 계약을 본다.

## 용어 풀이

> **3방향 비교 연산자(`<=>`)** — 두 값의 순서를 **한 번에** 돌려주는 연산자. 결과는 **비교 범주 타입**이고 **0 과 견줘** 읽는다.\
> 예: (1)에서 `(a <=> b) < 0` 이 1 이었다.

> **재작성 후보(rewritten candidate)** — C++20 이 `a < b` 를 풀 때 **`(a <=> b) < 0`**, `a != b` 를 **`!(a == b)`** 로 바꿔 **후보에 넣는 것**.\
> 예: (2)에서 `operator<` 없이 `a < b` 가 `Id::operator<=>` 를 불렀다.

> **뒤집힌 후보(reversed candidate)** — 재작성 후보 중 **인자를 뒤집은 판**. `1 < a` → `0 < (a <=> 1)` · `1 == a` → `a == 1`.\
> 예: (6)에서 `5000 < a` 가 `this=1000 o=5000` 을 찍었다.

> **`strong_ordering`** — **같으면 바꿔 넣어도 구별이 안 되는** 순서. `int` 가 이것이다.\
> 예: (4)의 `I`.

> **`weak_ordering`** — **구별은 되지만 순서로는 같은 급**이 있는 순서. `equivalent` 를 쓴다.\
> 예: (4)에서 `'a'` 와 `'A'` 가 `equivalent`.

> **`partial_ordering`** — **순서가 없는 쌍**(`unordered`)이 있을 수 있는 순서. `double`(NaN)이 이것이다.\
> 예: (4)에서 `D{1,NaN} <=> D{1,2.0}` 이 `unordered`.

> **합성된 3방향 비교(synthesized three-way comparison)** — `<=>` 가 없는 멤버를 **`==` 와 `<` 로** 3방향 결과로 만드는 것. 반환 타입을 범주로 적었을 때만.\
> 예: (7)에서 `Legacy::operator==` → `Legacy::operator<` 순서로 불렸다.

## 더 들어가면

- **뒤집힌 후보와의 모호성** — 두 방향을 다 손으로 쓰거나 `const` 가 어긋나면 **원래 판과 뒤집힌 판이 모호**해지는 자리가 있다. 이 문서는 **던지지 않았다.**
- **`std::compare_three_way`·`std::strong_order`(전순서 `double`)** — Rust 28편 (7)의 `total_cmp` 와 짝이 되는 도구. 이 문서는 **던지지 않았다.**
- **`std::sort` 에 NaN 을 넣으면** — `partial_ordering` 을 돌려주는 타입은 **정렬의 요구 조건(엄격 약순서)** 을 못 지킨다. 결과는 이 문서가 **재지 않았다.**
- **기반 클래스가 있을 때의 `= default`** — 기준 소스 ④의 「**기반 먼저**」 순서. 이 문서는 **멤버만** 봤다.
