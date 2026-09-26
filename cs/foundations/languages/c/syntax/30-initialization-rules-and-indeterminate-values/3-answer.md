# c/syntax/30 — 초기화 규칙과 불확정 값: 「**0 은 누가 보장하고, 안 보장된 자리에서는 무엇이 읽히나**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s30a.c`\~`s30go.go` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
> ★★ **최적화 수준이 결과를 바꾸는 문항(4·5·6·9)은 판 격자**로 돌렸다.\
> ★ **스택을 먼저 더럽히는 실험(2·5)은 「무엇이 남아 있나」를 내가 정했다** — 그래서 재실행에 같다.
> ★★★ **본체 창** — `readelf -S`·`size`(1번) · `-O0` 대 `-O2` 경고·어셈블리(4·8번).
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★ MSan 리포트의 **PID**(`==N==`)·**프레임 주소**(`#0 0x…`) — 기본 규칙 둘로 정규화 | ★★★ **섹션 크기 · `size` 표 · 오브젝트 바이트 수** |
> | — | ★★★ **탐침 격자의 칸 · 답한 칸 30 / 48** |
> | — | ★★ 패딩 덤프 · `malloc` 격자 · `bool` 격자 · `call` 목록 |
> | — | ★★ MSan·UBSan 의 **`파일:줄:칸`** · 컴파일러 진단 전문 · 종료 코드 |
>
> ★ **이 편은 불확정 값을 숫자로 찍지 않는다** — 찍으면 흔들리고, 흔들려도 **아무것도 증명하지 않는다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 정적 배열 두 개 — **0 인 쪽은 `.bss NOBITS` 라 파일이 안 커진다** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s30a.c -o s30a.o && gcc -std=c17 -Wall -Wextra -pedantic -c s30b.c -o s30b.o && readelf -S -W s30a.o s30b.o | grep -E '^File|\.(data|bss|rodata) ' (cc exit=0) =====
File: s30a.o
  [ 3] .data             PROGBITS        0000000000000000 000084 000004 00  WA  0   0  4
  [ 4] .bss              NOBITS          0000000000000000 0000a0 061aa0 00  WA  0   0 32
  [ 5] .rodata           PROGBITS        0000000000000000 0000a0 000004 00   A  0   0  4
File: s30b.o
  [ 3] .data             PROGBITS        0000000000000000 0000a0 061aa0 00  WA  0   0 32
  [ 4] .bss              NOBITS          0000000000000000 061b40 000008 00  WA  0   0  4
  [ 5] .rodata           PROGBITS        0000000000000000 061b40 000004 00   A  0   0  4
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s30a.c -o s30a.o && gcc -std=c17 -Wall -Wextra -pedantic -c s30b.c -o s30b.o && size s30a.o s30b.o && stat -c '%s 바이트  %n' s30a.o s30b.o (cc exit=0) =====
   text	   data	    bss	    dec	    hex	filename
    160	      4	 400032	 400196	  61b44	s30a.o
    160	 400032	      8	 400200	  61b48	s30b.o
1768 바이트  s30a.o
401792 바이트  s30b.o
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s30a.c -o s30a.o && nm -S s30a.o (cc exit=0) =====
0000000000000020 0000000000061a80 b big_zero
0000000000000000 0000000000000004 d nonzero
0000000000000000 0000000000000004 r ro
0000000000000000 0000000000000044 T use
0000000000000004 0000000000000004 b zero_explicit
0000000000000000 0000000000000004 b zero_implicit
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s30a.c -o s30a.o && nm -S s30a.o (cc exit=0) =====
0000000000000010 0000000000061a80 b big_zero
0000000000000000 0000000000000004 d nonzero
0000000000000000 000000000000002c T use
0000000000000004 0000000000000004 b zero_explicit
0000000000000000 0000000000000004 b zero_implicit
```

**왜 그런가**

- ★★★ `s30a.o` — **`.bss 0x061aa0`(400032) · `.data 0x4`**. `s30b.o` — **`.bss 0x8` · `.data 0x061aa0`**. 배열 하나가 **`.bss` 에서 `.data` 로 옮겨 갔다.**
- ★★★ **`.bss` 는 `NOBITS`** — 「**파일에 비트가 없다**」. 크기만 적고 내용은 싣지 않는다. `.data` 는 **`PROGBITS`** — 내용이 파일에 있다.
- ★★ **1768 대 401792 바이트** — 원소 하나를 `1` 로 바꾸자 **나머지 99999 개의 0 까지** 파일에 실렸다.
- ★★ **`zero_explicit = 0` 은 `b`**(`.bss`) — 0 을 적어도 안 적은 것과 **같은 자리**다.
- ★ **`ro` 는 gcc 에서 `r ro`, clang 에서 없다** — clang 이 **`-O0` 에서도 즉치값으로 접어** 심볼째 없앴다. **두 컴파일러가 갈린 자리**다.
- ★ **`.bss` 는 표준의 말이 아니다** — 표준은 「0 으로 시작한다」만 보장하고, `.bss` 는 **이 구현이 그 약속을 지키는 방법**이다.

### 2. 부분 초기화 — **나머지는 전부 0 · 네 벌 동일 · 보장** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s30c.c -o x ; ./x (cc exit=0 · run exit=0) =====
a = 1 0 0 0 0 0 0 0
b = 0 0 0 0 0 9 0 0
c = { port=0  retries=3  name=NULL  ratio=0.0 }
```

