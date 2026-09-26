# cpp/syntax/28 — `weak_ptr` 와 순환 참조 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·리포트·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · x86-64 Linux · rustc 1.92.0 에서 실제로 돌려 얻은 것이다.\
> 소스는 질문 파일과 같다(출력 블록의 배너에 파일 이름이 있다).\
> ★ ASan 블록은 마커를 `stderr` 로 찍었고, 자른 블록은 **자르는 명령을 배너에** 적었다. TSan 블록은 **`setarch -R`** 로 돌렸다(배너에 있다). 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **2만 판 중 틈이 열린 횟수 · 「10번 돌려 몇 번」 · ASan 의 PID·주소 · 어셈블리의 레지스터·레이블**이다.\
> 근거로 쓰는 것은 다음이다 — **「있었나」의 참/거짓 · `lock`/`cmpxchg` 개수 · 소멸자 로그 · `is_constructible` 0/1 · 에러 줄 · 예외 이름**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **두 단계 판은 1(틈이 열렸다) · 한 단계 판은 값이 틀린 판 0** — 참/거짓은 근거, 횟수는 흔들린다 · TSan 은 **침묵**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -pthread wptr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
빈 shared_ptr 를 쥔 판이 있었나 1 · 값이 틀린 판이 있었나 0
===== g++ -std=c++20 -Wall -Wextra -pedantic -pthread -DASK_ONESTEP wptr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
빈 shared_ptr 를 쥔 판이 있었나 0 · 값이 틀린 판이 있었나 0
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -pthread wptr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
빈 shared_ptr 를 쥔 판이 있었나 1 · 값이 틀린 판이 있었나 0
===== clang++ -std=c++20 -Wall -Wextra -pedantic -pthread -DASK_ONESTEP wptr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
빈 shared_ptr 를 쥔 판이 있었나 0 · 값이 틀린 판이 있었나 0
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -pthread wptr01.cpp -o ex && ./ex n (cc exit=0 · run exit=0) =====
판 20000 · 살아 있다고 답한 판 19996 · 그 뒤 빈 shared_ptr 17 · 값이 틀린 판 0
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -pthread wptr01.cpp -o ex && n=0; for i in 1 2 3 4 5 6 7 8 9 10; do case $(./ex) in *'쥔 판이 있었나 1'*) n=$((n+1));; esac; done; echo "두 단계 판 — 10번 돌려 빈 shared_ptr 를 쥔 적이 있던 번 $n" (exit=0) =====
두 단계 판 — 10번 돌려 빈 shared_ptr 를 쥔 적이 있던 번 10
===== g++ -std=c++20 -Wall -Wextra -pedantic -pthread -DASK_ONESTEP wptr01.cpp -o ex && n=0; for i in 1 2 3 4 5 6 7 8 9 10; do case $(./ex) in *'값이 틀린 판이 있었나 1'*) n=$((n+1));; esac; done; echo "한 단계 판 — 10번 돌려 값이 틀린 적이 있던 번 $n" (exit=0) =====
한 단계 판 — 10번 돌려 값이 틀린 적이 있던 번 0
```

```text
===== g++ -std=c++20 -fsanitize=thread -g -pthread wptr01.cpp -o ext && setarch -R ./ext 2>&1 (cc exit=0 · run exit=0) =====
빈 shared_ptr 를 쥔 판이 있었나 1 · 값이 틀린 판이 있었나 0
===== clang++ -std=c++20 -fsanitize=thread -g -pthread wptr01.cpp -o ext && setarch -R ./ext 2>&1 (cc exit=0 · run exit=0) =====
빈 shared_ptr 를 쥔 판이 있었나 1 · 값이 틀린 판이 있었나 0
```

**왜 그런가**

- ★★★ **`expired()` 가 「살아 있다」고 답한 뒤, `lock()` 을 부르기 전에 소유자 스레드가 `s.reset()` 을 끝냈다** — 그래서 `lock()` 이 **빈 것**을 돌려줬다. 두 컴파일러 다.
- ★★★ **한 단계 판에서는 `lock()` 이 준 것이 비어 있지 않으면 끝까지 산다** — 「값이 틀린 판」 0. 이 판에는 **두 번째 질문이 없다.**
- ★★ **2만 판 중 몇 번 · 10번 중 몇 번은 흔들리는 칸**이다 — 주장하는 것은 「**열린다**」뿐이다.
- ★★★ **TSan 은 두 컴파일러 다 침묵 · `run exit=0`** — 두 원자 연산 **사이**의 틈은 데이터 경쟁이 아니다(7번).

### 2. ★★★ **`expired` — lock 0 · cmpxchg 0 · `lock` — lock 1 · cmpxchg 1**(두 컴파일러 같다) · 뒤로 가는 점프는 **「계수를 다시 읽고 다시 시도」**

**출력**

```text
===== bash wptr-asm.sh (exit=0) =====
g++      EXPIRED  lock 접두 0개 · cmpxchg 0개
g++      LOCK     lock 접두 1개 · cmpxchg 1개
clang++  EXPIRED  lock 접두 0개 · cmpxchg 0개
clang++  LOCK     lock 접두 1개 · cmpxchg 1개
```

```text
===== g++ -std=c++20 -O2 -S -o - -DASK_EXPIRED wptr02.cpp | sed -n '/^_Z3ask/,/\.cfi_endproc/p' | grep -vE '^[[:space:]]+\.(cfi|p2align)' (exit=0) =====
_Z3askRKSt8weak_ptrIiE:
.LFB3348:
	endbr64
	movq	8(%rdi), %rdx
	xorl	%eax, %eax
	testq	%rdx, %rdx
	je	.L1
	movl	8(%rdx), %eax
	testl	%eax, %eax
	setne	%al
