# c/syntax/46 — `errno` 와 C 의 오류 반환 관례: 「**실패는 반환값이 말하고 `errno` 는 그 이유만 말한다 — 반환값을 건너뛰고 `errno` 부터 보면 성공한 호출도 실패로 읽힌다**」 — 정리 (힌트)

★★★ **본체는 둘째 창 — 실행 결과의 판정 격자다.** 같은 호출을 **호출 전 `errno = 0` 을 하고/안 하고** 두 번 돌리고, 두 판정법이 맞았는지를 한 칸에 찍는다.
★★★ 그 격자에서 **틀린 판정 칸 5 / 28** — **`errno` 로 판정해 틀린 칸 4 / 14**, **반환값 먼저 판정해 틀린 칸 1 / 14**. 뒤쪽의 1 은 **`strtol` 에서 `errno = 0` 을 빠뜨린 줄**이다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | ★ 격자 소스는 **경고 0** — 판정 순서의 실수는 컴파일러가 모른다 | 씀(침묵으로) |
| ★★★ ② **실행 출력(판정 격자)** | ★ **본체** — 반환 · `errno` 이름 · 두 판정의 맞음/틀림 | 씀 |
| ③ sanitizer | — | 부적용(메모리 사고가 없는 주제다) |
| ④ 링크 · `nm` | ★ `errno` 가 **`U __errno_location`** 으로 보인다 | 씀 |
| ⑤ 어셈블리 | ★★★ clang `-O2` 가 **`errno` 읽기를 상수 0 으로 접은** 자리 | 씀 |
| ⑥ 전처리 출력(`-E`) | ★★ `errno` 가 **`(*__errno_location ())`** 로 펼쳐진다 | 씀 |
| 시간 측정 | — | 부적용 |
| ★ 제5의 상태 | 「이 실패의 이유가 무엇인가」를 **`errno` 에게 물으면 빌드에 따라 대답이 사라진다**(`0`). **반환값으로 바꿔 물으면** 여섯 빌드 전부 **실패를 말했다**(`NULL` · `NaN`) — 반환값은 이유를 안 주지만 **실패 여부는 한 번도 틀리지 않았다** | 창을 바꿔 답함 |

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

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **판정 격자 · 빌드 격자 · 스레드 · 문구** | 같은 판 · 같은 플래그 · 같은 환경변수(`TZ` · `LC_ALL`)면 같다 |
| ★ 환경에 매인다 | **`localtime` 줄**의 `errno` · **`perror` 문구** | `TZ` 가 가리키는 파일이 **있으면** `localtime` 줄이 바뀐다 · 문구는 **`LC_ALL` 과 `setlocale` 호출** 둘에 매인다 — 그래서 배너에 환경변수를 적었다 |
| ★ 흔들린다 | 어셈블리의 레지스터 배치 | 이 편은 **`errno` 를 읽는 자리가 있나**만 본다 |

## 한눈에 — 쉽게 말하면

**`errno` 는 창구 옆 게시판이다.** 창구(함수)는 **돌려주는 물건(반환값)** 으로 「됐다 / 안 됐다」를 말하고, **안 됐을 때만** 게시판에 이유를 붙인다.

- **게시판은 떼는 사람이 없다** — 어떤 함수도 게시판을 0 으로 지우지 않는다. **지난 손님의 사유**가 그대로 붙어 있다. → **남은 `errno`**
- **잘된 창구도 게시판에 뭔가 붙일 수 있다** — 일하다 겪은 사소한 일을 적어 두고 **일은 해냈다.** → **성공한 호출이 바꾼 `errno`**
- **그래서 물건부터 본다** — 물건이 「안 됐다」를 말할 때만 게시판을 읽는다. → **반환값 먼저**
- **물건만으로 모르는 창구가 있다** — 「최댓값」을 준 게 진짜 최댓값인지 넘친 건지. 그 창구 앞에서만 **게시판을 먼저 지우고** 기다린다. → **`strtol` 앞의 `errno = 0`**
- **창구마다 게시판이 따로다** — 스레드마다. → **`__errno_location()`**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 떼는 사람 없음 | 「라이브러리는 `errno` 를 0 으로 안 되돌린다」 | ★★★ 호출 전 `ERANGE` 가 **성공한 `fprintf` 뒤에도** 남았다 |
| 잘된 창구의 쪽지 | 성공한 `localtime` 이 `ENOENT` | ★★★ **`errno = 0` 을 해도 `errno` 판정이 틀렸다** |
| 물건부터 | 반환값 먼저 판정 | ★★ **틀린 칸 1 / 14** |
| 먼저 지우는 창구 | `strtol` 앞 `errno = 0` | ★★ 빠뜨린 줄 하나가 그 1 이다 |
| 창구마다 게시판 | 스레드 저장 기간 | ★★ 다른 스레드의 `ENOENT` 가 main 에서 `0` |

```text
   판정 순서 — 한 방향으로만 읽는다

   r = f(...);
        |
        v
   반환값이 실패 모양인가?  (NULL · -1 · EOF · NaN · 음수 …)
        |                          |
       아니다                      그렇다
        |                          |
        v                          v
   성공이다                    이제 errno 를 읽는다 — 이유
   errno 는 읽지 않는다          (다른 호출 전에 옮겨 둔다)
   (무엇이 들어 있든)

   ★ 예외 — 성공과 실패가 같은 반환값을 쓰는 함수 (strtol 의 LONG_MAX)
      errno = 0;  r = strtol(...);  if (r == LONG_MAX && errno == ERANGE) 넘침
      └ 지우는 자리는 「바로 앞」 — 사이에 다른 호출이 끼면 그 호출이 쓸 수 있다
```

