# cpp/syntax/02 — `enum class` 와 범위 있는 열거형 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — Enumeration declaration](https://en.cppreference.com/w/cpp/language/enum) · [cppreference — `std::underlying_type`](https://en.cppreference.com/w/cpp/types/underlying_type) · [cppreference — `std::to_underlying`](https://en.cppreference.com/w/cpp/utility/to_underlying) · [GCC 13 C++ Dialect Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/C_002b_002b-Dialect-Options.html) · [Clang UndefinedBehaviorSanitizer](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html)
> **실행 검증** — 이 문서의 모든 출력·경고·에러는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **gcc 13.3.0**(C 대비용) · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex` 이고,\
> **C 와 나란히 던진 블록은 `gcc -std=c17 -Wall -Wextra -pedantic ex.c -o ex`** 다.\
> ★ 블록은 `capture.sh` 가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.
> **버전** — `enum class`(범위 있는 열거형)와 **기저 타입 지정**(`: unsigned char`)은 **C++11부터**다.\
> **`using enum`** 은 **C++20부터**이고 이 g++ 에서 **된다**((10)). **`std::to_underlying`** 은 **C++23부터**이고\
> `-std=c++20` 에서는 에러다((6)). ★ 이 g++ 의 `-std=c++23` 은 `__cplusplus` 가 `202100L` 이다(정식 값 `202302L` 이 아니다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> **경계** — 「C 의 `enum` 이 무엇을 안 막나」의 정본은 C 갈래의\
> [`07-enum-and-enumeration-constants/`](../../../c/syntax/07-enum-and-enumeration-constants/)다.\
> 그쪽은 **크기·부호·`-fshort-enums`·C23 고정 기반 타입**까지 다 결론지었다.\
> 여기는 **C++ 가 새로 하는 것**만 쓴다 — 이름을 가두는 것 · 암묵 변환을 끊는 것 · **범위 밖 값의 판정이 C 와 갈리는 것**.\
> 「`static_cast` 자체」는 [**03번 형제**](../03-four-cast-operators/), 「오버로드 후보가 줄어드는 것」은 [**01번 형제**](../01-function-overloading-and-overload-resolution/)가 정본이다.\
> 「`switch` 문법」은 C 갈래의 [`12-control-flow-and-switch/`](../../../c/syntax/12-control-flow-and-switch/)가 정본이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 컴파일 시간 | **진단 본문** · `파일:줄:칸` · **종료 코드**(`cc exit`·`run exit` 을 갈라 적었다) |
> | — | `sizeof` 값 · `std::is_same_v` 판정 · **경고 건수**(`grep -c 'warning:'`) |
> | ★ **UB 가 만든 값**(`Plain=200`) | ★ **그 값이 「유효하지 않다」고 판정된 사실**과 **어느 도구가 그걸 말했나** |

## 한눈에 — 쉽게 말하면

**`enum class` 는 「이름을 자기 안에 가두고, 정수와의 통행을 끊은 열거형」이다.**

C 의 `enum` 은 **이름이 붙은 정수 상수 묶음**이었다 — C 갈래
[`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)이 그것을 못 박았다.
`enum class` 는 거기에 **담장 둘**을 세운다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 이름표를 **아무 데나 붙여 놓은 것** | C 의 `enum` — 열거 상수가 **바깥 스코프에** 풀려 있다 |
| ★ **이름표를 서랍에 넣고 서랍 이름을 붙인다** | `enum class Color` — 이름은 `Color::Red` 로만 부른다 |
| 다른 서랍에 **같은 이름표**를 넣어도 된다 | `Color::Red` 와 `Signal::Red` 가 **공존한다** |
| ★ 서랍에서 **꺼내려면 손으로 꺼내야** 한다 | 정수로 나가려면 **`static_cast` 를 써야** 한다 |
| 서랍 **규격**을 지정할 수 있다 | `enum class Small : unsigned char` — `sizeof` 가 **1** |
| 규격을 안 쓰면 **기본 규격**이 정해져 있다 | 범위 있는 열거형의 기저 타입은 **`int`** — ★ 표준이 정한다 |
| 규격을 안 쓴 **옛 서랍**은 규격이 제각각 | 범위 없는 열거형은 기저 타입이 **구현 정의** — 여기선 `unsigned int` |

- ★★ **담장은 둘이고 따로 논다** — ① **이름 가두기**(`Color::Red`) ② **암묵 변환 끊기**(정수로 못 나감).\
  `enum class` 는 둘 다 하고, `enum E : unsigned char` 는 **①을 안 하고 크기만 고정**한다((5)).
- ★★ **C 에서 통과하던 세 줄이 C++ 에서 전부 에러가 된다**((3)) — 그 셋이 이 주제의 값이다.
- ★ **`enum class` 는 클래스가 아니다.** 멤버 함수도 상속도 없다. 이름이 그렇게 생겼을 뿐이다.

```text
   C 의 enum                              C++ 의 enum class
   enum Color { RED, GREEN };             enum class Color { Red, Green };

   +--------------------------+           +--------------------------+
   | 바깥 스코프              |           | 바깥 스코프              |
   |   RED   GREEN   ...      |           |   Color                  |
   |   ↑ 이름이 여기 있다     |           |     +------------------+ |
   +--------------------------+           |     | Red  Green       | |
            │                             |     +------------------+ |
            │ int 로 자유 통행            +--------------------------+
            ↓                                        │
   +--------------------------+                      │ static_cast 로만
   |        int               |                      ↓
   +--------------------------+           +--------------------------+
                                          |        int               |
   c = 999;  도 통과                      +--------------------------+
   c + 1     도 통과                      c = 999;  -> error
   c == APPLE 도 통과(경고만)             c + 1     -> error
                                          c == Fruit::Red -> error
```

> **범위 있는 열거형(scoped enumeration)** — `enum class` 또는 `enum struct` 로 선언한 것.\
> 열거자 이름이 **열거형 안에 갇히고**, 정수로의 **암묵 변환이 없다**. `class` 와 `struct` 는 여기서 **뜻이 같다**.

> **범위 없는 열거형(unscoped enumeration)** — 그냥 `enum`. C 의 것과 같은 모양이다.\
> 열거자가 **바깥 스코프에도** 들어가고 정수로 **암묵 변환된다**.

> **기저 타입(underlying type)** — 열거형 값을 실제로 담는 정수 타입.\
> 범위 있는 열거형은 기본이 **`int`**(표준), 범위 없는 것은 **구현 정의**다.

> **고정 기저 타입(fixed underlying type)** — `enum E : T` 로 **적어 준** 기저 타입.\
> ★ 적어 주면 **유효한 값의 범위가 `T` 전체**가 된다 — (8)에서 이것이 결정적이다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **C 에서 통과하던 무엇이 여기서 막히나** — 세 줄을 나란히 던져 **에러 전문**으로 보일 수 있나.
2. **크기와 기저 타입은 누가 정하나** — 네 벌(범위 유무 × 고정 유무)의 `sizeof` 와 기저 타입을 예측할 수 있나.
3. **범위 밖 값을 넣으면 어떻게 되나** — C 편이 「UB 아님」으로 결론지은 그 자리가 **C++ 에서도 같나**.

