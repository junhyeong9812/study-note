# cpp/syntax/12 — 클래스 기본: 멤버·접근 지정·`this` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·심볼은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **GNU nm (binutils 2.42)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이므로 **출력을 싣는 블록마다 그 출력을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — **진단 문구**와 **주소값**은 흔들리는 칸이다.\
> 근거로 쓰는 것은 **에러냐 통과냐 · 진단이 가리킨 줄 · `cc exit` · `sizeof` 값 · 심볼 개수 · 경고 개수**다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「몇 배 빠르다」는 문장이 **한 줄도 없다**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 에러 **둘** — `class` 의 기본은 `private`, `struct` 의 기본은 `public`

**출력**

```text
===== 소스: cls01.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -pedantic cls01.cpp -o ex (cc exit=1) =====
cls01.cpp: In function ‘int main()’:
cls01.cpp:12:15: error: ‘int C::hidden’ is private within this context
   12 |     int x = c.hidden;    // class 의 기본은 private — 막힌다
      |               ^~~~~~
cls01.cpp:2:15: note: declared private here
    2 | class C { int hidden = 1; };
      |               ^~~~~~
cls01.cpp:13:16: error: ‘int SPriv::shut’ is private within this context
   13 |     int y = sp.shut;     // struct 여도 private 이라고 적으면 막힌다
      |                ^~~~
cls01.cpp:6:29: note: declared private here
    6 | struct SPriv { private: int shut = 4; };
      |                             ^~~~
===== clang++ -std=c++20 -Wall -Wextra -pedantic cls01.cpp -o ex (cc exit=1) =====
cls01.cpp:12:15: error: 'hidden' is a private member of 'C'
   12 |     int x = c.hidden;    // class 의 기본은 private — 막힌다
      |               ^
cls01.cpp:2:15: note: implicitly declared private here
    2 | class C { int hidden = 1; };
      |               ^
cls01.cpp:13:16: error: 'shut' is a private member of 'SPriv'
   13 |     int y = sp.shut;     // struct 여도 private 이라고 적으면 막힌다
      |                ^
cls01.cpp:6:29: note: declared private here
    6 | struct SPriv { private: int shut = 4; };
      |                             ^
2 errors generated.
```

**왜 그런가**

- ★★★ **막히는 것은 12번 줄과 13번 줄 둘**이다. 10\~11번 줄은 통과한다.
  - `s.open` — `struct` 의 기본이 `public` 이라 통과.
  - `cp.shown` — `class` 라도 **`public:` 이라고 적었으니** 통과.
  - `c.hidden` — `class` 의 기본이 `private` 이라 **막힌다**.
  - `sp.shut` — `struct` 라도 **`private:` 이라고 적었으니** 막힌다.
- ★★★ **`class` 와 `struct` 의 문법 차이는 둘뿐**이다 — **멤버의 기본 접근**과 **기반 클래스의 기본 접근**.\
  나머지는 완전히 같다. **적어 주면 그 차이도 사라진다.**
- ★★ **clang 이 한 마디를 더 적는다** — `implicitly declared private here`.\
  g++ 의 `declared private here` 와 달리 「**내가 그렇게 정한 게 아니라 기본값이었다**」까지 말해 준다.\
  같은 자리에서 `SPriv` 쪽은 clang 도 `declared private here` 다(**직접 적은 `private:` 이기 때문**).
- ★ 진단 **문구**는 흔들리는 칸이고, **어느 줄이 막히나**가 안 흔들리는 칸이다.

### 2. ★★★ 멤버 함수를 넷 달아도 `sizeof` 는 **4** — 코드는 객체 안에 없다

**출력**

```text
===== 소스: cls03.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -pedantic cls03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof(Empty)      = 1   (멤버가 하나도 없다)
sizeof(OneInt)     = 4   (int 하나)
sizeof(ThreeFns)   = 4   (int 하나 + 멤버 함수 넷)
sizeof(WithStatic) = 4   (int 하나 + static int 하나)
sizeof(EmptyBase)  = 4   (빈 클래스를 상속 + int 하나)
sizeof(TwoBytes)   = 4   (char + short)
sizeof(Empty[3])   = 3   (빈 객체 셋을 나란히)
is_empty_v<Empty>  = 1
&arr[0] != &arr[1] = 1   (그래도 주소는 달라야 한다)
```