.L1:
	ret
===== g++ -std=c++20 -O2 -S -o - -DASK_LOCK wptr02.cpp | sed -n '/^_Z3ask/,/\.cfi_endproc/p' | grep -vE '^[[:space:]]+\.(cfi|p2align)' (exit=0) =====
_Z3askRKSt8weak_ptrIiE:
.LFB3348:
	endbr64
	movq	8(%rsi), %rax
	movq	%rax, 8(%rdi)
	testq	%rax, %rax
	je	.L2
	leaq	8(%rax), %rdx
	movl	8(%rax), %eax
.L5:
	testl	%eax, %eax
	je	.L3
	leal	1(%rax), %ecx
	lock cmpxchgl	%ecx, (%rdx)
	jne	.L5
	movq	8(%rdi), %rax
	testq	%rax, %rax
	je	.L2
	movl	8(%rax), %eax
	testl	%eax, %eax
	je	.L2
	movq	(%rsi), %rax
	movq	%rax, (%rdi)
	movq	%rdi, %rax
	ret
.L3:
	movq	$0, 8(%rdi)
.L2:
	xorl	%eax, %eax
	movq	%rax, (%rdi)
	movq	%rdi, %rax
	ret
```

**왜 그런가**

- ★★★ **`expired()` 는 강한 계수를 한 번 읽는다**(`movl` → `testl` → `setne`) — 결과는 **읽은 순간의 사진**이다.
- ★★★ **`lock()` 은 「0 이면 포기(`je .L3`) · 아니면 `lock cmpxchgl` 로 +1 · 그 사이 바뀌었으면 `jne .L5` 로 다시」** — **확인과 +1 이 한 명령 안에서 묶인다.** 이것이 1번의 한 단계 판에 틈이 없는 이유다.
- ★ 어느 칸이 강한 계수인지는 **내 읽기**다 — 실측한 것은 **개수 · 명령 이름 · 루프 모양**이다.

### 3. ★★★ **A1 = 2 · A2 = 0 · B1 = 0 · B2 = 1** · 누수는 **어느 판도 없다** · 규칙은 **「약한 참조는 소유의 반대 방향 — 트리면 자식 → 부모」**

**출력**

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. wptr03.cpp -o exa && ./exa 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=0) =====
(A1) 설계 A · 뿌리를 쥔다
    쥔 것 = 뿌리 r · 살아 있는 자식 수 2
    쥔 것을 놓는다
      ~A r
      ~A x
      ~A y
(A2) 설계 A · 자식 x 를 쥔다
      ~A r
      ~A y
    쥔 것 = 자식 x · 그 부모가 살아 있나 0
    쥔 것을 놓는다
      ~A x
(B1) 설계 B · 뿌리를 쥔다
      ~B y
      ~B x
    쥔 것 = 뿌리 r · 살아 있는 자식 수 0
    쥔 것을 놓는다
      ~B r
(B2) 설계 B · 자식 x 를 쥔다
      ~B y
    쥔 것 = 자식 x · 그 부모가 살아 있나 1
    쥔 것을 놓는다
      ~B x
      ~B r
(끝) main 을 나간다
```

