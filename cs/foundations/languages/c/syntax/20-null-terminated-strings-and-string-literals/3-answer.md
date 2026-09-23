# c/syntax/20 — 널 종단 문자열과 문자열 리터럴: 「**문자열은 타입이 아니라 0 하나로 맺는 약속이다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·sanitizer 리포트는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 작업 디렉터리는 `/tmp/c17b/20`, 소스는 `ex.c`\~`ex7.c` 다.\
> ★★ **죽는 프로그램에는 `setvbuf(stdout, NULL, _IONBF, 0)` 를 넣었다** — 그러지 않으면 **찍힌 줄이 통째로 사라진다.**\
> ASan 리포트는 `| sed -n '1,/^SUMMARY/p'` 로 잘랐다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 의 주소 · `pc`/`bp`/`sp` · PID · `BuildId` · 섹션 주소 | ★★ **바이트 격자**(`61 62 63 00`) · **`sizeof`/`strlen` 값** |
> | 리터럴의 실제 번지 | ★★ **공유/따로 판정**과 **벌마다 갈린다는 사실** |
> | — | ★★ **종료 코드**(`cc exit` · `run exit=0`/`139`/`1`) · 진단 본문 · **플래그 이름** · 섹션 **이름** |

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 배열·포인터·손으로 쓴 네 바이트를 나란히 재면 — **`memcmp` 가 0** ★★★

**출력**

```c
/* ex.c */
#include <stdio.h>
#include <string.h>

int main(void) {
    char arr[] = "abc";          /* 배열 — 복사본이 만들어진다 */
    char *lit  = "abc";          /* 포인터 — 리터럴을 가리킨다 */
    char raw[4] = {'a', 'b', 'c', '\0'};   /* 손으로 쓴 같은 것 */

    printf("sizeof arr = %zu · strlen(arr) = %zu\n", sizeof arr, strlen(arr));
    printf("sizeof lit = %zu · strlen(lit) = %zu   (★ 포인터 크기다)\n", sizeof lit, strlen(lit));
    printf("sizeof raw = %zu · strlen(raw) = %zu\n", sizeof raw, strlen(raw));
    printf("arr 과 raw 의 바이트가 같은가 : memcmp = %d\n", memcmp(arr, raw, 4));

    printf("\n바이트를 직접 본다\n");
    for (size_t k = 0; k < sizeof arr; k++)
        printf("  arr[%zu] = 0x%02x %s\n", k, (unsigned char)arr[k],
               arr[k] ? "" : "<- 널 종단자");

    printf("\n널이 중간에 있으면 — 「길이」가 둘로 갈린다\n");
    char mid[] = "ab\0cd";
    printf("  sizeof mid = %zu · strlen(mid) = %zu\n", sizeof mid, strlen(mid));
    printf("  바이트 : ");
    for (size_t k = 0; k < sizeof mid; k++) printf("%02x ", (unsigned char)mid[k]);
    printf("\n");
    printf("  printf(\"%%s\") 로 찍으면 : [%s]   <- 첫 널에서 멈춘다\n", mid);
    printf("  여섯 바이트를 눈에 보이게 : [");
    for (size_t k = 0; k < sizeof mid; k++)
        printf("%s", mid[k] ? (char[2]){mid[k], 0} : "\\0");
    printf("]\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex.c -o x ; ./x (cc exit=0 · run exit=0) =====
sizeof arr = 4 · strlen(arr) = 3
sizeof lit = 8 · strlen(lit) = 3   (★ 포인터 크기다)
sizeof raw = 4 · strlen(raw) = 3
arr 과 raw 의 바이트가 같은가 : memcmp = 0

바이트를 직접 본다
  arr[0] = 0x61 
  arr[1] = 0x62 
  arr[2] = 0x63 
  arr[3] = 0x00 <- 널 종단자

널이 중간에 있으면 — 「길이」가 둘로 갈린다
  sizeof mid = 6 · strlen(mid) = 2
  바이트 : 61 62 00 63 64 00 
  printf("%s") 로 찍으면 : [ab]   <- 첫 널에서 멈춘다
  여섯 바이트를 눈에 보이게 : [ab\0cd\0]
```

**왜 그런가**

```text
   char arr[] = "abc"        char raw[4] = {'a','b','c','\0'}
   +----+----+----+----+     +----+----+----+----+
   | 61 | 62 | 63 | 00 |     | 61 | 62 | 63 | 00 |      memcmp = 0
   +----+----+----+----+     +----+----+----+----+

   char mid[] = "ab\0cd"
   +----+----+----+----+----+----+
   | 61 | 62 | 00 | 63 | 64 | 00 |    sizeof 6  ·  strlen 2  ·  %s -> [ab]
   +----+----+----+----+----+----+
   |<- strlen ->|
```

- **`sizeof` 는 4 · 8 · 4** 다. 가운데 8 은 **`lit` 가 포인터**라서 나온 값이다(★ [16번 형제](../16-array-pointer-decay-and-function-parameters/)가 정본).
- **`strlen` 은 셋 다 3** 이다. **가리키는 곳이 같은 글자**이기 때문이다.
- ★★★ **`memcmp(arr, raw, 4)` 가 0** 이다 — **리터럴로 만든 배열과 손으로 쓴 배열의 바이트가 같다.**\
  ★ 그래서 「**문자열 타입**」이라고 말할 수 있는 것은 **없다.** 있는 것은 **`char` 배열과 끝의 0 하나**뿐이다.
- ★★ **`mid` 는 `sizeof` 6, `strlen` 2** 다. **둘 다 맞다** — `sizeof` 는 **상자**를, `strlen` 은 **약속**을 답한다.
- ★ **`printf("%s", mid)` 는 `[ab]`** 를 찍는다. 뒤의 `63 64 00` 은 **메모리에 있는데 관례가 거기서 끊는다.**\
  ★ 여섯 바이트를 펼쳐 찍으면 `[ab\0cd\0]` 로 **다 있다는 것**이 보인다.

| 무엇을 물었나 | `arr`(`"abc"`) | `lit`(`char *`) | `mid`(`"ab\0cd"`) |
|---|---|---|---|
| `sizeof` — 상자 크기 | **4** | **8**(포인터) | **6** |
| `strlen` — 첫 0 까지 | **3** | **3** | ★ **2** |
| 차이가 뜻하는 것 | 널 한 칸 | ★ **재는 대상이 다르다** | ★ **질문이 다르다** |

- ★★ **표의 가운데 칸만 성격이 다르다.** `arr` 와 `mid` 는 **같은 것을 두 방식으로 잰 것**이고,\
  `lit` 는 **아예 다른 것을 잰 것**이다 — 변수 자신(8바이트 포인터)이다.

### 2. 복사본을 고치고 이어서 리터럴을 고치면 — **`run exit=139`** ★★★ 본체

**출력**

