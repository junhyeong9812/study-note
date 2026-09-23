# c/syntax/16 — 배열-포인터 감쇠와 함수 매개변수: 「**함수 문턱에서 길이를 잃는다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고·sanitizer 진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 작업 디렉터리는 `/tmp/c13`, 소스 파일명은 언제나 `ex.c` 다.\
> ★★ **실행 블록은 `./x 2>&1 | cat`(또는 `| sed -n '1,/^SUMMARY/p'`)으로 받았다** —
> sanitizer 는 stderr, `printf` 는 stdout 이라 순서가 실행 환경에 달린다. 16-c 에는 `setvbuf(…, _IONBF, …)` 를 넣어 고정했다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | `%p` 주소값 · ASan 의 `pc`/`bp`/`sp` · PID · `BuildId` | ★ 주소들 **사이의 차이**(`+4` ↔ `+40`) |
> | UB 가 만든 값(`sum10(small)` 의 `34`) | ★ **`sizeof` 값**(40 · 8 · 16 · 3) |
> | — | **`파일:줄:칸`** · 진단 본문 · 플래그 이름 · **종료 코드** |

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 같은 배열을 세 꼴로 받아 `sizeof` 를 찍으면 — **셋 다 8** ★★★

**출력**

```text
===== 실행 (gcc·clang 출력이 바이트 단위로 같다) =====
main 밖      : sizeof(arr) = 40   (int 10 개 x 4 바이트)
int a[10] 안 : sizeof(a) = 8
int a[]   안 : sizeof(a) = 8
int *a    안 : sizeof(a) = 8

sizeof(int *) = 8
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (cc exit=0) =====
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
===== clang -std=c17 -Wall -Wextra -pedantic (cc exit=0) =====
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

**왜 그런가**

```text
   void f(int a[10])  --재작성-->  void f(int *a)
   void f(int a[])    --재작성-->  void f(int *a)
   void f(int *a)                  void f(int *a)

   sizeof a  :   8        8        8       <- ★ 셋 다 sizeof(int *)
   경고      :   1건      1건      ★ 0건
```

- **네 숫자는 40 · 8 · 8 · 8** 이다. 밖에서는 배열, 안에서는 포인터다.
- **경고는 2건**이고 **세 함수 중 둘**(`f_sized`·`f_open`)에 대한 것이다.
- ★★ **`f_ptr(int *a)` 에는 안 붙는다.** **포인터에 `sizeof` 를 쓴 것은 수상할 게 없기 때문**이다.\
  ★ 그래서 **이미 포인터로 써 놓은 코드에서 길이를 잃는 것은 도구가 말해 주지 않는다.**
- ★ **플래그는 필요 없다.** `-Wsizeof-array-argument` 는 **아무 플래그 없이도 켜져 있다**(9번 답의 표).
- ★ **clang 이 한 가지를 더 말한다** — 「`instead of 'int[10]'`」로 **버려진 타입**까지 적는다.

### 2. `sizeof` 로 감쇠 여부를 들여다보면 — **여덟 중 둘만 40** ★★

**출력**

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
===== gcc -std=c17 -Wall -Wextra -pedantic (cc exit=0) =====
ex.c: In function ‘main’:
ex.c:13:69: warning: left-hand operand of comma expression has no effect [-Wunused-value]
   13 |     printf("감쇠함     : sizeof (arr, arr)     = %zu\n", sizeof (arr, arr));
      |                                                                     ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic (cc exit=0) =====
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
===== sizeof (+arr) 만 따로 — gcc -std=c17 -Wall -Wextra -pedantic (cc exit=1) =====
ex.c: In function ‘main’:
ex.c:4:29: error: wrong type argument to unary plus
    4 |     printf("%zu\n", sizeof (+arr));
      |                             ^
```

```text
===== sizeof (+arr) 만 따로 — clang -std=c17 -Wall -Wextra -pedantic (cc exit=1) =====
ex.c:4:29: error: invalid argument type 'int *' to unary expression
    4 |     printf("%zu\n", sizeof (+arr));
      |                             ^~~~
1 error generated.
```

**왜 그런가**

