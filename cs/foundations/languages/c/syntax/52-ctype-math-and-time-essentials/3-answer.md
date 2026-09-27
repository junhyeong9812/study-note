# c/syntax/52 — `<ctype.h>` · `<math.h>` · `<time.h>` 핵심: 「**`isalpha` 는 `unsigned char` 의 값을 기다리고, NaN 검사는 옵션 하나에 지워지며, `localtime` 은 하나뿐인 칸을 돌려준다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **clang 18.1.3** · **glibc 2.39** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s52a.c`\~`s52g.c` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다). 시각은 **고정 `time_t` + `TZ=`** 로만 찍었다.\
> ★★★ **본체 창은 ctype 격자** — 로케일 5 × 부호 2 × 바이트 2.
> ★★ **흔들리는 칸** — ASan 리포트의 PID · 주소 · `BuildId`(정규화 기본 규칙).

## 이 파일이 다시 싣는 소스

★ 7번은 질문 파일에 소스가 없다 — 여기 싣는다.

```c
/* s52e.c */
#include <math.h>

int check_isnan(double x) { return isnan(x); }
int check_self(double x) { return x != x; }
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ctype 격자 — **`(int)c` 는 `-23` · `-1` · 갈린 칸 1 / 20(Latin-1 · 기본 · `0xFF`) · UB 칸 다섯은 전부 같은 답 · sanitizer 침묵** ★★★

**출력**

```text
===== ctype 에 char 를 그대로 — 로케일 5 × char 부호 2 × 바이트 2 (gcc -O0) (exit=0) =====
로케일             char     setlocale || 0xE9: (int)c  isalpha(c)  isalpha((uc)c)  iswalpha || 0xFF: (int)c  isalpha(c)  isalpha((uc)c)  iswalpha
C                  기본     ok        || -23        0*          0               0        || -1         0(EOF)      0               0        
C                  unsigned ok        || 233        0           0               0        || 255        0           0               0        
C.UTF-8            기본     ok        || -23        0*          0               1        || -1         0(EOF)      0               1        
C.UTF-8            unsigned ok        || 233        0           0               1        || 255        0           0               1        
ko_KR.UTF-8        기본     ok        || -23        0*          0               1        || -1         0(EOF)      0               1        
ko_KR.UTF-8        unsigned ok        || 233        0           0               1        || 255        0           0               1        
en_US.UTF-8        기본     NULL      || -23        0*          0               0        || -1         0(EOF)      0               0        
en_US.UTF-8        unsigned NULL      || 233        0           0               0        || 255        0           0               0        
en_US.ISO-8859-1   기본     ok        || -23        1*          1               1        || -1         0(EOF)      1               1        <-0xFF 
en_US.ISO-8859-1   unsigned ok        || 233        1           1               1        || 255        1           1               1        
(기본 = 이 판의 char 는 부호 있음 · unsigned = -funsigned-char · * = EOF 아닌 음수를 넘긴 칸: UB — 이 glibc 의 관찰 · en_US.ISO-8859-1 은 LOCPATH=./loc)
isalpha(c) 와 isalpha((unsigned char)c) 가 갈린 칸 1 / 20
```

```text
===== gcc -std=c17 -O0 -g -fsanitize=address,undefined -ffile-prefix-map="$PWD"=. s52a.c -o x && LOCPATH=./loc ./x en_US.ISO-8859-1 | tr '\037' ' ' (exit=0) =====
ok -23 1 1 1 -1 0 1 1
```

**왜 그런가**

- ★★★ **`-23` 은 UB, `-1` 은 UB 가 아니다** — 인자는 「`unsigned char` 로 표현 가능하거나 `EOF` 와 같아야」 한다. `-1` 은 `EOF` 와 같다. 그래서 **UB 칸은 `0xE9` 쪽(`*`)**, `0xFF` 쪽은 **정의된 `EOF` 호출**이다.
- ★★★ **갈린 칸은 Latin-1 · `0xFF` 하나** — `EOF` 로 읽힌 `isalpha(c)` 는 0, 'ÿ' 로 읽힌 `isalpha((unsigned char)c)` 는 1. 다른 로케일에서는 `0xFF` 가 애초에 알파벳이 아니라 **둘 다 0** 이라 안 갈렸다.
- ★★ **`iswalpha` 는 U+00E9 · U+00FF 를 묻는다** — 두 UTF-8 로케일과 Latin-1 에서 1, `C` 에서 0. `en_US.UTF-8` 은 **`setlocale` 이 `NULL` 이라 `C` 로 남아** `C` 줄과 같다.
- ★★ **ASan+UBSan 판은 같은 값을 찍고 아무 말도 없다** — UB 칸조차.

### 2. 256 칸 표 — **첫 줄만 찍히고 `heap-buffer-overflow` · `23 bytes before`** ★★

**출력**

```text
===== gcc -std=c17 -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s52b.c -o x && ASAN_OPTIONS=strip_path_prefix="$PWD/" ./x | sed -n '1,/^SUMMARY/p' | grep -v -E '^ +#[1-9]' (exit=1) =====
my_isalpha('A') = 1
=================================================================
==1149524==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x511000000029 at pc 0x5c099ec602dc bp 0x7ffc2bde0310 sp 0x7ffc2bde0300
READ of size 1 at 0x511000000029 thread T0
    #0 0x5c099ec602db in my_isalpha s52b.c:6

