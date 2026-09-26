# c/syntax/22 — 구조체 패딩·정렬: 「**같은 멤버라도 순서가 크기를 바꾸고, 구멍의 값은 아무도 약속하지 않는다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 수치·바이트 격자·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s22a.c`·`s22b.c`·`s22b2.c`·`s22d.c`·`s22d2.c`·`s22e.c`·`s22f.c` 다.\
> ★★ **패딩 값이 걸린 블록은 여섯 벌(gcc·clang × `-O0`/`-O1`/`-O2`)을 돌리고 한 벌을 20번씩 반복했다.**\
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★★ **패딩 바이트의 실제 값** — gcc `-O2`·clang 은 **20번 실행이 전부 달랐다** | ★★ **`sizeof`·`offsetof`·`_Alignof`** — 여섯 순열 전부 |
> | `memcmp` 반환값의 **크기**(이 머신에서는 30/30 이 `170` 이었지만 근거가 못 된다) | ★★ **`memcmp` 반환값의 부호**가 「0이냐 아니냐」로 갈리는 것 |
> | 주소·`%p`·스택 자리 | ★★ **gcc `-O0`·`-O1` 의 격자**(20/20 동일 — 그래서 정본 격자로 실었다) |
> | ★ `-O2`/clang 블록의 구멍 값 — **대조할 것은 숫자가 아니라 「구멍만 흔들리고 멤버 자리는 안 흔들린다」는 성질**이다 | ★★ **진단 본문**(`_Alignas` 두 에러) · **종료 코드**(`cc exit=0`/`1`) · **경고 건수** |
> | | ★ **`#pragma pack` 네 벌의 크기·`offsetof`** — gcc·clang 이 한 글자도 같았다 |

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 멤버 셋을 여섯 가지 순서로 — **16 과 24 두 종류로 갈리고, 넷이 16** ★★★

**출력**

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

**왜 그런가**

```text
   멤버 크기의 합 = char 1 + int 4 + double 8 = 13
   ('.' 이 구멍)

   CID   c...iiiidddddddd            16     구멍  3
   CDI   c.......ddddddddiiii....    24     구멍 11   ★
   ICD   iiiic...dddddddd            16     구멍  3
   IDC   iiii....ddddddddc.......    24     구멍 11   ★
   DCI   ddddddddc...iiii            16     구멍  3
   DIC   ddddddddiiiic...            16     구멍  3
```

- **여섯 벌의 멤버 집합은 한 글자도 다르지 않다.** 순서만 다르다.
- 크기는 **16 아니면 24** 두 종류였고, **여섯 중 넷이 16** 이다. 차이는 **8바이트**다.
- ★★ **「큰 것부터」는 충분조건일 뿐**이다 — `DCI`·`DIC` 는 큰 것부터라 16이지만\
  `CID`·`ICD` 는 **작은 것부터인데도 16** 이다.
- ★★★ 손해 본 두 벌의 공통점은 하나다 — **`double` 이 가운데 있다.**\
  `double` 앞에서 8의 배수로 밀어 올리느라 구멍이 생기고, 뒤에 남은 `int` 4바이트 때문에 **끝 구멍이 또** 붙는다.
- `_Alignof` 는 **여섯 벌 전부 8** 이다. 규칙 ②가 「가장 엄한 멤버의 정렬」이라고 했고,\
  여섯 벌 모두 `double` 을 갖고 있기 때문이다. 정렬이 같으니 **크기는 8의 배수**여야 하고, 그래서 16 아니면 24다.
- 외울 것은 「큰 것부터」가 아니라 ★ **「가장 엄한 멤버를 가운데 두지 마라」** 다.

| 순서 | `sizeof` | 구멍 | 가장 엄한 멤버(`double`)의 자리 |
|---|---|---|---|
| `CID` · `ICD` | **16** | 3 | 끝 |
| `DCI` · `DIC` | **16** | 3 | 처음 |
| `CDI` · `IDC` | ★ **24** | 11 | ★ **가운데** |

### 2. 같은 `{ 1, 2, 3 }` 을 네 방법으로 — **구멍이 `00` 인 것은 `memset` 한 벌뿐** ★★★ 본체

**출력**

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

**왜 그런가**

