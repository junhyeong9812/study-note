# c/syntax/43 — 문자열화 `#` 와 토큰 붙이기 `##`: 「**`#`·`##` 에 붙은 인자는 먼저 펼쳐지지 않는다 — 그래서 펼친 결과가 필요하면 한 겹 더 감싼다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) 매크로 치환 절 — 「**`#`·`##` 에 붙지 않은 매개변수만 인자를 매크로 전부 치환한 뒤 넣는다**」 · 「**`#` 은 인자의 철자를 담은 문자열 리터럴 하나가 되고, 토큰 사이 공백은 한 칸이 되며, 문자열·문자 상수 안의 `"`·`\` 앞에는 `\` 가 붙는다**」 · 「**`##` 의 결과가 유효한 전처리 토큰이 아니면 동작은 미정의**」 · 「**`##` 는 치환 목록의 맨 앞·맨 끝에 올 수 없다(제약)**」 · 「**`__VA_OPT__`**」 · 「**가변 매크로 호출의 인자는 매개변수(`...` 제외)보다 적으면 안 된다**」 · 「**`__func__` 는 함수 몸통 첫머리에 선언된 것처럼 보는 식별자**」를 **본문에서 직접 찾아 읽었다**)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **전처리 결과 · 문자열 · 진단은 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.\
> ★★★ **본체는 감싸기 격자다** — 인자 9 × `STR`/`XSTR`, 칸마다 **만들어진 문자열**. 가변 매크로 격자는 FORM 3 × 컴파일러 3 × 판 2.\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> **버전** — `#`·`##` 는 C89, 가변 매크로 `__VA_ARGS__` 는 C99, ★★ **`__VA_OPT__` 는 C23**. `, ##__VA_ARGS__` 는 **GNU 확장**이다.
> ★★★ **경계** — **전처리 결과를 읽는 법**은 [41번 형제](../41-preprocessor-directives-and-conditional-compilation/), **함수형 매크로의 괄호·중복 평가**는 [42번 형제](../42-function-like-macro-pitfalls/)가 정본이다. ★ [36번 형제](../36-variadic-functions-stdarg/)는 **가변 인자 함수**(`<stdarg.h>`)이고 **가변 매크로는 다루지 않았다**(`grep VA_ARGS` 0건) — 이 편이 그 자리다.
> 선행 — [42번 형제](../42-function-like-macro-pitfalls/).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 넷째 창 — 전처리 결과와 그것이 만든 문자열이다.** `#` 과 `##` 는 **컴파일러가 보기 전에** 끝나므로 결과 글자가 곧 증거다.
★★★ 감싸기 격자에서 **`STR` 과 `XSTR` 이 갈린 칸 4 / 9** — 인자 안에 **매크로가 있는 칸만** 갈렸다. gcc 와 clang 은 한 글자도 같다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | ★★ 잘못된 `##` 의 에러 · 가변 매크로의 빈 인자 경고 · `"…" __func__` 에러 | 씀 |
| ② 실행 출력 | ★ 만들어진 문자열을 찍는다 · X-매크로의 결과 | 씀 |
| ③ sanitizer | — | 부적용(런타임에 아무것도 없다) |
| ★★★ ④ **전처리 결과(`-E -P`)** | ★ **본체** — `#`·`##` 가 만든 토큰 | 씀 |
| ★ 제5의 상태 | 「`##` 로 잘못된 토큰을 만들면 무엇이 되나」를 **진단으로** 물으면 두 컴파일러 다 **에러**로 답한다. **표준으로 바꿔 물으니** 「**미정의**」였다 — 에러는 **컴파일러의 선택**이다 | 창을 바꿔 답함 |

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
| 안 흔들린다 | ★★★ **감싸기 격자 · `-E -P` · 가변 매크로 격자** · 진단 문구 | 전처리는 결정적이다 |
| 안 흔들린다 | ★ `__LINE__` 이 만든 숫자 | **소스의 줄 번호**다 — 소스를 고치면 바뀐다(흔들림이 아니라 입력이 바뀐 것) |
| **흔들린다** | — | 이 편에는 없다 |

## 한눈에 — 쉽게 말하면

**`#` 은 「받아 적기」, `##` 는 「두 낱말 붙여 쓰기」다. 둘 다 받은 쪽지를 펼쳐 보지 않고 겉에 쓰인 글자로 한다.**

- **쪽지에 「버전」이라고 쓰여 있으면 「버전」이라고 받아 적는다** — 쪽지 안의 「3」을 보지 않는다. → **`STR(VERSION)` 은 `"VERSION"`**
- **한 사람을 거쳐 전하면 그 사람은 쪽지를 펼쳐 본다** — 두 번째 사람은 펼친 내용을 받아 적는다. → **`XSTR(VERSION)` 은 `"3"`**
- **붙여 쓴 결과가 말이 안 되면** — 사전에 없는 낱말이다. → **`CAT(., x)` 는 에러(표준은 미정의)**
- **목록 하나로 여러 문서를 찍는다** — 같은 목록에 양식만 바꿔 대면 번호표와 이름표가 **어긋나지 않는다.** → **X-매크로**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 겉 글자 받아 적기 | `STR(__LINE__)` → `"__LINE__"` | ★★★ (1) |
| 한 사람 거쳐 전하기 | `XSTR(__LINE__)` → `"10"` | ★★★ (1) |
| 붙여 쓰기 | `CAT(x, y)` → `xy` · `XCAT(tmp_, __LINE__)` → `tmp_9` | ★★ (2) |
| 사전에 없는 낱말 | `CAT(., x)` → 에러 | ★★ (3) |
| 목록 하나 · 양식 여럿 | `COLORS(AS_ENUM)` · `COLORS(AS_NAME)` | ★★ (4) |

