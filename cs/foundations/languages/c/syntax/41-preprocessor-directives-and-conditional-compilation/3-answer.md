# c/syntax/41 — 전처리기 지시자와 조건부 컴파일: 「**전처리기는 컴파일러보다 먼저 도는 텍스트 치환기다 — 컴파일러는 그 결과만 받는다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **gcc-12 12.4.0** · **clang 18.1.3** ·
> x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s41a.c`\~`s41e.c` · `s41c5.c` · `s41i1.c` · `s41i2.c` · `s41w.c` 이고, 블록은 **전부 캡처 파일에서 조립**했다.\
> ★★★ **본체 창은 전처리 결과** — `#if` 격자는 식 5 × 판 · 정의 4 × 컴파일러 2.
> ★★ **흔들리는 칸** — 없다. 정규화 규칙은 기본 넷뿐이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 전처리 결과 — **지시자는 전부 사라지고 `return ((10) * 2);` 만 남는다 · `nm` 에 매크로 이름은 없다** ★★★

**출력**

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

**왜 그런가**

- ★★★ **`#define`·`#ifdef` 는 전처리기에게 하는 말**이라 결과에 안 남는다. `TWICE(LIMIT)` 은 **글자 그대로** `((10) * 2)` 가 된다 — 계산하지 않는다.
- ★★ `-DVERBOSE` 는 「파일 앞에 `#define VERBOSE 1`」이라 `#ifdef VERBOSE` 그룹이 살아난다.
- ★★ `-P` 를 빼면 **줄 표지**(`# 1 "s41a.c"` 등)가 남고, 사라진 지시자 자리는 **빈 줄**로 채워 원래 줄 번호를 지킨다.
- ★★★ `nm` 에는 `limit_twice`·`verbose_mode` 뿐 — **매크로는 목적 파일에 흔적이 없다.**

### 2. 매크로 안의 오류 — **gcc 는 정의 줄 1:22 + 쓰는 줄 note, clang 은 쓰는 줄 6:12 + 정의 줄 note · `.i` 를 컴파일하면 매크로 언급이 사라진다** ★★★

**출력**

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

**왜 그런가**

- ★★★ **두 컴파일러가 짚는 두 자리는 같고 순서가 반대다** — gcc 는 정의 줄이 본문(`1:22`)이고 `in expansion of macro ‘FIELD’` 가 `6:12`, clang 은 쓰는 줄이 본문(`6:12`)이고 `expanded from macro 'FIELD'` 가 `1:24`.
- ★★★ **`.i` 를 따로 컴파일하면 매크로 note 가 없다** — `s41b.i:3:16`. 컴파일러가 받은 글자에는 `FIELD` 라는 이름이 **없기** 때문이다.
- ★★ **줄 표지가 있는 `.i` 는 `s41b.c:6:16` 을 댄다** — 줄 표지는 **파일·줄만** 나른다. 열 16 은 확장된 줄 기준인데 보여 주는 줄은 원본 `return FIELD(n);` 이라 **캐럿이 어긋난다.**
- ★★ **결론** — 「매크로 안에서 났다」는 정보는 **전처리기가 한 프로세스 안에서 컴파일러에 넘긴 확장 위치**다.

### 3. `#if` 격자 — **`#ifdef` 와 갈린 칸 11 / 40 · gcc·clang 이 분기로 갈린 칸 3 / 24(전부 `#elifdef` c17 행)** ★★★

**출력**

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

**왜 그런가**

- ★★★ **`#ifdef X` = `#if defined(X)`** — 「정의돼 있나」만 본다. `-DX=0`·`-DX="s"` 도 1.
- ★★★ **`#if X` 는 값을 본다** — 없음 → 치환 뒤 남은 식별자 `X` 가 **0** → 2 · `-DX` 는 `1` → 1 · `-DX=0` → 2 · `-DX="s"` → **에러**(문자열은 전처리 식에 못 온다).
- ★★ **`#if X == 1` 은 이 네 정의에서 `#if X` 와 같은 칸**을 냈다(값이 1·0·없음·문자열뿐이라서).
- ★★★ **`#elifdef` 의 c17 행** — **gcc 는 네 칸 다 2 · 진단 0줄**(모르는 지시자를 건너뛰는 그룹에서 무시 — 8번), **clang 은 1 + `-Wc23-extensions` 경고**. c2x 행은 두 컴파일러가 표준대로 같다.
- ★★ 경고가 붙은 칸은 **clang 의 `#elifdef` c17 행 넷**뿐이다. `#if X` 에서 `X` 가 없어도 **경고 0**.

