# c/syntax/41 — 전처리기 지시자와 조건부 컴파일: 「**전처리기는 컴파일러보다 먼저 도는 텍스트 치환기다 — 컴파일러는 그 결과만 받는다**」 — 정리 (힌트)

★★★ **본체는 넷째 창 — 전처리 결과다.** `gcc -E -P` 가 찍는 것이 **컴파일러가 받는 텍스트 전부**다. 매크로 이름도 `#if` 도 거기엔 없다.
★★★ `#if` 격자에서 **`#ifdef X` 와 고른 분기가 갈린 칸 11 / 40** — 「`#if X` 는 `#ifdef X` 의 줄임」이 **틀렸다는** 수다. **gcc 와 clang 은 고른 분기로 3 / 24 칸 갈렸고**, 셋 다 `#elifdef` 의 c17 행이다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | ★★ 매크로 안의 오류를 **어느 줄로 가리키나** · `-Wundef` · `#error`/`#warning` · 전처리 식의 에러 | 씀 |
| ② 실행 출력 | — | ★ **잴 것이 없다** — 이 편의 일은 **실행 전에** 끝난다. 격자의 값은 실행이 아니라 전처리 결과에 남은 토큰(`branch_1`/`branch_2`)이다 |
| ③ sanitizer | — | 부적용(런타임에 아무것도 남지 않는다) |
| ④ `nm` | ★ **매크로 이름이 목적 파일에 없다** | 씀(한 블록) |
| ★★★ ⑤ **전처리 결과(`-E -P` · `-dM -E` · `-v`)** | ★ **본체** — 남은 텍스트 · 고른 분기 · 미리 정의된 매크로 · include 검색 순서 | 씀 |
| ★ 제5의 상태 | 「**컴파일러는 매크로를 아나**」를 진단으로 물으면 두 컴파일러 다 `in expansion of macro` 로 **아는 것처럼** 답한다. **전처리 결과(`.i`)를 따로 컴파일해 바꿔 물으니** 매크로 언급이 사라지고 **확장된 줄**만 가리켰다 — 매크로를 아는 것은 컴파일러가 아니라 **전처리기가 넘긴 위치 정보**다 | 창을 바꿔 답함 |

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
| 안 흔들린다 | ★★★ **전처리 결과 전부 · `#if` 격자 · 미리 정의된 매크로 격자 · include 격자** · 진단 문구 | 같은 판 · 같은 플래그면 같다 — 재대조에서 **179 블록 전부 동일** |
| 안 흔들린다 | ★ `-E`(`-P` 없음)의 줄 표지 `# 1 "/usr/include/stdc-predef.h" 1 3 4` | 시스템 경로다(로컬 경로가 아니다) — 판이 바뀌면 달라질 수 있다 |
| **흔들린다** | — | 이 편에는 없다 — 정규화 규칙은 기본 넷뿐이다 |

## 한눈에 — 쉽게 말하면

**전처리기는 「원고를 인쇄소에 넘기기 전에 편집자가 하는 일」이다.**

- **편집자는 문장의 뜻을 모른다** — 「이 낱말을 저 낱말로 바꿔라」·「이 문단은 판본 B 에서만 싣는다」만 한다. → **토큰 치환과 조건부 포함**
- **인쇄소(컴파일러)는 편집이 끝난 원고만 받는다** — 편집자의 메모는 원고에 없다. → **매크로 이름도 `#if` 도 컴파일러에 안 간다**
- **「판본 B 면 싣는다」의 판본 B 가 정해지지 않았으면 「아니다」로 친다** — 물어보지 않는다. → **정의 안 된 이름은 `#if` 에서 `0`**
- **「다른 책에서 이 장을 통째로 가져와라」** — 어느 서가에서 먼저 찾을지 순서가 있다. → **`#include` 검색 경로**
- **편집자마다 미리 붙여 두는 도장이 다르다** — 판본 번호 · 편집자 이름. → **미리 정의된 매크로**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 편집이 끝난 원고 | `gcc -E -P` 의 출력 | ★★★ (1) |
| 메모는 원고에 없다 | `nm` 에 `LIMIT`·`TWICE` 가 없다 · `.i` 를 컴파일하면 매크로 언급이 사라진다 | ★★ (1)·(2) |
| 정해지지 않은 판본 = 아니다 | `#if X` 에서 `X` 가 없으면 `0` · `-Wundef` 로만 경고 | ★★★ (3) |
| 서가 순서 | `"…"` 는 옆 파일 → `-iquote` → `-I` → 시스템 · `<…>` 는 `-I` → 시스템 | ★★ (5) |
| 편집자 도장 | `__STDC_VERSION__` · `__GNUC__` · `__clang__` | ★★ (4) |

```text
   s41a.c                              gcc -E -P s41a.c                 컴파일러
   ---------------------------         ------------------------         ----------------
   #define LIMIT 10          ──┐
   #define TWICE(x) ((x) * 2)  │ 지시자는 전부 사라진다
   #ifdef VERBOSE              │ (-DVERBOSE 가 없으면 이 줄들째)
   int verbose_mode = 1;       │
   #endif                    ──┘
   int limit_twice(void)              int limit_twice(void)            이것만 받는다
     { return TWICE(LIMIT); }  ─────▶   { return ((10) * 2); }  ─────▶  (LIMIT·TWICE 라는
                                                                        이름을 모른다)
```

- ★★★ **이 주제는 「표준」 칸이 거의 전부**다 — 치환 · `#if` 의 `0` 규칙 · 건너뛴 그룹의 처리가 **모두 표준 문장**이다.
- ★★ **「구현 정의」 칸은 include 검색 순서**, **「컴파일러 구현」 칸은 판 이전 지시자의 처리(`#elifdef`)와 미리 정의된 매크로**에 몰린다.

> **전처리(preprocessing)** — 컴파일 전에 소스 텍스트를 **토큰 단위로** 고치는 단계. `#` 로 시작하는 줄(지시자)과 매크로 치환이 여기서 끝난다.\
> 예: `gcc -E` 가 이 단계까지만 돌린다.

> **`-P`** — `-E` 출력에서 **줄 표지**(`# 1 "s41a.c"` 같은 원래 파일·줄 정보)를 빼는 gcc/clang 옵션.\
> 예: `gcc -E -P s41a.c`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **전처리가 「컴파일 이전」이라는 것을 어떻게 눈으로 확인하나** — `-E -P` 의 결과 · 목적 파일 · 매크로 안 오류의 진단.
2. ★★★ **`#if X` · `#if defined(X)` · `#ifdef X` 는 언제 갈리나** — 정의 안 됨 · `0` · 문자열 · C23 `#elifdef`.
3. ★★ **전처리기가 「미리 아는 것」과 「찾아가는 순서」는 누가 정하나** — 미리 정의된 매크로 · `#include` 검색 경로.

