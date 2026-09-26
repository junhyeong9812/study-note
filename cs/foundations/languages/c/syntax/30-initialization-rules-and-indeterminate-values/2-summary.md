# c/syntax/30 — 초기화 규칙과 불확정 값: 「**0 은 누가 보장하고, 안 보장된 자리에서는 무엇이 읽히나**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) — 「불확정 표현」·「비값 표현」의 정의, 주소를 안 잡은 자동 객체를 읽는 규칙, 패딩 바이트 규칙을 **본문에서 직접 찾아 읽었다**) · [cppreference — Initialization (C)](https://en.cppreference.com/w/c/language/initialization)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **섹션 크기·바이트·진단·종료 코드는 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★★ **최적화 수준이 결과를 바꾸는 자리는 전부 판 격자**로 돌렸다(컴파일러 2 × `-O0`/`-O2`, 탐침은 도구 6).\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> **버전** — 정적 객체의 0 초기화 · 부분 초기화의 나머지 0 은 **C89 부터**, 지정 초기자는 **C99 부터**, **빈 중괄호 `= {}` 는 C23 부터**다((3)).\
> ★ C23 은 「트랩 표현」이라는 낱말을 「**비값 표현(non-value representation)**」으로 바꿨다. 이 문서는 새 이름을 쓰고 옛 이름을 괄호에 둔다.
> ★★ **경계** — **저장 기간 자체**와 「정적은 0 · 자동은 불확정」의 **첫 관찰**은 [28번 형제](../28-choosing-among-four-storage-durations/)가 정본이다. 여기는 **그 이유와 경계선**을 판다.\
> ★ **지정 초기자 문법**은 [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/), **패딩이 어디 생기나**는 [22번 형제](../22-struct-padding-and-alignment/)가 정본이다.\
> ★ **`malloc`/`calloc` 의 API 계약**은 목록의 **37번 주제**, **`memcmp` 의 계약**은 목록의 **50번 주제**, **sanitizer 사용법**은 목록의 **58번 주제**다.
> 선행 — [28번 형제](../28-choosing-among-four-storage-durations/).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 둘째 창과 넷째 창이다.** ① **`readelf -S`·`size`** 가 「**0 은 파일에 싣지 않는다**」를 섹션 크기로 증명하고,
② **`-O0` 대 `-O2` 판 격자**(경고·어셈블리)가 「**불확정 값을 잡는 도구가 최적화 수준을 탄다**」를 증명한다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | `-Wuninitialized`·`-Wmaybe-uninitialized`·`-Wsometimes-uninitialized`·`-fanalyzer` — **탐침 8개에** | 씀 |
| ② 실행 출력 | 부분 초기화의 0 · 패딩 바이트 덤프 · `malloc` 재사용 · `bool` 의 이상한 참거짓 | 씀 |
| ③ sanitizer | ★ **MSan**(clang) — 탐침 8개 전부 · ★ **UBSan** — `bool` 의 비값 표현 | 씀 |
| ★★★ ④ **`readelf -S`·`size`·`nm -S`** | ★ **본체 ①** — `.bss` 가 **`NOBITS`** 이고 오브젝트 크기가 **안 는다** | 씀 |
| ★★★ ⑤ **`-O0` 대 `-O2`** | ★ **본체 ②** — 경고가 **판에 따라 생기고 사라진다** · P2 가 `-O2` 에서 **접혀 사라진 것**을 어셈블리로 | 씀 |
| Valgrind | ★ **이 머신에 없다** — `which` 가 `exit=1`((4)) | ★ **못 잰 것** |
| ★ 제5의 상태 | 「이 값이 불확정인가」를 **값으로 물을 수 없어서**(무엇이 나와도 증거가 안 된다) **MSan 의 그림자 비트로** 물었다 | 창을 바꿔 답함 |

★ **바꾼 창(MSan)이 못 보는 것** — MSan 은 「**초기화 안 된 바이트가 분기·반환에 쓰였나**」를 본다. **패딩을 `memcmp` 로 읽는 것**처럼 초기화 안 된 바이트가 **분기에 안 쓰이면** 조용하다(이 문서는 그 자리를 던지지 않았다).

## 이 판

```text
===== gcc --version | sed -n 1p (cc exit=0) =====
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

```text
===== clang --version | sed -n 1p (cc exit=0) =====
Ubuntu clang version 18.1.3 (1ubuntu1)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | MSan 리포트의 **PID**(`==N==`) · **프레임 주소**(`#0 0x…`) | 실행마다 다르다 — `normalize-shaky.py` 의 기본 규칙 둘이 지운다 |
| 안 흔들린다 | ★★★ **섹션 크기**(`.bss 061aa0`) · `size` 표 · 오브젝트 파일 바이트 수 | 같은 컴파일러 · 같은 소스면 같다 |
| 안 흔들린다 | ★★★ **탐침 격자의 칸**(경고 N · 침묵 · 보고) · **답한 칸 30 / 48** | 컴파일러 진단은 결정적이다 |
| 안 흔들린다 | ★★ **패딩 덤프** · `malloc` 재사용 · `bool` 격자 | ★ **스택을 먼저 `0xAA` 로 더럽혀** 「무엇이 남아 있나」를 내가 정했다 — 그래서 재실행에 같다 |
| 안 흔들린다 | MSan 리포트의 **`파일:줄:칸`** · `SUMMARY` 줄 · UBSan 의 `runtime error` 줄 | `-ffile-prefix-map` 으로 경로를 죽였다 |
| 해당 없음 | [28번 형제](../28-choosing-among-four-storage-durations/)의 「쓰레기 숫자」 | ★ 이 편은 **불확정 값을 숫자로 찍지 않는다** — 찍으면 흔들리고, 흔들려도 **아무것도 증명하지 않는다** |

★ **정규화 규칙은 기본 둘(주소 · PID)만 썼다.** 갈래 고유 규칙은 **0개**다.

## 한눈에 — 쉽게 말하면

**새 집에 입주하는 것과 같다.**

- **분양받은 새 아파트** — 빈 방이 **깨끗이 비어 있다고 계약서에 적혀 있다.** 확인하지 않아도 된다. → **정적 저장 기간 = 0 보장**
- **방금 누가 나간 원룸** — 전 세입자의 물건이 **남아 있을 수도, 없을 수도** 있다. 계약서에 아무 말이 없다. → **자동 저장 기간 = 불확정**
- **이사 업체에 「이 상자만 옮겨 주세요」라고 하면** — 적은 상자는 옮기고, **나머지 칸은 비워 준다.** → **부분 초기화 = 나머지 0**
- **가구 사이의 틈** — 업체가 **틈까지 닦아 준다는 약속은 없다.** → **패딩 바이트 = 미명시**
- **「스위치가 켜짐도 꺼짐도 아닌 중간」에 걸린 전등** — 켜졌냐고 물으면 **대답이 사람마다 다르다.** → **`bool` 에 2 = 비값 표현 — UB**

| 비유 | 실체 | 누가 무엇을 보장하나 |
|---|---|---|
| 새 아파트 | `static int s;` · 전역 · 문자열 리터럴 | ★★★ **표준 — 0**(패딩 비트까지) |
| 새 아파트의 **계약서만 있고 방은 아직 없음** | `.bss` — 크기만 적고 **파일에 0 을 싣지 않는다** | ★ **구현** — `NOBITS` |
| 방금 나간 원룸 | 함수 안 `int a;` · `malloc` | ★★ **불확정** |
| 「이 상자만」 | `int a[8] = {1};` · `{.retries = 3}` | ★★★ **표준 — 나머지 0** |
| 가구 사이 틈 | 구조체 패딩 바이트 | ★ **미명시** |
| 중간에 걸린 스위치 | `_Bool` 바이트가 `2` | ★★ **UB** — gcc 는 「참이면서 거짓」, clang 은 「거짓」 |

```text
   초기자가 없을 때 — 저장 기간이 답을 정한다

   정적·스레드 저장 기간         자동 저장 기간              할당 (malloc)
   -----------------------     -----------------------   -----------------------
   0 · 널 포인터 · +0.0         ★ 불확정 표현               ★ 불확정 표현
   패딩 비트까지 0               (무엇이 있든 증거가 안 됨)    (calloc 이면 모든 바이트 0)
   ★ 표준                       ★ 읽으면 — 층이 갈린다(7)   ★ 읽으면 — 층이 갈린다(7)

   초기자가 「일부만」 있을 때 — 저장 기간과 무관하게
   -----------------------------------------------------------------
   int a[8] = {1};   -> 1 0 0 0 0 0 0 0      ★ 나머지는 「정적처럼」 0
```

- ★★★ **이 주제는 「표준」과 「UB」가 같은 두께**다 — 0 초기화 규칙은 표준이고, 불확정 값을 **읽는 것**은 자리에 따라 UB 다.
- ★★★ 그리고 **「미명시」가 가장 정밀하게 갈라야 하는 칸**이다 — 불확정 **표현**은 「미명시 값」이거나 「비값 표현」이다. **어느 쪽이냐가 층을 가른다**((7)).
- ★ **구현 정의 칸** — `.bss` 라는 배치 · 어느 타입에 비값 표현이 있나(`_Bool` 은 `0`·`1` 밖이 전부 비값).

