# c/syntax/34 — 함수 선언·정의·프로토타입: 「**빈 괄호는 C17 에서 「모른다」, C23 에서 「없다」**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **gcc-12 (Ubuntu 12.4.0-2ubuntu1\~24.04.1) 12.4.0** ·
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 소스는 `s34a.c`\~`s34m2.c` · `s34x.cpp` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
> ★★★ **판 격자** — 1·2·3번은 컴파일러 3 × `-std=c17`/`-std=c2x`, 4번은 × 판 4 × 강도 2.
> ★★ **흔들리는 칸은 없다** — 5번의 틀린 값은 **참/거짓으로** 찍었다. 정규화 규칙은 기본 넷뿐이고 이 편에서는 걸리는 칸이 없다.

## 이 파일이 다시 싣는 소스

★ 5번의 격자·sanitizer 블록은 **소스 줄을 끼워 보여 주지 않는다** — 그 블록이 가리키는 소스를 여기 한 번 더 싣는다(질문 파일의 것과 같다).

```c
/* s34e1.c */
#include <stdio.h>

double half_f();                  /* 괄호 안이 비었다 */
double half_d();

int main(void) {
    float v = 3.0f;
    printf("half_f(v) == 1.5 ? %s\n", half_f(v) == 1.5 ? "yes" : "no");
    printf("half_d(v) == 1.5 ? %s\n", half_d(v) == 1.5 ? "yes" : "no");
    return 0;
}
```

```c
/* s34e2.c */
double half_f(float x)  { return x / 2; }
double half_d(double x) { return x / 2; }
```

```c
/* s34e3.c */
#include <stdio.h>

double half_f(double);            /* 프로토타입을 적었다 — 정의와 다르게 */
double half_d(double);

int main(void) {
    float v = 3.0f;
    printf("half_f(v) == 1.5 ? %s\n", half_f(v) == 1.5 ? "yes" : "no");
    printf("half_d(v) == 1.5 ? %s\n", half_d(v) == 1.5 ? "yes" : "no");
    return 0;
}
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 빈 괄호 + `f(1, 2)` — **C17 은 셋 다 통과(gcc 경고 0) · C23 은 gcc 13·clang 에러 · ★ gcc-12 는 C23 에서도 통과** ★★★

**출력**

```text
===== 빈 괄호와 옛 정의 — 파일 4 × 컴파일러 3 × 판 2 (exit=0) =====
파일     컴파일러 -std=c17 -pedantic         | -std=c2x -pedantic
s34v.c   gcc-12   exit=0 경고 0 에러 0       | exit=0 경고 0 에러 0
s34v.c   gcc      exit=0 경고 0 에러 0       | exit=0 경고 0 에러 0
s34v.c   clang    exit=0 경고 0 에러 0       | exit=0 경고 0 에러 0
s34a.c   gcc-12   exit=0 경고 0 에러 0       | exit=0 경고 0 에러 0
s34a.c   gcc      exit=0 경고 0 에러 0       | exit=1 경고 0 에러 2
s34a.c   clang    exit=0 경고 3 에러 0       | exit=1 경고 0 에러 2
s34b.c   gcc-12   exit=0 경고 0 에러 0       | exit=0 경고 1 에러 0
s34b.c   gcc      exit=0 경고 0 에러 0       | exit=0 경고 1 에러 0
s34b.c   clang    exit=0 경고 1 에러 0       | exit=1 경고 0 에러 4
s34c.c   gcc-12   exit=1 경고 0 에러 1       | exit=1 경고 0 에러 1
s34c.c   gcc      exit=1 경고 0 에러 1       | exit=1 경고 0 에러 1
s34c.c   clang    exit=1 경고 2 에러 1       | exit=1 경고 0 에러 1
(격자 플래그 = -Wall -Wextra -pedantic -fmax-errors=0 / clang 은 -ferror-limit=0)
두 판의 종료 코드가 갈린 칸 3 / 12
```

```text
===== 같은 두 파일을 -pedantic-errors 로 — 판 c2x (exit=0) =====
s34a.c   gcc-12   -std=c2x -pedantic-errors  exit=0 경고 0 에러 0
s34a.c   gcc      -std=c2x -pedantic-errors  exit=1 경고 0 에러 2
s34a.c   clang    -std=c2x -pedantic-errors  exit=1 경고 0 에러 2
s34b.c   gcc-12   -std=c2x -pedantic-errors  exit=1 경고 0 에러 1
s34b.c   gcc      -std=c2x -pedantic-errors  exit=1 경고 0 에러 1
s34b.c   clang    -std=c2x -pedantic-errors  exit=1 경고 0 에러 4
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic -c s34a.c -o /dev/null (cc exit=1) =====
s34a.c: In function ‘main’:
s34a.c:6:30: error: too many arguments to function ‘f’
    6 |     printf("f(1, 2) = %d\n", f(1, 2));
      |                              ^
