# c/syntax/48 — `<stdio.h>` 입력과 파일: 「**읽기 함수의 반환값은 「멈췄다」만 말한다 — 끝이었는지 고장이었는지는 멈춘 뒤에 `feof`·`ferror` 에게 따로 물어야 한다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) — `fgets` 의 「**n 보다 하나 적게 읽는다 · 개행(보존) 뒤나 파일 끝 뒤로는 더 안 읽는다 · 끝에 널을 쓴다**」·「**아무것도 못 읽고 파일 끝이면 배열은 그대로이고 널 포인터 · 읽기 오류면 배열 내용은 미지정이고 널 포인터**」, `fgetc` 의 「**문자를 `unsigned char` 로 얻어 `int` 로 바꿔 돌려준다 · 파일 끝이면 끝 표시를 세우고 `EOF` · 읽기 오류면 오류 표시를 세우고 `EOF`**」·각주 「**파일 끝과 읽기 오류는 `feof` 와 `ferror` 로 가를 수 있다**」, `fread` 의 「**읽은 원소 수 — 오류나 끝이면 `nmemb` 보다 적을 수 있다**」, `scanf` 의 「**첫 변환 전에 입력 실패면 `EOF`, 아니면 대입한 입력 항목 수(이른 매치 실패면 0 일 수 있다)**」, 텍스트 스트림의 `ftell` 「**`fseek` 에 쓸 수 있는 미지정 정보**」, 바뀐 점 목록의 「**C11 — `gets` 함수를 없앴다**」를 **본문에서 직접 찾아 읽었다**) · 이 머신의 `/usr/include/stdio.h` 의 `gets` 주석(글자째 캡처)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **읽은 바이트 · 표시 · 진단 · ASan 리포트는 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.\
> ★★★ **본체는 EOF 대 오류 격자다** — 입력 5(정상 · 빈 파일 · 마지막 개행 없음 · `0xFF` 바이트 · 디렉토리) × 읽기 4(`fgets` · `fgetc` 를 `char` 에 · `fgetc` 를 `int` 에 · `fread`).\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> ★★★ **경계** — **출력 쪽 스트림 · 버퍼링 · 서식 지정자**는 [47번 형제](../47-stdio-streams-buffering-and-formatted-output/), **널 종단 문자열 · 널 없는 배열에 `strlen`** 은 [20번 형제](../20-null-terminated-strings-and-string-literals/), **읽은 문자열을 복사·이어 붙이기**는 [49번 형제](../49-string-functions-and-pitfalls/), **읽은 숫자를 `strtol` 로 파싱**은 [목록의 **51번 주제**](../51-stdlib-conversion-qsort-and-bsearch/)가 정본이다. 여기는 **읽기가 멈춘 이유를 가르는 법 · 크기를 모르는 입력 함수**만 본다.
> 선행 — [47번 형제](../47-stdio-streams-buffering-and-formatted-output/).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 둘째 창 — 실행 결과의 EOF 대 오류 격자다.** 읽기 루프는 **반환값이 멈추라고 할 때** 멈추고, 멈춘 **뒤에** `feof`/`ferror` 를 묻는다.
★★★ 그 격자에서 **EOF 만 본 코드가 오판한 칸 5 / 20**(디렉토리 네 칸 + `char` 로 받은 `0xFF` 한 칸) · **`feof`/`ferror` 로 본 코드가 오판한 칸 0 / 20**. 그리고 **다 못 읽고 멈춘 칸 1 / 20** — 그 한 칸은 **`feof` 도 `ferror` 도 0** 이었다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | ★ `gets` 의 판별(판마다 경고 · 에러 · 링커 경고) · `-funsigned-char` 의 `-Wtype-limits` | 씀 |
| ★★★ ② **실행 출력(EOF 대 오류 격자)** | ★ **본체** — 읽은 바이트 · `feof` · `ferror` | 씀 |
| ③ sanitizer | ★★ `scanf("%s")` 의 **`stack-buffer-overflow` WRITE** | 씀 |
| ④ 링크 | ★ 링커의 `the 'gets' function is dangerous` | 씀 |
| 시간 측정 | — | 부적용 |
| ★ 제5의 상태 | 「읽기가 **왜** 멈췄나」를 **반환값에게 물으면 끝과 오류가 같은 대답**이다(`NULL` · `EOF` · `0`). **`feof`/`ferror` 로 바꿔 물어** 20 칸을 갈랐다 — 그리고 `char` 로 받은 칸은 **두 표시가 다 0** 이라 **「끝도 오류도 아닌데 멈췄다」** 는 대답이 나왔다 | 창을 바꿔 답함 |

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
| 안 흔들린다 | ★★★ **EOF 대 오류 격자 · 부호 격자 · 진단 · 실행 출력** | 같은 판 · 같은 입력 파일이면 같다 |
| ★ 흔들린다 | **ASan 리포트의 PID · 주소** | 정규화 기본 규칙이 가린다 — 대조할 것은 **종류(`stack-buffer-overflow`) · `WRITE of size 27` · `'name'` · `[32, 42)`** 다 |

## 한눈에 — 쉽게 말하면

**읽기 함수는 물을 긷는 두레박이다.** 두레박이 **빈 채로 올라오면** 멈춘다 — 그런데 빈 이유가 둘이다.