0x511000000029 is located 23 bytes before 256-byte region [0x511000000040,0x511000000140)
allocated by thread T0 here:
    #0 0x70c43aefd340 in calloc ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:77

SUMMARY: AddressSanitizer: heap-buffer-overflow s52b.c:6 in my_isalpha
```

```text
===== clang -std=c17 -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s52b.c -o x && ASAN_OPTIONS=strip_path_prefix="$PWD/" ./x | sed -n '1,/^SUMMARY/p' | grep -v -E '^ +#[1-9]' (exit=1) =====
my_isalpha('A') = 1
=================================================================
==1149607==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x511000000029 at pc 0x59bf9a5ff90e bp 0x7ffc8ba29be0 sp 0x7ffc8ba29bd8
READ of size 1 at 0x511000000029 thread T0
    #0 0x59bf9a5ff90d in my_isalpha s52b.c:6:39

0x511000000029 is located 23 bytes before 256-byte region [0x511000000040,0x511000000140)
allocated by thread T0 here:
    #0 0x59bf9a5c137d in calloc (x+0xc637d) (BuildId: 2c6f78e2a35e3340ec52ab545aff6fa1c11408f5)

SUMMARY: AddressSanitizer: heap-buffer-overflow s52b.c:6:39 in my_isalpha
```

**왜 그런가**

- ★★ **`alpha_tbl[-23]` 은 표의 23 칸 앞** — ASan 이 힙 블록 앞의 경계 구역에서 잡았다. 두 컴파일러 같은 결론이다.
- ★ **1번과 나란히 두면** — glibc 는 **같은 인덱스에 답을 채워 두었고**, 256 칸 구현은 **그 자리에 아무것도 없다.** 표준은 둘 다 허용한다 — 그래서 **음수 인자는 UB** 다.

### 3. 네 쌍 — **`==` 는 넷 다 0 · `abs` 는 `1 1 0 0` · `rel` 은 `1 0 1 1` · `abs` 는 양쪽으로 틀린다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s52c.c -o x -lm ; ./x (cc exit=0 · run exit=0) =====
a                          b                           ==  abs  rel
0.30000000000000004        0.29999999999999999         0   1    1
9.9999999999999995e-21     1.9999999999999999e-20      0   1    0
10000000000000000          10000000000000002           0   0    1
10000000000000002          10000000000000000           0   0    1
```

**왜 그런가**

- ★★ **둘째 줄** — `1e-20` 과 `2e-20` 의 차이 `1e-20` 은 `DBL_EPSILON`(`2.2e-16`)보다 한참 작아 **`abs` 가 「같다」** 고 했다. 두 배 차이인데.
- ★★ **셋째 · 넷째 줄** — `1e16` 근처의 이웃 double 간격은 **2** 라 차이 `2` 가 `DBL_EPSILON` 보다 커 **`abs` 가 「다르다」**. 한 칸 옆인데.
- ★ `rel` 은 문턱을 **값의 크기에 비례**시켜 넷 다 의도대로다.

### 4. NaN 격자 — **못 본 칸 18 / 64 · 비트 검사는 0 칸 · gcc 는 `-O0` 에서도 못 봄 · clang 만 경고** ★★★

