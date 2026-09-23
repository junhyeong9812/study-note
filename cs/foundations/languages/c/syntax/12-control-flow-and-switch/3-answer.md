# c/syntax/12 — 제어문과 `switch`: **점프이지 블록이 아니다** — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고·에러·어셈블리는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★ **에러가 난 것도 그대로 실었다** — 종료 코드를 같이 적었다.
> ★★ **이 주제의 답은 「어느 도구가 무엇이라 하나」다.** UB 가 거의 없어 sanitizer 가 할 일이 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 중괄호를 뺀 중첩 `if` — `else` 는 **안쪽** `if` 에 붙는다

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘main’:
ex.c:4:8: warning: suggest explicit braces to avoid ambiguous ‘else’ [-Wdangling-else]
    4 |     if (a == 1)
      |        ^
끝
===== clang -std=c17 -Wall -Wextra =====
ex.c:7:5: warning: add explicit braces to avoid dangling else [-Wdangling-else]
    7 |     else
      |     ^
1 warning generated.
끝
```

**왜 그런가**

```text
   들여쓰기가 말하는 것              ★ 실제로 묶이는 것
   if (a == 1)                      if (a == 1) {
       if (b == 1)  ...                 if (b == 1) ...
   else                                 else        ...   <- 안쪽 if 의 else
       ...                          }

   a == 0 이므로 바깥 if 가 거짓 -> ★ 안쪽 전체를 건너뛴다 -> 출력은 "끝" 한 줄
```

- **출력은 `끝` 한 줄뿐**이다. `else` 가지는 실행되지 않는다.
- **`else` 는 가장 가까운 짝 없는 `if`** 에 붙는다. **들여쓰기는 컴파일러에게 아무 뜻이 없다.**
- **경고는 1건**이고 플래그는 **`-Wdangling-else`**, 소속은 ★ **`-Wall`** 이다 — **`-Wextra` 단독은 0건**이다.
- ★ **가리키는 줄이 다르다** — gcc 는 **바깥 `if`**(4행), clang 은 **`else`**(7행). 같은 사실을 다른 자리에서 말한다.

### 2. 루프 안의 `switch` 와 `continue` ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, exit=0) =====
(1) 0 | | 2 | 3 | 
(2) n=1 n=3 n=4 
(3) zero other two 
(4) k=0 k=1 k=2 
(clang 의 출력도 바이트 단위로 같다)
```

**왜 그런가**

```text
   (1)  i=0 -> default "0 " -> switch 끝 -> "| "
        i=1 -> case 1: break -> ★ switch 만 나간다 -> "| "     <- 루프는 계속 돈다
        i=2 -> "2 | "
        i=3 -> "3 | "
        ★ break 는 가장 안쪽 switch 또는 루프 ★ 하나만 끝낸다.

   (2)  continue 가 가는 곳
        for (init; cond; ★step) -> ★ step 으로 (증가가 실행된다)
        while (cond)            -> cond 로
        do { } while (★cond)    -> ★ cond 로  -> 무한 루프가 아니다
        실측: n=2 만 건너뛰고 n=3·n=4 가 찍혔다.

   (3)  default 는 ★ 위치가 자유다. "매치가 없을 때" 가 조건이지 "마지막" 이 조건이 아니다.
```

- **첫 덩어리에서 `break` 는 `switch` 만 끝낸다.** `| ` 가 **네 번 다** 찍힌 것이 증거다.\
  ★ **루프를 나가려면 깃발 변수나 `goto` 가 필요하다.**
- **둘째 덩어리는 무한 루프가 아니다.** `continue` 가 **조건 검사**로 가므로 `n` 이 계속 는다.
- **셋째 덩어리는 문제가 없다.** `zero other two` 가 나온다.
- **경고는 0건**이다 — ★ **이 주제에서 가장 많이 당하는 사고(`break` 가 루프를 안 끝냄)를 아무 도구도 말해 주지 않는다.**\
  **정의된 동작**이기 때문이다.

### 3. `break` 를 빠뜨리면 — **gcc 와 clang 이 다른 일을 한다**

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘run’:
ex.c:6:9: warning: this statement may fall through [-Wimplicit-fallthrough=]
    6 |         printf("one ");
      |         ^~~~~~~~~~~~~~
ex.c:7:5: note: here
    7 |     case 2:
      |     ^~~~
