# cpp/syntax/26 — `unique_ptr` 와 소유권 이동 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — `std::unique_ptr`](https://en.cppreference.com/w/cpp/memory/unique_ptr) · [cppreference — `std::make_unique`](https://en.cppreference.com/w/cpp/memory/unique_ptr/make_unique) · [cppreference — 복사 생략](https://en.cppreference.com/w/cpp/language/copy_elision)\
> ★ **이 배치에서는 위 cppreference 세 쪽을 열지 못했다**(웹 도구 한도). 규칙은 **전부 두 컴파일러·ASan·libstdc++ 헤더의 진단 줄**로 적었다 —\
> 진단이 **`unique_ptr.h:522` 의 `unique_ptr(const unique_ptr&) = delete;`** 를 직접 인용하므로, 「복사가 지워져 있다」는 **헤더 줄 자체가 근거**다.
> **실행 검증** — 이 문서의 모든 출력·진단·리포트는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **libstdc++ 13**(두 컴파일러가 같은 것을 쓴다) · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고, 블록마다 **소스 파일 이름이 다르다**(`uptr01.cpp` \~ `uptr11.cpp`).\
> ★ (3)(8)은 **`-std=c++14`/`-std=c++11`** 판을 더 던졌고, **배너에 적었다.**\
> ★★★ **ASan 을 붙인 블록은 마커를 `stderr` 로 찍었다** — sanitizer 가 `abort()` 로 죽이면 **버퍼에 남은 표준 출력이 통째로 사라지기 때문**이다(소스 첫머리에 그렇게 적었다).\
> ★★ **리포트를 자른 블록은 자르는 명령을 배너에 적었다** — 실린 것이 「생략한 일부」가 아니라 「**그 명령의 전체 출력**」이다.\
> ★★ **clang + ASan 블록은 런타임 프레임의 절대 경로와 BuildId 를 `sed` 로 지웠다** — 그 `sed` 도 **배너에 있다.**\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. 소스 펜스의 배너도 **캡처가 찍은 것**이다.
> **버전** — `unique_ptr` 는 **C++11부터**, **`make_unique` 는 C++14부터**, **반환 prvalue 의 의무 생략·함수 인자 평가의 비끼워넣기는 C++17부터**다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 실행으로 접지했다.
> ★★★ **앞 편들이 이 주제의 절반을 이미 쟀다 — 다시 재지 않고 인용한다.**\
> [15번](../15-raii-resources-as-types/) (5) — **삭제자는 빈 것에는 0회 · `release()` 0회 · `reset()` 2회** · `sizeof` **상태 없는 함수 객체·람다 8 · 함수 포인터 16**.\
> [17번](../17-move-constructor-assignment-and-moved-from-state/) (4) — **이동 후 `u1.get() == nullptr` 은 표준이 못 박은 것**이고 `string`·`vector` 는 「유효하되 미지정」 · (8) — **러스트는 이동 후 사용을 컴파일에서 막는다.**\
> [18번](../18-rule-of-zero-three-five-default-delete/) (1)(5) — `unique_ptr` 멤버를 가진 타입이 **복사 `0` · 이동 `1`** 인 0의 법칙 격자.\
> [20번](../20-virtual-destructors-and-polymorphic-deletion/) (1) — **`unique_ptr<Base>(new Derived)` 는 `~Base` 만**(삭제자가 `default_delete<Base>`) · `sizeof` **8** · **clang 18 + ASan 은 그 type-mismatch 를 크기 없는 `_ZdlPv` 때문에 못 본다.**\
> ★★ **여기서 새로 묻는 것은 「소유권이 타입에 있다」는 한 문장이다** — **복사 불가를 에러 전문으로** · **팩토리 반환이 몇 번 옮기나** · **삭제자가 어디에 사나(크기 격자)** · **배열 판** · **함수에 넘기는 네 모양**.
> **경계** — ★★★ 「**RAII·스마트 포인터가 무엇을 못 지우는가**」의 **논증은 [`c-cpp-csharp.md`](../../../c-cpp-csharp.md)가 정본**이다(「`unique_ptr` 은 소유권이 하나임을 타입으로 표현한다」 · 「누가 해제하는가에는 답하지만 누가 아직 보고 있는가에는 답하지 않는다」). 여기는 **API 사용**이다.\
> 「공유 소유와 제어 블록」은 [27번](../27-shared-ptr-and-reference-counting/), 「`weak_ptr` 와 순환」은 [목록의 **28번 주제**](../28-weak-ptr-and-reference-cycles/), 「`new`/`delete` 와 raw 포인터가 남는 자리」는 [목록의 **29번 주제**](../29-new-delete-and-where-raw-pointers-remain/)다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 리포트의 **PID**·주소 · 진단 **문구** | ★★★ **에러가 나는 줄 · 개수 · `cc exit`/`run exit`** · **삭제자가 몇 번 옮겨졌나** — 이 주제의 답 자체다 |
> | — | ★★★ **`sizeof` 격자** · **타입 특성 0/1** · ★★ **ASan 오류의 종류**(`bad-free` · `alloc-dealloc-mismatch` · `Direct leak`) · **소멸자 로그** |

## 한눈에 — 쉽게 말하면

**`unique_ptr` 는 「열쇠가 하나뿐인 금고」다.**

금고 열쇠를 **복사해 주는 가게가 없다.** 열쇠를 남에게 주려면 **내 손에서 빼서 건넨다** — 그 순간 내 손은 **빈손**이다.\
열쇠를 가진 사람이 떠나면(스코프를 나가면) **금고가 저절로 비워진다.** 누가 비울지 다툴 일이 없다 — **열쇠가 하나니까.**

- **복사 금지** — 열쇠 복사기가 **법으로 금지**돼 있다. 복사하려는 순간 **컴파일러가 막는다**((1)).
- **이동** — 열쇠를 **건넨다.** 건넨 손은 **확실히 빈손**이다(표준이 못 박았다 — 17편 (4)).
- **팩토리** — 금고를 **새로 만들어 열쇠째 넘겨주는 가게.** 열쇠를 **건네는 동작조차 없이** 받는 사람 손에서 바로 생긴다((2)).
- **삭제자** — 금고를 비우는 **방법 쪽지.** 쪽지가 백지면(**상태 없는 함수 객체**) **자리를 안 차지한다**((3)).

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 열쇠 복사 금지 | ★★★ **복사 생성·복사 대입이 `= delete`** — 에러 3 · 3 | (1) |
| 건넨 손은 빈손 | ★★★ **이동 후 `get() == nullptr` — 표준 보장** | (1) · 17편 (4) |
| 열쇠째 넘겨주는 가게 | ★★★ **`return std::make_unique<T>()` — 삭제자 이동 0회**(C++17 의무 생략) | (2) |
| 백지 쪽지는 자리를 안 차지한다 | ★★★ **빈 삭제자는 0바이트 — 10칸 중 7칸이 커진다** | (3) |
| 금고 여러 칸 | ★★ **`unique_ptr<T[]>`** — `delete[]` · `[]` 만 있고 `*`·`->` 는 없다 | (4) |
| 열쇠를 버리고 떠난다 | ★★★ **`release()` 의 반환값을 버리면 누수** — 경고 0 · ASan `Direct leak` | (5) |
| 열쇠를 건넬까 빌려줄까 | ★★ **값 · `&` · `const&` · 원시 포인터** 판단표 | (6) |

```text
   unique_ptr<int> a = make_unique<int>(1);        a ──▶ [ 1 ]

   auto b = a;               ✗ 컴파일 에러          열쇠 복사 금지
   auto b = std::move(a);    O                     a ──▶ nullptr ★ 표준 보장     b ──▶ [ 1 ]
   } // b 스코프 끝                                  delete 1회 — 누가 지울지 다툴 일이 없다

   ★ 「소유자가 하나」가 주석이 아니라 타입(복사 = delete)에 적혀 있다
```

## 이 주제가 답하려는 질문

