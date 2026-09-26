# c/syntax/19 — `void *`·널 포인터·`NULL`: 「**타입을 잠시 벗는 포인터와, 어디도 안 가리키는 값**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — ★ **이 문서는 웹 문서를 열지 않았다.** 규칙의 접지는 둘뿐이다 —\
> ① **실행·전처리·어셈블리 출력**(아래 전부) ② **이 머신의 시스템 헤더**\
> `/usr/lib/gcc/x86_64-linux-gnu/13/include/stddef.h`(`#define NULL` 세 줄을 직접 찍었다).\
> 그래서 이 문서는 **「표준이 이렇게 정한다」를 조항으로 인용하지 않는다** — 층 표의 「표준」 칸은\
> **두 컴파일러가 같고 `-pedantic` 이 침묵한 자리**를 그렇게 부른 것이다.
> **실행 검증** — 이 문서의 모든 출력·경고·어셈블리·sanitizer 진단은\
> **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과 **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 플래그는 `-std=c17 -Wall -Wextra -pedantic`. 작업 디렉터리는 `/tmp/c17b/19`,\
> 소스는 `ex.c`·`ex2.c`… 로 고정했다 — sanitizer 출력에 경로와 줄 번호가 박히기 때문이다.\
> ★ **널 역참조 프로그램에는 `setvbuf(stdout, NULL, _IONBF, 0)` 를 넣었다** — 죽는 프로그램의\
> 표준 출력은 flush 되지 않으면 **통째로 사라진다.**
> ★★ **흔들리는 칸 / 안 흔들리는 칸** — ★ **이 주제는 바로 그 표가 결론이다.**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | clang `-O2` 가 찍은 **쓰레기 값** — 같은 바이너리를 세 번 돌려 세 번 다 달랐다 | ★★★ **「clang `-O2` 에서는 안 죽는다」는 판정** — 세 판 전부 `run exit=0` |
> | ASan 의 주소·`pc`/`bp`/`sp` · PID · `BuildId` | **종료 코드** — `0` · `1` · `139` |
> | — | `_Generic` 이 답한 **타입 이름** · `NULL` 의 **전처리 결과 문자열** |
> | — | 진단 본문 · **플래그 이름** · 어셈블리 명령 · `sizeof` 값 |
>
> ★★ **한 줄로** — **널 실험에서 근거는 「값」이 아니라 「판정」이다.**\
> 「무엇이 찍혔나」는 흔들리고 「죽었나 안 죽었나」는 안 흔들린다.
> **버전** — `void *` 와 널 포인터 상수는 **C89 부터** 같다. `_Generic` 은 **C11**,\
> `nullptr`·`nullptr_t` 는 **C23** 이다. ★ **gcc 13 에는 `-std=c23` 이 없어 `-std=c2x` 로 던졌다.**
> 이 본문은 Claude 작성이다(원고 없음).
> ★★ **경계** — **캐스트 문법 일반·정수↔포인터 왕복·타입 펀닝**은\
> [05번 형제](../05-explicit-casts-and-pointer-conversions/)가 정본이고, 여기는 **캐스트가 필요 없는 쪽**만 본다.\
> **포인터의 기본**(`&`·`*`·포인터 타입·이중 포인터)은 [14번 형제](../14-pointers-address-dereference-and-pointer-types/)가 정본이다 —\
> 겹치는 것은 링크하고 **결론만** 되짚는다.\
> **`memset`/`memcpy`/`calloc` 의 계약**은 목록의 **50번 주제**,\
> **널 역참조가 어떤 실패 계급인가**는 목록의 **56번 주제**가 정본이다.\
> ★ 여기는 「**`void *` 가 왜 캐스트 없이 오가나**」와 「**널을 어떻게 쓰고 어디서 깨지나**」까지다.
> 선행 — [14번 형제](../14-pointers-address-dereference-and-pointer-types/) · [05번 형제](../05-explicit-casts-and-pointer-conversions/).

## 한눈에 — 쉽게 말하면

**`void *` 는 「품목을 안 적은 보관표」이고, 널 포인터는 「해당 없음이라고 찍힌 표」다.**

물품 보관소를 생각하자.\
보통 표에는 **칸 번호와 품목**이 같이 적혀 있다 — 「3번 칸, 우산」(`int *`·`double *`).\
그런데 **품목 칸을 비운 표**가 하나 있다. 「3번 칸」만 적힌 표다.\
이 표는 **어느 품목 표와도 서로 바꿔 쓸 수 있다.** 칸 번호가 그대로니까.\
★ 바꿔 쓸 때 **창구에 서명할 필요가 없다** — 그게 `void *` 가 특별한 이유다.

그런데 **보관소 밖의 것**은 이 체계에 안 들어온다.\
공연장 좌석표(함수 포인터)를 보관소 표로 바꿔 달라고 하면, **이 창구는 해 주기는 하는데 규정에는 없다.**

그리고 표 중에 **「해당 없음」이라고 찍힌 것**이 있다 — 널 포인터다.\
그 표를 들고 물건을 찾으러 가면(역참조) **무슨 일이 날지는 규정에 안 적혀 있다.**\
★★ 실제로 **창구마다 다른 일이 났다** — 어떤 창구는 바로 쫓아내고, 어떤 창구는 **아무 일도 없었던 척**했다.

| 비유 | 실체 | 층 |
|---|---|---|
| 품목을 안 적은 보관표 | `void *` | **표준** |
| 품목까지 적은 표 | `int *`·`double *`·`struct P *` | **표준** |
| 두 표를 **서명 없이** 바꿔 쓴다 | 객체 포인터 ↔ `void *` — 캐스트가 필요 없다 | **표준** |
| 바꿔도 **칸 번호가 그대로** | 주소값이 보존된다(왕복) | **표준** |
| 보관소 **밖**의 좌석표 | 함수 포인터 | ★ **표준 밖** — 구현이 메운다 |
| 품목을 모르면 **한 칸이 몇 걸음인지도 모른다** | `void *` 산술 · `sizeof(void)` | ★ **표준 밖**(GNU 확장) |
| 「해당 없음」이라고 **찍는 도장** | 널 포인터 **상수** — 정수 상수 `0`, 그것을 `void *` 로 캐스트한 것 | **표준** |
| 그 도장이 찍힌 **표 한 장** | 널 포인터 **값** | **표준** |
| 도장의 **모양은 가게마다 다르다** | `NULL` 이 무엇으로 펼쳐지는지 | **구현 정의** |
| 표를 **백지로 지운 것** | `memset(&p, 0, sizeof p)` | ★ **「해당 없음」과 같다는 보장이 없다** |
| 「해당 없음」 표로 **물건을 찾으러 간다** | 널 역참조 | ★★ **UB** |

```text
   객체 포인터들은 void * 를 ★ 허브로 삼아 서로 오간다 (캐스트 없이)

        int *          double *        struct P *
          \               |               /
           \              |              /
            +---------> void * <--------+        <- ★ 서명(캐스트) 없이 양방향
           /              |              \
          /               |               \
        malloc 이 주는 것   memset 이 받는 것   free 가 받는 것

   ★ 이 그림 밖에 있는 것 둘
     int (*)(int)   함수 포인터  -> 규정에 없다 (gcc·clang 은 해 준다)
     void * 에 + 1              -> 규정에 없다 (gcc 확장이 1바이트로 친다)
```

> **`void *`** — 「**타입을 안 밝힌 객체 포인터**」. 어느 객체 포인터와도 **캐스트 없이** 오가고, 왕복하면 원래 주소다.\
> 예: `malloc` 은 `void *` 를 돌려주고, 그것을 `int *` 에 **캐스트 없이** 받는다.

> **널 포인터(null pointer)** — 「**어떤 객체도 함수도 가리키지 않는다**」고 정해진 포인터 값.\
> 예: `char *p = NULL;` 의 `p`. `if (p)` 가 거짓이 되는 유일한 포인터 값이다.

> **널 포인터 상수(null pointer constant)** — 「**어떻게 써야 널 포인터가 되는가**」를 정한 **문법 범주**.\
> 예: `0` 과 `(void *)0` 은 상수이고, `char *p = NULL;` 의 **`p` 는 상수가 아니다**(값만 널이다).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **`void *` 는 왜 캐스트 없이 오가고, 어디까지인가** — 함수 포인터와 산술 둘을 던져 경계를 찾는다.
2. ★★★ **`NULL`·`0`·`(void *)0`·`nullptr` 은 무엇이 다른가** — 전처리기와 `_Generic` 에게 직접 묻는다.\
   그리고 **널 포인터 「상수」와 「값」이 다른 개념**이라는 것을 가른다.
3. ★★★ **널을 역참조하면 무슨 일이 나는가** — ★ **답이 하나가 아니다.** 컴파일러와 최적화 수준으로 갈린다.

## 동작 방식

### (1) `void *` 는 양방향으로 조용하다 — 캐스트가 **한 번도** 안 나온다

