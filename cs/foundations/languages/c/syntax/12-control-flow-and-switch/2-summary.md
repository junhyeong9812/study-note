# c/syntax/12 — 제어문과 `switch`: **점프이지 블록이 아니다** — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — Statements (C)](https://en.cppreference.com/w/c/language/statements) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html) · [Clang Diagnostic flags](https://clang.llvm.org/docs/DiagnosticsReference.html)
> **실행 검증** — 이 문서의 모든 출력·경고·에러·어셈블리는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과\
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★ **에러가 난 것도 출력이다** — 이 문서에는 **컴파일이 실패한 프로그램이 넷** 실려 있고 종료 코드를 같이 적었다.
> **버전** — `if`/`while`/`for`/`switch`/`goto` 의 규칙은 **C89 이후 바뀐 적이 없다.**\
> **C23 이 둘을 바꿨다** — `[[fallthrough]]` 속성과 **라벨 뒤 선언 허용**. 아래 (6)·(7)에서 실측한다.\
> ★ **gcc 13.3.0 에는 `-std=c23` 이 없다**(`-std=c2x` 뿐) — [11번 형제](../11-bitwise-operations-and-shifts/)에서 실측했다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★ **경계** — `?:` 가 시퀀스 포인트인 것과 단락 평가는 [10번 형제](../10-evaluation-order-and-sequence-points/)가 정본이다.\
> `case` 라벨에 쓰는 **열거 상수**는 [07번 형제](../07-enum-and-enumeration-constants/), 제어식의 **승격 규칙**은 [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)가 정본이다.
> 선행 — [07번 형제](../07-enum-and-enumeration-constants/).

## 한눈에 — 쉽게 말하면

**`if`·`while`·`for` 는 「상자」인데 `switch` 는 「상자가 아니라 문패 붙은 주소들」이다.**

건물에 비유하면 이렇다.\
`if (…) { … }` 는 **방**이다 — 조건이 맞으면 방에 들어가고, 방을 나오면 끝난다.\
그런데 `switch` 는 방이 아니라 **복도에 문패를 몇 개 박아 둔 것**이다.\
`case 3:` 은 **문이 아니라 「3번 주소」라는 팻말**이고, `switch` 는 **그 주소로 뛰어드는 것**뿐이다.

그래서 **뛰어든 뒤에는 그냥 복도를 계속 걸어간다** — 다음 팻말을 그대로 지나친다(fall-through).\
멈추려면 `break` 를 직접 써야 한다. ★ **이것이 버그가 아니라 설계**이고,\
그 설계를 극단까지 쓴 것이 **Duff's device**(아래 (4))다.

| 비유 | 실체 | 층 |
|---|---|---|
| 방에 들어갔다 나온다 | `if`·`while`·`for` 의 몸통 | **표준** |
| 복도의 **문패** | `case 3:`·`default:` | **표준** — 문이 아니라 **라벨**이다 |
| 팻말을 지나쳐 계속 걷는다 | fall-through | **표준** — 막으려면 `break` |
| 문패가 **방 안쪽**에 박혀 있어도 된다 | Duff's device(`do`\~`while` 안의 `case`) | **표준** |
| `else` 는 **가장 가까운** `if` 에 붙는다 | dangling else | **표준** |
| 복도 안으로 **뛰어들 수 없는 구역** | VLA 가 사는 스코프 | ★ **컴파일 에러** |
| 문패 앞에서 짐을 풀어도 **아무도 안 푼다** | 첫 `case` 앞의 선언 | **표준** — 초기화가 실행되지 않는다 |

```text
   switch (x) {           x 의 값으로 "주소" 를 고른다
   case 1:  A();          <- 팻말 1        \
   case 2:  B(); break;   <- 팻말 2         |  x==1 이면 A 다음 B 까지 간다
   case 3:  C();          <- 팻말 3         |  (break 를 만나야 나간다)
   default: D();          <- 팻말 default  /
   }

   ★ if 였다면 A 만 실행됐을 것이다. switch 는 "고르는" 것이 아니라 "뛰는" 것이다.
```

- ★★ **이 주제에는 UB 가 거의 없다.** [11번 형제](../11-bitwise-operations-and-shifts/)가 **UB 가 본체**였고 [10번 형제](../10-evaluation-order-and-sequence-points/)가 **미명시가 본체**였다면,\
  여기는 **「표준」과 「컴파일 에러」 칸이 본체**다 — **틀리면 대개 빌드가 안 되거나, 되더라도 정의된 동작으로 틀린다.**
- ★ 그래서 이 주제의 검사는 **런타임 도구가 아니라 컴파일러 진단**에 몰려 있다.

> **라벨(label)** — 문 앞에 붙이는 이름. `case 3:`·`default:`·`out:` 이 전부 라벨이다.\
> 예: `goto out;` 의 `out:` 과 `case 3:` 은 **같은 종류의 물건**이다.

> **fall-through** — `case` 몸통이 끝났는데 `break` 가 없어 **다음 `case` 로 흘러드는 것**.\
> 예: `case 1: A(); case 2: B();` 에서 `x==1` 이면 `A` 와 `B` 가 둘 다 실행된다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★ **`switch` 가 블록이 아니라 점프라는 것을 무엇으로 증명하나** — Duff's device 가 합법인 이유.
2. ★ **fall-through 를 도구가 어떻게 다루나** — gcc 와 clang 이 **같은 플래그 이름으로 다른 일**을 한다.
3. ★ **제어문에서 컴파일이 아예 실패하는 자리는 어디인가** — 경고가 아니라 에러가 나는 넷.

## 동작 방식

### (1) `else` 는 가장 가까운 `if` 에 붙는다 — dangling else

**언제 쓰나** — 중괄호를 생략한 `if` 안에 또 `if` 가 있을 때.

```text
===== 소스: ex.c (12-a) =====
#include <stdio.h>
int main(void) {
    int a = 0, b = 0;
    if (a == 1)
        if (b == 1)
            printf("둘 다 1\n");
    else
        printf("else 가 어디에 붙었나?\n");
    printf("끝\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
ex.c: In function ‘main’:
ex.c:4:8: warning: suggest explicit braces to avoid ambiguous ‘else’ [-Wdangling-else]
    4 |     if (a == 1)
      |        ^
exit=0
끝
```

```text
===== clang -std=c17 -Wall -Wextra =====
ex.c:7:5: warning: add explicit braces to avoid dangling else [-Wdangling-else]
    7 |     else
      |     ^
1 warning generated.
끝
```

```text
   들여쓰기가 말하는 것              ★ 실제로 묶이는 것
   +---------------------------+   +---------------------------+
   | if (a == 1)               |   | if (a == 1) {             |
   |     if (b == 1)  ...      |   |     if (b == 1) ...       |
   | else                      |   |     else        ...       |  <- 안쪽 if 에 붙는다
   |     ... (바깥 if 의 else) |   | }                         |
   +---------------------------+   +---------------------------+
     a==0 이면 "else 가..." 출력      a==0 이면 ★ 아무것도 안 나온다
```

그림 해설 (한 단계씩):

- **`a` 가 0 인데 `else` 가지가 실행되지 않았다.** 출력이 `끝` 한 줄뿐이다.\
  `else` 가 **안쪽 `if (b == 1)` 에 붙었기 때문**이고, 바깥 `if` 가 거짓이라 **둘 다 건너뛴 것**이다.
