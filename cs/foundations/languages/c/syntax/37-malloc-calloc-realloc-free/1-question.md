# c/syntax/37 — `malloc`/`calloc`/`realloc`/`free`: 「**실패는 `NULL` 하나로 온다 — 그 `NULL` 을 받는 자리가 원본을 지키느냐를 가른다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · gcc-12 12.4.0 · clang 18.1.3 · glibc 2.39 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **언제 `NULL` 이 오고 그때 무엇이 약속되나**(크기 0 · 거대한 크기 · 곱셈 넘침 · `errno`) ② **`realloc` 실패에서 원본을 지키는 호출 형태**(와 그것을 보는 도구)
> ③ **해제 쪽 규칙**(`free(NULL)` · double free · 해제 후 사용 · C23).
> ★★★ **본체 창은 실패 격자** — 1번은 **칸마다 「널인가 / `errno`」** 를 적어야 답이다.
> ★★ **할당자 내부(빈 목록 · 분할 · 병합)는 묻지 않는다** — 그것은 [`data-structure/35-allocator/`](../../../../../data-structure/35-allocator/)가 정본이다.
> 선행 — [28번 형제](../28-choosing-among-four-storage-durations/).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **1·3번은 「보통 빌드」와 「ASan 빌드」를 따로** 적어라 — 같은 소스가 **다른 경로**를 탄다.
- ★★ **「표준이 약속한 것」과 「이 판의 glibc 가 한 것」을 갈라** 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 `NULL` 을 받은 뒤 원본을 가리키는 변수가 남아 있나**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 탐침 일곱 × 빌드 여덟 — 실패 격자 (예측) ★★★ 이 주제의 축

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

격자는 `./x 1` \~ `./x 7` 을 **gcc/clang × `-O0`/`-O2`** 네 빌드와 **ASan 빌드 둘**(기본값 · `ASAN_OPTIONS=allocator_may_return_null=1`)에서 돌린다. `n = SIZE_MAX/2+2`.

- ★★★ 크기 0 인 세 호출(`malloc(0)` · `calloc(0, 8)` · `realloc(p, 0)`)은 각각 널을 돌려주는가?
- ★★★ `calloc(n, 2)` 와 `malloc(n * 2)` 는 **같은 곱**이다. 둘의 결과는 같은가?
- ★★★ `malloc(SIZE_MAX)` 줄에서 **여덟 빌드가 모두 같은가**? 갈린다면 어느 빌드가, 무엇으로?
- ★★ `errno` 가 `ENOMEM` 이 되는 것은 **누구의 약속**인가?

### 2. 크기가 상수인 `malloc(SIZE_MAX)` (예측) ★★

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

- ★★ gcc 와 clang 을 `-O0`·`-O1`·`-O2` 로 돌리면 두 줄에 각각 무엇이 찍히는가?
- ★★ 여섯 빌드 중 경고를 내는 것은?
- ★ 1번 탐침이 크기를 `volatile` 로 둔 이유를 이 결과로 설명하면?

### 3. 같은 실패, 두 호출 형태 (예측) ★★★

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

- ★★★ 두 파일을 **보통 빌드**로 돌리면 각각 무엇이 찍히고 `exit` 는?
- ★★★ **ASan 기본값**으로 돌리면? 두 파일이 **구분되는가**?
- ★★★ `ASAN_OPTIONS=allocator_may_return_null=1` 을 주면? LeakSanitizer 가 **몇 바이트**를, **어느 줄**에서 잡은 블록이라고 말하는가?
- ★ 정적 도구(gcc `-fanalyzer` 두 판 · `clang --analyze`) 중 `s37c.c` 의 누수를 말하는 것은?

### 4. `setrlimit` 으로 실패시키기 (예측) ★★

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

- ★★ 보통 빌드에서 `realloc` 은 실패하는가? 누수를 말해 주는 것이 있는가?
- ★★★ ASan(`allocator_may_return_null=1`) 판에서 **종료 시 누수 검사**는 무엇을 출력하는가?
- ★ 3번이 이 방법 대신 **거대한 크기**를 쓴 이유는?

### 5. `free(NULL)` 과 두 번째 `free(p)` (예측) ★★

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

- ★★ gcc 는 컴파일 때 무엇이라고 말하는가? `cc exit` 는?
- ★★★ 보통 빌드로 돌리면 **몇 줄**이 찍히고 `run exit` 는? 표준 오류에는 무엇이 나오는가?
- ★★ ASan 리포트의 첫 줄 종류는? 스택이 **몇 개** 붙는가?

### 6. `realloc(p, 0)` 과 C23 (예측) ★★

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

- ★★ 이 판에서 실행하면 무엇이 찍히는가?
- ★★★ gcc-12 · gcc · clang 을 `-std=c17` 과 `-std=c2x` 로 컴파일하고 UBSan 으로 돌리면 **판에 따라 갈리는 줄**이 있는가?
- ★ `-Walloc-zero` 는 기본 경고 묶음에 들어 있는가?

### 7. `calloc(n, size)` 와 `malloc(n * size)` 의 인자 모양 (왜) ★★

- ★★ 두 호출이 곱의 넘침을 대하는 방식이 다르다면 그 **구조적 이유**는?
- ★ `malloc` 으로 같은 안전을 얻으려면 곱하기 **전에** 무엇을 검사하는가?

### 8. 해제 후 읽기 — ASan 은 무엇을 말하나 (경계) ★★

- ★★ 해제한 `p` 에서 `p[0]` 을 읽으면 ASan 은 어떤 종류를, **몇 바이트 읽기**로 보고하는가?
- ★ 그 소스의 **보통 빌드 실행 결과**를 싣지 않은 이유는?

### 9. `realloc` 은 주소를 바꾸는가 (경계) ★★

- ★★ 16 번 늘렸을 때 이 판에서 주소가 바뀐 횟수는? 그것이 20 판 동안 흔들렸는가?
- ★★★ 그 결과로 「`realloc` 뒤에도 옛 포인터를 써도 된다 / 안 된다」를 판정할 수 있는가? 표준은 무엇이라고 하는가?

### 10. `malloc` 불확정 · `calloc` 0 — 형제와 이어서 (연결) ★★

- ★★ [30번 형제](../30-initialization-rules-and-indeterminate-values/)는 이 차이를 **어떤 방법으로** 쟀는가? 이 편이 더한 한 칸은?
- ★ `calloc` 이 「모든 비트 0」이라는 것이 **널 포인터 · `0.0`** 까지 보장하는가(28·30번 형제가 남긴 자리)?

### 11. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- 이 주제에서 **표준 / 구현 정의 / 컴파일러 구현 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- ★★★ `p = realloc(p, n)` 의 누수는 **UB 인가**? 아니라면 왜 도구가 기본값으로는 못 보는가?
- ★★ 이 편의 **네 번째 창**은 무엇이고, 그 창이 **못 보는 것**은?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

- **빈 목록 · 분할 · 병합**은 어느 폴더의 어느 절이 정본인가?
- **누가 해제하는가를 시그니처로 말하기**는 목록의 몇 번 주제인가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
