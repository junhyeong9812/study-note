# c/syntax/37 — `malloc`/`calloc`/`realloc`/`free`: 「**실패는 `NULL` 하나로 온다 — 그 `NULL` 을 받는 자리가 원본을 지키느냐를 가른다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **gcc-12 12.4.0** ·
> **clang 18.1.3** · **glibc 2.39** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s37a.c`\~`s37k.c` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
> ★★★ **본체 창은 실패 격자** — 탐침 7 × 빌드 8.
> ★★ **흔들리는 칸** — 리포트의 PID · 주소(정규화 기본 규칙) · `realloc` 이 주소를 바꾸는가(선언 — 20 판 가짓수로 찍었다).

## 이 파일이 다시 싣는 소스

★ 8·9번은 질문 파일에 소스가 없다 — 여기 싣는다.

```c
/* s37g.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    char *p = malloc(8);
    if (!p) return 1;
    strcpy(p, "abc");
    free(p);
    printf("[g] free 다음 줄\n");
    int c = p[0];                        /* 해제된 곳을 읽는다 */
    printf("[g] 읽은 뒤 줄 %d\n", c != 0);
    return 0;
}
```

```c
/* s37h.c */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    char *p = malloc(16);
    if (!p) return 1;
    int grew = 0, moved = 0;
    for (size_t n = 32; n <= ((size_t)1 << 20); n *= 2) {
        uintptr_t before = (uintptr_t)p;          /* 옛 주소는 realloc 전에 정수로 적어 둔다 */
        char *t = realloc(p, n);
        if (!t) { free(p); return 1; }
        grew++;
        moved += (uintptr_t)t != before;
        p = t;
    }
    printf("늘린 횟수 %d · 주소가 바뀐 횟수 %d\n", grew, moved);
    free(p);
    return 0;
}
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 실패 격자 — **크기 0 은 `malloc`·`calloc` 이 `ptr`, `realloc(p, 0)` 은 `NULL` · `calloc(n, 2)` 는 `NULL` 인데 `malloc(n * 2)` 는 성공 · 갈린 칸 6 / 49** ★★★

**출력**

```text
===== 실패 격자 — 탐침 7 × 빌드 8 (각 칸 -std=c17 -Wall -Wextra -pedantic) (exit=0) =====
탐침                      	gcc -O0	gcc -O2	clang -O0	clang -O2	gcc ASan	clang ASan	gcc ASan+null	clang ASan+null
malloc(0)                 	ptr/0	ptr/0	ptr/0	ptr/0	ptr/0	ptr/0	ptr/0	ptr/0
calloc(0, 8)              	ptr/0	ptr/0	ptr/0	ptr/0	ptr/0	ptr/0	ptr/0	ptr/0
realloc(NULL, 8)          	ptr/0	ptr/0	ptr/0	ptr/0	ptr/0	ptr/0	ptr/0	ptr/0
realloc(p, 0)             	NULL/0	NULL/0	NULL/0	NULL/0	NULL/0	NULL/0	NULL/0	NULL/0
malloc(SIZE_MAX)          	NULL/ENOMEM	NULL/ENOMEM	NULL/ENOMEM	NULL/0	죽음(exit 1)	죽음(exit 1)	NULL/ENOMEM	NULL/ENOMEM
calloc(n, 2)              	NULL/ENOMEM	NULL/ENOMEM	NULL/ENOMEM	NULL/0	죽음(exit 1)	죽음(exit 1)	NULL/ENOMEM	NULL/ENOMEM
malloc(n * 2) [n*2=2]     	ptr/0	ptr/0	ptr/0	ptr/0	ptr/0	ptr/0	ptr/0	ptr/0
(칸 = 반환/errno · ptr = 널이 아닌 포인터 · n = SIZE_MAX/2+2 · ASan+null = ASAN_OPTIONS=allocator_may_return_null=1)
gcc -O0 칸과 갈린 칸 6 / 49
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s37a.c -o x && ASAN_OPTIONS=strip_path_prefix="$PWD/" ./x 5 | sed -n '/ERROR/,/^SUMMARY/p' (exit=1) =====
==1209613==ERROR: AddressSanitizer: requested allocation size 0xffffffffffffffff (0x800 after adjustments for alignment, red zones etc.) exceeds maximum supported size of 0x10000000000 (thread T0)
    #0 0x7be4760fd9c7 in malloc ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:69
    #1 0x56ade3f2c684 in main s37a.c:27
    #2 0x7be475c2a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #3 0x7be475c2a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #4 0x56ade3f2c284 in _start (x+0x2284) (BuildId: 2696d24b0c19904fe47940f142cb84cb200cc85f)

==1209613==HINT: if you don't care about these errors you may set allocator_may_return_null=1
SUMMARY: AddressSanitizer: allocation-size-too-big ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:69 in malloc
```