## 동작 방식

### (1) ★★★ 전처리 결과 — 매크로는 사라지고 텍스트만 남는다

**언제 쓰나** — 매크로·조건부 컴파일이 **실제로 무엇을 만들었나** 확인할 때. 이 편의 모든 실험이 이 창에서 시작한다.

```c
/* s41a.c */
#define LIMIT 10
#define TWICE(x) ((x) * 2)

#ifdef VERBOSE
int verbose_mode = 1;
#endif

int limit_twice(void) { return TWICE(LIMIT); }
```

```text
===== gcc -std=c17 -E -P s41a.c (cc exit=0) =====
int limit_twice(void) { return ((10) * 2); }
```

```text
===== gcc -std=c17 -E -P -DVERBOSE s41a.c (cc exit=0) =====
int verbose_mode = 1;
int limit_twice(void) { return ((10) * 2); }
```

```text
===== gcc -std=c17 -E s41a.c (cc exit=0) =====
# 0 "s41a.c"
# 0 "<built-in>"
# 0 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 0 "<command-line>" 2
# 1 "s41a.c"







int limit_twice(void) { return ((10) * 2); }
```

```text
===== gcc -std=c17 -DVERBOSE -c s41a.c -o s41a.o && nm s41a.o (cc exit=0) =====
0000000000000000 T limit_twice
0000000000000000 D verbose_mode
```

그림 해설 (한 단계씩):

- ★★★ **`#define`·`#ifdef`·`#endif` 줄이 전부 사라졌다.** 남은 것은 **`return ((10) * 2);`** — `TWICE(LIMIT)` 이 **글자 그대로** 바뀌었다. 계산(`20`)은 하지 않는다. 계산은 컴파일러 몫이다.
- ★★ **`-DVERBOSE` 한 개가 `int verbose_mode = 1;` 한 줄을 살렸다** — 조건부 컴파일은 **어느 텍스트를 컴파일러에 넘길지** 고르는 일이다.
- ★★ **`-P` 를 빼면 줄 표지가 남는다** — `# 1 "s41a.c"` 는 「여기서부터 `s41a.c` 의 1행」이라는 뜻이다. 사라진 지시자 자리는 **빈 줄**로 채워 줄 번호를 맞춘다. ★ 컴파일러가 진단에 원래 줄 번호를 찍을 수 있는 것은 **이 표지 덕분**이다((2)).
- ★★★ **`nm` 에 `LIMIT` 도 `TWICE` 도 없다** — 목적 파일에 남은 이름은 `limit_twice` 와 `verbose_mode` 둘뿐이다. **매크로는 컴파일러 앞에서 이미 끝난 일**이다.

### (2) ★★★ 매크로 안의 오류 — 누가 매크로를 기억하나

**언제 쓰나** — 에러가 매크로 정의 줄을 가리키는데 **고칠 곳은 쓰는 자리**일 때.

```c
/* s41b.c */
#define FIELD(p) ((p)->val)

struct box { int val; };

int get(int n) {
    return FIELD(n);
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s41b.c -o /dev/null (cc exit=1) =====
s41b.c: In function ‘get’:
s41b.c:1:22: error: invalid type argument of ‘->’ (have ‘int’)
    1 | #define FIELD(p) ((p)->val)
      |                      ^~
s41b.c:6:12: note: in expansion of macro ‘FIELD’
    6 |     return FIELD(n);
      |            ^~~~~
s41b.c:7:1: warning: control reaches end of non-void function [-Wreturn-type]
    7 | }
      | ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s41b.c -o /dev/null (cc exit=1) =====
s41b.c:6:12: error: member reference type 'int' is not a pointer
    6 |     return FIELD(n);
      |            ^~~~~~~~
s41b.c:1:24: note: expanded from macro 'FIELD'
    1 | #define FIELD(p) ((p)->val)
      |                   ~~~  ^
1 error generated.
```

- ★★★ **gcc 는 매크로 정의 줄(1:22)을 먼저 가리키고 `note: in expansion of macro ‘FIELD’` 로 쓰는 자리(6:12)를 덧붙인다.** clang 은 **거꾸로** — 쓰는 자리(6:12)가 본문이고 `note: expanded from macro 'FIELD'` 로 정의 줄(1:24)을 덧붙인다. **짚는 곳은 같은데 순서가 반대다.**
- ★ gcc 는 에러 뒤 `control reaches end of non-void function` 까지 낸다 — 첫 에러의 여파다.

**그럼 컴파일러는 매크로를 아는가 — 전처리 결과를 따로 컴파일해 본다.**

```text
===== gcc -std=c17 -E -P s41b.c -o s41b.i && cat s41b.i (cc exit=0) =====
struct box { int val; };
int get(int n) {
    return ((n)->val);
}
```

```text
===== gcc -std=c17 -c s41b.i -o /dev/null (cc exit=1) =====
s41b.i: In function ‘get’:
s41b.i:3:16: error: invalid type argument of ‘->’ (have ‘int’)
    3 |     return ((n)->val);
      |                ^~
```

```text
===== gcc -std=c17 -E s41b.c -o s41lm.i && gcc -std=c17 -c s41lm.i -o /dev/null (cc exit=1) =====
s41b.c: In function ‘get’:
s41b.c:6:16: error: invalid type argument of ‘->’ (have ‘int’)
    6 |     return FIELD(n);
      |                ^~
```

- ★★★ **`.i`(`-P` 로 만든 것)를 컴파일하면 `in expansion of macro` 가 사라진다** — 에러는 `s41b.i:3:16`, **확장된 줄** `return ((n)->val);` 을 가리킨다. 컴파일러 본체는 `FIELD` 라는 이름을 **모른다.**
- ★★★ **줄 표지를 남긴 `.i`(`-P` 없음)를 컴파일하면 파일·줄은 `s41b.c:6` 으로 돌아오지만 매크로 note 는 여전히 없다.** 그리고 **캐럿이 어긋난다** — 16열은 확장된 줄 `return ((n)->val);` 의 `->` 자리인데, gcc 가 원래 파일에서 다시 읽어 보여 준 줄은 `return FIELD(n);` 이다.
- ★★ **결론** — 「매크로 안에서 났다」를 알려 주는 것은 **gcc·clang 이 전처리와 컴파일을 한 프로세스에서 돌리며 넘기는 확장 위치 정보**다. 줄 표지는 **파일과 줄만** 나른다.

