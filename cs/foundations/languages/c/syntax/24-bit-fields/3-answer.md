# c/syntax/24 — 비트필드: 「**폭은 내가 정하고 자리는 컴파일러가 정한다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s24a.c`\~`s24f.c` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
> ★★ **배치가 걸린 문항(3·4)은 「컴파일러 2 × 최적화 3」 여섯 벌**을 돌렸다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★ **초기화 안 한 미사용 비트에 무엇이 들어 있었나** — 스택에 달렸고 **프로그램마다 다르다** | ★★★ **바이트 격자**(`d3 f8 ff ff` · `d3 08 00 00` · `D3 78 00 00` · `D3 08 00 00`) |
> | 스택 주소 · 컴파일러 진단의 줄 번호(소스를 고치면 밀린다) | ★★★ **빌드별 갈림 자체**(gcc `-O0` ↔ `-O1` 에서 갈린다는 사실) — **여섯 벌 재현됨** |
> | — | ★★ **`sizeof`·`_Alignof`·비트 자리**(`0xAD` = `10101101`) |
> | — | ★★ **멤버 값** — 여섯 벌 전부 같았다 |
> | — | ★★ **진단 본문·플래그 이름·종료 코드**(`cc exit=0` \| `cc exit=1`) |
>
> ★ **같은 바이너리를 15번 돌린 격자는 한 가지**였다 — 흔들린 것은 **실행이 아니라 빌드**다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 플래그 다섯 개를 비트로 선언하고 크기와 바이트를 재면 — **`sizeof` 4 대 5 · 첫 바이트 `0xAD`** ★★★

**출력**

```c
/* s24a.c */
#include <stdio.h>
#include <string.h>

struct Flags {                     /* 여덟 개의 플래그를 비트로 */
    unsigned ready : 1;
    unsigned dirty : 1;
    unsigned locked: 1;
    unsigned kind  : 3;            /* 0~7 */
    unsigned prio  : 2;            /* 0~3 */
};
struct Plain { unsigned char ready, dirty, locked, kind, prio; };

int main(void) {
    printf("struct Flags sizeof=%zu _Alignof=%zu   (비트 합 = 1+1+1+3+2 = 8)\n",
           sizeof(struct Flags), _Alignof(struct Flags));
    printf("struct Plain sizeof=%zu _Alignof=%zu\n",
           sizeof(struct Plain), _Alignof(struct Plain));

    struct Flags f;
    memset(&f, 0, sizeof f);
    f.ready = 1; f.dirty = 0; f.locked = 1; f.kind = 5; f.prio = 2;
    printf("\nready=%u dirty=%u locked=%u kind=%u prio=%u\n",
           f.ready, f.dirty, f.locked, f.kind, f.prio);

    const unsigned char *b = (const unsigned char *)&f;
    printf("바이트 :");
    for (size_t k = 0; k < sizeof f; k++) printf(" %02x", b[k]);
    printf("\n첫 바이트를 비트로 : ");
    for (int k = 7; k >= 0; k--) putchar((b[0] >> k) & 1 ? '1' : '0');
    printf("   <- 오른쪽이 bit0\n");

    f.kind = 9;                    /* 3비트에 9(1001) 를 넣으면 */
    printf("\nkind 에 9 를 넣고 읽으면 = %u   <- 3비트라 잘린다\n", f.kind);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24a.c -o x ; ./x (cc exit=0 · run exit=0) =====
struct Flags sizeof=4 _Alignof=4   (비트 합 = 1+1+1+3+2 = 8)
struct Plain sizeof=5 _Alignof=1

ready=1 dirty=0 locked=1 kind=5 prio=2
바이트 : ad 00 00 00
첫 바이트를 비트로 : 10101101   <- 오른쪽이 bit0

kind 에 9 를 넣고 읽으면 = 1   <- 3비트라 잘린다
```

**왜 그런가**

```text
   struct Flags — 선언한 비트는 1+1+1+3+2 = 8 뿐인데 sizeof 는 4 다

   비트 번호  31 ................ 8 |  7  6 |  5  4  3 |  2 |  1 |  0
            +---------------------+-------+----------+----+----+----+
            |   아무도 안 쓰는 자리  | prio  |   kind   | lo | di | re |
            +---------------------+-------+----------+----+----+----+
                    ★ 24비트          2       5(101)    1    0    1

   첫 바이트 = 1 0 1 0 1 1 0 1 = 0xAD
               ^^^ prio  ^^^^^ kind   ^ lo ^ di ^ re      (오른쪽이 bit0)

   struct Plain — unsigned char 다섯 개
            +----+----+----+----+----+
            | re | di | lo |kind|prio|      sizeof 5 · _Alignof 1
            +----+----+----+----+----+
```

- ★★ **`sizeof(struct Flags)` 는 4** 다. 8비트만 선언했는데도 **할당 단위가 4바이트**라 그만큼 잡힌다.\
  ★ **비트 합으로 크기를 예측하면 틀린다** — 이것은 [22번 형제](../22-struct-padding-and-alignment/)의 「멤버 크기 합으로 `sizeof` 를 예측하면 틀린다」와 같은 실수다.
- ★★ **`sizeof(struct Plain)` 은 5** 다. **4 대 5 — 한 바이트 차이**뿐이다.\
  ★★ 「비트필드를 쓰면 작아진다」가 **여기서는 거의 안 통한다.** 값이 나는 것은 **멤버가 많아질 때**다 —\
  같은 플래그를 **여덟 개**로 늘리면 `unsigned char` 쪽은 8 이 되고 비트필드 쪽은 **4 그대로**다.
- **`_Alignof` 는 4 와 1** 이다. 비트필드 구조체의 정렬은 **할당 단위**를 따르고, `unsigned char` 배열 같은 구조체는 **1** 이다.
- ★★ **첫 바이트가 `0xAD` = `10101101`** 이다. 오른쪽이 bit0 이므로 **선언 순서대로 낮은 비트부터** 채워졌다.\
  ★ **이 방향은 구현 정의**다 — 다른 ABI 에서는 높은 비트부터 채운다. `0xAD` 는 **이 머신의 답**이지 규칙이 아니다.
- ★★★ **`kind = 9` 는 `1` 로 읽힌다.** 그리고 이것은 **UB 가 아니라 변환**이다 —\
  9 는 `1001`, 3비트 폭에 넣으면 위쪽 한 자리가 잘려 `001` = **1** 이 된다.\
  ★ 「**미정의**」와 「**정의된 잘림**」을 가르는 것이 이 문항의 핵심이다(10번에서 다시 본다).

| 무엇을 물었나 | `struct Flags` | `struct Plain` |
|---|---|---|
| `sizeof` | **4** | **5** |
| `_Alignof` | **4** | **1** |
| 선언한 비트 \| 실제 바이트 | 8비트 \| 32비트 | 40비트 \| 40비트 |
| 어느 층인가 | ★★ **구현 정의**(단위·방향) | **표준**(배치는 [22번 형제](../22-struct-padding-and-alignment/)) |

### 2. 그 자리에서 컴파일러가 하는 말 — **`-Woverflow` 1건, 그런데 이름이 `unsigned char:3`** ★★

**출력**

