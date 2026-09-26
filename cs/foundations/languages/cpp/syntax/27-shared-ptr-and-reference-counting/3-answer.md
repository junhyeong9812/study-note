# cpp/syntax/27 — `shared_ptr` 와 참조 계수 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·리포트·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · x86-64 Linux · rustc 1.92.0 · Python 3.12.3 에서 실제로 돌려 얻은 것이다.\
> 소스는 질문 파일과 같다(출력 블록의 배너에 파일 이름이 있다).\
> ★ ASan 블록은 마커를 `stderr` 로 찍었고, 자른 블록은 **자르는 명령을 배너에** 적었다. 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **ASan 의 PID·주소 · clang + ASan 이 보고한 판의 수 · 어셈블리의 레지스터·오프셋**이다.\
> 근거로 쓰는 것은 다음이다 — **할당·해제 횟수와 바이트 · `use_count()` · 소멸자 로그 · 누수 종류 · `lock` 접두 개수 · 예외·에러 이름**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **`1회 32` · `2회 40` · `1회 16` · `2회 40` · `1회 32`** — 차이는 **제어 블록**(16 대 24) · 판을 바꿔도 **안 움직인다**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic sptr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof(T) = 16
(1) std::make_shared<T>()          할당 1회 · 32바이트
(2) std::shared_ptr<T>(new T)      할당 2회 · 40바이트
(3) std::make_unique<T>()          할당 1회 · 16바이트
(4) std::shared_ptr<T>(make_unique) 할당 2회 · 40바이트
(5) 복사 한 번 더             할당 1회 · 32바이트
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic sptr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof(T) = 16
(1) std::make_shared<T>()          할당 1회 · 32바이트
(2) std::shared_ptr<T>(new T)      할당 2회 · 40바이트
(3) std::make_unique<T>()          할당 1회 · 16바이트
(4) std::shared_ptr<T>(make_unique) 할당 2회 · 40바이트
(5) 복사 한 번 더             할당 1회 · 32바이트
===== g++ -std=c++20 -O2 sptr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof(T) = 16
(1) std::make_shared<T>()          할당 1회 · 32바이트
(2) std::shared_ptr<T>(new T)      할당 2회 · 40바이트
(3) std::make_unique<T>()          할당 1회 · 16바이트
(4) std::shared_ptr<T>(make_unique) 할당 2회 · 40바이트
(5) 복사 한 번 더             할당 1회 · 32바이트
===== clang++ -std=c++20 -O2 sptr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof(T) = 16
(1) std::make_shared<T>()          할당 1회 · 32바이트
(2) std::shared_ptr<T>(new T)      할당 2회 · 40바이트
(3) std::make_unique<T>()          할당 1회 · 16바이트
(4) std::shared_ptr<T>(make_unique) 할당 2회 · 40바이트
(5) 복사 한 번 더             할당 1회 · 32바이트
```

```text
===== grep -nE '_Atomic_word  _M_(use|weak)_count;' /usr/include/c++/13/bits/shared_ptr_base.h (exit=0) =====
237:      _Atomic_word  _M_use_count;     // #shared
238:      _Atomic_word  _M_weak_count;    // #weak + (#shared != 0)
===== grep -nE '^    class _Sp_counted_(ptr|deleter|ptr_inplace) final' /usr/include/c++/13/bits/shared_ptr_base.h (exit=0) =====
419:    class _Sp_counted_ptr final : public _Sp_counted_base<_Lp>
494:    class _Sp_counted_deleter final : public _Sp_counted_base<_Lp>
580:    class _Sp_counted_ptr_inplace final : public _Sp_counted_base<_Lp>
```

**왜 그런가**

- ★★★ **`make_shared` 는 객체와 블록을 한 덩어리(`_Sp_counted_ptr_inplace`)로 한 번에** 잡는다 — 블록 몫 16(vptr 8 + 계수 4 + 4).
- ★★★ **`new T` 판은 객체(16)를 먼저 잡고 블록(`_Sp_counted_ptr`, 포인터 8 을 더 들어 24)을 따로** 잡는다.
- ★★ **`make_unique` 는 블록이 없어 16** · **복사는 할당하지 않는다**(`(5)` 도 1회 — 처음의 `make_shared` 뿐).
- ★ **계수는 판을 잘 안 탄다** — clang · `-O2` 두 판 다 한 글자도 같았다.

### 2. ★★ **`1 2 2 2 3 2 2 1`** · `~T` 는 **`(8)` 줄 뒤(`a.reset()` 에서)** — `w` 는 **살아 있다** · `l2` 는 **비었다**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic sptr02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) auto a = make_shared<T>()        a.use_count()=1
(2) auto b = a                        a.use_count()=2
(3) auto c = std::move(b)             a.use_count()=2 · b 가 비었나 1
(4) weak_ptr<T> w = a                 a.use_count()=2 · w.use_count()=2
(5) auto l = w.lock()   (블록 안)     a.use_count()=3
(6) l 이 블록을 나간 뒤               a.use_count()=2
(7) const auto& r = a                 a.use_count()=2
(8) c.reset()                         a.use_count()=1
      ~T
(9) a.reset()                         w.use_count()=0 · w.expired()=1
(10) auto l2 = w.lock()               l2 가 비었나 1
```

