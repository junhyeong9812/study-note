# c/syntax/37 — `malloc`/`calloc`/`realloc`/`free`: 「**실패는 `NULL` 하나로 온다 — 그 `NULL` 을 받는 자리가 원본을 지키느냐를 가른다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) — 메모리 관리 함수 공통 절의 「**공간을 못 잡으면 널 포인터를 돌려준다**」·「**요청 크기가 0 이면 구현 정의 — 널이거나, 0 이 아닌 크기처럼 굴되 그 포인터로 객체에 접근하면 안 된다**」·「**기본 정렬 요구를 가진 어떤 객체에도 맞게 정렬된 포인터**」, `calloc` 의 「**`nmemb * size` 가 `size_t` 를 한 바퀴 돌면 널 포인터**」·「**모든 비트 0**」, `free` 의 「**`ptr` 이 널이면 아무 일도 없다 · 이미 해제된 공간이면 UB**」, `realloc` 의 「**새 객체를 못 잡으면 옛 객체는 해제되지 않고 값도 그대로**」·「**크기가 0 이면 UB**」, 부록의 바뀐 점 목록 「**zero-sized reallocations with realloc are undefined behavior**」를 **본문에서 직접 찾아 읽었다**) · `man 3 malloc`(glibc 판 — 이 머신에 깔린 것)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **반환값 · `errno` · sanitizer 리포트 · 어셈블리는 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★★★ **본체는 실패 격자다** — 탐침 7 × 빌드 8(두 컴파일러 × `-O0`/`-O2` · 두 ASan × `allocator_may_return_null` 두 값), 칸마다 **반환이 널인가 · `errno`**.\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> **버전** — 네 함수는 **C89 부터** 있다. ★ **C23** 이 `realloc(p, 0)` 을 **UB** 로 옮겼다(C17 까지는 메모리 관리 함수 공통의 「크기 0 은 구현 정의」 아래에 있었다 — ★ C17 본문은 이 문서가 직접 열지 않았고, N3220 부록의 바뀐 점 목록으로 확인했다).
> ★★★ **경계** — **할당자의 내부(빈 목록 · 분할 · 병합 · 단편화)** 는 [`data-structure/35-allocator/`](../../../../../data-structure/35-allocator/)가 정본이다(그쪽 서머리의 「구현 — FreeListAllocator」 절에 「할당(분할)」·「해제(병합 coalescing)」·「단편화」 소절이 있다). 여기는 **API 계약 · 실패 처리 · `realloc` 호출 형태**만 본다.\
> ★ **할당 저장 기간이라는 선택**은 [28번 형제](../28-choosing-among-four-storage-durations/), **`malloc` 은 불확정 · `calloc` 은 0** 의 실측은 [30번 형제](../30-initialization-rules-and-indeterminate-values/)가 정본이다(이 편은 그 결과를 **다시 재지 않고** 인용한다). **해제 후 사용 · 댕글링의 코드 패턴**은 목록의 **57번 주제**, **sanitizer 사용법**은 목록의 **58번 주제**다.
> 선행 — [28번 형제](../28-choosing-among-four-storage-durations/).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 둘째 창 — 실행 결과의 실패 격자다.** 크기 0 · 크기 `SIZE_MAX` · 곱셈 넘침을 네 함수에 넣고, **보통 빌드와 ASan 빌드**에서 「널인가 · `errno`」를 한 칸에 찍는다.
★★★ 그 격자에서 **갈린 칸 6 / 49** 는 전부 **「거대한 크기」 두 줄**에 몰렸다 — 그리고 그 여섯 칸이 **셋 다 다른 이유**로 갈렸다(clang `-O2` 의 `errno` · ASan 의 기본 동작 · 없음).

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | `-Walloc-size-larger-than` · `-Walloc-zero` · `-Wuse-after-free` · 정적 분석기 둘 | 씀 |
| ★★★ ② **실행 출력(실패 격자)** | ★ **본체** — 반환 널 여부 · `errno` · 죽었나 | 씀 |
| ③ sanitizer | ★★★ **LeakSanitizer 가 `p = realloc(p, n)` 누수를 잡나** · double free · use-after-free 리포트 전문 · ★ MSan(`malloc` 대 `calloc`) | 씀 |
| ④ `-O2` 어셈블리 | ★★ clang 이 **`malloc(SIZE_MAX)` 호출 자체를 지운 것** — `call` 목록 | 씀 |
| 시간 측정 | — | 부적용(성능 주제가 아니다 — ★ **「`calloc` 이 `malloc`+`memset` 보다 빠르다」는 재지 않았다**) |
| ★ 제5의 상태 | 「실패한 `realloc` 뒤에 원본이 새나」를 **값으로는 물을 수 없다**(잃은 포인터는 찍을 수도 없다) — **LSan 의 도달 불가 판정**으로 바꿔 물었다. ★ 그런데 **ASan 의 기본값은 실패를 일으키기 전에 프로그램을 죽인다** — 그 창을 열려면 `allocator_may_return_null=1` 이 필요했다 | 창을 바꿔 답함 |

★ **바꾼 창(LSan)이 못 보는 것** — LSan 은 **종료 시점에 도달할 수 없는 블록**을 센다. 스택이나 레지스터에 **옛 값이 남아 있으면 「도달 가능」으로 본다**(38편의 격자에서 clang 판이 실제로 그랬다). ★ 그리고 `setrlimit` 으로 실패를 일으키면 **LSan 자신이 메모리를 못 잡아 검사가 통째로 안 돈다**((5)).

## 이 판

