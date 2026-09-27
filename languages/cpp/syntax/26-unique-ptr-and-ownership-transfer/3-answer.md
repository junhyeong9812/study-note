# cpp/syntax/26 — `unique_ptr` 와 소유권 이동 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·리포트는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> **진단의 줄 번호는 그 파일 기준**이므로 **출력을 싣는 블록마다 그 출력을 낸 소스를 같은 자리에** 뒀다(소스는 질문 파일과 같다).\
> ★ ASan 블록은 마커를 `stderr` 로 찍었고, 자른 블록은 **자르는 명령을 배너에** 적었다. 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **ASan 의 PID·주소 · 진단 문구**다.\
> 근거로 쓰는 것은 다음이다 — **에러 줄·개수 · `cc exit`/`run exit` · 삭제자 이동 횟수 · `sizeof` · 타입 특성 0/1 · ASan 오류 이름 · 소멸자 로그**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **1·2·3번이 에러**(4번 `std::move` 는 통과) · grep 하면 **g++ 3 · clang 0** · 헤더 줄은 **`unique_ptr(const unique_ptr&) = delete;`**

**출력**

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

**왜 그런가**

- ★★★ **복사 생성·복사 대입이 libstdc++ 헤더 522·523 줄에서 `= delete`** 다 — 「소유자가 하나」가 **선언**에 적혀 있다.
- ★★ **clang 은 같은 사실을 `call to deleted constructor` · `selected deleted operator '='` 로** 말한다 — **문구로 세면 0** 이 되니 근거는 **줄과 개수(3 · 3)다**.
- ★ 4번은 **이동 생성자**가 후보가 되어 통과한다(clang 의 후보 목록에 `expects an rvalue` 로 보인다).

### 2. ★★ **`0 1 0 1 1`** · `shared_ptr` 와 **갈린 칸 2 / 5**(복사 생성·복사 대입)

**출력**

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

**왜 그런가**

- ★★ **복사 둘은 0, 이동 둘은 1, `noexcept` 이동도 1** — 이동 전용 타입이다. `noexcept` 이동이라 `vector<unique_ptr<T>>` 는 재할당 때 **이동**한다([17번](../17-move-constructor-assignment-and-moved-from-state/) (3)).
- ★ `shared_ptr` 는 **다섯 다 1** — 복사가 **공유**라는 뜻이다(27번).

### 3. ★★★ **`0 · 0 · 1 · 1`** · 생략을 끄면 **(2)만 0 → 1**, **(1)은 0 그대로** · C++14 로 끄면 **(1)이 2**

**출력**

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

**왜 그런가**

- ★★★ **(1) prvalue 반환은 C++17 의 의무 생략** — 옮기는 동작 자체가 없어 **스위치로 끌 수 없다.** (2) 이름 있는 지역(NRVO)은 **재량**이라 끄면 1회가 드러난다.
- ★★ **(3) `return std::move(p)` 는 생략을 스스로 막아 1회** — 두 컴파일러가 `-Wpessimizing-move` 로 경고한다.
- ★★ **C++14 에는 의무 생략이 없다** — 끄면 **반환값 1 + 받는 변수 1 = 2회**.

### 4. ★★★ **`8 8 8 16 16 16 16 32 16 40`** — **커진 칸 7 / 10** · 캡처 없는 람다 **8** 대 함수 포인터 **16** · `EmptyDel&` 는 **1 인데 16**

**출력**

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

```text
===== grep -n 'tuple<pointer, _Dp> _M_t;' /usr/include/c++/13/bits/unique_ptr.h (exit=0) =====
232:      tuple<pointer, _Dp> _M_t;
```

**왜 그런가**

- ★★★ **상태 없는 삭제자는 EBO 로 0바이트** — libstdc++ 가 `tuple<pointer, _Dp>` 에 담는다(헤더 232줄).
- ★★★ **캡처 없는 람다는 「어느 함수」가 타입에 있고, 함수 포인터는 값에 있다** — 그래서 8 과 16.
- ★ **`sizeof(D&)` 는 가리키는 타입(`EmptyDel`, 1)의 크기**를 돌려주지만, 멤버 참조는 **포인터 하나(8)** 를 차지한다 — `sizeof(D)` 칸은 이 줄에서 **삭제자 몫을 말하지 않는다.**

