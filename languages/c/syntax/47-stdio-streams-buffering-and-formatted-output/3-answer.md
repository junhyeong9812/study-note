# c/syntax/47 — `<stdio.h>` 스트림 · 버퍼링 · 서식 출력: 「**지정자는 타입과의 계약이고 틀리면 미정의다 — 그리고 출력이 「언제」 나가는지는 받는 쪽이 터미널이냐에 달렸다**」 — 정답

## 이 파일이 다시 싣는 소스

★ 1번의 경고 전문을 낸 소스를 다시 둔다.

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

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 지정자 격자 — **경고 난 칸 gcc 10 / 24 · clang 10 / 24 · 같은 열 줄 · `-Wno-format` 은 0 / 24 · 조용한 틀림은 `%lu`(`size_t`) · `%ld`(`ptrdiff_t`)** ★★★

**출력**

```text
===== 서식 지정자 격자 — 타입 8 × 지정자 3 × 컴파일러 설정 4 (exit=0) =====
타입 · 지정자         	gcc	gcc -Wno-format	clang	clang -Wno-format
size_t · %zu          	-	-	-	-
size_t · %d           	경고	-	경고	-
size_t · %lu          	-	-	-	-
long long · %lld      	-	-	-	-
long long · %d        	경고	-	경고	-
long long · %ld       	경고	-	경고	-
int64_t · PRId64      	-	-	-	-
int64_t · %d          	경고	-	경고	-
int64_t · %lld        	경고	-	경고	-
uint8_t · PRIu8       	-	-	-	-
uint8_t · %d          	-	-	-	-
uint8_t · %c          	-	-	-	-
ptrdiff_t · %td       	-	-	-	-
ptrdiff_t · %d        	경고	-	경고	-
ptrdiff_t · %ld       	-	-	-	-
void * · %p           	-	-	-	-
void * · %d           	경고	-	경고	-
void * · %lx          	경고	-	경고	-
double · %f           	-	-	-	-
double · %d           	경고	-	경고	-
double · %lf          	-	-	-	-
float · %f            	-	-	-	-
float · %d            	경고	-	경고	-
float · %lf           	-	-	-	-
(칸 = 그 줄에 warning: 이 났나 · 각 칸 $CC -std=c17 -c s47f.c 만 · -Wall 없음)
경고 난 칸 — gcc 10 / 24 · gcc -Wno-format 0 / 24 · clang 10 / 24 · clang -Wno-format 0 / 24
```

```text
===== gcc -std=c17 -c s47f.c -o /dev/null (cc exit=0) =====
s47f.c: In function ‘probe’:
s47f.c:9:14: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘size_t’ {aka ‘long unsigned int’} [-Wformat=]
    9 |     printf("%d\n", z);                  /* size_t · %d */
      |             ~^     ~
      |              |     |
      |              int   size_t {aka long unsigned int}
      |             %ld
s47f.c:12:14: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘long long int’ [-Wformat=]
   12 |     printf("%d\n", ll);                 /* long long · %d */
      |             ~^     ~~
      |              |     |
      |              int   long long int
      |             %lld
s47f.c:13:15: warning: format ‘%ld’ expects argument of type ‘long int’, but argument 2 has type ‘long long int’ [-Wformat=]
   13 |     printf("%ld\n", ll);                /* long long · %ld */
      |             ~~^     ~~
      |               |     |
      |               |     long long int
      |               long int
      |             %lld
s47f.c:15:14: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘int64_t’ {aka ‘long int’} [-Wformat=]
   15 |     printf("%d\n", i64);                /* int64_t · %d */
      |             ~^     ~~~
      |              |     |
      |              int   int64_t {aka long int}
      |             %ld
s47f.c:16:16: warning: format ‘%lld’ expects argument of type ‘long long int’, but argument 2 has type ‘int64_t’ {aka ‘long int’} [-Wformat=]
   16 |     printf("%lld\n", i64);              /* int64_t · %lld */
      |             ~~~^     ~~~
      |                |     |
      |                |     int64_t {aka long int}
      |                long long int
      |             %ld
s47f.c:21:14: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘ptrdiff_t’ {aka ‘long int’} [-Wformat=]
   21 |     printf("%d\n", pd);                 /* ptrdiff_t · %d */
      |             ~^     ~~
      |              |     |
      |              int   ptrdiff_t {aka long int}
      |             %ld
s47f.c:24:14: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘void *’ [-Wformat=]
   24 |     printf("%d\n", vp);                 /* void * · %d */
      |             ~^     ~~
      |              |     |
      |              int   void *
      |             %p
s47f.c:25:15: warning: format ‘%lx’ expects argument of type ‘long unsigned int’, but argument 2 has type ‘void *’ [-Wformat=]
   25 |     printf("%lx\n", vp);                /* void * · %lx */
      |             ~~^     ~~
      |               |     |
      |               |     void *
      |               long unsigned int
      |             %p
s47f.c:27:14: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘double’ [-Wformat=]
   27 |     printf("%d\n", d);                  /* double · %d */
      |             ~^     ~
      |              |     |
      |              int   double
      |             %f
s47f.c:30:14: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘double’ [-Wformat=]
   30 |     printf("%d\n", f);                  /* float · %d */
      |             ~^     ~
      |              |     |
      |              int   double
      |             %f
```