**왜 그런가**

| 줄 | 값 | 왜 |
|---|---|---|
| `sizeof(Empty)` | **1** | ★ 완전한 객체는 **주소가 서로 달라야** 하므로 0 이 될 수 없다 |
| `sizeof(OneInt)` | 4 | `int` 하나 |
| `sizeof(ThreeFns)` | ★★★ **4** | **멤버 함수는 객체 안에 없다** |
| `sizeof(WithStatic)` | ★★ **4** | **정적 데이터 멤버는 객체가 아니라 클래스에 하나** 있다 |
| `sizeof(EmptyBase)` | ★ **4** | **빈 기반 최적화** — 빈 기반 클래스에 자리를 안 준다 |
| `sizeof(TwoBytes)` | 4 | `char`(1) + 패딩(1) + `short`(2) — 정본은 C 갈래 [`22번`](../../../c/syntax/22-struct-padding-and-alignment/) |
| `sizeof(Empty[3])` | ★ **3** | 1바이트짜리 셋 — **`is_empty_v` 가 참이어도 자리는 1** |
| `&arr[0] != &arr[1]` | 1 | ★ 그 1바이트가 존재하는 **이유 자체**다 |

- ★★ **`sizeof(Empty)` 가 1 인 것과 `sizeof(EmptyBase)` 가 4 인 것은 모순이 아니다.**\
  **독립된 객체**는 주소가 달라야 해서 1바이트를 받고, **기반 부분**은 파생 객체와 주소를 나눠 써도 되므로 0바이트가 된다.
- ★ 이 값들은 **구현 정의**다(x86-64 Itanium ABI). 다만 **`Empty` 가 1 이상이라는 것**은 표준이 보장한다.

### 3. ★★ 부족하다 — 심볼을 세야 끝난다. `Counter::bump()` 는 **1개**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic cls04.cpp -o ex && nm -C ex | grep -c 'Counter::bump()' | sed 's/^/Counter::bump() 심볼 수 /' (exit=0) =====
Counter::bump() 심볼 수 1
===== nm -C ex | awk '/Counter::/ { sub(/^[0-9a-f]+ /, ""); print }' (exit=0) =====
W Counter::bump()
W Counter::get() const
```

**왜 그런가**

- ★★★ **`sizeof` 는 「객체 안에 없다」까지만 말한다.** 코드가 **다른 어딘가에 객체 수만큼 복제됐을 가능성**은 못 지운다.\
  그래서 **네 번째 창**이 필요하다 — `nm` 으로 **심볼을 세면** 그 가능성이 닫힌다.
- ★★ **`Counter::bump()` 심볼은 정확히 1개**다. 객체를 셋 만들어도 코드는 한 벌이다.
- ★ **`W` 는 약한 심볼(weak)** 이다. 클래스 정의 안에 본문까지 적은 멤버 함수는 **암묵적으로 `inline`** 이 되고,\
  `inline` 함수는 여러 번역 단위에 같은 정의가 생길 수 있어 **링커가 하나로 합치도록** 약한 심볼이 된다(정본은 목록의 **55번 주제**).
- ★ **`Counter::get() const` 가 별도 심볼**인 것은 **`const` 가 시그니처의 일부**이기 때문이다.\
  같은 이름의 `const`/비-`const` 오버로드가 서로 다른 함수로 존재할 수 있는 근거이고, 그 활용의 정본은 형제 [`10번`](../10-const-correctness/)이다.

### 4. ★★ 에러 **셋** — 원인은 하나, `this` 가 `const Counter*` 다

**출력**

```text
===== 소스: cls05.cpp =====
// const 멤버 함수에서 this 가 const Counter* 라는 것을 에러로 본다
struct Counter {
    int n = 0;
    void bump_const() const { ++n; }            // const 멤버 함수가 멤버를 고친다
    void call_nonconst() const { bump(); }      // const 멤버 함수가 비-const 멤버 함수를 부른다
    void bump() { ++n; }
    Counter* escape() const { return this; }    // const Counter* 를 Counter* 로 돌려준다
};
int main() { Counter c; c.bump(); }
===== g++ -std=c++20 -Wall -Wextra -pedantic cls05.cpp -o ex (cc exit=1) =====
cls05.cpp: In member function ‘void Counter::bump_const() const’:
cls05.cpp:4:33: error: increment of member ‘Counter::n’ in read-only object
    4 |     void bump_const() const { ++n; }            // const 멤버 함수가 멤버를 고친다
      |                                 ^