```text
   s41b.c ──(한 번에)──▶ gcc -c        진단: 1:22 error + 6:12 note: in expansion of macro 'FIELD'
                                        (전처리기가 넘긴 「확장 위치」가 있다)

   s41b.c ──-E -P──▶ s41b.i ──▶ gcc -c   진단: s41b.i:3:16 error          매크로 언급 없음
   s41b.c ──-E────▶ s41lm.i ──▶ gcc -c   진단: s41b.c:6:16 error          줄 표지로 줄만 돌아온다
                                         (보여 주는 줄은 원본 · 열은 확장 결과 기준 → 어긋남)
```

### (3) ★★★ `#if` 격자 — 식 다섯 × 정의 넷 × 컴파일러 둘

**언제 쓰나** — `-D` 로 기능을 켜고 끄는 코드에서 **`#if X` 와 `#ifdef X` 중 무엇을 쓸지** 고를 때.

```c
/* s41c.c */
#if FORM == 1
#  if X
branch_1
#  else
branch_2
#  endif
#elif FORM == 2
#  if defined(X)
branch_1
#  else
branch_2
#  endif
#elif FORM == 3
#  ifdef X
branch_1
#  else
branch_2
#  endif
#elif FORM == 4
#  if X == 1
branch_1
#  else
branch_2
#  endif
#endif
```

```c
/* s41c5.c */
#if 0
#elifdef X
branch_1
#else
branch_2
#endif
```

```text
===== #if 격자 — 식 5 × 판 · 정의 4 × 컴파일러 2 (s41c.c) (exit=0) =====
식 (판)                   	gcc (없음)	gcc -DX	gcc -DX=0	gcc -DX="s"	clang (없음)	clang -DX	clang -DX=0	clang -DX="s"
#if X (c17)               	2	1	2	에러	2	1	2	에러
#if defined(X) (c17)      	2	1	1	1	2	1	1	1
#ifdef X (c17)            	2	1	1	1	2	1	1	1
#if X == 1 (c17)          	2	1	2	에러	2	1	2	에러
#if 0 / #elifdef X (c17)  	2	2	2	2	2 +경고	1 +경고	1 +경고	1 +경고
#if 0 / #elifdef X (c2x)  	2	1	1	1	2	1	1	1
(칸 = $CC -std=<판> -Wall -Wextra -pedantic [-DFORM=<행>] <정의> -E -P <소스> 가 남긴 branch_N 의 N · 1~4행 s41c.c · 5행 s41c5.c · 에러 = exit≠0 · +경고 = warning: 줄 있음)
#ifdef X 행과 고른 분기가 갈린 칸 11 / 40
gcc 와 clang 이 고른 분기로 갈린 칸 3 / 24 · 경고까지 넣으면 4 / 24
#elifdef 의 c17 행과 c2x 행이 고른 분기로 갈린 칸 3 / 8
```

그림 해설 (한 단계씩):

- ★★★ **`#ifdef X` 와 `#if defined(X)` 는 한 칸도 안 갈렸다** — 둘 다 「**정의돼 있나**」만 본다. `-DX=0` 도 `-DX="s"` 도 **정의돼 있으니 1**.
- ★★★ **`#if X` 는 「값이 0 이 아닌가」를 본다** — `-DX=0` 이면 **2**, `-DX` 는 `X` 를 `1` 로 정의하므로 **1**. ★ **정의 안 됨도 2** — 매크로 치환 뒤 남은 식별자 `X` 는 **`0` 으로 바뀐다**(표준). **에러도 경고도 없다**(`-Wall -Wextra -pedantic` 에서도).
- ★★★ **`-DX="s"` 면 `#if X` 와 `#if X == 1` 은 에러** — 문자열 리터럴은 **전처리 식에 올 수 없다.** 같은 정의가 `#ifdef` 행에서는 **조용히 1** 이다.
- ★★★ **`#elifdef` 의 c17 행은 gcc 와 clang 이 갈린다** — **gcc 는 네 칸 모두 2**(`-DX` 인데도 `#else` 쪽), **clang 은 1 + 경고**. c2x 행은 둘 다 표준대로 갈렸다. ★ 「갈린 칸 3 / 24」의 셋이 전부 이 행이다. 이유는 (6).
- ★ **`#if X == 1` 은 `#if X` 와 같은 칸을 냈다** — 이 정의 넷에서는 `X` 가 `1`·`0`·없음·문자열뿐이라서다. `-DX=2` 면 둘이 갈린다(던지지 않았다 — 식의 뜻이 다를 뿐이다).

**정의 안 된 이름이 `0` 이 되는 것은 `-Wundef` 로만 보인다.**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -DFORM=1 -E -P s41c.c -o /dev/null && clang -std=c17 -Wall -Wextra -pedantic -DFORM=1 -E -P s41c.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wundef -DFORM=1 -E -P s41c.c -o /dev/null && gcc -std=c17 -Wundef -DFORM=4 -DX=abc -E -P s41c.c -o /dev/null (cc exit=0) =====
s41c.c:2:7: warning: "X" is not defined, evaluates to 0 [-Wundef]
    2 | #  if X
      |       ^
<command-line>: warning: "abc" is not defined, evaluates to 0 [-Wundef]
s41c.c:20:7: note: in expansion of macro ‘X’
   20 | #  if X == 1
      |       ^
```

```text
===== clang -std=c17 -Wundef -DFORM=1 -E -P s41c.c -o /dev/null && clang -std=c17 -Wundef -DFORM=4 -DX=abc -E -P s41c.c -o /dev/null (cc exit=0) =====
s41c.c:2:7: warning: 'X' is not defined, evaluates to 0 [-Wundef]
    2 | #  if X
      |       ^
1 warning generated.
s41c.c:20:7: warning: 'abc' is not defined, evaluates to 0 [-Wundef]
   20 | #  if X == 1
      |       ^
<command line>:2:11: note: expanded from macro 'X'
    2 | #define X abc
      |           ^
1 warning generated.
```

- ★★★ **`-Wall -Wextra -pedantic` 은 0줄**(18-A — 두 컴파일러 · `cc exit=0`). **`-Wundef` 를 줘야** 「`X` is not defined, evaluates to 0」 이 나온다.
- ★★ **오타도 같은 길로 빠진다** — `-DX=abc` 면 `#if X == 1` 은 `#if abc == 1` → `abc` 가 정의 안 됐으니 `0 == 1` → **조용히 2**. `-Wundef` 는 이것도 잡는다(`"abc" is not defined`).

**문자열이 들어오면 — 두 컴파일러가 짚는 곳이 다르다.**

