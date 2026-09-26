# cpp/syntax/09 — rvalue 참조·`std::move`·`std::forward` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — `std::move`](https://en.cppreference.com/w/cpp/utility/move) · [`std::forward`](https://en.cppreference.com/w/cpp/utility/forward) · [참조 선언과 참조 축약](https://en.cppreference.com/w/cpp/language/reference) · [`std::move_if_noexcept`](https://en.cppreference.com/w/cpp/utility/move_if_noexcept) · [`std::vector::push_back`](https://en.cppreference.com/w/cpp/container/vector/push_back) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html)
> **실행 검증** — 이 문서의 모든 출력·진단·기계어는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **GNU objdump/nm 2.42** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`mvsem01.cpp` \~ `mvsem10.cpp`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 긴 출력은 **거르는 명령을 배너에 적어 두었다.** 실린 것은 「생략한 일부」가 아니라 **그 명령의 전체 출력**이다.\
> ★★ ASan 블록의 마커는 **표준 오류**로 찍었다 — sanitizer 가 죽이면 **버퍼에 남은 표준 출력이 통째로 사라지기** 때문이다.
> **버전** — rvalue 참조(`T&&`)·`std::move`·`std::forward`·참조 축약은 전부 **C++11부터**다.\
> `-Wpessimizing-move`·`-Wredundant-move` 는 **컴파일러의 것**이지 표준이 아니다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> **경계** — 「어떤 식이 xvalue 인가」의 정본은 [목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/)다 — 여기서는 **그 범주를 만드는 법**부터 쓴다.\
> 「이동 생성자를 어떻게 구현하나」와 「이동 후 상태라는 계약」의 정본은 [목록의 **17번 주제**](../17-move-constructor-assignment-and-moved-from-state/),\
> 「`noexcept` 가 무엇을 계약하나」는 목록의 **53번 주제**, 「그래서 매개변수를 무엇으로 받나」는 [목록의 **11번 주제**](../11-choosing-parameter-passing/),\
> 「가변 인자 템플릿에서의 완벽 전달」은 목록의 **34번 주제**, 「참조가 무엇인가」는 형제 [`07번`](../07-references-vs-pointers/)이 정본이다.\
> 여기는 **`std::move`·`std::forward` 라는 두 함수가 실제로 무엇을 하나**까지다.
> ★★★ **08 → 09 → 11 은 한 사슬이다** — 08 이 **범주**를 정하고, 여기가 **그 범주를 만드는 법**을 주고,\
> 11 이 **그래서 무엇으로 받을지**를 고른다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 기계어 덤프의 **주소·오프셋**(`0:` · `17:`) | ★ **명령어 열 자체**(`mov %rdi,%rax` · `call` 이 있나 없나) |
> | ASan 리포트의 **PID·주소·`pc`/`bp`/`sp`** | **`SEGV` 라는 종류** · `mvsem10.cpp:13` · **`run exit`** |
> | 진단 문구 · 두 컴파일러의 **열 번호** | **경고 이름**(`-Wpessimizing-move` · `-Wredundant-move`) |
> | ★ **이동 후 `std::string`·`vector` 의 상태** — ★★ **미명시**다 | ★ **생성자·소멸자 호출 횟수**(`copy 3 · move 4`) · `unique_ptr` 이 **널**인 것 |

## 한눈에 — 쉽게 말하면

**`std::move` 는 짐을 옮기는 사람이 아니라, 짐에 「가져가도 됩니다」라고 써 붙이는 쪽지다.**

쪽지를 붙였다고 짐이 움직이지 않는다.\
**누군가 그 쪽지를 보고 가져갈 때** 비로소 짐이 움직인다.

| 비유 | 실체 |
|---|---|
| **짐에 쪽지를 붙인다** | `std::move(x)` — ★ `static_cast<T&&>(x)` 일 뿐이다 |
| ★★ **쪽지만 붙이고 아무도 안 가져가면** | 아무 일도 안 일어난다((3)의 `[3]`) |
| **쪽지를 보고 가져가는 사람** | **이동 생성자·이동 대입** |
| ★★ **「가져가지 마세요」 도장(`const`)이 찍혀 있으면** | 쪽지를 붙여도 **복사해 간다**((5)) — 조용히 |
| ★★ **짐을 가져간 뒤 남은 빈 상자** | 이동 후 원본 — **유효하지만 내용은 미명시**((4)) |
| ★ **「누가 줬는지에 따라 다르게 취급해 주세요」** | `std::forward<T>(x)` — 전달 참조에서만 뜻이 있다((6)) |

```text
   Noisy a(1);
   Noisy b = a;                복사 생성자     a 는 그대로

   Noisy c(2);
   Noisy d = std::move(c);     이동 생성자     c 의 내장이 d 로

   Noisy e(3);
   (void)std::move(e);         ★ 아무 일도 안 일어난다
                               쪽지만 붙었고 가져간 사람이 없다


   std::move 가 하는 일 전부:

       template <class T>
       constexpr remove_reference_t<T>&& move(T&& t) noexcept
       { return static_cast<remove_reference_t<T>&&>(t); }

       └─ 캐스트 한 줄. 런타임에 남는 코드는 -O2 에서 0 이다 ((2))
```