★ C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)이 「**`enum` 은 이름이 붙은 정수일 뿐이다**」를 결론으로 냈다면,
여기는 「**그 「뿐이다」를 어디까지 고칠 수 있나, 그리고 고치면 무엇을 잃나**」다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| **컴파일 진단** | 담장이 막는 자리 — 세 에러가 한 화면에 | 본체다((3)) |
| **실행 출력** | `sizeof` · 기저 타입 판정 · 범위 밖 값 | (4)·(8) |
| **sanitizer** | ★ **범위 밖 값이 미정의인지** — 그런데 **한쪽만 말한다** | (8) |
| ★ **같은 세 줄을 C 로도 던지기** | 「무엇이 새로 막혔나」를 **한 글자도 안 틀리게** 가른다 | (1)·(2)·(3) |

★ **네 번째 창을 왜 이것으로 골랐나.** 이 주제는 **「C 에서 되던 것이 안 된다」가 내용의 절반**이다.
「C 는 이랬다」를 기억이나 다른 문서에서 옮겨 오면 **그 절반이 근거 없는 산문**이 된다.
그래서 **같은 모양의 프로그램을 `ex.c` 로도 쓰고 `gcc` 로 던져 출력을 나란히 싣는다.**
정본 결론은 C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)에 있고,
여기서는 **대비에 필요한 만큼만** 다시 던진다.

★ **sanitizer 칸이 반쪽이다** — 이 주제의 UB 는 **clang 의 UBSan 만 잡고 gcc 의 UBSan 은 한 줄도 안 낸다**((8)).
「도구가 조용하다」를 「문제가 없다」로 읽으면 안 되는 전형이다.

### (1) C 의 `enum` 이 안 막는 세 자리 — 먼저 C 로 던진다

**언제 쓰나** — 「C++ 가 무엇을 새로 막나」의 기준선을 세울 때.

```text
===== 소스: ex.c =====
/* C 의 enum 이 무엇을 안 막나 — 세 자리를 한 파일에서 */
#include <stdio.h>

enum Color { RED, GREEN, BLUE };
enum Fruit { APPLE, BANANA };

int main(void) {
    enum Color c = RED;
    int n = c + 1;                       /* ① 암묵 정수 변환 */
    if (c == APPLE) puts("c == APPLE");  /* ② 다른 열거형과 비교 */
    c = 999;                             /* ③ 범위 밖 값 대입 */
    printf("n=%d c=%d\n", n, (int)c);
    return 0;
}
===== gcc -std=c17 -Wall -Wextra -pedantic ex.c -o ex (cc exit=0) =====
ex.c: In function ‘main’:
ex.c:10:11: warning: comparison between ‘enum Color’ and ‘enum Fruit’ [-Wenum-compare]
   10 |     if (c == APPLE) puts("c == APPLE");  /* ② 다른 열거형과 비교 */
      |           ^~
```

경고는 **한 건**이다(`-Wenum-compare`). 그리고 **컴파일은 통과한다**(`cc exit=0`).

```text
===== ./ex (run exit=0) =====
c == APPLE
n=1 c=999
```

- ★ **`c = 999;` 가 아무 말 없이 통과하고 `999` 가 그대로 찍힌다.**
- ★ 다른 열거형과의 비교는 **경고만** 나고 실행되어 `c == APPLE` 을 찍는다(둘 다 `0` 이라 참이다).
- 이 세 자리의 정본 결론은 C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)에 있다 —\
  거기서는 **여섯 플래그 조합 전부에서 0건**까지 세어 놓았다.

### (2) 같은 세 줄을 C++ 의 범위 **없는** 열거형으로

**언제 쓰나** — 「C++ 로 옮기기만 하면 고쳐지나」를 물을 때. 답은 「**거의 안 고쳐진다**」이다.

```text
===== 소스: ex.cpp =====
// 같은 소스를 C++ 의 「범위 없는 열거형」으로 — C 와 어디까지 같은가
#include <cstdio>

enum Color { RED, GREEN, BLUE };
enum Fruit { APPLE, BANANA };

int main() {
    Color c = RED;
    int n = c + 1;                              // ① 암묵 정수 변환
    if (c == APPLE) std::puts("c == APPLE");    // ② 다른 열거형과 비교
    c = static_cast<Color>(999);                // ③ C 의 `c = 999` 는 C++ 에서 에러다
    std::printf("n=%d c=%d\n", n, static_cast<int>(c));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=0) =====
ex.cpp: In function ‘int main()’:
ex.cpp:10:11: warning: comparison between ‘enum Color’ and ‘enum Fruit’ [-Wenum-compare]
   10 |     if (c == APPLE) std::puts("c == APPLE");    // ② 다른 열거형과 비교
      |         ~~^~~~~~~~
```

```text
===== ./ex (run exit=0) =====
c == APPLE
n=1 c=999
```

- ★★ **경고 문구까지 C 와 같다**(`comparison between 'enum Color' and 'enum Fruit' [-Wenum-compare]`).\
  캐럿 줄의 물결 모양만 다르다 — g++ 가 비교식 전체를 짚는다.
- ★ **딱 하나가 다르다** — C 의 `c = 999;` 는 **C++ 에서 에러**라서 `static_cast<Color>(999)` 로 바꿔야 했다.\
  그 캐스트가 (8)에서 UB 가 된다.
- ★★ **결론** — 「C++ 로 컴파일한다」가 열거형을 고쳐 주지 않는다. **`class` 를 붙여야** 고쳐진다.

### (3) `enum class` 로 바꾸면 — 세 줄이 전부 막힌다

**언제 쓰나** — 이 주제에서 **읽을 값이 가장 많은 진단**이다.

```text
===== 소스: ex.cpp =====
// 같은 세 자리를 enum class 로 — 세 줄이 전부 막힌다
#include <cstdio>

enum class Color { Red, Green, Blue };
enum class Fruit { Red, Banana };     // Red 라는 이름을 다시 써도 되나

int main() {
    Color c = Color::Red;
    int n = c + 1;                    // ①
    if (c == Fruit::Red) std::puts("같다");   // ②
    c = 999;                          // ③
    std::printf("n=%d\n", n);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp: In function ‘int main()’:
ex.cpp:9:15: error: no match for ‘operator+’ (operand types are ‘Color’ and ‘int’)
    9 |     int n = c + 1;                    // ①
      |             ~ ^ ~
      |             |   |
      |             |   int
      |             Color
ex.cpp:10:11: error: no match for ‘operator==’ (operand types are ‘Color’ and ‘Fruit’)
   10 |     if (c == Fruit::Red) std::puts("같다");   // ②
      |         ~ ^~ ~~~~~~~~~~
      |         |           |
      |         Color       Fruit
ex.cpp:10:11: note: candidate: ‘operator==(Fruit, Fruit)’ (built-in)
   10 |     if (c == Fruit::Red) std::puts("같다");   // ②
      |         ~~^~~~~~~~~~~~~
ex.cpp:10:11: note:   no known conversion for argument 1 from ‘Color’ to ‘Fruit’
ex.cpp:10:11: note: candidate: ‘operator==(Color, Color)’ (built-in)
ex.cpp:10:11: note:   no known conversion for argument 2 from ‘Fruit’ to ‘Color’
ex.cpp:11:9: error: cannot convert ‘int’ to ‘Color’ in assignment
   11 |     c = 999;                          // ③
      |         ^~~
      |         |
      |         int
```

