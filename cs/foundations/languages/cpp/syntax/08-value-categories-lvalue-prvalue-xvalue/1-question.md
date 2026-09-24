# cpp/syntax/08 — 값 범주 — lvalue·prvalue·xvalue — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 어떤 식이 **어느 칸에 들어가는지**,
> 그리고 그 칸이 **무엇을 가르는지**를 맞힐 수 있는지 묻는다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **범주는 셋이다** — lvalue · prvalue · xvalue. 답을 적을 때 **셋 중 하나로** 적어라.
> ★ **네 번째 창은 `decltype((식))` 을 정의 없는 템플릿에 넣어 타입으로 찍는 것**이다.
> 그 창의 원리(이름 대 식)는 형제 [`05번`](../05-auto-and-decltype-type-deduction/)에 있다 — 여기서는 **창만 쓴다**.
> 선행 — 형제 [`07번`](../07-references-vs-pointers/)(참조) · 형제 [`01번`](../01-function-overloading-and-overload-resolution/)(오버로드 해석).
> 이 주제는 목록의 **09·11번 주제**로 이어지는 사슬의 첫 칸이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 스무 개의 식에 이름표를 붙인다 (예측)

```cpp
/* vcat01.cpp */
// decltype((식)) 로 값 범주를 직접 묻는다 — T 면 prvalue, T& 면 lvalue, T&& 면 xvalue
#include <utility>

template <class T> struct TypeOf;   // 선언만 — 정의가 없다

struct S { int m; };

int  byval();     // 값을 돌려준다
int& bylref();    // lvalue 참조를 돌려준다
int&& byrref();   // rvalue 참조를 돌려준다

int main() {
    int i = 0, j = 0;
    int arr[3]{};
    S s{0};

    TypeOf<decltype((42))>                  v01;   // 정수 리터럴
    TypeOf<decltype(("abc"))>               v02;   // 문자열 리터럴
    TypeOf<decltype(('c'))>                 v03;   // 문자 리터럴
    TypeOf<decltype((i))>                   v04;   // 변수 이름
    TypeOf<decltype((i + 1))>               v05;   // 계산 식
    TypeOf<decltype((++i))>                 v06;   // 전위 증가
    TypeOf<decltype((i++))>                 v07;   // 후위 증가
    TypeOf<decltype((byval()))>             v08;   // 값 반환 호출
    TypeOf<decltype((bylref()))>            v09;   // T& 반환 호출
    TypeOf<decltype((byrref()))>            v10;   // T&& 반환 호출
    TypeOf<decltype((std::move(i)))>        v11;   // std::move
    TypeOf<decltype((static_cast<int&&>(i)))> v12; // 같은 캐스트를 손으로
    TypeOf<decltype((arr))>                 v13;   // 배열 이름
    TypeOf<decltype((arr[0]))>              v14;   // 첨자
    TypeOf<decltype((s.m))>                 v15;   // lvalue 의 멤버
    TypeOf<decltype((S{}))>                 v16;   // 임시 객체
    TypeOf<decltype((S{}.m))>               v17;   // prvalue 의 멤버
    TypeOf<decltype((std::move(s).m))>      v18;   // xvalue 의 멤버
    TypeOf<decltype((i ? i : j))>           v19;   // 조건 식
    TypeOf<decltype(("abc"[0]))>            v20;   // 문자열 리터럴의 첨자
}
```

- `TypeOf<...>` 의 꺾쇠 안에 **무엇이 찍히는가** — 스무 줄을 **각각** 맞힐 수 있는가?
- `int` · `int&` · `int&&` 셋 중 어느 것이 **어느 범주**를 뜻하는가?
- `v02`(문자열 리터럴)만 모양이 다른데, **무엇이 찍히는가**?
- `v16`(`S{}`)과 `v17`(`S{}.m`)은 **같은가 다른가** — 왜 그런가?
- `v10`·`v11`·`v12` 셋은 **어떤 관계**인가?

### 2. ★★ 후보를 셋 두고 다섯 가지로 부르면 (예측)