**왜 그런가**

- ★★★ **복사 +1 · 이동 0 · `weak_ptr` 0 · `lock()` +1(그 `shared_ptr` 가 죽으면 −1) · `const&` 0.**
- ★★★ **강한 계수가 0 이 되는 순간(`(8)` 을 찍은 뒤 `(9)` 의 `a.reset()`)** 객체가 파괴된다 — **약한 참조는 객체를 못 살린다.** 그 뒤 `lock()` 은 `nullptr`.

### 3. ★★★ **`2 · 2`** · 소멸자 **0줄** · ASan **`Indirect leak` 2건(64바이트)** · `-DASK_WEAK` 는 **`1 · 2` · 누수 0**

**출력**

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. sptr03.cpp -o exa && ./exa 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=1) =====
(1) 서로 이은 직후  p.use_count()=2 · c.use_count()=2
(2) link_pair() 에서 돌아왔다

=================================================================
==415667==ERROR: LeakSanitizer: detected memory leaks

Indirect leak of 32 byte(s) in 1 object(s) allocated from:
    #0 0x7a028bcfe548 in operator new(unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:95
    #1 0x5725035183ff in std::__new_allocator<std::_Sp_counted_ptr_inplace<Child, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> >::allocate(unsigned long, void const*) /usr/include/c++/13/bits/new_allocator.h:151
    #2 0x5725035178f8 in std::allocator<std::_Sp_counted_ptr_inplace<Child, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> >::allocate(unsigned long) /usr/include/c++/13/bits/allocator.h:198
    #3 0x5725035178f8 in std::allocator_traits<std::allocator<std::_Sp_counted_ptr_inplace<Child, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> > >::allocate(std::allocator<std::_Sp_counted_ptr_inplace<Child, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> >&, unsigned long) /usr/include/c++/13/bits/alloc_traits.h:482
    #4 0x5725035178f8 in std::__allocated_ptr<std::allocator<std::_Sp_counted_ptr_inplace<Child, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> > > std::__allocate_guarded<std::allocator<std::_Sp_counted_ptr_inplace<Child, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> > >(std::allocator<std::_Sp_counted_ptr_inplace<Child, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> >&) /usr/include/c++/13/bits/allocated_ptr.h:98
    #5 0x57250351709e in std::__shared_count<(__gnu_cxx::_Lock_policy)2>::__shared_count<Child, std::allocator<void>>(Child*&, std::_Sp_alloc_shared_tag<std::allocator<void> >) /usr/include/c++/13/bits/shared_ptr_base.h:969
    #6 0x572503516c0a in std::__shared_ptr<Child, (__gnu_cxx::_Lock_policy)2>::__shared_ptr<std::allocator<void>>(std::_Sp_alloc_shared_tag<std::allocator<void> >) /usr/include/c++/13/bits/shared_ptr_base.h:1712
    #7 0x5725035167bb in std::shared_ptr<Child>::shared_ptr<std::allocator<void>>(std::_Sp_alloc_shared_tag<std::allocator<void> >) /usr/include/c++/13/bits/shared_ptr.h:464
    #8 0x5725035161e1 in std::shared_ptr<Child> std::make_shared<Child>() /usr/include/c++/13/bits/shared_ptr.h:1010
    #9 0x572503515503 in link_pair() sptr03.cpp:22
    #10 0x572503515684 in main sptr03.cpp:29

