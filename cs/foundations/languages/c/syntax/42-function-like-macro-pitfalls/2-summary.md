# c/syntax/42 — 함수형 매크로의 함정: 「**매크로는 인자를 값이 아니라 글자로 받는다 — 괄호도 평가 횟수도 문장 경계도 대신 지켜 주지 않는다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) 매크로 치환 절 — 「**`#`·`##` 에 붙지 않은 매개변수는 인자의 매크로를 전부 치환한 토큰열로 바뀐다**」 · 「**함수형 매크로 이름 뒤에 `(` 가 오지 않으면 호출이 아니다**」 · 식 절의 「**스칼라 객체에 순서 없는 두 부작용이 있으면 미정의**」를 **본문에서 직접 찾아 읽었다**)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **전처리 결과 · 값 · 진단은 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.\
> ★★★ **본체는 함정 격자다** — 매크로 3판(`x * x` · `(x) * (x)` · `((x) * (x))`) × 인자 3(`3` · `1+2` · `-3`) × 쓰는 자리 4(그대로 · `100/` · `~` · `!`), 칸마다 **값**, 기준은 같은 식을 **함수로** 계산한 값. 전처리 결과(`-E -P`)를 옆에 둔다.\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> **버전** — 함수형 매크로는 C89 부터다. `static inline` 은 C99 · `__typeof__`·문장 식 `({ })` 은 **GNU 확장**(C23 의 `typeof` 는 표준이지만 이 편은 `__typeof__` 만 썼다).
> ★★★ **경계** — **전처리가 컴파일 이전이라는 것 · `-E -P` 로 읽는 법**은 [41번 형제](../41-preprocessor-directives-and-conditional-compilation/), **`#`·`##` 와 한 겹 더 감싸기**는 [43번 형제](../43-stringizing-and-token-pasting/), **`inline`·`static inline` 의 링크 규칙**은 [39번 형제](../39-inline-and-c-inline-rules/), **시퀀스 포인트와 평가 순서 자체**는 [10번 형제](../10-evaluation-order-and-sequence-points/)가 정본이다 — 이 편은 **매크로가 그것들을 어떻게 깨뜨리나**만 쓴다.\
> ★ **`_Generic` 과 매크로를 묶는 한계**는 [40번 형제](../40-generic-selection-c11/)가 보였다.
> 선행 — [41번 형제](../41-preprocessor-directives-and-conditional-compilation/).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 둘째 창(실행 값) + 넷째 창(전처리 결과)이다.** 값이 틀린 칸을 세고, 왜 틀렸는지는 `-E -P` 의 글자가 말한다.
★★★ 격자에서 **함수와 다른 칸 14 / 36** — `x * x` 는 **8 / 12**, `(x) * (x)` 는 **6 / 12**, `((x) * (x))` 만 **0 / 12**. **gcc 와 clang 의 출력은 한 글자도 같고 경고는 둘 다 0** 이다 — **틀린 값이 전부 적법한 식이라** 어떤 도구도 말하지 않는다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | ★★ `-Wsequence-point`/`-Wunsequenced` · `-Wmultistatement-macros`(gcc 만) · `else` 짝 잃음 에러 · 문장 식의 `-pedantic` · 함수로 바꿨을 때의 타입 진단 | 씀 |
| ★★★ ② **실행 값(함정 격자)** | ★ **본체** — 칸마다 값과 함수 기준값 · 호출 횟수 계수 | 씀 |
| ③ sanitizer | ★★ `SQ3(i++)` 에 UBSan 을 걸었다 | ★★★ **침묵** — UBSan 에는 순서 없는 수정을 보는 검사가 없다(두 컴파일러 0줄) |
| ★★★ ④ **전처리 결과(`-E -P`)** | ★ **본체의 짝** — 틀린 값이 **어떤 글자에서 왔나** | 씀 |
| 시간 측정 | — | ★★★ **부적용 — 「매크로가 함수보다 빠르다」는 재지 않았다.** 이 편은 **값이 맞나**의 주제다 |
| ★ 제5의 상태 | 「`SQ3(i++)` 는 무엇을 내나」를 **실행으로 물을 수 없다**(미정의 — 결과를 싣지 않는다). **컴파일러 경고로 바꿔 물으니** 두 컴파일러가 「미정의일 수 있다」·「순서 없는 수정」이라고 답했다. ★ **UBSan 으로 바꿔 물은 것은 실패**했다(위 ③) | 창을 바꿔 답함 |

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
===== g++ --version | sed -n 1p (cc exit=0) =====
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

```text
===== rustc --version (exit=0) =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **함정 격자 · 호출 횟수 · 전처리 결과** · 진단 문구 | 전부 **정의된 동작**의 값이다 |
| ★★★ **싣지 않는다** | `SQ3(i++)` 의 값과 그 뒤의 `i` | **미정의 동작**이다 — 한 판의 출력은 근거가 못 된다. 진단(①)만 싣는다 |
| **흔들린다** | — | 이 편에는 없다 — 정규화 규칙은 기본 넷뿐이다 |

## 한눈에 — 쉽게 말하면

**함수형 매크로는 「빈칸 채우기 양식」이다. 빈칸에 쓴 글자를 그대로 옮겨 적을 뿐, 뜻은 모른다.**

- **빈칸에 `1+2` 를 쓰면 `1+2` 가 들어간다** — `3` 이 들어가는 게 아니다. 양식 쪽 문장이 `x*x` 면 `1+2*1+2`. → **괄호 누락**
- **양식에 빈칸이 두 번 나오면 두 번 옮겨 적는다** — 빈칸에 「도장을 하나 찍어라」라고 쓰면 도장이 **두 번** 찍힌다. → **인자 중복 평가**
- **양식이 두 문장이면 「만약 ~면」이 첫 문장에만 걸린다** — 빈칸 양식 뒤에 쓴 `;` 도 문장 하나가 된다. → **`do { } while (0)`**
- **함수는 「계산해서 값을 넘기는 창구」다** — 한 번 계산하고, 받는 종류(타입)가 정해져 있다. → **`static inline` 함수**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 글자를 옮겨 적는다 | `SQ1(1+2)` → `1+2 * 1+2` = `5` | ★★★ (1) 격자 · `-E -P` |
| 두 번 옮겨 적는다 | `SQ3(next())` → `next()` 두 번 · `calls = 2` | ★★★ (3) |
| 도장이 몇 번인지 모른다 | `SQ3(i++)` — 미정의 | ★★ (2) 경고만 |
| 첫 문장에만 걸린다 | `if (argc > 5) TWO1("a");` 인데 `[2] a` 가 찍힌다 | ★★★ (4) |
| 창구 | `sq(next())` → `calls = 1` · `sq(2.5)` → `4` | ★★ (3)·(6) |

```text
   #define SQ1(x) x * x                 쓴 식            -E -P 가 만든 글자              값
   ------------------------------       -------------    ---------------------------    ----
   인자를 「글자」로 받는다        ──▶  SQ1(1+2)         1+2 * 1+2                      5
                                        100/SQ1(3)       100/3 * 3                      99
   괄호를 치환 목록 안에만 두면   ──▶  100/SQ2(3)       100/(3) * (3)                  99
   바깥 괄호까지 두면             ──▶  100/SQ3(3)       100/((3) * (3))                11
   함수(기준)                     ──▶  100/sq(3)        100/sq(3)  → sq 가 9 를 돌려준다 11