```text
===== MANWIDTH=80 man 3 malloc | sed -n '/^   Nonportable behavior/,/^EXAMPLES/p' | grep -v '^EXAMPLES' (exit=0) =====
   Nonportable behavior
       The  behavior  of  these  functions  when the requested size is zero is
       glibc specific; other implementations may return NULL  without  setting
       errno,  and portable POSIX programs should tolerate such behavior.  See
       realloc(3p).

       POSIX requires memory allocators to set errno upon  failure.   However,
       the C standard does not require this, and applications portable to non-
       POSIX platforms should not assume this.

       Portable  programs  should  not use private memory allocators, as POSIX
       and the C standard do not allow replacement of malloc(),  free(),  cal‐
       loc(), and realloc().

```

**왜 그런가**

- ★★★ **크기 0 은 구현 정의**다 — 표준은 「널이거나, 0 이 아닌 크기처럼 굴되 접근하면 안 되는 포인터」 둘 중 하나를 허락한다. 이 판(glibc)은 `malloc(0)`·`calloc(0, 8)` 에 **`ptr`**, `realloc(p, 0)` 에 **`NULL`**(옛 블록을 해제 — 오류 아님)을 준다.
- ★★★ **`calloc(n, 2)` 는 `NULL/ENOMEM`, `malloc(n * 2)` 는 `ptr/0`** — `n * 2` 는 `malloc` 에 닿기 전에 넘쳐 **`2`** 가 됐다(라벨의 `n*2=2`). `calloc` 은 두 수를 따로 받아 곱의 넘침을 본다 — **표준의 약속**이다.
- ★★★ **`malloc(SIZE_MAX)`·`calloc(n, 2)` 두 줄에서만 갈렸다**(6 / 49) — ① **clang `-O2`** 는 `NULL` 이면서 **`errno` 를 `0` 으로 읽었다**(원인은 확정하지 않았다 — 내 추론은 요약 (1)) ② **ASan 기본값**은 `allocation-size-too-big` 로 **멈췄다**(`exit 1`) ③ `allocator_may_return_null=1` 은 보통 빌드와 같다.
- ★★ **`ENOMEM` 은 POSIX(와 glibc)의 약속**이다 — `man 3 malloc` 이 「POSIX 는 `errno` 설정을 요구하지만 **C 표준은 요구하지 않는다**」고 적는다.

### 2. 상수 크기 — **gcc 는 세 수준 다 `NULL` + 경고 1 · clang `-O1`·`-O2` 는 둘 다 `ptr` + 경고 0** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -c s37b.c -o /dev/null (cc exit=0) =====
s37b.c: In function ‘main’:
s37b.c:6:15: warning: argument 1 value ‘18446744073709551615’ exceeds maximum object size 9223372036854775807 [-Walloc-size-larger-than=]
    6 |     void *q = malloc(SIZE_MAX);          /* 크기가 상수 · 받은 메모리는 쓰지 않는다 */
      |               ^~~~~~~~~~~~~~~~
In file included from s37b.c:3:
/usr/include/stdlib.h:672:14: note: in a call to allocation function ‘malloc’ declared here
  672 | extern void *malloc (size_t __size) __THROW __attribute_malloc__
      |              ^~~~~~
