# cpp/syntax/29 — `new`/`delete` 와 raw 포인터가 남는 자리 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·리포트·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 소스는 질문 파일과 같다(출력 블록의 배너에 파일 이름이 있다).\
> ★ ASan 블록은 마커를 `stderr` 로 찍었고, 자른 블록은 **자르는 명령을 배너에** 적었다. 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **ASan 의 PID·주소 · clang + ASan 이 (2) 누수를 보고한 판의 수**다.\
> 근거로 쓰는 것은 다음이다 — **격자 칸의 도구 이름 · 「N / 42」 · 호출 수 · 예외 이름 · ASan 오류 종류 · `run exit`**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 경고는 **(3) 짝 불일치 세 열 + (6)을 `-O2` 에서만** · ASan 은 **여섯 다 잡는데 clang 은 (2) 누수를 놓친다** · 분석기는 **(4)를 둘 다 놓치고**, `-fanalyzer` 는 **없는 널을 5칸**

**출력**

```text
===== bash raw-grid.sh (exit=0) =====
(1) g++ -Wall -O0        -
(1) g++ -Wall -O2        -
(1) clang++ -Wall        -
(1) g++ -fanalyzer     O -Wanalyzer-possible-null-argument,-Wanalyzer-use-after-free
(1) clang++ --analyze  O cplusplus.NewDelete
(1) g++ ASan           O double-free
(1) clang++ ASan       O double-free
(2) g++ -Wall -O0        -
(2) g++ -Wall -O2        -
(2) clang++ -Wall        -
(2) g++ -fanalyzer     O -Wanalyzer-malloc-leak,-Wanalyzer-possible-null-argument
(2) clang++ --analyze  O cplusplus.NewDeleteLeaks
(2) g++ ASan           O Direct-leak
(2) clang++ ASan         -
(3) g++ -Wall -O0      O -Wmismatched-new-delete
(3) g++ -Wall -O2      O -Wmismatched-new-delete
(3) clang++ -Wall      O -Wmismatched-new-delete
(3) g++ -fanalyzer       -Wanalyzer-malloc-leak,-Wanalyzer-possible-null-dereference
(3) clang++ --analyze  O unix.MismatchedDeallocator
(3) g++ ASan           O bad-free
(3) clang++ ASan       O bad-free
(4) g++ -Wall -O0        -
(4) g++ -Wall -O2        -
(4) clang++ -Wall        -
(4) g++ -fanalyzer       -Wanalyzer-possible-null-argument
(4) clang++ --analyze    -
(4) g++ ASan           O Direct-leak
(4) clang++ ASan       O Direct-leak
(5) g++ -Wall -O0        -
(5) g++ -Wall -O2        -
(5) clang++ -Wall        -
(5) g++ -fanalyzer     O -Wanalyzer-mismatching-deallocation
(5) clang++ --analyze  O unix.MismatchedDeallocator
(5) g++ ASan           O alloc-dealloc-mismatch
(5) clang++ ASan       O alloc-dealloc-mismatch
(6) g++ -Wall -O0        -
(6) g++ -Wall -O2      O -Wuse-after-free
(6) clang++ -Wall        -
(6) g++ -fanalyzer     O -Wanalyzer-possible-null-argument,-Wanalyzer-use-after-free
(6) clang++ --analyze  O cplusplus.NewDelete
(6) g++ ASan           O heap-use-after-free
(6) clang++ ASan       O heap-use-after-free
사고를 제 이름으로 댄 칸 24 / 42 · 없는 널을 짚은 칸 5
```

```text
===== clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DACC=2 raw01.cpp -o exa && n=0; for i in 1 2 3 4 5 6 7 8 9 10; do r=$(./exa 2>&1); case $r in *'SUMMARY: AddressSanitizer'*) n=$((n+1));; esac; done; echo "clang + ASan (2) 10판 중 리포트가 나온 판 $n" (exit=0) =====
clang + ASan (2) 10판 중 리포트가 나온 판 0
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DACC=2 raw01.cpp -o exa && n=0; for i in 1 2 3 4 5 6 7 8 9 10; do r=$(./exa 2>&1); case $r in *'SUMMARY: AddressSanitizer'*) n=$((n+1));; esac; done; echo "g++   + ASan (2) 10판 중 리포트가 나온 판 $n" (exit=0) =====
g++   + ASan (2) 10판 중 리포트가 나온 판 10
```

**왜 그런가**

