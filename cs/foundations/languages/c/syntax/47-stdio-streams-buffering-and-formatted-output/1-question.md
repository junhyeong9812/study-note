# c/syntax/47 — `<stdio.h>` 스트림 · 버퍼링 · 서식 출력: 「**지정자는 타입과의 계약이고 틀리면 미정의다 — 그리고 출력이 「언제」 나가는지는 받는 쪽이 터미널이냐에 달렸다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · glibc 2.39 · strace 6.8 · x86-64 Linux. 터미널은 **`script -qc`** 가 만든 의사 터미널로 흉내 냈다.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **타입마다 맞는 지정자**(`%zu` · `%lld` · `PRId64` · `%td` · `%p`)와 **컴파일러가 잡는 틀린 지정자 · 안 잡는 틀린 지정자**
> ② **stdout 의 버퍼링 모드는 받는 쪽이 정한다**(터미널 · 파이프 · 파일) — 보이는 순서와 `write` 호출 수 ③ **stderr 은 왜 먼저 나오나.**
> ★★★ **본체 창은 둘** — 지정자는 **① 컴파일 진단**(틀린 지정자의 출력은 미정의라 싣지 않는다), 버퍼링은 **`strace` 가 센 `write` 호출 수**다.
> ★★ **「`printf` 는 가변 인자 함수라 컴파일러가 형식 문자열을 대조해 준다」** 는 [36번 형제](../36-variadic-functions-stdarg/)가 이미 보였다 — 여기는 **타입별 지정자 표**를 세운다.
> 선행 — [02번 형제](../02-basic-types-sizes-and-fixed-width-integers/) · [46번 형제](../46-errno-and-error-return-conventions/).

## 이 파일을 푸는 법

- ★★ **예측형 다섯 문항(1\~5)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「경고가 나나」만** 묻는다 — 틀린 지정자가 **무엇을 찍는지는 묻지 않는다**(미정의다).
- ★★ **3번은 두 가지를 따로** 적어라 — **화면에 보이는 순서**와 **`write` 시스템 호출이 몇 번인가.**

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 타입 여덟 × 지정자 셋 (예측) ★★★ 이 주제의 축

```c
/* s47f.c */
#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

void probe(size_t z, long long ll, int64_t i64, uint8_t u8,
           ptrdiff_t pd, void *vp, double d, float f) {
    printf("%zu\n", z);                 /* size_t · %zu */
    printf("%d\n", z);                  /* size_t · %d */
    printf("%lu\n", z);                 /* size_t · %lu */
    printf("%lld\n", ll);               /* long long · %lld */
    printf("%d\n", ll);                 /* long long · %d */
    printf("%ld\n", ll);                /* long long · %ld */
    printf("%" PRId64 "\n", i64);       /* int64_t · PRId64 */
    printf("%d\n", i64);                /* int64_t · %d */
    printf("%lld\n", i64);              /* int64_t · %lld */
    printf("%" PRIu8 "\n", u8);         /* uint8_t · PRIu8 */
    printf("%d\n", u8);                 /* uint8_t · %d */
    printf("%c\n", u8);                 /* uint8_t · %c */
    printf("%td\n", pd);                /* ptrdiff_t · %td */
    printf("%d\n", pd);                 /* ptrdiff_t · %d */
    printf("%ld\n", pd);                /* ptrdiff_t · %ld */
    printf("%p\n", vp);                 /* void * · %p */
    printf("%d\n", vp);                 /* void * · %d */
    printf("%lx\n", vp);                /* void * · %lx */
    printf("%f\n", d);                  /* double · %f */
    printf("%d\n", d);                  /* double · %d */
    printf("%lf\n", d);                 /* double · %lf */
    printf("%f\n", f);                  /* float · %f */
    printf("%d\n", f);                  /* float · %d */
    printf("%lf\n", f);                 /* float · %lf */
}
```

`$CC -std=c17 -c s47f.c` 만 한다(**`-Wall` 없음**). `$CC` 는 `gcc` · `gcc -Wno-format` · `clang` · `clang -Wno-format`.

- ★★★ 24 줄 × 네 설정에서 **경고가 나는 칸**은? 두 컴파일러가 같은 줄을 잡는가?
- ★★ 경고가 **안 나는** 줄 가운데 **이식성이 없는 줄**은 어느 것인가?

### 2. 맞는 지정자로 찍으면 (예측) ★★

```c
/* s47ok.c */
#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

int main(void) {
    size_t z = sizeof(long double);
    long long ll = -9000000000LL;
    int64_t i64 = INT64_MIN;
    uint8_t u8 = 200;
    char arr[10];
    ptrdiff_t pd = &arr[2] - &arr[9];
    double d = 0.1;
    float f = 0.1f;
    printf("%zu | %lld | %" PRId64 " | %" PRIu8 " %d | %td\n", z, ll, i64, u8, u8, pd);
    printf("%f %.17g | %f %.17g\n", d, d, f, f);
    printf("%%p 로 NULL = %p\n", (void *)0);
    return 0;
}
```

