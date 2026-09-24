# cpp/syntax/11 — 매개변수 전달 방식 고르기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **세어서 답하는 것**이 대부분이다 — 「어느 쪽이 나은가」를 **의견으로 답하지 마라.**
> 복사·이동 **호출 횟수**와 **힙 할당 횟수**를 **숫자로** 맞혀야 한다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · x86-64 Linux · `objdump`(GNU Binutils 2.42) · AddressSanitizer.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **「몇 배 빠른가」를 묻는 문항은 하나도 없다** — 이 문서는 **시간을 재지 않았다**(7번이 그 이유다).
> ★ **네 번째 창은 AddressSanitizer** 다(5번). 컴파일러 셋이 다 조용한 자리를 그것만 잡는다.
> 선행 — 목록의 **08번 주제**(값 범주)와 목록의 **09번 주제**(`std::move`·`std::forward`)가 이 주제의 바로 앞이다.
> 형제 [`07번`](../07-references-vs-pointers/)의 「참조가 무엇을 못 하나」가 여기서 설계 기준이 된다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 읽기만 하는 함수에 넷을 던지면 (예측)

```cpp
/* pass01.cpp */
// 전달 방식마다 복사·이동이 몇 번 도는지 센다
#include <cstdio>
#include <utility>

static int cp = 0, mv = 0;

struct Probe {
    int id;
    explicit Probe(int i = 0) : id(i) {}
    Probe(const Probe& o) : id(o.id) { ++cp; }
    Probe(Probe&& o) noexcept : id(o.id) { ++mv; }
    Probe& operator=(const Probe& o) { id = o.id; ++cp; return *this; }
    Probe& operator=(Probe&& o) noexcept { id = o.id; ++mv; return *this; }
};

static Probe keep;                                   // 받은 것을 여기 보관한다

void by_value(Probe p)         { keep = std::move(p); }
void by_cref (const Probe& p)  { keep = p; }
void by_rref (Probe&& p)       { keep = std::move(p); }
void by_pair (const Probe& p)  { keep = p; }
void by_pair (Probe&& p)       { keep = std::move(p); }
template <class T> void by_fwd(T&& p) { keep = std::forward<T>(p); }

void read_value(Probe p)        { keep.id += p.id * 0; }
void read_cref (const Probe& p) { keep.id += p.id * 0; }

#define RUN(label, call) do { cp = mv = 0; call; \
    std::printf("  %-34s copy %d · move %d\n", label, cp, mv); } while (0)

int main() {
    Probe lv(1);

    std::puts("[A] 읽기만 한다");
    RUN("read_value(lv)        by value", read_value(lv));
    RUN("read_value(Probe(2))  by value", read_value(Probe(2)));
    RUN("read_cref(lv)         const&", read_cref(lv));
    RUN("read_cref(Probe(2))   const&", read_cref(Probe(2)));

    std::puts("[B] 받아서 보관한다");
    RUN("by_value(lv)          by value", by_value(lv));
    RUN("by_value(Probe(2))    by value", by_value(Probe(2)));
    RUN("by_cref(lv)           const&", by_cref(lv));
    RUN("by_cref(Probe(2))     const&", by_cref(Probe(2)));
    RUN("by_rref(move(lv))     &&", by_rref(std::move(lv)));
    RUN("by_rref(Probe(2))     &&", by_rref(Probe(2)));
    RUN("by_pair(lv)           overloads", by_pair(lv));
    RUN("by_pair(Probe(2))     overloads", by_pair(Probe(2)));
    RUN("by_fwd(lv)            T&&", by_fwd(lv));
    RUN("by_fwd(Probe(2))      T&&", by_fwd(Probe(2)));

    std::printf("(보관소 id=%d)\n", keep.id);
}
```

- `[A]` 네 줄의 **`copy` 와 `move` 숫자 여덟 개**를 각각 맞힐 수 있는가?
- `read_value(lv)` 와 `read_value(Probe(2))` 가 **왜 다른가** — 무엇이 달라졌는가?
- `read_cref` 두 줄이 **둘 다 0** 인 이유는?
- 「값 전달은 복사한다」는 문장은 **어디까지 참인가**?