- ★★★ **이 주제의 본체는 「표준」 칸** — 「0 으로 안 되돌린다」·「성공해도 바꿀 수 있다」·「`strtol` 은 `ERANGE`」·「수학 함수는 `math_errhandling` 에 따라」가 **전부 표준 문장**이다.
- ★★ **`fopen`·`malloc` 이 `errno` 를 채우는 것은 표준이 아니라 POSIX(와 glibc)의 약속**이다 — 표준은 「실패하면 널」까지만 적는다.

> **`errno`** — 「마지막으로 실패를 알린 라이브러리 호출의 이유」가 들어 있는 `int` lvalue. **스레드마다** 따로다.\
> 예: `fopen` 이 `NULL` 을 돌려준 **직후**의 `errno == ENOENT`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **실패는 무엇으로 판정하고 `errno` 는 언제 읽나** — 반환값을 먼저 보지 않으면 어느 칸이 틀리나.
2. ★★ **`errno = 0` 은 언제 해야 하나** — 반환값만으로 실패를 못 가르는 함수와 그 자리.
3. ★★ **`errno` 가 조용히 틀리는 자리는 어디인가** — 성공한 호출 · 빌드 플래그 · 스레드 · 로케일.

## 동작 방식

### (1) ★★★ 판정 격자 — 호출 일곱 × 호출 전 `errno` × 판정법 둘

**언제 쓰나** — 오류 검사 코드를 **`if (errno)` 로 쓸까 반환값으로 쓸까** 정할 때. ★★★ **이 편의 본체**다.

```c
/* s46a.c */
#include <errno.h>
#include <limits.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* volatile — 컴파일러가 인자를 미리 알고 호출을 접지 못하게 한다 */
static volatile size_t huge = SIZE_MAX;
static volatile double minus_one = -1.0;
static void *volatile sink;

static const char *name(int e) {
    switch (e) {
    case 0: return "0";
    case ERANGE: return "ERANGE";
    case ENOENT: return "ENOENT";
    case ENOMEM: return "ENOMEM";
    case EDOM: return "EDOM";
    default: return "기타";
    }
}

int main(int argc, char **argv) {
    int k = argc > 1 ? atoi(argv[1]) : 0;
    int reset = argc > 2 ? atoi(argv[2]) : 0;
    int real_fail = 0, ret_says_fail = 0;
    char ret[32] = "";
    FILE *out = fopen("/dev/null", "w");
    if (out == NULL) return 2;

    (void)strtol("99999999999999999999", NULL, 10);   /* 앞선 호출 하나 */
    if (reset) errno = 0;

    switch (k) {
    case 1: { long v = strtol("99999999999999999999", NULL, 10);
              real_fail = 1;
              ret_says_fail = (v == LONG_MAX || v == LONG_MIN) && errno == ERANGE;
              snprintf(ret, sizeof ret, "%s", v == LONG_MAX ? "LONG_MAX" : "?"); break; }
    case 2: { long v = strtol("9223372036854775807", NULL, 10);
              real_fail = 0;
              ret_says_fail = (v == LONG_MAX || v == LONG_MIN) && errno == ERANGE;
              snprintf(ret, sizeof ret, "%s", v == LONG_MAX ? "LONG_MAX" : "?"); break; }
    case 3: { FILE *f = fopen("s46-none.txt", "r");
              real_fail = 1; ret_says_fail = f == NULL;
              snprintf(ret, sizeof ret, "%s", f == NULL ? "NULL" : "ptr");
              if (f) fclose(f);
              break; }
    case 4: { void *q = malloc(huge); sink = q;
              real_fail = 1; ret_says_fail = q == NULL;
              snprintf(ret, sizeof ret, "%s", q == NULL ? "NULL" : "ptr");
              free(q);
              break; }
    case 5: { double r = sqrt(minus_one);
              real_fail = 1; ret_says_fail = isnan(r);
              snprintf(ret, sizeof ret, "%s", isnan(r) ? "NaN" : "수"); break; }
    case 6: { int n = fprintf(out, "x");
              real_fail = 0; ret_says_fail = n < 0;
              snprintf(ret, sizeof ret, "%d", n); break; }
    case 7: { time_t t = 0; struct tm *tm = localtime(&t);
              real_fail = 0; ret_says_fail = tm == NULL;
              snprintf(ret, sizeof ret, "%s", tm == NULL ? "NULL" : "ptr"); break; }
    }
    int e = errno;
    int errno_says_fail = e != 0;
    printf("%s\t%s\t%s\t%s\n", ret, name(e),
           errno_says_fail == real_fail ? "맞음" : "틀림",
           ret_says_fail == real_fail ? "맞음" : "틀림");
    fclose(out);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s46a.c -o /dev/null (cc exit=0) =====
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s46a.c -o /dev/null (cc exit=0) =====
```

```text
===== errno 관례 격자 — 호출 7 × 호출 전 errno=0 (안 함 / 함) × 판정 2 (exit=0) =====
호출                                	호출 전   	반환	errno	errno 로 판정	반환값 먼저 판정	실제
strtol 넘침 "99999999999999999999"  	안 함     	LONG_MAX	ERANGE	맞음	맞음	실패
strtol 넘침 "99999999999999999999"  	errno=0   	LONG_MAX	ERANGE	맞음	맞음	실패
strtol 최댓값 "9223372036854775807" 	안 함     	LONG_MAX	ERANGE	틀림	틀림	성공
strtol 최댓값 "9223372036854775807" 	errno=0   	LONG_MAX	0	맞음	맞음	성공
fopen 없는 파일                     	안 함     	NULL	ENOENT	맞음	맞음	실패
fopen 없는 파일                     	errno=0   	NULL	ENOENT	맞음	맞음	실패
malloc(SIZE_MAX)                    	안 함     	NULL	ENOMEM	맞음	맞음	실패
malloc(SIZE_MAX)                    	errno=0   	NULL	ENOMEM	맞음	맞음	실패
sqrt(-1.0)                          	안 함     	NaN	EDOM	맞음	맞음	실패
sqrt(-1.0)                          	errno=0   	NaN	EDOM	맞음	맞음	실패
fprintf 성공                        	안 함     	1	ERANGE	틀림	맞음	성공
fprintf 성공                        	errno=0   	1	0	맞음	맞음	성공
localtime(0) · TZ 파일 없음         	안 함     	ptr	ENOENT	틀림	맞음	성공
localtime(0) · TZ 파일 없음         	errno=0   	ptr	ENOENT	틀림	맞음	성공
(각 줄 = TZ=s46/none ./x <호출> <0|1> · 호출 전에 strtol 넘침을 한 번 불러 errno 를 ERANGE 로 남겨 둔다 · gcc -O0)
(errno 로 판정 = errno != 0 이면 실패 · 반환값 먼저 판정 = 반환이 실패 모양일 때만 실패 — strtol 은 LONG_MAX/LONG_MIN 이고 errno == ERANGE 일 때)
errno 로 판정해 틀린 칸 4 / 14
반환값 먼저 판정해 틀린 칸 1 / 14
틀린 판정 칸 5 / 28
```