```text
   #define STR(x)  #x                  #define XSTR(x) STR(x)
   ----------------------------       --------------------------------------------
   STR(VERSION)                        XSTR(VERSION)
     x 는 # 의 피연산자                   x 는 # 에 안 붙었다 → 인자를 먼저 펼친다
     → 펼치지 않는다                        VERSION → 3
     → "VERSION"                          → STR(3) 을 다시 읽는다
                                          → 이번엔 # 의 피연산자 3 → "3"
```

- ★★★ **이 주제는 「표준」 칸이 전부**에 가깝다 — 감싸기 격자는 **두 컴파일러가 한 글자도 같다.**
- ★★ **「미정의」 칸이 하나 있다** — 잘못된 `##`. 두 컴파일러가 **에러로 막는 것은 컴파일러 구현**이다.
- ★★ **「조건부 표준」과 「컴파일러 구현」이 부딪는 자리** — 빈 가변 인자(`, ##__VA_ARGS__` 대 `__VA_OPT__`).

> **문자열화(stringizing)** — 치환 목록의 `#매개변수` 가 **인자의 철자를 담은 문자열 리터럴**로 바뀌는 것.\
> 예: `#define STR(x) #x` 에서 `STR(a b)` → `"a b"`.

> **토큰 붙이기(token pasting)** — `a ## b` 가 앞뒤 두 토큰을 **하나의 토큰**으로 이어 붙이는 것.\
> 예: `CAT(x, y)` → `xy`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **왜 `XSTR(x) STR(x)` 처럼 한 겹 더 감싸야 하나** — 인자가 **언제** 펼쳐지는가.
2. ★★ **`##` 로 무엇을 만들 수 있고 무엇은 못 만드나** — 이름 생성 · 연산자 토큰 · 잘못된 토큰.
3. ★★ **디버그 매크로에 필요한 조각은 어디서 오나** — `__FILE__`·`__LINE__`·`__func__` · 빈 가변 인자.

## 동작 방식

### (1) ★★★ 감싸기 격자 — 인자 아홉 × `STR`/`XSTR`

**언제 쓰나** — 매크로 값·줄 번호를 **문자열로** 남길 때(버전 문자열 · 로그 · `static_assert` 메시지). ★★★ **이 편의 본체**다.

```c
/* s43a.c */
#include <stdio.h>

#define STR(x) #x
#define XSTR(x) STR(x)
#define VERSION 3
#define ROW "%-14s\t%s\t%s\n"

int main(void) {
    printf(ROW, "arg", "STR", "XSTR");
    printf(ROW, "__LINE__",    STR(__LINE__),    XSTR(__LINE__));
    printf(ROW, "VERSION",     STR(VERSION),     XSTR(VERSION));
    printf(ROW, "VERSION + 1", STR(VERSION + 1), XSTR(VERSION + 1));
    printf(ROW, "a b",         STR(a b),         XSTR(a b));
    printf(ROW, "a    b",      STR(a    b),      XSTR(a    b));
    printf(ROW, "\"q\"",       STR("q"),         XSTR("q"));
    printf(ROW, "'\\n'",       STR('\n'),        XSTR('\n'));
    printf(ROW, "__FILE__",    STR(__FILE__),    XSTR(__FILE__));
    printf(ROW, "__func__",    STR(__func__),    XSTR(__func__));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s43a.c -o x ; ./x (cc exit=0 · run exit=0) =====
arg           	STR	XSTR
__LINE__      	__LINE__	10
VERSION       	VERSION	3
VERSION + 1   	VERSION + 1	3 + 1
a b           	a b	a b
a    b        	a b	a b
"q"           	"q"	"q"
'\n'          	'\n'	'\n'
__FILE__      	__FILE__	"s43a.c"
__func__      	__func__	__func__
```

```text
===== 감싸기 격자 — 인자 9 × STR/XSTR (gcc · clang) (exit=0) =====
인자          	STR	XSTR	갈렸나
__LINE__      	__LINE__	10	갈림
VERSION       	VERSION	3	갈림
VERSION + 1   	VERSION + 1	3 + 1	갈림
a b           	a b	a b	같음
a    b        	a b	a b	같음
"q"           	"q"	"q"	같음
'\n'          	'\n'	'\n'	같음
__FILE__      	__FILE__	"s43a.c"	갈림
__func__      	__func__	__func__	같음
감싸기로 갈린 칸 4 / 9
gcc 와 clang 의 실행 출력이 다른가: 같다 · warning: 줄 gcc 0 · clang 0
```

