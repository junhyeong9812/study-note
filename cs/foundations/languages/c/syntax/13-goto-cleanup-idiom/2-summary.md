# c/syntax/13 — `goto cleanup` 관용구: 「**분기가 아니라 중복을 줄인다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — `goto`](https://en.cppreference.com/w/c/language/goto) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html) · [Clang Diagnostic flags](https://clang.llvm.org/docs/DiagnosticsReference.html)
> **실행 검증** — 이 문서의 모든 출력·경고·에러·어셈블리는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과\
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 작업 디렉터리는 `/tmp/c13` 이고 소스 파일명은 언제나 `ex.c` 다 — sanitizer 출력에 경로가 박히기 때문이다.\
> ★★ **실행 블록은 `./x 2>&1 | cat` 로 받았다** — sanitizer 는 stderr, `printf` 는 stdout 이라\
> **터미널과 파이프에서 순서가 달라진다.** 섞이는 프로그램에는 `fflush(stdout)` 또는 `setvbuf(…, _IONBF, …)` 를 넣어 **순서를 고정**했고 소스에 그렇게 적혀 있다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸** — 다시 돌리면 바뀌는 것을 미리 선언한다.
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | `%p` 주소값 · 스택 주소 · ASan 의 `pc`/`bp`/`sp` | 주소들 **사이의 차이** |
> | ASan 리포트의 **PID**(`==12345==`)·`BuildId`·모듈 오프셋 | **`파일:줄:칸`** · 진단 본문 · 프레임 **함수 이름** |
> | 초기화 안 된 변수의 값 | **종료 코드** · 경고 건수 · 플래그 이름 |
> | 어셈블리의 **레지스터 이름**(`r12` ↔ `r13`) | 어셈블리의 **명령·분기·`call` 개수** |
>
> **버전** — `goto` 와 라벨의 규칙은 **C89 이후 바뀐 적이 없다.**\
> **C23 이 둘을 바꿨다** — 「**라벨 뒤 선언**」과 「**블록 끝의 라벨**」이 허용됐다. 아래 (8)에서 실측한다.\
> ★ **gcc 13.3.0 에는 `-std=c23` 이 없다**(`-std=c2x` 뿐) — 이 문서도 `-std=c2x` 로 던졌다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★ **경계** — `goto` 자체의 기본 동작과 VLA 스코프 금지는 [12번 형제](../12-control-flow-and-switch/)가 정본이다.\
> 여기는 「**그것으로 다중 자원 해제를 어떻게 짜나**」만 본다. `malloc`/`free` 의 계약은 목록의 **37번 주제**가 정본이다.
> 선행 — [12번 형제](../12-control-flow-and-switch/) · 목록의 **37번 주제**.

## 한눈에 — 쉽게 말하면

**`goto cleanup` 은 「등산의 하산길」이다.**

산을 오른다고 하자.\
1단계 베이스캠프를 세우고, 2단계 중간캠프를 세우고, 3단계 정상 캠프를 세운다.\
어느 단계에서든 날씨가 나빠지면 **내려와야 하는데**, 내려오는 길은 **올라온 순서의 역순**이다 —\
정상 캠프를 걷고, 중간 캠프를 걷고, 베이스캠프를 걷는다.

여기서 중요한 것은 「**2단계에서 실패했으면 2단계 캠프는 아직 없다**」는 것이다.\
없는 캠프를 걷으려 하면 사고가 난다. 그래서 **실패한 단계에 맞는 하산 지점**으로 내려와야 한다.

`goto cleanup` 이 하는 일이 정확히 그것이다.\
정리 코드를 **함수 끝에 한 줄씩 층층이 쌓아 두고**, 실패한 단계가 **자기 층으로 뛰어내린다.**

| 비유 | 실체 | 층 |
|---|---|---|
| 베이스 → 중간 → 정상 순서로 세운다 | 자원을 순서대로 획득 | **표준** |
| 하산은 정상 → 중간 → 베이스 | ★ **역순 해제** | **표준** |
| 2단계에서 실패하면 2층으로 내려온다 | `goto out_buf;` 처럼 **층마다 다른 라벨** | **표준** |
| 없는 캠프를 걷으면 사고 | `fclose(NULL)` — ★ 실측에서 **SIGSEGV** | ★ **UB** |
| 짐이 없으면 그냥 지나간다 | `free(NULL)` — **표준이 보장한다** | **표준** |
| 하산길은 **한 줄기** | 정리 코드가 소스에 **한 번만** 적힌다 | — |

```text
   획득 (올라간다)                       해제 (내려온다)

   buf  = malloc()  --실패--> goto out;        out:       return rc;
     |                                          ^
   file = fopen()   --실패--> goto out_buf; ----+---> out_buf:  free(buf);
     |                                          ^                  ^
   tbl  = calloc()  --실패--> goto out_file;----+---> out_file: fclose(f);
     |                                                             ^
   본작업           --실패--> goto out_tbl; ------------> out_tbl: free(tbl);

   ★ 라벨 이름은 "다음에 할 일" 이 아니라 "지금까지 잡은 것" 을 가리킨다.
      out_buf 로 뛰면 buf 만 풀고 끝난다 — file 은 아직 없기 때문이다.
```

- ★★ **이 주제에는 UB 가 거의 없다.** [12번 형제](../12-control-flow-and-switch/)와 같은 성격이고,\
  [15번 형제](../15-pointer-arithmetic-and-indexing)·[16번 형제](../16-array-pointer-decay-and-function-parameters)가 **UB 가 본체**인 것과 정반대다.\
  이 주제에서 틀리면 대개 **빌드가 안 되거나**, 아니면 **자원이 조용히 샌다.**
- ★ 그래서 이 주제의 네 번째 창은 **어셈블리**와 **LeakSanitizer** 다 — 앞의 셋으로는 「샜다」가 안 보인다.

> **관용구(idiom)** — 문법이 아니라 **그 언어에서 굳어진 쓰는 방식**. 컴파일러는 모른다.\
> 예: C 에 `finally` 가 없어서 「정리는 함수 끝 라벨로 모은다」가 관용구가 됐다.

> **역순 해제(reverse-order release)** — 획득한 순서의 **거꾸로** 풀어 주는 것.\
> 예: 버퍼 → 파일 → 표 순서로 잡았으면 표 → 파일 → 버퍼 순서로 푼다.

## 이 주제가 답하려는 질문

원고가 없는 관용구 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★ **왜 C 에만 이 패턴이 남는가** — 소멸자도 `defer` 도 `finally` 도 없는 언어에서 무엇이 대신하나.
2. ★★ **`goto` 판이 중첩 `if` 판보다 정말 싼가** — 소스와 **기계어**를 둘 다 세어 확인한다.
3. ★ **이 패턴이 깨지는 자리는 어디인가** — 라벨 뒤 선언 · 블록 끝 라벨 · `fclose(NULL)`.

## 동작 방식

### (1) 다중 자원 획득 함수 — 실패 경로를 **단계마다** 던진다

