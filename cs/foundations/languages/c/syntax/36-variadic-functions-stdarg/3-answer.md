# c/syntax/36 — 가변 인자 함수 `<stdarg.h>`: 「**`...` 뒤에서는 타입이 사라지고, 승격된 것만 남는다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **gcc-12 12.4.0** ·
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s36a.c`\~`s36h2.c` · `s36go.go` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
> ★★★ **본체 창은 승격 격자** — 넘긴 타입 5 × 꺼낸 타입 2 × 컴파일러 2 × `-O0`/`-O2`.
> ★★ **흔들리는 칸** — `printf("%d\n", 3.0)` 이 찍는 수. **싣지 않고 「3 이 찍힌 판 N / 10」으로** 찍었다. 정규화 규칙은 기본 넷뿐이다.

## 이 파일이 다시 싣는 소스

★ 1·5번의 격자는 **소스 줄을 끼워 보여 주지 않는다** — 그 소스를 여기 한 번 더 싣는다(질문 파일의 것과 같다).

```c
/* s36a.c */
#include <stdarg.h>
#include <stdio.h>

static double get_double(int n, ...) {
    va_list ap;
    va_start(ap, n);
    double v = va_arg(ap, double);
    va_end(ap);
    return v;
}

static double get_float(int n, ...) {
    va_list ap;
    va_start(ap, n);
    float v = va_arg(ap, float);
    va_end(ap);
    return v;
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    float f = 1.5f;
    printf("[1] va_arg(ap, double) -> %g\n", get_double(1, f));
    printf("[2] va_arg(ap, float)  -> %g\n", get_float(1, f));
    return 0;
}
```

```c
/* s36e.c */
#include <stdarg.h>
#include <stdio.h>

static int sum_n(int n, ...) {
    va_list ap;
    unsigned total = 0;                  /* 쓰레기 값을 더해도 넘침(UB)이 안 나게 unsigned 로 */
    va_start(ap, n);
    for (int i = 0; i < n; i++) total += (unsigned)va_arg(ap, int);
    va_end(ap);
    return (int)total;
}

int main(void) {
    fprintf(stderr, "[1] sum_n(3, ...) == 60 ? %d\n", sum_n(3, 10, 20, 30) == 60);
    volatile int got = sum_n(8, 10, 20, 30);  /* 셋을 넘기고 여덟을 읽는다 */
    (void)got;
    fprintf(stderr, "[2] after sum_n(8, ...)\n");
    return 0;
}
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `va_arg(ap, float)` — **두 컴파일러 경고 · `cc exit=0` · gcc 는 `ud2` 로 `run exit=132` · clang 은 `0`** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s36a.c -o /dev/null (cc exit=0) =====
In file included from s36a.c:1:
s36a.c: In function ‘get_float’:
s36a.c:15:26: warning: ‘float’ is promoted to ‘double’ when passed through ‘...’
   15 |     float v = va_arg(ap, float);
      |                          ^
s36a.c:15:26: note: (so you should pass ‘double’ not ‘float’ to ‘va_arg’)
s36a.c:15:26: note: if this code is reached, the program will abort
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s36a.c -o /dev/null (cc exit=0) =====
s36a.c:15:26: warning: second argument to 'va_arg' is of promotable type 'float'; this va_arg has undefined behavior because arguments will be promoted to 'double' [-Wvarargs]
   15 |     float v = va_arg(ap, float);
      |                          ^~~~~
/usr/lib/llvm-18/lib/clang/18/include/__stdarg_va_arg.h:20:47: note: expanded from macro 'va_arg'
   20 | #define va_arg(ap, type) __builtin_va_arg(ap, type)
      |                                               ^~~~
1 warning generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s36a.c -o x ; ./x (cc exit=0 · run exit=132) =====
[1] va_arg(ap, double) -> 1.5
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s36a.c -o x ; ./x (cc exit=0 · run exit=0) =====
[1] va_arg(ap, double) -> 1.5
[2] va_arg(ap, float)  -> 0
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s36a.c -o - 2>/dev/null | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand | sed -n '/^get_float/,/ud2/p' (cc exit=0) =====
get_float.constprop.0:
        mov     rax, QWORD PTR fs:40
        mov     QWORD PTR -16[rsp], rax
        xor     eax, eax
        lea     rax, 8[rsp]
        mov     QWORD PTR -32[rsp], rax
        ud2