- **우물이 말랐다** — 파일 끝. → **`feof`**
- **줄이 끊겼다** — 읽기 오류(디렉토리 · 장치 오류). → **`ferror`**
- **두레박만 봐서는 둘이 같다** — 빈 두레박 하나. → **`NULL` · `EOF` · `0`**
- **물 색이 「빈 두레박 표시」와 같은 물** — `char` 로 받은 `0xFF` 는 `EOF`(-1)와 **같아진다.** 물이 남았는데 멈춘다. → **`char` 로 받은 `fgetc`**
- **두레박 크기를 모르고 붓는 사람** — `gets` · `scanf("%s")` 는 **버퍼 크기를 모른다.** → **넘침**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 우물이 말랐다 | 파일 끝 | ★★ `feof = 1` |
| 줄이 끊겼다 | 디렉토리를 `fread` | ★★★ **읽은 0 · `ferror = 1`** · `EISDIR` |
| 빈 두레박 하나 | 반환값 | ★★★ **EOF 만 본 코드가 오판한 칸 5 / 20** |
| 표시와 같은 물 색 | `char c = fgetc(f)` 의 `0xFF` | ★★★ **4 바이트 중 1 바이트에서 멈춤 · 두 표시 다 0** |
| 크기를 모르고 붓기 | `scanf("%s", name)` | ★★ **`WRITE of size 27` · `[32, 42) 'name'`** |

```text
   읽기 루프 — 멈추는 것은 반환값, 이유를 대는 것은 표시

   while (r = 읽기(...), r 이 「더 없다」가 아니다)
       처리(r);
        |
        v  멈췄다 — 반환값은 끝과 오류를 가르지 않는다
   +---------------------+----------------------+-----------------------+
   | feof(f) != 0        | ferror(f) != 0       | 둘 다 0               |
   | 파일 끝 — 정상      | 읽기 오류            | ★ 루프가 스스로 멈췄다 |
   |                     |                      |   (char 로 받은 0xFF)  |
   +---------------------+----------------------+-----------------------+

   ★ while (!feof(f)) { 읽기; 처리; } 는 순서가 반대다
     - feof 는 「이미 끝에 부딪혔나」를 말한다 — 「다음이 끝인가」가 아니다
     - 마지막 줄을 읽은 뒤에도 feof 는 아직 0 → 한 번 더 돌고, 실패한 읽기의 결과를 처리한다
```

- ★★★ **이 주제의 본체는 「표준」 칸** — 반환값이 끝과 오류에 같다는 것, `feof`/`ferror` 로 가른다는 것, `fgetc` 가 `unsigned char` 를 `int` 로 준다는 것, `gets` 가 C11 에서 없어졌다는 것이 **전부 표준 문장**이다.
- ★★ **「디렉토리를 `fopen` 할 수 있다」·「`EISDIR`」은 glibc · POSIX 칸**이다.

> **끝 표시 / 오류 표시(end-of-file indicator / error indicator)** — 스트림마다 있는 두 깃발. 읽기가 끝에 부딪히면 앞의 것이, 오류를 만나면 뒤의 것이 선다.\
> 예: `feof(f)` · `ferror(f)` 가 읽는다 · `clearerr(f)` 가 내린다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **읽기가 멈췄을 때 그것이 끝인지 오류인지 어떻게 가르나** — 그리고 반환값만 본 코드는 어디서 틀리나.
2. ★★ **`fgetc` 의 반환을 어디에 받아야 하나** — `char` 의 부호에 따라 사고가 어떻게 달라지나.
3. ★★ **어떤 입력 함수가 버퍼의 크기를 모르나** — `gets` · `scanf("%s")` · 반환값을 안 보는 `scanf`.

## 동작 방식

### (1) ★★★ EOF 대 오류 격자 — 입력 다섯 × 읽기 넷

**언제 쓰나** — 읽기 루프의 **끝 처리**를 쓸 때. ★★★ **이 편의 본체**다.

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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s48a.c -o /dev/null (cc exit=0) =====
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s48a.c -o /dev/null (cc exit=0) =====
```

```text
===== wc -c s48-ok.txt s48-empty.txt s48-nonl.txt s48-ff.bin && od -An -tx1 s48-ff.bin (exit=0) =====
 6 s48-ok.txt
 0 s48-empty.txt
 5 s48-nonl.txt
 4 s48-ff.bin
15 total
 61 ff 62 0a