```c
/* ex2.c */
#include <stdio.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    char arr[] = "abc";          /* 배열 = 복사본 */
    char *lit  = "abc";          /* 리터럴 그 자체 */

    arr[0] = 'A';                /* (가) 복사본은 고쳐도 된다 */
    printf("(가) arr 를 고쳤다 : %s\n", arr);

    printf("(나) 이제 리터럴을 고쳐 본다 — lit[0] = 'A'\n");
    lit[0] = 'A';                /* (나) 리터럴 수정 = UB */
    printf("(나) 살아남았다 : %s\n", lit);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex2.c -o x2 ; ./x2 (cc exit=0 · run exit=139) =====
(가) arr 를 고쳤다 : Abc
(나) 이제 리터럴을 고쳐 본다 — lit[0] = 'A'
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic ex2.c -o x2c ; ./x2c (cc exit=0 · run exit=139) =====
(가) arr 를 고쳤다 : Abc
(나) 이제 리터럴을 고쳐 본다 — lit[0] = 'A'
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -g -fsanitize=address ex2.c -o x2a ; ./x2a | sed -n '1,/^SUMMARY/p' (cc exit=0 · run exit=1) =====
(가) arr 를 고쳤다 : Abc
(나) 이제 리터럴을 고쳐 본다 — lit[0] = 'A'
AddressSanitizer:DEADLYSIGNAL
=================================================================
==85373==ERROR: AddressSanitizer: SEGV on unknown address 0x5a077fa98040 (pc 0x5a077fa97456 bp 0x7fff53a45c80 sp 0x7fff53a45bf0 T0)
==85373==The signal is caused by a WRITE memory access.
    #0 0x5a077fa97456 in main /tmp/c17b/20/ex2.c:12
    #1 0x71117682a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #2 0x71117682a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #3 0x5a077fa971e4 in _start (/tmp/c17b/20/x2a+0x11e4) (BuildId: 0cb573e04e8c9b7d8af12058870b40bb9d193bf1)

AddressSanitizer can not provide additional info.
SUMMARY: AddressSanitizer: SEGV /tmp/c17b/20/ex2.c:12 in main
```

> ★ **대조할 것은 주소가 아니라 성질이다.** ASan 의 주소·`pc`/`bp`/`sp`·PID·`BuildId` 는 실행마다 바뀐다.\
> 근거는 **출력이 어디서 끊겼는가**, **`run exit=139` ↔ ASan `run exit=1`**,\
> 그리고 ASan 이 「**The signal is caused by a WRITE memory access**」라고 말했다는 것이다.

**왜 그런가**

```text
   arr[0] = 'A'                       lit[0] = 'A'
   스택의 내 복사본을 고친다             .rodata 의 리터럴을 고친다
   +----+----+----+----+              +----+----+----+----+
   | 41 | 62 | 63 | 00 |   "Abc"      | 61 | 62 | 63 | 00 |   ★ 쓰기 금지
   +----+----+----+----+              +----+----+----+----+
        ★ 완전히 합법                         ★ UB -> SIGSEGV (run exit=139)
```

- ★★★ **출력은 「(나) 이제 리터럴을 고쳐 본다」까지만** 찍혔다. **마지막 줄은 안 나온다** — 거기서 죽었다.
- **평범한 실행의 종료 코드는 139** 이고 **gcc 와 clang 이 같았다.**\
  ★ **두 컴파일러가 같다는 것은 보장이 아니다** — 같은 OS 위에서 같은 배치를 했을 뿐이다.
- ★★★ **`-Wall -Wextra -pedantic` 의 경고는 0건**이다(배너가 `cc exit=0` 이고 진단 줄이 한 줄도 없다).\
  이유는 3번 답에 있다.
- ★★ **ASan 은 `run exit=1`** 이고 「**WRITE memory access**」라고 **무엇을 했는지**를 말한다.\
  ★ 다만 **여기서는 ASan 도 반쪽**이다 — 「`AddressSanitizer can not provide additional info`」로 끝난다.\
  **리터럴 수정은 ASan 에게도 그냥 SEGV** 이고, 7번의 `stack-buffer-overflow` 처럼 **범위를 찍어 주지 못한다.**
- ★★★ **다섯 층 중 UB** 다. ★ **「죽는다」가 UB 의 정의가 아니다** — UB 는 「**표준이 아무 요구도 하지 않는다**」는 뜻이고,\
  **죽어 준 것은 이 플랫폼의 친절**이다. 쓰기 가능하게 매핑된 환경이면 **조용히 성공했을 수도 있다.**
- ★ **앞의 `arr[0] = 'A'` 가 합법인 이유**는 `arr` 가 **리터럴을 베껴 만든 내 배열**이기 때문이다(10번 답).

| 한 줄 | 무슨 층인가 | 실측 |
|---|---|---|
| `char arr[] = "abc"; arr[0] = 'A';` | **표준** — 완전히 합법 | `Abc` 가 찍혔다 |
| `char *lit = "abc";` | **표준** — 대입 자체는 정상 | 경고 0건 |
| `lit[0] = 'A';` | ★★★ **UB** | **`run exit=139`** · ASan `WRITE memory access` |
| 리터럴을 **읽는 것**(`printf("%s", lit)`) | **표준** — 읽기는 언제나 된다 | 죽기 전까지 정상이었다 |

- ★★ **한 글자 차이로 층이 바뀐다** — **읽으면 표준, 쓰면 UB** 다.\
  ★ 그래서 **`const char *` 로 받는 습관**이 이 주제의 가장 싼 방어선이다.

### 3. 그 위험을 컴파일러에게 물어보려면 — **`-Wwrite-strings`** ★★

**출력**

```c
/* ex2.c */
#include <stdio.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    char arr[] = "abc";          /* 배열 = 복사본 */
    char *lit  = "abc";          /* 리터럴 그 자체 */

    arr[0] = 'A';                /* (가) 복사본은 고쳐도 된다 */
    printf("(가) arr 를 고쳤다 : %s\n", arr);

    printf("(나) 이제 리터럴을 고쳐 본다 — lit[0] = 'A'\n");
    lit[0] = 'A';                /* (나) 리터럴 수정 = UB */
    printf("(나) 살아남았다 : %s\n", lit);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -Wwrite-strings ex2.c -o /dev/null (cc exit=0) =====
ex2.c: In function ‘main’:
ex2.c:6:18: warning: initialization discards ‘const’ qualifier from pointer target type [-Wdiscarded-qualifiers]
    6 |     char *lit  = "abc";          /* 리터럴 그 자체 */
      |                  ^~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -Wwrite-strings ex2.c -o /dev/null (cc exit=0) =====
ex2.c:6:11: warning: initializing 'char *' with an expression of type 'const char[4]' discards qualifiers [-Wincompatible-pointer-types-discards-qualifiers]
    6 |     char *lit  = "abc";          /* 리터럴 그 자체 */
      |           ^      ~~~~~
1 warning generated.
```

```text
===== gcc -std=c17 ex2.c -o x2s && objdump -h x2s | grep -E 'rodata|[.]data' (exit=0) =====
 17 .rodata       00000085  0000000000002000  0000000000002000  00002000  2**3
 24 .data         00000010  0000000000004000  0000000000004000  00003000  2**3
```

