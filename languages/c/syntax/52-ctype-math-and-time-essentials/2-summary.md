# c/syntax/52 — `<ctype.h>` · `<math.h>` · `<time.h>` 핵심: 「**`isalpha` 는 `unsigned char` 의 값을 기다리고, NaN 검사는 옵션 하나에 지워지며, `localtime` 은 하나뿐인 칸을 돌려준다**」 — 정리 (힌트)

★★★ **본체는 둘째 창 — 실행 출력의 ctype 격자다.** 로케일 다섯 × `char` 부호 둘 × 바이트 둘(`0xE9` · `0xFF`)에서 `isalpha(c)` 와 `isalpha((unsigned char)c)` 를 나란히 찍고, **스크립트가 두 호출이 갈린 칸을 센다.**
★★★ 그 격자에서 **갈린 칸 1 / 20** — 그런데 그 한 칸은 **UB 칸이 아니라 정의된 칸**이다. UB 인 다섯 칸은 **glibc 가 표를 음수 쪽으로 늘려 둔 덕에** 전부 멀쩡한 값을 냈다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | clang `-Wnan-infinity-disabled` · gcc **0 건** · `localtime_r` 의 암시적 선언((4)·(6)) | 씀 |
| ★★★ ② **실행 출력(ctype 격자)** | ★ **본체** — 로케일 × 부호 × 바이트 · NaN 격자 · 시각 | 씀 |
| ③ sanitizer | ★★ **glibc `isalpha` 에 음수를 넣어도 ASan+UBSan 침묵** · 자작 표는 ASan `heap-buffer-overflow` | 씀 |
| ④ 어셈블리 | ★★ `-ffast-math` 판의 `check_isnan` 이 **`xor eax,eax` · `ret`** 두 줄이 된다((5)) | 씀 |
| 시간 측정 | — | 부적용(성능 주제가 아니다) · ★ **벽시계 시각도 부적용** — 현재 시각을 찍지 않았다 |
| ★ 제5의 상태 | 「음수를 넘기는 것이 왜 UB 인가」는 **glibc 에서는 물을 수 없다**(표가 음수 쪽으로 늘려져 있어 **증상이 없다**) — **256 칸짜리 표를 직접 만들어 ASan 으로** 물었다((2)). ★ 그리고 「`EOF` 와 겹치는 바이트」는 **이 머신에 없는 Latin-1 로케일을 `localedef` 로 만들어서야** 보였다 | 창을 바꿔 답함 |

★ **바꾼 창(자작 표 + ASan)이 못 보는 것** — **glibc 의 실제 동작**은 말하지 않는다. 「표준을 따르는 **다른** 구현에서는 이렇게 될 수 있다」는 **가능성의 시연**이다.

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
===== locale -a (exit=0) =====
C
C.utf8
POSIX
ko_KR.utf8
```

```text
===== mkdir -p ./loc && localedef -i en_US -f ISO-8859-1 ./loc/en_US.ISO-8859-1 && ls ./loc (exit=0) =====
en_US.ISO-8859-1
```

★★ **`en_US.UTF-8` 은 이 머신에 없다**(`locale -a` 에 없다) — 격자에 넣되 `setlocale` 이 `NULL` 인 줄로 남긴다. ★ **Latin-1 로케일도 없어서** 스크래치 디렉토리의 `./loc` 에 **만들어 `LOCPATH=./loc` 로만** 썼다(시스템에 설치하지 않았다).

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | ASan 리포트의 **PID** · **주소** · `BuildId` · `pc`/`bp`/`sp` | 실행마다 다르다 — 기본 규칙이 지운다 |
| 안 흔들린다 | ★★★ **ctype 격자 · NaN 격자 · 어셈블리** · 경고 | 같은 판 · 같은 플래그면 같다 |
| 안 흔들린다(선언) | ★★ **시각 블록** | `time_t` 가 고정 · `TZ` 가 명령에 있다. ★ **tzdata 판이 바뀌면 흔들릴 수 있다**(`Asia/Seoul` 은 이 기간에 규칙 변화가 없어 안 흔들릴 것으로 본다 — ★ 확인하지 않았다) |

★★ **정규화 규칙은 기본 넷뿐**이다.

## 한눈에 — 쉽게 말하면

**세 헤더는 「받는 칸의 규격」을 어기면 조용히 틀린다.**

- **`isalpha` 는 「번호표 0\~255 와 `EOF` 하나」만 받는 창구다** — 부호 있는 `char` 의 `'\xE9'` 는 **번호표 −23** 이다. 이 창구(glibc)는 −128\~−1 번 줄도 **예전 손님을 위해** 만들어 두었다. 그래서 틀린 번호표도 **대개** 받아 준다. 그런데 **−1 번은 `EOF` 자리**라 `'\xFF'` 는 **「손님이 아니다」** 로 처리된다. → **`(unsigned char)` 로 넘겨라**
- **부동소수의 「같다」는 「같은 눈금」이 아니라 「가까운 눈금」이다** — 눈금 간격이 **값의 크기에 비례**하니 「가깝다」도 **비율로** 재야 한다. → **상대 오차**
- **NaN 은 「자기와도 다른 값」이다** — 그런데 `-ffast-math` 는 컴파일러에게 **「NaN 은 안 온다」고 약속**하는 것이라, 컴파일러는 검사를 **「항상 아니다」로 바꿔 끼운다.** → **옵션이 보장을 거둔다**
- **`localtime` 은 「공용 칠판 한 장」에 답을 적어 준다** — 다음 사람이 물으면 **같은 칠판을 지우고 쓴다.** `gmtime` 도 **같은 칠판**이다. → **정적 버퍼 공유 · `localtime_r`**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 번호표 0\~255 · `EOF` | `<ctype.h>` 의 인자 범위 | ★★★ 격자의 `*` 칸 · `0(EOF)` 칸 |
| 음수 줄도 만들어 둔 창구 | glibc 의 384 칸 표 | ★★ 헤더 주석 · UB 칸이 전부 멀쩡 |
| 음수 줄이 없는 창구 | 256 칸 자작 표 | ★★ ASan `23 bytes before` |
| 「NaN 은 안 온다」는 약속 | `-ffinite-math-only` | ★★★ `isnan` → `xor eax,eax` |
| 공용 칠판 | `localtime`/`gmtime` 의 정적 `struct tm` | ★★★ `p1 == p2 : 1` · `p1 == g : 1` |

```text
   char c = '\xE9';     // 이 판의 char 는 부호 있음

   (int)c        = -23          <- 0..255 도 EOF(-1) 도 아니다  -> isalpha(c) 는 UB
   (unsigned char)c = 233       <- 범위 안                       -> isalpha 는 정의됨

   char c = '\xFF';
   (int)c        = -1  == EOF   <- UB 는 아니다. 그런데 "문자"가 아니라 "EOF" 로 읽힌다
   (unsigned char)c = 255       <- Latin-1 에서는 'ÿ' — 알파벳
