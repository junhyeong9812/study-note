# c/syntax/03 — 정수 승격과 통상 산술 변환: 말없이 일어나는 변환 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> **UB 가 걸린 답은 예외 없이 `-O0`·`-O2`·sanitizer 셋으로 돌렸다.** 한 수준만 돌린 결과는 싣지 않았다.\
> `clang 18.1.3` 을 대조로 쓴 자리는 그 블록에 밝혔다. 무한 루프는 `timeout 5` 로 끊었다(`exit 124`).
> ★ **답의 형식은 세 겹이다** — 값 / 수준마다 같은가 / 어느 층인가.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `-1 < 1u` ★

**출력**

```text
ex.c:5:42: warning: comparison of integer expressions of different signedness: ‘int’ and ‘unsigned int’ [-Wsign-compare]
    5 |     printf("-1 < 1u          : %d\n", -1 < 1u);
      |                                          ^
ex.c:6:41: warning: comparison of integer expressions of different signedness: ‘int’ and ‘unsigned int’ [-Wsign-compare]
    6 |     printf("i < u            : %d\n", i < u);
      |                                         ^
--- 실행 ---
-1 < 1u          : 0
i < u            : 0
(int)-1 < (int)1 : 1
(unsigned)(-1)   : 4294967295
-1 as unsigned   : 4294967295
```

**세 값**

- `-1 < 1u` → **`0`(거짓)** · `-1 < 1` → **`1`(참)** · `(unsigned)i` → **`4294967295`**.
- **`u` 한 글자에 답이 뒤집혔다.**

**비트로 보면**

```text
  int i = -1;                     unsigned u = 1;

  1111 1111 ... 1111 1111          0000 0000 ... 0000 0001
  (32비트 전부 1)

  통상 산술 변환:
    rank 가 같고(int / unsigned int) 부호가 다르다
    -> 부호 없는 쪽으로 맞춘다

  i 의 비트는 ★ 한 비트도 안 바뀐다. 읽는 방식만 바뀐다.
    1111 1111 ... 1111 1111  =  4294967295

  4294967295 < 1  ->  거짓
```

- **변환이 값을 「고치지」 않는다.** 같은 비트를 다른 규칙으로 읽을 뿐이다.
- `(int)-1 < (int)1` 이 참인 것이 대조군이다 — 양쪽이 같은 부호면 아무 일도 안 일어난다.

**경고와 플래그**

```text
(플래그 없음) : 경고 0 건
-Wall         : 경고 0 건      ★
-Wextra       : 경고 1 건
-Wall -Wextra : 경고 1 건
-Wsign-compare: 경고 1 건
```

- **`-Wsign-compare` 가 잡는다.**
- **`-Wall` 에는 안 들어 있다.** `-Wextra` 에 있다.
- 「`-Wall` 켰으니 됐다」는 이 주제 최대 사고를 **통째로 못 본다**는 뜻이다.

### 2. `sizeof` 가 낀 비교

**출력**

```text
ex.c:14:51: warning: comparison of integer expressions of different signedness: ‘int’ and ‘long unsigned int’ [-Wsign-compare]
--- 실행 ---
sizeof(a)/sizeof(a[0]) = 10
k < sizeof(a)/sizeof(a[0]) : 0
k < (int)(sizeof(a)/sizeof(a[0])) : 1
```

```text
ex.c:6:51: warning: comparison of unsigned expression in ‘>= 0’ is always true [-Wtype-limits]
    6 |     for (size_t i = sizeof(a)/sizeof(a[0]) - 1; i >= 0; i--) {
      |                                                   ^~
=== -O0 실행 ===
sum = 433762248
(exit 0)
```

```text
=== ASan ===
==1423171==ERROR: AddressSanitizer: stack-buffer-underflow on address 0x76361520001c at pc 0x5beadc218474 bp 0x7ffd1648bf50 sp 0x7ffd1648bf40
READ of size 4 at 0x76361520001c thread T0
    #0 0x5beadc218473 in main ex.c:7
    #1 0x76361722a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #2 0x76361722a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #3 0x5beadc218184 in _start (/tmp/z5+0x1184) (BuildId: a5548c6838187d6b539742fd5364995450c90857)

Address 0x76361520001c is located in stack of thread T0 at offset 28 in frame
    #0 0x5beadc218258 in main ex.c:2

  This frame has 1 object(s):
    [32, 52) 'a' (line 3) <== Memory access at offset 28 underflows this variable
SUMMARY: AddressSanitizer: stack-buffer-underflow ex.c:7 in main
```

**두 값**

- `k < sizeof(...)` → **`0`** · `k < (int)(sizeof(...))` → **`1`**.
- `k` 가 `-1` 인데 「배열 길이 10보다 작지 않다」고 한다. `sizeof` 가 `size_t`(부호 없음)라 `k` 가 `18446744073709551615` 로 읽혔다.

**루프는 언제 끝나나**

```text
  size_t i = 4;
  i >= 0  ?   size_t 는 부호가 없다 -> ★ 언제나 참
  i-- ...  4, 3, 2, 1, 0, 그 다음은 SIZE_MAX (18446744073709551615)

  -> 조건으로는 절대 안 끝난다. 배열 밖을 계속 읽다가 죽거나, 안 죽으면 영원히 돈다.
```