**언제 쓰나** — 자원을 둘 이상 잡는 함수를 쓸 때. 실패는 **어느 단계에서든** 날 수 있다.

```text
===== 소스: ex.c (13-a) =====
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* 자원 셋을 단계마다 실패시키기 위한 스위치 */
static int fail_at;                 /* 0 이면 전부 성공, N 이면 N 번째 획득이 실패 */

static void *get_buf(int step, size_t n) {
    if (fail_at == step) { printf("  [%d] buf   획득 실패\n", step); return NULL; }
    void *p = malloc(n);
    printf("  [%d] buf   획득\n", step);
    return p;
}
static FILE *get_file(int step, const char *path) {
    if (fail_at == step) { printf("  [%d] file  획득 실패\n", step); return NULL; }
    FILE *f = fopen(path, "w");
    printf("  [%d] file  획득\n", step);
    return f;
}
static int *get_tbl(int step, size_t n) {
    if (fail_at == step) { printf("  [%d] table 획득 실패\n", step); return NULL; }
    int *t = calloc(n, sizeof *t);
    printf("  [%d] table 획득\n", step);
    return t;
}

static int run(void) {
    char *buf = NULL;
    FILE *f   = NULL;
    int  *tbl = NULL;
    int rc = -1;

    buf = get_buf(1, 64);
    if (!buf) goto out;

    f = get_file(2, "/tmp/c13a.tmp");
    if (!f) goto out_buf;

    tbl = get_tbl(3, 8);
    if (!tbl) goto out_file;

    if (fail_at == 4) { printf("  [4] 본작업 실패\n"); goto out_tbl; }

    strcpy(buf, "ok");
    fputs(buf, f);
    tbl[0] = 1;
    printf("  [*] 본작업 성공\n");
    rc = 0;

out_tbl:
    free(tbl);   printf("  <-- table 해제\n");
out_file:
    fclose(f);   printf("  <-- file  해제\n");
out_buf:
    free(buf);   printf("  <-- buf   해제\n");
out:
    printf("  rc=%d\n", rc);
    return rc;
}

int main(void) {
    for (int k = 0; k <= 4; k++) {
        fail_at = k;
        printf("fail_at=%d\n", k);
        run();
    }
    return 0;
}
```

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
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -g -fsanitize=address,undefined · ./x 2>&1 | cat =====
(출력이 위와 바이트 단위로 같고 — diff 로 대조했다 — 진단은 0줄이다. run exit=0)
```

```text
   fail_at 별로 몇 개를 푸나

   fail_at  획득한 것        뛴 라벨      푼 것                 푼 개수
   -------  ---------------  ----------   -------------------   -------
      1     (없음)            out          (없음)                  0
      2     buf               out_buf      buf                     1
      3     buf file          out_file     file buf                2
      4     buf file tbl      out_tbl      tbl file buf            3
      0     buf file tbl      (안 뜀)       tbl file buf            3

   ★ "푼 개수 == 획득한 개수" 가 다섯 줄 전부 맞는다. 이것이 이 패턴이 파는 것이다.
```

그림 해설 (한 단계씩):

- **다섯 경로가 전부 밟혔다.** 획득 실패 셋 · 본작업 실패 하나 · 성공 하나.
- ★ **해제 순서가 언제나 획득의 역순**이다 — `table` → `file` → `buf`.\
  라벨을 **아래로 갈수록 먼저 풀 것**으로 쌓았기 때문이고, 각 라벨 뒤에 `break` 같은 것이 없으니 **그대로 흘러내린다.**
- ★★ **라벨 이름이 「지금까지 잡은 것」을 가리킨다.** `out_buf` 는 「buf 만 잡혀 있다」는 뜻이고,\
  그래서 `goto out_buf;` 는 **buf 하나만 푼다.** 이름을 「다음에 풀 것」으로 읽으면 한 칸씩 어긋난다.
- **ASan·UBSan 이 진단 0줄**로 통과했다 — 누수도 이중 해제도 없다.

비용 — 라벨 개수 = 자원 개수. **정리 코드는 소스에 한 번씩만 적힌다.**

### (2) `fclose(NULL)` — 왜 라벨을 **하나로 합치면 안 되나**

**언제 쓰나** — 「라벨 하나에 `free` 를 다 몰아 넣으면 안 되나?」라고 생각했을 때.

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

> **대조할 것은 숫자가 아니라 성질이다.** PID(`==3647034==`)·주소·`pc`/`bp`/`sp`·`BuildId` 는 **실행마다 바뀐다.**\
> 근거는 **`SEGV on unknown address 0x000000000000`** · **`_IO_new_fclose`** 라는 프레임 이름 ·\
> **`main /tmp/c13/ex.c:11`** 이라는 줄 번호 · **`run exit=1`** 이고, 넷 다 세 판에서 같았다.\
> ★ **`free(NULL) 통과` 가 맨 앞에 오는 것**은 소스에 `fflush(stdout);` 이 있어서다 —\
> 그것이 없으면 **파이프로 받을 때 stdout 이 끝에 몰려** 순서가 뒤집힌다.

그림 해설 (한 단계씩):

- **`free(NULL)` 은 표준이 「아무 일도 하지 않는다」고 보장한다.** 경고도 없고 죽지도 않는다.
- ★★ **`fclose(NULL)` 에는 그런 보장이 없다.** 실측에서 **SIGSEGV** 로 죽었고 셸이 종료 코드 **139**(= 128 + 11)를 돌려줬다.
- ★ **그래서 라벨을 하나로 합칠 수 없다.** 「`out:` 하나에 `free`·`fclose` 를 다 모으자」는\
  `malloc` 만 쓰는 함수에서는 되고 **파일·락·소켓이 섞이는 순간 깨진다.**
- ★ **UBSan 이 `fclose` 에 붙은 `nonnull` 속성을 읽어 말해 줬다** — `null pointer passed as argument 1`.\
  **표준이 아니라 glibc 헤더의 속성**이 근거라 **다른 libc 에서는 안 나올 수 있다.**

비용 — 라벨이 자원 개수만큼 는다. **그 대신 「잡지도 않은 것을 푸는」 경로가 사라진다.**

### (3) 세 판을 나란히 — `goto` · 중첩 `if` · 정리 코드 복사

**언제 쓰나** — 「`goto` 안 쓰고도 되잖아」라고 할 때. **세 판이 무엇을 다르게 파는지** 세어 본다.

```text
===== 소스: ex.c (13-b) =====
/* 같은 일을 하는 세 판 — goto / 중첩 if / 정리 코드 복사 */
extern void *acq1(void);
extern void *acq2(void);
extern void *acq3(void);
extern int   work(void *, void *, void *);
extern void  rel1(void *);
extern void  rel2(void *);
extern void  rel3(void *);

