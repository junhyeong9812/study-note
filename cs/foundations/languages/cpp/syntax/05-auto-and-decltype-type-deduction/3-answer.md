# cpp/syntax/05 — `auto`·`decltype` 과 타입 추론 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 타입·출력·경고·에러는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이라 질문 쪽 발췌와 어긋날 수 있다 —\
> 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★★★ 이 주제의 **주력 창은 의도적 타입 에러**(`TypeOf<T>`)다. 타입을 찍는 블록은
> 긴 진단에서 **타입 줄만 남기는 필터**를 배너에 적어 두었다 — 실린 것은 **그 명령의 전체 출력**이다.
> **읽는 법** — 읽을 것은 **`TypeOf<...>` 의 꺾쇠 안**이다. 그 줄이 곧 답이다.\
> UB 가 걸린 것은 6번 하나뿐이고, **그 UB 가 만든 값은 싣지 않았다**(흔들리는 칸).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 「함수 매개변수처럼 받는다」 — 맨 위 `const` 와 참조가 떨어진다

**출력**

```text
===== 소스: dedu01.cpp =====
// auto 가 무엇을 떨어뜨리나 — 아홉 줄
template <class T> struct TypeOf;   // 선언만 — 정의가 없다

int main() {
    int        i  = 0;
    const int  ci = 0;
    const int& cr = i;
    const int* cp = &i;
    int* const pc = &i;

    auto a1 = ci;         // ① 맨 위 const
    auto a2 = cr;         // ② 참조 + const
    auto a3 = cp;         // ③ 가리키는 곳의 const
    auto a4 = pc;         // ④ 포인터 자신의 const
    auto& b1 = ci;        // ⑤ auto&
    const auto& b2 = i;   // ⑥ const auto&
    auto&& c1 = i;        // ⑦ 전달 참조에 lvalue
    auto&& c2 = 1;        // ⑧ 전달 참조에 rvalue
    auto  d1 = cr + 0;    // ⑨ 식의 결과

    TypeOf<decltype(a1)> t1; TypeOf<decltype(a2)> t2; TypeOf<decltype(a3)> t3;
    TypeOf<decltype(a4)> t4; TypeOf<decltype(b1)> t5; TypeOf<decltype(b2)> t6;
    TypeOf<decltype(c1)> t7; TypeOf<decltype(c2)> t8; TypeOf<decltype(d1)> t9;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu01.cpp -o ex 2>&1 | grep 'incomplete type' (cc exit=1) =====
dedu01.cpp:21:26: error: aggregate ‘TypeOf<int> t1’ has incomplete type and cannot be defined
dedu01.cpp:21:51: error: aggregate ‘TypeOf<int> t2’ has incomplete type and cannot be defined
dedu01.cpp:21:76: error: aggregate ‘TypeOf<const int*> t3’ has incomplete type and cannot be defined
dedu01.cpp:22:26: error: aggregate ‘TypeOf<int*> t4’ has incomplete type and cannot be defined
dedu01.cpp:22:51: error: aggregate ‘TypeOf<const int&> t5’ has incomplete type and cannot be defined
dedu01.cpp:22:76: error: aggregate ‘TypeOf<const int&> t6’ has incomplete type and cannot be defined
dedu01.cpp:23:26: error: aggregate ‘TypeOf<int&> t7’ has incomplete type and cannot be defined
dedu01.cpp:23:51: error: aggregate ‘TypeOf<int&&> t8’ has incomplete type and cannot be defined
dedu01.cpp:23:76: error: aggregate ‘TypeOf<int> t9’ has incomplete type and cannot be defined
```

**왜 그런가**

| 줄 | 쓴 것 | 타입 | 무엇이 떨어졌나 |
|---|---|---|---|
| ① | `auto a1 = ci;`(`const int`) | **`int`** | 맨 위 `const` |
| ② | `auto a2 = cr;`(`const int&`) | **`int`** | 참조 + `const` |
| ③ | `auto a3 = cp;`(`const int*`) | ★ **`const int*`** | ★ **아무것도** |
| ④ | `auto a4 = pc;`(`int* const`) | **`int*`** | 맨 위 `const` |
| ⑤ | `auto& b1 = ci;` | **`const int&`** | — `auto&` 는 `const` 를 안 뗀다 |
| ⑥ | `const auto& b2 = i;` | **`const int&`** | — 직접 붙였다 |
| ⑦ | `auto&& c1 = i;`(lvalue) | ★ **`int&`** | 전달 참조 |
| ⑧ | `auto&& c2 = 1;`(rvalue) | ★ **`int&&`** | 전달 참조 |
| ⑨ | `auto d1 = cr + 0;` | **`int`** | 식의 결과가 이미 prvalue |