- ★★ **에러 셋이 한 번에 나온다** — `operator+` 없음 · `operator==` 없음 · `int` 를 `Color` 로 대입 불가.
- ★★ **`operator==` 진단이 오버로드 해석의 언어로 말한다** —\
  `candidate: 'operator==(Fruit, Fruit)' (built-in)` + `no known conversion for argument 1 from 'Color' to 'Fruit'`.\
  **내장 연산자도 후보 집합에 들어간다**는 것이 여기서 보인다([**01번 형제**](../01-function-overloading-and-overload-resolution/)의 2단계 그대로다).
- ★ `enum class Fruit { Red, Banana };` 가 **`Color::Red` 와 이름이 겹쳐도 아무 문제가 없다** —\
  이 파일이 컴파일되다가 **저 세 줄에서만** 걸린 것이 그 증거다.

clang 도 같은 셋을 잡는다 — 문구가 짧고 후보 나열이 없다.

```text
===== 소스: ex.cpp =====
// 같은 세 자리를 enum class 로 — 세 줄이 전부 막힌다
#include <cstdio>

enum class Color { Red, Green, Blue };
enum class Fruit { Red, Banana };     // Red 라는 이름을 다시 써도 되나

int main() {
    Color c = Color::Red;
    int n = c + 1;                    // ①
    if (c == Fruit::Red) std::puts("같다");   // ②
    c = 999;                          // ③
    std::printf("n=%d\n", n);
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp:9:15: error: invalid operands to binary expression ('Color' and 'int')
    9 |     int n = c + 1;                    // ①
      |             ~ ^ ~
ex.cpp:10:11: error: invalid operands to binary expression ('Color' and 'Fruit')
   10 |     if (c == Fruit::Red) std::puts("같다");   // ②
      |         ~ ^  ~~~~~~~~~~
ex.cpp:11:9: error: assigning to 'Color' from incompatible type 'int'
   11 |     c = 999;                          // ③
      |         ^~~
3 errors generated.
```

### (4) 이름 충돌 — C 와 C++ 과 `enum class`

**언제 쓰나** — 열거형이 여럿인 헤더를 쓸 때. 실무에서 가장 자주 부딪히는 자리다.

C 에서는 **에러**다. 열거 상수가 **바깥 스코프에 풀려** 있기 때문이다.

```text
===== 소스: ex.c =====
/* C 에서 열거 상수의 이름이 부딪히면 */
enum Color  { RED, GREEN };
enum Signal { RED, YELLOW };

int main(void) { return 0; }
===== gcc -std=c17 -Wall -Wextra -pedantic ex.c -o ex (cc exit=1) =====
ex.c:3:15: error: redeclaration of enumerator ‘RED’
    3 | enum Signal { RED, YELLOW };
      |               ^~~
ex.c:2:15: note: previous definition of ‘RED’ with type ‘enum Color’
    2 | enum Color  { RED, GREEN };
      |               ^~~
```

C++ 의 범위 **없는** 열거형도 같은 자리에서 막힌다. 문구만 다르다.

```text
===== 소스: ex.cpp =====
// C++ 의 범위 없는 열거형도 같은 자리에서 부딪힌다
enum Color  { RED, GREEN };
enum Signal { RED, YELLOW };

int main() { return 0; }
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp:3:15: error: ‘RED’ conflicts with a previous declaration
    3 | enum Signal { RED, YELLOW };
      |               ^~~
ex.cpp:2:15: note: previous declaration ‘Color RED’
    2 | enum Color  { RED, GREEN };
      |               ^~~
```

- ★ **`note:` 가 말하는 타입이 갈린다** — C 는 `previous definition of 'RED' with type 'enum Color'`,\
  C++ 은 `previous declaration 'Color RED'`. **C++ 에서 열거자의 타입은 그 열거형 자체**다.\
  C 에서는 **`int`** 다(정본은 C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)).

`enum class` 로 바꾸면 **같은 이름 둘이 공존한다.**

```text
===== 소스: ex.cpp =====
// enum class 는 이름을 자기 안에 가둔다 — 그래서 부딪히지 않는다
#include <cstdio>

enum class Color  { Red, Green };
enum class Signal { Red, Yellow };

int main() {
    Color  c = Color::Red;
    Signal s = Signal::Red;
    std::printf("%d %d\n", static_cast<int>(c), static_cast<int>(s));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
0 0
```

- ★★ **이 자리는 C 갈래에 선례가 없다.** C 편은 스코프 차이(블록 대 파일 끝)만 다뤘고\
  **열거 상수끼리의 이름 충돌을 따로 다루지 않았다.** 여기가 C++ 가 새로 푸는 문제다.

### (5) 크기와 기저 타입 — 네 벌을 나란히

**언제 쓰나** — 직렬화·ABI·비트 플래그처럼 **크기가 약속의 일부**일 때.

범위 유무 × 고정 유무로 넷을 만들어 `sizeof` 와 `std::underlying_type_t` 를 찍는다.

```text
===== 소스: ex.cpp =====
// 크기와 기저 타입 — 네 벌을 나란히 찍는다
#include <cstdio>
#include <type_traits>

enum       Plain           { P_A, P_B };            // 범위 없음 · 기저 타입 안 정함
enum       PlainFixed : unsigned char { PF_A, PF_B };// 범위 없음 · 기저 타입 고정
enum class Scoped          { A, B };                // 범위 있음 · 기저 타입 안 씀
enum class ScopedFixed : unsigned char { A, B };    // 범위 있음 · 기저 타입 고정

template <class E> void report(const char* name) {
    using U = std::underlying_type_t<E>;
    std::printf("%-12s sizeof=%zu  underlying: int=%d unsigned=%d uchar=%d\n",
                name, sizeof(E),
                static_cast<int>(std::is_same_v<U, int>),
                static_cast<int>(std::is_same_v<U, unsigned int>),
                static_cast<int>(std::is_same_v<U, unsigned char>));
}

int main() {
    report<Plain>("Plain");
    report<PlainFixed>("PlainFixed");
    report<Scoped>("Scoped");
    report<ScopedFixed>("ScopedFixed");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
Plain        sizeof=4  underlying: int=0 unsigned=1 uchar=0
PlainFixed   sizeof=1  underlying: int=0 unsigned=0 uchar=1
Scoped       sizeof=4  underlying: int=1 unsigned=0 uchar=0
ScopedFixed  sizeof=1  underlying: int=0 unsigned=0 uchar=1
```

| 선언 | `sizeof` | 기저 타입 | 누가 정하나 |
|---|---|---|---|
| `enum Plain { ... }` | **4** | `unsigned int` | ★ **구현 정의** — gcc 가 음수 열거자가 없어서 고른 것 |
| `enum PlainFixed : unsigned char` | **1** | `unsigned char` | **적어 준 대로**(C++11) |
| `enum class Scoped { ... }` | **4** | **`int`** | ★ **표준** — 범위 있는 열거형의 기본은 `int` 다 |
| `enum class ScopedFixed : unsigned char` | **1** | `unsigned char` | 적어 준 대로 |

- ★★ **여기가 C 와 갈리는 두 번째 자리다.** C 에서는 `sizeof(enum E)` 도 부호도 **전부 구현 정의**였다\
  (C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)이 `-fshort-enums` 하나로 4→1 을 뒤집어 보였다).\
  **범위 있는 열거형은 표준이 `int` 로 못 박는다** — 그래서 **뒤집히지 않는다.**
- ★ **`Plain` 이 `unsigned int` 인 것**은 gcc 의 선택이고 **보장이 아니다.** C 편과 같은 결론이다.\
  **뒤집어 보면** 그것이 드러난다 — `-fshort-enums` 하나로 **`Plain` 만** 움직인다.

