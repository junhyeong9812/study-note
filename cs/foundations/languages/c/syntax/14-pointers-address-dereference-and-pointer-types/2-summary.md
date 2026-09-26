# c/syntax/14 — 포인터: 「**값이 주소인 변수**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — Pointer declarators](https://en.cppreference.com/w/c/language/pointer) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html) · [Clang Diagnostic flags](https://clang.llvm.org/docs/DiagnosticsReference.html)
> **실행 검증** — 이 문서의 모든 출력·경고·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과\
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 작업 디렉터리는 `/tmp/c13`, 소스 파일명은 언제나 `ex.c` 다 — sanitizer 출력에 경로가 박히기 때문이다.\
> ★★ **실행 블록은 `./x 2>&1 | cat` 로 받았다** — sanitizer 는 stderr, `printf` 는 stdout 이라\
> **터미널과 파이프에서 순서가 달라진다.** 섞이는 프로그램에는 `setvbuf(stdout, NULL, _IONBF, 0)` 를 넣어 **순서를 고정**했다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸** — 이 주제는 **주소를 찍는 것이 본문**이라 이 선언이 특히 중요하다.
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | `%p` 가 찍는 **주소값**(ASLR) · 스택 주소 | ★ 주소들 **사이의 차이**(`4`·`8`·`8`) |
> | ASan 의 PID·`BuildId`·모듈 오프셋 | ★ **등식**(`p==&x`·`pp==&p`·`*pp==p`) |
> | — | **`파일:줄:칸`** · 진단 본문 · 플래그 이름 · **종료 코드** · `sizeof` 값 |
>
> **버전** — 포인터의 기본 규칙은 **C89 이후 바뀐 적이 없다.** `nullptr`(C23)은 [목록의 **19번 주제**](../19-void-pointer-null-pointer-and-null/)의 몫이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★ **경계** — 선언을 **읽는 법**(`int *p[10]` 대 `int (*p)[10]`)은 [01번 형제](../01-declaration-syntax-and-reading/)가 정본이다.\
> **주소 공간·스택 프레임·힙**은 [`foundations/memory-management/`](../../../../memory-management/) 와 [`foundations/variables-and-memory/`](../../../../variables-and-memory/) 가 정본이고,\
> 여기는 「**C 문법으로 그것을 어떻게 쓰나**」만 본다. **포인터 산술**은 [15번 형제](../15-pointer-arithmetic-and-indexing/), **배열 감쇠**는 [16번 형제](../16-array-pointer-decay-and-function-parameters/)가 정본이다.
> 선행 — [01번 형제](../01-declaration-syntax-and-reading/).

## 한눈에 — 쉽게 말하면

**포인터는 「사물함 번호를 적은 쪽지」다.**

사물함이 줄지어 있다고 하자. 각 칸에는 **번호**가 있고 안에 **물건**이 들어 있다.\
쪽지에 「**1307**」이라고 적으면, 그 쪽지는 **물건이 아니라 번호**를 담고 있다.

여기서 헷갈리는 것이 딱 둘이다.

- **쪽지에 적힌 것을 고치는 것**(`p = &y`) — 이제 다른 칸을 가리킨다. **원래 칸의 물건은 그대로다.**
- **쪽지가 가리키는 칸의 물건을 고치는 것**(`*p = 99`) — 칸 안이 바뀐다. **쪽지는 그대로다.**

그리고 **쪽지 자체도 어딘가의 칸에 들어 있다.** 그 칸의 번호를 적은 또 다른 쪽지가 **이중 포인터**다.

| 비유 | 실체 | 층 |
|---|---|---|
| 사물함 번호 | 주소 | **표준**(값이 무엇인지는 구현 정의) |
| 번호를 적은 쪽지 | 포인터 변수 | **표준** |
| 「이 칸의 번호를 알려 줘」 | `&x` | **표준** |
| 「이 번호의 칸을 열어 줘」 | `*p` | **표준** |
| 쪽지에 적힌 번호를 고침 | `p = &y` | **표준** |
| 쪽지가 가리키는 칸을 고침 | `*p = 99` | **표준** |
| **쪽지가 든 칸의 번호**를 적은 쪽지 | `int **pp = &p;` | **표준** |
| 번호가 실제로 몇 번인가 | ★ 실행마다 다르다(ASLR) | ★ **구현 정의** |
| 라벨 종류가 다른 쪽지를 끼워 넣음 | `char *cp = &i;`(`int *` 를 대입) | ★ **제약 위반** — 경고 |

```text
   스택의 한 조각 (실측 — 아래 (1)의 출력)

   주소           칸 이름   내용                        (칸 크기)
   ------------   -------   -------------------------   --------
   ...fe80        x         42                          4 바이트
   ...fe84        y         7                           4 바이트
   ...fe88        p         ...fe80  <-- x 의 주소       8 바이트
   ...fe90        pp        ...fe88  <-- p 의 주소       8 바이트

     p  --> x      *p  는 42
     pp --> p      *pp 는 ...fe80 (= p),  **pp 는 42

   ★ 주소값 자체는 실행마다 바뀐다. 바뀌지 않는 것은
     "y 는 x 보다 4 뒤", "p 는 x 보다 8 뒤", "pp 는 p 보다 8 뒤" 라는 차이다.
```

- ★★ **이 주제의 근거는 주소값이 아니라 「차이와 순서」다.** 같은 프로그램을 다섯 번 돌려\
  주소는 전부 달랐고 **차이 셋은 한 번도 안 바뀌었다.**
- ★ **포인터는 「주소」가 아니라 「타입이 붙은 주소」다.** `int *` 와 `char *` 는 **같은 번호를 담아도 다른 물건**이고,\
  그 차이가 드러나는 자리가 [15번 형제](../15-pointer-arithmetic-and-indexing/)의 산술과 [16번 형제](../16-array-pointer-decay-and-function-parameters/)의 감쇠다.

> **역참조(dereference)** — 포인터가 가리키는 자리의 값을 꺼내거나 넣는 것. 기호는 `*`.\
> 예: `p` 가 `x` 를 가리킬 때 `*p = 99;` 는 `x = 99;` 와 같다.

> **주소 연산자(address-of)** — 객체가 놓인 자리의 번호를 내는 것. 기호는 `&`.\
> 예: `&x` 는 「`x` 가 어디 있나」이고 그 타입은 `int *` 다.

