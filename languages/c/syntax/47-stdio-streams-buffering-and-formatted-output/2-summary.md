# c/syntax/47 — `<stdio.h>` 스트림 · 버퍼링 · 서식 출력: 「**지정자는 타입과의 계약이고 틀리면 미정의다 — 그리고 출력이 「언제」 나가는지는 받는 쪽이 터미널이냐에 달렸다**」 — 정리 (힌트)

★★★ **본체는 두 창이다.** 지정자는 **① 컴파일 진단** — 틀린 지정자의 **출력은 미정의라 싣지 않는다.** 버퍼링은 **`strace` 가 센 `write` 호출 수** — 보이는 순서는 그 결과다.
★★★ 지정자 격자에서 **경고 난 칸 — gcc 10 / 24 · clang 10 / 24**(`-Wall` 없이), 버퍼링 격자에서 **터미널과 보이는 순서가 갈린 칸 2 / 8** — 그 둘이 **전부 `s47b2.c`** 다. 브리핑의 예제 모양(`printf("a")` · 개행 없음)인 `s47b1.c` 는 **세 받는 쪽에서 순서가 같았다**((3)).

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ★★★ ① **컴파일 진단** | ★ **지정자 격자의 본체** — `-Wformat` 경고 전문 · 줄마다 났나 | 씀 |
| ② 실행 출력 | ★ **맞는 지정자로만** 찍은 값 · ★ 버퍼링 판의 보이는 순서 | 씀 — ★★★ **틀린 지정자의 출력은 싣지 않았다**(미정의) |
| ③ sanitizer | — | 부적용(ASan·UBSan 은 형식 문자열과 인자 타입의 불일치를 보지 않는다 — 던지지 않았다) |
| ★★★ ④ **`strace` 의 시스템 호출** | ★ **버퍼링 격자의 본체** — `write(1, …)` · `write(2, …)` 수 · 크기 · `fstat`/`ioctl` | 씀 |
| 시간 측정 | — | 부적용(버퍼링이 빠르다는 주장은 이 문서에 없다) |
| ★ 제5의 상태 | 「stdout 은 지금 어떤 버퍼링인가」를 **프로그램 안에서 물을 표준 함수가 없다.** **`strace` 가 센 `write` 수와 stdio 가 부른 `fstat`/`ioctl` 로 바꿔 물어** 모드를 거꾸로 읽었다 | 창을 바꿔 답함 |

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

```text
===== strace -V | sed -n 1p (exit=0) =====
strace -- version 6.8
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **지정자 격자 · 버퍼링 격자 · `write` 수 · 크기** | 같은 판이면 같다 |
| ★ 흔들린다 | **`strace` 의 PID · 주소 · 터미널의 부 번호** | 블록에 안 싣는다 — `-f` 없이 돌려 PID 가 안 찍히고, `ioctl` 의 주소는 `0x…` 로, 의사 터미널의 **부 번호**(`makedev(0x88, …)`)는 배너의 `sed` 로 가렸다(**주 번호 `0x88` 은 남겼다**) |
| ★ 재현 조건 | **터미널 판** | 진짜 터미널이 아니라 **`script -qc` 의 의사 터미널**이다 — 줄 끝이 `\r\n` 이라 격자는 `\r` 을 지우고 찍었다 |

## 한눈에 — 쉽게 말하면

**stdout 은 택배 상자, stderr 은 전화다.**

- **택배는 상자가 찰 때 보낸다** — 파이프·파일로 가는 stdout. 한 줄마다 보내지 않는다. → **완전 버퍼**
- **받는 사람이 창구 앞에 서 있으면 한 줄마다 보낸다** — 터미널이면 사람이 보고 있으니까. → **줄 버퍼**
- **전화는 바로 간다** — stderr 은 모으지 않는다. → **버퍼 없음**
- **그래서 택배보다 나중에 건 전화가 먼저 도착한다** — 파이프로 모으면 stderr 이 앞으로 나온다. → **순서가 받는 쪽에 달렸다**
- **송장에 적은 크기와 상자의 크기가 달라도 우체국은 모른다** — 지정자와 인자 타입이 어긋나면 **받는 쪽이 엉뚱한 크기로 뜯는다.** 컴파일러가 대조해 주는 것은 **`printf` 가 우체국 함수라서**다. → **`-Wformat`**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 상자가 찰 때 | 파이프·파일의 stdout | ★★★ `write(1, "a\nc\n", 4)` **한 번** · 만 바이트는 **4096 · 4096 · 1808** |
| 한 줄마다 | 터미널의 stdout | ★★ `write(1, …)` **두 번**(`a\n` · `c\n`) |
| 전화 | stderr | ★★ `write(2, …)` **한 번 · 늘 먼저** |
| 송장과 크기 | `%d` 에 `size_t` | ★★★ **두 컴파일러 경고** — 출력은 싣지 않는다 |
| 송장 대조 안 됨 | `%lu` 에 `size_t` | ★★ **경고 0** — 이 판에서는 타입이 같다 |

```text
   printf("a\n"); fprintf(stderr, "b\n"); printf("c\n");   (s47b2.c)

   받는 쪽이 터미널                         받는 쪽이 파이프 · 파일
   stdout = 줄 버퍼                         stdout = 완전 버퍼
   ----------------------------------       ----------------------------------
   "a\n"  -> 개행 -> write(1, "a\n")        "a\n"  -> 상자에 담는다
   "b\n"  -> write(2, "b\n")                "b\n"  -> write(2, "b\n")      ★ 먼저
   "c\n"  -> 개행 -> write(1, "c\n")        "c\n"  -> 상자에 담는다
                                            exit   -> write(1, "a\nc\n")   ★ 한 번

   보이는 순서  a b c                        보이는 순서  b a c