```text
===== 소스: ex.cpp =====
// 크기와 기저 타입 — 네 벌을 나란히 찍는다
#include <cstdio>
#include <type_traits>

enum       Plain           { P_A, P_B };            // 범위 없음 · 기저 타입 안 정함
enum       PlainFixed : unsigned char { PF_A, PF_B };// 범위 없음 · 기저 타입 고정
enum class Scoped          { A, B };                // 범위 있음 · 기저 타입 안 씀
enum class ScopedFixed : unsigned char { A, B };    // 범위 있음 · 기저 타입 고정

template <class E> void report(const char* name) {
    using U = std::underlying_type_t<E>;
    std::printf("%-12s sizeof=%zu  underlying: int=%d unsigned=%d uchar=%d\n",
                name, sizeof(E),
                static_cast<int>(std::is_same_v<U, int>),
                static_cast<int>(std::is_same_v<U, unsigned int>),
                static_cast<int>(std::is_same_v<U, unsigned char>));
}

int main() {
    report<Plain>("Plain");
    report<PlainFixed>("PlainFixed");
    report<Scoped>("Scoped");
    report<ScopedFixed>("ScopedFixed");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -fshort-enums ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
Plain        sizeof=1  underlying: int=0 unsigned=0 uchar=1
PlainFixed   sizeof=1  underlying: int=0 unsigned=0 uchar=1
Scoped       sizeof=4  underlying: int=1 unsigned=0 uchar=0
ScopedFixed  sizeof=1  underlying: int=0 unsigned=0 uchar=1
```

- ★★ **넷 중 하나만 흔들렸다.** `Scoped` 는 **표준이 `int` 로 정해** 두었고 나머지 둘은 **적어 두었기** 때문이다.\
  C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)이 같은 플래그로 C 의 `enum` 을 4→1 로 뒤집어 보인 것과\
  **같은 실험인데 결과가 좁다** — 그 좁음이 C++ 가 벌어 준 것이다.
- ★ 기저 타입을 적어 주면 **범위 없는 열거형도 크기가 고정**된다 — 담장 ②(암묵 변환 끊기)와는 **별개**다.

### (6) `static_cast` 로 담장을 넘는다 — 그리고 그것이 눈에 보인다

**언제 쓰나** — 인덱스·직렬화·C API 경계처럼 정수가 꼭 필요한 자리.

```text
===== 소스: ex.cpp =====
// static_cast 가 양쪽 벽을 뚫는다 — 그리고 그것이 눈에 보인다
#include <cstdio>

enum class Color : unsigned char { Red = 0, Green = 1 };

int main() {
    Color c = Color::Green;
    int n = static_cast<int>(c);            // 나가는 쪽
    Color back = static_cast<Color>(n);      // 들어오는 쪽
    std::printf("n=%d back==Green: %d\n", n, static_cast<int>(back == Color::Green));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
n=1 back==Green: 1
```

- ★ **나가는 쪽도 들어오는 쪽도 `static_cast` 가 필요하다.** 암묵 변환이 **양방향으로** 끊겨 있다.
- ★★ **그것이 이 담장의 값이다** — 정수로 나가는 자리가 **코드에 글자로 남는다.**\
  C 에서는 같은 일이 **아무 표시 없이** 일어났다((1)).
- `static_cast` 자체의 규칙은 [**03번 형제**](../03-four-cast-operators/)가 정본이다.

C++23 은 「기저 타입으로 꺼내기」에 **이름을 붙였다** — `std::to_underlying`.

```text
===== 소스: ex.cpp =====
// C++23 의 std::to_underlying — 이 컴파일러에서 되나
#include <cstdio>
#include <utility>

enum class Color : unsigned char { Red, Green };

int main() {
    std::printf("%d\n", static_cast<int>(std::to_underlying(Color::Green)));
}
===== g++ -std=c++23 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
1
```

`-std=c++20` 으로 같은 소스를 던지면 **g++ 가 몇 년도 물건인지까지 말해 준다.**

```text
===== 소스: ex.cpp =====
// C++23 의 std::to_underlying — 이 컴파일러에서 되나
#include <cstdio>
#include <utility>

enum class Color : unsigned char { Red, Green };

int main() {
    std::printf("%d\n", static_cast<int>(std::to_underlying(Color::Green)));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp: In function ‘int main()’:
ex.cpp:8:47: error: ‘to_underlying’ is not a member of ‘std’
    8 |     std::printf("%d\n", static_cast<int>(std::to_underlying(Color::Green)));
      |                                               ^~~~~~~~~~~~~
ex.cpp:8:47: note: ‘std::to_underlying’ is only available from C++23 onwards
```

- ★ `note: 'std::to_underlying' is only available from C++23 onwards` —\
  **「미지원」을 한 낱말로 적지 말라**는 규칙의 좋은 예다. 이 진단은 「**다음 표준에 있다**」까지 말한다.

### (7) 전방 선언이 되는 조건 — 크기를 아는가

**언제 쓰나** — 헤더 의존을 끊고 싶을 때.

```text
===== 소스: ex.cpp =====
// 전방 선언이 되는 조건 — 기저 타입을 아는가
enum class A;      // 범위 있는 열거형: 기저 타입 기본값이 int 라 크기를 안다
enum       B;      // 범위 없고 기저 타입도 없다
enum       C : int;// 기저 타입을 적어 주면

int main() {}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp:3:12: error: use of enum ‘B’ without previous declaration
    3 | enum       B;      // 범위 없고 기저 타입도 없다
      |            ^
```

- ★★ **셋 중 하나만 막힌다.** `enum class A;` 는 되고, `enum C : int;` 도 되고, **`enum B;` 만 안 된다.**
- **왜** — 전방 선언은 **크기를 알아야** 성립한다.\
  `enum class` 는 기본 기저 타입이 **`int` 로 표준이 정해져 있어서** 크기를 안다((5)).\
  기저 타입을 적어 준 `enum C : int;` 도 안다.\
  **`enum B;` 는 열거자를 다 봐야 크기가 정해지므로** 못 한다.
- ★ clang 은 이유를 **표준의 말로** 말한다 — `ISO C++ forbids forward references to 'enum' types`.

```text
===== 소스: ex.cpp =====
// 전방 선언이 되는 조건 — 기저 타입을 아는가
enum class A;      // 범위 있는 열거형: 기저 타입 기본값이 int 라 크기를 안다
enum       B;      // 범위 없고 기저 타입도 없다
enum       C : int;// 기저 타입을 적어 주면

int main() {}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp:3:12: error: ISO C++ forbids forward references to 'enum' types
    3 | enum       B;      // 범위 없고 기저 타입도 없다
      |            ^
1 error generated.
```

★ C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)은 불완전 열거 타입이 **C23부터**라고 적고
「**던져 보지 않았다**」고 밝혀 뒀다. C++ 에서는 **C++11부터 위 세 줄의 갈림이 그대로** 성립한다.

### (8) ★★ 범위 밖 값 — C 편의 결론이 여기서 갈린다

**언제 쓰나** — 파일·네트워크에서 읽은 정수를 열거형으로 바꿀 때. **실무에서 가장 위험한 자리다.**

C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)은 이 자리를 이렇게 결론지었다 —
**「범위 밖 값을 넣는 것은 UB 가 아니다. 이 주제에서 만들 수 있는 UB 는 열거 타입 자체로는 없다.」**