1. ★★★ **「소유자가 하나」는 어디에 적혀 있나** — 주석인가 타입인가((1)).
2. ★★★ **팩토리가 `unique_ptr` 를 돌려줄 때 무엇이 몇 번 옮겨지나** — 판(C++14/17)과 생략 스위치에 따라((2)).
3. ★★ **커스텀 삭제자는 `unique_ptr` 를 몇 바이트로 만드나** — 빈 것·상태 있는 것·함수 포인터·`std::function`((3)).
4. ★★ **`unique_ptr` 로 무엇을 잘못할 수 있나** — 배열 판을 안 쓰면 · `release()` 를 버리면 · 함수 인자 모양을 잘못 고르면((4)(5)(6)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ② 두 컴파일러 대조와 ⑥ 크기 격자다

★★★ **이 주제의 본체는 둘이다** — 「**복사가 안 된다**」를 **② 에러 전문**으로, 「**삭제자가 어디 사나**」를 **⑥ `sizeof` 격자**로 보인다.

```text
① 호출 로그             삭제자가 몇 번 옮겨졌나 · 소멸자가 언제 도나              (2)(6)
② ★ 두 컴파일러 대조     복사 불가 · const& 로 못 하는 것 · T[] 의 * / ->          (1)(4)(6)
③ ASan                   배열을 T 판에 · release() 누수 · 인자 평가 순서          (4)(5)(7)
④ 어셈블리               —                                                        부적용
⑤ 경고 격자              release() 의 반환값을 버려도 경고가 나나                 (5)
⑥ ★ <type_traits>·sizeof 복사·이동 가능성 · 삭제자 × sizeof                       (1)(3)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 호출 로그 | ★★ **삭제자 이동 `0 · 0 · 1 · 1`**(C++17) 대 **`2 · 2 · 2 · 3`**(C++14 · 생략 끔) | **쓴다** |
| ★★★ **② 두 컴파일러 대조** | ★★★ **본체** — 에러 3 · 3 · **문구는 g++ 만 `use of deleted function`** | **쓴다** |
| ③ ASan | ★★ **`bad-free`(비자명 소멸자 배열) · `alloc-dealloc-mismatch`(`int` 배열) · `Direct leak`** | **쓴다** |
| ④ 어셈블리 | ★ **부적용** — `unique_ptr` 의 비용은 **`sizeof` 로 이미 다 보인다**(원시 포인터와 같은 8). 이동은 포인터 복사 + 널 쓰기다 — **27번이 `lock` 명령을 셀 때 `UNIQUE` 판으로 같이 본다** | **안 쓴다(27번이 본다)** |
| ⑤ 경고 격자 | `release()` 를 버려도 **0 · 0** | **쓴다** |
| ★★★ **⑥ `<type_traits>`·`sizeof`** | ★★★ **본체** — 복사 **0** · 이동 **1** · **커진 칸 7 / 10** | **쓴다** |

- ★★ **④ 는 「부적용」이면서 「창을 바꿔 답한 것」이다** — 「`unique_ptr` 가 원시 포인터보다 비싼가」라는 질문에 **`sizeof` 8**(⑥)과 **27번의 `lock 접두 0개`** 로 답한다. **제5의 상태**다.\
  ★ 바꾼 창이 못 보는 것 — **분기·인라인 여부**는 `sizeof` 로 안 보인다. 이 문서는 **시간을 재지 않았다.**

### (1) ★★★ 복사 불가 — 「소유자가 하나」가 타입에 적혀 있다

**언제 쓰나** — `unique_ptr` 를 변수에 옮겨 담거나 함수에 넘길 때마다. **이 절이 이 주제의 중심이다.**

★ **17편 「금지 사례」가 g++ 의 한 줄을 이미 실었다** — 여기서는 **세 자리(초기화·인자·대입) × 두 컴파일러 전문**을 본다.

```cpp
/* uptr01.cpp */
// unique_ptr 를 복사하려는 세 자리 — 변수로 받기 · 값 인자로 넘기기 · 대입
#include <memory>
#include <utility>

void sink(std::unique_ptr<int> p) { (void)p; }

int main() {
    std::unique_ptr<int> a = std::make_unique<int>(1);
    std::unique_ptr<int> c;
    std::unique_ptr<int> b = a;       // 1. 복사 초기화
    sink(a);                          // 2. 값 인자
    c = a;                            // 3. 대입
    sink(std::move(a));               // 4. std::move 로 넘긴다
    (void)b;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 uptr01.cpp -o ex (cc exit=1) =====
uptr01.cpp: In function ‘int main()’:
uptr01.cpp:10:30: error: use of deleted function ‘std::unique_ptr<_Tp, _Dp>::unique_ptr(const std::unique_ptr<_Tp, _Dp>&) [with _Tp = int; _Dp = std::default_delete<int>]’
   10 |     std::unique_ptr<int> b = a;       // 1. 복사 초기화
      |                              ^
In file included from /usr/include/c++/13/memory:78,
                 from uptr01.cpp:2:
/usr/include/c++/13/bits/unique_ptr.h:522:7: note: declared here
  522 |       unique_ptr(const unique_ptr&) = delete;
      |       ^~~~~~~~~~
uptr01.cpp:11:9: error: use of deleted function ‘std::unique_ptr<_Tp, _Dp>::unique_ptr(const std::unique_ptr<_Tp, _Dp>&) [with _Tp = int; _Dp = std::default_delete<int>]’
   11 |     sink(a);                          // 2. 값 인자
      |     ~~~~^~~
/usr/include/c++/13/bits/unique_ptr.h:522:7: note: declared here
  522 |       unique_ptr(const unique_ptr&) = delete;
      |       ^~~~~~~~~~
uptr01.cpp:5:32: note:   initializing argument 1 of ‘void sink(std::unique_ptr<int>)’
    5 | void sink(std::unique_ptr<int> p) { (void)p; }
      |           ~~~~~~~~~~~~~~~~~~~~~^
uptr01.cpp:12:9: error: use of deleted function ‘std::unique_ptr<_Tp, _Dp>& std::unique_ptr<_Tp, _Dp>::operator=(const std::unique_ptr<_Tp, _Dp>&) [with _Tp = int; _Dp = std::default_delete<int>]’
   12 |     c = a;                            // 3. 대입
      |         ^
/usr/include/c++/13/bits/unique_ptr.h:523:19: note: declared here
  523 |       unique_ptr& operator=(const unique_ptr&) = delete;
      |                   ^~~~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 uptr01.cpp -o ex (cc exit=1) =====
uptr01.cpp:10:26: error: call to deleted constructor of 'std::unique_ptr<int>'
   10 |     std::unique_ptr<int> b = a;       // 1. 복사 초기화
      |                          ^   ~
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/unique_ptr.h:522:7: note: 'unique_ptr' has been explicitly marked deleted here
  522 |       unique_ptr(const unique_ptr&) = delete;
      |       ^
uptr01.cpp:11:10: error: call to deleted constructor of 'std::unique_ptr<int>'
   11 |     sink(a);                          // 2. 값 인자
      |          ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/unique_ptr.h:522:7: note: 'unique_ptr' has been explicitly marked deleted here
  522 |       unique_ptr(const unique_ptr&) = delete;
      |       ^
uptr01.cpp:5:32: note: passing argument to parameter 'p' here
    5 | void sink(std::unique_ptr<int> p) { (void)p; }
      |                                ^
uptr01.cpp:12:7: error: overload resolution selected deleted operator '='
   12 |     c = a;                            // 3. 대입
      |     ~ ^ ~
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/unique_ptr.h:523:19: note: candidate function has been explicitly deleted
  523 |       unique_ptr& operator=(const unique_ptr&) = delete;
      |                   ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/unique_ptr.h:414:19: note: candidate function not viable: expects an rvalue for 1st argument
  414 |       unique_ptr& operator=(unique_ptr&&) = default;
      |                   ^         ~~~~~~~~~~~~
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/unique_ptr.h:430:2: note: candidate function [with _Up = int, _Ep = std::default_delete<int>] not viable: expects an rvalue for 1st argument
  430 |         operator=(unique_ptr<_Up, _Ep>&& __u) noexcept
      |         ^         ~~~~~~~~~~~~~~~~~~~~~~~~~~
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/unique_ptr.h:440:7: note: candidate function not viable: no known conversion from 'std::unique_ptr<int>' to 'nullptr_t' (aka 'std::nullptr_t') for 1st argument
  440 |       operator=(nullptr_t) noexcept
      |       ^         ~~~~~~~~~
3 errors generated.
```

```text
===== echo "g++   에러 $(g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 -c uptr01.cpp -o /dev/null 2>&1 | grep -c 'error:') · 그중 use of deleted function $(g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 -c uptr01.cpp -o /dev/null 2>&1 | grep -c 'error: use of deleted function')" (exit=0) =====
g++   에러 3 · 그중 use of deleted function 3
===== echo "clang 에러 $(clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 -c uptr01.cpp -o /dev/null 2>&1 | grep -c 'error:') · 그중 use of deleted function $(clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 -c uptr01.cpp -o /dev/null 2>&1 | grep -c 'error: use of deleted function')" (exit=0) =====
clang 에러 3 · 그중 use of deleted function 0
```

- ★★★ **1·2·3번이 에러, 4번(`std::move`)은 통과**다 — 에러 **3 · 3**.
- ★★★ **진단이 헤더의 한 줄을 인용한다** — `unique_ptr.h:522: unique_ptr(const unique_ptr&) = delete;` · `:523: operator=(const unique_ptr&) = delete;`.\
  ★ **「복사가 안 된다」는 주석이나 문서가 아니라 선언 두 줄**이다. 이것이 「**소유권이 타입에 있다**」의 뜻이다.
- ★★ **문구는 두 컴파일러가 다르다** — g++ 는 **`use of deleted function`**(3건 전부), clang 은 **`call to deleted constructor`** · **`overload resolution selected deleted operator '='`**(`use of deleted function` **0건**).\
  ★ 근거는 **줄 번호와 개수**다 — 문구로 grep 하면 clang 판이 0 으로 샌다(위 세기 블록).
- ★★ **clang 이 3번에서 후보를 나열한다** — 이동 대입 `operator=(unique_ptr&&)` 는 「**rvalue 를 기대한다**」로 탈락. **`std::move` 를 붙이면 그 후보가 산다**(4번이 된 이유).

★★★ **타입 특성으로 한 줄에 본다** — [18번](../18-rule-of-zero-three-five-default-delete/)의 격자 형식이다.

```cpp
/* uptr02.cpp */
// 소유권을 <type_traits> 로 묻는다 — 다섯 타입 × 다섯 특성
#include <cstdio>
#include <memory>
#include <type_traits>

template <class T>
int row(const char* name) {
    int v[5] = {(int)std::is_copy_constructible_v<T>, (int)std::is_move_constructible_v<T>,
                (int)std::is_copy_assignable_v<T>,    (int)std::is_move_assignable_v<T>,
                (int)std::is_nothrow_move_constructible_v<T>};
    std::printf("%-20s %d      %d      %d      %d      %d\n", name, v[0], v[1], v[2], v[3], v[4]);
    return v[0] << 4 | v[1] << 3 | v[2] << 2 | v[3] << 1 | v[4];
}

int main() {
    std::printf("%-20s 복사생 이동생 복사대 이동대 noexcept이동\n", "type");
    row<int*>("int*");
    int u = row<std::unique_ptr<int>>("unique_ptr<int>");
    row<std::unique_ptr<int[]>>("unique_ptr<int[]>");
    int s = row<std::shared_ptr<int>>("shared_ptr<int>");
    row<std::weak_ptr<int>>("weak_ptr<int>");
    int split = 0;
    for (int i = 0; i < 5; ++i) split += ((u >> i) & 1) != ((s >> i) & 1);
    std::printf("unique_ptr<int> 와 shared_ptr<int> 가 갈린 칸 %d / 5\n", split);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic uptr02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
type                 복사생 이동생 복사대 이동대 noexcept이동
int*                 1      1      1      1      1
unique_ptr<int>      0      1      0      1      1
unique_ptr<int[]>    0      1      0      1      1
shared_ptr<int>      1      1      1      1      1
weak_ptr<int>        1      1      1      1      1
unique_ptr<int> 와 shared_ptr<int> 가 갈린 칸 2 / 5
```

- ★★★ **`unique_ptr<int>` — 복사생 0 · 이동생 1 · 복사대 0 · 이동대 1 · `noexcept` 이동 1.** `shared_ptr` 와 **갈린 칸 2 / 5**(복사 둘).
- ★★ **`noexcept` 이동 1** 이 중요하다 — [17번](../17-move-constructor-assignment-and-moved-from-state/) (3)의 「**`noexcept` 가 `vector` 재할당을 가른다**」에서 `vector<unique_ptr<T>>` 가 **복사 대신 이동으로 재할당**되는 근거다.
- ★ **`int*` 는 다섯 칸 다 1** — 원시 포인터는 **복사해도 아무도 막지 않는다.** 두 복사본이 둘 다 `delete` 하면 이중 해제다.

★★ **이동 후 상태는 17편이 정본이다** — `u1.get() == nullptr` 이 **표준이 못 박은 드문 자리**이고, `string`·`vector` 는 「유효하되 미지정」이다.

```text
   이동 후 원본                     층            근거
   unique_ptr : get() == nullptr    ★★★ 표준       17편 (4) — 표준이 명시한다 · 이 편 (2)(4)번 로그 d.get()==nullptr 1
   string·vector : size() == 0      ★ 구현 관찰    17편 (4) — libstdc++ 의 선택, 「유효하되 미지정」
   ★ 「이동하면 비어 있다」에 기대도 되는 표준 타입은 unique_ptr(와 shared_ptr·weak_ptr) 쪽이다
```

### (2) ★★★ 팩토리 반환 — 삭제자 이동 로그로 센다

**언제 쓰나** — `std::unique_ptr<T> make()` 모양의 팩토리를 쓸 때마다.

★ `unique_ptr` 자체의 이동 생성자에는 로그를 심을 수 없다 — **삭제자의 이동 생성자에 로그를 심었다.** `unique_ptr` 가 옮겨질 때 **삭제자도 한 번 옮겨진다.**

```cpp
/* uptr03.cpp */
// 팩토리가 unique_ptr 를 돌려준다 — 삭제자의 이동 생성자에 로그를 심어 몇 번 옮겨졌나 센다
#include <cstdio>
#include <memory>
#include <utility>

static int moves = 0;

struct Del {
    Del() = default;
    Del(Del&&) noexcept { ++moves; }
    Del& operator=(Del&&) noexcept { ++moves; return *this; }
    void operator()(int* p) const { delete p; }
};
using Up = std::unique_ptr<int, Del>;

Up make_prvalue()  { return Up(new int(1)); }            // 이름 없는 임시를 돌려준다
Up make_named()    { Up p(new int(2)); return p; }         // 이름 있는 지역을 돌려준다
Up make_moved()    { Up p(new int(3)); return std::move(p); }

int main() {
    moves = 0; { Up a = make_prvalue(); } std::printf("(1) 임시를 돌려준다          삭제자 이동 %d회\n", moves);
    moves = 0; { Up b = make_named();   } std::printf("(2) 이름 있는 지역을 돌려준다 삭제자 이동 %d회\n", moves);
    moves = 0; { Up c = make_moved();   } std::printf("(3) std::move 로 돌려준다    삭제자 이동 %d회\n", moves);
    moves = 0; { Up d = make_prvalue(); Up e = std::move(d);
                 std::printf("(4) 받은 뒤 한 번 더 옮긴다   삭제자 이동 %d회 · d.get()==nullptr %d\n", moves, (int)(d.get() == nullptr)); }
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic uptr03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
uptr03.cpp: In function ‘Up make_moved()’:
uptr03.cpp:18:56: warning: moving a local object in a return statement prevents copy elision [-Wpessimizing-move]
   18 | Up make_moved()    { Up p(new int(3)); return std::move(p); }
      |                                               ~~~~~~~~~^~~
uptr03.cpp:18:56: note: remove ‘std::move’ call
(1) 임시를 돌려준다          삭제자 이동 0회
(2) 이름 있는 지역을 돌려준다 삭제자 이동 0회
(3) std::move 로 돌려준다    삭제자 이동 1회
(4) 받은 뒤 한 번 더 옮긴다   삭제자 이동 1회 · d.get()==nullptr 1
```

- ★★★ **(1) 임시를 돌려주면 0회 · (2) 이름 있는 지역도 0회 · (3) `std::move` 로 돌려주면 1회.**
- ★★ **(3)은 두 컴파일러가 `-Wpessimizing-move` 로 경고한다** — 「`std::move` 가 복사 생략을 막는다」. [17번](../17-move-constructor-assignment-and-moved-from-state/) (6)의 「반환에 `std::move` 를 쓰면 생성자가 한 번 더 돈다」와 같다.
- ★ **(4) 받은 뒤 한 번 더 옮기면 1회**이고 **`d.get()==nullptr 1`** — 이동 후 널 보장이 이 로그에도 찍힌다.

★★★ **생략을 끄면(`-fno-elide-constructors`) 어느 칸이 움직이나.**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fno-elide-constructors uptr03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
uptr03.cpp: In function ‘Up make_moved()’:
uptr03.cpp:18:56: warning: moving a local object in a return statement prevents copy elision [-Wpessimizing-move]
   18 | Up make_moved()    { Up p(new int(3)); return std::move(p); }
      |                                               ~~~~~~~~~^~~
uptr03.cpp:18:56: note: remove ‘std::move’ call
(1) 임시를 돌려준다          삭제자 이동 0회
(2) 이름 있는 지역을 돌려준다 삭제자 이동 1회
(3) std::move 로 돌려준다    삭제자 이동 1회
(4) 받은 뒤 한 번 더 옮긴다   삭제자 이동 1회 · d.get()==nullptr 1
===== clang++ -std=c++20 -Wall -Wextra -pedantic -fno-elide-constructors uptr03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
uptr03.cpp:18:47: warning: moving a local object in a return statement prevents copy elision [-Wpessimizing-move]
   18 | Up make_moved()    { Up p(new int(3)); return std::move(p); }
      |                                               ^
uptr03.cpp:18:47: note: remove std::move call here
   18 | Up make_moved()    { Up p(new int(3)); return std::move(p); }
      |                                               ^~~~~~~~~~ ~
1 warning generated.
(1) 임시를 돌려준다          삭제자 이동 0회
(2) 이름 있는 지역을 돌려준다 삭제자 이동 1회
(3) std::move 로 돌려준다    삭제자 이동 1회
(4) 받은 뒤 한 번 더 옮긴다   삭제자 이동 1회 · d.get()==nullptr 1
```

- ★★★ **(1)은 끄고도 0회** · **(2)는 0 → 1회**로 움직였다. 두 컴파일러가 **같다.**
- ★★★ **(1)이 안 움직인 것이 C++17 의 「의무 생략」이다** — 반환하는 것이 **prvalue(이름 없는 임시)** 면 **옮기는 동작 자체가 없다.** 스위치가 끌 수 있는 것은 **재량 생략(NRVO)** 뿐이다.\
  ★ [16번](../16-copy-constructor-and-copy-assignment/) (2)가 **복사 생성자 로그**로 같은 선을 그었다 — 여기서는 **이동 전용 타입**에서 같은 선을 확인했다.

★★ **같은 것을 `-std=c++14` 로** — 의무 생략이 없던 판이다.

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic -fno-elide-constructors uptr03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
uptr03.cpp: In function ‘Up make_moved()’:
uptr03.cpp:18:56: warning: moving a local object in a return statement prevents copy elision [-Wpessimizing-move]
   18 | Up make_moved()    { Up p(new int(3)); return std::move(p); }
      |                                               ~~~~~~~~~^~~
uptr03.cpp:18:56: note: remove ‘std::move’ call
(1) 임시를 돌려준다          삭제자 이동 2회
(2) 이름 있는 지역을 돌려준다 삭제자 이동 2회
(3) std::move 로 돌려준다    삭제자 이동 2회
(4) 받은 뒤 한 번 더 옮긴다   삭제자 이동 3회 · d.get()==nullptr 1
```

- ★★★ **(1)이 0 → 2회** — C++14 에서는 prvalue 반환도 「**옮길 수 있어야 한다**」였다. 끄면 **반환값으로 1회 + 받는 변수로 1회**가 드러난다.
- ★★ **그래서 C++14 에서 「이동도 복사도 안 되는 타입」은 팩토리로 돌려줄 수 없었다** — `unique_ptr` 는 이동이 되니 문제가 없었지만, **의무 생략은 「이동이 싸다」가 아니라 「이동이 필요 없다」를** 준다.

```text
                           C++17 기본   C++17 생략 끔   C++14 생략 끔
   return Up(new int(1));      0            ★ 0             2        ★ 의무 생략(C++17) — 끌 수 없다
   Up p(...); return p;        0              1             2        재량 생략(NRVO)
   return std::move(p);        1              1             2        ★ 생략을 스스로 막았다(-Wpessimizing-move)
```

### (3) ★★★ 삭제자 크기 격자 — 삭제자는 어디에 사나

**언제 쓰나** — `fclose`·`free`·`CloseHandle` 같은 **C API 해제 함수**를 `unique_ptr` 에 달 때.

★ **[15번](../15-raii-resources-as-types/) (5)가 네 칸(빈 함수 객체 8 · 빈 람다 8 · 함수 포인터 16 · 기본 8)을 쟀다** — 여기서는 **열 칸으로 넓힌다.**

```cpp
/* uptr04.cpp */
// 삭제자의 종류 × sizeof(unique_ptr<int, D>) — 삭제자가 어디에 사나
#include <cstdio>
#include <functional>
#include <memory>

struct EmptyDel { void operator()(int* p) const { delete p; } };
struct IntDel   { int tag = 0; void operator()(int* p) const { delete p; } };
struct FatDel   { char buf[24] = {}; void operator()(int* p) const { delete p; } };
void free_fn(int* p) { delete p; }

int main() {
    int k = 1;
    int* kp = &k;
    auto lam0 = [](int* p) { delete p; };
    auto lam1 = [k](int* p) { (void)k; delete p; };
    auto lam2 = [kp](int* p) { (void)kp; delete p; };

    struct Row { const char* name; std::size_t del, up; };
    const Row rows[] = {
        {"default_delete<int>",  sizeof(std::default_delete<int>), sizeof(std::unique_ptr<int>)},
        {"EmptyDel",             sizeof(EmptyDel),                 sizeof(std::unique_ptr<int, EmptyDel>)},
        {"[](int*){}",           sizeof(lam0),                     sizeof(std::unique_ptr<int, decltype(lam0)>)},
        {"void(*)(int*)",        sizeof(&free_fn),                 sizeof(std::unique_ptr<int, void (*)(int*)>)},
        {"IntDel",               sizeof(IntDel),                   sizeof(std::unique_ptr<int, IntDel>)},
        {"[k](int*){}",          sizeof(lam1),                     sizeof(std::unique_ptr<int, decltype(lam1)>)},
        {"[kp](int*){}",         sizeof(lam2),                     sizeof(std::unique_ptr<int, decltype(lam2)>)},
        {"FatDel",               sizeof(FatDel),                   sizeof(std::unique_ptr<int, FatDel>)},
        {"EmptyDel&",            sizeof(EmptyDel&),                sizeof(std::unique_ptr<int, EmptyDel&>)},
        {"function<void(int*)>", sizeof(std::function<void(int*)>), sizeof(std::unique_ptr<int, std::function<void(int*)>>)},
    };
    std::printf("%-22s sizeof(D)  sizeof(unique_ptr<int, D>)\n", "D");
    int grew = 0, n = 0;
    for (const Row& r : rows) {
        std::printf("%-22s %-10zu %zu\n", r.name, r.del, r.up);
        ++n;
        if (r.up != sizeof(int*)) ++grew;
    }
    std::printf("int* 한 개(%zu)보다 커진 칸 %d / %d\n", sizeof(int*), grew, n);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic uptr04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
D                      sizeof(D)  sizeof(unique_ptr<int, D>)
default_delete<int>    1          8
EmptyDel               1          8
[](int*){}             1          8
void(*)(int*)          8          16
IntDel                 4          16
[k](int*){}            4          16
[kp](int*){}           8          16
FatDel                 24         32
EmptyDel&              1          16
function<void(int*)>   32         40
int* 한 개(8)보다 커진 칸 7 / 10
```

- ★★★ **`int* 한 개(8)보다 커진 칸 7 / 10`** — 스크립트가 센 것이다. **8 로 남은 셋은 전부 「상태 없는 삭제자」**(`default_delete` · 빈 함수 객체 · 캡처 없는 람다)다.
- ★★★ **빈 삭제자는 `sizeof(D)` 가 1 인데 `unique_ptr` 에 0바이트를 더한다** — 이것이 **빈 기반 최적화(EBO)** 다. libstdc++ 는 포인터와 삭제자를 **`tuple` 에 담아** 빈 타입이 자리를 안 차지하게 한다(구현 — 아래 헤더 줄).
- ★★ **상태가 있으면 그만큼 커진다** — `IntDel`(4) · `[k]`(4) → **16**(8 + 4 + 패딩 4) · `[kp]`(8) → 16 · `FatDel`(24) → **32** · `std::function`(32) → **40**.
- ★★ **함수 포인터는 16** — 「어느 함수를 부를지」가 **값**이라 들고 다녀야 한다. 같은 일을 하는 **캡처 없는 람다는 8** 이다 — 「**어느 함수**」가 **타입**에 들어 있기 때문이다.
- ★★★ **`EmptyDel&` 는 `sizeof(D)` 가 1 로 찍히는데 `unique_ptr` 는 16** 이다 — `sizeof` 는 **참조가 가리키는 타입의 크기**를 돌려주지만, 멤버로 든 참조는 **포인터 하나만큼** 자리를 먹는다. **`sizeof(D)` 칸을 믿으면 틀린다.**
- ★ **clang 도 한 글자도 같았다** — 두 컴파일러가 **같은 libstdc++** 를 쓴다. 「두 컴파일러에서 같았다」는 **표준 라이브러리가 같다**는 뜻일 뿐이다.

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic uptr04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
D                      sizeof(D)  sizeof(unique_ptr<int, D>)
default_delete<int>    1          8
EmptyDel               1          8
[](int*){}             1          8
void(*)(int*)          8          16
IntDel                 4          16
[k](int*){}            4          16
[kp](int*){}           8          16
FatDel                 24         32
EmptyDel&              1          16
function<void(int*)>   32         40
int* 한 개(8)보다 커진 칸 7 / 10
```

```text
===== grep -n 'tuple<pointer, _Dp> _M_t;' /usr/include/c++/13/bits/unique_ptr.h (exit=0) =====
232:      tuple<pointer, _Dp> _M_t;
```

```text
   unique_ptr<int, D> 의 배치 (libstdc++ — tuple<int*, D>)

   D 가 빈 타입    [ int* 8 ]                                   = 8    ★ D 는 EBO 로 0바이트
   D = 함수 포인터 [ int* 8 ][ void(*)(int*) 8 ]                 = 16   ★ 어느 함수인지가 「값」
   D = [k] (int)   [ int* 8 ][ k 4 ][ 패딩 4 ]                    = 16
   D = function    [ int* 8 ][ std::function 32 ]                = 40

   ★ 「어느 함수를 부를지」를 타입에 두면 공짜, 값에 두면 그 값만큼 든다
```

### (4) ★★ 배열 — `unique_ptr<T[]>` 를 써야 하는 이유

**언제 쓰나** — `new T[n]` 을 맡길 때(대개는 `std::vector` 가 낫다).

```cpp
/* uptr05.cpp */
// 배열을 unique_ptr 에 맡긴다 — 인자 a 는 unique_ptr<Cell[]>, s 는 unique_ptr<Cell>, i 는 unique_ptr<int>
// 마커는 표준 오류로 찍는다 — sanitizer 가 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>
#include <cstring>
#include <memory>

struct Cell {
    int id = 0;
    ~Cell() { std::fprintf(stderr, "      ~Cell\n"); }
};

int main(int argc, char** argv) {
    const char* m = argc > 1 ? argv[1] : "a";
    if (std::strcmp(m, "a") == 0) {
        std::fprintf(stderr, "(a) unique_ptr<Cell[]>(new Cell[3])\n");
        std::unique_ptr<Cell[]> p(new Cell[3]);
        p[1].id = 7;
        std::fprintf(stderr, "    p[1].id = %d\n", p[1].id);
    } else if (std::strcmp(m, "s") == 0) {
        std::fprintf(stderr, "(s) unique_ptr<Cell>(new Cell[3])\n");
        std::unique_ptr<Cell> p(new Cell[3]);
    } else {
        std::fprintf(stderr, "(i) unique_ptr<int>(new int[3])\n");
        std::unique_ptr<int> p(new int[3]);
    }
    std::fprintf(stderr, "    블록을 나왔다\n");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic uptr05.cpp -o ex && ./ex a 2>&1 (cc exit=0 · run exit=0) =====
(a) unique_ptr<Cell[]>(new Cell[3])
    p[1].id = 7
      ~Cell
      ~Cell
      ~Cell
    블록을 나왔다
```

- ★★ **`unique_ptr<Cell[]>` 는 `delete[]` 를 부른다** — `~Cell` 이 **세 번**. `p[1]` 로 원소에 닿는다.

```cpp
/* uptr10.cpp */
// unique_ptr<Cell[]> 에 * 와 -> 를 쓴다
#include <memory>
struct Cell { int id = 0; };
int main() {
    std::unique_ptr<Cell[]> p(new Cell[3]);
    (*p).id = 1;          // 1.
    p->id = 2;            // 2.
    p[0].id = 3;          // 3.
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 uptr10.cpp -o ex (cc exit=1) =====
uptr10.cpp: In function ‘int main()’:
uptr10.cpp:6:6: error: no match for ‘operator*’ (operand type is ‘std::unique_ptr<Cell []>’)
    6 |     (*p).id = 1;          // 1.
      |      ^~
uptr10.cpp:7:6: error: base operand of ‘->’ has non-pointer type ‘std::unique_ptr<Cell []>’
    7 |     p->id = 2;            // 2.
      |      ^~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 uptr10.cpp -o ex 2>&1 | grep -E 'error:|generated' (cc exit=1) =====
uptr10.cpp:6:6: error: indirection requires pointer operand ('std::unique_ptr<Cell[]>' invalid)
uptr10.cpp:7:6: error: member reference type 'std::unique_ptr<Cell[]>' is not a pointer; did you mean to use '.'?
uptr10.cpp:7:8: error: no member named 'id' in 'std::unique_ptr<Cell[]>'
3 errors generated.
```

- ★★ **`T[]` 판에는 `operator*`·`operator->` 가 없다** — 1·2번이 에러(g++ 2 · clang 3 — clang 은 2번에서 `id` 를 못 찾는 줄을 하나 더 낸다). **배열의 「첫 원소」를 포인터처럼 쓰는 길을 타입이 막았다.**

★★★ **배열을 `T` 판에 맡기면 — ASan 에게 묻는다.**

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. uptr05.cpp -o exa && ./exa s 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=1) =====
(s) unique_ptr<Cell>(new Cell[3])
      ~Cell
=================================================================
==411767==ERROR: AddressSanitizer: attempting free on address which was not malloc()-ed: 0x503000000048 in thread T0
    #0 0x7a83658ff5e8 in operator delete(void*, unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:164
    #1 0x587808da326c in std::default_delete<Cell>::operator()(Cell*) const /usr/include/c++/13/bits/unique_ptr.h:99
    #2 0x587808da2dea in std::unique_ptr<Cell, std::default_delete<Cell> >::~unique_ptr() /usr/include/c++/13/bits/unique_ptr.h:404
    #3 0x587808da275b in main uptr05.cpp:22

0x503000000048 is located 8 bytes inside of 20-byte region [0x503000000040,0x503000000054)
allocated by thread T0 here:
    #0 0x7a83658fe6c8 in operator new[](unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:98
    #1 0x587808da26e2 in main uptr05.cpp:21

SUMMARY: AddressSanitizer: bad-free ../../../../src/libsanitizer/asan/asan_new_delete.cpp:164 in operator delete(void*, unsigned long)
```

```text
===== clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. uptr05.cpp -o exa && ./exa s 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' | sed -E 's# \(/[^ ]*/(exa\+0x[0-9a-f]+)\) \(BuildId: [0-9a-f]+\)# (\1)#' (cc exit=0 · run exit=1) =====
(s) unique_ptr<Cell>(new Cell[3])
      ~Cell
=================================================================
==411779==ERROR: AddressSanitizer: attempting free on address which was not malloc()-ed: 0x503000000048 in thread T0
    #0 0x57c747bea061 in operator delete(void*) (exa+0x106061)
    #1 0x57c747becc53 in std::default_delete<Cell>::operator()(Cell*) const /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/unique_ptr.h:99:2
    #2 0x57c747bec44b in std::unique_ptr<Cell, std::default_delete<Cell>>::~unique_ptr() /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/unique_ptr.h:404:4
    #3 0x57c747bebff3 in main uptr05.cpp:22:5

0x503000000048 is located 8 bytes inside of 20-byte region [0x503000000040,0x503000000054)
allocated by thread T0 here:
    #0 0x57c747be9901 in operator new[](unsigned long) (exa+0x105901)
    #1 0x57c747bebf83 in main uptr05.cpp:21:33

SUMMARY: AddressSanitizer: bad-free (exa+0x106061) in operator delete(void*)
```

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. uptr05.cpp -o exa && ./exa i 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=1) =====
(i) unique_ptr<int>(new int[3])
=================================================================
==412466==ERROR: AddressSanitizer: alloc-dealloc-mismatch (operator new [] vs operator delete) on 0x502000000010
    #0 0x7e08036ff5e8 in operator delete(void*, unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:164
    #1 0x57ec99562347 in std::default_delete<int>::operator()(int*) const /usr/include/c++/13/bits/unique_ptr.h:99
    #2 0x57ec99561fe6 in std::unique_ptr<int, std::default_delete<int> >::~unique_ptr() /usr/include/c++/13/bits/unique_ptr.h:404
    #3 0x57ec995617e0 in main uptr05.cpp:25

0x502000000010 is located 0 bytes inside of 12-byte region [0x502000000010,0x50200000001c)
allocated by thread T0 here:
    #0 0x7e08036fe6c8 in operator new[](unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:98
    #1 0x57ec995617c2 in main uptr05.cpp:24

SUMMARY: AddressSanitizer: alloc-dealloc-mismatch ../../../../src/libsanitizer/asan/asan_new_delete.cpp:164 in operator delete(void*, unsigned long)
```

```text
===== echo "g++   (s) $(g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. uptr05.cpp -o exa 2>&1; ./exa s 2>&1 | grep -oE '^SUMMARY: AddressSanitizer: [a-z-]+' | sort -u | tr '\n' ' ')· (i) $(./exa i 2>&1 | grep -oE '^SUMMARY: AddressSanitizer: [a-z-]+' | sort -u | tr '\n' ' ')" (exit=0) =====
g++   (s) SUMMARY: AddressSanitizer: bad-free · (i) SUMMARY: AddressSanitizer: alloc-dealloc-mismatch 
===== echo "clang (s) $(clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. uptr05.cpp -o exa 2>&1; ./exa s 2>&1 | grep -oE '^SUMMARY: AddressSanitizer: [a-z-]+' | sort -u | tr '\n' ' ')· (i) $(./exa i 2>&1 | grep -oE '^SUMMARY: AddressSanitizer: [a-z-]+' | sort -u | tr '\n' ' ')" (exit=0) =====
clang (s) SUMMARY: AddressSanitizer: bad-free · (i) SUMMARY: AddressSanitizer: alloc-dealloc-mismatch 
```

- ★★★ **`Cell`(비자명 소멸자) 배열은 `bad-free`**, **`int` 배열은 `alloc-dealloc-mismatch`** — **같은 실수인데 ASan 이 다른 이름을 댄다.**
- ★★★ **이유는 배열 쿠키다** — `Cell` 은 소멸자를 돌려야 하니 `new Cell[3]` 이 **원소 수(8바이트)를 앞에 붙여** 20바이트를 잡고, 돌려준 포인터는 **8바이트 안쪽**이다(`located 8 bytes inside of 20-byte region`).\
  `delete`(배열 아님)는 **그 안쪽 주소를 그대로 해제**하려 하니 「**malloc 한 주소가 아니다**」가 된다. `int` 는 쿠키가 없어 **주소는 맞고 짝(`new[]` 대 `delete`)만 틀렸다.**
- ★★ **로그에 `~Cell` 이 한 번뿐**이다 — 셋 중 **하나만** 파괴됐다.
- ★ **clang + ASan 도 같은 두 이름**이다 — [20번](../20-virtual-destructors-and-polymorphic-deletion/)의 type-mismatch 처럼 **clang 이 못 보는 자리가 아니다**(주소·짝 검사는 크기를 안 쓴다).

### (5) ★★★ `release()` — 소유권을 버리면 누수가 된다

**언제 쓰나** — `unique_ptr` 에서 **C API 로 소유권을 넘길 때**(`release()` 가 정당한 유일한 자리).

★ **15편 (5)가 「`release()` 는 삭제자를 0회 부른다 · 손으로 닫아야 한다」를 쟀다** — 여기서는 **손으로 안 닫으면** 무엇이 보이나를 본다.

```cpp
/* uptr06.cpp */
// release() 는 소유권을 놓는다 — 받은 포인터를 아무도 지우지 않으면
// 마커는 표준 오류로 찍는다 — sanitizer 가 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>
#include <cstring>
#include <memory>

int main(int argc, char** argv) {
    const char* m = argc > 1 ? argv[1] : "r";
    auto p = std::make_unique<long>(42);
    if (std::strcmp(m, "r") == 0) {
        std::fprintf(stderr, "(r) p.release() 의 반환값을 버린다\n");
        p.release();
    } else if (std::strcmp(m, "k") == 0) {
        std::fprintf(stderr, "(k) long* raw = p.release(); 그 뒤 delete raw;\n");
        long* raw = p.release();
        delete raw;
    } else {
        std::fprintf(stderr, "(x) p.reset();\n");
        p.reset();
    }
    std::fprintf(stderr, "    p.get() == nullptr : %d\n", (int)(p.get() == nullptr));
}
```

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. uptr06.cpp -o exa && ./exa r 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=1) =====
(r) p.release() 의 반환값을 버린다
    p.get() == nullptr : 1

=================================================================
==413562==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 8 byte(s) in 1 object(s) allocated from:
    #0 0x7768b4efe548 in operator new(unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:95
    #1 0x64b6c0ad67af in std::__detail::_MakeUniq<long>::__single_object std::make_unique<long, int>(int&&) /usr/include/c++/13/bits/unique_ptr.h:1070
    #2 0x64b6c0ad64c8 in main uptr06.cpp:9

SUMMARY: AddressSanitizer: 8 byte(s) leaked in 1 allocation(s).
```

```text
===== clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. uptr06.cpp -o exa && ./exa r 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' | sed -E 's# \(/[^ ]*/(exa\+0x[0-9a-f]+)\) \(BuildId: [0-9a-f]+\)# (\1)#' (cc exit=0 · run exit=1) =====
(r) p.release() 의 반환값을 버린다
    p.get() == nullptr : 1

=================================================================
==413723==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 8 byte(s) in 1 object(s) allocated from:
    #0 0x59231bdca7e1 in operator new(unsigned long) (exa+0x1057e1)
    #1 0x59231bdccfb4 in std::__detail::_MakeUniq<long>::__single_object std::make_unique<long, int>(int&&) /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/unique_ptr.h:1070:30
    #2 0x59231bdcccc4 in main uptr06.cpp:9:14

SUMMARY: AddressSanitizer: 8 byte(s) leaked in 1 allocation(s).
```

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. uptr06.cpp -o exa && ./exa k 2>&1 (cc exit=0 · run exit=0) =====
(k) long* raw = p.release(); 그 뒤 delete raw;
    p.get() == nullptr : 1
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. uptr06.cpp -o exa && ./exa x 2>&1 (cc exit=0 · run exit=0) =====
(x) p.reset();
    p.get() == nullptr : 1
```

```text
===== echo "g++   -Wall -Wextra -pedantic 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic -c uptr06.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
g++   -Wall -Wextra -pedantic 경고 0
===== echo "clang -Wall -Wextra -pedantic 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic -c uptr06.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
clang -Wall -Wextra -pedantic 경고 0
```

- ★★★ **`p.release();` 한 줄에 `Direct leak of 8 byte(s)`** — 두 컴파일러 다. `p` 는 **비었고**(`p.get() == nullptr : 1`) 객체는 **아무도 안 가리킨다.**
```text
===== grep -n -B2 '^      release() noexcept' /usr/include/c++/13/bits/unique_ptr.h (exit=0) =====
492-      _GLIBCXX23_CONSTEXPR
493-      pointer
494:      release() noexcept
--
754-      _GLIBCXX23_CONSTEXPR
755-      pointer
756:      release() noexcept
```

- ★★★ **컴파일러 경고는 0 · 0** 이다 — 이 판(libstdc++ 13)의 `release()` 선언에는 **`[[nodiscard]]` 가 없다**(위 헤더 줄 — `_GLIBCXX23_CONSTEXPR` 뿐이다). 그래서 **반환값을 버려도 경고하지 않는다.** 이름이 「풀어 준다」처럼 읽히는 것이 함정이다 — **`release` 는 해제가 아니라 소유권 포기다.**
- ★★ **(k) 받아서 `delete` · (x) `reset()`** 은 둘 다 누수가 없다. **해제하려면 `reset()`** 이다.

### (6) ★★ 함수에 넘기는 네 모양 — 무엇을 할 수 있고 무엇이 남나

**언제 쓰나** — `unique_ptr` 를 받는 함수의 매개변수 타입을 정할 때마다.

```cpp
/* uptr07.cpp */
// unique_ptr 를 함수에 넘기는 네 모양 — 함수가 무엇을 할 수 있고, 부른 쪽에 무엇이 남나
#include <cstdio>
#include <memory>
#include <utility>

struct Res {
    int v;
    explicit Res(int x) : v(x) {}
    ~Res() { std::printf("      ~Res(%d)\n", v); }
};
using Up = std::unique_ptr<Res>;

void by_value(Up p)          { std::printf("      by_value: v=%d\n", p->v); }
void by_ref(Up& p)           { p.reset(new Res(p->v + 100)); std::printf("      by_ref: reset 했다\n"); }
void by_cref(const Up& p)    { p->v += 1; std::printf("      by_cref: *p 를 바꿨다 v=%d\n", p->v); }
void by_raw(Res* r)          { std::printf("      by_raw: v=%d\n", r->v); }

int main() {
    Up a = std::make_unique<Res>(1);
    std::printf("(1) by_value(std::move(a))\n");
    by_value(std::move(a));
    std::printf("    돌아온 뒤 a 가 비었나 %d\n", (int)(a == nullptr));

    Up b = std::make_unique<Res>(2);
    std::printf("(2) by_ref(b)\n");
    by_ref(b);
    std::printf("    돌아온 뒤 b->v %d\n", b->v);

    Up c = std::make_unique<Res>(3);
    std::printf("(3) by_cref(c)\n");
    by_cref(c);
    std::printf("    돌아온 뒤 c->v %d\n", c->v);

    Up d = std::make_unique<Res>(5);
    std::printf("(4) by_raw(d.get())\n");
    by_raw(d.get());
    std::printf("(5) main 끝\n");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic uptr07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) by_value(std::move(a))
      by_value: v=1
      ~Res(1)
    돌아온 뒤 a 가 비었나 1
(2) by_ref(b)
      ~Res(2)
      by_ref: reset 했다
    돌아온 뒤 b->v 102
(3) by_cref(c)
      by_cref: *p 를 바꿨다 v=4
    돌아온 뒤 c->v 4
(4) by_raw(d.get())
      by_raw: v=5
(5) main 끝
      ~Res(5)
      ~Res(4)
      ~Res(102)
```

- ★★★ **값(`Up p`)으로 받으면 소유권이 넘어간다** — `~Res(1)` 이 **함수 안에서** 돌았고, 돌아온 뒤 `a` 는 **비었다.** 부르는 쪽에 **`std::move` 를 써야만** 부를 수 있다((1)).
- ★★ **`Up&` 로 받으면 함수가 갈아 끼울 수 있다** — `reset` 이 옛것(`~Res(2)`)을 지우고 새것(102)을 넣었다. **「빌려줬더니 바꿔 놓았다」**.
- ★★★ **`const Up&` 는 「읽기 전용」이 아니다** — `*p` 를 **바꿀 수 있다**(`v=4`). `const` 는 **포인터(`unique_ptr` 객체)에 붙었지 가리키는 것에 붙지 않았다**([10번](../10-const-correctness/)의 얕은 `const`).
- ★★ **원시 포인터(`d.get()`)는 관찰** — 소유권·수명과 **무관**하다. 함수가 저장해 두면 **댕글링**이 될 수 있다([목록의 **29번 주제**](../29-new-delete-and-where-raw-pointers-remain/)).

★★ **`const Up&` 로 받은 함수가 못 하는 것** —

```cpp
/* uptr09.cpp */
// const unique_ptr& 로 받은 함수가 할 수 없는 것
#include <memory>
void f(const std::unique_ptr<int>& p) {
    p.reset();                         // 1.
    std::unique_ptr<int> q = std::move(p);   // 2.
    *p = 5;                            // 3.
}
int main() { auto p = std::make_unique<int>(1); f(p); }
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 uptr09.cpp -o ex (cc exit=1) =====
uptr09.cpp: In function ‘void f(const std::unique_ptr<int>&)’:
uptr09.cpp:4:12: error: passing ‘const std::unique_ptr<int>’ as ‘this’ argument discards qualifiers [-fpermissive]
    4 |     p.reset();                         // 1.
      |     ~~~~~~~^~
In file included from /usr/include/c++/13/memory:78,
                 from uptr09.cpp:2:
/usr/include/c++/13/bits/unique_ptr.h:505:7: note:   in call to ‘void std::unique_ptr<_Tp, _Dp>::reset(pointer) [with _Tp = int; _Dp = std::default_delete<int>; pointer = int*]’
  505 |       reset(pointer __p = pointer()) noexcept
      |       ^~~~~
uptr09.cpp:5:39: warning: redundant move in initialization [-Wredundant-move]
    5 |     std::unique_ptr<int> q = std::move(p);   // 2.
      |                              ~~~~~~~~~^~~
uptr09.cpp:5:39: note: remove ‘std::move’ call
uptr09.cpp:5:41: error: use of deleted function ‘std::unique_ptr<_Tp, _Dp>::unique_ptr(const std::unique_ptr<_Tp, _Dp>&) [with _Tp = int; _Dp = std::default_delete<int>]’
    5 |     std::unique_ptr<int> q = std::move(p);   // 2.
      |                                         ^
/usr/include/c++/13/bits/unique_ptr.h:522:7: note: declared here
  522 |       unique_ptr(const unique_ptr&) = delete;
      |       ^~~~~~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 uptr09.cpp -o ex 2>&1 | grep -E 'error:|generated' (cc exit=1) =====
uptr09.cpp:4:5: error: 'this' argument to member function 'reset' has type 'const std::unique_ptr<int>', but function is not marked const
uptr09.cpp:5:26: error: call to deleted constructor of 'std::unique_ptr<int>'
2 errors generated.
```

- ★★ **`reset()` 과 소유권 가져가기(`std::move(p)`)가 막힌다** — 2 · 2. `std::move` 를 붙여도 **`const Up&&` 는 이동 생성자에 안 맞아 복사로 떨어지고, 복사는 지워져 있다**([17번](../17-move-constructor-assignment-and-moved-from-state/) (5)의 「이동이 복사로 되돌아가는 자리」).\
  ★ g++ 는 그 `std::move` 에 **`-Wredundant-move`** 까지 낸다.
- ★ **3번 `*p = 5` 는 통과**한다 — 위 판의 「`*p` 를 바꿀 수 있다」와 같은 사실이다.

| 매개변수 | 함수가 할 수 있는 것 | 부른 쪽에 남는 것 | 언제 |
|---|---|---|---|
| ★★★ `unique_ptr<T>`(값) | 소유 · 보관 · 파괴 | ★ **빈 `unique_ptr`**(부를 때 `std::move` 필수) | **소유권을 가져가는 함수**(sink) |
| ★★ `unique_ptr<T>&` | `reset`·`release`·교체 | 바뀌었을 수 있는 것 | **갈아 끼우는 함수** — 드물다 |
| ★ `const unique_ptr<T>&` | `*p` 변경 · `get()` | 그대로(가리키는 값은 바뀔 수 있다) | ★ **거의 없다** — `T&`/`T*` 로 받는 게 낫다 |
| ★★★ `T*` · `T&` | 관찰 · 사용 | 그대로 | **대부분의 함수** — 소유권과 무관한 일 |

### (7) ★ `make_unique` 가 없던 C++11 — 예외 안전 문제는 이 두 구현에서 재현되나

**언제 쓰나** — 「`make_unique` 를 써야 하는 이유」를 판단할 때.

```cpp
/* uptr11.cpp */
// make_unique 를 쓴다 — 판에 따라 되나
#include <memory>
int main() {
    auto p = std::make_unique<int>(1);
    return *p - 1;
}
```

```text
===== g++ -std=c++11 -Wall -Wextra -pedantic -fmax-errors=0 uptr11.cpp -o ex 2>&1 | grep -E 'error:' (cc exit=1) =====
uptr11.cpp:4:19: error: ‘make_unique’ is not a member of ‘std’
uptr11.cpp:4:31: error: expected primary-expression before ‘int’
===== clang++ -std=c++11 -Wall -Wextra -pedantic -ferror-limit=0 uptr11.cpp -o ex 2>&1 | grep -E 'error:|generated' (cc exit=1) =====
uptr11.cpp:4:19: error: no member named 'make_unique' in namespace 'std'
uptr11.cpp:4:34: error: expected '(' for function-style cast or type construction
2 errors generated.
===== g++ -std=c++14 -Wall -Wextra -pedantic uptr11.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
```

- ★ **C++11 에는 `std::make_unique` 가 없다** — 두 컴파일러 다 `not a member of 'std'` · `no member named`. C++14 부터 된다.

★★ **고전적인 걱정** — `f(std::unique_ptr<W>(new W), g())` 에서 **`new W` → `g()` 가 던짐 → `unique_ptr` 생성 전** 순서로 끼워 평가되면 `W` 가 샌다(C++14 까지는 그 끼워 넣기가 허락됐다고 알려져 있다).\
★★★ **던져서 확인했다** — `-std=c++14` 로.

```cpp
/* uptr08.cpp */
// f(unique_ptr<W>(new W), g()) — g() 가 던진다. 인자 c 는 한 줄로 쓴 판, h 는 그 순서를 손으로 풀어 쓴 판
// 마커는 표준 오류로 찍는다 — sanitizer 가 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <new>

struct W { W() { std::fprintf(stderr, "    W() 생성\n"); } ~W() { std::fprintf(stderr, "    ~W()\n"); } };

void* operator new(std::size_t n) {
    std::fprintf(stderr, "    operator new(%zu)\n", n);
    if (void* p = std::malloc(n)) return p;
    throw std::bad_alloc();
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

int g() { std::fprintf(stderr, "    g() 가 던진다\n"); throw 1; }
void f(std::unique_ptr<W>, int) {}

__attribute__((noinline)) void one_line() {
    f(std::unique_ptr<W>(new W), g());
}
__attribute__((noinline)) void by_hand() {
    W* raw = new W;
    int x = g();
    f(std::unique_ptr<W>(raw), x);
}

int main(int argc, char** argv) {
    const char* m = argc > 1 ? argv[1] : "c";
    try {
        if (std::strcmp(m, "c") == 0) {
            std::fprintf(stderr, "(c) f(std::unique_ptr<W>(new W), g())\n");
            one_line();
        } else {
            std::fprintf(stderr, "(h) 손으로 풀어 쓴 순서 — new W → g() → unique_ptr 생성\n");
            by_hand();
        }
    } catch (int) {
        std::fprintf(stderr, "    catch (int)\n");
    }
}
```

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic -fsanitize=address -g -ffile-prefix-map="$PWD"=. uptr08.cpp -o exa && ./exa c 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=0) =====
(c) f(std::unique_ptr<W>(new W), g())
    g() 가 던진다
    catch (int)
===== clang++ -std=c++14 -Wall -Wextra -pedantic -fsanitize=address -g -ffile-prefix-map="$PWD"=. uptr08.cpp -o exa && ./exa c 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' | sed -E 's# \(/[^ ]*/(exa\+0x[0-9a-f]+)\) \(BuildId: [0-9a-f]+\)# (\1)#' (cc exit=0 · run exit=0) =====
(c) f(std::unique_ptr<W>(new W), g())
    operator new(1)
    W() 생성
    g() 가 던진다
    ~W()
    catch (int)
```

- ★★★ **두 컴파일러 다 새지 않았다** — 그리고 **평가 순서가 반대**다. g++ 는 **`g()` 를 먼저**(`new` 가 아예 안 불렸다), clang 은 **`new W` → `unique_ptr` 완성 → `g()`**(던진 뒤 `~W()` 가 돌았다).\
  ★★ **어느 쪽도 「`new` 와 `unique_ptr` 생성 사이에 `g()` 를 끼우지」 않았다** — 규칙이 허락하던 순서를 **이 두 구현이 고르지 않았다.**
- ★★★ **그래서 이 사고는 「못 잰 것」이다** — 측정에는 **끼워 넣는 구현**이 필요한데 이 머신에 없다(제3의 상태).\
  ★ **쪼개서 잰 조각** — 그 순서를 **손으로 풀어 쓰면**(`by_hand`) 샌다.

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic -fsanitize=address -g -ffile-prefix-map="$PWD"=. uptr08.cpp -o exa && ./exa h 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=1) =====
(h) 손으로 풀어 쓴 순서 — new W → g() → unique_ptr 생성
    operator new(1)
    W() 생성
    g() 가 던진다
    catch (int)

=================================================================
==415276==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 1 byte(s) in 1 object(s) allocated from:
    #0 0x73f61dafd9c7 in malloc ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:69
    #1 0x55b2a691542b in operator new(unsigned long) uptr08.cpp:13
    #2 0x55b2a69157a5 in by_hand() uptr08.cpp:26
    #3 0x55b2a69159a0 in main uptr08.cpp:39

SUMMARY: AddressSanitizer: 1 byte(s) leaked in 1 allocation(s).
```

- ★★ **`Direct leak of 1 byte(s)`** — `new W` 뒤에 `g()` 가 던지면 **아무도 `raw` 를 소유하지 않는다.** 한 식으로 쓰든 풀어 쓰든 **그 순서가 되면** 샌다는 것이 이 조각의 결론이다.
- ★★ **C++17 부터는 함수 인자 하나의 초기화가 다른 인자와 끼워지지 않는다** — 그래서 한 식 판은 **판에 따라서도** 안전해졌다. **`make_unique` 는 그와 무관하게 `new` 를 식에서 없애** 순서 걱정 자체를 지운다.
- ★ LSan 은 **스택을 보수적으로 훑는다** — 처음에 `raw` 를 `main` 안에 두었더니 **스택에 남은 주소 때문에 누수를 못 봤다.** 그래서 **별도 함수(`noinline`)** 에 넣었다. **27번이 같은 성질을 따로 쟀다.**

## 문법 — 형태와 규칙

### 형태

```text
   auto p = std::make_unique<T>(args...);        // 기본형 — new 가 식에 없다(C++14)
   std::unique_ptr<T[]> a(new T[n]);             // 배열 — delete[] · [] 만
   std::unique_ptr<FILE, Closer> f(fopen(...));  // 커스텀 삭제자 — 빈 함수 객체면 8바이트
   std::unique_ptr<T> make() { return std::make_unique<T>(); }   // 팩토리 — 이동 0회(C++17)
   void sink(std::unique_ptr<T> p);              // 소유권을 가져가는 함수 — sink(std::move(p))
   void use(T& t);  void look(T* t);             // 소유권과 무관한 함수
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (1)\~(6)이 **컴파일한 소스**로 보였다.

### 규칙

- ★★★ **복사는 지워져 있다 — 옮기려면 `std::move`** · 옮긴 원본은 **`nullptr` 이 표준 보장**((1) · 17편 (4)).
- ★★★ **팩토리는 `return std::make_unique<T>(…)` 로** — 이동 0회(의무 생략). **`return std::move(local)` 은 쓰지 않는다**((2)).
- ★★ **삭제자는 상태 없는 함수 객체·람다로** — 함수 포인터는 16, `std::function` 은 40((3)).
- ★★ **배열은 `unique_ptr<T[]>`**(대개는 `vector`) — `T` 판에 맡기면 `bad-free`/`alloc-dealloc-mismatch`((4)).
- ★★★ **해제는 `reset()`, `release()` 는 소유권을 C API 에 넘길 때만**((5)).
- ★★ **함수는 대개 `T&`/`T*` 로 받는다** — `unique_ptr` 를 값으로 받는 것은 **소유권을 가져갈 때만**((6)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | 무엇이 되나 | 어디서 |
|---|---|---|
| `auto b = a;` · `sink(a)` · `c = a;` | ★★★ **에러 3 · 3** | (1) |
| `unique_ptr<Cell[]>` 에 `*p` · `p->id` | ★★ **에러 2 · 3** | (4) |
| `const unique_ptr&` 로 `p.reset()` · `std::move(p)` | ★★ **에러 2 · 2** | (6) |
| C++11 에서 `std::make_unique` | ★ **에러** | (7) |
| `unique_ptr<Cell>(new Cell[3])` | ★★★ **컴파일 O · ASan `bad-free`** | (4) |
| `p.release();`(반환값을 버림) | ★★★ **컴파일 O · 경고 0 · ASan `Direct leak`** | (5) |

## 어디서 틀리나

### 1. ★★★ 「`unique_ptr` 는 규칙을 지키라는 관례다」

(1)이 반증이다 — **복사 생성·복사 대입이 헤더에서 `= delete`** 다. 관례가 아니라 **타입**이다.

### 2. ★★★ 「팩토리가 `unique_ptr` 를 돌려주면 이동이 한 번은 있다」

(2)가 반증이다 — **prvalue 반환은 이동 0회**이고, **생략을 꺼도 0회**다(C++17). `std::move` 를 붙이면 **오히려 1회**가 생긴다.

### 3. ★★★ 「커스텀 삭제자를 달면 `unique_ptr` 가 커진다」

(3)이 반쯤 반증이다 — **빈 삭제자는 0바이트**다. 커지는 것은 **상태·함수 포인터·`std::function`** 이고, 그 몫만큼이다. 10칸 중 **7칸**이 커졌다.

### 4. ★★ 「`sizeof(D)` 를 보면 삭제자 몫을 안다」

(3)이 반증이다 — **`EmptyDel&` 는 `sizeof` 1 인데 16** 이 되고, **빈 삭제자는 1 인데 0** 이 된다.

### 5. ★★★ 「`release()` 는 해제한다」

(5)가 반증이다 — **소유권만 놓는다.** 반환값을 버리면 **경고 0건에 `Direct leak`**.

### 6. ★★ 「`const unique_ptr&` 로 받으면 읽기만 한다」

(6)이 반증이다 — **`*p` 를 바꿀 수 있다.** 막히는 것은 **포인터 자체**(`reset`·이동)뿐이다.

### 7. ★★ 「`f(unique_ptr<W>(new W), g())` 는 C++14 에서 반드시 샌다」

(7)이 반증이다 — **이 두 구현은 끼워 넣지 않아** 안 샌다. **「허락된 순서」와 「구현이 고른 순서」는 다르다** — 그래도 **`make_unique` 를 쓰는 이유는 사라지지 않는다**(새는 순서를 손으로 쓰면 샌다).

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제의 급소는 「이동 후 `nullptr`」이 「표준」 칸에 있다는 것이다** — [17번](../17-move-constructor-assignment-and-moved-from-state/)의 「유효하되 미지정」과 **다른 칸**이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **복사 생성·대입이 지워져 있다**((1)) · ★★★ **이동 후 `get() == nullptr`**((2)(6) · 17편 (4)) · **prvalue 반환의 의무 생략(C++17)**((2)) · **`T[]` 판은 `delete[]`**((4)) · **`release()` 는 삭제자를 부르지 않는다**((5)) | 에러 전문 · 삭제자 이동 로그 · ASan | ★★ **`const Up&` 의 얕은 `const`** — 컴파일러가 통과시킨다((6)) |
| **조건부 표준** | 특정 판에서만 | ★★ **`make_unique` 는 C++14** · **의무 생략·인자 비끼워넣기는 C++17** | `-std=c++11`/`c++14` | ★ C++14 의 이동 2회는 **생략을 꺼야** 보인다 |
| **구현 정의** | 문서화 의무 | ★★★ **삭제자의 배치(EBO)와 `sizeof`**((3)) · **배열 쿠키 8바이트**((4)) · 진단 문구 | `sizeof` 격자 · ASan 리포트 | ★ **표준은 `sizeof(unique_ptr<T>) == sizeof(T*)` 를 약속하지 않는다** — 이 판의 관찰이다 |
| **미명시** | 몇 가지 중 하나 | ★★ **함수 인자의 평가 순서**((7)) — g++ 는 오른쪽부터, clang 은 왼쪽부터였다(관찰) | 로그 | ★★★ **C++14 에서 허락됐던 끼워 넣기를 이 두 구현이 안 골라** 사고가 **재현되지 않는다** |
| **UB** | 아무 일이나 | ★★★ **`T` 판에 배열을 맡기기**((4)) · 이동한 `unique_ptr` 를 `*` 로 쓰기(17편) | ASan | ★★ **컴파일러 경고 0** — ASan 을 붙여 **실행해야** 보인다 |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | ASan (g++ · clang) |
|---|---|---|---|---|
| ★★★ **`release()` 반환값을 버림** | 표준(누수) | ★★★ **0건** | ★★★ **0건** | ★★ **`Direct leak` · `Direct leak`** |
| ★★★ **`unique_ptr<Cell>(new Cell[3])`** | UB | **0건** | **0건** | ★★ **`bad-free` · `bad-free`** |
| ★★ **`unique_ptr<int>(new int[3])`** | UB | **0건** | **0건** | ★★ **`alloc-dealloc-mismatch` · 같다** |
| ★★ **`const Up&` 로 `*p` 변경** | 표준(허용) | **0건** | **0건** | — (오류가 아니다) |
| ★ **`return std::move(p)`** | 표준(허용) | ★ **`-Wpessimizing-move` 1** | ★ **1** | — |
| ★★ **C++14 인자 끼워 넣기 누수** | 미명시 | — | — | ★★★ **재현 안 됨**(두 구현 다 안 끼움) |

- ★★ **이 표의 결론** — ★★★ **`unique_ptr` 가 막는 것은 「복사」 하나이고, 그것만은 컴파일러가 반드시 막는다. 나머지 실수(배열 · `release` · 인자)는 경고 0 이고 ASan 으로만 보인다.**

### ★ 종료 코드 0인데 ill-formed — 이 편에서는 못 찾았다

- ★ 이 편의 사고는 전부 **컴파일 에러**(복사 · `T[]` 의 `*` · C++11 `make_unique`)이거나 **UB/누수**(ASan)였다. **「경고만 내고 통과하는 ill-formed」** 는 이 주제의 탐침에서 **나오지 않았다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 힙 객체 하나를 한 곳이 소유 | ★★★ **`std::make_unique<T>()`** | 크기 8 · 복사 불가가 소유권을 강제한다((1)) |
| 팩토리 | ★★★ **`std::unique_ptr<T>` 를 값으로 반환** | 이동 0회((2)) · 받는 쪽이 `shared_ptr` 로 바꿀 수도 있다(27번) |
| C API 자원 | ★★ **`unique_ptr<R, 빈 함수 객체>`** | 삭제자가 0바이트((3)) |
| 배열 | ★★ **`std::vector`**, 굳이면 **`unique_ptr<T[]>`** | (4) |
| 함수 인자 | ★★★ **`T&`/`T*`**, 소유권을 가져갈 때만 **값** | (6) |
| 여러 곳이 수명을 나눠 가진다 | ★ **[27번](../27-shared-ptr-and-reference-counting/) `shared_ptr`** | 대가가 있다 — 크기·할당·원자 명령 |

## 핵심 문장

- ★★★ **「소유자가 하나」는 주석이 아니라 타입이다** — 복사 생성·대입이 `= delete` 이고 에러가 **헤더의 그 줄**을 인용한다.
- ★★★ **이동한 `unique_ptr` 는 `nullptr` 이 표준 보장이다** — `string`·`vector` 의 「유효하되 미지정」과 다른 칸이다.
- ★★★ **팩토리의 `return std::make_unique<T>()` 는 이동 0회** — 생략을 꺼도 0회(C++17), C++14 에서는 2회였다.
- ★★★ **빈 삭제자는 0바이트** — 삭제자 10종 중 **7종이 `unique_ptr` 를 키웠고**, 8 로 남은 셋은 전부 상태가 없었다.
- ★★ **배열을 `T` 판에 맡기면 비자명 소멸자면 `bad-free`, `int` 면 `alloc-dealloc-mismatch`** — 배열 쿠키 8바이트가 가른다.
- ★★ **`release()` 는 해제가 아니다** — 반환값을 버리면 **경고 0건에 `Direct leak`**.

## 관련 자료

- [`c-cpp-csharp.md`](../../../c-cpp-csharp.md) — ★★★ **논증의 정본.** 「`unique_ptr` 은 소유권이 하나임을 타입으로 표현한다」 · 「RAII 는 누가 해제하는가에 답하지만 누가 아직 보고 있는가에는 답하지 않는다」. 여기는 **API 사용**까지.
- [27번](../27-shared-ptr-and-reference-counting/) — ★★★ **이 편과 한 사슬.** 소유자가 여럿이면 무엇을 치르나 — 제어 블록.
- [15번](../15-raii-resources-as-types/) (5) — 삭제자 호출 횟수(빈 것 0 · `release` 0 · `reset` 2)와 첫 크기 표.
- [17번](../17-move-constructor-assignment-and-moved-from-state/) (4)(5)(6)(8) — 이동 후 `nullptr` 보장 · 이동이 복사로 떨어지는 자리 · 반환의 `std::move` · 러스트의 컴파일 거부.
- [18번](../18-rule-of-zero-three-five-default-delete/) — `<type_traits>` 격자 형식과 0의 법칙.
- [20번](../20-virtual-destructors-and-polymorphic-deletion/) (1) — `unique_ptr<Base>` 의 삭제자가 `default_delete<Base>` 라 `~Base` 만 도는 것.
- [16번](../16-copy-constructor-and-copy-assignment/) (2) — 의무 생략과 재량 생략의 선.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **8번**([`08-ownership-and-move/`](../../../rust/syntax/08-ownership-and-move/)) — ★★ **이동 후 원본을 쓰면 컴파일 에러**인 언어. C++ 은 이동 후 원본을 **쓸 수 있고(널이다)**, Rust 는 **이름째 못 쓴다.** `Box<T>` 는 목록의 **40번**(폴더 없음) — 이 편은 던지지 않았다.

## 용어 풀이

> **소유권(ownership)** — 「이 자원을 **누가 해제하나**」에 대한 답. `unique_ptr` 는 **그 답이 하나**임을 타입으로 강제한다.\
> 예: (1)의 복사 에러 3 · 3.

> **이동 전용 타입(move-only type)** — 복사는 지워지고 이동만 되는 타입.\
> 예: (1)의 타입 특성 `0 1 0 1`.

> **의무 생략(guaranteed copy elision)** — C++17. prvalue 로 초기화할 때 **복사·이동을 아예 하지 않는** 것. 끌 수 없다.\
> 예: (2)의 `(1)` 이 생략을 꺼도 0회.

> **빈 기반 최적화(EBO)** — 빈 클래스를 기반(또는 `[[no_unique_address]]` 멤버)으로 두면 **0바이트**를 차지하게 하는 최적화.\
> 예: (3)의 빈 삭제자 세 칸이 8.

> **배열 쿠키(array cookie)** — 비자명 소멸자 타입의 `new T[n]` 이 **원소 수를 앞에 적어 두는 자리**. `delete[]` 가 그것을 읽는다.\
> 예: (4)의 `located 8 bytes inside of 20-byte region`.

> **sink 매개변수** — 소유권을 **가져가는** 매개변수. `unique_ptr<T>` 를 값으로 받는다.\
> 예: (6)의 `by_value`.

## 더 들어가면

- **`unique_ptr<Base>` 와 가상 소멸자** — [20번](../20-virtual-destructors-and-polymorphic-deletion/)이 정본이다.
- **`std::out_ptr`·`inout_ptr`(C++23)** — C API 가 `T**` 로 받는 자리에 `unique_ptr` 를 넘기는 어댑터. 이 문서는 던지지 않았다.
- **`unique_ptr` 를 `shared_ptr` 로** — `shared_ptr<T>(std::move(up))` 이 된다. 할당이 **한 번 더** 생긴다 — [27번](../27-shared-ptr-and-reference-counting/) (1)의 `(4)`.
- **pimpl 과 불완전 타입** — `unique_ptr<Impl>` 멤버는 **소멸자를 `.cpp` 에 정의**해야 한다(삭제자가 완전한 타입을 요구한다). 이 문서는 던지지 않았다.
