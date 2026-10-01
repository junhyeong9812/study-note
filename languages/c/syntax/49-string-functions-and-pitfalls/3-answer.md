# c/syntax/49 — `<string.h>` 문자열 함수와 함정: 「**`n` 이 붙은 함수도 「널까지 n」을 약속하지 않는다 — 함수마다 `n` 의 뜻이 다르고, 널 종단은 함수가 아니라 호출자가 확인한다**」 — 정답

## 이 파일이 다시 싣는 소스

★ 1번 · 8번의 블록을 낸 소스를 다시 둔다.

```c
/* s49a.c */
#define _DEFAULT_SOURCE                  /* 기능 매크로 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *const SRC[] = { "abc", "abcdefgh", "abcdefghijkl" };

int main(int argc, char **argv) {
    if (argc < 3) return 2;
    int fn = atoi(argv[1]);
    const char *s = SRC[atoi(argv[2])];
    char d[8];
    char before[8];
    long ret = 0;

    memset(d, 0x7e, sizeof d);
    if (fn == 3 || fn == 4) d[0] = '\0';          /* 이어 붙일 빈 문자열 */
    memcpy(before, d, sizeof d);

    switch (fn) {
    case 1: strcpy(d, s); break;
    case 2: strncpy(d, s, sizeof d); break;
    case 3: strncat(d, s, sizeof d); break;
    case 4: strncat(d, s, sizeof d - 1); break;
    case 5: ret = snprintf(d, sizeof d, "%s", s); break;
    case 6: ret = (long)strlcpy(d, s, sizeof d); break;
    case 7: { size_t n = strlen(s) < sizeof d ? strlen(s) : sizeof d;
              memcpy(d, s, n); break; }
    }

    int changed = 0;
    for (size_t i = 0; i < sizeof d; i++) changed += d[i] != before[i];
    printf("%s\t%d\t%ld\n", memchr(d, '\0', sizeof d) != NULL ? "있음" : "없음", changed, ret);
    return 0;
}
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 경계 조건 격자 — **널 종단 안 된 칸 5 / 21 · 넘친 칸 4 / 21 · gcc `-O2` 는 넷 다 멈춤 · clang `-O2` 는 하나도 안 멈춤** ★★★

**출력**

```text
===== 경계 조건 격자 — 함수 7 × 원본 길이 3 × 빌드 3 (d 는 char[8]) (exit=0) =====
함수                          	원본 길이	gcc ASan -O0	gcc -O2 (보통 빌드)	clang -O2 (보통 빌드)
strcpy(d, s)                  	짧음 3   	널 있음 · 쓴 4 · 반환 0	널 있음 · 쓴 4 · 반환 0	널 있음 · 쓴 4 · 반환 0
strcpy(d, s)                  	같음 8   	넘침 stack-buffer-overflow (exit 1)	fortify 멈춤 (exit 134)	안 멈춤 (exit 0) — UB
strcpy(d, s)                  	김 12    	넘침 stack-buffer-overflow (exit 1)	fortify 멈춤 (exit 134)	안 멈춤 (exit 0) — UB
strncpy(d, s, sizeof d)       	짧음 3   	널 있음 · 쓴 8 · 반환 0	널 있음 · 쓴 8 · 반환 0	널 있음 · 쓴 8 · 반환 0
strncpy(d, s, sizeof d)       	같음 8   	널 없음 · 쓴 8 · 반환 0	널 없음 · 쓴 8 · 반환 0	널 없음 · 쓴 8 · 반환 0
strncpy(d, s, sizeof d)       	김 12    	널 없음 · 쓴 8 · 반환 0	널 없음 · 쓴 8 · 반환 0	널 없음 · 쓴 8 · 반환 0
strncat(d, s, sizeof d)       	짧음 3   	널 있음 · 쓴 4 · 반환 0	널 있음 · 쓴 4 · 반환 0	널 있음 · 쓴 4 · 반환 0
strncat(d, s, sizeof d)       	같음 8   	넘침 stack-buffer-overflow (exit 1)	fortify 멈춤 (exit 134)	안 멈춤 (exit 0) — UB
strncat(d, s, sizeof d)       	김 12    	넘침 stack-buffer-overflow (exit 1)	fortify 멈춤 (exit 134)	안 멈춤 (exit 0) — UB
strncat(d, s, sizeof d - 1)   	짧음 3   	널 있음 · 쓴 4 · 반환 0	널 있음 · 쓴 4 · 반환 0	널 있음 · 쓴 4 · 반환 0
strncat(d, s, sizeof d - 1)   	같음 8   	널 있음 · 쓴 8 · 반환 0	널 있음 · 쓴 8 · 반환 0	널 있음 · 쓴 8 · 반환 0
strncat(d, s, sizeof d - 1)   	김 12    	널 있음 · 쓴 8 · 반환 0	널 있음 · 쓴 8 · 반환 0	널 있음 · 쓴 8 · 반환 0
snprintf(d, sizeof d, "%s", s)	짧음 3   	널 있음 · 쓴 4 · 반환 3	널 있음 · 쓴 4 · 반환 3	널 있음 · 쓴 4 · 반환 3
snprintf(d, sizeof d, "%s", s)	같음 8   	널 있음 · 쓴 8 · 반환 8	널 있음 · 쓴 8 · 반환 8	널 있음 · 쓴 8 · 반환 8
snprintf(d, sizeof d, "%s", s)	김 12    	널 있음 · 쓴 8 · 반환 12	널 있음 · 쓴 8 · 반환 12	널 있음 · 쓴 8 · 반환 12
strlcpy(d, s, sizeof d)       	짧음 3   	널 있음 · 쓴 4 · 반환 3	널 있음 · 쓴 4 · 반환 3	널 있음 · 쓴 4 · 반환 3
strlcpy(d, s, sizeof d)       	같음 8   	널 있음 · 쓴 8 · 반환 8	널 있음 · 쓴 8 · 반환 8	널 있음 · 쓴 8 · 반환 8
strlcpy(d, s, sizeof d)       	김 12    	널 있음 · 쓴 8 · 반환 12	널 있음 · 쓴 8 · 반환 12	널 있음 · 쓴 8 · 반환 12
memcpy(d, s, n)               	짧음 3   	널 없음 · 쓴 3 · 반환 0	널 없음 · 쓴 3 · 반환 0	널 없음 · 쓴 3 · 반환 0
memcpy(d, s, n)               	같음 8   	널 없음 · 쓴 8 · 반환 0	널 없음 · 쓴 8 · 반환 0	널 없음 · 쓴 8 · 반환 0
memcpy(d, s, n)               	김 12    	널 없음 · 쓴 8 · 반환 0	널 없음 · 쓴 8 · 반환 0	널 없음 · 쓴 8 · 반환 0
(각 줄 = ./x <함수> <길이> · d 는 char[8] 을 0x7e 로 채운 것(strncat 두 줄은 d[0] 만 0) · 널 = memchr(d, 0, 8) · 쓴 = 호출 전과 달라진 바이트 수 · 반환 = snprintf/strlcpy 의 값(나머지는 0) · memcpy 의 n = min(strlen(s), sizeof d))
널 종단 안 된 칸 5 / 21
넘친 칸(ASan) 4 / 21
넘친 칸 가운데 gcc -O2 가 멈춘 칸 4 / 4 · clang -O2 가 멈춘 칸 0 / 4
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s49a.c -o x 2>/dev/null && ASAN_OPTIONS=strip_path_prefix="$PWD/" ./x 1 2 | sed -n '1,/^SUMMARY/p' (exit=1) =====
=================================================================
==1212269==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x780f4c800028 at pc 0x780f4eca7923 bp 0x7ffe5bd199d0 sp 0x7ffe5bd19178
WRITE of size 13 at 0x780f4c800028 thread T0
    #0 0x780f4eca7922 in strcpy ../../../../src/libsanitizer/asan/asan_interceptors.cpp:563
    #1 0x604a9b5bf63f in main s49a.c:21
    #2 0x780f4e82a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #3 0x780f4e82a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #4 0x604a9b5bf304 in _start (x+0x1304) (BuildId: 288822a83d8901ad63526cf6eb4aa8fea8a04a2d)

