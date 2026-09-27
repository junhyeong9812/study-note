# c/syntax/09 — 연산자 우선순위와 결합성: 무엇이 먼저 **묶이나** — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고·에러는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 플래그는 `-std=c17 -Wall -Wextra -pedantic`. **플래그가 갈리는 답은 그 자리에 밝혔다.**\
> `clang 18.1.3` 을 쓴 자리도 그 자리에 밝혔다.
> ★ **이 주제에는 UB 가 없다.** 그래서 sanitizer 출력이 한 줄도 안 나온다 — 그것도 결과다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 다섯 줄이 각각 무엇을 찍는가 ★★

**출력**

```text
a=6 b=2 c=2 : a & b == c   = 0   |  (a & b) == c = 1
a=6         : a << 1 + 2   = 48   |  (a << 1) + 2 = 14
x=0 y=2     : !x & y       = 0   |  !(x & y)     = 1
d=6 e=3 f=1 : d & e ^ f    = 3   |  d & (e ^ f)  = 2
g=1 h=3 i=1 : g | h ^ i    = 3   |  (g | h) ^ i  = 2
```

**왜 그런가 — 한 줄씩 괄호로 풀어서**

```text
   a & b == c   ->  a & (b == c)  =  6 & (2==2)  =  6 & 1  = ★ 0
   a << 1 + 2   ->  a << (1 + 2)  =  6 << 3                = ★ 48
   !x & y       ->  (!x) & y      =  1 & 2                 = ★ 0
   d & e ^ f    ->  (d & e) ^ f   =  (6&3) ^ 1  =  2 ^ 1   = ★ 3
   g | h ^ i    ->  g | (h ^ i)   =  1 | (3^1)  =  1 | 2   = ★ 3
```

**같은 줄이 있는가**

- **없다. 다섯 줄 전부 왼쪽과 오른쪽이 다르다.** 값을 그렇게 고른 것이다 —\
  값을 잘못 고르면 두 묶음이 우연히 같은 답을 내서 **아무것도 증명하지 못한다**(이 문서를 쓰다가 실제로 한 번 그랬다).

**세 비트 연산자의 순서**

```text
   센 쪽   &    (비트 AND)
           ^    (비트 XOR)
   약한 쪽 |    (비트 OR)

   그 셋 전부가 ==  !=  <  >  보다 약하다.
```

**경고**

```text
[-std=c17] 0 건  exit=0
[-std=c17 -Wall] 5 건  exit=0
[-std=c17 -Wextra] 0 건  exit=0
[-std=c17 -Wall -Wextra] 5 건  exit=0
[-std=c17 -Wparentheses] 5 건  exit=0
[-std=c17 -Wall -Wextra -pedantic] 5 건  exit=0
[-std=c17 -Wall -Wno-parentheses] 0 건  exit=0
[-std=c17 -Wall -Wextra -Wconversion] 5 건  exit=0
```

- **5건이고 전부 `-Wparentheses`** 다. **`-Wall` 에 들어 있고** `-Wextra` 단독은 **0건**이다.
- `-Wno-parentheses` 로 끄면 0건이 된다 — 다섯 건이 전부 그 플래그의 것이라는 증거다.

진단 전문(첫 건만).

```text
===== 소스: ex.c =====
#include <stdio.h>
int main(void) {
    int a = 6, b = 2, c = 2;
    printf("a=6 b=2 c=2 : a & b == c   = %d   |  (a & b) == c = %d\n", a & b == c, (a & b) == c);
    printf("a=6         : a << 1 + 2   = %d   |  (a << 1) + 2 = %d\n", a << 1 + 2, (a << 1) + 2);
    int x = 0, y = 2;
    printf("x=0 y=2     : !x & y       = %d   |  !(x & y)     = %d\n", !x & y, !(x & y));
    int d = 6, e = 3, f = 1;
    printf("d=6 e=3 f=1 : d & e ^ f    = %d   |  d & (e ^ f)  = %d\n", d & e ^ f, d & (e ^ f));
    int g = 1, h = 3, i = 1;
    printf("g=1 h=3 i=1 : g | h ^ i    = %d   |  (g | h) ^ i  = %d\n", g | h ^ i, (g | h) ^ i);
    return 0;
}
```

