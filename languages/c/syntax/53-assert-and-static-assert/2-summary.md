# c/syntax/53 — `assert` 와 `static_assert`: 「**`assert` 는 `NDEBUG` 하나에 식째 사라지는 매크로이고, `static_assert` 는 컴파일러가 대신 멈춰 주는 선언이다**」 — 정리 (힌트)

★★★ **본체는 둘째 창 — 실행 출력의 `NDEBUG` 격자다.** 부작용이 든 단언 `assert(x++ > 0)` 을 두 컴파일러 × 두 최적화 × `NDEBUG` 두 값으로 빌드해 **`x` 를 찍고, 스크립트가 「`x` 가 1 로 남은 칸」을 센다.**
★★★ 그 격자에서 **`x` 가 1 로 남은 칸 4 / 8** — 정확히 **`-DNDEBUG` 네 칸**이다. 최적화 수준은 한 칸도 바꾸지 않았다 — **지운 것은 컴파일러가 아니라 전처리기**다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | ★★ `static_assert` 격자(여섯 꼴 × 두 컴파일러 × 세 판) · 실패 메시지 · 상수 아닌 식 · `assert` 를 함수처럼 · 쉼표 | 씀 |
| ★★★ ② **실행 출력(`NDEBUG` 격자)** | ★ **본체** — `x` · 실패 메시지 · `run exit` | 씀 |
| ③ 전처리 결과(`gcc -E -P`) | ★★ **`NDEBUG` 판은 식이 `((void) (0))` 로 바뀐다** — 사라진 것을 **글자로** 본다 | 씀 |
| ④ 오브젝트 재배치 | ★★ `__assert_fail` 재배치 수 — `NDEBUG` 판은 **0** | 씀 |
| sanitizer | — | 부적용 — 단언은 UB 를 만들지도 잡지도 않는다(★ `NDEBUG` 판의 **0 으로 나누기**는 UB 지만 그 칸은 `SIGFPE` 종료 코드로만 적었다) |
| 시간 측정 | — | 부적용 — 「`NDEBUG` 가 빠르다」는 **재지 않았다** |

★ **이 편은 제5의 상태가 없다** — 묻고 싶은 것(「사라졌나」)을 **전처리 결과가 글자로 직접** 답한다.

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
===== ldd --version | sed -n 1p (exit=0) =====
ldd (Ubuntu GLIBC 2.39-0ubuntu8.9) 2.39
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

★★ **glibc 2.39 의 `assert` 는 인자 하나짜리 매크로**다(`define assert(expr)` — 네 정의 전부). **`static_assert` 는 C17 이하에서만 `_Static_assert` 로 정의**한다(154 줄의 조건 · 158 줄).

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 없음 | 이 편의 출력에는 PID · 주소 · 시간이 없다 |
| 안 흔들린다 | ★★★ **`NDEBUG` 격자 · 실패 메시지 · 종료 코드 134/136** · `static_assert` 격자 · 재배치 수 · 전처리 결과 | 같은 판 · 같은 플래그면 같다 |
| 안 흔들린다(선언) | ★ **메시지의 프로그램 이름 `x:`** | 실행 파일 이름이 박힌다 — 그래서 늘 `./x` 로 돌렸다 |

★★ **정규화 규칙은 기본 넷뿐**이다(이 편에서는 지울 것이 없다).

## 한눈에 — 쉽게 말하면

**`assert` 는 「공사 중에만 세워 두는 검문소」다.**