```

```text
===== EOF 대 오류 격자 — 입력 5 × 읽기 4 (exit=0) =====
입력          	읽기       	읽은 바이트	feof	ferror	feof/ferror 로 본 끝	EOF 만 본 끝	실제
s48-ok.txt    	fgets      	6	1	0	EOF	EOF	끝까지 (6 바이트)
s48-ok.txt    	fgetc-char 	6	1	0	EOF	EOF	끝까지 (6 바이트)
s48-ok.txt    	fgetc-int  	6	1	0	EOF	EOF	끝까지 (6 바이트)
s48-ok.txt    	fread      	6	1	0	EOF	EOF	끝까지 (6 바이트)
s48-empty.txt 	fgets      	0	1	0	EOF	EOF	끝까지 (0 바이트)
s48-empty.txt 	fgetc-char 	0	1	0	EOF	EOF	끝까지 (0 바이트)
s48-empty.txt 	fgetc-int  	0	1	0	EOF	EOF	끝까지 (0 바이트)
s48-empty.txt 	fread      	0	1	0	EOF	EOF	끝까지 (0 바이트)
s48-nonl.txt  	fgets      	5	1	0	EOF	EOF	끝까지 (5 바이트)
s48-nonl.txt  	fgetc-char 	5	1	0	EOF	EOF	끝까지 (5 바이트)
s48-nonl.txt  	fgetc-int  	5	1	0	EOF	EOF	끝까지 (5 바이트)
s48-nonl.txt  	fread      	5	1	0	EOF	EOF	끝까지 (5 바이트)
s48-ff.bin    	fgets      	4	1	0	EOF	EOF	끝까지 (4 바이트)
s48-ff.bin    	fgetc-char 	1	0	0	둘 다 아님	EOF	끝까지 (4 바이트)
s48-ff.bin    	fgetc-int  	4	1	0	EOF	EOF	끝까지 (4 바이트)
s48-ff.bin    	fread      	4	1	0	EOF	EOF	끝까지 (4 바이트)
s48-dir       	fgets      	0	0	1	오류	EOF	읽기 오류
s48-dir       	fgetc-char 	0	0	1	오류	EOF	읽기 오류
s48-dir       	fgetc-int  	0	0	1	오류	EOF	읽기 오류
s48-dir       	fread      	0	0	1	오류	EOF	읽기 오류
(각 줄 = ./x <읽기> <입력> · 읽기 루프는 반환값이 끝을 말할 때 멈춘다 · feof/ferror 는 멈춘 뒤에 묻는다 · gcc -O0)
다 못 읽고 멈춘 칸 1 / 20
EOF 만 본 코드가 오판한 칸 5 / 20
feof/ferror 로 본 코드가 오판한 칸 0 / 20
```

그림 해설 (한 단계씩):

- ★★★ **정상 · 빈 파일 · 개행 없는 마지막 줄 — 열두 칸 다 「끝까지 · `feof = 1`」.** 빈 파일은 **첫 읽기부터** 끝이다. 개행 없는 마지막 줄도 `fgets` 가 **5 바이트 다** 돌려줬다((4)).
- ★★★ **디렉토리 — 네 칸 다 「읽은 0 · `feof = 0` · `ferror = 1`」.** 반환값(`NULL` · `EOF` · `0`)은 **빈 파일과 한 글자도 같다.** 「루프가 멈췄으니 끝」으로 보는 코드는 **빈 파일로 오판**한다.
- ★★★ **`0xFF` 바이트를 `char` 로 받은 칸 — 4 바이트 중 1 에서 멈추고 `feof`·`ferror` 가 둘 다 0.** `fgetc` 는 `0xFF` 를 **`255`(`int`)** 로 줬는데, `char`(이 판은 부호 있음)에 넣는 순간 **`-1`** 이 되어 `EOF` 와 같아졌다((2)).
- ★★ **같은 파일을 `int` 로 받은 칸은 4 바이트 다 읽었다** — 반환을 **`int` 에 받는 것**이 처방이다.
- ★★★ **EOF 만 본 코드가 오판한 칸 5 / 20 · `feof`/`ferror` 로 본 코드는 0 / 20** — 뒤쪽은 디렉토리를 **오류로**, `0xFF` 칸을 **「둘 다 아님 — 뭔가 이상하다」** 로 읽는다. **틀린 결론을 내지 않았다.**

### (2) ★★ `char` 로 받은 `fgetc` — 부호가 사고의 모양을 바꾼다

**언제 쓰나** — `char c; while ((c = fgetc(f)) != EOF)` 를 봤을 때.

```text
===== char 로 받은 fgetc — char 의 부호 × 입력 2 (exit=0) =====
빌드                      	s48-ok.txt (6 바이트)	s48-ff.bin (4 바이트)
gcc                       	읽은 6 · feof 1	읽은 1 · feof 0
gcc -funsigned-char       	읽은 100 · feof 1	읽은 100 · feof 1
clang                     	읽은 6 · feof 1	읽은 1 · feof 0
clang -funsigned-char     	읽은 100 · feof 1	읽은 100 · feof 1
(칸 = ./x fgetc-char <입력> · 루프에 100 번 상한이 있다 — 100 은 「EOF 를 한 번도 못 봤다」)
```

```text
===== gcc -std=c17 -Wall -Wextra -funsigned-char -c s48a.c -o /dev/null (cc exit=0) =====
s48a.c: In function ‘main’:
s48a.c:15:31: warning: comparison is always true due to limited range of data type [-Wtype-limits]
   15 |         while ((c = fgetc(f)) != EOF && n < 100) n++;    /* 100 번에서 멈추는 상한 */
      |                               ^~
```

```text
   fgetc 가 돌려주는 int :   0 ... 255  (바이트)   또는   -1 (EOF)       — 257 가지

   char 가 부호 있음 (이 판 기본)            char 가 부호 없음 (-funsigned-char · ARM 등의 기본)
   --------------------------------         ---------------------------------------------
   255 -> char 에 넣으면 -1                  -1 (EOF) -> char 에 넣으면 255
   -1 == EOF   ★ 데이터 한가운데서 멈춘다     255 != EOF 영원히   ★ 끝에서 안 멈춘다
```

- ★★★ **부호 있는 `char` — `0xFF` 에서 멈춘다**(1 바이트 · `feof 0`). 정상 파일은 문제없다(6 · `feof 1`) — **`0xFF` 가 없는 입력으로 시험하면 통과한다.**
- ★★★ **부호 없는 `char` — 정상 파일에서도 끝나지 않는다** — 두 입력 다 **상한 100** 에 걸렸고 `feof = 1` 이다. **끝에 부딪혔는데도** `EOF`(-1)가 `char` 에서 `255` 가 되어 `!= EOF` 가 영원히 참이다.
- ★★ **gcc 는 `-funsigned-char` 판에서만 `-Wtype-limits` 로 「비교가 늘 참」이라고** 말한다 — 부호 있는 판(이 머신 기본)에서는 **경고 0**(격자의 `48-a-gcc`). **사고가 조용한 쪽이 기본값**이다.
- ★ **`char` 의 부호는 구현 정의**다 — x86-64 리눅스는 부호 있음, ARM 리눅스는 대개 부호 없음이다(이 편은 ARM 에서 돌리지 않았다 — `-funsigned-char` 로 흉내 냈다).

### (3) ★★ `while (!feof(f))` — 마지막 줄을 두 번

**언제 쓰나** — `feof` 를 루프 **조건**에 둔 코드를 봤을 때.

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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s48w.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s48w.c -o x ; ./x (cc exit=0 · run exit=0) =====
1: l1
2: l2
3: l2
```

