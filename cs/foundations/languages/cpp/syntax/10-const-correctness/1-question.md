# cpp/syntax/10 — `const` 정확성 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「`const` 가 무엇을 안 막나」에 몰려 있다** — 막는 쪽은 에러가 알려 주지만
> **안 막는 쪽은 경고 한 줄도 안 나오기** 때문이다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · x86-64 Linux · `nm`(GNU Binutils 2.42).
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **「`const` 니까 안 바뀐다」를 먼저 의심해라** — 3번과 4번이 그 반례다.
> ★ **네 번째 창**은 「**같은 UB 를 네 판으로 돌리는 것**」이다(4번) — 최적화 수준·컴파일러·UBSan 을 갈라 본다.
> 선행 — 형제 [`03번`](../03-four-cast-operators/)(`const_cast`) · [`07번`](../07-references-vs-pointers/)(참조) ·
> C 갈래 [`14번`](../../../c/syntax/14-pointers-address-dereference-and-pointer-types/)(포인터) ·
> C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **31번**(`const` 위치를 읽는 순서).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 같은 이름의 멤버 함수 둘 (예측)

```cpp
/* cnst01.cpp */
// const 멤버 함수와 const 오버로드 — 객체의 const 가 어느 함수를 고르나
#include <cstdio>

struct Buf {
    int a[3]{1, 2, 3};

    int&       at(int i)       { std::puts("    at()       비-const 판"); return a[i]; }
    const int& at(int i) const { std::puts("    at() const const 판");    return a[i]; }

    int sum() const { return a[0] + a[1] + a[2]; }
    void bump()     { ++a[0]; }
};

int main() {
    Buf b;
    const Buf& cb = b;

    std::puts("[1] b.at(0) = 9;        객체가 비-const");
    b.at(0) = 9;
    std::puts("[2] cb.at(0) 을 읽는다   객체가 const");
    std::printf("    값 %d\n", cb.at(0));
    std::puts("[3] const 객체로도 부를 수 있는 것");
    std::printf("    cb.sum() = %d\n", cb.sum());
    std::printf("    b.sum()  = %d   (비-const 객체도 const 멤버를 부른다)\n", b.sum());
    b.bump();
    std::printf("    b.bump() 뒤 sum = %d\n", b.sum());
}
```

- 출력 **일곱 줄**을 순서대로 맞힐 수 있는가?
- `[1]` 과 `[2]` 에서 **어느 판이 불리는가** — 무엇이 그것을 정하는가?
- `cb.at(0)` 이 돌려준 값이 **왜 9 인가**?
- `b.sum()` 은 왜 되는가 — `b` 는 `const` 가 아닌데?
- `cb.at(0) = 1;` 을 쓰면 무슨 일이 나는가?

### 2. ★★ `const` 객체에 무슨 일이 나나 (예측)

```cpp
/* cnst02.cpp */
// mutable — const 멤버 함수 안에서 바뀌는 유일한 멤버
#include <cstdio>

struct Doc {
    int              text = 41;
    mutable int      cached = -1;      // 계산 결과 저장
    mutable unsigned hits = 0;         // 호출 횟수

    int score() const {
        ++hits;                         // const 인데 바뀐다
        if (cached < 0) cached = text + 1;
        return cached;
    }
};

int main() {
    const Doc d;
    std::printf("부르기 전: cached=%d hits=%u\n", d.cached, d.hits);
    for (int n = 1; n <= 3; ++n) {
        int v = d.score();              // ★ 한 줄에 하나만 — 평가 순서에 안 기댄다
        std::printf("%d회째    : score=%d cached=%d hits=%u\n", n, v, d.cached, d.hits);
    }
    std::printf("text      : %d  (이쪽은 const 객체라 못 바꾼다)\n", d.text);
}
```

- `d` 는 `const Doc` 인데 **출력 다섯 줄**이 각각 무엇인가?
- `hits` 는 어떻게 변하는가 — 그리고 `cached` 는?
- `score()` 에 `const` 가 붙어 있는데 `++hits` 가 **왜 컴파일되는가**?
- `text` 를 같은 방법으로 바꾸려면 무엇이 필요한가?
- 이 클래스는 **스레드 안전한가**?
- ★ 소스가 `printf` 한 줄에 `d.score()` 와 `d.cached` 를 같이 안 넣은 이유는?

### 3. ★★★ `const` 를 지나 밖으로 (예측)