```text
   struct S { char c; int i; char e; };     sizeof = 12

   자리  0     1   2   3     4   5   6   7     8     9  10  11
       +-----+-------------+-----------------+-----+-------------+
       |  c  |   구멍 3    |        i        |  e  |   구멍 3    |
       +-----+-------------+-----------------+-----+-------------+

   a  초기자      01  [aa aa aa]  02 00 00 00  03  [aa aa aa]
   b  멤버 대입   01  [aa aa aa]  02 00 00 00  03  [aa aa aa]
   c  memset 뒤   01  [00 00 00]  02 00 00 00  03  [00 00 00]   <- 유일하게 예측 가능
   d  d = a       01  [aa aa aa]  02 00 00 00  03  [aa aa aa]   <- 구멍까지 복사됐다

   멤버끼리 :  1  1  1     (넷 다 같다)
   memcmp   :  0  +  0     (a,c 만 「다르다」)
```

- **구멍이 `00` 으로 나온 것은 `c` 한 벌뿐**이다. `memset` 이 **멤버가 아닌 바이트까지** 0으로 만들었기 때문이다.
- ★★★ **`a` 는 초기자를 썼는데도 구멍이 `0xAA` 였다.**\
  「`= { … }` 로 안 적은 멤버는 0이 된다」는 **멤버에만** 걸리는 규칙이고([21번 형제](../21-struct-declaration-initialization-and-designated-initializers/)가 정본),\
  **구멍은 멤버가 아니므로 그 규칙 밖**이다. 표준은 여기에 아무 값도 약속하지 않았다.
- ★★ **`d = a` 는 구멍까지 그대로 복사했다.** 구조체 대입이 패딩을 복사하는지도 **미명시**다 —\
  이 벌에서는 복사했지만, 다른 벌에서는 안 할 수 있다(4번 아래 clang 실측).
- ★★ 「멤버끼리」는 `1 1 1` 인데 「`memcmp`」는 `a,c` 만 다르다고 답했다.\
  **`memcmp` 는 멤버가 아니라 바이트를 보기 때문**이다. 틀린 쪽은 `memcmp` 가 아니라 **그것을 쓴 코드**다.
- ★ 프로그램이 `memcmp` 의 **부호만** 찍는 이유는 **크기가 미명시**이기 때문이다(4번).\
  크기를 찍으면 그 숫자가 「돌려 본 결과」로 문서에 박히고, **다음 실행에서 달라질 수 있다.**

| 만드는 방법 | 멤버 | 구멍 | 예측 가능한가 |
|---|---|---|---|
| `a` 초기자 `= { … }` | `1 2 3` | ★ 쓰레기 | **아니다** |
| `b` 멤버 대입만 | `1 2 3` | 쓰레기 | 아니다 |
| `c` `memset` 뒤 대입 | `1 2 3` | **`00`** | ★ **그렇다**(그 순간만) |
| `d` 구조체 대입 `d = a` | `1 2 3` | `a` 를 따라간다 | ★ **미명시** |

### 3. 몇 벌·몇 번 — **gcc `-O0`·`-O1` 만 20/20 같고 나머지 넷은 20/20 다르다** ★★★

**출력**

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

```text
===== 같은 바이너리를 20번씩 돌려 패딩 격자 네 줄이 몇 가지나 나오나 (exit=0) =====
gcc   -O0 : 20번 중 서로 다른 격자  1가지
gcc   -O1 : 20번 중 서로 다른 격자  1가지
gcc   -O2 : 20번 중 서로 다른 격자 20가지
clang -O0 : 20번 중 서로 다른 격자 20가지
clang -O1 : 20번 중 서로 다른 격자 20가지
clang -O2 : 20번 중 서로 다른 격자 20가지
```

**왜 그런가**

```text
   한 벌만 돌렸을 때 적게 되는 문장          실제로 여섯 벌을 돌리면

   「패딩은 0xAA 로 남는다」                 gcc -O0 에서만 그렇다
   「초기자를 쓰면 앞 구멍이 0 이다」          clang -O0 에서만 그렇다
   「memcmp(a,b) 는 0 이다」                 clang -O0 은 '-' 를 냈다
   ------------------------------------      ------------------------------
   전부 ★ 한 벌의 결과를 규칙으로 적은 것      ★ 틀린 구현은 하나도 없다
```

- **gcc `-O2`** 는 `a` 의 앞 구멍이 `aa` 가 아니고, `b` 의 꼬리 구멍은 **`00`** 이 됐다.\
  같은 소스·같은 컴파일러인데 **`-O` 하나로 갈린다.**
- **clang `-O0`** 은 또 다르다 — `a` 의 앞 구멍은 `00` 인데 **꼬리 구멍은 쓰레기**이고,\
  ★ **`memcmp(a,b)` 의 부호가 `-`** 다(gcc 는 `0`).