```

- ★★★ **이 주제의 본체는 「UB」 칸과 「정의됐지만 틀린」 칸이 뒤바뀐 자리**다 — UB 인 `-23` 은 glibc 에서 **맞는 답**을, 정의된 `-1` 은 **틀린 답**을 냈다.
- ★★ **「옵션이 보장을 거둔다」 칸** — `isnan` 의 「NaN 이면 참」은 **`-ffinite-math-only` 아래에서는 컴파일러가 지키지 않는다.**

> **`isalpha(c)`** — `c` 가 **현재 로케일에서** 알파벳이면 0 이 아닌 값. 인자는 **`unsigned char` 로 표현 가능한 값 또는 `EOF`** 여야 한다.\
> 예: `isalpha((unsigned char)s[i])`.

> **`localtime_r(&t, &buf)`** — `localtime` 과 같되 **호출자의 `buf`** 에 쓴다(C23 · POSIX).\
> 예: `struct tm tm; localtime_r(&t, &tm);`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **`<ctype.h>` 에 `char` 를 그대로 넘기면 무엇이 달라지나** — 부호 · `EOF` · 로케일 · 도구.
2. ★★★ **부동소수를 어떻게 「같다」고 하고, NaN 을 어떻게 검사하나** — 절대 · 상대 오차 · 네 가지 검사 · 옵션.
3. ★★ **`<time.h>` 의 칸은 누가 쓰나** — 정적 버퍼 · `mktime` 정규화 · `tm_mon`·`tm_year`.

## 동작 방식

### (1) ★★★ ctype 격자 — 로케일 다섯 × `char` 부호 둘 × 바이트 둘

**언제 쓰나** — 사용자 입력 · 파일 내용의 바이트를 **`isalpha`·`isspace`·`toupper`** 로 분류할 때. ★★★ **이 편의 본체**다.

```c
/* s52a.c */
#include <ctype.h>
#include <locale.h>
#include <stdio.h>
#include <wctype.h>

int main(int argc, char **argv) {
    const char *r = setlocale(LC_ALL, argc > 1 ? argv[1] : "C");
    const char in[] = { '\xE9', '\xFF' };
    /* 필드: setlocale 성공 여부, 그리고 바이트마다 (int)c · isalpha(c) · isalpha((unsigned char)c) · iswalpha */
    printf("%s", r ? "ok" : "NULL");
    for (int k = 0; k < 2; k++) {
        char c = in[k];
        printf("\x1f%d\x1f%d\x1f%d\x1f%d", (int)c, isalpha(c) != 0,
               isalpha((unsigned char)c) != 0, iswalpha((wint_t)(unsigned char)c) != 0);
    }
    printf("\n");
    return 0;
}
```

```text
===== ctype 에 char 를 그대로 — 로케일 5 × char 부호 2 × 바이트 2 (gcc -O0) (exit=0) =====
로케일             char     setlocale || 0xE9: (int)c  isalpha(c)  isalpha((uc)c)  iswalpha || 0xFF: (int)c  isalpha(c)  isalpha((uc)c)  iswalpha
C                  기본     ok        || -23        0*          0               0        || -1         0(EOF)      0               0        
C                  unsigned ok        || 233        0           0               0        || 255        0           0               0        
C.UTF-8            기본     ok        || -23        0*          0               1        || -1         0(EOF)      0               1        
C.UTF-8            unsigned ok        || 233        0           0               1        || 255        0           0               1        
ko_KR.UTF-8        기본     ok        || -23        0*          0               1        || -1         0(EOF)      0               1        
ko_KR.UTF-8        unsigned ok        || 233        0           0               1        || 255        0           0               1        
en_US.UTF-8        기본     NULL      || -23        0*          0               0        || -1         0(EOF)      0               0        
en_US.UTF-8        unsigned NULL      || 233        0           0               0        || 255        0           0               0        
en_US.ISO-8859-1   기본     ok        || -23        1*          1               1        || -1         0(EOF)      1               1        <-0xFF 
en_US.ISO-8859-1   unsigned ok        || 233        1           1               1        || 255        1           1               1        
(기본 = 이 판의 char 는 부호 있음 · unsigned = -funsigned-char · * = EOF 아닌 음수를 넘긴 칸: UB — 이 glibc 의 관찰 · en_US.ISO-8859-1 은 LOCPATH=./loc)
isalpha(c) 와 isalpha((unsigned char)c) 가 갈린 칸 1 / 20
```

```text
===== gcc -std=c17 -O0 -g -fsanitize=address,undefined -ffile-prefix-map="$PWD"=. s52a.c -o x && LOCPATH=./loc ./x en_US.ISO-8859-1 | tr '\037' ' ' (exit=0) =====
ok -23 1 1 1 -1 0 1 1
```

그림 해설 (한 단계씩):

- ★★★ **갈린 칸은 하나 — Latin-1 · 기본 빌드 · `0xFF`** 다. `(int)c` 가 `-1` 이 되어 **`EOF` 와 같은 값**이고, `isalpha(EOF)` 는 0 이다. `(unsigned char)c` 는 255 = 'ÿ' 라 1 이다. **이 칸은 UB 가 아니다** — `EOF` 는 허용된 인자다. **정의된 호출이 틀린 답을 냈다.**
- ★★★ **`*` 표시 다섯 칸(기본 빌드 · `0xE9` → `-23`)은 전부 UB 인데, 전부 `(unsigned char)` 칸과 같은 답**이다 — Latin-1 에서는 `1*`, 나머지는 `0*`. glibc 가 **음수 인덱스에도 답을 채워 두었기** 때문이다(8번 · 아래 헤더 주석).
- ★★ **`-funsigned-char` 판은 열 칸 다 두 호출이 같다** — `char` 가 부호 없으면 `'\xE9'` 는 233, `'\xFF'` 는 255 다. **같은 소스가 컴파일 옵션 하나로 UB 에서 벗어난다**(부호는 구현 정의 — [02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)).
- ★★ **로케일이 결과를 바꾼다** — `C` · 두 UTF-8 로케일에서 `isalpha((unsigned char)0xE9)` 는 **0**, Latin-1 에서는 **1**. UTF-8 에서 바이트 `0xE9` 는 **글자가 아니라 여러 바이트 글자의 첫 조각**이기 때문이다.
- ★★ **`iswalpha` 열은 바이트가 아니라 코드 포인트를 묻는다** — 소스가 `(wint_t)(unsigned char)c` 로 넘기므로 U+00E9 'é' · U+00FF 'ÿ' 를 묻는 셈이다. **UTF-8 로케일 둘과 Latin-1 에서 1, `C` 에서 0** 이다.
- ★ **`en_US.UTF-8` 줄은 `setlocale` 이 `NULL`** — 없는 로케일이라 **`C` 로 남았다.** 그래서 `C` 줄과 한 글자도 같다. 격자를 읽을 때 그 줄은 **「C 로케일 한 번 더」** 다.
- ★★ **ASan+UBSan 판도 Latin-1 줄을 그대로 찍고 침묵**했다(`-23 1 1 1 -1 0 1 1`) — 두 sanitizer 가 **UB 칸(`-23`)을 못 봤다.** `isalpha` 는 **glibc 의 표를 인덱스로 읽는 매크로**이고(아래 헤더 블록의 마지막 세 줄), 그 표가 **실제로 음수 쪽까지 있어서** ASan 이 볼 경계 밖 접근이 아니다.

```text
===== sed -n '71,76p;88,89p;190p' /usr/include/ctype.h | expand (exit=0) =====
   These point into arrays of 384, so they can be indexed by any `unsigned
   char' value [0,255]; by EOF (-1); or by any `signed char' value
   [-128,-1).  ISO C requires that the ctype functions work for `unsigned
   char' values and for EOF; we also support negative `signed char' values
   for broken old programs.  The case conversion arrays are of `int's
   rather than `unsigned char's because tolower (EOF) must be EOF, which