```

- ★★★ **이 주제는 「표준」 칸이 전부다** — 매크로 치환 규칙대로 **정확히** 틀린다. 컴파일러도 판도 안 탄다.
- ★★ **「컴파일러 구현」 칸은 경고의 유무**(gcc 만 `-Wmultistatement-macros`)와 **GNU 문장 식**에만 있다.

> **함수형 매크로(function-like macro)** — `#define 이름(매개변수) 치환목록`. 이름 **바로 뒤에 `(`** 가 와야 호출이다.\
> 예: `#define SQ3(x) ((x) * (x))`.

> **중복 평가(double evaluation)** — 치환 목록에 매개변수가 두 번 나와 **인자 식이 두 번 실행**되는 것.\
> 예: `SQ3(next())` → `((next()) * (next()))`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **매크로의 괄호는 어디에 몇 겹 있어야 하나** — 인자의 괄호 · 바깥 괄호 · 쓰는 자리의 연산자.
2. ★★★ **인자가 두 번 평가되면 무엇이 되나** — 정의된 경우(함수 호출)와 미정의인 경우(`i++`).
3. ★★ **여러 문장 매크로는 왜 `do { } while (0)` 인가, 그리고 언제 함수로 바꾸나** — 문장 식 · `static inline` · 타입.

## 동작 방식

### (1) ★★★ 함정 격자 — 매크로 셋 × 인자 셋 × 쓰는 자리 넷

**언제 쓰나** — 매크로를 새로 쓰거나 남의 매크로를 **믿어도 되나** 판단할 때. ★★★ **이 편의 본체**다.

```c
/* s42a.c */
#include <stdio.h>

#define SQ1(x) x * x
#define SQ2(x) (x) * (x)
#define SQ3(x) ((x) * (x))

static int sq(int x) { return x * x; }

#define ROW "%-12s\t%d\t%d\t%d\t%d\n"

int main(void) {
    printf("%-12s\t%s\t%s\t%s\t%s\n", "expr", "SQ1", "SQ2", "SQ3", "sq()");
    printf(ROW, "SQ(3)",       SQ1(3),        SQ2(3),        SQ3(3),        sq(3));
    printf(ROW, "SQ(1+2)",     SQ1(1+2),      SQ2(1+2),      SQ3(1+2),      sq(1+2));
    printf(ROW, "SQ(-3)",      SQ1(-3),       SQ2(-3),       SQ3(-3),       sq(-3));
    printf(ROW, "100/SQ(3)",   100/SQ1(3),    100/SQ2(3),    100/SQ3(3),    100/sq(3));
    printf(ROW, "100/SQ(1+2)", 100/SQ1(1+2),  100/SQ2(1+2),  100/SQ3(1+2),  100/sq(1+2));
    printf(ROW, "100/SQ(-3)",  100/SQ1(-3),   100/SQ2(-3),   100/SQ3(-3),   100/sq(-3));
    printf(ROW, "~SQ(3)",      ~SQ1(3),       ~SQ2(3),       ~SQ3(3),       ~sq(3));
    printf(ROW, "~SQ(1+2)",    ~SQ1(1+2),     ~SQ2(1+2),     ~SQ3(1+2),     ~sq(1+2));
    printf(ROW, "~SQ(-3)",     ~SQ1(-3),      ~SQ2(-3),      ~SQ3(-3),      ~sq(-3));
    printf(ROW, "!SQ(3)",      !SQ1(3),       !SQ2(3),       !SQ3(3),       !sq(3));
    printf(ROW, "!SQ(1+2)",    !SQ1(1+2),     !SQ2(1+2),     !SQ3(1+2),     !sq(1+2));
    printf(ROW, "!SQ(-3)",     !SQ1(-3),      !SQ2(-3),      !SQ3(-3),      !sq(-3));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s42a.c -o x ; ./x (cc exit=0 · run exit=0) =====
expr        	SQ1	SQ2	SQ3	sq()
SQ(3)       	9	9	9	9
SQ(1+2)     	5	9	9	9
SQ(-3)      	9	9	9	9
100/SQ(3)   	99	99	11	11
100/SQ(1+2) 	104	99	11	11
100/SQ(-3)  	99	99	11	11
~SQ(3)      	-12	-12	-10	-10
~SQ(1+2)    	2	-12	-10	-10
~SQ(-3)     	-6	-6	-10	-10
!SQ(3)      	0	0	0	0
!SQ(1+2)    	4	0	0	0
!SQ(-3)     	0	0	0	0
```

```text
===== 함정 격자 — 매크로 3 × 인자 3 × 쓰는 자리 4 (sq() 와 대조) (exit=0) =====
식          	SQ1	SQ2	SQ3	sq() (기준)
SQ(3)       	9	9	9	9
SQ(1+2)     	5*	9	9	9
SQ(-3)      	9	9	9	9
100/SQ(3)   	99*	99*	11	11
100/SQ(1+2) 	104*	99*	11	11
100/SQ(-3)  	99*	99*	11	11
~SQ(3)      	-12*	-12*	-10	-10
~SQ(1+2)    	2*	-12*	-10	-10
~SQ(-3)     	-6*	-6*	-10	-10
!SQ(3)      	0	0	0	0
!SQ(1+2)    	4*	0	0	0
!SQ(-3)     	0	0	0	0
(* = sq() 칸과 다른 값 · gcc -std=c17 -Wall -Wextra -pedantic s42a.c 의 실행 출력)
sq() 와 다른 칸 14 / 36  (SQ1 8 / 12 · SQ2 6 / 12 · SQ3 0 / 12)
gcc 와 clang 의 실행 출력이 다른가: 같다 · warning: 줄 gcc 0 · clang 0
```

