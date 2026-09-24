# c/syntax/25 — 불완전 타입과 opaque struct: 「**도면 없이 열쇠만 받은 방**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — Incomplete type (C)](https://en.cppreference.com/w/c/language/type) · [cppreference — Struct declaration (C)](https://en.cppreference.com/w/c/language/struct) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html) · [GCC 13 Optimize Options — `-flto`](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Optimize-Options.html) · [Clang Diagnostic flags](https://clang.llvm.org/docs/DiagnosticsReference.html)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값·진단·종료 코드는 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과\
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> **버전** — 불완전 타입과 opaque struct 관용구는 **C89 부터** 있고 규칙이 바뀐 적이 없다.\
> ★ **같은 `typedef` 를 두 번 쓰는 것**은 **C11 부터** 허용된다(아래 (9)). `-std=c99` 에서는 `-Wpedantic` 이 잡는다.\
> ★ **`-std=` 는 강제가 아니라 기본값 선택**이다 — 표준 준수를 주장하는 자리에는 전부 `-pedantic` 을 붙였고,\
> ★★ (5)에서는 **`-pedantic` 으로 모자라 `-pedantic-errors` 라야** 종료 코드가 움직였다.
> ★★ **경계** — **`void *` 라는 「무엇이든 가리키는 포인터」**는 [19번 형제](../19-void-pointer-null-pointer-and-null/)가 정본이다.\
> 여기서는 「**`void` 가 왜 불완전 타입인가**」만 본다 — 그쪽은 「**포인터**」, 여기는 「**타입의 완성 여부**」다.\
> ★ **`sizeof`·`offsetof` 라는 도구**는 [8번 형제](../08-sizeof-alignment-and-offsetof/), **구조체 선언·초기화**는 [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/)가 정본이다.\
> ★ **포인터 문법 자체**는 [14번 형제](../14-pointers-address-dereference-and-pointer-types/), **배열이 포인터로 감쇠하는 규칙**은 [16번 형제](../16-array-pointer-decay-and-function-parameters/)가 정본이다.\
> ★ **헤더를 어떻게 나누나**는 목록의 **44번 주제**, **링크 오류 읽기**는 목록의 **45번 주제**, **`malloc` 의 계약**은 목록의 **37번 주제**다.
> 선행 — [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/) · 목록의 **44번 주제**.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**불완전 타입은 「도면 없이 열쇠만 받은 방」이다.**

호텔에 묵는다고 하자. 프런트가 **카드키**를 준다. 방 번호도 알고 드나들 수도 있다.\
그런데 **방 도면은 안 준다.** 그래서 이런 일이 생긴다.

- 카드키는 **주머니에 들어간다** — 열쇠의 크기는 정해져 있으니까.
- ★ **방을 통째로 트럭에 싣지는 못한다** — 방이 몇 평인지 모르니 자리를 못 비운다.
- ★ **방을 세 개 나란히 예약하지도 못한다** — 한 칸이 몇 평인지 모르니 줄을 못 세운다.
- ★ 방 안의 **냉장고를 직접 열지도 못한다** — 도면이 없어 냉장고가 어디 있는지 모른다.
- 방 안에서 할 일은 전부 **프런트에 부탁한다** — 도면을 가진 쪽은 거기뿐이다.

| 비유 | 실체 | 층 |
|---|---|---|
| 방 번호 | 태그 이름 `struct Counter` | **표준** |
| 카드키 | `struct Counter *` — **포인터는 늘 완전한 타입**이다 | **표준** |
| 도면이 없다 | 멤버 목록이 이 번역 단위에 없다 = **불완전 타입** | **표준** |
| 방을 트럭에 싣기 | `struct Counter v;` · `sizeof` | **표준 — 컴파일 에러** |
| 방 세 개를 나란히 | `struct Counter a[3];` | **표준 — 컴파일 에러** |
| 냉장고를 직접 열기 | `p->n` | **표준 — 컴파일 에러** |
| 프런트에 부탁하기 | `ctr_tick(c)` — 정의를 가진 `.c` 의 함수 | **표준** |
| 도면을 **몰래 다시 그려** 오는 손님 | 다른 번역 단위가 제 맘대로 `struct Counter` 를 정의 | ★★★ **UB — 아무도 안 본다** |
| 「이 방은 몇 평이죠?」를 **영원히** 못 묻는 방 | `void` | **표준 — 완성될 수 없는 불완전 타입** |

```text
   헤더 (s25b.h)                    구현 (s25b.c)              쓰는 쪽 (s25b_main.c)
   ------------------------        ---------------------      -----------------------
   typedef struct Counter          struct Counter {           #include "s25b.h"
           Counter;                    long n;
                                       long step;             Counter *c = ctr_new(5);
   Counter *ctr_new(long);         };                         ctr_tick(c);
   void     ctr_tick(Counter *);                              ctr_get(c);
   long     ctr_get(const Counter*); malloc(sizeof *c)  <- 크기를 아는 곳은 ★ 여기뿐
   void     ctr_free(Counter *);

        ★ 이름만                        ★ 도면                   ★ 열쇠만 들고 다닌다
     = 불완전 타입                  = 완전한 타입                = 불완전 타입 + 포인터

   그래서 구현의 멤버를 바꿔도 ★ 쓰는 쪽은 다시 컴파일할 필요가 없다.
   그 대신 쓰는 쪽은 ★ sizeof 도 못 묻고 ★ 스택에도 못 놓는다.
```

- ★★★ **이 주제는 「표준」 칸이 본체**다 — 무엇이 에러이고 무엇이 되는지가 전부 표준에 적혀 있고, **두 컴파일러의 진단이 그대로 겹친다.**
- ★★ 두 번째 무게중심은 「**UB**」다 — 다만 **한 자리뿐**이고, 그 한 자리가 **어떤 도구에도 안 걸린다**(아래 (6)).
- ★ **구현 정의·미명시 칸은 거의 비어 있다.** 그것이 이 주제가 [22번 형제](../22-struct-padding-and-alignment/)·[24번 형제](../24-bit-fields/)와 **정반대인 점**이다.

> **불완전 타입(incomplete type)** — **이름은 정해졌는데 크기를 모르는** 타입.\
> 예: `struct Counter;` 만 써 놓으면 `Counter` 라는 이름은 쓸 수 있지만 `sizeof` 는 못 묻는다.

> **opaque struct(불투명 구조체)** — 헤더에 **태그 이름만** 노출하고 멤버 정의는 `.c` 안에 숨기는 관용구.\
> 예: `typedef struct Counter Counter;` 만 헤더에 두고 `struct Counter { … };` 는 `s25b.c` 에만 둔다.

> **번역 단위(translation unit)** — 전처리가 끝난 `.c` 파일 하나. 컴파일러가 한 번에 보는 범위다.\
> 예: `s25b.c` 와 `s25b_main.c` 는 **서로의 내용을 전혀 모른 채** 따로 번역되고 나중에 링크된다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **불완전 타입으로 무엇이 되고 무엇이 안 되나** — 그 경계가 **왜 거기인가.**
2. ★★★ **내부를 숨겨서 얻는 것과 잃는 것은 정확히 무엇인가** — 그리고 **그 숨김을 깨뜨리는 코드를 누가 잡아 주나.**
3. ★★ **「크기를 모른다」는 상태가 `struct` 말고 또 어디에 있나** — 그리고 그중 **영원히 완성되지 않는 것**은 무엇인가.

## 동작 방식

### (1) ★★ 불완전 타입은 세 가지뿐이다

**언제 쓰나** — 「이 타입이 불완전한가」를 판단할 때.

```text
   ① 선언만 된 struct / union / enum
      struct Counter;              태그는 있는데 멤버 목록이 없다
      ★ 같은 번역 단위 뒤쪽에 struct Counter { … }; 가 오면 ★ 그 자리에서 완성된다

   ② 크기를 안 적은 배열
      extern char msg[];           원소 타입은 아는데 몇 개인지 모른다
      ★ 다른 번역 단위(또는 뒤쪽)의 정의가 ★ 크기를 채워 준다

   ③ void
      ★ 영원히 완성되지 않는다 — 완성할 문법 자체가 없다

   공통 성질 — 「크기를 모른다」
      -> 저장 공간을 잡을 수 없다 (변수 · 배열 원소 · 구조체 멤버)
      -> sizeof 를 못 쓴다
      -> 멤버 접근을 못 한다 (①만 해당)
      그런데 ★ 그것을 가리키는 포인터는 언제나 ★ 완전한 타입이다 (크기 8바이트)
```