**왜 그런가**

```text
   C 에서 "abc" 의 타입          ->  char[4]       -> char * 로 받는 것이 ★ 정상 (경고 0건)
   -Wwrite-strings 를 켜면       ->  const char[4] -> char * 로 받는 것이 ★ const 버림 (경고 1건)
   C++ 에서는                    ->  const char[4] -> 처음부터 걸린다
```

```text
   ★ 누가 언제 말해 주는가 — 아래로 갈수록 늦다

   컴파일  -Wall -Wextra -pedantic   ->  ★ 0 건
                 |
   컴파일  + -Wwrite-strings          ->  1 건 · ★ 가리키는 줄은 "초기화" 다
                 |
   링크 뒤  objdump -h                ->  .rodata 에 있다는 "배치" 만
                 |
   실행    그냥                        ->  SIGSEGV · run exit=139
                 |
   실행    ASan                       ->  "WRITE memory access" · run exit=1
```

- ★★★ **기본 플래그가 침묵하는 이유는 타입**이다. **C 에서 문자열 리터럴의 타입은 `const` 가 아니다.**\
  그래서 `char *lit = "abc";` 는 **타입이 맞는 대입**이고, 수상할 것이 없다.
- ★★ **`-Wwrite-strings` 는 리터럴의 타입을 `const char[]` 로 바꿔 준다.** 그제서야 진단이 난다.
- ★★ **플래그 이름이 두 컴파일러에서 다르다** —\
  gcc `-Wdiscarded-qualifiers` · clang `-Wincompatible-pointer-types-discards-qualifiers`.
- ★★★ **진단이 가리키는 줄은 `char *lit = "abc";`** 다. **`lit[0] = 'A';` 가 아니다** —\
  도구가 잡는 것은 「수정」이 아니라 「**수정할 수 있는 포인터로 받은 것**」, 즉 **한 발 앞**이다.
- ★★ **경고이지 에러가 아니다**(`cc exit=0`). 빌드는 그대로 나온다.
- ★ **`objdump -h` 에 `.rodata` 와 `.data` 가 따로 보인다.**\
  ★ **이것은 구현 정의(이 플랫폼의 배치)이지 보장이 아니다.** 표준이 말하는 것은 「**고치면 UB**」까지다.\
  ★ 섹션의 **주소·크기는 흔들리는 칸**이고 **이름과 「둘이 따로 있다」는 대비**만 근거로 쓴다.

### 4. 같은 글자의 리터럴 둘이 같은 주소인가 — **미명시** ★★★

**출력**

```c
/* ex3.c */
#include <stdio.h>
#include <string.h>

static const char *f(void) { return "hello"; }

int main(void) {
    const char *a = "hello";
    const char *b = "hello";          /* 같은 글자의 리터럴 둘 */
    const char *c = f();              /* 다른 함수 안의 같은 리터럴 */
    const char *d = "hello world";    /* 더 긴 리터럴 */
    const char *tail = d + 6;         /* 그 꼬리 "world" */
    const char *e = "world";          /* 꼬리와 같은 글자 */

    printf("a == b            : %s   (같은 파일 안의 같은 리터럴)\n", a == b ? "★ 공유" : "따로");
    printf("a == c            : %s   (다른 함수 안의 같은 리터럴)\n", a == c ? "★ 공유" : "따로");
    printf("e == d+6          : %s   (꼬리 겹침)\n", e == tail ? "★ 공유" : "따로");
    printf("strcmp(a,b) = %d · strcmp(e,tail) = %d  (글자는 어차피 같다)\n",
           strcmp(a, b), strcmp(e, tail));
    printf("a-b 의 바이트 차  : %td\n", a - b);
    printf("d 와 a 의 차가 0 인가 : %s\n", d == a ? "그렇다" : "아니다");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 ex3.c -o x3_O0 ; ./x3_O0 (cc exit=0 · run exit=0) =====
a == b            : ★ 공유   (같은 파일 안의 같은 리터럴)
a == c            : ★ 공유   (다른 함수 안의 같은 리터럴)
e == d+6          : 따로   (꼬리 겹침)
strcmp(a,b) = 0 · strcmp(e,tail) = 0  (글자는 어차피 같다)
a-b 의 바이트 차  : 0
d 와 a 의 차가 0 인가 : 아니다
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 ex3.c -o x3_O2 ; ./x3_O2 (cc exit=0 · run exit=0) =====
a == b            : ★ 공유   (같은 파일 안의 같은 리터럴)
a == c            : ★ 공유   (다른 함수 안의 같은 리터럴)
e == d+6          : ★ 공유   (꼬리 겹침)
strcmp(a,b) = 0 · strcmp(e,tail) = 0  (글자는 어차피 같다)
a-b 의 바이트 차  : 0
d 와 a 의 차가 0 인가 : 아니다
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -fno-merge-constants ex3.c -o x3_nm ; ./x3_nm (cc exit=0 · run exit=0) =====
a == b            : ★ 공유   (같은 파일 안의 같은 리터럴)
a == c            : ★ 공유   (다른 함수 안의 같은 리터럴)
e == d+6          : 따로   (꼬리 겹침)
strcmp(a,b) = 0 · strcmp(e,tail) = 0  (글자는 어차피 같다)
a-b 의 바이트 차  : 0
d 와 a 의 차가 0 인가 : 아니다
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 ex3.c -o x3c_O0 ; ./x3c_O0 (cc exit=0 · run exit=0) =====
a == b            : ★ 공유   (같은 파일 안의 같은 리터럴)
a == c            : ★ 공유   (다른 함수 안의 같은 리터럴)
e == d+6          : ★ 공유   (꼬리 겹침)
strcmp(a,b) = 0 · strcmp(e,tail) = 0  (글자는 어차피 같다)
a-b 의 바이트 차  : 0
d 와 a 의 차가 0 인가 : 아니다
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 ex3.c -o x3c_O2 ; ./x3c_O2 (cc exit=0 · run exit=0) =====
a == b            : ★ 공유   (같은 파일 안의 같은 리터럴)
a == c            : ★ 공유   (다른 함수 안의 같은 리터럴)
e == d+6          : ★ 공유   (꼬리 겹침)
strcmp(a,b) = 0 · strcmp(e,tail) = 0  (글자는 어차피 같다)
a-b 의 바이트 차  : 0
d 와 a 의 차가 0 인가 : 아니다
```

**왜 그런가**

| 빌드 | `a == b` | `a == c` | ★★ `e == d+6` |
|---|---|---|---|
| gcc `-O0` | 공유 | 공유 | ★ **따로** |
| gcc `-O2` | 공유 | 공유 | ★ **공유** |
| gcc `-O2 -fno-merge-constants` | 공유 | 공유 | ★ **따로** |
| clang `-O0` | 공유 | 공유 | ★ **공유** |
| clang `-O2` | 공유 | 공유 | ★ **공유** |

