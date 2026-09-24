# cpp/syntax/09 — rvalue 참조·`std::move`·`std::forward` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·기계어는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **GNU objdump/nm 2.42** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이라 질문 쪽 발췌와 어긋날 수 있다 —\
> 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★★ 이 주제의 주력 창은 **복사·이동 생성자 로그**다. 「이동이 났다」는 **센 것**이지 읽은 것이 아니다.
> **읽는 법** — 기계어 덤프의 **주소·오프셋**과 ASan 의 **PID·주소**는 흔들리는 칸이다.\
> 근거로 쓰는 것은 **명령어 열** · **호출 횟수** · **경고 이름** · **`cc exit`/`run exit`** 다.\
> ★ UB 는 9번 하나다(이동 후 `front()`). **그 UB 가 만든 값은 싣지 않았다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 전부 `&&` — 그리고 `const` 는 떨어지지 않는다

**출력**

```text
===== 소스: mvsem01.cpp =====
// std::move 는 캐스트다 — 타입으로 확인한다
#include <type_traits>
#include <string>
#include <utility>

template <class T> struct TypeOf;

int main() {
    int i = 0;
    const int ci = 0;
    std::string s = "hi";

    TypeOf<decltype(std::move(i))>              m1;
    TypeOf<decltype(static_cast<int&&>(i))>     m2;
    TypeOf<decltype(std::move(ci))>             m3;   // ★ const 가 붙어 나온다
    TypeOf<decltype(std::move(s))>              m4;
    TypeOf<decltype(std::move(std::move(i)))>   m5;   // 두 번 걸어도
    static_assert(std::is_same_v<decltype(std::move(i)),
                                 decltype(static_cast<int&&>(i))>);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic mvsem01.cpp -o ex 2>&1 | grep 'incomplete type' (cc exit=1) =====
mvsem01.cpp:13:49: error: aggregate ‘TypeOf<int&&> m1’ has incomplete type and cannot be defined
mvsem01.cpp:14:49: error: aggregate ‘TypeOf<int&&> m2’ has incomplete type and cannot be defined
mvsem01.cpp:15:49: error: aggregate ‘TypeOf<const int&&> m3’ has incomplete type and cannot be defined
mvsem01.cpp:16:49: error: aggregate ‘TypeOf<std::__cxx11::basic_string<char>&&> m4’ has incomplete type and cannot be defined
mvsem01.cpp:17:49: error: aggregate ‘TypeOf<int&&> m5’ has incomplete type and cannot be defined
```

**왜 그런가**

| 줄 | 쓴 것 | 찍힌 타입 |
|---|---|---|
| `m1` | `std::move(i)` | `int&&` |
| `m2` | `static_cast<int&&>(i)` | ★ **같은 `int&&`** |
| `m3` | `std::move(ci)` | ★★★ **`const int&&`** |
| `m4` | `std::move(s)` | `std::__cxx11::basic_string<char>&&` |
| `m5` | `std::move(std::move(i))` | `int&&` — 멱등이다 |

- ★★★ **`m1` 과 `m2` 가 한 글자도 다르지 않다.** `std::move` 의 몸통이 **그 캐스트 한 줄**이기 때문이다.\
  소스의 `static_assert` 도 통과했다 — **실패했다면 에러 목록에 한 줄이 더 있었을 것**이다.
- ★★★ **`m3` 에 `const` 가 그대로 남았다.** `std::move` 는 **`const` 를 떼지 않는다** —\
  `remove_reference` 는 **참조만** 떼고 **`const` 는 건드리지 않기** 때문이다.\
  ★ 6번의 「조용한 복사」가 전부 이 한 줄에서 나온다.
- ★ `m4` 의 `__cxx11` 는 **libstdc++ 의 인라인 네임스페이스**다 — **구현 이름이지 표준 이름이 아니다.**

### 2. ★★★ `-O0` 은 다르고 `-O2` 는 같다

**출력** — 먼저 `-O0`.

```text
===== 소스: mvsem02.cpp =====
// std::move 가 낳는 코드 — 손으로 쓴 캐스트와 같은가
#include <utility>

int&& via_move(int& x) { return std::move(x); }
int&& via_cast(int& x) { return static_cast<int&&>(x); }
int&  no_cast (int& x) { return x; }
===== g++ -std=c++20 -O0 -c mvsem02.cpp -o mv00.o && objdump -d --no-show-raw-insn mv00.o | sed -n '/>:/,$p' (exit=0) =====
0000000000000000 <_Z8via_moveRi>:
   0:	endbr64
   4:	push   %rbp
   5:	mov    %rsp,%rbp
   8:	sub    $0x10,%rsp
   c:	mov    %rdi,-0x8(%rbp)
  10:	mov    -0x8(%rbp),%rax
  14:	mov    %rax,%rdi
  17:	call   1c <_Z8via_moveRi+0x1c>
  1c:	leave
  1d:	ret

000000000000001e <_Z8via_castRi>:
  1e:	endbr64
  22:	push   %rbp
  23:	mov    %rsp,%rbp
  26:	mov    %rdi,-0x8(%rbp)
  2a:	mov    -0x8(%rbp),%rax
  2e:	pop    %rbp
  2f:	ret

0000000000000030 <_Z7no_castRi>:
  30:	endbr64
  34:	push   %rbp
  35:	mov    %rsp,%rbp
  38:	mov    %rdi,-0x8(%rbp)
  3c:	mov    -0x8(%rbp),%rax
  40:	pop    %rbp
  41:	ret

Disassembly of section .text._ZSt4moveIRiEONSt16remove_referenceIT_E4typeEOS2_:

0000000000000000 <_ZSt4moveIRiEONSt16remove_referenceIT_E4typeEOS2_>:
   0:	endbr64
   4:	push   %rbp
   5:	mov    %rsp,%rbp
   8:	mov    %rdi,-0x8(%rbp)
   c:	mov    -0x8(%rbp),%rax
  10:	pop    %rbp
  11:	ret
```

**왜 그런가**