### 2. ★★★ 같은 프로그램, 이번엔 받아서 보관한다 (예측)

1번과 같은 파일의 `[B]` 절이다. 함수들이 받은 것을 `keep` 에 **대입해 보관한다**.

```text
   void by_value(Probe p)         { keep = std::move(p); }
   void by_cref (const Probe& p)  { keep = p; }
   void by_rref (Probe&& p)       { keep = std::move(p); }
   void by_pair (const Probe& p)  { keep = p; }          // 오버로드 쌍
   void by_pair (Probe&& p)       { keep = std::move(p); }
   template <class T> void by_fwd(T&& p) { keep = std::forward<T>(p); }
```

- `[B]` 열 줄의 **`copy`·`move` 숫자 스무 개**를 맞힐 수 있는가?
- ★ `by_cref(Probe(2))` 는 **임시를 받았는데** `copy` 가 몇인가 — 왜 그런가?
- ★ `by_value(lv)` 의 합이 **다른 줄보다 큰가 작은가** — 무엇이 하나 더 도는가?
- ★ `by_pair` 와 `by_fwd` 의 네 줄을 비교하면 **어떤 관계인가**?
- `by_rref` 행의 인자가 `lv` 가 아니라 **`std::move(lv)`** 인 이유는?

### 3. ★★ 세터 셋 · 인자 셋 (예측)

```cpp
/* pass02.cpp */
// 싱크 매개변수 — 세터를 세 가지로 짜고 힙 할당 횟수를 센다
#include <cstdio>
#include <cstdlib>
#include <new>
#include <string>
#include <utility>

static int allocs = 0;
void* operator new(std::size_t n) {
    ++allocs;
    void* p = std::malloc(n ? n : 1);
    if (!p) throw std::bad_alloc();
    return p;
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

struct SetCref { std::string v; void set(const std::string& s) { v = s; } };
struct SetPair { std::string v;
                 void set(const std::string& s) { v = s; }
                 void set(std::string&& s) { v = std::move(s); } };
struct SetVal  { std::string v; void set(std::string s) { v = std::move(s); } };

#define LONG "0123456789012345678901234567890123456789"
#define RUN(label, stmt) do { allocs = 0; { stmt; } \
    std::printf("  %-28s new %d회\n", label, allocs); } while (0)

int main() {
    std::string lv = LONG;
    std::puts("인자 세 가지 x 세터 세 가지 (문자열은 40자 — SSO 밖)");
    RUN("SetCref::set(lvalue)",   SetCref t; t.set(lv));
    RUN("SetCref::set(temporary)",     SetCref t; t.set(std::string(LONG)));
    RUN("SetCref::set(literal)",   SetCref t; t.set(LONG));
    RUN("SetPair::set(lvalue)",   SetPair t; t.set(lv));
    RUN("SetPair::set(temporary)",     SetPair t; t.set(std::string(LONG)));
    RUN("SetPair::set(literal)",   SetPair t; t.set(LONG));
    RUN("SetVal::set(lvalue)",    SetVal  t; t.set(lv));
    RUN("SetVal::set(temporary)",      SetVal  t; t.set(std::string(LONG)));
    RUN("SetVal::set(literal)",    SetVal  t; t.set(LONG));
    std::printf("(원본은 그대로 %zu자)\n", lv.size());
}
```

- 아홉 줄의 **`new` 횟수 아홉 개**를 각각 맞힐 수 있는가?
- ★ `SetCref` 행에서 **`lvalue` 와 나머지 둘이 갈리는** 이유는?
- ★ `SetVal`(값 + `std::move`)과 `SetPair`(오버로드 쌍)의 **아홉 숫자가 같은가 다른가**?
- 그렇다면 둘 중 **무엇을 고를 근거**는 무엇인가?
- ★ 문자열을 **40자**로 잡은 이유는 무엇이겠는가?