x=1 : one two 
x=2 : two 
x=3 : three four 
x=4 : four 
x=5 : other 
```

```text
[gcc -Wall                       ] ★ 0 건 exit=0
[gcc -Wextra                     ]   1 건 exit=0
[gcc -Wall -Wextra               ]   1 건 exit=0
[gcc -Wimplicit-fallthrough=1    ]   1 건 exit=0
[gcc -Wimplicit-fallthrough=3    ]   1 건 exit=0
[gcc -Wimplicit-fallthrough=5    ] ★ 2 건 exit=0
[clang -Wall -Wextra             ] ★ 0 건 exit=0
[clang -Wimplicit-fallthrough    ] ★ 2 건 exit=0
```

```text
===== clang -std=c17 -Wimplicit-fallthrough =====
ex.c:7:5: warning: unannotated fall-through between switch labels [-Wimplicit-fallthrough]
    7 |     case 2:
      |     ^
ex.c:7:5: note: insert '__attribute__((fallthrough));' to silence this warning
ex.c:7:5: note: insert 'break;' to avoid fall-through
ex.c:13:5: warning: unannotated fall-through between switch labels [-Wimplicit-fallthrough]
   13 |     case 4:
      |     ^
```

**왜 그런가**

```text
   이 소스에는 fall-through 가 둘 있다.
   ① case 1 -> case 2 : 주석 없음            (실수로 보이는 것)
   ② case 3 -> case 4 : /* fall through */ 주석 있음

   gcc  기본(=3) : ① 만 (1건)    <- ★ 주석을 읽어 준다
   gcc  =5       : ①② 다 (2건)   <- ★ 주석을 안 봐주고 속성을 요구한다
   clang         : ①② 다 (2건)   <- ★ 주석 자체를 안 읽는다
                   그리고 ★ -Wall 에도 -Wextra 에도 없다
```

- **`x=1` 이 `one two`** 를 찍는다 — `break` 가 없어 다음 `case` 로 흘렀다.
- ★ **gcc 의 `-Wimplicit-fallthrough` 는 `-Wextra` 소속**이다(`-Wall` 단독 0건).
- ★★ **clang 은 `-Wall -Wextra` 에 이 검사가 없다.** **직접 켜야** 하고, 켜면 **주석을 안 읽어 2건**을 낸다.\
  **같은 플래그 이름인데 기본 소속도 판정 기준도 다르다.**
- clang 은 고치는 법을 두 줄로 제안한다 — `__attribute__((fallthrough));` 또는 `break;`.

### 4. `case` 가 `do` 루프 안에 있으면 — **컴파일되고 정확히 동작한다** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘send’:
ex.c:5:24: warning: this statement may fall through [-Wimplicit-fallthrough=]
    5 |     case 0: do { *to++ = *from++;
      |                  ~~~~~~^~~~~~~~~
ex.c:6:5: note: here
    6 |     case 7:      *to++ = *from++;
      |     ^~~~
(같은 모양의 경고가 ★ 7 건)
복사 결과 : ABCDEFGHIJKLMNOPQRSTU
길이      : 21
```

```text
[gcc -Wall                          ] ★ 0 건 exit=0
[gcc -Wextra                        ]   7 건 exit=0
[gcc -Wall -Wextra -pedantic        ]   7 건 exit=0
[gcc -Wall -Wextra -Wimplicit-fallthrough=5] 7 건 exit=0
[clang -Wall -Wextra                ] ★ 0 건 exit=0
[clang -Wimplicit-fallthrough       ]   7 건 exit=0
```

**왜 그런가**

```text
   count = 21,  21 % 8 = 5,  n = (21+7)/8 = 3

   +-------------------------------------------------+
   | case 0:  do {  X                                |
   | case 7:        X                                |
   | case 6:        X                                |
   | case 5:        O  <- ★ 여기로 뛰어든다 (첫 바퀴 5개) |
   | case 4:        O                                |
   | case 3:        O                                |
   | case 2:        O                                |
   | case 1:        O                                |
   |          } while (--n > 0);                     |  <- 둘째·셋째 바퀴는 위부터 8개씩
   +-------------------------------------------------+
     5 + 8 + 8 = ★ 21개
```

- **컴파일된다.** 21자가 **정확히** 복사됐다.
- **`case 5:` 로 뛰고 세 바퀴**를 돈다 — 첫 바퀴 5개, 나머지 두 바퀴 8개씩.
- **경고는 7건**이고 전부 fall-through 다. **gcc `-Wextra`**, clang 은 **직접 켜야** 나온다.
- ★★★ **이 코드가 합법이라는 사실이 증명하는 것** — **`case` 는 문이 아니라 라벨**이고,\
  **`switch` 는 「어느 블록을 실행할까」를 고르는 것이 아니라 「어느 주소로 뛸까」를 고른다.**\
  블록을 고르는 것이었다면 **`do` 블록 안쪽의 라벨로 뛰어드는 일이 성립하지 않는다.**