```text
   via_move   endbr64 / push / mov / sub $0x10 / mov / mov / ★ call / leave / ret
   via_cast   endbr64 / push / mov / mov / mov / pop / ret
   no_cast    endbr64 / push / mov / mov / mov / pop / ret      ← via_cast 와 같다

   그리고 호출되는 std::move 의 몸통:
              endbr64 / push / mov / mov / mov / pop / ret      ← 받은 것을 그대로 돌려준다 (mov 둘은 저장·적재)
```

- ★★★ **`via_move` 에만 `call` 이 있다.** `-O0` 에서는 `std::move` 가 **진짜 함수 호출**이다.
- ★★ 그 함수가 하는 일은 **인자를 반환 레지스터로 옮기는 것뿐**이다\
  (`-O0` 이라 스택을 한 번 거친다: `mov %rdi,-0x8(%rbp)` → `mov -0x8(%rbp),%rax`).\
  「아무것도 안 옮긴다」가 **기계어로** 보이는 자리다.
- ★★ **`via_cast` 와 `no_cast` 가 같다** — `static_cast<T&&>` 도 `T&` 도 **기계어가 같은 포인터 전달**이다.

**`-O2` 로 올리면 셋이 같아진다.**

```text
===== 소스: mvsem02.cpp =====
// std::move 가 낳는 코드 — 손으로 쓴 캐스트와 같은가
#include <utility>

int&& via_move(int& x) { return std::move(x); }
int&& via_cast(int& x) { return static_cast<int&&>(x); }
int&  no_cast (int& x) { return x; }
===== g++ -std=c++20 -O2 -c mvsem02.cpp -o mv02.o && objdump -d --no-show-raw-insn mv02.o | sed -n '/>:/,$p' (exit=0) =====
0000000000000000 <_Z8via_moveRi>:
   0:	endbr64
   4:	mov    %rdi,%rax
   7:	ret
   8:	nopl   0x0(%rax,%rax,1)

0000000000000010 <_Z8via_castRi>:
  10:	endbr64
  14:	mov    %rdi,%rax
  17:	ret
  18:	nopl   0x0(%rax,%rax,1)

0000000000000020 <_Z7no_castRi>:
  20:	endbr64
  24:	mov    %rdi,%rax
  27:	ret
```

- ★★★ **세 함수가 `endbr64 / mov %rdi,%rax / ret`** 로 한 글자도 다르지 않다.
- ★★ **답이 최적화 수준에 따라 바뀐다** — 그래서 「`std::move` 는 공짜다」를 적을 때 **수준을 같이** 적어야 한다.

심볼 목록이 그 차이를 한 번 더 확인해 준다.

```text
===== 소스: mvsem02.cpp =====
// std::move 가 낳는 코드 — 손으로 쓴 캐스트와 같은가
#include <utility>

int&& via_move(int& x) { return std::move(x); }
int&& via_cast(int& x) { return static_cast<int&&>(x); }
int&  no_cast (int& x) { return x; }
===== g++ -std=c++20 -O0 -c mvsem02.cpp -o mv00.o && nm -C mv00.o; echo '--- -O2 ---'; g++ -std=c++20 -O2 -c mvsem02.cpp -o mv02.o && nm -C mv02.o (exit=0) =====
0000000000000030 T no_cast(int&)
000000000000001e T via_cast(int&)
0000000000000000 T via_move(int&)
0000000000000000 W std::remove_reference<int&>::type&& std::move<int&>(int&)
--- -O2 ---
0000000000000020 T no_cast(int&)
0000000000000010 T via_cast(int&)
0000000000000000 T via_move(int&)
```

- ★★ `-O0` 에는 `std::move<int&>(int&)` 가 **`W`(약한 심볼)로 있고**, `-O2` 목록에는 **없다**.
- ★ 「인라인됐을 것이다」가 아니라 「**목록에서 사라졌다**」가 근거다.

### 3. ★ 두 줄 · 두 줄 · **한 줄** — 세 번째가 답이다

**출력**

```text
===== 소스: mvsem03.cpp =====
// 복사와 이동을 로그로 가른다
#include <cstdio>
#include <utility>

struct Noisy {
    int id;
    explicit Noisy(int i) : id(i) { std::printf("    ctor(%d)\n", id); }
    Noisy(const Noisy& o) : id(o.id) { std::printf("    copy(%d)\n", id); }
    Noisy(Noisy&& o) noexcept : id(o.id) { std::printf("    move(%d)\n", id); o.id = -1; }
    ~Noisy() { std::printf("    dtor(%d)\n", id); }
};

int main() {
    std::puts("[1] Noisy a(1); Noisy b = a;");
    { Noisy a(1); Noisy b = a;
      std::printf("    a.id=%d b.id=%d\n", a.id, b.id); }
    std::puts("[2] Noisy c(2); Noisy d = std::move(c);");
    { Noisy c(2); Noisy d = std::move(c);
      std::printf("    c.id=%d d.id=%d\n", c.id, d.id); }
    std::puts("[3] std::move 만 하고 아무 데도 안 쓰면");
    { Noisy e(3); (void)std::move(e);
      std::printf("    e.id=%d  — 아무 일도 안 일어났다\n", e.id); }
    std::puts("[4] main 끝");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic mvsem03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] Noisy a(1); Noisy b = a;
    ctor(1)
    copy(1)
    a.id=1 b.id=1
    dtor(1)
    dtor(1)
[2] Noisy c(2); Noisy d = std::move(c);
    ctor(2)
    move(2)
    c.id=-1 d.id=2
    dtor(2)
    dtor(-1)
[3] std::move 만 하고 아무 데도 안 쓰면
    ctor(3)
    e.id=3  — 아무 일도 안 일어났다
    dtor(3)
[4] main 끝
```

**왜 그런가**

```text
   [1] Noisy a(1); Noisy b = a;              ctor(1) → copy(1)   a.id=1  b.id=1
   [2] Noisy c(2); Noisy d = std::move(c);   ctor(2) → move(2)   c.id=-1 d.id=2
   [3] Noisy e(3); (void)std::move(e);       ctor(3) → (끝)      ★ e.id=3
```

