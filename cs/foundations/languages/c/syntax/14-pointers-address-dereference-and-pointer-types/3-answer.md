# c/syntax/14 — 포인터: 「**값이 주소인 변수**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 작업 디렉터리는 `/tmp/c13`, 소스 파일명은 언제나 `ex.c` 다.\
> ★★ **실행 블록은 `./x 2>&1 | cat` 로 받았다** — sanitizer 는 stderr, `printf` 는 stdout 이라 순서가 실행 환경에 달린다.
> ★★ **주소가 박힌 블록에는 「대조할 것」을 한 줄 달아 두었다** — 값이 아니라 **차이와 등식**이 근거다.
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | `%p` 가 찍는 **주소값**(ASLR) · 스택 주소 | ★ 주소들 **사이의 차이**(`4`·`8`·`8`) |
> | ASan 의 PID·`BuildId`·모듈 오프셋 | ★ **등식**(`p==&x`·`pp==&p`·`*pp==p`) |
> | — | **`파일:줄:칸`** · 진단 본문 · 플래그 이름 · **종료 코드** · `sizeof` 값 |

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 네 변수의 주소를 찍고 둘을 고치면 ★★

**출력**

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
> 다섯 판을 돌려 주소는 전부 달랐고 **차이 셋(`4`·`8`·`8`)은 한 번도 안 바뀌었다.**

**왜 그런가**

```text
   전 상태                        *p = 99 뒤                 p = &y 뒤
   +----------+                  +----------+               +----------+
   | x    42  |<--+              | x    99  |<--+           | x    99  |   <- 99 인 채
   | y     7  |   |              | y     7  |   |           | y     7  |<--+
   | p   [&x] |---+              | p   [&x] |---+           | p   [&y] |---+
   | pp  [&p] |--> p             | pp  [&p] |--> p          | pp  [&p] |--> p
   +----------+                  +----------+               +----------+
     칸 안이 바뀐다                                            쪽지가 바뀐다
```

- **`p` 는 `x` 의 주소**, **`*p` 는 42**, **`&p` 는 `p` 자신이 놓인 칸의 주소**다. 셋이 다 다르다.
- **차이는 `4` · `8` · `8`** 이고 **다섯 판에서 안 바뀌었다.** `int` 가 4바이트, 포인터가 8바이트라서다.
- **`*p = 99` 뒤 `x` 는 99.** 그 다음 **`p = &y` 뒤에도 `x` 는 99** 다 — **되돌아가지 않는다.**\
  `*p` 만 7(=`y`)로 바뀐다.
- ★ **근거로 쓸 수 있는 것** — 차이 셋 · 등식 넷(`p==&x`·`pp==&p`·`*pp==p`·`**pp==x` 가 전부 1) · `sizeof` 네 개.\
  ★ **쓸 수 없는 것** — 주소값 자체(`0x7fff416bfe80`). **실행마다 바뀐다.**

### 2. 함수 둘이 각각 호출자의 포인터를 건드리면 — **별 하나가 갈랐다** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, cc exit=0) =====
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
> **없으면 파이프로 받을 때 두 줄이 통째로 사라진다**(ASan 이 버퍼를 비우기 전에 프로세스를 끝낸다).

**왜 그런가**

```text
   alloc_bad                         alloc_good
   main          함수                main          함수
   +---------+  +---------+          +---------+  +---------+
   | a [NULL]|->| p [NULL]|          | b [NULL]|<-| pp [&b] |
   +---------+  +---------+          +---------+  +---------+
       ^             |  p = malloc        ^            |  *pp = malloc
       |             v                    |            v
       |        | p [힙주소]|             | b [힙주소]|
       |        +---------+               +---------+
   ★ a 는 안 바뀐다                  ★ b 가 바뀐다
     함수가 끝나면 p 가 사라져
     힙 16바이트가 샌다
```