**왜 그런가**

- ★★★ **A 는 부모가 자식을 소유한다** — 뿌리를 쥐면 **자식 둘이 산다**(A1). 자식만 쥐면 뿌리와 형제가 먼저 죽고 **자식의 `weak_ptr` 가 만료된다**(A2 `0` · `~A r`·`~A y` 가 「쥔 것」 줄보다 먼저).
- ★★★ **B 는 아무도 자식을 소유하지 않는다** — `build()` 가 뿌리만 돌려주는 순간 지역 `x`·`y` 가 죽고(`~B y`·`~B x` 가 먼저) **자식 0**(B1). 자식을 쥐면 그 자식이 **부모를 살린다**(B2 `1`).
- ★★ **누수는 두 설계 모두 0** — 순환이 없으니 ASan 이 볼 것이 없다. **B 가 틀린 것은 「샜나」가 아니라 「사라졌나」다**(8번).

### 4. ★★ **다시 찍힌다** · `(4)` 는 **크기 3 · 만료 2 → 쓸어낸 뒤 1** · 죽은 구독자 **1 · 0**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic wptr04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) a = get(1); b = get(1);
      [load] 1
    a 와 b 가 같은 객체인가 1 · use_count 2
(2) a.reset(); b.reset();
      [drop] 1
    캐시 크기 1 · 만료된 항목 1
(3) c = get(1);
      [load] 1
(4) get(2) · get(3) 을 받자마자 버린다
      [load] 2
      [drop] 2
      [load] 3
      [drop] 3
    캐시 크기 3 · 만료된 항목 2
    만료 항목을 쓸어낸 뒤 캐시 크기 1
(5) 관찰자 p · q · r 을 구독시키고 q 를 놓는다
      p 가 받았다
      r 가 받았다
      죽은 구독자 1 · 남은 구독 2
(6) 한 번 더 알린다
      p 가 받았다
      r 가 받았다
      죽은 구독자 0 · 남은 구독 2
      [drop] 1