- ★★★ **`[3]` 에서 아무 일도 안 일어났다.** `std::move` 를 불렀는데 **그 결과를 아무 데도 안 썼기** 때문이다.\
  **`std::move` 는 옮기지 않는다 — 옮길 수 있게 만들 뿐이다.**
- ★★ `[2]` 의 `c.id = -1` 은 **이 클래스의 이동 생성자가 직접 쓴 값**이다.\
  **표준이 정한 값이 아니다** — 표준 타입의 사정은 4번에서 따로 본다.
- ★ `[2]` 의 마지막 두 줄이 **`dtor(2)` 먼저, `dtor(-1)` 나중**이다.\
  **선언의 역순**으로 죽으니 `d`(id 2)가 먼저다.

### 4. ★★ `unique_ptr` 만 보장이다 — 나머지는 관찰이다

**출력**

```text
===== 소스: mvsem04.cpp =====
// 이동 후 원본은 어떤 상태인가 — 세 타입을 갈라 찍는다
#include <cstdio>
#include <memory>
#include <string>
#include <utility>
#include <vector>

int main() {
    std::string s1 = "hi";                                   // 짧다(SSO)
    std::string d1 = std::move(s1);
    std::printf("string 짧음 : 원본 size=%zu empty=%d 내용=\"%s\" | 대상=\"%s\"\n",
                s1.size(), static_cast<int>(s1.empty()), s1.c_str(), d1.c_str());

    std::string s2 = "0123456789012345678901234567890123456789";   // 길다(힙)
    std::string d2 = std::move(s2);
    std::printf("string 김   : 원본 size=%zu empty=%d 내용=\"%s\" | 대상 size=%zu\n",
                s2.size(), static_cast<int>(s2.empty()), s2.c_str(), d2.size());

    std::vector<int> v1{1, 2, 3};
    std::vector<int> v2 = std::move(v1);
    std::printf("vector      : 원본 size=%zu empty=%d capacity=%zu | 대상 size=%zu\n",
                v1.size(), static_cast<int>(v1.empty()), v1.capacity(), v2.size());

    std::unique_ptr<int> p1 = std::make_unique<int>(7);
    std::unique_ptr<int> p2 = std::move(p1);
    std::printf("unique_ptr  : 원본 null=%d | 대상 *p2=%d\n",
                static_cast<int>(p1 == nullptr), *p2);

    s1 = "다시 쓴다";                       // 이동 후에도 대입은 된다
    v1.push_back(9);
    std::printf("되살리기    : s1=\"%s\" v1.size=%zu v1[0]=%d\n",
                s1.c_str(), v1.size(), v1[0]);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic mvsem04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
string 짧음 : 원본 size=0 empty=1 내용="" | 대상="hi"
string 김   : 원본 size=0 empty=1 내용="" | 대상 size=40
vector      : 원본 size=0 empty=1 capacity=0 | 대상 size=3
unique_ptr  : 원본 null=1 | 대상 *p2=7
되살리기    : s1="다시 쓴다" v1.size=1 v1[0]=9
```

**왜 그런가**

| 타입 | 원본 | 표준이 뭐라 하나 |
|---|---|---|
| `std::string`(짧음) | `size=0` · `""` | ★★ **유효하지만 미명시** |
| `std::string`(김) | `size=0` | 〃 |
| `std::vector<int>` | `size=0` · `capacity=0` | 〃 |
| `std::unique_ptr<int>` | ★ **널** | ★★★ **표준이 정한다** |

- ★★★ **두 줄을 가려 읽어야 한다.** `unique_ptr` 이 널인 것은 **어느 구현에서나 참**이고,\
  `string`·`vector` 가 빈 것은 **libstdc++ 에서 관찰된 것**이다.\
  ★ 이 문서는 뒤엣것을 **흔들리는 칸**으로 선언했다.
- ★★ **짧은 문자열도 비워졌다.** 「SSO 라 이동이 복사와 같아서 원본이 남는다」는 흔한 짐작이 **이 판에서는 틀렸다.**\
  ★ 그래도 **미명시**라 다른 구현에서는 남아 있을 수 있다.
- ★★ **마지막 줄이 중요하다** — `s1 = "다시 쓴다";` 와 `v1.push_back(9);` 가 **정상으로 돈다.**\
  「유효하다」는 **전제 조건이 없는 연산은 쓸 수 있다**는 뜻이다. 전제가 있는 쪽은 9번에서 터진다.
- ★ 「이동 후 상태」가 **계약으로서** 무엇인지의 정본은 목록의 **17번 주제**다.

### 5. ★★★ `Safe` 는 복사 0 · 이동 7 — `Risky` 는 복사 3 · 이동 4

**출력**

```text
===== 소스: mvsem07.cpp =====
// 이동 생성자에 noexcept 가 없으면 vector 는 복사한다
#include <cstdio>
#include <type_traits>
#include <vector>

static int g_copy = 0, g_move = 0;

struct Safe {                                   // 이동이 noexcept
    int id;
    explicit Safe(int i) : id(i) {}
    Safe(const Safe& o) : id(o.id) { ++g_copy; }
    Safe(Safe&& o) noexcept : id(o.id) { ++g_move; }
};

struct Risky {                                  // 같은데 noexcept 만 없다
    int id;
    explicit Risky(int i) : id(i) {}
    Risky(const Risky& o) : id(o.id) { ++g_copy; }
    Risky(Risky&& o) : id(o.id) { ++g_move; }
};

template <class T>
void grow(const char* label) {
    g_copy = g_move = 0;
    std::vector<T> v;
    v.reserve(1);
    for (int i = 0; i < 4; ++i) v.push_back(T(i));
    std::printf("  %-6s nothrow_move=%d  ->  copy %d회 · move %d회  (size=%zu cap=%zu)\n",
                label, static_cast<int>(std::is_nothrow_move_constructible_v<T>),
                g_copy, g_move, v.size(), v.capacity());
}

int main() {
    std::puts("reserve(1) 뒤 push_back 을 네 번 — 재할당이 두 번 일어난다");
    grow<Safe>("Safe");
    grow<Risky>("Risky");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic mvsem07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
reserve(1) 뒤 push_back 을 네 번 — 재할당이 두 번 일어난다
  Safe   nothrow_move=1  ->  copy 0회 · move 7회  (size=4 cap=4)
  Risky  nothrow_move=0  ->  copy 3회 · move 4회  (size=4 cap=4)
```

