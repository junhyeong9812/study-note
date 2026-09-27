# c/syntax/15 — 포인터 산술과 인덱싱: 「**`a[i]` 는 문법이 아니라 축약이다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고·sanitizer 진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 작업 디렉터리는 `/tmp/c13`, 소스 파일명은 언제나 `ex.c` 다.\
> ★★ **실행 블록은 `./x 2>&1 | cat`(또는 `| sed -n '1,/^SUMMARY/p'`)으로 받았다** —\
> sanitizer 는 stderr, `printf` 는 stdout 이라 순서가 실행 환경에 달린다. 섞이는 프로그램에는 `setvbuf(…, _IONBF, …)` 를 넣어 고정했다.
> ★★ **UB 가 걸린 블록의 값은 근거가 아니다** — 「갈렸다」는 사실이 근거다. 블록마다 한 줄로 적어 두었다.
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | `%p` 주소값 · ASan 의 `pc`/`bp`/`sp` · PID · `BuildId` | 주소들 **사이의 차이** · `sizeof` 값 |
> | ★ **UB 가 만든 값**(`*end` · `a[10]` · `NULL+1`) | ★ **그 값이 「갈린다」는 사실** |
> | ASan 리포트의 Shadow bytes 와 메모리 덤프 | **`파일:줄:칸`** · 진단 본문 · 플래그 이름 · **종료 코드** |

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 세 타입의 포인터에 각각 1 을 더하면 — **한 걸음이 아니라 한 칸** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, exit=0) =====
타입      sizeof  p        p+1      주소 차이(바이트)
int           4  0x7ffff6bd1360  0x7ffff6bd1364  4
char          1  0x7ffff6bd13b3  0x7ffff6bd13b4  1
double        8  0x7ffff6bd1380  0x7ffff6bd1388  8

&ai[4] - &ai[1] = 3   (원소 개수)
바이트로는       = 12
sizeof(ptrdiff_t) = 8   sizeof(size_t) = 8
&ai[1] - &ai[4] = -3   (음수가 나온다)
```

> ★ **대조할 것은 숫자가 아니라 성질이다.** 주소는 ASLR 로 실행마다 바뀐다.\
> 근거는 **「주소 차이 == `sizeof *p`」** 세 줄과 **뺄셈이 3 을 낸다**는 것이다.

**왜 그런가**

```text
   char *pc      [0][1][2][3][4]        pc+1 은 +1 바이트
   int *pi       [ 0 ][ 1 ][ 2 ]        pi+1 은 +4 바이트
   double *pd    [   0   ][   1   ]     pd+1 은 +8 바이트

   규칙 :  (p + n) 의 주소 = p 의 주소 + n * sizeof(*p)
   뺄셈 :  (q - p) = (주소 차이) / sizeof(*p)   ->  12 / 4 = 3
```

- **주소 차이가 `sizeof *p` 와 정확히 같다** — `4` · `1` · `8`.\
  **포인터 산술의 단위는 바이트가 아니라** 「**가리키는 타입 한 개**」다.
- **`&ai[4] - &ai[1]` 은 3**, **바이트로는 12** 다. 뺄셈은 스케일링의 **역연산**이다.
- **`&ai[1] - &ai[4]` 는 `-3`** 이다 — ★ **`ptrdiff_t` 가 부호 있는 타입**이라는 뜻이다.\
  `size_t` 로 받으면 **거대한 양수**가 된다.
- ★ **다시 돌리면 달라지는 것은 주소 세 쌍**이다. `sizeof`·차이·뺄셈 결과는 안 바뀐다.

### 2. 인덱싱을 일곱 가지로 써 보면 — **일곱 개가 다 컴파일된다** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘main’:
ex.c:17:35: warning: self-comparison always evaluates to true [-Wtautological-compare]
   17 |            a[i] == *(a + i), a[i] == i[a], &a[i] == &i[a]);
      |                                   ^~
ex.c:17:50: warning: self-comparison always evaluates to true [-Wtautological-compare]
   17 |            a[i] == *(a + i), a[i] == i[a], &a[i] == &i[a]);
      |                                                  ^~
a[i]      = 30
*(a + i)  = 30
*(i + a)  = 30
i[a]      = 30   <- ★ 되는가?
p[i]      = 30
i[p]      = 30
2[a]      = 30

같은가 : a[i]==*(a+i) 1   a[i]==i[a] 1   &a[i]==&i[a] 1
i[a] = 99 후 : a[2] = 99
===== clang -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c:17:35: warning: self-comparison always evaluates to true [-Wtautological-compare]
   17 |            a[i] == *(a + i), a[i] == i[a], &a[i] == &i[a]);
      |                                   ^
1 warning generated.
(출력은 gcc 와 바이트 단위로 같다)
```

**왜 그런가**

```text
   표준이 정의하는 것 :  a[i]  ==  *(a + i)
   덧셈은 교환 가능   :  *(a+i) == *(i+a) == i[a]

   ★ 그래서 2[a] 도 되고 좌변으로도 쓸 수 있다.
     "배열의 2번" 이 아니라 "주소 + 2 칸" 이기 때문이다.
```

