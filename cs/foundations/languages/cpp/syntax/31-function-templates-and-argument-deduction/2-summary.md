# cpp/syntax/31 — 함수 템플릿과 인자 추론 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 템플릿 인자 추론](https://en.cppreference.com/w/cpp/language/template_argument_deduction) · [cppreference — 함수 템플릿](https://en.cppreference.com/w/cpp/language/function_template)\
> ★ **이 배치에서는 위 cppreference 두 쪽을 열지 않았다** — 규칙은 **전부 두 컴파일러가 스스로 말한 타입**(`static_assert` 진단 · `__PRETTY_FUNCTION__`)과 **기호표**로 적었다.
> **실행 검증** — 이 문서의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **libstdc++ 13** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 대비 블록은 **rustc 1.92.0** 이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고, 블록마다 **소스 파일 이름이 다르다**(`tmpl01.cpp` \~ `tmpl05.cpp` · `tmpl-grid.sh` · `tmpl-inst.sh` · `infer.rs`).\
> ★★ **격자형 에러 블록은 `-fmax-errors=0` · `-ferror-limit=0` 을 배너에 적어** 던졌다 · ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. 소스 펜스의 배너도 **캡처가 찍은 것**이다.
> **버전** — 함수 템플릿과 인자 추론은 **C++98부터**, 전달 참조와 참조 축약은 **C++11부터**, **`std::type_identity_t` 는 C++20부터**다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 실행으로 접지했다.
> ★★★ **[05번](../05-auto-and-decltype-type-deduction/)에서 온다 — 앞 편들이 잰 것은 다시 재지 않고 인용한다.**\
> [05번](../05-auto-and-decltype-type-deduction/) (1)(4) — **`auto` 는 참조·최상위 `const` 를 떨어뜨리고, 배열·함수를 감쇠시킨다 · `auto&` 는 안 시킨다**(`int*` 대 `int (&)[3]`) · (9) — **`void show(auto x)` 는 `template <class T> void show(T x)` 의 다른 표기라 추론 규칙이 같다.**\
> [09번](../09-rvalue-references-move-and-forward/) (6) — **`T&&` 에 lvalue 를 넘기면 `T = int&`, 축약해 `int&`** · **`probe(42)` 와 `probe(std::move(i))` 는 같은 인스턴스라 에러가 여섯 줄**.\
> Rust 갈래 [31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/) (7)(8) — **C++ 템플릿의 몸통은 인스턴스화할 때 검사된다**(두 컴파일러 `exit 0`) · **단형화를 센다.**\
> ★★ **여기서 새로 묻는 것은 넷이다** — **추론된 `T` 를 컴파일러가 말하게 하는 탐침** · **인자 여섯 × 매개변수 꼴 넷 = 24칸 격자** · **추론이 멈추는 다섯 자리** · **인스턴스가 몇 개 생기나**.
> **경계** — 「클래스 템플릿과 CTAD」는 [목록의 **32번 주제**](../32-class-templates-and-ctad/), 「가변 인자 템플릿」은 **34번**, 「인스턴스화와 오류 읽기」는 **35번**, 「컨셉」은 **36번** 주제가 정본이다. 「컴파일 단계 일반」은 [`compiler-pipeline/`](../../../../compiler-pipeline/) 쪽이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★ **타입의 철자** — g++ 는 `int*`·`int [3]`·`long int`, clang 은 `int *`·`int[3]`·`long`((2)(4)) | ★★★ **공백을 지운 뒤의 타입** — 24칸 중 **다른 칸 0**((2)) · **`&`·`*` 가 든 칸의 수** |
> | 진단의 **문구**(`couldn’t deduce` 대 `couldn't infer`) | ★★★ **에러가 나는 줄 · 개수 · `cc exit`** · **기호표의 인스턴스 수**((5)) · **Rust 에러 코드** |

## 한눈에 — 쉽게 말하면

**함수 템플릿의 인자 추론은 「틀에 맞춰 반죽을 누르는 것」이다.**

틀(매개변수 꼴 `T` · `T&` · `const T&` · `T&&`)에 반죽(인자)을 누르면 **틀에 안 들어간 나머지**가 `T` 가 된다.\
**틀이 `T` 하나뿐이면** 반죽은 **납작해진다** — 배열은 포인터로, 함수는 함수 포인터로, 겉의 `const`·참조는 떨어진다.\
**틀에 `&` 가 있으면** 반죽이 **모양 그대로** 들어간다 — 배열의 크기도, `const` 도 남는다.

- **두 반죽이 같은 틀 자리를 다르게 채우면**(`max_of(1, 2.0)`) — 틀이 **어느 쪽도 고르지 않는다**((3)).
- **틀에 반죽을 누를 자리가 없으면**(반환 타입에만 `T`) — **아무것도 채워지지 않는다**((3)).
- **반죽 모양이 다르면 틀이 한 벌씩 더 생긴다** — 인스턴스((5)).

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 틀 | ★★ **매개변수 꼴 `T` · `T&` · `const T&` · `T&&`** | (2) |
| 납작해진다 | ★★★ **값 매개변수 `T` — 배열·함수 감쇠 · `const`·참조 제거** | (2) |
| 모양 그대로 | ★★★ **`T&` — `int[3]` · `const int` 가 남는다** | (2) |
| 틀 자체가 참조가 된다 | ★★★ **`T&&` + lvalue → `T` 가 `int&`** | (2) · 09편 |
| 두 반죽이 다투는 자리 | ★★★ **`deduced conflicting types`** | (3) |
| 누를 자리가 없다 | ★★★ **반환 타입에만 `T` · 중괄호 목록 · `type_identity_t<T>`** | (3) |
| 틀에 이름을 적어 준다 | ★★ **명시 지정 `max_of<double>`** | (4) |
| 틀이 몇 벌 생겼나 | ★★ **인스턴스 1 · 2 · 2**(호출 네 번씩) | (5) |

```text
   인자 : const int ci                  인자 : int arr[3]
   ┌──────────────┬─────────────────┐   ┌──────────────┬─────────────────┐
   │ f(T)         │ T = int         │   │ f(T)         │ T = int*   ★ 감쇠│
   │ f(T&)        │ T = const int   │   │ f(T&)        │ T = int[3] ★ 크기│
   │ f(const T&)  │ T = int         │   │ f(const T&)  │ T = int[3]      │
   │ f(T&&)       │ T = const int&  │   │ f(T&&)       │ T = int(&)[3]   │
   └──────────────┴─────────────────┘   └──────────────┴─────────────────┘
```

