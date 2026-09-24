# c/syntax/22 — 구조체 패딩·정렬: 「**같은 멤버라도 순서가 크기를 바꾸고, 구멍의 값은 아무도 약속하지 않는다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — struct](https://en.cppreference.com/w/c/language/struct) · [cppreference — object representation](https://en.cppreference.com/w/c/language/object) · [cppreference — \_Alignas](https://en.cppreference.com/w/c/language/_Alignas) · [GCC 13 Structure-Layout Pragmas](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Structure-Layout-Pragmas.html)
> **실행 검증** — 이 문서의 모든 수치·바이트 격자·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과\
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본 플래그는 `-std=c17 -Wall -Wextra -pedantic`.\
> 패딩 값이 걸린 블록은 **gcc·clang × `-O0`/`-O1`/`-O2` 여섯 벌**을 돌리고 **한 벌을 20번씩** 반복했다.\
> 손으로 계산한 수치는 하나도 없다 — 크기는 `sizeof`, 자리는 `offsetof`, 값은 **바이트 덤프**로 물어봤다.
> **버전** — 패딩·정렬 규칙 자체는 **C89부터**. `_Alignas`/`_Alignof` 는 **C11부터**(`alignas`/`alignof` 철자는 C23부터),\
> 유연 배열 멤버는 **C99부터**. `#pragma pack` 은 **어느 표준에도 없다** — 컴파일러 확장이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> **경계** — [08번 형제](../08-sizeof-alignment-and-offsetof/)는 **도구**(`sizeof`·`_Alignof`·`offsetof`·`_Static_assert`)가 정본이고,\
> 여기는 **규칙**이 정본이다 — 08 자신이 머리말에서 「패딩·정렬의 정본은 22번 주제」라고 선언해 두었다.\
> 구조체의 **선언·초기화**는 [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/),\
> **`union` 의 크기·정렬**은 [23번 형제](../23-union-and-the-boundary-of-type-punning/),\
> **유연 배열 멤버**는 목록의 **26번 주제**, **`memcmp`/`memcpy` 의 계약**은 목록의 **50번 주제**,\
> **엄격한 앨리어싱**은 목록의 **55번 주제**가 정본이다.

## 한눈에 — 쉽게 말하면

**구조체는 멤버를 이어 붙인 것이 아니다. 사이사이에 구멍이 있고, 그 구멍에 무엇이 들어 있는지는 아무도 약속하지 않았다.**

08 이 「구멍이 어디 있나」를 **재는 도구**를 다뤘다면, 여기는 **왜 거기에 생기고 그 안에 무엇이 있나**를 다룬다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **책장에 책을 꽂는다** — 칸 높이가 정해져 있다 | **정렬**(alignment) — `int` 는 4의 배수 주소에서만 시작한다 |
| 큰 책을 먼저 꽂느냐 나중에 꽂느냐로 **남는 틈이 달라진다** | **멤버 순서가 `sizeof` 를 바꾼다** |
| 같은 책 세 권이라도 **꽂는 순서가 여섯 가지** | 멤버 세 개의 순열 여섯 벌 — 실측에서 **16 과 24 로 갈렸다** |
| 틈에 **먼지가 있을 수도 비어 있을 수도** 있다 | **패딩 바이트의 값은 미명시** — 실행마다 달라질 수 있다 |
| 책장을 **통째로 저울에 올리면** 먼지 무게까지 잰다 | `memcmp` 는 **패딩까지 비교한다** — 그래서 쓰면 안 된다 |
| 칸 높이를 **일부러 더 높게** 잡는다 | `_Alignas(16)` — 늘리는 것만 된다 |
| 칸 선을 **깎아 낸다** | `#pragma pack(2)` — **없애는 것이 아니라 2로 깎는 것**이다 |

```text
   struct S { char c; int i; char e; };        sizeof = 12

   자리  0     1   2   3     4   5   6   7     8     9  10  11
       +-----+-------------+-----------------+-----+-------------+
       |  c  |   구멍 3    |     i (4바이트)  |  e  |   구멍 3    |
       +-----+-------------+-----------------+-----+-------------+
          01   ??  ??  ??    02  00  00  00     03   ??  ??  ??
               ^^^^^^^^^^                            ^^^^^^^^^^
               ★ 이 여섯 바이트의 값을 표준은 정해 주지 않는다
```

- 멤버 셋의 크기 합은 **6** 인데 `sizeof` 는 **12** 다. 절반이 구멍이다.
- 그리고 **그 구멍에 무엇이 들어 있는지가 이 편의 본체**다.

> **정렬(alignment)** — 어떤 타입의 객체가 놓일 수 있는 주소의 배수 조건.\
> 예: `int` 의 정렬이 4라는 것은 `int` 객체의 주소가 **4의 배수**여야 한다는 뜻이다.

> **패딩(padding)** — 정렬을 맞추려고 멤버 사이나 구조체 끝에 끼워 넣는 빈 바이트.\
> 예: `char` 다음에 `int` 가 오면 3바이트를 버린다.

> **미명시(unspecified)** — 표준이 「몇 가지 중 하나」라고만 하고 **어느 것인지 고르지 않은 것**.\
> 예: 패딩 바이트의 값. 구현이 문서화할 의무도 없고, **같은 프로그램의 두 실행에서 달라도 된다.**

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **같은 멤버 집합인데 왜 크기가 갈리는가** — 순서를 바꾸면 얼마나 갈리고, 「큰 것부터」가 항상 답인가.
2. ★★★ **구멍 안에는 무엇이 있는가** — 같은 값을 만드는 네 가지 방법이 같은 바이트를 만드는가.
3. **정렬을 내 손으로 바꾸면** 무엇을 얻고 무엇을 잃는가 — `_Alignas` 와 `#pragma pack`.

## 동작 방식

### (1) 배치 규칙은 세 줄뿐이다 — 정본은 08

**언제 쓰나** — 「이 크기가 왜 나왔나」를 설명해야 할 때.

규칙 자체는 [08번 형제](../08-sizeof-alignment-and-offsetof/)가 여섯 구조체로 확인해 두었다. 여기서는 **결론만** 다시 적는다.

```text
   ① 각 멤버는 ★ 자기 정렬의 배수 자리에서 시작한다
   ② 구조체의 정렬  = ★ 가장 엄한 멤버의 정렬
   ③ sizeof         = ★ 그 정렬의 배수   (그래서 끝에도 구멍이 붙는다)
```

- ①이 **멤버 사이의 구멍**을, ③이 **끝의 구멍**을 만든다. 구멍은 이 둘뿐이다.
- 표준이 주는 것은 **「멤버는 선언 순서대로 놓인다」와 「첫 멤버의 `offsetof` 는 0」** 정도다.\
  **구체적인 수치는 전부 구현 정의**다 — 그래서 손으로 계산하지 않고 물어본다.
- ★ 물어보는 법도 08 이 정본이다 — `sizeof` · `_Alignof` · `offsetof` · `_Static_assert`.

비용 — 규칙은 공짜로 적용된다. **비용이 생기는 자리는 순서를 고르는 쪽**이다((2)).

### (2) ★★ 같은 멤버 집합, 순서 여섯 벌 — 이 편의 첫 번째 본체