```text
===== gcc -std=c17 -E -P s43a.c | sed -n '/^int main/,$p' (cc exit=0) =====
int main(void) {
    printf("%-14s\t%s\t%s\n", "arg", "STR", "XSTR");
    printf("%-14s\t%s\t%s\n", "__LINE__", "__LINE__", "10");
    printf("%-14s\t%s\t%s\n", "VERSION", "VERSION", "3");
    printf("%-14s\t%s\t%s\n", "VERSION + 1", "VERSION + 1", "3 + 1");
    printf("%-14s\t%s\t%s\n", "a b", "a b", "a b");
    printf("%-14s\t%s\t%s\n", "a    b", "a b", "a b");
    printf("%-14s\t%s\t%s\n", "\"q\"", "\"q\"", "\"q\"");
    printf("%-14s\t%s\t%s\n", "'\\n'", "'\\n'", "'\\n'");
    printf("%-14s\t%s\t%s\n", "__FILE__", "__FILE__", "\"s43a.c\"");
    printf("%-14s\t%s\t%s\n", "__func__", "__func__", "__func__");
    return 0;
}
```

그림 해설 (한 단계씩):

- ★★★ **갈린 칸 4 / 9 — `__LINE__` · `VERSION` · `VERSION + 1` · `__FILE__`** — **인자 안에 매크로 이름이 있는 칸만** 갈렸다. N3220 — 「**`#`·`##` 에 붙지 않은 매개변수**만 인자의 매크로를 전부 치환한 뒤 넣는다」. `STR` 의 `x` 는 `#` 에 붙어 있어 **펼쳐지지 않고**, `XSTR` 의 `x` 는 안 붙어 있어 **먼저 펼쳐진 뒤** `STR` 로 넘어간다.
- ★★ **`VERSION + 1` 은 `"3 + 1"`** — 문자열화는 **계산하지 않는다.** 펼친 **토큰의 철자**를 적을 뿐이다.
- ★★ **`a    b` 는 `"a b"`** — 토큰 사이 공백은 **몇 칸이든 한 칸**이 된다(표준).
- ★★ **`"q"` 는 `"\"q\""`**, `'\n'` 은 `"'\\n'"` — 문자열·문자 상수 안의 `"` 와 `\` 앞에 **`\` 가 붙는다**(`-E -P` 의 글자). 찍으면 원래 철자가 그대로 나온다.
- ★★★ **`__func__` 는 두 판 다 `"__func__"`** — `__func__` 는 **매크로가 아니라 식별자**다(함수 몸통 첫머리에 `static const char __func__[] = "…";` 가 있는 것처럼 본다). 전처리기는 그 이름을 모르므로 **펼칠 것이 없다.** (6) 에서 다시 본다.

### (2) ★★ `##` — 이름 붙이기와 감싸기

```c
/* s43b.c */
#define CAT(a, b) a ## b
#define XCAT(a, b) CAT(a, b)
#define N 7

CAT(x, y)
CAT(x, N)
XCAT(x, N)
CAT(tmp_, __LINE__)
XCAT(tmp_, __LINE__)
CAT(+, +)
CAT(-, >)
CAT(1, 2)
CAT(, z)
```

```text
===== gcc -std=c17 -pedantic -E -P s43b.c (cc exit=0) =====
xy
xN
x7
tmp___LINE__
tmp_9
++
->
12
z
```

```text
===== clang -std=c17 -pedantic -E -P s43b.c (cc exit=0) =====
xy
xN
x7
tmp___LINE__
tmp_9
++
->
12
z
```

- ★★★ **`CAT(x, N)` 은 `xN`, `XCAT(x, N)` 은 `x7`** — `##` 도 `#` 과 같다. 피연산자는 **먼저 펼쳐지지 않는다.**
- ★★★ **`CAT(tmp_, __LINE__)` 은 `tmp___LINE__`, `XCAT(tmp_, __LINE__)` 은 `tmp_9`** — **고유한 이름 생성**(한 파일 안에서 줄마다 다른 변수 이름)에는 **감싸기가 필수**다.
- ★★ **`CAT(+, +)` 은 `++`, `CAT(-, >)` 은 `->`, `CAT(1, 2)` 는 `12`** — 결과가 **유효한 전처리 토큰**이면 연산자도 숫자도 된다.
- ★ **`CAT(, z)` 은 `z`** — 빈 인자는 **자리표(placemarker)** 가 되어 붙여도 사라진다(C99).
- ★ **gcc 와 clang 의 출력이 같다**(`-pedantic` 경고 0줄).

### (3) ★★ 잘못된 토큰을 만들면

```c
/* s43c.c */
#define CAT(a, b) a ## b

CAT(., x)
CAT(+, -)
CAT(x, +)
```

```text
===== gcc -std=c17 -E -P s43c.c -o /dev/null (cc exit=1) =====
s43c.c:3:5: error: pasting "." and "x" does not give a valid preprocessing token
    3 | CAT(., x)
      |     ^
s43c.c:1:19: note: in definition of macro ‘CAT’
    1 | #define CAT(a, b) a ## b
      |                   ^
s43c.c:4:5: error: pasting "+" and "-" does not give a valid preprocessing token
    4 | CAT(+, -)
      |     ^
s43c.c:1:19: note: in definition of macro ‘CAT’
    1 | #define CAT(a, b) a ## b
      |                   ^
s43c.c:5:5: error: pasting "x" and "+" does not give a valid preprocessing token
    5 | CAT(x, +)
      |     ^
s43c.c:1:19: note: in definition of macro ‘CAT’
    1 | #define CAT(a, b) a ## b
      |                   ^
```