# define __isctype(c, type) \
  ((*__ctype_b_loc ())[(int) (c)] & (unsigned short int) type)
# define isalpha(c)     __isctype((c), _ISalpha)
```

- ★★★ **glibc 가 스스로 적었다** — `isalpha(c)` 는 `__isctype` 을 거쳐 **`(*__ctype_b_loc ())[(int) (c)]`** 를 읽는다. 표는 **384 칸**이고 **`[-128, -1)` 도 받도록** 만들었으며 「ISO C 는 `unsigned char` 값과 `EOF` 만 요구한다 · **오래된 망가진 프로그램을 위해** 음수도 받는다」. **UB 칸이 멀쩡한 이유는 표준이 아니라 이 주석**이다.

비용 — **`(unsigned char)` 캐스트 한 번.** 그것만으로 UB 도, `0xFF` 의 `EOF` 충돌도 사라진다.

### (2) ★★ 제5의 상태 — 256 칸짜리 표를 직접 만들면

**언제 쓰나** — 「glibc 에서 괜찮으니 괜찮다」가 **다른 구현에서도** 참인지 묻고 싶을 때.

```c
/* s52b.c */
#include <stdio.h>
#include <stdlib.h>

static unsigned char *alpha_tbl;           /* 인덱스 0..255 만 있는 분류 표 */

static int my_isalpha(int c) { return alpha_tbl[c]; }

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    alpha_tbl = calloc(256, 1);
    if (!alpha_tbl) return 1;
    for (int k = 'A'; k <= 'Z'; k++) alpha_tbl[k] = alpha_tbl[k + 32] = 1;
    char c = '\xE9';
    printf("my_isalpha('A') = %d\n", my_isalpha('A'));
    printf("my_isalpha(c)   = %d\n", my_isalpha(c));
    free(alpha_tbl);
    return 0;
}
```

```text
===== gcc -std=c17 -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s52b.c -o x && ASAN_OPTIONS=strip_path_prefix="$PWD/" ./x | sed -n '1,/^SUMMARY/p' | grep -v -E '^ +#[1-9]' (exit=1) =====
my_isalpha('A') = 1
=================================================================
==1149524==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x511000000029 at pc 0x5c099ec602dc bp 0x7ffc2bde0310 sp 0x7ffc2bde0300
READ of size 1 at 0x511000000029 thread T0
    #0 0x5c099ec602db in my_isalpha s52b.c:6

0x511000000029 is located 23 bytes before 256-byte region [0x511000000040,0x511000000140)
allocated by thread T0 here:
    #0 0x70c43aefd340 in calloc ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:77

SUMMARY: AddressSanitizer: heap-buffer-overflow s52b.c:6 in my_isalpha
```

```text
===== clang -std=c17 -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s52b.c -o x && ASAN_OPTIONS=strip_path_prefix="$PWD/" ./x | sed -n '1,/^SUMMARY/p' | grep -v -E '^ +#[1-9]' (exit=1) =====
my_isalpha('A') = 1
=================================================================
==1149607==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x511000000029 at pc 0x59bf9a5ff90e bp 0x7ffc8ba29be0 sp 0x7ffc8ba29bd8
READ of size 1 at 0x511000000029 thread T0
    #0 0x59bf9a5ff90d in my_isalpha s52b.c:6:39

0x511000000029 is located 23 bytes before 256-byte region [0x511000000040,0x511000000140)
allocated by thread T0 here:
    #0 0x59bf9a5c137d in calloc (x+0xc637d) (BuildId: 2c6f78e2a35e3340ec52ab545aff6fa1c11408f5)

SUMMARY: AddressSanitizer: heap-buffer-overflow s52b.c:6:39 in my_isalpha
```

- ★★★ **첫 줄(`'A'`)만 찍히고 둘째 줄에서 ASan 이 멈춘다** — `heap-buffer-overflow` · **`23 bytes before 256-byte region`**. `-23` 이 **표의 23 칸 앞**을 읽었다.
- ★★ **표준을 따르는 구현이 256 칸 표를 써도 된다** — 표준은 음수를 **요구하지 않으니까.** 그런 구현에서 `isalpha(c)` 는 **표 밖을 읽는다.** glibc 의 멀쩡함은 **이식되지 않는다.**
- ★ 그래서 이 블록은 **glibc 의 동작이 아니라 「UB 가 무엇일 수 있나」의 시연**이다(규칙 18-B 제5의 상태 — 창을 바꿔 답함).

### (3) ★★ 네 쌍의 「같은가」 — 절대 오차는 양쪽으로 틀린다

**언제 쓰나** — 계산 결과를 기댓값과 비교할 때. `0.1 + 0.2 != 0.3` 과 `DBL_EPSILON` 의 크기는 [04번 형제](../04-floating-point-types-and-conversions/) (2)·(3)절이 정본이고, 여기서는 **절대 오차와 상대 오차를 같은 표에** 놓는다.

```c
/* s52c.c */
#include <float.h>
#include <math.h>
#include <stdio.h>