```text
===== gcc -std=c17 -DFORM=4 '-DX="s"' -E -P s41c.c -o /dev/null (cc exit=1) =====
<command-line>: error: token ""s"" is not valid in preprocessor expressions
s41c.c:20:7: note: in expansion of macro ‘X’
   20 | #  if X == 1
      |       ^
```

```text
===== clang -std=c17 -DFORM=4 '-DX="s"' -E -P s41c.c -o /dev/null (cc exit=1) =====
s41c.c:20:7: error: invalid token at start of a preprocessor expression
   20 | #  if X == 1
      |       ^
<command line>:2:11: note: expanded from macro 'X'
    2 | #define X "s"
      |           ^
1 error generated.
```

- ★★ **gcc 는 `<command-line>` 을 에러 위치로 댄다** — 문제의 토큰 `"s"` 가 **명령줄의 `-D` 에서 왔기** 때문이다. `note: in expansion of macro ‘X’` 가 소스의 20행을 짚는다. clang 은 20행이 본문이고 `<command line>:2:11` 에 가짜 `#define X "s"` 줄을 보여 준다 — **`-D` 는 전처리기에게 「파일 앞에 `#define` 한 줄」이다.**

### (4) ★★ 미리 정의된 매크로 — 판과 컴파일러의 도장

**언제 쓰나** — `#if __STDC_VERSION__ >= …` 로 판을 가르거나, 컴파일러별 우회 코드를 넣을 때.

```text
===== 미리 정의된 매크로 — 매크로 8 × 컴파일러·판 9 (exit=0) =====
매크로            	gcc c11	gcc c17	gcc gnu17	gcc c2x	gcc-12 c2x	clang c11	clang c17	clang gnu17	clang c2x
__STDC__          	1	1	1	1	1	1	1	1	1
__STDC_VERSION__  	201112L	201710L	201710L	202000L	202000L	201112L	201710L	201710L	202311L
__STRICT_ANSI__   	1	1	(없음)	1	1	1	1	(없음)	1
__GNUC__          	13	13	13	13	12	4	4	4	4
__clang__         	(없음)	(없음)	(없음)	(없음)	(없음)	1	1	1	1
__linux__         	1	1	1	1	1	1	1	1	1
linux             	(없음)	(없음)	1	(없음)	(없음)	(없음)	(없음)	1	(없음)
unix              	(없음)	(없음)	1	(없음)	(없음)	(없음)	(없음)	1	(없음)
(칸 = $CC -std=<판> -dM -E - </dev/null 이 찍은 #define 의 값 · (없음) = 정의 안 됨)
c17 과 gnu17 이 갈린 칸(gcc·clang) 6 / 16
gcc c2x 와 clang c2x 가 갈린 칸 3 / 8
```

```text
===== for k in 'gcc -std=c17' 'clang -std=c17'; do printf '%s : %s 개\n' "$k" $($k -dM -E - </dev/null | wc -l); done (exit=0) =====
gcc -std=c17 : 400 개
clang -std=c17 : 388 개
```

그림 해설 (한 단계씩):

- ★★★ **`__STDC_VERSION__` 은 c11 `201112L` · c17 `201710L`** — 두 컴파일러가 같다. ★★ **c2x 는 갈린다 — gcc 13 · gcc-12 는 `202000L`, clang 18 은 `202311L`**. `202311L` 은 N3220 이 C23 에 준 값이고, gcc 의 `202000L` 은 **「C23 이 확정되기 전의 임시 값」** 으로 보인다(★ gcc 문서로 확인하지 않았다 — 값만 실측).\
  ★ 그래서 `#if __STDC_VERSION__ >= 202311L` 은 **이 판의 gcc `-std=c2x` 에서 거짓**이다.
- ★★ **`__GNUC__` 는 clang 에서도 `4`** — clang 은 GNU 확장을 흉내 내며 **gcc 4 인 척**한다. `#ifdef __GNUC__` 로 「gcc 인가」를 가르면 clang 도 들어온다. **`__clang__` 을 먼저** 봐야 한다.
- ★★ **`linux`·`unix`(밑줄 없음)는 `gnu17` 에만 있다** — `c17` 은 **`__STRICT_ANSI__` 를 켜고** 사용자 이름 공간을 침범하는 이 둘을 뺀다. **`__linux__` 는 양쪽에 다 있다.** 「c17 과 gnu17 이 갈린 칸 6 / 16」이 이 세 줄 × 두 컴파일러다.
- ★ 미리 정의된 매크로는 **gcc 400 개 · clang 388 개**(`-std=c17`) — 표준이 요구하는 것은 그중 몇 개뿐이고 **나머지는 구현의 선택**이다.

### (5) ★★ `#include "…"` 대 `<…>` — 검색 순서

**언제 쓰나** — 같은 이름의 헤더가 여러 곳에 있거나, 「못 찾음」이 날 때.

```c
/* s41i1.c */
#include "s41q.h"
```

```c
/* s41i2.c */
#include <s41q.h>
```

```text
===== head qd/s41q.h id/s41q.h s41q.h (exit=0) =====
==> qd/s41q.h <==
int from_qd;

==> id/s41q.h <==
int from_id;

==> s41q.h <==
int from_here;
```

```text
===== include 검색 — 옆 파일 2 × 플래그 4 × 형태 2 × 컴파일러 2 (exit=0) =====
옆 파일 · 플래그              	gcc "…"	gcc <…>	clang "…"	clang <…>
s41q.h 있음 · (플래그 없음)   	옆(here)	못 찾음	옆(here)	에러 · 옆(here) 로 복구
s41q.h 있음 · -iquote qd      	옆(here)	못 찾음	옆(here)	에러 · 옆(here) 로 복구
s41q.h 있음 · -I id           	옆(here)	id	옆(here)	id
s41q.h 있음 · -iquote qd -I id	옆(here)	id	옆(here)	id
s41q.h 없음 · (플래그 없음)   	못 찾음	못 찾음	못 찾음	못 찾음
s41q.h 없음 · -iquote qd      	qd	못 찾음	qd	에러 · qd 로 복구
s41q.h 없음 · -I id           	id	id	id	id
s41q.h 없음 · -iquote qd -I id	qd	id	qd	id
(칸 = $CC -std=c17 <플래그> -E -P s41i1.c(#include "s41q.h") / s41i2.c(#include <s41q.h>) 가 가져온 파일)
gcc 와 clang 이 갈린 행 3 / 8
```

```text
===== gcc -std=c17 -iquote qd -I id -v -E -P s41i1.c -o /dev/null | sed -n '/search starts here/,/End of search/p' (cc exit=0) =====
#include "..." search starts here:
 qd
#include <...> search starts here:
 id
 /usr/lib/gcc/x86_64-linux-gnu/13/include
 /usr/local/include
 /usr/include/x86_64-linux-gnu
 /usr/include
End of search list.
```