```text
===== clang -std=c17 -E -P s43c.c -o /dev/null (cc exit=1) =====
s43c.c:3:1: error: pasting formed '.x', an invalid preprocessing token
    3 | CAT(., x)
      | ^
s43c.c:1:21: note: expanded from macro 'CAT'
    1 | #define CAT(a, b) a ## b
      |                     ^
s43c.c:4:1: error: pasting formed '+-', an invalid preprocessing token
    4 | CAT(+, -)
      | ^
s43c.c:1:21: note: expanded from macro 'CAT'
    1 | #define CAT(a, b) a ## b
      |                     ^
s43c.c:5:1: error: pasting formed 'x+', an invalid preprocessing token
    5 | CAT(x, +)
      | ^
s43c.c:1:21: note: expanded from macro 'CAT'
    1 | #define CAT(a, b) a ## b
      |                     ^
3 errors generated.
```

```text
===== gcc -std=c17 -E -P s43c.c 2>/dev/null (cc exit=1) =====
. x
+ -
x +
```

그림 해설 (한 단계씩):

- ★★★ **`.x` · `+-` · `x+` 는 하나의 전처리 토큰이 아니다** — gcc 「pasting "." and "x" does not give a valid preprocessing token」, clang 「pasting formed '.x', an invalid preprocessing token」. **둘 다 `exit=1`**.
- ★★★ **표준은 에러를 요구하지 않는다 — 미정의다**(N3220 「결과가 유효한 전처리 토큰이 아니면 동작은 미정의」). 두 컴파일러가 **에러로 막는 것은 컴파일러의 선택**이다(제5의 상태).
- ★★ **gcc 는 붙이지 않은 두 토큰을 남기고 간다**(`. x` · `+ -` · `x +`) — 표준 출력은 이렇게 **계속 만들어진다**(종료 코드만 1).
- ★ **짚는 자리가 다르다** — gcc 는 **인자 자리**(3:5 · note 는 `##` 앞의 `a` 1:19), clang 은 **호출 첫 열**(3:1 · note 는 `b` 1:21).

### (4) ★★ X-매크로 — 한 목록에서 enum 과 이름 배열

**언제 쓰나** — enum 값과 그 **이름 문자열**을 따로 관리하다 **어긋나는 사고**를 막을 때.

```c
/* s43d.c */
#include <stdio.h>

#define COLORS(X) X(RED) X(GREEN) X(BLUE)

#define AS_ENUM(n) COLOR_##n,
#define AS_NAME(n) #n,

enum color { COLORS(AS_ENUM) COLOR_COUNT };
static const char *const color_names[] = { COLORS(AS_NAME) };

int main(void) {
    for (int i = 0; i < COLOR_COUNT; i++)
        printf("%d %s\n", i, color_names[i]);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s43d.c -o x ; ./x (cc exit=0 · run exit=0) =====
0 RED
1 GREEN
2 BLUE
```

```text
===== gcc -std=c17 -E -P s43d.c | grep -E '^(enum color|static const char)' (cc exit=0) =====
enum color { COLOR_RED, COLOR_GREEN, COLOR_BLUE, COLOR_COUNT };
static const char *const color_names[] = { "RED", "GREEN", "BLUE", };
```

- ★★★ **`COLORS(X)` 는 목록을 한 번만 적는다** — `X` 자리에 `AS_ENUM`(`COLOR_##n,`)을 대면 enum 이, `AS_NAME`(`#n,`)을 대면 이름 배열이 나온다. **항목을 더하면 두 곳이 같이 바뀐다.**
- ★★ **`COLOR_COUNT` 는 마지막 뒤에 오므로 자동으로 개수**가 된다(3).
- ★ 이 매크로들은 **감싸기가 필요 없다** — 인자가 `RED` 같은 **매크로가 아닌 이름**이라서다.

### (5) ★★ 가변 매크로의 빈 인자 — `, ##__VA_ARGS__` 대 `__VA_OPT__`

**언제 쓰나** — `LOG("msg")` 처럼 **서식 뒤 인자가 없는 호출**을 받아야 할 때.

```c
/* s43e.c */
#include <stdio.h>

#if FORM == 1
#define LOG(fmt, ...) printf(fmt "\n", __VA_ARGS__)
#elif FORM == 2
#define LOG(fmt, ...) printf(fmt "\n", ##__VA_ARGS__)
#elif FORM == 3
#define LOG(fmt, ...) printf(fmt "\n" __VA_OPT__(,) __VA_ARGS__)
#endif

int main(void) {
    LOG("n=%d", 1);
    LOG("none");
    return 0;
}
```

```text
===== 가변 매크로의 빈 인자 — FORM 3 × 컴파일러 3 × 판 2 (s43e.c) (exit=0) =====
FORM                  	gcc c17	gcc c2x	gcc-12 c17	gcc-12 c2x	clang c17	clang c2x
1 ,__VA_ARGS__        	exit 1 · 경고 1	exit 1 · 경고 0	exit 1 · 경고 1	exit 1 · 경고 1	exit 1 · 경고 1	exit 1 · 경고 1
2 , ##__VA_ARGS__     	exit 0 · 경고 1	exit 0 · 경고 0	exit 0 · 경고 1	exit 0 · 경고 1	exit 0 · 경고 2	exit 0 · 경고 2
3 __VA_OPT__(,)       	exit 0 · 경고 2	exit 0 · 경고 0	exit 0 · 경고 2	exit 0 · 경고 2	exit 0 · 경고 1	exit 0 · 경고 1
(칸 = $CC -std=<판> -Wall -Wextra -pedantic -DFORM=<행> -c s43e.c 의 exit 와 warning: 줄 수)
c17 과 c2x 가 갈린 칸 3 / 9
```