**언제 쓰나** — `malloc` 의 반환을 받을 때, 타입을 모르는 버퍼를 함수에 넘길 때.

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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex.c -o x ; ./x (cc exit=0 · run exit=0) =====
(가) int* double* struct* -> void* : 캐스트 한 번도 안 썼다
(나) void* -> int* double* struct* : *pi = 7 · *pd = 2.5 · pp->x = 1
(다) (void*)&i == &i 인가 : 같다
(라) malloc/memset : 0 42 0
(마) sizeof(void *) = 8 · sizeof(int *) = 8 · sizeof(char *) = 8
```

```text
   (가) 가는 길                        (나) 오는 길
   int *      ──┐                    ┌──> int *
   double *   ──┼──> void *          ├──> double *
   struct P * ──┘        │           └──> struct P *
                         └───────────┘
   ★ 화살표 어디에도 (T *) 라고 적을 자리가 없다 — 소스에 캐스트가 0 번 나온다

   (다) 주소는 그대로            (라) 표준 라이브러리가 서 있는 자리
   &i  ==  (void *)&i           malloc  : void * 를 준다   -> int * 에 그냥 받는다
       비트가 안 바뀐다          memset  : void * 를 받는다  -> int * 를 그냥 준다
```

그림 해설 (한 단계씩):

- ★★ **(가)와 (나) 둘 다 캐스트가 없다.** 객체 포인터 → `void *` 도, `void *` → 객체 포인터도 **조용하다**.\
  ★ **이 양방향성이 `void *` 의 정의 그 자체**다. 다른 어떤 포인터 쌍도 이렇지 않다 —\
  `int *` 를 `double *` 에 넣으면 진단이 난다([14번 형제](../14-pointers-address-dereference-and-pointer-types/)가 정본).
- **(다) 주소값이 보존된다.** `(void *)&i == v1` 이 「같다」였다. **변환이 비트를 바꾸지 않는다.**
- ★ **(라) 그래서 `malloc` 의 반환에 캐스트를 안 붙인다.** `int *arr = malloc(…)` 이 C 의 관례다 —\
  C++ 에서는 붙여야 하지만 **C 에서 붙이면 군더더기**이고, 옛날에는 `<stdlib.h>` 를 빼먹은 것을 가려 주기까지 했다.
- **`memset` 이 준 0 세 개 중 가운데만 42** 로 바뀌었다 — `void *` 로 오간 메모리가 멀쩡하다는 뜻이다.
- **(마) 세 포인터의 `sizeof` 가 전부 8** 이다. ★ **이것은 구현 정의**다 —\
  표준이 보장하는 것은 「왕복하면 같다」이지 「크기가 같다」가 아니다.
- **경고는 0건**이다(`-pedantic` 포함). **합법이고 수상할 게 없다.**

비용 — 없다. **`void *` 변환은 기계어를 한 줄도 만들지 않는다**([05번 형제](../05-explicit-casts-and-pointer-conversions/)가 포인터 캐스트 일반에 대해 어셈블리로 보였다).\
치르는 값은 다른 데 있다 — **타입 검사가 그 지점에서 꺼진다.**

### (2) ★★★ 함수 포인터는 이 그림 밖이다 — 그런데 **`-pedantic` 이 없으면 아무도 말 안 해 준다**

**언제 쓰나** — 콜백 테이블을 `void *` 배열에 담고 싶을 때. **POSIX `dlsym` 을 쓸 때는 피할 수가 없다.**

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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex2.c -o x2 ; ./x2 (cc exit=0 · run exit=0) =====
객체 포인터 -> void* : 간다
함수 포인터 -> void* -> 함수 포인터 : back(21) = 42
fp1 == fp2 : 같다
```

```text
   객체의 세계                          함수의 세계
   +-------------------------+          +-------------------------+
   |  int *   double *       |          |  int (*)(int)           |
   |  struct P *   char *    |          |  void (*)(void)         |
   |          \   /          |          |                         |
   |          void *  <------|--- ? ----|---->                    |
   +-------------------------+          +-------------------------+
        ★ 규정이 있는 왕복                ★ 규정이 없는 왕복
        진단 0 건                        gcc 3 건 · clang 2 건 (-pedantic 일 때만)

   -pedantic 을 빼면                     ★ gcc 0 건 · clang 0 건 · 실행도 잘 된다
```

그림 해설 (한 단계씩):

- ★★★ **컴파일도 되고 실행도 된다.** `back(21)` 이 **42** 를 냈고 `fp1 == fp2` 가 「같다」였다.\
  ★ **그래서 위험하다** — 「돌아갔다」가 아무것도 증명하지 못하는 전형적인 자리다.
- ★★ **`-pedantic` 이 있어야만 보인다.** 없으면 **gcc·clang 둘 다 0건**이다.\
  [16번 형제](../16-array-pointer-decay-and-function-parameters/)와 **정반대**다 — 그쪽 경고는 플래그 없이도 켜져 있었다.
- ★★★ **gcc 3건 대 clang 2건**으로 갈린다. **갈리는 지점이 정확히 한 줄**이다 —\
  **명시 캐스트를 붙인 `(void *)twice` 줄**에서 **gcc 는 그래도 말하고 clang 은 봐준다**.\
  ★ **「캐스트를 붙였으니 괜찮다」가 컴파일러마다 다르다는 뜻**이다. 캐스트는 **표준 밖인 것을 표준 안으로 만들지 못한다.**
- ★ **진단 문구가 두 가지를 말한다** — gcc 는 「ISO C 가 금지한다」고 **표준을 근거로** 말하고,\
  clang 은 「`void` 포인터와 함수 포인터 사이를 변환한다」고 **무엇이 일어나는지**를 말한다.
- ★ **이 변환이 필요한 진짜 자리는 `dlsym`** 이다 — POSIX 가 `void *` 를 돌려주므로 **피할 수 없다.**\
  ★ **이 문서는 `dlsym` 을 던지지 않았다**([14번 형제](../14-pointers-address-dereference-and-pointer-types/)도 던지지 않았다 — [목록의 **35번 주제**](../35-function-pointers-and-callback-tables/)의 몫이다).

비용 — 이식성. 이 머신에서는 **코드 주소와 데이터 주소의 표현이 같아서** 아무 일도 안 난다.\
표현이 다른 구현(주소가 함수 기술자인 것들)에서는 **왕복 자체가 깨진다.**

### (3) `void *` 산술은 표준에 없다 — gcc 가 **1바이트**로 쳐 준다

**언제 쓰나** — 바이트 오프셋을 더하고 싶을 때. **`char *` 로 캐스트하는 것이 맞는 답**인데 손이 먼저 `void *` 에 간다.

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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex3.c -o x3 ; ./x3 (cc exit=0 · run exit=0) =====
sizeof(void) = 1   (표준에는 없다 — gcc 확장이 1 로 친다)
v      = a 의 첫 바이트
v+1 - v      = 1 바이트
c+1 - c      = 1 바이트
w++ 뒤 w - v = 1 바이트
v 로 4바이트 뒤를 읽으면 : 20
```

```text
   포인터에 +1 을 하면 "한 칸" 움직인다. 그럼 void * 의 한 칸은 몇 바이트인가?

   int *  p          한 칸 = sizeof(int)   = 4      -> 규정이 있다
   char * c          한 칸 = sizeof(char)  = 1      -> 규정이 있다
   void * v          한 칸 = sizeof(void)  = ???    -> ★ void 에는 크기가 없다

   gcc·clang 의 답 : "1 로 친다" (GNU 확장)
   표준의 답        : "그런 연산은 없다"

   ★ 그래서 세 자리가 전부 잡힌다 (-pedantic 일 때만)
      sizeof(void)   ·   v + 1   ·   w++
```

그림 해설 (한 단계씩):

- ★★ **`sizeof(void)` 가 1** 이고 `v + 1` 이 **1바이트**, `w++` 도 **1바이트** 움직였다.\
  `char *` 와 **똑같이** 굴렀다. ★ **편해 보이는 것이 함정**이다 — 편해서 쓰게 되고, 다른 컴파일러에서 깨진다.
- ★★★ **`-pedantic` 을 빼면 gcc 도 clang 도 0건**이다. (2)와 **같은 모양**이다 —\
  ★ **이 주제의 표준 위반 둘은 기본 설정에서 완전히 침묵한다.**
- ★★ **플래그 이름이 갈린다** — gcc 는 셋 다 `-Wpointer-arith` 로 묶는데,\
  clang 은 **`sizeof(void)` 만 `-Wpointer-arith`** 이고 **산술 둘은 `-Wgnu-pointer-arith`** 다.\
  ★ **clang 은 「GNU 확장을 쓰고 있다」고 이름으로 말해 준다** — 더 정확한 분류다.
- ★★ **`-Werror=pointer-arith` 를 붙이면 `cc exit=1`** 이 된다. **빌드를 깨는 것이 유일하게 확실한 처방**이다.\
  ★ **경고만 켜 두면 아무도 안 본다** — 이 주제에서 실제로 쓸 수 있는 유일한 강제 수단이다.
- **`*(int *)((char *)v + 4)` 는 20** 을 냈다 — **맞는 방법**이다. `void *` 를 `char *` 로 바꿔서 세면 된다.

비용 — `(char *)` 여덟 글자. **그 여덟 글자가 표준 안과 밖을 가른다.**

### (4) ★★ `NULL` 의 실제 정의 — **컴파일해서는 안 보인다. `-E` 로 물어야 한다**

**언제 쓰나** — 「`NULL` 은 그냥 0 아닌가」라고 생각했을 때. **전처리기에게 직접 물으면 끝난다.**

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

```text
   소스에 쓴 것        전처리기가 펼친 것              그래서 타입은
   ----------------   ---------------------------    ---------------
   NULL   (gcc, C)    (void 포인터로 캐스트한 0)      void *
   NULL   (clang, C)  같은 뜻인데 ★ 공백 한 칸이 다른 문자열
   NULL   (g++)       컴파일러 내장 이름 __null        ★ C++ 의 것이라 여기서는 축이 다르다

   그리고 헤더 한 장 안에 #define NULL 이 ★ 세 개 들어 있다
        +-----------------------------------------------+
        |  C++ 이면        -> 내장 이름                  |
        |  C 이면          -> void 포인터로 캐스트한 0    |
        |  그 밖이면        -> 정수 0                    |
        +-----------------------------------------------+
        ★ 셋 다 "널 포인터 상수" 다 — 어느 것이 뽑히는지가 구현 정의다