- **여덟 값은 40 · 40 · 8 · 8 · 8 · 8 · 8 · 8** 이다.
- ★ **감쇠가 일어나지 않은 것은 셋**이다 — `sizeof arr`·`sizeof *&arr`·`sizeof &arr`.\
  ★ 앞의 둘은 **40 이라는 숫자로** 드러나지만 **`&arr` 는 8 이라 숫자로 구분이 안 된다** —\
  그쪽의 증거는 **`&arr + 1` 이 40바이트 움직인다**는 것이다(3번 답).
- ★★ **경고 건수가 gcc 1건 대 clang 3건**으로 갈린다. **`-Wsizeof-array-decay` 가 clang 에만 있다.**\
  gcc 가 낸 1건은 `-Wunused-value`(쉼표 연산자)이고 **감쇠와 무관한 이야기**다.
- ★★ **`sizeof (+arr)` 는 양쪽 다 에러**다(`cc exit=1`). C 에서 단항 `+` 는 **산술 타입**을 요구한다.\
  ★ **clang 의 문구가 순서를 말해 준다** — `invalid argument type 'int *'`.\
  **먼저 `int *` 로 감쇠한 뒤** 그 포인터에 단항 `+` 를 못 쓰는 것이다. (C++ 에서는 이것이 관용구로 쓰인다.)

### 3. 감쇠가 안 일어나는 세 자리를 증명하면 ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, cc exit=0 · run exit=0) =====
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
> 근거는 **`+4` 대 `+40`** 이라는 보폭 차이와, **`s` 와 `q` 가 서로 다른 대역**에 있다는 것이다.

**왜 그런가**

```text
        arr / &arr  (같은 번지, ★ 다른 타입)
        v
        +--+--+--+--+--+--+--+--+--+--+ 
        | 0| 1| 2| 3| 4| 5| 6| 7| 8| 9|      40바이트
        +--+--+--+--+--+--+--+--+--+--+ 
         ^  ^                          ^
         |  arr+1 (+4)                 &arr+1 (+40)
         arr
```

```text
   char s[] = "hi";   리터럴 내용을 스택 배열로 ★ 복사   sizeof s = 3   고칠 수 있다
   char *q  = "hi";   리터럴이 ★ 감쇠해 포인터           sizeof q = 8   가리키는 곳은 다른 대역
```

- **`arr + 1` 은 +4 바이트, `&arr + 1` 은 +40 바이트**다. **같은 번지에서 시작해 보폭이 다르다.**
- **`sizeof p2` 는 8**(포인터니까), **`sizeof *p2` 는 40**(가리키는 것이 `int[10]` 이니까)이다.
- **`sizeof s` 는 3**(`'h'`·`'i'`·`'\0'`), **`sizeof q` 는 8**(포인터)이다.\
  ★ **다른 이유** — `char s[] = "hi"` 에서는 리터럴이 **감쇠하지 않고 내용이 복사**되고,\
  `char *q = "hi"` 에서는 리터럴이 **감쇠해 포인터**가 된다.
- ★ **경고는 0건**이다. **이 세 자리는 도구가 말해 주지 않는다** — 규칙을 아는 것 말고 방법이 없다.
- ★ **`q` 가 가리키는 것을 고치면 UB** 다. **이 문서는 그것을 던지지 않았다**(목록의 **20번 주제**).

### 4. 매개변수에 `static` 을 넣고 계약을 어기면 — **검사가 켜진다** ★★

**출력**

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

> ★ **대조할 것은 숫자가 아니라 성질이다.** `small : 34` 는 **UB 의 산물이라 근거가 못 된다.**\
> 근거는 **`[48, 60) 'small'` 을 넘어 offset 60 을 읽었다**는 것과 **종료 코드가 139 ↔ 1 로 갈린다**는 것이다.

**왜 그런가**

- **`sizeof` 는 달라지지 않는다** — 여전히 **8** 이다. `static` 은 **크기를 돌려주지 않는다.**
- **경고는 2건**이고 **`sum10(small)`(17행)과 `sum10(NULL)`(18행)** 두 호출에 대한 것이다.\
  ★ **플래그 이름이 다르다** — gcc 는 `-Wstringop-overflow=`, clang 은 `-Warray-bounds`.\
  `-Wnonnull` 만 이름이 같다.
- ★★★ **`static` 을 빼면 둘이 갈린다** — **gcc 1건**(작은 배열만), **clang 0건.**\
  **clang 에서는 `static` 이 검사를 켜는 스위치**이고, **gcc 는 `static` 없이도 작은 배열을 잡되 `static` 이 `-Wnonnull` 을 더한다.**