**출력**

```text
===== NaN 검사 네 가지 — 컴파일러 2 × 최적화 2 × 플래그 4 (exit=0) =====
컴파일러 최적화 플래그                             | isnan  x!=x  fpclassify  비트검사 | 경고
gcc    -O0  (없음)                             | 1      1     1           1        | 0
gcc    -O0  -ffast-math                        | 0      0     0           1        | 0
gcc    -O0  -ffinite-math-only                 | 0      0     0           1        | 0
gcc    -O0  -ffast-math -fno-finite-math-only  | 1      1     1           1        | 0
gcc    -O2  (없음)                             | 1      1     1           1        | 0
gcc    -O2  -ffast-math                        | 0      0     0           1        | 0
gcc    -O2  -ffinite-math-only                 | 0      0     0           1        | 0
gcc    -O2  -ffast-math -fno-finite-math-only  | 1      1     1           1        | 0
clang  -O0  (없음)                             | 1      1     1           1        | 0
clang  -O0  -ffast-math                        | 1      1     1           1        | 1
clang  -O0  -ffinite-math-only                 | 1      1     1           1        | 1
clang  -O0  -ffast-math -fno-finite-math-only  | 1      1     1           1        | 0
clang  -O2  (없음)                             | 1      1     1           1        | 0
clang  -O2  -ffast-math                        | 0      0     0           1        | 1
clang  -O2  -ffinite-math-only                 | 0      0     0           1        | 1
clang  -O2  -ffast-math -fno-finite-math-only  | 1      1     1           1        | 0
(입력은 strtod("nan") — 실행할 때 온다 · 1 = NaN 이라고 답함)
NaN 을 못 본 칸 18 / 64
```

```text
===== clang -std=c17 -O2 -ffast-math -c s52d.c -o /dev/null (cc exit=0) =====
s52d.c:16:38: warning: use of NaN is undefined behavior due to the currently enabled floating-point options [-Wnan-infinity-disabled]
   16 |     printf("%d\x1f%d\x1f%d\x1f%d\n", isnan(x) != 0, x != x, fpclassify(x) == FP_NAN, by_bits(x));
      |                                      ^~~~~~~~
/usr/include/math.h:1011:20: note: expanded from macro 'isnan'
 1011 | #  define isnan(x) __builtin_isnan (x)
      |                    ^~~~~~~~~~~~~~~~~~~
1 warning generated.
```

```text
===== gcc -std=c17 -O2 -ffast-math -Wall -Wextra -c s52d.c -o /dev/null (cc exit=0) =====
```

**왜 그런가**

- ★★★ **`-ffinite-math-only` 가 「NaN 은 안 온다」를 약속한다** — 그러면 컴파일러는 `isnan` · `x != x` · `fpclassify == FP_NAN` 을 **거짓으로 접어도 된다.** `-fno-finite-math-only` 를 붙이면 네 검사가 다 산다.
- ★★ **비트 검사는 정수 연산**이라 그 약속이 닿지 않는다 — 64 칸 다 1.
- ★★ **clang `-O0` 은 접지 않았다 · gcc `-O0` 은 접었다** — 최적화 수준이 결과를 가른 것은 clang 뿐이다.
- ★★ **clang `-Wnan-infinity-disabled`** — 「use of NaN is undefined behavior due to the currently enabled floating-point options」. gcc 는 0 줄.