- **들여쓰기는 컴파일러에게 아무 뜻이 없다.** 사람만 속는다.
- ★ **gcc 와 clang 이 다른 줄을 가리킨다** — gcc 는 **바깥 `if`**(4행), clang 은 **`else`**(7행).\
  **같은 사실을 다른 자리에서 말한다.** 플래그 이름은 둘 다 `-Wdangling-else` 다.
- ★ 그 플래그는 **`-Wall` 소속**이다(`-Wextra` 단독 0건 — 아래 (10)의 표).

비용 — 중괄호 두 개. **`if`·`else`·루프 몸통에는 언제나 중괄호를 쓴다**가 규칙이 된다.

### (2) 세 루프와 `break`/`continue` — `break` 는 가장 안쪽 하나만 끝낸다

**언제 쓰나** — 루프 안에 `switch` 가 있을 때. **가장 많이 당하는 자리**다.

```text
===== 소스: ex.c (12-b) =====
#include <stdio.h>
int main(void) {
    /* (1) switch 안의 break 는 루프가 아니라 switch 를 끝낸다 */
    printf("(1) ");
    for (int i = 0; i < 4; i++) {
        switch (i) {
        case 1: break;              /* 루프가 아니라 switch 를 나간다 */
        default: printf("%d ", i);
        }
        printf("| ");
    }
    printf("\n");
    /* (2) do-while 의 continue 는 조건으로 간다 */
    printf("(2) ");
    int n = 0;
    do {
        n++;
        if (n == 2) continue;       /* 조건 검사로 간다 — 무한루프가 아니다 */
        printf("n=%d ", n);
    } while (n < 4);
    printf("\n");
    /* (3) default 는 가운데 있어도 된다 */
    printf("(3) ");
    for (int i = 0; i < 3; i++) {
        switch (i) {
        case 0: printf("zero ");  break;
        default: printf("other "); break;
        case 2: printf("two ");   break;
        }
    }
    printf("\n");
    /* (4) 빈 for 의 세 칸 */
    printf("(4) ");
    int k = 0;
    for (;;) { if (k >= 3) break; printf("k=%d ", k); k++; }
    printf("\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, exit=0) =====
(1) 0 | | 2 | 3 | 
(2) n=1 n=3 n=4 
(3) zero other two 
(4) k=0 k=1 k=2 
(clang 의 출력도 바이트 단위로 같다)
```

```text
   (1) for 안의 switch 에서 break

       i=0  -> default: "0 " -> switch 끝 -> "| "
       i=1  -> case 1: break -> ★ switch 만 나간다 -> "| "   <- 루프는 계속 돈다
       i=2  -> default: "2 " -> "| "
       i=3  -> default: "3 " -> "| "

   ★ 루프를 나가고 싶었다면 break 로는 안 된다 — 깃발이나 goto 가 필요하다.
```

```text
   (2) continue 가 가는 곳

   for (init; cond; ★ step)  { ... continue; ... }   -> ★ step 으로 간다 (증가가 실행된다)
   while (cond)              { ... continue; ... }   -> cond 로 간다
   do { ... continue; ... } while (★ cond);          -> ★ cond 로 간다 (무한루프 아님)

   실측 : for   : 0 1 3 4      (i==2 만 건너뛰고 증가는 됐다)
          while : 1 2 4 5      (j 를 먼저 늘린 판)
```

그림 해설 (한 단계씩):

- **`case 1: break;` 가 루프를 끝내지 않았다.** `| ` 가 네 번 다 찍혔다 — `break` 는 **가장 안쪽의 `switch` 또는 루프 하나**만 끝낸다.
- **`do`\~`while` 의 `continue` 는 조건으로 간다.** `n==2` 를 건너뛰고도 `n=3`·`n=4` 가 찍혔다 — **무한루프가 아니다.**
- ★ **`for` 의 `continue` 는 증가 칸을 실행한다.** `while` 로 옮겨 적으면서 증가를 몸통 끝에 두면 **그 증가가 건너뛰어진다** —\
  `for` → `while` 변환에서 나는 고전적인 사고다.
- **`default` 는 가운데 있어도 된다.** `zero other two` 가 그 증거다 — **위치가 아니라 「매치가 없을 때」가 조건**이다.
- **`for (;;)` 는 세 칸을 다 비운 것**이고 그냥 무한 루프다(아래 (9)).

비용 — 없다. 다만 **루프 안의 `switch` 에서는 `break` 가 무엇을 끝내는지 한 번 더 본다.**

### (3) `goto` — 할 수 있는 것과 **못 하는 것**

**언제 쓰나** — 여러 단계 자원을 정리할 때. C 에는 `defer` 도 `finally` 도 없다.

```text
===== 소스: ex.c (12-c) =====
#include <stdio.h>
#include <stdlib.h>
static int work(int fail_at) {
    char *a = NULL, *b = NULL;
    int rc = -1;
    a = malloc(16); if (!a) goto out;
    if (fail_at == 1) { printf("  1단계 실패\n"); goto out; }
    b = malloc(16); if (!b) goto out;
    if (fail_at == 2) { printf("  2단계 실패\n"); goto out; }
    printf("  전부 성공\n");
    rc = 0;
out:
    free(b); free(a);
    printf("  정리 완료 rc=%d\n", rc);
    return rc;
}
int main(void) {
    printf("fail_at=1\n"); work(1);
    printf("fail_at=2\n"); work(2);
    printf("fail_at=0\n"); work(0);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, exit=0) =====
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
exit=0   (진단 0줄 — 누수도 이중 해제도 없다)
```

**★ 그런데 `goto` 가 못 넘는 선이 있다.**

```text
===== 소스: ex.c (12-d) =====
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

```text
   goto 가 할 수 있는 것              ★ 못 하는 것
   +---------------------------+   +---------------------------+
   | 함수 안 아무 라벨로        |   | VLA 가 사는 스코프 ★ 안으로 |
   | 앞으로도 뒤로도            |   |   -> 컴파일 에러           |
   | 블록 밖으로 나오기         |   | 다른 함수로 (라벨이 함수마다)|
   +---------------------------+   +---------------------------+

   이유 : VLA 는 들어갈 때 ★ 크기만큼 자리를 잡는다.
          그 자리 잡기를 건너뛰고 vla 를 쓰면 없는 메모리를 쓰게 된다.
          -> 컴파일러가 아예 막는다 (경고가 아니라 에러)
```

그림 해설 (한 단계씩):

- **`goto out;` 로 정리를 한 곳에 모으는 것은 C 의 정석**이다. ASan·UBSan 이 **진단 0줄**로 통과했다.
- ★ **VLA 스코프 안으로는 못 뛴다.** 경고가 아니라 **에러**이고 `exit=1` 이다 —\
  **컴파일러가 막아 주는 몇 안 되는 자리**다.
- **gcc 와 clang 의 문구가 다르다** — gcc 는 「jump into scope of identifier with **variably modified type**」,\
  clang 은 「jump **bypasses initialization** of variable length array」. **clang 쪽이 이유를 말해 준다.**
- ★ 같은 규칙이 **`switch` 에도 걸린다** — 아래 (7)에서 본다.

비용 — 없다. **정리 경로를 한 곳에 모으면 `free` 를 빠뜨릴 자리가 줄어든다.**

### (4) ★★★ Duff's device — `switch` 가 **점프이지 블록이 아니라는** 증거

**언제 쓰나** — 이 주제의 이해를 시험할 때. **실무에서 쓰라는 코드가 아니다.**

```text
===== 소스: ex.c (12-e) =====
#include <stdio.h>
static void send(const char *from, char *to, int count) {
    int n = (count + 7) / 8;
    switch (count % 8) {
    case 0: do { *to++ = *from++;
    case 7:      *to++ = *from++;
    case 6:      *to++ = *from++;
    case 5:      *to++ = *from++;
    case 4:      *to++ = *from++;
    case 3:      *to++ = *from++;
    case 2:      *to++ = *from++;
    case 1:      *to++ = *from++;
            } while (--n > 0);
    }
}
int main(void) {
    const char src[] = "ABCDEFGHIJKLMNOPQRSTU";   /* 21 자 */
    char dst[32] = {0};
    send(src, dst, 21);
    printf("복사 결과 : %s\n", dst);
    printf("길이      : %zu\n", sizeof src - 1);
    return 0;
}
```

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
[gcc -Wall -Wextra                  ]   7 건 exit=0
[gcc -Wall -Wextra -pedantic        ]   7 건 exit=0
[gcc -Wall -Wextra -Wimplicit-fallthrough=5] 7 건 exit=0
[clang -Wall -Wextra                ] ★ 0 건 exit=0
[clang -Wimplicit-fallthrough       ]   7 건 exit=0
```