```c
/* s48w2.c */
#include <stdio.h>

int main(void) {
    FILE *f = fopen("s48-two.txt", "r");
    if (f == NULL) return 1;
    char line[16];
    int k = 0;
    while (fgets(line, sizeof line, f) != NULL)
        printf("%d: %s", ++k, line);
    if (ferror(f)) printf("읽기 오류\n");
    fclose(f);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s48w2.c -o x ; ./x (cc exit=0 · run exit=0) =====
1: l1
2: l2
```

- ★★★ **`3: l2`** — 둘째 줄을 읽은 뒤에도 **`feof` 는 아직 0** 이다(끝에 **부딪힌** 적이 없다). 셋째 `fgets` 가 끝에 부딪혀 `NULL` 을 돌려주는데, 코드는 그 반환을 **안 보고** `line` 을 찍는다.
- ★★ **그 `line` 은 둘째 줄 그대로다** — 표준: 「**아무것도 못 읽고 끝이면 배열은 그대로**」. 그래서 이 출력은 **미정의가 아니라 정해진 틀림**이다. ★ 읽기 **오류**였다면 배열 내용은 **미지정**이다.
- ★★ **경고 0**(`-Wall -Wextra -pedantic`) — 컴파일러는 이 순서 실수를 모른다.
- ★★ **고친 판은 반환값을 조건에 두고, 멈춘 뒤에 `ferror` 를 묻는다**(`s48w2.c`).

### (4) ★★ `fgets` 의 두 경계 — 개행 없는 끝 · 버퍼보다 긴 줄

**언제 쓰나** — 「한 번의 `fgets` = 한 줄」이라고 가정한 코드를 봤을 때.

```c
/* s48f.c */
#include <stdio.h>
#include <string.h>

int main(void) {
    FILE *f = fopen("s48-long.txt", "r");
    if (f == NULL) return 1;
    char buf[5];
    int k = 0;
    while (fgets(buf, sizeof buf, f) != NULL) {
        size_t n = strlen(buf);
        int nl = n > 0 && buf[n - 1] == '\n';
        if (nl) buf[n - 1] = '\0';
        printf("%d번째 fgets : [%s] · 길이 %zu · 끝이 개행인가 = %d\n", ++k, buf, n, nl);
    }
    printf("feof = %d · ferror = %d\n", feof(f) != 0, ferror(f) != 0);
    fclose(f);
    return 0;
}
```

```text
===== od -An -c s48-long.txt (exit=0) =====
   a   b   c   d   e   f   g   h   i   j  \n   x   y
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s48f.c -o x ; ./x (cc exit=0 · run exit=0) =====
1번째 fgets : [abcd] · 길이 4 · 끝이 개행인가 = 0
2번째 fgets : [efgh] · 길이 4 · 끝이 개행인가 = 0
3번째 fgets : [ij] · 길이 3 · 끝이 개행인가 = 1
4번째 fgets : [xy] · 길이 2 · 끝이 개행인가 = 0
feof = 1 · ferror = 0
```

- ★★★ **버퍼(5)보다 긴 줄은 네 글자씩 잘려 온다** — `[abcd]` · `[efgh]` · `[ij]`. **끝이 개행인 조각만 줄의 끝**이다. `fgets` 는 **n 보다 하나 적게** 읽고 널을 붙인다(표준).
- ★★ **마지막 줄에 개행이 없으면 개행 없이 온다** — `[xy]` · `끝이 개행인가 = 0`. 그 뒤의 `fgets` 가 `NULL` 이고 **`feof = 1`**.
- ★★ **그래서 「이번 조각이 줄 전체인가」는 끝 글자가 `'\n'` 인가로** 가른다 — 개행이 없으면 **(가) 줄이 버퍼보다 길다** 이거나 **(나) 파일의 마지막 줄**이다. 다음 `fgets` 가 `NULL` 인가로 둘을 가른다.

### (5) ★★★ `gets` — C11 이 없앴다, 그런데 판마다 말이 다르다

**언제 쓰나** — 옛 코드의 `gets` 를 새 컴파일러로 빌드할 때.

```c
/* s48g.c */
#include <stdio.h>

int main(void) {
    char buf[8];
    if (gets(buf) != NULL) puts(buf);
    return 0;
}
```

```text
===== gcc -std=c11 -c s48g.c -o /dev/null (cc exit=0) =====
s48g.c: In function ‘main’:
s48g.c:5:9: warning: implicit declaration of function ‘gets’; did you mean ‘fgets’? [-Wimplicit-function-declaration]
    5 |     if (gets(buf) != NULL) puts(buf);
      |         ^~~~
      |         fgets
s48g.c:5:19: warning: comparison between pointer and integer
    5 |     if (gets(buf) != NULL) puts(buf);
      |                   ^~
```

```text
===== gcc-12 -std=c11 -c s48g.c -o /dev/null (cc exit=0) =====
s48g.c: In function ‘main’:
s48g.c:5:9: warning: implicit declaration of function ‘gets’; did you mean ‘fgets’? [-Wimplicit-function-declaration]
    5 |     if (gets(buf) != NULL) puts(buf);
      |         ^~~~
      |         fgets
s48g.c:5:19: warning: comparison between pointer and integer
    5 |     if (gets(buf) != NULL) puts(buf);
      |                   ^~
```

```text
===== gcc -std=c11 -pedantic-errors -c s48g.c -o /dev/null (cc exit=1) =====
s48g.c: In function ‘main’:
s48g.c:5:9: error: implicit declaration of function ‘gets’; did you mean ‘fgets’? [-Wimplicit-function-declaration]
    5 |     if (gets(buf) != NULL) puts(buf);
      |         ^~~~
      |         fgets
s48g.c:5:19: error: comparison between pointer and integer
    5 |     if (gets(buf) != NULL) puts(buf);
      |                   ^~
```