```

- ★★★ **이 주제의 본체는 둘로 갈린다** — 지정자는 **「표준 — 틀리면 미정의」** 칸, 버퍼링은 **「표준이 말한 것은 한 줄 · 나머지는 구현」** 칸이다.
- ★★ **「터미널이면 줄 버퍼」는 표준 문장이 아니다** — 표준은 「**대화형 장치가 아니라고 판정되면 완전 버퍼**」만 적고, 무엇이 대화형 장치인지와 대화형일 때의 모드는 **구현**에 맡긴다.

> **버퍼링 모드** — stdio 가 출력을 **언제 운영체제에 넘기나**(`write` 시스템 호출). 완전 버퍼(`_IOFBF`) · 줄 버퍼(`_IOLBF`) · 버퍼 없음(`_IONBF`).\
> 예: `setvbuf(stdout, NULL, _IOLBF, 0)` 은 stdout 을 줄 버퍼로 바꾼다.

> **서식 지정자(conversion specifier)** — `printf` 의 형식 문자열에서 **인자 하나의 타입과 표기**를 정하는 `%` 조각.\
> 예: `size_t` 는 `%zu`, `ptrdiff_t` 는 `%td`, `int64_t` 는 `"%" PRId64`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **타입마다 어느 지정자가 맞고, 컴파일러는 틀린 것을 어디까지 잡나.**
2. ★★★ **stdout 의 버퍼링 모드는 누가 정하고, 그것이 보이는 순서와 `write` 수를 어떻게 바꾸나.**
3. ★★ **어느 것이 표준의 약속이고 어느 것이 이 판(glibc · Ubuntu gcc)의 선택인가.**

## 동작 방식

### (1) ★★★ 서식 지정자 격자 — 타입 여덟 × 지정자 셋

**언제 쓰나** — `size_t`·고정폭 정수·포인터를 찍을 때 **지정자를 고르고**, 경고가 없는 줄을 **믿어도 되나** 판단할 때. ★★★ **이 편의 첫째 본체**다.

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

그림 해설 (한 단계씩):

- ★★★ **경고 난 칸 gcc 10 / 24 · clang 10 / 24** — 두 컴파일러가 **같은 열 줄**을 잡았다. `%d` 일곱 줄(`uint8_t` 만 빼고 전부)과 `long long · %ld` · `int64_t · %lld` · `void * · %lx` 셋이다.
- ★★★ **`-Wno-format` 두 열은 0 / 24** — 이 격자의 경고는 **전부 `-Wformat` 한 묶음**이다.
- ★★ **경고가 안 난 틀림 둘** — `size_t · %lu` · `ptrdiff_t · %ld`. 이 판(LP64)에서 `size_t` 는 **`unsigned long` 그 자체**, `ptrdiff_t` 는 **`long` 그 자체**라 컴파일러가 볼 때 틀린 데가 없다. LLP64(윈도우)에서는 둘 다 **`long long` 계열**이라 같은 줄이 틀린다 — [02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)가 `int64_t · %ld` 로 본 것과 같은 자리다.
- ★★ **`long long · %ld` 는 경고가 난다** — 이 판에서 `long` 과 `long long` 은 **둘 다 64 비트인데 다른 타입**이다. 크기가 같아도 **타입이 다르면 틀린 지정자**다.
- ★★ **`uint8_t · %d` 와 `%c`, `float · %lf` 는 맞다** — 가변 인자에서는 **기본 인자 승격**이 일어나 `uint8_t` 는 `int` 로, `float` 은 `double` 로 넘어간다([36번 형제](../36-variadic-functions-stdarg/)). `%lf` 는 C99 부터 `%f` 와 같다.
- ★★★ **gcc 는 `-Wall` 없이도 경고했다** — 그 이유가 (2)다.

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

- ★★ **gcc 의 제안 줄은 이 판의 타입을 말한다** — `size_t · %d` 에 **`%ld`** 를 제안했다(`size_t {aka long unsigned int}`). **이식성 있는 답은 `%zu`** 다. 제안은 **고칠 방향**이지 정답이 아니다.
- ★★ **clang 은 캐럿 아래에 제안을 안 달고** `format specifies type 'int' but the argument has type 'size_t' (aka 'unsigned long')` 한 줄로 말한다.

### (2) ★★ gcc 의 `-Wformat` 은 누가 켰나 — 배포판의 specs

**언제 쓰나** — 「내 머신에서는 경고가 나는데 CI 에서는 안 난다」.

```text
===== gcc -dumpspecs | grep -o '%{!Wformat:%{!Wformat=2:%{!Wformat=0:%{!Wall:-Wformat} %{!Wno-format-security:-Wformat-security}}}}' (exit=0) =====
%{!Wformat:%{!Wformat=2:%{!Wformat=0:%{!Wall:-Wformat} %{!Wno-format-security:-Wformat-security}}}}
```

- ★★★ **Ubuntu 의 gcc 는 specs 에 「`-Wformat` 을 안 받았고 `-Wall` 도 없으면 `-Wformat` 을 넣고, `-Wno-format-security` 가 없으면 `-Wformat-security` 를 넣어라」를 박아 두었다** — 업스트림 gcc 는 `-Wformat` 을 **`-Wall` 에만** 넣는다.
- ★★ **그래서 (1)의 gcc 열은 「gcc 의 성질」이 아니라 「이 배포판 gcc 의 성질」** 이다. 경고에 기대는 빌드는 **`-Wall`(또는 `-Wformat`)을 명시**한다.
- ★ clang 은 **`-Wformat` 을 기본으로 켠다**(이 판에서 `-Wall` 없이 10 / 24) — 배포판 설정인지 clang 기본인지는 이 문서가 가르지 않았다.

### (3) ★★★ 버퍼링 격자 — 프로그램 넷 × 받는 쪽 셋

**언제 쓰나** — 로그에서 **stderr 이 stdout 보다 앞에** 찍혀 인과가 뒤집혀 보일 때. ★★★ **이 편의 둘째 본체**다.

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

그림 해설 (한 단계씩):

- ★★★ **`s47b1.c`(`printf("a")` · 개행 없음)는 세 받는 쪽에서 다 `bac`** 다 — 터미널에서도 `a` 는 **개행이 올 때까지 안 나간다.** 줄 버퍼든 완전 버퍼든 **`a` 가 `b` 보다 늦게** 나가서 **순서로는 두 모드가 안 갈린다.** ★ **`write(1, …)` 도 셋 다 1 번** — 이 예제로는 **모드 차이가 아무 창에도 안 보인다.**
- ★★★ **`s47b2.c`(`"a\n"`)에서 비로소 갈린다** — 터미널은 `a/b/c/` · `write(1, …)` **2 번**, 파이프·파일은 **`b/a/c/`** · **1 번.** 격자의 **갈린 칸 2 / 8** 이 전부 이 줄이다.
- ★★ **`s47b3.c`(`setvbuf(stdout, NULL, _IOLBF, 0)`)는 세 받는 쪽 다 터미널 모양** — 모드를 **프로그램이 정하면** 받는 쪽이 안 정한다.
- ★★ **`s47b4.c`(`fflush(stdout)`)도 세 받는 쪽 다 `a/b/c/`** — 순서가 필요한 자리에서 **직접 비웠다.** `write(1, …)` 는 2 번이다(비운 한 번 + 끝에서 한 번).
- ★★★ **`write(2, …)` 는 열두 칸 다 1 번** — stderr 은 **모으지 않았다.** 그래서 **파이프·파일에서 stderr 이 먼저** 나온다.
- ★★ **「stdout 과 stderr 을 한 블록에 섞지 마라」**([작성법 규칙 18](../../../../reference/study-note-guide.md))의 원인이 이 격자다 — **받아 적으려고 파이프를 태우는 순간** `b` 가 앞으로 온다.

### (4) ★★ stdio 는 무엇을 보고 고르나 — `fstat` 과 `ioctl`

**언제 쓰나** — 「터미널인지 어떻게 아나」.

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

- ★★★ **stdio 는 첫 출력 때 fd 1 을 `fstat` 한다** — 파일이면 **`S_IFREG`** → 대화형이 아니라고 판정 → 완전 버퍼.
- ★★ **터미널 판은 `S_IFCHR`(문자 장치) · 주 번호 `0x88` 에서 끝났다** — `ioctl` 을 안 불렀다.
- ★★★ **`/dev/null` 도 `S_IFCHR` 인데 한 번 더 물었다** — `ioctl(1, TCGETS, …)` 가 **`ENOTTY`** 로 실패하자 **완전 버퍼**가 됐다(파일 판과 같은 `write` 모양). 문자 장치라고 다 터미널로 치지 않는다.
- ★ **어떤 문자 장치를 `ioctl` 없이 터미널로 치는지**는 이 문서가 **glibc 소스로 확인하지 않았다** — 관찰은 「의사 터미널(`0x88`)은 `fstat` 만, `/dev/null`(`0x1`)은 `ioctl` 까지」다.
- ★★ **표준은 이 판정법을 적지 않는다** — 「무엇이 대화형 장치인가는 구현 정의」. 위 세 블록이 **이 판의 정의**다.

### (5) ★★ 완전 버퍼의 크기 — 만 바이트를 한 글자씩

**언제 쓰나** — 「`putchar` 를 만 번 부르면 시스템 호출도 만 번인가」.

```c
/* s47b5.c */
#include <stdio.h>