```cpp
/* cnst03.cpp */
// 비트단위 const 와 논리적 const — 포인터 멤버가 뚫는 구멍
#include <cstdio>

struct Holder {
    int  own = 1;        // 내 것
    int* p;              // 남의 것을 가리킨다

    explicit Holder(int* q) : p(q) {}

    void poke() const { *p = 99; }        // 된다 — p 가 const 지 *p 는 아니다
    int& leak() const { return *p; }      // const 멤버가 쓰기 가능한 참조를 내준다
    int  read() const { return own; }
};

int main() {
    int outside = 1;
    const Holder h(&outside);

    std::printf("전   : outside=%d h.own=%d\n", outside, h.own);
    h.poke();
    std::printf("poke : outside=%d   (h 는 const 인데 밖이 바뀌었다)\n", outside);
    h.leak() = 7;
    std::printf("leak : outside=%d   (const 멤버가 돌려준 참조로 썼다)\n", outside);
    std::printf("own  : %d           (이쪽은 정말 못 바꾼다)\n", h.read());
}
```

- `h` 는 `const Holder` 다. **출력 네 줄**에서 `outside` 는 어떻게 변하는가?
- `poke()` 가 `const` 인데 `*p = 99` 가 **왜 컴파일되는가**?
- `leak()` 이 돌려준 것으로 대입이 되는 이유는?
- `own` 은 왜 안 바뀌는가 — `p` 와 무엇이 다른가?
- 이 소스에 **경고가 몇 개** 나는가?
- 고치려면 무엇을 바꿔야 하는가 — 두 가지 방법은?

### 4. ★★★ 같은 주소, 두 번 읽기 (예측)

```cpp
/* cnst04.cpp */
// const_cast — 원래 const 인 것을 고치면 UB, 아니면 아니다
#include <cstdio>

int main() {
    const int k = 10;
    int* p = const_cast<int*>(&k);
    *p = 20;                                   // ★ 여기가 UB
    std::printf("[UB]    k=%d  *p=%d  &k==p:%d\n",
                k, *p, static_cast<int>(&k == p));

    int m = 30;                                // 원래 const 가 아니다
    const int& cr = m;
    const_cast<int&>(cr) = 40;                 // ★ UB 아님
    std::printf("[정상]  m=%d  cr=%d\n", m, cr);
}
```

- `[UB]` 줄의 **세 값**을 맞힐 수 있는가?
- `&k == p` 가 **참인데** `k` 와 `*p` 가 다를 수 있는가?
- `[정상]` 줄은 왜 `[UB]` 가 아닌가 — 무엇이 둘을 가르는가?
- 이것을 **`-O0`·`-O2`·clang·UBSan 네 판**으로 돌리면 답이 갈리는가?
- ★ 네 판이 전부 같았다면 **「안전하다」고 결론 내도 되는가**?

### 5. ★★ 두 파일이 같은 이름을 쓰면 (예측)

```cpp
/* cnst05a.cpp */
// 번역 단위 A — 네임스페이스 스코프의 const 는 내부 링크다
const int limit = 10;              // 이 TU 만의 것
extern const int shared = 20;      // extern 을 붙이면 외부 링크

int from_a()        { return limit; }
int shared_from_a() { return shared; }
```

```cpp
/* cnst05b.cpp */
// 번역 단위 B — 같은 이름을 다시 정의해도 충돌하지 않는다
#include <cstdio>

const int limit = 99;              // A 의 limit 과 다른 물건
extern const int shared;           // A 의 것을 쓴다

int from_a();
int shared_from_a();

int main() {
    std::printf("limit  : B 에서 %d · A 에서 %d\n", limit, from_a());
    std::printf("shared : B 에서 %d · A 에서 %d\n", shared, shared_from_a());
    std::printf("&limit 를 비교할 수 있나 : 두 TU 의 limit 는 서로 다른 객체다\n");
}
```

- 두 파일에 `const int limit` 이 **둘 다 있는데 링크가 되는가**?
- 출력 세 줄에서 `limit` 과 `shared` 는 각각 무엇으로 찍히는가?
- `nm -C a.o` 에서 `limit` 과 `shared` 의 **심볼 문자**는 무엇인가?
- `shared` 의 선언에 `extern` 이 붙은 이유는?
- 헤더에 `const int N = 10;` 을 두고 열 파일에서 포함하면 **몇 개가 생기는가**?
- ★ C 에서는 어떻게 다른가?

### 6. ★ 배열 크기 자리에 무엇이 들어가나 (예측)

```cpp
/* cnst06.cpp */
// const 와 constexpr — 「못 바꾼다」와 「컴파일 때 안다」는 다르다
#include <cstdio>

int runtime() { return 3; }

int main() {
    const int     a = 5;          // 초기화식이 상수식이라 상수식으로도 쓰인다
    constexpr int b = 5;          // 상수식임을 강제한다
    const int     c = runtime();  // ★ const 는 런타임 값도 받는다

    int arr1[a]{};                // 된다
    int arr2[b]{};                // 된다
    static_assert(a == 5);
    static_assert(b == 5);

    std::printf("a=%d b=%d c=%d  sizeof(arr1)=%zu sizeof(arr2)=%zu\n",
                a, b, c, sizeof(arr1), sizeof(arr2));
}
```