> **불확정 표현(indeterminate representation)** — **미명시 값이거나 비값 표현**인 객체 표현. 초기화 안 한 자동 객체가 이렇다.\
> 예: 함수 안 `int a;` 의 네 바이트.

> **비값 표현(non-value representation, 옛 이름 트랩 표현)** — 그 타입의 **어떤 값도 나타내지 않는** 비트 패턴. 문자 타입이 아닌 것으로 읽으면 **UB** 다.\
> 예: 이 구현의 `_Bool` 에서 바이트 `2`.

> **`.bss`** — 0 으로 시작하는 정적 객체를 모아 두는 섹션. **파일에는 크기만 적고 내용은 싣지 않는다**(`NOBITS`).\
> 예: `static int big[100000];` 은 400000 바이트인데 오브젝트 파일이 안 커진다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **어떤 객체가 0 이고 어떤 것이 불확정인가** — 그리고 「0 이다」를 **무엇으로 증명하나.**
2. ★★★ **불확정 값을 읽는 코드를 누가 찾아 주나** — 도구 여섯 개 중 누가 어느 자리에서 침묵하나.
3. ★★ **불확정 값을 읽는 것이 언제 UB 인가** — 「불확정」·「미명시」·「비값 표현」을 가르면.

## 동작 방식

### (1) ★★★ 「0 으로 초기화된다」를 `.bss` 로 증명한다

**언제 쓰나** — 큰 정적 배열이 **바이너리 크기**를 키우는지 물을 때. 「0 은 공짜인가」를 답할 때.

```c
/* s30a.c */
static int zero_implicit;             /* 초기자 없음 */
static int zero_explicit = 0;         /* 0 을 직접 적음 */
static int nonzero = 5;               /* 0 이 아닌 값 */
static int big_zero[100000];          /* 400000 바이트 — 전부 0 */
static const int ro = 7;              /* const — 값 있음 */

int use(int k) {
    return zero_implicit + zero_explicit + nonzero + big_zero[k] + ro;
}
```

```c
/* s30b.c */
static int zero_implicit;
static int zero_explicit = 0;
static int nonzero = 5;
static int big_one[100000] = {1};     /* ★ 첫 원소만 1 — 나머지 99999 개는 0 */
static const int ro = 7;

int use(int k) {
    return zero_implicit + zero_explicit + nonzero + big_one[k] + ro;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s30a.c -o s30a.o && gcc -std=c17 -Wall -Wextra -pedantic -c s30b.c -o s30b.o && readelf -S -W s30a.o s30b.o | grep -E '^File|\.(data|bss|rodata) ' (cc exit=0) =====
File: s30a.o
  [ 3] .data             PROGBITS        0000000000000000 000084 000004 00  WA  0   0  4
  [ 4] .bss              NOBITS          0000000000000000 0000a0 061aa0 00  WA  0   0 32
  [ 5] .rodata           PROGBITS        0000000000000000 0000a0 000004 00   A  0   0  4
File: s30b.o
  [ 3] .data             PROGBITS        0000000000000000 0000a0 061aa0 00  WA  0   0 32
  [ 4] .bss              NOBITS          0000000000000000 061b40 000008 00  WA  0   0  4
  [ 5] .rodata           PROGBITS        0000000000000000 061b40 000004 00   A  0   0  4
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s30a.c -o s30a.o && gcc -std=c17 -Wall -Wextra -pedantic -c s30b.c -o s30b.o && size s30a.o s30b.o && stat -c '%s 바이트  %n' s30a.o s30b.o (cc exit=0) =====
   text	   data	    bss	    dec	    hex	filename
    160	      4	 400032	 400196	  61b44	s30a.o
    160	 400032	      8	 400200	  61b48	s30b.o
1768 바이트  s30a.o
401792 바이트  s30b.o
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s30a.c -o s30a.o && clang -std=c17 -Wall -Wextra -pedantic -c s30b.c -o s30b.o && size s30a.o s30b.o && stat -c '%s 바이트  %n' s30a.o s30b.o (cc exit=0) =====
   text	   data	    bss	    dec	    hex	filename
    100	      4	 400016	 400120	  61af8	s30a.o
    100	 400016	      8	 400124	  61afc	s30b.o
1504 바이트  s30a.o
401504 바이트  s30b.o
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s30a.c -o s30a.o && nm -S s30a.o (cc exit=0) =====
0000000000000020 0000000000061a80 b big_zero
0000000000000000 0000000000000004 d nonzero
0000000000000000 0000000000000004 r ro
0000000000000000 0000000000000044 T use
0000000000000004 0000000000000004 b zero_explicit
0000000000000000 0000000000000004 b zero_implicit
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s30a.c -o s30a.o && nm -S s30a.o (cc exit=0) =====
0000000000000010 0000000000061a80 b big_zero
0000000000000000 0000000000000004 d nonzero
0000000000000000 000000000000002c T use
0000000000000004 0000000000000004 b zero_explicit
0000000000000000 0000000000000004 b zero_implicit
```

```text
   s30a.c  big_zero[100000]            s30b.c  big_one[100000] = {1}
   ---------------------------------   ---------------------------------
   .bss   NOBITS  061aa0 (400032)      .bss   NOBITS  000008
   .data  PROGBITS 000004              .data  PROGBITS 061aa0 (400032)
   오브젝트 파일  1768 바이트            오브젝트 파일  401792 바이트
                                                     ★ 400000 바이트가 늘었다

   ★ 같은 크기의 배열. 한 원소를 1 로 바꿨을 뿐인데 ★ 0 까지 전부 파일에 실린다
```

그림 해설 (한 단계씩):

- ★★★ **`.bss` 의 타입이 `NOBITS`** 다 — 「**파일에 비트가 없다**」는 뜻이다. 크기(`061aa0`)만 적고 내용은 싣지 않는다. 로더가 **실행할 때 0 으로 채운 페이지**를 준다.
- ★★★ **원소 하나를 `1` 로 바꾸면 배열 전체가 `.data`(`PROGBITS`)로 간다** — 오브젝트 파일이 **1768 → 401792 바이트**. 나머지 99999 개의 0 까지 **파일에 실린다.**
- ★★ **`zero_explicit = 0` 도 `b`**(`.bss`)다 — 「0 을 적었다」와 「안 적었다」가 **같은 자리**에 간다.
- ★★ **두 컴파일러가 갈린 자리** — gcc 는 `static const int ro = 7` 을 **`.rodata` 에 `r ro`** 로 남겼고, **clang 은 심볼째 없앴다**(`.rodata` 도 없다). 값을 **즉치값으로 접어** 넣었기 때문이다 — `-O0` 인데도.
- ★ **`.bss`·`NOBITS` 는 표준의 말이 아니다.** 표준이 보장하는 것은 「**0 으로 시작한다**」이고, 그것을 **어떻게** 지키느냐가 이 구현의 `.bss` 다.

비용 — **0 이 아닌 값 하나가 배열 전체의 비용을 바꾼다.** 큰 테이블의 기본값이 0 이 아니면 **실행 중에 채우는 쪽**이 파일을 안 키운다.

### (2) ★★★ 부분 초기화 — 적지 않은 칸은 **저장 기간과 무관하게** 0

**언제 쓰나** — `int a[8] = {1};` 이 「첫 칸만 1, 나머지는 쓰레기」인지 물을 때.

```c
/* s30c.c */
#include <stdio.h>

struct Cfg { int port; int retries; const char *name; double ratio; };

static void dirty(void) {                /* 스택을 먼저 더럽혀 둔다 — 「원래 0 이었다」를 막으려고 */
    volatile int junk[64];
    for (int k = 0; k < 64; k++) junk[k] = -1;
}

static void show(void) {
    int a[8] = {1};                      /* 첫 칸만 적었다 */
    int b[8] = {[5] = 9};                /* 지정 초기자 — 여섯째 칸만 적었다 */
    struct Cfg c = {.retries = 3};       /* 멤버 하나만 적었다 */

    printf("a =");
    for (int k = 0; k < 8; k++) printf(" %d", a[k]);
    printf("\nb =");
    for (int k = 0; k < 8; k++) printf(" %d", b[k]);
    printf("\nc = { port=%d  retries=%d  name=%s  ratio=%.1f }\n",
           c.port, c.retries, c.name == NULL ? "NULL" : "(NULL 아님)", c.ratio);
}

int main(void) {
    dirty();
    show();                              /* ★ 전부 자동 저장 기간이다 */
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s30c.c -o x ; ./x (cc exit=0 · run exit=0) =====
a = 1 0 0 0 0 0 0 0
b = 0 0 0 0 0 9 0 0
c = { port=0  retries=3  name=NULL  ratio=0.0 }
```

```text
===== 부분 초기화 — 컴파일러 2 × 최적화 2 (exit=0) =====
gcc    -O0  출력 md5 앞 8자리 = c0b5b02c
gcc    -O2  출력 md5 앞 8자리 = c0b5b02c
clang  -O0  출력 md5 앞 8자리 = c0b5b02c
clang  -O2  출력 md5 앞 8자리 = c0b5b02c
네 벌의 출력이 한 글자도 같은가 = 예
```

