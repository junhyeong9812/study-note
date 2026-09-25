# cpp/syntax/12 — 클래스 기본: 멤버·접근 지정·`this` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · GNU nm (binutils 2.42) · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★ 이 주제의 답은 **대부분 컴파일러 진단**이다 — 「막히나 통과하나」를 먼저 답하고, 그다음 **왜**를 답한다.
> ★★ **네 번째 창은 `nm` 의 심볼 개수**다(3번). `sizeof` 가 못 끝내는 자리를 그것만 끝낸다.
> ★ **「부적용인 창」이 있다** — 런타임 sanitizer. 접근 지정은 컴파일이 끝나면 사라져 **잴 것이 없다**.
> 선행 — 형제 [`07번`](../07-references-vs-pointers/)(참조와 포인터)과 형제 [`10번`](../10-const-correctness/)(`const`)이 이 주제의 바로 옆이다.
> 이어지는 것 — [13번](../13-constructors-member-init-list-and-delegating/) · [14번](../14-destructors-and-deterministic-destruction/) · [15번](../15-raii-resources-as-types/)이 한 사슬이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 같은 멤버를 넷에 나눠 적으면 (예측)

```cpp
/* cls01.cpp */
// class 와 struct 의 기본 접근을 에러로 가른다
class C { int hidden = 1; };
struct S { int open = 2; };

class CPub { public: int shown = 3; };
struct SPriv { private: int shut = 4; };

int main() {
    C c; S s; CPub cp; SPriv sp;
    int a = s.open;      // struct 의 기본은 public — 된다
    int b = cp.shown;    // class 여도 public 이라고 적으면 된다
    int x = c.hidden;    // class 의 기본은 private — 막힌다
    int y = sp.shut;     // struct 여도 private 이라고 적으면 막힌다
    return a + b + x + y;
}
```

- 이 파일은 **컴파일되는가**, 아니면 **몇 개의 에러**가 나는가?
- 에러가 난다면 **어느 줄**인가 — 그리고 **어느 줄은 안 나는가**?
- `class` 와 `struct` 가 **다른 점은 몇 가지**인가?
- ★ clang 이 g++ 보다 **한 마디를 더 적는다** — 무엇을 더 말해 주는가?

### 2. ★★★ 멤버 함수를 넷 달면 객체가 얼마나 커지나 (예측)

```cpp
/* cls03.cpp */
// 객체에 무엇이 들어 있나 — sizeof 로 센다
#include <cstdio>
#include <type_traits>

struct Empty {};
struct OneInt { int a; };
struct ThreeFns { int a; void f1(); void f2(); void f3(); static void s1(); };
struct WithStatic { int a; static int shared; };
int WithStatic::shared = 0;
struct EmptyBase : Empty { int a; };
struct TwoBytes { char c; short s; };

int main() {
    std::printf("sizeof(Empty)      = %zu   (멤버가 하나도 없다)\n", sizeof(Empty));
    std::printf("sizeof(OneInt)     = %zu   (int 하나)\n", sizeof(OneInt));
    std::printf("sizeof(ThreeFns)   = %zu   (int 하나 + 멤버 함수 넷)\n", sizeof(ThreeFns));
    std::printf("sizeof(WithStatic) = %zu   (int 하나 + static int 하나)\n", sizeof(WithStatic));
    std::printf("sizeof(EmptyBase)  = %zu   (빈 클래스를 상속 + int 하나)\n", sizeof(EmptyBase));
    std::printf("sizeof(TwoBytes)   = %zu   (char + short)\n", sizeof(TwoBytes));
    Empty arr[3];
    std::printf("sizeof(Empty[3])   = %zu   (빈 객체 셋을 나란히)\n", sizeof(arr));
    std::printf("is_empty_v<Empty>  = %d\n", (int)std::is_empty_v<Empty>);
    std::printf("&arr[0] != &arr[1] = %d   (그래도 주소는 달라야 한다)\n", (int)(&arr[0] != &arr[1]));
}
```

