# c/syntax/21 — 구조체 선언·초기화·지정 초기자: 「**구조체는 값이고, 배열은 값이 아니다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·sanitizer 리포트는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s21a.c`\~`s21h.c` 와 `s21g.cpp` 이고, **모든 블록은 캡처 파일에서 그대로 조립됐다** — 손으로 옮긴 수치가 없다.\
> ★★ **죽거나 sanitizer 를 태우는 프로그램에는 `setvbuf(stdout, NULL, _IONBF, 0)` 를 넣고 마커를 `stderr` 로 찍었다.**\
> ASan 리포트는 `| sed -n '1,/^SUMMARY/p' | grep -v '^    #[1-9] '` 로 잘랐다 — **배너에 자르는 명령이 적혀 있다.**
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 의 주소 · `pc`/`bp`/`sp` · PID · 프레임 오프셋 | ★★ **`memcmp` 0** · **`a.name == b.name` 0** · 네 초기화 꼴의 출력 |
> | ★ `-O0` 판이 찍은 **쓰레기 숫자**(`p->x`·`p->y`) | ★★ **`-O0` 과 `-O2` 가 갈린다는 사실**과 **둘 다 `run exit=0`** 인 것 |
> | gcc 내부 임시 이름(`<Uf1b0>` 꼴 — `-O1` 과 `-O2` 가 다르다) | ★★ **진단의 종류와 건수**(`-Wdangling-pointer=` 2 + `-Wuninitialized` 2) |
> | — | ★★ **`offsetof` 값 · `sizeof` 20** · 진단 본문 · **플래그 이름** · `cc exit` · ★ **ASan 블록의 `run exit=1`** |

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 구조체 대입은 **배열 멤버까지 복사한다** ★★★

**출력**

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

**왜 그런가**

```text
   b = a;   한 줄이 한 일

   a                                    b
   +--------+--------------+--------+   +--------+--------------+--------+
   | id  7  | 6b 69 6d 00… | 1.5    |-->| id  7  | 6b 69 6d 00… | 1.5    |
   +--------+--------------+--------+   +--------+--------------+--------+
              ^^^^^^^^^^^^                        ^^^^^^^^^^^^
              배열 멤버                            ★ 바이트째 따라왔다

   그 뒤 b 만 고쳤다:  b.id = 9;  b.name[0] = 'L';

   a = { 7, "kim", 1.5 }                b = { 9, "Lim", 1.5 }
   ★ a 는 한 글자도 안 바뀌었다          ★ 별칭이 아니라 복사본이다
```

- **`a.name == b.name` 이 `0`** 이다. 두 배열이 감쇠해 **다른 주소**가 나왔다는 뜻이다 —\
  ★ 「같은 메모리를 가리키는 두 이름」이 아니라 **따로 사는 두 배열**이다.
- **`memcmp(a.name + 1, b.name + 1, 7)` 이 `0`** 이다. 첫 글자만 `L` 로 바꿨으니 **뒤 7바이트는 같다** —\
  ★★ **배열 멤버가 통째로 복사됐다**는 직접 증거다. 「포인터만 복사」였다면 `b.name[0]='L'` 이 `a` 까지 바꿨을 것이다.
- 마지막 줄이 짝이다 — **맨 배열 `y` 에는 `y = x;` 를 못 쓴다.** `memcpy` 로만 옮긴다(7번 답이 에러 전문이다).
- ★ **`char *` 멤버였다면 달라진다.** 포인터 값만 복사되므로 **가리키는 곳은 공유**된다 —\
  그때 「누가 해제하나」가 문제가 되고, 그 정본은 목록의 **38번 주제**다.

| 무엇을 물었나 | 답 | 무엇을 증명하나 |
|---|---|---|
| `a.name == b.name` | **0** | 두 배열이 **다른 메모리**다 |
| `memcmp(a.name+1, b.name+1, 7)` | **0** | 배열 멤버가 **통째로 복사**됐다 |
| `y = x;`(맨 배열) | ★ **에러** | 배열은 **값이 아니다** |

### 2. 안 적은 멤버는 **전부 0 이 된다** ★★★

**출력**

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

**왜 그런가**

