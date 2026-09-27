# cpp/syntax/23 — 3방향 비교 `<=>`(C++20) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이므로 **출력을 싣는 블록마다 그 출력을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **진단 문구** · **지역 레이블 이름**이다.\
> 근거로 쓰는 것은 다음이다 — **어느 연산자 함수가 불렸나 · 인자 순서** · **`static_assert` 통과** · **비교 결과 0/1** · **`cc exit`/`run exit`** · **에러 개수** · **명령 수와 글자 대조**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 셋 다 **`Id::operator<=>`** — `a == b` 는 **컴파일 에러** · `std::max` 는 **`<`** 에 기댄다

**출력**

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

**왜 그런가**

- ★★★ **`a < b` 가 된다** — `operator<` 는 없지만 **재작성 후보 `(a <=> b) < 0`** 이 뽑혔다. `a >= b` 도 같다.
- ★★★ **`a == b` 는 `no match for 'operator=='`** — **손으로 쓴 `<=>` 는 `==` 를 주지 않는다.** `==` 는 `<=>` 로 다시 쓰지 않는다.
- ★★ **`std::max` 는 `<` 로 비교**하고, 그 `<` 가 다시 `<=>` 로 써졌다. 파이썬의 `max` 가 `__gt__` 를 부르는 것(Python 31번 2절)과 **기대는 연산자가 다르다.**

### 2. ★★★ **`Part::operator==`** — `!=` 도 **`Part::operator==`** · `==` 는 **`<=>` 가 암묵 선언해 준 것**

**출력**

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

**왜 그런가**

- ★★★ **`a == b` 에서 `<=>` 는 안 불렸다** — `Whole` 의 `==` 는 **멤버별 `==`** 로 계산된다.
- ★★ **`a != b` 는 `!(a == b)`** — 역시 `Part::operator==` 다.
- ★★★ **컴파일되는 이유** — 기준 소스 ①: `==` 를 **명시적으로 선언하지 않았고** `<=>` 가 **`= default`** 이므로, **`bool operator==(const Whole&) const = default;` 가 암묵 선언**됐다.

### 3. ★★ **전부 통과** — `strong` · `weak` · `partial` · `partial` · NaN 이면 **`<` 0 · `>` 0 · `==` 0 · `!=` 1** · `z == z` 는 **0**

**출력**

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

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DWRONG -ferror-limit=0 cmp04.cpp -o ex (cc exit=1) =====
cmp04.cpp:26:15: error: static assertion failed due to requirement 'std::is_same_v<std::partial_ordering, std::strong_ordering>'
   26 | static_assert(std::is_same_v<decltype(D{} <=> D{}), std::strong_ordering>);   // ★ 일부러 틀리게 적는다
      |               ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1 error generated.
```

**왜 그런가**

- ★★ **`auto` 는 멤버 결과 중 가장 약한 범주**(`common_comparison_category_t`) — `double` 하나로 `partial`, `weak` 멤버 하나로 `weak`.
- ★★★ **NaN 은 `unordered`** — 순서 셋이 전부 거짓이고 **`!=` 만 참**이다. 같은 NaN 끼리도 **같지 않다.**
- ★★ **`-DWRONG` 의 clang 진단**이 실제 타입을 짚는다 — `is_same_v<std::partial_ordering, std::strong_ordering>`.

### 4. ★★ **다르다 — 1 과 0**

**출력**

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

**왜 그런가**

- ★★ **`= default` 는 선언 순서대로 사전식**이다 — `DateDMY` 는 **`day`(31 대 1)** 에서 이미 갈려 `2024-12-31 < 2025-01-01` 이 **거짓**이 됐다.
- ★ Rust 28편 (8)의 `derive(PartialOrd)` 도 **필드 순서 사전식**이다.

### 5. ★★★ **된다** — 로그는 **`this=1000 o=5000`**(인자가 뒤집혔다) · `==`·`!=` 도 **`a == 1000` · `!(a == 7)`**

**출력**

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

**왜 그런가**

- ★★★ **22편 (1)과 다르다** — 산술 `1 + a` 는 막혔지만, 비교 `5000 < a` 는 **뒤집힌 재작성 후보 `0 < (a <=> 5000)`** 으로 풀린다.
- ★★★ **`this=1000 o=5000`** 이 증거다 — 불린 것은 `5000.operator<=>(a)` 가 아니라 **`a.operator<=>(5000)`** 이다. 결과를 **`0 <` 로 뒤집어** 읽어 `0`(거짓)이 나왔다.
- ★★ **`1000 == a` → `a.operator==(1000)`**, **`7 != a` → `!(a.operator==(7))`** — `==` 도 뒤집힌다.

### 6. ★★ **된다 — `Legacy::operator==` 다음 `Legacy::operator<`** · `auto` 면 **지워진 함수** · g++ 가 **처방을 말한다**

**출력**

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

**왜 그런가**

- ★★★ **반환 타입을 범주로 적으면 합성**한다 — 기준 소스 ⑤ `a == b ? equal : a < b ? less : greater`. 로그가 **`==` → `<`** 순서다.
- ★★ **`auto` 면 범주를 추론할 수 없어** `<=>` 가 **암묵적으로 지워진다** — `use of deleted function`.
- ★ g++ note — `changing the return type from 'auto' to a comparison category type will allow the comparison to use 'operator<' and 'operator=='`.

### 7. ★ C++17 은 **`<=` 와 `>` 로 쪼개 읽는다** · `<compare>` 가 없으면 **`-std=c++20` 이어도 에러**

**출력**

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
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 cmp08.cpp -o ex (cc exit=1) =====
cmp08.cpp:6:5: error: cannot default 'operator<=>' because type 'std::strong_ordering' was not found; include <compare>
    6 |     auto operator<=>(const Ver&) const = default;
      |     ^
1 error generated.
```