- 위 실행에서는 **`sum = 433762248` 을 찍고 exit 0** 으로 끝났다.\
  배열 앞쪽 스택 메모리를 읽다가 `break` 조건(`sum > 1000000`)에 걸린 것이다.\
  **에러도 경고도 없이 쓰레기 값을 냈다.**

**경고**

- `-Wtype-limits`(**`-Wextra`** 에 포함)가 `comparison of unsigned expression in ‘>= 0’ is always true` 를 준다.
- `-Wall` 만으로는 안 나온다 — 1번과 같은 구조다.

**ASan**

- `stack-buffer-underflow` 로 **정확히 짚는다** — `'a' (line 3)` 의 `offset 28` 을 읽었고,\
  `a` 는 `[32, 52)` 에 있으니 **시작보다 4바이트 앞**이다. 즉 `a[-1]`.
- **컴파일 시간 경고와 런타임 도구가 서로 다른 것을 말한다.**\
  경고는 「조건이 항상 참」, ASan 은 「어느 바이트를 넘었다」. 둘 다 필요하다.

**고치는 법**

```c
for (size_t i = n; i-- > 0;) { ... }        /* 가장 흔한 관용구 */
for (ptrdiff_t i = (ptrdiff_t)n - 1; i >= 0; i--) { ... }   /* 부호 있는 인덱스로 */
```

- 앞엣것은 조건에서 `i` 를 감소시키므로 `i` 가 0일 때 조건이 거짓이 되면서 감소해 래핑을 안 한다.

### 3. 좁은 타입끼리의 곱셈

**출력**

```text
c * c            : 40000
(unsigned char)(c*c) : 64
sc * 2           : -200
us * us          : -131071
```

```text
=== ubsan ===
ex.c:13:5: runtime error: signed integer overflow: 65535 * 65535 cannot be represented in type 'int'
```

**네 값**

- `c * c` → **`40000`** · `(unsigned char)(c*c)` → **`64`** · `sc * 2` → **`-200`** · `us * us` → **`-131071`**.

**`c * c` 가 `40000` 인 이유**

```text
  unsigned char c = 200;      c * c

  [1단계] 정수 승격 — unsigned char 를 int 로
          (이 환경의 int 가 0~255 를 전부 담으므로 unsigned int 가 아니라 int 로 간다)
          200 (int)  *  200 (int)
  [2단계] 둘 다 int — 할 일 없음
  계산    40000 (int)          <- ★ unsigned char 의 255 상한은 관계가 없다

  절단은 ★ 대입할 때만 일어난다:
          unsigned char r = 40000;   ->  40000 % 256 = 64
```

- **연산은 `unsigned char` 끼리 하는 게 아니라 `int` 끼리 한다.** 이것이 승격이다.
- `sc * 2` = `-200` 도 같다 — `signed char` 범위(`-128\~127`) 밖이지만 **`int` 라 멀쩡하다.**

**`us * us` 만 이상한 이유**

```text
  unsigned short us = 65535;   us * us

  [1단계] unsigned short -> int   (이 환경의 int 가 0~65535 를 전부 담는다)
  계산    65535 * 65535 = 4294836225
          INT_MAX      = 2147483647   <- ★ 넘는다

  -> 부호 있는 정수 오버플로 = UB
```

- **부호 없는 값끼리 곱했는데 부호 있는 오버플로 UB 가 났다.**\
  승격이 **부호 있는 `int`** 로 올렸기 때문이다. 이것이 승격의 가장 고약한 결과다.
- 16비트 `int` 환경이라면 `unsigned short` 가 `unsigned int` 로 승격되어 **모듈러가 되고 UB 가 아니다.**\
  즉 **같은 코드가 환경에 따라 UB 이기도 하고 아니기도 하다.**

**UB 인 것**

- **`us * us` 하나**다.
- 확인 도구는 **UBSan** 이다 — `signed integer overflow: 65535 * 65535 cannot be represented in type 'int'`.
- 고치는 법: `(unsigned)us * us` 또는 `(uint32_t)us * us` — 곱하기 **전에** 올린다.

### 4. 통상 산술 변환 — 결과 타입

**출력** (`_Generic`)

```text
--- 1단계: 정수 승격 (단항 + 로 승격만 일으킨다) ---
  +char          -> int
  +signed char   -> int
  +unsigned char -> int
  +short         -> int
  +unsigned short-> int
  +_Bool         -> int
  +int           -> int
  +unsigned      -> unsigned int
--- 2단계: 통상 산술 변환 ---
  int + unsigned            -> unsigned int
  int + long                -> long
  unsigned + long           -> long
  unsigned + unsigned long  -> unsigned long
  long + unsigned long      -> unsigned long
  long + unsigned           -> long
  long long + unsigned long -> unsigned long long
  unsigned long + long long -> unsigned long long
  int + float               -> float
  float + double            -> double
  double + long double      -> long double
  unsigned long + double    -> double
  char + char               -> int
  short + unsigned short    -> int
--- 값으로 확인 ---
  (long)-1 + (unsigned long)1 = 0
  (int)-1 + (unsigned)1       = 0
  (int)-1 < (long)1           = 1  (long 이 더 넓어 값 보존)
  (int)-1 < (unsigned)1       = 0  (폭이 같아 부호 없는 쪽으로)
```

**열네 개의 타입**

