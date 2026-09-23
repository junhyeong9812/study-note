# cpp/syntax/02 — `enum class` 와 범위 있는 열거형 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — **C 에서 통과하던 줄이 여기서 어떻게 되는지**,
> 그리고 **어느 도구가 무엇을 말하는지**를 맞힐 수 있는지 묻는다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · gcc 13.3.0(C 대비) · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex`,
> C 쪽은 `gcc -std=c17 -Wall -Wextra -pedantic ex.c -o ex && ./ex`.
> ★★ **이 주제에는 UB 가 하나 있다** — 그리고 **한쪽 sanitizer 만 그것을 말한다.**
> 「도구가 조용하다」를 근거로 쓰지 않는 연습이 5번이다.
> 선행 — C 갈래의 [`07-enum-and-enumeration-constants/`](../../../c/syntax/07-enum-and-enumeration-constants/)(C 의 `enum`).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ C 의 `enum` 에 세 가지를 시켜 보면 (예측)

```c
/* ex.c */
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
```

- 컴파일되는가? 경고는 **몇 건**이고 무슨 플래그인가?
- 세 줄 중 **막히는 것**이 있는가?
- 실행하면 무엇이 찍히는가 — `c` 는 얼마인가?
- `if (c == APPLE)` 의 본문이 실행되는가? 왜?

### 2. ★★ 같은 세 줄을 `enum class` 로 바꾸면 (예측)

```cpp
/* ex.cpp */
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
```

- 에러가 **몇 개** 나는가? 각각 어느 줄인가?
- `enum class Fruit` 안에 `Red` 라는 이름을 또 쓴 것은 문제가 되는가?
- `operator==` 진단에 `candidate:` 줄이 **몇 개** 붙는가? 그것이 무엇을 말하는가?
- 같은 소스를 **범위 없는** `enum` 으로 두면 셋 중 몇 개가 막히는가?

### 3. ★★ 범위 유무 × 고정 유무 네 벌의 크기와 기저 타입 (예측)

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

- 네 줄의 `sizeof` 는 각각 얼마인가?
- `Plain` 의 기저 타입은 무엇인가 — 그리고 그것은 **누가 정하는가**?
- `Scoped` 의 기저 타입은 무엇인가 — 그것은 **누가 정하는가**?
- 이 넷 중 **`-fshort-enums` 로 뒤집을 수 있는** 것이 있는가?

### 4. ★ 전방 선언 셋 중 무엇이 막히나 (예측)

```cpp
/* ex.cpp */
// 전방 선언이 되는 조건 — 기저 타입을 아는가
enum class A;      // 범위 있는 열거형: 기저 타입 기본값이 int 라 크기를 안다
enum       B;      // 범위 없고 기저 타입도 없다
enum       C : int;// 기저 타입을 적어 주면

int main() {}
```

- 셋 중 **몇 개**가 막히는가? 어느 것인가?
- 막히는 이유를 한 낱말로 말할 수 있는가?
- clang 은 그 이유를 **어느 문서의 말로** 말하는가?

### 5. ★★★ 범위 밖 값을 두 열거형에 넣고 sanitizer 를 걸면 (예측)

```cpp
/* ex.cpp */
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
```

- `-O0` 과 `-O2` 의 출력이 같은가?
- **gcc 의 UBSan** 은 몇 줄을 말하는가?
- **clang 의 UBSan** 은 몇 줄을 말하는가? 그리고 **둘 중 어느 열거형**을 지목하는가?
- 지목되지 않은 쪽은 **왜** 안 지목되는가?
- C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)은 같은 자리를 무엇이라고 결론지었는가? 여기서 갈리는가?

### 6. ★ `using enum` 을 `-std=c++17` 로 던지면 (예측)

```cpp
/* ex.cpp */
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
```

- `-std=c++20` 에서는 컴파일되는가? 무엇이 찍히는가?
- `-std=c++17` 에서는 에러가 **몇 줄** 나는가? 왜 그 개수인가?
- 그 진단이 **버전을 말해 주는가**?

### 7. C 와 C++ 에서 열거자 이름이 부딪히면 (왜)

- `enum Color { RED }` 와 `enum Signal { RED }` 를 같이 두면 C 에서 어떻게 되는가? C++ 에서는?
- 두 진단의 `note:` 가 말하는 **`RED` 의 타입**이 서로 다르다. 각각 무엇인가?
- `enum class` 로 바꾸면 왜 공존하는가?
- ★ 이 문제를 C 갈래 [`07번`](../../../c/syntax/07-enum-and-enumeration-constants/)이 다뤘는가?

### 8. 담장 둘의 경계 (경계)

- `enum class` 가 세우는 담장 **둘**을 이름 붙일 수 있는가?
- `enum E : unsigned char`(범위 없음 + 고정)는 그중 **몇 개**를 세우는가?
- `using enum E;` 는 그중 **어느 것**을 낮추는가?
- `static_cast` 는 어느 것을 넘는가?

### 9. `switch` 누락 경고는 어디 붙어 있나 (경계)

- 열거자 하나를 빠뜨린 `switch` 에 대해 `-Wall` 은 몇 건, `-Wextra` 는 몇 건인가?
- 그때 `cc exit` 은 얼마인가?
- 이 방어선을 **없애 버리는** 코딩 습관 하나는?

### 10. 버전 경계 (경계)

- `enum class` · 기저 타입 지정 · `using enum` · `std::to_underlying` 은 각각 **몇 년 표준**부터인가?
- `-std=c++20` 에서 `std::to_underlying` 을 쓰면 g++ 는 무슨 `note:` 를 붙이는가?
- 이 g++ 의 `-std=c++23` 에서 `__cplusplus` 는 얼마인가 — 정식 값과 같은가?

### 11. 다른 주제와 잇기 (연결)

- (3)의 `operator==` 진단이 쓰는 낱말(`candidate` · `no known conversion`)은 형제 주제 몇 번의 언어인가?
- `static_cast` 의 정본은 형제 주제 몇 번인가?
- 「값까지 담는 열거형」이 필요하면 목록의 몇 번을 보나?
- 비트 플래그를 `enum class` 로 하려면 목록의 몇 번이 필요한가?
- C 의 `enum` 크기·부호·`-fshort-enums` 의 정본은 어느 갈래 어느 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