- ★★ **불완전 ≠ 못 쓴다.** 포인터로는 얼마든지 쓴다. 못 하는 것은 「**저장 공간을 잡는 일**」뿐이다.
- ★★ 불완전은 타입의 영구 성질이 아니라 「**그 지점에서의 상태**」다. `struct S;` 다음 줄에 `struct S { int x; };` 가 오면 그 뒤로는 완전한 타입이다.

### (2) ★★★ 되는 것과 안 되는 것 — 에러 카탈로그

**언제 쓰나** — 컴파일 에러를 보고 「무엇이 불완전한가」를 역추적할 때.

```c
/* s25a.c */
#include <stdio.h>

struct Hidden;                      /* 선언만 했다 — 불완전 타입 */

struct Hidden *make(void);          /* (가) 포인터는 된다 */
void use(struct Hidden *p);         /* (나) 매개변수로도 된다 */

int main(void) {
    struct Hidden *p = make();      /* OK */
    use(p);                         /* OK */

    struct Hidden v;                /* (1) 변수로 못 만든다 */
    struct Hidden a[3];             /* (2) 배열 원소로 못 쓴다 */
    printf("%zu\n", sizeof(struct Hidden));   /* (3) 크기를 못 묻는다 */
    printf("%d\n", p->x);           /* (4) 멤버를 못 만진다 */

    (void)v; (void)a;
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25a.c -o x (cc exit=1) =====
s25a.c: In function ‘main’:
s25a.c:12:19: error: storage size of ‘v’ isn’t known
   12 |     struct Hidden v;                /* (1) 변수로 못 만든다 */
      |                   ^
s25a.c:13:19: error: array type has incomplete element type ‘struct Hidden’
   13 |     struct Hidden a[3];             /* (2) 배열 원소로 못 쓴다 */
      |                   ^
s25a.c:14:28: error: invalid application of ‘sizeof’ to incomplete type ‘struct Hidden’
   14 |     printf("%zu\n", sizeof(struct Hidden));   /* (3) 크기를 못 묻는다 */
      |                            ^~~~~~
s25a.c:15:21: error: invalid use of undefined type ‘struct Hidden’
   15 |     printf("%d\n", p->x);           /* (4) 멤버를 못 만진다 */
      |                     ^~
s25a.c:13:19: warning: unused variable ‘a’ [-Wunused-variable]
   13 |     struct Hidden a[3];             /* (2) 배열 원소로 못 쓴다 */
      |                   ^
s25a.c:12:19: warning: unused variable ‘v’ [-Wunused-variable]
   12 |     struct Hidden v;                /* (1) 변수로 못 만든다 */
      |                   ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s25a.c -o x (cc exit=1) =====
s25a.c:12:19: error: variable has incomplete type 'struct Hidden'
   12 |     struct Hidden v;                /* (1) 변수로 못 만든다 */
      |                   ^
s25a.c:3:8: note: forward declaration of 'struct Hidden'
    3 | struct Hidden;                      /* 선언만 했다 — 불완전 타입 */
      |        ^
s25a.c:13:20: error: array has incomplete element type 'struct Hidden'
   13 |     struct Hidden a[3];             /* (2) 배열 원소로 못 쓴다 */
      |                    ^
s25a.c:3:8: note: forward declaration of 'struct Hidden'
    3 | struct Hidden;                      /* 선언만 했다 — 불완전 타입 */
      |        ^
s25a.c:14:21: error: invalid application of 'sizeof' to an incomplete type 'struct Hidden'
   14 |     printf("%zu\n", sizeof(struct Hidden));   /* (3) 크기를 못 묻는다 */
      |                     ^     ~~~~~~~~~~~~~~~
s25a.c:3:8: note: forward declaration of 'struct Hidden'
    3 | struct Hidden;                      /* 선언만 했다 — 불완전 타입 */
      |        ^
s25a.c:15:21: error: incomplete definition of type 'struct Hidden'
   15 |     printf("%d\n", p->x);           /* (4) 멤버를 못 만진다 */
      |                    ~^
s25a.c:3:8: note: forward declaration of 'struct Hidden'
    3 | struct Hidden;                      /* 선언만 했다 — 불완전 타입 */
      |        ^
4 errors generated.
```

```text
   되는 것                          안 되는 것
   ----------------------------    ---------------------------------------------
   struct Hidden *p;        OK     struct Hidden v;      ★ storage size ... isn't known
   함수 매개변수 (포인터)     OK     struct Hidden a[3];   ★ array type has incomplete
   함수 반환 타입 (포인터)    OK                             element type
   포인터끼리 대입·비교       OK     sizeof(struct Hidden) ★ invalid application of sizeof
                                    p->x                  ★ invalid use of undefined type

   ★ 경계는 한 줄이다 — 「크기를 알아야 하는 일」만 막힌다.
```

그림 해설 (한 단계씩):

- ★★★ **네 줄이 전부 에러이고 두 컴파일러의 문구가 짝을 이룬다.**\
  gcc 는 `storage size of 'v' isn't known`, clang 은 `variable has incomplete type 'struct Hidden'` 이다.
- ★★ **두 컴파일러가 에러 네 건을 똑같이 보고하는데 「덧붙이는 것」이 다르다.**\
  ★ **clang 은 네 에러마다 `note: forward declaration of 'struct Hidden'` 을 붙여 3번 줄을 가리킨다** — **원인 줄을 매번 같이 준다.**\
  ★ **gcc 는 그 note 가 없는 대신 `unused variable` 경고 2건을 더 낸다** — 에러로 죽은 변수를 **여전히 「안 쓴 변수」로 세는 것**이다.\
  ★★ 그래서 **「진단 줄 수」로 두 컴파일러를 견주면 안 된다** — gcc 는 짧고 clang 은 길지만 **에러 건수는 둘 다 4** 다.
- ★ **`cc exit=1`** 이다 — 경고가 아니라 **에러**다. 종료 코드까지 같이 읽어야 뜻이 산다.
- ★ **포인터 선언 `struct Hidden *p;` 에는 아무 말이 없다.** 이것이 이 주제 전체가 서 있는 발판이다.

비용 — 없다. **컴파일러가 전부 막아 준다.** 이 절의 값은 「**문구를 알아보는 것**」에 있다.

### (3) ★★★ opaque struct — 헤더에는 이름만 둔다

**언제 쓰나** — 라이브러리·모듈의 내부 표현을 바꿀 자유를 남기고 싶을 때.

```c
/* s25b.h */
#ifndef S25B_H
#define S25B_H

/* ★ 여기에 있는 것은 「이름」뿐이다 — 멤버가 무엇인지 쓰여 있지 않다 */
typedef struct Counter Counter;

Counter *ctr_new(long step);
void     ctr_tick(Counter *c);
long     ctr_get(const Counter *c);
void     ctr_free(Counter *c);

#endif
```

```c
/* s25b.c */
#include <stdlib.h>
#include "s25b.h"

struct Counter {                    /* ★ 정의는 이 번역 단위에만 있다 */
    long n;
    long step;
};

Counter *ctr_new(long step) {
    Counter *c = malloc(sizeof *c); /* 크기를 아는 것은 여기뿐이다 */
    if (c) { c->n = 0; c->step = step; }
    return c;
}
void ctr_tick(Counter *c)       { c->n += c->step; }
long ctr_get(const Counter *c)  { return c->n; }
void ctr_free(Counter *c)       { free(c); }
```

```c
/* s25b_main.c */
#include <stdio.h>
#include "s25b.h"

int main(void) {
    Counter *c = ctr_new(5);
    ctr_tick(c); ctr_tick(c); ctr_tick(c);
    printf("ctr_get = %ld\n", ctr_get(c));
    printf("포인터 크기는 안다 : sizeof(Counter *) = %zu\n", sizeof(Counter *));
    ctr_free(c);
    return 0;
}
```

```text
===== gcc -c 로 따로 번역한 뒤 링크한다 (exit=0) =====
s25b.o      OK  (정의가 있는 쪽)
s25b_main.o OK  (이름만 아는 쪽)
링크 OK
ctr_get = 15
포인터 크기는 안다 : sizeof(Counter *) = 8
```