```

```text
===== 크기가 상수인 malloc — 컴파일러 2 × 최적화 3 (exit=0) =====
gcc    -O0  경고 1 | malloc(SIZE_MAX)   -> NULL|malloc(SIZE_MAX/2) -> NULL|
gcc    -O1  경고 1 | malloc(SIZE_MAX)   -> NULL|malloc(SIZE_MAX/2) -> NULL|
gcc    -O2  경고 1 | malloc(SIZE_MAX)   -> NULL|malloc(SIZE_MAX/2) -> NULL|
clang  -O0  경고 0 | malloc(SIZE_MAX)   -> NULL|malloc(SIZE_MAX/2) -> NULL|
clang  -O1  경고 0 | malloc(SIZE_MAX)   -> ptr|malloc(SIZE_MAX/2) -> ptr|
clang  -O2  경고 0 | malloc(SIZE_MAX)   -> ptr|malloc(SIZE_MAX/2) -> ptr|
```

```text
===== main 이 부르는 함수를 차례대로 — 어셈블리의 call 만 (컴파일러 2 × 최적화 2) (exit=0) =====
gcc    -O0  | malloc@PLT printf@PLT free@PLT malloc@PLT printf@PLT free@PLT 
gcc    -O2  | malloc@PLT __printf_chk@PLT free@PLT malloc@PLT __printf_chk@PLT free@PLT 
clang  -O0  | malloc@PLT printf@PLT free@PLT malloc@PLT printf@PLT free@PLT 
clang  -O2  | printf@PLT printf@PLT 
```

**왜 그런가**

- ★★ **clang `-O2` 의 `main` 에는 `malloc` 도 `free` 도 없다** — 받은 메모리를 쓰지 않으니 **할당을 통째로 지우고** 결과를 널이 아닌 것으로 뒀다. 「`SIZE_MAX` 할당이 성공했다」가 찍힌다.
- ★★ **gcc 는 호출을 남기고** `-Walloc-size-larger-than` 를 낸다.
- ★ **그래서 1번은 크기를 `volatile` 로** 뒀다 — 컴파일러가 크기를 알면 **실패 시험이 지워진다.** 이 판단은 **컴파일러 구현 층**이다.

### 3. 두 호출 형태 — **보통 빌드는 둘 다 조용 · ASan 기본값은 둘 다 멈춤 · `allocator_may_return_null=1` 에서만 `s37c` 가 `Direct leak of 16 byte(s)`(`s37c.c:9`)** ★★★

**출력**

```text
===== realloc 실패 — 호출 형태 2 × 컴파일러 2 × 실행 3 (-std=c17 -O0 · ASan 판은 -g -fsanitize=address) (exit=0) =====
s37c	gcc  	보통     	exit=0	[c] p == NULL : 1 	-	-
s37c	gcc  	ASan     	exit=1		AddressSanitizer: allocation-size-too-big	-
s37c	gcc  	ASan+null	exit=1	[c] p == NULL : 1 	LeakSanitizer: detected memory leaks	Direct leak of 16 byte
s37c	clang	보통     	exit=0	[c] p == NULL : 1 	-	-
s37c	clang	ASan     	exit=1		AddressSanitizer: allocation-size-too-big	-
s37c	clang	ASan+null	exit=1	[c] p == NULL : 1 	LeakSanitizer: detected memory leaks	Direct leak of 16 byte
s37d	gcc  	보통     	exit=1	[d] tmp == NULL · p 의 내용 : fifteen chars.. 	-	-
s37d	gcc  	ASan     	exit=1		AddressSanitizer: allocation-size-too-big	-
s37d	gcc  	ASan+null	exit=1	[d] tmp == NULL · p 의 내용 : fifteen chars.. 	-	-
s37d	clang	보통     	exit=1	[d] tmp == NULL · p 의 내용 : fifteen chars.. 	-	-
s37d	clang	ASan     	exit=1		AddressSanitizer: allocation-size-too-big	-
s37d	clang	ASan+null	exit=1	[d] tmp == NULL · p 의 내용 : fifteen chars.. 	-	-
누수 보고가 나온 칸 2 / 12
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s37c.c -o x && ASAN_OPTIONS=allocator_may_return_null=1:strip_path_prefix="$PWD/" ./x | sed -n '1,/^SUMMARY/p' (exit=1) =====
==1214874==WARNING: AddressSanitizer failed to allocate 0x7fffffffffffffff bytes
[c] p == NULL : 1

=================================================================
==1214874==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 16 byte(s) in 1 object(s) allocated from:
    #0 0x7068d6afd9c7 in malloc ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:69
    #1 0x63c76822a27e in main s37c.c:9
    #2 0x7068d662a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #3 0x7068d662a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #4 0x63c76822a1a4 in _start (x+0x11a4) (BuildId: 0c5e4b615cec930918aaf9a9cf9f837392413378)

SUMMARY: AddressSanitizer: 16 byte(s) leaked in 1 allocation(s).
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s37c.c -o x && ASAN_OPTIONS=strip_path_prefix="$PWD/" ./x | sed -n '1,/^SUMMARY/p' (exit=1) =====
=================================================================
==1214895==ERROR: AddressSanitizer: requested allocation size 0x7fffffffffffffff (0x8000000000001000 after adjustments for alignment, red zones etc.) exceeds maximum supported size of 0x10000000000 (thread T0)
    #0 0x748234afc778 in realloc ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:85
    #1 0x5fade90102c4 in main s37c.c:12
    #2 0x74823462a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #3 0x74823462a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #4 0x5fade90101a4 in _start (x+0x11a4) (BuildId: 0c5e4b615cec930918aaf9a9cf9f837392413378)