```text
   count = 21,  21 % 8 = 5,  n = (21+7)/8 = 3

   switch (5) 가 ★ do 루프 "안쪽" 의 case 5 로 뛴다.
   +-------------------------------------------------+
   | case 0:  do {  X                                |  <- 첫 바퀴는 여기서 시작 안 함
   | case 7:        X                                |
   | case 6:        X                                |
   | case 5:        O  <- ★ 여기로 뛰어든다           |
   | case 4:        O                                |
   | case 3:        O                                |
   | case 2:        O                                |
   | case 1:        O                                |
   |          } while (--n > 0);                     |  <- 2·3 바퀴는 위부터 8개씩
   +-------------------------------------------------+
     첫 바퀴 5개 + 둘째 8개 + 셋째 8개 = ★ 21개

   ★ case 라벨이 do 블록 "안" 에 있는데도 switch 가 거기로 뛴다.
     switch 가 블록을 고르는 것이었다면 이 코드는 성립하지 않는다.
```

그림 해설 (한 단계씩):

- **21자가 정확히 복사됐다.** 코드가 실제로 동작한다.
- ★★ **`case 5:` 는 `do { … } while` 블록 **안쪽**에 있다.** 그런데 `switch` 가 거기로 **곧장 뛴다.**\
  **`switch` 는 「어느 블록을 실행할까」를 고르는 것이 아니라 「어느 주소로 뛸까」를 고르는 것**이기 때문이다.
- ★ **`case` 는 문이 아니라 라벨**이다 — `goto` 의 `out:` 과 같은 종류다. 그래서 **어느 문 앞에나 붙을 수 있다.**
- **경고는 7건**이고 전부 fall-through 다 — **의도한 fall-through 이므로 그것이 정상**이다.\
  ★ **`-Wall` 에는 없고 `-Wextra` 에 있다**(clang 은 둘 다에 없다 — 아래 (5)).

비용 — **읽기가 나쁘다.** 오늘 이 코드를 쓸 이유는 거의 없고, **이해의 도구**로 남는다.

### (5) fall-through 와 경고 — gcc 와 clang 이 **같은 이름으로 다른 일**을 한다

**언제 쓰나** — `break` 를 빠뜨렸는지 빌드가 잡아 주길 바랄 때.

```text
===== 소스: ex.c (12-f) =====
#include <stdio.h>
static void run(int x) {
    printf("x=%d : ", x);
    switch (x) {
    case 1:
        printf("one ");
    case 2:
        printf("two ");
        break;
    case 3:
        printf("three ");
        /* fall through */
    case 4:
        printf("four ");
        break;
    default:
        printf("other ");
    }
    printf("\n");
}
int main(void) {
    for (int i = 1; i <= 5; i++) run(i);
    return 0;
}
```

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
[gcc -Wimplicit-fallthrough      ]   1 건 exit=0
[gcc -Wimplicit-fallthrough=1    ]   1 건 exit=0
[gcc -Wimplicit-fallthrough=2    ]   1 건 exit=0
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

```text
   같은 소스의 두 fall-through

   ① case 1 -> case 2 : 주석 없음        (실수로 보이는 것)
   ② case 3 -> case 4 : /* fall through */ 주석 있음

   gcc  기본(=3) : ①만 잡는다 (1건)   <- ★ 주석을 읽어 준다
   gcc  =5       : ①②를 다 잡는다 (2건) <- ★ 주석을 안 봐준다. 속성을 요구한다
   clang         : ①②를 다 잡는다 (2건) <- ★ 주석 자체를 안 읽는다
                   단 ★ -Wall 에도 -Wextra 에도 없다 — 직접 켜야 한다
```

그림 해설 (한 단계씩):

- **`x=1` 이 `one two` 를 찍는다** — `break` 가 없어 다음 `case` 로 흘렀다. **의도했든 안 했든 같은 일이 일어난다.**
- ★ **gcc 의 `-Wimplicit-fallthrough` 는 `-Wextra` 에 있다**(`-Wall` 단독 0건). [11번 형제](../11-bitwise-operations-and-shifts/)의 `-Wsign-compare` 와 같은 자리다.
- ★★ **gcc 는 `/* fall through */` 주석을 읽어 준다.** 기본 레벨 3 에서 ② 를 봐주고 **레벨 5 에서는 안 봐준다.**
- ★★ **clang 은 `-Wall -Wextra` 에 이 검사가 없다.** 직접 켜야 하고, 켜면 **주석은 안 읽고 2건을 낸다.**\
  **같은 플래그 이름인데 기본 소속도 판정 기준도 다르다.**
- **clang 은 고치는 법을 두 줄로 제안한다** — `__attribute__((fallthrough));` 또는 `break;`.

비용 — 없다. 다만 「**`-Wall` 만 켜면 fall-through 를 못 잡는다**」는 것을 알아야 한다.

### (6) `[[fallthrough]]`(C23) — 그리고 `-std=` 가 강제가 아니라는 증거

**언제 쓰나** — 의도한 fall-through 를 **주석이 아니라 코드로** 적고 싶을 때.

```text
===== 소스: ex.c (12-g) =====
#include <stdio.h>
static void run(int x) {
    switch (x) {
    case 1:
        printf("one ");
        [[fallthrough]];
    case 2:
        printf("two ");
        break;
    default:
        printf("other ");
    }
    printf("\n");
}
int main(void) { run(1); run(2); run(3); return 0; }
```

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
===== gcc -std=c17 -Wall -Wextra -pedantic 이 하는 말 =====
ex.c: In function ‘run’:
ex.c:6:9: warning: ISO C does not support ‘[[]]’ attributes before C2X [-Wpedantic]
    6 |         [[fallthrough]];
      |         ^

===== clang -std=c17 -Wall -Wextra -pedantic =====
ex.c:6:9: warning: [[]] attributes are a C23 extension [-Wc23-extensions]
    6 |         [[fallthrough]];
      |         ^
1 warning generated.