### 5. `switch` 안에서 선언하면 — **경고**다. 단 VLA 면 **에러**다 ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘main’:
ex.c:5:13: warning: statement will never be executed [-Wswitch-unreachable]
    5 |         int v = 99;            /* 첫 case 앞의 선언 — 실행되지 않는다 */
      |             ^
ex.c:10:9: warning: ‘v’ is used uninitialized [-Wuninitialized]
   10 |         printf("case 2: v=%d\n", v);
      |         ^~~~~~~~~~~~~~~~~~~~~~~~~~~
ex.c:5:13: note: ‘v’ was declared here
case 2: v=32764
===== clang -std=c17 -Wall -Wextra (exit=0) =====
ex.c:7:34: warning: variable 'v' is uninitialized when used here [-Wuninitialized]
    7 |         printf("case 1: v=%d\n", v);
      |                                  ^
ex.c:5:9: note: variable 'v' is declared here
1 warning generated.
case 2: v=32765
```

**VLA 로 바꾸면**

```text
===== 소스: ex.c =====
    switch (m) {
    case 4:;
        int vla2[m];             /* switch 안에서 VLA 를 만든다 */
        vla2[0] = 2;
        printf("vla2 %d\n", vla2[0]);
        break;
    default: break;
    }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
ex.c:10:5: error: switch jumps into scope of identifier with variably modified type
   10 |     default: break;
      |     ^~~~~~~
