# c/syntax/13 — `goto cleanup` 관용구: 「**분기가 아니라 중복을 줄인다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고·에러·어셈블리는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 작업 디렉터리는 `/tmp/c13`, 소스 파일명은 언제나 `ex.c` 다.\
> ★★ **실행 블록은 `./x 2>&1 | cat` 로 받았다** — sanitizer 는 stderr, `printf` 는 stdout 이라 순서가 실행 환경에 달린다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 주소 · ASan 의 `pc`/`bp`/`sp` · PID · `BuildId` | **`파일:줄:칸`** · 진단 본문 · 프레임 함수 이름 |
> | 초기화 안 된 변수의 값 | **종료 코드** · 경고 건수 · 플래그 이름 |
> | 어셈블리의 레지스터 이름 | 어셈블리의 명령·분기·`call` 개수 |
>
> ★ **에러가 난 것도 그대로 실었다** — 종료 코드를 같이 적었다.
> ★★ **이 주제의 답은 「어느 도구가 무엇이라 하나」다.** UB 가 둘뿐이라 sanitizer 가 할 일이 적고,
> 대신 **어셈블리와 LeakSanitizer** 가 근거를 낸다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 자원 셋을 잡는 함수를 단계마다 실패시키면 — **푼 개수 == 잡은 개수** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, exit=0) =====
fail_at=0
  [1] buf   획득
  [2] file  획득
  [3] table 획득
  [*] 본작업 성공
  <-- table 해제
  <-- file  해제
  <-- buf   해제
  rc=0
fail_at=1
  [1] buf   획득 실패
  rc=-1
fail_at=2
  [1] buf   획득
  [2] file  획득 실패
  <-- buf   해제
  rc=-1
fail_at=3
  [1] buf   획득
  [2] file  획득
  [3] table 획득 실패
  <-- file  해제
  <-- buf   해제
  rc=-1
fail_at=4
  [1] buf   획득
  [2] file  획득
  [3] table 획득
  [4] 본작업 실패
  <-- table 해제
  <-- file  해제
  <-- buf   해제
  rc=-1
===== gcc -std=c17 -Wall -Wextra -pedantic -g -fsanitize=address,undefined =====
(출력이 위와 바이트 단위로 같고 진단 0줄, exit=0)
```

**왜 그런가**

```text
   fail_at  잡은 것          뛴 라벨      푼 것                 해제 줄 수
   -------  ---------------  ----------   -------------------   ---------
      1     (없음)            out          (없음)                    0
      2     buf               out_buf      buf                       1
      3     buf file          out_file     file buf                  2
      4     buf file tbl      out_tbl      tbl file buf              3
      0     buf file tbl      (안 뜀)       tbl file buf              3
```

- **해제 줄 수는 0 · 1 · 2 · 3 · 3** 이다. **잡은 개수와 언제나 같다.**
- **`fail_at=2` 에서 `fclose` 는 불리지 않는다.** `goto out_buf;` 가 **`out_file:` 을 건너뛰어** 착지하기 때문이다.\
  ★ 그래야 한다 — 그 시점에 `f` 는 여전히 `NULL` 이고, **`fclose(NULL)` 은 죽는다**(3번 답).
- **해제 순서는 획득의 역순**이다. 라벨을 **아래로 갈수록 먼저 풀 것**으로 쌓았고,\
  `break` 같은 것이 없으니 **라벨을 지나 그대로 흘러내린다.**
- **경고 0건**이고 **ASan+UBSan 진단 0줄**이다 — 누수도 이중 해제도 없다.

### 2. 같은 일을 세 가지 모양으로 짜서 `-O2` 로 컴파일하면 — **`goto` 와 중첩 `if` 가 같다** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -S -masm=intel (경고 0 건, exit=0) =====
함수            명령     j*   call test/cmp
with_goto        39      4      7      3
with_nest        39      4      7      3
with_dup         45      5     10      3
===== gcc -std=c17 -O<수준> -S -masm=intel — 명령 수 =====
수준       goto     nest      dup
-O0          45       36       50
-O1          39       39       48
-O2          39       39       45
-O3          39       39       45
-Os          37       37       41
===== 소스 쪽 세기 (빈 줄 제외) =====
with_goto : 줄 15 · 해제 호출이 소스에 적힌 횟수 3
with_nest : 줄 17 · 해제 호출이 소스에 적힌 횟수 3
with_dup  : 줄 11 · 해제 호출이 소스에 적힌 횟수 6
```

