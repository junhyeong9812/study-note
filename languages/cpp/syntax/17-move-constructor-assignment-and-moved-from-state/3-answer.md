# cpp/syntax/17 — 이동 생성자·이동 대입·이동 후 상태 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·어셈블리는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **rustc 1.92.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이므로 **출력을 싣는 블록마다 그 출력을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **어셈블리의 레지스터 이름** · **진단 문구** · **객체 주소** ·\
> **libstdc++ 가 이동 후 원본에 남기는 값**이다.\
> 근거로 쓰는 것은 다음이다 — **어느 특수 멤버가 몇 번 불렸나** · **`malloc`/`free` 횟수** ·\
> **이동 뒤 원본이 널인가** · **`call` 개수** · **`cc exit`/`run exit`** · **경고 개수**.
> ★★★ **이 문서는 시간을 재지 않았다.** 「이동이 몇 배 빠르다」는 문장이 **한 줄도 없다** —\
> 7번이 센 것은 **명령과 `call` 개수까지**다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **0줄**이다 — `std::move` 는 캐스트일 뿐이다

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic move01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
    기본 생성자  #1
(1) std::move(a); 만 적는다 — 아래에 로그가 몇 줄 찍히나
(2) 그 결과를 초기화에 쓴다  L b = std::move(a);
    이동 생성자  #2 <- #1
(3) std::move(a) 의 타입은 무엇인가
    decltype(std::move(a)) 가 L&&      인가: 1
    &a 와 &r 이 같은 주소인가          : 1
(4) 만들어진 객체 수 2개 — (1)에서는 하나도 안 늘었다
```

**왜 그런가**

- ★★★ **`(1)` 아래에 로그가 한 줄도 없다.** `std::move(a);` 는 **타입만 바꾸고 끝난다.**
- ★★★ **`decltype(std::move(a))` 가 `L&&`** 다(`1`). 그 캐스트의 결과를 **초기화나 대입에 쓸 때** 비로소 이동이 뽑힌다.\
  ★ `(2)` 에서 `L b = std::move(a);` 가 **이동 생성자**를 불렀다.
- ★★ **`&a == &r` 이 `1`** 이다 — **새 객체가 안 생겼고 주소도 그대로**다.
- ★ **만들어진 객체 수는 2개** — `a` 와 `b` 뿐이다.
- ★ 「옮기는 것」은 **`std::move` 가 아니라 이동 생성자·이동 대입**이다. 정본은 [9번](../09-rvalue-references-move-and-forward/).

### 2. ★★★ **2회 대 1회** — 원본은 널이 되고 `free` 도 **1회**다

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic move02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 복사판
    a.p 가 널인가 0 · b.p 가 널인가 0 · 같은 주소인가 0
    malloc 2회
    블록을 나온 뒤 free 2회
(2) 이동판
    a.p 가 널인가 1 · b.p 가 원래 주소 그대로인가 1
    malloc 1회
    블록을 나온 뒤 free 1회  ★ 원본의 소멸자는 돌았지만 놓을 것이 없었다
```

**왜 그런가**

- ★★★ **복사판은 `malloc` 2회**다. 새 버퍼를 잡아 내용을 베꼈다 — `a.p == b.p` 가 `0` 이다.
- ★★★ **이동판은 `malloc` 1회**다. `b.p 가 원래 주소 그대로인가` 가 `1` — **짐은 한 발짝도 안 움직였다.**
- ★★★ **`a.p 가 널인가` 가 `1`** 이다. 이것이 **「훔치기」의 나머지 절반**이다.\
  ★ 이동 생성자 안의 `o.p = nullptr; o.n = 0;` 두 줄이 그 일을 한다.
- ★★★ **`free` 도 1회다** — 그런데 **`a` 의 소멸자는 돌았다.**\
  소멸자가 `if (p)` 로 널을 걸러 **놓을 것이 없어서** 세지 않았을 뿐이다.
- ★★ **이 두 줄을 빼먹으면 `free` 가 2회가 되고 그것이 이중 해제**다.\
  [15번](../15-raii-resources-as-types/) (4)가 같은 사고를 **ASan 의 `double-free`** 로 실측했다.

### 3. ★★★ 차이는 **`noexcept` 한 낱말**뿐인데 **이동 대 복사**로 갈린다

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic move03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) noexcept 가 있는 타입
  [Yes] is_nothrow_move_constructible = 1
    자리 둘을 잡아 두고 둘을 넣는다 (capacity=2)
      기본 #1
      기본 #2
    ★ 세 번째를 넣어 재할당을 일으킨다 — 있던 둘이 무엇으로 옮겨지나
      기본 #3
      이동 #4 <- #1
      이동 #5 <- #2
    capacity 4 · size 3
