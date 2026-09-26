# c/syntax/36 — 가변 인자 함수 `<stdarg.h>`: 「**`...` 뒤에서는 타입이 사라지고, 승격된 것만 남는다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) — 「**`...` 뒤의 인자에는 정수 승격과 `float` → `double` 을 건다(기본 인자 승격)**」, `va_arg` 의 「**꺼내는 타입이 승격된 실제 인자의 타입과 호환되지 않으면 UB — 부호만 다른 정수 등 예외 넷**」·「**다음 인자가 없으면 UB**」, `va_list` 를 다른 함수에 넘겨 그쪽이 `va_arg` 를 부르면 「**부른 쪽의 `ap` 는 불확정**」, 「**`va_end` 없이 돌아가면 UB**」, C23 의 **`void va_start(va_list ap, ...);`** 서명, 전처리기의 「**`...` 를 뺀 매개변수 수만큼만 인자가 있으면 된다**」(`...` 자리에 인자 0개가 합법)를 **본문에서 직접 찾아 읽었다**)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **진단·종료 코드·어셈블리는 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★★★ **본체는 승격 격자다** — 넘긴 타입 5 × 꺼낸 타입 2(승격 전 / 승격 후) × 컴파일러 2 × `-O0`/`-O2`, 칸마다 **경고 수 · 실행 종료 코드 · 값이 같나.**\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> **버전** — `<stdarg.h>` 는 **C89 부터**, **`va_copy` 는 C99 부터**다. ★ **C23** 이 `va_start` 의 두 번째 인자를 **없어도 되게** 하고, **이름 있는 매개변수가 없는 `f(...)`** 를 허락했다((8)의 판 격자).
> ★★ **경계** — **정수 승격 규칙 자체**는 [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/), **`float` → `double`** 은 [04번 형제](../04-floating-point-types-and-conversions/)가 정본이다. **프로토타입이 없을 때의 승격**은 [34번 형제](../34-function-declarations-definitions-and-prototypes/)가 정본이다 — 이 편과 **한 사슬**이다.\
> ★ **`printf` 계열의 형식 문자열**은 목록의 **47번 주제**가 정본이다. 여기는 「**형식을 컴파일러가 검사하느냐**」만 본다.
> 선행 — [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/) · [34번 형제](../34-function-declarations-definitions-and-prototypes/).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 둘째 창 — 실행 결과의 승격 격자다.** 승격되는 타입(`char`·`unsigned char`·`short`·`_Bool`·`float`)을 넘기고 **승격 전 타입 / 승격 후 타입**으로 꺼내, 칸마다 **경고 · 종료 코드 · 값**을 한 줄에 찍는다.
★★★ 그 격자에서 **두 컴파일러가 정반대로 갈렸다** — gcc 는 **프로그램을 죽이고**(`exit=132`), clang 은 **값을 낸다** — 그리고 그 값이 **대부분 맞아 보인다.**

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | 승격 전 타입의 `va_arg`(두 컴파일러 경고) · `-Wformat` · `format`·`sentinel` 속성 · C23 판 격자 | 씀 |
| ★★★ ② **실행 출력(승격 격자)** | ★ **본체** — gcc `exit=132` · clang 「같나 = 1」(맞아 보이는 UB) · `float` 만 `0` | 씀 |
| ③ sanitizer | ★★ **`va_arg(ap, float)` 탐침 8칸(컴파일러 2 × ASan·UBSan × 최적화 2) · 과잉 읽기 탐침 5칸 — 리포트 0줄** | 씀(침묵) |
| ④ `-O2` 어셈블리 | ★★ gcc 가 그 자리를 **`ud2`**(일부러 죽는 명령)로 바꾼 것 · `va_end` 가 **아무 명령도 안 만든** 것 | 씀 |
| 시간 측정 | — | 부적용(성능 주제가 아니다) |
| ★ 제5의 상태 | 「`va_end` 를 안 부르면 무슨 일이 나나」를 **실행**으로 물으면 **아무 일도 안 난다** — 그것만으로는 「괜찮다」인지 「못 봤다」인지 모른다. **어셈블리로 바꿔 물어** 「`va_end` 는 이 판에서 **명령이 0개**다」를 봤다 | 창을 바꿔 답함 |

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
| **흔들린다** | ★★ **`printf("%d\n", 3.0)` 이 찍는 수** | 레지스터에 남은 값이다 — ★ 그래서 **수를 싣지 않고 「3 이 찍힌 판 N / 10」으로** 찍었다(그 칸은 안 흔들린다) |
| 안 흔들린다 | ★★★ **승격 격자 전부**(경고 수 · `exit` · 같나) | 같은 컴파일러 · 같은 플래그면 같다 — **UB 의 값은 「같나」 참/거짓으로만** 싣는다 |
| 안 흔들린다 | ★★ `va_arg(ap, float) -> 0`(clang) | 이 판의 번역이 정해져 있다 — 「**이 판의 값**」이다 |
| 안 흔들린다 | 어셈블리 · `va_end` 비교 격자 · C23 판 격자 · sanitizer 격자 | 같다 |

★★ **정규화 규칙은 기본 넷뿐**이다 — 흔들리는 칸을 **블록에 싣지 않게** 찍었다.

## 한눈에 — 쉽게 말하면

**가변 인자는 「내용물 표시 없는 택배 상자 줄」이다.**

- **보내는 쪽은 표준 규격 상자에만 담을 수 있다** — 작은 물건(`char`·`short`·`_Bool`)은 **중간 상자(`int`)** 에, `float` 은 **큰 상자(`double`)** 에 담긴다. → **기본 인자 승격**
- **받는 쪽은 「다음 상자는 작은 상자」라고 믿고 열 수 없다** — 작은 상자는 **애초에 오지 않는다.** → **`va_arg(ap, char)` · `va_arg(ap, float)` 는 UB**
- **상자에 무엇이 들었는지 적힌 곳이 없다** — 몇 개인지도, 무슨 타입인지도 **받는 쪽이 따로 알아야** 한다. → **개수 인자 · 센티널(`NULL`) · 형식 문자열**
- **`printf` 만은 우체국이 송장을 대조해 준다** — 형식 문자열을 **컴파일러가 안다.** 내가 만든 함수는 **송장을 붙여 줘야** 대조된다. → **`-Wformat` · `format` 속성**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 중간 상자·큰 상자 | `char`·`short`·`_Bool` → `int`, `float` → `double` | ★★ 34편의 `cvtss2sd` · 이 편의 격자 |
| 작은 상자를 기다리기 | `va_arg(ap, float)` · `va_arg(ap, char)` | ★★★ **gcc 는 죽고(`132`) clang 은 값을 낸다** |
| 내용물 표시 없음 | 개수 · 타입을 모른다 | ★★ **과잉 읽기에 sanitizer 0 / 5** |
| 송장 대조 | `printf` 의 `-Wformat` | ★★ 두 컴파일러 경고 |
| 내 상자에 송장 붙이기 | `__attribute__((format(printf, 1, 2)))` | ★★ **붙이면 경고가 되살아난다** |

```text
   same(1, (char)'A')            ...  뒤의 인자                    받는 쪽
   ---------------------------   ---------------------------    ------------------------------
   'A' 는 char                -> 정수 승격 -> int 로 넘어간다 -> va_arg(ap, int)   ★ 맞다
                                                               va_arg(ap, char)  ★ UB
   1.5f 는 float              -> float -> double 로          -> va_arg(ap, double) ★ 맞다
                                                               va_arg(ap, float) ★ UB
```