**왜 그런가**

```text
   -O2 에서 with_goto 와 with_nest 의 명령 열을 라벨 정규화 후 diff 하면
   다른 줄이 6개뿐이고, 전부 레지스터 이름이다 :

       <  mov  r13d, -1        >  mov  r12d, -1
       <  mov  r12, rax        >  mov  r13, rax
       <  mov  rdi, r12        >  mov  rdi, r13
       ...

   ★ 구조가 같다. 분기도 call 도 test/cmp 도 개수가 같다.
```

- ★★★ **`goto` 판이 중첩 `if` 판보다 분기가 적지 않다.** `-O2` 에서 **둘 다 명령 39 · 분기 4 · `call` 7.**\
  `-O1`·`-Os` 에서는 **정규화한 명령 열까지 한 글자도 같았다.**
- ★ **`-O0` 에서는 순서가 뒤집힌다** — 중첩 `if` 가 **36**, `goto` 가 **45**.\
  **한 최적화 수준만 보고 단정하면 정반대 결론**을 적는다.
- ★★ **비싼 것은** 「**정리 코드를 복사한 판**」이다 — `-O2` 에서 **명령 45 · 분기 5 · `call` 10.**\
  `call` 이 셋 더 있는 것이 소스의 「**해제 호출 6곳**」과 정확히 맞는다.
- ★★ **그래서 이 관용구가 파는 것은 속도가 아니라 「고칠 자리 수」다.**\
  자원이 하나 늘 때 `goto` 판과 중첩 `if` 판은 **한 곳**, 복사판은 **네 곳**을 고쳐야 한다.
- **`goto` 판과 중첩 `if` 판 사이의 선택은 가독성 문제다.** 중첩 판은 **들여쓰기가 자원 개수만큼** 깊어지고,\
  `goto` 판은 **평평하되 라벨을 읽어야** 한다.

### 3. `free` 와 `fclose` 에 널을 넘기면 — **한쪽만 안전하다** ★★

**출력**

```text
===== 소스: ex.c (13-i) =====
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    char *p = NULL;
    free(p);                       /* 표준이 보장한다 — 아무 일도 안 일어난다 */
    printf("free(NULL) 통과\n");
    fflush(stdout);

    FILE *f = NULL;
    fclose(f);                     /* ★ 보장이 없다 */
    printf("fclose(NULL) 통과\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, cc exit=0) =====
free(NULL) 통과
(여기서 죽는다 — 셸이 "세그멘테이션 오류 (코어 덤프됨)" 를 찍었고 run exit=139)
```

```text
===== gcc -std=c17 -g -fsanitize=address,undefined · ./x 2>&1 | cat  (run exit=1) =====
free(NULL) 통과
ex.c:11:5: runtime error: null pointer passed as argument 1, which is declared to never be null
AddressSanitizer:DEADLYSIGNAL
=================================================================
==3647034==ERROR: AddressSanitizer: SEGV on unknown address 0x000000000000 (pc 0x78783be85384 bp 0x7ffcb7819550 sp 0x7ffcb7819530 T0)
==3647034==The signal is caused by a READ memory access.
==3647034==Hint: address points to the zero page.
    #0 0x78783be85384 in _IO_new_fclose libio/iofclose.c:48
    #1 0x78783cadf425 in fclose ../../../../src/libsanitizer/sanitizer_common/sanitizer_common_interceptors.inc:6295
    #2 0x78783cadf425 in fclose ../../../../src/libsanitizer/sanitizer_common/sanitizer_common_interceptors.inc:6288
    #3 0x640db0dc72f4 in main /tmp/c13/ex.c:11
    #4 0x78783be2a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #5 0x78783be2a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #6 0x640db0dc71a4 in _start (/tmp/c13/xs+0x11a4) (BuildId: 272993278d9ae48c32427cdb4eb819f0068449d0)

AddressSanitizer can not provide additional info.
SUMMARY: AddressSanitizer: SEGV libio/iofclose.c:48 in _IO_new_fclose
==3647034==ABORTING
```

