# c/syntax/24 — 비트필드: 「**폭은 내가 정하고 자리는 컴파일러가 정한다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **비트 격자**(32비트 중 어느 자리에 무엇이 들어갔나) ② **바이트 덤프**(`d3 f8 ff ff` 인가 `d3 08 00 00` 인가)
> ③ **그 사실이 다섯 층 중 어느 칸인가**(표준인가 구현 정의인가 미명시인가).
> ★★★ **이 주제는 「구현 정의」가 본체**다 — 자리·방향·단위·부호가 전부 거기 있다.
> 두 번째가 **미명시**(미사용 비트의 값)이고, ★ **UB 칸은 얇다.**
> ★★ **한 벌만 빌드하고 답하지 마라** — 3번과 4번은 **컴파일러 2 × 최적화 3 = 여섯 벌**을 돌려야
> 「갈린다」가 보인다. 한 벌짜리 답은 **정반대 결론**이 된다.
> ★ **멤버 값과 바이트를 갈라서 답해라** — 멤버 값은 여섯 벌 전부 같고, 갈리는 것은 **바이트**뿐이다.
> 선행 — [11번 형제](../11-bitwise-operations-and-shifts/) · [22번 형제](../22-struct-padding-and-alignment/) · [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1·3·4·5·7·8)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **3번과 4번은 「한 줄의 답」이 없다** — **여섯 벌의 격자**를 적어야 답이다.
  한 벌만 적으면 틀린 것이 아니라 **질문을 못 읽은 것**이다.
- ★ **바이트를 16진으로 적고, 갈리는 자리에 표시**해 두면 4번이 쉬워진다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 사실은 다섯 층 중 어느 칸인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 플래그 다섯 개를 비트로 선언하고 크기와 바이트를 재면 (예측) ★★★ 이 주제의 축

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

- `struct Flags` 와 `struct Plain` 의 `sizeof` 는 각각 얼마인가?
- `_Alignof` 는 각각 얼마인가?
- 첫 바이트는 16진으로 무엇이고, 그것을 **2진으로 펼치면** 어느 자리에 어느 멤버가 들어가 있는가?
- ★ `kind` 는 3비트인데 **9** 를 넣으면 읽히는 값은 무엇인가?
- ★ 그 일은 **UB 인가 아닌가** — 어느 층인가?
- ★ 비트 합이 8 인데 `sizeof` 가 그 값이 된 이유는 무엇인가?
- ★★ 「비트필드를 쓰면 작아진다」가 여기서 **얼마나** 작아졌는가? 그 차이가 언제부터 값이 나는가?

### 2. 그 자리에서 컴파일러가 하는 말 (경계) ★★

- 1번을 `-Wall -Wextra -pedantic` 으로 컴파일하면 **경고가 몇 건** 나는가?
- 그 경고의 **플래그 이름**은 무엇인가?
- ★★ 진단 문구가 그 멤버의 타입을 무엇이라고 부르는가 — **선언과 같은가 다른가**?
- ★ 그 이름이 **무엇을 알려 주는가**(왜 그 이름이 그 자리에 나오는가)?
- ★ **변수**를 대입해도 같은 경고가 나는가?

### 3. 12비트만 선언한 구조체를 두 가지 방식으로 채우면 (예측) ★★★ 본체

**(가)** 먼저 `memset(0xFF)` 로 전부 1 로 만든 뒤 두 멤버를 대입한다.

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

**(나)** 이번에는 **초기화를 하지 않고** 두 멤버만 대입한다(앞서 스택을 `0xFF` 로 더럽힌다).

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

- (가)의 네 바이트는 무엇인가? gcc 와 clang, `-O0` 과 `-O2` 에서 **같은가 다른가**?
- ★★ (나)를 **gcc/clang × `-O0`/`-O2` 네 벌**로 빌드하면 네 바이트가 어떻게 되는가?
- ★★★ **갈린다면 무엇이 갈린 축인가** — 컴파일러인가, 최적화 수준인가?
- ★ 갈리는 이유를 **코드 모양**으로 설명하면? (컴파일러가 대입을 어떻게 처리하는가)
- ★ (가)와 (나)의 차이는 소스에서 **무엇 하나**인가? 왜 그 하나가 결과를 가르는가?
- ★ **같은 바이너리**를 여러 번 돌리면 바이트가 흔들리는가?
- 이 사실은 다섯 층 중 **어느 칸**인가?
- ★★ 이 구조체를 `memcmp` 로 비교하거나 `fwrite` 로 저장하면 무엇이 문제가 되는가?

### 4. 11번 편이 「갈린다」고 적은 구조체를 여섯 벌로 다시 던지면 (예측) ★★★ 전제를 뒤집는 자리

[11번 형제](../11-bitwise-operations-and-shifts/)는 같은 소스에서
**gcc 가 `D3 78 00 00`, clang 이 `D3 08 00 00`** 을 냈다고 적었다. 그 구조체를 그대로 다시 던진다.

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

- **gcc `-O0`/`-O1`/`-O2`** 와 **clang `-O0`/`-O1`/`-O2`** 여섯 벌의 바이트는 각각 무엇인가?
- ★★★ 11번 편의 수치는 **재현되는가** — 재현된다면 **어느 벌에서**인가?
- ★★★ 「**gcc 와 clang 이 갈린다**」는 진술은 **맞는가 틀린가**? 고쳐 쓴다면 어떻게 쓰겠는가?
- ★ 여섯 벌에서 **멤버 값**(`a`·`b`·`c`·`d`)은 갈리는가?
- ★ 11번 편은 `-O` 를 적지 않았다. 그때 실제로 쓰인 수준은 무엇인가?
- ★ 이 문항이 말하는 **실험 설계의 교훈**은 무엇인가?