**언제 쓰나** — 구조체를 선언할 때마다. 배열로 100만 개 만들 거라면 특히.

08 은 **두 순서**(나쁜 것·좋은 것)를 비교했다. 여기서는 **순열을 전부** 돌린다 —\
멤버가 셋이면 여섯 가지고, 여섯 가지의 크기가 **몇 종류로 갈리는지**가 질문이다.

```c
/* s22a.c */
#include <stdio.h>
#include <stddef.h>

struct CID { char c; int i; double d; };
struct CDI { char c; double d; int i; };
struct ICD { int i; char c; double d; };
struct IDC { int i; double d; char c; };
struct DCI { double d; char c; int i; };
struct DIC { double d; int i; char c; };

#define ROW(T, m1, m2, m3) \
    printf("%-4s sizeof=%2zu _Alignof=%zu   offsets: %s=%2zu %s=%2zu %s=%2zu\n", \
           #T, sizeof(struct T), _Alignof(struct T), \
           #m1, offsetof(struct T, m1), #m2, offsetof(struct T, m2), \
           #m3, offsetof(struct T, m3))

int main(void) {
    printf("멤버 집합은 여섯 벌 모두 같다 — char 1 + int 4 + double 8 = 13 바이트\n\n");
    ROW(CID, c, i, d);
    ROW(CDI, c, d, i);
    ROW(ICD, i, c, d);
    ROW(IDC, i, d, c);
    ROW(DCI, d, c, i);
    ROW(DIC, d, i, c);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s22a.c -o x ; ./x (cc exit=0 · run exit=0) =====
멤버 집합은 여섯 벌 모두 같다 — char 1 + int 4 + double 8 = 13 바이트

CID  sizeof=16 _Alignof=8   offsets: c= 0 i= 4 d= 8
CDI  sizeof=24 _Alignof=8   offsets: c= 0 d= 8 i=16
ICD  sizeof=16 _Alignof=8   offsets: i= 0 c= 4 d= 8
IDC  sizeof=24 _Alignof=8   offsets: i= 0 d= 8 c=16
DCI  sizeof=16 _Alignof=8   offsets: d= 0 c= 8 i=12
DIC  sizeof=16 _Alignof=8   offsets: d= 0 i= 8 c=12
```

`offsetof` 로 잰 자리를 **바이트 지도**로 그렸다(`.` 이 구멍).

```text
   멤버 크기의 합 = char 1 + int 4 + double 8 = 13

   CID   c...iiiidddddddd            16     구멍 3
   CDI   c.......ddddddddiiii....    24     구멍 11   ★ 최악
   ICD   iiiic...dddddddd            16     구멍 3
   IDC   iiii....ddddddddc.......    24     구멍 11   ★ 최악
   DCI   ddddddddc...iiii            16     구멍 3
   DIC   ddddddddiiiic...            16     구멍 3
```

그림 해설 (한 단계씩):

- 여섯 벌의 멤버 집합은 **한 글자도 다르지 않다.** 순서만 다르다.
- 크기는 **16 아니면 24** 두 종류로 갈렸다. **여섯 중 넷이 16** 이다.
- ★★ **「큰 것부터 놓아라」는 충분조건이지 필요조건이 아니다.** `DCI`·`DIC` 는 큰 것부터라 16이지만,\
  `CID`·`ICD` 는 **작은 것부터인데도 16** 이다.
- ★★★ **갈리는 자리는 하나뿐이다 — `double` 이 가운데 낀 두 벌**(`CDI`·`IDC`).\
  `double` 앞에서 8의 배수로 밀어 올리느라 구멍이 생기고, **남은 `int` 4바이트 뒤에 또 끝 구멍**이 붙는다.
- 그래서 외울 것은 「큰 것부터」가 아니라 ★ **「가장 엄한 멤버를 가운데 두지 마라」** 다.
- 순서를 바꾸는 것은 **공짜**다 — 코드도 안 바뀌고 성능도 안 바뀐다. 24가 16이 되면 **배열 100만 개에 8MB** 다.

비용 — 없다. 다만 **`offsetof` 로 확인하지 않으면 어느 쪽인지 알 수 없다.**

### (3) ★★★ 구멍 안에는 무엇이 있나 — 패딩 값은 미명시다

**언제 쓰나** — 구조체를 `memcmp` 로 비교하거나, 통째로 파일·소켓에 쓰거나, 해시할 때.

같은 값 `{ 1, 2, 3 }` 을 **네 가지 방법**으로 만들었다. 만들기 전에 **스택을 `0xAA` 로 더럽혀** 둔다 —\
구멍에 「무엇이든」 들어올 수 있다는 것을 눈에 보이게 하려는 것이다.

```c
/* s22b.c */
#include <stdio.h>
#include <string.h>

struct S { char c; int i; char e; };   /* 구멍: 1~3 과 9~11 */

#define SGN(m) ((m) > 0 ? "+" : (m) < 0 ? "-" : "0")

static void dirty(void) {              /* 스택의 같은 자리를 0xAA 로 더럽힌다 */
    volatile unsigned char buf[64];
    for (int k = 0; k < 64; k++) buf[k] = 0xAA;
    if (buf[0] != 0xAA) printf("!");
}

static struct S make(int how) {        /* dirty 와 같은 깊이·같은 자리 */
    volatile unsigned char guard[8] = {0};
    struct S v;
    if (how == 0) { struct S t = { .c = 1, .i = 2, .e = 3 }; v = t; }
    else if (how == 1) { v.c = 1; v.i = 2; v.e = 3; }
    else { memset(&v, 0, sizeof v); v.c = 1; v.i = 2; v.e = 3; }
    (void)guard;
    return v;
}

static void show(const char *tag, const struct S *p) {
    const unsigned char *b = (const unsigned char *)p;
    printf("%-18s", tag);
    for (size_t k = 0; k < sizeof *p; k++) {
        int pad = (k >= 1 && k <= 3) || (k >= 9 && k <= 11);
        printf(" %s%02x%s", pad ? "[" : " ", b[k], pad ? "]" : " ");
    }
    printf("\n");
}

int main(void) {
    dirty(); struct S a = make(0);   /* 초기자 */
    dirty(); struct S b = make(1);   /* 멤버 대입만 */
    dirty(); struct S c = make(2);   /* memset 뒤 대입 */
    struct S d = a;                  /* 구조체 대입 */

    printf("멤버 값은 넷 다 { 1, 2, 3 } 이다.  [ ] 안이 패딩 바이트\n\n");
    show("a initializer", &a);
    show("b member-assign", &b);
    show("c memset+assign", &c);
    show("d = a  (copy)", &d);
    printf("\n멤버끼리 : a==b %d  a==c %d  a==d %d   (1 이면 같다)\n",
           a.c == b.c && a.i == b.i && a.e == b.e,
           a.c == c.c && a.i == c.i && a.e == c.e,
           a.c == d.c && a.i == d.i && a.e == d.e);
    printf("memcmp   : a,b %s  a,c %s  a,d %s   (부호만 — 크기는 미명시다)\n",
           SGN(memcmp(&a, &b, sizeof a)), SGN(memcmp(&a, &c, sizeof a)),
           SGN(memcmp(&a, &d, sizeof a)));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s22b.c -o x ; ./x (cc exit=0 · run exit=0) =====
멤버 값은 넷 다 { 1, 2, 3 } 이다.  [ ] 안이 패딩 바이트

a initializer       01  [aa] [aa] [aa]  02   00   00   00   03  [aa] [aa] [aa]
b member-assign     01  [aa] [aa] [aa]  02   00   00   00   03  [aa] [aa] [aa]
c memset+assign     01  [00] [00] [00]  02   00   00   00   03  [00] [00] [00]
d = a  (copy)       01  [aa] [aa] [aa]  02   00   00   00   03  [aa] [aa] [aa]

멤버끼리 : a==b 1  a==c 1  a==d 1   (1 이면 같다)
memcmp   : a,b 0  a,c +  a,d 0   (부호만 — 크기는 미명시다)
```

