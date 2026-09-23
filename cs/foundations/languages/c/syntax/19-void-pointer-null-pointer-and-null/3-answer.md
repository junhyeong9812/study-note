# c/syntax/19 — `void *`·널 포인터·`NULL`: 「**타입을 잠시 벗는 포인터와, 어디도 안 가리키는 값**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고·어셈블리·sanitizer 진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 작업 디렉터리는 `/tmp/c17b/19`, 소스는 `ex.c`·`ex2.c`… 로 고정했다.\
> ★ 널 역참조 프로그램에는 `setvbuf(stdout, NULL, _IONBF, 0)` 를 넣었다 —\
> **죽는 프로그램의 표준 출력은 flush 되지 않으면 통째로 사라지기 때문**이다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | clang `-O2` 가 찍은 **쓰레기 값**(세 판이 전부 다르다) | ★★★ **「clang `-O2` 에서는 안 죽는다」는 판정** |
> | ASan 의 주소·`pc`/`bp`/`sp` · PID · `BuildId` | **종료 코드** — `0` · `1` · `139` |
> | — | `_Generic` 의 타입 이름 · `NULL` 의 전처리 결과 문자열 · 진단 본문 · 플래그 이름 · 어셈블리 명령 |
>
> ★★ **널 실험에서 근거는 「값」이 아니라 「판정」이다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `void *` 로 갔다 되돌아오면 — **캐스트가 0번, 경고도 0건** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex.c -o x ; ./x (cc exit=0 · run exit=0) =====
(가) int* double* struct* -> void* : 캐스트 한 번도 안 썼다
(나) void* -> int* double* struct* : *pi = 7 · *pd = 2.5 · pp->x = 1
(다) (void*)&i == &i 인가 : 같다
(라) malloc/memset : 0 42 0
(마) sizeof(void *) = 8 · sizeof(int *) = 8 · sizeof(char *) = 8
```

```c
/* ex.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct P { int x, y; };

int main(void) {
    int i = 7;
    double d = 2.5;
    struct P p = {1, 2};

    /* (가) 객체 포인터 -> void * : 캐스트 없이 간다 */
    void *v1 = &i;
    void *v2 = &d;
    void *v3 = &p;
    printf("(가) int* double* struct* -> void* : 캐스트 한 번도 안 썼다\n");

    /* (나) void * -> 객체 포인터 : 이쪽도 캐스트 없이 온다 */
    int *pi = v1;
    double *pd = v2;
    struct P *pp = v3;
    printf("(나) void* -> int* double* struct* : *pi = %d · *pd = %.1f · pp->x = %d\n",
           *pi, *pd, pp->x);

    /* (다) 주소값은 그대로다 — 변환이 비트를 바꾸지 않는다 */
    printf("(다) (void*)&i == &i 인가 : %s\n", (void *)&i == v1 ? "같다" : "다르다");

    /* (라) 표준 라이브러리가 void * 로 오가는 자리 */
    int *arr = malloc(3 * sizeof *arr);     /* malloc 은 void * 를 준다 */
    if (!arr) return 1;
    memset(arr, 0, 3 * sizeof *arr);        /* memset 은 void * 를 받는다 */
    arr[1] = 42;
    printf("(라) malloc/memset : %d %d %d\n", arr[0], arr[1], arr[2]);
    free(arr);

    /* (마) 다른 객체 포인터끼리는 캐스트 없이 못 간다 — void * 만 특별하다 */
    printf("(마) sizeof(void *) = %zu · sizeof(int *) = %zu · sizeof(char *) = %zu\n",
           sizeof(void *), sizeof(int *), sizeof(char *));
    return 0;
}
```

**왜 그런가**

```text
   int *      ──┐                    ┌──> int *
   double *   ──┼──> void * ─────────┼──> double *
   struct P * ──┘                    └──> struct P *

   ★ 화살표 어디에도 (T *) 를 적을 자리가 없다
```

- **캐스트는 한 번도 안 쓴다.** 객체 포인터 → `void *` 도, `void *` → 객체 포인터도 **양방향으로 조용하다.**\
  ★ **이 양방향성이 `void *` 의 정의 그 자체**다. 다른 포인터 쌍은 이러지 않는다 —\
  `int *` 를 `double *` 에 넣으면 진단이 난다([14번 형제](../14-pointers-address-dereference-and-pointer-types/)가 정본).
- **`(void *)&i == v1` 은 「같다」** 다. **변환이 비트를 바꾸지 않는다** — 왕복하면 원래 주소다.
- **`arr[0] arr[1] arr[2]` 는 `0 42 0`** 이다. `malloc`(주는 쪽)과 `memset`(받는 쪽)이 **둘 다 `void *`** 인데\
  그 사이를 캐스트 없이 오간 메모리가 멀쩡하다.\
  ★ **그래서 C 에서는 `malloc` 의 반환에 캐스트를 안 붙인다.**
- **세 `sizeof` 는 전부 8** 이다. ★★ **그런데 이것은 표준이 정한 것이 아니라 구현 정의**다.\
  표준 쪽 사실은 「**왕복하면 같다**」이지 「크기가 같다」가 아니다.\
  ★ **같은 출력에서 두 층을 갈라 읽는 연습**이 이 문항의 요점이다.
- **경고는 0건**이다(`-pedantic` 포함). **합법이라 진단이 없는 것이 정상**이다.

### 2. 함수 포인터를 `void *` 에 넣으면 — **되는데 표준 밖이고, `-pedantic` 만 말한다** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex2.c -o x2 ; ./x2 (cc exit=0 · run exit=0) =====
객체 포인터 -> void* : 간다
함수 포인터 -> void* -> 함수 포인터 : back(21) = 42
fp1 == fp2 : 같다
```

```c
/* ex2.c */
#include <stdio.h>

static int twice(int n) { return 2 * n; }

int main(void) {
    int i = 7;
    void *ok = &i;              /* 객체 포인터는 조용하다 */
    printf("객체 포인터 -> void* : %s\n", ok == &i ? "간다" : "?");

    void *fp1 = twice;          /* (가) 함수 -> void * : 캐스트 없이 */
    void *fp2 = (void *)twice;  /* (나) 명시 캐스트를 붙여도 */
    int (*back)(int) = fp2;     /* (다) void * -> 함수 포인터 */
    printf("함수 포인터 -> void* -> 함수 포인터 : back(21) = %d\n", back(21));
    printf("fp1 == fp2 : %s\n", fp1 == fp2 ? "같다" : "다르다");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex2.c -o x2 (cc exit=0) =====
ex2.c: In function ‘main’:
ex2.c:10:17: warning: ISO C forbids initialization between function pointer and ‘void *’ [-Wpedantic]
   10 |     void *fp1 = twice;          /* (가) 함수 -> void * : 캐스트 없이 */
      |                 ^~~~~
ex2.c:11:17: warning: ISO C forbids conversion of function pointer to object pointer type [-Wpedantic]
   11 |     void *fp2 = (void *)twice;  /* (나) 명시 캐스트를 붙여도 */
      |                 ^
ex2.c:12:24: warning: ISO C forbids initialization between function pointer and ‘void *’ [-Wpedantic]
   12 |     int (*back)(int) = fp2;     /* (다) void * -> 함수 포인터 */
      |                        ^~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic ex2.c -o /dev/null (cc exit=0) =====
ex2.c:10:11: warning: initializing 'void *' with an expression of type 'int (int)' converts between void pointer and function pointer [-Wpedantic]
   10 |     void *fp1 = twice;          /* (가) 함수 -> void * : 캐스트 없이 */
      |           ^     ~~~~~
ex2.c:12:11: warning: initializing 'int (*)(int)' with an expression of type 'void *' converts between void pointer and function pointer [-Wpedantic]
   12 |     int (*back)(int) = fp2;     /* (다) void * -> 함수 포인터 */
      |           ^            ~~~
2 warnings generated.
```