그림 해설 (한 단계씩):

- ★★★ **호출 전 `errno` 는 `ERANGE`** 로 시작한다 — `main` 이 앞에서 `strtol` 넘침을 한 번 불러 **남겨 둔** 값이다. 실제 코드에서 **앞선 어떤 실패가 남긴 값**과 같은 자리다.
- ★★★ **`errno` 로 판정해 틀린 칸 4 / 14** — 전부 **실제로는 성공한 호출**이다.
  - **`fprintf` 성공 · 안 함** — `fprintf` 는 `errno` 를 **안 건드렸다.** 남은 `ERANGE` 가 **실패로 읽혔다.**
  - **`strtol` 최댓값 · 안 함** — `strtol` 은 성공 시 `errno` 를 안 바꾼다(`man` — 「**does not modify errno on success**」). 남은 `ERANGE` 가 그대로 남았다.
  - ★★★ **`localtime` · 두 판 다** — **`errno = 0` 을 하고 불러도** `errno` 가 **`ENOENT`** 다. 반환은 **`ptr`(성공)** 이다. 시간대 파일(`TZ=s46/none`)을 찾다 실패한 흔적을 **남긴 채 일은 해냈다** — 표준이 「설명에 `errno` 가 없는 함수는 오류가 없어도 바꿀 수 있다」고 적은 **바로 그 자리**다.
- ★★ **반환값 먼저 판정해 틀린 칸 1 / 14** — **`strtol` 최댓값 · 안 함** 한 줄뿐이다. 반환이 `LONG_MAX` 이고 `errno` 가 `ERANGE` 라서 **넘침으로 읽혔다.** 그 `ERANGE` 는 **앞선 호출이 남긴 것**이다 — **`strtol` 앞에서는 `errno = 0` 이 필요하다**((3)).
- ★★ **실패한 네 호출은 여덟 칸 다 맞다** — 실패한 호출은 `errno` 를 **자기 이유로 덮어쓰므로**(`ENOENT` · `ENOMEM` · `EDOM` · `ERANGE`) 남은 값이 문제가 안 된다.
- ★★★ **틀린 판정 칸 5 / 28** — 그 다섯이 **전부 성공한 호출**에 있다. **`errno` 판정의 사고는 「실패를 놓친다」보다 「성공을 실패로 본다」 쪽**이었다.

### (2) ★★★ 빌드 격자 — 같은 실패가 `errno` 에 안 남는 빌드

**언제 쓰나** — 「디버그 빌드에서는 이유가 찍히는데 릴리스에서는 `Success` 가 찍힌다」.

```c
/* s46c.c */
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
static volatile size_t huge = SIZE_MAX;
static void *volatile sink;
int main(void) {
    errno = 0;
    void *q = malloc(huge);
    sink = q;
    int e = errno;
    printf("%s %d\n", q == NULL ? "NULL" : "ptr", e);
    free(q);
    return 0;
}
```

```c
/* s46m.c */
#include <math.h>
#include <stdio.h>

int main(void) {
    printf("math_errhandling = %d (MATH_ERRNO %d · MATH_ERREXCEPT %d)\n",
           math_errhandling, MATH_ERRNO, MATH_ERREXCEPT);
    return 0;
}
```

```text
===== 빌드 격자 — 실패 호출 3 × 빌드 6 (호출 전 errno=0) (exit=0) =====
빌드                        	malloc(SIZE_MAX) (s46a 4 1)	sqrt(-1.0) (s46a 5 1)	malloc(SIZE_MAX) (s46c)	math_errhandling
gcc -O0                     	NULL/ENOMEM	NaN/EDOM	NULL/12	3
gcc -O2                     	NULL/ENOMEM	NaN/EDOM	NULL/12	3
clang -O0                   	NULL/ENOMEM	NaN/EDOM	NULL/12	3
clang -O2                   	NULL/ENOMEM	NaN/EDOM	NULL/0	3
gcc -O2 -fno-math-errno     	NULL/ENOMEM	NaN/0	NULL/0	2
clang -O2 -fno-math-errno   	NULL/ENOMEM	NaN/0	NULL/0	2
(칸 = 반환/errno · s46c 는 errno 를 숫자로 찍는다(12 = ENOMEM) · math_errhandling 1 = MATH_ERRNO · 2 = MATH_ERREXCEPT)
실패했는데 errno 가 0 인 칸 5 / 18
```