**왜 그런가**

```text
   reserve(1) 뒤 push_back 4회 → 용량이 1 → 2 → 4 로 두 번 재할당된다

   Safe   noexcept 있음   재할당 이동 3 + 넣기 이동 4 = move 7 · copy 0
   Risky  noexcept 없음   재할당 ★복사 3 + 넣기 이동 4 = move 4 · copy 3
```

- ★★★ **두 클래스의 소스에서 다른 것은 `noexcept` 한 낱말뿐**이다.
- ★★★ **이유는 강한 예외 보장**이다 — 재할당 중에 이동이 예외를 던지면 **원본 원소가 이미 망가져** 되돌릴 수 없다.\
  그래서 `vector` 는 **이동이 던지지 않는다고 확인될 때만** 이동하고, 아니면 **복사한다**(복사는 원본을 안 건드린다).
- ★★ **`push_back` 이 원소를 넣는 4회는 양쪽 다 이동**이다 — 그 자리는 **새로 만드는 것**이라 보장이 걸리지 않는다.
- ★★ **`is_nothrow_move_constructible_v` 가 미리 답한다**(출력의 `nothrow_move` 칸: 1 과 0).\
  ★ `static_assert` 로 못 박아 두면 **컴파일 시간에** 잡는다.
- ★★★ **컴파일러는 한 줄도 경고하지 않는다.** 이 차이는 **세어야만** 보인다.
- ★ `noexcept` 의 계약으로서의 뜻은 목록의 **53번 주제**가 정본이다.\
  ★ 이 문서는 **횟수만 셌고 시간은 재지 않았다** — 「몇 배 느리다」는 적지 않는다.

### 6. ★★★ `[1]` 은 이동 · `[2]` 는 복사 — 경고는 0건

**출력**

```text
===== 소스: mvsem05.cpp =====
// const 객체를 move 하면 — 조용히 복사가 된다
#include <cstdio>
#include <string>
#include <utility>

struct Noisy {
    int id;
    explicit Noisy(int i) : id(i) { std::printf("    ctor(%d)\n", id); }
    Noisy(const Noisy& o) : id(o.id) { std::printf("    copy(%d)\n", id); }
    Noisy(Noisy&& o) noexcept : id(o.id) { std::printf("    move(%d)\n", id); o.id = -1; }
    ~Noisy() { std::printf("    dtor(%d)\n", id); }
};

int main() {
    std::puts("[1] Noisy a(1);       Noisy b = std::move(a);");
    { Noisy a(1); Noisy b = std::move(a); (void)b; }
    std::puts("[2] const Noisy c(2); Noisy d = std::move(c);   ★ const");
    { const Noisy c(2); Noisy d = std::move(c); (void)d; }

    std::puts("[3] std::string 으로 같은 일을");
    const std::string cs = "0123456789012345678901234567890123456789";
    std::string dst = std::move(cs);
    std::printf("    원본 size=%zu (이동이었다면 0 이거나 미명시) 대상 size=%zu\n",
                cs.size(), dst.size());
}
===== g++ -std=c++20 -Wall -Wextra -pedantic mvsem05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] Noisy a(1);       Noisy b = std::move(a);
    ctor(1)
    move(1)
    dtor(1)
    dtor(-1)
[2] const Noisy c(2); Noisy d = std::move(c);   ★ const
    ctor(2)
    copy(2)
    dtor(2)
    dtor(2)
[3] std::string 으로 같은 일을
    원본 size=40 (이동이었다면 0 이거나 미명시) 대상 size=40
```

**왜 그런가**

- ★★★ **`[2]` 에서 `copy(2)` 가 찍혔다.** 1번에서 본 대로 `std::move(c)` 의 타입이 **`const Noisy&&`** 이고,\
  이동 생성자(`Noisy&&`)는 **`const` 를 받을 수 없다** — 그래서 후보에서 빠지고\
  **복사 생성자(`const Noisy&`)가 유일한 후보**가 된다.\
  ★ 오버로드 표는 목록의 **08번 주제**에 있다(`f(std::move(ci))` 줄).
- ★★ **`[3]` 의 `cs.size()` 가 40 그대로**다 — 이동이었다면 libstdc++ 에서 0 이 됐을 것이다(4번).\
  **표준 타입에서도 똑같이 복사가 난다.**
- ★★★ **경고가 0건**이다.

```text
===== 소스: mvsem05.cpp =====
// const 객체를 move 하면 — 조용히 복사가 된다
#include <cstdio>
#include <string>
#include <utility>

struct Noisy {
    int id;
    explicit Noisy(int i) : id(i) { std::printf("    ctor(%d)\n", id); }
    Noisy(const Noisy& o) : id(o.id) { std::printf("    copy(%d)\n", id); }
    Noisy(Noisy&& o) noexcept : id(o.id) { std::printf("    move(%d)\n", id); o.id = -1; }
    ~Noisy() { std::printf("    dtor(%d)\n", id); }
};

int main() {
    std::puts("[1] Noisy a(1);       Noisy b = std::move(a);");
    { Noisy a(1); Noisy b = std::move(a); (void)b; }
    std::puts("[2] const Noisy c(2); Noisy d = std::move(c);   ★ const");
    { const Noisy c(2); Noisy d = std::move(c); (void)d; }

    std::puts("[3] std::string 으로 같은 일을");
    const std::string cs = "0123456789012345678901234567890123456789";
    std::string dst = std::move(cs);
    std::printf("    원본 size=%zu (이동이었다면 0 이거나 미명시) 대상 size=%zu\n",
                cs.size(), dst.size());
}
===== echo "g++   경고 $(g++ -std=c++20 -Wall -Wextra -pedantic mvsem05.cpp -o ex 2>&1 | grep -c 'warning:')"; echo "clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic mvsem05.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
g++   경고 0
clang 경고 0
```

