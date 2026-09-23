# c/syntax/01 — 선언 문법과 읽는 법: 안에서 밖으로·저장 클래스·`const` 의 자리 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 플래그는 `-std=c17 -Wall -Wextra` 이고, 다른 표준·최적화 수준을 쓴 블록은 **그 자리에 밝혔다.**\
> gcc 13 에는 `-std=c23` 이 없어 C23 확인은 전부 `-std=c2x` 로 했다.
> 주소값은 ASLR 때문에 실행마다 바뀐다 — **자릿수와 영역만 근거로 읽는다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 괄호 두 개가 만드는 차이

**출력**

```text
sizeof(int *p1[10]) = 80   (포인터 8 x 10)
sizeof(int (*p2)[10]) =  8 (포인터 하나)
sizeof(*p2)          = 40  (가리키는 배열 전체)
sizeof(p1[0])        =  8
p2 vs p2+1 diff = 40 bytes
```

**왜 그런가**

```text
int *p1[10];                          int (*p2)[10];

 p1: +----+----+ ... +----+            p2: +--------+
     |ptr0|ptr1|     |ptr9|                | 주소 1개 |
     +----+----+ ... +----+                +--------+
       |    |          |                        |
       v    v          v                        v
      int  int        int              +----+----+ ... +----+
                                       |int |int |     |int |
  80바이트 = 8 x 10                    +----+----+ ... +----+
                                        8바이트, 가리키는 것이 40
```

- `p1` 은 **바깥이 배열**이다 — 괄호가 없으니 `[]` 가 `*` 보다 먼저 붙는다.\
  원소가 포인터라 8 × 10 = 80바이트.
- `p2` 는 **바깥이 포인터**다 — 괄호가 `[]` 를 막아 `*` 가 먼저 붙었다.\
  포인터 하나이므로 8바이트, `*p2` 는 가리키는 `int[10]` 이라 40바이트.
- `p2 + 1` 이 **40바이트를 건너뛴다**는 것이 결정적 증거다.\
  포인터 산술은 가리키는 타입의 크기만큼 움직이는데, `p2` 가 가리키는 타입이 `int[10]` 이다.

**한국어로 옮기면**

- `int *p1[10]` — 「`p1` 은 `int` 를 가리키는 포인터 10개짜리 **배열**」
- `int (*p2)[10]` — 「`p2` 는 `int` 10개짜리 배열을 가리키는 **포인터**」

> **포인터 산술(pointer arithmetic)** — 포인터에 정수를 더하면 **바이트가 아니라 원소 단위**로 움직이는 규칙.\
> 예: `int *p` 에서 `p + 1` 은 4바이트, `int (*q)[10]` 에서 `q + 1` 은 40바이트 뒤다.\
> 정본은 [목록의 **15번 주제**](../15-pointer-arithmetic-and-indexing/).

### 2. 이 선언을 말로 옮겨라

**출력**

```text
ft[0]('a') = "A"   ft2[0]('a') = "A"
ft[1]('a') = "a"   ft2[1]('a') = "a"
ft[2]('a') = "b"   ft2[2]('a') = "b"
sizeof ft = 24   sizeof ft2 = 24   sizeof ft[0] = 8
(*ft[0])('a') = "A"   ft[0]('a') = "A"
```

**안에서 밖으로 다섯 단계**

```text
char *(*ft[3])(int);

  ① ft                      "ft 는"
  ② ft[3]                   "3개짜리 배열이고"          <- [] 가 * 보다 세다
  ③ (*ft[3])                "그 원소는 포인터이고"       <- 괄호 안이 끝났으니 밖으로
  ④ (*ft[3])(int)           "int 를 받는 함수를 가리키고"
  ⑤ char *(*ft[3])(int)     "그 함수는 char* 를 돌려준다"
```

- 최종: 「**`ft` 는, `int` 를 받아 `char *` 를 돌려주는 함수를 가리키는 포인터, 3개짜리 배열**」
- `sizeof ft` = **24** — 함수 포인터 8바이트 × 3.

