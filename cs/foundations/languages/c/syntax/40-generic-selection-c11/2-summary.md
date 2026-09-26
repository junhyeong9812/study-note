# c/syntax/40 — `_Generic` 타입 제네릭 선택 (C11): 「**`_Generic` 은 식을 평가하지 않고 타입만 본다 — 그 타입은 한정자를 벗고 배열을 포인터로 바꾼 뒤의 것이다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) 제네릭 선택 절 — 「**제어식의 타입은 lvalue 변환 · 배열→포인터 · 함수→포인터 변환을 거친 것처럼 본다**」·각주 「**lvalue 변환은 타입 한정자를 떨어뜨린다**」·「**`default` 가 없으면 제어식의 타입이 목록의 정확히 하나와 호환되어야 한다(제약)**」·「**두 연관이 호환 타입을 지정하면 안 된다**」·「**제어식은 평가되지 않는다 · 고르지 않은 연관의 식도 평가되지 않는다**」, 예제 `#define cbrt(X) _Generic((X), long double: cbrtl, default: cbrt, float: cbrtf)(X)` 를 **본문에서 직접 찾아 읽었다**)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **고른 분기 · 진단 · 헤더 내용은 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★★★ **본체는 선택 격자다** — 인자 14 × 컴파일러 3(gcc · gcc-12 · clang) × 판 2(`-std=c11`/`c17`), 칸마다 **고른 분기의 이름**.\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> **버전** — `_Generic` 은 **C11 부터**다.
> ★★ **경계** — **`typedef` 가 새 타입을 안 만든다**(`two compatible types` 에러)는 [06번 형제](../06-typedef-and-type-aliases/), **`NULL`·`0`·`nullptr` 의 타입**을 `_Generic` 으로 가른 것은 [19번 형제](../19-void-pointer-null-pointer-and-null/)가 이미 보였다 — 이 편은 그 결과를 **다시 재지 않는다.** **매크로 자체의 규칙**은 목록의 **41번 주제**(전처리기)와 목록의 **42번 주제**(함수형 매크로의 함정)가 정본이다. `<tgmath.h>` 의 수학 함수 목록은 이 목록이 **뺀** 영역이다(README 「뺀 것과 이유」) — 여기는 **그 헤더가 무엇으로 만들어졌나**만 본다.
> 선행 — 목록의 **41번 주제**.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 둘째 창 — 실행이 찍은 「고른 분기의 이름」이다.** `_Generic` 은 **컴파일 때 끝나는** 일이라 값이 곧 증거다 — 고른 분기의 문자열 리터럴을 찍었다.
★★★ 그 격자에서 **갈린 칸 0 / 70** — 세 컴파일러 · 두 판이 **한 칸도 안 갈렸다.** 갈린 것은 **경고**뿐이다(gcc 두 판 0 · clang 14).

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | ★★ `default` 없이 맞는 분기가 없을 때의 에러 · clang 의 `-Wunreachable-code-generic-assoc`·`-Wunevaluated-expression` · 매크로의 한계(에러) | 씀 |
| ★★★ ② **실행 출력(선택 격자)** | ★ **본체** — 고른 분기의 이름 | 씀 |
| ③ sanitizer | — | 부적용(런타임에 아무 일도 없는 문법이다) |
| ④ 어셈블리 | — | ★ **잴 것이 없다** — 고르지 않은 분기는 **평가되지 않는다**(표준). (3)이 **부작용 계수**로 그것을 보였다 |
| ★ 전처리 결과(`-E`) | ★★ `<tgmath.h>` 가 **`_Generic` 이 아닌 것**으로 만들어졌다는 것 | 씀 |
| ★ 제5의 상태 | 「`const int` 분기는 왜 안 골라지나」를 **실행으로** 물으면 `int` 가 찍힐 뿐 이유가 안 보인다 — **clang 의 경고로 바꿔 물으니** 「lvalue 변환 때문에 한정된 연관은 **절대** 안 골라진다」는 문장이 나왔다 | 창을 바꿔 답함 |

## 이 판

```text
===== gcc --version | sed -n 1p (cc exit=0) =====
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

```text
===== gcc-12 --version | sed -n 1p (cc exit=0) =====
gcc-12 (Ubuntu 12.4.0-2ubuntu1~24.04.1) 12.4.0
```

```text
===== clang --version | sed -n 1p (cc exit=0) =====
Ubuntu clang version 18.1.3 (1ubuntu1)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **선택 격자 전부 · 경고 수** · 에러 문구 · 부작용 계수 | 컴파일 때 정해지는 것이다 |
| **흔들린다** | — | 이 편에는 없다 — 정규화 규칙은 기본 넷뿐이다 |

## 한눈에 — 쉽게 말하면

**`_Generic` 은 「물건의 겉 포장을 벗겨 보고 고르는 분류대」다.**