- ★★ **g++ 도 clang 도 0** — 「경고 0건」이 **안전을 뜻하지 않는다**는 실측 사례다.
- ★ **세는 법**도 답에 들어간다 — `grep -c 'warning:'` 이 맞다.\
  `grep -c warning` 은 clang 의 요약 줄(`N warnings generated.`)까지 세어 **한 개 더** 나온다.

### 7. ★ 여섯 줄 — 네 번 불렀는데 인스턴스가 셋이다

**출력**

```text
===== 소스: mvsem06.cpp =====
// 전달 참조와 참조 축약 — T 와 T&& 가 각각 무엇으로 정해지나
#include <utility>

template <class T> struct TypeOf;

template <class T>
void probe(T&& x) {
    TypeOf<T> a;              // 추론된 T
    TypeOf<decltype(x)> b;    // 축약된 매개변수 타입
    (void)x;
}

int main() {
    int i = 0;
    const int ci = 0;
    probe(i);              // lvalue
    probe(ci);             // const lvalue
    probe(42);             // prvalue
    probe(std::move(i));   // xvalue
}
===== g++ -std=c++20 -Wall -Wextra -pedantic mvsem06.cpp -o ex 2>&1 | grep 'incomplete type' (cc exit=1) =====
mvsem06.cpp:8:15: error: ‘TypeOf<int&> a’ has incomplete type
mvsem06.cpp:9:25: error: ‘TypeOf<int&> b’ has incomplete type
mvsem06.cpp:8:15: error: ‘TypeOf<const int&> a’ has incomplete type
mvsem06.cpp:9:25: error: ‘TypeOf<const int&> b’ has incomplete type
mvsem06.cpp:8:15: error: ‘TypeOf<int> a’ has incomplete type
mvsem06.cpp:9:25: error: ‘TypeOf<int&&> b’ has incomplete type
```

**왜 그런가**

| 부른 것 | 인자 범주 | 추론된 `T` | `T&&` 축약 결과 = `decltype(x)` |
|---|---|---|---|
| `probe(i)` | lvalue | `int&` | `int& &&` → **`int&`** |
| `probe(ci)` | const lvalue | `const int&` | **`const int&`** |
| `probe(42)` | prvalue | `int` | **`int&&`** |
| `probe(std::move(i))` | xvalue | `int` | **`int&&`** |

- ★★★ **에러가 여섯 줄이다** — 네 번 불렀는데.\
  `probe(42)` 와 `probe(std::move(i))` 가 **둘 다 `T = int`** 라 **같은 인스턴스**이고,\
  컴파일러는 그 인스턴스를 **한 번만** 보고한다. ★ **줄 수 자체가 추론 결과의 증거**다.
- ★★ **참조 축약** — `&` 가 하나라도 있으면 `&`, 둘 다 `&&` 일 때만 `&&`.\
  그래서 lvalue 를 넘기면 매개변수가 **`int&`** 가 되어 **lvalue 를 받는다.**
- ★★★ **함수 안에서 `x` 는 언제나 lvalue** 다 — **이름이 있으니까.**\
  그래서 그대로 넘기면 **전부 복사**가 된다. 원래 범주를 되살리려면 **`std::forward<T>(x)`** 가 필요하다.\
  ★ 여기서 `std::move(x)` 를 쓰면 **lvalue 로 받은 것까지 훔쳐 간다** — 두 함수가 갈리는 자리다.

### 8. ★★ 경고 셋(이름 둘) · `cc exit=0` · `[1]` 만 생성자 하나

**출력**

```text
===== 소스: mvsem08.cpp =====
// return std::move(지역) 은 무엇을 막는가
#include <cstdio>
#include <utility>

struct Noisy {
    int id;
    explicit Noisy(int i) : id(i) { std::printf("    ctor(%d)\n", id); }
    Noisy(const Noisy& o) : id(o.id) { std::printf("    copy(%d)\n", id); }
    Noisy(Noisy&& o) noexcept : id(o.id) { std::printf("    move(%d)\n", id); }
    ~Noisy() { std::printf("    dtor(%d)\n", id); }
};

Noisy by_nrvo()   { Noisy n(1); return n; }                  // 그냥 돌려준다
Noisy by_move()   { Noisy n(2); return std::move(n); }       // ★ 이동을 강요한다
Noisy by_pessim() { return std::move(Noisy(3)); }            // ★ 임시에 move
Noisy by_param(Noisy n) { return std::move(n); }              // ★ 매개변수는 다르다

int main() {
    std::puts("[1] return n;                 (NRVO 가 가능하다)");
    { Noisy a = by_nrvo(); (void)a; }
    std::puts("[2] return std::move(n);");
    { Noisy b = by_move(); (void)b; }
    std::puts("[3] return std::move(Noisy(3));");
    { Noisy c = by_pessim(); (void)c; }
    std::puts("[4] Noisy by_param(Noisy n) { return std::move(n); }");
    { Noisy d = by_param(Noisy(4)); (void)d; }
}
===== g++ -std=c++20 -Wall -Wextra -pedantic mvsem08.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
mvsem08.cpp: In function ‘Noisy by_move()’:
mvsem08.cpp:14:49: warning: moving a local object in a return statement prevents copy elision [-Wpessimizing-move]
   14 | Noisy by_move()   { Noisy n(2); return std::move(n); }       // ★ 이동을 강요한다
      |                                        ~~~~~~~~~^~~
mvsem08.cpp:14:49: note: remove ‘std::move’ call
mvsem08.cpp: In function ‘Noisy by_pessim()’:
mvsem08.cpp:15:37: warning: moving a temporary object prevents copy elision [-Wpessimizing-move]
   15 | Noisy by_pessim() { return std::move(Noisy(3)); }            // ★ 임시에 move
      |                            ~~~~~~~~~^~~~~~~~~~
mvsem08.cpp:15:37: note: remove ‘std::move’ call
mvsem08.cpp: In function ‘Noisy by_param(Noisy)’:
mvsem08.cpp:16:43: warning: redundant move in return statement [-Wredundant-move]
   16 | Noisy by_param(Noisy n) { return std::move(n); }              // ★ 매개변수는 다르다
      |                                  ~~~~~~~~~^~~
mvsem08.cpp:16:43: note: remove ‘std::move’ call
[1] return n;                 (NRVO 가 가능하다)
    ctor(1)
    dtor(1)
[2] return std::move(n);
    ctor(2)
    move(2)
    dtor(2)
    dtor(2)
[3] return std::move(Noisy(3));
    ctor(3)
    move(3)
    dtor(3)
    dtor(3)
[4] Noisy by_param(Noisy n) { return std::move(n); }
    ctor(4)
    move(4)
    dtor(4)
    dtor(4)
```