> **ASLR(주소 공간 배치 무작위화)** — 프로그램을 돌릴 때마다 스택·힙의 시작 주소를 바꾸는 OS 기능.\
> 예: 같은 바이너리를 두 번 돌리면 `&x` 가 다르게 나온다. **차이는 그대로다.**

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★ **「포인터의 값」과 「포인터가 가리키는 값」을 무엇으로 갈라 보이나** — 주소를 찍어 **차이**로 증명한다.
2. ★★ **함수 안에서 호출자의 포인터를 바꾸려면 무엇이 필요한가** — 안 되는 판과 되는 판을 나란히 놓는다.
3. ★ **타입이 다른 포인터를 섞으면 무엇이 나오나** — 그리고 **어느 플래그가 그것을 말해 주나.**

## 동작 방식

### (1) 포인터 변수의 값 대 가리키는 값 — 주소를 찍어 **차이**로 본다

**언제 쓰나** — `p` 와 `*p` 가 헷갈릴 때. **한 번 찍어 보면 끝난다.**

```text
===== 소스: ex.c (14-a) =====
#include <stdio.h>
#include <stdint.h>

int main(void) {
    int   x  = 42;
    int   y  = 7;
    int  *p  = &x;
    int **pp = &p;

    printf("x   값 = %d          &x  = %p\n", x, (void *)&x);
    printf("y   값 = %d           &y  = %p\n", y, (void *)&y);
    printf("p   값 = %p   &p  = %p\n", (void *)p,  (void *)&p);
    printf("pp  값 = %p   &pp = %p\n", (void *)pp, (void *)&pp);
    printf("*p = %d   *pp = %p   **pp = %d\n", *p, (void *)*pp, **pp);

    printf("\nsizeof : int=%zu  int*=%zu  int**=%zu  char*=%zu\n",
           sizeof x, sizeof p, sizeof pp, sizeof(char *));

    /* ★ 서로 다른 객체의 주소는 빼면 UB 다(15번 주제). 정수로 바꿔 뺀다. */
    uintptr_t ax = (uintptr_t)&x, ay = (uintptr_t)&y;
    uintptr_t ap = (uintptr_t)&p, app = (uintptr_t)&pp;
    printf("\n바이트 차이 (uintptr_t 로 변환해 뺀 것)\n");
    printf("  &y  - &x  = %ld\n", (long)(ay - ax));
    printf("  &p  - &x  = %ld\n", (long)(ap - ax));
    printf("  &pp - &p  = %ld\n", (long)(app - ap));

    printf("\n같은가 : p==&x %d   pp==&p %d   *pp==p %d   **pp==x %d\n",
           p == &x, pp == &p, *pp == p, **pp == x);

    *p = 99;
    printf("\n*p = 99 후 : x = %d   (p 가 가리키는 값을 바꿨다)\n", x);
    p = &y;
    printf("p = &y 후   : x = %d, *p = %d   (p 자신을 바꿨다 — x 는 그대로)\n", x, *p);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, exit=0) =====
x   값 = 42          &x  = 0x7fff416bfe80
y   값 = 7           &y  = 0x7fff416bfe84
p   값 = 0x7fff416bfe80   &p  = 0x7fff416bfe88
pp  값 = 0x7fff416bfe88   &pp = 0x7fff416bfe90
*p = 42   *pp = 0x7fff416bfe80   **pp = 42

sizeof : int=4  int*=8  int**=8  char*=8

바이트 차이 (uintptr_t 로 변환해 뺀 것)
  &y  - &x  = 4
  &p  - &x  = 8
  &pp - &p  = 8

같은가 : p==&x 1   pp==&p 1   *pp==p 1   **pp==x 1

*p = 99 후 : x = 99   (p 가 가리키는 값을 바꿨다)
p = &y 후   : x = 99, *p = 7   (p 자신을 바꿨다 — x 는 그대로)
```

> ★★ **대조할 것은 숫자가 아니라 성질이다.** `0x7fff416bfe80` 은 **ASLR 때문에 실행마다 바뀐다.**\
> 다섯 번 돌려 주소는 전부 달랐고, **차이 셋(`4` · `8` · `8`)은 한 번도 안 바뀌었다.**\
> 근거로 쓸 것은 **차이**와 **`p==&x`·`pp==&p`·`*pp==p`·`**pp==x` 가 전부 1** 이라는 등식이다.

```text
   전 상태                              *p = 99 을 한 뒤
   +----------+----------+             +----------+----------+
   | x    42  |<---+     |             | x    99  |<---+     |   <- 칸 안이 바뀜
   | y     7  |    |     |             | y     7  |    |     |
   | p   [&x] |----+     |             | p   [&x] |----+     |   <- 쪽지는 그대로
   | pp  [&p] |--> p     |             | pp  [&p] |--> p     |
   +----------+----------+             +----------+----------+
```

```text
   그 다음 p = &y 를 한 뒤
   +----------+----------+
   | x    99  |          |   <- ★ x 는 99 인 채 그대로 (되돌아가지 않는다)
   | y     7  |<---+     |
   | p   [&y] |----+     |   <- 쪽지에 적힌 번호가 바뀜
   | pp  [&p] |--> p     |   <- pp 는 여전히 p 를 가리킨다
   +----------+----------+
```

그림 해설 (한 단계씩):

- **`p` 의 값은 `x` 의 주소**이고, **`*p` 의 값은 42** 다. 같은 줄의 두 숫자가 다른 종류라는 것이 전부다.
- **`*p = 99`** 는 **칸 안**을 바꾼다 — `x` 가 99 가 된다. **`p` 는 안 바뀐다.**
- **`p = &y`** 는 **쪽지**를 바꾼다 — `x` 는 **99 인 채 그대로**다. 되돌아가지 않는다.
- **`pp` 는 `p` 가 든 칸을 가리킨다.** `*pp` 가 `p` 와 같고(`*pp==p` 가 1), `**pp` 가 `x` 와 같다.
- ★ **`sizeof` 가 말해 주는 것** — `int*` 도 `int**` 도 `char*` 도 **전부 8** 이다.\
  **포인터의 크기는 가리키는 타입과 무관**하다(이 환경에서). **가리키는 타입이 정하는 것은 크기가 아니라** 「**한 칸이 몇 바이트인가**」이고,\
  그것이 [15번 형제](../15-pointer-arithmetic-and-indexing/)의 주제다.