> **대조할 것은 숫자가 아니라 성질이다.** PID(`==3647034==`)·`pc`/`bp`/`sp` 주소·`BuildId` 는 **실행마다 바뀐다.**\
> 근거는 **`SEGV on unknown address 0x000000000000`** · **`_IO_new_fclose`** · **`main /tmp/c13/ex.c:11`** · **`run exit=1`** 이다.\
> ★ **`free(NULL) 통과` 가 맨 앞에 오는 것**은 소스에 `fflush(stdout);` 이 있어서다.

**왜 그런가**

- **한 줄만 찍고 죽는다.** `free(NULL) 통과` 뒤 `fclose(NULL)` 에서 **SIGSEGV**, 종료 코드 **139**(= 128 + 11).
- **컴파일 경고는 0건**이다 — 모든 플래그 조합에서. **컴파일러는 값이 널인지 모른다.**
- ★ **UBSan 이 추가로 말해 준다** — `null pointer passed as argument 1, which is declared to never be null`.\
  ★ **근거는 표준이 아니라 구현**이다. glibc 헤더가 `fclose` 에 **`nonnull` 속성**을 붙여 둔 것을 읽은 것이고,\
  **다른 libc 에서는 안 나올 수 있다.**
- ★★ **이 사실이 라벨 설계를 강제한다** — 「`out:` 하나에 `free`·`fclose` 를 다 모으자」가 **안 된다.**\
  자원마다 라벨을 따로 두어야 **「잡지도 않은 것을 푸는」 경로**가 없어진다.
- **`free(NULL)` 이 무해한 것은 표준의 보장**이다. 그래서 `malloc` 만 쓰는 함수는 라벨 하나로도 된다.

### 4. 라벨 바로 뒤에 선언을 두면 — **C17 위반, C23 합법** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra (경고 0 건, exit=0) =====
(아무것도 나오지 않는다)
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘run’:
ex.c:10:5: warning: a label can only be part of a statement and a declaration is not a statement [-Wpedantic]
   10 |     int n = 1;              /* ★ 라벨 바로 뒤의 선언 */
      |     ^~~
===== gcc -std=c17 -Wall -Wextra -pedantic-errors (exit=1) =====
ex.c: In function ‘run’:
ex.c:10:5: error: a label can only be part of a statement and a declaration is not a statement [-Wpedantic]
   10 |     int n = 1;              /* ★ 라벨 바로 뒤의 선언 */
      |     ^~~
===== clang -std=c17 -Wall -Wextra (exit=0) =====
ex.c:10:5: warning: label followed by a declaration is a C23 extension [-Wc23-extensions]
   10 |     int n = 1;              /* ★ 라벨 바로 뒤의 선언 */
      |     ^
1 warning generated.
===== gcc -std=c2x -Wall -Wextra -pedantic (경고 0 건, exit=0) =====
(아무것도 나오지 않는다)
```

**왜 그런가**

```text
   C17 :  라벨 뒤에는 "문(statement)" 이 와야 한다.
          선언은 문이 아니다  ->  out: int n = 1;  은 위반

   고치는 법 :  out: ;  int n = 1;      <- 세미콜론 하나(빈 문)
   또는      :  -std=c2x                 <- C23 에서 허용됐다
```

- **gcc `-Wall -Wextra` 는 0건**이다. **`-pedantic` 이 있어야 1건**(`-Wpedantic`), `-pedantic-errors` 면 **error `exit=1`**.
- ★ **clang 은 `-pedantic` 없이도 1건**(`-Wc23-extensions`)이다. **같은 사실을 다른 조건에서 본다** —\
  clang 은 이것을 「표준 위반」이 아니라 「**C23 기능을 앞당겨 쓴 것**」으로 분류한다.
- ★★★ **`-std=c17` 은 강제가 아니라 기본값 선택**이다. gcc 에서 **C17 준수를 주장하려면 `-pedantic`** 이 필요하다.
- **`-std=c2x` 로 바꾸면 양쪽 다 0건**이다 — C23 이 이 제약을 없앴다.

### 5. 라벨을 블록의 마지막에 두면 — **같은 규칙의 다른 얼굴**

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘run’:
ex.c:11:1: warning: label at end of compound statement [-Wpedantic]
   11 | cleanup_end:
      | ^~~~~~~~~~~
ex.c:11:1: warning: label ‘cleanup_end’ defined but not used [-Wunused-label]
===== clang -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c:12:1: warning: label at end of compound statement is a C23 extension [-Wc23-extensions]
   12 | }
      | ^
ex.c:11:1: warning: unused label 'cleanup_end' [-Wunused-label]
   11 | cleanup_end:
      | ^~~~~~~~~~~~
2 warnings generated.
===== gcc -std=c2x -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘run’:
ex.c:11:1: warning: label ‘cleanup_end’ defined but not used [-Wunused-label]
   11 | cleanup_end:
      | ^~~~~~~~~~~
```