```

그림 해설 (한 단계씩):

- ★★★ **gcc 와 clang 의 펼친 문자열이 다르다** — 뜻은 같은데 **공백 한 칸이 다르다.**\
  ★ **`NULL` 을 문자열로 비교하는 코드는 이 한 칸에서 깨진다.** 정의는 **구현 정의**다.
- ★★ **g++ 는 아예 다른 것**(컴파일러 내장 이름)으로 펼친다. ★ **C 와 C++ 의 `NULL` 은 같은 것이 아니다.**\
  C++ 쪽 사정은 이 목록 밖이므로 **여기서는 「다르다」까지만** 적는다.
- ★★★ **헤더 한 장에 `#define NULL` 이 셋** 있다. 그중 하나만 살아남는다.\
  ★ **「`NULL` 은 `((void *)0)` 이다」는 이 머신의 C 모드에서 그렇다는 말**이지 규칙이 아니다.\
  **정수 `0` 으로 정의되는 분기가 같은 파일 안에 실제로 있다** — (7)에서 이것이 되살아난다.
- ★ **`-std=c2x` 로 바꿔도 gcc 의 `NULL` 은 그대로**다. **C23 이 `NULL` 의 정의를 바꾸지는 않았다** —\
  C23 이 더한 것은 **`nullptr` 이라는 새 낱말**이다((6)).
- ★★ **이것이 이 주제의 네 번째 창**이다 — **`-E`**. 컴파일 진단·실행 출력·sanitizer **셋 다 `NULL` 의 정의를 안 보여 준다.**

비용 — 없다. `-E` 한 번이면 끝난다. **모르면 평생 추측한다.**

### (5) ★★★ 널 포인터 「상수」와 널 포인터 「값」은 **다른 개념**이다

**언제 쓰나** — 「`0` 을 써도 되나」·「`NULL` 을 넘겨도 되나」가 헷갈릴 때.\
★ **둘을 안 가르면 (7)의 가변 인자 이야기가 통째로 안 읽힌다.**

한 문장으로 갈라 두자.

- **널 포인터 상수** — **문법 범주**다. 「**이렇게 쓰면 널 포인터가 된다**」고 정해진 **쓰는 법**이고,\
  그 범주에 드는 것은 둘이다 — **값이 0 인 정수 상수식**과 **그것을 `void *` 로 캐스트한 것**.\
  ★ 판정은 **컴파일 시간**에 난다. `0`·`0L`·`(void *)0` 은 상수이고 **`NULL` 은 그중 하나로 펼쳐진다.**
- **널 포인터 값** — **실행 시점의 값**이다. 「어떤 객체도 함수도 안 가리킨다」고 정해진 그 값.\
  ★ **어떻게 얻었는지는 안 따진다.** 상수로 만들었든, 다른 널 포인터를 복사했든, 함수가 돌려줬든 같다.

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

```text
   널 포인터 "상수" — 문법 범주 (컴파일 시간에 판정)
   +------------------------------------------------------+
   |  0        <- 정수 상수식, 값이 0                       |
   |  0L       <- 이것도 정수 상수식이다 (타입은 long)       |
   |  (void *)0 <- 그것을 void * 로 캐스트한 것              |
   |  NULL     <- 위의 어느 하나로 ★ 펼쳐진다 (구현 정의)     |
   +------------------------------------------------------+
            |
            |  포인터가 와야 하는 자리에 쓰면  -> 널 포인터 "값" 이 된다
            v
   널 포인터 "값" — 실행 시점의 값
   +------------------------------------------------------+
   |  char *cp = NULL;   char *c0 = 0;   char *cv = (void *)0;   |
   |        셋 다 널이고 ★ 서로 같다                        |
   |                                                       |
   |  char *p3 = cp;   <- p3 도 널이다 (값이 널)             |
   |                   ★ 그런데 p3 은 널 포인터 "상수" 가 아니다 |
   +------------------------------------------------------+

   ★ 갈라지는 자리 : "포인터가 와야 하는 자리" 가 없는 곳
      = 가변 인자 (...) 자리.  거기서는 변환해 줄 상대 타입이 없다.  -> (7)
```

그림 해설 (한 단계씩):

- ★★★ **`_Generic` 이 네 타입을 다르게 답했다.** `NULL` 은 `void *`, `0` 은 `int`, `(void *)0` 은 `void *`, `0L` 은 `long`.\
  ★ **네 개가 전부 널 포인터 상수인데 타입이 셋으로 갈린다.**\
  「널 포인터 상수」는 **타입의 이름이 아니라 쓰는 법의 이름**이라는 증거다.
- ★★ **그런데 셋으로 만든 널 포인터는 서로 같다.** `cp == c0` 도 `c0 == cv` 도 「같다」였다.\
  ★ **들어가는 문법은 셋인데 나오는 값은 하나**다. 그게 이 개념 쌍의 요점이다.
- ★★ **`char *p3 = cp;` 의 `p3` 은 값이 널이지만 상수가 아니다.**\
  ★ 그래서 **`p3` 을 가변 인자 자리에 넘기는 것은 아무 문제가 없고**(이미 `char *` 다),\
  **문제가 되는 것은 언제나 「상수를 그냥 던진」 쪽**이다.
- ★ **널 포인터의 여덟 바이트가 전부 `00`** 이었다. ★★ **이것은 관찰이지 보장이 아니다** —\
  (8)에서 같은 사실을 한 번 더, 더 위험한 얼굴로 만난다.
- ★ **`_Generic` 은 C11 부터**다. 이 관찰 자체가 **조건부 표준** 칸의 도구로 얻은 것이다.

비용 — 없다. **개념을 가르는 비용이 전부**이고, 그 값은 (7)에서 치러진다.

### (6) C23 의 `nullptr` — **타입이 다른 새 낱말**

**언제 쓰나** — C23 코드를 읽을 때. 그리고 「`nullptr` 은 `NULL` 의 새 이름이겠지」라고 생각했을 때.

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

```text
   C23 에서 세 낱말의 타입이 전부 다르다

   0         -> int          정수 상수. 포인터 자리에 놓이면 널이 된다
   NULL      -> void *       ★ C23 이어도 이 구현에서는 그대로다
   nullptr   -> nullptr_t    ★ 포인터도 정수도 아닌 ★ 전용 타입

   그런데 비교하면              nullptr == NULL  ->  같다
   대입해도                    char *p = nullptr;  ->  널

   -std=c17 로 내리면
   gcc   : 에러 1 개 — 그런데 ★ "nullptr_t 말인가요?" 라고 되묻는다
   clang : 에러 5 개 — nullptr 도 nullptr_t 도 ★ 모른다
```

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

그림 해설 (한 단계씩):

- ★★★ **`nullptr` 의 타입은 `void *` 가 아니다.** 전용 타입 `nullptr_t` 다.\
  **`NULL` 은 이 구현에서 C23 에서도 여전히 `void *`** 였다. ★ **둘은 같은 것이 아니다.**\
  그래서 **`_Generic` 으로 갈라 잡을 수 있고**, `printf("%d", nullptr)` 같은 오용도 **타입으로** 막힌다.
- ★ **그런데 값으로는 같다** — `nullptr == NULL` 이 「같다」이고 `char *p = nullptr` 도 널이다.\
  **새 타입을 준 것이지 새 값을 준 것이 아니다.**
- ★★ **`__STDC_VERSION__` 이 gcc `-std=c2x` 는 `202000L`, clang `-std=c23` 은 `202311L`** 이다.\
  ★ **`-std=c2x` 는 「C23 으로 컴파일했다」가 아니라 「그 당시 초안으로 컴파일했다」는 뜻**이다.\
  gcc 13 에는 `-std=c23` 자체가 없다.