```text
ex.c: In function ‘main’:
ex.c:4:78: warning: suggest parentheses around comparison in operand of ‘&’ [-Wparentheses]
    4 |     printf("a=6 b=2 c=2 : a & b == c   = %d   |  (a & b) == c = %d\n", a & b == c, (a & b) == c);
      |                                                                            ~~^~~~
ex.c:5:74: warning: suggest parentheses around ‘+’ inside ‘<<’ [-Wparentheses]
    5 |     printf("a=6         : a << 1 + 2   = %d   |  (a << 1) + 2 = %d\n", a << 1 + 2, (a << 1) + 2);
      |                                                                          ^~
ex.c:7:72: warning: suggest parentheses around operand of ‘!’ or change ‘&’ to ‘&&’ or ‘!’ to ‘~’ [-Wparentheses]
    7 |     printf("x=0 y=2     : !x & y       = %d   |  !(x & y)     = %d\n", !x & y, !(x & y));
      |                                                                        ^~
ex.c:9:74: warning: suggest parentheses around arithmetic in operand of ‘^’ [-Wparentheses]
    9 |     printf("d=6 e=3 f=1 : d & e ^ f    = %d   |  d & (e ^ f)  = %d\n", d & e ^ f, d & (e ^ f));
      |                                                                        ~~^~~
ex.c:11:78: warning: suggest parentheses around arithmetic in operand of ‘|’ [-Wparentheses]
   11 |     printf("g=1 h=3 i=1 : g | h ^ i    = %d   |  (g | h) ^ i  = %d\n", g | h ^ i, (g | h) ^ i);
      |                                                                            ~~^~~
```

- ★ 세 번째 문구가 **고치는 법 두 가지**를 같이 말해 준다 — 「`&` 를 `&&` 로」 또는 「`!` 를 `~` 로」.

### 2. `sizeof` 뒤에 연산을 이으면 ★

**출력**

```text
sizeof a + b   = 6   |  sizeof (a + b) = 4
sizeof a * 2   = 8   |  sizeof (a * 2) = 4
```

**왜 그런가**

```text
   sizeof a + b       (int a, b = 2 · sizeof(int) = 4)

   sizeof 는 단항이라 a 하나만 데려간다
   +----------+
   sizeof  a   +  b
   +----------+
        = 4        4 + 2 = ★ 6

   sizeof a * 2  =  (sizeof a) * 2  =  4 * 2 = ★ 8
```

**규칙 한 줄**

- **`sizeof` 는 단항 연산자**다. 괄호 없는 피연산자 하나만 데려가고, 뒤에 이항 연산자가 오면 거기서 끊긴다.
- `sizeof(a + b)` 의 괄호는 **`sizeof` 의 일부가 아니라 그냥 괄호**다. 그래서 식 전체가 피연산자가 된다.

**경고**

```text
[-std=c17 -Wall -Wextra -Wconversion -pedantic] 0 건  exit=0
```

- ★ **0건**이다. 이 문서의 세기 표에서 **유일하게 아무도 말하지 않는 자리**다.

**1번과 결정적으로 다른 점**

- 1번은 `-Wall` 이 전부 잡는다. **이 자리는 어느 플래그도 안 잡는다.**
- 그래서 **`sizeof` 에는 언제나 괄호**가 규칙이 된다 — 도구가 뒤를 봐 주지 않기 때문이다.

### 3. 포인터 증감 세 형태

**출력**

```text
*p++   = 10,  p - arr = 1
(*p)++ = 10,  arr[0] = 11,  p - arr = 0
*++p   = 20,  p - arr = 1
```

**괄호로 풀면**