```

**왜 그런가**

- ★★★ **캐시의 `weak_ptr` 는 객체를 살려 두지 않는다** — `a`·`b` 가 놓자 `[drop] 1`, 다시 부르면 **새로 만든다.**
- ★★★ **만료된 칸은 캐시에 남는다** — `lock()` 이 실패해도 칸은 그대로다. **`erase_if` 로 직접 쓸어야** 준다.
- ★★ **구독자 목록은 알릴 때 치운다** — 첫 알림에서 `q` 를 세고(1) 지웠으니 둘째 알림은 0.

### 5. ★★ **8행(`unique_ptr` 에서)과 9행(`*w1`)이 에러** — 두 컴파일러가 **같은 줄** · `sizeof` **16** · **6 / 10** · 만료된 `w` 에서 **`lock()` 은 빈 것, 생성자는 `bad_weak_ptr`**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 wptr05.cpp -o ex (cc exit=1) =====
wptr05.cpp: In function ‘int main()’:
wptr05.cpp:8:29: error: conversion from ‘std::unique_ptr<int, std::default_delete<int> >’ to non-scalar type ‘std::weak_ptr<int>’ requested
    8 |     std::weak_ptr<int> w2 = u;          // 2. unique_ptr 에서
      |                             ^
wptr05.cpp:9:13: error: no match for ‘operator*’ (operand type is ‘std::weak_ptr<int>’)
    9 |     int a = *w1;                        // 3. 역참조
      |             ^~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 wptr05.cpp -o ex (cc exit=1) =====
wptr05.cpp:8:24: error: no viable conversion from '__detail::__unique_ptr_t<int>' (aka 'unique_ptr<int>') to 'std::weak_ptr<int>'
    8 |     std::weak_ptr<int> w2 = u;          // 2. unique_ptr 에서
      |                        ^    ~
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/shared_ptr.h:831:7: note: candidate constructor not viable: no known conversion from '__detail::__unique_ptr_t<int>' (aka 'unique_ptr<int>') to 'const weak_ptr<int> &' for 1st argument
  831 |       weak_ptr(const weak_ptr&) noexcept = default;
      |       ^        ~~~~~~~~~~~~~~~
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/shared_ptr.h:837:7: note: candidate constructor not viable: no known conversion from '__detail::__unique_ptr_t<int>' (aka 'unique_ptr<int>') to 'weak_ptr<int> &&' for 1st argument
  837 |       weak_ptr(weak_ptr&&) noexcept = default;
      |       ^        ~~~~~~~~~~
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/shared_ptr.h:828:2: note: candidate template ignored: could not match 'shared_ptr' against 'unique_ptr'
  828 |         weak_ptr(const shared_ptr<_Yp>& __r) noexcept
      |         ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/shared_ptr.h:834:2: note: candidate template ignored: could not match 'weak_ptr' against 'unique_ptr'
  834 |         weak_ptr(const weak_ptr<_Yp>& __r) noexcept
      |         ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/shared_ptr.h:840:2: note: candidate template ignored: could not match 'weak_ptr' against 'unique_ptr'
  840 |         weak_ptr(weak_ptr<_Yp>&& __r) noexcept
      |         ^
wptr05.cpp:9:13: error: indirection requires pointer operand ('std::weak_ptr<int>' invalid)
    9 |     int a = *w1;                        // 3. 역참조
      |             ^~~
2 errors generated.
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic wptr06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof(weak_ptr<int>) = 16 · sizeof(shared_ptr<int>) = 16 · sizeof(unique_ptr<int>) = 8
is_constructible_v<To, From>
  weak_ptr<int>    <- const shared_ptr<int>&           1
  weak_ptr<int>    <- shared_ptr<int>&&                1
  weak_ptr<int>    <- const weak_ptr<int>&             1
  weak_ptr<Base>   <- const shared_ptr<Derived>&       1
  weak_ptr<int>    <- const unique_ptr<int>&           0
  weak_ptr<int>    <- unique_ptr<int>&&                0
  weak_ptr<int>    <- int*                             0
  shared_ptr<int>  <- unique_ptr<int>&&                1
  shared_ptr<int>  <- const weak_ptr<int>&             1
  unique_ptr<int>  <- const shared_ptr<int>&           0
만들 수 있는 칸 6 / 10
만료된 w 에서 — w.lock() 이 비었나 1
만료된 w 에서 — shared_ptr<int>(w) catch: bad_weak_ptr
```

**왜 그런가**

- ★★★ **`weak_ptr` 의 생성자는 `shared_ptr` 와 `weak_ptr` 만 받는다** — clang 의 후보 목록(`could not match 'shared_ptr' against 'unique_ptr'`)과 `is_constructible` 의 0 이 같은 말을 한다.
- ★★ **`weak_ptr` 에는 `operator*` 가 없다** — 반드시 `lock()` 을 거친다(10행은 통과).
- ★★ **승격의 두 길** — `lock()` 은 **조용히 빈 것**을, `shared_ptr<int>(w)` 는 **`bad_weak_ptr`** 를 준다.

