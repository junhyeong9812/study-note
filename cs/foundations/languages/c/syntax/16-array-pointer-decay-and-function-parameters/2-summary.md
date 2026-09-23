# c/syntax/16 — 배열-포인터 감쇠와 함수 매개변수: 「**함수 문턱에서 길이를 잃는다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — Array to pointer conversion](https://en.cppreference.com/w/c/language/conversion) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html) · [Clang Diagnostic flags](https://clang.llvm.org/docs/DiagnosticsReference.html)
> **실행 검증** — 이 문서의 모든 출력·경고·sanitizer 진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과\
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 작업 디렉터리는 `/tmp/c13`, 소스 파일명은 언제나 `ex.c` 다 — sanitizer 출력에 경로가 박히기 때문이다.\
> ★★ **실행 블록은 `./x 2>&1 | cat`(또는 `| sed -n '1,/^SUMMARY/p'`)으로 받았다** —\
> sanitizer 는 stderr, `printf` 는 stdout 이라 **터미널과 파이프에서 순서가 달라진다.**\
> 섞이는 프로그램(16-c)에는 `setvbuf(stdout, NULL, _IONBF, 0)` 를 넣어 **순서를 고정**했다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | `%p` 주소값 · ASan 의 `pc`/`bp`/`sp` · PID · `BuildId` | ★ 주소들 **사이의 차이**(`+4` ↔ `+40`) |
> | UB 가 만든 값(`sum10(small)` 의 `34`) | ★ **`sizeof` 값**(40 · 8 · 16 · 3) |
> | — | **`파일:줄:칸`** · 진단 본문 · 플래그 이름 · **종료 코드** |
>
> **버전** — 감쇠 규칙은 **C89 이후 바뀐 적이 없다.** **`int a[static 10]` 은 C99부터**다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★ **경계** — **동적 배열 자료구조**(용량·증가 전략)는 [`data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/)가 정본이고\
> 여기는 **감쇠 규칙과 `sizeof` 가 달라지는 자리**만 본다.\
> ★ **`int (*)[4]` 를 `int **` 와 혼동하는 것**은 [01번 형제](../01-declaration-syntax-and-reading/)가 정본이다 — 여기서는 **결론만** 되짚는다.\
> **`sizeof` 의 일반 규칙**은 [08번 형제](../08-sizeof-alignment-and-offsetof/), **포인터 산술**은 [15번 형제](../15-pointer-arithmetic-and-indexing/)가 정본이다.
> 선행 — [15번 형제](../15-pointer-arithmetic-and-indexing/) · [01번 형제](../01-declaration-syntax-and-reading/).

## 한눈에 — 쉽게 말하면

**배열을 함수에 넘기면 「상자」가 아니라 「상자의 첫 칸 주소」만 간다.**

이삿짐을 옮긴다고 하자.\
집 안에 있을 때 상자는 「**10칸짜리 상자**」다 — 크기를 물으면 답이 나온다.\
그런데 문밖으로 내보내면 **「여기부터 시작이오」라는 쪽지 한 장**만 건너간다.\
받는 쪽은 **어디서 끝나는지 모른다.**

그래서 함수 안에서 `sizeof(arr)` 을 물으면 **상자 크기가 아니라 쪽지 크기**가 나온다.\
★ **매개변수에 `[10]` 이라고 적어 두어도 그렇다.** 그 `10` 은 **컴파일러가 버린다.**

| 비유 | 실체 | 층 |
|---|---|---|
| 집 안의 상자 | `int arr[10]` — 타입이 `int[10]` | **표준** |
| 문밖으로 나간 쪽지 | 감쇠한 `int *` | **표준** |
| 쪽지에는 끝이 안 적혀 있다 | 함수 안 `sizeof(a)` == `sizeof(int *)` | **표준** |
| 문패에 「10칸」이라 써도 소용없다 | 매개변수 `int a[10]` ≡ `int *a` | **표준** |
| 상자째 재는 자리 | `sizeof arr` | **표준** — ★ 감쇠 안 함 |
| 상자 전체를 가리키는 쪽지 | `&arr` — 타입이 `int (*)[10]` | **표준** — ★ 감쇠 안 함 |
| 상자에 **내용물을 채워 넣는** 것 | `char s[] = "hi";` | **표준** — ★ 감쇠 안 함 |
| 「최소 10칸은 보장하시오」 | `int a[static 10]`(C99) | **표준** — 어기면 ★ UB |
| 끝을 모른 채 걷기 | 길이를 따로 안 넘겨 경계를 넘는 것 | ★ **UB** |

```text
   밖에서                              함수 안에서
   int arr[10]                         void f(int a[10])
   +--+--+--+--+--+--+--+--+--+--+     +--------+
   | 0| 1| 2| 3| 4| 5| 6| 7| 8| 9|     | a: 주소 |----> 같은 메모리
   +--+--+--+--+--+--+--+--+--+--+     +--------+
   sizeof arr = 40  (★ 40바이트)       sizeof a = 8  (★ 포인터)
   원소 개수  = 40/4 = 10              원소 개수  = ★ 알 수 없다

   ★ 그래서 길이는 "따로" 넘겨야 한다 :  void f(int *a, size_t n)
```

- ★★ **이 주제는 UB 가 본체**다 — [15번 형제](../15-pointer-arithmetic-and-indexing/)와 같은 모양이고 [13번 형제](../13-goto-cleanup-idiom/)와 정반대다.\
  다만 UB 의 **모양이 다르다** — 15번은 **산술이 UB** 이고, 16번은 **길이를 잃은 뒤의 접근이 UB** 다.
- ★★★ **이 주제의 네 번째 창은** 「**같은 배열을 세 꼴로 받아 `sizeof` 를 찍는 것**」이다.\
  셋이 **전부 8** 이 나오는 것을 보기 전까지는 `int a[10]` 이라는 표기를 믿게 된다.

> **감쇠(decay)** — 배열 이름이 식에서 **첫 원소를 가리키는 포인터로 자동 변환**되는 것.\
> 예: `int a[10]` 에서 `a + 1` 은 `&a[0] + 1` 이다. 「배열 + 1」이라는 연산은 없다.

> **매개변수 재작성(parameter adjustment)** — 함수 매개변수의 배열 타입이 **포인터 타입으로 고쳐 쓰이는 것**.\
> 예: `void f(int a[10])` 은 컴파일러에게 `void f(int *a)` 와 **글자만 다른 것**이다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **함수 안에서 `sizeof(arr)` 이 왜 원 배열 크기가 아닌가** — 세 꼴을 나란히 던져 보인다.
2. ★★ **감쇠가 일어나지 않는 자리는 어디인가** — 셋을 각각 증명한다.
3. ★ **매개변수의 `[10]` 은 아무 뜻도 없는가** — `static` 을 넣으면 무엇이 달라지나.

## 동작 방식

### (1) ★★★ 같은 배열을 세 꼴로 받아 `sizeof` 를 찍는다

**언제 쓰나** — 「매개변수에 `[10]` 이라고 썼으니 크기가 전달되겠지」라고 생각했을 때.

```text
===== 소스: ex.c (16-a) =====
#include <stdio.h>

static void f_sized(int a[10])  { printf("int a[10] 안 : sizeof(a) = %zu\n", sizeof a); }
static void f_open (int a[])    { printf("int a[]   안 : sizeof(a) = %zu\n", sizeof a); }
static void f_ptr  (int *a)     { printf("int *a    안 : sizeof(a) = %zu\n", sizeof a); }

int main(void) {
    int arr[10] = {0};
    printf("main 밖      : sizeof(arr) = %zu   (int %zu 개 x %zu 바이트)\n",
           sizeof arr, sizeof arr / sizeof arr[0], sizeof arr[0]);
    f_sized(arr);
    f_open(arr);
    f_ptr(arr);
    printf("\nsizeof(int *) = %zu\n", sizeof(int *));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘f_sized’:
ex.c:3:85: warning: ‘sizeof’ on array function parameter ‘a’ will return size of ‘int *’ [-Wsizeof-array-argument]
    3 | static void f_sized(int a[10])  { printf("int a[10] 안 : sizeof(a) = %zu\n", sizeof a); }
      |                                                                                     ^
ex.c:3:25: note: declared here
    3 | static void f_sized(int a[10])  { printf("int a[10] 안 : sizeof(a) = %zu\n", sizeof a); }
      |                     ~~~~^~~~~
ex.c: In function ‘f_open’:
ex.c:4:85: warning: ‘sizeof’ on array function parameter ‘a’ will return size of ‘int *’ [-Wsizeof-array-argument]
    4 | static void f_open (int a[])    { printf("int a[]   안 : sizeof(a) = %zu\n", sizeof a); }
      |                                                                                     ^
ex.c:4:25: note: declared here
    4 | static void f_open (int a[])    { printf("int a[]   안 : sizeof(a) = %zu\n", sizeof a); }
      |                     ~~~~^~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c:3:86: warning: sizeof on array function parameter will return size of 'int *' instead of 'int[10]' [-Wsizeof-array-argument]
    3 | static void f_sized(int a[10])  { printf("int a[10] 안 : sizeof(a) = %zu\n", sizeof a); }
      |                                                                                     ^
ex.c:3:25: note: declared here
    3 | static void f_sized(int a[10])  { printf("int a[10] 안 : sizeof(a) = %zu\n", sizeof a); }
      |                         ^
ex.c:4:86: warning: sizeof on array function parameter will return size of 'int *' instead of 'int[]' [-Wsizeof-array-argument]
    4 | static void f_open (int a[])    { printf("int a[]   안 : sizeof(a) = %zu\n", sizeof a); }
      |                                                                                     ^
ex.c:4:25: note: declared here
    4 | static void f_open (int a[])    { printf("int a[]   안 : sizeof(a) = %zu\n", sizeof a); }
      |                         ^
2 warnings generated.
```

```text
===== 실행 (gcc·clang 출력이 바이트 단위로 같다) =====
main 밖      : sizeof(arr) = 40   (int 10 개 x 4 바이트)
int a[10] 안 : sizeof(a) = 8
int a[]   안 : sizeof(a) = 8
int *a    안 : sizeof(a) = 8

sizeof(int *) = 8
```

```text
   세 꼴이 컴파일러에게는 ★ 같은 것이다

   void f(int a[10])  --재작성-->  void f(int *a)
   void f(int a[])    --재작성-->  void f(int *a)
   void f(int *a)                  void f(int *a)

   sizeof a  :   8        8        8       <- ★ 셋 다 sizeof(int *)
   경고      :   1건      1건      ★ 0건   <- 세 번째는 수상할 게 없다
```

그림 해설 (한 단계씩):

- ★★★ **세 꼴이 전부 8** 이다. `sizeof(int *)` 와 같다. **밖에서는 40** 이었는데 문턱을 넘자 8 이 됐다.
- ★★ **`-Wsizeof-array-argument` 가 잡는 것은 앞의 둘뿐**이다. **`int *a` 는 0건** —\
  **포인터에 `sizeof` 를 쓴 것은 수상할 게 없기 때문**이다.\
  ★ **그래서 도구는 「배열처럼 써 놓은 것」만 잡는다.** 이미 포인터로 쓴 코드에서 길이를 잃는 것은 **말해 주지 않는다.**
- ★ **이 경고는 플래그 없이도 켜져 있다** — 아래 (6)의 표에서 `gcc 무플래그`도 2건이다.
- ★ **clang 의 문구가 한 가지를 더 말한다** — 「`instead of 'int[10]'`」라고 **버려진 타입**까지 적는다.\
  `int a[]` 쪽은 「`instead of 'int[]'`」다.
- **`sizeof arr / sizeof arr[0]`** 관용구가 **밖에서만** 동작한다 — 안에서는 `8/4 = 2` 라는 **틀린 답**이 나온다.

비용 — 길이를 **따로 넘겨야 한다**(`void f(int *a, size_t n)`). **C 에 다른 방법이 없다.**

### (2) 감쇠가 **일어나는** 자리 — 식에서 쓰면 거의 전부

**언제 쓰나** — 「어디서 감쇠가 일어나나」를 셀 때. **`sizeof` 로 타입을 들여다보면** 보인다.

```text
===== 소스: ex.c (16-e) =====
#include <stdio.h>

static void take(int *p) { (void)p; }

int main(void) {
    int arr[10] = {0};
    int i = 1;

    printf("감쇠 안 함 : sizeof arr            = %zu\n", sizeof arr);
    printf("감쇠 안 함 : sizeof *&arr          = %zu\n", sizeof *&arr);
    printf("감쇠함     : sizeof (arr + 0)      = %zu\n", sizeof (arr + 0));
    printf("감쇠함     : sizeof (1 ? arr : arr)= %zu\n", sizeof (1 ? arr : arr));
    printf("감쇠함     : sizeof (arr, arr)     = %zu\n", sizeof (arr, arr));
    printf("감쇠함     : sizeof &arr[0]        = %zu\n", sizeof &arr[0]);
    printf("감쇠 안 함 : sizeof &arr           = %zu   (포인터라 8 — 증거는 &arr+1 쪽이다)\n", sizeof &arr);
    printf("감쇠함     : sizeof (int *){arr}   = %zu\n", sizeof (int *){arr});

    int *p = arr;            /* 초기화 — 감쇠 */
    p = arr;                 /* 대입 — 감쇠 */
    take(arr);               /* 함수 인자 — 감쇠 */
    (void)(arr + i);         /* 산술 — 감쇠 */
    (void)(arr == p);        /* 비교 — 감쇠 */
    (void)arr[i];            /* 인덱싱 — *(arr+i) 이므로 감쇠 */
    printf("\n위 여섯 자리는 전부 컴파일된다 (경고 0건이면 감쇠가 일어난 것)\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘main’:
ex.c:13:69: warning: left-hand operand of comma expression has no effect [-Wunused-value]
   13 |     printf("감쇠함     : sizeof (arr, arr)     = %zu\n", sizeof (arr, arr));
      |                                                                     ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c:11:73: warning: sizeof on pointer operation will return size of 'int *' instead of 'int[10]' [-Wsizeof-array-decay]
   11 |     printf("감쇠함     : sizeof (arr + 0)      = %zu\n", sizeof (arr + 0));
      |                                                                  ~~~ ^
ex.c:13:72: warning: sizeof on pointer operation will return size of 'int *' instead of 'int[10]' [-Wsizeof-array-decay]
   13 |     printf("감쇠함     : sizeof (arr, arr)     = %zu\n", sizeof (arr, arr));
      |                                                                  ~~~^
ex.c:13:72: warning: sizeof on pointer operation will return size of 'int *' instead of 'int[10]' [-Wsizeof-array-decay]
   13 |     printf("감쇠함     : sizeof (arr, arr)     = %zu\n", sizeof (arr, arr));
      |                                                                     ^ ~~~
3 warnings generated.
```

```text
===== 실행 (gcc·clang 출력이 바이트 단위로 같다) =====
감쇠 안 함 : sizeof arr            = 40
감쇠 안 함 : sizeof *&arr          = 40
감쇠함     : sizeof (arr + 0)      = 8
감쇠함     : sizeof (1 ? arr : arr)= 8
감쇠함     : sizeof (arr, arr)     = 8
감쇠함     : sizeof &arr[0]        = 8
감쇠 안 함 : sizeof &arr           = 8   (포인터라 8 — 증거는 &arr+1 쪽이다)
감쇠함     : sizeof (int *){arr}   = 8

위 여섯 자리는 전부 컴파일된다 (경고 0건이면 감쇠가 일어난 것)
```

```text
   감쇠가 일어나는 자리 (전부 열거)

   ① 포인터에 초기화·대입       int *p = arr;   p = arr;
   ② 함수 인자로 넘기기          take(arr);
   ③ 산술                       arr + i,  arr - 1
   ④ 비교                       arr == p,  arr < p
   ⑤ 인덱싱                     arr[i]   (== *(arr + i) 이므로 ③의 결과)
   ⑥ 조건 연산자의 두 가지       1 ? arr : arr
   ⑦ 쉼표 연산자의 오른쪽        (arr, arr)
   ⑧ 캐스트·복합 리터럴          (int *){arr}
   ⑨ return 값으로 내보내기      return arr;   (지역 배열이면 ★ 댕글링)

   ★ 한 줄로 : "배열을 식에서 쓰면 감쇠한다."
     ★ 단 아래 (3)의 셋만 예외다.
```

그림 해설 (한 단계씩):

- **`sizeof` 가 8 을 내면 감쇠한 것**이고 **40 을 내면 안 한 것**이다. `sizeof` 자체는 (3)의 예외라\
  **괄호 안의 식이 감쇠했는지**를 그대로 비춘다.
- ★ **clang 이 `-Wsizeof-array-decay` 로 세 자리를 잡는다** — **gcc 에는 그 플래그가 없다.**\
  gcc 는 `-Wunused-value`(쉼표 연산자) 하나만 낸다. **잡는 대상이 완전히 다르다.**
- ★★ **단항 `+` 는 배열에 쓸 수 없다.** 따로 던져 보면 **양쪽 다 에러**다 —\
  gcc 는 `error: wrong type argument to unary plus`, clang 은 `error: invalid argument type 'int *' to unary expression`.\
  ★ **clang 의 문구가 순서를 말해 준다** — **먼저 `int *` 로 감쇠한 뒤** 그 포인터에 단항 `+` 를 못 쓰는 것이다.\
  (C++ 에서는 된다. C 는 단항 `+` 에 **산술 타입**을 요구한다.)
- ★ **`return arr;`(지역 배열)는 감쇠는 하되 댕글링**이 된다 — 목록의 **57번 주제**의 몫이고 **이 문서는 던지지 않았다.**

비용 — 없다. **감쇠는 자동이고 막을 수 없다.**

### (3) ★★ 감쇠가 **안 일어나는** 자리 셋

**언제 쓰나** — 예외를 외워야 하는 자리다. **셋뿐**이다.

```text
===== 소스: ex.c (16-b) =====
#include <stdio.h>
#include <stdint.h>
#include <string.h>

int main(void) {
    int arr[10] = {0};

    /* ★ 감쇠가 안 일어나는 자리 1 — sizeof */
    printf("[1] sizeof arr      = %zu   (감쇠했다면 %zu 여야 한다)\n",
           sizeof arr, sizeof(int *));
    printf("    _Alignof(arr)   = %zu\n", _Alignof(int[10]));

    /* ★ 감쇠가 안 일어나는 자리 2 — & */
    int  *p1 = arr;          /* 감쇠 : int * */
    int (*p2)[10] = &arr;    /* 감쇠 안 함 : int (*)[10] */
    printf("[2] arr          = %p   arr + 1   = %p   (+%ld 바이트)\n",
           (void *)arr, (void *)(arr + 1),
           (long)((uintptr_t)(arr + 1) - (uintptr_t)arr));
    printf("    &arr         = %p   &arr + 1  = %p   (+%ld 바이트)\n",
           (void *)&arr, (void *)(&arr + 1),
           (long)((uintptr_t)(&arr + 1) - (uintptr_t)&arr));
    printf("    같은 주소인가 : arr==&arr[0] %d, (void*)arr==(void*)&arr %d\n",
           arr == &arr[0], (void *)arr == (void *)&arr);
    printf("    sizeof p1 = %zu   sizeof p2 = %zu   sizeof *p2 = %zu\n",
           sizeof p1, sizeof p2, sizeof *p2);

    /* ★ 감쇠가 안 일어나는 자리 3 — 문자열 리터럴로 배열을 초기화할 때 */
    char s[] = "hi";         /* 리터럴이 "복사"된다 — s 는 배열 */
    char *q  = "hi";         /* 리터럴이 감쇠한다 — q 는 포인터 */
    printf("[3] char s[] = \"hi\" : sizeof s = %zu\n", sizeof s);
    printf("    char *q  = \"hi\" : sizeof q = %zu\n", sizeof q);
    s[0] = 'H';
    printf("    s 는 고칠 수 있다 : %s\n", s);
    printf("    주소가 다른가 : s=%p  q=%p\n", (void *)s, (void *)q);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, exit=0) =====
[1] sizeof arr      = 40   (감쇠했다면 8 여야 한다)
    _Alignof(arr)   = 4
[2] arr          = 0x7ffe1fc0d9e0   arr + 1   = 0x7ffe1fc0d9e4   (+4 바이트)
    &arr         = 0x7ffe1fc0d9e0   &arr + 1  = 0x7ffe1fc0da08   (+40 바이트)
    같은 주소인가 : arr==&arr[0] 1, (void*)arr==(void*)&arr 1
    sizeof p1 = 8   sizeof p2 = 8   sizeof *p2 = 40
[3] char s[] = "hi" : sizeof s = 3
    char *q  = "hi" : sizeof q = 8
    s 는 고칠 수 있다 : Hi
    주소가 다른가 : s=0x7ffe1fc0d9cd  q=0x5cfc06ae9157
```

> ★ **대조할 것은 숫자가 아니라 성질이다.** 주소 넷은 실행마다 바뀐다.\
> 근거는 **`arr + 1` 이 +4, `&arr + 1` 이 +40** 이라는 **보폭 차이**와,\
> **`s` 와 `q` 가 서로 다른 영역**(`0x7ff…` 스택 ↔ `0x5cf…` 읽기 전용)에 있다는 것이다.

```text
   [2] 같은 주소인데 ★ 타입이 다르다

   arr   (감쇠)  ->  int *        ,  arr + 1  = +4 바이트   (원소 하나)
   &arr  (그대로) ->  int (*)[10]  ,  &arr + 1 = +40 바이트  (★ 배열 하나)

        arr / &arr  (같은 번지)
        v
        +--+--+--+--+--+--+--+--+--+--+ 
        | 0| 1| 2| 3| 4| 5| 6| 7| 8| 9|      40바이트
        +--+--+--+--+--+--+--+--+--+--+ 
         ^  ^                          ^
         |  arr+1 (+4)                 &arr+1 (+40)
         arr
```

```text
   [3] 문자열 리터럴 — 같은 "hi" 인데 사는 곳이 다르다

   char s[] = "hi";      ★ 리터럴의 내용을 스택의 배열로 ★ 복사한다
       s : ['h']['i']['\0']   sizeof s = 3    고칠 수 있다

   char *q  = "hi";      리터럴이 ★ 감쇠해 포인터가 된다
       q : [주소] --> 읽기 전용 영역의 "hi"    sizeof q = 8

   실측 주소 : s = 0x7ffe1fc0d9cd (스택)   q = 0x5cfc06ae9157 (다른 영역)
```

그림 해설 (한 단계씩):

- ★★ **자리 ① `sizeof`** — `sizeof arr` 가 **40** 이다. 감쇠했다면 8 이었을 것이다.\
  **`_Alignof` 도 같은 예외**다(여기서는 `_Alignof(int[10])` 로 물어 4 를 받았다).
- ★★ **자리 ② `&`** — `&arr` 는 감쇠하지 않아 타입이 **`int (*)[10]`** 이다.\
  **주소값은 `arr` 과 같은데**(`(void*)arr == (void*)&arr` 가 1) **보폭이 다르다** — `+4` 대 **`+40`**.\
  ★ **이것이 증거다.** `sizeof &arr` 는 8 이라 **`sizeof` 로는 구분이 안 된다.**\
  `sizeof *p2` 가 **40** 인 것도 같은 사실의 다른 얼굴이다.
- ★★ **자리 ③ 문자열 리터럴로 배열을 초기화할 때** — `char s[] = "hi"` 는 리터럴이 **복사**된다.\
  `sizeof s` 가 **3**(널 종단 포함)이고 **고칠 수 있다**(`Hi` 가 찍혔다).\
  `char *q = "hi"` 는 리터럴이 **감쇠**해 포인터가 되고 `sizeof q` 는 **8**, 주소도 **다른 영역**이다.\
  ★ **`q` 가 가리키는 것을 고치면 UB** 다 — 목록의 **20번 주제**가 정본이고 **이 문서는 던지지 않았다.**
- ★ **세 자리 전부 경고 0건**이다. **도구가 말해 주는 것이 아니라 규칙을 아는 것**이 전부다.

비용 — 없다. **예외 셋을 외우는 것이 비용이다.**

### (4) 매개변수의 `[10]` 이 거짓말인 것 — 그리고 **`static` 을 넣으면**

**언제 쓰나** — 「그럼 `[10]` 은 아무 뜻도 없나?」라고 물을 때.

```text
===== 소스: ex.c (16-c) =====
#include <stdio.h>

/* ★ "최소 10개짜리 배열의 첫 원소를 가리키는 포인터를 다오" 라는 계약 */
static int sum10(int a[static 10]) {
    int s = 0;
    for (int i = 0; i < 10; i++) s += a[i];
    return s;
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);   /* ★ 출력 순서를 고정한다 — 파이프로 받아도 같게 */
    int big[10] = {1,2,3,4,5,6,7,8,9,10};
    int small[3] = {1,2,3};

    printf("sizeof(a) 는 여전히 포인터인가 : %zu\n", sizeof(int *));
    printf("big   : %d\n", sum10(big));
    printf("small : %d   <- ★ 계약 위반\n", sum10(small));
    printf("NULL  : %d   <- ★ 계약 위반\n", sum10(NULL));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (cc exit=0) =====
ex.c: In function ‘main’:
ex.c:17:5: warning: ‘sum10’ accessing 40 bytes in a region of size 12 [-Wstringop-overflow=]
   17 |     printf("small : %d   <- ★ 계약 위반\n", sum10(small));
      |     ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
ex.c:17:5: note: referencing argument 1 of type ‘int[10]’
ex.c:4:12: note: in a call to function ‘sum10’
    4 | static int sum10(int a[static 10]) {
      |            ^~~~~
ex.c:18:5: warning: argument 1 to ‘int[static 10]’ is null where non-null expected [-Wnonnull]
   18 |     printf("NULL  : %d   <- ★ 계약 위반\n", sum10(NULL));
      |     ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
ex.c:4:12: note: in a call to function ‘sum10’
    4 | static int sum10(int a[static 10]) {
      |            ^~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic (cc exit=0) =====
ex.c:17:51: warning: array argument is too small; contains 3 elements, callee requires at least 10 [-Warray-bounds]
   17 |     printf("small : %d   <- ★ 계약 위반\n", sum10(small));
      |                                             ^     ~~~~~
ex.c:4:22: note: callee declares array parameter as static here
    4 | static int sum10(int a[static 10]) {
      |                      ^~~~~~~~~~~~
ex.c:18:51: warning: null passed to a callee that requires a non-null argument [-Wnonnull]
   18 |     printf("NULL  : %d   <- ★ 계약 위반\n", sum10(NULL));
      |                                             ^     ~~~~
ex.c:4:22: note: callee declares array parameter as static here
    4 | static int sum10(int a[static 10]) {
      |                      ^~~~~~~~~~~~
2 warnings generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic · ./x 2>&1 | cat  (run exit=139) =====
sizeof(a) 는 여전히 포인터인가 : 8
big   : 55
small : 34   <- ★ 계약 위반
(여기서 죽는다 — sum10(NULL) 에서 SIGSEGV)
```

```text
===== static 을 뺀 판 (int a[10]) — warning: 줄 수 =====
gcc   -std=c17 -Wall -Wextra -pedantic : 1 건   [-Wstringop-overflow=]   (NULL 쪽은 ★ 0건)
clang -std=c17 -Wall -Wextra -pedantic : ★ 0 건
```

```text
===== 최적화 수준을 바꿔도 같은가 — warning: 줄 수 =====
gcc   -O0 : 2 건  [-Wnonnull] [-Wstringop-overflow=]
gcc   -O1 : 2 건  [-Wnonnull] [-Wstringop-overflow=]
gcc   -O2 : 2 건  [-Wnonnull] [-Wstringop-overflow=]
clang -O0 : 2 건  [-Warray-bounds] [-Wnonnull]
clang -O1 : 2 건  [-Warray-bounds] [-Wnonnull]
clang -O2 : 2 건  [-Warray-bounds] [-Wnonnull]
```

```text
===== gcc -std=c17 -g -fsanitize=address,undefined · ./x 2>&1 | sed -n '1,/^SUMMARY/p'  (run exit=1) =====
sizeof(a) 는 여전히 포인터인가 : 8
big   : 55
=================================================================
==3681609==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x70907e90003c at pc 0x611e6bf553d1 bp 0x7ffe406a6990 sp 0x7ffe406a6980
READ of size 4 at 0x70907e90003c thread T0
    #0 0x611e6bf553d0 in sum10 /tmp/c13/ex.c:6
    #1 0x611e6bf558b5 in main /tmp/c13/ex.c:17
    #2 0x709080c2a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #3 0x709080c2a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #4 0x611e6bf55244 in _start (/tmp/c13/xs+0x2244) (BuildId: ce83fb4883ac72d640f4b3fff1194875873efa99)

Address 0x70907e90003c is located in stack of thread T0 at offset 60 in frame
    #0 0x611e6bf55444 in main /tmp/c13/ex.c:10

  This frame has 2 object(s):
    [48, 60) 'small' (line 13) <== Memory access at offset 60 overflows this variable
    [80, 120) 'big' (line 12)
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-buffer-overflow /tmp/c13/ex.c:6 in sum10
```

> ★ **대조할 것은 숫자가 아니라 성질이다.** 주소·PID·`BuildId` 는 실행마다 바뀌고,\
> `sum10(small)` 이 찍는 `34` 도 **UB 의 산물이라 근거가 못 된다.**\
> 근거는 **`stack-buffer-overflow` 가 `sum10 ex.c:6` 에서 났다**는 것과 **`[48, 60) 'small'` 을 넘어 60 을 읽었다**는 것,\
> 그리고 **평범한 실행은 `run exit=139`, ASan 실행은 `run exit=1`** 이라는 것이다.\
> ★ ASan 은 **`small` 에서 먼저 잡고 멈추므로** `sum10(NULL)` 까지 가지 않는다 — **평범한 실행이 거기서 죽는다.**

```text
   int a[10]          ->  int *a               "10" 은 ★ 버려진다
   int a[]            ->  int *a
   int a[static 10]   ->  int *a  + ★ 계약     "최소 10개를 보장한다"

   sizeof a : 셋 다 8  (계약이 있어도 ★ 크기는 안 돌아온다)

   진단
                       작은 배열      NULL
   int a[10]     gcc :  1건           ★ 0건
                 clang: ★ 0건         ★ 0건
   int a[static] gcc :  1건           1건
                 clang:  1건           1건
```

그림 해설 (한 단계씩):

- ★★ **`static` 을 넣어도 `sizeof` 는 여전히 포인터 크기**다. **길이가 돌아오지 않는다.**\
  바뀌는 것은 **계약**뿐이다 — 「이 포인터는 **최소 10개짜리 배열**의 첫 원소를 가리킨다」.
- ★★★ **clang 에서는 `static` 이 검사를 켜는 스위치**다. 없으면 **0건**, 있으면 **2건**.
- ★ **gcc 는 `static` 없이도 작은 배열을 잡는다**(`-Wstringop-overflow=`). **`static` 이 더해 주는 것은 `-Wnonnull`** 이다.\
  ★ **같은 기능을 두 컴파일러가 다른 문턱에서 켠다.**
- **최적화 수준을 바꿔도 건수가 같았다** — `-O0`·`-O1`·`-O2` 전부 2건. **이 진단은 최적화에 안 달렸다.**
- ★ **계약을 어겨도 컴파일은 된다**(exit=0). **어기면 UB** 이고 ASan 이 `sum10 ex.c:6` 에서 잡았다.
- ★ **경고 문구가 정보를 준다** — clang 은 「`contains 3 elements, callee requires at least 10`」로 **수를 말한다.**

비용 — 표기 하나. **호출부가 상수 크기 배열일 때만 검사가 걸린다** — 포인터를 넘기면 둘 다 조용하다.

### (5) 2차원 배열 인자 — **바깥 한 겹만 잃는다**

**언제 쓰나** — `int a[3][4]` 를 함수에 넘길 때. ★ **`int (*)[4]` 와 `int **` 를 혼동하는 것은 [01번 형제](../01-declaration-syntax-and-reading/)가 정본**이고 여기서는 **결론만** 되짚는다.

```text
===== 소스: ex.c (16-d) =====
#include <stdio.h>

static void row_form(int a[][4], int rows) {   /* == int (*a)[4] */
    printf("  매개변수 안 : sizeof(a) = %zu   sizeof(a[0]) = %zu   sizeof(a[0][0]) = %zu\n",
           sizeof a, sizeof a[0], sizeof a[0][0]);
    printf("  a[1][0] = %d   (rows=%d)\n", a[1][0], rows);
}

int main(void) {
    int m[3][4] = {{1,2,3,4},{5,6,7,8},{9,10,11,12}};
    printf("밖에서    : sizeof(m) = %zu   sizeof(m[0]) = %zu   sizeof(m[0][0]) = %zu\n",
           sizeof m, sizeof m[0], sizeof m[0][0]);
    int (*p)[4] = m;                 /* ★ m 은 int (*)[4] 로 감쇠한다 */
    printf("m -> p    : sizeof(p) = %zu   sizeof(*p) = %zu\n", sizeof p, sizeof *p);
    row_form(m, 3);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘row_form’:
ex.c:5:19: warning: ‘sizeof’ on array function parameter ‘a’ will return size of ‘int (*)[4]’ [-Wsizeof-array-argument]
    5 |            sizeof a, sizeof a[0], sizeof a[0][0]);
      |                   ^
ex.c:3:26: note: declared here
    3 | static void row_form(int a[][4], int rows) {   /* == int (*a)[4] */
      |                      ~~~~^~~~~~
```

```text
===== 실행 =====
밖에서    : sizeof(m) = 48   sizeof(m[0]) = 16   sizeof(m[0][0]) = 4
m -> p    : sizeof(p) = 8   sizeof(*p) = 16
  매개변수 안 : sizeof(a) = 8   sizeof(a[0]) = 16   sizeof(a[0][0]) = 4
  a[1][0] = 5   (rows=3)
```

```text
   밖에서                        매개변수 안에서
   m      : int[3][4]  = 48      a      : int (*)[4]  = 8    <- ★ 바깥 한 겹만 잃었다
   m[0]   : int[4]     = 16      a[0]   : int[4]      = 16   <- ★ 그대로다
   m[0][0]: int        = 4       a[0][0]: int         = 4

   ★ 그래서 a[1][0] 이 맞는 값(5)을 낸다 — 한 행이 16바이트라는 것을 타입이 알고 있다.
```

```text
===== 소스: ex.c (16-g) =====
#include <stdio.h>
static void bad(int **p) { printf("%d\n", p[1][0]); }
int main(void) { int m[3][4] = {{1,2,3,4},{5,6,7,8},{9,10,11,12}}; bad(m); return 0; }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (cc exit=0) =====
ex.c: In function ‘main’:
ex.c:3:72: warning: passing argument 1 of ‘bad’ from incompatible pointer type [-Wincompatible-pointer-types]
    3 | int main(void) { int m[3][4] = {{1,2,3,4},{5,6,7,8},{9,10,11,12}}; bad(m); return 0; }
      |                                                                        ^
      |                                                                        |
      |                                                                        int (*)[4]
ex.c:2:23: note: expected ‘int **’ but argument is of type ‘int (*)[4]’
    2 | static void bad(int **p) { printf("%d\n", p[1][0]); }
      |                 ~~~~~~^
```

그림 해설 (한 단계씩):

- ★★ **감쇠는 「바깥 한 겹」만 벗긴다.** `int[3][4]` → **`int (*)[4]`** 다.\
  매개변수 안에서 `sizeof a` 는 8 인데 **`sizeof a[0]` 은 16 으로 그대로**다.
- ★ **그래서 `a[1][0]` 이 맞는 값(5)을 낸다** — **한 행이 `int[4]`** 라는 것을 타입이 들고 있기 때문이다.\
  **열 수(4)는 타입에 남고, 행 수(3)만 잃는다.** 그래서 `rows` 를 따로 넘긴다.
- ★ **`int **` 로 받으면 안 된다.** gcc 의 `note:` 가 정확히 말해 준다 —\
  「**expected `int **` but argument is of type `int (*)[4]`**」.\
  ★ **왜 위험한지와 무엇을 읽게 되는지는 [01번 형제](../01-declaration-syntax-and-reading/)가 정본**이다. 결론만 되짚으면 —\
  **`int **` 로 보면 배열의 값 비트를 주소로 읽어** 엉뚱한 곳을 가리키고, **죽을지 조용히 틀릴지는 그날의 데이터가 정한다.**
- ★ **경고이지 에러가 아니다**(exit=0). **`-Wincompatible-pointer-types` 는 플래그 없이도 켜져 있다**([14번 형제](../14-pointers-address-dereference-and-pointer-types/)).

비용 — **열 수를 타입에 박아야 한다**(`int a[][4]`). 열 수가 실행 시간에 정해지면 VLA 매개변수가 필요하고,\
★ **이 문서는 VLA 매개변수를 던지지 않았다**(목록의 **18번 주제**).

### (6) 이 주제의 진단을 한 표로

```text
===== 각 프로그램을 일곱 조합으로 던져 warning: 줄을 센 것 =====
(세는 법 — grep -c 'warning:' 이다. grep -c warning 은 clang 의
 "2 warnings generated." 요약 줄까지 세어 한 건이 더 나온다)
```

| 프로그램 | gcc 무플래그 | gcc `-Wall` | gcc `+Wextra` | gcc `+pedantic` | gcc `-std=c2x +ped` | clang `-Wall -Wextra` | clang `+pedantic` |
|---|---|---|---|---|---|---|---|
| 16-a 세 꼴 `sizeof` | **2** | 2 | 2 | 2 | 2 | **2** | 2 |
| 16-b 감쇠 안 하는 셋 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 16-c `static 10` | **2** | 2 | 2 | 2 | 2 | **2** | 2 |
| 16-d 2차원 | **1** | 1 | 1 | 1 | 1 | **1** | 1 |
| 16-e 감쇠 자리 열거 | 0 | **1** | 1 | 1 | 1 | **3** | 3 |

- ★★ **이 주제의 경고는 대부분 플래그 없이도 켜져 있다** — `-Wsizeof-array-argument`·`-Wnonnull`·`-Wstringop-overflow=`.\
  **`-pedantic` 이 더해 주는 것이 없다** — [13번](../13-goto-cleanup-idiom/)·[14번](../14-pointers-address-dereference-and-pointer-types/)·[15번 형제](../15-pointer-arithmetic-and-indexing/)와 다른 점이다.
- ★★ **16-e 에서 gcc 1건 대 clang 3건**으로 크게 갈린다 — **`-Wsizeof-array-decay` 가 clang 에만 있다.**
- ★★★ **16-b 는 0건**이다. **감쇠가 안 일어나는 자리는 도구가 말해 주지 않는다** — 규칙을 알아야 한다.

## 문법 — 형태와 규칙

### 형태 — 배열을 넘기는 네 가지 표기

```c
void f1(int *a,        size_t n);   /* ① 솔직한 형태 — 이것이 실체다 */
void f2(int a[],       size_t n);   /* ② ①과 완전히 같다 */
void f3(int a[10],     size_t n);   /* ③ 10 은 버려진다. 사람에게만 말한다 */
void f4(int a[static 10]);          /* ④ C99 — "최소 10개" 를 계약으로 (검사가 걸린다) */

void g(int a[][4], int rows);       /* 2차원 — 바깥 한 겹만 잃는다 (== int (*a)[4]) */

/* 배열째 넘기고 싶으면 포인터 투 배열을 쓴다 */
void h(int (*a)[10]) { /* sizeof *a == 40 */ }
```

### 금지 사례 — 어느 것이 무슨 층인가

```c
void f(int a[10]) {
    size_t n = sizeof a / sizeof a[0];   /* ★ 8/4 = 2 — 틀린 길이. 경고는 난다 */
    for (size_t i = 0; i < 10; i++) …    /* ★ 호출자가 작은 배열을 줬으면 UB */
}

int *bad(void) { int a[10]; return a; }  /* ★ 감쇠는 하되 댕글링 — UB (57번 주제) */

void g(int **p) { … }   g(m);            /* ★ int (*)[4] 를 int ** 로 — 제약 위반 (01번 형제) */

char *q = "hi";  q[0] = 'H';             /* ★ 문자열 리터럴 수정 — UB (20번 주제) */

f4(NULL);                                /* ★ static 계약 위반 — UB. -Wnonnull 이 말한다 */
f4(small);                               /* ★ 10개 미만 — UB */
```

### 규칙 불릿

- ★ **배열 이름을 식에서 쓰면 첫 원소를 가리키는 포인터로 감쇠한다.**
- ★★ **감쇠가 안 일어나는 자리는 셋** — **`sizeof`**(과 `_Alignof`) · **`&`** · **문자열 리터럴로 배열을 초기화할 때**.
- ★★ **함수 매개변수의 배열 타입은 포인터로 재작성된다.** `int a[10]` ≡ `int a[]` ≡ `int *a` — **셋이 같은 함수**다.
- ★ **그래서 `sizeof(arr)/sizeof(arr[0])` 는 함수 안에서 틀린다.** 길이는 **따로 넘긴다.**
- ★ **`&arr` 의 타입은 `int (*)[10]`** 이다. 주소값은 같고 **보폭이 다르다**(`+40` 대 `+4`).
- ★ **2차원은 바깥 한 겹만 잃는다** — `int[3][4]` → `int (*)[4]`. **열 수는 타입에 남는다.**
- ★ **`int a[static 10]`(C99)은 크기를 돌려주지 않는다.** 계약을 만들고 **검사를 켠다.**
- **계약을 어기면 UB** 다. 컴파일은 된다.

## 어디서 틀리나

### 1. ★★★ 「매개변수에 `[10]` 이라고 썼으니 크기가 전달되겠지」

- **버려진다.** 세 꼴(`int a[10]`·`int a[]`·`int *a`)이 **전부 `sizeof` 8** 이었다.
- ★ **도구가 말해 준다** — `-Wsizeof-array-argument`(플래그 없이도 켜짐).\
  ★ 단 **`int *a` 로 써 놓으면 0건**이다 — **이미 포인터인 코드는 잡지 않는다.**
- 길이는 **따로 넘긴다**(`size_t n`).

### 2. ★★ 「`sizeof(arr)/sizeof(arr[0])` 관용구를 쓰면 된다」

- **밖에서만** 된다. 안에서는 **`8/4 = 2`** 라는 그럴듯한 오답이 나온다.
- ★ **2 라는 값이 함정이다** — 0 이나 음수였다면 바로 알았을 것이다.

### 3. ★★ 「`&arr` 와 `arr` 는 같은 것 아닌가」

- **주소값은 같다**(`(void*)arr == (void*)&arr` 가 1). **타입이 다르다.**
- **`arr + 1` 은 +4, `&arr + 1` 은 +40** 이었다. ★ **`sizeof` 로는 구분이 안 된다**(둘 다 8이 나올 수 있다).\
  **보폭으로 봐야 한다.**

### 4. ★ 「`char *q = "hi"` 와 `char s[] = "hi"` 는 같겠지」

- **`s` 는 배열이고 `q` 는 포인터**다. `sizeof` 가 **3 대 8**, 주소도 **다른 영역**이었다.
- **`s` 는 고칠 수 있고**(`Hi` 가 찍혔다) **`q` 가 가리키는 것을 고치면 UB** 다(목록의 **20번 주제**).

### 5. ★ 「2차원 배열은 `int **` 로 받으면 되겠지」

- **안 된다.** `int[3][4]` 는 **`int (*)[4]`** 로 감쇠한다.
- gcc 가 정확히 말한다 — 「**expected `int **` but argument is of type `int (*)[4]`**」.
- **경고이지 에러가 아니라** 실행 파일이 나온다. 무엇을 읽게 되는지는 [01번 형제](../01-declaration-syntax-and-reading/)가 정본이다.

### 6. ★ 「`int a[static 10]` 을 쓰면 안전해지겠지」

- **계약일 뿐**이다. 어기면 **UB** 이고 컴파일은 된다.
- ★ **검사는 호출부가 상수 크기 배열일 때만** 걸린다. 포인터를 넘기면 **둘 다 조용하다.**
- ★ **clang 에서는 `static` 이 검사를 켜는 스위치**이고, **gcc 는 `static` 없이도 작은 배열을 잡는다.**

### 7. ★ 「단항 `+` 로 배열을 포인터로 만들 수 있다던데」

- **C 에서는 에러**다(C++ 에서 되는 이야기다). gcc 는 `wrong type argument to unary plus`.
- ★ **clang 의 문구가 순서를 말해 준다** — `invalid argument type 'int *' to unary expression`.\
  **먼저 감쇠하고, 그 포인터에 단항 `+` 를 못 쓰는 것**이다.
- 포인터가 필요하면 **`arr + 0`** 이나 **`&arr[0]`** 를 쓴다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★ **이 주제는 UB 가 본체**다([15번 형제](../15-pointer-arithmetic-and-indexing/)와 같은 모양).\
다만 **UB 의 모양이 다르다** — 15번은 **산술 자체가 UB** 이고, 16번은 **길이를 잃은 뒤의 접근이 UB** 다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | **감쇠 규칙** · **매개변수 재작성**(`int a[10]` ≡ `int *a`) · **감쇠 안 하는 셋**(`sizeof`·`&`·리터럴 초기화) · `&arr` 의 타입이 `int (*)[10]` · 2차원은 **바깥 한 겹만** | `sizeof` 40 ↔ 8 · 보폭 +4 ↔ +40 · `sizeof a[0]`=16 · gcc·clang 출력이 같음 | ★ **감쇠 안 하는 셋은 진단이 0건**이다 — 규칙을 알아야 한다 |
| **조건부 표준** | 매크로가 정의될 때만 | ★ **해당 없음** — 감쇠에 조건부 보장은 없다 | — | — |
| **구현 정의** | 문서화 의무가 있다 | `sizeof(int)`=4·`sizeof(int *)`=8 이라 **40 과 8** 인 것 · 문자열 리터럴이 **읽기 전용 영역**에 놓이는 것 | `sizeof` 출력 · `s` 와 `q` 의 주소 대역이 다름 | ★ **주소 대역은 관찰**이지 보장이 아니다 |
| **미명시** | 몇 가지 중 하나 | ★ **같은 내용의 문자열 리터럴을 공유하는지** — 이 문서는 **던지지 않았다** | (미확인) | — |
| **UB** | 아무 일이나 | ★★ **본체** — **길이를 모른 채 경계를 넘는 접근**(`sizeof` 로 2 를 얻어 도는 루프) · **`static N` 계약 위반**(작은 배열·널) · 지역 배열 주소 반환 · 문자열 리터럴 수정 | ASan `stack-buffer-overflow` at `sum10 ex.c:6` · `-Wnonnull`·`-Wstringop-overflow=` | ★★ **포인터를 넘기면 계약 검사가 통째로 꺼진다** — 상수 배열일 때만 걸린다 |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | gcc 무플래그 | gcc `-Wall -Wextra -pedantic` | clang `-Wall -Wextra` | 런타임 도구 |
|---|---|---|---|---|---|
| `int a[10]` 안의 `sizeof a` | 표준 | **2건** | 2건 | **2건** | — |
| ★ `int *a` 안의 `sizeof a` | 표준 | **0건** | **0건** | **0건** | ★★ **없다 — 수상할 게 없다** |
| 감쇠 안 하는 셋 | 표준 | **0건** | **0건** | **0건** | ★ 없다(합법이다) |
| `sizeof (arr + 0)` 류 | 표준 | 0건 | **1건**(쉼표만) | **3건**(`-Wsizeof-array-decay`) | ★ **gcc 에 그 플래그가 없다** |
| `static 10` 에 작은 배열 | **UB** | **1건** | 1건 | **1건** | ★ ASan |
| `static 10` 에 `NULL` | **UB** | **1건** | 1건 | **1건** | ★ ASan(죽는다) |
| `int a[10]` 에 작은 배열 | **UB** | **1건**(gcc만) | 1건 | ★ **0건** | ★ ASan |
| ★ 포인터 변수를 넘긴 경우 | **UB** | **0건** | **0건** | **0건** | ★★ **ASan 뿐** |
| `int (*)[4]` 를 `int **` 로 | 제약 위반 | **1건** | 1건 | **1건** | — |

- ★★ **이 표의 결론 네 줄**
  - **이 주제의 경고는 `-pedantic` 이 필요 없다** — 대부분 **기본으로 켜져 있다.**\
    [13번](../13-goto-cleanup-idiom/)·[14번](../14-pointers-address-dereference-and-pointer-types/)·[15번 형제](../15-pointer-arithmetic-and-indexing/)와 정반대다.
  - ★★★ **`int *a` 로 써 놓으면 `sizeof` 함정이 안 잡힌다.** 도구는 **「배열처럼 써 놓은 것」만** 본다.
  - ★★ **`static N` 계약 검사는 호출부가 상수 크기 배열일 때만** 걸린다. **포인터를 넘기면 통째로 꺼진다.**
  - **`-Wsizeof-array-decay` 는 clang 에만 있다** — 16-e 에서 gcc 1건 대 clang 3건으로 갈렸다.

### 이 주제의 네 번째 창 — **세 꼴 `sizeof`** 와 **ASan**

- **컴파일 진단**은 `int *a` 꼴을 안 잡고, 포인터를 넘긴 호출도 안 잡는다.
- **실행 출력**은 그럴듯하다 — `sizeof a / sizeof a[0]` 이 **2** 를 낸다. **0 이나 음수가 아니라서 더 나쁘다.**
- **UBSan** 은 감쇠 자체에 할 일이 없다 — 감쇠는 **정의된 동작**이다.
- ★★ **그래서 창을 둘 더 썼다.**
  - ★★★ **같은 배열을 세 꼴로 받아 `sizeof` 를 나란히 찍는 것** —\
    **40 → 8 · 8 · 8** 을 한 화면에 놓는다. **`[10]` 이라는 표기가 거짓말이라는 것**을 눈으로 만든다.
  - **ASan** — 계약을 어긴 호출이 **`stack-buffer-overflow` at `sum10 ex.c:6`** 로 드러난다.\
    ★ **경고가 「호출부」를 가리킨 것과 달리 ASan 은 「읽은 자리」를 가리킨다** — 두 정보가 다르다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 배열을 함수에 넘긴다 | `void f(int *a, size_t n)` | 길이 없이 `void f(int a[10])` |
| 길이를 사람에게 말한다 | `int a[static 10]`(검사도 걸린다) | `int a[10]`(clang 은 0건) |
| 배열째 넘긴다(크기 유지) | `void h(int (*a)[10])` | `int a[10]`(감쇠한다) |
| 2차원을 넘긴다 | `void g(int a[][4], int rows)` | `int **p` |
| 원소 개수를 센다 | **밖에서** `sizeof a / sizeof a[0]` | 함수 안에서 같은 식 |
| 문자열을 고칠 것이다 | `char s[] = "hi";` | `char *q = "hi";` |
| 배열 전체의 주소 | `&arr`(타입은 `int (*)[N]`) | `arr`(첫 원소만) |
| 배열을 포인터로 만든다 | `arr + 0` · `&arr[0]` | `+arr`(C 에서는 에러) |
| 경계 넘기를 확인한다 | ASan | 경고만 보고 만족 |
| 동적 배열이 필요하다 | [`data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) | 고정 배열에 길이를 끼워 맞추기 |

판단 규칙 두 줄.

- **배열은 함수 문턱에서 길이를 잃는다.** 길이는 **따로 넘기는 것이 유일한 방법**이다.
- **감쇠가 안 일어나는 자리는 셋뿐**이다 — `sizeof`·`&`·문자열 리터럴 초기화.

## 핵심 문장

- ★★★ **같은 배열을 세 꼴(`int a[10]`·`int a[]`·`int *a`)로 받으면 `sizeof` 가 전부 8** 이다.\
  **밖에서는 40** 이었다. **매개변수의 `[10]` 은 컴파일러가 버린다.**
- ★★ **`-Wsizeof-array-argument` 가 앞의 둘만 잡고 `int *a` 는 0건**이다 — **이미 포인터인 코드는 안 잡는다.**\
  ★ 그리고 **이 경고는 플래그 없이도 켜져 있다.**
- ★★★ **감쇠가 안 일어나는 자리는 셋**이다 —\
  ① **`sizeof`**(`sizeof arr` 가 40) ② **`&`**(`&arr + 1` 이 **+40**, `arr + 1` 은 +4)\
  ③ **문자열 리터럴로 배열을 초기화할 때**(`char s[] = "hi"` 는 `sizeof` 3 이고 고칠 수 있다).\
  ★ **셋 다 진단이 0건**이다 — 규칙을 아는 것 말고 방법이 없다.
- ★★ **`&arr` 와 `arr` 는 주소값이 같고 타입이 다르다.** `sizeof` 로는 구분이 안 되고 **보폭으로 갈린다.**
- ★★ **2차원은 바깥 한 겹만 잃는다** — `int[3][4]` → `int (*)[4]`.\
  매개변수 안에서 **`sizeof a` 는 8 인데 `sizeof a[0]` 은 16 으로 그대로**다. **열 수는 타입에 남는다.**
- ★ **`int **` 로 받으면 안 된다.** gcc 가 「`expected 'int **' but argument is of type 'int (*)[4]'`」라고 말한다.\
  **왜 위험한지는 [01번 형제](../01-declaration-syntax-and-reading/)가 정본**이다.
- ★★ **`int a[static 10]`(C99)은 크기를 돌려주지 않는다.** 계약을 만들고 **검사를 켠다.**\
  ★ **clang 에서는 `static` 이 검사의 스위치**(없으면 0건), **gcc 는 `static` 없이도 작은 배열을 잡고** `static` 이 `-Wnonnull` 을 더한다.
- ★★ **계약 검사는 호출부가 상수 크기 배열일 때만** 걸린다. **포인터 변수를 넘기면 통째로 꺼진다.**
- ★ **`sizeof a / sizeof a[0]` 이 함수 안에서 2 를 낸다** — **0 이나 음수가 아니라서 더 나쁘다.**
- ★ **단항 `+` 는 배열에 못 쓴다**(C 에서는 에러). clang 의 문구가 **먼저 감쇠한다는 순서**를 말해 준다.
- ★ **이 주제의 경고는 `-pedantic` 이 필요 없다** — [13번](../13-goto-cleanup-idiom/)·[14번](../14-pointers-address-dereference-and-pointer-types/)·[15번 형제](../15-pointer-arithmetic-and-indexing/)와 정반대다.

## 관련 자료

- [`../README.md`](../README.md) — C 문법·API 주제 목록(이 주제는 16번)
- [`01-declaration-syntax-and-reading/`](../01-declaration-syntax-and-reading/) — ★★ **`int (*)[N]` 을 `int **` 로 받는 사고의 정본.** 그쪽은 「선언을 어떻게 읽나·무엇을 읽게 되나」, 여기는 「**감쇠가 그 타입을 만든다**」까지
- [`08-sizeof-alignment-and-offsetof/`](../08-sizeof-alignment-and-offsetof/) — ★ **`sizeof` 일반 규칙의 정본.** 함수 안에서 달라지는 자리는 **여기**가 정본이다
- [`14-pointers-address-dereference-and-pointer-types/`](../14-pointers-address-dereference-and-pointer-types/) — 포인터 타입과 `&`/`*` 의 정본
- [`15-pointer-arithmetic-and-indexing/`](../15-pointer-arithmetic-and-indexing/) — ★★ **`a[i]` == `*(a+i)` 와 `p+1` 의 보폭.** 감쇠는 **그 산술이 시작되는 지점**이다
- [`13-goto-cleanup-idiom/`](../13-goto-cleanup-idiom/) — **표준이 본체인 형제.** 층 분포가 정반대다
- [`data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) — ★ **동적 배열 자료구조의 정본.** 용량·증가 전략·상환 분석은 거기, 여기는 **감쇠 규칙과 `sizeof` 가 달라지는 자리**
- 목록의 **17번 주제** (다차원 배열과 그 포인터 타입) — `int a[3][4]` 의 메모리 배치를 **자세히**
- 목록의 **18번 주제** (VLA) — 열 수가 실행 시간에 정해지는 매개변수
- 목록의 **20번 주제** (널 종단 문자열과 문자열 리터럴) — ★ **`char *q = "hi"` 를 고치면 UB 인 것의 정본**
- 목록의 **56번 주제** (공간 위반 — 배열 밖 접근) — 길이를 잃은 뒤 무엇이 일어나나
- 목록의 **57번 주제** (시간 위반 — 댕글링) — `return arr;`(지역 배열)이 만드는 것

## 용어 풀이

- **감쇠(decay)** — 배열 이름이 식에서 첫 원소를 가리키는 포인터로 자동 변환되는 것. 예: `arr + 1` 은 `&arr[0] + 1`.
- **매개변수 재작성(parameter adjustment)** — 함수 매개변수의 배열 타입이 포인터 타입으로 고쳐 쓰이는 것.\
  예: `void f(int a[10])` 은 컴파일러에게 `void f(int *a)` 와 같다.
- **포인터 투 배열(pointer to array)** — 배열 하나 전체를 가리키는 포인터. 예: `int (*p)[10]`, `sizeof *p` 는 40.
- **`int a[static 10]`** — C99 의 표기. 「이 포인터는 **최소 10개짜리 배열**의 첫 원소를 가리킨다」는 계약.\
  ★ 크기를 돌려주지는 않는다.
- **문자열 리터럴(string literal)** — `"hi"` 같은 것. **배열 타입**이고, 식에서 쓰면 감쇠한다.\
  ★ **배열 초기화에 쓰면 감쇠하지 않고 내용이 복사된다.**
- **`-Wsizeof-array-argument`** — 매개변수의 배열에 `sizeof` 를 쓴 것을 경고. **gcc·clang 둘 다 기본으로 켜져 있다.**
- **`-Wsizeof-array-decay`** — 감쇠한 식에 `sizeof` 를 쓴 것을 경고. ★ **clang 에만 있다.**
- **`-Wstringop-overflow=`** — 선언된 크기보다 많이 접근하는 호출을 경고(gcc). 이름은 문자열용이지만 **배열 인자에도 붙는다.**
- **`-Wnonnull`** — 널일 수 없는 인자에 널을 넘긴 것을 경고. ★ **`static N` 이 이것을 켠다.**
- **`-Warray-bounds`** — clang 이 `static N` 계약 위반에 쓰는 플래그 이름. **gcc 의 같은 자리와 이름이 다르다.**

---

## 더 들어가면

- ★ **`int a[static 10]` 이 최적화에 쓰이는지**는 확인하지 않았다.\
  계약이 있으면 컴파일러가 **널 검사를 지울 수 있다**고 알려져 있지만 ★ **어셈블리로 던져 보지 않았다.**

- **VLA 매개변수**(`void f(int n, int a[n])`·`int (*a)[n]`)는 열 수가 실행 시간에 정해질 때 쓴다.\
  ★ **이 문서에서 던져 보지 않았다.** 목록의 **18번 주제**의 몫이다.

- ★ **같은 내용의 문자열 리터럴을 컴파일러가 공유하는지**(`"hi"` 두 개가 같은 주소인지)는 **미명시**이고\
  ★ **던져 보지 않았다.** 이 문서는 `char s[]` 와 `char *q` 의 **주소 대역이 다르다**는 것까지만 봤다.

- ★ **`char *q = "hi"; q[0] = 'H';`** 를 실제로 던지지 않았다 — 목록의 **20번 주제**의 몫이다.\
  이 문서는 **`s[0] = 'H'` 가 되는 것**만 실측했다.

- ★ **`return arr;`(지역 배열)의 댕글링**도 던지지 않았다. 목록의 **57번 주제**의 몫이다.

- ★ **`-Wsizeof-array-argument` 가 어느 플래그 집합 소속인지**를 gcc 문서로 확인하지 않았다.\
  **플래그 없이도 나온다**는 것만 실측했고, 그것이 「기본 켜짐」인지 「다른 무언가가 켠 것」인지는 **구분하지 못했다.**

- **`_Alignof(arr)`** 를 물을 때 이 문서는 **`_Alignof(int[10])` 이라는 타입 형태**로 던졌다.\
  ★ **식 형태(`_Alignof(arr)`)로는 던지지 않았다** — C 에서 `_Alignof` 의 피연산자는 **타입 이름**이기 때문이다.