- ★★★ **`-std=c17` 에서 둘이 갈린다** — clang 은 에러 5개로 **`nullptr_t` 라는 이름조차 모른다**고 하는데,\
  **gcc 13 은 에러 1개만 내고 「`nullptr_t` 말인가요?」라고 되묻는다.**\
  ★ **되물었다는 것은 그 이름을 이미 안다는 뜻**이다. 따로 던져 보면\
  **`-std=c17 -pedantic` 에서 `nullptr_t` 를 선언까지 하고 `sizeof` 가 8** 이 나온다 — **경고 0건**으로.
- ★★★ **그러니 「`-std=c17` 로 컴파일했다」는 「C17 코드다」가 아니다.**\
  `-std=` 는 **강제가 아니라 기본값 선택**이고, `-pedantic` 을 붙여도 **이름 하나는 새어 나왔다.**

비용 — 이식성. `nullptr` 을 쓰면 **C23 컴파일러가 필요하다.** `NULL` 은 C89 부터 어디서나 된다.

### (7) ★★★ 가변 인자 자리 — 고전 사례를 **던져 봤더니 재현되지 않았다**

**언제 쓰나** — `execl`·`open` 처럼 **끝을 널로 표시하는 가변 인자 함수**를 부를 때.\
「끝에 `0` 을 쓰면 깨진다」는 이야기를 **이 머신에서 확인하려고** 던졌다.

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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex7.c -o x7 ; ./x7 (cc exit=0 · run exit=0) =====
끝을 0 으로       : 2 개
끝을 NULL 로      : 2 개
끝을 (char*)0 으로: 2 개
```

여기까지는 인자가 적어 **전부 레지스터**로 간다. 그래서 **끝이 스택으로 밀려나는 판**을 따로 만들어\
**기계어를 직접 비교**했다.

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

```text
   무엇을 확인하려던 것인가

   va_arg(ap, char *) 는 "8바이트 슬롯" 을 꺼낸다
   그런데 0 을 그냥 넘기면 "int" 가 간다 — 4바이트다
        -> 슬롯이 4바이트만 채워지고 위쪽 4바이트가 쓰레기면 널이 아니게 된다
        -> 루프가 안 끝나고 쓰레기 주소를 문자열로 읽는다   ... 라는 것이 고전 사례다

   이 ABI 에서 실제로 일어난 일

   스택 슬롯                            레지스터 자리
   +----------------------------+      +----------------------------+
   | 8바이트 단위로 밀어 넣는다  |      | 32비트에 쓰면 위쪽 32비트가 |
   | 0 을 밀면 8바이트가 0 이다  |      | ★ 0 으로 채워진다           |
   +----------------------------+      +----------------------------+
        -> 어느 쪽이든 널 포인터와 ★ 같은 비트가 된다
   ★ 이 문서가 어셈블리로 확인한 것은 ★ 스택 슬롯 쪽이다 (레지스터 쪽은 안 찍었다)

   ★★ 그래서 두 함수의 기계어가 한 글자도 같았다 (with_zero == with_null)
```

그림 해설 (한 단계씩):

- ★★★ **세 표기가 전부 `2 개`** 를 냈다. **깨진 것이 하나도 없다.**
- ★★★ **어셈블리도 한 글자도 같다.** `with_zero` 와 `with_null` 이 **같은 명령 순서**로 나왔다 —\
  끝 인자를 스택으로 미는 자리가 **양쪽 다 8바이트짜리 0 밀어 넣기**다.\
  ★ **이 머신에서는 「`0` 을 넘기면 깨진다」가 재현되지 않았다.** 그대로 적는다.
- ★★★ **그런데 이것은 「`0` 을 써도 된다」는 뜻이 아니다.** 근거가 셋이다.
  - **가변 인자에서 넣은 타입과 꺼내는 타입이 안 맞는 것 자체가 UB** 다.\
    UB 는 「이번에 잘 돌았다」로 반증되지 않는다 — ★ **잘 도는 UB 가 가장 나쁘다.**
  - ★★ **`NULL` 이 정수 `0` 으로 정의된 구현이 실제로 가능하다** — (4)에서 **같은 헤더 안에 그 분기를 봤다.**\
    그런 구현에서는 **`NULL` 을 써도 `int` 가 간다.**
  - **`int` 와 포인터의 크기·슬롯 규칙이 다른 ABI** 에서는 그대로 어긋난다.\
    ★ **이 문서가 보인 것은 「이 ABI 에서 어긋나지 않는다」까지**이고, 다른 ABI 는 **던지지 못했다.**
- ★★ **그래서 관례는 `(char *)NULL` 이다.** 캐스트가 하는 일은 **널을 만드는 것이 아니라 타입을 못 박는 것**이다 —\
  ★ **(5)에서 갈라 둔 「상수」 문제를 「값」 문제로 바꿔 버리는 것**이 이 캐스트의 전부다.
- ★ **이것이 이 주제의 다섯 번째 창**이다 — **`-S`(어셈블리)**. 출력이 셋 다 같아서\
  **컴파일 진단·실행 출력으로는 아무것도 가를 수 없었다.**

비용 — 캐스트 아홉 글자. ★ **그리고 「여기서는 안 깨지더라」를 근거로 쓰지 않는 규율.**

### (8) `memset` 으로 0 을 채운 것이 널 포인터라는 **보장은 없다**

**언제 쓰나** — 구조체를 `memset` 으로 밀거나 `calloc` 으로 잡고 「**포인터 멤버는 널이겠지**」라고 넘어갈 때.

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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex9.c -o x9 ; ./x9 (cc exit=0 · run exit=0) =====
(가) memset 0 뒤 n.next == NULL : 참
(나) calloc 뒤 arr[2].next == NULL : 참
(다) NULL 의 바이트 : 0000000000000000 · 0 채움 : 0000000000000000 · memcmp = 0
    -> 이 구현에서는 같다. ★ 표준이 그렇게 정한 것이 아니라 여기서 그랬을 뿐이다.
```

```text
   두 가지를 갈라야 한다

   ① 바이트가 전부 0 인 표현        ② 널 포인터 값
   +---------------------+         +---------------------+
   | 00 00 00 00 ...     |         | "어디도 안 가리킨다" |
   | memset / calloc 이   |         | NULL 로 만든 것      |
   | 만드는 것            |         |                     |
   +---------------------+         +---------------------+
              \                             /
               \                           /
                이 구현에서는 ★ 같았다 (memcmp = 0)
                표준이 그렇게 정한 것은 ★ 아니다

   ★ 보장되는 것은 한 방향뿐이다
       p = NULL;  이라고 쓰면   ->  p 는 널이다        (보장)
       바이트를 0 으로 밀면      ->  널일 것이다        (★ 보장 아님 — 관찰)
```

그림 해설 (한 단계씩):

- **셋 다 「참」이었다** — `memset` 뒤에도, `calloc` 뒤에도 `next == NULL` 이고 `memcmp` 가 0 이었다.
- ★★★ **그래도 보장이 아니다.** 널 포인터의 **비트 표현은 구현 정의**이고,\
  「0 비트로 채운 것이 널 포인터다」라고 정한 곳이 없다.\
  ★ **`memcmp = 0` 이라는 출력은 「이 구현에서 같더라」까지만 말한다.**
- ★★ **이것이 「여러 번 돌려 봐도 같은 것이 더 위험한」 자리**다.\
  이 코드는 **어느 판을 돌려도 참**이 나올 것이고, 그래서 **가정이 굳는다.**
- ★ **`calloc` 이 약속하는 것은 「0 으로 채운 바이트」다.** 「널 포인터로 채운 배열」이 아니다.\
  **`0.0` 이라는 부동소수 값도 같은 이야기**이고 ★ **이 문서는 부동소수는 던지지 않았다.**
- ★ **널로 채우고 싶으면 루프로 `p[i] = NULL` 을 쓰는 것이 맞다.**\
  **실무에서는 거의 모두 `memset`/`calloc` 에 의존하고**, POSIX 계열 구현에서는 그 가정이 성립한다 —\
  ★ **「성립한다」와 「보장된다」를 가르는 것이 이 절의 전부**다.\
  **`memset`/`calloc` 의 계약 자체**는 목록의 **50번 주제**가 정본이다.

비용 — 루프 한 줄. **거의 아무도 치르지 않는다.** 대신 **가정을 주석으로 적어 두는 것**이 현실적인 타협이다.

### (9) ★★★ 널 역참조 — **컴파일러와 최적화 수준으로 갈린다**

**언제 쓰나** — 「널 역참조는 죽는다」고 외우고 있을 때. ★ **그 한 줄이 여기서 깨진다.**

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
===== gcc -std=c17 -Wall -Wextra -pedantic -g ex10.c -o x10 ; ./x10 (cc exit=0 · run exit=139) =====
역참조 직전
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

```text
   도구를 켜면 무엇이 달라지나 (둘 다 gcc · 최적화는 안 줬다)

   그냥 실행       "역참조 직전" 까지 찍고 죽는다            run exit=139
   UBSan          진단 한 줄을 찍고 ★ 그래도 죽는다          run exit=139
   ASan           리포트를 찍고 멈춘다                      run exit=1

   ★ 같은 사고인데 종료 코드가 139 와 1 로 갈린다
```