ex.c:4:5: note: switch starts here
    4 |     switch (m) {
      |     ^~~~~~
ex.c:7:13: note: ‘vla2’ declared here
exit=1
```

**왜 그런가**

```text
   switch (x) {
       int v = 99;     <- 이 "문" 은 어떤 라벨보다도 앞에 있다
   case 1: ...            switch 는 case 로 ★ 뛰어들므로 이 문을 건너뛴다
   case 2: ...            -> v 는 ★ 선언은 되어 있고 ★ 초기화만 안 됐다
   }
```

- **에러가 아니라 경고**다. **컴파일되고 실행된다.**
- **gcc 는 `32764`, clang 은 `32765`** 를 찍었다 — **스택에 남아 있던 값**이고 **실행마다 달라질 수 있다.**
- **경고는 gcc 2건**(`-Wswitch-unreachable`·`-Wuninitialized`, 둘 다 **`-Wall`**), **clang 1건**이다.
- ★ **`int vla[x];` 로 바꾸면 에러**다(`exit=1`). `switch` 가 **VLA 스코프 안으로 뛰어드는 꼴**이라\
  8번의 `goto` 와 **같은 규칙**에 걸린다. gcc 의 문구가 아예 「**switch** jumps into scope …」다.
- ★ **막는 법은 `case` 몸통에 중괄호**를 치는 것이다 — `case 4: { int vla2[m]; … break; }`.

### 6. `char` 를 `switch` 하면 — 타입 하나가 답을 바꾼다

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘main’:
ex.c:7:5: warning: case label value exceeds maximum value for type [-Wswitch-outside-range]
    7 |     case 200:  printf("case 200 에 걸렸다\n"); break;
      |     ^~~~
c = -56  (CHAR_MIN=-128)
case -56 에 걸렸다
unsigned char 200 은 case 200 에 걸린다
===== clang -std=c17 -Wall -Wextra (exit=0) =====
ex.c:7:10: warning: overflow converting case value to switch condition type (200 to -56) [-Wswitch]
    7 |     case 200:  printf("case 200 에 걸렸다\n"); break;
      |          ^
1 warning generated.
```

**왜 그런가**

```text
   switch (c)    c 는 plain char (여기서는 부호 있음, -128 ~ 127)
       ↓ ★ 제어식이 정수 승격을 받는다 (03번)
   switch ((int)c)   -> -56

   case 200 은 int 상수 200 이다.
   ★ 승격된 char 가 200 이 되는 일은 없다 -> ★ 영원히 안 걸린다

   unsigned char u = 200 -> 승격하면 200 (0~255 가 전부 int 에 들어간다)
   -> ★ case 200 에 걸린다.
```

- **`c` 는 `-56`** 이고 `case -56` 에 걸린다. `case 200` 은 **도달 불가**다.
- **`unsigned char` 쪽은 같은 200 이 `case 200` 에 걸린다.** **같은 숫자인데 타입이 답을 바꾼다.**
- **경고는 양쪽 다 1건**이지만 ★ **플래그 이름과 문구가 다르다** —\
  gcc 는 `-Wswitch-outside-range`(「exceeds maximum value for type」),\
  clang 은 `-Wswitch`(「overflow converting case value to switch condition type **(200 to -56)**」)로 **변환된 값까지** 찍는다.
- ★ **`(char)200` 이 `-56` 인 것은 구현 정의**다 — **plain `char` 의 부호**가 구현에 맡겨져 있다([02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)).

### 7. `switch` 는 블록인가 점프인가 — **점프다** ★★

**답**

- **한 문장으로** — **`case` 는 문이 아니라 라벨이고, `switch` 는 매치되는 라벨의 주소로 뛰는 것**이라서\
  **라벨이 어느 중첩 블록 안에 있든 상관이 없다.**
- **`case 3:` 은 라벨이다.** `goto` 의 `out:` 과 **같은 종류의 물건**이고, 차이는 **누가 뛰느냐**뿐이다 —\
  `goto` 는 이름으로 뛰고 `switch` 는 **값으로** 뛴다.
- **fall-through 는 버그가 아니라 설계다.** 라벨은 **도착점**일 뿐 **경계가 아니다.**\
  경계를 만들고 싶으면 **`break` 를 직접 써야** 한다.

```text
   if 였다면                        switch 는
   +----------------------+        +----------------------+
   | 조건이 맞는 "블록"    |        | 값이 맞는 "주소"      |
   | 하나를 실행하고 끝     |        | 로 뛰고 ★ 계속 걷는다 |
   +----------------------+        +----------------------+
                                     -> 그래서 Duff 가 합법이다
```

- ★ 어셈블리로도 보인다 — `case 0`\~`4` 를 둔 함수를 `gcc -O2 -S -masm=intel` 로 찍으면\
  `cmp edi, 4` / `ja .L2` / `lea rdx, .L4[rip]` / `notrack jmp rax` 와 `.L4:` 아래의 **오프셋 표**가 나온다.\
  **문자 그대로** 「**주소로 뛰는 것**」이다.

### 8. `goto` 가 못 넘는 선 ★

**출력**

```text
===== 할 수 있는 것 — 정리 코드를 한 곳으로 (gcc -Wall -Wextra -pedantic, 경고 0 건, exit=0) =====
fail_at=1
  1단계 실패
  정리 완료 rc=-1
fail_at=2
  2단계 실패
  정리 완료 rc=-1
fail_at=0
  전부 성공
  정리 완료 rc=0
===== gcc -fsanitize=address,undefined -fno-sanitize-recover=all =====
exit=0   (진단 0줄)
```

```text
===== 못 하는 것 — VLA 스코프 안으로 =====
===== 소스: ex.c =====
#include <stdio.h>
int main(void) {
    int n = 4;
    int x = 1;
    if (x) goto skip;            /* VLA 스코프 안으로 뛴다 */
    int vla[n];
    vla[0] = 7;
skip:
    printf("여기 왔다 %d\n", n);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
ex.c: In function ‘main’:
ex.c:5:12: error: jump into scope of identifier with variably modified type
    5 |     if (x) goto skip;            /* VLA 스코프 안으로 뛴다 */
      |            ^~~~
ex.c:8:1: note: label ‘skip’ defined here
    8 | skip:
      | ^~~~
ex.c:6:9: note: ‘vla’ declared here
exit=1
===== clang -std=c17 -Wall -Wextra =====
ex.c:5:12: error: cannot jump from this goto statement to its label
    5 |     if (x) goto skip;            /* VLA 스코프 안으로 뛴다 */
      |            ^
ex.c:6:9: note: jump bypasses initialization of variable length array
    6 |     int vla[n];
      |         ^
1 error generated.
exit=1
```

**왜 그런가**

- **할 수 있는 것 셋** — ① 같은 함수 안 **아무 라벨로** ② **앞으로도 뒤로도** ③ **블록 밖으로 나오기**.
- **못 하는 것 둘** — ① **다른 함수로**(라벨은 함수마다 따로다) ② ★ **VLA 가 사는 스코프 안으로**.
- ★ **경고가 아니라 에러**이고 **`exit=1`** 이다. **컴파일러가 막아 주는 몇 안 되는 자리**다.\
  이유는 **VLA 가 들어갈 때 크기만큼 자리를 잡는데 그 자리 잡기를 건너뛰게 되기 때문**이다.
- ★ **clang 쪽이 이유를 말한다** — 「jump **bypasses initialization** of variable length array」.\
  gcc 는 「jump into scope of identifier with **variably modified type**」로 **무엇인지만** 말한다.
- ★ **같은 규칙이 `switch` 에도 걸린다**(5번 답) — gcc 의 문구가 「**switch** jumps into scope …」다.

### 9. `case` 에 무엇을 쓸 수 있나 ★★

**출력**

```text
===== 되는 것 (gcc·clang 둘 다 exit=0) =====
enum Color { RED = 1, GREEN = 2 };
#define K 3
case RED:            /* 열거 상수 */
case K:              /* 매크로가 펼쳐진 상수 */
case 1 + 1:          /* 상수식 */
case sizeof(int):    /* 4 */
-> x = 3 일 때 "K" 를 찍었다.

===== const int (ex.c) =====
const int K = 3;
switch (x) { case K: ... }

gcc   : ex.c: In function ‘main’:
        ex.c:6:5: error: case label does not reduce to an integer constant
            6 |     case K:            /* const int 는 정수 상수식이 아니다 */
              |     ^~~~
        exit=1
clang : ex.c:6:10: warning: expression is not an integer constant expression;
        folding it to a constant is a GNU extension [-Wgnu-folding-constant]
            6 |     case K:            /* const int 는 정수 상수식이 아니다 */
              |          ^
        1 warning generated.
        exit=0   ★ 실행된다 — "K" 를 찍었다
clang -pedantic-errors :
        ex.c:6:10: error: expression is not an integer constant expression;
        folding it to a constant is a GNU extension [-Werror,-Wgnu-folding-constant]

===== 제어식이 정수가 아니면 =====
double d = 1.0; switch (d) { case 1: ... }
gcc   : error: switch quantity not an integer                     exit=1
clang : error: statement requires expression of integer type ('double' invalid)

===== 중복 case =====
case 'A': ... case 65: ...
gcc   : ex.c:7:5: error: duplicate case value
        ex.c:6:5: note: previously used here                      exit=1
```

**왜 그런가**

- **`case` 라벨은 정수 상수식**이어야 한다 — **컴파일 시간에 값이 정해져야** 점프 표를 만들 수 있다.
- **열거 상수·매크로·`1+1`·`sizeof(int)` 는 전부 정수 상수식**이다([07번 형제](../07-enum-and-enumeration-constants/)).
- ★★ **`const int` 는 아니다.** C 의 `const` 는 「**바꾸지 마라**」이지 「**컴파일 시간 상수**」가 아니다(C++ 와 다른 자리다).
- ★★★ **「내 기계에서는 된다」가 나는 자리가 바로 여기다** — **gcc 는 에러, clang 은 GNU 확장으로 받아 준다.**\
  `-pedantic-errors` 를 주면 clang 도 에러가 된다.
- **부동소수 제어식과 중복 `case` 는 양쪽 다 에러**다.

### 10. `-std=` 는 무엇을 강제하나 — **아무것도 강제하지 않는다** ★★★

**출력**

```text
[gcc -std=c89 -Wall -Wextra -Wimplicit-fallthrough=5          ] 경고 ★ 0 건  에러 0 건  exit=0
[gcc -std=c89 -Wall -Wextra -Wimplicit-fallthrough=5 -pedantic]   경고 1 건  에러 0 건  exit=0
[gcc -std=c99 -Wall -Wextra -Wimplicit-fallthrough=5          ] 경고 ★ 0 건  에러 0 건  exit=0
[gcc -std=c99 -Wall -Wextra -Wimplicit-fallthrough=5 -pedantic]   경고 1 건  에러 0 건  exit=0
[gcc -std=c17 -Wall -Wextra -Wimplicit-fallthrough=5          ] 경고 ★ 0 건  에러 0 건  exit=0
[gcc -std=c17 -Wall -Wextra -Wimplicit-fallthrough=5 -pedantic]   경고 1 건  에러 0 건  exit=0
[gcc -std=c2x -Wall -Wextra -Wimplicit-fallthrough=5          ] 경고   0 건  에러 0 건  exit=0
[gcc -std=c2x -Wall -Wextra -Wimplicit-fallthrough=5 -pedantic] 경고   0 건  에러 0 건  exit=0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
ex.c: In function ‘run’:
ex.c:6:9: warning: ISO C does not support ‘[[]]’ attributes before C2X [-Wpedantic]
    6 |         [[fallthrough]];
      |         ^
===== clang -std=c17 -Wall -Wextra -pedantic =====
ex.c:6:9: warning: [[]] attributes are a C23 extension [-Wc23-extensions]
    6 |         [[fallthrough]];
      |         ^
1 warning generated.
```

```text
===== 소스: ex.c (라벨 뒤 선언) =====
#include <stdio.h>
int main(void) {
    int x = 2;
    switch (x) {
    case 1:
        printf("one\n");
        break;
    case 2:
        int v = 99;            /* C23 전에는 라벨 뒤 선언이 위반이다 */
        printf("case 2: v=%d\n", v);
        break;
    }
    return 0;
}
```

```text
===== 라벨 뒤 선언 (위 ex.c) =====
[gcc -std=c17 -Wall -Wextra                  ] 경고 ★ 0 건  exit=0
[gcc -std=c17 -Wall -Wextra -pedantic        ]   경고 1 건  exit=0
        ex.c:9:9: warning: a label can only be part of a statement and a declaration is not a statement [-Wpedantic]
[gcc -std=c17 -Wall -Wextra -pedantic-errors ]   ★ error   exit=1
        ex.c:9:9: error: a label can only be part of a statement and a declaration is not a statement [-Wpedantic]
[gcc -std=c2x -Wall -Wextra -pedantic        ]   경고 0 건  exit=0   ★ C23 부터 합법
[clang -std=c17 -Wall -Wextra                ]   경고 1 건 (-Wc23-extensions)
```

**왜 그런가**

- ★★★ **C23 문법이 `-std=c89` 에서 경고 0건으로 통과한다.** **`-std=` 는 강제가 아니라 기본값 선택**이다.\
  **표준 준수를 주장하려면 `-pedantic` 이 필요하다** — 켜면 c89·c99·c17 전부 1건이 된다.
- ★ **`[[fallthrough]]` 는 `-std=c89` 에서도 `-Wimplicit-fallthrough=5` 를 조용히 시킨다.**\
  **경고 억제는 표준 준수와 별개로 동작한다.**
- **라벨 뒤 선언은 `-pedantic` 에서 경고, `-pedantic-errors` 에서 에러**다. **C23(`-std=c2x`)부터는 합법**이라 0건이 된다.
- **gcc 13 에서 C23 을 쓰려면 `-std=c2x`** 다. ★ **`-std=c23` 은 경고 0건에 `exit=1`**(옵션 자체가 없다)이었다 —\
  [11번 형제](../11-bitwise-operations-and-shifts/)에서 실측했고, **경고만 세면 「0건 통과」로 기록된다.**

### 11. `for (;;)` 과 `while (1)` — **기계어가 같다**

**출력**

```text
===== gcc -std=c17 -O2 -S -masm=intel =====
loop_for:                       loop_while:                     loop_do:
	endbr64                 	endbr64                 	endbr64
	push	rax             	push	rax             	push	rax
	pop	rax             	pop	rax             	pop	rax
	sub	rsp, 8          	sub	rsp, 8          	sub	rsp, 8
	.p2align 4,,10          	.p2align 4,,10          	.p2align 4,,10
	.p2align 3              	.p2align 3              	.p2align 3
.L2:                            .L6:                            .L9:
	call	tick@PLT        	call	tick@PLT        	call	tick@PLT
	jmp	.L2             	jmp	.L6             	jmp	.L9
```

```text
===== gcc -std=c17 -O0 -c · objdump -d (최적화를 끄고도 같다) =====
0000000000000000 <loop_for>:        000000000000000f <loop_while>:      000000000000001e <loop_do>:
   0:	endbr64                       f:	endbr64                      1e:	endbr64
   4:	push   %rbp                  13:	push   %rbp                  22:	push   %rbp
   5:	mov    %rsp,%rbp             14:	mov    %rsp,%rbp             23:	mov    %rsp,%rbp
   8:	call   d <loop_for+0xd>      17:	call   1c <loop_while+0xd>   26:	call   2b <loop_do+0xd>
   d:	jmp    8 <loop_for+0x8>      1c:	jmp    17 <loop_while+0x8>   2b:	jmp    26 <loop_do+0x8>
(경고 0 건)
```

**왜 그런가**

- **어느 쪽도 빠르지 않다.** **명령 열이 완전히 같다.**
- ★ **`-O0` 에서까지 같다는 것이 더 강한 근거다.** `-O2` 에서만 같았다면 「**최적화가 지워 준 것**」일 수 있는데,\
  `-O0` 에서도 같다는 것은 **프런트엔드가 처음부터 같은 것으로 본다**는 뜻이다.
- **`while (1)` 의 조건 비교는 어디에도 없다.** `cmp` 명령이 **한 개도 안 나온다** — 상수 조건이라 코드가 생기지 않는다.
- ★ **이것은 도식이 아니라 도구의 출력**이다. 지어낼 수 없고 독자가 자기 머신에서 재현한다.
- 고르는 기준은 **가독성**뿐이다 — `for (;;)` 는 **조건이 없다는 것을 형태로** 말하고, `while (1)` 은 **읽기 쉽다.**

### 12. 다섯 층과 도구 ★★

**답**

| 층 | 이 주제(12번) | [11번](../11-bitwise-operations-and-shifts/) | [10번](../10-evaluation-order-and-sequence-points/) |
|---|---|---|---|
| **표준** | ★★ **본체** — dangling else 결합 · fall-through · **`case` 가 라벨** · `break`/`continue` 가 가는 곳 · `default` 위치 자유 · 제어식 승격 · `for(;;)` ≡ `while(1)` | 비트 연산의 동작 · 승격 | 시퀀스 포인트 · 단락 평가 |
| **조건부 표준** | ★ **해당 없음** | ★ **해당 없음** | ★ **해당 없음** |
| **구현 정의** | plain `char` 의 부호 · `switch` 를 점프 표로 만들지 | ★ **찬다** — `-1 >> 1` · 비트필드 배치 | ★ **비어 있다** |
| **미명시** | ★ **해당 없음** | ★ **해당 없음** | ★★ **본체** |
| **UB** | ★ **거의 없다** — 오용이 대개 **컴파일 에러**로 막힌다 | ★★ **본체 셋** | 같은 객체 두 번 건드리기 |

- **비어 있는 칸은** 「**조건부 표준**」과 「**미명시**」다. 조건부 보장이 걸릴 매크로가 없고,\
  **제어 흐름에는 「여러 가능성 중 하나」로 둘 자리가 없다** — 어디로 가는지가 전부 정해져 있다.\
  (제어식 **안에** 부작용을 둘 넣으면 그 순서는 미명시가 되는데, **그것은 [10번](../10-evaluation-order-and-sequence-points/)의 몫**이다.)
- ★★ **세 주제의 층 분포가 서로 다르다.** 10번은 **미명시**, 11번은 **UB**, 12번은 **표준 + 컴파일 에러**가 본체다.\
  **같은 언어의 같은 다섯 층인데 주제마다 무게중심이 옮겨 간다** — 그것이 이 다섯 층 표를 매번 그리는 이유다.
- ★ **어떤 도구도 안 잡는 함정** — **루프 안 `switch` 의 `break` 가 루프를 안 끝내는 것**(2번 답).\
  **경고 0건**이고 sanitizer 도 할 일이 없다. **문법이 맞고 동작도 정의되어 있기 때문**이다.\
  ★ [10번의 미명시](../10-evaluation-order-and-sequence-points/)·[11번의 구현 정의](../11-bitwise-operations-and-shifts/)와 **같은 성격의 사각지대**다 —\
  「**틀린 것**」이 아니라 「**내 뜻이 아닌 것**」이고, 도구는 뜻을 모른다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 컴파일러·플래그로 돌렸나 |
|---|---|---|
| dangling else (12-a) | 출력이 `끝` 한 줄 · gcc 4행 / clang 7행 · **`-Wextra` 단독 0건** | gcc 5벌 · clang 1벌 |
| 제어 흐름 4종 (12-b) | `0 \| \| 2 \| 3 \|` · `n=1 n=3 n=4` · `zero other two` · **경고 0건** · clang 출력이 **바이트 단위로 같음** | gcc·clang `-Wall -Wextra -pedantic` |
| `continue` 자리 (12-c) | `for : 0 1 3 4` ↔ `while : 1 2 4 5` — **증가 칸이 실행되는 것** | gcc `-Wall -Wextra -pedantic` |
| `goto` 정리 (12-c) | 세 경로 모두 `정리 완료` · **ASan+UBSan 진단 0줄** | gcc `-fsanitize=address,undefined -fno-sanitize-recover=all` |
| VLA 점프 (12-d) | **`goto` → error `exit=1`** · gcc/clang 문구가 다름 | gcc·clang |
| Duff (12-e) | **21자 정확히 복사** · fall-through **7건** · `-Wall` 0건 / `-Wextra` 7건 / clang `-Wall -Wextra` **0건** | gcc 5벌 · clang 2벌 |
| fall-through (12-f) | 다섯 줄 출력 · gcc `-Wall` 0 / `-Wextra` 1 / `=5` **2** · clang `-Wall -Wextra` **0** / 켜면 **2** | gcc 8벌 · clang 2벌 |
| `[[fallthrough]]` (12-g) | **c89 에서 0건** · `-pedantic` 1건 · `-std=c2x` 0건 · clang `-Wc23-extensions` | gcc 8벌 · clang 2벌 |
| `switch` 안 선언 (12-h) | **경고 2건**(gcc) / 1건(clang) · 값 **`32764` ↔ `32765`** | gcc 5벌 · clang 1벌 |
| `switch`+VLA (12-i) | **error `exit=1`** — 「switch jumps into scope …」 | gcc |
| 제어식 승격 (12-j) | `c=-56` · `case 200` 도달 불가 · gcc `-Wswitch-outside-range` / clang `-Wswitch`(**200 to -56**) | gcc 5벌 · clang 1벌 |
| `case` 상수식 (12-k·l) | 열거·매크로·`1+1`·`sizeof` 통과 · **`const int` 는 gcc error / clang 경고 후 실행** · `double` 제어식 error · 중복 error | gcc·clang · clang `-pedantic-errors` |
| 무한 루프 (12-m) | 세 함수의 명령 열이 **`-O2` 와 `-O0` 둘 다 동일** · `cmp` 없음 | gcc `-O2 -S` · `-O0 -c` + `objdump` |
| 점프 표 | `switch` 가 `notrack jmp rax` + `.long .L8-.L4` 오프셋 표로 컴파일됨 | gcc `-O2 -S -masm=intel` |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3)에서만** 그렇다.