- ★★★ **전부 자동 저장 기간인데 나머지가 0** 이다. 초기자가 **하나라도** 있으면 적지 않은 칸은 **「정적 저장 기간처럼」 0** 이 된다 — 표준 규칙이다.
- ★★★ **네 벌의 출력이 한 글자도 같다**(md5 동일). 스택을 먼저 `-1` 로 더럽혔는데도 0 이다 — **컴파일러가 0 을 써 넣었다.**
- ★★ **포인터 멤버는 널 포인터, `double` 은 `0.0`** 이다 — 「0 비트」가 아니라 **「그 타입의 0」** 이다.
- ★ **지정 초기자의 규칙도 같다** — `{[5] = 9}` 는 여섯째 칸만 적고 나머지는 0([21번 형제](../21-struct-declaration-initialization-and-designated-initializers/)가 정본).

비용 — **「하나라도 적으면 나머지는 0」과 「아무것도 안 적으면 불확정」** 사이가 한 글자다. `int a[8];` 와 `int a[8] = {0};` 은 **전혀 다른 물건**이다.

### (3) ★ `= {}` — C23 문법을 `-std=c17` 에서 쓰면

**언제 쓰나** — 「`= {0}` 대신 `= {}` 를 써도 되나」를 물을 때.

```c
/* s30d.c */
#include <stdio.h>

int main(void) {
    int a[4] = {};                       /* ★ 빈 중괄호 — C23 에서 들어온 문법 */
    struct { int x; double y; } s = {};
    printf("a = %d %d %d %d · s = { %d, %.1f }\n", a[0], a[1], a[2], a[3], s.x, s.y);
    return 0;
}
```

```text
===== 빈 중괄호 = {} — 컴파일러 2 × 판 4 (exit=0) =====
gcc    -std=c17                    cc exit=0 · 경고 0 · 에러 0
gcc    -std=c17 -pedantic          cc exit=0 · 경고 2 · 에러 0
gcc    -std=c17 -pedantic-errors   cc exit=1 · 경고 0 · 에러 2
gcc    -std=c2x -pedantic-errors   cc exit=0 · 경고 0 · 에러 0
clang  -std=c17                    cc exit=0 · 경고 0 · 에러 0
clang  -std=c17 -pedantic          cc exit=0 · 경고 2 · 에러 0
clang  -std=c17 -pedantic-errors   cc exit=1 · 경고 0 · 에러 2
clang  -std=c2x -pedantic-errors   cc exit=0 · 경고 0 · 에러 0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s30d.c -o x (cc exit=0) =====
s30d.c: In function ‘main’:
s30d.c:4:16: warning: ISO C forbids empty initializer braces before C2X [-Wpedantic]
    4 |     int a[4] = {};                       /* ★ 빈 중괄호 — C23 에서 들어온 문법 */
      |                ^
s30d.c:5:37: warning: ISO C forbids empty initializer braces before C2X [-Wpedantic]
    5 |     struct { int x; double y; } s = {};
      |                                     ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s30d.c -o x (cc exit=0) =====
s30d.c:4:16: warning: use of an empty initializer is a C23 extension [-Wc23-extensions]
    4 |     int a[4] = {};                       /* ★ 빈 중괄호 — C23 에서 들어온 문법 */
      |                ^
s30d.c:5:37: warning: use of an empty initializer is a C23 extension [-Wc23-extensions]
    5 |     struct { int x; double y; } s = {};
      |                                     ^
2 warnings generated.
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic s30d.c -o x ; ./x (cc exit=0 · run exit=0) =====
a = 0 0 0 0 · s = { 0, 0.0 }
```

- ★★★ **`-std=c17` 만 주면 경고 0 · `cc exit=0`** 이다 — C17 문법에 없는데 **조용히 받는다.** ★★ **「종료 코드 0인데 ill-formed」** 새 항목이다.
- ★★ **`-pedantic` 을 붙여야 경고 2건**이 나오고, **`-pedantic-errors` 라야 `cc exit=1`** 이다. `-std=` 는 **강제가 아니라 기본값 선택**이다.
- ★★ **문구가 갈린다** — gcc 는 `ISO C forbids empty initializer braces before C2X [-Wpedantic]`, clang 은 `use of an empty initializer is a C23 extension [-Wc23-extensions]`.
- ★ **`-std=c2x` 에서는 두 컴파일러 다 에러 0** · 결과는 `0 0 0 0 · { 0, 0.0 }` 이다.

비용 — **C17 코드베이스에 `= {}` 가 섞여도 빌드는 초록불**이다. 판을 지키려면 **`-pedantic-errors`** 가 필요하다.

### (4) ★★★ 불확정 값을 읽는 탐침 8개 — **누가 답하고 누가 침묵하나**

**언제 쓰나** — 「경고가 없으니 초기화는 다 됐겠지」라고 생각할 때. ★★★ **이 편의 본체**다.

탐침 여덟 개는 **같은 `main`** 을 쓰고 `probe` 만 다르다. `main` 은 **`probe` 의 결과로 분기**한다 — MSan 이 거기서 본다.

```c
/* s30p1.c */
#include <stdio.h>
#include <stdlib.h>

static int probe(int c) {
    (void)c;
    int a;                               /* P1 — 한 번도 안 쓰고 읽는다 */
    return a;
}

int main(int argc, char **argv) {
    (void)argv;
    int v = probe(argc);                 /* argc = 1 로 돌린다 */
    if (v == 12345) puts("12345");       /* ★ 그 값으로 분기한다 — MSan 은 여기서 본다 */
    else puts("12345 가 아니다");
    return 0;
}
```

```c
/* s30p2.c */
#include <stdio.h>
#include <stdlib.h>

static int probe(int c) {
    int a;
    if (c > 5) a = 1;                    /* P2 — 한쪽 가지에서만 쓴다 */
    return a;
}

int main(int argc, char **argv) {
    (void)argv;
    int v = probe(argc);                 /* argc = 1 로 돌린다 */
    if (v == 12345) puts("12345");       /* ★ 그 값으로 분기한다 — MSan 은 여기서 본다 */
    else puts("12345 가 아니다");
    return 0;
}
```

```c
/* s30p3.c */
#include <stdio.h>
#include <stdlib.h>

static int probe(int c) {
    int sum;                             /* P3 — 누산기를 0 으로 안 둔다 */
    for (int i = 0; i < c; i++) sum += i;
    return sum;
}

int main(int argc, char **argv) {
    (void)argv;
    int v = probe(argc);                 /* argc = 1 로 돌린다 */
    if (v == 12345) puts("12345");       /* ★ 그 값으로 분기한다 — MSan 은 여기서 본다 */
    else puts("12345 가 아니다");
    return 0;
}
```

```c
/* s30p4.c */
#include <stdio.h>
#include <stdlib.h>

static void fill(int *p, int c) { if (c > 5) *p = 1; }

static int probe(int c) {
    int a;
    fill(&a, c);                         /* P4 — 주소를 넘긴 함수가 한쪽에서만 쓴다 */
    return a;
}

int main(int argc, char **argv) {
    (void)argv;
    int v = probe(argc);                 /* argc = 1 로 돌린다 */
    if (v == 12345) puts("12345");       /* ★ 그 값으로 분기한다 — MSan 은 여기서 본다 */
    else puts("12345 가 아니다");
    return 0;
}
```

```c
/* s30p5.c */
#include <stdio.h>
#include <stdlib.h>

static int probe(int c) {
    int arr[4];
    arr[0] = c;                          /* P5 — 배열의 한 칸만 쓴다 */
    return arr[2];
}

int main(int argc, char **argv) {
    (void)argv;
    int v = probe(argc);                 /* argc = 1 로 돌린다 */
    if (v == 12345) puts("12345");       /* ★ 그 값으로 분기한다 — MSan 은 여기서 본다 */
    else puts("12345 가 아니다");
    return 0;
}
```

```c
/* s30p6.c */
#include <stdio.h>
#include <stdlib.h>

struct Pair { int x, y; };

static int probe(int c) {
    struct Pair s;
    s.x = c;                             /* P6 — 구조체의 한 멤버만 쓴다 */
    return s.y;
}

int main(int argc, char **argv) {
    (void)argv;
    int v = probe(argc);                 /* argc = 1 로 돌린다 */
    if (v == 12345) puts("12345");       /* ★ 그 값으로 분기한다 — MSan 은 여기서 본다 */
    else puts("12345 가 아니다");
    return 0;
}
```

```c
/* s30p7.c */
#include <stdio.h>
#include <stdlib.h>

static int probe(int c) {
    (void)c;
    int *p = malloc(sizeof *p);          /* P7 — malloc 한 자리를 쓰기 전에 읽는다 */
    if (!p) return 0;
    int v = *p;
    free(p);
    return v;
}

int main(int argc, char **argv) {
    (void)argv;
    int v = probe(argc);                 /* argc = 1 로 돌린다 */
    if (v == 12345) puts("12345");       /* ★ 그 값으로 분기한다 — MSan 은 여기서 본다 */
    else puts("12345 가 아니다");
    return 0;
}
```