- ★★ 20번씩 돌려 세 보니 **gcc `-O0`·`-O1` 은 격자가 1가지**, **gcc `-O2` 와 clang 세 벌은 20가지**였다 —\
  **같은 바이너리인데 매 실행이 다르다.**
- ★ 그래서 **대조할 것이 부류마다 다르다.**
  - gcc `-O0`/`-O1` → **격자 그 자체**를 대조한다(그래서 2번의 정본 격자로 실었다).
  - gcc `-O2`·clang → ★ **「구멍 자리만 흔들리고 멤버 자리(`01`·`02 00 00 00`·`03`)는 절대 안 흔들린다」는 성질**을 대조한다.
- ★★ 「세 번 돌려 보고 같았다」가 위험한 이유가 여기 있다 — **gcc `-O0` 을 세 번 돌리면 세 번 다 같다.**\
  세 번이 아니라 **벌을 바꿔야** 갈린다. 반복 횟수와 **벌 수는 다른 축**이다.

| 무엇을 바꿨나 | 격자가 갈리나 |
|---|---|
| 같은 바이너리를 여러 번 | gcc `-O0`/`-O1` **안 갈린다** · 나머지 넷 **매번 갈린다** |
| `-O0` → `-O2` | ★ **갈린다** |
| gcc → clang | ★ **갈린다** |
| 멤버 값 | 안 갈린다(`01`·`02 00 00 00`·`03` 고정) |

### 4. `memcmp` — **바이트를 비교하고, 부호만 규정이다** ★★

**출력**

```c
/* s22b2.c */
#include <stdio.h>
#include <string.h>

struct S { char c; int i; char e; };

static void dirty(void) {
    volatile unsigned char buf[64];
    for (int k = 0; k < 64; k++) buf[k] = 0xAA;
    if (buf[0] != 0xAA) printf("!");
}

static struct S make(int how) {
    volatile unsigned char guard[8] = {0};
    struct S v;
    if (how == 0) { struct S t = { .c = 1, .i = 2, .e = 3 }; v = t; }
    else { memset(&v, 0, sizeof v); v.c = 1; v.i = 2; v.e = 3; }
    (void)guard;
    return v;
}

int main(void) {                      /* memcmp 의 「크기」만 찍는다 */
    dirty(); struct S a = make(0);
    dirty(); struct S c = make(1);
    printf("%d\n", memcmp(&a, &c, sizeof a));
    return 0;
}
```

```text
===== 같은 바이너리를 30번 돌려 memcmp 의 반환값 크기를 센다 (exit=0) =====
30번 : 170
```

**왜 그런가**

- `memcmp` 는 **멤버가 아니라 바이트**를 본다. 구조체에는 **멤버가 아닌 바이트**가 있고(패딩),\
  그 값이 미명시이므로 **멤버가 전부 같아도 「다르다」가 나올 수 있다.**
- ★ 표준이 정한 것은 **부호**뿐이다 — 「처음으로 다른 바이트에서 큰 쪽이 양수」.\
  **크기는 미명시**다. 이 머신에서 **30번 전부 `170`**(`0xAA`)이 나왔지만 그것은 **glibc 가 고른 한 경로의 결과**다.
- ★★ 「30번 돌려 같았으니 믿어도 된다」는 **이 주제에서 정확히 반대의 결론**을 낸다 —\
  3번에서 보았듯 **벌을 바꾸면 갈리는 축**이고, 30번은 그 축을 건드리지 않는다.
- **옳은 방법은 멤버끼리 비교**하는 것이다.\
  ★ `memset` 은 답이 못 된다 — **그 뒤의 대입 한 번이 되돌릴 수 있고**(2번의 `d`),\
  되돌렸는지를 **컴파일러가 검사해 주지 않는다.**
- **`fwrite(&s, sizeof s, …)`·해시·소켓 전송이 같은 집안**이다. 전부 **구멍을 읽어 판단·전송에 쓴다.**\
  구멍의 값은 **스택에 있던 다른 데이터**일 수 있으므로 정보 누출이 되기도 한다.

| 무엇 | 표준이 정했나 | 이 머신의 관찰 |
|---|---|---|
| `memcmp` 반환값의 **부호** | ★ **정했다** | `0` / `+` / `-` 가 벌마다 갈렸다 |
| `memcmp` 반환값의 **크기** | **미명시** | 30/30 이 `170` — ★ **근거로 쓰지 않는다** |
| 비교 대상 | ★ **바이트 전부**(패딩 포함) | — |