```text
===== gcc --version | sed -n 1p (cc exit=0) =====
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

```text
===== clang --version | sed -n 1p (cc exit=0) =====
Ubuntu clang version 18.1.3 (1ubuntu1)
```

```text
===== ldd --version | sed -n 1p (exit=0) =====
ldd (Ubuntu GLIBC 2.39-0ubuntu8.9) 2.39
```

```text
===== command -v valgrind (exit=1) =====
```

★ **`valgrind` 는 이 머신에 없다**(`command -v` 가 `exit=1`). 설치하면 `--leak-check=full` 로 (4)의 누수를 **다른 창에서** 한 번 더 물을 수 있다 — ★ 이 문서는 **설치하지 않았다.**

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | ASan·LSan 리포트의 **PID**(`==N==`) · **주소**(`0x…`) | 실행마다 다르다 — `normalize-shaky.py` 의 기본 규칙 둘이 지운다 |
| **흔들린다(선언)** | ★★ **`realloc` 이 주소를 바꾸는가** | 할당자의 상태에 달린 관찰이다 — (7)은 **20 판을 돌려 서로 다른 줄의 가짓수**로 찍었다(그 가짓수는 이 판에서 1 이었지만 **보장이 아니다**) |
| 안 흔들린다 | ★★★ **실패 격자 전부** · 누수 격자 · 정적 도구 격자 | 같은 판 · 같은 플래그면 같다 |
| 안 흔들린다 | 리포트의 **`파일:줄`** · `SUMMARY` 줄 · `BuildId` · `Direct leak of 16 byte(s)` | `-ffile-prefix-map` 과 `strip_path_prefix` 로 경로를 죽였다 |

★★ **정규화 규칙은 기본 넷뿐**이다 — 위 표의 첫 줄과 같은 목록이다.

## 한눈에 — 쉽게 말하면

**할당은 「창고 대여 창구」다.**

- **빌려 달라고 하면 열쇠를 주거나, 「없다」는 빈손을 준다** — 빈손이 `NULL` 이다. 이유는 **창구마다** 적어 주기도(`errno`) 하고 안 적어 주기도 한다. → **실패는 `NULL` 하나**
- **「0 칸 주세요」에 무엇을 줄지는 창구가 정한다** — 이 창구(glibc)는 **열쇠를 준다.** → **크기 0 은 구현 정의**
- **「칸 수 × 칸 크기」를 손으로 곱해 내밀면 창구는 적힌 숫자만 본다** — 곱셈이 넘쳐 **작은 숫자**가 되면 **작은 창고를 준다.** `calloc` 은 **곱하기 전 두 숫자를 받아서** 넘침을 본다. → **곱셈 넘침**
- **「더 큰 칸으로 바꿔 주세요」가 거절되면 원래 칸은 그대로 내 것이다** — 그런데 **원래 칸의 열쇠를 버리고 새 열쇠 자리에 빈손을 받으면**, 칸은 남았는데 **열 방법이 없다.** → **`p = realloc(p, n)`**
- **반납은 두 번 할 수 없다** — 두 번째 반납은 **남의 칸을 건드리는 일**이 된다. 빈손(`NULL`) 반납은 **아무 일도 아니다.** → **double free · `free(NULL)`**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 빈손 | `NULL` 반환 | ★★★ 격자의 `NULL/…` 칸 |
| 이유 적어 주기 | `errno = ENOMEM` | ★★ **POSIX 의 요구 · C 표준은 요구하지 않는다** — clang `-O2` 는 **`0` 으로 읽었다** |
| 0 칸 | `malloc(0)` · `calloc(0, 8)` | ★ 이 판은 `ptr` |
| 손으로 곱한 숫자 | `malloc(n * 2)` | ★★★ **`n*2=2` 로 성공** |
| 열쇠를 버리고 빈손 받기 | `p = realloc(p, n)` | ★★★ **LSan `Direct leak of 16 byte(s)`** |
| 두 번 반납 | `free(p); free(p);` | ★★ glibc 가 `abort` · ASan `double-free` |

```text
   p = realloc(p, big);                     tmp = realloc(p, big);
   -------------------------------------    -------------------------------------
   성공 -> p 가 새 블록                      성공 -> p = tmp;
   실패 -> p = NULL                         실패 -> tmp == NULL, p 는 그대로
           옛 블록은 해제되지 않았다(표준)            옛 블록을 쓰거나 free(p) 로 놓는다
           그 주소를 아는 변수가 없다  ★ 누수
```

- ★★★ **이 주제의 본체는 「표준」 칸과 「구현 정의」 칸의 경계**다 — 「실패하면 `NULL`」·「실패한 `realloc` 은 원본을 안 건드린다」·「`calloc` 은 곱셈 넘침을 본다」·「`free(NULL)` 은 아무 일도 없다」가 **표준**이고, **크기 0 · `errno`** 가 **구현(과 POSIX)** 이다.
- ★★ **「UB」 칸** — double free · 해제 후 사용 · C23 의 `realloc(p, 0)`.

> **`malloc(n)`** — `n` 바이트짜리 **할당 저장 기간** 객체를 잡는다. 내용은 **불확정**. 못 잡으면 `NULL`.\
> 예: `char *p = malloc(16);`.

> **`realloc(p, n)`** — 옛 객체를 **해제하고** 크기 `n` 의 새 객체를 돌려준다(내용은 앞쪽 `min(옛, 새)` 바이트까지 복사). **못 잡으면 옛 객체를 해제하지 않는다.**\
> 예: `char *tmp = realloc(p, 64);`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **네 함수는 언제 `NULL` 을 돌려주고, 그때 무엇을 보장하나** — 크기 0 · 거대한 크기 · 곱셈 넘침 · `errno`.
2. ★★★ **`realloc` 실패에서 원본을 잃는 호출 형태와 안 잃는 형태는 무엇이고, 도구는 그 차이를 보나.**
3. ★★ **해제 쪽의 규칙** — `free(NULL)` · double free · 해제 후 사용 · C23 의 `realloc(p, 0)`.

## 동작 방식

### (1) ★★★ 실패 격자 — 탐침 일곱 × 빌드 여덟

**언제 쓰나** — 「이 호출이 실패할 수 있나, 실패하면 무엇이 오나」를 **호출마다** 확인할 때. ★★★ **이 편의 본체**다.

```c
/* s37a.c */
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/* volatile — 컴파일러가 크기를 미리 알고 호출을 접지 못하게 한다 */
static volatile size_t zero = 0, eight = 8, huge = SIZE_MAX, big = SIZE_MAX / 2 + 2, two = 2;

static void show(const char *what, void *q) {
    int e = errno;
    printf("%s\t%s\t%s\n", what, q == NULL ? "NULL" : "ptr",
           e == 0 ? "0" : e == ENOMEM ? "ENOMEM" : "other");
}