여기까지는 「죽는다」가 맞다. ★ **그런데 최적화 수준을 올리면 이야기가 달라진다** —그래서 **여섯 벌**을 전부 던졌다.

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
   같은 소스 · 같은 머신 · ★ 여섯 벌

                        출력                        run exit
   gcc   기본     "역참조 직전" 에서 끝             139   <- SIGSEGV  (-O 안 줬다)
   gcc   -O1      "역참조 직전" 에서 끝             139   <- SIGSEGV
   gcc   -O2      "역참조 직전" 에서 끝             139   <- SIGSEGV
   ---------------------------------------------------------------
   clang -O0      "역참조 직전" 에서 끝             139   <- SIGSEGV
   clang -O1      ★ 읽은 값까지 찍고 정상 종료         0   <- ★★★ 여기서 갈린다
   clang -O2      ★ 읽은 값까지 찍고 정상 종료         0   <- ★★★ 안 죽었다

   ★ 경계선이 컴파일러 안에 있다
     gcc   : 세 수준 전부 죽는다          -> "죽는다" 가 맞다
     clang : -O0 만 죽고 ★ -O1 부터 안 죽는다 -> "죽는다" 가 틀린다
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

```text
   clang -O2 에서 무슨 일이 일어났나 (어셈블리를 읽은 결과)

   소스가 시킨 것                     생성된 코드에 남은 것
   +---------------------------+     +---------------------------+
   | setvbuf(...)              |     | setvbuf 호출              |
   | puts("역참조 직전")        |     | puts 호출                 |
   | int v = *p;   <- 널 로드   |     | ★ 없다 — 로드가 통째로 사라졌다 |
   | printf("...%d", v)        |     | printf 호출               |
   |                           |     | ★ 그런데 값을 싣는 명령이 없다 |
   +---------------------------+     +---------------------------+

   -> 그래서 printf 가 "그 자리에 남아 있던 것" 을 찍는다
   -> 그래서 실행마다 값이 다르다 (세 판이 전부 다른 값)
```

그림 해설 (한 단계씩):

- ★★★ **여섯 벌 중 둘이 안 죽었다.** **gcc 는 기본·`-O1`·`-O2` 세 수준 전부 `run exit=139`** 인데,\
  **clang 은 `-O0` 만 139 이고 `-O1` 과 `-O2` 가 `run exit=0`** 으로 **값까지 찍고 정상 종료**했다.\
  ★★ **경계선은 「최적화를 켰나」가 아니라 「어느 컴파일러의 어느 수준인가」다** —\
  **clang 은 `-O1` 에서 이미 갈리고 gcc 는 `-O2` 에서도 안 갈린다.**\
  ★ **한 수준만 돌리고 「죽는다」고 적었으면 틀린 문서가 됐을 것**이다.
- ★★ **어셈블리를 보면 로드가 아예 없다.** UB 이므로 컴파일러는 **그 줄이 실행되지 않는다고 가정할 수 있고**,\
  그 가정 위에서 **읽기를 지워 버렸다.** ★ **「최적화가 UB 를 이용한다」가 눈에 보이는 자리**다.
- ★★★ **그래서 찍히는 값은 아무 뜻이 없다.** `-O2` 판을 세 판 돌려 **세 번 다 다른 값**이 나왔고,\
  `-O1` 판이 찍은 값도 그것들과 또 달랐다.\
  ★ **근거로 쓸 수 있는 것은 값이 아니라 `run exit=0` 이라는 판정**이다(머리말의 표).
- ★★ **UBSan 은 말해 주고도 못 막는다** — 진단 한 줄을 찍고 **그대로 `run exit=139`** 다.\
  ★ **진단이 났다고 프로그램이 멈추는 것이 아니다**(멈추려면 `-fno-sanitize-recover=all` 이 필요하다 —\
  ★ **이 문서는 그것을 던지지 않았다**).
- ★★ **ASan 은 종료 코드가 다르다**(`1`). 그리고 **주소를 정확히 말해 준다** —\
  「알 수 없는 주소 0」과 「읽기 접근」과 「영 페이지」라는 힌트까지 붙는다.\
  ★ **같은 사고가 도구에 따라 `139` 와 `1` 로 갈린다** — CI 에서 이 둘을 같은 실패로 묶어 두지 않으면 샌다.
- ★ **컴파일 진단은 0건**이다. `-Wall -Wextra -pedantic` 이 **널 역참조를 한 줄도 말하지 않았다** —\
  이 소스에서는 널이 **바로 위 줄에 있는데도** 그렇다.
- ★ **왜 죽었나·어떤 실패 계급인가**(영 페이지·신호·복구 가능성)는 목록의 **56번 주제**가 정본이다.\
  여기는 **「한 줄로 단정할 수 없다」는 것**까지다.

비용 — 널 검사 한 줄(`if (!p) return …`). ★ **안 하면 도구가 말해 줄 것이라는 기대가 이 절에서 깨진다.**

## 문법 — 형태와 규칙

### 형태 — 여섯 가지 쓰임

```c
/* ① void * 는 객체 포인터와 캐스트 없이 오간다 */
int i = 7;
void *v = &i;              /* 가는 길 */
int  *p = v;               /* 오는 길 — 캐스트를 쓰지 않는다 */

/* ② malloc 의 반환은 캐스트하지 않는 것이 C 의 관례다 */
int *arr = malloc(3 * sizeof *arr);

/* ③ 널 포인터를 만드는 네 가지 표기 */
char *a = NULL;            /* 관례. 어느 표준에서나 된다 */
char *b = 0;               /* 되기는 된다 — 읽는 사람이 헷갈린다 */
char *c = (void *)0;       /* NULL 이 이것으로 펼쳐지는 구현이 많다 */
char *d = nullptr;         /* C23 — 타입이 nullptr_t 다 */

/* ④ 검사는 값으로 한다 */
if (p)        { }          /* p != NULL 과 같다 */
if (p == NULL){ }          /* 명시형 — 이쪽이 읽기 낫다 */

/* ⑤ 바이트 오프셋은 char * 로 센다 */
int second = *(int *)((char *)v + sizeof(int));

/* ⑥ 가변 인자의 끝은 캐스트해서 넘긴다 */
execl_like(path, "a", "b", (char *)NULL);
```

### 금지 사례 — 어느 것이 무슨 층인가

```c
void *fp = some_function;      /* ★ 표준 밖 — 함수 포인터. -pedantic 만 말한다 */
void *g  = (void *)some_func;  /* ★ 캐스트를 붙여도 표준 밖이다 (gcc 는 그래도 말한다) */

void *v = buf;  v = v + 1;     /* ★ 표준 밖 — void * 산술. GNU 확장이 1바이트로 친다 */
size_t z = sizeof(void);       /* ★ 표준 밖 — void 에는 크기가 없다 */

f(path, "a", "b", 0);          /* ★ UB — 가변 인자에 정수 0. 이 ABI 에서는 안 깨졌다 */
f(path, "a", "b", NULL);       /* ★ 역시 위험 — NULL 이 0 으로 정의된 구현이 있을 수 있다 */

struct Node n; memset(&n, 0, sizeof n);
if (n.next == NULL) { }        /* ★ 보장 아님 — 이 구현에서만 참이다 */

int *p = NULL;  int v2 = *p;   /* ★★ UB — 죽을 수도 있고 ★ 안 죽을 수도 있다 */

int x = NULL;                  /* ★ 널을 정수 자리에 — 타입이 섞인다. 쓰지 마라 */
```

### 규칙 불릿

- ★★ **`void *` 는 어느 객체 포인터와도 캐스트 없이 양방향으로 오가고, 왕복하면 원래 주소다.**
- ★★ **함수 포인터는 그 규칙 밖**이다. gcc·clang 은 해 주지만 **`-pedantic` 이 「ISO C 가 금지한다」고 말한다.**
- ★★ **`void *` 산술과 `sizeof(void)` 도 표준 밖**이다. gcc 확장이 **1바이트**로 친다.
- ★★★ **널 포인터 「상수」는 문법 범주**다 — **값이 0 인 정수 상수식**과 **그것을 `void *` 로 캐스트한 것**.\
  **널 포인터 「값」은 실행 시점의 값**이고 **어떻게 얻었는지 안 따진다.**
- ★★ **`NULL` 이 무엇으로 펼쳐지는지는 구현 정의**다. 이 머신의 C 모드에서는 `void *` 캐스트 꼴이었다.
- ★★ **C23 `nullptr` 의 타입은 `nullptr_t`** 이고 **`NULL` 의 타입과 다르다.** 값으로는 같다.
- ★★ **포인터가 와야 할 자리가 없으면**(가변 인자) **상수는 변환되지 않는다.** 그래서 **캐스트해서 넘긴다.**
- ★★ **바이트를 0 으로 민 것이 널 포인터라는 보장은 없다.** 이 구현에서 같았을 뿐이다.
- ★★★ **널 역참조는 UB 이고, 「죽는다」는 한 줄 답이 실제로 깨진다.**

## 어디서 틀리나

### 1. ★★ 「`malloc` 의 반환은 캐스트해야 한다」