### 4. ★ 같은 자리에 리터럴과 `std::string` 을 (예측)

```cpp
/* pass03.cpp */
// const std::string& 과 std::string_view — 리터럴을 넘길 때 갈린다
#include <cstdio>
#include <cstdlib>
#include <new>
#include <string>
#include <string_view>

static int allocs = 0;
void* operator new(std::size_t n) {
    ++allocs;
    void* p = std::malloc(n ? n : 1);
    if (!p) throw std::bad_alloc();
    return p;
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

static std::size_t total = 0;
void take_cref(const std::string& s) { total += s.size(); }
void take_view(std::string_view s)   { total += s.size(); }

#define LONG "0123456789012345678901234567890123456789"
#define RUN(label, stmt) do { allocs = 0; { stmt; } \
    std::printf("  %-30s new %d회\n", label, allocs); } while (0)

int main() {
    std::string s = LONG;
    const char* cstr = LONG;

    RUN("take_cref(literal)",   take_cref(LONG));
    RUN("take_view(literal)",   take_view(LONG));
    RUN("take_cref(const char*)", take_cref(cstr));
    RUN("take_view(const char*)", take_view(cstr));
    RUN("take_cref(std::string)", take_cref(s));
    RUN("take_view(std::string)", take_view(s));
    RUN("take_cref(s.substr)",  take_cref(s.substr(0, 5)));
    RUN("take_view(view.substr)", take_view(std::string_view(s).substr(0, 5)));
    std::printf("(합계 %zu — 최적화로 호출이 사라지지 않게)\n", total);
}
```

- 여덟 줄의 **`new` 횟수 여덟 개**를 맞힐 수 있는가?
- ★ `take_cref(literal)` 에서 **무슨 객체가 생기는가**?
- ★ 마지막 두 줄(`substr`)의 숫자는 **앞 여섯 줄과 같은 근거로 읽어도 되는가**?
- `std::string_view` 를 **값으로** 받은 이유는?

### 5. ★★ 임시를 뷰에 담고 한 글자 읽으면 (예측)

```cpp
/* pass04.cpp */
// string_view 는 빌려 볼 뿐이다 — 임시에 붙이면 문장 끝에 끊긴다
#include <cstdio>
#include <string>
#include <string_view>

std::string make() { return std::string("0123456789012345678901234567890123456789"); }

int main() {
    std::string_view sv = make();          // ★ 임시는 이 문장 끝에 죽는다
    std::fprintf(stderr, "[마커] 여기까지는 산다 — size=%zu\n", sv.size());
    std::fprintf(stderr, "[마커] 이제 sv[0] 를 읽는다\n");
    char c = sv[0];
    std::fprintf(stderr, "[마커] sv[0]=%c\n", c);
}
```

- **g++ 의 경고 개수**와 **clang 의 경고 개수**를 각각 맞힐 수 있는가?
- **`cc exit`** 과 **`run exit`** 은 각각 몇인가?
- ★ `sv.size()` 는 통과하는데 `sv[0]` 에서 걸리는가 — 아니면 그 반대인가?
- ★★ 마커를 `printf` 가 아니라 **`fprintf(stderr, …)`** 로 찍은 이유는?
- 이 프로그램은 **ill-formed 인가** — `-pedantic-errors` 를 붙이면 잡히는가?

### 6. ★ `int` 둘을 받는 두 시그니처 (예측)

```cpp
/* pass05.cpp */
// 작은 타입은 값이 낫다 — 생성된 코드로 확인한다
struct Big { double d[8]; };                       // 64바이트

int add_val (int a, int b)                { return a + b; }
int add_cref(const int& a, const int& b)  { return a + b; }

double sum_val (Big b)        { return b.d[0] + b.d[7]; }
double sum_cref(const Big& b) { return b.d[0] + b.d[7]; }

double call_val (const Big& b) { return sum_val(b); }   // 복사가 여기서 난다
double call_cref(const Big& b) { return sum_cref(b); }
```