- **일곱 개가 다 컴파일되고 전부 30** 이다. `i[a]`·`i[p]`·`2[a]` 까지.
- **경고는 gcc 2건, clang 1건**이고 플래그는 둘 다 **`-Wtautological-compare`**(`-Wall` 소속).\
  clang 은 `&a[i] == &i[a]` 쪽을 잡지 않았다 — **잡는 범위가 다르다.**
- ★★★ **그 경고 이름이 증명한다** — **`self-comparison`**(자기 자신과의 비교).\
  **컴파일러가 `a[i]` 와 `i[a]` 를 같은 식으로 본다**는 뜻이다. 사람이 주장한 게 아니라 **도구가 말했다.**
- **`i[a] = 99` 가 된다** — `a[2]` 가 99 가 됐다. **완전히 같은 식**이라 좌변으로도 쓰인다.
- ★ **이 사실의 쓸모는 `i[a]` 를 쓰는 데 있지 않다.**\
  쓸모는 「**인덱싱이 주소 계산일 뿐이고 경계 검사가 없다**」는 함의에 있다 — 4번·5번 답의 UB 가 거기서 나온다.

### 3. 배열 끝 한 칸 뒤를 만들고 읽으면 — **만드는 건 합법, 읽는 건 UB** ★★

**출력**

```text
===== 소스: ex.c (15-c) =====
#include <stdio.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);   /* ★ 출력 순서를 고정한다 — 파이프로 받아도 같게 */
    int a[5] = {10, 20, 30, 40, 50};
    int *end = a + 5;              /* ★ 한 칸 뒤 포인터 — 합법이다 */

    printf("a      = %p\n", (void *)a);
    printf("a + 5  = %p   (끝 한 칸 뒤 — 만들어도 되고 비교해도 된다)\n", (void *)end);
    printf("end - a = %td\n", end - a);
    printf("end > a ? %d\n", end > a);

    int sum = 0;
    for (int *p = a; p != end; p++) sum += *p;   /* 관용구 — end 를 역참조하지 않는다 */
    printf("합 = %d\n", sum);

    printf("\n이제 역참조한다 -> ★ UB\n");
    printf("*end = %d\n", *end);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, cc exit=0 · run exit=0) =====
a      = 0x7ffd07decd70
a + 5  = 0x7ffd07decd84   (끝 한 칸 뒤 — 만들어도 되고 비교해도 된다)
end - a = 5
end > a ? 1
합 = 150

이제 역참조한다 -> ★ UB
*end = 32765
```

```text
===== gcc -std=c17 -g -fsanitize=address,undefined · ./x 2>&1 | sed -n '1,/^SUMMARY/p'  (run exit=1) =====
a      = 0x7d17eea00020
a + 5  = 0x7d17eea00034   (끝 한 칸 뒤 — 만들어도 되고 비교해도 된다)
end - a = 5
end > a ? 1
합 = 150

이제 역참조한다 -> ★ UB
ex.c:18:5: runtime error: load of address 0x7d17eea00034 with insufficient space for an object of type 'int'
0x7d17eea00034: note: pointer points here
  32 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00
              ^ 
=================================================================
==3681571==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x7d17eea00034 at pc 0x562b23d957e0 bp 0x7fffc09e9770 sp 0x7fffc09e9760
READ of size 4 at 0x7d17eea00034 thread T0
    #0 0x562b23d957df in main /tmp/c13/ex.c:18
    #1 0x7d17f0e2a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #2 0x7d17f0e2a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #3 0x562b23d95264 in _start (/tmp/c13/xs+0x2264) (BuildId: 9133f346a3176b3e9d14295232229cb6b620f63b)

Address 0x7d17eea00034 is located in stack of thread T0 at offset 52 in frame
    #0 0x562b23d95338 in main /tmp/c13/ex.c:3

  This frame has 1 object(s):
    [32, 52) 'a' (line 5) <== Memory access at offset 52 overflows this variable
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-buffer-overflow /tmp/c13/ex.c:18 in main
```

> ★ **대조할 것은 숫자가 아니라 성질이다.** 주소·PID·`BuildId` 와 **`*end` 의 값은 실행마다 바뀐다**(두 블록은 다른 판이다).\
> 근거는 **`a+5` 를 만들고 비교하는 동안 진단 0줄** · **18행에서만 두 도구가 동시에 말한다** · **run exit 이 0 에서 1 로 갈린다**는 것이다.\
> ★ ASan 리포트는 **`SUMMARY` 줄까지** 받았다(`sed -n '1,/^SUMMARY/p'`).

**왜 그런가**

```text
   +-----+-----+-----+-----+-----+  - - - +
   |  0  |  1  |  2  |  3  |  4  |  a+5   |
   +-----+-----+-----+-----+-----+  - - - +
    ^                             ^
    a                             ★ 가리키는 것·비교·뺄셈 = 합법
                                  ★ 읽는 것 = UB
```

- **앞의 세 줄은 `5` · `1` · `150`** 이고 **진단이 0줄**이다. 합법이다.
- **평범한 실행은 안 죽는다** — `*end` 에 쓰레기값(`32765`)을 찍고 **`run exit=0`** 으로 끝났다.\
  ★ **「안 터졌다」는 「안전하다」가 아니다.**