Indirect leak of 32 byte(s) in 1 object(s) allocated from:
    #0 0x7a028bcfe548 in operator new(unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:95
    #1 0x5725035182af in std::__new_allocator<std::_Sp_counted_ptr_inplace<Parent, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> >::allocate(unsigned long, void const*) /usr/include/c++/13/bits/new_allocator.h:151
    #2 0x5725035173b3 in std::allocator<std::_Sp_counted_ptr_inplace<Parent, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> >::allocate(unsigned long) /usr/include/c++/13/bits/allocator.h:198
    #3 0x5725035173b3 in std::allocator_traits<std::allocator<std::_Sp_counted_ptr_inplace<Parent, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> > >::allocate(std::allocator<std::_Sp_counted_ptr_inplace<Parent, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> >&, unsigned long) /usr/include/c++/13/bits/alloc_traits.h:482
    #4 0x5725035173b3 in std::__allocated_ptr<std::allocator<std::_Sp_counted_ptr_inplace<Parent, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> > > std::__allocate_guarded<std::allocator<std::_Sp_counted_ptr_inplace<Parent, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> > >(std::allocator<std::_Sp_counted_ptr_inplace<Parent, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> >&) /usr/include/c++/13/bits/allocated_ptr.h:98
    #5 0x572503516e28 in std::__shared_count<(__gnu_cxx::_Lock_policy)2>::__shared_count<Parent, std::allocator<void>>(Parent*&, std::_Sp_alloc_shared_tag<std::allocator<void> >) /usr/include/c++/13/bits/shared_ptr_base.h:969
    #6 0x572503516aaa in std::__shared_ptr<Parent, (__gnu_cxx::_Lock_policy)2>::__shared_ptr<std::allocator<void>>(std::_Sp_alloc_shared_tag<std::allocator<void> >) /usr/include/c++/13/bits/shared_ptr_base.h:1712
    #7 0x5725035166b3 in std::shared_ptr<Parent>::shared_ptr<std::allocator<void>>(std::_Sp_alloc_shared_tag<std::allocator<void> >) /usr/include/c++/13/bits/shared_ptr.h:464
    #8 0x5725035160e3 in std::shared_ptr<Parent> std::make_shared<Parent>() /usr/include/c++/13/bits/shared_ptr.h:1010
    #9 0x5725035154d5 in link_pair() sptr03.cpp:21
    #10 0x572503515684 in main sptr03.cpp:29

SUMMARY: AddressSanitizer: 64 byte(s) leaked in 2 allocation(s).
```

```text
===== echo "g++ (순환) 누수 종류 : $(g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. sptr03.cpp -o exa 2>&1; ./exa 2>&1 | grep -oE '^(Direct|Indirect) leak' | sort | uniq -c | tr -s ' ' | tr '\n' ';')" (exit=0) =====
g++ (순환) 누수 종류 :  2 Indirect leak;
```

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DASK_WEAK sptr03.cpp -o exa && ./exa 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=0) =====
(1) 서로 이은 직후  p.use_count()=1 · c.use_count()=2
      ~Parent
      ~Child
(2) link_pair() 에서 돌아왔다
===== clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DASK_WEAK sptr03.cpp -o exa && ./exa 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' | sed -E 's# \(/[^ ]*/(exa\+0x[0-9a-f]+)\) \(BuildId: [0-9a-f]+\)# (\1)#' (cc exit=0 · run exit=0) =====
(1) 서로 이은 직후  p.use_count()=1 · c.use_count()=2
      ~Parent
      ~Child
(2) link_pair() 에서 돌아왔다
```

