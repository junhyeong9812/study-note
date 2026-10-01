# c/syntax/48 — `<stdio.h>` 입력과 파일: 「**읽기 함수의 반환값은 「멈췄다」만 말한다 — 끝이었는지 고장이었는지는 멈춘 뒤에 `feof`·`ferror` 에게 따로 물어야 한다**」 — 정답

## 이 파일이 다시 싣는 소스

★ 9번은 질문 파일에 없는 `s48f.c` 와 `s48w2.c` 를 쓴다.

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

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. EOF 대 오류 격자 — **디렉토리 네 칸은 「0 · `ferror` 1」 · `char` 로 받은 `0xFF` 는 1 바이트에서 두 표시 0 · EOF 만 본 코드의 오판 5 / 20 · `feof`/`ferror` 는 0 / 20 · 디렉토리 `fopen` 은 성공** ★★★

**출력**

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

**왜 그런가**

- ★★★ **반환값은 끝과 오류에 같다** — 디렉토리 칸의 `NULL` · `EOF` · `0` 은 **빈 파일 칸과 한 글자도 같다.** 가르는 것은 **`ferror = 1`** 뿐이다.
- ★★★ **`char` 로 받은 `fgetc` 는 `0xFF` 에서 멈췄다** — `255` 가 부호 있는 `char` 에서 `-1` 이 되어 `EOF` 와 같아졌다. **끝도 오류도 아니라서 두 표시가 0** 이다 — `feof`/`ferror` 로 보는 코드는 적어도 **「끝이라고 틀리게 말하지는」** 않는다.
- ★★ **디렉토리를 `"rb"` 로 `fopen` 하면 성공**한다(glibc · 리눅스) — 실패는 읽기에서 온다(6번).

### 2. 부호 격자 — **부호 있는 `char` 는 `0xFF` 에서 멈춤 · 부호 없는 `char` 는 두 입력 다 상한 100 · 경고는 `-funsigned-char` 판에서만 `-Wtype-limits`** ★★

**출력**

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

**왜 그런가**

- ★★★ **부호 없는 `char` 에서 `EOF`(-1)는 `255` 가 된다** — `c != EOF` 에서 `c` 는 `int` 로 승격돼 `255 != -1`, **늘 참.** 끝에 부딪혀 `feof = 1` 인데도 루프는 상한까지 돌았다.
- ★★ **gcc 는 그 판에서만 「비교가 늘 참」이라고 말한다** — 부호 있는 판(이 머신 기본)은 **경고 0**(1번 소스의 `48-a-gcc`).

### 3. `while (!feof(f))` — **`1: l1` · `2: l2` · `3: l2` · 경고 0** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s48w.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s48w.c -o x ; ./x (cc exit=0 · run exit=0) =====
1: l1
2: l2
3: l2
```

**왜 그런가**

- ★★ **`feof` 는 「이미 끝에 부딪혔나」** 다 — 둘째 줄을 읽은 뒤에는 아직 부딪히지 않았다. 셋째 `fgets` 가 끝에 부딪혀 `NULL` 을 돌려주지만 코드는 **반환을 안 보고** `line` 을 찍는다.
- ★ **그 `line` 이 둘째 줄 그대로인 것은 표준의 약속**이다 — 「아무것도 못 읽고 끝이면 배열은 그대로」.

### 4. `gets` — **gcc `-std=c11` 경고 · `exit=0` · `-pedantic-errors` `exit=1` · clang 에러 `exit=1` · `-std=c99` 는 `deprecated` + 링커의 `dangerous` 경고 · `exit=0`** ★★★

**출력**

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

**왜 그런가**

- ★★★ **C11 판에서 glibc 헤더는 `gets` 선언을 감춘다** — 그래서 호출은 **암시적 선언**이 되고, gcc 13 과 gcc-12 는 그것을 **경고로만** 낸다(`exit=0`). clang 18 은 **에러**다. 같은 표준 · 같은 헤더에서 **진단의 세기가 컴파일러마다** 달랐다.
- ★★ **`-std=c99` 에서는 선언이 보여 `deprecated`**, 링크는 되고 **링커가 `warning: the 'gets' function is dangerous and should not be used.`** 를 한 줄 더 찍는다 — glibc 가 `gets` 를 아직 내보내며 **경고 표식을 심어 두었다.**

### 5. `scanf` 셋 — **`%s`: `stack-buffer-overflow` · `WRITE of size 27` · `'name'` · `%9s`: 9 글자씩 세 번 · `abc`: 반환 0 이 다섯 번 · `n = -1` · 다음 `getchar()` 97 · `12 34`: 1 · 1 · `getchar()` -1** ★★★

**출력**

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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s48s9.c -o x ; printf 'abcdefghijklmnopqrstuvwxyz\n' | ./x (cc exit=0 · run exit=0) =====
[abcdefghi]
[jklmnopqr]
[stuvwxyz]
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

**왜 그런가**

- ★★★ **`%s` 는 버퍼 크기를 모른다** — 26 글자와 널, 27 바이트를 `[32, 42)`(10 바이트)에 썼다.
- ★★ **`%9s` 는 널 자리를 남기고 9 글자까지** — 한 줄이 조각 셋으로 왔다. 잘렸다는 표시는 없다.
- ★★★ **`%d` 가 `a` 에서 매치에 실패하면 `a` 는 입력에 남는다** — 다음 `scanf` 도 같은 `a` 에서 실패한다. 반환은 **0**(대입 0 개)이지 `EOF` 가 아니라서 **`!= EOF` 루프는 끝나지 않는다.**

### 6. 텍스트 모드 · 디렉토리 — **`"r"` 과 `"rb"` 가 `ftell` 4 · 7 · `0d` 로 같다 · 디렉토리 `fopen` 은 `ptr`, `fread` 가 0 · `ferror` 1 · `Is a directory`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s48p.c -o x ; ./x (cc exit=0 · run exit=0) =====
"r" : 첫 줄 뒤 ftell = 4 · 끝 ftell = 7 · 첫 줄 끝 바이트 0d
"rb" : 첫 줄 뒤 ftell = 4 · 끝 ftell = 7 · 첫 줄 끝 바이트 0d
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s48d.c -o x ; ./x (cc exit=0 · run exit=0) =====
fopen = ptr · errno = 0
fread = 0 · feof = 0 · ferror = 1 · errno = Is a directory
```