- 아홉 줄의 출력을 **숫자로** 맞힐 수 있는가?
- ★ `sizeof(Empty)` 가 **0 이 아닌 이유**는 무엇인가?
- ★ `sizeof(ThreeFns)` 와 `sizeof(WithStatic)` 이 `sizeof(OneInt)` 와 **같은** 이유는 각각 무엇인가?
- `sizeof(EmptyBase)` 가 **8 이 아닌** 이유는?

### 3. ★★ `sizeof` 가 안 늘었다는 것으로 충분한가 (왜)

- 「멤버 함수는 객체마다 복제되지 않는다」를 **`sizeof` 만으로 증명할 수 있는가**?
- 그 답을 끝내려면 **무엇을 더 봐야** 하는가?
- `nm -C` 가 찍은 `Counter::bump()` 심볼은 **몇 개**인가?
- ★ 그 심볼 앞의 `W` 는 무슨 뜻이며 **왜 그렇게 되었나**?
- ★ `Counter::get() const` 가 **별도의 심볼**인 이유는?

### 4. ★★ `const` 멤버 함수에 이 셋을 적으면 (예측)

```cpp
/* cls05.cpp */
// const 멤버 함수에서 this 가 const Counter* 라는 것을 에러로 본다
struct Counter {
    int n = 0;
    void bump_const() const { ++n; }            // const 멤버 함수가 멤버를 고친다
    void call_nonconst() const { bump(); }      // const 멤버 함수가 비-const 멤버 함수를 부른다
    void bump() { ++n; }
    Counter* escape() const { return this; }    // const Counter* 를 Counter* 로 돌려준다
};
int main() { Counter c; c.bump(); }
```

- 에러는 **몇 개**이고 **어느 줄**인가?
- ★ 셋의 **원인은 하나**다 — 무엇인가?
- `decltype(this)` 는 `const` 멤버 함수 안에서 **무슨 타입**인가?
- g++ 가 두 번째 에러에 쓴 **`discards qualifiers`** 는 무엇이 버려진다는 말인가?

### 5. ★ `friend` 가 여는 범위 (경계)

- `friend` 를 **`private:` 구역에 적으면** 효력이 달라지는가?
- ★ `audit` 은 되는데 `also_audit` 은 막힌다 — **무엇이 그 둘을 갈랐나**?
- **파생 클래스**는 기반의 `private` 을 보는가, `protected` 를 보는가?
- ★ `friend` 는 **상속되는가**? **전이되는가**(친구의 친구)?

### 6. ★★★ 클래스 안에서 뒤에 선언한 것을 쓰면 (예측)

```cpp
/* cls07.cpp */
// 클래스 안에서 선언 순서가 어디까지 자유로운가 — 이름 찾기는 자유롭다
#include <cstdio>

class Later {
public:
    int twice() const { return value_ * 2; }   // 본문이 아래에서 선언할 멤버를 쓴다
    int plus() const { return value_ + helper(); }
    int lazy = value_ + 1;                     // 기본 멤버 초기자도 아래 이름을 찾는다
    class Inner { public: int k = 7; };        // 중첩 클래스
    Inner make() const { return Inner{}; }
    int value() const { return value_; }
private:
    int helper() const { return 3; }           // 위에서 부른 함수를 여기서 선언한다
    int value_ = 10;                           // 위에서 쓴 멤버를 여기서 선언한다
};

int main() {
    Later l;
    std::printf("  twice()  = %d\n", l.twice());
    std::printf("  plus()   = %d\n", l.plus());
    std::printf("  Inner.k  = %d\n", l.make().k);
    std::printf("  value()  = %d\n", l.value());
    std::printf("  lazy 가 value_+1 인가 : %d\n", (int)(l.lazy == l.value() + 1));
    std::printf("  (lazy 의 값 자체는 싣지 않는다 — 13번이 그 이유를 답한다)\n");
}
```

- 이 파일은 **컴파일되는가**?
- 출력 다섯 줄 중 **마지막 두 줄**은 무엇을 말하는가?
- ★ `lazy` 는 왜 그런 답이 나오는가 — 그 규칙의 **정본은 몇 번 주제**인가?
- ★★ **g++ 와 clang 의 경고 개수가 다르다** — 각각 몇 건인가?