| 식 | 결과 타입 | 어느 규칙 |
|---|---|---|
| `i + u` | `unsigned int` | 부호 다름 + rank 같음 → 부호 없는 쪽 |
| `i + l` | `long` | 부호 같음 → rank 높은 쪽 |
| `u + l` | `long` | `long` 이 `unsigned int` 값을 전부 담는다 |
| `u + ul` | `unsigned long` | 부호 같음 → rank 높은 쪽 |
| `l + ul` | `unsigned long` | 부호 다름 + `unsigned` 쪽 rank 가 같거나 큼 → 부호 없는 쪽 |
| `l + u` | `long` | `u + l` 과 같다(순서는 상관없다) |
| `ll + ul` | **`unsigned long long`** | 어느 쪽도 상대를 못 담음 → rank 높은 쪽의 **부호 없는 판** |
| `i + f` | `float` | 부동소수가 이긴다 |
| `f + d` | `double` | 넓은 부동소수 쪽 |
| `ul + d` | `double` | 정수는 통째로 밀린다 |
| `c + c` | `int` | 승격 결과 |
| `s + us` | `int` | 둘 다 `int` 로 승격되어 끝 |
| `+c` | `int` | 승격 |
| `+us` | `int` | 승격 |

**`u + l` 은 `long` 인데 `l + ul` 은 `unsigned long`**

- 한 문장으로: **부호 없는 쪽의 rank 가 부호 있는 쪽보다 작을 때만 부호 있는 쪽이 이긴다.**
- `unsigned int`(rank 3) vs `long`(rank 4) → `long` 이 더 높고 `unsigned int` 값을 전부 담으니 `long`.
- `long`(rank 4) vs `unsigned long`(rank 4) → rank 가 같으니 **부호 없는 쪽**.

**`ll + ul` 이 어느 쪽도 아닌 이유**

```text
  long long      rank 5, 부호 있음, 64비트  ->  최대 9223372036854775807
  unsigned long  rank 4, 부호 없음, 64비트  ->  최대 18446744073709551615

  rank 는 long long 이 높다. 그런데 long long 이 unsigned long 값을 ★ 전부 담지 못한다.
  (18446744073709551615 > 9223372036854775807)

  -> 규칙 ②-5: rank 높은 쪽(long long)의 "부호 없는 판" = unsigned long long
```

- `long` 이 4바이트인 환경(LLP64)이면 `long long`(8바이트)이 `unsigned long`(4바이트)을 전부 담으므로 **`long long`** 이 된다.\
  **같은 식이 플랫폼에 따라 다른 타입이 된다.**

**`+c` 와 `+us` 가 같은 타입인 것은 이 환경에서만인가**

- **`+c`(char)는 어디서나 `int`** 다 — `char` 의 범위는 어느 환경의 `int` 든 담는다.
- **`+us`(unsigned short)는 이 환경에서만** `int` 다.\
  16비트 `int` 환경이면 `int` 가 `0\~65535` 를 못 담으므로 **`unsigned int`** 로 승격된다.
- 즉 `+us` 의 결과는 **구현 정의**(정확히는 `int` 의 폭에 따라 정해지는 것)다.\
  3번의 `us * us` 가 UB 인지 아닌지가 여기에 달려 있다.

### 5. `INT_MAX + 1` — 세 도구로 ★★

**(A) 단순 덧셈 — 출력**

```text
=== -O0 ===
INT_MAX = 2147483647
x + 1   = -2147483648
(exit 0)
=== -O1 ===
INT_MAX = 2147483647
x + 1   = -2147483648
(exit 0)
=== -O2 ===
INT_MAX = 2147483647
x + 1   = -2147483648
(exit 0)
=== -O3 ===
INT_MAX = 2147483647
x + 1   = -2147483648
(exit 0)
=== -fsanitize=undefined (-O0) ===
ex.c:4:31: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
INT_MAX = 2147483647
x + 1   = -2147483648
(exit 0)
=== -fsanitize=undefined -fno-sanitize-recover=all ===
ex.c:4:31: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
(exit 1)
=== -O2 -fwrapv ===
INT_MAX = 2147483647
x + 1   = -2147483648
(exit 0)
```

- **셋이 다른가? — 값은 전부 같다.** `-O0`\~`-O3`·`-fwrapv` 가 모두 `-2147483648`.
- **다른 것은 sanitizer 뿐**이다. 값은 안 바꾸고 「여기서 UB 가 났다」고 말한다.\
  `-fno-sanitize-recover=all` 을 더하면 그 자리에서 **exit 1** 로 멈춘다(그래서 뒤의 `printf` 가 안 찍혔다).
- ★ **여기서 멈추면 「어차피 랩어라운드하네」라고 잘못 배운다.**

**(B) 루프 조건 — 출력**

```text
=== -O0 ===
n = 3
(exit 0)
=== -O1 ===
ex.c:6:39: warning: iteration 2 invokes undefined behavior [-Waggressive-loop-optimizations]
    6 |     for (int i = INT_MAX - 2; i > 0; i++) n++;
      |                                      ~^~
ex.c:6:33: note: within this loop
    6 |     for (int i = INT_MAX - 2; i > 0; i++) n++;
      |                               ~~^~~
n = 3
(exit 0)
=== -O2 ===
ex.c:6:39: warning: iteration 2 invokes undefined behavior [-Waggressive-loop-optimizations]
(exit 124)      <- timeout 5초. 끝나지 않는다.
=== -O2 -fwrapv ===
n = 3
(exit 0)
=== -O2 -fsanitize=undefined -fno-sanitize-recover=all ===
ex.c:6:39: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
(exit 1)
```