- **분류대는 물건을 열지 않는다** — 크기와 모양(타입)만 본다. 안에서 무엇이 일어날지(부작용)는 **일어나지 않는다.** → **제어식은 평가되지 않는다**
- **「깨지기 쉬움」 스티커(`const`)는 떼고 본다** — `const int` 짜리 칸을 만들어 둬도 **아무것도 거기 안 간다.** → **lvalue 변환이 한정자를 벗긴다**
- **상자째 들어온 배열은 「첫 칸을 가리키는 쪽지」로 바꿔 본다** — `int[3]` 은 `int *` 칸으로 간다. → **배열 → 포인터**
- **맞는 칸이 없고 「기타」 칸도 없으면 분류대가 멈춘다** — 컴파일 에러. → **`default` 가 없으면 정확히 하나**
- **칸 목록은 분류대를 만들 때 정해진다** — 새 모양의 물건이 오면 **분류대를 다시 만들어야** 한다. → **매크로를 고쳐야 한다**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 열지 않는다 | `_Generic(i++, …)` 뒤에도 `i = 0` | ★★ (3) |
| 스티커 떼기 | `const int ci` → `int` 분기 | ★★★ 격자 · clang 경고 |
| 쪽지로 바꾸기 | `int a[3]` → `int *` · `"abc"` → `char *` | ★★★ 격자 |
| 칸이 없음 | `_Generic(f, int: 1, double: 2)` 에 `float` | ★★ 에러 |
| 분류대 다시 만들기 | `ABS` 에 `short`·`struct` 가 오면 에러 | ★★ (4) |

```text
   T(ci)   ci 는 const int (lvalue)
             │ lvalue 변환 — 한정자를 벗긴다
             ▼
           int ──▶ int: "int" 를 고른다          const int: "const int" 는 절대 안 골라진다

   T(a)    a 는 int[3]
             │ 배열 → 포인터
             ▼
           int * ──▶ int *: "int *"              ★ &a 는 int (*)[3] — 배열 자체의 주소

   T('a')  'a' 는 C 에서 int 다(문자 상수) ──▶ int: "int"
```

- ★★★ **이 주제는 「표준」 칸이 거의 전부**다 — 변환 규칙 · 제약 · 평가하지 않음이 **모두 표준 문장**이고, 격자가 0 / 70 인 이유가 그것이다.
- ★★ **「컴파일러 구현」 칸은 경고와 `<tgmath.h>` 의 구현 수단**에만 있다.

> **제네릭 선택(generic selection)** — `_Generic(제어식, 타입: 식, …, default: 식)`. 제어식의 **타입**에 맞는 연관의 식이 **그 자리의 식**이 된다.\
> 예: `_Generic(x, int: "int", default: "other")`.

> **lvalue 변환** — 객체를 가리키는 식을 **그 값**으로 바꾸는 변환. 이때 **`const`·`volatile` 같은 한정자가 떨어진다.**\
> 예: `const int ci` 의 값의 타입은 `int`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **`_Generic` 은 인자의 어떤 타입을 보고 고르나** — 한정자 · 배열 · 문자 상수 · 승격된 식.
2. ★★ **고르지 않은 것은 어떻게 되나** — 제어식과 나머지 분기의 평가 · 맞는 분기가 없을 때.
3. ★★ **매크로와 묶어 「타입 제네릭 함수」를 만들면 어디서 막히나** — 새 타입 · 인자 수 · `<tgmath.h>` 의 실제 구현.

## 동작 방식

### (1) ★★★ 선택 격자 — 인자 열넷 × 컴파일러 셋 × 판 둘

**언제 쓰나** — `_Generic` 으로 분기하는 매크로에 **어떤 식이 들어오면 어느 칸이 골라지나** 확인할 때. ★★★ **이 편의 본체**다.

```c
/* s40a.c */
#include <stdio.h>

#define T(x) _Generic((x),                                         \
    char: "char", signed char: "signed char",                      \
    unsigned char: "unsigned char", short: "short",                \
    int: "int", const int: "const int", long: "long",              \
    char *: "char *", const char *: "const char *",                \
    int *: "int *", const int *: "const int *",                    \
    int (*)[3]: "int (*)[3]", double: "double",                    \
    default: "default")

#define P(e) printf("%-10s\t%s\n", #e, T(e))

int main(void) {
    char c = 'x';
    short s = 1;
    const int ci = 2;
    int a[3] = {0};
    const int ca[2] = {0};
    char *pc = &c;
    const char *pcc = "k";
    P(c);  P('a');  P(s);  P(ci);  P(a);  P(&a);  P(ca);
    P(pc);  P(pcc);  P("abc");  P(+c);  P(c + c);  P((char)1);  P(1.0f);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s40a.c -o x ; ./x (cc exit=0 · run exit=0) =====
c         	char
'a'       	int
s         	short
ci        	int
a         	int *
&a        	int (*)[3]
ca        	const int *
pc        	char *
pcc       	const char *
"abc"     	char *
+c        	int
c + c     	int
(char)1   	char
1.0f      	default
```