- **최적화 수준을 바꿔도 2건 그대로**다 — 이 진단은 **최적화에 안 달렸다**(`-O0`·`-O1`·`-O2` 여섯 벌).
- **종료 코드** — 평범한 실행은 **139**(= 128 + 11, `sum10(NULL)` 에서 SIGSEGV),\
  ASan 실행은 **1**(그 앞 `sum10(small)` 에서 먼저 잡고 멈춘다).\
  ★ **같은 프로그램이 도구에 따라 다른 자리에서 죽는다.**

### 5. 2차원 배열을 함수에 넘기면 — **바깥 한 겹만 잃는다** ★★

**출력**

```text
===== 실행 =====
밖에서    : sizeof(m) = 48   sizeof(m[0]) = 16   sizeof(m[0][0]) = 4
m -> p    : sizeof(p) = 8   sizeof(*p) = 16
  매개변수 안 : sizeof(a) = 8   sizeof(a[0]) = 16   sizeof(a[0][0]) = 4
  a[1][0] = 5   (rows=3)
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (cc exit=0) =====
ex.c: In function ‘row_form’:
ex.c:5:19: warning: ‘sizeof’ on array function parameter ‘a’ will return size of ‘int (*)[4]’ [-Wsizeof-array-argument]
    5 |            sizeof a, sizeof a[0], sizeof a[0][0]);
      |                   ^
ex.c:3:26: note: declared here
    3 | static void row_form(int a[][4], int rows) {   /* == int (*a)[4] */
      |                      ~~~~^~~~~~
```

```text
===== int ** 로 받은 판 — gcc -std=c17 -Wall -Wextra -pedantic (cc exit=0) =====
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

**왜 그런가**

```text
   밖에서                        매개변수 안에서
   m      : int[3][4]  = 48      a      : int (*)[4]  = 8    <- ★ 바깥 한 겹만 잃었다
   m[0]   : int[4]     = 16      a[0]   : int[4]      = 16   <- ★ 그대로다
   m[0][0]: int        = 4       a[0][0]: int         = 4
```

- **여덟 숫자는 48 · 16 · 4 / 8 · 16 / 8 · 16 · 4** 이고 `a[1][0]` 이 **5** 다.
- ★★ **잃은 것은 행 수(3)뿐**이고 **열 수(4)는 타입에 남는다.**\
  `sizeof a` 만 8 이 되고 **`sizeof a[0]` 은 16 으로 그대로**다.
- ★ **그래서 `a[1][0]` 이 맞는 값을 낸다** — 한 행이 `int[4]`(16바이트)라는 것을 타입이 들고 있어\
  `a + 1` 이 **16바이트** 건너뛴다. 행 수를 모르니 `rows` 를 따로 넘긴다.
- ★★ **`int **` 로 받으면 경고**다 — **에러가 아니고 `cc exit=0`**, 실행 파일이 나온다.\
  gcc 의 `note:` 가 정확히 말해 준다 — 「**expected `int **` but argument is of type `int (*)[4]`**」.\
  ★ **무엇을 읽게 되고 왜 위험한지는 [01번 형제](../01-declaration-syntax-and-reading/)가 정본**이다. 결론만 되짚으면 —\
  **`int **` 로 보면 배열 원소의 비트를 주소로 읽어** 엉뚱한 곳을 가리키고,\
  **죽을지 조용히 틀릴지는 그날의 데이터가 정한다.**

### 6. 감쇠가 일어나는 자리를 전부 대면 ★★

**답**

```text
   감쇠가 일어나는 자리 아홉

   ① 포인터에 초기화·대입       int *p = arr;   p = arr;
   ② 함수 인자로 넘기기          take(arr);
   ③ 산술                       arr + i,  arr - 1
   ④ 비교                       arr == p,  arr < p
   ⑤ 인덱싱                     arr[i]   (== *(arr + i) 이므로 ③의 결과)
   ⑥ 조건 연산자의 두 가지       1 ? arr : arr
   ⑦ 쉼표 연산자의 오른쪽        (arr, arr)
   ⑧ 캐스트·복합 리터럴          (int *){arr}
   ⑨ return 값으로 내보내기      return arr;   (지역 배열이면 ★ 댕글링)

   감쇠가 ★ 안 일어나는 자리 셋

   ① sizeof (그리고 _Alignof)
   ② &            -> int (*)[10]
   ③ 문자열 리터럴로 배열을 초기화할 때   char s[] = "hi";