### 4. 미리 정의된 매크로 — **c11 `201112L` · c17 `201710L` · c2x 는 gcc `202000L` 대 clang `202311L` · clang 의 `__GNUC__` 는 `4` · `linux`/`unix` 는 gnu17 에만** ★★

**출력**

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

**왜 그런가**

- ★★★ **`__STDC_VERSION__`** 은 판마다 표준이 정한 값이다(C23 은 N3220 에서 `202311L`). **gcc 13 · gcc-12 의 c2x 는 `202000L`** — 이 판의 gcc 에서는 **`>= 202311L` 이 거짓**이다.
- ★★ **clang 은 `__GNUC__` 를 `4` 로 정의**한다 — GNU 확장 호환을 위해 gcc 4 인 척한다. 컴파일러 판별은 `__clang__` 을 먼저.
- ★★ **`-std=c17` 은 `__STRICT_ANSI__` 를 켜고 `linux`·`unix` 를 뺀다** — 사용자 이름 공간을 침범하는 이름이라서다. `__linux__` 는 양쪽 다 있다.
- ★ 전체는 gcc 400 개 · clang 388 개 — 대부분 **구현의 선택**이다.

### 5. include 검색 — **`"…"` 는 옆 → `-iquote` → `-I` → 시스템 · `<…>` 는 `-I` → 시스템 · 못 찾을 때 gcc 는 fatal, clang 은 에러 후 복구** ★★

**출력**

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

**왜 그런가**

- ★★★ **`"…"` 는 소스 옆을 먼저** 본다 — 옆에 있으면 플래그와 무관하게 옆 파일. 없으면 `-iquote qd` → `-I id` 순.
- ★★★ **`<…>` 는 옆도 `-iquote` 도 안 본다** — `-v` 의 `#include <...> search starts here:` 목록이 `id` 와 시스템뿐이다.
- ★★ **gcc 와 clang 이 갈린 행 3 / 8 은 전부 `<…>` 를 못 찾은 칸** — gcc 는 `fatal error` 로 끝, clang 은 `use "quotes" instead` 에러를 내고 **`"…"` 로 찾은 파일을 넣어 계속 간다**(에러 복구). **둘 다 `exit=1`**.
- ★ 검색 위치와 순서는 **구현 정의**다 — 표준은 「`"…"` 가 실패하면 `<…>` 로 다시」까지만 정한다.

### 6. `#warning` 과 `#error` — **`#warning` 은 C23 표준 · c17 에서는 확장 경고 한 줄이 더 · `exit=0` · `#error` 는 `exit=1` 이지만 다음 줄 에러까지 두 개** ★★

**출력**

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

**왜 그런가**

- ★★ **c17 `-pedantic`** — gcc 「`#warning` before C2X is a GCC extension」 + 경고 문구 · clang 「`#warning` is a C23 extension」 + 경고 문구 = **각각 두 줄.** c2x 면 **경고 문구 한 줄**.
- ★★ **`#warning` 은 빌드를 안 멈춘다**(`exit=0`).
- ★★ **`#error` 는 `exit=1`** — 그런데 전처리가 거기서 끝나지 않아 **`int limit = LIMIT;` 의 에러까지 둘**이다.

### 7. 정의 안 된 이름은 `0` 이다 (왜) ★★★

- ★★★ N3220 — 「**매크로 치환 뒤 남은 식별자는 pp-number `0` 으로 바뀐다**」. 에러를 낼 근거가 없다.
- ★★ **`-Wundef`** 가 그것을 경고한다. **`-Wall`·`-Wextra` 에 안 들어 있다**(18-A — 아래 첫 블록이 0줄).

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

- ★ `-DX=abc` 면 `#if abc == 1` → `abc` 는 정의 안 됐으니 `0 == 1` → 거짓(2). `-Wundef` 는 `"abc" is not defined` 라고 짚는다.

### 8. gcc `-std=c17` 의 `#elifdef` — **건너뛰는 그룹 안에서는 없는 줄 · 살아 있는 그룹 안에서는 에러** (경계) ★★★

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -DX -E -P s41c5.c (cc exit=0) =====
branch_2
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

- ★★★ **gcc `-std=c17` 은 `#elifdef` 를 지시자로 모른다.** 표준은 「**건너뛰는 그룹 안의 지시자는 이름만 보고 나머지는 무시**」한다 — 모르는 이름은 조건 구조에 영향이 없으니 **없는 줄**이 되고, `#if 0` 의 그룹이 `#else` 까지 이어진다 → `branch_2`.
- ★★ **`#if 1` 뒤면 그 줄은 살아 있는 그룹 안**이다 — 모르는 지시자가 **처리 대상**이 되어 `invalid preprocessing directive #elifdef` 에러.
- ★★ **`-std=gnu17` 은 확장으로 받는다**(`-pedantic` 경고 + `branch_1`). clang 18 은 c17 에서도 받고 경고한다.