- ★★★ **이 주제는 「UB」 칸이 본체**다 — 가변 인자 함수의 사고는 **거의 전부 `va_arg` 가 실제 인자와 안 맞는 것**이고, 표준은 그것을 UB 로 둔다.
- ★★★ **「표준」 칸이 그 UB 의 경계를 정밀하게 긋는다** — **부호만 다른 정수**(`int` ↔ `unsigned int`, 값이 둘 다에 들 때)는 **예외로 허락**된다.
- ★★ **「구현 정의」 칸에 `va_list` 가 든다** — 이 판에서 `sizeof(va_list) = 24` 이고 **배열 타입**처럼 동작한다((6)).

> **가변 인자 함수(variadic function)** — 매개변수 목록이 `...` 로 끝나는 함수. `...` 뒤의 인자는 **수도 타입도 선언에 없다.**\
> 예: `int printf(const char *, ...);`.

> **`va_arg`** — `va_list` 에서 **다음 인자 하나를 지정한 타입으로 꺼내는** 매크로. 그 타입이 **승격된 실제 인자와 호환되지 않으면 UB**.\
> 예: `va_arg(ap, int)`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **승격된 인자를 승격 전 타입으로 꺼내면 무엇이 나오나** — 두 컴파일러의 컴파일 · 실행 · sanitizer.
2. ★★ **가변 인자 함수의 타입과 개수는 누가 검사하나** — `printf` 는 되고 내 함수는 안 되는 이유와 되살리는 법.
3. ★★ **`va_list` 를 다루는 규칙** — `va_copy` · `va_end` · C23 의 변경.

## 동작 방식

### (1) ★★★ `va_arg(ap, float)` — 두 컴파일러가 정반대로 간다

**언제 쓰나** — 가변 인자로 `float` 을 받으려 할 때. ★★★ **이 편의 첫 칸**이다.

```c
/* s36a.c */
#include <stdarg.h>
#include <stdio.h>

static double get_double(int n, ...) {
    va_list ap;
    va_start(ap, n);
    double v = va_arg(ap, double);
    va_end(ap);
    return v;
}

static double get_float(int n, ...) {
    va_list ap;
    va_start(ap, n);
    float v = va_arg(ap, float);
    va_end(ap);
    return v;
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    float f = 1.5f;
    printf("[1] va_arg(ap, double) -> %g\n", get_double(1, f));
    printf("[2] va_arg(ap, float)  -> %g\n", get_float(1, f));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s36a.c -o /dev/null (cc exit=0) =====
In file included from s36a.c:1:
s36a.c: In function ‘get_float’:
s36a.c:15:26: warning: ‘float’ is promoted to ‘double’ when passed through ‘...’
   15 |     float v = va_arg(ap, float);
      |                          ^
s36a.c:15:26: note: (so you should pass ‘double’ not ‘float’ to ‘va_arg’)
s36a.c:15:26: note: if this code is reached, the program will abort
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s36a.c -o /dev/null (cc exit=0) =====
s36a.c:15:26: warning: second argument to 'va_arg' is of promotable type 'float'; this va_arg has undefined behavior because arguments will be promoted to 'double' [-Wvarargs]
   15 |     float v = va_arg(ap, float);
      |                          ^~~~~
/usr/lib/llvm-18/lib/clang/18/include/__stdarg_va_arg.h:20:47: note: expanded from macro 'va_arg'
   20 | #define va_arg(ap, type) __builtin_va_arg(ap, type)
      |                                               ^~~~
1 warning generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s36a.c -o x ; ./x (cc exit=0 · run exit=132) =====
[1] va_arg(ap, double) -> 1.5
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s36a.c -o x ; ./x (cc exit=0 · run exit=0) =====
[1] va_arg(ap, double) -> 1.5
[2] va_arg(ap, float)  -> 0
```

그림 해설 (한 단계씩):

- ★★★ **두 컴파일러 다 경고**한다 — 그런데 **말이 다르다.** gcc 는 「`float` 은 `...` 를 지나며 `double` 로 승격된다 · **이 코드에 닿으면 프로그램이 중단된다**」, clang 은 「**이 `va_arg` 는 UB** — 인자가 `double` 로 승격된다」.
- ★★★ **gcc 는 말한 대로 죽인다** — **`run exit=132`**(SIGILL), `[1]` 줄만 찍히고 `[2]` 가 없다. 표준 출력을 **버퍼 없이** 둬서 `[1]` 이 살아남았다(sanitizer·시그널이 버퍼를 지우는 사고를 막으려고).
- ★★★ **clang 은 값을 낸다 — `0`**. `double` `1.5` 의 비트를 `float` 자리로 읽은 쓰레기다. **`exit=0`** 이다.
- ★ **둘 다 `cc exit=0`** — 경고만 보고 넘기면 **gcc 판은 실행 중 죽고 clang 판은 조용히 틀린다.**

```text
   float v = va_arg(ap, float);      경고는 둘 다 · cc exit 는 둘 다 0

   gcc 13                                   clang 18
   --------------------------------------   --------------------------------------
   "닿으면 중단된다"                          "이 va_arg 는 UB 다"
   그 자리에 ud2 를 심는다                    double 의 비트를 float 으로 읽는다
   실행 -> SIGILL · run exit 132             실행 -> 0 · run exit 0
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s36a.c -o - 2>/dev/null | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand | sed -n '/^get_float/,/ud2/p' (cc exit=0) =====
get_float.constprop.0:
        mov     rax, QWORD PTR fs:40
        mov     QWORD PTR -16[rsp], rax
        xor     eax, eax
        lea     rax, 8[rsp]
        mov     QWORD PTR -32[rsp], rax
        ud2
```

- ★★ **gcc `-O2` 의 `get_float` 는 `ud2` 로 끝난다** — `ud2` 는 **「정의되지 않은 명령」을 일부러 실행해 SIGILL 을 내는** 명령이다. 경고의 「중단된다」가 **이 한 줄**이다.

```text
===== va_arg(ap, float) 를 실행하면 — 컴파일러 2 × sanitizer 3 × 최적화 2 (stdout 무버퍼) (exit=0) =====
gcc    (없음)     -O0  run exit=132 리포트 0줄 | [1] va_arg(ap, double) -> 1.5|
gcc    (없음)     -O2  run exit=132 리포트 0줄 | [1] va_arg(ap, double) -> 1.5|
gcc    address    -O0  run exit=132 리포트 0줄 | [1] va_arg(ap, double) -> 1.5|
gcc    address    -O2  run exit=132 리포트 0줄 | [1] va_arg(ap, double) -> 1.5|
gcc    undefined  -O0  run exit=132 리포트 0줄 | [1] va_arg(ap, double) -> 1.5|
gcc    undefined  -O2  run exit=132 리포트 0줄 | [1] va_arg(ap, double) -> 1.5|
clang  (없음)     -O0  run exit=0   리포트 0줄 | [1] va_arg(ap, double) -> 1.5|[2] va_arg(ap, float)  -> 0|
clang  (없음)     -O2  run exit=0   리포트 0줄 | [1] va_arg(ap, double) -> 1.5|[2] va_arg(ap, float)  -> 0|
clang  address    -O0  run exit=0   리포트 0줄 | [1] va_arg(ap, double) -> 1.5|[2] va_arg(ap, float)  -> 0|
clang  address    -O2  run exit=0   리포트 0줄 | [1] va_arg(ap, double) -> 1.5|[2] va_arg(ap, float)  -> 0|
clang  undefined  -O0  run exit=0   리포트 0줄 | [1] va_arg(ap, double) -> 1.5|[2] va_arg(ap, float)  -> 0|
clang  undefined  -O2  run exit=0   리포트 0줄 | [1] va_arg(ap, double) -> 1.5|[2] va_arg(ap, float)  -> 0|
```