비용 — 포인터 하나에 8바이트. **간접 참조 한 겹이 늘 때마다 칸을 한 번 더 읽어야 한다.**

### (2) 이중 포인터가 필요한 자리 — **안 되는 판과 되는 판**

**언제 쓰나** — 함수 안에서 **호출자의 포인터 자체**를 바꾸고 싶을 때.

```text
===== 소스: ex.c (14-c) =====
#include <stdio.h>
#include <stdlib.h>

/* 안 되는 판 — 포인터를 값으로 받는다 */
static void alloc_bad(int *p, int n) {
    p = malloc((size_t)n * sizeof *p);      /* 지역 복사본만 바뀐다 */
    if (p) p[0] = 7;
}

/* 되는 판 — 포인터의 주소를 받는다 */
static void alloc_good(int **pp, int n) {
    *pp = malloc((size_t)n * sizeof **pp);  /* 호출자의 포인터 자체를 바꾼다 */
    if (*pp) (*pp)[0] = 7;
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);   /* ★ 출력 순서를 고정한다 — 파이프로 받아도 같게 */
    int *a = NULL;
    alloc_bad(a, 4);
    printf("alloc_bad  후 : a = %s\n", a ? "NULL 아님" : "여전히 NULL");

    int *b = NULL;
    alloc_good(&b, 4);
    printf("alloc_good 후 : b = %s", b ? "NULL 아님" : "여전히 NULL");
    if (b) printf(", b[0] = %d", b[0]);
    printf("\n");
    free(b);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, exit=0) =====
alloc_bad  후 : a = 여전히 NULL
alloc_good 후 : b = NULL 아님, b[0] = 7
```

```text
===== gcc -std=c17 -g -fsanitize=address,undefined · ./x 2>&1 | cat  (run exit=1) =====
alloc_bad  후 : a = 여전히 NULL
alloc_good 후 : b = NULL 아님, b[0] = 7

=================================================================
==3652260==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 16 byte(s) in 1 object(s) allocated from:
    #0 0x706da34fd9c7 in malloc ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:69
    #1 0x5f35a38dc36c in alloc_bad /tmp/c13/ex.c:6
    #2 0x5f35a38dc629 in main /tmp/c13/ex.c:19
    #3 0x706da282a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #4 0x706da282a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #5 0x5f35a38dc284 in _start (/tmp/c13/xs+0x2284) (BuildId: 9bf61f4f15008adc4f4913b627b72974a56e3348)

SUMMARY: AddressSanitizer: 16 byte(s) leaked in 1 allocation(s).
```

> ★ **대조할 것은 숫자가 아니라 성질이다.** PID·주소·`BuildId` 는 실행마다 바뀐다.\
> 근거는 **`16 byte(s) leaked`** · 프레임 **`alloc_bad /tmp/c13/ex.c:6`** · **`run exit=1`** 이다.\
> ★★ **두 `printf` 줄이 리포트보다 앞에 오는 것**은 소스 첫 줄의 `setvbuf(stdout, NULL, _IONBF, 0)` 덕분이다 —\
> **그것이 없으면 파이프로 받을 때 두 줄이 통째로 사라진다**(ASan 이 버퍼를 비우기 전에 프로세스를 끝낸다).\
> 이 문서를 쓰며 실제로 그 일이 났고, **`2>&1 | cat` 로 세 번 받아 같은 순서인 것**을 확인해 고쳤다.

```text
   alloc_bad — 인자는 ★ 복사본이다

   main 의 프레임          alloc_bad 의 프레임        힙
   +-----------+          +-----------+             +--------+
   | a  [NULL] |  --복사-->| p  [NULL] |             |        |
   +-----------+          +-----------+             +--------+
                                |  p = malloc(...)         ^
                                +--------------------------+
                          | p  [힙주소] |   <- ★ 복사본만 바뀐다
                          +-----------+
   함수가 끝나면 p 는 사라진다 -> a 는 여전히 NULL, 힙 16바이트는 ★ 샌다

   alloc_good — 인자가 ★ a 의 주소다

   main 의 프레임          alloc_good 의 프레임       힙
   +-----------+          +-----------+             +--------+
   | b  [NULL] |<---------| pp [&b]   |             |        |
   +-----------+          +-----------+             +--------+
        ^                      |  *pp = malloc(...)       ^
        +----------------------+--------------------------+
   | b  [힙주소] |   <- ★ 호출자의 칸이 바뀐다
```

그림 해설 (한 단계씩):

- ★★ **C 의 인자 전달은 언제나 복사**다. `alloc_bad(a, 4)` 는 **`a` 의 값(널)을 복사해** `p` 에 넣는다.\
  `p` 를 바꿔도 **`a` 가 든 칸은 건드리지 않는다.**
- ★★ **바꾸고 싶은 것이 「`a` 라는 칸」이면 그 칸의 주소를 넘겨야 한다** — `&b` 를 넘기고 `*pp = …` 로 쓴다.\
  「포인터를 바꾸려면 포인터의 포인터」라는 말이 이것이다.
- ★★★ **이 사고는 컴파일러가 잡지 못한다** — **모든 플래그 조합에서 경고 0건**이다.\
  문법이 맞고 동작도 정의되어 있다. `alloc_bad` 는 **자기가 할 일을 하고 조용히 끝난다.**
- ★ **LeakSanitizer 만 말한다** — `16 byte(s) leaked`, 프레임이 `alloc_bad` 를 가리킨다.\
  **이 주제의 네 번째 창이 여기 있다.**
- ★ **`sizeof *p` 와 `sizeof **pp`** 를 보라 — 「가리키는 것의 크기」라 타입을 고쳐도 따라온다.

비용 — 별 하나. **읽기는 나빠지지만 「누가 그 칸의 주인인가」가 시그니처에 드러난다.**

### (3) 타입이 다른 포인터를 대입하면 — **경고이지 에러가 아니다**

**언제 쓰나** — 컴파일은 되는데 실행이 이상할 때. **이 경고를 읽는 것이 전부**다.