### 5. ★★★ `a` 는 **`~Cell` 3번** · `s` 는 **`bad-free`**, `i` 는 **`alloc-dealloc-mismatch`** — **이름이 다르다** · `s` 의 `~Cell` 은 **1번**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic uptr05.cpp -o ex && ./ex a 2>&1 (cc exit=0 · run exit=0) =====
(a) unique_ptr<Cell[]>(new Cell[3])
    p[1].id = 7
      ~Cell
      ~Cell
      ~Cell
    블록을 나왔다
```

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

**왜 그런가**

- ★★★ **`Cell` 은 소멸자가 있어 배열 쿠키(원소 수 8바이트)가 앞에 붙는다** — 받은 포인터가 **8바이트 안쪽**이라 `delete` 가 「**malloc 한 주소가 아니다**」(`bad-free`)가 된다.
- ★★ **`int` 는 쿠키가 없어** 주소는 맞고 **`new[]`/`delete` 짝만 틀렸다**(`alloc-dealloc-mismatch`).
- ★ **clang + ASan 도 같은 두 이름** — 이 검사는 크기를 안 쓰므로 20편의 type-mismatch 처럼 새지 않는다.

### 6. ★★ **`a` 는 빈 것 · `b` 는 새 `Res(102)` · `c` 는 `v=4`** · `const` 인데도 **바뀐다** · 끝에 **`~Res(5)` → `~Res(4)` → `~Res(102)`**

**출력**

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

**왜 그런가**

- ★★★ **값으로 받으면 소유권이 넘어가** `~Res(1)` 이 **함수 안에서** 돈다 — `a` 는 **`nullptr`**(표준 보장).
- ★★★ **`const unique_ptr&` 의 `const` 는 포인터 객체에 붙었다** — 가리키는 `Res` 는 `const` 가 아니다(얕은 `const`).
- ★ 끝의 세 줄은 **`main` 지역의 역순 파괴** — `d`(5) → `c`(4) → `b`(102).

### 7. ★★★ **경고 0 · 0** · ASan **`Direct leak of 8 byte(s)`**(두 컴파일러) · `p.get()` 은 **`nullptr`** · 불렀어야 할 것은 **`reset()`**

**출력**

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
===== echo "g++   -Wall -Wextra -pedantic 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic -c uptr06.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
g++   -Wall -Wextra -pedantic 경고 0
===== echo "clang -Wall -Wextra -pedantic 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic -c uptr06.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
clang -Wall -Wextra -pedantic 경고 0
```

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

**왜 그런가**

- ★★★ **`release()` 는 소유권 포기**다 — 포인터를 돌려주고 자기는 비운다. 받은 쪽이 버리면 **아무도 소유하지 않는다.**
- ★★ **이 판의 선언에 `[[nodiscard]]` 가 없어** 컴파일러가 버린 것을 모른다.

### 8. ★★ **`reset()` 과 `std::move(p)` 가 막히고 `*p = 5` 는 통과**

**출력**

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

**왜 그런가**

- ★★ **`reset()` 은 비`const` 멤버**라 `const` 객체에서 못 부른다.
- ★★ **`std::move(p)` 는 `const unique_ptr&&`** 가 되어 이동 생성자(`unique_ptr&&`)에 안 맞고 **복사 생성자로 떨어지는데 복사는 지워져 있다** — [17번](../17-move-constructor-assignment-and-moved-from-state/) (5)의 「이동이 복사로 조용히 되돌아가는 자리」가 **여기서는 에러로** 드러났다.

### 9. ★★ **두 판 다 안 샌다 · 순서는 반대**(g++ `g()` 먼저 · clang `new W` 먼저) — 걱정은 **이 두 구현에서 재현되지 않을 뿐**이고, **순서를 손으로 풀어 쓰면 샌다** · C++11 은 **`make_unique` 가 없다**

**출력**

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

**왜 그런가**

- ★★ **어느 구현도 `new W` 와 `unique_ptr` 생성 사이에 `g()` 를 끼우지 않았다** — 사고의 조건이 **이 머신에서는 안 생긴다**(못 잰 것 — 제3의 상태).
- ★★ **그 순서를 손으로 쓰면 `Direct leak of 1 byte(s)`** — 조건이 생기면 샌다는 조각이다. **`make_unique` 는 `new` 를 식에서 없애** 조건 자체를 지운다.

### 10. ★★ **`unique_ptr` 는 「표준」(`get() == nullptr` 명시), `string` 은 「유효하되 미지정」**(값은 구현)