```text
===== clang -std=c17 -iquote qd -I id -v -E -P s41i1.c -o /dev/null | sed -n '/search starts here/,/End of search/p' (cc exit=0) =====
#include "..." search starts here:
 qd
#include <...> search starts here:
 id
 /usr/lib/llvm-18/lib/clang/18/include
 /usr/local/include
 /usr/include/x86_64-linux-gnu
 /usr/include
End of search list.
```

그림 해설 (한 단계씩):

- ★★★ **`"…"` 는 소스 파일 옆을 먼저 본다** — 옆에 `s41q.h` 가 있으면 `-iquote`·`-I` 가 무엇이든 **옆 파일**이다. 옆에 없으면 **`-iquote` → `-I` → 시스템** 순.
- ★★★ **`<…>` 는 옆 파일도 `-iquote` 도 안 본다** — `-I` 와 시스템 경로뿐이다(`-v` 가 찍은 두 목록이 그대로다). 표준은 「`"…"` 가 실패하면 `<…>` 로 다시 찾는다」까지만 정하고 **어디를 어떤 순서로 보는지는 구현 정의**다.
- ★★ **gcc 와 clang 이 갈린 행 3 / 8 — 전부 「`<…>` 를 못 찾은」 칸이다.** gcc 는 `fatal error` 로 멈추고, **clang 은 에러를 내면서 `"…"` 로 찾은 파일을 넣고 계속 간다**(에러 복구). **둘 다 `exit=1`** 이라 빌드는 똑같이 실패한다 — 갈린 것은 **에러 뒤 전처리 결과**다.

```text
===== gcc -std=c17 -iquote qd -E -P s41i2.c -o /dev/null (cc exit=1) =====
s41i2.c:1:10: fatal error: s41q.h: No such file or directory
    1 | #include <s41q.h>
      |          ^~~~~~~~
compilation terminated.
```

```text
===== clang -std=c17 -iquote qd -E -P s41i2.c -o /dev/null (cc exit=1) =====
s41i2.c:1:10: error: 's41q.h' file not found with <angled> include; use "quotes" instead
    1 | #include <s41q.h>
      |          ^~~~~~~~
      |          "s41q.h"
1 error generated.
```

- ★ clang 은 **fix-it**(`"s41q.h"`)까지 제안한다. **「옆에 있는데 `<…>` 로 썼다」는 실수를 알아보는 것**은 clang 쪽뿐이다.

### (6) ★★ C23 지시자를 옛 판에서 쓰면 — `#elifdef`·`#warning`

**언제 쓰나** — C23 문법을 `-std=c17` 코드에 섞을 때. ★★★ **(3) 의 격자에서 gcc 만 네 칸 다 2 를 낸 이유**다.

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -DX -E -P s41c5.c (cc exit=0) =====
branch_2
```

```text
===== clang -std=c17 -pedantic -DX -E -P s41c5.c -o /dev/null (cc exit=0) =====
s41c5.c:2:2: warning: use of a '#elifdef' directive is a C23 extension [-Wc23-extensions]
    2 | #elifdef X
      |  ^
1 warning generated.
```

```text
===== gcc -std=gnu17 -pedantic -DX -E -P s41c5.c (cc exit=0) =====
s41c5.c:2:11: warning: #elifdef before C2X is a GCC extension
    2 | #elifdef X
      |           ^
branch_1
```

```c
/* s41e.c */
#if 1
int first;
#elifdef X
int second;
#endif
```

```text
===== gcc -std=c17 -pedantic -E -P s41e.c -o /dev/null (cc exit=1) =====
s41e.c:3:2: error: invalid preprocessing directive #elifdef
    3 | #elifdef X
      |  ^~~~~~~
```

```text
===== clang -std=c17 -pedantic -E -P s41e.c -o /dev/null (cc exit=0) =====
s41e.c:3:2: warning: use of a '#elifdef' directive is a C23 extension [-Wc23-extensions]
    3 | #elifdef X
      |  ^
1 warning generated.
```

그림 해설 (한 단계씩):

- ★★★ **gcc `-std=c17` 은 `#elifdef` 를 지시자로 모른다.** 그래서 두 자리에서 **정반대로** 군다 —
  - **건너뛰는 그룹 안**(`#if 0` 뒤)이면 **모르는 지시자를 조용히 무시**한다(건너뛰는 그룹의 지시자는 이름만 본다 — 표준). `#elifdef X` 가 **없는 줄**이 되고 `#else` 로 간다 → `-DX` 인데 **`branch_2` · 진단 0줄 · `exit=0`**. ★★★ **가장 나쁜 칸이다** — 틀린 분기를 골랐는데 아무도 말하지 않는다.
  - **살아 있는 그룹 안**(`#if 1` 뒤)이면 `invalid preprocessing directive #elifdef` **에러**.
- ★★ **gcc `-std=gnu17` 은 `#elifdef` 를 확장으로 받는다** — `-pedantic` 경고 「`#elifdef` before C2X is a GCC extension」 + `branch_1`. **같은 gcc 가 `c17` 과 `gnu17` 에서 다른 분기를 고른다.**
- ★★ **clang 18 은 `-std=c17` 에서도 `#elifdef` 를 받고** `-Wc23-extensions` 경고를 낸다 — 두 자리 모두.

```text
===== gcc -std=c17 -pedantic -DLIMIT=3 -c s41w.c -o /dev/null (cc exit=0) =====
s41w.c:1:2: warning: #warning before C2X is a GCC extension
    1 | #warning "check the limit"
      |  ^~~~~~~
s41w.c:1:2: warning: #warning "check the limit" [-Wcpp]
```

```text
===== clang -std=c17 -pedantic -DLIMIT=3 -c s41w.c -o /dev/null (cc exit=0) =====
s41w.c:1:2: warning: #warning is a C23 extension [-Wpedantic]
    1 | #warning "check the limit"
      |  ^
s41w.c:1:2: warning: "check the limit" [-W#warnings]
2 warnings generated.
```

```text
===== gcc -std=c2x -pedantic -DLIMIT=3 -c s41w.c -o /dev/null (cc exit=0) =====
s41w.c:1:2: warning: #warning "check the limit" [-Wcpp]
    1 | #warning "check the limit"
      |  ^~~~~~~
```

```text
===== clang -std=c2x -pedantic -DLIMIT=3 -c s41w.c -o /dev/null (cc exit=0) =====
s41w.c:1:2: warning: "check the limit" [-W#warnings]
    1 | #warning "check the limit"
      |  ^
1 warning generated.
```

