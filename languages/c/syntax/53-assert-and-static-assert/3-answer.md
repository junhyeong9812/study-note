# c/syntax/53 — `assert` 와 `static_assert`: 「**`assert` 는 `NDEBUG` 하나에 식째 사라지는 매크로이고, `static_assert` 는 컴파일러가 대신 멈춰 주는 선언이다**」 — 정답

## 이 파일이 다시 싣는 소스

★ 7번은 질문 파일에 소스가 없다 — 여기 싣는다.

```c
/* s53g.c */
#include <assert.h>
#include <stdio.h>
#define NDEBUG

int main(void) {
    int x = 0;
    fprintf(stderr, "[before]\n");
    assert(x == 1);
    fprintf(stderr, "[after]\n");
    return 0;
}
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 부작용이 있는 단언 — **`NDEBUG` 없음 네 칸은 `x = 2` · 있음 네 칸은 `x = 1` · 최적화는 무관 · 실패 0** ★★★

**출력**

```text
===== 부작용이 있는 단언 — 컴파일러 2 × 최적화 2 × NDEBUG 2 (exit=0) =====
컴파일러 최적화 NDEBUG       | 출력
gcc    -O0  (없음)       | x = 2
gcc    -O0  -DNDEBUG     | x = 1
gcc    -O2  (없음)       | x = 2
gcc    -O2  -DNDEBUG     | x = 1
clang  -O0  (없음)       | x = 2
clang  -O0  -DNDEBUG     | x = 1
clang  -O2  (없음)       | x = 2
clang  -O2  -DNDEBUG     | x = 1
x 가 1 로 남은 칸 4 / 8
```

**왜 그런가**

- ★★★ **`NDEBUG` 가 있으면 `assert(...)` 는 `((void)0)`** — `x++` 가 **소스에서 사라진다.** 그래서 `x` 가 1 로 남는다(4 / 8).
- ★★ **단언은 여덟 칸 다 참**(`1 > 0`) — 실패한 칸은 없다. 이 문항이 묻는 것은 참·거짓이 아니라 **평가됐느냐**다.
- ★★ **`-O0`/`-O2` 가 같다** — 지우는 것이 최적화기가 아니라 전처리기이기 때문이다(10번의 전처리 결과).

### 2. 실패하는 단언 — **stdout `start` · stderr `` x: s53b.c:5: take: Assertion `count > 0' failed. `` · `run exit=134` · clang 은 함수 칸이 `int take(int)` · `NDEBUG` 판은 `136`·stderr 0 줄 · 재배치 `1 0 1 0 1 0 2 0`** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s53b.c -o x ; ./x (cc exit=0 · run exit=134) =====
start
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s53b.c -o x ; ./x 2>&1 >/dev/null (cc exit=0 · run exit=134) =====
x: s53b.c:5: take: Assertion `count > 0' failed.
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 s53b.c -o x ; ./x 2>&1 >/dev/null (cc exit=0 · run exit=134) =====
x: s53b.c:5: int take(int): Assertion `count > 0' failed.
```

```text
===== 실패하는 단언 — 컴파일러 2 × 최적화 2 × NDEBUG 2 (objdump -dr 의 __assert_fail 재배치 수 · 실행) (exit=0) =====
컴파일러 최적화 NDEBUG       | __assert_fail 재배치 | 실행
gcc    -O0  (없음)       | 1                    | run exit=134 · stdout start/ · stderr 1줄
gcc    -O0  -DNDEBUG     | 0                    | run exit=136 · stdout start/ · stderr 0줄
gcc    -O2  (없음)       | 1                    | run exit=134 · stdout start/ · stderr 1줄
gcc    -O2  -DNDEBUG     | 0                    | run exit=136 · stdout start/ · stderr 0줄
clang  -O0  (없음)       | 1                    | run exit=134 · stdout start/ · stderr 1줄
clang  -O0  -DNDEBUG     | 0                    | run exit=136 · stdout start/ · stderr 0줄
clang  -O2  (없음)       | 2                    | run exit=134 · stdout start/ · stderr 1줄
clang  -O2  -DNDEBUG     | 0                    | run exit=136 · stdout start/ · stderr 0줄
```

**왜 그런가**

- ★★★ **메시지의 네 칸(식 · 파일 · 줄 · 함수)은 표준이 요구한다** — 양식은 구현 정의다. glibc 는 앞에 **프로그램 이름** `x:` 를 붙인다.
- ★★ **함수 칸** — gcc 는 `take`, clang 은 `int take(int)`. 같은 glibc 매크로인데 **컴파일러가 채운 이름**이 다르다.
- ★★★ **134 = `SIGABRT`** — `abort()`. **`NDEBUG` 판의 136 = `SIGFPE`** — 단언이 사라져 `100 / 0` 이 실행됐다. 단언이 **막고 있던 UB** 가 드러났다.
- ★★ **재배치** — `NDEBUG` 판은 0, gcc 두 판과 clang `-O0` 은 1, clang `-O2` 는 2(8번).

### 3. `static_assert` 격자 — **갈린 줄 7 / 12 · `s53c5.c` 는 gcc `ok` · clang `warning` · gcc 첫 진단은 「expected declaration specifiers or '...' before 'sizeof'」** ★★★

**출력**

```text
===== static_assert 여섯 꼴 — 파일 6 × 컴파일러 2 × -std 3 (exit=0) =====
파일     | 컴파일러 | -std=c11     | -std=c17     | -std=c2x
s53c1    | gcc    | ok           | ok           | ok          
s53c1    | clang  | ok           | ok           | ok          
s53c2    | gcc    | ok           | ok           | ok          
s53c2    | clang  | ok           | ok           | ok          
s53c3    | gcc    | error        | error        | ok          
s53c3    | clang  | error        | error        | ok          
s53c4    | gcc    | warning      | warning      | ok          
s53c4    | clang  | warning      | warning      | ok          
s53c5    | gcc    | ok           | ok           | ok          
s53c5    | clang  | warning      | warning      | ok          
s53c6    | gcc    | error        | error        | ok          
s53c6    | clang  | error        | error        | ok          
(각 칸 -Wall -pedantic -c · error = cc exit 1 · warning = cc exit 0 에 진단 있음)
c11 과 c2x 가 갈린 줄 7 / 12
```

```text
===== gcc -std=c11 -Wall -pedantic -c s53c3.c -o /dev/null (cc exit=1) =====
s53c3.c:1:15: error: expected declaration specifiers or '...' before 'sizeof'
    1 | static_assert(sizeof(int) == 4, "m");
      |               ^~~~~~
