# cpp/syntax/03 — 캐스트 4종 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — `static_cast`](https://en.cppreference.com/w/cpp/language/static_cast) · [`const_cast`](https://en.cppreference.com/w/cpp/language/const_cast) · [`reinterpret_cast`](https://en.cppreference.com/w/cpp/language/reinterpret_cast) · [`dynamic_cast`](https://en.cppreference.com/w/cpp/language/dynamic_cast) · [explicit cast(C 스타일)](https://en.cppreference.com/w/cpp/language/explicit_cast) · [`std::bit_cast`](https://en.cppreference.com/w/cpp/numeric/bit_cast) · [GCC 13 Optimize Options — `-fstrict-aliasing`](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Optimize-Options.html) · [GCC 13 C++ Dialect Options — `-fno-rtti`](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/C_002b_002b-Dialect-Options.html)
> **실행 검증** — 이 문서의 모든 출력·경고·에러·심볼은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **gcc 13.3.0**(C 대비용) · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> **UB 가 걸린 블록은 `-O0`·`-O1`·`-O2`·`-O3`·`-Os` 다섯 수준 × 두 컴파일러로 돌렸다.** 한 수준만 돌린 결과는 싣지 않는다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex` 이고 파일 이름은 **`ex.cpp`·`ex.c`** 뿐이다.\
> ★ 블록은 `capture.sh` 가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.
> **버전** — 캐스트 네 종류는 **C++98부터** 있고 규칙은 그때와 같다.\
> **`std::bit_cast` 는 C++20부터**이고 이 g++ 에서 **된다**((7)).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> **경계** — 「C 스타일 캐스트가 무엇을 하나」의 정본은 C 갈래의\
> [`05-explicit-casts-and-pointer-conversions/`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)다.\
> 그쪽은 **값 변환 대 해석 변환의 어셈블리 증명 · 정렬 · 엄격한 앨리어싱 열 벌 실측 · `const` 벗기기 UB ·\
> 함수 포인터 · 캐스트가 끄는 경고**까지 전부 결론지었다.\
> 여기는 **C++ 가 새로 하는 것**만 쓴다 — **그 한 덩어리를 넷으로 쪼갠 것**, 그리고\
> **`dynamic_cast` 라는 C 에 없는 다섯째**, 그리고 **`const` 객체에 쓰는 UB 가 C 와 갈리는 자리**((4)).\
> 「정수 승격·산술 변환」은 C 갈래 [`03번`](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/),\
> 「가상 함수와 다형성」은 목록의 **19번 주제**, 「`const` 정확성 설계」는 목록의 **10번 주제**가 정본이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸** — 이 주제는 **UB 가 만든 값이 본문에 실리므로** 이 선언이 특히 중요하다.
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★ **UB 가 만든 값 자체**(`punned=1` 대 `1073741824` · `k=7` 대 `99`) | ★ **그 값이 「갈린다」는 사실**과 **어느 플래그에서 갈렸나** |
> | 컴파일 시간 · 오브젝트 파일의 타임스탬프 | **진단 본문** · `파일:줄:칸` · **종료 코드**(`cc exit`·`run exit` 을 갈라 적었다) |
> | — | **오브젝트 파일의 미정의 심볼 목록**과 **바이트 크기**(같은 컴파일러·플래그에서 결정적이다) |
> | — | `typeid(...).name()` 의 맹글링 문자열 · `bad_cast::what()` |

## 한눈에 — 쉽게 말하면

**C++ 의 캐스트 넷은 「C 의 괄호 캐스트 하나를 네 개의 이름 붙은 도구로 쪼갠 것」이다.**

C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)이 결론지은 것은
「**캐스트는 안전장치가 아니라 안전장치를 끄는 스위치**」였다.
C++ 는 그 스위치를 **넷으로 쪼개서 어느 안전장치를 끄는지 이름으로 적게** 만들었다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **만능 열쇠 하나** — 무슨 문을 여는지 알 수 없다 | C 의 `(T)x` |
| **「규격이 맞는 부품으로 바꿔 끼운다」** | `static_cast` — 언어가 이미 아는 변환을 명시적으로 |
| **「출입 금지 딱지만 뗀다」** | `const_cast` — `const`/`volatile` 만 건드린다 |
| **「같은 비트를 다른 라벨로 읽는다」** | `reinterpret_cast` — 값은 그대로, 해석만 바꾼다 |
| ★ **「이 물건이 진짜 그거 맞는지 물어본다」** | `dynamic_cast` — **실행 중에 확인하고 아니면 알려 준다** |
| 만능 열쇠는 **넷 중 하나로 자동으로 풀린다** | C 스타일 캐스트는 순서대로 시도해 **처음 되는 것**이 된다((11)) |
| ★ 만능 열쇠로는 **「물어보기」만은 못 한다** | C 스타일 캐스트는 **절대 `dynamic_cast` 가 되지 않는다**((11)) |

- ★★ **넷 중 셋은 컴파일 시간에 끝나고, `dynamic_cast` 만 실행 시간 비용이 있다**((10)).
- ★★ **이름이 붙었다고 안전해진 것이 아니다** — `const_cast` 와 `reinterpret_cast` 는 **UB 를 만드는 도구**다((4)·(6)).\
  달라진 것은 **어느 안전장치를 껐는지가 코드에 글자로 남는다**는 것뿐이다. 그리고 그것이 **`grep` 가능하다.**
- ★ **`static_cast` 가 거부하는 셋이 나머지 셋의 일자리**다((2)) — 그 대응을 외우면 도구 고르기가 끝난다.

```text
   C:    (T)x      하나의 괄호가 아래를 전부 한다

   C++:  static_cast<T>(x)       "언어가 아는 변환"
         const_cast<T>(x)        "const/volatile 만"
         reinterpret_cast<T>(x)  "비트는 그대로, 라벨만"
         dynamic_cast<T>(x)      "진짜 그 타입인지 물어본다"  <- C 에 없다
                                       │
                                       └─ 실행 시간 · RTTI 필요 · 실패를 알려 준다

   (T)x 는 위에서부터 시도한다:
       const_cast -> static_cast -> static_cast+const_cast
                  -> reinterpret_cast -> reinterpret_cast+const_cast
   ★ 이 줄에 dynamic_cast 는 없다.
```

> **`static_cast`** — 「언어가 암묵적으로 할 수 있는 변환」과 「그 역방향 중 안전한 것」을 명시적으로 쓰는 것.\
> 산술 변환 · `void*`→`T*` · 상속 계통의 업/다운캐스트 · 열거형↔정수.

> **`const_cast`** — `const`·`volatile` **한정자만** 더하거나 뺀다. 타입 자체는 못 바꾼다.

> **`reinterpret_cast`** — **비트를 그대로 두고 타입만 바꾼다.** 포인터↔포인터, 포인터↔정수.

> **`dynamic_cast`** — 다형 타입의 **실제 타입을 실행 중에 확인**하고 맞을 때만 바꾼다.\
> 포인터면 실패 시 **`nullptr`**, 참조면 **`std::bad_cast` 예외**.

> **RTTI(Run-Time Type Information)** — 실행 중에 객체의 실제 타입을 알아내는 장치.\
> `dynamic_cast` 와 `typeid` 가 그 위에 서 있다. **`-fno-rtti` 로 끄면 둘 다 에러**다((9)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **넷을 어떻게 고르나** — 「되는 예와 안 되는 예」를 각각 던져 **경계**로 익힐 수 있나.
2. **C 스타일 캐스트는 무엇으로 풀리나** — 순서를 말하고 **`static_cast` 가 거부한 것을 그것이 하는 것**을 보일 수 있나.
3. **이름이 붙어도 UB 는 그대로인가** — `const_cast`·`reinterpret_cast` 가 만드는 UB 를 **출력으로** 보이고,\
   **어느 도구가 그것을 못 보는지** 셀 수 있나.

★ C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)이
「**캐스트는 안전장치를 끄는 스위치**」를 결론으로 냈다면,
여기는 「**그 스위치를 넷으로 쪼개면 무엇이 좋아지고 무엇은 그대로인가**」다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| **컴파일 진단** | 각 캐스트가 **거부하는 자리** — 그것이 도구의 경계다 | (2)·(9) |
| **실행 출력** | UB 가 만든 값 · `dynamic_cast` 의 성공과 실패 | (4)·(6)·(8) |
| **sanitizer** | ★ **둘 다 이 주제의 UB 를 못 본다** — C 편과 같은 결론 | (4)·(6) |
| ★ **오브젝트 파일의 미정의 심볼과 크기** | `dynamic_cast` 가 **런타임 호출**이라는 것과 그 값 | (10) |

★ **네 번째 창을 왜 이것으로 골랐나.** `dynamic_cast` 는 「실행 중에 확인한다」가 정의인데,
**그 「확인」이 어디에 사는지**는 실행 출력만 봐서는 안 보인다. 성공·실패만 보인다.

**같은 함수를 `static_cast` 판과 `dynamic_cast` 판으로 하나씩 컴파일해 `nm -uC` 로 대조하면**
`dynamic_cast` 판에만 **`__dynamic_cast` 라는 미정의 심볼**이 생긴다((10)).
「런타임 라이브러리를 부른다」가 **파일에 글자로** 남는 것이고, 그 옆에 **오브젝트 크기**까지 붙는다.
`-fno-rtti` 로 던져 받는 에러((9))는 **같은 사실의 반대편**이다.

★ **sanitizer 칸을 「못 본다」로 적는다.** 이 주제에는 UB 가 둘 있는데
**gcc·clang 의 UBSan·ASan 이 어느 것도 한 줄을 내지 않았다**((4)·(6)).
C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)이
「**앨리어싱·`const` 는 UBSan 도 ASan 도 못 잡는다**」로 결론지은 것과 **같은 답**이다.

### (1) `static_cast` — 되는 것

**언제 쓰나** — 캐스트가 필요한 자리의 **대부분**. 먼저 이것부터 시도한다.

```text
===== 소스: ex.cpp =====
// static_cast 가 하는 일 — 「원래 되는 변환을 명시적으로 쓴다」
#include <cstdio>