```cpp
/* vcat02.cpp */
// 값 범주가 오버로드를 가른다 — 같은 이름에 세 후보를 두고 다섯 가지 식으로 부른다
#include <cstdio>
#include <utility>

void f(int&)       { std::puts("f(int&)"); }
void f(const int&) { std::puts("f(const int&)"); }
void f(int&&)      { std::puts("f(int&&)"); }

void g(const int&) { std::puts("g(const int&)"); }
void g(int&&)      { std::puts("g(int&&)"); }

void h(const int&) { std::puts("h(const int&)"); }

int main() {
    int i = 0;
    const int ci = 0;

    std::puts("[1] 후보 셋: f(int&) / f(const int&) / f(int&&)");
    std::printf("  %-26s -> ", "f(i)          lvalue");        f(i);
    std::printf("  %-26s -> ", "f(ci)         const lvalue");  f(ci);
    std::printf("  %-26s -> ", "f(42)         prvalue");       f(42);
    std::printf("  %-26s -> ", "f(move(i))    xvalue");        f(std::move(i));
    std::printf("  %-26s -> ", "f(move(ci))   const xvalue");  f(std::move(ci));

    std::puts("[2] 후보 둘: g(const int&) / g(int&&)");
    std::printf("  %-26s -> ", "g(i)          lvalue");        g(i);
    std::printf("  %-26s -> ", "g(42)         prvalue");       g(42);
    std::printf("  %-26s -> ", "g(move(i))    xvalue");        g(std::move(i));

    std::puts("[3] 후보 하나: h(const int&)");
    std::printf("  %-26s -> ", "h(i)          lvalue");        h(i);
    std::printf("  %-26s -> ", "h(42)         prvalue");       h(42);
    std::printf("  %-26s -> ", "h(move(i))    xvalue");        h(std::move(i));
}
```

- `[1]` 의 다섯 줄이 **각각 어느 함수**로 가는가?
- `f(42)` 와 `f(std::move(i))` 는 **같은 곳으로 가는가**?
- `f(std::move(ci))` 는 어디로 가는가 — `ci` 가 `const` 인 것이 **무엇을 바꾸는가**?
- `[2]`(`const&` 와 `&&` 둘만)에서 `g(i)` 는 어디로 가는가?
- `[3]`(`const&` 하나만)이 **세 줄 다 통과하는** 이유는?

### 3. ★ 여섯 줄의 운명 (예측)

```cpp
/* vcat03.cpp */
// 범주가 막는 것 — 여섯 줄이 전부 에러다(주석의 OK 줄은 통과한다)
#include <utility>

int main() {
    int i = 0;
    const int ci = 0;

    const int& ok1 = 42;              // OK — const lvalue 참조는 prvalue 를 받는다
    int&&      ok2 = std::move(i);    // OK — rvalue 참조는 xvalue 를 받는다
    auto*      ok3 = &"abc";          // OK — 문자열 리터럴은 lvalue 라 주소가 있다
    (void)ok1; (void)ok2; (void)ok3;

    int&  e1 = 42;                    // (1) 비-const lvalue 참조 <- prvalue
    int&& e2 = i;                     // (2) rvalue 참조 <- lvalue
    int&  e3 = ci;                    // (3) const 를 버린다
    int&& e4 = std::move(ci);         // (4) int&& <- const int&&
    int*  e5 = &42;                   // (5) prvalue 의 주소
    42 = i;                           // (6) prvalue 에 대입
    (void)e1; (void)e2; (void)e3; (void)e4; (void)e5;
}
```

- 위쪽 `ok1`\~`ok3` 은 통과하고 아래 여섯 줄은 막힌다 — **각각 왜 그런가**?
- 에러가 **몇 개** 나오는가? g++ 와 clang 이 **같은 수**인가?
- `ok3`(`&"abc"`)이 통과하는데 `e5`(`&42`)가 막히는 이유는?
- `e4`(`int&& e4 = std::move(ci);`)는 `std::move` 를 썼는데 왜 막히는가?

### 4. ★ 리터럴 중 하나만 다르다 (예측)

```cpp
/* vcat04.cpp */
// 문자열 리터럴만 lvalue 다 — 주소가 있고, 배열 참조에 묶이고, 크기가 있다
#include <cstdio>

int main() {
    const char* a = "abc";
    const char* b = "abc";
    const char (&r)[4] = "abc";       // 배열 참조에 묶인다 — lvalue 라는 증거

    std::printf("sizeof(\"abc\")   = %zu\n", sizeof("abc"));
    std::printf("&\"abc\" 를 얻는다 : %s\n", (&"abc") ? "된다" : "안 된다");
    std::printf("a == b          : %d   (같은 리터럴이 한 덩어리로 합쳐졌나 — 미명시)\n",
                static_cast<int>(a == b));
    std::printf("&r[0] == a      : %d\n", static_cast<int>(&r[0] == a));
    std::printf("r[0] r[1] r[2]  = %c %c %c\n", r[0], r[1], r[2]);
}
```

- 출력 다섯 줄을 **각각** 맞힐 수 있는가?
- `sizeof("abc")` 가 **얼마**이고 왜 그런가?
- `a == b` 가 **0 인가 1 인가** — 그리고 그 답을 **근거로 써도 되는가**?
- 문자열 리터럴이 `const char (&)[4]` 에 묶인다는 것은 **무엇을 뜻하는가**?