```text
===== 부분 초기화 — 컴파일러 2 × 최적화 2 (exit=0) =====
gcc    -O0  출력 md5 앞 8자리 = c0b5b02c
gcc    -O2  출력 md5 앞 8자리 = c0b5b02c
clang  -O0  출력 md5 앞 8자리 = c0b5b02c
clang  -O2  출력 md5 앞 8자리 = c0b5b02c
네 벌의 출력이 한 글자도 같은가 = 예
```

**왜 그런가**

- ★★★ `a = 1 0 0 0 0 0 0 0` · `b = 0 0 0 0 0 9 0 0` · `c = { port=0 retries=3 name=NULL ratio=0.0 }`.
- ★★★ **보장이다.** 초기자가 **하나라도** 있으면 적지 않은 칸은 **정적 저장 기간처럼** 초기화된다 — 저장 기간이 자동이어도. 스택을 `-1` 로 더럽혔는데도 0 인 것은 **컴파일러가 0 을 써 넣었기** 때문이다.
- ★★ **네 벌 md5 동일** — 「예」.
- ★ **`name` 은 `NULL`, `ratio` 는 `0.0`** — 「0 비트」가 아니라 **그 타입의 0** 이다(널 포인터 · 양의 0).

### 3. `= {}` — **`-std=c17` 만이면 경고 0 · `cc exit=0`** ★★

**출력**

```text
===== 빈 중괄호 = {} — 컴파일러 2 × 판 4 (exit=0) =====
gcc    -std=c17                    cc exit=0 · 경고 0 · 에러 0
gcc    -std=c17 -pedantic          cc exit=0 · 경고 2 · 에러 0
gcc    -std=c17 -pedantic-errors   cc exit=1 · 경고 0 · 에러 2
gcc    -std=c2x -pedantic-errors   cc exit=0 · 경고 0 · 에러 0
clang  -std=c17                    cc exit=0 · 경고 0 · 에러 0
clang  -std=c17 -pedantic          cc exit=0 · 경고 2 · 에러 0
clang  -std=c17 -pedantic-errors   cc exit=1 · 경고 0 · 에러 2
clang  -std=c2x -pedantic-errors   cc exit=0 · 경고 0 · 에러 0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s30d.c -o x (cc exit=0) =====
s30d.c: In function ‘main’:
s30d.c:4:16: warning: ISO C forbids empty initializer braces before C2X [-Wpedantic]
    4 |     int a[4] = {};                       /* ★ 빈 중괄호 — C23 에서 들어온 문법 */
      |                ^
s30d.c:5:37: warning: ISO C forbids empty initializer braces before C2X [-Wpedantic]
    5 |     struct { int x; double y; } s = {};
      |                                     ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s30d.c -o x (cc exit=0) =====
s30d.c:4:16: warning: use of an empty initializer is a C23 extension [-Wc23-extensions]
    4 |     int a[4] = {};                       /* ★ 빈 중괄호 — C23 에서 들어온 문법 */
      |                ^
s30d.c:5:37: warning: use of an empty initializer is a C23 extension [-Wc23-extensions]
    5 |     struct { int x; double y; } s = {};
      |                                     ^
2 warnings generated.
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic s30d.c -o x ; ./x (cc exit=0 · run exit=0) =====
a = 0 0 0 0 · s = { 0, 0.0 }
```

**왜 그런가**