```text
===== gcc -std=c11 -Werror=implicit-function-declaration -c s48g.c -o /dev/null (cc exit=1) =====
s48g.c: In function ‘main’:
s48g.c:5:9: error: implicit declaration of function ‘gets’; did you mean ‘fgets’? [-Werror=implicit-function-declaration]
    5 |     if (gets(buf) != NULL) puts(buf);
      |         ^~~~
      |         fgets
s48g.c:5:19: warning: comparison between pointer and integer
    5 |     if (gets(buf) != NULL) puts(buf);
      |                   ^~
cc1: some warnings being treated as errors
```

```text
===== clang -std=c11 -c s48g.c -o /dev/null (cc exit=1) =====
s48g.c:5:9: error: call to undeclared function 'gets'; ISO C99 and later do not support implicit function declarations [-Wimplicit-function-declaration]
    5 |     if (gets(buf) != NULL) puts(buf);
      |         ^
s48g.c:5:19: warning: comparison between pointer and integer ('int' and 'void *') [-Wpointer-integer-compare]
    5 |     if (gets(buf) != NULL) puts(buf);
      |         ~~~~~~~~~ ^  ~~~~
1 warning and 1 error generated.
```

```text
===== gcc -std=c99 -c s48g.c -o s48g.o && gcc s48g.o -o x (cc exit=0) =====
s48g.c: In function ‘main’:
s48g.c:5:5: warning: ‘gets’ is deprecated [-Wdeprecated-declarations]
    5 |     if (gets(buf) != NULL) puts(buf);
      |     ^~
In file included from s48g.c:1:
/usr/include/stdio.h:667:14: note: declared here
  667 | extern char *gets (char *__s) __wur __attribute_deprecated__;
      |              ^~~~
/usr/bin/ld: s48g.o: in function `main':
s48g.c:(.text+0x23): warning: the `gets' function is dangerous and should not be used.
```

```text
===== sed -n '/This function is impossible/,/^#endif/p' /usr/include/stdio.h (exit=0) =====
   This function is impossible to use safely.  It has been officially
   removed from ISO C11 and ISO C++14, and we have also removed it
   from the _GNU_SOURCE feature list.  It remains available when
   explicitly using an old ISO C, Unix, or POSIX standard.

   This function is a possible cancellation point and therefore not
   marked with __THROW.  */
extern char *gets (char *__s) __wur __attribute_deprecated__;
#endif
```

- ★★★ **`gcc -std=c11` 은 경고 둘에 `cc exit=0`**(gcc-12 도 같다) — glibc 헤더가 C11 판에서 **`gets` 선언을 감춰** 「**암시적 선언**」이 됐고, gcc 13 은 그것을 **경고로만** 낸다. **「종료 코드 0인데 ill-formed」** 의 또 한 사례다. **`-pedantic-errors` 나 `-Werror=implicit-function-declaration` 이라야** 에러(`exit=1`)가 된다.
- ★★ **clang 18 은 기본으로 에러**(`call to undeclared function 'gets'`, `exit=1`) — **같은 소스 · 같은 판에서 두 컴파일러가 종료 코드를 달리한다.**
- ★★★ **`-std=c99` 에서는 선언이 있어 `deprecated` 경고 · 링크는 통과하고 링커가 한 줄 더 말한다** — `warning: the 'gets' function is dangerous and should not be used.` **glibc 는 `gets` 를 아직 내보낸다**(옛 판을 위해).
- ★★ **헤더 주석이 스스로 층을 가른다** — 「**ISO C11 과 C++14 에서 공식적으로 제거됐고 `_GNU_SOURCE` 목록에서도 뺐다 · 옛 ISO C · Unix · POSIX 판을 명시하면 남는다**」.
- ★ **C11 부록 K 의 `gets_s` 는 이 판에 없다** — 헤더에도 `libc.so.6` 에도 없다:

```text
===== echo "stdio.h 에서 gets_s 가 나오는 줄 $(grep -c gets_s /usr/include/stdio.h)"; echo "libc.so.6 의 gets_s 심볼 $(nm -D /lib/x86_64-linux-gnu/libc.so.6 | grep -c ' gets_s')" (exit=0) =====
stdio.h 에서 gets_s 가 나오는 줄 0
libc.so.6 의 gets_s 심볼 0
```

- ★ **왜 없앴나** — `gets` 는 **버퍼 크기를 받지 않는다.** 한 줄이 버퍼보다 길면 넘친다 — 막을 방법이 **호출자에게 없다.** 대체는 **`fgets(buf, sizeof buf, stdin)`**.

### (6) ★★★ `scanf("%s")` 의 넘침 · `%9s` · 반환값을 안 보는 루프

**언제 쓰나** — `scanf` 로 문자열·숫자를 받는 코드를 봤을 때.