### 5. ★★ 괄호를 세 겹 씌우면 (예측)

```cpp
/* vcat05.cpp */
// prvalue 는 객체가 아니다 — C++17 의 「물질화」를 생성자 로그로 센다
#include <cstdio>

struct Noisy {
    int id;
    explicit Noisy(int i) : id(i) { std::printf("    ctor(%d)\n", id); }
    Noisy(const Noisy& o) : id(o.id) { std::printf("    copy(%d)\n", id); }
    Noisy(Noisy&& o) noexcept : id(o.id) { std::printf("    move(%d)\n", id); }
    ~Noisy() { std::printf("    dtor(%d)\n", id); }
};

Noisy make(int i) { return Noisy(i); }

int main() {
    std::puts("[1] Noisy a = make(1);");
    Noisy a = make(1);
    std::puts("[2] Noisy b = Noisy(Noisy(Noisy(2)));");
    Noisy b = Noisy(Noisy(Noisy(2)));
    std::puts("[3] Noisy c = make(3); 를 인자로 넘기면");
    [](Noisy) { std::puts("    함수 안"); }(make(3));
    std::puts("[4] main 끝 — 여기서 a, b 가 죽는다");
    (void)a; (void)b;
}
```

- `[1]`\~`[3]` 에서 **`ctor`·`copy`·`move`·`dtor` 가 각각 몇 번** 찍히는가?
- 같은 프로그램에 **`-fno-elide-constructors`** 를 붙이면 출력이 **어떻게 바뀌는가**?
- 같은 프로그램을 **`-std=c++14`** 로 돌리고 그 플래그를 붙이면?
- `[3]` 의 `dtor(3)` 은 **어느 줄에서** 찍히는가?

### 6. ★★ 넷은 언제 죽나 (예측)

```cpp
/* vcat06.cpp */
// prvalue 를 참조에 묶으면 수명이 늘고, xvalue 를 묶으면 늘 것이 없다
#include <cstdio>

struct Noisy {
    int id;
    explicit Noisy(int i) : id(i) { std::printf("    ctor(%d)\n", id); }
    ~Noisy() { std::printf("    dtor(%d)\n", id); }
};

Noisy make(int i) { return Noisy(i); }

int main() {
    std::puts("[A] const Noisy& r = make(1);   prvalue 를 묶는다");
    { const Noisy& r = make(1); std::printf("    블록 안 r.id=%d\n", r.id); }
    std::puts("[B] Noisy&& r = make(2);        prvalue 를 rvalue 참조에");
    { Noisy&& r = make(2); std::printf("    블록 안 r.id=%d\n", r.id); }
    std::puts("[C] make(3);                    묶지 않는다");
    { make(3); std::puts("    다음 문장"); }
    std::puts("[D] Noisy local(4); Noisy&& r = static_cast<Noisy&&>(local);  xvalue");
    { Noisy local(4); Noisy&& r = static_cast<Noisy&&>(local);
      std::printf("    블록 안 r.id=%d  &r==&local:%d\n",
                  r.id, static_cast<int>(&r == &local)); }
    std::puts("[E] main 끝");
}
```

- `[A]`\~`[D]` 에서 **`dtor` 가 어느 줄 다음에** 찍히는가?
- `[A]`(`const Noisy&`)와 `[B]`(`Noisy&&`)는 **같은가 다른가**?
- `[D]` 의 `&r == &local` 은 **0 인가 1 인가** — 그것이 무엇을 뜻하는가?
- `[C]` 가 `[A]`·`[B]` 와 갈리는 **한 글자**는 무엇인가?

### 7. ★ 에러 말고 실행으로 같은 것을 묻는다면 (왜)

```cpp
/* vcat07.cpp */
// 같은 격자를 실행으로 — 세 범주를 타입 특성으로 판정해 한 표에 찍는다
#include <cstdio>
#include <type_traits>
#include <utility>

struct S { int m; };

int  byval();
int& bylref();
int&& byrref();

template <class T>
const char* cat() {
    if constexpr (std::is_lvalue_reference_v<T>)      return "lvalue";
    else if constexpr (std::is_rvalue_reference_v<T>) return "xvalue";
    else                                              return "prvalue";
}

#define SHOW(e) std::printf("  %-26s %s\n", #e, cat<decltype((e))>())

int main() {
    int i = 0, j = 0;
    int arr[3]{};
    S s{0};

    std::puts("  expr                       category");
    SHOW(42);
    SHOW("abc");
    SHOW(i);
    SHOW(i + 1);
    SHOW(++i);
    SHOW(i++);
    SHOW(byval());
    SHOW(bylref());
    SHOW(byrref());
    SHOW(std::move(i));
    SHOW(arr);
    SHOW(arr[0]);
    SHOW(s.m);
    SHOW(S{});
    SHOW(S{}.m);
    SHOW(std::move(s).m);
    SHOW(i ? i : j);
    SHOW("abc"[0]);

    std::printf("(부수 효과 확인 i=%d j=%d arr[0]=%d)\n", i, j, arr[0]);
}
```