```text
   (가) 따로                          (나) 꼬리 겹침
   | hello world\0 | world\0 |        | hello world\0 |
     ^               ^                  ^         ^
     d               e                  d         e = d+6

   둘 다 적법하다. strcmp 는 어느 판에서도 0 이고 ★ 주소만 갈린다.
```

- ★★ **`a == b` 와 `a == c` 는 다섯 벌 전부 공유**였다. 같은 글자면 **같은 판 하나**를 쓴 것이다.\
  ★ **다섯 벌이 한 글자도 다르지 않으면 보장이라고 믿게 된다** — **그래서 더 위험하다.**
- ★★★ **갈리는 자리는 꼬리 겹침**이다.\
  **gcc 는 `-O0` 에서 따로, `-O2` 에서 공유**, **`-fno-merge-constants` 를 주면 `-O2` 에서도 따로**다.\
  **clang 은 `-O0` 부터 공유**다. ★ **같은 소스·같은 표준·같은 머신에서 갈렸다.**
- ★★ **가장 보수적인 벌은 gcc `-O0`**(과 `-fno-merge-constants`)이다.\
  ★ **그 벌만 보고 「리터럴은 겹치지 않는다」고 적으면**, `-O2` 로 빌드한 날 **반대 결론**이 된다.
- ★★ **`strcmp` 는 어느 벌에서도 0** 이었다. **글자는 언제나 같고 주소만 갈린다** —\
  ★ 그래서 문자열 비교는 **`==` 가 아니라 `strcmp`** 다. `==` 는 「같은 판인가」를 묻는다.
- ★ **`d == a` 는 어느 벌에서도** 「**아니다**」였다. **겹칠 수 있는 것은 꼬리뿐**이다 —\
  **머리를 공유하면 거기서 끝난다는 표시를 넣을 수 없기 때문**이다(널 종단 관례의 직접적 결과).
- ★★★ **다섯 층 중 미명시**다. 표준은 **공유해도 되고 안 해도 된다**고만 한다.\
  **어떤 코드도 이 결과에 의지해서는 안 된다.**
- ★ **공유가 주는 것은 크기**다 — 꼬리를 겹치면 `"world\0"` 여섯 바이트가 통째로 사라진다.\
  ★ **그 대가가 「리터럴 두 개가 정말 두 개인가」가 빌드마다 달라지는 것**이다.
- ★★ **`a - b` 가 0** 으로 찍힌 것도 같은 사실의 다른 얼굴이다 — 두 포인터가 **같은 곳**을 가리킨다.\
  ★ 단 **서로 다른 객체의 포인터를 빼는 것 자체가 위험한 짓**이고, 그 경계는 [15번 형제](../15-pointer-arithmetic-and-indexing/)가 정본이다.

### 5. 세 칸짜리 배열에 네 글자 리터럴을 넣으면 — **되고, 경고도 0건** ★★

**출력**

```c
/* ex4.c */
#include <stdio.h>
#include <string.h>

int main(void) {
    char exact[4] = "abc";     /* 딱 맞는다 — 널까지 들어간다 */
    char tight[3] = "abc";     /* ★ 널이 안 들어간다 (표준이 허용한다) */
    char big[6]   = "abc";     /* 남는 칸은 0 으로 채워진다 */

    printf("exact : sizeof %zu · 바이트 ", sizeof exact);
    for (size_t k = 0; k < sizeof exact; k++) printf("%02x ", (unsigned char)exact[k]);
    printf("· strlen %zu\n", strlen(exact));

    printf("tight : sizeof %zu · 바이트 ", sizeof tight);
    for (size_t k = 0; k < sizeof tight; k++) printf("%02x ", (unsigned char)tight[k]);
    printf("· ★ 널이 없다 -> strlen 은 배열 밖을 읽는다(UB)\n");

    printf("big   : sizeof %zu · 바이트 ", sizeof big);
    for (size_t k = 0; k < sizeof big; k++) printf("%02x ", (unsigned char)big[k]);
    printf("· strlen %zu\n", strlen(big));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex4.c -o x4 (cc exit=0) =====
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic ex4.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex4.c -o x4 ; ./x4 (cc exit=0 · run exit=0) =====
exact : sizeof 4 · 바이트 61 62 63 00 · strlen 3
tight : sizeof 3 · 바이트 61 62 63 · ★ 널이 없다 -> strlen 은 배열 밖을 읽는다(UB)
big   : sizeof 6 · 바이트 61 62 63 00 00 00 · strlen 3
```

**왜 그런가**

```text
   exact[4] = "abc"   61 62 63 00        strlen 3   ★ 정상
   tight[3] = "abc"   61 62 63           ★ 널이 없다 — 그래도 적법 · 경고 0건
   big  [6] = "abc"   61 62 63 00 00 00  strlen 3   ★ 남는 칸은 0
```

- ★★★ **컴파일된다**(`cc exit=0`). **`char tight[3] = "abc"` 는 적법**하다 —\
  **널 종단자만 안 들어가는 경우**는 초과 초기화로 치지 않는다.
- ★★★ **경고는 gcc 도 clang 도 0건**이다. 두 진단 블록이 **비어 있는 것**이 그 근거다.\
  ★ **gcc 13 에는 이것을 잡는 옵션 자체가 없다** —\
  `-Wunterminated-string-initialization` 을 주면 `unrecognized command-line option` 으로 **컴파일이 시작도 안 된다**(`cc exit=1`).\
  ★ **이 문서는 그 실패를 진단 블록으로 싣지 않았다**(「옵션이 없다」는 진단이 아니라 컴파일 실패다).
- ★★ **`big` 의 남는 칸은 0 으로 채워진다.** 바이트가 `61 62 63 00 00 00` 이고 **쓰레기가 아니다.**\
  ★ 그래서 **크기를 넉넉히 잡은 쪽은 안전**하고, **딱 한 칸 모자란 쪽만 위험**하다.
- ★★★ **`tight` 가 위험한 이유**는 「**글자는 다 들어갔는데 끝 표시만 없다**」는 데 있다.\
  **`%s` 로 찍어 보면 정상으로 보인다** — 7번 답이 그 결과다.
- ★ **`char s[] = "abc"` 라고 쓰면 이 사고가 원천적으로 안 난다** — **칸 수를 컴파일러가 센다.**\
  ★ **크기를 손으로 적는 순간** 「널 한 칸」을 사람이 기억해야 한다.

| 쓴 것 | 칸 수 | 널 | 진단 | 그 뒤 `strlen` |
|---|---|---|---|---|
| `char s[] = "abc"` | **4**(컴파일러가 센다) | 있다 | 0건 | **안전** |
| `char exact[4] = "abc"` | 4 | 있다 | 0건 | **안전** |
| `char tight[3] = "abc"` | 3 | ★ **없다** | ★ **0건** | ★★★ **UB** |
| `char big[6] = "abc"` | 6 | 있다(+0 채움) | 0건 | **안전** |
| `char over[2] = "abc"` | 2 | 없다 | ★ **1건** | (실행 안 함) |

### 6. 한 칸을 더 줄이면 — **거기서는 양쪽 다 말해 준다** ★