- `-O2` 에서 `add_val` 과 `add_cref` 의 **명령어 열**이 어떻게 다른가?
- ★ `const int&` 가 **무엇을 아끼고 무엇을 더 쓰는가**?
- `sum_val(Big)` 과 `sum_cref(const Big&)` 는 받는 쪽만 보면 어떻게 다른가?

### 7. ★★★ 64바이트를 값으로 넘기는데 복사 명령이 한 줄도 없다 (왜)

6번과 같은 파일의 `call_val` 을 `-O2` 로 떠 보면 **`movsd` 두 줄로 끝난다.**

- 64바이트를 **값으로** 넘기는 호출인데 **복사가 어디로 갔는가**?
- ★ 그 복사를 **보이게 하려면** 무엇을 해야 하는가?
- ★★ 그렇다면 **「값 전달이 복사 때문에 느리다」를 이 실험만으로 단정해도 되는가**?
- ★★★ 이 문서가 **시간을 한 번도 재지 않은** 이유를 한 문장으로 말할 수 있는가?

### 8. ★★ C 배열을 넘기는 두 방법 (경계)

```cpp
/* pass06.cpp */
// std::span — 「연속된 것이면 무엇이든」 받는다
#include <array>
#include <cstdio>
#include <cstdlib>
#include <new>
#include <span>
#include <vector>

static int allocs = 0;
void* operator new(std::size_t n) {
    ++allocs;
    void* p = std::malloc(n ? n : 1);
    if (!p) throw std::bad_alloc();
    return p;
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

static long total = 0;
void sum_span(std::span<const int> s)        { for (int x : s) total += x; }
void sum_vec (const std::vector<int>& v)     { for (int x : v) total += x; }

#define RUN(label, stmt) do { allocs = 0; { stmt; } \
    std::printf("  %-28s new %d회\n", label, allocs); } while (0)

int main() {
    std::vector<int> v{1, 2, 3};
    int carr[3]{1, 2, 3};
    std::array<int, 3> arr{1, 2, 3};

    RUN("sum_vec(vector)",   sum_vec(v));
    RUN("sum_span(vector)",  sum_span(v));
    RUN("sum_span(C array)", sum_span(carr));
    RUN("sum_span(std::array)", sum_span(arr));
    RUN("sum_vec(C array)",  sum_vec(std::vector<int>(carr, carr + 3)));
    std::printf("(합계 %ld)\n", total);
}
```

- 다섯 줄의 **`new` 횟수**를 맞힐 수 있는가 — 특히 **마지막 줄**은?
- ★ `sum_vec` 에 `std::array<int,3>` 를 그냥 넘기면 어떻게 되는가?
- `std::span<const int>` 와 `std::span<int>` 는 **무엇이 다른가**?
- ★ 배열을 매개변수에 그냥 쓰면 **무엇이 사라지는가** — 그 정본은 **어느 갈래 어느 주제**인가?

### 9. 무엇으로 받을까 (왜)

- **읽기만 하는** 함수에서 **값**을 고르는 자리 하나와 **`const T&`** 를 고르는 자리 하나를 댈 수 있는가?
- **보관하는** 함수에서 **값 + `std::move`** 가 **오버로드 쌍**을 대신할 수 있는 조건은?
- 대신할 수 **없는** 조건은?
- `std::string_view` 를 **쓰면 안 되는** 자리 둘은?
- ★ 고르는 기준을 **「크기」가 아니라 무엇**으로 잡아야 하는가?

### 10. 다른 주제와 잇기 (연결)

- lvalue·prvalue·xvalue 의 정본은 목록의 몇 번인가?
- `std::move` 가 **아무것도 옮기지 않는다**는 것의 정본은 몇 번인가?
- `std::forward` 와 **전달 참조**의 정본은 몇 번인가?
- 죽은 임시를 가리키는 뷰가 **왜 UB 인지**의 정본은 몇 번인가?
- `std::string` 과 `string_view` **자체**의 정본은 몇 번인가?
- 배열이 함수 매개변수에서 **포인터로 감쇠**하는 것은 **어느 갈래 어느 주제**인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