```text
===== 선택 격자 — 인자 14 × 컴파일러 3 × 판 2 (-Wall -Wextra -pedantic) (exit=0) =====
인자      	gcc c11	gcc c17	gcc-12 c11	gcc-12 c17	clang c11	clang c17
c         	char	char	char	char	char	char
'a'       	int	int	int	int	int	int
s         	short	short	short	short	short	short
ci        	int	int	int	int	int	int
a         	int *	int *	int *	int *	int *	int *
&a        	int (*)[3]	int (*)[3]	int (*)[3]	int (*)[3]	int (*)[3]	int (*)[3]
ca        	const int *	const int *	const int *	const int *	const int *	const int *
pc        	char *	char *	char *	char *	char *	char *
pcc       	const char *	const char *	const char *	const char *	const char *	const char *
"abc"     	char *	char *	char *	char *	char *	char *
+c        	int	int	int	int	int	int
c + c     	int	int	int	int	int	int
(char)1   	char	char	char	char	char	char
1.0f      	default	default	default	default	default	default
경고	0	0	0	0	14	14
gcc c11 칸과 갈린 칸 0 / 70
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s40a.c -o /dev/null | sed -n '1,4p;$p' (cc exit=0) =====
s40a.c:22:5: warning: due to lvalue conversion of the controlling expression, association of type 'const int' will never be selected because it is qualified [-Wunreachable-code-generic-assoc]
   22 |     P(c);  P('a');  P(s);  P(ci);  P(a);  P(&a);  P(ca);
      |     ^
s40a.c:12:40: note: expanded from macro 'P'
14 warnings generated.
```

그림 해설 (한 단계씩):

- ★★★ **갈린 칸 0 / 70** — gcc 13 · gcc-12 · clang 18 × `-std=c11`/`c17` 이 **한 칸도 안 갈렸다.**
- ★★★ **`ci`(`const int`)는 `int`** · **`ca`(`const int[2]`)는 `const int *`** — 한정자는 **제어식 자체의 최상위**에서만 떨어진다. 배열이 포인터가 되면 `const` 는 **가리키는 쪽**에 붙어 남는다. 그래서 `const int:` 칸은 **어떤 식으로도 골라지지 않는다.**
- ★★★ **`a`(`int[3]`)는 `int *`** · **`&a` 는 `int (*)[3]`** — 배열→포인터 변환은 **배열 식에만** 걸린다. `&a` 는 이미 포인터다([16번 형제](../16-array-pointer-decay-and-function-parameters/)·[17번 형제](../17-multidimensional-arrays-and-pointer-types/)의 감쇠 규칙 그대로).
- ★★★ **`'a'` 는 `int`, `c` 는 `char`, `(char)1` 은 `char`** — C 의 문자 상수는 **`int` 타입**이다. `char` 변수는 **승격되지 않는다**(제어식은 평가되지 않으니 **정수 승격도 없다**). 승격은 **연산이 있을 때만** — `+c` · `c + c` 는 `int`.
- ★★ **`"abc"` 는 `char *`** — C 의 문자열 리터럴은 `char[4]` 이고 포인터가 되면 **`char *`**(`const char *` 가 아니다 — [20번 형제](../20-null-terminated-strings-and-string-literals/)).
- ★★ **`1.0f` 는 `default`** — `float` 칸을 안 만들었다. `double` 칸이 있어도 **`float` 은 `double` 로 가지 않는다** — 승격이 없다.
- ★★★ **경고만 갈렸다** — gcc 두 판은 **0**, clang 은 **14** — `P(…)` 한 번마다 `const int` 연관이 **「절대 안 골라진다」** 는 `-Wunreachable-code-generic-assoc`.

★ **브리핑이 물은 「`const` 는 벗겨진다(C17 DR 481) — gcc/clang 판 차이?」의 답은 「이 판들에서는 차이가 없다」** 다. `-std=c11` 과 `-std=c17` 이 같고, gcc-12 와 13 도 같다. ★ **DR 481 의 내용과 옛 판(gcc 7 이전 등)의 동작은 이 문서가 확인하지 않았다** — N3220 의 각주 「lvalue 변환은 한정자를 떨어뜨린다」가 **지금의 규칙**이다.

### (2) ★★ 맞는 분기가 없고 `default` 도 없으면

**언제 쓰나** — `default` 를 빼고 타입을 **닫힌 목록**으로 만들 때.

```c
/* s40b.c */
int pick(float f) {
    return _Generic(f, int: 1, double: 2);
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s40b.c -o /dev/null (cc exit=1) =====
s40b.c: In function ‘pick’:
s40b.c:2:21: error: ‘_Generic’ selector of type ‘float’ is not compatible with any association
    2 |     return _Generic(f, int: 1, double: 2);
      |                     ^
s40b.c:3:1: warning: control reaches end of non-void function [-Wreturn-type]
    3 | }
      | ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s40b.c -o /dev/null (cc exit=1) =====
s40b.c:2:21: error: controlling expression type 'float' not compatible with any generic association type
    2 |     return _Generic(f, int: 1, double: 2);
      |                     ^
1 error generated.
```

- ★★★ **두 컴파일러 다 에러 · `cc exit=1`** — gcc 「`_Generic` selector of type ‘float’ is not compatible with any association」, clang 「controlling expression type 'float' not compatible with any generic association type」. **제약 위반**이다.
- ★★ **`float` 은 `double` 칸으로 가지 않는다** — `_Generic` 에는 **변환 사다리가 없다.** 호환 타입이어야 한다.
- ★ gcc 는 선택이 실패한 뒤 `control reaches end of non-void function` 까지 낸다 — **첫 에러의 여파**다.
- ★ 같은 연관 목록에 **호환 타입 둘**(`int` 와 `typedef int MyInt`)을 두면 `two compatible types` 에러 — [06번 형제](../06-typedef-and-type-aliases/)가 보였다.

### (3) ★★ 평가되지 않는 것 — 제어식과 고르지 않은 분기