- **ASan+UBSan 은 18행(`*end`)에서만** 말한다 — UBSan 이 `insufficient space for an object of type 'int'`,\
  ASan 이 `stack-buffer-overflow` 와 `[32, 52) 'a' (line 4)`(배열이 32\~52 인데 52 를 읽었다).
- ★ **한 문장으로** — 「**끝 한 칸 뒤까지는 「존재하는 주소」이고, 그 자리에 객체는 없다.**\
  그래서 `for (p = a; p != a + n; p++)` 가 안전하다 — `p` 가 `a+n` 이 되는 순간 **역참조 없이** 끝난다.」

### 4. 배열 범위를 넘는 포인터를 만들면 — **gcc 는 만들 때를 못 본다** ★★★

**출력**

```text
===== 소스: ex.c (15-d) =====
#include <stdio.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);   /* ★ 출력 순서를 고정한다 — 파이프로 받아도 같게 */
    int a[5] = {1, 2, 3, 4, 5};
    volatile int i = 10;
    int *p = a + i;                 /* ★ UB 1 — 배열 + 한 칸 뒤 를 넘는 포인터를 "만드는" 것 */
    printf("a + 10 = %p  (역참조는 하지 않았다)\n", (void *)p);
    printf("a[10] = %d   <- 여기서 읽는다\n", a[i]);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, cc exit=0 · run exit=0) =====
a + 10 = 0x7ffc923c9b38  (역참조는 하지 않았다)
a[10] = 325231050   <- 여기서 읽는다
```

```text
===== clang -std=c17 -g -fsanitize=undefined · ./x 2>&1 | cat  (run exit=0) =====
ex.c:7:16: runtime error: index 10 out of bounds for type 'int[5]'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior ex.c:7:16 
a + 10 = 0x7ffee0029338  (역참조는 하지 않았다)
ex.c:9:53: runtime error: index 10 out of bounds for type 'int[5]'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior ex.c:9:53 
a[10] = 1317183946   <- 여기서 읽는다
```

```text
===== gcc -std=c17 -g -fsanitize=address,undefined · ./x 2>&1 | sed -n '1,/^SUMMARY/p'  (run exit=1) =====
a + 10 = 0x7c6008200068  (역참조는 하지 않았다)
ex.c:9:54: runtime error: index 10 out of bounds for type 'int [5]'
ex.c:9:5: runtime error: load of address 0x7c6008200068 with insufficient space for an object of type 'int'
0x7c6008200068: note: pointer points here
 00 00 00 00  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  00 c0 0f 08 60 7c 00 00  00 00 00 00
              ^ 
=================================================================
==3681600==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x7c6008200068 at pc 0x6156008d869c bp 0x7fff1ec817d0 sp 0x7fff1ec817c0
READ of size 4 at 0x7c6008200068 thread T0
    #0 0x6156008d869b in main /tmp/c13/ex.c:9
    #1 0x7c600a62a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #2 0x7c600a62a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #3 0x6156008d8244 in _start (/tmp/c13/xs+0x1244) (BuildId: 6320b50f35ce20e097017f67142a880b9d12d33a)

Address 0x7c6008200068 is located in stack of thread T0 at offset 104 in frame
    #0 0x6156008d8318 in main /tmp/c13/ex.c:3

  This frame has 2 object(s):
    [48, 52) 'i' (line 6)
    [64, 84) 'a' (line 5) <== Memory access at offset 104 overflows this variable
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-buffer-overflow /tmp/c13/ex.c:9 in main
```

```text
===== 소스: ex.c (15-g) =====
#include <stdio.h>
int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);   /* ★ 출력 순서를 고정한다 — 파이프로 받아도 같게 */
    int a[5] = {1, 2, 3, 4, 5};
    volatile int i = 10;
    int *p = a + i;                 /* 만들기만 한다 — 역참조하지 않는다 */
    printf("만들어진 포인터 = %p\n", (void *)p);
    return 0;
}
```

```text
===== 포인터를 만들기만 하는 판 (ex.c 15-g) — gcc · ./x 2>&1 | cat  (run exit=0) =====
만들어진 포인터 = 0x77b92d000068
```

```text
===== 포인터를 만들기만 하는 판 (ex.c 15-g) — clang · ./x 2>&1 | cat  (run exit=0) =====
ex.c:6:16: runtime error: index 10 out of bounds for type 'int[5]'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior ex.c:6:16 
만들어진 포인터 = 0x7633aba00048
```

```text
===== 같은 프로그램에서 volatile 만 뗀 판 — warning: 줄 수 =====
gcc   -std=c17 -Wall -Wextra -pedantic -O0 :  0 건
gcc   -std=c17 -Wall -Wextra -pedantic -O2 :  2 건   [-Warray-bounds=]
clang -std=c17 -Wall -Wextra -pedantic -O0 :  0 건
clang -std=c17 -Wall -Wextra -pedantic -O2 :  0 건
```

> ★ **`a[10]` 의 값은 근거가 아니다.** UB 라 실행마다·빌드마다 달라진다(위 두 블록에서 `325231050` ↔ `1317183946`).\
> 근거는 **어느 행에서 어느 도구가 말하는가**다.