```text
===== gcc -std=c2x -DFORM=1 -E -P s43e.c | sed -n '/^int main/,$p' (cc exit=0) =====
int main(void) {
    printf("n=%d" "\n", 1);
    printf("none" "\n", );
    return 0;
}
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic -DFORM=1 -c s43e.c -o /dev/null (cc exit=1) =====
s43e.c: In function ‘main’:
s43e.c:4:51: error: expected expression before ‘)’ token
    4 | #define LOG(fmt, ...) printf(fmt "\n", __VA_ARGS__)
      |                                                   ^
s43e.c:13:5: note: in expansion of macro ‘LOG’
   13 |     LOG("none");
      |     ^~~
```

```text
===== gcc -std=c17 -DFORM=2 -E -P s43e.c | sed -n '/^int main/,$p' (cc exit=0) =====
int main(void) {
    printf("n=%d" "\n", 1);
    printf("none" "\n");
    return 0;
}
```

```text
===== gcc -std=c2x -DFORM=3 -E -P s43e.c | sed -n '/^int main/,$p' (cc exit=0) =====
int main(void) {
    printf("n=%d" "\n" , 1);
    printf("none" "\n" );
    return 0;
}
```

그림 해설 (한 단계씩):

- ★★★ **FORM 1(`, __VA_ARGS__`)은 여섯 판 전부 에러** — 빈 인자면 `printf("none" "\n", );` — **쉼표가 남는다.** 판이 C23 이어도 매크로는 쉼표를 지워 주지 않는다.
- ★★ **FORM 2(`, ##__VA_ARGS__`)는 GNU 확장** — 빈 인자면 **앞의 쉼표를 먹는다**(`printf("none" "\n");`). 표준 `##` 의 뜻이 아니다 — 표준이라면 `,` 와 빈 인자를 붙여 `,` 가 남는다.
- ★★ **FORM 3(`__VA_OPT__(,)`)은 C23 표준** — 가변 인자가 **있을 때만** `,` 를 넣는다.
- ★★★ **c17 과 c2x 가 갈린 칸 3 / 9 — 전부 gcc 13 이다.** gcc 13 `-std=c2x` 는 **세 FORM 모두 경고가 0** 이 된다(빈 가변 인자가 C23 에서 적법해졌다 — FORM 1 은 경고만 사라지고 에러는 그대로다). **gcc-12 와 clang 18 은 c2x 에서도 경고 수가 c17 과 같다.**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -DFORM=3 -c s43e.c -o /dev/null (cc exit=0) =====
s43e.c:8:39: warning: __VA_OPT__ is not available until C2X
    8 | #define LOG(fmt, ...) printf(fmt "\n" __VA_OPT__(,) __VA_ARGS__)
      |                                       ^
s43e.c: In function ‘main’:
s43e.c:13:15: warning: ISO C99 requires at least one argument for the "..." in a variadic macro
   13 |     LOG("none");
      |               ^
```

```text
===== gcc-12 -std=c17 -Wall -Wextra -pedantic -DFORM=3 -c s43e.c -o /dev/null (cc exit=0) =====
s43e.c:8:39: warning: __VA_OPT__ is not available until C++20
    8 | #define LOG(fmt, ...) printf(fmt "\n" __VA_OPT__(,) __VA_ARGS__)
      |                                       ^
s43e.c: In function ‘main’:
s43e.c:13:15: warning: ISO C99 requires at least one argument for the "..." in a variadic macro
   13 |     LOG("none");
      |               ^
```

```text
===== clang -std=c2x -Wall -Wextra -pedantic -DFORM=3 -c s43e.c -o /dev/null (cc exit=0) =====
s43e.c:13:15: warning: must specify at least one argument for '...' parameter of variadic macro [-Wgnu-zero-variadic-macro-arguments]
   13 |     LOG("none");
      |               ^
s43e.c:8:9: note: macro 'LOG' defined here
    8 | #define LOG(fmt, ...) printf(fmt "\n" __VA_OPT__(,) __VA_ARGS__)
      |         ^
1 warning generated.
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -DFORM=2 -c s43e.c -o /dev/null (cc exit=0) =====
s43e.c:6:40: warning: token pasting of ',' and __VA_ARGS__ is a GNU extension [-Wgnu-zero-variadic-macro-arguments]
    6 | #define LOG(fmt, ...) printf(fmt "\n", ##__VA_ARGS__)
      |                                        ^
s43e.c:6:38: warning: token pasting of ',' and __VA_ARGS__ is a GNU extension [-Wgnu-zero-variadic-macro-arguments]
    6 | #define LOG(fmt, ...) printf(fmt "\n", ##__VA_ARGS__)
      |                                      ^
