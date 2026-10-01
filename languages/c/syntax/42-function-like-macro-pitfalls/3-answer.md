# c/syntax/42 — 함수형 매크로의 함정: 「**매크로는 인자를 값이 아니라 글자로 받는다 — 괄호도 평가 횟수도 문장 경계도 대신 지켜 주지 않는다**」 — 정답

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 함정 격자 — **함수와 다른 칸 14 / 36(SQ1 8 · SQ2 6 · SQ3 0) · 경고 0 · gcc·clang 같음** ★★★

**출력**

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

**왜 그런가**

- ★★★ **매크로는 인자를 글자로 옮긴다** — `SQ1(1+2)` 는 `1+2 * 1+2` = 1 + 2 + 2 = **5**. 곱셈이 먼저다.
- ★★★ **바깥 괄호가 없으면 쓰는 자리의 연산자가 첫 인자에만 붙는다** — `100/(3) * (3)` 은 `(100/3) * 3` = 33 × 3 = **99**, `~(3) * (3)` 은 `(~3) * 3` = −4 × 3 = **−12**.
- ★★ **`SQ(-3)` 은 세 판 다 9, `!SQ(3)`·`!SQ(-3)` 은 세 판 다 0** — 틀린 매크로도 **우연히** 맞는다(`-3 * -3` 은 9, `!3 * 3` 은 0 × 3). 틀린 두 매크로의 24칸 중 **10칸이 맞는 값**이었다.
- ★★★ **경고 0** — 틀린 칸도 전부 적법한 식이다. **gcc 와 clang 은 한 글자도 같다** — 치환과 우선순위는 표준이다.

### 2. `SQ3(i++)` — **gcc `-Wsequence-point` · clang `-Wunsequenced` · UBSan 은 두 컴파일러 다 0줄** ★★★

**출력**

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

**왜 그런가**

- ★★★ `((i++) * (i++))` 는 **같은 스칼라를 순서 없이 두 번 수정**한다 — N3220 식 절 「스칼라 객체의 부작용이 다른 부작용과 순서가 없으면 **미정의**」. ★★★ **그래서 값을 싣지 않는다.**
- ★★★ **컴파일러 경고가 유일한 창**이다 — gcc 는 `note: in definition of macro ‘SQ3’` 로 매크로 안의 두 번째 `x` 를 짚고, clang 은 `expanded from macro 'SQ3'` 로 두 `x` 를 `^ ~` 로 짚는다.
- ★★★ **UBSan 에는 순서 없는 수정을 보는 검사가 없다** — 두 컴파일러 다 stderr 0줄 · `run exit=0`.
- ★★ 표준 출력은 함수 쪽 `sq(j++) = 4 · j = 3` 뿐 — 함수는 인자를 **한 번** 평가한다.

### 3. 함수 호출 인자 — **`SQ3` 는 calls = 2 · 문장 식과 함수는 1 · 값은 셋 다 9 · 문장 식은 `-pedantic` 경고** ★★★

**출력**

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

**왜 그런가**

- ★★★ `((next()) * (next()))` — **함수 호출 두 번은 정의된 동작**이다(순서만 미명시). 두 번 다 3 을 돌려줘 값은 9, **`calls` 는 2**.
- ★★ **문장 식은 인자를 지역 변수에 한 번 담는다** → `calls = 1`. 함수도 1.
- ★★ **`({ })` 는 GNU 확장** — gcc 「ISO C forbids braced-groups within expressions [-Wpedantic]」, clang 「use of GNU statement expression extension from macro expansion」. **`-std=gnu17` 이면 0줄**(`cc exit=0`).

### 4. 두 문장 매크로를 `if` 에 — **`[2] a` 와 `end` · gcc 만 `-Wmultistatement-macros`** ★★★

**출력**

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

**왜 그런가**

- ★★★ `if (argc > 5) puts("[1] " "a"); puts("[2] " "a");` — **`if` 는 첫 문장에만** 걸린다. 두 번째 `puts` 는 무조건 돈다.
- ★★ **gcc 는 `-Wall` 안의 `-Wmultistatement-macros` 로 경고**, **clang 은 0줄**.

### 5. 중괄호 매크로와 `else` — **에러 · 30열 · `};` 의 `;` 가 `if` 문을 끝낸다** ★★★

**출력**

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

```text
===== gcc -std=c17 -E -P s42e.c | sed -n '/^int main/,$p' (cc exit=0) =====
int main(int argc, char **argv) {
    (void)argv;
    if (argc > 5) { puts("[1] " "b"); puts("[2] " "b"); }; else puts("[else] b");
    return 0;
}
```