```text
===== gcc -std=c17 -Wall -Wextra ex2.c -o /dev/null (cc exit=0) =====
```

**왜 그런가**

```text
   객체의 세계                         함수의 세계
   int * / double * / struct P *       int (*)(int)
            \                              |
            void *  <----- ? -------------+
        ★ 규정이 있는 왕복              ★ 규정이 없는 왕복

   -pedantic 있음 :  gcc 3 건        clang 2 건
   -pedantic 없음 :  gcc ★ 0 건      clang ★ 0 건
   실행           :  back(21) = 42 · fp1 == fp2 "같다" · run exit=0
```

- ★★★ **컴파일도 되고 실행도 된다.** `back(21)` 이 **42**, `fp1 == fp2` 가 「같다」다.\
  ★ **「돌아갔다」가 아무것도 증명하지 못하는 전형**이다.
- ★★★ **gcc 3건 대 clang 2건**이고 **갈리는 곳이 정확히 한 줄**이다 —\
  **명시 캐스트를 붙인 `(void *)twice` 줄**에서 **gcc 는 그래도 말하고 clang 은 봐준다.**\
  ★ **「캐스트를 붙였으니 괜찮다」가 컴파일러 의견**이라는 뜻이다. **캐스트는 표준 밖을 안으로 못 옮긴다.**
- ★★ **`-pedantic` 을 빼면 둘 다 0건**이다. `-Wall -Wextra` 로는 **아무 말도 안 해 준다.**\
  ★ [16번 형제](../16-array-pointer-decay-and-function-parameters/)와 **정반대**다 — 그쪽 경고는 플래그 없이도 켜져 있었다.
- **에러가 아니라 경고**다(`cc exit=0`). **실행 파일이 나온다.**
- ★ **문구가 두 가지를 말한다** — gcc 는 「ISO C 가 금지한다」고 **표준을 근거로**,\
  clang 은 「`void` 포인터와 함수 포인터 사이를 변환한다」고 **무엇이 일어나는지**를 말한다.
- ★ **이 변환이 꼭 필요한 자리는 POSIX `dlsym`** 이다 — **이 문서는 던지지 않았다**(목록의 **35번 주제**).

### 3. `void *` 에 `+1` 을 하면 — **1바이트. 표준에는 그 연산이 없다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex3.c -o x3 ; ./x3 (cc exit=0 · run exit=0) =====
sizeof(void) = 1   (표준에는 없다 — gcc 확장이 1 로 친다)
v      = a 의 첫 바이트
v+1 - v      = 1 바이트
c+1 - c      = 1 바이트
w++ 뒤 w - v = 1 바이트
v 로 4바이트 뒤를 읽으면 : 20
```

```c
/* ex3.c */
#include <stdio.h>