**왜 그런가**

- **컴파일된다.** gcc `-pedantic` 은 **2건**, clang 은 **2건**, gcc `-Wall -Wextra`(pedantic 없이)는 **1건**이다.
- ★ **두 경고는 서로 다른 이야기다.**\
  `-Wunused-label` 은 「이 라벨로 아무도 안 뛴다」 — **스타일** 문제.\
  `-Wpedantic` / `-Wc23-extensions` 는 「**닫는 중괄호는 문이 아니다**」 — **표준 위반**.\
  `-std=c2x` 로 바꾸면 **뒤엣것만 사라진다.**
- ★ **가리키는 자리가 다르다** — gcc 는 **라벨**(11행), clang 은 **`}`**(12행).
- **고치는 데 필요한 글자는 하나**다 — `cleanup_end: ;`.

### 6. `goto` 가 선언을 건너뛰면 — **합법이다. 값만 불확정이다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic · ./x 를 네 번 돌린 결과 (경고 0 건, run exit=0) =====
v=491432456
(다시 돌리면) v=470477064
(또 돌리면)   v=-1579220376
(또 돌리면)   v=430025784
===== gcc -std=c17 -Wall -Wextra -pedantic -O<수준> =====
-O0 : 0 건
-O1 : 1 건   /usr/include/x86_64-linux-gnu/bits/stdio2.h:86:10: warning: ‘v’ is used uninitialized [-Wuninitialized]
-O2 : 1 건   (같은 줄)
===== clang -std=c17 -Wall -Wextra -pedantic (-O0, exit=0) =====
ex.c:4:9: warning: variable 'v' is used uninitialized whenever 'if' condition is true [-Wsometimes-uninitialized]
    4 |     if (fail) goto skip;
      |         ^~~~
ex.c:8:26: note: uninitialized use occurs here
    8 |         printf("v=%d\n", v);
      |                          ^
```

> **대조할 것은 숫자가 아니라 「실행마다 다르다」는 성질이다.** 네 판의 값이 전부 달랐다.

**왜 그런가**

```text
   VLA 면                              보통 변수면
   goto 가 ★ 크기 잡기를 건너뜀        goto 가 ★ 초기화를 건너뜀
     -> 컴파일 에러                      -> 합법. v 는 "존재하고 값만 불확정"
   (없는 메모리를 쓰게 되므로)           (읽는 것이 UB)
```

- **컴파일된다.** C 는 **선언과 초기화를 가른다** — 블록에 들어가는 순간 `v` 는 **존재**하고, 건너뛴 것은 **초기화뿐**이다.
- **찍히는 값은 실행마다 다르다.** 네 번 돌려 네 값이 달랐다 — **값 자체는 아무것도 증명하지 않는다.**
- ★★ **gcc `-O0` 은 어떤 플래그 조합으로도 0건**이다. `-O1` 부터 말하는데\
  **가리키는 줄이 시스템 헤더**(`bits/stdio2.h:86`)라 원인을 찾기 어렵다 — `printf` 가 매크로로 펼쳐지기 때문이다.
- ★ **clang 은 `-O0` 에서 바로 잡고 원인 줄(`if (fail) goto skip;`)을 가리킨다.**\
  ★ **이 차이가 뜻하는 것** — 「내 컴파일러가 조용하다」는 「코드가 맞다」가 아니다. **둘 다 돌려야 한다.**
- ★ `goto cleanup` 에서 이 사고가 나는 자리는 정해져 있다 — **자원 포인터를 `= NULL` 로 초기화하지 않았을 때**다.

### 7. `goto` 가 못 넘는 선 ★

**답**

```text
   할 수 있는 것 셋                     못 하는 것 둘
   +---------------------------+      +---------------------------+
   | ① 중첩 루프를 한 번에 탈출 |      | ① VLA 스코프 ★ 안으로     |
   | ② 뒤로 뛰기 (루프를 만듦)  |      |    -> 컴파일 에러 exit=1  |
   | ③ 몇 겹 블록이든 밖으로    |      | ② 다른 함수의 라벨로       |
   |   (블록 ★ 안으로도 된다)   |      |    -> "그런 이름이 없다"   |
   +---------------------------+      +---------------------------+
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic — VLA 스코프 (13-e) =====
ex.c: In function ‘run’:
ex.c:3:15: error: jump into scope of identifier with variably modified type
    3 |     if (fail) goto out;
      |               ^~~~