===== gcc -std=c2x 실행 · clang -std=c23 실행 (같다) =====
one two 
two 
other 
```

그림 해설 (한 단계씩):

- ★★★ **C23 문법이 `-std=c89` 에서 경고 0건으로 통과한다.** `-std=` 는 **강제가 아니라 기본값 선택**이다.\
  **표준 준수를 주장하려면 `-pedantic` 이 필요하다** — 켜면 c89·c99·c17 전부 1건이 된다.
- ★ **`[[fallthrough]]` 는 `-Wimplicit-fallthrough=5` 를 조용히 시킨다** — `-std=c89` 에서도 그렇다.\
  **경고 억제는 표준 준수와 별개로 동작한다.**
- **gcc 13 은 `-std=c2x`**, clang 18 은 `-std=c23` 을 받는다([11번 형제](../11-bitwise-operations-and-shifts/)에서 `-std=c23` 이 gcc 에서 `exit=1` 인 것을 실측했다).
- **진단 문구도 다르다** — gcc 「ISO C does not support `[[]]` attributes before C2X」 / clang 「`[[]]` attributes are a C23 extension」.
- ★ **C23 이전의 이식 가능한 표기는 `__attribute__((fallthrough));`** 이고 gcc·clang 둘 다 받는다(clang 이 직접 제안한다).

비용 — `-pedantic` 한 개.

### (7) `switch` 안에서 선언하면 — **경고와 에러가 갈린다**

**언제 쓰나** — `case` 안에서 지역 변수를 만들 때.

```text
===== 소스: ex.c (12-h) =====
#include <stdio.h>
int main(void) {
    int x = 2;
    switch (x) {
        int v = 99;            /* 첫 case 앞의 선언 — 실행되지 않는다 */
    case 1:
        printf("case 1: v=%d\n", v);
        break;
    case 2:
        printf("case 2: v=%d\n", v);
        break;
    }
    return 0;
}
```

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

```text
   switch (x) {
       int v = 99;     <- ★ 이 "문" 은 어떤 라벨보다도 앞에 있다
   case 1: ...            switch 는 case 로 ★ 뛰어들므로 이 문을 ★ 지나치지 않고 건너뛴다
   case 2: ...            -> v 는 ★ 선언은 되어 있고 ★ 초기화만 안 됐다
   }

   ★ 에러가 아니다. 경고이고, 읽으면 쓰레기값이 나온다 (32764 / 32765 — 실행마다 다르다)
