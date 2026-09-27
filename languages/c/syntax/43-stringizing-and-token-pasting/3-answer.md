# c/syntax/43 — 문자열화 `#` 와 토큰 붙이기 `##`: 「**`#`·`##` 에 붙은 인자는 먼저 펼쳐지지 않는다 — 그래서 펼친 결과가 필요하면 한 겹 더 감싼다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **gcc-12 12.4.0** · **clang 18.1.3** ·
> x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s43a.c`\~`s43g.c` 이고, 블록은 **전부 캡처 파일에서 조립**했다.\
> ★★★ **본체 창은 전처리 결과** — 감싸기 격자는 인자 9 × `STR`/`XSTR`.
> ★★ **흔들리는 칸** — 없다. 정규화 규칙은 기본 넷뿐이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 감싸기 격자 — **갈린 칸 4 / 9(`__LINE__` · `VERSION` · `VERSION + 1` · `__FILE__`) · gcc·clang 같음** ★★★

**출력**

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

**왜 그런가**

- ★★★ **갈린 넷은 인자 안에 매크로 이름이 있는 행**이다 — `STR` 의 `x` 는 `#` 의 피연산자라 **펼치지 않고**, `XSTR` 의 `x` 는 **먼저 펼친 뒤** `STR` 에 넘긴다.
- ★★ `VERSION + 1` 은 `"3 + 1"` — 계산하지 않는다. `a    b` 는 `"a b"` — 공백은 한 칸. `"q"` 는 `"\"q\""` — `"`·`\` 앞에 `\`.
- ★★★ `__func__` 는 **두 열 다 `"__func__"`** — 매크로가 아니라 펼칠 것이 없다.

### 2. `##` — **`xy` · `xN` · `x7` · `tmp___LINE__` · `tmp_9` · `++` · `->` · `12` · `z`** ★★★

**출력**

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

**왜 그런가**

- ★★★ `##` 의 피연산자도 **펼쳐지지 않는다** — `CAT(x, N)` 은 `xN`, `XCAT` 으로 감싸야 `x7`.
- ★★★ **줄마다 다른 이름은 `XCAT(tmp_, __LINE__)`** — `CAT` 은 늘 `tmp___LINE__` 이다.
- ★★ `++`·`->`·`12` 는 **유효한 전처리 토큰**이라 된다. `CAT(, z)` 의 빈 인자는 **자리표**가 되어 사라진다.

### 3. 잘못된 토큰 — **gcc 「does not give a valid preprocessing token」 · clang 「an invalid preprocessing token」 · 둘 다 exit=1 · gcc 는 `. x` 를 남긴다** ★★

**출력**

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

**왜 그런가**

- ★★ `.x` · `+-` · `x+` 는 **하나의 전처리 토큰이 아니다.** 두 컴파일러가 **에러**로 막는다(8번 — 표준은 미정의).
- ★ gcc 는 에러를 내고도 **붙이지 않은 두 토큰**으로 출력을 계속 만든다. 짚는 열도 다르다 — gcc 는 인자(3:5), clang 은 호출 첫 열(3:1).

### 4. X-매크로 — **`0 RED` · `1 GREEN` · `2 BLUE`** ★★

**출력**

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

**왜 그런가**

- ★★ `COLORS(AS_ENUM)` 은 `COLOR_RED, COLOR_GREEN, COLOR_BLUE,` 를, `COLORS(AS_NAME)` 은 `"RED", "GREEN", "BLUE",` 를 만든다 — **같은 목록**에서 나와 **순서가 어긋날 수 없다.** `COLOR_COUNT` 는 3.

### 5. 빈 가변 인자 — **FORM 1 은 여섯 판 전부 에러 · FORM 2·3 은 통과 · c17/c2x 가 갈린 칸 3 / 9 는 전부 gcc 13** ★★★

**출력**

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

**왜 그런가**

- ★★★ **FORM 1** — `printf("none" "\n", );` — **쉼표가 남아** 식 에러. C23 이어도 같다(쉼표를 지우는 것은 `__VA_OPT__` 의 일이다).
- ★★ **FORM 2** — GNU 의 `, ##__VA_ARGS__` 는 빈 인자면 **앞 쉼표를 먹는다**(`printf("none" "\n");`).
- ★★ **FORM 3** — C23 `__VA_OPT__(,)` 는 가변 인자가 **있을 때만** `,` 를 넣는다(`printf("none" "\n" );`).
- ★★★ **gcc 13 `c2x` 만 세 FORM 모두 경고 0** — gcc-12 · clang 18 은 c2x 에서도 c17 과 같은 경고 수다.

### 6. 디버그 매크로 — **`s43f.c:8 load: n=4` · `s43f.c:13 main: __func__`** ★★

**출력**

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

**왜 그런가**