ex.c:7:1: note: label ‘out’ defined here
    7 | out:
      | ^~~
===== clang -std=c17 -Wall -Wextra -pedantic (cc exit=1) =====
ex.c:3:15: error: cannot jump from this goto statement to its label
    3 |     if (fail) goto out;
      |               ^
ex.c:4:9: note: jump bypasses initialization of variable length array
    4 |     int vla[n];
      |         ^
===== gcc -std=c17 -Wall -Wextra -pedantic — 함수 경계 (13-h) (cc exit=1) =====
ex.c: In function ‘main’:
ex.c:4:5: error: label ‘out’ used but not defined
    4 |     goto out;
      |     ^~~~
ex.c: In function ‘late’:
ex.c:8:1: warning: label ‘out’ defined but not used [-Wunused-label]
    8 | out:
      | ^~~
```

- **VLA 스코프 진입은 에러**이고 **`exit=1`** 이다. 경고가 아니다 — [12번 형제](../12-control-flow-and-switch/)가 정본이고 여기서 다시 던져 같은 결론을 받았다.\
  ★ **clang 쪽이 이유를 말해 준다**(「초기화를 건너뛴다」), gcc 는 **타입 이름**으로 말한다(「variably modified type」).
- **함수 경계는 「금지」가 아니라 「없다」로 진단된다** — 라벨의 **스코프가 함수 단위**라 `main` 에서는 그 이름이 아예 안 보인다.
- ★ **보통 변수의 초기화를 건너뛰는 것은 막히지 않는다**(6번 답). **VLA 는 크기를 잡는 일 자체를 건너뛰어**\
  없는 메모리를 쓰게 되지만, 보통 변수는 **자리가 이미 잡혀 있고 값만 안 들어간 것**이다.
- ★ **종료 코드는 파이프 없이 재야 한다.** 이 두 진단을 `| head` 로 받았을 때 **clang 74 · gcc 2** 가 나왔고,\
  직접 재니 **둘 다 1** 이었다.

### 8. 이 패턴이 C 에만 남는 이유 ★★

**답**

```text
   C              획득 -> 실패하면 goto out_xxx -> 라벨에 해제를 층층이     <- 직접 쓴다
   C++            생성자에서 잡고 ★ 소멸자가 자동으로 푼다 (RAII)           <- 스코프가 푼다
   Rust           값이 스코프를 벗어나면 ★ Drop 이 자동으로 호출된다        <- 스코프가 푼다
   Go             defer f.Close()  -> 함수가 끝날 때 역순 실행              <- 런타임이 푼다
   Java/C#        try { } finally { }  /  try-with-resources                <- 예외 기구가 푼다
```

- **C 에 없는 것 둘** — ① **스코프를 벗어날 때 자동으로 불리는 코드**(소멸자·`Drop`·`defer`)\
  ② **예외**. 실패가 **반환값으로만** 오므로 「여기까지 잡은 것」을 **사람이 추적**해야 한다.
- **한 문장으로** — 「**함수 안의 다른 지점으로 무조건 뛰는 유일한 문이 `goto` 라서**,\
  정리 구역을 함수 끝에 만들고 실패 경로가 거기로 뛰는 구조가 유일한 답이 됐다.」
- ★ **이것은 「`goto` 를 쓰자」는 주장이 아니다.** 「`goto` 를 안 쓰면 **정리 코드를 복사해야 한다**」는 것이고,\
  2번 답에서 복사판이 **`call` 을 셋 더** 만든 것을 봤다. **복사가 늘면 빠뜨릴 자리도 는다.**
- ★ **「Linux 커널·OpenSSL 이 이 형태를 쓴다」는 이 문서가 확인하지 않았다.** 코드베이스를 열어 세지 않았다.

### 9. 라벨 이름과 역순 해제 ★

**답**

```text
   out_buf  로 읽으면 : "여기 오면 buf 까지 잡혀 있다"   -> free(buf) 하나만 푼다   (맞다)
   free_buf 로 읽으면 : "여기 오면 buf 를 풀어야 한다"   -> 어느 시점인지 안 보인다 (어긋난다)

   goto out_file;  ->  out_file: fclose(f);     <- file 까지 잡혀 있다
                       out_buf:  free(buf);     <- 흘러내린다
                       out:      return rc;