**`ft[0]('a')` 와 `(*ft[0])('a')`**

- **같다.** 위 출력의 마지막 줄이 둘을 나란히 찍은 것이다(둘 다 `"A"`).
- 이유: 함수 지시자는 호출 자리에서 **자동으로 함수 포인터가 되고**, 함수 포인터는 호출 자리에서 **자동으로 역참조된다.**\
  그래서 `*` 를 몇 개 붙여도 같다 — 형태가 여럿인 것이지 뜻이 여럿인 게 아니다.

**`typedef` 두 줄로 푼 것**

```c
typedef char *CharFn(int);      /* 함수 타입 */
typedef CharFn *CharFnPtr;      /* 그 함수를 가리키는 포인터 */

CharFnPtr ft2[3] = { to_upper, to_same, to_next };
```

- 위 출력에서 `sizeof ft2` 도 **24** 로 같고, `ft2[0] = ft[0];` 대입이 경고 없이 통과한다.\
  **같은 타입이라는 뜻이다.**
- `typedef` 는 **새 타입을 만들지 않고 별명만 붙인다.** 정본은 [목록의 **06번 주제**](../06-typedef-and-type-aliases/).

### 3. 한 선언에 이름이 둘이면

**출력**

```text
ex.c:6:7: warning: assignment to ‘int’ from ‘int *’ makes integer from pointer without a cast [-Wint-conversion]
--- 실행 ---
p=0x7ffe1e05fc68  q=503708776  (x 의 주소는 0x7ffe1e05fc68)
```

**왜 그런가**

- `q` 의 타입은 **`int`** 다. `*` 는 기본 타입 쪽이 아니라 **선언자 쪽**에 속한다.

```text
int *p, q;
    ^^^  ^
    |    선언자 2: q       -> int
    선언자 1: *p           -> int *
```

- **경고일 뿐 에러가 아니다.** `-Wall -Wextra` 로도 `-Wint-conversion` 경고 한 줄이고 실행 파일이 만들어진다.
- 찍으면 **주소의 아래 32비트**가 나온다 — `0x7ffe1e05fc68` 의 하위 32비트 `0x1e05fc68` = `503708776`.\
  상위 절반이 조용히 잘렸다.
- `int* p, q;` 로 붙여 써도 **뜻이 안 바뀐다.** `*` 가 어디에 붙어 보이든 문법적으로는 선언자 쪽이다.\
  그래서 실무 규칙은 **한 줄에 포인터 선언자 하나**다.

### 4. `const` 를 어디에 뒀느냐

**출력**

```text
ex.c: In function ‘main’:
ex.c:9:8: error: assignment of read-only location ‘*p’
    9 |     *p = 9;      /* (2) 에러 — 가리키는 값은 못 바꾼다 */
      |        ^
ex.c:10:7: error: assignment of read-only variable ‘q’
   10 |     q = &b;      /* (3) 에러 — 포인터를 못 바꾼다 */
      |       ^
ex.c:12:7: error: assignment of read-only variable ‘r’
   12 |     r = &b;      /* (5) 에러 */
      |       ^
```

**에러가 나는 줄**

- **(2)·(3)·(5)** 셋이다. (1)`p = &b;` 와 (4)`*q = 9;` 는 **진단이 전혀 없다.**

**`read-only location` 과 `read-only variable`**

```text
const int *p;          int * const q;
    ^^^^^^^                  ^^^^^^^
    가리키는 값이 const       포인터 자신이 const

  *p = 9  ->  error: assignment of read-only location ‘*p’
                                      ^^^^^^^^  "위치"    (변수가 아니라 가리키는 자리)

  q = &b  ->  error: assignment of read-only variable ‘q’
                                      ^^^^^^^^  "변수"    (q 그 자체)
```

- gcc 의 낱말 선택이 **무엇이 얼었는지를 그대로 말해 준다.**\
  `*p` 는 변수가 아니라 「역참조한 위치」라 `location`, `q` 는 변수 자체라 `variable`.

