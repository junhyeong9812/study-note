# c/syntax/26 — 유연 배열 멤버: 「**머리와 꼬리를 한 번에 잡는다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — Struct declaration (C)](https://en.cppreference.com/w/c/language/struct) · [GCC 13 — Arrays of Length Zero](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Zero-Length.html) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html) · [Clang Diagnostic flags](https://clang.llvm.org/docs/DiagnosticsReference.html)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값·바이트·진단·종료 코드는 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과\
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> **버전** — 유연 배열 멤버는 **C99 부터**다. 그 이전에는 **「길이 1 배열」 관용구**를 썼고(아래 (6)),\
> ★ 「**길이 0 배열**」(`char d[0];`)은 **표준이 아니라 gcc·clang 의 확장**이다 — `-pedantic` 이 잡는다.\
> ★ **C23 에서도 규칙은 그대로**다. gcc 14 가 새로 넣은 `-Wflex-array-member-not-at-end` 는 **gcc 13 에 없다**(확인: 옵션 자체가 `cc exit=1`).\
> ★★ **`-std=` 는 강제가 아니라 기본값 선택**이다 — 이 주제의 확장 세 가지는 **`-pedantic` 을 붙여야** 드러나고, 붙여도 **`cc exit=0`** 이다.
> ★★ **경계** — **구조체 선언·초기화·지정 초기자**는 [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/), **패딩·정렬**은 [22번 형제](../22-struct-padding-and-alignment/)가 정본이다.\
> 여기는 「**마지막 멤버의 길이를 비워 두면 무엇이 달라지나**」만 본다 — ★ **꼬리 패딩이 할당 산술에 새어 드는 자리**가 이 편의 값이다.\
> ★ **`sizeof`·`offsetof` 라는 도구**는 [8번 형제](../08-sizeof-alignment-and-offsetof/), **포인터 산술**은 [15번 형제](../15-pointer-arithmetic-and-indexing/)가 정본이다.\
> ★ **배열이 포인터로 감쇠하는 규칙**은 [16번 형제](../16-array-pointer-decay-and-function-parameters/), **크기를 모르는 배열**은 [25번 형제](../25-incomplete-types-and-opaque-struct/)다.\
> ★ **`malloc` 의 계약과 실패 처리**는 [목록의 **37번 주제**](../37-malloc-calloc-realloc-free/), **배열 밖 접근**은 목록의 **56번 주제**가 정본이다.
> 선행 — [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/) · [22번 형제](../22-struct-padding-and-alignment/) · [목록의 **37번 주제**](../37-malloc-calloc-realloc-free/).
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**유연 배열 멤버는 「봉투와 편지지를 한 장으로 사는 것」이다.**

편지를 부친다고 하자. 보통은 **봉투 하나**와 **편지지 뭉치 하나**를 따로 산다 — 사는 것도 두 번, 버리는 것도 두 번이다.\
유연 배열 멤버는 **봉투 뒤에 편지지가 붙어 나오는 문구**를 사는 것이다. **한 번 사고 한 번 버린다.**

- ★ 대신 **편지지가 몇 장인지 계산해서 사야 한다** — 가게가 대신 세어 주지 않는다.
- ★★ 그리고 **「봉투 값」을 물으면 편지지는 빼고 답한다**(`sizeof`).
- ★★★ 더 나쁜 것은 — **봉투를 복사하면 편지지가 안 따라온다.** 그런데 **아무도 안 알려 준다.**

| 비유 | 실체 | 층 |
|---|---|---|
| 봉투 | 구조체의 머리(`int len;`) | **표준** |
| 뒤에 붙은 편지지 | `char data[];` — 유연 배열 멤버 | **표준 (C99부터)** |
| 한 번에 사기 | `malloc(sizeof *m + n)` | **표준** |
| 「봉투 값」이 편지지를 뺀 값 | `sizeof(struct Msg)` 에 `data` 가 안 들어간다 | **표준** |
| ★ 봉투 규격 때문에 **남는 여백** | 꼬리 패딩 — `sizeof` 가 `offsetof` 보다 클 수 있다 | ★★ **구현 정의** |
| 편지지가 **맨 뒤가 아니면** | `struct { char d[]; int n; };` | **표준 — 컴파일 에러** |
| 봉투만 있고 **주소 칸이 없으면** | `struct { char d[]; };` | **표준 — 컴파일 에러** |
| 봉투를 **상자에 넣거나 여러 장 겹치기** | 다른 구조체의 멤버 · 배열 원소 | ★★ **확장 (경고뿐 · `cc exit=0`)** |
| ★★★ **봉투만 복사하기** | `*b = *a;` · `memcpy(b, a, sizeof *a)` | ★★★ **표준인데 아무도 안 말린다** |
| 편지지 칸을 넘겨 쓰기 | `m->data[n]` | **UB** |

```text
   struct Msg { int len; char data[]; };
   m = malloc(sizeof(struct Msg) + 5);          "hello" 를 담는다

   주소   +0       +4                          +9
          +--------+--+--+--+--+--+
          | len=5  |h |e |l |l |o |
          +--------+--+--+--+--+--+
          ^        ^
          |        +-- data  (offsetof(data) = 4)
          +----------- 구조체의 시작

   ★ sizeof(struct Msg) = 4      <- data 가 안 들어간다
   ★ malloc 에 주는 것은 sizeof + n = 9

   실제로 찍어 보면   05 00 00 00 68 65 6c 6c 6f
                      ^^^^^^^^^^^ len          ^^^^^^^^^^^^^^ data
```

- ★★★ **이 주제는 「표준」 칸이 본체**다 — `sizeof` 규칙·금지 사례·할당 관용구가 전부 표준이다.
- ★★ 두 번째 무게중심은 「**구현 정의**」인데 **한 자리뿐**이다 — **꼬리 패딩** 때문에 `sizeof` 와 `offsetof` 가 갈리는 것.
- ★★★ 그리고 **가장 조용한 사고는 어느 층도 아니다** — **구조체 대입이 꼬리를 안 옮기는 것**은 **완전히 적법한 표준 동작**이고, 그래서 **아무 도구도 말릴 이유가 없다**(아래 (4)).

> **유연 배열 멤버(flexible array member, FAM)** — 구조체의 **마지막** 멤버로 놓인 **길이를 안 적은 배열**.\
> 예: `struct Msg { int len; char data[]; };` 의 `data`. **C99 부터**다.

> **꼬리 패딩(trailing padding)** — 구조체 끝에 정렬을 맞추려고 붙는 여백.\
> 예: `struct Gap { int n; char c; char data[]; };` 는 `offsetof(data)` 가 5인데 `sizeof` 는 **8** 이다.

