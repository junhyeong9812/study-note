# cpp/syntax/06 — 네임스페이스와 ADL — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·심볼은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **GNU nm 2.42** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이라 질문 쪽 발췌와 어긋날 수 있다 —\
> 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★★ 이 주제의 네 번째 창은 **오브젝트 파일의 심볼**(`nm -C`)이다(6번).
> **읽는 법** — 이 주제에는 **미정의 동작이 없다.** 조심할 것은 **진단이 안 나는 쪽**이다 —\
> 5번과 4번이 그 자리이고, 근거는 **실행 출력**뿐이다.\
> 심볼 **주소**는 흔들리는 칸이다. 근거로 쓰는 것은 **이름**과 **`T`/`t` 표시**다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 찾아진다 — 인자가 서랍을 열어 준다

**출력**

```text
===== 소스: ns01.cpp =====
// 한정 없이 불렀는데 찾아진다 — 인자 의존 탐색(ADL)
#include <cstdio>

namespace lib {
    struct Widget { int v; };
    void touch(const Widget& w) { std::printf("lib::touch v=%d\n", w.v); }
    void reset()                { std::printf("lib::reset\n"); }
}

int main() {
    lib::Widget w{7};
    touch(w);          // ① 인자의 네임스페이스가 후보에 얹힌다
    lib::reset();      // ② 인자가 없으니 한정 이름으로만
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ns01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
lib::touch v=7
lib::reset
```

**왜 그런가**

- **`touch(w)`** — `w` 의 타입이 `lib::Widget` 이라 **`lib` 가 연관 네임스페이스**가 되고,\
  `lib::touch` 가 **후보 집합에 얹힌다.** 그 장치의 이름이 **인자 의존 탐색(ADL)**,\
  옛 이름으로는 **쾨니그 탐색**이다.
- **`reset()`** — **인자가 없다.** 연관 네임스페이스가 없으니 ADL 이 아무것도 안 얹고,\
  보통 탐색은 전역까지 올라가도 `reset` 을 못 찾는다. 그래서 `lib::` 를 붙여야 한다.
- ★★ **ADL 이 없었다면 연산자를 못 쓴다.** `std::cout << x` 의 `operator<<` 는 `std` 안에 있는데\
  아무도 `std::operator<<(std::cout, x)` 라고 적지 않는다. **ADL 이 그것을 대신 찾아 준다.**

### 2. ★★ 에러 **셋** — 그런데 ①은 「못 찾았다」가 아니다

**출력**

```text
===== 소스: ns02.cpp =====
// ADL 이 도는 자리와 안 도는 자리
namespace lib {
    struct Widget { int v; };
    void reset() {}
    void touch(const Widget&) {}
}

int main() {
    lib::Widget w{1};
    touch(&w);           // ① 포인터를 넘기면 — ADL 은 도는가?
    reset();             // ② 인자가 없다 — 연관 네임스페이스가 없다
    int i = 0;
    touch(i);            // ③ 인자 타입이 무관하다
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ns02.cpp -o ex (cc exit=1) =====
ns02.cpp: In function ‘int main()’:
ns02.cpp:10:11: error: invalid initialization of reference of type ‘const lib::Widget&’ from expression of type ‘lib::Widget*’
   10 |     touch(&w);           // ① 포인터를 넘기면 — ADL 은 도는가?
      |           ^~
ns02.cpp:5:16: note: in passing argument 1 of ‘void lib::touch(const Widget&)’
    5 |     void touch(const Widget&) {}
      |                ^~~~~~~~~~~~~
ns02.cpp:11:5: error: ‘reset’ was not declared in this scope; did you mean ‘lib::reset’?
   11 |     reset();             // ② 인자가 없다 — 연관 네임스페이스가 없다
      |     ^~~~~
      |     lib::reset
ns02.cpp:4:10: note: ‘lib::reset’ declared here
    4 |     void reset() {}
      |          ^~~~~
ns02.cpp:13:5: error: ‘touch’ was not declared in this scope; did you mean ‘lib::touch’?
   13 |     touch(i);            // ③ 인자 타입이 무관하다
      |     ^~~~~
      |     lib::touch
ns02.cpp:5:10: note: ‘lib::touch’ declared here
    5 |     void touch(const Widget&) {}
      |          ^~~~~
```

**왜 그런가**