**왜 그런가**

- ★★★ `if (argc > 5) { … }; else …` — `{ … }` 로 `if` 문이 끝나고 **`;` 가 빈 문장**이 되어 `else` 가 **짝을 잃는다.** gcc 「‘else’ without a previous ‘if’」, clang 「expected expression」 — 둘 다 **30열**(`else` 자리).

### 6. 매크로와 같은 이름의 함수 — **`2 4 6` · 매크로로 펼쳐지는 것은 `max(1, 2)` 하나** ★★

**출력**

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

**왜 그런가**

- ★★ N3220 — 함수형 매크로 이름은 **다음 토큰이 `(` 일 때만** 호출이다. `(max)(3, 4)` 는 `max` 뒤가 `)`, `fp = max` 는 뒤가 `;` — 둘 다 **함수 `max`** 로 남는다.

### 7. 여러 문장 매크로의 세 모양 — **`do { … } while (0)` 만 문장 하나로 붙는다** (왜) ★★★

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s42f.c -o x ; ./x (cc exit=0 · run exit=0) =====
[else] c
[1] d
[2] d
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s42f.c -o /dev/null && clang -std=c17 -Wall -Wextra -pedantic -c s42f.c -o /dev/null (cc exit=0) =====
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

- ★★★ **`do { … } while (0)` 은 끝에 `;` 가 필요한 문장 하나**다 — 쓰는 쪽의 `;` 가 그 자리를 채워 **정확히 한 문장**이 된다. `if` 에 걸리면 **몸통 전체**가 걸리고(4번의 문제 해결), `;` 뒤에 빈 문장이 안 생겨 `else` 가 **제자리**다(5번의 문제 해결).
- ★★ **치환 목록 끝에 `;` 를 넣으면** `while (0);` + `;` = 문장 둘 → `else` 가 고아가 되어 **5번과 같은 에러**(두 컴파일러, 30열).

### 8. 문장 식은 ISO 가 아니다 (경계) ★★

- ★★ **컴파일러 구현(GNU 확장)** 이다 — 3번의 `-pedantic` 경고 두 가지 · gnu 모드 0줄.
- ★★ 문장 식 안의 `v_` 가 **인자의 `v_` 를 가린다** — `SQ4(v_)` 는 `__typeof__(v_) v_ = (v_);` 가 되어 **초기화 중인 자기 자신**을 읽는다. C 매크로에는 위생이 없다.

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

```c
/* s42k.c */
#define SQ4(x) ({ __typeof__(x) v_ = (x); v_ * v_; })

int caller(void) {
    int v_ = 3;
    return SQ4(v_);
}
```

- ★★ **clang 은 `-Wuninitialized` 로 짚고, gcc 는 `-O0` 에서 0줄**이다(18-A). 밑줄 붙은 이름은 **충돌을 드물게 할 뿐 막지 못한다.**

### 9. `static inline` 으로 바꾸면 — **`sq(2.5)` 는 조용히 4 · `-Wconversion` 이라야 보인다 · 포인터는 매크로 쪽이 에러** (왜) ★★

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

```c
/* s42h.c */
#define SQ3(x) ((x) * (x))

static inline int sq(int x) { return x * x; }

int *p;

int by_func(void)  { return sq(p); }
int by_macro(void) { return SQ3(p); }
```

- ★★ **함수는 인자를 매개변수 타입(`int`)으로 바꾼다** — 2.5 → 2 → 4. 매크로는 `double` 그대로 6.25. **`-Wall -Wextra -pedantic` 은 0줄**, `-Wconversion` 이 `-Wfloat-conversion` 을 낸다.
- ★★ **포인터** — `SQ3(p)` 는 **두 컴파일러 다 에러**(`invalid operands`). `sq(p)` 는 **gcc 경고(`-Wint-conversion`) · clang 에러**. 연산자가 못 받는 타입이면 **매크로도 에러**다 — 「매크로는 조용하다」는 여기서 틀렸다.
- ★ **얻는 것** = 한 번 평가 · 괄호 불필요 · 명백한 오용 진단. **잃는 것** = 타입 하나에 고정 · 뜻이 바뀌는 변환이 조용할 수 있다.
- ★★★ **속도는 재지 않았다.** 이 편의 주장은 값과 횟수뿐이다.

### 10. C++ `constexpr` · Rust `macro_rules!` (연결) ★★

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic s42x.cpp -o x ; ./x (cc exit=0 · run exit=0) =====
sq(1 + 2) = 9 · sq(i++) = 4 · i = 3
```

```text
===== rustc --edition 2021 s42r.rs -o x (cc exit=0) =====
```

```text
===== rustc --edition 2021 s42r.rs -o x ; ./x (cc exit=0 · run exit=0) =====
sq!(1 + 2) = 9 · 100 / sq!(1 + 2) = 11 · sq!(next()) = 9 · calls = 2
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

