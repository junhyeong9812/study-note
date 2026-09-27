# cpp/syntax/18 — 0/3/5의 법칙 · `=default`/`=delete` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이므로 **출력을 싣는 블록마다 그 출력을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **ASan 의 PID·주소**와 **진단 문구**다.\
> 근거로 쓰는 것은 다음이다 — **트레이트 격자의 0/1** · **어느 특수 멤버가 불렸나** ·\
> **`new`/`delete` 횟수** · **`cc exit`/`run exit`** · **경고·에러 개수** · **`sizeof`**.
> ★★★ **이 문서는 시간을 재지 않았다.** 「0의 법칙이 빠르다」는 문장이 **한 줄도 없다** —\
> 이 문서가 센 것은 **트레이트의 0/1 과 할당 횟수까지**다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `S1` 은 `S0` 와 **한 칸도 안 다르다** — 그것이 이 편의 함정이다

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic rule01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
타입 | 기본 복사생 복사대 이동생 이동대 | 이동이 noexcept 인가
S0  |  1   1   1   1   1  |   1
S1  |  1   1   1   1   1  |   1
S2  |  0   1   1   1   1  |   1
S3  |  0   0   0   1   0  |   1
S4  |  1   1   1   1   1  |   1
S5  |  0   0   1   0   1  |   0
S6  |  1   0   0   1   1  |   1
S7  |  1   1   1   1   1  |   1
S8  |  1   1   1   1   1  |   0
```

**왜 그런가**

| 타입 | 적은 것 | 격자가 말하는 것 |
|---|---|---|
| `S0` | 아무것도 | 여섯 다 `1` — 기준선 |
| `S1` | 소멸자만 `{}` | ★★★ **여섯 칸이 `S0` 와 똑같다** — `noexcept` 칸까지 `1` |
| `S2` | 복사 생성자만 | ★★ **기본 생성 `0`** — 복사 생성자를 선언하면 기본 생성자가 안 만들어진다 |
| `S3` | 이동 생성자만 | ★★★ **복사 생성 `0` · 복사 대입 `0` · 이동 대입 `0`** |
| `S4` | 여섯을 `= default` | `S0` 와 같다 |
| `S5` | 복사 생성자 `= delete` | ★★ **복사 생성 `0` 인데 복사 대입은 `1`** |
| `S6` | `unique_ptr`+`vector` | ★★★ **복사 `0` · 이동 `1` · `noexcept` `1`** |
| `S7` | `string` 하나 | 전부 `1` |
| `S8` | `string` + 소멸자 `{}` | ★★★ **마지막 칸만 `1` → `0`** |

- ★★★ **`S1` 이 `S0` 와 한 칸도 안 다르다.** 멤버가 `int` 라서 **복사와 이동이 같은 일**이기 때문이다.\
  ★ 그래서 「**격자만 보면 아무 문제가 없어 보인다**」. 이 편의 함정이 여기 있다.\
  ★ **`S8` 은 멤버가 `string` 이라 갈린다** — `noexcept` 칸이 `1` 에서 `0` 으로 떨어졌다.
- ★★★ **`S3` 의 복사가 `0` 인 이유** — **이동 생성자를 선언하면 복사 둘이 `= delete` 된다.**\
  「안 만들어진다」가 아니라 「**지워진다**」이고, 그 차이는 4번에서 본다.
- ★★ **`S5` 의 비대칭** — 복사 생성자만 지웠는데 **복사 대입이 `1` 로 남아 있다.**\
  ★ **둘을 다 지워야** 복사가 막힌다.
- ★★ **`S6` 이 0의 법칙의 격자다** — 한 줄도 안 썼는데 **복사는 막히고 이동은 열려 있다.**\
  `unique_ptr` 이 복사 불가라서 **멤버가 그 성질을 타입에 그대로 물려준** 것이다.
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic rule01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
타입 | 기본 복사생 복사대 이동생 이동대 | 이동이 noexcept 인가
S0  |  1   1   1   1   1  |   1
S1  |  1   1   1   1   1  |   1
S2  |  0   1   1   1   1  |   1
S3  |  0   0   0   1   0  |   1
S4  |  1   1   1   1   1  |   1
S5  |  0   0   1   0   1  |   0
S6  |  1   0   0   1   1  |   1
S7  |  1   1   1   1   1  |   1
S8  |  1   1   1   1   1  |   0
```

### 2. ★★★ **이동이 복사로 바뀐다** — 그런데 `is_move_constructible` 은 **둘 다 1** 이다

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic rule02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) Zero — 아무것도 안 쓴 타입
      멤버: 이동
      멤버: 이동 대입
(2) Dtor — 소멸자 한 줄만 더한 타입
      멤버: 복사
      멤버: 복사 대입
(3) 격자는 무엇이라고 답하나
    is_move_constructible          Zero=1  Dtor=1   ← 둘 다 1이라 안 갈린다
    is_nothrow_move_constructible  Zero=1  Dtor=0   ← 여기서 갈린다