```

```text
===== va_arg(ap, float) 를 실행하면 — 컴파일러 2 × sanitizer 3 × 최적화 2 (stdout 무버퍼) (exit=0) =====
gcc    (없음)     -O0  run exit=132 리포트 0줄 | [1] va_arg(ap, double) -> 1.5|
gcc    (없음)     -O2  run exit=132 리포트 0줄 | [1] va_arg(ap, double) -> 1.5|
gcc    address    -O0  run exit=132 리포트 0줄 | [1] va_arg(ap, double) -> 1.5|
gcc    address    -O2  run exit=132 리포트 0줄 | [1] va_arg(ap, double) -> 1.5|
gcc    undefined  -O0  run exit=132 리포트 0줄 | [1] va_arg(ap, double) -> 1.5|
gcc    undefined  -O2  run exit=132 리포트 0줄 | [1] va_arg(ap, double) -> 1.5|
clang  (없음)     -O0  run exit=0   리포트 0줄 | [1] va_arg(ap, double) -> 1.5|[2] va_arg(ap, float)  -> 0|
clang  (없음)     -O2  run exit=0   리포트 0줄 | [1] va_arg(ap, double) -> 1.5|[2] va_arg(ap, float)  -> 0|
clang  address    -O0  run exit=0   리포트 0줄 | [1] va_arg(ap, double) -> 1.5|[2] va_arg(ap, float)  -> 0|
clang  address    -O2  run exit=0   리포트 0줄 | [1] va_arg(ap, double) -> 1.5|[2] va_arg(ap, float)  -> 0|
clang  undefined  -O0  run exit=0   리포트 0줄 | [1] va_arg(ap, double) -> 1.5|[2] va_arg(ap, float)  -> 0|
clang  undefined  -O2  run exit=0   리포트 0줄 | [1] va_arg(ap, double) -> 1.5|[2] va_arg(ap, float)  -> 0|
```

**왜 그런가**

- ★★★ **`float` 은 `...` 를 지나며 `double` 이 된다** — `va_arg(ap, float)` 는 **승격된 실제 인자(`double`)와 호환되지 않는 타입**이라 UB 다. `va_arg(ap, double)` 은 `1.5`.
- ★★★ **gcc 는 「도달하면 중단된다」고 말하고 `ud2` 를 심는다** — SIGILL, `run exit=132`. 표준 출력을 버퍼 없이 둬서 `[1]` 은 남았다.
- ★★★ **clang 은 「UB 다」라고 말하고 번역은 한다** — `double` 의 비트를 `float` 으로 읽어 **`0`**.
- ★★ **sanitizer 는 바꾸지 못한다** — gcc 는 sanitizer 판에서도 `132`(죽인 것은 컴파일러의 `ud2`), clang 은 **리포트 0줄**. sanitizer 를 켠 8칸 중 리포트를 낸 칸 0.

### 2. 승격 격자 — **승격된 타입 다섯 줄은 전부 맞다 · 같은 타입 다섯 줄은 두 컴파일러가 전부 갈린다(5 / 10) · clang 정수 넷은 맞아 보인다** ★★★

**출력**

```text
===== 기본 인자 승격 격자 — 넘긴 타입 5 × 꺼낸 타입 2 × 컴파일러 2 × 최적화 2 (-std=c17 -Wall -Wextra -pedantic) (exit=0) =====
넘긴 타입 → 꺼낸 타입          | gcc -O0             | gcc -O2             | clang -O0           | clang -O2
char → char                    | W1 exit=132 같나=-  | W1 exit=132 같나=-  | W1 exit=0 같나=1    | W1 exit=0 같나=1
char → int                     | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1
unsigned char → unsigned char  | W1 exit=132 같나=-  | W1 exit=132 같나=-  | W1 exit=0 같나=1    | W1 exit=0 같나=1
unsigned char → int            | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1
short → short                  | W1 exit=132 같나=-  | W1 exit=132 같나=-  | W1 exit=0 같나=1    | W1 exit=0 같나=1
short → int                    | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1
_Bool → _Bool                  | W1 exit=132 같나=-  | W1 exit=132 같나=-  | W1 exit=0 같나=1    | W1 exit=0 같나=1
_Bool → int                    | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1
float → float                  | W1 exit=132 같나=-  | W1 exit=132 같나=-  | W1 exit=0 같나=0    | W1 exit=0 같나=0
float → double                 | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1
(W = 경고 수 · exit = 실행 종료 코드 · 같나 = 꺼낸 값이 넘긴 값과 같으면 1, 실행이 죽으면 -)
두 컴파일러가 갈린 줄 5 / 10
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s36b.c -o /dev/null (cc exit=0) =====
s36b.c: In function ‘same’:
s36b.c:13:16: warning: ‘char’ is promoted to ‘int’ when passed through ‘...’
   13 |     PASS got = (PASS)va_arg(ap, PULL);
      |                ^