**`const int *p` 와 `int const *p`**

- **완전히 같다.** `const` 는 자기 **바로 왼쪽**을 얼리고, 왼쪽에 아무것도 없으면 오른쪽을 얼린다.\
  `const int` 나 `int const` 나 「`const` 인 `int`」다.
- 외우는 법: **`*` 를 기준으로 `const` 가 왼쪽이면 가리키는 값, 오른쪽이면 포인터 자신.**

**매개변수에서 의미가 있는 쪽**

- **`const char *s`**(앞엣것)다. 「이 함수는 당신이 준 문자열을 안 바꿉니다」라는 **호출자와의 계약**이다.
- `char * const s`(뒤엣것)는 함수 안의 지역 변수 `s` 를 얼릴 뿐이라 **호출자가 알 필요가 없다.**\
  헤더에 쓰면 계약을 말하는 척하면서 아무 계약도 안 한 것이 된다.
- `const` 가 최적화 보장이 아니라 **계약**이라는 논점의 정본은 목록의 **31번 주제**.

### 5. `f()` 에 인자를 주면

**출력**

```text
##### -std=c17 -Wall -Wextra #####
(exit 0)
1
2

##### -std=c17 -Wall -Wextra -Wstrict-prototypes #####
ex.c:2:1: warning: function declaration isn’t a prototype [-Wstrict-prototypes]
ex.c:5:5: warning: function declaration isn’t a prototype [-Wstrict-prototypes]

##### -std=c2x -Wall -Wextra #####
ex.c: In function ‘main’:
ex.c:9:20: error: too many arguments to function ‘noproto’
    9 |     printf("%d\n", noproto(1, 2, 3));   /* 인자를 줘 본다 */
      |                    ^~~~~~~
ex.c:5:5: note: declared here
    5 | int noproto() { return 1; }
      |     ^~~~~~~
(exit 1)
```

**왜 그런가**

- C17 `-Wall -Wextra` 는 **아무 말도 안 한다.** 인자 셋을 던졌는데 조용히 통과하고 `1` 을 찍는다.
- 잡으려면 **`-Wstrict-prototypes`** 를 따로 켜야 한다. 이 플래그는 `-Wall` 에도 `-Wextra` 에도 안 들어 있다.
- `-std=c2x` 에서는 **하드 에러**다. C23 부터 `f()` 가 `f(void)` 와 같은 뜻이 되었기 때문이다.

| 표준 | `int f();` 의 뜻 | `f(1,2,3)` 호출 |
|---|---|---|
| C17 이하 | **매개변수 정보를 밝히지 않음**(「없다」가 아니다) | 조용히 통과 |
| C23 | `int f(void);` 와 같음 | `error: too many arguments` |

- 실무 결론: **C17 코드에서는 `-Wstrict-prototypes` 를 항상 켠다.**\
  `-Wall -Wextra` 만 믿으면 이 구멍이 그대로 남는다.
- 정본은 목록의 **34번 주제**.

### 6. 저장 클래스 지정자는 무엇을 정하는가

**출력**

```text
10 20 1 2
counter: 3 2 1
&a = 0x7fff80c6dd84 (스택)
&file_static = 0x639c34ed6010 (정적 영역)

ex2.c: In function ‘main’:
ex2.c:1:1: error: address of register variable ‘r’ requested
    1 | int main(void) { register int r = 2; int *p = &r; return *p; }
      | ^~~~~~~~~~~~~~
```

**두 축**

```text
                     저장 기간              연결
                  (언제 생기고 사라지나)   (다른 파일이 같은 것을 보나)
  ------------------------------------------------------------------
  (아무것도 없음)   블록 안: 자동          블록 안: 없음
                    파일 수준: 정적        파일 수준: 외부
  static            언제나 정적            파일 수준이면 내부
  extern            정적                   외부 (정의는 다른 곳)
  auto              자동                   없음
  register          자동 + 주소를 못 잡음  없음
```