- ★★★ **경고는 한 줄 안에서 보이는 짝만 본다** — `new[]` 로 받은 이름을 `delete` 하는 것(3). `-O2` 에서 흐름을 조금 더 따라가 **(6) 해제 뒤 읽기**를 본다(`-Wuse-after-free`).
- ★★★ **분석기는 경로를 따라가지만 예외 경로는 못 따라갔다** — (4)가 두 분석기 모두 비었다. `-fanalyzer` 는 **던지는 `new` 를 널 가능으로** 보아 헛짚었다.
- ★★★ **ASan 은 실행이 지나간 경로만 본다 — 그래서 (4)를 잡는다.** 그런데 **누수 판정은 보수적 스캔**이라 clang 판이 (2)를 **10판 모두** 놓쳤다(수는 흔들리는 칸).

### 2. ★★★ raw 판 **`delete` 1 · `_Unwind_Resume` 0**, `unique_ptr` 판 **`delete` 2 · `_Unwind_Resume` 1** — 두 컴파일러 같다 · 1번의 **(4) 예외 경로 누수**

**출력**

```text
===== bash raw-asm.sh (exit=0) =====
g++      RAW     operator new 1 · operator delete 1 · _Unwind_Resume 0
g++      UNIQUE  operator new 1 · operator delete 2 · _Unwind_Resume 1
clang++  RAW     operator new 1 · operator delete 1 · _Unwind_Resume 0
clang++  UNIQUE  operator new 1 · operator delete 2 · _Unwind_Resume 1
```

**왜 그런가**

- ★★★ **raw 포인터에는 소멸자가 없어** 되감기가 할 일이 없다 — 던지면 **정리 없이 호출자로** 나간다.
- ★★★ **`unique_ptr` 는 지역 객체라 되감기 중 소멸자가 돈다** — 그 경로가 두 번째 `operator delete` 와 `_Unwind_Resume` 이다.

### 3. ★★ `16` 은 **둘 다 성공** · 2^62 와 `-1` 은 **`catch bad_alloc` · `q==nullptr 1`** · ASan 빌드에서는 **`(1)` 줄이 없다 — `allocation-size-too-big` 으로 죽는다**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic raw02.cpp -o ex && ./ex 16 2>&1 (cc exit=0 · run exit=0) =====
n = 16
(1) new char[n]                  성공 · p==nullptr 0
(2) new (std::nothrow) char[n]   q==nullptr 0
===== g++ -std=c++20 -Wall -Wextra -pedantic raw02.cpp -o ex && ./ex 4611686018427387904 2>&1 (cc exit=0 · run exit=0) =====
n = 4611686018427387904
(1) new char[n]                  catch bad_alloc: std::bad_alloc
(2) new (std::nothrow) char[n]   q==nullptr 1
===== g++ -std=c++20 -Wall -Wextra -pedantic raw02.cpp -o ex && ./ex -1 2>&1 (cc exit=0 · run exit=0) =====
n = -1
(1) new char[n]                  catch bad_alloc: std::bad_alloc
(2) new (std::nothrow) char[n]   q==nullptr 1
```

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw02.cpp -o exa && ./exa 4611686018427387904 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=1) =====
n = 4611686018427387904
=================================================================
==3371847==ERROR: AddressSanitizer: requested allocation size 0x4000000000000000 (0x4000000000001000 after adjustments for alignment, red zones etc.) exceeds maximum supported size of 0x10000000000 (thread T0)
    #0 0x7a762d2fe6c8 in operator new[](unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:98
    #1 0x647dd4138392 in main raw02.cpp:12

==3371847==HINT: if you don't care about these errors you may set allocator_may_return_null=1
SUMMARY: AddressSanitizer: allocation-size-too-big ../../../../src/libsanitizer/asan/asan_new_delete.cpp:98 in operator new[](unsigned long)
```

```text
===== echo "g++   $(g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw02.cpp -o exa 2>&1; ./exa 4611686018427387904 2>&1 | grep -oE '^SUMMARY: AddressSanitizer: [a-z-]+')" (exit=0) =====
g++   SUMMARY: AddressSanitizer: allocation-size-too-big
===== echo "clang $(clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw02.cpp -o exa 2>&1; ./exa 4611686018427387904 2>&1 | grep -oE '^SUMMARY: AddressSanitizer: [a-z-]+')" (exit=0) =====
clang SUMMARY: AddressSanitizer: allocation-size-too-big
```

**왜 그런가**