- **`alloc_bad` 뒤 `a` 는 여전히 NULL** 이고, **`alloc_good` 뒤 `b` 는 널이 아니고 `b[0]` 이 7** 이다.
- ★★ **경고는 어느 플래그 조합에서도 0건**이다(gcc 무플래그·`-Wall`·`+Wextra`·`+pedantic`·clang 전부).\
  **문법이 맞고 동작도 정의되어 있다** — `alloc_bad` 는 자기 지역 변수를 바꾸고 조용히 끝난다.
- ★ **ASan 이 `16 byte(s) leaked`** 를 낸다. `int` 4바이트 × 4개 = **16바이트**다.
- **한 문장으로** — 「**인자는 복사라서 `p` 를 바꿔도 `a` 가 든 칸은 안 건드린다.**\
  바꾸고 싶은 것이 `a` 라는 **칸**이면 그 칸의 **주소**를 넘겨야 한다.」

### 3. 타입이 다른 포인터를 대입하면 — **둘에서 나고, 경고다**

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘main’:
ex.c:10:8: warning: assignment to ‘char *’ from incompatible pointer type ‘int *’ [-Wincompatible-pointer-types]
   10 |     cp = &i;            /* int*  -> char*   : 경고 */
      |        ^
ex.c:14:8: warning: assignment to ‘double *’ from incompatible pointer type ‘int *’ [-Wincompatible-pointer-types]
   14 |     dp = ip;            /* int*  -> double* : 경고 */
      |        ^
===== clang -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c:10:8: warning: incompatible pointer types assigning to 'char *' from 'int *' [-Wincompatible-pointer-types]
   10 |     cp = &i;            /* int*  -> char*   : 경고 */
      |        ^ ~~
ex.c:14:8: warning: incompatible pointer types assigning to 'double *' from 'int *' [-Wincompatible-pointer-types]
   14 |     dp = ip;            /* int*  -> double* : 경고 */
      |        ^ ~~
2 warnings generated.
===== gcc -std=c17 -pedantic-errors (exit=1) =====
ex.c: In function ‘main’:
ex.c:10:8: error: assignment to ‘char *’ from incompatible pointer type ‘int *’ [-Wincompatible-pointer-types]
   10 |     cp = &i;            /* int*  -> char*   : 경고 */
      |        ^
ex.c:14:8: error: assignment to ‘double *’ from incompatible pointer type ‘int *’ [-Wincompatible-pointer-types]
   14 |     dp = ip;            /* int*  -> double* : 경고 */
      |        ^
```

**왜 그런가**

- **다섯 줄 중 둘**에서 난다 — `cp = &i;`(10행)와 `dp = ip;`(14행).
- **경고이고 종료 코드는 0** 이다. **실행 파일이 나온다.**\
  C 에서 이것은 **제약 위반**이라 진단 의무가 있지만, **에러여야 한다는 요구는 없다.**
- ★ **`-pedantic-errors` 를 붙이면 `error:` 가 되고 `exit=1`** 이다(gcc·clang 둘 다 error 2건).\
  ★ 이 종료 코드를 처음 잴 때 **셸에서 `$?` 가 명령 치환의 것을 잡아** `exit=0` 으로 적을 뻔했다.\
  **파이프·치환 없이 직접 돌려 다시 재야 한다.**
- **`void *` 가 오가는 두 줄은 조용하다** — `void *` 는 「타입을 모르는 객체 포인터」로 설계됐고,\
  **어느 객체 포인터와도 캐스트 없이 오간다.** 그래서 `malloc` 의 반환을 그냥 받을 수 있다.
- ★ **`-Wincompatible-pointer-types` 는 플래그 없이도 켜져 있다** — 표 참조(9번 답).

### 4. `%p` 에 캐스트를 빼면 — **`-pedantic` 만 말한다** ★★

**출력**

```text
===== 플래그별 warning: 줄 수 =====
gcc   -std=c17                         0 건
gcc   -std=c17 -Wall                   0 건
gcc   -std=c17 -Wall -Wextra           0 건
gcc   -std=c17 -Wall -Wextra -pedantic 2 건   [-Wformat=] [-Wpedantic]
clang -std=c17 -Wall -Wextra           0 건
clang -std=c17 -Wall -Wextra -pedantic 2 건   [-Wformat-pedantic]
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
===== clang -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c:10:39: warning: format specifies type 'void *' but the argument has type 'int *' [-Wformat-pedantic]
   10 |     printf("캐스트 안 함: %p\n", ip);          /* int * 를 %p 로 */
      |                           ~~     ^~