- ★★★ **여덟 칸** — `-std=c17` 만: **경고 0 · `exit=0`**(두 컴파일러) · `-pedantic`: **경고 2 · `exit=0`** · `-pedantic-errors`: **에러 2 · `exit=1`** · `-std=c2x -pedantic-errors`: **0 · `exit=0`**.
- ★★ **문구와 플래그가 갈린다** — gcc `ISO C forbids empty initializer braces before C2X [-Wpedantic]` · clang `use of an empty initializer is a C23 extension [-Wc23-extensions]`.
- ★★★ **「종료 코드 0인데 ill-formed」는 `-std=c17` 만 준 두 칸**(그리고 `-pedantic` 두 칸) — C17 문법에 없는 것을 **`exit=0`** 으로 받았다.
- ★ `-std=c2x` 의 출력은 `a = 0 0 0 0 · s = { 0, 0.0 }`.

### 4. 탐침 8 × 도구 6 — **답한 칸 30 / 48 · MSan 만 8/8 · P4 는 정적 도구 전부 침묵** ★★★

**출력**

```text
===== 불확정 값 탐침 8 × 도구 6 (경고는 uninitialized 가 들어간 것만 센다) (exit=0) =====
탐침 | gcc -O0   | gcc -O2   | clang -O0 | clang -O2 | gcc 분석기 | clang MSan
P1   | 경고 1    | 경고 1    | 경고 1    | 경고 1    | 경고 1     | 보고
P2   | 침묵      | 침묵      | 경고 1    | 경고 1    | 경고 1     | 보고
P3   | 침묵      | 경고 1    | 경고 1    | 경고 1    | 경고 2     | 보고
P4   | 침묵      | 침묵      | 침묵      | 침묵      | 침묵       | 보고
P5   | 경고 1    | 경고 1    | 침묵      | 침묵      | 경고 1     | 보고
P6   | 경고 1    | 경고 2    | 침묵      | 침묵      | 경고 1     | 보고
P7   | 경고 1    | 경고 1    | 침묵      | 침묵      | 경고 1     | 보고
P8   | 침묵      | 침묵      | 침묵      | 침묵      | 경고 1     | 보고
답한 칸 30 / 48
```

```text
===== which valgrind (exit=1) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -c s30p3.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -c s30p3.c -o /dev/null (cc exit=0) =====
In function ‘probe’,
    inlined from ‘main’ at s30p3.c:12:13:
s30p3.c:6:37: warning: ‘sum’ may be used uninitialized [-Wmaybe-uninitialized]
    6 |     for (int i = 0; i < c; i++) sum += i;
      |                                 ~~~~^~~~
s30p3.c: In function ‘main’:
s30p3.c:5:9: note: ‘sum’ was declared here
    5 |     int sum;                             /* P3 — 누산기를 0 으로 안 둔다 */
      |         ^~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=memory -ffile-prefix-map="$PWD"=. s30p4.c -o m && ./m 2>&1 >/dev/null | sed -n '1,3p;/^SUMMARY/p' (exit=1) =====
==4091404==WARNING: MemorySanitizer: use-of-uninitialized-value
    #0 0x5f13a31ca58f in probe s30p4.c:9:5
    #1 0x5f13a31ca426 in main s30p4.c:14:13
SUMMARY: MemorySanitizer: use-of-uninitialized-value s30p4.c:9:5 in probe
```

**왜 그런가**

- ★★★ **답한 칸 30 / 48.** 열별로 — gcc `-O0` 4 · gcc `-O2` 5 · clang `-O0` 3 · clang `-O2` 3 · `-fanalyzer` 7 · MSan 8.
- ★★★ **P3 이 `-O0` 침묵 · `-O2` 경고**다. 경고 머리가 `inlined from 'main'` — gcc 의 `-Wmaybe-uninitialized` 는 **최적화가 만든 정보**를 쓰므로 `-O0` 에서는 볼 것이 없다.\
  ★★★ **반대로 P2 는 gcc `-O2` 에서도 침묵** — 코드가 **접혀 사라져서**다(8번).
- ★★ **clang 두 열은 한 글자도 같다** — clang 의 이 경고들은 **프런트엔드**(최적화 전)에서 나오므로 판을 안 탄다. 대신 **P5\~P7(배열·멤버·`malloc`)을 전부 놓친다.**
- ★★ **P4 는 정적 도구 다섯이 전부 침묵** — 주소를 넘긴 순간 컴파일러는 「**초기화됐을 수도 있다**」고 본다. **MSan 만** `s30p4.c:9:5`(`return a;`)에서 잡는다.
- ★ **Valgrind 는 이 머신에 없다** — `which` 가 **`exit=1`**. 「**못 잰 것**」이다 — 없다고 적기 전에 블록으로 확인했다.