```

- 한 줄로 — 「**배열을 식에서 쓰면 감쇠한다. 위 셋만 예외다.**」
- **`sizeof arr / sizeof arr[0]` 은 함수 안에서 `8/4 = 2`** 를 낸다.
- ★ **2 라는 값이 더 나쁘다** — **0 이나 음수였다면 바로 알았을 것**이다.\
  2 는 「길이가 2 인 배열」로 그럴듯해서 **루프가 조용히 두 번만 돈다.**

### 7. `&arr` 와 `arr` ★★

**답**

- **타입** — `arr` 은 식에서 **`int *`** 로 감쇠하고, `&arr` 은 감쇠하지 않아 **`int (*)[10]`** 이다.
- **주소값은 같다.** 실측에서 **`(void*)arr == (void*)&arr` 가 1** 이었고 `arr == &arr[0]` 도 1 이었다.
- ★★ **`sizeof` 로는 구분할 수 없다** — `sizeof &arr` 가 **8** 이라 다른 포인터와 같다.\
  ★ **구분은 보폭으로 한다** — **`arr + 1` 은 +4, `&arr + 1` 은 +40.**\
  ★ 또 하나의 방법은 **가리키는 것의 크기**다 — `int (*p2)[10] = &arr;` 로 받아 **`sizeof *p2` 가 40**.

### 8. 문자열 리터럴의 두 얼굴 ★

**답**

- **`char s[] = "hi"`** — 리터럴의 내용이 **스택의 배열로 복사**된다. `s` 의 타입은 `char[3]`.
- **`char *q = "hi"`** — 리터럴이 **감쇠**해 포인터가 된다. `q` 의 타입은 `char *`.
- **고칠 수 있는 것은 `s`** 다. 실측에서 `s[0] = 'H'` 뒤 **`Hi`** 가 찍혔다.\
  ★ **`q[0] = 'H'` 는 UB** 이고 **이 문서는 던지지 않았다**(목록의 **20번 주제**).
- **주소 대역** — `s` 가 `0x7ffe…`(스택), `q` 가 `0x5cfc…`(다른 영역)였다.\
  ★ **그것은 관찰이지 보장이 아니다.** 「문자열 리터럴이 읽기 전용 영역에 놓인다」는 **구현 정의**이고,\
  표준이 보장하는 것은 「**고치면 UB**」까지다.

### 9. 어느 도구가 무엇을 보나 ★★

**답**

| 프로그램 | gcc 무플래그 | gcc `-Wall` | gcc `+Wextra` | gcc `+pedantic` | gcc `-std=c2x +ped` | clang `-Wall -Wextra` | clang `+pedantic` |
|---|---|---|---|---|---|---|---|
| 16-a 세 꼴 `sizeof` | **2** | 2 | 2 | 2 | 2 | **2** | 2 |
| 16-b 감쇠 안 하는 셋 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 16-c `static 10` | **2** | 2 | 2 | 2 | 2 | **2** | 2 |
| 16-d 2차원 | **1** | 1 | 1 | 1 | 1 | **1** | 1 |
| 16-e 감쇠 자리 열거 | 0 | **1** | 1 | 1 | 1 | **3** | 3 |

- **경고 0건인 것은 16-b**(감쇠가 안 일어나는 셋)다. **합법이고 수상할 게 없다.**
- ★★ **`-pedantic` 이 필요한 것은 0개**다. 이 주제의 경고는 **전부 기본 또는 `-Wall`** 이다 —\
  [13번](../13-goto-cleanup-idiom/)·[14번](../14-pointers-address-dereference-and-pointer-types/)·[15번 형제](../15-pointer-arithmetic-and-indexing/)와 **정반대**다.
- **gcc 와 clang 이 서로 다른 것을 보는 자리 둘** —\
  ① **`-Wsizeof-array-decay`**(16-e) — **clang 에만 있다**(gcc 1건 대 clang 3건).\
  ② **`static` 없는 `int a[10]` 에 작은 배열**(16-c 변형) — **gcc 만 잡는다**(1건 대 0건).
- ★★★ **`int *a` 로 써 놓으면 안 잡히는 이유** — **`sizeof` 를 포인터에 쓴 것은 정상적인 코드**다.\
  도구가 잡을 수 있는 것은 **「배열처럼 써 놓고 포인터처럼 동작하는」 불일치**뿐이고,\
  처음부터 포인터로 썼으면 **불일치가 없다.** **길이를 잃었다는 사실은 도구가 아니라 계약이 말한다.**

### 10. 다섯 층과 무게중심 ★★

**답**

| 층 | 이 주제(16번) | [15번](../15-pointer-arithmetic-and-indexing/) | [13번](../13-goto-cleanup-idiom/) |
|---|---|---|---|
| **표준** | 감쇠 규칙 · **매개변수 재작성** · **감쇠 안 하는 셋** · `&arr` 의 타입 · 2차원은 바깥 한 겹만 | 스케일링 · `a[i]` == `*(a+i)` | ★★ **본체** |
| **조건부 표준** | ★ **해당 없음** | `uintptr_t` | ★ **해당 없음** |
| **구현 정의** | `sizeof(int)`=4·`sizeof(int *)`=8 · 리터럴이 읽기 전용 영역에 놓이는 것 | `sizeof(ptrdiff_t)` · GNU `sizeof(void)` | ★ **거의 없다** |
| **미명시** | ★ 같은 리터럴을 **공유하는지**(이 문서는 던지지 않았다) | 서로 다른 객체의 포인터 비교 | ★ **해당 없음** |
| **UB** | ★★ **본체** — **길이를 잃은 뒤의 경계 넘기** · `static N` 계약 위반 · 지역 배열 주소 반환 · 리터럴 수정 | ★★ **본체 넷** | ★ **둘뿐** |

- **비어 있는 칸은** 「**조건부 표준**」이다 — 감쇠에 **매크로 조건이 걸릴 것이 없다.**\
  「미명시」 칸도 거의 비어 있고, 거기 넣을 수 있는 하나(**리터럴 공유**)는 **이 문서가 던지지 않았다.**
- ★★ **[15번 형제](../15-pointer-arithmetic-and-indexing/)와 UB 의 모양이 다르다.**\
  15번은 **산술 자체가 UB**(`a + 6` 을 만들기만 해도)이고,\
  16번은 **감쇠 자체는 완전히 합법**인데 **그 결과 길이를 잃은 뒤의 접근이 UB** 다.\
  ★ **16번의 UB 는** 「**도구가 못 잡는 종류**」가 아니라 「**사람이 계약으로 막아야 하는 종류**」다.
- ★ **네 번째 창 둘** —
  - ★★★ **같은 배열을 세 꼴로 받아 `sizeof` 를 나란히 찍는 것** — **40 → 8 · 8 · 8** 을 한 화면에 놓는다.
  - **ASan** — 계약을 어긴 호출이 **`stack-buffer-overflow` at `sum10 ex.c:6`** 로 드러나고,\
    ★ **경고가 「호출부(17행)」를 가리킨 것과 달리 ASan 은 「읽은 자리(6행)」를 가리킨다.**

### 11. 경계 — 어디까지가 이 주제인가 ★

**답**

- **동적 배열의 용량·증가 전략·상환 분석** — [`data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/)가 정본이다.\
  이 주제는 **감쇠 규칙과 `sizeof` 가 달라지는 자리**까지다.