```c
/* s30p8.c */
#include <stdio.h>
#include <stdlib.h>

static int probe(int c) {
    int a;
    switch (c) {                         /* P8 — default 가 없는 switch */
    case 2: a = 20; break;
    case 3: a = 30; break;
    }
    return a;
}

int main(int argc, char **argv) {
    (void)argv;
    int v = probe(argc);                 /* argc = 1 로 돌린다 */
    if (v == 12345) puts("12345");       /* ★ 그 값으로 분기한다 — MSan 은 여기서 본다 */
    else puts("12345 가 아니다");
    return 0;
}
```

```text
===== 불확정 값 탐침 8 × 도구 6 (경고는 uninitialized 가 들어간 것만 센다) (exit=0) =====
탐침 | gcc -O0   | gcc -O2   | clang -O0 | clang -O2 | gcc 분석기 | clang MSan
P1   | 경고 1    | 경고 1    | 경고 1    | 경고 1    | 경고 1     | 보고
P2   | 침묵      | 침묵      | 경고 1    | 경고 1    | 경고 1     | 보고
P3   | 침묵      | 경고 1    | 경고 1    | 경고 1    | 경고 2     | 보고
P4   | 침묵      | 침묵      | 침묵      | 침묵      | 침묵       | 보고
P5   | 경고 1    | 경고 1    | 침묵      | 침묵      | 경고 1     | 보고
P6   | 경고 1    | 경고 2    | 침묵      | 침묵      | 경고 1     | 보고
P7   | 경고 1    | 경고 1    | 침묵      | 침묵      | 경고 1     | 보고
P8   | 침묵      | 침묵      | 침묵      | 침묵      | 경고 1     | 보고
답한 칸 30 / 48
```

```text
===== which valgrind (exit=1) =====
```

★★★ **선언 — 탐침 8 × 도구 6 = 48칸 중 답한 칸 30, 침묵한 칸 18.**\
★ 여섯째 도구로 **Valgrind** 를 넣으려 했으나 **이 머신에 없다** — `which` 가 `exit=1` 이다. 「안 쟀다」가 아니라 「**못 잰 것**」이다.

```text
                 gcc        gcc       clang      clang      gcc        clang
                 -O0        -O2       -O0        -O2        분석기      MSan
   P1 직접       ●          ●         ●          ●          ●          ●
   P2 한쪽 가지   .          .         ●          ●          ●          ●
   P3 누산기      .    ->    ●         ●          ●          ●          ●   <- ★ -O0 침묵 · -O2 경고
   P4 주소 넘김   .          .         .          .          .          ●   <- ★ MSan 만
   P5 배열 한 칸  ●          ●         .          .          ●          ●
   P6 멤버 하나   ●          ●(2)      .          .          ●          ●
   P7 malloc     ●          ●         .          .          ●          ●
   P8 switch     .          .         .          .          ●          ●

   ● 답함 · . 침묵         ★ clang 의 두 열은 한 글자도 같다 — 프런트엔드 경고라 판을 안 탄다
```

그림 해설 (한 단계씩):

- ★★★ **MSan 만 여덟 칸 전부 답한다.** 정적 도구 다섯은 **각자 다른 자리에서** 침묵한다 — **어느 하나로 다른 것을 대신할 수 없다.**
- ★★★ **P4(주소를 넘긴 함수가 한쪽에서만 씀)는 정적 도구 다섯이 전부 침묵**한다. 컴파일러는 「주소를 넘겼으니 **초기화됐을 수도 있다**」고 본다.
- ★★★ **P3 이 `-O0` 에서 침묵하고 `-O2` 에서 경고한다** — 유명한 자리다. gcc 의 이 경고는 **최적화 패스가 만든 정보**를 쓰기 때문에 `-O0` 에서는 **볼 정보가 없다.**
- ★★★ **그런데 P2 는 반대로 `-O2` 에서도 침묵한다** — 「`-O2` 면 잡힌다」도 틀렸다. (4-나)에서 어셈블리로 이유를 본다.
- ★★ **clang 은 판을 안 탄다** — 두 열이 같다. 대신 **배열·구조체 멤버·`malloc`(P5\~P7)을 전부 놓친다.** gcc 와 **잡는 자리가 거의 겹치지 않는다.**
- ★★ **gcc `-fanalyzer` 가 정적 도구 중 가장 많이 답한다**(7/8). 하지만 **P4 는 역시 못 본다.**

**(4-나) ★★★ P3 — `-O0` 대 `-O2` 가 경고를 만든다**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -c s30p3.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -c s30p3.c -o /dev/null (cc exit=0) =====
In function ‘probe’,
    inlined from ‘main’ at s30p3.c:12:13:
s30p3.c:6:37: warning: ‘sum’ may be used uninitialized [-Wmaybe-uninitialized]
    6 |     for (int i = 0; i < c; i++) sum += i;
      |                                 ~~~~^~~~
s30p3.c: In function ‘main’:
s30p3.c:5:9: note: ‘sum’ was declared here
    5 |     int sum;                             /* P3 — 누산기를 0 으로 안 둔다 */
      |         ^~~
```

- ★★★ **`-O0` 은 진단 0줄 · `cc exit=0`**, `-O2` 는 `[-Wmaybe-uninitialized]` 1건이다. **같은 소스 · 같은 플래그 · 최적화 수준만 다르다.**
- ★★ 경고 머리가 **`In function 'probe', inlined from 'main'`** 이다 — **인라인이 된 뒤에야** 보인 것이다. 인라인은 `-O0` 에서 안 한다.

**(4-다) ★★★ P2 — `-O2` 에서 사라진 이유를 어셈블리가 답한다**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -c s30p2.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s30p2.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' (cc exit=0) =====
.LC0:
main:
	endbr64
	sub	rsp, 8
	lea	rdi, .LC0[rip]
	call	puts@PLT
	xor	eax, eax
	add	rsp, 8
	ret
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 -c s30p2.c -o /dev/null (cc exit=0) =====
s30p2.c:6:9: warning: variable 'a' is used uninitialized whenever 'if' condition is false [-Wsometimes-uninitialized]
    6 |     if (c > 5) a = 1;                    /* P2 — 한쪽 가지에서만 쓴다 */
      |         ^~~~~
s30p2.c:7:12: note: uninitialized use occurs here
    7 |     return a;
      |            ^
s30p2.c:6:5: note: remove the 'if' if its condition is always true
    6 |     if (c > 5) a = 1;                    /* P2 — 한쪽 가지에서만 쓴다 */
      |     ^~~~~~~~~~
s30p2.c:5:10: note: initialize the variable 'a' to silence this warning
    5 |     int a;
      |          ^
      |           = 0
1 warning generated.
```

- ★★★ **gcc `-O2` 의 `main` 에는 `probe` 도 비교도 없다** — `puts` 한 번이 전부다. `a` 는 「`1` 이거나 불확정」인데, 불확정은 **아무 값이어도 되므로** gcc 는 **`a = 1` 로 접었다.** 그러면 `1 == 12345` 는 거짓이고 **분기째 사라진다.**
- ★★★ **경고를 낼 코드가 최적화로 사라졌다** — 그래서 **`-O2` 에서도 침묵**한다. 「경고가 없다」가 「문제가 없다」가 아닌 가장 선명한 예다.
- ★★ **clang 은 프런트엔드에서 잡는다** — `whenever 'if' condition is false [-Wsometimes-uninitialized]`. 최적화 전이라 코드가 **아직 있다.**
- ★ 이 접기는 **UB 의 한 결과**다 — 「`a` 는 1 이 된다」가 아니다. **다른 판에서는 다르게 접을 수 있다.**

**(4-라) ★ MSan 은 P4 를 이렇게 말한다 — 제5의 상태**

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=memory -ffile-prefix-map="$PWD"=. s30p4.c -o m && ./m 2>&1 >/dev/null | sed -n '1,3p;/^SUMMARY/p' (exit=1) =====
==4091404==WARNING: MemorySanitizer: use-of-uninitialized-value
    #0 0x5f13a31ca58f in probe s30p4.c:9:5
    #1 0x5f13a31ca426 in main s30p4.c:14:13
SUMMARY: MemorySanitizer: use-of-uninitialized-value s30p4.c:9:5 in probe
```

- ★★ **정적 도구 다섯이 침묵한 P4 를 MSan 이 `s30p4.c:9:5`(`return a;`)에서 잡는다.** 「불확정인가」를 **값으로 물을 수 없어서**(무엇이 찍혀도 증거가 안 된다) **초기화 여부를 따라다니는 그림자 비트**로 물은 것이다.
- ★ **반환에서 잡는다** — `main` 의 분기(14행)가 아니라 **`probe` 의 `return a;`(9행)** 에서 멈췄다. 이 판의 MSan 이 **반환값을 바로 검사**한다는 뜻이다. ★ 그것이 **언제부터인지는 이 문서가 확인하지 않았다.**
- ★ **대가** — MSan 은 **프로그램 전체(라이브러리까지)를 계측해야** 정확하다. 이 탐침은 libc 를 거의 안 거쳐 됐다.

비용 — **도구 하나로는 부족하다.** 이 격자에서 **정적 도구 전부를 켜도 P4 를 못 잡고**, MSan 은 **실행된 경로만** 본다.

### (5) ★★ 패딩 바이트 — 초기화 형태 다섯의 판 격자

**언제 쓰나** — 구조체를 `memcmp`·해시·파일 쓰기에 통째로 쓸 때. **패딩이 어디 생기나**는 [22번 형제](../22-struct-padding-and-alignment/)가 정본이고, 여기는 「**어떤 초기화가 패딩까지 0 으로 만드나**」만 본다.

```c
/* s30e.c */
#include <stdio.h>
#include <string.h>