- **검문소는 도면(소스)에 그려져 있지만, 준공 도장(`NDEBUG`)이 찍히면 도면에서 통째로 지워진다** — 검문소 안에서 하던 **다른 일**(`x++`)도 같이 사라진다. → **식째 사라진다**
- **검문에 걸리면 「어느 공구 · 몇 번 말뚝 · 무슨 조건」을 적은 쪽지를 남기고 공사를 멈춘다** — 쪽지의 **양식**은 현장(구현)이 정한다. → **메시지 형식은 구현 정의 · `abort`**
- **`static_assert` 는 「설계 검토」다** — 도면 단계에서 틀리면 **착공(컴파일) 자체가 안 된다.** 준공 도장과 무관하다. → **컴파일 시간 · `NDEBUG` 무관**
- **설계 검토 양식이 판마다 바뀌었다** — C11 은 「`_Static_assert`(식, 사유)」, C23 은 「`static_assert`(식)」만 써도 된다. → **판 차이**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 준공 도장 | `NDEBUG` | ★★★ 격자의 `-DNDEBUG` 네 칸 |
| 도면에서 지워진 검문소 | `((void) (0))` | ★★ `gcc -E -P` 블록 |
| 검문소에서 하던 다른 일 | `x++` | ★★★ `x = 1` 로 남음 |
| 쪽지 | `` x: s53b.c:5: take: Assertion `…' failed. `` | ★★ gcc 와 clang 이 **함수 칸만** 다르다 |
| 설계 검토 | `_Static_assert` / `static_assert` | ★★★ 격자 7 / 12 줄이 판 사이에서 갈림 |

```text
   assert(x++ > 0);

   NDEBUG 없음                                  NDEBUG 있음 (#include 보다 앞에서)
   ----------------------------------------     ----------------------------------------
   ((x++ > 0) ? (void) (0)                       ((void) (0));
             : __assert_fail ("x++ > 0",
                 "s53a.c", 7, __PRETTY_FUNCTION__));
   x++ 가 실행된다  -> x = 2                      x++ 가 소스에서 사라졌다 -> x = 1
   __assert_fail 재배치 1                         __assert_fail 재배치 0
```

- ★★★ **이 주제의 본체는 「표준」 칸** — `NDEBUG` 가 있으면 `assert(...)` 가 `((void)0)` 이 된다는 것 · 실패하면 `abort` 한다는 것 · 메시지에 **식 · 파일 · 줄 · 함수**가 들어간다는 것이 **전부 표준**이다.
- ★★ **「구현」 칸** — 메시지의 **양식**(`` x: 파일:줄: 함수: Assertion `식' failed. ``) · 함수 칸을 `take` 로 쓰나 `int take(int)` 로 쓰나 · C23 요구를 따라잡았나.

> **`assert(식)`** — `NDEBUG` 가 없으면 `식` 이 0 일 때 메시지를 쓰고 `abort()`. **`NDEBUG` 가 있으면 `((void)0)`** — 식은 **평가되지 않는다.**\
> 예: `assert(p != NULL);`.

> **`_Static_assert(상수식, "메시지")`** — 컴파일 때 상수식이 0 이면 **컴파일 에러**. C23 은 `static_assert(상수식)` 도 된다.\
> 예: `_Static_assert(sizeof(int) == 4, "int is 32-bit");`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **`NDEBUG` 는 무엇을 지우나** — 단언 · 그 안의 부작용 · `__assert_fail` 호출 · 그리고 **최적화는 상관있나**.
2. ★★ **단언이 실패하면 무엇이 나오나** — 메시지의 칸 · 종료 코드 · `NDEBUG` 판에서는.
3. ★★★ **`static_assert` 는 판마다 어떻게 쓰나** — `_Static_assert` · `<assert.h>` 매크로 · C23 키워드 · 메시지 생략 · 상수 아닌 식.

## 동작 방식

### (1) ★★★ `NDEBUG` 격자 — 부작용이 있는 단언

**언제 쓰나** — 단언 안에서 **함수를 부르거나 값을 바꾸고** 싶어질 때(`assert(init() == 0)` · `assert(n-- > 0)`). ★★★ **이 편의 본체**다.

```c
/* s53a.c */
#include <assert.h>
#include <stdio.h>

int main(int argc, char **argv) {
    (void)argv;
    int x = argc;                          /* 인자 없이 돌리면 1 */
    assert(x++ > 0);
    printf("x = %d\n", x);
    return 0;
}
```

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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s53a.c -o x ; ./x (cc exit=0 · run exit=0) =====
x = 2
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -DNDEBUG s53a.c -o x ; ./x (cc exit=0 · run exit=0) =====
x = 1
```

그림 해설 (한 단계씩):

- ★★★ **`x` 가 1 로 남은 칸 4 / 8 — `-DNDEBUG` 네 칸 전부, 그 밖은 0 칸.** 단언은 여덟 칸 다 **참**(`1 > 0`)이었다. 갈린 것은 참·거짓이 아니라 **`x++` 가 실행됐느냐**다.
- ★★★ **최적화 수준은 답을 안 바꿨다** — `-O0` 과 `-O2` 가 같은 값이다. 「최적화가 지웠다」가 아니다 — **`NDEBUG` 판은 컴파일러에 식이 도착하지도 않는다**((2)의 전처리 결과).
- ★★ **그래서 단언에는 부작용을 넣지 않는다** — 디버그 빌드와 릴리스 빌드가 **다른 프로그램**이 된다. 필요한 일은 단언 **밖**에서 하고 결과만 단언한다(`int r = init(); assert(r == 0);` — 그러면 `NDEBUG` 판에서 `r` 이 안 쓰인다는 경고를 받을 수 있다. ★ 표준은 그 경우 **경고하지 말라고 권한다**).

### (2) ★★ 전처리 결과 — 사라진 것을 글자로 본다

**언제 쓰나** — 「이 단언이 릴리스에서 무엇이 되나」를 **추측 말고 확인**할 때.

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -E -P s53a.c | grep -F 'x++' (cc exit=0) =====
    ((x++ > 0) ? (void) (0) : __assert_fail ("x++ > 0", "s53a.c", 7, __extension__ __PRETTY_FUNCTION__));
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -E -P -DNDEBUG s53a.c | grep -n -A1 'int x = argc' (cc exit=0) =====
219:    int x = argc;
220-    ((void) (0));
```

- ★★★ **`NDEBUG` 가 없으면 삼항식** — `((x++ > 0) ? (void) (0) : __assert_fail ("x++ > 0", "s53a.c", 7, __extension__ __PRETTY_FUNCTION__));`. 식이 **한 번 평가**되고, 거짓이면 `__assert_fail` 이 **식의 글자 · 파일 · 줄 · 함수**를 받는다.
- ★★★ **`NDEBUG` 가 있으면 `((void) (0));`** — `int x = argc;` 다음 줄에 **식이 없다.** 표준 문장 「`#define assert(...) ((void)0)`」 그대로다.
- ★ **`"x++ > 0"` 은 인자의 문자열화**다([43번 형제](../43-stringizing-and-token-pasting/)의 `#`). 그래서 메시지에 **소스에 쓴 글자 그대로** 나온다.

### (3) ★★ 실패하는 단언 — 메시지 · 종료 코드 · `NDEBUG` 판

**언제 쓰나** — 단언이 실패했을 때 **무엇을 보고 어디를 고칠지** 정할 때.

```c
/* s53b.c */
#include <assert.h>
#include <stdio.h>

int take(int count) {
    assert(count > 0);
    return 100 / count;
}

int main(int argc, char **argv) {
    (void)argv;
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("start\n");
    int r = take(argc - 1);                /* 인자 없이 돌리면 0 */
    printf("r = %d\n", r);
    return 0;
}
```

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

- ★★★ **메시지는 표준이 요구한 네 칸** — 식 `count > 0` · 파일 `s53b.c` · 줄 `5` · 함수. 앞의 **`x:`** 는 프로그램 이름이다(glibc 의 양식).
- ★★ **함수 칸만 컴파일러마다 다르다** — gcc 는 `take`, clang 은 **`int take(int)`**. gcc 의 전처리 결과는 `__PRETTY_FUNCTION__` 을 넘기고((2)), 그 값이 **C 에서 gcc 는 이름만**이다. clang 은 **서명째**를 적었다(★ clang 쪽 전처리 결과는 펼쳐 보지 않았다). 표준이 「구현 정의 형식」이라 적은 자리다.
- ★★★ **`run exit=134`** = 128 + 6(`SIGABRT`) — `abort()` 가 불렸다. **`start` 는 찍혔고 `r = …` 는 안 찍혔다**(stdout 을 버퍼 없이 둔 판 — 규칙 19-A).
- ★★★ **`-DNDEBUG` 네 칸은 `run exit=136`** = 128 + 8(`SIGFPE`) — 단언이 사라져 **`100 / 0` 이 실제로 실행됐다.** 메시지는 0 줄이다. **단언이 막던 UB 가 그대로 드러난 것**이다(★ 0 으로 나누기는 UB — 이 판은 신호로 죽었을 뿐이다).
- ★★ **`__assert_fail` 재배치 — `NDEBUG` 판 0 · gcc 1 · clang `-O0` 1 · clang `-O2` 2** — (4)에서 함수 목록으로 읽는다.

### (4) ★★ 재배치 수를 함수 목록으로 읽기

**언제 쓰나** — 「릴리스 바이너리에 단언 코드가 남았나」를 **오브젝트에서** 확인할 때.

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

- ★★ **gcc `-O2` 는 실패 경로를 `take.part.0` 으로 떼어 냈다** — `__assert_fail` 재배치는 **그 한 곳**이다. `take` 와 `main` 에는 `idiv`(나눗셈)만 보인다.
- ★★ **clang `-O2` 는 `take` 와 `main` 에 하나씩** — `main` 이 `take` 를 **인라인한 사본**을 따로 가졌다. 그래서 2 다.
- ★★★ **`-DNDEBUG` 판은 `__assert_fail` 이 아예 없다** — 함수 목록에 `take.part.0` 도 없다. 남은 것은 **`idiv` 둘**(원래 `take` 와 인라인된 사본)이다.

### (5) ★★★ `static_assert` 격자 — 여섯 꼴 × 두 컴파일러 × 세 판

**언제 쓰나** — 타입 크기 · 구조체 오프셋 · 상수 관계를 **컴파일 때** 못 박을 때.

```c
/* s53c1.c */
_Static_assert(sizeof(int) == 4, "m");
```

```c
/* s53c2.c */
#include <assert.h>
static_assert(sizeof(int) == 4, "m");
```

```c
/* s53c3.c */
static_assert(sizeof(int) == 4, "m");
```

```c
/* s53c4.c */
_Static_assert(sizeof(int) == 4);
```

```c
/* s53c5.c */
#include <assert.h>
static_assert(sizeof(int) == 4);
```

```c
/* s53c6.c */
static_assert(sizeof(int) == 4);
```

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
===== clang -std=c11 -Wall -pedantic -c s53c3.c -o /dev/null (cc exit=1) =====
s53c3.c:1:15: error: expected parameter declarator
    1 | static_assert(sizeof(int) == 4, "m");
      |               ^
s53c3.c:1:15: error: expected ')'
s53c3.c:1:14: note: to match this '('
    1 | static_assert(sizeof(int) == 4, "m");
      |              ^
s53c3.c:1:1: error: type specifier missing, defaults to 'int'; ISO C99 and later do not support implicit int [-Wimplicit-int]
    1 | static_assert(sizeof(int) == 4, "m");
      | ^
      | int
s53c3.c:1:14: warning: a function declaration without a prototype is deprecated in all versions of C [-Wstrict-prototypes]
    1 | static_assert(sizeof(int) == 4, "m");
      |              ^                     
      |                                    void
1 warning and 3 errors generated.
```

```text
===== gcc -std=c11 -Wall -pedantic -c s53c4.c -o /dev/null (cc exit=0) =====
s53c4.c:1:1: warning: ISO C11 does not support omitting the string in '_Static_assert' [-Wpedantic]
    1 | _Static_assert(sizeof(int) == 4);
      | ^~~~~~~~~~~~~~
```

```text
===== clang -std=c11 -Wall -pedantic -c s53c5.c -o /dev/null (cc exit=0) =====
s53c5.c:2:31: warning: '_Static_assert' with no message is a C23 extension [-Wc23-extensions]
    2 | static_assert(sizeof(int) == 4);
      |                               ^
      |                               , ""
1 warning generated.
```

```text
===== gcc -std=c11 -Wall -pedantic -c s53c5.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c11 -Wall -pedantic-errors -c s53c5.c -o /dev/null (cc exit=0) =====
```

```text
                             c11 / c17                          c2x
   _Static_assert(e, "m")    ok                                 ok
   <assert.h> static_assert  ok (매크로 -> _Static_assert)       ok (키워드)
   static_assert(e, "m")     error (그런 이름이 없다)            ok (키워드)
   _Static_assert(e)         warning (메시지 생략은 C23)         ok
   <assert.h> static_assert(e)  gcc ok · clang warning  ★        ok
   static_assert(e)          error                              ok
```

- ★★★ **`c11` 과 `c2x` 가 갈린 줄 7 / 12** — `<assert.h>` 없는 `static_assert` 네 줄(error → ok) · 메시지 생략 `_Static_assert` 두 줄(warning → ok) · 그리고 **clang 의 `<assert.h>` + 메시지 생략 한 줄**(warning → ok). `c17` 은 열두 줄 다 `c11` 과 같다.
- ★★★ **`<assert.h>` 없이 `static_assert` 를 쓰면 C11·C17 에서 에러** — 그 판에서 `static_assert` 는 **헤더가 주는 매크로**이지 키워드가 아니다. 진단이 엉뚱하다 — gcc 는 **「`sizeof` 앞에 선언 지정자가 와야 한다」**, clang 은 **「매개변수 선언자가 와야 한다」 · 「implicit int」** — **함수 선언으로 읽었다.** 진단 문구가 원인을 가리키지 않는 자리다(규칙 27).
- ★★★ **`s53c5.c`(헤더 + 메시지 생략)에서 gcc 는 조용하다 — `-pedantic-errors` 에서도 `cc exit=0`.** 같은 생략을 **직접** 쓴 `s53c4.c` 는 `-Wpedantic` 경고를 낸다. 매크로가 **시스템 헤더에서 펼쳐졌기 때문에** gcc 가 그 자리의 `-pedantic` 진단을 **거둔 것**으로 보인다(★ 그 메커니즘은 확인하지 않았다 — 두 블록의 차이만 사실이다). clang 은 `-Wc23-extensions` 로 짚는다.

### (6) ★★ 가정 검사 — 실패 메시지와 상수 아닌 식

**언제 쓰나** — 전송 형식 · 파일 형식처럼 **바이트 배치가 곧 계약**인 구조체를 쓸 때.

```c
/* s53d.c */
#include <stddef.h>
#include <stdint.h>

struct Header { uint8_t tag; uint32_t len; uint16_t kind; };

_Static_assert(sizeof(uint32_t) == 4, "wire format needs 4-byte len");
_Static_assert(offsetof(struct Header, len) == 4, "len must start at byte 4");
_Static_assert(sizeof(struct Header) == 7, "header must be 7 bytes");

int f(int n) {
    _Static_assert(n == 4, "n");
    return n;
}
```

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

- ★★★ **세 번째 단언이 멈춘다** — `sizeof(struct Header)` 는 7 이 아니라 **12** 다(clang 이 `expression evaluates to '12 == 7'` 로 **값까지** 적어 준다). 멤버 합은 7 바이트인데 **패딩 5 바이트**가 있다([22번 형제](../22-struct-padding-and-alignment/)). `offsetof(struct Header, len) == 4` 는 **통과**했다 — `len` 앞에 패딩 3 바이트.
- ★★ **gcc 는 메시지 문자열만** · **clang 은 「due to requirement '식'」 + 식의 값** — 같은 실패를 **두 양식**으로 적는다.
- ★★★ **상수가 아닌 식은 단언이 아니라 에러** — gcc 「expression in static assertion is not constant」 · clang 「static assertion expression is not an integral constant expression」. **실행 시 값은 `assert` 의 몫**이다.

### (7) ★★ `assert` 는 함수가 아니다

**언제 쓰나** — `assert` 를 **콜백으로 넘기거나** 괄호로 감싸 부르고 싶을 때.

```c
/* s53e.c */
#include <assert.h>

int main(void) {
    void (*check)(int) = assert;
    (void)check;
    return 0;
}
```

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

- ★★★ **`assert` 라는 함수는 없다** — 함수형 매크로는 **뒤에 `(` 가 올 때만** 펼쳐진다. `= assert;` 는 매크로가 아니라 **없는 이름**이다. 표준은 「실제 함수로 구현하지 말라 · **매크로를 억눌러 함수에 닿으려 하면 UB**」라고 적는다.
- ★★ **두 컴파일러의 「고친 제안」은 둘 다 틀렸다** — gcc 는 **이미 있는** `#include <assert.h>` 를 넣으라 하고, clang 은 glibc 내부 함수 **`__assert`** 로 바꾸라 한다(그러면 서명이 안 맞는다는 둘째 에러가 따라온다). **진단의 제안을 그대로 따르면 안 되는 자리**다(규칙 27).

### (8) ★★ 쉼표가 든 단언 — C23 은 고쳤고 glibc 는 아직

**언제 쓰나** — 단언 안에 **복합 리터럴 · 매크로 인자 · 쉼표가 든 식**을 쓸 때.

```c
/* s53f.c */
#include <assert.h>

struct P { int x, y; };

int main(void) {
    assert((struct P){ 1, 2 }.x == 1);
    return 0;
}
```

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

- ★★★ **`{ 1, 2 }` 의 쉼표가 매크로 인자를 둘로 가른다** — 괄호 `( )` 는 쉼표를 보호하지만 **중괄호 `{ }` 는 못 한다**([42번 형제](../42-function-like-macro-pitfalls/)). 그래서 `assert` 가 **인자 2 개**를 받았다.
- ★★★ **C23 은 이것을 고치려고 `assert(...)` — 가변 인자 매크로 — 를 요구한다.** 그런데 **`-std=c2x` 에서도 같은 에러**다 — 이 판의 glibc 헤더가 `define assert(expr)` 하나뿐이기 때문이다((이 판)의 헤더 블록). **표준 문장과 이 판의 라이브러리가 다르다.**
- ★★ **clang 은 고치는 법을 짚는다** — 「parentheses are required around macro argument containing braced initializer list」. **식 전체를 한 겹 더 괄호로** 감싸면 된다(★ 그 판은 **던지지 않았다**).
- ★ gcc 의 「did you forget to `#include <assert.h>`」는 (7)과 같은 엉뚱한 제안이다.

### (9) ★★ `#define NDEBUG` 의 자리 — `#include` 보다 뒤면 안 먹는다

**언제 쓰나** — 파일 하나에서만 단언을 끄려고 `#define NDEBUG` 를 적을 때.

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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -E -P s53g.c | grep -F 'x == 1' (cc exit=0) =====
    ((x == 1) ? (void) (0) : __assert_fail ("x == 1", "s53g.c", 8, __extension__ __PRETTY_FUNCTION__));
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s53g.c -o x ; ./x 2>&1 >/dev/null (cc exit=0 · run exit=134) =====
[before]
x: s53g.c:8: main: Assertion `x == 1' failed.
```

- ★★★ **`#include <assert.h>` 다음에 정의한 `NDEBUG` 는 효과가 없다** — 전처리 결과에 `__assert_fail ("x == 1", …)` 이 **그대로** 있고, 실행하면 `[before]` 뒤에 메시지 · `run exit=134` 다. `[after]` 는 없다.
- ★★ **표준 문장 그대로** — 「**`<assert.h>` 가 포함되는 자리에서** `NDEBUG` 가 정의돼 있으면」 · 「**포함될 때마다** 그때의 `NDEBUG` 상태로 다시 정의된다」. `NDEBUG` 는 헤더가 **읽는** 매크로이고, 헤더가 지나간 뒤에 바꿔도 이미 정의된 `assert` 는 그대로다.
- ★ **그래서 `-DNDEBUG` 를 명령행에 둔다** — 모든 헤더보다 먼저다.

## 문법 — 형태와 규칙

### 형태

```c
/* s53d.c */
#include <stddef.h>
#include <stdint.h>

struct Header { uint8_t tag; uint32_t len; uint16_t kind; };

_Static_assert(sizeof(uint32_t) == 4, "wire format needs 4-byte len");
_Static_assert(offsetof(struct Header, len) == 4, "len must start at byte 4");
_Static_assert(sizeof(struct Header) == 7, "header must be 7 bytes");

int f(int n) {
    _Static_assert(n == 4, "n");
    return n;
}
```

- `assert(식)` — **실행 시간 · `NDEBUG` 로 꺼짐 · 실패하면 `abort`.** 식은 **스칼라**여야 한다.
- `_Static_assert(상수식, "메시지")` — **컴파일 시간 · `NDEBUG` 무관 · 파일 범위와 블록 범위 둘 다.** C23 은 `static_assert(상수식)`.
- ★ 이식하려면 **C11 부터 되는 `_Static_assert(식, "메시지")`** 가 가장 넓다(격자에서 여섯 칸 — 두 컴파일러 × 세 판 — 이 다 `ok` 인 파일은 `s53c1`·`s53c2` 뿐이다).

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 도구 | 층 | 절 |
|---|---|---|---|
| `assert(x++ > 0)` | 경고 0 | 적법 — `NDEBUG` 판과 뜻이 갈린다 | (1) |
| `assert` 로 입력 검증 | 경고 0 | 적법 — 릴리스에서 검증이 사라진다 | (3) |
| `static_assert(e, "m")`(C11/C17, 헤더 없음) | gcc·clang **error**(엉뚱한 문구) | 제약 위반 | (5) |
| `_Static_assert(e)`(C11/C17) | `-Wpedantic` / `-Wc23-extensions` | 확장 | (5) |
| `_Static_assert(n == 4, …)`(`n` 변수) | **error** | 제약 위반 | (6) |
| `void (*f)(int) = assert;` | **error** | 없는 이름(억눌러 함수에 닿으면 UB) | (7) |
| `assert((struct P){1, 2}.x == 1)` | **error**(c2x 에서도 · 이 glibc) | 매크로 인자 개수 | (8) |
| `#include <assert.h>` 뒤 `#define NDEBUG` | 경고 0 | 적법 — 효과가 없을 뿐 | (9) |

### 규칙 불릿

- ★★★ **단언에는 부작용을 넣지 않는다.** 일은 밖에서, 단언은 결과만.
- ★★★ **단언은 「있을 수 없는 일」에 · 입력 검증은 `if` 로.** `NDEBUG` 판에서 사라져도 되는 것만 단언한다.
- ★★ **레이아웃 · 타입 크기 가정은 `_Static_assert`.** 실행 비용이 0 이고 `NDEBUG` 와 무관하다.
- ★★ **`NDEBUG` 는 명령행(`-DNDEBUG`)에.**

## 어디서 틀리나

### 1. ★★★ 「`-O2` 가 단언을 지운다」

**지우는 것은 `NDEBUG` 다** — `-O0`/`-O2` 는 한 칸도 안 바꿨다((1)).

### 2. ★★★ 「단언 안의 `init()` 은 릴리스에서도 돈다」

**식째 사라진다** — `x` 가 1 로 남았다((1)·(2)).

### 3. ★★ 「단언이 있으니 릴리스에서도 0 으로 안 나눈다」

`NDEBUG` 판은 **`SIGFPE`(136)** 로 죽었다((3)).

### 4. ★★ 「`static_assert` 는 C11 부터 그냥 쓴다」

**헤더가 있어야** 한다(C11·C17). 없으면 **엉뚱한 문구의 에러**다((5)).

### 5. ★★ 「`-pedantic-errors` 면 C23 확장을 다 잡는다」

gcc 는 **헤더 매크로를 거친 메시지 생략**을 **말하지 않았다**((5) — `s53c5.c`).

### 6. ★★ 「C23 으로 컴파일하면 `assert` 안의 쉼표가 된다」

**표준은 그렇지만 이 판의 glibc 는 아니다**((8)).

### 7. ★ 「파일 첫머리에 `#define NDEBUG` 를 두면 된다」

**`#include <assert.h>` 보다 앞**이어야 한다((9)).

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.

| 층 | 뜻 | 이 주제에서 | 근거 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | `NDEBUG` → `((void)0)` · 포함될 때마다 다시 정의 · 실패하면 표준 오류에 쓰고 `abort` · 메시지에 식·파일·줄·함수 · `assert` 는 함수가 아니다 · `_Static_assert` 는 상수식 · C23 키워드·메시지 생략·가변 인자 | 격자 · 전처리 결과 · 진단 |
| ★★ **구현 정의** | 문서화 의무 | ★★ **메시지의 양식** · `abort` 의 종료 방식 | `x: s53b.c:5: take: …` · `134` |
| ★★ **컴파일러·glibc 구현** | 이 판이 한 것 | 함수 칸(`take` 대 `int take(int)`) · 실패 경로 분리(`take.part.0`) · **glibc 2.39 의 인자 하나짜리 `assert`** · gcc 가 헤더 매크로의 `-pedantic` 진단을 안 내는 것 · 진단 문구와 「고친 제안」 | 블록들 |
| **미명시** | 몇 가지 중 하나 | ★ 해당 없음 | — |
| ★★★ **UB** | 아무 일이나 | ★★ 매크로를 억눌러 `assert` 함수에 닿기 · ★★ **`NDEBUG` 판에서 단언이 막던 UB 가 드러나는 것**(`100 / 0`) | `run exit=136` |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 이 편의 사례 | 무엇이 봤나 | 무엇이 못 봤나 |
|---|---|---|---|
| 적법(뜻이 갈림) | `assert(x++ > 0)` | **아무 경고도** — `gcc -E -P` 가 글자로 보여 줄 뿐 | 컴파일러 · sanitizer |
| 적법(효과 없음) | 뒤늦은 `#define NDEBUG` | **아무 경고도** | 전부 |
| 확장 | 헤더 + 메시지 생략(c11) | clang `-Wc23-extensions` | gcc `-pedantic-errors` |
| 판 불일치 | C23 가변 인자 `assert` | 에러로 드러남(이 판) | — |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓴다 | 안 쓴다 |
|---|---|---|
| 내부 불변식(있을 수 없는 일) | `assert` | — |
| 외부 입력 · 실패할 수 있는 호출 | `if` + 오류 처리 | `assert` |
| 타입 크기 · 오프셋 · 상수 관계 | ★★★ `_Static_assert` | `assert`(실행까지 미룬다) |
| 단언 안에서 함수 호출·증감 | — | ★★★ 쓰지 않는다 |
| 파일 하나만 단언 끄기 | `#define NDEBUG` 를 **`#include <assert.h>` 앞에** | 뒤에 |

## 핵심 문장

1. ★★★ **`NDEBUG` 는 전처리 단계에서 `assert(...)` 를 `((void)0)` 으로 바꾼다 — 식째 사라지고, 이 판에서 `x` 가 1 로 남은 칸은 4 / 8 이었다.**
2. ★★★ **최적화 수준은 아무것도 바꾸지 않았다 — 지우는 것은 컴파일러가 아니라 `NDEBUG` 다.**
3. ★★ **실패 메시지는 식·파일·줄·함수가 표준이고 양식은 구현이 정한다 — gcc 는 `take`, clang 은 `int take(int)`.**
4. ★★★ **`static_assert` 는 C11·C17 에서 헤더의 매크로, C23 에서 키워드다 — 판 사이에서 7 / 12 줄이 갈렸다.**
5. ★★ **C23 은 `assert(...)` 를 요구하지만 이 판의 glibc 는 아직 인자 하나다 — 쉼표가 든 단언은 `-std=c2x` 에서도 에러다.**

## 관련 자료

- [41번 형제 — 전처리기 지시자와 조건부 컴파일](../41-preprocessor-directives-and-conditional-compilation/) — `#if`·`#ifdef` · `gcc -E` 읽기. 그쪽은 **전처리기 일반**까지, 여기는 **`NDEBUG` 가 `assert` 에 하는 일**부터.
- [42번 형제 — 함수형 매크로의 함정](../42-function-like-macro-pitfalls/) — 매크로는 인자를 **글자로** 받는다 · 쉼표. (8)의 뿌리다.
- [43번 형제 — 문자열화와 토큰 붙이기](../43-stringizing-and-token-pasting/) — 메시지의 `` `x++ > 0' `` 이 `#` 로 만들어진다.
- [22번 형제 — 구조체 패딩](../22-struct-padding-and-alignment/) · [08번 형제 — `sizeof`·`offsetof`](../08-sizeof-alignment-and-offsetof/) — (6)의 12 바이트.
- [Rust 갈래 23번 — `panic!` 대 `Result`](../../../rust/syntax/23-panic-vs-result/) — ★★ (7)절 — **`assert!` 는 `-O` 에서도 남고 `debug_assert!` 만 사라진다**(그쪽 실측: 기본 빌드 종료 코드 101, `-O` 는 0). C 의 `assert` 는 **`debug_assert!` 쪽**이고, C 에는 **`assert!` 에 해당하는 표준 매크로가 없다** — 「릴리스에서도 남는 검사」는 `if` 로 쓴다.
- [Kotlin 갈래 51번 — 전제 조건](../../../kotlin/syntax/51-preconditions-require-check-error-todo/) — ★ Kotlin `assert` 는 **JVM 에 `-ea` 를 줘야** 울린다(그쪽 KDoc 인용). **기본이 꺼짐**이다 — C 는 **기본이 켜짐**이고 `NDEBUG` 로 끈다. 방향이 반대다. `require`·`check` 는 **늘 켜진** 검사다.

## 용어 풀이

> **단언(assertion)** — 「여기서 이 조건은 반드시 참이다」를 코드로 적은 것. 거짓이면 프로그램이 멈춘다.

> **`NDEBUG`** — 「디버그가 아니다(no debug)」. `<assert.h>` 가 포함될 때 **정의돼 있으면** `assert` 를 비운다. 헤더가 정의하지 않는다 — **사용자가** 정의한다.

> **`__assert_fail`** — glibc 의 내부 함수. `assert` 가 거짓일 때 메시지를 쓰고 `abort` 한다.

> **`abort`** — 프로그램을 **비정상 종료**시키는 표준 함수. 이 판에서는 `SIGABRT` 로 죽어 종료 코드 134.

> **`SIGFPE`** — 산술 예외 신호. 이 판에서 정수 0 으로 나누기가 이것으로 죽었다(종료 코드 136).

> **정적 단언(static assertion)** — 컴파일 때 평가하는 단언. `_Static_assert` · `static_assert`.

> **가변 인자 매크로(variadic macro)** — `#define m(...)` 처럼 **인자 개수를 정하지 않은** 매크로. C23 `assert` 가 이 모양이어야 한다.

## 더 들어가면

- ★★ **`static_assert` 를 블록 범위 · 구조체 안에서** — C 는 구조체 멤버 선언 자리에 `static_assert` 를 둘 수 있다(C11 문법의 `static_assert-declaration`). ★ **던지지 않았다.**
- ★ **`assert` 의 `-Wunused-variable`** — `NDEBUG` 판에서 단언에만 쓰던 변수가 경고를 받는지. 표준 예제는 「구현은 경고하지 말라」고 권한다. ★ **던지지 않았다.**
- ★ **glibc 가 C23 `assert(...)` 를 따라잡는 판** — 이 머신에는 2.39 뿐이다.

## 실행 환경

**기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) — `<assert.h>` 머리의 「**If NDEBUG is defined as a macro name at the point in the source file where <assert.h> is included, the assert macro is defined simply as `#define assert(...) ((void)0)`**」·「**The assert macro is redefined according to the current state of NDEBUG each time that <assert.h> is included**」·「**shall be implemented as a macro with an ellipsis parameter, not as an actual function. If the macro definition is suppressed to access an actual function, the behavior is undefined**」, `assert` 의 「**writes information about the particular invocation that failed (including the text of the argument, the name of the source file, the source line number, and the name of the enclosing function …) on the standard error stream in an implementation-defined format. It then calls the abort function**」를 **본문에서 직접 찾아 읽었다**) · glibc `/usr/include/assert.h`(이 머신)
★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **`x` 값 · 메시지 · 종료 코드 · 진단 · 재배치 · 전처리 결과는 전부 실행으로** 접지했다.
**실행 검증** — 이 문서의 모든 출력·진단은 「이 판」 절의 판에서 실제로 돌려 **파일로 캡처한 것**이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`, 캡처 셸은 `LC_ALL=C` · `ulimit -c 0`.\
★★ **블록은 전부 캡처 파일에서 조립했다.** 이 편의 **그림 2 · 덤프(캡처 블록) 32**.
**버전** — `assert` 는 **C89 부터**. `_Static_assert` 는 **C11 부터**, `<assert.h>` 의 `static_assert` 매크로도 **C11 부터**. ★★ **C23** 이 `static_assert` 를 **키워드**로 만들고 **메시지를 생략**할 수 있게 했으며, `assert` 를 **가변 인자 매크로**(`assert(...)`)로 정의하라고 요구한다 — ★ 이 판의 glibc 는 **마지막 것을 아직 따르지 않는다**((5)).
★★★ **경계** — **전처리기 · 조건부 컴파일 · `gcc -E` 읽기**는 [41번 형제](../41-preprocessor-directives-and-conditional-compilation/), **함수형 매크로가 인자를 글자로 받는 것**은 [42번 형제](../42-function-like-macro-pitfalls/), **`#` 문자열화**는 [43번 형제](../43-stringizing-and-token-pasting/)가 정본이다. **`offsetof`·패딩 계산 자체**는 [08번 형제](../08-sizeof-alignment-and-offsetof/)·[22번 형제](../22-struct-padding-and-alignment/). 여기는 **단언을 언제 쓰고, 무엇이 사라지고, 판마다 무엇이 되나**만 본다.
선행 — [41번 형제](../41-preprocessor-directives-and-conditional-compilation/).