```text
   따로 번역된다                     링크된다
   ----------------------------     ---------------------------
   s25b.c      -> s25b.o            s25b.o + s25b_main.o -> x
     struct Counter { long n;                 ^
                      long step; };           |
     ★ 도면을 아는 유일한 곳                    |
                                              |
   s25b_main.c -> s25b_main.o  -----------------
     Counter *c;   ★ 8바이트 열쇠만
     ctr_new / ctr_tick / ctr_get 은 ★ 이름만 알고 부른다

   ★ s25b.c 의 멤버를 바꿔도 s25b_main.o 는 다시 만들 필요가 없다.
   ★ 그 대신 s25b_main.c 는 sizeof(Counter) 를 영영 못 묻는다.
```

그림 해설 (한 단계씩):

- ★★★ **`sizeof *c` 를 쓰는 곳은 `ctr_new` 하나뿐**이다. 크기를 아는 곳이 하나면 **레이아웃을 바꿀 자유**가 거기 남는다.
- ★★ **쓰는 쪽은 `sizeof(Counter *)` 는 안다 — `8`** 이다. **포인터는 완전한 타입**이기 때문이고, 이 한 줄이 (1)의 규칙을 실행으로 보인 것이다.
- ★ **`typedef struct Counter Counter;`** 를 헤더에 두면 쓰는 쪽이 `struct` 를 안 써도 된다. **별칭은 불완전한 타입에도 붙는다**([6번 형제](../06-typedef-and-type-aliases/)가 정본).
- ★ **`ctr_free` 를 반드시 같이 내놓아야 한다.** 쓰는 쪽은 크기를 모르니 **제 손으로 해제할 수도 없다** — 소유권이 통째로 넘어간다(목록의 **38번 주제**).

비용 — 호출마다 **함수 한 번**을 거친다. 인라인이 안 되고 멤버를 직접 못 읽는다.

### (4) ★★ 대가 — 쓰는 쪽이 못 하게 되는 네 가지

**언제 쓰나** — 「내부를 숨길까 말까」를 결정할 때.

```c
/* s25c.c */
#include <stdio.h>
#include "s25b.h"

struct Job {
    Counter c;          /* (1) 값으로 품을 수 없다 */
    int id;
};

int main(void) {
    Counter local;              /* (2) 스택에 못 놓는다 */
    Counter *p = ctr_new(1);
    printf("%ld\n", p->n);      /* (3) 멤버를 못 읽는다 */
    printf("%zu\n", sizeof *p); /* (4) 크기를 못 묻는다 */
    (void)local;
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25c.c -o x (cc exit=1) =====
s25c.c:5:13: error: field ‘c’ has incomplete type
    5 |     Counter c;          /* (1) 값으로 품을 수 없다 */
      |             ^
s25c.c: In function ‘main’:
s25c.c:10:13: error: storage size of ‘local’ isn’t known
   10 |     Counter local;              /* (2) 스택에 못 놓는다 */
      |             ^~~~~
s25c.c:12:22: error: invalid use of incomplete typedef ‘Counter’
   12 |     printf("%ld\n", p->n);      /* (3) 멤버를 못 읽는다 */
      |                      ^~
s25c.c:13:28: error: invalid application of ‘sizeof’ to incomplete type ‘Counter’
   13 |     printf("%zu\n", sizeof *p); /* (4) 크기를 못 묻는다 */
      |                            ^
s25c.c:10:13: warning: unused variable ‘local’ [-Wunused-variable]
   10 |     Counter local;              /* (2) 스택에 못 놓는다 */
      |             ^~~~~
```

```text
   보통 구조체                        opaque struct
   ------------------------------    ------------------------------
   struct Job { Counter c; ... };    ★ field 'c' has incomplete type
   Counter local;                    ★ storage size of 'local' isn't known
   p->n                              ★ invalid use of incomplete typedef
   sizeof *p                         ★ invalid application of sizeof

   ★ 네 에러가 전부 같은 원인이다 — 「크기를 모른다」.
```

그림 해설 (한 단계씩):

- ★★ **값으로 품을 수 없다** — 다른 구조체의 멤버로 넣지 못한다. **포인터로만** 품는다.
- ★★ **스택에 못 놓는다** — 반드시 `ctr_new` 같은 **생성 함수**를 거쳐야 하고, 그 말은 **거의 언제나 할당 저장 기간**이 된다는 뜻이다([28번 형제](../28-choosing-among-four-storage-durations/)와 맞물린다).
- ★ **진단이 `incomplete typedef 'Counter'` 라고 적는다** — `struct` 를 안 썼는데도 **별칭을 그대로 불러 준다.** 원인 추적에 그대로 쓸 수 있다.
- ★ **`cc exit=1`** 이다. 이 대가는 **컴파일 시간에 전부 드러난다** — 실행 시간에 새어 나오는 것이 없다.

비용 — **모든 접근이 함수 호출**이 된다. 성능이 중요한 자리에서 이 관용구를 안 쓰는 이유가 그것이다\
(★ **다만 이 문서는 그 비용을 재지 않았다** — 재지 않은 성능 주장은 하지 않는다).

### (5) ★★★ `void` — 영원히 완성되지 않는 불완전 타입, 그리고 **exit 0 인데 ill-formed**

**언제 쓰나** — `void *` 로 산술을 하려 할 때. 그리고 「`-pedantic` 이면 표준 검증이 끝난 것인가」를 물을 때.

```c
/* s25d.c */
#include <stdio.h>

int main(void) {
    /* void 는 ★ 영원히 완성되지 않는 불완전 타입이다 */
    printf("sizeof(void)  = %zu\n", sizeof(void));

    int a[4] = {10, 20, 30, 40};
    void *vp = a;
    printf("vp        = %p\n", (void *)vp);
    printf("vp + 1    = %p   <- 몇 바이트 갔나?\n", (void *)(vp + 1));
    printf("차이      = %td 바이트\n", (char *)(vp + 1) - (char *)vp);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25d.c -o x ; ./x (cc exit=0 · run exit=0) =====
sizeof(void)  = 1
vp        = 0x7ffe7f3764f0
vp + 1    = 0x7ffe7f3764f1   <- 몇 바이트 갔나?
차이      = 1 바이트
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25d.c -o x (cc exit=0) =====
s25d.c: In function ‘main’:
s25d.c:5:44: warning: invalid application of ‘sizeof’ to a void type [-Wpointer-arith]
    5 |     printf("sizeof(void)  = %zu\n", sizeof(void));
      |                                            ^~~~
s25d.c:10:65: warning: pointer of type ‘void *’ used in arithmetic [-Wpointer-arith]
   10 |     printf("vp + 1    = %p   <- 몇 바이트 갔나?\n", (void *)(vp + 1));
      |                                                                 ^
s25d.c:11:52: warning: pointer of type ‘void *’ used in arithmetic [-Wpointer-arith]
   11 |     printf("차이      = %td 바이트\n", (char *)(vp + 1) - (char *)vp);
      |                                                    ^
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic-errors s25d.c -o x (cc exit=1) =====
s25d.c: In function ‘main’:
s25d.c:5:44: error: invalid application of ‘sizeof’ to a void type [-Wpointer-arith]
    5 |     printf("sizeof(void)  = %zu\n", sizeof(void));
      |                                            ^~~~
s25d.c:10:65: error: pointer of type ‘void *’ used in arithmetic [-Wpointer-arith]
   10 |     printf("vp + 1    = %p   <- 몇 바이트 갔나?\n", (void *)(vp + 1));
      |                                                                 ^
s25d.c:11:52: error: pointer of type ‘void *’ used in arithmetic [-Wpointer-arith]
   11 |     printf("차이      = %td 바이트\n", (char *)(vp + 1) - (char *)vp);
      |                                                    ^
```

```text
   같은 소스 · 같은 컴파일러 · 플래그 한 낱말 차이

   -pedantic         -> warning 3건 · ★ cc exit=0 · 실행되고 sizeof(void) 가 1 을 답한다
   -pedantic-errors  -> error   3건 · ★ cc exit=1 · 컴파일이 멈춘다

   ★ 「경고 0건」이 아니라 ★ 「경고는 났는데 종료 코드가 0」이다.
   ★ 그래서 빌드 스크립트가 ★ 통과로 기록한다.
```

그림 해설 (한 단계씩):