(4) 그래서 vector 재할당이 갈린다
    [Zero] 자리 둘을 잡고 둘을 넣은 뒤 셋째를 넣는다
      멤버: 이동
      멤버: 이동
    [Dtor] 자리 둘을 잡고 둘을 넣은 뒤 셋째를 넣는다
      멤버: 복사
      멤버: 복사
```

**왜 그런가**

- ★★★ **`(1)` 은 `멤버: 이동` · `멤버: 이동 대입`, `(2)` 는 `멤버: 복사` · `멤버: 복사 대입`** 이다.\
  소스 차이는 **`~Dtor() {}` 한 줄**뿐이다.
- ★★★ **사용자가 소멸자를 선언하면 이동 생성자·이동 대입이 아예 안 만들어진다.**\
  그런데 **복사는 남아 있으므로** `std::move(a)` 가 만든 rvalue 가 **`const Tr&` 에 묶여** 복사가 뽑힌다.
- ★★★ **`is_move_constructible` 이 둘 다 `1`** 인 이유가 거기 있다.\
  그 트레이트는 「**rvalue 로부터 생성할 수 있나**」를 묻는다 — **복사 생성자로 할 수 있으면 `1`** 이다.\
  ★ 「이동 생성자가 있나」를 묻는 트레이트가 **아니다.**
- ★★★ **그래서 「이동이 사라졌다」를 보이려면 창을 바꿔야 한다.**
  - **`is_nothrow_move_constructible`** — `1` 대 `0` 으로 **갈린다**(복사 생성자는 `noexcept` 가 아니다).
  - ★★★ **호출 로그** — `(1)`·`(2)` 가 직접 보여 준다. **가장 확실한 창**이다.
- ★★ **`(4)` 가 그 결과를 컨테이너에서 확인한다** — `[Zero]` 는 `멤버: 이동` 두 줄, `[Dtor]` 는 `멤버: 복사` 두 줄이다.\
  ★ [17번](../17-move-constructor-assignment-and-moved-from-state/) **(3)과 같은 자리**다. 거기서는 `noexcept` 한 낱말이 갈랐고, 여기서는 **소멸자 한 줄**이 가른다.
- ★★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic rule02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) Zero — 아무것도 안 쓴 타입
      멤버: 이동
      멤버: 이동 대입
(2) Dtor — 소멸자 한 줄만 더한 타입
      멤버: 복사
      멤버: 복사 대입
(3) 격자는 무엇이라고 답하나
    is_move_constructible          Zero=1  Dtor=1   ← 둘 다 1이라 안 갈린다
    is_nothrow_move_constructible  Zero=1  Dtor=0   ← 여기서 갈린다
(4) 그래서 vector 재할당이 갈린다
    [Zero] 자리 둘을 잡고 둘을 넣은 뒤 셋째를 넣는다
      멤버: 이동
      멤버: 이동
    [Dtor] 자리 둘을 잡고 둘을 넣은 뒤 셋째를 넣는다
      멤버: 복사
      멤버: 복사
```

- ★★★ **이것이 「법칙」이 법칙인 이유다.** 취향이 아니라 **이 출력** 때문이다.

### 3. ★★ `T1`/`T2` 는 **1 대 0** · `T4` 는 **네 칸 다 0** · `T7` 은 **`T4` 와 같아진다**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic rule03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
타입 | t기본 t복사 t소멸 trivial | sizeof
T0  |   1     1     1     1   |  4
T1  |   1     1     1     1   |  4
T2  |   0     1     1     0   |  4
T3  |   1     1     1     1   |  4
T4  |   0     0     0     0   |  4
T5  |   0     1     1     0   |  4
T6  |   0     0     1     0   |  4
T7  |   0     0     0     0   |  4
```

**왜 그런가**

- ★★★ **`= default` 는 「컴파일러가 만들 것을 그대로 쓰겠다」는 선언**이고, `{}` 는 「**내가 쓴 함수**」다.\
  `T1` 의 `trivial` 이 `1`, `T2` 는 `0` 이다.
- ★★★ **`T4`(빈 소멸자 `{}`) 는 네 칸이 전부 `0`** 이다.\
  ★ **`is_trivially_copyable` 까지 떨어진다** — `memcpy` 로 옮겨도 되는지, 컨테이너가 최적화 경로를 탈 수 있는지가 그 값에 달려 있다.
- ★★★ **`T7` 이 함정이다.** `~T7();` 로 선언만 하고 **클래스 밖에서 `= default`** 를 쓰면\
  **`T3` 이 아니라 `T4` 와 똑같은 줄**이 나온다(`0 0 0 0`).\
  ★ **「첫 선언에서 `= default`」라야** trivial 이 유지된다. 클래스 밖은 **사용자 제공(user-provided)으로 친다.**
- ★★ **`T5` 의 `t기본` 이 `0`** 인 것은 다른 이유다 — 복사 생성자를 선언하면 **기본 생성자가 안 만들어진다**(1번의 `S2`).\
  ★ 없는 것을 trivial 하게 부를 수는 없다.
- ★ **`sizeof` 는 여덟 타입 모두 4** 다. **이 성질들은 크기에 아무 흔적도 안 남긴다** — 격자 말고는 볼 창이 없다.
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic rule03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
타입 | t기본 t복사 t소멸 trivial | sizeof
T0  |   1     1     1     1   |  4
T1  |   1     1     1     1   |  4
T2  |   0     1     1     0   |  4
T3  |   1     1     1     1   |  4
T4  |   0     0     0     0   |  4
T5  |   0     1     1     0   |  4
T6  |   0     0     1     0   |  4
T7  |   0     0     0     0   |  4
```