```text
   struct Cfg { int port; int retry; char host[8]; double t; };

   = {0}          = { 80 }        = { .retry=3, .host="a" }   = { 8080, .t=0.5 }
   port   0       port   80       port   0                     port   8080
   retry  0       retry  0  ★     retry  3                     retry  0  ★
   host   ""      host   ""  ★    host   "a"                   host   ""  ★
   t      0.0     t      0.0 ★    t      0.0 ★                 t      0.5

   ★ 표시한 칸이 전부 「안 적은 멤버」다 — 네 꼴 모두 0 이다
```

- 규칙은 하나다 — **초기자가 하나라도 있으면** 안 적은 멤버는 **정적 저장 기간 객체와 같은 규칙**으로 초기화된다.\
  정수 `0` · 부동소수 `0.0` · 배열은 **원소마다 그 규칙을 다시** 적용해 `'\0'` 로 채운다.
- 그래서 `d.port = 0` · `d.t = 0.0` · `d.host[1] = 0` 이다. **쓰레기가 아니다.**
- **`m` 처럼 섞어 써도 된다** — `{ 8080, .t = 0.5 }` 는 첫 멤버를 위치로, `t` 를 이름으로 준 것이다.
- ★★ **초기자를 아예 안 주면 규칙이 통째로 다르다.** 자동 저장 기간 객체는 **불확정**이고,\
  그 정본은 목록의 **30번 주제**다. **「`= {0}` 을 붙였나 안 붙였나」가 갈림길**이다.
- ★ `host` 가 `""` 로 찍히는 것은 **첫 바이트가 0** 이기 때문이다 — 여덟 칸이 전부 0 이다.

### 3. 지정 초기자는 **선언 순서대로 채워지고, 중복이면 뒤엣것이 이긴다** ★★

**출력**

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
===== gcc -std=c17 -Wall -Wextra -pedantic s21c.c -o x (cc exit=0) =====
s21c.c: In function ‘main’:
s21c.c:7:33: warning: initialized field overwritten [-Woverride-init]
    7 |     struct P t = { .a = 1, .a = 9 };        /* ★ 같은 멤버를 두 번 */
      |                                 ^
s21c.c:7:33: note: (near initialization for ‘t.a’)
```

**왜 그런가**

```text
   { .c = 3, .a = 1 }         적은 순서는 c -> a
                              채워진 자리는 선언 순서 a b c
   +-----+-----+-----+
   |  1  |  0  |  3  |        ★ b 는 안 적었으니 0
   +-----+-----+-----+
      a     b     c

   { .a = 1, .a = 9 }         같은 칸을 두 번
   +-----+-----+-----+
   |  9  |  0  |  0  |        ★ 뒤엣것이 이긴다 (에러가 아니라 정의된 동작)
   +-----+-----+-----+

   int arr[6] = { [4] = 40, [1] = 10 }
   +----+----+----+----+----+----+
   |  0 | 10 |  0 |  0 | 40 |  0 |    ★ 안 찍은 칸은 0
   +----+----+----+----+----+----+
      0    1    2    3    4    5
```

- **적은 순서와 채워지는 자리는 무관**하다. C 는 **순서 밖 지정을 그냥 받는다.**
- **중복은 뒤엣것이 이긴다.** 이것은 **정의된 동작**이고, gcc 는 그래도 한 마디 해 준다 —\
  `-Woverride-init` **1건**. ★ **`cc exit=0`** 이므로 **컴파일은 성공**했다.
- **순서 밖 지정에는 경고가 없다.** 그것이 정상적인 C 이기 때문이다.
- 배열에도 같은 문법이 있다 — `[4] = 40`. 구조체와 **같은 규칙**이다.
- ★★ 9번 답이 짝이다 — **같은 순서 밖 지정을 C++ 에 던지면 에러**다.

### 4. 중첩은 **한 단계**, 익명은 **바로 닿는다** ★★

**출력**

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
===== gcc -std=c99 -Wall -Wextra -pedantic s21d.c -o x (cc exit=0) =====
s21d.c:7:25: warning: ISO C99 doesn’t support unnamed structs/unions [-Wpedantic]
    7 |     struct { int u, v; };            /* ★ 익명 구조체 멤버 (C11) */
      |                         ^
```