- ★★★ **규칙 한 문장** — 「**`auto x = e;` 는 `template <class T> void f(T x)` 에 `e` 를 넘긴 것과 같은 추론이다.**」
- ★★ **①과 ③을 가르는 것은** 「`const` 가 어디 붙었나」다.\
  `const int*` 의 `const` 는 **가리키는 대상**에 붙어 **타입의 일부**이고,\
  `int* const` 의 `const` 는 **포인터 자신**에 붙어 **맨 위**다. **맨 위 것만** 떨어진다.\
  선언을 읽는 규칙의 정본은 C 갈래 [`01번`](../../../c/syntax/01-declaration-syntax-and-reading/)이다.
- ★★ **⑦과 ⑧이 다른 이유** — `auto&&` 는 **전달 참조**라 **받은 값 범주에 따라** 타입이 정해진다.\
  lvalue 면 `T&`, rvalue 면 `T&&`. 정본은 목록의 **09번 주제**다.

**clang 도 같은 타입을 답한다**(문구만 다르다).

```text
===== 소스: dedu01.cpp =====
// auto 가 무엇을 떨어뜨리나 — 아홉 줄
template <class T> struct TypeOf;   // 선언만 — 정의가 없다

int main() {
    int        i  = 0;
    const int  ci = 0;
    const int& cr = i;
    const int* cp = &i;
    int* const pc = &i;

    auto a1 = ci;         // ① 맨 위 const
    auto a2 = cr;         // ② 참조 + const
    auto a3 = cp;         // ③ 가리키는 곳의 const
    auto a4 = pc;         // ④ 포인터 자신의 const
    auto& b1 = ci;        // ⑤ auto&
    const auto& b2 = i;   // ⑥ const auto&
    auto&& c1 = i;        // ⑦ 전달 참조에 lvalue
    auto&& c2 = 1;        // ⑧ 전달 참조에 rvalue
    auto  d1 = cr + 0;    // ⑨ 식의 결과

    TypeOf<decltype(a1)> t1; TypeOf<decltype(a2)> t2; TypeOf<decltype(a3)> t3;
    TypeOf<decltype(a4)> t4; TypeOf<decltype(b1)> t5; TypeOf<decltype(b2)> t6;
    TypeOf<decltype(c1)> t7; TypeOf<decltype(c2)> t8; TypeOf<decltype(d1)> t9;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic dedu01.cpp -o ex 2>&1 | grep 'implicit instantiation' (cc exit=1) =====
dedu01.cpp:21:26: error: implicit instantiation of undefined template 'TypeOf<int>'
dedu01.cpp:21:51: error: implicit instantiation of undefined template 'TypeOf<int>'
dedu01.cpp:21:76: error: implicit instantiation of undefined template 'TypeOf<const int *>'
dedu01.cpp:22:26: error: implicit instantiation of undefined template 'TypeOf<int *>'
dedu01.cpp:22:51: error: implicit instantiation of undefined template 'TypeOf<const int &>'
dedu01.cpp:22:76: error: implicit instantiation of undefined template 'TypeOf<const int &>'
dedu01.cpp:23:26: error: implicit instantiation of undefined template 'TypeOf<int &>'
dedu01.cpp:23:51: error: implicit instantiation of undefined template 'TypeOf<int &&>'
dedu01.cpp:23:76: error: implicit instantiation of undefined template 'TypeOf<int>'
```

### 2. ★★★ 괄호 하나가 「이름」을 「식」으로 바꾼다

**출력**

```text
===== 소스: dedu02.cpp =====
// decltype 은 「식을 그대로 베낀다」 — 괄호 하나가 답을 바꾼다
#include <vector>

template <class T> struct TypeOf;

struct S { int m; };
int  f(double);
int& g();

int main() {
    int i = 0;
    const int ci = 0;
    S s{0};
    int arr[3]{};
    std::vector<int> v{1, 2, 3};

    TypeOf<decltype(i)>      y1;   // 이름
    TypeOf<decltype((i))>    y2;   // 괄호를 씌운 식
    TypeOf<decltype(ci)>     y3;
    TypeOf<decltype((ci))>   y4;
    TypeOf<decltype(s.m)>    y5;   // 멤버 이름
    TypeOf<decltype((s.m))>  y6;
    TypeOf<decltype(f)>      y7;   // 함수 이름
    TypeOf<decltype(f(1.0))> y8;   // 호출 식
    TypeOf<decltype(g())>    y9;   // 참조를 돌려주는 호출
    TypeOf<decltype(arr)>    ya;   // 배열
    TypeOf<decltype(v[0])>   yb;   // 첨자 식
    TypeOf<decltype(i + 1)>  yc;   // 계산 식
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu02.cpp -o ex 2>&1 | grep 'incomplete type' (cc exit=1) =====
dedu02.cpp:17:30: error: aggregate ‘TypeOf<int> y1’ has incomplete type and cannot be defined
dedu02.cpp:18:30: error: aggregate ‘TypeOf<int&> y2’ has incomplete type and cannot be defined
dedu02.cpp:19:30: error: aggregate ‘TypeOf<const int> y3’ has incomplete type and cannot be defined
dedu02.cpp:20:30: error: aggregate ‘TypeOf<const int&> y4’ has incomplete type and cannot be defined
dedu02.cpp:21:30: error: aggregate ‘TypeOf<int> y5’ has incomplete type and cannot be defined
dedu02.cpp:22:30: error: aggregate ‘TypeOf<int&> y6’ has incomplete type and cannot be defined
dedu02.cpp:23:30: error: aggregate ‘TypeOf<int(double)> y7’ has incomplete type and cannot be defined
dedu02.cpp:24:30: error: aggregate ‘TypeOf<int> y8’ has incomplete type and cannot be defined
dedu02.cpp:25:30: error: aggregate ‘TypeOf<int&> y9’ has incomplete type and cannot be defined
dedu02.cpp:26:30: error: aggregate ‘TypeOf<int [3]> ya’ has incomplete type and cannot be defined
dedu02.cpp:27:30: error: aggregate ‘TypeOf<int&> yb’ has incomplete type and cannot be defined
dedu02.cpp:28:30: error: aggregate ‘TypeOf<int> yc’ has incomplete type and cannot be defined
```

