# cpp/syntax/07 — 참조와 포인터의 차이 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 참조가 **무엇을 못 하는지**,
> 그리고 그 「못 함」이 **설계에서 무엇을 사는지**를 맞힐 수 있는지 묻는다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · x86-64 Linux · `objdump`/`nm`(GNU Binutils 2.42).
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **「참조는 포인터보다 빠르다/느리다」를 먼저 의심해라** — 3번에서 **기계어를 직접 대조**한다.
> ★ **네 번째 창은 생성된 기계어**(`objdump -d`)다. 타입 체계와 코드 생성을 **갈라서** 본다.
> 선행 — C 갈래 [`14-pointers-address-dereference-and-pointer-types/`](../../../c/syntax/14-pointers-address-dereference-and-pointer-types/)(포인터).
> 형제 [`05번`](../05-auto-and-decltype-type-deduction/)의 `auto&`·`auto&&` 가 여기서 온다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 같은 모양의 대입이 다른 일을 한다 (예측)

```cpp
/* ptr01.cpp */
// 참조는 재결합되지 않는다 — 같은 모양의 대입이 다른 일을 한다
#include <cstdio>

int main() {
    int a = 1, b = 2;
    int& r = a;
    int* p = &a;

    r = b;      // 참조: a 에 b 의 값을 쓴다
    p = &b;     // 포인터: p 가 가리키는 곳을 바꾼다

    std::printf("a=%d b=%d r=%d *p=%d\n", a, b, r, *p);
    std::printf("&a == &r : %d    &a == p : %d\n",
                static_cast<int>(&a == &r), static_cast<int>(&a == p));
    std::printf("sizeof(a)=%zu sizeof(r)=%zu sizeof(p)=%zu\n",
                sizeof(a), sizeof(r), sizeof(p));
}
```

- 출력 세 줄을 **각각** 맞힐 수 있는가?
- `r = b;` 가 한 일과 `p = &b;` 가 한 일이 무엇이 다른가?
- `&a == &r` 이 **참인가 거짓인가** — 그것이 무엇을 뜻하는가?
- `sizeof(r)` 이 **4** 인 이유는? 그러면 참조는 **저장 공간을 안 쓰는가**?

### 2. ★ 참조가 못 하는 넷 (예측)

```cpp
/* ptr02.cpp */
// 참조가 못 하는 넷 — 포인터는 전부 된다
int g = 0;

int main() {
    int a = 1;
    int& r;                 // ① 초기화 없이
    int& ar[2] = {a, g};    // ② 참조의 배열
    int&* pr = &a;          // ③ 참조로의 포인터
    int& & rr = a;          // ④ 참조로의 참조
    (void)r; (void)ar; (void)pr; (void)rr;
}
```

- 에러가 **몇 개** 나는가?
- 넷 중 **포인터로는 되는 것**은 몇 개인가?
- ④의 에러 문구에 붙은 단서(「typedef 나 템플릿 인자가 아니면」)는 무엇을 암시하는가?
- 이 넷이 **못 되는 것**에서 참조의 성질 **하나**를 끌어낼 수 있는가?

### 3. ★★★ 기계어가 다른가 (예측)

```cpp
/* ptr03.cpp */
int by_ref(int& x) { return x + 1; }
int by_ptr(int* x) { return *x + 1; }
```

- `g++ -O2 -c` 로 만든 두 함수의 **명령어 열**이 같은가 다른가?
- `-O0` 에서는 어떤가?
- `nm -C` 로 보면 무엇이 다른가?
- 「참조가 더 빠르다」는 말은 **무엇을 근거로 하면 틀리는가**?

### 4. ★★ 참조를 멤버로 두면 (예측)

```cpp
/* ptr04.cpp */
// 참조 멤버는 대입을 지운다
#include <cstdio>

struct HasRef { int& r; };
struct HasPtr { int* p; };

int main() {
    int a = 1, b = 2;
    HasRef x{a}, y{b};
    HasPtr u{&a}, v{&b};
    std::printf("sizeof(HasRef)=%zu sizeof(HasPtr)=%zu\n", sizeof(HasRef), sizeof(HasPtr));
    u = v;                 // 포인터 멤버는 대입된다
    std::printf("*u.p = %d\n", *u.p);
    x = y;                 // 참조 멤버는?
}
```

- `sizeof(HasRef)` 와 `sizeof(HasPtr)` 가 각각 얼마인가?
- `u = v;` 는 되고 `x = y;` 는 어떻게 되는가?
- 그 진단이 말하는 **이유**가 무엇인가?
- 이 성질이 컨테이너(`std::vector<HasRef>`)에 무엇을 뜻하는가?