==1214895==HINT: if you don't care about these errors you may set allocator_may_return_null=1
SUMMARY: AddressSanitizer: allocation-size-too-big ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:85 in realloc
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s37d.c -o x && ASAN_OPTIONS=allocator_may_return_null=1:strip_path_prefix="$PWD/" ./x (exit=1) =====
==1214902==WARNING: AddressSanitizer failed to allocate 0x7fffffffffffffff bytes
[d] tmp == NULL · p 의 내용 : fifteen chars..
```

```text
===== 정적 도구 — 소스 4 × 도구 5 (exit=0) =====
소스  	gcc -Wall	gcc-12 -fanalyzer	gcc -fanalyzer	clang -Wall	clang --analyze
s37c  	경고 0	경고 0	경고 0	경고 0	경고 1
s37d  	경고 0	경고 0	경고 0	경고 0	경고 0
s37f  	경고 1	경고 2	경고 2	경고 0	경고 1
s37g  	경고 1	경고 2	경고 2	경고 0	경고 1
(각 칸 -std=c17 -Wall -Wextra -pedantic -c)
경고가 나온 칸 9 / 20
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic --analyze s37c.c -o /dev/null (cc exit=0) =====
s37c.c:14:5: warning: Potential leak of memory pointed to by 'p' [unix.Malloc]
   14 |     free(p);
      |     ^~~~~~~
1 warning generated.
```

**왜 그런가**

- ★★★ **표준 — 새 객체를 못 잡으면 옛 객체는 해제되지 않고 값도 그대로**다. `p = realloc(p, n)` 은 그 옛 객체의 **유일한 주소를 `NULL` 로 덮는다** → 누수. `tmp` 로 받으면 `p` 가 남아 **옛 내용을 읽고 `free` 한다**(`s37d` 가 `fifteen chars..` 를 찍었다).
- ★★★ **보통 빌드는 누수를 말하지 않는다**(`exit=0`). **ASan 기본값은 실패 경로 앞에서 멈춘다** — 이 칸에서는 두 형태가 **구분되지 않는다.** `allocator_may_return_null=1` 을 줘야 **LSan 이 `s37c` 만** 잡는다 — **2 / 12**.
- ★★ **16 바이트 · `s37c.c:9`** — LSan 은 「**어디서 잡은 블록이 주인을 잃었나**」를 말하므로 `malloc(16)` 한 줄을 가리킨다.
- ★★ **정적 도구 중에는 `clang --analyze` 하나**가 `Potential leak` 를 냈다 — gcc `-fanalyzer` 두 판은 0.

### 4. `setrlimit` — **보통 빌드는 `NULL` 을 받고 조용 · ASan 판은 `realloc` 은 `NULL` 인데 종료 시 검사기가 `out of memory` 로 죽는다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s37e.c -o x && ./x (exit=0) =====
[e] setrlimit = 0
[e] p == NULL : 1
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s37e.c -o x && ASAN_OPTIONS=allocator_may_return_null=1:strip_path_prefix="$PWD/" ./x | grep -v -E '^ +#[0-9]' (exit=1) =====
[e] setrlimit = 0
[e] p == NULL : 1
==1215232==ERROR: AddressSanitizer: out of memory: failed to allocate 0x201000 (2101248) bytes of ScopedStackWithGuard (error code: 12)
ERROR: Failed to mmap
```

**왜 그런가**

- ★★ **주소 공간 1 GiB 에서 2 GiB 요청은 실패한다** — 두 판 다 `p == NULL : 1`.
- ★★★ **LSan 은 끝날 때 자기 스택을 `mmap` 해야 하는데 그것도 한도에 걸렸다** — `ScopedStackWithGuard` · `Failed to mmap`. **리포트가 없는 것은 검사가 안 돈 것**이다(누수 없음이 아니다).
- ★ 3번은 **크기로** 실패를 일으켜 한도를 건드리지 않았다 — 검사기가 살아 있게.

### 5. `free(NULL)` · 두 번째 `free(p)` — **gcc `-Wuse-after-free` · `cc exit=0` · 보통 빌드는 두 줄 찍고 `run exit=134`(`double free detected in tcache 2`) · ASan `attempting double-free` + 스택 셋** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s37f.c -o /dev/null (cc exit=0) =====
s37f.c: In function ‘main’:
s37f.c:12:5: warning: pointer ‘p’ used after ‘free’ [-Wuse-after-free]
   12 |     free(p);
      |     ^~~~~~~