**왜 그런가**

| 쓴 것 | 타입 | 규칙 |
|---|---|---|
| `decltype(i)` | `int` | **이름** — 선언 타입 그대로 |
| `decltype((i))` | ★ **`int&`** | ★ **식** — lvalue 라 `T&` |
| `decltype(ci)` | `const int` | 이름 — `const` 가 남는다 |
| `decltype((ci))` | `const int&` | 식 |
| `decltype(s.m)` | `int` | **멤버 이름**도 이름이다 |
| `decltype((s.m))` | ★ **`int&`** | 괄호를 치면 식 |
| `decltype(f)` | `int(double)` | 함수 이름 — **감쇠하지 않는다** |
| `decltype(f(1.0))` | `int` | **호출 식** — prvalue |
| `decltype(g())` | ★ **`int&`** | `g` 가 `int&` 를 돌려주니 lvalue 식 |
| `decltype(arr)` | ★ **`int [3]`** | 배열 이름 — **감쇠하지 않는다** |
| `decltype(v[0])` | ★ **`int&`** | `operator[]` 가 `int&` 를 돌려준다 |
| `decltype(i + 1)` | `int` | prvalue 식 |

- ★★★ **이름이면 「선언 타입」, 식이면 「타입 + 값 범주」다.** lvalue 식은 **`T&`** 가 된다.\
  값 범주와 `&`/`&&` 의 대응은 목록의 **08번 주제**가 정본이다.
- ★★ **`decltype(f)` 와 `decltype(f(1.0))` 의 차이** — 앞은 **함수 자체**(`int(double)`),\
  뒤는 **부른 결과**(`int`)다. ★ 그런데 **부르지는 않는다** — `decltype` 은 **식을 평가하지 않는다.**\
  이 소스의 `f` 는 **선언만 있고 정의가 없는데도** 컴파일이 여기까지 온다.
- ★★ **`decltype(arr)` 는 감쇠하지 않는다.** `auto a = arr;` 는 `int*` 인데(3번) **`decltype` 은 `int [3]`** 이다.
- ★ **`decltype(v[0])` 이 참조이고 `decltype(i + 1)` 이 아닌 이유** — 앞은 **그 자리를 가리키는 lvalue**,\
  뒤는 **계산해서 나온 값**(prvalue)이다.

### 3. ★ `int*` · `int (&)[3]` · 함수 포인터 · 함수 참조

**출력**

```text
===== 소스: dedu03.cpp =====
// 배열과 함수 — auto 는 감쇠시키고 auto& 는 안 시킨다
template <class T> struct TypeOf;

int f(double);

int main() {
    int arr[3]{};
    auto  a = arr;
    auto& b = arr;
    auto  c = f;
    auto& d = f;
    TypeOf<decltype(a)> t1; TypeOf<decltype(b)> t2;
    TypeOf<decltype(c)> t3; TypeOf<decltype(d)> t4;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu03.cpp -o ex 2>&1 | grep 'incomplete type' (cc exit=1) =====
dedu03.cpp:12:25: error: aggregate ‘TypeOf<int*> t1’ has incomplete type and cannot be defined
dedu03.cpp:12:49: error: aggregate ‘TypeOf<int (&)[3]> t2’ has incomplete type and cannot be defined
dedu03.cpp:13:25: error: aggregate ‘TypeOf<int (*)(double)> t3’ has incomplete type and cannot be defined
dedu03.cpp:13:49: error: aggregate ‘TypeOf<int (&)(double)> t4’ has incomplete type and cannot be defined
```

**왜 그런가**

| 쓴 것 | 타입 |
|---|---|
| `auto a = arr;`(`int[3]`) | ★ **`int*`** — 크기가 사라졌다 |
| `auto& b = arr;` | ★ **`int (&)[3]`** — 크기가 남았다 |
| `auto c = f;`(`int(double)`) | **`int (*)(double)`** |
| `auto& d = f;` | **`int (&)(double)`** |