```text
===== gcc -std=c17 -E -P s42a.c | sed -n '/^int main/,$p' (cc exit=0) =====
int main(void) {
    printf("%-12s\t%s\t%s\t%s\t%s\n", "expr", "SQ1", "SQ2", "SQ3", "sq()");
    printf("%-12s\t%d\t%d\t%d\t%d\n", "SQ(3)", 3 * 3, (3) * (3), ((3) * (3)), sq(3));
    printf("%-12s\t%d\t%d\t%d\t%d\n", "SQ(1+2)", 1+2 * 1+2, (1+2) * (1+2), ((1+2) * (1+2)), sq(1+2));
    printf("%-12s\t%d\t%d\t%d\t%d\n", "SQ(-3)", -3 * -3, (-3) * (-3), ((-3) * (-3)), sq(-3));
    printf("%-12s\t%d\t%d\t%d\t%d\n", "100/SQ(3)", 100/3 * 3, 100/(3) * (3), 100/((3) * (3)), 100/sq(3));
    printf("%-12s\t%d\t%d\t%d\t%d\n", "100/SQ(1+2)", 100/1+2 * 1+2, 100/(1+2) * (1+2), 100/((1+2) * (1+2)), 100/sq(1+2));
    printf("%-12s\t%d\t%d\t%d\t%d\n", "100/SQ(-3)", 100/-3 * -3, 100/(-3) * (-3), 100/((-3) * (-3)), 100/sq(-3));
    printf("%-12s\t%d\t%d\t%d\t%d\n", "~SQ(3)", ~3 * 3, ~(3) * (3), ~((3) * (3)), ~sq(3));
    printf("%-12s\t%d\t%d\t%d\t%d\n", "~SQ(1+2)", ~1+2 * 1+2, ~(1+2) * (1+2), ~((1+2) * (1+2)), ~sq(1+2));
    printf("%-12s\t%d\t%d\t%d\t%d\n", "~SQ(-3)", ~-3 * -3, ~(-3) * (-3), ~((-3) * (-3)), ~sq(-3));
    printf("%-12s\t%d\t%d\t%d\t%d\n", "!SQ(3)", !3 * 3, !(3) * (3), !((3) * (3)), !sq(3));
    printf("%-12s\t%d\t%d\t%d\t%d\n", "!SQ(1+2)", !1+2 * 1+2, !(1+2) * (1+2), !((1+2) * (1+2)), !sq(1+2));
    printf("%-12s\t%d\t%d\t%d\t%d\n", "!SQ(-3)", !-3 * -3, !(-3) * (-3), !((-3) * (-3)), !sq(-3));
    return 0;
}
```

그림 해설 (한 단계씩):

- ★★★ **`SQ1(x) x * x` 는 12칸 중 8칸이 틀렸다** — 인자 `1+2` 가 `1+2 * 1+2`(=5)가 되고, 쓰는 자리의 연산자 `100/`·`~`·`!` 가 **첫 `x` 에만** 붙는다(`100/3 * 3` = 99 · `~3 * 3` = −12).
- ★★★ **`SQ2(x) (x) * (x)` 는 인자는 지켰지만 6칸이 틀렸다** — `(1+2) * (1+2)` 는 9 로 맞는데, **바깥 괄호가 없어** `100/(3) * (3)` 이 `(100/3) * 3` = 99 로 묶인다. `~`·`!` 도 같다.
- ★★★ **`SQ3(x) ((x) * (x))` 만 12칸 전부 함수와 같다** — 괄호가 **두 겹**(각 인자 + 전체) 있어야 한다.
- ★★ **`SQ(-3)` 은 세 판 다 9** — `-3 * -3` 은 괄호 없이도 9 다. ★ **「음수로 시험했더니 맞더라」는 괄호가 필요 없다는 증거가 아니다.** 같은 인자에서 `100/SQ1(-3)` 은 99 로 틀렸다.
- ★★ **`!SQ(3)` · `!SQ(-3)` 은 세 판 다 0** — `!3 * 3` 은 `0 * 3` 이라 **우연히** 맞는다. `!SQ1(1+2)` 에서야 4 로 드러났다. ★ **틀린 두 매크로(SQ1 · SQ2)가 맞는 값을 낸 칸**이 24칸 중 10칸이다 — 몇 칸만 시험하면 통과한다.
- ★★★ **경고 0 · gcc 와 clang 이 같다** — 틀린 칸은 **전부 적법한 식**이다. 우선순위대로 계산했을 뿐이다.

### (2) ★★★ `SQ3(i++)` — 중복 평가가 미정의가 되는 자리

**언제 쓰나** — 매크로에 **부작용이 있는 인자**(`i++`·`*p++`)를 넘길 때.

```c
/* s42b.c */
#include <stdio.h>

#define SQ3(x) ((x) * (x))

static int sq(int x) { return x * x; }

int main(void) {
    int i = 2;
    int r = SQ3(i++);
    (void)r;

    int j = 2;
    int s = sq(j++);
    printf("sq(j++) = %d · j = %d\n", s, j);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s42b.c -o /dev/null (cc exit=0) =====
s42b.c: In function ‘main’:
s42b.c:9:18: warning: operation on ‘i’ may be undefined [-Wsequence-point]
    9 |     int r = SQ3(i++);
      |                  ^
s42b.c:3:24: note: in definition of macro ‘SQ3’
    3 | #define SQ3(x) ((x) * (x))
      |                        ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s42b.c -o /dev/null (cc exit=0) =====
s42b.c:9:18: warning: multiple unsequenced modifications to 'i' [-Wunsequenced]
    9 |     int r = SQ3(i++);
      |                  ^~
s42b.c:3:18: note: expanded from macro 'SQ3'
    3 | #define SQ3(x) ((x) * (x))
      |                  ^     ~
1 warning generated.
```

```text
===== gcc -std=c17 -w -fsanitize=undefined s42b.c -o x ; ./x 2>&1 >/dev/null (cc exit=0 · run exit=0) =====
```

```text
===== clang -std=c17 -w -fsanitize=undefined s42b.c -o x ; ./x 2>&1 >/dev/null (cc exit=0 · run exit=0) =====
```

```text
===== gcc -std=c17 -w -fsanitize=undefined s42b.c -o x ; ./x (cc exit=0 · run exit=0) =====
sq(j++) = 4 · j = 3
```

그림 해설 (한 단계씩):

- ★★★ **`SQ3(i++)` 는 `((i++) * (i++))`** — 같은 `i` 를 **순서 없이 두 번 수정**한다. 식 절의 규칙상 **미정의 동작**이다([10번 형제](../10-evaluation-order-and-sequence-points/)). ★★★ **그래서 이 편은 `r` 의 값을 싣지 않는다** — 소스도 `(void)r;` 로 버린다.
- ★★★ **컴파일러는 둘 다 말한다** — gcc `operation on ‘i’ may be undefined [-Wsequence-point]` + `note: in definition of macro ‘SQ3’`, clang `multiple unsequenced modifications to 'i' [-Wunsequenced]`. 둘 다 `-Wall` 안이다.
- ★★★ **UBSan 은 두 컴파일러 다 0줄 · `run exit=0`** — UBSan 에는 **순서 없는 수정**을 보는 검사가 없다. ★ 「UBSan 으로 잡는다」는 **틀렸다** — 이 UB 는 **컴파일러 경고가 유일한 창**이다.
- ★★ **함수 `sq(j++)` 는 정의된 동작** — 인자가 **한 번** 평가되고 `j` 는 3, 값은 4.

