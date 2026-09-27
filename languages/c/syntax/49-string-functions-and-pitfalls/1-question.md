# c/syntax/49 — `<string.h>` 문자열 함수와 함정: 「**`n` 이 붙은 함수도 「널까지 n」을 약속하지 않는다 — 함수마다 `n` 의 뜻이 다르고, 널 종단은 함수가 아니라 호출자가 확인한다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · glibc 2.39 · x86-64 Linux · `-fsanitize=address`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **함수마다 `n` 이 무엇의 개수인가** — `strncpy` · `strncat` · `snprintf` · `strlcpy`
> ② **원본이 버퍼보다 짧음 · 같음 · 김** 에서 **널 종단 · 넘침 · 반환값** ③ **`strlen`·`strcat` 은 매번 처음부터 걷는다.**
> ★★★ **본체 창은 둘째 창 — 실행 결과의 경계 조건 격자**다. 널 종단은 **`memchr(d, 0, sizeof d)`** 로 판정하고 문자열을 찍지 않는다(널이 없으면 찍는 것 자체가 미정의다).
> ★★ **`strncpy` 의 세 경우를 바이트로 찍은 것**(`61 62 00 00 00` · `61 62 63 64 65` · 잘림)과 **널 없는 배열에 `strlen`** 은 [20번 형제](../20-null-terminated-strings-and-string-literals/)가 이미 보였다 — 여기는 **여섯 함수를 한 격자**에 세운다.
> 선행 — [20번 형제](../20-null-terminated-strings-and-string-literals/).

## 이 파일을 푸는 법

- ★★ **예측형 다섯 문항(1\~5)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **1번은 칸마다 셋을 따로** 적어라 — **널이 있나 · 몇 바이트를 썼나 · 넘쳤나.** 넘친 칸은 **어느 빌드가 멈추나**까지.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 함수의 `n` 은 무엇의 개수인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 함수 일곱 × 원본 길이 셋 (예측) ★★★ 이 주제의 축

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

`./x <함수 1~7> <원본 0~2>` — 원본은 `"abc"`(3) · `"abcdefgh"`(8) · `"abcdefghijkl"`(12), `d` 는 `char[8]`. 빌드는 셋 — **gcc ASan `-O0`** · **gcc `-O2`(보통 빌드)** · **clang `-O2`(보통 빌드)**.

- ★★★ 21 줄 각각 — **널이 있나 · 바꾼 바이트 수 · 반환값**, 넘친다면 **어느 빌드가 멈추나**?
- ★★ **널 종단 안 된 칸**과 **넘친 칸**은 각각 몇 칸인가?

### 2. 컴파일러는 무엇을 잡나 (예측) ★★

1번의 `s49a.c` 를 `gcc`·`clang` 에 `-std=c17 -Wall -Wextra -pedantic -O0 -c` 로 넣는다.

- ★★ 경고는 **어느 줄**에서 나는가? 두 컴파일러의 문구는 **무엇을 권하는가**?

### 3. `strcat` 을 되풀이하면 (예측) ★★

```c
/* s49c.c */
#include <stdio.h>
#include <string.h>

static unsigned long long reads;                 /* 읽은 바이트를 센다 */

static size_t counting_strlen(const char *s) {
    size_t n = 0;
    while (reads++, s[n] != '\0') n++;
    return n;
}

static char *counting_strcat(char *d, const char *s) {  /* strcat 과 같은 일 */
    char *end = d + counting_strlen(d);
    size_t k = 0;
    do { reads++; end[k] = s[k]; } while (s[k++] != '\0');
    return d;
}

static char buf[2 * 4000 + 1];

int main(void) {
    const int ns[] = { 10, 100, 1000, 4000 };
    for (int t = 0; t < 4; t++) {
        int n = ns[t];

        reads = 0; buf[0] = '\0';
        for (int i = 0; i < n; i++) counting_strcat(buf, "ab");
        unsigned long long a = reads;

        reads = 0; buf[0] = '\0';
        char *end = buf;                          /* 끝을 기억해 두는 꼴 */
        for (int i = 0; i < n; i++) end = counting_strcat(end, "ab") + 2;
        unsigned long long b = reads;

        printf("n = %4d · 길이 %5zu · strcat 반복 %9llu 바이트 읽음 · 끝을 기억 %6llu 바이트 읽음\n",
               n, strlen(buf), a, b);
    }
    return 0;
}
```