```text
===== clang -std=c17 -c s47f.c -o /dev/null (cc exit=0) =====
s47f.c:9:20: warning: format specifies type 'int' but the argument has type 'size_t' (aka 'unsigned long') [-Wformat]
    9 |     printf("%d\n", z);                  /* size_t · %d */
      |             ~~     ^
      |             %zu
s47f.c:12:20: warning: format specifies type 'int' but the argument has type 'long long' [-Wformat]
   12 |     printf("%d\n", ll);                 /* long long · %d */
      |             ~~     ^~
      |             %lld
s47f.c:13:21: warning: format specifies type 'long' but the argument has type 'long long' [-Wformat]
   13 |     printf("%ld\n", ll);                /* long long · %ld */
      |             ~~~     ^~
      |             %lld
s47f.c:15:20: warning: format specifies type 'int' but the argument has type 'int64_t' (aka 'long') [-Wformat]
   15 |     printf("%d\n", i64);                /* int64_t · %d */
      |             ~~     ^~~
      |             %ld
s47f.c:16:22: warning: format specifies type 'long long' but the argument has type 'int64_t' (aka 'long') [-Wformat]
   16 |     printf("%lld\n", i64);              /* int64_t · %lld */
      |             ~~~~     ^~~
      |             %ld
s47f.c:21:20: warning: format specifies type 'int' but the argument has type 'ptrdiff_t' (aka 'long') [-Wformat]
   21 |     printf("%d\n", pd);                 /* ptrdiff_t · %d */
      |             ~~     ^~
      |             %td
s47f.c:24:20: warning: format specifies type 'int' but the argument has type 'void *' [-Wformat]
   24 |     printf("%d\n", vp);                 /* void * · %d */
      |             ~~     ^~
s47f.c:25:21: warning: format specifies type 'unsigned long' but the argument has type 'void *' [-Wformat]
   25 |     printf("%lx\n", vp);                /* void * · %lx */
      |             ~~~     ^~
s47f.c:27:20: warning: format specifies type 'int' but the argument has type 'double' [-Wformat]
   27 |     printf("%d\n", d);                  /* double · %d */
      |             ~~     ^
      |             %f
s47f.c:30:20: warning: format specifies type 'int' but the argument has type 'float' [-Wformat]
   30 |     printf("%d\n", f);                  /* float · %d */
      |             ~~     ^
      |             %f
10 warnings generated.
```

**왜 그런가**