**왜 그런가**

```text
   7행 :  int *p = a + i;     <- ★ 포인터를 "만드는" 것. 이미 UB 다.
   9행 :  a[i]                <- 읽는 것. 역시 UB.

   gcc   sanitizer :  7행 ★ 침묵      9행에서만 말한다
   clang sanitizer :  7행 ★ 말한다    9행에서도 말한다
```

- **컴파일 경고는 0건**이다 — 일곱 조합 전부. 첨자가 `volatile` 이라 **컴파일 타임에 알 수 없다.**
- ★★★ **gcc 는 7행을 못 본다.** 9행(`a[i]`)에서만 `index 10 out of bounds` 를 낸다.\
  **clang 은 7행에서 이미** 낸다 — 포인터 **형성** 자체를 UB 로 본다.
- ★★ **그래서 「만들기만 하고 안 읽는」 코드**를 따로 던져 보면 —\
  **gcc 는 진단 0줄에 `run exit=0`**, **clang 은 `ex.c:6:16: runtime error: index 10 out of bounds`** 였다.\
  **UB 인데 gcc 조합에서는 아무 흔적이 없다.**
- ★ **`volatile` 을 떼면 이야기가 달라진다** — **gcc `-O2` 에서만 2건**(`-Warray-bounds=`)이 난다.\
  `-O0` 은 0건이고 **clang 은 어느 수준에서도 0건**이다.\
  ★ **한 최적화 수준만 돌리고 「도구가 잡는다/못 잡는다」를 단정하면 안 된다.**

### 5. 서로 다른 배열의 포인터를 빼고 비교하면 — **답이 셋으로 갈린다** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (cc exit=0 · run exit=0) =====
ex.c: In function ‘main’:
ex.c:9:71: warning: comparison between two arrays [-Warray-compare]
    9 |     printf("b < a ? %d   (서로 다른 배열끼리의 비교도 미명시다)\n", b < a);
      |                                                                       ^
ex.c:9:71: note: use ‘&b[0] < &a[0]’ to compare the addresses
b - a = 4
b < a ? 0   (서로 다른 배열끼리의 비교도 미명시다)
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic (cc exit=0 · run exit=0) =====
ex.c:9:87: warning: array comparison always evaluates to a constant [-Wtautological-compare]
    9 |     printf("b < a ? %d   (서로 다른 배열끼리의 비교도 미명시다)\n", b < a);
      |                                                                       ^
1 warning generated.
b - a = -4
b < a ? 1   (서로 다른 배열끼리의 비교도 미명시다)
```

```text
===== 같은 소스를 40벌로 던진 결과 — b - a 의 값 =====
gcc   -O0/-O1/-O2/-O3/-Os                             b - a = 4
gcc   + -fsanitize=undefined                          b - a = 4
gcc   + -fsanitize=address (또는 address,undefined)    b - a = 8
clang -O0/-O1/-O2/-O3/-Os                             b - a = -4
clang + -fsanitize=undefined                          b - a = -4
clang + -fsanitize=address (또는 address,undefined)    b - a = 8

★ 뺄셈에 대한 sanitizer 진단은 한 줄도 없었다.
★ "b < a" 의 값도 갈린다 — gcc 는 0, clang 은 1.
```

> ★★★ **대조할 것은 값이 아니라 「세 답으로 갈린다」는 사실이다.**\
> `4`·`-4`·`8` 중 어느 하나를 정답으로 외우면 틀린 것을 외우는 것이다.

**왜 그런가**

```text
   갈린 축은 ★ 최적화 수준이 아니었다.

   최적화 수준 5벌 :  전부 같았다
   컴파일러       :  gcc 4  ↔  clang -4     <- 두 배열의 배치 순서가 다르다
   ASan 여부      :  켜면 둘 다 8            <- 레드존이 사이에 끼어 배치가 벌어진다
```

- **경고는 1건**이고 **`b < a`(9행)** 에 대한 것이다. **`b - a`(7행) 에는 아무 말도 없다.**\
  플래그 이름도 문구도 다르다 — **gcc 는 `-Warray-compare`**(「comparison between two arrays」),\
  **clang 은 `-Wtautological-compare`**(「array comparison always evaluates to a constant」).\
  ★ 그리고 **그 비교의 값마저 갈린다** — **gcc 0, clang 1**. 뺄셈은 UB, 비교는 미명시인데 **둘 다 답이 달라졌다.**
- ★★★ **`b - a` 는 `4`·`-4`·`8` 세 값이 나왔다.** 같은 소스, 같은 머신이다.\
  ★ **갈린 축은 최적화 수준이 아니라** 「**컴파일러 + ASan 여부**」였다 — ASan 이 스택 객체 사이에 **레드존**을 끼워 배치를 벌린다.
- ★★★ **sanitizer 는 뺄셈에 대해 침묵**한다. **아무 도구도 이 UB 를 말하지 않는다.**
- ★ **gcc 의 `note:` 는 함정이다.** 「`&b[0] < &a[0]` 을 쓰라」고 권하는데,\
  **그렇게 고쳐도 서로 다른 객체의 포인터 비교라 미명시**다. **경고를 끄는 조언이지 UB 를 없애는 조언이 아니다.**
- **거리를 재야 하면 `uintptr_t` 로 캐스트해 정수 뺄셈**을 한다 — 그것은 **구현 정의**이지 UB 가 아니다.

### 6. 널 포인터에 정수를 더하면 — **clang 만 본다** ★★

**출력**

```text
===== 소스: ex.c (15-f) =====
#include <stdio.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);   /* ★ 출력 순서를 고정한다 — 파이프로 받아도 같게 */
    int *n = NULL;
    volatile int k = 1;
    int *p = n + k;                 /* ★ UB 3 — 널 포인터에 0 아닌 값을 더한다 */
    printf("NULL + 1 = %p\n", (void *)p);
    int *q = n + 0;                 /* C17 에서는 이것도 UB, C23 에서 정의됨 */
    printf("NULL + 0 = %p\n", (void *)q);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, cc exit=0 · run exit=0) =====