**왜 그런가**

- ★★ **리눅스는 텍스트 모드에서 줄 끝을 바꾸지 않는다** — `\r` 이 그대로 남았다(`0d`). 표준은 텍스트 스트림의 `ftell` 값을 「**미지정 정보**」라고만 적는다 — 바이트 오프셋인 것은 **이 판의 구현**이다.
- ★★ **디렉토리 `fopen` 의 성공 · `fread` 의 `EISDIR`** 은 glibc · 리눅스의 동작이다. `errno` 는 **`ferror` 를 확인한 뒤** 읽었다([46번 형제](../46-errno-and-error-return-conventions/)의 순서).

### 7. EOF 와 오류 — **셋 다 같은 반환(`NULL` · `EOF` · 적은 수) · 표준 각주: 「`feof` 와 `ferror` 로 가를 수 있다」 · `feof` 는 이미 부딪혔나** ★★★

- ★★★ **`fgets`** — 끝(못 읽음)이면 `NULL`(배열 그대로), 오류면 `NULL`(배열 미지정). **`fgetc`** — 끝이면 끝 표시 + `EOF`, 오류면 오류 표시 + `EOF`. **`fread`** — 둘 다 **요청보다 적은 수**. 표준 각주가 처방을 적는다 — 「**파일 끝과 읽기 오류는 `feof` 와 `ferror` 로 가를 수 있다.**」
- ★★ **`while (!feof(f))` 가 한 번 더 도는 이유** — `feof` 는 **읽기가 끝에 부딪힌 뒤에야** 선다. 마지막 줄을 **성공적으로** 읽은 직후에는 아직 0 이다.

### 8. `fgetc` 의 `int` — **257 가지 값을 담으려면 `char` 보다 넓어야 한다 · 부호 있으면 데이터에서 멈추고 없으면 끝에서 안 멈춘다** ★★

- ★★ **바이트 256 가지 + `EOF` 하나 = 257 가지** — `unsigned char` 를 `int` 로 바꿔 주고(`0`\~`255`), `EOF` 는 그 밖의 음수다. **`char` 에 넣는 순간 한 가지가 겹친다.**
- ★★ **부호 있는 `char`** — `0xFF` 가 `-1` 이 되어 **데이터 한가운데서 멈춘다**(조용 · 경고 0). **부호 없는 `char`** — `EOF` 가 `255` 가 되어 **끝에서 안 멈춘다**(무한 루프 · `-Wtype-limits` 가 말해 준다).

### 9. `fgets` 의 두 경계 — **개행 없는 마지막 줄도 돌려준다 · 긴 줄은 n−1 글자씩 조각 · 끝이 `'\n'` 인 조각이 줄의 끝** ★★