| 줄 | 에러 | 뜻 |
|---|---|---|
| ① `touch(&w)` | ``invalid initialization of reference ... from expression of type `lib::Widget*` `` | ★ **찾았는데 안 맞는다** |
| ② `reset()` | ``  `reset` was not declared in this scope`` | **못 찾았다** |
| ③ `touch(i)` | ``  `touch` was not declared in this scope`` | **못 찾았다** |

- ★★★ **①이 증명하는 것** — 에러가 **오버로드 쪽**(참조 바인딩 실패)이고 `note: in passing argument 1 of 'void lib::touch(const Widget&)'` 까지 붙었다.\
  **`lib::touch` 라는 후보를 이미 찾아냈다**는 뜻이다.\
  → **포인터 인자도 「가리키는 타입」의 네임스페이스를 연관시킨다.**
- ②③은 **같은 모양**이다 — `was not declared in this scope` + ``did you mean `lib::X`?`` +\
  ``note: `lib::X` declared here``.
- ★ **g++ 의 제안은 한정 이름**이다(`lib::reset` · `lib::touch`). 「서랍을 밝혀라」를 컴파일러가 말해 준다.
- clang 도 같은 셋을 같은 순서로 말한다.

```text
===== 소스: ns02.cpp =====
// ADL 이 도는 자리와 안 도는 자리
namespace lib {
    struct Widget { int v; };
    void reset() {}
    void touch(const Widget&) {}
}

int main() {
    lib::Widget w{1};
    touch(&w);           // ① 포인터를 넘기면 — ADL 은 도는가?
    reset();             // ② 인자가 없다 — 연관 네임스페이스가 없다
    int i = 0;
    touch(i);            // ③ 인자 타입이 무관하다
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ns02.cpp -o ex 2>&1 | grep -E 'error:|note:|generated' (cc exit=1) =====
ns02.cpp:10:5: error: no matching function for call to 'touch'
ns02.cpp:5:10: note: candidate function not viable: no known conversion from 'lib::Widget *' to 'const Widget' for 1st argument; remove &
ns02.cpp:11:5: error: use of undeclared identifier 'reset'; did you mean 'lib::reset'?
ns02.cpp:4:10: note: 'lib::reset' declared here
ns02.cpp:13:5: error: use of undeclared identifier 'touch'; did you mean 'lib::touch'?
ns02.cpp:5:10: note: 'lib::touch' declared here
ns02.cpp:13:11: error: reference to type 'const Widget' could not bind to an lvalue of type 'int'
ns02.cpp:5:29: note: passing argument to parameter here
4 errors generated.
```

### 3. ★★ 둘 다 불린다 — 그리고 `poke` 는 `lib` 의 멤버가 아니다

**출력**

```text
===== 소스: ns03.cpp =====
// 숨은 friend 와 템플릿 인자의 연관
#include <cstdio>
#include <vector>

namespace lib {
    struct Box {
        int v;
        friend void poke(const Box& b) { std::printf("숨은 friend poke v=%d\n", b.v); }
    };
    void tag(const std::vector<Box>&) { std::printf("lib::tag — 원소 타입으로 lib 가 연관됐다\n"); }
}

int main() {
    lib::Box b{5};
    poke(b);                        // ① 숨은 friend — ADL 로만 찾아진다
    std::vector<lib::Box> vs{b};
    tag(vs);                        // ② std::vector<lib::Box> 의 연관 네임스페이스에 lib 가 있다
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ns03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
숨은 friend poke v=5
lib::tag — 원소 타입으로 lib 가 연관됐다
```

**왜 그런가**

- **`poke(b)`** — `poke` 는 `lib::Box` **안에 정의한 `friend`** 다. 이것이 **숨은 `friend`** 이고,\
  **`lib` 의 멤버가 아니다.** 오직 **ADL 로만** 찾아진다.
- **`tag(vs)`** — `vs` 의 타입은 `std::vector<lib::Box>` 다.\
  ★ **템플릿 인자의 네임스페이스도 연관**되므로 연관 집합이 **`std` 와 `lib` 둘**이고, `lib::tag` 가 찾아진다.

다른 방법으로 부르려 하면 둘 다 막힌다.

```text
===== 소스: ns04.cpp =====
// 숨은 friend 를 다른 방법으로 부르려 하면
#include <vector>

namespace lib {
    struct Box { int v; friend void poke(const Box&) {} };
}

int main() {
    lib::Box b{5};
    (poke)(b);        // ① 괄호를 씌우면 ADL 이 꺼진다
    lib::poke(b);     // ② 한정 이름으로는 찾아지나
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ns04.cpp -o ex (cc exit=1) =====
ns04.cpp: In function ‘int main()’:
ns04.cpp:10:6: error: ‘poke’ was not declared in this scope
   10 |     (poke)(b);        // ① 괄호를 씌우면 ADL 이 꺼진다
      |      ^~~~
ns04.cpp:11:10: error: ‘poke’ is not a member of ‘lib’
   11 |     lib::poke(b);     // ② 한정 이름으로는 찾아지나
      |          ^~~~
```