Address 0x780f4c800028 is located in stack of thread T0 at offset 40 in frame
    #0 0x604a9b5bf3d8 in main s49a.c:8

  This frame has 2 object(s):
    [32, 40) 'd' (line 12) <== Memory access at offset 40 overflows this variable
    [64, 72) 'before' (line 13)
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-buffer-overflow ../../../../src/libsanitizer/asan/asan_interceptors.cpp:563 in strcpy
```

**왜 그런가**

- ★★★ **널 없음 다섯** — `strncpy(…, sizeof d)` 의 같음·김(딱 8 칸을 쓰고 널 자리가 없다) · `memcpy` 세 길이(널을 복사하지 않았다).
- ★★★ **넘침 넷** — `strcpy` 의 같음·김(크기를 안 받는다 · 같음도 널 한 칸이 모자란다) · `strncat(…, sizeof d)` 의 같음·김(8 글자 + 널 = 9).
- ★★ **`snprintf` · `strlcpy` 는 세 길이 다 널이 있고 반환이 원본 길이** · `strncat(…, sizeof d - 1)` 은 빈 `d` 라서 맞았다.

### 2. 컴파일러가 잡은 것 — **`strncat(d, s, sizeof d)` 한 줄뿐 · gcc 는 「bound 가 목적지 크기와 같다」 · clang 은 `sizeof(d) - strlen(d) - 1` 을 권한다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -c s49a.c -o /dev/null (cc exit=0) =====
s49a.c: In function ‘main’:
s49a.c:23:13: warning: ‘strncat’ specified bound 8 equals destination size [-Wstringop-overflow=]
   23 |     case 3: strncat(d, s, sizeof d); break;
      |             ^~~~~~~~~~~~~~~~~~~~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 -c s49a.c -o /dev/null (cc exit=0) =====
s49a.c:23:27: warning: the value of the size argument in 'strncat' is too large, might lead to a buffer overflow [-Wstrncat-size]
   23 |     case 3: strncat(d, s, sizeof d); break;
      |                           ^~~~~~~~
s49a.c:23:27: note: change the argument to be the free space in the destination buffer minus the terminating null byte
   23 |     case 3: strncat(d, s, sizeof d); break;
      |                           ^~~~~~~~
      |                           sizeof(d) - strlen(d) - 1
1 warning generated.
```