> **rvalue 참조(rvalue reference, `T&&`)** — rvalue 에만 묶이는 참조. **C++11부터.**\
> 예: `int&& r = 42;` 는 되고 `int&& r = i;` 는 안 된다([목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/)의 격자).

> **이동(move)** — 새 객체를 만들면서 **원본의 내장(힙 포인터 등)을 가져가는 것**.\
> 예: `std::string` 의 이동은 **문자 40개를 복사하지 않고 포인터 하나를 옮긴다**((4)).

## 이 주제가 답하려는 질문

1. **`std::move` 는 무엇을 하나** — 진짜로 무엇을 옮기나((1)(2)(3)).
2. **이동한 뒤 원본은 어떤 상태인가** — 표준이 무엇을 보장하나((4)).
3. **왜 `forward` 가 따로 있나** — `move` 로는 왜 안 되나((6)).

## 동작 방식

### (0) 이 주제가 쓰는 네 창

```text
① decltype + 정의 없는 템플릿     std::move 가 무슨 타입을 돌려주나        (1)(6)
② objdump / nm                    그 캐스트가 기계어를 몇 줄 만드나        (2)
③ 복사·이동 생성자 로그           ★ 실제로 무엇이 불렸나                   (3)(5)(7)(8)
④ ASan + 표준 오류 마커           이동 후 원본을 잘못 쓰면 어디서 터지나   (9)
```

- ★★★ **이 주제의 근거는 ③이다.** 「이동이 일어났다」를 **말로 적을 수 없다** — **로그로 센다.**
- ★ ②는 「`std::move` 가 캐스트일 뿐」을 **코드 생성 쪽에서** 확인하는 창이다.

### (1) `std::move` 는 캐스트다 — 타입으로 확인

**언제 쓰나** — 「`move` 가 뭘 하는 함수지?」가 떠오를 때. 답은 **타입에 다 적혀 있다.**

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

- ★★★ **`m1`(`std::move(i)`)과 `m2`(`static_cast<int&&>(i)`)가 같은 `int&&`** 다.\
  소스의 `static_assert` 도 통과했다(통과했기에 에러 목록에 없다).
- ★★★ **`m3` 이 `const int&&`** — **`std::move` 는 `const` 를 떼지 않는다.**\
  이 한 줄이 (5)의 「조용한 복사」를 통째로 설명한다.
- ★ **`m5`(두 번 건 것)도 `int&&`** — 멱등이다. 두 번 써도 달라지는 게 없다.

**비용** — 타입만 바뀐다. 실행되는 코드는 (2)에서 센다.

### (2) ★★★ 기계어 — `-O0` 에서는 함수 호출이 남고 `-O2` 에서는 사라진다

**언제 쓰나** — 「`move` 가 공짜인가」가 궁금할 때. **한 수준만 보고 단정하지 않는다.**

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

- ★★ **`via_move` 안에 `call` 이 있다.** `-O0` 에서는 `std::move` 가 **진짜 함수 호출**로 남는다.
- ★★ 그 호출되는 함수(`_ZSt4move…`)의 몸통은 **인자를 받아 그대로 반환 레지스터에 옮기는 것뿐**이다\
  (`-O0` 이라 스택을 한 번 거친다: `mov %rdi,-0x8(%rbp)` → `mov -0x8(%rbp),%rax`).
- ★ `via_cast` 와 `no_cast` 에는 `call` 이 **없다.**

**`-O2` 에서는 셋이 같아진다.**

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

- ★★★ **세 함수가 `endbr64 / mov %rdi,%rax / ret` 로 한 글자도 다르지 않다.**\
  「`std::move` 는 런타임 비용이 0」이 **이 수준에서** 참이다.
- ★★ **그런데 `-O0` 에서는 참이 아니다** — 「공짜다」를 적을 때 **어느 수준인지 같이** 적어야 하는 이유다.

심볼 목록이 그 차이를 한 번 더 보여 준다.

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

- ★★ **`-O0` 에는 `std::move<int&>(int&)` 라는 약한 심볼이 실제로 있고, `-O2` 에는 없다.**
- ★ 「인라인될 것이다」가 아니라 「**목록에서 사라졌다**」가 근거다.

**비용** — `-O2` 기준 **0**. `-O0` 에서는 **호출 한 번**. ★ 그 이상은 이 문서가 **재지 않았다.**

### (3) 그래서 무엇이 일어나나 — 로그로 센다

**언제 쓰나** — 「여기서 복사가 나나 이동이 나나」가 걸릴 때. **읽지 말고 센다.**

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

```text
   [1] Noisy b = a;              ctor(1) copy(1)        a.id 는 1 그대로
   [2] Noisy d = std::move(c);   ctor(2) move(2)        c.id 가 -1 로 바뀐다
   [3] (void)std::move(e);       ctor(3) …그리고 끝     ★ 아무 일도 안 났다
```