### 4. ★★ **`f(1.0f)` 이 에러**다 — 안 썼다면 `f(int)` 로 통과했을 것이다

**출력**

```cpp
/* rule04.cpp */
// = delete 는 후보에서 빠지는 것이 아니라 뽑힌 뒤 거부된다
#include <cstdio>
void f(int)    { std::printf("f(int)\n"); }
void f(double) = delete;                       // 실수로 double 로 부르는 것을 막고 싶다

struct M {
    int x;
    M() : x(0) {}
    M(const M&) = default;
    M(M&&)      = delete;                      // 이동은 지우고 복사만 남긴다
};

int main() {
    f(1);                                      // int 는 정확히 맞는다
    f(1.0f);                                   // float -> double 이 float -> int 보다 나은 변환이다
    M a;
    M b = a;                                   // 복사 — 된다
    M c = static_cast<M&&>(a);                 // 이동이 뽑힌 뒤 거부된다
    (void)b; (void)c;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 rule04.cpp -o ex (cc exit=1) =====
rule04.cpp: In function ‘int main()’:
rule04.cpp:15:6: error: use of deleted function ‘void f(double)’
   15 |     f(1.0f);                                   // float -> double 이 float -> int 보다 나은 변환이다
      |     ~^~~~~~
rule04.cpp:4:6: note: declared here
    4 | void f(double) = delete;                       // 실수로 double 로 부르는 것을 막고 싶다
      |      ^
rule04.cpp:18:29: error: use of deleted function ‘M::M(M&&)’
   18 |     M c = static_cast<M&&>(a);                 // 이동이 뽑힌 뒤 거부된다
      |                             ^
rule04.cpp:10:5: note: declared here
   10 |     M(M&&)      = delete;                      // 이동은 지우고 복사만 남긴다
      |     ^
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 rule04.cpp -o ex (cc exit=1) =====
rule04.cpp:15:5: error: call to deleted function 'f'
   15 |     f(1.0f);                                   // float -> double 이 float -> int 보다 나은 변환이다
      |     ^
rule04.cpp:4:6: note: candidate function has been explicitly deleted
    4 | void f(double) = delete;                       // 실수로 double 로 부르는 것을 막고 싶다
      |      ^
rule04.cpp:3:6: note: candidate function
    3 | void f(int)    { std::printf("f(int)\n"); }
      |      ^
rule04.cpp:18:7: error: call to deleted constructor of 'M'
   18 |     M c = static_cast<M&&>(a);                 // 이동이 뽑힌 뒤 거부된다
      |       ^   ~~~~~~~~~~~~~~~~~~~
rule04.cpp:10:5: note: 'M' has been explicitly marked deleted here
   10 |     M(M&&)      = delete;                      // 이동은 지우고 복사만 남긴다
      |     ^
2 errors generated.
```

**왜 그런가**

- ★★★ **`f(1)` 은 통과하고 `f(1.0f)` 이 에러다.**\
  `float` 에서는 `double` 로 가는 것(부동소수 승격)이 `int` 로 가는 것(부동소수→정수 변환)보다 **나은 변환**이다.\
  그래서 오버로드 해결이 **`f(double)` 을 뽑고**, **그다음에** 「지워졌다」고 거부한다.
- ★★★ **`f(double) = delete;` 를 아예 안 썼다면 `f(int)` 가 뽑혀 조용히 통과했을 것**이다.\
  ★ **그것이 `= delete` 의 쓸모다** — 「없는 것」이 아니라 「**후보에 남아 막는 것**」이다.
- ★★★ **`M c = static_cast<M&&>(a);` 가 에러인 이유도 같다.**\
  `M` 에는 **복사 생성자가 있지만**, rvalue 에는 **이동 생성자가 더 나은 후보**라 그것이 뽑힌다.\
  뽑힌 뒤 「지워졌다」고 거부되므로 **복사로 떨어지지 않는다.**
- ★★ **두 컴파일러 다 에러 2건**이고 `cc exit=1` 이다.\
  ★ clang 은 **후보 목록까지 보여 준다**(`candidate function has been explicitly deleted` + `candidate function`).\
  진단 문구는 **구현 정의**이므로 근거로 쓰는 것은 **에러 개수**와 진단의 `(행,열)` 둘이다.

