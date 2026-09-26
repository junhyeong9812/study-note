# cpp/syntax/24 — `explicit` 과 변환 생성자 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「이 줄에서 생성자가 말없이 도나」를 맞히는 것**이 절반이다 — 「`Meter` 라고 안 썼으니 안 돈다」로 뭉개지 말고
> **그 자리가 복사 초기화인가 직접 초기화인가**를 따라가야 한다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 본체는 「호출 로그」다**(1번) — 인자 하나짜리 생성자에 로그를 심었다. ★★ 짝은 **`explicit` 격자**(3번).
> ★ **「부적용인 창」이 둘 있다** — ASan(메모리를 건드리지 않는다)과 어셈블리(평범한 생성자 호출이다).
> ★★★ **[22번](../22-operator-overloading/)이 잰 것은 다시 묻지 않는다** — 「`1 + a` 는 비멤버 × 암묵 변환일 때만 · `explicit` 이면 비멤버여도 에러 2 · 2」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 인자 하나짜리 생성자에 로그를 심으면 (예측)

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

- `(1)`\~`(6)` 각각에서 **`calls` 는 얼마**인가?
- ★★★ `(5)` 와 `(6)` 은 같은 모양의 삼항이다 — 두 줄의 `calls` 는 같은가?
- ★ 첫 줄에 찍히는 `Meter(int 1)` 은 어느 문장이 낸 것인가?

### 2. ★★★ 같은 소스에 `-DASK_EXPLICIT` 을 주면 (예측)

- ★★ **몇 줄이 에러**인가 — `give()` 의 `return 7;` 도 들어가나?
- ★★★ 1번에서 `calls` 가 0 이었던 줄도 에러인가?

### 3. ★★★ 한 줄씩 켜는 `explicit` 격자 (예측)

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

- ★★ 15개 탐침 중 `explicit` 을 붙이면 **X 로 바뀌는 칸**은 어느 것들인가?
- ★★★ `vec.push_back(5)` 와 `vec.emplace_back(5)` 는 같은 쪽인가?
- ★ `return {5};` 와 `Meter a{5};` 는 둘 다 중괄호다 — 같은 쪽인가?
- ★ g++ 와 clang 이 다르게 답하는 칸이 있나?

### 4. ★★ `std::string` 을 받는 생성자에 문자열 리터럴을 넘기면 (예측)

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

- 1\~4번 중 **어느 줄이 에러**인가?
- ★★ 2번은 막히는데 4번(`Name m("choi")`)은 된다면 — 두 자리의 차이는 무엇인가?

### 5. ★★★ 오버로드 두 벌에 리터럴과 정수를 넘기면 (예측)

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

- ★★★ `(1)`\~`(5)` 각각에서 **어느 함수**가 불리나?
- ★★ g++ 와 clang 이 `-Wall -Wextra -pedantic` 으로 `(1)` 에 경고를 내나 — `-Wconversion` 을 더하면?
- ★ `(4)` 는 「사용자 정의 변환은 한 번뿐」에 걸리나?

### 6. ★★★ `explicit operator bool` 을 가진 핸들 (예측)

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

- ★★ 1\~10번 중 **어느 줄이 에러**인가?
- ★★★ `-DASK_IMPLICIT` 로 `explicit` 을 떼면 **9번과 10번은 무엇을 찍나**?
- ★ 4번(`h ? 1 : 0`)과 7번(`bool b3 = h`)은 둘 다 `bool` 이 필요한데 왜 갈리나?

### 7. ★★ `int` 생성자에 `double` 을 괄호·복사 초기화·중괄호로 넘기면 (경계)

- ★★ `Meter a(3.5)` · `Meter b = 3.5` · `Meter c{d}`(`d` 는 `double` 변수) 각각을 g++ 와 clang 은 **통과 · 경고 · 에러** 중 무엇으로 처리하나?
- ★ 중괄호에 **상수** `3.5` 를 넣으면 g++ 도 같은 판정인가?

### 8. ★ `explicit(bool)` 을 `-std=c++17` 로 (경계)

- ★★ `explicit(!std::is_integral_v<U>)` 가 든 파일을 `-std=c++17 -Wall -Wextra -pedantic` 으로 던지면 `cc exit` 는?
- ★ 그것을 막으려면 무엇을 켜야 하나 — 앞 편의 어느 항목과 같은 집안인가?

### 9. ★★ `explicit` 이 가르는 두 타입 특성 (왜)

- ★★ `explicit Exp(int)` 에 대해 `is_convertible_v<int, Exp>` 와 `is_constructible_v<Exp, int>` 가 다르게 나오는 이유는?
- ★ 그 두 특성은 3번 격자의 어느 선과 같은 선인가?

### 10. ★★ 언제 `explicit` 을 붙이나 (왜)

- ★★★ `Meter(int)` · `BigInt(long)` · `Buffer(size_t n)` · `String(const char*)` 중 어디에 붙이고 어디에 안 붙이나 — 그 기준은?
- ★ 붙여도 막히지 않는 자리가 있다는 것은 무엇을 뜻하나?

### 11. 다른 주제와 잇기 (연결)

- ★★★ 22편의 「`1 + a`」 대칭은 이 편의 어느 결정과 맞바꾸는 것인가?
- ★ 5번의 「표준 변환이 이긴다」는 몇 번 주제의 무엇인가?
- ★ 1번의 `give()` 가 `calls 1` 인 것(복사·이동이 한 번도 없는 것)은 몇 번 주제의 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