**왜 그런가**

- ★★ **`strcpy` 넘침 · `strncpy` 의 널 없음은 경고 0** — 원본 길이는 **실행 인자로 고른 것**이라 컴파일러가 모른다. `strncat` 줄은 **`n` 의 모양 자체**가 틀려서 잡혔다.

### 3. `strcat` 되풀이 — **130 · 10300 · 1003000 · 16012000 대 40 · 400 · 4000 · 16000 — 앞은 약 100 배씩, 뒤는 10 배씩** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s49c.c -o x ; ./x (cc exit=0 · run exit=0) =====
n =   10 · 길이    20 · strcat 반복       130 바이트 읽음 · 끝을 기억     40 바이트 읽음
n =  100 · 길이   200 · strcat 반복     10300 바이트 읽음 · 끝을 기억    400 바이트 읽음
n = 1000 · 길이  2000 · strcat 반복   1003000 바이트 읽음 · 끝을 기억   4000 바이트 읽음
n = 4000 · 길이  8000 · strcat 반복  16012000 바이트 읽음 · 끝을 기억  16000 바이트 읽음
```

**왜 그런가**

- ★★ **`strcat` 은 매번 `d` 의 끝을 처음부터 찾는다** — i 번째 호출이 약 `2i` 바이트를 걷는다. 합이 길이의 제곱으로 자란다.
- ★★ **끝 포인터를 들고 다니면 조각만 읽는다** — 길이에 비례한다.
- ★ **시간은 재지 않았다** — 계수기가 센 **바이트**다.

### 4. `sizeof` 포인터 — **두 컴파일러 `-Wsizeof-pointer-memaccess` · `sizeof name = 32 · strlen(name) = 7`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s49z.c -o /dev/null (cc exit=0) =====
s49z.c: In function ‘fill’:
s49z.c:5:26: warning: argument to ‘sizeof’ in ‘strncpy’ call is the same expression as the destination; did you mean to provide an explicit length? [-Wsizeof-pointer-memaccess]
    5 |     strncpy(d, s, sizeof d);            /* 배열 크기를 쓰려던 자리 */
      |                          ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s49z.c -o /dev/null (cc exit=0) =====
s49z.c:5:26: warning: 'strncpy' call operates on objects of type 'char' while the size is based on a different type 'char *' [-Wsizeof-pointer-memaccess]
    5 |     strncpy(d, s, sizeof d);            /* 배열 크기를 쓰려던 자리 */
      |             ~            ^
s49z.c:5:26: note: did you mean to provide an explicit length?
    5 |     strncpy(d, s, sizeof d);            /* 배열 크기를 쓰려던 자리 */
      |                          ^
1 warning generated.
```

```text
===== gcc -std=c17 s49z.c -o x ; ./x (cc exit=0 · run exit=0) =====
sizeof name = 32 · strlen(name) = 7
```

**왜 그런가**

- ★★ **매개변수 `char *d` 의 `sizeof` 는 8** — `strncpy(d, s, 8)` 뒤 `d[7] = '\0'` 이라 7 글자로 **조용히 잘렸다.** 배열 감쇠는 [16번 형제](../16-array-pointer-decay-and-function-parameters/)가 정본이다.