- ★★★ **`sizeof(void)` 가 `1` 을 답한다.** 표준에는 그런 값이 없다 — **gcc·clang 의 확장**이고, 그 확장 덕에 `void *` 산술이 `char *` 산술처럼 **1바이트씩** 움직인다(`vp + 1` 의 차이가 `1`).
- ★★★ **`-pedantic` 만으로는 `cc exit=0`** 이다. 「**`-pedantic` 을 붙였으니 표준 검증을 했다**」가 **여기서 깨진다** — 진단은 났는데 **빌드는 통과**한다.
- ★★ **`-pedantic-errors` 로 바꾸면 같은 세 줄이 `error:` 가 되고 `cc exit=1`** 이 된다. 문구도 플래그 이름(`[-Wpointer-arith]`)도 그대로다. **바뀐 것은 심각도뿐**이다.
- ★ **`void` 는 완성할 방법이 없다.** `struct S;` 는 뒤에 정의를 쓰면 완성되고 `extern char msg[];` 는 크기가 채워지지만, **`void` 에는 그런 문법이 없다.**
- ★ **`%p` 로 찍은 주소 두 줄은 실행마다 바뀐다**(ASLR). **안 흔들리는 것은 둘의 차이인 `1`** 이다.

비용 — **표준을 벗어난 편의**를 공짜로 쓰게 된다. 다른 컴파일러로 옮길 때 그 자리가 전부 터진다.

### (6) ★★★ 아무도 안 보는 자리 — 다른 번역 단위가 **도면을 제 맘대로 다시 그리면**

**언제 쓰나** — 「헤더를 안 쓰고 선언을 손으로 베껴 적어도 되나」를 물을 때. **이 편의 본체다.**

```c
/* s25e.c */
#include <stdlib.h>

struct Counter { long n; long step; };      /* ★ 이쪽의 정의 */

struct Counter *cnew(long step) { struct Counter *c = malloc(sizeof *c); c->n = 0; c->step = step; return c; }
void ctick(struct Counter *c)   { c->n += c->step; }
long cget(const struct Counter *c) { return c->n; }
void cfree(struct Counter *c)   { free(c); }
```

```c
/* s25e_main.c */
#include <stdio.h>

struct Counter { char tag; long n; };       /* ★ 저쪽과 다른 정의 — 헤더를 안 쓰고 손으로 적었다 */

struct Counter *cnew(long step);
void ctick(struct Counter *c);
long cget(const struct Counter *c);
void cfree(struct Counter *c);

int main(void) {
    struct Counter *c = cnew(3);
    ctick(c); ctick(c);
    printf("저쪽 함수로 읽으면 cget = %ld\n", cget(c));
    printf("이쪽 정의로 읽으면 tag = %d · n = %ld\n", c->tag, c->n);
    cfree(c);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25e.c s25e_main.c -o x ; ./x (cc exit=0 · run exit=0) =====
저쪽 함수로 읽으면 cget = 6
이쪽 정의로 읽으면 tag = 6 · n = 3
```

```text
===== 네 벌로 던져 본다 — 아무도 말하지 않는다 (exit=0) =====
gcc   none                         cc exit=0 경고 0건 | 저쪽 함수로 읽으면 cget = 6
clang none                         cc exit=0 경고 0건 | 저쪽 함수로 읽으면 cget = 6
gcc   -flto                        cc exit=0 경고 0건 | 저쪽 함수로 읽으면 cget = 6
gcc   -fsanitize=address,undefined cc exit=0 경고 0건 | 저쪽 함수로 읽으면 cget = 6
```

```text
   s25e.c 가 잡은 16바이트           s25e_main.c 가 읽는 법
   ---------------------------       -------------------------------
   +--------+--------+               +--+ (패딩 7) +--------+
   |  n(8)  | step(8)|               |t1|         |  n(8)  |
   +--------+--------+               +--+         +--------+
    ^ 6                               ^ 6 의 첫 바이트     ^ 실은 step 자리
    (2회 틱 × step 3)                   = tag 6            = 3

   ★ 그래서 tag = 6 · n = 3 이 나온다. ★ 둘 다 「그럴듯한 수」다.
   ★ 링커는 이름만 맞추고 ★ 구조체 내용은 오브젝트 파일에 아예 없다.
```

그림 해설 (한 단계씩):

- ★★★ **네 벌 전부 `cc exit=0` · 경고 0건 · `run exit=0`** 이다. gcc·clang·`-flto`·`-fsanitize=address,undefined` 가 **한 마디도 안 한다.**
- ★★★ **값이 그럴듯하다.** `tag = 6` 은 `n` 의 **첫 바이트**이고 `n = 3` 은 실은 `step` 이다. **둘 다 실제로 쓰인 수**라 「이상한 값이 나왔네」로도 안 걸린다.
- ★★ **구조체 레이아웃은 오브젝트 파일에 실리지 않는다.** 링커가 맞추는 것은 **이름**뿐이다 — 그래서 원리상 링크 시간에 잡을 것이 없다.
- ★ **이것이 opaque struct 의 진짜 값**이다. **정의를 아예 내놓지 않으면** 남이 다르게 적을 도면 자체가 없다.
- ★ 이 실험은 **손으로 선언을 베껴 적었기 때문에** 성립한다. `#include "s25b.h"` 를 썼다면 **정의가 한 곳뿐**이라 이 사고가 안 난다.

비용 — **헤더를 안 쓰고 선언을 베껴 적는 순간 이 문이 열린다.** 그리고 **닫아 줄 도구가 없다.**

**(6-나) `-flto` 는 무엇을 보고 무엇을 못 보나**

```c
/* s25f_main.c */
#include <stdio.h>

void ctick(int x);          /* ★ 이번에는 ★ 시그니처 ★ 가 어긋난다 */

int main(void) { ctick(1); printf("done\n"); return 0; }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25e.c s25f_main.c -o x (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -flto s25e.c s25f_main.c -o x (cc exit=0) =====
s25f_main.c:3:6: warning: type of ‘ctick’ does not match original declaration [-Wlto-type-mismatch]
    3 | void ctick(int x);          /* ★ 이번에는 ★ 시그니처 ★ 가 어긋난다 */
      |      ^
s25e.c:6:6: note: type mismatch in parameter 1
    6 | void ctick(struct Counter *c)   { c->n += c->step; }
      |      ^
s25e.c:6:6: note: ‘ctick’ was previously declared here
s25e.c:6:6: note: code may be misoptimized unless ‘-fno-strict-aliasing’ is used
```

```text
   어긋난 것          -flto 없이     -flto 켜고
   ---------------   -----------   --------------------------------------
   구조체 정의        ★ 침묵         ★ 침묵          <- (6)의 실험
   함수 시그니처      ★ 침묵         ★ 경고 1건       <- 여기
                                    [-Wlto-type-mismatch] + note 3줄
                                    ★ 그런데 cc exit=0 이다
```

- ★★★ **`-flto` 는 시그니처는 본다.** `void ctick(int)` 대 `void ctick(struct Counter *)` 를 잡아 `type mismatch in parameter 1` 이라고 적는다.
- ★★★ **그런데 구조체 내용은 못 본다.** (6)에서는 **양쪽 시그니처가 글자까지 같았다**(`void ctick(struct Counter *)`). 다른 것은 **그 이름이 가리키는 것**뿐이라 LTO 의 비교를 통과한다.
- ★★ **그리고 `cc exit=0`** 이다. `code may be misoptimized unless '-fno-strict-aliasing' is used` 라고까지 적어 놓고 **빌드는 성공**한다. (5)와 **같은 집안**이다.
- ★ 그래서 **이 주제의 네 번째 창은 「없다」가 답**이다 — 아래 「도구가 못 보는 것」에서 그렇게 센다.

### (7) ★★ 매개변수 목록 안에서 처음 나온 `struct` 는 **다른 타입**이다

**언제 쓰나** — `conflicting types` 인데 **양쪽 글자가 똑같아** 보일 때.