```text
   같은 { 1, 2, 3 } 인데 바이트는 이렇게 갈린다  (gcc -O0)

   a  초기자 = { .c=1, .i=2, .e=3 }   01 [aa aa aa] 02 00 00 00 03 [aa aa aa]
   b  멤버 대입만                      01 [aa aa aa] 02 00 00 00 03 [aa aa aa]
   c  memset(0) 뒤 대입                01 [00 00 00] 02 00 00 00 03 [00 00 00]
   d  d = a  (구조체 대입)             01 [aa aa aa] 02 00 00 00 03 [aa aa aa]
                                          ^^^^^^^^                 ^^^^^^^^
   멤버끼리 비교 : 넷 다 같다 (1 1 1)
   memcmp       : a,c 만 「다르다」  <- ★ 구멍만 보고 다르다고 답했다
```

그림 해설 (한 단계씩):

- ★★★ **초기자로 만든 `a` 조차 구멍이 `0xAA` 로 남았다.**\
  「`= { … }` 를 쓰면 나머지가 0이 된다」는 **멤버에만** 해당하는 규칙이다([21번 형제](../21-struct-declaration-initialization-and-designated-initializers/)가 정본).\
  **구멍은 멤버가 아니므로 그 규칙 밖**이다.
- ★★ **`d = a` 는 구멍까지 그대로 복사했다.** 구조체 대입이 패딩을 복사하는지도 **미명시**다 —\
  이 벌에서는 복사했고, 다른 벌에서는 안 할 수 있다.
- ★★ **`memcmp` 는 멤버가 아니라 바이트를 본다.** 멤버끼리는 `1 1 1` 로 전부 같은데 `a,c` 만 「다르다」고 답했다.\
  틀린 쪽은 `memcmp` 가 아니라 **구조체를 `memcmp` 로 비교한 코드**다.
- ★ 유일하게 예측 가능한 것은 **`c`** 뿐이다 — `memset` 이 **구멍을 포함해 전부** 0으로 만들었기 때문이다.

**그런데 이 격자 자체가 한 벌의 결과다.** 컴파일러와 최적화 수준을 바꾸면 다르게 나온다.

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 s22b.c -o x ; ./x (cc exit=0 · run exit=0) =====
멤버 값은 넷 다 { 1, 2, 3 } 이다.  [ ] 안이 패딩 바이트

a initializer       01  [80] [00] [00]  02   00   00   00   03  [23] [fa] [9b]
b member-assign     01  [7f] [00] [00]  02   00   00   00   03  [00] [00] [00]
c memset+assign     01  [00] [00] [00]  02   00   00   00   03  [00] [00] [00]
d = a  (copy)       01  [80] [00] [00]  02   00   00   00   03  [23] [fa] [9b]

멤버끼리 : a==b 1  a==c 1  a==d 1   (1 이면 같다)
memcmp   : a,b +  a,c +  a,d 0   (부호만 — 크기는 미명시다)
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 s22b.c -o x ; ./x (cc exit=0 · run exit=0) =====
멤버 값은 넷 다 { 1, 2, 3 } 이다.  [ ] 안이 패딩 바이트

a initializer       01  [00] [00] [00]  02   00   00   00   03  [ca] [2b] [91]
b member-assign     01  [aa] [aa] [aa]  02   00   00   00   03  [00] [00] [00]
c memset+assign     01  [00] [00] [00]  02   00   00   00   03  [00] [00] [00]
d = a  (copy)       01  [00] [00] [00]  02   00   00   00   03  [ca] [2b] [91]

멤버끼리 : a==b 1  a==c 1  a==d 1   (1 이면 같다)
memcmp   : a,b -  a,c +  a,d 0   (부호만 — 크기는 미명시다)
```

- **gcc `-O2`** 에서는 `a` 의 앞 구멍이 `aa` 가 아니라 **다른 값**이 됐고, 꼬리 구멍도 셋 다 달랐다.\
  `b` 의 꼬리 구멍은 **0** 이 됐다 — 같은 소스, 같은 컴파일러인데 **`-O` 하나로 갈린다.**
- **clang `-O0`** 은 또 다르다 — `a` 의 앞 구멍이 `00` 인데 **꼬리 구멍은 쓰레기**다.\
  ★ **`memcmp(a,b)` 의 부호가 gcc 는 `0`/`+`, clang 은 `-`** 로 갈렸다.
- ★★★ 세 벌에서 **한 줄도 같은 자리가 없다.** 이것이 「미명시」의 뜻이다 —\
  **틀린 구현이 하나도 없고**, 어느 벌도 표준을 어기지 않았다.

**그러면 몇 번을 돌려야 하나.** 같은 바이너리를 **20번씩** 돌려 격자 네 줄이 몇 가지나 나오는지 셌다.

```text
===== 같은 바이너리를 20번씩 돌려 패딩 격자 네 줄이 몇 가지나 나오나 (exit=0) =====
gcc   -O0 : 20번 중 서로 다른 격자  1가지
gcc   -O1 : 20번 중 서로 다른 격자  1가지
gcc   -O2 : 20번 중 서로 다른 격자 20가지
clang -O0 : 20번 중 서로 다른 격자 20가지
clang -O1 : 20번 중 서로 다른 격자 20가지
clang -O2 : 20번 중 서로 다른 격자 20가지
```

- ★★ **gcc `-O0`·`-O1` 은 20번 전부 같은 격자**였다. 그래서 위 `-O0` 블록을 **정본 격자**로 실었다.
- ★★ **gcc `-O2` 와 clang 세 벌은 20번이 전부 달랐다** — 20/20 이 서로 다른 격자다.\
  그래서 그 두 블록에서 **대조할 것은 숫자가 아니라 「구멍 자리만 흔들리고 멤버 자리는 안 흔들린다」는 성질**이다.
- ★ 「세 번 돌려 보고 같았다」로 끝냈다면 **gcc `-O0` 만 보고 「패딩은 `0xAA` 로 남는다」고 적었을 것**이다.

**`memcmp` 의 반환값은 어디까지 믿을 수 있나.** 부호는 규정되어 있고 **크기는 미명시**다.

```text
===== 같은 바이너리를 30번 돌려 memcmp 의 반환값 크기를 센다 (exit=0) =====
30번 : 170
```

- 이 머신에서는 **30번 전부 `170`**(`0xAA`)이었다. **그래도 크기에 기대면 안 된다** —\
  같은 glibc 도 정렬·길이에 따라 다른 경로를 타고, 다른 구현은 `-1`/`0`/`1` 만 돌려주기도 한다.
- ★ 그래서 위 프로그램은 **부호만 찍는다.** 「돌려 보니 170 이더라」를 근거로 쓰지 않으려는 것이다.

비용 — **구멍을 예측 가능하게 만드는 값은 `memset` 한 번**이다. 다만 그 뒤의 **대입 한 번이 다시 불확실하게 만들 수 있다**((5) 아래 「어디서 틀리나」 2번).

### (4) `_Alignas` — 늘릴 수는 있고 줄일 수는 없다

**언제 쓰나** — 캐시 라인·SIMD·DMA 버퍼처럼 **기본 정렬보다 엄한 자리**에 놓아야 할 때.

기본 사용법과 `_Alignof` 는 [08번 형제](../08-sizeof-alignment-and-offsetof/)가 정본이다. 여기서는 **구조체 크기가 따라 커지는 쪽**만 본다.

```c
/* s22d.c */
#include <stdio.h>
#include <stddef.h>