### (3) ★★★ 정의된 중복 평가 — 호출이 두 번 일어난다

**언제 쓰나** — 인자가 **함수 호출**일 때. 미정의는 아니지만 **일이 두 번** 일어난다.

```c
/* s42c.c */
#include <stdio.h>

#define SQ3(x) ((x) * (x))
#define SQ4(x) ({ __typeof__(x) v_ = (x); v_ * v_; })

static int calls;
static int next(void) { calls++; return 3; }
static int sq(int x) { return x * x; }

int main(void) {
    int r3 = SQ3(next());
    printf("SQ3(next()) = %d · calls = %d\n", r3, calls);
    calls = 0;
    int r4 = SQ4(next());
    printf("SQ4(next()) = %d · calls = %d\n", r4, calls);
    calls = 0;
    int rf = sq(next());
    printf("sq(next())  = %d · calls = %d\n", rf, calls);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s42c.c -o x ; ./x (cc exit=0 · run exit=0) =====
SQ3(next()) = 9 · calls = 2
SQ4(next()) = 9 · calls = 1
sq(next())  = 9 · calls = 1
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s42c.c -o /dev/null (cc exit=0) =====
s42c.c: In function ‘main’:
s42c.c:4:16: warning: ISO C forbids braced-groups within expressions [-Wpedantic]
    4 | #define SQ4(x) ({ __typeof__(x) v_ = (x); v_ * v_; })
      |                ^
s42c.c:14:14: note: in expansion of macro ‘SQ4’
   14 |     int r4 = SQ4(next());
      |              ^~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s42c.c -o /dev/null (cc exit=0) =====
s42c.c:14:14: warning: use of GNU statement expression extension from macro expansion [-Wgnu-statement-expression-from-macro-expansion]
   14 |     int r4 = SQ4(next());
      |              ^
s42c.c:4:17: note: expanded from macro 'SQ4'
    4 | #define SQ4(x) ({ __typeof__(x) v_ = (x); v_ * v_; })
      |                 ^
1 warning generated.
```

```text
===== gcc -std=gnu17 -Wall -Wextra -c s42c.c -o /dev/null && clang -std=gnu17 -Wall -Wextra -c s42c.c -o /dev/null (cc exit=0) =====
```

그림 해설 (한 단계씩):

- ★★★ **`SQ3(next())` 는 `calls = 2`** — `next()` 두 호출은 **순서가 정해지지 않았을 뿐 둘 다 일어난다**(함수 호출끼리는 겹치지 않는다). 값은 3 × 3 = 9 로 맞다. **틀린 것은 값이 아니라 호출 횟수**다 — 인자가 `malloc`·`read`·로그 함수면 사고다.
- ★★★ **`SQ4` — GNU 문장 식 `({ … })` + `__typeof__` 로 한 번만 평가** — `calls = 1`. 인자를 **지역 변수 `v_` 에 한 번 담고** 그것을 두 번 쓴다.
- ★★ **문장 식은 ISO C 가 아니다** — `-std=c17 -pedantic` 에서 gcc 「ISO C forbids braced-groups within expressions [-Wpedantic]」, clang 「use of GNU statement expression extension from macro expansion」. **`-std=gnu17` 이면 두 컴파일러 다 0줄**(18-A).
- ★★ **함수 `sq(next())` 도 `calls = 1`** — 확장 없이 같은 결과. ★ **「한 번만 평가하는 매크로」가 필요하면 거의 항상 함수로 된다.** 문장 식이 남는 자리는 **타입을 가리지 않아야 할 때**뿐이다((6)).
- ★★ **그래도 이름은 샌다** — 문장 식 안의 지역 변수가 **호출하는 쪽의 같은 이름을 가린다.** C 매크로에는 **위생**(hygiene)이 없다.

```c
/* s42k.c */
#define SQ4(x) ({ __typeof__(x) v_ = (x); v_ * v_; })

int caller(void) {
    int v_ = 3;
    return SQ4(v_);
}
```

```text
===== gcc -std=gnu17 -E -P s42k.c (cc exit=0) =====
int caller(void) {
    int v_ = 3;
    return ({ __typeof__(v_) v_ = (v_); v_ * v_; });
}
```

```text
===== gcc -std=gnu17 -Wall -Wextra -c s42k.c -o /dev/null (cc exit=0) =====
```

```text
===== clang -std=gnu17 -Wall -Wextra -c s42k.c -o /dev/null (cc exit=0) =====
s42k.c:5:16: warning: variable 'v_' is uninitialized when used within its own initialization [-Wuninitialized]
    5 |     return SQ4(v_);
      |            ~~~~^~~
s42k.c:1:39: note: expanded from macro 'SQ4'
    1 | #define SQ4(x) ({ __typeof__(x) v_ = (x); v_ * v_; })
      |                                 ~~    ^
1 warning generated.
```

- ★★ `SQ4(v_)` 는 `__typeof__(v_) v_ = (v_);` — **초기화 중인 안쪽 `v_` 를 읽는다.** clang 은 `-Wuninitialized` 로 짚고 **gcc 는 `-O0` 에서 0줄**(18-A). 밑줄 이름은 충돌을 **드물게** 할 뿐이다.

### (4) ★★★ 여러 문장 매크로 — 중괄호도 괄호 없음도 안 된다

**언제 쓰나** — 로그·해제처럼 **두 문장 이상**을 한 매크로로 묶을 때.

```c
/* s42d.c */
#include <stdio.h>

#define TWO1(m) puts("[1] " m); puts("[2] " m)

int main(int argc, char **argv) {
    (void)argv;
    if (argc > 5) TWO1("a");
    puts("end");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s42d.c -o x ; ./x (cc exit=0 · run exit=0) =====
[2] a
end
```

```text
===== gcc -std=c17 -E -P s42d.c | sed -n '/^int main/,$p' (cc exit=0) =====
int main(int argc, char **argv) {
    (void)argv;
    if (argc > 5) puts("[1] " "a"); puts("[2] " "a");
    puts("end");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s42d.c -o /dev/null (cc exit=0) =====
s42d.c: In function ‘main’:
s42d.c:3:17: warning: macro expands to multiple statements [-Wmultistatement-macros]
    3 | #define TWO1(m) puts("[1] " m); puts("[2] " m)
      |                 ^~~~
s42d.c:7:19: note: in expansion of macro ‘TWO1’
    7 |     if (argc > 5) TWO1("a");
      |                   ^~~~
s42d.c:7:5: note: some parts of macro expansion are not guarded by this ‘if’ clause
    7 |     if (argc > 5) TWO1("a");
      |     ^~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s42d.c -o /dev/null (cc exit=0) =====
```