**C++ 에서는 갈린다.** 기저 타입이 **고정된 쪽**과 **안 된 쪽**이 다르다.

```text
===== 소스: ex.cpp =====
// 범위 밖 값 — 기저 타입이 고정된 쪽과 안 된 쪽이 갈린다
#include <cstdio>

enum class Scoped : unsigned char { A = 0, B = 1 };  // 기저 타입 고정
enum       Plain                  { P_A = 0, P_B = 1 };  // 기저 타입 없음

int main() {
    auto s = static_cast<Scoped>(200);
    auto p = static_cast<Plain>(200);
    std::fprintf(stderr, "Scoped=%d Plain=%d\n",
                 static_cast<int>(s), static_cast<int>(p));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
Scoped=200 Plain=200
```

```text
===== 소스: ex.cpp =====
// 범위 밖 값 — 기저 타입이 고정된 쪽과 안 된 쪽이 갈린다
#include <cstdio>

enum class Scoped : unsigned char { A = 0, B = 1 };  // 기저 타입 고정
enum       Plain                  { P_A = 0, P_B = 1 };  // 기저 타입 없음

int main() {
    auto s = static_cast<Scoped>(200);
    auto p = static_cast<Plain>(200);
    std::fprintf(stderr, "Scoped=%d Plain=%d\n",
                 static_cast<int>(s), static_cast<int>(p));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
Scoped=200 Plain=200
```

값은 **두 최적화 수준에서 같다**. 그런데 **clang 의 UBSan 은 한쪽을 미정의로 판정한다.**

```text
===== 소스: ex.cpp =====
// 범위 밖 값 — 기저 타입이 고정된 쪽과 안 된 쪽이 갈린다
#include <cstdio>

enum class Scoped : unsigned char { A = 0, B = 1 };  // 기저 타입 고정
enum       Plain                  { P_A = 0, P_B = 1 };  // 기저 타입 없음

int main() {
    auto s = static_cast<Scoped>(200);
    auto p = static_cast<Plain>(200);
    std::fprintf(stderr, "Scoped=%d Plain=%d\n",
                 static_cast<int>(s), static_cast<int>(p));
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic -O0 -fsanitize=undefined ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
ex.cpp:11:56: runtime error: load of value 200, which is not a valid value for type 'Plain'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior ex.cpp:11:56 
Scoped=200 Plain=200
```

★★ **`Plain` 만 지목하고 `Scoped` 는 지목하지 않는다.**

- `enum class Scoped : unsigned char` 는 **기저 타입이 고정**돼 있다 → 유효한 값의 범위가 **`unsigned char` 전체**다 → **200 은 유효하다.**
- `enum Plain { P_A = 0, P_B = 1 }` 는 **고정이 아니다** → 유효 범위는 **열거자를 담는 최소 비트 폭**까지다 → **200 은 그 밖이다.**

**gcc 의 UBSan 은 같은 자리에서 한 줄도 안 낸다.**

```text
===== 소스: ex.cpp =====
// 범위 밖 값 — 기저 타입이 고정된 쪽과 안 된 쪽이 갈린다
#include <cstdio>

enum class Scoped : unsigned char { A = 0, B = 1 };  // 기저 타입 고정
enum       Plain                  { P_A = 0, P_B = 1 };  // 기저 타입 없음

int main() {
    auto s = static_cast<Scoped>(200);
    auto p = static_cast<Plain>(200);
    std::fprintf(stderr, "Scoped=%d Plain=%d\n",
                 static_cast<int>(s), static_cast<int>(p));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 -fsanitize=undefined ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
Scoped=200 Plain=200
```

- ★★ **「도구가 조용하다」가 「정의됐다」가 아니다.** 같은 소스·같은 sanitizer 이름인데 **한쪽만 말한다.**
- ★ 처방은 **고정 기저 타입을 갖게 하는 것**이다 — **`enum class` 는 안 적어도 고정**(`int`)이고,\
  범위 없는 열거형은 **`: T` 를 적어야** 고정된다. 그러면 「`T` 로 표현되는 아무 값이나 유효」가 되어\
  **역직렬화가 정의된 동작**이 된다.\
- ★★ 다만 **「정의된 동작」이 「맞는 값」은 아니다.** 값이 열거자 중 하나인지는 **따로 검사**해야 한다 —\
  그것은 타입이 해 주지 않는다. C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)의\
  「`enum` 은 좌석을 지키지 않는다」가 **C++ 에서도 그대로 남는 부분**이다.

### (9) `switch` 누락 경고 — 플래그별로 세기

**언제 쓰나** — 열거자를 추가했을 때 고칠 곳을 컴파일러에게 찾게 할 때.

```text
===== 소스: ex.cpp =====
// switch 가 열거자를 빠뜨리면 — 경고는 어느 플래그에 붙어 있나
enum class Color { Red, Green, Blue };

int rank(Color c) {
    switch (c) {
        case Color::Red:   return 0;
        case Color::Green: return 1;
    }
    return -1;
}

int main() { return rank(Color::Blue); }
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=0) =====
ex.cpp: In function ‘int rank(Color)’:
ex.cpp:5:12: warning: enumeration value ‘Blue’ not handled in switch [-Wswitch]
    5 |     switch (c) {
      |            ^
```

플래그를 갈아 가며 **`grep -c 'warning:'` 로 센다.** ★ 종료 코드도 같이 본다.

```text
===== 소스: ex.cpp =====
// switch 가 열거자를 빠뜨리면 — 경고는 어느 플래그에 붙어 있나
enum class Color { Red, Green, Blue };

int rank(Color c) {
    switch (c) {
        case Color::Red:   return 0;
        case Color::Green: return 1;
    }
    return -1;
}

int main() { return rank(Color::Blue); }
===== for F in "" "-Wall" "-Wextra" "-Wall -Wextra" "-Wall -Wextra -pedantic" "-Wswitch-enum"; do printf "[%-24s] warning: %s 건  cc exit=" "$F" "$(g++ -std=c++20 $F ex.cpp -o ex 2>&1 | grep -c "warning:")"; g++ -std=c++20 $F ex.cpp -o ex >/dev/null 2>&1; echo $?; done (exit=0) =====
[                        ] warning: 0 건  cc exit=0
[-Wall                   ] warning: 1 건  cc exit=0
[-Wextra                 ] warning: 0 건  cc exit=0
[-Wall -Wextra           ] warning: 1 건  cc exit=0
[-Wall -Wextra -pedantic ] warning: 1 건  cc exit=0
[-Wswitch-enum           ] warning: 1 건  cc exit=0
```

- ★★ **`-Wswitch` 는 `-Wall` 에 들어 있고 `-Wextra` 에는 없다.** `-Wextra` 만 주면 **0건**이다.
- ★ **`cc exit` 은 전부 0** 이다 — 경고일 뿐 컴파일은 통과한다. 「경고 0건」과 「exit=0」을 **갈라 읽어야** 하는 자리.
- ★ 이 방어선은 **`default:` 를 쓰면 사라진다**(C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)이 실측해 두었다).\
  열거형 `switch` 에 `default:` 를 넣을지는 「**새 열거자를 컴파일러가 찾아 주길 원하나**」로 정한다.

### (10) `using enum`(C++20) — 담장을 잠깐 낮춘다

**언제 쓰나** — `switch` 나 좁은 함수 안에서 `Color::` 가 반복돼 읽기 나쁠 때.