static int near_abs(double a, double b) { return fabs(a - b) < DBL_EPSILON; }
static int near_rel(double a, double b) {
    return fabs(a - b) <= 4 * DBL_EPSILON * fmax(fabs(a), fabs(b));
}

int main(void) {
    double pair[][2] = {
        { 0.1 + 0.2, 0.3 },
        { 1e-20, 2e-20 },
        { 1e16, 1e16 + 2 },
        { 1e16 * (1 + DBL_EPSILON), 1e16 },
    };
    printf("%-26s %-26s  ==  abs  rel\n", "a", "b");
    for (int k = 0; k < 4; k++) {
        double a = pair[k][0], b = pair[k][1];
        printf("%-26.17g %-26.17g  %d   %d    %d\n", a, b, a == b, near_abs(a, b), near_rel(a, b));
    }
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s52c.c -o x -lm ; ./x (cc exit=0 · run exit=0) =====
a                          b                           ==  abs  rel
0.30000000000000004        0.29999999999999999         0   1    1
9.9999999999999995e-21     1.9999999999999999e-20      0   1    0
10000000000000000          10000000000000002           0   0    1
10000000000000002          10000000000000000           0   0    1
```

```text
   값의 크기            이웃 double 사이 간격(대략)    fabs(a-b) < DBL_EPSILON 이면
   1e-20                1e-36                          1e-20 과 2e-20 도 "같다"   ★ 너무 느슨
   1                    2.2e-16                        의도대로
   1e16                 2                              이웃 값조차 "다르다"       ★ 너무 빡빡
```

- ★★★ **`abs` 는 두 방향으로 틀렸다** — `1e-20` 과 `2e-20`(두 배 차이)을 **같다**고 했고, `1e16` 과 **바로 옆 double** 인 `10000000000000002` 를 **다르다**고 했다.
- ★★ **`rel` 은 넷 다 의도대로** — 차이를 **두 값 중 큰 쪽의 크기에 비례한 문턱**(`4 * DBL_EPSILON * fmax(|a|,|b|)`)과 견준다. ★ 문턱의 **4** 는 이 편이 고른 값이다 — 계산에 따라 달리 잡는다.
- ★ **`==` 는 넷 다 0** — 넷째 줄은 셋째 줄과 **같은 쌍**을 다른 식으로 만든 것이다.

### (4) ★★★ NaN 검사 네 가지 × 플래그 넷 — 옵션이 보장을 거둔다

**언제 쓰나** — 입력·계산 결과에서 NaN 을 걸러야 하는데 **빌드 옵션에 `-ffast-math`·`-Ofast` 가 있을 수 있을 때.**

```c
/* s52d.c */
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int by_bits(double x) {
    uint64_t u;
    memcpy(&u, &x, sizeof u);
    return (u & 0x7ff0000000000000u) == 0x7ff0000000000000u && (u & 0x000fffffffffffffu) != 0;
}

int main(int argc, char **argv) {
    double x = strtod(argc > 1 ? argv[1] : "nan", NULL);   /* 값은 실행할 때 온다 */
    /* 필드: isnan · x != x · fpclassify == FP_NAN · 비트 검사 */
    printf("%d\x1f%d\x1f%d\x1f%d\n", isnan(x) != 0, x != x, fpclassify(x) == FP_NAN, by_bits(x));
    return 0;
}
```

```text
===== NaN 검사 네 가지 — 컴파일러 2 × 최적화 2 × 플래그 4 (exit=0) =====
컴파일러 최적화 플래그                             | isnan  x!=x  fpclassify  비트검사 | 경고
gcc    -O0  (없음)                             | 1      1     1           1        | 0
gcc    -O0  -ffast-math                        | 0      0     0           1        | 0
gcc    -O0  -ffinite-math-only                 | 0      0     0           1        | 0
gcc    -O0  -ffast-math -fno-finite-math-only  | 1      1     1           1        | 0
gcc    -O2  (없음)                             | 1      1     1           1        | 0
gcc    -O2  -ffast-math                        | 0      0     0           1        | 0
gcc    -O2  -ffinite-math-only                 | 0      0     0           1        | 0
gcc    -O2  -ffast-math -fno-finite-math-only  | 1      1     1           1        | 0
clang  -O0  (없음)                             | 1      1     1           1        | 0
clang  -O0  -ffast-math                        | 1      1     1           1        | 1
clang  -O0  -ffinite-math-only                 | 1      1     1           1        | 1
clang  -O0  -ffast-math -fno-finite-math-only  | 1      1     1           1        | 0
clang  -O2  (없음)                             | 1      1     1           1        | 0
clang  -O2  -ffast-math                        | 0      0     0           1        | 1
clang  -O2  -ffinite-math-only                 | 0      0     0           1        | 1
clang  -O2  -ffast-math -fno-finite-math-only  | 1      1     1           1        | 0
(입력은 strtod("nan") — 실행할 때 온다 · 1 = NaN 이라고 답함)
NaN 을 못 본 칸 18 / 64
```

```text
===== clang -std=c17 -O2 -ffast-math -c s52d.c -o /dev/null (cc exit=0) =====
s52d.c:16:38: warning: use of NaN is undefined behavior due to the currently enabled floating-point options [-Wnan-infinity-disabled]
   16 |     printf("%d\x1f%d\x1f%d\x1f%d\n", isnan(x) != 0, x != x, fpclassify(x) == FP_NAN, by_bits(x));
      |                                      ^~~~~~~~
/usr/include/math.h:1011:20: note: expanded from macro 'isnan'
 1011 | #  define isnan(x) __builtin_isnan (x)
      |                    ^~~~~~~~~~~~~~~~~~~
1 warning generated.
```

```text
===== gcc -std=c17 -O2 -ffast-math -Wall -Wextra -c s52d.c -o /dev/null (cc exit=0) =====
```

- ★★★ **NaN 을 못 본 칸 18 / 64** — 전부 **`isnan` · `x != x` · `fpclassify` 세 검사**이고, **`-ffast-math` 또는 `-ffinite-math-only` 가 켜진 판**이다. **비트 검사는 64 칸 중 한 번도 놓치지 않았다.**
- ★★★ **gcc 는 `-O0` 에서도 못 본다 · clang 은 `-O0` 에서는 본다** — 같은 플래그에서 **최적화 수준이 답을 가른 것은 clang 뿐**이다. 「`-O0` 이니 안전하다」도 **컴파일러 하나의 관찰**이다.
- ★★ **범인은 `-ffinite-math-only`** — 그 하나만 켜도 같고, `-ffast-math -fno-finite-math-only` 는 **네 검사 다 산다.** `-ffast-math` 는 여러 플래그의 묶음이다([04번 형제](../04-floating-point-types-and-conversions/) 「더 들어가면」).
- ★★★ **clang 은 경고한다 · gcc 는 침묵한다** — clang `-Wnan-infinity-disabled`: 「**use of NaN is undefined behavior due to the currently enabled floating-point options**」. ★ **이 「UB」 는 C 표준의 UB 가 아니다** — 컴파일러가 **자기 옵션의 전제**를 그렇게 부른 것이다. gcc 는 `-Wall -Wextra` 에서 **0 줄 · `cc exit=0`**.
- ★★ **비트 검사가 살아남은 이유** — `memcpy` 로 `uint64_t` 에 옮긴 뒤의 비교는 **정수 연산**이라 부동소수 옵션의 전제가 닿지 않는다. ★ **이식성은 대가다** — IEC 60559 binary64 배치를 가정한다.

### (5) ★★ `check_isnan` 의 몸통 — 검사가 상수 0 이 된다

**언제 쓰나** — 4번 격자의 「0」이 **실행 중에 판정한 0 인지, 컴파일러가 박아 넣은 0 인지** 가를 때.

```c
/* s52e.c */
#include <math.h>

int check_isnan(double x) { return isnan(x); }
int check_self(double x) { return x != x; }
```

```text
===== check_isnan 의 몸통 — 컴파일러 2 × 플래그 2 (objdump -d -M intel) (exit=0) =====
--- gcc -O2
0000000000000000 <check_isnan>:
endbr64
xor    eax,eax
ucomisd xmm0,xmm0
setp   al
ret
xchg   ax,ax
--- gcc -O2 -ffast-math
0000000000000000 <check_isnan>:
endbr64
xor    eax,eax
ret
nop    WORD PTR [rax+rax*1+0x0]
--- clang -O2
0000000000000000 <check_isnan>:
xor    eax,eax
ucomisd xmm0,xmm0
setp   al
ret
nop    WORD PTR [rax+rax*1+0x0]
--- clang -O2 -ffast-math
0000000000000000 <check_isnan>:
xor    eax,eax
ret
data16 data16 data16 cs nop WORD PTR [rax+rax*1+0x0]
```

- ★★★ **기본 `-O2` 는 `ucomisd xmm0,xmm0` · `setp al`** — 자기와 비교해 **「순서 없음(unordered)」 플래그**를 읽는다. NaN 만 자기와 순서가 없다.
- ★★★ **`-ffast-math` 판은 `xor eax,eax` · `ret`** — **입력을 보지도 않고 0** 을 돌려준다. 두 컴파일러가 같다. 4번의 0 은 **판정이 아니라 상수**였다.

### (6) ★★★ `<time.h>` — 공용 칠판 · 정규화 · 0 기반 월

**언제 쓰나** — `time_t` 를 날짜로 바꾸거나, 날짜를 더하고 빼서 `time_t` 로 돌릴 때.

```c
/* s52f.c */
#include <stdio.h>
#include <time.h>

int main(void) {
    time_t t1 = 1700000000, t2 = 1800000000;

    struct tm *p1 = localtime(&t1);
    int year1 = p1->tm_year, hour1 = p1->tm_hour;
    struct tm *p2 = localtime(&t2);
    printf("[1] p1 == p2 : %d\n", p1 == p2);
    printf("[1] tm_year saved %d, p1->tm_year now %d\n", year1, p1->tm_year);

    p1 = localtime(&t1);
    struct tm *g = gmtime(&t1);
    printf("[2] p1 == g  : %d\n", p1 == g);
    printf("[2] tm_hour saved %d, p1->tm_hour now %d\n", hour1, p1->tm_hour);

    struct tm a = { .tm_year = 2024 - 1900, .tm_mon = 0, .tm_mday = 32, .tm_isdst = -1 };
    struct tm b = { .tm_year = 2024 - 1900, .tm_mon = 2, .tm_mday = 0, .tm_isdst = -1 };
    struct tm c = { .tm_year = 2024 - 1900, .tm_mon = 12, .tm_mday = 1, .tm_isdst = -1 };
    struct tm *all[] = { &a, &b, &c };
    for (int k = 0; k < 3; k++) {
        struct tm *p = all[k];
        int y = p->tm_year, m = p->tm_mon, d = p->tm_mday;
        time_t r = mktime(p);
        char s[32];
        strftime(s, sizeof s, "%Y-%m-%d %a", p);
        printf("[3] in {year %d, mon %d, mday %d} -> tm_year %d tm_mon %d tm_mday %d -> \"%s\"  (time_t %lld)\n",
               y, m, d, p->tm_year, p->tm_mon, p->tm_mday, s, (long long)r);
    }
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s52f.c -o x ; TZ=Asia/Seoul ./x (cc exit=0 · run exit=0) =====
[1] p1 == p2 : 1
[1] tm_year saved 123, p1->tm_year now 127
[2] p1 == g  : 1
[2] tm_hour saved 7, p1->tm_hour now 22
[3] in {year 124, mon 0, mday 32} -> tm_year 124 tm_mon 1 tm_mday 1 -> "2024-02-01 Thu"  (time_t 1706713200)
[3] in {year 124, mon 2, mday 0} -> tm_year 124 tm_mon 1 tm_mday 29 -> "2024-02-29 Thu"  (time_t 1709132400)
[3] in {year 124, mon 12, mday 1} -> tm_year 125 tm_mon 0 tm_mday 1 -> "2025-01-01 Wed"  (time_t 1735657200)
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s52f.c -o x ; TZ=UTC ./x (cc exit=0 · run exit=0) =====
[1] p1 == p2 : 1
[1] tm_year saved 123, p1->tm_year now 127
[2] p1 == g  : 1
[2] tm_hour saved 22, p1->tm_hour now 22
[3] in {year 124, mon 0, mday 32} -> tm_year 124 tm_mon 1 tm_mday 1 -> "2024-02-01 Thu"  (time_t 1706745600)
[3] in {year 124, mon 2, mday 0} -> tm_year 124 tm_mon 1 tm_mday 29 -> "2024-02-29 Thu"  (time_t 1709164800)
[3] in {year 124, mon 12, mday 1} -> tm_year 125 tm_mon 0 tm_mday 1 -> "2025-01-01 Wed"  (time_t 1735689600)
```

```text
   p1 = localtime(&t1)      ->  [ 정적 struct tm 하나 ]  <-  p2 = localtime(&t2)
                                  ^                            gmtime(&t1) 도 같은 칸
                                  |
                           p1, p2, g 가 전부 여기를 가리킨다
                           "저장해 둔 값" 이 아니면 마지막 호출의 답만 남는다
```

- ★★★ **`p1 == p2 : 1` · `p1 == g : 1`** — 세 호출이 **같은 객체**를 돌려준다. `p1->tm_year` 는 **127**(2027 — `t2` 의 해)로, `p1->tm_hour` 는 **22**(UTC 의 시)로 바뀌었다. **표준이 「덮어쓸 수 있다」고 허용한 것**이고, 이 glibc 는 **`localtime` 과 `gmtime` 이 한 칸을 같이 쓴다.**
- ★★ **`tm_year` 는 1900 기준 · `tm_mon` 은 0 기반** — 저장해 둔 `123` 은 2023 년, 입력의 `mon 0` 은 1 월이다.
- ★★★ **`mktime` 은 범위 밖 칸을 정규화한다** — 1 월 32 일 → **2 월 1 일**, 3 월 0 일 → **2 월 29 일**(2024 는 윤년), 13 번째 달(`mon 12`) → **이듬해 1 월 1 일**. 요일(`Thu`·`Wed`)도 **다시 계산해 채운다.**
- ★★ **`TZ=UTC` 로 바꾸면 `time_t` 만 9 시간(32400 초) 차이** — 같은 벽시계 날짜를 **다른 시간대의 자정**으로 읽었다. `[2]` 의 저장된 시도 `7` → `22` 로 바뀐다(`localtime` 이 곧 UTC).

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s52g.c -o /dev/null (cc exit=0) =====
s52g.c: In function 'main':
s52g.c:7:20: warning: implicit declaration of function 'localtime_r'; did you mean 'localtime'? [-Wimplicit-function-declaration]
    7 |     struct tm *p = localtime_r(&t, &mine);
      |                    ^~~~~~~~~~~
      |                    localtime
s52g.c:7:20: warning: initialization of 'struct tm *' from 'int' makes pointer from integer without a cast [-Wint-conversion]
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic -O0 s52g.c -o x ; TZ=Asia/Seoul ./x (cc exit=0 · run exit=0) =====
2023-11-15 07:13:20 KST  (p == &mine : 1)
```

- ★★ **`-std=c17 -pedantic` 에서 `localtime_r` 은 선언이 없다** — `implicit declaration` 경고 + **`int` 를 포인터로** 받는 경고(`cc exit=0` — 경고일 뿐 빌드된다). C17 에는 그 함수가 없다(★ POSIX 기능 매크로를 줘서 선언이 생기는지는 **던지지 않았다**).
- ★★ **`-std=c2x` 에서는 선언되고 제대로 돈다** — `2023-11-15 07:13:20 KST` · `p == &mine : 1`. C23 이 표준에 넣었기 때문이다.

## 문법 — 형태와 규칙

### 형태

```c
/* s52g.c */
#include <stdio.h>
#include <time.h>

int main(void) {
    time_t t = 1700000000;
    struct tm mine;
    struct tm *p = localtime_r(&t, &mine);
    char s[40];
    strftime(s, sizeof s, "%Y-%m-%d %H:%M:%S %Z", p);
    printf("%s  (p == &mine : %d)\n", s, p == &mine);
    return 0;
}
```

- `<ctype.h>` — **`isalpha((unsigned char)c)`**. `getchar()` 의 반환(`int` — 이미 `unsigned char` 값 또는 `EOF`)은 **캐스트 없이** 넘긴다.
- `<math.h>` — `isnan(x)` · 상대 오차 비교. **빌드 옵션**까지가 계약이다.
- `<time.h>` — `localtime_r`/`gmtime_r`(C23 · POSIX) · `mktime` 은 **`tm_isdst = -1`** 로 넘겨 DST 판정을 맡긴다.

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 도구 | 층 | 절 |
|---|---|---|---|
| `isalpha(c)`(`char c`, 음수) | 경고 0 · ASan/UBSan 0 | ★★★ UB(glibc 는 증상 없음) | (1)·(2) |
| `isalpha(c)`(`c == '\xFF'`) | 전부 0 | 적법 — **`EOF` 로 읽힌다** | (1) |
| `fabs(a - b) < DBL_EPSILON` | 경고 0 | 적법 — 뜻이 틀렸을 뿐 | (3) |
| `-ffast-math` + `isnan` | clang `-Wnan-infinity-disabled` · gcc 0 | ★★ 옵션의 전제 위반(컴파일러가 「UB」라 부름) | (4)·(5) |
| `localtime` 결과를 두 번 붙잡기 | 전부 0 | 적법 — 표준이 덮어쓰기를 허용 | (6) |
| `-std=c17` 에서 `localtime_r` | `implicit declaration` 경고 | ★★ 선언 없음 | (6) |

### 규칙 불릿

- ★★★ **`<ctype.h>` 에는 `unsigned char` 로 바꿔 넘긴다.** 부호 있는 `char` 는 **UB 이거나 `EOF` 로 읽힌다.**
- ★★ **바이트 분류는 로케일에 달렸다.** UTF-8 텍스트의 글자는 **`mbrtowc` + `iswalpha`** 로 본다(★ `mbrtowc` 는 이 편이 던지지 않았다).
- ★★★ **부동소수 비교는 상대 오차.** 문턱은 계산마다 정한다.
- ★★★ **NaN 이 올 수 있으면 `-ffast-math`·`-ffinite-math-only` 를 쓰지 않는다** — 쓸 거면 **`-fno-finite-math-only`** 를 붙이거나 비트로 본다.
- ★★ **`localtime`/`gmtime` 의 결과는 곧바로 복사하거나 `_r` 판을 쓴다.**

## 어디서 틀리나

### 1. ★★★ 「glibc 에서 `isalpha(c)` 가 잘 되니 캐스트는 필요 없다」

UB 칸이 멀쩡한 것은 **glibc 의 384 칸 표** 덕이다((1)의 헤더 주석). 256 칸 구현에서는 **표 밖을 읽는다**((2)). 그리고 glibc 에서도 **`0xFF` 는 `EOF` 로 읽혀 틀린다.**

### 2. ★★★ 「sanitizer 를 켰으니 음수 인자는 잡힌다」

**ASan+UBSan 둘 다 침묵**했다((1)).

### 3. ★★ 「`fabs(a - b) < DBL_EPSILON` 이 정석이다」

작은 수에서는 **다른 값을 같다**고, 큰 수에서는 **이웃 값을 다르다**고 한다((3)).

### 4. ★★★ 「`isnan` 은 표준 함수니 옵션과 무관하다」

`-ffinite-math-only` 하나로 **`xor eax,eax`** 가 된다((4)·(5)). **`x != x` 도 같이 죽는다.**

### 5. ★★ 「`-O0` 으로 디버그하면 NaN 검사가 산다」

**clang 만** 그랬다. gcc 는 `-O0` 에서도 0 이다((4)).

### 6. ★★★ 「`localtime` 두 번 불러 두 포인터를 들고 있으면 된다」

**같은 칸**이다((6)). `gmtime` 도 같은 칸이었다.

### 7. ★★ 「`tm_mon = 12` 는 오류다」

`mktime` 이 **이듬해 1 월**로 정규화한다((6)). 날짜 더하기는 그 성질을 쓴다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.

| 층 | 뜻 | 이 주제에서 | 근거 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | `<ctype.h>` 인자 범위 · `EOF` 허용 · C 로케일의 `isalpha` · `isnan` 의 뜻 · `tm_mon` 0 기반 · `tm_year` 1900 기준 · `mktime` 정규화 · 정적 객체 덮어쓰기 허용 · C23 `localtime_r` | 격자의 `C` 줄 · 시각 블록 · c2x 블록 |
| ★★ **조건부 표준** | `__STDC_IEC_559__` 일 때 | NaN 의 자기 불일치 · 상대 오차 계산의 근거가 되는 형식 | [04번 형제](../04-floating-point-types-and-conversions/) (5)절 |
| ★★ **구현(로케일·glibc·컴파일러)** | 이 판이 한 것 | `char` 의 부호 · 로케일 데이터(UTF-8 에서 `0xE9` 는 비알파) · **384 칸 표** · `localtime`/`gmtime` 한 칸 공유 · `-ffinite-math-only` 의 **상수 접기** · clang 만의 경고 · clang `-O0` 의 생존 | 격자 · 헤더 주석 · 어셈블리 · 경고 |
| **미명시** | 몇 가지 중 하나 | ★ 해당 없음 — 이 편의 칸은 전부 정의됐거나 UB 이거나 구현이 정한 것이다 | — |
| ★★★ **UB** | 아무 일이나 | ★★★ **`EOF` 가 아닌 음수를 `<ctype.h>` 에** | 격자의 `*` 칸 · 자작 표 ASan |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 이 편의 사례 | 무엇이 봤나 | 무엇이 못 봤나 |
|---|---|---|---|
| UB | `isalpha(-23)`(glibc) | **아무 도구도** — 표가 거기 있다 | ASan · UBSan · 경고 |
| UB | 256 칸 자작 표 | ASan `heap-buffer-overflow` | — |
| 정의됐지만 틀림 | `isalpha((char)0xFF)` = `EOF` | **아무 도구도** | 전부 |
| 옵션의 전제 | `-ffast-math` + NaN | clang `-Wnan-infinity-disabled` | gcc 전부 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓴다 | 안 쓴다 |
|---|---|---|
| 바이트 분류 | `isalpha((unsigned char)c)` | `isalpha(c)`(`char`) |
| UTF-8 글자 분류 | `mbrtowc` + `iswalpha` | 바이트마다 `isalpha` |
| 부동소수 같음 | 상대 오차(+필요하면 절대 하한) | `==` · `fabs(a-b) < DBL_EPSILON` |
| NaN 검사 | `isnan` + **`-ffast-math` 없는 빌드** | `-Ofast` 빌드의 `isnan`·`x != x` |
| 날짜 변환 | `localtime_r`/`gmtime_r` | `localtime` 결과를 오래 들고 있기 |
| 날짜 더하기 | `tm_mday += n; mktime(&tm);` | 달 길이를 손으로 계산 |

## 핵심 문장

1. ★★★ **`<ctype.h>` 는 `unsigned char` 값이나 `EOF` 만 받는다 — 부호 있는 `char` 는 UB 이거나 `EOF` 로 읽힌다.**
2. ★★★ **이 판에서 두 호출이 갈린 칸은 1 / 20 이고, 그것은 UB 칸이 아니라 `0xFF` = `EOF` 칸이었다 — UB 칸은 glibc 의 384 칸 표가 가렸다.**
3. ★★ **절대 오차 비교는 작은 수에서 느슨하고 큰 수에서 빡빡하다 — 상대 오차로 잰다.**
4. ★★★ **`-ffinite-math-only` 는 `isnan` 을 `xor eax,eax` 로 만든다 — 64 칸 중 18 칸이 NaN 을 못 봤고, 비트 검사만 살았다.**
5. ★★★ **`localtime` 과 `gmtime` 은 한 칸을 같이 쓴다 — 결과는 바로 복사하거나 `_r` 판을 쓴다.**

## 관련 자료

- [04번 형제 — 부동소수점 타입과 변환](../04-floating-point-types-and-conversions/) — ★★★ `0.1 + 0.2` · `DBL_EPSILON` · 큰 수 · gcc `-ffast-math` 에서 `isnan` 0 · `__STDC_IEC_559__`. 그쪽은 **값과 옵션의 사실**까지, 여기는 **컴파일러 대비 · 최적화 수준 · 검사 방법 · 어셈블리**부터.
- [02번 형제 — 기본 타입](../02-basic-types-sizes-and-fixed-width-integers/) — `char` 의 부호 · `-funsigned-char`. 그쪽이 「`isalpha` 에 `char` 를 넘기는 것이 같은 사고」라고 예고한 것을 여기서 쟀다.
- [20번 형제 — 널 종단 문자열](../20-null-terminated-strings-and-string-literals/) — 문자열이 바이트의 나열이라는 것.
- [JS 갈래 52번 — `switch` 레이블](../../../js/syntax/52-switch-labels-and-control-flow/) — ★ `case NaN:` 은 **절대 안 걸린다**(`NaN === NaN` 이 거짓 — 그쪽 실측). C 의 `x != x` 와 **같은 IEEE 754 규칙**이다.
- [JS 갈래 49번 — `Date` 와 Temporal](../../../js/syntax/49-date-and-temporal/) — ★ `Date` 도 **월이 0 부터이고 넘치면 넘긴다**(`new Date(2026, 1, 31)` → 3 월 3 일 — 그쪽 실측). C 의 `tm_mon` · `mktime` 과 같은 설계다. Temporal 은 1 기반이다.
- [Python 갈래 50번 — `decimal`·float 정밀도](../../../python/syntax/50-decimal-float-precision-and-round/) — `0.1 + 0.2` 가 **바로 옆 눈금(1 ulp)** 이라는 것을 세 창으로 봤다.
- [Go 갈래 48번 — `time`](../../../go/syntax/48-time-monotonic-clock-duration-timer-and-ticker/) — Go 의 시각 API. ★ 그쪽의 주제는 **단조 시계와 벽시계**이고, 「공용 칠판」 같은 정적 칸 문제는 **이 편이 Go 쪽에서 재지 않았다.**

## 용어 풀이

> **`EOF`** — `<stdio.h>` 의 음수 매크로(이 판에서 −1). `<ctype.h>` 함수가 **유일하게 받아 주는 음수**다.

> **로케일(locale)** — 문자 분류 · 숫자 형식 등을 정하는 환경. `setlocale(LC_ALL, "…")` 로 고른다. 없는 이름이면 `NULL` 을 돌려주고 **바뀌지 않는다.**

> **`localedef`** — 로케일 소스와 문자 집합표로 로케일 데이터를 만드는 도구. `LOCPATH` 로 그 디렉토리를 가리키게 했다.

> **상대 오차(relative error)** — 차이를 **값의 크기로 나눈** 오차. 눈금 간격이 값에 비례하니 비교도 비례로 한다.

> **`-ffinite-math-only`** — 「NaN 과 무한대는 오지 않는다」고 가정해 최적화하라는 gcc·clang 옵션. `-ffast-math` 에 들어 있다.

> **`ucomisd`** — x86-64 의 부동소수 비교 명령. NaN 이 끼면 **패리티 플래그(unordered)** 를 세운다 — `setp` 가 그것을 읽는다.

> **`mktime` 정규화** — 범위 밖의 `tm` 칸(32 일 · 13 번째 달)을 **올바른 날짜로 넘겨** 채우는 것.

## 더 들어가면

- ★★ **`mbrtowc` + `iswalpha`** — UTF-8 바이트열을 글자로 읽어 분류하는 정석. ★ 이 편은 **`iswalpha` 에 코드 포인트를 직접 넣었을 뿐** 다중 바이트 해석은 던지지 않았다.
- ★ **`timegm`** — `mktime` 의 UTC 판(표준 아님 · glibc·BSD 확장). **던지지 않았다.**
- ★ **`fenv.h` 와 `FE_INVALID`** — NaN 이 **생긴 순간**을 잡는 창. **던지지 않았다.**

## 실행 환경

**기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) — `<ctype.h>` 머리의 「**the argument is an int, the value of which shall be representable as an unsigned char or shall equal the value of the macro EOF. If the argument has any other value, the behavior is undefined.**」·「**affected by the current locale**」, `isalpha` 의 「**In the "C" locale, isalpha returns true only for the characters for which isupper or islower is true**」, `isnan` 의 「**returns a nonzero value if and only if its argument has a NaN value**」, `struct tm` 의 「**tm_mon — months since January — [0, 11]**」·「**tm_year — years since 1900**」, `mktime` 의 「**the original values of the other components are not restricted to the ranges indicated**」, `gmtime`·`localtime` 의 「**may overwrite the information returned from any previous call to one of these functions that uses the same object**」, 부록의 바뀐 점 목록 「**integration of functions: gmtime_r, localtime_r**」를 **본문에서 직접 찾아 읽었다**) · glibc `/usr/include/ctype.h` 의 주석(이 머신)
★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **분류 결과 · sanitizer · 어셈블리 · 시각은 전부 실행으로** 접지했다.
**실행 검증** — 이 문서의 모든 출력·진단은 「이 판」 절의 판에서 실제로 돌려 **파일로 캡처한 것**이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`, 캡처 셸은 `LC_ALL=C`.\
★★ **현재 시각은 한 번도 찍지 않았다** — `time_t` 는 전부 고정값(`1700000000` · `1800000000`)이고, 시간대는 **명령에 `TZ=` 로 적었다.**\
★★ **블록은 전부 캡처 파일에서 조립했다.** 이 편의 **그림 3 · 덤프(캡처 블록) 19**.
**버전** — `<ctype.h>`·`<math.h>`·`<time.h>` 의 이 편 함수는 **C89 부터**(`isnan`·`fpclassify` 는 **C99**, `iswalpha` 는 **C95**). ★★ **C23** 이 `localtime_r`·`gmtime_r` 를 표준에 넣었다 — 이 판의 glibc 는 `-std=c2x` 에서 **헤더가 선언해 준다**((6)).
★★★ **경계** — **`0.1 + 0.2` · `DBL_EPSILON` · 큰 수에서 1 이 사라지는 것 · `-ffast-math` 로 `isnan` 이 0 이 되는 것 · `__STDC_IEC_559__` 가 사라지는 것**은 [04번 형제](../04-floating-point-types-and-conversions/) (2)·(3)·(5)절이 정본이다(이 편은 **다시 재지 않고** 인용하고, **컴파일러 대비 · 최적화 수준 · 검사 방법 · 어셈블리** 칸만 더한다). **`char` 의 부호**는 [02번 형제](../02-basic-types-sizes-and-fixed-width-integers/), **문자열이 바이트의 나열이라는 것**은 [20번 형제](../20-null-terminated-strings-and-string-literals/)가 정본이다.
선행 — [04번 형제](../04-floating-point-types-and-conversions/) · [20번 형제](../20-null-terminated-strings-and-string-literals/).