s37f.c:10:5: note: call to ‘free’ here
   10 |     free(p);
      |     ^~~~~~~
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s37f.c -o x ; ./x (cc exit=0 · run exit=134) =====
[f] free(NULL) 다음 줄
[f] 첫 free(p) 다음 줄
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s37f.c -o x ; ./x 2>&1 >/dev/null (cc exit=0 · run exit=134) =====
free(): double free detected in tcache 2
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s37f.c -o x && ./x 2>/dev/null (exit=1) =====
[f] free(NULL) 다음 줄
[f] 첫 free(p) 다음 줄
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s37f.c -o x && ASAN_OPTIONS=strip_path_prefix="$PWD/" ./x 2>&1 >/dev/null | sed -n '1,/^SUMMARY/p' (exit=1) =====
=================================================================
==1215659==ERROR: AddressSanitizer: attempting double-free on 0x502000000010 in thread T0:
    #0 0x5c00ae4e2efa in free (x+0xc5efa) (BuildId: aa8f7381545f516d4b9c2036589404d687d45be6)
    #1 0x5c00ae5217e0 in main s37f.c:12:5
    #2 0x7efa4162a1c9 in __libc_start_call_main csu/../sysdeps/nptl/libc_start_call_main.h:58:16
    #3 0x7efa4162a28a in __libc_start_main csu/../csu/libc-start.c:360:3
    #4 0x5c00ae448344 in _start (x+0x2b344) (BuildId: aa8f7381545f516d4b9c2036589404d687d45be6)

0x502000000010 is located 0 bytes inside of 8-byte region [0x502000000010,0x502000000018)
freed by thread T0 here:
    #0 0x5c00ae4e2efa in free (x+0xc5efa) (BuildId: aa8f7381545f516d4b9c2036589404d687d45be6)
    #1 0x5c00ae5217c9 in main s37f.c:10:5
    #2 0x7efa4162a1c9 in __libc_start_call_main csu/../sysdeps/nptl/libc_start_call_main.h:58:16
    #3 0x7efa4162a28a in __libc_start_main csu/../csu/libc-start.c:360:3
    #4 0x5c00ae448344 in _start (x+0x2b344) (BuildId: aa8f7381545f516d4b9c2036589404d687d45be6)

previously allocated by thread T0 here:
    #0 0x5c00ae4e3193 in malloc (x+0xc6193) (BuildId: aa8f7381545f516d4b9c2036589404d687d45be6)
    #1 0x5c00ae52179e in main s37f.c:8:15
    #2 0x7efa4162a1c9 in __libc_start_call_main csu/../sysdeps/nptl/libc_start_call_main.h:58:16
    #3 0x7efa4162a28a in __libc_start_main csu/../csu/libc-start.c:360:3
    #4 0x5c00ae448344 in _start (x+0x2b344) (BuildId: aa8f7381545f516d4b9c2036589404d687d45be6)

SUMMARY: AddressSanitizer: double-free (x+0xc5efa) (BuildId: aa8f7381545f516d4b9c2036589404d687d45be6) in free
```

**왜 그런가**

- ★★★ **`free(NULL)` 은 표준이 「아무 일도 없다」고 약속**한다 — 첫 줄이 찍혔다.
- ★★★ **두 번째 `free(p)` 는 UB** 다. 이 판에서는 **glibc 의 tcache 검사**가 잡아 `abort`(134) 했고, ASan 은 **둘째 free · 첫 free · 처음 malloc** 세 스택을 줬다. 세 번째 `printf` 는 어느 판에서도 안 찍혔다.
- ★ **gcc 는 컴파일 때 이미 경고**했지만 빌드는 통과한다(`cc exit=0`).

### 6. `realloc(p, 0)` — **이 판은 `NULL` · 판에 따라 갈린 줄 0 / 8 · `-Walloc-zero` 는 기본 묶음 밖** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s37k.c -o x ; ./x (cc exit=0 · run exit=0) =====
realloc(p, 0) -> NULL
```

```text
===== realloc(p, 0) — 컴파일러 3 × 플래그 × 판 2 (exit=0) =====
컴파일러 · 플래그             	-std=c17	-std=c2x
gcc-12 -Wall -Wextra -pedantic	경고 0 · cc exit=0	경고 0 · cc exit=0
gcc-12 -Wall -Wextra -pedantic -Walloc-zero	경고 1 · cc exit=0	경고 1 · cc exit=0
gcc-12 UBSan 실행             	runtime error 0 · run exit=0	runtime error 0 · run exit=0
gcc -Wall -Wextra -pedantic   	경고 0 · cc exit=0	경고 0 · cc exit=0
gcc -Wall -Wextra -pedantic -Walloc-zero	경고 1 · cc exit=0	경고 1 · cc exit=0
gcc UBSan 실행                	runtime error 0 · run exit=0	runtime error 0 · run exit=0
clang -Wall -Wextra -pedantic 	경고 0 · cc exit=0	경고 0 · cc exit=0
clang UBSan 실행              	runtime error 0 · run exit=0	runtime error 0 · run exit=0
c17 과 c2x 가 갈린 줄 0 / 8
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic -Walloc-zero -c s37k.c -o /dev/null (cc exit=0) =====
s37k.c: In function ‘main’:
s37k.c:7:15: warning: argument 2 value is zero [-Walloc-zero]
    7 |     char *q = realloc(p, 0);              /* 크기 0 으로 realloc */
      |               ^~~~~~~~~~~~~
In file included from s37k.c:2:
/usr/include/stdlib.h:683:14: note: in a call to allocation function ‘realloc’ declared here
  683 | extern void *realloc (void *__ptr, size_t __size)
      |              ^~~~~~~
```