- ★★ **sanitizer 를 켜도 바뀌지 않는다** — gcc 는 ASan·UBSan 판에서도 **`132`**(sanitizer 가 아니라 **컴파일러가 심은 `ud2`** 가 죽인다), clang 은 ASan·UBSan 판에서 **리포트 0줄 · `0`**. **sanitizer 를 켠 8칸 중 리포트를 낸 칸 0** — gcc 의 네 칸이 죽은 것은 sanitizer 의 답이 아니다.

### (2) ★★★ 승격 격자 — 넘긴 타입 다섯 × 꺼낸 타입 둘

**언제 쓰나** — 「`char` 를 넘겼으니 `char` 로 받자」가 되는지 **타입마다** 확인할 때. ★★★ **이 편의 본체**다.

```c
/* s36b.c */
#include <stdarg.h>
#include <stdio.h>

#ifndef PASS                       /* 격자는 -DPASS=… -DPULL=… -DVAL=… 로 바꿔 끼운다 */
#define PASS char
#define PULL char
#define VAL  'A'
#endif

static int same(int n, ...) {
    va_list ap;
    va_start(ap, n);
    PASS got = (PASS)va_arg(ap, PULL);
    va_end(ap);
    return got == (PASS)VAL;
}

int main(void) {
    printf("%d\n", same(1, (PASS)VAL));
    return 0;
}
```

```text
===== 기본 인자 승격 격자 — 넘긴 타입 5 × 꺼낸 타입 2 × 컴파일러 2 × 최적화 2 (-std=c17 -Wall -Wextra -pedantic) (exit=0) =====
넘긴 타입 → 꺼낸 타입          | gcc -O0             | gcc -O2             | clang -O0           | clang -O2
char → char                    | W1 exit=132 같나=-  | W1 exit=132 같나=-  | W1 exit=0 같나=1    | W1 exit=0 같나=1
char → int                     | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1
unsigned char → unsigned char  | W1 exit=132 같나=-  | W1 exit=132 같나=-  | W1 exit=0 같나=1    | W1 exit=0 같나=1
unsigned char → int            | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1
short → short                  | W1 exit=132 같나=-  | W1 exit=132 같나=-  | W1 exit=0 같나=1    | W1 exit=0 같나=1
short → int                    | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1
_Bool → _Bool                  | W1 exit=132 같나=-  | W1 exit=132 같나=-  | W1 exit=0 같나=1    | W1 exit=0 같나=1
_Bool → int                    | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1
float → float                  | W1 exit=132 같나=-  | W1 exit=132 같나=-  | W1 exit=0 같나=0    | W1 exit=0 같나=0
float → double                 | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1    | W0 exit=0 같나=1
(W = 경고 수 · exit = 실행 종료 코드 · 같나 = 꺼낸 값이 넘긴 값과 같으면 1, 실행이 죽으면 -)
두 컴파일러가 갈린 줄 5 / 10
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s36b.c -o /dev/null (cc exit=0) =====
s36b.c: In function ‘same’:
s36b.c:13:16: warning: ‘char’ is promoted to ‘int’ when passed through ‘...’
   13 |     PASS got = (PASS)va_arg(ap, PULL);
      |                ^
s36b.c:13:16: note: (so you should pass ‘int’ not ‘char’ to ‘va_arg’)
s36b.c:13:16: note: if this code is reached, the program will abort
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s36b.c -o /dev/null (cc exit=0) =====
s36b.c:13:33: warning: second argument to 'va_arg' is of promotable type 'char'; this va_arg has undefined behavior because arguments will be promoted to 'int' [-Wvarargs]
   13 |     PASS got = (PASS)va_arg(ap, PULL);
      |                                 ^~~~
s36b.c:6:14: note: expanded from macro 'PULL'
    6 | #define PULL char
      |              ^~~~
/usr/lib/llvm-18/lib/clang/18/include/__stdarg_va_arg.h:20:47: note: expanded from macro 'va_arg'
   20 | #define va_arg(ap, type) __builtin_va_arg(ap, type)
      |                                               ^~~~
1 warning generated.
```

그림 해설 (한 단계씩):

- ★★★ **승격 후 타입으로 꺼낸 다섯 줄은 모든 칸이 같다** — `W0 exit=0 같나=1`. `char`·`unsigned char`·`short`·`_Bool` → **`int`**, `float` → **`double`** 로 꺼내면 된다.
- ★★★ **승격 전 타입으로 꺼낸 다섯 줄에서 두 컴파일러가 갈렸다 — 갈린 줄 5 / 10.** gcc 는 **다섯 다 경고 1 + `exit=132`**(심은 `ud2`), clang 은 **다섯 다 경고 1 + `exit=0`**.
- ★★★ **clang 의 네 칸은 「같나 = 1」** 이다 — `char`·`unsigned char`·`short`·`_Bool` 은 **`int` 의 아래쪽 바이트를 읽으면 우연히 같은 값**이 나온다. **UB 가 맞아 보이는 가장 위험한 칸**이다. `float` 만 `같나=0`(비트 배치가 달라서).
- ★★ **`-O0`/`-O2` 는 한 칸도 안 움직였다** — 여기서 갈리는 것은 **최적화가 아니라 컴파일러**다.
- ★ [30번 형제](../30-initialization-rules-and-indeterminate-values/)의 `_Bool` 에 바이트 `2` 와 닮은 자리다 — 거기는 **표현이 틀린 값**을 읽었고, 여기는 **타입이 틀린 자리**를 읽는다. 둘 다 **UB 의 한 판 결과**다.

★★★ **여기에 처방은 없다 — 대신 규칙이 있다.** 「clang 에서 `char` 로 받아도 맞더라」는 **판 결과**이고, 표준의 선은 **「승격된 타입으로 꺼낸다」** 한 줄이다(부호만 다른 정수는 예외로 허락).

### (3) ★★ `printf("%d", 3.0)` — 컴파일러가 아는 함수와 모르는 함수

**언제 쓰나** — 로그 함수를 `printf` 처럼 만들었을 때.

```c
/* s36c.c */
#include <stdarg.h>
#include <stdio.h>

static void my_log(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vprintf(fmt, ap);
    va_end(ap);
}

__attribute__((format(printf, 1, 2)))
static void my_log_checked(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vprintf(fmt, ap);
    va_end(ap);
}

int main(void) {
    printf("printf         : %d\n", 3.0);
    my_log("my_log         : %d\n", 3.0);
    my_log_checked("my_log_checked : %d\n", 3.0);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s36c.c -o /dev/null (cc exit=0) =====
s36c.c: In function ‘main’:
s36c.c:20:31: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘double’ [-Wformat=]
   20 |     printf("printf         : %d\n", 3.0);
      |                              ~^     ~~~
      |                               |     |
      |                               int   double
      |                              %f
s36c.c:22:39: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘double’ [-Wformat=]
   22 |     my_log_checked("my_log_checked : %d\n", 3.0);
      |                                      ~^     ~~~
      |                                       |     |
      |                                       int   double
      |                                      %f
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s36c.c -o /dev/null (cc exit=0) =====
s36c.c:20:37: warning: format specifies type 'int' but the argument has type 'double' [-Wformat]
   20 |     printf("printf         : %d\n", 3.0);
      |                              ~~     ^~~
      |                              %f
s36c.c:22:45: warning: format specifies type 'int' but the argument has type 'double' [-Wformat]
   22 |     my_log_checked("my_log_checked : %d\n", 3.0);
      |                                      ~~     ^~~
      |                                      %f
2 warnings generated.
```