- **C 에서는 필요 없다.** `void *` 가 캐스트 없이 오간다.
- 캐스트를 붙이면 **군더더기**이고, 옛날에는 **`<stdlib.h>` 를 빼먹은 것을 가려 주기까지** 했다.
- ★ **C++ 에서는 붙여야 한다** — 거기서는 `void *` → 객체 포인터가 **암묵 변환이 아니다.**\
  **두 언어의 규칙이 다른 자리**이고, 그래서 C 코드를 C++ 로 컴파일하면 여기서 깨진다.

### 2. ★★★ 「`void *` 는 뭐든 담는다」

- **객체 포인터만**이다. **함수 포인터는 밖**이다.
- **실행은 잘 된다**(`back(21)` 이 42 였다). ★ **그래서 위험하다.**
- ★★ **`-pedantic` 이 없으면 gcc·clang 둘 다 0건**이다.
- ★ **명시 캐스트를 붙여도 gcc 는 여전히 말한다** — **캐스트는 표준 밖을 안으로 옮기지 못한다.**

### 3. ★★ 「`void *` 도 `+1` 하면 1바이트지」

- **그렇게 도는 것은 gcc 확장**이다. **표준에는 그 연산이 없다.**
- `-pedantic` 에서 **gcc 3건 · clang 3건**인데 ★ **플래그 이름이 갈린다** —\
  clang 은 산술 둘을 **`-Wgnu-pointer-arith`** 로 따로 분류한다.
- **맞는 방법은 `char *` 로 캐스트해 세는 것**이다.
- ★ **`-Werror=pointer-arith` 로 빌드를 깨는 것**이 유일하게 확실한 처방이다(`cc exit=1`).

### 4. ★★ 「`NULL` 은 결국 `0` 이다」

- **무엇으로 펼쳐지는지는 구현 정의**다. 같은 헤더 안에 **분기가 셋** 있었다.
- gcc 와 clang 의 문자열이 **공백 한 칸 다르고**, **g++ 는 아예 다른 것**이다.
- ★ **`-E` 로 물어야 보인다.** 컴파일 진단·실행 출력·sanitizer 셋 다 이것을 안 보여 준다.

### 5. ★★★ 「가변 인자 끝에 `0` 을 넘기면 깨진다」 — **이 머신에서는 재현되지 않았다**

- **세 표기가 전부 같은 답**(`2 개`)을 냈고, **기계어까지 한 글자도 같았다.**
- ★★ **그러니 「깨진다」를 사실로 적을 수 없다.** 널리 알려진 사고라도 **던져 보고 적는다.**
- ★★★ **그래도 `(char *)NULL` 을 쓴다.** 이유는 **세 가지이고 전부 「여기서 안 깨짐」과 무관**하다 —\
  ① 타입이 안 맞는 가변 인자 꺼내기는 **그 자체가 UB** 다\
  ② **`NULL` 이 `0` 으로 정의된 구현이 가능**하다(같은 헤더에 그 분기가 있었다)\
  ③ **슬롯 규칙이 다른 ABI** 에서는 어긋난다 — ★ **이 문서는 다른 ABI 를 던지지 못했다.**
- ★ **「잘 도는 UB」가 가장 나쁘다** — 고칠 이유가 안 보이기 때문이다.

### 6. ★★ 「`memset` 0 으로 밀었으니 포인터 멤버는 널이다」

- **이 구현에서는 참**이었다(`memcmp = 0`). ★ **그런데 보장이 아니다.**
- **`calloc` 이 약속하는 것은 「0 으로 채운 바이트」이지** 「널 포인터 배열」이 아니다.
- ★ **여러 번 돌려도 같은 답이 나오는 자리**라 **가정이 조용히 굳는다.**

### 7. ★★★ 「널을 역참조하면 죽는다」

- **clang 은 `-O1`·`-O2` 에서 안 죽었다**(`run exit=0`). **값을 찍고 정상 종료했다.**\
  ★ **gcc 는 기본·`-O1`·`-O2` 세 수준 전부 죽는다** — **컴파일러 안에 경계선이 있다.**
- **어셈블리를 보면 로드가 통째로 사라졌다** — 컴파일러가 **UB 를 근거로 지웠다.**
- ★★ **그래서 「크래시가 안 났으니 널이 아니었다」는 추론이 성립하지 않는다.**
- ★ **UBSan 은 말해 주고도 죽는다**(139), **ASan 은 `1` 로 끝난다.** **종료 코드가 도구마다 다르다.**

### 8. ★★ 「`nullptr` 은 `NULL` 의 새 이름이다」

- **타입이 다르다** — `nullptr_t` 대 `void *`. **값으로는 같다.**
- **`-std=c17` 에서는 에러**다(`cc exit=1`).
- ★★ **그런데 gcc 13 은 `-std=c17 -pedantic` 에서도 `nullptr_t` 라는 이름을 안다** — **경고 0건**으로 통과한다.\
  ★ **「`-std=` 로 막았다」를 믿지 마라.**

### 9. ★★ 「`-Wall -Wextra` 면 표준 위반은 잡힌다」

- **이 주제에서는 안 잡힌다.** 함수 포인터 변환도, `void *` 산술도 **둘 다 0건**이었다.
- ★ **`-pedantic` 을 붙여야 나온다.** [16번 형제](../16-array-pointer-decay-and-function-parameters/)와 **정반대**다.
- ★ 그리고 **널 역참조는 `-pedantic` 으로도 0건**이다 — **경고의 문제가 아니라 종류가 다른 문제**다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★ **이 주제는 무게중심이 둘로 쪼개져 있다** —\
**`void *` 쪽은 「표준」이 본체**이고(규칙이 명확하고 진단이 0건이다),\
**널 쪽은 「구현 정의 + UB」가 본체**다(비트 표현과 역참조).\
[16번 형제](../16-array-pointer-decay-and-function-parameters/)는 UB 한 칸이 본체였는데, ★ **여기는 한 문서 안에서 양극단이 같이 산다.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★ **`void *` ↔ 객체 포인터 양방향 무캐스트와 왕복** · **널 포인터 상수의 정의**(정수 상수 0 · 그것의 `void *` 캐스트) · **`NULL` 이 널 포인터 상수로 펼쳐진다는 것** · **널 포인터는 어떤 객체와도 같지 않다** · 세 표기로 만든 널이 **서로 같다** | 캐스트 0회로 컴파일·경고 0건 · `(void *)&i == v1` 이 「같다」 · `cp == c0`·`c0 == cv` 가 「같다」 | ★★ **진단이 0건인 것이 정상**이다 — `void *` 를 **어느 타입으로 되받는지**는 컴파일러가 검사할 근거가 없다 |
| **조건부 표준** | 버전·매크로 조건이 붙는다 | **`_Generic`**(C11) · **`nullptr`·`nullptr_t`**(C23) | `-std=c2x`/`-std=c23` 에서 `nullptr_t` · `-std=c17` 에서 **`cc exit=1`** | ★★★ **gcc 13 은 `-std=c17 -pedantic` 에서도 `nullptr_t` 를 안다** — 경고 0건 · `sizeof`=8. **`-std=` 는 강제가 아니다** |
| **구현 정의** | 문서화 의무가 있다 | ★ **`NULL` 의 실제 정의**(gcc·clang 이 공백 한 칸 다르고 g++ 는 아예 다르다) · **널 포인터의 비트 표현**(여기서 `00` 여덟 개) · **포인터 크기 8** · `__STDC_VERSION__` 값 | `-E` 출력 · `memcmp` · `sizeof` | ★★ **`-E` 로 물어야만 보인다.** 컴파일 진단·실행 출력·sanitizer 셋 다 침묵한다 |
| **미명시** | 몇 가지 중 하나 | ★ **없다** — 이 문서가 던진 실험 중 이 칸에 들어가는 것이 없었다. 몰래 채우지 않는다 | — | — |
| **UB** | 아무 일이나 | ★★ **본체 넷** — **널 역참조** · **가변 인자에서 타입이 안 맞는 꺼내기** · **함수 포인터 ↔ `void *`**(표준 밖 — 구현이 확장으로 메운다) · **`void *` 산술·`sizeof(void)`**(표준 밖 — GNU 확장) | `run exit=139`/`0` 의 갈림 · 어셈블리에서 **로드가 사라짐** · UBSan·ASan · `-pedantic` 진단 | ★★★ **`-pedantic` 없이는 뒤의 둘이 0건** · **널 역참조는 `-pedantic` 으로도 0건** · ★ **clang 은 `-O1` 부터 지워 버려서 아무 일도 없었던 것처럼 보인다** |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | gcc `-Wall -Wextra` | gcc `+pedantic` | clang `-Wall -Wextra` | clang `+pedantic` | 런타임 도구 |
|---|---|---|---|---|---|---|
| `void *` 양방향 변환 | 표준 | 0건 | 0건 | 0건 | 0건 | — (합법이다) |
| 함수 포인터 → `void *` | **표준 밖** | ★ **0건** | **3건** | ★ **0건** | **2건** | ★★ **없다 — 잘 돈다** |
| ★ 그중 **명시 캐스트** 줄 | **표준 밖** | 0건 | **1건**(gcc만) | 0건 | ★ **0건**(clang 은 봐준다) | — |
| `void *` 산술 · `sizeof(void)` | **표준 밖** | ★ **0건** | **3건** | ★ **0건** | **3건** | — |
| ★ `-Werror=pointer-arith` | **표준 밖** | — | **`cc exit=1`** | — | — | — |
| `NULL` 의 실제 정의 | 구현 정의 | 0건 | 0건 | 0건 | 0건 | ★★ **`-E` 뿐** |
| 널 포인터의 비트 표현 | 구현 정의 | 0건 | 0건 | 0건 | 0건 | ★ **직접 찍어 보는 것뿐** |
| `memset` 0 == 널 이라는 가정 | 구현 정의 | 0건 | 0건 | 0건 | 0건 | ★★ **없다 — 이 구현에서 참이다** |
| `-std=c17` 의 `nullptr` | 조건부 표준 | — | **`cc exit=1`** | — | **`cc exit=1`** | — |
| ★ `-std=c17` 의 `nullptr_t` **이름** | 조건부 표준 | 0건 | ★ **0건**(gcc 는 안다) | — | **에러**(clang 은 모른다) | — |
| 가변 인자 끝의 `0` | **UB** | 0건 | 0건 | 0건 | 0건 | ★★★ **없다 — 기계어가 같다** |
| 널 역참조 | **UB** | ★ **0건** | ★ **0건** | 0건 | 0건 | UBSan(139) · ASan(1) · ★ **clang `-O1`·`-O2` 는 0** · gcc 는 세 수준 전부 139 |