**출력**

```c
/* ex5.c */
#include <stdio.h>

int main(void) {
    char over[2] = "abc";      /* 두 칸에 네 바이트 — 넘친다 */
    printf("%c%c\n", over[0], over[1]);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex5.c -o /dev/null (cc exit=0) =====
ex5.c: In function ‘main’:
ex5.c:4:20: warning: initializer-string for array of ‘char’ is too long
    4 |     char over[2] = "abc";      /* 두 칸에 네 바이트 — 넘친다 */
      |                    ^~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic ex5.c -o /dev/null (cc exit=0) =====
ex5.c:4:20: warning: initializer-string for char array is too long [-Wexcess-initializers]
    4 |     char over[2] = "abc";      /* 두 칸에 네 바이트 — 넘친다 */
      |                    ^~~~~
1 warning generated.
```

**왜 그런가**

```text
   ★ 경계선은 "널 한 칸" 이다

   char tight[3] = "abc";   널만 못 넣었다   -> ★ 진단 0건 (표준이 허용)
   char over [2] = "abc";   ★ 글자가 넘친다  -> ★ 진단 1건 (양쪽 다)
```

- ★★ 달라진 것은 「**널이 모자란가, 글자가 모자란가**」다. **글자가 잘리면 초과 초기화**이고 진단이 난다.
- ★ **gcc 의 진단에는 플래그 이름이 안 붙는다** — `initializer-string for array of ‘char’ is too long` 뿐이다.\
  **clang 은 `-Wexcess-initializers` 라고 이름을 댄다.**\
  ★ **이름이 없다는 것은 `-Wno-…` 로 끌 수 없다는 뜻**이기도 하다.
- ★ **경고이지 에러가 아니다**(`cc exit=0`). 실행 파일은 나온다.\
  ★ **`-Werror` 를 켜지 않는 한 이 진단은 빌드를 막지 못한다.**
- ★ **두 칸에는 두 바이트만** 들어간다. ★ **이 문서는 `ex5.c` 를 실행하지 않았다** — 컴파일 진단까지만 보았다.
- ★★ **5번과 6번을 이어 읽는 것이 이 주제의 요점**이다 —\
  **표준이 허용하는 쪽(널만 없음)에는 아무 말이 없고**, **명백히 넘친 쪽에만 말한다.**\
  ★ **위험의 크기 순서와 진단의 유무가 뒤집혀 있다** — 조용한 쪽(`tight`)이 **실제로 UB 를 만든다.**

### 7. 널이 없는 배열을 `strlen` 에 넘기면 — **조용히 맞아 보인다** ★★★

**출력**

```c
/* ex6.c */
#include <stdio.h>
#include <string.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    char tight[3] = "abc";     /* 널이 없다 */
    printf("strlen 직전\n");
    printf("strlen(tight) = %zu\n", strlen(tight));
    printf("%%s 로 찍으면 : [%s]\n", tight);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -g ex6.c -o x6 ; ./x6 (cc exit=0 · run exit=0) =====
strlen 직전
strlen(tight) = 3
%s 로 찍으면 : [abc]
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -g -fsanitize=address ex6.c -o x6a ; ./x6a | sed -n '1,/^SUMMARY/p' (cc exit=0 · run exit=1) =====
strlen 직전
=================================================================
==85590==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x7918f4500023 at pc 0x7918f6a7d96f bp 0x7ffd35694930 sp 0x7ffd356940d8
READ of size 4 at 0x7918f4500023 thread T0
    #0 0x7918f6a7d96e in strlen ../../../../src/libsanitizer/sanitizer_common/sanitizer_common_interceptors.inc:391
    #1 0x5cbda230c3fe in main /tmp/c17b/20/ex6.c:8
    #2 0x7918f662a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #3 0x7918f662a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #4 0x5cbda230c1e4 in _start (/tmp/c17b/20/x6a+0x11e4) (BuildId: c31ad5242638fd215017d60788a2581d5d156168)

Address 0x7918f4500023 is located in stack of thread T0 at offset 35 in frame
    #0 0x5cbda230c2b8 in main /tmp/c17b/20/ex6.c:4

  This frame has 1 object(s):
    [32, 35) 'tight' (line 6) <== Memory access at offset 35 overflows this variable
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-buffer-overflow ../../../../src/libsanitizer/sanitizer_common/sanitizer_common_interceptors.inc:391 in strlen
```

> ★ **대조할 것은 주소가 아니라 성질이다.** 근거는 **평범한 실행이 `3`·`[abc]`·`run exit=0`** 이라는 것과,\
> ASan 이 **`stack-buffer-overflow`** 를 **`READ of size 4`** 로 잡고 **`[32, 35) 'tight'`** 를 짚었다는 것,\
> 그리고 **`run exit=1`** 로 바뀐다는 것이다.

**왜 그런가**

```text
   [32] [33] [34] | [35]
   +----+----+----+ +----+
   | 61 | 62 | 63 | | ?? |
   +----+----+----+ +----+
   |<- tight[3] ->| |<- ★ 남의 칸

   strlen : 61? 아니다 -> 62? 아니다 -> 63? 아니다 -> [35] 를 읽는다 -> 마침 0 이라 3 을 돌려줬다
```

- **평범한 실행의 두 줄은 `strlen(tight) = 3` 과 `%s 로 찍으면 : [abc]`** 다.
- ★★★ **종료 코드는 0** 이다. **어디서 봐도 정상**이다.
- ★★ **ASan 은 `stack-buffer-overflow` 로 잡고** **`[32, 35) 'tight'`** 라고 **배열의 범위를 찍은 뒤**\
  「**offset 35 에서 이 변수를 넘었다**」고 말한다. **`run exit=1`** 로 바뀐다.
- ★★ **`READ of size 4` 인 이유**는 「**글자 3 + 끝 표시 1**」이다. `strlen` 은 **0 을 실제로 읽어야** 끝을 알기 때문에\
  **네 번째 바이트를 반드시 읽고**, 그 칸이 **이 배열의 것이 아니다.**\
  ★ **못 가른 것** — 그 `4` 가 **ASan 가로채기의 셈법**인지 **실제 읽기 폭**인지는 확인하지 못했다.
- ★★★ **가장 나쁜 자리인 이유** — **5번의 「경고 0건」과 이 문항의 「`run exit=0` 에 맞는 답」을 이어 붙이면**\
  **컴파일 창도 초록, 실행 창도 초록인데 UB** 다. ★ **틀린 값이 나왔다면 오히려 다행**이었을 것이다.
- ★ **ASan 스택은 위에서 아래로 「누가 읽었나 → 누가 불렀나」** 순서다 — 맨 위가 `strlen`(가로채기),\
  그 다음이 **내 소스 줄**이다.