**왜 그런가**

- ★★ **g++ `declaration of 'operator<=' as non-function`** — `<=>` 가 **토큰이 아니라** `<=` 뒤에 `>` 로 읽혔다. clang 은 `'<=>' is a single token in C++20` 경고를 먼저 낸다.
- ★ **`std::strong_ordering` 은 `<compare>` 에 있다** — 언어 기능이지만 **결과 타입이 헤더에** 있어서 헤더 없이는 못 쓴다.

### 8. ★★ **넷 중 하나**(clang 의 `==`) — **아니다**, 명령이 다르다는 것까지다

**출력**

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

**왜 그런가**

- ★★★ **글자로 같아진 것은 clang `eq_default` 대 `eq_hand` 한 쌍**이다. `<` 는 두 컴파일러 다 **달랐고**(19 대 12 · 12 대 10), g++ 의 `==` 도 **분기 모양이 달랐다.**
- ★★★ **「느리다」로 갈 수 없다** — 명령 수는 시간이 아니고, **시간은 재지 않았다.** 게다가 **손으로 쓴 판을 다르게 쓰면** 결과가 또 바뀔 수 있다.

### 9. ★★ **g++ `cc exit=1` · clang `cc exit=0`**(경고 1건) — 1번 줄은 **문제없다**

**출력**

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

**왜 그런가**

- ★★★ **재작성에 쓰이는 `==` 는 `bool` 을 돌려줘야 한다** — clang 의 경고가 그 문장을 **그대로** 적는다. **ill-formed 인데 clang 은 `cc exit=0` 으로 통과**시켰다 — 이 편의 「**종료 코드 0인데 ill-formed**」 항목이다.
- ★★ **`-pedantic-errors` 로 clang 도 에러 1**.
- ★ **`a == b` 직접 호출은 합법**이다 — `int` 를 돌려주는 `operator==` 자체는 금지가 아니다. **재작성될 때만** `bool` 이어야 한다.

### 10. ★★★ **같은지 볼 때는 순서를 끝까지 매길 필요가 없어서** — 「`<=> = default` 가 **`== = default` 를 함께 암묵 선언**하고 그 `==` 는 **멤버의 `==`** 를 쓴다」

**왜 그런가**

- ★★★ **`<=>` 로 `==` 를 풀면 순서를 끝까지 계산해야** 한다 — 문자열·벡터는 **길이가 다르면 즉시 「다르다」인데** `<=>` 는 그 지름길을 모른다.\
  ★ 이것은 **C++20 설계의 논증**이고 이 문서가 **재서 확인한 것이 아니다.** 이 문서가 확인한 것은 **2번의 로그**(`==` 가 `<=>` 를 안 부른다)와 **1번의 에러**(손으로 쓴 `<=>` 는 `==` 를 안 준다)다.
- ★★ **고쳐 적은 문장** — 「`<=>` 에서 `==` 가 생긴다」(틀림) → 「**`= default` 인 `<=>` 가 `==` 의 `= default` 선언을 함께 만든다**」(맞음). 손으로 쓴 `<=>` 에는 **이 선언이 안 붙는다.**

### 11. ★★ **표준** · **미명시** · **표준을 어긴 코드를 통과시킨 것 — 「종료 코드 0인데 ill-formed」**

**왜 그런가**

- ★★ **뒤집힌 재작성은 표준 규칙**이다 — 어느 구현에서도 5번의 로그가 같아야 한다.
- ★★ **기계어는 미명시** — 결과가 같으면 어떤 명령을 내도 된다. 8번 표는 **이 판의 관찰**이다.
- ★ **9번은 「구현의 관대함」이다** — 표준(`bool` 이어야 한다)을 어긴 프로그램을 clang 이 **경고만 내고** 받았다. 층으로는 **표준 위반(ill-formed)** 이고, **도구가 못 보는 것** 칸의 고정 항목이다.

