# cpp/syntax/03 — 캐스트 4종 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 어느 캐스트가 **무엇을 거부하는지**,
> 그리고 **UB 가 어느 플래그에서 드러나는지**를 맞힐 수 있는지 묻는다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · gcc 13.3.0(C 대비) · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex`.
> ★★ **UB 가 걸린 문항은 `-O0`·`-O1`·`-O2`·`-O3`·`-Os` 다섯 수준 × 두 컴파일러로 돌렸다.**
> 한 수준만 보고 답하면 틀린다 — 그리고 **한 수준만 봐도 맞는 자리**가 있다. 그 갈림이 3번·5번이다.
> ★★ **이 주제의 UB 는 sanitizer 가 거의 못 본다.** 「도구가 조용하다」를 근거로 쓰지 않는 연습이다.
> 선행 — C 갈래의 [`05-explicit-casts-and-pointer-conversions/`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)(C 스타일 캐스트).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ `static_cast` 여섯 줄이 각각 무엇을 하나 (예측)

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

- 컴파일되는가? 출력은 무엇인가?
- `static_cast<int>(3.9)` 는 **3** 인가 **4** 인가 — 그 동작에 붙은 이름은?
- ④(다운캐스트)에서 컴파일러가 **무엇을 확인하는가**?
- ⑤⑥이 없으면 컴파일이 되는가 — 그 이유는 어느 형제 주제인가?

### 2. ★★ `static_cast` 가 거부하는 셋 (예측)

```cpp
/* ex.cpp */
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
```

- 에러가 **몇 개** 나는가?
- 각각 **어느 캐스트**를 쓰라는 뜻인가?
- clang 이 g++ 보다 **한 줄 더** 말해 주는 곳이 어디인가?
- 이 셋에 `dynamic_cast` 가 답인 자리가 있는가?

### 3. ★★★ `const_cast` 로 **진짜 `const`** 객체를 고치면 (예측)

```cpp
/* ex.cpp */
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
```

- 한 `fprintf` 안에서 `k` 와 `*p` 가 **같은 값**으로 찍히는가?
- `-O0`·`-O1`·`-O2`·`-O3`·`-Os` 다섯 수준에서 **답이 갈리는가**? clang 은?
- UBSan·ASan 은 **몇 줄**을 말하는가?
- `-Wcast-qual` 을 켜면 **몇 건**인가?
- 원래 객체를 `const` 가 **아니게** 바꾸면 결과가 달라지는가?

### 4. ★★★ 같은 코드를 **C 로** 던지면 (예측)

```c
/* ex.c */
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
```

- `gcc -O0` 의 출력이 3번의 `g++ -O0` 과 **같은가**?
- `gcc -O1` 은?
- 경계선이 **있는가 없는가** — C 와 C++ 중 어느 쪽에 있는가?
- 갈리는 이유를 **최적화가 아닌 낱말**로 설명할 수 있는가?

### 5. ★★★ `reinterpret_cast` 로 만든 앨리어싱 위반 (예측)

```cpp
/* ex.cpp */
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
```

- `-O0` 과 `-O2` 의 출력이 같은가?
- **경계선은 어느 최적화 수준**인가? `-fno-strict-aliasing` 을 주면?
- clang 의 경계선은 g++ 와 같은가?
- `-Wall -Wextra -pedantic` 은 **몇 건**을 말하는가? UBSan·ASan 은?

### 6. ★★ `dynamic_cast` 넷 (예측)

```cpp
/* ex.cpp */
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
```

- `typeid(*b).name()` 은 무엇이 찍히는가 — 그 철자는 **누가 정하는가**?
- 맞는 파생으로의 `dynamic_cast` 와 **틀린** 파생으로의 것이 각각 무엇을 주는가?
- **참조 판**은 무엇을 하는가? `what()` 은 무엇을 말하는가?
- `typeid(*b) == typeid(Left)` 와 `dynamic_cast<Left*>(b)` 는 **같은 질문**인가?

### 7. `dynamic_cast` 의 전제 둘 (경계)

- 원본 타입에 가상 함수가 하나도 없으면 무엇이 나오는가 — g++ 와 clang 각각 한 문구?
- `-fno-rtti` 로 컴파일하면 `dynamic_cast` 와 `typeid` 중 **무엇이** 막히는가?
- 그때 g++ 와 clang 의 **에러 개수**가 같은가?
- `-fno-rtti` 가 흔한 현장이 어디인가 — 거기서는 무엇으로 대신하는가?

### 8. 오브젝트 파일이 `dynamic_cast` 에 대해 말해 주는 것 (왜)

- 같은 함수를 `static_cast` 판과 `dynamic_cast` 판으로 컴파일하고 `nm -uC` 를 걸면 무엇이 다른가?
- `static_cast` 판의 미정의 심볼은 **몇 개**인가?
- 오브젝트 파일 **크기**는 어떻게 달라지는가?
- 이 창이 7번의 `-fno-rtti` 에러와 **어떤 관계**인가?

### 9. C 스타일 캐스트가 무엇으로 풀리나 (경계)

- `(T)x` 가 시도하는 순서를 **다섯 단계**로 적을 수 있는가?
- 그 줄에 **없는** 캐스트 하나는 무엇인가?
- `static_cast` 가 거부한 셋(2번)을 `(T)x` 로 던지면 통과하는가?
- `(Right*)b` 로 다운캐스트한 뒤 멤버를 읽으면 무엇이 나오는가 — 그리고 **누가 말해 주는가**?

### 10. 비트를 그대로 읽는 세 방법 (경계)

- `*reinterpret_cast<int*>(&f)` · `memcpy` · `std::bit_cast` 의 **값**이 같은가?
- 셋 중 **UB 인 것**은 무엇인가?
- g++ `-O2` 가 내는 경고 **두 줄** 중 두 번째가 왜 교재인가?
- `-O0` 과 clang `-O2` 는 각각 몇 건인가?
- `-Wstrict-aliasing=3` 은 몇 건인가 — C 편의 실측과 같은가?

### 11. 다른 주제와 잇기 (연결)

- 이 넷 중 **실행 시간 비용이 있는 것**은 무엇이고, 그 밑에 깔린 장치는 목록의 몇 번이 정본인가?
- `const_cast` 를 **안 쓰게 만드는** 설계는 목록의 몇 번인가?
- `dynamic_cast` 를 **안 쓰게 만드는** 설계 둘을 대면?
- 열거형↔정수 캐스트가 필요한 이유는 형제 주제 몇 번인가?
- C 스타일 캐스트와 엄격한 앨리어싱의 정본은 어느 갈래 어느 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