struct S { char c; int i; };             /* 바이트 1~3 이 패딩이다 */

static struct S st;                      /* ★ 정적 — 초기자 없음 */

static void dirty(void) {                /* 같은 깊이의 스택을 0xAA 로 더럽힌다 */
    volatile unsigned char buf[64];
    for (int k = 0; k < 64; k++) buf[k] = 0xAA;
}

static void dump(const char *tag, const struct S *p) {
    const unsigned char *b = (const unsigned char *)p;
    printf("%-20s", tag);
    for (size_t k = 0; k < sizeof *p; k++)
        printf(k >= 1 && k <= 3 ? " [%02x]" : "  %02x ", b[k]);
    printf("\n");
}

static void auto_zero(void)   { struct S v = {0};         dump("auto = {0}", &v); }
static void auto_desig(void)  { struct S v = {.i = 2};    dump("auto = {.i = 2}", &v); }
static void auto_full(void)   { struct S v = {1, 2};      dump("auto = {1, 2}", &v); }
static void auto_assign(void) { struct S v; v.c = 1; v.i = 2; dump("auto member-assign", &v); }

int main(void) {
    printf("[ ] 안이 패딩 바이트다\n");
    dump("static (no init)", &st);
    dirty(); auto_zero();
    dirty(); auto_desig();
    dirty(); auto_full();
    dirty(); auto_assign();
    return 0;
}
```

```text
===== 패딩 바이트 — 초기화 형태 5 × 컴파일러 2 × 최적화 2 (exit=0) =====
--- gcc -O0
static (no init)      00  [00] [00] [00]  00   00   00   00 
auto = {0}            00  [00] [00] [00]  00   00   00   00 
auto = {.i = 2}       00  [00] [00] [00]  02   00   00   00 
auto = {1, 2}         01  [00] [00] [00]  02   00   00   00 
auto member-assign    01  [00] [00] [00]  02   00   00   00 
--- gcc -O2
static (no init)      00  [00] [00] [00]  00   00   00   00 
auto = {0}            00  [00] [00] [00]  00   00   00   00 
auto = {.i = 2}       00  [00] [00] [00]  02   00   00   00 
auto = {1, 2}         01  [00] [00] [00]  02   00   00   00 
auto member-assign    01  [00] [00] [00]  02   00   00   00 
--- clang -O0
static (no init)      00  [00] [00] [00]  00   00   00   00 
auto = {0}            00  [00] [00] [00]  00   00   00   00 
auto = {.i = 2}       00  [00] [00] [00]  02   00   00   00 
auto = {1, 2}         01  [00] [00] [00]  02   00   00   00 
auto member-assign    01  [aa] [aa] [aa]  02   00   00   00 
--- clang -O2
static (no init)      00  [00] [00] [00]  00   00   00   00 
auto = {0}            00  [00] [00] [00]  00   00   00   00 
auto = {.i = 2}       00  [00] [00] [00]  02   00   00   00 
auto = {1, 2}         01  [00] [00] [00]  02   00   00   00 
auto member-assign    01  [aa] [aa] [aa]  02   00   00   00 
```

```text
                         gcc -O0  gcc -O2  clang -O0  clang -O2    누가 보장하나
   static (no init)       00       00       00         00          ★★★ 표준 — 패딩 비트까지 0
   auto = {0}             00       00       00         00          ★ 관찰
   auto = {.i = 2}        00       00       00         00          ★ 관찰
   auto = {1, 2}          00       00       00         00          ★ 관찰
   auto member-assign     00       00       ★ aa       ★ aa        ★ 미명시 — 남은 것이 보인다
```

그림 해설 (한 단계씩):

- ★★★ **정적 쪽은 표준이 패딩까지 0 을 보장한다** — 네 벌 다 `00`.
- ★★ **초기자가 있는 자동 셋은 네 벌 다 `00`** 이다 — 그런데 **이것은 관찰**이다. 두 컴파일러가 **구조체를 통째로 0 으로 채운 뒤** 멤버를 쓴 것일 뿐, 자동 객체의 패딩을 0 으로 만든다는 약속은 표준에 없다.
- ★★★ **멤버를 하나씩 대입하면 clang 에서 `aa` 가 보인다** — 스택을 더럽힌 `0xAA` 가 **패딩 자리에 그대로** 남았다. gcc 는 이 판에서 `00` 이었지만 **그 자리에 원래 0 이 있었을 뿐**일 수 있다.
- ★★ **표준** — 구조체나 그 멤버에 값을 저장하면 **패딩 바이트는 미명시 값**을 가진다. **미명시 칸**이다.
- ★ [22번 형제](../22-struct-padding-and-alignment/)는 **초기자로 만든 `a` 조차 `0xAA`** 가 남았다(gcc `-O0`). **이 편의 `{1, 2}` 는 `00`** 이다 — 구조체 모양도 주변 코드도 다르고, **무엇이 갈랐는지는 이 문서가 가르지 않았다.** 같은 질문에 두 편이 **다른 관찰**을 낸 것 자체가, 관찰을 규칙으로 올리면 안 되는 이유다.

비용 — **「초기자를 썼으니 패딩도 0」은 두 형제 편에서 서로 다른 답이 나왔다.** 패딩까지 0 이어야 하면 **`memset` 이 유일하게 예측 가능한 쪽**이다([22번 형제](../22-struct-padding-and-alignment/)).

### (6) ★ `malloc` 은 불확정 · `calloc` 은 0 — 그리고 `-O2` 가 실험을 지운다

**언제 쓰나** — 「`malloc` 한 메모리가 0 이던데」를 믿을까 말까.

```c
/* s30f.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

static int count_eq(const unsigned char *p, size_t from, size_t to, unsigned char v) {
    int n = 0;
    for (size_t k = from; k < to; k++) n += (p[k] == v);
    return n;
}

int main(void) {
    unsigned char *p = malloc(64);
    if (!p) return 1;
    memset(p, 0xAB, 64);                 /* 0xAB 로 채운 뒤 */
    uintptr_t old = (uintptr_t)p;
    free(p);                             /* 돌려준다 */

    unsigned char *q = malloc(64);       /* ★ 같은 크기를 다시 빌린다 — 새로 쓰기 전에 읽는다 */
    if (!q) return 1;
    printf("malloc : 방금 돌려준 조각이 다시 왔나 = %s\n", (uintptr_t)q == old ? "예" : "아니오");
    printf("malloc : 바이트 16~63 중 0xAB 그대로 = %d / 48\n", count_eq(q, 16, 64, 0xAB));
    free(q);

    unsigned char *r = calloc(64, 1);    /* ★ calloc */
    if (!r) return 1;
    printf("calloc : 바이트  0~63 중 0x00       = %d / 64\n", count_eq(r, 0, 64, 0x00));
    free(r);
    return 0;
}
```

```text
===== malloc 대 calloc — 컴파일러 2 × 최적화 2 (exit=0) =====
--- gcc -O0
malloc : 방금 돌려준 조각이 다시 왔나 = 예
malloc : 바이트 16~63 중 0xAB 그대로 = 48 / 48
calloc : 바이트  0~63 중 0x00       = 64 / 64
--- gcc -O2
malloc : 방금 돌려준 조각이 다시 왔나 = 예
malloc : 바이트 16~63 중 0xAB 그대로 = 0 / 48
calloc : 바이트  0~63 중 0x00       = 64 / 64
--- clang -O0
malloc : 방금 돌려준 조각이 다시 왔나 = 예
malloc : 바이트 16~63 중 0xAB 그대로 = 48 / 48
calloc : 바이트  0~63 중 0x00       = 64 / 64
--- clang -O2
malloc : 방금 돌려준 조각이 다시 왔나 = 아니오
malloc : 바이트 16~63 중 0xAB 그대로 = 0 / 48
calloc : 바이트  0~63 중 0x00       = 64 / 64
```

```text
===== main 이 부르는 함수를 차례대로 — 어셈블리의 call 만 (컴파일러 2 × 최적화 2) (exit=0) =====
gcc    -O0  | malloc@PLT memset@PLT free@PLT malloc@PLT printf@PLT count_eq printf@PLT free@PLT calloc@PLT count_eq printf@PLT free@PLT 
gcc    -O2  | malloc@PLT free@PLT malloc@PLT __printf_chk@PLT __printf_chk@PLT free@PLT calloc@PLT __printf_chk@PLT free@PLT 
clang  -O0  | malloc@PLT memset@PLT free@PLT malloc@PLT printf@PLT count_eq printf@PLT free@PLT calloc@PLT count_eq printf@PLT free@PLT 
clang  -O2  | malloc@PLT printf@PLT printf@PLT free@PLT calloc@PLT printf@PLT free@PLT 
```

- ★★★ **`-O0` 의 `malloc` 은 방금 돌려준 조각을 다시 주고, `0xAB` 48바이트가 그대로 남아 있다.** 「새로 빌린 메모리」에 **남의 흔적**이 있다 — 불확정이다.
- ★★ **바이트 0\~15 는 세지 않았다** — 할당기가 해제된 조각에 **자기 관리 정보**를 써 넣는 자리라, 실행마다 흔들리는 값이 들어간다.
- ★★★ **`-O2` 에서는 `0 / 48`** 이다 — 둘째 블록이 이유를 보인다. **gcc `-O2` 의 `call` 목록에 `memset` 이 없다** — 곧 `free` 할 메모리에 쓰는 것을 지웠다. **clang `-O2` 는 첫 `malloc`·`memset`·`free` 가 통째로 없다** — 그래서 「다시 왔나 = 아니오」다.
- ★★ **`calloc` 은 네 벌 다 `64 / 64`** — **모든 바이트 0 이 표준의 약속**이다.
- ★ **이 실험은 해제된 메모리를 읽지 않는다** — 옛 주소는 `free` 전에 **정수로 적어 두고** 비교했다. 해제된 포인터 값을 쓰는 것 자체가 문제이기 때문이다(목록의 **57번 주제**).

비용 — **`malloc` 뒤에 읽기 전에 반드시 쓴다.** 0 이 필요하면 `calloc` 이다 — 다만 **모든 바이트 0 이 널 포인터·`0.0` 이라는 보장**은 따로 있다(더 들어가면).

### (7) ★★★ 불확정 값을 읽는 것은 **언제** UB 인가 — 그리고 비값 표현

**언제 쓰나** — 「초기화 안 한 변수를 읽는 것은 UB 다」라는 문장이 **정확히 어디까지 맞나** 물을 때.

표준은 세 갈래로 가른다.

```text
   초기화 안 한 객체를 읽는다
     |
     +-- ① 자동 저장 기간이고 ★ 주소를 한 번도 안 잡았다 (register 로 선언될 수 있었다)
     |        -> ★★★ UB. 무엇이 들었든 상관없다
     |        예: P1 · P2 · P3 · P8 의 a / sum
     |        (P5 배열 · P6 구조체 멤버는 경계가 섬세해 ★ 이 문서가 층을 단정하지 않는다)
     |
     +-- ② 그 밖 (주소를 잡았다 · 배열 · malloc 등) -> 「불확정 표현」을 읽는다
              |
              +-- 그 바이트가 ★ 그 타입의 비값 표현이면  -> ★★★ UB (문자 타입으로 읽을 때는 제외)
              |        예: _Bool 에 바이트 2
              |
              +-- 그 타입에 비값 표현이 없거나 아니면    -> ★ 미명시 값 (UB 는 아니다)
                       예: unsigned char 로 읽는 것 · 이 구현의 int