```c
/* s24a.c */
#include <stdio.h>
#include <string.h>

struct Flags {                     /* 여덟 개의 플래그를 비트로 */
    unsigned ready : 1;
    unsigned dirty : 1;
    unsigned locked: 1;
    unsigned kind  : 3;            /* 0~7 */
    unsigned prio  : 2;            /* 0~3 */
};
struct Plain { unsigned char ready, dirty, locked, kind, prio; };

int main(void) {
    printf("struct Flags sizeof=%zu _Alignof=%zu   (비트 합 = 1+1+1+3+2 = 8)\n",
           sizeof(struct Flags), _Alignof(struct Flags));
    printf("struct Plain sizeof=%zu _Alignof=%zu\n",
           sizeof(struct Plain), _Alignof(struct Plain));

    struct Flags f;
    memset(&f, 0, sizeof f);
    f.ready = 1; f.dirty = 0; f.locked = 1; f.kind = 5; f.prio = 2;
    printf("\nready=%u dirty=%u locked=%u kind=%u prio=%u\n",
           f.ready, f.dirty, f.locked, f.kind, f.prio);

    const unsigned char *b = (const unsigned char *)&f;
    printf("바이트 :");
    for (size_t k = 0; k < sizeof f; k++) printf(" %02x", b[k]);
    printf("\n첫 바이트를 비트로 : ");
    for (int k = 7; k >= 0; k--) putchar((b[0] >> k) & 1 ? '1' : '0');
    printf("   <- 오른쪽이 bit0\n");

    f.kind = 9;                    /* 3비트에 9(1001) 를 넣으면 */
    printf("\nkind 에 9 를 넣고 읽으면 = %u   <- 3비트라 잘린다\n", f.kind);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24a.c -o x (cc exit=0) =====
s24a.c: In function ‘main’:
s24a.c:32:14: warning: unsigned conversion from ‘int’ to ‘unsigned char:3’ changes value from ‘9’ to ‘1’ [-Woverflow]
   32 |     f.kind = 9;                    /* 3비트에 9(1001) 를 넣으면 */
      |              ^
```

**왜 그런가**

- ★ **경고는 1건**이고 플래그 이름은 **`-Woverflow`** 다. `cc exit=0` — **경고이지 에러가 아니다.**
- ★★★ **진단이 그 멤버를 `unsigned char:3` 이라고 부른다.** 소스의 선언은 **`unsigned kind : 3;`** 이다.\
  **선언은 `unsigned int` 인데 컴파일러는 `unsigned char` 단위로 잡아 두었다** — 그 속사정이 진단에 새어 나온 것이다.
- ★★ **그 이름이 알려 주는 것** — 「**할당 단위와 그 안의 타입은 컴파일러가 고른다**」는 것.\
  ★ 5번에서 같은 자리가 **`signed char:3`** 이라고 불리는데, **그것이 `int x : 3` 의 부호를 읽어 내는 창**이 된다.\
  ★★ 이 갈래에서 **진단 문구가 구현 정의 사항을 드러내는 드문 자리**다 — 「경고도 출력이다」의 좋은 예다.
- ★★ **변수를 넣으면 경고가 안 난다.** 컴파일러는 **상수일 때만** 잘림을 계산할 수 있다.\
  [11번 형제](../11-bitwise-operations-and-shifts/)의 「`-Wshift-*` 는 상수만 본다 — 변수는 한 건도 못 본다」와 **완전히 같은 모양**이다.
- ★ 그래서 **범위 검사는 내 몫**이다. 비트필드는 「넘치면 컴파일러가 잡아 준다」는 물건이 아니다.

### 3. 12비트만 선언한 구조체를 두 가지 방식으로 채우면 — **`-O0` 은 `d3 f8 ff ff` · `-O2` 는 `d3 08 00 00`** ★★★ 본체

**출력 (가)** — `memset(0xFF)` 로 채운 뒤 대입

```c
/* s24b.c */
#include <stdio.h>
#include <string.h>

struct B { unsigned a : 8; unsigned b : 4; };   /* 12비트만 쓴다 */

int main(void) {
    struct B v;
    memset(&v, 0xFF, sizeof v);      /* 먼저 전부 1 로 */
    v.a = 0xD3;
    v.b = 0x8;
    const unsigned char *p = (const unsigned char *)&v;
    printf("sizeof=%zu  memset(0xFF) 뒤 a=0xD3, b=0x8 을 대입했다\n", sizeof v);
    printf("바이트 :");
    for (size_t k = 0; k < sizeof v; k++) printf(" %02x", p[k]);
    printf("\n비트   :");
    for (size_t k = 0; k < sizeof v; k++) {
        putchar(' ');
        for (int j = 7; j >= 0; j--) putchar((p[k] >> j) & 1 ? '1' : '0');
    }
    printf("\n★ 12~31 비트는 어느 멤버도 아니다 — 그 자리가 어떻게 되는지는 구현에 달렸다\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24b.c -o x ; ./x (cc exit=0 · run exit=0) =====
sizeof=4  memset(0xFF) 뒤 a=0xD3, b=0x8 을 대입했다
바이트 : d3 f8 ff ff
비트   : 11010011 11111000 11111111 11111111
★ 12~31 비트는 어느 멤버도 아니다 — 그 자리가 어떻게 되는지는 구현에 달렸다
```

**출력 (나)** — 초기화 없이 대입만, 네 벌로 빌드

```c
/* s24b2.c */
#include <stdio.h>

struct B { unsigned a : 8; unsigned b : 4; };   /* 12비트만 쓴다 */

static void dirty(void) {
    volatile unsigned char buf[64];
    for (int k = 0; k < 64; k++) buf[k] = 0xFF;
    if (buf[0] != 0xFF) printf("!");
}

static struct B make(void) {       /* 초기화 없이 두 멤버만 대입한다 */
    volatile unsigned char guard[8] = {0};
    struct B v;
    v.a = 0xD3;
    v.b = 0x8;
    (void)guard;
    return v;
}

int main(void) {
    dirty();
    struct B v = make();
    const unsigned char *p = (const unsigned char *)&v;
    printf("초기화 없이 a=0xD3, b=0x8 만 대입했다 (앞서 스택을 0xFF 로 더럽혔다)\n");
    printf("바이트 :");
    for (size_t k = 0; k < sizeof v; k++) printf(" %02x", p[k]);
    printf("\n");
    return 0;
}
```

```text
===== 초기화 없이 두 멤버만 대입했을 때의 바이트 — 네 벌 (exit=0) =====
gcc   -O0 : 바이트 : d3 f8 ff ff
gcc   -O2 : 바이트 : d3 08 00 00
clang -O0 : 바이트 : d3 f8 ff ff
clang -O2 : 바이트 : d3 08 00 00
```

**왜 그런가**

