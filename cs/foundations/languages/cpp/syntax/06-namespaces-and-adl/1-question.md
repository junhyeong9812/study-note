# cpp/syntax/06 — 네임스페이스와 ADL — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 한정 없이 적은 이름이 **어디서 찾아지는지**,
> 그리고 **누가 뽑히는지**를 맞힐 수 있는지 묻는다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · x86-64 Linux · `nm`(GNU Binutils 2.42).
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 사고는 「에러」가 아니라 「조용히 다른 것이 불리는 것」이다.** 5번이 그 자리다 —
> 경고 0건 · 실행 정상 · **부른 함수만 다르다.**
> ★ **네 번째 창은 오브젝트 파일의 심볼**이다(`nm -C`). 네임스페이스가 **파일에 글자로** 남는다(6번).
> 선행 — 없음. 형제 [`01번`](../01-function-overloading-and-overload-resolution/)(오버로드 해석)이 **후보를 줄 세우는 규칙**을 갖고 있고,
> 여기는 **그 후보 집합이 어떻게 만들어지나**다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 한정 없이 적은 이름이 찾아지나 (예측)

```cpp
/* ns01.cpp */
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
```

- 컴파일되는가? 출력은?
- `touch(w)` 는 `lib::` 를 안 붙였는데 어떻게 찾아졌는가 — 그 장치의 이름은?
- `reset()` 은 왜 `lib::` 를 붙여야 하는가?
- 이 장치가 **없었다면** 어떤 코드가 불편해지는가?

### 2. ★★ 안 도는 자리 셋 (예측)

```cpp
/* ns02.cpp */
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
```

- 에러가 **몇 개** 나는가?
- ①의 에러는 「못 찾았다」인가 「찾았는데 안 맞는다」인가 — 그 차이가 무엇을 증명하는가?
- ②와 ③의 에러 문구가 **같은 모양**인가?
- g++ 가 덧붙여 주는 **제안**은 무엇인가?

### 3. ★★ 숨은 `friend` 와 템플릿 인자 (예측)

```cpp
/* ns03.cpp */
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
```

- 컴파일되는가? 출력은?
- `poke` 는 `lib` 의 **멤버인가**?
- `std::vector<lib::Box>` 를 넘겼는데 `lib::tag` 가 찾아지는 이유는?
- 같은 `poke` 를 `(poke)(b)` 와 `lib::poke(b)` 로 부르면 각각 어떻게 되는가?

### 4. ★★★ `swap` 2단계 관용구 (예측)

```cpp
/* ns05.cpp */
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
```

- `bad(p, q)` 와 `good(p, q)` 중 **`lib::swap` 이 불리는** 쪽은?
- 두 호출 뒤 `p`·`q` 의 값이 각각 무엇인가?
- `using std::swap;` 이 **정확히 무엇을 바꾸는가**?
- `std::swap(a, b)` 로 적으면 왜 안 되는가?

### 5. ★★★ 조용히 이기는 자리 (예측)

```cpp
/* ns06.cpp */
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
```

- 두 줄이 각각 **어느 함수**를 부르는가?
- 경고는 **몇 건**인가?
- 갈리는 이유를 **한 문장**으로 대면?
- 이 사고를 **컴파일러가 잡아 줄 수 있는가**?

### 6. ★ 오브젝트 파일이 네임스페이스에 대해 말해 주는 것 (예측)

```cpp
/* ns09.cpp */
// 네임스페이스가 심볼에 어떻게 남나
namespace app { void exported() {} }
namespace { void internal() {} }
static void file_static() {}

namespace api {
    inline namespace v2 { void latest() {} }
    namespace v1        { void latest() {} }
}

void use() { internal(); file_static(); api::latest(); api::v1::latest(); }
```

- `nm -C` 를 걸면 심볼이 **몇 개** 나오는가?
- `app::exported()` 와 `(anonymous namespace)::internal()` 의 **대문자/소문자 표시**가 무엇이 다른가?
- `api::latest()` 를 불렀는데 심볼은 **무엇으로** 남는가?
- `static void file_static()` 과 익명 네임스페이스는 심볼 수준에서 **같은가 다른가**?

### 7. `using namespace std;` 가 무는 자리 (경계)

```cpp
/* ns07.cpp */
// using namespace std 가 만드는 모호 호출
#include <algorithm>
using namespace std;

template <class T> T max(T a, T b) { return a < b ? b : a; }

int main() { return max(1, 2); }
```

- 이 파일이 컴파일되는가 — 에러 문구는?
- 후보로 제시되는 **둘**이 각각 무엇인가?
- 같은 사고를 **헤더**에서 내면 무엇이 더 나빠지는가?
- `#include <cmath>` 만 하고 전역에 `double y1 = 1.0;` 을 두면 어떻게 되는가 —\
  그것도 `using namespace std;` 탓인가?

### 8. ADL 을 끄는 것 (경계)

```cpp
/* ns11.cpp */
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
```

- 이 코드가 컴파일되는가 — 에러 문구는?
- **무엇이** ADL 을 껐는가?
- 괄호를 씌우는 것(`(f)(x)`)과 같은 효과인가?
- ADL 을 **일부러 끄고 싶을 때** 무엇을 쓰는가?

### 9. 이름을 좁게 들여오는 네 형태 (왜)

```cpp
/* ns10.cpp */
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
```

- 네 형태의 이름을 각각 댈 수 있는가?
- `using outer::level;` 과 `using namespace outer;` 는 무엇이 다른가?
- 블록 안의 `using namespace` 가 헤더의 그것보다 안전한 이유는?
- 「한정 이름으로 적는다」가 **언제나 옳은가** — 4번과 충돌하지 않는가?

### 10. 다른 주제와 잇기 (연결)

- ADL 이 만드는 **후보 집합** 위에서 실제로 하나를 고르는 규칙의 정본은 형제 몇 번인가?
- 「숨은 `friend`」가 인터페이스 설계에서 갖는 뜻은 목록의 몇 번 주제와 이어지나?
- `swap` 2단계와 같은 모양의 관용구가 C++20 에서 무엇으로 대체됐나 — 목록의 몇 번인가?
- 익명 네임스페이스가 대신하는 C 의 장치는 **어느 갈래 어느 주제**인가?
- 「이름이 어느 번역 단위에 사는가」의 정본은 목록의 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