> **「길이 1 배열」 관용구(struct hack)** — C99 이전에 FAM 대신 쓰던 것. `char data[1];` 로 쓰고 `sizeof - 1 + n` 을 할당한다.\
> 예: 지금도 낡은 코드에 남아 있고, **출력도 진단도 FAM 과 똑같다**(아래 (6)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **몇 바이트를 할당해야 하나** — `sizeof` 인가 `offsetof` 인가, 그리고 **그 둘이 언제 갈리나.**
2. ★★★ **이 구조체를 복사하면 무슨 일이 나나** — 그리고 **그것을 누가 말려 주나.**
3. ★★ **C99 이전의 「길이 1 배열」과 무엇이 다른가** — **실행 결과로 갈리나 아니면 다른 것으로 갈리나.**

## 동작 방식

### (1) ★★★ `sizeof` 에 꼬리는 안 들어간다 — 그리고 **`offsetof` 와 갈린다**

**언제 쓰나** — 할당할 바이트 수를 정할 때. **이 편의 첫 번째 축이다.**

```c
/* s26a.c */
#include <stdio.h>
#include <stddef.h>

struct Msg  { int len; char data[]; };          /* 유연 배열 멤버 */
struct Gap  { int n; char c; char data[]; };    /* ★ 꼬리 패딩이 끼는 모양 */
struct Wide { char c; double d; char data[]; };
struct Old  { int len; char data[1]; };         /* C99 이전 관용구 */

int main(void) {
    printf("%-6s %-8s %-10s %s\n", "struct", "sizeof", "offsetof", "sizeof - offsetof");
    printf("%-6s %-8zu %-10zu %zu\n", "Msg",  sizeof(struct Msg),  offsetof(struct Msg,  data),
           sizeof(struct Msg)  - offsetof(struct Msg,  data));
    printf("%-6s %-8zu %-10zu %zu\n", "Gap",  sizeof(struct Gap),  offsetof(struct Gap,  data),
           sizeof(struct Gap)  - offsetof(struct Gap,  data));
    printf("%-6s %-8zu %-10zu %zu\n", "Wide", sizeof(struct Wide), offsetof(struct Wide, data),
           sizeof(struct Wide) - offsetof(struct Wide, data));
    printf("%-6s %-8zu %-10zu %zu\n", "Old",  sizeof(struct Old),  offsetof(struct Old,  data),
           sizeof(struct Old)  - offsetof(struct Old,  data));
    printf("\n★ sizeof 에 data 는 안 들어간다. Gap 은 sizeof 가 offsetof 보다 3 크다 (꼬리 패딩)\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26a.c -o x ; ./x (cc exit=0 · run exit=0) =====
struct sizeof   offsetof   sizeof - offsetof
Msg    4        4          0
Gap    8        5          3
Wide   16       16         0
Old    8        4          4

★ sizeof 에 data 는 안 들어간다. Gap 은 sizeof 가 offsetof 보다 3 크다 (꼬리 패딩)
```

```text
   struct Msg  { int len; char data[]; };
      0       4
      +-------+~~~~~~      sizeof = 4 · offsetof(data) = 4   -> 차이 0

   struct Gap  { int n; char c; char data[]; };
      0       4  5      8
      +-------+--+--##--+~~~~~~
                    ^^ ★ 꼬리 패딩 3바이트
      offsetof(data) = 5 · sizeof = ★ 8                      -> 차이 3
      ★ data 는 5번 바이트에서 시작하는데 sizeof 는 8 이다

   struct Old  { int len; char data[1]; };
      0       4  5      8
      +-------+--+--##--+
              ^^ data[0] 한 바이트가 ★ sizeof 에 들어 있다
      offsetof(data) = 4 · sizeof = ★ 8                      -> 차이 4
```

그림 해설 (한 단계씩):

- ★★★ **`sizeof` 에 `data` 가 안 들어간다.** `struct Msg` 는 `int` 하나짜리와 똑같이 **4** 다.
- ★★★ **`Gap` 에서 `sizeof` 가 `offsetof` 보다 3 크다.** `data` 는 **5번 바이트**에서 시작하는데 구조체 크기는 **8** 이다 — **꼬리 패딩**이 그 사이에 있다.
- ★★ **그래서 할당식이 두 가지가 된다.**

  | 할당식 | `Gap` 에서 n=5 일 때 | 안전한가 |
  |---|---|---|
  | `sizeof(struct Gap) + n` | 8 + 5 = **13** | ★★ **언제나 안전하다**(꼬리 패딩만큼 더 잡는다) |
  | `offsetof(struct Gap, data) + n` | 5 + 5 = **10** | ★ **꼭 맞다** — 낭비가 없다 |

  ★★ **`sizeof + n` 은 절대 모자라지 않는다** — `sizeof` 가 세는 꼬리 패딩 3바이트(5\~7번)를 **`data` 가 이미 쓰고 있어서**, `sizeof + n` 은 그 3바이트를 **두 번 센다.** 늘 넉넉한 쪽으로 틀린다.
- ★ **`Wide` 는 차이가 0** 이다(`sizeof` 도 `offsetof` 도 16). 정렬이 8인 `double` 뒤라 꼬리 패딩이 없다.
- ★ **`Old`**(길이 1 배열)는 차이가 **4** 다 — `data[0]` 한 바이트 + 꼬리 패딩 3 이 `sizeof` 에 들어 있다((6)에서 다시 본다).

비용 — **`sizeof + n` 은 꼬리 패딩만큼 낭비**하고, **`offsetof + n` 은 낭비가 없는 대신 식이 길다.**

### (2) ★★ 한 번의 할당으로 머리와 꼬리를 묶는다

**언제 쓰나** — 가변 길이 데이터를 헤더와 함께 다룰 때. **이 관용구의 본래 목적이다.**

```c
/* s26b.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>

struct Msg { int len; char data[]; };

static struct Msg *msg_new(const char *s) {
    size_t n = strlen(s);
    struct Msg *m = malloc(sizeof *m + n);      /* ★ 헤더 + 꼬리를 한 번에 */
    if (!m) return NULL;
    m->len = (int)n;
    memcpy(m->data, s, n);
    return m;
}

int main(void) {
    struct Msg *m = msg_new("hello");
    printf("len=%d  data=%.*s\n", m->len, m->len, m->data);
    printf("malloc 한 바이트 = sizeof(struct Msg)(%zu) + 5 = %zu\n",
           sizeof(struct Msg), sizeof(struct Msg) + 5);
    printf("꼭 필요한 바이트  = offsetof(data)(%zu) + 5 = %zu\n",
           offsetof(struct Msg, data), offsetof(struct Msg, data) + 5);

    const unsigned char *b = (const unsigned char *)m;
    printf("바이트 :");
    for (size_t k = 0; k < sizeof *m + 5; k++) printf(" %02x", b[k]);
    printf("\n         ^^^^^^^^^^^ len(4바이트)  ^^^^^^^^^^^^^^ data 5바이트\n");
    free(m);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26b.c -o x ; ./x (cc exit=0 · run exit=0) =====
len=5  data=hello
malloc 한 바이트 = sizeof(struct Msg)(4) + 5 = 9
꼭 필요한 바이트  = offsetof(data)(4) + 5 = 9
바이트 : 05 00 00 00 68 65 6c 6c 6f
         ^^^^^^^^^^^ len(4바이트)  ^^^^^^^^^^^^^^ data 5바이트
```

```text
   두 번 할당하는 방식                      유연 배열 멤버
   ------------------------------------    ----------------------------------
   struct Msg { int len; char *data; };    struct Msg { int len; char data[]; };

   m = malloc(sizeof *m);                  m = malloc(sizeof *m + n);
   m->data = malloc(n);                    memcpy(m->data, s, n);

   free(m->data);                          free(m);
   free(m);

   ★ 할당 2회 · 해제 2회 · 포인터 8바이트   ★ 할당 1회 · 해제 1회 · 포인터 0바이트
   ★ 머리와 꼬리가 ★ 멀리 떨어진다           ★ 붙어 있다
   ★ 해제 순서를 틀릴 수 있다                ★ 틀릴 순서가 없다
```

그림 해설 (한 단계씩):

- ★★ **바이트 덤프가 `05 00 00 00 68 65 6c 6c 6f`** 다. `len = 5` 가 리틀 엔디언으로 4바이트, 바로 뒤에 `hello` 다섯 바이트다 — **머리와 꼬리가 한 덩어리**임이 보인다.
- ★★ **`free` 가 한 번**이다. 두 번 할당하는 방식은 **해제 순서**(`m->data` 를 먼저)를 틀릴 수 있는데 여기서는 **틀릴 순서가 없다.**
- ★ **포인터 8바이트를 아낀다.** `char *data;` 를 쓰면 구조체가 그만큼 커진다.
- ★ **`sizeof *m` 을 썼지 `sizeof(struct Msg)` 를 안 썼다** — 타입 이름을 두 번 안 적는 관용구다([목록의 **37번 주제**](../37-malloc-calloc-realloc-free/)).

비용 — **크기를 바꾸려면 통째로 다시 할당**해야 한다. `char *data` 방식은 꼬리만 `realloc` 하면 된다.

### (3) ★★★ 금지 사례 — **에러 두 가지와 「경고뿐」 세 가지**

**언제 쓰나** — FAM 을 어디에 둘 수 있는지 판단할 때. ★★ **에러와 경고를 갈라 읽는 것**이 이 절의 값이다.

```c
/* s26c.c */
struct NoName  { char d[]; };           /* (1) 이름 있는 멤버가 하나도 없다 */
struct NotLast { char d[]; int n; };    /* (2) 마지막이 아니다 */

int main(void) { return 0; }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26c.c -o x (cc exit=1) =====
s26c.c:1:23: error: flexible array member in a struct with no named members
    1 | struct NoName  { char d[]; };           /* (1) 이름 있는 멤버가 하나도 없다 */
      |                       ^
s26c.c:2:23: error: flexible array member not at end of struct
    2 | struct NotLast { char d[]; int n; };    /* (2) 마지막이 아니다 */
      |                       ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s26c.c -o x (cc exit=1) =====
s26c.c:1:23: error: flexible array member 'd' not allowed in otherwise empty struct
    1 | struct NoName  { char d[]; };           /* (1) 이름 있는 멤버가 하나도 없다 */
      |                       ^
s26c.c:2:23: error: flexible array member 'd' with type 'char[]' is not at the end of struct
    2 | struct NotLast { char d[]; int n; };    /* (2) 마지막이 아니다 */
      |                       ^
s26c.c:2:32: note: next field declaration is here
    2 | struct NotLast { char d[]; int n; };    /* (2) 마지막이 아니다 */
      |                                ^
2 errors generated.
```

```c
/* s26c2.c */
struct Ok   { int n; char d[]; };
struct Nest { struct Ok c; };           /* (3) 다른 구조체가 값으로 품는다 */
struct Ok   arr[4];                     /* (4) 배열 원소로 쓴다 */
struct Zero { int n; char d[0]; };      /* (5) 길이 0 배열 */

int main(void) { (void)arr; return 0; }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26c2.c -o x (cc exit=0) =====
s26c2.c:2:25: warning: invalid use of structure with flexible array member [-Wpedantic]
    2 | struct Nest { struct Ok c; };           /* (3) 다른 구조체가 값으로 품는다 */
      |                         ^
s26c2.c:3:13: warning: invalid use of structure with flexible array member [-Wpedantic]
    3 | struct Ok   arr[4];                     /* (4) 배열 원소로 쓴다 */
      |             ^~~
s26c2.c:4:27: warning: ISO C forbids zero-size array ‘d’ [-Wpedantic]
    4 | struct Zero { int n; char d[0]; };      /* (5) 길이 0 배열 */
      |                           ^
```

```text
===== gcc -std=c17 -Wall -Wextra s26c2.c -o x (cc exit=0) =====
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s26c2.c -o x (cc exit=0) =====
s26c2.c:2:25: warning: 'c' may not be nested in a struct due to flexible array member [-Wflexible-array-extensions]
    2 | struct Nest { struct Ok c; };           /* (3) 다른 구조체가 값으로 품는다 */
      |                         ^
s26c2.c:3:16: warning: 'struct Ok' may not be used as an array element due to flexible array member [-Wflexible-array-extensions]
    3 | struct Ok   arr[4];                     /* (4) 배열 원소로 쓴다 */
      |                ^
s26c2.c:4:29: warning: zero size arrays are an extension [-Wzero-length-array]
    4 | struct Zero { int n; char d[0]; };      /* (5) 길이 0 배열 */
      |                             ^
3 warnings generated.
```

```text
   무엇                                   gcc              clang           cc exit
   ------------------------------------  ---------------  --------------  --------
   (1) 이름 있는 멤버가 없다               ★ error          ★ error         1
   (2) FAM 이 마지막이 아니다              ★ error          ★ error         1
   ------------------------------------  ---------------  --------------  --------
   (3) 다른 구조체가 값으로 품는다          warning(-ped)    warning         ★ 0
   (4) 배열 원소로 쓴다                    warning(-ped)    warning         ★ 0
   (5) 길이 0 배열 char d[0];              warning(-ped)    warning         ★ 0

   ★★★ 아래 셋은 -pedantic 을 빼면 ★ 진단이 0건이 된다 (gcc).
```

그림 해설 (한 단계씩):

- ★★★ **위의 둘은 진짜 에러**(`cc exit=1`)이고 **아래 셋은 확장**이다.\
  gcc 는 아래 셋을 `[-Wpedantic]` 으로만 잡고 **`cc exit=0`** 이며, **`-pedantic` 을 빼면 진단이 0건**이다(블록이 배너뿐이다).
- ★★★ **「종료 코드가 0인데 ill-formed」가 여기 셋**이다. 경고 건수만 세는 빌드는 **전부 통과로 기록한다.**
- ★★ **clang 은 플래그 이름을 따로 준다** — `[-Wflexible-array-extensions]`·`[-Wzero-length-array]`.\
  ★ **gcc 는 전부 `[-Wpedantic]` 으로 뭉뚱그린다** — 그래서 **gcc 쪽은 확장 하나만 끄고 싶어도 못 끈다.**
- ★★ **에러 문구가 규칙을 그대로 말해 준다.**\
  `flexible array member in a struct with no named members` — **이름 있는 멤버가 최소 하나 필요하다.**\
  `flexible array member not at end of struct` — **반드시 마지막이어야 한다.**\
  ★ clang 은 두 번째에 `note: next field declaration is here` 로 **범인 줄까지** 가리킨다.
- ★ 왜 「**이름 있는 멤버가 하나는 있어야 하나**」 — FAM 자체는 크기가 0 이라, 그것뿐이면 **크기 0 짜리 구조체**가 되어 C 의 객체 모형이 깨진다.

비용 — **`-pedantic` 을 안 붙이면 확장 셋이 조용히 들어온다.** 이식성이 필요하면 **반드시 붙인다.**

### (4) ★★★ 구조체 대입이 꼬리를 안 옮긴다 — **이 편의 본체**

**언제 쓰나** — FAM 구조체를 복사·대입·`memcpy` 하려 할 때.

```c
/* s26d.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Msg { int len; char data[]; };

static struct Msg *msg_new(const char *s) {
    size_t n = strlen(s);
    struct Msg *m = malloc(sizeof *m + n);
    m->len = (int)n;
    memcpy(m->data, s, n);
    return m;
}

int main(void) {
    struct Msg *a = msg_new("hello");
    struct Msg *b = malloc(sizeof *b + 5);      /* 넉넉히 잡아 둔다 */
    memset(b, 0, sizeof *b + 5);

    *b = *a;                                    /* ★ 구조체 대입 */

    printf("원본   : len=%d data=%.5s\n", a->len, a->data);
    printf("복사본 : len=%d data=%.5s\n", b->len, b->data);
    printf("data 5바이트 :");
    for (int k = 0; k < 5; k++) printf(" %02x", (unsigned char)b->data[k]);
    printf("   <- 원본은 68 65 6c 6c 6f 였다\n");
    printf("memcpy(sizeof *a) 도 같다 — 옮기는 것은 %zu 바이트뿐이다\n", sizeof *a);
    free(a); free(b);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26d.c -o x ; ./x (cc exit=0 · run exit=0) =====
원본   : len=5 data=hello
복사본 : len=5 data=
data 5바이트 : 00 00 00 00 00   <- 원본은 68 65 6c 6c 6f 였다
memcpy(sizeof *a) 도 같다 — 옮기는 것은 4 바이트뿐이다
```

```text
===== 구조체 대입이 꼬리를 옮기나 — 네 벌 + 도구 (exit=0) =====
gcc   -O0                          cc=0 경고 0건 run=0 | data 5바이트 : 00 00 00 00 00   <- 원본은 68 65 6c 6c 6f 였다
gcc   -O2                          cc=0 경고 0건 run=0 | data 5바이트 : 00 00 00 00 00   <- 원본은 68 65 6c 6c 6f 였다
clang -O0                          cc=0 경고 0건 run=0 | data 5바이트 : 00 00 00 00 00   <- 원본은 68 65 6c 6c 6f 였다
clang -O2                          cc=0 경고 0건 run=0 | data 5바이트 : 00 00 00 00 00   <- 원본은 68 65 6c 6c 6f 였다
gcc   -fsanitize=address,undefined cc=0 경고 0건 run=0 | data 5바이트 : 00 00 00 00 00   <- 원본은 68 65 6c 6c 6f 였다
gcc   -D_FORTIFY_SOURCE=2 -O2      cc=0 경고 0건 run=0 | data 5바이트 : 00 00 00 00 00   <- 원본은 68 65 6c 6c 6f 였다
```

```text
   *b = *a;   가 실제로 옮기는 것

   a:  +--------+--+--+--+--+--+
       | len=5  |h |e |l |l |o |
       +--------+--+--+--+--+--+
       <-------->
        ★ 이 4바이트만 옮긴다 (sizeof(struct Msg) = 4)

   b:  +--------+--+--+--+--+--+
       | len=5  |00|00|00|00|00|
       +--------+--+--+--+--+--+
       ★ len 은 5 라고 말하는데 ★ data 는 비어 있다

   ★ 컴파일러 경고 0건 · ASan 0건 · UBSan 0건 · FORTIFY 0건 · run exit=0
```

그림 해설 (한 단계씩):

- ★★★ **`len = 5` 는 따라오고 `data` 는 안 따라온다.** 복사본의 다섯 바이트가 `00 00 00 00 00` 이다.\
  **구조체 대입은 `sizeof` 만큼만 옮기는데 `sizeof` 에 `data` 가 없기 때문**이다.
- ★★★ **여섯 벌 전부 같고 전부 침묵이다** — gcc·clang × `-O0`/`-O2`, `-fsanitize=address,undefined`, `-D_FORTIFY_SOURCE=2 -O2` 가 **경고 0건 · `run exit=0`** 이다.
- ★★★ **이것은 UB 가 아니다.** `*b = *a` 는 **완전히 적법한 표준 동작**이고, 옮기는 바이트 수도 표준이 정한 그대로다.\
  ★ **그래서 도구가 말릴 이유가 없다** — 「틀린 코드」가 아니라 「**내 기대가 틀린 것**」이다.
- ★★ **`memcpy(b, a, sizeof *a)` 도 똑같다.** 같은 수를 쓰니 같은 결과다.
- ★★ **제5의 상태다** — 컴파일도 되고 실행도 되고 `len` 도 맞는다. 틀린 것은 값이 아니라 「**무엇이 복사됐는가**」다.
- ★ **옳은 복사법은 하나다** — **직접 계산한 바이트 수로 `memcpy`** 한다: `memcpy(b, a, sizeof *a + a->len)`.

비용 — **가장 자연스러워 보이는 한 줄이 조용히 반만 한다.** 이 관용구를 쓰는 값의 대부분을 여기서 잃는다.

### (5) ★★ 꼬리를 넘겨 쓰면 — ASan 은 잡고 컴파일러는 못 본다

**언제 쓰나** — 「경계를 넘었는지 어떻게 아나」를 물을 때.

```c
/* s26e.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Msg { int len; char data[]; };

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);       /* ★ ASan 이 abort 해도 stdout 이 안 사라지게 */
    size_t n = 5;
    struct Msg *m = malloc(sizeof *m + n);  /* data 는 5바이트뿐이다 */
    m->len = (int)n;
    memcpy(m->data, "hello", n);
    printf("여기까지는 정상이다 : %.5s\n", m->data);
    m->data[n] = '!';                       /* ★ 한 칸 넘는다 */
    printf("★ 한 칸 넘겨 썼다 — 이 줄이 보이나? 빌드에 달렸다\n");
    free(m);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26e.c -o x ; ./x (cc exit=0 · run exit=0) =====
여기까지는 정상이다 : hello
★ 한 칸 넘겨 썼다 — 이 줄이 보이나? 빌드에 달렸다
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -fsanitize=address s26e.c -o x ; ASAN_OPTIONS=strip_path_prefix=/src/ ./x 2>&1 | sed -n '1,/^SUMMARY/p' (cc exit=0 · run exit=1) =====
여기까지는 정상이다 : hello
=================================================================
==1011083==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x502000000019 at pc 0x621d859883f5 bp 0x7ffed6c90380 sp 0x7ffed6c90370
WRITE of size 1 at 0x502000000019 thread T0
    #0 0x621d859883f4 in main (x+0x13f4) (BuildId: cb3166a5fdc38669d84d4f672e4605647ad835c3)
    #1 0x75d55202a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #2 0x75d55202a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #3 0x621d85988204 in _start (x+0x1204) (BuildId: cb3166a5fdc38669d84d4f672e4605647ad835c3)

0x502000000019 is located 0 bytes after 9-byte region [0x502000000010,0x502000000019)
allocated by thread T0 here:
    #0 0x75d5524fd9c7 in malloc libsanitizer/asan/asan_malloc_linux.cpp:69
    #1 0x621d8598832e in main (x+0x132e) (BuildId: cb3166a5fdc38669d84d4f672e4605647ad835c3)
    #2 0x75d55202a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #3 0x75d55202a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #4 0x621d85988204 in _start (x+0x1204) (BuildId: cb3166a5fdc38669d84d4f672e4605647ad835c3)

SUMMARY: AddressSanitizer: heap-buffer-overflow (x+0x13f4) (BuildId: cb3166a5fdc38669d84d4f672e4605647ad835c3) in main
```

```text
   malloc(sizeof *m + 5) = 9바이트

   +--------+--+--+--+--+--+ X
   | len=5  |h |e |l |l |o | !|   <- data[5] 에 쓴다
   +--------+--+--+--+--+--+--+
    0                     8  ★9  = 할당 범위 밖

   그냥 빌드   -> ★ 아무 일도 안 난다. run exit=0. 다음 줄도 찍힌다.
   ASan 빌드   -> heap-buffer-overflow · WRITE of size 1
                  ★ 「0 bytes after 9-byte region」 이라고 ★ 크기까지 적어 준다
                  run exit=1
```

그림 해설 (한 단계씩):

- ★★★ **그냥 빌드하면 증상이 없다.** `run exit=0` 이고 다음 줄까지 찍힌다 — **한 바이트 넘은 것은 대개 아무 일도 안 일어난다.**
- ★★★ **ASan 은 정확히 잡는다** — `heap-buffer-overflow` · `WRITE of size 1` · **`0 bytes after 9-byte region`**.\
  ★ **할당 크기 9 를 그대로 적어 준다** — `sizeof *m + n` 이 무엇이었는지 리포트만 보고 역산할 수 있다.
- ★★ **컴파일러는 한 마디도 못 한다.** `n` 이 변수라 컴파일 시간에 알 수 없고, FAM 의 길이는 **애초에 타입에 없다.**
- ★★ **소스 첫 줄의 `setvbuf(stdout, NULL, _IONBF, 0)` 가 없으면** ASan 이 `abort()` 할 때 **버퍼에 남은 `printf` 줄이 통째로 사라진다.** 순서가 밀리는 게 아니라 **없어진다.**
- ★ **ASan 리포트의 PID·`pc`/`bp`/`sp`·모듈 오프셋은 실행마다 바뀐다.** 안 흔들리는 것은 **에러 종류·`WRITE of size 1`·`9-byte region`·`run exit=1`** 이다.

비용 — **이 경계는 실행 시간에만 드러나고, 그것도 sanitizer 를 켰을 때만** 드러난다.

### (6) ★★ C99 이전의 「길이 1 배열」 — **갈리는 것은 할당 산술뿐이다**

**언제 쓰나** — 낡은 코드에서 `char data[1];` 을 만났을 때.

```c
/* s26f.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>

struct New { int len; char data[]; };   /* C99 부터 — 유연 배열 멤버 */
struct Old { int len; char data[1]; };  /* C99 이전 관용구 — 「길이 1」 */

int main(void) {
    const char *s = "hello";
    size_t n = strlen(s);

    size_t need_new = sizeof(struct New) + n;
    size_t need_old = sizeof(struct Old) - 1 + n;
    size_t exact    = offsetof(struct New, data) + n;

    struct New *a = malloc(need_new);
    struct Old *b = malloc(need_old);
    a->len = (int)n; memcpy(a->data, s, n);
    b->len = (int)n; memcpy(b->data, s, n);

    printf("New sizeof=%zu  Old sizeof=%zu   (Old 는 data[1] 한 바이트를 포함한다)\n",
           sizeof(struct New), sizeof(struct Old));
    printf("New 할당식 sizeof+n       = %zu\n", need_new);
    printf("Old 할당식 sizeof-1+n     = %zu   <- ★ %zu 바이트 더 잡았다\n",
           need_old, need_old - need_new);
    printf("꼭 필요한 바이트 offsetof+n = %zu\n", exact);
    printf("\n둘 다 읽힌다 : new=%.5s old=%.5s\n", a->data, b->data);
    printf("★ 출력도 같고 진단도 없다 — 갈리는 것은 할당 산술과 ★ 표준이 보장하느냐 ★ 뿐이다\n");
    free(a); free(b);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26f.c -o x ; ./x (cc exit=0 · run exit=0) =====
New sizeof=4  Old sizeof=8   (Old 는 data[1] 한 바이트를 포함한다)
New 할당식 sizeof+n       = 9
Old 할당식 sizeof-1+n     = 12   <- ★ 3 바이트 더 잡았다
꼭 필요한 바이트 offsetof+n = 9

둘 다 읽힌다 : new=hello old=hello
★ 출력도 같고 진단도 없다 — 갈리는 것은 할당 산술과 ★ 표준이 보장하느냐 ★ 뿐이다
```

```text
   struct New { int len; char data[];  };   sizeof = 4
   struct Old { int len; char data[1]; };   sizeof = ★ 8   (data[0] 1 + 꼬리 패딩 3)

   n = 5 를 담으려면
     New :  sizeof + n        = 4 + 5 = ★ 9      <- 꼭 맞다
     Old :  sizeof - 1 + n    = 8 - 1 + 5 = ★ 12 <- ★ 3바이트 더 잡는다
     꼭 필요한 것 offsetof + n = 4 + 5 = 9

   ★ 「-1」 은 data[0] 한 바이트를 빼는 것인데, ★ 꼬리 패딩은 못 뺀다.
   ★ 그래서 더 잡는 쪽으로 틀린다 — 안전하지만 낭비다.
```

그림 해설 (한 단계씩):

- ★★★ **출력이 같다.** 둘 다 `hello` 를 담고 읽는다. **실행 결과로는 안 갈린다.**
- ★★★ **진단도 같다** — `-Wall -Wextra -pedantic` 에서 **둘 다 0건**이다.
- ★★ **갈리는 것은 두 가지뿐**이다.

  | | `char data[];`(FAM) | `char data[1];`(관용구) |
  |---|---|---|
  | 표준이 보장하나 | ★ **C99 부터 보장** | ★★ **아니다** — `data[1]` 을 넘겨 쓰는 것은 형식상 배열 밖 접근이다 |
  | 할당 산술 | `sizeof + n` = 9 | `sizeof - 1 + n` = **12** (여기서 3 낭비) |
  | `sizeof` | 4 | 8 |

- ★★ **`- 1` 이 꼬리 패딩을 못 뺀다.** `data[0]` 한 바이트는 빼지만 `sizeof` 안의 패딩 3바이트(5\~7번)는 그대로 남는다 — 그 세 바이트도 `data` 가 쓸 자리인데 **두 번 세어진다.** 그래서 **늘 더 잡는 쪽**으로 틀린다: 안전하지만 낭비다.
- ★ **새 코드에서는 FAM 을 쓴다.** 관용구를 쓸 이유는 **C89 만 쓰는 컴파일러**밖에 없다.

비용 — **낡은 코드를 읽을 때 `- 1` 의 뜻을 몰라 지우면** 한 바이트가 모자라게 된다.

### (7) ★★ 도구가 보는 자리와 안 보는 자리 — **크기를 아는 객체 대 할당된 객체**

**언제 쓰나** — 「`-D_FORTIFY_SOURCE` 를 켜면 FAM 도 지켜 주나」를 물을 때.

```c
/* s26g.c */
#include <stdio.h>
#include <string.h>

struct New { int len; char data[]; };
struct Old { int len; char data[1]; };

static struct New g_new;        /* 크기를 아는 객체 — data 는 0바이트다 */
static struct Old g_old;        /* 크기를 아는 객체 — data 는 1바이트다 */

int main(void) {
    strcpy(g_new.data, "hello");   /* 둘 다 넘친다 */
    strcpy(g_old.data, "hello");
    printf("%s %s\n", g_new.data, g_old.data);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -D_FORTIFY_SOURCE=2 s26g.c -o x (cc exit=0) =====
In file included from /usr/include/string.h:548,
                 from s26g.c:2:
In function ‘strcpy’,
    inlined from ‘main’ at s26g.c:11:5:
/usr/include/x86_64-linux-gnu/bits/string_fortified.h:79:10: warning: ‘__builtin___memcpy_chk’ offset [4, 9] is out of the bounds [0, 4] of object ‘g_new’ with type ‘struct New’ [-Warray-bounds=]
   79 |   return __builtin___strcpy_chk (__dest, __src, __glibc_objsize (__dest));
      |          ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
s26g.c: In function ‘main’:
s26g.c:7:19: note: ‘g_new’ declared here
    7 | static struct New g_new;        /* 크기를 아는 객체 — data 는 0바이트다 */
      |                   ^~~~~
In function ‘strcpy’,
    inlined from ‘main’ at s26g.c:12:5:
/usr/include/x86_64-linux-gnu/bits/string_fortified.h:79:10: warning: ‘__builtin___memcpy_chk’ forming offset [8, 9] is out of the bounds [0, 8] of object ‘g_old’ with type ‘struct Old’ [-Warray-bounds=]
   79 |   return __builtin___strcpy_chk (__dest, __src, __glibc_objsize (__dest));
      |          ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
s26g.c: In function ‘main’:
s26g.c:8:19: note: ‘g_old’ declared here
    8 | static struct Old g_old;        /* 크기를 아는 객체 — data 는 1바이트다 */
      |                   ^~~~~
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -D_FORTIFY_SOURCE=2 s26f.c -o x (cc exit=0) =====
```

```text
   같은 플래그 (-O2 -D_FORTIFY_SOURCE=2) 로 두 프로그램을 던졌다

   s26g.c — 크기를 ★ 아는 정적 객체
     static struct New g_new;   (data 0바이트)  -> ★ warning: offset [4, 9] out of bounds [0, 4]
     static struct Old g_old;   (data 1바이트)  -> ★ warning: offset [8, 9] out of bounds [0, 8]
     ★ 둘 다 잡는다. ★ 그런데 cc exit=0 이다.

   s26f.c — malloc 으로 ★ 할당한 객체
     -> ★ 경고 0건 (블록이 배너뿐이다)

   ★ 갈리는 축은 「FAM 이냐 길이 1 배열이냐」가 아니라
     ★ 「그 객체의 크기를 컴파일러가 아느냐」였다.
```

그림 해설 (한 단계씩):

- ★★★ **크기를 아는 정적 객체에서는 둘 다 잡힌다.** `__builtin_object_size` 가 `g_new` 는 4바이트, `g_old` 는 8바이트로 보고 `strcpy` 가 넘는 것을 `[-Warray-bounds=]` 로 알린다.
- ★★★ **`malloc` 으로 잡은 객체에서는 둘 다 못 잡는다.** 그런데 **FAM 을 쓰는 실제 코드는 전부 `malloc` 쪽**이다 — 즉 **실전에서는 이 도구가 도움이 안 된다.**
- ★★ **여기서도 `cc exit=0`** 이다. 넘치는 것이 확실한데도 **빌드는 통과**한다.
- ★ **전제가 뒤집힌 자리다** — 「길이 1 배열은 도구가 잡고 FAM 은 못 잡는다」를 기대하고 던졌는데, 갈린 축은 그게 아니라 「**객체의 크기를 아느냐**」였다.

비용 — **정적 진단에 기대면 안 된다.** 경계 검사는 **ASan 이나 내 코드의 길이 검사**가 한다.

### (8) ★ 초기자 — **정적이면 확장, 자동이면 에러**

**언제 쓰나** — FAM 구조체를 초기자로 만들려 할 때.

```c
/* s26h.c */
#include <stdio.h>

struct Msg { int len; char data[]; };

static struct Msg g = { 3, { 'a', 'b', 'c' } };   /* (1) 정적 저장 기간 */

int main(void) {
    struct Msg m = { 3, { 'a', 'b', 'c' } };      /* (2) 자동 저장 기간 */
    struct Msg z = { 3 };                          /* (3) 꼬리를 안 적는다 */
    printf("%d %c\n", g.len, g.data[0]);
    printf("%d %d\n", m.len, z.len);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26h.c -o x (cc exit=1) =====
s26h.c:5:28: warning: initialization of a flexible array member [-Wpedantic]
    5 | static struct Msg g = { 3, { 'a', 'b', 'c' } };   /* (1) 정적 저장 기간 */
      |                            ^
s26h.c:5:28: note: (near initialization for ‘g.data’)
s26h.c: In function ‘main’:
s26h.c:8:25: warning: initialization of a flexible array member [-Wpedantic]
    8 |     struct Msg m = { 3, { 'a', 'b', 'c' } };      /* (2) 자동 저장 기간 */
      |                         ^
s26h.c:8:25: note: (near initialization for ‘m.data’)
s26h.c:8:25: error: non-static initialization of a flexible array member
s26h.c:8:25: note: (near initialization for ‘m’)
```

```text
   static struct Msg g = { 3, {'a','b','c'} };   -> warning [-Wpedantic] ★ 확장으로 통과
   struct Msg m        = { 3, {'a','b','c'} };   -> ★ error — 자동 저장 기간은 안 된다
   struct Msg z        = { 3 };                  -> ★ 아무 말 없다 (꼬리를 안 적었다)

   ★ 그런데 z 의 data 에는 ★ 쓸 공간이 0바이트다 — 「되는 것」과 「쓸모 있는 것」이 다르다.
```

그림 해설 (한 단계씩):

- ★★ **정적 저장 기간이면 gcc 가 받아 준다** — `[-Wpedantic]` 경고 한 줄 + `note: (near initialization for 'g.data')`. **표준이 아니라 확장**이다.
- ★★ **자동 저장 기간이면 에러**다 — `non-static initialization of a flexible array member`. 스택 프레임 크기는 **컴파일 시간에 정해져야** 하기 때문이다.
- ★ **꼬리를 안 적으면 아무 말이 없다**(`{ 3 }`). 다만 그 객체의 `data` 에는 **쓸 공간이 0바이트**다 — **선언은 되는데 쓸모가 없다.**
- ★ **`cc exit=1`** 이다(자동 쪽 에러 때문). ★ 정적 쪽만 남기면 **`cc exit=0`** 이 된다 — (3)·(7)과 같은 모양이다.

비용 — **초기자로는 실질적으로 못 만든다.** FAM 구조체는 **거의 언제나 `malloc` 으로 만든다**([28번 형제](../28-choosing-among-four-storage-durations/)와 맞물린다).

### (9) ★★ 배열처럼 늘어놓을 수 없다 — 포인터 산술이 `sizeof` 를 쓴다

**언제 쓰나** — FAM 구조체를 여러 개 한 덩어리에 담으려 할 때.

```c
/* s26i.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Msg { int len; char data[]; };

int main(void) {
    const size_t payload = 8;
    const size_t stride  = sizeof(struct Msg) + payload;   /* 한 칸의 진짜 크기 */
    char *buf = malloc(stride * 3);
    memset(buf, 0, stride * 3);

    for (int i = 0; i < 3; i++) {                           /* ★ 손으로 stride 를 곱한다 */
        struct Msg *m = (struct Msg *)(buf + (size_t)i * stride);
        m->len = i;
        memcpy(m->data, "abcdefgh", payload);
        m->data[0] = (char)('A' + i);
    }

    struct Msg *m0 = (struct Msg *)buf;
    printf("sizeof(struct Msg) = %zu · 내가 쓴 stride = %zu\n", sizeof(struct Msg), stride);
    printf("m0 + 1 은 %td 바이트 뒤다   <- ★ stride 가 아니다\n",
           (char *)(m0 + 1) - (char *)m0);
    printf("m0[1].len = %d   <- 두 번째 칸의 len 이 아니다\n", m0[1].len);
    printf("\n손으로 stride 를 곱해 읽으면\n");
    for (int i = 0; i < 3; i++) {
        struct Msg *m = (struct Msg *)(buf + (size_t)i * stride);
        printf("  칸 %d : len=%d data=%.8s\n", i, m->len, m->data);
    }
    free(buf);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26i.c -o x ; ./x (cc exit=0 · run exit=0) =====
sizeof(struct Msg) = 4 · 내가 쓴 stride = 12
m0 + 1 은 4 바이트 뒤다   <- ★ stride 가 아니다
m0[1].len = 1684234817   <- 두 번째 칸의 len 이 아니다

손으로 stride 를 곱해 읽으면
  칸 0 : len=0 data=Abcdefgh
  칸 1 : len=1 data=Bbcdefgh
  칸 2 : len=2 data=Cbcdefgh
```

```text
   내가 만든 배치 (stride = sizeof + 8 = 12)

   buf +0        +12       +24
       +---------+---------+---------+
       | 칸 0    | 칸 1    | 칸 2    |
       +---------+---------+---------+

   그런데 m0 + 1 은 ★ sizeof(struct Msg) = 4 바이트만 간다

   buf +0   +4
       +----+
       |    |  <- m0 + 1 은 여기다. ★ 칸 1 이 아니라 칸 0 의 data 한복판이다.
       +----+

   m0[1].len = 1684234817 = 0x64636261 = "abcd" 를 int 로 읽은 것
```

그림 해설 (한 단계씩):

- ★★★ **`m0 + 1` 은 4바이트만 간다.** 포인터 산술은 **`sizeof` 를 쓰는데 `sizeof` 에 꼬리가 없기** 때문이다([15번 형제](../15-pointer-arithmetic-and-indexing/)가 정본).
- ★★★ **`m0[1].len` 이 `1684234817`** 이다. 16진으로 `0x64636261` = `"abcd"` — **칸 0 의 `data` 한복판을 `int` 로 읽은 값**이다.\
  ★ **이 수가 그럴듯해 보이지 않는 것이 그나마 다행**이다. 만약 `data` 가 0 으로 차 있었다면 `0` 이 나와 **못 알아챘을 것**이다.
- ★★ **답은 손으로 stride 를 곱하는 것**이다 — `(char *)buf + i * stride`. 그러면 세 칸이 제대로 읽힌다(`A…`/`B…`/`C…`).
- ★ 그래서 FAM 구조체는 「**배열로 못 만든다**」((3)의 경고와 같은 이야기다). 여러 개가 필요하면 **포인터 배열**(`struct Msg *arr[3]`)을 쓴다.

비용 — **인덱싱이라는 가장 익숙한 도구를 못 쓴다.** 쓰면 조용히 엉뚱한 자리를 읽는다.

### (10) ★ C++ 에서는 표준이 아니다

**언제 쓰나** — 헤더를 C 와 C++ 양쪽에서 쓸 때.

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -x c++ s26c2.c -o x (cc exit=0) =====
s26c2.c:1:27: warning: ISO C++ forbids flexible array member ‘d’ [-Wpedantic]
    1 | struct Ok   { int n; char d[]; };
      |                           ^
s26c2.c:2:25: warning: invalid use of ‘struct Ok’ with a flexible array member in ‘struct Nest’ [-Wpedantic]
    2 | struct Nest { struct Ok c; };           /* (3) 다른 구조체가 값으로 품는다 */
      |                         ^
s26c2.c:1:27: note: array member ‘char Ok::d []’ declared here
    1 | struct Ok   { int n; char d[]; };
      |                           ^
s26c2.c:4:29: warning: ISO C++ forbids zero-size array ‘d’ [-Wpedantic]
    4 | struct Zero { int n; char d[0]; };      /* (5) 길이 0 배열 */
      |                             ^
```

```text
   같은 파일을 g++ 로 던지면

   struct Ok { int n; char d[]; };   -> ★ warning: ISO C++ forbids flexible array member
   struct Nest { struct Ok c; };     -> warning: invalid use ... with a flexible array member
   struct Zero { int n; char d[0]; };-> warning: ISO C++ forbids zero-size array

   ★ 셋 다 경고이고 ★ cc exit=0 이다 — g++ 가 확장으로 받아 준다.
```

- ★★ **유연 배열 멤버는 C++ 표준에 없다.** g++ 는 **확장으로 받아 주고 `-pedantic` 으로만 알린다**(`cc exit=0`).
- ★★ **C 에서는 「표준 기능」이던 것이 C++ 에서는 「확장」이 된다** — (3)의 표에서 **에러 두 줄은 그대로이고 나머지 한 줄이 위로 올라온다.**
- ★ 그래서 **C 와 C++ 가 같이 쓰는 헤더에 FAM 을 두면** 한쪽에서는 표준이고 한쪽에서는 확장이 된다. ★ 자세한 것은 C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md)) 쪽이다.

## 문법 — 형태와 규칙

### 형태

```text
/* 선언 — 마지막 멤버 · 길이 없음 · 앞에 이름 있는 멤버가 최소 하나 */
struct Msg {
    int  len;          /* ★ 이름 있는 멤버가 최소 하나 있어야 한다 */
    char data[];       /* ★ 반드시 마지막 · 길이를 안 적는다 (C99부터) */
};

/* 만들기 — 머리와 꼬리를 한 번에 */
struct Msg *m = malloc(sizeof *m + n);          /* 넉넉하다 (꼬리 패딩만큼 여유) */
struct Msg *m = malloc(offsetof(struct Msg, data) + n);  /* 꼭 맞다 */

/* 복사 — ★ 대입은 머리만 옮긴다. 직접 계산해서 옮긴다 */
memcpy(dst, src, sizeof *src + src->len);

/* 없애기 — 한 번 */
free(m);
```

### 금지 사례 — 어느 것이 무슨 층인가

```text
struct A { char d[]; };            /* ★ 컴파일 에러 — 이름 있는 멤버가 없다 */
struct B { char d[]; int n; };     /* ★ 컴파일 에러 — 마지막이 아니다 */

struct Ok { int n; char d[]; };
struct C { struct Ok o; };         /* ★★ 확장 — 경고뿐 · cc exit=0 */
struct Ok arr[4];                  /* ★★ 확장 — 경고뿐 · cc exit=0 */
struct D { int n; char d[0]; };    /* ★★ 확장 — 길이 0 배열. 경고뿐 · cc exit=0 */

struct Ok a = { 1, {'x'} };        /* ★ 컴파일 에러 — 자동 저장 기간은 초기화 못 한다 */
static struct Ok g = { 1, {'x'} }; /* ★★ 확장 — 경고뿐 (정적이면 gcc 가 받는다) */

*b = *a;                           /* ★★★ 표준 동작인데 ★ 꼬리가 안 따라온다. 진단 0건 */
memcpy(b, a, sizeof *a);           /* ★★★ 같다 */

m0[1].len                          /* ★★ sizeof 로 건너뛴다 — 엉뚱한 자리다. 진단 0건 */
m->data[n]                         /* ★ UB — 할당 범위 밖. ASan 만 본다 */

sizeof(struct Msg)                 /* ★ data 는 안 들어간다 — 에러가 아니라 ★ 뜻이 다르다 */
```

### 규칙 불릿

- ★★★ **`sizeof` 에 유연 배열 멤버는 안 들어간다.** 이 한 줄에서 나머지가 전부 따라 나온다.
- ★★★ **반드시 마지막 멤버**여야 하고, **앞에 이름 있는 멤버가 최소 하나** 있어야 한다. 둘 다 어기면 **컴파일 에러**다.
- ★★★ **구조체 대입·`memcpy(…, sizeof *a)` 는 머리만 옮긴다.** **표준 동작**이라 **아무 도구도 말리지 않는다.**
- ★★ **할당은 `sizeof + n` 또는 `offsetof(…, data) + n`.** 앞엣것은 **꼬리 패딩만큼 더 잡고** 뒤엣것은 **꼭 맞는다.** 앞엣것이 모자라는 일은 없다.
- ★★ **꼬리 패딩이 있으면 `sizeof` 가 `offsetof` 보다 크다** — `struct Gap` 에서 **8 대 5** 였다. **구현 정의**다.
- ★★ 다른 구조체의 멤버로 넣는 것·배열 원소로 쓰는 것·길이 0 배열은 「**확장**」이다. `-pedantic` 이 경고하고 **`cc exit=0`** 이며, `-pedantic` 이 없으면 **진단 0건**이다.
- ★★ **포인터 산술이 `sizeof` 를 쓰므로 `m + 1` 은 꼬리를 건너뛰지 않는다.** 여러 개가 필요하면 **손으로 stride 를 곱하거나 포인터 배열**을 쓴다.
- ★★ **초기자로는 자동 저장 기간에서 에러**, 정적 저장 기간에서만 **확장으로** 통과한다.
- ★ **C99 이전 관용구(`char d[1]`)는 실행 결과도 진단도 같다.** 갈리는 것은 **할당 산술(`- 1`)과 표준의 보장 여부**뿐이다.
- ★ **`-D_FORTIFY_SOURCE=2 -O2` 는 크기를 아는 정적 객체만 본다.** `malloc` 으로 잡은 것은 **둘 다 못 본다.**
- ★ **꼬리를 넘겨 쓰면 UB** 이고, **ASan 만** 잡는다(`0 bytes after 9-byte region`).
- ★ **C++ 표준에는 없다.** g++ 는 확장으로 받고 `-pedantic` 으로만 알린다.

## 어디서 틀리나

### 1. ★★★ 「구조체 대입하면 다 복사되겠지」

**머리만 간다**((4)). `len = 5` 는 따라오는데 `data` 는 `00 00 00 00 00` 이었고,\
**여섯 벌**(컴파일러 2 × `-O` 2 + ASan+UBSan + FORTIFY)이 **전부 침묵**했다.\
★★ **UB 가 아니라 적법한 동작**이라 도구가 말릴 이유가 없다 — **틀린 것은 코드가 아니라 내 기대**다.\
★ 옳은 복사는 `memcpy(dst, src, sizeof *src + src->len)` 다.

### 2. ★★★ 「`sizeof` 로 배열처럼 건너뛰면 되겠지」

**안 된다**((9)). `m0 + 1` 은 **4바이트**만 갔고 `m0[1].len` 은 `1684234817`(= `"abcd"`)였다.\
★ **손으로 stride 를 곱하거나 포인터 배열**을 쓴다.

### 3. ★★ 「`offsetof + n` 이 정석이고 `sizeof + n` 은 틀린 것 아닌가」

**둘 다 맞다**((1)). 꼬리 패딩은 `data` **앞**에 있으므로 `sizeof + n` 은 **늘 넉넉하다.**\
★ 다만 `struct Gap` 에서 **3바이트를 버린다.** 백만 개를 만들면 그것이 3MB 다.

### 4. ★★ 「`-Wall -Wextra` 면 확장도 잡히겠지」

**안 잡힌다**((3)). 중첩·배열 원소·길이 0 배열은 **`-pedantic` 이 있어야** 경고가 나오고,\
★★ **경고가 나와도 `cc exit=0`** 이다. 이식성을 강제하려면 **`-pedantic-errors`** 다.

### 5. ★★ 「`-D_FORTIFY_SOURCE` 를 켜면 꼬리 경계도 지켜 주겠지」

**`malloc` 으로 잡은 것은 못 본다**((7)). 잡히는 것은 **크기를 아는 정적 객체**뿐인데,\
★ **FAM 을 쓰는 실제 코드는 전부 `malloc` 쪽**이다. 경계는 **ASan 이나 내 길이 검사**가 지킨다.

### 6. ★★ 「낡은 코드의 `char d[1]` 은 버그니까 `- 1` 을 지우자」

**지우면 안 된다**((6)). `- 1` 은 `data[0]` 한 바이트를 빼는 것이고,\
지우면 한 바이트를 **더** 잡게 된다(그건 안전하다). 진짜 문제는 **`- 1` 이 꼬리 패딩을 못 빼서 낭비**한다는 것이다.\
★ 새로 쓰면 **FAM 으로 바꾸는 쪽**이 맞다.

### 7. ★ 「구조체 안에 FAM 구조체를 넣었는데 잘 되던데」

**gcc·clang 의 확장으로 통과한 것**이다((3)). `-pedantic` 을 붙여 보면 경고가 난다.\
★ **그 구조체의 `sizeof` 안에 꼬리가 없으므로** 뒤에 오는 멤버와 겹친다 — 실제로 쓰면 무너진다.

### 8. ★ 「한 바이트 넘겼는데 안 터지던데」

**대개 안 터진다**((5)). `run exit=0` 이고 다음 줄도 찍혔다.\
★★ **「안 터졌다」는 「안전하다」가 아니다** — ASan 을 켜면 `heap-buffer-overflow` 가 나온다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 본체**다 — `sizeof` 규칙·두 가지 금지·할당 관용구가 전부 거기 있다.\
★★ 두 번째는 「**구현 정의**」인데 **한 자리뿐**이다 — **꼬리 패딩**.\
★★★ 그리고 이 편의 가장 위험한 사고((4))는 **어느 층도 아니다** — **표준 동작인데 기대가 틀린 것**이라, 다섯 층 표로는 **잡히지 않는 성격**이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준 (본체)** | 어느 구현에서도 같다 | **`sizeof` 에 FAM 이 안 들어가는 것** · **마지막 멤버여야 하는 것** · **이름 있는 멤버가 최소 하나 필요한 것** · **자동 저장 기간에서 초기화 못 하는 것** · **구조체 대입이 `sizeof` 만큼만 옮기는 것** · 포인터 산술이 `sizeof` 를 쓰는 것 · C99 부터인 것 | `sizeof(struct Msg)` = **4** · 에러 2건 두 컴파일러(`cc exit=1`) · `non-static initialization` 에러 · `*b = *a` 뒤 `data` 가 **`00 00 00 00 00`**(여섯 벌 동일) · `m0 + 1` 이 **4바이트** |
| **조건부 표준** | 매크로가 정의될 때만 | ★ **해당 없음** — FAM 에는 매크로로 켜고 꺼지는 보장이 없다 | — |
| ★★ **구현 정의** | 문서화 의무가 있다 | ★★ **꼬리 패딩** — `sizeof` 가 `offsetof` 보다 큰가 · 얼마나 큰가 · 진단 문구와 플래그 이름 · **어떤 확장을 받아 주는가**(중첩·배열 원소·길이 0 배열·정적 초기자) | `Msg` 4/4 · **`Gap` 8/5** · `Wide` 16/16 · `Old` 8/4 · gcc 는 `[-Wpedantic]` 하나로 뭉치고 clang 은 `[-Wflexible-array-extensions]`·`[-Wzero-length-array]` 로 가른다 |
| **미명시** | 몇 가지 중 하나 · 문서화 의무도 없다 | ★ **꼬리 패딩 바이트의 값**([22번 형제](../22-struct-padding-and-alignment/)가 정본) · ★ 넘겨 쓴 뒤 **무엇이 깨지는가** | ★ 이 편은 **패딩 값 자체는 던지지 않았다** — 22번 형제의 몫이다 |
| ★ **UB** | 아무 일이나 | ★ **할당 범위를 넘겨 읽고 쓰는 것**(`m->data[n]`) · ★ **`m0[1]` 처럼 `sizeof` 로 건너뛴 자리를 읽는 것** | ASan `heap-buffer-overflow` · `WRITE of size 1` · `0 bytes after 9-byte region` · `run exit=1` / `m0[1].len` = `1684234817` |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★★ **`*b = *a` 를 아무도 안 말린다** — **적법한 동작**이라 말릴 근거가 없다. 여섯 벌 전부 **경고 0건 · `run exit=0`** 이었다. ★ 이 자리가 이 주제에서 **가장 조용하다** |
| **조건부 표준** | ★ **해당 없음** — 볼 것이 없으니 도구도 할 말이 없다 |
| ★★ **구현 정의** | ★★ **`sizeof` 와 `offsetof` 가 갈린다고 말해 주는 경고가 없다.** `Gap` 에서 3바이트가 어긋나는데 **둘을 직접 찍어야** 보인다. ★ **어떤 확장을 받았는지도 `-pedantic` 을 붙여야** 알고, 붙여도 **`cc exit=0`** 이다 |
| **미명시** | ★ **패딩 바이트의 값은 어떤 도구도 안 본다**(22번 형제의 결론과 같다) |
| ★ **UB** | ★★ **정적 진단은 `malloc` 객체를 못 본다** — `-D_FORTIFY_SOURCE=2 -O2` 가 **정적 객체는 잡고 할당된 객체는 놓쳤다.** ★ 그리고 **`m0[1]` 은 ASan 도 못 잡는다**(할당 범위 안이다) |
| ★★ **(층을 가로지름)** | ★★★ **「종료 코드가 0인데 ill-formed」가 다섯 군데**다 — ① 중첩 ② 배열 원소 ③ 길이 0 배열 ④ 정적 FAM 초기자 ⑤ g++ 의 FAM 전부. **다섯 자리 모두 `-pedantic` 이라야 보이고, 보여도 `cc exit=0`** 이다 |

- ★★ **이 표의 결론 네 줄**
  - ★★★ **가장 조용한 자리는 UB 가 아니라 표준 동작이다** — `*b = *a` 는 틀린 코드가 아니고, 그래서 **원리상 어떤 도구도 못 잡는다.** 여기서 **다섯 층 표의 한계**가 보인다.
  - ★★ **두 번째는 꼬리 패딩**이다 — `sizeof` 와 `offsetof` 를 **나란히 찍기 전에는** 3바이트가 어긋나는 것을 알 길이 없다.
  - ★★ **확장 다섯 자리가 전부 `cc exit=0`** 이다. 「이식되는가」를 **빌드로 강제**하려면 `-pedantic-errors` 밖에 없다.
  - ★ **경계 검사는 ASan 이 유일하게 쓸 만하다.** 다만 `m0[1]` 처럼 **할당 범위 안에서 엉뚱한 자리를 읽는 것**은 ASan 도 못 본다.

### 이 주제의 네 번째 창 — **복사본의 꼬리를 바이트로 대조하는 것**

- **컴파일 진단**은 (3)·(8)을 잡는다 — 금지 두 가지는 에러, 확장 다섯 가지는 경고다.
- **실행 출력**은 (4)에서 **`len = 5` 라고 맞게 답한다** — 창이 아니라 **함정**이다.
- **ASan·UBSan** 은 (5)를 잡지만 (4)·(9)에는 할 말이 없다 — **할당 범위 안**이기 때문이다.
- ★★ 그래서 네 번째 창은 「**복사본의 `data` 를 원본과 바이트로 대조하는 것**」이다.\
  `len` 만 보면 통과하고, **`data` 다섯 바이트를 찍어야** `00 00 00 00 00` 이 보인다.
- ★★ **그 창을 여는 조건은 하나** — **`sizeof` 와 `offsetof` 와 실제 할당 바이트 수를 한 화면에 같이 찍는다.** (1)·(2)의 블록이 그 형식이다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 헤더 + 가변 길이 데이터를 한 덩어리로 | **유연 배열 멤버** + `malloc(sizeof *m + n)` | `char *data;` 두 번 할당(틀린 건 아니고 비용이 다르다) |
| 낭비 없이 딱 맞게 잡기 | `offsetof(struct M, data) + n` | 손으로 센 상수 |
| 넉넉하고 짧게 잡기 | `sizeof *m + n` | ★ `sizeof *m` 만 (꼬리가 0바이트다) |
| 복사하기 | ★★★ **`memcpy(dst, src, sizeof *src + src->len)`** | ★★★ `*dst = *src` · `memcpy(…, sizeof *src)` |
| 여러 개를 담기 | **포인터 배열** `struct Msg *arr[3]` 또는 **손으로 곱한 stride** | ★★ `struct Msg arr[3]` · `m[i]` |
| 다른 구조체에 품기 | **포인터로 품는다** | ★★ 값으로 품기(확장이고 무너진다) |
| 초기화하기 | **`malloc` 뒤에 대입** | ★ 초기자(자동은 에러, 정적은 확장) |
| 경계를 지키기 | ★★ **`len` 을 검사하는 내 코드 + ASan** | ★ `-D_FORTIFY_SOURCE`(할당 객체는 못 본다) |
| 이식성을 강제하기 | ★★ **`-pedantic-errors`** | `-pedantic` 만 붙이고 경고 세기 |
| C99 이전 컴파일러 | `char data[1];` + `sizeof - 1 + n` | ★ `char data[0];`(그것도 확장이다) |
| C 와 C++ 공용 헤더 | ★ **FAM 을 피하거나 `#ifdef` 로 가른다** | 그냥 두기(C++ 에서는 확장이다) |

판단 규칙 두 줄.

- ★★★ **`sizeof` 에 꼬리가 없다 — 그러니 `sizeof` 를 쓰는 모든 연산(대입·`memcpy`·포인터 산술·인덱싱)이 꼬리를 빠뜨린다.**
- ★★ **이 관용구의 값은 「할당 1회·해제 1회」이고, 대가는 「복사와 배열을 잃는 것」이다.**

## 핵심 문장

- ★★★ **`sizeof` 에 유연 배열 멤버는 안 들어간다** — 그래서 `struct Msg` 가 `int` 하나와 같은 **4** 다.
- ★★★ **구조체 대입은 머리만 옮긴다** — `len = 5` 인데 `data` 가 `00 00 00 00 00` 이었고 **여섯 벌 전부 침묵**했다.
- ★★★ **그 사고는 UB 가 아니라 표준 동작**이다. **틀린 것은 코드가 아니라 기대**라서 **원리상 도구가 못 잡는다.**
- ★★★ **포인터 산술도 `sizeof` 를 쓴다** — `m0 + 1` 은 **4바이트**만 갔고 `m0[1].len` 은 `"abcd"` 였다.
- ★★ **꼬리 패딩이 있으면 `sizeof` 가 `offsetof` 보다 크다** — `struct Gap` 에서 **8 대 5**. `sizeof + n` 은 그만큼 더 잡는다(**안전하다**).
- ★★ **에러는 둘, 확장은 다섯**이다. 확장 다섯은 **`-pedantic` 이라야 보이고 보여도 `cc exit=0`** 이다.
- ★★ **`-D_FORTIFY_SOURCE=2 -O2` 는 크기를 아는 정적 객체만 본다** — `malloc` 으로 잡은 것은 **FAM 도 `char[1]` 도 못 본다.**
- ★ **C99 이전 관용구와 실행 결과·진단은 같다.** 갈리는 것은 **할당 산술(`- 1`)과 표준의 보장** 뿐이다.
- ★ **초기자로는 자동 저장 기간에서 에러**, 정적에서만 확장으로 통과한다.
- ★ **C++ 표준에는 없다** — g++ 는 확장으로 받는다.

## 관련 자료

- [21번 형제 — 구조체 선언·초기화·지정 초기자](../21-struct-declaration-initialization-and-designated-initializers/) — ★★ **직접 선행.**\
  그쪽은 「**길이가 정해진 멤버들**」까지, 여기는 「**마지막 멤버의 길이를 비우면**」부터다.
- [22번 형제 — 구조체 패딩·정렬](../22-struct-padding-and-alignment/) — ★★ **꼬리 패딩의 정본.**\
  그쪽은 「**왜 패딩이 생기나**」, 여기는 「**그 패딩이 할당 산술에 어떻게 새어 드나**」다.\
  ★ **패딩 바이트의 값이 미명시**라는 것도 그쪽이다.
- [8번 형제 — `sizeof`·정렬·`offsetof`](../08-sizeof-alignment-and-offsetof/) — ★★ 재는 **도구**의 정본.\
  여기는 「**그 둘이 갈리는 구조체**」만 본다.
- [15번 형제 — 포인터 산술과 인덱싱](../15-pointer-arithmetic-and-indexing/) — ★★ **(9)가 그 규칙의 직접 결과**다.\
  `a[i]` 가 `*(a+i)` 이고 그 걸음이 `sizeof` 라는 것이 그쪽 정본이다.
- [16번 형제 — 배열-포인터 감쇠와 함수 매개변수](../16-array-pointer-decay-and-function-parameters/) — ★ `m->data` 가 포인터로 감쇠하는 자리.
- [25번 형제 — 불완전 타입과 opaque struct](../25-incomplete-types-and-opaque-struct/) — ★★ **「크기를 모르는 배열」과 헷갈리지 마라.**\
  그쪽은 **타입 전체가 불완전**하고, 여기는 **구조체는 완전한데 꼬리만 비어 있다.**
- [28번 형제 — 저장 기간 4종을 고르는 법](../28-choosing-among-four-storage-durations/) — ★ (8) 때문에 FAM 구조체는 **거의 언제나 할당 저장 기간**이다.
- [23번 형제 — `union` 과 타입 펀닝의 경계](../23-union-and-the-boundary-of-type-punning/) — ★ `union` 의 멤버로 FAM 구조체를 넣는 것도 **(3)의 확장**에 걸린다.
- [목록의 **37번 주제**](../37-malloc-calloc-realloc-free/) — `malloc`/`realloc` 의 계약. **크기를 바꾸려면 통째로 다시 할당**해야 하는 이유는 그쪽이다.
- 목록의 **56번 주제** — 공간 위반. (5)의 「넘겨 써도 대개 안 터진다」는 그쪽이 정본이다.
- 목록의 **58번 주제** — sanitizer 와 경고 플래그. (5)·(7)의 도구 이야기는 그쪽이 정본이다.
- ★ **C++ 갈래와 갈리는 자리** — C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md)).\
  ★★ **유연 배열 멤버는 C++ 표준에 없다** — g++ 는 `ISO C++ forbids flexible array member` 로 **경고만** 내고 받아 준다((10)).