struct A { char c; };
struct B { _Alignas(16) char c; };            /* 멤버 하나를 16 으로 */
struct C { char c; _Alignas(8) int i; };      /* 가운데 멤버를 8 로 */
struct D { char c; int i; };                  /* 대조군 */

#define ROW(T) printf("%-9s sizeof=%2zu _Alignof=%2zu\n", #T, sizeof(struct T), _Alignof(struct T))

int main(void) {
    ROW(A); ROW(B); ROW(C); ROW(D);
    printf("\nstruct C offsets: c=%zu i=%zu   <- 구멍이 3 이 아니라 7 이 된다\n",
           offsetof(struct C, c), offsetof(struct C, i));
    printf("struct D offsets: c=%zu i=%zu\n",
           offsetof(struct D, c), offsetof(struct D, i));
    struct B arr[2];
    printf("\n_Alignas 는 배열에도 따라온다 : (char*)&arr[1] - (char*)&arr[0] = %td\n",
           (char *)&arr[1] - (char *)&arr[0]);
    printf("&arr[0] 가 16 의 배수인가 : %d\n", ((unsigned long)(void *)&arr[0] % 16) == 0);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s22d.c -o x ; ./x (cc exit=0 · run exit=0) =====
A         sizeof= 1 _Alignof= 1
B         sizeof=16 _Alignof=16
C         sizeof=16 _Alignof= 8
D         sizeof= 8 _Alignof= 4

struct C offsets: c=0 i=8   <- 구멍이 3 이 아니라 7 이 된다
struct D offsets: c=0 i=4

_Alignas 는 배열에도 따라온다 : (char*)&arr[1] - (char*)&arr[0] = 16
&arr[0] 가 16 의 배수인가 : 1
```

```text
   struct A { char c; }                        1

   struct B { _Alignas(16) char c; }           16     <- ★ 멤버는 1바이트인데
   +-+---------------------------+
   |c|  . . . . . . . . . . . .  |   구멍 15
   +-+---------------------------+

   struct D { char c; int i; }                 8      <- 대조군
   +-+---+----+
   |c|...| i  |   구멍 3
   +-+---+----+

   struct C { char c; _Alignas(8) int i; }     16
   +-+-------+----+----+
   |c|.......| i  |....|   구멍 7 + 끝 구멍 4
   +-+-------+----+----+
```

그림 해설 (한 단계씩):

- **`_Alignas(16)` 를 멤버 하나에 걸면 구조체 전체의 정렬이 16이 되고, `sizeof` 도 16** 이 된다.\
  규칙 ②·③이 그대로 따라온 것이다 — **정렬을 키우면 크기가 따라 커진다.**
- **배열에도 따라온다.** `arr[1] - arr[0]` 이 **16** 이었고 `&arr[0]` 도 16의 배수였다.
- `struct C` 는 구멍이 **3에서 7로 늘고 끝에 4가 더 붙어** 8이 16이 됐다.\
  ★ **정렬 지시 하나가 크기를 두 배로 만든다.**
- **줄이는 쪽은 거절당한다.**

```c
/* s22d2.c */
struct Narrow { _Alignas(1) int i; };      /* 정렬을 줄이려 한다 */
struct Odd    { _Alignas(3) char c; };     /* 2의 거듭제곱이 아닌 값 */
int main(void) { return sizeof(struct Narrow) + sizeof(struct Odd); }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s22d2.c -o x (cc exit=1) =====
s22d2.c:1:33: error: ‘_Alignas’ specifiers cannot reduce alignment of ‘i’
    1 | struct Narrow { _Alignas(1) int i; };      /* 정렬을 줄이려 한다 */
      |                                 ^
s22d2.c:2:8: error: requested alignment ‘3’ is not a positive power of 2
    2 | struct Odd    { _Alignas(3) char c; };     /* 2의 거듭제곱이 아닌 값 */
      |        ^~~
```

- ★ 에러가 둘이다 — **줄이려 한 것**(`_Alignas(1) int`)과 **2의 거듭제곱이 아닌 값**(`_Alignas(3)`).
- **`cc exit=1`** 이다. 「경고 0건」이 아니라 **컴파일이 멈춘 것**이다.
- ★ 정렬을 **줄이고 싶으면** `_Alignas` 가 아니라 `#pragma pack` 쪽이다((5)) — 그리고 그쪽은 표준이 아니다.

비용 — 메모리다. `_Alignas(64)` 짜리를 배열로 만들면 **한 원소가 64바이트 경계마다** 놓인다.

### (5) `#pragma pack` — 없애는 것이 아니라 깎는 것이다

**언제 쓰나** — 파일 형식·네트워크 패킷을 구조체로 그대로 매핑하고 싶을 때. **대개는 쓰지 않는 쪽이 답이다.**

`#pragma pack(1)` 과 UBSan·경고 비대칭은 [08번 형제](../08-sizeof-alignment-and-offsetof/)가 정본이다.\
여기서는 **`1` 이 아닌 값**을 넣어 본다 — `pack` 의 인자가 **「정렬 상한」** 이라는 것이 여기서 드러난다.

```c
/* s22e.c */
#include <stdio.h>
#include <string.h>
#include <stddef.h>

struct P0 { char c; int i; double d; };            /* 기본 */
#pragma pack(push, 1)
struct P1 { char c; int i; double d; };
#pragma pack(pop)
#pragma pack(push, 2)
struct P2 { char c; int i; double d; };
#pragma pack(pop)
#pragma pack(push, 4)
struct P4 { char c; int i; double d; };
#pragma pack(pop)

#define ROW(T) printf("%-4s sizeof=%2zu _Alignof=%zu   c=%zu i=%zu d=%2zu\n", \
    #T, sizeof(struct T), _Alignof(struct T), \
    offsetof(struct T, c), offsetof(struct T, i), offsetof(struct T, d))

int main(void) {
    ROW(P0); ROW(P1); ROW(P2); ROW(P4);
    printf("\npack(2) 는 정렬을 「없애는」 것이 아니라 2 로 「깎는」 것이다\n");

    struct P2 v;
    memset(&v, 0, sizeof v);              /* 패딩까지 0 으로 — 덤프를 결정적으로 */
    v.c = 'x'; v.i = 0x41424344; v.d = 1.5;
    const unsigned char *b = (const unsigned char *)&v;
    printf("P2 의 바이트 :");
    for (size_t k = 0; k < sizeof v; k++) printf(" %02x", b[k]);
    printf("\n");

    struct P1 arr[3];
    printf("\npack(1) 배열의 멤버 주소가 정렬을 지키나 (0 이면 지킨 것)\n");
    for (int k = 0; k < 3; k++)
        printf("  arr[%d] : &i %% 4 = %lu · &d %% 8 = %lu\n", k,
               (unsigned long)(void *)&arr[k].i % 4,
               (unsigned long)(void *)&arr[k].d % 8);
    printf("  -> 13 바이트씩 밀리므로 ★ 맞는 자리가 나오는 것은 우연이다\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s22e.c -o x ; ./x (cc exit=0 · run exit=0) =====
P0   sizeof=16 _Alignof=8   c=0 i=4 d= 8
P1   sizeof=13 _Alignof=1   c=0 i=1 d= 5
P2   sizeof=14 _Alignof=2   c=0 i=2 d= 6
P4   sizeof=16 _Alignof=4   c=0 i=4 d= 8

pack(2) 는 정렬을 「없애는」 것이 아니라 2 로 「깎는」 것이다
P2 의 바이트 : 78 00 44 43 42 41 00 00 00 00 00 00 f8 3f

pack(1) 배열의 멤버 주소가 정렬을 지키나 (0 이면 지킨 것)
  arr[0] : &i % 4 = 1 · &d % 8 = 5
  arr[1] : &i % 4 = 2 · &d % 8 = 2
  arr[2] : &i % 4 = 3 · &d % 8 = 7
  -> 13 바이트씩 밀리므로 ★ 맞는 자리가 나오는 것은 우연이다
```

```text
   같은 { char c; int i; double d; } 를 네 가지 pack 으로

   기본     c...iiiidddddddd            16   _Alignof 8
   pack(1)  ciiiidddddddd               13   _Alignof 1   구멍 0
   pack(2)  c.iiiidddddddd              14   _Alignof 2   구멍 1
   pack(4)  c...iiiidddddddd            16   _Alignof 4   구멍 3
                                                ^
                          ★ pack(N) = 「각 멤버의 정렬을 N 이하로 깎아라」
```

그림 해설 (한 단계씩):

- ★★ **`pack(4)` 는 기본과 크기가 같다.** `int` 의 정렬 4는 이미 4 이하라 안 깎이고,\
  `double` 만 8에서 4로 깎였는데 **그 자리가 마침 8의 배수**여서 결과가 안 바뀌었다.
- ★★★ **`pack(2)` 가 14** 인 것이 핵심이다. 구멍이 **0이 아니라 1** 이다 —\
  「`pack` 은 패딩을 없앤다」가 아니라 **「각 멤버의 정렬 요구를 N 으로 깎는다」** 이기 때문이다.
- **clang 도 한 글자도 같았다.**

```text
===== clang -std=c17 -Wall -Wextra -pedantic s22e.c -o x ; ./x (cc exit=0 · run exit=0) =====
P0   sizeof=16 _Alignof=8   c=0 i=4 d= 8
P1   sizeof=13 _Alignof=1   c=0 i=1 d= 5
P2   sizeof=14 _Alignof=2   c=0 i=2 d= 6
P4   sizeof=16 _Alignof=4   c=0 i=4 d= 8

pack(2) 는 정렬을 「없애는」 것이 아니라 2 로 「깎는」 것이다
P2 의 바이트 : 78 00 44 43 42 41 00 00 00 00 00 00 f8 3f

pack(1) 배열의 멤버 주소가 정렬을 지키나 (0 이면 지킨 것)
  arr[0] : &i % 4 = 1 · &d % 8 = 5
  arr[1] : &i % 4 = 2 · &d % 8 = 2
  arr[2] : &i % 4 = 3 · &d % 8 = 7
  -> 13 바이트씩 밀리므로 ★ 맞는 자리가 나오는 것은 우연이다
```

- ★ **구현 정의인데 두 구현이 같은 답을 냈다.** 이것은 **보장이 아니라 관찰**이다 —\
  둘 다 같은 플랫폼 ABI 를 따르기 때문이고, 컴파일러가 바뀌거나 아키텍처가 바뀌면 갈릴 수 있다.
- ★★ **그래서 얻는 대신 잃는 것**은 `pack(1)` 배열이 보여 준다. 원소가 **13바이트씩** 밀리므로\
  `&arr[k].i % 4` 가 `1 · 2 · 3` 으로 돌아간다 — **어느 원소에서도 0이 아니다.**\
  값이 0으로 나오는 원소가 있어도 그것은 **우연**이고, 그 주소를 역참조하면 08 이 UBSan 으로 잡은 그 UB 다.

비용 — 크기 3바이트를 얻고 **정렬 보장을 잃는다.** 이식 가능한 답은 **`memcpy` 로 바이트를 직접 옮기는 것**이다(목록의 **50번 주제**).

### (6) 유연 배열 멤버 — 헤더 뒤에도 패딩이 있다

**언제 쓰나** — 헤더 + 가변 길이 데이터를 **한 번의 할당**으로 묶을 때. 정본은 목록의 **26번 주제**다.

08 이 `sizeof` 가 유연 배열 멤버를 세지 않는다는 것을 보였다. 여기서는 **패딩 각도**만 본다.

```c
/* s22f.c */
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>

struct Ba { int  n; char a[]; };    /* 헤더가 4, 원소가 1 */
struct Bb { char n; int  a[]; };    /* 헤더가 1, 원소가 4 */
struct Bc { double d; char a[]; };  /* 헤더가 8, 원소가 1 */

#define ROW(T, m) printf("%-9s sizeof=%zu _Alignof=%zu offsetof(a)=%zu\n", \
                         #T, sizeof(struct T), _Alignof(struct T), offsetof(struct T, m))

int main(void) {
    ROW(Ba, a); ROW(Bb, a); ROW(Bc, a);
    printf("\n★ Bb 는 sizeof 가 4 인데 offsetof(a) 도 4 다 — 헤더 뒤 3바이트가 패딩이다\n");

    size_t n = 5;
    struct Bb *p = malloc(offsetof(struct Bb, a) + n * sizeof p->a[0]);
    if (!p) return 1;
    p->n = 'x';
    for (size_t k = 0; k < n; k++) p->a[k] = (int)k * 10;
    printf("한 번 할당한 크기 = %zu 바이트 (offsetof %zu + 5*%zu)\n",
           offsetof(struct Bb, a) + n * sizeof p->a[0],
           offsetof(struct Bb, a), sizeof p->a[0]);
    printf("p->n='%c'  a =", p->n);
    for (size_t k = 0; k < n; k++) printf(" %d", p->a[k]);
    printf("\n");
    printf("sizeof(*p) + 5*4 로 잡았다면 = %zu 바이트 — ★ 같은 값이지만 우연이다\n",
           sizeof *p + n * sizeof p->a[0]);
    free(p);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s22f.c -o x ; ./x (cc exit=0 · run exit=0) =====
Ba        sizeof=4 _Alignof=4 offsetof(a)=4
Bb        sizeof=4 _Alignof=4 offsetof(a)=4
Bc        sizeof=8 _Alignof=8 offsetof(a)=8

★ Bb 는 sizeof 가 4 인데 offsetof(a) 도 4 다 — 헤더 뒤 3바이트가 패딩이다
한 번 할당한 크기 = 24 바이트 (offsetof 4 + 5*4)
p->n='x'  a = 0 10 20 30 40
sizeof(*p) + 5*4 로 잡았다면 = 24 바이트 — ★ 같은 값이지만 우연이다
```

```text
   struct Bb { char n; int a[]; };

   sizeof = 4                 offsetof(a) = 4
   +----+                     +----+----+----+----+----+----+
   | n  | . . .               | n  |...| a[0]| a[1]| ...
   +----+                     +----+----+----+----+----+----+
     0   1  2  3                0   1 2 3  4
         ^^^^^^^
         ★ 헤더 1바이트 뒤 3바이트가 패딩이고, sizeof 는 그것까지 센다

   할당 = offsetof(Bb, a) + n * sizeof p->a[0]     <- ★ 옳은 형태
   할당 = sizeof(*p)      + n * sizeof p->a[0]     <- 여기서는 우연히 같았다
```

그림 해설 (한 단계씩):

- **`sizeof(struct Bb)` 와 `offsetof(struct Bb, a)` 가 둘 다 4** 다. 멤버는 `char` 하나뿐인데 그렇다 —\
  `int` 배열이 4의 배수 자리에서 시작해야 하므로 **헤더 뒤에 3바이트 구멍**이 생기고,\
  규칙 ③이 `sizeof` 를 4의 배수로 만든다.
- ★ **두 값이 같은 것은 이 구조체의 우연**이다. `struct Bc`(`double` 헤더)도 둘 다 8로 같았지만,\
  **헤더 뒤 패딩과 끝 패딩이 다른 구조체에서는 갈린다.**
- ★★ 그래서 **`offsetof` 쪽이 언제나 옳은 형태**다. `sizeof *p` 는 **끝 패딩을 세므로 더 크게 잡을 수는 있어도**\
  「헤더가 어디서 끝나는가」를 답하지는 않는다.

비용 — 할당 한 번으로 줄여 준다. 대신 **크기 계산을 손으로 한다** — 그 식을 틀리면 잡아 주는 것이 없다.

## 문법 — 형태와 규칙

### 형태

```text
struct S { char c; int i; double d; };   /* 멤버는 ★ 선언 순서대로 놓인다 */

_Alignas(16) struct S s;                 /* C11 — 객체에 */
struct T { _Alignas(8) int i; };         /* C11 — 멤버에 */
_Alignof(struct S)                       /* C11 — 물어보는 쪽 */

#pragma pack(push, 2)                    /* ★ 표준이 아니다 — 컴파일러 확장 */
struct P { char c; int i; };
#pragma pack(pop)

struct Buf { int n; char a[]; };         /* C99 유연 배열 멤버 */
malloc(offsetof(struct Buf, a) + n * sizeof b->a[0]);
```

### 금지 사례 — 걸리는 것과 안 걸리는 것

```text
/* (1) 정렬을 줄이려 한다 -> ★ error (cc exit=1) */
struct Narrow { _Alignas(1) int i; };

/* (2) 2의 거듭제곱이 아닌 정렬 -> ★ error */
struct Odd { _Alignas(3) char c; };

/* (3) 멤버 크기를 더해 sizeof 를 예측한다 -> 에러도 경고도 없다. 그냥 틀린다 */
sizeof(struct S) == 1 + 4 + 8;

/* (4) memcmp 로 구조체를 비교한다 -> ★ 경고 0건. 패딩 때문에 틀린다 */
memcmp(&x, &y, sizeof x);

/* (5) 구조체를 통째로 파일·소켓에 쓴다 -> ★ 경고 0건. 구멍의 값이 새어 나간다 */
fwrite(&x, sizeof x, 1, fp);

/* (6) 유연 배열 멤버를 sizeof 로 할당한다 -> 경고 0건. 여기서는 우연히 맞았다 */
malloc(sizeof *p + n * sizeof p->a[0]);
```

- **(1)·(2)만 컴파일러가 막는다.** (3)\~(6)은 **전부 조용히 통과한다.**
- ★ 이 주제의 사고가 위험한 이유가 여기 있다 — **막아 주는 것이 거의 없다.**

### 규칙 불릿

- 멤버는 **선언 순서대로** 놓인다. 컴파일러가 순서를 바꿔 주지 않는다.
- 각 멤버는 **자기 정렬의 배수 자리**에서 시작하고, 구조체의 정렬은 **가장 엄한 멤버의 정렬**,\
  **`sizeof` 는 그 정렬의 배수**다(정본은 [08번 형제](../08-sizeof-alignment-and-offsetof/)).
- **같은 멤버 집합이라도 순서가 다르면 크기가 다를 수 있다** — 실측에서 여섯 순열이 **16 과 24** 로 갈렸다.
- **가장 엄한 멤버를 가운데 두면 손해**다. 「큰 것부터」는 충분조건일 뿐이다.
- ★★ **패딩 바이트의 값은 미명시**다. 초기자를 써도, 구조체 대입을 해도 보장되지 않는다.
- ★ **구조체 대입이 패딩을 복사하는지도 미명시**다.
- **`memcmp` 는 패딩까지 본다** — 구조체 비교에 쓰면 안 된다. `memcmp` 의 **부호는 규정, 크기는 미명시**다.
- **`_Alignas` 는 늘리기만** 된다. 줄이려 하거나 2의 거듭제곱이 아니면 **에러**다.
- **`#pragma pack(N)` 은 「정렬 상한 N」** 이다. 패딩을 **없애는 것이 아니라 깎는 것**이고, **표준이 아니다.**
- **유연 배열 멤버의 할당 크기는 `offsetof` 로 잡는다.**

## 어디서 틀리나

### 1. 멤버 순서를 「큰 것부터」로만 외운다

- 실측에서 **여섯 순열 중 넷이 최소(16)** 였다. 「큰 것부터」인 두 벌도 16이지만 **작은 것부터인 두 벌도 16** 이다.
- ★ 실제로 손해 본 것은 **`double` 을 가운데 둔 두 벌**뿐이다.
- 외울 것은 **「가장 엄한 멤버를 가운데 두지 마라」** 이고, 확인은 **`offsetof` 로** 한다.

### 2. 「`memset` 했으니 패딩은 0이다」로 믿는다

- `memset` 직후에는 맞다. 그런데 **그 뒤의 구조체 대입 한 번이 되돌릴 수 있다.**
- 실측 — clang `-O0` 에서 `d = a` 가 **`a` 의 쓰레기 구멍을 그대로 복사**했고,\
  clang `-O1` 에서는 `memset` 으로 0이 된 `c` 의 **꼬리 구멍이 값 반환 과정에서 되살아났다.**
- ★★ **안전한 답은 패딩을 예측하는 것이 아니라 패딩을 보지 않는 것**이다 — **멤버끼리 비교**한다.

### 3. 구조체를 통째로 파일·네트워크·해시에 넣는다

- 구멍의 값이 **그대로 나간다.** 스택에 있던 다른 데이터가 섞여 나갈 수 있다.
- 받는 쪽이 **다른 컴파일러·다른 `-O`** 면 같은 바이트가 안 나온다 — 실측에서 여섯 벌이 전부 달랐다.
- ★ 경고는 **0건**이다. `-Wall -Wextra -pedantic` 도 UBSan 도 말하지 않는다.
- 답은 **멤버를 하나씩 직렬화**하는 것이다.

### 4. `#pragma pack` 을 「패딩을 없애는 스위치」로 읽는다

- `pack(2)` 는 구멍이 **0이 아니라 1** 이었고, `pack(4)` 는 **기본과 크기가 같았다.**
- 인자는 「없앤다」가 아니라 **「정렬 상한」** 이다.
- ★ 그리고 `pack(1)` 배열의 원소가 13바이트씩 밀려 **멤버 주소가 정렬을 지키는 것이 우연**이 된다.

### 5. `sizeof *p` 로 유연 배열 멤버를 할당한다

- 실측에서 `offsetof` 로 잡은 것과 **같은 24바이트**가 나왔다 — **우연이다.**
- `sizeof` 는 **끝 패딩을 세고** `offsetof` 는 **헤더가 끝나는 자리**를 답한다. 두 값이 갈리는 구조체가 있다.
- 정본은 목록의 **26번 주제**.

### 6. 「같은 머신이니 같을 것」으로 믿는다

- 같은 머신·같은 소스인데 **gcc `-O0`/`-O2`/clang `-O0` 세 벌이 전부 달랐다.**
- 게다가 **gcc `-O2` 와 clang 은 20번 실행이 전부 달랐다** — 같은 바이너리인데도.
- ★ 「세 판 돌려 보고 같았다」는 이 주제에서 **가장 위험한 근거**다.

## 구현 세부사항 대 언어 보장

C 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★ **이 주제는 「구현 정의」와 「미명시」가 나란히 본체**다 —\
크기와 자리는 구현 정의, **구멍의 값은 미명시**. 표준이 주는 것은 뼈대뿐이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | 멤버가 **선언 순서대로** 놓이는 것 · 첫 멤버의 `offsetof` 가 0인 것 · **`sizeof` 가 `_Alignof` 의 배수**인 것 · 끝에도 패딩이 올 수 있는 것 · **`_Alignas` 로 줄일 수 없는 것**(에러) · `memcmp` 반환값의 **부호** | 여섯 순열의 `offsetof` · `_Alignas` 두 에러(**`cc exit=1`**) | — |
| **조건부 표준** | 매크로가 정의될 때만 | **해당 없음** | — | — |
| **구현 정의** | 문서화 의무가 있다 | 각 타입의 **정렬** · **패딩의 양과 자리** · 여섯 순열의 구체적 `sizeof`(16/24) · `_Alignas(16)` 가 크기를 16으로 만드는 것 · **`#pragma pack` 의 효과**(표준 밖 확장이다) | `sizeof`·`offsetof`·`_Alignof` 를 **찍어서** · gcc·clang 두 벌 대조 | 수치는 **찍어야만** 안다. 경고가 없다 |
| **미명시** | 몇 가지 중 하나 | ★★★ **패딩 바이트의 값** · **구조체 대입이 패딩을 복사하는지** · `memcmp` 반환값의 **크기** · **초기자가 패딩을 0으로 만드는지** | 여섯 벌 × 20회 반복 — **gcc `-O2`·clang 은 20/20 이 전부 달랐다** | ★★ **sanitizer 가 원리상 못 잡는다.** 경고 **0건** |
| **UB** | 아무 일이나 | **정렬이 안 맞는 멤버 주소의 역참조**(`#pragma pack` 뒤) — 정본은 [08번 형제](../08-sizeof-alignment-and-offsetof/) | 08 에서 UBSan 이 `misaligned address` 2줄 | `#pragma pack` 쪽은 **경고 0건**(08 실측) |

### 「도구가 못 보는 것」을 층마다

```text
===== 패딩 사고에 경고가 붙나 — grep -c 'warning:' (exit=0) =====
s22a.c   -Wall -Wextra 0건 · +pedantic 0건 · +UBSan 0건
s22b.c   -Wall -Wextra 0건 · +pedantic 0건 · +UBSan 0건
s22e.c   -Wall -Wextra 0건 · +pedantic 0건 · +UBSan 0건
s22f.c   -Wall -Wextra 0건 · +pedantic 0건 · +UBSan 0건
```

| 사실 | `-Wall -Wextra` | `-pedantic` | UBSan | `_Static_assert` |
|---|---|---|---|---|
| 멤버 순서가 나빠 8바이트를 버린 것 | 0건 | 0건 | 못 잡는다 | ★ **잡는다**(크기를 못 박으면) |
| 패딩 바이트에 쓰레기가 남은 것 | **0건** | 0건 | ★★ **못 잡는다** | 못 잡는다 |
| `memcmp` 로 구조체를 비교한 것 | **0건** | 0건 | 못 잡는다 | 못 잡는다 |
| 구조체를 통째로 `fwrite` 한 것 | **0건** | 0건 | 못 잡는다 | 못 잡는다 |
| `#pragma pack` 이 표준이 아닌 것 | 0건 | ★ **0건** | — | — |
| `_Alignas` 로 줄이려 한 것 | — | — | — | ★ **컴파일러가 에러로 막는다** |

- ★★ **패딩 관련 사고는 어느 도구도 보지 못한다.** 「미명시」 층이라 **원리상 잡을 방법이 없다** —\
  잡으려면 「무엇이 옳은 값인가」를 알아야 하는데 **표준이 그것을 정하지 않았다.**
- ★ 네 소스 전부에서 `-Wall -Wextra` **0건** · `+pedantic` **0건** · `+UBSan` **0건**이었다.\
  ★ 특히 **`#pragma pack` 에 `-pedantic` 이 침묵한다** — 표준 밖 확장인데도 그렇다.
- 이 주제에서 쓸 수 있는 유일한 자동 검사는 **`_Static_assert`** 다(정본은 [08번 형제](../08-sizeof-alignment-and-offsetof/)).\
  그것도 **크기와 자리만** 못 박을 수 있고 **값은 못 박는다.**

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 구조체 크기 줄이기 | **멤버 순서 바꾸기**(공짜) | `#pragma pack` |
| 크기 근거 대기 | `offsetof` 로 찍기 | 멤버 크기 더하기 |
| 배치 못 박기 | `_Static_assert`(08) | 주석에 적기 |
| 구조체 비교 | **멤버끼리 비교** | `memcmp` |
| 구조체 저장·전송 | **멤버를 하나씩 직렬화** | `fwrite(&s, sizeof s, …)` |
| 구조체 해시 | 멤버를 하나씩 먹이기 | 바이트 전체를 먹이기 |
| 패딩을 0으로 | `memset` 직후에만 유효 | 「초기자를 썼으니 0이다」 |
| 캐시 라인 맞추기 | `_Alignas(64)` | 수동 더미 멤버 |
| 패킷·파일 매핑 | **`memcpy` 로 바이트 옮기기**(목록의 **50번 주제**) | packed 구조체를 그대로 캐스트 |
| 헤더 + 가변 데이터 | `offsetof` 로 할당(목록의 **26번 주제**) | `sizeof *p` 로 할당 |

판단 규칙 두 줄.

- **구멍을 보는 코드는 전부 틀렸다** — 비교·저장·해시·전송.
- **크기가 중요하면 순서를 바꾸고, 그래도 안 되면 포기한다** — `pack` 은 정렬 보장을 판 값이다.

## 핵심 문장

1. **구조체의 크기는 멤버 크기의 합이 아니다** — 멤버 사이와 끝에 구멍이 있다.
2. **같은 멤버 집합이라도 순서가 크기를 바꾼다** — 실측에서 여섯 순열이 16과 24로 갈렸다.
3. ★ **「큰 것부터」는 충분조건일 뿐**이다. 실제로 손해 보는 것은 **가장 엄한 멤버를 가운데 둔 벌**이다.
4. ★★★ **구멍의 값은 미명시다** — 초기자도, 구조체 대입도 그것을 정해 주지 않는다.
5. ★★ **같은 바이너리를 20번 돌려도 구멍이 매번 달라질 수 있다**(gcc `-O2`·clang 실측).
6. **`memcmp` 는 구멍까지 본다** — 멤버가 전부 같아도 「다르다」고 답한다.
7. **`_Alignas` 는 늘리기만** 되고, 늘리면 **크기가 따라 커진다.**
8. **`#pragma pack(N)` 은 정렬 상한이지 「패딩 제거」가 아니다** — `pack(2)` 의 구멍은 1이었다.
9. ★★ **이 주제의 사고는 어느 도구도 못 잡는다** — 경고·pedantic·UBSan 전부 0건.

## 관련 자료

- [08번 형제 — `sizeof`·정렬·`offsetof`](../08-sizeof-alignment-and-offsetof/) — **그쪽은 재는 도구까지, 여기는 그 수치가 왜 그렇게 나오는가부터.**\
  `_Alignof`·`_Static_assert`·`#pragma pack(1)` 의 UBSan·`__attribute__((packed))` 경고 비대칭은 **08 이 정본**이다.
- [21번 형제 — 구조체 선언·초기화·지정 초기자](../21-struct-declaration-initialization-and-designated-initializers/) — **그쪽은 멤버의 값까지, 여기는 멤버가 아닌 바이트부터.**
- [23번 형제 — `union` 과 타입 펀닝의 경계](../23-union-and-the-boundary-of-type-punning/) — **그쪽은 한 자리를 여러 타입으로 보는 것, 여기는 한 타입 안의 빈자리.**
- [24번 형제 — 비트필드](../24-bit-fields/) — **그쪽은 바이트 안의 비트 배치, 여기는 바이트 단위 배치.**
- [02번 형제 — 기본 타입·크기·고정폭 정수](../02-basic-types-sizes-and-fixed-width-integers/) — 각 타입의 크기·정렬이 왜 고정이 아닌가.
- [05번 형제 — 명시 캐스트와 포인터 변환](../05-explicit-casts-and-pointer-conversions/) — 정렬이 안 맞는 포인터를 만드는 자리.
- 목록의 **26번 주제** — 유연 배열 멤버가 정본.
- 목록의 **50번 주제** — `memcmp`/`memcpy`/`memset` 의 계약이 정본.
- 목록의 **55번 주제** — 엄격한 앨리어싱이 정본.

## 용어 풀이

- **정렬(alignment)** — 객체가 놓일 수 있는 주소의 배수 조건. 예: `_Alignof(int)` 가 4면 `int` 는 4의 배수 주소에서만 시작한다.
- **패딩(padding)** — 정렬을 맞추려고 끼워 넣는 빈 바이트. 예: `char` 뒤에 `int` 가 오면 3바이트가 버려진다.
- **끝 패딩(trailing padding)** — 구조체 끝에 붙는 구멍. 예: `struct { double d; char c; }` 가 9가 아니라 16인 이유.
- **객체 표현(object representation)** — 객체가 차지한 바이트 전부. 예: 멤버 값이 같아도 **객체 표현은 다를 수 있다**(패딩 때문에).
- **미명시(unspecified)** — 표준이 「몇 가지 중 하나」라고만 하고 고르지 않은 것. 예: 패딩 바이트의 값.
- **구현 정의(implementation-defined)** — 구현이 고르되 **문서화할 의무**가 있는 것. 예: `_Alignof(double)` 가 8인 것.
- **순열(permutation)** — 같은 것들을 늘어놓는 순서를 바꾼 것. 예: 멤버 셋이면 여섯 가지.
- **정렬 상한(`#pragma pack(N)`)** — 각 멤버의 정렬 요구를 N 이하로 깎으라는 지시. 예: `pack(2)` 면 `double` 도 2의 배수 자리면 된다.
- **유연 배열 멤버(flexible array member)** — 구조체 끝의 크기 없는 배열(`int a[];`). 예: 헤더와 데이터를 한 번에 할당할 때 쓴다.
- **ABI** — 같은 플랫폼의 컴파일러들이 공유하는 배치·호출 약속. 예: gcc 와 clang 이 같은 `sizeof` 를 낸 이유.

## 더 들어가면

- **왜 컴파일러가 순서를 안 바꿔 주나** — 표준이 **선언 순서를 보장**하기 때문이다.\
  그 보장이 있어야 「공통 초기 시퀀스」([23번 형제](../23-union-and-the-boundary-of-type-punning/))와 구조체 간 캐스트 관용구가 성립한다.\
  ★ 순서를 자동으로 고쳐 주는 언어(Rust 의 기본 표현)는 **그 보장을 포기하는 대신** 크기를 얻는다.
- **패딩이 왜 「불확정」이 아니라 「미명시」인가** — 표준은 두 낱말을 가려 쓴다.\
  값을 **읽어도 UB 가 아니라는 것**이 미명시 쪽이고, 그래서 `memcmp` 가 **에러 없이 틀린 답을 준다.**\
  ★ 「잡아 주지 않는다」가 아니라 **「잡을 것이 없다」** 가 정확한 표현이다.
- **`_Static_assert` 로 어디까지 막을 수 있나** — 크기·자리·정렬은 못 박을 수 있고 **값은 못 박는다.**\
  그래서 「패딩까지 같다」를 컴파일 타임에 보장할 방법이 C 에는 없다.
- **`memcmp` 를 쓰고 싶으면** — `memset` 으로 만들고 **그 뒤로 대입을 한 번도 하지 않는** 규율이 필요한데,\
  그 규율을 **컴파일러가 검사해 주지 않는다.** 실측에서 대입 한 번이 되돌렸다.
- **다른 플랫폼에서는** — `_Alignof(double)` 가 4인 32비트 ABI 도 있다. 그러면 **여섯 순열의 크기가 전부 달라진다.**\
  ★ 이 문서의 16·24 는 **x86-64 Linux 의 수치**이지 C 의 수치가 아니다.