| 쓴 것 | 결과 | 뜻 |
|---|---|---|
| `(poke)(b)` | ``error: `poke` was not declared in this scope`` | ★ **괄호가 ADL 을 껐다** |
| `lib::poke(b)` | ★ ``error: `poke` is not a member of `lib` `` | ★ **정말로 멤버가 아니다** |

- ★★★ **이 둘이 숨은 `friend` 의 정의를 그대로 보여 준다.**\
  이름이 **그 타입을 쓸 때만** 보이므로 ① 오버로드 후보 집합이 안 부풀고 ② `using namespace` 로도 안 새어 나간다.\
  「연산자를 어디에 두나」의 설계 쪽 정본은 [목록의 **22번 주제**](../22-operator-overloading/)다.

### 4. ★★★ `good` 쪽만 `lib::swap` 을 부른다

**출력**

```text
===== 소스: ns05.cpp =====
// swap 2단계 관용구 — using std::swap 이 무엇을 바꾸나
#include <cstdio>
#include <utility>

namespace lib {
    struct Box { int v; };
    void swap(Box& a, Box& b) { std::printf("  lib::swap 이 불렸다\n"); std::swap(a.v, b.v); }
}

template <class T> void bad (T& a, T& b) { std::swap(a, b); }
template <class T> void good(T& a, T& b) { using std::swap; swap(a, b); }

int main() {
    lib::Box p{1}, q{2};
    std::printf("bad(p, q):\n");  bad(p, q);
    std::printf("  p=%d q=%d\n", p.v, q.v);
    std::printf("good(p, q):\n"); good(p, q);
    std::printf("  p=%d q=%d\n", p.v, q.v);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ns05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
bad(p, q):
  p=2 q=1
good(p, q):
  lib::swap 이 불렸다
  p=1 q=2
```

**왜 그런가**

| 쓴 것 | 불린 것 | 출력 뒤의 값 |
|---|---|---|
| `bad(p, q)` — `std::swap(a, b)` | **`std::swap`**(아무 말 없이) | `p=2 q=1` |
| `good(p, q)` — `using std::swap; swap(a, b);` | ★ **`lib::swap`** | `p=1 q=2`(다시 뒤집혀 원래대로) |

- ★★★ `using std::swap;` 이 바꾸는 것은 「**기본값을 후보에 넣는 것**」이다.\
  그러고 나서 **한정 없이** 부르면 ADL 후보(`lib::swap`)와 **같은 자리에서 경쟁**한다.\
  사용자 타입이 있으면 그쪽이 이기고, 없으면 `std::swap` 으로 떨어진다. **둘 다 되는 코드**가 된다.
- ★★★ **`std::swap(a, b)` 로 적으면 안 되는 이유** — **한정 이름이 ADL 을 끈다.**\
  `lib::swap` 은 **후보도 되지 못한다.** 출력에서 `bad` 가 **아무 말 없이 값만 바꾼** 것이 그 결과다.
- ★★ **그래서 이 사고는 「틀린 답」이 아니라 「잘 도는데 맞춤 구현을 안 쓰는 코드」로 남는다.**\
  경고도 에러도 없다.
- ★ 같은 모양이 `begin`/`end`/`size` 에도 있고, **C++20 은 `std::ranges::swap` 으로 그 2단계를 대신해 준다**(9번).

### 5. ★★★ 첫 줄은 `lib::handle`, 둘째 줄은 `::handle` — 경고 0건

**출력**

```text
===== 소스: ns06.cpp =====
// ADL 이 조용히 이기는 자리 — 에러도 경고도 없다
#include <cstdio>

namespace lib {
    struct W { int v; };
    void handle(W&) { std::printf("lib::handle(W&)\n"); }
}
void handle(const lib::W&) { std::printf("::handle(const W&)\n"); }

int main() {
    lib::W w{1};
    handle(w);              // 비const lvalue — 어느 쪽이 이기나
    const lib::W cw{2};
    handle(cw);             // const lvalue — 이쪽은?
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ns06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
lib::handle(W&)
::handle(const W&)
```