**왜 그런가**

```text
   struct Outer {
       int tag;                          o.tag       offset  0
       struct Inner { int x, y; } in;    o.in.x      offset  4
                                         o.in.y      offset  8
       struct { int u, v; };             o.u         offset 12   ★ 이름이 없다
                                         o.v         offset 16
   };

   +--------+--------+--------+--------+--------+
   |  tag   |  in.x  |  in.y  |   u    |   v    |     sizeof = 20
   +--------+--------+--------+--------+--------+
       0        4        8       12       16

   o.in.x = 9;   <- 중첩:  o . in . x   (세 토막)
   o.v    = 6;   <- 익명:  o . v        (★ 두 토막)
```

- **`offsetof(struct Outer, in)` 과 `offsetof(struct Outer, in.x)` 가 둘 다 4** 다.\
  ★ 중첩 구조체의 **첫 멤버는 바깥 구조체 기준으로도 같은 자리**에서 시작한다.
- **익명 멤버 `u`·`v` 가 12 와 16** 이다 — **따로 떨어진 객체가 아니라 바깥 구조체 안에 펼쳐진 칸**이다.
- **`struct Inner i = { 7, 8 };` 이 바깥 함수에서 된다.** C 에는 클래스 스코프가 없어 **안쪽 태그가 바깥 스코프에 생긴다.**\
  ★ 이 자리가 C++ 와 다르다.
- 초기자도 섞인다 — `{ .tag = 1, .in = { .y = 20 }, .u = 5 }`. **중첩 지정 초기자**가 그대로 먹고,\
  안 적은 `in.x` 는 0 이었다가 나중에 `o.in.x = 9` 로 덮였다.
- ★★ **익명 구조체는 C11 부터**다. `-std=c99 -pedantic` 이 **`ISO C99 doesn't support unnamed structs/unions`** 로 말해 준다.\
  ★ **`-pedantic` 이 없으면 C99 에서도 말없이 통과**한다 — 10번 답이 같은 이야기다.

### 5. 복합 리터럴은 **객체이고, 블록마다 새로 만들어진다** ★★

**출력**

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

**왜 그런가**

```text
   적은 자리                          저장 기간      언제 죽나
   --------------------------------  ------------  --------------------------
   sum((struct P){3, 4})             자동          호출이 끝나면
   g = (struct P){ .y = 5 };         자동          그 문장이 끝나면
   static struct P *gp = &(…){7,8};  ★ 정적        프로그램이 끝날 때
   for { struct P *q = &(…){1,2}; }  자동          ★ 바퀴마다

   for 두 바퀴
   0 바퀴 : q->x = 1  -> 99 로 고침     )  ★ 고친 값이 다음 바퀴로 안 넘어온다
   1 바퀴 : q->x = 1  -> 99 로 고침     )     = 바퀴마다 새 객체다
```

- **`sum((struct P){3,4})` 가 7** 이다. 복합 리터럴을 **인자로 그냥 넘길 수 있다.**
- **`g = (struct P){ .y = 5 };` 뒤 `g` 가 `{0,5}`** 다. ★ **지정 초기자 규칙이 그대로 적용**돼 `x` 가 0 이 됐다 —\
  복합 리터럴도 **초기자를 가진 집합체**이기 때문이다.
- **`gp->x=7 gp->y=8`** 이 `main` 에서 멀쩡히 읽힌다. **파일 스코프면 정적 저장 기간**이다.
- **두 바퀴가 둘 다 `1` 에서 시작**한다. 첫 바퀴에서 99 로 고친 것이 **안 넘어왔다** —\
  ★★ **바퀴마다 객체가 새로 만들어지고 블록 끝에서 죽는다**는 증거다.
- **`q->x = 99` 가 합법**이다. ★ 복합 리터럴은 **상수가 아니라 수정 가능한 lvalue** 다.\
  이름이 「리터럴」이라 문자열 리터럴과 헷갈리지만, **문자열 리터럴은 고치면 UB** 다([20번 형제](../20-null-terminated-strings-and-string-literals/)).

### 6. 수명이 끝난 복합 리터럴 — **`-O0` 과 `-O2` 가 갈리고 둘 다 안 죽는다** ★★★ 본체

**출력**

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