- ★★ **감쇠를 막는 쪽은 `auto&`** 다.
- ★★ **이것이 「매개변수처럼 받는다」의 직접적인 결과**다 — 함수 매개변수에서 배열이 포인터가 되는 것과\
  **같은 규칙**이고, 정본은 C 갈래\
  [`16-array-pointer-decay-and-function-parameters/`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/)다.
- ★ 함수 이름에 `auto&` 를 붙이면 **함수 참조**(`int (&)(double)`)다. 부를 수 있고, **재대입은 안 된다.**
- ★ 크기를 지키려면 `auto&`·`std::array`·`std::span` 이다.

### 4. ★★★ `b0` 이 옛 값을 못 들고 있다 — 프록시다

**출력**

```text
===== 소스: dedu04.cpp =====
// auto 가 「값을 복사한다」가 아닌 자리 — vector<bool> 의 프록시
#include <cstdio>
#include <vector>

int main() {
    std::vector<bool> vb{true, false, true};
    std::vector<char> vc{'a', 'b', 'c'};
    auto b0 = vb[0];
    auto c0 = vc[0];
    vb[0] = false;       // 원본을 건드린다
    vc[0] = 'z';
    std::printf("b0 = %d   (vb[0] = %d)\n", static_cast<int>(b0), static_cast<int>(vb[0]));
    std::printf("c0 = %c   (vc[0] = %c)\n", c0, vc[0]);
    std::printf("sizeof(b0) = %zu   sizeof(c0) = %zu\n", sizeof(b0), sizeof(c0));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
b0 = 0   (vb[0] = 0)
c0 = a   (vc[0] = z)
sizeof(b0) = 16   sizeof(c0) = 1
```

**왜 그런가**

- ★★★ **`b0` 은 값이 아니라 대리인이다.** `vb[0] = false;` 로 원본을 바꿨더니 **`b0` 도 `0` 이 됐다.**\
  같은 자리를 `vector<char>` 로 하면 `c0` 은 **`'a'` 그대로**다 — 그쪽은 진짜 복사다.
- ★★ **`sizeof(b0) = 16`** 이 결정적 증거다. `bool` 하나가 16바이트일 리 없다.\
  `std::vector<bool>::reference` 라는 **프록시 객체**(워드 포인터 + 비트 마스크)가 복사된 것이다.\
  `sizeof(c0) = 1` 과 나란히 놓으면 바로 보인다.
- ★★ **`auto` 가 「값을 복사한다」인데 왜 이런 일이 나나** — `auto` 는 **초기값 식의 타입**을 복사한다.\
  그 식의 타입이 **이미 프록시**이므로 복사되는 것도 프록시다. `auto` 는 정직하게 일했다.
- ★ **`std::vector<bool>` 은 비트로 눌러 담는 특수화**라 `operator[]` 가 `bool&` 를 **못 돌려준다.**
- ★★ **고치는 법은 타입을 못 박는 것** — `bool b0 = vb[0];` 또는 `static_cast<bool>(vb[0])`.\
  ★ 「거의 언제나 `auto`」의 **가장 큰 예외**다.
- ★ clang 도 같은 답이다.

```text
===== 소스: dedu04.cpp =====
// auto 가 「값을 복사한다」가 아닌 자리 — vector<bool> 의 프록시
#include <cstdio>
#include <vector>

int main() {
    std::vector<bool> vb{true, false, true};
    std::vector<char> vc{'a', 'b', 'c'};
    auto b0 = vb[0];
    auto c0 = vc[0];
    vb[0] = false;       // 원본을 건드린다
    vc[0] = 'z';
    std::printf("b0 = %d   (vb[0] = %d)\n", static_cast<int>(b0), static_cast<int>(vb[0]));
    std::printf("c0 = %c   (vc[0] = %c)\n", c0, vc[0]);
    std::printf("sizeof(b0) = %zu   sizeof(c0) = %zu\n", sizeof(b0), sizeof(c0));
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic dedu04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
b0 = 0   (vb[0] = 0)
c0 = a   (vc[0] = z)
sizeof(b0) = 16   sizeof(c0) = 1
```

### 5. ★★ `decltype(auto)` 만 `int&` 를 돌려준다

**출력**

```text
===== 소스: dedu05.cpp =====
// 반환 타입 — auto 는 참조를 떨어뜨리고 decltype(auto) 는 남긴다
#include <cstdio>
#include <vector>

std::vector<int> g_v{10, 20, 30};

auto           f1(int i) { return g_v[i]; }
decltype(auto) f2(int i) { return g_v[i]; }

int main() {
    f2(0) = 99;
    std::printf("g_v[0] = %d  (f2 로 고쳤다)\n", g_v[0]);
    std::printf("f1(0)  = %d  (복사본이다)\n", f1(0));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
g_v[0] = 99  (f2 로 고쳤다)
f1(0)  = 99  (복사본이다)
```