```c
/* s41w.c */
#warning "check the limit"

#ifndef LIMIT
#error "LIMIT is not defined"
#endif

int limit = LIMIT;
```

- ★★ **`#warning` 은 C23 에서 표준이 됐다** — `-std=c17 -pedantic` 이면 gcc 「`#warning` before C2X is a GCC extension」, clang 「`#warning` is a C23 extension」. `-std=c2x` 면 그 줄이 빠지고 **경고 문구만** 남는다. ★ **`#warning` 은 `exit=0`** — 빌드를 멈추지 않는다.

```text
===== gcc -std=c2x -c s41w.c -o /dev/null (cc exit=1) =====
s41w.c:1:2: warning: #warning "check the limit" [-Wcpp]
    1 | #warning "check the limit"
      |  ^~~~~~~
s41w.c:4:2: error: #error "LIMIT is not defined"
    4 | #error "LIMIT is not defined"
      |  ^~~~~
s41w.c:7:13: error: ‘LIMIT’ undeclared here (not in a function)
    7 | int limit = LIMIT;
      |             ^~~~~
```

```text
===== clang -std=c2x -c s41w.c -o /dev/null (cc exit=1) =====
s41w.c:1:2: warning: "check the limit" [-W#warnings]
    1 | #warning "check the limit"
      |  ^
s41w.c:4:2: error: "LIMIT is not defined"
    4 | #error "LIMIT is not defined"
      |  ^
s41w.c:7:13: error: use of undeclared identifier 'LIMIT'
    7 | int limit = LIMIT;
      |             ^
1 warning and 2 errors generated.
```

- ★★ **`#error` 는 `exit=1`** 이지만 **전처리가 거기서 멈추지 않는다** — 두 컴파일러 다 **다음 줄의 `LIMIT` 까지** 가서 에러를 하나 더 냈다. 「`#error` 는 즉시 중단」이라고 믿으면 두 번째 에러가 의아해진다.

### (7) ★★ 전처리 식 안의 에러 — `#if 1 / 0`

```text
===== gcc -std=c17 -E -P s41d.c -o /dev/null (cc exit=1) =====
s41d.c:1:7: error: division by zero in #if
    1 | #if 1 / 0
      |       ^
```

```text
===== clang -std=c17 -E -P s41d.c -o /dev/null (cc exit=1) =====
s41d.c:1:7: error: division by zero in preprocessor expression
    1 | #if 1 / 0
      |     ~ ^ ~
1 error generated.
```

```c
/* s41d.c */
#if 1 / 0
int unreachable;
#endif
```