```text
   (가) memset(0xFF) 뒤 대입 — 네 벌이 전부 같았다

   비트  31 ............ 12 | 11 10  9  8 |  7  6  5  4  3  2  1  0
        +------------------+-------------+------------------------+
        | 1 1 1 ...... 1 1 | 1  0  0  0  | 1  1  0  1  0  0  1  1 |
        +------------------+-------------+------------------------+
          ★ 미사용 20비트        b = 8           a = 0xD3
        바이트 : d3 f8 ff ff
                   ^^ 위쪽 니블 f 가 미사용 비트다

   (나) 초기화 없이 대입만 — ★ 최적화 수준으로 갈린다

   -O0  ->  d3 ★f8 ★ff ★ff     멤버 비트만 갈아 끼웠다 (주변이 살아남았다)
   -O2  ->  d3 ★08 ★00 ★00     할당 단위를 통째로 새로 썼다
```

- ★★ **(가)는 네 벌이 전부 `d3 f8 ff ff`** 다. `memset` 이 먼저 20비트를 1 로 만들어 두었고,\
  대입이 그 자리를 **안 건드렸기 때문**이다. 대조군으로 쓴다.
- ★★★ **(나)는 `-O0` 과 `-O2` 가 갈린다.** 멤버 값은 둘 다 `a=0xD3 b=0x8` 로 **같다.**
- ★★ **갈린 축은 컴파일러가 아니라 최적화 수준**이다 — **gcc 와 clang 은 각 수준에서 한 글자도 같았다.**
- ★ **코드 모양으로 보면** — `-O0` 은 멤버마다 **읽고-고치고-쓰기**를 해서 주변 비트를 그대로 둔다.\
  `-O2` 는 두 대입을 하나로 합쳐 **32비트 상수를 통째로 쓴다.** 그래서 나머지가 0 이 된다.
- ★★ **(가)와 (나)의 차이는 소스에서 단 하나** — `memset(&v, 0xFF, sizeof v)` 한 줄이다.\
  그 줄이 있으면 **미사용 비트가 결정된 값**을 갖고, 없으면 **컴파일러가 고른 코드 모양에 맡겨진다.**
- ★ **같은 바이너리를 15번 돌린 격자는 한 가지**였다. **흔들린 것은 실행이 아니라 빌드다.**
- ★★★ **이 사실은 「미명시」 칸**이다. 표준은 미사용 비트의 값을 정하지 않았고, **문서화 의무도 없다.**
- ★★ 그래서 **`memcmp` 로 두 구조체를 비교하면 멤버가 같아도 다르다고 나올 수 있고**,\
  **`fwrite` 로 저장하면 다른 빌드가 다른 바이트를 쓴다.**\
  [22번 형제](../22-struct-padding-and-alignment/)의 패딩 바이트와 **같은 성격**이고, 여기는 **비트 단위**라 더 촘촘하다.

### 4. 11번 편이 「갈린다」고 적은 구조체를 여섯 벌로 다시 던지면 — **`-O0` 에서만 갈린다** ★★★ 전제가 뒤집힌 자리

**출력**

```c
/* s24b3.c */
#include <stdio.h>

/* 11번 편이 「gcc 와 clang 이 갈린다」고 적은 그 구조체를 그대로 다시 던진다 */
struct Flags {
    unsigned a : 1;
    unsigned b : 3;
    signed   c : 4;
    int      d : 4;
};

int main(void) {
    struct Flags f = { 1, 5, -3, 7 };
    f.b = 9;                       /* 3비트에 9 는 안 들어간다 */
    f.d = 8;                       /* int : 4 에 8 */
    printf("a=%u b=%u c=%d d=%d  ", f.a, f.b, f.c, f.d);
    const unsigned char *p = (const unsigned char *)&f;
    printf("바이트 = %02X %02X %02X %02X\n", p[0], p[1], p[2], p[3]);
    return 0;
}
```

```text
===== 11번 편의 구조체를 여섯 벌로 — 컴파일러 2 × 최적화 3 (exit=0) =====
gcc   -O0 : a=1 b=1 c=-3 d=-8  바이트 = D3 78 00 00
gcc   -O1 : a=1 b=1 c=-3 d=-8  바이트 = D3 08 00 00
gcc   -O2 : a=1 b=1 c=-3 d=-8  바이트 = D3 08 00 00
clang -O0 : a=1 b=1 c=-3 d=-8  바이트 = D3 08 00 00
clang -O1 : a=1 b=1 c=-3 d=-8  바이트 = D3 08 00 00
clang -O2 : a=1 b=1 c=-3 d=-8  바이트 = D3 08 00 00
```

**왜 그런가**

```text
   11번 편이 적은 것                 여기서 여섯 벌로 본 것
   ------------------------        --------------------------------------
   gcc   -> D3 ★78 00 00           gcc  -O0 -> D3 ★78 00 00   ← 재현됐다
   clang -> D3 ★08 00 00           gcc  -O1 -> D3 ★08 00 00   ← ★ 같아진다
   「gcc 와 clang 이 갈린다」          gcc  -O2 -> D3 ★08 00 00
                                   clang -O0 -> D3 ★08 00 00
                                   clang -O1 -> D3 ★08 00 00
                                   clang -O2 -> D3 ★08 00 00

   ★ 갈린 것은 컴파일러가 아니라 「할당 단위를 통째로 쓰느냐」였다.
   ★ gcc 는 -O 하나로 그 선택을 바꾸고, clang 은 -O0 부터 통째로 쓴다.
```

- ★★ **11번 편의 수치는 재현된다** — 다만 **`gcc -O0` 에서만**이다. 그 편은 `-O` 를 안 적었고, **기본이 `-O0`** 이다.
- ★★★ **`-O1` 로 한 칸만 올리면 gcc 가 clang 과 같아진다.**\
  그러므로 「**gcc 는 `78`, clang 은 `08`**」은 **컴파일러의 성질이 아니다.**
- ★★★ **고쳐 쓰면 이렇다** — 「**미사용 비트는 컴파일러가 고른 코드 모양의 부산물이고,\
  그 선택은 컴파일러로도 최적화 수준으로도 갈린다.**」\
  ★ 3번의 (나)에서는 **`-O` 로만** 갈렸고, 여기서는 **`-O0` 에서 컴파일러로도** 갈렸다 — **같은 원인의 두 얼굴**이다.
- ★ **멤버 값은 여섯 벌 전부 `a=1 b=1 c=-3 d=-8`** 로 같다. **갈리는 것은 바이트뿐**이다.\
  ★ (참고로 `b` 가 5 가 아니라 1 인 것과 `d` 가 7 이 아니라 -8 인 것은 **폭을 넘는 대입이 잘린 결과**다 — 1번·5번과 같은 이야기다.)
- ★★ **실험 설계의 교훈** — **두 벌은 모자란다.** 한 축(컴파일러)만 흔들면 **그 축이 원인이라고 오해**한다.\
  축을 둘 흔들어 **여섯 벌**을 보면 원인이 **제3의 것**(코드 생성 방식)이라는 것이 드러난다.
- ★ **못 잰 것** — gcc `-O0` 이 남긴 `7` 이라는 니블이 **어디서 온 값인지**는 이 실험만으로 못 가른다.\
  `-O0` 이 그 니블을 **한 번도 안 건드린다**는 것까지는 보이지만, 그 자리에 **원래 무엇이 있었는지**는 이 프로그램 밖의 일이다.

### 5. `int`·`signed int`·`unsigned int` 비트필드에 각각 7 을 넣으면 — **`-1` · `-1` · `7`** ★★