s36b.c:13:16: note: (so you should pass ‘int’ not ‘char’ to ‘va_arg’)
s36b.c:13:16: note: if this code is reached, the program will abort
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s36b.c -o /dev/null (cc exit=0) =====
s36b.c:13:33: warning: second argument to 'va_arg' is of promotable type 'char'; this va_arg has undefined behavior because arguments will be promoted to 'int' [-Wvarargs]
   13 |     PASS got = (PASS)va_arg(ap, PULL);
      |                                 ^~~~
s36b.c:6:14: note: expanded from macro 'PULL'
    6 | #define PULL char
      |              ^~~~
/usr/lib/llvm-18/lib/clang/18/include/__stdarg_va_arg.h:20:47: note: expanded from macro 'va_arg'
   20 | #define va_arg(ap, type) __builtin_va_arg(ap, type)
      |                                               ^~~~
1 warning generated.
```

**왜 그런가**

- ★★★ **승격된 타입(`int`·`double`)으로 꺼내면** 모든 칸이 `W0 exit=0 같나=1` — 표준이 정한 길이다.
- ★★★ **같은 타입으로 꺼내면 UB** — gcc 는 다섯 다 **`exit=132`**, clang 은 다섯 다 **`exit=0`** 에 값을 낸다. **갈린 줄 5 / 10** 이 스크립트의 마지막 줄이다.
- ★★★ **clang 의 `char`·`unsigned char`·`short`·`_Bool` 은 「같나 = 1」** — `int` 로 넘어온 자리의 **아래 바이트를 읽으면** 우연히 같은 값이 나온다. **경고를 무시하고 clang 에서 시험하면 통과**한다 — 가장 위험한 칸이다. `float` 은 비트 배치가 달라 `0`.
- ★ **`-O0`/`-O2` 사이에 움직인 칸은 없다** — 갈린 것은 **컴파일러**다.

### 3. `printf` 대 내 함수 — **`printf` 와 속성 붙인 쪽만 경고 · 내 함수는 0 · `3` 은 0 / 10** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s36c.c -o /dev/null (cc exit=0) =====
s36c.c: In function ‘main’:
s36c.c:20:31: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘double’ [-Wformat=]
   20 |     printf("printf         : %d\n", 3.0);
      |                              ~^     ~~~
      |                               |     |
      |                               int   double
      |                              %f
s36c.c:22:39: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘double’ [-Wformat=]
   22 |     my_log_checked("my_log_checked : %d\n", 3.0);
      |                                      ~^     ~~~
      |                                       |     |
      |                                       int   double
      |                                      %f
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s36c.c -o /dev/null (cc exit=0) =====
s36c.c:20:37: warning: format specifies type 'int' but the argument has type 'double' [-Wformat]
   20 |     printf("printf         : %d\n", 3.0);
      |                              ~~     ^~~
      |                              %f
s36c.c:22:45: warning: format specifies type 'int' but the argument has type 'double' [-Wformat]
   22 |     my_log_checked("my_log_checked : %d\n", 3.0);
      |                                      ~~     ^~~
      |                                      %f
2 warnings generated.
```

```text
===== printf("%d\n", 3.0) 을 10 번 — 컴파일러 2 (-std=c17, 경고 무시) (exit=0) =====
gcc    10 번 돌려 3 이 찍힌 판 0 / 10
clang  10 번 돌려 3 이 찍힌 판 0 / 10
```