```c
/* s36c2.c */
#include <stdio.h>

int main(void) {
    printf("%d\n", 3.0);
    return 0;
}
```

```text
===== printf("%d\n", 3.0) 을 10 번 — 컴파일러 2 (-std=c17, 경고 무시) (exit=0) =====
gcc    10 번 돌려 3 이 찍힌 판 0 / 10
clang  10 번 돌려 3 이 찍힌 판 0 / 10
```

- ★★★ **`printf` 줄은 두 컴파일러 다 `-Wformat` 경고** — `%d` 는 `int` 를 기대하는데 인자가 `double` 이다. **컴파일러가 `printf` 라는 함수의 형식 규칙을 알기** 때문이다.
- ★★★ **`my_log` 줄은 경고 0건** — `...` 뒤의 타입을 **아무도 모른다.** 같은 실수가 **조용히 통과**한다.
- ★★★ **`my_log_checked` 는 경고가 되살아난다** — `__attribute__((format(printf, 1, 2)))` 가 「**1번 인자가 `printf` 형식 문자열이고, 2번부터가 그 대상**」이라고 컴파일러에 알렸다.
- ★★ **실행하면 `3` 은 한 판도 안 찍힌다** — 10 번 돌려 **`0 / 10`**(두 컴파일러). `double` 은 **다른 레지스터**(`xmm0`)로 넘어가서 `%d` 가 읽는 자리에는 **다른 값**이 있다. 그 값 자체는 **흔들리므로 싣지 않았다.**

### (4) ★★ 개수를 모르는 문제 — 센티널과 개수 인자

**언제 쓰나** — 가변 인자 함수가 **어디서 멈출지** 정할 때.

```c
/* s36d.c */
#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>

__attribute__((sentinel))
static int count_until_null(const char *first, ...) {
    va_list ap;
    int n = 0;
    va_start(ap, first);
    for (const char *s = first; s != NULL; s = va_arg(ap, const char *)) n++;
    va_end(ap);
    return n;
}

static int sum_n(int n, ...) {
    va_list ap;
    int total = 0;
    va_start(ap, n);
    for (int i = 0; i < n; i++) total += va_arg(ap, int);
    va_end(ap);
    return total;
}

int main(void) {
    printf("%d\n", count_until_null("a", "b", "c", (char *)NULL));
    printf("%d\n", count_until_null("a", "b", "c"));
    printf("%d\n", sum_n(3, 10, 20, 30));
    printf("%d\n", sum_n(8, 10, 20, 30));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s36d.c -o /dev/null (cc exit=0) =====
s36d.c: In function ‘main’:
s36d.c:26:5: warning: missing sentinel in function call [-Wformat=]
   26 |     printf("%d\n", count_until_null("a", "b", "c"));
      |     ^~~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s36d.c -o /dev/null (cc exit=0) =====
s36d.c:26:50: warning: missing sentinel in function call [-Wsentinel]
   26 |     printf("%d\n", count_until_null("a", "b", "c"));
      |                                                  ^
      |                                                  , NULL
s36d.c:6:12: note: function has been explicitly marked sentinel here
    5 | __attribute__((sentinel))
      |                ~~~~~~~~
    6 | static int count_until_null(const char *first, ...) {
      |            ^
1 warning generated.
```

- ★★★ **`sentinel` 속성이 있으면 끝의 `NULL` 이 빠진 호출을 잡는다** — gcc 는 `-Wformat` 묶음으로, clang 은 `-Wsentinel` 로. clang 은 **`, NULL` 을 넣으라고** 고칠 자리까지 보여 준다.
- ★★★ **개수 인자(`sum_n(8, 10, 20, 30)`)는 아무도 못 잡는다** — 두 컴파일러 **0건**. 개수와 실제 인자 수를 견줄 방법이 **선언에 없다.**
- ★ 이 소스는 **컴파일만** 했다 — 뒤의 두 호출은 **UB**(다음 인자가 없는데 `va_arg`)라 실행 결과를 싣지 않는다. 실행 쪽은 (5)가 **sanitizer 로만** 묻는다.

### (5) ★★ 없는 인자를 읽으면 — sanitizer 탐침

**언제 쓰나** — 「ASan 이 가변 인자 과잉 읽기를 잡겠지」라고 생각할 때.

```c
/* s36e.c */
#include <stdarg.h>
#include <stdio.h>

static int sum_n(int n, ...) {
    va_list ap;
    unsigned total = 0;                  /* 쓰레기 값을 더해도 넘침(UB)이 안 나게 unsigned 로 */
    va_start(ap, n);
    for (int i = 0; i < n; i++) total += (unsigned)va_arg(ap, int);
    va_end(ap);
    return (int)total;
}

int main(void) {
    fprintf(stderr, "[1] sum_n(3, ...) == 60 ? %d\n", sum_n(3, 10, 20, 30) == 60);
    volatile int got = sum_n(8, 10, 20, 30);  /* 셋을 넘기고 여덟을 읽는다 */
    (void)got;
    fprintf(stderr, "[2] after sum_n(8, ...)\n");
    return 0;
}
```

```text
===== 셋을 넘기고 여덟을 va_arg 로 — sanitizer 탐침 (-std=c17 -O0 -g) (exit=0) =====
gcc    address    run exit=0 · 리포트 0줄 | [1] sum_n(3, ...) == 60 ? 1|[2] after sum_n(8, ...)|
gcc    undefined  run exit=0 · 리포트 0줄 | [1] sum_n(3, ...) == 60 ? 1|[2] after sum_n(8, ...)|
clang  address    run exit=0 · 리포트 0줄 | [1] sum_n(3, ...) == 60 ? 1|[2] after sum_n(8, ...)|
clang  undefined  run exit=0 · 리포트 0줄 | [1] sum_n(3, ...) == 60 ? 1|[2] after sum_n(8, ...)|
clang  memory     run exit=0 · 리포트 0줄 | [1] sum_n(3, ...) == 60 ? 1|[2] after sum_n(8, ...)|
답한 칸 0 / 5
```

- ★★★ **답한 칸 0 / 5** — gcc ASan·UBSan, clang ASan·UBSan·MSan 이 **전부 침묵**하고 `exit=0` 으로 끝났다.
- ★★ **이유(이 판의 x86-64 호출 규약)** — `va_arg` 가 읽는 곳은 **함수가 스스로 만든 레지스터 저장 영역과 스택**이라, 넘치게 읽어도 **ASan 의 경계 안쪽**이다. ★ 이 이유는 **호출 규약의 설명이고 도구 소스로 확인하지 않았다** — 결론은 「**이 판의 다섯 도구가 침묵했다**」까지다.
- ★ 표준은 **「다음 인자가 없으면 UB」** 라고 적는다 — 도구가 못 봐도 UB 다.
- ★★ **합을 `unsigned` 로 더한 이유** — 처음 판은 `int` 로 더했더니 **쓰레기 값끼리의 덧셈이 넘쳐** UBSan 이 **`signed integer overflow`** 를 **실행마다 났다 안 났다** 했다(재대조에서 gcc·clang 칸이 번갈아 갈렸다). 그것은 과잉 읽기가 아니라 **엉뚱한 UB 에 대한 답**이라, 탐침을 과잉 읽기 하나로 고립시켰다.