- **plain `char` 가 부호 있는 것**(`(char)200` 이 `-56`, `CHAR_MIN=-128`) — ★ **구현 정의**다([02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)).
- `switch` 가 **점프 표**로 컴파일된 것 — 구현이 고르는 것이고 **동작은 어느 쪽이든 같다.**
- 초기화 안 된 `v` 가 **`32764`(gcc)·`32765`(clang)** 인 것 — ★ **쓰레기값이라 아무 근거도 못 된다.**
- `-Wimplicit-fallthrough` 가 **gcc `-Wextra`** 에 있고 **clang 은 어느 집합에도 없는 것** — 진단 구현의 분류다.
- `case` 에 `const int` 를 **clang 이 받아 주는 것**(GNU 확장).
- gcc 13.3.0 에 **`-std=c23` 이 없는 것**(`-std=c2x`).

**제어문의 규칙 자체는 구현 의존이 아니다.** dangling else 의 결합 · fall-through · **`case` 가 라벨이라는 것** ·\
`break`/`continue` 가 가는 곳 · 제어식의 정수 승격은 **어느 C 구현에서도 같다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `do { } while (0)` 매크로 관용구(목록의 **42번 주제**) · 계산된 `goto`(`goto *ptr;`, GNU 확장) ·\
  `setjmp`/`longjmp` · 희소한 `case`·큰 범위에서 점프 표가 비교 사슬로 바뀌는 경계 · C23 의 다른 제어 흐름 변경 전수 확인.
- **못 잰 것** — ★ **「`switch` 가 `if` 사슬보다 빠른가」.** 어셈블리를 한 번 본 것이 전부이고,\
  **수치를 내려면 측정 조건(도구·머신·반복·흔들림 폭) 선언이 필요**한데 이 문서는 그것을 하지 않았다.\
  ★ `for(;;)` ↔ `while(1)` 은 **기계어가 같아 잴 것 자체가 없었다** — 「못 잰 것」이 아니라 「**잴 필요가 없는 것**」이다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- `-Wimplicit-fallthrough` 의 **기본 소속**(gcc `-Wextra` · clang 없음)과 **기본 레벨**(gcc 3).
- clang 이 `case` 의 `const int` 를 **여전히 받아 주는지**(`-Wgnu-folding-constant`).
- gcc 가 **`-std=c23` 을 받기 시작했는지**(13.3.0 은 `-std=c2x` 뿐).
- gcc·clang 의 **진단 문구** — 이 문서는 문구를 그대로 인용한다.
- **제어문의 규칙 자체는 다시 돌릴 필요가 없다** — C89 이후 바뀐 적이 없고, C23 이 바꾼 둘은 이 문서가 실측했다.