**왜 그런가**

- ★★★ **서로가 서로의 강한 계수 1 을 붙들어** `p`·`c` 가 스코프를 나가도 **2 → 1 에서 멈춘다.** 아무도 0 이 안 되니 소멸자가 한 줄도 없다.
- ★★ **Direct 가 없고 Indirect 둘** — 순수한 순환에서는 두 블록 다 「다른 누수 블록에서만 닿는」 블록이다. **뿌리가 없다.**
- ★★★ **자식 → 부모를 `weak_ptr` 로 바꾸면 부모의 강한 계수가 1** — `p` 가 나가면 0 → `~Parent` → `child` 해제 → `~Child`.

### 4. ★★★ **`(M)` 은 해제 0회 · 0바이트** — `~Big` 은 **이미 돌았다** · `(N)` 은 **객체 1000바이트가 먼저** 풀린다 · 합계 차이는 **블록 크기 차이**(16 대 24)

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic sptr06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(M) make_shared<Big>()
      ~Big
    마지막 shared_ptr 이 죽었다 해제 0회 ·    0바이트
    weak_ptr 도 죽었다   해제 1회 · 1016바이트
(N) shared_ptr<Big>(new Big)
      ~Big
    마지막 shared_ptr 이 죽었다 해제 1회 · 1000바이트
    weak_ptr 도 죽었다   해제 2회 · 1024바이트
```

**왜 그런가**

- ★★★ **`make_shared` 는 객체와 블록이 한 덩어리**라 약한 계수가 남아 블록을 못 버리면 **객체 자리도 못 버린다** — `weak_ptr` 가 죽을 때 **1016바이트가 한 번에**.
- ★★ **`new` 판은 객체와 블록이 따로**라 강한 계수 0 에서 **객체(1000)**, 약한 계수 0 에서 **블록(24)** 이 풀린다.
- ★ 합계 **1016 대 1024** — 한 덩어리 블록은 16바이트 오버헤드, 따로 잡은 블록은 24바이트다(1번과 같은 차이).

### 5. ★★ **`use_count()=2`** · `(2)`·`(3)` 은 **`bad_weak_ptr` 예외** · C++14 판도 **같지만 보장이 아니다**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic sptr04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) shared_ptr 가 맡은 객체   owned.use_count()=2 · 같은 객체인가 1
(2) 지역 변수에서 부른다
    catch: bad_weak_ptr
(3) new 로 만들고 아직 안 맡겼다
    catch: bad_weak_ptr
(4) weak_from_this() — 안 맡긴 객체
    expired=1
```

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic sptr04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) shared_ptr 가 맡은 객체   owned.use_count()=2 · 같은 객체인가 1
(2) 지역 변수에서 부른다
    catch: bad_weak_ptr
(3) new 로 만들고 아직 안 맡겼다
    catch: bad_weak_ptr
===== clang++ -std=c++14 -Wall -Wextra -pedantic sptr04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) shared_ptr 가 맡은 객체   owned.use_count()=2 · 같은 객체인가 1
(2) 지역 변수에서 부른다
    catch: bad_weak_ptr
(3) new 로 만들고 아직 안 맡겼다
    catch: bad_weak_ptr