```text
===== 소스: ex.c (14-b) =====
#include <stdio.h>

int main(void) {
    int    i = 0x41424344;
    char  *cp;
    int   *ip;
    void  *vp;
    double *dp;

    cp = &i;            /* int*  -> char*   : 경고 */
    ip = &i;            /* 맞다 */
    vp = &i;            /* int*  -> void*   : 조용하다 */
    ip = vp;            /* void* -> int*    : 조용하다 */
    dp = ip;            /* int*  -> double* : 경고 */

    printf("%d %d %d\n", *cp, *ip, (int)*dp);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘main’:
ex.c:10:8: warning: assignment to ‘char *’ from incompatible pointer type ‘int *’ [-Wincompatible-pointer-types]
   10 |     cp = &i;            /* int*  -> char*   : 경고 */
      |        ^
ex.c:14:8: warning: assignment to ‘double *’ from incompatible pointer type ‘int *’ [-Wincompatible-pointer-types]
   14 |     dp = ip;            /* int*  -> double* : 경고 */
      |        ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c:10:8: warning: incompatible pointer types assigning to 'char *' from 'int *' [-Wincompatible-pointer-types]
   10 |     cp = &i;            /* int*  -> char*   : 경고 */
      |        ^ ~~
ex.c:14:8: warning: incompatible pointer types assigning to 'double *' from 'int *' [-Wincompatible-pointer-types]
   14 |     dp = ip;            /* int*  -> double* : 경고 */
      |        ^ ~~
2 warnings generated.
```

```text
===== gcc -std=c17 -pedantic-errors (exit=1) =====
ex.c: In function ‘main’:
ex.c:10:8: error: assignment to ‘char *’ from incompatible pointer type ‘int *’ [-Wincompatible-pointer-types]
   10 |     cp = &i;            /* int*  -> char*   : 경고 */
      |        ^
ex.c:14:8: error: assignment to ‘double *’ from incompatible pointer type ‘int *’ [-Wincompatible-pointer-types]
   14 |     dp = ip;            /* int*  -> double* : 경고 */
      |        ^
```

```text
   i 의 4바이트 :  44 43 42 41   (리틀 엔디언, 0x41424344)
                   ^^
   char *cp = &i  ->  *cp 는 ★ 첫 1바이트만  = 0x44 = 68
   int  *ip = &i  ->  *ip 는 4바이트 전부     = 0x41424344
   double *dp     ->  8바이트를 읽으려 한다   = ★ 4바이트는 i 밖이다
```

그림 해설 (한 단계씩):

- ★★ **경고이지 에러가 아니다.** `exit=0` 이고 **실행 파일이 나온다.**\
  C 에서 이것은 **제약 위반**이라 진단 의무가 있는데, gcc·clang 은 **경고로 내고 계속 간다.**
- **`void *` 는 양방향으로 조용하다.** `int *` → `void *` 도, `void *` → `int *` 도 경고가 없다 —\
  그것이 `void *` 의 존재 이유이고 [목록의 **19번 주제**](../19-void-pointer-null-pointer-and-null/)가 정본이다.
- ★ **`-pedantic-errors` 를 붙이면 `error:` 로 바뀌고 `exit=1`** 이 된다(gcc·clang 둘 다 error 2건).\
  ★ 이 숫자를 처음 잴 때 **셸에서 `$?` 가 명령 치환의 종료 코드를 잡아** `exit=0` 으로 기록했었다.\
  **컴파일러를 파이프·치환 없이 직접 돌려 다시 재니 1** 이었다 — **도구를 믿기 전에 도구가 무엇을 보는지 확인해야 한다.**
- ★★ **실행 자체는 「돌아간다」** — `*cp` 는 첫 1바이트만 읽고, `*dp` 는 `i` 밖 4바이트까지 읽는다.\
  **후자가 UB** 이고, 이 문서는 그 값을 근거로 쓰지 않았다.
- ★ **경고 문구를 읽는 법** — gcc 는 「**assignment to A from incompatible pointer type B**」,\
  clang 은 「**assigning to A from B**」. **순서가 A ← B 로 같다.**

비용 — 캐스트를 끼워 경고를 끄면 **문제가 사라지는 게 아니라 안 보이게** 된다.\
캐스트가 「비트를 바꾸는 것」인지 「해석을 바꾸는 것」인지는 [05번 형제](../05-explicit-casts-and-pointer-conversions/)가 정본이다.

### (4) `%p` 는 `void *` 로 캐스트해야 한다 — **`-pedantic` 만 말한다**

**언제 쓰나** — 주소를 찍을 때. **거의 모두가 그냥 넘긴다.**

```text
===== 소스: ex.c (14-d) =====
#include <stdio.h>

int main(void) {
    int    i = 42;
    int   *ip = &i;
    char   s[] = "hi";
    void (*fp)(void) = 0;

    printf("캐스트 함  : %p\n", (void *)ip);
    printf("캐스트 안 함: %p\n", ip);          /* int * 를 %p 로 */
    printf("char 배열  : %p\n", s);            /* char * 를 %p 로 */
    printf("함수 포인터: %p\n", (void *)fp);   /* 함수 포인터 -> void * */
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘main’:
ex.c:10:28: warning: format ‘%p’ expects argument of type ‘void *’, but argument 2 has type ‘int *’ [-Wformat=]
   10 |     printf("캐스트 안 함: %p\n", ip);          /* int * 를 %p 로 */
      |                           ~^     ~~
      |                            |     |
      |                            |     int *
      |                            void *
      |                           %ls
ex.c:12:33: warning: ISO C forbids conversion of function pointer to object pointer type [-Wpedantic]
   12 |     printf("함수 포인터: %p\n", (void *)fp);   /* 함수 포인터 -> void * */
      |                                 ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c:10:39: warning: format specifies type 'void *' but the argument has type 'int *' [-Wformat-pedantic]
   10 |     printf("캐스트 안 함: %p\n", ip);          /* int * 를 %p 로 */
      |                           ~~     ^~
ex.c:11:35: warning: format specifies type 'void *' but the argument has type 'char *' [-Wformat-pedantic]
   11 |     printf("char 배열  : %p\n", s);            /* char * 를 %p 로 */
      |                          ~~     ^
      |                          %s
2 warnings generated.
```

```text
===== 플래그별 warning: 줄 수 =====
gcc   -std=c17                         0 건
gcc   -std=c17 -Wall                   0 건
gcc   -std=c17 -Wall -Wextra           0 건
gcc   -std=c17 -Wall -Wextra -pedantic 2 건   [-Wformat=] [-Wpedantic]
clang -std=c17 -Wall -Wextra           0 건
clang -std=c17 -Wall -Wextra -pedantic 2 건   [-Wformat-pedantic]
```

