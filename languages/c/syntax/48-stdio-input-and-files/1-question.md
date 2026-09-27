# c/syntax/48 — `<stdio.h>` 입력과 파일: 「**읽기 함수의 반환값은 「멈췄다」만 말한다 — 끝이었는지 고장이었는지는 멈춘 뒤에 `feof`·`ferror` 에게 따로 물어야 한다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · glibc 2.39 · x86-64 Linux · `-fsanitize=address`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **EOF 와 읽기 오류는 반환값이 같다**(`NULL` · `EOF` · `0`) — `feof`/`ferror` 로 가른다 ② **`fgetc` 의 반환을 `char` 에 받으면** 한 바이트가 EOF 와 같아지거나 EOF 가 영영 안 온다
> ③ **크기를 모르는 입력 함수**(`gets` · `scanf("%s")`)와 **반환값을 안 보는 `scanf`**.
> ★★★ **본체 창은 둘째 창 — 실행 결과의 EOF 대 오류 격자**다. 1번은 **칸마다 「읽은 바이트 · `feof` · `ferror`」** 를 적어야 답이다.
> ★ **출력 쪽 스트림 · 버퍼링**은 [47번 형제](../47-stdio-streams-buffering-and-formatted-output/)가 정본이다.
> 선행 — [47번 형제](../47-stdio-streams-buffering-and-formatted-output/).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「루프가 멈췄다」와 「왜 멈췄나」를 따로** 적어라 — 앞은 반환값, 뒤는 `feof`/`ferror` 다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 함수는 버퍼의 크기를 아는가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 입력 다섯 × 읽기 넷 (예측) ★★★ 이 주제의 축

```c
/* s48a.c */
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc < 3) return 2;
    const char *how = argv[1];
    FILE *f = fopen(argv[2], "rb");
    if (f == NULL) { printf("fopen 이 NULL\n"); return 0; }
    long n = 0;
    if (strcmp(how, "fgets") == 0) {
        char buf[8];
        while (fgets(buf, sizeof buf, f) != NULL) n += (long)strlen(buf);
    } else if (strcmp(how, "fgetc-char") == 0) {
        char c;
        while ((c = fgetc(f)) != EOF && n < 100) n++;    /* 100 번에서 멈추는 상한 */
    } else if (strcmp(how, "fgetc-int") == 0) {
        int c;
        while ((c = fgetc(f)) != EOF) n++;
    } else {
        char buf[4];
        size_t r;
        while ((r = fread(buf, 1, sizeof buf, f)) > 0) n += (long)r;
    }
    printf("%ld\t%d\t%d\n", n, feof(f) != 0, ferror(f) != 0);
    fclose(f);
    return 0;
}
```

입력은 다섯이다 — `s48-ok.txt`(`l1\nl2\n` · 6 바이트) · `s48-empty.txt`(0 바이트) · `s48-nonl.txt`(`l1\nl2` · 5 바이트) · `s48-ff.bin`(`61 ff 62 0a` · 4 바이트) · **`s48-dir`(디렉토리)**. `./x <읽기> <입력>` 으로 돌린다(`gcc -O0`).

- ★★★ 20 칸 각각의 **읽은 바이트 · `feof` · `ferror`** 는?
- ★★ 「루프가 멈췄으니 끝까지 읽었다」고 보는 코드가 **틀리는 칸**은 어디인가? `feof`/`ferror` 로 보는 코드는?
- ★ 디렉토리를 `fopen(…, "rb")` 하면 `NULL` 인가?

### 2. `char` 의 부호가 바뀌면 (예측) ★★

1번의 `fgetc-char` 읽기를 `gcc` · `gcc -funsigned-char` · `clang` · `clang -funsigned-char` 로 만들어 `s48-ok.txt` 와 `s48-ff.bin` 에 돌린다. 루프에는 **100 번 상한**이 있다.

- ★★ 여덟 칸의 **읽은 바이트 · `feof`** 는?
- ★ `-funsigned-char` 로 컴파일하면 gcc 는 무엇이라고 경고하는가?

### 3. `while (!feof(f))` (예측) ★★

```c
/* s48w.c */
#include <stdio.h>

int main(void) {
    FILE *f = fopen("s48-two.txt", "r");
    if (f == NULL) return 1;
    char line[16];
    int k = 0;
    while (!feof(f)) {
        fgets(line, sizeof line, f);
        printf("%d: %s", ++k, line);
    }
    fclose(f);
    return 0;
}
```

`s48-two.txt` 는 `l1\nl2\n` 이다.

- ★★ 출력은? 경고는 나는가?

### 4. `gets` 를 판마다 (예측) ★★★

```c
/* s48g.c */
#include <stdio.h>

int main(void) {
    char buf[8];
    if (gets(buf) != NULL) puts(buf);
    return 0;
}
```