```text
===== 소스: ex.cpp =====
// using enum (C++20) — 이름을 잠깐 풀어 놓는다
#include <cstdio>

enum class Color { Red, Green, Blue };

const char* name(Color c) {
    using enum Color;                 // C++20
    switch (c) {
        case Red:   return "Red";
        case Green: return "Green";
        case Blue:  return "Blue";
    }
    return "?";
}

int main() { std::puts(name(Color::Green)); }
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
Green
```

- ★ **된다** — 이 g++ 13.3.0 에서 `-std=c++20` 으로 컴파일·실행된다.
- ★ **`using enum` 은 이름 가두기(담장 ①)만 잠깐 낮춘다.** 암묵 변환(담장 ②)은 **그대로 막혀 있다.**
- ★ **스코프 안에서만** 풀린다 — 위 예제는 함수 하나 안이다. **헤더의 네임스페이스 범위에 두면 안 된다.**

`-std=c++17` 로 같은 소스를 던지면 **버전을 정확히 말해 준다.**

```text
===== 소스: ex.cpp =====
// using enum (C++20) — 이름을 잠깐 풀어 놓는다
#include <cstdio>

enum class Color { Red, Green, Blue };

const char* name(Color c) {
    using enum Color;                 // C++20
    switch (c) {
        case Red:   return "Red";
        case Green: return "Green";
        case Blue:  return "Blue";
    }
    return "?";
}

int main() { std::puts(name(Color::Green)); }
===== g++ -std=c++17 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp: In function ‘const char* name(Color)’:
ex.cpp:7:16: error: ‘using enum’ only available with ‘-std=c++20’ or ‘-std=gnu++20’
    7 |     using enum Color;                 // C++20
      |                ^~~~~
ex.cpp:7:21: error: ‘using’ with enumeration scope ‘enum class Color’ only available with ‘-std=c++20’ or ‘-std=gnu++20’
    7 |     using enum Color;                 // C++20
      |                     ^
ex.cpp:7:21: error: ‘using’ with enumeration scope ‘enum class Color’ only available with ‘-std=c++20’ or ‘-std=gnu++20’
ex.cpp:7:21: error: ‘using’ with enumeration scope ‘enum class Color’ only available with ‘-std=c++20’ or ‘-std=gnu++20’
```

★ `error: 'using enum' only available with '-std=c++20' or '-std=gnu++20'` — 같은 줄에 대해
**에러가 네 줄** 나온다(하나는 `using enum` 자체, 셋은 그 결과로 각 `case` 가 걸린 것).

### (11) 다섯 층 — 무엇이 표준이고 무엇이 gcc 인가

C++ 에서도 **「돌아갔다」가 아무것도 증명하지 못한다.** C 갈래가 굳혀 놓은 다섯 층을 그대로 쓴다.\
★★ **이 주제는 「표준」이 C 보다 확 두꺼워지고, 「구현 정의」가 그만큼 얇아진다** — 그것 자체가 결론이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | **범위 있는 열거형의 기본 기저 타입이 `int`** · 열거자 이름이 **열거형 안에 갇히는 것** · 정수와의 **암묵 변환이 없는 것**(양방향) · **다른 열거형과 비교가 안 되는 것** · `enum class` 의 **전방 선언이 되는 것** · **고정 기저 타입이면 그 타입의 모든 값이 유효한 것** · `enum class` 와 `enum struct` 가 같은 것 | `sizeof`+`is_same_v` · 세 에러 전문 · 두 컴파일러가 같은 자리에서 막았다 | — |
| **조건부 표준** | 매크로·옵션이 있을 때만 | **해당 없음** | — | — |
| **구현 정의** | 문서화 의무가 있다 | **범위 없고 기저 타입도 없는 열거형의 기저 타입**(여기선 `unsigned int`) · 그래서 그 `sizeof`(여기선 4) · 진단 문구 · `-std=c++23` 에서 `__cplusplus` 가 `202100L` 인 것 | `is_same_v` 3벌 · `sizeof` | **`-Wall -Wextra -pedantic` 이 한 건도 말하지 않는다** |
| **미명시** | 몇 가지 중 하나 | **해당 없음** | — | — |
| **UB** | 아무 일이나 | ★★ **고정 기저 타입이 없는 열거형에 그 값 범위 밖 정수를 캐스트해 넣고 읽는 것** — C 편은 「**UB 아님**」으로 결론지은 자리다 | **clang UBSan 이 `not a valid value for type 'Plain'`** · `-O0`·`-O2` 값은 같았다 | ★★ **gcc 의 UBSan 은 한 줄도 안 낸다** · 경고도 0건 · **최적화 수준으로는 안 갈린다** |

**「도구가 못 보는 것」을 층마다 — 전용 표**

| 사실 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | gcc UBSan | clang UBSan |
|---|---|---|---|---|
| 범위 있는 열거형에서 정수 연산·대입·타 열거형 비교 | **에러 3** | **에러 3** | — | — |
| 범위 **없는** 열거형에서 같은 세 줄 | **경고 1**(`-Wenum-compare`) | 〃 | — | — |
| `switch` 열거자 누락 | **경고 1**(`-Wall` 에 있다) | 〃 | — | — |
| ★ **범위 밖 값**(고정 기저 타입 없음) | **0건** | **0건** | ★ **0건 — 못 본다** | ★ **1건 — 잡는다** |
| 범위 밖 값(고정 기저 타입 있음) | 0건 | 0건 | 0건 | ★ **0건 — 유효하므로 맞는 침묵이다** |
| 열거자 중복 값 | 0건 | 0건 | — | — |
| 기저 타입이 무엇으로 정해졌나 | 0건 | 0건 | — | — |

- ★★ **이 주제의 유일한 런타임 위험이 「gcc 가 못 보는 것」이다.** C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)은 「UB 가 없어서 sanitizer 가 할 일이 없다」로 끝났는데, **C++ 에서는 UB 가 생겼고 gcc 쪽 도구가 그것을 못 본다.**
- ★ **최적화 수준을 바꿔도 값이 안 갈렸다**(`-O0`·`-O2` 가 `Plain=200` 으로 같다). **「안 터졌다」가 「안전하다」가 아니다.**

## 문법 — 형태와 규칙

### 형태

```cpp
/* ex.cpp */
// 크기와 기저 타입 — 네 벌을 나란히 찍는다
#include <cstdio>
#include <type_traits>

enum       Plain           { P_A, P_B };            // 범위 없음 · 기저 타입 안 정함
enum       PlainFixed : unsigned char { PF_A, PF_B };// 범위 없음 · 기저 타입 고정
enum class Scoped          { A, B };                // 범위 있음 · 기저 타입 안 씀
enum class ScopedFixed : unsigned char { A, B };    // 범위 있음 · 기저 타입 고정

template <class E> void report(const char* name) {
    using U = std::underlying_type_t<E>;
    std::printf("%-12s sizeof=%zu  underlying: int=%d unsigned=%d uchar=%d\n",
                name, sizeof(E),
                static_cast<int>(std::is_same_v<U, int>),
                static_cast<int>(std::is_same_v<U, unsigned int>),
                static_cast<int>(std::is_same_v<U, unsigned char>));
}

int main() {
    report<Plain>("Plain");
    report<PlainFixed>("PlainFixed");
    report<Scoped>("Scoped");
    report<ScopedFixed>("ScopedFixed");
}
```

규칙 불릿.