int main(void) {
    for (int k = 0; k < 10000; k++) putchar('x');
    fprintf(stderr, "%s%s%s\n", "e", "r", "r");  /* 한 번의 호출 · 조각 셋 */
    return 0;
}
```

```text
===== gcc -std=c17 s47b5.c -o x && strace -e trace=write -o st.txt ./x > out.txt 2>/dev/null; wc -c < out.txt; sed -E 's/"x+"(\.\.\.)?/"x…"/' st.txt (exit=0) =====
10000
write(1, "x…", 4096) = 4096
write(1, "x…", 4096) = 4096
write(2, "err\n", 4)                    = 4
write(1, "x…", 1808) = 1808
+++ exited with 0 +++
```

- ★★★ **`putchar` 만 번이 `write(1, …)` 세 번** — **4096 · 4096 · 1808** 바이트. 파일로 가는 stdout 의 버퍼가 **4096 바이트**였고, 남은 1808 은 **`exit` 가 비웠다.**
- ★★ **stderr 의 `fprintf` 는 조각 셋(`"e"` · `"r"` · `"r"`)인데 `write(2, …)` 는 한 번** — 「버퍼 없음」이 **「조각마다 `write`」가 아니었다.** 호출 한 번의 출력을 한 번에 냈다. ★ 이것은 **glibc 의 구현**이다 — 표준은 「가능한 한 빨리」까지만 적는다.
- ★★ **`write(2, …)` 는 둘째와 셋째 `write(1, …)` 사이** — stdout 의 버퍼가 **두 번 차고 난 뒤** stderr 가 끼었다(이 블록은 stderr 을 버렸다 — 섞은 판은 (3)이다).
- ★ **이 버퍼가 「빠르다」는 이 문서가 재지 않았다** — 센 것은 **시스템 호출 수**다.

### (6) ★ 맞는 지정자로 찍은 값

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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s47ok.c -o x ; ./x (cc exit=0 · run exit=0) =====
16 | -9000000000 | -9223372036854775808 | 200 200 | -7
0.100000 0.10000000000000001 | 0.100000 0.10000000149011612
%p 로 NULL = (nil)
```

