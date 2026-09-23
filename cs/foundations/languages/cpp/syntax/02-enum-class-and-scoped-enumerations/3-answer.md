# cpp/syntax/02 — `enum class` 와 범위 있는 열거형 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고·에러는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **gcc 13.3.0**(C 대비) · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex`,\
> C 쪽은 `gcc -std=c17 -Wall -Wextra -pedantic ex.c -o ex` 다.\
> 파일 이름은 **`ex.cpp` 와 `ex.c` 둘뿐**이고 진단의 줄 번호는 그 파일 기준이다.\
> 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 `capture.sh` 가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★★ 이 주제의 네 번째 창은 **같은 프로그램을 C 로도 던지기**(1번·7번)다.
> **읽는 법** — 컴파일 진단과 실행 출력은 **블록을 갈라** 실었다.\
> 한 블록에 두 스트림을 섞으면 파이프로 받을 때 순서가 뒤집히기 때문이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 통과한다 — 경고는 **한 건**뿐이고 `999` 가 그대로 찍힌다

**출력 — 컴파일**

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

**출력 — 실행**

```text
===== ./ex (run exit=0) =====
c == APPLE
n=1 c=999
```

**왜 그런가**

- **컴파일은 통과한다**(`cc exit=0`). 경고는 **한 건**, `-Wenum-compare` 다.
- **세 줄 중 막히는 것은 없다.** `c + 1` 도, `c == APPLE` 도, `c = 999` 도 전부 통과한다.
- `c` 는 **999** 다. ★ **범위 밖 값이 아무 말 없이 들어간다.**
- **`if (c == APPLE)` 의 본문은 실행된다.** `RED` 도 `APPLE` 도 **0** 이라 참이다.\
  두 열거형이 **다른 타입인데도 정수로 내려가 비교**되기 때문이다.
- 이 셋의 정본 결론은 C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)에 있다 —\
  거기서 **여섯 플래그 조합 전부 0건**까지 세어 두었다. 여기서는 **대비 기준선**으로만 다시 던졌다.

### 2. ★★ 에러 **셋** — 그리고 `Fruit::Red` 는 아무 문제가 없다

**출력**

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

**왜 그런가**

| 줄 | 에러 |
|---|---|
| `int n = c + 1;` | `no match for 'operator+' (operand types are 'Color' and 'int')` |
| `if (c == Fruit::Red)` | `no match for 'operator==' (operand types are 'Color' and 'Fruit')` |
| `c = 999;` | `cannot convert 'int' to 'Color' in assignment` |

- **`enum class Fruit` 안의 `Red` 는 문제가 아니다.** 이름이 **`Fruit` 안에 갇혀** 있기 때문이다.\
  이 파일이 **저 세 줄에서만** 걸린 것이 그 증거다.
- **`candidate:` 줄은 둘**이다 — `operator==(Fruit, Fruit)` 와 `operator==(Color, Color)`,\
  각각 `no known conversion for argument 1 from 'Color' to 'Fruit'` ·\
  `no known conversion for argument 2 from 'Fruit' to 'Color'` 가 따라붙는다.\
  ★★ **내장 연산자도 오버로드 후보 집합에 들어간다**는 뜻이다 —\
  [**01번 형제**](../01-function-overloading-and-overload-resolution/)의 「실행 가능 후보」 절차 그대로다.
- clang 도 같은 셋을 잡되 후보를 나열하지 않는다.

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

- **범위 없는 `enum` 으로 두면 셋 중 하나만** 막힌다 — `c = 999;` 뿐이고,\
  나머지 둘은 **경고 한 건**으로 통과한다.

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

  ★★ **경고 문구가 C 와 한 글자도 다르지 않다.** 「C++ 로 옮기면 고쳐진다」가 틀린 이유다.

### 3. ★★ `4 / 1 / 4 / 1` — 그리고 두 개의 `4` 는 **다른 층**이다

**출력**

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

**왜 그런가**