- ★★ **C++** — `constexpr` 함수는 `static_assert` 를 통과하고(컴파일 시간 평가) `sq(i++)` 는 4 · `i = 3`(한 번 평가). [C++ 38](../../../cpp/syntax/38-constexpr-consteval-and-constinit/).
- ★★★ **Rust** — `$x:expr` 는 **식 한 덩어리**라 `sq!(1 + 2)` = 9 · `100 / sq!(1 + 2)` = 11 — **괄호 함정을 푼다.** 그러나 `sq!(next())` 는 **calls = 2** — **중복 평가는 못 푼다.**

### 11. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- ★★★ **표준** — 치환 규칙 · 괄호의 결과 · `(name)(…)` · 호출 두 번(정의됨) · 매개변수 변환. **UB** — `SQ3(i++)`. **미명시** — `next() * next()` 의 호출 순서(같은 값을 돌려줘 결과에 안 드러나게 했다). **컴파일러 구현** — `-Wmultistatement-macros`(gcc 만) · 문장 식 · 포인터 인자의 함수 쪽 진단.
- ★★★ **어떤 도구도 말하지 않는다** — 격자의 틀린 14칸은 경고 0. **`-E -P` 를 읽는 사람**만 안다.
- ★★ **clang 만 쓰면** — `if` 밖으로 샌 두 번째 문장(4번)이 안 보인다.

### 12. 경계 (연결) ★

- ★ 시퀀스 포인트 = [10번 형제](../10-evaluation-order-and-sequence-points/) · `static inline` 링크 = [39번 형제](../39-inline-and-c-inline-rules/) · `#`/`##` = [43번 형제](../43-stringizing-and-token-pasting/).
- ★ 매크로가 꼭 필요한 자리 — **호출 자리의 정보**(`__FILE__`·`__LINE__`) · **토큰 조작**(`#`·`##`) · **타입 무관**(여러 타입을 한 이름으로 — 또는 `_Generic`).

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s42a.c` | ★★★ **함정 격자 36칸** · `-E -P` · gcc/clang 대조 | 빌드 2 · 실행 2 · 전처리 1 |
| `s42b.c` | ★★★ 순서 없는 수정 — 경고 2 · UBSan 2 | 진단 2 · 실행 3 |
| `s42c.c` | ★★★ 호출 횟수 · 문장 식 | 실행 1 · 진단 3 |
| `s42d.c`\~`s42f.c` · `s42j.c` | ★★★ 여러 문장 매크로 네 모양 | 실행 2 · 진단 7 · 전처리 2 |
| `s42g.c` · `s42h.c` | ★★ 함수로 바꿨을 때 | 실행 1 · 진단 5 |
| `s42i.c` | ★★ `(max)(…)` | 실행 1 · 전처리 1 |
| `s42k.c` | ★★ 문장 식의 이름 가림 | 진단 2 · 전처리 1 |
| `s42x.cpp` · `s42r.rs` | ★ C++ · Rust 대비 | 실행 2 · 진단 1 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. **이 편의 블록은 정규화 없이 전부 동일**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★ **4번의 경고 유무**(gcc 만) · **9번의 포인터 인자 진단 세기**(gcc 경고 · clang 에러).
- ★★ **2번의 UBSan 침묵** — gcc 13 · clang 18 의 UBSan 판.

**격자의 모든 칸 · 호출 횟수 · `else` 에러 · `(name)(…)` 는 구현 의존이 아니다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — C23 `typeof` 판의 `SQ4` · `SQ4(v_)` 를 gcc `-O2` 로 · 시간 측정(**의도적으로 안 했다**).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **2번의 UBSan** — 순서 없는 수정 검사가 생길 수 있다.
- ★ **4번** — clang 이 `-Wmultistatement-macros` 류를 들여올 수 있다.

## 실행 환경

이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **clang 18.1.3** · **g++ 13.3.0** · **rustc 1.92.0** ·
x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
소스는 `s42a.c`\~`s42k.c` · `s42x.cpp` · `s42r.rs` 이고, 블록은 **전부 캡처 파일에서 조립**했다.\
★★★ **본체 창은 함정 격자** — 매크로 3 × 인자 3 × 쓰는 자리 4, 기준은 함수 `sq()`.
★★ **흔들리는 칸** — 없다. ★★★ **`SQ3(i++)` 의 값은 미정의라 싣지 않는다.**