- ★★ **`%zu` 16 · `%lld` · `PRId64` 의 `INT64_MIN` · `PRIu8` 과 `%d` 가 같은 200 · `%td` 의 음수 `-7`** — 맞는 지정자는 **값을 그대로** 보인다.
- ★★ **`%f` 는 둘 다 `0.100000`, `%.17g` 는 `0.10000000000000001` 대 `0.10000000149011612`** — `float` 은 승격돼 `double` 로 넘어갔지만 **값은 `float` 의 `0.1` 근사 그대로**다.
- ★ **`%p` 로 널 포인터는 `(nil)`** — `%p` 의 표기는 **구현 정의**다(glibc 의 선택).

### (7) ★ 끝날 때 — `exit` 와 `_exit`

- ★★ **`main` 이 돌아오거나 `exit` 를 부르면 출력 스트림이 비워진다**(표준) — (3)·(5)의 파이프·파일 판에서 마지막 `write(1, …)` 가 그것이다.
- ★★ **`_exit` 은 안 비운다** — [Go 44](../../../go/syntax/44-os-bufio-and-io-copy/)가 C 프로그램으로 **`exit` 18 바이트 · `_exit` 0 바이트**를 `strace` 로 이미 쟀다. **Go 의 `bufio` 는 `_exit` 쪽**(끝날 때 아무도 안 비운다)이다. 이 편은 **다시 재지 않았다.**
- ★ **`abort` 나 sanitizer 가 죽이면 비워지지 않는다**(표준: 「다른 종료 경로는 파일을 제대로 닫지 않을 수 있다」) — [작성법 규칙 19-A](../../../../reference/study-note-guide.md)의 사고다.