### 5. `strlcpy` — **`-std=c17` 은 암시적 선언 경고(`exit=0`) · `_DEFAULT_SOURCE` 에서 `반환 6 · d = abc · 잘렸나 = 1` · `GLIBC_2.38`** ★★

**출력**

```text
===== gcc -std=c17 -c s49l.c -o /dev/null (cc exit=0) =====
s49l.c: In function ‘main’:
s49l.c:6:16: warning: implicit declaration of function ‘strlcpy’; did you mean ‘strncpy’? [-Wimplicit-function-declaration]
    6 |     size_t r = strlcpy(d, "abcdef", sizeof d);
      |                ^~~~~~~
      |                strncpy
```

```text
===== gcc -std=c17 -D_DEFAULT_SOURCE -Wall s49l.c -o x ; ./x (cc exit=0 · run exit=0) =====
반환 6 · d = abc · 잘렸나 = 1
```

```text
===== nm -D /lib/x86_64-linux-gnu/libc.so.6 | grep -E ' strlcpy| strlcat' (exit=0) =====
00000000000b4cd0 W strlcat@@GLIBC_2.38
00000000000b4d50 W strlcpy@@GLIBC_2.38
```

**왜 그런가**

- ★★ **ISO C 의 함수가 아니다** — 엄격한 판에서 glibc 헤더가 선언을 안 연다. **`_DEFAULT_SOURCE`** 가 연다. 심볼 판 **`GLIBC_2.38`** 이 「2.38 부터」의 근거다.

### 6. `strncpy` 의 계약 — **짧으면 n 까지 널로 채운다 · 길면 n 글자만 · 「널을 붙인다」는 문장은 없다** ★★★

- ★★★ N3220 — 「**n 글자를 넘지 않게 복사한다**」·「**원본이 n 보다 짧은 문자열이면 모두 n 글자가 될 때까지 널을 덧붙인다**」. **원본이 n 이상일 때 널을 붙인다는 문장이 없다** — 그래서 같음·김에서 널이 없다.
- ★★ **짧은 원본에 8 바이트를 쓴 것은 뒤 문장** — 「**n 글자가 될 때까지**」 채운다. `strncpy` 는 **고정 폭 필드를 만드는 함수**다([20번 형제](../20-null-terminated-strings-and-string-literals/) (7)).

### 7. 잘림을 아는 함수 — **`snprintf`·`strlcpy` 는 원본(썼을) 길이 · `>= 크기` 면 잘림 · `strncat(…, sizeof d - 1)` 은 `d` 가 빌 때만 맞다** ★★

- ★★ **`snprintf` 는 「n 이 충분했다면 썼을 글자 수」** — 표준: 「**반환이 음수가 아니고 n 보다 작을 때, 그리고 그때만 완전히 쓰였다**」. 격자의 **8 · 12** 가 잘린 칸이다. `strlcpy` 도 같은 판정(glibc).
- ★ **`strncat` 의 n 은 「붙일 글자 수」** — `d` 에 이미 글자가 있으면 `sizeof d - 1` 은 **그만큼 넘친다.** 일반형은 `sizeof d - strlen(d) - 1`.

### 8. 두 컴파일러의 보통 빌드 — **gcc `-O2` 는 `_FORTIFY_SOURCE=3` 으로 `__*_chk` · `exit 134` · clang 은 그 매크로가 없다 · 표준의 차이가 아니다 · `exit 0` 은 「검사 안 함」** ★★★

**출력**

```text
===== gcc -O2 -dM -E - < /dev/null | grep FORTIFY; clang -O2 -dM -E - < /dev/null | grep FORTIFY; echo "clang grep exit=$?" (exit=0) =====
#define _FORTIFY_SOURCE 3
clang grep exit=1
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 s49a.c -o x ; ./x 1 1 2>&1 >/dev/null (cc exit=0 · run exit=134) =====
*** buffer overflow detected ***: terminated
```

**왜 그런가**

- ★★★ **Ubuntu 의 gcc 는 `-O2` 에서 `_FORTIFY_SOURCE=3` 을 미리 정의한다** — glibc 헤더가 크기를 아는 호출을 **검사하는 판**으로 바꾸고, 넘치면 `*** buffer overflow detected ***` 로 `abort` 한다. clang 은 이 판에서 그 매크로를 **정의하지 않았다.**
- ★★ **표준은 둘 다 「미정의」라고만** 한다 — 멈추는 것도 안 멈추는 것도 허용된다. **차이는 배포판이 드라이버에 심은 기본값**이다.
- ★★★ **clang 칸의 `exit 0` 은 「넘치지 않았다」가 아니다** — ASan 이 같은 칸을 넘침으로 잡았다. **아무도 묻지 않은 것**이다. 그 칸의 결과 바이트는 싣지 않았다.