## 용어 풀이

> **유연 배열 멤버(flexible array member, FAM)** — 구조체의 마지막에 놓인 **길이를 안 적은 배열**.\
> 예: `struct Msg { int len; char data[]; };`. **C99 부터**다.

> **꼬리 패딩(trailing padding)** — 구조체 끝에 정렬을 맞추려고 붙는 여백.\
> 예: `struct Gap { int n; char c; char data[]; };` 는 `offsetof(data)` 가 5인데 `sizeof` 가 **8** 이다.

> **`offsetof`** — 구조체 시작부터 그 멤버까지의 **바이트 거리**를 주는 매크로(`<stddef.h>`).\
> 예: `offsetof(struct Gap, data)` 는 **5** 다 — 패딩 전의 진짜 자리다.

> **「길이 1 배열」 관용구(struct hack)** — C99 이전에 FAM 대신 쓰던 것.\
> 예: `char data[1];` 로 선언하고 `malloc(sizeof(s) - 1 + n)` 으로 잡는다.

> **확장(extension)** — 표준에는 없는데 그 구현이 받아 주는 기능.\
> 예: 길이 0 배열 `char d[0];` 은 gcc·clang 의 확장이라 `-pedantic` 으로만 드러난다.

> **`_FORTIFY_SOURCE`** — glibc 가 `strcpy` 같은 함수에 **크기 검사**를 끼워 넣게 하는 매크로.\
> 예: **크기를 아는 정적 객체**는 잡지만 `malloc` 으로 잡은 것은 못 본다.