| 창 | 이 자리에서 무엇을 말하나 |
|---|---|
| 컴파일 경고(gcc·clang) | ★ **아무 말도 안 한다**(5번 답) |
| 화면 출력 `%s` | ★ **`[abc]`** — 정상으로 보인다 |
| 반환값 `strlen` | ★ **3** — 맞는 값처럼 보인다 |
| 종료 코드 | ★ **0** |
| **ASan** | ★★★ **여기서만 드러난다** — `stack-buffer-overflow` · `run exit=1` |

### 8. `strncpy` 를 세 가지 길이로 부르면 — **널이 안 붙는다** ★★

**출력**

```c
/* ex7.c */
#include <stdio.h>
#include <string.h>

static void dump(const char *tag, const char buf[5]) {
    printf("%s : ", tag);
    for (int k = 0; k < 5; k++) printf("%02x ", (unsigned char)buf[k]);
    printf("\n");
}

int main(void) {
    /* (가) 원본이 짧으면 — 남는 칸을 전부 0 으로 채운다 */
    char a[5];
    memset(a, 0x7e, sizeof a);
    strncpy(a, "ab", 5);
    dump("(가) strncpy(a,\"ab\",5)   ", a);

    /* (나) 원본이 딱 맞으면 — 널이 안 붙는다 */
    char b[5];
    memset(b, 0x7e, sizeof b);
    strncpy(b, "abcde", 5);
    dump("(나) strncpy(b,\"abcde\",5)", b);

    /* (다) 원본이 길면 — 잘리고 널도 없다 */
    char c[5];
    memset(c, 0x7e, sizeof c);
    strncpy(c, "abcdefgh", 5);
    dump("(다) strncpy(c,\"abcdefgh\",5)", c);

    /* (라) 안전하게 쓰는 꼴 — 마지막 칸을 직접 0 으로 */
    char d[5];
    strncpy(d, "abcdefgh", sizeof d - 1);
    d[sizeof d - 1] = '\0';
    dump("(라) 마지막 칸을 손으로 0", d);
    printf("     d = [%s] · strlen = %zu\n", d, strlen(d));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex7.c -o x7 (cc exit=0) =====
ex7.c: In function ‘main’:
ex7.c:20:5: warning: ‘strncpy’ output truncated before terminating nul copying 5 bytes from a string of the same length [-Wstringop-truncation]
   20 |     strncpy(b, "abcde", 5);
      |     ^~~~~~~~~~~~~~~~~~~~~~
ex7.c:26:5: warning: ‘strncpy’ output truncated copying 5 bytes from a string of length 8 [-Wstringop-truncation]
   26 |     strncpy(c, "abcdefgh", 5);
      |     ^~~~~~~~~~~~~~~~~~~~~~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 ex7.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 ex7.c -o /dev/null (cc exit=0) =====
ex7.c: In function ‘main’:
ex7.c:20:5: warning: ‘__builtin_strncpy’ output truncated before terminating nul copying 5 bytes from a string of the same length [-Wstringop-truncation]
   20 |     strncpy(b, "abcde", 5);
      |     ^
ex7.c:26:5: warning: ‘__builtin_strncpy’ output truncated copying 5 bytes from a string of length 8 [-Wstringop-truncation]
   26 |     strncpy(c, "abcdefgh", 5);
      |     ^
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex7.c -o x7 ; ./x7 (cc exit=0 · run exit=0) =====
(가) strncpy(a,"ab",5)    : 61 62 00 00 00 
(나) strncpy(b,"abcde",5) : 61 62 63 64 65 
(다) strncpy(c,"abcdefgh",5) : 61 62 63 64 65 
(라) 마지막 칸을 손으로 0 : 61 62 63 64 00 
     d = [abcd] · strlen = 4
```

**왜 그런가**

```text
   시작 : 7e 7e 7e 7e 7e   (★ 무엇이 덮였는지 보려고 미리 채웠다)

   (가) "ab"       -> 61 62 00 00 00   ★ 남는 칸을 전부 0 으로 (7e 가 한 칸도 안 남았다)
   (나) "abcde"    -> 61 62 63 64 65   ★ 널이 없다
   (다) "abcdefgh" -> 61 62 63 64 65   ★ 잘리고 널도 없다
   (라) n-1 복사 + 마지막 칸 0 -> 61 62 63 64 00   [abcd] · strlen 4
```

- ★★ **(가)는 `61 62 00 00 00`** 이다. **`7e` 가 한 칸도 안 남았다** —\
  **`strncpy` 는** 「복사」가 아니라 「**n 바이트를 통째로 쓴다**」에 가깝다.
- ★★★ **(나)·(다)는 `61 62 63 64 65`** 로 **널이 없다.** 원본이 **딱 맞거나 길면** 끝 표시가 안 붙는다.\
  ★ 그 뒤에 `%s`·`strlen` 을 쓰면 **7번과 같은 UB** 가 된다.
- ★ **`0x7e` 로 미리 채운 이유**는 「**0 이 원래 있던 것인지 `strncpy` 가 쓴 것인지**」를 가르기 위해서다.\
  ★ 덮이지 않은 칸이 있었다면 `7e` 로 남았을 것이다.
- ★★ **gcc 는 두 건**을 잡는다(`-Wstringop-truncation`) — **(나)와 (다)** 다. **(가)는 안 잡는다**(널이 붙었으니까).\
  ★★ **`-O2` 에서는 같은 두 건인데 함수 이름이 `__builtin_strncpy` 로 바뀐다** —\
  ★ **진단 문구를 글자로 대조하는 검사는 최적화 수준에서 깨진다.**
- ★★★ **clang 은 `-O2` 에서도 0건**이다. **같은 코드인데 한쪽만 말해 준다.**
- ★ **(라)가 보장하는 것**은 「**널이 있다**」뿐이다. ★ **여전히 보장되지 않는 것은 「잘렸는지 아닌지」** —\
  `d` 는 `abcd` 인데 원본은 `abcdefgh` 였고 **아무도 그 사실을 알려 주지 않는다**(목록의 **49번 주제**).

### 9. `sizeof` 와 `strlen` 이 답하는 것 ★★

**답**

- **`sizeof` 는 상자를 잰다** — **컴파일 시간**에 정해지고 **널 종단자를 포함**한다.\
  **`strlen` 은 약속을 센다** — **실행 시간**에 **첫 0 까지** 걸어가며 세고 **0 은 안 센다.**
- ★ **`char *p = "abc"` 에서 `sizeof p` 가 8 인 이유**(포인터를 잰다)는\
  [16번 형제](../16-array-pointer-decay-and-function-parameters/)와 [08번 형제](../08-sizeof-alignment-and-offsetof/)가 정본이다.
- **갈라지는 입력 둘** —\
  ① **중간에 널이 있는 배열** — `char mid[] = "ab\0cd"` 에서 **6 과 2.**\
  ② **남는 칸이 있는 배열** — `char big[6] = "abc"` 에서 **6 과 3.**
- ★ **널이 아예 없으면 `strlen` 은 「답」을 내지 못한다.** 실측에서 **3 을 돌려줬지만** 그것은\
  **배열 밖의 바이트가 마침 0 이었다**는 뜻이고 **UB** 다. ★ **값이 맞아 보이는 것과 답인 것은 다르다.**
