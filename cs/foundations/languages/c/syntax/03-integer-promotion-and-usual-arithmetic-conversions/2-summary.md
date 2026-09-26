# c/syntax/03 — 정수 승격과 통상 산술 변환: 말없이 일어나는 변환 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — Implicit conversions (C)](https://en.cppreference.com/w/c/language/conversion) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html) · [GCC 13 — Integers (구현 정의 동작)](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Integers-implementation.html)
> **실행 검증** — 이 문서의 모든 출력·경고는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> **UB 가 걸린 블록은 예외 없이 `-O0`·`-O2`·sanitizer 셋으로 돌렸다.** 한 수준만 돌린 결과는 이 문서에 싣지 않는다.\
> 대조용으로 `clang 18.1.3` 도 썼고, 그 자리는 블록마다 밝혔다.
> **버전** — 승격·통상 산술 변환 규칙은 C89 부터 같다. C23 에서 부호 표현이 **2의 보수로 못박혔지만** 부호 있는 오버플로는 **여전히 UB** 다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> **경계** — 「C 의 미정의 동작이 왜 정합성 도메인에서 최악인가」는 [`../../../c-cpp-csharp.md`](../../../c-cpp-csharp.md) 가 정본이다.\
> 여기는 **어떤 코드가 그것을 만드나**만 쓴다.

## 한눈에 — 쉽게 말하면

**C 의 산술 연산자는 서로 다른 타입을 못 받는다. 그래서 연산 전에 몰래 둘을 같은 타입으로 맞춘다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 씨름판에 오르기 전 **체급을 맞추는 계체** | 연산 전에 두 피연산자를 한 타입으로 맞추는 것 |
| 1단계 — 경량급은 **무조건 `int` 급으로 올린다** | **정수 승격**(integer promotion) — `char`·`short`·`_Bool` → `int` |
| 2단계 — 둘의 체급이 다르면 **높은 쪽으로 맞춘다** | **통상 산술 변환**(usual arithmetic conversions) |
| 체급이 같은데 **한쪽만** 「**무제한급**」이면 그쪽으로 | 폭이 같고 부호가 다르면 **부호 없는 쪽으로** ★ |
| 계체 결과는 **전광판에 안 나온다** | 소스에 아무 표시가 없다 — 그래서 조용히 틀린다 |

- 이 계체에서 사고가 나는 자리는 **딱 하나**다 — 「폭이 같은데 부호가 다르면 부호 없는 쪽으로」.
- `-1 < 1u` 를 물으면 `-1` 이 **`4294967295`** 가 되어 답이 **거짓**이 된다.
- 그리고 C 는 여기서 한 번 더 함정을 판다.\
  **부호 있는 정수가 넘치면 UB**(아무 일이나 일어날 수 있음)이고, **부호 없는 정수가 넘치면 모듈러**(정의된 동작)다.\
  같은 「넘침」인데 한쪽은 아무 일이나, 한쪽은 정확히 정해진 일이 일어난다.

```text
   int i = -1;        unsigned u = 1;        i < u  ?

   계체 전                        계체 후
   i : int      -1                i : unsigned  4294967295   <- 비트는 그대로, 해석만 바뀐다
   u : unsigned  1                u : unsigned           1

   -> 4294967295 < 1 -> 거짓
```

실무에서 이게 터지는 자리는 **`sizeof` 와의 비교**와 **길이 계산**이다.\
`if (i < sizeof(arr)/sizeof(arr[0]))` 는 `i` 가 음수일 때 조용히 참이 되고, `len - 1` 은 `len` 이 0일 때 `SIZE_MAX` 가 된다.

> **정수 승격(integer promotion)** — `int` 보다 좁은 정수 타입을 연산 전에 `int`(안 들어가면 `unsigned int`)로 올리는 것.\
> 예: `unsigned char c = 200;` 일 때 `c * c` 는 `unsigned char` 끼리가 아니라 **`int` 끼리 곱해져** `40000` 이 된다.

> **통상 산술 변환(usual arithmetic conversions)** — 승격이 끝난 두 피연산자를 다시 한 타입으로 맞추는 규칙.\
> 예: `int + unsigned` 는 `unsigned` 가 되고, `int + long` 은 `long` 이 된다.

> **UB(undefined behavior, 미정의 동작)** — 표준이 「어떻게 되는지 정의하지 않은」 것. 아무 일이나 일어나도 된다.\
> 예: 부호 있는 정수 오버플로. 값이 이상해질 수도 있고, **최적화기가 그 코드가 일어나지 않는다고 가정해 루프를 통째로 없앨 수도** 있다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `a op b` 를 쓰면 **어느 타입으로 계산되는가** — 그 결정 순서를 도식으로 말할 수 있는가.
2. `-1 < 1u` 가 거짓인 것과 `unsigned char c=200; c*c` 가 `40000` 인 것은 **같은 규칙인가 다른 규칙인가.**
3. 넘쳤을 때 **부호 있는 쪽과 없는 쪽이 왜 다른가** — 그리고 그 차이를 무엇으로 잡는가.

## 동작 방식

### (1) 2단계 계체 — 승격 먼저, 그 다음 통상 산술 변환

**언제 쓰나** — 이항 산술 연산자(`+ - * / % < > == & | ^`)를 쓸 때마다. 즉 **거의 모든 줄에서.**

```text
  a op b
    |
    v
  [1단계] 정수 승격 — 각 피연산자를 따로
    _Bool / char / signed char / unsigned char / short / unsigned short
        -> int  (int 가 그 값을 전부 담으면)
        -> unsigned int  (못 담으면)
    int 이상은 그대로
    |
    v
  [2단계] 통상 산술 변환 — 둘을 비교해서
    ① 한쪽이 부동소수면 넓은 부동소수 쪽으로
    ② 둘 다 정수:
       ②-1 타입이 같으면 끝
       ②-2 부호가 같으면 rank 높은 쪽
       ②-3 부호가 다르고 '부호 없는 쪽'의 rank 가 크거나 같으면 -> 부호 없는 쪽 ★
       ②-4 부호가 다르고 '부호 있는 쪽'이 상대 값을 전부 담으면 -> 부호 있는 쪽
       ②-5 둘 다 아니면 -> 부호 있는 쪽의 "부호 없는 판"
```