| 선언 | `sizeof` | 기저 타입 | 누가 정하나 |
|---|---|---|---|
| `enum Plain` | **4** | `unsigned int` | ★ **구현 정의** |
| `enum PlainFixed : unsigned char` | **1** | `unsigned char` | 적어 준 대로 |
| `enum class Scoped` | **4** | **`int`** | ★ **표준** |
| `enum class ScopedFixed : unsigned char` | **1** | `unsigned char` | 적어 준 대로 |

- **`Plain` 의 기저 타입은 `unsigned int`** 이고 **정하는 것은 구현**이다.\
  gcc 가 「음수 열거자가 없으므로」 고른 것이다 — C 갈래\
  [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)이 같은 규칙을 C 에서 실측해 두었다.
- **`Scoped` 의 기저 타입은 `int`** 이고 **정하는 것은 표준**이다.\
  ★★ 여기가 C 와 갈리는 자리다 — C 에서는 크기도 부호도 **전부 구현 정의**였다.
- **`-fshort-enums` 로 뒤집히는 것은 `Plain` 하나**다 — 던져서 확인했다.

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

  나머지 셋은 **기저 타입이 정해져 있어서**(표준 또는 명시) 그 플래그의 사정거리 밖이다.\
  ★ 그래서 **범위 있는 열거형은 ABI 를 플래그 하나로 흔들 수 없다** — 이것이 실무적 값이다.\
  C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)이 같은 플래그로 C 의 `enum` 세 개를 4→1 로 뒤집은 것과\
  **같은 실험인데 흔들리는 칸이 하나로 줄었다.**

### 4. ★ 하나만 막힌다 — `enum B;`

**출력**

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

**왜 그런가**

- **막히는 것은 `enum B;` 하나**다. `enum class A;` 와 `enum C : int;` 는 **통과한다**\
  (그 둘에 대해서는 진단이 한 줄도 없다).
- **이유를 한 낱말로** — 「**크기**」다. 전방 선언은 **그 타입의 크기를 알아야** 성립한다.\
  `enum class` 는 기본 기저 타입이 **`int` 로 표준에 정해져** 있고, `enum C : int;` 는 적어 주었다.\
  `enum B;` 는 **열거자를 다 봐야** 기저 타입이 정해지므로 크기를 모른다.
- **clang 은 표준의 말로** 말한다 — `ISO C++ forbids forward references to 'enum' types`.

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
「**던져 보지 않았다**」고 밝혀 두었다. C++ 쪽은 **C++11부터** 위 갈림이 성립한다.

### 5. ★★★ 값은 같고, **clang 만 말한다** — 그리고 `Plain` 만 지목한다

**출력 — `-O0`**

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

**출력 — `-O2`**

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

**출력 — gcc 의 UBSan**

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

**출력 — clang 의 UBSan**

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

**왜 그런가**

- **`-O0` 과 `-O2` 의 출력이 같다** — `Scoped=200 Plain=200`.\
  ★ **「최적화 수준을 바꿔도 안 갈렸다」가 「UB 가 아니다」가 아니다.**
- **gcc 의 UBSan 은 0줄**이다. **clang 의 UBSan 은 2줄**(`runtime error:` + `SUMMARY:`)이고\
  **`Plain` 만** 지목한다 — `load of value 200, which is not a valid value for type 'Plain'`.
- **`Scoped` 가 안 지목되는 이유** — `enum class Scoped : unsigned char` 는 **고정 기저 타입**을 갖는다.\
  그러면 **유효한 값의 범위가 `unsigned char` 전체**가 되어 **200 은 유효한 값**이다.\
  ★ 범위 있는 열거형은 **기저 타입을 안 적어도 고정**(`int`)이므로 **언제나 이쪽**이다.
- **`Plain` 이 지목되는 이유** — `enum Plain { P_A = 0, P_B = 1 }` 은 고정 기저 타입이 없다.\
  유효 범위는 **열거자를 담는 최소 비트 폭**까지이고 **200 은 그 밖**이다.
- **C 편과 갈린다.** C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)은\
  「**범위 밖 값을 넣는 것은 UB 가 아니다 — 이 주제에서 만들 수 있는 UB 는 열거 타입 자체로는 없다**」로 결론지었다.\
  ★★ **C++ 에서는 그 결론이 「고정 기저 타입이 없을 때는 아니다」로 갈린다.**\
  그리고 **그 사실을 gcc 쪽 도구는 한 줄도 말해 주지 않는다.**