ex.c:11:35: warning: format specifies type 'void *' but the argument has type 'char *' [-Wformat-pedantic]
   11 |     printf("char 배열  : %p\n", s);            /* char * 를 %p 로 */
      |                          ~~     ^
      |                          %s
2 warnings generated.
===== 실행 (gcc) =====
캐스트 함  : 0x7ffdf513f69c
캐스트 안 함: 0x7ffdf513f69c
char 배열  : 0x7ffdf513f6b5
함수 포인터: (nil)
```

**왜 그런가**

- **`gcc -Wall -Wextra` 는 0건**, **`+pedantic` 은 2건**이다. clang 도 같은 모양이다.
- ★★ **gcc 와 clang 이 잡는 줄이 다르다.**\
  gcc — **10행(`int *`)** 과 **12행(함수 포인터 → `void *`)**.\
  clang — **10행(`int *`)** 과 **11행(`char *`)**. ★ **셋 중 겹치는 것은 10행 하나**다.
- **실행 출력에서 첫 줄과 둘째 줄이 같은 주소**를 찍는다 — 캐스트한 것과 안 한 것이 **구별되지 않는다.**
- ★★ **그래서 이 함정이 안 보인다.** x86-64 에서 **모든 객체 포인터의 표현이 같아서**\
  `%p` 가 `int *` 를 받아도 정확한 주소를 찍는다. **「안 터졌다」는 「안전하다」가 아니다.**
- `printf` 는 가변 인자 함수라 **컴파일러가 인자 타입을 모르고**, `%p` 는 **`void *` 를 꺼내도록** 정해져 있다.

### 5. 포인터들의 `sizeof`

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
sizeof : int=4  int*=8  int**=8  char*=8
```

**왜 그런가**

- **4 · 8 · 8 · 8** 이다. **포인터는 셋 다 같은 크기**다.
- **가리키는 타입이 바뀌어도 포인터의 크기는 안 바뀐다**(이 환경에서). 크기는 **구현 정의**다.
- ★ **가리키는 타입이 정하는 것은** 「**한 칸이 몇 바이트인가**」다 —\
  `p + 1` 이 몇 바이트 움직이고 `*p` 가 몇 바이트를 읽는지. 그것이 [15번 형제](../15-pointer-arithmetic-and-indexing/)의 주제다.

### 6. 주소를 근거로 쓸 수 있나 ★★

**답**

- **같지 않다.** ASLR(주소 공간 배치 무작위화) 때문에 **실행마다 스택 시작 주소가 바뀐다.**\
  다섯 판을 돌려 `&x` 가 전부 달랐다(`0x7fff416bfe80` · `0x7ffd035f63d0` · …).
- **근거로 실을 것은 차이와 등식**이다 — `&y - &x = 4` · `p == &x` 가 1 같은 것.\
  ★ 그래서 이 주제의 블록에는 「**대조할 것은 숫자가 아니라 \~라는 성질이다**」를 붙여 두었다.
- **두 주소의 거리를 재는 올바른 방법** — **같은 배열 안**이면 포인터 뺄셈, **아니면 `uintptr_t` 로 캐스트해 정수 뺄셈**.\
  ★ **서로 다른 객체의 포인터끼리 빼는 것은 UB** 이기 때문이다([15번 형제](../15-pointer-arithmetic-and-indexing/)에서 실측으로 세 답이 갈렸다).
- ★ **「차이가 다섯 번 다 같았다」는 관찰이지 보장이 아니다.** 지역 변수의 스택 배치는 **미명시**이고,\
  최적화 수준·컴파일러가 바뀌면 달라질 수 있다. 이 문서는 **`-O0` 한 벌**에서만 반복했다.