- ★★★ **`argc` 는 1 인데 `[2] a` 가 찍혔다** — 전처리 결과 `if (argc > 5) puts("[1] " "a"); puts("[2] " "a");` 에서 **`if` 는 첫 문장에만 걸린다.** 두 번째 `puts` 는 `if` **밖의 문장**이다.
- ★★ **gcc 만 경고한다** — `-Wmultistatement-macros`(`-Wall` 안) 「some parts of macro expansion are not guarded by this ‘if’ clause」. **clang 은 0줄**(18-A) — clang 으로만 빌드하면 안 보인다.

**중괄호로 감싸면 — `else` 가 짝을 잃는다.**

```c
/* s42e.c */
#include <stdio.h>

#define TWO2(m) { puts("[1] " m); puts("[2] " m); }

int main(int argc, char **argv) {
    (void)argv;
    if (argc > 5) TWO2("b"); else puts("[else] b");
    return 0;
}
```

```text
===== gcc -std=c17 -E -P s42e.c | sed -n '/^int main/,$p' (cc exit=0) =====
int main(int argc, char **argv) {
    (void)argv;
    if (argc > 5) { puts("[1] " "b"); puts("[2] " "b"); }; else puts("[else] b");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s42e.c -o /dev/null (cc exit=1) =====
s42e.c: In function ‘main’:
s42e.c:7:30: error: ‘else’ without a previous ‘if’
    7 |     if (argc > 5) TWO2("b"); else puts("[else] b");
      |                              ^~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s42e.c -o /dev/null (cc exit=1) =====
s42e.c:7:30: error: expected expression
    7 |     if (argc > 5) TWO2("b"); else puts("[else] b");
      |                              ^
1 error generated.
```

- ★★★ **`{ … };` 의 `;` 가 빈 문장이다** — `if (c) { … }` 로 `if` 문이 **끝나고**, `;` 가 다음 문장, 그다음 `else` 는 **붙을 `if` 가 없다.** gcc 「‘else’ without a previous ‘if’」, clang 「expected expression」.

**`do { … } while (0)` 은 문장 하나이고 `;` 를 먹는다.**

```c
/* s42f.c */
#include <stdio.h>

#define TWO3(m) do { puts("[1] " m); puts("[2] " m); } while (0)

int main(int argc, char **argv) {
    (void)argv;
    if (argc > 5) TWO3("c"); else puts("[else] c");
    if (argc > 0) TWO3("d"); else puts("[else] d");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s42f.c -o x ; ./x (cc exit=0 · run exit=0) =====
[else] c
[1] d
[2] d
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s42f.c -o /dev/null && clang -std=c17 -Wall -Wextra -pedantic -c s42f.c -o /dev/null (cc exit=0) =====
```

- ★★★ **`do { … } while (0)` 은 끝에 `;` 가 필요한 문장 하나**다 — 쓰는 쪽의 `;` 가 **정확히 그 자리를 채운다.** `if`/`else` 어디에 넣어도 한 문장으로 붙고, 몸통은 **정확히 한 번** 돈다. 두 컴파일러 경고 0.

```c
/* s42j.c */
#include <stdio.h>

#define TWO4(m) do { puts("[1] " m); puts("[2] " m); } while (0);

int main(int argc, char **argv) {
    (void)argv;
    if (argc > 5) TWO4("e"); else puts("[else] e");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s42j.c -o /dev/null (cc exit=1) =====
s42j.c: In function ‘main’:
s42j.c:7:30: error: ‘else’ without a previous ‘if’
    7 |     if (argc > 5) TWO4("e"); else puts("[else] e");
      |                              ^~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s42j.c -o /dev/null (cc exit=1) =====
s42j.c:7:30: error: expected expression
    7 |     if (argc > 5) TWO4("e"); else puts("[else] e");
      |                              ^
1 error generated.
```

- ★★ **치환 목록 끝에 `;` 를 넣으면 다시 깨진다** — `while (0);` + 쓰는 쪽의 `;` = **문장 둘**(`do … while (0);` 과 빈 문장 `;`) → `else` 가 고아가 되어 `{ }` 판과 **같은 에러**다.

```text
   쓰는 쪽                          TWO1 (괄호 없음)            TWO2 { }                    TWO3 do { } while (0)
   ----------------------------     -------------------------   -------------------------   --------------------------------
   if (c) M("x"); else puts(...);   if (c) A; B; else ...       if (c) { A; B; }; else ...  if (c) do { A; B; } while (0); else ...
                                    -> B 가 if 밖 · else 고아    -> ; 가 if 를 끝낸다          -> 문장 하나 · else 가 제자리
                                       (에러)                      (에러)                       (통과)
   if (c) M("x");  (else 없음)       B 가 항상 실행(조용함)       통과                          통과
```

### (5) ★★ 매크로 이름이 함수를 가린다 — `(max)(a, b)`

```c
/* s42i.c */
#include <stdio.h>

int max(int a, int b) { return a > b ? a : b; }

#define max(a, b) ((a) > (b) ? (a) : (b))

int main(void) {
    int (*fp)(int, int) = max;
    printf("%d %d %d\n", max(1, 2), (max)(3, 4), fp(5, 6));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s42i.c -o x ; ./x (cc exit=0 · run exit=0) =====
2 4 6
```

```text
===== gcc -std=c17 -E -P s42i.c | sed -n '/^int max/,$p' (cc exit=0) =====
int max(int a, int b) { return a > b ? a : b; }
int main(void) {
    int (*fp)(int, int) = max;
    printf("%d %d %d\n", ((1) > (2) ? (1) : (2)), (max)(3, 4), fp(5, 6));
    return 0;
}
```

- ★★★ **함수형 매크로는 이름 뒤에 `(` 가 올 때만 펼쳐진다** — `max(1, 2)` 는 매크로로, **`(max)(3, 4)`** 는 이름 뒤에 `)` 가 와서 **진짜 함수**로, `fp = max` 도 **함수 주소**로 남았다(`-E -P` 가 글자 그대로 보인다).
- ★★ 표준 라이브러리가 **같은 이름의 함수와 매크로를 함께** 둘 수 있는 이유다 — 괄호로 감싸면 **항상 함수**를 부른다.

### (6) ★★ `static inline` 함수로 바꾸면 — 얻는 것과 잃는 것

