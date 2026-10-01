# c/syntax/46 — `errno` 와 C 의 오류 반환 관례: 「**실패는 반환값이 말하고 `errno` 는 그 이유만 말한다 — 반환값을 건너뛰고 `errno` 부터 보면 성공한 호출도 실패로 읽힌다**」 — 질문

## 이 파일을 푸는 법

- ★★ **예측형 다섯 문항(1\~5)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「무엇이 실제로 실패했나」와 「각 판정법이 무엇이라고 했나」를 따로** 적어라 — 둘이 다른 칸이 답이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 `errno` 값은 누가 언제 쓴 것인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 호출 일곱 × 호출 전 `errno` (예측) ★★★ 이 주제의 축

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

`TZ=s46/none ./x <호출> <0|1>` 로 돌린다(`gcc -O0` · `-lm`). 둘째 인자가 `1` 이면 호출 직전에 `errno = 0` 을 한다. `s46/none` 이라는 시간대 파일은 없다.

- ★★★ 호출 1\~7 × 두 판(14 줄)에서 **반환 · `errno`** 는 각각 무엇인가?
- ★★★ 「`errno != 0` 이면 실패」로 판정한 쪽과 「반환이 실패 모양일 때만 실패」로 판정한 쪽은 **각각 몇 줄에서 틀리는가**? 어느 줄인가?
- ★★ 어느 줄이 「**`errno = 0` 을 해야만** 맞는」 줄인가?

### 2. 빌드를 바꾸면 (예측) ★★★

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

`s46a` 의 호출 4 · 5(둘째 인자 `1`), `s46c`, `s46m` 을 `gcc -O0` · `gcc -O2` · `clang -O0` · `clang -O2` · `gcc -O2 -fno-math-errno` · `clang -O2 -fno-math-errno` 로 만든다.

- ★★★ 18 칸의 **반환/`errno`** 와 `math_errhandling` 값은?
- ★★ **실패했는데 `errno` 가 0** 인 칸은 몇 칸이고, 어느 빌드 · 어느 소스인가?

### 3. `perror` 와 `strerror` 의 문구 (예측) ★★

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

- ★★ `LC_ALL=C ./x` · `LC_ALL=ko_KR.UTF-8 ./x` · `LC_ALL=ko_KR.UTF-8 ./x setlocale` · `LC_ALL=C ./x setlocale` 는 각각 표준 오류에 무엇을 찍는가?
- ★ `int e = errno;` 한 줄을 `perror` **앞에** 둔 이유는?

### 4. 두 스레드의 `errno` (예측) ★★

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

- ★★ 세 줄은 각각 무엇을 찍는가?

### 5. `errno` 는 무엇으로 펼쳐지나 (예측) ★★

```c
/* s46e.c */
#include <errno.h>

int read_errno(void) { return errno; }
```

- ★★ `gcc -E -P` 로 펼치면 `return errno;` 는 무엇이 되는가?
- ★ `nm s46e.o` 에 `errno` 라는 이름이 보이는가? 무엇이 보이는가?

### 6. 반환값을 먼저 보는 이유 (왜) ★★★

- ★★★ 표준은 **성공한 호출의 `errno`** 에 대해 무엇이라고 적는가?
- ★★ 1번에서 **`errno = 0` 을 했는데도** `errno` 로 판정한 쪽이 틀린 줄은 무엇이 그렇게 만들었나?

### 7. `strtol` 은 왜 예외인가 (왜) ★★

- ★★ `strtol` 의 반환값만으로 넘침을 가를 수 없는 이유는?
- ★★ 그러면 `errno = 0` 은 **언제** 해야 하고, **왜 그 자리**인가?

### 8. clang `-O2` 의 `errno` `0` (경계) ★★★

- ★★★ 2번의 그 칸은 **컴파일러가 무엇을 가정해서** 나왔나? 어셈블리의 **어느 한 줄**이 그것을 보이는가?
- ★★ 그 가정은 **C 표준 위반**인가, **POSIX 와의 약속 위반**인가? 무엇을 주면 사라지는가?

### 9. `math_errhandling` 과 `-fno-math-errno` (경계) ★★

- ★★ `math_errhandling` 이 `2` 인 빌드에서 `sqrt(-1.0)` 의 실패는 **어디로** 알려지는가?
- ★ `-fno-math-errno` 는 **수학 함수가 아닌 호출**의 `errno` 도 건드렸는가?

### 10. Go 의 다중 반환과 견주면 (연결) ★★

- ★★ Go 의 `(값, error)` 는 C 의 「반환값 + `errno`」 관례에서 **무엇을 고쳤나**? 1번의 어느 줄이 Go 에서는 원리상 안 생기는가?

### 11. 다섯 층과 경계 (연결) ★★

- 이 주제에서 **표준 / 구현 정의 / POSIX · glibc / 컴파일러 구현** 칸에 각각 무엇이 들어가는가?
- ★ **`strtol` 로 파싱하는 법 전체** · **`strerror` 결과의 소유** 는 어디가 정본인가?

## 실행 환경

**환경** — gcc 13.3.0 · clang 18.1.3 · glibc 2.39 · x86-64 Linux. `strerror` 문구는 **`LC_ALL=C`** 로 고정했다(3번은 로케일을 일부러 바꾼다).

★★★ **본체 창은 둘째 창 — 실행 결과의 판정 격자**다. 1번은 **줄마다 「반환 · `errno` · 두 판정법이 맞았나」** 를 적어야 답이다.
★★ **`malloc` 실패의 반환·`errno` 격자**(탐침 7 × 빌드 8)는 [37번 형제](../37-malloc-calloc-realloc-free/)가 이미 쟀다 — 여기는 그 격자의 **clang `-O2` 칸**을 원인까지 판다.
선행 — [34번 형제](../34-function-declarations-definitions-and-prototypes/) · [37번 형제](../37-malloc-calloc-realloc-free/).

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