```text
===== 소스: dedu06.cpp =====
// auto 반환에는 대입할 수 없다
#include <vector>

std::vector<int> g_v{10, 20, 30};
auto f1(int i) { return g_v[i]; }

int main() { f1(0) = 99; }
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu06.cpp -o ex (cc exit=1) =====
dedu06.cpp: In function ‘int main()’:
dedu06.cpp:7:16: error: lvalue required as left operand of assignment
    7 | int main() { f1(0) = 99; }
      |              ~~^~~
```

**왜 그런가**

| 반환 타입 | 추론 결과 | `f(0) = 99;` |
|---|---|---|
| `auto f1(int i)` | **`int`** — `auto` 규칙이라 참조가 떨어진다 | ★ **에러** — `lvalue required as left operand of assignment` |
| `decltype(auto) f2(int i)` | ★ **`int&`** — `decltype` 규칙이라 참조가 남는다 | **된다** — `g_v[0]` 이 **99** 가 된다 |

- ★★ **`g_v[i]` 는 `int&` 를 돌려주는 식**이다((2)의 `decltype(v[0])`).\
  `auto` 는 거기서 **참조를 떼어** 복사본을 만들고, `decltype(auto)` 는 **그대로 남긴다.**
- ★★★ **래퍼에서 `auto` 를 쓰면 성능이 아니라 「의미」가 바뀐다** — `wrapper(v, 0) = 99;` 가\
  원본을 못 고치게 된다. **그때 `decltype(auto)` 를 쓴다.**
- ★ 그 외의 자리에서는 `auto` 반환이 **더 안전하다** — 6번이 그 이유다.

### 6. ★★ `int&` — 경고만 나고 `cc exit=0` 이다

**출력**

```text
===== 소스: dedu07.cpp =====
// decltype(auto) 가 참조를 남긴다는 것은 댕글링도 남긴다는 뜻이다
int make() { return 42; }

decltype(auto) leak() {
    int local = make();
    return (local);          // 괄호 하나 때문에 int& 가 된다
}

int main() { return leak(); }
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu07.cpp -o ex (cc exit=0) =====
dedu07.cpp: In function ‘decltype(auto) leak()’:
dedu07.cpp:6:13: warning: reference to local variable ‘local’ returned [-Wreturn-local-addr]
    6 |     return (local);          // 괄호 하나 때문에 int& 가 된다
      |            ~^~~~~~
dedu07.cpp:5:9: note: declared here
    5 |     int local = make();
      |         ^~~~~
```

```text
===== 소스: dedu07.cpp =====
// decltype(auto) 가 참조를 남긴다는 것은 댕글링도 남긴다는 뜻이다
int make() { return 42; }

decltype(auto) leak() {
    int local = make();
    return (local);          // 괄호 하나 때문에 int& 가 된다
}

int main() { return leak(); }
===== clang++ -std=c++20 -Wall -Wextra -pedantic dedu07.cpp -o ex 2>&1 | cat (cc exit=0) =====
dedu07.cpp:6:13: warning: reference to stack memory associated with local variable 'local' returned [-Wreturn-stack-address]
    6 |     return (local);          // 괄호 하나 때문에 int& 가 된다
      |             ^~~~~
1 warning generated.
```

```text
===== 소스: dedu07.cpp =====
// decltype(auto) 가 참조를 남긴다는 것은 댕글링도 남긴다는 뜻이다
int make() { return 42; }

decltype(auto) leak() {
    int local = make();
    return (local);          // 괄호 하나 때문에 int& 가 된다
}

int main() { return leak(); }
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 -fsanitize=undefined dedu07.cpp -o ex && ./ex (cc exit=0 · run exit=139) =====
dedu07.cpp: In function ‘decltype(auto) leak()’:
dedu07.cpp:6:13: warning: reference to local variable ‘local’ returned [-Wreturn-local-addr]
    6 |     return (local);          // 괄호 하나 때문에 int& 가 된다
      |            ~^~~~~~
dedu07.cpp:5:9: note: declared here
    5 |     int local = make();
      |         ^~~~~
dedu07.cpp:6:18: runtime error: reference binding to null pointer of type 'int'
dedu07.cpp:9:26: runtime error: load of null pointer of type 'int'
```

**왜 그런가**

| 물음 | 답 |
|---|---|
| `leak()` 의 반환 타입 | ★ **`int&`** — `return (local);` 의 **괄호** 때문이다 |
| 컴파일되는가 | ★★ **된다. `cc exit=0`** — 경고 한 줄뿐이다 |
| 경고 이름 | g++ **`-Wreturn-local-addr`** · clang **`-Wreturn-stack-address`** |
| UBSan | ★ **`runtime error:` 두 줄** — `reference binding to null pointer` + `load of null pointer` |
| 실행 종료 코드 | ★ **139**(SIGSEGV) |
| `return local;`(괄호 없이) | ★ **`int`** 가 되어 **복사본**을 돌려준다 — 문제가 사라진다 |

- ★★★ **괄호 하나가 `int` 를 `int&` 로 바꾼다**((2)의 `decltype((i))` 규칙 그대로).\
  `decltype(auto)` 를 쓸 때 **`return (x);` 를 쓰면 안 되는** 이유가 이것이다.