### 5. 두 시각 · 세 `mktime` — **`p1 == p2 : 1` · `123` → `127` · `p1 == g : 1` · 시 `7` → `22` · 2 월 1 일 · 2 월 29 일 · 이듬해 1 월 1 일** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s52f.c -o x ; TZ=Asia/Seoul ./x (cc exit=0 · run exit=0) =====
[1] p1 == p2 : 1
[1] tm_year saved 123, p1->tm_year now 127
[2] p1 == g  : 1
[2] tm_hour saved 7, p1->tm_hour now 22
[3] in {year 124, mon 0, mday 32} -> tm_year 124 tm_mon 1 tm_mday 1 -> "2024-02-01 Thu"  (time_t 1706713200)
[3] in {year 124, mon 2, mday 0} -> tm_year 124 tm_mon 1 tm_mday 29 -> "2024-02-29 Thu"  (time_t 1709132400)
[3] in {year 124, mon 12, mday 1} -> tm_year 125 tm_mon 0 tm_mday 1 -> "2025-01-01 Wed"  (time_t 1735657200)
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s52f.c -o x ; TZ=UTC ./x (cc exit=0 · run exit=0) =====
[1] p1 == p2 : 1
[1] tm_year saved 123, p1->tm_year now 127
[2] p1 == g  : 1
[2] tm_hour saved 22, p1->tm_hour now 22
[3] in {year 124, mon 0, mday 32} -> tm_year 124 tm_mon 1 tm_mday 1 -> "2024-02-01 Thu"  (time_t 1706745600)
[3] in {year 124, mon 2, mday 0} -> tm_year 124 tm_mon 1 tm_mday 29 -> "2024-02-29 Thu"  (time_t 1709164800)
[3] in {year 124, mon 12, mday 1} -> tm_year 125 tm_mon 0 tm_mday 1 -> "2025-01-01 Wed"  (time_t 1735689600)
```

**왜 그런가**

- ★★★ **`localtime` 은 매번 같은 정적 객체를 돌려준다** — 둘째 호출이 첫째 답을 덮었다(해 `123` → `127`). **`gmtime` 도 같은 객체**라 한국 시 `7` 이 UTC 시 `22` 로 덮였다. 표준은 「같은 객체를 쓰는 함수의 앞 결과를 **덮어쓸 수 있다**」고 적는다.
- ★★★ **`mktime` 은 칸의 범위를 따지지 않고 정규화한다** — 1 월 32 일 = 2 월 1 일 · 3 월 0 일 = 2 월 29 일(윤년) · 13 번째 달 = 이듬해 1 월. 요일도 새로 채운다.
- ★★ **`TZ=UTC`** — 날짜 칸은 같고 `time_t` 가 **32400 초(9 시간)** 크다. `[2]` 의 저장된 시는 처음부터 `22` 다.

### 6. `localtime_r` 과 `-std` — **c17 은 `implicit declaration` + `int-conversion` 경고(`cc exit=0`) · c2x 는 `2023-11-15 07:13:20 KST`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s52g.c -o /dev/null (cc exit=0) =====
s52g.c: In function 'main':
s52g.c:7:20: warning: implicit declaration of function 'localtime_r'; did you mean 'localtime'? [-Wimplicit-function-declaration]
    7 |     struct tm *p = localtime_r(&t, &mine);
      |                    ^~~~~~~~~~~
      |                    localtime
s52g.c:7:20: warning: initialization of 'struct tm *' from 'int' makes pointer from integer without a cast [-Wint-conversion]
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic -O0 s52g.c -o x ; TZ=Asia/Seoul ./x (cc exit=0 · run exit=0) =====
2023-11-15 07:13:20 KST  (p == &mine : 1)
```

**왜 그런가**

- ★★ **C17 에 `localtime_r` 은 없다** — 헤더가 선언하지 않아 **암시적 선언**이 되고, 반환값을 `int` 로 받아 포인터에 넣는 경고가 따라왔다. **빌드는 통과한다**(경고일 뿐) — 64 비트에서 그 `int` 는 **포인터를 잘라 먹을 수 있다**(★ 실행은 하지 않았다).
- ★★ **C23 이 표준에 넣었다** — `-std=c2x` 에서 헤더가 선언하고, 결과는 **호출자의 `mine`** 에 들어간다(`p == &mine : 1`).

### 7. `check_isnan` 몸통 — **`-O2` 는 `ucomisd`/`setp` · `-ffast-math` 는 `xor eax,eax`/`ret`** ★★

**출력**

```text
===== check_isnan 의 몸통 — 컴파일러 2 × 플래그 2 (objdump -d -M intel) (exit=0) =====
--- gcc -O2
0000000000000000 <check_isnan>:
endbr64
xor    eax,eax
ucomisd xmm0,xmm0
setp   al
ret
xchg   ax,ax
--- gcc -O2 -ffast-math
0000000000000000 <check_isnan>:
endbr64
xor    eax,eax
ret
nop    WORD PTR [rax+rax*1+0x0]
--- clang -O2
0000000000000000 <check_isnan>:
xor    eax,eax
ucomisd xmm0,xmm0
setp   al
ret
nop    WORD PTR [rax+rax*1+0x0]
--- clang -O2 -ffast-math
0000000000000000 <check_isnan>:
xor    eax,eax
ret
data16 data16 data16 cs nop WORD PTR [rax+rax*1+0x0]
```