- 이 프로그램은 (1번의) 컴파일 에러 창과 **무엇이 다른가** — 왜 **둘 다** 필요한가?
- 마지막 줄이 찍는 `i` 와 `arr[0]` 의 값에서 **무엇을 읽어야 하는가**?
- `SHOW(++i)` 를 썼는데 `i` 가 안 변한다면 그것이 **무슨 규칙**의 증거인가?

### 8. ★★ 왼쪽에 놓을 수 있나 (경계)

```cpp
/* vcat08.cpp */
// 「prvalue 에는 대입이 안 된다」는 내장 타입 이야기다 — 클래스 prvalue 는 받는다
#include <cstdio>
#include <string>

struct S { int m; };

struct Guarded {
    int m;
    Guarded& operator=(const Guarded&) & = default;   // ★ lvalue 에만 허용
};

int main() {
    S s{1};
    S{} = s;                       // (a) 된다 — 임시에 대입한다
    std::string t("a");
    std::string("x") += "y";       // (b) 된다

    Guarded g{1};
    Guarded h{2};
    g = h;                         // (c) 된다 — 왼쪽이 lvalue

    std::printf("s.m=%d t=%s g.m=%d — 여기까지 전부 컴파일된다\n",
                s.m, t.c_str(), g.m);
}
```

```cpp
/* vcat09.cpp */
// 그래도 막히는 넷 — 범주가 왼쪽 자리와 참조 묶기를 가른다
struct S { int m; };
struct Guarded { int m; Guarded& operator=(const Guarded&) & = default; };
struct Bits { int b : 3; };

int main() {
    S s{1};
    Guarded g{1};
    Bits x{1};

    S{}.m = 7;          // (1) xvalue 인 스칼라 멤버에 대입
    42 = 1;             // (2) prvalue 에 대입
    Guarded{} = g;      // (3) & 한정자를 단 operator= 는 임시를 거부한다
    int& br = x.b;      // (4) 비트필드 lvalue 는 int& 에 못 묶는다
    (void)s; (void)br;
}
```

- 앞 파일의 `(a)`·`(b)`·`(c)` 는 **컴파일되는가**?
- 뒤 파일의 넷은 **각각 왜** 막히는가?
- 「rvalue 에는 대입을 못 한다」는 문장은 **어디까지 맞는가**?
- `S{}.m` 은 1번에서 `int&&` 로 찍혔는데 **대입은 왜 막히는가**?
- 임시에 대입되는 것을 **막고 싶으면** 무엇을 쓰는가?

### 9. ★★ 플래그 하나가 규칙을 낮추면 (경계)

```cpp
/* vcat10.cpp */
// -fpermissive 는 범주 규칙을 경고로 낮춘다 — 쓴 값은 그대로 사라진다
#include <cstdio>

struct S { int m; };

int main() {
    S s{1};
    S{}.m = 7;                    // ★ 표준으로는 ill-formed
    std::printf("s.m=%d — 7 은 어디로도 가지 않았다\n", s.m);
}
```

- `-Wall -Wextra -pedantic` 으로 이 파일을 컴파일하면 **`cc exit` 이 얼마**인가?
- 거기에 **`-fpermissive`** 를 붙이면 `cc exit` 과 **프로그램 출력**은?
- `s.m` 이 찍히는 값에서 **무엇을 읽어야 하는가** — 7 은 어디로 갔는가?
- **`-pedantic-errors`** 를 함께 붙이면 다시 에러가 되는가?
- 이 자리를 「**종료 코드가 0인데 ill-formed**」라고 부르는 이유는?

### 10. 다른 주제와 잇기 (연결)

- `decltype(x)` 와 `decltype((x))` 가 갈리는 **규칙 자체**의 정본은 형제 몇 번인가?
- 「참조가 무엇인가」의 정본은 형제 몇 번인가 — 여기서는 그 위에 **무엇을 얹었는가**?
- `std::move` 가 xvalue 를 만든다는 것의 정본은 목록의 몇 번인가?
- 「그래서 매개변수를 무엇으로 받나」의 정본은 목록의 몇 번인가?
- 임시의 수명 연장이 **안 되는** 자리(댕글링)의 정본은 목록의 몇 번인가?
- Rust 에는 왜 「이 식이 rvalue 인가」라는 질문이 **없는가**?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