int with_goto(void) {
    void *a = 0, *b = 0, *c = 0;
    int rc = -1;
    a = acq1(); if (!a) goto out;
    b = acq2(); if (!b) goto out_a;
    c = acq3(); if (!c) goto out_b;
    rc = work(a, b, c);
    rel3(c);
out_b:
    rel2(b);
out_a:
    rel1(a);
out:
    return rc;
}

int with_nest(void) {
    int rc = -1;
    void *a = acq1();
    if (a) {
        void *b = acq2();
        if (b) {
            void *c = acq3();
            if (c) {
                rc = work(a, b, c);
                rel3(c);
            }
            rel2(b);
        }
        rel1(a);
    }
    return rc;
}

int with_dup(void) {
    void *a = acq1();
    if (!a) return -1;
    void *b = acq2();
    if (!b) { rel1(a); return -1; }
    void *c = acq3();
    if (!c) { rel2(b); rel1(a); return -1; }
    int rc = work(a, b, c);
    rel3(c); rel2(b); rel1(a);
    return rc;
}
```

```text
===== 소스 쪽 세기 (빈 줄 제외) =====
with_goto : 줄 15 · 해제 호출이 소스에 적힌 횟수 3
with_nest : 줄 17 · 해제 호출이 소스에 적힌 횟수 3
with_dup  : 줄 11 · 해제 호출이 소스에 적힌 횟수 6
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -S -masm=intel (경고 0 건, exit=0) =====
함수            명령     j*   call test/cmp
with_goto        39      4      7      3
with_nest        39      4      7      3
with_dup         45      5     10      3
```

```text
===== gcc -std=c17 -O<수준> -S -masm=intel — 명령 수 =====
수준       goto     nest      dup
-O0          45       36       50
-O1          39       39       48
-O2          39       39       45
-O3          39       39       45
-Os          37       37       41
```

```text
   세 판이 파는 것

   +---------------------+  +---------------------+  +---------------------+
   | with_goto           |  | with_nest           |  | with_dup            |
   |---------------------|  |---------------------|  |---------------------|
   | 소스 15줄           |  | 소스 17줄           |  | 소스 11줄  <- 제일 짧다
   | 해제 호출 3곳       |  | 해제 호출 3곳       |  | 해제 호출 6곳 <- ★ 두 배
   | 들여쓰기 1단        |  | 들여쓰기 ★ 3단      |  | 들여쓰기 1단        |
   | -O2 명령 39         |  | -O2 명령 39         |  | -O2 명령 45         |
   +---------------------+  +---------------------+  +---------------------+

   ★ goto 와 nest 는 -O1 이상에서 기계어가 사실상 같다.
      비싼 것은 "정리 코드를 복사한 판" 이다.
```

그림 해설 (한 단계씩):

- ★★★ **`goto` 판이 중첩 `if` 판보다 분기가 적지 않다.** `-O2` 에서 **명령 39 · 분기 4 · `call` 7 로 둘이 같다.**\
  `-O1`·`-Os` 에서는 **명령 열까지 같았고**, `-O2`\~`-O3` 에서 **다른 것은 레지스터 이름뿐**이었다(`r12` ↔ `r13` 6곳).
- ★ **`-O0` 에서는 오히려 중첩 `if` 쪽이 적다**(36 대 45). **최적화를 끄면 결론이 뒤집힌다** —\
  한 수준만 보고 단정하면 안 되는 자리다.
- ★★ **진짜로 갈리는 것은 「정리 코드를 복사한 판」이다** — `-O2` 에서 **명령 45 · 분기 5 · `call` 10.**\
  `call` 이 **세 개 더** 있는 것이 소스의 「해제 호출 6곳」과 그대로 맞는다.
- ★ **그러니 `goto cleanup` 의 값은 분기 절약이 아니다.** 값은 「**정리 코드가 소스에 한 번만 적힌다**」는 것이고,\
  그래야 **자원을 하나 더 늘릴 때 고칠 자리가 한 곳**이다.
- **중첩 `if` 판도 정리 코드를 한 번만 적는다.** 대신 **들여쓰기가 자원 개수만큼 깊어진다** — 자원이 다섯이면 5단이다.

비용 — `goto` 판과 중첩 `if` 판은 **기계어로는 같은 값**이다. 고르는 기준은 **읽기와 고치기**다.

### (4) 그래서 왜 **C 에만** 이 패턴이 남는가

**언제 쓰나** — 다른 언어를 쓰다 온 사람이 「왜 이렇게 지저분하게 쓰냐」고 할 때.

```text
   같은 일을 각 언어가 어떻게 하나

   C              획득 -> 실패하면 goto out_xxx -> 라벨에 해제를 층층이     <- 직접 쓴다
   C++            생성자에서 잡고 ★ 소멸자가 자동으로 푼다 (RAII)           <- 스코프가 푼다
   Rust           값이 스코프를 벗어나면 ★ Drop 이 자동으로 호출된다        <- 스코프가 푼다
   Go             defer f.Close()  -> 함수가 끝날 때 역순 실행              <- 런타임이 푼다
   Java/C#        try { } finally { }  /  try-with-resources                <- 예외 기구가 푼다

   ★ C 에는 이 다섯 중 아무것도 없다 —
     소멸자도 없고, 예외도 없고, defer 도 없고, finally 도 없다.
     함수가 끝날 때 "자동으로 불리는 코드" 라는 개념 자체가 없다.
```

그림 해설 (한 단계씩):

- **C 의 지역 변수는 스코프를 벗어날 때 저장 공간만 사라진다.** `malloc` 한 메모리·열린 파일은 **아무도 건드리지 않는다.**
- **C 에는 예외가 없어서** 실패가 **반환값**으로만 온다. 실패마다 「여기까지 잡은 것」을 **사람이 직접** 추적해야 한다.
- ★★ 그 둘이 합쳐져서 「**함수 끝에 정리 구역을 만들고 실패 경로가 거기로 뛴다**」가 유일한 구조적 답이 된다.\
  `goto` 는 **함수 안의 다른 지점으로 무조건 뛰는 유일한 문**이라 이 자리를 맡게 됐다.
- ★ **그래서 이것은 「`goto` 를 쓰자」는 주장이 아니다.** 「`goto` 가 없으면 **정리 코드를 복사해야 한다**」는 것이고,\
  (3)에서 복사판이 `call` 을 셋 더 만든 것을 봤다. **복사가 늘면 빠뜨릴 자리도 는다.**
- Linux 커널·OpenSSL·SQLite 같은 대형 C 코드베이스가 이 형태를 쓴다 —\
  ★ 그러나 **이 문서는 그 코드베이스들을 읽어 확인하지 않았다.** 「널리 쓰인다」는 관찰이 아니라 전해 들은 것이다.

비용 — 없다. **C 에는 대안이 없다.**

### (5) `goto` 가 **할 수 있는 것** 셋

**언제 쓰나** — 정리 말고 `goto` 가 쓸모 있는 자리를 셀 때.

```text
===== 소스: ex.c (13-g) =====
#include <stdio.h>