- ★★ **이 주제의 UB 는 도구가 본다.** 형제 [`03번`](../03-four-cast-operators/)의 UB(앨리어싱·`const` 벗기기)가\
  **UBSan·ASan 어디에도 안 걸린 것과 반대**다 — 「sanitizer 가 조용하다」를 일반 규칙으로 외우면 틀린다.
- ★ **UB 가 만든 값 자체는 싣지 않았다.** 근거로 쓰는 것은 「경고가 났다」·「UBSan 두 줄」·「`run exit=139`」다.

### 7. 복사 **2 · 0 · 0** — 그리고 루프 전의 2 는 다른 것이 냈다

**출력**

```text
===== 소스: dedu08.cpp =====
// 범위 for 에서 auto 를 어떻게 쓰느냐 — 복사가 몇 번 일어나나
#include <cstdio>
#include <vector>

struct Loud {
    int v;
    Loud(int x) : v(x) {}
    Loud(const Loud& o) : v(o.v) { std::printf("  복사 %d\n", v); }
};

int main() {
    std::printf("[벡터를 만든다]\n");
    std::vector<Loud> vs{Loud(1), Loud(2)};
    std::printf("[for (auto x : vs)]\n");
    for (auto x : vs) { (void)x; }
    std::printf("[for (auto& x : vs)]\n");
    for (auto& x : vs) { (void)x; }
    std::printf("[for (const auto& x : vs)]\n");
    for (const auto& x : vs) { (void)x; }
    std::printf("[끝]\n");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu08.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[벡터를 만든다]
  복사 1
  복사 2
[for (auto x : vs)]
  복사 1
  복사 2
[for (auto& x : vs)]
[for (const auto& x : vs)]
[끝]
```

**왜 그런가**

| 루프 | 복사 | 왜 |
|---|---|---|
| `for (auto x : vs)` | ★ **2** | 원소마다 복사 생성자 |
| `for (auto& x : vs)` | **0** | 참조로 묶는다 |
| `for (const auto& x : vs)` | **0** | 〃 |

- ★ **`[벡터를 만든다]` 뒤의 복사 2번은 루프가 아니다** — `std::vector<Loud> vs{Loud(1), Loud(2)};` 의\
  **`initializer_list`** 가 낸 것이다. 목록의 원소는 **`const` 라 옮길 수 없어** 복사된다.\
  정본은 형제 [`04번`](../04-brace-initialization-narrowing-and-initializer-list/)이다.
- ★★ **읽기만 하면 `const auto&`** 가 기본값이다. 고칠 거면 `auto&`.
- ★ **`auto`(값)가 오히려 맞는 때** — ① 원소가 `int` 처럼 작을 때(참조가 오히려 간접 접근이다) ·\
  ② **루프 안에서 사본을 망가뜨릴 때**(원본을 지키려고 일부러 복사한다).
- ★ 프록시 컨테이너(`vector<bool>`)에서는 **`auto&` 가 안 된다** — 프록시가 prvalue 라서 `auto&&` 를 쓴다.

### 8. 에러 **셋** — `void take(auto x);` 만 된다

**출력**

```text
===== 소스: dedu09.cpp =====
// auto 가 못 쓰이는 자리 넷
struct S {
    auto m = 0;                  // ① 비정적 멤버
};

auto g;                          // ② 초기화 없는 변수

void take(auto x);               // ③ C++20 축약 템플릿 — 이건 된다
auto h();                        // ④ 정의 없이 선언만 한 반환 타입 추론 함수

int main() { return h(); }
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu09.cpp -o ex 2>&1 | grep -E 'error:|warning:' (cc exit=1) =====
dedu09.cpp:3:5: error: non-static data member declared with placeholder ‘auto’
dedu09.cpp:6:1: error: declaration of ‘auto g’ has no initializer
dedu09.cpp:11:22: error: use of ‘auto h()’ before deduction of ‘auto’
```

```text
===== 소스: dedu09.cpp =====
// auto 가 못 쓰이는 자리 넷
struct S {
    auto m = 0;                  // ① 비정적 멤버
};

auto g;                          // ② 초기화 없는 변수

void take(auto x);               // ③ C++20 축약 템플릿 — 이건 된다
auto h();                        // ④ 정의 없이 선언만 한 반환 타입 추론 함수

int main() { return h(); }
===== clang++ -std=c++20 -Wall -Wextra -pedantic dedu09.cpp -o ex 2>&1 | grep -E 'error:|warning:|generated' (cc exit=1) =====
dedu09.cpp:3:5: error: 'auto' not allowed in non-static struct member
dedu09.cpp:6:6: error: declaration of variable 'g' with deduced type 'auto' requires an initializer
dedu09.cpp:11:21: error: function 'h' with deduced return type cannot be used before it is defined
3 errors generated.
```

**왜 그런가**