## 이 주제가 답하려는 질문

1. ★★★ **추론된 `T` 를 어떻게 보나** — 컴파일러가 **스스로 말하게** 하는 법((1)(2)).
2. ★★★ **인자 모양 × 매개변수 꼴마다 `T` 는 무엇인가** — 감쇠·`const`·참조가 **어느 칸에서** 떨어지나((2)).
3. ★★★ **추론은 어디서 멈추나 — 그때 명시 지정은 무엇을 푸나**((3)(4)).
4. ★★ **호출이 몇 번이면 인스턴스는 몇 개인가**((5)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ② 두 컴파일러에게 「T 가 무엇이냐」를 묻는 것이다

★★★ **이 주제의 본체는 ② 두 컴파일러 대조다** — **추론된 `T` 는 눈에 안 보인다.** 그래서 **컴파일러의 입으로** 듣는다 — 에러로(`static_assert`), 그리고 실행 중 문자열로(`__PRETTY_FUNCTION__`).\
★★ **짝이 ⑥ `<type_traits>` 다** — 탐침 자체가 `std::is_same_v` 이다. **④ 어셈블리 대신 기호표(`nm -C`)** 로 인스턴스를 센다(제5의 상태).

```text
① 다섯 층 표            추론 규칙은 표준 · 타입의 철자는 구현                            (구현 세부사항 절)
② ★ 두 컴파일러 대조     static_assert 진단 · __PRETTY_FUNCTION__ 24칸 · 실패 다섯          (1)(2)(3)
③ ASan                   —                                                                부적용
④ 어셈블리 → 기호표      nm -C 로 인스턴스 1 · 2 · 2                                       (5)
⑤ 경고 격자             —                                                                부적용
⑥ ★ <type_traits>       static_assert(is_same_v<T, void>) 탐침                            (1)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 다섯 층 표 | ★★ **추론 규칙은 표준, `long int` 대 `long` 같은 철자는 구현** | **쓴다** |
| ★★★ **② 두 컴파일러 대조** | ★★★ **본체** — 24칸 중 **다른 칸 0 / 24**(공백을 지운 뒤) · 실패 다섯 줄이 **같은 줄** | **쓴다** |
| ③ ASan | ★ **부적용** — 추론은 **컴파일 때 끝난다.** 실행에 남는 것이 없다(18-B 「잴 것이 없다」) | **안 쓴다** |
| ★★ **④ → 기호표** | ★★ **어셈블리를 볼 필요가 없다** — 인스턴스는 **기호 이름**에 `T` 째 적힌다. 창을 바꿔 답했다(제5의 상태) | **쓴다(바꿔서)** |
| ⑤ 경고 격자 | ★ **부적용** — 격자의 모든 칸이 **경고 0** 으로 컴파일됐다((2) 배너의 `cc exit=0`, 진단 0줄). 추론 결과는 **경고할 일이 아니다** | **안 쓴다** |
| ★★ **⑥ `<type_traits>`** | ★★ **탐침** — `std::is_same_v<T, void>` 가 **일부러 거짓**이 되게 | **쓴다** |

### (1) ★★★ 컴파일러가 `T` 를 말하게 한다 — 일부러 실패하는 `static_assert`

**언제 쓰나** — 「이 호출에서 `T` 가 무엇으로 정해졌나」가 궁금할 때마다.

```cpp
/* tmpl01.cpp */
// 추론된 T 를 컴파일러가 말하게 한다 — 일부러 실패하는 static_assert
#include <type_traits>

template <class T>
void probe(T) {
    static_assert(std::is_same_v<T, void>, "T 를 보여 달라");
}

int main() {
    const int ci = 1;
    probe(ci);
    probe("hi");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic tmpl01.cpp -o ex (cc exit=1) =====
tmpl01.cpp: In instantiation of ‘void probe(T) [with T = int]’:
tmpl01.cpp:11:10:   required from here
tmpl01.cpp:6:24: error: static assertion failed: T 를 보여 달라
    6 |     static_assert(std::is_same_v<T, void>, "T 를 보여 달라");
      |                   ~~~~~^~~~~~~~~~~~~~~~~~
tmpl01.cpp:6:24: note: ‘std::is_same_v<int, void>’ evaluates to false
tmpl01.cpp: In instantiation of ‘void probe(T) [with T = const char*]’:
tmpl01.cpp:12:10:   required from here
tmpl01.cpp:6:24: error: static assertion failed: T 를 보여 달라
tmpl01.cpp:6:24: note: ‘std::is_same_v<const char*, void>’ evaluates to false
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic tmpl01.cpp -o ex (cc exit=1) =====
tmpl01.cpp:6:19: error: static assertion failed due to requirement 'std::is_same_v<int, void>': T 를 보여 달라
    6 |     static_assert(std::is_same_v<T, void>, "T 를 보여 달라");
      |                   ^~~~~~~~~~~~~~~~~~~~~~~
tmpl01.cpp:11:5: note: in instantiation of function template specialization 'probe<int>' requested here
   11 |     probe(ci);
      |     ^
tmpl01.cpp:6:19: error: static assertion failed due to requirement 'std::is_same_v<const char *, void>': T 를 보여 달라
    6 |     static_assert(std::is_same_v<T, void>, "T 를 보여 달라");
      |                   ^~~~~~~~~~~~~~~~~~~~~~~
tmpl01.cpp:12:5: note: in instantiation of function template specialization 'probe<const char *>' requested here
   12 |     probe("hi");
      |     ^
2 errors generated.
```

- ★★★ **g++ 는 `In instantiation of ‘void probe(T) [with T = int]’` 와 `note: ‘std::is_same_v<int, void>’ evaluates to false`** 로, **clang 은 `due to requirement 'std::is_same_v<int, void>'` 와 `'probe<int>' requested here`** 로 — **`T` 를 에러에 적어 준다.**
- ★★★ **`const int ci` 를 넘겼는데 `T = int`** · **`"hi"` 를 넘겼는데 `T = const char*`** — 값 매개변수는 **최상위 `const` 를 떨어뜨리고 배열을 감쇠시킨다**(05편 (1)(4)의 `auto` 와 **같은 규칙**).
- ★★ **같은 원리의 탐침이 TS 갈래에도 있다** — [TS 21번](../../../ts/syntax/21-inference-control-const-and-noinfer/)의 `const probe: null = 무엇인가;` 는 **일부러 틀린 주석으로** 컴파일러가 추론된 타입을 에러에 적게 한다. 05·09편은 **정의 없는 `TypeOf<T>`** 로 같은 일을 했다.
- ★ 에러 수 — g++ **2** · clang **2**(`2 errors generated.`). **호출 두 번 = 인스턴스 둘 = 에러 둘**이다.

### (2) ★★★ 추론 격자 — 인자 여섯 × 매개변수 꼴 넷

**언제 쓰나** — 템플릿 매개변수를 `T` · `T&` · `const T&` · `T&&` 중 무엇으로 받을지 정할 때.\
★ (1)의 탐침은 **한 칸에 에러 하나**라 24칸을 한 번에 못 본다. 그래서 **같은 질문을 실행 중 문자열로** 물었다 — `__PRETTY_FUNCTION__` 은 **컴파일러가 채운 함수 이름**이라 **`T` 를 컴파일러가 말한 그대로** 담는다.

```cpp
/* tmpl02.cpp */
// 인자 여섯 × 매개변수 꼴 넷 — 추론된 T 를 컴파일러의 __PRETTY_FUNCTION__ 에서 잘라 찍는다
#include <cstdio>
#include <cstring>

template <class T>
const char* name_of() { return __PRETTY_FUNCTION__; }

// __PRETTY_FUNCTION__ 에서 「T = 」 뒤부터 마지막 「]」 앞까지만 찍는다
void print_T(const char* pf) {
    const char* s = std::strstr(pf, "T = ") + 4;
    const char* e = std::strrchr(pf, ']');
    std::printf("%-22.*s", (int)(e - s), s);
}

template <class T> void by_value(T)       { print_T(name_of<T>()); }
template <class T> void by_ref(T&)        { print_T(name_of<T>()); }
template <class T> void by_cref(const T&) { print_T(name_of<T>()); }
template <class T> void by_fwd(T&&)       { print_T(name_of<T>()); }

void func(int) {}

#define ROW(label, arg)                                    \
    std::printf("%-18s", label);                           \
    by_value(arg); by_ref(arg); by_cref(arg); by_fwd(arg); \
    std::printf("\n");

int main() {
    int arr[3] = {};
    const int ci = 1;
    int i = 2;
    int& ri = i;
    const int& cri = i;
    std::printf("%-18s%-22s%-22s%-22s%-22s\n", "arg", "T", "T&", "const T&", "T&&");
    ROW("int arr[3]", arr)
    ROW("const int ci", ci)
    ROW("int& ri", ri)
    ROW("const int& cri", cri)
    ROW("\"hi\"", "hi")
    ROW("void func(int)", func)
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic tmpl02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
arg               T                     T&                    const T&              T&&                   
int arr[3]        int*                  int [3]               int [3]               int (&)[3]            
const int ci      int                   const int             int                   const int&            
int& ri           int                   int                   int                   int&                  
const int& cri    int                   const int             int                   const int&            
"hi"              const char*           const char [3]        char [3]              const char (&)[3]     
void func(int)    void (*)(int)         void(int)             void(int)             void (&)(int)         
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic tmpl02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
arg               T                     T&                    const T&              T&&                   
int arr[3]        int *                 int[3]                int[3]                int (&)[3]            
const int ci      int                   const int             int                   const int &           
int& ri           int                   int                   int                   int &                 
const int& cri    int                   const int             int                   const int &           
"hi"              const char *          const char[3]         char[3]               const char (&)[3]     
void func(int)    void (*)(int)         void (int)            void (int)            void (&)(int)         
```

```bash
# tmpl-grid.sh
# tmpl-grid.sh — 같은 격자를 두 컴파일러로 찍고, 공백을 지운 뒤 칸마다 견준다
g++ -std=c++20 -Wall -Wextra -pedantic tmpl02.cpp -o gx && ./gx | tail -n +2 > g.txt
clang++ -std=c++20 -Wall -Wextra -pedantic tmpl02.cpp -o cx && ./cx | tail -n +2 > c.txt
cells() { while IFS= read -r line; do for i in 0 1 2 3; do printf '%s\n' "${line:$((18+22*i)):22}" | tr -d ' '; done; done < "$1"; }
paste -d'|' <(cells g.txt) <(cells c.txt) > both.txt
total=$(wc -l < both.txt)
differ=$(awk -F'|' '$1 != $2' both.txt | wc -l)
ref=$(cut -d'|' -f1 both.txt | grep -c '&')
ptr=$(cut -d'|' -f1 both.txt | grep -c '\*')
echo "두 컴파일러가 다른 T 를 낸 칸 $differ / $total"
echo "T 에 & 가 들어간 칸 $ref / $total · T 에 * 가 생긴 칸 $ptr / $total"
rm -f gx cx g.txt c.txt both.txt
```

```text
===== bash tmpl-grid.sh (exit=0) =====
두 컴파일러가 다른 T 를 낸 칸 0 / 24
T 에 & 가 들어간 칸 6 / 24 · T 에 * 가 생긴 칸 3 / 24
```

- ★★★ **두 컴파일러가 다른 `T` 를 낸 칸 0 / 24** — 공백을 지우면 **한 글자도 같다.** 철자만 다르다(`int*` 대 `int *` · `int [3]` 대 `int[3]` · `void(int)` 대 `void (int)`).
- ★★★ **`T` 열(값) — 감쇠가 일어난다**: `int arr[3]` → **`int*`**, `"hi"` → **`const char*`**, `func` → **`void (*)(int)`** — **`*` 가 생긴 칸 3** 이 전부 이 열이다. 그리고 `const int`·`int&`·`const int&` 가 전부 **`int`**(최상위 `const` 와 참조가 떨어진다).
- ★★★ **`T&` 열 — 감쇠가 없다**: `int[3]` · `const char[3]` · `void(int)` 가 **모양 그대로**. **`const int` 인자는 `T = const int`** — `const` 가 **`T` 안으로** 들어간다(그래서 `T&` 로 `const` 를 못 벗긴다).
- ★★ **`const T&` 열 — `const` 는 틀이 가져가고 `T` 에는 안 남는다**: `const int ci` → **`int`**, `"hi"` → **`char[3]`**(`const char[3]` 의 `const` 를 틀이 먹었다).
- ★★★ **`T&&` 열 — 여섯 인자가 전부 lvalue 라 `T` 가 참조가 된다**: `int (&)[3]` · `const int&` · `int&` · `const char (&)[3]` · `void (&)(int)` — **`&` 가 든 칸 6** 이 전부 이 열이다(09편 (6)의 참조 축약).
- ★ **컴파일은 두 컴파일러 다 `cc exit=0` · 진단 0줄** — 24칸 모두 **합법적인 추론**이다(⑤ 경고 격자가 부적용인 근거).

```text
                    T              T&               const T&        T&&
   int arr[3]       int*   ★감쇠   int[3]           int[3]          int(&)[3]      ★참조
   const int ci     int    ★const  const int        int             const int&
   int& ri          int    ★참조   int              int             int&
   const int& cri   int            const int        int             const int&
   "hi"             const char*    const char[3]    char[3]         const char(&)[3]
   void func(int)   void(*)(int)   void(int)        void(int)       void(&)(int)
   ★ T 열만 감쇠 · 참조와 최상위 const 가 떨어진다      ★ T&& 열만 T 가 참조
```

### (3) ★★★ 추론이 멈추는 다섯 자리

**언제 쓰나** — `no matching function for call` 을 만났을 때 **무엇이 모자랐나**를 가를 때.

```cpp
/* tmpl03.cpp */
// 다섯 호출 — 각각 T 를 추론할 수 있나
#include <initializer_list>
#include <type_traits>

template <class T> T max_of(T a, T b) { return a < b ? b : a; }
template <class T> T make() { return T{}; }
template <class T> void take(T) {}
template <class T> void exact(std::type_identity_t<T>) {}

int main() {
    max_of(1, 2.0);          // 1. int 와 double
    make();                  // 2. 인자 없이
    take({1, 2, 3});         // 3. 중괄호 목록
    exact(1);                // 4. type_identity_t<T> 매개변수
    int n = make();          // 5. int 변수로 받는다
    (void)n;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 tmpl03.cpp -o ex (cc exit=1) =====
tmpl03.cpp: In function ‘int main()’:
tmpl03.cpp:11:11: error: no matching function for call to ‘max_of(int, double)’
   11 |     max_of(1, 2.0);          // 1. int 와 double
      |     ~~~~~~^~~~~~~~
tmpl03.cpp:5:22: note: candidate: ‘template<class T> T max_of(T, T)’
    5 | template <class T> T max_of(T a, T b) { return a < b ? b : a; }
      |                      ^~~~~~
tmpl03.cpp:5:22: note:   template argument deduction/substitution failed:
tmpl03.cpp:11:11: note:   deduced conflicting types for parameter ‘T’ (‘int’ and ‘double’)
   11 |     max_of(1, 2.0);          // 1. int 와 double
      |     ~~~~~~^~~~~~~~
tmpl03.cpp:12:9: error: no matching function for call to ‘make()’
   12 |     make();                  // 2. 인자 없이
      |     ~~~~^~
tmpl03.cpp:6:22: note: candidate: ‘template<class T> T make()’
    6 | template <class T> T make() { return T{}; }
      |                      ^~~~
tmpl03.cpp:6:22: note:   template argument deduction/substitution failed:
tmpl03.cpp:12:9: note:   couldn’t deduce template parameter ‘T’
   12 |     make();                  // 2. 인자 없이
      |     ~~~~^~
tmpl03.cpp:13:9: error: no matching function for call to ‘take(<brace-enclosed initializer list>)’
   13 |     take({1, 2, 3});         // 3. 중괄호 목록
      |     ~~~~^~~~~~~~~~~
tmpl03.cpp:7:25: note: candidate: ‘template<class T> void take(T)’
    7 | template <class T> void take(T) {}
      |                         ^~~~
tmpl03.cpp:7:25: note:   template argument deduction/substitution failed:
tmpl03.cpp:13:9: note:   couldn’t deduce template parameter ‘T’
   13 |     take({1, 2, 3});         // 3. 중괄호 목록
      |     ~~~~^~~~~~~~~~~
tmpl03.cpp:14:10: error: no matching function for call to ‘exact(int)’
   14 |     exact(1);                // 4. type_identity_t<T> 매개변수
      |     ~~~~~^~~
tmpl03.cpp:8:25: note: candidate: ‘template<class T> void exact(std::type_identity_t<T>)’
    8 | template <class T> void exact(std::type_identity_t<T>) {}
      |                         ^~~~~
tmpl03.cpp:8:25: note:   template argument deduction/substitution failed:
tmpl03.cpp:14:10: note:   couldn’t deduce template parameter ‘T’
   14 |     exact(1);                // 4. type_identity_t<T> 매개변수
      |     ~~~~~^~~
tmpl03.cpp:15:17: error: no matching function for call to ‘make()’
   15 |     int n = make();          // 5. int 변수로 받는다
      |             ~~~~^~
tmpl03.cpp:6:22: note: candidate: ‘template<class T> T make()’
    6 | template <class T> T make() { return T{}; }
      |                      ^~~~
tmpl03.cpp:6:22: note:   template argument deduction/substitution failed:
tmpl03.cpp:15:17: note:   couldn’t deduce template parameter ‘T’
   15 |     int n = make();          // 5. int 변수로 받는다
      |             ~~~~^~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 tmpl03.cpp -o ex (cc exit=1) =====
tmpl03.cpp:11:5: error: no matching function for call to 'max_of'
   11 |     max_of(1, 2.0);          // 1. int 와 double
      |     ^~~~~~
tmpl03.cpp:5:22: note: candidate template ignored: deduced conflicting types for parameter 'T' ('int' vs. 'double')
    5 | template <class T> T max_of(T a, T b) { return a < b ? b : a; }
      |                      ^
tmpl03.cpp:12:5: error: no matching function for call to 'make'
   12 |     make();                  // 2. 인자 없이
      |     ^~~~
tmpl03.cpp:6:22: note: candidate template ignored: couldn't infer template argument 'T'
    6 | template <class T> T make() { return T{}; }
      |                      ^
tmpl03.cpp:13:5: error: no matching function for call to 'take'
   13 |     take({1, 2, 3});         // 3. 중괄호 목록
      |     ^~~~
tmpl03.cpp:7:25: note: candidate template ignored: couldn't infer template argument 'T'
    7 | template <class T> void take(T) {}
      |                         ^
tmpl03.cpp:14:5: error: no matching function for call to 'exact'
   14 |     exact(1);                // 4. type_identity_t<T> 매개변수
      |     ^~~~~
tmpl03.cpp:8:25: note: candidate template ignored: couldn't infer template argument 'T'
    8 | template <class T> void exact(std::type_identity_t<T>) {}
      |                         ^
tmpl03.cpp:15:13: error: no matching function for call to 'make'
   15 |     int n = make();          // 5. int 변수로 받는다
      |             ^~~~
tmpl03.cpp:6:22: note: candidate template ignored: couldn't infer template argument 'T'
    6 | template <class T> T make() { return T{}; }
      |                      ^
5 errors generated.
```

- ★★★ **다섯 줄 전부 에러 · 두 컴파일러가 같은 줄** — g++ **5** · clang **5**(`5 errors generated.`).
- ★★★ **1. `max_of(1, 2.0)` — `deduced conflicting types for parameter ‘T’ (‘int’ and ‘double’)`**(clang 은 `'int' vs. 'double'`). **두 인자가 같은 `T` 를 다르게 말하면 추론은 어느 쪽도 고르지 않는다** — `int` 를 `double` 로 올려 주는 변환은 **추론 단계에서는 없다**(01편의 오버로드 해석과 다른 점).
- ★★★ **2. `make()` · 5. `int n = make();` — `couldn’t deduce template parameter ‘T’`**. **`T` 가 반환 타입에만 있으면 추론할 재료가 없다** — ★★ **받는 변수의 타입(5.)도 재료가 되지 않는다.** 추론은 **인자에서만** 한다.
- ★★ **3. `take({1, 2, 3})`** — **중괄호 목록은 `T` 로 추론되지 않는다.** (4)에서 보듯 **`auto` 는 같은 것을 `initializer_list<int>` 로 받는다** — **`auto` 와 템플릿 추론이 갈리는 자리**다(이 문서는 둘이 갈리는 자리를 **이 하나만** 던졌다).
- ★★ **4. `exact(1)` — `std::type_identity_t<T>` 는 추론하지 않는 자리**(비추론 문맥)다. **일부러 추론을 끄는 도구**로 쓴다 — 다른 매개변수가 `T` 를 정하게 하고 이 매개변수는 **변환만** 받게.

```text
   추론의 재료                      쓰이나
   인자의 타입 (1, 2.0)             O   ── 둘이 다르게 말하면 실패 (1.)
   반환 타입  T make()              ×   (2.)
   받는 변수  int n = make();       ×   (5.)  ── Rust 는 O
   중괄호 목록 {1, 2, 3}             ×   (3.)  ── auto 는 initializer_list
   type_identity_t<T>               ×   (4.)  ── 일부러 끈 자리
```

### (4) ★★ 명시 지정 — 같은 호출에 `T` 를 적어 주면

**언제 쓰나** — (3)의 다섯 자리를 풀 때.

```cpp
/* tmpl04.cpp */
// 같은 네 호출에 T 를 직접 적는다 — 그리고 auto 는 중괄호 목록을 무엇으로 받나
#include <cstdio>
#include <cstring>
#include <initializer_list>
#include <type_traits>

template <class T>
const char* name_of() { return __PRETTY_FUNCTION__; }

void print_T(const char* label, const char* pf) {
    const char* s = std::strstr(pf, "T = ") + 4;
    const char* e = std::strrchr(pf, ']');
    std::printf("%-44s %.*s\n", label, (int)(e - s), s);
}

template <class T> T max_of(T a, T b) { return a < b ? b : a; }
template <class T> T make() { return T{}; }
template <class T> void take(T) { print_T("  T inside take", name_of<T>()); }
template <class T> void exact(std::type_identity_t<T>) { print_T("  T inside exact", name_of<T>()); }

int main() {
    std::printf("max_of<double>(1, 2.0) = %.1f\n", max_of<double>(1, 2.0));
    std::printf("make<int>() = %d\n", make<int>());
    std::printf("take<std::initializer_list<int>>({1, 2, 3})\n");
    take<std::initializer_list<int>>({1, 2, 3});
    std::printf("exact<long>(1)\n");
    exact<long>(1);
    auto il = {1, 2, 3};
    print_T("auto il = {1, 2, 3};  decltype(il)", name_of<decltype(il)>());
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic tmpl04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
max_of<double>(1, 2.0) = 2.0
make<int>() = 0
take<std::initializer_list<int>>({1, 2, 3})
  T inside take                              std::initializer_list<int>
exact<long>(1)
  T inside exact                             long int
auto il = {1, 2, 3};  decltype(il)           std::initializer_list<int>
===== clang++ -std=c++20 -Wall -Wextra -pedantic tmpl04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
max_of<double>(1, 2.0) = 2.0
make<int>() = 0
take<std::initializer_list<int>>({1, 2, 3})
  T inside take                              std::initializer_list<int>
exact<long>(1)
  T inside exact                             long
auto il = {1, 2, 3};  decltype(il)           std::initializer_list<int>
```

- ★★★ **`max_of<double>(1, 2.0)` = 2.0 · `make<int>()` = 0 · `take<std::initializer_list<int>>` · `exact<long>(1)`** — 네 줄 전부 **두 컴파일러에서 통과**한다. **`T` 를 적으면 추론할 것이 없다** — `1` 은 **변환**으로 `double`·`long` 이 된다.
- ★★★ **`auto il = {1, 2, 3};` 은 `std::initializer_list<int>`** — (3)의 3. 과 같은 중괄호 목록을 **`auto` 는 받는다.**
- ★★ **`exact<long>` 의 `T` 를 g++ 는 `long int`, clang 은 `long` 으로 적는다** — 같은 타입의 **다른 철자**다(흔들리는 칸).

### (5) ★★ 인스턴스는 몇 개인가 — 기호표로 센다

**언제 쓰나** — 「호출마다 함수가 한 벌씩 생긴다」를 의심할 때.

```cpp
/* tmpl05.cpp */
// 네 인자로 세 함수 템플릿을 부른다 — 인스턴스는 몇 개 생기나
template <class T> void by_value(T) {}
template <class T> void by_ref(T&) {}
template <class T> void by_fwd(T&&) {}

void call_all() {
    int i = 0;
    const int ci = 0;
    int& ri = i;
    const int& cri = i;
    by_value(i); by_value(ci); by_value(ri); by_value(cri);
    by_ref(i);   by_ref(ci);   by_ref(ri);   by_ref(cri);
    by_fwd(i);   by_fwd(ci);   by_fwd(ri);   by_fwd(cri);
}
```

```bash
# tmpl-inst.sh
# tmpl-inst.sh — 오브젝트 파일의 기호표에서 템플릿마다 인스턴스를 센다
for c in g++ clang++; do
  $c -std=c++20 -c tmpl05.cpp -o t5.o
  printf '%-8s by_value %d개 · by_ref %d개 · by_fwd %d개\n' "$c" \
    "$(nm -C t5.o | grep -c ' by_value<')" "$(nm -C t5.o | grep -c ' by_ref<')" "$(nm -C t5.o | grep -c ' by_fwd<')"
done
nm -C t5.o | grep -E ' W ' | sed 's/^0*//' | sort
rm -f t5.o
```

```text
===== bash tmpl-inst.sh (exit=0) =====
g++      by_value 1개 · by_ref 2개 · by_fwd 2개
clang++  by_value 1개 · by_ref 2개 · by_fwd 2개
 W void by_fwd<int const&>(int const&)
 W void by_fwd<int&>(int&)
 W void by_ref<int const>(int const&)
 W void by_ref<int>(int&)
 W void by_value<int>(int)
```

- ★★★ **호출 네 번씩인데 인스턴스는 `by_value` 1 · `by_ref` 2 · `by_fwd` 2** — 두 컴파일러 같다.
- ★★★ **값 매개변수는 네 인자를 전부 `T = int` 로 만들어 한 벌** — (2)의 `T` 열이 「`const`·참조가 떨어진다」였던 것이 **바이너리 크기**로 드러난다.
- ★★ **`by_ref` 는 `int` · `int const` 두 벌**(`const` 가 `T` 에 남는다) · **`by_fwd` 는 `int&` · `int const&` 두 벌**(lvalue 넷이 두 모양).
- ★ **기호 이름에 `T` 가 박힌다**(`by_ref<int const>`) — 어셈블리를 볼 필요가 없었다. 인스턴스 수와 코드 크기의 관계는 Rust 갈래 [31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/) (8)이 셌다.

### (6) ★★ Rust 와 나란히 — 같은 두 실패, 한쪽은 풀린다

**언제 쓰나** — 「반환 타입으로 추론하는 언어는 없나」를 물을 때.

```rust
// infer.rs
// C++ 에서 추론이 멈춘 두 자리를 Rust 로 — --cfg 로 하나씩 켠다(mixed · bare). 아무것도 안 켜면 타입을 적은 판
fn max_of<T: PartialOrd>(a: T, b: T) -> T {
    if a < b { b } else { a }
}

fn make<T: Default>() -> T {
    T::default()
}

fn main() {
    #[cfg(mixed)]
    let m = max_of(1, 2.0);
    #[cfg(bare)]
    let m = make();
    #[cfg(not(any(mixed, bare)))]
    let m: i64 = make();
    #[cfg(not(any(mixed, bare)))]
    println!("make() -> {} · max_of(1, 2) -> {}", m, max_of(1, 2));
    #[cfg(any(mixed, bare))]
    let _ = m;
}
```

```text
===== rustc --edition 2021 --cfg mixed infer.rs -o irx (cc exit=1) =====
error[E0308]: mismatched types
  --> infer.rs:12:23
   |
12 |     let m = max_of(1, 2.0);
   |             ------ -  ^^^ expected integer, found floating-point number
   |             |      |
   |             |      expected all arguments to be this integer type because they need to match the type of this parameter
   |             arguments to this function are incorrect
   |
help: the return type of this call is `{float}` due to the type of the argument passed
  --> infer.rs:12:13
   |
12 |     let m = max_of(1, 2.0);
   |             ^^^^^^^^^^---^
   |                       |
   |                       this argument influences the return type of `max_of`
note: function defined here
  --> infer.rs:2:4
   |
 2 | fn max_of<T: PartialOrd>(a: T, b: T) -> T {
   |    ^^^^^^ -              ----  ---- this parameter needs to match the integer type of `a`
   |           |              |
   |           |              `b` needs to match the integer type of this parameter
   |           `a` and `b` both reference this parameter `T`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

```text
===== rustc --edition 2021 --cfg bare infer.rs -o irx (cc exit=1) =====
error[E0283]: type annotations needed
  --> infer.rs:14:9
   |
14 |     let m = make();
   |         ^   ------ type must be known at this point
   |
   = note: cannot satisfy `_: Default`
note: required by a bound in `make`
  --> infer.rs:6:12
   |
 6 | fn make<T: Default>() -> T {
   |            ^^^^^^^ required by this bound in `make`
help: consider giving `m` an explicit type
   |
14 |     let m: /* Type */ = make();
   |          ++++++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0283`.
```

```text
===== rustc --edition 2021 infer.rs -o irx && ./irx (cc exit=0 · run exit=0) =====
make() -> 0 · max_of(1, 2) -> 2
```

- ★★ **`max_of(1, 2.0)` 은 Rust 도 에러(`E0308`)** — 「`a` 와 `b` 가 같은 `T` 를 가리킨다」를 **그림으로** 그려 준다.
- ★★ **`let m = make();` 도 에러(`E0283` · `type annotations needed`)** — 여기까지는 C++ 과 같다.
- ★★★ **그런데 `let m: i64 = make();` 는 통과한다**(`make() -> 0`) — **Rust 는 받는 쪽의 타입에서 `T` 를 추론한다.** C++ 은 (3)의 5. `int n = make();` 가 **에러**였다.\
  ★ C++ 의 추론은 **호출의 인자에서만**, Rust 의 추론은 **식 전체(받는 자리 포함)에서** 한다 — 이 한 블록이 보인 차이다.

## 문법 — 형태와 규칙

### 형태

```text
   template <class T> void f(T x);          값 — 감쇠 · 최상위 const·참조 제거
   template <class T> void f(T& x);         lvalue 만 · 모양 그대로(const 가 T 에 남는다)
   template <class T> void f(const T& x);   무엇이든 · const 는 틀이 가져간다
   template <class T> void f(T&& x);        전달 참조 · lvalue 면 T 가 참조 (09편)
   f<double>(1);                            명시 지정 — 추론하지 않는다
   template <class T> void g(std::type_identity_t<T> x);   비추론 문맥 — 일부러 끈다
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (2)\~(4)가 **실행한 소스**로 보였다.

### 규칙

- ★★★ **값 매개변수는 인자를 납작하게** — 배열·함수 감쇠, 최상위 `const`·참조 제거((2)).
- ★★★ **참조 매개변수는 모양을 지킨다** — 배열 크기를 알고 싶으면 `T&`/`const T&`((2)).
- ★★★ **추론은 인자에서만** — 반환 타입·받는 변수는 재료가 아니다. 명시 지정으로 푼다((3)(4)).
- ★★ **같은 `T` 를 두 인자가 다르게 말하면 실패** — 변환은 추론 뒤의 일이다((3)).
- ★★ **중괄호 목록은 `T` 로 추론되지 않는다** — `initializer_list<T>` 로 받거나 명시한다((3)(4)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | g++ 진단 | clang 진단 | 어디서 |
|---|---|---|---|
| `max_of(1, 2.0)` | `deduced conflicting types` | `deduced conflicting types` | (3) 11행 |
| `make()` · `int n = make();` | `couldn’t deduce template parameter` | `couldn't infer template argument` | (3) 12 · 15행 |
| `take({1, 2, 3})` | `couldn’t deduce template parameter` | `couldn't infer template argument` | (3) 13행 |
| `exact(1)` | `couldn’t deduce template parameter` | `couldn't infer template argument` | (3) 14행 |

## 어디서 틀리나

### 1. ★★★ 「`T` 는 인자의 타입 그대로다」

(2)가 반증이다 — **`T` 열에서 `const int`·`int&`·`const int&` 가 전부 `int`**, 배열은 `int*` 다.

### 2. ★★★ 「`const T&` 로 받으면 `T` 에 `const` 가 들어간다」

(2)가 반증이다 — **`const int ci` 를 넣어도 `T = int`** · `"hi"` 는 **`char[3]`**. `const` 는 **틀이** 갖는다. `T&` 일 때만 `T` 에 남는다.

### 3. ★★★ 「`max_of(1, 2.0)` 은 `double` 로 맞춰 준다」

(3)이 반증이다 — **`deduced conflicting types`**. 일반 함수라면 변환이 되지만 **추론은 변환하지 않는다.**

### 4. ★★★ 「`int n = make();` 처럼 받는 타입을 적으면 추론된다」

(3)의 5. 가 반증이다 — **C++ 은 에러**다. Rust 는 된다((6)).

### 5. ★★ 「`auto` 와 템플릿 추론은 완전히 같다」

(3)(4)가 반증이다 — **중괄호 목록**에서 `auto` 는 `initializer_list<int>`, 템플릿은 **실패**.

### 6. ★★ 「호출마다 인스턴스가 하나씩 생긴다」

(5)가 반증이다 — **호출 넷에 `by_value` 는 한 벌.** 인스턴스는 **`T` 가 다를 때만** 생긴다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제는 거의 전부 「표준」 칸이다** — 추론 규칙은 **컴파일 때 끝나는 약속**이라 두 컴파일러가 **24칸 전부 같은 `T`** 를 냈다. **갈린 것은 철자뿐**이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **24칸의 `T`**((2)) · **추론이 멈추는 다섯 자리**((3)) · **명시 지정이 추론을 대신함**((4)) · **`auto x = {…}` 는 `initializer_list`**((4)) · **`T` 가 같으면 인스턴스 하나**((5)) | 컴파일러가 말한 `T` · 에러 줄 · 기호표 | ★ **실패가 「추론 실패」인지 「오버로드 없음」인지**는 문구로만 갈린다(둘 다 `no matching function`) |
| **조건부 표준** | 특정 판에서만 | ★ **`std::type_identity_t` 는 C++20**((3)) — 이 문서는 판을 바꿔 던지지 않았다 | — | — |
| **구현 정의** | 문서화 의무 | ★★ **`__PRETTY_FUNCTION__` 의 모양과 타입의 철자**(`long int` 대 `long` · 공백)((2)(4)) — ★ `__PRETTY_FUNCTION__` 자체가 **표준이 아니라 두 컴파일러의 확장**이다 | 두 컴파일러 출력 | ★★ **철자 차이를 규칙 차이로 읽기 쉽다** — 공백을 지워 견줘야 한다 |
| **미명시** | 몇 가지 중 하나 | ★ 이 주제에는 **해당하는 결론이 없다** | — | — |
| **UB** | 아무 일이나 | ★ **이 주제의 코드는 UB 가 없다** — 추론은 컴파일 때 끝난다 | — | — |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ 컴파일러 | clang 컴파일러 | 실행 도구 |
|---|---|---|---|---|
| ★★★ **값 매개변수가 배열 크기를 잃는다** | 표준(허용된 코드) | ★★★ **경고 0** | ★★★ **경고 0** | 부적용 |
| ★★ **`const T&` 가 `T` 에서 `const` 를 벗긴다** | 표준 | **경고 0** | **경고 0** | 부적용 |
| ★★★ **추론 실패** | ill-formed | ★★★ **에러** | ★★★ **에러** | — |

- ★★ **이 표의 결론** — **추론이 「성공한 결과」가 기대와 다를 때는 아무도 말해 주지 않는다**(배열이 포인터가 된 것 · `const` 가 빠진 것). **실패는 에러로 크게 나고, 뜻밖의 성공은 조용하다.** 그래서 (1)의 탐침이 필요하다.

### ★ 종료 코드 0인데 ill-formed — 이 편에서는 못 찾았다

- ★ 추론이 실패한 다섯 줄은 **두 컴파일러 다 `cc exit=1`** 이었다 — 조용히 통과한 ill-formed 는 **없었다.**
- ★ 가까운 자리 — `__PRETTY_FUNCTION__` 은 **표준 식별자가 아닌데** `-pedantic` 에서도 **경고 0** 으로 통과했다. 그러나 이것은 **ill-formed 가 아니라 구현이 미리 정의한 이름**을 쓴 것이다(구현 정의 칸).

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 작은 값을 받는다 · 복사해도 된다 | ★★ **`T`** | 인스턴스가 적다((5)) — 단 배열 크기는 잃는다 |
| 읽기만 하고 무엇이든 받는다 | ★★★ **`const T&`** | 임시도 받고 `const` 를 틀이 가져간다((2)) |
| 배열의 크기를 알아야 한다 | ★★★ **`T&` 또는 `const T&`**(또는 `std::span`) | `int[3]` 이 남는다((2)) |
| 받은 것을 그대로 넘긴다 | ★★ **`T&&` + `std::forward<T>`** | 09편 |
| 두 인자의 타입이 다를 수 있다 | ★★ **명시 지정** 또는 **매개변수 둘(`T`, `U`)** | (3)(4) — 뒤쪽은 이 문서가 던지지 않았다 |
| `T` 가 반환에만 있다 | ★★★ **명시 지정**(`make<int>()`) | (3)(4) |
| 한 매개변수만 추론에서 빼고 싶다 | ★ **`std::type_identity_t<T>`** | (3)(4) |

## 핵심 문장

- ★★★ **추론된 `T` 는 컴파일러에게 말하게 한다** — `static_assert(std::is_same_v<T, void>)` 가 **에러에 `T` 를 적는다**(두 컴파일러).
- ★★★ **인자 여섯 × 꼴 넷 = 24칸에서 두 컴파일러가 다른 `T` 를 낸 칸은 0** — **`T` 열만 감쇠(`*` 3칸)**, **`T&&` 열만 `T` 가 참조(`&` 6칸)**.
- ★★★ **`T&` 는 `const` 를 `T` 에 남기고, `const T&` 는 틀이 가져간다** — `const int` 가 각각 `const int` · `int`.
- ★★★ **추론은 인자에서만** — 충돌(`1, 2.0`) · 반환 타입 · 받는 변수 · 중괄호 목록 · `type_identity_t` 에서 멈추고, **명시 지정**이 푼다.
- ★★ **인스턴스는 `T` 가 다를 때만** — 호출 넷에 `by_value` 1 · `by_ref` 2 · `by_fwd` 2.
- ★★ **Rust 는 받는 쪽 타입(`let m: i64`)에서도 추론한다** — C++ 은 같은 자리가 에러다.

## 관련 자료

- [05번](../05-auto-and-decltype-type-deduction/) — ★★★ **이 편의 앞 절반.** `auto` 의 감쇠·`const` 제거와 **같은 규칙**이 (2)의 `T` 열이다. (9) 축약 템플릿.
- [09번](../09-rvalue-references-move-and-forward/) (6) — 전달 참조와 참조 축약 — (2)의 `T&&` 열.
- [08번](../08-value-categories-lvalue-prvalue-xvalue/) — lvalue·rvalue — `T&&` 열이 전부 참조인 이유(인자가 전부 lvalue).
- [01번](../01-function-overloading-and-overload-resolution/) — 오버로드 해석의 변환 순서 — 추론은 **그 앞 단계**라 변환을 모른다((3)).
- [TS 21번](../../../ts/syntax/21-inference-control-const-and-noinfer/) — `const probe: null` 탐침 — (1)과 같은 원리.
- Rust 갈래 [31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/) — 경계·단형화, C++ 템플릿의 인스턴스화 시점 검사.
- [목록의 **32번 주제**](../32-class-templates-and-ctad/)(클래스 템플릿과 CTAD) · [목록의 **34번 주제**](../34-variadic-templates-and-pack-expansion/)(가변 인자) · [목록의 **35번 주제**](../35-instantiation-header-placement-and-reading-errors/)(인스턴스화와 오류 읽기) · [목록의 **36번 주제**](../36-concepts-and-requires/)(컨셉).

## 용어 풀이

> **템플릿 인자 추론(template argument deduction)** — 함수 템플릿을 부를 때 **인자의 타입에서 `T` 를 정하는** 과정.\
> 예: (2)의 24칸.

> **감쇠(decay)** — 배열이 첫 원소 포인터로, 함수가 함수 포인터로 바뀌는 것. **값 매개변수 `T` 에서** 일어난다.\
> 예: (2)의 `int*` · `void (*)(int)`.

> **전달 참조(forwarding reference)** — 추론되는 `T` 에 붙은 `T&&`. lvalue 를 받으면 `T` 가 참조가 된다.\
> 예: (2)의 `T&&` 열 · 09편 (6).

> **비추론 문맥(non-deduced context)** — 그 매개변수로는 `T` 를 정하지 않는 자리. `type_identity_t<T>` 가 대표다.\
> 예: (3)의 4.

> **명시적 템플릿 인자(explicit template argument)** — `f<double>(…)` 처럼 `T` 를 직접 적는 것. 적힌 자리는 추론하지 않는다.\
> 예: (4).

> **`__PRETTY_FUNCTION__`** — g++·clang 이 함수 안에서 정의해 주는 **함수 서명 문자열**(템플릿 인자 포함). **표준이 아니라 확장**이다.\
> 예: (2)의 격자.

> **인스턴스(instantiation)** — 템플릿에 구체 `T` 를 넣어 만든 **실제 함수 한 벌**. 기호표에 `T` 째 이름이 남는다.\
> 예: (5)의 `by_ref<int const>`.

## 더 들어가면

- **부분 순서(partial ordering)** — 여러 함수 템플릿이 다 맞을 때 **더 특수한 것**을 고르는 규칙. 이 문서는 던지지 않았다.
- **기본 템플릿 인자 · 매개변수 둘(`T`, `U`)** — `max_of` 를 `template <class T, class U>` 로 만들면 (3)의 1. 이 풀린다 — 대신 **반환 타입을 무엇으로 할지**가 새 문제가 된다. 이 문서는 던지지 않았다.
- **C++17 CTAD** — 클래스 템플릿도 생성자 인자로 추론한다. [목록의 **32번 주제**](../32-class-templates-and-ctad/)의 정본.
- **C++20 컨셉으로 추론 결과를 제약하기** — [목록의 **36번 주제**](../36-concepts-and-requires/).