cls05.cpp: In member function ‘void Counter::call_nonconst() const’:
cls05.cpp:5:38: error: passing ‘const Counter’ as ‘this’ argument discards qualifiers [-fpermissive]
    5 |     void call_nonconst() const { bump(); }      // const 멤버 함수가 비-const 멤버 함수를 부른다
      |                                  ~~~~^~
cls05.cpp:6:10: note:   in call to ‘void Counter::bump()’
    6 |     void bump() { ++n; }
      |          ^~~~
cls05.cpp: In member function ‘Counter* Counter::escape() const’:
cls05.cpp:7:38: error: invalid conversion from ‘const Counter*’ to ‘Counter*’ [-fpermissive]
    7 |     Counter* escape() const { return this; }    // const Counter* 를 Counter* 로 돌려준다
      |                                      ^~~~
      |                                      |
      |                                      const Counter*
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic cls05.cpp -o ex (cc exit=1) =====
cls05.cpp:4:31: error: cannot assign to non-static data member within const member function 'bump_const'
    4 |     void bump_const() const { ++n; }            // const 멤버 함수가 멤버를 고친다
      |                               ^ ~
cls05.cpp:4:10: note: member function 'Counter::bump_const' is declared const here
    4 |     void bump_const() const { ++n; }            // const 멤버 함수가 멤버를 고친다
      |     ~~~~~^~~~~~~~~~~~~~~~~~
cls05.cpp:5:34: error: 'this' argument to member function 'bump' has type 'const Counter', but function is not marked const
    5 |     void call_nonconst() const { bump(); }      // const 멤버 함수가 비-const 멤버 함수를 부른다
      |                                  ^~~~
cls05.cpp:6:10: note: 'bump' declared here
    6 |     void bump() { ++n; }
      |          ^
cls05.cpp:7:38: error: cannot initialize return object of type 'Counter *' with an rvalue of type 'const Counter *'
    7 |     Counter* escape() const { return this; }    // const Counter* 를 Counter* 로 돌려준다
      |                                      ^~~~
3 errors generated.
```

**왜 그런가**

- ★★★ **세 에러가 전부 한 원인에서 나온다.** `const` 멤버 함수 안에서 `decltype(this)` 는 **`const Counter*`** 다.
  - `++n` → `++this->n` → **읽기 전용 객체의 멤버**를 고치려 했다.
  - `bump()` → `bump(this)` → **`Counter*` 를 요구하는 자리에 `const Counter*`** 를 넘겼다.
  - `return this;` → **`const Counter*` 를 `Counter*`** 로 돌려주려 했다.
- ★★ **`discards qualifiers`** 는 「**`const` 라는 한정자를 버리게 된다**」는 뜻이다 —\
  버려지는 것은 값이 아니라 **타입에 붙은 `const`** 다.
- ★ 이 사실은 **4번 문항의 `static_assert`**([2-summary.md](2-summary.md) (3))가 이미 증명해 둔 것이다.\
  `static_assert(std::is_same_v<decltype(this), const Counter*>)` 가 **통과했다** — 통과가 곧 근거다.
- ★ 두 컴파일러의 **에러 개수가 셋으로 같고 짚은 줄도 같다.** 문구만 다르다.

### 5. ★ 이름을 적은 그 하나에만 열린다 — `private:` 구역에 적어도 같다

**출력**

```text
===== 소스: cls06.cpp =====
// friend 는 무엇을 여나
#include <cstdio>

class Account {
public:
    explicit Account(int won) : balance_(won) {}
private:
    int balance_;
    friend void audit(const Account&);      // 이 함수 하나에만 연다
    friend class Auditor;                   // 이 클래스 전체에 연다
};

void audit(const Account& a) { std::printf("  friend 함수가 본 잔액 : %d\n", a.balance_); }

class Auditor {
public:
    static void look(const Account& a) { std::printf("  friend 클래스가 본 잔액: %d\n", a.balance_); }
};