**왜 그런가**

- ★★★ **C23 은 크기 0 의 `realloc` 을 UB 로 옮겼다**(N3220 부록의 바뀐 점 목록 「zero-sized reallocations with realloc are undefined behavior」). 그런데 **세 컴파일러의 경고 · UBSan 모두 `-std=` 를 가리지 않는다** — 0 / 8.
- ★★ **`-Walloc-zero` 는 판과 무관하게** 크기 0 을 알린다 — 켜야만 나온다.
- ★ **이 판(glibc)의 동작**은 「옛 블록 해제 + `NULL`」이다 — 표준이 약속한 것이 아니다.

### 7. 인자 모양 — **`calloc` 은 곱하기 전의 두 수를 받는다 · `malloc` 은 이미 곱해진 한 수만 받는다** ★★

**왜 그런가**

- ★★ **`malloc(n * size)` 의 곱은 호출하는 쪽에서 `size_t` 로 계산된다** — 부호 없는 산술이라 넘치면 **조용히 한 바퀴 돈다**(UB 도 아니다). `malloc` 에 닿는 것은 **결과 한 수**라 넘쳤는지 알 방법이 없다.
- ★★ **`calloc(nmemb, size)` 는 두 수를 받으니** 할당기가 곱의 넘침을 검사할 수 있다 — 표준이 「**곱이 `size_t` 를 한 바퀴 돌면 널**」이라고 **요구**한다.
- ★ `malloc` 으로는 **`if (n > SIZE_MAX / size)`** 를 곱하기 전에 검사한다(`size > 0` 일 때).

### 8. 해제 후 읽기 — **`heap-use-after-free` · `READ of size 1` · `s37g.c:12:13`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s37g.c -o /dev/null (cc exit=0) =====
s37g.c: In function ‘main’:
s37g.c:12:14: warning: pointer ‘p’ used after ‘free’ [-Wuse-after-free]
   12 |     int c = p[0];                        /* 해제된 곳을 읽는다 */
      |             ~^~~
s37g.c:10:5: note: call to ‘free’ here
   10 |     free(p);
      |     ^~~~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s37g.c -o x && ./x 2>/dev/null (exit=1) =====
[g] free 다음 줄
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s37g.c -o x && ASAN_OPTIONS=strip_path_prefix="$PWD/" ./x 2>&1 >/dev/null | sed -n '1,/^SUMMARY/p' (exit=1) =====
=================================================================
==1217978==ERROR: AddressSanitizer: heap-use-after-free on address 0x502000000010 at pc 0x5cace5db380a bp 0x7ffce66c7a50 sp 0x7ffce66c7a48
READ of size 1 at 0x502000000010 thread T0
    #0 0x5cace5db3809 in main s37g.c:12:13
    #1 0x7f274682a1c9 in __libc_start_call_main csu/../sysdeps/nptl/libc_start_call_main.h:58:16
    #2 0x7f274682a28a in __libc_start_main csu/../csu/libc-start.c:360:3
    #3 0x5cace5cda344 in _start (x+0x2b344) (BuildId: eff007c8323d3b2527d37774c00acdda511d0418)

0x502000000010 is located 0 bytes inside of 8-byte region [0x502000000010,0x502000000018)
freed by thread T0 here:
    #0 0x5cace5d74efa in free (x+0xc5efa) (BuildId: eff007c8323d3b2527d37774c00acdda511d0418)
    #1 0x5cace5db37c2 in main s37g.c:10:5
    #2 0x7f274682a1c9 in __libc_start_call_main csu/../sysdeps/nptl/libc_start_call_main.h:58:16
    #3 0x7f274682a28a in __libc_start_main csu/../csu/libc-start.c:360:3
    #4 0x5cace5cda344 in _start (x+0x2b344) (BuildId: eff007c8323d3b2527d37774c00acdda511d0418)