### 5. ★★★ 격자가 **한 칸도 안 다르다** · 이동에서 할당 **0회** · `new`/`delete` **3회씩**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic rule05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
타입  | 복사생 복사대 이동생 이동대 | 이동이 noexcept 인가 | 손으로 쓴 특수 멤버
Five  |   0      0      1      1   |         1            |        5개
Zero  |   0      0      1      1   |         1            |        0개
(1) Zero 를 옮긴다 — 할당이 몇 번 더 나나
    생성에서 3회 · 이동에서 0회
    블록을 나온 뒤 new 3회 · delete 3회
```

**왜 그런가**

- ★★★ **`Five`(다섯 줄)와 `Zero`(0줄)의 격자가 같다** — 복사 `0` · 이동 `1` · `noexcept` `1`.\
  ★ `Zero` 가 그 성질을 **멤버에게서 물려받았기 때문**이다. `unique_ptr` 이 복사 불가이므로 타입도 복사 불가가 된다.
- ★★★ **이동에서 할당이 0회다.** 멤버 셋이 각자 **자기 자원을 훔쳐 온다** —\
  [17번](../17-move-constructor-assignment-and-moved-from-state/) (2)의 일이 **세 번 일어나는 것**이다.
- ★★ **`new 3회 · delete 3회`** 로 맞는다 — **누수도 이중 해제도 없다.**\
  ★ 셋은 `unique_ptr<char[]>` · `vector<int>` · `string` 이다(64바이트 문자열이라 **SSO 를 넘어 힙에 간다**).
- ★★★ **그 계수는 전역 `operator new`/`operator delete` 를 갈아끼워** 셌다.\
  ★ C++ 표준에 **런타임 할당 계수기가 없기 때문**이다. [15번](../15-raii-resources-as-types/)은 같은 질문을 **ASan 누수 리포트**로 바꿔 물었다 —\
  **같은 질문에 창을 바꿔 답한 것**이지 안 물어본 것이 아니다.
- ★★★ **그래서 규칙은 넷으로 읽는 것이 맞다.**
  - **0의 법칙** — 자원을 직접 안 들면 **다섯을 하나도 안 쓴다.** **기본값이다.**
  - **3의 법칙** — 소멸자·복사 생성자·복사 대입 중 하나를 쓰면 **셋을 다**(C++98).
  - **5의 법칙** — 거기에 **이동 둘**을 더한다(2번이 그 이유다).
  - ★ **현실판** — 자원을 직접 들어야 하면 **타입을 쪼개서 0으로 돌아간다**([15번](../15-raii-resources-as-types/) (6)).

### 6. ★★ 탐침 여섯 중 **둘**이 답했다 — **2번과 6번**이다

**출력**

```cpp
/* rule06.cpp */
// 0/3/5 를 어긴 자리 여섯을 심었다 — 컴파일러가 몇 군데에서 말하는지 센다
#include <cstdio>
#include <cstdlib>
#include <utility>

struct R1 { char* p;                          // 1. 소멸자만 썼다 — 3의 법칙 위반
    R1() : p(static_cast<char*>(std::malloc(8))) {}
    ~R1() { std::free(p); } };
struct R2 { int a;                            // 2. 복사 생성자만 썼다
    R2() : a(0) {}
    R2(const R2& o) : a(o.a) {} };
struct R3 { int a;                            // 3. 이동 생성자만 썼다 — 복사가 지워진다
    R3() : a(0) {}
    R3(R3&& o) noexcept : a(o.a) {} };
struct R4 { char* p;                          // 4. 소멸자 + 복사는 막았는데 이동을 안 열었다
    R4() : p(static_cast<char*>(std::malloc(8))) {}
    ~R4() { std::free(p); }
    R4(const R4&) = delete;
    R4& operator=(const R4&) = delete; };
struct R5 { int a; ~R5(); };                  // 5. 클래스 밖 = default — trivial 이 아니게 된다
R5::~R5() = default;
struct R6 { int a;                            // 6. 복사 대입만 썼다
    R6() : a(0) {}
    R6& operator=(const R6& o) { a = o.a; return *this; } };

int main() {
    R1 a; R1 b(a);                            // 얕은 복사 — 소멸자 둘이 같은 포인터를 놓는다
    R2 c; R2 d(c); c = d;                     // 암묵 복사 대입을 쓴다
    R3 e; R3 f(std::move(e)); (void)f;
    R4 g; (void)g;
    R5 h; R5 i(h); (void)i;
    R6 j, k; j = k; R6 l(j); (void)l;
    std::printf("여섯 자리 전부 컴파일됐다\n");
    a.p = nullptr; b.p = nullptr;             // 이중 해제를 피해 치운다
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic rule06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
rule06.cpp: In function ‘int main()’:
rule06.cpp:28:24: warning: implicitly-declared ‘constexpr R2& R2::operator=(const R2&)’ is deprecated [-Wdeprecated-copy]
   28 |     R2 c; R2 d(c); c = d;                     // 암묵 복사 대입을 쓴다
      |                        ^
rule06.cpp:11:5: note: because ‘R2’ has user-provided ‘R2::R2(const R2&)’
   11 |     R2(const R2& o) : a(o.a) {} };
      |     ^~