- ★★★ **`[3]` 이 이 주제의 핵심**이다. `std::move` 를 부르고 **그 결과를 아무 데도 안 쓰면** 원본은 **그대로**다(`e.id=3`).\
  **`std::move` 는 옮기지 않는다** — **옮길 수 있게 만들 뿐**이다.
- ★★ `[2]` 에서 `c.id` 가 **-1** 인 것은 **이 클래스의 이동 생성자가 그렇게 쓴 것**이다 —\
  **표준이 정한 값이 아니다.** 표준 타입의 사정은 (4)에서 따로 본다.
- ★ 소멸 순서가 `dtor(2) dtor(-1)` 인 것은 **선언의 역순**이라서다.

**비용** — 이동 생성자가 하는 일에 달렸다. `Noisy` 는 `int` 하나라 **복사와 이동의 비용이 사실상 같다.**\
★ **「이동이 항상 싸다」가 아니다** — 싸지는 것은 **힙을 들고 있는 타입**이다((4)).

### (4) 이동 후 원본 — 「유효하지만 미명시」

**언제 쓰나** — 이동한 변수를 **다시 쓰는** 코드를 읽을 때.

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

| 타입 | 이동 후 원본 | 표준이 뭐라 하나 |
|---|---|---|
| `std::string`(짧음·SSO) | `size=0` · 빈 문자열 | ★★ **유효하지만 미명시** |
| `std::string`(김·힙) | `size=0` | 〃 |
| `std::vector<int>` | `size=0` · `capacity=0` | 〃 |
| `std::unique_ptr<int>` | ★ **널** | ★★★ **표준이 「널이 된다」고 정한다** |

- ★★★ **두 줄을 가려 읽어야 한다** — `unique_ptr` 이 널인 것은 **보장**이고,\
  `string`·`vector` 가 비는 것은 **이 구현에서 관찰된 것**이다.
- ★★ **짧은 문자열(SSO)도 비워졌다.** 「짧으면 이동이 복사와 같아서 원본이 남는다」는 흔한 짐작이 **이 판에서는 틀렸다** —\
  ★ 그래도 **미명시**라 다른 구현에서 남아 있을 수 있다. **근거로 쓰지 않는다.**
- ★★ **마지막 줄이 중요하다** — 이동한 뒤에도 **대입과 `push_back` 은 된다.**\
  「유효하다」는 **전제 조건이 없는 연산은 쓸 수 있다**는 뜻이고, 전제가 있는 것은 (9)에서 터진다.

**비용** — 긴 문자열 40자가 **한 번도 복사되지 않는다.** 이동이 싸지는 것이 여기다.

### (5) ★★ `const` 객체를 `move` 하면 — 조용히 복사가 된다

**언제 쓰나** — `const` 멤버·`const` 지역을 이동하려는 코드를 볼 때마다.

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

```text
   [1] Noisy a(1);        Noisy b = std::move(a);    -> move(1)   이동
   [2] const Noisy c(2);  Noisy d = std::move(c);    -> copy(2)   ★ 복사
   [3] const std::string cs(40자);  std::string dst = std::move(cs);
                          -> cs.size() 가 40 그대로  ★ 복사됐다
```

- ★★★ **`const` 한 낱말이 `move` 를 `copy` 로 바꾼다.** (1)에서 본 대로 `std::move(c)` 의 타입은 **`const Noisy&&`** 이고,\
  이동 생성자(`Noisy&&`)는 그것을 못 받는다 — 그래서 **`const Noisy&`(복사 생성자)로 떨어진다**([목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/)의 오버로드 표 마지막 줄).
- ★★★ **경고가 한 줄도 없다.**

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

- ★★ **두 컴파일러 다 0 건**이다. 「경고 0」이 **안전하다는 뜻이 아니라는** 실측 사례다.\
  ★ 세는 법도 적는다 — `grep -c 'warning:'` 이다(`grep -c warning` 은 clang 의 요약 줄까지 센다).
- ★ 잡는 법은 **로그이거나**(위 블록) **`static_assert`** 다. 컴파일러는 안 말해 준다.

### (6) 전달 참조와 참조 축약 — `T` 가 무엇으로 정해지나

**언제 쓰나** — 템플릿에서 `T&&` 를 볼 때. **`T&&` 가 늘 rvalue 참조인 것이 아니다.**

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

| 부른 것 | 인자 범주 | 추론된 `T` | `T&&` 를 축약하면 | 무엇으로 전달해야 하나 |
|---|---|---|---|---|
| `probe(i)` | lvalue | `int&` | `int& &&` → **`int&`** | `std::forward<T>` = lvalue |
| `probe(ci)` | const lvalue | `const int&` | `const int&` | 〃 |
| `probe(42)` | prvalue | `int` | `int&&` | `std::forward<T>` = rvalue |
| `probe(std::move(i))` | xvalue | `int` | `int&&` | 〃 |

> **전달 참조(forwarding reference)** — **템플릿 매개변수 `T` 에 대해** 쓴 `T&&`.\
> **추론되는 자리에서만** 그렇다 — `std::vector<T>&&` 나 구체 타입의 `Noisy&&` 는 전달 참조가 **아니다.**\
> 예: `template <class T> void f(T&& x)` 의 `x` 는 lvalue 도 받는다.