(2) noexcept 가 없는 타입
  [No] is_nothrow_move_constructible = 0
    자리 둘을 잡아 두고 둘을 넣는다 (capacity=2)
      기본 #1
      기본 #2
    ★ 세 번째를 넣어 재할당을 일으킨다 — 있던 둘이 무엇으로 옮겨지나
      기본 #3
      복사 #4 <- #1
      복사 #5 <- #2
    capacity 4 · size 3
```

**왜 그런가**

- ★★★ **`Yes` 는 `이동 #4 <- #1` · `이동 #5 <- #2`, `No` 는 `복사 #4 <- #1` · `복사 #5 <- #2`** 다.
- ★★★ **`vector` 가 보는 것은 `is_nothrow_move_constructible` 이다** — 출력의 `1` 과 `0` 이 그 판정이다.\
  ★ 이유는 **강한 보장**이다. 옮기는 도중에 던지면 **옛 버퍼도 새 버퍼도 온전하지 않다.**\
  복사는 실패해도 **원본이 멀쩡히 남으므로** 되돌릴 수 있다.
- ★★ **`capacity` 는 양쪽 다 2에서 4로** 갔다. **재할당 정책은 같고 옮기는 방법만 갈린다.**\
  ★ 그래서 「느려졌다」가 아니라 「**무엇이 불렸나**」로 봐야 답이 나온다.
- ★★ **clang 도 한 글자도 같았다** — 컴파일러가 아니라 **표준 라이브러리가 정하는 일**이기 때문이다.

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic move03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) noexcept 가 있는 타입
  [Yes] is_nothrow_move_constructible = 1
    자리 둘을 잡아 두고 둘을 넣는다 (capacity=2)
      기본 #1
      기본 #2
    ★ 세 번째를 넣어 재할당을 일으킨다 — 있던 둘이 무엇으로 옮겨지나
      기본 #3
      이동 #4 <- #1
      이동 #5 <- #2
    capacity 4 · size 3
(2) noexcept 가 없는 타입
  [No] is_nothrow_move_constructible = 0
    자리 둘을 잡아 두고 둘을 넣는다 (capacity=2)
      기본 #1
      기본 #2
    ★ 세 번째를 넣어 재할당을 일으킨다 — 있던 둘이 무엇으로 옮겨지나
      기본 #3
      복사 #4 <- #1
      복사 #5 <- #2
    capacity 4 · size 3
```

- ★★★ **그래서 이동 생성자·이동 대입에는 `noexcept` 를 붙이는 것이 기본형이다.**\
  ★ 「붙이면 빨라진다」가 아니라 「**안 붙이면 표준 라이브러리가 이동을 안 쓴다**」로 외운다.

### 4. ★★★ **`unique_ptr` 만 보장**이고 나머지 숫자는 **libstdc++ 의 선택**이다

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic move04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 표준이 「널」이라고 못 박은 것 — unique_ptr
    u1.get() == nullptr : 1   (표준 보장)
    *u2                 : 7
(2) 표준이 「유효하되 미지정」이라고만 한 것 — 이 구현이 무엇으로 두나
    짧은 string : size=0  empty=1  capacity=15  값=""
    긴 string   : size=0  empty=1  capacity=15
    vector      : size=0  capacity=0
(3) 이동당한 원본에 무엇을 해도 되나 — 표준이 허락한 것만
    다시 대입한 뒤 s1 = "다시 넣는다"  ·  clear 뒤 v1.size()=0
    t1="짧다" t2.size()=64 v2.size()=3
```

**왜 그런가**

- ★★★ **표준이 못 박은 것은 하나다** — 「이동 후 `unique_ptr::get()` 은 널」. `(1)` 의 `1` 이 그 보장이다.
- ★★★ **`(2)` 의 숫자는 전부 관찰이다.** 표준이 `string`·`vector` 에 대해 말한 것은\
  「**유효하되 미지정**」뿐이다 — **불변식은 지켜지되 값은 정해지지 않았다.**
- ★★ **짧은 것과 긴 것의 이동 후 `capacity` 가 둘 다 15** 다.\
  ★ libstdc++ 의 `std::string` 은 **15바이트까지 객체 안에** 담는다(작은 문자열 최적화).\
  긴 쪽은 **힙 버퍼를 넘겨주고 자기는 내부 버퍼로 돌아갔다.** 이런 세부가 **구현 층**이다.