- ★★★ **던지는 `new` 는 실패를 예외로, `nothrow` 는 `nullptr` 로** 알린다.
- ★★ **`-1` 은 `bad_array_new_length` 핸들러가 아니라 `bad_alloc` 핸들러가 잡았다** — 두 컴파일러 다(9번).
- ★★★ **ASan 의 할당자는 한도를 넘는 요청을 예외로 돌려주지 않고 리포트로 죽인다** — `catch` 까지 가지 못한다.

### 4. ★★★ `c` 는 **`free` → `fclose` · 8 · 8** · **`p` 만 `heap-use-after-free`**(`i` 는 침묵) · `t` 는 **`~Node r` → `~Node x` → `~Node y`** — 자식은 **부모보다 먼저** 죽는다

**출력**

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw04.cpp -o exa && ./exa o 2>&1 (cc exit=0 · run exit=0) =====
(o) unique_ptr 가 소유하고 show() 는 .get() 을 받는다
    show: 7
    show: -1
    main 끝
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw04.cpp -o exa && ./exa c 2>&1 (cc exit=0 · run exit=0) =====
(c) fopen · strdup 의 결과를 삭제자 달린 unique_ptr 로 받는다
    sizeof 두 unique_ptr = 8 · 8
    free
    fclose
    main 끝
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw04.cpp -o exa && ./exa i 2>&1 (cc exit=0 · run exit=0) =====
(i) vector 원소를 인덱스로 들고 push_back 한다
    v[first].v = 1
    main 끝
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw04.cpp -o exa && ./exa t 2>&1 (cc exit=0 · run exit=0) =====
(t) 부모 r · 자식 x · 손자 y — 손자에서 뿌리까지 raw 포인터로 올라간다
    y -> x -> r
      ~Node r
      ~Node x
      ~Node y
    main 끝
```

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw04.cpp -o exa && ./exa p 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' | grep -vE '^(Shadow|  [A-Z]|  0x|=>0x)' (cc exit=0 · run exit=1) =====
(p) vector 원소를 raw 포인터로 들고 push_back 한다
=================================================================
==3371987==ERROR: AddressSanitizer: heap-use-after-free on address 0x502000000010 at pc 0x612861505c45 bp 0x7ffc44d68ec0 sp 0x7ffc44d68eb0
READ of size 4 at 0x502000000010 thread T0
    #0 0x612861505c44 in main raw04.cpp:50

0x502000000010 is located 0 bytes inside of 8-byte region [0x502000000010,0x502000000018)
freed by thread T0 here:
    #0 0x723b566ff5e8 in operator delete(void*, unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:164
    #1 0x61286150bb80 in std::__new_allocator<W>::deallocate(W*, unsigned long) /usr/include/c++/13/bits/new_allocator.h:172
    #2 0x612861508e7a in std::allocator<W>::deallocate(W*, unsigned long) /usr/include/c++/13/bits/allocator.h:210
    #3 0x612861508e7a in std::allocator_traits<std::allocator<W> >::deallocate(std::allocator<W>&, W*, unsigned long) /usr/include/c++/13/bits/alloc_traits.h:517
    #4 0x612861508e7a in std::_Vector_base<W, std::allocator<W> >::_M_deallocate(W*, unsigned long) /usr/include/c++/13/bits/stl_vector.h:390
    #5 0x61286150a7db in void std::vector<W, std::allocator<W> >::_M_realloc_insert<W>(__gnu_cxx::__normal_iterator<W*, std::vector<W, std::allocator<W> > >, W&&) /usr/include/c++/13/bits/vector.tcc:519
    #6 0x61286150906e in W& std::vector<W, std::allocator<W> >::emplace_back<W>(W&&) /usr/include/c++/13/bits/vector.tcc:123
    #7 0x61286150824d in std::vector<W, std::allocator<W> >::push_back(W&&) /usr/include/c++/13/bits/stl_vector.h:1299
    #8 0x612861505be2 in main raw04.cpp:49

previously allocated by thread T0 here:
    #0 0x723b566fe548 in operator new(unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:95
    #1 0x612861508175 in std::__new_allocator<W>::allocate(unsigned long, void const*) /usr/include/c++/13/bits/new_allocator.h:151
    #2 0x6128615074c5 in std::allocator<W>::allocate(unsigned long) /usr/include/c++/13/bits/allocator.h:198
    #3 0x6128615074c5 in std::allocator_traits<std::allocator<W> >::allocate(std::allocator<W>&, unsigned long) /usr/include/c++/13/bits/alloc_traits.h:482
    #4 0x6128615074c5 in std::_Vector_base<W, std::allocator<W> >::_M_allocate(unsigned long) /usr/include/c++/13/bits/stl_vector.h:381
    #5 0x612861506db3 in void std::vector<W, std::allocator<W> >::_M_range_initialize<W const*>(W const*, W const*, std::forward_iterator_tag) /usr/include/c++/13/bits/stl_vector.h:1692
    #6 0x6128615069c6 in std::vector<W, std::allocator<W> >::vector(std::initializer_list<W>, std::allocator<W> const&) /usr/include/c++/13/bits/stl_vector.h:682
    #7 0x612861505b27 in main raw04.cpp:47

SUMMARY: AddressSanitizer: heap-use-after-free raw04.cpp:50 in main
```