> **참조 축약(reference collapsing)** — 참조의 참조가 생기면 한 겹으로 접는 규칙.\
> **`&` 가 하나라도 있으면 `&`**, 둘 다 `&&` 일 때만 `&&`.\
> 예: `int& &&` → `int&` (위 표 첫 줄).

- ★★★ **에러가 여섯 줄뿐이다** — 네 번 불렀는데. `probe(42)` 와 `probe(std::move(i))` 는 **`T = int` 로 같은 인스턴스**라\
  컴파일러가 **한 번만** 보고한다. ★ 「네 줄일 줄 알았는데 여섯 줄」이 그 자체로 **추론 결과의 증거**다.
- ★★★ **`x` 는 언제나 lvalue 다** — 이름이 있으니까. 그래서 **`forward` 를 한 번 더** 써야 한다.\
  ★ 여기서 `std::move` 를 쓰면 **lvalue 로 받은 것까지 훔쳐 간다** — 그것이 `move` 와 `forward` 가 갈리는 자리다.

**비용** — `forward` 도 `move` 와 같은 캐스트다. **런타임 비용은 (2)와 같다.**

### (7) ★★ 이동에 `noexcept` 가 없으면 — `vector` 가 복사한다

**언제 쓰나** — 이동 생성자를 직접 쓸 때. **한 낱말이 수백 번의 복사를 만든다.**

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

```text
   같은 클래스, 다른 것은 noexcept 한 낱말뿐

   Safe   nothrow_move=1  ->  copy 0회 · move 7회
   Risky  nothrow_move=0  ->  copy 3회 · move 4회      ★ 복사 3회가 재할당에서 났다
```

- ★★★ **`Risky` 의 복사 3회는 전부 재할당 때 「기존 원소를 새 버퍼로 옮기는」 자리**다.\
  `push_back` 이 원소를 넣는 4회는 양쪽 다 이동이다(move 4회).
- ★★★ **이유는 강한 예외 보장**이다 — 재할당 도중 이동이 예외를 던지면 **원본이 이미 망가져 되돌릴 수 없다.**\
  그래서 `vector` 는 **이동이 `noexcept` 임을 확인될 때만** 이동한다.
- ★★ **`is_nothrow_move_constructible_v` 가 그것을 미리 답한다** — 출력의 `nothrow_move` 칸.\
  ★ `static_assert` 로 못 박아 두면 실수로 `noexcept` 를 빼는 것을 **컴파일 시간에** 잡는다.
- ★ `noexcept` 가 **계약으로서** 무엇을 뜻하는지는 목록의 **53번 주제**가 정본이다. 여기서는 **이 한 자리의 결과**만 본다.

**비용** — `Risky` 는 원소가 많아질수록 **복사가 늘어난다.**\
★ 이 문서는 **횟수만 셌고 시간은 재지 않았다.** 「몇 배 느리다」는 적지 않는다.

### (8) `return std::move(지역)` — NRVO 를 막는다

**언제 쓰나** — 반환문에 `std::move` 를 붙이고 싶을 때마다.

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

```text
   [1] return n;                    ctor(1)                         ★ 복사도 이동도 없다
   [2] return std::move(n);         ctor(2) move(2)                 이동 한 번이 더 난다
   [3] return std::move(Noisy(3));  ctor(3) move(3)                 〃
   [4] Noisy by_param(Noisy n)      ctor(4) move(4)                 ★ 여긴 사정이 다르다
       { return std::move(n); }
```

- ★★★ **`[1]` 이 생성자 하나로 끝난다.** 반환할 지역을 **반환 자리에 바로 만든다**(NRVO).\
  `std::move` 를 붙이면 **그 길이 막히고** 이동이 한 번 는다.
- ★★ **경고 이름이 둘로 갈린다** — `[2]`·`[3]` 은 `-Wpessimizing-move`, `[4]` 는 `-Wredundant-move`.\
  ★ `[4]` 는 **매개변수**라 애초에 NRVO 대상이 아니다. 그래서 「비관적」이 아니라 「**군더더기**」다 —\
  C++11 부터 반환문의 지역·매개변수는 **자동으로 먼저 이동으로 해석**되기 때문이다.
- ★★ **`cc exit=0`** 이다. 경고일 뿐이고 **프로그램은 돈다.**

clang 도 **같은 경고 이름 셋**을 낸다(열 번호만 다르다).

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

**비용** — `[2]`\~`[4]` 는 이동 한 번. ★ `Noisy` 에서는 싸지만 **NRVO 가 되는 자리를 일부러 막은 것**이 요점이다.

### (9) 이동 후 원본을 잘못 쓰면 — 「유효」와 「무엇이든 해도 된다」는 다르다

**언제 쓰나** — (4)의 「유효하지만 미명시」를 실제로 시험할 때.

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