```text
   *p++     =  *(p++)     후위 ++ 가 단항 * 보다 세다
   (*p)++   =  괄호가 있으니 *p 가 먼저 묶이고 그 값이 증가한다
   *++p     =  *(++p)

   arr = [10, 20, 30, 40]
          ^
          p

   *p++   -> 값 10, p 가 한 칸 간다        p - arr = 1
   (*p)++ -> arr[0] 이 11, p 는 그대로     p - arr = 0
   *++p   -> p 가 먼저 간 뒤 값 20         p - arr = 1
```

**`p->x++` 는**

- 후위 무리 안의 이야기다 — `->` 와 `++` 가 **같은 우선순위**이고 **왼쪽 결합**이라 `(p->x)++` 로 묶인다.
- `*p++` 와 달리 괄호를 안 쳐도 **뜻이 맞는다.** 그래서 이 자리는 함정이 아니다.

**★ 한 `printf` 안에서 재면**

**답이 뒤집힌다.** 처음에 그렇게 쟀다가 틀린 관찰을 얻었다.

```text
===== 소스: ex.c (틀린 측정 코드) =====
#include <stddef.h>
#include <stdio.h>
int main(void) {
    int arr[4] = {10, 20, 30, 40};
    int *p = arr;
    printf("*p++   = %d, p 는 이제 arr[%td]\n", *p++, (ptrdiff_t)(p - arr));
    p = arr;
    printf("(*p)++ = %d, arr[0] 은 이제 %d\n", (*p)++, arr[0]);
    arr[0] = 10;
    p = arr;
    printf("*++p   = %d, p 는 이제 arr[%td]\n", *++p, (ptrdiff_t)(p - arr));
    return 0;
}
```

```text
ex.c: In function ‘main’:
ex.c:6:51: warning: operation on ‘p’ may be undefined [-Wsequence-point]
    6 |     printf("*p++   = %d, p 는 이제 arr[%td]\n", *p++, (ptrdiff_t)(p - arr));
      |                                                  ~^~
ex.c:11:50: warning: operation on ‘p’ may be undefined [-Wsequence-point]
   11 |     printf("*++p   = %d, p 는 이제 arr[%td]\n", *++p, (ptrdiff_t)(p - arr));
      |                                                  ^~~
*p++   = 10, p 는 이제 arr[0]
(*p)++ = 10, arr[0] 은 이제 10
*++p   = 20, p 는 이제 arr[0]
```

```text
   같은 세 줄인데 답이 다르다.

   한 printf 안에서 잰 것        문을 나눠 잰 것
   +------------------------+   +------------------------+
   | p - arr  = 0           |   | p - arr  = 1           |
   | arr[0]   = 10          |   | arr[0]   = 11          |
   | p - arr  = 0           |   | p - arr  = 1           |
   +------------------------+   +------------------------+
     ★ 전부 "안 변했다" 로 보인다   ★ 실제로는 변했다
```

- 한 `printf` 의 인자들 사이에는 **시퀀스 포인트가 없다.** `p` 를 바꾸면서 같은 식에서 읽으면 **UB** 다.
- gcc 가 **`-Wsequence-point`(`-Wall` 소속)로 말해 줬다.** 경고를 안 봤으면 틀린 관찰을 실었을 것이다.
- **이 사고의 정본은 [10번 형제](../10-evaluation-order-and-sequence-points/)다.** 09 는 여기까지만 본다.

### 4. 결합성이 답을 바꾸는 자리

**출력**

```text
sizeof a + b   = 6   |  sizeof (a + b) = 4
sizeof a * 2   = 8   |  sizeof (a * 2) = 4
0 ? 1 : 0 ? 2 : 3       = 3   (0 ? 1 : (0 ? 2 : 3))
a = b = c   ->  a=100 b=100 c=100   (오른쪽 결합)
p - q - r   = 5   ((p - q) - r)   |  p - (q - r) = 11
z = (1, 2, 3)  -> z = 3   (콤마는 마지막 값)
w = 1, 2       -> w = 1   (= 가 , 보다 높다)
```

- `t` = **3** · `a` = `b` = `c` = **100** · `p - q - r` = **5** · `z` = **3** · `w` = **1**.

**오른쪽 결합인 것**