- ★★★ `gcc -std=c11 -c` · `gcc -std=c11 -pedantic-errors -c` · `clang -std=c11 -c` · `gcc -std=c99`(컴파일 + 링크)의 **종료 코드와 진단의 종류**는?
- ★★ 링크 단계에서 무엇이 한 줄 더 나오는가?

### 5. `scanf` 셋 (예측) ★★★

```c
/* s48s.c */
#include <stdio.h>

int main(void) {
    char name[10];
    if (scanf("%s", name) == 1) printf("name = %s\n", name);
    return 0;
}
```

```c
/* s48s9.c */
#include <stdio.h>

int main(void) {
    char name[10];
    while (scanf("%9s", name) == 1) printf("[%s]\n", name);
    return 0;
}
```

```c
/* s48r.c */
#include <stdio.h>

int main(void) {
    int n = -1, r, rounds = 0;
    while ((r = scanf("%d", &n)) != EOF && rounds < 5) {   /* 5 번에서 멈추는 상한 */
        rounds++;
        printf("scanf 반환 %d · n = %d\n", r, n);
    }
    printf("돈 횟수 %d · 다음 getchar() = %d\n", rounds, getchar());
    return 0;
}
```

- ★★★ `s48s.c` 를 ASan 으로 만들어 26 글자 한 줄을 넣으면? 리포트의 **종류 · 몇 바이트 쓰기 · 어느 변수**는?
- ★★ 같은 줄을 `s48s9.c` 에 넣으면?
- ★★ `s48r.c` 에 `abc` 를 넣으면? `12 34` 를 넣으면?

### 6. 텍스트 모드 · 디렉토리 (예측) ★★

```c
/* s48p.c */
#include <stdio.h>

static void walk(const char *mode) {
    FILE *f = fopen("s48-crlf.txt", mode);
    if (f == NULL) return;
    char line[16];
    fgets(line, sizeof line, f);
    long after_line = ftell(f);
    fseek(f, 0, SEEK_END);
    printf("\"%s\" : 첫 줄 뒤 ftell = %ld · 끝 ftell = %ld · 첫 줄 끝 바이트 %02x\n",
           mode, after_line, ftell(f), (unsigned char)line[after_line - 2]);
    fclose(f);
}

int main(void) {
    walk("r");
    walk("rb");
    return 0;
}
```

```c
/* s48d.c */
#include <errno.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    errno = 0;
    FILE *f = fopen("s48-dir", "r");
    printf("fopen = %s · errno = %d\n", f == NULL ? "NULL" : "ptr", errno);
    if (f == NULL) return 1;
    char buf[4];
    size_t n = fread(buf, 1, sizeof buf, f);
    int e = errno;
    printf("fread = %zu · feof = %d · ferror = %d · errno = %s\n",
           n, feof(f) != 0, ferror(f) != 0, strerror(e));
    fclose(f);
    return 0;
}
```

`s48-crlf.txt` 는 `ab\r\ncd\n`(7 바이트)이다.

- ★★ `s48p.c` 의 두 줄은?
- ★★ `s48d.c` 의 두 줄은?

### 7. EOF 와 오류는 왜 따로 물어야 하나 (왜) ★★★

- ★★★ `fgets` · `fgetc` · `fread` 가 **끝**과 **오류**에 각각 무엇을 돌려주는가? 표준은 둘을 가르는 방법으로 무엇을 적는가?
- ★★ `while (!feof(f))` 가 한 줄을 **더** 도는 이유는?

### 8. `fgetc` 는 왜 `int` 를 돌려주나 (왜) ★★

- ★★ 바이트 256 가지와 **EOF 하나**를 한 반환값에 담으려면 무엇이 필요한가?
- ★ `char` 가 부호 있는 판과 없는 판에서 **사고의 모양**이 어떻게 다른가?

### 9. `fgets` 의 두 경계 (경계) ★★

- ★★ 마지막 줄에 개행이 없으면 `fgets` 는 그 줄을 돌려주는가? 한 줄이 버퍼보다 길면?
- ★ 「이번에 받은 것이 줄 전체인가」를 어떻게 아는가?

### 10. `scanf` 의 반환값 (경계) ★★

- ★★ `scanf` 가 돌려주는 `0` 과 `EOF` 는 각각 무엇을 뜻하나? `!= EOF` 로 루프를 돌리면 왜 위험한가?
- ★ 매치에 실패한 글자는 어디로 가는가?

### 11. 다섯 층과 경계 (연결) ★★

- 이 주제에서 **표준 / 구현 정의 / glibc · POSIX / 컴파일러 구현** 칸에 각각 무엇이 들어가는가?
- ★ **읽은 뒤의 문자열 다루기** · **숫자 파싱(`strtol`)** 은 어디가 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