> **rank(정수 변환 등급)** — 정수 타입의 서열. `_Bool` < `char` < `short` < `int` < `long` < `long long`.\
> 부호 있는 것과 없는 것은 **같은 등급**이다 — `int` 와 `unsigned int` 의 rank 가 같다. 그래서 ②-3 이 필요하다.

`_Generic` 으로 실제 결과 타입을 전수로 찍었다.

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

그림 해설 (한 단계씩):

- **1단계에서 `unsigned char`·`unsigned short` 도 `int` 가 된다.** 부호가 없어도 `int` 로 간다 —\
  이 환경의 `int` 가 그 값들을 전부 담기 때문이다. 16비트 `int` 환경이면 `unsigned short` 는 `unsigned int` 가 된다.
- `char + char` 가 `int` 인 것이 1단계의 결과다. **`char` 끼리 더해도 `char` 가 아니다.**
- `int + unsigned` → `unsigned`(②-3, rank 같음) 인데 `unsigned + long` → `long`(②-4, `long` 이 8바이트라 담는다)이다.\
  **한 줄 차이로 규칙이 갈린다.**
- `long long + unsigned long` → **`unsigned long long`**(②-5). 둘 다 64비트라 `long long` 이 `unsigned long` 을 못 담고,\
  그래서 rank 높은 쪽의 부호 없는 판이 된다. **어느 쪽도 원래 타입이 아니다.**
- `unsigned long + double` → `double`. 정수는 ①에서 통째로 밀린다 — 정밀도 손실이 있어도 그렇다\
  ([`04-floating-point-types-and-conversions/`](../04-floating-point-types-and-conversions/)).

비용 — 없다. 대부분 컴파일 시간에 끝난다. **비용은 「틀린 줄 모르는 것」이다.**

### (2) `-1 < 1u` — 이 갈래 최고의 예제

**언제 쓰나** — 부호 있는 값과 부호 없는 값을 비교할 때. `sizeof`·`strlen`·`.size()` 가 전부 부호 없다.

```text
  int i = -1;                     unsigned u = 1;

  비트 (32비트)                    비트 (32비트)
  1111 1111 ... 1111 1111          0000 0000 ... 0000 0001
  = -1 로 읽으면                    = 1

  계체: rank 가 같고(int/unsigned int) 부호가 다르다 -> ②-3 -> 부호 없는 쪽

  i 의 비트는 한 비트도 안 바뀐다. 해석만 바뀐다.
  1111 1111 ... 1111 1111 = 4294967295

  4294967295 < 1  ->  거짓
```

실제 출력과 경고를 같이 싣는다.

```text
$ gcc -std=c17 -Wall -Wextra ex.c -o /tmp/x
ex.c:5:42: warning: comparison of integer expressions of different signedness: ‘int’ and ‘unsigned int’ [-Wsign-compare]
    5 |     printf("-1 < 1u          : %d\n", -1 < 1u);
      |                                          ^
ex.c:6:41: warning: comparison of integer expressions of different signedness: ‘int’ and ‘unsigned int’ [-Wsign-compare]
    6 |     printf("i < u            : %d\n", i < u);
      |                                         ^
ex.c:14:51: warning: comparison of integer expressions of different signedness: ‘int’ and ‘long unsigned int’ [-Wsign-compare]
   14 |     printf("k < sizeof(a)/sizeof(a[0]) : %d\n", k < sizeof(a)/sizeof(a[0]));
      |                                                   ^
$ /tmp/x
-1 < 1u          : 0
i < u            : 0
(int)-1 < (int)1 : 1
(unsigned)(-1)   : 4294967295
-1 as unsigned   : 4294967295
sizeof(a)/sizeof(a[0]) = 10
k < sizeof(a)/sizeof(a[0]) : 0
k < (int)(sizeof(a)/sizeof(a[0])) : 1
c * c            : 40000
(unsigned char)(c*c) : 64
sc * 2           : -200
us * us          : -131071
```

그림 해설 (한 단계씩):

- `-1 < 1u` 가 **`0`(거짓)** 이다. `-1 < 1` 은 `1`(참)이다. **`u` 한 글자에 답이 뒤집혔다.**
- `k < sizeof(a)/sizeof(a[0])` 도 `0` 이다 — `k` 가 `-1` 인데 배열 길이 10보다 작지 않다고 한다.\
  `(int)` 로 캐스트하면 `1` 이 된다.
- **이 사고는 `-Wsign-compare` 가 잡는다.** 세 자리 전부 경고가 붙었다.
- **`-Wsign-compare` 는 `-Wall` 에 없고 `-Wextra` 에 있다.** 플래그별로 세어 확인했다.

```text
(플래그 없음) : 경고 0 건
-Wall         : 경고 0 건
-Wextra       : 경고 1 건
-Wall -Wextra : 경고 1 건
-Wsign-compare: 경고 1 건
```

- **`-Wall` 만 켜고 안심하면 이 사고가 통째로 안 보인다.**

비용 — 없다. 값이 틀릴 뿐이다.

### (3) `unsigned char c = 200; c * c` — 이건 다른 규칙이다

**언제 쓰나** — 좁은 타입으로 계산할 때. (2)와 헷갈리기 쉬운데 **1단계(승격)의 이야기**다.