```text
===== 실행 (gcc) =====
캐스트 함  : 0x7ffdf513f69c
캐스트 안 함: 0x7ffdf513f69c
char 배열  : 0x7ffdf513f6b5
함수 포인터: (nil)
```

그림 해설 (한 단계씩):

- ★★★ **`-Wall -Wextra` 로는 0건이다.** **`-pedantic` 을 붙여야** 양쪽 컴파일러가 말한다.\
  **「`-std=c17` 로 돌렸다」는 「C17 로 검증했다」가 아니다**가 이 자리에서도 성립한다.
- ★ **gcc 와 clang 이 다른 것을 본다.**\
  gcc 는 **`int *` 만** 잡고 `char *` 는 넘어간다. clang 은 **둘 다** 잡는다.\
  반대로 gcc 는 **함수 포인터를 `void *` 로 캐스트하는 것**을 `-Wpedantic` 으로 잡고 clang 은 조용하다.
- ★ **왜 캐스트가 필요한가** — `printf` 는 가변 인자 함수라 **컴파일러가 인자 타입을 모른다.**\
  `%p` 는 **`void *` 를 꺼내도록** 정해져 있고, 다른 포인터 타입을 넘기면 **UB** 다.
- ★★ **그런데 실행 결과는 같다.** 캐스트한 것과 안 한 것이 **같은 주소를 찍었다.**\
  x86-64 에서 모든 객체 포인터의 **표현이 같기 때문**이고, **이것이 이 함정을 안 보이게 만든다.**\
  「안 터졌다」는 「안전하다」가 아니다.
- **함수 포인터를 `void *` 로 바꾸는 것은 ISO C 가 금지한다** — 그래도 POSIX `dlsym` 이 그것을 요구한다.\
  ★ 이 문서는 `dlsym` 을 던져 보지 않았고, **POSIX 는 축이 다르다.**

비용 — `(void *)` 아홉 글자. **안 쓰면 어느 컴파일러도 기본 설정에서는 말해 주지 않는다.**

### (5) 이 주제의 진단을 한 표로

```text
===== 각 프로그램을 일곱 조합으로 던져 warning: 줄을 센 것 =====
(세는 법 — grep -c 'warning:' 이다. grep -c warning 은 clang 의
 "2 warnings generated." 요약 줄까지 세어 한 건이 더 나온다)
```

| 프로그램 | gcc 무플래그 | gcc `-Wall` | gcc `+Wextra` | gcc `+pedantic` | gcc `-std=c2x +ped` | clang `-Wall -Wextra` | clang `+pedantic` |
|---|---|---|---|---|---|---|---|
| 14-a 주소 덤프 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 14-b 타입 다른 대입 | **2** | 2 | 2 | 2 | 2 | **2** | 2 |
| 14-c 이중 포인터 | **0** | **0** | **0** | **0** | 0 | **0** | **0** |
| 14-d `%p` 캐스트 | 0 | 0 | **0** | **2** | 2 | **0** | **2** |

- ★★ **14-b 는 플래그 없이도 잡힌다** — `-Wincompatible-pointer-types` 는 **기본으로 켜져 있다.**\
  타입이 다른 포인터 대입은 **C 에서 제약 위반**이라 진단 의무가 있기 때문이다.
- ★★★ **14-c 는 어느 조합에서도 0건**이다. **이 주제의 가장 비싼 사고를 컴파일러가 못 본다.**
- ★★ **14-d 는 `-pedantic` 에서만** 나온다. 두 컴파일러가 **잡는 대상이 다르다.**

## 문법 — 형태와 규칙

### 형태 — 다섯 가지 쓰임

```c
int  x = 42;
int *p;             /* 선언 — "*p 가 int 다" 로 읽는다 (01번 형제) */

p  = &x;            /* ① 주소를 얻는다        p 의 값이 x 의 주소가 된다 */
int v = *p;         /* ② 역참조해 읽는다      v = 42 */
*p = 99;            /* ③ 역참조해 쓴다        x = 99 */
p  = NULL;          /* ④ 포인터 자신을 바꾼다  x 는 그대로 */

int **pp = &p;      /* ⑤ 포인터가 든 칸의 주소 */
**pp = 7;           /* 두 겹 벗기면 x 에 닿는다 */
```

### 금지 사례 — 어느 것이 무슨 층인가

```c
/* (가) 타입이 다른 포인터 대입 — ★ 제약 위반. 경고 후 컴파일된다 */
char *cp = &i;                  /* i 는 int */

/* (나) %p 에 void * 아닌 것 — ★ UB. -pedantic 만 말한다 */
printf("%p\n", ip);             /* ip 는 int * */

/* (다) 함수에서 호출자의 포인터를 바꾸려 함 — ★ 경고 0건. 조용히 샌다 */
void f(int *p) { p = malloc(8); }

/* (라) 널 역참조 — ★ UB */
int *q = NULL;  int v = *q;

/* (마) 함수 포인터를 void * 로 — ★ ISO C 금지. gcc 는 -Wpedantic 으로 말한다 */
void *vp = (void *)fp;

/* (바) 초기화하지 않은 포인터를 역참조 — ★ UB */
int *r;  *r = 1;
```

### 규칙 불릿

- **포인터는** 「**타입이 붙은 주소**」다. 타입이 정하는 것은 **크기가 아니라** 「**한 칸이 몇 바이트인가**」다.
- ★ **`sizeof(int *)` 와 `sizeof(char *)` 와 `sizeof(int **)` 가 전부 같다**(이 환경에서 8).
- **`&x` 의 타입은 `int *`**, **`&p` 의 타입은 `int **`** 다. `&` 는 타입에 별을 하나 붙인다.
- **`*p = v` 는 가리키는 칸을 바꾸고, `p = q` 는 포인터 자신을 바꾼다.**
- ★ **인자는 언제나 복사**다. 호출자의 **포인터**를 바꾸려면 **그 포인터의 주소**를 넘겨야 한다.
- **`void *` 는 어느 객체 포인터와도 캐스트 없이 오간다.** 함수 포인터는 **아니다.**
- ★ **`%p` 에는 `(void *)` 캐스트가 필요하다.** 안 하면 UB 이고 **`-pedantic` 만 말해 준다.**
- **주소값 자체는 근거가 못 된다.** ASLR 때문에 실행마다 바뀐다. 근거는 **차이와 등식**이다.