- ★★★ **실패했는데 `errno` 가 0 인 칸 5 / 18** — 반환은 **18 칸 전부 실패**(`NULL` · `NaN`)를 말했다.
- ★★★ **`sqrt(-1.0)` 은 `-fno-math-errno` 두 빌드에서 `NaN/0`** — `math_errhandling` 이 **`3` → `2`** 로 바뀌었다. `MATH_ERRNO`(1) 비트가 빠졌으니 **표준이 허용하는 대로** 정의역 오류를 `errno` 에 안 적는다(부동소수 예외 쪽으로만 알린다).
- ★★★ **`s46c` 의 `malloc(SIZE_MAX)` 는 clang `-O2` 와 `-fno-math-errno` 두 빌드에서 `NULL/0`** — `errno` 를 **읽는 코드 자체가 없어졌다**((4)).
- ★★ **같은 호출인데 `s46a` 는 여섯 빌드 다 `ENOMEM`** — `s46a` 는 `malloc` 뒤에 `snprintf`·`free` 가 끼고 **`switch` 밖에서** `errno` 를 읽는다. 컴파일러가 「그 사이 누가 `errno` 를 썼을 수 있다」고 보고 **다시 읽었다.** ★ **같은 가정이 코드 모양에 따라 드러나기도 숨기도 한다** — [37번 형제](../37-malloc-calloc-realloc-free/)의 격자가 clang `-O2` 에서 `NULL/0` 이었던 것도 이 모양이다.
- ★★ **`-fno-math-errno` 는 수학 함수만 건드리지 않았다** — gcc 판에서 `malloc` 의 `errno` 도 접혔다. 플래그 이름이 범위를 말하지 않는다.

### (3) ★★ `strtol` — `errno = 0` 이 필요한 예외

**언제 쓰나** — 반환값의 **모든 값이 성공일 수도 있는** 함수를 부를 때.

```text
===== MANWIDTH=80 man 3 strtol | sed -n '/^RETURN VALUE/,/^ATTRIBUTES/p' | grep -v '^ATTRIBUTES' (exit=0) =====
RETURN VALUE
       The strtol() function returns the result of the conversion, unless  the
       value  would  underflow  or overflow.  If an underflow occurs, strtol()
       returns LONG_MIN.  If an overflow occurs,  strtol()  returns  LONG_MAX.
       In  both  cases,  errno is set to ERANGE.  Precisely the same holds for
       strtoll()  (with  LLONG_MIN  and  LLONG_MAX  instead  of  LONG_MIN  and
       LONG_MAX).

ERRORS
       This function does not modify errno on success.

       EINVAL (not in C99) The given base contains an unsupported value.

       ERANGE The resulting value was out of range.

       The  implementation  may also set errno to EINVAL in case no conversion
       was performed (no digits seen, and 0 returned).

```

- ★★★ **`LONG_MAX` 는 성공의 값이기도 하다** — `"9223372036854775807"` 은 넘침이 아니다. 반환만으로는 **넘침과 정확한 최댓값이 같다.**
- ★★★ **그래서 `errno` 가 유일한 구분자이고, 그 `errno` 를 믿으려면 호출 직전에 0 이어야 한다** — `strtol` 은 **성공 시 `errno` 를 안 건드리므로**(`man`) 남은 값이 그대로 보인다. 격자의 「반환값 먼저 · 안 함」 한 칸이 그 사고다.
- ★★ **지우는 자리는 「바로 앞」** — `errno = 0;` 과 `strtol(…)` 사이에 다른 라이브러리 호출이 끼면 그 호출이 `errno` 를 쓸 수 있다((1)의 `localtime`).
- ★ `man` 은 한 가지를 더 적는다 — 「**변환이 없었을 때(숫자 없음) `EINVAL` 을 넣을 수도 있다**」. **표준에는 없는 약속**이다. 빈 입력은 **끝 포인터**로 가른다 — [목록의 **51번 주제**](../51-stdlib-conversion-qsort-and-bsearch/).

### (4) ★★★ clang `-O2` 의 `errno` `0` — 37편의 추론을 확정한다

**언제 쓰나** — `errno` 를 읽었는데 **실패 직후인데도 0** 일 때.

```text
===== clang -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s46c.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand | sed -n '/^main:/,/ret/p' (cc exit=0) =====
main:                                   # @main
# %bb.0:
        push    rbx
        call    __errno_location@PLT
        mov     dword ptr [rax], 0
        mov     rdi, qword ptr [rip + huge]
        call    malloc@PLT
        mov     rbx, rax
        mov     qword ptr [rip + sink], rax
        test    rax, rax
        lea     rax, [rip + .L.str.1]
        lea     rsi, [rip + .L.str.2]
        cmove   rsi, rax
        lea     rdi, [rip + .L.str]
        xor     edx, edx
        xor     eax, eax
        call    printf@PLT
        mov     rdi, rbx
        call    free@PLT
        xor     eax, eax
        pop     rbx
        ret
```

```text
===== clang -std=c17 -O2 -fno-builtin-malloc s46c.c -o x ; ./x (cc exit=0 · run exit=0) =====
NULL 12
```

- ★★★ **`call malloc` 뒤에 `errno` 를 읽는 명령이 없다** — `printf` 의 셋째 인자(`edx`)가 **`xor edx, edx`**, 즉 **상수 0** 이다. clang 은 「**`malloc` 은 `errno` 를 안 바꾼다**」고 보고, 앞에서 쓴 `errno = 0` 을 **그대로 가져다 썼다.**
- ★★ **`-fno-builtin-malloc` 을 주면 `NULL 12`**(`ENOMEM`)로 돌아온다 — 컴파일러가 `malloc` 을 **「내가 아는 그 함수」로 보지 않게** 하면 가정도 사라진다.
- ★★★ **이것은 C 표준 위반이 아니다** — 표준의 `malloc` 은 `errno` 를 **약속하지 않는다.** 깨진 것은 **POSIX(와 glibc 문서)의 약속**이다 — 「할당 실패 시 `errno` 를 `ENOMEM` 으로」. **표준 C 만 보고 쓰는 컴파일러 최적화가 POSIX 약속을 지운 자리**다.
- ★★ [37번 형제](../37-malloc-calloc-realloc-free/)의 「clang 이 `malloc` 은 `errno` 를 안 바꾼다고 보고 앞서 쓴 `errno = 0` 을 그대로 썼다」는 **추론이 맞았다** — 이 블록이 그 근거다.