- ★ **`(3)` 에서 허용된 것 둘** — **다시 대입하는 것**(`s1 = "다시 넣는다";`)과\
  **전제조건이 없는 연산**(`v1.clear()`·`size()`·`empty()`).\
  ★ **금지된 것**은 전제조건이 있는 연산이다 — `v1.front()`·`*u1` 처럼 「비어 있지 않아야」 하는 것.
- ★★★ **코드에 쓸 수 있는 규칙은 하나다** — 「**이동한 뒤에는 대입하거나 파괴한다**」.

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic move04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 표준이 「널」이라고 못 박은 것 — unique_ptr
    u1.get() == nullptr : 1   (표준 보장)
    *u2                 : 7
(2) 표준이 「유효하되 미지정」이라고만 한 것 — 이 구현이 무엇으로 두나
    짧은 string : size=0  empty=1  capacity=15  값=""
    긴 string   : size=0  empty=1  capacity=15
    vector      : size=0  capacity=0
(3) 이동당한 원본에 무엇을 해도 되나 — 표준이 허락한 것만
    다시 대입한 뒤 s1 = "다시 넣는다"  ·  clear 뒤 v1.size()=0
    t1="짧다" t2.size()=64 v2.size()=3
```

- ★★★ **clang 으로 돌려도 같은 숫자가 나왔다는 것이 보장의 근거가 못 된다** — **같은 libstdc++ 를 썼기 때문**이다.\
  갈리는 것은 **컴파일러가 아니라 표준 라이브러리**다.

### 5. ★★ **멤버별로 갈린다** · `const` 한 낱말에 **복사로 되돌아간다**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic move05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 멤버가 전부 이동 가능하면
      멤버: 이동
(2) 멤버 하나가 복사만 되면 — 그 멤버만 복사되나, 전부 복사되나
      멤버: 이동
      멤버: 복사(이동 생성자가 없는 타입)
(3) const 를 move 하면
      멤버: 복사
(4) const 를 안 붙이면
      멤버: 이동
```

**왜 그런가**

- ★★★ **`(2)` 에서 로그가 두 줄이고 서로 다르다** — `멤버: 이동` 과 `멤버: 복사(이동 생성자가 없는 타입)`.\
  ★ 「멤버 하나가 복사만 되면 전부 복사」가 아니다. **컴파일러가 만드는 이동 생성자는 멤버마다 따로 고른다.**
- ★★★ **`(3)` 과 `(4)` 는 소스가 `const` 한 낱말만 다르다.**\
  `const Tr` 에 `std::move` 를 쓰면 타입이 **`const Tr&&`** 가 되는데,\
  이동 생성자는 **`Tr&&`** 를 받으므로 **안 맞는다.** 그래서 **`const Tr&` 를 받는 복사 생성자**가 뽑힌다.
- ★★ **에러도 경고도 안 난다.** 이 주제에서 가장 조용한 사고이고, **로그를 찍어야만** 보인다.
- ★ **처방** — 이동을 기대하는 자리에 **`const` 를 안 붙인다.**

### 6. ★ **2줄 대 4줄** — 생략이 막혀 이동 생성자가 한 번 더 돈다

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic move06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
move06.cpp: In function ‘L moved()’:
move06.cpp:16:35: warning: moving a local object in a return statement prevents copy elision [-Wpessimizing-move]
   16 | L moved()  { L t; return std::move(t); }       // std::move 를 붙여 돌려준다
      |                          ~~~~~~~~~^~~
move06.cpp:16:35: note: remove ‘std::move’ call
(1) return t;
    기본 생성자  #1
    소멸자        #1
(2) return std::move(t);
    기본 생성자  #2
    이동 생성자  #3 <- #2
    소멸자        #2
    소멸자        #3
(3) 만들어진 객체 수 3개
```

**왜 그런가**

- ★★★ **`return t;` 는 `기본 생성자 #1` + `소멸자 #1` 두 줄**이다. **이동조차 안 일어났다**(NRVO).
- ★★★ **`return std::move(t);` 는 네 줄**이다 — `기본 #2` · `이동 #3 <- #2` · `소멸 #2` · `소멸 #3`.
- ★★★ **이유는 [16번](../16-copy-constructor-and-copy-assignment/) (2)와 같다.**\
  NRVO 는 「**이름 있는 지역 변수를 그대로 돌려줄 때**」의 생략인데,\
  `std::move(t)` 는 **더 이상 그 변수가 아니라 식**이다. **그 자격을 스스로 버린 것**이다.
