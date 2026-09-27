# cpp/syntax/30 — 댕글링 참조와 수명 연장 규칙 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·리포트·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · x86-64 Linux · rustc 1.92.0 · go1.27.1 에서 실제로 돌려 얻은 것이다.\
> 소스는 질문 파일과 같다(출력 블록의 배너에 파일 이름이 있다).\
> ★ ASan 블록은 마커를 `stderr` 로 찍었고, 자른 블록은 **자르는 명령을 배너에** 적었다. 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **도구 없이 돌린 탐침의 「42 였나」 · ASan 의 PID·주소 · 신호 번호**다.\
> 근거로 쓰는 것은 다음이다 — **격자 칸의 도구 이름 · 「잡은 칸 N / 42」 · 소멸자 로그 순서 · 매크로 값 · 에러 코드 · `moved to heap`**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ g++ 경고 **1 · 2 · 3 · 6**, clang 경고 **1 · 4 · 5** — **탐침 7 은 둘 다 0** · `-O0` ASan 은 **7 · 7**(g++ 의 1 은 SEGV), clang `-O2` ASan 은 **2** · **잡은 칸 30 / 42**

**출력**

```text
===== bash dang-grid.sh (exit=0) =====
#   g++ -Wall              clang -Wall            g++ ASan -O0           clang ASan -O0         g++ ASan -O2           clang ASan -O2        
1   -Wreturn-local-addr    -Wreturn-stack-address  SEGV                   stack-use-after-return SEGV                   -                     
2   -Wdangling-reference   -                      stack-use-after-scope  stack-use-after-scope  stack-use-after-scope  -                     
3   -Wdangling-reference   -                      stack-use-after-scope  stack-use-after-scope  stack-use-after-scope  heap-use-after-free   
4   -                      -Wdangling-gsl         heap-use-after-free    heap-use-after-free    heap-use-after-free    heap-use-after-free   
5   -                      -Wreturn-stack-address  stack-use-after-return stack-use-after-return stack-use-after-scope  -                     
6   -Wdangling-reference   -                      stack-use-after-scope  stack-use-after-scope  stack-use-after-scope  -                     
7   -                      -                      stack-use-after-scope  stack-use-after-scope  stack-use-after-scope  -                     
잡은 칸 30 / 42 (그중 SEGV 로 멈춘 칸 2)
```

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DPROBE=7 dang01.cpp -o exa && ./exa 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' | grep -vE '^(Shadow|  [A-Z]|  0x|=>0x)' (cc exit=0 · run exit=1) =====
=================================================================
==3378889==ERROR: AddressSanitizer: stack-use-after-scope on address 0x750995200030 at pc 0x57f0af8223d9 bp 0x7ffd3c8eadf0 sp 0x7ffd3c8eade0
READ of size 4 at 0x750995200030 thread T0
    #0 0x57f0af8223d8 in probe() dang01.cpp:58
    #1 0x57f0af822457 in main dang01.cpp:63