int main(void) {
    int a[4] = {10, 20, 30, 40};
    void *v = a;
    char *c = (char *)a;

    printf("sizeof(void) = %zu   (표준에는 없다 — gcc 확장이 1 로 친다)\n", sizeof(void));
    printf("v      = %s\n", "a 의 첫 바이트");
    printf("v+1 - v      = %td 바이트\n", (char *)(v + 1) - (char *)v);
    printf("c+1 - c      = %td 바이트\n", (c + 1) - c);
    void *w = v;
    w++;                                   /* void * 증가 */
    printf("w++ 뒤 w - v = %td 바이트\n", (char *)w - (char *)v);
    printf("v 로 4바이트 뒤를 읽으면 : %d\n", *(int *)((char *)v + 4));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex3.c -o x3 (cc exit=0) =====
ex3.c: In function ‘main’:
ex3.c:8:84: warning: invalid application of ‘sizeof’ to a void type [-Wpointer-arith]
    8 |     printf("sizeof(void) = %zu   (표준에는 없다 — gcc 확장이 1 로 친다)\n", sizeof(void));
      |                                                                                    ^~~~
ex3.c:10:54: warning: pointer of type ‘void *’ used in arithmetic [-Wpointer-arith]
   10 |     printf("v+1 - v      = %td 바이트\n", (char *)(v + 1) - (char *)v);
      |                                                      ^
ex3.c:13:6: warning: wrong type argument to increment [-Wpointer-arith]
   13 |     w++;                                   /* void * 증가 */
      |      ^~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic ex3.c -o /dev/null (cc exit=0) =====
ex3.c:8:91: warning: invalid application of 'sizeof' to a void type [-Wpointer-arith]
    8 |     printf("sizeof(void) = %zu   (표준에는 없다 — gcc 확장이 1 로 친다)\n", sizeof(void));
      |                                                                             ^     ~~~~~~
ex3.c:10:57: warning: arithmetic on a pointer to void is a GNU extension [-Wgnu-pointer-arith]
   10 |     printf("v+1 - v      = %td 바이트\n", (char *)(v + 1) - (char *)v);
      |                                                    ~ ^
ex3.c:13:6: warning: arithmetic on a pointer to void is a GNU extension [-Wgnu-pointer-arith]
   13 |     w++;                                   /* void * 증가 */
      |     ~^
3 warnings generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -Werror=pointer-arith ex3.c -o /dev/null (cc exit=1) =====
ex3.c: In function ‘main’:
ex3.c:8:84: error: invalid application of ‘sizeof’ to a void type [-Werror=pointer-arith]
    8 |     printf("sizeof(void) = %zu   (표준에는 없다 — gcc 확장이 1 로 친다)\n", sizeof(void));
      |                                                                                    ^~~~
ex3.c:10:54: error: pointer of type ‘void *’ used in arithmetic [-Werror=pointer-arith]
   10 |     printf("v+1 - v      = %td 바이트\n", (char *)(v + 1) - (char *)v);
      |                                                      ^
ex3.c:13:6: error: wrong type argument to increment [-Werror=pointer-arith]
   13 |     w++;                                   /* void * 증가 */
      |      ^~
cc1: some warnings being treated as errors
```

```text
===== gcc -std=c17 -Wall -Wextra ex3.c -o /dev/null (cc exit=0) =====
```

**왜 그런가**

```text
   포인터 +1 은 "한 칸" 이다. void * 의 한 칸은?

   int *   한 칸 = 4     규정 있음
   char *  한 칸 = 1     규정 있음
   void *  한 칸 = ???   ★ void 에는 크기가 없다

   gcc·clang : "1 로 친다" (GNU 확장)        표준 : "그런 연산은 없다"

   잡히는 자리 셋 :  sizeof(void)  ·  v + 1  ·  w++
   플래그 이름    :  gcc 셋 다 -Wpointer-arith
                    clang 은 sizeof(void) 만 -Wpointer-arith,
                             산술 둘은 ★ -Wgnu-pointer-arith
```

- **`sizeof(void)` 가 1** 이고 `v + 1` 도 `w++` 도 **1바이트** 움직였다. **`char *` 와 똑같이 굴렀다.**\
  ★ **편해 보이는 것이 함정**이다 — 편해서 쓰게 되고 다른 컴파일러에서 깨진다.
- **`c + 1` 과 같다** — 그래서 구분이 안 된다. ★ **출력으로는 표준 안과 밖이 안 갈린다.**
- ★★ **플래그 이름이 갈린다.** clang 이 **`-Wgnu-pointer-arith`** 로 「GNU 확장을 쓰고 있다」고 **이름으로** 말해 준다.\
  ★ **더 정확한 분류**다 — gcc 는 셋을 한 이름으로 묶는다.
- ★★ **`-pedantic` 을 빼면 둘 다 0건**이다. **2번 문항과 같은 모양**이다.
- ★★★ **`-Werror=pointer-arith` 를 붙이면 `cc exit=1`** 이다. **빌드를 깨는 것이 유일하게 확실한 처방**이고,\
  `cc1: some warnings being treated as errors` 라는 줄이 그 승격을 말해 준다.
- **맞는 방법은 `char *` 로 세는 것**이다 — `*(int *)((char *)v + 4)` 가 **20** 을 냈다.

### 4. 네 가지 널 표기를 `_Generic` 에 넣으면 — **타입은 셋으로 갈리고 값은 하나다** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex4.c -o x4 ; ./x4 (cc exit=0 · run exit=0) =====
NULL       의 타입 : void *
0          의 타입 : int
(void *)0  의 타입 : void *
0L         의 타입 : long

셋 다 널 포인터인가 : 널 널 널
셋이 서로 같은가     : 같다 같다

널 포인터의 바이트 : 00 00 00 00 00 00 00 00   (이 구현의 관찰이지 표준의 보장이 아니다)
```

```c
/* ex4.c */
#include <stdio.h>
#include <stddef.h>

#define TYPE(e) _Generic((e),          \
    void *: "void *",                  \
    int:    "int",                     \
    long:   "long",                    \
    char *: "char *",                  \
    default: "그 밖")

int main(void) {
    printf("NULL       의 타입 : %s\n", TYPE(NULL));
    printf("0          의 타입 : %s\n", TYPE(0));
    printf("(void *)0  의 타입 : %s\n", TYPE((void *)0));
    printf("0L         의 타입 : %s\n", TYPE(0L));

    char *cp = NULL;
    char *c0 = 0;
    char *cv = (void *)0;
    printf("\n셋 다 널 포인터인가 : %s %s %s\n",
           cp ? "아니다" : "널", c0 ? "아니다" : "널", cv ? "아니다" : "널");
    printf("셋이 서로 같은가     : %s %s\n",
           cp == c0 ? "같다" : "다르다", c0 == cv ? "같다" : "다르다");

    /* 널 포인터 값의 실제 비트를 본다 — 0 비트라는 보장은 없다(이 구현에서는 0 이다) */
    unsigned char buf[sizeof(char *)];
    __builtin_memcpy(buf, &cp, sizeof cp);
    printf("\n널 포인터의 바이트 : ");
    for (size_t k = 0; k < sizeof buf; k++) printf("%02x ", buf[k]);
    printf("  (이 구현의 관찰이지 표준의 보장이 아니다)\n");
    return 0;
}
```

**왜 그런가**

```text
   쓰는 법 (문법 범주)            타입           만들어진 값
   ------------------------      -----------    ------------
   NULL                          void *     ┐
   0                             int        ├──>  전부 ★ 같은 널 포인터
   (void *)0                     void *     │      cp == c0  "같다"
   0L                            long       ┘      c0 == cv  "같다"

   ★ 넷 다 "널 포인터 상수" 인데 타입은 셋이다
     -> "널 포인터 상수" 는 타입의 이름이 아니라 ★ 쓰는 법의 이름이다
```

- **네 타입은 `void *` · `int` · `void *` · `long`** 이다.\
  ★★ **넷 다 널 포인터 상수인데 타입이 셋으로 갈린다.** 이것이 9번 문항의 근거다.
- **`cp`·`c0`·`cv` 는 셋 다 널이고 서로 같다.** ★ **들어가는 문법은 셋, 나오는 값은 하나.**
- **여덟 바이트는 전부 `00`** 으로 찍혔다.
- ★★★ **그것은 관찰이지 보장이 아니다.** 널 포인터의 **비트 표현은 구현 정의**다.\
  ★ **「전부 0 이더라」와 「전부 0 이다」 사이의 거리**가 이 주제 전체의 축이고, 10번 문항에서 되풀이된다.
- ★ **`_Generic` 은 C11 부터**다 — 이 관찰 자체가 **조건부 표준 칸의 도구**로 얻은 것이다.

### 5. 가변 인자 끝을 세 가지로 적으면 — **셋 다 같고 기계어까지 같았다** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex7.c -o x7 ; ./x7 (cc exit=0 · run exit=0) =====
끝을 0 으로       : 2 개
끝을 NULL 로      : 2 개
끝을 (char*)0 으로: 2 개
```

```c
/* ex7.c */
#include <stdio.h>
#include <stdarg.h>
#include <stddef.h>

static int count_until_null(int first, ...) {
    va_list ap;
    int n = 0;
    va_start(ap, first);
    for (;;) {
        char *s = va_arg(ap, char *);
        if (s == NULL) break;
        n++;
    }
    va_end(ap);
    return n;
}

int main(void) {
    printf("끝을 0 으로       : %d 개\n", count_until_null(0, "a", "b", 0));
    printf("끝을 NULL 로      : %d 개\n", count_until_null(0, "a", "b", NULL));
    printf("끝을 (char*)0 으로: %d 개\n", count_until_null(0, "a", "b", (char *)0));
    return 0;
}
```

인자를 늘려 **끝이 스택으로 밀려나는** 판을 따로 컴파일해 기계어를 대조했다.

```c
/* ex8.c */
#include <stddef.h>

extern int f(int first, ...);

/* 인자가 많아 레지스터를 다 쓰고 스택으로 넘어가는 자리 */
int with_zero(void) { return f(0, "a", "b", "c", "d", "e", "f", "g", 0); }
int with_null(void) { return f(0, "a", "b", "c", "d", "e", "f", "g", (char *)NULL); }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O1 -S -masm=intel ex8.c -o ex8.s (cc exit=0) =====
```

```text
===== sed -n '/^with_zero:/,/^\tret/p;/^with_null:/,/^\tret/p' ex8.s | grep -v '^\s*\.cfi\|^\.LFB' (exit=0) =====
with_zero:
	endbr64
	sub	rsp, 16
	push	0
	lea	rax, .LC5[rip]
	push	rax
	lea	rax, .LC6[rip]
	push	rax
	lea	r9, .LC0[rip]
	lea	r8, .LC1[rip]
	lea	rcx, .LC2[rip]
	lea	rdx, .LC3[rip]
	lea	rsi, .LC4[rip]
	mov	edi, 0
	mov	eax, 0
	call	f@PLT
	add	rsp, 40
	ret
with_null:
	endbr64
	sub	rsp, 16
	push	0
	lea	rax, .LC5[rip]
	push	rax
	lea	rax, .LC6[rip]
	push	rax
	lea	r9, .LC0[rip]
	lea	r8, .LC1[rip]
	lea	rcx, .LC2[rip]
	lea	rdx, .LC3[rip]
	lea	rsi, .LC4[rip]
	mov	edi, 0
	mov	eax, 0
	call	f@PLT
	add	rsp, 40
	ret
```

**왜 그런가**

```text
   고전 사례가 말하는 것
   va_arg(ap, char *) 는 8바이트 슬롯을 꺼내는데
   0 을 그냥 넘기면 int(4바이트)가 간다 -> 위쪽 4바이트가 쓰레기면 널이 아니다

   이 ABI 에서 실제로 일어난 일
   +--------------------------+      +--------------------------+
   | 스택 슬롯은 8바이트 단위   |      | 레지스터는 32비트 쓰기가   |
   | 0 을 밀면 8바이트가 0      |      | 위쪽 32비트를 0 으로 채운다 |
   +--------------------------+      +--------------------------+
        -> 어느 쪽이든 널 포인터와 ★ 같은 비트가 된다
   ★ 어셈블리로 확인한 것은 ★ 스택 슬롯 쪽이다 (레지스터 쪽은 이 문서가 안 찍었다)

   ★★ 그래서 with_zero 와 with_null 의 기계어가 한 글자도 같았다
```

- **세 줄 전부 `2 개`** 다. **깨진 것이 하나도 없다.**
- ★★★ **어셈블리도 한 글자도 같다.** 끝 인자를 스택으로 미는 명령이 **양쪽 다 8바이트짜리 0 밀어 넣기**다.\
  ★ **「`0` 을 넘기면 깨진다」는 이 ABI 에서 재현되지 않았다.** 그대로 적는다.
- ★★★ **그래도 「`0` 을 써도 된다」는 뜻이 아니다.** 이유 셋은 **전부 「여기서 안 깨짐」과 무관**하다.
  - **가변 인자에서 넣은 타입과 꺼내는 타입이 안 맞는 것 자체가 UB** 다.\
    ★ **UB 는 「이번에 잘 돌았다」로 반증되지 않는다. 잘 도는 UB 가 가장 나쁘다.**
  - ★★ **`NULL` 이 정수 `0` 으로 정의된 구현이 가능**하다 — 7번 문항에서 **같은 헤더 안에 그 분기를 본다.**\
    그런 구현에서는 **`NULL` 을 써도 `int` 가 간다.**
  - **슬롯 규칙·포인터 크기가 다른 ABI** 에서는 어긋난다. ★ **이 문서는 다른 ABI 를 던지지 못했다.**
- ★★ **그래서 관례는 `(char *)NULL`** 이다. 캐스트가 하는 일은 **널을 만드는 것이 아니라 타입을 못 박는 것** —\
  ★ **「상수」 문제를 「값」 문제로 바꿔 버리는 것**이 전부다(9번 문항).
- ★ **이 자리는 어셈블리로만 판정됐다** — 출력이 셋 다 같아서 **다른 창으로는 아무것도 못 가른다.**

### 6. 널을 역참조하면 — **여섯 벌 중 둘이 안 죽었다** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -g ex10.c -o x10 ; ./x10 (cc exit=0 · run exit=139) =====
역참조 직전
```

```c
/* ex10.c */
#include <stdio.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    int *p = NULL;
    printf("역참조 직전\n");
    int v = *p;
    printf("읽은 값 = %d\n", v);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -g -fsanitize=undefined ex10.c -o x10u ; ./x10u (cc exit=0 · run exit=139) =====
역참조 직전
ex10.c:7:9: runtime error: load of null pointer of type 'int'
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -g -fsanitize=address ex10.c -o x10a ; ./x10a | sed -n '1,/^SUMMARY/p' (cc exit=0 · run exit=1) =====
역참조 직전
AddressSanitizer:DEADLYSIGNAL
=================================================================
==84827==ERROR: AddressSanitizer: SEGV on unknown address 0x000000000000 (pc 0x5e3c47b1f2e9 bp 0x7ffddbfe42f0 sp 0x7ffddbfe42e0 T0)
==84827==The signal is caused by a READ memory access.
==84827==Hint: address points to the zero page.
    #0 0x5e3c47b1f2e9 in main /tmp/c17b/19/ex10.c:7
    #1 0x70ad4c42a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #2 0x70ad4c42a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #3 0x5e3c47b1f184 in _start (/tmp/c17b/19/x10a+0x1184) (BuildId: 45b6f99b6c68e70ff93b832b9f72ac384e1ff039)

AddressSanitizer can not provide additional info.
SUMMARY: AddressSanitizer: SEGV /tmp/c17b/19/ex10.c:7 in main
```

최적화 수준을 올려 **여섯 벌**을 전부 던졌다.

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O1 -g ex10.c -o x10_O1 ; ./x10_O1 (cc exit=0 · run exit=139) =====
역참조 직전
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -g ex10.c -o x10_O2 ; ./x10_O2 (cc exit=0 · run exit=139) =====
역참조 직전
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 -g ex10.c -o xc_O0 ; ./xc_O0 (cc exit=0 · run exit=139) =====
역참조 직전
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O1 -g ex10.c -o xc_O1 ; ./xc_O1 (cc exit=0 · run exit=0) =====
역참조 직전
읽은 값 = 310400579
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 -g ex10.c -o xc_O2 ; ./xc_O2 (cc exit=0 · run exit=0) =====
역참조 직전
읽은 값 = -153070013
```

```text
===== for i in 1 2 3; do ./xc_O2 2>&1 | tr '\n' ' '; echo "| run exit=${PIPESTATUS[0]}"; done (exit=0) =====
역참조 직전 읽은 값 = 2124437059 | run exit=0
역참조 직전 읽은 값 = -970959293 | run exit=0
역참조 직전 읽은 값 = -733981117 | run exit=0
```

```text
===== clang -std=c17 -O2 -S -masm=intel ex10.c -o - | sed -n '/^main:/,/^\tret/p' | grep -v '^\s*\.cfi\|^# ' (exit=0) =====
main:                                   # @main
	push	rax
	mov	rax, qword ptr [rip + stdout@GOTPCREL]
	mov	rdi, qword ptr [rax]
	xor	esi, esi
	mov	edx, 2
	xor	ecx, ecx
	call	setvbuf@PLT
	lea	rdi, [rip + .Lstr]
	call	puts@PLT
	lea	rdi, [rip + .L.str.1]
	xor	eax, eax
	call	printf@PLT
	xor	eax, eax
	pop	rcx
	ret
```

> ★ **대조할 것은 숫자가 아니라 성질이다.** clang 이 찍은 값은 **`-O2` 세 판이 전부 다르고**\
> **`-O1` 판의 값도 그것들과 또 다르다.** ASan 의 주소·PID·`BuildId` 도 실행마다 바뀐다.\
> 근거는 **종료 코드**(`139` · `0` · `1`)와 **어셈블리에 로드가 없다**는 것이다.

**왜 그런가**

```text
   여섯 벌                출력                        run exit
   gcc   기본     "역참조 직전" 에서 끝             139   (-O 안 줬다)
   gcc   -O1      "역참조 직전" 에서 끝             139
   gcc   -O2      "역참조 직전" 에서 끝             139
   ---------------------------------------------------------------
   clang -O0      "역참조 직전" 에서 끝             139
   clang -O1      ★ 읽은 값까지 찍고 정상 종료         0   <- ★★★ 여기서 갈린다
   clang -O2      ★ 읽은 값까지 찍고 정상 종료         0   <- ★★★

   도구를 켜면 (gcc · 최적화 안 줌)
   UBSan          진단 한 줄을 찍고 ★ 그래도        139   <- 말해 주고도 못 막는다
   ASan           리포트를 찍고                       1   <- 종료 코드가 다르다

   ★ 경계선이 "최적화를 켰나" 가 아니라 ★ 컴파일러 안에 있다
     gcc   : 세 수준 전부 죽는다
     clang : -O0 만 죽고 ★ -O1 부터 안 죽는다
```

```text
   clang -O2 에서 무슨 일이 났나 (어셈블리를 읽은 결과 — -O1 도 같은 판정이다)

   소스가 시킨 것            생성된 코드에 남은 것
   setvbuf(...)              setvbuf 호출
   puts("역참조 직전")        puts 호출
   int v = *p;   널 로드      ★ 없다 — 로드가 통째로 사라졌다
   printf("...%d", v)        printf 호출 — ★ 값을 싣는 명령이 없다

   -> printf 가 "그 자리에 남아 있던 것" 을 찍는다
   -> 그래서 실행마다 값이 다르다
```

- ★★★ **여섯 벌 중 clang `-O1`·`-O2` 둘만 `run exit=0`** 이다.\
  **gcc 는 기본·`-O1`·`-O2` 세 수준 전부 `139`**(= 128 + 11, SIGSEGV)이고 **clang 도 `-O0` 은 139** 다.\
  ★★ **갈림목은 `-O1` 이고, 그것도 clang 에서만** 그렇다 — **gcc 는 `-O2` 에서도 여전히 죽는다.**\
  ★ **「최적화를 켜면 안 죽는다」도 틀린 요약**이다. **컴파일러를 같이 적어야 답이 된다.**\
  ★ **한 벌만 돌리고 「죽는다」고 적었으면 틀린 문서가 됐다.**
- ★★ **어셈블리에 로드가 아예 없다.** UB 이므로 컴파일러는 **그 줄이 실행되지 않는다고 가정할 수 있고**,\
  그 가정 위에서 **읽기를 지웠다.** ★ **최적화가 UB 를 이용하는 것이 눈에 보이는 자리**다.
- ★★★ **그래서 찍히는 값은 아무 뜻이 없다** — `-O2` 세 판이 전부 다른 값이었고 `-O1` 판도 또 달랐다.\
  ★ **근거로 쓸 수 있는 것은 `run exit=0` 이라는 판정뿐**이다.
- ★★ **UBSan 은 말해 주고도 못 막는다** — 진단 한 줄을 찍고 **그대로 139** 다.\
  ★ 멈추게 하려면 `-fno-sanitize-recover=all` 이 필요한데 **이 문서는 던지지 않았다.**
- ★★ **ASan 은 종료 코드가 `1`** 이고, **주소 0 · 읽기 접근 · 영 페이지**라는 정보까지 준다.\
  ★ **같은 사고가 도구에 따라 `139` 와 `1` 로 갈린다** — CI 가 둘을 같이 잡아야 한다.
- ★ **컴파일 진단은 0건**이다. 널이 **바로 위 줄에 있는데도** `-Wall -Wextra -pedantic` 이 침묵했다.
- ★ **왜 죽었나·어떤 실패 계급인가**는 목록의 **56번 주제**가 정본이다.\
  ★★ **여기서 가져갈 것은 「한 줄로 단정할 수 없다」는 것 하나**다.

### 7. `NULL` 은 어디서 오나 — **헤더 안에 정의가 셋 있다** ★★

**출력**

```c
/* nulldef.c */
#include <stddef.h>
NULL
```

```text
===== gcc -std=c17 -E nulldef.c | tail -2 (exit=0) =====
# 2 "nulldef.c" 2
((void *)0)
```

```text
===== clang -std=c17 -E nulldef.c | tail -2 (exit=0) =====
# 2 "nulldef.c" 2
((void*)0)
```

```text
===== g++ -E nulldef.cpp | tail -2 (exit=0) =====
# 2 "nulldef.cpp" 2
__null
```

```text
===== gcc -std=c2x -E nulldef.c | tail -2 (exit=0) =====
# 2 "nulldef.c" 2
((void *)0)
```

```text
===== grep -n '#define NULL' /usr/lib/gcc/x86_64-linux-gnu/13/include/stddef.h (exit=0) =====
401:#define NULL __null
404:#define NULL ((void *)0)
406:#define NULL 0
```

**왜 그런가**

```text
   같은 낱말 NULL 이 무엇으로 펼쳐지나

   gcc  (C)    void 포인터로 캐스트한 0
   clang(C)    같은 뜻인데 ★ 공백 한 칸이 다른 문자열
   g++  (C++)  컴파일러 내장 이름 — ★ 아예 다른 것

   헤더 한 장 안의 #define NULL 이 ★ 셋
        C++ 이면 -> 내장 이름
        C   이면 -> void 포인터로 캐스트한 0
        그 밖    -> 정수 0        <- ★ 5번 문항의 근거가 여기 있다
```

- ★★ **gcc 와 clang 의 문자열이 다르다** — 뜻은 같고 **공백 한 칸이 다르다.**\
  ★ **`NULL` 을 문자열로 비교하는 코드는 이 한 칸에서 깨진다.**
- ★★ **`g++` 는 아예 다른 것**으로 펼친다. **C 와 C++ 의 `NULL` 은 같은 것이 아니다.**\
  C++ 쪽 사정은 이 목록 밖이라 **「다르다」까지만** 적는다.
- ★★★ **헤더 한 장에 `#define NULL` 이 셋**이고, 그중 하나만 살아남는다.\
  ★ **「`NULL` 은 `((void *)0)` 이다」는 이 머신의 C 모드에서 그렇다는 말**이지 규칙이 아니다.\
  ★★ **정수 `0` 으로 정의되는 분기가 실제로 있다** — 5번 문항이 여기에 기대고 있다.
- ★ **`-std=c2x` 로 바꿔도 gcc 의 `NULL` 은 그대로**다. **C23 이 `NULL` 을 바꾼 것이 아니라 `nullptr` 을 더했다.**
- **층은 「구현 정의」** 다. ★★ **그리고 `-E` 로만 보인다** — 컴파일 진단·실행 출력·sanitizer 셋 다 침묵한다.\
  ★ **이것이 이 주제의 네 번째 창**이다.

### 8. C23 `nullptr` — **타입이 다른 새 낱말** ★★

**출력**

```c
/* ex5.c */
#include <stdio.h>
#include <stddef.h>

int main(void) {
    printf("__STDC_VERSION__ = %ldL\n", (long)__STDC_VERSION__);
    printf("NULL     -> %s\n", _Generic(NULL,    void *: "void *", nullptr_t: "nullptr_t", int: "int", default: "그 밖"));
    printf("nullptr  -> %s\n", _Generic(nullptr, void *: "void *", nullptr_t: "nullptr_t", int: "int", default: "그 밖"));
    printf("0        -> %s\n", _Generic(0,       void *: "void *", nullptr_t: "nullptr_t", int: "int", default: "그 밖"));
    char *p = nullptr;
    printf("char *p = nullptr : %s\n", p ? "아니다" : "널");
    printf("nullptr == NULL   : %s\n", nullptr == NULL ? "같다" : "다르다");
    return 0;
}
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic ex5.c -o x5 ; ./x5 (cc exit=0 · run exit=0) =====
__STDC_VERSION__ = 202000L
NULL     -> void *
nullptr  -> nullptr_t
0        -> int
char *p = nullptr : 널
nullptr == NULL   : 같다
```

```text
===== clang -std=c23 -Wall -Wextra -pedantic ex5.c -o x5c ; ./x5c (cc exit=0 · run exit=0) =====
__STDC_VERSION__ = 202311L
NULL     -> void *
nullptr  -> nullptr_t
0        -> int
char *p = nullptr : 널
nullptr == NULL   : 같다
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex5.c -o /dev/null (cc exit=1) =====
ex5.c: In function ‘main’:
ex5.c:7:41: error: ‘nullptr’ undeclared (first use in this function); did you mean ‘nullptr_t’?
    7 |     printf("nullptr  -> %s\n", _Generic(nullptr, void *: "void *", nullptr_t: "nullptr_t", int: "int", default: "그 밖"));
      |                                         ^~~~~~~
      |                                         nullptr_t
ex5.c:7:41: note: each undeclared identifier is reported only once for each function it appears in
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic ex5.c -o /dev/null (cc exit=1) =====
ex5.c:6:68: error: unknown type name 'nullptr_t'
    6 |     printf("NULL     -> %s\n", _Generic(NULL,    void *: "void *", nullptr_t: "nullptr_t", int: "int", default: "그 밖"));
      |                                                                    ^
ex5.c:7:41: error: use of undeclared identifier 'nullptr'
    7 |     printf("nullptr  -> %s\n", _Generic(nullptr, void *: "void *", nullptr_t: "nullptr_t", int: "int", default: "그 밖"));
      |                                         ^
ex5.c:8:68: error: unknown type name 'nullptr_t'
    8 |     printf("0        -> %s\n", _Generic(0,       void *: "void *", nullptr_t: "nullptr_t", int: "int", default: "그 밖"));
      |                                                                    ^
ex5.c:9:15: error: use of undeclared identifier 'nullptr'
    9 |     char *p = nullptr;
      |               ^
ex5.c:11:40: error: use of undeclared identifier 'nullptr'
   11 |     printf("nullptr == NULL   : %s\n", nullptr == NULL ? "같다" : "다르다");
      |                                        ^
5 errors generated.
```

`-std=c17` 에서 gcc 가 「**`nullptr_t` 말인가요?**」라고 되물은 것이 걸려서, 그 이름만 따로 던졌다.

```c
/* nt.c */
#include <stddef.h>
#include <stdio.h>
int main(void){ nullptr_t z; (void)z; printf("%zu\n", sizeof(nullptr_t)); }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic nt.c -o nt ; ./nt (cc exit=0 · run exit=0) =====
8
```

**왜 그런가**

```text
   C23 에서 세 낱말의 타입이 전부 다르다

   0        -> int         정수 상수
   NULL     -> void *      ★ C23 에서도 이 구현에서는 그대로
   nullptr  -> nullptr_t   ★ 포인터도 정수도 아닌 전용 타입

   값으로는          nullptr == NULL  "같다"    char *p = nullptr  -> 널

   -std=c17 로 내리면
   gcc   : 에러 1 개 — 그런데 ★ nullptr_t 는 안다 (되묻는다)
   clang : 에러 5 개 — nullptr 도 nullptr_t 도 모른다
   gcc 로 nullptr_t 만 따로 : -std=c17 -pedantic 에서 ★ 경고 0건 · sizeof = 8
```

- **`__STDC_VERSION__` 은 gcc `-std=c2x` 가 `202000L`, clang `-std=c23` 이 `202311L`** 이다.\
  ★ **`-std=c2x` 는 「C23 으로 컴파일했다」가 아니라 「그 당시 초안으로」라는 뜻**이다.\
  **gcc 13 에는 `-std=c23` 자체가 없다.**
- ★★★ **`NULL` 은 `void *`, `nullptr` 은 `nullptr_t`** 로 **타입이 다르다.**\
  그래서 **`_Generic` 으로 갈라 잡을 수 있다.** ★ **값으로는 같다**(`nullptr == NULL` 이 「같다」).\
  **새 타입을 준 것이지 새 값을 준 것이 아니다.**
- **`-std=c17` 에서는 양쪽 다 `cc exit=1`** 이다. 단 **에러 개수가 1 대 5** 로 크게 갈린다.
- ★★★ **gcc 13 은 `-std=c17 -pedantic` 에서도 `nullptr_t` 라는 이름을 안다.**\
  되물었다는 것이 단서였고, 따로 던져 보니 **선언까지 되고 `sizeof` 가 8** 이며 **경고가 0건**이다.\
  ★★ **「`-std=c17` 로 컴파일했으니 C17 코드다」가 여기서 깨진다.** `-std=` 는 **강제가 아니라 기본값 선택**이고,\
  `-pedantic` 을 붙여도 **이름 하나는 새어 나왔다.**

### 9. 널 포인터 「상수」와 널 포인터 「값」 ★★★

**답**

```text
   널 포인터 "상수" — 문법 범주 (컴파일 시간에 판정된다)
   +--------------------------------------------------+
   |  값이 0 인 정수 상수식            0 · 0L · 0x0    |
   |  그것을 void * 로 캐스트한 것      (void *)0       |
   |  NULL 은 그중 하나로 ★ 펼쳐진다   (구현 정의)      |
   +--------------------------------------------------+
        |  포인터가 와야 하는 자리에 놓이면
        v
   널 포인터 "값" — 실행 시점의 값
   +--------------------------------------------------+
   |  char *p = NULL;   ->  p 의 값이 널              |
   |  char *q = p;      ->  q 도 널  ★ 그런데 p 는 상수가 아니다 |
   |  함수가 돌려준 널   ->  이것도 널 (어떻게 얻었든 같다)       |
   +--------------------------------------------------+

   ★ 구분이 살아나는 자리 = "포인터가 와야 하는 자리" 가 없는 곳
      = 가변 인자 (...) · 상대 타입이 선언돼 있지 않다
```

- **널 포인터 상수는 문법 범주**다. 「**이렇게 쓰면 널 포인터가 된다**」고 정한 **쓰는 법**이고,\
  그 범주에 드는 것은 둘이다 — **값이 0 인 정수 상수식**과 **그것을 `void *` 로 캐스트한 것**.\
  ★ **판정은 컴파일 시간에 난다.**
- **널 포인터 값은 실행 시점의 값**이다. 「어떤 객체도 함수도 안 가리킨다」고 정해진 그 값이고,\
  ★ **어떻게 얻었는지는 안 따진다.**
- ★★ **`char *q = p;` 에서 `p` 는 널 포인터 상수가 아니다.** **값만 널**이다.\
  변수는 상수식이 아니므로 **애초에 그 범주에 못 든다.**
- ★★★ **구분이 살아나는 자리는 가변 인자 자리**다. 왜 하필 거기인가 —\
  **다른 모든 자리에는 「받는 쪽 타입」이 선언돼 있어서** 상수가 **그 타입의 널 포인터로 변환된다.**\
  `char *p = 0;` 도, `f(0)` 에서 `f` 가 `void f(char *)` 면 마찬가지다.\
  ★ **가변 인자에는 받는 쪽 타입이 없다.** 변환해 줄 상대가 없으니 **적은 그대로 간다** — 그래서 `0` 은 `int` 로 간다.
- ★ **`(char *)0` 은 상수가 아니다.** 상수 범주에 드는 캐스트는 **`void *` 로 캐스트한 것**뿐이다.\
  ★ **그래도 값은 널**이고, **가변 인자 자리에서 필요한 것은 바로 그 「값 + 정확한 타입」이다** —\
  ★★ **그래서 관례가 `(char *)NULL` 인 것**이지 「상수를 더 잘 만들려고」가 아니다.
- ★ **4번 문항이 이 구분의 증거**다 — 네 표기가 **전부 상수인데 타입은 셋**이었고, **만든 값은 하나**였다.

### 10. `memset` 으로 0 을 채운 포인터 — **이 구현에서는 참, 보장은 아님** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex9.c -o x9 ; ./x9 (cc exit=0 · run exit=0) =====
(가) memset 0 뒤 n.next == NULL : 참
(나) calloc 뒤 arr[2].next == NULL : 참
(다) NULL 의 바이트 : 0000000000000000 · 0 채움 : 0000000000000000 · memcmp = 0
    -> 이 구현에서는 같다. ★ 표준이 그렇게 정한 것이 아니라 여기서 그랬을 뿐이다.
```

```c
/* ex9.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Node { struct Node *next; int v; };

int main(void) {
    /* (가) memset 으로 0 을 채운다 */
    struct Node n;
    memset(&n, 0, sizeof n);
    printf("(가) memset 0 뒤 n.next == NULL : %s\n", n.next == NULL ? "참" : "거짓");

    /* (나) calloc 이 준 0 바이트 */
    struct Node *arr = calloc(4, sizeof *arr);
    if (!arr) return 1;
    printf("(나) calloc 뒤 arr[2].next == NULL : %s\n", arr[2].next == NULL ? "참" : "거짓");

    /* (다) 널 포인터의 실제 바이트와 0 바이트를 대조한다 */
    struct Node *null_p = NULL;
    unsigned char a[sizeof null_p], b[sizeof null_p];
    memcpy(a, &null_p, sizeof null_p);
    memset(b, 0, sizeof b);
    printf("(다) NULL 의 바이트 : ");
    for (size_t k = 0; k < sizeof a; k++) printf("%02x", a[k]);
    printf(" · 0 채움 : ");
    for (size_t k = 0; k < sizeof b; k++) printf("%02x", b[k]);
    printf(" · memcmp = %d\n", memcmp(a, b, sizeof a));
    printf("    -> 이 구현에서는 같다. ★ 표준이 그렇게 정한 것이 아니라 여기서 그랬을 뿐이다.\n");
    free(arr);
    return 0;
}
```

**왜 그런가**

```text
   ① 바이트가 전부 0 인 표현          ② 널 포인터 값
      memset / calloc 이 만드는 것       NULL 로 만든 것
                  \                     /
                   이 구현에서는 ★ 같았다 (memcmp = 0)
                   표준이 그렇게 정한 것은 ★ 아니다

   보장되는 방향은 하나뿐이다
     p = NULL      ->  p 는 널이다      (보장)
     바이트를 0 으로 ->  널일 것이다     (★ 관찰)