**출력**

```c
/* s24c.c */
#include <stdio.h>

struct S {
    int          plain : 3;   /* ★ 부호가 구현 정의다 */
    signed int   sgn   : 3;
    unsigned int uns   : 3;
};

int main(void) {
    struct S s;
    s.plain = 7; s.sgn = 7; s.uns = 7;     /* 셋 다 비트는 111 */
    printf("셋 다 111 을 넣었다\n");
    printf("  int      x:3  ->  %d\n", s.plain);
    printf("  signed   x:3  ->  %d\n", s.sgn);
    printf("  unsigned x:3  ->  %u\n", s.uns);
    printf("\nint x:3 이 음수로 읽히면 이 구현에서는 ★ 부호 있는 것이다\n");
    printf("판정 : %s\n", s.plain < 0 ? "signed (이 구현)" : "unsigned (이 구현)");

    s.plain = 3; s.sgn = 3; s.uns = 3;
    printf("\n3 을 넣으면 셋 다 %d %d %u — 부호 비트가 안 켜지면 차이가 안 보인다\n",
           s.plain, s.sgn, s.uns);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24c.c -o x ; ./x (cc exit=0 · run exit=0) =====
셋 다 111 을 넣었다
  int      x:3  ->  -1
  signed   x:3  ->  -1
  unsigned x:3  ->  7

int x:3 이 음수로 읽히면 이 구현에서는 ★ 부호 있는 것이다
판정 : signed (이 구현)

3 을 넣으면 셋 다 3 3 3 — 부호 비트가 안 켜지면 차이가 안 보인다
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24c.c -o x (cc exit=0) =====
s24c.c: In function ‘main’:
s24c.c:11:15: warning: overflow in conversion from ‘int’ to ‘signed char:3’ changes value from ‘7’ to ‘-1’ [-Woverflow]
   11 |     s.plain = 7; s.sgn = 7; s.uns = 7;     /* 셋 다 비트는 111 */
      |               ^
s24c.c:11:26: warning: overflow in conversion from ‘int’ to ‘signed char:3’ changes value from ‘7’ to ‘-1’ [-Woverflow]
   11 |     s.plain = 7; s.sgn = 7; s.uns = 7;     /* 셋 다 비트는 111 */
      |                          ^
```

**왜 그런가**

```text
   비트는 셋 다 111 이다. ★ 읽는 법이 다를 뿐이다.

   unsigned x:3        signed x:3 (2의 보수)
   +--+--+--+          +--+--+--+
   | 1| 1| 1| = 7      | 1| 1| 1| = -1
   +--+--+--+          +--+--+--+
    4  2  1             ^ 부호 비트

   범위:  unsigned x:3  ->  0 .. 7
         signed   x:3  -> -4 .. 3      ★ 7 은 애초에 안 들어간다
         int      x:3  ->  ★ 둘 중 무엇인지 구현이 정한다
```

- ★★ **`int x : 3` 에 7 을 넣으면 `-1`** 이 읽힌다 — 이 구현에서는 **부호 있는 것**으로 잡혔다.
- ★★★ **그 사실은 「구현 정의」 칸**이다. 다른 구현에서는 **`7`** 이 나올 수 있고, 그래도 적법하다.
- ★ **경고는 2건**이고, `plain` 과 `sgn` 에 붙었다. **`uns` 에는 안 붙었다** — 7 이 `unsigned x:3` 에는 **정상으로 들어가기 때문**이다.\
  ★★ **경고가 붙은 멤버**가 곧 「**부호 있는 것으로 잡힌 멤버**」다 — 이것이 **부호를 알아내는 또 하나의 창**이다.
- ★★ **진단이 `signed char:3` 이라고 적는다.** 2번의 `unsigned char:3` 과 짝이다.\
  **선언에 `int` 라고 썼는데 컴파일러는 `signed char` 단위로 잡았다**는 뜻이다.
- ★★★ **3 을 넣으면 셋 다 `3`** 이다. **부호 비트가 안 켜지는 동안은 차이가 안 보인다.**\
  ★ 그래서 이 함정은 **오래 숨는다** — 값이 작을 때는 잘 돌다가, 어느 날 큰 값이 들어오면서 **음수가 튀어나온다.**
- ★ **답은 하나다** — **`signed`·`unsigned` 를 직접 적는 것.** 한 낱말이고 공짜다.

### 6. 그 선택을 플래그로 되돌릴 수 있나 — **gcc 만 먹고 clang 은 「모른다」면서 통과시킨다** ★★★

**출력**

```c
/* s24c.c */
#include <stdio.h>

struct S {
    int          plain : 3;   /* ★ 부호가 구현 정의다 */
    signed int   sgn   : 3;
    unsigned int uns   : 3;
};

int main(void) {
    struct S s;
    s.plain = 7; s.sgn = 7; s.uns = 7;     /* 셋 다 비트는 111 */
    printf("셋 다 111 을 넣었다\n");
    printf("  int      x:3  ->  %d\n", s.plain);
    printf("  signed   x:3  ->  %d\n", s.sgn);
    printf("  unsigned x:3  ->  %u\n", s.uns);
    printf("\nint x:3 이 음수로 읽히면 이 구현에서는 ★ 부호 있는 것이다\n");
    printf("판정 : %s\n", s.plain < 0 ? "signed (이 구현)" : "unsigned (이 구현)");

    s.plain = 3; s.sgn = 3; s.uns = 3;
    printf("\n3 을 넣으면 셋 다 %d %d %u — 부호 비트가 안 켜지면 차이가 안 보인다\n",
           s.plain, s.sgn, s.uns);
    return 0;
}
```

```text
===== int 비트필드의 부호 — 컴파일러와 -funsigned-bitfields 를 바꿔 가며 (exit=0) =====
gcc   (기본)             : int x:3 에 7 을 넣으면 -1
gcc   -funsigned-bitfields : int x:3 에 7 을 넣으면 7
clang (기본)             : int x:3 에 7 을 넣으면 -1
clang -funsigned-bitfields : int x:3 에 7 을 넣으면 -1
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -Wunused-command-line-argument -funsigned-bitfields s24c.c -o x (cc exit=0) =====
clang: warning: the clang compiler does not support '-funsigned-bitfields'
s24c.c:11:13: warning: implicit truncation from 'int' to bit-field changes value from 7 to -1 [-Wbitfield-constant-conversion]
   11 |     s.plain = 7; s.sgn = 7; s.uns = 7;     /* 셋 다 비트는 111 */
      |             ^ ~
s24c.c:11:24: warning: implicit truncation from 'int' to bit-field changes value from 7 to -1 [-Wbitfield-constant-conversion]
   11 |     s.plain = 7; s.sgn = 7; s.uns = 7;     /* 셋 다 비트는 111 */
      |                        ^ ~
2 warnings generated.
```

**왜 그런가**

- ★★ **gcc 는 `-funsigned-bitfields` 로 바뀐다** — `int x : 3` 에 7 을 넣은 결과가 `-1` 에서 **`7`** 이 된다.\
  ★ **그 플래그가 있다는 것 자체가 「구현 정의」의 증거**다 — 구현이 **고를 수 있는 것**이라서 스위치가 있다.
