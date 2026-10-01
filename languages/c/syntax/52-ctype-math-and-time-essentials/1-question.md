# c/syntax/52 — `<ctype.h>` · `<math.h>` · `<time.h>` 핵심: 「**`isalpha` 는 `unsigned char` 의 값을 기다리고, NaN 검사는 옵션 하나에 지워지며, `localtime` 은 하나뿐인 칸을 돌려준다**」 — 질문

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「UB 인 칸」과 「정의된 칸」을 따로** 적어라 — 같은 숫자여도 뜻이 다르다.
- ★★ **「표준이 약속한 것」과 「이 판의 glibc·컴파일러가 한 것」을 갈라** 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 값은 누구의 범위 안에 있어야 하나**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 로케일 다섯 × `char` 부호 둘 × 바이트 둘 — ctype 격자 (예측) ★★★ 이 주제의 축

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

격자는 로케일 `C` · `C.UTF-8` · `ko_KR.UTF-8` · `en_US.UTF-8` · `en_US.ISO-8859-1`(`localedef` 로 스크래치 디렉토리에 만들어 `LOCPATH` 로 준다) × 기본 빌드 · `-funsigned-char` 빌드로 돌린다.

- ★★★ 기본 빌드에서 `(int)c` 는 두 바이트에 대해 각각 얼마인가? 그중 **`isalpha(c)` 가 UB 인 것**과 **UB 가 아닌 것**은?
- ★★★ 스무 칸(10 줄 × 바이트 2)에서 `isalpha(c)` 와 `isalpha((unsigned char)c)` 가 **다른 답을 내는 칸**은 어디인가?
- ★★ `iswalpha` 열이 로케일에 따라 어떻게 바뀌는가? `setlocale` 이 `NULL` 인 줄은?
- ★ ASan+UBSan 으로 빌드해 Latin-1 줄을 돌리면 무엇이 나오는가?

### 2. 256 칸짜리 표를 직접 만들면 (예측) ★★

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

- ★★ gcc·clang ASan 으로 돌리면 몇 번째 줄까지 찍히고, 리포트는 무엇을 말하는가? 몇 바이트 **앞**인가?
- ★ 1번의 glibc `isalpha(c)` 와 이 결과를 나란히 두면 무엇을 알 수 있는가?

### 3. 네 쌍의 「같은가」 (예측) ★★

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

- ★★ 네 줄에서 `==` · `abs` · `rel` 은 각각 0 인가 1 인가?
- ★★ `abs` 가 **틀린 방향**으로 답한 줄이 있다면 어느 줄이고, 양쪽 방향 모두 있는가?

### 4. NaN 검사 네 가지 × 플래그 넷 (예측) ★★★

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

격자는 `./x nan` 을 gcc/clang × `-O0`/`-O2` × 플래그 넷(없음 · `-ffast-math` · `-ffinite-math-only` · `-ffast-math -fno-finite-math-only`)에서 돌린다.

- ★★★ 64 칸 중 NaN 을 **못 본** 칸은 몇 개이고, 어느 검사 · 어느 판에 몰리는가?
- ★★ **한 번도 놓치지 않은** 검사가 있다면 무엇인가?
- ★★ 경고를 내는 컴파일러는? 그 경고는 무엇이라고 말하는가?

### 5. 두 시각 · 두 함수 · 세 `mktime` (예측) ★★★

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

`TZ=Asia/Seoul ./x` 로 돌린다.

- ★★★ `[1]` 두 줄 — `p1 == p2` 는? 저장해 둔 `tm_year` 와 **지금 `p1->tm_year`** 는?
- ★★★ `[2]` 두 줄 — `gmtime` 을 부른 뒤 `p1->tm_hour` 는 무엇이 되는가?
- ★★ `[3]` 세 줄 — `mday 32` · `mday 0` · `mon 12` 는 각각 어느 날짜로 정규화되는가?
- ★ `TZ=UTC` 로 돌리면 어느 칸이 바뀌는가?

### 6. `localtime_r` 과 `-std` (예측) ★★

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

- ★★ `-std=c17 -pedantic` 으로 컴파일하면 무엇이 나오는가? `cc exit` 는?
- ★★ `-std=c2x` 로 컴파일해 `TZ=Asia/Seoul` 로 돌리면?

### 7. `-ffast-math` 판의 `check_isnan` 몸통 (왜) ★★

- ★★ `int check_isnan(double x) { return isnan(x); }` 를 `-O2` 와 `-O2 -ffast-math` 로 컴파일하면 몸통의 명령은 달라지는가? 4번 격자와 이어서 설명하면?
- ★ 그 판에서 NaN 을 넘기면 **누구의 약속**이 깨진 것인가 — C 표준인가, 컴파일러 옵션의 전제인가?

### 8. `<ctype.h>` 인자의 범위와 glibc 의 표 (경계) ★★★

- ★★★ 표준은 `<ctype.h>` 함수의 인자에 무엇을 요구하는가? 1번의 `*` 칸 값을 glibc 의 표 모양으로 설명하면?
- ★★ `EOF` 의 값과 1번 격자의 `(int)c` 열을 나란히 두면 무엇이 보이는가?

### 9. 로케일이 없을 때 (경계) ★

- ★ `en_US.UTF-8` 줄에서 `setlocale` 이 `NULL` 이면 그 줄은 **어느 로케일로** 돌았는가? 격자를 읽을 때 그 줄을 어떻게 다뤄야 하는가?

### 10. 04 · 02번 형제와 이어서 (연결) ★★

- [04번 형제](../04-floating-point-types-and-conversions/)는 `-ffast-math` 에서 **무엇을** 이미 쟀는가? 이 편의 4번이 더한 칸은?
- ★ [02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)의 `-funsigned-char` 실측과 1번 격자는 어떻게 이어지는가?

### 11. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / 구현(로케일·glibc·컴파일러) / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- ★★★ 이 편의 **네 번째 창**은 무엇이고, 그 창이 **못 보는 것**은?

### 12. 다른 갈래와 (연결) ★

- ★ JS 는 `case NaN:` 에서 어떻게 되는가([JS 갈래 52번](../../../js/syntax/52-switch-labels-and-control-flow/))? C 의 `x != x` 와 같은 뿌리인가?
- ★ JS `Date` 의 월([JS 갈래 49번](../../../js/syntax/49-date-and-temporal/))과 C 의 `tm_mon` 은 같은가? 넘치는 날짜는?

## 실행 환경

**환경** — gcc 13.3.0 · clang 18.1.3 · glibc 2.39 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic` · 캡처 셸 `LC_ALL=C` · 시각은 **고정 `time_t`** 와 **`TZ=` 지정**으로만 찍었다.

★★★ **본체 창은 ctype 격자** — 1번은 **로케일 × `char` 부호마다 두 호출이 갈리는지**를 적어야 답이다.
★★ **`0.1 + 0.2` · `DBL_EPSILON` · `-ffast-math` 의 기본 사실은 묻지 않는다** — [04번 형제](../04-floating-point-types-and-conversions/)가 정본이다.
선행 — [04번 형제](../04-floating-point-types-and-conversions/) · [20번 형제](../20-null-terminated-strings-and-string-literals/).

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