rule06.cpp:32:27: warning: implicitly-declared ‘constexpr R6::R6(const R6&)’ is deprecated [-Wdeprecated-copy]
   32 |     R6 j, k; j = k; R6 l(j); (void)l;
      |                           ^
rule06.cpp:24:9: note: because ‘R6’ has user-provided ‘R6& R6::operator=(const R6&)’
   24 |     R6& operator=(const R6& o) { a = o.a; return *this; } };
      |         ^~~~~~~~
여섯 자리 전부 컴파일됐다
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic rule06.cpp -o ex (cc exit=0) =====
rule06.cpp:11:5: warning: definition of implicit copy assignment operator for 'R2' is deprecated because it has a user-provided copy constructor [-Wdeprecated-copy-with-user-provided-copy]
   11 |     R2(const R2& o) : a(o.a) {} };
      |     ^
rule06.cpp:28:22: note: in implicit copy assignment operator for 'R2' first required here
   28 |     R2 c; R2 d(c); c = d;                     // 암묵 복사 대입을 쓴다
      |                      ^
rule06.cpp:24:9: warning: definition of implicit copy constructor for 'R6' is deprecated because it has a user-provided copy assignment operator [-Wdeprecated-copy-with-user-provided-copy]
   24 |     R6& operator=(const R6& o) { a = o.a; return *this; } };
      |         ^
rule06.cpp:32:24: note: in implicit copy constructor for 'R6' first required here
   32 |     R6 j, k; j = k; R6 l(j); (void)l;
      |                        ^
2 warnings generated.
```

```text
===== echo "rule06 탐침 여섯  g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic rule06.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
rule06 탐침 여섯  g++ 경고 2
===== echo "rule06 탐침 여섯  clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic rule06.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
rule06 탐침 여섯  clang 경고 2
===== echo "rule06 을 ASan 으로 돌리면: $(g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. rule06.cpp -o exa 2>/dev/null; ./exa >/dev/null 2>asan18.txt; grep -cE 'ERROR: (Address|Leak)Sanitizer' asan18.txt) 건" (exit=0) =====
rule06 을 ASan 으로 돌리면: 1 건
===== echo "그 리포트의 요약: $(grep -hE '^SUMMARY' asan18.txt | head -1 | grep . || echo 리포트 없음)" (exit=0) =====
그 리포트의 요약: SUMMARY: AddressSanitizer: 8 byte(s) leaked in 1 allocation(s).
```

**왜 그런가**

| 심은 것 | g++ | clang | 실제로는 |
|---|---|---|---|
| 1. 소멸자만 썼다 | 0 | 0 | ★★★ 얕은 복사 → 이중 해제 · 이동도 사라졌다 |
| 2. 복사 생성자만 썼다 | ★ **1** | ★ **1** | 암묵 복사 **대입**이 deprecated |
| 3. 이동 생성자만 썼다 | 0 | 0 | ★★★ 복사가 `= delete` 된다 |
| 4. 소멸자+복사 차단, 이동 안 엶 | 0 | 0 | ★★ 옮길 수도 복사할 수도 없다 |
| 5. 클래스 밖 `= default` | 0 | 0 | ★★★ trivial 이 아니게 된다 |
| 6. 복사 대입만 썼다 | ★ **1** | ★ **1** | 암묵 복사 **생성자**가 deprecated |

- ★★★ **답한 것 2, 침묵한 것 4**이고 `cc exit=0` 이다.
- ★★★ **답한 둘의 공통점** — **3의 법칙의 두 방향**이다(복사 생성자만 · 복사 대입만).\
  ★ **안 답한 넷의 공통점** — **이동과 `= default` 가 걸린 자리**다. **5의 법칙은 하나도 안 잡힌다.**
- ★★ **ASan 은 `8 byte(s) leaked in 1 allocation(s)`** 를 잡는다 — **탐침 4번의 `R4`** 가 샌 것이다.\
  ★ 탐침 1번의 얕은 복사는 소스가 `a.p = nullptr;` 로 **치워 놓아** 안 잡혔다.\
  **「탐침을 심었다」와 「그 경로를 밟았다」는 다른 것**이다([16번](../16-copy-constructor-and-copy-assignment/) 7번과 같은 교훈).
- ★★ **가장 위험한 것은 5번이다** — 경고도 없고 ASan 도 안 보고 **격자로만** 드러난다(3번의 `T7`).

### 7. ★★ 둘 다 **`cc exit=0`** 이고 값까지 그럴듯하다

**출력**

```cpp
/* rule07.cpp */
// 종료 코드가 0인데 표준이 금지한 것 둘 — 익명 구조체 멤버와 비-trivially-copyable 의 memcpy
#include <cstdio>
#include <cstring>
#include <string>
#include <type_traits>