**왜 그런가**

```text
   make() 가 반환한 것

   호출 중                             반환 뒤
   +--------------------------+        +--------------------------+
   | make 의 스택 프레임       |        | ★ 그 프레임은 이미 없다   |
   |   (struct P){3, 30}      |        |   p 는 죽은 자리를 가리킨다|
   |        ^                 |        |                          |
   |        p 가 이것을 가리킨다|        +--------------------------+
   +--------------------------+

   그 자리를 읽으면 —
   -O0 : 죽은 프레임의 바이트를 그대로 읽는다   -> 쓰레기 숫자
   -O2 : 「읽을 것이 없다」고 판단해 접는다      -> 0 0
   ASan : 그 접근 자체를 가로챈다               -> stack-use-after-return
```

- **`-O0` 은 쓰레기 숫자**를, **`-O2` 는 `p->x = 0 p->y = 0`** 을 찍는다. **둘 다 `run exit=0`** 이다.
- ★★★ **어느 쪽도 「맞는 답」이 아니다.** UB 에는 맞는 답이 없다 —\
  **「안 죽었으니 괜찮다」가 이 주제에서 가장 비싼 추론**이다.
- ★ `-O0` 쪽의 숫자는 **실행마다 달라진다.** 근거로 쓸 것은 숫자가 아니라 **「두 벌이 갈렸다」는 사실**이다.
- ASan 은 **`stack-use-after-return`** 을 내고, 프레임을 **`make s21e2.c:5`** 로 짚는다 —\
  **복합 리터럴이 만들어진 바로 그 줄**이다. 접근한 줄은 **`main s21e2.c:14`** 다.
- ★ 배너의 **`run exit=1`** 이 ASan 이 낸 값이다 — **맨 실행 두 벌은 `run exit=0`** 이었다.\
  ★★ 「**죽었나**」가 아니라 「**어느 도구가 무엇을 냈나**」가 근거다. 같은 UB 가 세 벌에서 세 가지로 나왔다.
- ★★ **`setvbuf(stdout, NULL, _IONBF, 0)`** 는 **sanitizer 가 죽일 때 버퍼에 남은 표준 출력이 사라지는 것**을 막는다.\
  구분 마커를 **`fprintf(stderr, …)`** 로 찍은 것은 **표준 출력과 진단의 순서가 뒤집히는 것**을 막는다.
- 11번 답이 짝이다 — **이 UB 를 경고로 잡을 수 있는가**.

### 7. 배열은 **값이 아니라서**, 구조체는 **`==` 가 없어서** ★★

**출력**

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

**왜 그런가**

```text
   에러 세 줄

   b   = a;                 error: assignment to expression with array type
   s == t;                  error: invalid operands to binary ==
   arr = (int[3]){1,2,3};   error: assignment to expression with array type
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                            ★ 첫째와 셋째가 같은 에러다 — 왼쪽이 배열이면 끝이다

   되는 것과 안 되는 것
   구조체 : 대입 O · 인자 O · 반환 O · ==  X
   배열   : 대입 X · 인자 △(감쇠) · 반환 X · == △(주소 비교)
```

- **에러 3건 · 경고 2건 · `cc exit=1`** 이다.
- **첫째와 셋째가 같은 에러**다 — `assignment to expression with array type`.\
  ★ **오른쪽이 복합 리터럴이어도 왼쪽이 배열이면 안 된다.** 문제는 오른쪽이 아니라 **왼쪽의 타입**이다.
- **`s == t` 는 다른 에러**다 — `invalid operands to binary ==`.\
  ★★ 이것은 「다르다」가 아니라 「**그 연산자가 구조체에 정의돼 있지 않다**」는 뜻이다. **비교 자체가 없다.**
- 「그럼 `memcmp` 로」의 함정은 **패딩**이다. 멤버 값이 같아도 **패딩 바이트가 달라 0 이 아닐 수 있다** —\
  정본은 [22번 형제](../22-struct-padding-and-alignment/)이고 거기 **갈린 실측**이 있다.
- ★ 꼬리의 `-Wunused-but-set-variable` 2건은 **에러와 무관한 잡음**이다.\
  그래도 **블록에서 지우지 않았다** — 「한 글자도 더하거나 빼지 않는다」가 이 갈래의 규칙이다.