2 warnings generated.
```

- ★★ **gcc 13 `c17`** — 「`__VA_OPT__` is not available until C2X」 + 「ISO C99 requires at least one argument for the "..." in a variadic macro」.
- ★★ **gcc-12 `c17` 은 같은 자리에서 「until C++20」** 이라고 한다 — **C 모드인데 C++ 판을 댄다.** 문구가 사실과 어긋나는 사례다(규칙 27 — 종료 코드와 경고 수만 근거로 쓴다).
- ★★ **clang 18 `c2x` 는 `__VA_OPT__` 에 대해서는 말이 없고** 「must specify at least one argument for '...' parameter of variadic macro」 를 **c2x 에서도** 낸다 — N3220 은 빈 가변 인자를 허용하므로(「매개변수(`...` 제외)보다 **적으면 안 된다**」) **이 경고는 이 판 clang 의 보수적 선택**이다. ★ clang 은 `c17` 에서도 `__VA_OPT__` 를 **확장이라 경고하지 않았다.**
- ★ clang 의 FORM 2 경고는 **두 줄**(`,` 와 `__VA_ARGS__` 각각 한 번씩 짚는다).

### (6) ★★ 디버그 매크로 — `__FILE__` · `__LINE__` · `__func__`

**언제 쓰나** — 로그에 **호출한 자리**의 파일·줄·함수를 남길 때. ★ 이것이 **함수로 대신할 수 없는** 매크로의 대표 자리다([42번 형제](../42-function-like-macro-pitfalls/)).

```c
/* s43f.c */
#include <stdio.h>

#define STR(x) #x
#define TRACE(fmt, ...) \
    printf("%s:%d %s: " fmt "\n", __FILE__, __LINE__, __func__, __VA_ARGS__)

static void load(int n) {
    TRACE("n=%d", n);
}

int main(void) {
    load(4);
    TRACE("%s", STR(__func__));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s43f.c -o x ; ./x (cc exit=0 · run exit=0) =====
s43f.c:8 load: n=4
s43f.c:13 main: __func__
```

```text
===== gcc -std=c17 -E -P s43f.c | sed -n '/^static void load/,$p' (cc exit=0) =====
static void load(int n) {
    printf("%s:%d %s: " "n=%d" "\n", "s43f.c", 8, __func__, n);
}
int main(void) {
    load(4);
    printf("%s:%d %s: " "%s" "\n", "s43f.c", 13, __func__, "__func__");
    return 0;
}
```

- ★★★ **`__FILE__`·`__LINE__` 은 호출 자리에서 펼쳐진다** — `"s43f.c", 8` · `"s43f.c", 13`. 함수 안에서 `__LINE__` 을 쓰면 **그 함수의 줄**이 찍힌다 — 매크로라야 **부른 자리**의 줄이다.
- ★★★ **`__func__` 는 `-E -P` 뒤에도 `__func__` 그대로** 남았다 — 전처리기가 모르는 이름이다. 컴파일러가 그 자리의 함수 이름(`load`·`main`)으로 채운다.
- ★★ **`STR(__func__)` 는 `"__func__"`** — 문자열화할 수 있는 것은 **토큰의 철자**뿐이다. 함수 이름을 문자열로 얻는 길은 **`__func__` 를 그대로 쓰는 것**이다.

```c
/* s43g.c */
#include <stdio.h>

void where(void) {
    puts("in " __func__);
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s43g.c -o /dev/null (cc exit=1) =====
s43g.c: In function ‘where’:
s43g.c:4:15: error: expected ‘)’ before ‘__func__’
    4 |     puts("in " __func__);
      |         ~     ^~~~~~~~~
      |               )
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s43g.c -o /dev/null (cc exit=1) =====
s43g.c:4:16: error: expected ')'
    4 |     puts("in " __func__);
      |                ^
s43g.c:4:9: note: to match this '('
    4 |     puts("in " __func__);
      |         ^
1 error generated.
```

- ★★ **`"in " __func__` 는 에러** — 문자열 리터럴 이어 붙이기는 **리터럴끼리만** 된다. `__func__` 는 `const char[]` **객체**라 리터럴이 아니다. gcc 「expected ‘)’ before ‘__func__’」, clang 「expected ')'」. `__FILE__` 은 **리터럴로 펼쳐지므로** `"in " __FILE__` 은 된다(★ 이 줄은 던지지 않았다 — 43f 의 `"%s:%d %s: " fmt` 가 리터럴 이어 붙이기의 실측이다).

## 문법 — 형태와 규칙

### 형태

```text
   #define STR(x)   #x                 문자열화 — 인자를 펼치지 않는다
   #define XSTR(x)  STR(x)             ★ 한 겹 더 — 먼저 펼친 뒤 문자열화
   #define CAT(a,b) a ## b             붙이기 — 인자를 펼치지 않는다
   #define XCAT(a,b) CAT(a, b)         ★ 한 겹 더
   #define LOG(fmt, ...) f(fmt __VA_OPT__(,) __VA_ARGS__)   ★ C23
   #define LOG(fmt, ...) f(fmt, ##__VA_ARGS__)              GNU 확장
   __FILE__ · __LINE__                  매크로 — 호출 자리에서 펼쳐진다
   __func__                             ★ 매크로가 아니다 — 식별자(const char[])