```

- **셋 다 「참」** 이다 — `memset` 뒤에도, `calloc` 뒤에도 `next == NULL` 이고 `memcmp` 가 **0** 이다.
- ★★★ **그래도 보장이 아니다.** 널 포인터의 **비트 표현은 구현 정의**이고,\
  「0 비트로 채운 것이 널 포인터다」라고 정한 곳이 없다.\
  ★ **보장되는 것은 「`NULL` 을 대입하면 널이다」쪽**이고, **반대 방향은 보장이 아니다.**
- ★★ **`calloc` 이 약속하는 것은 「0 으로 채운 바이트」이지** 「**널 포인터 배열**」이 아니다.\
  **부동소수 `0.0` 에 대해서도 같은 이야기**이고 ★ **이 문서는 부동소수는 던지지 않았다.**
- ★ **널로 채우고 싶으면 루프로 `p[i] = NULL`** 을 쓰는 것이 맞다.\
  ★ **현실에서는 거의 모두 `memset`/`calloc` 에 의존**하고 주류 구현에서 성립한다 —\
  ★★ **「성립한다」와 「보장된다」를 가르는 것**이 이 문항의 전부다.
- ★ **이 자리는 여러 번 돌려도 같은 답이 나온다.** **그래서 더 위험하다** — 가정이 조용히 굳는다.\
  **`memset`/`calloc` 의 계약 자체**는 목록의 **50번 주제**가 정본이다.

### 11. 어느 도구가 무엇을 보나 ★★

**답**

| 사실 | 층 | gcc `-Wall -Wextra` | gcc `+pedantic` | clang `-Wall -Wextra` | clang `+pedantic` | 런타임 도구 |
|---|---|---|---|---|---|---|
| `void *` 양방향 변환 | 표준 | 0건 | 0건 | 0건 | 0건 | — (합법) |
| 함수 포인터 → `void *` | **표준 밖** | ★ **0건** | **3건** | ★ **0건** | **2건** | ★★ **없다 — 잘 돈다** |
| ★ 그중 **명시 캐스트** 줄 | **표준 밖** | 0건 | **1건**(gcc만) | 0건 | ★ **0건** | — |
| `void *` 산술·`sizeof(void)` | **표준 밖** | ★ **0건** | **3건** | ★ **0건** | **3건** | — |
| `NULL` 의 실제 정의 | 구현 정의 | 0건 | 0건 | 0건 | 0건 | ★★ **`-E` 뿐** |
| 널 포인터의 비트 표현 | 구현 정의 | 0건 | 0건 | 0건 | 0건 | ★ 직접 찍어 보기 |
| `memset` 0 == 널 가정 | 구현 정의 | 0건 | 0건 | 0건 | 0건 | ★★ **없다** |
| `-std=c17` 의 `nullptr` | 조건부 표준 | — | **`cc exit=1`** | — | **`cc exit=1`** | — |
| ★ `-std=c17` 의 `nullptr_t` **이름** | 조건부 표준 | 0건 | ★ **0건**(안다) | — | **에러**(모른다) | — |
| 가변 인자 끝의 `0` | **UB** | 0건 | 0건 | 0건 | 0건 | ★★★ **없다 — 기계어가 같다** |
| 널 역참조 | **UB** | ★ **0건** | ★ **0건** | 0건 | 0건 | UBSan(139)·ASan(1)·★ clang `-O2` 는 **0** |

- ★★★ **`-pedantic` 이 있어야 보이는 것은 둘** — **함수 포인터 ↔ `void *`** 와 **`void *` 산술·`sizeof(void)`**.\
  ★ **`-Wall -Wextra` 로만 컴파일하면 둘 다 0건**이다. 이 두 블록은 **아무 진단도 안 실린 채 컴파일된다.**
- ★★ **`NULL` 의 실제 정의는 `-E` 로만 보인다.** 컴파일 진단도 실행 출력도 sanitizer 도 **한 글자도 안 알려 준다.**
- ★★★ **널 역참조에 대한 컴파일 진단은 0건**이다. 널이 **바로 위 줄에 있는데도** 그렇다.\
  런타임 도구는 잡지만 **종료 코드가 갈린다** — **UBSan 139 · ASan 1**, 그리고 **clang `-O2` 는 도구 없이 `0`**.
- ★★★ **네 번째 창은 `-E`, 다섯 번째 창은 `-S`** 다.\
  ① `NULL` 의 정체는 **전처리 결과**로만 보이고\
  ② **가변 인자 세 표기가 같다는 것**과 **clang `-O2` 가 로드를 지웠다는 것**은 **어셈블리로만** 보인다.\
  ★ **둘 다 「실행이 정상이라서」 다른 창으로는 아무것도 못 가르는 자리**였다.

### 12. 다섯 층·무게중심과 경계 ★★

**답**

| 층 | 이 주제(19번) | [16번 형제](../16-array-pointer-decay-and-function-parameters/) |
|---|---|---|
| **표준** | ★★ **`void *` ↔ 객체 포인터 양방향 무캐스트와 왕복** · 널 포인터 상수의 정의 · `NULL` 이 상수로 펼쳐진다는 것 · 세 표기의 널이 **서로 같다** | 감쇠 규칙 · 매개변수 재작성 |
| **조건부 표준** | `_Generic`(C11) · **`nullptr`·`nullptr_t`**(C23) | ★ **해당 없음** |
| **구현 정의** | ★ **`NULL` 의 실제 정의** · **널 포인터의 비트 표현** · 포인터 크기 8 | `sizeof(int)`·`sizeof(int *)` |
| **미명시** | ★ **없다** — 이 문서의 실험 중 이 칸에 들어가는 것이 없었다 | 같은 리터럴의 공유 여부(안 던짐) |
| **UB** | ★★ **본체 넷** — 널 역참조 · 가변 인자 타입 불일치 · 함수 포인터 ↔ `void *`(표준 밖) · `void *` 산술(표준 밖) | ★★ **본체** — 길이를 잃은 뒤의 접근 |

- **비어 있는 칸은 「미명시」** 다. ★ **몰래 채우지 않는다** — 던진 실험 중 거기 들어갈 것이 없었다.
- ★★★ **무게중심이 둘로 쪼개져 있다.** [16번 형제](../16-array-pointer-decay-and-function-parameters/)는 **UB 한 칸이 본체**였는데,\
  여기는 **`void *` 쪽이 「표준」**(규칙이 명확하고 진단이 0건이다)이고 **널 쪽이 「구현 정의 + UB」다.**\
  ★ **한 문서 안에 양극단이 같이 산다** — 그래서 **같은 출력에서 「누가 보장하나」를 매번 되물어야 한다.**
- **경계** —
  - **캐스트 문법 일반 · 정수↔포인터 왕복 · 타입 펀닝 · 정렬** — [05번 형제](../05-explicit-casts-and-pointer-conversions/)가 정본이다.\
    ★ 여기는 **캐스트가 필요 없는 쪽**(`void *`)과 **캐스트로도 안 되는 쪽**(함수 포인터)이다.
  - **포인터 기본**(`&`·`*`·포인터 타입·이중 포인터·`%p`) — [14번 형제](../14-pointers-address-dereference-and-pointer-types/)가 정본이다.\
    ★ 그쪽이 남겨 둔 두 가지(**널의 비트 표현**·**`memset` 이 널을 만드나**)를 **여기서 던졌다.**
  - **`memset`/`memcpy`/`calloc` 의 계약** — 목록의 **50번 주제**가 정본이다.\
    ★ 여기는 「**0 바이트와 널 포인터는 다른 개념**」까지다.
  - **널 역참조의 실패 계급**(영 페이지·신호·복구) — 목록의 **56번 주제**가 정본이다.\
    ★ 여기는 「**컴파일러·최적화 수준으로 갈린다**」까지다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 컴파일러·플래그로 돌렸나 |
|---|---|---|
| `void *` 왕복 (19-a) | 캐스트 **0회** · `(void *)&i == v1` **같다** · `malloc`/`memset` 이 `0 42 0` · 세 `sizeof` **8** · 경고 **0건** | gcc `-std=c17 -Wall -Wextra -pedantic` 1벌 + 실행 |
| 함수 포인터 (19-b) | 실행 **성공**(`back(21)`=42 · `fp1 == fp2` 같다) · `-pedantic` 에서 **gcc 3건 · clang 2건** · ★ **명시 캐스트 줄에서 갈림** · **`-pedantic` 빼면 0건** · `cc exit=0` | gcc 2벌(ped·noped) · clang 1벌(ped) + 실행 |
| `void *` 산술 (19-c) | `sizeof(void)`=**1** · `v+1`=**1바이트** · `w++`=**1바이트** · gcc **3건**(`-Wpointer-arith`) · clang **3건**(★ 산술 둘은 `-Wgnu-pointer-arith`) · **`-pedantic` 빼면 0건** · `-Werror=pointer-arith` 에서 **`cc exit=1`** | gcc 3벌 · clang 1벌 + 실행 |
| `NULL` 의 정의 (19-d) | gcc·clang 이 **공백 한 칸 다름** · g++ 는 **아예 다름** · `-std=c2x` 도 **그대로** · 헤더에 `#define NULL` **3개** | gcc `-E` 2벌 · clang `-E` 1벌 · g++ `-E` 1벌 · `grep` 1회 |
| 널 표기의 타입 (19-e) | `NULL`→`void *` · `0`→`int` · `(void *)0`→`void *` · `0L`→`long` · **셋이 서로 같다** · 바이트 **`00`×8** | gcc 1벌 + 실행 |
| `nullptr` (19-f) | `__STDC_VERSION__` **202000L**(gcc c2x)·**202311L**(clang c23) · `nullptr`→**`nullptr_t`** · `nullptr == NULL` **같다** · `-std=c17` 에서 **gcc 에러 1 · clang 에러 5**(`cc exit=1`) · ★ **gcc 는 `-std=c17 -pedantic` 에서 `nullptr_t` 를 경고 0건으로 받고 `sizeof`=8** | gcc 3벌 · clang 2벌 + 실행 3회 |
| 가변 인자 (19-g·19-h) | 세 표기가 **전부 `2 개`** · ★ **`with_zero` 와 `with_null` 의 기계어가 한 글자도 같다** | gcc 1벌 + 실행 · gcc `-O1 -S -masm=intel` 1벌 |
| `memset` 0 (19-i) | `memset`·`calloc` 뒤 `next == NULL` **참** · `memcmp` **0** | gcc 1벌 + 실행 |
| 널 역참조 (19-j) | ★ **여섯 벌** — gcc **기본·`-O1`·`-O2` 전부 139** · clang **`-O0` 139** · ★★ **clang `-O1`·`-O2` `run exit=0`** · `-O2` 바이너리 **3판이 전부 다른 값** · 어셈블리에 **로드 없음** · UBSan **진단 + 139** · ASan **리포트 + 1** · 컴파일 진단 **0건** | gcc 5벌(기본·`-O1`·`-O2`·UBSan·ASan) · clang 4벌(`-O0`·`-O1`·`-O2`·`-S`) · 실행 **3회 반복 1세트** |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3 · glibc)에서만** 그렇다.