### 8. 경고가 붙는 것은 **`{ 80 }` 하나뿐이다** ★★★

**출력**

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

**왜 그런가**

```text
   같은 파일 · 같은 플래그 · 네 꼴

   struct Cfg z = {0};                          -> 0건
   struct Cfg p = { 80 };                       -> ★ 1건
   struct Cfg d = { .retry = 3, .host = "a" };  -> 0건
   struct Cfg m = { 8080, .t = 0.5 };           -> 0건

   뜻은 넷 다 같다 — 「일부만 적었고 나머지는 0 이다」
   그런데 경고는 하나다
```

- **`-Wall -Wextra` 로 경고 1건**, 붙은 줄은 **`struct Cfg p = { 80 };`** 이다.\
  진단 이름은 **`-Wmissing-field-initializers`** 이고 **`cc exit=0`** 이다.
- ★★ 그 경고는 **「위치 초기자가 멤버 수보다 적은 것」만** 본다.\
  **`= {0}` 은 특별 취급으로 빠지고**, **지정 초기자는 애초에 대상이 아니다.**
- ★ 그러니 이것은 **꼴을 보는 경고**이지 **뜻을 보는 경고가 아니다.**\
  「경고 0건이니 초기화를 다 적었다」는 **경고가 보는 것을 잘못 읽은 것**이다.
- ★★★ 여기서 나오는 실무 규칙 한 줄 — **멤버가 늘어날 구조체는 지정 초기자로 쓴다.**\
  멤버를 하나 붙여도 **기존 초기자가 전부 그대로 맞고**, 새 멤버는 **0 이 되고**, **경고도 안 난다.**
- ★ 짝이 되는 사실 — **위치 초기자로 쓴 코드는 멤버가 끼어들면 전부 밀린다.** 그때는 경고가 아니라 **타입 에러**가 나거나, 타입이 맞으면 **조용히 틀린다.**

### 9. C++ 는 **선언 순서를 요구한다** — C++20 에서도 ★★★

**출력**

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

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic s21g.cpp -o x (cc exit=1) =====
s21g.cpp: In function ‘int main()’:
s21g.cpp:6:28: warning: missing initializer for member ‘P::a’ [-Wmissing-field-initializers]
    6 |     P s = { .c = 3, .a = 1 };     /* C 에서는 되던 순서 밖 지정 초기자 */
      |                            ^
s21g.cpp:6:28: warning: missing initializer for member ‘P::b’ [-Wmissing-field-initializers]
s21g.cpp:6:28: error: designator order for field ‘P::a’ does not match declaration order in ‘P’
```

**왜 그런가**

```text
   같은 초기자 { .c = 3, .a = 1 }

   C   (-std=c17)      -> 통과. s = { 1, 0, 3 }
   C++ (-std=c++17)    -> 경고 4건 + ★ 에러 1건 · cc exit=1
                          (확장 경고 2 + missing initializer 2)
   C++ (-std=c++20)    -> 경고 2건 + ★ 에러 1건 · cc exit=1
                          (확장 경고만 사라졌다)

   남는 에러 : designator order for field 'P::a'
               does not match declaration order in 'P'
```

- **`-std=c++17` 은 문법 자체가 확장**이다 — `-Wc++20-extensions` 2건.\
  그런데 **경고로 끝나지 않는다.** 마지막 줄이 **에러**다.
- **`-std=c++20` 으로 올려도 같은 에러**가 남는다. ★★ **확장 경고만 사라졌을 뿐**이다.
- ★★★ 에러 문구가 요구하는 것은 「**선언 순서**」다. **C 는 그것을 요구하지 않는다** — 3번 답이 그 증거다.
- **두 벌 다 `cc exit=1`** 이다. 경고가 아니라 **빌드 실패**다.
- ★ 그래서 헤더를 C 와 C++ 양쪽에서 include 하는 프로젝트에서는 **C 쪽은 멀쩡한데 C++ 쪽 번역 단위만 깨진다.**\
  ★ C++ 의 중괄호 초기화 전반(`{}` 초기화·좁힘 변환 금지)은 **C++ 갈래가 정본**이다. 여기서는 **갈리는 한 줄**만 짚었다.

### 10. `-pedantic` 이 없으면 **아무 말도 안 해 준다** ★★

**출력**

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

**왜 그런가**

```text
   「언제부터인가」를 물어보는 법

   익명 구조체 멤버    gcc -std=c99 -pedantic   -> ISO C99 doesn't support
                                                   unnamed structs/unions
                                                   = ★ C11 부터라는 답

   빈 중괄호 = {}      gcc -std=c17 -pedantic   -> ISO C forbids empty initializer
                                                   braces before C2X
                                                   = ★ C23 부터라는 답
                       gcc -std=c2x             -> 경고 없이 통과, s = { 0, 0 }

   ★ 두 진단 모두 cc exit=0 이다 — 컴파일은 된다