s53c3.c:1:33: error: expected declaration specifiers or '...' before string constant
    1 | static_assert(sizeof(int) == 4, "m");
      |                                 ^~~
```

```text
===== gcc -std=c11 -Wall -pedantic -c s53c5.c -o /dev/null (cc exit=0) =====
```

```text
===== clang -std=c11 -Wall -pedantic -c s53c5.c -o /dev/null (cc exit=0) =====
s53c5.c:2:31: warning: '_Static_assert' with no message is a C23 extension [-Wc23-extensions]
    2 | static_assert(sizeof(int) == 4);
      |                               ^
      |                               , ""
1 warning generated.
```

**왜 그런가**

- ★★★ **C11·C17 에서 `static_assert` 는 `<assert.h>` 의 매크로**다 — 헤더 없이 쓰면 **없는 이름**이고, 컴파일러는 그것을 **함수 선언**으로 읽으려다 엉뚱한 에러를 낸다. C23 에서는 **키워드**라 헤더 없이도 된다.
- ★★ **메시지 생략은 C23 부터** — C11·C17 의 `_Static_assert(e)` 는 `-Wpedantic`(gcc) · `-Wc23-extensions`(clang) 경고.
- ★★ **`s53c5.c` 에서 두 컴파일러가 갈렸다** — gcc 는 헤더 매크로를 거친 생략을 **말하지 않는다**(`-pedantic-errors` 에서도 `cc exit=0` — 요약 (5)절). clang 은 짚는다.

### 4. 레이아웃 가정 검사 — **셋째 단언(`sizeof == 7`)이 멈춘다 · clang 은 식과 값(`12 == 7`)까지 · `f` 안은 「상수가 아니다」 에러** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s53d.c -o /dev/null (cc exit=1) =====
s53d.c:8:1: error: static assertion failed: "header must be 7 bytes"
    8 | _Static_assert(sizeof(struct Header) == 7, "header must be 7 bytes");
      | ^~~~~~~~~~~~~~
s53d.c: In function 'f':
s53d.c:11:22: error: expression in static assertion is not constant
   11 |     _Static_assert(n == 4, "n");
      |                    ~~^~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s53d.c -o /dev/null (cc exit=1) =====
s53d.c:8:16: error: static assertion failed due to requirement 'sizeof(struct Header) == 7': header must be 7 bytes
    8 | _Static_assert(sizeof(struct Header) == 7, "header must be 7 bytes");
      |                ^~~~~~~~~~~~~~~~~~~~~~~~~~
s53d.c:8:38: note: expression evaluates to '12 == 7'
    8 | _Static_assert(sizeof(struct Header) == 7, "header must be 7 bytes");
      |                ~~~~~~~~~~~~~~~~~~~~~~^~~~
s53d.c:11:20: error: static assertion expression is not an integral constant expression
   11 |     _Static_assert(n == 4, "n");
      |                    ^~~~~~
2 errors generated.
```

