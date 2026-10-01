# c/syntax/46 — `errno` 와 C 의 오류 반환 관례: 「**실패는 반환값이 말하고 `errno` 는 그 이유만 말한다 — 반환값을 건너뛰고 `errno` 부터 보면 성공한 호출도 실패로 읽힌다**」 — 정답

## 이 파일이 다시 싣는 소스

★ 8번의 어셈블리를 낸 소스를 다시 둔다.

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

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 판정 격자 — **`errno` 로 판정해 틀린 칸 4 / 14 · 반환값 먼저 판정해 틀린 칸 1 / 14 · 다섯 다 성공한 호출** ★★★

**출력**

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

**왜 그런가**

- ★★★ **실패한 네 호출(`strtol` 넘침 · `fopen` · `malloc` · `sqrt`)은 여덟 칸 다 맞다** — 실패는 `errno` 를 **자기 이유로 덮어쓴다.**
- ★★★ **`errno` 판정이 틀린 넷** — `strtol` 최댓값 · 안 함(남은 `ERANGE`) · `fprintf` 성공 · 안 함(남은 `ERANGE`) · **`localtime` 두 판**(성공인데 **스스로 `ENOENT`**).
- ★★ **반환값 판정이 틀린 하나** — `strtol` 최댓값 · 안 함. `LONG_MAX && errno == ERANGE` 가 **남은 `ERANGE`** 에 속았다.
- ★★ **「`errno = 0` 을 해야만 맞는 줄」은 `strtol` 최댓값** — 두 판정 다 `errno = 0` 판에서만 맞다. `fprintf` 줄은 **반환값 판정이면 초기화 없이도** 맞다.

### 2. 빌드 격자 — **실패했는데 `errno` 가 0 인 칸 5 / 18 · `sqrt` 는 `-fno-math-errno` 두 빌드 · `s46c` 는 clang `-O2` 와 `-fno-math-errno` 두 빌드 · `math_errhandling` 3 → 2** ★★★

**출력**

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

**왜 그런가**

- ★★★ **`-fno-math-errno` 는 `math_errhandling` 을 `2` 로 바꿨다** — `MATH_ERRNO` 비트가 없으니 `sqrt(-1.0)` 의 정의역 오류는 **`errno` 에 안 적힌다**(표준이 허용한다).
- ★★★ **`s46c` 의 `NULL/0` 셋** — `errno` 를 읽는 명령이 **지워졌다**(8번). clang `-O2` 와, **gcc 의 `-fno-math-errno`** 판도 그랬다.
- ★★ **`s46a` 의 `malloc` 은 여섯 빌드 다 `ENOMEM`** — 읽는 자리가 `snprintf`·`free` 뒤라 컴파일러가 **다시 읽었다.** 같은 가정이 **코드 모양에 따라** 드러나기도 숨기도 한다.
- ★★ **반환값은 18 칸 전부 실패를 말했다**(`NULL` · `NaN`).

### 3. `perror` · `strerror` — **`setlocale` 을 부르고 `LC_ALL=ko_KR.UTF-8` 일 때만 한국어** ★★

**출력**

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

**왜 그런가**

- ★★★ **프로그램은 시작 때 `"C"` 로케일**이다(표준). 환경변수는 **`setlocale(LC_ALL, "")` 을 불러야** 읽힌다 — 그래서 둘째 판은 영어, 셋째 판만 한국어다.
- ★★ **`int e = errno;` 를 `perror` 앞에** 둔 것은 `perror` 도 라이브러리 호출이라 **그 뒤의 `errno` 가 `perror` 가 남긴 값일 수 있기** 때문이다. 이유를 두 번 쓰려면 **먼저 옮긴다.**

### 4. 두 스레드의 `errno` — **worker `2` · 주소 다름 `0` · main `0`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -pthread s46t.c -o x ; ./x 2>&1 >/dev/null (cc exit=0 · run exit=0) =====
[worker] errno = 2
[worker] main 의 &errno 와 같은가 = 0
[main]   errno = 0
```

**왜 그런가**

- ★★ **`errno` 는 스레드 저장 기간**이다(표준) — worker 의 `ENOENT` 는 **worker 의 것**이고 main 의 `errno` 는 `0` 그대로다. 두 `&errno` 는 **다른 객체의 주소**다.

### 5. `errno` 의 정체 — **`(*__errno_location ())` · `nm` 에는 `U __errno_location` 만** ★★

**출력**

```text
===== gcc -std=c17 -E -P s46e.c | grep -A1 'read_errno' (exit=0) =====
int read_errno(void) { return (*__errno_location ()); }
```

```text
===== gcc -std=c17 -c s46e.c -o s46e.o && nm s46e.o (exit=0) =====
                 U __errno_location