- **`NULL` 이 `((void *)0)` 꼴로 펼쳐지는 것** — ★ **구현 정의**다. 같은 헤더에 **분기가 셋** 있다.
- **널 포인터의 여덟 바이트가 전부 `00` 인 것**, **`memset` 0 이 널과 `memcmp` 0 인 것** — ★ **관찰이지 보장이 아니다.**
- **`sizeof(void *)`=8 · `sizeof(nullptr_t)`=8** — 구현 정의다.
- ★★ **가변 인자 끝의 `0`·`NULL`·`(char *)0` 이 같은 기계어를 내는 것** — **이 ABI 의 성질**이다.\
  **표준의 보장이 아니고**, 다른 ABI 는 **던지지 못했다.**
- ★★ **함수 포인터 ↔ `void *` 가 실제로 왕복하는 것** — **이 구현의 확장**이다. **표준 밖**이다.
- **`void *` 산술이 1바이트인 것** — **GNU 확장**이다.
- ★★★ **clang 이 `-O1` 부터 안 죽는 것** — **최적화 구현의 결과**다. **다른 버전에서 달라질 수 있다.**\
  ★ **UB 에는 「이 구현에서는 이렇다」조차 약속이 아니다.**
- **gcc 13 이 `-std=c17` 에서 `nullptr_t` 를 아는 것** — **gcc 의 구현 사정**이다.