```

그런데 ②의 **비값 표현이 실제로 어떻게 터지는지**를 보려면, 표현을 **내가 만들어 넣어야** 한다.

```c
/* s30g.c */
#include <stdio.h>
#include <string.h>
#include <stdbool.h>

int main(void) {
    bool b;
    unsigned char two = 2;
    memcpy(&b, &two, 1);                 /* ★ 0 도 1 도 아닌 바이트를 bool 에 넣는다 */
    printf("b 의 바이트    = %d\n", *(unsigned char *)&b);
    printf("b  ? 참 : 거짓 = %s\n", b ? "참" : "거짓");
    printf("!b ? 참 : 거짓 = %s\n", !b ? "참" : "거짓");
    printf("b == true      = %d\n", b == true);
    printf("(int)b         = %d\n", (int)b);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s30g.c -o x ; ./x (cc exit=0 · run exit=0) =====
b 의 바이트    = 2
b  ? 참 : 거짓 = 참
!b ? 참 : 거짓 = 참
b == true      = 2
(int)b         = 2
```

```text
===== bool 에 0 도 1 도 아닌 바이트 — 컴파일러 2 × 최적화 2 (exit=0) =====
--- gcc -O0
b  ? 참 : 거짓 = 참
!b ? 참 : 거짓 = 참
b == true      = 2
(int)b         = 2
--- gcc -O2
b  ? 참 : 거짓 = 참
!b ? 참 : 거짓 = 거짓
b == true      = 2
(int)b         = 2
--- clang -O0
b  ? 참 : 거짓 = 거짓
!b ? 참 : 거짓 = 참
b == true      = 0
(int)b         = 0
--- clang -O2
b  ? 참 : 거짓 = 거짓
!b ? 참 : 거짓 = 참
b == true      = 0
(int)b         = 0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=undefined -ffile-prefix-map="$PWD"=. s30g.c -o x && ./x 2>&1 >/dev/null (exit=0) =====
s30g.c:10:42: runtime error: load of value 2, which is not a valid value for type '_Bool'
s30g.c:11:40: runtime error: load of value 2, which is not a valid value for type '_Bool'
s30g.c:12:5: runtime error: load of value 2, which is not a valid value for type '_Bool'
s30g.c:13:5: runtime error: load of value 2, which is not a valid value for type '_Bool'
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=undefined -ffile-prefix-map="$PWD"=. s30g.c -o x && ./x 2>&1 >/dev/null (exit=0) =====
s30g.c:10:40: runtime error: load of value 2, which is not a valid value for type '_Bool'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior s30g.c:10:40 
s30g.c:11:41: runtime error: load of value 2, which is not a valid value for type '_Bool'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior s30g.c:11:41 
s30g.c:12:37: runtime error: load of value 2, which is not a valid value for type '_Bool'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior s30g.c:12:37 
s30g.c:13:42: runtime error: load of value 2, which is not a valid value for type '_Bool'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior s30g.c:13:42 
```

그림 해설 (한 단계씩):

- ★★★ **gcc `-O0` 에서 `b` 도 참이고 `!b` 도 참이다.** 그리고 **`b == true` 가 `2`** 다 — 비교 결과가 0 도 1 도 아니다. **값이 아닌 것을 값으로 읽은 결과**다.
- ★★★ **clang 은 같은 바이트를 「거짓」으로 읽는다** — `(int)b = 0`. 최하위 비트만 본 것이다. **컴파일러마다 다른 답**이 나오고, gcc 는 **최적화 수준마다도 다르다**(`-O2` 에서 `!b` 가 거짓).
- ★★ **UBSan 이 두 컴파일러에서 네 번씩 잡는다** — `load of value 2, which is not a valid value for type '_Bool'`. `cc exit=0` · `run exit=0`(리포트하고 계속 간다).\
  ★ **칸 번호가 다르다**(gcc `10:42` 대 clang `10:40`) · **clang 만 `SUMMARY` 줄을 매번 찍는다.**
- ★★ **이 구현에서 `_Bool` 의 값은 `0` 과 `1` 뿐**이고, 나머지 254개 바이트 패턴은 **비값 표현**이다. 어느 패턴이 비값인지는 **구현이 정한다.**
- ★ **`memcpy` 로 넣는 것 자체는 UB 가 아니다** — 문자 단위로 바이트를 쓴 것이다. **UB 는 `bool` 로 읽는 순간**이다.

비용 — **「초기화 안 한 변수를 읽는 것은 UB」는 ①에서만 무조건 맞다.** ②에서는 **타입이 층을 정한다.** ★ 그리고 **어느 쪽이든 처방이 없다** — 읽기 전에 쓴다.

### (8) ★ 다른 언어는 이 문제를 언어가 막는다

**언제 쓰나** — 「C 는 왜 이걸 안 막나」를 물을 때.

```rust
// s30r.rs
fn main() {
    let x: i32;
    println!("{}", x);
}
```

```text
===== rustc s30r.rs (rustc exit=1) =====
error[E0381]: used binding `x` isn't initialized
 --> s30r.rs:3:20
  |
2 |     let x: i32;
  |         - binding declared here but left uninitialized
3 |     println!("{}", x);
  |                    ^ `x` used here but it isn't initialized
  |
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider assigning a value
  |
2 |     let x: i32 = 42;
  |                ++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0381`.
```

```text
===== rustc --version (exit=0) =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
```

```go
// s30go.go
package main

import "fmt"

type Cfg struct {
	Port int
	Name string
	Next *Cfg
}

func main() {
	var i int
	var s string
	var p *int
	var c Cfg
	fmt.Printf("int=%d string=%q pointer=%v struct=%+v\n", i, s, p, c)
}
```

```text
===== go run s30go.go (exit=0) =====
int=0 string="" pointer=<nil> struct={Port:0 Name: Next:<nil>}
```

```text
===== go version (exit=0) =====
go version go1.27.1 linux/amd64
```

- ★★★ **Rust 는 컴파일러가 막는다** — `E0381`, `rustc exit=1`. 「초기화 안 된 읽기」가 **프로그램이 되지 못한다.** 정본은 [Rust 02 — 바인딩·`mut`·섀도잉](../../../rust/syntax/02-bindings-mut-and-shadowing/)이다.
- ★★★ **Go 는 언어가 0 을 보장한다** — 모든 변수가 **제로 값**으로 시작한다. **C 의 정적 저장 기간 규칙을 모든 변수에** 적용한 것과 같다. 정본은 [Go 02 — 변수 선언과 제로 값](../../../go/syntax/02-variable-declarations-and-zero-values/)이다.
- ★★ **C 는 둘 다 안 한다** — 자동 변수를 0 으로 채우는 비용을 **프로그래머의 선택**으로 남겼고, 그 대가가 (4)의 격자다.

## 문법 — 형태와 규칙

### 형태

(2)의 `s30c.c` 와 (3)의 `s30d.c` 가 이 절의 **실제로 컴파일되는 형태**다. 한 줄씩 다시 적으면:

| 쓴 꼴 | 저장 기간 | 결과 | 층 |
|---|---|---|---|
| `static int s;` | 정적 | `0` · 패딩까지 0 · `.bss` | ★★★ 표준 |
| `int g = 0;`(파일 스코프) | 정적 | `0` · ★ **역시 `.bss`** | 표준(배치는 구현) |
| `int a;`(함수 안) | 자동 | ★★ **불확정** | 표준 — 읽으면 (7) |
| `int a[8] = {1};` | 자동 | `1 0 0 0 0 0 0 0` | ★★★ 표준 |
| `struct Cfg c = {.retries = 3};` | 자동 | 나머지 `0` · 널 · `0.0` | ★★★ 표준 |
| `int a[4] = {};` | 자동 | `0 0 0 0` | ★ **C23 부터** 표준 · C17 에서는 확장 |
| `malloc(64)` | 할당 | ★★ **불확정** | 표준 |
| `calloc(64, 1)` | 할당 | 모든 바이트 0 | 표준 |

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 종료 코드 | 층 | 어느 절 |
|---|---|---|---|
| 주소를 안 잡은 `int a;` 를 읽음 | 도구마다 다름(격자) · `cc exit=0` | ★★★ UB | (4)·(7) |
| 주소를 넘긴 뒤 한쪽에서만 씀(P4) | ★★ **정적 도구 다섯 전부 침묵** · MSan 만 | 불확정 표현 읽기 — 타입에 달림 | (4) |
| `bool` 에 바이트 `2` 를 넣고 읽음 | 경고 0 · UBSan 4건 · `run exit=0` | ★★★ UB(비값 표현) | (7) |
| `-std=c17` 에서 `= {}` | ★★ **경고 0 · `cc exit=0`** · `-pedantic-errors` 라야 `exit=1` | ill-formed(C17 문법 밖) | (3) |
| 멤버 대입 뒤 패딩을 읽음 | 경고 0 | ★ 미명시 | (5) |

### 규칙 불릿

- ★★★ **정적·스레드 저장 기간 객체는 초기자가 없으면 0 이다** — 포인터는 널, 부동소수는 `+0.0`, **패딩 비트까지 0**.
- ★★★ **초기자가 하나라도 있으면 적지 않은 칸은 0 이다** — 자동 저장 기간이어도.
- ★★★ **자동 저장 기간 객체와 `malloc` 은 초기자가 없으면 불확정이다.**
- ★★★ **주소를 한 번도 안 잡은 자동 객체를 초기화 전에 읽으면 UB** 다. 그 밖에서는 **비값 표현이면 UB, 아니면 미명시 값**이다.
- ★★ **`.bss` 는 `NOBITS`** 다 — 0 인 정적 객체는 **파일 크기를 안 늘린다.** 원소 하나라도 0 이 아니면 **배열 전체가 `.data`** 로 간다.
- ★★ **불확정 값을 잡는 도구는 서로 대신할 수 없다** — 48칸 중 30칸이 답했고, **MSan 만 8/8** 이다.
- ★★ **gcc 의 경고는 최적화 수준을 탄다** — P3 은 `-O0` 침묵 · `-O2` 경고, P2 는 **`-O2` 에서 코드째 접혀** 침묵.
- ★★ **패딩 바이트는 멤버에 값을 저장한 뒤 미명시**다 — 초기자가 있어도 **자동 객체의 패딩이 0 이라는 보장은 없다.**
- ★ **`= {}` 는 C23 부터**다. `-std=c17` 은 **경고 0 · `cc exit=0`** 으로 받는다.
- ★ **`_Bool` 의 `0`·`1` 밖 바이트는 비값 표현**이다 — gcc 는 「참이면서 거짓」, clang 은 「거짓」으로 읽었다.

## 어디서 틀리나

### 1. ★★★ 「경고가 안 났으니 초기화는 다 됐다」

**격자 48칸 중 18칸이 침묵**했다((4)). **P4 는 정적 도구 다섯이 전부 침묵**하고, **P2 는 gcc 가 `-O2` 에서 코드째 접어** 침묵한다.\
★ 「경고 0건」은 **이 도구가 이 판에서 못 봤다**는 뜻일 뿐이다.

### 2. ★★★ 「`-O2` 로 빌드하면 경고가 더 잘 나온다」

**P3 은 맞고 P2 는 틀리다**((4-나)·(4-다)). 최적화는 경고에 쓸 정보를 **만들기도 하고 지우기도 한다.**\
★ **판 격자를 돌려라** — 한 판만 보고 성질을 말하지 마라.

### 3. ★★★ 「초기화 안 한 변수를 읽는 것은 무조건 UB 다」

**주소를 안 잡은 자동 객체에서만 무조건**이다((7)). 그 밖에서는 **타입의 비값 표현**이 층을 정한다.\
★ 반대로 「**UB 가 아니면 괜찮다**」도 틀리다 — 미명시 값은 **아무 값**이다. 처방은 늘 같다 — **읽기 전에 쓴다.**

### 4. ★★ 「`= {0}` 이면 패딩도 0 이다」

**이 판에서 그렇게 보였을 뿐**이다((5)). 정적은 표준이 보장하고 자동은 **관찰**이다. [22번 형제](../22-struct-padding-and-alignment/)에서는 초기자로 만든 구조체에 `0xAA` 가 남았다.

### 5. ★★ 「`malloc` 한 메모리가 0 이던데」

**처음 받은 페이지가 0 이었을 뿐**이다((6)). 해제했다 다시 받으면 **남의 흔적**(`0xAB` 48바이트)이 있다. 0 이 필요하면 **`calloc`**.

### 6. ★★ 「큰 정적 배열은 바이너리를 키운다」

**0 이면 안 키운다**((1)). `.bss` 는 `NOBITS` 라 **크기만 적힌다.** 원소 하나를 `1` 로 바꾸자 **1768 → 401792 바이트**가 됐다.

### 7. ★ 「`bool` 은 참 아니면 거짓이다」

**`0`·`1` 밖의 바이트면 둘 다 아니다**((7)). gcc `-O0` 에서 `b` 도 참, `!b` 도 참이었다.

### 8. ★ 「`-std=c17` 로 빌드하니 C23 문법은 막히겠지」

**`= {}` 가 경고 0 · `cc exit=0`** 으로 통과했다((3)). **`-pedantic-errors`** 라야 막힌다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」과 「UB」가 같은 두께**이고, **「미명시」가 가장 정밀한 칸**이다 — 불확정 표현이 **미명시 값이냐 비값 표현이냐**가 층을 가른다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | **정적·스레드 = 0**(패딩 비트까지) · **부분 초기화의 나머지 0** · 지정 초기자 · **자동·`malloc` = 불확정** · `calloc` = 모든 바이트 0 · **`= {}` 가 C23 부터**인 것 | `.bss` 크기 · 네 벌 md5 동일 · `calloc 64 / 64` · 판 격자 |
| **조건부 표준** | 매크로가 정의될 때만 | ★ **이 편이 던진 것 중에는 없다.** (`calloc` 의 0 바이트가 `double` 의 `+0.0` 이 되는 것은 IEC 60559 부록에 기댄다 — **던지지 않았다**) | — |
| ★ **구현 정의** | 문서화 의무가 있다 | ★★ **어느 타입에 비값 표현이 있나**(이 구현의 `_Bool` 은 `0`·`1` 밖이 전부 비값 · `int` 는 없다) · `.bss`/`NOBITS` 라는 배치 · clang 이 `static const` 를 심볼째 접는 것 · 진단 이름과 문구 | UBSan `not a valid value for type '_Bool'` · `readelf -S` · `nm -S` 두 벌 |
| ★★ **미명시** | 몇 가지 중 하나 · 문서화 의무도 없다 | ★★★ **불확정 표현이 비값이 아닐 때 그 값** · ★★ **멤버 저장 뒤의 패딩 바이트** · 해제된 조각이 다시 오는지와 그 내용 | 패딩 격자(clang `aa`) · `malloc` 격자 네 벌이 전부 다름 |
| ★★★ **UB** | 아무 일이나 | ★★★ **주소를 안 잡은 자동 객체를 초기화 전에 읽기**(P1·P2·P3·P8) · ★★★ **비값 표현을 비문자 타입으로 읽기**(`_Bool` 에 `2`) | ★ P2 가 `-O2` 에서 **`a = 1` 로 접혀 사라짐** · `bool` 격자 — gcc 「참이면서 참」·clang 「거짓」 |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★ **「이 0 은 보장인가 우연인가」를 말해 주는 도구가 없다** — 네 벌이 전부 `00` 인 패딩(자동)도, 보장된 `00`(정적)도 **같은 글자**다 |
| **조건부 표준** | — (던진 것 없음) |
| ★ **구현 정의** | ★ **어느 비트 패턴이 비값인지 컴파일러가 알려 주지 않는다** — `_Bool` 은 UBSan 이 **읽는 순간**에야 말한다 |
| ★★ **미명시** | ★★★ **패딩 바이트에 무엇이 남았는지는 경고 0건**이다 — MSan 도 **분기에 안 쓰이면** 조용하다. ★ `malloc` 재사용은 **어느 도구도 안 본다**(읽기 전에 쓰지 않았다는 사실은 MSan 만 본다) |
| ★★★ **UB** | ★★★ **P4 는 정적 도구 다섯이 전부 침묵** · **P2 는 gcc 가 코드를 지워 침묵** · ★★ **Valgrind 는 이 머신에 없다** |
| ★★ **(층을 가로지름)** | ★★★ **「종료 코드가 0인데 ill-formed」** — `-std=c17` 의 **`= {}` 가 경고 0 · `cc exit=0`**. `-pedantic` 으로 경고, **`-pedantic-errors` 라야 `exit=1`** 이다 |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **가장 위험한 칸은 P2 의 gcc `-O2`** 다 — **UB 가 코드째 접혀** 경고를 낼 대상이 사라졌다. 「최적화가 경고를 도와준다」의 **반례**다.
  - ★★★ **MSan 만 8/8** 이지만 **실행된 경로만** 본다 — 정적 도구와 **서로 다른 구멍**을 가진다.
  - ★★ **「0 이 보인다」는 이 편에서 세 번 증거가 못 됐다** — 자동 패딩의 `00` · 첫 `malloc` 의 0 · [28번 형제](../28-choosing-among-four-storage-durations/)의 gcc `a_indet=0`.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 자동 변수를 쓰기 | ★★★ **선언과 함께 초기화** `int a = 0;` | 「어차피 뒤에서 쓴다」 |
| 배열·구조체를 0 으로 | ★★ `= {0}`(C17) · `= {}`(C23) | 멤버를 하나씩 대입(나머지·패딩이 남는다) |
| 패딩까지 0 이어야 한다(`memcmp`·해시·전송) | ★★ **`memset(&s, 0, sizeof s)` 뒤 대입** | `= {0}` 을 믿기(자동은 관찰일 뿐) |
| 0 인 큰 테이블 | ★ **정적 배열**(`.bss` — 파일이 안 커진다) | 원소 하나만 0 이 아닌 초기자(전체가 `.data`) |
| 힙에 0 으로 | ★ **`calloc`** | `malloc` 뒤 「0 이던데」 |
| 불확정 값 찾기 | ★★★ **gcc(`-O0`+`-O2`) + clang + MSan** 을 **같이** | 도구 하나 · 판 하나 |
| C17 을 지키기 | ★ **`-pedantic-errors`** | `-std=c17` 만 |

판단 규칙 두 줄.

- ★★★ **「이 객체는 초기자가 있나」를 먼저 본다** — 없으면 **저장 기간**이 답을 정한다. 하나라도 있으면 **나머지는 0** 이다.
- ★★ **「읽기 전에 쓰였나」를 도구에 묻지 말고 코드로 보장한다** — 도구는 48칸 중 18칸에서 침묵했다.

## 핵심 문장

- ★★★ **정적 저장 기간은 0 이 보장되고, 그 0 은 `.bss`(`NOBITS`)라 파일에 실리지 않는다** — 원소 하나를 1 로 바꾸자 1768 → 401792 바이트.
- ★★★ **초기자가 하나라도 있으면 나머지는 0** 이다 — 자동이어도, 네 벌이 한 글자도 같았다.
- ★★★ **불확정 값 탐침 8 × 도구 6 = 48칸 중 30칸만 답했다** — MSan 8/8, P4 는 정적 도구 전부 침묵.
- ★★★ **gcc 경고는 판을 탄다** — P3 은 `-O0` 침묵 · `-O2` 경고, **P2 는 `-O2` 에서 `a = 1` 로 접혀 침묵**했다.
- ★★★ **주소를 안 잡은 자동 객체를 읽으면 UB, 그 밖은 비값 표현이면 UB · 아니면 미명시 값**이다.
- ★★ **`_Bool` 에 `2` 를 넣으면 gcc 는 참이면서 참(`!b` 도 참), clang 은 거짓**으로 읽었다 — UBSan 은 둘 다 잡았다.
- ★★ **패딩 바이트는 멤버 저장 뒤 미명시**다 — clang 의 멤버 대입에서 `aa` 가 남았다.
- ★ **`-std=c17` 의 `= {}` 는 경고 0 · `cc exit=0`** — 「종료 코드 0인데 ill-formed」.

## 관련 자료

- [28번 형제 — 저장 기간 4종을 고르는 법](../28-choosing-among-four-storage-durations/) — ★★★ **직접 선행.** 「정적은 0 · 자동은 불확정」의 **첫 관찰**과 여섯 벌 격자가 거기 있다.
- [21번 형제 — 구조체 선언·초기화·지정 초기자](../21-struct-declaration-initialization-and-designated-initializers/) — ★★ **지정 초기자 문법**의 정본.
- [22번 형제 — 구조체 패딩·정렬](../22-struct-padding-and-alignment/) — ★★ **패딩이 어디 생기고 `memcmp` 가 왜 위험한가**의 정본. (5)는 그 위에 **초기화 형태**만 얹었다.
- [29번 형제 — 스코프와 링크](../29-scope-and-linkage-static-extern/) — ★ `B`/`b`(`.bss`)라는 `nm` 글자를 거기서 먼저 봤다.
- 목록의 **37번 주제** — `malloc`/`calloc`/`realloc`/`free`. **API 계약과 실패 처리**의 정본.
- 목록의 **50번 주제** — `<string.h>` 메모리 함수. `memset`·`memcmp` 의 계약.
- 목록의 **57번 주제** — 시간 위반. (6)이 **해제된 포인터를 안 읽은 이유**.
- 목록의 **58번 주제** — UB 를 잡는 도구. MSan·UBSan·`-fanalyzer` **사용법**의 정본.
- ★ **다른 갈래** — [Rust 02 — 바인딩·`mut`·섀도잉](../../../rust/syntax/02-bindings-mut-and-shadowing/)(`E0381`) · [Go 02 — 변수 선언과 제로 값](../../../go/syntax/02-variable-declarations-and-zero-values/).

## 용어 풀이

> **불확정 표현(indeterminate representation)** — 미명시 값이거나 비값 표현인 객체 표현.\
> 예: 초기화 안 한 자동 `int a;`, `malloc` 이 돌려준 바이트.

> **미명시 값(unspecified value)** — 그 타입의 **올바른 값 중 하나**인데 **어느 것인지 정해지지 않은** 것.\
> 예: 멤버 대입 뒤의 패딩 바이트.

> **비값 표현(non-value representation)** — 그 타입의 어떤 값도 아닌 비트 패턴. C17 까지는 **트랩 표현**이라 불렀다.\
> 예: 이 구현의 `_Bool` 에서 `2`. 문자 타입이 아닌 것으로 읽으면 UB.

> **`.bss` / `NOBITS`** — 0 으로 시작하는 정적 객체의 섹션. 파일에 **크기만** 적는다.\
> 예: `readelf -S` 의 `.bss NOBITS … 061aa0`.

> **`-Wmaybe-uninitialized`** — gcc 가 **최적화 패스의 정보**로 내는 경고. `-O0` 에서는 거의 안 난다.\
> 예: P3 이 `-O2` 에서만 이 경고를 받았다.

> **`-Wsometimes-uninitialized`** — clang 이 **프런트엔드**에서 「어떤 가지에서는 초기화가 안 된다」를 잡는 경고.\
> 예: P2 에 `whenever 'if' condition is false`.

> **MSan(MemorySanitizer)** — clang 의 도구. 바이트마다 **「초기화됐나」 그림자 비트**를 달고, 초기화 안 된 값이 **분기·반환**에 쓰이면 알린다.\
> 예: P4 를 `s30p4.c:9:5` 에서 잡았다.

> **잠정 정의와의 관계** — 파일 스코프 `int t;` 는 [29번 형제](../29-scope-and-linkage-static-extern/)의 잠정 정의이고, 파일 끝까지 정의가 없으면 **이 편의 규칙대로 0** 이 된다.\
> 예: `nm` 의 `B t`.

## 더 들어가면

- ★★ **`calloc` 의 모든 바이트 0 이 널 포인터·`0.0` 인가** — 널 포인터 표현은 **구현 정의**, `0.0` 은 IEC 60559 부록에 기댄다. ★ **던지지 않았다.**
- ★★ **`-ftrivial-auto-var-init=zero`**(gcc 12+ · clang) — 자동 변수를 **컴파일러가 0 으로 채우게** 하는 옵션이다. (4)의 격자를 **통째로 바꿀** 것이다. ★ **던지지 않았다.**
- ★ **MSan 에 패딩 `memcmp` 를 주면** — 분기에 쓰이면 잡을 것이다. ★ **던지지 않았다.**
- ★ **Valgrind 의 `--track-origins`** — ★ **못 잰 것**. 이 머신에 Valgrind 가 없다.
- ★ **C23 의 `= {}` 가 패딩까지 0 을 보장하나** — cppreference 는 **빈 초기화(empty-initialization)** 에 패딩 비트 0 을 포함한다고 적는다. ★ 이 문서는 **그것을 실행으로 가르지 않았다**(관찰로는 `= {0}` 과 같은 `00` 이 나올 뿐이다).