```c
/* s42g.c */
#include <stdio.h>

#define SQ3(x) ((x) * (x))

static inline int sq(int x) { return x * x; }

int main(void) {
    double d = 2.5;
    printf("SQ3(d) = %g\n", SQ3(d));
    printf("sq(d)  = %d\n", sq(d));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s42g.c -o x ; ./x (cc exit=0 · run exit=0) =====
SQ3(d) = 6.25
sq(d)  = 4
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s42g.c -o /dev/null && clang -std=c17 -Wall -Wextra -pedantic -c s42g.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -Wconversion -c s42g.c -o /dev/null (cc exit=0) =====
s42g.c: In function ‘main’:
s42g.c:10:32: warning: conversion from ‘double’ to ‘int’ may change value [-Wfloat-conversion]
   10 |     printf("sq(d)  = %d\n", sq(d));
      |                                ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -Wconversion -c s42g.c -o /dev/null (cc exit=0) =====
s42g.c:10:32: warning: implicit conversion turns floating-point number into integer: 'double' to 'int' [-Wfloat-conversion]
   10 |     printf("sq(d)  = %d\n", sq(d));
      |                             ~~ ^
1 warning generated.
```

```c
/* s42h.c */
#define SQ3(x) ((x) * (x))

static inline int sq(int x) { return x * x; }

int *p;

int by_func(void)  { return sq(p); }
int by_macro(void) { return SQ3(p); }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s42h.c -o /dev/null (cc exit=1) =====
s42h.c: In function ‘by_func’:
s42h.c:7:32: warning: passing argument 1 of ‘sq’ makes integer from pointer without a cast [-Wint-conversion]
    7 | int by_func(void)  { return sq(p); }
      |                                ^
      |                                |
      |                                int *
s42h.c:3:26: note: expected ‘int’ but argument is of type ‘int *’
    3 | static inline int sq(int x) { return x * x; }
      |                      ~~~~^
s42h.c: In function ‘by_macro’:
s42h.c:1:21: error: invalid operands to binary * (have ‘int *’ and ‘int *’)
    1 | #define SQ3(x) ((x) * (x))
      |                     ^
s42h.c:8:29: note: in expansion of macro ‘SQ3’
    8 | int by_macro(void) { return SQ3(p); }
      |                             ^~~
s42h.c:8:37: warning: control reaches end of non-void function [-Wreturn-type]
    8 | int by_macro(void) { return SQ3(p); }
      |                                     ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s42h.c -o /dev/null (cc exit=1) =====
s42h.c:7:32: error: incompatible pointer to integer conversion passing 'int *' to parameter of type 'int'; dereference with * [-Wint-conversion]
    7 | int by_func(void)  { return sq(p); }
      |                                ^
      |                                *
s42h.c:3:26: note: passing argument to parameter 'x' here
    3 | static inline int sq(int x) { return x * x; }
      |                          ^
s42h.c:8:29: error: invalid operands to binary expression ('int *' and 'int *')
    8 | int by_macro(void) { return SQ3(p); }
      |                             ^~~~~~
s42h.c:1:21: note: expanded from macro 'SQ3'
    1 | #define SQ3(x) ((x) * (x))
      |                 ~~~ ^ ~~~
2 errors generated.
```

그림 해설 (한 단계씩):

- ★★★ **함수는 인자를 매개변수 타입으로 바꾼다** — `sq(2.5)` 는 `int` 2 로 바뀌어 **4**. 매크로 `SQ3(2.5)` 는 `double` 그대로 **6.25**. ★★ **`-Wall -Wextra -pedantic` 은 0줄**(18-A) — `-Wconversion` 을 줘야 `-Wfloat-conversion` 이 나온다.
- ★★ **포인터를 넘기면 둘 다 막힌다** — 매크로 쪽은 `int * * int *` 가 **에러**(두 컴파일러), 함수 쪽은 gcc 가 **경고**(`-Wint-conversion`), clang 18 은 **에러**. ★ **「매크로는 조용하고 함수만 타입을 검사한다」는 이 칸에서 틀렸다** — 연산자가 받지 않는 타입이면 매크로도 에러다. **갈리는 곳은 「연산자는 받는데 뜻이 바뀌는 타입」**(`double` → `int`)이고, 거기서는 **함수가 조용히 바꾸고 매크로가 그대로 둔다.**
- ★★ **얻는 것** — 인자를 **한 번** 평가 · 괄호 걱정 없음 · 디버거에 이름이 남음 · 포인터 같은 명백한 오용은 진단. **잃는 것** — **타입 하나에 고정**(여러 타입이면 [40번 형제](../40-generic-selection-c11/)의 `_Generic` 이나 함수 여러 벌).
- ★ **`static inline` 을 헤더에 둘 때의 링크 규칙**은 [39번 형제](../39-inline-and-c-inline-rules/)가 쟀다 — `static inline` 은 그 격자에서 **모든 칸이 링크 성공**이었다.
- ★★★ **「매크로가 함수보다 빠르다」는 이 편이 재지 않았다** — `static inline` 이 실제로 펼쳐지는지는 [39번 형제](../39-inline-and-c-inline-rules/)의 어셈블리 격자가 **호출 수**로 셌을 뿐, 시간은 아무도 안 쟀다.

### (7) ★ C++ `constexpr` · Rust `macro_rules!` 와 대비

```cpp
// s42x.cpp
#include <cstdio>

constexpr int sq(int x) { return x * x; }
static_assert(sq(1 + 2) == 9, "");

int main() {
    int i = 2;
    int r = sq(i++);
    std::printf("sq(1 + 2) = %d · sq(i++) = %d · i = %d\n", sq(1 + 2), r, i);
    return 0;
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic s42x.cpp -o x ; ./x (cc exit=0 · run exit=0) =====
sq(1 + 2) = 9 · sq(i++) = 4 · i = 3
```

```rust
// s42r.rs
use std::sync::atomic::{AtomicU32, Ordering};

static CALLS: AtomicU32 = AtomicU32::new(0);

fn next() -> i32 {
    CALLS.fetch_add(1, Ordering::Relaxed);
    3
}

macro_rules! sq {
    ($x:expr) => { $x * $x };
}

fn main() {
    let a = sq!(1 + 2);
    let b = 100 / sq!(1 + 2);
    let c = sq!(next());
    println!("sq!(1 + 2) = {a} · 100 / sq!(1 + 2) = {b} · sq!(next()) = {c} · calls = {}", CALLS.load(Ordering::Relaxed));
}
```

```text
===== rustc --edition 2021 s42r.rs -o x (cc exit=0) =====
```