**언제 쓰나** — 제어식이나 분기에 **부작용이 있는 식**을 넣을 때.

```c
/* s40c.c */
#include <stdio.h>

static int calls;
static int bump(void) { return ++calls; }

int main(void) {
    int i = 0;
    int r1 = _Generic(i++, int: 10, default: bump());
    printf("r1 = %d · i = %d · calls = %d\n", r1, i, calls);
    int r2 = _Generic(1.5, int: bump(), double: 20, default: bump());
    printf("r2 = %d · calls = %d\n", r2, calls);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s40c.c -o x ; ./x (cc exit=0 · run exit=0) =====
r1 = 10 · i = 0 · calls = 0
r2 = 20 · calls = 0
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s40c.c -o /dev/null (cc exit=0) =====
s40c.c:8:24: warning: expression with side effects has no effect in an unevaluated context [-Wunevaluated-expression]
    8 |     int r1 = _Generic(i++, int: 10, default: bump());
      |                        ^
1 warning generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s40c.c -o /dev/null (cc exit=0) =====
```

- ★★★ **`i++` 가 일어나지 않았다(`i = 0`)** — 제어식은 **타입만 쓰이고 평가되지 않는다.**
- ★★★ **`bump()` 는 한 번도 불리지 않았다(`calls = 0`)** — 고르지 않은 분기의 식은 **평가되지 않는다.** 두 선택 모두 부작용 없는 분기(`10` · `20`)를 골랐다.
- ★★ **clang 은 `-Wunevaluated-expression` 으로 알려 준다** — 「부작용이 있는 식이 평가되지 않는 문맥에 있다」. **gcc 는 0건** — 두 컴파일러가 갈린 자리다.
- ★ 이것은 `sizeof` 의 피연산자와 같은 성질이다 — [18번 형제](../18-variable-length-arrays-vla/)가 `_Generic(sizeof vla, …)` 로 `sizeof` 의 결과 타입을 물었다.

### (4) ★★ 매크로와 묶으면 — 닫힌 목록 · 고정된 호출 모양

**언제 쓰나** — `ABS(x)` 하나로 `int`·`long`·`double` 을 다 받고 싶을 때(표준 예제의 `cbrt` 와 같은 모양).

```c
/* s40d.c */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define ABS(x) _Generic((x), int: abs, long: labs, double: fabs)(x)

struct money { long cents; };

int main(void) {
    printf("%d %ld %.1f\n", ABS(-3), ABS(-4L), ABS(-2.5));
#ifdef USE_SHORT
    short sh = -7;
    printf("%d\n", ABS(sh));
#endif
#ifdef USE_MONEY
    struct money m = { -500 };
    printf("%ld\n", ABS(m).cents);
#endif
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s40d.c -o x ; ./x (cc exit=0 · run exit=0) =====
3 4 2.5
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -DUSE_SHORT -c s40d.c -o /dev/null (cc exit=1) =====
s40d.c: In function ‘main’:
s40d.c:5:25: error: ‘_Generic’ selector of type ‘short int’ is not compatible with any association
    5 | #define ABS(x) _Generic((x), int: abs, long: labs, double: fabs)(x)
      |                         ^
s40d.c:13:20: note: in expansion of macro ‘ABS’
   13 |     printf("%d\n", ABS(sh));
      |                    ^~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -DUSE_SHORT -c s40d.c -o /dev/null (cc exit=1) =====
s40d.c:13:20: error: controlling expression type 'short' not compatible with any generic association type
   13 |     printf("%d\n", ABS(sh));
      |                    ^~~~~~~
s40d.c:5:25: note: expanded from macro 'ABS'
    5 | #define ABS(x) _Generic((x), int: abs, long: labs, double: fabs)(x)
      |                         ^~~
1 error generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -DUSE_MONEY -c s40d.c -o /dev/null (cc exit=1) =====
s40d.c: In function ‘main’:
s40d.c:5:25: error: ‘_Generic’ selector of type ‘struct money’ is not compatible with any association
    5 | #define ABS(x) _Generic((x), int: abs, long: labs, double: fabs)(x)
      |                         ^
s40d.c:17:21: note: in expansion of macro ‘ABS’
   17 |     printf("%ld\n", ABS(m).cents);
      |                     ^~~
```

그림 해설 (한 단계씩):

- ★★★ **`short` 를 넣으면 에러** — 목록에 `short` 가 없고 `default` 도 없다. **`short` 는 `int` 로 승격되지 않는다**((1)의 `s` 칸). 함수 `abs(sh)` 로 부르면 되던 것이 **매크로를 거치면 안 된다.**
- ★★★ **사용자 타입(`struct money`)도 같은 에러** — 새 타입을 받으려면 **매크로 본문을 고쳐야** 한다. 목록은 **매크로를 정의한 곳 한 군데에** 닫혀 있다.
- ★★ **clang 은 매크로를 부른 자리(13행)를, gcc 는 매크로 본문(5행)을 먼저 짚는다** — 둘 다 다른 쪽을 `note:` 로 보인다.