```

**왜 그런가**

- ★★ **`shared_from_this()` 는 객체 안의 `weak_ptr` 를 `lock` 한 것**이다 — 맡긴 객체면 **같은 블록**에 +1, 안 맡긴 객체면 그 `weak_ptr` 가 비어 **`bad_weak_ptr`**.
- ★★★ **C++17 부터 그 예외가 규정**이고, **C++14 에서는 미정의**였다 — libstdc++ 가 두 판에 **같은 코드**를 써서 같은 결과가 나왔을 뿐이다(판 경계는 알려진 사실 — 기준 소스는 이 배치에서 열지 못했다).

### 6. ★★★ **`4 · 0 · 0`**(두 컴파일러 같다) · 옆에 **`__libc_single_threaded` 검사 4곳** — **단일 스레드면 원자 명령을 건너뛰는** 분기다

**출력**

```bash
# sptr-asm.sh
# sptr-asm.sh — 세 판을 -O2 로 어셈블해 lock 접두 명령과 단일 스레드 검사를 센다
for c in g++ clang++; do
  for k in SHARED UNIQUE RAW; do
    asm=$($c -std=c++20 -O2 -S -o - -DASK_$k sptr07.cpp)
    printf '%-8s %-7s lock 접두 %d개 · __libc_single_threaded 검사 %d곳\n' "$c" "$k" \
      "$(printf '%s\n' "$asm" | grep -cE '^[[:space:]]+lock[[:space:]]')" \
      "$(printf '%s\n' "$asm" | grep -c '__libc_single_threaded')"
  done
done
```

```text
===== bash sptr-asm.sh (exit=0) =====
g++      SHARED  lock 접두 4개 · __libc_single_threaded 검사 4곳
g++      UNIQUE  lock 접두 0개 · __libc_single_threaded 검사 0곳
g++      RAW     lock 접두 0개 · __libc_single_threaded 검사 0곳
clang++  SHARED  lock 접두 4개 · __libc_single_threaded 검사 4곳
clang++  UNIQUE  lock 접두 0개 · __libc_single_threaded 검사 0곳
clang++  RAW     lock 접두 0개 · __libc_single_threaded 검사 0곳
```

```text
===== g++ -std=c++20 -O2 -S -o - -DASK_SHARED sptr07.cpp | grep -E '^[[:space:]]+lock[[:space:]]|__libc_single_threaded' (exit=0) =====
	cmpb	$0, __libc_single_threaded(%rip)
	lock xaddl	%eax, 12(%rdi)
	cmpb	$0, __libc_single_threaded(%rip)
	cmpb	$0, __libc_single_threaded(%rip)
	lock xaddl	%eax, (%rcx)
	lock addl	$1, 8(%rbx)
	cmpb	$0, __libc_single_threaded(%rip)
	lock xaddl	%eax, (%rcx)
===== clang++ -std=c++20 -O2 -S -o - -DASK_SHARED sptr07.cpp | grep -E '^[[:space:]]+lock[[:space:]]|__libc_single_threaded' (exit=0) =====
	movq	__libc_single_threaded@GOTPCREL(%rip), %rcx
	lock		xaddl	%eax, 8(%rbx)
	movq	__libc_single_threaded@GOTPCREL(%rip), %rax
	movq	__libc_single_threaded@GOTPCREL(%rip), %rcx
	lock		incl	8(%r14)
	lock		xaddl	%eax, 8(%rbx)
	movq	__libc_single_threaded@GOTPCREL(%rip), %rax
	lock		xaddl	%eax, 12(%rbx)