```text
===== 소스: ns06.cpp =====
// ADL 이 조용히 이기는 자리 — 에러도 경고도 없다
#include <cstdio>

namespace lib {
    struct W { int v; };
    void handle(W&) { std::printf("lib::handle(W&)\n"); }
}
void handle(const lib::W&) { std::printf("::handle(const W&)\n"); }

int main() {
    lib::W w{1};
    handle(w);              // 비const lvalue — 어느 쪽이 이기나
    const lib::W cw{2};
    handle(cw);             // const lvalue — 이쪽은?
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ns06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
lib::handle(W&)
::handle(const W&)
```

**왜 그런가**

| 호출 | 불린 것 | 왜 |
|---|---|---|
| `handle(w)`(비const lvalue) | ★ **`lib::handle(W&)`** | ADL 후보가 **정확히 맞는다** — `const` 를 덧붙일 필요가 없으니 더 낫다 |
| `handle(cw)`(const lvalue) | **`::handle(const W&)`** | `lib::handle(W&)` 는 **`const` 를 못 받아** 후보에서 탈락 |

- ★★★ **경고는 0건이다.** 컴파일 통과 · 실행 정상 · **부른 함수만 다르다.**\
  「내가 쓴 전역 `handle` 이 불리겠지」라고 믿었으면 **첫 줄에서 이미 틀렸다.**
- ★★ **한 문장으로** — 「**ADL 은 후보를 추가하고, 그 뒤에는 보통의 오버로드 해석이 돈다.\
  그러니 라이브러리 쪽 후보가 더 잘 맞으면 그쪽이 이긴다.**」\
  순위 규칙(정확 일치 → 승격 → 변환)의 정본은 형제 [`01번`](../01-function-overloading-and-overload-resolution/)이다.
- ★★ **컴파일러가 잡아 줄 수 없다.** 둘 다 **합법인 호출**이고 모호하지도 않다 —\
  모호했다면 오히려 에러가 나서 알았을 것이다. **더 잘 맞아서 이긴 것**이라 진단할 거리가 없다.
- ★ 막는 방법은 **한정 이름으로 적는 것**(`::handle(w)`)뿐이다.\
  ★★ 그런데 4번과 **정반대 조언**이다 — 그래서 판단 기준은 「한정이 좋다/나쁘다」가 아니라\
  「**이 자리에서 맞춤 구현이 불려야 하나**」다.

### 6. ★ 심볼 **여섯** — `api::latest()` 는 `api::v2::latest()` 로 남는다

**출력**

```text
===== 소스: ns09.cpp =====
// 네임스페이스가 심볼에 어떻게 남나
namespace app { void exported() {} }
namespace { void internal() {} }
static void file_static() {}

namespace api {
    inline namespace v2 { void latest() {} }
    namespace v1        { void latest() {} }
}

void use() { internal(); file_static(); api::latest(); api::v1::latest(); }
===== g++ -std=c++20 -Wall -Wextra -pedantic -c ns09.cpp -o ns09.o && nm -C ns09.o | sort -k3 (exit=0) =====
000000000000000b t (anonymous namespace)::internal()
000000000000002c T api::v1::latest()
0000000000000021 T api::v2::latest()
0000000000000000 T app::exported()
0000000000000016 t file_static()
0000000000000037 T use()
```

```text
===== 소스: ns09.cpp =====
// 네임스페이스가 심볼에 어떻게 남나
namespace app { void exported() {} }
namespace { void internal() {} }
static void file_static() {}

namespace api {
    inline namespace v2 { void latest() {} }
    namespace v1        { void latest() {} }
}

void use() { internal(); file_static(); api::latest(); api::v1::latest(); }
===== nm ns09.o | sort -k3 (exit=0) =====
0000000000000037 T _Z3usev
0000000000000016 t _ZL11file_staticv
000000000000000b t _ZN12_GLOBAL__N_18internalEv
000000000000002c T _ZN3api2v16latestEv
0000000000000021 T _ZN3api2v26latestEv
0000000000000000 T _ZN3app8exportedEv
```

**왜 그런가**

| 심볼 | 표시 | 뜻 |
|---|---|---|
| `app::exported()` | **`T`** | **전역 링크** — 다른 번역 단위에서 보인다 |
| `(anonymous namespace)::internal()` | ★ **`t`** | ★ **내부 링크** |
| `file_static()` | ★ **`t`** | ★ **익명 네임스페이스와 같은 표시** |
| `api::v1::latest()` | `T` | 한정 이름 그대로 |
| `api::v2::latest()` | `T` | ★ **`api::latest()` 라고 불렀는데 `v2` 가 붙어 있다** |
| `use()` | `T` | — |

