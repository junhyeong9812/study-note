# cpp/syntax/18 — 0/3/5의 법칙 · `=default`/`=delete` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 특수 멤버 함수 규칙](https://en.cppreference.com/w/cpp/language/rule_of_three) · [cppreference — `= default`](https://en.cppreference.com/w/cpp/language/function#Deleted_functions) · [cppreference — `<type_traits>`](https://en.cppreference.com/w/cpp/header/type_traits) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html) · [AddressSanitizer](https://github.com/google/sanitizers/wiki/AddressSanitizer)
> **실행 검증** — 이 문서의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`rule01.cpp` \~ `rule09.cpp`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 배너도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
> **버전** — 3의 법칙은 **C++98부터**. **`= default`·`= delete`·이동 연산·5의 법칙은 C++11부터**,\
> **0의 법칙은 C++11 의 스마트 포인터와 함께** 실용이 됐다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.
> ★★★ **16 → 17 → 18 은 한 사슬이고 이 편이 결론이다.** [16번](../16-copy-constructor-and-copy-assignment/)이 「복사가 무엇을 부르나」를,\
> [17번](../17-move-constructor-assignment-and-moved-from-state/)이 「이동이 무엇을 훔치나」를 수로 고정했다.\
> **여기 18 은 「그래서 다섯 중 무엇을 적을 것인가」에 답한다** — 그리고 답은 대개 「**하나도 안 적는다**」다.
> **경계** — 「복사의 구현」은 [16번](../16-copy-constructor-and-copy-assignment/), 「이동의 구현」은 [17번](../17-move-constructor-assignment-and-moved-from-state/)이 정본이다.\
> 「RAII 래퍼를 만드는 법」은 [15번](../15-raii-resources-as-types/), 「`unique_ptr` 의 API」는 목록의 **26번**,\
> 「예외 안전 보장 4단계」는 **52번**, 「`noexcept` 의 전모」는 **53번 주제**가 정본이다.\
> ★ 여기서는 「**무엇이 자동 생성되고 무엇이 조용히 사라지나**」만 본다.
> **대비** — Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **9번**([`09-copy-clone-and-drop/`](../../../rust/syntax/09-copy-clone-and-drop/)) — 러스트는 **`derive(Clone)` 을 적어야 복사가 생기고**,\
> `Drop` 을 구현하면 **그 타입을 통째로 옮기는 것만** 남는다. 기본값이 「**아무것도 안 준다**」다.\
> C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **37번 주제**(`IDisposable`/`using`) — GC 가 있는 언어의 「소멸자 자리」다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 리포트의 **PID**·주소 · 두 컴파일러의 **진단 문구** | ★★★ **`<type_traits>` 격자의 0/1** — 이 주제의 답 자체다 |
> | 객체의 주소값 · 실행 시간 | ★★★ **어느 특수 멤버가 불렸나**(계수 로그) · **`new`/`delete` 횟수** |
> | — | ★★ **`cc exit`/`run exit`** · **경고 개수** · **에러 개수** · **`sizeof`** |
> | — | ★ **진단의 `(행,열)`** · **ASan 이 샌 바이트 수와 할당 수** |

## 한눈에 — 쉽게 말하면

**특수 멤버 다섯은 「집에 딸려 오는 기본 옵션」이다.** 하나를 직접 고르면 **몇 개가 조용히 빠진다.**

새 아파트를 계약하면 싱크대·붙박이장·에어컨이 **기본으로 딸려 온다.**\
그런데 「에어컨은 제가 직접 달게요」라고 말하는 순간, 시공사는 「**이 사람은 자기 취향이 있구나**」라고 판단하고\
**같은 계열의 다른 옵션도 빼 버린다.** 그러면 나중에 「어? 붙박이장이 왜 없지?」가 된다.

C++ 이 정확히 그렇다. **소멸자 한 줄을 적으면 이동 두 개가 조용히 사라진다.**\
그래서 규칙이 셋이다 — **다섯을 하나도 안 적거나(0), 셋을 다 적거나(3), 다섯을 다 적거나(5).**

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 기본 옵션이 딸려 온다 | ★★★ **컴파일러가 특수 멤버를 자동 생성한다** | (1) |
| ★★★ **하나를 직접 고르면 다른 것이 빠진다** | ★★★ **소멸자를 쓰면 이동이 사라진다** | (2) |
| 「기본 옵션 그대로 주세요」라고 **말한다** | ★★ **`= default`** | (3) |
| 「이 옵션은 아예 빼 주세요」 | ★★ **`= delete`** | (4) |
| 옵션을 **하나도 안 고른다** | ★★★ **0의 법칙** | (5) |
| 직접 다는 것이 **하나라도 있으면 전부 직접** | ★★ **3의 법칙 · 5의 법칙** | (5) |

> **특수 멤버 함수(special member function)** — 컴파일러가 필요하면 스스로 만들어 주는 여섯.\
> 기본 생성자 · 소멸자 · 복사 생성자 · 복사 대입 · 이동 생성자 · 이동 대입.

> **0의 법칙(rule of zero)** — **자원을 직접 들지 않으면 다섯을 하나도 안 쓴다.**\
> 예: (5)의 `Zero` 는 한 줄도 안 썼는데 `Five` 와 같은 성질을 얻었다.

```text
   내가 적은 것                      컴파일러가 만들어 주는 것

   아무것도 안 적음          기본 · 소멸 · 복사생 · 복사대 · 이동생 · 이동대   (여섯 다)
                                                            
   소멸자 한 줄              기본 · (내 것) · 복사생 · 복사대 · ✗ · ✗
                                                            ^^^^^^^
                                       ★ 이동 둘이 사라진다 — 에러도 경고도 없이

   복사 생성자 하나          ✗ · 소멸 · (내 것) · 복사대(deprecated) · ✗ · ✗
                             ^                                        ^^^^^^^
                    기본 생성자도 사라진다                  이동 둘도 사라진다

   이동 생성자 하나          ✗ · 소멸 · ✗(delete) · ✗(delete) · (내 것) · ✗
                                        ^^^^^^^^^^^^^^^^^^^^
                                        ★ 복사가 「지워진다」 — 그냥 없는 것과 다르다
```

- ★★★ **이 그림이 (1)의 격자 그대로**다. 격자가 **이 주제의 본체**다.

## 이 주제가 답하려는 질문