struct Pair { struct { int a; int b; }; };      // ① ISO C++ 는 익명 구조체를 금지한다
struct NT   { std::string s; int x; };          // ② trivially copyable 이 아니다

int main() {
    Pair p; p.a = 1; p.b = 2;
    Pair q = p;                                 // 암묵 복사 생성자는 그래도 만들어진다
    std::printf("익명 구조체 멤버를 복사하면  q.a=%d q.b=%d\n", q.a, q.b);

    NT u{"가", 1}, v{"나", 2};
    std::printf("is_trivially_copyable<NT> = %d\n", (int)std::is_trivially_copyable_v<NT>);
    std::memcpy(&v, &u, sizeof(NT));            // ★ 표준이 금지한 것 — UB 다
    std::printf("memcpy 뒤 v.x = %d\n", v.x);
    new (&v) NT{"치운다", 0};                    // 소멸자가 같은 버퍼를 두 번 놓지 않도록 덮어쓴다
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic rule07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
rule07.cpp:7:22: warning: ISO C++ prohibits anonymous structs [-Wpedantic]
    7 | struct Pair { struct { int a; int b; }; };      // ① ISO C++ 는 익명 구조체를 금지한다
      |                      ^
rule07.cpp: In function ‘int main()’:
rule07.cpp:17:16: warning: ‘void* memcpy(void*, const void*, size_t)’ writing to an object of type ‘struct NT’ with no trivial copy-assignment; use copy-assignment or copy-initialization instead [-Wclass-memaccess]
   17 |     std::memcpy(&v, &u, sizeof(NT));            // ★ 표준이 금지한 것 — UB 다
      |     ~~~~~~~~~~~^~~~~~~~~~~~~~~~~~~~
rule07.cpp:8:8: note: ‘struct NT’ declared here
    8 | struct NT   { std::string s; int x; };          // ② trivially copyable 이 아니다
      |        ^~
익명 구조체 멤버를 복사하면  q.a=1 q.b=2
is_trivially_copyable<NT> = 0
memcpy 뒤 v.x = 1
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic rule07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
rule07.cpp:7:15: warning: anonymous structs are a GNU extension [-Wgnu-anonymous-struct]
    7 | struct Pair { struct { int a; int b; }; };      // ① ISO C++ 는 익명 구조체를 금지한다
      |               ^
1 warning generated.
익명 구조체 멤버를 복사하면  q.a=1 q.b=2
is_trivially_copyable<NT> = 0
memcpy 뒤 v.x = 1
```

```text
===== echo "g++ -pedantic-errors 에러 $(g++ -std=c++20 -Wall -Wextra -pedantic-errors -fmax-errors=0 rule07.cpp -o ex 2>&1 | grep -c 'error:')" (exit=0) =====
g++ -pedantic-errors 에러 1
===== echo "clang -pedantic-errors 에러 $(clang++ -std=c++20 -Wall -Wextra -pedantic-errors -ferror-limit=0 rule07.cpp -o ex 2>&1 | grep -c 'error:')" (exit=0) =====
clang -pedantic-errors 에러 1
```

**왜 그런가**

| 심은 것 | g++ `-pedantic` | clang `-pedantic` | `-pedantic-errors` |
|---|---|---|---|
| ① 익명 구조체 멤버 | ★★ **warning** | ★★ **warning**(GNU 확장이라고 부른다) | ★★★ **양쪽 에러 1건** |
| ② 비 trivially-copyable 을 `memcpy` | ★ **warning**(`-Wclass-memaccess`) | ★★★ **0건** | ★★★ **양쪽 그대로 통과** |

- ★★★ **둘 다 `cc exit=0` · `run exit=0`** 이고 값까지 그럴듯하게 나온다(`q.a=1 q.b=2` · `memcpy 뒤 v.x = 1`).
- ★★★ **①은 `-pedantic-errors` 라야 잡힌다.** `-pedantic` 만으로는 경고에 머문다 —\
  [14번](../14-destructors-and-deterministic-destruction/) (8)이 실측한 것과 **같은 집안**이다.
- ★★★ **②가 두 컴파일러가 갈리는 자리다.** g++ 는 경고를 내고 **clang 은 아예 침묵한다.**\
  ★ 그리고 `-pedantic-errors` 로도 **양쪽 다 안 잡힌다** — **UB 이지 ill-formed 가 아니기** 때문이다.
- ★★★ **같은 프로그램이 `is_trivially_copyable<NT> = 0` 이라고 찍어 놓고도** 그 값을 `memcpy` 에 연결해 주는 것은 **g++ 뿐**이다.\
  ★ **3번의 격자가 왜 실용적인지**가 여기서 보인다 — **격자가 `0` 이라고 말한 타입을 `memcpy` 로 옮기면 UB** 이고,\
  **도구는 그것을 반만 본다.**

### 8. ★ 근거는 **2번의 출력** 하나다

- 「소멸자를 썼으면 나머지 넷도 결정하라」가 **취향이 아닌 근거**는 2번의 `(1)`·`(2)` 로그다 —\
  **소멸자 한 줄에 `std::move` 가 복사로 떨어진다.**\
  ★ 그리고 `(4)` 가 그것을 **컨테이너 동작까지** 끌고 간다.
- ★★ **3의 법칙과 5의 법칙이 갈린 지점은 C++11 이다.**\
  C++98 에는 **이동이라는 개념이 없어서** 챙길 것이 셋뿐이었다.\
  C++11 이 이동 둘을 더하면서 「**소멸자를 쓰면 이동이 사라진다**」는 새 연쇄가 생겼고,\
  그래서 셋이 다섯이 됐다. ★ **같은 규칙의 확장이 아니라 새 규칙이 붙은 것**이다.

### 9. ★★ **표준 · 표준 · UB 아님 · 관찰** 넷으로 갈린다

- 「**소멸자를 선언하면 이동이 안 만들어진다**」 — ★★★ **표준**이다. 언어 규칙이고 구현의 재량이 아니다.\
  ★ 두 컴파일러에서 같았던 것은 **확인**이지 근거가 아니다.
- 「**클래스 밖 `= default` 는 trivial 이 아니다**」 — ★★★ **표준**이다.\
  첫 선언이 아닌 `= default` 는 **사용자 제공**으로 친다.
- ★★★ 「**0/3/5 를 어기는 것**」 자체는 **UB 가 아니다.** 그냥 **합법인 코드**다.\
  ★ **그래서 경고가 거의 없다** — 컴파일러가 말할 근거가 없다. 탐침 여섯 중 넷이 침묵한 이유다.\
  ★ UB 가 되는 것은 **그 결과로 생긴 이중 해제·누수**이고, 그것도 **경로를 밟아야** 드러난다.
- 「**`new 3회`**」 — ★★★ **관찰**이다. `string`·`vector`·`unique_ptr` 각각의 할당 전략은 **구현이 정한다.**\
  ★ 작은 문자열 최적화가 꺼지거나 크기가 달라지면 **수가 달라진다.**

### 10. 다른 주제와 잇기

- **(2)의 `vector` 재할당**이 갈리는 것은 [17번](../17-move-constructor-assignment-and-moved-from-state/) **(3)과 같은 자리**다.\
  ★ 거기서는 **`noexcept` 한 낱말**이, 여기서는 **소멸자 한 줄**이 같은 결과를 만든다.
- ★★ **이 주제를 예고한 경고**는 [16번](../16-copy-constructor-and-copy-assignment/) **(7)의 탐침 2번**이다 —\
  거기서 **두 컴파일러가 유일하게 답한 자리**가 바로 3의 법칙이었다.
- ★★ 「**자원을 둘 이상 들면 타입을 쪼갠다**」의 정본은 [15번](../15-raii-resources-as-types/)의 **(6)이 그 자리다** —\
  생성자가 완주하지 못하면 **이미 지어진 멤버만** 파괴된다.
- ★★★ **러스트는 기본값이 정반대다** — Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **9번**([`09-copy-clone-and-drop/`](../../../rust/syntax/09-copy-clone-and-drop/)).\
  **`#[derive(Clone)]` 을 적어야** 복사가 생긴다. C++ 은 **적지 않아야** 생긴다.\
  ★ **그래서 러스트에는 「조용히 사라지는」 자리가 없다** — 2번 같은 사고가 성립하지 않는다.\
  ★ **대가는 매번 적어야 한다는 것**이다. C++ 의 0의 법칙은 **아무것도 안 적고** 다섯을 얻는다.
- ★ **GC 가 있는 언어에 그 연쇄가 없는 이유** — **해제와 복사가 다른 축**이기 때문이다.\
  `IDisposable` 을 구현해도 **복사 동작은 아무것도 안 바뀐다.**\
  C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **37번 주제**가 그 자리다.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `rule01.cpp` 아홉 타입 격자 | g++ · clang 각 1회 | ★★★ `S1` 이 `S0` 와 **동일** · `S3` 복사 **0** · `S5` 비대칭 · `S8` 만 `noexcept` **0** · 두 컴파일러 동일 |
| `rule02.cpp` 소멸자가 이동을 지움 | g++ · clang 각 1회 | ★★★ **이동 대 복사** 로그 · `is_move_constructible` **1 대 1** · `nothrow` **1 대 0** · `vector` 재할당도 갈림 |
| `rule03.cpp` `= default` 대 `{}` | g++ · clang 각 1회 | ★★★ `T1`/`T2` **trivial 1 대 0** · `T4` **네 칸 0** · `T7` 이 `T4` 와 **동일** · `sizeof` 전부 **4** |
| `rule04.cpp` `= delete` 오버로드 | g++ · clang 각 1회 | ★★ **양쪽 에러 2건**(`f(1.0f)` · `static_cast<M&&>`) · `cc exit=1` |
| `rule05.cpp` 0의 법칙 | g++ 1회 | ★★★ 격자 **동일** · 이동에서 할당 **0회** · `new 3 · delete 3` |
| `rule06.cpp` 탐침 여섯 | g++ · clang 각 1회 + ASan 1회 | ★★★ **경고 2 · 2**(탐침 2·6번) · ASan **8바이트 · 1할당** |
| `rule07.cpp` ill-formed | g++ · clang 각 1회 + `-pedantic-errors` 2회 | ★★★ **양쪽 `cc exit=0`** · `-pedantic-errors` 는 **양쪽 에러 1건** · ②는 clang **0건** |
| `rule08.cpp` 형태 | g++ 1회 | `Zero` 이동 가능 **1** · `Five` 복사 **0** · `Explicit` trivial **1** |
| `rule09.cpp` 금지 사례 | g++ 1회 | **에러 4건**(`= default` 오용 · 지워진 기본 생성자 · 지워진 복사 · 값 전달) |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · libstdc++ · ASan)에서만** 그렇다.