```text
  unsigned char c = 200;      c * c  는?

  "unsigned char 끼리니까 200*200 = 40000 이 255 를 넘어 모듈러로 64" ?   ← 틀렸다

  실제:
    [1단계] c 를 int 로 승격                 200 (int)
            c 를 int 로 승격                 200 (int)
    [2단계] 둘 다 int, 할 일 없음
    계산:   200 * 200 = 40000  (int 로)      <- 절단이 안 일어난다

    unsigned char r = c * c;  라고 써야 비로소 40000 -> 64 로 절단된다
```

위 출력의 해당 줄이다.

```text
c * c            : 40000
(unsigned char)(c*c) : 64
sc * 2           : -200
us * us          : -131071
```

그림 해설 (한 단계씩):

- `c * c` 는 **`40000`** 이다. `unsigned char` 의 범위를 넘지만 **계산이 `int` 로 되니 아무 일이 없다.**
- `sc * 2` 가 `-200` 인 것도 같다 — `signed char` 범위(`-128\~127`) 밖인데 `int` 라 멀쩡하다.
- **`us * us` 만 `-131071` 이라는 이상한 값**이다. 이게 왜 다른가:

```text
  unsigned short us = 65535;   us * us = ?

  [1단계] unsigned short -> int   (이 환경의 int 가 0~65535 를 전부 담으므로)
  계산:   65535 * 65535 = 4294836225   <- int 로 계산
          INT_MAX = 2147483647   <- 넘는다!

  -> ★ 부호 있는 정수 오버플로 = UB
```

- 「**부호 없는 값끼리 곱했는데 부호 있는 오버플로 UB 가 났다**.」\
  승격이 `int`(부호 있음)로 올렸기 때문이다. 이것이 승격의 가장 고약한 결과다.
- sanitizer 가 잡아 준다.

```text
ex.c:13:5: runtime error: signed integer overflow: 65535 * 65535 cannot be represented in type 'int'
```

- 고치는 법: **곱하기 전에 `unsigned` 로 올린다** — `(unsigned)us * us`.

비용 — 없다. 타입 캐스트 하나다.

### (4) `INT_MAX + 1` — 세 도구로 돌려야 보인다

**언제 쓰나** — 오버플로가 걸린 코드를 판단할 때. **한 수준만 돌리면 거짓 결론이 난다.**

먼저 **단순한 덧셈**부터. 예상과 달랐던 자리다.

```c
int add_one(int x) { return x + 1; }
int x = INT_MAX;
printf("x + 1 = %d\n", add_one(x));
```

```text
=== -O0 ===        INT_MAX = 2147483647 / x + 1   = -2147483648  (exit 0)
=== -O1 ===        INT_MAX = 2147483647 / x + 1   = -2147483648  (exit 0)
=== -O2 ===        INT_MAX = 2147483647 / x + 1   = -2147483648  (exit 0)
=== -O3 ===        INT_MAX = 2147483647 / x + 1   = -2147483648  (exit 0)
=== -fsanitize=undefined (-O0) ===
ex.c:4:31: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
INT_MAX = 2147483647
x + 1   = -2147483648
=== -fsanitize=undefined -fno-sanitize-recover=all ===
ex.c:4:31: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
(exit 1)
=== -O2 -fwrapv ===  INT_MAX = 2147483647 / x + 1 = -2147483648  (exit 0)
```

- **네 최적화 수준의 값이 전부 같다.** `-2147483648`.
- **「값이 달라진다」가 UB 의 증상이 아니다.** 이 경우 값은 안 달라졌고 **sanitizer 만 UB 라고 말했다.**
- 여기서 멈추면 「어차피 랩어라운드하네」라고 잘못 배운다.

그래서 **같은 UB 를 루프 조건에 넣으면** 무엇이 달라지는지 봐야 한다.

```c
int n = 0;
for (int i = INT_MAX - 2; i > 0; i++) n++;
printf("n = %d\n", n);
```

```text
=== -O0 ===
n = 3
(exit 0)
=== -O1 ===
ex.c:6:39: warning: iteration 2 invokes undefined behavior [-Waggressive-loop-optimizations]
    6 |     for (int i = INT_MAX - 2; i > 0; i++) n++;
      |                                      ~^~
ex.c:6:33: note: within this loop
n = 3
(exit 0)
=== -O2 ===
ex.c:6:39: warning: iteration 2 invokes undefined behavior [-Waggressive-loop-optimizations]
(exit 124)      <- ★ 5초 timeout. 무한 루프.
=== -O2 -fwrapv ===
n = 3
(exit 0)
=== -O2 -fsanitize=undefined -fno-sanitize-recover=all ===
ex.c:6:39: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
(exit 1)
```

```text
   같은 소스, 플래그만 다르다

   -O0                -O2                -O2 -fwrapv        -fsanitize=undefined
   +-------------+    +-------------+    +-------------+    +-------------------+
   | n = 3       |    | (영원히 안  |    | n = 3       |    | runtime error 후  |
   | 정상 종료    |    |  끝난다)     |    | 정상 종료    |    | exit 1            |
   +-------------+    +-------------+    +-------------+    +-------------------+
        |                   |                  |                    |
    랩어라운드했다      "i 는 절대 안          랩어라운드를         UB 를 잡아서
                        넘친다"고 가정해       언어 규칙으로        멈췄다
                        i > 0 을 지웠다        보장시켰다
```

그림 해설 (한 단계씩):

- **`-O0` 은 `3`, `-O2` 는 무한 루프다.** 같은 프로그램이다.
- 최적화기는 「부호 있는 오버플로는 UB → 일어나지 않는다 → `i` 는 `INT_MAX-2` 에서 계속 커지기만 한다 → `i > 0` 은 언제나 참」이라고 추론하고 **조건 검사를 지웠다.**
- **gcc 가 `-O1` 부터 경고를 준다** — `iteration 2 invokes undefined behavior`. 컴파일러가 UB 를 안다고 말하면서 최적화한 것이다.
- `-fwrapv` 는 「**부호 있는 오버플로를 2의 보수 랩어라운드로 정의한다**」고 컴파일러에게 시키는 플래그다.\
  그 순간 UB 가 아니게 되어 최적화기가 저 추론을 못 한다.