- ★★ 세 줄의 출력은?
- ★ `float` 을 `%f` 로 찍어도 되는 이유는? `%.17g` 두 값은 왜 다른가?

### 3. `a` · `b` · `c` 의 순서 (예측) ★★★

```c
/* s47b1.c */
#include <stdio.h>

int main(void) {
    printf("a");
    fprintf(stderr, "b");
    printf("c\n");
    return 0;
}
```

```c
/* s47b2.c */
#include <stdio.h>

int main(void) {
    printf("a\n");
    fprintf(stderr, "b\n");
    printf("c\n");
    return 0;
}
```

```c
/* s47b3.c */
#include <stdio.h>

int main(void) {
    setvbuf(stdout, NULL, _IOLBF, 0);   /* 줄 버퍼로 */
    printf("a\n");
    fprintf(stderr, "b\n");
    printf("c\n");
    return 0;
}
```

```c
/* s47b4.c */
#include <stdio.h>

int main(void) {
    printf("a\n");
    fflush(stdout);
    fprintf(stderr, "b\n");
    printf("c\n");
    return 0;
}
```

넷을 **터미널** · **파이프**(`./x 2>&1 | cat`) · **파일**(`./x > 파일 2>&1`)로 돌린다 — stdout 과 stderr 을 **한 곳으로** 모은 판이다. `strace -e trace=write` 로 fd 1 · fd 2 의 `write` 를 센다.

- ★★★ 12 칸 각각의 **보이는 순서**와 **`write(1, …)` · `write(2, …)` 수**는?
- ★★ `s47b1.c` 와 `s47b2.c` 중 **받는 쪽에 따라 순서가 갈리는** 것은?

### 4. 만 바이트를 한 글자씩 (예측) ★★

```c
/* s47b5.c */
#include <stdio.h>

int main(void) {
    for (int k = 0; k < 10000; k++) putchar('x');
    fprintf(stderr, "%s%s%s\n", "e", "r", "r");  /* 한 번의 호출 · 조각 셋 */
    return 0;
}
```

stdout 을 **파일**로 받고 stderr 은 버린다.

- ★★ fd 1 의 `write` 는 몇 번 · 각각 몇 바이트인가? fd 2 의 `write` 는 몇 번인가?
- ★ fd 2 의 `write` 는 fd 1 의 `write` 들 사이 **어디에** 끼는가?

### 5. stdio 는 무엇을 보고 모드를 고르나 (예측) ★★

`s47b2.c` 를 **파일** · **터미널** · **`/dev/null`** 로 받는 세 판에서 `strace -e trace=fstat,ioctl` 로 **fd 1 에 대한 호출**만 본다.

- ★★ 세 판에서 각각 무엇이 찍히는가? stdio 가 가른 것은 **무엇**인가?
- ★ `/dev/null` 도 문자 장치다 — 터미널 판과 **무엇이 다른가**?

### 6. 표준은 무엇을 약속하나 (왜) ★★★

- ★★★ 표준은 **stdout · stderr 의 처음 버퍼링**에 대해 정확히 무엇이라고 적는가? 「터미널이면 줄 버퍼」는 **표준 문장**인가?
- ★★ 「대화형 장치」가 무엇인지는 누가 정하나?

### 7. 틀린 지정자의 출력 (왜) ★★

- ★★ `printf("%d\n", z)`(`size_t`)가 **맞는 값처럼 보이는 수**를 찍었다면, 그것을 「`%d` 도 된다」의 근거로 쓸 수 있는가?
- ★ 이 편이 1번의 틀린 줄을 **실행하지 않은** 이유는?

### 8. 경고가 없는 틀림 (경계) ★★

- ★★ `size_t` 를 `%lu` 로 · `ptrdiff_t` 를 `%ld` 로 찍는 줄에 경고가 없는 이유는? 어느 플랫폼에서 깨지나?
- ★ gcc 가 `size_t · %d` 에 제안하는 지정자는 무엇이고, 그 제안은 **이식성 면에서** 옳은가?
- ★ 1번에서 `-Wall` 없는 gcc 칸의 결과는 **누가 정한 것**인가?

### 9. 승격이 바꾸는 지정자 (경계) ★★

- ★★ `uint8_t` 를 `%d` 로 찍는 것이 **맞는** 이유는? `float` 을 `%lf` 로 찍는 것은?

### 10. 끝날 때 누가 비우나 (연결) ★★

- ★★ `exit` 와 `_exit` 은 stdio 버퍼에 대해 무엇이 다른가? Go 의 `bufio` 는 어느 쪽과 같은가?

### 11. 다섯 층과 경계 (연결) ★★

- 이 주제에서 **표준 / 구현 정의 / glibc / 컴파일러 구현(배포판 설정 포함)** 칸에 각각 무엇이 들어가는가?
- ★ **입력 · 파일**(`fgets` · `fread` · `EOF`)은 어디가 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