**블록 안 `static` 과 파일 수준 `static` 은 다른 것을 바꾼다**

- **블록 안** `static int n;` — 바꾸는 것은 **저장 기간**이다(자동 → 정적).\
  연결은 원래도 「없음」이고 그대로다. 함수가 끝나도 값이 남는다.
- **파일 수준** `static int n;` — 바꾸는 것은 **연결**이다(외부 → 내부).\
  저장 기간은 원래도 정적이고 그대로다. 다른 `.c` 에서 못 본다.
- 같은 낱말이 **자리에 따라 다른 축을 건드린다** — 이 주제에서 가장 헷갈리는 자리다.\
  정본은 목록의 **29번 주제**.

**아무 지정자도 안 쓰면**

- 블록 안 — **자동 저장 기간 · 연결 없음**. `&a` 가 스택 주소(`0x7fff…`)로 나온 이유다.
- 파일 수준 — **정적 저장 기간 · 외부 연결**. `&file_static` 이 전혀 다른 자릿수(`0x639c…`)인 이유다.

**`register` 의 주소**

- **컴파일 에러**다 — `error: address of register variable ‘r’ requested`.
- 표준이 강제하는 것은 **이 제약뿐**이고, 실제로 레지스터에 둘지는 구현 마음이다(구현 정의).\
  현대 컴파일러는 대개 무시한다 — 레지스터 배치는 이미 최적화기의 일이다.

### 7. 링커에게 물어보기

**출력**

```text
$ gcc -std=c17 -c a.c -o a.o && nm a.o
                 U printf
                 U puts
000000000000001a T exported
0000000000000000 t helper
0000000000000000 d hidden
0000000000000004 D shared
```

```text
$ gcc -std=c17 -Wall -Wextra a.c b.c -o out
/usr/bin/ld: /tmp/ccMiixhs.o: in function `main':
b.c:(.text+0x2b): undefined reference to `hidden'
/usr/bin/ld: b.c:(.text+0x46): undefined reference to `helper'
collect2: error: ld returned 1 exit status
```

**왜 그런가**

```text
  a.c                              b.c
  static int hidden = 1;           extern int hidden;   <- 선언은 된다
  static void helper(void){}       void helper(void);   <- 선언은 된다
  int shared = 2;                  extern int shared;
  void exported(void){}            void exported(void);

  nm 에서:                          링크에서:
    d hidden   (소문자 = 내부)        undefined reference to `hidden'
    t helper   (소문자 = 내부)        undefined reference to `helper'
    D shared   (대문자 = 외부)        OK
    T exported (대문자 = 외부)        OK
```

- `nm` 의 **대소문자가 연결을 그대로 보여 준다** — 대문자면 외부, 소문자면 내부.\
  (`T`/`t` 는 코드 영역, `D`/`d` 는 초기화된 데이터 영역, `U` 는 정의가 없어 다른 곳에서 찾아야 하는 것.)
- **컴파일은 통과하고 링크에서 터진다.** `b.c` 만 보면 `extern int hidden;` 은 흠잡을 데 없는 선언이다.\
  「정의가 어디 있는가」는 컴파일러가 보는 범위(번역 단위) 밖이라 **링커만 알 수 있다.**
- 그 차이가 중요한 이유: 에러 메시지가 나오는 단계로 **원인의 종류가 갈린다.**\
  컴파일 에러면 그 파일 안에 원인이 있고, 링크 에러면 **파일 사이의 문제**다.\
  정본은 목록의 **45번 주제**.

### 8. 안에서 밖으로 — 규칙 세 줄

**규칙**

```text
① 이름에서 출발한다.
② 오른쪽을 먼저 본다 — [](배열)와 ()(함수)는 *보다 세다.
③ 오른쪽에 더 볼 게 없으면 왼쪽의 * 를 본다.
   괄호가 있으면 괄호 안을 다 끝내고 밖으로 나간다.