0000000000000000 T read_errno
```

**왜 그런가**

- ★★ **표준은 「lvalue 로 펼쳐지는 매크로」까지만** 적는다 — glibc 는 **스레드마다 다른 주소를 돌려주는 함수 호출**로 펼친다. 목적 파일에 `errno` 라는 **전역 이름이 없다.**

### 6. 반환값을 먼저 — **표준: 설명에 없는 함수는 성공해도 `errno` 를 바꿀 수 있고, 아무도 0 으로 안 되돌린다** ★★★

- ★★★ N3220 은 두 문장을 적는다 — 「**`errno` 는 … 어떤 라이브러리 함수도 0 으로 되돌리지 않는다**」·「**함수 설명이 `errno` 를 쓴다고 적지 않았으면, 오류가 없어도 0 아닌 값으로 바꿀 수 있다**」. 앞 문장이 **남은 값**을, 뒤 문장이 **성공한 호출이 쓴 값**을 만든다.
- ★★ **`errno = 0` 을 하고도 틀린 줄은 `localtime`** — 성공한 `localtime` 이 시간대 파일을 찾다 실패한 흔적(`ENOENT`)을 **스스로 남겼다.** `man 3 errno` 도 「**성공한 함수도 `errno` 를 바꿀 수 있다**」고 적는다:

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

### 7. `strtol` 의 예외 — **`LONG_MAX` 가 성공값이기도 해서 · `errno = 0` 은 호출 바로 앞** ★★

- ★★ **`"9223372036854775807"` 의 정확한 변환도 `LONG_MAX`** 다 — 반환값 공간이 성공과 실패를 **같이** 쓴다. 가르는 것은 `errno == ERANGE` 하나뿐이다.
- ★★ **그 `errno` 는 호출 직전에 0 이어야 믿을 수 있다** — `strtol` 은 성공 시 `errno` 를 **안 건드리므로** 앞선 값이 그대로 보인다(`man`: 「**does not modify errno on success**」). **바로 앞**이어야 하는 이유는 사이에 낀 호출이 `errno` 를 쓸 수 있어서다(6번의 `localtime`).

### 8. clang `-O2` 의 `errno` `0` — **「`malloc` 은 `errno` 를 안 쓴다」는 가정 · `xor edx, edx` · C 표준 위반이 아니라 POSIX 약속을 지운 것 · `-fno-builtin-malloc`** ★★★

**출력**

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

**왜 그런가**

- ★★★ **`call malloc@PLT` 뒤에 `errno` 를 다시 읽는 명령이 없고**, `printf` 의 `errno` 인자(`edx`)가 **`xor edx, edx`** — 상수 0 이다. 앞의 `mov dword ptr [rax], 0`(`errno = 0`)을 **그대로 이어 쓴** 것이다.
- ★★ **C 표준의 `malloc` 은 `errno` 를 약속하지 않는다** — 그래서 이 최적화는 **표준 C 로는 틀리지 않았다.** 깨진 것은 **POSIX · glibc 의 약속**(실패 시 `ENOMEM`)이다.
- ★★ **`-fno-builtin-malloc` 이 풀었다**(`NULL 12`) — `malloc` 을 「아는 함수」로 보지 않게 하면 가정도 없다. ★ [37번 형제](../37-malloc-calloc-realloc-free/)의 추론(「앞서 쓴 `errno = 0` 을 그대로 썼다」)이 **이 블록으로 확정**됐다.

### 9. `math_errhandling` 과 `-fno-math-errno` — **`2` 면 부동소수 예외로만 · gcc 판은 `malloc` 까지 건드렸다** ★★

- ★★ **`math_errhandling` 이 `2`(`MATH_ERREXCEPT`)면** 정의역 오류는 **「invalid」 부동소수 예외**로 알려진다 — `errno` 는 **그대로 두거나 채울 수 있다**(표준). 이 판은 **그대로 뒀다**(`NaN/0`).
- ★★ **gcc `-O2 -fno-math-errno` 판에서 `s46c` 의 `malloc` 도 `NULL/0`** 이었다(2번 격자) — **플래그 이름은 「수학」인데 범위는 그보다 넓었다.** ★ 이것은 **이 판의 관찰**이다 — gcc 문서의 범위 진술은 읽지 않았다.

### 10. Go 의 다중 반환 — **실패를 「반환값의 한 자리」에 둬서 남은 값 · 공유 게시판이 없어졌다** ★★

- ★★ [Go 23](../../../go/syntax/23-error-interface-and-errors-as-values/)의 `(값, error)` 는 **호출마다 새 `error` 값**을 돌려준다 — `errno` 처럼 **이전 호출이 남긴 값을 읽을 자리가 없다.**
- ★★ 그래서 1번의 **「남은 `ERANGE`」 두 줄**(`strtol` 최댓값 · `fprintf` · 안 함)은 Go 에서 **원리상 안 생긴다.** `strtol` 의 「`LONG_MAX` 가 성공이기도 하다」도 **`err != nil` 이 따로 있어** 안 생긴다.
- ★ 남는 것 — **`err` 를 안 보는 실수**는 Go 에도 있다(`_` 로 버리기). 관례가 **순서**를 강제하지는 않는다.

### 11. 다섯 층과 경계 — **표준은 판정 순서의 문장들 · POSIX 가 `fopen`/`malloc` 의 `errno` · 컴파일러가 그 약속을 지울 수 있다** ★★

| 층 | 이 주제에서 |
|---|---|
| ★★★ **표준** | ★★★ `errno` 는 스레드마다의 lvalue 매크로 · 0 으로 안 되돌림 · 성공해도 바꿀 수 있음 · `strtol` 의 `ERANGE` · `math_errhandling` · 시작 로케일 `"C"` |
| ★★ **조건부 표준** | ★★ `math_errhandling` 의 값 |
| ★ **구현 정의** | ★ `strerror` 문구 |
| ★★ **POSIX · glibc** | ★★ `fopen`·`malloc` 의 `errno` · `__errno_location` · `localtime` 의 `ENOENT` |
| ★★ **컴파일러 구현** | ★★★ clang `-O2` 의 `malloc` 가정 · `-fno-math-errno` 의 범위 |

- ★ **`strtol` 파싱 전체**는 [목록의 **51번 주제**](../51-stdlib-conversion-qsort-and-bsearch/), **`strerror` 결과의 소유**는 [38번 형제](../38-expressing-ownership-conventions-in-code/)가 정본이다.

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s46a.c` | ★★★ **판정 격자 14 줄 · 5 / 28 · 4 / 14 · 1 / 14** · 두 컴파일러 경고 0 | 14 · 2 |
| `s46a.c` · `s46c.c` · `s46m.c` | ★★★ **빌드 격자 18칸 · 5 / 18** · `math_errhandling` 6 | 6 빌드 × 4 |
| `s46c.c` | ★★★ clang `-O2` 어셈블리 · `-fno-builtin-malloc` | 1 · 1 |
| `s46e.c` | ★★ `-E` · `nm` | 1 · 1 |
| `s46t.c` | ★★ 두 스레드 | 1 |
| `s46p.c` | ★★ 로케일 4 판 | 4 |
| — | ★ `man 3 errno` · `man 3 strtol` | 2 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. **이 편의 블록은 정규화 없이 전부 동일**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **1번의 `localtime` 줄** — glibc 가 없는 시간대 파일을 찾다 `ENOENT` 를 남긴 것.
- ★★★ **2번 · 8번** — clang 18 의 `malloc` 가정 · gcc 13 의 `-fno-math-errno` 범위.
- ★★ **5번** — `__errno_location`(glibc) · **3번** — 한국어 메시지 카탈로그가 설치된 머신.

**「반환값으로 실패를 판정하고 `errno` 는 그 뒤에만 읽는다」의 근거 문장들(0 으로 안 되돌림 · 성공해도 바꿀 수 있음 · `strtol` 의 `ERANGE`)은 구현 의존이 아니다.**\
어느 C 구현에서도 같다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `fetestexcept` 로 부동소수 예외 읽기 · `errno` 를 직접 선언하는 UB · 숫자 없는 `strtol` 의 `EINVAL`.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **2번 · 8번** — 컴파일러가 `malloc` 에 대한 가정을 바꾸면 칸이 움직인다.
- ★ **1번의 `localtime`** — glibc 의 시간대 처리가 바뀌면.

## 실행 환경

이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **clang 18.1.3** · **glibc 2.39** ·
x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
소스는 `s46a.c` · `s46c.c` · `s46e.c` · `s46m.c` · `s46p.c` · `s46t.c` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
★★★ **본체 창은 판정 격자** — 호출 7 × 호출 전 `errno` 2 × 판정법 2.
★★ **흔들리는 칸** — 없다. `localtime` 줄과 문구 블록은 **환경변수(`TZ` · `LC_ALL`)를 배너에 적어** 고정했다. 정규화 규칙은 기본 넷뿐이다.