- 이것이 이 갈래의 제1 규칙이 필요한 이유다 — **「`-O0` 에서 잘 돌던데요」는 아무것도 증명하지 않는다.**

비용 — `-fwrapv` 는 최적화 기회를 줄인다. 근본 해법은 **넘치기 전에 검사하는 것**이다(목록의 **54번 주제**).

### (5) 부호 없는 정수는 UB 가 아니다 — 모듈러다

**언제 쓰나** — (4)와 대조할 때. 이 대조가 이 주제의 결론을 만든다.

같은 모양의 루프를 `unsigned` 로 바꿨다.

```c
unsigned n = 0;
for (unsigned i = UINT_MAX - 2; i > 0; i++) n++;
```

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

그림 해설 (한 단계씩):

- **셋이 완전히 같다.** 경고도 없고 sanitizer 도 조용하다.
- 부호 없는 연산은 **2^N 으로 나눈 나머지**로 정의되어 있다 — 표준이 정한 것이다.
- 그래서 `UINT_MAX + 1 == 0` 과 `0u - 1 == UINT_MAX` 는 **보장된 동작**이다. 해시·체크섬이 이것에 의존한다.
- 정리하면:

```text
                 넘쳤을 때              최적화기가              sanitizer
  --------------  --------------------  ---------------------  -----------
  부호 있는 정수   ★ UB                  "안 일어난다"고 가정    잡는다
  부호 없는 정수     2^N 모듈러 (정의됨)   아무 가정 못 함         조용하다
```

- **역설**: 부호 없는 쪽이 안전해 보이지만, `-1` 이 `4294967295` 가 되는 (2)의 사고는 부호 없는 쪽에서만 난다.\
  **어느 쪽도 공짜가 아니다.**

비용 — 없다.

### (6) 시프트 — 여기서는 최적화 수준이 값을 바꾼다

**언제 쓰나** — 비트 연산. 정본은 [목록의 **11번 주제**](../11-bitwise-operations-and-shifts/)이고, 여기서는 **승격과 UB** 만 본다.

```c
int over31(int v, int s) { return v << s; }   /* 1 << 31 */
int cnt32 (int v, int s) { return v << s; }   /* 1 << 32 */
int cntneg(int v, int s) { return v << s; }   /* 1 << -1 */
```

```text
=== -O0 ===
1 << 31 = -2147483648
1 << 32 = 1                 ★
1 << -1 = -2147483648       ★
=== -O2 ===
1 << 31 = -2147483648
1 << 32 = 0                 ★ 달라졌다
1 << -1 = 0                 ★ 달라졌다
=== ubsan -O0 ===
ex.c:2:37: runtime error: left shift of 1 by 31 places cannot be represented in type 'int'
ex.c:3:37: runtime error: shift exponent 32 is too large for 32-bit type 'int'
ex.c:4:37: runtime error: shift exponent -1 is negative
1 << 31 = -2147483648
1 << 32 = 1
1 << -1 = -2147483648
```

왜 갈렸는지는 어셈블리가 말해 준다.

```text
=== -O0 : cnt32 ===                  === -O2 : 상수 접기된 1 << 32 ===
	mov	eax, DWORD PTR -8[rbp]        cnt32_const:
	mov	edx, DWORD PTR -4[rbp]        	endbr64
	mov	ecx, eax                      	xor	eax, eax        <- 0 으로 접었다
	sal	edx, cl                       	ret
	mov	eax, edx
```

그림 해설 (한 단계씩):

- **`-O0` 은 런타임 시프트**다. x86 의 `sal` 명령이 시프트 횟수를 **하위 5비트만 본다** — `32 & 31 = 0` 이라 `1 << 0 = 1`.
- **`-O2` 는 인라인 후 상수 접기**다. gcc 가 `1 << 32` 를 **`0`** 으로 접었다.
- **하드웨어가 한 일과 컴파일러가 한 일이 다르다.** 둘 다 「맞다」 — UB 라 정답이 없기 때문이다.
- 상수로 쓰면 컴파일 시간 경고가 나온다.

```text
ex.c:2:36: warning: left shift count >= width of type [-Wshift-count-overflow]
    2 | int cnt32_const(void)   { return 1 << 32; }
      |                                    ^~
```

- 그런데 **변수로 넘기면 그 경고가 안 나온다.** 위 세 함수에 `-Wall -Wextra` 로 경고가 하나도 안 붙었다.
- UBSan 은 셋을 다 잡는데 **주의할 점이 있다** — 같은 소스 위치의 UB 는 **처음 한 번만 보고**한다.\
  세 함수로 나눠 놓지 않고 한 함수에 세 번 넘겼더니 **첫 건만 나왔다.**

비용 — 없다. 시프트량을 검사하거나 `unsigned` 로 시프트한다.

### (7) 경고로 잡히는 것과 안 잡히는 것 — 전수

**언제 쓰나** — 빌드 플래그를 정할 때. 「경고를 켰으니 안전하다」를 검증하는 자리다.

여섯 가지 함정을 한 파일에 넣고 도구를 하나씩 켜 봤다.

```c
int f1(int a, int b)             { return a + b; }   /* 부호 있는 오버플로 */
int f2(int v, int s)             { return v << s; }  /* 시프트 폭 초과 */
unsigned char f3(unsigned char c){ return c * c; }   /* 승격 후 절단 */
int f4(int i, unsigned u)        { return i < u; }   /* 부호 비교 */
int f5(double d)                 { return (int)d; }  /* 범위 밖 부동->정수 */
int f6(int *p)                   { return p[5]; }    /* 배열 밖 (a 는 int[3]) */
```