- ★★ **이 표의 결론 다섯 줄**
  - ★★★ **이 주제의 표준 위반 둘은 `-pedantic` 이 없으면 통째로 안 보인다.**\
    [16번 형제](../16-array-pointer-decay-and-function-parameters/)의 경고는 플래그가 필요 없었다 — **정반대의 주제**다.
  - ★★ **널 쪽 사실은 대부분 진단이 0건**이다. **비트 표현도, `memset` 가정도, 가변 인자도.**\
    ★ **직접 찍어 보는 것 말고 방법이 없다.**
  - ★★★ **널 역참조는 경고로 안 잡히고 런타임 도구로만 잡히는데, 그 도구마저 종료 코드가 갈린다**(139 대 1).
  - ★★ **명시 캐스트 한 줄에서 gcc 와 clang 이 갈린다** — 「캐스트했으니 괜찮다」가 **컴파일러 의견**이다.
  - ★★ **`-std=` 는 강제가 아니다** — gcc 13 은 `-std=c17 -pedantic` 에서도 `nullptr_t` 를 받아 준다.

### 이 주제의 네 번째 창과 다섯 번째 창

[16번 형제](../16-array-pointer-decay-and-function-parameters/)의 세 창(컴파일 진단 · 실행 출력 · sanitizer)이 **여기서는 자주 전부 침묵**한다.\
그래서 창을 둘 더 썼다.

- ★★★ **네 번째 창 — `-E`(전처리 결과).** `NULL` 이 무엇인지는 **컴파일해서는 영영 안 보인다.**\
  `-E` 로 물으면 **한 줄로 끝난다.** 그리고 헤더를 열면 **분기가 셋 있다는 것**까지 나온다.
- ★★★ **다섯 번째 창 — `-S`(어셈블리).** 두 자리가 이것으로만 판정됐다.\
  ① **가변 인자의 세 표기** — 출력이 셋 다 같아서 **기계어를 봐야 「같다」를 말할 수 있었다.**\
  ② **clang `-O1` 이상의 널 역참조** — **로드가 사라진 것**이 어셈블리에만 보인다.\
  ★ **둘 다 「실행이 정상이라서」 다른 창으로는 아무것도 못 가르는 자리**였다.
- ★ **그리고 제5의 상태가 하나 있다** — **「진단도 0건이고 출력도 정상인데 근거가 없는 것」.**\
  `memset` 0 이 정확히 그렇다. **틀린 것은 값이 아니라 그 값을 믿는 근거**다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 타입을 모르는 메모리를 넘긴다 | `void *` + 길이 | `char *` 로 대충 받기 |
| `malloc` 의 반환을 받는다 | `int *p = malloc(…)` | `(int *)malloc(…)`(C 에서는 군더더기) |
| 바이트 오프셋을 더한다 | `(char *)v + n` | `v + n`(표준 밖) |
| 콜백을 `void *` 에 담는다 | **담지 않는다** — 함수 포인터 타입 그대로 쓴다 | `void *fp = f;` |
| `dlsym` 의 반환을 받는다 | 캐스트가 **불가피**하다 — 주석으로 남긴다 | 표준이 보장한다고 적어 두기 |
| 널을 만든다 | `NULL`(어디서나) · `nullptr`(C23 전용 코드) | `0`(읽는 사람이 헷갈린다) |
| 널인지 본다 | `if (p == NULL)` · `if (!p)` | `if (p == 0)` |
| 가변 인자의 끝을 표시한다 | `(char *)NULL` | `0` · `NULL`(캐스트 없이) |
| 구조체를 0 으로 민다 | `memset` 은 쓰되 **가정을 주석으로** | 「포인터 멤버가 널이다」를 보장으로 쓰기 |
| 포인터 배열을 널로 채운다 | 루프로 `p[i] = NULL` | `calloc` 결과를 널 배열로 읽기 |
| 표준 위반을 찾는다 | `-pedantic`(+ `-Werror=…`) | `-Wall -Wextra` 로 만족하기 |
| 널 역참조를 확인한다 | **여러 최적화 수준** + ASan/UBSan | 한 벌 돌려 보고 「죽는다」로 적기 |
| `NULL` 의 정의를 본다 | `-E` | 헤더를 기억으로 재구성하기 |

판단 규칙 세 줄.

- **`void *` 는 객체 포인터의 허브**다. **함수와 산술 둘만 밖**이고, 그 둘은 **`-pedantic` 으로만 보인다.**
- **널 포인터 상수는 「쓰는 법」이고 널 포인터 값은 「그 결과」다.** **변환해 줄 상대가 없는 자리**에서만 이 구분이 살아난다.
- **널 역참조에 관한 한 줄짜리 답은 전부 틀린다** — **컴파일러와 최적화 수준을 밝혀야 답이 된다.**

## 핵심 문장

- ★★★ **`void *` 는 어느 객체 포인터와도 캐스트 없이 양방향으로 오간다.** 소스에 **캐스트가 0번** 나왔고 **경고도 0건**이다.\
  **주소값은 보존된다** — `(void *)&i == v1` 이 「같다」였다.
- ★★★ **함수 포인터는 그 밖이다.** 컴파일도 되고 **실행도 된다**(`back(21)` 이 42).\
  ★★ **`-pedantic` 이 없으면 gcc·clang 둘 다 0건**이고, 있으면 **gcc 3건 대 clang 2건**으로 갈린다 —\
  ★ **갈리는 한 줄은 명시 캐스트를 붙인 줄**이다. **캐스트는 표준 밖을 안으로 못 옮긴다.**
- ★★ **`void *` 산술도 표준 밖**이다. gcc 확장이 **1바이트**로 치고 `sizeof(void)` 가 **1** 이다.\
  ★ **`-Werror=pointer-arith` 로 빌드를 깨는 것**이 유일하게 확실한 처방이다(`cc exit=1`).
- ★★★ **널 포인터 「상수」는 문법 범주**이고 **「값」은 실행 시점의 값**이다.\
  `_Generic` 이 `NULL`→`void *`, `0`→`int`, `0L`→`long` 으로 **타입을 셋으로 갈랐는데**\
  **그 셋으로 만든 널 포인터는 서로 같았다.** ★ **들어가는 문법은 여럿, 나오는 값은 하나.**
- ★★ **`NULL` 의 정의는 구현 정의**다. gcc 와 clang 이 **공백 한 칸** 다르고 **g++ 는 아예 다른 것**이며,\
  같은 헤더 안에 **`#define NULL` 이 셋** 있다. ★ **`-E` 로만 보인다.**
- ★★ **C23 `nullptr` 의 타입은 `nullptr_t`** 로 **`NULL`(`void *`)과 다르다.** 값으로는 같다.\
  ★★ **gcc 13 은 `-std=c17 -pedantic` 에서도 `nullptr_t` 라는 이름을 경고 0건으로 받는다** — **`-std=` 는 강제가 아니다.**
- ★★★ **「가변 인자 끝에 `0` 을 넘기면 깨진다」는 이 ABI 에서 재현되지 않았다.**\
  세 표기가 전부 같은 답을 냈고 **기계어가 한 글자도 같았다.**\
  ★ **그래도 `(char *)NULL` 을 쓴다** — 타입이 안 맞는 꺼내기는 **그 자체가 UB** 이고,\
  **`NULL` 이 `0` 으로 정의된 구현이 가능**하며, **슬롯 규칙이 다른 ABI 가 있기 때문**이다.
- ★★ **`memset` 0 이 널 포인터라는 보장은 없다.** 이 구현에서는 `memcmp = 0` 으로 같았다 —\
  ★ **관찰이지 보장이 아니다.**