### (5) ★★ `errno` 의 정체 — 매크로 · 함수 호출 · 스레드마다

**언제 쓰나** — 「`errno` 는 전역 변수」라는 말을 들었을 때.

```c
/* s46e.c */
#include <errno.h>

int read_errno(void) { return errno; }
```

```text
===== gcc -std=c17 -E -P s46e.c | grep -A1 'read_errno' (exit=0) =====
int read_errno(void) { return (*__errno_location ()); }
```

```text
===== gcc -std=c17 -c s46e.c -o s46e.o && nm s46e.o (exit=0) =====
                 U __errno_location
0000000000000000 T read_errno
```

```c
/* s46t.c */
#include <errno.h>
#include <pthread.h>
#include <stdio.h>

static void *worker(void *main_errno) {
    errno = ENOENT;                              /* 이 스레드에서 쓴다 */
    fprintf(stderr, "[worker] errno = %d\n", errno);
    fprintf(stderr, "[worker] main 의 &errno 와 같은가 = %d\n", main_errno == (void *)&errno);
    return NULL;
}

int main(void) {
    pthread_t t;
    errno = 0;
    if (pthread_create(&t, NULL, worker, (void *)&errno) != 0) return 1;
    pthread_join(t, NULL);
    fprintf(stderr, "[main]   errno = %d\n", errno);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -pthread s46t.c -o x ; ./x 2>&1 >/dev/null (cc exit=0 · run exit=0) =====
[worker] errno = 2
[worker] main 의 &errno 와 같은가 = 0
[main]   errno = 0
```

```text
===== MANWIDTH=80 man 3 errno | sed -n '/^   errno$/,/^   Error numbers/p' | grep -v '^   Error numbers' (exit=0) =====
   errno
       The value in errno is significant only when the  return  value  of  the
       call  indicated  an  error (i.e., -1 from most system calls; -1 or NULL
       from most library functions); a function that succeeds  is  allowed  to
       change  errno.   The  value of errno is never set to zero by any system
       call or library function.

       For some system calls and library functions (e.g., getpriority(2)),  -1
       is  a  valid return on success.  In such cases, a successful return can
       be distinguished from an error return by setting errno to  zero  before
       the call, and then, if the call returns a status that indicates that an
       error may have occurred, checking to see if errno has a nonzero value.

       errno  is  defined  by  the ISO C standard to be a modifiable lvalue of
       type int, and must not be explicitly declared; errno may  be  a  macro.
       errno  is  thread-local;  setting  it in one thread does not affect its
       value in any other thread.

```

- ★★★ **`errno` 는 변수가 아니라 `(*__errno_location ())` 로 펼쳐지는 매크로**다 — 목적 파일에는 **`U __errno_location`** 만 있고 `errno` 라는 이름은 **없다.** 표준은 「**수정 가능한 lvalue 로 펼쳐지는 매크로**」까지만 적는다 — 함수 호출로 펼치는 것은 **glibc 의 선택**이다.
- ★★ **스레드마다 따로다** — worker 가 `ENOENT` 를 써도 main 은 `0`, 두 `&errno` 는 **다른 주소**다. 표준이 **스레드 저장 기간**이라고 적는 자리다.
- ★ `man 3 errno` 는 **「성공한 함수도 `errno` 를 바꿀 수 있다」·「어떤 호출도 0 으로 안 되돌린다」** 를 그대로 적는다 — 표준과 같은 말이다.

### (6) ★★ `perror` · `strerror` — 문구는 로케일에 매인다

**언제 쓰나** — 로그의 오류 문구가 **환경마다 다른 말**로 나올 때.

```c
/* s46p.c */
#include <errno.h>
#include <locale.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
    (void)argv;
    if (argc > 1) setlocale(LC_ALL, "");       /* 인자가 있으면 환경의 로케일을 쓴다 */
    FILE *f = fopen("s46-none.txt", "r");
    if (f == NULL) {
        int e = errno;                          /* 다른 호출 전에 옮겨 둔다 */
        perror("fopen s46-none.txt");
        fprintf(stderr, "strerror(%d) = %s\n", e, strerror(e));
        return 1;
    }
    fclose(f);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s46p.c -o x ; LC_ALL=C ./x 2>&1 >/dev/null (cc exit=0 · run exit=1) =====
fopen s46-none.txt: No such file or directory
strerror(2) = No such file or directory
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s46p.c -o x ; LC_ALL=ko_KR.UTF-8 ./x 2>&1 >/dev/null (cc exit=0 · run exit=1) =====
fopen s46-none.txt: No such file or directory
strerror(2) = No such file or directory
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s46p.c -o x ; LC_ALL=ko_KR.UTF-8 ./x setlocale 2>&1 >/dev/null (cc exit=0 · run exit=1) =====
fopen s46-none.txt: 그런 파일이나 디렉터리가 없습니다
strerror(2) = 그런 파일이나 디렉터리가 없습니다
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s46p.c -o x ; LC_ALL=C ./x setlocale 2>&1 >/dev/null (cc exit=0 · run exit=1) =====
fopen s46-none.txt: No such file or directory
strerror(2) = No such file or directory
```