```text
--- (1) -Wall -Wextra ---
경고 1 건
--- (2) + -Wconversion -Wsign-conversion ---
6:44: warning: comparison of integer expressions of different signedness: ‘int’ and ‘unsigned int’ [-Wsign-compare]
--- (3) -O2 -Wall -Wextra (최적화가 켜지면 더 보인다) ---
6:44: warning: comparison of integer expressions of different signedness: ‘int’ and ‘unsigned int’ [-Wsign-compare]
8:43: warning: array subscript 5 is outside array bounds of ‘int[3]’ [-Warray-bounds=]
--- (4) UBSan 단독 ---
ex.c:7:1: runtime error: 1e+10 is outside the range of representable values of type 'int'
ex.c:4:44: runtime error: shift exponent 40 is too large for 32-bit type 'int'
ex.c:3:44: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
--- (5) ASan 단독 ---
==1439099==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x7a9908700034 ...
SUMMARY: AddressSanitizer: stack-buffer-overflow ex.c:8 in f6
--- 아무것도 안 켠 -O0 실행 ---
-2147483648 256 64 0 -2147483648 0
(exit 0)
--- 아무것도 안 켠 -O2 실행 ---
-2147483648 0 64 0 2147483647 -2090046208
(exit 0)
```

```text
  여섯 열 중 세 열이 최적화 수준에 따라 달라진다.

  -O0 :  -2147483648   256   64   0   -2147483648   0
  -O2 :  -2147483648     0   64   0    2147483647   -2090046208
                       ^^^            ^^^^^^^^^^   ^^^^^^^^^^^
  둘 다 exit 0. 에러도 경고도 없다.
```

| 함정 | `-Wall -Wextra` | `+-Wconversion` | `-O2` 로 올리면 | UBSan | ASan |
|---|---|---|---|---|---|
| 부호 있는 오버플로 (`f1`) | ✗ | ✗ | ✗ | **✓** | ✗ |
| 시프트 폭 초과 — 변수 (`f2`) | ✗ | ✗ | ✗ | **✓** | ✗ |
| 시프트 폭 초과 — 상수 | **✓** `-Wshift-count-overflow` | ✓ | ✓ | ✓ | ✗ |
| 승격 후 절단 (`f3`) | ✗ | **✗** ★ | ✗ | ✗ (UB 가 아니다) | ✗ |
| 부호 비교 (`f4`) | **✓** `-Wsign-compare`(`-Wextra`) | ✓ | ✓ | ✗ (UB 가 아니다) | ✗ |
| 범위 밖 부동→정수 (`f5`) | ✗ | ✗ | ✗ | **✗** ★ 따로 켜야 함 | ✗ |
| 배열 밖 (`f6`) | ✗ | ✗ | **✓** `-Warray-bounds` | ✗ | **✓** |

그림 해설 (한 단계씩):

- ★ **`-Wconversion` 이 `unsigned char r = c * c;` 를 안 잡는다.** 이 표에서 가장 뜻밖이었다.\
  gcc 에는 **승격을 되돌리는 변환은 경고하지 않는다**는 규칙이 있다. 쪼개서 확인했다.

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

  **모든 피연산자가 목표 타입이면 조용**하고, `int` 가 하나라도 섞이면 경고가 난다.\
  「`-Wconversion` 켰으니 절단은 다 보인다」가 틀린 것이다.

- ★ **UBSan 의 기본 집합에 `float-cast-overflow` 가 없다.** 따로 켜야 잡힌다.

```text
--- -fsanitize=undefined 만 ---           (f5 에 대해 아무 말 없음)
--- -fsanitize=float-cast-overflow ---
ex.c:4:1: runtime error: 1e+10 is outside the range of representable values of type 'int'
ex.c:5:1: runtime error: -nan is outside the range of representable values of type 'int'
ex.c:6:1: runtime error: -1 is outside the range of representable values of type 'unsigned int'
```

- ★ **`-Warray-bounds` 는 `-O0` 에서 안 나오고 `-O2` 에서 나온다.** 인라인이 되어야 컴파일러가 배열 크기를 알기 때문이다.\
  **최적화를 켜야 보이는 경고가 있다.**
- 실무 결론 — 이 주제의 실무 결론이 정확히 이 표다.

```text
  빌드 플래그 (권장)
    -Wall -Wextra -Wconversion -Wsign-conversion -Wshadow
    + 별도 빌드로 -O2 한 번 더 (경고가 달라진다)
    + 테스트 빌드에 -fsanitize=undefined,address,float-cast-overflow
    + -fno-sanitize-recover=all  (첫 UB 에서 멈춘다)
```

비용 — sanitizer 빌드는 느리고 메모리를 더 쓴다. **CI 에 별도 잡으로 둔다.**

## 문법 — 형태와 규칙

### 형태 — 승격을 일으키지 않고 타입만 보는 법

```c
/* 단항 + 는 정수 승격만 일으킨다 — 승격 결과를 보는 최소 도구 */
_Generic((+c), int: "int", unsigned int: "unsigned int", ...)

/* sizeof 는 승격을 안 일으킨다 — 원래 타입의 크기 */
sizeof(c)        /* 1 */
sizeof(+c)       /* 4 — 승격된 뒤 */
sizeof(c + c)    /* 4 */
```

### 금지 사례 — 조용히 틀리는 네 형태

```c
/* (1) 부호 있는 값과 sizeof 를 비교 */
for (int i = 0; i < sizeof(a)/sizeof(a[0]); i++) { }      /* 경고는 난다 */

/* (2) 부호 없는 인덱스를 거꾸로 돌린다 */
for (size_t i = n - 1; i >= 0; i--) { }                   /* 절대 안 끝난다 */

/* (3) 길이에서 1을 뺀다 */
if (i < len - 1) { }                    /* len 이 0 이면 SIZE_MAX */

/* (4) 좁은 부호 없는 타입끼리 곱한다 */
unsigned short a = 65535; unsigned x = a * a;   /* int 로 곱해 UB */
```