```c
/* s25g.c */
#include <stdio.h>

void show(struct Point *p);         /* ★ struct Point 가 여기서 처음 나온다 */

struct Point { int x, y; };         /* 그 뒤에 정의한다 */

void show(struct Point *p) { printf("(%d,%d)\n", p->x, p->y); }

int main(void) { struct Point q = {1, 2}; show(&q); return 0; }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25g.c -o x (cc exit=1) =====
s25g.c:3:18: warning: ‘struct Point’ declared inside parameter list will not be visible outside of this definition or declaration
    3 | void show(struct Point *p);         /* ★ struct Point 가 여기서 처음 나온다 */
      |                  ^~~~~
s25g.c:7:6: error: conflicting types for ‘show’; have ‘void(struct Point *)’
    7 | void show(struct Point *p) { printf("(%d,%d)\n", p->x, p->y); }
      |      ^~~~
s25g.c:3:6: note: previous declaration of ‘show’ with type ‘void(struct Point *)’
    3 | void show(struct Point *p);         /* ★ struct Point 가 여기서 처음 나온다 */
      |      ^~~~
```

```text
   void show(struct Point *p);      <- ★ 여기서 struct Point 가 ★ 태어난다
                                       스코프는 ★ 이 괄호 안까지다

   struct Point { int x, y; };      <- ★ 이것은 ★ 파일 스코프의 ★ 다른 struct Point

   void show(struct Point *p) {…}   <- 파일 스코프 쪽을 쓴다

   그래서 선언과 정의가 ★ 다른 타입을 받는 함수가 되고, 진단은
     have     'void(struct Point *)'
     previous 'void(struct Point *)'     ★ 글자가 똑같다
```

그림 해설 (한 단계씩):

- ★★★ **진단의 두 줄이 글자까지 같다.** `have 'void(struct Point *)'` 와 `previous declaration ... with type 'void(struct Point *)'` — **눈으로는 왜 충돌인지 알 수 없다.**
- ★★ **답은 앞줄의 경고에 있다** — `'struct Point' declared inside parameter list will not be visible outside of this definition or declaration`. 이 경고가 **원인**이고 에러는 **증상**이다.
- ★ **고치는 법은 한 줄**이다 — `struct Point;` 또는 정의를 **선언보다 위로** 올린다. 그러면 괄호 안의 이름이 **이미 있는 태그**를 가리킨다.
- ★ **`cc exit=1`** 이다. 이 함정은 **반드시 컴파일 에러로 드러난다** — 조용히 지나가지 않는다.

비용 — 없다. **경고를 읽기만 하면 된다.** 이 절의 값은 「**경고와 에러의 순서를 뒤집어 읽는 법**」이다.

### (8) ★ 크기를 안 적은 배열도 불완전 타입이다

**언제 쓰나** — `extern` 배열을 헤더에 적을 때.

```c
/* s25h.c */
char msg[6] = "hello";              /* ★ 여기서 완성된다 — 크기 6 */
```

```c
/* s25h_main.c */
#include <stdio.h>

extern char msg[];                  /* ★ 크기를 모르는 배열 = 불완전 타입 */

int main(void) {
    printf("msg   = %s\n", msg);    /* 읽기는 된다 (포인터로 감쇠) */
    printf("msg[1]= %c\n", msg[1]); /* 인덱싱도 된다 */
    printf("sizeof= %zu\n", sizeof msg);   /* ★ 크기는 못 묻는다 */
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25h_main.c s25h.c -o x (cc exit=1) =====
s25h_main.c: In function ‘main’:
s25h_main.c:8:36: error: invalid application of ‘sizeof’ to incomplete type ‘char[]’
    8 |     printf("sizeof= %zu\n", sizeof msg);   /* ★ 크기는 못 묻는다 */
      |                                    ^~~
```

```c
/* s25h_ok.c */
#include <stdio.h>

extern char msg[];                  /* 크기를 모르는 배열 = 불완전 타입 */

int main(void) {
    printf("msg    = %s\n", msg);   /* 읽기는 된다 — 포인터로 감쇠하니까 */
    printf("msg[1] = %c\n", msg[1]);/* 인덱싱도 된다 */
    printf("★ sizeof msg 는 이 번역 단위에서 쓸 수 없다\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25h_ok.c s25h.c -o x ; ./x (cc exit=0 · run exit=0) =====
msg    = hello
msg[1] = e
★ sizeof msg 는 이 번역 단위에서 쓸 수 없다
```

```text
   s25h.c        char msg[6] = "hello";   <- ★ 여기서 완성된다
   s25h_main.c   extern char msg[];       <- ★ 여기서는 끝까지 불완전하다

   읽기   msg      -> 포인터로 감쇠하므로 크기가 필요 없다     OK
   인덱싱 msg[1]   -> *(msg + 1) 이므로 크기가 필요 없다       OK
   크기   sizeof msg                                          ★ 에러

   ★ 같은 객체인데 번역 단위에 따라 sizeof 를 쓸 수 있고 없고가 갈린다.
```

그림 해설 (한 단계씩):

- ★★ **같은 객체의 `sizeof` 가 한쪽에서는 되고 한쪽에서는 에러**다. 「크기를 아느냐」는 **객체의 성질이 아니라 그 번역 단위의 상태**다.
- ★★ **읽기와 인덱싱은 된다** — 둘 다 **포인터로 감쇠**해서 크기를 안 쓰기 때문이다([16번 형제](../16-array-pointer-decay-and-function-parameters/)가 정본).
- ★ **그래서 헤더에는 `extern char msg[6];` 처럼 크기를 적는 쪽이 낫다** — 다만 그러면 크기를 바꿀 때 **양쪽을 같이 고쳐야** 하고, 안 고치면 (6)과 같은 무음 사고가 난다.
- ★ 진단이 타입을 **`char[]`** 라고 적는다 — 「원소 타입은 아는데 개수를 모른다」가 그대로 보인다.

비용 — **헤더에 크기를 적으면 (6)의 위험이, 안 적으면 `sizeof` 를 잃는다.** 둘 중 하나를 고르는 자리다.

### (9) ★ 상호 참조와 `typedef` 반복

**언제 쓰나** — 연결 리스트·그래프처럼 **두 구조체가 서로를 가리킬** 때.

```c
/* s25i.c */
#include <stdio.h>

typedef struct Node Node;           /* ① 불완전한 채로 별칭을 만든다 */
typedef struct Node Node;           /* ② 같은 typedef 를 또 쓴다 — C11 부터 허용 */

struct Edge;                        /* ③ 상호 참조를 위한 선언 */
struct Node { int v; struct Edge *out; };
struct Edge { Node *to; int w; };   /* ④ 여기서 Edge 가 완성된다 */

int main(void) {
    Node b = {2, 0};
    struct Edge e = {&b, 7};
    Node a = {1, &e};
    printf("a.v=%d -> w=%d -> v=%d\n", a.v, a.out->w, a.out->to->v);
    printf("sizeof(Node)=%zu sizeof(struct Edge)=%zu\n", sizeof(Node), sizeof(struct Edge));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25i.c -o x ; ./x (cc exit=0 · run exit=0) =====
a.v=1 -> w=7 -> v=2
sizeof(Node)=16 sizeof(struct Edge)=16
```

```text
===== gcc -std=c99 -Wall -Wextra -pedantic s25i.c -o x (cc exit=0) =====
s25i.c:4:21: warning: redefinition of typedef ‘Node’ [-Wpedantic]
    4 | typedef struct Node Node;           /* ② 같은 typedef 를 또 쓴다 — C11 부터 허용 */
      |                     ^~~~
s25i.c:3:21: note: previous declaration of ‘Node’ with type ‘Node’
    3 | typedef struct Node Node;           /* ① 불완전한 채로 별칭을 만든다 */
      |                     ^~~~
```

```text
   typedef struct Node Node;      ① 불완전한 채로 별칭을 만든다   ★ 이것이 된다
   typedef struct Node Node;      ② 같은 typedef 를 또 쓴다      ★ C11 부터
   struct Edge;                   ③ 상호 참조를 위한 선언
   struct Node { int v; struct Edge *out; };   ★ Edge 가 불완전해도 ★ 포인터니까 된다
   struct Edge { Node *to; int w; };           ④ 여기서 Edge 가 완성된다

   ★ 순환이 풀리는 이유는 하나다 — 서로를 ★ 포인터로 ★ 가리키기 때문이다.
   ★ 값으로 품으면 순환이 풀리지 않는다 (크기가 서로를 요구한다).
```

그림 해설 (한 단계씩):