- ★★★ **`size()`·`empty()` 는 적법하다** — 전제 조건이 없다. 그래서 마커 두 줄이 정상으로 찍힌다.
- ★★★ **`front()` 는 UB 다** — 빈 컨테이너에 전제 조건을 어겼고, 이 판에서는 **널 주소 읽기(SEGV)** 로 죽었다.
- ★★ **컴파일러는 경고 0 건**이다(g++·clang 둘 다). **ASan 만 잡았다.**
- ★ **`run exit=1`** 은 ASan 이 정한 종료 코드다 — **UB 가 「SEGV 로 죽는다」는 보장은 없다.**\
  근거로 쓰는 것은 「**전제 조건이 있는 연산은 못 쓴다**」이지 **죽는 방식이 아니다.**
- ★ 마커를 **표준 오류**로 찍은 이유 — sanitizer 가 `abort()` 하면 **버퍼에 남은 표준 출력이 사라진다.**

### (10) ★ 헤더를 안 넣었는데 컴파일된다

**언제 쓰나** — 「내 코드가 이식되나」를 따질 때.

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

- ★★ **`<utility>` 가 없는데 `std::move` 가 쓰인다.** `<string>` 이 **전이적으로** 끌어왔기 때문이다\
  (전처리 결과에 `bits/move.h` 가 **6번** 들어왔다).
- ★★★ **표준은 그 전이 포함을 보장하지 않는다.** 두 컴파일러가 **같은 libstdc++ 를 쓰기 때문에** 둘 다 통과한 것이라,\
  **컴파일러를 둘 돌렸다는 것이 이식성의 근거가 되지 않는다.**
- ★ **경고 0 건 · `cc exit=0`** 이다 — 이 갈래의 「**종료 코드가 0인데 이식되지 않는다**」 자리다.

### (11) 다섯 층 — 무엇이 표준이고 무엇이 도구인가

★★ **08 과 달리 이 주제는 층이 고르게 퍼진다.** `move`·`forward` 자체는 표준이 한 줄로 정하는데,\
**이동 후 상태**가 미명시로 빠지고 **`noexcept` 여부**가 관용구를 만들고 **오용이 UB 로 떨어진다.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | **`std::move` 가 `static_cast<T&&>` 와 같은 것**((1)) · **`const` 를 떼지 않는 것**((1)(5)) · **참조 축약 규칙**((6)) · **전달 참조에서 `T` 가 정해지는 규칙**((6)) · **`T&&` 로 선언된 이름이 lvalue 인 것**((6)) · **`unique_ptr` 이 이동 후 널인 것**((4)) · **`vector` 가 `noexcept` 가 아니면 복사로 가는 것**((7)) · **`return std::move(지역)` 이 NRVO 를 막는 것**((8)) | 타입 창 + 로그 창 **양쪽** | ★★★ **`const` 를 `move` 하면 복사가 되는 것 — 경고 0건**((5)) |
| **조건부 표준** | 표준판이 있을 때만 | ★ **`T&&`·`move`·`forward`·참조 축약이 전부 C++11부터** · ★ **반환문의 지역이 자동으로 rvalue 로 해석되는 것도 C++11부터**((8)의 `[4]`) | `-std=c++20` 한 판만 돌렸다(★ **C++11\~14 판은 안 돌렸다**) | ★ 「언제부터인가」는 **컴파일이 통과해도 안 보인다** |
| **구현 정의** | 문서화 의무가 있다 | 진단 문구 · 경고 이름(`-Wpessimizing-move`·`-Wredundant-move`) · **`-O0` 에서 `std::move` 가 실제 호출로 남는 것**((2)) · 심볼 이름 | `objdump`·`nm` · 두 컴파일러 대조 | ★ **`-O2` 만 보면 「항상 공짜」로 오해한다** |
| **미명시** | 몇 가지 중 하나 | ★★★ **이동 후 `std::string`·`std::vector` 의 상태**((4)) — 「유효하지만 미명시」 · ★ **SSO 짧은 문자열도 비워지는 것** | 실행 1판(libstdc++) | ★★ **출력이 `size=0` 으로 깔끔해서 보장처럼 보인다** — 이 칸은 **미명시라고 적어야** 안 쓰인다 |
| **UB** | 아무 일이나 | ★★ **이동 후 원본에 전제 조건이 있는 연산**((9)의 `v1.front()`) | ASan `SEGV` · `run exit=1` | ★★★ **g++·clang 둘 다 경고 0건** — **ASan 만 잡는다** |

**「도구가 못 보는 것」을 층마다 — 전용 표**

| 사실 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | ASan | 비고 |
|---|---|---|---|---|
| ★★★ **`const` 를 `move`**((5)) | ★★ **0건** | ★★ **0건** | — | ★ 로그로만 보인다 |
| ★★★ **`noexcept` 없는 이동**((7)) | ★★ **0건** | ★★ **0건** | — | ★ **복사 3회를 세야** 보인다 |
| `return std::move(지역)`((8)) | **경고 2 + 1** · `cc exit=0` | **같은 셋** | — | ★ 이름이 둘로 갈린다 |
| ★★ **이동 후 `front()`**((9)) | ★★ **0건** | ★★ **0건** | ★ **SEGV** · `run exit=1` | ★ 컴파일 시간에는 안 보인다 |
| `<utility>` 누락((10)) | **0건** · `cc exit=0` | **0건** | — | ★★ 「**종료 코드가 0인데 이식되지 않는다**」 |
| `std::move` 의 런타임 비용((2)) | — | — | — | ★ **`objdump` 로만**, 그것도 **최적화 수준마다 답이 다르다** |