```

- **익명 구조체 멤버는 C11 부터**, **빈 중괄호 `= {}` 는 C23 부터**다. 둘 다 **컴파일러에게 물어서** 얻은 답이다.
- **`-std=c17` 에서 `= {}` 를 던져도 `cc exit=0`** 이다 — **경고만 나오고 컴파일은 성공**한다.
- ★★★ **`-pedantic` 을 빼면 두 진단 모두 사라진다.** 그러면 **C99 에서 익명 구조체가, C17 에서 `= {}` 가 말없이 통과**한다.\
  ★ **「`-std=c17` 로 돌렸다」는 「C17 로 검증했다」가 아니다.** `-std=` 는 **강제가 아니라 기본값 선택**이다.
- ★ gcc 13 에는 **`-std=c23` 이 없다.** **`-std=c2x`** 를 써야 한다 —\
  잘못 쓰면 **경고 0건에 `cc exit=1`** 이 되어 「통과했다」로 오독된다.

### 11. **gcc `-O0` 0건 · clang 은 전부 0건** — 경고는 코드의 성질이 아니다 ★★★

**출력**

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

**왜 그런가**

```text
   같은 UB · 같은 소스 · 여덟 벌

            -O0    -O1    -O2    -O3        cc exit
   gcc       0      4      4      4           전부 0
   clang     0      0      0      0           전부 0

   gcc 가 내는 4건의 내역
     -Wdangling-pointer=   2건   <- 죽은 객체의 주소를 쓰고 있다
     -Wuninitialized       2건   <- 그 객체의 x 와 y 를 읽고 있다