### (6) ★★ `va_list` 를 두 번 쓰기 — `va_copy`

**언제 쓰나** — 가변 인자를 **두 번 훑어야** 할 때(길이를 세고 나서 복사하기 등).

```c
/* s36f.c */
#include <stdarg.h>
#include <stdio.h>

static int sum(int n, va_list ap) {
    int t = 0;
    for (int i = 0; i < n; i++) t += va_arg(ap, int);
    return t;
}

static void twice_plain(int n, ...) {
    va_list ap;
    va_start(ap, n);
    int a = sum(n, ap);
    int b = sum(n, ap);                   /* 같은 ap 를 한 번 더 */
    va_end(ap);
    printf("twice_plain : first == 60 ? %d   second == 60 ? %d\n", a == 60, b == 60);
}

static void twice_copy(int n, ...) {
    va_list ap, ap2;
    va_start(ap, n);
    va_copy(ap2, ap);
    int a = sum(n, ap);
    int b = sum(n, ap2);
    va_end(ap2);
    va_end(ap);
    printf("twice_copy  : first == 60 ? %d   second == 60 ? %d\n", a == 60, b == 60);
}

int main(void) {
    printf("sizeof(va_list) = %zu\n", sizeof(va_list));
    twice_plain(3, 10, 20, 30);
    twice_copy(3, 10, 20, 30);
    return 0;
}
```

```text
===== va_list 를 두 번 쓰기 — 컴파일러 2 × 최적화 2 (exit=0) =====
--- gcc -O0
sizeof(va_list) = 24
twice_plain : first == 60 ? 1   second == 60 ? 0
twice_copy  : first == 60 ? 1   second == 60 ? 1
--- gcc -O2
sizeof(va_list) = 24
twice_plain : first == 60 ? 1   second == 60 ? 0
twice_copy  : first == 60 ? 1   second == 60 ? 1
--- clang -O0
sizeof(va_list) = 24
twice_plain : first == 60 ? 1   second == 60 ? 0
twice_copy  : first == 60 ? 1   second == 60 ? 1
--- clang -O2
sizeof(va_list) = 24
twice_plain : first == 60 ? 1   second == 60 ? 0
twice_copy  : first == 60 ? 1   second == 60 ? 1
```

- ★★★ **`twice_plain` 의 두 번째는 네 벌 다 틀린다**(`second == 60 ? 0`) — `sum(n, ap)` 가 **`ap` 를 소비**했다. 표준은 **넘긴 함수가 `va_arg` 를 불렀다면 부른 쪽의 `ap` 는 불확정**이라고 적는다 — **두 번째 사용은 UB** 다.
- ★★★ **`va_copy` 로 사본을 만들면 네 벌 다 맞는다.**

```text
   va_list ap;   (이 판: 24 바이트짜리 배열 타입)

   twice_plain:  sum(n, ap)  ->  배열이 포인터로 감쇠 -> sum 이 원본 ap 를 앞으로 민다
                 sum(n, ap)  ->  이미 끝까지 간 ap 에서 다시 읽는다   (표준: 불확정 — UB)

   twice_copy:   va_copy(ap2, ap)  ->  sum(n, ap) 가 ap 를 민다
                                       sum(n, ap2) 는 사본에서 처음부터 읽는다
```

- ★★ **`sizeof(va_list) = 24`** — 이 판에서 `va_list` 는 **24바이트짜리 배열 타입**처럼 동작한다(그래서 함수에 넘기면 **포인터로 감쇠해 원본이 소비된다**). ★ **표준은 `va_list` 의 정체를 정하지 않는다** — 다른 ABI 에서는 다르다(★ 던지지 않았다).

### (7) ★ `va_end` 를 안 부르면 — 제5의 상태

**언제 쓰나** — 「`va_end` 는 빼도 아무 일 없더라」를 물을 때.

```c
/* s36g.c */
#include <stdarg.h>

int with_end(int n, ...) {
    va_list ap;
    va_start(ap, n);
    int v = va_arg(ap, int);
    va_end(ap);
    return v;
}

int without_end(int n, ...) {
    va_list ap;
    va_start(ap, n);
    int v = va_arg(ap, int);
    return v;
}
```

```text
===== va_end 가 있는 함수와 없는 함수 — 어셈블리 몸통 비교 (exit=0) =====
gcc    -O0  with_end 56 줄 · without_end 56 줄 · 다른 줄 0
gcc    -O2  with_end 19 줄 · without_end 19 줄 · 다른 줄 0
clang  -O0  with_end 56 줄 · without_end 56 줄 · 다른 줄 0
clang  -O2  with_end 39 줄 · without_end 39 줄 · 다른 줄 0
(지역 레이블 번호 .L숫자 는 지우고 견줬다)
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s36g.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand | sed -n '/^with_end:/,/^without_end:/p' | grep -v '^without_end:' (cc exit=0) =====
with_end:
        endbr64
        sub     rsp, 88
        mov     QWORD PTR 40[rsp], rsi
        mov     rax, QWORD PTR fs:40
        mov     QWORD PTR 24[rsp], rax
        xor     eax, eax
        lea     rax, 96[rsp]
        mov     DWORD PTR [rsp], 8
        mov     QWORD PTR 8[rsp], rax
        lea     rax, 32[rsp]
        mov     QWORD PTR 16[rsp], rax
        mov     eax, DWORD PTR 40[rsp]
        mov     rdx, QWORD PTR 24[rsp]
        sub     rdx, QWORD PTR fs:40
        jne     .L7
        add     rsp, 88
        ret
.L7:
        call    __stack_chk_fail@PLT
```

- ★★★ **네 벌 다 「다른 줄 0」** — `va_end` 가 있는 함수와 없는 함수의 어셈블리가 **한 글자도 같다**(지역 레이블 번호만 지우고 견줬다). **이 판에서 `va_end` 는 명령을 하나도 만들지 않는다.**
- ★★★ **그래도 표준은 「`va_end` 없이 돌아가면 UB」** 라고 적는다 — 이 판에서 아무 일이 없는 것은 **관찰**이다. **다른 ABI 에서 `va_start` 가 자원을 잡는다면** `va_end` 가 그것을 놓는 자리다.
- ★ **실행으로는 이 질문에 답할 수 없었다** — 「아무 일도 안 났다」는 **괜찮다는 뜻도, 못 봤다는 뜻도** 될 수 있다. **어셈블리로 창을 바꿔** 「명령 0개」를 봤다.

### (8) ★★ C23 의 두 변경 — `va_start(ap)` 와 `f(...)`

**언제 쓰나** — C23 코드에서 `va_start(ap)` 만 쓰거나, **이름 있는 매개변수 없이** `...` 만 받을 때.

```c
/* s36h0.c */
#include <stdarg.h>

int first(int n, ...) {
    va_list ap;
    va_start(ap, n);
    int v = va_arg(ap, int);
    va_end(ap);
    return v + n;
}
```

```c
/* s36h1.c */
#include <stdarg.h>

int first(int n, ...) {
    va_list ap;
    va_start(ap);                 /* 두 번째 인자를 안 적었다 */
    int v = va_arg(ap, int);
    va_end(ap);
    return v + n;
}
```

```c
/* s36h2.c */
#include <stdarg.h>

int only_dots(...) {              /* 이름 있는 매개변수가 없다 */
    va_list ap;
    va_start(ap);
    int v = va_arg(ap, int);
    va_end(ap);
    return v;
}
```