int main(void) {
    /* (1) 중첩 루프를 한 번에 나가기 */
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            if (i * 3 + j == 4) { printf("(1) 찾음 i=%d j=%d\n", i, j); goto found; }
found:
    /* (2) 뒤로 뛰기 — 루프를 만든다 */
    ;
    int n = 0;
again:
    n++;
    if (n < 3) goto again;
    printf("(2) 뒤로 세 번 뛰어 n=%d\n", n);

    /* (3) 블록 밖으로 나오기 */
    {
        {
            goto escaped;
        }
    }
escaped:
    printf("(3) 두 겹 블록에서 나왔다\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, exit=0) =====
(1) 찾음 i=1 j=1
(2) 뒤로 세 번 뛰어 n=3
(3) 두 겹 블록에서 나왔다
```

그림 해설 (한 단계씩):

- **중첩 루프 탈출** — `break` 는 **가장 안쪽 하나만** 끝낸다([12번 형제](../12-control-flow-and-switch/)). 두 겹을 한 번에 나가려면 깃발이나 `goto` 다.
- **뒤로 뛰기** — 라벨이 **앞에 있어도** 된다. 실제로 루프가 만들어진다.
- **블록 탈출** — 몇 겹이든 **밖으로** 나오는 것은 막히지 않는다.
- ★ `found:` 뒤에 세미콜론 하나(`;`)가 있는 것을 보라 — **C17 에서 라벨 뒤에는 「문」이 와야** 하기 때문이다.\
  바로 뒤가 선언(`int n = 0;`)이면 안 된다. 그 규칙을 (8)에서 실측한다.

비용 — 없다. 단 **뒤로 뛰는 `goto` 는 읽기 어렵다** — 루프 문법이 있으면 그쪽을 쓴다.

### (6) `goto` 가 **못 넘는 것** 둘

**언제 쓰나** — 컴파일러가 막아 주는 몇 안 되는 자리다.

```text
===== 소스: ex.c (13-e) =====
#include <stdio.h>
static void run(int n, int fail) {
    if (fail) goto out;
    int vla[n];
    vla[0] = 1;
    printf("%d\n", vla[0]);
out:
    printf("out\n");
}
int main(void) { run(4, 1); return 0; }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (cc exit=1) =====
ex.c: In function ‘run’:
ex.c:3:15: error: jump into scope of identifier with variably modified type
    3 |     if (fail) goto out;
      |               ^~~~
ex.c:7:1: note: label ‘out’ defined here
    7 | out:
      | ^~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic (cc exit=1) =====
ex.c:3:15: error: cannot jump from this goto statement to its label
    3 |     if (fail) goto out;
      |               ^
ex.c:4:9: note: jump bypasses initialization of variable length array
    4 |     int vla[n];
      |         ^
```

```text
===== 소스: ex.c (13-h) =====
#include <stdio.h>
static void other(void) { printf("other\n"); }
int main(void) {
    goto out;
    return 0;
}
static void late(void) {
out:
    printf("late\n");
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (cc exit=1) =====
ex.c: In function ‘main’:
ex.c:4:5: error: label ‘out’ used but not defined
    4 |     goto out;
      |     ^~~~
ex.c: In function ‘late’:
ex.c:8:1: warning: label ‘out’ defined but not used [-Wunused-label]
    8 | out:
      | ^~~
```

그림 해설 (한 단계씩):

- ★ **VLA 스코프 안으로는 못 뛴다.** 경고가 아니라 **에러**이고 `exit=1` 이다 — [12번 형제](../12-control-flow-and-switch/)가 정본이고,\
  여기서도 **다시 던져 같은 결론을 받았다.** clang 쪽이 **이유**를 말해 준다(「초기화를 건너뛴다」).
- ★★ **라벨은 「함수 스코프」다.** 다른 함수의 라벨은 **보이지 않으므로** gcc 가 「**used but not defined**」라고 말한다 —\
  「함수를 넘는 점프는 금지」가 아니라 「**그런 이름이 없다**」로 진단이 나온다. 이름 공간 자체가 함수 단위다.
- ★ **종료 코드를 파이프 너머로 재면 틀린다.** 이 두 진단을 처음 잴 때 `| head` 를 끼웠더니\
  **clang 이 74, gcc 가 2** 로 나왔다. 파이프를 빼고 직접 재니 **둘 다 1** 이었다 — `head` 가 먼저 닫아 생긴 값이다.\
  **도구를 믿기 전에 도구가 무엇을 보는지 확인해야 한다.**

비용 — 없다. **이 둘은 컴파일러가 막아 준다.**

### (7) ★ 그런데 **초기화를 건너뛰는 것**은 막지 않는다

**언제 쓰나** — 「VLA 만 막힌다면 보통 변수는?」이라고 물었을 때. **이 주제의 사각지대**다.

```text
===== 소스: ex.c (13-f) =====
#include <stdio.h>
int main(void) {
    int fail = 1;
    if (fail) goto skip;
    {
        int v = 99;
skip:
        printf("v=%d\n", v);
    }
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic · ./x 를 네 번 돌린 결과 (경고 0 건, run exit=0) =====
v=491432456
(다시 돌리면) v=470477064
(또 돌리면)   v=-1579220376
(또 돌리면)   v=430025784
```

> **대조할 것은 숫자가 아니라 「실행마다 다르다」는 성질이다.** 네 번의 값이 전부 달랐고,\
> **같은 값이 두 번 나오면 그것이 우연**이다. 값 자체는 아무것도 증명하지 않는다.

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O<수준> =====
-O0 : 0 건
-O1 : 1 건   /usr/include/x86_64-linux-gnu/bits/stdio2.h:86:10: warning: ‘v’ is used uninitialized [-Wuninitialized]
-O2 : 1 건   (같은 줄)
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic (-O0, exit=0) =====
ex.c:4:9: warning: variable 'v' is used uninitialized whenever 'if' condition is true [-Wsometimes-uninitialized]
    4 |     if (fail) goto skip;
      |         ^~~~
ex.c:8:26: note: uninitialized use occurs here
    8 |         printf("v=%d\n", v);
      |                          ^
1 warning generated.
```

```text
   VLA 면                              보통 변수면
   +---------------------------+      +---------------------------+
   | goto 가 크기 잡기를 건너뜀 |      | goto 가 초기화를 건너뜀    |
   |   -> ★ 컴파일 에러         |      |   -> ★ 합법. v 는 "선언됨,|
   |      (없는 메모리를 쓰게됨)|      |      값은 불확정"          |
   +---------------------------+      +---------------------------+
                                        그 값을 읽는 것이 UB 이고,
                                        ★ gcc -O0 은 아무 말도 안 한다.
```

그림 해설 (한 단계씩):

- ★★ **보통 변수의 초기화를 건너뛰는 `goto` 는 합법이다.** C 는 **선언과 초기화를 가른다** —\
  `v` 는 블록에 들어간 시점부터 **존재하고**, 건너뛴 것은 **초기화뿐**이다.
- ★ **그 값을 읽는 것이 UB** 이고, 실측 값이 **네 번 다 달랐다.**
- ★★★ **gcc 는 `-O0` 에서 어떤 플래그 조합으로도 0건**이다(`-Wall -Wextra -pedantic` 포함).\
  `-O1` 부터 말해 주는데 **가리키는 줄이 시스템 헤더**(`stdio2.h:86`)라 원인을 찾기 어렵다.
- ★ **clang 은 `-O0` 에서 바로 잡고 원인 줄을 가리킨다**(`-Wsometimes-uninitialized`).\
  **같은 함정을 두 컴파일러가 전혀 다른 조건에서 본다** — 둘 다 돌려야 하는 이유다.
- ★ **`goto cleanup` 에서 이 사고가 나는 자리는 정해져 있다** — 자원 포인터를 **선언과 동시에 `NULL` 로 초기화하지 않았을 때**다.\
  (1)의 `char *buf = NULL;` 이 바로 그 방어다.

비용 — 변수 하나당 `= NULL` 한 번. **그것이 이 패턴의 전제**다.

### (8) 라벨 뒤에 선언이 오면 — **C23 이 바꾼 둘**

**언제 쓰나** — `goto cleanup` 을 쓰다 보면 **반드시 만나는** 두 자리다.

```text
===== 소스: ex.c (13-c) =====
#include <stdio.h>
#include <stdlib.h>

static int run(int fail) {
    char *buf = malloc(8);
    if (!buf) return -1;
    if (fail) goto out;
    buf[0] = 'x';
out:
    int n = 1;              /* ★ 라벨 바로 뒤의 선언 */
    free(buf);
    return n;
}

int main(void) { printf("run=%d\n", run(1)); return 0; }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘run’:
ex.c:10:5: warning: a label can only be part of a statement and a declaration is not a statement [-Wpedantic]
   10 |     int n = 1;              /* ★ 라벨 바로 뒤의 선언 */
      |     ^~~
```

```text
===== clang -std=c17 -Wall -Wextra (exit=0) =====
ex.c:10:5: warning: label followed by a declaration is a C23 extension [-Wc23-extensions]
   10 |     int n = 1;              /* ★ 라벨 바로 뒤의 선언 */
      |     ^
1 warning generated.
```

```text
===== 소스: ex.c (13-d) =====
#include <stdio.h>
#include <stdlib.h>

static void run(int fail) {
    char *buf = malloc(8);
    if (!buf) return;
    if (fail) goto out;
    buf[0] = 'x';
out:
    free(buf);
cleanup_end:
}

int main(void) { run(1); printf("done\n"); return 0; }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘run’:
ex.c:11:1: warning: label at end of compound statement [-Wpedantic]
   11 | cleanup_end:
      | ^~~~~~~~~~~
ex.c:11:1: warning: label ‘cleanup_end’ defined but not used [-Wunused-label]
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c:12:1: warning: label at end of compound statement is a C23 extension [-Wc23-extensions]
   12 | }
      | ^
ex.c:11:1: warning: unused label 'cleanup_end' [-Wunused-label]
   11 | cleanup_end:
      | ^~~~~~~~~~~~
2 warnings generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic-errors (exit=1) =====
ex.c: In function ‘run’:
ex.c:10:5: error: a label can only be part of a statement and a declaration is not a statement [-Wpedantic]
   10 |     int n = 1;              /* ★ 라벨 바로 뒤의 선언 */
      |     ^~~
```

```text
   같은 소스를 네 조합으로 던진 결과 (13-c : 라벨 뒤 선언)

   gcc  -std=c17  -Wall -Wextra           0 건   <- ★ 아무 말도 안 한다
   gcc  -std=c17  +pedantic               1 건   [-Wpedantic]
   gcc  -std=c17  +pedantic-errors        error  exit=1
   gcc  -std=c2x  +pedantic               0 건   <- C23 에서 합법
   clang -std=c17 -Wall -Wextra           1 건   [-Wc23-extensions]  <- pedantic 없이도
   clang -std=c2x +pedantic               0 건
```

그림 해설 (한 단계씩):

- ★★ **C17 에서 라벨 뒤에는 「문」이 와야 한다.** 선언은 문이 아니고, **블록의 닫는 중괄호도** 문이 아니다.\
  그래서 `out: int n = 1;` 과 `cleanup_end: }` 가 **둘 다 표준 위반**이다.
- ★ **둘 다 C23 에서 허용됐다.** `-std=c2x` 로 던지면 **양쪽 다 0건**이 된다.
- ★★★ **`-std=c17` 만으로는 이 위반이 드러나지 않는다** — gcc 는 `-Wall -Wextra` 로도 **0건**이고,\
  **`-pedantic` 을 붙여야** 말한다. **`-std=` 는 강제가 아니라 기본값 선택**이다.
- ★ **clang 은 다르다** — `-pedantic` 없이도 `-Wc23-extensions` 로 말해 준다. **같은 사실을 다른 조건에서 본다.**
- ★ **C17 코드에서 고치는 법은 세미콜론 하나**다 — `out: ; int n = 1;` 또는 `cleanup_end: ;` 로 **빈 문**을 둔다.\
  (5)의 `found: ;` 가 그것이다.

비용 — 세미콜론 하나. **`-pedantic` 을 안 켜면 그 하나가 필요한 줄도 모른다.**

### (9) 이 주제의 진단을 한 표로

```text
===== 각 프로그램을 일곱 조합으로 던져 warning: 줄을 센 것 =====
(세는 법 — grep -c 'warning:' 이다. grep -c warning 은 clang 의
 "2 warnings generated." 요약 줄까지 세어 한 건이 더 나온다)
```

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

- **종료 코드까지 같이 봐야 뜻이 있다.** 13-e·13-h 는 **경고 0건에 `exit=1`** 이다 — 경고만 셌으면 「깨끗함」으로 기록됐다.
- 13-d 의 `-Wall` 1건은 **`-Wunused-label`** 이고 표준 위반과는 **다른 이야기**다. 위반 쪽은 `-pedantic` 이 말한다.
- ★ **13-f 와 13-i 가 이 주제의 사각지대**다 — **컴파일러가 0건**이고 런타임 도구(clang 의 `-O0` 진단·UBSan·ASan)만 말한다.

## 문법 — 형태와 규칙

### 형태 — 관용구의 뼈대

```c
static int f(void) {
    T1 *r1 = NULL;              /* ① 전부 NULL 로 초기화 — goto 가 초기화를 건너뛸 수 있다 */
    T2 *r2 = NULL;
    int rc = -1;                /* ② 실패를 기본값으로 */

    r1 = acquire1();  if (!r1) goto out;        /* ③ 아무것도 안 잡혔으면 out */
    r2 = acquire2();  if (!r2) goto out_r1;     /* ④ r1 만 잡혔으면 out_r1 */

    if (do_work(r1, r2) < 0) goto out_r2;       /* ⑤ 본작업 실패도 같은 길 */
    rc = 0;                                      /* ⑥ 여기까지 왔으면 성공 */

out_r2: release2(r2);           /* ⑦ 획득의 역순으로 쌓는다 */
out_r1: release1(r1);
out:    return rc;              /* ⑧ 라벨 뒤에는 "문" 이 와야 한다 (C17) */
}
```

### 금지 사례 — 어느 것이 무슨 층인가

```c
/* (가) 라벨 하나에 몰아 넣기 — NULL 을 견디지 못하는 해제 함수가 섞이면 ★ UB */
out:  free(buf); fclose(f);     /* f 가 NULL 이면 SIGSEGV (실측) */

/* (나) 라벨 뒤 선언 — C17 표준 위반, C23 합법. -pedantic 만 말한다 */
out:  int n = 0;

/* (다) 라벨이 블록 끝 — C17 표준 위반, C23 합법 */
out:  }

/* (라) VLA 스코프 안으로 점프 — ★ 컴파일 에러 (exit=1) */
goto out;  int vla[n];  out: ;

/* (마) 초기화 없이 선언 후 goto 로 건너뛰기 — 합법이지만 읽으면 ★ UB */
char *buf;  if (x) goto out;  buf = malloc(8);  out: free(buf);

/* (바) 다른 함수의 라벨로 점프 — ★ 컴파일 에러 (라벨은 함수 스코프) */
```

### 규칙 불릿

- **라벨은 함수 스코프**다. 같은 함수 안 어디서든 보이고, **함수를 넘지 못한다.**
- **`goto` 는 앞으로도 뒤로도** 뛴다. 블록 **밖으로** 나오는 것은 언제나 된다.
- ★ **블록 안으로 뛰어드는 것도 된다** — 단 **VLA 가 사는 스코프만 예외**(컴파일 에러).
- ★ **초기화를 건너뛴 변수는** 「**선언은 됐고 값은 불확정**」이다. 읽으면 UB.
- ★ **C17 에서 라벨 뒤에는 문이 와야 한다.** 선언도 `}` 도 안 된다. **C23 에서 둘 다 허용.**
- **`free(NULL)` 은 안전하고 `fclose(NULL)` 은 아니다.** 해제 함수마다 계약이 다르다.
- **라벨 이름은** 「**지금까지 잡은 것**」으로 짓는다(`out_buf`). 「다음에 할 일」로 읽으면 한 칸 어긋난다.

## 어디서 틀리나

### 1. ★★ 「라벨 하나에 정리를 다 모으면 되잖아」

- `malloc` 만 쓰는 함수에서는 된다 — **`free(NULL)` 이 안전**하기 때문이다.
- ★ **파일·락·소켓이 섞이는 순간 깨진다.** 실측에서 `fclose(NULL)` 이 **SIGSEGV** 로 죽었다(run exit=139).
- **어떤 컴파일러 플래그도 0건**이다. UBSan 이 glibc 의 `nonnull` 속성을 읽어야 겨우 말해 준다.

### 2. ★★ 「`goto` 를 쓰면 분기가 줄어 빠르다」

- ★ **틀렸다.** `-O2` 에서 `goto` 판과 중첩 `if` 판이 **명령 39 · 분기 4 · `call` 7 로 같았다.**
- `-O1`·`-Os` 에서는 **명령 열까지 같았고**, `-O0` 에서는 **중첩 `if` 쪽이 오히려 적었다**(36 대 45).
- **이 패턴이 파는 것은 속도가 아니라** 「**정리 코드가 소스에 한 번만 적힌다**」는 것이다.

### 3. ★ 「자원 포인터는 쓰기 직전에 선언하면 되지」

- `goto` 가 그 선언을 **건너뛸 수 있다.** 초기화만 건너뛰고 변수는 존재하므로 **컴파일은 된다.**
- ★ **gcc `-O0` 은 어떤 플래그로도 0건**이다. `-O1` 부터 말하는데 **시스템 헤더 줄**을 가리킨다.
- **선언 자리에서 `= NULL`** 을 붙이는 것이 이 패턴의 전제다.

### 4. ★ 「`out:` 뒤에 바로 변수를 선언했는데 왜 경고가?」

- **C17 에서 라벨 뒤에는 문이 와야 한다.** 선언은 문이 아니다.
- **`-pedantic` 없이는 gcc 가 0건**이고, clang 은 `-Wc23-extensions` 로 말한다.
- 고치는 법은 **세미콜론 하나**(`out: ;`) 또는 **`-std=c2x`**.

### 5. 「`out:` 를 함수 맨 끝 `}` 바로 앞에 두면 깔끔하다」

- 그 자리에 **문이 없으면** 역시 C17 위반이다(「label at end of compound statement」).
- `out: return rc;` 처럼 **반드시 문을 하나 둔다.**

### 6. ★ 「라벨 이름을 `free_file`, `free_buf` 로 지었다」

- 그러면 「**다음에 풀 것**」으로 읽혀 **한 칸씩 어긋난다.**
- `out_buf` 는 「**buf 까지 잡혀 있다**」는 뜻으로 읽어야 `goto out_buf;` 가 맞는 개수를 푼다.

### 7. 「종료 코드는 `| head` 를 끼워도 같겠지」

- ★ **아니다.** 이 문서를 쓰며 clang 이 **74**, gcc 가 **2** 로 나온 적이 있는데 **파이프 때문**이었다.
- **파이프를 빼고 직접 재니 둘 다 1** 이었다. **「경고 0건」과 짝지어 보는 숫자이므로 틀리면 결론이 뒤집힌다.**

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★ **이 주제는 「표준」 칸이 압도적으로 두껍고 UB 칸이 거의 비어 있다.**\
[15번 형제](../15-pointer-arithmetic-and-indexing)·[16번 형제](../16-array-pointer-decay-and-function-parameters)가 **UB 가 본체**인 것과 정반대이고, [12번 형제](../12-control-flow-and-switch/)와 같은 모양이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★ **본체** — 라벨이 **함수 스코프**인 것 · `goto` 가 앞뒤·블록 밖으로 뛰는 것 · 라벨 뒤로 **흘러내리는 것**(역순 해제가 성립하는 근거) · **`free(NULL)` 이 무해한 것** · C17 의 「라벨 뒤에는 문」 · **VLA 스코프 진입 금지** | 다섯 경로 출력 대조 · `-pedantic` 진단 · `exit=1` | ★★ **라벨 이름이 틀린 것** — `goto out_file;` 을 써야 할 자리에 `goto out_buf;` 를 쓰면 **경고 0건**에 자원이 샌다 |
| **조건부 표준** | 매크로가 정의될 때만 | **해당 없음** — 이 주제에 조건부 보장은 없다 | — | — |
| **구현 정의** | 문서화 의무가 있다 | ★ **거의 없다** — `goto` 를 **점프로 컴파일할지 흘려보낼지**는 구현이 고르지만 **동작은 같다** | `-O0`\~`-Os` 다섯 벌 명령 수 | ★ **어느 쪽이든 동작이 같다** — 성능만 다르고 실측에서 그 차이도 없었다 |
| **미명시** | 몇 가지 중 하나 | ★ **해당 없음** — `goto` 가 어디로 가는지는 전부 정해져 있다 | — | — |
| **UB** | 아무 일이나 | ★ **둘뿐이다** — ① **초기화를 건너뛴 변수를 읽는 것**(13-f) ② **`NULL` 을 견디지 못하는 해제 함수에 `NULL` 을 넘기는 것**(13-i, `fclose`) | 값이 네 번 다 다름 · SIGSEGV + UBSan `nonnull` | ★★ ①은 **gcc `-O0` 이 0건** · ②는 **모든 컴파일러 플래그가 0건** |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | gcc `-Wall -Wextra` | `+pedantic` | clang `-Wall -Wextra` | 런타임 도구 | 무엇이 잡나 |
|---|---|---|---|---|---|---|
| 정상 `goto cleanup` | 표준 | 0건 | 0건 | 0건 | ASan+UBSan 0줄 | ★ 잡을 것이 없다 |
| 라벨 뒤 선언(C17) | 표준 위반 | **0건** | **1건** | **1건** | — | ★ gcc 는 `-pedantic` 뿐 · clang 은 기본 |
| 블록 끝 라벨(C17) | 표준 위반 | 1건(`unused-label`) | **2건** | **2건** | — | ★ 위반 자체는 `-pedantic` 뿐 |
| VLA 스코프 진입 | — | **error** | error | **error** | — | 컴파일러가 막는다 |
| 함수 넘는 `goto` | — | **error** | error | **error** | — | 컴파일러가 막는다 |
| 초기화 건너뛴 값 읽기 | **UB** | ★ **0건**(`-O0`) | 0건 | **1건** | — | ★★ gcc 는 `-O1` 부터, **줄은 시스템 헤더** |
| `fclose(NULL)` | **UB** | **0건** | **0건** | **0건** | ★ UBSan `nonnull` + SIGSEGV | ★★ **컴파일러는 전부 침묵** |
| ★ 라벨을 잘못 골라 자원이 샘 | 표준 | **0건** | **0건** | **0건** | ★ **LeakSanitizer** | ★★★ **컴파일러가 절대 못 본다** |

- ★★ **이 표의 결론 세 줄**
  - **`-pedantic` 없이는 C17 표준 위반 둘이 보이지 않는다.** `-std=c17` 은 **기본값 선택**일 뿐이다.
  - **gcc 와 clang 이 서로 다른 것을 본다.** 라벨 규칙과 초기화 건너뜀은 **clang 이 먼저** 말한다.
  - ★★★ **이 관용구의 진짜 사고(라벨을 잘못 골라 자원이 새는 것)는 컴파일러가 못 본다.**\
    **문법이 맞고 동작도 정의되어 있기 때문**이다 — [12번 형제](../12-control-flow-and-switch/)의 「`break` 가 루프를 안 끝내는 것」과 같은 성격이다.\
    **LeakSanitizer(ASan)로 실패 경로를 전부 밟아 봐야** 드러난다.

### 이 주제의 네 번째 창 — 어셈블리와 LeakSanitizer

- **컴파일 진단**은 문법만 본다 — 라벨 이름이 맞는지는 모른다.
- **실행 출력**은 성공 경로만 본다 — **실패 경로를 안 밟으면 아무 일도 안 난다.**
- **UBSan** 은 이 주제에서 거의 할 일이 없다(UB 가 둘뿐이다).
- ★★ **네 번째 창 둘** —
  - **어셈블리**(`-O0`\~`-Os` 다섯 벌) — 「`goto` 가 분기를 줄인다」는 통념을 **반증**했다.
  - **LeakSanitizer** — **실패 경로를 단계마다 던져** 「푼 개수 == 잡은 개수」를 기계가 검산하게 한다.\
    (1)에서 **다섯 경로 전부**를 돌리고 진단 0줄을 받은 것이 이 주제에서 가장 강한 근거다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 자원 둘 이상을 잡는 함수 | 층별 라벨 + 역순 해제 | 분기마다 `free` 를 복사 |
| 자원 하나뿐인 함수 | `if (!p) return -1;` 로 끝 | 라벨 하나짜리 `goto` |
| `malloc` 만 쓰는 함수 | 라벨 하나에 몰아도 된다(`free(NULL)` 안전) | 파일·락이 섞였는데 라벨 하나 |
| 자원 포인터 선언 | `T *r = NULL;` | `T *r;`(초기화 없음) |
| 라벨 이름 | `out_buf`(지금까지 잡은 것) | `free_buf`(다음에 할 일) |
| 라벨 뒤 | `out: return rc;`·`out: ;` | `out: int n = 0;`·`out: }` |
| 중첩 루프 탈출 | `goto found;` | 깃발 변수 두 개 |
| 표준 준수 확인 | `-pedantic` 또는 `-pedantic-errors` | `-std=c17` 만 믿기 |
| 실패 경로 검증 | 단계마다 실패시켜 **전수 실행** + ASan | 성공 경로만 돌려 보기 |
| 성능이 걱정될 때 | ★ 걱정하지 않는다(기계어가 같다) | 「`goto` 가 빠르다」로 정당화 |

판단 규칙 두 줄.

- **`goto cleanup` 은 속도가 아니라 「고칠 자리 수」를 판다.** 자원이 하나 늘면 고칠 곳이 **한 곳**이다.
- **실패 경로는 밟아 봐야 존재한다.** 단계마다 실패시켜 돌리지 않으면 **그 코드는 없는 것과 같다.**

## 핵심 문장

- ★★★ **`goto` 판은 중첩 `if` 판보다 분기가 적지 않다.** `-O2` 에서 **명령 39 · 분기 4 · `call` 7** 로 같았고,\
  `-O0` 에서는 **중첩 `if` 쪽이 오히려 적었다**(36 대 45). **비싼 것은** 「**정리 코드를 복사한 판**」이다(명령 45 · `call` 10).
- ★★ **이 패턴이 파는 것은** 「**정리 코드가 소스에 한 번만 적힌다**」는 것이다. 복사판은 해제 호출이 **소스에 6곳** 적혔다.
- ★★ **라벨 이름은** 「**지금까지 잡은 것**」이다. `out_buf` 로 뛰면 **buf 하나만** 푼다.
- ★★ **해제 순서는 획득의 역순**이고, 라벨을 **아래로 갈수록 먼저 풀 것**으로 쌓으면 저절로 그렇게 된다.
- ★★ **`free(NULL)` 은 표준이 보장하고 `fclose(NULL)` 은 아니다.** 실측에서 **SIGSEGV**(run exit=139)로 죽었다 —\
  **그래서 라벨을 하나로 합칠 수 없다.**
- ★ **자원 포인터는 선언 자리에서 `NULL` 로 초기화한다.** `goto` 가 초기화를 **건너뛸 수 있고**,\
  그 값을 읽으면 UB 인데 **gcc `-O0` 은 0건**이다(clang 은 잡는다).
- ★★★ **C17 에서 라벨 뒤에는 「문」이 와야 한다** — 선언도 `}` 도 안 된다. **C23 에서 둘 다 허용**됐고,\
  **`-pedantic` 없이는 gcc 가 0건**이다.
- ★ **VLA 스코프 안으로는 못 뛴다**(컴파일 에러 `exit=1`) — [12번 형제](../12-control-flow-and-switch/)와 같은 결론을 다시 던져 받았다.
- ★ **라벨은 함수 스코프**다. 다른 함수의 라벨은 「**없는 이름**」으로 진단된다.
- ★★ **이 관용구의 진짜 사고는 컴파일러가 못 본다.** 라벨을 잘못 골라 자원이 새는 것은 **경고 0건**이고,\
  **실패 경로를 전수로 밟으며 ASan 을 돌려야** 드러난다.
- ★ **C 에 이 패턴이 남는 이유는 소멸자도 예외도 `defer` 도 `finally` 도 없기 때문**이다.\
  「함수가 끝날 때 자동으로 불리는 코드」라는 개념 자체가 없다.

## 관련 자료

- [`../README.md`](../README.md) — C 문법·API 주제 목록(이 주제는 13번)
- [`12-control-flow-and-switch/`](../12-control-flow-and-switch/) — ★★ **`goto` 자체의 정본.** 그쪽은 「`goto` 가 무엇을 할 수 있나·VLA 스코프 금지」, 여기는 **「그것으로 다중 자원 해제를 어떻게 짜나」**
- [`14-pointers-address-dereference-and-pointer-types/`](../14-pointers-address-dereference-and-pointer-types/) — 자원 포인터를 `NULL` 로 두는 것 · **이중 포인터로 호출자의 포인터를 바꾸는 것**
- [`08-sizeof-alignment-and-offsetof/`](../08-sizeof-alignment-and-offsetof/) — `calloc(n, sizeof *t)` 의 `sizeof` 가 컴파일 시간에 정해지는 것
- 목록의 **37번 주제** (`malloc`/`calloc`/`realloc`/`free`) — ★ **`free(NULL)` 보장과 `realloc` 실패 처리의 정본.** 여기는 **정리 경로의 모양**만
- 목록의 **38번 주제** (소유권 관례를 코드로 표현하기) — 「누가 해제하는가」를 시그니처로 말하는 법
- 목록의 **46번 주제** (`errno` 와 오류 반환 관례) — `rc` 를 어떻게 정하나
- 목록의 **57번 주제** (해제 후 사용·이중 해제) — 이 패턴이 깨졌을 때 생기는 것
- 목록의 **58번 주제** (UB 를 잡는 도구) — LeakSanitizer 로 실패 경로를 검산하는 법

## 용어 풀이

- **관용구(idiom)** — 문법이 아니라 그 언어에서 굳어진 쓰는 방식. 예: C 의 `goto cleanup`.
- **역순 해제(reverse-order release)** — 획득의 거꾸로 푸는 것. 예: 버퍼 → 파일 순서로 잡았으면 파일 → 버퍼로 푼다.
- **라벨(label)** — 문 앞에 붙이는 이름. `out:`·`case 3:` 이 전부 라벨이고 **스코프는 함수 단위**다.
- **흘러내림(fall-through)** — 라벨 뒤 문이 끝나면 **다음 라벨의 문으로 그대로 이어지는 것**. 역순 해제가 성립하는 근거다.
- **RAII** — C++ 에서 「자원 획득은 초기화」. 객체가 스코프를 벗어나면 **소멸자가 자동으로** 푼다. C 에는 없다.
- **`Drop`** — Rust 에서 값이 스코프를 벗어날 때 자동으로 불리는 정리 코드. C 에는 없다.
- **`defer`** — Go 에서 함수가 끝날 때 역순으로 실행할 문을 등록하는 것. C 에는 없다.
- **불확정 값(indeterminate value)** — 초기화되지 않은 객체가 가진 것. **읽으면 UB** 이고 실측에서 네 번 다 달랐다.
- **`-Wpedantic` / `-pedantic-errors`** — 표준이 요구하는 진단을 **내게 하는** / **에러로 만드는** 플래그.
- **`-Wc23-extensions`** — C23 기능을 그 이전 표준으로 쓸 때 clang 이 내는 경고. **`-pedantic` 없이도 켜져 있다.**
- **`-Wunused-label`** — 정의만 하고 쓰지 않은 라벨을 경고. **gcc·clang 둘 다 `-Wall` 소속.**
- **LeakSanitizer** — ASan 에 딸려 오는 누수 검사기. **프로그램이 끝날 때 안 풀린 할당**을 보고한다.
- **`nonnull` 속성** — glibc 헤더가 `fclose` 같은 함수에 붙여 둔 「이 인자는 널일 수 없다」는 표시. **표준이 아니라 구현의 것**이다.

---

## 더 들어가면

- ★ **`__attribute__((cleanup(f)))` 는 GNU 확장**이다. 변수가 스코프를 벗어날 때 `f` 를 부르게 해\
  **C 에서 RAII 를 흉내** 낸다. systemd 가 이것으로 `_cleanup_free_` 매크로를 만든다.\
  ★ **이 문서에서 던져 보지 않았고**, `-pedantic` 이 무엇이라 하는지도 확인하지 않았다. **이식성 축이 달라** 기준 소스(ISO C)로 접지되지 않는다.

- **C23 의 `defer` 제안**(TS 25755 계열)은 표준에 들어가지 않았다.\
  ★ **이 문서는 그 문서를 열어 확인하지 않았다** — 「없다」는 것만 gcc·clang 의 거동으로 간접 확인했다.

- **`setjmp`/`longjmp` 는 함수를 넘는 점프**다. `goto` 가 못 하는 것을 하지만 **정리 코드가 안 돌고**\
  자동 변수의 값이 불확정이 될 수 있다. ★ **이 문서에서 던져 보지 않았다.**

- ★ **실패 경로에서 `rc` 를 어떻게 정할지**는 이 문서가 다루지 않았다. `errno` 를 보존해야 하는 자리가 있고\
  (정리 코드가 `errno` 를 덮어쓴다), 그것은 목록의 **46번 주제**의 몫이다. ★ **`errno` 보존 실험은 하지 않았다.**

- ★ **「Linux 커널이 이 형태를 쓴다」는 이 문서가 확인하지 않았다.** 코드베이스를 열어 세지 않았으므로\
  **전해 들은 것**이고, 근거로 쓰지 않았다.

- **자원이 다섯·여섯으로 늘었을 때** 중첩 `if` 판의 들여쓰기가 어디서 깨지는지는 **재지 않았다.**\
  이 문서는 **자원 셋**에서만 세 판을 비교했다.