```c
/* s40d2.c */
#include <stdio.h>
#include <stdlib.h>

struct scaled { long v; };
long scaled_abs(struct scaled s, int unit) { return labs(s.v) / unit; }

#define ABS(x) _Generic((x), int: abs, long: labs, struct scaled: scaled_abs)(x)

int main(void) {
    struct scaled q = { -900 };
    printf("%d %ld\n", ABS(-3), ABS(-4L));
    printf("%ld\n", ABS(q));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s40d2.c -o /dev/null (cc exit=1) =====
s40d2.c: In function ‘main’:
s40d2.c:7:16: error: too few arguments to function ‘scaled_abs’
    7 | #define ABS(x) _Generic((x), int: abs, long: labs, struct scaled: scaled_abs)(x)
      |                ^~~~~~~~
s40d2.c:12:21: note: in expansion of macro ‘ABS’
   12 |     printf("%ld\n", ABS(q));
      |                     ^~~
s40d2.c:5:6: note: declared here
    5 | long scaled_abs(struct scaled s, int unit) { return labs(s.v) / unit; }
      |      ^~~~~~~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s40d2.c -o /dev/null (cc exit=1) =====
s40d2.c:12:21: error: too few arguments to function call, expected 2, have 1
   12 |     printf("%ld\n", ABS(q));
      |                     ^~~~~~
s40d2.c:7:80: note: expanded from macro 'ABS'
    7 | #define ABS(x) _Generic((x), int: abs, long: labs, struct scaled: scaled_abs)(x)
      |                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  ^
s40d2.c:5:6: note: 'scaled_abs' declared here
    5 | long scaled_abs(struct scaled s, int unit) { return labs(s.v) / unit; }
      |      ^          ~~~~~~~~~~~~~~~~~~~~~~~~~
1 error generated.
```

- ★★★ **인자 수가 다른 함수는 한 매크로에 못 담는다** — `ABS(x)` 는 고른 함수를 **`(x)` 하나로 부른다.** `scaled_abs` 는 인자가 둘이라 **`too few arguments`**. 호출의 모양이 **매크로 한 곳에 고정**돼 있다.
- ★ 이 에러는 **`struct scaled` 를 넣은 호출(12행)에서만** 난다 — `ABS(-3)`·`ABS(-4L)` 은 `scaled_abs` 를 **고르지 않으니** 평가하지 않는다((3)의 규칙).

### (5) ★★ `<tgmath.h>` 는 `_Generic` 으로 만들어져 있나

**언제 쓰나** — 「`_Generic` 의 대표 사용처가 `<tgmath.h>` 」라는 설명을 확인할 때.

```c
/* s40e.c */
#include <stdio.h>
#include <tgmath.h>

#define NAME(x) _Generic((x), float: "float", double: "double", \
                         long double: "long double", default: "other")

int main(void) {
    float f = 2.0f;
    int n = 2;
    printf("sqrt(f)    -> %s\n", NAME(sqrt(f)));
    printf("sqrt(n)    -> %s\n", NAME(sqrt(n)));
    printf("sqrt(2.0L) -> %s\n", NAME(sqrt(2.0L)));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s40e.c -o x -lm ; ./x (cc exit=0 · run exit=0) =====
sqrt(f)    -> float
sqrt(n)    -> double
sqrt(2.0L) -> long double
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s40e.c -o x -lm ; ./x (cc exit=0 · run exit=0) =====
sqrt(f)    -> float
sqrt(n)    -> double
sqrt(2.0L) -> long double
```

```text
===== gcc -std=c17 -E s40e.c | grep -oE '__builtin_tgmath|__tg_sqrt|_Generic' | sort | uniq -c (cc exit=0) =====
      3 _Generic
      3 __builtin_tgmath
```

```text
===== clang -std=c17 -E s40e.c | grep -oE '__builtin_tgmath|__tg_sqrt|_Generic' | sort | uniq -c (cc exit=0) =====
      3 _Generic
      9 __tg_sqrt
```

```text
===== for f in /usr/include/tgmath.h /usr/lib/llvm-18/lib/clang/18/include/tgmath.h; do printf '%s : _Generic %s · __builtin_tgmath %s · overloadable %s\n' $f $(grep -c _Generic $f) $(grep -c __builtin_tgmath $f) $(grep -c overloadable $f); done (exit=0) =====
/usr/include/tgmath.h : _Generic 4 · __builtin_tgmath 24 · overloadable 0
/usr/lib/llvm-18/lib/clang/18/include/tgmath.h : _Generic 0 · __builtin_tgmath 0 · overloadable 3
```

그림 해설 (한 단계씩):

- ★★ **`sqrt(n)`(`int`)은 `double`** — `<tgmath.h>` 의 규칙은 **정수 인자를 `double` 로** 본다. `float` 은 `float`, `long double` 은 `long double` — 두 컴파일러가 같다.
- ★★★ **그런데 전처리 결과에 `_Generic` 은 3 개뿐이다 — 전부 내가 쓴 `NAME` 매크로의 것**이다. gcc 판(glibc 의 `tgmath.h`)은 **`__builtin_tgmath`**, clang 판(clang 자체의 `tgmath.h`)은 **`__tg_sqrt`** 라는 **`overloadable` 함수들**로 푼다.
- ★★ **헤더를 세어 보면** — glibc 의 `tgmath.h` 는 `_Generic` 4 줄 · `__builtin_tgmath` 24 줄, clang 의 것은 `_Generic` 0 줄 · `overloadable` 3 줄. ★ glibc 의 `_Generic` 4 줄이 **어느 컴파일러 판에서 쓰이는 갈래인지**는 이 문서가 읽지 않았다 — 결론은 「**이 판의 gcc·clang 은 `_Generic` 을 거치지 않았다**」까지다.
- ★★★ **왜 `_Generic` 만으로는 안 되나** — (4)의 두 한계 그대로다. `pow(x, y)` 처럼 **인자가 둘이고 둘 다 타입을 봐야** 하는 함수, 정수를 `double` 로 **올려서 보는** 규칙은 **연관 목록 하나로 표현이 번거롭다.** 두 구현이 **컴파일러 내장 기능**으로 간 이유로 읽힌다(★ 헤더 주석으로 확인한 것은 아니다 — **내 추론**).