**출력**

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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s48w2.c -o x ; ./x (cc exit=0 · run exit=0) =====
1: l1
2: l2
```

**왜 그런가**

- ★★ **마지막 줄 `xy` 는 개행 없이 왔다** — `fgets` 는 개행 **또는 파일 끝** 뒤에서 멈춘다. 1번 격자의 `s48-nonl.txt` 도 5 바이트를 다 받았다.
- ★★ **버퍼(5)보다 긴 줄은 4 글자씩** — `[abcd]` · `[efgh]` · `[ij]`. **끝 글자가 `'\n'` 인가**로 「줄 전체인가」를 가르고, 아니면 **다음 `fgets` 가 `NULL` 인가**로 「마지막 줄인가 · 긴 줄인가」를 가른다.

### 10. `scanf` 의 반환 — **0 = 첫 항목부터 매치 실패(글자는 남음) · `EOF` = 첫 변환 전에 입력이 끝남 · `!= EOF` 는 0 을 통과시킨다** ★★

- ★★ **`scanf` 는 대입한 항목 수**를 돌려준다. 5번의 `abc` 는 **0**, `12 34` 의 끝은 **`EOF`**.
- ★★ **`!= EOF` 로 돌면 0 이 계속 통과한다** — 숫자가 아닌 글자 하나가 **영원히 루프를 붙잡는다.** 조건은 **`== 1`**(기대 개수)로 쓴다.
- ★ **매치에 실패한 글자는 입력에 남는다** — 5번 뒤 `getchar()` 가 `97`('a').

### 11. 다섯 층과 경계 — **표준은 끝·오류 가르기 · `int` 반환 · `gets` 제거 · `char` 의 부호는 구현 정의 · 디렉토리 동작은 glibc · 진단 세기는 컴파일러** ★★

| 층 | 이 주제에서 |
|---|---|
| ★★★ **표준** | ★★★ 끝과 오류의 같은 반환 · `feof`/`ferror` · `int` 반환 · `fgets` 의 n−1 · `scanf` 의 대입 수 · C11 `gets` 제거 |
| ★★ **구현 정의** | ★★ `char` 의 부호 · 텍스트 스트림의 줄 끝 · `ftell` 의 뜻 |
| ★★ **glibc · 리눅스** | ★★ 디렉토리 `fopen` 성공 · `EISDIR` · `gets` 를 감추고도 내보냄 |
| ★★ **컴파일러 구현** | ★★★ `gets` 의 암시적 선언을 gcc 는 경고 · clang 은 에러 |
| ★★★ **UB** | ★★★ `%s` · `gets` 의 넘침 |

- ★ **읽은 문자열 다루기**는 [49번 형제](../49-string-functions-and-pitfalls/), **숫자 파싱**은 [목록의 **51번 주제**](../51-stdlib-conversion-qsort-and-bsearch/)가 정본이다.

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s48a.c` | ★★★ **EOF 대 오류 격자 20칸 · 5 / 20 · 0 / 20 · 1 / 20** · 부호 격자 8칸 · 경고 3 | 20 · 8 · 3 |
| `s48w.c` · `s48w2.c` | ★★ `while (!feof)` 대 반환값 조건 | 2 |
| `s48f.c` | ★★ 긴 줄 · 개행 없는 끝 | 1 |
| `s48g.c` | ★★★ `gets` 다섯 판 · 헤더 주석 · `gets_s` 판별 | 5 · 1 · 1 |
| `s48s.c` · `s48s9.c` · `s48r.c` | ★★★ ASan 1 · 실행 3 | 4 |
| `s48p.c` · `s48d.c` | ★★ 텍스트/이진 · 디렉토리 | 2 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. **흔들린 칸은 ASan 리포트의 PID · 주소뿐**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **1번 · 6번의 디렉토리 칸** — glibc · 리눅스.
- ★★★ **4번의 종료 코드** — gcc 13 · gcc-12 · clang 18 의 암시적 선언 처리(다른 판은 이 머신에 없다).
- ★★ **2번** — x86-64 의 부호 있는 `char`. **6번** — 리눅스의 텍스트 모드.

**끝과 오류를 `feof`/`ferror` 로 가른다는 것 · `fgetc` 가 `int` 를 돌려준다는 것 · C11 이 `gets` 를 없앴다는 것은 구현 의존이 아니다.**\
어느 C 구현에서도 같다.

**안 돌려 본 것 / 못 잰 것**

- **못 잰 것** — gcc 14 이후 판 · ARM 리눅스 · 윈도우의 텍스트 모드(이 머신에 없다).
- **안 돌려 본 것** — `getline` · `clearerr` 뒤 재읽기 · 읽기 오류 뒤 `fgets` 배열의 내용(미지정 — 일부러).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **4번** — 컴파일러가 암시적 선언을 기본 에러로 바꾸면 gcc 칸이 뒤집힌다.
- ★ **1번 디렉토리 칸** — glibc 가 디렉토리 `fopen` 을 막으면.

## 실행 환경

이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **clang 18.1.3** · **glibc 2.39** ·
x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
소스는 `s48a.c` · `s48d.c` · `s48f.c` · `s48g.c` · `s48p.c` · `s48r.c` · `s48s.c` · `s48s9.c` · `s48w.c` · `s48w2.c` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
★★★ **본체 창은 EOF 대 오류 격자** — 입력 5 × 읽기 4.
★★ **흔들리는 칸** — ASan 리포트의 PID · 주소(정규화 기본 규칙). 나머지는 정규화 없이 같다.
