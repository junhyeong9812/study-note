# c/syntax/51 — `<stdlib.h>` 변환 · `qsort` · `bsearch`: 「**`atoi` 에는 실패를 말할 자리가 없다 — `strtol` 의 `endptr` 와 `errno` 가 그 자리다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · glibc 2.39 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **문자열 → 정수에서 「실패」를 가르는 법**(`atoi` 대 `strtol` + `endptr` + `errno`) ② **`qsort` 비교자가 지켜야 하는 것**(부호 · 서명 · 일관성)
> ③ **`qsort`·`bsearch` 가 약속하지 않는 것**(안정성 · 정렬 안 된 입력).
> ★★★ **본체 창은 변환 격자** — 1번은 **입력마다 「`strtol` 이 무엇을 알렸나」** 를 적어야 답이다.
> ★★ **정렬·탐색 알고리즘 자체는 묻지 않는다** — [`algorithm/03-quick-sort/`](../../../../cs/algorithm/03-quick-sort/) · [`algorithm/06-binary-search/`](../../../../cs/algorithm/06-binary-search/)가 정본이다.
> 선행 — [35번 형제](../35-function-pointers-and-callback-tables/) · [목록의 **46번 주제**](../46-errno-and-error-return-conventions/).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **1번은 `atoi` 칸과 `strtol` 칸을 따로** 적어라 — **값을 적으면 안 되는 칸**이 있다.
- ★★ **「표준이 약속한 것」과 「이 판의 glibc 가 한 것」을 갈라** 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 호출이 실패했다는 것을 호출자가 알 수 있나**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 입력 열 × 두 함수 — 변환 격자 (예측) ★★★ 이 주제의 축

```c
/* s51a.c */
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *ename(int e) { return e == 0 ? "0" : e == ERANGE ? "ERANGE" : e == EINVAL ? "EINVAL" : "other"; }

int main(int argc, char **argv) {
    if (argc < 3) return 2;
    const char *s = argv[1];
    int base = atoi(argv[2]);
    char *end;
    errno = 0;
    long v = strtol(s, &end, base);
    int e = errno;
    /* 필드: strtol 값 · 소비한 글자 수 · errno · 남은 글자 수 */
    printf("%ld\x1f%d\x1f%s\x1f%zu", v, (int)(end - s), ename(e), strlen(end));
    if (argc > 3) printf("\x1f%d", atoi(s));
    printf("\n");
    return 0;
}
```

격자는 `./x "<입력>" 10 atoi` 를 입력 열 개에 돌린다 — `"42"` · `"0"` · `"42abc"` · `"abc"` · `""` · `"  42"` · `"42 "` · `"99999999999999999999"` · `"-0x1A"` · `"08"`.

- ★★★ 입력마다 `atoi` 가 돌려주는 값은? **값을 적으면 안 되는 입력**이 있다면 어느 것이고 왜인가?
- ★★★ 입력마다 `strtol` 의 값 · 소비한 글자 수 · `errno` · 남은 글자 수는?
- ★★★ `strtol` 이 「성공이 아니다」라고 알리는 입력은 몇 개이고, 그 입력들을 `atoi` 만으로 **성공과 가를 수 있는가**?

### 2. 진법 접두와 `-std` (예측) ★★

같은 `s51a.c` 를 `-std=c17` 과 `-std=c2x` 로 컴파일해 `./x "<입력>" <base>` 를 돌린다. 입력은 `"0b101"` · `"0B11"` · `"0x1A"` · `"08"` · `"010"`, base 는 `0` · `2` · `8` · `16`.

- ★★ 스무 칸 중 **두 판이 다른 값을 내는 칸**이 있는가? 있다면 어느 입력 · 어느 base 인가?
- ★★ `"0b101"` 을 base 16 으로 읽으면? `"08"` 을 base 0 으로 읽으면 **소비한 글자 수**는?
- ★ 판이 갈린다면, 링크된 심볼에서 그것이 보이는가?

### 3. 비교자 넷 (예측) ★★★