s34a.c:3:5: note: declared here
    3 | int f();                          /* 괄호 안이 비었다 */
      |     ^
s34a.c: At top level:
s34a.c:10:5: error: conflicting types for ‘f’; have ‘int(int,  int)’
   10 | int f(int a, int b) { return a + b; }
      |     ^
s34a.c:3:5: note: previous declaration of ‘f’ with type ‘int(void)’
    3 | int f();                          /* 괄호 안이 비었다 */
      |     ^
```

```text
===== clang -std=c2x -Wall -Wextra -pedantic -c s34a.c -o /dev/null (cc exit=1) =====
s34a.c:6:32: error: too many arguments to function call, expected 0, have 2
    6 |     printf("f(1, 2) = %d\n", f(1, 2));
      |                              ~ ^~~~
s34a.c:3:5: note: 'f' declared here
    3 | int f();                          /* 괄호 안이 비었다 */
      |     ^
s34a.c:10:5: error: conflicting types for 'f'
   10 | int f(int a, int b) { return a + b; }
      |     ^
s34a.c:3:5: note: previous declaration is here
    3 | int f();                          /* 괄호 안이 비었다 */
      |     ^
2 errors generated.
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s34a.c -o /dev/null (cc exit=0) =====
s34a.c:3:6: warning: a function declaration without a prototype is deprecated in all versions of C [-Wstrict-prototypes]
    3 | int f();                          /* 괄호 안이 비었다 */
      |      ^
      |       void
s34a.c:6:31: warning: passing arguments to 'f' without a prototype is deprecated in all versions of C and is not supported in C23 [-Wdeprecated-non-prototype]
    6 |     printf("f(1, 2) = %d\n", f(1, 2));
      |                               ^
s34a.c:3:5: warning: a function declaration without a prototype is deprecated in all versions of C and is treated as a zero-parameter prototype in C23, conflicting with a subsequent definition [-Wdeprecated-non-prototype]
    3 | int f();                          /* 괄호 안이 비었다 */
      |     ^
s34a.c:10:5: note: conflicting prototype is here
   10 | int f(int a, int b) { return a + b; }
      |     ^
3 warnings generated.
```

```text
===== gcc-12 -std=c2x -Wall -Wextra -pedantic -c s34a.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s34a.c -o x ; ./x (cc exit=0 · run exit=0) =====
f(1, 2) = 3
```

**왜 그런가**

- ★★★ **C17 의 빈 괄호는 「매개변수 정보 없음」** — 인자 검사가 없고, 인자는 승격되어 넘어간다. 그래서 `f(1, 2)` 가 **합법**이고 gcc 는 **경고 0건**, 실행하면 `3` 이다.
- ★★★ **C23 의 빈 괄호는 `void` 하나짜리 목록**이다 — gcc 13 이 **`int(void)`** 라고 직접 적었고, clang 은 **`expected 0, have 2`**. 인자 둘은 제약 위반이고, 뒤의 정의와도 충돌한다(에러 2건).
- ★★★ **gcc-12 는 `-std=c2x` 에서도 옛 뜻** — `-pedantic-errors` 로도 `exit=0`. **그 판은 이 C23 변경을 구현하지 않았다.**
- ★★ **clang 은 C17 에서도 경고 3건** — 그중 하나가 「**C23 에서는 매개변수 0개 프로토타입으로 다뤄져 뒤 정의와 충돌한다**」고 판 경계를 미리 말한다.
- ★ **`s34v.c` 는 모든 칸이 같다** — `void` 를 적으면 판이 상관없다.

### 2. 옛 정의 — **gcc 13 `c2x` 는 경고(`exit=0`) · `-pedantic-errors` 면 에러 · clang `c2x` 는 문법째 모른다** ★★★

**출력**

```text
===== gcc -std=c2x -Wall -Wextra -pedantic -c s34b.c -o /dev/null (cc exit=0) =====
s34b.c: In function ‘g’:
s34b.c:3:5: warning: old-style function definition [-Wold-style-definition]
    3 | int g(a, b)                       /* 매개변수 이름만 적고 */
      |     ^
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic-errors -c s34b.c -o /dev/null (cc exit=1) =====
s34b.c: In function ‘g’:
s34b.c:3:5: error: old-style function definition [-Wold-style-definition]
    3 | int g(a, b)                       /* 매개변수 이름만 적고 */
      |     ^