- ★★★ **`inline namespace` 는 이름만 투명하다.** 소스에서는 `api::latest()` 로 부르는데\
  오브젝트 파일에는 **`api::v2::latest()`**(맹글링 `_ZN3api2v26latestEv`)로 남는다.\
  그래서 **`inline` 을 `v2` 에서 `v3` 로 옮기면 ABI 가 갈린다** — 옛 바이너리는 `v2` 심볼을 계속 찾는다.
- ★★ **익명 네임스페이스와 `static` 은 링크 측면에서 같다**(둘 다 `t`).\
  맹글링만 다르다 — `_ZN12_GLOBAL__N_18internalEv` 대 `_ZL11file_staticv`.\
  ★ **C++ 에서는 익명 네임스페이스를 쓴다** — `static` 과 달리 **타입·템플릿에도 쓸 수 있기 때문**이다.
- ★ **주소 칸은 흔들리는 칸**이다. 근거로 쓰는 것은 **이름**과 **`T`/`t`** 다.

### 7. 모호 — 그리고 `using` 없이도 전역은 더러워진다

**출력**

```text
===== 소스: ns07.cpp =====
// using namespace std 가 만드는 모호 호출
#include <algorithm>
using namespace std;

template <class T> T max(T a, T b) { return a < b ? b : a; }

int main() { return max(1, 2); }
===== g++ -std=c++20 -Wall -Wextra -pedantic ns07.cpp -o ex 2>&1 | grep -vE '^( *from |In file included from )' (cc exit=1) =====
ns07.cpp: In function ‘int main()’:
ns07.cpp:7:24: error: call of overloaded ‘max(int, int)’ is ambiguous
    7 | int main() { return max(1, 2); }
      |                     ~~~^~~~~~
ns07.cpp:5:22: note: candidate: ‘T max(T, T) [with T = int]’
    5 | template <class T> T max(T a, T b) { return a < b ? b : a; }
      |                      ^~~
/usr/include/c++/13/bits/stl_algobase.h:257:5: note: candidate: ‘constexpr const _Tp& std::max(const _Tp&, const _Tp&) [with _Tp = int]’
  257 |     max(const _Tp& __a, const _Tp& __b)
      |     ^~~
```

**왜 그런가**

- ``error: call of overloaded `max(int, int)` is ambiguous`` — 후보 **둘**이다.\
  ① 내가 쓴 ``T max(T, T) [with T = int]`` · ② ``constexpr const _Tp& std::max(const _Tp&, const _Tp&) [with _Tp = int]``.
- ★★ **헤더에서 내면 더 나쁜 이유** — 그 헤더를 `#include` 한 **모든 번역 단위**가 같은 사고를 물려받고,\
  **사고가 난 파일에는 `using namespace std;` 라는 줄이 안 보인다.** 원인을 찾으러 헤더를 뒤져야 한다.\
  ★ 게다가 표준 라이브러리는 **판마다 이름이 늘어난다** — 오늘 안 부딪힌다고 내일 안 부딪히는 것이 아니다.

★★ **마지막 물음의 답 — `using namespace std;` 탓이 아니다.**

```text
===== 소스: ns08.cpp =====
// 헤더가 전역에 쏟아 놓는 이름 — using namespace 는 관계가 없다
#include <cmath>

double y1 = 1.0;

int main() { return static_cast<int>(y1); }
===== g++ -std=c++20 -Wall -Wextra -pedantic ns08.cpp -o ex 2>&1 | grep -vE '^( *from |In file included from )' (cc exit=1) =====
ns08.cpp:4:8: error: ‘double y1’ redeclared as different kind of entity
    4 | double y1 = 1.0;
      |        ^~
/usr/include/x86_64-linux-gnu/bits/mathcalls.h:224:1: note: previous declaration ‘double y1(double)’
  224 | __MATHCALL (y1,, (_Mdouble_));
      | ^~~~~~~~~~
ns08.cpp: In function ‘int main()’:
ns08.cpp:6:21: error: invalid ‘static_cast’ from type ‘double(double) noexcept’ to type ‘int’
    6 | int main() { return static_cast<int>(y1); }
      |                     ^~~~~~~~~~~~~~~~~~~~
```