NULL + 1 = 0x4
NULL + 0 = (nil)
```

```text
===== gcc -std=c17 -g -fsanitize=address,undefined · ./x 2>&1 | cat  (run exit=0) =====
NULL + 1 = 0x4
NULL + 0 = (nil)
```

```text
===== gcc -std=c17 -g -fsanitize=pointer-overflow · ./x 2>&1 | cat  (run exit=0) =====
NULL + 1 = 0x4
NULL + 0 = (nil)
```

```text
===== clang -std=c17 -g -fsanitize=undefined · ./x 2>&1 | cat  (run exit=0) =====
ex.c:7:16: runtime error: applying non-zero offset 4 to null pointer
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior ex.c:7:16 
NULL + 1 = 0x4
ex.c:9:16: runtime error: applying zero offset to null pointer
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior ex.c:9:16 
NULL + 0 = (nil)
```

★ **`-std=c2x` 로 바꿔 던진 판도 한 글자도 같았다** — C23 이 `NULL + 0` 을 정의했는데도 clang 18 은 여전히 두 줄을 낸다.

> ★ **`0x4` 는 근거가 아니다.** `0 + 1 * sizeof(int)` 를 그냥 계산한 값이고 UB 라 보장이 없다.\
> ★ **gcc 두 블록에 진단이 한 줄도 없는 것은** 「**생략**」이 아니라 「**나오지 않은 것**」이다 —\
> `2>&1 | cat` 로 받았으므로 stderr 까지 포함한 전부가 저 두 줄이다.

**왜 그런가**

- **두 줄은 `0x4` 와 `(nil)`** 을 찍고 **컴파일 경고는 0건**이다.
- ★★★ **gcc 의 `-fsanitize=undefined,address` 는 0줄**이다.\
  **`-fsanitize=pointer-overflow` 를 직접 켜도 0줄**이었다 — **플래그는 받아 주는데 동작하지 않는다.**\
  ★ **「플래그가 받아졌다」는 「검사가 켜졌다」가 아니다.**
- ★★ **clang 은 2줄**을 낸다 — `applying non-zero offset 4 to null pointer`(7행)와\
  `applying zero offset to null pointer`(9행). **두 자리를 따로 본다.**
- ★ **`-std=c2x` 로 바꿔도 9행이 조용해지지 않는다.** 두 판의 출력이 **한 글자도 다르지 않았다.**\
  C23 이 **`NULL + 0` 을 정의된 동작으로 바꿨는데도** clang 18 은 여전히 보고한다.\
  ★ **명세가 바뀐 것과 도구가 따라온 것은 다른 문제**다 — 도구의 기본 표준이 무엇이든, 검사기 구현이 그대로면 같은 줄이 나온다.

### 7. `void *` 로 산술을 하면 — **GNU 확장이다**

**출력**

```text
===== gcc -std=c17 -Wall -Wextra (경고 0 건, exit=0) =====
(아무것도 나오지 않는다)
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘main’:
ex.c:8:43: warning: invalid application of ‘sizeof’ to a void type [-Wpointer-arith]
    8 |     printf("sizeof(void) = %zu\n", sizeof(void));   /* 표준에 없다 */
      |                                           ^~~~
ex.c:9:19: warning: pointer of type ‘void *’ used in arithmetic [-Wpointer-arith]
    9 |     void *v1 = vp + 1;                              /* 표준에 없다 */
      |                   ^
===== clang -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c:8:36: warning: invalid application of 'sizeof' to a void type [-Wpointer-arith]
    8 |     printf("sizeof(void) = %zu\n", sizeof(void));   /* 표준에 없다 */
      |                                    ^     ~~~~~~
ex.c:9:19: warning: arithmetic on a pointer to void is a GNU extension [-Wgnu-pointer-arith]
    9 |     void *v1 = vp + 1;                              /* 표준에 없다 */
      |                ~~ ^