**왜 그런가**

- ★★ **기본 판은 실제로 비교한다** — `ucomisd xmm0,xmm0` 은 자기와 비교하고, NaN 이면 **패리티 플래그**(순서 없음)가 선다. `setp al` 이 그것을 결과로 옮긴다.
- ★★ **`-ffast-math` 판은 입력을 안 본다** — 두 컴파일러 다 **`xor eax,eax` · `ret`**. 4번 격자의 `-O2` 0 은 **상수**였다.
- ★ **깨진 것은 C 표준이 아니라 옵션의 전제**다 — 표준의 `isnan` 은 「NaN 이면 참」이지만, 옵션이 「NaN 은 오지 않는다」를 **호출자의 약속**으로 바꿨다. 그 약속을 어긴 것이다(clang 은 그것을 「UB」라 부른다).

### 8. `<ctype.h>` 인자의 범위와 glibc 의 표 — **`unsigned char` 값 또는 `EOF` · 384 칸 표 · `-1` 이 `EOF` 와 겹친다** ★★★

**출력**

```text
===== sed -n '71,76p;88,89p;190p' /usr/include/ctype.h | expand (exit=0) =====
   These point into arrays of 384, so they can be indexed by any `unsigned
   char' value [0,255]; by EOF (-1); or by any `signed char' value
   [-128,-1).  ISO C requires that the ctype functions work for `unsigned
   char' values and for EOF; we also support negative `signed char' values
   for broken old programs.  The case conversion arrays are of `int's
   rather than `unsigned char's because tolower (EOF) must be EOF, which
# define __isctype(c, type) \
  ((*__ctype_b_loc ())[(int) (c)] & (unsigned short int) type)