## 어디서 틀리나

### 1. ★★★ 「함수에 포인터를 넘겼으니 함수가 바꾼 게 보이겠지」

- **가리키는 값을 바꾸는 것**(`p[0] = 7`)은 보인다. **포인터 자신을 바꾸는 것**(`p = malloc(…)`)은 안 보인다.
- ★ **경고 0건**이다 — 모든 플래그 조합에서. **LeakSanitizer 만** 말한다.
- 고치는 법은 **별 하나** — `void f(int **pp)` 로 받고 `*pp = …` 로 쓴다.

### 2. ★★ 「주소를 찍어 두면 근거가 된다」

- **아니다.** ASLR 때문에 **실행마다 바뀐다.** 다섯 판을 돌려 주소가 전부 달랐다.
- 근거로 쓸 것은 **차이**(`&y - &x = 4`)와 **등식**(`p == &x` 가 1)이다.
- ★ 그리고 **서로 다른 객체의 주소를 포인터 뺄셈으로 빼면 UB** 다([15번 형제](../15-pointer-arithmetic-and-indexing/)).\
  차이를 재려면 **`uintptr_t` 로 바꿔** 정수 뺄셈을 한다.

### 3. ★ 「`%p` 에 그냥 넘겨도 잘 찍히던데」

- **잘 찍힌다.** x86-64 에서 모든 객체 포인터의 **표현이 같기 때문**이다.
- ★ **`-Wall -Wextra` 로는 0건**이고 **`-pedantic` 에서만** 나온다.
- 「안 터졌다」는 「안전하다」가 아니다 — **표현이 다른 플랫폼에서 깨진다.**

### 4. 「`int *` 를 `char *` 에 넣었는데 컴파일됐으니 괜찮겠지」

- **경고가 났고 exit=0 이었다.** C 에서 이것은 **제약 위반**이지만 gcc·clang 은 **경고로 내고 계속 간다.**
- `-pedantic-errors` 를 붙이면 `error:` 가 된다.
- **캐스트로 경고를 끄면 문제가 사라지는 게 아니라 안 보이게** 된다.

### 5. ★ 「포인터의 크기는 가리키는 타입에 달렸겠지」

- **아니다.** `int *`·`char *`·`int **` 가 **전부 8** 이었다.
- 가리키는 타입이 정하는 것은 **`p + 1` 이 몇 바이트 움직이나**이고, 그것은 [15번 형제](../15-pointer-arithmetic-and-indexing/)의 주제다.

### 6. 「`*pp` 와 `**pp` 가 헷갈린다」

- **별을 하나 벗길 때마다 한 겹 들어간다.** `pp` → `*pp`(= `p`) → `**pp`(= `x`).
- 실측에서 `*pp == p` 와 `**pp == x` 가 **둘 다 1** 이었다 — **그 등식이 정의다.**

### 7. 「선언의 `*` 와 식의 `*` 가 같은 것 아닌가」

- **선언의 `*` 는 타입을 만들고**(`int *p;` = 「`*p` 가 `int` 다」), **식의 `*` 는 값을 꺼낸다.**
- 그래서 `int *p = &x;` 에서 `*p = &x` 가 아니라 `p = &x` 다. 선언을 읽는 법은 [01번 형제](../01-declaration-syntax-and-reading/)가 정본이다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★ **이 주제는 「표준」이 본체이고 UB 칸은 얇다** — [15번 형제](../15-pointer-arithmetic-and-indexing/)에서 **UB 가 폭발**하는데,\
그 UB 들이 전부 **이 주제의 타입 규칙 위에** 서 있다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★ **본체** — `&`/`*` 의 뜻 · 인자가 **복사**인 것 · `p = q` 와 `*p = v` 가 다른 것 · `void *` 와 객체 포인터의 **무손실 왕복** · `&x` 의 타입이 `int *` 인 것 | 출력 대조 · 등식 네 개가 전부 1 · gcc·clang 출력이 같음 | ★★★ **「포인터를 값으로 받아 바꾸는 것」** — 경고 0건, 정의된 동작. **컴파일러가 절대 못 본다** |
| **조건부 표준** | 매크로가 정의될 때만 | ★ `uintptr_t`/`intptr_t` — **`<stdint.h>` 가 정의할 때만** 있다(선택 타입) | `sizeof` 로 8 확인 · 컴파일 통과 | ★ **없는 구현에서 컴파일이 깨지는 것**을 이 환경에서는 볼 수 없다 |
| **구현 정의** | 문서화 의무가 있다 | ★ **포인터의 크기와 표현**(여기서 8바이트) · `NULL` 을 찍은 `(nil)` 이라는 **`printf` 표기** · 모든 객체 포인터의 표현이 같은 것 | `sizeof` 출력 · `%p` 출력 | ★ **표현이 같아서 `%p` 오용이 안 드러난다** |
| **미명시** | 몇 가지 중 하나 | ★ **지역 변수들이 스택에 놓이는 순서**(차이 `4`·`8`·`8` 은 관찰이지 보장이 아니다) | 다섯 판 반복 — 차이는 안 흔들렸다 | ★ **안 흔들렸다고 보장은 아니다** — 최적화·컴파일러가 바뀌면 달라진다 |
| **UB** | 아무 일이나 | ★ `%p` 에 **`void *` 아닌 것**을 넘기기 · **널/초기화 안 된 포인터 역참조** · 타입이 다른 포인터로 읽기(엄격한 앨리어싱 — 목록의 **55번 주제**) | `-pedantic` 진단 | ★★ **`%p` 오용은 실행 결과가 정상이다** — 이 환경에서 표현이 같다 |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | gcc `-Wall -Wextra` | `+pedantic` | clang `-Wall -Wextra` | clang `+pedantic` | 런타임 도구 |
|---|---|---|---|---|---|---|
| 타입 다른 포인터 대입 | 제약 위반 | **2건** | 2건 | **2건** | 2건 | — |
| `%p` 에 `int *` | **UB** | **0건** | **1건** | **0건** | **1건** | ★ 없다(결과가 정상) |
| `%p` 에 `char *` | **UB** | 0건 | **0건**(gcc 못 봄) | 0건 | **1건**(clang만) | ★ 없다 |
| 함수 포인터 → `void *` | ISO 금지 | 0건 | **1건**(gcc만) | 0건 | **0건**(clang 못 봄) | — |
| ★ 포인터를 값으로 받아 바꿈 | 표준 | **0건** | **0건** | **0건** | **0건** | ★★ **LeakSanitizer** |
| 주소값이 실행마다 다름 | 구현 정의 | — | — | — | — | ★ 반복 실행으로만 |