```c
/* s48s.c */
#include <stdio.h>

int main(void) {
    char name[10];
    if (scanf("%s", name) == 1) printf("name = %s\n", name);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s48s.c -o x && printf 'abcdefghijklmnopqrstuvwxyz\n' | ASAN_OPTIONS=strip_path_prefix="$PWD/" ./x | sed -n '1,/^SUMMARY/p' (exit=1) =====
=================================================================
==1211369==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x75a0d470002a at pc 0x75a0d6c91ad0 bp 0x7ffdd9216610 sp 0x7ffdd9215d98
WRITE of size 27 at 0x75a0d470002a thread T0
    #0 0x75a0d6c91acf in scanf_common ../../../../src/libsanitizer/sanitizer_common/sanitizer_common_interceptors_format.inc:342
    #1 0x75a0d6ccd1f2 in __isoc99_vscanf ../../../../src/libsanitizer/sanitizer_common/sanitizer_common_interceptors.inc:1489
    #2 0x75a0d6ccdc40 in __isoc99_scanf ../../../../src/libsanitizer/sanitizer_common/sanitizer_common_interceptors.inc:1520
    #3 0x5880fbbf52ca in main s48s.c:5
    #4 0x75a0d682a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #5 0x75a0d682a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #6 0x5880fbbf5164 in _start (x+0x1164) (BuildId: 6e9bda1e1d9517e072387ab1ec4bff03d07a8f5f)

Address 0x75a0d470002a is located in stack of thread T0 at offset 42 in frame
    #0 0x5880fbbf5238 in main s48s.c:3

  This frame has 1 object(s):
    [32, 42) 'name' (line 4) <== Memory access at offset 42 overflows this variable
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-buffer-overflow ../../../../src/libsanitizer/sanitizer_common/sanitizer_common_interceptors_format.inc:342 in scanf_common
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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s48s9.c -o x ; printf 'abcdefghijklmnopqrstuvwxyz\n' | ./x (cc exit=0 · run exit=0) =====
[abcdefghi]
[jklmnopqr]
[stuvwxyz]
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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s48r.c -o x ; printf 'abc\n' | ./x (cc exit=0 · run exit=0) =====
scanf 반환 0 · n = -1
scanf 반환 0 · n = -1
scanf 반환 0 · n = -1
scanf 반환 0 · n = -1
scanf 반환 0 · n = -1
돈 횟수 5 · 다음 getchar() = 97
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s48r.c -o x ; printf '12 34\n' | ./x (cc exit=0 · run exit=0) =====
scanf 반환 1 · n = 12
scanf 반환 1 · n = 34
돈 횟수 2 · 다음 getchar() = -1
```

- ★★★ **`%s` 는 공백 전까지 전부 쓴다** — 26 글자 + 널 = **`WRITE of size 27`**, `name` 은 **`[32, 42)`**(10 바이트). ASan 이 `scanf` 의 가로채기 안에서 잡았다. ★ ASan 없이는 **조용히 스택을 덮는다** — 이 편은 보통 빌드의 출력을 **싣지 않았다**(미정의).
- ★★ **`%9s` 는 9 글자씩 끊어 받는다** — `[abcdefghi]` · `[jklmnopqr]` · `[stuvwxyz]`. 폭은 **널 자리를 뺀** 수다(`char[10]` 이면 9). **넘치지 않지만 잘린 줄을 여러 번 받는다** — 잘렸다는 표시는 없다.
- ★★★ **`abc` 에 `%d` — `scanf` 는 0 을 돌려주고 `abc` 를 안 먹는다** — `n` 은 그대로 `-1`, 다음 `scanf` 도 **같은 `a` 에서** 또 실패한다. **`!= EOF` 로 도는 루프는 영원히 돈다**(이 소스는 5 번 상한으로 멈췄다) · 그 뒤 `getchar()` 가 **`97`('a')** — 실패한 글자는 **입력에 남아 있다.**
- ★★ **`12 34` 는 1 · 1 · 그리고 `EOF`(루프 끝) · `getchar()` 가 `-1`** — 정상 입력에서는 이 루프도 멀쩡하다. **시험 입력이 좋으면 안 보인다.**
- ★★ **반환값의 뜻** — 「**대입한 항목 수**」이고, **첫 변환 전에 입력이 끝나면 `EOF`**. 조건은 **`== 기대한 개수`** 로 쓴다.

### (7) ★ 텍스트 모드 · 디렉토리 — 리눅스에서는