**왜 그런가**

```text
   [1] return n;                     ctor(1)                    ★ 복사도 이동도 없다 (NRVO)
   [2] return std::move(n);          ctor(2) move(2)            이동 한 번이 더 난다
   [3] return std::move(Noisy(3));   ctor(3) move(3)            〃
   [4] Noisy by_param(Noisy n)       ctor(4) move(4)            매개변수는 NRVO 대상이 아니다
       { return std::move(n); }
```

- ★★★ **`[1]` 이 생성자 하나로 끝난다** — 컴파일러가 `n` 을 **반환 자리에 직접** 만든다(NRVO).\
  `std::move` 를 붙이면 **반환식이 더 이상 「이름」이 아니게 되어** 그 길이 막힌다.
- ★★ **경고 이름이 둘로 갈린다** — `[2]`·`[3]` 은 `-Wpessimizing-move`(비관적), `[4]` 는 `-Wredundant-move`(군더더기).\
  ★ `[4]` 의 매개변수는 **애초에 NRVO 대상이 아니라** 막을 것이 없다.\
  대신 **C++11 부터 반환문의 지역·매개변수는 자동으로 먼저 rvalue 로 해석**되므로 `std::move` 가 **군더더기**다.
- ★★ **`cc exit=0`** — 경고일 뿐이고 프로그램은 돈다. ★ **경고만 세고 exit 을 안 보면 「통과」로 기록된다.**

clang 도 **같은 이름 셋**을 낸다.

```text
===== 소스: mvsem08.cpp =====
// return std::move(지역) 은 무엇을 막는가
#include <cstdio>
#include <utility>

struct Noisy {
    int id;
    explicit Noisy(int i) : id(i) { std::printf("    ctor(%d)\n", id); }
    Noisy(const Noisy& o) : id(o.id) { std::printf("    copy(%d)\n", id); }
    Noisy(Noisy&& o) noexcept : id(o.id) { std::printf("    move(%d)\n", id); }
    ~Noisy() { std::printf("    dtor(%d)\n", id); }
};

Noisy by_nrvo()   { Noisy n(1); return n; }                  // 그냥 돌려준다
Noisy by_move()   { Noisy n(2); return std::move(n); }       // ★ 이동을 강요한다
Noisy by_pessim() { return std::move(Noisy(3)); }            // ★ 임시에 move
Noisy by_param(Noisy n) { return std::move(n); }              // ★ 매개변수는 다르다

int main() {
    std::puts("[1] return n;                 (NRVO 가 가능하다)");
    { Noisy a = by_nrvo(); (void)a; }
    std::puts("[2] return std::move(n);");
    { Noisy b = by_move(); (void)b; }
    std::puts("[3] return std::move(Noisy(3));");
    { Noisy c = by_pessim(); (void)c; }
    std::puts("[4] Noisy by_param(Noisy n) { return std::move(n); }");
    { Noisy d = by_param(Noisy(4)); (void)d; }
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic mvsem08.cpp -o ex 2>&1 | grep -E 'warning:|generated' (cc exit=0) =====
mvsem08.cpp:14:40: warning: moving a local object in a return statement prevents copy elision [-Wpessimizing-move]
mvsem08.cpp:15:28: warning: moving a temporary object prevents copy elision [-Wpessimizing-move]
mvsem08.cpp:16:34: warning: redundant move in return statement [-Wredundant-move]
3 warnings generated.
```

- ★ **열 번호만 다르다**(g++ 49/37/43 · clang 40/28/34) — 흔들리는 칸이다.

### 9. ★★ `size()` 는 적법 · `front()` 는 UB — 그런데 컴파일러는 조용하다

**출력** — 먼저 경고를 센다.

```text
===== 소스: mvsem10.cpp =====
// 이동 후 원본에 「전제 조건이 있는 연산」을 부르면 — 유효하지만 비어 있는 것이 문제다
#include <cstdio>
#include <vector>
#include <utility>

int main() {
    std::vector<int> v1{1, 2, 3};
    std::vector<int> v2 = std::move(v1);

    std::fprintf(stderr, "[마커] v1.size()=%zu  v1.empty()=%d  — 여기까지는 적법하다\n",
                 v1.size(), static_cast<int>(v1.empty()));
    std::fprintf(stderr, "[마커] 이제 v1.front() 를 부른다\n");
    int x = v1.front();                 // ★ 빈 컨테이너의 front() 는 UB
    std::fprintf(stderr, "[마커] v1.front()=%d\n", x);
    (void)v2;
}
===== echo "g++   경고 $(g++ -std=c++20 -Wall -Wextra -pedantic mvsem10.cpp -o ex 2>&1 | grep -c 'warning:')"; echo "clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic mvsem10.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
g++   경고 0
clang 경고 0
```

**그다음 ASan.**