```text
   같은 소스, 플래그만 다르다

   -O0 / -O1          -O2                -O2 -fwrapv        ubsan
   +-------------+    +-------------+    +-------------+    +-------------------+
   | n = 3       |    | 영원히      |    | n = 3       |    | runtime error     |
   | exit 0      |    | 안 끝난다   |    | exit 0      |    | exit 1            |
   +-------------+    | exit 124    |    +-------------+    +-------------------+
                      +-------------+
```

- **`-O2` 만 무한 루프다.** 셋이 다르다.
- 최적화기의 추론: 「부호 있는 오버플로는 UB → 일어날 리 없다 → `i` 는 계속 커지기만 한다 → `i > 0` 은 항상 참」\
  → **조건 검사를 지웠다.**

**`-O1` 이상이 컴파일 시간에 말해 주는 것**

- **`iteration 2 invokes undefined behavior [-Waggressive-loop-optimizations]`**
- 컴파일러가 **「2번째 반복에서 UB 가 난다」고 정확히 짚으면서** 그것을 근거로 최적화한다고 알려 준다.
- 이 경고는 `-O1` 부터 **기본으로 켜져 있다**(`-w` 로만 꺼진다 — 플래그를 바꿔 가며 확인했다).

**(A)와 (B)가 갈린 데서 배우는 것**

- **UB 의 증상은 「값이 이상해지는 것」이 아니다.**\
  (A)는 값이 네 수준에서 똑같았다. 그래도 UB 다.
- UB 의 진짜 증상은 「**최적화기가 코드를 지우는 것**」이다. 그것은 값이 아니라 **제어 흐름**에서 드러난다.
- 그래서 **UB 를 값으로 판정할 수 없다.** 판정자는 sanitizer 뿐이다.
- 이 갈래의 제1 규칙 — **「`-O0` 에서 잘 돌던데요」는 아무것도 증명하지 않는다.**

### 6. 시프트

**출력**

```text
=== -O0 ===
1 << 31 = -2147483648
1 << 32 = 1
1 << -1 = -2147483648
=== -O2 ===
1 << 31 = -2147483648
1 << 32 = 0
1 << -1 = 0
=== ubsan -O0 ===
ex.c:2:37: runtime error: left shift of 1 by 31 places cannot be represented in type 'int'
ex.c:3:37: runtime error: shift exponent 32 is too large for 32-bit type 'int'
ex.c:4:37: runtime error: shift exponent -1 is negative
1 << 31 = -2147483648
1 << 32 = 1
1 << -1 = -2147483648
```

**값**

| 식 | `-O0` | `-O2` |
|---|---|---|
| `1 << 31` | `-2147483648` | `-2147483648` |
| `1 << 32` | **`1`** | **`0`** |
| `1 << -1` | **`-2147483648`** | **`0`** |

- **둘이 갈렸다.** 왜 갈렸는지는 어셈블리가 말해 준다.

```text
=== -O0 : 런타임 시프트 ===          === -O2 : 상수 접기 ===
	mov	eax, DWORD PTR -8[rbp]        cnt32_const:
	mov	edx, DWORD PTR -4[rbp]        	endbr64
	mov	ecx, eax                      	xor	eax, eax     <- 0 으로 접었다
	sal	edx, cl                       	ret
```

- `-O0` 은 x86 의 `sal` 명령을 그대로 쓴다. 이 명령은 **시프트 횟수의 하위 5비트만 본다** — `32 & 31 = 0` 이라 `1 << 0 = 1`.
- `-O2` 는 인라인 뒤 **gcc 가 직접 접어서 `0`** 으로 만든다.
- **하드웨어가 한 일과 컴파일러가 한 일이 다르다.** 둘 다 「맞다」 — UB 라 정답이 없다.

**UBSan 이 잡는 것**

- **세 건 전부** 잡고, 셋이 **다른 문장**이다.
  - `left shift of 1 by 31 places cannot be represented in type 'int'` — 값이 표현 범위를 넘음
  - `shift exponent 32 is too large for 32-bit type 'int'` — 시프트량이 폭 이상
  - `shift exponent -1 is negative` — 시프트량이 음수
- **세 가지가 서로 다른 UB 다.** 「시프트 UB」 한 낱말로 뭉치면 이 구분을 잃는다.

**세 함수를 하나로 합치면**

- **첫 건만 보고된다.** 실제로 한 함수에 세 번 넘겼더니 그랬고, 세 함수로 나누니 셋 다 나왔다.
- 이유: **UBSan 은 같은 소스 위치의 UB 를 한 번만 보고한다.**
- ★ **「한 건만 나왔다」가 「한 건뿐이다」가 아니다.** 이 갈래에서 도구를 믿을 때 가장 조심할 자리다.

**상수로 쓰면**

```text
ex.c:2:36: warning: left shift count >= width of type [-Wshift-count-overflow]
    2 | int cnt32_const(void)   { return 1 << 32; }
      |                                    ^~
```

- **컴파일 시간 경고**가 나온다(`-Wshift-count-overflow`, 기본 활성).
- 그런데 **시프트량을 변수로 넘기면 이 경고가 전혀 안 나온다.**\
  위 세 함수에 `-Wall -Wextra` 로 경고가 하나도 안 붙었다.
- **상수일 때만 보이는 경고**라는 것이 이 자리의 교훈이다.