### 7. ★★ 같은 「나중 선언」인데 이쪽은 막힌다 (경계)

```cpp
/* cls08.cpp */
// 같은 「나중 선언」인데 한쪽만 막힌다
#include <cstdio>
class Later {
public:
    Alias twice() const { return value_; }     // 반환 타입 — 그 자리에서 이미 알아야 한다
    int lazy = value_;                         // 기본 멤버 초기자 — 이쪽은 어떤가
private:
    using Alias = int;
    int value_ = 10;
};
int main() { Later l; std::printf("%d\n", l.lazy); }
```

- **에러는 몇 개**이고, 두 줄 중 **어느 쪽**이 막히는가?
- ★ **본문·기본 멤버 초기자**와 **선언**을 가르는 규칙을 한 문장으로 말할 수 있는가?

### 8. ★★ 정적 멤버 함수에 이 둘을 적으면 (예측)

```cpp
/* cls10.cpp */
// 정적 멤버 함수에 this 가 없다는 것을 에러로 본다
class Pool {
public:
    static int made() { return next_; }        // 정적 멤버 함수가 비정적 멤버를 본다
    static int addr() { return (int)(long)this; }  // 정적 멤버 함수에서 this 를 쓴다
    static int count_;
private:
    int next_ = 1;
};
int main() { return Pool::made(); }
```

- 에러는 **몇 개**이고 각각 **무엇을 짚는가**?
- ★ 정적 멤버 함수에 **없는 것**은 무엇인가?
- 정적 데이터 멤버의 **선언**과 **정의**는 어디에 각각 적는가 — C++17 이 그것을 어떻게 바꿨는가?

### 9. ★★★ 이 두 멤버 선언을 네 가지 플래그로 던지면 (예측)

```cpp
/* cls11.cpp */
// 종료 코드가 0인데 표준이 금지하는 것 둘
#include <cstdio>
struct ZeroArray { int a[0]; };               // ISO C++ 가 금지하는 크기 0 배열
struct Anon { struct { int x; int y; }; };    // ISO C++ 가 금지하는 익명 struct
int main() {
    ZeroArray z; Anon a; a.x = 1; a.y = 2;
    std::printf("sizeof(ZeroArray) = %zu\n", sizeof z);
    std::printf("sizeof(Anon)      = %zu\n", sizeof a);
    std::printf("a.x + a.y         = %d   (이름 없이 바로 쓴다)\n", a.x + a.y);
}
```

- `g++ -Wall -Wextra` 로 **경고는 몇 건**이고 **`cc exit`** 은 얼마인가?
- ★ `-pedantic` 을 붙이면 **몇 건**이 되는가 — clang 은?
- ★★ `sizeof(ZeroArray)` 는 얼마이며, 그 값이 **2번 문항의 어느 사실과 부딪히는가**?
- ★ 「`-std=c++20` 으로 돌렸다」가 「C++20 으로 검증했다」가 **아닌 이유**는?

### 10. 어느 도구가 무엇까지 보나 (경계)

- 접근 위반 중 **컴파일러가 못 잡는 것**이 있는가?
- ★ `private` 을 전부 `public` 으로 바꾸면 **어느 도구가** 무슨 말을 하는가?
- ★★ 이 주제에서 **런타임 sanitizer 가 「부적용」인 이유**를 한 문장으로 말할 수 있는가?

### 11. 다른 주제와 잇기 (연결)

- `this` 가 **포인터**라는 사실의 배경(참조와의 차이)은 형제 몇 번인가?
- `const` 멤버 함수를 **설계에 쓰는 법**의 정본은 형제 몇 번인가?
- 구조체 **패딩**의 정본은 **어느 갈래 어느 주제**인가?
- 멤버 **초기화 순서**의 정본은 몇 번인가?
- 정적 멤버와 **`inline` 변수**의 정본은 몇 번인가?
- ★ 러스트는 데이터와 코드를 **어떻게 갈라 적는가** — 어느 갈래 어느 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