1. **무엇을 적으면 무엇이 자동 생성되나** — **격자로 전수 확인**할 수 있나((1)).
2. **「사라진다」를 무엇으로 보이나** — 격자로 안 보이는 자리가 있나((2)).
3. **`= default` 는 본문 `{}` 와 무엇이 다른가**((3)).
4. **`= delete` 는 「없는 것」과 무엇이 다른가**((4)).
5. **그래서 무엇을 적을 것인가** — **0 이 왜 기본값인가**((5)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ⑥이다

★★★ **이 주제의 본체는 앞 두 편과 다르다** — **`<type_traits>` 격자**다.\
「자동 생성됐나」는 **호출 로그로는 안 보인다.** 안 만들어진 것은 **불리지도 않기 때문**이다.

```text
① 호출 계수 로그        (2)의 「이동이 복사로 바뀐다」를 실제로 보인다        (2)(5)
② 두 컴파일러 대조      격자 · 진단 · 경고 개수                              (1)(3)(4)(6)(7)
③ ASan 리포트           탐침이 실제로 새는지                                 (6)
④ `-O2` 어셈블리        ★ 부적용 — 17번이 정본이다                           —
⑤ 경고 격자             탐침 여섯 중 몇이 답하나                             (6)
⑥ ★★★ <type_traits> 격자  무엇이 자동 생성됐나를 0/1 로 전수                 (1)(2)(3)(5)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ★★★ **⑥ `<type_traits>` 격자** | ★★★ **본체** — `is_copy_constructible`·`is_move_assignable`·`is_trivially_*` 를 타입마다 찍는다 | **쓴다** |
| ① 호출 계수 로그 | ★★★ **격자가 못 보는 자리를 메운다**((2)) | **쓴다** |
| ② 두 컴파일러 대조 | 격자의 0/1 · `= delete` 의 진단 전문 | **쓴다** |
| ③ ASan 리포트 | 탐침 여섯이 **8바이트를 샜다** | **쓴다** |
| ④ `-O2` 어셈블리 세기 | ★ **부적용** — 이 편의 질문은 **무엇이 생성됐나**이지 코드 크기가 아니다 | **안 쓴다** |
| ⑤ 경고 격자 | 탐침 여섯 중 **둘**이 답했다 | **쓴다** |

- ★★★ **「제5의 상태」가 (2)에 있다** — **격자가 답을 못 주는 칸**이 있다.\
  `is_move_constructible` 은 `Zero` 와 `Dtor` 에 **둘 다 `1`** 을 준다. **갈리지 않는다.**\
  ★ 「이동이 사라졌다」는 그 트레이트로는 안 보이고 **`is_nothrow_move_constructible`** 과 **호출 로그**로만 보인다.\
  ★★ **같은 질문을 다른 창으로 바꿔 물은 것**이지 안 물어본 것이 아니다.
- ★★ **④를 「안 쟀다」가 아니라 「잴 것이 없다」로 적는다.** 이 편의 질문은 **선언의 유무**이고,\
  그것은 **어셈블리가 아니라 트레이트가 답한다.**

### (1) ★★★ 무엇이 자동 생성됐나 — 격자로 전수

**언제 쓰나** — 「이 타입을 `vector` 에 넣을 수 있나?」·「복사가 되나?」가 궁금할 때마다.\
**이 절이 이 주제의 중심이다.**

```cpp
/* rule01.cpp */
// 컴파일러가 무엇을 자동 생성했나 — 특수 멤버 다섯을 격자로 찍는다
#include <cstdio>
#include <memory>
#include <string>
#include <type_traits>
#include <vector>

struct S0 { int x; };                                     // 아무것도 안 썼다
struct S1 { int x; ~S1() {} };                            // 소멸자만 썼다
struct S2 { int x; S2(const S2&) = default; };            // 복사 생성자만 선언했다
struct S3 { int x; S3(S3&&) = default; };                 // 이동 생성자만 선언했다
struct S4 { int x;                                        // 다섯을 전부 = default
            S4() = default; ~S4() = default;
            S4(const S4&) = default; S4& operator=(const S4&) = default;
            S4(S4&&) = default;      S4& operator=(S4&&) = default; };
struct S5 { int x; S5(const S5&) = delete; };             // 복사 생성자를 지웠다
struct S6 { std::unique_ptr<int> p; std::vector<int> v; };// 0의 법칙 — 자원을 남에게 맡겼다
struct S7 { std::string s; };                             // 무거운 멤버 하나, 아무것도 안 썼다
struct S8 { std::string s; ~S8() {} };                     // 같은 멤버 + 소멸자 한 줄

template <class T> void row(const char* name) {
    std::printf("%-3s |  %d   %d   %d   %d   %d  |   %d\n", name,
        (int)std::is_default_constructible_v<T>,
        (int)std::is_copy_constructible_v<T>,
        (int)std::is_copy_assignable_v<T>,
        (int)std::is_move_constructible_v<T>,
        (int)std::is_move_assignable_v<T>,
        (int)std::is_nothrow_move_constructible_v<T>);
}

int main() {
    std::printf("타입 | 기본 복사생 복사대 이동생 이동대 | 이동이 noexcept 인가\n");
    row<S0>("S0"); row<S1>("S1"); row<S2>("S2"); row<S3>("S3");
    row<S4>("S4"); row<S5>("S5"); row<S6>("S6"); row<S7>("S7"); row<S8>("S8");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic rule01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
타입 | 기본 복사생 복사대 이동생 이동대 | 이동이 noexcept 인가
S0  |  1   1   1   1   1  |   1
S1  |  1   1   1   1   1  |   1
S2  |  0   1   1   1   1  |   1
S3  |  0   0   0   1   0  |   1
S4  |  1   1   1   1   1  |   1
S5  |  0   0   1   0   1  |   0
S6  |  1   0   0   1   1  |   1
S7  |  1   1   1   1   1  |   1
S8  |  1   1   1   1   1  |   0
```

```text
   격자를 읽는 순서

   ① 기본 생성 칸이 0 인가   -> 복사·이동 중 무엇인가를 「선언」했다
   ② 복사 두 칸이 0 인가     -> 이동을 선언했다 (지워진 것이다)
   ③ 이동 두 칸이 0 인가     -> 이동을 「지웠거나」 복사 전용 멤버가 있다
   ④ noexcept 칸만 0 인가    -> ★ 소멸자를 선언했다 (이동이 사라졌다 — (2))

   ★ ④가 이 편에서 가장 안 보이는 칸이다. 앞 다섯 칸은 아무 말도 안 한다.
```

| 타입 | 적은 것 | 읽는 법 |
|---|---|---|
| `S0` | 아무것도 | **여섯 다 생긴다** — 기준선 |
| `S1` | 소멸자만 | ★★★ **격자로는 `S0` 와 똑같아 보인다** — 마지막 칸(`noexcept`)도 `1` 이다 |
| `S2` | 복사 생성자만 | ★★ **기본 생성자가 사라진다**(첫 칸 `0`) |
| `S3` | 이동 생성자만 | ★★★ **복사가 지워진다**(둘째·셋째 칸 `0`) · 이동 대입도 `0` |
| `S4` | 여섯을 `= default` | **`S0` 와 같다** — 명시해도 손해가 없다 |
| `S5` | 복사 생성자 `= delete` | ★★ **복사 생성 `0` · 복사 대입 `1`** — 한쪽만 지워졌다 |
| `S6` | `unique_ptr`+`vector` 멤버 | ★★★ **복사 `0` · 이동 `1`** — 0의 법칙이 얻는 것 |
| `S7` | `string` 멤버, 아무것도 안 씀 | **전부 `1`** |
| `S8` | 같은 멤버 + 소멸자 한 줄 | ★★★ **마지막 칸만 `1` 에서 `0`** 으로 떨어진다 |

- ★★★ **`S7` 과 `S8` 의 차이가 이 주제의 핵심이다.** 소스 차이는 **`~S8() {}` 한 줄**뿐인데\
  **`is_nothrow_move_constructible` 이 `1` 에서 `0`** 으로 떨어진다.
- ★★★ **그런데 앞의 다섯 칸은 안 갈린다.** `is_move_constructible` 은 **둘 다 `1`** 이다.\
  ★ **이동이 사라졌는데 트레이트가 `1` 이라고 답하는 이유**는 (2)에서 본다.
- ★★ **`S3` 이 가장 극적이다** — 이동 생성자 하나를 선언했더니 **복사 둘이 `0`** 이 됐다.\
  ★ 「안 만들어진다」가 아니라 「**`= delete` 된다**」다((4)에서 그 차이를 본다).
- ★★ **`S5` 의 비대칭** — 복사 생성자만 지웠는데 **복사 대입은 살아 있다**(`1`).\
  ★ 「복사를 막았다」고 생각하기 쉬운 자리다. [16번](../16-copy-constructor-and-copy-assignment/)의 금지 사례가 같은 비대칭을 보였다.
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic rule01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
타입 | 기본 복사생 복사대 이동생 이동대 | 이동이 noexcept 인가
S0  |  1   1   1   1   1  |   1
S1  |  1   1   1   1   1  |   1
S2  |  0   1   1   1   1  |   1
S3  |  0   0   0   1   0  |   1
S4  |  1   1   1   1   1  |   1
S5  |  0   0   1   0   1  |   0
S6  |  1   0   0   1   1  |   1
S7  |  1   1   1   1   1  |   1
S8  |  1   1   1   1   1  |   0
```

### (2) ★★★ 소멸자 한 줄을 더하면 이동이 조용히 사라진다

**언제 쓰나** — 「법칙」이 **왜 법칙인지**를 볼 때. **(1)의 짝이다.**

★★★ **격자만으로는 이 자리를 못 잡는다.** 호출 로그를 같이 봐야 한다.

```cpp
/* rule02.cpp */
// 소멸자 한 줄을 더하면 이동이 조용히 사라진다 — 격자가 아니라 계수 로그가 답한다
#include <cstdio>
#include <type_traits>
#include <utility>
#include <vector>

struct Tr {                                      // 멤버 — 무엇이 불렸는지 말한다
    Tr() {}
    Tr(const Tr&)          { std::printf("      멤버: 복사\n"); }
    Tr(Tr&&)      noexcept { std::printf("      멤버: 이동\n"); }
    Tr& operator=(const Tr&)          { std::printf("      멤버: 복사 대입\n"); return *this; }
    Tr& operator=(Tr&&)      noexcept { std::printf("      멤버: 이동 대입\n"); return *this; }
    ~Tr() {}
};

struct Zero { Tr t; };                           // 0의 법칙 — 다섯을 하나도 안 썼다
struct Dtor { Tr t; ~Dtor() {} };                // 소멸자 한 줄만 더했다

int main() {
    std::printf("(1) Zero — 아무것도 안 쓴 타입\n");
    { Zero a; Zero b = std::move(a); Zero c; c = std::move(b); }
    std::printf("(2) Dtor — 소멸자 한 줄만 더한 타입\n");
    { Dtor a; Dtor b = std::move(a); Dtor c; c = std::move(b); }

    std::printf("(3) 격자는 무엇이라고 답하나\n");
    std::printf("    is_move_constructible          Zero=%d  Dtor=%d   ← 둘 다 1이라 안 갈린다\n",
                (int)std::is_move_constructible_v<Zero>, (int)std::is_move_constructible_v<Dtor>);
    std::printf("    is_nothrow_move_constructible  Zero=%d  Dtor=%d   ← 여기서 갈린다\n",
                (int)std::is_nothrow_move_constructible_v<Zero>,
                (int)std::is_nothrow_move_constructible_v<Dtor>);

    std::printf("(4) 그래서 vector 재할당이 갈린다\n");
    {
        std::printf("    [Zero] ");  std::printf("자리 둘을 잡고 둘을 넣은 뒤 셋째를 넣는다\n");
        std::vector<Zero> v; v.reserve(2); v.emplace_back(); v.emplace_back(); v.emplace_back();
    }
    {
        std::printf("    [Dtor] ");  std::printf("자리 둘을 잡고 둘을 넣은 뒤 셋째를 넣는다\n");
        std::vector<Dtor> v; v.reserve(2); v.emplace_back(); v.emplace_back(); v.emplace_back();
    }
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic rule02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) Zero — 아무것도 안 쓴 타입
      멤버: 이동
      멤버: 이동 대입
(2) Dtor — 소멸자 한 줄만 더한 타입
      멤버: 복사
      멤버: 복사 대입
(3) 격자는 무엇이라고 답하나
    is_move_constructible          Zero=1  Dtor=1   ← 둘 다 1이라 안 갈린다
    is_nothrow_move_constructible  Zero=1  Dtor=0   ← 여기서 갈린다
(4) 그래서 vector 재할당이 갈린다
    [Zero] 자리 둘을 잡고 둘을 넣은 뒤 셋째를 넣는다
      멤버: 이동
      멤버: 이동
    [Dtor] 자리 둘을 잡고 둘을 넣은 뒤 셋째를 넣는다
      멤버: 복사
      멤버: 복사
```

```text
   Zero { Tr t; }              Dtor { Tr t; ~Dtor() {} }
   소스 차이는 ~Dtor() {} 한 줄

   std::move 로 만들면        멤버: 이동                멤버: 복사     <- ★ 갈린다
   std::move 로 대입하면      멤버: 이동 대입           멤버: 복사 대입

   is_move_constructible            1                        1        <- ★ 안 갈린다
   is_nothrow_move_constructible    1                        0        <- ★ 여기서 갈린다

   vector 재할당                이동                       복사        <- 17번 (3)과 같은 자리
```

- ★★★ **`std::move` 를 썼는데 복사가 돈다.** 소스에서 바뀐 것은 **소멸자 한 줄**뿐이다.
- ★★★ **이유** — 사용자가 소멸자를 선언하면 **이동 생성자·이동 대입이 아예 안 만들어진다.**\
  그런데 **복사가 남아 있으므로** `std::move(a)` 가 만든 rvalue 는 **`const Tr&` 에 묶여 복사가 뽑힌다.**\
  ★ 그래서 **`is_move_constructible` 이 `1`** 이다 — 「이동 생성자가 있다」가 아니라 「**rvalue 로 만들 수 있다**」를 묻는 트레이트이기 때문이다.
- ★★★ **격자로 갈리는 칸은 `is_nothrow_move_constructible` 하나뿐**이다(`1` 대 `0`).\
  ★ **복사 생성자는 `noexcept` 가 아니므로** 그 칸이 떨어진다. **이것이 격자에 남는 유일한 흔적**이다.
- ★★★ **그 한 칸이 [17번](../17-move-constructor-assignment-and-moved-from-state/) (3)과 그대로 이어진다** — `(4)` 에서 `vector` 재할당이 **이동 대 복사**로 갈렸다.\
  ★ **소멸자 한 줄이 컨테이너의 동작까지 바꾼다.**
- ★★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic rule02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) Zero — 아무것도 안 쓴 타입
      멤버: 이동
      멤버: 이동 대입
(2) Dtor — 소멸자 한 줄만 더한 타입
      멤버: 복사
      멤버: 복사 대입
(3) 격자는 무엇이라고 답하나
    is_move_constructible          Zero=1  Dtor=1   ← 둘 다 1이라 안 갈린다
    is_nothrow_move_constructible  Zero=1  Dtor=0   ← 여기서 갈린다
(4) 그래서 vector 재할당이 갈린다
    [Zero] 자리 둘을 잡고 둘을 넣은 뒤 셋째를 넣는다
      멤버: 이동
      멤버: 이동
    [Dtor] 자리 둘을 잡고 둘을 넣은 뒤 셋째를 넣는다
      멤버: 복사
      멤버: 복사
```

- ★★★ **이것이 「법칙」이 법칙인 이유다.** 「소멸자를 적었으면 나머지 넷도 결정하라」는\
  **취향이 아니라 이 출력 때문**이다.

### (3) ★★ `= default` 는 본문 `{}` 와 다르다

**언제 쓰나** — 「어차피 빈 함수인데 `= default` 라고 굳이 써야 하나?」에서.

```cpp
/* rule03.cpp */
// = default 는 빈 본문 {} 과 다르다 — trivial 인가로 갈린다
#include <cstdio>
#include <type_traits>

struct T0 { int x; };                                  // 아무것도 안 썼다
struct T1 { int x; T1() = default; };                  // 기본 생성자 = default
struct T2 { int x; T2() {} };                          // 기본 생성자 빈 본문
struct T3 { int x; ~T3() = default; };                 // 소멸자 = default
struct T4 { int x; ~T4() {} };                         // 소멸자 빈 본문
struct T5 { int x; T5(const T5&) = default; };         // 복사 생성자 = default
struct T6 { int x; T6(const T6& o) : x(o.x) {} };      // 복사 생성자를 손으로 썼다
struct T7 { int x; ~T7(); };                           // 선언만 하고
T7::~T7() = default;                                   // ★ 클래스 밖에서 = default

template <class T> void row(const char* name) {
    std::printf("%-3s |   %d     %d     %d     %d   |  %zu\n", name,
        (int)std::is_trivially_default_constructible_v<T>,
        (int)std::is_trivially_copyable_v<T>,
        (int)std::is_trivially_destructible_v<T>,
        (int)std::is_trivial_v<T>,
        sizeof(T));
}

int main() {
    std::printf("타입 | t기본 t복사 t소멸 trivial | sizeof\n");
    row<T0>("T0"); row<T1>("T1"); row<T2>("T2"); row<T3>("T3");
    row<T4>("T4"); row<T5>("T5"); row<T6>("T6"); row<T7>("T7");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic rule03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
타입 | t기본 t복사 t소멸 trivial | sizeof
T0  |   1     1     1     1   |  4
T1  |   1     1     1     1   |  4
T2  |   0     1     1     0   |  4
T3  |   1     1     1     1   |  4
T4  |   0     0     0     0   |  4
T5  |   0     1     1     0   |  4
T6  |   0     0     1     0   |  4
T7  |   0     0     0     0   |  4
```

```text
   같은 「빈 함수」 세 가지가 서로 다르다

   ~T3() = default;            클래스 안 · 첫 선언   -> trivial 유지
   ~T4() {}                    본문을 내가 썼다      -> trivial 전부 0
   ~T7();  T7::~T7() = default;  클래스 밖           -> ★ T4 와 같아진다
                                                       (사용자 제공으로 친다)
```

| 타입 | 적은 것 | `t기본` | `t복사` | `t소멸` | `trivial` |
|---|---|---|---|---|---|
| `T0` | 아무것도 | 1 | 1 | 1 | 1 |
| `T1` | `T1() = default;` | ★ **1** | 1 | 1 | ★ **1** |
| `T2` | `T2() {}` | ★★★ **0** | 1 | 1 | ★★★ **0** |
| `T3` | `~T3() = default;` | 1 | 1 | 1 | 1 |
| `T4` | `~T4() {}` | ★★★ **0** | ★★★ **0** | ★★★ **0** | ★★★ **0** |
| `T5` | 복사 생성자 `= default` | ★ **0** | 1 | 1 | ★ **0** |
| `T6` | 복사 생성자를 손으로 | 0 | ★★ **0** | 1 | 0 |
| `T7` | **클래스 밖** `= default` | ★★★ **0** | ★★★ **0** | ★★★ **0** | ★★★ **0** |

- ★★★ **`T1` 과 `T2` 가 갈린다.** 소스는 `= default;` 대 `{}` 뿐인데 **`trivial` 이 `1` 대 `0`** 이다.\
  ★ `= default` 는 **「컴파일러가 만든 것을 그대로 쓰겠다」는 선언**이고, `{}` 는 「**내가 쓴 함수**」다.
- ★★★ **`T3` 과 `T4` 는 더 크게 갈린다.** 빈 소멸자 `{}` 하나가 **`is_trivially_copyable` 까지 `0`** 으로 떨어뜨린다.\
  ★ 그 값은 `memcpy` 로 옮겨도 되는지, 컨테이너가 최적화 경로를 탈 수 있는지를 가른다.
- ★★★ **`T7` 이 함정이다.** `~T7();` 로 선언만 하고 **클래스 밖에서 `= default`** 를 쓰면\
  **`= default` 의 효과가 안 난다** — `T4` 와 **똑같은 줄**이 나온다.\
  ★ 「첫 선언에서 `= default` 여야」 trivial 이 유지된다.
- ★★ **`T5` 의 `t기본` 이 `0`** 인 것은 다른 이유다 — **복사 생성자를 선언하면 기본 생성자가 안 만들어진다**((1)의 `S2`).\
  ★ 「없는 것」이라 **trivial 하게 기본 생성할 수도 없다.**
- ★ **`sizeof` 는 여덟 타입 모두 4** 다. **이 성질들은 크기에 아무 흔적도 안 남긴다.**
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic rule03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
타입 | t기본 t복사 t소멸 trivial | sizeof
T0  |   1     1     1     1   |  4
T1  |   1     1     1     1   |  4
T2  |   0     1     1     0   |  4
T3  |   1     1     1     1   |  4
T4  |   0     0     0     0   |  4
T5  |   0     1     1     0   |  4
T6  |   0     0     1     0   |  4
T7  |   0     0     0     0   |  4
```

### (4) ★★ `= delete` 는 「없는 것」이 아니라 「뽑힌 뒤 거부되는 것」이다

**언제 쓰나** — 「그 함수를 안 만들면 되지 왜 `= delete` 를 쓰나?」에서.

```cpp
/* rule04.cpp */
// = delete 는 후보에서 빠지는 것이 아니라 뽑힌 뒤 거부된다
#include <cstdio>
void f(int)    { std::printf("f(int)\n"); }
void f(double) = delete;                       // 실수로 double 로 부르는 것을 막고 싶다

struct M {
    int x;
    M() : x(0) {}
    M(const M&) = default;
    M(M&&)      = delete;                      // 이동은 지우고 복사만 남긴다
};

int main() {
    f(1);                                      // int 는 정확히 맞는다
    f(1.0f);                                   // float -> double 이 float -> int 보다 나은 변환이다
    M a;
    M b = a;                                   // 복사 — 된다
    M c = static_cast<M&&>(a);                 // 이동이 뽑힌 뒤 거부된다
    (void)b; (void)c;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 rule04.cpp -o ex (cc exit=1) =====
rule04.cpp: In function ‘int main()’:
rule04.cpp:15:6: error: use of deleted function ‘void f(double)’
   15 |     f(1.0f);                                   // float -> double 이 float -> int 보다 나은 변환이다
      |     ~^~~~~~
rule04.cpp:4:6: note: declared here
    4 | void f(double) = delete;                       // 실수로 double 로 부르는 것을 막고 싶다
      |      ^
rule04.cpp:18:29: error: use of deleted function ‘M::M(M&&)’
   18 |     M c = static_cast<M&&>(a);                 // 이동이 뽑힌 뒤 거부된다
      |                             ^
rule04.cpp:10:5: note: declared here
   10 |     M(M&&)      = delete;                      // 이동은 지우고 복사만 남긴다
      |     ^
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 rule04.cpp -o ex (cc exit=1) =====
rule04.cpp:15:5: error: call to deleted function 'f'
   15 |     f(1.0f);                                   // float -> double 이 float -> int 보다 나은 변환이다
      |     ^
rule04.cpp:4:6: note: candidate function has been explicitly deleted
    4 | void f(double) = delete;                       // 실수로 double 로 부르는 것을 막고 싶다
      |      ^
rule04.cpp:3:6: note: candidate function
    3 | void f(int)    { std::printf("f(int)\n"); }
      |      ^
rule04.cpp:18:7: error: call to deleted constructor of 'M'
   18 |     M c = static_cast<M&&>(a);                 // 이동이 뽑힌 뒤 거부된다
      |       ^   ~~~~~~~~~~~~~~~~~~~
rule04.cpp:10:5: note: 'M' has been explicitly marked deleted here
   10 |     M(M&&)      = delete;                      // 이동은 지우고 복사만 남긴다
      |     ^
2 errors generated.
```

```text
   void f(int)    { ... }
   void f(double) = delete;

   f(1.0f);   float -> double  (부동소수 승격)   <- 더 나은 변환이다
              float -> int     (부동소수→정수 변환)
              ↓
              오버로드 해결이 f(double) 을 「뽑는다」
              ↓
              그다음에 「지워졌다」고 거부한다   <- ★ 후보에서 빠지는 것이 아니다
```

- ★★★ **`f(1.0f)` 이 에러다.** `f(double)` 이 **선언조차 없었다면 `f(int)` 가 뽑혀 통과했을 것**이다.\
  ★ **`= delete` 는 후보 목록에 남아 있고, 뽑힌 뒤에 거부된다.** 그것이 「없는 것」과의 차이다.
- ★★★ **그래서 `= delete` 는 「실수로 이 변환으로 들어오는 것」을 막는 도구**가 된다.\
  ★ [16번](../16-copy-constructor-and-copy-assignment/)의 금지 사례에서 `by_value(a)` 가 걸린 것도 같은 원리다.
- ★★ **두 번째 에러가 특수 멤버 쪽이다** — `M(M&&) = delete;` 를 두고 `static_cast<M&&>(a)` 를 쓰면\
  **복사 생성자가 있는데도** 이동이 뽑혀 거부된다.\
  ★ 「이동을 지우면 복사로 떨어지겠지」가 **틀리는 자리**다.
- ★★ **두 컴파일러의 문구가 다르다** — g++ 는 `use of deleted function`,\
  clang 은 `call to deleted function` 에 **후보 목록까지** 보여 준다(`candidate function` 두 줄).\
  ★ 근거로 쓰는 것은 **`cc exit=1` 과 에러 개수 2**다.

### (5) ★★★ 0의 법칙 — 다섯을 하나도 안 쓰고 같은 것을 얻는다

**언제 쓰나** — 새 타입을 설계할 때마다. **이 절이 이 주제의 결론이다.**

```cpp
/* rule05.cpp */
// 0의 법칙 — 자원을 unique_ptr·vector 에 맡기면 다섯을 하나도 안 쓴다
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <string>
#include <type_traits>
#include <utility>
#include <vector>

static int allocs = 0, frees = 0;
void* operator new(std::size_t n) { ++allocs; return std::malloc(n); }
void  operator delete(void* p)              noexcept { if (p) ++frees; std::free(p); }
void  operator delete(void* p, std::size_t) noexcept { if (p) ++frees; std::free(p); }

struct Five {                                    // 5의 법칙 — 손으로 다섯을 다 썼다
    char* p;
    explicit Five(std::size_t n) : p(new char[n]) {}
    ~Five() { delete[] p; }
    Five(const Five&)            = delete;
    Five& operator=(const Five&) = delete;
    Five(Five&& o) noexcept : p(o.p) { o.p = nullptr; }
    Five& operator=(Five&& o) noexcept { if (this != &o) { delete[] p; p = o.p; o.p = nullptr; } return *this; }
};

struct Zero {                                    // 0의 법칙 — 한 줄도 안 썼다
    std::unique_ptr<char[]> p;
    std::vector<int>        v;
    std::string             s;
    explicit Zero(std::size_t n) : p(new char[n]), v(n, 0), s(n, 'x') {}
};

int main() {
    std::printf("타입  | 복사생 복사대 이동생 이동대 | 이동이 noexcept 인가 | 손으로 쓴 특수 멤버\n");
    std::printf("Five  |   %d      %d      %d      %d   |         %d            |        5개\n",
        (int)std::is_copy_constructible_v<Five>, (int)std::is_copy_assignable_v<Five>,
        (int)std::is_move_constructible_v<Five>, (int)std::is_move_assignable_v<Five>,
        (int)std::is_nothrow_move_constructible_v<Five>);
    std::printf("Zero  |   %d      %d      %d      %d   |         %d            |        0개\n",
        (int)std::is_copy_constructible_v<Zero>, (int)std::is_copy_assignable_v<Zero>,
        (int)std::is_move_constructible_v<Zero>, (int)std::is_move_assignable_v<Zero>,
        (int)std::is_nothrow_move_constructible_v<Zero>);

    std::printf("(1) Zero 를 옮긴다 — 할당이 몇 번 더 나나\n");
    {
        allocs = frees = 0;
        Zero a(64);
        int after_ctor = allocs;
        Zero b = std::move(a);
        std::printf("    생성에서 %d회 · 이동에서 %d회\n", after_ctor, allocs - after_ctor);
    }
    std::printf("    블록을 나온 뒤 new %d회 · delete %d회\n", allocs, frees);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic rule05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
타입  | 복사생 복사대 이동생 이동대 | 이동이 noexcept 인가 | 손으로 쓴 특수 멤버
Five  |   0      0      1      1   |         1            |        5개
Zero  |   0      0      1      1   |         1            |        0개
(1) Zero 를 옮긴다 — 할당이 몇 번 더 나나
    생성에서 3회 · 이동에서 0회
    블록을 나온 뒤 new 3회 · delete 3회
```

```text
   Five  (손으로 다섯을 다 썼다)        Zero  (한 줄도 안 썼다)
   ──────────────────────────           ──────────────────────
   explicit Five(size_t n)               std::unique_ptr<char[]> p;
   ~Five()                               std::vector<int>        v;
   Five(const Five&)     = delete        std::string             s;
   Five& operator=(const Five&) = delete
   Five(Five&&) noexcept                 explicit Zero(size_t n) : ...
   Five& operator=(Five&&) noexcept
   ──────────────────────────           ──────────────────────
   복사 0 · 이동 1 · noexcept 1          복사 0 · 이동 1 · noexcept 1   <- ★ 같다
   손으로 쓴 특수 멤버 5개                손으로 쓴 특수 멤버 0개
```

- ★★★ **격자가 한 칸도 안 다르다.** `Five` 가 다섯 줄로 얻은 것을 `Zero` 는 **한 줄도 안 쓰고** 얻는다.
- ★★★ **이동에서 할당이 0회다** — `생성에서 3회 · 이동에서 0회`.\
  ★ 멤버들이 각자 **자기 자원을 훔쳐 오기 때문**이다([17번](../17-move-constructor-assignment-and-moved-from-state/) (2)의 일이 세 번 일어난다).
- ★★★ **`new 3회 · delete 3회`** 로 맞는다 — **누수도 이중 해제도 없다.**\
  ★ 이 계수는 **전역 `operator new`/`operator delete` 를 갈아끼워** 센 것이다.\
  C++ 표준에 **런타임 할당 계수기가 없기 때문**에 쓰는 방법이다.
- ★★★ **그래서 규칙은 셋이 아니라 넷으로 읽는 것이 맞다.**
  - **0의 법칙** — 자원을 직접 안 들면 **다섯을 하나도 안 쓴다**. **기본값이다.**
  - **3의 법칙** — 소멸자·복사 생성자·복사 대입 중 **하나를 쓰면 셋을 다** 쓴다(C++98 시절).
  - **5의 법칙** — 거기에 **이동 둘을 더한다**((2)가 그 이유다).
  - ★ **5의 법칙의 현실판** — 자원을 직접 들면 **타입을 쪼개서 0으로 돌아간다**([15번](../15-raii-resources-as-types/)의 결론).

### (6) 경고를 누가 보나 — 탐침 여섯

「경고가 안 났다」를 산문으로 적으면 **안 물어본 것과 물었는데 조용한 것이 구분되지 않는다.**\
그래서 **0/3/5 를 어긴 자리 여섯 개**를 한 파일에 심고 두 컴파일러에 똑같이 물었다.

```cpp
/* rule06.cpp */
// 0/3/5 를 어긴 자리 여섯을 심었다 — 컴파일러가 몇 군데에서 말하는지 센다
#include <cstdio>
#include <cstdlib>
#include <utility>

struct R1 { char* p;                          // 1. 소멸자만 썼다 — 3의 법칙 위반
    R1() : p(static_cast<char*>(std::malloc(8))) {}
    ~R1() { std::free(p); } };
struct R2 { int a;                            // 2. 복사 생성자만 썼다
    R2() : a(0) {}
    R2(const R2& o) : a(o.a) {} };
struct R3 { int a;                            // 3. 이동 생성자만 썼다 — 복사가 지워진다
    R3() : a(0) {}
    R3(R3&& o) noexcept : a(o.a) {} };
struct R4 { char* p;                          // 4. 소멸자 + 복사는 막았는데 이동을 안 열었다
    R4() : p(static_cast<char*>(std::malloc(8))) {}
    ~R4() { std::free(p); }
    R4(const R4&) = delete;
    R4& operator=(const R4&) = delete; };
struct R5 { int a; ~R5(); };                  // 5. 클래스 밖 = default — trivial 이 아니게 된다
R5::~R5() = default;
struct R6 { int a;                            // 6. 복사 대입만 썼다
    R6() : a(0) {}
    R6& operator=(const R6& o) { a = o.a; return *this; } };

int main() {
    R1 a; R1 b(a);                            // 얕은 복사 — 소멸자 둘이 같은 포인터를 놓는다
    R2 c; R2 d(c); c = d;                     // 암묵 복사 대입을 쓴다
    R3 e; R3 f(std::move(e)); (void)f;
    R4 g; (void)g;
    R5 h; R5 i(h); (void)i;
    R6 j, k; j = k; R6 l(j); (void)l;
    std::printf("여섯 자리 전부 컴파일됐다\n");
    a.p = nullptr; b.p = nullptr;             // 이중 해제를 피해 치운다
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic rule06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
rule06.cpp: In function ‘int main()’:
rule06.cpp:28:24: warning: implicitly-declared ‘constexpr R2& R2::operator=(const R2&)’ is deprecated [-Wdeprecated-copy]
   28 |     R2 c; R2 d(c); c = d;                     // 암묵 복사 대입을 쓴다
      |                        ^
rule06.cpp:11:5: note: because ‘R2’ has user-provided ‘R2::R2(const R2&)’
   11 |     R2(const R2& o) : a(o.a) {} };
      |     ^~
rule06.cpp:32:27: warning: implicitly-declared ‘constexpr R6::R6(const R6&)’ is deprecated [-Wdeprecated-copy]
   32 |     R6 j, k; j = k; R6 l(j); (void)l;
      |                           ^
rule06.cpp:24:9: note: because ‘R6’ has user-provided ‘R6& R6::operator=(const R6&)’
   24 |     R6& operator=(const R6& o) { a = o.a; return *this; } };
      |         ^~~~~~~~
여섯 자리 전부 컴파일됐다
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic rule06.cpp -o ex (cc exit=0) =====
rule06.cpp:11:5: warning: definition of implicit copy assignment operator for 'R2' is deprecated because it has a user-provided copy constructor [-Wdeprecated-copy-with-user-provided-copy]
   11 |     R2(const R2& o) : a(o.a) {} };
      |     ^
rule06.cpp:28:22: note: in implicit copy assignment operator for 'R2' first required here
   28 |     R2 c; R2 d(c); c = d;                     // 암묵 복사 대입을 쓴다
      |                      ^
rule06.cpp:24:9: warning: definition of implicit copy constructor for 'R6' is deprecated because it has a user-provided copy assignment operator [-Wdeprecated-copy-with-user-provided-copy]
   24 |     R6& operator=(const R6& o) { a = o.a; return *this; } };
      |         ^
rule06.cpp:32:24: note: in implicit copy constructor for 'R6' first required here
   32 |     R6 j, k; j = k; R6 l(j); (void)l;
      |                        ^
2 warnings generated.
```

```text
===== echo "rule06 탐침 여섯  g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic rule06.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
rule06 탐침 여섯  g++ 경고 2
===== echo "rule06 탐침 여섯  clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic rule06.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
rule06 탐침 여섯  clang 경고 2
===== echo "rule06 을 ASan 으로 돌리면: $(g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. rule06.cpp -o exa 2>/dev/null; ./exa >/dev/null 2>asan18.txt; grep -cE 'ERROR: (Address|Leak)Sanitizer' asan18.txt) 건" (exit=0) =====
rule06 을 ASan 으로 돌리면: 1 건
===== echo "그 리포트의 요약: $(grep -hE '^SUMMARY' asan18.txt | head -1 | grep . || echo 리포트 없음)" (exit=0) =====
그 리포트의 요약: SUMMARY: AddressSanitizer: 8 byte(s) leaked in 1 allocation(s).
```

```text
   컴파일러가 말해 주는 축과 안 말해 주는 축

   3의 법칙 축   복사 생성자만 썼다  -> warning     ★ 답한다
                 복사 대입만 썼다    -> warning     ★ 답한다
   ─────────────────────────────────────────────
   5의 법칙 축   소멸자만 썼다       -> 0건
                 이동 생성자만 썼다  -> 0건
                 이동을 안 열었다    -> 0건         (ASan 이 8바이트를 잡는다)
   = default 축  클래스 밖 = default -> 0건         ★ 격자로만 보인다
```

| 심은 것 | g++ | clang | 실제로는 |
|---|---|---|---|
| 1. 소멸자만 썼다(3의 법칙 위반) | 0 | 0 | ★★★ **얕은 복사 → 이중 해제** · 이동도 사라졌다((2)) |
| 2. 복사 생성자만 썼다 | ★ **1** | ★ **1** | ★★ 암묵 복사 대입이 **deprecated** |
| 3. 이동 생성자만 썼다 | 0 | 0 | ★★★ **복사가 `= delete` 된다**((1)의 `S3`) |
| 4. 소멸자+복사 차단, 이동은 안 열었다 | 0 | 0 | ★★ 옮길 수 없어 **컨테이너에서 복사도 이동도 못 한다** |
| 5. 클래스 밖 `= default` | 0 | 0 | ★★★ **trivial 이 아니게 된다**((3)의 `T7`) |
| 6. 복사 대입만 썼다 | ★ **1** | ★ **1** | ★★ 암묵 복사 **생성자**가 deprecated |

- ★★★ **탐침 여섯 중 답한 것 2, 침묵한 것 4다.** **`cc exit=0`** 이고 프로그램은 끝까지 돈다.
- ★★★ **답한 둘이 정확히 「3의 법칙」의 두 방향이다** — 복사 생성자만 쓴 것과 복사 대입만 쓴 것.\
  ★ **이동 쪽은 하나도 안 잡는다.** 5의 법칙은 **컴파일러가 도와주지 않는다.**
- ★★★ **ASan 은 `8 byte(s) leaked in 1 allocation(s)` 를 잡는다** — 탐침 4번의 `R4` 가 샌 것이다.\
  ★ 탐침 1번의 얕은 복사는 **소스가 `a.p = nullptr;` 로 치워 놓아** 안 잡혔다.
- ★★ **가장 위험한 것은 5번이다** — `T7` 형태는 **경고도 없고 ASan 도 안 보고 격자로만** 드러난다.

### (7) ★★ 종료 코드가 0인데 표준이 금지한 것 둘

**언제 쓰나** — 「빌드가 됐으니 표준에 맞는 코드다」를 의심할 때.

★★ **이 배치의 고정 항목이다** — 앞 배치들이 같은 모양을 세 번 만났다([14번](../14-destructors-and-deterministic-destruction/) (8)).

```cpp
/* rule07.cpp */
// 종료 코드가 0인데 표준이 금지한 것 둘 — 익명 구조체 멤버와 비-trivially-copyable 의 memcpy
#include <cstdio>
#include <cstring>
#include <string>
#include <type_traits>

struct Pair { struct { int a; int b; }; };      // ① ISO C++ 는 익명 구조체를 금지한다
struct NT   { std::string s; int x; };          // ② trivially copyable 이 아니다

int main() {
    Pair p; p.a = 1; p.b = 2;
    Pair q = p;                                 // 암묵 복사 생성자는 그래도 만들어진다
    std::printf("익명 구조체 멤버를 복사하면  q.a=%d q.b=%d\n", q.a, q.b);

    NT u{"가", 1}, v{"나", 2};
    std::printf("is_trivially_copyable<NT> = %d\n", (int)std::is_trivially_copyable_v<NT>);
    std::memcpy(&v, &u, sizeof(NT));            // ★ 표준이 금지한 것 — UB 다
    std::printf("memcpy 뒤 v.x = %d\n", v.x);
    new (&v) NT{"치운다", 0};                    // 소멸자가 같은 버퍼를 두 번 놓지 않도록 덮어쓴다
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic rule07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
rule07.cpp:7:22: warning: ISO C++ prohibits anonymous structs [-Wpedantic]
    7 | struct Pair { struct { int a; int b; }; };      // ① ISO C++ 는 익명 구조체를 금지한다
      |                      ^
rule07.cpp: In function ‘int main()’:
rule07.cpp:17:16: warning: ‘void* memcpy(void*, const void*, size_t)’ writing to an object of type ‘struct NT’ with no trivial copy-assignment; use copy-assignment or copy-initialization instead [-Wclass-memaccess]
   17 |     std::memcpy(&v, &u, sizeof(NT));            // ★ 표준이 금지한 것 — UB 다
      |     ~~~~~~~~~~~^~~~~~~~~~~~~~~~~~~~
rule07.cpp:8:8: note: ‘struct NT’ declared here
    8 | struct NT   { std::string s; int x; };          // ② trivially copyable 이 아니다
      |        ^~
익명 구조체 멤버를 복사하면  q.a=1 q.b=2
is_trivially_copyable<NT> = 0
memcpy 뒤 v.x = 1
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic rule07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
rule07.cpp:7:15: warning: anonymous structs are a GNU extension [-Wgnu-anonymous-struct]
    7 | struct Pair { struct { int a; int b; }; };      // ① ISO C++ 는 익명 구조체를 금지한다
      |               ^
1 warning generated.
익명 구조체 멤버를 복사하면  q.a=1 q.b=2
is_trivially_copyable<NT> = 0
memcpy 뒤 v.x = 1
```

```text
===== echo "g++ -pedantic-errors 에러 $(g++ -std=c++20 -Wall -Wextra -pedantic-errors -fmax-errors=0 rule07.cpp -o ex 2>&1 | grep -c 'error:')" (exit=0) =====
g++ -pedantic-errors 에러 1
===== echo "clang -pedantic-errors 에러 $(clang++ -std=c++20 -Wall -Wextra -pedantic-errors -ferror-limit=0 rule07.cpp -o ex 2>&1 | grep -c 'error:')" (exit=0) =====
clang -pedantic-errors 에러 1
```

| 심은 것 | g++ `-pedantic` | clang `-pedantic` | `-pedantic-errors` | 실제로는 |
|---|---|---|---|---|
| ① **익명 구조체 멤버** | ★★ **warning** (`ISO C++ prohibits anonymous structs`) | ★★ **warning** (`anonymous structs are a GNU extension`) | ★★★ **양쪽 에러 1건** | ISO C++ 가 **금지**한다 |
| ② **비 trivially-copyable 을 `memcpy`** | ★ **warning** (`-Wclass-memaccess`) | ★★★ **0건** | ★★★ **양쪽 그대로 통과** | **UB** 다 |

- ★★★ **둘 다 `cc exit=0` · `run exit=0`** 이고 **값까지 그럴듯하게 나온다**(`q.a=1 q.b=2` · `memcpy 뒤 v.x = 1`).
- ★★★ **①은 `-pedantic-errors` 라야 잡힌다.** `-pedantic` 만으로는 **경고에 머문다** —  [14번](../14-destructors-and-deterministic-destruction/) (8)과 **같은 집안**이다.
- ★★★ **②는 clang 이 아예 침묵한다.** `is_trivially_copyable<NT>` 가 **`0`** 이라고 같은 프로그램이 찍어 놓고도  **그 값을 `memcpy` 에 연결해 주는 것은 g++ 뿐**이다.  ★ **두 컴파일러가 갈리는 자리**이므로 **양쪽을 다 실었다.**
- ★★ **이것이 (3)의 `trivial` 격자가 왜 실용적인지를 보인다** — 격자가 `0` 이라고 말한 타입을  `memcpy` 로 옮기면 **UB** 이고, **도구는 그것을 반만 본다.**

## 문법 — 형태와 규칙

### 형태

```cpp
/* rule08.cpp */
// 0의 법칙 · 5의 법칙 · = default / = delete 의 형태. 이 파일은 그대로 컴파일된다
#include <cstdio>
#include <memory>
#include <string>
#include <type_traits>
#include <vector>

struct Zero {                          // ① 0의 법칙 — 자원을 남에게 맡기고 다섯을 안 쓴다
    std::string             name;
    std::vector<int>        data;
    std::unique_ptr<char[]> buf;
};

class Five {                           // ② 5의 법칙 — 자원을 직접 들면 다섯을 다 적는다
public:
    explicit Five(std::size_t n) : p_(new char[n]) {}
    ~Five()                                   { delete[] p_; }
    Five(const Five&)                         = delete;      // 복사는 막는다
    Five& operator=(const Five&)              = delete;
    Five(Five&& o) noexcept : p_(o.p_)        { o.p_ = nullptr; }
    Five& operator=(Five&& o) noexcept {
        if (this != &o) { delete[] p_; p_ = o.p_; o.p_ = nullptr; }
        return *this;
    }
private:
    char* p_;
};

struct Explicit {                      // ③ = default 는 「컴파일러가 만든 것을 쓰겠다」는 선언이다
    int x;
    Explicit()                         = default;
    Explicit(const Explicit&)          = default;
    Explicit& operator=(const Explicit&) = default;
    ~Explicit()                        = default;
};

int main() {
    std::printf("Zero     : 손으로 쓴 특수 멤버 0개 · 이동 가능 %d · trivially copyable %d\n",
                (int)std::is_move_constructible_v<Zero>, (int)std::is_trivially_copyable_v<Zero>);
    std::printf("Five     : 손으로 쓴 특수 멤버 5개 · 복사 가능 %d · 이동 가능 %d\n",
                (int)std::is_copy_constructible_v<Five>, (int)std::is_move_constructible_v<Five>);
    std::printf("Explicit : 전부 = default   · trivially copyable %d · trivial %d\n",
                (int)std::is_trivially_copyable_v<Explicit>, (int)std::is_trivial_v<Explicit>);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic rule08.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
Zero     : 손으로 쓴 특수 멤버 0개 · 이동 가능 1 · trivially copyable 0
Five     : 손으로 쓴 특수 멤버 5개 · 복사 가능 0 · 이동 가능 1
Explicit : 전부 = default   · trivially copyable 1 · trivial 1
```

### 규칙

- ★★★ **0의 법칙이 기본값이다** — 자원을 `unique_ptr`·`vector`·`string` 에 맡기고 **다섯을 하나도 안 쓴다**((5)).
- **3의 법칙** — 소멸자·복사 생성자·복사 대입 중 **하나를 썼으면 셋을 다** 쓴다.
- **5의 법칙** — 거기에 **이동 생성자·이동 대입**을 더한다. **소멸자를 쓰면 이동이 사라지기 때문**이다((2)).
- ★★ **`= default` 는 첫 선언에 쓴다.** 클래스 밖에서 쓰면 **trivial 이 아니게 된다**((3)의 `T7`).
- ★★ **`= default` 는 본문 `{}` 와 다르다** — `trivial` 계열 트레이트가 갈린다((3)).
- ★★ **`= delete` 는 후보에서 빼는 것이 아니라 뽑힌 뒤 거부하는 것**이다((4)).
- **복사를 막으려면 둘을 다 지운다** — 복사 생성자만 지우면 **복사 대입이 남는다**((1)의 `S5`).
- **이동 생성자를 쓰면 복사가 자동으로 지워진다**((1)의 `S3`) — 그래서 **필요하면 `= default` 로 되살린다.**
- ★ **자원을 둘 이상 직접 들지 않는다** — 타입을 쪼개면 0으로 돌아간다([15번](../15-raii-resources-as-types/) (6)).

### 금지 사례 — 네 줄이 각각 막힌다

```cpp
/* rule09.cpp */
// = default 와 = delete 가 컴파일에서 막는 네 줄
struct A {
    int x;
    A(int) = default;                    // 1. 특수 멤버가 아닌 것에 = default
};
struct B {
    int x;
    B() = delete;                        // 기본 생성자를 지웠다
};
struct C {
    int x;
    C() = default;
    C(const C&) = delete;                // 복사를 지웠다
};
void takes(C);                           // 값으로 받는다

int main() {
    B b;                                 // 2. 지워진 기본 생성자를 썼다
    C c;
    C d = c;                             // 3. 지워진 복사 생성자를 썼다
    takes(c);                            // 4. 값 전달도 복사다
    (void)d;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 rule09.cpp -o ex (cc exit=1) =====
rule09.cpp:4:14: error: ‘A::A(int)’ cannot be defaulted
    4 |     A(int) = default;                    // 1. 특수 멤버가 아닌 것에 = default
      |              ^~~~~~~
rule09.cpp: In function ‘int main()’:
rule09.cpp:18:7: error: use of deleted function ‘B::B()’
   18 |     B b;                                 // 2. 지워진 기본 생성자를 썼다
      |       ^
rule09.cpp:8:5: note: declared here
    8 |     B() = delete;                        // 기본 생성자를 지웠다
      |     ^
rule09.cpp:20:11: error: use of deleted function ‘C::C(const C&)’
   20 |     C d = c;                             // 3. 지워진 복사 생성자를 썼다
      |           ^
rule09.cpp:13:5: note: declared here
   13 |     C(const C&) = delete;                // 복사를 지웠다
      |     ^
rule09.cpp:21:10: error: use of deleted function ‘C::C(const C&)’
   21 |     takes(c);                            // 4. 값 전달도 복사다
      |     ~~~~~^~~
rule09.cpp:13:5: note: declared here
   13 |     C(const C&) = delete;                // 복사를 지웠다
      |     ^
rule09.cpp:15:12: note:   initializing argument 1 of ‘void takes(C)’
   15 | void takes(C);                           // 값으로 받는다
      |            ^
rule09.cpp:18:7: warning: unused variable ‘b’ [-Wunused-variable]
   18 |     B b;                                 // 2. 지워진 기본 생성자를 썼다
      |       ^
```

- ★★★ **네 에러의 이유가 다르다.**
  - **`A(int) = default;`** — `= default` 는 **특수 멤버에만** 쓸 수 있다. 시그니처가 맞아야 한다.
  - **`B b;`** — 기본 생성자를 지웠다. 「없는 것」이 아니라 「**지워진 것**」이라 진단이 그 줄을 가리킨다.
  - **`C d = c;`** — 복사 생성자를 지웠다.
  - ★★ **`takes(c);`** — **값 전달도 복사다.** 복사라는 글자가 없는데 같은 에러가 난다((4)와 같은 원리).

## 어디서 틀리나

### 1. ★★★ 「소멸자만 적었으니 나머지는 그대로겠지」

(2)가 그 반증이다 — **이동 둘이 사라지고 `std::move` 가 복사로 떨어진다.**\
★ **에러도 경고도 없다.** 탐침 1번이 **두 컴파일러 다 0건**이었다((6)).

### 2. ★★★ 「`is_move_constructible` 이 1 이니 이동이 있다」

(2)가 보인 것은 **`Zero` 와 `Dtor` 가 둘 다 `1`** 이라는 것이다.\
그 트레이트는 「**rvalue 로 만들 수 있나**」를 묻지 「이동 생성자가 있나」를 묻지 않는다.\
★ **갈리는 칸은 `is_nothrow_move_constructible` 하나**다.

### 3. ★★★ 「`= default` 는 빈 본문과 같다」

(3)의 `T1`·`T2` 가 그 자리다 — **`trivial` 이 `1` 대 `0`** 으로 갈린다.\
★ 더 나쁜 것은 `T7` 이다 — **클래스 밖 `= default` 는 효과가 없다.**

### 4. ★★ 「`= delete` 는 그 함수를 없애는 것」

(4)가 보인 것은 **뽑힌 뒤 거부된다**는 것이다.\
★ `void f(double) = delete;` 를 **아예 안 썼다면** `f(1.0f)` 은 `f(int)` 로 **통과했을 것**이다.

### 5. ★★ 「복사 생성자를 지웠으니 복사가 막혔다」

(1)의 `S5` 가 그 자리다 — **복사 대입이 `1` 로 남아 있다.**\
★ **둘을 다 지워야** 막힌다.

### 6. ★★ 「이동을 지우면 복사로 떨어지겠지」

(4)의 두 번째 에러가 그 자리다 — `M(M&&) = delete;` 를 두면 **복사 생성자가 있는데도** 이동이 뽑혀 거부된다.

### 7. ★ 「컴파일러가 법칙 위반을 알려 준다」

**탐침 여섯 중 둘만 답했다**((6)). **답한 둘은 전부 3의 법칙 쪽**이고 **5의 법칙은 하나도 안 잡힌다.**

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 거의 전부를 덮는다** — 격자의 0/1 은 **언어 규칙이 정한 값**이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **격자의 0/1 전부**((1)(3)(5)) · ★★★ **소멸자를 선언하면 이동이 안 만들어지는 것**((2)) · **이동을 선언하면 복사가 지워지는 것**((1)의 `S3`) · **복사 생성자를 선언하면 기본 생성자가 사라지는 것**((1)의 `S2`) · ★★★ **`= delete` 가 뽑힌 뒤 거부되는 것**((4)) · **클래스 밖 `= default` 는 trivial 이 아닌 것**((3)의 `T7`) | 트레이트 출력 · 계수 로그 · 진단 + `cc exit` | ★★★ 「**이 줄에서 이동이 불렸나 복사가 불렸나**」 — 격자로는 안 보인다((2)) |
| **조건부 표준** | 특정 조건에서만 보장 | ★★ **`= default`·`= delete`·이동 연산·5의 법칙은 C++11부터** · **암묵 복사 대입의 deprecated 도 C++11부터** · `-Wdeprecated-copy` 는 **컴파일러의 호의**다 | `-std=c++20` 으로만 돌렸다 | ★ **C++98 판으로는 안 돌려 봤다**(거기에는 3의 법칙만 있다) |
| **구현 정의** | 문서화 의무가 있다 | ★ **진단 문구와 경고 이름** · **clang 이 후보 목록을 보여 주는 것** · **`sizeof` 가 4인 것** | 두 컴파일러 전문 · `sizeof` 출력 | ★★ **다른 컴파일러는 다른 이름을 쓴다** |
| **미명시** | 몇 가지 중 하나 | ★ **(5)에서 생성 중 `new` 가 3회인 것** — `string`·`vector`·`unique_ptr` 각각의 할당 전략은 **구현이 정한다** | 전역 `operator new` 계수 | ★ **작은 문자열 최적화가 꺼지면 수가 달라진다** |
| **UB** | 아무 일이나 | ★★ **탐침 1번의 얕은 복사 뒤 이중 해제**((6)) — 소스가 치워 놓아 **이 판에서는 안 터졌다** | [15번](../15-raii-resources-as-types/) (4)의 ASan `double-free` | ★★★ **법칙 위반 자체는 UB 가 아니다** — 그래서 **경고가 없다** |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | ASan | 트레이트 격자 |
|---|---|---|---|---|---|
| `= default` 를 특수 멤버가 아닌 것에 | 표준 | **error** | **error** | — | — |
| 지워진 함수를 부름 | 표준 | **error** | **error** | — | — |
| 복사 생성자만 씀 | 조건부 | ★ **warning 1** | ★ **warning 1** | — | ★ `S2` 의 첫 칸 |
| 복사 대입만 씀 | 조건부 | ★ **warning 1** | ★ **warning 1** | — | — |
| ★★★ **소멸자만 써서 이동이 사라짐** | 표준 | ★★★ **0건** | ★★★ **0건** | ★★★ **0건** | ★★★ **`nothrow` 칸만**((2)) |
| ★★★ **클래스 밖 `= default`** | 표준 | ★★★ **0건** | ★★★ **0건** | ★★★ **0건** | ★★★ **격자만**((3)의 `T7`) |
| 자원을 든 채 이동을 안 엶 | — | ★★★ **0건** | ★★★ **0건** | ★ **8바이트 누수** | ★ 이동 칸이 `0` |

- ★★ **이 표의 결론 세 줄**
  - **`= default`/`= delete` 의 「형태」가 틀린 것은 전부 컴파일에서 걸린다.**
  - ★★★ **「법칙」 위반은 3의 법칙 두 방향만 경고가 있다.** 5의 법칙은 **하나도 없다.**
  - ★★★ **그래서 이 주제의 유일한 전수 도구가 트레이트 격자다** — 그리고 **그 격자도 (2)의 자리는 못 본다.**

### ★ 진단이 0줄인 것도 블록으로 받았다

(6)이 그 자리다. **탐침 여섯 중 답한 것 2, 침묵한 것 4**이고 **`cc exit=0`** 이다.\
그 침묵을 메우는 것이 **(1)(3)의 격자**·**(2)의 계수 로그**·**ASan 의 `8 byte(s) leaked in 1 allocation(s)`** 다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 새 타입을 만든다 | ★★★ **0의 법칙 — 다섯을 하나도 안 쓴다** | 자원은 멤버에게 맡긴다((5)) |
| 자원을 직접 들어야 한다 | ★★ **5의 법칙 — 다섯을 다 쓴다** | 하나만 쓰면 나머지가 사라진다((2)) |
| 자원을 둘 이상 든다 | ★★★ **타입을 쪼갠다** | 생성자 중간 실패에서 샌다([15번](../15-raii-resources-as-types/) (6)) |
| 복사를 막고 싶다 | ★★ **복사 생성자·복사 대입 둘 다 `= delete`** | 하나만 지우면 다른 쪽이 남는다((1)의 `S5`) |
| 실수로 들어오는 변환을 막고 싶다 | ★★ **그 오버로드를 `= delete`** | 뽑힌 뒤 거부된다((4)) |
| 「기본 그대로」를 명시하고 싶다 | ★★ **첫 선언에 `= default`** | 클래스 밖은 효과가 없다((3)의 `T7`) |
| 소멸자를 꼭 써야 한다 | ★★★ **이동 둘을 `= default` 로 되살린다** | 안 그러면 `vector` 가 복사로 간다((2)) |
| `trivially_copyable` 이 필요하다 | ★ **본문 `{}` 를 쓰지 않는다** | 빈 소멸자 하나에 떨어진다((3)의 `T4`) |

- ★ **「법칙을 외워라」가 아니라 「자원을 직접 들지 마라」가 기본값이다.** 그러면 법칙이 안 필요해진다.

## 핵심 문장

- **소멸자 한 줄을 적으면 이동 두 개가 조용히 사라진다** — 그것이 **「법칙」이 법칙인 이유**다.
- **`is_move_constructible` 은 그 사라짐을 못 본다.** 갈리는 칸은 **`is_nothrow_move_constructible`** 하나다.
- **`= default` 는 본문 `{}` 와 다르고**, **클래스 밖 `= default` 는 효과가 없다.**
- **`= delete` 는 후보에서 빠지는 것이 아니라 뽑힌 뒤 거부된다** — 그래서 **변환을 막는 도구**가 된다.
- **이동 생성자를 선언하면 복사가 지워지고**, **복사 생성자를 선언하면 기본 생성자가 사라진다.**
- ★★★ **0의 법칙이 기본값이다** — `Zero` 가 **한 줄도 안 쓰고** `Five` 의 다섯 줄과 **같은 격자**를 얻었다.
- **컴파일러가 잡아 주는 것은 3의 법칙 두 방향뿐**이다 — **5의 법칙은 하나도 안 잡는다.**

## 관련 자료

- [16번](../16-copy-constructor-and-copy-assignment/) — **복사의 구현.** (7)의 탐침 2번이 답한 경고가 **이 주제의 예고**였다.
- [17번](../17-move-constructor-assignment-and-moved-from-state/) — **이동의 구현.** (2)의 `(4)` 가 그 편 (3)의 `vector` 재할당과 **같은 자리**다.
- [15번](../15-raii-resources-as-types/) — **자원을 타입으로 묶기.** (5)의 「타입을 쪼개면 0으로 돌아간다」가 그 편 (6)의 결론이다.
- [14번](../14-destructors-and-deterministic-destruction/) — **소멸자.** (2)의 「소멸자를 선언했다」가 무슨 뜻인지가 거기다.
- [13번](../13-constructors-member-init-list-and-delegating/) — **생성자와 초기화 순서.** (문법)의 형태가 그 규칙 위에 있다.
- [1번](../01-function-overloading-and-overload-resolution/) — **오버로드 해결.** (4)의 「뽑힌 뒤 거부된다」가 그 절차의 어느 단계인지가 거기다.
- 목록의 **26번 주제** — `unique_ptr`. (5)의 `Zero` 가 기대는 것이 그것이다.
- 목록의 **41번 주제** — 순차 컨테이너. (2)의 `vector` 재할당 정책이 거기가 정본이다.
- 목록의 **52·53번 주제** — 예외 안전 보장과 `noexcept`. (2)의 `nothrow` 칸이 왜 중요한지가 거기다.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **9번**([`09-copy-clone-and-drop/`](../../../rust/syntax/09-copy-clone-and-drop/)) — 기본값이 「**아무것도 안 준다**」다.\
  ★ 러스트는 **`#[derive(Clone)]` 을 적어야** 복사가 생긴다. C++ 은 **적지 않아야** 생긴다.\
  ★ 그래서 러스트에는 **「조용히 사라지는」 자리가 없다** — 대신 **매번 적어야** 한다.
- C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **37번 주제**(`IDisposable`/`using`) — **GC 가 있는 언어의** 「**소멸자 자리**」다.\
  ★ 거기에는 **「해제를 적으면 복사가 사라지는」 연쇄가 없다** — 해제와 복사가 **다른 축**이기 때문이다.

## 용어 풀이

> **0의 법칙(rule of zero)** — 자원을 직접 안 들면 **특수 멤버를 하나도 안 쓴다.**\
> 예: (5)의 `Zero` — `unique_ptr`·`vector`·`string` 세 멤버뿐이다.

> **3의 법칙(rule of three)** — 소멸자·복사 생성자·복사 대입 중 **하나를 썼으면 셋을 다** 쓴다. **C++98 시절의 규칙**이다.

> **5의 법칙(rule of five)** — 3의 법칙 + **이동 생성자·이동 대입**. **C++11부터**다.

> **`= default`** — 「컴파일러가 만들 것을 그대로 쓰겠다」는 선언.\
> 예: (3)의 `T1` — 빈 본문 `{}` 와 달리 **trivial 이 유지된다.**

> **`= delete`** — 「이 함수를 부르면 에러」라는 선언. **후보에는 남는다.**\
> 예: (4)에서 `f(1.0f)` 이 `f(double)` 로 뽑힌 뒤 거부됐다.

> **trivial** — **컴파일러가 아무 일도 안 하는** 특수 멤버를 가진 것. `memcpy` 로 옮겨도 되는지를 가른다.\
> 예: (3)에서 빈 소멸자 `{}` 하나에 `is_trivially_copyable` 이 `0` 이 됐다.

> **`is_move_constructible`** — 「**rvalue 로 만들 수 있나**」를 묻는다. **이동 생성자가 있나를 묻는 것이 아니다.**\
> 예: (2)에서 이동이 사라진 `Dtor` 에도 `1` 이 나왔다.

> **`is_nothrow_move_constructible`** — 그 생성이 **`noexcept` 인가**를 묻는다.\
> 예: (2)에서 **유일하게 갈린 칸**이고, [17번](../17-move-constructor-assignment-and-moved-from-state/) (3)의 `vector` 재할당이 보는 것도 이것이다.

> **암묵적으로 지워진 함수(implicitly deleted)** — 기본 정의가 ill-formed 라서 **컴파일러가 지운 것**.\
> 예: (1)의 `S3` 에서 이동 생성자를 선언했더니 **복사 둘이 지워졌다.**

## 더 들어가면

- **`= default` 의 예외 명세 불일치** — C++17 이전에는 `noexcept = default` 가 안 맞으면 **함수가 지워졌고**, 이후에는 ill-formed 다. 이 문서는 안 던졌다.
- **`std::is_trivially_relocatable`(C++26 제안)** — (3)의 `trivial` 계열이 답하지 못하는 「**옮겨도 되나**」를 직접 묻는 트레이트.
- **할당자 인식 타입의 특수 멤버** — `propagate_on_container_*` 가 **복사·이동의 뜻을 바꾼다.** 표준 컨테이너의 층이다.
- **`=delete("이유")`(C++26)** — 지운 이유를 진단에 싣는 문법. 이 머신의 컴파일러 판에서는 **안 던졌다.**
- **`std::exchange` 로 쓰는 5의 법칙** — (문법)의 `Five` 를 더 짧게 쓰는 관용구. [17번](../17-move-constructor-assignment-and-moved-from-state/)의 「더 들어가면」과 같은 항목이다.