- ★★★ **`%d` 일곱 줄**(`uint8_t` 만 빼고)은 인자의 (승격된) 타입이 `int` 가 아니다 — 두 컴파일러가 잡았다.
- ★★ **`long long · %ld` · `int64_t · %lld` 도 잡혔다** — 이 판에서 `long` 과 `long long` 은 **크기가 같지만 다른 타입**이다. `int64_t` 는 이 판에서 `long` 이다.
- ★★★ **`size_t · %lu` · `ptrdiff_t · %ld` 는 조용했다** — 이 판(LP64)에서 **타입이 정확히 같다.** LLP64 에서는 `size_t` 가 `unsigned long long` 이라 같은 줄이 틀린다. **이식성 있는 답은 `%zu` · `%td`.**
- ★★ **`uint8_t · %d` · `%c` · `float · %lf` 는 틀림이 아니다** — 승격(9번).

### 2. 맞는 지정자의 출력 ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s47ok.c -o x ; ./x (cc exit=0 · run exit=0) =====
16 | -9000000000 | -9223372036854775808 | 200 200 | -7
0.100000 0.10000000000000001 | 0.100000 0.10000000149011612
%p 로 NULL = (nil)
```

**왜 그런가**

- ★★ **`float` 은 가변 인자로 넘길 때 `double` 로 승격**된다 — 그래서 `%f` 가 맞다. 값은 **`float` 의 `0.1` 근사**(`0.10000000149011612`) 그대로다. `double` 의 `0.1` 은 `0.10000000000000001`.
- ★ **`%p` 의 널이 `(nil)`** 인 것은 glibc 의 표기다(구현 정의).

### 3. 버퍼링 격자 — **`s47b1.c` 는 세 쪽 다 `bac` · `s47b2.c` 만 파이프·파일에서 `b/a/c/` · 갈린 칸 2 / 8 · stderr 은 늘 `write` 1 번** ★★★

**출력**

```text
===== 버퍼링 격자 — 프로그램 4 × 받는 쪽 3 (stdout 과 stderr 을 한 곳으로) (exit=0) =====
프로그램                  	받는 쪽         	보이는 순서	write(1, …)	write(2, …)
s47b1.c                   	터미널          	bac/	1	1
s47b1.c                   	파이프          	bac/	1	1
s47b1.c                   	파일            	bac/	1	1
s47b2.c                   	터미널          	a/b/c/	2	1
s47b2.c                   	파이프          	b/a/c/	1	1
s47b2.c                   	파일            	b/a/c/	1	1
s47b3.c                   	터미널          	a/b/c/	2	1
s47b3.c                   	파이프          	a/b/c/	2	1
s47b3.c                   	파일            	a/b/c/	2	1
s47b4.c                   	터미널          	a/b/c/	2	1
s47b4.c                   	파이프          	a/b/c/	2	1
s47b4.c                   	파일            	a/b/c/	2	1
(터미널 = script -qc "strace -e trace=write -o st ./x" /dev/null · 파이프 = strace … ./x 2>&1 | cat · 파일 = strace … ./x > 파일 2>&1 · 보이는 순서의 / 는 줄바꿈)
터미널과 보이는 순서가 갈린 칸 2 / 8
터미널과 write(1, …) 수가 갈린 칸 2 / 8
```

**왜 그런가**

- ★★★ **`s47b1.c` 에서는 `a` 가 개행 없이 버퍼에 남는다** — 터미널(줄 버퍼)이든 파이프·파일(완전 버퍼)이든 `a` 는 **`c\n` 과 함께** 나간다. 그래서 **세 쪽 다 `bac`** · `write(1, …)` 1 번이다. **이 예제는 두 모드를 가르지 못한다.**
- ★★★ **`s47b2.c` 에서는 줄 버퍼가 `a\n` 에서 바로 내보낸다** — 터미널은 `a/b/c/` · `write(1, …)` 2 번. 파이프·파일은 완전 버퍼라 `a\n` 과 `c\n` 이 **끝까지 모였다가** `exit` 에서 한 번 — 그 사이 stderr 의 `b\n` 이 **먼저** 나간다.
- ★★ **`s47b3.c`(`_IOLBF`) · `s47b4.c`(`fflush`)** 는 프로그램이 모드·시점을 정해 **받는 쪽과 무관하게** `a/b/c/` 다.

### 4. 만 바이트 — **`write(1, …)` 세 번(4096 · 4096 · 1808) · `write(2, …)` 한 번 · 둘째와 셋째 사이** ★★

**출력**

```text
===== gcc -std=c17 s47b5.c -o x && strace -e trace=write -o st.txt ./x > out.txt 2>/dev/null; wc -c < out.txt; sed -E 's/"x+"(\.\.\.)?/"x…"/' st.txt (exit=0) =====
10000
write(1, "x…", 4096) = 4096
write(1, "x…", 4096) = 4096
write(2, "err\n", 4)                    = 4
write(1, "x…", 1808) = 1808
+++ exited with 0 +++
```

**왜 그런가**

- ★★ **파일로 가는 stdout 의 버퍼는 4096 바이트**였다 — 찰 때마다 한 번, 남은 1808 은 `exit` 가 비웠다.
- ★★ **stderr 은 조각 셋을 `write` 한 번으로** 냈다 — 「버퍼 없음」이 「조각마다」가 아니었다(glibc).
- ★ **fd 2 의 `write` 는 stdout 버퍼가 두 번 찬 뒤**에 끼었다 — `putchar` 만 번이 끝나고 `fprintf(stderr, …)` 가 불린 시점에 **stdout 버퍼에는 1808 바이트가 남아 있었다.**

### 5. stdio 의 판정 — **파일은 `S_IFREG` · 터미널은 `S_IFCHR` 에서 끝 · `/dev/null` 은 `ioctl(TCGETS)` 가 `ENOTTY`** ★★

**출력**

```text
===== gcc -std=c17 s47b2.c -o x && strace -e trace=fstat,ioctl -o st.txt ./x > out.txt 2>/dev/null; grep -E '^(fstat|ioctl)\(1,' st.txt (exit=0) =====
fstat(1, {st_mode=S_IFREG|0664, st_size=0, ...}) = 0
```

```text
===== gcc -std=c17 s47b2.c -o x && script -qc 'strace -e trace=fstat,ioctl -o st.txt ./x' /dev/null > /dev/null; grep -E '^(fstat|ioctl)\(1,' st.txt | sed -E 's/makedev\((0x[0-9a-f]+), 0x[0-9a-f]+\)/makedev(\1, …)/' (exit=0) =====
fstat(1, {st_mode=S_IFCHR|0620, st_rdev=makedev(0x88, …), ...}) = 0
```

```text
===== gcc -std=c17 s47b2.c -o x && strace -e trace=fstat,ioctl -o st.txt ./x > /dev/null 2>/dev/null; grep -E '^(fstat|ioctl)\(1,' st.txt | sed -E 's/0x7[0-9a-f]{7,}/0x…/' (exit=0) =====
fstat(1, {st_mode=S_IFCHR|0666, st_rdev=makedev(0x1, 0x3), ...}) = 0
ioctl(1, TCGETS, 0x…)        = -1 ENOTTY (Inappropriate ioctl for device)
```

**왜 그런가**

- ★★ **stdio 가 가른 것은 「fd 1 이 무엇인가」** 다 — 정규 파일이면 비대화형. 문자 장치면 한 번 더 따지는데, **의사 터미널(주 번호 `0x88`)은 `ioctl` 없이** 대화형으로, **`/dev/null` 은 `ioctl(TCGETS)` 가 실패해** 비대화형으로 쳤다.
- ★ 이 판정법이 곧 표준이 「구현 정의」라고 적은 **「무엇이 대화형 장치인가」의 이 판 답**이다. ★ 어느 문자 장치를 `ioctl` 없이 치는지의 규칙은 **glibc 소스로 확인하지 않았다.**

### 6. 표준의 약속 — **「stderr 은 완전 버퍼가 아니다 · stdin/stdout 은 대화형이 아니라고 판정될 수 있을 때만 완전 버퍼」 · 「터미널이면 줄 버퍼」는 표준이 아니다** ★★★

- ★★★ N3220 은 이 한 문장만 적는다 — 「**처음 열린 표준 오류 스트림은 완전 버퍼가 아니다. 표준 입력과 표준 출력은 대화형 장치를 가리키지 않는다고 판정될 수 있을 때, 그리고 그때만 완전 버퍼다.**」
- ★★ **대화형일 때 줄 버퍼인지 버퍼 없음인지는 적지 않는다** — 「이 특성의 지원은 구현 정의」. **줄 버퍼는 glibc 의 선택**이다.
- ★★ **「무엇이 대화형 장치인가」도 구현 정의**다 — 적합성 절이 그렇게 적는다. 이 판의 답이 5번이다.

### 7. 틀린 지정자의 출력 — **근거가 못 된다 · 미정의 동작의 한 판이라 싣지 않았다** ★★

- ★★ **맞는 값처럼 보여도 「`%d` 도 된다」의 근거가 아니다** — 지정자와 타입이 안 맞으면 **미정의 동작**이다. [36번 형제](../36-variadic-functions-stdarg/)의 `printf("%d", 3.0)` 은 `3` 을 **한 판도** 안 찍었다(`0 / 10`) — `double` 은 다른 레지스터로 가기 때문이다.
- ★ **이 편이 틀린 줄을 실행하지 않은 이유** — 미정의 동작의 출력을 **「결과」로 실으면** 독자가 그것을 약속으로 읽는다. 창은 **경고**로 충분했다.

### 8. 경고 없는 틀림 — **이 판에서 타입이 같다 · LLP64 에서 깨진다 · gcc 의 제안은 `%ld`(이 판의 답이지 이식성의 답이 아니다) · `-Wall` 없는 gcc 칸은 배포판 specs 가 정했다** ★★

**출력**

```text
===== gcc -dumpspecs | grep -o '%{!Wformat:%{!Wformat=2:%{!Wformat=0:%{!Wall:-Wformat} %{!Wno-format-security:-Wformat-security}}}}' (exit=0) =====
%{!Wformat:%{!Wformat=2:%{!Wformat=0:%{!Wall:-Wformat} %{!Wno-format-security:-Wformat-security}}}}
```

**왜 그런가**

- ★★ **`size_t` = `unsigned long`, `ptrdiff_t` = `long`**(이 판) — 지정자와 **타입이 같으니** 경고할 거리가 없다. **윈도우(LLP64)** 는 둘 다 `long long` 계열이라 같은 줄이 **틀린 지정자**가 된다.
- ★★ **gcc 는 `size_t · %d` 에 `%ld` 를 제안했다**(1번 전문) — **이 판의 타입에서 나온 제안**이다. 이식성 있는 답은 **`%zu`**.
- ★★★ **Ubuntu 의 gcc specs 가 「`-Wall` 이 없으면 `-Wformat` 을 넣어라」를 박아 두었다** — 1번 gcc 열의 10 / 24 는 **이 배포판 gcc 의 성질**이다.

### 9. 승격 — **`uint8_t` 는 `int` 로, `float` 은 `double` 로 넘어간다 · `%lf` 는 C99 부터 `%f` 와 같다** ★★

- ★★ **가변 인자 자리에서는 기본 인자 승격**이 일어난다 — `uint8_t` 는 `int` 로 넘어가므로 **`%d` 가 받는 타입과 맞다.** `PRIu8` 은 `"u"` 로 펼쳐진다(`unsigned int` 로 읽는다 — 값이 두 타입에 다 들어가 문제없다).
- ★★ **`float` 은 `double` 로 넘어가므로 `%f`** 다. **`%lf` 의 `l` 은 `f` 에 아무 효과가 없다**(C99 부터). 그래서 1번 격자의 `float · %lf` 가 조용했다.

### 10. 끝날 때 — **`exit` 는 비우고 `_exit` 은 안 비운다 · Go `bufio` 는 `_exit` 쪽** ★★

- ★★ **`exit`(과 `main` 의 반환)은 열린 출력 스트림을 비운다**(표준) — 3번의 파이프·파일 판에서 **마지막 `write(1, …)`** 가 그것이다.
- ★★ **`_exit` 은 안 비운다** — [Go 44](../../../go/syntax/44-os-bufio-and-io-copy/)가 C 프로그램으로 **`exit` 18 바이트 · `_exit` 0 바이트**를 이미 쟀다. **Go 의 `bufio` 는 끝날 때 아무도 안 비워 주므로 `_exit` 쪽**이다(`Flush` 를 불러야 나간다).

### 11. 다섯 층과 경계 — **지정자는 표준 · 버퍼링 판정은 구현 정의 · 줄 버퍼와 4096 은 glibc · `-Wformat` 기본값은 배포판** ★★

| 층 | 이 주제에서 |
|---|---|
| ★★★ **표준** | ★★★ 지정자 불일치는 UB · 승격 · stderr 은 완전 버퍼 아님 · 비대화형이면 stdout 완전 버퍼 · `exit` 는 비운다 |
| ★★ **구현 정의** | ★★★ 무엇이 대화형 장치인가 · 버퍼링 특성 · `%p` 표기 · `size_t` 등의 기본 타입 |
| ★★ **glibc** | ★★ 터미널이면 줄 버퍼 · 4096 · stderr `fprintf` 한 번 = `write` 한 번 |
| ★★ **컴파일러 구현(배포판)** | ★★★ Ubuntu gcc specs 의 `-Wformat` · gcc 의 제안 줄 |
| ★★★ **UB** | ★★★ 틀린 지정자의 출력(싣지 않음) |

- ★ **입력 · 파일 · `EOF`** 는 [48번 형제](../48-stdio-input-and-files/)가 정본이다.

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s47f.c` | ★★★ **지정자 격자 96칸 · 10 / 24 · 10 / 24 · 0 / 24 · 0 / 24** · 경고 전문 둘 · specs | 4 · 2 · 1 |
| `s47ok.c` | ★★ 맞는 지정자의 값 | 1 |
| `s47b1.c`\~`s47b4.c` | ★★★ **버퍼링 격자 12칸 · 2 / 8 · 2 / 8** | 12 |
| `s47b2.c` | ★★ `fstat`/`ioctl` 세 판 | 3 |
| `s47b5.c` | ★★ 4096 · 4096 · 1808 | 1 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. **이 편의 블록은 정규화 없이 전부 동일**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **3번 · 4번 · 5번** — glibc 2.39 의 대화형 판정 · 줄 버퍼 · 4096 바이트.
- ★★★ **8번** — Ubuntu gcc 의 specs.
- ★★ **1번의 조용한 두 줄** — LP64 의 타입 정의.

**지정자와 타입이 안 맞으면 미정의라는 것 · 승격 · stderr 이 완전 버퍼가 아니라는 것 · 비대화형 stdout 이 완전 버퍼라는 것은 구현 의존이 아니다.**\
어느 C 구현에서도 같다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — 틀린 지정자의 출력(미정의 — 일부러 싣지 않음) · 형식 문자열이 변수인 판 · `%n` · `stdbuf`.
- ★ **못 잰 것** — **진짜 터미널**(의사 터미널 `script -qc` 로 대신했다).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **5번** — glibc 가 대화형 판정을 바꾸면.
- ★ **8번** — 배포판이 specs 를 바꾸면.

## 실행 환경

이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **clang 18.1.3** · **glibc 2.39** · **strace 6.8** ·
x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
소스는 `s47f.c` · `s47ok.c` · `s47b1.c`\~`s47b5.c` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
★★★ **본체 창은 둘** — 지정자 격자(컴파일 진단)와 버퍼링 격자(`strace` 의 `write` 수).
★★ **흔들리는 칸** — 없다(`strace` 의 PID 는 안 찍었고 주소·터미널 부 번호는 배너의 `sed` 로 가렸다). 정규화 규칙은 기본 넷뿐이다.
