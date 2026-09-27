# cpp/syntax/24 — `explicit` 과 변환 생성자 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — `explicit` 지정자](https://en.cppreference.com/w/cpp/language/explicit) · [cppreference — 암묵 변환](https://en.cppreference.com/w/cpp/language/implicit_conversion) · [cppreference — 변환 생성자](https://en.cppreference.com/w/cpp/language/converting_constructor)\
> ★ cppreference 두 쪽은 2026-09-26 에 열어 **네 문장을 확인했다** — ① `explicit` 은 「**암묵 변환과 복사 초기화에 쓰일 수 없다**」 ·\
> ② `explicit(식)` 은 C++20 이고 「**그 상수식이 `true` 일 때만 explicit**」 · ③ 암묵 변환 순서는 「**표준 변환 0\~1 → 사용자 정의 변환 0\~1 → 표준 변환 0\~1**」 ·\
> ④ **문맥적 bool 변환**은 「`bool t(e);` 가 성립하면」 수행되고 그래서 **`explicit operator bool` 이 고려된다** — 자리는 `if`·`while`·`for` 의 조건, `!`·`&&`·`||` 의 피연산자, `?:` 의 첫 피연산자, `static_assert`, `noexcept`.\
> 「변환 생성자」 쪽은 **이 배치에서 열지 못했다**(도구 한도) — 그 쪽 규칙은 이 문서가 **전부 컴파일러에 던져서** 확인했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`conv01.cpp` \~ `conv08.cpp` · `conv-grid.sh`). ★ (7)만 **`-std=c++17`** 판을 더 던졌고, **배너에 적었다.**\
> ★ **한 소스를 매크로로 두 판에 던졌다** — `-DASK_EXPLICIT` 는 **같은 생성자에 `explicit` 을 붙이고**, `-DASK_IMPLICIT` 은 **`operator bool` 에서 뗀다.** 소스가 하나라 두 판의 차이가 **그 한 낱말**임이 보장된다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. 소스 펜스의 배너도 **캡처가 찍은 것**이다.
> **버전** — 변환 생성자·`explicit` 생성자는 **C++98부터**, **`explicit` 변환 함수(`explicit operator bool`)는 C++11부터**, **`explicit(bool)` 은 C++20부터**다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.
> ★★★ **앞 편이 이 주제의 절반을 이미 쟀다 — 다시 재지 않고 인용한다.**\
> [22번](../22-operator-overloading/) (1) — 「**`1 + a` 는 비멤버 × 암묵 변환일 때만 되고, 생성자에 `explicit` 을 붙이면 비멤버여도 에러 2 · 2**」.\
> [13번](../13-constructors-member-init-list-and-delegating/) 「금지 사례」 — `explicit B(int)` 에 `takeB(3)` 을 넘기면 `could not convert '3' from 'int' to 'B'` · 「어디서 틀리나 6」 — **`Feet c{5}` 는 되고 `Feet b = {5}` 는 막힌다.**\
> [4번](../04-brace-initialization-narrowing-and-initializer-list/) (4) — **비상수 좁히기를 g++ 는 경고로 통과시키고 clang 은 에러로 막는다.**\
> ★★ **여기서 새로 묻는 것은 「암묵 변환이 만드는 사고」 쪽이다** — **어느 자리에서 몇 번 불리나(호출 로그)** · **`explicit` 이 어느 칸을 에러로 바꾸나(격자)** · **엉뚱한 오버로드가 불리는 자리** · **`explicit operator bool`**.
> **경계** — 「생성자 문법 일반」은 [13번](../13-constructors-member-init-list-and-delegating/)이, 「대칭 변환과 연산자」는 [22번](../22-operator-overloading/)이,\
> 「오버로드 해결의 순위」는 [1번](../01-function-overloading-and-overload-resolution/)이, 「중괄호 초기화와 좁히기」는 [4번](../04-brace-initialization-narrowing-and-initializer-list/)이 정본이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 두 컴파일러의 **진단 문구** · note 의 수 | ★★★ **생성자가 몇 번 불렸나**(호출 로그) · **어느 오버로드가 불렸나** — 이 주제의 답 자체다 |
> | — | ★★★ **어느 줄이 에러인가 · 에러 개수 · `cc exit`** · ★★ **격자의 O/X** · **타입 특성의 0/1** · **경고 개수** |

## 한눈에 — 쉽게 말하면

**인자 하나짜리 생성자는 「자동 환전기」다.**

지갑에 달러가 들어 있는데 가게가 원화만 받는다. 계산대 옆에 **자동 환전기**가 붙어 있으면 손님이 아무 말도 안 해도 **달러가 원화로 바뀌어** 결제된다. 편하다 —\
그런데 손님이 **동전을 흘렸는데 환전기가 그것까지 원화로 바꿔 결제해 버리면?** 아무도 결제를 원하지 않았는데 **결제가 됐다.**

- **변환 생성자 `Meter(int)`** — 계산대 옆 **자동 환전기**다. `int` 가 필요한 자리에 들어오면 **말없이 `Meter` 로 바뀐다.**
- **`explicit Meter(int)`** — 환전기를 **창구 안쪽으로** 옮긴다. **「환전해 주세요」라고 말해야**(`Meter(5)` · `Meter{5}`) 바뀐다.
- **`explicit operator bool`** — 「**참이냐 거짓이냐만** 묻는 자리」(`if (h)`)에서는 창구가 알아서 답해 준다. **숫자로 바꿔 달라**(`int n = h`)는 요청은 거절한다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 계산대 옆 자동 환전기 | ★★★ **인자 하나짜리 비`explicit` 생성자** | (1) |
| 아무도 모르게 결제된다 | ★★★ **복사 초기화·인자·반환·`==`·삼항에서 말없이 불린다** | (1) |
| 창구 안쪽 환전기 | ★★★ **`explicit`** — 직접 초기화·캐스트만 된다 | (2) |
| 환전은 한 번만 | ★★ **사용자 정의 변환은 한 번만** — `const char*` → `string` → `Name` 은 막힌다 | (3) |
| 동전이 원화로 결제된다 | ★★★ **엉뚱한 오버로드** — `show("hello")` 가 `show(bool)` 로 간다 | (4) |
| 「참이냐 거짓이냐」 창구 | ★★★ **문맥적 bool 변환** — `explicit operator bool` 이 `if` 에서만 열린다 | (5) |
| 조건부로 옮기는 환전기 | ★ **`explicit(bool)`**(C++20) | (7) |

```text
   struct Meter { Meter(int); };          자동 환전기

   Meter a = 5;       int -> Meter  말없이      ★ 복사 초기화
   take(6);           int -> Meter  말없이      ★ 인자
   return 7;          int -> Meter  말없이      ★ 반환
   m == 1             int -> Meter  말없이      ★ 연산자 인자

   explicit Meter(int);                    창구 안쪽 환전기

   위 네 줄           전부 에러                  ★ 「말없이」가 금지된다
   Meter a(5);  Meter a{5};  Meter(5);  static_cast<Meter>(5);  emplace_back(5)
                      그대로 된다                ★ 「환전해 주세요」라고 말한 자리
```

## 이 주제가 답하려는 질문