enum class Color : unsigned char { Red, Green };
struct Base { int a = 1; };
struct Derived : Base { int b = 2; };

int main() {
    double d = 3.9;
    int    i = static_cast<int>(d);              // ① 산술 변환(절단)
    void*  v = &i;
    int*   p = static_cast<int*>(v);             // ② void* -> T*
    Derived der;
    Base*  up = static_cast<Base*>(&der);        // ③ 업캐스트
    Derived* down = static_cast<Derived*>(up);   // ④ 다운캐스트 — 검사는 없다
    int    n = static_cast<int>(Color::Green);   // ⑤ 범위 있는 열거형 -> 정수
    Color  c = static_cast<Color>(1);            // ⑥ 정수 -> 범위 있는 열거형
    std::printf("i=%d *p=%d up->a=%d down->b=%d n=%d c==Green:%d\n",
                i, *p, up->a, down->b, n,
                static_cast<int>(c == Color::Green));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
i=3 *p=3 up->a=1 down->b=2 n=1 c==Green:1
```

여섯 쓰임이 한 줄에 다 들어 있다.

| 쓰임 | 예 | 무엇인가 |
|---|---|---|
| ① 산술 변환 | `static_cast<int>(3.9)` → `3` | **절단**이다(반올림이 아니다) |
| ② `void*` → `T*` | `static_cast<int*>(v)` | C 에서는 캐스트조차 필요 없던 자리 |
| ③ 업캐스트 | `static_cast<Base*>(&der)` | 암묵으로도 되지만 명시할 수 있다 |
| ④ 다운캐스트 | `static_cast<Derived*>(up)` | ★ **검사가 없다** — 틀리면 UB |
| ⑤ 열거형 → 정수 | `static_cast<int>(Color::Green)` | [**02번 형제**](../02-enum-class-and-scoped-enumerations/)의 담장 ② |
| ⑥ 정수 → 열거형 | `static_cast<Color>(1)` | 〃 |

- ★★ **④가 이 절의 함정이다.** `static_cast` 로 하는 다운캐스트는 **컴파일러가 믿고 넘어간다.**\
  틀린 타입이면 그 뒤 접근이 전부 UB 다 — (11)에서 그것을 눈으로 본다.
- ★ ①의 **절단**은 C 와 같다. 어셈블리 수준 증명(`cvttsd2si` 의 `tt` 가 truncate)은\
  C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)에 있다.

### (2) `static_cast` — 안 되는 셋. 그 셋이 나머지 도구의 일자리다

**언제 쓰나** — 「어느 캐스트를 써야 하지?」를 **컴파일러에게 물어보는** 방법.

```text
===== 소스: ex.cpp =====
// static_cast 가 거부하는 셋 — 그 셋이 나머지 세 캐스트의 일자리다
struct Base { int a = 1; };
struct Hidden : private Base { int b = 2; };   // private 상속

int main() {
    const int k = 7;
    int* p = static_cast<int*>(&k);            // ① const 를 떼는 일

    Hidden h;
    Base* q = static_cast<Base*>(&h);          // ② 접근할 수 없는 기반으로

    double d = 1.0;
    int* r = static_cast<int*>(&d);            // ③ 무관한 포인터 타입으로

    (void)p; (void)q; (void)r;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp: In function ‘int main()’:
ex.cpp:7:14: error: invalid ‘static_cast’ from type ‘const int*’ to type ‘int*’
    7 |     int* p = static_cast<int*>(&k);            // ① const 를 떼는 일
      |              ^~~~~~~~~~~~~~~~~~~~~
ex.cpp:10:36: error: ‘Base’ is an inaccessible base of ‘Hidden’
   10 |     Base* q = static_cast<Base*>(&h);          // ② 접근할 수 없는 기반으로
      |                                    ^
ex.cpp:13:14: error: invalid ‘static_cast’ from type ‘double*’ to type ‘int*’
   13 |     int* r = static_cast<int*>(&d);            // ③ 무관한 포인터 타입으로
      |              ^~~~~~~~~~~~~~~~~~~~~
```

clang 은 ②의 이유를 **한 줄 더** 말해 준다 — `note: declared private here`.

```text
===== 소스: ex.cpp =====
// static_cast 가 거부하는 셋 — 그 셋이 나머지 세 캐스트의 일자리다
struct Base { int a = 1; };
struct Hidden : private Base { int b = 2; };   // private 상속

int main() {
    const int k = 7;
    int* p = static_cast<int*>(&k);            // ① const 를 떼는 일

    Hidden h;
    Base* q = static_cast<Base*>(&h);          // ② 접근할 수 없는 기반으로

    double d = 1.0;
    int* r = static_cast<int*>(&d);            // ③ 무관한 포인터 타입으로

    (void)p; (void)q; (void)r;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp:7:14: error: static_cast from 'const int *' to 'int *' is not allowed
    7 |     int* p = static_cast<int*>(&k);            // ① const 를 떼는 일
      |              ^~~~~~~~~~~~~~~~~~~~~
ex.cpp:10:34: error: cannot cast 'Hidden' to its private base class 'Base'
   10 |     Base* q = static_cast<Base*>(&h);          // ② 접근할 수 없는 기반으로
      |                                  ^
ex.cpp:3:17: note: declared private here
    3 | struct Hidden : private Base { int b = 2; };   // private 상속
      |                 ^~~~~~~~~~~~
ex.cpp:13:14: error: static_cast from 'double *' to 'int *' is not allowed
   13 |     int* r = static_cast<int*>(&d);            // ③ 무관한 포인터 타입으로
      |              ^~~~~~~~~~~~~~~~~~~~~
3 errors generated.
```

| 거부된 것 | 누구의 일자리인가 |
|---|---|
| ① `const int*` → `int*` | **`const_cast`** |
| ② `Hidden*` → `Base*`(private 상속) | **`reinterpret_cast`**(또는 설계를 고치는 것) |
| ③ `double*` → `int*` | **`reinterpret_cast`** |

- ★★ **이 표가 도구 고르기의 전부다.** `static_cast` 를 먼저 써 보고, 거부당하면 **거부 문구가 다음 도구를 가리킨다.**
- ★ **`dynamic_cast` 는 이 표에 없다.** 그것은 「거부당해서 쓰는 것」이 아니라\
  **「`static_cast` 로도 되지만 검사가 필요해서」** 쓰는 것이다((8)).

### (3) `const_cast` — 정의된 쓰임

**언제 쓰나** — **원래 `const` 가 아닌 객체**를 `const` 경로를 통해 받았을 때. 주로 C API 경계다.

```text
===== 소스: ex.cpp =====
// const 를 떼고 써도 「정의된」 자리 — 원래 객체가 const 가 아니면 된다
#include <cstdio>

void write_through(const int* cp) { *const_cast<int*>(cp) = 99; }

int main() {
    int k = 7;                     // 원래 객체가 const 가 아니다
    write_through(&k);
    std::fprintf(stderr, "k=%d\n", k);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
k=99
```

```text
===== 소스: ex.cpp =====
// const 를 떼고 써도 「정의된」 자리 — 원래 객체가 const 가 아니면 된다
#include <cstdio>

void write_through(const int* cp) { *const_cast<int*>(cp) = 99; }

int main() {
    int k = 7;                     // 원래 객체가 const 가 아니다
    write_through(&k);
    std::fprintf(stderr, "k=%d\n", k);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
k=99
```

- **`k=99`** — 두 최적화 수준에서 같고, **이것은 정의된 동작**이다.
- ★★ **가르는 것**은 포인터의 타입이 아니라 「**원래 객체가 무엇으로 선언됐나**」다.\
  `int k = 7;` 이므로 `const` 를 떼고 쓰는 것이 정의된다.\
  C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)이 C 에서 같은 결론을 냈다 — **언어가 바뀌어도 이 규칙은 같다.**

### (4) ★★ `const_cast` — UB. 그런데 **최적화 수준으로는 안 갈린다**

**언제 쓰나** — 「최적화 수준을 여럿 돌려라」가 **왜 처방이 아닌지**를 배우는 자리.

```text
===== 소스: ex.cpp =====
// const_cast 로 「진짜 const 객체」를 고치면 — 한 printf 안에서 값이 둘로 갈린다
#include <cstdio>

int read_through(const int* q) { return *q; }   // 밖에서 다시 읽어 본다

int main() {
    const int k = 7;
    int* p = const_cast<int*>(&k);
    *p = 99;
    std::fprintf(stderr, "k=%d  *p=%d  read_through(&k)=%d\n",
                 k, *p, read_through(&k));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
k=7  *p=99  read_through(&k)=99
```

★★ **한 `fprintf` 안에서 같은 객체가 두 값으로 읽힌다** — `k=7` 인데 `*p=99` 이고 `read_through(&k)=99` 다.

다섯 최적화 수준 × 두 컴파일러 = **열 벌이 전부 같았다.**

| 명령 | 출력 |
|---|---|
| g++ `-O0` / `-O1` / `-O2` / `-O3` / `-Os` | `k=7  *p=99  read_through(&k)=99` (다섯 벌 동일) |
| clang++ `-O0` / `-O1` / `-O2` / `-O3` / `-Os` | 〃 (다섯 벌 동일) |
| g++ `-O0 -fsanitize=undefined` | 〃 — **진단 0줄** |
| clang++ `-O0 -fsanitize=undefined` | 〃 — **진단 0줄** |
| g++ `-O0 -fsanitize=address` | 〃 — **진단 0줄** |
| g++ `-O2 -fsanitize=undefined,address` | 〃 — **진단 0줄** |

대표로 clang `-O2` 판을 싣는다. **나머지 아홉 벌도 한 글자도 같았다.**

```text
===== 소스: ex.cpp =====
// const_cast 로 「진짜 const 객체」를 고치면 — 한 printf 안에서 값이 둘로 갈린다
#include <cstdio>

int read_through(const int* q) { return *q; }   // 밖에서 다시 읽어 본다

int main() {
    const int k = 7;
    int* p = const_cast<int*>(&k);
    *p = 99;
    std::fprintf(stderr, "k=%d  *p=%d  read_through(&k)=%d\n",
                 k, *p, read_through(&k));
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic -O2 ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
k=7  *p=99  read_through(&k)=99
```

- ★★★ **C 와 갈린다.** 같은 모양의 프로그램을 C 로 던지면 **`-O0` 에서 답이 다르다.**

```text
===== 소스: ex.c =====
/* 같은 코드를 C 로 — 원래 객체가 const 일 때 C 와 C++ 이 갈리는 자리 */
#include <stdio.h>

int read_through(const int *q) { return *q; }

int main(void) {
    const int k = 7;
    int *p = (int *)&k;
    *p = 99;
    fprintf(stderr, "k=%d  *p=%d  read_through(&k)=%d\n",
            k, *p, read_through(&k));
    return 0;
}
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 ex.c -o ex && ./ex (cc exit=0 · run exit=0) =====
k=99  *p=99  read_through(&k)=99
```

```text
===== 소스: ex.c =====
/* 같은 코드를 C 로 — 원래 객체가 const 일 때 C 와 C++ 이 갈리는 자리 */
#include <stdio.h>

int read_through(const int *q) { return *q; }

int main(void) {
    const int k = 7;
    int *p = (int *)&k;
    *p = 99;
    fprintf(stderr, "k=%d  *p=%d  read_through(&k)=%d\n",
            k, *p, read_through(&k));
    return 0;
}
===== gcc -std=c17 -Wall -Wextra -pedantic -O1 ex.c -o ex && ./ex (cc exit=0 · run exit=0) =====
k=7  *p=99  read_through(&k)=99
```

- **`gcc -O0` 은 `k=99`, `gcc -O1` 부터 `k=7`.** C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)이\
  「**경계선이 `-O2` 가 아니라 `-O1`**」이라고 실측해 둔 그 자리다.
- ★★ **C++ 에서는 `-O0` 에서부터 `k=7`** 이다. **경계선이 없다** — 최적화가 아니라 **언어가 다르기 때문**이다.\
  C++ 에서 `const int k = 7;` 은 **상수식**이라 이름 `k` 가 **어느 최적화 수준에서도 7로 접힌다.**\
  ★ **「최적화 수준을 여럿 돌려라」가 이 자리를 잡아 주지 않았다.** 잡아 준 것은 **언어를 바꿔 던진 것**이다.
- ★★ **UBSan 도 ASan 도 한 줄을 안 낸다**(위 표 — 네 벌을 따로 돌렸다). **`-Wcast-qual` 도 0건**이다((5)).\
  대표로 `-O2 -fsanitize=undefined,address` 판을 싣는다.

```text
===== 소스: ex.cpp =====
// const_cast 로 「진짜 const 객체」를 고치면 — 한 printf 안에서 값이 둘로 갈린다
#include <cstdio>

int read_through(const int* q) { return *q; }   // 밖에서 다시 읽어 본다

int main() {
    const int k = 7;
    int* p = const_cast<int*>(&k);
    *p = 99;
    std::fprintf(stderr, "k=%d  *p=%d  read_through(&k)=%d\n",
                 k, *p, read_through(&k));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 -fsanitize=undefined,address ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
k=7  *p=99  read_through(&k)=99
```

  C 편이 「`const` 는 UBSan 도 ASan 도 못 잡는다」로 결론지은 것과 같다.

### (5) 경고를 플래그별로 세기 — `const_cast` 쪽

```text
===== 소스: ex.cpp =====
// const_cast 로 「진짜 const 객체」를 고치면 — 한 printf 안에서 값이 둘로 갈린다
#include <cstdio>

int read_through(const int* q) { return *q; }   // 밖에서 다시 읽어 본다

int main() {
    const int k = 7;
    int* p = const_cast<int*>(&k);
    *p = 99;
    std::fprintf(stderr, "k=%d  *p=%d  read_through(&k)=%d\n",
                 k, *p, read_through(&k));
}
===== for F in "-Wall -Wextra" "-Wall -Wextra -pedantic" "-Wcast-qual" "-Wall -Wextra -Wcast-qual"; do printf "[%-26s] warning: %s 건  cc exit=" "$F" "$(g++ -std=c++20 -O2 $F ex.cpp -o ex 2>&1 | grep -c "warning:")"; g++ -std=c++20 -O2 $F ex.cpp -o ex >/dev/null 2>&1; echo $?; done (exit=0) =====
[-Wall -Wextra             ] warning: 0 건  cc exit=0
[-Wall -Wextra -pedantic   ] warning: 0 건  cc exit=0
[-Wcast-qual               ] warning: 0 건  cc exit=0
[-Wall -Wextra -Wcast-qual ] warning: 0 건  cc exit=0
```

- ★★ **네 벌 전부 0건이다.** `-Wcast-qual` 은 **C 스타일로 `const` 를 벗길 때** 말하는 플래그이고,\
  **`const_cast` 는 「일부러 벗긴다」는 선언**이라 말하지 않는다.
- ★ **`cc exit` 도 전부 0** 이다. 「경고 0건 + exit 0」이 **UB 가 없다는 뜻이 전혀 아닌** 전형이다.

### (6) ★★ `reinterpret_cast` 와 엄격한 앨리어싱 — 여기는 갈린다

**언제 쓰나** — 캐스트가 **답을 바꾸는** 유일한 자리.

```text
===== 소스: ex.cpp =====
// reinterpret_cast 와 엄격한 앨리어싱 — 최적화가 답을 바꾸는 자리
#include <cstdio>

int punned(int* pi, float* pf) {   // 컴파일러는 이 둘이 겹칠 수 없다고 가정한다
    *pi = 1;
    *pf = 2.0f;
    return *pi;
}

int main() {
    int x = 0;
    int r = punned(&x, reinterpret_cast<float*>(&x));
    std::fprintf(stderr, "punned=%d\n", r);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 -fstrict-aliasing ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
punned=1073741824
```

같은 프로그램을 **다섯 수준 × 두 플래그**로 돌린 결과다.

| 최적화 | `-fstrict-aliasing` | `-fno-strict-aliasing` |
|---|---|---|
| `-O0` | `punned=1073741824` | `punned=1073741824` |
| **`-O1`** | ★ **`punned=1`** | `punned=1073741824` |
| `-O2` | `punned=1` | `punned=1073741824` |
| `-O3` | `punned=1` | `punned=1073741824` |
| `-Os` | `punned=1` | `punned=1073741824` |

- ★★ **경계선은 `-O1`** 이다. `-O0` 과 `-O1` 사이에서 답이 뒤집힌다.\
  C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)은 **다른 소스 모양에서 `-O2`** 를 경계로 실측했다 —\
  ★ **「경계는 `-O2` 다」를 외우면 안 된다.** 경계는 **소스 모양과 컴파일러에 달렸다.**
- **`-fno-strict-aliasing` 은 다섯 수준 전부에서 `1073741824`** 다 — 그 플래그가 **가정을 끈다.**
- clang 은 **`-O2` 에서 갈렸다**(`-O0` 은 `1073741824`, `-O2` 는 `1`).

```text
===== 소스: ex.cpp =====
// reinterpret_cast 와 엄격한 앨리어싱 — 최적화가 답을 바꾸는 자리
#include <cstdio>

int punned(int* pi, float* pf) {   // 컴파일러는 이 둘이 겹칠 수 없다고 가정한다
    *pi = 1;
    *pf = 2.0f;
    return *pi;
}

int main() {
    int x = 0;
    int r = punned(&x, reinterpret_cast<float*>(&x));
    std::fprintf(stderr, "punned=%d\n", r);
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic -O2 ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
punned=1
```

- ★★ **sanitizer 를 둘 다 걸어도 `punned=1`** 이고 **진단은 0줄**이다.

```text
===== 소스: ex.cpp =====
// reinterpret_cast 와 엄격한 앨리어싱 — 최적화가 답을 바꾸는 자리
#include <cstdio>

int punned(int* pi, float* pf) {   // 컴파일러는 이 둘이 겹칠 수 없다고 가정한다
    *pi = 1;
    *pf = 2.0f;
    return *pi;
}

int main() {
    int x = 0;
    int r = punned(&x, reinterpret_cast<float*>(&x));
    std::fprintf(stderr, "punned=%d\n", r);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 -fsanitize=undefined,address ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
punned=1
```

  ★ **이것이 이 갈래에서 도구가 가장 못 보는 UB 다.** C 편의 결론과 같다.

### (7) 비트를 그대로 읽는 세 방법 — 값은 같고 「합법인가」가 다르다

**언제 쓰나** — `float` 의 비트를 보거나, 직렬화하거나, 해시를 만들 때.

```text
===== 소스: ex.cpp =====
// 비트를 그대로 읽는 세 방법 — 값은 같고 「합법인가」가 다르다
#include <cstdio>
#include <cstring>
#include <bit>

int main() {
    float f = 3.14f;
    int a = *reinterpret_cast<int*>(&f);                 // UB (엄격한 앨리어싱 위반)
    int b; std::memcpy(&b, &f, sizeof b);                // 정의됨
    int c = std::bit_cast<int>(f);                       // 정의됨 (C++20)
    std::fprintf(stderr, "reinterpret=%d memcpy=%d bit_cast=%d\n", a, b, c);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 -w ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
reinterpret=1078523331 memcpy=1078523331 bit_cast=1078523331
```

- **셋이 같은 값**(`1078523331`)을 낸다. **값이 같은 것이 합법성을 말해 주지 않는다.**
- `*reinterpret_cast<int*>(&f)` 만 **UB** 다. `memcpy` 와 **`std::bit_cast`(C++20)** 는 정의된다.
- ★ C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)이 **`memcpy` 가 기계어까지 공짜**임을 실측해 두었다.\
  C++20 은 거기에 **`std::bit_cast` 라는 이름**을 얹었다 — `constexpr` 에서도 쓸 수 있는 것이 덤이다.

**경고는 어떤가.** g++ `-O2` 는 **두 줄**을 낸다.

```text
===== 소스: ex.cpp =====
// 비트를 그대로 읽는 세 방법 — 값은 같고 「합법인가」가 다르다
#include <cstdio>
#include <cstring>
#include <bit>

int main() {
    float f = 3.14f;
    int a = *reinterpret_cast<int*>(&f);                 // UB (엄격한 앨리어싱 위반)
    int b; std::memcpy(&b, &f, sizeof b);                // 정의됨
    int c = std::bit_cast<int>(f);                       // 정의됨 (C++20)
    std::fprintf(stderr, "reinterpret=%d memcpy=%d bit_cast=%d\n", a, b, c);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 ex.cpp -o ex (cc exit=0) =====
ex.cpp: In function ‘int main()’:
ex.cpp:8:14: warning: dereferencing type-punned pointer will break strict-aliasing rules [-Wstrict-aliasing]
    8 |     int a = *reinterpret_cast<int*>(&f);                 // UB (엄격한 앨리어싱 위반)
      |              ^~~~~~~~~~~~~~~~~~~~~~~~~~
ex.cpp:8:9: warning: ‘f’ is used uninitialized [-Wuninitialized]
    8 |     int a = *reinterpret_cast<int*>(&f);                 // UB (엄격한 앨리어싱 위반)
      |         ^
ex.cpp:7:11: note: ‘f’ declared here
    7 |     float f = 3.14f;
      |           ^
```

- ★★ **두 번째 경고가 진짜 교재다** — `'f' is used uninitialized`.\
  `f` 는 바로 윗줄에서 `3.14f` 로 초기화됐다. **컴파일러가 「그 대입은 이 읽기에 닿지 않는다」고 판단한 것**이고,\
  그 판단의 근거가 **엄격한 앨리어싱 가정**이다. **경고가 가정을 자백한다.**
- ★ **`-O0` 에서는 경고가 0건**이다 — 최적화기가 봐야 보이는 경고다.

```text
===== 소스: ex.cpp =====
// 비트를 그대로 읽는 세 방법 — 값은 같고 「합법인가」가 다르다
#include <cstdio>
#include <cstring>
#include <bit>

int main() {
    float f = 3.14f;
    int a = *reinterpret_cast<int*>(&f);                 // UB (엄격한 앨리어싱 위반)
    int b; std::memcpy(&b, &f, sizeof b);                // 정의됨
    int c = std::bit_cast<int>(f);                       // 정의됨 (C++20)
    std::fprintf(stderr, "reinterpret=%d memcpy=%d bit_cast=%d\n", a, b, c);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 ex.cpp -o ex (cc exit=0) =====
```

- ★★ **clang `-O2` 는 같은 플래그로 0건**이다. 「경고가 안 나니까 괜찮다」가 **컴파일러에 달렸다**는 뜻이다.

```text
===== 소스: ex.cpp =====
// 비트를 그대로 읽는 세 방법 — 값은 같고 「합법인가」가 다르다
#include <cstdio>
#include <cstring>
#include <bit>

int main() {
    float f = 3.14f;
    int a = *reinterpret_cast<int*>(&f);                 // UB (엄격한 앨리어싱 위반)
    int b; std::memcpy(&b, &f, sizeof b);                // 정의됨
    int c = std::bit_cast<int>(f);                       // 정의됨 (C++20)
    std::fprintf(stderr, "reinterpret=%d memcpy=%d bit_cast=%d\n", a, b, c);
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic -O2 ex.cpp -o ex (cc exit=0) =====
```

플래그별로 세면 이렇다.

```text
===== 소스: ex.cpp =====
// 비트를 그대로 읽는 세 방법 — 값은 같고 「합법인가」가 다르다
#include <cstdio>
#include <cstring>
#include <bit>

int main() {
    float f = 3.14f;
    int a = *reinterpret_cast<int*>(&f);                 // UB (엄격한 앨리어싱 위반)
    int b; std::memcpy(&b, &f, sizeof b);                // 정의됨
    int c = std::bit_cast<int>(f);                       // 정의됨 (C++20)
    std::fprintf(stderr, "reinterpret=%d memcpy=%d bit_cast=%d\n", a, b, c);
}
===== for F in "-Wall -Wextra" "-Wstrict-aliasing=1" "-Wstrict-aliasing=2" "-Wstrict-aliasing=3"; do printf "[%-22s] warning: %s 건  cc exit=" "$F" "$(g++ -std=c++20 -O2 $F ex.cpp -o ex 2>&1 | grep -c "warning:")"; g++ -std=c++20 -O2 $F ex.cpp -o ex >/dev/null 2>&1; echo $?; done (exit=0) =====
[-Wall -Wextra         ] warning: 2 건  cc exit=0
[-Wstrict-aliasing=1   ] warning: 1 건  cc exit=0
[-Wstrict-aliasing=2   ] warning: 1 건  cc exit=0
[-Wstrict-aliasing=3   ] warning: 1 건  cc exit=0
```

- ★ `-Wstrict-aliasing` 은 **`=1`·`=2`·`=3` 이 전부 1건**이다.\
  C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)은 **`=3` 이 0건**인 소스를 실측했다 —\
  ★ **같은 플래그가 소스 모양에 따라 다르게 답한다.** 「`-Wall` 이 켜는 수준 3은 못 잡는다」를 **규칙으로 외우면 틀린다.**
- ★ 여기서 `-Wall -Wextra` 가 2건인 것은 **`-Wstrict-aliasing` 1건 + `-Wuninitialized` 1건**이다.

### (8) `dynamic_cast` — 물어보고 답을 받는다

**언제 쓰나** — 기반 포인터가 **실제로** 어느 파생인지 알아야 할 때.

```text
===== 소스: ex.cpp =====
// dynamic_cast 넷 — 포인터는 nullptr, 참조는 bad_cast
#include <cstdio>
#include <typeinfo>

struct Base  { virtual ~Base() = default; };
struct Left  : Base { int l = 10; };
struct Right : Base { int r = 20; };

int main() {
    Base* b = new Left;                            // 실제로는 Left 다
    std::printf("typeid(*b).name() = %s\n", typeid(*b).name());
    std::printf("typeid(*b) == typeid(Left) : %d\n",
                static_cast<int>(typeid(*b) == typeid(Left)));
    std::printf("dynamic_cast<Left*>  : %s\n",
                dynamic_cast<Left*>(b)  ? "非null" : "nullptr");
    std::printf("dynamic_cast<Right*> : %s\n",
                dynamic_cast<Right*>(b) ? "非null" : "nullptr");
    try {
        Right& r = dynamic_cast<Right&>(*b);
        (void)r;
    } catch (const std::bad_cast& e) {
        std::printf("참조 판은 예외 — what() = %s\n", e.what());
    }
    delete b;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
typeid(*b).name() = 4Left
typeid(*b) == typeid(Left) : 1
dynamic_cast<Left*>  : 非null
dynamic_cast<Right*> : nullptr
참조 판은 예외 — what() = std::bad_cast
```

- **성공하면 포인터**, **실패하면 `nullptr`** — 이것이 포인터 판의 계약이다.
- **참조 판은 `nullptr` 이 없으므로 예외를 던진다** — `std::bad_cast`, `what()` 은 `"std::bad_cast"`.
- **`typeid(*b).name()` 이 `4Left`** 다 — **맹글링된 이름**이고 `4` 는 이름 길이다.\
  ★ 이 철자는 **플랫폼 ABI** 소관이다(사람이 읽을 이름을 보장하지 않는다).
- **`typeid(*b) == typeid(Left)` 가 `1`** — `dynamic_cast` 없이 **정확한 타입 일치**를 물어보는 방법이다.\
  ★ 둘은 다르다 — `dynamic_cast` 는 「**그것이거나 그 파생**」을 묻고, `typeid` 비교는 「**정확히 그것**」을 묻는다.

### (9) `dynamic_cast` 의 전제 둘 — 다형 타입과 RTTI

**언제 쓰나** — `dynamic_cast` 가 **컴파일조차 안 될 때**.

**전제 ①** — 원본 타입에 **가상 함수가 하나는 있어야** 한다.

```text
===== 소스: ex.cpp =====
// dynamic_cast 는 다형 타입에만 쓴다 — 가상 함수가 하나도 없으면
struct Plain  { int y = 1; };
struct PlainD : Plain { int z = 2; };

int main() {
    Plain p;
    PlainD* d = dynamic_cast<PlainD*>(&p);
    return d ? 1 : 0;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp: In function ‘int main()’:
ex.cpp:7:17: error: cannot ‘dynamic_cast’ ‘& p’ (of type ‘struct Plain*’) to type ‘struct PlainD*’ (source type is not polymorphic)
    7 |     PlainD* d = dynamic_cast<PlainD*>(&p);
      |                 ^~~~~~~~~~~~~~~~~~~~~~~~~
```

clang 은 같은 것을 **네 낱말로** 말한다.

```text
===== 소스: ex.cpp =====
// dynamic_cast 는 다형 타입에만 쓴다 — 가상 함수가 하나도 없으면
struct Plain  { int y = 1; };
struct PlainD : Plain { int z = 2; };

int main() {
    Plain p;
    PlainD* d = dynamic_cast<PlainD*>(&p);
    return d ? 1 : 0;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp:7:17: error: 'Plain' is not polymorphic
    7 |     PlainD* d = dynamic_cast<PlainD*>(&p);
      |                 ^                     ~~
1 error generated.
```

- ★ g++ 는 `(source type is not polymorphic)`, clang 은 `'Plain' is not polymorphic`.\
  ★★ **이 진단이 「`dynamic_cast` 는 vtable 을 타고 내려간다」를 말한다** — vtable 이 없으면 물어볼 곳이 없다.

**전제 ②** — **RTTI 가 켜져 있어야** 한다. `-fno-rtti` 로 던지면 이렇게 된다.

```text
===== 소스: ex.cpp =====
// dynamic_cast 와 typeid 는 RTTI 위에 서 있다 — -fno-rtti 로 던져 본다
#include <cstdio>
#include <typeinfo>

struct Base    { virtual ~Base() = default; };
struct Derived : Base {};

int main() {
    Base* b = new Derived;
    std::printf("%s\n", typeid(*b).name());
    Derived* d = dynamic_cast<Derived*>(b);
    std::printf("%s\n", d ? "非null" : "nullptr");
    delete b;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -fno-rtti ex.cpp -o ex (cc exit=1) =====
ex.cpp: In function ‘int main()’:
ex.cpp:10:33: error: cannot use ‘typeid’ with ‘-fno-rtti’
   10 |     std::printf("%s\n", typeid(*b).name());
      |                                 ^
ex.cpp:11:18: error: ‘dynamic_cast’ not permitted with ‘-fno-rtti’
   11 |     Derived* d = dynamic_cast<Derived*>(b);
      |                  ^~~~~~~~~~~~~~~~~~~~~~~~~
```

```text
===== 소스: ex.cpp =====
// dynamic_cast 와 typeid 는 RTTI 위에 서 있다 — -fno-rtti 로 던져 본다
#include <cstdio>
#include <typeinfo>

struct Base    { virtual ~Base() = default; };
struct Derived : Base {};

int main() {
    Base* b = new Derived;
    std::printf("%s\n", typeid(*b).name());
    Derived* d = dynamic_cast<Derived*>(b);
    std::printf("%s\n", d ? "非null" : "nullptr");
    delete b;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic -fno-rtti ex.cpp -o ex (cc exit=1) =====
ex.cpp:10:25: error: use of typeid requires -frtti
   10 |     std::printf("%s\n", typeid(*b).name());
      |                         ^
ex.cpp:11:18: error: use of dynamic_cast requires -frtti
   11 |     Derived* d = dynamic_cast<Derived*>(b);
      |                  ^
2 errors generated.
```

- ★★ **`typeid` 와 `dynamic_cast` 가 함께 죽는다.** 둘이 **같은 장치 위에 서 있다**는 증거다.
- ★ g++ 는 **에러 넷**(`typeid` 1 + `dynamic_cast` 3), clang 은 **에러 둘**(각 종류 1개씩)이다 —\
  같은 소스인데 **세는 방식이 다르다.** clang 은 `2 errors generated.` 꼬리를 붙인다.
- ★ `-fno-rtti` 는 **임베디드·게임 엔진에서 흔한 설정**이다. 그런 코드베이스에서는 `dynamic_cast` 가 **문법이 아니라 금지어**다.

### (10) ★ 네 번째 창 — 오브젝트 파일이 `dynamic_cast` 의 값을 말한다

**언제 쓰나** — 「`dynamic_cast` 가 비싸다」를 **수치가 아니라 사실로** 보일 때.

같은 함수를 `static_cast` 판과 `dynamic_cast` 판으로 하나씩 컴파일하고 `nm -uC` 로 본다.

```text
===== 소스: ex.cpp =====
// 같은 함수를 두 캐스트로 — 오브젝트 파일이 값을 말한다
struct Base    { virtual ~Base() = default; };
struct Derived : Base {};

#ifdef USE_DYNAMIC
Derived* down(Base* b) { return dynamic_cast<Derived*>(b); }
#else
Derived* down(Base* b) { return static_cast<Derived*>(b); }
#endif
===== g++ -std=c++20 -Wall -Wextra -pedantic -c ex.cpp -o ex.o && nm -uC ex.o; echo '오브젝트 크기:' $(wc -c < ex.o) '바이트' (cc exit=0 · run exit=0) =====
오브젝트 크기: 1232 바이트
```

```text
===== 소스: ex.cpp =====
// 같은 함수를 두 캐스트로 — 오브젝트 파일이 값을 말한다
struct Base    { virtual ~Base() = default; };
struct Derived : Base {};

#ifdef USE_DYNAMIC
Derived* down(Base* b) { return dynamic_cast<Derived*>(b); }
#else
Derived* down(Base* b) { return static_cast<Derived*>(b); }
#endif
===== g++ -std=c++20 -Wall -Wextra -pedantic -DUSE_DYNAMIC -c ex.cpp -o ex.o && nm -uC ex.o; echo '오브젝트 크기:' $(wc -c < ex.o) '바이트' (cc exit=0 · run exit=0) =====
                 U vtable for __cxxabiv1::__class_type_info
                 U vtable for __cxxabiv1::__si_class_type_info
                 U __dynamic_cast
오브젝트 크기: 2704 바이트
```

- ★★ **`static_cast` 판은 미정의 심볼이 하나도 없다.** 컴파일 시간에 끝났다는 뜻이다.
- ★★ **`dynamic_cast` 판에는 셋이 생긴다** — `__dynamic_cast`(런타임 함수) ·\
  `vtable for __cxxabiv1::__class_type_info` · `vtable for __cxxabiv1::__si_class_type_info`(타입 정보 객체).
- **오브젝트 크기가 1232 → 2704 바이트**다. 함수 한 줄 차이인데 **2배 이상**이다.\
  ★ 이 수치는 **같은 컴파일러·플래그에서 결정적**이라 근거로 쓸 수 있다(머리말의 「안 흔들리는 칸」).
- ★ 이 창과 (9)의 `-fno-rtti` 에러는 **같은 사실의 양면**이다 — 있는 것을 보여 주기 / 없애서 비명을 듣기.

### (11) C 스타일 캐스트가 무엇으로 풀리나

**언제 쓰나** — 남의 C++ 코드에서 `(T)x` 를 읽을 때. **무엇이 일어나는지 이름을 붙일 수 있어야** 한다.

**(2)에서 `static_cast` 가 거부한 셋을 그대로 C 스타일로 던진다.**

```text
===== 소스: ex.cpp =====
// C 스타일 캐스트는 무엇으로 풀리나 — static_cast 가 거부한 셋을 그대로 던진다
#include <cstdio>

struct Base   { int a = 1; };
struct Hidden : private Base { int b = 2; };

int main() {
    const int k = 7;
    int* p = (int*)&k;          // -> const_cast
    Hidden h;
    Base* q = (Base*)&h;        // -> reinterpret_cast (static_cast 는 접근 불가)
    double d = 1.0;
    int* r = (int*)&d;          // -> reinterpret_cast
    std::printf("*p=%d q->a=%d r!=nullptr:%d\n", *p, q->a, static_cast<int>(r != nullptr));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
*p=7 q->a=1 r!=nullptr:1
```

- ★★ **셋 다 통과한다.** 거부당한 것이 **괄호로 바꾸면 되는 것**이 이 문법의 성격이다.
- 풀리는 순서는 이렇다 — 위에서부터 시도해 **처음 되는 것**이 된다.

```text
   (T)x  를 만나면 컴파일러가 차례로 시도한다

   1. const_cast<T>(x)
   2. static_cast<T>(x)
   3. static_cast<T>(...) 한 뒤 const_cast<T>(...)
   4. reinterpret_cast<T>(x)
   5. reinterpret_cast<T>(...) 한 뒤 const_cast<T>(...)

   ★ dynamic_cast 는 이 줄에 없다 — 절대 선택되지 않는다.
```

- `(int*)&k` 는 **1번**(`const_cast`)으로 풀린다. `*p=7` 이 나온 것은 (4)의 상수 접기 때문이다.
- `(Base*)&h` 는 **4번**(`reinterpret_cast`)으로 풀린다 — `static_cast` 는 private 기반이라 거부했으므로.\
  ★★ **이것이 위험한 이유** — 다중 상속에서는 업캐스트가 **주소 보정**을 해야 하는데\
  `reinterpret_cast` 는 **비트를 그대로 둔다.** 「되는데 틀린 주소」가 나올 수 있다.
- `(int*)&d` 는 **4번**이다.

**그리고 절대 되지 않는 하나 — 검사.**

```text
===== 소스: ex.cpp =====
// C 스타일 캐스트가 절대 되지 못하는 하나 — dynamic_cast
#include <cstdio>

struct Base  { virtual ~Base() = default; int a = 1; };
struct Left  : Base { int l = 10; };
struct Right : Base { int r = 20; };

int main() {
    Base* b = new Left;                              // 실제로는 Left 다
    Right* by_c       = (Right*)b;                   // 검사 없음
    Right* by_static  = static_cast<Right*>(b);      // 검사 없음
    Right* by_dynamic = dynamic_cast<Right*>(b);     // 검사한다
    std::printf("(Right*)b=%s  static_cast=%s  dynamic_cast=%s\n",
        by_c       ? "非null" : "nullptr",
        by_static  ? "非null" : "nullptr",
        by_dynamic ? "非null" : "nullptr");
    std::printf("by_c->r 을 읽으면: %d\n", by_c->r);
    delete b;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(Right*)b=非null  static_cast=非null  dynamic_cast=nullptr
by_c->r 을 읽으면: 10
```

- ★★★ **`(Right*)b` 와 `static_cast<Right*>(b)` 는 둘 다 `非null` 을 주고, `dynamic_cast` 만 `nullptr` 을 준다.**\
  객체는 실제로 `Left` 다 — 앞의 둘은 **틀린 답을 자신 있게** 준 것이다.
- ★★ **`by_c->r` 을 읽으면 `10` 이 나온다.** 그 자리에 있는 것은 `Left::l` 이다 —\
  **UB 이고, 아무도 말해 주지 않는다.**
- ★ **C 스타일 캐스트로 다운캐스트를 하면** `dynamic_cast` 를 「안 쓴 것」이 아니라 「**못 쓴 것**」이다.\
  문법이 그것을 후보에 넣지 않는다.

### (12) 다섯 층 — 무엇이 표준이고 무엇이 도구인가

C++ 에서도 **「돌아갔다」가 아무것도 증명하지 못한다.** C 갈래가 굳혀 놓은 다섯 층을 그대로 쓴다.\
★★ **이 주제는 「UB」 칸이 제일 두껍고, 그 UB 를 도구가 거의 못 본다.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | **네 캐스트가 각각 무엇을 거부하는가** · `static_cast` 의 산술 변환이 **절단**인 것 · `dynamic_cast` 포인터 실패가 **`nullptr`**, 참조 실패가 **`bad_cast`** 인 것 · `dynamic_cast` 가 **다형 타입만** 받는 것 · **C 스타일 캐스트의 풀리는 순서**와 **거기 `dynamic_cast` 가 없는 것** · `memcpy`·`std::bit_cast` 가 정의된 것 | 두 컴파일러가 같은 자리에서 막았다 · 실행 출력 | — |
| **조건부 표준** | 매크로·옵션이 있을 때만 | **`dynamic_cast`·`typeid` 가 되는 것** — ★ **`-fno-rtti` 면 아예 문법이 아니다**((9)) | `-fno-rtti` 로 던져 에러 확인 | — |
| **구현 정의** | 문서화 의무가 있다 | `typeid(...).name()` 의 **철자**(`4Left`) · 맹글링 · 진단 문구 · **오브젝트 파일의 심볼 이름과 크기** · RTTI 구현 방식 | `nm -uC` · `wc -c` · `typeid` 출력 | 경고가 한 건도 안 난다 |
| **미명시** | 몇 가지 중 하나 | **해당 없음** — 이 문서가 만든 것 중에는 없다 | — | — |
| **UB** | 아무 일이나 | ★ **진짜 `const` 객체를 `const_cast` 로 고치기**((4)) · ★ **엄격한 앨리어싱 위반**((6)) · **틀린 타입으로 `static_cast` 다운캐스트 후 접근**((11)) · private 기반으로의 `reinterpret_cast` 업캐스트 | `-O0`\~`-Os` 다섯 수준 × 두 컴파일러 · C 와 대비 | ★★ **UBSan·ASan 이 셋 다 0줄** · `const` 쪽은 **경고도 0건** · 앨리어싱 쪽은 **컴파일러에 따라 2건 대 0건** |

**「도구가 못 보는 것」을 층마다 — 전용 표**

| 사실 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | UBSan | ASan |
|---|---|---|---|---|
| `static_cast` 가 거부하는 셋 | **에러 3** | **에러 3 + `note:` 1** | — | — |
| `dynamic_cast` 를 비다형 타입에 | **에러 1** | **에러 1** | — | — |
| `-fno-rtti` 에서 `dynamic_cast`·`typeid` | **에러 4** | **에러 2** | — | — |
| ★ **진짜 `const` 를 `const_cast` 로 고치기** | **0건**(`-Wcast-qual` 을 줘도 0건) | 0건 | ★ **0건** | ★ **0건** |
| ★ **엄격한 앨리어싱 위반(함수 인자로 넘긴 판)** | **0건** | **0건** | ★ **0건** | ★ **0건** |
| 엄격한 앨리어싱 위반(그 자리에서 역참조한 판) | **`-O2` 에서 2건 · `-O0` 에서 0건** | ★ **0건** | — | — |
| 틀린 타입으로 다운캐스트한 뒤 멤버 읽기 | **0건** | **0건** | 0건 | 0건 |

- ★★★ **이 주제의 UB 는 전부 도구가 못 본다.** C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)의 결론과 같고,\
  **캐스트에 이름을 붙인 것이 그 사실을 바꾸지 않았다.** 달라진 것은 **`grep reinterpret_cast` 가 된다**는 것뿐이다.
- ★ **경고가 최적화 수준에 달린 것**도 기억할 것 — 같은 소스가 `-O0` 에서 0건, `-O2` 에서 2건이다.

## 문법 — 형태와 규칙

### 형태

```cpp
/* ex.cpp */
// static_cast 가 하는 일 — 「원래 되는 변환을 명시적으로 쓴다」
#include <cstdio>

enum class Color : unsigned char { Red, Green };
struct Base { int a = 1; };
struct Derived : Base { int b = 2; };

int main() {
    double d = 3.9;
    int    i = static_cast<int>(d);              // ① 산술 변환(절단)
    void*  v = &i;
    int*   p = static_cast<int*>(v);             // ② void* -> T*
    Derived der;
    Base*  up = static_cast<Base*>(&der);        // ③ 업캐스트
    Derived* down = static_cast<Derived*>(up);   // ④ 다운캐스트 — 검사는 없다
    int    n = static_cast<int>(Color::Green);   // ⑤ 범위 있는 열거형 -> 정수
    Color  c = static_cast<Color>(1);            // ⑥ 정수 -> 범위 있는 열거형
    std::printf("i=%d *p=%d up->a=%d down->b=%d n=%d c==Green:%d\n",
                i, *p, up->a, down->b, n,
                static_cast<int>(c == Color::Green));
}
```

규칙 불릿.

- **`static_cast<T>(x)`** — 언어가 아는 변환. 산술 · `void*`→`T*` · 업/다운캐스트 · 열거형↔정수.\
  **다운캐스트에 검사가 없다.**
- **`const_cast<T>(x)`** — `const`/`volatile` **한정자만** 바꾼다. **원래 객체가 `const` 면 쓰는 순간 UB.**
- **`reinterpret_cast<T>(x)`** — 비트를 그대로 두고 타입만. **대부분의 쓰임이 UB 이거나 UB 직전**이다.
- **`dynamic_cast<T>(x)`** — 다형 타입만. 포인터 실패는 `nullptr`, 참조 실패는 `std::bad_cast`.\
  **RTTI 가 필요하다.**
- **C 스타일 `(T)x`** — `const_cast` → `static_cast` → `static_cast`+`const_cast` → `reinterpret_cast` → `reinterpret_cast`+`const_cast` 순으로 풀린다. **`dynamic_cast` 는 후보가 아니다.**
- **함수 꼴 `T(x)`** 는 C 스타일과 같다(인자 하나일 때).
- 비트를 읽고 싶으면 **`std::bit_cast<T>(x)`(C++20)** 나 `memcpy` 를 쓴다.

### 금지 사례 — 던져서 받은 여섯

| 쓴 것 | 컴파일러 | 무엇이 나오나 |
|---|---|---|
| `static_cast<int*>(&k)`(`k` 가 `const int`) | g++ | `error: invalid 'static_cast' from type 'const int*' to type 'int*'` |
| 〃 | clang | `error: static_cast from 'const int *' to 'int *' is not allowed` |
| `static_cast<Base*>(&h)`(private 상속) | g++ | `error: 'Base' is an inaccessible base of 'Hidden'` |
| 〃 | clang | `error: cannot cast 'Hidden' to its private base class 'Base'` + `note: declared private here` |
| `static_cast<int*>(&d)`(`d` 가 `double`) | g++ | `error: invalid 'static_cast' from type 'double*' to type 'int*'` |
| `dynamic_cast<PlainD*>(&p)`(가상 함수 없음) | g++ | `error: cannot 'dynamic_cast' … (source type is not polymorphic)` |
| 〃 | clang | `error: 'Plain' is not polymorphic` |
| `dynamic_cast`/`typeid` 를 `-fno-rtti` 에서 | g++ | `error: 'dynamic_cast' not permitted with '-fno-rtti'` (총 **4줄**) |
| 〃 | clang | `error: use of dynamic_cast requires -frtti` (총 **2줄**) |

### 고를 것을 손으로 돌리는 순서

1. **`static_cast` 로 써 본다.** 되면 끝이다. 대부분 여기서 끝난다.
2. 거부당하면 **거부 문구를 읽는다** — `const` 얘기면 `const_cast`, 타입이 무관하다면 `reinterpret_cast`.
3. **`const_cast` 를 쓰기 전에 묻는다** — **원래 객체가 `const` 인가?** 그렇다면 **쓰면 UB 다.** 설계를 고친다.
4. **`reinterpret_cast` 를 쓰기 전에 묻는다** — **비트만 읽고 싶은 것인가?** 그렇다면 **`std::bit_cast`/`memcpy`** 가 답이다.
5. **다운캐스트라면 묻는다** — **틀릴 수 있나?** 그렇다면 **`dynamic_cast`** 이고, 아니라면 `static_cast` 로 충분하다.
6. **`(T)x` 는 쓰지 않는다** — 1\~5 중 무엇이 일어나는지 코드가 말하지 않는다.

## 어디서 틀리나

### 1. ★★ 「이름 있는 캐스트를 쓰면 안전하다」

아니다. **`const_cast` 와 `reinterpret_cast` 는 UB 를 만드는 도구**다((4)·(6)).\
달라진 것은 **무엇을 껐는지가 코드에 남는다**는 것뿐이다.\
C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)의 「캐스트는 안전장치를 끄는 스위치」가 **그대로 유효**하다.

### 2. ★★★ 「`const_cast` UB 는 최적화를 올려야 드러난다」

**C++ 에서는 `-O0` 에서부터 드러난다**((4)). 다섯 수준 × 두 컴파일러가 **열 벌 전부 같았다.**\
★ 갈리는 것은 최적화가 아니라 **언어**다 — 같은 코드를 C 로 던지면 `-O0` 에서 `k=99` 다.\
**「여러 최적화 수준을 돌려라」가 이 자리를 잡아 주지 않는다.**

### 3. ★★ 「엄격한 앨리어싱은 `-O2` 부터 문다」

**여기서는 `-O1` 부터**였다((6)). C 편은 **`-O2`** 를 경계로 실측했다.\
★ **경계는 소스 모양과 컴파일러에 달렸다** — 숫자를 외우지 말고 **자기 코드로 다섯 수준을 돌려라.**

### 4. ★★ 「`-Wall -Wextra` 면 앨리어싱 위반은 잡힌다」

**함수 인자로 넘긴 판은 g++·clang 둘 다 0건**이다((6)).\
**그 자리에서 역참조한 판만** g++ 가 `-O2` 에서 2건을 낸다 — **clang 은 그것도 0건**이다((7)).\
★ 그리고 **UBSan 도 ASan 도 0줄**이다.

### 5. ★★ 「C 스타일 캐스트로도 `dynamic_cast` 가 된다」

**절대 안 된다**((11)). `(Right*)b` 는 `static_cast` 로 풀려 **검사 없이 통과**하고,\
그 포인터로 멤버를 읽으면 **엉뚱한 값**(`10`)이 나온다.

### 6. ★ 「`dynamic_cast` 는 어디에나 쓸 수 있다」

**다형 타입**(가상 함수가 하나 이상)에만 쓴다((9)) — 아니면 **컴파일 에러**다.\
그리고 **`-fno-rtti` 빌드에서는 문법이 아니다.**

### 7. ★ 「`typeid` 와 `dynamic_cast` 는 같은 질문을 한다」

다르다((8)). `dynamic_cast<Left*>` 는 **「`Left` 이거나 그 파생인가」**,\
`typeid(x) == typeid(Left)` 는 「**정확히 `Left` 인가**」를 묻는다.

### 8. ★ 「`reinterpret_cast` 로 비트를 읽는 게 제일 빠르다」

값도 기계어도 같다((7)) — C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)이\
`memcpy` 가 **한 글자도 다르지 않은 기계어**를 낸다고 실측해 두었다.\
★ **「성능 때문에」라는 근거는 여기서 사라진다.** C++20 에는 `std::bit_cast` 도 있다.

### 9. ★ 「`static_cast` 다운캐스트는 컴파일러가 검사해 준다」

안 해 준다((1)·(11)). **믿고 넘어간다.** 틀리면 그 뒤가 전부 UB 다.

### 10. 「`(Base*)&h` 가 되니까 private 상속도 업캐스트가 되는 것이다」

`reinterpret_cast` 로 풀린 것이다((11)) — **주소 보정이 없다.**\
단일 상속에서는 우연히 맞지만 **다중 상속에서는 틀린 주소**가 된다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| **네 캐스트가 각각 무엇을 거부하는가** | **언어** |
| **C 스타일 캐스트의 풀리는 순서**와 거기 `dynamic_cast` 가 **없는 것** | **언어** |
| `dynamic_cast` 포인터 실패 = `nullptr`, 참조 실패 = `std::bad_cast` | **언어** |
| `dynamic_cast` 가 **다형 타입만** 받는 것 | **언어** |
| `static_cast` 의 부동→정수가 **절단**인 것 | **언어** |
| `memcpy`·`std::bit_cast` 가 **정의된** 것 | **언어**(`bit_cast` 는 C++20) |
| ★ **`dynamic_cast`·`typeid` 가 아예 쓸 수 있는지** | ★ **조건부** — `-fno-rtti` 면 문법이 아니다 |
| `typeid(...).name()` 이 **`4Left`** 인 것 | **플랫폼 ABI.** 사람이 읽을 이름을 보장하지 않는다 |
| **`__dynamic_cast` 라는 심볼 이름**과 **오브젝트 크기 1232/2704** | **이 컴파일러·ABI 의 구현.** 결정적이되 보장은 아니다 |
| ★ **엄격한 앨리어싱 경계가 `-O1`** 인 것 | ★ **관찰이다.** UB 의 결과이므로 **보장이 아니다** |
| ★ **`const_cast` UB 가 열 벌에서 같았던 것** | ★ **관찰이다.** 같은 이유로 보장이 아니다 |
| 진단 문구 · 에러를 **몇 개로 세는가**(`-fno-rtti` 에서 4 대 2) | **컴파일러 구현** |
| `-Wstrict-aliasing=3` 이 **1건**인 것 | **이 소스 모양에서의 gcc 구현.** C 편은 같은 플래그로 0건을 봤다 |

## 언제 쓰고 언제 안 쓰나

**`static_cast`** — 기본값. 캐스트가 필요하면 **먼저 이것**.

**`const_cast`** — **원래 `const` 가 아닌 것**을 `const` 경로로 받았을 때만.\
주로 **C API 경계**(`char*` 를 받는 옛 함수)다. ★ 그 외에는 **설계가 잘못된 신호**로 읽는다.

**`reinterpret_cast`** — 하드웨어 레지스터 주소 · 직렬화 버퍼 · 타입 소거 경계.\
★ **비트만 읽고 싶은 것이면 `std::bit_cast`/`memcpy` 가 답이다.**

**`dynamic_cast`** — 기반 포인터가 **틀릴 수 있을 때**.\
★ 자주 쓰게 되면 **설계를 의심한다** — 가상 함수 하나로 풀리는 경우가 많다(목록의 **19번 주제**).\
`-fno-rtti` 빌드에서는 **쓸 수 없으므로** 대안을 미리 정해 둔다(태그 필드·`std::variant`).

**C 스타일 `(T)x`** — **안 쓴다.** 무엇이 일어나는지 코드가 말하지 않고, `grep` 도 안 된다.\
★ 예외는 **C 헤더와 공유하는 코드**뿐이다.

## 핵심 문장

1. **네 캐스트는 C 의 괄호 하나를 쪼갠 것이다** — 무엇을 끄는지가 이름에 적힌다.
2. **`static_cast` 가 거부하는 셋이 나머지 도구의 일자리다** — 거부 문구가 다음 도구를 가리킨다.
3. **이름이 붙어도 UB 는 그대로다** — `const_cast`·`reinterpret_cast` 의 UB 를 **어떤 도구도 못 봤다.**
4. **`const_cast` UB 는 C++ 에서 `-O0` 부터 드러난다** — 갈리는 것은 최적화가 아니라 **언어**다.
5. **`dynamic_cast` 만 실행 시간에 물어본다** — 그 값은 오브젝트 파일에 `__dynamic_cast` 로 적힌다.
6. **C 스타일 캐스트는 `dynamic_cast` 가 되지 않는다** — 검사만은 괄호로 얻을 수 없다.

## 관련 자료

- [C 갈래 `05-explicit-casts-and-pointer-conversions/`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/) —\
  **C 스타일 캐스트의 정본.** 값/해석 변환의 어셈블리 증명 · 정렬 · 엄격한 앨리어싱 10벌 · `const` 벗기기 UB ·\
  함수 포인터 · **캐스트가 끄는 경고**가 전부 거기 있다.\
  여기는 **넷으로 쪼갠 뒤 무엇이 달라지고 무엇이 그대로인가**부터.
- [C 갈래 `03-integer-promotion-and-usual-arithmetic-conversions/`](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/) —\
  `static_cast<int>(3.9)` 가 왜 **절단**인지, 부호가 섞이면 무슨 일이 나는지.
- [**01번 형제**](../01-function-overloading-and-overload-resolution/) — 캐스트로 **오버로드 후보의 계단을 하나로 만드는** 처방이 거기 있다.
- [**02번 형제**](../02-enum-class-and-scoped-enumerations/) — (1)의 ⑤⑥이 그 주제의 담장을 넘는 도구다.\
  ★ 그리고 **범위 밖 값 캐스트가 UB 가 되는 경계**가 거기 있다.
- 목록의 **10번 주제**(`const` 정확성) — `const_cast` 를 **안 쓰게 만드는** 설계.
- 목록의 **19번 주제**(가상 함수) — `dynamic_cast` 를 **안 쓰게 만드는** 설계. vtable 이 무엇인지도 거기다.
- 목록의 **47번 주제**(`variant`) — 「여럿 중 하나」를 **RTTI 없이** 하는 법.

## 용어 풀이

> **`static_cast<T>(x)`** — 언어가 아는 변환을 명시적으로. **검사는 없다.**

> **`const_cast<T>(x)`** — `const`/`volatile` 한정자만 더하거나 뺀다.

> **`reinterpret_cast<T>(x)`** — 비트를 그대로 두고 타입만 바꾼다.

> **`dynamic_cast<T>(x)`** — 실행 중에 실제 타입을 확인하고 맞을 때만 바꾼다.\
> 포인터면 `nullptr`, 참조면 `std::bad_cast`.

> **RTTI(Run-Time Type Information)** — 실행 중 타입 확인 장치. `-fno-rtti` 로 끌 수 있다.

> **다형 타입(polymorphic type)** — **가상 함수가 하나 이상** 있는 클래스. `dynamic_cast` 의 전제다.

> **타입 펀닝(type punning)** — 같은 비트를 다른 타입으로 읽는 것.\
> `reinterpret_cast` 로 하면 **UB**, `memcpy`·`std::bit_cast` 로 하면 **정의된다.**

> **엄격한 앨리어싱(strict aliasing)** — 「서로 다른 타입의 포인터는 같은 메모리를 가리키지 않는다」는\
> 컴파일러의 가정. 규칙 자체의 정본은 C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)이다.

> **`std::bit_cast<T>(x)`(C++20)** — 비트를 그대로 옮기는 정의된 방법. `constexpr` 에서도 쓸 수 있다.

## 더 들어가면

- **`dynamic_cast` 의 비용** — (10)이 「호출이 생긴다」까지 보였다.\
  **얼마나 느린가**는 계층 깊이·다중 상속에 달려 있고 **이 문서는 재지 않았다**(수치를 적으려면 벤치마크가 따로 필요하다).
- **다중 상속에서의 캐스트** — 업캐스트가 **주소 보정**을 한다. `reinterpret_cast` 가 위험한 진짜 이유다.\
  정본은 목록의 **19번 주제**의 자매 주제로 미뤄져 있다.
- **`dynamic_cast<void*>(p)`** — 최상위 객체의 시작 주소를 얻는 특수 형태다. 이 문서는 안 던졌다.
- **`std::any` 와 `std::variant`** — RTTI 없이 「여럿 중 하나」를 하는 표준 도구. 목록의 **47번 주제**.
- **`union` 을 통한 타입 펀닝** — **C 에서는 허용되고 C++ 에서는 아니다.**\
  C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)이 그 차이를 적어 두고 **던져 보지는 않았다.**\
  ★ 이 문서도 안 던졌다 — `std::bit_cast` 가 C++20 의 답이라 그쪽을 실측했다.