### 7. 부호 없는 정수는 UB 인가

**출력**

```text
=== -O0 ===
n = 3
UINT_MAX + 1 = 0
0u - 1       = 4294967295
(exit 0)
=== -O2 ===
n = 3
UINT_MAX + 1 = 0
0u - 1       = 4294967295
(exit 0)
=== ubsan ===
n = 3
UINT_MAX + 1 = 0
0u - 1       = 4294967295
(exit 0)
```

**세 결과가 다른가**

- **완전히 같다.** 경고도 없고 UBSan 도 조용하다.

**세 값**

- `n` → **`3`** · `UINT_MAX + 1u` → **`0`** · `0u - 1u` → **`4294967295`**.

**어느 층인가**

- **표준이 정한 것**이다. 부호 없는 연산은 **2^N 으로 나눈 나머지**로 정의되어 있다.
- 5번의 (B)와 무엇이 다른가:

```text
                 넘쳤을 때              최적화기가              sanitizer   -O0/-O2
  --------------  --------------------  ---------------------  ---------  --------
  부호 있는 정수   ★ UB                  "안 일어난다"고 가정    잡는다     ★ 갈린다
  부호 없는 정수     2^N 모듈러 (정의됨)   아무 가정 못 함         조용하다     같다
```

- 최적화기가 「`i` 는 넘치지 않는다」고 가정할 **근거 자체가 없다.** 넘치면 0으로 돈다고 언어가 정했으니까.

**「부호 없는 쪽이 안전하다」가 맞는가**

- **아니다.** 두 가지가 서로 다른 함정이다.
  - 부호 있는 쪽 — 넘치면 **UB**(최적화기가 코드를 지운다).
  - 부호 없는 쪽 — 넘쳐도 정의되지만, **비교에서 `-1` 이 `4294967295` 가 된다**(1·2번).
- 실제로 1·2번의 사고는 **부호 없는 쪽에서만** 난다.
- **어느 쪽도 공짜가 아니다.** 고르는 게 아니라 **섞지 않는 것**이 답이다.

### 8. `-fwrapv` 는 무엇을 바꾸나

**출력**

```text
=== -O2 -fwrapv ===
n = 3
(exit 0)
```

무엇이 달라졌는지는 어셈블리가 가장 선명하다. `int always_true(int a) { return a + 1 > a; }` 를 찍어 봤다.

```text
=== -O2 (기본) ===                 === -O2 -fwrapv ===
always_true:                       always_true:
	endbr64                         	endbr64
	mov	eax, 1     <- 상수 1        	xor	eax, eax
	ret                             	cmp	edi, 2147483647
                                    	setne	al          <- 진짜로 비교한다
                                    	ret
```

```text
--- 실행 ---
-O0         : always_true(INT_MAX) = 1
-O2         : always_true(INT_MAX) = 1
-O2 -fwrapv : always_true(INT_MAX) = 0     ★ 답이 바뀐다
```

**하드웨어인가 언어 규칙인가**

- **언어 규칙**이다. x86 의 `add` 명령은 어차피 2의 보수로 랩한다 — 하드웨어는 원래 그랬다.
- `-fwrapv` 가 바꾸는 것은 「**이 컴파일러에서 부호 있는 오버플로는 UB 가 아니라 랩어라운드로 정의된다**」는 선언이다.

**그 차이가 결정적인 이유**

- UB 가 아니게 되는 순간 **최적화기가 「일어나지 않는다」고 가정할 수 없다.**
- 위 어셈블리가 그 증거다 — 기본 빌드는 `a + 1 > a` 를 **상수 `1`** 로 접었고, `-fwrapv` 는 **`a != INT_MAX`** 라는 진짜 비교를 남겼다.
- 5번 (B)의 루프도 같은 이유로 살아났다.

**대가**

- 최적화 기회가 줄어든다. 루프 변수의 범위를 추론하지 못하므로 벡터화·강도 감소가 약해진다.
- 그리고 **UB 를 감추는 것이지 버그를 고치는 게 아니다.**\
  값은 여전히 랩하고 논리는 여전히 틀렸다.
- 근본 해법은 **넘치기 전에 검사하는 것**이다(목록의 **54번 주제**).

### 9. 경고로 잡히는 것 / 안 잡히는 것

**출력**

```text
--- (1) -Wall -Wextra ---
경고 1 건
--- (2) + -Wconversion -Wsign-conversion ---
6:44: warning: comparison of integer expressions of different signedness: ‘int’ and ‘unsigned int’ [-Wsign-compare]
--- (3) -O2 -Wall -Wextra ---
6:44: warning: comparison of integer expressions of different signedness: ‘int’ and ‘unsigned int’ [-Wsign-compare]
8:43: warning: array subscript 5 is outside array bounds of ‘int[3]’ [-Warray-bounds=]
--- (4) UBSan 단독 ---
ex.c:7:1: runtime error: 1e+10 is outside the range of representable values of type 'int'
ex.c:4:44: runtime error: shift exponent 40 is too large for 32-bit type 'int'
ex.c:3:44: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
--- (5) ASan 단독 ---
==1439099==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x7a9908700034 at pc 0x57a739836312 ...
SUMMARY: AddressSanitizer: stack-buffer-overflow ex.c:8 in f6
--- 아무것도 안 켠 -O0 실행 ---
-2147483648 256 64 0 -2147483648 0
(exit 0)
--- 아무것도 안 켠 -O2 실행 ---
-2147483648 0 64 0 2147483647 -2090046208
(exit 0)
```