```text
===== rustc --edition 2021 s42r.rs -o x ; ./x (cc exit=0 · run exit=0) =====
sq!(1 + 2) = 9 · 100 / sq!(1 + 2) = 11 · sq!(next()) = 9 · calls = 2
```

- ★★ **C++ 는 이 자리를 함수로 푼다** — `constexpr` 함수는 **컴파일 시간에도 돌고**(`static_assert(sq(1 + 2) == 9)` 통과) 인자는 **한 번** 평가된다(`sq(i++)` = 4 · `i = 3`). [C++ 38 — `constexpr`](../../../cpp/syntax/38-constexpr-consteval-and-constinit/)이 정본이다.
- ★★★ **Rust `macro_rules!` 는 괄호 문제가 없다** — `$x:expr` 는 **식 하나로 파싱된 덩어리**라 `sq!(1 + 2)` = 9, `100 / sq!(1 + 2)` = 11. ★★ **그러나 중복 평가는 그대로다** — `sq!(next())` 는 `calls = 2`. Rust 매크로도 **식을 두 번 옮겨 적는다.** Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **57번**(`macro_rules!`)이 그 자리다.
- ★ 대비의 요점 — **괄호 문제는 「글자 치환」이라서 생기고**(Rust 는 토큰 트리로 풀었다), **중복 평가는 「옮겨 적기」라서 생긴다**(Rust 도 못 풀었다 — 값으로 받아야 풀린다).

## 문법 — 형태와 규칙

### 형태

```text
   #define SQ(x)  ((x) * (x))               ★ 인자마다 괄호 + 전체 괄호
   #define STMT(a) do { f(a); g(a); } while (0)   ★ 여러 문장은 do-while(0) — 끝에 ; 없음
   #define ONCE(x) ({ __typeof__(x) v_ = (x); v_ * v_; })   GNU 확장 — ISO 아님
   static inline int sq(int x) { return x * x; }         ★ 대개 이쪽이 답
   (name)(args)                             매크로를 건너뛰고 함수를 부른다
```

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 결과 | 층 |
|---|---|---|
| `#define SQ(x) x * x` 에 `SQ(1+2)` | **조용히 5** | ★★★ 표준(규칙대로 틀린다) |
| `SQ3(i++)` | **미정의** · 경고만 · UBSan 침묵 | ★★★ 표준(UB) |
| `SQ3(next())` | 호출 두 번 — 정의된 동작 | ★★ 표준 |
| `if (c) M1(); else …`(여러 문장 · 괄호 없음 / `{ }`) | 에러 | 표준(문법) |
| `if (c) M1();`(else 없음) | **조용히 두 번째 문장이 밖으로** · gcc 만 경고 | ★★ 표준 + 컴파일러 구현(경고) |
| `({ … })` | `-pedantic` 경고 · gnu 모드 0줄 | ★★ 컴파일러 구현(확장) |

### 규칙 불릿

- ★★★ **괄호는 두 겹** — 매개변수마다 `(x)`, 치환 목록 전체에 `( … )`.
- ★★★ **매개변수는 치환 목록에 한 번만** — 두 번이면 인자가 두 번 실행된다. 부작용 인자면 미정의일 수도 있다.
- ★★★ **여러 문장은 `do { … } while (0)`** — 끝에 `;` 를 넣지 않는다(쓰는 쪽이 넣는다).
- ★★ **값을 돌려주는 매크로는 함수(`static inline`)로 바꿀 수 있는지 먼저 본다.**
- ★ **`(name)(…)` 로 매크로를 건너뛴다.**

## 어디서 틀리나

### 1. ★★★ 「인자에 괄호를 쳤으니 됐다」

`(x) * (x)` 는 **바깥 괄호가 없어** `100/SQ2(3)` = 99 · `~SQ2(3)` = −12 로 틀렸다((1)). **쓰는 자리의 연산자**가 첫 인자에만 붙는다.

### 2. ★★★ 「몇 개 넣어 봤더니 맞다」

틀린 매크로 둘(SQ1 · SQ2)이 **24칸 중 10칸에서 맞는 값**을 냈다 — `SQ(3)` · `SQ(-3)` · `!SQ(3)` 은 틀린 매크로로도 맞다. **`1+2` 와 `100/` 를 반드시 넣어라.**

### 3. ★★★ 「UBSan 이 `SQ3(i++)` 를 잡는다」

**두 컴파일러 다 0줄**((2)). 순서 없는 수정은 **컴파일러 경고**(`-Wsequence-point`·`-Wunsequenced`)로만 보인다.

### 4. ★★ 「중복 평가는 `i++` 같은 것만 문제다」

`SQ3(next())` 는 **정의된 동작인데 호출이 두 번**이다((3)). 값이 맞아도 **일이 두 번 일어난다.**

### 5. ★★ 「중괄호로 감싸면 여러 문장 매크로가 안전하다」

`else` 앞에서 **에러**다((4)). 그리고 **`else` 가 없으면 괄호 없는 판은 조용히 틀린다** — clang 은 경고도 없다.

### 6. ★★ 「함수로 바꾸면 타입이 검사되니 더 안전하다」

**`double` 을 넘기면 함수가 조용히 `int` 로 바꿨다**(4 대 6.25, `-Wall -Wextra -pedantic` 0줄 — (6)). 안전해지는 것은 **평가 횟수와 괄호**이고, 타입은 **고정되는 대신 조용히 변환**될 수 있다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 전부다** — 함정 격자는 **gcc·clang 이 한 글자도 같다.** 틀린 값은 **치환 규칙과 우선순위의 정확한 결과**다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | ★★★ **인자는 토큰으로 치환 · 괄호 규칙의 결과 · `(name)(…)` 는 호출이 아님 · 함수 호출 두 번은 정의된 동작 · 매개변수 타입으로의 변환** | 격자 · `-E -P` · 계수 |
| ★★★ **UB** | 아무 일이나 | ★★★ **`SQ3(i++)` — 순서 없는 두 수정** | 진단만(값은 싣지 않음) |
| **미명시** | 몇 가지 중 하나 | ★ **`next() * next()` 의 두 호출 순서** — 이 편은 같은 값(3)을 돌려줘 **순서가 결과에 안 드러나게** 했다 | — |
| **구현 정의** | 문서화 의무 | ★ 해당 없음 | — |
| ★★ **컴파일러 구현** | 도구의 선택 | ★★ **`-Wmultistatement-macros`(gcc 만)** · 문장 식 `({ })`·`__typeof__`(GNU 확장) · **포인터 인자의 함수 쪽 진단(gcc 경고 · clang 에러)** | 진단 |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★★ **함정 격자의 틀린 14칸 전부** — 두 컴파일러 경고 0. 적법한 식이다 |
| ★★★ **UB** | ★★★ **UBSan 이 `SQ3(i++)` 에 0줄** — 컴파일러 경고가 유일한 창이다 |
| ★★ **컴파일러 구현** | ★★ **clang 은 `if` 밖으로 샌 두 번째 문장에 0줄** · 두 컴파일러 다 **`sq(2.5)` 의 조용한 변환에 0줄**(`-Wconversion` 없이는) |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **매크로의 사고는 적법한 식으로 나타난다** — 경고를 기다리지 말고 **`-E -P` 를 읽는다.**
  - ★★★ **부작용 인자의 미정의는 경고만 잡는다** — `-Wall` 을 끄면 아무것도 안 남는다.
  - ★★ **gcc 와 clang 을 둘 다 돌려라** — 경고의 유무가 갈린다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 값 하나를 계산 | ★★★ **`static inline` 함수** | 매크로(괄호 · 중복 평가) |