### 7. 선언의 `*` 와 식의 `*` ★

**답**

```text
   int *p = &x;
       ^                        선언의 * — 타입을 만든다. "*p 가 int 다"
                                 -> p 의 타입은 int *
   *p = 99;
   ^                            식의 * — 값을 꺼낸다(역참조)

   &x  의 타입 : int *          &가 별을 하나 붙인다
   &p  의 타입 : int **
   **pp        : "pp 가 가리키는 것이 가리키는 것"  = x
```

- **`int *p = &x;` 에 `*` 는 한 번** 나오고 그것은 **선언의 `*`** 다.\
  「`*p` 가 `int` 다」라고 읽으면 **`p` 는 `int *`** 라는 뜻이 된다([01번 형제](../01-declaration-syntax-and-reading/)).\
  그래서 초기화는 **`*p = &x` 가 아니라 `p = &x`** 다 — 여기서 헷갈리는 사람이 많다.
- **`&` 는 타입에 별을 하나 붙인다.** `x` 가 `int` 면 `&x` 는 `int *`, `p` 가 `int *` 면 `&p` 는 `int **`.
- **`**pp` 를 말로 풀면** 「`pp` 가 가리키는 칸(= `p`)이 가리키는 칸(= `x`)의 값」이다.\
  실측에서 `**pp == x` 가 **1** 이었다.

### 8. `void *` 의 자리

**답**

- **`void *` 는** 「**타입을 모르는 객체를 가리키는 포인터**」로 설계됐다.\
  어느 객체 포인터와도 **캐스트 없이 양방향으로** 오간다 — 3번 답의 `vp = &i;` 와 `ip = vp;` 가 **둘 다 경고 0건**이었다.\
  그래서 `malloc` 의 반환값을 그냥 받을 수 있다.
- ★ **함수 포인터는 아니다.** ISO C 는 함수 포인터와 객체 포인터 사이 변환을 보장하지 않고,\
  **gcc 가 `-Wpedantic` 으로 말한다** — `ISO C forbids conversion of function pointer to object pointer type`.\
  ★ **clang 은 이 자리를 잡지 않았다.**
- **`%p` 가 `void *` 를 요구하는 것도 같은 이유**다 — `printf` 는 타입을 모르니\
  「**모든 객체 포인터가 통과할 수 있는 한 가지 타입**」을 정해 두어야 했고 그것이 `void *` 다.

### 9. 어느 도구가 무엇을 보나 ★★

**답**

| 프로그램 | gcc 무플래그 | gcc `-Wall` | gcc `+Wextra` | gcc `+pedantic` | gcc `-std=c2x +ped` | clang `-Wall -Wextra` | clang `+pedantic` |
|---|---|---|---|---|---|---|---|
| 14-a 주소 덤프 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 14-b 타입 다른 대입 | **2** | 2 | 2 | 2 | 2 | **2** | 2 |
| 14-c 이중 포인터 | **0** | **0** | **0** | **0** | 0 | **0** | **0** |
| 14-d `%p` 캐스트 | 0 | 0 | **0** | **2** | 2 | **0** | **2** |

- ★★★ **어느 플래그로도 0건인 것은 14-c**(이중 포인터 자리)다. **이 주제의 가장 비싼 사고**이고,\
  **LeakSanitizer(ASan)만** 말한다 — `16 byte(s) leaked`.
- **`-pedantic` 에서만 보이는 것은 14-d**(`%p` 캐스트 누락)다. **`-Wall -Wextra` 로는 양쪽 컴파일러 다 0건.**
- **gcc 와 clang 이 서로 다른 것을 보는 자리 둘** —\
  ① `%p` 에 **`char *`** 를 넘긴 것 — **clang 만** 잡는다.\
  ② **함수 포인터를 `void *` 로** 캐스트한 것 — **gcc 만** 잡는다.