- ★★ [17번](../17-move-constructor-assignment-and-moved-from-state/) (4)가 **한 블록에서 두 층을 갈라** 찍었다 — `u1.get() == nullptr : 1 (표준 보장)` 대 libstdc++ 가 고른 `size=0`.
- ★ 그래서 이동한 `unique_ptr` 에는 **`== nullptr` 검사 · `reset` · 대입**을 해도 된다. `*` 는 **널 역참조**라 안 된다.

### 11. 다른 주제와 잇기

- ★★★ **[`c-cpp-csharp.md`](../../../c-cpp-csharp.md)** — 「**누가 해제하는가**에는 답하지만 **누가 아직 보고 있는가**에는 답하지 않는다」. 6번의 `by_raw` 가 그 「보고 있는 쪽」이다.
- ★★ **[27번](../27-shared-ptr-and-reference-counting/)** — 제어 블록 · 할당 한 번 더 · 원자 명령.
- ★ Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **8번**([`08-ownership-and-move/`](../../../rust/syntax/08-ownership-and-move/)) — 이동 후 원본을 **이름째 못 쓰게** 컴파일에서 막는다(17편 (8)도 인용했다).

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `uptr01.cpp` 복사 | g++ · clang 각 1회 + 문구 세기 | ★★★ **에러 3 · 3** · `use of deleted function` **3 · 0** |
| `uptr02.cpp` 타입 특성 | g++ 1회 | ★★ **`0 1 0 1 1`** · 갈린 칸 **2 / 5** |
| `uptr03.cpp` 팩토리 | g++ C++20 · 두 컴파일러 생략 끔 · g++ C++14 생략 끔 | ★★★ **`0 0 1 1` → `0 1 1 1` → `2 2 2 3`** |
| `uptr04.cpp` 삭제자 크기 | g++ · clang 각 1회 + 헤더 줄 | ★★★ **커진 칸 7 / 10** |
| `uptr05.cpp`·`uptr10.cpp` 배열 | 실행 1 · 에러 2 · ASan g++ 2 · clang 1 · 이름 세기 2 | ★★ **`~Cell` 3 · 1** · **`bad-free` · `alloc-dealloc-mismatch`** |
| `uptr06.cpp` `release` | ASan g++ 3판 · clang 1판 · 경고 2 · 헤더 줄 | ★★★ **`Direct leak` 8바이트** · 경고 **0 · 0** |
| `uptr07.cpp`·`uptr09.cpp` 인자 | 실행 1 · 에러 2 | ★★ `const&` 로 **`v=4`** · 막힘 **2 · 2** |
| `uptr08.cpp`·`uptr11.cpp` 판 경계 | C++14 ASan 두 컴파일러 + 손 순서 1 · C++11 두 컴파일러 | ★★ **안 샘 · 순서 반대** · 손 순서 **1바이트 샘** · C++11 **에러** |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · libstdc++ 13)에서만** 그렇다.

- ★★★ **`sizeof` 격자 전부**(EBO 배치는 표준 약속이 아니다) · **배열 쿠키 8바이트** · **함수 인자 평가 순서** · **`release()` 에 `[[nodiscard]]` 가 없는 것.**

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **복사가 지워져 있다** · **이동 후 `nullptr`** · **prvalue 반환의 의무 생략(C++17)** · **`T[]` 판은 `delete[]`** · **`release()` 는 삭제자를 안 부른다.**

**안 돌려 본 것 / 못 잰 것**

- **못 잰 것** — ★★ **C++14 인자 끼워 넣기 누수**: 끼워 넣는 구현이 이 머신에 없다. 조각(손 순서)만 쟀다.
- **안 돌려 본 것** — ★ **pimpl 의 불완전 타입** · ★ **`out_ptr`(C++23)** · ★ **Rust `Box<T>`**(40번, 폴더 없음).
- ★ **「부적용인 창」** — `-O2` 어셈블리. **27번이 `UNIQUE` 판으로 `lock 접두 0개` 를 같이 센다**(제5의 상태).
- ★ **cppreference 의 해당 쪽들을 이 배치에서 열지 못했다**(도구 한도) — 규칙은 **헤더 줄과 실행**으로만 적었다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **7번** — libstdc++ 가 `release()` 에 `[[nodiscard]]` 를 붙이면 경고가 생긴다.
- ★ **4번** — `tuple` 대신 `[[no_unique_address]]` 로 바뀌어도 숫자가 같은지.