- ★★ **이 표의 결론 세 줄**
  - **가장 비싼 사고(이중 포인터 자리)를 어떤 컴파일러도 못 본다.** 런타임 도구가 유일한 답이다.
  - **`-pedantic` 이 없으면 `%p` 오용이 통째로 안 보인다.** 그리고 **gcc 와 clang 이 잡는 대상이 다르다.**
  - ★ **이 환경에서 표현이 같아 UB 가 정상처럼 보인다** — 「안 터졌다」가 가장 약한 근거인 자리다.

### 이 주제의 네 번째 창 — 주소 덤프와 LeakSanitizer

- **컴파일 진단**은 타입만 본다 — 「포인터를 바꿔도 호출자에 안 보인다」는 **타입이 맞는 코드**다.
- **실행 출력**은 「널이 아니다」까지만 본다 — **샌 메모리는 출력에 안 나온다.**
- **UBSan** 은 이 주제에서 할 일이 적다 — 역참조를 안 하면 UB 가 없다.
- ★★ **네 번째 창 둘** —
  - **`%p` 주소 덤프 + `uintptr_t` 차이** — 「값이 주소다」를 **눈으로** 만든다.\
    ★ **근거는 값이 아니라 차이와 등식**이고, 그래서 ASLR 을 견딘다.
  - **LeakSanitizer** — 「호출자의 포인터가 안 바뀌었다」를 **`16 byte(s) leaked`** 라는 수치로 바꾼다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 호출자의 **값**을 바꾼다 | `void f(int *p) { *p = 7; }` | 값으로 받아 `p = 7` |
| 호출자의 **포인터**를 바꾼다 | `void f(int **pp) { *pp = …; }` | `void f(int *p) { p = …; }` |
| 큰 구조체를 넘긴다 | 포인터로 넘긴다 | 값으로 복사 |
| 안 바꿀 것을 넘긴다 | `const T *` | 그냥 `T *`([31번 주제](../README.md)) |
| 주소를 찍는다 | `printf("%p", (void *)p)` | `printf("%p", p)` |
| 두 주소의 거리를 잰다 | 같은 배열이면 포인터 뺄셈, 아니면 `uintptr_t` | 다른 객체끼리 포인터 뺄셈([15번 형제](../15-pointer-arithmetic-and-indexing/)) |
| 타입 모르는 메모리를 다룬다 | `void *` | `char *` 로 대충 받기 |
| 포인터를 선언만 한다 | `T *p = NULL;` | `T *p;`(불확정 값) |
| 누수를 확인한다 | ASan(LeakSanitizer) | 출력이 정상인 것으로 만족 |
| 표준 준수 확인 | `-pedantic` | `-std=c17` 만 믿기 |

판단 규칙 두 줄.

- **「무엇을 바꾸고 싶은가」를 먼저 말한다** — 칸 안이면 별 하나, 칸 자체면 별 둘.
- **주소는 근거가 아니다. 차이와 등식이 근거다.**

## 핵심 문장

- ★★ **포인터는** 「**값이 주소인 변수**」다. `p` 와 `*p` 는 **같은 줄의 다른 종류 숫자**다.
- ★★ **`*p = 99` 는 가리키는 칸을 바꾸고, `p = &y` 는 쪽지를 바꾼다.** 뒤엣것 뒤에도 **`x` 는 99 인 채**다.
- ★★★ **C 의 인자는 언제나 복사**다. 호출자의 **포인터**를 바꾸려면 **그 포인터의 주소**(`int **`)를 넘겨야 한다.\
  ★ **이 사고에 컴파일러 경고가 0건**이고 **LeakSanitizer 만** 말한다(실측 `16 byte(s) leaked`).
- ★★ **주소값은 근거가 못 된다.** 다섯 판에서 주소는 전부 달랐고 **차이 `4`·`8`·`8` 은 안 바뀌었다.**\
  등식 `p==&x`·`pp==&p`·`*pp==p`·`**pp==x` 가 **전부 1** 인 것이 근거다.
- ★ **포인터의 크기는 가리키는 타입과 무관**하다 — `int*`·`char*`·`int**` 가 **전부 8** 이었다.\
  가리키는 타입이 정하는 것은 **`p + 1` 의 보폭**이고 그것은 [15번 형제](../15-pointer-arithmetic-and-indexing/)의 주제다.
- ★ **타입이 다른 포인터 대입은 경고이지 에러가 아니다.** `-Wincompatible-pointer-types` 는 **플래그 없이도 켜져 있고**,\
  `-pedantic-errors` 에서 `error:` 가 된다.
- ★★★ **`%p` 에는 `(void *)` 캐스트가 필요하다.** 안 하면 UB 인데 **`-Wall -Wextra` 로는 0건**이고\
  **`-pedantic` 에서만** 나온다. ★ **gcc 는 `int *` 만, clang 은 `char *` 까지** 잡는다.
- ★ **`void *` 는 객체 포인터와 캐스트 없이 오간다.** **함수 포인터는 아니고**, ISO C 가 금지한다(gcc `-Wpedantic`).
- ★ **실행 결과가 정상이라는 것이 이 주제에서 가장 약한 근거**다 — x86-64 에서 **모든 객체 포인터의 표현이 같아**\
  `%p` 오용이 **정확한 주소를 찍는다.**

## 관련 자료