- ★★★ **clang 은 안 바뀐다.** `-1` 그대로다.
- ★★★ **그런데 빌드는 `cc exit=0` 으로 통과한다.** clang 은
  `the clang compiler does not support '-funsigned-bitfields'` 라고 **말은 해 준다** —\
  다만 그 줄은 **`-Wunused-command-line-argument` 를 켜야** 보인다.
- ★★★ **「경고가 났다」와 「반영됐다」가 정반대로 어긋나는 자리**다.\
  여기서 경고는 **「했다」는 보고가 아니라 「안 했다」는 통보**다. **경고를 읽고 안심하면 정확히 틀린다.**
- ★ 같은 소스에 대한 **진단 이름도 갈린다** — gcc 는 `-Woverflow`, clang 은 `-Wbitfield-constant-conversion` 이다.\
  ★ **문구로 도구를 식별할 수는 있어도, 문구로 동작을 보장받을 수는 없다.**
- ★★ **이식 가능한 답은 플래그가 아니다** — **선언에 `signed`/`unsigned` 를 적는 것** 하나뿐이다.\
  빌드 플래그로 언어 의미를 맞추려는 시도는 **팀·빌드 시스템·컴파일러가 바뀌는 순간 무너진다.**

### 7. 비트필드에 `&` 와 `sizeof` 를 쓰면 — **양쪽 다 컴파일 에러 · `cc exit=1`** ★

**출력**

```c
/* s24d.c */
#include <stdio.h>

struct S { unsigned a : 3; unsigned b : 5; };

int main(void) {
    struct S s = { 1, 2 };
    unsigned *p = &s.a;              /* (1) 비트필드는 주소를 못 잡는다 */
    printf("%zu\n", sizeof s.a);     /* (2) sizeof 도 안 된다 */
    printf("%zu\n", _Alignof(s.b));  /* (3) _Alignof 도 안 된다 */
    return p != 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24d.c -o x (cc exit=1) =====
s24d.c: In function ‘main’:
s24d.c:7:19: error: cannot take address of bit-field ‘a’
    7 |     unsigned *p = &s.a;              /* (1) 비트필드는 주소를 못 잡는다 */
      |                   ^
s24d.c:8:28: error: ‘sizeof’ applied to a bit-field
    8 |     printf("%zu\n", sizeof s.a);     /* (2) sizeof 도 안 된다 */
      |                            ^
s24d.c:9:21: warning: ISO C does not allow ‘_Alignof (expression)’ [-Wpedantic]
    9 |     printf("%zu\n", _Alignof(s.b));  /* (3) _Alignof 도 안 된다 */
      |                     ^~~~~~~~
s24d.c:9:21: error: ‘__alignof’ applied to a bit-field
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s24d.c -o x (cc exit=1) =====
s24d.c:7:19: error: address of bit-field requested
    7 |     unsigned *p = &s.a;              /* (1) 비트필드는 주소를 못 잡는다 */
      |                   ^~~~
s24d.c:8:30: error: invalid application of 'sizeof' to bit-field
    8 |     printf("%zu\n", sizeof s.a);     /* (2) sizeof 도 안 된다 */
      |                              ^
s24d.c:9:21: warning: '_Alignof' applied to an expression is a GNU extension [-Wgnu-alignof-expression]
    9 |     printf("%zu\n", _Alignof(s.b));  /* (3) _Alignof 도 안 된다 */
      |                     ^
s24d.c:9:29: error: invalid application of 'alignof' to bit-field
    9 |     printf("%zu\n", _Alignof(s.b));  /* (3) _Alignof 도 안 된다 */
      |                             ^~~~~
1 warning and 3 errors generated.
```

**왜 그런가**

```text
   보통 멤버                          비트필드 멤버
   -----------------------------    -----------------------------
   struct { int x; }                struct { unsigned a : 3; }
   &s.x   -> int *         OK       &s.a   -> ★ 컴파일 에러
   sizeof s.x -> 4         OK       sizeof s.a -> ★ 컴파일 에러
   offsetof(S, x) -> 0     OK       offsetof(S, a) -> ★ 쓸 수 없다

   ★ 이유는 하나다 — 주소는 ★ 바이트 단위로만 존재한다.
     비트필드는 바이트 경계에 안 맞을 수 있어 가리킬 주소가 없다.
```

- ★★ **에러도 출력이다.** 두 컴파일러의 문구를 나란히 봐 두면 실전에서 바로 읽힌다.

| 무엇을 했나 | gcc 13.3.0 | clang 18.1.3 |
|---|---|---|
| `&s.a` | `cannot take address of bit-field ‘a’` | `address of bit-field requested` |
| `sizeof s.a` | `‘sizeof’ applied to a bit-field` | `invalid application of 'sizeof' to bit-field` |
| `_Alignof(s.b)` | `‘__alignof’ applied to a bit-field` | `invalid application of 'alignof' to bit-field` |
| 그 줄의 **추가 진단** | `-Wpedantic` — `ISO C does not allow ‘_Alignof (expression)’` | `-Wgnu-alignof-expression` |
| `cc exit` | **1** | **1** |

- ★★ **세 번째 줄에서만 진단이 둘** 나온다. `_Alignof(식)` 은 **그 자체가 ISO C 가 아니라서**(GNU 확장)\
  「**비표준 문법**」 경고와 「**비트필드에는 못 쓴다**」 에러가 **한 줄에 겹친다.**\
  ★ gcc 는 `-Wpedantic` 이라는 이름으로, clang 은 `-Wgnu-alignof-expression` 이라는 이름으로 같은 말을 한다.
- ★★ **이 제약은 「표준」 칸**이다. 구현 정의가 아니라 **어느 구현에서도 에러**다.\
  ★ 그래서 **도구가 아주 잘 본다** — 이 주제에서 도구가 확실히 일하는 거의 유일한 자리다.
- ★ **`offsetof` 도 쓸 수 없다.** `offsetof` 는 **바이트 오프셋**을 내는 물건인데 비트필드에는 그것이 없다\
  ([08번 형제](../08-sizeof-alignment-and-offsetof/)가 `offsetof` 의 정본이다).
- ★ **주소가 꼭 필요해지면** 그 멤버는 **비트필드가 아니어야** 한다 — 보통 멤버로 빼는 것이 답이다.

### 8. 폭 3 과 폭 32 짜리 비트필드에서 각각 0 에서 1 을 빼면 — **`-1` 과 `4294967295`** ★★

**출력**