- ★★★ **이 갈래의 고정 항목은 「종료 코드가 0인데 ill-formed」인데, 이 주제에서 나온 것은 그 사촌이다** —\
  (10)은 **ill-formed 가 아니라 「이 구현에서만 되는」** 것이고, (5)·(7)·(9)는 **적법한 프로그램인데 뜻이 틀린** 것이다.\
  ★ **09 에서는 컴파일러가 막아 줄 자리가 거의 없다** — 그래서 **로그와 sanitizer 가 본체**가 된다.

## 문법 — 형태와 규칙

### 형태

```text
   ── 선언 ──
   T&&  r = <rvalue>;              rvalue 참조 (C++11부터)
   void f(T&&);                    rvalue 만 받는 오버로드
   template <class T>
   void g(T&&);                    ★ 전달 참조 — lvalue 도 받는다

   ── 두 캐스트 ──
   std::move(x)                    무조건 rvalue 로   (인자를 「버리는」 자리)
   std::forward<T>(x)              ★ T 에 따라 갈린다 (전달 참조를 넘기는 자리)

   ── 참조 축약 ──
   T = int    ->  T&& = int&&
   T = int&   ->  T&& = int&       ★ & 가 하나라도 있으면 &
   T = int&&  ->  T&& = int&&

   ── 직접 만들면 ──
   Widget(Widget&& o) noexcept     ★ noexcept 를 빼면 vector 가 복사한다 ((7))
       : p(o.p) { o.p = nullptr; } ★ 원본을 「유효한 상태」로 남겨야 한다
```

- ★★ **`std::forward` 는 템플릿 인자를 반드시 명시한다** — `std::forward(x)` 는 추론이 안 되게 만들어져 있다.
- ★ **`Widget&&` 는 전달 참조가 아니다** — **추론되는 `T&&`** 만 그렇다.

### 금지 사례 — 던지면 무엇이 나오나

| 쓴 것 | 결과 | 어디서 |
|---|---|---|
| `Noisy d = std::move(c);` (`c` 가 `const`) | ★ **컴파일 통과 · 복사** · 경고 0 | (5) |
| `Widget(Widget&&)` 에서 `noexcept` 누락 | ★ **컴파일 통과 · `vector` 가 복사** · 경고 0 | (7) |
| `return std::move(n);` | **경고 1**(`-Wpessimizing-move`) · `cc exit=0` | (8) |
| `return std::move(매개변수);` | **경고 1**(`-Wredundant-move`) · `cc exit=0` | (8) |
| 이동 후 `v1.front()` | ★ **컴파일 통과 · 경고 0 · ASan SEGV** | (9) |
| `<utility>` 없이 `std::move` | ★ **컴파일 통과**(이 구현에서만) | (10) |
| `std::forward(x)` (인자 생략) | (이 문서는 안 던졌다) | — |

★★★ **여섯 줄 중 컴파일러가 막아 주는 것이 하나도 없다.** 이 주제가 「어디서 틀리나」가 두꺼운 이유다.

### 고를 것을 손으로 돌리는 순서

```text
   이 인자를 다시 쓸 일이 있나?
      있다  -> move/forward 를 쓰지 마라
      없다
        ↓
   내가 받은 것이 구체 타입의 T&& 인가, 추론된 T&& 인가?
      구체 타입(Widget&&)  -> std::move
      추론(template T&&)   -> std::forward<T>
        ↓
   그 타입이 const 인가?
      그렇다 -> ★ 이동이 안 된다. 복사가 난다 ((5)) — const 를 뗄 수 있는지 먼저 본다
```

## 어디서 틀리나

### 1. ★★★ 「`std::move` 가 옮긴다」

**안 옮긴다.** (3)의 `[3]` 이 그 반례다 — 부르고 안 쓰면 **원본이 그대로**다.\
★ 옮기는 것은 **이동 생성자·이동 대입**이고, `std::move` 는 **그것이 뽑히게 만드는 캐스트**다.

### 2. ★★★ 「`const` 를 `move` 하면 이동한다」

**복사가 난다**((5)). `std::move(ci)` 의 타입이 **`const T&&`** 라 이동 생성자가 못 받는다.\
★★ **경고 0건**이다 — 두 컴파일러 다. **로그를 찍기 전에는 안 보인다.**

### 3. ★★★ 「이동 생성자를 썼으니 `vector` 가 이동한다」

**`noexcept` 가 없으면 복사한다**((7): 복사 3회).\
★ **`noexcept` 한 낱말**이 원인이고, `is_nothrow_move_constructible_v` 로 **미리 물을 수 있다.**