- ★★ **두 컴파일러가 다 경고한다** — `-Wpessimizing-move`, 문구까지 「remove `std::move` call」로 같은 뜻이다.\
  ★ **이 주제에서 컴파일러가 말해 주는 거의 유일한 자리**다(9번은 전부 0건이다).

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic move06.cpp -o ex (cc exit=0) =====
move06.cpp:16:26: warning: moving a local object in a return statement prevents copy elision [-Wpessimizing-move]
   16 | L moved()  { L t; return std::move(t); }       // std::move 를 붙여 돌려준다
      |                          ^
move06.cpp:16:26: note: remove std::move call here
   16 | L moved()  { L t; return std::move(t); }       // std::move 를 붙여 돌려준다
      |                          ^~~~~~~~~~ ~
1 warning generated.
```

- ★ **만들어진 객체 수 3개** — `(1)` 이 1개, `(2)` 가 2개다.

### 7. ★★ **`call` 이 2 대 0** 이다 — 명령 수는 근거가 아니다

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 -S -masm=intel move08.cpp -o move08.s && sed -n '/^_Z9make_copyRK3Box:/,/\.cfi_endproc/p' move08.s | grep -vE '^\s*\.(cfi|loc|file|size|type|globl|p2align|section|ident|align)' (exit=0) =====
_Z9make_copyRK3Box:
.LFB63:
	endbr64
	push	r12
	mov	r12, rsi
	push	rbp
	push	rbx
	mov	rbp, QWORD PTR 8[rsi]
	mov	rbx, rdi
	mov	rdi, rbp
	call	malloc@PLT
	mov	QWORD PTR 8[rbx], rbp
	mov	rsi, QWORD PTR [r12]
	mov	rcx, rbp
	mov	QWORD PTR [rbx], rax
	mov	rdx, rbp
	mov	rdi, rax
	call	__memcpy_chk@PLT
	mov	rax, rbx
	pop	rbx
	pop	rbp
	pop	r12
	ret
```

```text
===== sed -n '/^_Z9make_moveR3Box:/,/\.cfi_endproc/p' move08.s | grep -vE '^\s*\.(cfi|loc|file|size|type|globl|p2align|section|ident|align)' (exit=0) =====
_Z9make_moveR3Box:
.LFB64:
	endbr64
	mov	rdx, QWORD PTR [rsi]
	mov	rax, rdi
	mov	QWORD PTR [rsi], 0
	mov	QWORD PTR [rdi], rdx
	mov	rdx, QWORD PTR 8[rsi]
	mov	QWORD PTR 8[rsi], 0
	mov	QWORD PTR 8[rdi], rdx
	ret
```

```text
===== echo "복사판  명령 $(sed -n '/^_Z9make_copyRK3Box:/,/\.cfi_endproc/p' move08.s | grep -cE '^[[:space:]][a-z]') · call $(sed -n '/^_Z9make_copyRK3Box:/,/\.cfi_endproc/p' move08.s | grep -c 'call')" (exit=0) =====
복사판  명령 21 · call 2
===== echo "이동판  명령 $(sed -n '/^_Z9make_moveR3Box:/,/\.cfi_endproc/p' move08.s | grep -cE '^[[:space:]][a-z]') · call $(sed -n '/^_Z9make_moveR3Box:/,/\.cfi_endproc/p' move08.s | grep -c 'call')" (exit=0) =====
이동판  명령 9 · call 0
```

**왜 그런가**

| | 복사판 `make_copy` | 이동판 `make_move` |
|---|---|---|
| 명령 개수 | **21** | **9** |
| ★★★ **`call` 개수** | ★★★ **2** | ★★★ **0** |
| 부르는 것 | `malloc@PLT` · `__memcpy_chk@PLT` | — |
| 레지스터 저장/복원 | `push`/`pop` **3쌍** | 없음 |

- ★★★ **근거로 쓸 수 있는 것은 `call` 개수다.** 복사판은 **힙에 두 번 다녀오고** 이동판은 **한 번도 안 간다.**\
  ★ 이 사실은 2번의 `malloc 2회 대 1회` 와 **같은 것을 다른 창으로 본 것**이다.
- ★★ **명령 개수 21 대 9 는 구현 정의다.** 다른 컴파일러·다른 최적화 수준·다른 ABI 에서 움직인다.\
  ★ [15번](../15-raii-resources-as-types/) (7)이 같은 창에서 **최적화 수준마다 수가 달라지는 것**을 실측했다.
- ★★★ **재지 않은 것은 시간이다.** 명령 수는 시간이 아니다 —\
  캐시·분기 예측·할당기의 상태가 전부 빠져 있다. **재려면 벤치마크 하네스가 따로 필요하다.**\
  이 문서에 「이동이 몇 배 빠르다」는 문장은 **한 줄도 없다.**