- ★★★ **이 파일에는 `using` 이 한 줄도 없다.** 그런데도 ``error: `double y1` redeclared as different kind of entity`` 다.\
  **`<cmath>` 가 전역에 `y1`(POSIX 베셀 함수)을 선언해 놓기 때문**이다.
- ★★ 그러니 **두 가지를 갈라야 한다** —\
  ① **`using namespace` 가 서랍을 쏟는 것** — 내가 만든 문제, 안 쓰면 된다.\
  ② **C 호환 헤더가 애초에 전역에 이름을 쏟아 두는 것** — 내가 못 막는다.\
  ②의 처방은 **내 이름을 네임스페이스에 넣는 것**뿐이다.

### 8. `int render = 0;` 이 ADL 을 껐다

**출력**

```text
===== 소스: ns11.cpp =====
// ADL 을 끄는 것 — 블록 스코프의 「함수가 아닌」 선언
#include <cstdio>

namespace lib {
    struct W { int v; };
    void render(const W&) { std::printf("lib::render\n"); }
}

void off_case() {
    int render = 0;        // 블록 스코프의 변수 선언
    lib::W w{1};
    render(w);             // 이 자리에서 ADL 은 꺼진다
    (void)render;
}

int main() { off_case(); }
===== g++ -std=c++20 -Wall -Wextra -pedantic ns11.cpp -o ex (cc exit=1) =====
ns11.cpp: In function ‘void off_case()’:
ns11.cpp:12:11: error: ‘render’ cannot be used as a function
   12 |     render(w);             // 이 자리에서 ADL 은 꺼진다
      |     ~~~~~~^~~
```

```text
===== 소스: ns11.cpp =====
// ADL 을 끄는 것 — 블록 스코프의 「함수가 아닌」 선언
#include <cstdio>

namespace lib {
    struct W { int v; };
    void render(const W&) { std::printf("lib::render\n"); }
}

void off_case() {
    int render = 0;        // 블록 스코프의 변수 선언
    lib::W w{1};
    render(w);             // 이 자리에서 ADL 은 꺼진다
    (void)render;
}

int main() { off_case(); }
===== clang++ -std=c++20 -Wall -Wextra -pedantic ns11.cpp -o ex 2>&1 | grep -E 'error:|note:|generated' (cc exit=1) =====
ns11.cpp:12:11: error: called object type 'int' is not a function or function pointer
1 error generated.
```

**왜 그런가**

- ``error: `render` cannot be used as a function`` — **블록 스코프의 `int render`** 가 먼저 찾히면서\
  **ADL 이 아예 안 돌았다.** 그래서 `lib::render` 는 후보가 되지 못했다.
- ★★ **규칙** — 한정 없는 이름의 보통 탐색이 **클래스 멤버**나 **블록 스코프의 「함수가 아닌」 선언**을 찾으면\
  **ADL 이 꺼진다.**\
  ★ 블록 스코프의 **함수 선언**은 끄지 **않는다** — **이 문서는 비함수 판만 던졌다.**
- ★ **괄호를 씌우는 것**(`(f)(x)`)도 ADL 을 끈다(3번). 그쪽은 **일부러 끄는 문법적 방법**이다.
- ★★ **일부러 끌 때 쓰는 정석은 한정 이름**이다 — `lib::f(x)` 나 `::f(x)`.\
  괄호 방법은 **의도가 코드에 안 적히므로** 읽는 사람이 오해한다.

### 9. 별칭 · `using` 선언 · 블록 안 `using` 지시 · 한정 이름

**출력**

```text
===== 소스: ns10.cpp =====
// 이름을 좁게 들여오는 네 가지 형태
#include <cstdio>

namespace outer {
    namespace inner { void ping() { std::printf("outer::inner::ping\n"); } }
    int level = 1;
}
namespace oi = outer::inner;          // ① 네임스페이스 별칭

using outer::level;                   // ② using 선언 — 이름 하나만

int main() {
    oi::ping();                       // ① 로 부른다
    std::printf("level = %d\n", level);
    {
        using namespace outer::inner; // ③ using 지시 — 블록 안으로 한정
        ping();
    }
    outer::inner::ping();             // ④ 한정 이름 — 언제나 확실하다
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ns10.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
outer::inner::ping
level = 1
outer::inner::ping
outer::inner::ping
```

**왜 그런가**