### 5. 멤버 하나에 `_Alignas` — **`char` 하나짜리가 16바이트가 된다** ★★

**출력**

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

**왜 그런가**

```text
   struct A { char c; }                        1
   +-+
   |c|
   +-+

   struct B { _Alignas(16) char c; }           16    ★ 멤버는 1바이트인데
   +-+-----------------------------+
   |c| . . . . . . . . . . . . . . |  구멍 15
   +-+-----------------------------+

   struct D { char c; int i; }                 8     (대조군)
   +-+---+----+
   |c|...| i  |  구멍 3
   +-+---+----+

   struct C { char c; _Alignas(8) int i; }     16
   +-+-------+----+----+
   |c|.......| i  |....|  구멍 7 + 끝 구멍 4
   +-+-------+----+----+
    0        8   12
```

- **`_Alignas(16)` 를 멤버 하나에 걸면 구조체 전체의 정렬이 16** 이 된다(규칙 ②),\
  그리고 **`sizeof` 는 그 배수**여야 하므로(규칙 ③) **1바이트짜리가 16바이트**가 된다.
- `struct C` 와 `struct D` 는 **멤버 집합이 같은데 8 과 16** 으로 갈렸다.\
  ★ `offsetof(struct C, i)` 는 **4가 아니라 8** 이다 — 지시한 정렬 8을 지키느라 구멍이 **3에서 7로** 늘었고,\
  거기에 **끝 구멍 4**가 붙어 16이 됐다.
- ★★ **배열에도 따라온다.** `(char *)&arr[1] - (char *)&arr[0]` 이 **16** 이고 `&arr[0]` 도 **16의 배수**였다.\
  원소 하나하나가 정렬을 지켜야 하니 당연한 결과지만, **메모리 비용이 배열 크기만큼 곱해진다**는 뜻이다.
- **얻는 것** — 캐시 라인·SIMD·DMA 가 요구하는 주소를 **언어 안에서** 보장받는다.
- **잃는 것** — 메모리다. `_Alignas(64)` 짜리 100만 개면 64MB 다.

### 6. `_Alignas` 가 거절하는 둘 — **에러 두 건, `cc exit=1`** ★

**출력**

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

**왜 그런가**

- **경고가 아니라 에러**다. **`cc exit=1`** — 컴파일이 멈춘다.\
  ★ 「경고 0건」과 「에러로 멈췄다」를 가르려면 **종료 코드를 같이 봐야** 한다.
- 사유가 둘이다.
  - **줄이려 한 것** — `_Alignas(1) int` 는 `int` 의 기본 정렬 4보다 작다. **`_Alignas` 는 늘리기만 된다.**
  - **2의 거듭제곱이 아닌 것** — `_Alignas(3)` 은 값 자체가 안 된다.
- 정렬을 **줄이고 싶으면** C 에는 표준 수단이 없다. `#pragma pack` 이 그 자리를 메우지만 **표준이 아니다**(7번).
- ★ 이 주제에서 **컴파일러가 막아 주는 사고는 이것뿐**이다. 나머지(순서·패딩 값·`memcmp`·`fwrite`)는 **전부 조용히 통과**한다(9번).

| 무엇 | 결과 |
|---|---|
| `_Alignas` 로 **늘리기** | 된다 · 크기가 따라 커진다 |
| `_Alignas` 로 **줄이기** | ★ **error** |
| `_Alignas` 에 3·5·6 | ★ **error**(2의 거듭제곱만) |
| `#pragma pack` 으로 줄이기 | 된다 · ★ **표준이 아니다** |

### 7. `pack(2)`·`pack(4)` — **깎는 것이지 없애는 것이 아니다** ★★

**출력**

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

**왜 그런가**

```text
   같은 { char c; int i; double d; } 를 네 가지 pack 으로  ('.' 이 구멍)

   기본     c...iiiidddddddd            16   _Alignof 8   구멍 3
   pack(1)  ciiiidddddddd               13   _Alignof 1   구멍 0
   pack(2)  c.iiiidddddddd              14   _Alignof 2   구멍 1   ★ 0 이 아니다
   pack(4)  c...iiiidddddddd            16   _Alignof 4   구멍 3   ★ 기본과 같다
```

- ★★★ **`pack(2)` 의 구멍이 1** 이다. `pack` 은 **「패딩을 없애라」가 아니라 「각 멤버의 정렬 요구를 N 이하로 깎아라」** 이기 때문에,\
  `int` 의 정렬이 2로 깎여 **홀수 자리 1에서 시작하지 못하고 2로** 밀렸다.