```

**왜 그런가**

- ★★★ **복사 대입은 새것의 계수 +1 · 옛것의 계수 −1(0 이면 파괴 · 블록 해제)** 을 **원자적으로** 한다 — `lock addl`/`lock incl`/`lock xaddl`.
- ★★ **libstdc++ 는 「아직 스레드가 하나뿐인가」를 먼저 본다** — **명령이 있다 ≠ 매번 실행된다.** 이것은 **구현의 선택**이다.
- ★ **`unique_ptr` 이동과 원시 포인터 복사는 0** — 장부가 없다.

### 7. ★★ **읽어도 된다**(`*part=2`) · `~Pair` 는 **`part.reset()` 에서** · `get()` 은 **멤버**, 살려 두는 것은 **`Pair` 전체**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic sptr05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) part.get()==&whole->second 1 · *part=2 · use_count=2
(2) whole.reset() 뒤  *part=2 · part.use_count()=1
      ~Pair
(3) part.reset() 뒤
===== clang++ -std=c++20 -Wall -Wextra -pedantic sptr05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) part.get()==&whole->second 1 · *part=2 · use_count=2
(2) whole.reset() 뒤  *part=2 · part.use_count()=1
      ~Pair
(3) part.reset() 뒤
```

**왜 그런가**

- ★★ **별칭 생성자는 `whole` 의 블록을 공유**하면서 **다른 주소(`&whole->second`)** 를 가리킨다 — 강한 계수 1 을 `part` 가 들고 있어 `Pair` 가 산다.
- ★ `shared_ptr` 의 두 칸(**가리키는 것 · 블록**)이 **따로 있는 이유**가 이것이다.

### 8. ★★★ **아니다 — 판마다 다르다**(g++ 는 10 / 10) · 결론 내면 안 되는 것은 「**순환이 없다**」 · 원리상 못 보는 것은 **메모리가 아닌 자원을 붙든 순환**

**출력**

```text
===== clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. sptr03.cpp -o exa && n=0; for i in 1 2 3 4 5 6 7 8 9 10; do r=$(./exa 2>&1); case $r in *'SUMMARY: AddressSanitizer'*) n=$((n+1));; esac; done; echo "clang + ASan 10판 중 리포트가 나온 판 $n" (exit=0) =====
clang + ASan 10판 중 리포트가 나온 판 6
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. sptr03.cpp -o exa && n=0; for i in 1 2 3 4 5 6 7 8 9 10; do r=$(./exa 2>&1); case $r in *'SUMMARY: AddressSanitizer'*) n=$((n+1));; esac; done; echo "g++   + ASan 10판 중 리포트가 나온 판 $n" (exit=0) =====
g++   + ASan 10판 중 리포트가 나온 판 10
```

**왜 그런가**

- ★★ **LeakSanitizer 는 스택·레지스터를 보수적으로 훑는다** — 죽은 칸에 남은 주소가 「닿는 포인터」로 보이면 누수를 놓친다. **clang 판의 수는 실행마다 바뀌었다**(예행 30판 중 14 · 10판 중 6).
- ★★★ **ASan 은 메모리만 본다**([15번](../15-raii-resources-as-types/)) — 순환이 **파일 핸들·소켓**을 들고 있으면 **그 자원이 안 닫힌 것은 어느 판도 모른다.**

### 9. ★★ **Rust `Rc` 는 `E0277`(컴파일 에러) · `Arc` 는 된다** · C++ 은 **통과한다 — 더 안전한 것이 아니라 늘 원자 비용을 내고 가리키는 값은 안 지킨다**

**출력**

```text
===== rustc --edition 2021 rcsend.rs -o rcx (cc exit=1) =====
error[E0277]: `Rc<i32>` cannot be sent between threads safely
  --> rcsend.rs:13:27
   |
13 |       let h = thread::spawn(move || {
   |               ------------- ^------
   |               |             |
   |  _____________|_____________within this `{closure@rcsend.rs:13:27: 13:34}`
   | |             |
   | |             required by a bound introduced by this call
14 | |         println!("thread 안에서 *b = {}", b);
15 | |     });
   | |_____^ `Rc<i32>` cannot be sent between threads safely
   |
   = help: within `{closure@rcsend.rs:13:27: 13:34}`, the trait `Send` is not implemented for `Rc<i32>`
note: required because it's used within this closure
  --> rcsend.rs:13:27
   |
13 |     let h = thread::spawn(move || {
   |                           ^^^^^^^
note: required by a bound in `spawn`
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/std/src/thread/mod.rs:725:1

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
```