```text
   오른쪽 결합  단항 연산자 (! ~ - + * & sizeof 캐스트 ++a --a)
                ?:
                =  +=  -=  *=  /=  %=  <<=  >>=  &=  ^=  |=

   ★ 나머지 이항 연산자는 전부 왼쪽 결합이다. (후위 ++ 도 왼쪽 결합)
```

- `a = b = c` 가 `a = (b = c)` 인 이유 — **대입은 식이고 그 값이 대입된 값**이다.\
  왼쪽 결합이면 `(a = b) = c` 가 되는데 `(a = b)` 는 lvalue 가 아니라 **에러**가 난다.
- `0 ? 1 : 0 ? 2 : 3` 이 `0 ? 1 : (0 ? 2 : 3)` 이라 **else-if 사다리**로 읽힌다. `?:` 가 오른쪽 결합이라 얻는 것이다.

**`w` 가 1 인 이유**

```text
   w = 1, 2

   = 가 , 보다 세다
   +-------+
   w  =  1  ,  2
   +-------+
     여기까지가 한 덩어리 -> w 는 ★ 1
     그 다음 2 는 계산되고 버려진다
```

- gcc 가 「right-hand operand of comma expression has no effect」로 말해 준다(`-Wunused-value`).

**`int z = 1, 2, 3;` 이면**

- **선언이 된다.** 초기자 자리의 `,` 는 연산자가 아니라 **선언자 구분자**로 먹힌다.\
  `z` 를 1 로 초기화하고 `2`·`3` 이라는 **이름을 선언하려다 실패**한다 — 그래서 괄호가 필수다.
- ★ 이것은 **던져 보지 않았다**(에러 문구를 인용하지 않는다). 위의 `int z = (1, 2, 3);` 만 돌렸다.

### 5. 비교를 사슬로 쓰고 조건에서 대입하면

**출력**

```text
a=5 b=3 c=1 : a < b < c   = 1   |  (a < b) < c = 1
            : a == b == 0 = 1   |  (a == b) == 0 = 1
if (x = b)  -> 참으로 읽혔다, x = 3
a + b << c  = 16   |  a + (b << c) = 11
-a % b       = -2   |  -(a % b)     = -2
```

- **`if` 는 실행된다.** `x = b` 의 값이 3 이고 0 이 아니므로 참이다.
- `a < b < c` 는 `(a<b)<c` = `0 < 1` = **1** 이다 — **수학의 `5 < 3 < 1`(거짓)과 반대**다.
- `a + b << c` 는 `(a+b) << c` = `8 << 1` = **16**.

**gcc 의 문구**

```text
===== 소스: ex.c =====
#include <stdio.h>
int main(void) {
    int a = 5, b = 3, c = 1, x = 0;
    printf("a=5 b=3 c=1 : a < b < c   = %d   |  (a < b) < c = %d\n", a < b < c, (a < b) < c);
    printf("            : a == b == 0 = %d   |  (a == b) == 0 = %d\n", a == b == 0, (a == b) == 0);
    if (x = b) printf("if (x = b)  -> 참으로 읽혔다, x = %d\n", x);
    printf("a + b << c  = %d   |  a + (b << c) = %d\n", a + b << c, a + (b << c));
    printf("-a %% b       = %d   |  -(a %% b)     = %d\n", -a % b, -(a % b));
    return 0;
}
```

```text
ex.c: In function ‘main’:
ex.c:4:72: warning: comparisons like ‘X<=Y<=Z’ do not have their mathematical meaning [-Wparentheses]
    4 |     printf("a=5 b=3 c=1 : a < b < c   = %d   |  (a < b) < c = %d\n", a < b < c, (a < b) < c);
      |                                                                      ~~^~~
ex.c:5:74: warning: suggest parentheses around comparison in operand of ‘==’ [-Wparentheses]
    5 |     printf("            : a == b == 0 = %d   |  (a == b) == 0 = %d\n", a == b == 0, (a == b) == 0);
      |                                                                        ~~^~~~
ex.c:6:9: warning: suggest parentheses around assignment used as truth value [-Wparentheses]
    6 |     if (x = b) printf("if (x = b)  -> 참으로 읽혔다, x = %d\n", x);
      |         ^
ex.c:7:59: warning: suggest parentheses around ‘+’ inside ‘<<’ [-Wparentheses]
    7 |     printf("a + b << c  = %d   |  a + (b << c) = %d\n", a + b << c, a + (b << c));
      |                                                         ~~^~~
```