Address 0x750995200030 is located in stack of thread T0 at offset 48 in frame
    #0 0x57f0af822298 in probe() dang01.cpp:35

    [48, 52) '<unknown>' <== Memory access at offset 48 is inside this variable
    [64, 72) 'w' (line 57)
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-use-after-scope dang01.cpp:58 in probe()
```

**왜 그런가**

- ★★★ **경고는 「모양」을 본다** — g++ 의 `-Wdangling-reference` 는 **「참조를 받아 참조를 돌려주는 호출에 임시를 넘김」**(2 · 3 · 6)을, clang 의 `-Wdangling-gsl`·`-Wreturn-stack-address` 는 **뷰·람다 캡처**(4 · 5)를 본다. **탐침 7(생성자를 거쳐 참조 멤버에 임시)은 어느 모양에도 안 걸렸다.**
- ★★★ **ASan 은 「실행이 그 메모리를 실제로 읽었나」를 본다** — `-O0` 에서는 읽기가 그대로 남아 전부 잡혔다. clang `-O2` 에서는 스택 탐침 다섯의 읽기가 ASan 이 볼 수 없는 모양이 되어 **힙 탐침 둘(3 · 4)만** 남았다.
- ★★ **탐침 7 을 clang `-O2` 로 빌드한 판은 네 창이 전부 빈다** — 경고 0 · ASan 침묵.

### 2. ★★★ **이미 잡혔다**(환경 변수 없음 = 켜진 상태) · `=0` 이면 **탐침 5 는 두 컴파일러 다, 탐침 1 은 clang 이 놓치고 `42 인가 1`** · g++ 탐침 1 은 **옵션과 무관하게 `SEGV`**

**출력**

```text
===== bash dang-uar.sh (exit=0) =====
ASAN_OPTIONS 환경 변수 = (설정 안 됨)
탐침 1  g++      detect_stack_use_after_return=1  ->  SUMMARY: AddressSanitizer: SEGV
탐침 1  g++      detect_stack_use_after_return=0  ->  SUMMARY: AddressSanitizer: SEGV
탐침 1  clang++  detect_stack_use_after_return=1  ->  SUMMARY: AddressSanitizer: stack-use-after-return
탐침 1  clang++  detect_stack_use_after_return=0  ->  (1) 읽은 값이 42 인가 1
탐침 5  g++      detect_stack_use_after_return=1  ->  SUMMARY: AddressSanitizer: stack-use-after-return
탐침 5  g++      detect_stack_use_after_return=0  ->  (5) 읽은 값이 42 인가 1
탐침 5  clang++  detect_stack_use_after_return=1  ->  SUMMARY: AddressSanitizer: stack-use-after-return
탐침 5  clang++  detect_stack_use_after_return=0  ->  (5) 읽은 값이 42 인가 1
```

**왜 그런가**

- ★★★ **이 판의 ASan 은 돌아간 함수의 스택을 「가짜 스택」으로 옮겨 두고 지켜보는 것이 기본**이었다(방식은 내 읽기 · 실측은 옵션에 따른 칸의 변화) — 끄면 그 칸이 **평범한 스택**이 되어, 덮이지 않은 옛 값이 읽힌다.
- ★★ **g++ 탐침 1 은 스택을 읽지 않는다** — 널을 읽는다(9번).

### 3. ★★★ **뒤 — (a)(c)(e)(f) · 앞 — (b)(d)(g)** · g++ 는 **(b)(d)**, clang 은 **(d)** 에 경고 · **(g) 는 아무도**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic dang02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
dang02.cpp: In function ‘int main(int, char**)’:
dang02.cpp:22:16: warning: possibly dangling reference to a temporary [-Wdangling-reference]
   22 |     { const T& r = pass(T{2});                 std::printf("    다음 문장\n"); (void)r; }
      |                ^
dang02.cpp:22:24: note: the temporary was destroyed at the end of the full expression ‘pass(T(2))’
   22 |     { const T& r = pass(T{2});                 std::printf("    다음 문장\n"); (void)r; }
      |                    ~~~~^~~~~~
dang02.cpp:26:11: warning: possibly dangling reference to a temporary [-Wdangling-reference]
   26 |     { T&& r = std::move(T{4});                 std::printf("    다음 문장\n"); (void)r; }
      |           ^
dang02.cpp:26:24: note: the temporary was destroyed at the end of the full expression ‘std::move<T>(T(4))’
   26 |     { T&& r = std::move(T{4});                 std::printf("    다음 문장\n"); (void)r; }
      |               ~~~~~~~~~^~~~~~
(a) const T& r = T{1};
    다음 문장
      ~T(1)
(b) const T& r = pass(T{2});
      ~T(2)
    다음 문장
(c) const int& r = T{3}.m;
    다음 문장
      ~T(3)
(d) T&& r = std::move(T{4});
      ~T(4)
    다음 문장
(e) const T& r = flag ? T{5} : T{6};
    다음 문장
      ~T(5)
(f) H h{T{7}};
    다음 문장
      ~T(7)
(g) H h(T{8});
      ~T(8)
    다음 문장
(끝)
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic dang02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
dang02.cpp:26:25: warning: temporary bound to local reference 'r' will be destroyed at the end of the full-expression [-Wdangling]
   26 |     { T&& r = std::move(T{4});                 std::printf("    다음 문장\n"); (void)r; }
      |                         ^~~~
dang02.cpp:26:15: warning: moving a temporary object prevents copy elision [-Wpessimizing-move]
   26 |     { T&& r = std::move(T{4});                 std::printf("    다음 문장\n"); (void)r; }
      |               ^
dang02.cpp:26:15: note: remove std::move call here
   26 |     { T&& r = std::move(T{4});                 std::printf("    다음 문장\n"); (void)r; }
      |               ^~~~~~~~~~    ~
2 warnings generated.
(a) const T& r = T{1};
    다음 문장
      ~T(1)
(b) const T& r = pass(T{2});
      ~T(2)
    다음 문장
(c) const int& r = T{3}.m;
    다음 문장
      ~T(3)
(d) T&& r = std::move(T{4});
      ~T(4)
    다음 문장
(e) const T& r = flag ? T{5} : T{6};
    다음 문장
      ~T(5)
(f) H h{T{7}};
    다음 문장
      ~T(7)
(g) H h(T{8});
      ~T(8)
    다음 문장
(끝)
```