```

**★ 그런데 VLA 를 선언하면 에러다.**

```text
===== 소스: ex.c (12-i) =====
#include <stdio.h>
int main(void) {
    int m = 4;
    switch (m) {
    case 4:;
        int vla2[m];             /* switch 안에서 VLA 를 만든다 */
        vla2[0] = 2;
        printf("vla2 %d\n", vla2[0]);
        break;
    default: break;
    }
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
ex.c: In function ‘main’:
ex.c:10:5: error: switch jumps into scope of identifier with variably modified type
   10 |     default: break;
      |     ^~~~~~~
ex.c:4:5: note: switch starts here
    4 |     switch (m) {
      |     ^~~~~~
ex.c:7:13: note: ‘vla2’ declared here
exit=1
```

그림 해설 (한 단계씩):

- ★★ **「`switch` 안에서 선언하면 에러」는 절반만 맞다.** 보통 변수는 **경고**이고, 값은 **쓰레기**가 된다.\
  실측에서 `32764`·`32765` 가 나왔고 **두 컴파일러가 서로 다른 값**을 냈다 — 스택에 남아 있던 값이다.
- **초기화가 실행되지 않은 것**이 전부다. `v` 는 **선언되어 있고**(스코프 안이다) **초기화만 건너뛰어졌다.**
- ★ **에러가 나는 것은 VLA 다.** `switch` 가 **VLA 스코프 안으로 뛰어드는 꼴**이라 (3)의 `goto` 와 **같은 규칙**에 걸린다.\
  gcc 의 문구가 아예 「**switch** jumps into scope …」다.
- ★ **막는 법은 `case` 마다 중괄호를 치는 것**이다 — `case 4: { int vla2[m]; … break; }` 로 쓰면 통과한다.
- ★ **`case` 라벨 바로 뒤의 선언은 C23 부터 합법**이다. C17 까지는 `-pedantic` 이 경고하고\
  **`-pedantic-errors` 를 쓰면 에러**가 된다(아래 (10)의 표).

비용 — 중괄호 두 개. **`case` 몸통에는 언제나 중괄호를 친다**가 규칙이 된다.

### (8) 제어식은 정수 승격을 받고, `case` 는 **정수 상수식**이어야 한다

**언제 쓰나** — `char`·열거형을 `switch` 할 때, 그리고 `case` 에 상수를 쓸 때.

```text
===== 소스: ex.c (12-j) =====
#include <stdio.h>
#include <limits.h>
int main(void) {
    char c = (char)200;                 /* 구현 정의: 여기서는 -56 */
    printf("c = %d  (CHAR_MIN=%d)\n", c, CHAR_MIN);
    switch (c) {
    case 200:  printf("case 200 에 걸렸다\n"); break;
    case -56:  printf("case -56 에 걸렸다\n"); break;
    default:   printf("default\n"); break;
    }
    unsigned char u = 200;
    switch (u) {                        /* unsigned char 도 int 로 승격 */
    case 200: printf("unsigned char 200 은 case 200 에 걸린다\n"); break;
    default:  printf("default\n"); break;
    }
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘main’:
ex.c:7:5: warning: case label value exceeds maximum value for type [-Wswitch-outside-range]
    7 |     case 200:  printf("case 200 에 걸렸다\n"); break;
      |     ^~~~
c = -56  (CHAR_MIN=-128)
case -56 에 걸렸다
unsigned char 200 은 case 200 에 걸린다
```

```text
===== clang -std=c17 -Wall -Wextra (exit=0) =====
ex.c:7:10: warning: overflow converting case value to switch condition type (200 to -56) [-Wswitch]
    7 |     case 200:  printf("case 200 에 걸렸다\n"); break;
      |          ^
1 warning generated.
```

**`case` 에 무엇을 쓸 수 있나**

```text
===== 되는 것 (ex.c 12-k, gcc·clang exit=0) =====
enum Color { RED = 1, GREEN = 2 };
#define K 3
case RED:            /* 열거 상수 */
case K:              /* 매크로가 펼쳐진 상수 */
case 1 + 1:          /* 상수식 */
case sizeof(int):    /* 4 — 컴파일 시간에 정해진다 */

===== 안 되는 것 (ex.c 12-l) =====
const int K = 3;
case K:
  gcc   : error: case label does not reduce to an integer constant      exit=1
  clang : warning: expression is not an integer constant expression;
          folding it to a constant is a GNU extension [-Wgnu-folding-constant]
          ★ 컴파일되고 실행된다 (exit=0)
          단 -pedantic-errors 를 주면 error 가 된다

===== 제어식이 정수가 아니면 =====
double d = 1.0; switch (d) { case 1: ... }
  gcc   : error: switch quantity not an integer                          exit=1
  clang : error: statement requires expression of integer type ('double' invalid)

===== 중복 case =====
case 'A': ... case 65: ...
  gcc   : error: duplicate case value / note: previously used here       exit=1
```

```text
   switch (c)    c 는 char (여기서는 부호 있음, -128 ~ 127)
       ↓ ★ 제어식이 정수 승격을 받는다 (03번)
   switch ((int)c)   -> -56

   case 200  은 int 상수 200 이다.
   ★ 승격된 char 가 200 이 되는 일은 없다 -> ★ 영원히 안 걸린다
      gcc 가 -Wswitch-outside-range 로 말해 준다.

   unsigned char u = 200 -> 승격하면 200 (0~255 가 전부 int 에 들어간다)
   -> ★ case 200 에 걸린다. 같은 "200" 인데 타입이 답을 바꾼다.
```

그림 해설 (한 단계씩):

- **`char c = (char)200` 이 `-56`** 이다 — **plain `char` 의 부호는 구현 정의**이고 여기서는 부호 있는 것이다([02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)).
- ★ **제어식이 정수 승격을 받는다.** 그래서 `case 200` 이 **도달 불가**가 되고, gcc 가 `-Wswitch-outside-range` 로 말해 준다.\
  ★ **clang 도 잡되 이름과 문구가 다르다** — `-Wswitch` 의 「overflow converting case value to switch condition type (200 to -56)」로,\
  **변환된 값 `-56` 까지 찍어 준다**(gcc 는 안 찍는다).
- **`unsigned char` 는 같은 200 이 `case 200` 에 걸린다.** **타입 하나가 답을 바꾼다.**
- ★★ **`case` 는 정수 상수식이어야 한다.** 열거 상수·매크로·`1+1`·`sizeof(int)` 는 되고 **`const int` 는 안 된다.**\
  ★ **gcc 는 에러, clang 은 GNU 확장으로 받아 준다**(`-Wgnu-folding-constant`) — **같은 소스가 한쪽에서만 빌드된다.**
- **중복 `case` 도 에러**다 — `'A'` 와 `65` 는 같은 값이므로 둘을 같이 쓸 수 없다.

비용 — 없다. **`case` 에 쓸 상수는 `enum` 이나 `#define` 으로 만든다**([07번 형제](../07-enum-and-enumeration-constants/)).

### (9) `for (;;)` 과 `while (1)` — 어셈블리로 확인

**언제 쓰나** — 「어느 쪽이 빠른가」라는 질문을 받았을 때.

```text
===== 소스: ex.c (12-m) =====
extern void tick(void);
void loop_for(void)   { for (;;)     tick(); }
void loop_while(void) { while (1)    tick(); }
void loop_do(void)    { do { tick(); } while (1); }
```

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
===== gcc -std=c17 -O2 -c · objdump -d (같은 것을 기계어로) =====
0000000000000000 <loop_for>:        0000000000000020 <loop_while>:      0000000000000040 <loop_do>:
   0:	endbr64                      20:	endbr64                      40:	endbr64
   4:	push   %rax                  24:	push   %rax                  44:	push   %rax
   5:	pop    %rax                  25:	pop    %rax                  45:	pop    %rax
   6:	sub    $0x8,%rsp             26:	sub    $0x8,%rsp             46:	sub    $0x8,%rsp
   a:	nopw   0x0(%rax,%rax,1)      2a:	nopw   0x0(%rax,%rax,1)      4a:	nopw   0x0(%rax,%rax,1)
  10:	call   15 <loop_for+0x15>    30:	call   35 <loop_while+0x15>  50:	call   55 <loop_do+0x15>
  15:	jmp    10 <loop_for+0x10>    35:	jmp    30 <loop_while+0x10>  55:	jmp    50 <loop_do+0x10>

===== gcc -std=c17 -O0 -c · objdump -d =====
0000000000000000 <loop_for>:        000000000000000f <loop_while>:      000000000000001e <loop_do>:
   0:	endbr64                       f:	endbr64                      1e:	endbr64
   4:	push   %rbp                  13:	push   %rbp                  22:	push   %rbp
   5:	mov    %rsp,%rbp             14:	mov    %rsp,%rbp             23:	mov    %rsp,%rbp
   8:	call   d <loop_for+0xd>      17:	call   1c <loop_while+0xd>   26:	call   2b <loop_do+0xd>
   d:	jmp    8 <loop_for+0x8>      1c:	jmp    17 <loop_while+0x8>   2b:	jmp    26 <loop_do+0x8>

(경고 0 건)
```

그림 해설 (한 단계씩):

- ★ **세 함수의 명령 열이 완전히 같다.** `-O2` 에서도 **`-O0` 에서도** 같다 —\
  **`-O0` 에서까지 같다는 것이 더 강한 근거다.** 최적화가 지워 준 것이 아니라 **처음부터 같은 것**이다.
- **`while (1)` 의 조건 비교가 어디에도 없다.** `cmp` 명령이 한 개도 안 나온다.
- ★ **이것은 도식이 아니라 도구의 출력**이다 — 지어낼 수 없고 독자가 자기 머신에서 재현한다.
- **셋 중 무엇을 쓸지는 취향이다.** `for (;;)` 는 **조건이 없다는 것을 형태로 말해 주고**, `while (1)` 은 **읽기 쉽다.**

비용 — 없다. **성능 이야기가 아니라 가독성 이야기다.**

### (10) 이 주제의 진단을 한 표로 — 경고인가 에러인가

**언제 쓰나** — 빌드 플래그를 정할 때.

```text
gcc 플래그별 (각 프로그램마다)
                            -Wall  -Wextra  -Wall -Wextra  +pedantic  -pedantic-errors
(12-a) dangling else          1건    ★ 0건       1건          1건          1건
(12-f) fall-through         ★ 0건      1건       1건          1건          1건
(12-e) Duff (7 곳)          ★ 0건      7건       7건          7건          7건
(12-h) switch 앞 선언          2건      2건       2건          2건          2건
(12-j) case 도달 불가          1건      1건       1건          1건          1건
라벨 뒤 선언 (C17)           ★ 0건    ★ 0건     ★ 0건          1건       ★ error (exit=1)

★ -Wall 에만 있는 것 : -Wdangling-else · -Wswitch-unreachable · -Wuninitialized
★ -Wextra 에만 있는 것 : -Wimplicit-fallthrough
★ -pedantic 에만 보이는 것 : 라벨 뒤 선언(C17) · [[]] 속성(C17)
```

```text
컴파일이 ★ 실패하는 넷 (exit=1)
  ① goto 가 VLA 스코프 안으로            (12-d)
  ② switch 가 VLA 스코프 안으로          (12-i)
  ③ case 에 const int                   (12-l)  ★ gcc 만. clang 은 경고 후 실행됨
  ④ switch 제어식이 double · 중복 case   (12-l)
```

그림 해설 (한 단계씩):

- ★★ **`-Wall` 과 `-Wextra` 가 서로 다른 함정을 잡는다.** 하나만 켜면 이 주제의 절반을 놓친다.
- ★ **`-pedantic` 이 없으면 안 보이는 것이 둘** 있고, **`-pedantic-errors` 는 그중 하나를 에러로 바꾼다.**
- ★★ **③ 이 가장 위험하다** — **gcc 에서는 빌드가 안 되는 코드가 clang 에서는 돌아간다.**\
  「내 기계에서는 된다」가 **컴파일러 차이로** 생기는 자리다.
- ★ **이 주제에는 sanitizer 가 등장하지 않는다.** UB 가 거의 없어 **런타임에 볼 것이 없다**(아래 층 표).

비용 — 플래그 세 개(`-Wall -Wextra -pedantic`). **둘만 켜면 반만 본다.**

## 문법 — 형태와 규칙

### 형태 — 여섯 제어문

```c
/* ===== 분기 ===== */
if (cond) { } else if (cond2) { } else { }
switch (expr) {                /* ★ expr 은 정수 승격을 받는다 */
case 1:  ... break;            /* ★ case 는 정수 상수식 */
case 2:  ... /* fall through */
case 3:  ... [[fallthrough]];  /* C23. 그 전에는 __attribute__((fallthrough)); */
default: ... break;            /* ★ 위치는 어디든 좋다 */
}

/* ===== 반복 ===== */
while (cond)        { }        /* 먼저 검사 */
do { } while (cond);           /* ★ 한 번은 무조건 실행 · 끝에 세미콜론 */
for (init; cond; step) { }     /* 세 칸 각각 비울 수 있다 */
for (;;) { }                   /* 무한 — while (1) 과 기계어가 같다 */

/* ===== 점프 ===== */
break;                         /* ★ 가장 안쪽 switch 또는 루프 하나 */
continue;                      /* ★ for 는 step 으로, while/do 는 cond 로 */
goto label;  label: ;          /* 같은 함수 안에서만 */
return v;
```

### 금지 사례 — 어느 것이 무슨 층인가

```c
/* (1) goto 가 VLA 스코프 안으로 -> ★ 컴파일 에러 */
if (x) goto skip;
int vla[n];
skip: ;

/* (2) switch 가 VLA 스코프 안으로 -> ★ 컴파일 에러 */
switch (m) { case 4:; int vla2[m]; break; default: break; }

/* (3) case 에 const int -> ★ gcc 에러 / clang 은 GNU 확장 경고 */
const int K = 3;
switch (x) { case K: break; }

/* (4) 제어식이 정수가 아님 · 중복 case -> ★ 컴파일 에러 */
switch (1.0) { case 1: break; }
switch (c)   { case 'A': break; case 65: break; }

/* (5) 첫 case 앞의 선언 -> ★ 경고 (에러 아님). 초기화가 실행되지 않는다 */
switch (x) { int v = 99; case 1: use(v); break; }

/* (6) 중괄호 없는 중첩 if -> ★ 정의된 동작이되 사람이 틀린다 */
if (a) if (b) f(); else g();          /* else 는 안쪽 if 의 것 */

/* (7) 루프를 나가려고 switch 안에서 break -> ★ 정의된 동작이되 뜻이 다르다 */
for (...) { switch (x) { case 1: break; } }   /* 루프는 계속 돈다 */

/* (8) 안전한 형태 */
switch (x) { case 4: { int vla2[m]; break; } default: break; }
```

- (1)\~(4)는 **컴파일러가 막아 준다.** 이 주제에서 **가장 강한 근거가 에러 메시지**다.
- (5)\~(7)은 **막아 주지 않는다** — 경고이거나 **정의된 동작이되 뜻이 다른 것**이다.

### 규칙 불릿

- **`else` 는 가장 가까운 짝 없는 `if` 에 붙는다.** 들여쓰기는 아무 뜻이 없다.
- ★ **`case`·`default` 는 문이 아니라 라벨**이다 — `switch` 몸통 **어느 문 앞에나**, **중첩 블록 안에도** 붙을 수 있다.\
  그래서 **Duff's device 가 합법**이다.
- **`switch` 는 매치되는 라벨로 뛴다.** 뛴 뒤에는 **`break` 나 몸통 끝까지 계속 실행**된다(fall-through).
- ★ **제어식은 정수 승격을 받는다**([03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)). 부동소수는 **에러**다.
- ★ **`case` 라벨은 정수 상수식**이어야 한다 — 열거 상수·매크로·`sizeof`·상수식은 되고 **`const int` 변수는 안 된다**(gcc 기준).
- **`case` 값이 중복되면 에러**다. **`default` 의 위치는 자유**다.
- **`break` 는 가장 안쪽 `switch` 또는 루프 하나**만 끝낸다. 여러 겹을 나가려면 **깃발이나 `goto`** 를 쓴다.
- ★ **`continue` 는 `for` 에서 증가 칸으로, `while`·`do` 에서 조건으로** 간다.
- **`goto` 는 같은 함수 안에서만** 뛴다. ★ **VLA 스코프 안으로는 못 뛴다 — 에러다.**
- **첫 `case` 앞의 선언은 실행되지 않는다.** 선언은 되고 **초기화만 건너뛴다.**
- **C23 부터 라벨 뒤 선언이 합법**이고 **`[[fallthrough]]`** 를 쓸 수 있다.

## 어디서 틀리나

### 1. ★★ 「루프를 나가려고 `switch` 안에서 `break` 를 쓴다」

```text
   for (...) { switch (x) { case 1: break; } }   -> ★ 루프는 계속 돈다
```

- **`break` 는 가장 안쪽 하나**만 끝낸다. 실측에서 `| ` 가 네 번 다 찍혔다.
- **경고가 없다** — 정의된 동작이고 문법도 맞다. **사람만 틀린다.**
- 막는 법: **깃발 변수**나 **`goto done;`**.

### 2. ★ 「중괄호는 한 줄이면 생략해도 된다」

- `else` 가 **안쪽 `if`** 에 붙어 출력이 통째로 사라졌다.
- `-Wall` 의 **`-Wdangling-else`** 가 잡아 주지만 **`-Wextra` 단독으로는 0건**이다.
- 막는 법: **언제나 중괄호.**

### 3. ★★ 「`-Wall` 이면 `break` 빠뜨린 것을 잡아 주겠지」

```text
   gcc   -Wall         -> ★ 0 건
   gcc   -Wextra       ->   1 건
   clang -Wall -Wextra -> ★ 0 건   (직접 켜야 한다)
```

- **gcc 는 `-Wextra`**, **clang 은 어디에도 없다.** 같은 이름의 플래그가 **기본 소속이 다르다.**
- gcc 는 `/* fall through */` **주석을 읽어 주고** clang 은 **안 읽는다.**
- 막는 법: **`-Wextra`(gcc)·`-Wimplicit-fallthrough`(clang)를 명시**하고, 의도한 자리는 **`[[fallthrough]]`** 로 적는다.

### 4. 「`case` 안에서 변수를 선언한다」

- 첫 `case` **앞**에 두면 **초기화가 실행되지 않는다**(실측 `32764`·`32765` — 실행마다 다르다).
- **VLA 면 아예 에러**다.
- 막는 법: **`case` 몸통에 중괄호**를 친다.

### 5. ★ 「`case` 에 `const int` 를 쓴다」

- **gcc 는 에러**(`exit=1`), **clang 은 경고 후 실행**된다. **같은 소스가 한쪽에서만 빌드된다.**
- 막는 법: **`enum` 이나 `#define`** 으로 만든다([07번 형제](../07-enum-and-enumeration-constants/)).

### 6. 「`char` 를 `switch` 하며 `case 200` 을 쓴다」

- 제어식이 **`int` 로 승격**되고 `char` 는 여기서 **부호 있는 타입**이라 `200` 이 될 수 없다.
- gcc 가 **`-Wswitch-outside-range`** 로 「case label value exceeds maximum value for type」이라 말하고,\
  clang 은 **`-Wswitch`** 로 「overflow converting case value to switch condition type (200 to -56)」이라 말한다.
- 막는 법: **`unsigned char` 로 받거나** `case` 값을 실제 범위로 쓴다.

### 7. ★ 「`-std=c17` 로 돌렸으니 C17 코드다」

- **C23 의 `[[fallthrough]]` 가 `-std=c89` 에서 경고 0건으로 통과했다.**
- 막는 법: **`-pedantic`** 을 켠다. 표준 위반을 빌드 실패로 만들려면 **`-pedantic-errors`**.

## 구현 세부사항 대 언어 보장

C 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★ **이 주제는 「표준」 칸이 압도적으로 두껍고 UB 칸이 거의 비어 있다.**\
[11번 형제](../11-bitwise-operations-and-shifts/)가 **UB 가 본체**, [10번 형제](../10-evaluation-order-and-sequence-points/)가 **미명시가 본체**였던 것과 정반대다 —\
★ **제어문에서 틀리면 대개 빌드가 안 되거나, 되더라도 「정의된 동작으로 내 뜻과 다르게」 돈다.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | dangling else 의 결합 · fall-through · **`case` 가 라벨이라 블록 안에도 놓이는 것**(Duff) · `break`/`continue` 가 가는 곳 · `default` 위치 자유 · **제어식의 정수 승격** · **첫 `case` 앞 선언이 실행되지 않는 것** · `for(;;)` ≡ `while(1)` | 출력 대조 · **gcc·clang 이 바이트 단위로 같은 출력** · `-O0`/`-O2` 어셈블리 | ★★ **`break` 가 `switch` 만 끝내는 것** — 경고 0건, 정의된 동작. **아무 도구도 안 잡는다** |
| **조건부 표준** | 매크로가 정의될 때만 | **해당 없음** — 이 주제에 조건부 보장은 없다 | — | — |
| **구현 정의** | 문서화 의무가 있다 | ★ plain **`char` 의 부호**(`(char)200` 이 `-56`) — 제어식 승격 결과를 바꾼다 · `switch` 를 **점프 테이블로 컴파일할지** | `CHAR_MIN=-128` 출력 · `-S` 로 점프 테이블 확인 | ★ **어느 쪽이든 동작은 같다** — 성능만 다르다 |
| **미명시** | 몇 가지 중 하나 | ★ **해당 없음** — 제어 흐름에는 미명시가 없다. 단 **제어식 안에 부작용을 둘 넣으면** 그 순서가 미명시다([10번 형제](../10-evaluation-order-and-sequence-points/)) | (10번에서 확인) | — |
| **UB** | 아무 일이나 | ★ **거의 없다** — 이 주제의 오용은 대개 **컴파일 에러**로 막힌다. **초기화 안 된 변수를 읽는 것**(첫 `case` 앞 선언)이 이 주제가 닿는 유일한 자리다 | `-Wuninitialized` 2건 · 값이 `32764`/`32765` 로 실행마다 다름 | ★ **읽은 값 자체는 아무 말도 안 한다** — 쓰레기값이 그럴듯하면 그냥 지나간다 |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | gcc `-Wall` | gcc `-Wextra` | `+pedantic` | clang `-Wall -Wextra` | 무엇이 잡나 |
|---|---|---|---|---|---|---|
| dangling else | 표준 | **1건** | 0건 | 1건 | **1건** | `-Wall` |
| fall-through(주석 없음) | 표준 | **0건** | **1건** | 1건 | **0건** | ★ gcc `-Wextra` · clang 은 **직접 켜야** |
| fall-through(주석 있음) | 표준 | 0건 | 0건 | 0건 | **0건** | ★ gcc `=5` 또는 clang `-Wimplicit-fallthrough` |
| 첫 `case` 앞 선언 | 표준 + UB(읽기) | **2건** | 2건 | 2건 | **1건** | `-Wswitch-unreachable`·`-Wuninitialized` |
| `case` 도달 불가(`char`) | 표준 | **1건** | 1건 | 1건 | **1건**(`-Wswitch`) | ★ **양쪽 다 잡되 플래그 이름과 문구가 다르다** |
| 라벨 뒤 선언(C17) | 표준 위반 | **0건** | 0건 | **1건** | **1건**(`-Wc23-extensions`) | ★ `-pedantic` 뿐 |
| `[[fallthrough]]`(C17) | 표준 위반 | **0건** | 0건 | **1건** | **1건** | ★ `-pedantic` 뿐 |
| ★ `break` 가 루프를 안 끝냄 | 표준 | **0건** | **0건** | **0건** | **0건** | ★★ **아무도 안 잡는다** |
| `goto`·`switch` → VLA 스코프 | — | **error** | error | error | **error** | 컴파일러가 막는다 |
| `case` 에 `const int` | — | **error** | error | error | ★ **경고 후 실행** | ★ **컴파일러마다 다르다** |

- ★★ **이 표의 결론 세 줄**
  - **`-Wall` 과 `-Wextra` 가 서로 다른 함정을 잡는다.** 둘 다 켜야 이 주제를 덮는다.
  - **`-pedantic` 없이는 「C23 문법이 C89 로 통과」를 못 본다.**
  - ★ **`break` 가 루프를 안 끝내는 것은 어떤 도구도 안 잡는다** — **정의된 동작**이기 때문이다.\
    [10번 형제](../10-evaluation-order-and-sequence-points/)의 미명시·[11번 형제](../11-bitwise-operations-and-shifts/)의 구현 정의와 **같은 성격의 사각지대**다: **「틀린 것」이 아니라 「내 뜻이 아닌 것」이다.**

### 이 주제에 sanitizer 가 거의 등장하지 않는 이유

- **제어문 자체에는 UB 가 없다.** `switch` 가 어디로 뛰든, fall-through 가 나든 **전부 정의된 동작**이다.
- 그래서 **검사가 컴파일 타임에 몰려 있고**, 이 문서에서 **UBSan 을 돌린 것은 (3)의 `goto` 정리 코드 한 번**이다(진단 0줄).
- ★ **유일한 런타임 위험은** 「**초기화 안 된 변수를 읽는 것**」이고, 그것은 **이 주제가 아니라 그 변수의 문제**다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 값으로 갈래 고르기 | `switch` + 각 `case` 에 `break` | `break` 를 빠뜨린 채 두기 |
| 의도한 fall-through | `[[fallthrough]];`(C23) 또는 `__attribute__((fallthrough));` | `/* fall through */` 주석만(clang 이 안 읽는다) |
| `case` 몸통에 지역 변수 | `case 1: { int v = 0; … break; }` | `switch (x) { int v = 0; case 1: … }` |
| `case` 상수 | `enum` 또는 `#define` | `const int` |
| 루프 탈출 | 깃발 변수 또는 `goto done;` | `switch` 안의 `break` |
| 여러 단계 자원 정리 | `goto out;` 한 곳으로 모으기 | 매 분기마다 `free` 를 복사 |
| 무한 루프 | `for (;;)` 또는 `while (1)`(기계어가 같다) | 어느 쪽이 빠른지 고민하기 |
| 중첩 `if` | 언제나 중괄호 | 들여쓰기로 짝을 표시 |
| 한 번은 꼭 실행 | `do { … } while (cond);` | `while` 앞에 몸통을 복사 |
| `char` 를 `switch` | `unsigned char` 로 받거나 실제 범위의 `case` | `case 200` 을 plain `char` 에 |

판단 규칙 두 줄.

- **`switch` 는 블록이 아니라 점프다.** `break` 와 중괄호를 **명시적으로** 쓴다.
- **`-Wall -Wextra -pedantic` 셋을 다 켠다.** 셋이 **서로 다른 함정**을 잡는다.

## 핵심 문장

- ★★ **`case` 는 문이 아니라 라벨**이다 — `goto` 의 라벨과 같은 종류이고, **중첩 블록 안에도** 붙는다.\
  **Duff's device 가 합법인 것**이 그 증거이고, 실측에서 **21자를 정확히 복사**했다.
- ★ **`switch` 는** 「**고르는 것**」이 아니라 「**뛰는 것**」이다. 뛴 뒤에는 **`break` 를 만날 때까지 계속 걷는다.**
- ★★ **`break` 는 가장 안쪽 `switch` 또는 루프 하나만 끝낸다.** 루프 안의 `switch` 에서 `break` 는 **루프를 안 끝내고**,\
  ★ **어떤 도구도 이것을 말해 주지 않는다** — 정의된 동작이기 때문이다.
- **`else` 는 가장 가까운 `if` 에 붙는다.** `-Wall` 의 `-Wdangling-else` 가 잡고 **`-Wextra` 단독은 0건**이다.
- ★★ **fall-through 경고는 gcc `-Wextra`, clang 은 어디에도 없다.** gcc 는 `/* fall through */` **주석을 읽어 주고**(기본 레벨 3)\
  **레벨 5 와 clang 은 안 읽는다.**
- ★★★ **C23 의 `[[fallthrough]]` 가 `-std=c89` 에서 경고 0건으로 통과했다.** **`-std=` 는 강제가 아니라 기본값 선택**이고,\
  표준 준수를 주장하려면 **`-pedantic`** 이 필요하다.
- ★ **`goto`·`switch` 가 VLA 스코프 안으로 뛰면 컴파일 에러**다(`exit=1`). **경고가 아니다.**
- ★ **첫 `case` 앞의 선언은 실행되지 않는다** — 선언은 되고 **초기화만 건너뛴다.** 실측 값이 `32764`·`32765` 였다.
- ★★ **`case` 에 `const int` 를 쓰면 gcc 는 에러, clang 은 경고 후 실행**된다. **같은 소스가 한쪽에서만 빌드된다.**
- ★ **제어식은 정수 승격을 받는다** — plain `char` 에 `case 200` 은 **영원히 안 걸린다**(gcc 가 말해 준다).
- ★ **`for (;;)` 과 `while (1)` 은 `-O0` 에서도 기계어가 같다.** 성능 이야기가 아니라 가독성 이야기다.

## 관련 자료

- [`../README.md`](../README.md) — C 문법·API 주제 목록(이 주제는 12번)
- [`07-enum-and-enumeration-constants/`](../07-enum-and-enumeration-constants/) — ★ **`case` 라벨에 쓰는 열거 상수의 정본.** 그쪽은 「열거 상수가 무엇인가」, 여기는 **「`switch` 가 그것을 어떻게 쓰나」**
- [`03-integer-promotion-and-usual-arithmetic-conversions/`](../03-integer-promotion-and-usual-arithmetic-conversions/) — **제어식이 받는 정수 승격의 정본.** `case 200` 이 도달 불가가 되는 이유가 거기 있다
- [`02-basic-types-sizes-and-fixed-width-integers/`](../02-basic-types-sizes-and-fixed-width-integers/) — plain `char` 의 **부호가 구현 정의**인 것. `(char)200` 이 `-56` 인 근거
- [`09-operator-precedence-and-associativity/`](../09-operator-precedence-and-associativity/) — `? :` 가 **오른쪽 결합**인 것 · `?:` 대 `if` 의 자리
- [`10-evaluation-order-and-sequence-points/`](../10-evaluation-order-and-sequence-points/) — ★★ **`&&`·`\|\|`·`?:` 가 시퀀스 포인트인 것과 단락 평가의 정본.** 여기는 **그것들이 만드는** 「**흐름**」까지
- [`11-bitwise-operations-and-shifts/`](../11-bitwise-operations-and-shifts/) — **UB 가 본체인 주제.** 이 주제와 **다섯 층의 두께가 정반대**다 — 거기는 UBSan 이 말하고 여기는 컴파일러가 막는다
- 목록의 **13번 주제** (함수 정의와 선언) — `return` 과 함수 경계. `goto` 가 **함수를 넘지 못하는** 이유
- 목록의 **42번 주제** (함수형 매크로의 함정) — `if (x) MACRO(); else …` 가 깨지는 자리. **`do { } while (0)` 관용구**의 정본
- 목록의 **58번 주제** (UB 를 잡는 도구) — 이 주제에서 sanitizer 가 할 일이 거의 없는 이유

## 용어 풀이

- **라벨(label)** — 문 앞에 붙이는 이름. `case 3:`·`default:`·`out:` 이 전부 라벨이다.
- **fall-through** — `break` 가 없어 다음 `case` 로 흘러드는 것. 예: `case 1: A(); case 2: B();` 에서 `x==1` 이면 둘 다 실행된다.
- **dangling else** — 중괄호 없는 중첩 `if` 에서 `else` 의 짝이 애매해 보이는 것. 규칙은 「**가장 가까운** `if`」로 정해져 있다.
- **Duff's device** — `do`\~`while` 루프의 **안쪽**에 `case` 라벨을 박아 루프를 펼친 관용구. `switch` 가 **점프**라는 증거.
- **정수 상수식(integer constant expression)** — 컴파일 시간에 값이 정해지는 정수 식. `case` 라벨·배열 크기에 쓴다. ★ **`const int` 변수는 아니다.**
- **VLA(variable length array)** — 크기가 실행 시간에 정해지는 배열(`int a[n];`). ★ **그 스코프 안으로 뛰어들 수 없다.**
- **`-Wdangling-else`** — 중첩 `if`/`else` 를 경고하는 플래그. **gcc·clang 둘 다 `-Wall` 소속.**
- **`-Wimplicit-fallthrough`** — fall-through 를 경고하는 플래그. ★ **gcc 는 `-Wextra` 소속, clang 은 어디에도 없다.**
- **`-Wswitch-unreachable`** — 첫 `case` 앞의 실행되지 않는 문을 경고. **gcc `-Wall`.**
- **`-Wswitch-outside-range`** — `case` 값이 제어식 타입 범위 밖이라 도달 불가임을 경고. **gcc `-Wall`.**
- **`-pedantic` / `-pedantic-errors`** — 표준이 요구하는 진단을 **내게 하는** / **에러로 만드는** 플래그.
- **`[[fallthrough]]`** — 의도한 fall-through 를 표시하는 **C23 속성**. 그 전에는 `__attribute__((fallthrough));`.

---

## 더 들어가면

- ★ **`switch` 가 점프 테이블로 컴파일되는 것을 볼 수 있다.** `case 0`\~`4` 와 `default` 를 둔 함수를\
  `gcc -O2 -S -masm=intel` 로 찍으면 `cmp edi, 4` / `ja .L2` / `lea rdx, .L4[rip]` / `notrack jmp rax` 와\
  `.L4:` 아래의 `.long .L8-.L4` 같은 **오프셋 표**가 나온다. **점프 테이블로 할지 비교 사슬로 할지는 구현 정의**이고\
  **동작은 어느 쪽이든 같다.** 이 문서는 **한 예에서만** 확인했고 **경계 조건(희소한 `case`·큰 범위)은 던져 보지 않았다.**

- **`do { … } while (0)` 은 매크로의 관용구**다. `if (x) MACRO(); else …` 가 깨지지 않게 **한 문으로 묶는** 장치인데\
  ★ **이 문서에서 매크로를 던져 보지 않았다.** 목록의 **42번 주제**의 몫이다.

- **계산된 `goto`(`goto *ptr;`)는 GNU 확장**이다. 인터프리터 디스패치에 쓰인다.\
  ★ **이 문서에서 던져 보지 않았고**, `-pedantic` 이 무엇이라 하는지도 확인하지 않았다.

- **C23 은 `switch` 자체를 바꾸지 않았다.** 바뀐 것은 **`[[fallthrough]]`** 와 **라벨 뒤 선언 허용** 둘이고\
  둘 다 이 문서에서 실측했다. ★ **C23 의 다른 제어 흐름 변경이 있는지는 전수 확인하지 않았다.**

- **`longjmp`/`setjmp` 는 함수를 넘는 점프**다. `goto` 가 못 하는 것을 하지만 **정리 코드가 안 돌고**,\
  ★ **이 문서에서 던져 보지 않았다.**

- ★ **「`switch` 가 `if` 사슬보다 빠른가」는 이 문서가 재지 않았다.** 어셈블리를 한 번 본 것이 전부이고,\
  **수치를 내려면 측정 조건 선언이 필요하다.** `for(;;)` ↔ `while(1)` 은 **기계어가 같아 잴 것이 없었다.**