## 문법 — 형태와 규칙

### 형태 — 타입별 지정자

| 타입 | 지정자 | 비고 |
|---|---|---|
| `size_t` | ★★★ **`%zu`** | `%lu` 는 LP64 에서만 우연히 맞다 |
| `ptrdiff_t` | ★★ **`%td`** | `%ld` 도 LP64 에서만 |
| `long long` | ★★ **`%lld`** | `%ld` 는 **경고**(크기가 같아도 타입이 다르다) |
| `int64_t` 등 고정폭 | ★★★ **`"%" PRId64`**(`<inttypes.h>`) | `%lld` 는 이 판에서 **경고** · `%ld` 는 이 판에서만 |
| `uint8_t` | ★ `"%" PRIu8` · `%d`(승격) | `%hhu` 도 있다 |
| `void *` | ★★ **`%p`** | 다른 객체 포인터는 `(void *)` 로 바꿔 넘긴다 |
| `double` · `float` | ★ `%f` · `%g` · `%e`(`%lf` 는 같은 뜻) | `float` 은 `double` 로 승격된다 |
| `intmax_t` | ★ `%jd` | — |

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 결과 | 층 | 어느 절 |
|---|---|---|---|
| `printf("%d", sz)`(`size_t`) | ★★ **두 컴파일러 경고** · 출력은 **미정의** | ★★★ 표준(지정자와 타입이 안 맞으면 UB) | (1) |
| `printf("%lu", sz)` | ★ **경고 0**(이 판) · LLP64 에서 틀림 | ★★ 구현(타입 정의)에 기댄 코드 | (1) |
| `printf("%ld", ll)` | ★★ **경고** — 크기가 같아도 | ★★★ 표준 | (1) |
| stdout 과 stderr 을 한 로그로 모으기 | ★★ **파이프·파일에서 stderr 이 먼저** | ★★ 구현(대화형 판정) · 표준(stderr 은 완전 버퍼 아님) | (3) |
| 순서가 중요한데 `fflush` 없음 | ★★ 받는 쪽에 따라 순서가 바뀐다 | ★★ 구현 | (3) |

### 규칙 불릿

- ★★★ **지정자는 인자의 (승격된) 타입과 정확히 맞아야 한다 — 크기가 같아도 타입이 다르면 틀리고, 틀리면 미정의다.**
- ★★★ **「경고가 없다」는 「이 판의 타입 정의와 맞다」일 뿐 — `%zu` · `%td` · `PRId64` 를 쓴다.**
- ★★★ **stderr 은 완전 버퍼가 아니고, stdout 은 「대화형이 아니라고 판정되면」 완전 버퍼다 — 판정법은 구현이 정한다.**
- ★★ **순서가 중요하면 `fflush(stdout)` 또는 `setvbuf` 로 모드를 정한다.**
- ★ **`exit`·`main` 의 반환은 비우고, `_exit`·`abort` 는 안 비운다.**

## 어디서 틀리나