- ★★ **전처리 식도 식이다** — 0 나누기는 **에러**(gcc 「division by zero in #if」, clang 「division by zero in preprocessor expression」). 컴파일 시간 상수 식의 규칙이 **전처리 단계에서 먼저** 적용된다.

### (8) ★ Go 는 전처리기가 없다

- ★ Go 에는 `#define`·`#if` 가 없다 — 조건부 빌드는 **파일 첫머리의 빌드 태그**(`//go:build linux`)로 **파일 단위**로만 고른다. Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **52번**(도구 · 빌드 태그)이 그 자리다. ★ **던지지 않았다** — 대비는 문법 수준의 사실이다.
- ★★ 대비의 요점 — C 는 **한 파일 안의 몇 줄**을 고를 수 있어서 편하고, 그래서 (3)·(6) 처럼 **고른 결과를 소스만 보고는 모른다.** `-E -P` 가 필요한 이유다.

## 문법 — 형태와 규칙

### 형태

```text
   #include "파일"        옆 파일 → -iquote → -I → 시스템 (구현 정의)
   #include <파일>        -I → 시스템
   #define 이름 치환목록   객체형 매크로
   #define 이름(인자) 치환 함수형 매크로 (42편)
   #undef 이름
   #if 상수식  /  #elif 상수식  /  #else  /  #endif
   #ifdef 이름 = #if defined(이름)      #ifndef 이름 = #if !defined(이름)
   #elifdef 이름 · #elifndef 이름       ★ C23
   #error 문구   (exit=1)     #warning 문구   ★ C23 표준 (exit=0)
   #pragma …     (구현 정의 — #pragma once 는 44편)
```

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 결과 | 층 |
|---|---|---|
| `#if X` 에 `-DX="s"` | 에러 — 문자열은 전처리 식에 못 온다 | 표준(제약) |
| `#if 1 / 0` | 에러 — 0 나누기 | 표준 |
| `#if X` 에 `X` 정의 안 됨 | **조용히 0** — `-Wundef` 로만 경고 | ★★★ 표준(규칙대로다) |
| `-std=c17` 의 `#elifdef`(건너뛴 그룹 안) | gcc **조용히 무시** · clang 경고 후 처리 | ★★ 컴파일러 구현 |
| `#include <옆 파일>` | gcc `fatal error` · clang 에러 + 복구 | 구현 정의(검색) + 컴파일러 구현(복구) |

### 규칙 불릿

- ★★★ **전처리 결과가 곧 컴파일 입력이다** — 의심스러우면 `-E -P` 로 **컴파일러가 받는 글자**를 본다.
- ★★★ **`#if X` 는 값을 본다 · `#ifdef X` 는 존재를 본다** — 정의 안 된 이름은 `#if` 에서 **0** 이다(에러가 아니다).
- ★★ **`-Wundef` 를 켜라** — 오타 난 매크로 이름이 **조용히 0** 이 되는 것을 이것만 잡는다.
- ★★ **C23 지시자를 쓰면 `-std=c2x` 로 빌드한다** — gcc `c17` 은 건너뛴 그룹 안의 `#elifdef` 를 **없는 줄**로 만든다.
- ★ **`__GNUC__` 는 clang 에서도 정의된다** — 컴파일러 판별은 `__clang__` 을 먼저.
- ★ **`<…>` 는 자기 헤더에 쓰지 않는다** — 옆 파일을 안 본다.

## 어디서 틀리나

### 1. ★★★ 「`#if X` 는 `#ifdef X` 의 짧은 꼴이다」

`-DX=0` 에서 둘이 **반대 분기**를 골랐다((3)). `#if X` 는 값, `#ifdef X` 는 존재를 본다. 스위치를 `-DFEATURE=0` 으로 끄는 빌드에 `#ifdef FEATURE` 를 쓰면 **꺼지지 않는다.**

### 2. ★★★ 「정의 안 된 매크로를 `#if` 에 쓰면 에러가 난다」

**조용히 `0` 이다** — `-Wall -Wextra -pedantic` 로 0줄. 오타(`#if FEATUER`)가 **항상 거짓인 조건**을 만들고 아무도 말하지 않는다. `-Wundef` 로만 보인다.

### 3. ★★★ 「`-std=c17` 로 빌드해도 gcc 가 모르는 지시자는 에러로 알려 준다」

**건너뛰는 그룹 안이면 안 알려 준다**((6)) — `#if 0 … #elifdef X` 는 gcc `c17` 에서 `#elifdef` 가 **사라지고** `#else` 로 간다. 살아 있는 그룹 안일 때만 에러다. **같은 지시자가 놓인 자리에 따라 에러이기도 하고 침묵이기도 하다.**

### 4. ★★ 「컴파일러가 매크로를 알고 에러를 짚어 준다」

짚어 주는 것은 **전처리기가 넘긴 확장 위치**다((2)) — 전처리 결과를 따로 컴파일하면 매크로 언급이 사라진다. ccache·distcc 처럼 **전처리와 컴파일을 나눠 돌리는 도구**에서 진단이 달라 보이는 이유가 이것일 수 있다(★ 그 도구들은 돌려 보지 않았다).

### 5. ★★ 「`__STDC_VERSION__ >= 202311L` 이면 C23 이다」

이 판의 **gcc `-std=c2x` 는 `202000L`** 이라 **거짓**이다((4)). clang 은 `202311L`. 판을 가르는 식은 **컴파일러마다 실측**해야 한다.

### 6. ★ 「`#error` 를 만나면 거기서 멈춘다」

두 컴파일러 다 **다음 줄까지 가서** 에러를 하나 더 냈다((6)). 종료 코드는 `1` 이다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 무겁다** — 치환 규칙과 `#if` 의 `0` 은 **두 컴파일러가 한 칸도 안 갈렸다.**\
★★ 갈린 자리는 전부 **「판 이전의 지시자」·「include 검색」·「미리 정의된 매크로」** 다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | ★★★ **지시자가 컴파일 전에 사라진다 · 정의 안 된 이름은 `#if` 에서 0 · `#ifdef` = `#if defined` · 건너뛴 그룹의 지시자는 이름만 본다 · 문자열은 전처리 식에 못 온다** | `-E -P` · 격자 · 에러 |
| ★★ **조건부 표준** | 판이 조건 | ★★ **`#elifdef`·`#warning`·`__STDC_VERSION__ = 202311L` 은 C23** | 격자의 c17/c2x 행 · 경고 |
| ★★ **구현 정의** | 문서화 의무가 있다 | ★★ **`"…"` 의 검색 위치와 순서 · `#pragma`** | include 격자 · `-v` |
| ★★ **컴파일러 구현** | 도구의 선택 | ★★★ **gcc `c17` 이 `#elifdef` 를 모름(침묵 · 에러) · gnu17 에서는 확장 · clang 은 c17 에서도 받음** · ★★ **gcc c2x 의 `202000L`** · `__GNUC__ = 4`(clang) · 미리 정의된 매크로 400/388 · clang 의 `<…>` 에러 복구 · 진단의 순서(gcc 정의 줄 먼저 · clang 쓰는 줄 먼저) | 격자 · `-dM -E` · 진단 |
| **미명시** | 몇 가지 중 하나 | ★ **해당 없음**(이 편이 던진 것 중에는) | — |
| **UB** | 아무 일이나 | ★ **해당 없음** — 이 편의 사고는 **「적법하게 조용한 것」**(0 으로 떨어지는 이름 · 무시되는 지시자)이다 | — |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★★ **정의 안 된 이름의 `0`** — `-Wall -Wextra -pedantic` 은 0줄 · **`-Wundef` 만** 말한다 |
| ★★ **컴파일러 구현** | ★★★ **gcc `-std=c17` 의 건너뛴 그룹 안 `#elifdef`** — `-pedantic` 까지 줘도 **0줄 · 틀린 분기**. clang 으로 한 번 더 빌드해야 보인다 |
| ★★ **(층을 가로지름)** | ★ **`#warning` 은 `exit=0`** — 경고를 에러로 안 보는 빌드에서는 **흘러간다** |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **`-E -P` 가 유일한 진실이다** — 매크로가 무엇을 만들었는지는 진단이 아니라 전처리 결과가 말한다.
  - ★★★ **`-Wundef` 와 `-std=c2x` 를 켜야 조용한 두 사고가 보인다.**
  - ★★ **판 판별 매크로는 실측해라** — `__STDC_VERSION__` 도 `__GNUC__` 도 「이름이 말하는 것」과 다르다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 기능 스위치(켜고 끄기) | ★★ **`#if FEATURE` + 항상 `-DFEATURE=0/1` 로 정의 + `-Wundef`** 또는 **`#ifdef` 만 일관되게** | 둘을 섞어 쓰기 |
| 판 가르기 | ★★ `#if __STDC_VERSION__ >= 201710L` — **c2x 값은 컴파일러마다 실측** | `>= 202311L` 로 C23 판별(gcc 13 에서 거짓) |
| 컴파일러 가르기 | ★ `#if defined(__clang__)` 먼저, 그다음 `__GNUC__` | `#ifdef __GNUC__` 만 |
| OS 가르기 | ★ `__linux__`(밑줄 있는 쪽) | `linux`(c17 에서 없다) |
| 자기 헤더 include | ★ `#include "…"` | `<…>`(옆 파일을 안 본다) |
| C23 지시자 | ★ `-std=c2x` 빌드에서만 | `-std=c17` 코드에 섞기 |
| 매크로가 무엇을 만들었나 | ★★★ `gcc -E -P` | 머릿속 치환 |

판단 규칙 두 줄.

- ★★★ **전처리기 코드를 읽을 때는 `-E -P` 결과를 옆에 둔다** — 머리로 치환하지 않는다.
- ★★ **「조용히 0」과 「조용히 무시」를 켜는 경고(`-Wundef`)와 판(`-std=c2x`)을 빌드에 넣는다.**

## 핵심 문장

- ★★★ **`gcc -E -P` 의 출력이 컴파일러가 받는 전부다 — 지시자는 사라지고 `TWICE(LIMIT)` 은 `((10) * 2)` 라는 글자가 됐다. `nm` 에 매크로 이름은 없다.**
- ★★★ **`#if X` 와 `#ifdef X` 는 `-DX=0` 과 `-DX="s"` 에서 갈렸다(#ifdef 와 갈린 칸 11 / 40) — 정의 안 된 이름은 `#if` 에서 조용히 0 이고, `-Wundef` 로만 보인다.**
- ★★★ **gcc `-std=c17` 은 건너뛴 그룹 안의 `#elifdef` 를 진단 0줄로 무시해 `-DX` 에서도 `#else` 로 갔다 — clang 은 경고 후 처리했다(gcc·clang 이 고른 분기로 갈린 칸 3 / 24 가 전부 이 행).**
- ★★ **매크로 안 오류의 `in expansion of macro` 는 전처리 결과를 따로 컴파일하면 사라진다 — 매크로를 아는 것은 컴파일러가 아니라 전처리기가 넘긴 위치 정보다.**
- ★★ **`__STDC_VERSION__` 은 c11 `201112L` · c17 `201710L` 이고, c2x 는 gcc `202000L` · clang `202311L` 로 갈렸다.**
- ★★ **`<…>` 는 옆 파일을 안 본다 — gcc 는 fatal error, clang 은 에러 후 옆 파일로 복구(둘 다 exit=1).**

## 관련 자료

- [`compiler-pipeline/`](../../../../cs/foundations/compiler-pipeline/) — ★★★ **경계.** 「4. 컴파일 전체 흐름과 링커」에 **전처리 → 컴파일 → 어셈블 → 링크** 흐름도가 있다. **그쪽은 단계의 순서까지, 여기는 전처리 단계 안에서 무엇이 일어나고 그 결과를 어떻게 읽나부터.**
- [42번 형제 — 함수형 매크로의 함정](../42-function-like-macro-pitfalls/) — ★★ 이 편의 치환이 **식을 깨는** 자리.
- [43번 형제 — `#` 와 `##`](../43-stringizing-and-token-pasting/) — ★ 치환 **순서**의 정본.
- [44번 형제 — 헤더와 분할 컴파일](../44-headers-and-separate-compilation/) — ★★ `#include` 가 **무엇을 붙여 넣나** · guard · `#pragma once`.
- [40번 형제 — `_Generic`](../40-generic-selection-c11/) — ★ `<tgmath.h>` 를 `-E` 로 연 자리.
- Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **52번** — ★ 빌드 태그(파일 단위 조건부 빌드).

## 용어 풀이

> **지시자(directive)** — `#` 로 시작하는 전처리 줄. `#include`·`#define`·`#if` 등.\
> 예: `#ifdef VERBOSE`.

> **객체형 매크로(object-like macro)** — 인자 없이 이름을 치환 목록으로 바꾸는 매크로.\
> 예: `#define LIMIT 10`.

> **줄 표지(linemarker)** — `-E` 출력의 `# 줄 "파일" 플래그` 줄. 뒤의 텍스트가 어느 파일 몇 행에서 왔는지 적는다.\
> 예: `# 1 "s41a.c"`.

> **건너뛰는 그룹(skipped group)** — 조건이 거짓인 `#if`/`#elif`/`#else` 뒤의 줄들. 지시자는 **이름만** 보고, 나머지는 무시한다.\
> 예: `#if 0` 과 `#endif` 사이.

> **`-Wundef`** — `#if` 식에서 정의 안 된 식별자가 `0` 으로 바뀔 때 경고하는 gcc/clang 옵션. `-Wall`·`-Wextra` 에 안 들어 있다.\
> 예: `warning: "X" is not defined, evaluates to 0`.

> **미리 정의된 매크로(predefined macro)** — 컴파일러가 소스 앞에 미리 넣어 둔 매크로. `-dM -E` 로 전부 볼 수 있다.\
> 예: `__STDC_VERSION__`·`__linux__`.

> **`-iquote`** — `"…"` 형태만 찾는 디렉토리를 더하는 옵션. `-I` 는 두 형태 모두에 더한다.\
> 예: `gcc -iquote qd`.

## 더 들어가면

- ★★ **`-g3` 로 매크로 정의를 디버그 정보에 남기기** — gdb 가 `macro expand` 를 하게 된다. ★ **던지지 않았다.**
- ★ **`__has_include`(C23)** — include 할 헤더가 있는지 전처리 식에서 묻기. ★ 던지지 않았다.
- ★ **ccache·distcc 가 전처리와 컴파일을 나눌 때의 진단** — (2) 의 관찰이 거기서도 그런지 **확인하지 않았다.**

## 실행 환경

**기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) 전처리 지시자 장 — 「**`#if` 의 식에서 매크로 치환 뒤 남은 식별자는 `0` 으로 바뀐다**」·「**`defined` 단항 연산자**」·「**`#ifdef`/`#ifndef` 는 `#if defined`/`#if !defined` 와 같다**」·「**건너뛰는 그룹 안의 지시자는 이름만 보고 처리하고 나머지는 무시한다**」·「**`#elifdef`·`#elifndef`·`#warning` 은 C23 에서 들어왔다**」·「**`__STDC_VERSION__` 은 C23 에서 `202311L`**」·「**`"…"` 형태는 구현 정의 방식으로 찾고, 실패하면 `<…>` 형태로 다시 찾는다**」를 **본문에서 직접 찾아 읽었다**)
★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **전처리 결과 · 고른 분기 · 진단은 전부 실행으로** 접지했다.
**실행 검증** — 이 문서의 모든 출력·진단은 「이 판」 절의 판에서 실제로 돌려 **파일로 캡처한 것**이다.\
★★★ **본체는 전처리 결과(`-E -P`)다** — 컴파일러가 **실제로 받는 글자**를 찍는다. `#if` 격자는 식 5 × 판 · 정의 4 × 컴파일러 2.\
★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
**버전** — 지시자 대부분은 C89 부터다. ★★ **`#elifdef`·`#warning` 은 C23** — 이 머신의 gcc 13 은 `-std=c2x`, clang 18 은 `-std=c2x` 로 C23 쪽을 본다.
★★★ **경계** — **「소스 → 전처리 → 컴파일 → 어셈블 → 링크」라는 단계 일반**은 [`compiler-pipeline/`](../../../../cs/foundations/compiler-pipeline/)의 「4. 컴파일 전체 흐름과 링커」가 정본이다 — ★ 그 문서에는 **전처리 단계가 흐름도 한 줄로만** 있고 따로 세운 절이 없다(`grep` 으로 확인). 이 편은 그 한 줄 **안쪽** — **C 전처리기를 어떻게 쓰고 그 결과를 어떻게 읽나** — 만 쓴다.\
★ **함수형 매크로의 함정**은 [42번 형제](../42-function-like-macro-pitfalls/), **`#`·`##`** 는 [43번 형제](../43-stringizing-and-token-pasting/), **헤더를 어떻게 나누나 · include guard · `#pragma once`** 는 [44번 형제](../44-headers-and-separate-compilation/)가 정본이다.
선행 — 없음.