- **`enum class`** 와 **`enum struct`** 는 **같은 뜻**이다(접근 지정과 무관하다).
- 범위 있는 열거형의 **기본 기저 타입은 `int`** 다 — **표준**이 정한다.
- 범위 **없는** 열거형은 기저 타입이 **구현 정의**다 — 적어 주면 고정된다(`enum E : T`).
- 범위 있는 열거형의 열거자는 **`Color::Red` 로만** 부른다. 범위 없는 것은 **둘 다** 된다(`Color::Red` 도 `RED` 도).
- 정수로 나가고 들어오는 것은 **`static_cast`** 로만 — C++23 에는 나가는 쪽에 `std::to_underlying` 이 있다.
- **전방 선언**은 **기저 타입을 알 때만** 된다 — `enum class A;` · `enum C : int;` 는 되고 `enum B;` 는 안 된다.
- **`using enum E;`**(C++20)는 그 스코프에서 **이름만** 풀어 준다.
- 값의 유효 범위는 **고정 기저 타입이면 그 타입 전체**, 아니면 **열거자를 담는 최소 비트 폭**까지다.

### 금지 사례 — 던져서 받은 여섯

| 쓴 것 | 컴파일러 | 무엇이 나오나 |
|---|---|---|
| `c + 1`(범위 있는 열거형) | g++ | `error: no match for 'operator+' (operand types are 'Color' and 'int')` |
| `c == Fruit::Red` | g++ | `error: no match for 'operator==' …` + **내장 후보 2개 나열** |
| `c = 999`(범위 있는 열거형) | g++ | `error: cannot convert 'int' to 'Color' in assignment` |
| `enum Color{RED}; enum Signal{RED};` | g++ | `error: 'RED' conflicts with a previous declaration` |
| 〃 | gcc(C) | `error: redeclaration of enumerator 'RED'` |
| `enum B;` | g++ | `error: use of enum 'B' without previous declaration` |
| 〃 | clang | `error: ISO C++ forbids forward references to 'enum' types` |
| `std::to_underlying` 을 `-std=c++20` 에서 | g++ | `error: … is not a member of 'std'` + `note: … only available from C++23 onwards` |
| `using enum` 을 `-std=c++17` 에서 | g++ | `error: 'using enum' only available with '-std=c++20'` (+ 결과 에러 3) |

### 고를 것을 손으로 돌리는 순서

1. **정수로 나갈 일이 잦은가** — 비트 플래그·인덱스라면 범위 **없는** 열거형이 편할 수 있다. 다만 (1)의 사고가 따라온다.
2. **크기가 약속의 일부인가**(직렬화·ABI·구조체 레이아웃) — 그렇다면 **기저 타입을 적는다.**
3. **바깥에서 읽은 정수를 담는가** — 그렇다면 **반드시 기저 타입을 적는다**((8)의 UB 를 피하는 유일한 길이다).
4. **이름이 흔한가**(`Red`·`None`·`Error`) — 그렇다면 **`enum class`**.
5. 위 어느 것도 아니면 **기본값은 `enum class`** 다. 담장은 나중에 낮출 수 있고(`using enum`·`static_cast`), 올리기는 어렵다.

## 어디서 틀리나

### 1. ★★ 「C++ 로 컴파일하면 `enum` 이 안전해진다」

아니다. **범위 없는 열거형은 C 와 거의 같다**((2)) — 경고 문구까지 같다.\
딱 하나 `c = 999;` 만 에러가 되고, 그것도 `static_cast` 로 뚫으면 **UB 가 된다**((8)).\
**`class` 를 붙여야** 고쳐진다.

### 2. ★★ 「`enum class` 를 쓰면 범위 밖 값이 못 들어온다」

들어온다. **`static_cast` 로 뚫린다**((6)).\
`enum class` 가 막는 것은 **암묵** 변환이지 명시적 변환이 아니다.\
바깥 데이터를 담는다면 **기저 타입을 적고**, 값이 열거자 중 하나인지 **따로 검사**해야 한다((8)).

### 3. ★★ 「범위 밖 값이 위험한 것은 `enum class` 도 마찬가지다」

아니다. ★ **범위 있는 열거형은 언제나 고정 기저 타입을 갖는다**(안 적으면 `int`).\
그래서 (8)에서 clang 의 UBSan 이 `Scoped` 를 **지목하지 않았다.**\
위험한 것은 **범위도 없고 기저 타입도 안 적은** 쪽 하나뿐이다.\
★ 반대로 `: uint8_t` 를 적는 이유는 **UB 를 피하려는 것이 아니라 크기를 약속으로 만드는 것**이다((5)).

### 4. ★ 「`enum class` 니까 상속하거나 멤버를 넣을 수 있겠지」

못 한다. **`class` 라는 낱말이 붙었을 뿐 클래스가 아니다.**\
`enum struct` 라고 써도 **똑같다.**

### 5. ★ 「`-Wextra` 를 켰으니 `switch` 누락은 잡힌다」

안 잡힌다. **`-Wswitch` 는 `-Wall` 쪽**이다((9)) — `-Wextra` 만 주면 **0건**이다.\
★ 그리고 `default:` 를 넣으면 **`-Wall` 이어도 사라진다.**

### 6. ★ 「전방 선언은 `enum` 이면 다 된다」

**`enum B;` 는 안 된다**((7)). 크기를 모르기 때문이다.\
`enum class A;` 와 `enum C : int;` 는 된다.

### 7. ★ 「`using enum` 을 쓰면 정수 변환도 풀린다」

안 풀린다((10)). **이름만** 풀린다.\
그리고 **스코프 안에서만** 쓴다 — 헤더의 네임스페이스 범위에 두면 `enum class` 를 쓴 이유가 사라진다.

### 8. ★ 「기저 타입을 적으면 범위 있는 열거형이 된다」

아니다. **`enum PlainFixed : unsigned char` 는 여전히 범위 없는 열거형**이다((5)) —\
크기만 고정되고 **이름은 여전히 바깥에 풀려 있고 암묵 변환도 그대로**다.\
두 담장은 **따로 논다.**

### 9. 「gcc 의 sanitizer 가 조용하니 문제가 없다」

((8))에서 **gcc UBSan 은 0건, clang UBSan 은 1건**이었다.\
★ **같은 이름의 도구가 같은 것을 본다는 보장이 없다.**

### 10. 「`sizeof(enum class)` 는 구현 정의겠지」

**범위 있는 열거형은 기저 타입이 표준으로 `int`** 라 여기서는 뒤집히지 않는다((5)).\
구현 정의인 것은 **범위 없고 기저 타입도 안 적은** 쪽이다 — 그쪽의 정본 실측은\
C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)에 있다(`-fshort-enums` 로 4→1 을 뒤집어 보였다).

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| **범위 있는 열거형의 기본 기저 타입이 `int`** | **언어** |
| **이름이 열거형 안에 갇히는 것** · **암묵 변환이 없는 것** | **언어** |
| **다른 열거형끼리 비교가 안 되는 것** | **언어** |
| **`enum class` 의 전방 선언이 되는 것** | **언어** |
| **고정 기저 타입이면 그 타입의 모든 값이 유효한 것** | **언어** — (8)의 안전장치가 여기 있다 |
| `enum class` 와 `enum struct` 가 같은 것 | **언어** |
| **`using enum` 이 C++20** · **`to_underlying` 이 C++23** | **언어**(버전) |
| ★ `enum Plain` 의 기저 타입이 **`unsigned int`** 인 것 | **구현 정의.** gcc 의 선택이다 |
| ★ 그래서 `sizeof(Plain) == 4` 인 것 | **구현 정의** |
| ★ **clang UBSan 이 범위 밖 값을 잡고 gcc UBSan 은 못 잡는 것** | **도구 구현.** 둘 다 「UBSan」이라는 이름을 쓴다 |
| 진단 문구·캐럿 줄 모양 | **컴파일러 구현** |
| `-std=c++23` 에서 `__cplusplus` 가 `202100L` 인 것 | **이 gcc 의 구현**(정식 C++23 값은 `202302L`) |
| ★ `-O0` 과 `-O2` 에서 `Plain=200` 이 같았던 것 | ★ **관찰이다.** UB 이므로 **보장이 아니다** |