### 1. ★★★ 「`%d` 로 찍어도 값이 맞게 나오더라」

**미정의 동작의 한 판**이다 — [36번 형제](../36-variadic-functions-stdarg/)의 `printf("%d", 3.0)` 은 **`3` 을 한 판도 안 찍었다**(`0 / 10`). 이 편은 틀린 줄을 **실행하지 않았다**((1)).

### 2. ★★ 「경고가 없으니 이식성도 있다」

`%lu`(`size_t`) · `%ld`(`ptrdiff_t`)는 **이 판에서 타입이 같아서** 조용했다((1)).

### 3. ★★ 「gcc 는 `-Wall` 이 없으면 형식 경고를 안 낸다 / 낸다」

**배포판 specs 가 정한다**((2)). Ubuntu 는 켰다.

### 4. ★★★ 「터미널에서 순서가 맞았으니 로그에서도 맞다」

`s47b2.c` 는 **파이프·파일에서 `b` 가 먼저**였다((3)). 그리고 **`s47b1.c` 처럼 개행이 없는 예제로는 그 차이가 안 보인다** — 확인용 예제가 확인을 못 한다.

### 5. ★★ 「버퍼 없는 stderr 은 조각마다 `write` 한다」

`fprintf(stderr, "%s%s%s\n", …)` 한 번이 **`write` 한 번**이었다((5)).

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **지정자는 「표준」 칸이 본체**다 — 맞으면 정의, 틀리면 미정의.\
★★★ **버퍼링은 「구현 정의」 칸이 본체**다 — 표준은 「stderr 은 완전 버퍼 아님 · 대화형이 아니면 완전 버퍼」 한 줄뿐이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | ★★★ **지정자와 타입이 안 맞으면 UB** · 승격(`uint8_t`→`int` · `float`→`double`) · **stderr 은 완전 버퍼 아님** · **대화형이 아니라고 판정되면 stdout 은 완전 버퍼** · `exit`/`main` 반환은 비운다 · `printf` 는 보낸 문자 수(오류면 음수) | 격자 · (7) |
| ★★ **구현 정의** | 문서화 의무가 있다 | ★★★ **무엇이 대화형 장치인가**(이 판: `fstat` · `ioctl(TCGETS)`) · **버퍼링 특성의 지원** · `%p` 의 표기(`(nil)`) · `size_t`/`ptrdiff_t`/`int64_t` 가 **어느 기본 타입인가** | (4) · (6) · (1) |
| ★★ **glibc 구현** | 라이브러리의 선택 | ★★ **터미널이면 줄 버퍼** · 완전 버퍼 **4096 바이트** · stderr 의 `fprintf` 한 번 = `write` 한 번 | (3) · (5) |
| ★★ **컴파일러 구현(배포판 포함)** | 도구의 선택 | ★★★ **Ubuntu gcc 의 specs 가 `-Wformat` 을 기본으로 켬** · clang 의 기본 `-Wformat` · gcc 의 제안 줄(`%ld`) | (2) · (1) |
| **미명시** | 몇 가지 중 하나 | ★ **해당 없음(이 편이 던진 것 중에는)** | — |
| ★★★ **UB** | 아무 일이나 | ★★★ **틀린 지정자로 찍은 값** — 이 편은 **싣지 않았다** | — |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★ **`%lu`(`size_t`) · `%ld`(`ptrdiff_t`)** — 이 판에서 타입이 같아 **경고 0** |
| ★★ **구현 정의 · glibc** | ★★★ **stdout 이 지금 어떤 모드인지 알려 주는 표준 함수가 없다** — `strace` 로만 봤다 · 파이프에서 순서가 뒤집혀도 **아무 경고가 없다** |
| ★★ **컴파일러 구현** | ★★ `-Wno-format` 이 **격자의 경고를 전부** 지웠다(0 / 24) |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **지정자는 표준, 버퍼링은 구현** — 앞은 경고로 잡히고 뒤는 `strace` 로만 보인다.
  - ★★ **경고의 유무는 배포판 설정과 이 판의 타입 정의를 탄다** — 기준으로 쓰지 말고 **`%zu` · `%td` · `PRId64`** 를 기준으로 쓴다.
  - ★★ **순서가 필요하면 모드를 프로그램이 정한다** — `setvbuf` · `fflush`.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| `size_t` · 크기 찍기 | ★★★ `%zu` | `%d` · `%lu` |