- ★★★ **5번의 `new 3회`** — 표준 라이브러리의 할당 전략(SSO 포함)에 달려 있다.
- ★★★ **7번의 ②에서 clang 이 침묵한 것** — 경고를 낼지는 **컴파일러의 재량**이다.
- ★★ **진단 문구와 경고 이름 전부** · **clang 이 후보 목록을 보여 주는 것** · **`sizeof` 가 4인 것.**
- ★ **ASan 리포트의 PID·주소** · **ASan 이 누수를 보고하는 기본값.**

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **1번·3번·5번 격자의 0/1 전부** — 언어 규칙이 정한 값이다.
- ★★★ **소멸자를 선언하면 이동 생성자·이동 대입이 안 만들어지는** 것.
- **이동 생성자를 선언하면 복사 둘이 `= delete` 되는** 것.
- **복사 생성자를 선언하면 기본 생성자가 안 만들어지는** 것.
- ★★★ **`= delete` 가 오버로드 해결에 참여하고 뽑힌 뒤 거부되는** 것.
- **클래스 밖 `= default` 는 사용자 제공으로 쳐서 trivial 이 아닌** 것.
- **익명 구조체 멤버가 ISO C++ 에서 ill-formed 인** 것(7번의 ①).

**UB 의 결과라 보장이 아닌 것**(관찰로만 읽는다)