```c
/* s24e.c */
#include <stdio.h>

struct S {
    unsigned small : 3;    /* int 가 다 담을 수 있다 */
    unsigned full  : 32;   /* int 로는 못 담는다 */
};

#define NAME(x) _Generic((x), int: "int", unsigned int: "unsigned int", \
                              long: "long", default: "그 밖")

int main(void) {
    struct S s = { 0, 0 };
    printf("s.small 을 식에 쓰면 타입은 : %s\n", NAME(s.small + 0));
    printf("s.full  을 식에 쓰면 타입은 : %s\n", NAME(s.full + 0));
    printf("맨 unsigned 변수는          : %s\n", NAME((unsigned)0 + 0));

    printf("\n0 에서 1 을 빼 보면\n");
    printf("  s.small - 1 = %d      <- int 로 승격돼 음수가 나온다\n", s.small - 1);
    printf("  s.full  - 1 = %u      <- unsigned 그대로라 감싼다\n", s.full - 1);
    printf("  (s.small - 1 < 0) = %d · (s.full - 1 < 0) = %d\n",
           s.small - 1 < 0, s.full - 1 < 0);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24e.c -o x ; ./x (cc exit=0 · run exit=0) =====
s.small 을 식에 쓰면 타입은 : int
s.full  을 식에 쓰면 타입은 : unsigned int
맨 unsigned 변수는          : unsigned int

0 에서 1 을 빼 보면
  s.small - 1 = -1      <- int 로 승격돼 음수가 나온다
  s.full  - 1 = 4294967295      <- unsigned 그대로라 감싼다
  (s.small - 1 < 0) = 1 · (s.full - 1 < 0) = 0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24e.c -o x (cc exit=0) =====
s24e.c: In function ‘main’:
s24e.c:21:40: warning: comparison of unsigned expression in ‘< 0’ is always false [-Wtype-limits]
   21 |            s.small - 1 < 0, s.full - 1 < 0);
      |                                        ^
```

**왜 그런가**

```text
   unsigned small : 3        담을 수 있는 값 0..7
                             -> int 가 전부 담는다  -> ★ int 로 승격
   unsigned full  : 32       담을 수 있는 값 0..4294967295
                             -> int 가 못 담는다    -> ★ unsigned int 그대로

   같은 「0 - 1」인데

     small - 1   ->  int 산술        ->  -1
     full  - 1   ->  unsigned 산술   ->  4294967295
                                          ^ 감싼다
```

- ★★ **`_Generic` 이 `int` 와 `unsigned int` 로 답했다.** 둘 다 **`unsigned` 로 선언**했는데도 그렇다.
- ★★★ **갈림을 결정하는 것은 「폭」이다** — 정확히는 「**`int` 가 그 비트필드의 모든 값을 담을 수 있는가**」다.\
  담을 수 있으면 **`int` 로 승격**되고, 못 담으면 **선언한 타입 그대로** 간다.
- ★★ 그래서 **`s.small - 1` 이 `-1`** 이고 **`s.full - 1` 이 `4294967295`** 다.\
  ★ **폭 한 자리 차이로 부호가 바뀐다** — 폭 31 이면 `int` 로 승격되고 폭 32 면 안 된다.
- ★ **경고는 `full` 쪽에만** 붙는다 — `-Wtype-limits` 로 「`< 0` 은 **항상 거짓**」이라고 한다.\
  `small` 쪽은 **참이 될 수 있으니** 할 말이 없다. ★ **경고가 없는 쪽이 오히려 「승격됐다」는 증거**다.
- ★★ 「**`unsigned` 로 선언했으니 식에서도 `unsigned` 겠지**」가 틀린 이유가 여기 있다 —\
  선언의 타입과 **식의 타입**은 다른 것이고, 그 사이에 **정수 승격**이 끼어 있다.
- ★ **정본은 [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)** 다. 여기서는 「**비트필드도 그 규칙을 받는다**」는 것과\
  「**폭에 따라 결과 타입이 갈린다**」는 것만 본다.

### 9. 폭 0 비트필드와 이름 없는 폭 2 는 무엇이 다른가 — **폭 0 은 `sizeof` 를 4 에서 8 로 늘린다** ★★

**출력**

```c
/* s24f.c */
#include <stdio.h>
#include <string.h>

struct A { unsigned a : 3; unsigned b : 3; };            /* 붙는다 */
struct B { unsigned a : 3; unsigned : 0; unsigned b : 3; };  /* ★ 폭 0 이 끊는다 */
struct C { unsigned a : 3; unsigned : 2; unsigned b : 3; };  /* 이름 없는 폭 2 */

static void dump(const char *tag, const void *p, size_t n) {
    const unsigned char *b = (const unsigned char *)p;
    printf("%-14s sizeof=%zu  바이트 :", tag, n);
    for (size_t k = 0; k < n; k++) printf(" %02x", b[k]);
    printf("\n");
}

int main(void) {
    struct A x; struct B y; struct C z;
    memset(&x, 0, sizeof x); memset(&y, 0, sizeof y); memset(&z, 0, sizeof z);
    x.a = 7; x.b = 7;
    y.a = 7; y.b = 7;
    z.a = 7; z.b = 7;
    dump("A  a:3 b:3", &x, sizeof x);
    dump("B  a:3 :0 b:3", &y, sizeof y);
    dump("C  a:3 :2 b:3", &z, sizeof z);
    printf("\n★ 폭 0 비트필드는 이름을 못 가진다 — 다음 할당 단위로 밀라는 지시다\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s24f.c -o x ; ./x (cc exit=0 · run exit=0) =====
A  a:3 b:3     sizeof=4  바이트 : 3f 00 00 00
B  a:3 :0 b:3  sizeof=8  바이트 : 07 00 00 00 07 00 00 00
C  a:3 :2 b:3  sizeof=4  바이트 : e7 00 00 00

★ 폭 0 비트필드는 이름을 못 가진다 — 다음 할당 단위로 밀라는 지시다
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s24f.c -o x ; ./x (cc exit=0 · run exit=0) =====
A  a:3 b:3     sizeof=4  바이트 : 3f 00 00 00
B  a:3 :0 b:3  sizeof=8  바이트 : 07 00 00 00 07 00 00 00
C  a:3 :2 b:3  sizeof=4  바이트 : e7 00 00 00

★ 폭 0 비트필드는 이름을 못 가진다 — 다음 할당 단위로 밀라는 지시다
```

**왜 그런가**

```text
   A { a:3; b:3; }                       한 할당 단위에 붙는다
   비트  ...  7  6  5  4  3  2  1  0
              .  .  1  1  1  1  1  1     -> 0x3F   sizeof 4
                    ^^^^^^^^ b  ^^^^^^^^ a

   C { a:3; :2; b:3; }                   이름 없는 폭 2 가 사이를 벌린다
   비트  ...  7  6  5  4  3  2  1  0
              1  1  1  0  0  1  1  1     -> 0xE7   sizeof 4
              ^^^^^^^^ b  ^^ 빈칸 ^^^^^^ a

   B { a:3; :0; b:3; }                   ★ 폭 0 이 할당 단위를 끊는다
   바이트  07 00 00 00 | 07 00 00 00                sizeof ★ 8
           ^ a 의 단위    ^ b 의 ★ 새 단위
```

- **`A` 는 `3f 00 00 00`** 이다. `a` 와 `b` 가 **한 단위 안에 이어 붙었다**(bit0\~bit5 = `111111`).
- **`C` 는 `e7 00 00 00`** 이다. **이름 없는 폭 2** 가 bit3\~bit4 를 **비워 두고**, `b` 가 bit5 부터 들어갔다.\
  ★ 이름 없는 비트필드는 **자리만 차지하고 읽고 쓸 수 없다.**