int main() {
    Account a(1000);
    audit(a);
    Auditor::look(a);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cls06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  friend 함수가 본 잔액 : 1000
  friend 클래스가 본 잔액: 1000
```

```text
===== 소스: cls12.cpp =====
// friend 가 아니면 어디까지 막히나
class Account {
public:
    explicit Account(int won) : balance_(won) {}
private:
    int balance_;
    friend void audit(const Account&);
};

class Stranger {
public:
    static int peek(const Account& a) { return a.balance_; }   // friend 가 아니다
};

struct Derived : Account {
    using Account::Account;
    int peek() const { return balance_; }      // 파생 클래스여도 private 은 못 본다
};

void audit(const Account& a) { (void)a.balance_; }             // 이쪽은 friend 다
int also_audit(const Account& a) { return a.balance_; }        // 이름이 비슷할 뿐 friend 가 아니다

int main() { Account a(1); audit(a); return also_audit(a); }
===== g++ -std=c++20 -Wall -Wextra -pedantic cls12.cpp -o ex (cc exit=1) =====
cls12.cpp: In static member function ‘static int Stranger::peek(const Account&)’:
cls12.cpp:12:50: error: ‘int Account::balance_’ is private within this context
   12 |     static int peek(const Account& a) { return a.balance_; }   // friend 가 아니다
      |                                                  ^~~~~~~~
cls12.cpp:6:9: note: declared private here
    6 |     int balance_;
      |         ^~~~~~~~
cls12.cpp: In member function ‘int Derived::peek() const’:
cls12.cpp:17:31: error: ‘int Account::balance_’ is private within this context
   17 |     int peek() const { return balance_; }      // 파생 클래스여도 private 은 못 본다
      |                               ^~~~~~~~
cls12.cpp:6:9: note: declared private here
    6 |     int balance_;
      |         ^~~~~~~~
cls12.cpp: In function ‘int also_audit(const Account&)’:
cls12.cpp:21:45: error: ‘int Account::balance_’ is private within this context
   21 | int also_audit(const Account& a) { return a.balance_; }        // 이름이 비슷할 뿐 friend 가 아니다
      |                                             ^~~~~~~~
cls12.cpp:6:9: note: declared private here
    6 |     int balance_;
      |         ^~~~~~~~
```

**왜 그런가**

- ★★★ **`friend` 선언은 접근 지정 구역의 영향을 받지 않는다.** 위 소스에서 `friend` 둘은 **`private:` 아래**에 있는데도 그대로 동작한다.\
  `friend` 는 **멤버가 아니라 「누구에게 열어 준다」는 선언**이기 때문이다.
- ★★ **`audit` 과 `also_audit` 을 가른 것은 오직 이름**이다. 시그니처가 같아도 **`friend` 로 적힌 이름이 아니면** 막힌다.
- ★★ **파생 클래스는 `protected` 까지 본다.** `Derived::peek` 이 `balance_`(private)를 읽으려다 막혔다.
- ★ **`friend` 는 상속되지 않고 전이되지 않는다.** 내 친구가 파생돼도 친구가 아니고, 내 친구의 친구도 친구가 아니다.
- ★ 그래서 `friend` 는 **`public` 으로 여는 것보다 좁다.** 둘 중 고민되면 **범위가 작은 쪽**이 `friend` 다.

### 6. ★★★ 컴파일된다 — 이름은 뒤를 보지만 **값은 아직 없다**

**출력**

```text
===== 소스: cls07.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -pedantic cls07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  twice()  = 20
  plus()   = 13
  Inner.k  = 7
  value()  = 10
  lazy 가 value_+1 인가 : 0
  (lazy 의 값 자체는 싣지 않는다 — 13번이 그 이유를 답한다)
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic cls07.cpp -o ex (cc exit=0) =====
cls07.cpp:8:16: warning: field 'value_' is uninitialized when used here [-Wuninitialized]
    8 |     int lazy = value_ + 1;                     // 기본 멤버 초기자도 아래 이름을 찾는다
      |                ^
cls07.cpp:18:11: note: in implicit default constructor for 'Later' first required here
   18 |     Later l;
      |           ^
cls07.cpp:4:7: note: during field initialization in the implicit default constructor
    4 | class Later {
      |       ^
1 warning generated.
```

**왜 그런가**

- ★★★ **멤버 함수 본문은 「클래스를 끝까지 읽은 뒤」 컴파일된다**(완전 클래스 문맥).\
  그래서 `twice()` 가 아래에서 선언할 `value_` 를, `plus()` 가 아래에서 선언할 `helper()` 를 쓸 수 있다.\
  **`private:` 구역에 있어도 자기 멤버 함수는 본다.**
- ★★★ **마지막 두 줄이 이 문항의 핵심이다.** `lazy 가 value_+1 인가` 가 **0** 이다.\
  `lazy` 의 기본 멤버 초기자 `value_ + 1` 에서 **이름 `value_` 는 찾아졌지만**,\
  멤버는 **선언 순서**로 초기화되고 `lazy` 가 `value_` **보다 먼저** 선언돼 있어 **그 시점에 `value_` 는 아직 초기화 전**이다.\
  ★ **그 규칙의 정본은** [13번](../13-constructors-member-init-list-and-delegating/)이다.
- ★★ **g++ 는 `-Wall -Wextra -pedantic` 에서 경고 0건**이고 **clang 은 1건**이다 —\
  `field 'value_' is uninitialized when used here [-Wuninitialized]`.\
  **한 컴파일러만 보는 UB** 라서 이 주제의 「도구가 못 보는 것」 표에서 가장 중요한 줄이 된다.
- ★ 그래서 이 문서는 **`lazy` 의 값을 싣지 않는다.** 미정(indeterminate)이라 판마다 달라질 수 있고,\
  실을 수 있는 것은 **「약속이 깨졌다」는 비교 결과**뿐이다.

### 7. ★★ 에러 **하나** — 막히는 것은 **선언**이지 기본 멤버 초기자가 아니다

**출력**

```text
===== 소스: cls08.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -pedantic cls08.cpp -o ex (cc exit=1) =====
cls08.cpp:5:5: error: ‘Alias’ does not name a type
    5 |     Alias twice() const { return value_; }     // 반환 타입 — 그 자리에서 이미 알아야 한다
      |     ^~~~~
```

**왜 그런가**

- ★★★ **`Alias twice() const` 의 반환 타입만 막힌다.** 바로 아래 줄 `int lazy = value_;` 는 **에러가 아니다**.
- ★★ **한 문장으로** — **본문과 기본 멤버 초기자는 완전 클래스 문맥이라 뒤를 보고,\
  선언 자체(반환 타입·매개변수 타입)는 그 자리에서 이미 알려져 있어야 한다.**
- ★ 이것이 **클래스 정의 앞쪽에 `using`·중첩 타입을 모아 두는** 관례의 이유다 —\
  타입 이름만큼은 **위에서 아래로** 읽히기 때문이다.

### 8. ★★ 에러 **둘** — 비정적 멤버를 쓴 것과 `this` 를 쓴 것

**출력**

```text
===== 소스: cls10.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra -pedantic cls10.cpp -o ex (cc exit=1) =====
cls10.cpp: In static member function ‘static int Pool::made()’:
cls10.cpp:4:32: error: invalid use of member ‘Pool::next_’ in static member function
    4 |     static int made() { return next_; }        // 정적 멤버 함수가 비정적 멤버를 본다
      |                                ^~~~~
cls10.cpp:8:9: note: declared here
    8 |     int next_ = 1;
      |         ^~~~~
cls10.cpp: In static member function ‘static int Pool::addr()’:
cls10.cpp:5:43: error: ‘this’ is unavailable for static member functions
    5 |     static int addr() { return (int)(long)this; }  // 정적 멤버 함수에서 this 를 쓴다
      |                                           ^~~~
```

**왜 그런가**

- ★★★ **정적 멤버 함수에는 `this` 가 없다.** g++ 가 그것을 **두 문장으로 갈라** 말한다.
  - `invalid use of member 'Pool::next_' in static member function` — **어느 객체의 `next_` 인지 정할 수가 없다.**
  - `'this' is unavailable for static member functions` — **원인 자체**를 그대로 적었다.
- ★★ **정적 데이터 멤버는 선언과 정의가 다르다.**\
  클래스 안의 `static int count_;` 는 **선언**이고, 클래스 밖의 `int Pool::count_ = 0;` 이 **정의**다.\
  정의를 빠뜨리면 컴파일은 되고 **링커에서 막힌다.**
- ★★ **C++17 의 `static inline int born = 0;`** 은 그 짝을 없앤다 — **클래스 안 한 줄이 곧 정의**다.\
  정본은 [목록의 **25번 주제**](../25-static-members-and-inline-variables/)다.
- ★ 정적 멤버가 살아 있는 동안과 **언제 파괴되는가**는 [14번](../14-destructors-and-deterministic-destruction/)이 답한다.

### 9. ★★★ 경고 **0건**에 **`cc exit=0`** — 그런데 둘 다 ISO C++ 위반

**출력**

```text
===== 소스: cls11.cpp =====
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
===== g++ -std=c++20 -Wall -Wextra cls11.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof(ZeroArray) = 0
sizeof(Anon)      = 8
a.x + a.y         = 3   (이름 없이 바로 쓴다)
===== g++ -std=c++20 -Wall -Wextra -pedantic cls11.cpp -o ex (cc exit=0) =====
cls11.cpp:3:26: warning: ISO C++ forbids zero-size array ‘a’ [-Wpedantic]
    3 | struct ZeroArray { int a[0]; };               // ISO C++ 가 금지하는 크기 0 배열
      |                          ^
cls11.cpp:3:24: warning: zero-size array member ‘ZeroArray::a’ in an otherwise empty ‘struct ZeroArray’ [-Wpedantic]
    3 | struct ZeroArray { int a[0]; };               // ISO C++ 가 금지하는 크기 0 배열
      |                        ^
cls11.cpp:3:8: note: in the definition of ‘struct ZeroArray’
    3 | struct ZeroArray { int a[0]; };               // ISO C++ 가 금지하는 크기 0 배열
      |        ^~~~~~~~~
cls11.cpp:4:22: warning: ISO C++ prohibits anonymous structs [-Wpedantic]
    4 | struct Anon { struct { int x; int y; }; };    // ISO C++ 가 금지하는 익명 struct
      |                      ^
===== clang++ -std=c++20 -Wall -Wextra cls11.cpp -o ex (cc exit=0) =====
===== clang++ -std=c++20 -Wall -Wextra -pedantic cls11.cpp -o ex (cc exit=0) =====
cls11.cpp:3:26: warning: zero size arrays are an extension [-Wzero-length-array]
    3 | struct ZeroArray { int a[0]; };               // ISO C++ 가 금지하는 크기 0 배열
      |                          ^
cls11.cpp:4:15: warning: anonymous structs are a GNU extension [-Wgnu-anonymous-struct]
    4 | struct Anon { struct { int x; int y; }; };    // ISO C++ 가 금지하는 익명 struct
      |               ^
2 warnings generated.
```

```text
===== echo "cls07 나중 선언 읽기  g++   경고 $(g++ -std=c++20 -Wall -Wextra -pedantic cls07.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
cls07 나중 선언 읽기  g++   경고 0
===== echo "cls07 나중 선언 읽기  clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic cls07.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
cls07 나중 선언 읽기  clang 경고 1
===== echo "g++  -Wall -Wextra          경고 $(g++ -std=c++20 -Wall -Wextra cls11.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
g++  -Wall -Wextra          경고 0
===== echo "g++  -Wall -Wextra -pedantic 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic cls11.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
g++  -Wall -Wextra -pedantic 경고 3
===== echo "clang -Wall -Wextra          경고 $(clang++ -std=c++20 -Wall -Wextra cls11.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
clang -Wall -Wextra          경고 0
===== echo "clang -Wall -Wextra -pedantic 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic cls11.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
clang -Wall -Wextra -pedantic 경고 2
```

**왜 그런가**

| 플래그 | g++ | clang |
|---|---|---|
| `-Wall -Wextra` | ★★★ **경고 0건 · `cc exit=0`** | ★★★ **경고 0건 · `cc exit=0`** |
| `-Wall -Wextra -pedantic` | **3건** | **2건** |

- ★★★ **「돌아갔다」가 「표준에 맞다」가 아니다.** `-Wall -Wextra` 만으로는 **둘 다 완전히 조용하다.**\
  `-pedantic` 을 붙여야 g++ 가 `ISO C++ forbids zero-size array` 와 `ISO C++ prohibits anonymous structs` 를 말한다.
- ★★ **`sizeof(ZeroArray)` 가 0 이다.** 2번 문항에서 본 「**완전한 객체는 1 이상**」이 이 확장에서는 **깨진다** —\
  표준이 그 배열을 금지하는 이유가 그 한 줄에 그대로 나와 있다.
- ★ **`-std=c++20` 은 강제가 아니라 기본값 선택**이다. 표준 준수를 주장하려면 **`-pedantic` 이 필요**하다.\
  같은 모양이 C 갈래에서도 나왔다(C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **07번**).
- ★ **진단 이름의 잘기가 다르다** — g++ 는 `-Wpedantic` 하나로 묶고,\
  clang 은 `-Wzero-length-array`·`-Wgnu-anonymous-struct` 로 갈라 **각각 끌 수 있게** 해 둔다.

### 10. 컴파일러는 규칙을 전부 막지만, **설계는 아무도 안 본다**

**출력**

```text
===== echo "cls07 나중 선언 읽기  g++   경고 $(g++ -std=c++20 -Wall -Wextra -pedantic cls07.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
cls07 나중 선언 읽기  g++   경고 0
===== echo "cls07 나중 선언 읽기  clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic cls07.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
cls07 나중 선언 읽기  clang 경고 1
===== echo "g++  -Wall -Wextra          경고 $(g++ -std=c++20 -Wall -Wextra cls11.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
g++  -Wall -Wextra          경고 0
===== echo "g++  -Wall -Wextra -pedantic 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic cls11.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
g++  -Wall -Wextra -pedantic 경고 3
===== echo "clang -Wall -Wextra          경고 $(clang++ -std=c++20 -Wall -Wextra cls11.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
clang -Wall -Wextra          경고 0
===== echo "clang -Wall -Wextra -pedantic 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic cls11.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
clang -Wall -Wextra -pedantic 경고 2
```

**왜 그런가**

- ★★★ **접근 규칙 자체는 컴파일러가 전부 막는다.** 이 주제에서 **「조용히 틀리는」 자리는 둘뿐**이었다 —\
  **표준 위반 확장**(9번, `-pedantic` 이 잡는다)과 **초기화 전 멤버 읽기**(6번, **clang 만** 잡는다).
- ★★★ **`private` 을 전부 `public` 으로 바꿔도 경고 0건**이다. `friend` 를 열 개 달아도 마찬가지다.\
  **캡슐화가 무너졌다는 것은 어떤 도구도 말해 주지 않는다** — 그것이 이 주제를 사람이 읽어야 하는 이유다.
- ★★ **런타임 sanitizer 는 「부적용」이다.** 「재 봤더니 조용했다」가 아니라 「**잴 것이 없다**」다 —\
  접근 지정과 `this` 는 **컴파일이 끝나면 기계어에 흔적이 남지 않는다.**\
  ASan·UBSan 에게 물어볼 대상 자체가 없다.

### 11. 이어지는 자리

- **`this` 가 포인터인 배경** — 형제 [`07번`](../07-references-vs-pointers/)(참조는 재결합되지 않는다).
- **`const` 멤버 함수의 설계 활용** — 형제 [`10번`](../10-const-correctness/). 여기서는 **`this` 의 타입**까지만 썼다.
- **구조체 패딩** — C 갈래 [`22-struct-padding-and-alignment/`](../../../c/syntax/22-struct-padding-and-alignment/)가 정본이다.
- **멤버 초기화 순서** — [13번](../13-constructors-member-init-list-and-delegating/). 6번 문항의 `lazy` 가 거기서 풀린다.
- **정적 멤버와 `inline` 변수** — [목록의 **25번 주제**](../25-static-members-and-inline-variables/).
- **러스트의 데이터·코드 분리** — 러스트 갈래 [`16-structs-impl-and-associated-functions/`](../../../rust/syntax/16-structs-impl-and-associated-functions/).\
  C++ 이 한 중괄호에 넣은 것을 `struct` 와 `impl` 로 **아예 갈라 적는다.**

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cls01.cpp` 기본 접근 | g++ · clang 각 1회 | ★ 양쪽 **에러 2건 · `cc exit=1`**, 짚은 줄 동일 |
| `cls02.cpp` 접근 지정 셋 | g++ 1회 | 에러 3건(파생의 `private` · 밖에서 `protected`·`private`) |
| `cls03.cpp` `sizeof` | g++ 1회 | ★★ **1 · 4 · 4 · 4 · 4 · 4 · 3**, `is_empty_v` 1 |
| `cls04.cpp` `this` | g++ 1회 + `nm` 2회 | ★★★ `static_assert` 둘 통과 · **심볼 1개** · 멤버 포인터 8/16 |
| `cls05.cpp` `const` 멤버 함수 | g++ · clang 각 1회 | 양쪽 **에러 3건** |
| `cls06.cpp` / `cls12.cpp` `friend` | g++ 각 1회 | 통과(잔액 1000 두 번) / **에러 3건** |
| `cls07.cpp` 완전 클래스 문맥 | g++ · clang 각 1회 | ★★ g++ **경고 0건** · clang **1건** · `lazy` 비교 **0** |
| `cls08.cpp` 선언의 이름 | g++ 1회 | **에러 1건**(반환 타입만) |
| `cls09.cpp` 정적·중첩 | g++ 1회 | `h1=1 h2=2 h3=1` · `made()=3` · `born=2` |
| `cls10.cpp` 정적 멤버 함수 | g++ 1회 | **에러 2건** |
| `cls11.cpp` 표준 위반 확장 | g++ · clang 각 2회(플래그 2종) | ★★★ `-Wall -Wextra` **0건·exit 0** / `-pedantic` g++ 3 · clang 2 |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · binutils 2.42)에서만** 그렇다.

- ★★ **`sizeof` 값 전부** — `int` 가 4인 것, `TwoBytes` 의 패딩, **빈 기반 최적화가 적용된 것**.
- ★★ **멤버 포인터 크기 8 / 16** — Itanium ABI 의 결과다.
- ★ **심볼이 약한 심볼(`W`)인 것**과 맹글링 이름의 모양.
- ★ **진단 문구·경고 이름 전부**(`-Wpedantic` 대 `-Wzero-length-array`).
- ★ **크기 0 배열과 익명 struct 를 받아 준다는 것** — GNU 확장이다. 다른 컴파일러에서는 다를 수 있다.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **`class` 의 기본 접근이 `private`, `struct` 가 `public` 인** 것.
- **완전한 객체의 크기가 1 이상인** 것.
- **정적 데이터 멤버가 객체 크기에 안 들어가는** 것.
- **비정적 멤버 함수에만 `this` 가 있고, `const` 멤버 함수에서 `const T*` 인** 것.
- **멤버 함수 본문·기본 멤버 초기자가 완전 클래스 문맥인** 것.
- **`friend` 가 상속·전이되지 않는** 것.
- **멤버가 선언 순서로 초기화되는** 것(정본은 [13번](../13-constructors-member-init-list-and-delegating/)).

**UB 의 결과라 보장이 아닌 것**(관찰로만 읽는다)

- ★ 6번의 **`lazy` 값** — 초기화 전 멤버를 읽었으므로 **미정**이다.\
  근거로 쓰는 것은 「**`lazy == value_+1` 이 0 이었다**」와 「**clang 이 `-Wuninitialized` 로 짚었다**」뿐이다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **`-std=c++14` 이하 판**(`static inline` 이 안 되는 자리를 에러로 받지 않았다) ·\
  ★ **최적화를 켠 판**(전부 기본값으로만 돌렸다) · ★ **다른 ABI**(ARM·Windows) ·\
  ★ **`[[no_unique_address]]`** 를 붙인 판 · ★ **여러 번역 단위로 나눈 판**(심볼 병합을 직접 보지 않았다) ·\
  ★ **`protected` 상속·`private` 상속**(기반 접근의 기본값 차이는 [목록의 **19번 주제**](../19-inheritance-virtual-functions-override-final/)로 미뤘다).
- **못 잰 것** — ★★★ **「캡슐화가 잘 됐는가」.** 이 문서가 잰 것은 **컴파일러가 막느냐**까지다.\
  **설계의 옳고 그름을 재는 도구는 이 환경에 없다.**
- ★ **「부적용인 창」** — **런타임 sanitizer.** 접근 지정은 런타임에 아무것도 아니므로 **잴 것이 없다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **g++ 가 6번의 초기화 전 읽기를 경고하기 시작했는지**(지금은 **0건**, clang 은 1건).\
  **가장 먼저 움직일 칸**이다.
- ★★ **크기 0 배열·익명 struct 가 계속 받아들여지는지**(9번) — 확장을 거두면 **에러로 바뀐다**.
- ★ **`sizeof` 값**(ABI 가 바뀌면 움직인다) · **멤버 포인터 16바이트**.
- ★ **진단 문구와 경고 이름**(clang 의 `-Wgnu-anonymous-struct` 등).