### 6. ★ C++20 에서는 `Green` 이 찍히고, C++17 에서는 에러 **네 줄**이 난다

**출력 — `-std=c++20`**

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

**출력 — `-std=c++17`**

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

**왜 그런가**

- **`-std=c++20` 에서 컴파일·실행된다.** 출력은 `Green` 이다.\
  ★ 「g++ 13 이 C++20 을 어디까지 하나」에 대한 **실측 하나**다 — 추측으로 적지 않는다.
- **`-std=c++17` 에서는 에러가 네 줄**이다.\
  첫 줄이 `using enum` 자체(`'using enum' only available with '-std=c++20' or '-std=gnu++20'`),\
  나머지 **셋은 그 결과**다 — `using enum` 이 실패했으니 `case Red:`·`case Green:`·`case Blue:` 가\
  각각 이름을 못 찾아 같은 문구로 한 번씩 걸린다.\
  ★ **에러 개수가 「문제 개수」가 아니라 「연쇄 개수」인 전형**이다. 첫 줄만 고치면 넷이 사라진다.
- **진단이 버전을 말해 준다** — `'-std=c++20' or '-std=gnu++20'`.\
  ★ **「미지원」을 한 낱말로 적지 말라**는 규칙의 좋은 예다.

### 7. C 는 `int` 로, C++ 은 열거형 타입으로 — 그리고 `enum class` 는 아예 안 부딪힌다

**출력 — C**

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

**출력 — C++ 의 범위 없는 열거형**

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

**출력 — `enum class`**

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

**왜 그런가**

- **둘 다 에러**다. 열거 상수가 **바깥 스코프에 풀려 있어서** 두 번째 선언이 첫 번째와 부딪힌다.
- **`note:` 가 말하는 타입이 다르다.**
  - C — `previous definition of 'RED' with type 'enum Color'`
  - C++ — `previous declaration 'Color RED'`
  ★ 진단이 쓰는 말은 달라도 **가리키는 사실은 같다** — 그 이름이 이미 그 스코프에 있다는 것.\
  단 **열거자 자체의 타입**은 갈린다 — **C 에서는 `int`**(C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)의 결론),\
  **C++ 에서는 그 열거형**(`Color`)이다.
- **`enum class` 로 바꾸면 공존한다** — 이름이 **열거형 안에** 들어가므로 바깥 스코프에서 부딪힐 것이 없다.\
  출력 `0 0` 은 **둘 다 첫 열거자라 0** 이라는 뜻이고, **컴파일이 됐다는 것 자체가 답**이다.
- ★ **C 갈래는 이 문제를 따로 다루지 않았다.** 거기서 다룬 것은 **스코프 차이**(열거 상수는 블록 스코프,\
  `#define` 은 파일 끝까지)였다. **열거자끼리의 이름 충돌은 C++ 가 새로 푸는 문제**다.

### 8. 담장은 둘, 그리고 넷이 각각 다른 것을 건드린다

**왜 그런가**

| 것 | 담장 ① 이름 가두기 | 담장 ② 암묵 변환 끊기 | 크기 고정 |
|---|---|---|---|
| `enum E { A, B };` | 없음 | 없음 | 없음(구현 정의) |
| `enum E : unsigned char { A, B };` | 없음 | 없음 | **있음** |
| `enum class E { A, B };` | **있음** | **있음** | 있음(`int`) |
| `enum class E : unsigned char { A, B };` | **있음** | **있음** | **있음** |

- **담장 둘의 이름** — ① **이름 가두기**(열거자를 `E::` 안에 넣는다) · ② **암묵 변환 끊기**(정수와 오간다).
- **`enum E : unsigned char` 는 둘 다 안 세운다.** 크기만 고정한다 —\
  ★ **「기저 타입을 적었으니 안전해졌겠지」가 틀린 자리**다.