```

- **gcc 는 `-O1` 부터 4건**을 낸다. **`-O0` 에서는 0건**이다 —\
  ★ 경고는 **최적화가 만든 데이터 흐름 분석의 부산물**이다. `-O0` 에서는 컴파일러가 거기까지 안 따라간다.
- **clang 18 은 `-O0`\~`-O3` 어느 벌에서도 0건**이다. ★★ **같은 UB 인데 컴파일러가 통째로 침묵한다.**
- **여덟 벌 전부 `cc exit=0`** 이다. ★ 이것을 같이 봐야 **「경고 0건」이 컴파일 실패 때문이 아니라는 것**이 확인된다.\
  종료 코드를 안 보면 **옵션 이름을 틀려 컴파일이 실패한 것**도 「경고 0건」으로 기록된다.
- ★ **`grep -c 'warning:'`** 로 센 이유는 clang 이 끝에 붙이는 **`N warnings generated.`** 요약 줄 때문이다.\
  `grep -c warning` 이면 그 줄까지 세어 **진단 수와 어긋난다.**
- ★★ 결론 한 줄 — **「경고 0건」은 코드의 성질이 아니라 컴파일러와 `-O` 의 성질**이다.\
  이 자리에서 믿을 것은 **ASan 하나**이고, ASan 은 **그 줄을 실제로 실행해야** 잡는다.

### 12. 다섯 층 — **표준이 본체이고 UB 는 한 자리뿐이다** ★★

**출력**

(이 문항은 앞 열한 문항의 블록을 묶어 읽는 것이라 새 블록이 없다.)

**왜 그런가**

| 층 | 이 주제에서 | 어떻게 확인했나 |
|---|---|---|
| **표준** | 멤버가 **선언 순서대로** 배치 · **구조체 대입 = 값 복사**(배열 멤버 포함) · **배열 대입 불가** · **구조체에 `==` 없음** · 초기자가 있으면 **안 적은 멤버 0** · 지정 초기자의 **순서 자유**와 **「뒤엣것이 이긴다」** · 복합 리터럴이 **lvalue** 이고 **블록이면 자동 · 파일 스코프면 정적** | 1·2·3·5·7번의 출력과 에러 |
| **조건부 표준** | **해당 없음** | — |
| **구현 정의** | **구조체의 크기와 패딩 자리**(`sizeof(struct Outer)` = 20) · 진단 **문구와 플래그 이름** | 4번의 `offsetof` · 두 컴파일러 대조 |
| **미명시** | **구조체 대입이 패딩까지 복사하는가** · 안 적은 멤버 **뒤의 패딩 값** | ★ 실측은 [22번 형제](../22-struct-padding-and-alignment/)에 있다 |
| **UB** | ★★★ **수명이 끝난 복합 리터럴 역참조** · 초기화 안 한 구조체 멤버 읽기 | 6번(`-O0` 대 `-O2`) · ASan |

- **비어 있는 칸은 「조건부 표준」** 하나다.
- ★★ **가장 두꺼운 칸**은 「**표준**」이다. 초기화·대입 규칙은 **어느 구현에서도 같다.**\
  [20번 형제](../20-null-terminated-strings-and-string-literals/)는 정반대였다 — 거기는 **UB 가 본체**이고 미명시가 두 번째였다.
- ★ **「구조체의 크기와 패딩 자리」는 이 주제가 아니다.** 정본은 [22번 형제](../22-struct-padding-and-alignment/)이고,\
  「`sizeof`·`offsetof` 라는 도구」는 [08번 형제](../08-sizeof-alignment-and-offsetof/)다.
- ★ **「복합 리터럴 전반」은 목록의 27번 주제**, **「초기화 안 한 객체」는 목록의 30번 주제**가 정본이다.\
  여기서는 각각 **저장 기간만**, **「초기자가 있으면」 쪽만** 봤다.
- 이 주제가 **끝까지 책임지는 것 셋** —\
  ① **구조체는 값이고 배열은 값이 아니다** ② **안 적은 멤버는 0 이다** ③ **복합 리터럴은 적은 자리가 수명을 정한다.**

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 컴파일러·플래그로 돌렸나 |
|---|---|---|
| `s21a.c` (21-a) | **`a.name == b.name` 이 0** · **`memcmp` 가 0** · `a` 는 그대로 `b` 만 바뀐 것 · 맨 배열은 `memcpy` | gcc `-std=c17 -Wall -Wextra -pedantic` 1벌(실행 포함) |
| `s21b.c` (21-b) | 네 초기화 꼴의 출력 · **안 적은 멤버가 전부 0** · **경고는 `{ 80 }` 한 줄에만 1건**(`-Wmissing-field-initializers`) · `cc exit=0` | gcc 2벌(실행·진단) |
| `s21c.c` (21-c) | 순서 밖 지정이 **선언 순서로** 채워지는 것 · 중복은 **뒤엣것이 이긴다** · 배열 지정 초기자 · **`-Woverride-init` 1건** | gcc 2벌(실행·진단) |
| `s21d.c` (21-d) | 중첩·익명 멤버의 접근 · **`offsetof` 다섯 값과 `sizeof` 20** · **`-std=c99 -pedantic` 이 익명 구조체를 1건 잡는다** | gcc 2벌(`-std=c17` 실행 · `-std=c99 -pedantic` 진단) |
| `s21e.c` (21-e) | 인자·대입·파일 스코프·블록 네 자리의 복합 리터럴 · `g = {0,5}` · **for 두 바퀴가 둘 다 1 에서 시작** | gcc 1벌(실행 포함) |
| `s21e2.c` (21-f) | ★★★ **`-O0` 쓰레기 대 `-O2` `0 0`** · **둘 다 `run exit=0`** · ASan **`stack-use-after-return`** · **gcc `-O1` 4건 · clang 전부 0건** | gcc 6벌(`-O0`·`-O1`·`-O2`·`-O3`·ASan·경고 세기) · clang 4벌(`-O0`\~`-O3`) |
| `s21f.c` (21-g) | **에러 3건**(배열 대입 2 · 구조체 `==` 1) · 경고 2건 · **`cc exit=1`** | gcc 1벌(진단만 — ★ **실행은 원리상 불가능하다**) |
| `s21g.cpp` (21-h) | C++17 **경고 4 + 에러 1** · C++20 **경고 2 + 에러 1** · **양쪽 다 `cc exit=1`** · 남는 에러는 **designator order** | g++ 2벌(`-std=c++17`·`-std=c++20`) |
| `s21h.c` (21-i) | `-std=c17 -pedantic` 이 **빈 중괄호를 1건** 잡는 것(`cc exit=0`) · **`-std=c2x` 는 통과하고 `s = { 0, 0 }`** | gcc 2벌(`-std=c17`·`-std=c2x`) |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3)에서만** 그렇다.

- **`sizeof(struct Outer)` = 20 과 `offsetof` 다섯 값** — ★ **구현 정의**다. 정본은 [22번 형제](../22-struct-padding-and-alignment/)다.
- **`-O0` 이 찍은 쓰레기 숫자** — ★★ **UB 의 산물이라 아무 근거도 못 된다.** 실행마다 달라진다.
- **`-O2` 가 `0 0` 을 찍은 것** — ★ 이것도 **UB 의 한 가지 발현**이다. 표준은 0 을 주라고 하지 않았다.
- **gcc 가 `-O1` 부터 4건을 내는 것 · clang 이 0건인 것** — ★★ **진단 구현의 차이**다. 버전이 오르면 바뀐다.
- **gcc 내부 임시 이름(`<Uf1b0>` 꼴)** — `-O1` 과 `-O2` 에서 **다른 문자열**이다. **대조 대상이 아니다.**
- **진단 문구와 플래그 이름** — 두 컴파일러가 서로 다르게 부른다.

**구조체 대입이 값 복사인 것 · 안 적은 멤버가 0 인 것 · 배열 대입이 에러인 것 · 복합 리터럴의 저장 기간은 구현 의존이 아니다.**\
**어느 C 구현에서도 같다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `s21f.c` 의 **실행**(★ 컴파일이 실패하므로 **원리상 불가능**하다) ·\
  **clang 으로 돌린 `s21a.c`\~`s21d.c`**(초기화·대입 규칙은 표준이라 갈릴 자리가 아니라고 보고 gcc 한 벌로 뒀다) ·\
  **`s21g.cpp` 를 clang++ 로 던진 것** · **복합 리터럴을 `static` 으로 선언한 블록 안 변수에 담았을 때** ·\
  **번역 단위가 여럿일 때 같은 복합 리터럴이 합쳐지는가.**
- **못 잰 것** — ★ **`-O2` 가 `0 0` 을 찍은 이유가 「0 으로 채웠다」인지 「접어서 상수가 됐다」인지.**\
  출력만으로는 가를 수 없다 — **어셈블리를 봐야 한다.** 그래서 「**`-O0` 과 갈렸다**」까지만 적었다.
- ★ **블록 없이 산문으로만 적은 것 하나** — 「**`-O0` 판의 숫자는 실행마다 달라진다**」.\
  그 자리는 **재현되지 않는 칸**이라 머리말의 「흔들리는 칸」 표에 올려 두었다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **clang 이 `-Wdangling-pointer=` 에 해당하는 진단을 갖게 됐는지**(지금은 `-O3` 에서도 0건).\
  **그러면 11번 답의 표가 통째로 바뀐다.**
- ★★ **gcc `-O0` 이 그 진단을 내게 됐는지**(지금은 `-O1` 부터다).
- ★ **gcc 가 `-std=c23` 을 받게 됐는지**(지금은 `-std=c2x` 다). **10번 답의 명령이 바뀐다.**
- ★ **`-Wmissing-field-initializers` 가 지정 초기자를 보게 됐는지**(지금은 대상이 아니다).\
  ★ **미명시·구현 정의가 아니라 진단 정책이라 언제든 바뀔 수 있다.**
- **구조체 대입·초기화 규칙·배열 대입 금지·복합 리터럴의 저장 기간은 다시 돌릴 필요가 없다** — C99 이후 바뀐 적이 없다.