> **stride(보폭)** — 배열에서 한 칸이 차지하는 바이트 수.\
> 예: FAM 구조체는 `sizeof` 가 stride 가 **아니라서** `m + 1` 이 엉뚱한 자리로 간다.

## 더 들어가면

- ★★ **`realloc` 으로 꼬리를 늘리는 것** — FAM 구조체는 통째로 다시 잡아야 하고, **`realloc` 이 주소를 옮기면 그 구조체를 가리키던 포인터가 전부 무효**가 된다.\
  ★ 이 문서는 **`realloc` 쪽을 던지지 않았다**([목록의 **37번 주제**](../37-malloc-calloc-realloc-free/)가 정본).
- ★★ **FAM 과 정렬** — `char data[]` 대신 `double data[]` 를 쓰면 구조체의 정렬이 올라간다.\
  ★ 이 문서는 **정렬이 올라가는 경우를 던지지 않았다**([8번 형제](../08-sizeof-alignment-and-offsetof/)·[22번 형제](../22-struct-padding-and-alignment/)가 정본).
- ★ **`union` 안의 FAM 구조체** — (3)의 확장에 걸린다. ★ 이 문서는 **던지지 않았다**.
- ★ **gcc 14 의 `-Wflex-array-member-not-at-end`** — 「FAM 을 품은 구조체를 다른 구조체 중간에 넣는 것」을 잡아 주는 새 경고다.\
  ★★ **gcc 13 에는 없다** — 옵션을 주면 `gcc: error: unrecognized command-line option` 이 나고 **`cc exit=1`** 이다(파이프 없이 직접 재서 확인했다).\
  ★ 그 경고를 **실제로 켜서 무엇이 잡히는지는 던지지 않았다**(gcc 14 가 이 머신에 없다).
- ★ **`__builtin_object_size` 를 직접 불러 보는 것** — (7)에서 FORTIFY 가 쓰는 그 함수다.\
  ★ 이 문서는 **직접 부르지 않고** FORTIFY 를 통해서만 관찰했다.
- ★ **C23 의 `memset_explicit`·`memccpy` 같은 새 함수가 FAM 과 어떻게 맞물리나** — ★ **던지지 않았다.**