### (6) ★★ 36편 가변 인자와 대비 — 타입을 언제 아나

**언제 쓰나** — 「여러 타입을 받는 함수」를 C 로 만들 두 길을 고를 때.

```text
                        가변 인자 (...)               _Generic
                        ----------------------------  ----------------------------
   타입을 아는 때         런타임 — 형식 문자열·개수로     컴파일 때 — 제어식의 타입으로
                         「따로 알려 줘야」 안다
   작은 타입              승격된다 (char→int,          승격되지 않는다 (char 는 char,
                          float→double)               float 은 float)
   틀리면                 UB — 대부분 조용하다           에러(목록에 없음) — 컴파일 때 멈춘다
   새 타입                형식 문자열을 발명             매크로 목록을 고친다
```

- ★★★ **[36번 형제](../36-variadic-functions-stdarg/)의 `...` 는 타입을 지운다** — 받는 쪽이 `va_arg(ap, T)` 로 **믿고** 꺼낸다. `_Generic` 은 **컴파일러가 타입을 보고** 고른다.
- ★★ **승격의 방향이 반대다** — `...` 는 `char`·`float` 을 **올려 보내고**, `_Generic` 은 **그대로 본다**((1)의 `c` 와 `1.0f`).
- ★★ **틀렸을 때** — 36편은 **UB 가 조용히** 지나갔고(`va_arg(ap, char)` 가 clang 에서 맞아 보였다), 이 편은 **컴파일 에러**로 멈췄다((2)·(4)).

### (7) ★ C++ 의 오버로드 — 열린 목록

**언제 쓰나** — 「다른 언어는 이것을 무엇으로 하나」.

```cpp
// s40x.cpp
#include <cstdio>
#include <cstdlib>

struct Money { long cents; };

int    my_abs(int x)    { return std::abs(x); }
long   my_abs(long x)   { return std::labs(x); }
double my_abs(double x) { return x < 0 ? -x : x; }
Money  my_abs(Money m)  { return Money{ std::labs(m.cents) }; }   // 새 타입은 여기에 한 벌 더

int main() {
    short sh = -7;
    std::printf("%d %ld %.1f %d %ld\n", my_abs(-3), my_abs(-4L), my_abs(-2.5), my_abs(sh), my_abs(Money{-500}).cents);
    return 0;
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic s40x.cpp -o x ; ./x (cc exit=0 · run exit=0) =====
3 4 2.5 7 500
```

- ★★★ **C++ 은 오버로드로 한다** — `my_abs(Money)` **한 벌을 더 선언**하면 된다. 기존 코드(다른 `my_abs` 들)를 **안 고친다** — 목록이 **열려** 있다.
- ★★ **`short` 는 `int` 로 승격되어 `my_abs(int)` 가 골라진다**(값 `7`) — 오버로드 해석에는 **승격·변환의 순위**가 있다. `_Generic` 에는 없다((4)의 에러). [C++ 01 — 함수 오버로딩과 오버로드 해석](../../../cpp/syntax/01-function-overloading-and-overload-resolution/)이 정본이다.
- ★ **템플릿**은 타입마다 함수를 **만들어 낸다** — [C++ 31 — 함수 템플릿과 인자 추론](../../../cpp/syntax/31-function-templates-and-argument-deduction/).

## 문법 — 형태와 규칙

### 형태

(1)의 `s40a.c` · (4)의 `s40d.c` 가 이 절의 **실제로 컴파일되는 형태**다. 쓰는 자리를 한 줄씩:

| 쓴 꼴 | 뜻 | 판 |
|---|---|---|
| `_Generic((x), int: e1, double: e2, default: e3)` | 제어식의 타입으로 식 하나를 고른다 | C11 부터 |
| `#define F(x) _Generic((x), int: f_i, double: f_d)(x)` | ★★ **함수 지명자를 고르고 `(x)` 로 부른다**(표준 예제의 `cbrt` 모양) | C11 부터 |
| `#define NAME(x) _Generic((x), …: "…")` | 타입 이름을 문자열로 — 이 갈래의 **증명 도구** | C11 부터 |
| `default:` | 목록 밖 타입의 갈 곳 — **없으면 정확히 하나가 맞아야** 한다 | C11 부터 |

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 종료 코드 | 층 | 어느 절 |
|---|---|---|---|
| 맞는 분기도 `default` 도 없음 | 두 컴파일러 **에러** | ★★★ 제약 위반 | (2)·(4) |
| 호환 타입 둘을 목록에 | **에러** `two compatible types` | ★★★ 제약 위반 | [06번 형제](../06-typedef-and-type-aliases/) |
| `const int:` 연관 | 경고 0(gcc) · clang `-Wunreachable-code-generic-assoc` · **절대 안 골라짐** | ★★ 적법하지만 죽은 칸 | (1) |
| 제어식에 부작용 | gcc 0 · clang `-Wunevaluated-expression` · **일어나지 않는다** | ★★ 적법 | (3) |
| 고른 함수가 인자 수가 다름 | **에러** `too few arguments` | ★★ 함수 호출의 제약 | (4) |