## 언제 쓰고 언제 안 쓰나

**`enum class` 를 쓴다.**

- **기본값으로.** 이름이 흔하거나 열거형이 여럿인 헤더에서는 특히.
- **의미가 정수가 아닌 것** — 상태·종류·모드. 「더하거나 빼는 것이 뜻이 없는」 것들.
- **바깥 데이터를 담을 때** — 단 **기저 타입을 적고** 값 검사를 따로 한다((8)).

**범위 없는 열거형을 남긴다.**

- **비트 플래그** — `|`·`&` 가 자연스러워야 하는 자리. (범위 있는 열거형으로 하려면 연산자를 직접 오버로드해야 한다 — 목록의 **22번 주제**.)
- **C 와 공유하는 헤더** — `enum class` 는 C 에 없다.
- **배열 인덱스 상수** — 정수로 바로 쓰는 것이 목적인 것. 다만 `static_cast` 한 번이 그렇게 비싸지 않다.

**안 쓴다.**

- **참·거짓 둘뿐인 것** — `bool` 이면 된다(이름이 필요하면 `enum class Verbose { No, Yes }` 가 낫긴 하다).
- **값이 계속 늘어나고 바깥에서 오는 것** — 그때는 열거형이 아니라 **검증하는 타입**을 만든다.

## 핵심 문장

1. **`enum class` 는 담장 둘을 세운다** — 이름 가두기와 암묵 변환 끊기. 둘은 **따로 논다.**
2. **C++ 로 컴파일하는 것만으로는 아무것도 안 고쳐진다** — `class` 를 붙여야 세 줄이 막힌다.
3. **범위 있는 열거형의 기저 타입은 표준이 `int` 로 정한다** — C 에서 구현 정의였던 자리가 여기서 표준이 된다.
4. **담장은 `static_cast` 로 넘을 수 있고, 넘는 자리가 코드에 글자로 남는다** — 그것이 값이다.
5. **범위 밖 값은 C 에서는 UB 가 아니고 C++ 에서는 될 수 있다** — 가르는 것은 **고정 기저 타입의 유무**다.
6. **그 UB 를 gcc 의 UBSan 은 못 보고 clang 의 UBSan 은 본다** — 도구 이름이 같다고 보는 것이 같지 않다.

## 관련 자료

- [C 갈래 `07-enum-and-enumeration-constants/`](../../../c/syntax/07-enum-and-enumeration-constants/) —\
  **C 의 `enum` 정본.** 크기·부호·`-fshort-enums`·중복 값·C23 고정 기반 타입·플래그별 경고 세기가 **전부 거기 있다.**\
  여기는 **C++ 가 새로 하는 것**(이름 가두기·암묵 변환 끊기·범위 밖 값의 판정)부터.
- [C 갈래 `12-control-flow-and-switch/`](../../../c/syntax/12-control-flow-and-switch/) — `switch` 문법의 정본. 여기는 **열거형 `switch` 의 경고**까지만.
- [**01번 형제**](../01-function-overloading-and-overload-resolution/) — (3)의 `operator==` 진단이 **후보 집합과 탈락 사유**를 말한다. 그 읽는 법이 거기 있다.
- [**03번 형제**](../03-four-cast-operators/) — `static_cast` 의 정본. (6)의 두 줄이 **왜 `static_cast` 인지**는 거기서 읽는다.
- [**04번 형제**](../04-brace-initialization-narrowing-and-initializer-list/) — `Color c{1}` 처럼 **중괄호로 열거형을 만드는** 문법(C++17)이 그쪽 경계다.
- 목록의 **22번 주제**(연산자 오버로딩) — 범위 있는 열거형으로 **비트 플래그**를 하려면 거기가 필요하다.
- 목록의 **47번 주제**(`variant`) — 「여럿 중 하나」에 **값까지 붙이고 싶을 때**의 답. 열거형은 값을 못 담는다.

## 용어 풀이

> **범위 있는 열거형(scoped enumeration)** — `enum class` / `enum struct`. 이름이 갇히고 암묵 변환이 없다.

> **범위 없는 열거형(unscoped enumeration)** — 그냥 `enum`. C 와 같은 모양.

> **열거자(enumerator)** — `Red`·`Green` 같은 이름 하나하나. ★ **C++ 에서 그 타입은 열거형 자체**이고 **C 에서는 `int`** 다((4)).

> **기저 타입(underlying type)** — 값을 실제로 담는 정수 타입. `std::underlying_type_t<E>` 로 물어본다.

> **고정 기저 타입(fixed underlying type)** — `enum E : T` 로 적어 준 것. **범위 있는 열거형은 안 적어도 고정**이다(`int`).\
> ★ 고정이면 **`T` 의 모든 값이 유효**하다 — (8)의 갈림이 여기서 난다.

> **`using enum E;`**(C++20) — 그 스코프에서 `E::` 를 생략할 수 있게 한다. **이름만** 푼다.

> **`std::to_underlying(e)`**(C++23) — `static_cast<std::underlying_type_t<E>>(e)` 에 붙인 이름.

> **UBSan(UndefinedBehaviorSanitizer)** — 미정의 동작을 실행 중에 잡는 도구.\
> ★ **gcc 판과 clang 판이 보는 것이 다르다**((8)).

## 더 들어가면

- **비트 플래그를 범위 있는 열거형으로** — `operator|`·`operator&` 를 직접 오버로드하거나\
  `std::underlying_type_t` 로 감싸는 래퍼를 만든다. 정본은 목록의 **22번 주제**.
- **`enum class` 와 `switch` 의 완전성 검사** — `-Wswitch` 가 유일한 자동 검사다((9)).\
  `default:` 를 안 쓰고 모든 열거자를 적는 것이 **컴파일러를 검사 도구로 쓰는 법**이다.
- **역직렬화 관용구** — 「기저 타입으로 읽고 → 범위 검사 → 캐스트」. 검사를 건너뛰면 (8)의 UB 다.\
  `std::optional<Color> to_color(std::uint8_t)` 처럼 **실패를 값으로** 내놓는 쪽이 낫다(목록의 **47번 주제**).
- **`enum class` 의 크기를 줄이는 것이 실제로 이득인가** — 구조체에 들어갈 때만이다.\
  단독 지역 변수는 정렬 때문에 차이가 없다. 정본은 C 갈래의\
  [`08-sizeof-alignment-and-offsetof/`](../../../c/syntax/08-sizeof-alignment-and-offsetof/).
- **C 헤더와 공유하기** — `enum class` 는 C 에 없다. 경계에서는 **고정 기저 타입을 쓴 범위 없는 열거형**을 두고\
  C++ 쪽에서만 감싸는 방법이 흔하다.