**`void *` 의 양방향 변환과 널 포인터 상수의 규칙 자체는 구현 의존이 아니다.**\
캐스트 없이 오가는 것, 왕복이 보존되는 것, 세 표기의 널이 서로 같은 것은 **어느 C 구현에서도 같다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — POSIX **`dlsym`**(목록의 **35번 주제**) · **`-fno-sanitize-recover=all`** ·\
  **`-fno-delete-null-pointer-checks`** · **`-O3`·`-Os`**(양쪽 다) ·\
  `void *` 를 **다른 타입으로 되받기**(엄격한 앨리어싱 — 목록의 **55번 주제**) ·\
  **`realloc`/`free` 에 널 넘기기** · **`qsort` 비교자의 `const void *`**.
- ★★ **못 잰 것 — 「다른 ABI 에서 가변 인자의 `0` 이 깨지는가」.**\
  이 머신이 x86-64 Linux 하나뿐이라 **측정 자체가 성립하지 않는다.**\
  ★ **손으로 유도해 적지 않았다** — 이유만 적고 **결론은 「여기서는 재현되지 않았다」로 닫았다.**
- ★ **못 잰 것 — 「널 포인터의 비트가 0 이 아닌 구현」.** 같은 이유로 던질 대상이 없다.
- ★★ **「clang 이 어느 수준부터 안 죽는가」는 답했다** — **`-O1`** 이다(여섯 벌을 던졌다).\
  ★ 남은 것은 **그 위쪽**이다 — **`-O3`·`-Os`** 에서도 같은지, **gcc 가 `-O3` 에서도 계속 죽는지**는 **안 던졌다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **clang `-O1`·`-O2` 의 널 역참조 결과** — UB 이므로 **버전이 오르면 언제든 달라진다.** 제일 먼저 다시 돌린다.\
  ★ **갈림목이 `-O1` 이라는 것**도 같이 다시 잰다 — **gcc 쪽으로 옮겨갈 수도 있다.**
- **gcc 가 `-std=c23` 을 갖게 됐는지**(지금은 `-std=c2x` 뿐) · **`__STDC_VERSION__` 이 `202311L` 로 올랐는지**.
- **gcc 13 이 `-std=c17` 에서 `nullptr_t` 를 받아 주던 것**이 막혔는지.
- **`NULL` 의 전처리 결과 문자열**(공백 한 칸) — 헤더가 바뀌면 달라진다.
- **함수 포인터 변환과 `void *` 산술이 기본에서 경고로 승격됐는지** — 지금은 **`-pedantic` 이 있어야 0건이 아니다.**
- **`void *` 의 양방향 변환 규칙 자체는 다시 돌릴 필요가 없다** — C89 이후 바뀐 적이 없다.