### 9. 전처리 식도 식이다 (왜) ★

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

- ★ 0 나누기는 정수 상수 식의 규칙대로 에러다. 문자열 리터럴은 전처리 식의 토큰이 될 수 없다.
- ★ **`-D` 는 명령줄에서 만든 `#define`** 이라, gcc 는 문제의 토큰이 온 곳을 `<command-line>` 으로 댄다. clang 은 `<command line>:2:11` 에 가짜 `#define X "s"` 줄을 보여 준다.

### 10. Go 에는 전처리기가 없다 (연결) ★

- ★ Go 는 **파일 단위** — 첫머리의 빌드 태그(`//go:build …`)로 파일을 넣고 뺀다. Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **52번**. ★ 이 편은 Go 를 돌리지 않았다.
- ★ C 는 **한 파일 안 몇 줄**을 고를 수 있어 편하지만, **소스만 보고 무엇이 컴파일되는지 모른다** — 3번 격자와 8번의 침묵이 그 대가다.

### 11. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- ★★★ **표준** — 지시자가 컴파일 전에 사라짐 · 정의 안 된 이름은 0 · `#ifdef` = `#if defined` · 건너뛴 그룹의 처리 · 문자열 금지. **조건부 표준** — `#elifdef`·`#warning`·`202311L` 은 C23. **구현 정의** — include 검색. **컴파일러 구현** — gcc c17 의 `#elifdef` 침묵 · gcc c2x 의 `202000L` · clang 의 `__GNUC__ = 4` · clang 의 include 에러 복구 · 진단의 순서. **UB · 미명시** — 이 편이 던진 것에는 없다.
- ★★★ **0줄 사고 둘** — ① 정의 안 된 이름의 `0`(`-Wundef` 로만) ② gcc c17 의 건너뛴 `#elifdef`(clang 으로만).
- ★★ gcc 13 `-std=c2x` 는 `202000L` 이라 **C23 코드가 C23 이 아닌 것으로** 판별된다.

### 12. 경계 (연결) ★

- ★ [`compiler-pipeline/`](../../../../compiler-pipeline/) 의 「4. 컴파일 전체 흐름과 링커」 — 흐름도에 **전처리기가 한 줄**로 있고, **전처리만 다룬 절은 없다.** 이 편은 그 한 줄의 안쪽이다.
- ★ 함수형 매크로의 함정 = [42번 형제](../42-function-like-macro-pitfalls/) · `#`/`##` = [43번 형제](../43-stringizing-and-token-pasting/) · include guard·`#pragma once` = [44번 형제](../44-headers-and-separate-compilation/).

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s41a.c` | ★★★ `-E -P` · `-E` 줄 표지 · `nm` | 전처리 3 · 목적 파일 1 |
| `s41b.c` | ★★★ 매크로 안 오류 · `.i` 두 벌 재컴파일 | 진단 4 |
| `s41c.c` · `s41c5.c` | ★★★ **`#if` 격자 48칸** · `-Wundef` · 문자열 에러 · `#elifdef` | 전처리 48 + 진단 8 |
| `s41e.c` | ★★ 살아 있는 그룹 안의 `#elifdef` | 진단 2 |
| `s41d.c` | ★ `#if 1 / 0` | 진단 2 |
| (없음 — `/dev/null`) | ★★ 미리 정의된 매크로 격자 | 9 판 |
| `s41i1.c` · `s41i2.c` | ★★ include 격자 32칸 · `-v` | 전처리 32 + 진단 4 |
| `s41w.c` | ★★ `#warning` · `#error` | 진단 6 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. **이 편의 블록은 정규화 없이 전부 동일**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **3·8번의 gcc c17 `#elifdef`** — gcc 13.3 · 12.4 의 동작. 다른 판은 확인하지 않았다.
- ★★ **4번의 c2x 값 `202000L`** — gcc 13·12 의 값이다. gcc 가 C23 을 확정 반영한 판에서는 달라질 수 있다.
- ★★ **5번의 검색 순서와 clang 의 복구** · **2번의 진단 순서.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `-std=c23`(gcc 13 에 없다 · clang 은 받는다) · `__has_include` · `#elifndef` · `-DX=2`.
- ★ **읽지 않은 것** — gcc 문서의 `202000L` 설명 · C17 초안(N2310) 원문.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **3번의 `#elifdef` 행과 4번의 `__STDC_VERSION__` c2x 칸.**
- ★ **5번의 「못 찾음」 칸** — 에러 복구는 판마다 바뀔 수 있다.