### 5. 패딩 — **정적만 보장 · 초기자 셋은 이 판에서 `00` · clang 멤버 대입은 `aa`** ★★

**출력**

```text
===== 패딩 바이트 — 초기화 형태 5 × 컴파일러 2 × 최적화 2 (exit=0) =====
--- gcc -O0
static (no init)      00  [00] [00] [00]  00   00   00   00 
auto = {0}            00  [00] [00] [00]  00   00   00   00 
auto = {.i = 2}       00  [00] [00] [00]  02   00   00   00 
auto = {1, 2}         01  [00] [00] [00]  02   00   00   00 
auto member-assign    01  [00] [00] [00]  02   00   00   00 
--- gcc -O2
static (no init)      00  [00] [00] [00]  00   00   00   00 
auto = {0}            00  [00] [00] [00]  00   00   00   00 
auto = {.i = 2}       00  [00] [00] [00]  02   00   00   00 
auto = {1, 2}         01  [00] [00] [00]  02   00   00   00 
auto member-assign    01  [00] [00] [00]  02   00   00   00 
--- clang -O0
static (no init)      00  [00] [00] [00]  00   00   00   00 
auto = {0}            00  [00] [00] [00]  00   00   00   00 
auto = {.i = 2}       00  [00] [00] [00]  02   00   00   00 
auto = {1, 2}         01  [00] [00] [00]  02   00   00   00 
auto member-assign    01  [aa] [aa] [aa]  02   00   00   00 
--- clang -O2
static (no init)      00  [00] [00] [00]  00   00   00   00 
auto = {0}            00  [00] [00] [00]  00   00   00   00 
auto = {.i = 2}       00  [00] [00] [00]  02   00   00   00 
auto = {1, 2}         01  [00] [00] [00]  02   00   00   00 
auto member-assign    01  [aa] [aa] [aa]  02   00   00   00 
```

**왜 그런가**

- ★★★ **정적(`static (no init)`)은 네 벌 다 `00`** 이고, **이것만 표준이 보장**한다 — 초기자 없는 정적 객체는 **패딩 비트까지 0** 이다.
- ★★ **`auto = {0}`·`{.i = 2}`·`{1, 2}` 는 네 벌 다 `00`** — 그런데 **관찰**이다. 자동 객체의 패딩을 0 으로 만든다는 약속은 없다. 두 컴파일러가 **통째로 0 을 채운 뒤** 멤버를 쓴 것뿐이다.
- ★★★ **clang 의 멤버 대입에서 `aa`** — 먼저 더럽힌 `0xAA` 가 **패딩 자리에 그대로** 남았다. 멤버에 값을 저장한 뒤의 패딩은 **미명시**다.\
  ★ gcc 의 `00` 은 **그 자리가 원래 0 이었을 뿐**일 수 있다 — 이 격자는 그것을 가르지 않는다.
- ★ [22번 형제](../22-struct-padding-and-alignment/)에서는 **초기자로 만든 구조체**에 `0xAA` 가 남았다(gcc `-O0`). **같은 질문에 두 편이 다른 관찰**을 냈다 — 그것이 곧 「보장이 아니다」의 증거다.

### 6. `bool` 에 `2` — **gcc `-O0` 은 참이면서 참, clang 은 거짓** ★★★

**출력**

```text
===== bool 에 0 도 1 도 아닌 바이트 — 컴파일러 2 × 최적화 2 (exit=0) =====
--- gcc -O0
b  ? 참 : 거짓 = 참
!b ? 참 : 거짓 = 참
b == true      = 2
(int)b         = 2
--- gcc -O2
b  ? 참 : 거짓 = 참
!b ? 참 : 거짓 = 거짓
b == true      = 2
(int)b         = 2
--- clang -O0
b  ? 참 : 거짓 = 거짓
!b ? 참 : 거짓 = 참
b == true      = 0
(int)b         = 0
--- clang -O2
b  ? 참 : 거짓 = 거짓
!b ? 참 : 거짓 = 참
b == true      = 0
(int)b         = 0
```

★ 아래 UBSan 이 가리키는 줄·칸을 다시 던질 수 있게 소스를 먼저 싣는다.