**`-Wall -Wextra` 는 몇 건**

- **1 건**이다. `f4`(부호 비교)만 잡는다.

**`-Wconversion -Wsign-conversion` 을 더하면**

- **여전히 1 건**이다. **새로 잡히는 게 없다.**
- 이 여섯 함정 중 `-Wconversion` 이 잡을 만한 것은 `f3` 하나인데, 그걸 안 잡는다(아래).

**`-O2` 로 올리면**

- **`-Warray-bounds` 가 새로 나온다** — `array subscript 5 is outside array bounds of ‘int[3]’`.
- 이유: `-O0` 에서는 `f6` 이 인라인되지 않아 컴파일러가 **`p` 가 `int[3]` 을 가리킨다는 것을 모른다.**\
  `-O2` 에서 인라인되면서 배열 크기가 보인다.
- ★ **최적화를 켜야 보이는 경고가 있다.** 경고 빌드를 `-O0` 으로만 돌리면 이런 것을 놓친다.

**`f3` 이 `-Wconversion` 으로도 안 잡히는 이유**

쪼개서 확인했다.

```text
unsigned char f1(unsigned char c)        { return c * c; }   -> 경고 없음
unsigned char f2(unsigned char c, int n) { return c * n; }   -> 경고 있음 ★
unsigned char f3(int n)                  { return n; }       -> 경고 있음
unsigned char f4(unsigned char c)        { return c + 1; }   -> 경고 없음
unsigned char f5(unsigned char c)        { return c << 4; }  -> 경고 없음
```

```text
2:53: warning: conversion from ‘int’ to ‘unsigned char’ may change value [-Wconversion]
3:51: warning: conversion from ‘int’ to ‘unsigned char’ may change value [-Wconversion]
```

- gcc 의 `-Wconversion` 에는 「**승격을 되돌리는 변환은 경고하지 않는다**」는 규칙이 있다.
- 모든 피연산자가 목표 타입(`unsigned char`)이면 조용하고, **`int` 가 하나라도 섞이면**(`c * n`) 경고가 난다.
- 그래서 `unsigned char r = c * c;` 는 **실제로 `40000` 을 `64` 로 자르면서 아무 말이 없다.**
- 「`-Wconversion` 켰으니 절단은 다 보인다」가 틀린 것이다.

**UBSan 기본 집합이 `f5` 를 안 잡는 이유**

```text
--- -fsanitize=undefined 만 ---   (f5 에 대해 아무 말 없음)
--- -fsanitize=float-cast-overflow ---
ex.c:4:1: runtime error: 1e+10 is outside the range of representable values of type 'int'
ex.c:5:1: runtime error: -nan is outside the range of representable values of type 'int'
ex.c:6:1: runtime error: -1 is outside the range of representable values of type 'unsigned int'
```

- gcc 13 의 `-fsanitize=undefined` 에 **`float-cast-overflow` 가 포함되어 있지 않다.** 따로 켜야 한다.
- (`float-divide-by-zero` 도 마찬가지다 — 별도로 확인했다.)
- 실무 형태: **`-fsanitize=undefined,address,float-cast-overflow -fno-sanitize-recover=all`**

**아무 도구도 안 켜면**

```text
  -O0 :  -2147483648   256   64   0   -2147483648    0
  -O2 :  -2147483648     0   64   0    2147483647   -2090046208
                       ^^^            ^^^^^^^^^^   ^^^^^^^^^^^
  여섯 값 중 ★ 세 개가 다르다. 둘 다 exit 0.
```

- **종료 코드는 둘 다 0** 이다. 에러도 경고도 없다.
- 이 프로그램이 테스트를 통과했다면 그 테스트는 **`-O0` 빌드의 우연**을 고정한 것이다.

**정리한 표**

| 함정 | `-Wall -Wextra` | `+-Wconversion` | `-O2` | UBSan 기본 | ASan |
|---|---|---|---|---|---|
| 부호 있는 오버플로 (`f1`) | ✗ | ✗ | ✗ | **✓** | ✗ |
| 시프트 폭 초과 — 변수 (`f2`) | ✗ | ✗ | ✗ | **✓** | ✗ |
| 시프트 폭 초과 — 상수 | **✓** | ✓ | ✓ | ✓ | ✗ |
| 승격 후 절단 (`f3`) | ✗ | **✗** ★ | ✗ | ✗ (UB 아님) | ✗ |
| 부호 비교 (`f4`) | **✓**(`-Wextra`) | ✓ | ✓ | ✗ (UB 아님) | ✗ |
| 범위 밖 부동→정수 (`f5`) | ✗ | ✗ | ✗ | **✗** ★ 따로 켜야 함 | ✗ |
| 배열 밖 (`f6`) | ✗ | ✗ | **✓** ★ | ✗ | **✓** |

### 10. 왜 부호 있는 것만 UB 인가

**부호 없는 쪽만 정의된 이유**

- 부호 없는 정수의 연산은 「**2^N 으로 나눈 나머지**」라고 표준이 정의했다.\
  모든 구현에서 같은 답이 나오고, 해시·체크섬·순환 버퍼가 이것에 의존한다.