- ★★★ **`LC_ALL=ko_KR.UTF-8` 만으로는 문구가 안 바뀐다** — 프로그램은 **`setlocale(LC_ALL, "")` 을 부르기 전까지 `"C"` 로케일**이다(표준: 시작 시 로케일은 `"C"`). **환경변수 + `setlocale` 호출** 둘이 다 있어야 한국어가 나온다.
- ★★ **문구는 로그 파싱의 열쇠로 쓰지 마라** — 같은 `ENOENT` 가 `No such file or directory` 와 `그런 파일이나 디렉터리가 없습니다` 로 갈렸다. **`errno` 값(숫자·매크로)** 을 남긴다.
- ★★ **`int e = errno;` 를 `perror` 앞에** — `perror` 자신도 라이브러리 호출이다. 그 뒤의 `errno` 는 **`perror` 가 남긴 값일 수 있다.** 이유를 두 번 쓰려면 **먼저 옮겨 둔다.**
- ★ `strerror` 가 돌려준 문자열은 **놓으면 안 되고 다음 호출이 덮을 수 있다** — [38번 형제](../38-expressing-ownership-conventions-in-code/)가 정본이다.

## 문법 — 형태와 규칙

### 형태

(1)의 `s46a.c` 의 **「반환값 먼저」 판정**(`ret_says_fail`)이 이 절의 실제로 컴파일되는 형태다. 함수마다 실패의 모양:

| 함수 | 실패의 모양(반환) | 그때 `errno` | 누가 약속하나 |
|---|---|---|---|
| `fopen` | ★ `NULL` | `ENOENT` 등 | ★★ **POSIX** — 표준은 「널」까지만 |
| `malloc` | ★ `NULL` | `ENOMEM` | ★★ **POSIX · glibc** — (4)에서 **컴파일러가 지운** 약속 |
| `strtol` | ★★★ **`LONG_MAX`/`LONG_MIN` 이면서 `errno == ERANGE`** — 호출 전 `errno = 0` | `ERANGE` | ★★★ **표준** |
| `sqrt` 등 수학 함수 | ★ `NaN`(정의역 오류) | `EDOM` — **`math_errhandling & MATH_ERRNO` 일 때만** | ★★ **표준**(조건부) |
| `fprintf`/`printf` | ★ **음수** | 표준은 말하지 않는다 | ★ 표준(반환만) |
| `localtime` | ★ `NULL` | — | ★★ **성공해도 `errno` 를 바꿨다**((1)) |

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 결과 | 층 | 어느 절 |
|---|---|---|---|
| `f(); if (errno) 실패;` | 경고 0 · ★★★ **성공을 실패로** — 남은 값 · 성공한 호출이 쓴 값 | ★★★ 표준(성공 시 `errno` 는 무엇이든 될 수 있다) | (1) |
| `strtol` 앞에 `errno = 0` 없음 | 경고 0 · ★★ **정확한 최댓값을 넘침으로** | ★★★ 표준 | (1) · (3) |
| 실패 직후 다른 호출(`perror`·`printf`) 뒤에 `errno` 읽기 | 경고 0 · 이유가 바뀔 수 있다 | ★★ 표준 | (6) |
| `malloc` 실패의 이유를 `errno` 로 | clang `-O2` · `-fno-math-errno` 에서 **`0`** | ★★ POSIX 약속 · 컴파일러 구현 | (2) · (4) |
| `-fno-math-errno` 빌드에서 `sqrt` 실패를 `errno` 로 | **`0`** · `math_errhandling` = `2` | ★★ 표준이 허용 | (2) |

### 규칙 불릿

- ★★★ **실패는 반환값으로 판정한다. `errno` 는 반환값이 실패를 말한 뒤에만, 다른 호출 전에 읽는다.**
- ★★★ **어떤 라이브러리 함수도 `errno` 를 0 으로 되돌리지 않는다 — 성공한 호출은 `errno` 를 그대로 두거나 바꾼다.**
- ★★ **반환값만으로 실패를 못 가르는 함수(`strtol` 류)만 호출 바로 앞에 `errno = 0`.**
- ★★ **수학 함수의 `errno` 는 `math_errhandling & MATH_ERRNO` 일 때만 믿는다.**
- ★ **문구가 아니라 값을 남긴다** — `strerror` 문구는 로케일에 매인다.

## 어디서 틀리나

### 1. ★★★ 「`errno` 가 0 이 아니면 실패다」

**성공한 호출 셋이 실패로 읽혔다**((1) — `fprintf` · `strtol` 최댓값 · `localtime`). `localtime` 은 **`errno = 0` 을 하고 불러도** `ENOENT` 를 남겼다.

### 2. ★★★ 「호출 전에 `errno = 0` 을 하면 `errno` 판정도 안전하다」

**아니다** — 성공한 호출이 **스스로** 쓴다((1)의 `localtime` 두 판). `errno = 0` 은 **「반환값이 애매할 때 `errno` 로 가른다」** 는 한 경우의 도구다.

### 3. ★★ 「`strtol` 이 `LONG_MAX` 면 넘친 것이다」

정확한 최댓값도 `LONG_MAX` 다. **`errno = 0` → 호출 → `errno == ERANGE`** 까지가 한 묶음이다((3)).

### 4. ★★ 「`malloc` 이 실패하면 `errno` 가 `ENOMEM` 이다」

**clang `-O2` 는 그 읽기를 지웠다**((4)). `errno` 는 **POSIX 의 약속**이고 컴파일러는 **표준 C 만** 볼 수 있다.

### 5. ★★ 「`-fno-math-errno` 는 수학 함수만 바꾼다」

gcc 판에서 **`malloc` 의 `errno` 읽기도 접혔다**((2)).

### 6. ★ 「`LANG` 을 바꾸면 `perror` 가 한국어로 나온다」