```

**`*` 와 `[]`**

- **`[]` 가 먼저 붙는다.** `int *p[10]` 은 「배열」이 바깥이다.
- 뒤집으려면 **괄호**를 쓴다. `int (*p)[10]` 은 「포인터」가 바깥이다.
- 함수의 `()` 도 같다 — `int *f(int)` 는 함수, `int (*f)(int)` 는 포인터.

**식의 우선순위와 같은 것은 우연인가**

- **우연이 아니라 설계다.** C 의 선언 문법은 「**선언은 사용을 닮는다**」는 원칙 위에 서 있다.\
  선언에 적은 모양 그대로 식에 쓰면 왼쪽의 기본 타입이 나오게 만든 것이다.

```text
선언   int  *p[10];        "*p[3] 라고 쓰면 int 가 나온다"
사용        *p[3]   ->  int

선언   int (*p)[10];       "(*p)[3] 이라고 쓰면 int 가 나온다"
사용       (*p)[3]  ->  int
```

- 실제로 `_Generic` 으로 찍어 확인했다.

```text
선언 int *pa[3] 에서 *pa[1] 을 쓰면 타입은 int
선언 int (*ap)[3] 에서 (*ap)[1] 을 쓰면 타입은 int
```

- 그래서 **식의 우선순위를 알면 선언의 우선순위를 따로 외울 필요가 없다.**\
  같은 규칙 하나다. `()`·`[]` 가 후위 연산자라 전위 `*` 보다 세다는 그것.
- *(「선언은 사용을 닮는다」는 C 설계의 원칙으로 널리 쓰이는 표현이고, 이 문서는 표준 문서 본문으로 접지하지 않았다 — 위 `_Generic` 출력이 이 환경에서의 실측 근거다.)*

### 9. 다차원 배열을 잘못 받으면

**출력**

```text
ex2.c:7:27: warning: passing argument 1 of ‘bad’ from incompatible pointer type [-Wincompatible-pointer-types]
ex2.c:2:16: note: expected ‘int **’ but argument is of type ‘int (*)[4]’
--- 실행 ---
good: 5
same: 5
세그멘테이션 오류 (exit 139)
```

**`good` 과 `same`**

- 둘 다 **`5`** 를 찍는다. **완전히 같다.**
- 매개변수 자리의 `[]` 는 **언제나 `*` 로 바뀐다.** `int p[][4]` 는 컴파일러에게 `int (*p)[4]` 와 글자만 다른 것이다.

**`bad(a)` 는**

- **경고다.** 에러가 아니라 실행 파일이 만들어진다.
- `note` 줄이 원인을 정확히 말해 준다 — `expected ‘int **’ but argument is of type ‘int (*)[4]’`.

**`p[1]` 이 읽는 값**

```text
a 의 메모리 (int 4바이트씩 연속 12개)

  +---+---+---+---+---+---+---+---+---+----+----+----+
  | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
  +---+---+---+---+---+---+---+---+---+----+----+----+
   ^^^^^^^^^^^^^^^  ^^^^^^^^
   int** 로 보면     int** 로 보면
   pp[0] (8바이트)   pp[1] (8바이트)  <- 3 과 4 의 비트를 주소로 읽는다

  int (*)[4] 로 보면
   p[0] = 행 0 (16바이트)   p[1] = 행 1 -> p[1][0] = 5   (맞다)