```

```text
===== gcc -std=c2x s34b.c -o x ; ./x (cc exit=0 · run exit=0) =====
g(3, 4) = 12
```

```text
===== clang -std=c2x -Wall -Wextra -pedantic -c s34b.c -o /dev/null (cc exit=1) =====
s34b.c:3:7: error: unknown type name 'a'
    3 | int g(a, b)                       /* 매개변수 이름만 적고 */
      |       ^
s34b.c:3:10: error: unknown type name 'b'
    3 | int g(a, b)                       /* 매개변수 이름만 적고 */
      |          ^
s34b.c:3:12: error: expected ';' after top level declarator
    3 | int g(a, b)                       /* 매개변수 이름만 적고 */
      |            ^
      |            ;
s34b.c:6:1: error: expected identifier or '('
    6 | {
      | ^
4 errors generated.
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s34b.c -o /dev/null (cc exit=0) =====
s34b.c:3:5: warning: a function definition without a prototype is deprecated in all versions of C and is not supported in C23 [-Wdeprecated-non-prototype]
    3 | int g(a, b)                       /* 매개변수 이름만 적고 */
      |     ^
1 warning generated.
```

**왜 그런가**

- ★★★ **C23 이 식별자 목록 정의를 뺐다** — 그런데 gcc 13 은 **`-Wold-style-definition` 경고**로만 말하고 **실행까지 된다**(`g(3, 4) = 12`). → **「종료 코드 0인데 ill-formed」**
- ★★ **clang 은 C23 에서 그것을 선언으로 읽다 깨진다** — `unknown type name 'a'`(에러 4건). gcc 는 「있지만 싫은 문법」, clang 은 「없는 문법」.
- ★ **C17 에서는** gcc 경고 0 · clang 은 「C23 에서 지원하지 않는다」 경고 1(1번 격자).

### 3. 빈 괄호 + `float` 매개변수 정의 — **두 판 다 에러 · 이유가 다르다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s34c.c -o /dev/null (cc exit=1) =====
s34c.c:3:8: error: conflicting types for ‘half’; have ‘double(float)’
    3 | double half(float x) { return x / 2; }
      |        ^~~~
s34c.c:3:1: note: an argument type that has a default promotion cannot match an empty parameter name list declaration
    3 | double half(float x) { return x / 2; }
      | ^~~~~~
s34c.c:1:8: note: previous declaration of ‘half’ with type ‘double()’
    1 | double half();                    /* 괄호 안이 비었다 */
      |        ^~~~
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic -c s34c.c -o /dev/null (cc exit=1) =====
s34c.c:3:8: error: conflicting types for ‘half’; have ‘double(float)’
    3 | double half(float x) { return x / 2; }
      |        ^~~~
s34c.c:1:8: note: previous declaration of ‘half’ with type ‘double(void)’
    1 | double half();                    /* 괄호 안이 비었다 */
      |        ^~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s34c.c -o /dev/null (cc exit=1) =====
s34c.c:1:12: warning: a function declaration without a prototype is deprecated in all versions of C [-Wstrict-prototypes]
    1 | double half();                    /* 괄호 안이 비었다 */
      |            ^
      |             void
s34c.c:1:8: warning: a function declaration without a prototype is deprecated in all versions of C and is treated as a zero-parameter prototype in C23, conflicting with a subsequent definition [-Wdeprecated-non-prototype]
    1 | double half();                    /* 괄호 안이 비었다 */
      |        ^
s34c.c:3:8: note: conflicting prototype is here
    3 | double half(float x) { return x / 2; }
      |        ^
s34c.c:3:8: error: conflicting types for 'half'
    3 | double half(float x) { return x / 2; }
      |        ^
s34c.c:1:8: note: previous declaration is here
    1 | double half();                    /* 괄호 안이 비었다 */
      |        ^
2 warnings and 1 error generated.
```

**왜 그런가**

- ★★★ **C17 — 승격 때문이다** — gcc 의 `note`: 「**기본 승격이 있는 인자 타입은 빈 매개변수 이름 목록 선언과 맞을 수 없다**」. 빈 괄호로 부르면 `float` 은 `double` 로 넘어오므로, `float` 을 받는 정의는 **그 선언과 호환되지 않는다.**
- ★★ **C23 — 개수 때문이다** — `previous declaration ... 'double(void)'`. 매개변수 0개 대 1개.
- ★ **`cc exit=1` 은 같고 이유가 다르다** — 판 격자의 「안 갈린 칸」도 문구를 읽어야 판 경계가 보인다.

### 4. 선언 없이 부르기 — **gcc 12·13 은 모든 판에서 경고(`-pedantic` `exit=0`) · clang 은 C99 이후 에러 · C89 는 합법** ★★★

**출력**

```text
===== 선언 없이 부르기 — 컴파일러 3 × 판 4 × 두 강도 (-Wall -Wextra) (exit=0) =====
컴파일러 판     -pedantic              | -pedantic-errors
gcc-12   c89    exit=0 경고 1 에러 0   | exit=0 경고 1 에러 0
gcc-12   c99    exit=0 경고 1 에러 0   | exit=1 경고 0 에러 1
gcc-12   c17    exit=0 경고 1 에러 0   | exit=1 경고 0 에러 1
gcc-12   c2x    exit=0 경고 1 에러 0   | exit=1 경고 0 에러 1
gcc      c89    exit=0 경고 1 에러 0   | exit=0 경고 1 에러 0
gcc      c99    exit=0 경고 1 에러 0   | exit=1 경고 0 에러 1
gcc      c17    exit=0 경고 1 에러 0   | exit=1 경고 0 에러 1
gcc      c2x    exit=0 경고 1 에러 0   | exit=1 경고 0 에러 1
clang    c89    exit=0 경고 1 에러 0   | exit=0 경고 1 에러 0
clang    c99    exit=1 경고 0 에러 1   | exit=1 경고 0 에러 1
clang    c17    exit=1 경고 0 에러 1   | exit=1 경고 0 에러 1
clang    c2x    exit=1 경고 0 에러 1   | exit=1 경고 0 에러 1
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s34d.c -o /dev/null (cc exit=0) =====
s34d.c: In function ‘main’:
s34d.c:4:28: warning: implicit declaration of function ‘sq’ [-Wimplicit-function-declaration]
    4 |     printf("sq(3) = %d\n", sq(3));  /* 이 줄 위에 sq 의 선언이 없다 */
      |                            ^~
```

```text
===== gcc -std=c89 -pedantic -c s34d.c -o /dev/null (cc exit=0) =====
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s34d.c -o /dev/null (cc exit=1) =====
s34d.c:4:28: error: call to undeclared function 'sq'; ISO C99 and later do not support implicit function declarations [-Wimplicit-function-declaration]
    4 |     printf("sq(3) = %d\n", sq(3));  /* 이 줄 위에 sq 의 선언이 없다 */
      |                            ^
1 error generated.
```

```text
===== clang -std=c2x -Wall -Wextra -pedantic -c s34d.c -o /dev/null (cc exit=1) =====
s34d.c:4:28: error: use of undeclared identifier 'sq'
    4 |     printf("sq(3) = %d\n", sq(3));  /* 이 줄 위에 sq 의 선언이 없다 */
      |                            ^
1 error generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s34d.c -o x ; ./x (cc exit=0 · run exit=0) =====
sq(3) = 9
```

```text
===== command -v gcc-12 gcc-13 gcc-14 gcc-15 (exit=0) =====
/usr/bin/gcc-12
/usr/bin/gcc-13
```

**왜 그런가**

- ★★★ **C99 가 암시적 함수 선언을 뺐다** — 그런데 **gcc 12·13 은 경고로만** 말한다(`-pedantic` 에서 `exit=0`, `-pedantic-errors` 라야 `exit=1`). → **「종료 코드 0인데 ill-formed」**
- ★★★ **clang 은 C99 이후 판에서 에러** — 문구가 「**ISO C99 and later do not support**」로 판을 직접 말한다.
- ★★ **C89 의 경고는 `-Wall` 이 켠 것**이다 — `gcc -std=c89 -pedantic` 만으로는 **0건**. C89 에서는 **합법**이다(그래서 `-pedantic-errors` 에서도 `exit=0`).
- ★★ **clang C23 의 문구는 다르다** — `use of undeclared identifier`. 암시적 선언이라는 **개념이 없는 판**이라 그냥 **모르는 이름**이다.
- ★ **gcc 14 는 확인할 수 없다** — `command -v` 가 `gcc-12`·`gcc-13` 만 찾았다. **못 잰 것**이다.

### 5. 두 번역 단위 — **`half_f` 네 벌 `no` · `half_d` 네 벌 `yes` · gcc 경고 0 · `-flto` 는 빈 괄호 쪽을 못 본다 · sanitizer 0 / 4** ★★★

**출력**

```text
===== 두 번역 단위 — 빈 괄호 선언으로 float 을 넘긴다 (s34e1.c + s34e2.c) (exit=0) =====
--- gcc -O0 (cc exit=0 · 경고 0)
half_f(v) == 1.5 ? no
half_d(v) == 1.5 ? yes
--- gcc -O2 (cc exit=0 · 경고 0)
half_f(v) == 1.5 ? no
half_d(v) == 1.5 ? yes
--- clang -O0 (cc exit=0 · 경고 4)
half_f(v) == 1.5 ? no
half_d(v) == 1.5 ? yes
--- clang -O2 (cc exit=0 · 경고 4)
half_f(v) == 1.5 ? no
half_d(v) == 1.5 ? yes
```

```text
===== -flto 가 두 번역 단위를 견주나 — 호출 쪽 파일 2 × 컴파일러 2 × -flto 유무 (exit=0) =====
s34e1.c + s34e2.c  gcc    (없음)  cc exit=0 · 경고 0 · lto-type-mismatch 0
s34e1.c + s34e2.c  gcc    -flto   cc exit=0 · 경고 0 · lto-type-mismatch 0
s34e1.c + s34e2.c  clang  (없음)  cc exit=0 · 경고 4 · lto-type-mismatch 0
s34e1.c + s34e2.c  clang  -flto   cc exit=0 · 경고 4 · lto-type-mismatch 0
s34e3.c + s34e2.c  gcc    (없음)  cc exit=0 · 경고 0 · lto-type-mismatch 0
s34e3.c + s34e2.c  gcc    -flto   cc exit=0 · 경고 1 · lto-type-mismatch 1
s34e3.c + s34e2.c  clang  (없음)  cc exit=0 · 경고 0 · lto-type-mismatch 0
s34e3.c + s34e2.c  clang  -flto   cc exit=0 · 경고 0 · lto-type-mismatch 0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -flto s34e3.c s34e2.c -o x (cc exit=0) =====
s34e3.c:3:8: warning: type of ‘half_f’ does not match original declaration [-Wlto-type-mismatch]
    3 | double half_f(double);            /* 프로토타입을 적었다 — 정의와 다르게 */
      |        ^
s34e2.c:1:8: note: type mismatch in parameter 1
    1 | double half_f(float x)  { return x / 2; }
      |        ^
s34e2.c:1:8: note: type ‘float’ should match type ‘double’
s34e2.c:1:8: note: ‘half_f’ was previously declared here
s34e2.c:1:8: note: code may be misoptimized unless ‘-fno-strict-aliasing’ is used
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -flto s34e3.c s34e2.c -o x ; ./x (cc exit=0 · run exit=0) =====
half_f(v) == 1.5 ? no
half_d(v) == 1.5 ? yes
```

```text
===== 같은 두 파일을 sanitizer 로 — 컴파일러 2 × sanitizer 2 (-O0 -g) (exit=0) =====
gcc    address    run exit=0 리포트 0줄 | half_f(v) == 1.5 ? no|half_d(v) == 1.5 ? yes|
gcc    undefined  run exit=0 리포트 0줄 | half_f(v) == 1.5 ? no|half_d(v) == 1.5 ? yes|
clang  address    run exit=0 리포트 0줄 | half_f(v) == 1.5 ? no|half_d(v) == 1.5 ? yes|
clang  undefined  run exit=0 리포트 0줄 | half_f(v) == 1.5 ? no|half_d(v) == 1.5 ? yes|
답한 칸 0 / 4
```

**왜 그런가**

- ★★★ **넘어간 것은 `double`, 받은 쪽은 `float`** — 빈 괄호 선언으로 부르면 `v` 는 **기본 인자 승격**으로 `double` 이 된다. `half_f(float)` 는 **다른 것을 읽는다.** **UB** 다(호환되지 않는 타입으로 부른 것).
- ★★★ **`half_d(double)` 는 맞는다** — 승격된 타입과 정의가 같다.
- ★★★ **`-flto` 는 호출 쪽에 서명이 있어야 견준다** — `s34e1`(빈 괄호) 판은 두 컴파일러 **`lto-type-mismatch 0`**. `s34e3`(프로토타입) 판은 gcc 가 **`type mismatch in parameter 1`** 을 낸다 — 그래도 **`cc exit=0`** 이고 실행 값은 여전히 `no` 다. clang `-flto` 는 두 판 다 0.
- ★★ **ASan·UBSan 네 칸 다 침묵** — 틀린 값을 조용히 낸다.
- ★ [25번 형제](../25-incomplete-types-and-opaque-struct/)의 「`-flto` 는 서명을 본다」에 「**양쪽에 서명이 있을 때 · gcc 에서**」라는 조건이 붙는다.

### 6. 호출 쪽 어셈블리 — **빈 괄호 쪽만 `cvtss2sd` 와 `al` 채우기** ★★

**출력**

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s34f.c -o - 2>/dev/null | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand (cc exit=0) =====
via_np:
        endbr64
        mov     eax, 1
        cvtss2sd        xmm0, xmm0
        jmp     take_np@PLT
via_p:
        endbr64
        jmp     take_p@PLT
```

```text
===== clang -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s34f.c -o - 2>/dev/null | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand (cc exit=0) =====
via_np:                                 # @via_np
# %bb.0:
        cvtss2sd        xmm0, xmm0
        mov     al, 1
        jmp     take_np@PLT                     # TAILCALL
.Lfunc_end0:
                                        # -- End function
via_p:                                  # @via_p
# %bb.0:
        jmp     take_p@PLT                      # TAILCALL
.Lfunc_end1:
                                        # -- End function
```

**왜 그런가**

- ★★★ **`cvtss2sd xmm0, xmm0`** — `float` 을 `double` 로 바꾸는 명령. **승격이 명령으로 보인다.** 프로토타입 쪽(`via_p`)은 `float` 그대로 `jmp`.
- ★★ **`mov eax, 1`(gcc) · `mov al, 1`(clang)** — x86-64 호출 규약에서 **가변 인자 함수에 넘긴 벡터 레지스터 수**를 `al` 로 알린다. **프로토타입 없는 호출을 가변 인자 호출처럼 번역**한 것이다. 두 컴파일러 같은 모양이다.

### 7. C++ — **처음부터 `f()` 는 `f(void)` · g++ 는 `too many arguments` · clang++ 는 후보가 안 맞는다** ★★

**출력**

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c s34x.cpp -o /dev/null (cc exit=1) =====
s34x.cpp: In function ‘int main()’:
s34x.cpp:3:22: error: too many arguments to function ‘int f()’
    3 | int main() { return f(1, 2); }
      |                     ~^~~~~~
s34x.cpp:1:5: note: declared here
    1 | int f();
      |     ^
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -c s34x.cpp -o /dev/null (cc exit=1) =====
s34x.cpp:3:21: error: no matching function for call to 'f'
    3 | int main() { return f(1, 2); }
      |                     ^
s34x.cpp:1:5: note: candidate function not viable: requires 0 arguments, but 2 were provided
    1 | int f();
      |     ^
1 error generated.
```

**왜 그런가**

- ★★ **C++ 에서 빈 괄호는 「매개변수 없음」** — C23 과 같은 판정이다. **C23 이 C 를 C++ 쪽으로 옮겼다**고 말할 수 있다.
- ★ **clang++ 의 말투는 오버로드 해석**이다 — 같은 이름의 다른 서명이 있을 수 있는 언어라 「이 후보는 0개를 요구한다」로 말한다.

### 8. `static` 순서 · `main` · noreturn — **링크 충돌 에러 · `void main` 은 구현 정의(gcc 경고 · clang 에러) · `_Noreturn` 은 두 판 0건** ★★

**출력**

```text
===== noreturn 두 꼴 · static 함수의 순서 · main 의 서명 — 파일 5 × 컴파일러 2 × 판 2 (-Wall -Wextra -pedantic) (exit=0) =====
s34g1.c  gcc    c17 exit=0 경고 0 에러 0   | c2x exit=0 경고 0 에러 0
s34g1.c  clang  c17 exit=0 경고 0 에러 0   | c2x exit=0 경고 0 에러 0
s34g2.c  gcc    c17 exit=0 경고 1 에러 0   | c2x exit=0 경고 0 에러 0
s34g2.c  clang  c17 exit=0 경고 1 에러 0   | c2x exit=0 경고 0 에러 0
s34h.c   gcc    c17 exit=1 경고 2 에러 1   | c2x exit=1 경고 2 에러 1
s34h.c   clang  c17 exit=1 경고 0 에러 2   | c2x exit=1 경고 0 에러 1
s34m.c   gcc    c17 exit=0 경고 1 에러 0   | c2x exit=0 경고 1 에러 0
s34m.c   clang  c17 exit=1 경고 0 에러 1   | c2x exit=1 경고 0 에러 1
s34m2.c  gcc    c17 exit=0 경고 0 에러 0   | c2x exit=0 경고 0 에러 0
s34m2.c  clang  c17 exit=0 경고 0 에러 0   | c2x exit=0 경고 0 에러 0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s34h.c -o /dev/null (cc exit=1) =====
s34h.c: In function ‘main’:
s34h.c:1:25: warning: implicit declaration of function ‘helper’ [-Wimplicit-function-declaration]
    1 | int main(void) { return helper(); }
      |                         ^~~~~~
s34h.c: At top level:
s34h.c:3:12: error: static declaration of ‘helper’ follows non-static declaration
    3 | static int helper(void) { return 0; }
      |            ^~~~~~
s34h.c:1:25: note: previous implicit declaration of ‘helper’ with type ‘int()’
    1 | int main(void) { return helper(); }
      |                         ^~~~~~
s34h.c:3:12: warning: ‘helper’ defined but not used [-Wunused-function]
    3 | static int helper(void) { return 0; }
      |            ^~~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s34h.c -o /dev/null (cc exit=1) =====
s34h.c:1:25: error: call to undeclared function 'helper'; ISO C99 and later do not support implicit function declarations [-Wimplicit-function-declaration]
    1 | int main(void) { return helper(); }
      |                         ^
s34h.c:3:12: error: static declaration of 'helper' follows non-static declaration
    3 | static int helper(void) { return 0; }
      |            ^
s34h.c:1:25: note: previous implicit declaration is here
    1 | int main(void) { return helper(); }
      |                         ^
2 errors generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s34m.c -o /dev/null (cc exit=0) =====
s34m.c:1:6: warning: return type of ‘main’ is not ‘int’ [-Wmain]
    1 | void main(void) { }
      |      ^~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s34m.c -o /dev/null (cc exit=1) =====
s34m.c:1:1: error: 'main' must return 'int'
    1 | void main(void) { }
      | ^~~~
      | int
1 error generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s34g2.c -o /dev/null (cc exit=0) =====
s34g2.c:3:1: warning: ISO C does not support ‘[[]]’ attributes before C2X [-Wpedantic]
    3 | [[noreturn]] void die2(void) { exit(1); }
      | ^
```

**왜 그런가**

- ★★★ **암시적 선언이 만든 외부 링크 `helper` 와 뒤의 `static` 정의가 충돌**한다 — gcc 의 `note: previous implicit declaration ... 'int()'`. 처방은 **위에 `static int helper(void);`**([29번 형제](../29-scope-and-linkage-static-extern/)의 링크 규칙).
- ★★ **`main` 은 두 서명 밖을 「다른 구현 정의 방식」에 맡겼다** — 그래서 gcc 는 `-Wmain` 경고, clang 은 에러로 **구현이 갈렸다.** `int main(int argc, char *argv[])` 는 모든 칸 0건.
- ★ **`[[noreturn]]`** — C17 에서 `-pedantic` 경고 1(두 컴파일러), C23 에서 0. **`_Noreturn`** — 두 판 다 0(C23 이 구식 기능으로 돌렸는데도).

### 9. 34 → 36 — **C17 은 두 자리(빈 괄호 · `...`) · C23 은 한 자리(`...`)** ★★★

**왜 그런가**

- ★★★ **기본 인자 승격은 「매개변수 타입을 모르는 인자」에 건다** — C17 에서는 **프로토타입 없는 호출의 모든 인자**와 **`...` 뒤의 인자**. C23 은 빈 괄호가 `void` 가 되어 **`...` 뒤만** 남았다(N3220 의 함수 호출 문장이 「**뒤따르는 인자**」만 말한다).
- ★★ **6번의 `al`** — [36번 형제](../36-variadic-functions-stdarg/)의 가변 인자 호출과 **같은 번역**이다. 컴파일러는 빈 괄호 호출을 「**가변 인자일지도 모르는 호출**」로 다뤘다.
- ★ **03·04편과의 관계** — 정수 승격 규칙은 같다([03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)). 다른 것은 **`float` → `double`** 이 붙는다는 것([04번 형제](../04-floating-point-types-and-conversions/)) — 식 안의 `float` 은 `double` 로 안 오른다.

### 10. 판 경계와 다섯 층 — **본체는 판 경계 · 「종료 코드 0인데 ill-formed」 셋 · UB 는 서명 불일치** ★★★

**왜 그런가**

- ★★★ **판 경계** — `int f();`(C23 에서 `void`) · 옛 정의(C23 이 뺐다) · 암시적 선언(C99 가 뺐다) · 승격 자리(두 자리 → 한 자리) · `[[noreturn]]`(C23) · `_Noreturn`(C23 구식).
- ★★★ **「종료 코드 0인데 ill-formed」 셋** — ① gcc 12·13 의 C99 이후 암시적 선언(**강도**로 드러남 — `-pedantic-errors`) ② gcc 13 `c2x` 의 옛 정의(**강도**) ③ gcc-12 `c2x` 의 `f(1, 2)`(**컴파일러 판**으로만 — 그 판은 강도를 올려도 `exit=0`).
- ★★ **UB** — 호환되지 않는 타입으로 부르기(빈 괄호로 `float` 정의 부르기). **도구 침묵** — gcc 경고 0 · `-flto` 0 · sanitizer 0 / 4.
- ★ **표준은 제약 위반에 「적어도 하나의 진단」만 요구한다** — 그것을 **경고로 낼지 에러로 낼지는 구현이 정한다.** 그래서 gcc(경고)와 clang(에러)이 **둘 다 적합한 구현**이다.

### 11. 경계 ★

**왜 그런가**

- **선언을 읽는 법** — [01번 형제](../01-declaration-syntax-and-reading/) · **링크** — [29번 형제](../29-scope-and-linkage-static-extern/).
- **가변 인자** — [36번 형제](../36-variadic-functions-stdarg/) · **헤더 배치** — 목록의 **44번 주제**.
- ★ 이 주제가 책임지는 것 — ① **괄호 안의 뜻**(판마다) ② **프로토타입이 없을 때 일어나는 것**(검사 소멸 · 승격 · 도구의 눈 가림) ③ **선언 없이 부르기의 판 격자**.

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s34v.c`·`s34a.c`·`s34b.c`·`s34c.c` | ★★★ **갈린 칸 3 / 12** · gcc-12 `c2x` 옛 뜻 · gcc 13 옛 정의 경고 · 두 판의 다른 에러 이유 | 격자 24칸 + `-pedantic-errors` 6 · 진단 9 · 실행 2 |
| `s34d.c` | ★★★ gcc 12·13 경고 · clang C99 이후 에러 · C89 합법 | 격자 24칸 · 진단 4 · 실행 1 |
| `s34e1.c`·`s34e2.c`·`s34e3.c` | ★★★ `half_f` `no` · `-flto` 조건 · sanitizer 0 / 4 | 격자 4 · `-flto` 8 · 진단 1 · 실행 1 · sanitizer 4 |
| `s34f.c` | ★★ `cvtss2sd` · `al` | 어셈블리 2 |
| `s34g1.c`·`s34g2.c`·`s34h.c`·`s34m.c`·`s34m2.c` | ★ 링크 충돌 · `main` 구현 정의 · noreturn | 격자 20칸 · 진단 5 |
| `s34x.cpp` | ★ C++ 의 빈 괄호 | 2 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. **이 편의 블록은 정규화 없이 전부 동일**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **「경고냐 에러냐」 전부** — 표준은 진단만 요구한다. gcc 12·13 · clang 18 의 선택이다.
- ★★★ **gcc-12 의 `-std=c2x`** — 그 판이 구현한 C23 의 범위다.
- ★★ **5번의 `no`** — UB 의 이 판 결과다. 결론은 「**호환되지 않는 타입으로 부르면 뜻이 없다**」까지다.
- ★ **6번의 `al`** — x86-64 System V 호출 규약의 것이다.

**빈 괄호의 판별 뜻 · 옛 정의와 암시적 선언이 빠진 판 · 기본 인자 승격 · 빈 괄호 선언과 승격 타입이 아닌 정의가 호환되지 않는 것은 구현 의존이 아니다.**\
각 판의 표준이 정한다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `int` 가 아닌 반환형의 암시적 선언 · `-Wstrict-prototypes`·`-Wmissing-prototypes` 격자 · clang 의 `-std=c23` 철자 · `-O3`.
- ★ **못 잰 것** — **gcc 14**(이 머신에 없다).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **1·2·4번 격자 전부** — 컴파일러가 C23 을 더 구현하거나 경고를 에러로 올리면 칸이 움직인다. **gcc 14 이상을 들이면 4번부터.**
- ★★ **5번의 `-flto` 격자** — clang 이 서명 대조를 들여올 수 있다.
- ★ **`_Noreturn` 경고** — 구식 기능 진단이 생길 수 있다.