- ★★ 네 줄의 **두 「읽음」 수**는? `n` 이 10 배가 될 때 각각 몇 배가 되는가?

### 4. `sizeof` 로 크기를 넘기면 (예측) ★★

```c
/* s49z.c */
#include <stdio.h>
#include <string.h>

static void fill(char *d, const char *s) {
    strncpy(d, s, sizeof d);            /* 배열 크기를 쓰려던 자리 */
    d[sizeof d - 1] = '\0';
}

int main(void) {
    char name[32];
    fill(name, "abcdefghijklmnop");
    printf("sizeof name = %zu · strlen(name) = %zu\n", sizeof name, strlen(name));
    return 0;
}
```

- ★★ 두 컴파일러의 경고와 실행 출력은?

### 5. `strlcpy` 는 있나 (예측) ★★

```c
/* s49l.c */
#include <stdio.h>
#include <string.h>

int main(void) {
    char d[4];
    size_t r = strlcpy(d, "abcdef", sizeof d);
    printf("반환 %zu · d = %s · 잘렸나 = %d\n", r, d, r >= sizeof d);
    return 0;
}
```

- ★★ `gcc -std=c17 -c` 는 무엇이라고 하는가? `-D_DEFAULT_SOURCE` 를 주면 실행 출력은?
- ★ `libc.so.6` 의 `strlcpy` 에는 **어느 판**이 붙어 있는가?

### 6. `strncpy` 는 왜 이렇게 생겼나 (왜) ★★★

- ★★★ 표준은 `strncpy` 가 **짧은 원본**과 **긴 원본**에서 각각 무엇을 한다고 적는가? 「널을 붙인다」는 문장이 있는가?
- ★★ 1번에서 **짧은 원본에 8 바이트를 쓴** 이유는?

### 7. 잘렸는지 아는 함수 (왜) ★★

- ★★ `snprintf` 와 `strlcpy` 의 반환값은 무엇이고, 그것으로 **잘림을 어떻게** 판정하나?
- ★ `strncat(d, s, sizeof d - 1)` 은 **어떤 `d`** 에서 옳고 **어떤 `d`** 에서 틀리는가?

### 8. 보통 빌드의 두 컴파일러 (경계) ★★★

- ★★★ 1번의 넘친 칸에서 gcc `-O2` 와 clang `-O2` 가 **다르게 굴었다면 무엇이 다른가**? 그 차이는 **표준**의 것인가?
- ★★ 넘친 칸에서 보통 빌드가 `exit 0` 으로 끝났다면, 그것은 무엇을 뜻하고 무엇을 뜻하지 않는가?

### 9. `memcpy` 는 문자열 함수인가 (경계) ★★

- ★★ 1번의 `memcpy` 줄은 왜 **세 길이 전부** 널이 없는가? 그것은 결함인가?

### 10. 길이를 가진 문자열 (연결) ★★

- ★★ Rust 의 `&str`·슬라이스는 이 편의 어느 사고를 **원리상** 없애는가? 없애지 못하는 것은?

### 11. 다섯 층과 경계 (연결) ★★

- 이 주제에서 **표준 / glibc · POSIX / 컴파일러 구현(배포판 포함)** 칸에 각각 무엇이 들어가는가?
- ★ **문자열 탐색 알고리즘** · **`memcpy`/`memmove` 의 겹침** 은 어디가 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