- ★★★ **널 역참조는 컴파일러와 최적화 수준으로 갈린다.**\
  **gcc 는 기본(`-O` 없음)·`-O1`·`-O2` 세 수준 전부 `run exit=139`** 인데\
  **clang 은 `-O0` 만 139 이고 `-O1` 부터 `run exit=0`** 이다. ★ **경계선이 컴파일러 안에 있다.**\
  **어셈블리를 보면 로드가 통째로 사라졌고**, 찍히는 값은 **세 판이 전부 달랐다.**
- ★★ **UBSan 은 말해 주고도 죽고**(139) **ASan 은 `1` 로 끝난다.** **컴파일 진단은 0건**이다.
- ★ **이 주제의 네 번째 창은 `-E`, 다섯 번째 창은 `-S`** 다. 셋(진단·출력·sanitizer)이 **전부 침묵하는 자리가 둘** 있었다.

## 관련 자료

- [`../README.md`](../README.md) — C 문법·API 주제 목록(이 주제는 19번)
- [`14-pointers-address-dereference-and-pointer-types/`](../14-pointers-address-dereference-and-pointer-types/) — ★★ **포인터 기본의 정본.**\
  `&`·`*`·포인터 타입·이중 포인터·`%p` 는 거기, 여기는 **`void *` 가 왜 특별한가**와 **널**부터
- [`05-explicit-casts-and-pointer-conversions/`](../05-explicit-casts-and-pointer-conversions/) — ★★ **캐스트·포인터 변환의 정본.**\
  그쪽은 **캐스트를 써야 하는 변환**(정수↔포인터 왕복·타입 펀닝·정렬), 여기는 ★ **캐스트가 필요 없는 쪽**과 **캐스트로도 안 되는 쪽**
- [`16-array-pointer-decay-and-function-parameters/`](../16-array-pointer-decay-and-function-parameters/) — ★ **플래그 분포가 정반대인 형제.**\
  그쪽 경고는 기본으로 켜져 있고, 여기는 **`-pedantic` 이 있어야** 둘이 보인다
- [`08-sizeof-alignment-and-offsetof/`](../08-sizeof-alignment-and-offsetof/) — `sizeof` 일반 규칙의 정본. **`sizeof(void)` 가 표준 밖인 것**은 여기
- [`13-goto-cleanup-idiom/`](../13-goto-cleanup-idiom/) — 자원 포인터를 `NULL` 로 두는 관용구가 막는 사고
- 목록의 **50번 주제** (`<string.h>` 메모리 함수) — ★ **`memset`/`calloc` 의 계약이 정본.**\
  여기는 「**0 바이트와 널 포인터는 다른 개념**」까지
- 목록의 **56번 주제** (공간 위반 — 널 역참조) — ★ **널 역참조의 실패 계급이 정본.**\
  여기는 「**컴파일러·최적화 수준으로 갈린다**」까지
- 목록의 **55번 주제** (엄격한 앨리어싱) — `void *` 로 받은 메모리를 **어느 타입으로 읽어도 되나**
- [목록의 **35번 주제**](../35-function-pointers-and-callback-tables/) (POSIX 쪽) — `dlsym` 이 함수 포인터 변환을 요구하는 자리
- 목록의 **58번 주제** (UB 를 잡는 도구) — `-pedantic`·`-Werror=`·sanitizer 를 묶어서

## 용어 풀이

- **`void *`** — 타입을 안 밝힌 객체 포인터. 어느 객체 포인터와도 **캐스트 없이** 오간다.\
  예: `int *p = malloc(4);` — `malloc` 이 준 `void *` 를 그냥 받는다.
- **널 포인터(null pointer)** — 어떤 객체도 함수도 가리키지 않는다고 정해진 포인터 **값**.\
  예: `char *p = NULL;` 에서 `if (p)` 는 거짓이다.
- **널 포인터 상수(null pointer constant)** — 「이렇게 쓰면 널 포인터가 된다」고 정한 **문법 범주**.\
  예: `0` 과 `(void *)0`. ★ `char *q = p;` 의 `p` 는 값만 널이고 **상수가 아니다.**
- **`NULL`** — `<stddef.h>` 등이 정의하는 매크로. **널 포인터 상수로 펼쳐진다.**\
  예: 이 머신의 C 모드에서는 `void *` 로 캐스트한 0 이었고 **C++ 모드에서는 내장 이름**이었다.
- **`nullptr` / `nullptr_t`** — C23 의 널 전용 낱말과 그 타입.\
  예: `_Generic(nullptr, nullptr_t: …)` 가 잡히고 `_Generic(NULL, void *: …)` 는 따로 잡힌다.
- **`_Generic`** — C11 의 **타입으로 고르는** 식. 이 문서에서 **타입 이름을 출력으로 만드는 데** 썼다.\
  예: `_Generic(0, int: "int", long: "long")` 이 `"int"` 를 고른다.
- **GNU 확장(GNU extension)** — 표준에 없는데 gcc 가 더해 둔 기능.\
  예: `void *` 산술과 `sizeof(void)` — clang 은 이것을 **`-Wgnu-pointer-arith`** 라는 이름으로 부른다.
- **`-pedantic`** — 「표준에 없는 것을 말해 달라」는 플래그. ★ **이 주제의 표준 위반 둘은 이것으로만 보인다.**\
  예: 함수 포인터를 `void *` 에 넣은 자리.
- **`-Werror=pointer-arith`** — 그 경고 하나만 **에러로 승격**한다. 예: `cc exit=1` 로 빌드가 깨진다.
- **`-E`** — 전처리까지만 하고 멈춘다. 예: `NULL` 이 무엇으로 펼쳐지는지 **한 줄로** 보여 준다.
- **가변 인자(variadic argument)** — `...` 로 받는 인자. **선언된 상대 타입이 없어** 변환이 안 일어난다.\
  예: `va_arg(ap, char *)` 로 꺼낼 자리에 `int` 를 넣으면 **UB** 다.
- **SIGSEGV / `run exit=139`** — 잘못된 메모리 접근으로 죽은 것. `139 = 128 + 11`.\
  예: 널 역참조가 gcc **세 수준 전부**와 clang `-O0` 에서 그렇게 끝났다(clang `-O1` 부터는 아니다).
- **UBSan / ASan** — 실행 중에 UB·메모리 오류를 잡는 도구.\
  예: 같은 널 역참조에 UBSan 은 진단을 찍고도 **139**, ASan 은 리포트를 찍고 **1** 로 끝났다.

---

## 더 들어가면

- ★ **`void *` 로 넘겼다가 「다른 타입」으로 되받는 것**은 던지지 않았다.\
  `int *` → `void *` → `double *` 이 **컴파일은 될 것**이지만 **읽는 순간 엄격한 앨리어싱 문제**가 된다 —\
  목록의 **55번 주제**의 몫이고, **이 문서는 왕복(같은 타입으로 되받기)만 확인했다.**

- ★★ **`-O3`·`-Os` 는 던지지 않았다.** 이 문서가 가진 것은 **여섯 벌**이다 —\
  **gcc 기본(`-O` 없음)·`-O1`·`-O2`** 와 **clang `-O0`·`-O1`·`-O2`**.\
  ★ **「clang 은 `-O1` 부터 안 죽는다」는 실측으로 답했다.** 남은 물음은 **그 위쪽**이다 —\
  `-O3`·`-Os` 에서도 같은지, 그리고 **gcc 가 `-O3` 에서도 계속 죽는지**는 **안 던졌다.**

- ★ **`-fno-sanitize-recover=all` 을 붙이지 않았다.** UBSan 이 **진단을 찍고도 그대로 죽는** 것까지만 봤고,\
  「첫 건에서 멈추게 하는」 판은 던지지 않았다.

- ★ **`-fno-delete-null-pointer-checks` 같은 플래그**로 clang `-O2` 의 결과가 달라지는지 **확인하지 않았다.**\
  로드가 사라진 것은 봤지만 **그것을 끄는 스위치를 던져 보지는 않았다.**

- ★★ **다른 ABI 를 던지지 못했다.** 이 머신은 x86-64 Linux 하나뿐이라\
  「가변 인자 슬롯이 4바이트인 ABI 에서 `0` 이 깨지는가」는 **확인할 수 없었다.**\
  ★ **그래서 (7)의 결론은 「여기서는 안 깨졌다」까지**이고, 그 밖은 **이유로만 적었다.**

- ★ **널 포인터의 비트 표현이 0 이 아닌 구현**도 던지지 못했다. 이 머신에서는 **여덟 바이트가 전부 `00`** 이었다.\
  ★ **관찰을 보장으로 옮겨 적지 않는 것**이 이 문서가 할 수 있는 전부다.

- ★ **`realloc`/`free` 에 널을 넘기는 계약**(널을 주면 아무 일도 안 한다)은 여기서 던지지 않았다.\
  목록의 **37번 주제**·**50번 주제** 쪽 이야기다.

- **`void *` 를 비교·정렬하는 것**(`qsort` 비교자가 `const void *` 를 받는 자리)도 던지지 않았다.\
  목록의 **51번 주제**의 몫이다.