- **`int (*)[4]` 를 `int **` 로 받았을 때 무엇을 읽게 되는가** — [01번 형제](../01-declaration-syntax-and-reading/)가 정본이다.\
  이 주제는 「**감쇠가 그 타입을 만든다**」와 **진단 문구**까지다.
- **`char *q = "hi"; q[0] = 'H';`** — 목록의 **20번 주제**가 정본이다.\
  이 주제는 「**리터럴로 배열을 초기화할 때 감쇠하지 않는다**」까지이고, **수정은 던지지 않았다.**

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 컴파일러·플래그로 돌렸나 |
|---|---|---|
| 세 꼴 `sizeof` (16-a) | 밖 **40** / 안 **8·8·8** · 경고 **2건**(세 함수 중 둘) · **`int *a` 는 0건** · 플래그 없이도 켜짐 | gcc 7벌 · clang 2벌 |
| 감쇠 안 하는 셋 (16-b) | `sizeof arr`=40 · **`arr+1`=+4 ↔ `&arr+1`=+40** · `sizeof *p2`=40 · `sizeof s`=3 ↔ `sizeof q`=8 · `s[0]='H'` → `Hi` · **경고 0건** | gcc 7벌 · clang 2벌 |
| `static 10` (16-c) | 경고 **2건**(gcc `-Wstringop-overflow=`+`-Wnonnull` / clang `-Warray-bounds`+`-Wnonnull`) · **`static` 빼면 gcc 1 / clang 0** · `-O0`\~`-O2` 여섯 벌 **전부 2건** · 평범 실행 **run exit=139** · ASan **run exit=1** | gcc 10벌 · clang 5벌 · gcc `-fsanitize=address,undefined` |
| 2차원 (16-d) | 밖 **48/16/4** · 안 **8/16/4** · `a[1][0]`=5 · `int **` 는 **경고 후 exit=0** | gcc 7벌 · clang 2벌 |
| 감쇠 자리 열거 (16-e) | 여덟 `sizeof` 값 · gcc **1건**(`-Wunused-value`) 대 clang **3건**(`-Wsizeof-array-decay`) · `sizeof (+arr)` 는 **양쪽 다 error cc exit=1** | gcc 7벌 · clang 4벌 |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3 · glibc)에서만** 그렇다.