### 8. ★★★ **러스트는 컴파일이 안 되고 C++ 은 된다** — 그리고 C++ 쪽은 **UB 도 아니다**

**출력**

```text
===== which rustc && rustc --version (exit=0) =====
/home/jun/.cargo/bin/rustc
rustc 1.92.0 (ded5c06cf 2025-12-08)
```

```rust
// movers.rs
// 러스트는 이동이 기본이고, 이동 후 원본을 컴파일러가 막는다
fn main() {
    let a = String::from("훔칠 것이 여기 있다");
    let b = a;                      // 이동 — clone 이 아니다
    println!("b = {}", b);
    println!("a = {}", a);          // 이동당한 원본을 다시 읽는다
}
```

```text
===== rustc --edition 2021 movers.rs -o exr (exit=1) =====
error[E0382]: borrow of moved value: `a`
 --> movers.rs:6:24
  |
3 |     let a = String::from("훔칠 것이 여기 있다");
  |         - move occurs because `a` has type `String`, which does not implement the `Copy` trait
4 |     let b = a;                      // 이동 — clone 이 아니다
  |             - value moved here
5 |     println!("b = {}", b);
6 |     println!("a = {}", a);          // 이동당한 원본을 다시 읽는다
  |                        ^ value borrowed here after move
  |
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider cloning the value if the performance cost is acceptable
  |
4 |     let b = a.clone();                      // 이동 — clone 이 아니다
  |              ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

```cpp
/* move09.cpp */
// 러스트와 같은 코드를 C++ 로 — 이동당한 원본을 다시 읽는다
#include <cstdio>
#include <string>
#include <utility>