| 쓴 것 | 결과 | 왜 |
|---|---|---|
| `struct S { auto m = 0; };` | **에러** | **클래스 레이아웃이 정의 시점에 정해져야** 한다 |
| `auto g;` | **에러** | 추론할 초기값이 없다 |
| `void take(auto x);` | ★ **된다** | **C++20 축약 템플릿** |
| `auto h();` 를 정의 전에 호출 | **에러** | ★ **정의를 봐야 반환 타입을 안다** |

- **에러는 셋**이다(clang 이 `3 errors generated.` 로 세어 준다).
- ★★ **`auto h();` 가 에러인 것이 「헤더에 선언만」 배치를 깬다** —\
  라이브러리 경계에서 `auto` 반환을 피하는 근거다.

`-std=c++17` 로 던지면 매개변수 `auto` 는 **에러가 아니라 경고**다.

```text
===== 소스: dedu10.cpp =====
// C++20 축약 템플릿 — auto 매개변수
#include <cstdio>

void show(auto x) { std::printf("sizeof = %zu\n", sizeof(x)); }

int main() {
    show(1);
    show(1.0);
    show('c');
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dedu10.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof = 4
sizeof = 8
sizeof = 1
```

```text
===== 소스: dedu10.cpp =====
// C++20 축약 템플릿 — auto 매개변수
#include <cstdio>

void show(auto x) { std::printf("sizeof = %zu\n", sizeof(x)); }

int main() {
    show(1);
    show(1.0);
    show('c');
}
===== g++ -std=c++17 -Wall -Wextra -pedantic dedu10.cpp -o ex 2>&1 | grep -E 'error:|warning:' (cc exit=0) =====
dedu10.cpp:4:11: warning: use of ‘auto’ in parameter declaration only available with ‘-std=c++20’ or ‘-fconcepts’
```

- ★★ **`cc exit=0`** 이다. 「`-std=c++17` 로 돌렸다」가 「C++17 로 검증했다」가 아니라는 사례가 또 나왔다 —\
  GCC 가 확장으로 받아 준다. **표준 준수를 주장하려면 `-pedantic-errors`** 다.

### 9. `auto` 의 값과 값어치

**왜 그런가**

**막아 주는 버그 둘**

- ★ **타입을 손으로 적다가 생기는 조용한 변환** — `int n = v.size();`(`size_t`→`int`)처럼\
  부호·너비가 어긋나는 자리. `auto n = v.size();` 면 안 생긴다.
- ★ **초기화를 빠뜨릴 수 없다** — `auto g;` 가 **에러**다(8번). `auto` 를 쓰면 **반드시 초기값이 있다.**

**숨기는 것 둘**

- ★★ **프록시**(4번) — 값인 줄 알았는데 대리인이다. **경고 0건**으로 값만 틀린다.
- ★ **복사 비용**(7번) — `auto x = 큰객체;` 가 한 줄에 숨는다.

**반환 타입에 쓸 때 치르는 값**

- ★★ **헤더에 선언만 둘 수 없다**(8번). 정의를 봐야 타입을 알기 때문이다 —\
  **컴파일 의존이 커지고**, 반환 타입이라는 **계약이 코드에 안 적힌다.**

**「거의 언제나 `auto`」의 경계**

- ★ ① **프록시가 걸린 첨자 접근** · ② **라이브러리 경계의 반환 타입** ·\
  ③ **독자가 타입을 알아야 읽히는 자리**(「타입이 문서」인 코드) ·\
  ④ **`auto x = {1}`** 처럼 **의도와 다른 타입**이 나오는 문법(형제 [`04번`](../04-brace-initialization-narrowing-and-initializer-list/)).

### 10. 이 주제의 지도

**왜 그런가**

- **`auto` 의 추론 규칙은 「함수 템플릿 인자 추론」과 거의 같다** — 정본은 목록의 **31번 주제**다.\
  ★ **갈리는 곳은 한 군데**, 중괄호 목록이다(`auto x = {1,2}` 는 되고 템플릿 추론은 실패한다).\
  ★ 이 문서는 **템플릿 쪽을 안 던졌다.**
- **`auto&&` 가 전달 참조가 되는 규칙**의 정본은 목록의 **09번 주제**(rvalue 참조·`move`·`forward`)이고,\
  그 밑의 **값 범주**는 목록의 **08번 주제**다.
- **`auto x = {1}` 이 `initializer_list` 가 되는 것**의 정본은 형제\
  [**04번**](../04-brace-initialization-narrowing-and-initializer-list/)이다.