| 고정폭 정수 | ★★ `"%" PRId64` · `PRIu32` … | `%ld` · `%lld` |
| 포인터 | ★ `%p`(+ `(void *)`) | `%lx` · `%d` |
| 진행 메시지와 오류를 한 로그로 | ★★★ **오류도 stdout 으로** 또는 **`setvbuf(stdout, NULL, _IOLBF, 0)`** | 파이프에서 순서를 기대하기 |
| 마커를 순서대로 | ★★ 마커를 **stderr** 로(작성법 규칙 18) · 또는 `fflush` | stdout 마커 + stderr 진단 |
| 죽기 직전 출력 | ★ `fflush` 후 종료 · 또는 stdout 을 `_IONBF` | `_exit` · `abort` 에 기대기 |

판단 규칙 두 줄.

- ★★★ **지정자는 인자의 타입 이름으로 고른다 — 크기로 고르지 않는다.**
- ★★ **stdout 과 stderr 이 같은 곳으로 갈 때는 「누가 언제 `write` 하나」를 먼저 묻는다.**

## 핵심 문장

- ★★★ **지정자 격자에서 경고 난 칸 gcc 10 / 24 · clang 10 / 24 — 같은 열 줄이었고, `-Wno-format` 이 전부 지웠다(0 / 24).**
- ★★ **`size_t · %lu` · `ptrdiff_t · %ld` 는 경고가 없었고, `long long · %ld` 는 경고가 났다 — 크기가 아니라 타입이 기준이다.**
- ★★ **Ubuntu gcc 는 specs 로 `-Wformat` 을 기본으로 켠다 — `-Wall` 없이 10 / 24 였다.**
- ★★★ **버퍼링 격자에서 터미널과 보이는 순서가 갈린 칸 2 / 8 — 전부 `"a\n"` 을 찍는 `s47b2.c` 였다. 개행이 없는 `s47b1.c` 는 세 받는 쪽 다 `bac` 였다.**
- ★★★ **파이프·파일의 stdout 은 `write` 한 번(`"a\nc\n"`), 터미널은 두 번 · stderr 은 늘 한 번이고 늘 먼저였다.**
- ★★ **stdio 는 fd 1 을 `fstat` 해서 골랐다 — `/dev/null` 은 `ioctl(TCGETS)` 가 `ENOTTY` 로 실패해 완전 버퍼가 됐다.**
- ★★ **`putchar` 만 번은 `write` 세 번(4096 · 4096 · 1808)이었다.**

## 관련 자료

- [36번 형제 — 가변 인자 함수](../36-variadic-functions-stdarg/) — ★★★ `printf` 의 형식 대조 · `format` 속성 · `printf("%d", 3.0)` 의 `0 / 10`.
- [02번 형제 — 기본 타입·크기·고정폭 정수](../02-basic-types-sizes-and-fixed-width-integers/) — ★★ `size_t` · `int64_t` 의 정체와 `%ld` 가 조용한 이유.
- [46번 형제 — `errno`](../46-errno-and-error-return-conventions/) — ★ `printf` 의 실패는 **음수 반환**으로 판정한다.
- [48번 형제 — `<stdio.h>` 입력과 파일](../48-stdio-input-and-files/) — ★★ 입력 쪽 스트림과 `EOF`.
- [Go 44 — `os` · `bufio` · `io.Copy`](../../../go/syntax/44-os-bufio-and-io-copy/) — ★★ C `exit` 대 `_exit` 의 `strace` 실측 · Go `bufio` 의 `Flush`.
- [작성법 — 규칙 18 · 19-A](../../../../reference/study-note-guide.md) — ★ stdout·stderr 을 섞은 블록의 사고.

## 용어 풀이

> **완전 버퍼 · 줄 버퍼 · 버퍼 없음** — 버퍼가 찰 때 · 개행을 만날 때 · 가능한 한 바로 `write` 한다.\
> 예: 이 판의 stdout 은 파일이면 완전 버퍼(4096), 터미널이면 줄 버퍼.

> **대화형 장치(interactive device)** — 사람이 앞에서 주고받는 장치. **무엇이 그것인지는 구현 정의**다.\
> 예: 이 판에서 의사 터미널은 대화형, `/dev/null` 은 `ioctl(TCGETS)` 실패로 비대화형.

> **`setvbuf` / `fflush`** — 스트림의 버퍼링 모드를 정한다 / 버퍼의 내용을 지금 내보낸다.\
> 예: `setvbuf(stdout, NULL, _IOLBF, 0)` · `fflush(stdout)`.