- ★★ **`pack(4)` 는 기본과 크기가 같다.** `char` 1 과 `int` 4 는 이미 4 이하라 안 깎이고,\
  `double` 만 8→4 로 깎였는데 **그 자리가 마침 8의 배수**여서 결과가 안 바뀌었다.\
  ★ 「`pack` 을 걸었는데 크기가 그대로」는 **버그가 아니라 정의대로**다.
- **`pack(1)` 배열**의 세 원소에서 `&arr[k].i % 4` 가 **`1 · 2 · 3`** 으로 돌았다 — **어느 원소에서도 0이 아니다.**\
  원소가 13바이트씩 밀리기 때문이다. ★ 값이 0으로 나오는 원소가 있더라도 그것은 **우연**이고,\
  그 주소를 역참조하면 [08번 형제](../08-sizeof-alignment-and-offsetof/)가 UBSan 으로 잡은 그 UB 다.
- ★★ **clang 의 출력이 gcc 와 한 글자도 같았다.** 그런데 이것은 **보장이 아니라 관찰**이다 —\
  `#pragma pack` 은 **어느 표준에도 없고**, 둘이 같은 답을 낸 것은 **같은 플랫폼 ABI 를 따르기 때문**이다.\
  아키텍처나 컴파일러가 바뀌면 갈릴 수 있다.

| `pack(N)` | `sizeof` | `_Alignof` | 구멍 | 무엇이 깎였나 |
|---|---|---|---|---|
| 기본 | 16 | 8 | 3 | — |
| `1` | **13** | 1 | 0 | `int` 4→1 · `double` 8→1 |
| `2` | **14** | 2 | ★ **1** | `int` 4→2 · `double` 8→2 |
| `4` | **16** | 4 | 3 | `double` 8→4 뿐 — ★ 결과가 안 바뀌었다 |

### 8. 유연 배열 멤버 — **`sizeof` 4 · `offsetof(a)` 4, 그러나 우연이다** ★

**출력**

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

**왜 그런가**

```text
   struct Bb { char n; int a[]; };

   sizeof = 4                       offsetof(a) = 4
   +----+----+----+----+            +----+----+----+----+---------+---------+
   | n  |  .    .    . |            | n  |  .    .    . | a[0](4) | a[1](4) | …
   +----+----+----+----+            +----+----+----+----+---------+---------+
     0    1    2    3                 0    1    2    3    4         8
          ^^^^^^^^^^^^
          ★ 헤더 1바이트 뒤 3바이트가 패딩

   malloc(offsetof(Bb, a) + n * sizeof p->a[0])   <- ★ 옳은 형태
   malloc(sizeof(*p)      + n * sizeof p->a[0])   <- 여기서는 우연히 같았다
```

- 멤버는 `char` 하나뿐인데 `sizeof` 가 **1이 아니라 4** 다.\
  `int` 배열이 **4의 배수 자리**에서 시작해야 하므로 헤더 뒤에 **3바이트 구멍**이 생기고,\
  규칙 ③이 `sizeof` 를 **정렬(4)의 배수**로 만든다.
- 두 할당 식이 **둘 다 24바이트**를 냈다. ★★ **같은 값이 나왔다고 같은 질문에 답한 것이 아니다.**
  - `offsetof(Bb, a)` — **「헤더가 어디서 끝나는가」**. 언제나 옳다.
  - `sizeof *p` — **「구조체 하나가 몇 바이트인가」**. **끝 패딩을 센다.**
  - 이 구조체에서는 둘이 마침 같았을 뿐이고, **끝 패딩이 헤더 뒤 패딩보다 큰 구조체에서는 갈린다.**
- `struct Ba`(`int` 헤더)와 `struct Bc`(`double` 헤더)도 둘 다 같은 값이었지만, **그것이 규칙은 아니다.**
- 정본은 [목록의 **26번 주제**](../26-flexible-array-members/)다. 여기서는 **패딩이 헤더 뒤에도 생긴다**는 사실만 본다.

### 9. 왜 경고가 없나 — **잡아 주지 않는 것이 아니라 잡을 것이 없다** ★★★

**출력**

```text
===== 패딩 사고에 경고가 붙나 — grep -c 'warning:' (exit=0) =====
s22a.c   -Wall -Wextra 0건 · +pedantic 0건 · +UBSan 0건
s22b.c   -Wall -Wextra 0건 · +pedantic 0건 · +UBSan 0건
s22e.c   -Wall -Wextra 0건 · +pedantic 0건 · +UBSan 0건
s22f.c   -Wall -Wextra 0건 · +pedantic 0건 · +UBSan 0건
```