```c
/* s30g.c */
#include <stdio.h>
#include <string.h>
#include <stdbool.h>

int main(void) {
    bool b;
    unsigned char two = 2;
    memcpy(&b, &two, 1);                 /* ★ 0 도 1 도 아닌 바이트를 bool 에 넣는다 */
    printf("b 의 바이트    = %d\n", *(unsigned char *)&b);
    printf("b  ? 참 : 거짓 = %s\n", b ? "참" : "거짓");
    printf("!b ? 참 : 거짓 = %s\n", !b ? "참" : "거짓");
    printf("b == true      = %d\n", b == true);
    printf("(int)b         = %d\n", (int)b);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=undefined -ffile-prefix-map="$PWD"=. s30g.c -o x && ./x 2>&1 >/dev/null (exit=0) =====
s30g.c:10:42: runtime error: load of value 2, which is not a valid value for type '_Bool'
s30g.c:11:40: runtime error: load of value 2, which is not a valid value for type '_Bool'
s30g.c:12:5: runtime error: load of value 2, which is not a valid value for type '_Bool'
s30g.c:13:5: runtime error: load of value 2, which is not a valid value for type '_Bool'
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=undefined -ffile-prefix-map="$PWD"=. s30g.c -o x && ./x 2>&1 >/dev/null (exit=0) =====
s30g.c:10:40: runtime error: load of value 2, which is not a valid value for type '_Bool'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior s30g.c:10:40 
s30g.c:11:41: runtime error: load of value 2, which is not a valid value for type '_Bool'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior s30g.c:11:41 
s30g.c:12:37: runtime error: load of value 2, which is not a valid value for type '_Bool'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior s30g.c:12:37 
s30g.c:13:42: runtime error: load of value 2, which is not a valid value for type '_Bool'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior s30g.c:13:42 
```

**왜 그런가**

- ★★★ **네 벌** — gcc `-O0`: `b` 참 · `!b` **참** · `b == true` **2** · `(int)b` **2** / gcc `-O2`: 참 · 거짓 · 2 · 2 / clang 두 벌: 거짓 · 참 · 0 · 0.
- ★★★ **「참이면서 참」은 gcc `-O0`** 이다 — `b` 도 참이고 `!b` 도 참. 그리고 `b == true` 가 **0 도 1 도 아닌 `2`** 다.
- ★★ **UBSan 은 두 컴파일러에서 네 번씩** `load of value 2, which is not a valid value for type '_Bool'` 이라고 말한다. **`run exit=0`** — 기본은 알리고 계속 간다. ★ 칸 번호가 다르고(gcc `10:42` · clang `10:40`) clang 만 `SUMMARY` 줄을 매번 찍는다.
- ★★ **UB 는 `bool` 로 읽는 순간**이다. `memcpy` 는 문자 단위로 바이트를 쓴 것이라 그 자체는 UB 가 아니다.
- ★ **어느 패턴이 비값인지는 구현이 정한다** — 이 구현에서 `_Bool` 의 값은 `0`·`1` 뿐이다.

### 7. 「읽으면 UB」의 경계 — **주소를 안 잡은 자동 객체만 무조건 · 나머지는 타입이 정한다** ★★★

**왜 그런가**

- ★★★ **무조건 UB** — **자동 저장 기간**이고 **주소를 한 번도 안 잡은**(`register` 로 선언될 수 있었던) 객체를 **초기화·대입 전에** 읽을 때. 탐침 중 **P1·P2·P3·P8** 이 가장 분명하게 여기 든다(P5·P6 은 경계가 섬세해 단정하지 않는다).
- ★★★ **그 밖**(주소를 잡았다 · `malloc`)에서는 **불확정 표현**을 읽는 것이고, **그 바이트가 그 타입의 비값 표현이냐**가 층을 정한다 — 비값이면 UB, 아니면 **미명시 값**.
- ★★ **미명시 값** — 올바른 값 중 하나인데 어느 것인지 정해지지 않은 것. **비값 표현** — 어떤 값도 아닌 패턴. **C17 까지는 「트랩 표현」이라** 불렀다.
- ★★ **`unsigned char` 로 읽는 것은 UB 가 아니다** — 문자 타입으로 읽을 때는 비값 규칙이 적용되지 않는다.
- ★ **「UB 가 아니면 괜찮다」가 틀린 이유** — 미명시 값은 **아무 값**이다. 그 값으로 무엇을 하든 **프로그램의 뜻이 정해지지 않는다.** 처방은 층과 무관하게 같다 — **읽기 전에 쓴다.**