**왜 그런가**

- ★★★ **컴파일러는 `printf` 의 형식 규칙을 안다** — 그래서 `%d` 와 `double` 의 불일치를 `-Wformat` 으로 잡는다.
- ★★★ **`my_log` 는 `...` 뒤의 타입을 아무도 모른다** — 경고 0. **`format(printf, 1, 2)`** 속성이 「1번이 형식, 2번부터 대상」을 알려 **검사를 되살렸다**(두 컴파일러).
- ★ **`3` 은 한 판도 안 찍혔다** — `double` 은 `xmm0` 로 넘어가고 `%d` 는 **정수 레지스터**를 읽는다. 찍힌 수 자체는 흔들리므로 「**3 이 찍힌 판 0 / 10**」을 적었다.

### 4. 센티널 대 개수 — **`sentinel` 속성은 빠진 `NULL` 을 잡고 · 개수 초과는 아무도 못 잡는다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s36d.c -o /dev/null (cc exit=0) =====
s36d.c: In function ‘main’:
s36d.c:26:5: warning: missing sentinel in function call [-Wformat=]
   26 |     printf("%d\n", count_until_null("a", "b", "c"));
      |     ^~~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s36d.c -o /dev/null (cc exit=0) =====
s36d.c:26:50: warning: missing sentinel in function call [-Wsentinel]
   26 |     printf("%d\n", count_until_null("a", "b", "c"));
      |                                                  ^
      |                                                  , NULL