**왜 그런가**

| 사실 | `-Wall -Wextra` | `-pedantic` | UBSan | `_Static_assert` |
|---|---|---|---|---|
| 멤버 순서가 나빠 8바이트를 버린 것 | 0건 | 0건 | 못 잡는다 | ★ **잡는다**(크기를 못 박으면) |
| 구멍에 쓰레기가 남은 것 | **0건** | 0건 | ★★ **못 잡는다** | 못 잡는다 |
| `memcmp` 로 구조체를 비교한 것 | **0건** | 0건 | 못 잡는다 | 못 잡는다 |
| 구조체를 통째로 `fwrite` 한 것 | **0건** | 0건 | 못 잡는다 | 못 잡는다 |
| `#pragma pack` 이 표준이 아닌 것 | 0건 | ★ **0건** | — | — |
| `_Alignas` 로 줄이려 한 것 | — | — | — | ★ **error 로 막힌다** |

- 네 소스 전부 `-Wall -Wextra` **0건** · `+pedantic` **0건** · `+UBSan` **0건**이었다.
- ★★ **sanitizer 가 원리상 못 잡는다.** UBSan 은 「정의되지 않은 일이 일어났다」를 잡는데,\
  **패딩을 읽는 것은 정의되지 않은 일이 아니다** — **미명시**일 뿐이다.\
  잡으려면 「무엇이 옳은 값인가」를 알아야 하는데 **표준이 그것을 정하지 않았다.**\
  ★ 그래서 「잡아 주지 않는다」가 아니라 **「잡을 것이 없다」** 가 정확한 표현이다.
- ★ **`#pragma pack` 에 `-pedantic` 이 침묵**한다. `#pragma` 는 **구현이 알아보지 못하면 무시하라**는 문법이라\
  **표준 밖 확장이어도 「표준 위반」이 아니다.** `-pedantic` 이 잡는 것은 위반이지 확장이 아니다.
- 이 주제에서 쓸 수 있는 유일한 자동 검사는 **`_Static_assert`** 다(정본은 [08번 형제](../08-sizeof-alignment-and-offsetof/)).\
  ★ 그것도 **크기·자리·정렬만** 못 박을 수 있고 **구멍의 값은 못 박는다.**

### 10. 다섯 층 — **「구현 정의」와 「미명시」가 나란히 본체, UB 는 08 쪽에 있다** ★★★

**출력** — 층 표는 [2-summary.md](2-summary.md)의 「구현 세부사항 대 언어 보장」이 정본이다. 요약하면 이렇다.

```text
   표준        멤버는 선언 순서 · 첫 멤버 offset 0 · sizeof 는 _Alignof 의 배수
               _Alignas 로 줄일 수 없다 · memcmp 반환값의 부호
   조건부 표준  ★ 해당 없음
   구현 정의   ★★ 각 타입의 정렬 · 패딩의 양과 자리 · 16/24 라는 수치 · #pragma pack 의 효과
   미명시      ★★★ 패딩 바이트의 값 · 구조체 대입이 패딩을 복사하는지 · memcmp 반환값의 크기
   UB          정렬이 안 맞는 멤버 주소의 역참조 (정본은 08)
```

**왜 그런가**

- **비어 있는 칸은 「조건부 표준」** 이다. 이 주제에는 `__STDC_…` 류 조건부 기능이 없다.
- ★★ **가장 두꺼운 칸은 「미명시」** 다 — 이 편의 본체가 거기 있고, **도구가 하나도 못 보는 칸**이기도 하다.\
  **두 번째는 「구현 정의」** 다 — 문서의 수치(16·24·13·14)가 전부 거기 있다.
- ★ **UB 칸은 얇다.** 이 주제 자체에는 UB 가 거의 없고, 있는 것(정렬 위반 역참조)은\
  `#pragma pack` 을 쓴 뒤에야 생기며 **정본이 [08번 형제](../08-sizeof-alignment-and-offsetof/)** 다.
- **구현 정의와 미명시를 가르는 기준 한 줄** — ★ **문서화 의무가 있나 없나**.\
  `_Alignof(double)` 가 8인 것은 컴파일러가 **문서에 적어야 하는 것**이고,\
  패딩 바이트의 값은 **아무도 적을 의무가 없다**(그래서 같은 프로그램의 두 실행에서 달라도 된다).