**`setlocale(LC_ALL, "")` 을 불러야** 나온다((6)).

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 본체**다 — 판정 순서를 강제하는 문장들이 전부 표준에 있다.\
★★ **「`fopen`·`malloc` 이 `errno` 를 채운다」는 POSIX 칸**이고, 그 약속을 **컴파일러가 지운** 자리가 있다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | ★★★ **`errno` 는 스레드마다의 `int` lvalue 매크로** · **시작 때 0 · 라이브러리는 0 으로 안 되돌림** · **설명에 없는 함수는 성공해도 바꿀 수 있다** · `strtol` 의 `ERANGE` · `math_errhandling` 조건 · 시작 로케일 `"C"` | 판정 격자 · 스레드 · 빌드 격자의 `sqrt` · 문구 |
| **조건부 표준** | 매크로가 정의될 때만 | ★★ **`math_errhandling` 의 값**(`MATH_ERRNO` · `MATH_ERREXCEPT` · 둘 다) | 빌드 격자 `3` / `2` |
| ★ **구현 정의** | 문서화 의무가 있다 | ★ **`strerror` 의 문구** · 로케일 이름(`ko_KR.UTF-8`) | 문구 블록 |
| ★★ **POSIX · glibc** | 표준 밖의 약속 | ★★ **`fopen`·`malloc` 이 `errno` 를 채운다** · `strtol` 은 성공 시 안 바꾼다 · 숫자 없음에 `EINVAL` 가능 · **`errno` = `(*__errno_location ())`** · `localtime` 이 `TZ` 파일을 찾다 `ENOENT` | `man` · `-E` · `nm` · 격자 |
| ★★ **컴파일러 구현** | 도구의 선택 | ★★★ **clang `-O2` 가 `malloc` 은 `errno` 를 안 쓴다고 가정** · **`-fno-math-errno` 가 gcc 에서 `malloc` 까지** · `-fno-builtin-malloc` 으로 풀림 | 어셈블리 · 빌드 격자 |
| **UB** | 아무 일이나 | ★ **`errno` 를 직접 선언하거나 매크로를 가리는 것**(표준: UB) — 이 편은 **던지지 않았다** | — |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★★ **`if (errno)` 판정에 경고가 없다** — 격자 소스는 두 컴파일러 `-Wall -Wextra -pedantic` 경고 0 |
| ★★ **POSIX · glibc** | ★★ 성공한 `localtime` 이 `errno` 를 바꿨다는 **어떤 알림도 없다** |
| ★★ **컴파일러 구현** | ★★★ **`errno` 읽기를 상수로 접은 것에 경고가 없다** — 어셈블리로만 보인다 · `-fno-math-errno` 의 범위도 말하지 않는다 |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **반환값은 여섯 빌드 전부에서 실패를 말했다 — `errno` 는 다섯 칸에서 침묵했다.** 믿을 창은 반환값이다.
  - ★★ **`errno` 판정의 사고는 「성공을 실패로」 쪽이었다(4 / 14)** — 남은 값과 성공한 호출이 쓴 값.
  - ★★ **`errno` 의 약속 가운데 표준 것과 POSIX 것을 갈라라** — 컴파일러는 앞쪽만 지킨다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 실패 판정 | ★★★ **반환값**(널 · 음수 · `EOF` · `NaN`) | `if (errno)` |
| 실패의 이유 | ★★ 실패 직후 **`int e = errno;`** 로 옮기고 쓰기 | 다른 호출 뒤에 `errno` 읽기 |
| `strtol` 넘침 | ★★★ **`errno = 0` → 호출 → `LONG_MAX/MIN && ERANGE`** | 반환값만 · 앞에서 지운 `errno` |
| 수학 함수 실패 | ★★ **반환값(`isnan` 등)** 또는 `math_errhandling` 확인 후 `errno` | `-fno-math-errno` 빌드에서 `errno` |
| 로그 | ★ **`errno` 숫자·이름**을 남기기 | 문구로 분기 |
| 스레드 | ★ 그 스레드 안에서 읽기 | 다른 스레드의 `errno` 기대 |

판단 규칙 두 줄.

- ★★★ **「반환값이 실패를 말했나」를 먼저 묻고, 그렇다고 할 때만 `errno` 를 연다.**
- ★★ **`errno = 0` 은 반환값이 애매한 함수 바로 앞에만 둔다 — 그 밖에는 판정에 아무 도움이 안 된다.**

## 핵심 문장

- ★★★ **판정 격자에서 틀린 판정 칸 5 / 28 — `errno` 로 판정해 4 / 14, 반환값 먼저 판정해 1 / 14. 다섯이 전부 성공한 호출에 있었다.**
- ★★★ **성공한 `localtime` 은 `errno = 0` 을 하고 불러도 `ENOENT` 를 남겼다 — 표준이 허용하는 자리다.**
- ★★★ **`strtol` 은 정확한 최댓값도 `LONG_MAX` 라 `errno = 0` 이 필요한 예외다 — 빠뜨린 한 줄이 반환값 판정의 유일한 오답이었다.**
- ★★★ **빌드 격자에서 실패했는데 `errno` 가 0 인 칸 5 / 18 — 반환값은 18 칸 전부 실패를 말했다.**
- ★★ **clang `-O2` 는 `malloc` 뒤의 `errno` 읽기를 `xor edx, edx` 로 접었다 — 37편의 추론이 맞았다. `-fno-builtin-malloc` 이 되돌린다.**
- ★★ **`errno` 는 `(*__errno_location ())` 로 펼쳐지는 스레드마다의 값이다.**
- ★ **`perror` 문구는 환경변수만으로 안 바뀌고 `setlocale` 호출까지 있어야 바뀌었다.**

## 관련 자료