### 8. P2 의 gcc `-O2` 침묵 — **불확정 `a` 를 `1` 로 접어 분기째 지웠다** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -c s30p2.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s30p2.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' (cc exit=0) =====
.LC0:
main:
	endbr64
	sub	rsp, 8
	lea	rdi, .LC0[rip]
	call	puts@PLT
	xor	eax, eax
	add	rsp, 8
	ret
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 -c s30p2.c -o /dev/null (cc exit=0) =====
s30p2.c:6:9: warning: variable 'a' is used uninitialized whenever 'if' condition is false [-Wsometimes-uninitialized]
    6 |     if (c > 5) a = 1;                    /* P2 — 한쪽 가지에서만 쓴다 */
      |         ^~~~~
s30p2.c:7:12: note: uninitialized use occurs here
    7 |     return a;
      |            ^
s30p2.c:6:5: note: remove the 'if' if its condition is always true
    6 |     if (c > 5) a = 1;                    /* P2 — 한쪽 가지에서만 쓴다 */
      |     ^~~~~~~~~~
s30p2.c:5:10: note: initialize the variable 'a' to silence this warning
    5 |     int a;
      |          ^
      |           = 0
1 warning generated.
```

**왜 그런가**

- ★★★ **`main` 에는 `puts` 한 번만 있다** — `probe` 호출도, `12345` 비교도 없다.
- ★★★ `a` 는 「`1` 이거나 불확정」이다. 불확정은 **아무 값이어도 되므로** gcc 는 **`a = 1`** 로 접었다. `1 == 12345` 는 거짓이라 **분기가 사라지고** `puts` 한 번만 남는다.
- ★★ **경고를 낼 코드가 최적화로 사라졌다** — 그래서 `-O2` 에서도 **진단 0줄 · `cc exit=0`** 이다.
- ★★ **clang 은 프런트엔드에서 잡는다** — `whenever 'if' condition is false [-Wsometimes-uninitialized]`. 최적화 전이라 **코드가 아직 있다.**
- ★ **「gcc 는 `a` 를 1 로 만든다」는 틀린 문장**이다 — 이것은 **UB 의 이 판 결과**다. 다른 판·다른 주변 코드에서는 다르게 접을 수 있다.

### 9. `malloc` 대 `calloc` — **`-O0` 은 흔적 48/48 · `-O2` 는 실험이 지워졌다** ★★

**출력**

```text
===== malloc 대 calloc — 컴파일러 2 × 최적화 2 (exit=0) =====
--- gcc -O0
malloc : 방금 돌려준 조각이 다시 왔나 = 예
malloc : 바이트 16~63 중 0xAB 그대로 = 48 / 48
calloc : 바이트  0~63 중 0x00       = 64 / 64
--- gcc -O2
malloc : 방금 돌려준 조각이 다시 왔나 = 예
malloc : 바이트 16~63 중 0xAB 그대로 = 0 / 48
calloc : 바이트  0~63 중 0x00       = 64 / 64
--- clang -O0
malloc : 방금 돌려준 조각이 다시 왔나 = 예
malloc : 바이트 16~63 중 0xAB 그대로 = 48 / 48
calloc : 바이트  0~63 중 0x00       = 64 / 64
--- clang -O2
malloc : 방금 돌려준 조각이 다시 왔나 = 아니오
malloc : 바이트 16~63 중 0xAB 그대로 = 0 / 48
calloc : 바이트  0~63 중 0x00       = 64 / 64
```

```text
===== main 이 부르는 함수를 차례대로 — 어셈블리의 call 만 (컴파일러 2 × 최적화 2) (exit=0) =====
gcc    -O0  | malloc@PLT memset@PLT free@PLT malloc@PLT printf@PLT count_eq printf@PLT free@PLT calloc@PLT count_eq printf@PLT free@PLT 
gcc    -O2  | malloc@PLT free@PLT malloc@PLT __printf_chk@PLT __printf_chk@PLT free@PLT calloc@PLT __printf_chk@PLT free@PLT 
clang  -O0  | malloc@PLT memset@PLT free@PLT malloc@PLT printf@PLT count_eq printf@PLT free@PLT calloc@PLT count_eq printf@PLT free@PLT 
clang  -O2  | malloc@PLT printf@PLT printf@PLT free@PLT calloc@PLT printf@PLT free@PLT 
```

**왜 그런가**

- ★★ **`-O0` 의 두 컴파일러** — 방금 돌려준 조각이 다시 오고, **`0xAB` 가 48/48 그대로**다. 새로 빌린 메모리에 **남의 흔적**이 있다 — **불확정**.
- ★★★ **gcc `-O2` 의 `call` 목록에 `memset` 이 없다** — 곧 `free` 할 메모리에 쓰는 것을 지웠다. 그래서 다시 받은 조각에 `0xAB` 가 **없다**(`0 / 48`).
- ★★ **clang `-O2` 는 첫 `malloc`·`memset`·`free` 가 통째로 없다** — 결과를 안 쓰는 할당을 지웠다. 그래서 「다시 왔나 = 아니오」다.
- ★★ **`calloc` 은 네 벌 다 `64 / 64`** — 표준의 약속이다.
- ★ **바이트 0\~15** 는 할당기가 해제된 조각에 **관리 정보**를 쓰는 자리라 실행마다 흔들린다 — 세지 않았다.\
  ★ **해제된 포인터는 안 읽었다** — 옛 주소를 `free` **전에 정수로** 적어 두고 비교했다.

### 10. 다른 언어 — **Rust 는 컴파일러가 거부하고, Go 는 언어가 0 을 준다** ★★

**출력**

```text
===== rustc s30r.rs (rustc exit=1) =====
error[E0381]: used binding `x` isn't initialized
 --> s30r.rs:3:20
  |