**언제 쓰나** — 윈도우에서 온 코드의 `"r"`/`"rb"`, 또는 **`fopen` 이 성공했으니 파일이다**라는 가정.

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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s48p.c -o x ; ./x (cc exit=0 · run exit=0) =====
"r" : 첫 줄 뒤 ftell = 4 · 끝 ftell = 7 · 첫 줄 끝 바이트 0d
"rb" : 첫 줄 뒤 ftell = 4 · 끝 ftell = 7 · 첫 줄 끝 바이트 0d
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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s48d.c -o x ; ./x (cc exit=0 · run exit=0) =====
fopen = ptr · errno = 0
fread = 0 · feof = 0 · ferror = 1 · errno = Is a directory
```

- ★★ **리눅스에서 `"r"` 과 `"rb"` 는 같다** — 첫 줄 뒤 `ftell` 4 · 끝 7 · 첫 줄 끝 바이트 `0d`(`\r` 이 그대로 남았다). ★ **표준은 텍스트 스트림에서 `ftell` 의 값을 「`fseek` 에 쓸 수 있는 미지정 정보」라고만** 적는다 — **바이트 오프셋이라는 것은 이 판의 구현**이다. 텍스트 모드에서 줄 끝을 바꾸는 구현(윈도우)에서는 두 줄이 갈릴 수 있다 — **이 편은 윈도우에서 돌리지 않았다.**
- ★★★ **디렉토리를 `fopen(…, "r")` 하면 `ptr`(성공)** 이다 — 실패는 **`fread` 에서** 온다: 0 · `ferror = 1` · `Is a directory`(`EISDIR`). **`fopen` 의 성공이 「읽을 수 있다」가 아니다.** ★ 이것은 **glibc · 리눅스의 동작**이다 — 표준은 디렉토리를 말하지 않는다.

## 문법 — 형태와 규칙

### 형태

(3)의 `s48w2.c` 와 (1)의 `fgetc-int` 가 이 절의 **실제로 컴파일되는 형태**다.

| 읽기 | 멈추는 조건 | 멈춘 뒤 |
|---|---|---|
| `fgets(buf, sizeof buf, f)` | ★ **`== NULL`** | ★★ `ferror(f)` 면 오류 · 아니면 끝 · 조각의 끝이 `'\n'` 인가 |
| `int c = fgetc(f)` | ★★★ **`c == EOF`**(`int` 에 받아서) | ★★ `ferror` / `feof` |
| `fread(buf, 1, n, f)` | ★ **`< n`** | ★★ `ferror` / `feof` |
| `scanf("%9s", s)` · `scanf("%d", &n)` | ★★★ **`!= 기대한 개수`** | ★★ `EOF` 면 입력 끝 · 0 이면 **매치 실패 · 그 글자는 남아 있다** |

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 결과 | 층 | 어느 절 |
|---|---|---|---|
| `while (!feof(f)) { fgets(…); 처리; }` | 경고 0 · **마지막 줄을 두 번** | ★★ 표준(`feof` 는 이미 부딪혔나) | (3) |
| `char c = fgetc(f)` | 경고 0(부호 있는 `char`) · **`0xFF` 에서 멈춤** / 부호 없는 `char` 는 **안 멈춤** | ★★★ 표준(`int` 반환) · 구현 정의(`char` 의 부호) | (1) · (2) |
| 멈춘 뒤 `ferror` 를 안 봄 | 경고 0 · **읽기 오류를 빈 입력으로** | ★★ 표준 | (1) |
| `gets(buf)` | gcc `-std=c11` **경고 · `exit=0`** · clang **에러** · 링커 경고 | ★★★ 표준(C11 제거) · 컴파일러 구현(진단 세기) | (5) |
| `scanf("%s", buf)` | 경고 0 · ASan **`stack-buffer-overflow` WRITE** | ★★★ UB | (6) |
| `while (scanf("%d", &n) != EOF)` | 경고 0 · **숫자 아닌 입력에서 영원히** | ★★ 표준(반환은 대입 수) | (6) |

### 규칙 불릿

- ★★★ **읽기 루프는 반환값으로 멈추고, 멈춘 뒤에 `ferror` → `feof` 를 묻는다.**
- ★★★ **`fgetc`·`getchar` 의 반환은 `int` 에 받는다.**
- ★★ **`fgets` 한 번은 한 줄이 아니다 — 끝이 `'\n'` 인 조각이 줄의 끝이다.**
- ★★ **`gets` 는 쓰지 않는다(C11 제거) · `%s` 에는 폭(`%9s`)을 준다 · `scanf` 는 반환값을 기대 개수와 견준다.**
- ★ **`fopen` 의 성공은 「읽을 수 있다」가 아니다** — 오류는 읽을 때 온다.

## 어디서 틀리나

### 1. ★★★ 「루프가 끝났으니 파일을 다 읽었다」

디렉토리 네 칸이 **빈 파일과 같은 반환**을 냈다((1)). `ferror` 를 안 보면 **오류가 빈 입력이 된다.**

### 2. ★★★ 「`char c = getchar()` 로 충분하다」

부호 있는 `char` 는 **`0xFF` 에서 멈추고**, 부호 없는 `char` 는 **끝에서 안 멈춘다**((2)). 둘 다 **`0xFF` 가 없는 시험 입력으로는 안 보이거나(앞) 곧바로 보인다(뒤).**

### 3. ★★ 「`while (!feof(f))` 가 자연스럽다」

**마지막 줄을 두 번** 처리했다((3)).

### 4. ★★ 「`-std=c11` 로 빌드하면 `gets` 가 막힌다」

gcc 13 은 **경고에 `cc exit=0`** 이었다((5)). `-pedantic-errors` 또는 `-Werror=implicit-function-declaration` 이 막았다.

### 5. ★★ 「`%9s` 면 안전하다」

넘치지는 않지만 **긴 입력을 조각으로 나눠 여러 번** 받았다 — 잘림을 말하지 않는다((6)).

### 6. ★ 「`fopen` 이 성공했으니 파일이다」

디렉토리도 `fopen` 이 **성공**했다((7)).

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 본체**다 — 끝과 오류를 가르는 방법 · `int` 반환 · `gets` 제거가 전부 표준 문장이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | ★★★ **끝과 오류에 같은 반환 · `feof`/`ferror` 로 가름** · `fgetc` 는 `unsigned char` 를 `int` 로 · `fgets` 는 n−1 과 널 · **끝이면 배열 그대로** · `scanf` 는 대입 수 · **C11 에서 `gets` 제거** | 격자 · (3) · (4) · (6) |
| ★★ **구현 정의** | 문서화 의무가 있다 | ★★★ **`char` 의 부호**(이 판 부호 있음) · 텍스트 스트림의 줄 끝 변환 · `ftell` 의 값의 뜻 | 부호 격자 · (7) |
| ★★ **glibc · POSIX · 리눅스** | 표준 밖의 선택 | ★★ **디렉토리 `fopen` 성공 · `fread` 가 `EISDIR`** · C11 판에서 `gets` 선언을 감춤 · **`gets` 를 아직 내보냄** · 텍스트와 이진이 같다 | (7) · (5) |
| ★★ **컴파일러 구현** | 도구의 선택 | ★★★ **gcc 13 은 암시적 선언을 경고로 · clang 18 은 에러로** · `-Wtype-limits` 는 부호 없는 판에서만 · 링커의 `gets` 경고 | (5) · (2) |
| **미명시** | 몇 가지 중 하나 | ★ **읽기 오류 뒤 `fgets` 배열의 내용** — 이 편은 **찍지 않았다** | — |
| ★★★ **UB** | 아무 일이나 | ★★★ **`scanf("%s")` · `gets` 의 넘침** — ASan 이 잡았다 · 보통 빌드의 결과는 싣지 않았다 | (6) |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★★ **`while (!feof(f))` · `ferror` 를 안 보는 루프 · `scanf` 반환 무시** — 전부 **경고 0** |
| ★★ **구현 정의** | ★★ **부호 있는 `char` 에 받은 `fgetc`** — 이 판 기본에서 **경고 0**(부호 없는 판만 `-Wtype-limits`) |
| ★★ **컴파일러 구현** | ★★ gcc 13 `-std=c11` 의 `gets` — **경고뿐 · `exit=0`** |
| ★★★ **UB** | ★★ `%s` 넘침은 **컴파일 경고 0** — ASan 이 **실행해야** 본다 |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **반환값은 「멈췄다」만 말한다** — 이유는 표시가 말한다(0 / 20).
  - ★★ **`char` 로 받은 사고는 기본값에서 조용하다** — `int` 에 받는다.
  - ★★ **크기를 모르는 입력 함수는 도구가 실행 전에 막지 못한다** — `fgets`·폭 있는 지정자로 바꾼다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 줄 단위 읽기 | ★★★ `fgets` + 끝 글자 확인 + 멈춘 뒤 `ferror` | `gets` · `while (!feof)` |
| 글자 단위 읽기 | ★★★ `int c = fgetc(f)` | `char c` |
| 이진 덩어리 | ★★ `fread` 의 반환 = 읽은 수 · `< n` 이면 `ferror`/`feof` | 반환 무시 |
| 단어 하나 | ★★ `scanf("%9s", buf)`(폭 = 크기 − 1) · 반환 `== 1` | `scanf("%s")` |
| 숫자 | ★★ `fgets` 로 줄 → 파싱([목록의 **51번 주제**](../51-stdlib-conversion-qsort-and-bsearch/)) | `while (scanf("%d") != EOF)` |
| 파일인지 확인 | ★ 읽기 오류를 처리하기(또는 POSIX `fstat`) | `fopen` 성공에 기대기 |

판단 규칙 두 줄.

- ★★★ **읽기가 멈추면 「끝인가 오류인가」를 반드시 한 번 묻는다 — 반환값은 대답하지 않는다.**
- ★★ **입력 함수를 고를 때 「이 함수는 버퍼 크기를 받는가」를 먼저 본다.**

## 핵심 문장

- ★★★ **EOF 대 오류 격자에서 EOF 만 본 코드가 오판한 칸 5 / 20, `feof`/`ferror` 로 본 코드는 0 / 20.**
- ★★★ **디렉토리는 `fopen` 이 성공하고 네 읽기가 전부 「0 · `ferror = 1`」 — 반환값은 빈 파일과 같았다.**
- ★★★ **`char` 로 받은 `fgetc` 는 `0xFF` 에서 멈췄고(1 / 4 바이트 · 두 표시 0), `-funsigned-char` 에서는 끝에서도 안 멈췄다(상한 100).**
- ★★ **`while (!feof(f))` 는 마지막 줄을 두 번 찍었다 — 실패한 `fgets` 뒤의 배열은 표준대로 그대로였다.**
- ★★★ **`gets` 는 gcc 13 `-std=c11` 에서 경고에 `cc exit=0`, clang 18 에서 에러 — 링커는 `dangerous` 경고를 냈다.**
- ★★ **`scanf("%s")` 는 `WRITE of size 27` 로 `char[10]` 을 넘었고, `%d` 에 `abc` 를 주면 0 을 돌려주고 글자를 남긴 채 같은 자리에서 계속 실패했다.**
- ★ **리눅스에서 `"r"` 과 `"rb"` 는 `ftell` 까지 같았다.**

## 관련 자료

- [47번 형제 — `<stdio.h>` 스트림 · 버퍼링 · 서식 출력](../47-stdio-streams-buffering-and-formatted-output/) — ★★ **선행.** 출력 쪽 스트림.
- [20번 형제 — 널 종단 문자열](../20-null-terminated-strings-and-string-literals/) — ★★ `fgets` 가 붙이는 널 · 널 없는 배열의 사고.
- [49번 형제 — `<string.h>` 문자열 함수와 함정](../49-string-functions-and-pitfalls/) — ★ 읽은 문자열의 복사 · 이어 붙이기.
- [46번 형제 — `errno`](../46-errno-and-error-return-conventions/) — ★ `ferror` 다음에 이유(`EISDIR`)를 읽는 순서.
- [목록의 **51번 주제**](../51-stdlib-conversion-qsort-and-bsearch/)(`<stdlib.h>` 변환) — ★★ 읽은 숫자를 `strtol` 로.

## 용어 풀이

> **`EOF`** — `<stdio.h>` 의 음수 `int` 매크로(이 판 `-1`). **끝과 오류에 같이** 쓰인다.\
> 예: `fgetc` 는 끝이든 오류든 `EOF`.

> **`feof` / `ferror` / `clearerr`** — 끝 표시를 읽는다 / 오류 표시를 읽는다 / 둘을 내린다.\
> 예: 디렉토리 `fread` 뒤 `ferror(f) == 1`.

> **`gets`** — 버퍼 크기 없이 한 줄을 읽던 함수. **C11 에서 제거**. glibc 는 옛 판을 위해 아직 내보내고 링커가 경고한다.\
> 예: `warning: the 'gets' function is dangerous and should not be used.`

> **`scanf` 의 폭** — `%9s` 의 9. **널을 뺀** 최대 글자 수.\
> 예: `char name[10]` 에는 `%9s`.

> **`-funsigned-char`** — `char` 를 부호 없는 타입으로 컴파일하는 gcc·clang 플래그. ARM 리눅스의 기본을 흉내 낼 때 쓴다.\
> 예: (2)의 두 줄.

## 더 들어가면

- ★★ **`getline`(POSIX)** — 버퍼를 **스스로 늘려** 한 줄 전체를 받는다. ★ **던지지 않았다.**
- ★ **`clearerr` 로 표시를 내린 뒤 다시 읽기** — 터미널 입력에서 Ctrl-D 뒤 계속 읽을 때. ★ **던지지 않았다.**
- ★ **부록 K 경계 검사 인터페이스 전체** — 이 판에 `gets_s` 가 없는 것만 확인했다((5)). ★ 다른 `_s` 함수는 **찾지 않았다.**
- ★ **읽기 오류 뒤 `fgets` 배열(미지정)** — 값을 찍지 않았다.