(2)를 실제로 돌려 봤다.

```text
ex.c:6:51: warning: comparison of unsigned expression in ‘>= 0’ is always true [-Wtype-limits]
    6 |     for (size_t i = sizeof(a)/sizeof(a[0]) - 1; i >= 0; i--) {
      |                                                   ^~
=== -O0 실행 ===
sum = 433762248
(exit 0)
=== ASan ===
==1423171==ERROR: AddressSanitizer: stack-buffer-underflow on address 0x76361520001c at pc 0x5beadc218474 bp 0x7ffd1648bf50 sp 0x7ffd1648bf40
READ of size 4 at 0x76361520001c thread T0
    #0 0x5beadc218473 in main ex.c:7
...
  This frame has 1 object(s):
    [32, 52) 'a' (line 3) <== Memory access at offset 28 underflows this variable
SUMMARY: AddressSanitizer: stack-buffer-underflow ex.c:7 in main
```

- `-Wtype-limits`(`-Wextra` 에 포함)가 **`i >= 0` 은 언제나 참**이라고 말해 준다.
- 그냥 돌리면 **쓰레기 값 `433762248` 을 내고 exit 0** 이다. 배열 앞쪽 메모리를 읽었다.
- **ASan 이 `stack-buffer-underflow` 로 정확히 짚는다** — 어느 변수의 어느 오프셋인지까지.
- 고치는 법: `for (size_t i = n; i-- > 0;)` 또는 인덱스를 `ptrdiff_t` 로.

### 규칙 불릿

- 승격은 **각 피연산자에 따로**, 통상 산술 변환은 **둘을 보고** 일어난다.
- `int` 보다 좁은 정수는 **부호가 있든 없든 `int` 로** 올라간다(이 환경에서).
- 폭이 같고 부호가 다르면 **부호 없는 쪽으로** — 이것 하나가 사고의 절반이다.
- **부호 있는 오버플로 = UB · 부호 없는 오버플로 = 2^N 모듈러.**
- 시프트량이 **음수이거나 타입 폭 이상이면 UB** 다. 부호 있는 값을 왼쪽 시프트해 부호 비트를 넘겨도 UB.
- `-Wsign-compare` 는 **`-Wextra`** 에 있다(`-Wall` 아님).
- `-Wconversion` 은 **모든 피연산자가 목표 타입이면 절단을 경고하지 않는다.**
- UBSan 기본 집합에 **`float-cast-overflow` 는 없다.**

## 어디서 틀리나

### 1. `-Wall` 만 켠다

```text
플래그 없음  : -1 < 1u 경고 0 건
-Wall       : -1 < 1u 경고 0 건      <- ★ 여기서 멈추는 프로젝트가 많다
-Wextra     : -1 < 1u 경고 1 건
```

- 이 주제 최대 사고인 부호 비교가 **`-Wall` 로는 안 보인다.**

### 2. `-O0` 에서 돌려 보고 「랩어라운드한다」고 배운다

- 단순 덧셈은 `-O0`\~`-O3` 이 전부 같아서 **그 결론이 강화된다.**
- 루프 조건에 넣는 순간 `-O2` 가 **무한 루프**가 된다.
- **「값이 안 변했다」가 「UB 가 아니다」의 근거가 못 된다.** sanitizer 가 유일한 판정자다.

### 3. 좁은 부호 없는 타입끼리의 연산을 안전하다고 본다

- `unsigned short * unsigned short` 가 **부호 있는 오버플로 UB** 가 된다.
- 「`unsigned` 니까 모듈러겠지」가 틀린 것이다 — **승격이 먼저 일어나기 때문**이다.
- 고치는 법: `(unsigned)us * us` 또는 `(uint32_t)us * us`.

### 4. `-Wconversion` 을 켜고 절단이 다 보인다고 믿는다

- `unsigned char r = c * c;` 가 **안 잡힌다.** gcc 의 승격 되돌림 예외 때문이다.
- 이 예외가 실제로 값을 자른다 — `200*200 = 40000` 이 `64` 가 된다.
- 막는 법은 경고가 아니라 **코드 쪽**이다: `uint8_t r = (uint8_t)(c * c);` 로 **의도를 적는다.**

## 구현 세부사항 대 언어 보장

C 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 네 층을 갈라야 한다.\
**이 주제는 네 층이 전부 나오는 유일한 묶음**이고, 그래서 이 절이 본체다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| **표준이 정한 것** | 어느 구현에서도 같다 | 승격 대상과 방향 · 통상 산술 변환의 결정 순서 · **부호 없는 연산은 2^N 모듈러** · `-1 < 1u` 가 거짓인 것 · 부호 있는 값의 오른쪽 시프트가 **구현 정의**이고 왼쪽 시프트 중 일부가 **UB** 인 것 | `_Generic` 타입표 · 값 출력 · `-O0/-O2/ubsan` 삼중 |
| **구현 정의** | 구현마다 다르되 **문서화 의무가 있다** | `int` 의 폭(→ 무엇이 `int` 로 승격되는지가 여기 달렸다) · `unsigned short` 가 `int` 로 갈지 `unsigned int` 로 갈지 · **부호 있는 값의 `>>`** (gcc 는 산술 시프트) · 범위를 넘는 값을 부호 있는 타입에 **대입**했을 때의 결과 | `sizeof` · `-1 >> 1 = -1`·`-8 >> 1 = -4` 실행 |
| **미명시** | 몇 가지 중 하나, 문서화 의무 없음 | 한 식 안의 부분식 평가 순서(이 주제에서 직접 다루지는 않는다 — [`01`](../01-declaration-syntax-and-reading/) 의 인자 평가 순서가 그 예) | gcc `3 2 1` ↔ clang `1 2 3` |
| **UB** | 아무 일이나 일어날 수 있다 | **부호 있는 정수 오버플로** · 시프트량이 음수이거나 폭 이상 · 부호 있는 왼쪽 시프트가 표현 범위를 넘음 · 범위를 넘는 **부동→정수 변환** · 0 으로 나누기 | `-O0` ↔ `-O2` 가 **다른 값**·**무한 루프** · UBSan 이 문장으로 잡음 |