```text
===== C23 의 두 변경 — 파일 3 × 컴파일러 3 × 판 2 (exit=0) =====
파일      컴파일러 -std=c17 -pedantic     | -std=c2x -pedantic
s36h0.c   gcc-12   exit=0 경고 0 에러 0   | exit=0 경고 0 에러 0
s36h0.c   gcc      exit=0 경고 0 에러 0   | exit=0 경고 0 에러 0
s36h0.c   clang    exit=0 경고 0 에러 0   | exit=0 경고 0 에러 0
s36h1.c   gcc-12   exit=1 경고 0 에러 2   | exit=1 경고 0 에러 2
s36h1.c   gcc      exit=1 경고 0 에러 2   | exit=0 경고 0 에러 0
s36h1.c   clang    exit=1 경고 1 에러 2   | exit=0 경고 1 에러 0
s36h2.c   gcc-12   exit=1 경고 0 에러 3   | exit=1 경고 0 에러 3
s36h2.c   gcc      exit=1 경고 1 에러 2   | exit=0 경고 0 에러 0
s36h2.c   clang    exit=1 경고 1 에러 3   | exit=0 경고 1 에러 0
```

```text
                     va_start(ap)            int only_dots(...)
                     --------------------    --------------------
   C89 ~ C17         에러 (인자 둘이 필요)    에러 (이름 있는 매개변수가 필요)
   C23               된다                     된다
   이 판             gcc 13 · clang 은 C23 에서 받는다 — gcc-12 는 C23 에서도 에러
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s36h1.c -o /dev/null (cc exit=1) =====
s36h1.c: In function ‘first’:
s36h1.c:5:16: error: macro "va_start" requires 2 arguments, but only 1 given
    5 |     va_start(ap);                 /* 두 번째 인자를 안 적었다 */
      |                ^
In file included from s36h1.c:1:
/usr/lib/gcc/x86_64-linux-gnu/13/include/stdarg.h:50: note: macro "va_start" defined here
   50 | #define va_start(v,l)   __builtin_va_start(v,l)
      | 
s36h1.c:5:5: error: ‘va_start’ undeclared (first use in this function)
    5 |     va_start(ap);                 /* 두 번째 인자를 안 적었다 */
      |     ^~~~~~~~
s36h1.c:5:5: note: each undeclared identifier is reported only once for each function it appears in
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic -c s36h1.c -o /dev/null (cc exit=0) =====
```

```text
===== clang -std=c2x -Wall -Wextra -pedantic -c s36h1.c -o /dev/null (cc exit=0) =====
s36h1.c:5:16: warning: must specify at least one argument for '...' parameter of variadic macro [-Wgnu-zero-variadic-macro-arguments]
    5 |     va_start(ap);                 /* 두 번째 인자를 안 적었다 */
      |                ^
/usr/lib/llvm-18/lib/clang/18/include/__stdarg_va_arg.h:14:9: note: macro 'va_start' defined here
   14 | #define va_start(ap, ...) __builtin_va_start(ap, 0)
      |         ^
1 warning generated.
```

```text
===== grep -n 'va_start' /usr/lib/llvm-18/lib/clang/18/include/__stdarg_va_arg.h (exit=0) =====
1:/*===---- __stdarg_va_arg.h - Definitions of va_start, va_arg, va_end-------===
13:/* C23 does not require the second parameter for va_start. */
14:#define va_start(ap, ...) __builtin_va_start(ap, 0)
17:#define va_start(ap, param) __builtin_va_start(ap, param)
```

```text
===== gcc-12 -std=c2x -Wall -Wextra -pedantic -c s36h2.c -o /dev/null (cc exit=1) =====
s36h2.c:3:15: error: ISO C requires a named argument before ‘...’
    3 | int only_dots(...) {              /* 이름 있는 매개변수가 없다 */
      |               ^~~
s36h2.c: In function ‘only_dots’:
s36h2.c:5:16: error: macro "va_start" requires 2 arguments, but only 1 given
    5 |     va_start(ap);
      |                ^
In file included from s36h2.c:1:
/usr/lib/gcc/x86_64-linux-gnu/12/include/stdarg.h:47: note: macro "va_start" defined here
   47 | #define va_start(v,l)   __builtin_va_start(v,l)
      | 
s36h2.c:5:5: error: ‘va_start’ undeclared (first use in this function)
    5 |     va_start(ap);
      |     ^~~~~~~~
s36h2.c:5:5: note: each undeclared identifier is reported only once for each function it appears in
```

그림 해설 (한 단계씩):

- ★★★ **gcc 13 과 clang 18 은 `-std=c2x` 에서 둘 다 받는다** — `va_start(ap)` 도, `only_dots(...)` 도 `exit=0`. **C17 에서는 둘 다 에러**다.
- ★★★ **gcc-12 는 C23 모드에서도 둘 다 에러**다 — 그 판의 `stdarg.h` 는 `va_start(v,l)` **두 인자 매크로**뿐이다. 34편의 빈 괄호처럼 **컴파일러 판이 한 축**이다.
- ★★★ **clang 은 C23 에서 받으면서 `-pedantic` 경고를 낸다** — `must specify at least one argument for '...' parameter of variadic macro [-Wgnu-zero-variadic-macro-arguments]`. clang 18 의 헤더가 C23 판을 `va_start(ap, ...)` 로 정의했고, **C23 에서는 합법인 「`...` 에 인자 0개」를** `-pedantic` 이 **옛 판의 기준으로** 짚었다. **진단이 판을 틀리게 읽은 자리**다(종료 코드 `0` 이 근거다).
- ★ **gcc 13 은 같은 소스에 0건**이다 — 두 컴파일러가 갈린 자리.

### (9) ★ Go 의 `...T` 는 슬라이스다 — 대비

**언제 쓰나** — 「다른 언어의 가변 인자에는 타입이 있나」를 볼 때.

```go
// s36go.go
package main

import "fmt"

func sum(xs ...float32) float32 {
    var t float32
    for _, x := range xs {
        t += x
    }
    return t
}

func main() {
    fmt.Printf("%T %v\n", []float32{1.5, 2.5}, sum(1.5, 2.5))
    f := sum
    fmt.Printf("%T\n", f)
}
```

```text
===== go version (exit=0) =====
go version go1.27.1 linux/amd64
```

```text
===== go run s36go.go (exit=0) =====
[]float32 4
func(...float32) float32
```

- ★★ **Go 의 `xs ...float32` 는 함수 안에서 `[]float32`** 다 — 타입이 **선언에 남고**, 개수는 **`len(xs)`** 로 안다. `float32` 가 **승격되지 않는다**(합이 `4`).
- ★ **함수 값의 타입도 `func(...float32) float32`** — 가변 인자가 **타입의 일부**다. C 의 `...` 는 타입에 「**무엇이든**」만 남긴다. [Go 12번 형제](../../../go/syntax/12-functions-multiple-returns-named-results-and-variadics/)가 정본이다.
- ★ **C++ 의 가변 인자 템플릿**은 타입을 **컴파일 때 전부** 안다 — C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **34번**(아직 폴더가 없다).

## 문법 — 형태와 규칙

### 형태

(2)의 `s36b.c`(승격 후 타입 판) · (6)의 `s36f.c` · (8)의 `s36h0.c` 가 이 절의 **실제로 컴파일되는 형태**다. 쓰는 자리를 한 줄씩:

| 쓴 꼴 | 뜻 | 판 |
|---|---|---|
| `int f(int n, ...);` | 가변 인자 선언 — `...` 앞에 이름 있는 매개변수 | C89 부터 |
| `va_list ap; va_start(ap, n);` | 순회 시작 — 두 번째 인자는 **마지막 이름 있는 매개변수** | C89 부터 |
| `va_arg(ap, int)` | 다음 인자 — ★★★ **승격된 타입으로** | C89 부터 |
| `va_end(ap);` | 순회 끝 — 돌아가기 전에 반드시 | C89 부터 |
| `va_copy(ap2, ap);` | 사본 — 두 번 훑을 때 | C99 부터 |
| `va_start(ap);` | ★ 두 번째 인자 생략 | **C23** |
| `int f(...);` | ★ 이름 있는 매개변수 없음 | **C23** |
| `__attribute__((format(printf, 1, 2)))` | 형식 문자열 검사 되살리기 | ★ 구현 확장 |
| `__attribute__((sentinel))` | 끝의 `NULL` 검사 | ★ 구현 확장 |

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 종료 코드 | 층 | 어느 절 |
|---|---|---|---|
| `va_arg(ap, float)` | 두 컴파일러 경고 · ★ **`cc exit=0`** · gcc `run exit=132` · clang `0` | ★★★ UB | (1)·(2) |
| `va_arg(ap, char)`·`short`·`_Bool` | 같음 · ★ **clang 은 「같나 = 1」** | ★★★ UB | (2) |
| 내 가변 인자 함수에 틀린 형식 | **경고 0**(속성 없이) | ★★★ UB | (3) |
| 끝의 `NULL` 을 빠뜨린 호출 | 속성 있으면 경고 · 없으면 0 | ★★★ UB(다음 인자가 없는 `va_arg`) | (4) |
| 개수 인자보다 적게 넘기기 | **경고 0 · sanitizer 0 / 5** | ★★★ UB | (4)·(5) |
| 넘긴 `ap` 를 다시 쓰기 | 경고 0 · 두 번째가 틀림 | ★★★ UB(불확정) | (6) |
| `va_end` 빠뜨리기 | 경고 0 · **명령 차이 0** | ★★ UB(이 판에서는 관찰상 무해) | (7) |
| C17 에서 `va_start(ap)` · `f(...)` | **에러** | 판 경계(C23 부터) | (8) |

### 규칙 불릿

- ★★★ **`...` 뒤의 인자는 기본 인자 승격을 거친다** — 정수 승격 + `float` → `double`.
- ★★★ **`va_arg` 는 승격된 타입으로 꺼낸다** — 아니면 UB. 예외는 **부호만 다른 정수**(값이 둘 다에 들 때) · `void *` 와 문자 포인터 등.
- ★★★ **개수와 타입은 선언에 없다** — 개수 인자 · 센티널 · 형식 문자열로 **따로** 알려야 한다.
- ★★ **컴파일러는 `printf` 만 안다** — 내 함수는 `format` 속성으로 알려 준다.
- ★★ **다른 함수에 넘긴 `ap` 는 불확정** — 두 번 훑으려면 `va_copy`.
- ★★ **`va_end` 는 표준의 의무**다 — 이 판에서 명령이 0개인 것은 관찰이다.
- ★ **C23** — `va_start(ap)` · `f(...)`.

## 어디서 틀리나

### 1. ★★★ 「`char` 를 넘겼으니 `va_arg(ap, char)`」

**UB** 다((2)). gcc 판은 **죽고**, clang 판은 **맞아 보인다** — clang 에서만 시험하면 **통과한 테스트가 가장 위험한 근거**가 된다.

### 2. ★★★ 「경고가 나도 빌드는 되니까」

**두 컴파일러 다 `cc exit=0`** 이었다((1)). gcc 의 경고는 「**이 코드에 닿으면 중단된다**」는 예고였고, 실제로 **`132`** 로 죽었다.

### 3. ★★★ 「`printf` 처럼 만들었으니 형식 검사도 되겠지」

**내 함수는 경고 0건**이다((3)). `format` 속성을 붙여야 되살아난다.

### 4. ★★ 「sanitizer 로 돌렸으니 가변 인자는 안전하다」

**탐침 13칸((1)의 8 · (5)의 5)에서 리포트 0줄**이었다. 가변 인자의 UB 는 **sanitizer 의 창 밖**이다(이 판).

### 5. ★★ 「`va_list` 를 함수에 넘기고 나서 다시 쓰면 된다」

**넘긴 쪽의 `ap` 는 불확정**이다((6)) — 이 판에서는 **소비된 상태**였다. `va_copy`.

### 6. ★ 「`va_end` 는 빼도 된다」

**이 판에서 명령 0개**인 것은 관찰이고, 표준은 **UB** 로 둔다((7)).

### 7. ★ 「`va_start(ap)` 는 되는 문법이다」

**C23 에서만**, 그리고 **gcc 13 이상 · clang** 에서만 됐다((8)). gcc-12 는 C23 모드에서도 에러.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「UB」 칸이 본체**다 — 가변 인자의 사고는 거의 전부 **`va_arg` 의 불일치**다.\
★★★ **「표준」 칸이 그 경계를 긋는다** — 승격 규칙 · 예외 넷 · `va_copy`·`va_end` 의 의무.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | ★★★ **기본 인자 승격** · **`va_arg` 가 승격된 타입과 호환되어야 한다**(예외 넷) · 넘긴 `ap` 는 불확정 · `va_end` 의무 · `va_copy`(C99) · ★ C23 의 `va_start(ap, ...)` · `f(...)` | 격자의 「승격 후」 다섯 줄 · `va_copy` 네 벌 · 판 격자 |
| **조건부 표준** | 매크로가 정의될 때만 | ★ **해당 없음** | — |
| ★★ **구현 정의** | 문서화 의무가 있다(또는 도구의 선택) | ★★ **`va_list` 의 정체**(이 판: 24바이트 · 배열처럼) · 호출 규약(`al` · 레지스터 저장 영역) · ★ **UB 를 만난 컴파일러의 선택**(gcc `ud2` · clang 값) · `format`·`sentinel` 속성 | `sizeof(va_list) = 24` · 어셈블리 · 격자 |
| **미명시** | 몇 가지 중 하나 | ★ **해당 없음**(이 편이 던진 것 중에는) | — |
| ★★★ **UB** | 아무 일이나 | ★★★ **승격 전 타입으로 `va_arg`** · 형식 불일치 · **없는 인자 읽기**(센티널 누락 · 개수 초과) · 넘긴 `ap` 재사용 · `va_end` 누락 | `132` / `같나=1` · `0 / 10` · 0 / 5 · `second == 60 ? 0` · 명령 차이 0 |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★ **clang 18 이 C23 에서 합법인 `va_start(ap)` 에 `-pedantic` 경고**를 낸다 — **도구가 틀린 말을 한 자리**다(종료 코드 `0`) |
| ★★ **구현 정의** | ★ `va_list` 가 배열처럼 동작해 **넘기면 원본이 소비된다**는 것을 말해 주는 경고가 없다 |
| ★★★ **UB** | ★★★ **내 가변 인자 함수의 형식 불일치 · 개수 초과는 경고 0** · ★★★ **sanitizer 탐침 13칸 리포트 0줄** · ★★ **`va_list` 재사용 · `va_end` 누락도 경고 0** |
| ★★ **(층을 가로지름)** | ★ **「종료 코드 0인데 ill-formed」는 이 편에 새 항목이 없다** — 이 편의 사고는 전부 **적격한 프로그램의 UB** 다. ★★ 대신 **「종료 코드 0인데 UB」가 가장 많다**(금지 사례 표의 UB 일곱 줄 — 전부 `cc exit=0`) |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **`va_arg` 불일치를 잡는 것은 컴파일러 경고뿐**이었다 — 그것도 **꺼내는 타입이 승격되는 타입일 때만**(형식·개수는 속성이 있어야).
  - ★★★ **gcc 의 `ud2` 는 sanitizer 보다 강했다** — sanitizer 가 침묵한 칸에서 **컴파일러가 심은 명령**이 프로그램을 멈췄다. 하지만 그것은 **gcc 의 선택**이지 보장이 아니다.
  - ★★ **clang 의 「같나 = 1」이 가장 위험하다** — 도구도 침묵하고 값도 맞는다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| `float`·`char` 인자 받기 | ★★★ **`va_arg(ap, double)` · `va_arg(ap, int)` 로 꺼내 캐스트** | `va_arg(ap, float)` · `va_arg(ap, char)` |