- ★ 첫 문구가 정확히 「**수학적 의미를 갖지 않는다**」라고 말한다. 외운 설명이 아니라 **컴파일러가 알려 준 것**이다.

**경고 수**

```text
[-std=c17] 0 건  exit=0
[-std=c17 -Wall] 4 건  exit=0
[-std=c17 -Wextra] 0 건  exit=0
[-std=c17 -Wall -Wextra] 4 건  exit=0
[-std=c17 -Wparentheses] 4 건  exit=0
[-std=c17 -Wall -Wextra -pedantic] 4 건  exit=0
```

- **4건, 전부 `-Wparentheses`, `-Wall` 소속.**

**일부러 대입할 때**

- **괄호를 한 겹 더 친다** — `if ((x = b))`. 널리 쓰이는 관용구다.
- ★ 이 문서에서는 **그 형태로 경고가 사라지는지 던져 보지 않았다.**

### 6. 괄호가 캐스트인가 호출인가 ★

**출력**

```text
(T)(d)  = 3   <- 캐스트다
(g)(4)  = 40   <- 호출이다
```

**`T` 를 변수로 바꾸면**

```text
===== 소스: ex.c =====
#include <stdio.h>
int T = 7;                           /* 이번엔 변수다 */
int f(int v) { return v * 10; }
int main(void) {
    int (*g)(int) = f;               /* g 는 함수 포인터 변수 */
    double d = 3.9;
    printf("(T)(d)  = %d   <- 캐스트다\n", (T)(d));
    printf("(g)(4)  = %d   <- 호출이다\n", (g)(4));
    return 0;
}
```

```text
ex.c: In function ‘main’:
ex.c:7:44: error: called object ‘T’ is not a function or function pointer
    7 |     printf("(T)(d)  = %d   <- 캐스트다\n", (T)(d));
      |                                            ^
ex.c:2:5: note: declared here
    2 | int T = 7;                           /* 이번엔 변수다 */
      |     ^
```

**우선순위로 풀리는 문제인가**

- **아니다.** 글자가 똑같아서 우선순위가 개입할 여지가 없다.\
  파서가 **「`T` 가 타입 이름으로 선언됐나」를 봐야** 어느 쪽인지 정해진다.
- C 문법에서 이것을 **lexer hack** 이라고 부르는 자리다 — 어휘 분석기가 심볼 테이블을 알아야 한다.

**메시지가 증거인 이유**

- 「**called object** `T` is not a function」은 컴파일러가 그 식을 **호출로 파싱했다**는 뜻이다.\
  캐스트로 파싱했다면 나올 수 없는 문구다.
- 「무엇이 안 되나」가 아니라 **「무엇으로 읽었나」를 말해 주는 에러**라 값이 크다.

### 7. 비트 연산자의 자리

**깨지는 코드**

```c
if (flags & MASK == 0) { ... }        /* flags & (MASK == 0) */
```

- `MASK` 가 0 이 아니면 `MASK == 0` 은 0 이고, `flags & 0` 은 **언제나 0** 이다.\
  즉 **`if` 몸통이 절대 안 돈다.** 반대로 `MASK` 를 0 으로 준 날에는 `flags & 1` 이 된다.
- 어느 쪽이든 **의도와 무관한 식**이 된다.

**올바른 형태**

```c
if ((flags & MASK) == 0) { ... }
```

**`&&` 에서는 왜 안 나는가**