### UB 를 「이론」이 아니라 출력으로

sanitizer 가 잡은 것을 전수로 옮긴다. 전부 이 문서의 프로그램에서 나온 실제 줄이다.

```text
ex.c:4:31: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
ex.c:6:39: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
ex.c:13:5: runtime error: signed integer overflow: 65535 * 65535 cannot be represented in type 'int'
ex.c:2:37: runtime error: left shift of 1 by 31 places cannot be represented in type 'int'
ex.c:3:37: runtime error: shift exponent 32 is too large for 32-bit type 'int'
ex.c:4:37: runtime error: shift exponent -1 is negative
ex.c:4:1:  runtime error: 1e+10 is outside the range of representable values of type 'int'
ex.c:5:1:  runtime error: -nan is outside the range of representable values of type 'int'
ex.c:6:1:  runtime error: -1 is outside the range of representable values of type 'unsigned int'
AddressSanitizer: stack-buffer-underflow ... [32, 52) 'a' (line 3) <== Memory access at offset 28 underflows this variable
AddressSanitizer: stack-buffer-overflow ex.c:8 in f6
```

- 각 줄이 **어떤 값으로 어떤 타입에서** 넘쳤는지까지 말해 준다. 「UB 가 났다」보다 훨씬 강한 근거다.
- 주의 — **UBSan 은 같은 소스 위치를 한 번만 보고한다.**\
  한 함수에 세 번 넘겼더니 첫 건만 나왔고, 세 함수로 나누니 셋 다 나왔다.\
  **「한 건만 나왔다」가 「한 건뿐이다」가 아니다.**

### 구현 정의를 실측으로 — 부호 있는 오른쪽 시프트

```text
-1 >> 1  = -1
-8 >> 1  = -4
```

- gcc 는 **산술 시프트**(부호 비트를 채운다)를 한다. `-8 >> 1 == -4` 는 2로 나눈 것과 같다.
- 표준은 이것을 **구현 정의**로 둔다 — 논리 시프트를 하는 구현도 적법하다.
- 그래서 **부호 있는 값을 `>>` 로 나누는 코드는 이식성이 없다.** 나누기를 쓰거나 `unsigned` 로 옮긴다.

### 「안 터졌다」는 「안전하다」가 아니다 — 이 절의 결론

```text
  --- 아무 플래그 없이 -O0 ---     -2147483648  256  64  0  -2147483648   0        (exit 0)
  --- 아무 플래그 없이 -O2 ---     -2147483648    0  64  0   2147483647  -2090046208  (exit 0)
```

- **둘 다 정상 종료했다.** 에러도 경고도 없다.
- 그런데 **여섯 값 중 세 값이 다르다.**
- 이 프로그램이 테스트를 통과했다면 그 테스트는 **`-O0` 빌드의 우연**을 고정한 것이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 이렇게 한다 | 안 하는 것 |
|---|---|---|
| 인덱스와 길이를 비교 | 양쪽을 **같은 부호**로 맞춘다 (`size_t` 끼리, 또는 `(ptrdiff_t)`) | `int i < sizeof(...)` |
| 역방향 루프 | `for (size_t i = n; i-- > 0;)` | `for (size_t i = n-1; i >= 0; i--)` |
| 길이에서 빼기 | `if (i + 1 < len)` | `if (i < len - 1)` |
| 좁은 부호 없는 타입 곱하기 | `(uint32_t)a * b` | `a * b` 그대로 |
| 오버플로 검사 | **일으키기 전에** 검사 (`a > INT_MAX - b`) | 일으킨 뒤 결과를 보는 것 (UB 라 검사 자체가 지워진다) |
| 비트 조작 | `unsigned` 타입으로 | 부호 있는 타입 시프트 |
| 2로 나누기 | `/ 2` | `>> 1` (부호 있으면 구현 정의) |

판단 규칙 두 줄.

- **한 식 안에 부호 있는 것과 없는 것을 섞지 않는다.** 섞어야 하면 **넓은 부호 있는 타입으로 올린다.**
- **오버플로는 일으킨 뒤에 못 잡는다.** UB 라서 「일어난 뒤의 값」이라는 게 없다.

## 핵심 문장

- 계체는 **2단계**다 — 각 피연산자를 `int` 로 올리고(승격), 그 다음 둘을 한 타입으로 맞춘다(통상 산술 변환).
- 폭이 같고 부호가 다르면 **부호 없는 쪽으로 간다** — `-1 < 1u` 가 거짓인 이유이고 이 주제 사고의 절반이다.
- **`unsigned char c=200; c*c` 는 `40000`** 이다. 승격이 `int` 로 올려서 절단이 안 일어난다.\
  그런데 **`unsigned short` 끼리 곱하면 `int` 를 넘쳐 UB** 가 된다 — 같은 승격이 반대 방향으로 문다.
- **부호 있는 오버플로는 UB, 부호 없는 오버플로는 2^N 모듈러**다. `-O0` 에서 `3` 이던 루프가 `-O2` 에서 **무한 루프**가 됐다.
- **「`-O0` 에서 값이 같았다」는 UB 가 아니라는 근거가 못 된다.** 판정자는 sanitizer 뿐이다.
- `-Wsign-compare` 는 **`-Wextra`** 에 있고, `-Wconversion` 은 **승격을 되돌리는 절단을 안 잡고**, UBSan 기본 집합에 **`float-cast-overflow` 가 없다.**