s36d.c:6:12: note: function has been explicitly marked sentinel here
    5 | __attribute__((sentinel))
      |                ~~~~~~~~
    6 | static int count_until_null(const char *first, ...) {
      |            ^
1 warning generated.
```

**왜 그런가**

- ★★ **`sentinel` 속성** — gcc 는 `-Wformat` 묶음으로, clang 은 `-Wsentinel` 로 `missing sentinel in function call`. clang 은 `, NULL` 을 넣을 자리까지 보여 준다.
- ★★ **`sum_n(8, …)` 은 0건** — 개수와 실제 인자 수를 견줄 정보가 **선언에 없다.**
- ★ **실행하지 않은 이유** — 뒤의 두 호출은 **다음 인자가 없는 `va_arg`** 라 UB 다. 그 값은 결론이 될 수 없다.

### 5. 과잉 읽기 — **답한 칸 0 / 5** ★★

**출력**

```text
===== 셋을 넘기고 여덟을 va_arg 로 — sanitizer 탐침 (-std=c17 -O0 -g) (exit=0) =====
gcc    address    run exit=0 · 리포트 0줄 | [1] sum_n(3, ...) == 60 ? 1|[2] after sum_n(8, ...)|
gcc    undefined  run exit=0 · 리포트 0줄 | [1] sum_n(3, ...) == 60 ? 1|[2] after sum_n(8, ...)|
clang  address    run exit=0 · 리포트 0줄 | [1] sum_n(3, ...) == 60 ? 1|[2] after sum_n(8, ...)|
clang  undefined  run exit=0 · 리포트 0줄 | [1] sum_n(3, ...) == 60 ? 1|[2] after sum_n(8, ...)|
clang  memory     run exit=0 · 리포트 0줄 | [1] sum_n(3, ...) == 60 ? 1|[2] after sum_n(8, ...)|
답한 칸 0 / 5
```

**왜 그런가**

- ★★ **다섯 도구 전부 리포트 0줄 · `exit=0`** — 이 판의 x86-64 에서 `va_arg` 가 읽는 곳은 **함수가 만든 레지스터 저장 영역과 스택**이라 도구의 경계 검사에 안 걸린 것으로 보인다(★ 도구 소스로 확인하지 않았다).
- ★★ **안전하다는 뜻이 아니다** — 표준은 「**다음 인자가 없으면 UB**」라고 적는다. 도구의 침묵은 **이 판에서 못 봤다**는 관찰이다.

### 6. `va_list` 두 번 — **24바이트 · 넘긴 `ap` 는 소비돼 두 번째가 틀린다 · `va_copy` 는 맞다** ★★

**출력**

```text
===== va_list 를 두 번 쓰기 — 컴파일러 2 × 최적화 2 (exit=0) =====
--- gcc -O0
sizeof(va_list) = 24
twice_plain : first == 60 ? 1   second == 60 ? 0
twice_copy  : first == 60 ? 1   second == 60 ? 1
--- gcc -O2
sizeof(va_list) = 24
twice_plain : first == 60 ? 1   second == 60 ? 0
twice_copy  : first == 60 ? 1   second == 60 ? 1
--- clang -O0
sizeof(va_list) = 24
twice_plain : first == 60 ? 1   second == 60 ? 0
twice_copy  : first == 60 ? 1   second == 60 ? 1
--- clang -O2
sizeof(va_list) = 24
twice_plain : first == 60 ? 1   second == 60 ? 0
twice_copy  : first == 60 ? 1   second == 60 ? 1
```

**왜 그런가**

- ★★★ **표준 — 넘긴 함수가 `va_arg` 를 불렀다면 부른 쪽의 `ap` 는 불확정**이고 `va_end` 말고는 다시 쓰면 안 된다. `twice_plain` 의 두 번째는 **UB** 다.
- ★★ **이 판에서는 「소비된」 상태였다** — `va_list` 가 **24바이트 배열 타입**처럼 동작해 함수에 넘기면 **포인터로 감쇠**하고, 받은 쪽이 **원본을 앞으로 민다.** 그래서 두 번째 합이 `60` 이 아니다.
- ★★ **`va_copy` 로 사본을 만들면** 네 벌 다 맞다.

### 7. `va_end` — **네 벌 다 어셈블리 차이 0 · 그래도 UB** ★★

**출력**

```text
===== va_end 가 있는 함수와 없는 함수 — 어셈블리 몸통 비교 (exit=0) =====
gcc    -O0  with_end 56 줄 · without_end 56 줄 · 다른 줄 0
gcc    -O2  with_end 19 줄 · without_end 19 줄 · 다른 줄 0
clang  -O0  with_end 56 줄 · without_end 56 줄 · 다른 줄 0
clang  -O2  with_end 39 줄 · without_end 39 줄 · 다른 줄 0
(지역 레이블 번호 .L숫자 는 지우고 견줬다)
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s36g.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand | sed -n '/^with_end:/,/^without_end:/p' | grep -v '^without_end:' (cc exit=0) =====
with_end:
        endbr64
        sub     rsp, 88
        mov     QWORD PTR 40[rsp], rsi
        mov     rax, QWORD PTR fs:40
        mov     QWORD PTR 24[rsp], rax
        xor     eax, eax
        lea     rax, 96[rsp]
        mov     DWORD PTR [rsp], 8
        mov     QWORD PTR 8[rsp], rax
        lea     rax, 32[rsp]
        mov     QWORD PTR 16[rsp], rax
        mov     eax, DWORD PTR 40[rsp]
        mov     rdx, QWORD PTR 24[rsp]
        sub     rdx, QWORD PTR fs:40
        jne     .L7
        add     rsp, 88
        ret
.L7:
        call    __stack_chk_fail@PLT
```

**왜 그런가**

- ★★ **이 판의 `va_end` 는 명령을 하나도 만들지 않는다** — 있는 함수와 없는 함수가 **한 글자도 같다.**
- ★★★ **「빼도 된다」로 적지 않는다** — 표준은 **`va_end` 없이 돌아가면 UB** 라고 적는다. 명령 0개는 **이 ABI 의 관찰**이다.
- ★ **실행으로는 「아무 일도 없다」까지만** 보인다 — 그것이 무해해서인지 못 봐서인지 **실행은 가르지 못한다.** 어셈블리로 창을 바꿔 **명령 0개**를 봤다(제5의 상태).

### 8. C23 — **gcc 13·clang 은 C23 에서 받고 C17 에서 에러 · gcc-12 는 C23 에서도 에러 · clang 의 `-pedantic` 경고는 판을 틀리게 읽었다** ★★

**출력**

```text
===== C23 의 두 변경 — 파일 3 × 컴파일러 3 × 판 2 (exit=0) =====
파일      컴파일러 -std=c17 -pedantic     | -std=c2x -pedantic
s36h0.c   gcc-12   exit=0 경고 0 에러 0   | exit=0 경고 0 에러 0
s36h0.c   gcc      exit=0 경고 0 에러 0   | exit=0 경고 0 에러 0
s36h0.c   clang    exit=0 경고 0 에러 0   | exit=0 경고 0 에러 0
s36h1.c   gcc-12   exit=1 경고 0 에러 2   | exit=1 경고 0 에러 2
s36h1.c   gcc      exit=1 경고 0 에러 2   | exit=0 경고 0 에러 0
s36h1.c   clang    exit=1 경고 1 에러 2   | exit=0 경고 1 에러 0
s36h2.c   gcc-12   exit=1 경고 0 에러 3   | exit=1 경고 0 에러 3
s36h2.c   gcc      exit=1 경고 1 에러 2   | exit=0 경고 0 에러 0
s36h2.c   clang    exit=1 경고 1 에러 3   | exit=0 경고 1 에러 0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s36h1.c -o /dev/null (cc exit=1) =====
s36h1.c: In function ‘first’:
s36h1.c:5:16: error: macro "va_start" requires 2 arguments, but only 1 given
    5 |     va_start(ap);                 /* 두 번째 인자를 안 적었다 */
      |                ^
In file included from s36h1.c:1:
/usr/lib/gcc/x86_64-linux-gnu/13/include/stdarg.h:50: note: macro "va_start" defined here
   50 | #define va_start(v,l)   __builtin_va_start(v,l)
      | 
s36h1.c:5:5: error: ‘va_start’ undeclared (first use in this function)
    5 |     va_start(ap);                 /* 두 번째 인자를 안 적었다 */
      |     ^~~~~~~~
s36h1.c:5:5: note: each undeclared identifier is reported only once for each function it appears in
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic -c s36h1.c -o /dev/null (cc exit=0) =====
```

```text
===== clang -std=c2x -Wall -Wextra -pedantic -c s36h1.c -o /dev/null (cc exit=0) =====
s36h1.c:5:16: warning: must specify at least one argument for '...' parameter of variadic macro [-Wgnu-zero-variadic-macro-arguments]
    5 |     va_start(ap);                 /* 두 번째 인자를 안 적었다 */
      |                ^
/usr/lib/llvm-18/lib/clang/18/include/__stdarg_va_arg.h:14:9: note: macro 'va_start' defined here
   14 | #define va_start(ap, ...) __builtin_va_start(ap, 0)
      |         ^
1 warning generated.
```

```text
===== grep -n 'va_start' /usr/lib/llvm-18/lib/clang/18/include/__stdarg_va_arg.h (exit=0) =====
1:/*===---- __stdarg_va_arg.h - Definitions of va_start, va_arg, va_end-------===
13:/* C23 does not require the second parameter for va_start. */
14:#define va_start(ap, ...) __builtin_va_start(ap, 0)
17:#define va_start(ap, param) __builtin_va_start(ap, param)
```

```text
===== gcc-12 -std=c2x -Wall -Wextra -pedantic -c s36h2.c -o /dev/null (cc exit=1) =====
s36h2.c:3:15: error: ISO C requires a named argument before ‘...’
    3 | int only_dots(...) {              /* 이름 있는 매개변수가 없다 */
      |               ^~~
s36h2.c: In function ‘only_dots’:
s36h2.c:5:16: error: macro "va_start" requires 2 arguments, but only 1 given
    5 |     va_start(ap);
      |                ^
In file included from s36h2.c:1:
/usr/lib/gcc/x86_64-linux-gnu/12/include/stdarg.h:47: note: macro "va_start" defined here
   47 | #define va_start(v,l)   __builtin_va_start(v,l)
      | 
s36h2.c:5:5: error: ‘va_start’ undeclared (first use in this function)
    5 |     va_start(ap);
      |     ^~~~~~~~
s36h2.c:5:5: note: each undeclared identifier is reported only once for each function it appears in
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s36h2.c -o /dev/null (cc exit=1) =====
s36h2.c:3:15: warning: ISO C requires a named argument before ‘...’ before C2X [-Wpedantic]
    3 | int only_dots(...) {              /* 이름 있는 매개변수가 없다 */
      |               ^~~
s36h2.c: In function ‘only_dots’:
s36h2.c:5:16: error: macro "va_start" requires 2 arguments, but only 1 given
    5 |     va_start(ap);
      |                ^
In file included from s36h2.c:1:
/usr/lib/gcc/x86_64-linux-gnu/13/include/stdarg.h:50: note: macro "va_start" defined here
   50 | #define va_start(v,l)   __builtin_va_start(v,l)
      | 
s36h2.c:5:5: error: ‘va_start’ undeclared (first use in this function)
    5 |     va_start(ap);
      |     ^~~~~~~~
s36h2.c:5:5: note: each undeclared identifier is reported only once for each function it appears in
```

**왜 그런가**

- ★★★ **C23 은 `va_start(va_list ap, ...)`** 로 서명을 바꿨고 **`f(...)`** 를 허락했다 — gcc 13 · clang 18 은 `-std=c2x` 에서 `exit=0`.
- ★★ **gcc-12 의 `stdarg.h` 는 두 인자 매크로뿐** — `macro "va_start" requires 2 arguments`. 34편처럼 **컴파일러 판이 한 축**이다.
- ★★ **clang 의 `-Wgnu-zero-variadic-macro-arguments` 는 옳지 않다** — C23 의 전처리기는 **`...` 자리에 인자 0개를 허락**한다(`...` 를 뺀 매개변수 수만큼이면 된다). clang 18 의 헤더가 C23 판을 `va_start(ap, ...)` 로 정의했는데, `-pedantic` 이 **옛 판의 기준**으로 그 호출을 짚었다. **판정의 근거는 문구가 아니라 종료 코드 `0` 과 표준 문장**이다.
- ★ **gcc 13 은 같은 소스에 0건** — 두 컴파일러가 갈린 자리다.

### 9. 34 → 36 — **같은 기본 인자 승격 · C17 은 두 자리, C23 은 한 자리** ★★★

**왜 그런가**

- ★★★ **공통 규칙은 기본 인자 승격** — 매개변수 타입을 모르는 인자에 **정수 승격 + `float` → `double`**. 34편의 빈 괄호 호출이 `cvtss2sd` 로 `float` 을 올리고 **`al` 에 벡터 레지스터 수를 넣은 것**은, 컴파일러가 그 호출을 **가변 인자 호출과 같은 번역**으로 다뤘다는 뜻이다.
- ★★ **C23 에서는 `...` 뒤 한 자리**만 남았다 — 빈 괄호가 `void` 가 되어 「매개변수를 모르는 호출」이 사라졌다.

### 10. 다른 언어 — **Go 는 `[]float32`, 승격 없음 · C++ 은 가변 인자 템플릿** ★

**출력**

```text
===== go version (exit=0) =====
go version go1.27.1 linux/amd64
```

```text
===== go run s36go.go (exit=0) =====
[]float32 4
func(...float32) float32
```

**왜 그런가**

- ★ **Go 의 가변 인자는 슬라이스**다 — 타입이 선언에 남고 `float32` 그대로(`1.5 + 2.5 = 4`). 함수 타입도 `func(...float32) float32`([Go 12번 형제](../../../go/syntax/12-functions-multiple-returns-named-results-and-variadics/)).
- ★ **C++ 은 가변 인자 템플릿** — 타입을 컴파일 때 전부 안다. C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **34번**(아직 폴더가 없다).

### 11. 다섯 층 — **UB 가 본체 · 표준이 그 경계를 긋는다 · 구현 정의에 `va_list` 와 UB 를 만난 컴파일러의 선택** ★★★

**왜 그런가**

- **표준** — 기본 인자 승격 · 승격된 타입과 호환되는 `va_arg`(예외 넷) · 넘긴 `ap` 불확정 · `va_end` 의무 · `va_copy` · C23 두 변경.
- **조건부 표준** — 해당 없음.
- **구현 정의** — `va_list` 의 정체(이 판 24바이트) · 호출 규약 · **gcc `ud2` / clang 값** · `format`·`sentinel` 속성.
- **미명시** — 이 편이 던진 것 중에는 없음.
- **UB** — 승격 전 타입 `va_arg` · 형식 불일치 · 없는 인자 읽기 · `ap` 재사용 · `va_end` 누락.
- ★★★ **잡은 도구** — **컴파일러 경고뿐**(승격되는 타입의 `va_arg` · `printf` 형식 · 속성을 붙인 형식과 센티널). **못 잡은 것** — 내 함수의 형식(속성 없이) · 개수 초과 · `ap` 재사용 · `va_end` 누락 · **sanitizer 13칸 리포트 0줄**.
- ★★ **gcc 의 `ud2` 는 선택**이다 — UB 를 만난 구현이 무엇을 하든 표준은 상관하지 않는다. clang 은 **다른 선택**을 했다.
- ★★ **「종료 코드 0인데 ill-formed」 새 항목은 없다** — 대신 **「종료 코드 0인데 UB」가 일곱**(금지 사례 표).

### 12. 경계 ★

**왜 그런가**

- **정수 승격** — [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/) · **`float` 변환** — [04번 형제](../04-floating-point-types-and-conversions/).
- **`printf` 형식 문자열** — 목록의 **47번 주제**.
- ★ 이 주제가 책임지는 것 — ① **승격된 인자를 어떻게 꺼내나**(격자) ② **누가 검사하나**(`printf` · 속성 · 침묵하는 도구) ③ **`va_list` 의 규칙**(`va_copy` · `va_end` · C23).

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s36a.c` | ★★★ 경고 둘 · gcc `132`(`ud2`) · clang `0` · sanitizer 8칸 0줄 | 진단 2 · 실행 2 · 어셈블리 1 · 격자 12 |
| `s36b.c` | ★★★ **승격 격자 40칸 · 갈린 줄 5 / 10** | 격자 40 · 진단 2 |
| `s36c.c`·`s36c2.c` | ★★ `-Wformat` · 속성 · `0 / 10` | 진단 2 · 실행 20 |
| `s36d.c` | ★★ `sentinel` 경고 · 개수 초과 0 | 진단 2 |
| `s36e.c` | ★★ sanitizer 0 / 5 | 5 |
| `s36f.c` | ★★ 24바이트 · 두 번째 틀림 · `va_copy` 맞음 | 격자 4 |
| `s36g.c` | ★ 어셈블리 차이 0 | 격자 4 · 어셈블리 1 |
| `s36h0.c`·`s36h1.c`·`s36h2.c` | ★★ C23 판 격자 · gcc-12 · clang 경고 | 격자 18 · 진단 5 · 헤더 1 |
| `s36go.go` | ★ Go 슬라이스 | 1 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. **이 편의 블록은 정규화 없이 전부 동일**이어야 하고, 그랬다(흔들리는 수는 블록에 싣지 않았다).

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **1·2번의 실행 결과** — gcc 의 `ud2` 와 clang 의 값은 **UB 를 만난 두 구현의 선택**이다.
- ★★ **6·7번** — `va_list` 가 24바이트 배열인 것, `va_end` 가 명령 0개인 것은 **x86-64 System V** 의 것이다.
- ★★ **5번의 침묵** — 이 판의 다섯 도구.
- ★ **8번의 clang 경고** — clang 18 의 헤더와 `-pedantic` 의 조합.

**기본 인자 승격 · `va_arg` 의 호환 규칙과 예외 · 넘긴 `ap` 가 불확정인 것 · `va_end` 의무 · C23 의 두 변경은 구현 의존이 아니다.**\
어느 C 구현에서도 같다(판 안에서).

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `va_arg(ap, unsigned int)` 로 `int` 꺼내기(허락된 예외) · `vprintf` 뒤 `ap` 재사용 · `nullptr` 센티널 · `-Wformat=2`.
- ★ **못 잰 것** — **다른 ABI 의 `va_list`**(이 머신은 x86-64 Linux 뿐).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **2번 격자** — 컴파일러가 UB 를 만났을 때의 선택이 바뀔 수 있다(clang 이 `ud2` 를 심는다든지).
- ★★ **8번 판 격자** — clang 의 `-pedantic` 경고가 고쳐질 수 있다.
- ★ **5번** — sanitizer 가 `va_arg` 검사를 들여올 수 있다.