**왜 그런가**

- ★★★ **(a) 기본형 · (c) 임시의 멤버 · (e) 조건 연산자 · (f) 중괄호 집합체** — 임시(또는 그 멤버)가 **참조에 직접** 묶였다.
- ★★★ **(b) `pass` 의 매개변수에 묶였을 뿐 `r` 에 묶인 것이 아니다** · **(d) `std::move` 가 xvalue 를 만든다 — xvalue 는 늘 것이 없다** · **(g) C++20 괄호 집합체 초기화는 연장하지 않는다**(cppreference 의 예외 목록 · since C++20).
- ★★ **(g) 는 (f) 와 괄호 모양 하나 차이**인데 두 컴파일러 다 **경고 0** 이다.

### 4. ★★★ **네 판 모두 앞**(두 컴파일러 · 두 판) · 매크로는 네 판 다 **`201603`** — P2718 이 들어오면 **`202211`** 이 된다 · g++ `-std=c++23` 의 `__cplusplus` 는 **`202100`**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic dang03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
dang03.cpp: In function ‘int main()’:
dang03.cpp:16:31: warning: possibly dangling reference to a temporary [-Wdangling-reference]
   16 |     for (int x : make().items()) {
      |                               ^
dang03.cpp:16:30: note: the temporary was destroyed at the end of the full expression ‘make()().Holder::items()’
   16 |     for (int x : make().items()) {
      |                  ~~~~~~~~~~~~^~
__cplusplus = 202002 · __cpp_range_based_for = 201603
(1) for (int x : make().items())
    ~Holder
    본문에 들어왔다
(2) 루프를 나왔다
===== g++ -std=c++23 -Wall -Wextra -pedantic dang03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
dang03.cpp: In function ‘int main()’:
dang03.cpp:16:31: warning: possibly dangling reference to a temporary [-Wdangling-reference]
   16 |     for (int x : make().items()) {
      |                               ^
dang03.cpp:16:30: note: the temporary was destroyed at the end of the full expression ‘make()().Holder::items()’
   16 |     for (int x : make().items()) {
      |                  ~~~~~~~~~~~~^~
__cplusplus = 202100 · __cpp_range_based_for = 201603
(1) for (int x : make().items())
    ~Holder
    본문에 들어왔다
(2) 루프를 나왔다
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic dang03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
__cplusplus = 202002 · __cpp_range_based_for = 201603
(1) for (int x : make().items())
    ~Holder
    본문에 들어왔다
(2) 루프를 나왔다
===== clang++ -std=c++23 -Wall -Wextra -pedantic dang03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
__cplusplus = 202302 · __cpp_range_based_for = 201603
(1) for (int x : make().items())
    ~Holder
    본문에 들어왔다
(2) 루프를 나왔다
```

**왜 그런가**

- ★★★ **g++ 13 · clang 18 은 P2718 을 구현하지 않았다** — cppreference 의 지원표가 **GCC 15 · Clang 19** 로 적는다. `-std=c++23` 은 **그 판의 기본값을 고를 뿐**이다.
- ★★ **판별은 `__cpp_range_based_for`** — 규칙이 들어왔으면 값이 바뀐다.
- ★ 본문이 한 번 돈 것은 **죽은 `vector` 를 읽은 UB 의 결과**다 — 근거는 `~Holder` 의 **자리**뿐이다.

### 5. ★★★ **`E0515` · `E0373` · `E0716`** — 탐침 **1 · 5 · 4** 와 짝

**출력**

```text
===== rustc --edition 2021 --cfg local_ref dangle.rs -o drx (cc exit=1) =====
error[E0515]: cannot return reference to local variable `x`
 --> dangle.rs:5:5
  |
5 |     &x
  |     ^^ returns a reference to data owned by the current function

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0515`.
```

```text
===== rustc --edition 2021 --cfg closure dangle.rs -o drx (cc exit=1) =====
error[E0373]: closure may outlive the current function, but it borrows `x`, which is owned by the current function
  --> dangle.rs:11:5
   |
11 |     || x
   |     ^^ - `x` is borrowed here
   |     |
   |     may outlive borrowed value `x`
   |
note: closure is returned here
  --> dangle.rs:11:5
   |
11 |     || x
   |     ^^^^
help: to force the closure to take ownership of `x` (and any other referenced variables), use the `move` keyword
   |
11 |     move || x
   |     ++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0373`.
```

```text
===== rustc --edition 2021 --cfg view dangle.rs -o drx (cc exit=1) =====
error[E0716]: temporary value dropped while borrowed
  --> dangle.rs:21:24
   |
21 |         let sv: &str = String::from("*42").as_str();
   |                        ^^^^^^^^^^^^^^^^^^^         - temporary value is freed at the end of this statement
   |                        |
   |                        creates a temporary value which is freed while still in use
22 |         println!("{}", sv);
   |                        -- borrow later used here
   |
   = note: consider using a `let` binding to create a longer lived value

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0716`.
```

**왜 그런가**

- ★★★ **빌림 검사기는 「참조가 가리키는 것보다 오래 살 수 있나」를 컴파일 때 묻는다** — C++ 에서 격자의 칸이던 것이 **빌드 실패**다.
- ★★ **`E0716` 은 「임시가 문장 끝에서 풀린다」** — C++ 의 「전체 식 끝에서 죽는다」와 **같은 규칙**을 Rust 도 가진다. 다른 것은 **그 뒤에 쓰면 거부**한다는 점이다.

### 6. ★★ **`moved to heap: x`** · 실행은 **`true true`** — `y` 는 **값으로 잡혀** 옮길 필요가 없었다

**출력**(소스를 다시 싣는다 — 진단 줄이 소스 줄을 끼워 보여 주지 않는다)

```go
// esc.go
// C++ 에서 댕글링이 되는 두 모양을 Go 로 — 지역 변수의 주소와 그것을 잡은 클로저를 돌려준다
package main

import "fmt"

func localPtr() *int {
	x := 42
	return &x
}

func makeReader() func() int {
	y := 42
	return func() int { return y }
}

func main() {
	p := localPtr()
	r := makeReader()
	fmt.Println(*p == 42, r() == 42)
}
```

```text
===== go version (exit=0) =====
go version go1.27.1 linux/amd64
===== go build -gcflags='-m -l' -o escx esc.go && ./escx (cc exit=0 · run exit=0) =====
# command-line-arguments
./esc.go:7:2: moved to heap: x
./esc.go:13:9: func literal escapes to heap
./esc.go:19:13: ... argument does not escape
./esc.go:19:17: *p == 42 escapes to heap
./esc.go:19:28: r() == 42 escapes to heap
true true
```

**왜 그런가**

- ★★★ **Go 컴파일러는 주소가 함수 밖으로 나가는 지역을 힙에 둔다** — 그래서 **UB 가 아니다**(GC 가 수명을 맡는다).
- ★ 클로저가 바꾸지 않는 변수는 **값으로 복사**되어 `func literal escapes to heap` 만 남는다(Go 13번).

### 7. ★★★ **「죽은 칸이 아직 안 덮였다」만 증명하고, 「안전하다」는 증명하지 않는다** · 갈리는 자리는 **UB 의 결과라 규칙이 아니다**

```text
===== bash dang-values.sh (exit=0) =====
#   g++ -O0          g++ -O2          clang++ -O0      clang++ -O2     
1   none rc=139      none rc=139      is42 rc=0        not42 rc=0      
2   is42 rc=0        not42 rc=0       is42 rc=0        is42 rc=0       
3   not42 rc=0       not42 rc=0       not42 rc=0       not42 rc=0      
4   is42 rc=0        is42 rc=0        is42 rc=0        is42 rc=0       
5   is42 rc=0        not42 rc=0       is42 rc=0        not42 rc=0      
6   is42 rc=0        not42 rc=0       is42 rc=0        is42 rc=0       
7   is42 rc=0        not42 rc=0       is42 rc=0        is42 rc=0       
42 를 읽은 칸 16 / 28
```

- ★★★ **16 / 28 칸이 42 를 읽었다** — 테스트가 이 값을 기대하면 **통과한다.** 그래서 댕글링은 **테스트가 못 잡는 사고**다.
- ★★ **「g++ `-O2` 에서만 갈린다」를 규칙으로 적으면** 그것은 **이 판의 메모리 배치**를 규칙으로 적는 것이다(규칙 14 — 처방은 없다). 근거로 쓰는 것은 「**42 를 읽은 칸이 있다**」 하나다.

### 8. ★★★ **「임시가 참조에 직접 묶일 때만 연장된다 — 함수 호출·`std::move`·괄호 집합체가 끼면 그 줄에서 죽는다」** · **표준** 층 — 그래서 로그 순서가 근거다

- ★★★ 연장 규칙은 **어느 구현에서도 같은 약속**이고, 3번은 **참조를 한 번도 읽지 않았다** — 소멸자가 불린 **자리**만 봤으니 UB 가 끼지 않는다.
- ★★ 3번의 두 컴파일러 로그가 **한 글자도 같았다**(경고 줄만 다르다) — 약속이니 당연하고, **이것만으로 약속을 증명하는 것은 아니다**(근거는 cppreference 의 규칙 + 로그).

### 9. ★★ **`movl $0, %eax`** — g++ 는 지역의 주소 대신 **0 을 돌려주는 코드**를 만들었다

```text
===== g++ -std=c++20 -O0 -S -o - -DPROBE=1 dang01.cpp 2>/dev/null | sed -n '/^_Z9local_refv:/,/\.cfi_endproc/p' | grep -vE '^[[:space:]]+\.cfi' (exit=0) =====
_Z9local_refv:
.LFB2539:
	endbr64
	pushq	%rbp
	movq	%rsp, %rbp
	subq	$16, %rsp
	movq	%fs:40, %rax
	movq	%rax, -8(%rbp)
	xorl	%eax, %eax
	movl	$42, -12(%rbp)
	movl	$0, %eax
	movq	-8(%rbp), %rdx
	subq	%fs:40, %rdx
	je	.L3
	call	__stack_chk_fail@PLT
.L3:
	leave
	ret
```

- ★★ 그래서 호출자는 **0 번지**를 읽고 ASan 이 **`SEGV`** 로 멈춘다. clang 은 주소를 그대로 돌려줘 **`stack-use-after-return`** 이 됐다 — **같은 UB 에 두 구현이 다른 코드**를 냈다.

### 10. ★★★ **`-std=` 는 규칙을 켜는 스위치가 아니라 그 컴파일러 판이 가진 것 중 기본값을 고르는 것** — **`__cpp_range_based_for`(`202211`)** 로 판별한다

- ★★★ C++23 은 P2718 을 **포함한다**(cppreference). 이 두 컴파일러 판이 **아직 구현하지 않았을 뿐**이다 — 4번의 매크로 `201603` 이 그것을 말한다.
- ★ 같은 집안 — 규칙 12(「`-std=` 는 기본값 선택」) · g++ `-std=c++23` 의 `__cplusplus = 202100`.

### 11. 다른 주제와 잇기

- ★★ **1번의 빈 칸 12개가 그 문장의 실측**이다 — RAII 는 소멸자를 **정확한 자리**에서 부르지만, 그 뒤에 **누가 아직 가리키는지**는 어떤 도구도 전부 보지 못했다. [`c-cpp-csharp.md`](../../../c-cpp-csharp.md) 의 「C++ — RAII는 해제를 잊는 실패를 지우고, 죽은 것을 가리키는 실패는 못 지운다」 절.
- ★ **댕글링 포인터** — 재할당이 옛 버퍼를 지운 뒤 그 주소를 읽었다(`heap-use-after-free`). 29편 (4)의 `p` 판.
- ★ **「참조도 댕글링한다 — 지역을 돌려주면 포인터와 같은 경고」**(07편 (7)) · **「`const&` 가 임시를 늘린다」**(07편 (5)).

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `dang01.cpp` + `dang-grid.sh` | 탐침 7 × 도구 6 = 42칸 | ★★★ **30 / 42** · 탐침 7 경고 0 · clang `-O2` ASan 2 / 7 |
| `dang01.cpp` + `dang-uar.sh` | 탐침 2 × 컴파일러 2 × 옵션 2 | ★★ `=0` 에서 **5(둘 다) · 1(clang)** 침묵 |
| `dang01.cpp` + `dang-values.sh` | 탐침 7 × 판 4 = 28칸 | ★ **16 / 28** — 흔들리는 칸으로 선언 |
| `dang01.cpp` 탐침 1 어셈블리 · 탐침 7 ASan | g++ `-O0 -S` · g++ ASan | ★★ **`movl $0, %eax`** · `stack-use-after-scope` |
| `dang02.cpp` 수명 연장 | g++ · clang | ★★★ **연장 (a)(c)(e)(f) · 아님 (b)(d)(g)** · (g) 경고 0 |
| `dang03.cpp` 범위 `for` | 두 컴파일러 × `c++20`/`c++23` | ★★★ **네 판 다 `~Holder` 먼저 · `201603`** |
| `dangle.rs` · `esc.go` | 세 cfg · 한 빌드 | ★★ **E0515 · E0373 · E0716** · **`moved to heap: x`** |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13 · clang 18)에서만** 그렇다.

- ★★★ **격자의 경고·ASan 칸 전부** · **ASan 가짜 스택의 기본값** · **g++ 의 널 반환 코드** · **P2718 미구현** · **`__cplusplus = 202100`** · ★ **도구 없는 실행 값**(UB).

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **임시는 전체 식 끝에서 죽는다 · 직접 묶이면 참조만큼 산다 · 함수 매개변수·xvalue·괄호 집합체는 연장되지 않는다** · ★★ **C++23 의 범위 `for` 임시 연장**(구현한 판에서).

**안 돌려 본 것 / 못 잰 것**

- **못 잰 것** — ★★ **P2718 이 구현된 판(GCC 15 · Clang 19)의 동작**(이 머신에 없다) · ★ **clang `-O2` 가 스택 탐침의 읽기를 어떻게 바꿨는지**(칸만 셌다).
- **안 돌려 본 것** — ★ **`return` 에서 임시에 묶기 · `new` 식 초기화자의 임시**(cppreference 예외 목록의 나머지 둘) · ★ **`[[clang::lifetimebound]]`** · ★ **C++20 init-statement 우회.**
- ★ **「부적용인 창」** — `<type_traits>`(수명은 타입에 없다).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **4번** — 판이 오르면 `~Holder` 의 자리와 매크로.
- ★★★ **1번** — 경고 열(특히 g++ 의 `-Wdangling-reference`)과 clang `-O2` ASan 열.
- ★★ **2번** — ASan 옵션의 기본값.