```text
===== echo "clang o · c · i · t · p : $(clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw04.cpp -o exa 2>&1; for m in o c i t p; do ./exa $m >/dev/null 2>&1; printf '%s ' $?; done)" (exit=0) =====
clang o · c · i · t · p : 0 0 0 0 1 
```

**왜 그런가**

- ★★ **지역 `unique_ptr` 두 개는 선언 역순으로** 죽는다 — `s`(free) 가 먼저. 삭제자가 빈 함수 객체라 **8바이트**다.
- ★★★ **`push_back` 의 재할당이 옛 버퍼를 지웠다** — 포인터는 옛 버퍼를, 인덱스는 「**몇 번째**」를 기억한다.
- ★★★ **`~Node r` 본체 → `kids` 파괴(`~Node x` → 그 `kids` → `~Node y`)** — 자식은 부모 **안에서** 죽으므로 `parent` 가 가리키는 부모는 **자식보다 오래 산다.**

### 5. ★★ **두 ASan 모두 리포트 0줄 · `run exit=0`**

**출력**

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw05.cpp -o exa && ./exa 2>&1 (cc exit=0 · run exit=0) =====
write_once() 에서 돌아왔다
===== clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw05.cpp -o exa && ./exa 2>&1 (cc exit=0 · run exit=0) =====
write_once() 에서 돌아왔다
```

**왜 그런가**

- ★★★ **열린 `FILE` 은 C 라이브러리의 스트림 목록에서 닿는다** — LSan 이 보기에 누수가 아니다(구현에 대한 내 읽기 · 실측은 「침묵」).
- ★★ **ASan 은 「닫았나」를 묻지 않는다** — 15편의 「파일 핸들은 못 본다」가 **메모리로 만든 핸들에도** 맞았다.

### 6. ★★★ **`delete p;` 가 `throw` 뒤에 있어 한 번도 실행되지 않았고, raw 포인터에는 되감기 때 돌 소멸자가 없다** — 2번의 **raw 판 `_Unwind_Resume` 0**

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DACC=4 raw01.cpp -o exa && ./exa 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=1) =====
(4) new 와 delete 사이에서 예외가 난다
    catch: work 실패
    accident() 에서 돌아왔다

=================================================================
==3371661==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 4 byte(s) in 1 object(s) allocated from:
    #0 0x73668e2fe548 in operator new(unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:95
    #1 0x5afba50cd449 in accident() raw01.cpp:31
    #2 0x5afba50cd583 in main raw01.cpp:51

SUMMARY: AddressSanitizer: 4 byte(s) leaked in 1 allocation(s).
```

- ★★★ **예외를 잡는 것(제어 흐름)과 자원을 돌려주는 것(소유)은 다른 일**이다. 소유가 **지역 객체의 타입**에 있어야 되감기가 돌려준다.

### 7. ★★★ **관찰자 매개변수(호출자) · C API 경계(삭제자) · 인덱스(컨테이너) · 부모 포인터(구조)** — 넷 다 **소유하지 않고**, 수명을 **누군가 보장**한다

- ★★★ `p` 판은 **소유하지 않는데 수명을 아무도 보장하지 않는다** — `vector` 는 원소의 **주소**가 아니라 **값**만 지킨다. 재할당이 옛 주소를 지운다.
- ★★ **`delete` 하는 raw 포인터**는 소유하는데 보장이 **사람의 기억**이다 — 1번의 여섯.

### 8. ★★★ 경고는 **이중 해제·누수·예외 경로** · 분석기는 **(4) 예외 경로** · ASan 은 **clang 의 (2) 누수와 안 닫은 `FILE`** · 할당 실패는 **ASan 이 예외 대신 죽여서** 시험할 수 없다