```text
   ==  !=     <- 비교
   &  ^  |    <- 비트  ★ 비교보다 약하다
   &&  ||     <- 논리  ★ 비교보다 약하다

   a && b == c  ->  a && (b == c)   ★ 이건 보통 뜻대로다
   a &  b == c  ->  a &  (b == c)   ★ 이건 뜻이 무너진다
```

- **묶이는 방식은 똑같다.** 다른 것은 **그게 내가 원한 뜻이냐**다.
- `&&` 는 「조건 두 개」를 잇는 것이라 오른쪽이 비교식인 게 **자연스럽다.**
- `&` 는 「비트 두 벌」을 겹치는 것이라 오른쪽이 0/1 로 줄어들면 **뜻이 사라진다.**

### 8. `-Wparentheses` 의 소속과 한계

**소속**

```text
[-std=c17] 0 건  exit=0
[-std=c17 -Wall] 5 건  exit=0
[-std=c17 -Wextra] 0 건  exit=0
[-std=c17 -Wall -Wextra] 5 건  exit=0
[-std=c17 -Wparentheses] 5 건  exit=0
[-std=c17 -Wall -Wno-parentheses] 0 건  exit=0
```

- **`-Wall` 에 있다.** `-Wextra` 단독은 0건이다.
- 확인 방법은 **켜고 끄고 세는 것**이다 — `-Wparentheses` 단독이 5건, `-Wall -Wno-parentheses` 가 0건.

**몇 개를 잡나**

| 함정 | `-Wall` | 못 잡나 |
|---|---|---|
| `a & b == c` | **1건** | 잡는다 |
| `a << 1 + 2` | **1건** | 잡는다 |
| `!x & y` | **1건** | 잡는다 |
| `d & e ^ f` · `g \| h ^ i` | **2건** | 잡는다 |
| `a < b < c` | **1건** | 잡는다 |
| `if (x = y)` | **1건** | 잡는다 |
| ★ `sizeof a * 2` | **0건** | **못 잡는다** |
| ★ `*p++` 오해 | 0건 | 못 잡는다(합법이다) |
| ★ 평가 순서 의존 | 0건 | 못 잡는다(→ 10번) |

**가르는 방법**

- **`-Wno-` 짝을 붙여 끄고 다시 센다.** 건수가 0 이 되면 그 경고가 전부 그 플래그의 것이다.
- 「이 플래그에 이게 들어 있나」를 **가장 싸게 증명하는 방법**이다.

### 9. 경고를 세다가 0 을 받았을 때 ★★

**출력**

```text
[-std=c17 -Wall -Wprecedence] ★컴파일실패 exit=1 (warning 줄 0 — 세지 않는다)
```

```text
gcc: error: unrecognized command-line option ‘-Wprecedence’
exit=1
--- grep -c warning 이 답한 것 ---
0
```

**무슨 뜻인가**

- 「**경고가 없다**」가 아니라 「**컴파일이 아예 안 됐다**」는 뜻이다.\
  gcc 에 `-Wprecedence` 라는 플래그는 없다. 우선순위 검사는 `-Wparentheses` 가 한다.

**한 가지 더 볼 것**

```text
   gcc ... | grep -c warning       -> 0      ★ 이것만 보면 속는다
   종료 코드 ($?)                   -> 1      ★ 여기서 갈린다
```

- **종료 코드**다. `0` 이면 「정말 경고가 없다」, `0` 이 아니면 「세기 자체가 무효」다.
- 이 문서의 모든 세기 표에 `exit=` 가 붙어 있는 이유가 이것이다.

**같은 집안인 이유**

- 둘 다 **「아무 일도 안 일어났다」를 「괜찮다」로 읽는** 사고다.
- 「안 터졌다 ≠ 안전하다」는 **실행** 쪽, 「경고 0건 ≠ 검사가 돌았다」는 **도구** 쪽의 같은 함정이다.
- ★ 검사기가 **자기가 무엇을 못 보는지 말하게** 만들어야 한다.

### 10. 우선순위는 무엇을 정하지 않는가 ★★★

**출력**