| 여러 타입에 같은 계산 | ★★ **`((x) * (x))` + 부작용 없는 인자만 쓴다는 규약** 또는 [40번 형제](../40-generic-selection-c11/)의 `_Generic` | 괄호 한 겹 매크로 |
| 한 번만 평가하는 타입 무관 매크로 | ★ GNU 문장 식 + `__typeof__`(**gnu 모드 전용이라고 적는다**) | ISO 코드에 섞기 |
| 여러 문장 묶기 | ★★★ **`do { … } while (0)`** | `{ … }` · 괄호 없음 |
| 매크로와 같은 이름의 함수 부르기 | ★ `(name)(args)` | `#undef` 로 지우기 |
| `__FILE__`·`__LINE__` 을 호출 자리에서 | ★★ **매크로가 필요하다**([43번 형제](../43-stringizing-and-token-pasting/)) | 함수(자기 자리의 줄을 찍는다) |

판단 규칙 두 줄.

- ★★★ **「함수로 쓸 수 있나」를 먼저 묻는다** — 안 되는 것은 **호출 자리의 정보**(`__LINE__`)·**토큰 조작**(`#`·`##`)·**타입 무관**뿐이다.
- ★★ **매크로를 쓰기로 했으면 격자의 세 줄**(`SQ(1+2)` · `100/SQ(3)` · `SQ(f())` 의 호출 수)을 시험한다.

## 핵심 문장

- ★★★ **함정 격자 36칸 중 14칸이 함수와 달랐다 — `x * x` 8 · `(x) * (x)` 6 · `((x) * (x))` 0. gcc·clang 출력이 같고 경고는 0이다.**
- ★★★ **`SQ1(1+2)` 는 `1+2 * 1+2`(5), `100/SQ2(3)` 은 `100/(3) * (3)`(99) — 괄호는 인자마다와 전체에 두 겹 있어야 한다.**
- ★★★ **`SQ3(i++)` 는 미정의라 값을 싣지 않는다 — gcc `-Wsequence-point` · clang `-Wunsequenced` 가 경고했고, UBSan 은 두 컴파일러 다 0줄이었다.**
- ★★ **`SQ3(next())` 는 호출 두 번(calls = 2) — GNU 문장 식 매크로와 함수는 한 번. 문장 식은 `-pedantic` 에서 두 컴파일러 다 경고했다.**
- ★★★ **괄호 없는 두 문장 매크로는 `if` 밖으로 두 번째 문장이 샜다(`[2] a` · gcc 만 경고) · `{ }` 매크로는 `else` 앞에서 에러 · `do { } while (0)` 만 통과.**
- ★★ **`static inline int sq(int)` 는 `2.5` 를 조용히 `2` 로 바꿔 4 를 냈다(매크로는 6.25) — 함수는 평가 횟수를 고치고 타입을 고정한다.**

## 관련 자료

- [41번 형제 — 전처리기 지시자](../41-preprocessor-directives-and-conditional-compilation/) — ★★ **선행.** `-E -P` 로 읽는 법.
- [43번 형제 — `#` 와 `##`](../43-stringizing-and-token-pasting/) — ★★ 매크로가 **꼭 필요한** 자리.
- [10번 형제 — 평가 순서와 시퀀스 포인트](../10-evaluation-order-and-sequence-points/) — ★★ `SQ3(i++)` 가 **왜** 미정의인가의 정본.
- [39번 형제 — `inline`](../39-inline-and-c-inline-rules/) — ★★ `static inline` 을 헤더에 둘 때.
- [40번 형제 — `_Generic`](../40-generic-selection-c11/) — ★ 타입마다 다른 함수를 **매크로로 고르는** 길과 그 한계.
- [09번 형제 — 연산자 우선순위](../09-operator-precedence-and-associativity/) — ★ 격자의 `100/3 * 3` 이 **왜 99** 인가.
- [C++ 38 — `constexpr`](../../../cpp/syntax/38-constexpr-consteval-and-constinit/) — ★ C++ 가 매크로 대신 쓰는 것.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **57번** — ★ `macro_rules!`(토큰 트리 매크로).

## 용어 풀이

> **치환 목록(replacement list)** — `#define` 의 이름(과 매개변수) 뒤에 오는 토큰들. 호출 자리가 이것으로 바뀐다.\
> 예: `#define SQ3(x) ((x) * (x))` 의 `((x) * (x))`.

> **순서 없는 수정(unsequenced modification)** — 한 식 안에서 같은 객체를 순서가 정해지지 않은 두 곳에서 바꾸는 것. **미정의 동작**이다.\
> 예: `((i++) * (i++))`.

> **문장 식(statement expression)** — `({ 문장들; 마지막식; })`. 블록을 식처럼 쓰고 마지막 식의 값을 낸다. **GNU 확장.**\
> 예: `({ int v = f(); v * v; })`.

> **`__typeof__`** — 식의 타입을 이름으로 쓰게 하는 GNU 확장. C23 에서는 `typeof` 가 표준이다.\
> 예: `__typeof__(x) v = (x);`.

> **위생적 매크로(hygienic macro)** — 매크로 안에서 만든 이름이 호출하는 쪽의 이름과 **안 섞이게** 하는 성질. C 매크로에는 없다.\
> 예: Rust `macro_rules!` 의 지역 변수.

## 더 들어가면

- ★★ **C23 `typeof` 로 `SQ4` 를 표준 판으로** — 문장 식은 여전히 확장이라 **한 번 평가**는 ISO 만으로 못 한다. ★ 던지지 않았다.
- ★ **`SQ4(v_)` 를 gcc `-O2` 로** — 최적화 판에서 gcc 가 초기화 안 된 읽기를 경고하는지. ★ 던지지 않았다.
- ★ **`-Wmultistatement-macros` 가 잡지 못하는 모양** — `for`·`while` 몸통에 넣었을 때. ★ 던지지 않았다.