### 4. ★★ 「`T&&` 매개변수 안에서 `x` 는 rvalue 다」

**lvalue 다** — 이름이 있으니까((6)).\
★ 그래서 안에서 또 `std::move`/`std::forward` 를 써야 한다. **이것이 두 함수가 따로 있는 이유**다.

### 5. ★★ 「`T&&` 는 rvalue 참조다」

**추론되는 자리에서는 전달 참조**다((6)).\
`probe(i)` 에서 `T = int&` 가 되어 매개변수가 **`int&`** 가 된다 — **lvalue 를 받았다.**\
★ `std::vector<T>&&` 나 `Widget&&` 는 **전달 참조가 아니다.**

### 6. ★★ 「이동 후 원본은 쓰면 안 된다」

**반은 맞다.** **전제 조건이 없는 연산**(대입·`clear`·`size`·`empty`·`push_back`)은 **적법하다**((4)의 마지막 줄).\
**전제 조건이 있는 것**(`front`·`back`·`operator[]`)이 UB 다((9)).\
★ 「쓰지 마라」로 외우면 **되살려 쓰는 정상 코드까지 막는다.**

### 7. ★★ 「이동 후 `string` 은 빈 문자열이 된다」

**이 구현에서는 그랬다**((4)). **표준은** 「**유효하지만 미명시**」라고만 한다.\
★ 이 문서는 그 칸을 **흔들리는 칸**으로 선언했다 — **값을 근거로 쓰지 않는다.**

### 8. ★★ 「`return std::move(x)` 가 더 빠르다」

**느리다**((8)). NRVO 를 막아 **이동이 한 번 더** 난다.\
★ 두 컴파일러가 **경고로 알려 준다**(`-Wpessimizing-move`) — 이 주제에서 **드물게 도구가 잡아 주는 자리**다.

### 9. ★ 「`std::move` 는 언제나 공짜다」

**`-O2` 에서는 그렇고 `-O0` 에서는 호출이 남는다**((2)).\
★ 「공짜다」를 적을 때 **어느 최적화 수준인지** 같이 적는다.

### 10. ★ 「두 컴파일러에서 되니 이식된다」

**아니다**((10)). g++ 와 clang 이 **같은 표준 라이브러리**(libstdc++)를 쓰면\
**헤더 전이 포함이 같아서** 둘 다 통과한다 — **컴파일러 둘은 표준 라이브러리 둘이 아니다.**

## 구현 세부사항 대 언어 보장

| 사실 | 누가 정하나 | 근거 |
|---|---|---|
| `std::move(x)` 가 `static_cast<T&&>(x)` 인 것 | ★★★ **표준** | (1) — 타입 일치 + `static_assert` |
| `std::move` 가 `const` 를 떼지 않는 것 | ★★★ **표준** | (1)의 `m3` = `const int&&` |
| 참조 축약과 전달 참조 추론 | ★★★ **표준** | (6) |
| `unique_ptr` 이 이동 후 널인 것 | ★★★ **표준** | (4) |
| `string`·`vector` 가 이동 후 어떤 상태인지 | ★★★ **미명시** | (4) — `size=0` 은 **관찰** |
| `vector` 가 `noexcept` 가 아니면 복사하는 것 | ★★ **표준**(강한 보장에서 나온다) | (7) — 복사 3회 |
| `-O0` 에서 `std::move` 가 호출로 남는 것 | ★★ **구현 정의** | (2) — `nm` 에 심볼이 있다 |
| 경고 이름·문구 | **구현 정의** | (8) |
| `<utility>` 를 안 넣어도 되는 것 | ★★★ **구현 정의**(표준 아님) | (10) |
| 이동 후 `front()` 가 SEGV 로 죽는 것 | ★★ **UB 의 한 결과일 뿐** | (9) — 보장이 아니다 |

## 언제 쓰고 언제 안 쓰나

- **`std::move` 를 쓴다** — 그 변수를 **다시 안 쓸 때**. 컨테이너에 넣을 때, 멤버에 저장할 때, 큰 지역을 넘길 때.
- **`std::move` 를 안 쓴다** — **반환문**((8)) · **`const` 인 것**((5)) · **다시 쓸 변수** · **작은 타입**(`int`·포인터는 이동이 복사와 같다).
- **`std::forward<T>` 를 쓴다** — **추론된 `T&&`** 를 그대로 넘길 때만. 그 자리에서 `std::move` 를 쓰면 **lvalue 까지 훔친다.**
- ★★ **이동 생성자를 직접 쓰면 `noexcept` 를 붙인다**((7)). 붙일 수 없으면 **왜 못 붙이는지**가 설계 문제다.
- ★ **이동 후 원본을 쓸 거면 먼저 대입해 초기 상태로 만든다**((4)의 마지막 줄).

## 핵심 문장

- **`std::move` 는 캐스트다** — 옮기는 것은 이동 생성자다.
- **`std::move` 는 `const` 를 떼지 않는다** — 그래서 `const` 를 옮기면 조용히 복사된다.
- **`T&&` 로 선언된 이름은 lvalue 다** — 그래서 `forward` 가 필요하다.
- **이동 후 원본은 유효하다** — 다만 내용은 미명시이고, 전제 조건이 있는 연산은 못 쓴다.
- **이동 생성자에 `noexcept` 가 없으면 `vector` 는 복사한다** — 한 낱말이 복사 3회를 만들었다.