- ★ **14-b 는 플래그 없이도 2건**이다 — 제약 위반이라 진단 의무가 있어 **기본으로 켜져 있다.**

### 10. 다섯 층과 도구 ★★

**답**

| 층 | 이 주제(14번) | [15번](../15-pointer-arithmetic-and-indexing/) | [13번](../13-goto-cleanup-idiom/) |
|---|---|---|---|
| **표준** | ★★ **본체** — `&`/`*` · 인자가 **복사** · `void *` 무손실 왕복 · `&x` 의 타입 | 인덱싱 == `*(a+i)` · `ptrdiff_t` | ★★ **본체** |
| **조건부 표준** | ★ **`uintptr_t`/`intptr_t`** — `<stdint.h>` 가 정의할 때만 있는 **선택 타입** | 같음 | ★ **해당 없음** |
| **구현 정의** | 포인터의 **크기와 표현**(8바이트) · `(nil)` 이라는 `printf` 표기 | 포인터 표현 | ★ **거의 없다** |
| **미명시** | ★ 지역 변수의 **스택 배치 순서** | 서로 다른 객체의 **포인터 비교** | ★ **해당 없음** |
| **UB** | `%p` 에 `void *` 아닌 것 · **널/불확정 포인터 역참조** | ★★ **본체 셋** | ★ **둘뿐** |

- **조건부 표준 칸에 들어가는 것은 `uintptr_t`/`intptr_t`** 다.\
  ★ **왜 조건부인가** — 표준이 **선택 타입**으로 두었기 때문이다. 포인터를 담을 정수 타입이 없는 구현이 있을 수 있어\
  「`<stdint.h>` 가 정의했을 때만」 쓸 수 있다. **이 환경에는 있고 8바이트**였다.
- ★★ **[15번 형제](../15-pointer-arithmetic-and-indexing/)와 견주면 UB 칸의 두께가 정반대**다.\
  여기는 **타입 규칙이 본체**이고, 15번은 **그 타입 위에서 무엇이 UB 가 되는가**가 본체다.\
  **14번의 규칙을 모르면 15번의 UB 가 왜 UB 인지 설명이 안 된다.**
- ★ **「실행 결과가 정상이다」가 이 주제에서 가장 약한 근거**인 이유 —\
  x86-64 에서 **모든 객체 포인터의 표현이 같아서** `%p` 오용도, 타입 틀린 대입도 **그럴듯한 값을 찍는다.**\
  **표현이 다른 플랫폼에서 깨지는데 여기서는 증상이 없다.**

### 11. 이 주제의 네 번째 창 ★

**답**

- **세 창으로 안 잡히는 것** —
  - **컴파일 진단**은 타입만 본다. 「포인터를 값으로 받아 바꾸는 것」은 **타입이 맞는 코드**라 0건이다.
  - **실행 출력**은 「널이 아니다」까지만 본다. **샌 메모리는 출력에 안 나온다.**
  - **UBSan** 은 할 일이 적다 — 역참조를 안 하면 UB 가 없다.
- ★★ **그래서 창을 둘 더 썼다.**
  - **`%p` 주소 덤프 + `uintptr_t` 차이** → 「값이 주소다」를 **차이 `4`·`8`·`8` 과 등식 넷**이라는 숫자로 바꿨다.\
    ★ **값이 아니라 차이를 근거로 삼아** ASLR 을 견딘다.
  - **LeakSanitizer** → 「호출자의 포인터가 안 바뀌었다」를 **`16 byte(s) leaked`** 라는 숫자로 바꿨다.