- [`../README.md`](../README.md) — C 문법·API 주제 목록(이 주제는 14번)
- [`01-declaration-syntax-and-reading/`](../01-declaration-syntax-and-reading/) — ★★ **선언을 읽는 법의 정본.** `int *p[10]` 대 `int (*p)[10]`·`int **` 대 `int (*)[4]` 는 거기, 여기는 **「그 포인터로 무엇을 하나」**
- [`05-explicit-casts-and-pointer-conversions/`](../05-explicit-casts-and-pointer-conversions/) — 포인터 캐스트가 **비트를 바꾸는가 해석을 바꾸는가**의 정본
- [`08-sizeof-alignment-and-offsetof/`](../08-sizeof-alignment-and-offsetof/) — `sizeof *p` 관용구 · 정렬
- [`13-goto-cleanup-idiom/`](../13-goto-cleanup-idiom/) — 자원 포인터를 `NULL` 로 두는 것이 막는 사고
- [`15-pointer-arithmetic-and-indexing/`](../15-pointer-arithmetic-and-indexing/) — ★★ **`p + 1` 이 타입 크기만큼 움직이는 것**과 포인터 뺄셈의 정본. **이 주제의 타입 위에 선다**
- [`16-array-pointer-decay-and-function-parameters/`](../16-array-pointer-decay-and-function-parameters/) — 배열이 포인터가 되는 자리
- [`../../../memory-management/`](../../../../memory-management/) · [`../../../variables-and-memory/`](../../../../variables-and-memory/) — ★ **주소 공간·스택 프레임·힙 구조의 정본.** 그쪽은 「메모리가 어떻게 생겼나」, 여기는 **「C 문법으로 그것을 어떻게 가리키나」**
- [목록의 **19번 주제**](../19-void-pointer-null-pointer-and-null/) (`void *`·널 포인터·`NULL`) — `void *` 가 왜 캐스트 없이 오가나 · `NULL` 대 `nullptr`
- [목록의 **28번 주제**](../28-choosing-among-four-storage-durations/) (저장 기간 4종) — 가리키는 대상이 **언제 사라지나**
- [목록의 **31번 주제**](../31-const-and-pointer-const-placement/) (`const` 와 포인터 const 위치) — 「바꾸지 않겠다」를 타입으로 말하는 법
- [목록의 **35번 주제**](../35-function-pointers-and-callback-tables/) (함수 포인터) — 함수 포인터가 객체 포인터와 다른 이유
- 목록의 **55번 주제** (엄격한 앨리어싱) — 타입이 다른 포인터로 **읽는 것**이 왜 UB 인가
- 목록의 **57번 주제** (해제 후 사용·댕글링) — 가리키는 대상이 사라진 뒤의 포인터

## 용어 풀이

- **포인터(pointer)** — 값이 주소인 변수. 예: `int *p = &x;` 의 `p` 는 `x` 가 놓인 칸 번호를 담는다.
- **역참조(dereference)** — 가리키는 자리의 값을 꺼내거나 넣는 것. 기호는 `*`. 예: `*p = 99;` 는 `x` 를 99 로 만든다.
- **주소 연산자(address-of)** — 객체가 놓인 자리의 번호를 내는 것. 기호는 `&`. 예: `&x` 의 타입은 `int *`.
- **이중 포인터(pointer to pointer)** — 포인터가 든 칸을 가리키는 포인터. 예: `int **pp = &p;`.
- **불완전한 대응 — 제약 위반(constraint violation)** — 표준이 「진단을 내야 한다」고 요구하는 위반.\
  예: `char *cp = &i;`(i 는 int). **에러일 필요는 없어서** gcc·clang 은 경고로 낸다.
- **ASLR** — 실행마다 스택·힙 시작 주소를 바꾸는 OS 기능. 예: 같은 바이너리를 두 번 돌리면 `&x` 가 다르다.
- **`uintptr_t`** — 포인터를 담을 수 있는 부호 없는 정수 타입(`<stdint.h>`). ★ **선택 타입이라 없을 수도 있다.**
- **`void *`** — 「타입을 모르는 객체를 가리키는 포인터」. **객체 포인터와 캐스트 없이 오간다.**
- **LeakSanitizer** — ASan 에 딸려 오는 누수 검사기. 프로그램이 끝날 때 **안 풀린 할당**을 보고한다.
- **`-Wincompatible-pointer-types`** — 타입이 다른 포인터 대입을 경고. **gcc·clang 둘 다 기본으로 켜져 있다.**
- **`-Wformat=` / `-Wformat-pedantic`** — 서식 문자열과 인자 타입이 안 맞는 것을 경고. ★ **`%p` 는 `-pedantic` 에서만.**

---

## 더 들어가면

- ★ **함수 포인터는 객체 포인터와 다른 세계다.** ISO C 는 둘 사이 변환을 보장하지 않고, gcc 가 `-Wpedantic` 으로 말한다.\
  그런데 POSIX `dlsym` 은 `void *` 를 돌려주므로 **캐스트가 불가피하다.**\
  ★ **이 문서는 `dlsym` 을 던져 보지 않았고**, POSIX 는 축이 달라 이 목록 밖이다([목록의 **35번 주제**](../35-function-pointers-and-callback-tables/) 참고).

- **`intptr_t`/`uintptr_t` 는 선택 타입**이다. 이 환경에는 있고 8바이트였지만\
  ★ **없는 구현에서 무슨 일이 나는지는 확인할 수 없었다** — 이 머신에 그런 구현이 없다.

- ★ **널 포인터 상수의 표기가 셋**이다 — `NULL`·`0`·C23 의 `nullptr`.\
  ★ **이 문서는 `nullptr` 을 던져 보지 않았다.** [목록의 **19번 주제**](../19-void-pointer-null-pointer-and-null/)의 몫이다.

- **「널 포인터의 비트 표현이 전부 0 인가」는 구현 정의**다. 이 환경에서 `%p` 가 `(nil)` 을 찍었지만\
  ★ **비트를 직접 들여다보지 않았다.** `memset(&p, 0, sizeof p)` 가 `p == NULL` 을 만드는지도 **던지지 않았다.**

- ★ **엄격한 앨리어싱** — 타입이 다른 포인터로 **같은 메모리를 읽는 것**은 대입 경고와 별개의 UB 다.\
  이 문서의 14-b 는 **대입까지만** 보였고 `*dp` 의 값은 근거로 쓰지 않았다. 목록의 **55번 주제**의 몫이다.

- ★ **지역 변수의 스택 배치 순서**(차이 `4`·`8`·`8`)는 **관찰이지 보장이 아니다.**\
  최적화 수준을 바꿔 가며 확인하지는 않았고, `-O0` 한 벌에서 다섯 판을 돌린 것이 전부다.