> **기본 인자 승격** — 가변 인자로 넘길 때 `char`·`short`(와 `uint8_t` 같은 작은 정수)는 `int` 로, `float` 은 `double` 로 바뀌는 것.\
> 예: `printf("%d", u8)` 는 맞다.

> **`PRId64` 류** — `<inttypes.h>` 가 고정폭 정수마다 주는 **지정자 문자열 매크로**.\
> 예: `printf("%" PRId64 "\n", v)`.

> **specs** — gcc 드라이버가 옵션을 어떻게 펼칠지 적은 규칙 문자열. 배포판이 기본 옵션을 여기에 넣는다.\
> 예: `%{!Wformat:…%{!Wall:-Wformat}…}`.

## 더 들어가면

- ★★ **형식 문자열이 변수일 때** — `printf(msg)` 는 `-Wformat-security` 의 대상이다(이 판 specs 가 켠다). ★ **던지지 않았다.**
- ★ **`%n`** — 찍은 문자 수를 **쓰는** 지정자. 형식 문자열 공격의 도구. ★ **던지지 않았다.**
- ★ **`setvbuf` 에 내 버퍼를 줄 때의 수명** — 스트림보다 먼저 사라지면 UB. ★ **던지지 않았다.**
- ★ **`stdbuf -oL`** — 프로그램을 안 고치고 stdout 모드를 바꾸는 coreutils 도구. ★ **던지지 않았다.**

## 실행 환경

**기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) 스트림 절 — 「**버퍼 없는 스트림은 문자가 가능한 한 빨리, 완전 버퍼는 버퍼가 찼을 때, 줄 버퍼는 개행을 만났을 때 한 덩어리로 보내려 한다 · 이 특성의 지원은 구현 정의**」·「**처음 열린 표준 오류는 완전 버퍼가 아니다 · 표준 입력과 표준 출력은 대화형 장치를 가리키지 않는다고 판정될 수 있을 때, 그리고 그때만 완전 버퍼다**」·「**`main` 이 돌아오거나 `exit` 를 부르면 열린 파일을 전부 닫는다(출력 스트림은 비운다)**」, 적합성 절 — 「**무엇이 대화형 장치인지는 구현 정의**」, `printf` 의 「**보낸 문자 수, 출력 오류면 음수**」를 **본문에서 직접 찾아 읽었다**)
★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **경고 · 출력 · `write` 호출 수 · `fstat`/`ioctl` 은 전부 실행으로** 접지했다.
**실행 검증** — 이 문서의 모든 출력·진단은 「이 판」 절의 판에서 실제로 돌려 **파일로 캡처한 것**이다.\
★★★ **본체는 둘** — **서식 지정자 격자**(타입 8 × 지정자 3 × 컴파일러 설정 4)와 **버퍼링 격자**(프로그램 4 × 받는 쪽 3 · `strace` 가 센 `write`).\
★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
★★★ **경계** — **`printf` 가 가변 인자 함수라 형식 문자열을 컴파일러가 대조한다 · 내가 만든 함수는 `format` 속성이 있어야 한다**는 [36번 형제](../36-variadic-functions-stdarg/)가 **이미 보였다**(`printf("%d", 3.0)` 이 `3` 을 한 판도 안 찍은 `0 / 10` 도 거기). **`size_t` 는 `%zu` · `int64_t` 는 `PRId64`** 라는 타입 쪽 정본은 [02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)다. **`exit` 는 stdio 를 비우고 `_exit` 는 안 비운다**는 [Go 44 — `os` · `bufio` · `io.Copy`](../../../go/syntax/44-os-bufio-and-io-copy/)가 **C 로 `strace` 까지 이미 쟀다**(`exit` 18 바이트 · `_exit` 0 바이트). 이 편은 셋을 **다시 재지 않는다.**\
★ **stdout 과 stderr 을 섞으면 순서가 받는 쪽에 달린다**는 사고는 [작성법](../../../../reference/study-note-guide.md)의 **규칙 18** 로 이미 박혀 있다 — 이 편이 그 **원인을 실측**한다. **입력 · 파일 · `EOF`** 는 [48번 형제](../48-stdio-input-and-files/)가 정본이다.
선행 — [02번 형제](../02-basic-types-sizes-and-fixed-width-integers/) · [46번 형제](../46-errno-and-error-return-conventions/).