```

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 결과 | 층 |
|---|---|---|
| `CAT(., x)` | gcc·clang **에러** | ★★★ 표준은 **미정의** · 에러는 컴파일러 구현 |
| `#define BAD(a) ## a` | 제약 위반 — 치환 목록 맨 앞의 `##` | 표준(제약) · ★ 던지지 않았다 |
| `LOG("none")` + `, __VA_ARGS__` | **남은 쉼표** 에러 | 표준(규칙대로 남는다) |
| `, ##__VA_ARGS__` | 통과 · `-pedantic` 경고 | ★★ 컴파일러 구현(GNU) |
| `"in " __func__` | 에러 | 표준(`__func__` 는 리터럴이 아니다) |

### 규칙 불릿

- ★★★ **`#`·`##` 의 피연산자는 펼쳐지지 않는다** — 매크로 값·`__LINE__` 이 필요하면 **한 겹 더 감싼다.**
- ★★ **`#` 은 공백을 한 칸으로 줄이고 `"`·`\` 를 이스케이프한다.**
- ★★ **`##` 의 결과는 하나의 유효한 토큰이어야 한다** — 아니면 미정의(이 판은 에러).
- ★★ **빈 가변 인자는 `__VA_OPT__`(C23) 또는 `, ##__VA_ARGS__`(GNU)** — 판과 컴파일러를 적어 둔다.
- ★ **`__func__` 는 문자열화도 리터럴 이어 붙이기도 안 된다.**

## 어디서 틀리나

### 1. ★★★ 「`STR(VERSION)` 은 `"3"` 이다」

`"VERSION"` 이다((1)). `#` 의 피연산자는 **펼쳐지지 않는다.** 버전 문자열 매크로가 **매크로 이름을 찍는** 사고가 이것이다.

### 2. ★★★ 「`CAT(tmp_, __LINE__)` 로 줄마다 다른 이름이 생긴다」

`tmp___LINE__` **한 이름**이다((2)) — 두 번 쓰면 **재선언 에러**가 난다(★ 두 번 쓰는 판은 던지지 않았다). `XCAT` 으로 감싸야 `tmp_9` 가 된다.

### 3. ★★ 「`##` 로 잘못된 토큰을 만들면 표준이 에러를 보장한다」

**미정의다**((3)). 이 판의 gcc·clang 은 에러로 막지만 **보장이 아니다.**

### 4. ★★ 「C23 이면 `, __VA_ARGS__` 의 빈 인자 쉼표가 사라진다」

**안 사라진다**((5)) — 여섯 판 전부 에러. C23 이 바꾼 것은 「**빈 인자로 불러도 된다**」이고, **쉼표 처리는 `__VA_OPT__` 를 써야** 한다.

### 5. ★★ 「`-std=c2x` 면 빈 가변 인자 경고가 없어진다」

**gcc 13 만** 그랬다((5)) — gcc-12 와 clang 18 은 c2x 에서도 경고했다. 경고의 유무는 **컴파일러와 판을 함께** 적어야 한다.

### 6. ★★ 「`__func__` 도 `__FILE__` 처럼 매크로다」

**식별자다**((6)) — `-E -P` 뒤에도 그대로 남고, `#__func__` 는 `"__func__"`, `"…" __func__` 는 에러다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 무겁다** — 감싸기 격자 · `##` 결과 · X-매크로 · `__func__` 의 정체가 **모두 표준 문장**이고 두 컴파일러가 같다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | ★★★ **`#`·`##` 피연산자는 펼치지 않음 · 공백 한 칸 · `"`/`\` 이스케이프 · 빈 인자 자리표 · 남는 쉼표 · `__func__` 는 식별자** | 격자 · `-E -P` · 에러 |
| ★★ **조건부 표준** | 판이 조건 | ★★ **`__VA_OPT__` 와 빈 가변 인자 허용은 C23** | 가변 매크로 격자 |
| ★★★ **UB** | 아무 일이나 | ★★★ **`##` 결과가 유효한 토큰이 아님** | 두 컴파일러 에러(= 구현의 선택) |
| **구현 정의 · 미명시** | — | ★ 해당 없음(이 편이 던진 것 중에는) | — |
| ★★ **컴파일러 구현** | 도구의 선택 | ★★ **잘못된 `##` 를 에러로 막음** · **`, ##__VA_ARGS__`(GNU)** · **clang 의 `__VA_OPT__` c17 무경고 · c2x 에서도 빈 인자 경고** · **gcc-12 의 「until C++20」 문구** · 진단이 짚는 열 | 진단 · 격자 |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★★ **`STR(VERSION)` 이 `"VERSION"` 을 만든 것** — 경고 0. 적법한 문자열이다. `CAT(tmp_, __LINE__)` 도 한 번만 쓰면 **조용하다** |
| ★★ **컴파일러 구현** | ★★ **clang `-std=c17` 은 C23 의 `__VA_OPT__` 에 0줄** — 판 경계가 안 보인다 |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **`#`·`##` 가 매크로 값을 쓸 때는 반드시 한 겹 감싼다** — 아무 도구도 알려 주지 않는다.
  - ★★ **에러로 막히는 `##` 는 운이 좋은 편**이다 — 표준은 미정의다.
  - ★★ **빈 가변 인자는 판과 컴파일러마다 경고가 다르다** — 격자를 머리에 두지 말고 빌드에서 재라.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 매크로 값을 문자열로 | ★★★ `XSTR(VERSION)` | `STR(VERSION)` |