**왜 그런가**

- ★★ **`struct Header` 는 12 바이트** — 멤버 합 7 에 패딩 5([22번 형제](../22-struct-padding-and-alignment/)). `offsetof(…, len) == 4` 는 **통과**했다.
- ★★ **gcc 는 메시지 문자열만 · clang 은 「due to requirement」+ 식 + 값** — 같은 실패의 두 양식.
- ★ **`n == 4` 는 상수식이 아니다** — 정적 단언은 **컴파일 때 알 수 있는 값**만 받는다.

### 5. `assert` 를 함수처럼 — **둘 다 「없는 이름」 에러 · 고친 제안은 둘 다 틀렸다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s53e.c -o /dev/null (cc exit=1) =====
s53e.c: In function 'main':
s53e.c:4:26: error: 'assert' undeclared (first use in this function)
    4 |     void (*check)(int) = assert;
      |                          ^~~~~~
s53e.c:2:1: note: 'assert' is defined in header '<assert.h>'; did you forget to '#include <assert.h>'?
    1 | #include <assert.h>
  +++ |+#include <assert.h>
    2 | 
s53e.c:4:26: note: each undeclared identifier is reported only once for each function it appears in
    4 |     void (*check)(int) = assert;
      |                          ^~~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s53e.c -o /dev/null (cc exit=1) =====
s53e.c:4:26: error: use of undeclared identifier 'assert'; did you mean '__assert'?
    4 |     void (*check)(int) = assert;
      |                          ^~~~~~
      |                          __assert
/usr/include/assert.h:81:13: note: '__assert' declared here
   81 | extern void __assert (const char *__assertion, const char *__file, int __line)
      |             ^
s53e.c:4:12: error: incompatible function pointer types initializing 'void (*)(int)' with an expression of type 'void (const char *, const char *, int) __attribute__((noreturn))' [-Wincompatible-function-pointer-types]
    4 |     void (*check)(int) = assert;
      |            ^             ~~~~~~