### 5. `int`·`signed int`·`unsigned int` 비트필드에 각각 7 을 넣으면 (예측) ★★

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

- 세 멤버를 읽으면 각각 무엇이 찍히는가?
- ★★ `int x : 3` 은 **어느 쪽으로** 잡혔는가? 그 사실은 **어느 층**인가?
- ★ 경고는 **몇 건**이고 어느 멤버에 붙는가? 붙지 않은 멤버는 왜 안 붙었는가?
- ★ **3** 을 넣으면 셋이 어떻게 되는가? 그것이 왜 위험한가?
- ★ `unsigned int x : 3` 과 `signed int x : 3` 이 담을 수 있는 값의 범위는 각각 무엇인가?

### 6. 그 선택을 플래그로 되돌릴 수 있나 (경계) ★★

- gcc 에 **`-funsigned-bitfields`** 를 주면 5번의 답이 바뀌는가?
- ★★★ clang 에 같은 플래그를 주면 어떻게 되는가 — **값이 바뀌는가, 빌드가 깨지는가, 아무 일도 안 나는가**?
- ★★ clang 이 내는 **그 한 줄**은 무엇을 뜻하는가? 그것을 보려면 어느 플래그가 필요한가?
- ★ `cc exit` 는 얼마인가? 「경고가 났다」와 「반영됐다」가 여기서 어떻게 어긋나는가?
- ★ 그래서 **이식 가능한 답**은 무엇인가?

### 7. 비트필드에 `&` 와 `sizeof` 를 쓰면 (예측) ★

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

- gcc 와 clang 의 출력은 각각 무엇인가? **`cc exit`** 는 얼마인가?
- ★ 세 줄 중 **한 줄은 진단이 두 개** 나온다. 어느 줄이고 왜 그런가?
- ★★ 이 제약은 다섯 층 중 **어느 칸**인가? **왜 그런 제약이 있는가**?
- ★ `offsetof` 는 비트필드 멤버에 쓸 수 있는가?
- ★ 그 멤버의 주소가 꼭 필요해졌다면 설계를 어떻게 고쳐야 하는가?

### 8. 폭 3 과 폭 32 짜리 비트필드에서 각각 0 에서 1 을 빼면 (예측) ★★

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

- `_Generic` 이 두 멤버의 식 타입을 각각 무엇이라고 답하는가?
- ★★ `s.small - 1` 과 `s.full - 1` 은 각각 무엇이 찍히는가?
- ★★ **왜 갈리는가** — 무엇이 그 갈림을 결정하는가?
- ★ `< 0` 비교 둘 중 **한쪽에만** 경고가 붙는다. 어느 쪽이고 왜인가?
- ★ 이 규칙의 정본은 어느 주제인가?
- ★★ 「`unsigned` 로 선언했으니 식에서도 `unsigned` 겠지」가 왜 틀렸는가?

### 9. 폭 0 비트필드와 이름 없는 폭 2 는 무엇이 다른가 (경계) ★★

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

- 세 구조체의 `sizeof` 와 바이트는 각각 무엇인가?
- ★★ **폭 0** 이 하는 일과 **이름 없는 폭 2** 가 하는 일은 어떻게 다른가?
- ★ 폭 0 비트필드에 **이름을 주면** 어떻게 되는가?
- ★ gcc 와 clang 이 여기서도 갈리는가?
- ★ 폭 0 을 **일부러 쓰는** 상황은 어떤 때인가?

### 10. 「잘린다」는 왜 UB 가 아닌가 (왜) ★★

- `f.kind = 9` 가 **UB 가 아니라 변환**인 이유는 무엇인가?
- ★★ 그러면 이 주제에서 **UB 칸에 들어갈 것**은 무엇인가? 그 칸이 **왜 얇은가**?
- ★ `struct T { unsigned a : 40; };` 는 무엇이 다른가 — 에러인가 변환인가?
- ★ **미사용 비트를 읽는 것** 자체는 UB 인가? 무엇이 틀린 것인가?
- ★ [11번 형제](../11-bitwise-operations-and-shifts/)는 **UB 칸이 두꺼운** 주제였다. 왜 여기서는 얇아졌는가?

### 11. 다섯 층과 무게중심 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / 구현 정의 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- **비어 있는 칸**은 무엇인가?
- ★★ **가장 두꺼운 칸**과 **두 번째로 두꺼운 칸**은 각각 무엇인가?
- ★★ **도구가 침묵하는 자리**를 층마다 하나씩 대면?
- ★ [22번 형제](../22-struct-padding-and-alignment/)의 「패딩 바이트의 값은 미명시」와 **무엇이 같고 무엇이 다른가**?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

- **마스크와 시프트로 손수 비트를 다루는 법**은 어느 주제가 정본인가?
- **정수 승격 규칙 자체**는 어느 주제가 정본인가?
- **구조체 패딩·정렬**과 **`sizeof`·`offsetof` 라는 도구**는 각각 어느 주제가 정본인가?
- ★★ **파일·패킷 포맷**을 그릴 때 비트필드를 쓰면 안 되는 이유를 한 줄로 대면?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?
- ★ **열거 상수 + 마스크**로 플래그를 담는 방식은 어느 주제가 정본이고, 언제 그쪽을 고르는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