### 6. ★★ 기본판 **r: strong 1 · weak 1** · `upgrade()` 는 **`None`** · `--cfg cycle` 판은 **컴파일된다 — `drop` 0줄**

**출력**

```text
===== rustc --version (exit=0) =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
===== rustc --edition 2021 rcweak.rs -o rwx && ./rwx (cc exit=0 · run exit=0) =====
(1) r: strong 1 weak 1 · x: strong 2 weak 0
(2) r 이 스코프를 나간다
      drop r
(3) x 의 부모를 upgrade — None
(4) main 끝
      drop x
===== rustc --edition 2021 --cfg cycle rcweak.rs -o rwx && ./rwx (cc exit=0 · run exit=0) =====
(1) r: strong 2 weak 0 · x: strong 2 weak 0
(2) r 이 스코프를 나간다
(3) x 의 부모 — Some('r')
(4) main 끝
```

**왜 그런가**

- ★★ **`Weak::upgrade()` 가 `lock()` 이다** — 강한 계수가 0 이면 `None`.
- ★★★ **Rust 도 `Rc` 순환을 컴파일에서 막지 않는다** — strong 2 · 2 로 서로를 붙들고 `main` 이 끝나도 **`drop` 이 없다.** 누수는 Rust 에서 **안전한 코드**다.

### 7. ★★★ TSan 은 **데이터 경쟁**을 찾는다 — 1번은 **원자 연산 둘 사이의 논리 틈**이라 범주가 다르다 · 그래서 **N판 판정**으로 보았다

- ★★★ **데이터 경쟁** = 두 스레드가 **동기화 없이 같은 메모리에 접근하고 하나 이상이 쓰는 것.** `expired()` 와 `lock()` 은 **각각 원자적**이라 그 조건에 걸리지 않는다.
- ★★★ **틈은 「두 원자 연산 사이에 다른 스레드가 끼는 것」** — 올바른 동기화 위의 **잘못된 논리**다. 어떤 sanitizer 도 **의도**를 모른다.
- ★★ **창을 바꿔 물었다(제5의 상태)** — 「빈 것을 쥔 판이 있었나」를 **2만 판 실행에서 참/거짓으로** 세었다.

### 8. ★★★ 설계 B 는 **자식을 아무도 소유하지 않아 자식이 즉시 죽는다** · 규칙은 **「소유는 만드는 쪽 → 만들어지는 쪽, 약한 참조는 그 반대」**

- ★★★ B1 에서 뿌리를 쥐고 있는데 **살아 있는 자식 0** — 순환은 없어졌지만 **트리도 없어졌다.**
- ★★ 「누수 0」은 **필요조건일 뿐**이다 — 「원하는 것이 살아 있나」는 **로그로** 따로 봐야 한다(ASan 은 못 본다).

### 9. ★★★ **객체 자리 전체(제어 블록과 한 덩어리)** 가 남는다 — 27편 (6)의 **「`~Big` 은 돌았는데 1016바이트는 weak 가 죽을 때」**

- ★★★ `make_shared` 는 객체와 블록을 **한 번에** 잡는다. 캐시 칸의 `weak_ptr` 가 **약한 계수를 붙드는 동안** 블록을 못 버리고, **블록과 한 덩어리인 객체 자리도** 못 버린다.
- ★★ 그래서 **청소하지 않는 `weak_ptr` 캐시 + `make_shared` 큰 객체**는 **소멸자가 다 돌았는데 메모리가 안 줄어드는** 모양이 된다.