```

실제로 찍어 확인했다.

```text
a 의 8바이트째부터 8바이트를 주소로 읽으면 0x400000003
pp[1] = 0x400000003
```

- `int **` 로 보면 `p[1]` 은 **`a[0][2]`(값 3)와 `a[0][3]`(값 4)의 비트를 이어 붙인 8바이트**를 주소로 읽는다.\
  리틀 엔디언이라 `0x00000004_00000003` = `0x400000003`.
- 그 주소를 역참조해서 죽었다.

**운이 좋은 이유**

- `0x400000003` 은 매핑되지 않은 영역이라 **바로 SEGV 가 났다.**
- 배열 값이 달라 그 비트가 **유효한 주소 범위에 떨어지면 안 죽는다.** 조용히 엉뚱한 값을 읽고 계속 돈다.
- **「죽었다」가 이 버그의 성질이 아니다.** 성질은 「타입이 틀렸다」이고, 죽는지 여부는 그날의 데이터가 정한다.\
  이 갈래의 제1 규칙 — **「안 터졌다」는 「안전하다」가 아니다.**

### 10. 함수 인자는 어느 쪽부터 평가되는가

**출력**

```text
gcc -O0  : 3 2 1
gcc -O1  : 3 2 1
gcc -O2  : 3 2 1
gcc -O3  : 3 2 1
gcc -Os  : 3 2 1
clang -O0  : 1 2 3
clang -O2  : 1 2 3
--- ubsan 이 잡나 ---
3 2 1
```

**왜 그런가**

- **gcc 는 오른쪽부터, clang 은 왼쪽부터** 평가했다. 같은 소스·같은 머신이다.
- gcc 안에서는 **최적화 수준 다섯 개가 전부 같았다** — 그래서 더 위험하다.\
  한 컴파일러만 다섯 번 돌려 보고 「이렇게 된다」고 적으면 틀린다.

**어느 층인가**

- **미명시(unspecified)** 다.
  - 표준이 정한 것 ✗ — 순서를 정하지 않았다.
  - 구현 정의 ✗ — 문서화 의무가 없다.
  - **미명시 ✓** — 여러 가능성 중 하나를 고르되 알릴 의무가 없다.
  - UB ✗ — 아무 일이나 일어나는 게 아니라 **셋 중 하나의 순서**로는 간다.
- 다만 같은 객체를 한 식에서 두 번 이상 **바꾸면** 그때는 UB 로 올라간다 — 정본은 [목록의 **10번 주제**](../10-evaluation-order-and-sequence-points/).

**sanitizer 가 잡는가**

- **안 잡는다.** 위 출력의 마지막 줄이 `-fsanitize=undefined` 로 돌린 것인데 아무 말 없이 `3 2 1` 을 찍었다.
- 이유: sanitizer 는 **UB 를 잡는 도구**다. 미명시는 UB 가 아니라 **허용된 선택**이라 잡을 근거가 없다.
- 그래서 **미명시가 네 층 중 가장 조용하다.**

```text
        표준이 정한 것   구현 정의       미명시          UB
        --------------  -------------  -------------  --------------
 문서    표준 문서        구현 문서       없음           표준이 "정의 안 함"
 도구    (필요 없음)      매크로/헤더     ★ 없다          sanitizer
 증상    없음             환경 따라 다름   조용히 다름     아무거나
```

### 11. 다른 주제와 잇기

**언제 `typedef` 로 자르나**

- **괄호가 두 겹 이상 되면** 자른다.
- `int (*f)(int)` 는 한 겹이라 그냥 쓴다. `char *(*ft[3])(int)` 는 두 겹이라 자른다.
- 더 실용적인 기준 한 줄: **헤더에 쓸 것이면 무조건 자른다.** 호출자가 읽어야 하기 때문이다.

**매개변수 자리의 `int a[10]`**

```text
ex3.c:2:64: warning: ‘sizeof’ on array function parameter ‘a’ will return size of ‘int *’ [-Wsizeof-array-argument]
호출자 sizeof(a) = 40
함수 안 sizeof(a) = 8
```

- 함수 안에서는 **8** 이다 — 포인터의 크기.
- 매개변수 자리의 `[]` 는 `*` 로 바뀌므로 `void f(int a[10])` 은 `void f(int *a)` 와 완전히 같다.\
  `10` 은 **문서 효과뿐**이고 컴파일러는 검사하지 않는다.
- gcc 는 이 자리에 전용 경고 `-Wsizeof-array-argument` 를 준다.\
  이것은 **플래그를 하나도 안 줘도 나온다** — `-Wint-conversion`·`-Wincompatible-pointer-types` 도 마찬가지로 기본이다.\
  (세 경고를 `gcc -std=c17 -c` 만으로 돌려 확인했다.)\
  정본은 [목록의 **16번 주제**](../16-array-pointer-decay-and-function-parameters/).

**선언 문법 자체로 UB 가 되는 자리가 있는가**

- **없다.** 이 주제에서 잘못 쓴 것들은 전부 **컴파일 에러나 경고**로 나온다.
- UB 는 **잘못 선언한 포인터로 실제로 접근하는 순간** 시작된다.\
  9번의 `bad(a)` 가 그 경계다 — 선언(경고) → 호출(경고) → **`p[1][0]` 역참조(UB)**.
- 그래서 이 주제의 실무 결론은 **경고를 에러로 올리는 것**이다.\
  `-Werror=incompatible-pointer-types` 하나만 켜도 9번은 링크까지 못 간다.

```text
  선언이 틀림           호출이 틀림           접근함
      |                     |                  |
   경고/에러             경고                 ★ UB 시작
   (컴파일러가 봄)      (컴파일러가 봄)      (아무도 안 봄 — sanitizer 만)