int main(int argc, char **argv) {
    int k = argc > 1 ? atoi(argv[1]) : 0;
    char label[64];
    void *p, *q = NULL;
    errno = 0;
    switch (k) {
    case 1: q = malloc(zero);          show("malloc(0)", q); break;
    case 2: q = calloc(zero, eight);   show("calloc(0, 8)", q); break;
    case 3: q = realloc(NULL, eight);  show("realloc(NULL, 8)", q); break;
    case 4: p = malloc(eight);
            if (!p) return 1;
            q = realloc(p, zero);      show("realloc(p, 0)", q); break;
    case 5: q = malloc(huge);          show("malloc(SIZE_MAX)", q); break;
    case 6: q = calloc(big, two);      show("calloc(n, 2)", q); break;
    case 7: snprintf(label, sizeof label, "malloc(n * 2) [n*2=%zu]", big * two);
            q = malloc(big * two);     show(label, q); break;
    }
    free(q);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s37a.c -o /dev/null (cc exit=0) =====
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s37a.c -o /dev/null (cc exit=0) =====
```

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

그림 해설 (한 단계씩):

- ★★★ **다섯 줄은 여덟 칸이 전부 같다** — `malloc(0)`·`calloc(0, 8)`·`realloc(NULL, 8)` 은 **`ptr/0`**, `realloc(p, 0)` 은 **`NULL/0`**, 곱셈이 넘친 `malloc(n * 2)` 는 **`ptr/0`**.
- ★★★ **갈린 칸 6 / 49 는 전부 거대한 크기 두 줄**(`malloc(SIZE_MAX)` · `calloc(n, 2)`)에 있다. 이유가 **셋**이다.
  - **clang `-O2` 의 두 칸** — 반환은 `NULL` 인데 **`errno` 가 `0`** 으로 읽혔다. `gcc -O2` 는 `ENOMEM` 이다. ★ **원인은 이 문서가 확정하지 않았다** — 「clang 이 `malloc` 은 `errno` 를 안 바꾼다고 보고 앞서 쓴 `errno = 0` 을 그대로 썼다」는 **내 추론**이다(어셈블리로 확인하지 않았다).
  - **ASan 기본값의 네 칸** — **`죽음(exit 1)`**. ASan 은 **지원 한도(이 판 `0x10000000000`)를 넘는 요청을 실패로 돌려주지 않고 프로그램을 멈춘다**(아래 리포트).
  - **`allocator_may_return_null=1` 의 네 칸** — 보통 빌드와 **같다**(`NULL/ENOMEM`). 갈리지 않는다.
- ★★★ **`calloc(n, 2)` 는 `NULL`, `malloc(n * 2)` 는 `ptr`** — 같은 곱이다. `calloc` 은 **두 수를 따로 받아** 곱이 넘치는지 본다(표준의 약속). `malloc` 에는 **이미 넘쳐 `2` 가 된 수**가 도착한다 — **2 바이트짜리 성공**이다. 그 뒤에 `n * 2` 바이트를 쓰면 **배열 밖 쓰기**가 된다(목록의 **56번 주제**).
- ★★ **`realloc(p, 0)` 은 `NULL` 이고 `errno` 는 `0`** — glibc 는 「옛 블록을 해제하고 `NULL` 을 돌려준다 · **오류가 아니다**」라고 적는다(아래 `man`). ★ **C23 에서 이 호출은 UB** 다((8)).

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

- ★★ **ASan 의 기본 동작은 「실패를 돌려준다」가 아니라 「멈춘다」** — `allocation-size-too-big`. 힌트 줄이 스스로 **`allocator_may_return_null=1`** 을 알려 준다. ★★★ **실패 경로를 시험하려고 ASan 을 켜면, 기본값에서는 실패 경로에 아예 못 간다** — (4)에서 이것이 결정적이다.

```text
===== MANWIDTH=80 man 3 malloc | sed -n '/^RETURN VALUE/,/^ERRORS/p' | grep -v '^ERRORS' (exit=0) =====
RETURN VALUE
       The  malloc(), calloc(), realloc(), and reallocarray() functions return
       a pointer to the allocated memory, which is suitably  aligned  for  any
       type  that fits into the requested size or less.  On error, these func‐
       tions return NULL and set errno.   Attempting  to  allocate  more  than
       PTRDIFF_MAX bytes is considered an error, as an object that large could
       cause later pointer subtraction to overflow.

       The free() function returns no value, and preserves errno.

       The  realloc()  and  reallocarray() functions return NULL if ptr is not
       NULL and the requested size is zero; this is not considered  an  error.
       (See  "Nonportable  behavior"  for portability issues.)  Otherwise, the
       returned pointer may be the same as ptr if the allocation was not moved
       (e.g., there was room to expand the allocation in-place), or  different
       from  ptr if the allocation was moved to a new address.  If these func‐
       tions fail, the original block is left untouched; it is  not  freed  or
       moved.

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

- ★★ **이 판의 문서가 층을 가른다** — 「실패하면 `NULL` 을 돌려주고 **`errno` 를 설정한다**」는 **glibc 의 약속**이고, 「**POSIX 는 `errno` 설정을 요구하지만 C 표준은 요구하지 않는다**」·「**크기 0 의 동작은 glibc 고유**」라고 스스로 적는다.
- ★ glibc 는 **`PTRDIFF_MAX` 를 넘는 요청을 오류로 본다** — 격자의 `SIZE_MAX` 와 `SIZE_MAX/2+2` 가 둘 다 그 선을 넘는다.

### (2) ★★ 크기가 상수면 — clang 이 호출을 지운다

**언제 쓰나** — 「`malloc(SIZE_MAX)` 는 당연히 실패하겠지」를 **테스트 코드**로 확인하려 할 때.

```c
/* s37b.c */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    void *q = malloc(SIZE_MAX);          /* 크기가 상수 · 받은 메모리는 쓰지 않는다 */
    printf("malloc(SIZE_MAX)   -> %s\n", q == NULL ? "NULL" : "ptr");
    free(q);
    void *r = malloc(SIZE_MAX / 2);
    printf("malloc(SIZE_MAX/2) -> %s\n", r == NULL ? "NULL" : "ptr");
    free(r);
    return 0;
}
```

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

그림 해설 (한 단계씩):

- ★★★ **clang `-O1`·`-O2` 는 두 줄 다 `ptr`** — `SIZE_MAX` 바이트 할당이 **「성공했다」** 고 답한다. `call` 목록이 이유를 보인다 — **clang `-O2` 의 `main` 에는 `malloc` 도 `free` 도 없다.** 받은 메모리를 **쓰지 않으니** 할당 자체를 지우고, 결과를 널이 아닌 것으로 뒀다.
- ★★ **gcc 는 세 수준 다 `NULL`** 이고 `-Walloc-size-larger-than` 경고를 낸다(clang 은 경고 0).
- ★★ **(1)이 크기를 `volatile` 로 둔 이유가 이것**이다 — 컴파일러가 크기를 알면 **실패 경로를 시험하는 코드가 시험을 지운다.**
- ★ 이것은 **컴파일러 구현 층의 관찰**이다 — 「할당을 지워도 되느냐」를 이 문서는 **판정하지 않는다.** 결론은 「**이 판의 clang 에서 상수 크기 실패 시험은 시험이 아니다**」까지다.

### (3) ★★★ `p = realloc(p, n)` — 실패하면 원본의 주소가 사라진다

**언제 쓰나** — 버퍼를 늘릴 때. ★★★ **이 편이 이름을 걸고 묻는 호출 형태**다.

```c
/* s37c.c */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static volatile size_t grow = SIZE_MAX / 2;   /* 이 판에서 할당이 실패하는 크기 */

int main(void) {
    char *p = malloc(16);
    if (!p) return 1;
    strcpy(p, "fifteen chars..");
    p = realloc(p, grow);                     /* ★ 결과를 같은 변수에 바로 받는다 */
    fprintf(stderr, "[c] p == NULL : %d\n", p == NULL);
    free(p);
    return 0;
}
```

```c
/* s37d.c */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static volatile size_t grow = SIZE_MAX / 2;

int main(void) {
    char *p = malloc(16);
    if (!p) return 1;
    strcpy(p, "fifteen chars..");
    char *tmp = realloc(p, grow);             /* ★ 결과를 다른 변수에 받는다 */
    if (tmp == NULL) {
        fprintf(stderr, "[d] tmp == NULL · p 의 내용 : %s\n", p);
        free(p);
        return 1;
    }
    p = tmp;
    free(p);
    return 0;
}
```

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

그림 해설 (한 단계씩):

- ★★★ **보통 빌드에서는 두 형태 다 조용하다** — `s37c` 는 **`exit=0`** 에 `p == NULL : 1` 한 줄. 누수를 말해 주는 것이 **아무것도 없다.** `s37d` 는 옛 내용(`fifteen chars..`)을 **그대로 읽고** 스스로 `free` 한 뒤 `exit=1`.
- ★★★ **ASan 기본값에서는 두 형태 다 `allocation-size-too-big` 로 죽는다** — 실패 경로에 **도달조차 못 한다.** 이 칸만 보면 「두 형태가 같다」로 읽힌다.
- ★★★ **`allocator_may_return_null=1` 을 주자 갈렸다** — `s37c` 만 **`Direct leak of 16 byte`**. `s37d` 는 리포트 없음. **누수 보고가 나온 칸 2 / 12** — 그 둘이 정확히 「`s37c` × 두 컴파일러 × ASan+null」이다.

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

- ★★★ **리포트가 `main s37c.c:9` 를 가리킨다** — `realloc` 한 줄(12)이 아니라 **`malloc(16)` 한 줄**이다. LSan 은 「**어디서 잡은 블록이 주인을 잃었나**」를 말한다. 16 바이트가 곧 **처음 `malloc` 의 크기**다.
- ★★ **표준이 그 16 바이트를 살려 둔다** — 「새 객체를 못 잡으면 옛 객체는 해제되지 않고 값도 그대로」. 그래서 **누수**다(해제됐다면 누수가 아니다). `s37d` 가 옛 내용을 읽을 수 있었던 것이 같은 약속의 다른 면이다.

```text
   s37c.c                               s37d.c
   p = malloc(16) ──▶ [16 B "fifteen…"]   p = malloc(16) ──▶ [16 B "fifteen…"]
   p = realloc(p, big)                     tmp = realloc(p, big)
     실패 -> p = NULL                         실패 -> tmp = NULL
   [16 B] 은 살아 있다 · 가리키는 변수 0       [16 B] 은 살아 있다 · p 가 가리킨다
   ★ LSan: Direct leak of 16 byte(s)          free(p) -> 리포트 없음
```

### (4) ★★ 정적 도구는 이 누수를 보나

**언제 쓰나** — 「실행 안 하고 잡을 수 없나」.

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

- ★★★ **`p = realloc(p, n)` 누수(`s37c`)를 잡은 정적 도구는 `clang --analyze` 하나**다 — `Potential leak of memory pointed to by 'p'`. gcc 의 `-fanalyzer` 는 **두 판 다 0건**이다.
- ★★ **`s37d` 는 다섯 도구 전부 0건** — 옳은 침묵이다.
- ★★ **double free(`s37f`) · 해제 후 사용(`s37g`)은 넷이 잡는다** — ★ gcc 는 **분석기 없이 `-Wall` 만으로도** `-Wuse-after-free` 를 낸다(★ 이 문서는 gcc-12·13 두 판만 봤다 — 더 옛 판의 유무는 확인하지 않았다). **clang `-Wall` 만 네 줄 다 0.**
- ★ **경고가 나온 칸 9 / 20** — 도구마다 **다른 자리**에서 침묵한다.

### (5) ★ `setrlimit` 로 실패를 일으키면 — 검사기가 먼저 죽는다

**언제 쓰나** — 「거대한 크기 대신 **진짜 메모리 부족**으로 실패시키자」.

```c
/* s37e.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>

int main(void) {
    char *p = malloc(16);
    if (!p) return 1;
    strcpy(p, "fifteen chars..");
    struct rlimit r = { (rlim_t)1 << 30, RLIM_INFINITY };   /* 주소 공간 1 GiB */
    fprintf(stderr, "[e] setrlimit = %d\n", setrlimit(RLIMIT_AS, &r));
    p = realloc(p, (size_t)2 << 30);                        /* 2 GiB 로 늘리기 */
    fprintf(stderr, "[e] p == NULL : %d\n", p == NULL);
    free(p);
    return 0;
}
```

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

- ★★ **보통 빌드에서는 된다** — 주소 공간을 1 GiB 로 묶고 2 GiB 로 늘리니 `p == NULL : 1`, `exit=0`. **누수는 역시 아무도 말하지 않는다.**
- ★★★ **ASan 판에서는 `realloc` 은 `NULL` 을 돌려줬는데, 종료 시 누수 검사가 `out of memory` 로 죽었다** — `ScopedStackWithGuard` 를 잡으려던 **검사기 자신의** `mmap` 이 한도에 걸렸다. **누수 리포트가 안 나온 것은 「누수가 없다」가 아니다** — 검사가 안 돌았다(`exit=1` 과 `ERROR: Failed to mmap` 이 근거다).
- ★ 그래서 (3)은 **크기로 실패를 일으켰다** — 한도를 건드리지 않으니 검사기가 산다.

### (6) ★★ `free(NULL)` · double free · 해제 후 사용

**언제 쓰나** — 정리 경로에서 `free` 를 여러 번 부를 수 있을 때([13번 형제](../13-goto-cleanup-idiom/)가 이 보장에 기댄다).

```c
/* s37f.c */
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    free(NULL);
    printf("[f] free(NULL) 다음 줄\n");
    char *p = malloc(8);
    if (!p) return 1;
    free(p);
    printf("[f] 첫 free(p) 다음 줄\n");
    free(p);
    printf("[f] 둘째 free(p) 다음 줄\n");
    return 0;
}
```

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

그림 해설 (한 단계씩):

- ★★★ **`free(NULL)` 은 아무 일도 없다** — 그 뒤 줄이 찍혔다. **표준의 약속**이다(「`ptr` 이 널이면 아무 일도 없다」).
- ★★★ **둘째 `free(p)` 에서 보통 빌드는 `run exit=134`** — glibc 가 **`free(): double free detected in tcache 2`** 를 찍고 `abort` 했다. ★ **이것은 glibc 의 검사**다 — 표준은 UB 로만 두고, 이 검사도 **tcache 에 있는 블록**일 때의 것이다(★ 다른 크기·다른 순서에서 잡히는지는 던지지 않았다).
- ★★ **ASan 은 `attempting double-free`** 와 함께 **세 스택**(둘째 free · 첫 free · 처음 malloc)을 준다. 셋째 줄(`둘째 free(p) 다음 줄`)은 **두 판 다 안 찍힌다.**
- ★ **gcc 는 컴파일 때 이미 `-Wuse-after-free`** 를 냈다 — 경고 1 · **`cc exit=0`**.

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

- ★★★ **해제 후 읽기는 ASan 의 `heap-use-after-free` `READ of size 1`** — `s37g.c:12:13` 이 그 읽기다. ★ **보통 빌드의 실행 결과는 싣지 않았다** — UB 의 값은 결과가 아니다.

### (7) ★ `realloc` 이 주소를 바꾸는가 — 흔들리는 칸

**언제 쓰나** — 「`realloc` 뒤에도 옛 포인터를 써도 되나」.

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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s37h.c -o x ; ./x (cc exit=0 · run exit=0) =====
늘린 횟수 16 · 주소가 바뀐 횟수 3
```

```text
===== realloc 으로 16 번 늘리기 — 컴파일러 2 × 20 판 (-std=c17 -O0) (exit=0) =====
gcc    20 판 · 서로 다른 줄 1 가지
clang  20 판 · 서로 다른 줄 1 가지
```

- ★★ **이 판에서 16 번 늘리는 동안 주소가 바뀐 것은 3 번**이다 — 그리고 **20 판이 한 가지 줄**로 같았다.
- ★★★ **그래도 이것은 결론이 아니다** — 표준은 「새 객체는 **옛 포인터와 같은 값일 수도 있다**」까지만 말한다. 바뀔지 말지는 **할당자의 상태**다. **`realloc` 이 성공하면 옛 포인터는 쓰지 않는다** — 그것이 규칙이다.
- ★ 옛 주소는 **`realloc` 전에 정수로 적어 두고** 견줬다 — 해제된 포인터 값을 다시 쓰지 않으려고([30번 형제](../30-initialization-rules-and-indeterminate-values/)의 (6)과 같은 방식).

### (8) ★★ `realloc(p, 0)` — C23 의 UB, 그리고 도구는 판을 모른다

**언제 쓰나** — 「크기를 0 으로 줄이면 해제 대신 쓸 수 있다」는 코드를 볼 때.

```c
/* s37k.c */
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    char *p = malloc(16);
    if (!p) return 1;
    char *q = realloc(p, 0);              /* 크기 0 으로 realloc */
    printf("realloc(p, 0) -> %s\n", q == NULL ? "NULL" : "ptr");
    free(q);
    return 0;
}
```

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

- ★★★ **`-std=c17` 과 `-std=c2x` 가 갈린 줄 0 / 8** — C23 이 이 호출을 **UB 로 옮겼는데**, 세 컴파일러의 경고도 UBSan 도 **판을 가리지 않는다.**
- ★★ **`-Walloc-zero`(gcc) 는 판과 무관하게** `argument 2 value is zero` 를 낸다 — **기본 묶음(`-Wall -Wextra`)에는 들어 있지 않다.** clang 에는 해당 경고를 던지지 않았다.
- ★★ **이 판의 실행은 `NULL`** — glibc 는 옛 블록을 해제하고 `NULL` 을 돌려준다(오류 아님). ★ **다른 구현은 널이 아닌 포인터를 돌려줄 수 있다**(C17 까지 구현 정의였던 이유). 그래서 「`NULL` 이면 실패」로 읽는 코드가 **구현마다 다른 경로**를 탄다 — C23 이 이것을 UB 로 정리했다.

### (9) ★ 초기화와 정렬 — 형제가 이미 잰 것 + 한 칸

**언제 쓰나** — `malloc` 한 메모리를 읽기 전에 · `malloc` 결과를 아무 타입 포인터에 넣을 때.

- ★★ **`malloc` 은 불확정 · `calloc` 은 모든 비트 0** — [30번 형제](../30-initialization-rules-and-indeterminate-values/)의 (6)이 네 벌로 쟀다(`calloc` 64 / 64 · `malloc` 은 `-O0` 에서 **옛 흔적 48 / 48**, `-O2` 는 실험 자체가 지워짐). 같은 형제의 탐침 **P7(`malloc`)** 은 MSan 이 보고했다. **이 편은 그 값을 다시 재지 않았다.**
- ★ **이 편이 더한 칸은 `calloc` 쪽의 MSan** 이다 — 같은 분기를 두고 `malloc` 과 `calloc` 만 바꿨다. **값은 싣지 않고 리포트 수만** 싣는다.

```c
/* s37i.c */
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    (void)argv;
    int *p = argc > 1 ? calloc(4, sizeof *p) : malloc(4 * sizeof *p);
    if (!p) return 1;
    if (p[2] == 12345) puts("12345");    /* 그 값으로 분기한다 — MSan 은 여기서 본다 */
    free(p);
    return 0;
}
```

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

- ★★ **`malloc` 은 두 수준 다 리포트 1 · `calloc` 은 0** — MSan 이 「그 바이트가 **쓰인 적이 있나**」를 본다는 것이 칸으로 보인다. `calloc` 의 0 은 **쓰인 값**이다.

```c
/* s37j.c */
#include <stdalign.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int ok = 0, total = 0;
    for (size_t n = 1; n <= 64; n++) {
        void *p = malloc(n);
        if (!p) return 1;
        total++;
        ok += (uintptr_t)p % alignof(max_align_t) == 0;
        free(p);
    }
    printf("alignof(max_align_t) = %zu · 크기 1~64 중 그 배수 주소 %d / %d\n",
           (size_t)alignof(max_align_t), ok, total);
    return 0;
}
```

```text
===== malloc 이 돌려준 주소의 정렬 — 컴파일러 2 × 최적화 2 (exit=0) =====
gcc    -O0  | alignof(max_align_t) = 16 · 크기 1~64 중 그 배수 주소 64 / 64
gcc    -O2  | alignof(max_align_t) = 16 · 크기 1~64 중 그 배수 주소 64 / 64
clang  -O0  | alignof(max_align_t) = 16 · 크기 1~64 중 그 배수 주소 64 / 64
clang  -O2  | alignof(max_align_t) = 16 · 크기 1~64 중 그 배수 주소 64 / 64
```

- ★ **64 / 64** — 크기 1\~64 의 모든 할당이 `alignof(max_align_t) = 16` 의 배수다. 표준은 「**요청한 크기 이하의, 기본 정렬 요구를 가진 어떤 객체**에도 맞게」까지 약속한다([08번 형제](../08-sizeof-alignment-and-offsetof/)가 가리킨 계약). ★ **크기 1 에도 16 인 것은 이 판의 관찰**이다 — 표준의 문장은 「크기 이하의 객체」라 더 약하게 읽힐 수 있다.

## 문법 — 형태와 규칙

### 형태

(3)의 `s37d.c` · (6)의 `s37f.c` 첫 두 줄 · (9)의 `s37j.c` 가 이 절의 **실제로 컴파일되는 형태**다. 쓰는 자리를 한 줄씩:

| 쓴 꼴 | 뜻 | 판 |
|---|---|---|
| `T *p = malloc(n * sizeof *p);` | 할당 — ★ **곱셈 넘침은 호출자 몫** | C89 부터 |
| `T *p = calloc(n, sizeof *p);` | 할당 + 모든 비트 0 — ★ **곱셈 넘침은 `calloc` 이 본다** | C89 부터 |
| `if (p == NULL) { … }` | 실패 검사 — 모든 할당 뒤에 | C89 부터 |
| `T *tmp = realloc(p, m); if (!tmp) { …p 는 그대로… } p = tmp;` | ★★★ **원본을 잃지 않는 형태** | C89 부터 |
| `realloc(NULL, m)` | `malloc(m)` 과 같다 | C89 부터 |
| `free(p); p = NULL;` | 해제 — 널은 안전하니 이중 해제를 막는 관례(★ 복사본은 못 막는다 — 목록의 **57번 주제**) | C89 부터 |
| `realloc(p, 0)` | ★ **C23 부터 UB** — 해제는 `free` 로 | C23 |

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 종료 코드 | 층 | 어느 절 |
|---|---|---|---|
| `p = realloc(p, n)` | 경고 0(`clang --analyze` 만 1) · 실패 시 **LSan `Direct leak`**(ASan+null 에서만) | ★★★ 표준 위의 **누수**(UB 아님) | (3)·(4) |
| `malloc(a * b)` | 경고 0 · **작은 크기로 성공** | ★★★ 호출자의 산술 넘침 → 그 뒤 쓰기가 UB | (1) |
| 상수 `malloc(SIZE_MAX)` 로 실패 시험 | gcc 경고 1 · **clang `-O2` 는 `ptr`** | ★★ 컴파일러 구현 | (2) |
| `free(p); free(p);` | gcc `-Wuse-after-free` · **`cc exit=0`** · glibc `abort`(134) · ASan `double-free` | ★★★ UB | (6) |
| 해제 후 `p[0]` | gcc 경고 · ASan `heap-use-after-free` | ★★★ UB | (6) |
| `realloc(p, 0)` | **판 무관** — 경고 0(기본) · UBSan 0 | ★★ C23 UB · C17 구현 정의 | (8) |
| `malloc` 결과를 쓰기 전에 읽기 | MSan 1 · 경고는 [30번 형제](../30-initialization-rules-and-indeterminate-values/) | ★★ 불확정 값 | (9) |

### 규칙 불릿

- ★★★ **실패는 `NULL` 하나** — 모든 할당 뒤에 검사한다. `errno` 는 **POSIX 의 약속**이지 C 표준의 것이 아니다.
- ★★★ **`realloc` 의 결과는 다른 변수로 받는다** — 실패해도 원본은 살아 있고, 그것을 가리킬 변수가 남아 있어야 한다.
- ★★★ **곱셈이 있으면 `calloc`** 이거나, 곱하기 전에 `n > SIZE_MAX / size` 를 검사한다.
- ★★ **`free(NULL)` 은 안전하다** — 정리 경로를 한 곳으로 모을 수 있는 이유다.
- ★★ **같은 블록을 두 번 놓지 않는다 · 놓은 뒤 쓰지 않는다** — UB.
- ★★ **크기 0 은 구현 정의**(C23 의 `realloc` 은 UB) — 기대지 않는다.
- ★ **실패 경로를 시험할 때** — 크기를 `volatile` 로 · ASan 에는 `allocator_may_return_null=1`.

## 어디서 틀리나

### 1. ★★★ 「`p = realloc(p, n)` 이 제일 짧다」

**실패하면 원본이 샌다**((3)). 보통 빌드는 **아무것도 말하지 않는다**(`exit=0`). 잡는 것은 **`clang --analyze`** 와 **옵션을 바꾼 LSan** 뿐이었다.

### 2. ★★★ 「ASan 을 켰는데 누수가 안 나오더라」

**ASan 기본값은 실패를 일으키기 전에 죽인다**((1)·(3)). `allocator_may_return_null=1` 없이는 **실패 경로를 한 번도 못 지난다.** `setrlimit` 으로 바꾸면 **검사기가 먼저 죽는다**((5)).

### 3. ★★★ 「`malloc(n * size)` 가 `NULL` 이 아니니 공간은 있다」

**넘친 곱으로 작게 성공한 것**일 수 있다((1) — `n*2=2`). `calloc(n, size)` 는 같은 곱에 `NULL` 이다.

### 4. ★★ 「`malloc(SIZE_MAX)` 가 성공했다 — 이 머신은 이상하다」

**clang `-O2` 가 호출을 지웠다**((2)). 크기가 상수면 시험이 시험이 아니다.

### 5. ★★ 「`NULL` 이면 `errno` 를 찍으면 된다」

**C 표준은 `errno` 를 약속하지 않는다**((1)의 `man`). 이 판에서도 **clang `-O2` 는 `0` 을 읽었다.**

### 6. ★★ 「`realloc(p, 0)` 이 곧 `free(p)` 다」

이 판(glibc)에서는 그렇게 동작하지만 **C23 에서는 UB** 이고 C17 에서도 **구현 정의**였다((8)). **도구는 판을 가리지 않고 조용하다.**

### 7. ★ 「`realloc` 은 늘 제자리에서 늘린다(또는 늘 옮긴다)」

이 판의 16 번 중 **3 번 옮겼다**((7)). 어느 쪽도 약속이 아니다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸과 「구현 정의」 칸의 경계가 본체**다 — 실패의 모양은 표준이, 크기 0 과 `errno` 는 구현이 정한다.\
★★ **「UB」 칸**은 해제 쪽에 몰린다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | ★★★ **못 잡으면 널** · **실패한 `realloc` 은 옛 객체를 해제하지 않는다** · **`calloc` 은 곱이 넘치면 널 · 모든 비트 0** · **`free(NULL)` 은 아무 일도 없다** · `realloc(NULL, n)` = `malloc(n)` · 기본 정렬 · `realloc` 의 새 포인터는 옛것과 **같을 수도** 있다 | 격자 · `s37d` 가 옛 내용을 읽음 · `calloc(n, 2)` 의 `NULL` · (9) |
| **조건부 표준** | 매크로가 정의될 때만 | ★ **해당 없음** | — |
| ★★ **구현 정의** | 문서화 의무가 있다 | ★★ **크기 0 의 반환**(이 판: `ptr` · `realloc(p, 0)` 은 `NULL`) · ★ **`errno = ENOMEM`**(POSIX · glibc) · `PTRDIFF_MAX` 상한(glibc) · glibc 의 double free 검사 | 격자 · `man 3 malloc` · `exit=134` |
| ★★ **컴파일러 구현** | 도구의 선택 | ★★ **clang 이 쓰지 않는 할당을 지운 것** · clang `-O2` 의 `errno` `0` · ASan 의 `allocation-size-too-big` 멈춤 · 경고 묶음(`-Walloc-zero` 는 기본 밖) | (2)의 `call` 목록 · 격자 |
| **미명시** | 몇 가지 중 하나 | ★ **연속 할당의 순서와 인접성**(표준이 「미명시」라고 적는다) · ★ **`realloc` 이 옮기느냐**(표준은 「같을 수도」만) | (7) 20 판 |
| ★★★ **UB** | 아무 일이나 | ★★★ **double free · 해제 후 사용 · 메모리 관리 함수가 준 것이 아닌 포인터 `free`**(38편) · ★★ **C23 `realloc(p, 0)`** · 넘친 곱으로 받은 블록 밖 쓰기 | ASan 리포트 전문 · `exit=134` |

★ **이 판의 관찰** 칸 — `realloc` 이 16 번 중 3 번 옮긴 것 · 크기 1 에도 16 바이트 정렬 · `malloc(0)` 이 널이 아닌 것.

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★★ **`p = realloc(p, n)` 의 누수는 표준 위에서 적법한 프로그램**이다 — 보통 빌드 0 · gcc 분석기 0 · ASan 기본값은 **거기 가기 전에 죽는다** · LSan 은 **옵션을 바꿔야** 보인다 |
| ★★ **구현 정의** | ★★ **`realloc(p, 0)` 의 C17/C23 차이를 세 컴파일러·UBSan 이 전부 모른다**(0 / 8) |
| ★★ **컴파일러 구현** | ★★ **clang 이 `malloc(SIZE_MAX)` 를 지운 것에 경고가 없다** · clang `-O2` 의 `errno` 도 조용하다 |
| ★★★ **UB** | ★ **clang `-Wall` 은 double free · 해제 후 사용에 0** · ★ `setrlimit` 판에서는 **LSan 이 돌지 못한다** |
| ★★ **(층을 가로지름)** | ★ **「종료 코드 0인데 ill-formed」는 새 항목이 없다** · ★★ 대신 **「경고가 났는데 `cc exit=0`」** 이 셋(`-Wuse-after-free` 둘 · `-Walloc-size-larger-than`) — 빌드는 통과한다 |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **실패 경로는 기본값의 도구로는 안 보인다** — 보통 빌드는 조용하고, ASan 은 그 앞에서 멈춘다. **옵션을 바꾼 LSan 이 이 편의 네 번째 창**이다.
  - ★★ **「표준이 원본을 살려 둔다」는 약속이 누수를 만든다** — 호출 형태가 그 약속을 쓸모 있게도, 해롭게도 만든다.
  - ★★ **판의 차이(`realloc(p, 0)`)는 도구가 모른다** — 문서(N3220 부록)로만 안다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 버퍼 늘리기 | ★★★ **`tmp = realloc(p, n); if (!tmp) …; p = tmp;`** | `p = realloc(p, n)` |
| 개수 × 크기 | ★★★ **`calloc(n, size)`** 또는 곱하기 전 `n > SIZE_MAX / size` 검사 | `malloc(n * size)` 그대로 |
| 0 으로 채운 배열 | ★★ `calloc` — ★ **속도 비교는 재지 않았다** | 「빠르니까」를 근거로 |
| 해제 | ★★ `free(p)` — **널이면 그냥 넘어간다** | `realloc(p, 0)` |
| 실패 원인 | ★ `errno` 는 **POSIX 에서만** 믿는다 | C 표준 코드에서 `errno` 에 기대기 |
| 실패 경로 시험 | ★★ 크기를 `volatile` 로 · `ASAN_OPTIONS=allocator_may_return_null=1` | 상수 크기 · ASan 기본값 · `setrlimit` + ASan |

판단 규칙 두 줄.

- ★★★ **`NULL` 을 받을 변수가 원본을 가리키던 변수라면 멈춘다** — 그 한 줄이 누수다.
- ★★ **곱셈이 보이면 `calloc` 을 떠올린다** — 넘침 검사를 할당자에게 맡기는 유일한 표준 함수다.

## 핵심 문장

- ★★★ **실패 격자에서 갈린 칸 6 / 49 는 거대한 크기 두 줄에 몰렸다 — clang `-O2` 의 `errno` `0` 두 칸 · ASan 기본값의 멈춤 네 칸.**
- ★★★ **`calloc(n, 2)` 는 `NULL`, 같은 곱의 `malloc(n * 2)` 는 넘친 `2` 바이트로 성공했다.**
- ★★★ **`p = realloc(p, n)` 이 실패하면 16 바이트가 샌다 — LSan 은 `allocator_may_return_null=1` 을 준 판에서만 그것을 말했다(2 / 12).**
- ★★ **ASan 기본값은 거대한 요청을 `allocation-size-too-big` 로 멈춰 실패 경로를 막는다. `setrlimit` 으로 바꾸면 LSan 이 먼저 죽는다.**
- ★★ **clang `-O1`·`-O2` 는 쓰지 않는 상수 크기 `malloc(SIZE_MAX)` 를 지우고 `ptr` 로 답했다.**
- ★★ **`free(NULL)` 은 아무 일도 없고, 두 번째 `free(p)` 는 glibc 가 `abort`(134) · ASan 이 `double-free` 로 잡았다.**
- ★ **C23 이 `realloc(p, 0)` 을 UB 로 옮겼지만 이 판의 도구는 `c17` 과 `c2x` 에서 0 / 8 로 같게 굴었다.**

## 관련 자료

- [`data-structure/35-allocator/`](../../../../../data-structure/35-allocator/) — ★★★ **할당자 내부의 정본.** 그쪽은 **빈 목록 · 분할 · 병합 · 단편화**까지, 여기는 **그 위의 C API 계약 · 실패 처리 · 호출 형태**부터.
- [28번 형제 — 저장 기간 4종](../28-choosing-among-four-storage-durations/) — ★★ **선행.** 할당 저장 기간을 **고르는** 자리. 스택 한도와 `malloc` 의 `NULL` 대비가 거기 있다.
- [30번 형제 — 초기화 규칙과 불확정 값](../30-initialization-rules-and-indeterminate-values/) — ★★ `malloc` 불확정 · `calloc` 0 의 **실측 정본**((6)) · MSan 탐침 P7.
- [13번 형제 — `goto cleanup`](../13-goto-cleanup-idiom/) — ★ `free(NULL)` 보장에 기대는 정리 경로.
- [08번 형제 — `sizeof`·정렬](../08-sizeof-alignment-and-offsetof/) — ★ `max_align_t`.
- [26번 형제 — 유연 배열 멤버](../26-flexible-array-members/) — ★ 한 번의 `malloc` 으로 헤더와 꼬리를 묶는 자리.
- [38번 형제](../38-expressing-ownership-conventions-in-code/) — 누가 해제하나를 **시그니처로** 말하는 법(이 편의 짝).
- 목록의 **56번 주제**(배열 밖 접근) · 목록의 **57번 주제**(해제 후 사용 · 이중 해제의 패턴) · 목록의 **58번 주제**(sanitizer).

## 용어 풀이

> **할당 저장 기간** — `malloc` 계열이 돌려준 순간 시작해 `free`(또는 `realloc`)로 끝나는 수명.\
> 예: `char *p = malloc(16);` 부터 `free(p);` 까지.

> **`ENOMEM`** — 「메모리가 모자라다」 오류 번호. **POSIX** 가 할당 실패 시 `errno` 에 넣으라고 한다.\
> 예: 격자의 `NULL/ENOMEM`.

> **LeakSanitizer(LSan)** — 프로그램이 끝날 때 **어디서도 도달할 수 없는 블록**을 보고하는 검사기. ASan 에 들어 있다.\
> 예: `Direct leak of 16 byte(s) in 1 object(s) allocated from:`.

> **`allocator_may_return_null`** — ASan 옵션. 1 이면 지원 한도를 넘는 요청에 **멈추지 않고 널을 돌려준다.**\
> 예: `ASAN_OPTIONS=allocator_may_return_null=1 ./x`.

> **tcache** — glibc 할당기의 스레드별 작은 블록 캐시. double free 검사 문구에 이름이 나온다.\
> 예: `free(): double free detected in tcache 2`.

> **`-Walloc-zero`** — gcc 경고. 할당 함수에 **크기 0** 을 넘기면 알린다. `-Wall -Wextra` 에는 없다.\
> 예: `argument 2 value is zero`.

## 더 들어가면

- ★★ **clang `-O2` 의 `errno` `0`** — 어셈블리로 원인을 확정하지 않았다. `errno` 읽기가 `malloc` 뒤로 남았는지 `-S` 로 볼 자리다. ★ **던지지 않았다.**
- ★★ **`reallocarray`**(glibc · POSIX 2024) — `realloc` 에 **곱셈 넘침 검사**를 붙인 것. ★ **던지지 않았다.**
- ★ **C23 `free_sized` · `free_aligned_sized`** — 크기를 같이 넘기는 해제. N3220 에 있다. ★ **이 판의 glibc 에서 쓸 수 있는지 확인하지 않았다.**
- ★ **Valgrind `--leak-check=full`** — (3)의 누수를 다른 창에서. ★ **못 잰 것**(설치 안 됨).
- ★ **`aligned_alloc`** — 정렬을 지정하는 할당(C11). ★ **던지지 않았다.**