```text
===== 소스: mvsem10.cpp =====
// 이동 후 원본에 「전제 조건이 있는 연산」을 부르면 — 유효하지만 비어 있는 것이 문제다
#include <cstdio>
#include <vector>
#include <utility>

int main() {
    std::vector<int> v1{1, 2, 3};
    std::vector<int> v2 = std::move(v1);

    std::fprintf(stderr, "[마커] v1.size()=%zu  v1.empty()=%d  — 여기까지는 적법하다\n",
                 v1.size(), static_cast<int>(v1.empty()));
    std::fprintf(stderr, "[마커] 이제 v1.front() 를 부른다\n");
    int x = v1.front();                 // ★ 빈 컨테이너의 front() 는 UB
    std::fprintf(stderr, "[마커] v1.front()=%d\n", x);
    (void)v2;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 -g -ffile-prefix-map="$PWD"=. -fsanitize=address mvsem10.cpp -o ex && ./ex 2>&1 | grep -E '\[마커\]|ERROR: AddressSanitizer|DEADLYSIGNAL|The signal is caused|Hint:|#0 |SUMMARY' (cc exit=0 · run exit=1) =====
[마커] v1.size()=0  v1.empty()=1  — 여기까지는 적법하다
[마커] 이제 v1.front() 를 부른다
AddressSanitizer:DEADLYSIGNAL
==1021616==ERROR: AddressSanitizer: SEGV on unknown address 0x000000000000 (pc 0x5e0b3b0a0730 bp 0x7fff178f3730 sp 0x7fff178f35e0 T0)
==1021616==The signal is caused by a READ memory access.
==1021616==Hint: address points to the zero page.
    #0 0x5e0b3b0a0730 in main mvsem10.cpp:13
SUMMARY: AddressSanitizer: SEGV mvsem10.cpp:13 in main
```

**왜 그런가**

- ★★★ **`size()`·`empty()` 는 전제 조건이 없다** — 이동 후에도 **적법**하다. 마커 두 줄이 그것을 보인다.
- ★★★ **`front()` 는 전제 조건이 있다**(비어 있으면 안 된다). 이동 후 벡터는 **유효하지만 비어 있어서** 그 전제를 어긴다.\
  이 판에서는 **널 주소 읽기(SEGV)** 로 죽었다.
- ★★★ **g++·clang 둘 다 경고 0건**이다. **ASan 만 잡았다.**
- ★★ **근거로 쓰는 것은 「죽는 방식」이 아니다** — `run exit=1` 은 ASan 이 정한 값이고,\
  UB 는 **아무 일이나 해도 된다.** 근거는 「**전제 조건이 있는 연산을 어겼다**」이다.
- ★ **마커를 표준 오류로 찍은 이유** — sanitizer 가 `abort()` 하면 **버퍼에 남은 표준 출력이 통째로 사라진다.**\
  터미널에서는 보이는데 **파이프로 받으면 없어진다** — 그래서 마커는 처음부터 `stderr` 다.

### 10. ★ 통과한다 — 그런데 그것은 이 구현의 성질이다

**출력**

```text
===== 소스: mvsem09.cpp =====
// <utility> 를 안 넣고 std::move 를 쓴다 — 이 구현에서는 통과한다
#include <cstdio>
#include <string>

int main() {
    std::string a = "0123456789012345678901234567890123456789";
    std::string b = std::move(a);          // ★ <utility> 가 없다
    std::printf("a.size=%zu b.size=%zu\n", a.size(), b.size());
}
===== g++ -std=c++20 -Wall -Wextra -pedantic mvsem09.cpp -o ex; echo "cc exit=$?"; ./ex; clang++ -std=c++20 -Wall -Wextra -pedantic mvsem09.cpp -o ex; echo "cc exit=$?"; g++ -std=c++20 -E mvsem09.cpp | grep -c 'bits/move.h' (exit=0) =====
g++   cc exit=0
a.size=0 b.size=40
clang cc exit=0
bits/move.h 가 전처리 결과에 들어온 횟수: 6
```

**왜 그런가**

- ★★ **`<utility>` 가 없는데 `std::move` 가 쓰인다.** `<string>` 이 **`bits/move.h` 를 전이적으로** 끌어왔다\
  (전처리 결과에 **6번** 들어왔다).
- ★★★ **표준은 그 전이 포함을 보장하지 않는다.** 헤더가 무엇을 더 포함하는지는 **구현의 자유**다.
- ★★★ **두 컴파일러에서 통과한 것이 이식성의 근거가 못 된다** —\
  g++ 와 clang 이 이 머신에서 **같은 libstdc++ 헤더**를 쓰기 때문이다.\
  ★ **컴파일러 둘은 표준 라이브러리 둘이 아니다.**
- ★ **경고 0건 · `cc exit=0`** 이다. 이 갈래의 「**종료 코드가 0인데 이식되지 않는다**」 자리다.

### 11. 이 주제의 지도

**출력** — 없다(연결 문항).

**왜 그런가**

- 「어떤 식이 xvalue 인가」는 목록의 **08번 주제**가 정본이다.\
  ★ 09 는 **그 범주를 만드는 법**을 줄 뿐이고, 1번의 타입 표가 08 의 격자와 정확히 겹친다.
- 「이동 생성자를 어떻게 구현하나」와 「유효하되 미지정」이라는 계약은 목록의 **17번 주제**다.\
  ★ 여기서는 **부르는 쪽**만 봤다 — 4번의 표가 「계약이 무엇을 보장하나」의 실측이다.