- ★★ `__FILE__`·`__LINE__` 은 **호출 자리에서** `"s43f.c"`·`8`·`13` 으로 펼쳐진다. **`__func__` 는 `-E -P` 뒤에도 그대로** — 컴파일러가 `load`·`main` 으로 채운다.
- ★★ 둘째 줄 끝은 `STR(__func__)` = `"__func__"` — 문자열화는 **철자**만 옮긴다.

### 7. 두 매크로를 가르는 규칙 (왜) ★★★

- ★★★ N3220 — 「**`#`·`##` 에 붙지 않은 매개변수**는 인자의 매크로를 **전부 치환한 뒤** 넣는다」. 뒤집으면 `#`·`##` 에 붙은 매개변수는 **안 펼친 인자**를 받는다. `XSTR(x) STR(x)` 의 `x` 는 붙지 않아 **펼친 뒤** `STR` 에 가고, `STR` 이 다시 읽힐 때 그 결과가 `#` 을 만난다.
- ★★ **펼치지 않는 것이 목적이면 `STR`** — `assert` 류의 메시지가 식의 **원래 철자**를 보여 주는 것이 이 성질이다.

### 8. 잘못된 토큰의 층 (경계) ★★★

- ★★★ **표준은 미정의** — N3220 「`##` 의 결과가 유효한 전처리 토큰이 아니면 동작은 미정의」. 3번의 에러는 **컴파일러 구현**(두 컴파일러가 막기로 한 것)이다.
- ★ `++`·`->` 는 **각각 하나의 구두점 토큰**이라 유효하다(2번).

### 9. `__func__` (경계) ★★

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

- ★★ **컴파일되지 않는다** — `__func__` 는 **전처리기가 모르는 식별자**(`static const char __func__[]` 처럼 보는 객체)라 리터럴 이어 붙이기에 끼지 못한다. `__FILE__` 은 **전처리기가 문자열 리터럴로 펼치는 매크로**라 이어 붙일 수 있다.

### 10. 가변 인자 함수와 가변 매크로 (연결) ★★

- ★★ [36번 형제](../36-variadic-functions-stdarg/)의 `va_arg` 는 **런타임에 값**을 꺼내고(타입을 믿어야 한다), `__VA_ARGS__` 는 **전처리 때 토큰**을 옮긴다(타입이 없다).
- ★ `, ##__VA_ARGS__` = **컴파일러 구현(GNU 확장)** · `__VA_OPT__` = **C23 표준**. gcc-12 는 C 모드에서 「`__VA_OPT__` is not available until **C++20**」 이라고 했다 — **C 판을 대야 할 자리에 C++ 판**을 댔다.

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

### 11. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- ★★★ **표준** — 피연산자를 펼치지 않음 · 공백 · 이스케이프 · 자리표 · 남는 쉼표 · `__func__` 는 식별자. **조건부 표준** — `__VA_OPT__`·빈 가변 인자 허용(C23). **UB** — 잘못된 `##`. **컴파일러 구현** — 잘못된 `##` 를 에러로 · `, ##__VA_ARGS__` · 경고의 판별(gcc 13 만 c2x 에서 0 · clang 은 c17 의 `__VA_OPT__` 에 무경고) · gcc-12 문구.
- ★★★ **어떤 도구도 알려 주지 않는다** — `"VERSION"` 은 적법한 문자열이다. `-E -P` 를 읽어야 보인다.

### 12. 경계 (연결) ★

- ★ 괄호·중복 평가 = [42번 형제](../42-function-like-macro-pitfalls/) · `-E -P` = [41번 형제](../41-preprocessor-directives-and-conditional-compilation/).
- ★ **없다** — 36번 형제는 가변 인자 **함수**만 다룬다(`VA_ARGS` 검색 0건).

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s43a.c` | ★★★ **감싸기 격자 9행** · gcc/clang 대조 · `-E -P` | 빌드 2 · 실행 3 · 전처리 1 |
| `s43b.c` | ★★★ `##` 아홉 줄 | 전처리 2 |
| `s43c.c` | ★★ 잘못된 토큰 | 진단 2 · 전처리 1 |
| `s43d.c` | ★★ X-매크로 | 실행 1 · 전처리 1 |
| `s43e.c` | ★★★ **가변 매크로 격자 18칸** · 펼침 3 · 진단 5 | 컴파일 18 + 8 |
| `s43f.c` · `s43g.c` | ★★ 디버그 매크로 · `__func__` | 실행 1 · 전처리 1 · 진단 2 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. **이 편의 블록은 정규화 없이 전부 동일**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **3번의 에러**(표준은 미정의) · **5번의 경고 수 전부** · **10번의 gcc-12 문구.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `#__VA_OPT__` · `##` 가 치환 목록 맨 앞에 오는 제약 위반 · `CAT(tmp_, __LINE__)` 을 두 번 쓰는 판 · `"in " __FILE__`.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **5번 격자** — C23 지원이 굳으면 gcc-12·clang 의 c2x 칸 경고가 바뀔 수 있다.