2 errors generated.
```

**왜 그런가**

- ★★ **함수형 매크로는 `(` 가 뒤따를 때만 펼쳐진다** — `= assert;` 의 `assert` 는 매크로가 아니라 **선언 안 된 이름**이다. 표준도 「실제 함수로 구현하지 말라」고 적는다.
- ★★ **gcc 는 「`<assert.h>` 를 포함하라」**(이미 포함했다) · **clang 은 「`__assert` 인가」**(glibc 내부 함수 — 서명이 안 맞아 둘째 에러). **제안을 따르면 안 된다.**

### 6. 쉼표가 든 단언 — **`-std=c17` · `-std=c2x` 둘 다 에러 · 표준(C23)은 `assert(...)` 를 요구 · 이 판의 glibc 와 맞지 않는다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s53f.c -o /dev/null (cc exit=1) =====
s53f.c: In function 'main':
s53f.c:6:37: error: macro "assert" passed 2 arguments, but takes just 1
    6 |     assert((struct P){ 1, 2 }.x == 1);
      |                                     ^
In file included from s53f.c:1:
/usr/include/assert.h:108: note: macro "assert" defined here
  108 | #  define assert(expr)                                                  \
      | 
s53f.c:6:5: error: 'assert' undeclared (first use in this function)
    6 |     assert((struct P){ 1, 2 }.x == 1);
      |     ^~~~~~
s53f.c:2:1: note: 'assert' is defined in header '<assert.h>'; did you forget to '#include <assert.h>'?
    1 | #include <assert.h>
  +++ |+#include <assert.h>
    2 | 
s53f.c:6:5: note: each undeclared identifier is reported only once for each function it appears in
    6 |     assert((struct P){ 1, 2 }.x == 1);
      |     ^~~~~~
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic -c s53f.c -o /dev/null (cc exit=1) =====
s53f.c: In function 'main':
s53f.c:6:37: error: macro "assert" passed 2 arguments, but takes just 1
    6 |     assert((struct P){ 1, 2 }.x == 1);
      |                                     ^
In file included from s53f.c:1:
/usr/include/assert.h:108: note: macro "assert" defined here
  108 | #  define assert(expr)                                                  \
      | 
s53f.c:6:5: error: 'assert' undeclared (first use in this function)
    6 |     assert((struct P){ 1, 2 }.x == 1);
      |     ^~~~~~
s53f.c:2:1: note: 'assert' is defined in header '<assert.h>'; did you forget to '#include <assert.h>'?
    1 | #include <assert.h>
  +++ |+#include <assert.h>
    2 | 
s53f.c:6:5: note: each undeclared identifier is reported only once for each function it appears in
    6 |     assert((struct P){ 1, 2 }.x == 1);
      |     ^~~~~~
```

```text
===== clang -std=c2x -Wall -Wextra -pedantic -c s53f.c -o /dev/null (cc exit=1) =====
s53f.c:6:27: error: too many arguments provided to function-like macro invocation
    6 |     assert((struct P){ 1, 2 }.x == 1);
      |                           ^
/usr/include/assert.h:108:11: note: macro 'assert' defined here
  108 | #  define assert(expr)                                                  \
      |           ^
s53f.c:6:5: note: parentheses are required around macro argument containing braced initializer list
    6 |     assert((struct P){ 1, 2 }.x == 1);
      |     ^                               
      |            (                        )
1 error generated.
```

```text
===== grep -n -E 'define assert\(|define static_assert|__STDC_VERSION__ <= 201710L' /usr/include/assert.h | expand (exit=0) =====
50:# define assert(expr)                (__ASSERT_VOID_CAST (0))
102:#  define assert(expr)                                                      \
108:#  define assert(expr)                                                      \
118:#  define assert(expr)                                                      \
154:     || __STDC_VERSION__ <= 201710L         \
158:# define static_assert _Static_assert
```

**왜 그런가**

- ★★ **`{ 1, 2 }` 의 쉼표**가 매크로 인자를 가른다 — 중괄호는 쉼표를 보호하지 않는다.
- ★★ **C23 의 해법은 가변 인자 `assert(...)`** — 표준이 「ellipsis parameter 가 있는 매크로로」라고 적는다. 그런데 **이 판의 glibc 는 `define assert(expr)`** — 인자 하나뿐이라 `-std=c2x` 에서도 같은 에러다. clang 의 제안(한 겹 더 괄호)이 이 판의 해법이다.

### 7. `#define NDEBUG` 를 `#include` 뒤에 — **사라지지 않는다 · 「included 되는 자리에서」 · 「포함될 때마다 다시 정의」** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -E -P s53g.c | grep -F 'x == 1' (cc exit=0) =====
    ((x == 1) ? (void) (0) : __assert_fail ("x == 1", "s53g.c", 8, __extension__ __PRETTY_FUNCTION__));
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s53g.c -o x ; ./x 2>&1 >/dev/null (cc exit=0 · run exit=134) =====
[before]
x: s53g.c:8: main: Assertion `x == 1' failed.
```

**왜 그런가**

- ★★ **`NDEBUG` 는 `<assert.h>` 가 읽힐 때 본다** — 「If NDEBUG is defined as a macro name **at the point in the source file where `<assert.h>` is included**」. 헤더를 지나간 뒤의 `#define` 은 이미 정의된 `assert` 를 바꾸지 않는다. 전처리 결과에 `__assert_fail` 이 그대로 있고, 실행은 `134` 로 멈춘다.

### 8. 재배치 수를 함수 목록으로 읽기 — **gcc 는 실패 경로를 `take.part.0` 하나로 · clang `-O2` 는 `take` 와 `main`(인라인 사본)에 하나씩** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -c s53b.c -o b.o && objdump -dr --no-show-raw-insn -M intel b.o | grep -E '^[0-9a-f]+ <|R_X86_64_PLT32|idiv' | expand (exit=0) =====
0000000000000000 <take.part.0>:
                        21: R_X86_64_PLT32      __assert_fail-0x4
0000000000000030 <take>:
  3f:   idiv   edi
0000000000000000 <main>:
                        18: R_X86_64_PLT32      setvbuf-0x4
                        2b: R_X86_64_PLT32      __printf_chk-0x4
  44:   idiv   edi
                        50: R_X86_64_PLT32      __printf_chk-0x4
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 -c s53b.c -o b.o && objdump -dr --no-show-raw-insn -M intel b.o | grep -E '^[0-9a-f]+ <|R_X86_64_PLT32|idiv' | expand (exit=0) =====
0000000000000000 <take>:
                        2a: R_X86_64_PLT32      __assert_fail-0x4
0000000000000030 <main>:
                        47: R_X86_64_PLT32      setvbuf-0x4
                        53: R_X86_64_PLT32      puts-0x4
                        73: R_X86_64_PLT32      printf-0x4
                        96: R_X86_64_PLT32      __assert_fail-0x4
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -DNDEBUG -c s53b.c -o b.o && objdump -dr --no-show-raw-insn -M intel b.o | grep -E '^[0-9a-f]+ <|R_X86_64_PLT32|idiv' | expand (exit=0) =====
0000000000000000 <take>:
   b:   idiv   edi
0000000000000000 <main>:
                        18: R_X86_64_PLT32      setvbuf-0x4
                        2b: R_X86_64_PLT32      __printf_chk-0x4
  39:   idiv   edi
                        4c: R_X86_64_PLT32      __printf_chk-0x4
```

**왜 그런가**

- ★★ **gcc `-O2`** — `take` 의 드문 경로(단언 실패)를 **`take.part.0`** 으로 떼어 냈다(부분 인라인). `__assert_fail` 재배치는 그 함수에 **하나**다.
- ★★ **clang `-O2`** — `main` 이 `take` 를 인라인하면서 **실패 경로까지 사본을 가졌다.** `take` 와 `main` 에 하나씩 **둘**이다.
- ★★ **`NDEBUG` 판** — `take.part.0` 도 `__assert_fail` 도 없다. `idiv` 만 남았다.

### 9. 층 — **형식은 구현 정의 · 네 칸(식 · 파일 · 줄 · 함수)은 표준 · C23 요구는 컴파일러(키워드)와 C 라이브러리(`assert.h`) 둘 다의 몫** ★★★

**왜 그런가**

- ★★★ 표준 — 「writes information about the particular invocation that failed (**including the text of the argument, the name of the source file, the source line number, and the name of the enclosing function**) … **in an implementation-defined format**. It then calls the abort function.」
- ★★ **`static_assert` 키워드 · 메시지 생략은 컴파일러의 일** — 두 컴파일러 다 `-std=c2x` 에서 받았다. **가변 인자 `assert` 는 `<assert.h>` — 곧 C 라이브러리의 일** — 이 판의 glibc 2.39 가 아직 안 했다. 같은 「C23 지원」이 **두 주체에 나뉘어** 있다.

### 10. 41 · 42 · 43번 형제와 이어서 — **없으면 삼항식 + `__assert_fail("x++ > 0", …)` · 있으면 `((void) (0));` · 메시지 글자는 `#` 문자열화** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -E -P s53a.c | grep -F 'x++' (cc exit=0) =====
    ((x++ > 0) ? (void) (0) : __assert_fail ("x++ > 0", "s53a.c", 7, __extension__ __PRETTY_FUNCTION__));
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -E -P -DNDEBUG s53a.c | grep -n -A1 'int x = argc' (cc exit=0) =====
219:    int x = argc;
220-    ((void) (0));
```

**왜 그런가**

- ★★ **`NDEBUG` 판의 `int x = argc;` 다음 줄은 `((void) (0));`** — 식의 흔적이 없다. [41번 형제](../41-preprocessor-directives-and-conditional-compilation/)가 `gcc -E` 로 읽는 법의 정본이다.
- ★ **`"x++ > 0"`** 은 매크로 인자를 `#` 로 문자열로 만든 것이다([43번 형제](../43-stringizing-and-token-pasting/)). 인자를 **글자로** 받는다는 것은 [42번 형제](../42-function-like-macro-pitfalls/)의 주제다 — 6번의 쉼표도 그 뿌리다.

### 11. 다른 갈래의 단언과 — **Rust `assert!` 는 남고 `debug_assert!` 만 사라진다 · C `assert` 는 `debug_assert!` 쪽 · Kotlin `assert` 는 `-ea` 를 줘야 울린다(기본 꺼짐)** ★★

**왜 그런가**

- ★★ [Rust 갈래 23번](../../../rust/syntax/23-panic-vs-result/) (7)절 — 기본 빌드에서 `debug_assert!` 가 터져 **종료 코드 101**, `-O` 에서는 **검사가 사라져 0**. `assert!` 는 `-O` 에서도 남는다. C 의 `assert` 는 **릴리스(`NDEBUG`)에서 사라지는 쪽** — `debug_assert!` 에 해당하고, `assert!` 에 해당하는 표준 매크로는 없다.
- ★ [Kotlin 갈래 51번](../../../kotlin/syntax/51-preconditions-require-check-error-todo/) — `assert` KDoc 「runtime assertions have been enabled on the JVM using the **-ea** JVM option」. **기본이 꺼짐 · 켜는 스위치**다. C 는 **기본이 켜짐 · 끄는 스위치(`NDEBUG`)** 다. 늘 켜진 검사는 Kotlin 의 `require`·`check`, C 의 `if` 다.

### 12. 다섯 층과 네 번째 창 ★★★

**왜 그런가**

- **표준** — `NDEBUG` → `((void)0)` · 포함될 때마다 재정의 · 실패 시 표준 오류 + `abort` · 메시지의 네 칸 · `assert` 는 함수가 아니다 · `_Static_assert` 는 상수식 · C23 의 키워드 · 생략 · 가변 인자.
- **구현 정의** — 메시지 양식 · `abort` 의 종료 방식.
- **컴파일러·glibc 구현** — 함수 칸 · 실패 경로 분리 · glibc 2.39 의 인자 하나 · gcc 의 헤더 매크로 진단 억제 · 엉뚱한 진단 문구.
- **미명시** — 해당 없음.
- **UB** — 매크로를 억눌러 함수에 닿기 · `NDEBUG` 판에서 드러난 `100 / 0`.
- ★★★ **네 번째 창 = 전처리 결과(`gcc -E -P`).** 「사라졌나」를 **실행도 어셈블리도 아닌 글자**로 답한다. 못 보는 것 — **그 뒤에 컴파일러가 한 일**(인라인 · 실패 경로 분리)은 안 보인다 — 그것은 재배치 창(8번)의 몫이다.

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s53a.c` | ★★★ **`NDEBUG` 격자 4 / 8** · 전처리 두 판 | 빌드 10 · 실행 10 · `-E` 2 |
| `s53b.c` | ★★★ 메시지 두 컴파일러 · 종료 코드 · 재배치 격자 · 덤프 셋 | 빌드 19 · 실행 11 · 덤프 3 |
| `s53c1.c`\~`s53c6.c` | ★★★ **`static_assert` 격자 7 / 12** · 진단 넷 | 진단 42 |
| `s53d.c` | ★★ 레이아웃 가정 · 상수 아닌 식 | 진단 2 |
| `s53e.c` | ★★ `assert` 를 함수처럼 | 진단 2 |
| `s53f.c` | ★★ 쉼표 · c17 · c2x · 헤더 | 진단 3 · `grep` 1 |
| `s53g.c` | ★★ 뒤늦은 `NDEBUG` | `-E` 1 · 실행 1 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. 이 편은 흔들린 칸이 없어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **2번의 메시지 양식 · 함수 칸** — glibc 와 두 컴파일러.
- ★★★ **6번** — glibc 2.39 의 `assert` 정의.
- ★★ **3번의 `s53c5.c` gcc 칸 · 8번의 함수 목록** — 컴파일러의 판단.

**`NDEBUG` 가 `assert` 를 `((void)0)` 으로 만드는 것 · 실패 시 `abort` · 메시지의 네 칸 · `_Static_assert` 가 상수식을 요구하는 것 · C11/C17 에서 `static_assert` 가 헤더 매크로라는 것은 구현 의존이 아니다.**\
어느 C 구현에서도 같다(판 안에서).

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — 구조체 안의 `static_assert` · `NDEBUG` 판의 `-Wunused-variable` · clang 의 `-E` 결과 · 한 겹 더 괄호로 감싼 6번.
- ★ **부적용** — sanitizer · 시간 측정.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **6번** — glibc 가 `assert(...)` 를 가변 인자로 바꾸는 판.
- ★★ **3번** — `-std=c23` 이 기본이 되는 판 · gcc 의 헤더 매크로 진단.
- ★ **2번 · 8번** — 메시지 양식과 인라인 판단.

## 실행 환경

이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **clang 18.1.3** · **glibc 2.39** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
소스는 `s53a.c` · `s53b.c` · `s53c1.c`\~`s53c6.c` · `s53d.c`\~`s53g.c` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
★★★ **본체 창은 `NDEBUG` 격자** — 컴파일러 2 × 최적화 2 × `NDEBUG` 2.
★★ **흔들리는 칸** — 없다.