| 형태 | 예 | 성격 |
|---|---|---|
| ① **네임스페이스 별칭** | `namespace oi = outer::inner;` | 이름을 **줄이기만** 한다 |
| ② **`using` 선언** | `using outer::level;` | ★ **이름 하나**만 들여온다 |
| ③ **블록 안 `using` 지시** | `{ using namespace outer::inner; ping(); }` | ★ **그 블록에서만** 산다 |
| ④ **한정 이름** | `outer::inner::ping();` | 언제나 확실하다 |

- ★★ **②와 `using namespace outer;` 의 차이** — ②는 **`level` 하나**만 보이게 하고,\
  뒤엣것은 **`outer` 안의 모든 이름**을 보이게 한다. 충돌 면적이 다르다.
- ★★ **③이 헤더의 `using namespace` 보다 안전한 이유** — **범위가 닫힌다.**\
  `#include` 한 남의 파일까지 따라가지 않으므로 7번 같은 사고가 **그 블록 밖으로 안 나간다.**
- ★★★ **④가 언제나 옳은 것은 아니다 — 4번과 충돌한다.**\
  **한정 이름은 ADL 을 끄므로** 맞춤 구현이 불려야 하는 자리에서는 **틀린 답**이 된다.\
  판단 기준은 「한정이 좋다」가 아니라 「**이 자리에서 맞춤 구현이 불려야 하나**」다.

C++20 은 그 2단계를 **객체 안으로 넣어** 준다.

```text
===== 소스: ns12.cpp =====
// C++20 의 사용자 지정 지점 객체 — 2단계를 안에서 해 준다
#include <cstdio>
#include <concepts>

namespace lib {
    struct Box { int v; };
    void swap(Box& a, Box& b) { std::printf("  lib::swap 이 불렸다\n"); int t = a.v; a.v = b.v; b.v = t; }
}

int main() {
    lib::Box p{1}, q{2};
    std::printf("std::ranges::swap(p, q):\n");
    std::ranges::swap(p, q);
    std::printf("  p=%d q=%d\n", p.v, q.v);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ns12.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
std::ranges::swap(p, q):
  lib::swap 이 불렸다
  p=2 q=1
```

- ★ **`std::ranges::swap`** 은 **사용자 지정 지점 객체(CPO)** 다 — **한정 이름으로 적었는데도**\
  안에서 ADL 2단계를 해 주어 **`lib::swap` 이 불렸다.**\
  「한정 이름이면 맞춤 구현을 못 쓴다」의 **예외를 표준이 만들어 준 것**이고, 정본은 목록의 **45번 주제**다.

### 10. 이 주제의 지도

**왜 그런가**

- **후보 집합 위에서 하나를 고르는 규칙**(정확 일치 → 승격 → 변환 → 모호)의 정본은 형제\
  [**01번**](../01-function-overloading-and-overload-resolution/)이다.\
  ★ 이 주제는 **그 앞 단계**(후보가 어떻게 모이나)이고, 5번의 결과는 **거기 규칙이 낸 것**이다.
- **숨은 `friend` 가 인터페이스 설계에서 갖는 뜻**은 [목록의 **22번 주제**](../22-operator-overloading/)(연산자 오버로딩)와 이어진다 —\
  「멤버냐 비멤버냐」를 **클래스 안의 `friend`** 로 푸는 배치다.\
  `friend` 의 **접근 제어** 쪽은 [목록의 **12번 주제**](../12-class-basics-members-access-and-this/)다.
- **`swap` 2단계를 C++20 이 대체한 것**은 **사용자 지정 지점 객체**(`std::ranges::swap`)이고,\
  정본은 목록의 **45번 주제**(범위와 뷰)다. **이 문서에서 실제로 던져 확인했다**(9번).
- **익명 네임스페이스가 대신하는 C 의 장치**는 파일 스코프 `static` 이다 —\
  정본은 C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **30번**(`static`/`extern` 과 링크)이고 **아직 폴더가 없다.**