# define isalpha(c)     __isctype((c), _ISalpha)
```

**왜 그런가**

- ★★★ **표준** — 「the value of which **shall be representable as an unsigned char or shall equal the value of the macro EOF**. If the argument has any other value, the behavior is undefined.」
- ★★★ **glibc 는 `[-128, 255]` 를 다 받는 표**를 만들어 두었다 — 「**we also support negative `signed char` values for broken old programs**」. 그래서 1번의 `*` 칸이 `unsigned char` 칸과 **같은 답**을 냈다.
- ★★ **그런데 `-1` 한 칸만은 `EOF` 의 자리**다 — 부호 있는 `char` 의 `'\xFF'` 는 `-1` 이 되어 **「문자 ÿ」가 아니라 「EOF」** 로 분류된다. 1번에서 갈린 **유일한 칸**이 그것이다.

### 9. 로케일이 없을 때 — **`C` 로케일로 돌았다 · 「C 줄 한 번 더」로 읽는다** ★

**왜 그런가**

- ★ `setlocale` 은 **실패하면 `NULL` 을 돌려주고 로케일을 바꾸지 않는다** — 프로그램은 시작 때의 `C` 로케일 그대로다. 그래서 그 두 줄은 `C` 두 줄과 **한 글자도 같다.** 「en_US 에서는 이렇다」의 근거로 쓰면 안 된다.

### 10. 04 · 02번 형제와 이어서 ★★

**왜 그런가**

- [04번 형제](../04-floating-point-types-and-conversions/) (5)절 — **gcc `-O2 -ffast-math`** 에서 `isnan=0` · `0.0/0.0 = 1.000000` · `nan == nan` 참 · `__STDC_IEC_559__` 미정의. ★★ **이 편이 더한 칸** — **clang 대비**(`-O0` 에서는 산다 · 경고를 낸다) · **`-ffinite-math-only` 가 범인**이라는 분리 · **검사 방법 넷**(비트 검사만 생존) · **어셈블리**(`xor eax,eax`).
- ★ [02번 형제](../02-basic-types-sizes-and-fixed-width-integers/) — `-funsigned-char` 로 `(char)200` 이 `-56` 에서 `200` 이 되는 것을 쟀고 「`isalpha` 에 `char` 를 넘기는 것이 같은 사고」라고 적었다. 1번 격자가 **그 사고의 실측**이다 — `-funsigned-char` 판은 열 칸 다 안전했다.

### 11. 다섯 층과 네 번째 창 ★★★

**왜 그런가**

- **표준** — 인자 범위 · `EOF` · C 로케일의 `isalpha` · `isnan` 의 뜻 · `tm` 칸의 기준 · `mktime` 정규화 · 정적 객체 덮어쓰기 허용 · C23 `localtime_r`.
- **조건부 표준** — NaN 의 성질(IEC 60559).
- **구현** — `char` 의 부호 · 로케일 데이터 · glibc 384 칸 표 · `localtime`/`gmtime` 공유 · `-ffinite-math-only` 의 접기 · clang 의 경고와 `-O0` 생존.
- **미명시** — 해당 없음.
- **UB** — `EOF` 가 아닌 음수를 `<ctype.h>` 에.
- ★★★ **네 번째 창 = 만든 로케일과 만든 표.** 이 머신에 없는 **Latin-1** 을 `localedef` 로 만들어서야 `EOF` 충돌이 보였고, **256 칸 표**를 만들어서야 UB 가 증상으로 보였다. 못 보는 것 — **다른 C 라이브러리의 실제 동작**(musl 등은 이 머신에 없다 — ★ 돌리지 않았다).

### 12. 다른 갈래와 ★

**왜 그런가**

- ★ **JS `case NaN:`** — 절대 안 걸린다(`NaN === NaN` 이 거짓 — [JS 갈래 52번](../../../js/syntax/52-switch-labels-and-control-flow/) 실측). C 의 `x != x` 가 NaN 에서만 참인 것과 **같은 IEEE 754 규칙**이다. ★ 다만 C 는 **옵션 하나로 그 규칙을 컴파일러가 버릴 수 있다**(4번).
- ★ **JS `Date` 의 월** — 0 부터 · 넘치면 넘긴다(`new Date(2026, 1, 31)` → 3 월 3 일 — [JS 갈래 49번](../../../js/syntax/49-date-and-temporal/) 실측). C 의 `tm_mon`·`mktime` 과 **같은 설계**다.

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s52a.c` | ★★★ **ctype 격자 1 / 20** · sanitizer 침묵 · 헤더 주석 | 빌드 3 · 실행 11 · `localedef` 1 |
| `s52b.c` | ★★ 256 칸 표 ASan | 빌드 2 · 리포트 2 |
| `s52c.c` | ★★ 절대 · 상대 오차 | 1 |
| `s52d.c` | ★★★ **NaN 격자 18 / 64** · 경고 둘 | 빌드 16 · 실행 16 · 진단 2 |
| `s52e.c` | ★★ 어셈블리 넷 | 4 |
| `s52f.c` | ★★★ 정적 버퍼 · `mktime` · `TZ` 둘 | 2 |
| `s52g.c` | ★★ `localtime_r` c17 · c2x | 진단 1 · 실행 1 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. 흔들린 칸은 **ASan 리포트의 PID · 주소 · `BuildId` · 레지스터 값**뿐이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **1번 전부** — glibc 의 표 · 로케일 데이터 · `char` 의 부호.
- ★★★ **4번 · 7번** — 두 컴파일러의 최적화 판단.
- ★★ **5번의 `p1 == g : 1`** — glibc 가 두 함수에 한 칸을 쓰는 것.

**`<ctype.h>` 인자 범위 · C 로케일의 `isalpha` · `isnan` 의 뜻 · `tm_mon`/`tm_year` 의 기준 · `mktime` 정규화 · C23 `localtime_r` 은 구현 의존이 아니다.**\
어느 C 구현에서도 같다(판 안에서).

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `mbrtowc` · `timegm` · `fenv.h` · POSIX 기능 매크로를 준 c17 의 `localtime_r` · c17 판 `localtime_r` 의 실행.
- ★ **못 잰 것** — musl 등 **다른 C 라이브러리**(이 머신에 없다) · `en_US.UTF-8`(설치되어 있지 않다 — `locale -a` 블록).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **4번 · 7번** — 옵션의 접기 판단과 clang 경고.
- ★★ **1번** — glibc 가 음수 지원을 거두는지 · 로케일 데이터.
- ★ **5번** — tzdata 의 `Asia/Seoul` 규칙.