- 출력 한 줄의 **다섯 값**을 맞힐 수 있는가?
- `const int a = 5;` 가 배열 크기로 쓰이는 이유는 — `const` 라서인가?
- `const int c = runtime();` 은 왜 컴파일되는가?
- 같은 자리에 `constexpr int d = runtime();` 을 쓰면?
- `const` 와 `constexpr` 의 차이를 **한 문장**으로 말할 수 있는가?

### 7. ★★ 일곱 줄이 각각 무엇을 어겼나 (경계)

```cpp
/* cnst08.cpp */
// const 가 막는 일곱 — 전부 에러다
int runtime();

struct S {
    int m = 0;
    int bad() const { m = 1; return m; }   // (1) const 멤버가 멤버를 고친다
    void mut()      { ++m; }
};

int main() {
    const int x;                            // (2) 초기화 없는 const
    const S s;
    s.mut();                                // (3) const 객체로 비-const 멤버 호출
    int* p = &s.m;                          // (4) const 멤버의 주소를 int* 로
    constexpr int d = runtime();            // (5) constexpr 는 런타임 값을 못 받는다

    int i = 0, j = 0;
    int* const cp = &i;
    cp = &j;                                // (6) const 포인터를 다시 겨눈다
    const int* pc = &i;
    *pc = 1;                                // (7) 포인터-투-const 로 쓴다
    (void)x; (void)p; (void)d; (void)pc;
}
```

- 에러가 **몇 개** 나는가?
- 일곱 줄이 **각각 다른 이유**로 막힌다 — 짝지을 수 있는가?
- `(6)` 과 `(7)` 의 차이를 **선언을 읽는 순서**로 설명할 수 있는가?
- `(5)` 는 `const` 이야기인가 `constexpr` 이야기인가?
- clang 으로 던지면 **개수가 같은가**?

### 8. ★★★ 빌드는 통과하는데 (왜)

```cpp
/* cnst07.cpp */
// C++11 부터 ill-formed 인데 컴파일이 통과하는 줄
#include <cstdio>

int main() {
    std::setvbuf(stdout, nullptr, _IONBF, 0);   // 죽어도 출력이 안 사라지게
    char* p = "abc";                            // ★ 여기
    std::printf("쓰기 전: p=%s\n", p);
    p[0] = 'X';                                 // ★ 읽기 전용 구역에 쓴다 — UB
    std::printf("쓴 뒤  : p=%s\n", p);
}
```

- `cc exit` 과 `run exit` 은 각각 얼마인가?
- `char* p = "abc";` 는 **경고인가 에러인가** — 표준은 무엇이라 하는가?
- 어느 플래그를 붙여야 **에러**가 되는가?
- clang 은 어떻게 다른가?
- ★ 소스 첫 줄의 `setvbuf(stdout, nullptr, _IONBF, 0)` 은 **무엇을 막으려고** 있는가?
- 「`-std=c++20` 으로 돌렸다」가 「C++20 으로 검증했다」와 다른 이유는?

### 9. 어느 쪽을 쓸까 (왜)

- 멤버 함수에 `const` 를 **안 붙이면** 무엇이 전염되는가?
- 캐시를 두어야 할 때 `mutable` 과 `const_cast` 중 무엇을 고르고, 왜인가?
- 멤버에 포인터가 있을 때 `const` 멤버 함수가 **무엇을 돌려줘야** 하는가?
- 헤더에 상수를 둘 때 `const` 대신 무엇을 쓰는가 — 왜인가?
- 옛 API 가 `const` 를 안 받을 때, `const_cast` 를 쓰기 전에 **무엇을 먼저 물어야** 하는가?
- ★ 「`const` 는 계약이지 검사가 아니다」를 **자기 말로** 한 문장으로 쓸 수 있는가?

### 10. 다른 주제와 잇기 (연결)

- `const_cast` 를 **언제 고르나**의 정본은 형제 몇 번인가?
- `const T&` 가 **어떤 식들을 받을 수 있나**의 정본은 목록의 몇 번인가?
- `const` 객체를 `std::move` 하면 무슨 일이 나는가 — 정본은 목록의 몇 번인가?
- 매개변수를 값·`const&`·`&&` 중 무엇으로 받을지의 정본은 목록의 몇 번인가?
- `const char*` / `char* const` 를 **읽는 순서**는 **어느 갈래 몇 번**인가?
- Rust 의 `&` 와 C++ 의 `const` 는 **무엇이 다른가** — 한 문장으로.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