```

- **라벨 이름은** 「**지금까지 잡은 것**」으로 짓는다. 「다음에 할 일」로 읽으면 **한 칸씩 어긋난다.**
- **라벨은 아래로 갈수록 먼저 풀 것**으로 쌓는다. 그러면 **역순 해제가 저절로** 된다.
- ★ **그것을 가능하게 하는 문법 성질은** 「**라벨을 지나 흘러내린다**」는 것이다 —\
  라벨은 문이 아니라 **이름표**라서 실행을 멈추지 않는다([12번 형제](../12-control-flow-and-switch/)의 `case` 와 같은 성질).
- **`= NULL` 초기화가 막는 사고**는 6번 답의 것이다 — `goto` 가 선언을 건너뛰어 **불확정 값을 `free` 에 넘기는 것.**
- **라벨을 하나로 합쳐도 되는 조건** — 해제 함수가 **전부 널을 견딜 때**뿐이다.\
  `free` 만 쓰면 된다. `fclose`·`pthread_mutex_unlock` 같은 것이 섞이면 **안 된다**(3번 답).

### 10. 다섯 층과 도구 ★★

**답**

| 층 | 이 주제(13번) | [12번](../12-control-flow-and-switch/) | [15번](../15-pointer-arithmetic-and-indexing) | [16번](../16-array-pointer-decay-and-function-parameters) |
|---|---|---|---|---|
| **표준** | ★★ **본체** — 라벨의 함수 스코프 · 흘러내림 · `free(NULL)` · C17 「라벨 뒤에는 문」 · VLA 진입 금지 | ★★ **본체** | 인덱싱 == `*(a+i)` · `ptrdiff_t` | 감쇠 규칙 · 매개변수 재작성 |
| **조건부 표준** | ★ **해당 없음** | ★ **해당 없음** | ★ **해당 없음** | ★ **해당 없음** |
| **구현 정의** | ★ **거의 없다** — `goto` 를 어떻게 컴파일할지(동작은 같다) | plain `char` 의 부호 | 포인터 표현·`uintptr_t` | `sizeof(int *)` 값 |
| **미명시** | ★ **해당 없음** | ★ **해당 없음** | ★ 서로 다른 객체의 **포인터 비교** | ★ **해당 없음** |
| **UB** | ★ **둘뿐** — 초기화 건너뛴 값 읽기 · `fclose(NULL)` | ★ **거의 없다** | ★★ **본체 셋** | ★★ **본체** — `sizeof` 로 길이를 잃은 뒤의 경계 넘기 |

- **비어 있는 칸은** 「**조건부 표준**」과 「**미명시**」다.\
  조건부 보장이 걸릴 매크로가 없고, **`goto` 가 어디로 가는지는 전부 정해져 있어** 「여럿 중 하나」가 없다.
- ★★ **13번과 12번은 층 분포가 같고, 15번·16번과는 정반대다.**\
  여기는 **틀리면 대개 빌드가 안 되거나 조용히 샌다**. 15·16 은 **틀리면 UB 로 아무 일이나 일어난다.**
- ★★★ **어떤 컴파일러도 안 잡는 함정** — **라벨을 잘못 골라 자원이 새는 것.**\
  `goto out_file;` 써야 할 자리에 `goto out_buf;` 를 쓰면 **경고 0건**에 `tbl` 과 `f` 가 샌다.\
  **문법이 맞고 동작도 정의되어 있기 때문**이고, **LeakSanitizer 로 실패 경로를 전부 밟아야** 드러난다.\
  ★ [12번의 「`break` 가 루프를 안 끝내는 것」](../12-control-flow-and-switch/)과 **같은 성격의 사각지대**다 —\
  「틀린 것」이 아니라 「**내 뜻이 아닌 것**」이고, 도구는 뜻을 모른다.

### 11. 플래그별 경고 수와 종료 코드 ★★

**답**

| 프로그램 | gcc 무플래그 | gcc `-Wall` | gcc `+Wextra` | gcc `+pedantic` | gcc `-std=c2x +ped` | clang `-Wall -Wextra` | clang `+pedantic` |
|---|---|---|---|---|---|---|---|
| 13-a 정상 정리 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 13-c 라벨 뒤 선언 | 0 | 0 | 0 | **1** | 0 | **1** | 1 |
| 13-d 블록 끝 라벨 | 0 | 1 | 1 | **2** | 1 | **2** | 2 |
| 13-e VLA 로 점프 | **error** | error | error | error | error | **error** | error |
| 13-f 초기화 건너뜀 | 0 | **0** | 0 | 0 | 0 | **1** | 1 |
| 13-g `goto` 세 용법 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 13-h 함수 넘는 `goto` | **error** | error | error | error | error | **error** | error |
| 13-i `fclose(NULL)` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

- **경고 0건인데 `exit=1` 인 것은 둘**이다 — **13-e**(VLA 스코프)와 **13-h**(함수 경계).\
  ★ **경고만 셌으면 「깨끗함」으로 기록됐다.** 13-h 는 gcc `-Wall` 에서 경고가 **3건** 더 붙지만\
  그 셋은 전부 `-Wunused-label`·`-Wunused-function` 이라 **에러와 무관**하다.
- **`-pedantic` 이 있어야만 보이는 것 둘** — **라벨 뒤 선언**(13-c)과 **블록 끝 라벨**(13-d)의 표준 위반.
- **gcc 와 clang 이 서로 다른 것을 보는 자리 둘** —\
  ① **라벨 규칙**(clang 은 `-pedantic` 없이도 `-Wc23-extensions` 로 말한다)\
  ② **초기화 건너뜀**(gcc `-O0` 은 0건, clang 은 1건).
- ★ **`grep -c warning` 과 `grep -c 'warning:'` 은 다르다.** 앞엣것은 clang 의 요약 줄\
  `2 warnings generated.` 까지 세어 **한 건을 더** 낸다. 이 표는 전부 **`grep -c 'warning:'`** 로 셌다.

### 12. 이 주제의 네 번째 창 ★

**답**

- **세 창으로 안 잡히는 것** —
  - **컴파일 진단**은 문법만 본다. **라벨 이름이 맞는지**는 모른다.
  - **실행 출력**은 밟은 경로만 본다. **실패 경로를 안 던지면 아무 일도 안 난다.**
  - **UBSan** 은 이 주제에서 거의 할 일이 없다 — UB 가 **둘뿐**이다.
- ★★ **그래서 창을 둘 더 썼다.**
  - **어셈블리**(`-O0`\~`-Os` 다섯 벌 + `-O2 -S -masm=intel`)\
    → ★ **반증**했다. 「`goto` 가 분기를 줄인다」는 통념이 **틀렸다** — `goto` 와 중첩 `if` 가 같고,\
    `-O0` 에서는 중첩 `if` 쪽이 **더 적었다.**
  - **LeakSanitizer(ASan)** + **실패 경로 전수 실행**\
    → ★ **검산**했다. 다섯 경로를 단계마다 실패시켜 돌리고 **진단 0줄**을 받았다.\
    「푼 개수 == 잡은 개수」를 사람이 아니라 **기계가 확인**한 것이다.
- ★ **두 창의 성격이 다르다** — 어셈블리는 **주장을 깨는** 데 썼고, LeakSanitizer 는 **주장을 세우는** 데 썼다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 컴파일러·플래그로 돌렸나 |
|---|---|---|
| 다중 자원 정리 (13-a) | 다섯 실패 경로 전수 실행 · 해제 줄 수 **0/1/2/3/3** · **경고 0건** · ASan+UBSan **진단 0줄** | gcc 7벌 · gcc `-fsanitize=address,undefined` |
| 세 판 비교 (13-b) | `-O2` 명령 **39/39/45** · 분기 **4/4/5** · `call` **7/7/10** · `-O0`\~`-Os` 다섯 벌 · 소스 해제 호출 **3/3/6** | gcc `-O0 -O1 -O2 -O3 -Os -S -masm=intel` |
| 라벨 뒤 선언 (13-c) | gcc `-Wall -Wextra` **0건** · `+pedantic` **1건** · `-pedantic-errors` **error exit=1** · `-std=c2x` **0건** · clang **1건**(`-Wc23-extensions`) | gcc 6벌 · clang 4벌 |
| 블록 끝 라벨 (13-d) | gcc `+pedantic` **2건** · clang **2건** · `-std=c2x` 에서 `-Wpedantic` 쪽만 사라짐 · `-pedantic-errors` **exit=1** | gcc 6벌 · clang 2벌 |
| VLA 점프 (13-e) | **error `exit=1`** · gcc 는 타입 이름으로 · clang 은 **이유**로 말함 | gcc·clang 7벌 |
| 초기화 건너뜀 (13-f) | 값이 **네 판 전부 다름** · gcc `-O0` **0건** / `-O1`·`-O2` **1건**(시스템 헤더 줄) · clang `-O0` **1건** | gcc 9벌 · clang 2벌 |
| `goto` 세 용법 (13-g) | 중첩 루프 탈출 · 뒤로 뛰기 · 두 겹 블록 탈출 — **경고 0건** | gcc·clang 7벌 |
| 함수 경계 (13-h) | **error `exit=1`** — 「label ‘out’ **used but not defined**」 | gcc·clang 7벌 |
| `free`/`fclose` 널 (13-i) | `free(NULL)` 통과 · `fclose(NULL)` **SIGSEGV run exit=139** · UBSan `nonnull` · **컴파일 경고 0건** | gcc 7벌 · gcc `-fsanitize=address,undefined` |
| ★ 종료 코드 재측정 | `\| head` 를 끼우면 clang **74** · gcc **2** — 파이프를 빼면 **둘 다 1** | 직접 측정 + `PIPESTATUS` 대조 |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3 · glibc)에서만** 그렇다.

- **`fclose(NULL)` 이 SIGSEGV 로 죽는 것** — 표준은 「UB」라고만 한다. **어떤 libc 는 조용히 돌아올 수도** 있다.
- **UBSan 이 `nonnull` 을 말해 주는 것** — ★ **glibc 헤더의 속성**이 근거다. 표준이 아니다.
- **초기화 안 된 `v` 의 값** — ★ **쓰레기값이라 아무 근거도 못 된다.** 네 판이 다 달랐다.
- **명령 수(39/39/45)** — x86-64 · gcc 13.3.0 의 것이다. **다른 ISA·버전에서 달라진다.**
- gcc 13.3.0 에 **`-std=c23` 이 없는 것**(`-std=c2x`).
- gcc `-Wuninitialized` 가 **시스템 헤더 줄을 가리키는 것** — `printf` 가 `bits/stdio2.h` 의 매크로로 펼쳐지기 때문이다.

**`goto` 와 라벨의 규칙 자체는 구현 의존이 아니다.** 라벨의 함수 스코프 · 흘러내림 · VLA 스코프 진입 금지 ·\
C17 의 「라벨 뒤에는 문」 · `free(NULL)` 의 무해함은 **어느 C 구현에서도 같다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `__attribute__((cleanup))`(GNU 확장) · `setjmp`/`longjmp` ·\
  정리 코드가 `errno` 를 덮어쓰는 문제(목록의 **46번 주제**) · 자원이 **다섯·여섯**으로 늘었을 때의 세 판 비교 ·\
  Linux 커널·OpenSSL 실제 코드에서 이 형태의 빈도.
- **못 잰 것** — ★ **「`goto` 판이 중첩 `if` 판보다 빠른가」.** 명령 수가 같아 **잴 것이 없었다** —\
  「못 잰 것」이 아니라 「**잴 필요가 없는 것**」이다. 수치를 내려면 측정 조건 선언이 필요한데 이 문서는 하지 않았다.
- ★ **`with_dup` 이 실제로 느린지도 재지 않았다.** `call` 이 셋 더 있다는 것은 **명령 수**이지 시간이 아니다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- gcc 가 **`-std=c23` 을 받기 시작했는지**(13.3.0 은 `-std=c2x` 뿐).
- clang 이 라벨 규칙을 **여전히 `-Wc23-extensions` 로** 분류하는지.
- gcc `-Wuninitialized` 가 **`-O0` 에서도 말하게 됐는지**.
- 세 판의 **명령 수** — 컴파일러 버전이 오르면 달라진다. **결론(「셋 중 복사판만 비싸다」)이 유지되는지**를 본다.
- **규칙 자체는 다시 돌릴 필요가 없다** — C89 이후 바뀐 적이 없고, C23 이 바꾼 둘은 이 문서가 실측했다.