```text
===== rustc --edition 2021 --cfg arc rcsend.rs -o rcx && ./rcx (cc exit=0 · run exit=0) =====
strong_count = 2
thread 안에서 *b = 5
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -pthread spthread.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
use_count = 2
thread 안에서 *b = 5
```

**왜 그런가**

- ★★★ **Rust 는 비원자 계수(`Rc`)와 원자 계수(`Arc`)를 타입으로 가르고**, 스레드를 넘는 것을 **`Send` 로 막는다.**
- ★★ **C++ `shared_ptr` 는 한 타입**이라 **늘 원자 계수**(6번의 `lock`)이고, **가리키는 `int` 에 대한 경쟁은 막지 않는다.**

### 10. ★ **인자로 넘기며 참조를 하나 더 만들기 때문** · 순환은 **순환 수집기(`gc.collect()`)가 회수** — C++ 에는 **없다**

**출력**

```python
# refcnt.py
# refcnt.py — CPython 의 참조 계수와 순환 수집기. use_count() 와 나란히 본다
import gc
import sys
import weakref

class Node:
    pass

a = Node()
print("(1) 이름 하나        getrefcount =", sys.getrefcount(a))
b = a
print("(2) 이름 둘          getrefcount =", sys.getrefcount(a))
del b
print("(3) 하나를 지운 뒤   getrefcount =", sys.getrefcount(a))

gc.disable()
p, c = Node(), Node()
p.child, c.parent = c, p
wp = weakref.ref(p)
del p, c
print("(4) 순환을 만들고 이름을 지운 뒤  살아 있나 =", wp() is not None)
print("(5) gc.collect() 가 회수한 객체 수 =", gc.collect())
print("(6) 그 뒤                         살아 있나 =", wp() is not None)
```

```text
===== python3 refcnt.py (exit=0) =====
(1) 이름 하나        getrefcount = 2
(2) 이름 둘          getrefcount = 3
(3) 하나를 지운 뒤   getrefcount = 2
(4) 순환을 만들고 이름을 지운 뒤  살아 있나 = True
(5) gc.collect() 가 회수한 객체 수 = 2
(6) 그 뒤                         살아 있나 = False
```

**왜 그런가**

- ★★★ **CPython 도 참조 계수만으로는 순환을 못 푼다**((4) `True`) — 그래서 **추적하는 순환 수집기**가 따로 있고, 그것이 2개를 회수했다.
- ★★ **C++ `shared_ptr` 에는 그 수집기가 없다** — 3번의 순환은 끝까지 샌다. **끊는 것은 프로그래머의 `weak_ptr`** 다.

### 11. ★★★ **크기 16 대 8 · 할당(블록) · 원자 명령 4 대 0 · 수명이 흐려짐(순환·늦은 해제)** — 팩토리는 **`unique_ptr`** 를 돌려주고, 공유가 필요하면 받는 쪽이 **블록 할당 한 번**을 치른다

- ★★ **크기** — [20번](../20-virtual-destructors-and-polymorphic-deletion/) (1)의 `sizeof` 16 · 8.
- ★★★ **할당** — 1번의 `1회 32`/`2회 40` 대 `1회 16`.
- ★★★ **원자 명령** — 6번의 `4 · 0`.
- ★★★ **수명** — 3번의 순환 · 4번의 늦은 해제.
- ★ **`shared_ptr<T>(std::move(up))`** 은 1번의 `(4)` — **2회 40바이트**(블록을 새로 잡는다).

### 12. 다른 주제와 잇기