## 관련 자료

- [`../README.md`](../README.md) — C 문법·API 주제 목록(이 주제는 03번)
- [`../../../c-cpp-csharp.md`](../../../c-cpp-csharp.md) — **그쪽은 「이 실패 계급이 왜 은행 원장에서 최악인가」라는 논증까지, 여기는 「어떤 코드가 그것을 만들고 어떻게 잡나」부터**
- [`../../../../data-representation/`](../../../../data-representation/) — **그쪽은 2의 보수 비트 표현까지, 여기는 그 위에서 C 가 언제 어느 타입으로 바꾸나부터.** `-1` 의 비트가 왜 전부 1인가는 거기
- [`02-basic-types-sizes-and-fixed-width-integers/`](../02-basic-types-sizes-and-fixed-width-integers/) — `sizeof` 가 `size_t` 인 것 · 16진 리터럴이 `unsigned` 인 것 — **이 주제 사고의 씨앗이 거기서 뿌려진다**
- [`04-floating-point-types-and-conversions/`](../04-floating-point-types-and-conversions/) — 통상 산술 변환의 ① 단계(부동소수 쪽) · 범위 밖 부동→정수 UB
- [목록의 **05번 주제**](../05-explicit-casts-and-pointer-conversions/) (명시 캐스트) — 「경고를 끄기만 하는 캐스트」를 가리는 곳
- [목록의 **11번 주제**](../11-bitwise-operations-and-shifts/) (비트 연산과 시프트) — 시프트의 정본
- [목록의 **36번 주제**](../36-variadic-functions-stdarg/) (`<stdarg.h>`) — 기본 인자 승격은 이 주제의 사촌이다
- 목록의 **54번 주제** (부호 있는 정수 오버플로) — **오버플로를 일으키기 전에 검사하는 식**의 정본
- 목록의 **58번 주제** (UB 를 잡는 도구) — 이 문서의 경고·sanitizer 표가 정본으로 다뤄지는 곳

## 용어 풀이

- **정수 승격(integer promotion)** — `int` 보다 좁은 정수 타입을 연산 전에 `int`(못 담으면 `unsigned int`)로 올리는 것.
- **통상 산술 변환(usual arithmetic conversions)** — 승격이 끝난 두 피연산자를 한 타입으로 맞추는 규칙.
- **rank(정수 변환 등급)** — 정수 타입의 서열. 부호 있는 것과 없는 것은 **같은 등급**이다.
- **UB(미정의 동작)** — 표준이 정의하지 않은 것. 아무 일이나 일어나도 되고 **최적화기가 「안 일어난다」고 가정한다.**
- **구현 정의 동작** — 구현마다 다르되 문서화 의무가 있는 것. 부호 있는 `>>` 가 그 예.
- **모듈러 산술(modular arithmetic)** — 결과를 2^N 으로 나눈 나머지로 하는 것. 부호 없는 정수 연산의 정의.
- **랩어라운드(wraparound)** — 최댓값을 넘으면 최솟값으로 도는 것. **부호 없는 쪽에서만 보장된다.**
- **`-fwrapv`** — 부호 있는 오버플로를 2의 보수 랩어라운드로 **정의하라**고 컴파일러에 시키는 플래그. UB 가 아니게 된다.
- **UBSan(`-fsanitize=undefined`)** — UB 를 런타임에 잡는 도구. 검사 코드를 끼워 넣는다.
- **ASan(`-fsanitize=address`)** — 메모리 접근 위반을 잡는 도구. 배열 밖·해제 후 사용을 잡는다.
- **상수 접기(constant folding)** — 컴파일 시간에 값을 계산해 버리는 최적화. `1 << 32` 가 `-O2` 에서 `0` 이 된 원인.
- **산술 시프트 / 논리 시프트** — 오른쪽 시프트 때 부호 비트를 채우느냐(산술) 0을 채우느냐(논리). 부호 있는 값에 대해서는 구현 정의.

---

## 더 들어가면

- **C23 에서 부호 표현이 2의 보수로 못박혔다.** 그래도 **부호 있는 오버플로는 여전히 UB** 다.\
  「표현이 정해졌으니 오버플로도 정의되겠지」가 틀린 것이다. 표현과 연산 정의는 별개다.
- **`-ftrapv`** 라는 플래그도 있다 — 부호 있는 오버플로에서 트랩을 건다.\
  `-fwrapv` 와 정반대 방향(랩 vs 중단)이고, 이 문서에서는 **안 돌려 봤다.**
- gcc 에는 오버플로를 **정의된 방식으로 검사하는 내장 함수**가 있다 — `__builtin_add_overflow` 계열.\
  GNU 확장이라 이식성이 없고, 이식 가능한 방법은 **미리 검사하는 것**이다(목록의 **54번 주제**).
- **`-Waggressive-loop-optimizations`** 는 gcc 가 「UB 를 근거로 루프를 바꿨다」고 알려 주는 드문 경고다.\
  `-O1` 부터 켜져 있고 기본 활성이다. **컴파일러가 UB 를 안다고 말하면서 최적화한다**는 걸 보여 주는 자리다.
- UBSan 의 기본 집합은 컴파일러마다 다르다. gcc 13 에서는 `float-cast-overflow` 와 `float-divide-by-zero` 가 빠져 있다 —\
  **`-fsanitize=undefined,float-cast-overflow` 로 명시**하는 편이 안전하다.
- 부동소수 나누기 0 은 UBSan 이 `division by zero` 로 잡지만, **`__STDC_IEC_559__` 가 정의된 환경에서는 `inf` 로 정의된 동작**이다.\
  둘이 어긋나는 자리이고, [`04-floating-point-types-and-conversions/`](../04-floating-point-types-and-conversions/) 에서 다시 본다.