### 12. 다른 주제와 잇기

- ★★★ **`PartialOrd` ↔ `partial_ordering` · `Ord` ↔ `strong_ordering`** — **`weak_ordering` 에는 Rust 표준 트레이트 짝이 없다**(Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **28번**([`28-partialeq-eq-partialord-ord-and-hash-contracts/`](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/))).
- ★★ **Rust 28편 (10) — 「대칭은 계약이지 문법이 아니다」**: 한쪽만 `impl` 하면 반대 방향이 **E0369**. **C++20 은 뒤집힌 재작성 후보로 언어가 반대 방향을 만든다**(5번).
- ★★ **C++20 에서는 언어가 한다** — 파이썬은 **`functools.total_ordering` 이라는 라이브러리 데코레이터**가 `__lt__` 에서 나머지를 채우고(Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **31번**([`31-comparison-protocol-and-sortability/`](../../../python/syntax/31-comparison-protocol-and-sortability/)) 5절), C++20 은 **컴파일러가 재작성**한다.
- ★ **산술 연산자**에서 그대로 남는다 — `+` 에는 재작성이 없다([22번](../22-operator-overloading/) (1)).

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `cmp01.cpp` `= default` 여섯 | g++ · clang 각 1회 | 여섯 다 됨 · `(a <=> b) < 0` 이 `a < b` 와 같다 |
| `cmp02.cpp` `==` 는 따로 | g++ · clang 각 1회 | ★★★ `==`·`!=` → **`Part::operator==`** · `<`·`>=` → **`<=>`** |
| `cmp03.cpp` 손으로 쓴 `<=>` | g++ · clang 각 2회(실행 · `-DASK_EQ`) | ★★★ 관계·`max` → **`<=>`** · `==` **에러 1 · 1** |
| `cmp04.cpp` 범주 | g++ · clang 각 2회(실행 · `-DWRONG`) | ★★ `static_assert` 4개 통과 · NaN **`unordered`** · clang 이 **`partial_ordering`** 을 짚음 |
| `cmp05.cpp` 선언 순서 | g++ · clang 각 1회 | ★★ **1 과 0** |
| `cmp06.cpp` 대칭 | g++ · clang 각 1회 | ★★★ **`5000 < a` 됨** · 로그 **`this=1000 o=5000`** |
| `cmp09.cpp` 합성 | g++ · clang 각 2회(실행 · `-DAUTO`) | ★★ **`==` → `<`** · `auto` 판 **지워짐** |
| `cmp07.cpp`·`cmp08.cpp` | g++·clang `-std=c++17` · `-std=c++20` · `<compare>` 없음 | ★ C++17 **에러 4 · 3** · `<compare>` 없음 **7 · 1** |
| `cmp10.cpp` `bool` 아닌 `==` | g++ 1회 · clang 2회(`-pedantic` · `-pedantic-errors`) | ★★★ **g++ 에러 · clang `cc exit=0`** → 에러 1 |
| `cmp11.cpp` 어셈블리 | g++ · clang `-O2` 각 1회 + 스크립트 | ★★ 같은 것은 **clang `==` 하나** |
| `cmp12.cpp` 형태 | g++ · clang 각 1회 | `0.9.9 1.2.3 1.10.0` · `Tag == : 1 · Tag < : 0` |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · libstdc++ 13)에서만** 그렇다.

- ★★ **8번의 어셈블리 표 전부** · **진단 문구** · **9번에서 clang 이 경고로만 받는 것.**

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **관계 넷의 `<=>` 재작성 · `!=` 의 `==` 재작성 · 뒤집힌 판.**
- ★★★ **`==` 는 `= default` 인 `<=>` 에서만 암묵 선언되고 멤버의 `==` 를 쓰는** 것.
- ★★ **`auto` = 가장 약한 범주 · 선언 순서 사전식 · `<`·`==` 로 합성 · `<compare>` 필요 · 재작성에 쓰일 `==` 는 `bool`.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **뒤집힌 판과의 모호성** · ★ **기반 클래스가 있는 `= default`** · ★ **`std::sort` 에 NaN** · ★ **`std::strong_order`(전순서 `double`).**
- ★ **안 잰 것 — 시간.** 8번은 명령까지다.
- ★ **「부적용인 창」** — ASan.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **9번** — clang 이 `bool` 이 아닌 `==` 재작성을 **에러로** 바꾸는지.
- ★★ **8번 표** — 미명시라 판이 바뀌면 뒤집힐 수 있다.