- ★★★ **`unique_ptr` 는 삭제자를 타입(템플릿 인자)에**, **`shared_ptr` 는 제어 블록에** 둔다 — 그래서 `unique_ptr` 는 삭제자에 따라 **8\~40바이트**로 크기가 바뀌고(26번 (3)), `shared_ptr` 는 **16 그대로**이며 삭제자의 타입이 **`shared_ptr<T>` 에 드러나지 않는다**(20번의 타입 소거).
- ★★ 목록의 **28번 주제** — `weak_ptr` 와 순환 참조.
- ★ [`c-cpp-csharp.md`](../../../c-cpp-csharp.md) — 「`shared_ptr` 순환 참조는 해제되지 않는다」.

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `sptr01.cpp` 할당 계수기 | g++ · clang · g++ `-O2` · clang `-O2` | ★★★ **`1/32 · 2/40 · 1/16 · 2/40 · 1/32`** 네 판 동일 |
| 헤더 줄 | `grep` 2회 | ★★ 계수 둘 `_Atomic_word` · 블록 종류 셋 |
| `sptr02.cpp` `use_count` | g++ · clang 각 1회 | ★★ **`1 2 2 2 3 2 2 1`** · `(8)` 뒤 `~T` |
| `sptr03.cpp` 순환 | g++ ASan 1 + 종류 세기 1 · weak 판 두 컴파일러 · 10판 × 2 | ★★★ **`Indirect leak` 2** · weak **0** · g++ **10 / 10** · clang **판마다 다름** |
| `sptr04.cpp` `shared_from_this` | g++ C++20 · 두 컴파일러 C++14 | ★★ **`bad_weak_ptr`** 두 판 다 |
| `sptr05.cpp` 별칭 | g++ · clang | ★★ `reset` 뒤에도 `*part=2` |
| `sptr06.cpp` weak 해제 시점 | g++ · clang | ★★★ **M: 0 → 1016 · N: 1000 → 1024** |
| `sptr07.cpp` + `sptr-asm.sh` | 두 컴파일러 × 세 판 `-O2 -S` + 줄 출력 | ★★★ **`lock` 4 · 0 · 0** · 단일 스레드 검사 **4 · 0 · 0** |
| `spthread.cpp` · `rcsend.rs` · `refcnt.py` | 각 1\~2회 | ★★ C++ **통과** · Rust **E0277 / 통과** · Python **회수 2** |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · libstdc++ 13)에서만** 그렇다.

- ★★★ **제어 블록의 크기·배치(16 · 24)** · **`make_shared` 가 한 덩어리로 잡는 것** · **`lock` 명령 수와 `__libc_single_threaded` 분기** · **C++14 판의 `bad_weak_ptr`** · **clang + ASan 의 판별 흔들림.**

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **마지막 강한 참조에서 파괴** · **`weak_ptr` 는 강한 계수를 안 올린다** · **만료된 `lock()` 은 `nullptr`** · **C++17 의 `bad_weak_ptr`** · **별칭 생성자의 수명 공유** · **계수 갱신의 스레드 안전.**

**안 돌려 본 것 / 못 잰 것**

- **못 잰 것** — ★★ **clang + ASan 이 순환을 놓치는 정확한 이유**(가짜 스택 스위치의 결과가 판마다 달라 좁히지 못했다).
- **안 돌려 본 것** — ★ **한 객체에 블록 둘(`shared_ptr<T>(this)`)의 UB** · ★ **`atomic<shared_ptr>`** · ★ **Java·C# 의 추적 GC 로 순환 회수**(Python 판으로 같은 질문에 답했다 — 제5의 상태) · ★ **C++14 `shared_ptr<T[]>` 의 층 판정.**
- ★ **「부적용인 창」** — 경고 격자(규칙대로 된 코드). **`sizeof` 는 20편 인용.**
- ★ **cppreference 의 해당 쪽들을 이 배치에서 열지 못했다**(도구 한도) — 규칙은 **헤더 줄과 실행**으로만 적었다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **6번** — 단일 스레드 분기가 바뀌거나 사라지는지.
- ★★ **8번** — clang + ASan 판별이 안정되는지.
- ★ **1번** — 블록 크기(libstdc++ 의 `_Sp_counted_*` 배치).