- ★★★ **`B` 는 `sizeof` 가 8** 이다. **폭 0 은 자리를 비우는 것이 아니라** 「**여기서 끊고 다음 할당 단위로 가라**」는 지시다.\
  그래서 `a` 와 `b` 가 **각각 자기 4바이트 단위**에 들어가고 `07 00 00 00 07 00 00 00` 이 된다.
- ★ **폭 0 에 이름을 주면 컴파일 에러**다. 담을 비트가 없으니 이름을 줄 이유도 없다.
- ★ **gcc 와 clang 이 한 글자도 같았다.** 다만 이것도 **구현 정의 영역**이라 다른 ABI 에서 같으리라는 보장은 없다.
- ★ **폭 0 을 일부러 쓰는 상황** — 하드웨어 레지스터나 ABI 문서가 「**이 필드부터는 새 워드**」라고 정해 둔 자리를\
  구조체로 흉내 낼 때. ★ 다만 **외부 포맷 자체를 비트필드로 그리는 것은 여전히 금물**이다(12번).

### 10. 「잘린다」는 왜 UB 가 아닌가 — **정의된 변환이기 때문** ★★

- ★★★ **`f.kind = 9` 는 「정수 변환」이다.** 폭 3 의 비트필드는 **값의 범위가 정해진 정수 타입처럼** 행동하고,\
  범위 밖의 값을 대입하면 **그 폭으로 변환**된다. 결과가 **`1`** 이라는 것도 정해져 있다(`unsigned` 이므로 모듈러).\
  ★ **미정의였다면 값이 정해지지 않았을 것이고, 컴파일러가 `-Woverflow` 로 「`9` → `1`」이라고 못 박지도 못했을 것**이다.
- ★★ 그러면 **UB 칸에 들어갈 것**은 무엇인가 — ★ **이 주제 고유의 것은 거의 없다.**\
  비트필드가 만드는 사고는 대부분 「**구현 정의**」이거나 「**미명시**」다.\
  ★ 넓은 UB(구조체를 다른 타입으로 읽기 등)는 [23번 형제](../23-union-and-the-boundary-of-type-punning/)와 목록의 **55번 주제**의 몫이다.
- ★★ **UB 칸이 얇은 이유** — 비트필드는 **컴파일러가 마스크와 시프트를 대신 써 주는 문법**이다.\
  내가 자리를 계산하지 않으니 **자리를 잘못 계산해서 생기는 UB 가 없다.**\
  [11번 형제](../11-bitwise-operations-and-shifts/)에서 UB 칸이 두꺼웠던 것은 **시프트량을 내가 정했기** 때문이다 —\
  ★ **UB 를 줄이는 대신 구현 정의를 늘린 거래**다.
- ★ **`struct T { unsigned a : 40; };` 는 다르다** — **컴파일 에러**다.\
  「**폭이 그 타입의 비트 수를 넘는 것**」은 **선언 자체가 위법**이라 변환의 여지가 없다.\
  ★★ **값이 넘치는 것은 변환, 폭이 넘치는 것은 에러** — 이 둘을 가르는 것이 이 문항이다.
- ★ **미사용 비트를 읽는 것 자체**는 UB 가 아니다. `unsigned char *` 로 보면 **어떤 바이트든 읽을 수 있다.**\
  ★★ **틀린 것은 읽는 행위가 아니라 그 값을 판단에 쓰는 것**이다 — 값이 **정해져 있지 않기** 때문이다.\
  ([22번 형제](../22-struct-padding-and-alignment/)의 「패딩 바이트를 읽고 판단에 쓰는 것」과 같은 경계다.)

### 11. 다섯 층과 무게중심 — **구현 정의가 본체, 미명시가 두 번째, UB 는 얇다** ★★★

| 층 | 이 주제에서 해당하는 것 | 무게 |
|---|---|---|
| **표준** | 선언 가능한 타입 셋 · **폭 초과 선언은 에러** · **폭 0 은 이름 금지** · **`&`·`sizeof` 금지** · **식에서 정수 승격** · 넘는 값은 **변환** · 멤버 값 자체의 이식성 | 보통 |
| **조건부 표준** | ★ **비어 있다** — 매크로로 켜지고 꺼지는 보장이 없다 | **없음** |
| ★★★ **구현 정의** | **비트를 채우는 방향** · **할당 단위의 크기** · **단위 경계를 걸치는가** · ★★ **`int x : n` 의 부호** · `char`·`short` 등을 허용하는가 · 구조체의 **정렬** | ★★★ **가장 두껍다** |
| ★★ **미명시** | ★★★ **어느 멤버도 아닌 비트의 값** · 구조체 끝 패딩 | ★★ **두 번째** |
| **UB** | ★ **고유한 것이 거의 없다.** 넓은 UB 는 23번·55번의 몫 | ★ **얇다** |

- ★★ **비어 있는 칸**은 「**조건부 표준**」이다.
- ★★ **도구가 침묵하는 자리를 층마다 하나씩**

| 층 | 도구가 침묵하는 자리 |
|---|---|
| **표준** | ★ 여기는 잘 본다 — `&`·`sizeof`·폭 초과가 전부 **에러**다. **다만 넘는 값은 상수일 때만** 잡는다 |
| **조건부 표준** | ★ 해당 없음 |
| **구현 정의** | ★★ **「낮은 비트부터 채웠습니다」라고 말해 주는 경고가 없다.** `int x:3` 의 부호도 **경고 0건**이고, 7 을 넣어 `-Woverflow` 가 뜰 때에야 문구(`signed char:3`)로 새어 나온다 |
| **미명시** | ★★★ **미사용 비트는 어떤 경고·UBSan·ASan 도 안 본다.** 값이 없는 것이 아니라 **정해지지 않은** 것이라 **원리상 잡을 것이 없다** |
| **UB** | ★ 잡을 UB 를 거의 만들지 않는다 — sanitizer 가 할 일이 없다 |

- ★★★ **[22번 형제](../22-struct-padding-and-alignment/)와 같은 것** — 「**값이 정해지지 않은 자리가 구조체 안에 있고,\
  그것이 `memcmp`·직렬화를 깨뜨리며, 어떤 도구도 안 본다**」는 구조가 똑같다.
- ★★ **다른 것 셋**
  - ★ **단위가 다르다** — 22번은 **바이트**, 여기는 **비트**다. 그래서 여기가 **더 촘촘하고 더 안 보인다.**
  - ★★ **22번에는 「구현 정의」와 「미명시」가 나란히 두껍지만, 여기는 「구현 정의」가 압도적**이다 —\
    22번에서 내가 못 정하는 것은 **패딩**뿐인데, 여기서는 **방향·단위·부호까지** 전부 못 정한다.
  - ★ **22번은 `_Static_assert` 로 `sizeof` 와 `offsetof` 를 못 박을 수 있다.**\
    여기서는 **`sizeof` 까지만** 못 박을 수 있고 **비트 자리는 못 박는다**(`offsetof` 가 안 되니까).

### 12. 경계 — 어디까지가 이 주제인가 ★