```c
/* s51c.c */
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

static int by_wide(const void *pa, const void *pb) {
    int a = *(const int *)pa, b = *(const int *)pb;
    long long d = (long long)a - b;
    return d;
}

static int by_diff(const void *pa, const void *pb) {
    double a = *(const double *)pa, b = *(const double *)pb;
    return a - b;
}

static int by_rel_i(const void *pa, const void *pb) {
    int a = *(const int *)pa, b = *(const int *)pb;
    return (a > b) - (a < b);
}

static int by_rel_d(const void *pa, const void *pb) {
    double a = *(const double *)pa, b = *(const double *)pb;
    return (a > b) - (a < b);
}

int main(void) {
    int v[] = { 3, INT_MAX, -1, 0, INT_MIN + 1, 2 }, w[6];
    double x[] = { 0.5, 0.25, 0.75, 0.125 }, y[4];
    size_t n = sizeof v / sizeof v[0];
    for (size_t k = 0; k < n; k++) w[k] = v[k];
    for (size_t k = 0; k < 4; k++) y[k] = x[k];
    qsort(v, n, sizeof v[0], by_wide);
    qsort(w, n, sizeof w[0], by_rel_i);
    qsort(x, 4, sizeof x[0], by_diff);
    qsort(y, 4, sizeof y[0], by_rel_d);
    printf("by_wide  :"); for (size_t k = 0; k < n; k++) printf(" %d", v[k]); printf("\n");
    printf("by_rel_i :"); for (size_t k = 0; k < n; k++) printf(" %d", w[k]); printf("\n");
    printf("by_diff  :"); for (size_t k = 0; k < 4; k++) printf(" %g", x[k]); printf("\n");
    printf("by_rel_d :"); for (size_t k = 0; k < 4; k++) printf(" %g", y[k]); printf("\n");
    return 0;
}
```

- ★★★ 네 줄은 각각 무엇을 찍는가? 정렬이 **맞는** 줄은?
- ★★★ `gcc -fsanitize=undefined` · `clang -fsanitize=undefined` · `clang -fsanitize=undefined,implicit-conversion` 세 벌에서 `runtime error` 는 각각 몇 줄인가? 말한다면 **어느 비교자의 어느 줄**인가?
- ★ `-Wall -Wextra -pedantic` 은 경고를 내는가?

### 4. 서명이 다른 비교자를 캐스트해 넘기기 (예측) ★★★

```c
/* s51d.c */
#include <stdio.h>
#include <stdlib.h>

typedef int (*Cmp)(const void *, const void *);

static int by_int(const int *a, const int *b) { return (*a > *b) - (*a < *b); }
static int by_two(int a, int b) { return (a > b) - (a < b); }

int main(void) {
    int v[] = { 3, 1, 2 };
    qsort(v, 3, sizeof v[0], (Cmp)by_int);
    printf("%d %d %d\n", v[0], v[1], v[2]);
    Cmp other = (Cmp)by_two;
    (void)other;
    return 0;
}
```

- ★★★ gcc `-Wall -Wextra` 는 두 캐스트 중 **어느 것**에 경고를 내는가?
- ★★ clang 은 `-Wall -Wextra` 에서? `-Wcast-function-type` 을 **따로** 주면?
- ★★ `clang -fsanitize=function` 으로 돌리면 `qsort` 안의 호출을 잡는가?

### 5. 같은 비교자 · 같은 입력 · 주소 공간 한도 (예측) ★★