- `noexcept` 가 **계약으로서** 무엇을 뜻하는지는 목록의 **53번 주제**다. 5번은 **`vector` 한 자리의 결과**만 봤다.
- 「그래서 매개변수를 무엇으로 받나」는 목록의 **11번 주제**다 — 08 → 09 → 11 사슬의 끝이다.
- ★★ **Rust 에서는 이동 후 원본을 쓰면 컴파일 에러다** — [`../../../rust/syntax/08-ownership-and-move/`](../../../rust/syntax/08-ownership-and-move/).\
  Rust 는 **이동이 기본**이고 **이동한 변수를 다시 쓰는 것을 타입 체계가 막는다**(`E0382`).\
  C++ 는 **기본이 복사**이고, 이동은 **캐스트로 요청**하며, 이동 후 원본을 쓰는 것은\
  **에러가 아니라 계약 문제**다(4번은 적법, 9번은 UB).\
  ★★ **같은 낱말이 한쪽은 타입 체계의 일이고 한쪽은 관용구의 일이다** — 그래서 C++ 에서는\
  **로그와 sanitizer 가 컴파일러를 대신한다.**

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 명령으로 돌렸나 |
|---|---|---|
| `mvsem01.cpp` 캐스트 | ★★ `move` = `static_cast` · ★★★ `const` 가 **남는다** | g++ |
| `mvsem02.cpp` 기계어 | ★★★ `-O0` 은 **`call` 이 남고** `-O2` 는 **셋이 같다** · `nm` 에서 심볼이 사라진다 | g++ `-O0 -c`·`-O2 -c` + `objdump`·`nm` |
| `mvsem03.cpp` 로그 | ★★★ `std::move` 만 하면 **아무 일도 안 난다** | g++ |
| `mvsem04.cpp` 이동 후 | `string`/`vector` **size 0**(★ 미명시) · `unique_ptr` **널**(보장) · **되살리기 된다** | g++ |
| `mvsem05.cpp` const | ★★★ `copy` 가 불린다 · **경고 0**(두 컴파일러) | g++ · clang |
| `mvsem06.cpp` 축약 | ★★ **에러 6줄**(호출 4회) · `T` 가 `int&`/`const int&`/`int` | g++ |
| `mvsem07.cpp` noexcept | ★★★ **Safe copy 0 move 7 · Risky copy 3 move 4** | g++ |
| `mvsem08.cpp` 반환 | ★★ 경고 **3**(이름 2종) · `cc exit=0` · `[1]` 만 ctor 하나 | g++ · clang |
| `mvsem09.cpp` 헤더 | ★ **경고 0 · `cc exit=0`** · `bits/move.h` **6회** | g++ · clang · `g++ -E` |
| `mvsem10.cpp` 이동 후 UB | ★★ **경고 0**(두 컴파일러) · ASan **SEGV** · `run exit=1` | g++ · clang · g++ `-fsanitize=address` |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · libstdc++ · binutils 2.42)에서만** 그렇다.

- ★★★ **이동 후 `std::string`·`std::vector` 의 상태**(`size=0`) — **미명시**다. 관찰일 뿐이다.
- ★★ **짧은 문자열(SSO)도 비워지는 것** — 같은 이유로 관찰이다.
- ★★ **`-O0` 에서 `std::move` 가 실제 호출로 남는 것**과 **`-O2` 에서 사라지는 것**.
- ★★ **`<utility>` 없이 컴파일되는 것**(10번) — **libstdc++ 헤더 구조**의 성질이다.
- 진단 문구·경고 이름·열 번호 · `__cxx11` 같은 **인라인 네임스페이스 이름** · 맹글링된 심볼.
- ASan 의 **PID·주소·`pc`/`bp`/`sp`** · **`run exit=1`** 이라는 값.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **`std::move(x)` 가 `static_cast<remove_reference_t<T>&&>(x)` 인 것**(1번).
- **`std::move` 가 `const` 를 떼지 않는 것** — 그래서 **`const` 객체는 복사된다**(6번).
- **참조 축약**과 **전달 참조에서의 `T` 추론**(7번) · **`T&&` 로 선언된 이름이 lvalue 인 것**.
- **`unique_ptr` 이 이동 후 널이 되는 것**(4번).
- **표준 컨테이너가 이동 후 「유효하지만 미명시」인 것** — ★ **「유효하다」쪽은 보장**이다(4번의 마지막 줄).
- **`vector` 재할당이 이동이 `noexcept` 가 아니면 복사로 가는 것**(5번) — 강한 예외 보장에서 나온다.
- **`return std::move(지역)` 이 NRVO 를 막는 것**(8번) · **C++11 부터 반환문의 지역이 자동으로 rvalue 로 해석되는 것**.
- **전제 조건이 있는 연산을 이동 후 원본에 부르는 것이 UB 인 것**(9번).

**UB 의 결과라 보장이 아닌 것**(관찰로만 읽는다)

- ★ 9번의 **`SEGV` 와 `run exit=1`** — **이 판의 결과**다.\
  근거로 쓰는 것은 「**ASan 이 그 줄을 짚었다**」와 「**컴파일러는 0건이었다**」다.
- ★ 이 문서는 **UB 가 만든 값**(`v1.front()` 의 결과)을 **싣지 않았다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **`std::move_if_noexcept`** · **`std::exchange`** ·
  **`const` 를 돌려주는 함수**(`const Widget f();`) · **가변 인자 팩의 `forward`**(목록의 **34번 주제**) ·
  **람다 초기화 캡처 `[p = std::move(p)]`**(목록의 **39번 주제**) ·
  **`std::forward` 를 잘못 써서 두 번 이동하는 것** ·
  **C++11\~14 판에서의 동작**(여기는 `-std=c++20` 한 판이다) ·
  **libc++ 에서의 이동 후 상태**(★ 4번의 미명시 칸을 가를 수 있는 유일한 실험인데 **이 머신에 libc++ 가 없다**) ·
  **`-O1`·`-O3` 의 기계어**(2번은 `-O0`·`-O2` 두 수준만 던졌다).
- **못 잰 것** — ★★ **「이동이 복사보다 몇 배 빠른가」**.\
  이 문서가 센 것은 **횟수**뿐이고, 시간을 재려면 **벤치마크 하네스가 따로** 필요하다.\
  그때도 답은 **타입의 크기와 할당 패턴에 달린** 것이라 **한 숫자로 안 나온다.**\
  ★ 그래서 이 문서는 **수치를 적지 않았다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **이동 후 `string`·`vector` 의 상태**(4번) — **미명시**라 **표준 라이브러리가 바뀌면 가장 먼저 움직인다.**
- ★ **`Risky` 의 복사 3회**(5번) — `vector` 의 성장 계수가 바뀌면 숫자가 바뀐다.
- ★ **`-O0` 에서 `std::move` 가 호출로 남는지**(2번).
- ★ **`<utility>` 없이 계속 컴파일되는지**(10번) — 헤더 구조가 정리되면 깨진다.
- 경고 이름 셋(`-Wpessimizing-move`·`-Wredundant-move`)과 **경고 0건인 자리 넷**(5·6·9번).