- **`sizeof(int)`=4·`sizeof(int *)`=8** 이라 **40 과 8**, **48/16/4** 인 것 — ★ **구현 정의**다.
- **문자열 리터럴이 스택과 다른 대역에 놓이는 것** — ★ **관찰이지 보장이 아니다.**
- **`sum10(small)` 이 `34` 를 찍은 것** — ★ **UB 의 산물이라 아무 근거도 못 된다.**
- **`-Wsizeof-array-decay` 가 clang 에만 있는 것**, **`static` 없이 gcc 만 잡는 것** — 진단 구현의 분류다.
- **`-Wstringop-overflow=` 라는 플래그 이름이 배열 인자에 붙는 것** — gcc 의 분류다.

**감쇠 규칙 자체는 구현 의존이 아니다.** 매개변수 재작성 · 감쇠가 안 일어나는 셋 · `&arr` 의 타입 ·\
2차원이 바깥 한 겹만 잃는 것은 **어느 C 구현에서도 같다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `char *q = "hi"; q[0] = 'H';`(목록의 **20번 주제**) · `return arr;`(지역 배열, 목록의 **57번 주제**) ·\
  **VLA 매개변수**(`void f(int n, int a[n])`, 목록의 **18번 주제**) · **같은 리터럴의 공유 여부**(미명시) ·\
  `int a[static 10]` 이 **최적화를 바꾸는지**(어셈블리를 안 찍었다) · **포인터 변수를 넘겼을 때** 계약 검사가 꺼지는 것을 실측으로.
- ★ **`_Alignof` 는 타입 형태(`_Alignof(int[10])`)로만 던졌다** — C 에서 `_Alignof` 의 피연산자가 **타입 이름**이기 때문이고,\
  **식 형태로는 던지지 않았다.**
- **못 잰 것** — ★ **「`-Wsizeof-array-argument` 가 어느 플래그 집합 소속인가」.**\
  **플래그 없이도 나온다**는 것은 실측했지만, 그것이 「기본 켜짐」인지 「다른 무언가가 켠 것」인지는\
  **컴파일러 문서를 열지 않고는 가를 수 없어** 이 문서는 **관찰까지만** 적었다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- **gcc 가 `-Wsizeof-array-decay` 에 해당하는 진단을 갖게 됐는지**(지금은 clang 만).
- **clang 이 `static` 없는 `int a[10]` 도 잡게 됐는지**(지금은 gcc 만).
- `-Wincompatible-pointer-types` 가 **기본에서 에러로 승격됐는지** — 지금은 **경고에 `cc exit=0`** 이다.\
  ★ 이 머신에 gcc 13.3.0 뿐이라 **다음 버전에서 어떤지는 확인할 수 없었다.**
- **`sizeof` 값들은 다른 ISA 로 갈 때** 다시 잰다.
- **감쇠 규칙 자체는 다시 돌릴 필요가 없다** — C89 이후 바뀐 적이 없다.