### 10. ★★★ **`unique_ptr` 는 포인터 한 칸(8바이트)뿐이고 제어 블록이 없다** — `weak_ptr` 가 물을 「현황판」이 없다 · 관찰은 **raw 포인터·참조**(수명을 구조가 보장할 때)

- ★★★ `weak_ptr` 의 모든 동작(`expired`·`lock`)은 **블록의 강한 계수**를 읽는 것이다. `unique_ptr` 는 계수 자체가 없다(26편 `sizeof` 8 · 27편 `make_unique` 16바이트).
- ★ raw 관찰자는 **만료를 알려 주지 않는다** — 그 대가와 정당한 자리는 [목록의 **29번 주제**](../29-new-delete-and-where-raw-pointers-remain/)다.

### 11. 다른 주제와 잇기

- ★★ **공통점 — 「도구가 조용하다」가 「문제가 없다」가 아니다.** 27편은 **판마다** 놓쳤고, 이 편은 **원리상** 범주 밖이었다.
- ★ Rust 의 `Rc` 는 **스레드로 보내는 것**(27편 (8) `E0277`)을 막고 **순환**은 안 막는다(6번).
- ★ [`c-cpp-csharp.md`](../../../c-cpp-csharp.md) 의 「C++ — RAII는 해제를 잊는 실패를 지우고, 죽은 것을 가리키는 실패는 못 지운다」 절.

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `wptr01.cpp` 두 단계 / 한 단계 | g++ · clang 각 2판 + 수 1판 + 10판 × 2 + TSan 두 컴파일러 | ★★★ **두 단계 1 · 한 단계 0** · TSan **침묵** · 횟수는 흔들림 |
| `wptr02.cpp` + `wptr-asm.sh` | 두 컴파일러 × 두 판 `-O2 -S` + g++ 몸통 둘 | ★★★ **lock 0 · 1 · cmpxchg 0 · 1** |
| `wptr03.cpp` 트리 | g++ · clang ASan | ★★★ **A1 2 · A2 0 · B1 0 · B2 1** · 누수 0 |
| `wptr04.cpp` 캐시·구독 | g++ · clang | ★★ **크기 3 · 만료 2 → 1** · 죽은 구독자 1 · 0 |
| `wptr05.cpp` 에러 | 두 컴파일러 | ★★ **8 · 9행** · 각 2건 |
| `wptr06.cpp` 격자 | 두 컴파일러 | ★★ **6 / 10** · `sizeof` 16 · `bad_weak_ptr` |
| `rcweak.rs` | 기본 · `--cfg cycle` | ★★ **`None`** · 순환 판 **`drop` 0줄** |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · libstdc++ 13)에서만** 그렇다.

- ★★★ **`lock()` 의 `lock cmpxchg` 루프 모양 · `expired()` 가 원자 명령 0** · **`sizeof(weak_ptr)` 16** · ★★ **TOCTOU 가 2만 판에 몇 번 열리나** · **g++ TSan 이 무작위화 아래에서 시작 못 하는 것**(`setarch -R` 로 돌렸다).

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **`lock()` 의 원자성** · **`weak_ptr` 는 `shared_ptr`/`weak_ptr` 에서만** · **만료된 `weak_ptr` 로 만든 `shared_ptr` 는 `bad_weak_ptr`** · **마지막 강한 참조에서 파괴.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **`atomic<weak_ptr>`** · ★ **`owner_less`** · ★ **틈에서 쥔 빈 `shared_ptr` 를 역참조하는 것(UB — 일부러 안 했다).**
- ★ **「부적용인 창」** — 경고 격자(규칙대로 된 코드).
- ★ **cppreference 의 `weak_ptr` 쪽을 이 배치에서 열지 않았다** — 규칙은 **실행·어셈블리·격자**로만 적었다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **2번** — `lock()` 이 다른 명령(예: 단일 스레드 분기)이 되는지.
- ★★ **1번의 TSan 판** — g++ TSan 이 무작위화 아래에서 시작하는지.
- ★ **5번** — 에러 문구.