```c
/* s51e.c */
#include <stdio.h>
#include <stdlib.h>

struct R { int key; int seq; };

static int by_key(const void *pa, const void *pb) {
    const struct R *a = pa, *b = pb;
    return (a->key > b->key) - (a->key < b->key);
}

int main(int argc, char **argv) {
    size_t n = argc > 1 ? strtoul(argv[1], NULL, 10) : 10;
    struct R *v = malloc(n * sizeof *v);
    if (!v) { printf("n=%zu malloc NULL\n", n); return 1; }
    unsigned s = 12345;
    for (size_t i = 0; i < n; i++) {
        s = s * 1103515245u + 12345u;
        v[i].key = (int)((s >> 16) % 4);
        v[i].seq = (int)i;
    }
    qsort(v, n, sizeof v[0], by_key);
    size_t order = 0, inv = 0;
    for (size_t i = 1; i < n; i++) {
        if (v[i - 1].key > v[i].key) order++;
        if (v[i - 1].key == v[i].key && v[i - 1].seq > v[i].seq) inv++;
    }
    printf("n=%zu  key order breaks=%zu  seq inversions among equal keys=%zu\n", n, order, inv);
    free(v);
    return 0;
}
```

- ★★ `n` 을 10 · 1000 · 1000000 으로 돌리면 `seq inversions among equal keys` 는 각각?
- ★★★ 같은 셋을 **`ulimit -v 15000`** 아래에서 돌리면? 어느 줄이 바뀌는가?
- ★ 그 결과로 「glibc `qsort` 는 안정 정렬이다」를 말할 수 있는가?

### 6. 정렬 안 된 배열에 `bsearch` (예측) ★★

```c
/* s51f.c */
#include <stdio.h>
#include <stdlib.h>

static int by_int(const void *pa, const void *pb) {
    int a = *(const int *)pa, b = *(const int *)pb;
    return (a > b) - (a < b);
}

static void probe(const char *tag, const int *v, size_t n) {
    printf("%-8s", tag);
    for (int key = 1; key <= 5; key++) {
        const int *hit = bsearch(&key, v, n, sizeof v[0], by_int);
        printf("  %d:%s", key, hit ? "hit" : "NULL");
    }
    printf("\n");
}

int main(void) {
    int a[] = { 5, 1, 4, 2, 3 };
    probe("as-is", a, 5);
    qsort(a, 5, sizeof a[0], by_int);
    probe("sorted", a, 5);
    return 0;
}
```

- ★★ `as-is` 줄에서 다섯 키 중 `hit` 은 어느 것인가? `sorted` 줄은?

### 7. `atoi` 의 오류 동작 (왜) ★★

- ★★ 표준은 `atoi` 계열이 **오류일 때** 무엇을 정하고 무엇을 정하지 않는가? 1번 격자의 `atoi` 칸을 채울 때 그 문장이 어디에 걸리는가?
- ★ 표준은 `atoi` 를 `strtol` 로 어떻게 정의하는가? 그 정의에서 **빠진 것**은?

### 8. `errno = 0` 과 `long` → `int` (왜) ★★

- ★★ `strtol` 을 부르기 **직전에** `errno` 를 0 으로 두는 이유는?
- ★★ `strtol` 이 성공해도 **`int` 변수에 넣기 전에** 한 번 더 확인해야 하는 것은?

### 9. `bsearch` 의 전제를 어기면 (경계) ★★

- ★★ 6번의 `as-is` 결과는 「미명시」인가 「UB」인가? 그렇게 읽는 근거가 되는 **두 문장**은?

### 10. 35번 형제와 이어서 (연결) ★★

- [35번 형제](../35-function-pointers-and-callback-tables/)는 `qsort` 비교자에서 **무엇을** 이미 쟀는가?
- ★★ 이 편의 3번 · 4번은 그 위에 **어떤 칸**을 더했는가?

### 11. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- 이 주제에서 **표준 / 구현 정의 / 컴파일러·glibc 구현 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- ★★★ 이 편의 **네 번째 창**은 무엇이고, 그 창이 **못 보는 것**은?

### 12. 경계와 다른 갈래 (연결) ★

- **정렬 · 이분 탐색 알고리즘**은 어느 폴더가 정본인가?
- ★ Go 의 `strconv.Atoi` 는 1번의 `"  42"` · `"42 "` 를 어떻게 다루는가([Go 갈래 11번](../../../go/syntax/11-strings-strconv-bytes-and-unicode-utf8/))?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