- ★★ 「gcc 와 clang 이 같은 답을 냈다」는 **어느 칸의 근거도 되지 못한다.**\
  구현 정의 칸에서는 **두 구현이 우연히 같은 ABI 를 따른 관찰**일 뿐이고,\
  미명시 칸에서는 3번이 보여 준 대로 **같지도 않았다.**

### 11. 08 편과의 경계 — **08 은 도구, 22 는 규칙** ★★

**출력** — 경계는 이렇게 갈린다.

```text
   08 (도구)                              22 (규칙)
   +----------------------------------+  +----------------------------------+
   | sizeof · _Alignof · offsetof     |  | 왜 그 수치가 나오나 (배치 규칙)    |
   | _Static_assert 로 못 박기         |  | ★ 순열 전수 — 순서가 크기를 바꾼다 |
   | #pragma pack(1) + UBSan          |  | ★★ 구멍의 값이 미명시인 것        |
   | __attribute__((packed)) 경고 비대칭|  | pack(N) 이 「상한」이라는 것       |
   | sizeof 의 세 얼굴 · VLA 예외       |  | _Alignas 가 크기를 키우는 것       |
   +----------------------------------+  +----------------------------------+
```

**왜 그런가**

- **도구 넷**(`sizeof`·`_Alignof`·`offsetof`·`_Static_assert`)은 **[08번 형제](../08-sizeof-alignment-and-offsetof/)가 정본**이다.\
  `#pragma pack(1)` 의 **UBSan 리포트**와 `__attribute__((packed))` 의 **경고 비대칭**도 그쪽이다.
- ★ **이 주제가 끝까지 책임지는 것 셋**.
  - **같은 멤버 집합의 순서가 크기를 바꾸는 것**(순열 전수와 그 공통점).
  - ★★ **패딩 바이트의 값이 미명시인 것**(여섯 벌 × 20회로 보인 것).
  - **`pack(N)` 이 「정렬 상한」이고 `_Alignas` 가 「늘리기 전용」이라는 것**.
- 이웃의 정본.

| 무엇 | 정본 |
|---|---|
| `sizeof`·`_Alignof`·`offsetof`·`_Static_assert` | [08번 형제](../08-sizeof-alignment-and-offsetof/) |
| 구조체 선언·초기화·지정 초기자 | [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/) |
| `union` 의 크기·정렬·공통 초기 시퀀스 | [23번 형제](../23-union-and-the-boundary-of-type-punning/) |
| 바이트 안의 **비트** 배치 | [24번 형제](../24-bit-fields/) |
| 유연 배열 멤버 | [목록의 **26번 주제**](../26-flexible-array-members/) |
| `memcmp`/`memcpy`/`memset` 의 계약 | 목록의 **50번 주제** |
| 엄격한 앨리어싱 | 목록의 **55번 주제** |

- ★ 구조체의 **초기화 규칙**(지정 초기자로 안 적은 **멤버**가 0이 되는 것)은 [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/)가 정본이고,\
  **그 규칙이 구멍에는 안 걸린다**는 것이 이 주제의 2번 답이다.

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 컴파일러·플래그로 돌렸나 |
|---|---|---|
| `s22a.c` (22-a) | 여섯 순열의 `sizeof` **16/24/16/24/16/16** · `_Alignof` **전부 8** · `offsetof` 로 구멍 자리 | gcc `-std=c17 -Wall -Wextra -pedantic` 1벌(실행 포함) |
| `s22b.c` (22-b) | 같은 `{1,2,3}` 네 방식의 **바이트 격자** · 멤버끼리 `1 1 1` · **`memcmp` 는 `a,c` 만 다르다** | ★ gcc `-O0`·`-O2`·clang `-O0` **세 벌을 문서에 싣고**, `-O1` 포함 **여섯 벌**을 **20번씩** 반복 |
| `s22b2.c` (22-c) | `memcmp` 반환값의 **크기** — 30번 전부 `170` | gcc 1벌 · ★ **30회 반복** |
| `s22d.c` (22-d) | `_Alignas(16)` 로 `sizeof` **16** · `struct C` 가 8이 아니라 **16** · `offsetof(i)`=**8** · 배열 간격 **16** | gcc 1벌(실행 포함) |
| `s22d2.c` (22-e) | `_Alignas` 두 에러 · **`cc exit=1`** | gcc 1벌 · ★ **실행 없음**(컴파일이 멈춘다) |
| `s22e.c` (22-f) | `pack` 네 벌의 `sizeof` **16/13/14/16** · ★ `pack(2)` 의 구멍 **1** · `pack(1)` 배열의 `% 4` 가 **1·2·3** | gcc 1벌 · clang 1벌 — ★ **한 글자도 같았다** |
| `s22f.c` (22-g) | `Bb` 의 `sizeof`=`offsetof(a)`=**4** · 할당 **24바이트** · 두 식이 **우연히 같았다** | gcc 1벌(실행 포함) |
| (경고 세기) | 네 소스 전부 `-Wall -Wextra` **0건** · `+pedantic` **0건** · `+UBSan` **0건** | gcc 3벌 × 4소스 · `grep -c 'warning:'` |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3 · glibc)에서만** 그렇다.