```text
===== 소스: ex.c =====
#include <stdio.h>
static int order = 0;
static int f(void) { printf("  f 가 %d 번째\n", ++order); return 1; }
static int g(void) { printf("  g 가 %d 번째\n", ++order); return 2; }
static int h(void) { printf("  h 가 %d 번째\n", ++order); return 3; }
static void take(int a, int b, int c) { printf("  받은 값 = %d %d %d\n", a, b, c); }
int main(void) {
    printf("take(f(), g(), h()):\n");
    take(f(), g(), h());
    order = 0;
    printf("f() + g() * h() = ");
    int v = f() + g() * h();
    printf("  결과 %d\n", v);
    return 0;
}
```

```text
take(f(), g(), h()):
  h 가 1 번째
  g 가 2 번째
  f 가 3 번째
  받은 값 = 1 2 3
f() + g() * h() =   f 가 1 번째
  g 가 2 번째
  h 가 3 번째
  결과 7
```

- `v` 는 **7** 이다 — `1 + (2 * 3)`.
- `f() + g() * h()` 에서 세 함수는 **`f` → `g` → `h`** 순으로 불렸다.

**우선순위로 설명할 수 있는가**

```text
   묶이는 순서 (우선순위)            도는 순서 (실측)
   +--------------------------+     +--------------------------+
   |     +                    |     |  f 가 1 번째              |
   |    / \                   |     |  g 가 2 번째              |
   |  f()  *                  |     |  h 가 3 번째              |
   |      / \                 |     |                          |
   |    g()  h()              |     |  ★ 가장 나중에 묶이는 f 가 |
   |                          |     |     가장 먼저 돌았다       |
   +--------------------------+     +--------------------------+
```

- **설명할 수 없다.** `*` 가 세니까 `g()`·`h()` 가 먼저 묶이지만, **부른 순서는 `f` 가 먼저**였다.
- 같은 실행의 첫 줄을 보면 더 분명하다 — **`take(f(), g(), h())` 에서 gcc 는 `h` 부터** 불렀다.\
  인자 사이에는 우선순위 자체가 없는데도 순서가 정해졌다. **누가 정했는지가 10번의 질문**이다.

**한 문장으로**

> **우선순위는 「값이 어떻게 조립되나」를 정하고, 평가 순서는 「부작용이 언제 나나」를 정한다.**\
> 앞엣것은 문법이라 어느 구현에서도 같고, 뒤엣것은 **미명시**라 구현마다 다르다.

**정본**

- [10번 형제](../10-evaluation-order-and-sequence-points/)다. 거기서 **gcc 와 clang 이 반대 순서**로 도는 것을 본다.

### 11. 그래서 괄호를 언제 치나

**규칙 두 줄**

> **괄호는 공짜다.** 읽는 사람이 우선순위 표를 찾아보게 만드는 쪽이 비싸다.\
> **`sizeof` 와 비트 연산에는 무조건 괄호를 친다** — 하나는 도구가 못 보고, 하나는 가장 자주 당한다.

**표 대신 기억할 네 줄**

```text
  1. 단항은 전부 이항보다 세다              !x & y  는  (!x) & y
  2. 산술 > 시프트 > 비교 > 비트 > 논리       a & b == c  는  a & (b == c)
  3. 나머지 이항은 왼쪽 결합                 a - b - c  는  (a-b)-c
  4. ?: 와 대입만 오른쪽 결합                a = b = c  는  a = (b=c)
```

**빌드 플래그 한 줄**

```text
개발·운영 빌드
  gcc -std=c17 -O2 -Wall -Wextra -Werror
  (-Wparentheses 는 ★ -Wall 에 있다. -Wextra 는 이 주제에 아무것도 더하지 않는다)

플래그 소속을 확인할 때
  gcc -Wall -Wno-parentheses ...   (건수가 0 이 되면 그 플래그의 것이다)
  ★ 그리고 종료 코드를 같이 본다

교차 확인
  clang -Wall -Wextra              (이 주제의 여섯 함정에서 gcc 와 같은 답이었다)
```

**남는 함정 하나**