- ★ **두 창의 성격이 다르다** — 앞엣것은 **보이지 않는 것을 보이게** 했고,\
  뒤엣것은 **보이지 않는 실패를 실패로 만들었다**(exit=1).

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 컴파일러·플래그로 돌렸나 |
|---|---|---|
| 주소 덤프 (14-a) | 차이 **4 / 8 / 8** · 등식 넷이 전부 1 · `sizeof` **4/8/8/8** · **주소는 다섯 판 전부 다름** · 경고 0건 | gcc 7벌 + 실행 5판 |
| 이중 포인터 (14-c) | `a` 는 NULL · `b[0]=7` · **경고 0건(7조합 전부)** · ASan **`16 byte(s) leaked`** run exit=1 | gcc 7벌 · clang 2벌 · gcc `-fsanitize=address,undefined` |
| 타입 다른 대입 (14-b) | 다섯 줄 중 **둘**에서 진단 · **경고이고 exit=0** · `-pedantic-errors` 는 **error 2건 exit=1** | gcc 8벌 · clang 3벌 |
| `%p` 캐스트 (14-d) | gcc `-Wall -Wextra` **0건** / `+pedantic` **2건** · clang 도 같음 · **gcc 는 `int *`+함수포인터, clang 은 `int *`+`char *`** · 실행 출력은 **캐스트 유무가 같음** | gcc 4벌 · clang 4벌 |
| ★ 종료 코드 재측정 | `-pedantic-errors` 의 exit 을 **명령 치환 안에서 `$?` 로 재어 0 으로 기록했다가** 직접 재어 **1** 로 고침 | 직접 측정 |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3 · glibc)에서만** 그렇다.

- **포인터가 8바이트인 것**과 **모든 객체 포인터의 표현이 같은 것** — ★ **구현 정의**다.\
  이것 때문에 `%p` 오용이 **정확한 주소를 찍는다.**
- **`%p` 가 널을 `(nil)` 로 찍는 것** — glibc `printf` 의 표기다. **표준이 정한 것이 아니다.**
- **주소값과 ASLR** — ★ **값 자체는 아무 근거도 못 된다.**
- **지역 변수의 스택 배치 차이(4 · 8 · 8)** — ★ **관찰이지 보장이 아니다.** `-O0` 한 벌에서만 반복했다.
- **`uintptr_t` 가 있는 것** — 선택 타입이다.
- **`-Wformat-pedantic` 이 clang 에서 `char *` 까지 잡는 것** — 진단 구현의 분류다.

**포인터의 규칙 자체는 구현 의존이 아니다.** `&`/`*` 의 뜻 · **인자가 복사인 것** ·\
`p = q` 와 `*p = v` 가 다른 것 · `void *` 와 객체 포인터의 무손실 왕복은 **어느 C 구현에서도 같다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — C23 `nullptr`(목록의 **19번 주제**) · `memset` 으로 포인터를 0 으로 만든 뒤 `== NULL` 인지 ·\
  `dlsym` 처럼 함수 포인터와 `void *` 를 섞는 POSIX 자리 · 엄격한 앨리어싱으로 **읽는** 쪽(목록의 **55번 주제**) ·\
  널 포인터의 **비트 표현**.
- **못 잰 것** — ★ **「표현이 다른 플랫폼에서 `%p` 오용이 실제로 깨지는가」.** 이 머신에 그런 플랫폼이 없어\
  **측정 방법 자체가 성립하지 않는다.** 그래서 이 문서는 「**표준이 UB 라고 한다 + 여기서는 증상이 없다**」까지만 적었다.
- ★ **`*dp` 로 `i` 밖 4바이트를 읽은 값**은 받았지만 **근거로 쓰지 않았다** — UB 라 아무것도 증명하지 않는다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- gcc·clang 이 **`%p` 오용을 `-Wall` 에 넣었는지**(지금은 `-pedantic` 뿐).
- gcc 가 **`char *` 도 잡게 됐는지**, clang 이 **함수 포인터 캐스트를 잡게 됐는지**.
- `-Wincompatible-pointer-types` 가 **기본에서 에러로 승격됐는지** — 지금은 **경고에 exit=0** 이다.\
  ★ 이 머신에 gcc 13.3.0 뿐이라 **다음 버전에서 어떤지는 확인할 수 없었다.**
- **포인터 크기·표현은 다른 ISA 로 갈 때** 다시 잰다.
- **규칙 자체는 다시 돌릴 필요가 없다** — C89 이후 바뀐 적이 없다.