1. ★★★ **인자 하나짜리 생성자는 어느 자리에서 말없이 불리나** — 그리고 `explicit` 은 그중 **어느 자리를 막고 어느 자리를 남기나**((1)(2)).
2. ★★ **암묵 변환이 만드는 사고는 어떤 모양인가** — 엉뚱한 오버로드 · 조용한 값 잘림 · 두 객체가 「같다」((4)(5)(6)).
3. ★★ **`explicit operator bool` 은 왜 `if` 에서는 되고 `int n = h` 에서는 안 되나**((5)).
4. ★ **변환은 몇 단계까지 이어지나** · **C++20 `explicit(bool)` 은 무엇을 푸나**((3)(7)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① 호출 로그다

★★★ **이 주제의 본체는 ① 호출 로그다** — 「**생성자에 로그를 심고 어느 자리에서 몇 번 불리나**」가 규칙의 전부를 보여 준다.\
★★ **짝이 ② 두 컴파일러 대조의 격자**다 — `explicit` 한 낱말로 **어느 칸이 에러로 바뀌나.**

```text
① 호출 로그             어느 자리에서 생성자가 몇 번 · 어느 오버로드가 불렸나   (1)(4)(5)
② 두 컴파일러 대조       explicit 격자 15칸 · 두 단계 변환 · 좁히기의 진단 전문   (2)(3)(6)
③ ASan                   —                                                        부적용
④ 어셈블리               —                                                        부적용
⑤ 경고 격자              엉뚱한 오버로드를 몇 개의 플래그가 보나                  (4)
⑥ <type_traits>          is_convertible 대 is_constructible — explicit 이 가르는 것 (2)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ★★★ **① 호출 로그** | ★★★ **본체** — `calls 1` · `calls 0` · **`show(bool)`** | **쓴다** |
| ★★ **② 두 컴파일러 대조** | ★★ **짝** — 격자 `10 / 15` · 두 컴파일러가 갈린 칸 `0 / 15` | **쓴다** |
| ③ ASan | ★ **부적용** — 변환은 메모리를 건드리지 않는다. **잴 것이 없다** | **안 쓴다** |
| ④ 어셈블리 | ★ **부적용** — 변환 생성자는 **평범한 생성자 호출**이다. 비용 주장이 없다 | **안 쓴다** |
| ⑤ 경고 격자 | `show("hello")` 를 **다섯 플래그 중 둘만** 본다(clang 쪽만) | **쓴다** |
| ⑥ `<type_traits>` | `explicit` 이 **`is_convertible` 을 0 으로, `is_constructible` 은 1 로** 둔다 | **쓴다** |

- ★★ **③④ 를 부적용으로 둔 이유** — 이 주제의 질문은 「**불렸나**」이지 「얼마나 드나」가 아니다. 변환 생성자 호출은 **보통 생성자 호출과 같은 코드**다.\
  ★ 「잴 것이 없다」가 결론이다 — 「안 쟀다」가 아니다.

### (1) ★★★ 호출 로그 — 인자 하나짜리 생성자는 어디서 말없이 불리나

**언제 쓰나** — 「이 생성자에 `explicit` 을 붙일까?」를 판단할 때마다. **이 절이 이 주제의 중심이다.**

```cpp
/* conv01.cpp */
// 인자 하나짜리 생성자에 로그를 심었다 — 어느 자리에서 몇 번 불리나
// -DASK_EXPLICIT 이면 같은 생성자에 explicit 을 붙인다
#include <cstdio>

#ifdef ASK_EXPLICIT
#define MAYBE_EXPLICIT explicit
#else
#define MAYBE_EXPLICIT
#endif

static int calls = 0;

struct Meter {
    int v;
    MAYBE_EXPLICIT Meter(int x) : v(x) { ++calls; std::printf("      Meter(int %d)\n", x); }
};
bool operator==(Meter a, Meter b) { return a.v == b.v; }
void take(Meter m) { std::printf("      take(Meter %d)\n", m.v); }
Meter give() { return 7; }

static void done() { std::printf("    calls %d\n", calls); calls = 0; }

int main(int argc, char**) {
    bool yes = argc > 0, no = argc < 0;      // 실행 시점에 정해지는 참·거짓
    Meter m(1);
    calls = 0;

    std::printf("(1) Meter a = 5;\n");
    { Meter a = 5; (void)a; }
    done();

    std::printf("(2) take(6);\n");
    take(6);
    done();

    std::printf("(3) Meter c = give();\n");
    { Meter c = give(); (void)c; }
    done();

    std::printf("(4) m == 1\n");
    { bool e = (m == 1); std::printf("      -> %d\n", (int)e); }
    done();

    std::printf("(5) yes ? m : 9\n");
    { Meter t = yes ? m : 9; (void)t; }
    done();

    std::printf("(6) no ? m : 9\n");
    { Meter t = no ? m : 9; (void)t; }
    done();
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic conv01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
      Meter(int 1)
(1) Meter a = 5;
      Meter(int 5)
    calls 1
(2) take(6);
      Meter(int 6)
      take(Meter 6)
    calls 1
(3) Meter c = give();
      Meter(int 7)
    calls 1
(4) m == 1
      Meter(int 1)
      -> 1
    calls 1
(5) yes ? m : 9
    calls 0
(6) no ? m : 9
      Meter(int 9)
    calls 1
```

- ★★★ **다섯 자리에서 말없이 불렸다** — 복사 초기화 `Meter a = 5;` · 인자 `take(6)` · 반환 `return 7;` · 연산자 인자 `m == 1` · 삼항의 가지 `no ? m : 9`.\
  ★ **어느 자리에도 `Meter` 라는 글자가 없다** — 읽는 사람은 **생성자가 돈다는 것을 코드에서 볼 수 없다.**
- ★★★ **(5)는 `calls 0`, (6)은 `calls 1`** 이다 — **같은 식 `? m : 9`** 인데 갈렸다.\
  ★ 삼항의 **타입은 `Meter` 로 정해지고**(`9` 를 `Meter` 로 바꾸는 변환이 **식에 들어간다**), **실제로 그 가지를 밟을 때만** 생성자가 돈다.\
  ★★ **「변환이 식에 있다」와 「변환이 실행됐다」는 다르다** — 앞 배치의 「**탐침을 심었다 ≠ 경로를 밟았다**」가 이 자리에도 있다.
- ★★ **(4) `m == 1` 에서 `Meter(int 1)` 이 한 번** — 비멤버 `operator==(Meter, Meter)` 의 **오른쪽 인자**가 변환됐다([22번](../22-operator-overloading/) (1)의 대칭).
- ★ **첫 줄 `Meter(int 1)` 은 `Meter m(1);`** 이다 — 직접 초기화라 **`explicit` 과 무관하게** 늘 된다. 그래서 세기 전에 `calls = 0` 으로 지웠다.
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic conv01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
      Meter(int 1)
(1) Meter a = 5;
      Meter(int 5)
    calls 1
(2) take(6);
      Meter(int 6)
      take(Meter 6)
    calls 1
(3) Meter c = give();
      Meter(int 7)
    calls 1
(4) m == 1
      Meter(int 1)
      -> 1
    calls 1
(5) yes ? m : 9
    calls 0
(6) no ? m : 9
      Meter(int 9)
    calls 1
```

★★★ **같은 소스에 `-DASK_EXPLICIT` 을 주면** — 생성자에 `explicit` 이 붙는다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DASK_EXPLICIT -fmax-errors=0 conv01.cpp -o ex (cc exit=1) =====
conv01.cpp: In function ‘Meter give()’:
conv01.cpp:19:23: error: could not convert ‘7’ from ‘int’ to ‘Meter’
   19 | Meter give() { return 7; }
      |                       ^
      |                       |
      |                       int
conv01.cpp: In function ‘int main(int, char**)’:
conv01.cpp:29:17: error: conversion from ‘int’ to non-scalar type ‘Meter’ requested
   29 |     { Meter a = 5; (void)a; }
      |                 ^
conv01.cpp:33:10: error: could not convert ‘6’ from ‘int’ to ‘Meter’
   33 |     take(6);
      |          ^
      |          |
      |          int
conv01.cpp:41:19: error: no match for ‘operator==’ (operand types are ‘Meter’ and ‘int’)
   41 |     { bool e = (m == 1); std::printf("      -> %d\n", (int)e); }
      |                 ~ ^~ ~
      |                 |    |
      |                 |    int
      |                 Meter
conv01.cpp:17:6: note: candidate: ‘bool operator==(Meter, Meter)’
   17 | bool operator==(Meter a, Meter b) { return a.v == b.v; }
      |      ^~~~~~~~
conv01.cpp:17:32: note:   no known conversion for argument 2 from ‘int’ to ‘Meter’
   17 | bool operator==(Meter a, Meter b) { return a.v == b.v; }
      |                          ~~~~~~^
conv01.cpp:45:21: error: operands to ‘?:’ have different types ‘Meter’ and ‘int’
   45 |     { Meter t = yes ? m : 9; (void)t; }
      |                 ~~~~^~~~~~~
conv01.cpp:49:20: error: operands to ‘?:’ have different types ‘Meter’ and ‘int’
   49 |     { Meter t = no ? m : 9; (void)t; }
      |                 ~~~^~~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DASK_EXPLICIT -ferror-limit=0 conv01.cpp -o ex 2>&1 | grep -E 'error:|generated' (cc exit=1) =====
conv01.cpp:19:23: error: no viable conversion from returned value of type 'int' to function return type 'Meter'
conv01.cpp:29:13: error: no viable conversion from 'int' to 'Meter'
conv01.cpp:33:5: error: no matching function for call to 'take'
conv01.cpp:41:19: error: invalid operands to binary expression ('Meter' and 'int')
conv01.cpp:45:21: error: incompatible operand types ('Meter' and 'int')
conv01.cpp:49:20: error: incompatible operand types ('Meter' and 'int')
6 errors generated.
```

- ★★★ **에러가 여섯 줄이다 — (1)의 「말없이 불린 다섯 자리」 + `give()` 의 `return 7;`**. 로그가 찍힌 자리와 **정확히 겹친다.**
- ★★★ **(5)도 에러다** — 로그로는 `calls 0` 이었다. **밟지 않은 가지도 컴파일 단계에서는 변환이 필요**하므로 막힌다.
- ★★ **진단이 자리마다 다른 말을 쓴다** — g++ 는 반환·인자에 `could not convert`, 복사 초기화에 `conversion ... to non-scalar type ... requested`, 삼항에 `operands to '?:' have different types` .\
  clang 은 `no viable conversion` · `no matching function` · `incompatible operand types` 다. **문구는 흔들리는 칸**이고 근거는 **줄 번호와 개수(6 · 6)다**.

### (2) ★★★ `explicit` 격자 — 한 낱말이 열다섯 칸 중 어디를 바꾸나

**언제 쓰나** — 「`explicit` 을 붙이면 **어디까지 불편해지나**」를 가늠할 때.

★★ **탐침마다 파일을 따로 컴파일한다** — 한 파일에 몰면 **첫 에러가 뒤를 가리지는 않지만**, 칸마다 `cc exit` 를 따로 받아야 격자가 선다.

```cpp
/* conv07.cpp */
// explicit 격자의 탐침 — -DPROBE=N 으로 한 줄씩 켠다. -DASK_EXPLICIT 이면 생성자에 explicit 을 붙인다
#include <vector>

#ifdef ASK_EXPLICIT
#define MAYBE_EXPLICIT explicit
#else
#define MAYBE_EXPLICIT
#endif

struct Meter { int v; MAYBE_EXPLICIT Meter(int x) : v(x) {} };
bool operator==(Meter a, Meter b) { return a.v == b.v; }
void take(Meter) {}

Meter ret_plain() {
#if PROBE == 3
    return 5;
#else
    return Meter(5);
#endif
}
Meter ret_brace() {
#if PROBE == 4
    return {5};
#else
    return Meter(5);
#endif
}

int main(int argc, char**) {
    Meter m(1);
    std::vector<Meter> vec;
    (void)m; (void)vec; (void)argc;
#if PROBE == 1
    Meter a = 5;
#elif PROBE == 2
    take(5);
#elif PROBE == 5
    take({5});
#elif PROBE == 6
    bool e = (m == 5); (void)e;
#elif PROBE == 7
    Meter t = argc > 1 ? m : 5; (void)t;
#elif PROBE == 8
    Meter a = {5};
#elif PROBE == 9
    Meter arr[] = {5, 6}; (void)arr;
#elif PROBE == 10
    vec.push_back(5);
#elif PROBE == 11
    Meter a(5);
#elif PROBE == 12
    Meter a{5};
#elif PROBE == 13
    Meter a = Meter(5);
#elif PROBE == 14
    Meter a = static_cast<Meter>(5);
#elif PROBE == 15
    vec.emplace_back(5);
#endif
#if PROBE == 1 || PROBE == 8 || PROBE == 11 || PROBE == 12 || PROBE == 13 || PROBE == 14
    (void)a;
#endif
    ret_plain(); ret_brace();
}
```

```bash
# conv-grid.sh
# conv-grid.sh — conv07.cpp 의 탐침 15개를 하나씩 켜고, explicit 유무 × 두 컴파일러로 컴파일되나를 찍는다
names=("" "Meter a = 5;" "take(5);" "return 5;" "return {5};" "take({5});" "m == 5" "c ? m : 5"
       "Meter a = {5};" "Meter arr[] = {5, 6};" "vec.push_back(5);" "Meter a(5);" "Meter a{5};"
       "Meter a = Meter(5);" "static_cast<Meter>(5)" "vec.emplace_back(5);")
ok() { "$@" >/dev/null 2>&1 && echo O || echo X; }
printf '%-3s %-24s %-8s %-8s %-8s %-8s\n' "#" "탐침" "g++" "g++ ex" "clang" "clang ex"
split=0; cc=0
for p in $(seq 1 15); do
  g0=$(ok g++ -std=c++20 -DPROBE=$p -c conv07.cpp -o /dev/null)
  g1=$(ok g++ -std=c++20 -DPROBE=$p -DASK_EXPLICIT -c conv07.cpp -o /dev/null)
  c0=$(ok clang++ -std=c++20 -DPROBE=$p -c conv07.cpp -o /dev/null)
  c1=$(ok clang++ -std=c++20 -DPROBE=$p -DASK_EXPLICIT -c conv07.cpp -o /dev/null)
  printf '%-3s %-24s %-8s %-8s %-8s %-8s\n' "$p" "${names[$p]}" "$g0" "$g1" "$c0" "$c1"
  [ "$g0" != "$g1" ] && split=$((split+1))
  [ "$g0$g1" != "$c0$c1" ] && cc=$((cc+1))
done
echo "explicit 로 갈린 칸 $split / 15 · 두 컴파일러가 갈린 칸 $cc / 15"
```

```text
===== bash conv-grid.sh (exit=0) =====
#   탐침                   g++      g++ ex   clang    clang ex
1   Meter a = 5;             O        X        O        X       
2   take(5);                 O        X        O        X       
3   return 5;                O        X        O        X       
4   return {5};              O        X        O        X       
5   take({5});               O        X        O        X       
6   m == 5                   O        X        O        X       
7   c ? m : 5                O        X        O        X       
8   Meter a = {5};           O        X        O        X       
9   Meter arr[] = {5, 6};    O        X        O        X       
10  vec.push_back(5);        O        X        O        X       
11  Meter a(5);              O        O        O        O       
12  Meter a{5};              O        O        O        O       
13  Meter a = Meter(5);      O        O        O        O       
14  static_cast<Meter>(5)    O        O        O        O       
15  vec.emplace_back(5);     O        O        O        O       
explicit 로 갈린 칸 10 / 15 · 두 컴파일러가 갈린 칸 0 / 15
```

- ★★★ **`explicit 로 갈린 칸 10 / 15`** — 스크립트가 센 것이다. **위 열 칸이 X 로 바뀌고 아래 다섯 칸은 그대로**다.
- ★★★ **갈리는 선은 「복사 초기화냐 직접 초기화냐」다.**\
  X 로 바뀐 열 칸은 전부 **복사 초기화**(`=` · 인자 전달 · `return` · `{…}` 를 `=` 나 인자로 넘기기 · 배열 원소 · `push_back`)이고,\
  남은 다섯 칸은 전부 **직접 초기화**(`Meter a(5)` · `Meter a{5}` · `Meter(5)` · `static_cast` · **`emplace_back`**)다.
- ★★★ **`push_back(5)` 는 X, `emplace_back(5)` 는 O** 다 — `push_back` 은 **`Meter` 를 인자로 받으니** 복사 초기화이고, `emplace_back` 은 **컨테이너 안에서 `Meter(5)` 로 직접 짓는다.**\
  ★ 그래서 **`emplace_back` 은 `explicit` 을 우회한다** — 「안전장치를 붙였는데 `emplace_back` 이 그냥 통과시킨다」는 뜻이기도 하다.
- ★★ **4번 `return {5};` 와 5번 `take({5})` 도 X** — 중괄호여도 **복사 리스트 초기화**다. [13번](../13-constructors-member-init-list-and-delegating/)의 「`Feet b = {5}` 는 막힌다」와 같은 규칙이다.
- ★ **`두 컴파일러가 갈린 칸 0 / 15`** — 이 규칙은 **표준 칸**이라 두 구현이 한 칸도 다르지 않다.

```text
                          explicit 없음     explicit
   복사 초기화 (10칸)       O               X   ★  =  · 인자 · return · {} 를 = / 인자로 · 배열 · push_back
   직접 초기화 (5칸)        O               O   ★  (5) · {5} · Meter(5) · static_cast · emplace_back

   ★ explicit 은 「이 생성자는 복사 초기화에서 후보가 아니다」라는 한 문장이다
```

★★ **타입 특성으로 같은 선을 한 줄에 본다.**

```cpp
/* conv08.cpp */
// explicit 은 타입 특성 두 개를 어떻게 가르나 — is_convertible 과 is_constructible
#include <cstdio>
#include <type_traits>

struct Imp  { Imp(int) {} };
struct Exp  { explicit Exp(int) {} };
struct BImp { operator bool() const { return true; } };
struct BExp { explicit operator bool() const { return true; } };

template <class From, class To>
void row(const char* name) {
    std::printf("%-16s is_convertible %d   is_constructible %d\n", name,
                (int)std::is_convertible_v<From, To>, (int)std::is_constructible_v<To, From>);
}

int main() {
    row<int, Imp>("int -> Imp");
    row<int, Exp>("int -> Exp");
    row<BImp, bool>("BImp -> bool");
    row<BExp, bool>("BExp -> bool");
    row<BExp, int>("BExp -> int");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic conv08.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
int -> Imp       is_convertible 1   is_constructible 1
int -> Exp       is_convertible 0   is_constructible 1
BImp -> bool     is_convertible 1   is_constructible 1
BExp -> bool     is_convertible 0   is_constructible 1
BExp -> int      is_convertible 0   is_constructible 0
===== clang++ -std=c++20 -Wall -Wextra -pedantic conv08.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
int -> Imp       is_convertible 1   is_constructible 1
int -> Exp       is_convertible 0   is_constructible 1
BImp -> bool     is_convertible 1   is_constructible 1
BExp -> bool     is_convertible 0   is_constructible 1
BExp -> int      is_convertible 0   is_constructible 0
```

- ★★★ **`explicit` 은 `is_convertible` 을 0 으로 만들고 `is_constructible` 은 1 로 둔다** — `int -> Exp` 가 **0 · 1** 이다.\
  ★ `is_convertible<From, To>` 는 「**`To t = from;` 이 되나**」(복사 초기화), `is_constructible<To, From>` 은 「**`To t(from);` 이 되나**」(직접 초기화)다. 격자의 선과 **같은 선**이다.
- ★★ **`explicit operator bool` 도 같다** — `BExp -> bool` 이 **0 · 1**. 그리고 **`BExp -> int` 는 0 · 0** — `int` 로는 **직접 초기화로도** 안 간다((5)).
- ★ 이 두 특성이 **(7)의 `explicit(bool)` 의 재료**다 — 「변환이 안전하면 암묵, 아니면 explicit」을 **타입 특성으로 적는다.**

### (3) ★★ 사용자 정의 변환은 한 번만 — `const char*` → `string` → `Name`

**언제 쓰나** — `std::string` 을 받는 생성자에 **문자열 리터럴**을 넘길 때.

```cpp
/* conv02.cpp */
// 생성자가 std::string 을 받는다 — 문자열 리터럴을 넘기면
#include <cstdio>
#include <string>
#include <utility>

struct Name {
    std::string s;
    Name(std::string x) : s(std::move(x)) {}
};
void greet(Name n) { std::printf("greet(%s)\n", n.s.c_str()); }

int main() {
    greet(std::string("kim"));   // 1. std::string 을 넘긴다
    greet("lee");                // 2. 리터럴을 넘긴다
    Name n = "park";             // 3. 리터럴로 복사 초기화
    Name m("choi");              // 4. 리터럴로 직접 초기화
    greet(m);
    (void)n;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 conv02.cpp -o ex (cc exit=1) =====
conv02.cpp: In function ‘int main()’:
conv02.cpp:14:11: error: could not convert ‘(const char*)"lee"’ from ‘const char*’ to ‘Name’
   14 |     greet("lee");                // 2. 리터럴을 넘긴다
      |           ^~~~~
      |           |
      |           const char*
conv02.cpp:15:14: error: conversion from ‘const char [5]’ to non-scalar type ‘Name’ requested
   15 |     Name n = "park";             // 3. 리터럴로 복사 초기화
      |              ^~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 conv02.cpp -o ex (cc exit=1) =====
conv02.cpp:14:5: error: no matching function for call to 'greet'
   14 |     greet("lee");                // 2. 리터럴을 넘긴다
      |     ^~~~~
conv02.cpp:10:6: note: candidate function not viable: no known conversion from 'const char[4]' to 'Name' for 1st argument
   10 | void greet(Name n) { std::printf("greet(%s)\n", n.s.c_str()); }
      |      ^     ~~~~~~
conv02.cpp:15:10: error: no viable conversion from 'const char[5]' to 'Name'
   15 |     Name n = "park";             // 3. 리터럴로 복사 초기화
      |          ^   ~~~~~~
conv02.cpp:6:8: note: candidate constructor (the implicit copy constructor) not viable: no known conversion from 'const char[5]' to 'const Name &' for 1st argument
    6 | struct Name {
      |        ^~~~
conv02.cpp:6:8: note: candidate constructor (the implicit move constructor) not viable: no known conversion from 'const char[5]' to 'Name &&' for 1st argument
    6 | struct Name {
      |        ^~~~
conv02.cpp:8:5: note: candidate constructor not viable: no known conversion from 'const char[5]' to 'std::string' (aka 'basic_string<char>') for 1st argument
    8 |     Name(std::string x) : s(std::move(x)) {}
      |     ^    ~~~~~~~~~~~~~
2 errors generated.
```

- ★★★ **2번과 3번만 에러다** — 리터럴은 `const char[4]` 다. `Name` 이 되려면 **`const char*` → `std::string`(사용자 정의 변환 1) → `Name`(사용자 정의 변환 2)** 두 번이 필요하다.
- ★★★ **암묵 변환 순서에 사용자 정의 변환은 0\~1 번뿐이다**(기준 소스 ③) — 둘째 칸이 **한 번**이라 막힌다.
- ★★ **1번(`std::string` 을 넘긴다)은 한 번**이라 되고, **4번(`Name m("choi")`)도 된다** — 직접 초기화는 **생성자의 인자를 초기화하는 것**이라 `const char*` → `string` **한 번**만 필요하다.
- ★ **clang 의 note 가 이유를 적는다** — `no known conversion from 'const char[5]' to 'std::string'`. 「`string` 으로는 갈 수 있는데 **거기서 한 번 더** 못 간다」가 아니라, **`Name` 을 찾는 자리에서 두 단계를 안 본다**는 뜻이다.

```text
   greet("lee")       const char[4] ─(배열→포인터: 표준)→ const char* ─(string(const char*): 사용자 1)→ string ─(Name(string): 사용자 2)→ Name
                                                                                                                  ★ 두 번째 사용자 정의 변환에서 멈춘다
   Name m("choi")     직접 초기화 — Name(std::string) 의 「인자」를 초기화한다 → const char* -> string 한 번   ★ 된다
```

### (4) ★★★ 종료 코드 0인데 의도와 다름 — 엉뚱한 오버로드가 불린다

**언제 쓰나** — 오버로드가 **둘 이상**인 함수에 **리터럴**을 넘길 때마다. **이 편의 두 번째 급소다.**

```cpp
/* conv05.cpp */
// 오버로드 두 벌 — 문자열 리터럴·정수를 넘기면 어느 쪽이 불리나
#include <cstdio>
#include <string>

struct Meter { int v; Meter(int x) : v(x) {} };

void show(const std::string& s) { std::printf("    show(const std::string&) \"%s\"\n", s.c_str()); }
void show(bool b)               { std::printf("    show(bool) %d\n", (int)b); }

void put(Meter m)  { std::printf("    put(Meter) %d\n", m.v); }
void put(double d) { std::printf("    put(double) %g\n", d); }

void len(Meter m) { std::printf("    len(Meter) %d\n", m.v); }

int main() {
    std::printf("(1) show(\"hello\")\n");            show("hello");
    std::printf("(2) show(std::string(\"hello\"))\n"); show(std::string("hello"));
    std::printf("(3) put(3)\n");                     put(3);
    std::printf("(4) len('A')\n");                   len('A');
    std::printf("(5) len(true)\n");                  len(true);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic conv05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) show("hello")
    show(bool) 1
(2) show(std::string("hello"))
    show(const std::string&) "hello"
(3) put(3)
    put(double) 3
(4) len('A')
    len(Meter) 65
(5) len(true)
    len(Meter) 1
```

- ★★★ **(1) `show("hello")` 가 `show(bool)` 로 갔다** — 출력이 `show(bool) 1` 이다. 문자열을 찍으려던 코드가 **`1` 을 찍었다.**\
  ★★★ **이유는 순위다** — `const char[6]` → `bool` 은 **표준 변환**(배열→포인터 → 불리언 변환)이고, `const char*` → `std::string` 은 **사용자 정의 변환**이다.\
  **오버로드 해결은 표준 변환 순서를 사용자 정의 변환 순서보다 앞에 둔다**([1번](../01-function-overloading-and-overload-resolution/)) — 그래서 `bool` 이 이긴다.
- ★★ **(3) `put(3)` 이 `put(double)`** — `int` → `double` 은 표준 변환, `int` → `Meter` 는 사용자 정의 변환이다. **같은 순위 규칙**이다.
- ★★ **(4) `len('A')` 가 `len(Meter) 65`** · **(5) `len(true)` 가 `len(Meter) 1`** — `char` → `int` → `Meter`, `bool` → `int` → `Meter`.\
  ★ **표준 변환 + 사용자 정의 변환 한 번**은 허락된다((3)의 순서 ①②). 「두 단계는 막힌다」는 **사용자 정의 변환이 두 번**일 때만이다.
- ★★★ **다섯 줄 전부 `cc exit=0 · run exit=0`** 이다 — 그리고 아래가 **경고를 누가 보나**다.

```text
===== echo "g++   -Wall -Wextra -pedantic               경고 $(g++ -std=c++20 -Wall -Wextra -pedantic -c conv05.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
g++   -Wall -Wextra -pedantic               경고 0
===== echo "g++   -Wall -Wextra -pedantic -Wconversion  경고 $(g++ -std=c++20 -Wall -Wextra -pedantic -Wconversion -c conv05.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
g++   -Wall -Wextra -pedantic -Wconversion  경고 0
===== echo "clang -Wall -Wextra -pedantic               경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic -c conv05.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
clang -Wall -Wextra -pedantic               경고 0
===== echo "clang -Wall -Wextra -pedantic -Wconversion  경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic -Wconversion -c conv05.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
clang -Wall -Wextra -pedantic -Wconversion  경고 1
===== echo "clang -Weverything 중 -Wstring-conversion   경고 $(clang++ -std=c++20 -Weverything -c conv05.cpp -o /dev/null 2>&1 | grep -c 'Wstring-conversion')" (exit=0) =====
clang -Weverything 중 -Wstring-conversion   경고 1
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -Wstring-conversion -c conv05.cpp -o /dev/null (cc exit=0) =====
conv05.cpp:16:59: warning: implicit conversion turns string literal into bool: 'const char[6]' to 'bool' [-Wstring-conversion]
   16 |     std::printf("(1) show(\"hello\")\n");            show("hello");
      |                                                      ~~~~ ^~~~~~~
1 warning generated.
```

- ★★★ **g++ 는 네 판 다 0건**(`-Wconversion` 을 켜도)이다. **clang 은 `-Wall -Wextra` 로 0건**, **`-Wconversion` 을 켜야 1건**(`-Wstring-conversion` 이 그 아래에 있다).
- ★★ **clang 이 본 것도 (1) 하나뿐**이다 — (3)(4)(5)는 **어느 플래그도 말하지 않는다.** 규칙대로 된 것이라 **컴파일러 입장에서는 경고할 일이 아니다.**
- ★ 두 컴파일러의 실행 출력은 **한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic conv05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) show("hello")
    show(bool) 1
(2) show(std::string("hello"))
    show(const std::string&) "hello"
(3) put(3)
    put(double) 3
(4) len('A')
    len(Meter) 65
(5) len(true)
    len(Meter) 1
```

```text
   오버로드 해결의 순위 (높은 쪽이 이긴다)

   정확히 일치  >  승격  >  표준 변환  >  ★ 사용자 정의 변환  >  ...
                            │                  │
     "hello" -> bool        ┘                  └  "hello" -> std::string
     3       -> double                            3       -> Meter

   ★ 변환 생성자를 가진 타입은 「오버로드 경쟁에서 늘 한 칸 아래」에 선다 — 표준 변환 후보가 하나라도 있으면 진다
```

### (5) ★★★ `explicit operator bool` — `if` 에서는 되고 `int n = h` 에서는 막힌다

**언제 쓰나** — 핸들·스마트 포인터·파서 결과처럼 「**유효한가**」를 `if (h)` 로 묻고 싶은 타입을 만들 때.

```cpp
/* conv03.cpp */
// operator bool 에 explicit 을 붙이면 어느 자리가 남나. -DASK_IMPLICIT 이면 explicit 을 뗀다
#include <cstdio>

#ifdef ASK_IMPLICIT
#define MAYBE_EXPLICIT
#else
#define MAYBE_EXPLICIT explicit
#endif

struct Handle {
    int fd;
    MAYBE_EXPLICIT operator bool() const { return fd >= 0; }
};

int main() {
    Handle h{3}, k{4};
    if (h) std::printf("1. if (h)\n");
    if (!h) {} else std::printf("2. !h\n");
    if (h && k) std::printf("3. h && k\n");
    std::printf("4. h ? 1 : 0    %d\n", h ? 1 : 0);
    bool b1(h);                          std::printf("5. bool b1(h)   %d\n", (int)b1);
    bool b2 = static_cast<bool>(h);      std::printf("6. static_cast  %d\n", (int)b2);
#ifndef ASK_CONTEXT_ONLY
    bool b3 = h;                         std::printf("7. bool b3 = h  %d\n", (int)b3);
    int  n  = h;                         std::printf("8. int n = h    %d\n", n);
    int  s  = h + k;                     std::printf("9. h + k        %d\n", s);
    std::printf("10. h == k       %d\n", (int)(h == k));
#endif
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 conv03.cpp -o ex (cc exit=1) =====
conv03.cpp: In function ‘int main()’:
conv03.cpp:24:15: error: cannot convert ‘Handle’ to ‘bool’ in initialization
   24 |     bool b3 = h;                         std::printf("7. bool b3 = h  %d\n", (int)b3);
      |               ^
      |               |
      |               Handle
conv03.cpp:25:15: error: cannot convert ‘Handle’ to ‘int’ in initialization
   25 |     int  n  = h;                         std::printf("8. int n = h    %d\n", n);
      |               ^
      |               |
      |               Handle
conv03.cpp:26:17: error: no match for ‘operator+’ (operand types are ‘Handle’ and ‘Handle’)
   26 |     int  s  = h + k;                     std::printf("9. h + k        %d\n", s);
      |               ~ ^ ~
      |               |   |
      |               |   Handle
      |               Handle
conv03.cpp:26:17: note: candidate: ‘operator+(int, int)’ (built-in)
   26 |     int  s  = h + k;                     std::printf("9. h + k        %d\n", s);
      |               ~~^~~
conv03.cpp:26:17: note:   no known conversion for argument 2 from ‘Handle’ to ‘int’
conv03.cpp:27:50: error: no match for ‘operator==’ (operand types are ‘Handle’ and ‘Handle’)
   27 |     std::printf("10. h == k       %d\n", (int)(h == k));
      |                                                ~ ^~ ~
      |                                                |    |
      |                                                |    Handle
      |                                                Handle
conv03.cpp:27:50: note: candidate: ‘operator==(int, int)’ (built-in)
   27 |     std::printf("10. h == k       %d\n", (int)(h == k));
      |                                                ~~^~~~
conv03.cpp:27:50: note:   no known conversion for argument 2 from ‘Handle’ to ‘int’
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 conv03.cpp -o ex 2>&1 | grep -E 'error:|generated' (cc exit=1) =====
conv03.cpp:24:10: error: no viable conversion from 'Handle' to 'bool'
conv03.cpp:25:10: error: no viable conversion from 'Handle' to 'int'
conv03.cpp:26:17: error: invalid operands to binary expression ('Handle' and 'Handle')
conv03.cpp:27:50: error: invalid operands to binary expression ('Handle' and 'Handle')
4 errors generated.
```

- ★★★ **1\~6번은 통과하고 7\~10번만 에러다** — 4 · 4.
- ★★★ **1\~4번이 되는 이유는 「문맥적 bool 변환」이다**(기준 소스 ④) — `if` 의 조건 · `!` · `&&` · `?:` 의 첫 피연산자는 **`bool t(h);` 가 성립하면** 변환한다.\
  `bool t(h);` 는 **직접 초기화**라 **`explicit` 변환 함수도 후보**가 된다((2)의 선과 같다).
- ★★ **5번 `bool b1(h)` 과 6번 `static_cast<bool>(h)` 도 직접 초기화**라 된다. **7번 `bool b3 = h;` 는 복사 초기화**라 막힌다 — **같은 `bool` 인데** 갈렸다.
- ★★★ **8\~10번이 `explicit` 이 막으려던 사고다** — 아래 판이 그것을 보인다.

★★★ **`-DASK_IMPLICIT` 로 `explicit` 을 떼면** — 열 줄이 전부 통과한다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DASK_IMPLICIT conv03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
1. if (h)
2. !h
3. h && k
4. h ? 1 : 0    1
5. bool b1(h)   1
6. static_cast  1
7. bool b3 = h  1
8. int n = h    1
9. h + k        2
10. h == k       1
```

- ★★★ **`9. h + k = 2`** — `fd` 3 과 4 인 핸들을 **더했더니 2** 가 나왔다. `bool` 로 바뀐 뒤 **정수로 승격**되어 `1 + 1` 이 됐다.
- ★★★ **`10. h == k = 1`** — **`fd` 가 다른 두 핸들이 「같다」.** 둘 다 `true` 로 바뀌어 비교됐다.
- ★★ **`8. int n = h = 1`** — `fd` 를 원했다면 **조용히 틀린 값**이다.
- ★★★ **전부 `cc exit=0 · run exit=0` 이고 경고 0건**이다. **이 편의 「종료 코드 0인데 의도와 다름」 두 번째 항목**이다.
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DASK_IMPLICIT conv03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
1. if (h)
2. !h
3. h && k
4. h ? 1 : 0    1
5. bool b1(h)   1
6. static_cast  1
7. bool b3 = h  1
8. int n = h    1
9. h + k        2
10. h == k       1
```

★ 그리고 **문맥적 자리만 남긴 판**(`-DASK_CONTEXT_ONLY`)은 두 컴파일러 다 통과한다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DASK_CONTEXT_ONLY conv03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
1. if (h)
2. !h
3. h && k
4. h ? 1 : 0    1
5. bool b1(h)   1
6. static_cast  1
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DASK_CONTEXT_ONLY conv03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
1. if (h)
2. !h
3. h && k
4. h ? 1 : 0    1
5. bool b1(h)   1
6. static_cast  1
```

```text
   explicit operator bool() const

   if (h) · !h · h && k · h ? a : b    문맥적 bool 변환 = bool t(h);  직접 초기화   ★ 된다
   bool b1(h) · static_cast<bool>(h)   직접 초기화                                    ★ 된다
   bool b3 = h                         복사 초기화                                    ✗
   int n = h · h + k · h == k          bool 로 간 뒤 int 로 — 암묵 변환이 필요       ✗   ★ 사고가 나던 자리

   ★ 「참이냐 거짓이냐」만 묻는 자리에 문을 열고, 「값으로 써라」는 자리는 닫는다
```

### (6) ★★ 괄호·중괄호에 `double` 을 넘기면 — 조용한 잘림과 좁히기

**언제 쓰나** — `int` 를 받는 생성자에 **실수**가 들어갈 수 있을 때.

★ **좁히기 규칙 자체는 [4번](../04-brace-initialization-narrowing-and-initializer-list/) (3)(4)가 정본**이다. 여기서는 **변환 생성자의 인자 자리**에서 같은 규칙이 어떻게 나오나만 본다.

```cpp
/* conv06.cpp */
// int 를 받는 생성자에 double 을 넘긴다 — 괄호·복사 초기화·중괄호
// -DASK_CONST 이면 중괄호에 상수를 넣은 줄을 켠다
#include <cstdio>

struct Meter { int v; Meter(int x) : v(x) {} };

int main() {
    double d = 3.5;
    Meter a(3.5);         // 1. 괄호 · 상수
    Meter b = 3.5;        // 2. 복사 초기화 · 상수
    Meter c{d};           // 3. 중괄호 · 변수
#ifdef ASK_CONST
    Meter e{3.5};         // 4. 중괄호 · 상수
    (void)e;
#endif
    std::printf("a.v=%d b.v=%d c.v=%d\n", a.v, b.v, c.v);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic conv06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
conv06.cpp: In function ‘int main()’:
conv06.cpp:11:13: warning: narrowing conversion of ‘d’ from ‘double’ to ‘int’ [-Wnarrowing]
   11 |     Meter c{d};           // 3. 중괄호 · 변수
      |             ^
a.v=3 b.v=3 c.v=3
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 conv06.cpp -o ex (cc exit=1) =====
conv06.cpp:9:13: warning: implicit conversion from 'double' to 'int' changes value from 3.5 to 3 [-Wliteral-conversion]
    9 |     Meter a(3.5);         // 1. 괄호 · 상수
      |           ~ ^~~
conv06.cpp:10:15: warning: implicit conversion from 'double' to 'int' changes value from 3.5 to 3 [-Wliteral-conversion]
   10 |     Meter b = 3.5;        // 2. 복사 초기화 · 상수
      |               ^~~
conv06.cpp:11:13: error: type 'double' cannot be narrowed to 'int' in initializer list [-Wc++11-narrowing]
   11 |     Meter c{d};           // 3. 중괄호 · 변수
      |             ^
conv06.cpp:11:13: note: insert an explicit cast to silence this issue
   11 |     Meter c{d};           // 3. 중괄호 · 변수
      |             ^
      |             static_cast<int>( )
2 warnings and 1 error generated.
```

- ★★★ **g++ 는 `cc exit=0` 이고 세 값이 전부 `3`** 이다 — `3.5` 가 **조용히 잘렸다.** 1·2번은 **경고도 없다**, 3번 `Meter c{d}` 만 `-Wnarrowing` **경고**다.
- ★★★ **clang 은 `cc exit=1`** — 3번을 **에러**로 막고, 1·2번에도 `-Wliteral-conversion` **경고**를 낸다.
- ★★ **괄호 `Meter a(3.5)` 는 좁히기 검사를 안 받는다** — 좁히기 금지는 **중괄호(목록 초기화)의 규칙**이다. 괄호로 쓰면 **`double` → `int` 가 그냥 된다.**

★★ **중괄호에 상수를 넣으면**(`-DASK_CONST`) — g++ 도 에러다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DASK_CONST -fmax-errors=0 conv06.cpp -o ex 2>&1 | grep -E 'error:|warning:' (cc exit=1) =====
conv06.cpp:11:13: warning: narrowing conversion of ‘d’ from ‘double’ to ‘int’ [-Wnarrowing]
conv06.cpp:13:16: error: narrowing conversion of ‘3.5e+0’ from ‘double’ to ‘int’ [-Wnarrowing]
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DASK_CONST -ferror-limit=0 conv06.cpp -o ex 2>&1 | grep -E 'error:|warning:|generated' (cc exit=1) =====
conv06.cpp:9:13: warning: implicit conversion from 'double' to 'int' changes value from 3.5 to 3 [-Wliteral-conversion]
conv06.cpp:10:15: warning: implicit conversion from 'double' to 'int' changes value from 3.5 to 3 [-Wliteral-conversion]
conv06.cpp:11:13: error: type 'double' cannot be narrowed to 'int' in initializer list [-Wc++11-narrowing]
conv06.cpp:13:13: error: type 'double' cannot be narrowed to 'int' in initializer list [-Wc++11-narrowing]
conv06.cpp:13:13: warning: implicit conversion from 'double' to 'int' changes value from 3.5 to 3 [-Wliteral-conversion]
3 warnings and 2 errors generated.
```

```text
===== echo "g++ -pedantic-errors conv06.cpp 에러 $(g++ -std=c++20 -Wall -Wextra -pedantic-errors -fmax-errors=0 -c conv06.cpp -o /dev/null 2>&1 | grep -c 'error:')" (exit=0) =====
g++ -pedantic-errors conv06.cpp 에러 1
```

- ★★ **g++ 가 상수 `3.5` 는 에러, 변수 `d` 는 경고**로 가른다 — [4번](../04-brace-initialization-narrowing-and-initializer-list/) (4)의 「**비상수 좁히기는 경고로 통과**」와 같은 모양이다. `-pedantic-errors` 면 **에러 1**이 된다.
- ★ **이 칸은 새 항목이 아니다** — 4번이 정본이다. 여기서 새로 본 것은 「**괄호로 받는 변환 생성자는 잘림을 경고 없이 통과시킨다(g++)**」 쪽이다.

### (7) ★ C++20 `explicit(bool)` — 조건에 따라 문을 연다

**언제 쓰나** — 래퍼 템플릿에서 「**안에 담은 타입이 암묵 변환되면 나도 암묵, 아니면 explicit**」을 적고 싶을 때(`std::pair`·`std::optional` 이 이렇게 한다).

```cpp
/* conv04.cpp */
// C++20 explicit(bool) — 인자 타입에 따라 explicit 을 켜고 끈다
#include <cstdio>
#include <type_traits>

struct Num {
    long v;
    template <class U>
    explicit(!std::is_integral_v<U>) Num(U u) : v(static_cast<long>(u)) {}
};

int main() {
    Num a = 5;                    // 1. int 로 복사 초기화
    Num b{2.5};                   // 2. double 로 직접 초기화
#ifdef ASK_COPY
    Num c = 2.5;                  // 3. double 로 복사 초기화
    (void)c;
#endif
    std::printf("a.v=%ld b.v=%ld\n", a.v, b.v);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic conv04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a.v=5 b.v=2
===== clang++ -std=c++20 -Wall -Wextra -pedantic conv04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a.v=5 b.v=2
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DASK_COPY -fmax-errors=0 conv04.cpp -o ex (cc exit=1) =====
conv04.cpp: In function ‘int main()’:
conv04.cpp:15:13: error: conversion from ‘double’ to non-scalar type ‘Num’ requested
   15 |     Num c = 2.5;                  // 3. double 로 복사 초기화
      |             ^~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DASK_COPY -ferror-limit=0 conv04.cpp -o ex (cc exit=1) =====
conv04.cpp:15:9: error: no viable conversion from 'double' to 'Num'
   15 |     Num c = 2.5;                  // 3. double 로 복사 초기화
      |         ^   ~~~
conv04.cpp:5:8: note: candidate constructor (the implicit copy constructor) not viable: no known conversion from 'double' to 'const Num &' for 1st argument
    5 | struct Num {
      |        ^~~
conv04.cpp:5:8: note: candidate constructor (the implicit move constructor) not viable: no known conversion from 'double' to 'Num &&' for 1st argument
    5 | struct Num {
      |        ^~~
conv04.cpp:8:38: note: explicit constructor is not a candidate (explicit specifier evaluates to true)
    8 |     explicit(!std::is_integral_v<U>) Num(U u) : v(static_cast<long>(u)) {}
      |              ~~~~~~~~~~~~~~~~~~~~~~  ^
1 error generated.
```

- ★★ **`Num a = 5;` 는 되고 `Num c = 2.5;` 는 막힌다** — 같은 생성자 템플릿인데 **`U` 에 따라 `explicit` 이 켜진다.** `Num b{2.5}` 는 직접 초기화라 된다(`b.v=2`).
- ★★ **clang 의 note 가 계산 결과를 말한다** — `explicit constructor is not a candidate (explicit specifier evaluates to true)`.

★★ **같은 파일을 `-std=c++17` 로 던지면** — 경고만 나고 **통과한다.**

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic conv04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
conv04.cpp:8:5: warning: ‘explicit(bool)’ only available with ‘-std=c++20’ or ‘-std=gnu++20’ [-Wc++20-extensions]
    8 |     explicit(!std::is_integral_v<U>) Num(U u) : v(static_cast<long>(u)) {}
      |     ^~~~~~~~
a.v=5 b.v=2
===== clang++ -std=c++17 -Wall -Wextra -pedantic conv04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
conv04.cpp:8:13: warning: explicit(bool) is a C++20 extension [-Wc++20-extensions]
    8 |     explicit(!std::is_integral_v<U>) Num(U u) : v(static_cast<long>(u)) {}
      |             ^
1 warning generated.
a.v=5 b.v=2
```

```text
===== echo "g++   -std=c++17 -pedantic-errors 에러 $(g++ -std=c++17 -Wall -Wextra -pedantic-errors -c conv04.cpp -o /dev/null 2>&1 | grep -c 'error:')" (exit=0) =====
g++   -std=c++17 -pedantic-errors 에러 1
===== echo "clang -std=c++17 -pedantic-errors 에러 $(clang++ -std=c++17 -Wall -Wextra -pedantic-errors -c conv04.cpp -o /dev/null 2>&1 | grep -c 'error:')" (exit=0) =====
clang -std=c++17 -pedantic-errors 에러 1
```

- ★★★ **두 컴파일러 다 `cc exit=0 · run exit=0`** 이고 값도 맞다. 그런데 **`explicit(bool)` 은 C++20 문법**이라 C++17 에서는 **ill-formed** 다 — 경고가 스스로 그렇게 말한다.
- ★★★ **`-pedantic` 으로는 경고, `-pedantic-errors` 라야 에러 1 · 1** — 앞 배치의 고정 항목([22번](../22-operator-overloading/) (8)의 `static operator()`)과 **같은 집안의 새 항목**이다.

## 문법 — 형태와 규칙

### 형태

```text
   struct T {
       T(int);                          변환 생성자 — int 에서 T 로 암묵 변환
       explicit T(double);              explicit 생성자 — 직접 초기화·캐스트에서만
       explicit operator bool() const;  explicit 변환 함수 — 문맥적 bool 변환에서만
       template <class U>
       explicit(!std::is_convertible_v<U, int>) T(U);   C++20 — 조건부 explicit
   };
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (1)(2)(5)(7)이 **컴파일한 소스**로 보였다.

### 규칙

- ★★★ **인자 하나로 부를 수 있는 생성자는 변환 생성자다** — 복사 초기화·인자·반환·연산자 인자·삼항에서 **말없이 불린다**((1)).
- ★★★ **`explicit` 은 「복사 초기화에서 후보가 아니다」** — 직접 초기화(`()`·`{}`·함수형 캐스트·`static_cast`·`emplace_back`)는 그대로 된다((2)).
- ★★ **사용자 정의 변환은 암묵 변환 순서에 한 번뿐** — `const char*` → `string` → `T` 는 막힌다((3)).
- ★★★ **변환 생성자는 오버로드 경쟁에서 표준 변환에 진다** — `show("hello")` 가 `show(bool)` 로 간다((4)).
- ★★★ **`explicit operator bool` 은 문맥적 bool 변환에서만 열린다** — `if`·`!`·`&&`·`||`·`?:` 첫 피연산자((5)).
- ★ **`explicit(bool)` 은 C++20** — C++17 모드에서는 **경고만 내고 통과**한다((7)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | 무엇이 되나 | 어디서 |
|---|---|---|
| `explicit Meter(int)` 에 `Meter a = 5;` · `take(6)` · `return 7;` · `m == 1` · `c ? m : 9` | ★★★ **에러 6 · 6** | (1) |
| `explicit` 에 `push_back(5)` · `take({5})` · `Meter arr[] = {5, 6}` | ★★ **X** — `emplace_back(5)` 는 O | (2) |
| `Name(std::string)` 에 `greet("lee")` · `Name n = "park"` | ★★ **에러 2 · 2** | (3) |
| `explicit operator bool` 에 `bool b = h` · `int n = h` · `h + k` · `h == k` | ★★★ **에러 4 · 4** | (5) |
| `Meter e{3.5}` (int 생성자) | ★ **에러**(g++ · clang) — `Meter c{d}` 는 g++ 만 경고 | (6) |
| `explicit(bool)` 에서 `Num c = 2.5` | ★ **에러 1 · 1** | (7) |

## 어디서 틀리나

### 1. ★★★ 「`explicit` 을 붙이면 그 타입으로 못 만든다」

(2)가 반증이다 — **직접 초기화 다섯 칸은 그대로**다. `explicit` 이 막는 것은 **「말없이」** 뿐이다.

### 2. ★★★ 「`emplace_back` 도 `push_back` 처럼 막히겠지」

(2)가 반증이다 — **`emplace_back(5)` 는 O**. 컨테이너 안에서 **직접 초기화**로 짓기 때문이다. `explicit` 을 붙였다고 **모든 자리가 안전해지지 않는다.**

### 3. ★★★ 「문자열을 넘겼으니 `string` 을 받는 쪽이 불리겠지」

(4)가 반증이다 — **`show(bool)` 이 이겼다.** 사용자 정의 변환은 **표준 변환보다 순위가 낮다.** 그리고 **g++ 는 어느 플래그로도 경고하지 않았다.**

### 4. ★★ 「`if (h)` 가 되니 `bool b = h` 도 되겠지」

(5)가 반증이다 — 앞은 **문맥적 변환**(직접 초기화), 뒤는 **복사 초기화**다. **`bool b(h)` 는 된다.**

### 5. ★★ 「삼항에서 안 밟은 가지는 상관없다」

(1)이 반쯤 반증이다 — **실행에서는 `calls 0`** 이지만, **`explicit` 판은 컴파일 에러**다. 타입은 **두 가지를 다 보고** 정해진다.

### 6. ★★ 「변환은 한 번만 된다 — 그러니 `char` 는 `Meter` 로 못 간다」

(4)가 반증이다 — **`len('A')` 가 `len(Meter) 65`**. 「한 번」은 **사용자 정의 변환**의 횟수다. **표준 변환은 앞뒤로 붙는다.**

### 7. ★ 「`-std=c++17` 로 빌드했으니 C++17 코드다」

(7)이 반증이다 — **`explicit(bool)` 이 경고만 내고 통과한다.** `-pedantic-errors` 라야 막힌다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 거의 전부다** — 변환은 **초기화 규칙과 오버로드 해결**의 문제이고, 격자의 `두 컴파일러가 갈린 칸 0 / 15` 가 그것을 보인다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **`explicit` 은 복사 초기화에서 후보가 아니다**((2)) · **사용자 정의 변환은 한 번**((3)) · **표준 변환 순서가 사용자 정의 변환 순서를 이긴다**((4)) · **문맥적 bool 변환은 `bool t(e);` 로 판단**((5)) | 격자 · 진단 전문 · 호출 로그 | ★★★ 「**이 줄에서 생성자가 돈다**」 — 코드에 `Meter` 라는 글자가 없다((1)) |
| **조건부 표준** | 특정 판에서만 | ★★ **`explicit(bool)` 은 C++20**((7)) · **`explicit` 변환 함수는 C++11** | `-std=c++17`/`c++20` 두 판 | ★★ **C++17 모드에서 경고만 내고 통과**((7)) |
| **구현 정의** | 문서화 의무 | ★ **진단 문구** · **좁히기 진단을 에러로 하나 경고로 하나**(g++ 비상수 = 경고)((6)) | 두 컴파일러 대조 | ★ **g++ 는 `Meter a(3.5)` 에 경고 0**((6)) |
| **미명시** | 몇 가지 중 하나 | ★ **이 주제에는 없다** — 변환이 몇 번 도는지는 규칙이 정한다(복사 생략은 [16번](../16-copy-constructor-and-copy-assignment/) (2)) | — | — |
| **UB** | 아무 일이나 | ★ **이 주제에는 없다** — 암묵 변환의 사고는 **UB 가 아니라 「규칙대로 틀린 값」이다**((4)(5)) | — | ★★★ **그래서 sanitizer 도 못 본다** — 부적용인 창 ③ 과 같은 이유 |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | 호출 로그 |
|---|---|---|---|---|
| ★★★ **`show("hello")` 가 `show(bool)`** | 표준 | ★★★ **0건**(`-Wconversion` 도 0) | ★ **0건** · `-Wconversion` 이면 **1** | ★★★ **`show(bool) 1`** |
| ★★ **`put(3)` 이 `put(double)`** | 표준 | **0건** | **0건** | **`put(double) 3`** |
| ★★★ **암묵 `operator bool` 로 `h == k` 가 1** | 표준 | ★★★ **0건** | ★★★ **0건** | **`10. h == k 1`** |
| ★★ **`Meter a(3.5)` 가 3** | 표준 | ★ **0건** | ★ **warning 1** | `a.v=3` |
| ★ **`explicit(bool)` 을 C++17 로** | 조건부 | **warning 1** · `cc exit=0` | **warning 1** · `cc exit=0` | 값 정상 |

- ★★ **이 표의 결론** — ★★★ **암묵 변환의 사고는 「규칙대로 된 것」이라 컴파일러가 말할 이유가 없다.** 로그로만 보인다. **그래서 막는 도구는 경고가 아니라 `explicit` 이다.**

### ★ 종료 코드 0인데 ill-formed — 새 항목 하나

- ★★ **`explicit(bool)` 을 `-std=c++17` 로** — 두 컴파일러 다 `cc exit=0` · 경고 1 · `-pedantic-errors` 로 **에러 1 · 1**((7)).
- ★ 비상수 좁히기 `Meter c{d}` 의 g++ 판은 **[4번](../04-brace-initialization-narrowing-and-initializer-list/) (4)가 이미 센 항목**이라 새로 세지 않는다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 인자 하나짜리 생성자 — **값의 뜻이 바뀐다**(`int` → `Meter` · `size_t` → 버퍼 크기) | ★★★ **`explicit`** | (1)의 다섯 자리를 막는다 |
| 인자 하나짜리 생성자 — **같은 값의 다른 표현**(`const char*` → `string` · `int` → `BigInt`) | ★★ **암묵**(그대로) | 대칭 연산이 필요하다([22번](../22-operator-overloading/) (1)) |
| 「유효한가」를 묻는 타입 | ★★★ **`explicit operator bool`** | `if (h)` 는 되고 `h + k` 는 막힌다((5)) |
| 래퍼 템플릿 | ★ **`explicit(bool)`**(C++20) | 담은 타입의 변환 가능성을 물려준다((7)) |
| 오버로드가 여럿인 함수에 리터럴을 넘긴다 | ★★ **타입을 명시**(`std::string("…")`) · 또는 `bool` 오버로드를 없앤다 | (4) — 경고가 안 난다 |

★★ **기본값은 `explicit`** 이다 — 「**암묵 변환이 필요하다는 이유를 댈 수 있을 때만 뗀다**」가 이 편의 판단 규칙이다.

## 핵심 문장

- ★★★ **인자 하나짜리 생성자는 복사 초기화·인자·반환·연산자·삼항에서 말없이 불린다** — 코드에 타입 이름이 안 보인다.
- ★★★ **`explicit` 은 「복사 초기화에서 후보가 아니다」** — 격자 15칸 중 10칸이 X 로 바뀌고 **직접 초기화 5칸(`emplace_back` 포함)은 그대로**다.
- ★★★ **변환 생성자는 오버로드 경쟁에서 표준 변환에 진다** — `show("hello")` 가 `show(bool)` 로 가고 **g++ 는 어느 플래그로도 경고하지 않았다.**
- ★★ **`explicit operator bool` 은 문맥적 bool 변환(= `bool t(e);`)에서만 열린다** — 떼면 **`fd` 가 다른 두 핸들이 `==` 로 1** 이 된다.
- ★★ **사용자 정의 변환은 한 번뿐** — `greet("lee")` 는 막히고 `Name m("choi")` 는 된다.
- ★ **`explicit(bool)` 은 C++20** — C++17 모드에서 경고만 내고 통과한다.

## 관련 자료

- [22번](../22-operator-overloading/) — ★★★ **대칭 변환.** (1)의 「`1 + a` 는 비멤버 × 암묵 변환일 때만」을 **여기서는 「그 암묵 변환이 만드는 사고」 쪽에서** 본다.
- [13번](../13-constructors-member-init-list-and-delegating/) — **생성자 문법.** `explicit` 생성자의 기본 금지 사례와 `Feet c{5}`/`Feet b = {5}` 가 거기다.
- [4번](../04-brace-initialization-narrowing-and-initializer-list/) — **중괄호와 좁히기.** (6)의 판정은 거기 (3)(4)가 정본이다.
- [1번](../01-function-overloading-and-overload-resolution/) — **오버로드 해결의 순위.** (4)의 「표준 변환 > 사용자 정의 변환」이 거기서 온다.
- [18번](../18-rule-of-zero-three-five-default-delete/) — **`<type_traits>` 격자의 형식.** (2)의 `is_convertible`/`is_constructible` 이 그 형식을 따른다.
- [16번](../16-copy-constructor-and-copy-assignment/) — **복사 생략.** (1)의 `give()` 가 생성자 **한 번**인 이유(반환 prvalue 의 의무 생략)가 거기 (2)다.

## 용어 풀이

> **변환 생성자(converting constructor)** — `explicit` 이 아닌, 인자 하나로 부를 수 있는 생성자. 그 타입으로 가는 **암묵 변환**이 된다.\
> 예: (1)의 `Meter(int)` — 다섯 자리에서 `calls 1`.

> **복사 초기화(copy-initialization)** — `T t = e;` · 인자 전달 · `return e;` · `T t = {e};` 처럼 **`=` 모양으로 짓는 것**. `explicit` 생성자는 여기서 후보가 아니다.\
> 예: (2)의 격자 위 열 칸.

> **직접 초기화(direct-initialization)** — `T t(e);` · `T t{e};` · `T(e)` · `static_cast<T>(e)` 처럼 **생성자를 명시해 부르는 것**.\
> 예: (2)의 아래 다섯 칸, `emplace_back`.

> **사용자 정의 변환(user-defined conversion)** — 변환 생성자나 변환 함수(`operator T()`)로 하는 변환. 한 암묵 변환 순서에 **한 번만** 들어간다.\
> 예: (3)의 `greet("lee")` 가 막힌 이유.

> **문맥적 bool 변환(contextual conversion to bool)** — `if`·`!`·`&&`·`||`·`?:` 첫 피연산자 등에서 **`bool t(e);` 가 성립하면** 하는 변환. `explicit operator bool` 이 여기서만 쓰인다.\
> 예: (5)의 1\~4번.

> **`explicit(bool)`** — C++20. 괄호 안 상수식이 `true` 일 때만 explicit 이 되는 조건부 지정자.\
> 예: (7)의 `explicit(!std::is_integral_v<U>)`.

## 더 들어가면

- **변환 함수 `operator T()` 의 일반형** — `operator bool` 말고도 `operator int()` 등을 둘 수 있다. **변환 생성자와 변환 함수가 둘 다 있으면 모호**해진다 — 이 문서는 **던지지 않았다.**
- **safe bool 관용구** — C++11 이전에는 `explicit operator bool` 이 없어 **멤버 포인터로 변환**하는 우회가 쓰였다. 지금은 필요 없다.
- **CTAD 의 `explicit` 추론 가이드**(C++17) — 기준 소스 ①이 적는 세 번째 자리다. 템플릿 인자 추론 주제에서 다룬다.
- **`std::pair`·`std::optional` 의 조건부 `explicit`** — (7)의 모양을 표준 라이브러리가 쓴다. 이 문서는 그 소스를 읽지 않았다.