## 관련 자료

- [목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/) — **어떤 식이 xvalue 인가**가 거기 정본이다. 여기는 **그 범주를 만드는 법**부터.
- [목록의 **17번 주제**](../17-move-constructor-assignment-and-moved-from-state/) — **이동 생성자·이동 대입을 어떻게 구현하나**와 **「유효하되 미지정」이라는 계약**이 거기. 여기는 **부르는 쪽**만.
- 목록의 **53번 주제** — **`noexcept` 가 무엇을 계약하나**가 거기. 여기는 **(7)의 결과**만.
- [목록의 **11번 주제**](../11-choosing-parameter-passing/) — 그래서 **매개변수를 무엇으로 받나**. 08 → 09 → 11 사슬의 끝.
- 목록의 **34번 주제** — 가변 인자 템플릿에서의 **완벽 전달**. 여기는 **인자 하나**짜리까지.
- [목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/) — `=default`/`=delete` 와 0/3/5의 법칙.
- 형제 [`07-references-vs-pointers/`](../07-references-vs-pointers/) — **참조가 무엇인가**. 그 문서는 **lvalue 참조만** 다룬다.
- 형제 [`01-function-overloading-and-overload-resolution/`](../01-function-overloading-and-overload-resolution/) — (5)에서 **왜 복사 생성자가 뽑혔나**의 순서.
- 형제 [`05-auto-and-decltype-type-deduction/`](../05-auto-and-decltype-type-deduction/) — `auto&&` 와 **추론 규칙**.
- 대비 — [`../../../rust/syntax/08-ownership-and-move/`](../../../rust/syntax/08-ownership-and-move/): ★★ **Rust 는 이동이 기본**이라 `let b = a;` 가 이미 이동이고,\
  **이동 후 원본을 쓰면 컴파일 에러**(`E0382`)다. C++ 는 **기본이 복사**이고 이동은 **캐스트로 요청**하는 것이며,\
  이동 후 원본을 쓰는 것은 **에러가 아니라 계약 문제**다((4)(9)). **같은 낱말이 한쪽은 타입 체계, 한쪽은 관용구다.**

## 용어 풀이

- **rvalue 참조(`T&&`)** — rvalue 에만 묶이는 참조. C++11부터. 예: `int&& r = 42;`.
- **`std::move`** — 인자를 무조건 rvalue 로 캐스트하는 함수. 예: `static_cast<T&&>(x)` 와 같다((1)).
- **`std::forward<T>`** — `T` 에 따라 lvalue 로도 rvalue 로도 캐스트하는 함수. 전달 참조에서만 뜻이 있다.
- **전달 참조(forwarding reference)** — **추론되는** `T&&`. lvalue 도 받는다. 예: `template <class T> void f(T&& x)`.
- **참조 축약(reference collapsing)** — 참조의 참조를 한 겹으로 접는 규칙. `&` 가 하나라도 있으면 `&`.
- **이동 후 상태(moved-from state)** — 이동당한 객체의 상태. **유효하지만 미명시**. 예: `v1.size()` 는 되고 `v1.front()` 는 UB((9)).
- **NRVO(named return value optimization)** — 이름 있는 지역을 **반환 자리에 바로 만드는** 최적화. `std::move` 를 붙이면 막힌다((8)).
- **강한 예외 보장(strong exception guarantee)** — 연산이 실패하면 **원래 상태가 그대로** 남는 보장. (7)에서 `vector` 가 복사를 고르는 이유다.
- **SSO(small string optimization)** — 짧은 문자열을 힙 대신 객체 안에 담는 구현 기법. ★ 표준 용어가 아니라 **구현 기법 이름**이다.
- **약한 심볼(weak symbol)** — 여러 번역 단위에 같은 정의가 있어도 되는 심볼. (2)의 `nm` 출력에서 `W` 로 찍힌다.

## 더 들어가면

- ★ **`std::move_if_noexcept`** — (7)에서 `vector` 가 고르는 것을 **손으로 쓰면** 이 함수다. 이 문서는 **던지지 않았다.**
- ★ **`std::exchange`** — 이동 생성자에서 「가져가고 널로 비우기」를 한 줄로 쓰는 관용구. 안 던졌다.
- ★ **`const` 를 돌려주는 함수** — `const Widget f();` 는 호출 쪽의 이동을 **전부 복사로** 만든다((5)와 같은 집안). 안 던졌다.
- ★ **이 문서가 안 던진 것** — 가변 인자 팩의 `forward`(목록의 **34번 주제**) · 람다 초기화 캡처 `[p = std::move(p)]`(목록의 **39번 주제**) ·
  `std::forward` 를 잘못 써서 두 번 이동하는 것 · **C++11\~14 판에서의 동작**(여기는 `-std=c++20` 한 판이다).