| 무엇 | 정본 |
|---|---|
| **마스크와 시프트로 손수 비트를 다루는 법** | [11번 형제](../11-bitwise-operations-and-shifts/) — ★★ **직접 선행** |
| **정수 승격 규칙 자체** | [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/) |
| **구조체 패딩·정렬** | [22번 형제](../22-struct-padding-and-alignment/) |
| **`sizeof`·`_Alignof`·`offsetof` 라는 도구** · `_Static_assert` | [08번 형제](../08-sizeof-alignment-and-offsetof/) |
| **구조체 선언·초기화·지정 초기자** | [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/) |
| **`union` 과 타입 펀닝** | [23번 형제](../23-union-and-the-boundary-of-type-punning/) |
| **플래그를 이름 붙은 상수 + 마스크로** | [07번 형제](../07-enum-and-enumeration-constants/) |
| **엄격한 앨리어싱** | 목록의 **55번 주제** |
| **비트 기법·응용**(popcount 등) | [`algorithm/29-bit-manipulation/`](../../../../../algorithm/29-bit-manipulation/) |

- ★★ **파일·패킷 포맷에 비트필드를 쓰면 안 되는 이유 한 줄** —\
  「**자리·방향·단위가 구현 정의이고 미사용 비트가 미명시라, 같은 소스도 빌드가 바뀌면 다른 바이트를 쓴다.**」\
  ★ 3번·4번이 그것을 **여섯 벌의 격자**로 보였다.
- ★ **이 주제가 끝까지 책임지는 것 셋**
  - ★★★ **미사용 비트의 값이 어떻게 갈리는가** — **여섯 벌의 격자**가 이 편의 본체다.
  - ★★ **`int x : n` 의 부호가 구현 정의라는 것**과 **플래그로 되돌릴 수 없다는 것.**
  - ★★ **비트필드가 무엇을 못 하는가** — `&`·`sizeof`·`offsetof` 가 안 되고, **식에서 승격된다.**
- ★ **열거 상수 + 마스크**([07번 형제](../07-enum-and-enumeration-constants/))를 고르는 때 —\
  **값이 프로그램 밖으로 나갈 때**(파일·패킷·다른 언어와의 경계). 그때는 자리를 **내가 못 박아야** 한다.

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s24a.c` (24-a) | `sizeof` **4 대 5** · `_Alignof` **4 대 1** · 첫 바이트 **`0xAD` = `10101101`** · `kind = 9` → **`1`** · 경고 **1건**(`-Woverflow`, 문구가 `unsigned char:3`) | gcc 2벌(실행·진단) |
| `s24b.c` (24-b) | `memset(0xFF)` 뒤 대입 → **`d3 f8 ff ff`** — **대조군** | gcc 1벌(문서) · ★ 네 벌(gcc/clang × `-O0`/`-O2`)로 **같음을 확인** |
| `s24b2.c` (24-c) | 초기화 없이 대입만 → **`-O0` `d3 f8 ff ff` · `-O2` `d3 08 00 00`** · **gcc = clang** | ★ **4벌**(gcc/clang × `-O0`/`-O2`) |
| `s24b3.c` (24-d) | 11번 편의 구조체 재현 → **gcc `-O0` 만 `D3 78`**, 나머지 다섯 벌은 **`D3 08`** · 멤버 값은 여섯 벌 동일 | ★★ **6벌**(gcc/clang × `-O0`/`-O1`/`-O2`) |
| `s24c.c` (24-e) | `int`/`signed`/`unsigned` `x:3` 에 7 → **`-1` · `-1` · `7`** · 경고 **2건**(`-Woverflow`, 문구가 `signed char:3`) · `-funsigned-bitfields` 로 **gcc 만 `7`** · clang 은 **「지원 안 함」 경고 + `cc exit=0`** | gcc 3벌 · clang 3벌 |
| `s24d.c` (24-f) | `&`·`sizeof`·`_Alignof` 에 대한 **에러 전문** · **`cc exit=1`** · `_Alignof(식)` 은 **경고와 에러가 겹친다** | gcc 1벌 · clang 1벌 |
| `s24e.c` (24-g) | `_Generic` → **`int`** 와 **`unsigned int`** · `0 - 1` → **`-1`** 과 **`4294967295`** · `-Wtype-limits` **1건**(한쪽만) | gcc 2벌(실행·진단) |
| `s24f.c` (24-h) | `A` **`3f 00 00 00` sizeof 4** · `B` **`07 00 00 00 07 00 00 00` sizeof 8** · `C` **`e7 00 00 00` sizeof 4** · **gcc = clang** | gcc 1벌 · clang 1벌 |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3)에서만** 그렇다.

- ★★ **비트를 낮은 자리부터 채우는 것**(`0xAD` = `10101101`) — **구현 정의**다.
- ★★ **할당 단위가 4바이트인 것**(`sizeof` 4 · `_Alignof` 4) — **구현 정의**다.
- ★★ **`int x : 3` 이 부호 있는 것**(7 → `-1`) — **구현 정의**다. 다른 구현에서 `7` 이 나와도 적법하다.
- ★★★ **모든 미사용 비트의 값**(`f8 ff ff` · `08 00 00` · `78`) — **미명시**다.\
  ★ **빌드가 바뀌면 갈린다**는 사실만이 결론이고, **어느 값이 나오는가는 결론이 아니다.**
- ★ **진단 문구가 `unsigned char:3`·`signed char:3` 이라고 적는 것** — gcc 내부 표현의 노출이다.
- ★ **`-funsigned-bitfields` 가 gcc 에만 있는 것** — 구현의 선택이다.

**폭 초과 대입이 「변환」인 것 · `&`·`sizeof` 금지 · 폭 0 의 의미 · 정수 승격은 구현 의존이 아니다.**\
어느 C 구현에서도 같다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `_Bool b : 1;` · `__attribute__((packed))` 와 비트필드 · `unsigned long long x : 40;`(확장 폭) ·\
  **비트필드와 `union` 을 겹쳐 쓰는 관용구** · `_BitInt(N)`(gcc 13 지원 범위 미확인) ·\
  **빅엔디언 머신**(방향이 뒤집히는지 확인할 장비가 없다) · **`-Os`·`-O3`**(3·4번은 `-O0`\~`-O2` 까지만 흔들었다).
- ★ **못 잰 것** — **gcc `-O0` 이 남긴 `7` 이라는 니블의 출처.**\
  역어셈블로 「`-O0` 이 그 자리를 한 번도 안 건드린다」까지는 보이지만,\
  **그 자리에 원래 무엇이 있었는지는 이 프로그램 밖의 일**이라 이 실험으로는 가를 수 없다.\
  ★ 「안 돌려 본 것」이 아니라 「**측정 방법이 전제를 요구해 잴 수 없는 것**」이라 따로 적는다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **3번·4번의 여섯 벌 격자** — **코드 생성이 바뀌면 그대로 바뀐다.** ★ 미명시 칸이라 **언제든 달라질 수 있다.**
- ★★ **clang 이 `-funsigned-bitfields` 를 지원하게 됐는지**(지금은 「지원 안 함」 경고 + 무시).
- ★ **진단 문구**(`unsigned char:3`·`signed char:3`)는 **문구 대조를 깨뜨리는 자리**다.
- **`&`·`sizeof` 금지, 폭 0 의 의미, 승격 규칙은 다시 돌릴 필요가 없다** — C89 이후 바뀐 적이 없다.