2 warnings generated.
===== 실행 (gcc) =====
sizeof(void) = 1
vp        = 0x7ffe0d1a6bd0
vp + 1    = 0x7ffe0d1a6bd1   (차이 1 바이트)
*(char*)(vp+1) = 1
```

**왜 그런가**

- **`gcc -Wall -Wextra` 는 0건**, **`+pedantic` 은 2건**이다. clang 도 같은 모양이다.
- **`sizeof(void)` 가 1** 이라 **`vp + 1` 이 1바이트** 간다 — GNU 확장이 그렇게 정했다.\
  **ISO C 에는 둘 다 없다** — `void` 는 **크기가 없는 타입**이라 스케일링할 값이 없다.
- ★ **clang 의 진단이 한 가지를 더 말한다** — 「**a GNU extension**」이라고 **이름을 붙인다.**\
  gcc 는 「`void *` 가 산술에 쓰였다」까지만 말한다. **「표준에 없다」와 「이 확장이다」는 다른 정보**다.
- **표준 안에서 바이트 단위로 걸으려면 `unsigned char *`** 를 쓴다.\
  `char *` 도 되지만 **부호가 구현 정의**라 값을 읽을 때 갈린다.

### 8. `*p++` 와 `(*p)++` 와 `*++p` ★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, exit=0) =====
*p++   = 10,  p - arr = 1
(*p)++ = 10,  arr[0] = 11,  p - arr = 0
*++p   = 20,  p - arr = 1
```

**왜 그런가**

```text
   *p++     ==  *(p++)   ->  값 10, ★ 포인터가 한 칸       p - arr = 1
   (*p)++              ->  ★ 값이 11, 포인터는 그대로       p - arr = 0
   *++p                ->  먼저 한 칸 가고 읽는다 -> 20      p - arr = 1
```

- **`*p++` 는 포인터가**, **`(*p)++` 는 값이**, **`*++p` 는 포인터가 먼저** 움직인다.\
  `p - arr` 가 각각 **1 · 0 · 1** 이다.
- **`*p++` 가 `*(p++)` 인 근거는 우선순위**다 — **후위 `++` 가 단항 `*` 보다 세다.**\
  정본은 [09번 형제](../09-operator-precedence-and-associativity/)이고 여기서는 결론만 되짚었다.
- ★ **한 `printf` 안에서 값과 `p - arr` 를 같이 재면 안 된다** — **함수 인자의 평가 순서가 미명시**라\
  `p` 가 증가하기 전에 읽힐지 후에 읽힐지 정해져 있지 않다([10번 형제](../10-evaluation-order-and-sequence-points/)).\
  ★ [09번 형제](../09-operator-precedence-and-associativity/)에 **실제로 값이 갈린 실측**이 있다. 그래서 이 문서는 **문을 나눠서** 쟀다.

### 9. `ptrdiff_t` 를 잘못 받으면 ★

**출력**

```text
===== 소스: ex.c (15-j) =====
#include <stdio.h>
#include <stddef.h>

int main(void) {
    int ai[5] = {10,20,30,40,50};
    ptrdiff_t d = &ai[1] - &ai[4];
    size_t    s = (size_t)(&ai[1] - &ai[4]);
    printf("ptrdiff_t 로 : %td\n", d);
    printf("size_t 로    : %zu\n", s);
    printf("int 로 %%d    : %d\n", (int)d);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, exit=0) =====
ptrdiff_t 로 : -3
size_t 로    : 18446744073709551613
int 로 %d    : -3
```

```text
===== 소스: ex.c (15-k) =====
#include <stdio.h>
#include <stddef.h>
int main(void) {
    int ai[5] = {10,20,30,40,50};
    printf("%d\n", &ai[4] - &ai[1]);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘main’:
ex.c:5:14: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘long int’ [-Wformat=]
    5 |     printf("%d\n", &ai[4] - &ai[1]);
      |             ~^     ~~~~~~~~~~~~~~~
      |              |            |
      |              int          long int
      |             %ld
```

**왜 그런가**

- **`size_t` 로 받으면 `-3` 이 `18446744073709551613` 이 된다** — 부호가 없어 **2⁶⁴ - 3** 으로 읽힌다.\
  루프 조건에 넣으면 **끝나지 않는다.**
- **서식 지정자는 `%td`** 다. `%d` 로 찍으면 `-Wformat=` 이 잡고, ★ **gcc 가 실제 타입을 `long int` 라고 말한다** —\
  이 환경에서 `ptrdiff_t` 가 `long int` 라는 뜻이고 **그것 자체가 구현 정의**다.
- ★ **`sizeof(ptrdiff_t)` 는 표준이 정하지 않는다.** 이 환경에서 **8** 이고 `sizeof(size_t)` 도 8 이었지만\
  **둘이 같다는 것도 보장이 아니다.**

### 10. 어느 도구가 무엇을 보나 ★★★

**답**