2 |     let x: i32;
  |         - binding declared here but left uninitialized
3 |     println!("{}", x);
  |                    ^ `x` used here but it isn't initialized
  |
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider assigning a value
  |
2 |     let x: i32 = 42;
  |                ++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0381`.
```

```text
===== go run s30go.go (exit=0) =====
int=0 string="" pointer=<nil> struct={Port:0 Name: Next:<nil>}
```

**왜 그런가**

- ★★ **Rust — 컴파일 단계**에서 `error[E0381]: used binding 'x' isn't initialized` · **`rustc exit=1`**. 초기화 안 된 읽기가 **프로그램이 되지 못한다.**
- ★★ **Go — 제로 값**. 모든 변수가 0 · `""` · `nil` 로 시작한다. C 의 **정적 저장 기간 규칙을 모든 변수에** 적용한 것과 같다.
- ★ **C 의 대가**는 4번 격자다 — 48칸 중 18칸이 침묵했다.

### 11. 다섯 층 — **표준과 UB 가 같은 두께 · 미명시가 가장 정밀한 칸** ★★★

**왜 그런가**

- **표준** — 정적·스레드 = 0(패딩까지) · 부분 초기화의 나머지 0 · 자동·`malloc` = 불확정 · `calloc` = 모든 바이트 0 · `= {}` 는 C23 부터.
- **조건부 표준** — ★ **이 편이 던진 것 중에는 없다.** 정말 빈 것이 아니라 **안 던졌다** — `calloc` 의 0 바이트가 `double` 의 `+0.0` 이 되는 것이 IEC 60559 부록에 기대는 자리다.
- **구현 정의** — 어느 타입에 비값 표현이 있나(`_Bool` 은 `0`·`1` 밖 전부) · `.bss`/`NOBITS` · clang 이 `static const` 를 접는 것 · 진단 이름.
- **미명시** — 비값이 아닌 불확정 표현의 값 · **멤버 저장 뒤 패딩** · 해제된 조각의 재사용과 내용.
- **UB** — 주소를 안 잡은 자동 객체 읽기 · 비값 표현을 비문자 타입으로 읽기.
- ★★★ **가장 정밀한 칸은 미명시** — 불확정 표현이 **미명시 값이냐 비값 표현이냐**가 **UB 냐 아니냐**를 가른다.
- ★★ **침묵하는 자리** — 표준: 보장된 0 과 우연한 0 이 같은 글자 · 구현 정의: 비값 패턴을 읽기 전엔 모름 · 미명시: 패딩에 경고 0 · UB: P4 는 정적 도구 전부 침묵, P2 는 코드째 사라짐.
- ★★★ **「종료 코드 0인데 ill-formed」** — `-std=c17` 의 **`= {}` 가 경고 0 · `cc exit=0`**.
- ★ **제5의 상태** — 「불확정인가」를 값으로 못 물어 **MSan 의 그림자 비트**로 물었다. 바꾼 창은 **분기·반환에 안 쓰인 초기화 안 된 바이트**(패딩을 통째로 복사하는 것 등)를 **못 본다.**