- **`decltype(auto)` 로 지역을 돌려주면 생기는 문제**의 정본은 목록의 **30번 주제**(댕글링 참조와 수명)다.
- **`vector<bool>` 이 왜 프록시를 돌려주나**의 컨테이너 쪽 정본은 목록의 **41번 주제**(순차 컨테이너 선택)다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 명령으로 돌렸나 |
|---|---|---|
| `dedu01.cpp` `auto` 아홉 줄 | `int`·`int`·**`const int*`**·`int*`·`const int&`·`const int&`·**`int&`**·**`int&&`**·`int` | g++ · clang |
| `dedu02.cpp` `decltype` 열두 줄 | ★ `decltype(i)`=`int` 대 `decltype((i))`=**`int&`** · `decltype(arr)`=**`int [3]`** | g++ |
| `dedu03.cpp` 감쇠 | `int*` / **`int (&)[3]`** / `int (*)(double)` / `int (&)(double)` | g++ |
| `dedu04.cpp` 프록시 | ★★ `b0=0`(원본 따라 바뀜) · `c0=a` · **`sizeof(b0)=16`** | g++ · clang |
| `dedu05.cpp` 반환 타입 | `decltype(auto)` 로 `g_v[0]` 을 **99** 로 고쳤다 | g++ |
| `dedu06.cpp` `auto` 반환에 대입 | **에러** — `lvalue required as left operand of assignment` | g++ |
| `dedu07.cpp` 괄호 댕글링 | ★ **경고 1 · `cc exit=0`** · g++ `-Wreturn-local-addr` · clang `-Wreturn-stack-address` | g++ · clang |
| 〃 UBSan | ★ **`runtime error:` 2줄** · **`run exit=139`** | g++ `-O0 -fsanitize=undefined` |
| `dedu08.cpp` 범위 for | 복사 **2 / 0 / 0** (+ 벡터를 만들 때 2) | g++ |
| `dedu09.cpp` `auto` 금지 자리 | **에러 3** — 비정적 멤버 · 초기값 없음 · 정의 전 호출 | g++ · clang |
| `dedu10.cpp` 축약 템플릿 | `sizeof = 4 / 8 / 1` | g++ |
| 〃 `-std=c++17` | ★ **경고 1 · `cc exit=0`** — GCC 확장으로 통과 | g++ |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · libstdc++ 13)에서만** 그렇다.

- ★ **`sizeof(std::vector<bool>::reference) == 16`** — 프록시의 레이아웃은 구현이다.\
  **프록시를 돌려준다는 사실 자체는 표준**이다.
- 진단 문구 전부 · 경고 이름(`-Wreturn-local-addr` 대 `-Wreturn-stack-address`).
- ★ **매개변수 `auto` 를 `-std=c++17` 에서 경고로 받아 주는 것** — GCC 확장이다.
- `TypeOf<T>` 에러의 문구(g++ `aggregate ... has incomplete type` 대 clang `implicit instantiation of undefined template`).

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- `auto` 가 **맨 위 `cv`·참조를 떼는** 것 · **배열/함수 감쇠** · **`auto&` 는 `const` 를 안 떼는** 것 ·
  **`auto&&` 가 전달 참조**인 것.
- `decltype(이름)` 과 `decltype((식))` 이 **다른** 것 · `decltype` 이 **식을 평가하지 않는** 것 ·
  `decltype` 이 **감쇠시키지 않는** 것.
- `decltype(auto)` 가 **참조를 남기는** 것(C++14부터).
- `auto` 를 **비정적 멤버·초기값 없는 변수**에 못 쓰고, **정의 전에 `auto` 반환 함수를 못 쓰는** 것.
- `std::vector<bool>` 이 **프록시를 돌려준다**는 것.
- ★ **언제부터인가도 언어가 보장한다** — `decltype(auto)` 는 C++14, `auto x{1}` 이 `int` 인 것은 C++17,
  매개변수 `auto` 는 C++20.

**UB 의 결과라 보장이 아닌 것**(관찰로만 읽는다)

- ★ 6번의 **`run exit=139`** — SIGSEGV 로 죽은 것은 **이 판의 결과**다. UB 이므로 다른 일이 날 수도 있다.\
  근거로 쓰는 것은 「**경고가 났다**」와 「**UBSan 이 묶는 순간을 짚었다**」다.
- ★ **댕글링 참조가 읽은 값** — 이 문서는 **싣지 않았다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **템플릿 인자 추론 쪽**(`auto` 와 갈리는 유일한 자리인 중괄호 목록을 포함해서 —\
  정본이 목록의 **31번 주제**라 거기서 던진다) · **후행 반환 타입**(`auto f() -> decltype(...)`) ·\
  **`decltype(auto)` 를 변수에** 쓰기 · **구조적 바인딩의 `auto`**(목록의 **48번 주제**) ·\
  **컨셉으로 제약한 `auto`**(목록의 **36번 주제**) ·\
  **표현식 템플릿 라이브러리의 프록시**(이 문서는 표준 라이브러리 안의 사례 하나만 던졌다).
- **못 잰 것** — 없다. 이 주제의 결론은 전부 **타입 진단과 실행 출력**으로 잡힌다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★ **`sizeof(std::vector<bool>::reference)`** — libstdc++ 가 바뀌면 움직인다.
- ★ **매개변수 `auto` 가 `-std=c++17` 에서 계속 경고인지**(에러가 될 수 있다).
- `TypeOf<T>` 진단 문구와 경고 이름.
- UBSan 이 내는 줄 수(지금은 2줄).