- **`using enum E;` 는 ①만 낮춘다**(그 스코프 안에서). ②는 그대로다.
- **`static_cast` 는 ②를 넘는다.** ①과는 무관하다.
- ★ 둘이 **따로 논다**는 것이 이 절의 전부다.

### 9. `-Wall` 에 있다 — `-Wextra` 만으로는 **0건**

**출력**

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

**출력 — 플래그별로 세기**

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

**왜 그런가**

- **`-Wall` 1건 · `-Wextra` 0건**이다. `-Wswitch` 는 `-Wall` 쪽에 들어 있다.\
  `-Wswitch-enum` 을 직접 주어도 1건이다(그쪽은 `default:` 가 있어도 말해 준다).
- **`cc exit` 은 전부 0** 이다 — 경고일 뿐이라 **컴파일은 통과한다.**\
  ★ 「경고 0건」과 「`exit=0`」을 **갈라 읽어야** 하는 전형이다. `-Wextra` 만 켜고\
  「경고 0건, exit 0」을 근거로 쓰면 **열거자 하나를 빠뜨린 코드가 통과한다.**
- **이 방어선을 없애는 습관은 `default:` 를 쓰는 것**이다.\
  열거형 `switch` 에 `default:` 를 넣으면 `-Wswitch` 가 침묵한다\
  (C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)이 C 에서 실측해 두었다).\
  ★ 「**새 열거자를 컴파일러가 찾아 주길 원하나**」로 정한다.

### 10. 11 / 11 / 20 / 23

**왜 그런가**

| 것 | 언제부터 | 이 머신에서 |
|---|---|---|
| `enum class`(범위 있는 열거형) | **C++11** | 됨 |
| 기저 타입 지정(`enum E : T`) | **C++11** | 됨 |
| `using enum` | **C++20** | ★ **됨**(6번) |
| `std::to_underlying` | **C++23** | `-std=c++23` 에서 됨 |

**출력 — `-std=c++23`**

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

**출력 — `-std=c++20`**

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

- g++ 가 붙이는 `note:` 는 **`'std::to_underlying' is only available from C++23 onwards`** 다.\
  ★ 「없다」가 아니라 「**다음 표준에 있다**」까지 말해 준다.
- **이 g++ 의 `-std=c++23` 에서 `__cplusplus` 는 `202100L`** 이다 — **정식 C++23 값 `202302L` 이 아니다.**\
  아직 초안 값을 쓰고 있다는 뜻이고, ★ **「`-std=c++23` 으로 돌렸다」가 「C++23 을 다 쓴다」가 아니다.**\
  C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)이 `-std=c2x` 와 `__STDC_VERSION__ 202000L` 로 적어 둔 것과 **같은 모양**이다.

### 11. 이 주제의 지도

**왜 그런가**

- **`candidate` · `no known conversion` 은 오버로드 해석의 언어**다 —\
  정본은 [**01번 형제**](../01-function-overloading-and-overload-resolution/).\
  (2)의 `operator==` 진단은 **내장 연산자가 후보 집합에 들어간 것**을 보여 준다.
- **`static_cast` 의 정본은 [03번 형제](../03-four-cast-operators/)** 다.\
  여기서는 **담장 ②를 넘는 도구**로만 썼다.
- **「값까지 담는 열거형」은 목록의 47번 주제**(`variant`)다. 열거형은 **이름만** 담는다.
- **비트 플래그를 `enum class` 로** 하려면 **목록의 22번 주제**(연산자 오버로딩)가 필요하다 —\
  `operator|`·`operator&` 를 직접 써야 한다.
- **C 의 `enum` 크기·부호·`-fshort-enums`·중복 값·플래그별 경고 세기**의 정본은\
  C 갈래 [`07-enum-and-enumeration-constants/`](../../../c/syntax/07-enum-and-enumeration-constants/)다.\
  이 문서는 **거기서 결론 난 것을 되짚기만** 하고 새로 파지 않았다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 명령으로 돌렸나 |
