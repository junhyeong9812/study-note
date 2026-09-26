# cpp/syntax/05 — `auto`·`decltype` 과 타입 추론 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — `auto` 가 **무엇을 떨어뜨리는지**,
> `decltype` 이 **무엇을 그대로 베끼는지**를 맞힐 수 있는지 묻는다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 답은 「출력」이 아니라 「타입」이다.** 타입은 실행 출력으로 안 보인다 —
> 그래서 **정의 없는 템플릿에 넣어 의도적으로 타입 에러를 받는다.**
> ```text
> template <class T> struct TypeOf;   // 선언만 — 정의가 없다
> TypeOf<decltype(x)> probe;          // error: ... TypeOf<int> ... incomplete type
> ```
> 아래 블록들은 **전부 컴파일 에러가 나는 것이 정상**이다. 읽을 것은 **`TypeOf<...>` 의 꺾쇠 안**이다.
> 선행 — 형제 [`07번`](../07-references-vs-pointers/)(참조와 포인터). `auto&`·`auto&&` 가 무엇인지가 거기서 온다.
> 형제 [`04번`](../04-brace-initialization-narrowing-and-initializer-list/)의 `auto x{1}` 대 `auto x = {1}` 도 같이 본다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ `auto` 아홉 줄 (예측)

```cpp
/* dedu01.cpp */
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
```

- 아홉 개의 타입을 **각각** 댈 수 있는가?
- ①과 ③을 가르는 것은 무엇인가 — 왜 하나는 `const` 가 떨어지고 하나는 남는가?
- ⑦과 ⑧이 **다른 타입**인 이유는?
- 규칙을 **한 문장**으로 말하면?

### 2. ★★★ `decltype` 열두 줄 — 괄호 하나 (예측)

```cpp
/* dedu02.cpp */
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
```

- `decltype(i)` 와 `decltype((i))` 가 **다른가**? 다르다면 왜?
- `decltype(ci)` 와 `decltype((ci))` 는?
- `decltype(f)` 와 `decltype(f(1.0))` 의 차이는?
- `decltype(arr)` 는 감쇠하는가?
- `decltype(v[0])` 는 왜 참조인가 — `decltype(i + 1)` 은 왜 아닌가?

### 3. ★ 배열과 함수 (예측)

```cpp
/* dedu03.cpp */
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
```

- 네 타입을 각각 댈 수 있는가?
- `auto` 와 `auto&` 중 **감쇠를 막는 쪽**은?
- 함수 이름에 `auto&` 를 붙이면 무엇이 되는가?
- 이 규칙이 **어느 갈래 어느 주제**와 같은 이야기인가?

### 4. ★★★ `auto` 가 복사를 안 하는 자리 (예측)

```cpp
/* dedu04.cpp */
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
```

- `b0` 와 `c0` 중 **원본이 바뀐 뒤에도 옛 값을 들고 있는** 쪽은?
- `sizeof(b0)` 와 `sizeof(c0)` 는 각각 얼마인가?
- `auto` 가 「값을 복사한다」인데 왜 이런 일이 나는가?
- 이런 타입을 부르는 이름은 무엇이고, 고치려면 무엇을 쓰는가?

### 5. ★★ `auto` 반환과 `decltype(auto)` 반환 (예측)

```cpp
/* dedu05.cpp */
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
```

- `f2(0) = 99;` 가 컴파일되는가? 되면 `g_v[0]` 이 무엇이 되는가?
- 같은 줄을 `f1` 로 바꾸면 무엇이 나오는가?
- 두 반환 타입이 각각 무엇으로 추론되는가?
- 언제 `decltype(auto)` 를 쓰는가?

### 6. ★★ 괄호 하나가 만드는 댕글링 (예측)

```cpp
/* dedu07.cpp */
// decltype(auto) 가 참조를 남긴다는 것은 댕글링도 남긴다는 뜻이다
int make() { return 42; }

decltype(auto) leak() {
    int local = make();
    return (local);          // 괄호 하나 때문에 int& 가 된다
}

int main() { return leak(); }
```

- `leak()` 의 반환 타입이 무엇으로 추론되는가?
- 컴파일되는가 — **종료 코드**는?
- 경고 이름은 무엇인가?
- `-fsanitize=undefined` 로 돌리면 **몇 줄**이 나오는가? 실행 종료 코드는?
- `return local;`(괄호 없이)로 바꾸면 달라지는가?

### 7. 범위 for 에서 복사가 몇 번 (경계)

```cpp
/* dedu08.cpp */
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
```

- 세 루프에서 「복사」가 각각 몇 번 찍히는가?
- 루프 전에 찍히는 복사는 **누가** 낸 것인가?
- `const auto&` 와 `auto&` 중 **읽기만 할 때** 무엇을 쓰는가?
- 어떤 경우에 `auto` (값)가 **오히려 맞는가**?

### 8. `auto` 가 못 쓰이는 자리 (경계)

```cpp
/* dedu09.cpp */
// auto 가 못 쓰이는 자리 넷
struct S {
    auto m = 0;                  // ① 비정적 멤버
};

auto g;                          // ② 초기화 없는 변수

void take(auto x);               // ③ C++20 축약 템플릿 — 이건 된다
auto h();                        // ④ 정의 없이 선언만 한 반환 타입 추론 함수

int main() { return h(); }
```

- 넷 중 **에러가 나는 것**은 몇 개인가?
- `void take(auto x);` 는 되는가 — **언제부터**인가?
- `-std=c++17` 로 던지면 그 줄이 어떻게 되는가 — 에러인가 경고인가?
- `auto h();` 를 정의 없이 쓰면 무엇이 나오는가?

### 9. `auto` 를 언제 쓰고 언제 안 쓰나 (왜)

- `auto` 가 **막아 주는** 버그 두 가지를 댈 수 있는가?
- `auto` 가 **숨기는** 것 두 가지는?
- 반환 타입에 `auto` 를 쓸 때 **헤더 쪽에서 치르는 값**은 무엇인가?
- 「거의 언제나 `auto`」라는 조언의 **경계**는 어디인가?

### 10. 다른 주제와 잇기 (연결)

- `auto` 의 추론 규칙은 **어느 주제의 규칙과 거의 같은가**?
- `auto&&` 가 「전달 참조」가 되는 규칙의 정본은 목록의 몇 번인가?
- `auto x = {1}` 이 `initializer_list` 가 되는 것의 정본은 형제 몇 번인가?
- `decltype(auto)` 로 지역을 돌려주면 생기는 문제의 정본은 목록의 몇 번인가?
- `auto` 로 받은 프록시가 무는 자리(`vector<bool>`)의 컨테이너 쪽 정본은 목록의 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