- **여섯 순열이 16/24 로 갈린 것** — ★ **구현 정의**다. `_Alignof(double)` 가 4인 ABI 에서는 **전부 달라진다.**
- **`_Alignof` 가 전부 8인 것 · `_Alignof(int)`=4** — 구현 정의다.
- **`pack(1)`=13 · `pack(2)`=14 · `pack(4)`=16** — ★★ `#pragma pack` **자체가 표준 밖**이다.\
  gcc 와 clang 이 같은 답을 낸 것은 **관찰이지 보장이 아니다.**
- **패딩 바이트의 실제 값(`aa`·`00`·쓰레기)** — ★★★ **미명시**다. **여섯 벌이 전부 달랐고 네 벌은 매 실행 달랐다.**
- **`memcmp` 가 `170` 을 돌려준 것** — ★ **미명시**다. **부호만** 근거로 쓴다.
- **구조체 대입이 패딩을 복사한 것** — ★ **미명시**다. clang `-O1` 에서는 `memset` 으로 0이 된 구멍이 **되살아났다.**
- **`Bb` 의 `sizeof` 와 `offsetof(a)` 가 같은 것** — 이 구조체의 **우연**이다.

**배치 규칙 세 줄과 「패딩 값은 미명시」 자체는 구현 의존이 아니다.**\
멤버가 선언 순서대로 놓이는 것 · `sizeof` 가 `_Alignof` 의 배수인 것 · `_Alignas` 로 줄일 수 없는 것은\
**어느 C 구현에서도 같다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **32비트 ABI**(`-m32`)에서의 여섯 순열 · **다른 아키텍처**(ARM·RISC-V) ·\
  **`-fpack-struct`** 전역 플래그 · **구조체를 `fwrite` 로 파일에 쓴 뒤 다른 벌로 읽는 실험** ·\
  **`_Static_assert` 로 패딩 크기를 못 박는 관용구**(08 이 크기·자리는 다뤘다) ·\
  **멤버 넷 이상의 순열**(24가지) — 셋으로도 결론이 섰다.
- ★ **못 잰 것** — ★★ **「구조체 대입이 패딩을 복사하는가」의 일반 답.**\
  실측에서 gcc `-O0` 은 복사했고 clang `-O1` 은 **`memset` 한 구멍을 되살렸다.**\
  이것은 **「복사한다/안 한다」가 아니라 「매번 다르다」가 관찰의 전부**이고,\
  **어떤 조건에서 어느 쪽인지는 컴파일러 내부 결정이라 밖에서 잴 수가 없다.**\
  ★ 그래서 **쪼개서 잰 조각들**로 적었다 — 여섯 벌의 격자와 20회 반복 횟수.
- ★ **블록 없이 산문으로만 적은 것** — 「clang `-O1` 에서 `memset` 한 구멍이 되살아났다」.\
  **그 벌은 20/20 이 매번 다른 부류**라 블록으로 실으면 **재대조 때마다 불일치**가 난다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **패딩 값이 걸린 세 블록 전부** — **미명시 칸이라 컴파일러가 올라가면 언제든 바뀐다.**\
  ★ 바뀌어도 **문서를 고칠 필요가 없게** 「흔들리는 칸」 표에 미리 선언해 두었다.
- ★★ **`b22b_stab` 의 「1가지 / 20가지」** — gcc `-O1` 이 어느 쪽으로 갈지는 **최적화 구현에 달렸다.**
- ★ **`#pragma pack` 네 벌의 수치** — 표준 밖이라 **컴파일러가 언제든 바꿀 수 있다.** gcc·clang 양쪽을 다시 찍는다.
- ★ **`_Alignas` 두 에러의 문구** — 진단 문구는 판이 올라가면 바뀐다. **`cc exit=1` 은 안 바뀐다.**
- **여섯 순열의 `sizeof` 와 배치 규칙 세 줄은 다시 돌릴 필요가 없다** — 같은 ABI 인 한 바뀌지 않는다.