- ★★ **`struct Edge;` 한 줄이 순환을 푼다.** `Node` 안의 `struct Edge *out` 은 **크기를 안 쓰므로** `Edge` 가 불완전해도 된다.
- ★★ **같은 `typedef` 를 두 번 쓰는 것은 C11 부터** 허용된다. `-std=c99 -pedantic` 에서는 `redefinition of typedef 'Node' [-Wpedantic]` 가 나온다 — ★ **경고이고 `cc exit=0`** 이다((5)와 같은 모양).
- ★ 이 성질이 실무에서 값이 나는 자리는 **헤더가 서로를 `#include` 할 때**다. 같은 `typedef` 가 두 헤더에서 들어와도 C11 이후로는 문제가 없다.
- ★ `sizeof(Node)` 가 **16** 인 것은 `int` 4 + 패딩 4 + 포인터 8 이다([22번 형제](../22-struct-padding-and-alignment/)가 정본).

비용 — **선언을 하나 더 쓰는 수고.** 그 밖에는 없다.

## 문법 — 형태와 규칙

### 형태 — 불완전 타입을 만드는 세 가지와 완성하는 법

```text
/* ① 태그만 선언한다 — struct · union · enum 이 다 된다 */
struct Counter;
union  Value;
/* ★ enum 은 다르다 — C23 이전에는 「선언만」이 표준이 아니다 (아래 규칙 불릿) */

/* 완성 — 같은 스코프에 정의가 오면 그 자리부터 완전한 타입이다 */
struct Counter { long n; long step; };

/* ② 크기를 안 적은 배열 */
extern char msg[];                 /* 다른 번역 단위(또는 뒤쪽)의 정의가 채운다 */
char msg[6] = "hello";             /* 여기서 완성된다 */

/* ③ void — 완성할 문법이 없다 */

/* opaque struct 관용구 — 헤더에 둘 것 */
typedef struct Counter Counter;    /* 이름만 */
Counter *ctr_new(long step);       /* 만드는 함수 */
void     ctr_free(Counter *c);     /* ★ 없으면 쓰는 쪽이 해제할 방법이 없다 */
```

### 금지 사례 — 어느 것이 무슨 층인가

```text
struct Hidden;                    /* 선언만 했다 */

struct Hidden v;                  /* ★ 컴파일 에러 — storage size isn't known */
struct Hidden a[3];               /* ★ 컴파일 에러 — array type has incomplete element type */
struct Job { struct Hidden h; };  /* ★ 컴파일 에러 — field has incomplete type */
size_t n = sizeof(struct Hidden); /* ★ 컴파일 에러 — invalid application of sizeof */
p->x;                             /* ★ 컴파일 에러 — invalid use of undefined type */

size_t z = sizeof(void);          /* ★★ 경고뿐 — gcc/clang 확장. cc exit=0 에 값은 1 */
void *q; q + 1;                   /* ★★ 경고뿐 — 같은 확장. -pedantic-errors 라야 막힌다 */

void show(struct Point *p);       /* ★ 파일 스코프에 struct Point 가 없으면 ★ 새 타입이 태어난다 */

/* 다른 .c 가 헤더를 안 쓰고 손으로 적는다 */
struct Counter { char tag; long n; };   /* ★★★ UB — 어떤 도구도 안 본다 */

struct Counter *p = malloc(sizeof *p);  /* ★ 쓰는 쪽에서는 컴파일 에러 — 크기를 모른다 */
```

### 규칙 불릿

- ★★★ **불완전 타입으로 못 하는 일은 하나뿐이다 — 「크기를 쓰는 일」.** 변수·배열 원소·구조체 멤버·`sizeof`·멤버 접근이 전부 거기 걸린다.
- ★★★ **불완전 타입을 가리키는 포인터는 언제나 완전한 타입**이다. opaque struct 관용구 전체가 이 한 줄 위에 선다.
- ★★ 불완전은 「**그 지점에서의 상태**」다. 같은 번역 단위 뒤쪽에 정의가 오면 그때부터 완전하다.
- ★★ **불완전 타입은 셋뿐이다** — 선언만 된 `struct`/`union`, 크기 없는 배열, `void`.\
  ★ **`enum` 은 갈린다** — C23 이전에는 `enum E;` 만 쓰는 것이 표준이 아니다([7번 형제](../07-enum-and-enumeration-constants/)가 정본).
- ★★★ **`void` 는 완성될 수 없다.** 그래서 `void *` 산술과 `sizeof(void)` 는 **표준 밖**이고, gcc·clang 은 **`1` 로 확장**해 준다.
- ★★ **`-pedantic` 은 심각도를 안 바꾼다.** 표준 위반을 **빌드 실패로** 만들려면 `-pedantic-errors` 가 필요하다.
- ★★★ **두 번역 단위가 같은 태그를 다르게 정의하면 UB 이고, 이것을 잡아 주는 도구가 없다.** `-flto` 도 **시그니처만** 본다.
- ★★ **매개변수 목록 안에서 처음 나온 태그는 그 괄호 안에서만 산다.** 그래서 선언과 정의가 **다른 타입**이 된다.
- ★ **크기를 안 적은 `extern` 배열은 읽기·인덱싱은 되고 `sizeof` 만 안 된다.**
- ★ **상호 참조는 포인터로만 풀린다.** 값으로 품으면 크기가 서로를 요구해 풀리지 않는다.
- ★ **같은 `typedef` 반복은 C11 부터.** `-std=c99 -pedantic` 에서는 경고(`cc exit=0`)다.
- ★ **opaque 로 만들면 `_free` 함수를 반드시 같이 내놓는다.** 쓰는 쪽은 크기를 모르니 해제도 못 한다.

## 어디서 틀리나

### 1. ★★★ 「헤더 쓰기 귀찮으니 선언만 베껴 적자」

**여기서 끝난다.** (6)에서 두 번역 단위가 `struct Counter` 를 다르게 정의했는데\
**gcc·clang·`-flto`·ASan+UBSan 네 벌이 전부 침묵**했고 값도 그럴듯했다.\
★ **선언은 베껴도 되지만 정의는 절대 안 된다.** 정의가 두 군데 있으면 그 순간부터 **아무도 안 본다.**

### 2. ★★★ 「`-pedantic` 붙였으니 표준으로 검증했다」

**아니다.** (5)에서 `sizeof(void)` 가 **경고 3건에 `cc exit=0`** 으로 통과했고 실행되어 `1` 을 답했다.\
★ **빌드 실패로 만들려면 `-pedantic-errors`** 다. 「경고 0건」이 아니라 「**경고는 났는데 종료 코드가 0**」이 위험한 모양이다.

### 3. ★★ 「`conflicting types` 인데 두 줄이 똑같다」

(7)이다. **진단을 위에서부터** 읽어라 — `declared inside parameter list` 경고가 **원인**이고,\
글자가 같은 `conflicting types` 는 **증상**이다. ★ 고치는 법은 `struct Point;` **한 줄**이다.

### 4. ★★ 「opaque 인데 왜 스택에 못 놓지」

**크기를 모르니까**다((4)). opaque 를 고르는 순간 그 객체는 **거의 언제나 할당 저장 기간**이 된다\
([28번 형제](../28-choosing-among-four-storage-durations/)). ★ 그 대가를 감당할 수 없으면 **정의를 헤더에 내놓아야** 한다 — 절충은 없다.

### 5. ★★ 「`_free` 는 나중에 만들지」

쓰는 쪽은 **크기를 모르므로** `free(c)` 를 못 부르는 것이 아니라\
**부를 수는 있어도 그것이 맞는지 판단할 수 없다**(내부에 또 다른 할당이 있을 수 있다).\
★ **생성 함수를 내놓는 순간 짝이 되는 해제 함수도 같이 내놓는다.**

### 6. ★ 「`void *` 로 바이트 계산을 하면 편하던데」

**gcc·clang 의 확장**이다((5)). 표준에서는 `sizeof(void)` 도 `void *` 산술도 없다.\
★ **`char *` 또는 `unsigned char *` 로 캐스트해서 쓴다.** 뜻이 같고 이식된다.

### 7. ★ 「`extern char msg[];` 로 적어도 `sizeof` 는 되겠지」

**안 된다**((8)). 같은 객체인데 **정의가 있는 번역 단위에서만** 크기를 안다.

### 8. ★ 「불완전 타입은 못 쓰는 타입이다」