- ★★★ **세 창이 서로 다른 칸을 비운다** — 하나만 믿으면 그 칸이 샌다.
- ★ ASan 빌드의 할당 실패는 **프로그램 동작 자체를 바꾼다**(3번) — 「`bad_alloc` 을 잡는 코드」가 **돌 기회가 없다.**

### 9. ★★ cppreference 는 **음수면 `bad_array_new_length` 와 맞는 예외**라 적는데, 이 판은 **그 핸들러를 건너 `bad_alloc` 핸들러**가 잡았다 · **표준 원문을 열지 못해** 판정하지 않았다

- ★★ 이 문서가 연 것은 **cppreference 한 쪽**이다. 그것과 다른 관찰은 「**문서와 다른 관찰**」로 적는다 — **구현이 틀렸다는 판정에는 원문 조항이 필요하다**(제3의 상태).
- ★ 「두 컴파일러에서 같았다」도 보장이 아니다 — **둘 다 libstdc++ 13 의 같은 `operator new[]`** 를 쓴다.

### 10. 다른 주제와 잇기

- ★★ 20편 (6)은 **파생 배열을 기반 포인터로 `delete[]`** 한 사고다. **`new[]` + `delete`** 는 **14편 (6)**(g++ `run exit=134`)이 정본이고, 이 편 1번의 (3)이 ASan `bad-free` 칸이다.
- ★★ **재현되지 않았다**(26편 (7) — 두 컴파일러가 끼워 넣는 순서를 고르지 않았다). 같은 문제인 이유 — 둘 다 **「`new` 와 소유자 생성 사이에 던지는 호출」** 이고, 2번이 **그 사이에 정리 경로가 없다는 것**을 기계어로 보였다.
- ★ [`c-cpp-csharp.md`](../../../c-cpp-csharp.md) 의 「C++ — RAII는 해제를 잊는 실패를 지우고, 죽은 것을 가리키는 실패는 못 지운다」 절.

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `raw01.cpp` + `raw-grid.sh` | 사고 6 × 도구 7 = 42칸 | ★★★ **24 / 42** · 헛짚음 5 |
| `raw01.cpp` (2) 반복 | 두 컴파일러 ASan × 10판 | ★★ clang **0** · g++ **10** (흔들리는 칸) |
| `raw01.cpp` (4) 전문 | g++ ASan 1판 | ★★ `catch` 뒤 `Direct leak of 4 byte(s)` |
| `raw03.cpp` + `raw-asm.sh` | 두 컴파일러 × 두 판 `-O2 -S` | ★★★ **delete 1 · 2 · `_Unwind_Resume` 0 · 1** |
| `raw02.cpp` | g++ 세 크기 · clang 두 크기 · ASan 두 컴파일러 | ★★★ **`bad_alloc` · `nullptr`** · ASan **`allocation-size-too-big`** |
| `raw04.cpp` | g++ ASan 다섯 판 + clang 종료 코드 | ★★★ **`p` 만 `heap-use-after-free`** |
| `raw05.cpp` | 두 컴파일러 ASan | ★★ **침묵** |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · glibc · libstdc++ 13)에서만** 그렇다.

- ★★★ **격자의 도구별 칸** · **clang + ASan 의 (2) 침묵** · **되감기 경로의 모양** · **2^62 가 실패하는 것** · **음수 크기가 `bad_alloc` 인 것** · **`FILE` 이 LSan 에 안 보이는 것**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **던지는 `new` 의 실패는 예외, `nothrow` 는 `nullptr`** · **되감기 중 지역 객체의 소멸자** · **이중 해제·짝 불일치·해제 뒤 사용은 UB** · **누수는 UB 가 아니다.**

**안 돌려 본 것 / 못 잰 것**

- **못 잰 것** — ★★ **음수 크기 `new[]` 의 층 판정**(표준 원문을 열지 못했다) · ★ **clang + ASan 이 (2)를 놓치는 정확한 이유.**
- **안 돌려 본 것** — ★ **ASan 없는 UB 실행 값**(일부러 싣지 않았다) · ★ **`set_new_handler`** · ★ **placement new.**
- ★ **「인용한 창」** — 삭제자 크기(26편 (3)).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **1번** — 분석기·경고의 칸이 가장 빨리 바뀐다(특히 `-fanalyzer` 의 헛짚음).
- ★★ **3번** — 음수 크기가 `bad_array_new_length` 가 되는지.
- ★ **5번** — LSan 이 스트림을 보게 되는지.