|---|---|---|
| C 의 `enum` 세 자리 (`ex.c`) | **경고 1건**(`-Wenum-compare`) · `cc exit=0` · `n=1 c=999` · `c == APPLE` 실행됨 | gcc `-std=c17 -Wall -Wextra -pedantic` |
| 같은 세 줄 · 범위 없는 열거형 | **경고 1건 — C 와 같은 문구** · `c = 999` 만 에러라 캐스트로 바꿈 | g++ `-std=c++20 -Wall -Wextra -pedantic` |
| 같은 세 줄 · `enum class` | **에러 3** · `operator==` 에 **내장 후보 2 나열** | g++ · clang |
| 이름 충돌 (`ex.c` / `ex.cpp`) | 둘 다 **에러** · `note:` 의 타입이 `enum Color` 대 `Color RED` | gcc · g++ |
| `enum class` 이름 충돌 | **통과** — `0 0` | g++ |
| 크기·기저 타입 4벌 | `4 / 1 / 4 / 1` · `Plain`=`unsigned int`, `Scoped`=`int` | g++ |
| ★ `-fshort-enums` | **`Plain` 만 4→1** · `Scoped` 는 4 유지 | g++ `-fshort-enums` |
| `static_cast` 왕복 | **통과** — `n=1 back==Green: 1` | g++ |
| `std::to_underlying` | `-std=c++23` **통과(`1`)** · `-std=c++20` **에러 + `note:` 가 버전을 말함** | g++ ×2 |
| 전방 선언 3종 | **`enum B;` 만 에러** · clang 은 `ISO C++ forbids …` | g++ · clang |
| ★ 범위 밖 값 | `-O0`·`-O2` **값 같음** · **gcc UBSan 0줄 · clang UBSan 2줄, `Plain` 만 지목** | g++ ×3 · clang ×1 |
| `using enum` | `-std=c++20` **통과(`Green`)** · `-std=c++17` **에러 4줄** | g++ ×2 |
| `switch` 누락 | `-Wall` **1건** · `-Wextra` **0건** · `cc exit` 전부 **0** | g++ 플래그 6벌 |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++/gcc 13.3.0 · clang 18.1.3)에서만** 그렇다.

- `enum Plain` 의 기저 타입이 **`unsigned int`** 인 것과 그래서 `sizeof` 가 **4** 인 것 — **구현 정의**.
- ★ **clang UBSan 이 잡고 gcc UBSan 이 못 잡는 것** — **도구 구현.** 둘 다 이름은 「UBSan」이다.
- 진단 문구 전부 · `candidate:` 줄의 개수 · 캐럿 줄 모양.
- `-std=c++23` 에서 `__cplusplus` 가 **`202100L`** 인 것.
- `-std=c++17` 에서 `using enum` 이 **에러 4줄**로 번지는 것(연쇄 진단은 컴파일러 재량이다).

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- 범위 있는 열거형의 기본 기저 타입이 **`int`** · 이름 가두기 · 암묵 변환 없음(양방향) ·
  다른 열거형과 비교 불가 · `enum class` 의 전방 선언 가능 ·
  **고정 기저 타입이면 그 타입의 모든 값이 유효**.
- ★ **`-O0`·`-O2` 에서 `Plain=200` 이 같았던 것은 관찰이다.** UB 이므로 **보장이 아니다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `enum class` 에 `operator|` 를 붙인 비트 플래그(목록의 **22번 주제**) ·\
  `clang -fsanitize=enum` 을 **따로** 켜 본 것(기본 집합에 들어 있어서 그냥 잡혔다) ·\
  `enum class` 를 C 헤더와 공유하는 실제 빌드.
- **못 잰 것** — 「값이 열거자 중 하나인지」를 **타입 수준에서** 검사하는 방법.\
  C++20 에는 그런 기능이 없고, 반사(reflection)가 들어오기 전에는 **매크로나 코드 생성**이 답이라\
  이 주제의 실측 대상이 아니다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- **gcc 의 UBSan 이 범위 밖 열거형 값을 잡게 되었는지** — 이 문서에서 가장 먼저 다시 찍을 자리다.
- `-std=c++23` 의 `__cplusplus` 가 `202302L` 이 되었는지.
- `using enum` 과 `std::to_underlying` 의 진단 문구.
- `-Wswitch` 가 여전히 `-Wall` 쪽인지.