previously allocated by thread T0 here:
    #0 0x5cace5d75193 in malloc (x+0xc6193) (BuildId: eff007c8323d3b2527d37774c00acdda511d0418)
    #1 0x5cace5db3787 in main s37g.c:7:15
    #2 0x7f274682a1c9 in __libc_start_call_main csu/../sysdeps/nptl/libc_start_call_main.h:58:16
    #3 0x7f274682a28a in __libc_start_main csu/../csu/libc-start.c:360:3
    #4 0x5cace5cda344 in _start (x+0x2b344) (BuildId: eff007c8323d3b2527d37774c00acdda511d0418)

SUMMARY: AddressSanitizer: heap-use-after-free s37g.c:12:13 in main
```

**왜 그런가**

- ★★ **ASan 은 해제된 블록을 격리(quarantine)해 두고** 그 자리를 읽으면 **세 스택**(읽기 · free · malloc)을 준다. 1 바이트(`char`) 읽기다.
- ★ **보통 빌드의 값은 UB 의 한 판 결과**라 싣지 않았다 — 무엇이 찍혀도 근거가 아니다. gcc 는 컴파일 때 `-Wuse-after-free` 를 낸다.

### 9. `realloc` 의 주소 — **이 판에서 16 번 중 3 번 · 20 판 한 가지 · 그래도 판정 불가** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s37h.c -o x ; ./x (cc exit=0 · run exit=0) =====
늘린 횟수 16 · 주소가 바뀐 횟수 3
```

```text
===== realloc 으로 16 번 늘리기 — 컴파일러 2 × 20 판 (-std=c17 -O0) (exit=0) =====
gcc    20 판 · 서로 다른 줄 1 가지
clang  20 판 · 서로 다른 줄 1 가지
```

**왜 그런가**

- ★★ **이 판에서는 흔들리지 않았다**(20 판 한 가지 줄) — 그러나 이것은 **할당자 상태의 관찰**이다.
- ★★★ **표준은 「새 포인터는 옛 포인터와 같은 값일 수도 있다」까지만** 말한다. 옛 객체는 **해제되었으므로** 성공한 `realloc` 뒤에 옛 포인터를 쓰면 **해제 후 사용**이다 — 주소가 같았든 달랐든.

### 10. 형제와 이어서 — **30편은 「옛 흔적 바이트 세기」 + MSan 탐침 P7 로 쟀다 · 이 편은 `calloc` 쪽 MSan 칸(0 줄)을 더했다** ★★

**출력**

```text
===== clang -fsanitize=memory -x c /dev/null -c -o /dev/null && echo 'clang -fsanitize=memory 받음' (exit=0) =====
clang -fsanitize=memory 받음
```

```text
===== 빌린 뒤 쓰기 전에 읽기 — malloc / calloc × 최적화 2 (clang -fsanitize=memory) (exit=0) =====
malloc -O0  run exit=1 · MSan 리포트 1줄 | #0 0x… in main s37i.c:8:9|
malloc -O2  run exit=1 · MSan 리포트 1줄 | #0 0x… in main s37i.c:8:9|
calloc -O0  run exit=0 · MSan 리포트 0줄 | 
calloc -O2  run exit=0 · MSan 리포트 0줄 | 
```

**왜 그런가**

- ★★ **30번 형제 (6)** — `malloc` 은 `-O0` 에서 **직전에 해제한 조각의 `0xAB` 가 48 / 48 남았고**, `calloc` 은 **네 벌 다 64 / 64 가 0**. 같은 형제의 불확정 값 탐침 **P7(`malloc`)** 을 MSan 이 보고했다.
- ★★ **이 편의 칸** — 같은 분기를 두고 `malloc` 은 **리포트 1**, `calloc` 은 **0**. `calloc` 의 0 은 **쓰인 값**이라 MSan 이 침묵하는 것이 옳다.
- ★ **모든 비트 0 이 널 포인터 · `0.0` 이라는 보장은 없다** — 표준은 「모든 비트 0」만 말한다. 널 포인터와 `0.0` 의 표현은 **구현이 정한다**(★ 이 편은 던지지 않았다 — 28·30번 형제도 그 자리를 비워 두었다).

### 11. 다섯 층 — **표준이 실패의 모양을, 구현이 크기 0 과 `errno` 를 정한다 · 누수는 UB 가 아니다** ★★★

**왜 그런가**