- ★★ **한 줄로** — 「**`sizeof` 는 컴파일러가 아는 것, `strlen` 은 메모리가 말해 주는 것.**」\
  ★ 그래서 **`sizeof` 는 포인터 앞에서 쓸모를 잃고**(8 이 나온다), **`strlen` 은 널 앞에서 쓸모를 잃는다**(없으면 걸어간다).
- ★ **둘을 섞어 쓰는 관용구의 함정** — `sizeof buf - 1` 은 **배열일 때만** 뜻이 있다.\
  포인터에 쓰면 **7** 이라는 그럴듯한 오답이 된다(8 − 1).

### 10. 리터럴로 배열을 초기화하면 왜 복사본인가 ★★

**답**

```text
   char s[] = "abc";     "배열을 만들고 그 안을 채워라"   -> ★ 바이트가 복사된다
   char *p = "abc";      "저기 있는 것의 주소를 가져라"    -> ★ 아무것도 복사되지 않는다
```

- **`char s[] = "abc"` 는 배열을 만들고** 리터럴의 바이트로 채운다. **`char *p = "abc"` 는 리터럴을 가리킨다.**
- ★★ **앞엣것에서 리터럴이 감쇠하지 않는 이유** — **배열 초기화는 원소를 채우는 일**이라\
  리터럴이 **주소로 변하지 않고 「바이트 넷」으로 쓰이기 때문**이다.\
  ★ **감쇠가 안 일어나는 세 자리 중 하나**이고, 그 규칙의 정본은 [16번 형제](../16-array-pointer-decay-and-function-parameters/)다.
- ★★ **「복사본이다」를 출력으로 증명하려면** ① **고쳐 보고**(`arr[0] = 'A'` → `Abc` 가 찍힌다)\
  ② **`sizeof` 를 찍고**(4 대 8) ③ **바이트를 찍는다**(손으로 쓴 배열과 `memcmp = 0`).
- ★★ **저장 기간이 다르다** — 복사본은 **그 블록과 함께 사라지고**, 리터럴은 **프로그램이 끝날 때까지 산다.**\
  ★ 그래서 **`return "hello";` 는 댕글링이 아니고**, **`char s[] = "hello"; return s;` 는 댕글링**이다(목록의 **57번 주제**).
- ★ **가장 싼 고침은 `[]` 한 쌍**이다 — `char *p = "abc"` 를 **`char p[] = "abc"`** 로 바꾸면 고칠 수 있게 된다.\
  ★ 반대로 **읽기만 할 것이면 `const char *p`** 로 받아 **컴파일러에게 대신 막게 한다.**

### 11. 다섯 층과 무게중심 ★★★

**답**

| 층 | 이 주제(20번) | [16번 형제](../16-array-pointer-decay-and-function-parameters/) |
|---|---|---|
| **표준** | 널 종단 관례 · 리터럴의 **정적 저장 기간** · **배열 초기화는 복사** · `char s[3] = "abc"` 가 적법한 것 · 남는 칸이 0 인 것 · `strncpy` 의 계약 | 감쇠 규칙 · 매개변수 재작성 |
| **조건부 표준** | ★ **없다** | ★ **없다** |
| **구현 정의** | `.rodata` 배치 · **쓰기 금지 매핑** · `sizeof(char *)`=8 · `'a'`=0x61 | `sizeof(int)`·`sizeof(int *)` |
| ★★ **미명시** | ★★★ **리터럴 공유 여부**(다섯 벌 중 **꼬리 겹침이 갈렸다**) | ★ 같은 리터럴 공유 여부(**던지지 않았다**) |
| ★★★ **UB (본체)** | **리터럴 수정**(`run exit=139`) · **널 없는 배열에 `strlen`/`%s`**(`run exit=0` 인데 UB) · `strncpy` 뒤 널 없는 버퍼를 문자열로 쓰는 것 | 길이를 잃은 뒤의 경계 넘기 · `static N` 계약 위반 |

- **비어 있는 칸**은 「**조건부 표준**」이다 — 널 종단과 리터럴에는 **매크로로 켜지고 꺼지는 보장이 없다.**\
  ★ 굳이 대면 **널 종단을 보장하는 선택적 부속서의 `_s` 계열**이 있으나 **이 문서는 던지지 않았고**\
  그쪽은 목록의 **49번 주제**의 몫이다.
- ★★★ **가장 두꺼운 칸은 UB** 다 — **리터럴 수정**이 본체이고, **널 없는 배열에 `strlen`** 이 그 옆이다.
- ★★ **두 번째로 두꺼운 칸은 미명시**다. ★ [16번 형제](../16-array-pointer-decay-and-function-parameters/)에서는 그 칸이 **「던지지 않았다」로 비어 있었는데**,\
  여기서는 **다섯 벌을 돌려 채웠고 갈렸다.** ★ **그 칸을 채운 것이 이 주제가 16번에 갚은 빚**이다.
- ★ **도구가 침묵하는 자리 — 층마다 하나씩**\
  **표준** : `char s[3] = "abc"` 에 **경고 0건**(gcc 13 엔 그 옵션조차 없다).\
  **구현 정의** : 컴파일러는 **어디에 놓았는지 말하지 않는다**(`objdump` 로 본다).\
  **미명시** : **어떤 경고도 공유 여부를 말하지 않는다** — 주소를 직접 비교하고 **여러 벌로 빌드**해야 보인다.\
  **UB** : 기본 플래그가 **리터럴 수정에 0건**이고, **널 없는 `strlen` 은 평범한 실행에서 `exit=0`** 이다.

### 12. 경계 — 어디까지가 이 주제인가 ★

**답**

- **`<string.h>` 함수들의 계약 전반**(`strcpy`·`strcat`·`strncat`·`strlen` 의 경계 조건) — 목록의 **49번 주제**가 정본이다.\
  여기서는 **`strncpy` 가 널을 안 붙일 수 있다**는 **한 가지만** 다뤘다.
- **배열이 포인터로 감쇠하는 규칙** — [16번 형제](../16-array-pointer-decay-and-function-parameters/)가 정본이다.
- **배열 밖 접근이 무엇을 만드나** — 목록의 **56번 주제**가 정본이다. 여기서는 **ASan 이 잡았다는 사실까지**다.
- **이 주제가 끝까지 책임지는 것 셋** —\
  ① **문자열이 타입이 아니라 관례**라는 것(`memcmp = 0`)\
  ② **리터럴의 저장 기간과 수정 금지**(정적 · 고치면 UB · `run exit=139`)\
  ③ **널이 있느냐 없느냐**가 만드는 것(`char s[3]` · `strncpy` · 조용한 `strlen`).
- ★ **`char *q = "hi"` 와 `char s[] = "hi"` 의 `sizeof` 대비(3 대 8)** 는 [16번 형제](../16-array-pointer-decay-and-function-parameters/)가 **먼저 다뤘다.**\
  그쪽은 「감쇠하지 않는 자리」로, **여기는 「왜 복사인가·고치면 무엇이 일어나나」로** 읽는다.