### 규칙 불릿

- ★★★ **제어식의 타입은 lvalue 변환 · 배열→포인터 · 함수→포인터 뒤의 것** — 최상위 한정자는 떨어진다.
- ★★★ **제어식은 평가되지 않는다 · 고르지 않은 분기도 평가되지 않는다.**
- ★★★ **승격도 변환 사다리도 없다** — `char` 는 `char`, `float` 은 `float`, `short` 는 `short`.
- ★★ **`default` 가 없으면 정확히 하나** — 없으면 에러.
- ★★ **연관 목록에 호환 타입 둘은 금지** — `typedef` 는 같은 타입이다.
- ★★ **매크로와 묶으면 목록이 닫힌다** — 새 타입 · 다른 인자 수는 **매크로를 고쳐야** 한다.

## 어디서 틀리나

### 1. ★★★ 「`const int` 분기를 만들어 두면 상수가 거기로 간다」

**절대 안 간다**((1)). 한정자는 떨어진다. gcc 는 **아무 말도 안 한다.**

### 2. ★★★ 「`'a'` 는 `char` 다」

**C 에서는 `int`** 다((1)) — 문자 상수의 타입이다. `char` 분기로 가는 것은 **`char` 변수**와 **`(char)` 캐스트**뿐이었다.

### 3. ★★ 「`short` 는 `int` 로 올라가니 `int` 분기면 된다」

**`_Generic` 은 승격하지 않는다**((1)의 `s` · (4)의 에러). 함수 호출이라면 올라갔을 값이다.

### 4. ★★ 「`float` 은 `double` 칸으로 가겠지」

**안 간다**((1)의 `1.0f` → `default` · (2)의 에러).

### 5. ★★ 「제어식에서 `i++` 해도 한 번은 증가한다」

**평가되지 않는다**((3)). gcc 는 경고도 없다.

### 6. ★ 「`<tgmath.h>` 는 `_Generic` 으로 되어 있다」

**이 판의 두 구현은 아니다**((5)) — `__builtin_tgmath` 와 `overloadable`.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 거의 전부**다 — 그래서 격자가 **0 / 70** 이다.\
★★ **「컴파일러 구현」 칸은 진단과 `<tgmath.h>` 의 수단**에만 있다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | ★★★ **제어식의 변환 셋 · 한정자 떨어짐 · 평가하지 않음 · `default` 규칙 · 호환 타입 금지** · 문자 상수는 `int` · 문자열 리터럴은 `char[]` | 선택 격자 0 / 70 · 부작용 계수 · 에러 |
| ★★ **조건부 표준** | 판이 조건 | ★★ **`_Generic` 은 C11 부터** — 이 편은 C11·C17 만 던졌다 | 격자의 두 판 |
| **구현 정의** | 문서화 의무가 있다 | ★ **해당 없음**(이 편이 던진 것 중에는) | — |
| ★★ **컴파일러 구현** | 도구의 선택 | ★★ **clang 의 두 경고(gcc 는 0)** · 에러 문구와 짚는 자리 · ★★ **`<tgmath.h>` 를 `__builtin_tgmath`(glibc/gcc) · `overloadable`(clang)로 구현** | 경고 행 · `-E` · 헤더 세기 |
| **미명시** | 몇 가지 중 하나 | ★ **해당 없음** | — |
| **UB** | 아무 일이나 | ★ **해당 없음** — 틀리면 **컴파일 에러**로 멈춘다. 이 편의 사고는 **「안 골라진다」·「평가되지 않는다」처럼 적법하게 조용한 것**이다 | — |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★ **gcc 는 절대 안 골라지는 `const int:` 칸에 0** · ★★ **gcc 는 평가되지 않는 `i++` 에 0** — 두 자리 다 clang 만 말했다 |
| ★★ **컴파일러 구현** | ★ `<tgmath.h>` 가 무엇으로 되어 있는지는 **어떤 진단도 말하지 않는다** — `-E` 와 헤더를 직접 봐야 한다 |
| ★★ **(층을 가로지름)** | ★ **「종료 코드 0인데 ill-formed」는 이 편에 없다** — 제약 위반은 두 컴파일러가 **전부 에러**로 막았다((2)·(4)) |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **`_Generic` 의 규칙은 판과 컴파일러를 안 탄다** — 0 / 70.
  - ★★ **사고는 「조용히 적법한」 쪽에 있다** — 죽은 칸 · 평가되지 않는 부작용. **gcc 로만 빌드하면 둘 다 안 보인다.**
  - ★★ **틀린 타입은 에러로 멈춘다** — 36편의 가변 인자와 정반대다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 타입 몇 개에 같은 이름 | ★★ **`_Generic` 매크로 + `default` 없음**(닫힌 목록 — 틀리면 에러) | `default` 에 아무 함수나 |