```

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 플래그로 돌렸나 |
|---|---|---|
| 선언 크기 비교 | `int *p[10]`·`int (*p)[10]`·`int (*f)(int)` 의 `sizeof` 와 `p2+1` 의 보폭 | `-std=c17 -Wall -Wextra` |
| 함수 포인터 배열 | `char *(*ft[3])(int)` 선언·호출·`typedef` 등가 | `-std=c17 -Wall -Wextra` |
| `int *p, q;` | `q` 가 `int` 임 · `-Wint-conversion` 경고 · 주소 절단값 | `-std=c17 -Wall -Wextra` |
| `const` 다섯 줄 | (2)(3)(5)만 에러 · `location` 대 `variable` 문구 | `-std=c17 -Wall -Wextra -c` |
| `noproto(1,2,3)` | C17 무진단 · `-Wstrict-prototypes` 로만 경고 · **C2x 에서 에러** | `-std=c17` · `-std=c17 -Wstrict-prototypes` · `-std=c2x` |
| 저장 클래스 | 자동/정적 주소 영역 · `register` 주소 에러 · `auto` 가 c2x 에서도 저장 클래스 | `-std=c17` · `-std=c2x` |
| 분할 컴파일 `a.c`+`b.c` | `nm` 대소문자 · `undefined reference` 링크 에러 | `-std=c17 -Wall -Wextra` · `nm` |
| 인자 평가 순서 | gcc `3 2 1` ↔ clang `1 2 3` · 최적화 5수준 불변 · ubsan 무반응 | gcc `-O0/-O1/-O2/-O3/-Os` · clang `-O0/-O2` · `-fsanitize=undefined` |
| 다차원 배열 3형태 | `good`/`same` 동일 · `bad` 는 경고 후 SEGV · `pp[1] = 0x400000003` | `-std=c17 -Wall -Wextra` |
| `sizeof` 매개변수 배열 | 호출자 40 ↔ 함수 안 8 · `-Wsizeof-array-argument` | `-std=c17 -Wall -Wextra` |

**구현 의존 항목** — 이 표의 값 중 다음은 **이 환경(x86-64 Linux · LP64 · gcc 13.3.0)에서만** 그렇다.

- 포인터 크기 8 → `sizeof p1`=80 · `sizeof ft`=24 가 전부 여기서 나온다.
- 스택·정적 영역의 주소 자릿수(ASLR 때문에 실행마다 다르다).
- **인자 평가 순서** — 컴파일러가 바뀌면 바뀐다(clang 에서 실제로 반대였다).
- `-Wstrict-prototypes`·`-Wsizeof-array-argument` 의 존재와 문구는 gcc 의 것이다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- `-std=c23` 이 생기면 5번·「더 들어가면」의 `typeof`·`static_assert` 를 다시 던진다(지금은 `-std=c2x` 로만 확인).
- gcc 가 올라가면 인자 평가 순서를 다시 찍는다 — **보장이 아니라 관찰**이다.