int main() {
    std::string a = "훔칠 것이 여기 있다";
    std::string b = std::move(a);          // 이동
    std::printf("b = %s\n", b.c_str());
    std::printf("a = \"%s\"  (size=%zu)\n", a.c_str(), a.size());   // 이동당한 원본을 다시 읽는다
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic move09.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
b = 훔칠 것이 여기 있다
a = ""  (size=0)
```

**왜 그런가**

- ★★★ **러스트는 컴파일에서 막는다** — `error[E0382]: borrow of moved value`.\
  ★ 진단이 **세 줄을 짚는다** — `a` 가 어디서 생겼고(3행), 어디서 옮겨졌고(4행), 어디서 다시 쓰였나(6행).\
  ★ **`Copy` 를 구현하지 않아서**라는 이유까지 붙는다. 러스트에서는 **이동이 기본**이다.
- ★★★ **C++ 은 컴파일된다.** `cc exit=0` · **경고 0건** · `run exit=0` 이고 **빈 문자열**이 찍힌다.
- ★★★ **그리고 그것은 UB 가 아니다.** `a.c_str()`·`a.size()` 는 **전제조건이 없는 연산**이라 **합법**이다.\
  ★ 그래서 **sanitizer 가 잡을 것이 없다** — 9번의 ASan 0건이 그 결과다.\
  ★ 「**규칙을 어긴 것이 아니라 기대와 다른 것**」이 이 주제 사고의 성격이다.
- ★★★ **찍힌 빈 문자열은 관찰이다.** 표준이 말한 것은 「유효하되 미지정」뿐이고,\
  `""` 와 `size=0` 은 **libstdc++ 의 선택**이다(4번).
- ★★ **러스트가 치르는 대가** — 옮긴 값을 **다시 쓸 방법이 아예 없다.**\
  C++ 은 **다시 대입하면 쓸 수 있다**(4번의 `(3)`). **금지의 강도와 유연성이 맞바꿔진 것**이다.
- ★ **러스트에는 「빈 껍데기를 손으로 만드는」 수고도 없다** — 이동한 값은 **원본 자리에서 `drop` 되지 않는다.**\
  그래서 2번의 `o.p = nullptr` 과 「널을 견디는 소멸자」가 **필요 없다.**

### 9. ★★ 탐침 여섯 중 **0개**가 답했다 — **ASan 도 0건**이다

**출력**

```cpp
/* move07.cpp */
// 이동에서 틀리는 자리 여섯을 심었다 — 컴파일러가 몇 군데에서 말하는지 센다
#include <cstdio>
#include <string>
#include <utility>
#include <vector>

struct Q1 {                                   // 1. 이동 생성자에 noexcept 를 안 붙였다
    std::string s;
    Q1() {}
    Q1(const Q1& o) : s(o.s) {}
    Q1(Q1&& o) : s(std::move(o.s)) {}
};
struct Q2 {                                   // 2. 이동 생성자가 원본을 비우지 않는다
    int* p;
    Q2() : p(new int(1)) {}
    ~Q2() { delete p; }
    Q2(const Q2& o) : p(new int(*o.p)) {}
    Q2(Q2&& o) noexcept : p(o.p) {}           // o.p 를 널로 안 만들었다 — 이중 해제가 열린다
};

void use_after_move() {                       // 3. 이동한 뒤 원본을 다시 읽는다
    std::string a = "무엇이 남나";
    std::string b = std::move(a);
    std::printf("    이동 뒤 a.size()=%zu b.size()=%zu\n", a.size(), b.size());
}
void move_a_const() {                         // 4. const 객체에 std::move 를 쓴다
    const std::string a = "복사로 되돌아간다";
    std::string b = std::move(a);
    (void)b;
}
void move_into_const_ref() {                  // 5. std::move 의 결과를 const& 로 받는다
    std::string a = "옮겨지지 않는다";
    const std::string& r = std::move(a);
    (void)r;
}
void push_without_reserve() {                 // 6. 이동이 없는 타입을 vector 에 담는다
    std::vector<Q1> v;
    for (int i = 0; i < 4; ++i) v.push_back(Q1());
}

int main() {
    Q1 a; Q1 b = std::move(a); (void)b;
    Q2 c; Q2 d = std::move(c); d.p = nullptr;  // 이중 해제를 피해 치운다
    use_after_move();
    move_a_const();
    move_into_const_ref();
    push_without_reserve();
    std::printf("여섯 자리 전부 컴파일됐다\n");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic move07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
    이동 뒤 a.size()=0 b.size()=16
여섯 자리 전부 컴파일됐다
```

```text
===== echo "move07 탐침 여섯  g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic move07.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
move07 탐침 여섯  g++ 경고 0
===== echo "move07 탐침 여섯  clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic move07.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
move07 탐침 여섯  clang 경고 0
===== echo "move07 을 ASan 으로 돌리면: $(g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. move07.cpp -o exa 2>/dev/null; ./exa >/dev/null 2>asan17.txt; grep -cE 'ERROR: (Address|Leak)Sanitizer' asan17.txt) 건" (exit=0) =====
move07 을 ASan 으로 돌리면: 0 건
===== echo "그 리포트의 요약: $(grep -hE '^SUMMARY' asan17.txt | head -1 | grep . || echo 리포트 없음)" (exit=0) =====
그 리포트의 요약: 리포트 없음
```

**왜 그런가**

| 심은 것 | g++ | clang | ASan | 실제로는 |
|---|---|---|---|---|
| 1. 이동 생성자에 `noexcept` 를 안 붙였다 | 0 | 0 | — | ★★★ 재할당이 **복사로 간다**(3번) |
| 2. 이동 생성자가 원본을 안 비운다 | 0 | 0 | — | ★★★ **이중 해제가 열린다**(2번) |
| 3. 이동한 뒤 원본을 다시 읽는다 | 0 | 0 | — | ★★ 값은 **미지정**이다(4번) |
| 4. `const` 객체에 `std::move` | 0 | 0 | — | ★★ **복사로 되돌아간다**(5번) |
| 5. `std::move` 의 결과를 `const&` 로 받는다 | 0 | 0 | — | ★ **아무것도 안 옮겨진다** |
| 6. 이동이 `noexcept` 가 아닌 타입을 `vector` 에 담는다 | 0 | 0 | — | ★★★ 자랄 때마다 **복사**다(3번) |

- ★★★ **답한 것 0, 침묵한 것 6**이고 `cc exit=0` · `run exit=0` 이다.
- ★★★ **ASan 도 0건이다.** 이 배치의 다른 셋과 비교하면 차이가 선명하다.

| 편 | 컴파일러 경고 | ASan |
|---|---|---|
| [16번](../16-copy-constructor-and-copy-assignment/) 탐침 여섯 | **1** | **24바이트 · 3할당** |
| ★★★ **17번(여기) 탐침 여섯** | ★★★ **0** | ★★★ **0건** |
| [목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/) 탐침 여섯 | **2** | **8바이트 · 1할당** |
| [목록의 **19번 주제**](../19-inheritance-virtual-functions-override-final/) 탐침 여덟 | **1** | **`new-delete-type-mismatch`** |

- ★★★ **이유가 분명하다** — 이동의 사고는 대부분 **「규칙 위반」이 아니라** 「**기대와 다름**」이다.\
  `noexcept` 를 안 붙인 것도, `const` 를 `move` 한 것도, 이동한 원본을 읽는 것도 **전부 합법**이다.\
  **합법인 것을 도구가 말해 줄 수는 없다.**
- ★★★ **그래서 이 주제는 계수 로그 없이는 아무것도 증명되지 않는다.**\
  ★ 예외가 하나 — **6번의 `-Wpessimizing-move`.** 그것만이 컴파일러가 스스로 말해 준 자리다.

### 10. ★★ **표준 · 미명시 · 관찰** — 세 층에 하나씩 있다

- 「**`vector` 재할당이 `noexcept` 이동만 쓴다**」 — ★★★ **표준**이다.\
  `push_back` 의 **강한 예외 보장**이 그것을 요구한다. 구현의 재량이 아니다.
- 「**이동한 `std::string` 의 `size()` 가 0 이다**」 — ★★★ **미명시**다.\
  표준이 말한 것은 「유효하되 미지정」뿐이다. `0` 은 **libstdc++ 가 그렇게 둔 것**이다.
- ★★★ **두 컴파일러에서 같은 숫자가 나온 것은 보장의 근거가 못 된다.**\
  갈리는 것은 **컴파일러가 아니라 표준 라이브러리**이고, 여기서는 **양쪽이 같은 libstdc++ 를 썼다.**\
  ★ 다른 구현(libc++·MSVC STL)에서는 다를 수 있고 **그것이 표준이 허락한 것**이다.
- 「**이동한 원본을 다시 읽는 것**」 — ★★★ **UB 가 아니다.**\
  전제조건이 없는 연산을 부르는 한 **합법**이고, **그래서 sanitizer 가 침묵한다**(9번).\
  ★ UB 인 것은 **전제조건이 있는 연산**(`front()`·`*u`)을 부르는 쪽이다.

### 11. 다른 주제와 잇기

- **`std::move` 가 캐스트라는 것**의 정본은 [9번](../09-rvalue-references-move-and-forward/)이고, 값 범주 자체는 [8번](../08-value-categories-lvalue-prvalue-xvalue/)이다.
- 6번의 「**생략이 막힌다**」를 실측한 것은 [16번](../16-copy-constructor-and-copy-assignment/)의 **(2)가 그 자리다** —\
  거기서 `-fno-elide-constructors` 로 **NRVO 가 재량임**을 보였다. 여기 6번은 **그 재량을 스스로 버리는 쪽**이다.
- **이동한 원본도 파괴된다**는 보장은 [14번](../14-destructors-and-deterministic-destruction/)에서 나오고,\
  **빈 껍데기와 널을 견디는 소멸자**는 [15번](../15-raii-resources-as-types/) (4)(5)가 실측했다.
- ★★★ **러스트는 이동당한 원본을 컴파일러가 막는다** — Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **8번**([`08-ownership-and-move/`](../../../rust/syntax/08-ownership-and-move/)).\
  ★ **C++ 이 안 막는 이유는 「미지정이되 유효」라는 계약을 골랐기 때문**이다 —\
  옮긴 뒤에도 **대입해서 다시 쓸 수 있게** 하려고 그 자유를 남겼다(4번의 `(3)`).
- ★ **`noexcept` 의 전모**는 목록의 **53번 주제**, **`vector` 재할당 정책**은 **41번 주제**가 정본이다.
- ★★ **다음 편이 이 사슬의 결론이다** — [목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/)(0/3/5의 법칙).\
  9번의 탐침 1번·2번이 거기서 **「무엇이 자동 생성되나」 격자**로 다시 나온다.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `move01.cpp` `std::move` | g++ 1회 | ★★★ `(1)` **로그 0줄** · `decltype` 이 `L&&`(`1`) · `&a == &r`(`1`) · 객체 **2개** |
| `move02.cpp` 훔치기 | g++ 1회 | ★★★ `malloc` **2 대 1** · 원본 널 **1** · `free` **1**(소멸자는 돌았다) |
| `move03.cpp` `noexcept` | g++ · clang 각 1회 | ★★★ **이동 2줄 대 복사 2줄** · 트레이트 **1 대 0** · `capacity` **양쪽 2→4** · 두 컴파일러 동일 |
| `move04.cpp` 이동 후 상태 | g++ · clang 각 1회 | ★★★ `unique_ptr` **널 보장** · `string` **size 0 / capacity 15**(구현) · `vector` **capacity 0**(구현) |
| `move05.cpp` 조용한 복사 | g++ 1회 | ★★★ 멤버별로 갈린다(`이동` + `복사`) · `const` 한 낱말에 **복사로 되돌아감** · 경고 0건 |
| `move06.cpp` `return std::move` | g++ · clang 각 1회 | ★★ **2줄 대 4줄** · 두 컴파일러 다 `-Wpessimizing-move` |
| `move08.cpp` 어셈블리 | g++ 1회(`-O2 -S`) + 세기 2회 | ★★ 명령 **21 대 9** · ★★★ **`call` 2 대 0** |
| `movers.rs` · `move09.cpp` | rustc 1회 · g++ 1회 | ★★★ rustc **`error[E0382]`**(exit=1) · g++ **exit=0 · 경고 0건 · 빈 문자열** |
| `move07.cpp` 탐침 여섯 | g++ · clang 각 1회 + ASan 1회 | ★★★ **경고 0 · 0** · **ASan 0건**(리포트 없음) |
| `move10.cpp` 형태 | g++ 1회 | `a=0 b=0 c=64` |
| `move11.cpp` 금지 사례 | g++ 1회 | **에러 3건**(`unique_ptr` 복사 · 이동 전용 값 전달 · `T&&` 에 lvalue) |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · libstdc++ · ASan)에서만** 그렇다.

- ★★★ **4번의 숫자 전부** — `string` 의 `size`·`capacity`, `vector` 의 `capacity`. **미명시**다.
- ★★★ **7번의 명령 개수 21 대 9** — 최적화 수준·ABI 에 따라 움직인다. **`call` 개수 쪽이 성질에 가깝다.**
- ★★ **`vector` 의 성장 배수**(2배) · **진단 문구와 경고 이름 전부.**
- ★ **rustc 진단의 형태**(소스를 끼워 보여 주는 것) — 판마다 달라질 수 있다.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **`std::move` 는 캐스트**이고 **그 자체로는 아무것도 안 옮기는** 것.
- **이동한 원본도 파괴되는** 것 — 그래서 **빈 껍데기를 안전하게 만들어야** 한다.
- ★★★ **`vector` 재할당이 `noexcept` 이동만 쓰는** 것 — `push_back` 의 강한 보장이 요구한다.
- ★★★ **`unique_ptr` 의 이동 후 `get()` 이 널인** 것.
- **`const` rvalue 에는 이동이 안 뽑히고 복사로 되돌아가는** 것.
- **`return std::move(t);` 가 NRVO 대상이 아닌** 것.
- **이동 후 원본이 「유효하되 미지정」인** 것 — **전제조건 없는 연산과 대입은 합법**이다.

**UB 의 결과라 보장이 아닌 것**(관찰로만 읽는다)

- ★★ **원본을 안 비운 이동 뒤의 이중 해제**(9번의 탐침 2번). 그 실측은 [15번](../15-raii-resources-as-types/) (4)에 있다.
- ★★★ **「이동한 원본을 읽는 것」은 UB 가 아니다** — 그래서 **값이 틀려도 도구가 말을 안 한다.**\
  이것이 이 주제가 조용한 **진짜 이유**다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **libc++ 로 4번을 다시 찍는 판**(libstdc++ 로만 봤다 — **그것이 4번의 결론을 가장 세게 시험할 판**이다) ·\
  ★ **자기 이동**(`a = std::move(a)`) · ★ **`push_back` 으로 3번을 다시 던지는 판**(`emplace_back` 으로만 했다) ·\
  ★ **clang 으로 7번의 어셈블리**(g++ 로만 쟀다) · ★ **`-O0`\~`-Os` 의 7번 판 격자**.
- **못 잰 것** — ★★★ **「이동이 시간을 얼마나 덜 쓰나」.** 이 문서가 센 것은 **호출 횟수·할당 횟수·`call` 개수까지**다.\
  ★★ **런타임 할당 계수기**가 C++ 표준에 없어 2번은 **소스에 계수기를 손으로 심었다.**
- ★★★ **「잴 것이 없는」 칸도 있다** — 9번의 ASan.\
  0건은 「안 돌렸다」가 아니라 「**돌렸는데 잡을 규칙 위반이 없다**」이다. **그 0 자체가 이 편의 결론**이다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **4번의 숫자 전부** — 표준 라이브러리 구현이 바뀌면 통째로 움직인다.
- ★★★ **9번의 탐침 중 하나라도 답하기 시작했는지**(지금은 **여섯 다 0건**).\
  ★ 특히 **`noexcept` 없는 이동**을 경고하는 컴파일러가 나오면 이 편의 결론이 바뀐다.
- ★★ **7번의 명령·`call` 개수** — GCC 가 인라인 정책을 바꾸면 움직인다.
- ★ **rustc 의 `E0382` 진단 형식** — 8번의 블록이 그대로인지.