| 사실 | 층 | gcc 컴파일 | clang 컴파일 | gcc sanitizer | clang sanitizer |
|---|---|---|---|---|---|
| 끝 한 칸 뒤 **형성** | 표준 | 0건 | 0건 | **0줄** | **0줄** |
| 끝 한 칸 뒤 **역참조** | **UB** | **0건** | **0건** | UBSan + ASan | UBSan + ASan |
| 범위 밖 포인터 **형성** | **UB** | **0건** | **0건** | ★ **0줄** | ★ **1줄** |
| 범위 밖 **읽기**(변수 첨자) | **UB** | **0건** | **0건** | UBSan + ASan | UBSan + ASan |
| 범위 밖 **읽기**(상수 첨자) | **UB** | ★ `-O2` **2건** | ★ **0건** | — | — |
| 다른 배열 **뺄셈** | **UB** | **0건** | **0건** | ★ **0줄** | ★ **0줄** |
| 다른 배열 **비교** | 미명시 | 1건 | 1건 | 0줄 | 0줄 |
| 널 포인터 산술 | **UB** | **0건** | **0건** | ★ **0줄** | ★ **2줄** |
| `void *` 산술 | 표준 밖 | `+pedantic` **2건** | `+pedantic` **2건** | — | — |

- **UB 네 자리** — ① **끝 한 칸 뒤 역참조** ② **그 범위를 넘는 포인터 형성**(읽지 않아도)\
  ③ **서로 다른 배열의 포인터 뺄셈** ④ **널 포인터 산술**.
- ★★★ **컴파일러 경고가 나는 것은 0개**다. 상수 첨자 + gcc `-O2` 라는 **아주 좁은 조건**에서만 하나가 잡힌다.
- **gcc sanitizer 와 clang sanitizer 가 다른 답을 내는 자리 둘** —\
  ① **포인터 형성**(gcc 0줄, clang 1줄) ② **널 포인터 산술**(gcc 0줄, clang 2줄).\
  ★ **둘 다 clang 이 더 본다.**
- ★★★ **아무 도구도 안 잡는 자리는** 「**다른 배열끼리 뺄셈**」이다.\
  **드러내는 방법은** 「**답이 갈리는지 보는 것**」뿐이었다 — 40벌을 던져 **4 · -4 · 8** 이 나왔다.\
  **진단 대신 불일치가 증거**다.

### 11. 다섯 층과 무게중심 ★★

**답**

| 층 | 이 주제(15번) | [14번](../14-pointers-address-dereference-and-pointer-types/) | [13번](../13-goto-cleanup-idiom/) |
|---|---|---|---|
| **표준** | 스케일링 · `q-p` · **`a[i]` == `*(a+i)`** · 끝 한 칸 뒤의 합법성 | ★★ **본체** | ★★ **본체** |
| **조건부 표준** | `uintptr_t`(거리 재기에 쓴다) | ★ `uintptr_t`/`intptr_t` | ★ **해당 없음** |
| **구현 정의** | `sizeof(ptrdiff_t)`·`sizeof(size_t)` · 포인터 표현 · GNU `sizeof(void)==1` | 포인터 크기·표현 | ★ **거의 없다** |
| **미명시** | ★ **서로 다른 객체의 포인터 비교** · 두 배열의 상대 배치 | 지역 변수의 스택 배치 | ★ **해당 없음** |
| **UB** | ★★★ **본체 넷** | `%p` 오용 · 널 역참조 | ★ **둘뿐** |

- **미명시 칸에 들어가는 것은 `b < a`**(서로 다른 객체의 포인터 비교)다.\
  ★ **왜 UB 가 아닌가** — **결과가 0 이거나 1 이거나 둘 중 하나**이고, **그 이상 나쁜 일은 없다.**\
  UB 는 「**아무 일이나 해도 된다**」이고 미명시는 「**몇 가지 중 하나**」다. 뺄셈(`b - a`)은 UB, 비교(`b < a`)는 미명시다.
- ★★ **층 분포가 13·14번과 정반대**다.\
  13번은 **표준이 본체**고 UB 가 둘뿐, 14번은 **타입 규칙이 본체**다.\
  **15번은 UB 가 본체**이고, ★ **그 UB 들이 전부 14번의 타입 규칙 위에 서 있다** —\
  「한 칸이 몇 바이트인가」가 정해져야 「범위를 넘었다」를 말할 수 있다.
- ★ **네 번째 창 둘** —
  - **`ptrdiff_t` 와 주소 차이** → 「+1 이 몇 바이트인가」를 **숫자로** 만들었다.\
    ★ **주소값이 아니라 차이를 근거로 삼아** ASLR 을 견딘다.
  - ★★★ **같은 소스를 40벌로 던져 「답이 갈리는지」 보는 것** →\
    **진단이 하나도 없는 UB**(다른 배열끼리 뺄셈)를 **4 · -4 · 8** 이라는 불일치로 드러냈다.\
    ★ 그러면서 「**갈린 축이 최적화 수준이 아니다**」도 같이 나왔다 — 처방이 아니라 **전수로 던져야** 알 수 있었다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 컴파일러·플래그로 돌렸나 |
