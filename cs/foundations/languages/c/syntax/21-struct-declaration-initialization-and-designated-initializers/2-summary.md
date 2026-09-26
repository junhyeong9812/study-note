# c/syntax/21 — 구조체 선언·초기화·지정 초기자: 「**구조체는 값이고, 배열은 값이 아니다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — struct](https://en.cppreference.com/w/c/language/struct) · [cppreference — struct initialization](https://en.cppreference.com/w/c/language/struct_initialization) · [cppreference — compound literals](https://en.cppreference.com/w/c/language/compound_literal) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html)
> **실행 검증** — 이 문서의 모든 출력·진단·sanitizer 리포트는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과 **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 플래그는 `-std=c17 -Wall -Wextra -pedantic` 이고, 갈리는 자리는 **`-O0`\~`-O3` 를 따로 돌렸다.**\
> 소스는 `s21a.c`\~`s21h.c` 와 `s21g.cpp` 다. **손으로 옮겨 적은 수치는 하나도 없다.**
> **버전** — 구조체 자체는 **C89부터**. **지정 초기자와 복합 리터럴은 C99부터**,\
> **익명 구조체 멤버는 C11부터**, **빈 중괄호 `= {}` 는 C23부터**다(이 머신의 gcc 13 은 `-std=c2x` 로 확인했다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> **경계** — 「**구조체 패딩·정렬**」의 정본은 [22번 형제](../22-struct-padding-and-alignment/)다. 여기는 **선언·초기화·대입**까지다.\
> 「`sizeof`·`_Alignof`·`offsetof` 라는 도구」는 [08번 형제](../08-sizeof-alignment-and-offsetof/), 「`union`」은 [23번 형제](../23-union-and-the-boundary-of-type-punning/)가 정본이다.\
> 「복합 리터럴」의 정본은 [목록의 **27번 주제**](../27-compound-literals/)다 — 여기서는 **저장 기간만** 본다.

## 한눈에 — 쉽게 말하면

**구조체는 「서류 양식 한 장」이다.** 칸이 여럿이지만 **들고 다닐 때는 한 장으로 다닌다.**

그래서 복사기에 넣으면 **칸 안에 그려 넣은 표까지 통째로 복사된다.**\
그런데 그 표만 따로 떼어 복사하려 하면 — **C 는 그것을 거절한다.** 배열은 값이 아니기 때문이다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **서류 양식 한 장** | `struct` 변수 — 멤버가 여럿이어도 **하나의 값**이다 |
| 양식을 **복사기에 넣는다** | `b = a;` — 구조체 대입. **멤버별 복사**가 일어난다 |
| 칸 안에 그려 넣은 **표까지 따라 복사된다** | ★ **배열 멤버도 복사된다** |
| **표만 떼어 복사**하려 한다 | `b = a;` 에서 `a` 가 맨 배열일 때 — **컴파일 에러** |
| 칸 **이름을 적어** 채운다 | **지정 초기자** `.retry = 3` (C99부터) |
| 안 채운 칸은 **0 으로 인쇄돼 나온다** | 안 적은 멤버는 **정적 초기화 규칙**을 따른다 |
| **그 자리에서 만든 임시 양식** | **복합 리터럴** `(struct P){1, 2}` (C99부터) |
| 임시 양식은 **책상을 떠나면 사라진다** | 블록 스코프 복합 리터럴 = **자동 저장 기간** |
| 게시판에 붙인 양식은 **안 사라진다** | 파일 스코프 복합 리터럴 = **정적 저장 기간** |

```text
   struct Rec a = { 7, "kim", 1.5 };
   struct Rec b;
   b = a;                       <- 한 줄로 전부 복사된다

   a                            b
   +------+----------+------+   +------+----------+------+
   | id 7 | "kim"    | 1.5  |   | id 7 | "kim"    | 1.5  |
   +------+----------+------+   +------+----------+------+
            ^^^^^                        ^^^^^
            배열 멤버                     ★ 따라왔다 (다른 메모리에)

   char x[8] = "kim", y[8];
   y = x;                       <- ★ 이것은 에러다
```

- 위의 두 「복사」가 **문법적으로 다른 일**이라는 것이 이 주제의 축이다.
- 구조체는 **값**이라 대입·인자 전달·반환이 되고, 배열은 **값이 아니라서** 그 셋이 전부 안 된다.

> **집합체(aggregate)** — 멤버를 모아 놓은 타입. C 에서는 **구조체와 배열**이 집합체다.\
> 예: `struct Rec` 도 `char[8]` 도 집합체이고, 둘 다 중괄호로 초기화한다.

> **지정 초기자(designated initializer)** — 초기자에서 **멤버 이름을 찍어** 값을 주는 문법.\
> 예: `struct Cfg d = { .retry = 3 };` 는 `retry` 만 3 이고 **나머지는 0** 이 된다. C99부터다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 구조체 **대입**은 정확히 무엇을 복사하는가 — 배열 멤버는 따라오는가, 왜 맨 배열은 대입이 안 되는가.
2. 초기자에 **안 적은 멤버**는 무엇이 되는가 — 그리고 컴파일러는 어느 꼴에만 경고하는가.
3. **복합 리터럴**은 어디에 살고 언제 죽는가 — 그 수명을 넘겨 읽으면 무엇이 보이는가.

## 동작 방식

### (1) ★★★ 대입은 멤버별 복사다 — 배열 멤버도 따라온다

**언제 쓰나** — 구조체를 함수에 넘기거나, 스냅샷을 떠 두거나, 설정을 한 벌 더 만들 때.

```c
/* s21a.c */
#include <stdio.h>
#include <string.h>

struct Rec {
    int  id;
    char name[8];      /* ★ 배열 멤버 */
    double rate;
};

int main(void) {
    struct Rec a = { 7, "kim", 1.5 };     /* 선언 + 초기화 */
    struct Rec b;                          /* 선언만 — 불확정 */
    b = a;                                 /* ★ 구조체 대입 */

    b.id = 9;
    b.name[0] = 'L';

    printf("a = { %d, \"%s\", %.1f }\n", a.id, a.name, a.rate);
    printf("b = { %d, \"%s\", %.1f }\n", b.id, b.name, b.rate);
    printf("a.name 과 b.name 은 같은 메모리인가 : %d  (0 이면 다른 메모리)\n",
           a.name == b.name);
    printf("배열 멤버가 따라왔나 : memcmp(a.name+1, b.name+1, 7) = %d\n",
           memcmp(a.name + 1, b.name + 1, 7));

    char x[8] = "kim", y[8];
    /* y = x;  <- 배열은 대입이 안 된다. 아래 블록에서 던진다 */
    memcpy(y, x, sizeof y);
    printf("맨 배열은 memcpy 로만 : y = \"%s\"\n", y);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s21a.c -o x ; ./x (cc exit=0 · run exit=0) =====
a = { 7, "kim", 1.5 }
b = { 9, "Lim", 1.5 }
a.name 과 b.name 은 같은 메모리인가 : 0  (0 이면 다른 메모리)
배열 멤버가 따라왔나 : memcmp(a.name+1, b.name+1, 7) = 0
맨 배열은 memcpy 로만 : y = "kim"
```

```text
   b = a;   가 실제로 하는 일

   a                                   b
   +--------+------------+--------+    +--------+------------+--------+
   | id  7  | 'k''i''m'0 | 1.5    | -> | id  7  | 'k''i''m'0 | 1.5    |
   +--------+------------+--------+    +--------+------------+--------+
     4바이트    8바이트     8바이트         ★ 전부 복사된다

   그 뒤 b 만 고치면
   b.id = 9; b.name[0] = 'L';
   +--------+------------+--------+    +--------+------------+--------+
   | id  7  | 'k''i''m'0 | 1.5    |    | id  9  | 'L''i''m'0 | 1.5    |
   +--------+------------+--------+    +--------+------------+--------+
     a 는 그대로다                        ★ 따로 산다 (별칭이 아니다)
```

그림 해설 (한 단계씩).

- `a.name == b.name` 이 **0** 이다. 두 배열이 **다른 메모리**라는 뜻이다 — **별칭이 아니라 복사본**이다.
- `memcmp(a.name + 1, b.name + 1, 7)` 이 **0** 이다. 첫 글자만 고쳤으니 **나머지 7바이트가 같다** — **배열 멤버가 통째로 따라왔다**는 증거다.
- 그런데 같은 파일에서 `y = x` 는 **못 쓴다.** 맨 배열은 `memcpy` 로만 옮긴다.

비용 — **구조체 대입은 크기만큼의 복사**다. `sizeof` 가 큰 구조체를 값으로 넘기면 그만큼 든다.\
★ 그것이 큰 구조체를 **포인터로 넘기는** 이유다.

### (1-나) ★★ 배열은 왜 안 되나 — 에러 전문

**언제 쓰나** — 「구조체는 되는데 배열은 왜 안 되지」에서 막혔을 때.

```c
/* s21f.c */
struct P { int x, y; };

int main(void) {
    char a[4] = "abc", b[4];
    struct P s = { 1, 2 }, t = { 1, 2 };
    int arr[3];

    b = a;                      /* (1) 배열은 대입이 안 된다 */
    if (s == t) return 1;       /* (2) 구조체는 == 가 없다 */
    arr = (int[3]){1, 2, 3};    /* (3) 복합 리터럴도 배열이면 마찬가지 */
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s21f.c -o x (cc exit=1) =====
s21f.c: In function ‘main’:
s21f.c:8:7: error: assignment to expression with array type
    8 |     b = a;                      /* (1) 배열은 대입이 안 된다 */
      |       ^
s21f.c:9:11: error: invalid operands to binary == (have ‘struct P’ and ‘struct P’)
    9 |     if (s == t) return 1;       /* (2) 구조체는 == 가 없다 */
      |           ^~
s21f.c:10:9: error: assignment to expression with array type
   10 |     arr = (int[3]){1, 2, 3};    /* (3) 복합 리터럴도 배열이면 마찬가지 */
      |         ^
s21f.c:6:9: warning: variable ‘arr’ set but not used [-Wunused-but-set-variable]
    6 |     int arr[3];
      |         ^~~
s21f.c:4:24: warning: variable ‘b’ set but not used [-Wunused-but-set-variable]
    4 |     char a[4] = "abc", b[4];
      |                        ^
```

```text
   구조체              배열
   +---------------+   +---------------+
   | b = a;   OK   |   | b = a;   에러 |   assignment to expression with array type
   | f(s);    OK   |   | f(x);    ★ 포인터로 감쇠해 넘어간다
   | return s; OK  |   | return x; ★ 포인터가 돌아간다
   | s == t;  에러 |   | x == y;  ★ 주소 비교가 된다 (내용 비교가 아니다)
   +---------------+   +---------------+
```

- 세 줄 중 **둘이 같은 에러**다 — `assignment to expression with array type`.\
  `arr = (int[3]){1,2,3}` 도 마찬가지다. **오른쪽이 복합 리터럴이어도 왼쪽이 배열이면 안 된다.**
- 가운데 줄은 다른 에러다 — `invalid operands to binary ==`. ★ **구조체에는 `==` 가 아예 없다.**
- ★ **「그럼 `memcmp` 로 비교하면 되겠네」가 이 주제에서 가장 비싼 오해**다.\
  그 이유는 [22번 형제](../22-struct-padding-and-alignment/)가 바이트로 보여 준다 — **패딩 때문이다.**
- 꼬리의 경고 두 줄(`-Wunused-but-set-variable`)은 **에러와 무관한 잡음**이다. 그래도 **블록에서 지우지 않았다.**

비용 — 에러는 **컴파일 타임**에 난다. 이 층은 **공짜로 막아 주는 층**이다.

### (2) ★★★ 지정 초기자 — 안 적은 멤버는 0 이 된다

**언제 쓰나** — 멤버가 많은 설정 구조체를 만들 때. 멤버가 **나중에 늘어날** 구조체일 때 특히.

```c
/* s21b.c */
#include <stdio.h>

struct Cfg { int port; int retry; char host[8]; double t; };

static void dump(const char *tag, struct Cfg c) {
    printf("%-14s port=%d retry=%d host=\"%s\" t=%.1f\n",
           tag, c.port, c.retry, c.host, c.t);
}

int main(void) {
    struct Cfg z = {0};                              /* 전부 0 */
    struct Cfg p = { 80 };                           /* 부분 초기화 */
    struct Cfg d = { .retry = 3, .host = "a" };      /* 지정 초기자 (C99) */
    struct Cfg m = { 8080, .t = 0.5 };               /* 섞어 쓰기 */

    dump("= {0}", z);
    dump("= { 80 }", p);
    dump(".retry .host", d);
    dump("8080, .t", m);

    printf("\n안 적은 멤버는 정적 초기화 규칙을 따른다 — 0 / 0.0 / '\\0'\n");
    printf("d.port = %d · d.t = %.1f · d.host[1] = %d\n", d.port, d.t, d.host[1]);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s21b.c -o x ; ./x (cc exit=0 · run exit=0) =====
= {0}          port=0 retry=0 host="" t=0.0
= { 80 }       port=80 retry=0 host="" t=0.0
.retry .host   port=0 retry=3 host="a" t=0.0
8080, .t       port=8080 retry=0 host="" t=0.5

안 적은 멤버는 정적 초기화 규칙을 따른다 — 0 / 0.0 / '\0'
d.port = 0 · d.t = 0.0 · d.host[1] = 0
```

```text
   struct Cfg { int port; int retry; char host[8]; double t; };

   = {0}                 = { 80 }              = { .retry = 3, .host = "a" }
   +------+------+---+   +------+------+---+   +------+------+---+
   | port |   0  |   |   | port |  80  |   |   | port |   0  |   |
   | retry|   0  |   |   | retry|   0  | ★ |   | retry|   3  |   |
   | host |  ""  |   |   | host |  ""  | ★ |   | host | "a"  |   |
   | t    |  0.0 |   |   | t    |  0.0 | ★ |   | t    |  0.0 | ★ |
   +------+------+---+   +------+------+---+   +------+------+---+
     전부 0              앞에서부터 채우고        이름으로 찍고
                         ★ 나머지는 0            ★ 나머지는 0
```

그림 해설 (한 단계씩).

- 세 꼴 모두 **안 적은 멤버가 0** 이다. 「쓰레기 값」이 아니다.
- 규칙은 하나다 — **초기자가 하나라도 있으면**, 안 적은 멤버는 **정적 저장 기간 객체와 같은 규칙**으로 초기화된다.\
  정수는 `0`, 부동소수는 `0.0`, 포인터는 널 포인터, 배열은 **원소마다 그 규칙을 다시 적용**한다.
- 출력의 마지막 줄이 그것이다 — `d.port = 0` · `d.t = 0.0` · `d.host[1] = 0`.
- ★ **`= {0}` 과 `= { }`(C23) 와 지정 초기자는 전부 이 규칙 하나의 얼굴**이다.
- ★★ **초기자를 아예 안 주면 이야기가 완전히 다르다** — 자동 저장 기간 객체는 **불확정**이다.\
  그 정본은 [목록의 **30번 주제**](../30-initialization-rules-and-indeterminate-values/)다.

비용 — **컴파일러가 0 으로 채운다.** 큰 구조체에 `= {0}` 을 쓰면 그만큼의 쓰기가 실제로 일어난다.

### (2-나) ★★★ 그런데 경고는 **한 꼴에만** 붙는다

**언제 쓰나** — 「`-Wall -Wextra` 를 켰으니 초기화 누락은 잡히겠지」라고 믿을 때.

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s21b.c -o x (cc exit=0) =====
s21b.c: In function ‘main’:
s21b.c:12:12: warning: missing initializer for field ‘retry’ of ‘struct Cfg’ [-Wmissing-field-initializers]
   12 |     struct Cfg p = { 80 };                           /* 부분 초기화 */
      |            ^~~
s21b.c:3:28: note: ‘retry’ declared here
    3 | struct Cfg { int port; int retry; char host[8]; double t; };
      |                            ^~~~~
```

```text
   같은 파일 안의 네 꼴

   struct Cfg z = {0};                          -> 경고 0건
   struct Cfg p = { 80 };                       -> ★ 1건 (-Wmissing-field-initializers)
   struct Cfg d = { .retry = 3, .host = "a" };  -> 경고 0건
   struct Cfg m = { 8080, .t = 0.5 };           -> 경고 0건
                                                   -------------------
                                                   ★ 네 꼴이 전부 「일부만 적은」 것인데
                                                      경고는 한 줄에만 붙었다
```

- **의미는 넷 다 같다** — 안 적은 멤버는 0 이다. 그런데 **경고는 하나뿐**이다.
- ★★ **`-Wmissing-field-initializers` 는 「위치 초기자가 멤버 수보다 적은 것」만 본다.**\
  `= {0}` 은 **특별 취급으로 빠지고**, **지정 초기자는 애초에 대상이 아니다.**
- ★ 그래서 이 경고를 **「초기화 누락 검사」로 읽으면 안 된다.** 그것은 **꼴을 보는 경고**이지 **뜻을 보는 경고**가 아니다.
- ★★ 뒤집으면 실무 규칙이 나온다 — **멤버가 늘어날 구조체는 지정 초기자로 쓴다.**\
  멤버를 하나 더 붙여도 **기존 초기자가 전부 그대로 맞고**, 새 멤버는 **0 이 된다.**

비용 — 경고를 끄지 않고도 **조용히 지나가는 자리**가 생긴다. **경고 0건이 「다 적었다」가 아니다.**

### (3) ★★ 순서 밖·중복 지정 — C 는 받아 준다

**언제 쓰나** — 초기자를 **읽기 좋은 순서**로 적고 싶을 때. 매크로로 초기자를 조립할 때.

```c
/* s21c.c */
#include <stdio.h>

struct P { int a, b, c; };

int main(void) {
    struct P s = { .c = 3, .a = 1 };        /* ★ 순서 밖 — C 는 된다 */
    struct P t = { .a = 1, .a = 9 };        /* ★ 같은 멤버를 두 번 */
    int arr[6] = { [4] = 40, [1] = 10 };    /* 배열 지정 초기자 */

    printf("s = { %d, %d, %d }\n", s.a, s.b, s.c);
    printf("t = { %d, %d, %d }   <- 뒤엣것이 이긴다\n", t.a, t.b, t.c);
    printf("arr =");
    for (int i = 0; i < 6; i++) printf(" %d", arr[i]);
    printf("\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s21c.c -o x ; ./x (cc exit=0 · run exit=0) =====
s = { 1, 0, 3 }
t = { 9, 0, 0 }   <- 뒤엣것이 이긴다
arr = 0 10 0 0 40 0
```

```text
   struct P { int a, b, c; };

   { .c = 3, .a = 1 }            { .a = 1, .a = 9 }         int arr[6] = { [4]=40, [1]=10 }

   적은 순서: c -> a              같은 칸을 두 번              칸 번호로 찍는다
   +---+---+---+                 +---+---+---+              +--+--+--+--+--+--+
   | 1 | 0 | 3 |                 | 9 | 0 | 0 |              | 0|10| 0| 0|40| 0|
   +---+---+---+                 +---+---+---+              +--+--+--+--+--+--+
     a   b   c                     ★ 뒤엣것이 이긴다           ★ 안 찍은 칸은 0
   ★ 선언 순서로 채워진다
```

그림 해설 (한 단계씩).

- **적은 순서와 채워지는 자리는 무관**하다 — `.c` 를 먼저 적어도 `c` 자리에 들어간다.
- 같은 멤버를 두 번 적으면 **뒤엣것이 이긴다.** 이것은 에러가 아니라 **정의된 동작**이다.
- 배열에도 같은 문법이 있다 — `[4] = 40`. ★ **찍지 않은 칸은 0** 이다.

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s21c.c -o x (cc exit=0) =====
s21c.c: In function ‘main’:
s21c.c:7:33: warning: initialized field overwritten [-Woverride-init]
    7 |     struct P t = { .a = 1, .a = 9 };        /* ★ 같은 멤버를 두 번 */
      |                                 ^
s21c.c:7:33: note: (near initialization for ‘t.a’)
```

- 중복 지정에는 **경고 한 건**이 붙는다 — `-Woverride-init`. **`cc exit=0`** 이므로 **컴파일은 된다.**
- ★ **순서 밖 지정에는 경고가 없다.** 그것은 **정상적인 C** 이기 때문이다.

비용 — 없다. **컴파일 타임에 전부 끝난다.**

### (3-나) ★★★ 그런데 **C++ 는 이것을 거절한다**

**언제 쓰나** — 헤더를 C 와 C++ 양쪽에서 include 할 때. C 코드를 C++ 로 옮길 때.

```cpp
/* s21g.cpp */
#include <cstdio>

struct P { int a, b, c; };

int main() {
    P s = { .c = 3, .a = 1 };     /* C 에서는 되던 순서 밖 지정 초기자 */
    std::printf("%d %d %d\n", s.a, s.b, s.c);
    return 0;
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic s21g.cpp -o x (cc exit=1) =====
s21g.cpp: In function ‘int main()’:
s21g.cpp:6:13: warning: C++ designated initializers only available with ‘-std=c++20’ or ‘-std=gnu++20’ [-Wc++20-extensions]
    6 |     P s = { .c = 3, .a = 1 };     /* C 에서는 되던 순서 밖 지정 초기자 */
      |             ^
s21g.cpp:6:21: warning: C++ designated initializers only available with ‘-std=c++20’ or ‘-std=gnu++20’ [-Wc++20-extensions]
    6 |     P s = { .c = 3, .a = 1 };     /* C 에서는 되던 순서 밖 지정 초기자 */
      |                     ^
s21g.cpp:6:28: warning: missing initializer for member ‘P::a’ [-Wmissing-field-initializers]
    6 |     P s = { .c = 3, .a = 1 };     /* C 에서는 되던 순서 밖 지정 초기자 */
      |                            ^
s21g.cpp:6:28: warning: missing initializer for member ‘P::b’ [-Wmissing-field-initializers]
s21g.cpp:6:28: error: designator order for field ‘P::a’ does not match declaration order in ‘P’
```

- C++17 에서는 **지정 초기자 문법 자체가 확장**이다 — `-Wc++20-extensions` 두 건.
- 그런데 **경고로 끝나지 않는다.** 마지막 줄이 **에러**다 —\
  `designator order for field 'P::a' does not match declaration order in 'P'`.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic s21g.cpp -o x (cc exit=1) =====
s21g.cpp: In function ‘int main()’:
s21g.cpp:6:28: warning: missing initializer for member ‘P::a’ [-Wmissing-field-initializers]
    6 |     P s = { .c = 3, .a = 1 };     /* C 에서는 되던 순서 밖 지정 초기자 */
      |                            ^
s21g.cpp:6:28: warning: missing initializer for member ‘P::b’ [-Wmissing-field-initializers]
s21g.cpp:6:28: error: designator order for field ‘P::a’ does not match declaration order in ‘P’
```

- **`-std=c++20` 으로 올려도 같은 에러**다. 확장 경고 두 건만 사라졌다.
- ★★★ 그러니까 **C++ 는 지정 초기자를 받아들인 뒤에도 「선언 순서」를 요구한다.**\
  C 는 **순서를 요구하지 않는다.** 이 한 줄이 두 언어의 갈림길이다.
- ★ **`cc exit=1`** 이 두 벌 다 같다 — **컴파일이 실패한 것**이지 경고가 아니다.
- C++ 의 중괄호 초기화 전반(`{}` 초기화·좁힘 변환 금지·초기화 리스트)은 **C++ 갈래가 정본**이다.\
  여기서는 **「C 에서 되던 것이 저기서 안 되는 자리」** 하나만 짚는다.

비용 — 헤더를 공유하면 **C 쪽에서 잘 돌던 초기자가 C++ 번역 단위에서 빌드를 깬다.**

### (4) ★ 중첩과 익명 구조체 — C11 부터

**언제 쓰나** — 구조체 안에 구조체를 둘 때. 한 단계를 **생략하고 싶을** 때.

```c
/* s21d.c */
#include <stdio.h>
#include <stddef.h>

struct Outer {
    int tag;
    struct Inner { int x, y; } in;   /* 중첩 — 안쪽 태그도 바깥 스코프에 생긴다 */
    struct { int u, v; };            /* ★ 익명 구조체 멤버 (C11) */
};

int main(void) {
    struct Outer o = { .tag = 1, .in = { .y = 20 }, .u = 5 };
    struct Inner i = { 7, 8 };       /* 바깥에서도 쓸 수 있다 */

    o.in.x = 9;
    o.v = 6;                         /* ★ 한 단계 없이 바로 */

    printf("o.tag=%d o.in={%d,%d} o.u=%d o.v=%d\n", o.tag, o.in.x, o.in.y, o.u, o.v);
    printf("i={%d,%d}\n", i.x, i.y);
    printf("offsetof: tag=%zu in=%zu in.x=%zu u=%zu v=%zu  sizeof=%zu\n",
           offsetof(struct Outer, tag), offsetof(struct Outer, in),
           offsetof(struct Outer, in.x), offsetof(struct Outer, u),
           offsetof(struct Outer, v), sizeof(struct Outer));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s21d.c -o x ; ./x (cc exit=0 · run exit=0) =====
o.tag=1 o.in={9,20} o.u=5 o.v=6
i={7,8}
offsetof: tag=0 in=4 in.x=4 u=12 v=16  sizeof=20
```

```text
   struct Outer {
       int tag;                          offset 0
       struct Inner { int x, y; } in;    offset 4   (in.x = 4, in.y = 8)
       struct { int u, v; };             offset 12  ★ 이름이 없다
   };

   +------+------+------+------+------+
   | tag  | in.x | in.y |  u   |  v   |
   +------+------+------+------+------+
      0      4      8     12     16      sizeof = 20

   o.in.x = 9;    <- 중첩은 한 단계 들어간다
   o.v    = 6;    <- ★ 익명은 바로 닿는다
```

그림 해설 (한 단계씩).

- **중첩 구조체의 태그는 바깥 스코프에 생긴다** — `struct Inner i = {7, 8};` 이 **바깥에서 된다.**\
  ★ 이것이 C++ 와 다른 자리다. C 에는 **클래스 스코프가 없다.**
- **익명 구조체 멤버는 이름이 없어서 `o.v` 로 바로 닿는다.** `offsetof` 로 자리를 찍어 보면 **12 와 16** 이다 —\
  **따로 떨어진 칸이 아니라 바깥 구조체 안에 펼쳐진 칸**이다.
- 초기화도 섞인다 — `{ .tag = 1, .in = { .y = 20 }, .u = 5 }`. **중첩 지정 초기자**가 그대로 된다.

```text
===== gcc -std=c99 -Wall -Wextra -pedantic s21d.c -o x (cc exit=0) =====
s21d.c:7:25: warning: ISO C99 doesn’t support unnamed structs/unions [-Wpedantic]
    7 |     struct { int u, v; };            /* ★ 익명 구조체 멤버 (C11) */
      |                         ^
```

- ★★ **익명 구조체는 C11 부터**다. `-std=c99 -pedantic` 으로 내리면 **한 줄로 말해 준다.**
- ★ **`-pedantic` 이 없으면 C99 에서도 말없이 통과한다.** 「`-std=c99` 로 돌렸다」는 「C99 로 검증했다」가 아니다.

비용 — 없다. 다만 **익명 멤버는 이름이 없어 `offsetof` 로만 자리를 물어볼 수 있다.**

### (5) ★★★ 복합 리터럴 — 이 주제의 UB 가 여기 있다

**언제 쓰나** — 임시 구조체를 **인자로 넘길** 때. 구조체를 **통째로 갈아 끼울** 때.

```c
/* s21e.c */
#include <stdio.h>

struct P { int x, y; };

static int sum(struct P p) { return p.x + p.y; }

static void blockscope(void) {
    for (int k = 0; k < 2; k++) {
        struct P *q = &(struct P){ .x = 1, .y = 2 };   /* 블록 안 복합 리터럴 */
        printf("  %d 바퀴: q->x=%d ", k, q->x);
        q->x = 99;                                     /* ★ 수정 가능한 lvalue */
        printf("-> 고치면 %d\n", q->x);
    }   /* <- 바퀴마다 여기서 수명이 끝나고 다음 바퀴에 다시 만들어진다 */
}

static struct P g = { 0 };
static struct P *gp = &(struct P){ 7, 8 };             /* 파일 스코프 = 정적 저장 기간 */

int main(void) {
    printf("인자로 넘기기 : sum((struct P){3,4}) = %d\n", sum((struct P){ 3, 4 }));
    g = (struct P){ .y = 5 };
    printf("통째로 대입   : g = {%d,%d}\n", g.x, g.y);
    printf("파일 스코프   : gp->x=%d gp->y=%d\n", gp->x, gp->y);
    printf("블록 스코프 — 자동 저장 기간이다\n");
    blockscope();
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s21e.c -o x ; ./x (cc exit=0 · run exit=0) =====
인자로 넘기기 : sum((struct P){3,4}) = 7
통째로 대입   : g = {0,5}
파일 스코프   : gp->x=7 gp->y=8
블록 스코프 — 자동 저장 기간이다
  0 바퀴: q->x=1 -> 고치면 99
  1 바퀴: q->x=1 -> 고치면 99
```

```text
   (struct P){ .x = 1, .y = 2 }   <- 이름 없는 객체가 「그 자리에」 만들어진다

   어디에 적었나                    저장 기간           언제 죽나
   ------------------------------  ----------------   ---------------------------
   함수 안 / 블록 안                자동               ★ 그 블록을 벗어날 때
   파일 스코프(전역)                정적               프로그램이 끝날 때
   for 문의 몸통 안                 자동               ★ 바퀴마다 죽고 다시 만들어진다

   sum((struct P){3, 4})           <- 인자로 넘긴다. 호출이 끝나면 끝
   g = (struct P){ .y = 5 };       <- 통째로 대입. ★ 안 적은 x 는 0 이다
   q->x = 99;                      <- ★ 수정 가능한 lvalue 다 (const 가 아니다)
```

그림 해설 (한 단계씩).

- 복합 리터럴은 「상수」가 아니라 「**객체**」다. 주소가 있고 **고칠 수 있다.**\
  출력의 `q->x=1 -> 고치면 99` 가 그 증거다.
- **for 두 바퀴가 둘 다 `1` 에서 시작**한다. ★ 바퀴마다 **새로 만들어진다**는 뜻이다 —\
  99 로 고친 것이 다음 바퀴로 넘어오지 않았다.
- `g = (struct P){ .y = 5 };` 는 **`{0,5}`** 다. ★ **지정 초기자 규칙이 그대로 적용**된다.
- 파일 스코프의 `gp` 는 **정적 저장 기간**이라 `main` 에서 읽어도 멀쩡하다.

> **복합 리터럴(compound literal)** — `(타입){초기자}` 꼴로 **그 자리에 이름 없는 객체를 만드는** 문법.\
> 예: `sum((struct P){3, 4})` 는 임시 구조체를 하나 만들어 넘긴다. C99부터다.

> **저장 기간(storage duration)** — 객체가 **언제 태어나 언제 죽는가**. 자동·정적·스레드·할당 네 가지다.\
> 예: 블록 안 복합 리터럴은 **자동**이라 그 블록을 벗어나면 죽는다.

비용 — 자동 저장 기간이면 **스택에 자리를 잡는다.** 큰 구조체를 루프 안에서 만들면 그만큼 쓴다.

### (5-나) ★★★ 수명이 끝난 뒤 읽으면 — **세 벌이 갈린다**

**언제 쓰나** — 복합 리터럴의 주소를 **돌려주고 싶어질** 때. 그 순간이 사고다.

```c
/* s21e2.c */
#include <stdio.h>

struct P { int x, y; };

static struct P *make(int v) {
    return &(struct P){ .x = v, .y = v * 10 };   /* ★ 함수가 끝나면 수명이 끝난다 */
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    fprintf(stderr, "--- (가) 복합 리터럴 주소를 반환받는다 ---\n");
    struct P *p = make(3);
    fprintf(stderr, "--- (나) 이제 역참조한다 ---\n");
    printf("p->x = %d p->y = %d\n", p->x, p->y);
    return 0;
}
```

`make()` 가 돌려준 것은 **함수 안에서 만든 복합 리터럴의 주소**다. 함수가 끝나면 그 객체는 이미 죽었다.

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s21e2.c -o x ; ./x (cc exit=0 · run exit=0) =====
--- (가) 복합 리터럴 주소를 반환받는다 ---
--- (나) 이제 역참조한다 ---
p->x = -1844605528 p->y = 25719
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 s21e2.c -o x ; ./x (cc exit=0 · run exit=0) =====
--- (가) 복합 리터럴 주소를 반환받는다 ---
--- (나) 이제 역참조한다 ---
p->x = 0 p->y = 0
```

```text
   같은 소스 · 같은 컴파일러 · -O 만 다르다

   -O0                              -O2
   p->x = (쓰레기) p->y = (쓰레기)   p->x = 0 p->y = 0
   ★ 죽은 스택 프레임을 그대로 읽었다  ★ 컴파일러가 「읽을 것이 없다」고 판단했다

   어느 쪽도 「맞는 답」이 아니다 — UB 에는 맞는 답이 없다.
```

- **`-O0` 은 쓰레기**가 나오고 **`-O2` 는 `0 0`** 이 나온다. **둘 다 `run exit=0`** 이다 — **안 죽는다.**
- ★★★ **「안 죽었으니 괜찮다」가 이 주제에서 가장 위험한 추론**이다.\
  UB 는 **죽는 것이 아니라 조용히 다른 것이 되는 것**이다.
- ★ `-O0` 쪽의 숫자는 **실행마다 달라진다.** 그 숫자를 답으로 외우면 안 된다 —\
  **외울 것은 「두 벌이 갈렸다」는 사실**이다.

**ASan 은 실행 시점에 잡는다.**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -g -ffile-prefix-map=$PWD=. -fsanitize=address s21e2.c -o x ; ./x 2>&1 | sed -n '1,/^SUMMARY/p' | grep -v '^    #[1-9] ' (cc exit=0 · run exit=1) =====
--- (가) 복합 리터럴 주소를 반환받는다 ---
--- (나) 이제 역참조한다 ---
=================================================================
==473574==ERROR: AddressSanitizer: stack-use-after-return on address 0x73806ff00024 at pc 0x5a9a14fab531 bp 0x7fff1e5ee240 sp 0x7fff1e5ee230
READ of size 4 at 0x73806ff00024 thread T0
    #0 0x5a9a14fab530 in main s21e2.c:14

Address 0x73806ff00024 is located in stack of thread T0 at offset 36 in frame
    #0 0x5a9a14fab2b8 in make s21e2.c:5

  This frame has 1 object(s):
    [32, 40) '<unknown>' <== Memory access at offset 36 is inside this variable
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-use-after-return s21e2.c:14 in main
```

- `stack-use-after-return` — **이미 반환된 프레임을 읽었다**는 진단이다.
- 프레임 정보가 `make s21e2.c:5` 를 가리킨다. **복합 리터럴이 만들어진 줄**이다.
- ★ 이 블록의 출력은 `| sed -n '1,/^SUMMARY/p' | grep -v '^    #[1-9] '` 로 **잘라서 받은 것**이다.\
  배너에 자르는 명령이 그대로 적혀 있으므로 **그 명령의 전체 출력**이다 — 다시 던질 수 있다.
- ★★ 소스 첫 줄에 **`setvbuf(stdout, NULL, _IONBF, 0)`** 를 넣었다.\
  sanitizer 가 죽이면 **버퍼에 남은 표준 출력이 통째로 사라지기** 때문이다.\
  구분 마커도 **`fprintf(stderr, …)`** 로 찍었다.

### (5-다) ★★ 경고는 **`-O` 를 올려야 나온다** — 그리고 clang 은 안 낸다

**언제 쓰나** — 「빌드에 경고가 없으니 댕글링은 없겠지」라고 믿을 때.

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O1 s21e2.c -o x (cc exit=0) =====
s21e2.c: In function ‘main’:
s21e2.c:14:5: warning: using a dangling pointer to an unnamed temporary [-Wdangling-pointer=]
   14 |     printf("p->x = %d p->y = %d\n", p->x, p->y);
      |     ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
s21e2.c:6:23: note: unnamed temporary defined here
    6 |     return &(struct P){ .x = v, .y = v * 10 };   /* ★ 함수가 끝나면 수명이 끝난다 */
      |                       ^
s21e2.c:14:5: warning: using a dangling pointer to an unnamed temporary [-Wdangling-pointer=]
   14 |     printf("p->x = %d p->y = %d\n", p->x, p->y);
      |     ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
s21e2.c:6:23: note: unnamed temporary defined here
    6 |     return &(struct P){ .x = v, .y = v * 10 };   /* ★ 함수가 끝나면 수명이 끝난다 */
      |                       ^
s21e2.c:14:5: warning: ‘<Uf1b0>.y’ is used uninitialized [-Wuninitialized]
   14 |     printf("p->x = %d p->y = %d\n", p->x, p->y);
      |     ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
s21e2.c:6:23: note: ‘({anonymous})’ declared here
    6 |     return &(struct P){ .x = v, .y = v * 10 };   /* ★ 함수가 끝나면 수명이 끝난다 */
      |                       ^
s21e2.c:14:5: warning: ‘<Uf1b0>.x’ is used uninitialized [-Wuninitialized]
   14 |     printf("p->x = %d p->y = %d\n", p->x, p->y);
      |     ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
s21e2.c:6:23: note: ‘({anonymous})’ declared here
    6 |     return &(struct P){ .x = v, .y = v * 10 };   /* ★ 함수가 끝나면 수명이 끝난다 */
      |                       ^
```

- gcc 는 **`-Wdangling-pointer=` 2건 + `-Wuninitialized` 2건 = 4건**을 낸다.
- ★ `<Uf1b0>` 같은 이름은 **컴파일러 내부의 임시 이름**이다. `-O1` 과 `-O2` 에서 **다른 문자열**이 나온다 —\
  **대조할 것은 그 문자열이 아니라 진단의 종류와 건수**다.

```text
===== 경고를 플래그별로 센다 — grep -c 'warning:' (exit=0) =====
gcc   -O0  warning: 0건  (cc exit=0)
gcc   -O1  warning: 4건  (cc exit=0)
gcc   -O2  warning: 4건  (cc exit=0)
gcc   -O3  warning: 4건  (cc exit=0)
clang -O0  warning: 0건  (cc exit=0)
clang -O1  warning: 0건  (cc exit=0)
clang -O2  warning: 0건  (cc exit=0)
clang -O3  warning: 0건  (cc exit=0)
```

```text
   같은 UB 를 여덟 벌로 돌렸다

            -O0    -O1    -O2    -O3
   gcc       0      4      4      4      ★ -O0 은 한 마디도 안 한다
   clang     0      0      0      0      ★★ 어느 수준에서도 0 이다

   -> 「경고 0건」은 컴파일러와 -O 에 달린 값이지 코드의 성질이 아니다
```

- ★★★ **gcc `-O0` 과 clang 전부가 0건**이다. **경고는 최적화가 만든 부산물**이다 —\
  `-O0` 에서는 컴파일러가 데이터 흐름을 그만큼 안 따라가므로 **볼 수가 없다.**
- ★ **`cc exit` 를 같이 봐야 뜻이 있다.** 여덟 벌 전부 **`cc exit=0`** 이다 — **경고 0건이 컴파일 실패 때문이 아니다.**
- 이 자리에서 믿을 것은 **ASan 하나**다. 그리고 ASan 은 **그 줄을 실제로 실행해야** 잡는다.

비용 — 없다. **켜는 것이 공짜**이고, 안 켜면 **아무도 말해 주지 않는다.**

### (6) ★ C23 의 빈 중괄호 `= {}`

**언제 쓰나** — `= {0}` 이 **첫 멤버가 스칼라가 아닐 때** 어색해질 때.

```c
/* s21h.c */
#include <stdio.h>
struct S { int a, b; };
int main(void) {
    struct S s = {};                 /* ★ 빈 중괄호 — C23 부터 */
    printf("s = { %d, %d }\n", s.a, s.b);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s21h.c -o x (cc exit=0) =====
s21h.c: In function ‘main’:
s21h.c:4:18: warning: ISO C forbids empty initializer braces before C2X [-Wpedantic]
    4 |     struct S s = {};                 /* ★ 빈 중괄호 — C23 부터 */
      |                  ^
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic s21h.c -o x ; ./x (cc exit=0 · run exit=0) =====
s = { 0, 0 }
```

- **C17 에서는 `-pedantic` 이 잡는다** — `ISO C forbids empty initializer braces before C2X`. **`cc exit=0`** 이므로 **컴파일은 된다.**
- **`-std=c2x` 로 올리면 경고 없이 통과**하고 `s = { 0, 0 }` 이 나온다.
- ★★ 여기서도 같은 함정이다 — **`-pedantic` 이 없으면 C17 에서도 말없이 통과**한다.\
  「`-std=c17` 로 돌렸다」는 「C17 로 검증했다」가 아니다.
- ★ gcc 13 은 `-std=c23` 을 모른다. **`-std=c2x`** 를 써야 한다.

비용 — 없다. 다만 **C17 이하와 호환이 필요하면 `= {0}` 으로 남긴다.**

## 문법 — 형태와 규칙

### 형태

```text
/* 1. 선언 — 태그 / typedef / 변수 선언이 한 자리에 올 수 있다 */
struct Rec { int id; char name[8]; double rate; };      /* 태그만 */
struct Rec a;                                            /* 변수 */
struct { int x, y; } p;                                  /* 태그 없는 타입 */
typedef struct { int x, y; } Point;                      /* typedef 로 별칭 (06번 주제) */

/* 2. 초기화 — 네 꼴 */
struct Rec r1 = { 7, "kim", 1.5 };        /* 위치 */
struct Rec r2 = { .rate = 1.5 };          /* 지정 (C99) — 나머지는 0 */
struct Rec r3 = { 7, .rate = 1.5 };       /* 섞기 */
struct Rec r4 = {0};                      /* 전부 0 */
struct Rec r5 = {};                       /* 전부 0 — ★ C23부터 */

/* 3. 대입 — 선언 뒤에 통째로 */
struct Rec b;
b = a;                                    /* 멤버별 복사 */
b = (struct Rec){ 9, "lee", 2.0 };        /* 복합 리터럴로 갈아 끼우기 (C99) */

/* 4. 중첩과 익명 */
struct Outer { int tag; struct Inner { int x, y; } in; struct { int u, v; }; };
o.in.x = 9;    /* 중첩은 한 단계 */
o.v    = 6;    /* 익명은 바로 (C11) */

/* 5. 복합 리터럴 */
sum((struct P){ 3, 4 });                  /* 인자로 */
struct P *q = &(struct P){ 1, 2 };        /* 주소를 잡아도 된다 — 수명만 조심 */
```

### 금지 사례 — 어느 것이 무슨 층인가

```text
/* (1) 컴파일 에러 — 공짜로 막아 준다 */
char a[4], b[4];
b = a;                     /* error: assignment to expression with array type */
struct P s, t;
if (s == t) { }            /* error: invalid operands to binary == */
int arr[3];
arr = (int[3]){1,2,3};     /* error: 왼쪽이 배열이면 오른쪽이 무엇이든 안 된다 */

/* (2) 경고만 — 컴파일은 된다 */
struct P u = { .a = 1, .a = 9 };   /* warning: -Woverride-init · 뒤엣것이 이긴다 */
struct Cfg v = { 80 };             /* warning: -Wmissing-field-initializers */
struct S w = {};                   /* warning: C17 에서 -pedantic 이 잡는다 */

/* (3) 아무 말도 안 해 주는 것 — ★ 여기가 사고 자리다 */
struct P *bad(void) { return &(struct P){1,2}; }   /* gcc -O0 · clang 전부 0건 */
```

### 규칙 불릿

- **구조체는 값이다** — 대입·인자·반환이 전부 된다. **배열은 값이 아니다** — 셋 다 안 된다.
- **구조체에는 `==` 가 없다.** 비교는 **멤버끼리** 한다(`memcmp` 는 [22번 형제](../22-struct-padding-and-alignment/)가 왜 안 되는지 보여 준다).
- **초기자가 하나라도 있으면** 안 적은 멤버는 **정적 초기화 규칙**으로 0 이 된다.
- **초기자가 아예 없으면** 자동 저장 기간 객체는 **불확정**이다([목록의 **30번 주제**](../30-initialization-rules-and-indeterminate-values/)).
- **지정 초기자는 순서를 안 지켜도 된다**(C). **중복이면 뒤엣것이 이긴다.**
- **배열에도 지정 초기자가 있다** — `[4] = 40`.
- **중첩 구조체의 태그는 바깥 스코프에 생긴다.** 익명 멤버는 **한 단계 없이** 닿는다(C11).
- **복합 리터럴은 lvalue 다** — 주소가 있고 고칠 수 있다. **저장 기간은 적은 자리가 정한다.**
- **블록 스코프 복합 리터럴의 주소를 돌려주면 UB** 다.

## 어디서 틀리나

### 1. ★★★ 「배열 멤버는 얕은 복사겠지」

**아니다.** 구조체 대입은 **배열 멤버를 통째로 복사**한다 — `a.name == b.name` 이 **0** 이고 `memcmp` 가 **0** 이다.\
★ 얕게 복사되는 것은 **포인터 멤버**다. 구조체 안에 `char *` 를 두면 **가리키는 곳은 공유**된다.\
**「배열 멤버냐 포인터 멤버냐」가 복사의 깊이를 가른다** — 그 선택은 목록의 **38번 주제**(소유권)가 정본이다.

### 2. ★★★ 「`-Wall -Wextra` 면 초기화 누락은 잡히겠지」

**한 꼴만 잡힌다.** 같은 파일에서 `{ 80 }` 만 경고가 붙고 `= {0}`·지정 초기자·섞어 쓰기는 **0건**이다.\
★ `-Wmissing-field-initializers` 는 **꼴을 보는 경고**다. **뜻을 보는 경고가 아니다.**

### 3. ★★★ 「복합 리터럴이니 리터럴처럼 오래 살겠지」

**이름이 「리터럴」일 뿐 객체다.** 블록 안에서 만들면 **그 블록에서 죽는다.**\
★ 문자열 리터럴과 **이름만 닮았다** — 문자열 리터럴은 정적 저장 기간이다([20번 형제](../20-null-terminated-strings-and-string-literals/)).\
★★ 그 둘을 같은 것으로 읽으면 **함수에서 주소를 돌려주는 코드**가 나온다.

### 4. ★★ 「죽지 않았으니 괜찮겠지」

`-O0` 은 쓰레기를 찍고 `-O2` 는 `0 0` 을 찍는다. **둘 다 `run exit=0`** 이다.\
★ **한 최적화 수준만 돌리고 「된다」고 적으면 안 된다.** 갈린 자리를 찾아 적는 것이 이 갈래의 일이다.

### 5. ★★ 「C 에서 되니 C++ 에서도 되겠지」

**지정 초기자의 순서**가 갈린다. C++ 는 **C++20 에서도 선언 순서를 요구**하고, 어기면 **에러**다.\
★ 헤더를 공유하는 프로젝트에서 **C 쪽 빌드는 멀쩡한데 C++ 쪽만 깨진다.**

### 6. ★★ 「`= {0}` 과 `= {}` 는 같은 거니까 아무거나」

**C17 이하에서 `= {}` 는 표준이 아니다.** `-pedantic` 이 `ISO C forbids empty initializer braces before C2X` 로 잡는다.\
★ **`-pedantic` 없이는 말없이 통과**한다.

### 7. ★ 「익명 구조체는 예전부터 있었겠지」

**C11 부터**다. `-std=c99 -pedantic` 으로 내리면 `ISO C99 doesn't support unnamed structs/unions` 가 나온다.

### 8. ★ 「구조체를 `memcmp` 로 비교하면 되겠지」

**안 된다.** 멤버 값이 같아도 **패딩 바이트 때문에 다르게 나올 수 있다.**\
정본은 [22번 형제](../22-struct-padding-and-alignment/)이고, 거기에 **같은 값인데 갈린 실측**이 있다.

## 구현 세부사항 대 언어 보장

C 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★ **이 주제는 「표준」이 본체**다 — 초기화·대입 규칙은 어느 구현에서도 같다.\
**구현 정의 칸이 얇고**, 무게는 **UB 칸**(복합 리터럴의 수명)에 실린다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | 멤버가 **선언 순서대로** 배치되는 것 · **구조체 대입이 값 복사**(배열 멤버 포함) · **배열은 대입 불가** · **구조체에 `==` 없음** · 초기자가 있으면 **안 적은 멤버가 0** · 지정 초기자의 **순서 자유와 「뒤엣것이 이긴다」** · 복합 리터럴이 **수정 가능한 lvalue** 인 것 · 블록 안이면 **자동**, 파일 스코프면 **정적** 저장 기간인 것 | `memcmp` 0 · `a.name == b.name` 이 0 · 네 초기화 꼴의 출력 · `s = {1,0,3}` · `t = {9,0,0}` · for 두 바퀴가 둘 다 1 · 컴파일 에러 세 줄 | — |
| **조건부 표준** | 매크로가 정의될 때만 | **해당 없음** | — | — |
| **구현 정의** | 문서화 의무가 있다 | **구조체의 크기와 패딩 자리**(→ [22번 형제](../22-struct-padding-and-alignment/)가 정본) · `sizeof(struct Outer)` = 20 · 진단 **문구와 플래그 이름**(`-Woverride-init` 등) | `offsetof` 로 찍음 · 두 컴파일러의 진단 대조 | 수치는 **찍어야만** 안다 |
| **미명시** | 몇 가지 중 하나 | **구조체 대입이 패딩까지 복사하는가** · **안 적은 멤버 뒤의 패딩 바이트 값** | ★ 실측은 [22번 형제](../22-struct-padding-and-alignment/)에 있다 — 여기서는 **링크만** | ★ **sanitizer 가 원리상 못 잡는다** |
| **UB** | 아무 일이나 | **수명이 끝난 복합 리터럴 역참조** · **초기화 안 한 구조체의 멤버 읽기** | `-O0` 은 쓰레기 · `-O2` 는 `0 0` · ASan 이 `stack-use-after-return` | ★★ **gcc `-O0` 0건 · clang 은 `-O0`\~`-O3` 전부 0건** |

### ★★ 「도구가 못 보는 것」을 층마다

| 사실 | gcc `-Wall -Wextra` | `-pedantic` | gcc `-O1` 이상 | clang 전부 | ASan |
|---|---|---|---|---|---|
| 배열에 대입 · 구조체 `==` | **에러**(경고 아님) | — | 〃 | 〃 | — |
| `{ 80 }` 부분 초기화 | **1건** | — | 〃 | 〃 | — |
| `= {0}` · 지정 초기자로 일부만 | **0건** | 0건 | 0건 | 0건 | 못 잡는다 |
| 중복 지정 `.a` 두 번 | **1건**(`-Woverride-init`) | — | 〃 | 〃 | — |
| 순서 밖 지정(C 에서) | 0건 | 0건 | 0건 | 0건 | — |
| 익명 구조체(C99 에서) | 0건 | **1건** | — | — | — |
| `= {}`(C17 에서) | 0건 | **1건** | — | — | — |
| **댕글링 복합 리터럴** | ★ **`-O0` 0건** | 0건 | **4건** | ★★ **0건** | ★ **잡는다** |

- ★★★ 마지막 줄이 이 주제의 결론이다 — **같은 UB 인데 컴파일러와 `-O` 에 따라 0건과 4건이 갈린다.**
- ★ 경고를 셀 때는 **`grep -c 'warning:'`** 로 센다. clang 의 `4 warnings generated.` 요약 줄까지 세면 수가 어긋난다.
- ★★ **「경고 0건」은 `cc exit` 를 같이 봐야 뜻이 있다.** 이 주제의 여덟 벌은 전부 `cc exit=0` 이다.

### 이 주제의 네 번째 창 — **`offsetof` 와 「두 벌 이상」**

- 진단 3창(에러 · 경고 · 실행 출력)이 전부 조용한 자리가 있다. 그때 쓰는 창이 둘이다.
- **`offsetof`** — 익명 멤버가 **정말 바깥 구조체 안에 펼쳐졌는가**를 이름 없이 물어보는 유일한 방법이다.
- **여러 벌 돌리기** — UB 는 **한 벌로는 성질이 안 보인다.** `-O0` 과 `-O2` 가 갈려야 「갈린다」를 적을 수 있다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 구조체 한 벌 더 만들기 | `b = a;` | `memcpy(&b, &a, sizeof b)`(되긴 하지만 타입 검사를 버린다) |
| 배열 한 벌 더 만들기 | `memcpy(y, x, sizeof y)` | `y = x;`(에러) |
| 멤버가 늘어날 설정 구조체 | **지정 초기자** | 위치 초기자(멤버가 늘면 전부 밀린다) |
| 전부 0 으로 | `= {0}`(이식) · `= {}`(C23) | `memset` 뒤 멤버 대입(패딩이 갈린다 → [22번](../22-struct-padding-and-alignment/)) |
| 구조체 비교 | **멤버끼리 비교** | `memcmp` · `==` |
| 임시 구조체를 인자로 | **복합 리터럴** | 지역 변수를 만들어 넘기기(이름이 낭비다) |
| 구조체를 통째로 갈아 끼우기 | `s = (struct P){…};` | 멤버를 하나씩 대입(빠뜨린 멤버가 생긴다) |
| 함수가 구조체를 돌려주기 | **값으로 반환** | ★ **복합 리터럴의 주소 반환**(UB) |
| 한 단계 줄이기 | **익명 구조체 멤버**(C11) | 멤버 이름을 `u_`·`v_` 로 늘어놓기 |
| 크기가 큰 구조체 전달 | `const struct S *` | 값 전달(크기만큼 복사한다) |

판단 규칙 두 줄.

- **「이 값이 이 블록을 벗어나 살아야 하나」** — 그렇다면 복합 리터럴의 주소를 쓰지 않는다.
- **「멤버가 나중에 늘어날 수 있나」** — 그렇다면 지정 초기자로 쓴다.

## 핵심 문장

1. **구조체는 값이고 배열은 값이 아니다** — 대입·인자·반환이 구조체에서는 되고 배열에서는 안 된다.
2. **구조체 대입은 배열 멤버까지 복사한다.** 얕아지는 것은 **포인터 멤버**뿐이다.
3. **초기자가 하나라도 있으면 안 적은 멤버는 0 이다** — 정적 초기화 규칙을 그대로 쓴다.
4. **`-Wmissing-field-initializers` 는 꼴을 보는 경고다.** `= {0}` 과 지정 초기자는 대상이 아니다.
5. **지정 초기자는 C 에서 순서 자유이고 C++ 에서는 아니다** — C++20 에서도 에러다.
6. **복합 리터럴은 상수가 아니라 객체다** — 주소가 있고 고칠 수 있고 **죽는다.**
7. **그 수명을 넘겨 읽으면 UB 이고, `-O` 에 따라 다른 값이 나오고, 둘 다 안 죽는다.**
8. **그 UB 를 gcc `-O0` 도 clang 도 한 마디도 경고하지 않는다.** 잡는 것은 ASan 뿐이다.
9. **구조체를 `memcmp` 로 비교하지 않는다** — 그 이유는 패딩이고, 정본은 22번이다.
10. **`-pedantic` 이 없으면 「언제부터인가」를 물어볼 수 없다** — C11·C23 표시가 전부 거기서 나왔다.

## 관련 자료

- [`../README.md`](../README.md) — C 문법·API 주제 목록(이 주제는 21번)
- [`22-struct-padding-and-alignment/`](../22-struct-padding-and-alignment/) — ★★★ **패딩·정렬의 정본.**\
  그쪽은 「**멤버 순서가 크기를 바꾸는 것**」과 「**패딩 값이 미명시인 것**」부터, 여기는 **선언·초기화·대입**까지
- [`08-sizeof-alignment-and-offsetof/`](../08-sizeof-alignment-and-offsetof/) — ★★ **`sizeof`·`_Alignof`·`offsetof` 라는 도구의 정본.**\
  이 문서의 `offsetof` 사용은 전부 거기 규칙을 쓴 것이다
- [`23-union-and-the-boundary-of-type-punning/`](../23-union-and-the-boundary-of-type-punning/) — **같은 메모리를 여러 타입으로 보는 쪽.** 구조체는 **동시에 담고** union 은 **하나만 담는다**
- [`20-null-terminated-strings-and-string-literals/`](../20-null-terminated-strings-and-string-literals/) — ★ **문자열 리터럴은 정적 저장 기간**이다. **복합 리터럴과 이름만 닮았다**
- [`16-array-pointer-decay-and-function-parameters/`](../16-array-pointer-decay-and-function-parameters/) — 배열이 **왜 값이 아닌가**의 바탕
- [`14-pointers-address-dereference-and-pointer-types/`](../14-pointers-address-dereference-and-pointer-types/) — 복합 리터럴의 **주소를 잡는** 문법
- [`06-typedef-and-type-aliases/`](../06-typedef-and-type-aliases/) — `typedef struct {…} Point;` 꼴의 정본
- [`01-declaration-syntax-and-reading/`](../01-declaration-syntax-and-reading/) — 태그·선언자가 한 줄에 섞이는 것을 읽는 법
- [목록의 **25번 주제**](../25-incomplete-types-and-opaque-struct/) (불완전 타입과 opaque struct) — 헤더에 `struct S;` 만 노출하는 쪽
- [목록의 **26번 주제**](../26-flexible-array-members/) (유연 배열 멤버) — 마지막 멤버가 `[]` 인 구조체
- [목록의 **27번 주제**](../27-compound-literals/) (복합 리터럴) — ★ **복합 리터럴의 정본.** 여기는 **저장 기간만** 봤다
- [목록의 **30번 주제**](../30-initialization-rules-and-indeterminate-values/) (초기화 규칙과 불확정 값) — ★ **초기자를 아예 안 줬을 때**가 거기다
- 목록의 **38번 주제** (소유권 관례) — **포인터 멤버를 둘 때** 누가 해제하나
- 목록의 **57번 주제** (시간 위반 — 댕글링) — 이 주제의 UB 를 **묶어서** 다루는 자리

## 용어 풀이

- **집합체(aggregate)** — 멤버를 모아 놓은 타입. C 에서는 **구조체와 배열**이다.\
  예: 둘 다 중괄호로 초기화하지만 **대입은 구조체만 된다.**
- **태그(tag)** — `struct Rec` 의 `Rec`. **타입 이름이 아니라 태그 이름공간**에 산다.\
  예: `struct Rec a;` 처럼 언제나 `struct` 를 붙여 쓴다(`typedef` 로 별칭을 만들지 않는 한).
- **지정 초기자(designated initializer)** — 초기자에서 멤버 이름·배열 첨자를 찍어 값을 주는 문법. C99부터.\
  예: `{ .retry = 3 }` · `{ [4] = 40 }`.
- **위치 초기자(positional initializer)** — 이름 없이 순서대로 적는 초기자.\
  예: `{ 7, "kim", 1.5 }`. ★ **멤버가 늘어나면 전부 밀린다.**
- **정적 초기화 규칙** — 초기자가 있는 집합체에서 **안 적은 멤버가 받는 값**.\
  예: 정수는 0, 부동소수는 0.0, 포인터는 널 포인터.
- **복합 리터럴(compound literal)** — `(타입){초기자}` 로 그 자리에 만드는 **이름 없는 객체**. C99부터.\
  예: `sum((struct P){3, 4})`. ★ **lvalue 라서 고칠 수 있다.**
- **lvalue** — 주소를 가질 수 있고 대입의 왼쪽에 올 수 있는 식.\
  예: 복합 리터럴은 lvalue 라 `q->x = 99` 가 합법이다.
- **저장 기간(storage duration)** — 객체가 언제 태어나 언제 죽는가. 자동·정적·스레드·할당.\
  예: 블록 안 복합 리터럴은 **자동**이라 블록을 벗어나면 죽는다.
- **익명 구조체 멤버(anonymous struct member)** — 이름 없이 박아 넣은 구조체 멤버. C11부터.\
  예: `struct { int u, v; };` 를 넣으면 `o.u` 로 바로 닿는다.
- **`-Wmissing-field-initializers`** — 위치 초기자가 멤버 수보다 적을 때 나오는 경고(`-Wextra` 에 포함).\
  ★ `= {0}` 과 지정 초기자는 **대상이 아니다.**
- **`-Woverride-init`** — 같은 멤버를 두 번 초기화했을 때의 경고. **뒤엣것이 이긴다**는 사실을 알려 준다.
- **`-Wdangling-pointer=`** — 죽은 객체의 주소를 쓰고 있다는 gcc 의 경고.\
  ★ **`-O1` 이상에서만** 나온다. clang 18 에는 이 진단이 없다.
- **`stack-use-after-return`** — 이미 반환된 스택 프레임을 읽었다는 ASan 의 진단.
- **미명시 동작(unspecified behavior)** — 표준이 **여러 가능성 중 하나**를 허용하고 **문서화도 요구하지 않는** 것.\
  예: 구조체 대입이 패딩까지 복사하는가.
- **미정의 동작(undefined behavior, UB)** — 표준이 **아무 요구도 하지 않는** 것.\
  예: 수명이 끝난 복합 리터럴 역참조.

---

## 더 들어가면

- **구조체를 값으로 넘길 때 실제로 어떻게 넘어가는가** — x86-64 System V ABI 는 **16바이트 이하를 레지스터로** 넘긴다.\
  그래서 「값 전달은 무조건 느리다」가 항상 맞지는 않다. ★ 이것은 **ABI 의 일**이지 C 표준의 일이 아니다.
- **왜 배열만 값이 아닌가** — 배열이 값이었다면 `a[i]` 마다 배열 전체가 복사될 수 있다.\
  ★ C 는 **감쇠**로 그 문제를 피했고, 그 대가가 「대입이 안 된다」이다([16번 형제](../16-array-pointer-decay-and-function-parameters/)).
- **지정 초기자가 C++ 에 늦게 들어온 이유** — C++ 는 **생성 순서**가 의미를 갖는 언어다.\
  멤버 초기화 순서가 선언 순서로 고정돼 있어 **순서 밖 지정을 허용하면 그 규칙과 부딪힌다.**
- **복합 리터럴의 개수** — 같은 블록에서 같은 복합 리터럴을 두 번 쓰면 **객체가 둘**이다.\
  for 두 바퀴가 둘 다 `1` 에서 시작한 것이 그 성질을 보여 준다.
- **구조체 안의 구조체 대입** — 중첩 구조체도 **통째로 복사**된다. 깊이와 무관하다.\
  ★ 얕아지는 자리는 **포인터가 나오는 자리 하나**뿐이다.
- **`static` 구조체의 초기화** — 정적 저장 기간이면 초기자가 없어도 **전부 0** 이다.\
  ★ 자동 저장 기간과 **여기서 갈린다**([목록의 **28번 주제**](../28-choosing-among-four-storage-durations/)·**30번 주제**).