```text
   ★ 경계선 그림 — 같은 두 줄을 세 주제가 나눠 본다

   char s[] = "hi";  /  char *q = "hi";
        |                    |
        |  16번 : "감쇠하지 않는 자리다"  (sizeof 3 대 8)
        |  20번 : "왜 복사인가 · q 를 고치면 UB · 리터럴은 어디 사는가"   <- ★ 여기
        |  49번 : "그 뒤 strcpy/strcat/strlen 을 어떻게 부르나"
        v
   56번 : "경계를 넘은 접근이 무엇을 만드나"
```

- ★ **한 줄 경계** — 「**16번은 타입, 20번은 약속과 권한, 49번은 함수, 56번은 결과.**」

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 컴파일러·플래그로 돌렸나 |
|---|---|---|
| `ex.c` (20-a) | `sizeof` **4·8·4** / `strlen` **3·3·3** · **`memcmp = 0`** · 바이트 `61 62 63 00` · `mid` 는 **`sizeof` 6 대 `strlen` 2** · `%s` 는 `[ab]` | gcc `-std=c17 -Wall -Wextra -pedantic` 1벌(실행 포함) |
| `ex2.c` (20-b) | 복사본 수정은 **`Abc`** · 리터럴 수정은 **`run exit=139`**(gcc·clang **둘 다**) · 기본 플래그 **경고 0건** · `-Wwrite-strings` 로 **각 1건**(이름이 서로 다르다) · ASan **`WRITE memory access`·`run exit=1`** · `objdump -h` 에 **`.rodata`** | gcc 4벌(기본·`-Wwrite-strings`·ASan·`objdump` 용) · clang 2벌 |
| `ex3.c` (20-c) | **다섯 벌**의 공유 판정 — `a==b`·`a==c` 는 **전부 공유**, **꼬리 겹침만 갈렸다** · `strcmp` 는 **어느 벌에서도 0** | gcc 3벌(`-O0`·`-O2`·`-O2 -fno-merge-constants`) · clang 2벌(`-O0`·`-O2`) |
| `ex4.c` (20-d) | `exact` `61 62 63 00` · **`tight` `61 62 63`(널 없음)** · `big` `61 62 63 00 00 00` · **경고 gcc 0건 · clang 0건** | gcc 2벌(진단·실행) · clang 1벌 |
| `ex5.c` (20-e) | 초과 초기화는 **양쪽 다 경고**(gcc 는 **플래그 이름 없음** · clang 은 `-Wexcess-initializers`) · **`cc exit=0`** | gcc 1벌 · clang 1벌 · ★ **실행은 안 했다** |
| `ex6.c` (20-f) | 평범한 실행 **`3`·`[abc]`·`run exit=0`** · ASan **`stack-buffer-overflow READ of size 4`·`[32, 35) 'tight'`·`run exit=1`** | gcc 2벌(기본 `-g`·ASan) |
| `ex7.c` (20-g) | `strncpy` 세 경우의 바이트 · gcc **2건**(`-Wstringop-truncation`) · **`-O2` 에서 문구가 `__builtin_strncpy`** · **clang `-O2` 0건** · (라)는 `61 62 63 64 00` | gcc 2벌(`-O0`·`-O2`) · clang 1벌(`-O2`) |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3 · glibc)에서만** 그렇다.

- **리터럴 수정이 `139` 로 죽는 것** — ★ **UB 의 한 가지 발현**일 뿐이다. 표준은 죽으라고 하지 않았다.
- **리터럴이 `.rodata` 에 놓이는 것** — ★ **구현 정의**다.
- **`sizeof(char *)` = 8 · `'a'` = `0x61`** — ★ 구현 정의다.
- **꼬리 겹침 판정** — ★★ **미명시**다. **컴파일러와 `-O` 를 바꾸면 갈린다**(실측).
- **널 없는 `tight` 에 `strlen` 이 `3` 을 낸 것** — ★★ **UB 의 산물이라 아무 근거도 못 된다.**\
  **배열 밖 바이트가 마침 0 이었을 뿐**이고 다음 실행에서 같으리라는 보장이 없다.
- **`-Wstringop-truncation` 이 gcc 에만 있는 것 · `-O2` 에서 `__builtin_` 접두가 붙는 것** — 진단 구현의 분류다.
- **`-Wwrite-strings` 가 켜는 진단의 이름이 두 컴파일러에서 다른 것** — 분류의 차이다.

**널 종단 관례와 「리터럴을 고치면 UB」 자체는 구현 의존이 아니다.**\
정적 저장 기간 · 배열 초기화의 복사 · `char s[3] = "abc"` 의 적법성 · `strncpy` 의 계약은 **어느 C 구현에서도 같다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `ex5.c` 의 **실행** · **번역 단위가 여럿일 때의 리터럴 공유**(링커가 합치는가) ·\
  **쓰기 가능하게 매핑된 환경에서의 리터럴 수정**(이 머신에서는 언제나 139 였다) ·\
  **와이드 문자열(`L"abc"`)** · **`-Wwrite-strings` 를 켠 채 `lit[0] = 'A'` 를 지운 코드**(진단이 초기화 줄에만 붙는지 재확인) ·\
  **`clang` 이 `-O0` 부터 꼬리를 겹치는 이유**(다른 스위치로 끌 수 있는지).
- ★ **블록 없이 산문으로만 적은 것 하나** — 「**gcc 13 에는 `-Wunterminated-string-initialization` 이 없다**」.\
  그 옵션을 주면 `unrecognized command-line option` 으로 **`cc exit=1`** 이다.\
  ★ **컴파일 실패라 진단 블록의 배너 규칙에 맞지 않아** 이 문서는 **블록으로 싣지 않았다.**
- **못 잰 것** — ★ **`READ of size 4` 의 `4` 가 무엇의 4 인가.**\
  「글자 3 + 끝 표시 1」이라는 셈은 맞아떨어지지만, 그 수가 **ASan 가로채기의 셈법**인지\
  **`strlen` 이 실제로 읽은 폭**인지는 **리포트만으로는 가를 수 없다** — 어셈블리나 다른 도구가 필요하다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **gcc 가 `-Wunterminated-string-initialization` 을 갖게 됐는지**(지금은 옵션 자체가 없다).\
  **그러면 5번 답의 「경고 0건」이 바뀐다.**
- ★★ **clang 이 `strncpy` 의 널 누락을 잡게 됐는지**(지금은 `-O2` 에서도 0건).
- ★ **꼬리 겹침 판정** — **컴파일러가 올라가면 다시 다섯 벌을 돌린다.** ★ **미명시 칸이라 언제든 바뀔 수 있다.**
- ★ **`-Wstringop-truncation` 의 문구**(`-O2` 에서 `__builtin_strncpy` 로 바뀌는 것)는 **문구 대조를 깨뜨리는 자리**다.
- **널 종단 관례·리터럴 수정 UB 는 다시 돌릴 필요가 없다** — C89 이후 바뀐 적이 없다.