- **`sizeof a * 2`** 다. `-Wall -Wextra -Wconversion -pedantic` 전부 **0건**이다.
- ★ 그리고 `-Wall` 이 못 보는 **더 큰 것**이 하나 더 있다 — **평가 순서 의존**이다.\
  그건 경고가 아니라 **주제가 다른 문제**이고, [10번 형제](../10-evaluation-order-and-sequence-points/)가 정본이다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 플래그로 돌렸나 |
|---|---|---|
| 우선순위 5종 | `a & b == c`·`a << 1+2`·`!x & y`·`d & e ^ f`·`g \| h ^ i` 가 **다섯 줄 전부** 괄호판과 다른 값 | `-Wall -Wextra -pedantic` · 플래그 8벌로 세기 |
| `sizeof`·결합성 | `sizeof a + b`=6 · `sizeof a * 2`=8 · `a=b=c` 전부 100 · `p-q-r`=5 · `z`=3 · `w`=1 | `-Wall -Wextra -pedantic`(`-Wunused-value` 3건) |
| 포인터 증감 | `*p++`/`(*p)++`/`*++p` 의 값과 `p - arr` · **문을 나눈 판과 안 나눈 판이 다름** | `-Wall -Wextra -pedantic` |
| 〃 틀린 측정 | 한 `printf` 안에서 재면 `p - arr`=0, `arr[0]`=10 으로 **틀린 관찰** · `-Wsequence-point` 2건 | `-Wall -Wextra -pedantic` |
| 비교 사슬·대입 조건 | `a<b<c`=1 · `a+b<<c`=16 · `if (x=b)` 실행됨 · 경고 4건 전부 `-Wparentheses` | 플래그 6벌로 세기 |
| 캐스트 대 호출 | `(T)(d)`=3(캐스트) · `(g)(4)`=40(호출) · `T` 를 변수로 바꾸면 **에러** | `-Wall -Wextra -pedantic` |
| 플래그 소속 | `-Wparentheses` 가 **`-Wall`** 소속 · `-Wextra` 단독 0건 · `-Wno-parentheses` 로 0건 | 플래그 8벌 |
| ★ 거짓 0 재현 | `-Wprecedence`(없는 플래그)로 **경고 0건 · exit=1** — 컴파일 실패였다 | `-Wall -Wprecedence` |
| 평가 순서 다리 | `f() + g() * h()` → `f`·`g`·`h` 순 · `take(f(),g(),h())` → **`h`·`g`·`f` 순** · 결과 7 | `-Wall -Wextra -pedantic` · `-O2` |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0)에서만** 그렇다.

- `sizeof(int)` 가 **4** 인 것 — `sizeof a + b` 가 6 인 근거다([02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)).
- `-Wparentheses` 가 **`-Wall`** 에 있는 것 — gcc 의 분류다.
- `take(f(), g(), h())` 가 **`h` 부터** 도는 것 — ★ **구현 정의가 아니라 미명시**다([10번 형제](../10-evaluation-order-and-sequence-points/)).
- `-Wprecedence` 가 **없는 옵션**인 것.

**우선순위·결합성 자체는 구현 의존이 아니다.** 위 표의 모든 「묶이는 방식」은 **어느 C 구현에서도 같다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `if ((x = b))` 로 경고가 사라지는지 · `int z = 1, 2, 3;` 의 에러 문구 ·\
  매크로 안에서 우선순위가 무너지는 것(42번 주제) · C++ 의 우선순위 표 · `_Alignof`·복합 리터럴의 결합.
- **못 잰 것** — 없다. 이 주제는 전부 컴파일·실행으로 확인된다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- `-Wparentheses` 의 소속이 바뀌었는지(`-Wall` → 다른 데로).
- `sizeof a * 2` 를 잡아 주는 검사가 새로 생겼는지.
- gcc 의 진단 **문구**가 바뀌었는지(이 문서는 문구를 그대로 인용한다).
- **우선순위·결합성 자체는 다시 돌릴 필요가 없다** — C89 이후 바뀐 적이 없고 C23 도 건드리지 않았다.