- [37번 형제 — `malloc`/`calloc`/`realloc`/`free`](../37-malloc-calloc-realloc-free/) — ★★★ **선행.** 실패 격자의 clang `-O2` `errno` `0` 두 칸 — 이 편 (4)가 원인을 확정했다.
- [34번 형제 — 함수 선언·정의·프로토타입](../34-function-declarations-definitions-and-prototypes/) — ★ 반환 타입으로 실패를 알리는 관례의 앞.
- [38번 형제 — 소유권 관례](../38-expressing-ownership-conventions-in-code/) — ★ `strerror` 결과를 놓으면 안 된다.
- [목록의 **51번 주제**](../51-stdlib-conversion-qsort-and-bsearch/)(`<stdlib.h>` 변환) — ★★ `strtol` 파싱 전체(끝 포인터 · 빈 입력)의 정본.
- [47번 형제 — `<stdio.h>` 스트림 · 버퍼링 · 서식 출력](../47-stdio-streams-buffering-and-formatted-output/) — ★ `printf` 의 반환값(음수가 실패).
- [Go 23 — `error` 인터페이스와 값으로서의 에러](../../../go/syntax/23-error-interface-and-errors-as-values/) — ★★ 실패를 **반환값 자리에** 두는 설계.

## 용어 풀이

> **`errno`** — 실패한 라이브러리 호출이 이유를 적는 **스레드마다의** `int` lvalue. glibc 에서는 `(*__errno_location ())`.\
> 예: `fopen` 이 `NULL` 을 준 뒤 `errno == ENOENT`.

> **`ERANGE` · `EDOM` · `ENOENT` · `ENOMEM`** — 범위 밖 · 정의역 밖 · 파일 없음 · 메모리 부족. **앞 둘은 표준**, 뒤 둘은 **POSIX**.\
> 예: `strtol` 넘침 → `ERANGE`, `sqrt(-1.0)` → `EDOM`.

> **`math_errhandling`** — 수학 함수가 오류를 **`errno` 로(1) · 부동소수 예외로(2) · 둘 다(3)** 알리는지 말하는 값.\
> 예: `-fno-math-errno` 빌드는 `2`.

> **`perror` / `strerror`** — 현재 `errno`(또는 인자)의 이유를 **문구**로 찍는다 / 돌려준다. 문구는 **로케일에 매인다.**\
> 예: `perror("fopen s46-none.txt")` → `fopen s46-none.txt: No such file or directory`.

> **`-fno-builtin-malloc`** — 컴파일러가 `malloc` 을 **알려진 함수로 다루지 않게** 하는 플래그. 그 함수에 대한 가정(여기서는 「`errno` 를 안 쓴다」)이 사라진다.\
> 예: clang `-O2` 에서 `NULL 0` → `NULL 12`.

## 더 들어가면

- ★★ **`errno` 를 쓰는 함수 목록** — 표준에서 `errno` 를 **문서로 약속한** 함수는 적다(`strtol` 류 · 수학 함수 · `fgetpos`/`ftell` 등). 나머지는 **POSIX 가 채운다.** ★ **전수로 읽지 않았다.**
- ★ **`errno` 를 저장·복원하는 라이브러리 관례** — 표준 각주가 「진입 때 저장하고 0 으로 둔 뒤, 여전히 0 이면 복원」을 허용한다. ★ **던지지 않았다.**
- ★ **부동소수 예외로 받기(`fetestexcept`)** — `math_errhandling` 이 `2` 인 빌드의 실패를 읽는 창. ★ **던지지 않았다.**

## 실행 환경

**기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) `<errno.h>` 절 — 「**`errno` 는 스레드 저장 기간을 가진 수정 가능한 `int` lvalue 로 펼쳐지는 매크로**」·「**첫 스레드의 `errno` 는 시작 때 0 이지만 어떤 라이브러리 함수도 0 으로 되돌리지 않는다**」·「**함수 설명이 `errno` 를 쓴다고 적지 않았으면, 그 함수는 오류가 없어도 `errno` 를 0 아닌 값으로 바꿀 수 있다**」·각주 「**`errno` 로 오류를 검사하는 프로그램은 호출 전에 0 으로 두고, 다음 라이브러리 호출 전에 읽는다**」, `strtol` 의 「**범위 밖이면 `LONG_MAX`/`LONG_MIN` 을 돌려주고 `ERANGE` 를 `errno` 에 넣는다**」, `<math.h>` 의 「**`math_errhandling & MATH_ERRNO` 가 0 이 아니면 정의역 오류에 `errno` 가 `EDOM` 이 된다**」·「**오류가 없으면 `math_errhandling` 과 무관하게 `errno` 를 건드리지 않는다**」, `fopen` 의 「**실패하면 널 포인터**」(`errno` 는 말하지 않는다)를 **본문에서 직접 찾아 읽었다**) · 이 머신의 **`man 3 errno` · `man 3 strtol`**(글자째 캡처)
★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **반환값 · `errno` 값 · 어셈블리 · 문구는 전부 실행으로** 접지했다.
**실행 검증** — 이 문서의 모든 출력·진단은 「이 판」 절의 판에서 실제로 돌려 **파일로 캡처한 것**이다.\
★★★ **본체는 판정 격자다** — 호출 7 × 호출 전 `errno = 0`(안 함 / 함) × 판정법 2(`errno` 로 / 반환값 먼저).\
★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
★★★ **경계** — **`malloc` 실패의 반환·`errno`**(탐침 7 × 빌드 8)는 [37번 형제](../37-malloc-calloc-realloc-free/)가 **이미 쟀다** — clang `-O2` 에서 **`errno` 가 0 으로 읽힌** 두 칸이 거기 있고, 원인은 「**내 추론 · 확정 안 함**」으로 남아 있었다. 이 편은 그 칸을 **어셈블리로 확정**한다((4)).\
★ **`strtol` 로 문자열을 파싱하는 법 전체**(끝 포인터 · 빈 입력 · `atoi` 대비)는 [목록의 **51번 주제**](../51-stdlib-conversion-qsort-and-bsearch/), **`strerror`·`getenv` 결과를 놓으면 안 된다**는 소유 규칙은 [38번 형제](../38-expressing-ownership-conventions-in-code/)가 정본이다. 여기는 **`errno` 를 언제 믿나**만 본다.
선행 — [34번 형제](../34-function-declarations-definitions-and-prototypes/) · [37번 형제](../37-malloc-calloc-realloc-free/).