### 9. `memcpy` — **문자열 함수가 아니라 널을 모른다 · 결함이 아니라 계약** ★★

- ★★ **`memcpy(d, s, n)` 은 n 바이트를 옮길 뿐** — `n = min(strlen(s), sizeof d)` 에는 **널이 포함되지 않으니** 세 길이 다 널이 없다. 문자열로 쓰려면 **`n` 에 널을 넣거나 직접 `d[n] = 0`** (자리가 있을 때). 겹침·`memmove` 는 [목록의 **50번 주제**](../50-string-h-memory-functions-memcpy-memmove-memset-memcmp/).

### 10. 길이를 가진 문자열 — **널을 찾는 걸음 · 널 없음 사고가 원리상 없다 · 잘림 판정과 UTF-8 경계는 남는다** ★★

- ★★ [Rust 15](../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/)의 `&str`·슬라이스는 **(포인터, 길이)** 다 — **끝을 찾으려 걷지 않고**(3번의 제곱이 없다), **널이 없어서 생기는 사고**(1번의 다섯 칸)가 **원리상 없다.** 범위 밖 접근은 **패닉**으로 멈춘다(넘친 넷).
- ★ **없애지 못하는 것** — **고정 크기 버퍼에 넣을 때 잘라야 하나**의 판단, 그리고 **바이트 경계가 문자 경계가 아닌 자리**(UTF-8 — Rust 는 그 자리에서 패닉한다).

### 11. 다섯 층과 경계 — **표준은 각 함수의 짧을 때·길 때 · glibc 는 `strlcpy`·fortify · 배포판은 `_FORTIFY_SOURCE` 기본값** ★★

| 층 | 이 주제에서 |
|---|---|
| ★★★ **표준** | ★★★ `strncpy` 채움·무널 · `strncat` n + 널 · `snprintf` 반환 · `strcpy` 크기 모름 |
| ★★ **glibc · POSIX** | ★★ `strlcpy`(2.38) · 기능 매크로 · `__*_chk` |
| ★★ **컴파일러 구현(배포판)** | ★★★ Ubuntu gcc 의 `_FORTIFY_SOURCE=3` · 경고 두 종류 |
| ★★★ **UB** | ★★★ 배열 밖 쓰기 · 널 없는 배열의 문자열 사용 |

- ★ **문자열 탐색 알고리즘**은 [`algorithm/25-string-matching/`](../../../../cs/algorithm/25-string-matching/), **`memcpy`/`memmove` 의 겹침**은 [목록의 **50번 주제**](../50-string-h-memory-functions-memcpy-memmove-memset-memcmp/)가 정본이다.

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s49a.c` | ★★★ **경계 격자 63칸 · 5 / 21 · 4 / 21 · 4 / 4 · 0 / 4** · 경고 둘 · ASan 1 · fortify 1 · 매크로 판별 | 63 · 2 · 1 · 1 · 1 |
| `s49c.c` | ★★ 읽은 바이트 계수 4 줄 | 1 |
| `s49z.c` | ★★ `sizeof` 포인터 · 경고 둘 | 3 |
| `s49l.c` | ★★ `strlcpy` 두 판 · 심볼 판 | 3 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. **흔들린 칸은 ASan 리포트의 PID · 주소뿐**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **1번 · 8번의 보통 빌드 열** — Ubuntu gcc 의 `_FORTIFY_SOURCE=3` · clang 18 의 기본값.
- ★★ **5번** — glibc 2.38+ 의 `strlcpy`.

**`strncpy` · `strncat` · `snprintf` 의 짧을 때 · 길 때 동작은 구현 의존이 아니다.**\
어느 C 구현에서도 같다.

**안 돌려 본 것 / 못 잰 것**

- **재지 않은 것** — **`strcat` 되풀이의 시간**(계수기만 셌다) · glibc 실제 `strcat` 의 읽기 폭.
- **안 돌려 본 것** — `memccpy` · 포인터로 받은 버퍼의 fortify · `strdup`.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **8번** — 배포판이 fortify 기본값을 바꾸거나 clang 이 따라오면.

## 실행 환경

이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **clang 18.1.3** · **glibc 2.39** ·
x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
소스는 `s49a.c` · `s49c.c` · `s49l.c` · `s49z.c` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
★★★ **본체 창은 경계 조건 격자** — 함수 7 × 원본 길이 3 × 빌드 3.
★★ **흔들리는 칸** — ASan 리포트의 PID · 주소(정규화 기본 규칙). 나머지는 정규화 없이 같다.