| 식 그대로를 문자열로(단언 메시지) | ★★ `STR(expr)`(펼치지 않는 게 목적) | `XSTR`(펼친 글자가 나온다) |
| 줄마다 고유한 이름 | ★★ `XCAT(tmp_, __LINE__)` | `CAT(tmp_, __LINE__)` |
| enum 과 이름표 | ★★ X-매크로 | 두 목록을 손으로 맞추기 |
| 빈 가변 인자 | ★★ C23 이면 `__VA_OPT__(,)` · GNU 전용이면 `, ##__VA_ARGS__` | `, __VA_ARGS__` |
| 로그의 호출 자리 | ★★ 매크로 + `__FILE__`·`__LINE__` + `__func__`(그대로) | `#__func__` · `"…" __func__` |

판단 규칙 두 줄.

- ★★★ **「인자를 펼친 결과가 필요한가」를 먼저 묻는다** — 필요하면 한 겹 감싼다, 아니면 그대로.
- ★★ **토큰을 만드는 매크로는 `-E -P` 로 결과를 한 번 본다.**

## 핵심 문장

- ★★★ **감싸기 격자에서 `STR` 과 `XSTR` 이 갈린 칸은 4 / 9 — 인자 안에 매크로가 있는 칸만. `STR(__LINE__)` 은 `"__LINE__"`, `XSTR(__LINE__)` 은 `"10"`.**
- ★★★ **`#`·`##` 에 붙은 매개변수만 인자를 펼치지 않는다(N3220) — 한 겹 더 감싸면 바깥 매크로에서 먼저 펼쳐진다.**
- ★★ **`XCAT(tmp_, __LINE__)` 은 `tmp_9`, `CAT` 은 `tmp___LINE__` — 고유 이름에는 감싸기가 필수다.**
- ★★★ **`CAT(., x)` 는 gcc·clang 둘 다 에러였지만 표준은 미정의다 — 에러는 컴파일러의 선택이다.**
- ★★ **빈 가변 인자의 `, __VA_ARGS__` 는 여섯 판 전부 남은 쉼표 에러 — `, ##__VA_ARGS__`(GNU)와 `__VA_OPT__(,)`(C23)은 통과, c17 과 c2x 의 경고 차이는 gcc 13 만(3 / 9).**
- ★★ **`__func__` 는 매크로가 아니다 — `-E -P` 뒤에도 남고, `STR(__func__)` 는 `"__func__"`, `"in " __func__` 는 에러.**

## 관련 자료

- [42번 형제 — 함수형 매크로의 함정](../42-function-like-macro-pitfalls/) — ★★ **선행.** 괄호 · 중복 평가.
- [41번 형제 — 전처리기 지시자](../41-preprocessor-directives-and-conditional-compilation/) — ★★ `-E -P` 로 읽는 법.
- [36번 형제 — 가변 인자 함수](../36-variadic-functions-stdarg/) — ★★ **대비.** 가변 **함수**는 런타임에 `va_arg` 로 꺼내고, 가변 **매크로**는 전처리 때 토큰을 옮긴다.
- [40번 형제 — `_Generic`](../40-generic-selection-c11/) — ★ 매크로로 타입별 함수를 고르는 자리.

## 용어 풀이

> **한 겹 더 감싸기(indirection)** — `XSTR(x) STR(x)` 처럼 **`#`·`##` 가 없는 바깥 매크로**를 두어 인자를 **먼저 펼치게** 하는 관용구.\
> 예: `XSTR(VERSION)` → `STR(3)` → `"3"`.

> **자리표(placemarker)** — 빈 인자가 `##` 옆에 올 때 넣는 가짜 토큰. 붙이면 사라진다.\
> 예: `CAT(, z)` → `z`.

> **X-매크로(X-macro)** — 항목 목록을 **매크로 인자 하나를 받는 매크로**로 적어 두고, 그 인자에 서로 다른 양식을 대 여러 선언을 생성하는 관용구.\
> 예: `COLORS(AS_ENUM)` · `COLORS(AS_NAME)`.

> **`__VA_ARGS__`** — 가변 매크로(`...`)의 나머지 인자 전체(쉼표 포함). C99.\
> 예: `LOG("n=%d", 1)` 에서 `1`.

> **`__VA_OPT__(…)`** — 가변 인자가 **비어 있지 않을 때만** 괄호 안 토큰을 넣는 C23 구문.\
> 예: `__VA_OPT__(,)`.

> **`__func__`** — 함수 몸통 안에서 그 함수 이름을 담은 `static const char[]` 처럼 보는 **식별자**(C99). 매크로가 아니다.\
> 예: `printf("%s", __func__)`.

## 더 들어가면

- ★★ **`#` 과 `__VA_OPT__` 를 같이** — N3220 의 예제 `#__VA_OPT__(…)`. ★ 던지지 않았다.
- ★ **재귀처럼 보이는 매크로** — 치환 중인 매크로 이름은 다시 펼쳐지지 않는다(「파란 칠」). ★ 던지지 않았다.
- ★ **`CAT(tmp_, __LINE__)` 을 두 번 쓰는 판** — 재선언 에러의 문구. ★ 던지지 않았다.