| 로그 함수 | ★★★ **`format(printf, …)` 속성** + `vprintf` | 속성 없는 `...` |
| 끝을 알리기 | ★★ **센티널 + `sentinel` 속성** 또는 **개수 인자**(검사 없음을 알고) | 아무 표시 없이 |
| 타입이 섞인 인자 | ★★ **가변 인자 대신 구조체 배열**이나 여러 함수 | 형식 문자열을 스스로 발명 |
| 두 번 훑기 | ★★ **`va_copy`** | 넘긴 `ap` 재사용 |
| 끝내기 | ★ **`va_end` 를 반드시** | 「이 판에서 무해하니까」 생략 |
| C23 코드 | ★ `va_start(ap)` — **gcc 13 이상 · clang** | gcc-12 |

판단 규칙 두 줄.

- ★★★ **`...` 뒤로 넘어간 값은 「승격된 타입」으로만 존재한다** — 꺼낼 때 그 타입을 쓴다.
- ★★ **타입과 개수를 컴파일러가 알 수 있게 만들 수 없다면**(속성·센티널) 가변 인자를 쓰지 않는 쪽이 낫다 — 도구가 도와주지 않는다.

## 핵심 문장

- ★★★ **`...` 뒤의 인자는 기본 인자 승격을 거친다** — `char`·`short`·`_Bool` → `int`, `float` → `double`. 34편의 빈 괄호 호출과 같은 규칙이다.
- ★★★ **`va_arg(ap, float)` 는 두 컴파일러 다 경고하고 `cc exit=0` — gcc 는 `ud2` 를 심어 `run exit=132` 로 죽이고, clang 은 `0` 을 낸다.**
- ★★★ **승격 격자에서 승격 전 타입으로 꺼낸 다섯 줄은 두 컴파일러가 전부 갈렸고(5 / 10), clang 의 정수 넷은 값이 맞아 보였다.**
- ★★★ **`printf` 는 `-Wformat` 이 잡고 내 함수는 못 잡는다 — `format(printf, 1, 2)` 속성이 그 검사를 되살린다.**
- ★★ **센티널 누락은 `sentinel` 속성으로 잡히고, 개수 초과는 아무도 못 잡았다 — sanitizer 0 / 5.**
- ★★ **넘긴 `va_list` 는 소비된다 — `va_copy` 로 사본을 만든다.** 이 판의 `va_list` 는 24바이트.
- ★★ **이 판에서 `va_end` 는 명령 0개지만 빼면 UB 다.**
- ★ **C23 은 `va_start(ap)` 와 `f(...)` 를 허락했다** — gcc 13·clang 은 받고 gcc-12 는 못 받았다. clang 은 받으면서 `-pedantic` 경고를 냈다.

## 관련 자료

- [34번 형제 — 함수 선언·정의·프로토타입](../34-function-declarations-definitions-and-prototypes/) — ★★★ **같은 사슬.** 빈 괄호 호출의 승격과 `al` 채우기가 이 편의 가변 인자 호출과 **같은 번역**이다.
- [03번 형제 — 정수 승격](../03-integer-promotion-and-usual-arithmetic-conversions/) · [04번 형제 — 부동소수점 변환](../04-floating-point-types-and-conversions/) — ★★ **선행.** 승격 규칙의 정본.
- [30번 형제 — 초기화 규칙과 불확정 값](../30-initialization-rules-and-indeterminate-values/) — ★ `_Bool` 에 바이트 `2` — 「틀린 자리를 읽은 UB」의 이웃.
- 목록의 **47번 주제** — `printf` 계열 형식 문자열의 정본.
- 목록의 **58번 주제** — sanitizer 사용법의 정본.
- ★ **Go 갈래** — [Go 12번 형제](../../../go/syntax/12-functions-multiple-returns-named-results-and-variadics/). **가변 인자가 슬라이스**인 언어.
- ★ C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **34번** — 가변 인자 템플릿(C 의 `<stdarg.h>` 를 대신한다고 그 목록이 적었다).

## 용어 풀이

> **`...`(말줄임표)** — 가변 인자 자리. 그 뒤의 인자는 수도 타입도 선언에 없다.\
> 예: `int sum_n(int n, ...);`.

> **기본 인자 승격** — `...` 뒤(와 C17 의 빈 괄호 호출)의 인자에 거는 정수 승격 + `float` → `double`.\
> 예: `(char)'A'` 는 `int` 로 넘어간다.

> **`va_list` · `va_start` · `va_arg` · `va_end` · `va_copy`** — 가변 인자를 훑는 타입과 매크로 다섯. 시작 · 하나 꺼내기 · 끝 · 사본.\
> 예: `va_start(ap, n); int v = va_arg(ap, int); va_end(ap);`.

> **센티널(sentinel)** — 인자 목록의 **끝을 알리는 값**. 보통 `NULL`.\
> 예: `count_until_null("a", "b", (char *)NULL)`.

> **`format` 속성** — gcc·clang 확장. 「이 함수의 N번 인자는 `printf` 형식 문자열, M번부터가 그 대상」이라고 알려 `-Wformat` 을 켠다.\
> 예: `__attribute__((format(printf, 1, 2)))`.

> **`ud2`** — x86 의 「정의되지 않은 명령」. 실행하면 **SIGILL**(종료 코드 132). gcc 가 **도달하면 UB 인 자리**에 심는다.\
> 예: `get_float.constprop.0` 의 끝.

> **SIGILL** — 잘못된 명령 시그널. 셸의 종료 코드로는 `128 + 4 = 132`.\
> 예: gcc 판의 `run exit=132`.

## 더 들어가면

- ★★ **다른 ABI(ARM64 · Windows x64)의 `va_list`** — 포인터 하나인 판도 있다. 그 판에서는 (6)의 「넘기면 소비된다」가 **다르게** 보일 것이다. ★ **못 잰 것**(이 머신은 x86-64 Linux).
- ★★ **`va_arg(ap, unsigned int)` 로 `int` 를 꺼내기** — 표준의 **허락된 예외**다. ★ **격자에 넣지 않았다.**
- ★ **`vprintf` 에 넘긴 `ap` 를 다시 쓰기** — (6)과 같은 규칙이다. ★ **던지지 않았다.**
- ★ **C23 `nullptr` 를 센티널로** — 표준 예외 목록에 `nullptr_t` 가 있다. ★ **던지지 않았다.**
- ★ **gcc `-Wformat=2` · `-Wformat-nonliteral`** — 형식 문자열이 리터럴이 아닐 때. ★ **던지지 않았다.**