**아니다.** 포인터로는 얼마든지 쓴다. 못 하는 것은 「**저장 공간을 잡는 일**」뿐이고,\
그 제약이 바로 **캡슐화의 재료**다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 압도적으로 두껍다** — 무엇이 에러인지가 전부 표준에 적혀 있고 **두 컴파일러가 짝을 이룬다.**\
★★ 두 번째는 「**UB**」인데 **자리가 하나뿐**이고, 그 하나가 **어떤 도구에도 안 걸린다.**\
★ **구현 정의 칸은 얇고 미명시 칸은 비어 있다** — [22번 형제](../22-struct-padding-and-alignment/)·[24번 형제](../24-bit-fields/)와 **정반대**다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준 (본체)** | 어느 구현에서도 같다 | 불완전 타입 세 가지 · **변수·배열 원소·구조체 멤버·`sizeof`·멤버 접근이 전부 에러**인 것 · **포인터는 완전한 타입**인 것 · 정의가 오면 **그 자리부터 완전**해지는 것 · **매개변수 목록 안의 태그가 그 괄호 안에서만 사는 것** · 상호 참조가 **포인터로만** 풀리는 것 · `typedef` 반복이 **C11 부터**인 것 | gcc·clang 에러 전문 4벌(`cc exit=1`) · `sizeof(Counter *)` = **8** · 3파일 분할 컴파일·링크 성공 · `conflicting types` 두 줄이 **글자까지 같은** 진단 · `-std=c99 -pedantic` 의 `redefinition of typedef` |
| **조건부 표준** | 매크로가 정의될 때만 | ★ **해당 없음** — 불완전 타입에는 매크로로 켜고 꺼지는 보장이 없다 | — |
| ★ **구현 정의** | 문서화 의무가 있다 | ★ **얇다.** 포인터의 크기(`8`) · 진단 문구와 플래그 이름 · `-flto` 가 **무엇까지 대조하는가** | `sizeof(Counter *)` = 8 · `[-Wlto-type-mismatch]` 가 **시그니처만** 잡음 |
| **미명시** | 몇 가지 중 하나 · 문서화 의무도 없다 | ★ **이 주제에는 없다.** 여기서 값이 갈리는 자리는 **미명시가 아니라 UB** 다 | — |
| ★★ **UB (자리는 하나)** | 아무 일이나 | ★★★ **두 번역 단위가 같은 태그를 다르게 정의하고 그 포인터를 주고받는 것** · ★ `void *` 산술과 `sizeof(void)` 는 UB 가 아니라 **확장**이다(표준 밖이지만 구현이 정의한다) | ★★ **네 벌**(gcc · clang · `-flto` · ASan+UBSan) 전부 **`cc exit=0` · 경고 0건 · `run exit=0`** · 값은 `tag = 6 · n = 3` 으로 **그럴듯했다** |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★ 여기는 **도구가 거의 다 본다** — 다섯 가지 금지가 전부 **컴파일 에러**(`cc exit=1`)다. ★ 다만 **`conflicting types` 의 원인은 안 알려 준다** — 두 줄의 글자가 같아서, **그 위의 경고를 읽어야만** 왜 충돌인지 안다 |
| **조건부 표준** | ★ **해당 없음** — 볼 것이 없으니 도구도 할 말이 없다 |
| **구현 정의** | ★★ **`-flto` 가 무엇을 대조하는지 도구가 말해 주지 않는다.** 시그니처는 잡고 **구조체 내용은 안 잡는데**, 어느 쪽인지는 **던져 봐야** 안다 |
| **미명시** | ★ **해당 없음** |
| ★★★ **UB** | ★★★ **두 번역 단위의 정의 불일치를 보는 도구가 없다.** 구조체 레이아웃은 **오브젝트 파일에 실리지 않으므로** 링커가 볼 것이 없고, `-flto` 도 **이름이 같으면 통과**시킨다. ★★ **ASan·UBSan 도 원리상 무력하다** — 메모리 접근은 **할당된 범위 안**이고 산술 문제도 아니다. ★ **처방은 도구가 아니라 규율이다 — 정의를 한 곳에만 둔다** |
| ★★ **(층을 가로지름)** | ★★★ **「종료 코드가 0인데 ill-formed」가 이 주제에서 세 번 나왔다** — ① `sizeof(void)`·`void *` 산술(`-pedantic` 으로는 경고, `-pedantic-errors` 라야 `cc exit=1`) ② `-Wlto-type-mismatch`(「misoptimized 될 수 있다」고 적고 `cc exit=0`) ③ `-std=c99` 의 `typedef` 반복. **경고 건수만 세는 빌드는 셋 다 통과로 기록한다** |

- ★★ **이 표의 결론 네 줄**
  - ★★★ 가장 조용한 자리는 「**두 정의**」다 — **컴파일도 링크도 실행도 통과하고 값까지 그럴듯하다.** 그 자리를 막는 것은 도구가 아니라 **정의를 한 곳에만 두는 규율**이다.
  - ★★ 그래서 opaque struct 는 「**숨기는 기법」이기 전에 「정의를 하나로 못 박는 장치**」다. 헤더에 정의가 없으면 **베낄 도면 자체가 없다.**
  - ★★ **반대로 이 주제의 나머지는 전부 컴파일 시간에 드러난다** — 실행 시간으로 새어 나오는 것이 없다. 그래서 **에러 문구를 알아보는 것**이 인출의 대부분이다.
  - ★ **`-pedantic` 과 `-pedantic-errors` 를 갈라 쓰는 습관**이 (5)에서 값을 냈다. 표준 준수를 **주장**하려면 앞엣것, **강제**하려면 뒤엣것이다.

### 이 주제의 네 번째 창 — **없다는 것이 답이다**

- **컴파일 진단**은 (2)·(4)·(7)·(8)을 전부 잡는다 — 이 주제의 **세 창 중 가장 세다.**
- **링커**는 (6)에 대해 할 말이 없다 — **구조체 레이아웃이 오브젝트 파일에 없다.**
- **실행 출력**은 (6)에서 **그럴듯한 값**을 준다 — 창이 아니라 **함정**이다.
- ★★ **네 번째 창 후보는 `-flto` 였다.** 실제로 던져 보니 **시그니처는 잡고 구조체 정의는 못 잡았다.**
- ★★★ 그래서 이 주제의 답은 「**창이 없다**」이다. 다른 주제들이 「네 번째 창을 찾아라」였다면 여기서는 「**창이 없으니 애초에 그 상태를 못 만들게 하라**」가 결론이고, 그 장치가 **opaque struct** 다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 라이브러리 내부 표현을 숨기기 | **opaque struct** — 헤더에 `typedef struct S S;` 만 | 멤버를 헤더에 내놓고 「만지지 마세요」 주석 |
| 그 객체를 만들기 | **생성 함수** `S *s_new(...)` | 쓰는 쪽에서 `malloc(sizeof(S))` (에러다) |
| 그 객체를 없애기 | ★ **짝이 되는 `s_free(S *)` 를 같이 내놓는다** | `free(s)` 를 쓰는 쪽에 맡기기 |
| 두 구조체가 서로를 가리키기 | **`struct B;` 선언 + 포인터 멤버** | 값으로 품기(순환이 안 풀린다) |
| 다른 `.c` 의 함수를 부르기 | ★★ **헤더를 `#include` 한다** | ★★★ 선언을 손으로 베껴 적기 |
| 헤더에 배열을 내놓기 | `extern char msg[6];`(크기를 적는다) | `extern char msg[];` 뒤에 `sizeof` (에러다) |
| 바이트 단위 포인터 산술 | **`char *`·`unsigned char *` 로 캐스트** | `void *` 에 `+ 1` (표준 밖 확장) |
| 표준 위반을 **빌드에서 막기** | ★★ **`-pedantic-errors`** | `-pedantic` 만 붙이고 「검증했다」 |
| 크기를 꼭 알아야 하는 값 | **정의를 헤더에 내놓는다** | opaque 로 두고 `sizeof` 를 시도 |
| 숨김이 깨졌는지 확인하기 | ★★★ **정의를 한 곳에만 두는 규율** | ASan·UBSan·`-flto` 를 믿기 |

판단 규칙 두 줄.

- ★★★ **내부를 바꿀 자유를 사려면 크기를 포기한다 — 그 거래가 opaque struct 전부다.**
- ★★ **선언은 헤더에서 오고, 정의는 한 곳에만 있다.** 이 둘을 어기는 순간 도구가 손을 뗀다.

## 핵심 문장