### 5. ★★ 임시를 받는 것 (예측)

```cpp
/* ptr05.cpp */
// const 참조가 임시의 수명을 늘린다
#include <cstdio>

struct Noisy {
    int v;
    explicit Noisy(int x) : v(x) { std::printf("  Noisy(%d) 생성\n", v); }
    ~Noisy()                     { std::printf("  ~Noisy(%d) 파괴\n", v); }
};

Noisy make(int x) { return Noisy(x); }

int main() {
    std::printf("A: const 참조에 묶는다\n");
    {
        const Noisy& r = make(1);
        std::printf("  블록 안 — r.v = %d\n", r.v);
    }
    std::printf("B: 안 묶고 그냥 만든다\n");
    {
        make(2);
        std::printf("  이 줄은 파괴 뒤다\n");
    }
    std::printf("끝\n");
}
```

- A 와 B 의 출력 순서를 맞힐 수 있는가?
- `const Noisy& r = make(1);` 에서 임시가 **언제** 파괴되는가 — 그 규칙의 이름은?
- 같은 일을 포인터로 하려고 `const Noisy* p = &make(3);` 를 쓰면 어떻게 되는가?
- 이 차이가 **함수 매개변수 설계**에서 무엇을 뜻하는가?

### 6. ★★ 널 참조 (예측)

```cpp
/* ptr08.cpp */
// 참조는 널이 아니라고 「가정된다」 — 검사하려 들면 컴파일러가 말해 준다
#include <cstdio>

bool check_ref(int& r) { return &r == nullptr; }
bool check_ptr(int* p) { return p == nullptr; }

int main() {
    int a = 1;
    std::printf("check_ref(a)=%d  check_ptr(&a)=%d  check_ptr(nullptr)=%d\n",
                static_cast<int>(check_ref(a)),
                static_cast<int>(check_ptr(&a)),
                static_cast<int>(check_ptr(nullptr)));
}
```

- 컴파일되는가 — 경고는 **몇 건**이고 이름은?
- `check_ref(a)` 의 결과는?
- 경고 문구가 말하는 **컴파일러의 가정**이 무엇인가?
- 그 가정을 깨는 코드(`int& r = *(int*)nullptr;`)를 `-fsanitize=undefined` 로 돌리면 무엇이 나오는가?

### 7. 지역을 돌려주면 (경계)

```cpp
/* ptr07.cpp */
// 지역을 돌려주면 — 참조와 포인터가 같은 경고를 받는다
#include <cstdio>

int& dangling_ref() { int local = 42; return local; }
int* dangling_ptr() { int local = 43; return &local; }

int main() {
    int& r = dangling_ref();
    int* p = dangling_ptr();
    std::printf("r=%d *p=%d\n", r, *p);
}
```

- 참조 판과 포인터 판이 **같은 경고**를 받는가?
- 경고 이름은 무엇인가 — **문구**는 같은가?
- 컴파일 종료 코드는?
- 참조가 포인터보다 **안전한가**?

### 8. 인터페이스 — 「없음」을 표현할 수 있나 (경계)

```cpp
/* ptr10.cpp */
// 인터페이스 — 참조 매개변수는 「없음」을 못 받는다
void take_ref(int& x) { (void)x; }
void take_ptr(int* x) { (void)x; }

int main() {
    take_ptr(nullptr);     // ① 포인터는 「없음」이 값이다
    take_ref(nullptr);     // ② 참조는?
}
```

- 두 줄 중 **막히는** 쪽은?
- 에러 문구가 말하는 것은?
- 「널이 될 수 있다」를 **타입으로** 말하려면 어느 쪽을 쓰는가?
- `T*` 말고 그것을 말하는 **더 나은 도구**가 있는가?

### 9. 어느 쪽을 쓸까 (왜)

- 참조를 **먼저** 고르는 이유 셋을 댈 수 있는가?
- 포인터를 **반드시** 써야 하는 자리 셋은?
- 「참조는 널이 아니다」가 **보장인가 약속인가**?
- 참조를 **재결합하고 싶어지면** 무엇을 쓰는가?

### 10. 다른 주제와 잇기 (연결)

- `auto&`·`auto&&` 가 무엇인지의 정본은 형제 몇 번인가?
- 참조가 **어떤 식에 묶이는지**(lvalue·rvalue)의 정본은 목록의 몇 번인가?
- `const T&` 매개변수 설계의 정본은 목록의 몇 번인가?
- 댕글링 참조와 수명 연장의 정본은 목록의 몇 번인가?
- 포인터 산술·배열 감쇠는 **어느 갈래 어느 주제**인가 — 참조에는 왜 그 이야기가 없는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