- 부호 있는 쪽은 **표현 방식이 여럿이었다.** C 표준은 오랫동안 2의 보수·1의 보수·부호+크기 셋을 허용했고,\
  세 표현에서 오버플로 결과가 제각각이라 「**하나로 정의할 수가 없었다**」.

**C23 에서 2의 보수로 못박혔는데도 UB 인 이유**

- **표현과 연산 정의는 별개**다. 「비트가 어떻게 생겼나」가 정해졌다고 「넘쳤을 때 무슨 일이 나나」가 정해지지 않는다.
- 그리고 UB 로 두는 쪽이 **최적화에 쓸모가 있어서** 의도적으로 남겼다.

**UB 로 두면 컴파일러가 할 수 있는 것**

실측 두 가지다.

```text
① 비교를 상수로 접는다

   int always_true(int a) { return a + 1 > a; }

   -O2 기본     : mov eax, 1               <- 무조건 참으로 접었다
   -O2 -fwrapv  : cmp edi, 2147483647      <- 진짜로 비교한다
                  setne al
   실행 결과    : 1  /  0    ★ 답이 갈린다

② 루프 종료 조건을 지운다  (5번 (B))

   for (int i = INT_MAX-2; i > 0; i++) n++;
   -O2 : 무한 루프 (i > 0 이 항상 참이라고 보고 지웠다)
```

- ①은 **`-O0` 에서도 그렇다.** gcc 가 프런트엔드 단계에서 접기 때문에 `-O0` 어셈블리에도 `mov eax, 1` 만 있다.
- 이것이 실무에서 쓸모 있는 이유: 루프 변수가 안 넘친다고 가정할 수 있으면\
  `for (int i = 0; i < n; i++)` 의 `i` 를 64비트 레지스터에 두고 부호 확장을 생략할 수 있다.

**「일으킨 뒤에 검사」할 수 없는 이유**

```c
int r = a + b;
if (r < a) return -1;    /* 넘쳤으면 ... 이 검사가 살아남나? */
```

- **이 검사는 논리적으로 성립하지 않는다.** `a + b` 가 이미 UB 이므로 `r` 에 「넘친 값」이라는 게 없다.\
  컴파일러는 UB 가 없다고 가정하고 `r >= a` 라고 추론해 **검사를 지울 자격이 있다.**
- 다만 ★ **이 gcc 13.3.0 의 `-O2` 는 실제로는 안 지웠다.**

```text
overflow_check_after:
	lea	eax, [rdi+rsi]
	cmp	edi, eax          <- 검사가 남아 있다
	jg	.L5
	ret
--- 실행 ---
overflow_check_after(INT_MAX, 1) = -1   (-O0 · -O2 모두)
```

- **「이 컴파일러가 안 지웠다」는 「안전하다」가 아니다.** 지울 자격이 있고 버전이 바뀌면 지울 수 있다.\
  ★ 이것이 이 갈래의 제1 규칙이 가장 날카롭게 드러나는 자리다 — **관찰은 관찰일 뿐 보장이 아니다.**
- 그리고 `always_true` 쪽은 **실제로 지워졌다.** 같은 빌드에서 하나는 살고 하나는 죽었다.
- 덧붙여 **UBSan 도 `always_true` 를 못 잡았다.**

```text
ex.c:4:9: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
overflow_check_after(INT_MAX, 1) = -1
always_true(INT_MAX) = 1
```

  한 건만 나왔고 그건 `overflow_check_after` 의 `a + b` 다.\
  `always_true` 의 덧셈은 **코드에서 사라진 뒤라 검사할 것이 없었다.**\
  ★ **sanitizer 는 런타임까지 살아남은 UB 만 잡는다.**

**올바른 형태**

```c
if (b > 0 && a > INT_MAX - b) return -1;    /* 넘치기 전에 검사 */
if (b < 0 && a < INT_MIN - b) return -1;
int r = a + b;
```

- 정본은 목록의 **54번 주제**.

### 11. 그래서 어떻게 쓰나

**인덱스와 길이를 비교하는 올바른 형태**

```c
for (size_t i = 0; i < n; i++) { }                  /* 양쪽 다 부호 없음 */
for (ptrdiff_t i = 0; i < (ptrdiff_t)n; i++) { }    /* 양쪽 다 부호 있음 */
```

- **섞지 않는 것**이 규칙이다. 어느 쪽으로 맞추든 상관없다.
- `int i` 와 `size_t n` 을 섞으면 `-Wsign-compare` 가 매번 운다 — **그 경고를 끄지 말고 코드를 고친다.**

**역방향 루프**

```c
for (size_t i = n; i-- > 0;) { /* i 는 n-1 부터 0 까지 */ }
```

- 조건 안에서 감소시키므로 `i == 0` 일 때 조건이 거짓이 되면서 감소해 **래핑 뒤의 값을 안 쓴다.**

**`if (i < len - 1)` 고치기**

```c
if (i + 1 < len) { }     /* len 이 0 이어도 안전하다 */
```

- `len - 1` 은 `len == 0` 일 때 **`SIZE_MAX`** 가 되어 조건이 언제나 참이 된다.
- 뺄셈을 덧셈으로 옮기면 사라진다(단 `i + 1` 이 넘칠 수 있으면 그쪽을 따로 본다).

**빌드 플래그 한 줄**

```text
개발 빌드
  gcc -std=c17 -O2 -Wall -Wextra -Wconversion -Wsign-conversion -Wshadow -Werror

테스트 빌드 (별도 잡)
  gcc -std=c17 -O1 -g -fsanitize=undefined,address,float-cast-overflow \
      -fno-sanitize-recover=all
```