- ★★★ **불완전 타입으로 못 하는 일은 「크기를 쓰는 일」 하나뿐**이고, **포인터는 언제나 완전하다.**
- ★★★ **두 번역 단위가 같은 태그를 다르게 정의하면 아무 도구도 안 본다** — 네 벌 전부 `cc exit=0` · 경고 0건 · 값도 그럴듯했다.
- ★★★ **`-flto` 는 시그니처는 보고 구조체 정의는 못 본다.**
- ★★ **`-pedantic` 은 심각도를 안 바꾼다** — `sizeof(void)` 가 **경고 3건에 `cc exit=0`** 으로 통과하고 `1` 을 답했다. `-pedantic-errors` 라야 `cc exit=1`.
- ★★ **`void` 는 영원히 완성되지 않는 불완전 타입**이다. `void *` 산술은 표준이 아니라 **확장**이다.
- ★★ **매개변수 목록 안에서 처음 나온 태그는 그 괄호 안에서만 산다** — 그래서 `conflicting types` 의 두 줄이 **글자까지 같아진다.**
- ★★ **opaque 를 고르면 스택에 못 놓는다** — 그 객체는 거의 언제나 **할당 저장 기간**이 된다.
- ★ **크기를 안 적은 `extern` 배열은 읽기·인덱싱은 되고 `sizeof` 만 안 된다.**
- ★ **상호 참조는 포인터로만 풀린다.**
- ★ **생성 함수를 내놓았으면 해제 함수도 같이 내놓는다.**

## 관련 자료

- [19번 형제 — `void *`·널 포인터·`NULL`](../19-void-pointer-null-pointer-and-null/) — ★★ **경계.**\
  그쪽은 「**무엇이든 가리키는 포인터를 어떻게 쓰나**」까지, 여기는 「**`void` 가 왜 완성될 수 없는 타입인가**」부터다.\
  ★ `void *` 산술과 `sizeof(void)` 가 **확장**이라는 실측은 여기 (5)에 있다.
- [8번 형제 — `sizeof`·정렬·`offsetof`](../08-sizeof-alignment-and-offsetof/) — ★ 재는 **도구**의 정본.\
  여기는 「**그 도구를 못 쓰는 상태**」만 다룬다.
- [21번 형제 — 구조체 선언·초기화·지정 초기자](../21-struct-declaration-initialization-and-designated-initializers/) — ★★ **직접 선행.**\
  그쪽은 「**정의가 있는 구조체를 어떻게 쓰나**」, 여기는 「**정의를 안 보여 주면 무엇이 달라지나**」다.
- [6번 형제 — `typedef` 와 타입 별칭](../06-typedef-and-type-aliases/) — ★ **별칭은 불완전한 타입에도 붙는다**는 것이 이 편의 발판이다.
- [16번 형제 — 배열-포인터 감쇠와 함수 매개변수](../16-array-pointer-decay-and-function-parameters/) — ★ (8)에서 **읽기·인덱싱이 되는 이유**가 감쇠다.
- [26번 형제 — 유연 배열 멤버](../26-flexible-array-members/) — ★ **「마지막 멤버의 크기를 안 적는다」는 다른 문법**이다. 그쪽은 **구조체가 완전한 채로** 꼬리만 비어 있다.
- [28번 형제 — 저장 기간 4종을 고르는 법](../28-choosing-among-four-storage-durations/) — ★★ opaque 를 고르면 **할당 저장 기간**으로 떠밀린다.
- [22번 형제 — 구조체 패딩·정렬](../22-struct-padding-and-alignment/) · [24번 형제 — 비트필드](../24-bit-fields/) — ★ **정반대의 주제**다. 그쪽은 「구현 정의·미명시」가 본체이고 여기는 「표준」이 본체다.
- 목록의 **44번 주제** — 헤더와 분할 컴파일. **무엇을 헤더에 두나**는 그쪽이 정본이다.
- 목록의 **45번 주제** — 번역 단위와 링크 오류 읽기. `undefined reference` 는 그쪽이다.
- 목록의 **37번 주제** — `malloc` 계열의 계약. 생성 함수 안의 할당은 그쪽이 정본이다.
- 목록의 **38번 주제** — 소유권 관례. **`_new`/`_free` 짝**을 시그니처로 표현하는 법은 그쪽이다.
- ★ **C++ 갈래와 갈리는 자리** — C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))에서 다룬다.\
  ★ C 에서는 `struct Counter` 를 쓸 때마다 `struct` 를 적거나 `typedef` 를 걸어야 하지만, **C++ 에서는 `Counter` 만으로 쓴다**(클래스 이름이 곧 타입 이름이다).\
  ★★ 그리고 **C++ 의 `std::unique_ptr<Counter>` 는 소멸자 자리에서 완전한 타입을 요구**해서, **C 에서 되던 「헤더에 포인터만」이 그대로 안 된다.** 이 편의 결론이 C++ 에서 **한 칸 좁아지는 자리**다(이 문서는 그 쪽을 **던지지 않았다**).

## 용어 풀이

> **불완전 타입(incomplete type)** — 이름은 정해졌는데 **크기를 모르는** 타입.\
> 예: `struct Counter;` 만 쓰면 포인터는 만들 수 있고 `sizeof` 는 못 쓴다.

> **완전한 타입(complete type)** — 크기를 아는 타입. **저장 공간을 잡을 수 있다.**\
> 예: `struct Counter { long n; long step; };` 가 보이는 곳에서는 `sizeof` 가 16 이다.

> **태그(tag)** — `struct`·`union`·`enum` 뒤에 붙는 이름.\
> 예: `struct Counter` 의 `Counter` 가 태그다. 변수 이름과 **다른 이름 공간**에 산다.

> **opaque struct(불투명 구조체)** — 헤더에 태그만 노출하고 멤버는 `.c` 에 숨기는 관용구.\
> 예: 헤더에 `typedef struct Counter Counter;` 만 두고 정의는 `s25b.c` 안에만 둔다.

> **번역 단위(translation unit)** — 전처리가 끝난 `.c` 하나. 컴파일러가 한 번에 보는 범위다.\
> 예: `s25b.c` 와 `s25b_main.c` 는 서로의 내용을 모른 채 따로 번역된다.

> **감쇠(decay)** — 배열이 식에서 **첫 원소를 가리키는 포인터**로 바뀌는 것.\
> 예: `extern char msg[];` 라도 `msg[1]` 은 된다 — 감쇠해서 크기를 안 쓰기 때문이다.

> **LTO(link-time optimization)** — 링크 시점에 번역 단위를 가로질러 최적화하는 것.\
> 예: `gcc -flto` 는 **함수 시그니처 불일치**를 잡아 주지만 **구조체 정의 불일치는 못 잡는다.**

> **`-pedantic` / `-pedantic-errors`** — 표준이 아닌 확장을 **경고로** / **에러로** 만드는 플래그.\
> 예: `sizeof(void)` 는 앞엣것으로는 `cc exit=0`, 뒤엣것으로는 `cc exit=1` 이다.

## 더 들어가면

- ★★ **`enum` 의 불완전 선언은 갈린다** — C23 이전에는 `enum E;` 만 쓰는 것이 표준이 아니다.\
  ★ 이 문서는 **`enum` 쪽을 던지지 않았다**([7번 형제](../07-enum-and-enumeration-constants/)가 정본).
- ★★ **`void *` 핸들 대 불완전 구조체 포인터** — 둘 다 내부를 숨기지만 **타입 안전성이 다르다.**\
  `void *` 는 아무 포인터나 받아 버리고, `struct Counter *` 는 **다른 핸들을 넘기면 컴파일 에러**다.\
  ★ 이 문서는 **`void *` 핸들 쪽을 던지지 않았다**([19번 형제](../19-void-pointer-null-pointer-and-null/)가 정본).
- ★ **함수가 불완전 타입을 「값으로」 반환하도록 선언하는 것** — 선언만은 되고 **정의·호출에서 에러**가 난다.\
  ★ 이 문서는 **그 자리를 던지지 않았다.**
- ★ **`-fsanitize=cfi`·`-Wodr`** 같은 더 센 도구가 (6)을 잡는지 — ★ **확인하지 않았다.** gcc 13 에서 C 에 대한 지원 범위를 안 봤다.
- ★ **오브젝트 파일에 디버그 정보(`-g`)를 넣으면** DWARF 에 구조체 레이아웃이 들어간다.\
  ★ 그것으로 (6)을 대조할 수 있는지는 **던지지 않았다** — 링커가 그 정보를 **검사에 쓰지는 않는다**는 것까지만 확인했다.