|---|---|---|
| 스케일링 (15-a) | 주소 차이 **4/1/8** == `sizeof *p` · `&ai[4]-&ai[1]` = **3**(바이트 12) · 뒤집으면 **-3** · `sizeof(ptrdiff_t)`=8 | gcc 7벌 |
| `i[a]` (15-b) | 일곱 식 전부 **30** · 등식 셋이 전부 1 · `i[a]=99` 가 `a[2]` 를 바꿈 · gcc **2건** / clang **1건** `-Wtautological-compare` | gcc 7벌 · clang 2벌 |
| 끝 한 칸 뒤 (15-c) | `end-a`=5 · `end>a`=1 · 합 **150** · **형성·비교는 진단 0줄** · `*end` 에서만 **UBSan+ASan** | gcc 7벌 · gcc `-fsanitize=address,undefined` |
| 범위 밖 (15-d·15-g) | 컴파일 **0건** · **gcc 는 8행만 / clang 은 6행부터** · 형성만 하면 **gcc 0줄 / clang 1줄** · `volatile` 떼면 **gcc `-O2` 만 2건** | gcc 7벌 + `-O0/-O2` · clang 5벌 |
| 다른 배열 뺄셈 (15-e) | ★ **40벌** 던져 `b-a` 가 **4 / -4 / 8** · **뺄셈 진단 0줄** · 경고는 **비교 쪽 1건**(이름이 다름) | gcc 20벌 · clang 20벌 |
| 널 산술 (15-f) | 컴파일 0건 · **gcc UBSan 0줄**(`pointer-overflow` 직접 켜도 0줄) · **clang 2줄** · `-std=c2x` 에서도 clang 은 여전히 보고 | gcc 9벌 · clang 3벌 |
| `void *` 산술 (15-h) | `-Wall -Wextra` **0건** / `+pedantic` **2건** · `sizeof(void)`=1 · `vp+1` 이 **1바이트** · clang 만 「GNU extension」이라 명명 | gcc 7벌 · clang 4벌 |
| `*p++` (15-i) | **10 / 10 / 20** · `p-arr` 가 **1 / 0 / 1** · `arr[0]` 이 11 — [09번 형제](../09-operator-precedence-and-associativity/)의 값과 일치 | gcc 7벌 |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3)에서만** 그렇다.

- **`sizeof(int)`=4·`sizeof(double)`=8** 이라 보폭이 4·8 인 것 — **구현 정의**다.
- **`sizeof(ptrdiff_t)`=`sizeof(size_t)`=8** — ★ **둘이 같다는 것도 보장이 아니다.**
- **GNU 확장에서 `sizeof(void)`=1** 인 것.
- ★★ **`b - a` 의 값(`4`·`-4`·`8`)** — 전부 **UB 의 산물이고 아무 근거도 못 된다.**\
  근거는 「**세 답으로 갈린다**」는 사실뿐이다.
- **`a[10]`·`*end`·`NULL+1` 의 값** — ★ **UB 라 아무 의미가 없다.**
- **gcc 의 `-fsanitize=pointer-overflow` 가 진단을 안 내는 것** — 이 버전의 구현이다.
- **clang 18 이 `-std=c2x` 에서도 `NULL + 0` 을 보고하는 것** — 검사기 구현이 C23 을 따라오지 않았다.

**포인터 산술의 규칙 자체는 구현 의존이 아니다.** 스케일링이 `sizeof(*p)` 배인 것 · `q - p` 가 원소 개수인 것 ·\
**`a[i]` == `*(a+i)`** · **끝 한 칸 뒤까지가 합법 범위**인 것 · 그 넷이 UB 인 것은 **어느 C 구현에서도 같다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `restrict` 와 앨리어싱([목록의 **33번 주제**](../33-restrict-and-the-aliasing-contract/)) · `p + huge` 로 정수 오버플로와 겹치는 자리 ·\
  `p - p` 와 널끼리의 뺄셈 · **`size_t` 로 받았을 때 실제로 나오는 거대한 양수** ·\
  `-fsanitize=pointer-overflow` 의 **다른 형태**(널 아닌 오버플로) · `unsigned char *` 로 걷는 판.
- **못 잰 것** — ★ **「clang 이 왜 `b` 를 `a` 앞에 두는가」.** 값이 `-4` 인 것은 봤지만\
  **스택 배치를 찍어 확인하지는 않았다.** 이것은 **미명시 영역**이라 원인을 안다고 보장이 생기지도 않는다.\
  ★ **재현되는 것**(「세 답으로 갈린다」)과 **한 판의 결과**(「clang 이 -4 다」)를 갈라 읽어야 한다.
- ★ **`b - a` 의 세 값이 「모든 조합을 덮었다」는 뜻은 아니다.** 40벌을 던졌고 그 안에서 셋이 나왔다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- **gcc 의 sanitizer 가 「포인터 형성」과 「널 산술」을 보게 됐는지** — 지금은 clang 만 본다.
- **gcc 의 `-fsanitize=pointer-overflow` 가 동작하게 됐는지** — 지금은 플래그만 받는다.
- **clang 이 `-std=c2x` 에서 `NULL + 0` 을 더 이상 보고하지 않게 됐는지**(C23 이 정의했다).
- **`-Warray-bounds` 가 `-O0` 에서도 잡게 됐는지**, **clang 이 잡기 시작했는지**.
- ★ **`b - a` 의 갈림** — 버전이 오르면 **다시 40벌을 던져** 「여전히 갈리는가」를 본다.\
  **값이 아니라 「갈린다」가 결론**이므로, 어쩌다 세 벌이 같아도 결론을 뒤집지 않는다.
- **규칙 자체는 다시 돌릴 필요가 없다** — C89 이후 바뀐 것은 **`NULL + 0`**(C23) 하나뿐이다.