- **표준** — 못 잡으면 널 · 실패한 `realloc` 은 원본 보존 · `calloc` 의 넘침 검사와 0 · `free(NULL)` · 기본 정렬 · `realloc(NULL, n)`.
- **구현 정의** — 크기 0 의 반환 · `errno = ENOMEM`(POSIX) · glibc 의 `PTRDIFF_MAX` 상한 · tcache double free 검사.
- **컴파일러 구현** — clang 의 할당 삭제 · clang `-O2` 의 `errno` `0` · ASan 의 멈춤 · 경고 묶음.
- **미명시** — 연속 할당의 순서·인접성 · `realloc` 이 옮기느냐.
- **UB** — double free · 해제 후 사용 · C23 `realloc(p, 0)` · 넘친 곱으로 받은 블록 밖 쓰기.
- ★★★ **`p = realloc(p, n)` 의 누수는 UB 가 아니다** — 적법한 프로그램이 메모리를 **돌려주지 않았을 뿐**이다. 그래서 컴파일러도 UBSan 도 할 말이 없고, **ASan 기본값은 실패를 일으키기 전에 멈춰** 거기 가지 못한다.
- ★★ **네 번째 창 = `allocator_may_return_null=1` 을 준 LSan.** 못 보는 것 — **스택·레지스터에 옛 값이 남으면 「도달 가능」으로 본다**(38편 격자의 clang 칸) · **주소 공간 한도 아래에서는 검사 자체가 못 돈다**(4번).

### 12. 경계 ★

**왜 그런가**

- **빈 목록 · 분할 · 병합** — [`data-structure/35-allocator/`](../../../../../data-structure/35-allocator/) 서머리의 「구현 — FreeListAllocator」 절(「할당(분할)」·「해제(병합 coalescing)」·「단편화」 소절).
- **소유권을 시그니처로** — [38번 형제](../38-expressing-ownership-conventions-in-code/).
- ★ 이 주제가 책임지는 것 — ① **실패의 모양**(격자 · 크기 0 · 넘침 · `errno`) ② **`realloc` 호출 형태**(누수 · 그것을 보는 창) ③ **해제 규칙**(`free(NULL)` · double free · UAF · C23).

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s37a.c` | ★★★ **실패 격자 56칸 · 갈린 칸 6 / 49** · ASan 멈춤 리포트 | 빌드 6 · 실행 56 · 진단 2 · 리포트 1 |
| `s37b.c` | ★★ clang 할당 삭제 · `call` 목록 | 빌드 6 · 어셈블리 4 · 진단 1 |
| `s37c.c`·`s37d.c` | ★★★ **누수 격자 2 / 12** · 리포트 셋 · 정적 도구 | 실행 12 · 리포트 3 · 진단 11 |
| `s37e.c` | ★★ `setrlimit` · 검사기 `out of memory` | 2 |
| `s37f.c`·`s37g.c` | ★★ `free(NULL)` · glibc `abort` · ASan 두 리포트 · `-Wuse-after-free` | 실행 5 · 진단 12 |
| `s37h.c` | ★ 주소 이동 3 / 16 · 20 판 × 2 한 가지 | 41 |
| `s37i.c` | ★★ MSan `malloc` 1 · `calloc` 0 | 4 |
| `s37j.c` | ★ 정렬 64 / 64 | 4 |
| `s37k.c` | ★★ **판 격자 0 / 8** · `-Walloc-zero` | 진단 12 · 실행 7 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. 흔들린 칸은 **리포트의 PID · 주소**뿐이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **1번의 크기 0 칸 · `errno` 칸** — glibc 2.39 와 두 컴파일러의 것이다.
- ★★ **2번** — clang 18 의 최적화 선택.
- ★★ **3·4번의 ASan 동작** — 지원 한도 `0x10000000000` · `allocator_may_return_null` 기본값 0 · 종료 시 LSan.
- ★ **5번의 `abort`** — glibc tcache 검사. **9번의 3 / 16** — 이 판의 할당자 상태.

**못 잡으면 널 · 실패한 `realloc` 의 원본 보존 · `calloc` 의 넘침 검사와 모든 비트 0 · `free(NULL)` · double free 와 해제 후 사용이 UB 인 것 · C23 의 `realloc(p, 0)` UB 는 구현 의존이 아니다.**\
어느 C 구현에서도 같다(판 안에서).

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `reallocarray` · `aligned_alloc` · C23 `free_sized` · clang 에 `-Walloc-zero` 같은 경고가 있는지.
- ★ **못 잰 것** — **Valgrind**(설치 안 됨 — `command -v` `exit=1`) · clang `-O2` `errno` `0` 의 원인(어셈블리로 확정하지 않음).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **6번 판 격자** — 컴파일러가 C23 의 `realloc(p, 0)` UB 를 경고하기 시작할 수 있다.
- ★★ **1번 clang `-O2` 의 `errno` 칸 · 2번 할당 삭제** — 최적화기의 선택.
- ★★ **3번 · 4번** — ASan 의 기본값과 한도.