- ★★★ **7번의 ②** — 비 trivially-copyable 을 `memcpy` 하는 것은 **UB** 다.\
  이 판에서 `v.x = 1` 이 나온 것은 **관찰**이고, 근거로 쓸 수 있는 것은 「**두 컴파일러 다 통과시켰다**」뿐이다.
- ★★ **6번의 탐침 1번** — 얕은 복사 뒤의 이중 해제. 소스가 치워 놓아 **이 판에서는 안 터졌다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **`-std=c++11`·`c++14`·`c++17` 판**(전부 `-std=c++20` — 특히 `= default` 의 예외 명세 규칙이 C++17 에서 바뀌었다) ·\
  ★ **`=delete("이유")`(C++26)** — 이 머신의 컴파일러 판에서는 **안 던졌다** ·\
  ★ **clang 으로 `rule05`·`rule08`·`rule09`**(g++ 로만 던졌다) ·\
  ★ **`S1` 의 멤버를 `string` 으로 바꿔 1번을 다시 찍는 판**(그러면 `S8` 과 같아질 것이다 — **확인 안 했다**).
- **못 잰 것** — ★★★ **「자동 생성된 함수가 실제로 어떤 코드인가」.**\
  이 문서가 센 것은 **선언의 유무(트레이트)와 호출 로그까지**다. **본문을 열어 보지는 않았다.**\
  ★★ **런타임 할당 계수기**가 C++ 표준에 없어 5번은 **전역 `operator new` 를 갈아끼웠다.**
- ★ 「**부적용인 창**」 — **`-O2` 어셈블리 세기.** 이 편의 질문은 **선언의 유무**이고 그것은 **트레이트가 답한다.**\
  **「안 쟀다」가 아니라 「잴 것이 없다」다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **7번의 ②** — clang 이 `-Wclass-memaccess` 상당의 경고를 붙이기 시작했는지.
- ★★★ **6번의 탐침 중 이동 쪽 하나라도 답하기 시작했는지**(지금은 **3의 법칙 둘뿐**).
- ★★ **5번의 `new 3회`** — 표준 라이브러리 구현이 바뀌면 움직인다.
- ★ **`=delete("이유")`** 가 받아들여지는지 — 받아들여지면 4번에 판이 하나 더 붙는다.