| 타입 이름 찍기(디버그) | ★★ `_Generic((x), …: "…")` | `sizeof` 로 추측 |
| `const` 로 분기 | ★ **포인터가 가리키는 쪽**의 `const`(`const char *`) — 최상위 `const` 는 못 가른다 | `const int:` 칸 |
| 새 타입이 자주 늘어난다 | ★★ **타입마다 이름이 다른 함수**(`money_abs`) | 매크로 목록을 계속 고치기 |
| 인자 수가 다른 변형 | ★ **별도의 매크로·함수** | 한 `_Generic` 매크로 |
| 수학 함수 | ★ `<tgmath.h>` — **구현이 내장 기능으로** 해 준다 | 직접 `_Generic` 으로 흉내 |

판단 규칙 두 줄.

- ★★★ **제어식을 보면 「lvalue 변환 · 배열→포인터 뒤의 타입」으로 한 번 바꿔 읽는다** — 그 타입만 목록과 맞춰 본다.
- ★★ **목록이 자주 바뀔 것 같으면 `_Generic` 을 쓰지 않는다** — 닫힌 목록은 C 에서 **한 곳을 고쳐야 하는** 구조다.

## 핵심 문장

- ★★★ **선택 격자 70 칸이 한 칸도 안 갈렸다 — gcc 13 · gcc-12 · clang 18 × C11·C17.**
- ★★★ **`const int` 는 `int` 로, `const int[2]` 는 `const int *` 로 골라졌다 — 최상위 한정자만 떨어진다. `const int:` 칸은 절대 안 골라진다(clang 만 경고).**
- ★★★ **`'a'` 는 `int`, `char` 변수는 `char`, `+c` 는 `int` — `_Generic` 은 승격하지 않고, 승격은 연산이 할 때만 생긴다.**
- ★★ **제어식의 `i++` 와 고르지 않은 분기의 `bump()` 는 평가되지 않았다(`i = 0 · calls = 0`).**
- ★★ **`default` 없이 맞는 분기가 없으면 두 컴파일러 다 에러 — `short`·사용자 타입을 받으려면 매크로를 고쳐야 하고, 인자 수가 다른 함수는 한 매크로에 못 담는다.**
- ★★ **이 판의 `<tgmath.h>` 는 `_Generic` 이 아니라 `__builtin_tgmath`(gcc)와 `overloadable`(clang)로 풀렸다.**

## 관련 자료

- [36번 형제 — 가변 인자](../36-variadic-functions-stdarg/) — ★★★ **대비.** 타입을 **런타임에 믿는** 길.
- [06번 형제 — `typedef`](../06-typedef-and-type-aliases/) — ★★ `two compatible types` · `_Generic` 을 **증명 도구**로 쓴 첫 자리.
- [19번 형제 — `void *`·`NULL`](../19-void-pointer-null-pointer-and-null/) — ★★ `NULL`·`0`·`nullptr` 의 타입을 `_Generic` 으로.
- [02번 형제 — 기본 타입](../02-basic-types-sizes-and-fixed-width-integers/) · [18번 형제 — VLA](../18-variable-length-arrays-vla/) — ★ `_Generic` 으로 타입을 찍은 자리.
- [16번 형제 — 배열 감쇠](../16-array-pointer-decay-and-function-parameters/) · [20번 형제 — 문자열 리터럴](../20-null-terminated-strings-and-string-literals/) — ★ 격자의 `a`·`"abc"` 칸의 정본.
- 목록의 **41번 주제**(전처리기) · 목록의 **42번 주제**(함수형 매크로의 함정) — ★★ **선행.** 매크로 규칙의 정본.
- [C++ 01 — 함수 오버로딩](../../../cpp/syntax/01-function-overloading-and-overload-resolution/) · [C++ 31 — 함수 템플릿](../../../cpp/syntax/31-function-templates-and-argument-deduction/) — ★ **열린 목록**의 두 길.

## 용어 풀이

> **연관(generic association)** — `_Generic` 목록의 `타입: 식` 한 쌍(또는 `default: 식`).\
> 예: `int: "int"`.

> **제어식(controlling expression)** — `_Generic` 의 첫 인자. **타입만** 쓰이고 평가되지 않는다.\
> 예: `_Generic(i++, …)` 의 `i++`.

> **호환 타입(compatible type)** — 컴파일러가 같은 것으로 보는 타입. `typedef` 별칭은 원래 타입과 호환된다.\
> 예: `int` 와 `typedef int MyInt`.

> **`<tgmath.h>`** — `sqrt` 처럼 **인자 타입에 따라 `sqrtf`·`sqrt`·`sqrtl` 을 고르는** 이름을 주는 헤더(C99). 정수 인자는 `double` 로 본다.\
> 예: `sqrt(n)` 의 결과가 `double`.

> **`overloadable`** — clang 의 C 확장 속성. C 에서도 **같은 이름의 함수를 여러 타입으로** 선언하게 해 준다.\
> 예: clang 의 `tgmath.h` 의 `__tg_sqrt`.

## 더 들어가면

- ★★ **C23 `typeof` 와 `_Generic` 을 같이** — `typeof_unqual` 로 한정자를 벗기는 자리. ★ **던지지 않았다.**
- ★ **glibc `tgmath.h` 의 `_Generic` 4 줄이 쓰이는 갈래** — 헤더를 끝까지 읽지 않았다.