- 「**이름이 어느 번역 단위에 사는가**」의 정본은 목록의 **55번 주제**(모듈·ODR·헤더 배치)다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 명령으로 돌렸나 |
|---|---|---|
| `ns01.cpp` ADL 기본 | `lib::touch v=7` · `lib::reset` | g++ |
| `ns02.cpp` 안 도는 자리 | **에러 3** · ★ ①은 「찾았는데 안 맞는다」 | g++ · clang |
| `ns03.cpp` 숨은 friend·템플릿 인자 | `숨은 friend poke v=5` · `lib::tag` | g++ |
| `ns04.cpp` 다른 방법으로 부르기 | **에러 2** — ``not declared in this scope`` · ★ ``is not a member of `lib` `` | g++ |
| `ns05.cpp` swap 2단계 | ★ `bad` 는 **조용히** `std::swap` · `good` 은 **`lib::swap`** | g++ |
| `ns06.cpp` 조용히 이기는 자리 | ★★ `lib::handle(W&)` / `::handle(const W&)` · **경고 0건** | g++ · clang |
| `ns07.cpp` `using namespace std` | **에러 1 · 후보 2**(내 `max` 와 `std::max`) | g++ |
| `ns08.cpp` 전역 오염 | ★ **`using` 없이도 에러** — `<cmath>` 의 `y1` | g++ |
| `ns09.cpp` 심볼 | ★ **`T` 4개 · `t` 2개** · `api::latest()` → **`api::v2::latest()`** | g++ `-c` + `nm -C` · `nm` |
| `ns10.cpp` 네 형태 | 전부 `outer::inner::ping` 이 불린다 · `level = 1` | g++ |
| `ns11.cpp` ADL 끄기 | ``error: `render` cannot be used as a function`` | g++ · clang |
| `ns12.cpp` CPO | ★ `std::ranges::swap` 이 **`lib::swap`** 을 부른다 | g++ `-std=c++20` |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · binutils 2.42 · glibc)에서만** 그렇다.

- ★ **맹글링 문자열**(`_ZN3api2v26latestEv` · `_ZN12_GLOBAL__N_18internalEv` · `_ZL11file_staticv`) —\
  **플랫폼 ABI**(Itanium C++ ABI)가 정한다. 언어 보장이 아니다.
- ★ **`<cmath>` 가 전역에 `y1` 을 선언하는 것** — POSIX + 이 구현이다.\
  C++ 표준은 `<cmath>` 의 이름이 `std` 에 있다고만 한다.
- 진단 문구 전부 · g++ 의 `did you mean` 제안 · `std::max` 가 있는 **헤더 파일과 줄 번호**(판마다 움직인다).
- 심볼 **주소**(`0000000000000021` 등) — 흔들리는 칸이다.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **ADL 이 후보를 「추가」하는** 것과 **연관 네임스페이스의 목록**(클래스·포인터/참조·템플릿 인자·기반 클래스·열거형).
- **숨은 `friend` 가 그 네임스페이스의 멤버가 아니고 ADL 로만 찾아지는** 것.
- **한정 이름·괄호·블록 스코프의 비함수 선언이 ADL 을 끄는** 것.
- **익명 네임스페이스가 내부 링크**인 것 · `inline namespace` 가 **이름만 투명한** 것.
- `using` 선언(이름 하나)과 `using` 지시(전부)의 차이 · 블록 안 `using` 지시의 **범위가 닫히는** 것.
- ★ **언제부터인가도 언어가 보장한다** — `inline namespace` 는 **C++11부터**,
  `std::ranges::swap` 은 **C++20부터**.

**미정의 동작**

- ★ **이 주제에는 없다.** 이 문서의 프로그램은 전부 정의된 동작만 한다.\
  위험은 UB 가 아니라 「**진단이 안 나는 쪽**」(4번·5번)에 있다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **기반 클래스가 만드는 연관**(파생 타입을 넘기면 기반의 서랍도 열린다) ·
  **열거형이 만드는 연관**(형제 [`02번`](../02-enum-class-and-scoped-enumerations/)과 이어진다) ·
  **블록 스코프의 「함수」 선언**이 ADL 을 끄지 **않는** 것(8번은 비함수 판만 던졌다) ·
  **`using` 선언으로 여러 네임스페이스의 같은 이름을 합쳤을 때의 오버로드**(정본이 형제 [`01번`](../01-function-overloading-and-overload-resolution/)이다) ·
  **모듈(C++20)에서의 이름 탐색**(g++ 13 의 모듈 지원이 제한적이다 — 목록의 **55번 주제**) ·
  `__attribute__((abi_tag))` 로 ABI 를 가르는 실무 관용구.
- **못 잰 것** — 없다. 이 주제의 결론은 전부 **실행 출력·진단·심볼**로 잡힌다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★ **`std::max` 가 사는 헤더와 줄 번호**(7번 진단에 박혀 있다) — libstdc++ 가 바뀌면 움직인다.
- ★ **`<cmath>` 가 전역에 쏟는 이름**(지금은 `y1` 로 확인했다).
- 맹글링 문자열과 `nm` 출력 형식.
- 진단 문구와 `did you mean` 제안.