### 12. 경계 ★

**왜 그런가**

- **저장 기간** — [28번 형제](../28-choosing-among-four-storage-durations/).
- **지정 초기자** — [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/) · **패딩의 자리** — [22번 형제](../22-struct-padding-and-alignment/).
- **`malloc`/`calloc` 계약** — [목록의 **37번 주제**](../37-malloc-calloc-realloc-free/) · **sanitizer 사용법** — 목록의 **58번 주제**.
- ★ 이 주제가 책임지는 것 — ① **무엇이 0 이고 무엇이 불확정인가**(와 `.bss` 증명) ② **도구 여섯의 침묵 지도**(48칸) ③ **불확정 · 미명시 · 비값의 층 구분**.

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s30a.c`·`s30b.c` | `.bss NOBITS 061aa0` 대 `.data PROGBITS 061aa0` · **1768 대 401792 바이트** · clang 이 `ro` 를 접음 | gcc `readelf` 1 · `size` 2 · `nm -S` 2 |
| `s30c.c` | 부분 초기화 나머지 0 · **네 벌 md5 동일** | 4벌 |
| `s30d.c` | ★★ `-std=c17` **경고 0 · `exit=0`** · `-pedantic-errors` `exit=1` · `-std=c2x` 통과 | 8칸 · 진단 2 · 실행 1 |
| `s30p1.c`\~`s30p8.c` | ★★★ **48칸 · 답한 칸 30** · P3 `-O0`/`-O2` · P2 가 `-O2` 에서 접힘 · MSan P4 | 격자 48 · 진단 4 · 어셈블리 1 · MSan 1 · `which valgrind` 1 |
| `s30e.c` | 패딩 — 정적 `00` 보장 · 초기자 셋 관찰 `00` · clang 멤버 대입 `aa` | 4벌 |
| `s30f.c` | `-O0` 흔적 48/48 · `-O2` `0/48` · `call` 목록 · `calloc 64/64` | 4벌 · 어셈블리 4 |
| `s30g.c` | ★★ `bool` 격자 — gcc 「참이면서 참」 · clang 「거짓」 · UBSan 4건씩 | 4벌 · UBSan 2 |
| `s30r.rs`·`s30go.go` | `E0381` · 제로 값 | rustc 1.92.0 · go1.27.1 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. **흔들린 것은 MSan 리포트의 PID·주소뿐**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **4번 격자의 모든 칸** — 경고는 컴파일러 판과 최적화 수준에 달렸다. ★ **P2 의 접힘은 UB 의 한 결과**다.
- ★★★ **6번 `bool` 격자** — UB 다. **어떤 값도 결론이 아니다.**
- ★★ **5번의 초기자 셋 `00`** · **9번의 재사용과 `-O2` 삭제** — 관찰이다.
- ★ **`.bss`/`NOBITS`** · clang 이 `static const` 를 접는 것 · 진단 문구 · MSan 이 반환에서 멈추는 것.

**정적 0 초기화(패딩 포함) · 부분 초기화의 나머지 0 · 자동·`malloc` 이 불확정인 것 · `calloc` 의 0 바이트 · 주소 안 잡은 자동 객체 읽기가 UB 인 것 · 비값 표현 규칙은 구현 의존이 아니다.**\
어느 C 구현에서도 같다(`= {}` 는 C23 부터).

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `-ftrivial-auto-var-init=zero` · MSan 에 패딩 `memcmp` · `calloc` 의 0 이 널 포인터·`0.0` 인지 · C23 `= {}` 가 패딩까지 0 을 보장하는지(관찰로는 `= {0}` 과 가를 수 없다) · `-O1`·`-O3`.
- ★ **못 잰 것** — **Valgrind 칸 전부.** 이 머신에 없다(`which valgrind` `exit=1`).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **4번 격자** — 경고 패스가 바뀌면 칸이 움직인다. 특히 **P2·P3 의 gcc 열**.
- ★★ **6번 격자** · **9번 `call` 목록**.
- ★ **3번의 문구** — gcc 는 아직 `C2X` 라는 옛 철자를 쓴다.
- **초기화 규칙 자체는 다시 돌릴 필요가 없다** — C89(지정 초기자 C99 · `= {}` C23) 이후 바뀐 적이 없다.