- **`-O2` 로도 한 번 컴파일한다** — `-Warray-bounds` 처럼 최적화를 켜야 나오는 경고가 있다.
- **`-fno-sanitize-recover=all`** 을 켠다 — 안 켜면 UB 를 보고하고 **계속 돌아서** CI 가 초록이 된다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 플래그로 돌렸나 |
|---|---|---|
| 부호 비교 묶음 | `-1 < 1u`·`k < sizeof(...)`·`c*c`·`us*us` 값과 `-Wsign-compare` | `-O0` `-Wall -Wextra` · `+-Wconversion -Wsign-compare` |
| 플래그별 경고 수 | `-Wsign-compare` 가 **`-Wextra`** 에만 있음 | 없음 / `-Wall` / `-Wextra` / `-Wall -Wextra` / `-Wsign-compare` |
| `_Generic` 변환표 | 승격 8건 + 통상 산술 변환 14건 + 값 4건 | `-std=c17 -Wall -Wextra` |
| `INT_MAX+1` (A) 단순 덧셈 | **네 수준 값 동일** · ubsan 만 잡음 · `-fno-sanitize-recover` 로 exit 1 | `-O0`·`-O1`·`-O2`·`-O3`·ubsan·`-O2 -fwrapv` |
| `INT_MAX+1` (B) 루프 | `-O0`/`-O1` = 3 · **`-O2` 무한 루프(exit 124)** · `-fwrapv` = 3 · ubsan exit 1 | 같은 셋 + `-fwrapv` |
| `-Waggressive-loop-optimizations` | `-O1` 부터 기본 활성(`-w` 로만 꺼짐) | `-O1` / `-O1 -w` / `-O2` |
| 부호 없는 루프·랩 | 세 수준 결과 동일 · 경고 0 · ubsan 조용 | `-O0`·`-O2`·ubsan |
| 시프트 3형태 | `-O0` `1`/`-2147483648` ↔ `-O2` `0`/`0` · ubsan 3건 **다른 문장** · 위치 합치면 1건만 | `-O0`·`-O2`·ubsan · `-S -masm=intel` |
| `-Wshift-count-overflow` | 상수 시프트만 컴파일 시간에 잡힘 | `-Wall -Wextra` |
| 여섯 함정 커버리지 | 경고 1건 → `-Wconversion` 으로도 1건 → `-O2` 에서 `-Warray-bounds` 추가 | `-Wall -Wextra` · `+-Wconversion` · `-O2` · UBSan · ASan |
| `-Wconversion` 승격 예외 | `c*c` 무경고 / `c*n` 경고 — 5형태로 경계 확인 | `-Wall -Wextra -Wconversion -Wsign-conversion` |
| `float-cast-overflow` | `-fsanitize=undefined` 에 **미포함** | `-fsanitize=undefined` vs `,float-cast-overflow` |
| 역방향 `size_t` 루프 | `-Wtype-limits`(`-Wextra`) · 쓰레기 값 exit 0 · ASan underflow | `-Wall`/`-Wextra`/`-Wtype-limits` · ASan |
| `always_true` / `overflow_check_after` | `a+1>a` 가 `-O0` 에서도 상수 접힘 · `-fwrapv` 로 답이 1→0 · 사후 검사는 **안 지워짐** · ubsan 이 접힌 쪽을 못 잡음 | `-O0`·`-O2`·`-O2 -fwrapv`·ubsan · `-S -masm=intel` |

**구현 의존 항목** — 이 표의 값 중 다음은 **이 환경(x86-64 Linux · LP64 · gcc 13.3.0)에서만** 그렇다.

- `int` 가 4바이트인 것 → **무엇이 `int` 로 승격되는지가 여기 달려 있다.**\
  16비트 `int` 환경이면 `unsigned short` 가 `unsigned int` 로 승격되어 3번의 `us * us` 가 **UB 가 아니게 된다.**
- `long` 이 8바이트인 것 → 4번의 `ll + ul` 이 `unsigned long long` 이 된 이유. LLP64 에서는 `long long` 이 된다.
- `1 << 32` 가 `-O0` 에서 `1` 인 것 — **x86 의 시프트 마스킹** 때문이다. ARM 은 다르다(여기서 확인 못 했다).
- `-O2` 에서 무한 루프가 된 것 · `always_true` 가 접힌 것 — **이 gcc 의 선택**이다.\
  UB 라 다른 컴파일러·버전에서 다른 결과가 나올 수 있다.
- `overflow_check_after` 의 사후 검사가 **살아남은 것** — 지울 자격이 있는데 안 지웠다. **보장이 아니다.**
- `-Wsign-compare`/`-Wtype-limits` 가 `-Wextra` 에 있는 것 · UBSan 기본 집합의 구성 — gcc 의 것이다.

**안 돌려 본 것**

- `-ftrapv` · `__builtin_add_overflow` 계열 · 16비트 `int` 환경 · ARM 의 시프트 동작.

**버전이 올랐을 때 다시 돌려야 하는 것**

- **전부다.** 이 문서의 UB 관련 값은 하나도 보장이 아니다.
- 특히 `overflow_check_after` 가 살아남는지, `-O2` 루프가 여전히 무한인지는 **gcc 가 올라갈 때마다 다시 찍는다.**
