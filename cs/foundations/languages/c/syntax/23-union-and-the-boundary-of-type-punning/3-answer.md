# c/syntax/23 — `union` 과 타입 펀닝의 경계: 「**union 은 동시에 담는 상자가 아니라 같은 바이트를 겹쳐 보는 창이다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과 **clang 18.1.3** ·
> **g++ 13.3.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s23a.c`·`s23b.c`·`s23d.c`·`s23e.c`·`s23f.c` 와 `s23g.cpp`·`s23h.cpp` 다.\
> ★ 덤프를 결정적으로 만들려고 `s23e.c`·`s23f.c` 는 **`memset` 으로 먼저 채운 뒤** 멤버를 썼다.\
> ★★ 4번은 **한 수준만 돌리지 않았다** — `-O0`\~`-O3` 네 벌 × 두 컴파일러 + `-fno-strict-aliasing` 두 벌 = **열 벌**이다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 주소 · `%p` · 스택에 남아 있던 값 | ★★ **바이트 격자**(`44 43 42 41` · `41 aa aa aa aa aa aa aa`) |
> | 초기화하지 않은 칸의 구체적 값 | ★★ **`sizeof` / `_Alignof` / `offsetof`** (8 · 16 · 전부 0) |
> | `memcmp` 반환값의 **크기**(부호만 규정이다) | ★★★ **최적화 수준별 갈림**(gcc `-O2` 부터 · clang `-O1` 부터) |
> | — | ★★ **진단 본문 · 플래그 이름 · 종료 코드**(`cc exit=0`/`1` · `run exit=0`) |
> | — | ★ **비트 격자**(`0 01111111 1000…`)와 `0x3fc00000` |
>
> ★ **이 문서가 실린 블록은 전부 캡처 파일을 그대로 붙인 것이다** — 손으로 옮겨 적은 출력이 하나도 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 같은 멤버 셋을 union 과 struct 에 넣고 재면 — **union 8 · struct 16, offset 은 전부 0** ★★★

**출력**

```c
/* s23a.c */
#include <stdio.h>
#include <stddef.h>

union U { int i; char c[4]; double d; };
struct S { int i; char c[4]; double d; };   /* 같은 멤버를 struct 로 */

int main(void) {
    printf("union  sizeof=%zu _Alignof=%zu   offsets: i=%zu c=%zu d=%zu\n",
           sizeof(union U), _Alignof(union U),
           offsetof(union U, i), offsetof(union U, c), offsetof(union U, d));
    printf("struct sizeof=%zu _Alignof=%zu   offsets: i=%zu c=%zu d=%zu\n",
           sizeof(struct S), _Alignof(struct S),
           offsetof(struct S, i), offsetof(struct S, c), offsetof(struct S, d));

    union U u;
    u.i = 0x41424344;                       /* 마지막에 쓴 멤버 = i */
    printf("\nu.i = 0x%08x 를 쓴 뒤 바이트를 보면 : ", u.i);
    for (int k = 0; k < 4; k++) printf("%02x ", (unsigned char)u.c[k]);
    printf("  <- ★ 엔디언이 드러난다\n");
    printf("u.c[0]='%c' u.c[3]='%c'\n", u.c[0], u.c[3]);

    u.d = 1.0;                              /* 이제 마지막에 쓴 멤버 = d */
    printf("\nu.d = 1.0 을 쓰고 나면 u.i 는 %d (0x%08x) — i 는 더 이상 의미가 없다\n",
           u.i, (unsigned)u.i);
    printf("전체 8바이트 : ");
    const unsigned char *b = (const unsigned char *)&u;
    for (size_t k = 0; k < sizeof u; k++) printf("%02x ", b[k]);
    printf("\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s23a.c -o x ; ./x (cc exit=0 · run exit=0) =====
union  sizeof=8 _Alignof=8   offsets: i=0 c=0 d=0
struct sizeof=16 _Alignof=8   offsets: i=0 c=4 d=8

u.i = 0x41424344 를 쓴 뒤 바이트를 보면 : 44 43 42 41   <- ★ 엔디언이 드러난다
u.c[0]='D' u.c[3]='A'

u.d = 1.0 을 쓰고 나면 u.i 는 0 (0x00000000) — i 는 더 이상 의미가 없다
전체 8바이트 : 00 00 00 00 00 00 f0 3f 
```

**왜 그런가**

```text
   struct S { int i; char c[4]; double d; };     sizeof 16 · _Alignof 8
   +--------+--------+----------------+
   |   i    |  c[4]  |       d        |     i@0  c@4  d@8
   +--------+--------+----------------+
   0        4        8                16      ★ 자리를 나눠 갖는다

   union U { int i; char c[4]; double d; };     sizeof 8 · _Alignof 8
   +----------------+
   |       d        |     d 는 여덟 칸
   +--------+-------+
   |   i    |       |     i 는 앞 네 칸
   +--------+-------+
   |  c[4]  |       |     c 도 앞 네 칸
   +--------+-------+
   0        4       8      ★ 자리를 겹쳐 쓴다 — offset 이 전부 0
```

- **`sizeof(union U)` 가 8** 이다 — **가장 큰 멤버**(`double`)를 담을 만큼. struct 쪽은 **16** 이다.
- **`_Alignof` 는 양쪽 다 8** 이다 — **가장 엄한 멤버의 정렬**을 따르는 것은 struct 와 union 이 같다.
- ★★ **union 의 `offsetof` 는 셋 다 0** 이다. struct 는 `0 / 4 / 8` 로 갈린다.\
  **이 한 줄이 union 의 정의**다 — 「겹친다」를 수치로 말하면 이것이다.

```text
   u.i = 0x41424344 을 쓴 직후

   offset  0    1    2    3
         +----+----+----+----+
         | 44 | 43 | 42 | 41 |
         +----+----+----+----+
          'D'  'C'  'B'  'A'      ★ u.c[0]='D' · u.c[3]='A'

   수로 쓴 차례      41 42 43 44   (큰 자리부터)
   메모리의 차례     44 43 42 41   (작은 자리부터)  -> 리틀 엔디언
```

- ★★★ **`u.c[0]` 이 `'D'`, `u.c[3]` 이 `'A'`** 다. 수로 쓸 때의 차례와 **거꾸로** 놓였다 —\
  **리틀 엔디언**이고 이것은 ★ **구현 정의**다. 표준이 정한 것이 아니다.
- ★★ **`u.d = 1.0` 을 쓰면 `u.i` 가 0** 이 된다. `1.0` 의 여덟 바이트가 **`00 00 00 00 00 00 f0 3f`** 라\
  **`i` 가 보는 앞 네 칸이 전부 0** 이 되었기 때문이다.\
  ★ `i` 라는 멤버가 없어진 것이 아니라 **바이트가 덮인 것**이다. 이것이 「**동시에 담지 않는다**」의 실측이다.

| 무엇을 물었나 | `union U` | `struct S` |
|---|---|---|
| `sizeof` | **8** | **16** |
| `_Alignof` | 8 | 8 |
| `offsetof(i)` / `(c)` / `(d)` | ★ **0 / 0 / 0** | 0 / 4 / 8 |
| 한 멤버에 쓰면 | ★ **다른 멤버가 바뀐다** | 다른 멤버는 그대로다 |

### 2. `float` 한 값을 넣고 정수 멤버로 읽으면 — **`0x3fc00000`, `memcpy` 와 같다** ★★★ 본체

**출력**

```c
/* s23b.c */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

union FB { float f; uint32_t u; };

static void bits(uint32_t u) {
    for (int k = 31; k >= 0; k--) {
        putchar((u >> k) & 1 ? '1' : '0');
        if (k == 31 || k == 23) putchar(' ');
    }
}

int main(void) {
    union FB v = { .f = 1.5f };            /* float 를 넣고 */
    printf("f = %.6f  ->  u = 0x%08x\n", v.f, v.u);   /* uint32 로 읽는다 */
    printf("  부호 지수      가수\n  ");
    bits(v.u);
    printf("\n");

    uint32_t m;
    memcpy(&m, &v.f, sizeof m);            /* 같은 일을 memcpy 로 */
    printf("memcpy 로 읽으면 : 0x%08x   (union 과 같은가: %d)\n", m, m == v.u);

    v.u = 0x40490fdb;                      /* 거꾸로 — 비트를 넣고 float 로 읽는다 */
    printf("\nu = 0x40490fdb  ->  f = %.7f\n", v.f);

    union FB nan = { .u = 0x7fc00000 };
    printf("u = 0x7fc00000 ->  f = %f\n", nan.f);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s23b.c -o x ; ./x (cc exit=0 · run exit=0) =====
f = 1.500000  ->  u = 0x3fc00000
  부호 지수      가수
  0 01111111 10000000000000000000000
memcpy 로 읽으면 : 0x3fc00000   (union 과 같은가: 1)

u = 0x40490fdb  ->  f = 3.1415927
u = 0x7fc00000 ->  f = nan
```

**왜 그런가**

```text
   1.5f 의 표현

     부호   지수 (8비트)     가수 (23비트)
     +---+ +----------+ +-------------------------+
     | 0 | | 01111111 | | 1000000000000000000000 0|      = 0x3fc00000
     +---+ +----------+ +-------------------------+
       ^        ^                ^
      양수   127 = 지수 0      1.1(2진) = 1.5

   같은 네 바이트를 두 이름으로 본다
   +----+----+----+----+
   | 00 | 00 | c0 | 3f |      메모리 (리틀 엔디언)
   +----+----+----+----+
     v.f 로 보면  1.500000
     v.u 로 보면  0x3fc00000
     memcpy 로 옮겨 읽어도 ★ 같은 값
```

- **`0x3fc00000`** 이다. 지수 칸이 **127** 인 것은 **편향(bias) 127 을 더한 값**이라 **실제 지수는 0** 이라는 뜻이고,\
  가수가 `1000…` 이라 **1.1(2진) = 1.5** 가 된다. 표현 자체의 정본은 [`data-representation/`](../../../../data-representation/)다.
- ★★ **`memcpy` 로 옮겨 읽은 값이 union 과 같았다**(`(union 과 같은가: 1)`).\
  **같은 바이트를 같은 타입으로 해석했으니 당연**하고, **그래서 이 대조는 「둘이 같은 일」이라는 증거가 못 된다**(3번 참조).
- ★ **거꾸로도 된다** — `0x40490fdb` 를 넣으면 **3.1415927**, `0x7fc00000` 을 넣으면 **`nan`** 이다.\
  「수가 아닌 비트 패턴」도 그대로 들어간다.
- ★★ **경고 0건 · `cc exit=0` · `run exit=0`** 이다. **C 에서 union 을 통한 펀닝은 허용**이라\
  컴파일러가 진단할 것이 없다. ★ **이 「0건」은 4번의 「0건」과 뜻이 정반대**다 —\
  여기서는 **적법해서** 0건이고, 4번에서는 **위반인데도** 0건이다.

### 3. 같은 일을 `memcpy` 로 하면 무엇이 달라지나 — **값은 같고 규칙이 다르다** ★★

**출력**

- 2번 블록의 `memcpy 로 읽으면 : 0x3fc00000   (union 과 같은가: 1)` 한 줄이 이 질문의 출력이다.
- 8번 블록의 g++ 실행 결과도 **같은 `0x3fc00000`** 이다.

**왜 그런가**

```text
   (가) union 을 거친다                    (나) memcpy 로 옮긴다
   +-------------------+                   +--------+          +--------+
   | union FB { f; u } |                   | float  |  바이트   | uint32 |
   +-------------------+                   +--------+  --복사-> +--------+
   같은 바이트를 두 이름으로 본다            ★ 다른 객체로 바이트를 옮긴다

           C          C++
   (가)   허용    ★ 활성 멤버가 아닌 것을 읽는 것
   (나)   허용       허용
                     ^^^^ 어느 언어에서도 안전한 쪽
```

- ★★★ **값이 같은 것은 당연하다.** 둘 다 **같은 네 바이트를 `uint32_t` 로 해석**했다.\
  ★ **그래서 「돌려 봤더니 같더라」는 여기서 아무것도 증명하지 못한다** — 갈리는 것은 **언어가 무엇을 약속했나**이고,\
  약속은 **출력으로 관찰되지 않는다.**
- **C 에서는 둘 다 허용**이다. union 을 통해 다른 멤버를 읽는 것은 **바이트를 그 타입으로 다시 해석하는 것**으로 규정돼 있다.
- ★★ **C++ 에서는 (가)가 「활성 멤버가 아닌 것을 읽는 것」** 이다. 실행 값은 같아도(8번) **모형이 다르다.**
- ★ **두 언어에서 같이 쓸 헤더에는 `memcpy`** 다. 최적화가 대개 지워 주므로 비용 걱정도 적다\
  (★ **그 비용은 이 문서가 재지 않았다**).

### 4. 같은 칸을 두 타입의 포인터로 건드리고 여러 수준으로 돌리면 — **gcc 는 `-O2`, clang 은 `-O1` 부터 갈린다** ★★★ 본체

**출력**

```c
/* s23d.c */
#include <stdio.h>
#include <stdint.h>

/* 같은 메모리를 unsigned 와 float 두 타입으로 접근한다 — 엄격한 앨리어싱 위반 */
static unsigned punned(unsigned *u, float *f) {
    *u = 1;
    *f = 0.0f;        /* 위의 *u 와 같은 바이트를 덮어쓴다 */
    return *u;        /* 컴파일러가 「안 겹친다」고 믿으면 1 을 그대로 돌려준다 */
}

int main(void) {
    unsigned x = 0;
    unsigned r = punned(&x, (float *)&x);
    printf("반환값 = %u · 메모리의 실제 값 = %u\n", r, x);
    return 0;
}
```

```text
===== 엄격한 앨리어싱 위반을 최적화 수준별로 — 한 줄 = 한 벌 (exit=0) =====
gcc   -O0                    : 반환값 = 0 · 메모리의 실제 값 = 0
gcc   -O1                    : 반환값 = 0 · 메모리의 실제 값 = 0
gcc   -O2                    : 반환값 = 1 · 메모리의 실제 값 = 0
gcc   -O3                    : 반환값 = 1 · 메모리의 실제 값 = 0
gcc   -O2 -fno-strict-aliasing : 반환값 = 0 · 메모리의 실제 값 = 0
clang -O0                    : 반환값 = 0 · 메모리의 실제 값 = 0
clang -O1                    : 반환값 = 1 · 메모리의 실제 값 = 0
clang -O2                    : 반환값 = 1 · 메모리의 실제 값 = 0
clang -O3                    : 반환값 = 1 · 메모리의 실제 값 = 0
clang -O2 -fno-strict-aliasing : 반환값 = 0 · 메모리의 실제 값 = 0
```

**왜 그런가**

```text
   punned(&x, (float *)&x)   —  두 포인터가 ★ 같은 칸을 가리킨다

   소스가 시키는 일                    컴파일러가 믿어도 되는 것
   +----------------------+            +-------------------------------+
   | *u = 1;              |            | unsigned* 와 float* 는         |
   | *f = 0.0f;  (같은 칸) |            | 타입이 다르다 -> ★ 안 겹친다    |
   | return *u;           |            | -> *f 쓰기는 *u 를 못 건드린다 |
   +----------------------+            | -> return 은 그냥 1            |
            |                          +-------------------------------+
            v                                        |
      메모리의 실제 값 0                              v
                                              반환값 ★ 1

   gcc    -O0 0 · -O1 0 · ★ -O2 1 · -O3 1
   clang  -O0 0 · ★ -O1 1 · -O2 1 · -O3 1
   둘 다  -O2 -fno-strict-aliasing -> 0
```

- ★★★ **갈리는 지점이 컴파일러마다 다르다.** gcc 는 `-O2` 부터, **clang 은 `-O1` 부터** 반환값이 **1** 이 된다.\
  「`-O2` 만 조심하면 된다」가 **틀렸다는 실측**이다.
- ★★ **메모리의 실제 값은 열 벌 전부 0** 이다. 바이트는 제대로 덮였고, **반환값만 옛 값을 들고 있다** —\
  컴파일러가 **`*f = 0.0f` 가 `*u` 를 건드릴 리 없다고 믿고** 다시 읽지 않은 것이다.
- ★ **`-fno-strict-aliasing` 으로 둘 다 0 으로 돌아온다.** **최적화가 만든 차이**라는 증거이고,\
  동시에 **그 최적화를 끄지 않은 코드는 UB 를 깔고 있다**는 뜻이다.
- ★★★ **1번·2번의 union 과 소스가 거의 같은데 층이 다르다.** union 은 **하나의 객체**를 두 이름으로 보는 것이고,\
  포인터 캐스트는 **서로 다른 타입의 두 lvalue 로 같은 저장소를 건드리는 것**이다.\
  ★ 규칙 전체의 정본은 목록의 **55번 주제**, 캐스트가 무엇을 하는 표현인지는 [05번 형제](../05-explicit-casts-and-pointer-conversions/)다.

| 벌 | 반환값 | 메모리의 실제 값 |
|---|---|---|
| gcc `-O0` · `-O1` | **0** | 0 |
| gcc `-O2` · `-O3` | ★ **1** | 0 |
| clang `-O0` | **0** | 0 |
| clang `-O1` · `-O2` · `-O3` | ★★ **1** | 0 |
| 둘 다 `-fno-strict-aliasing` | **0** | 0 |

### 5. 그 위험을 컴파일러와 sanitizer 에게 물어보면 — **clang 은 0건, sanitizer 는 `run exit=0`** ★★★

**출력**

```c
/* s23d.c */
#include <stdio.h>
#include <stdint.h>

/* 같은 메모리를 unsigned 와 float 두 타입으로 접근한다 — 엄격한 앨리어싱 위반 */
static unsigned punned(unsigned *u, float *f) {
    *u = 1;
    *f = 0.0f;        /* 위의 *u 와 같은 바이트를 덮어쓴다 */
    return *u;        /* 컴파일러가 「안 겹친다」고 믿으면 1 을 그대로 돌려준다 */
}

int main(void) {
    unsigned x = 0;
    unsigned r = punned(&x, (float *)&x);
    printf("반환값 = %u · 메모리의 실제 값 = %u\n", r, x);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -Wstrict-aliasing=2 -O2 s23d.c -o x (cc exit=0) =====
s23d.c: In function ‘main’:
s23d.c:13:38: warning: dereferencing type-punned pointer will break strict-aliasing rules [-Wstrict-aliasing]
   13 |     unsigned r = punned(&x, (float *)&x);
      |                                      ^~
```

```text
===== 도구가 잡나 — 경고 수(grep -c 'warning:')와 sanitizer 실행 결과 (exit=0) =====
gcc   -O0 -Wstrict-aliasing=2 : warning: 0건
gcc   -O2 -Wstrict-aliasing=2 : warning: 1건
clang -O0 -Wstrict-aliasing=2 : warning: 0건
clang -O2 -Wstrict-aliasing=2 : warning: 0건
gcc   -O2 -fsanitize=undefined,address : 반환값 = 1 · 메모리의 실제 값 = 0 (run exit=0)
```

**왜 그런가**

```text
   누가 무엇을 보나

   gcc   -O0 : 깨지지 않는다        경고 0건
   gcc   -O2 : ★ 깨진다             경고 1건   <- 유일하게 짝이 맞는 칸
   clang -O0 : 깨지지 않는다        경고 0건
   clang -O1 : ★★ 깨진다            (경고를 물어볼 칸이 표에 없다 — -O2 에서도 0건)
   clang -O2 : ★★ 깨진다            경고 ★ 0건
   UBSan + ASan : 출력 1 · run exit=0   <- ★★★ 초록 신호
```

- ★ **gcc 의 `-Wstrict-aliasing=2` 는 `-O2` 에서만 1건**이고 **`-O0` 에서는 0건**이다.\
  **경고가 최적화 분석 위에 얹혀 있어서** 최적화를 안 켜면 볼 수가 없다.\
  진단 본문은 「`dereferencing type-punned pointer will break strict-aliasing rules`」다.
- ★★★ **clang 은 `-O0`·`-O2` 둘 다 0건**이다. **정작 `-O1` 부터 깨지는 쪽이 clang** 이니\
  「**가장 일찍 깨지는 컴파일러가 가장 조용하다**」가 이 주제의 결론 한 줄이다.
- ★★★ **UBSan 과 ASan 을 같이 켜도 아무 말이 없다** — 출력은 **깨진 값 1** 그대로이고 **`run exit=0`** 이다.\
  ★ 못 잡는 이유는 한 문장이다 — **실행 시점에 관찰할 사건이 없다.**\
  잘못된 주소를 읽은 것도, 범위를 넘은 연산을 한 것도 아니다. **컴파일러가 이미 다르게 번역해 버린 뒤**다.
- ★★ **그래서 이 위반을 볼 수 있는 창은 하나뿐**이다 — **같은 소스를 여러 최적화 수준으로 빌드해 값을 나란히 찍는 것.**\
  한 벌만 돌리면 **`-O0` 이 「정상」을 보여 주고 끝난다.**

| 물어본 것 | gcc `-O0` | gcc `-O2` | clang `-O0` | clang `-O2` |
|---|---|---|---|---|
| `-Wstrict-aliasing=2` 경고 수 | 0건 | ★ **1건** | 0건 | ★★ **0건** |
| 값이 깨지나 | 아니오 | **예** | 아니오 | **예** |
| UBSan+ASan | — | ★★★ **0건 · `run exit=0`** | — | — |

### 6. 앞머리가 같은 두 구조체를 한 union 에 넣으면 — **`tag` 는 건너 읽어도 된다** ★★

**출력**

```c
/* s23e.c */
#include <stdio.h>
#include <string.h>

struct A { int tag; int    x; };       /* 앞머리 int tag 가 공통 */
struct B { int tag; double y; };
union V { struct A a; struct B b; };   /* ★ 한 union 안에 보여야 규칙이 선다 */

static void dump(const char *tag, const union V *v) {
    const unsigned char *b = (const unsigned char *)v;
    printf("%-14s", tag);
    for (size_t k = 0; k < sizeof *v; k++) printf(" %02x", b[k]);
    printf("\n");
}

int main(void) {
    union V v;
    memset(&v, 0, sizeof v);                       /* 덤프를 결정적으로 */
    v.a = (struct A){ .tag = 7, .x = 42 };
    dump("a 로 쓴 뒤", &v);
    printf("a 로 쓰고 b 로 읽기 : v.b.tag = %d   <- ★ 공통 초기 시퀀스라 허용된다\n", v.b.tag);

    memset(&v, 0, sizeof v);
    v.b = (struct B){ .tag = 9, .y = 2.5 };
    dump("b 로 쓴 뒤", &v);
    printf("b 로 쓰고 a 로 읽기 : v.a.tag = %d\n", v.a.tag);
    printf("v.a.x 를 읽으면 = %d  <- 공통 부분이 아니다 (B 에서는 패딩 자리다)\n", v.a.x);

    printf("\nsizeof A=%zu B=%zu V=%zu · offsetof(B,y)=%zu\n",
           sizeof(struct A), sizeof(struct B), sizeof(union V),
           (size_t)((char *)&v.b.y - (char *)&v.b));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s23e.c -o x ; ./x (cc exit=0 · run exit=0) =====
a 로 쓴 뒤  07 00 00 00 2a 00 00 00 00 00 00 00 00 00 00 00
a 로 쓰고 b 로 읽기 : v.b.tag = 7   <- ★ 공통 초기 시퀀스라 허용된다
b 로 쓴 뒤  09 00 00 00 00 00 00 00 00 00 00 00 00 00 04 40
b 로 쓰고 a 로 읽기 : v.a.tag = 9
v.a.x 를 읽으면 = 0  <- 공통 부분이 아니다 (B 에서는 패딩 자리다)

sizeof A=8 B=16 V=16 · offsetof(B,y)=8
```

**왜 그런가**

```text
   union V { struct A a; struct B b; };            sizeof V = 16

   struct A { int tag; int    x; }   sizeof 8
   +--------+--------+
   |  tag   |   x    |
   +--------+--------+
   0        4        8

   struct B { int tag; double y; }   sizeof 16      offsetof(y) = 8
   +--------+--------+----------------+
   |  tag   | ★ 패딩 |       y        |
   +--------+--------+----------------+
   0        4        8                16

   |<-공통->|          ★ 공통 초기 시퀀스는 tag 하나뿐이다
```

- ★★ **`a` 로 쓰고 `v.b.tag` 를 읽어 7**, **`b` 로 쓰고 `v.a.tag` 를 읽어 9** 가 나왔다.\
  이것이 「**공통 초기 시퀀스**」 규칙이고, **마지막에 쓴 멤버가 아닌 것을 읽는데도 뜻이 서는 유일한 자리**다.
- ★★ **공통이 아닌 자리는 다르다** — `b` 로 쓴 뒤 `v.a.x` 는 **0** 이었는데,\
  그 네 바이트는 `struct B` 에서 **`y` 를 8 에 놓으려고 생긴 패딩**이다(`offsetof(B, y) = 8`).\
  ★ **패딩 자리를 읽은 값에는 뜻이 없다.** 이 실측에서 0 으로 보인 것은 **`memset` 으로 먼저 채웠기 때문**이고,\
  **패딩 값이 미명시라는 것**의 정본은 [22번 형제](../22-struct-padding-and-alignment/)다.
- ★ **`int tag` 와 `short tag` 였다면 규칙이 서지 않는다.** 「앞에 있다」가 아니라 **「같은 타입이 같은 차례로」** 다.
- ★★ **규칙이 서려면 그 union 선언이 보여야 한다.** 두 구조체만 따로 알고 포인터로 건너뛰는 것은\
  이 규칙이 아니라 **4번의 UB** 다.

| 무엇을 물었나 | 값 |
|---|---|
| `a` 로 쓰고 `v.b.tag` | **7** |
| `b` 로 쓰고 `v.a.tag` | **9** |
| `b` 로 쓰고 `v.a.x` | 0 — ★ **B 의 패딩 자리라 뜻이 없다** |
| `sizeof A` / `B` / `V` | 8 / **16** / 16 |
| `offsetof(B, y)` | **8** |

### 7. union 을 네 가지 방식으로 만들면 — **뒤 일곱 칸은 미명시다** ★★

**출력**

```c
/* s23f.c */
#include <stdio.h>
#include <string.h>

union U { char c; int i; double d; };

static void dump(const char *tag, const union U *u) {
    const unsigned char *b = (const unsigned char *)u;
    printf("%-16s", tag);
    for (size_t k = 0; k < sizeof *u; k++) printf(" %02x", b[k]);
    printf("\n");
}

int main(void) {
    union U a = { 'A' };              /* 첫 멤버가 초기화된다 */
    union U b = { .i = 0x41424344 };  /* 지정 초기자로 고른다 */
    union U c = { 0 };
    union U d;
    memset(&d, 0xAA, sizeof d);
    d.c = 'A';                        /* 멤버 하나만 쓴다 */

    printf("sizeof(union U) = %zu · _Alignof = %zu\n\n", sizeof a, _Alignof(union U));
    dump("a = { 'A' }", &a);
    dump("b = { .i = X }", &b);
    dump("c = { 0 }", &c);
    dump("d: memset+d.c", &d);
    printf("\n★ d 의 뒤 7바이트는 「미명시」다 — 멤버 하나를 써도 나머지는 정해지지 않는다\n");
    printf("a.c = '%c' · b.i = 0x%08x · c.c = %d\n", a.c, b.i, c.c);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s23f.c -o x ; ./x (cc exit=0 · run exit=0) =====
sizeof(union U) = 8 · _Alignof = 8

a = { 'A' }      41 00 00 00 00 00 00 00
b = { .i = X }   44 43 42 41 00 00 00 00
c = { 0 }        00 00 00 00 00 00 00 00
d: memset+d.c    41 aa aa aa aa aa aa aa

★ d 의 뒤 7바이트는 「미명시」다 — 멤버 하나를 써도 나머지는 정해지지 않는다
a.c = 'A' · b.i = 0x41424344 · c.c = 0
```

**왜 그런가**

```text
   union U { char c; int i; double d; };     sizeof 8 · _Alignof 8

   a = { 'A' }         41 | 00 00 00 00 00 00 00
                       ^^ 첫 멤버 c 가 초기화된다

   b = { .i = X }      44 43 42 41 | 00 00 00 00
                       ^^^^^^^^^^^ 지정 초기자로 i 를 골랐다 (리틀 엔디언)

   c = { 0 }           00 00 00 00 00 00 00 00

   d  memset(0xAA) 뒤 d.c = 'A'
                       41 | aa aa aa aa aa aa aa
                       ^^   ^^^^^^^^^^^^^^^^^^^^
                       쓴 칸  ★ 안 쓴 칸 — 값이 정해지지 않는다
```

- **초기자가 하나면 첫 멤버**가 초기화된다 — `a = { 'A' }` 가 `c` 를 채웠다.
- ★ **다른 멤버를 고르려면 지정 초기자**가 필요하다(`{ .i = … }`). **C99부터**다.\
  앞 네 칸이 `44 43 42 41` 인 것은 1번과 같은 **리틀 엔디언** 때문이다.
- ★★★ **`d` 의 뒤 일곱 칸이 `aa` 로 남았다.** 멤버 하나를 썼다고 나머지가 0 이 되지 않는다 — 「**미명시**」 층이다.
- ★★ **`a`·`b`·`c` 에서 뒤가 0 으로 보이는 것은 「관찰」이지 「보장」이 아니다.**\
  **이 컴파일러가 그렇게 한 것**이고, 다른 구현·다른 플래그에서 같으리라는 약속이 없다.\
  ★ 0 이 필요하면 **`= { 0 }` 이나 `memset` 을 직접 쓴다.**
- ★ 그래서 **`memcmp` 로 union 두 개를 비교하면 안 된다** — **안 쓴 칸이 끼어든다.**\
  같은 함정을 구조체에서 **패딩**으로 보여 주는 것이 [22번 형제](../22-struct-padding-and-alignment/)다.

### 8. 같은 펀닝을 C++ 로 옮기면 — **값은 같고 모형이 다르다** ★★

**출력**

```cpp
/* s23g.cpp */
#include <cstdio>
#include <cstdint>

union FB { float f; std::uint32_t u; };

int main() {
    FB v;
    v.f = 1.5f;                 /* 활성 멤버는 f 다 */
    std::printf("v.u = 0x%08x   <- C++ 에서는 비활성 멤버 읽기다\n", v.u);
    return 0;
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -O2 s23g.cpp -o x ; ./x (cc exit=0 · run exit=0) =====
v.u = 0x3fc00000   <- C++ 에서는 비활성 멤버 읽기다
```

```cpp
/* s23h.cpp */
#include <string>

union U {
    int i;
    std::string s;      /* 자명하지 않은 생성자를 가진 멤버 */
};

int main() { U u; u.i = 1; return u.i; }
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic s23h.cpp -o x (cc exit=1) =====
s23h.cpp: In function ‘int main()’:
s23h.cpp:8:16: error: use of deleted function ‘U::U()’
    8 | int main() { U u; u.i = 1; return u.i; }
      |                ^
s23h.cpp:3:7: note: ‘U::U()’ is implicitly deleted because the default definition would be ill-formed:
    3 | union U {
      |       ^
s23h.cpp:5:17: error: union member ‘U::s’ with non-trivial ‘std::__cxx11::basic_string<_CharT, _Traits, _Alloc>::basic_string() [with _CharT = char; _Traits = std::char_traits<char>; _Alloc = std::allocator<char>]’
    5 |     std::string s;      /* 자명하지 않은 생성자를 가진 멤버 */
      |                 ^
s23h.cpp:8:16: error: use of deleted function ‘U::~U()’
    8 | int main() { U u; u.i = 1; return u.i; }
      |                ^
s23h.cpp:3:7: note: ‘U::~U()’ is implicitly deleted because the default definition would be ill-formed:
    3 | union U {
      |       ^
s23h.cpp:5:17: error: union member ‘U::s’ with non-trivial ‘std::__cxx11::basic_string<_CharT, _Traits, _Alloc>::~basic_string() [with _CharT = char; _Traits = std::char_traits<char>; _Alloc = std::allocator<char>]’
    5 |     std::string s;      /* 자명하지 않은 생성자를 가진 멤버 */
      |                 ^
```

**왜 그런가**

```text
   C 의 모형                               C++ 의 모형
   +---------------------------+           +-----------------------------+
   | 바이트가 한 벌 있다        |           | ★ 활성 멤버가 하나 있다      |
   | 멤버는 그 바이트를         |           | 멤버를 바꾸려면 수명을       |
   | 다시 해석하는 이름이다     |           | 끝내고 새로 시작해야 한다    |
   +---------------------------+           +-----------------------------+
            |                                        |
            v                                        v
   펀닝이 허용된다                         생성자·소멸자가 필요해지고
                                           자명하지 않으면 ★ 컴파일이 막힌다
```

- ★ **g++ `-O2` 의 값이 C 와 똑같은 `0x3fc00000`** 이다. **실행 결과로는 두 언어가 안 갈린다.**
- ★★ **갈린 것은 규칙이다.** C 는 「다른 멤버를 읽으면 바이트를 그 타입으로 다시 해석한다」로 규정했고,\
  C++ 는 「**활성 멤버가 하나뿐**」이라는 모형이라 **활성이 아닌 멤버를 읽는 것이 UB** 다.\
  ★ C 에는 「활성 멤버」라는 말 자체가 **없다.**
- ★★★ **그 모형이 실제로 강제되는 것**은 다른 자리에서 보인다. `std::string` 을 멤버로 넣으면 g++ 가 **`cc exit=1`** 로 막고,\
  진단이 **두 갈래**다 — 「`use of deleted function ‘U::U()’`」(생성자)와 「`use of deleted function ‘U::~U()’`」(소멸자),\
  그 이유로 각각 「`union member ‘U::s’ with non-trivial …`」이 붙는다.
- ★★ **C 에서는 이런 진단이 나올 수 없다** — **C 의 union 에는 생성자도 소멸자도 없기 때문**이다.\
  「지울 함수」가 없으니 「지워진 함수를 썼다」는 말도 성립하지 않는다.
- ★ **C++ 의 `union`·활성 멤버·`std::bit_cast` 는 C++ 갈래가 정본**이다.\
  여기서는 **「C 에서 허용되는 것이 C++ 에서 자동으로 허용되지는 않는다」** 한 줄까지다.

### 9. union 의 `sizeof` 가 가장 큰 멤버보다 클 수 있는 이유 ★

**왜 그런가**

- **`sizeof` 는 `_Alignof` 의 배수여야 하기 때문**이다. `union { char c[5]; int i; }` 는\
  가장 큰 멤버가 5바이트지만 **정렬이 4** 라 **8** 이 된다 — **끝에 패딩이 붙는다.**\
  ★ 이 프로그램은 **던지지 않았다.** 규칙은 [08번 형제](../08-sizeof-alignment-and-offsetof/)가 **여섯 구조체로 실측**해 둔 것을 그대로 따른다.
- ★ **구조체의 「`sizeof` 는 정렬의 배수」와 같은 규칙**이다. 배열로 늘어놓아도 원소마다 정렬을 지켜야 하기 때문이다.\
  정본은 [08번 형제](../08-sizeof-alignment-and-offsetof/)이고, 패딩 쪽은 [22번 형제](../22-struct-padding-and-alignment/)다.
- **union 의 `_Alignof` 는 가장 엄한 멤버**가 정한다. 실측에서 `double` 이 있는 union 이 **8** 이었다.
- ★ 그래서 union 의 크기를 「가장 큰 멤버의 `sizeof`」로 **계산하지 말고 `sizeof` 로 물어본다.**

### 10. 다섯 층과 무게중심 ★★★

**왜 그런가**

| 층 | 이 주제에서 | 실측 근거 |
|---|---|---|
| **표준** | 멤버가 **전부 offset 0** · `sizeof` 는 **가장 큰 멤버를 담을 만큼** · `_Alignof` 는 **가장 엄한 멤버** · 초기자 하나면 **첫 멤버** · **공통 초기 시퀀스** · ★ **union 펀닝이 허용되는 것**(C) | `offsetof` 셋 다 0 · 8 대 16 · `v.b.tag` 7·9 · 초기화 네 벌 |
| **조건부 표준** | ★ **해당 없음** | — |
| **구현 정의** | **엔디언**(`44 43 42 41`) · `float` 가 IEEE 754 인 것 · `sizeof`=8·`_Alignof`=8 · `struct B` 의 패딩 4바이트 | 바이트 덤프 · 비트 격자 · `offsetof(B,y)=8` |
| **미명시** | ★★ **쓴 멤버보다 뒤에 남은 바이트의 값** | **`41 aa aa aa aa aa aa aa`** |
| ★★★ **UB (본체)** | **포인터 캐스트로 다른 타입처럼 읽기** · ★★ **C++ 에서 활성이 아닌 멤버 읽기** | **열 벌 실측** — gcc `-O2` 부터 · clang `-O1` 부터 · g++ `cc exit=1` |

- ★★★ **무게중심은 UB 와 표준이 맞닿는 경계**다. 「네 바이트를 두 타입으로 본다」가\
  **union 을 거치면 표준 칸**이고 **포인터 캐스트면 UB 칸**이다. **소스가 거의 같이 생겼다.**
- ★★ **층마다 도구가 못 보는 것**
  - **표준** — union 펀닝에 **경고 0건**인 것이 정상이다. 진단할 이유가 없다.
  - **조건부 표준** — 볼 것이 없다.
  - **구현 정의** — 컴파일러는 **엔디언을 말해 주지 않는다.** union 으로 **찍어 봐야** 보인다.
  - **미명시** — **안 쓴 바이트가 무엇인지 말해 주는 도구가 없다.** 바이트를 한 칸씩 찍는 것이 유일한 창이다.
  - **UB** — ★★★ **clang 은 경고 0건**(정작 `-O1` 부터 깨진다) · gcc 는 **`-O2` 에서만 1건** ·\
    **UBSan + ASan 은 `run exit=0`** 으로 통과시킨다.

### 11. 경계 — 어디까지가 이 주제인가 ★

**왜 그런가**

- **엄격한 앨리어싱 규칙 전체** — 목록의 **55번 주제**가 정본이다.\
  여기는 「**union 은 되고 포인터 캐스트는 안 된다**」는 **경계 한 줄과 그 실측**까지다.
- **`memcpy`·`memcmp` 의 계약** — 목록의 **50번 주제**가 정본이다. 여기는 「**이식하려면 `memcpy`**」까지.
- **엔디언·IEEE 754 표현 자체** — [`data-representation/`](../../../../data-representation/)가 정본이다.\
  여기는 **union 이 그것을 드러내 보인다**는 것까지.
- **패딩 값이 미명시라는 것** — [22번 형제](../22-struct-padding-and-alignment/)가 정본이다.\
  6번에서 `v.a.x` 가 뜻이 없는 이유가 그쪽에 있다.
- **`sizeof`·`_Alignof`·`offsetof` 라는 도구** — [08번 형제](../08-sizeof-alignment-and-offsetof/)가 정본이다.
- **캐스트가 「비트를 바꾸는가 해석을 바꾸는가」** — [05번 형제](../05-explicit-casts-and-pointer-conversions/)가 정본이다.
- **이 주제가 끝까지 책임지는 것 셋**
  - ★★★ **「동시에 담지 않는다」** — 겹친 바이트와 「마지막에 쓴 멤버」.
  - ★★★ **union 펀닝은 허용, 포인터 캐스트는 UB 라는 경계** — 그리고 **어느 벌에서 갈리는지.**
  - ★★ **공통 초기 시퀀스** — 그 예외가 언제 서고 언제 안 서는지.

- ★ **한 줄 경계** — 「**55번은 규칙, 50번은 함수, 22번은 패딩, 23번은 「겹친다」는 사실 그 자체.**」

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 컴파일러·플래그로 돌렸나 |
|---|---|---|
| `s23a.c` (23-a) | union `sizeof` **8**·struct **16** · `_Alignof` 둘 다 8 · union `offsetof` **셋 다 0** · `44 43 42 41` · `u.c[0]='D'` · `u.d=1.0` 뒤 `u.i`=**0** · 여덟 바이트 `00 … f0 3f` | gcc `-std=c17 -Wall -Wextra -pedantic` 1벌(실행 포함) |
| `s23b.c` (23-b) | `1.5f` → **`0x3fc00000`** · 비트 격자 `0 01111111 1000…` · **`memcpy` 와 같음**(1) · `0x40490fdb` → **3.1415927** · `0x7fc00000` → **`nan`** · **경고 0건** | gcc 1벌(실행 포함) |
| `s23d.c` (23-c) | ★★ **열 벌** — gcc `-O2` 부터 · clang `-O1` 부터 반환값 **1** · 메모리 값은 **열 벌 전부 0** · `-fno-strict-aliasing` 이면 0 · gcc `-Wstrict-aliasing=2` 는 **`-O2` 에서만 1건** · clang 은 **0건** · **UBSan+ASan `run exit=0`** | gcc 6벌 · clang 5벌 (`-O0`\~`-O3` · `-fno-strict-aliasing` · sanitizer) |
| `s23e.c` (23-d) | `v.b.tag`=**7** · `v.a.tag`=**9** · `v.a.x`=0(**B 의 패딩**) · `sizeof` 8/16/16 · `offsetof(B,y)`=**8** | gcc 1벌(실행 포함) |
| `s23f.c` (23-e) | 초기화 네 벌의 바이트 격자 · ★ `d` 의 뒤 일곱 칸 **`aa`** · `sizeof`=8·`_Alignof`=8 | gcc 1벌(실행 포함) |
| `s23g.cpp` (23-f) | g++ `-O2` 에서도 **`0x3fc00000`** — C 와 같은 값 | g++ `-std=c++17 -O2` 1벌(실행 포함) |
| `s23h.cpp` (23-g) | **`cc exit=1`** · 진단 두 갈래(`U::U()` · `U::~U()` 가 deleted, 이유는 `non-trivial` 멤버) | g++ `-std=c++17` 1벌 · ★ **실행은 없다**(컴파일이 막힌다) |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3 · g++ 13.3.0)에서만** 그렇다.

- **`44 43 42 41` 로 보이는 것** — ★ **엔디언은 구현 정의**다.
- **`1.5f` 가 `0x3fc00000` 인 것** — ★ `float` 가 **IEEE 754 단정밀도**인 것도 구현 정의다.
- **`sizeof(union U)`=8 · `_Alignof`=8 · `struct B` 의 패딩 4바이트** — ★ 구현 정의다.
- **`d` 의 뒤 일곱 칸이 `aa` 인 것** — ★★ **미명시**다. **다른 값이어도 맞다.**
- **gcc 가 `-O2` 부터, clang 이 `-O1` 부터 갈린 것** — ★★★ **UB 의 한 가지 발현**일 뿐이다.\
  **표준은 어느 수준에서 갈리라고 하지 않았다.** 버전이 오르면 **갈리는 지점이 옮겨 갈 수 있다.**
- **`-Wstrict-aliasing=2` 가 gcc 의 `-O2` 에서만 1건인 것** — 진단 구현의 사정이다.

**`union` 의 「겹친다」와 「마지막에 쓴 멤버만 유효하다」 자체는 구현 의존이 아니다.**\
모든 멤버의 offset 0 · 초기자 하나면 첫 멤버 · 공통 초기 시퀀스 규칙은 **어느 C 구현에서도 같다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **트랩 표현을 읽는 것**(x86-64 의 정수에는 만들 수 없다) ·\
  `union { char c[5]; int i; }` 의 `sizeof`(9번은 [08번 형제](../08-sizeof-alignment-and-offsetof/)의 실측을 인용했다) ·\
  **익명 union** · **비트필드가 든 union**([24번 형제](../24-bit-fields/)와 묶어야 할 실험이다) ·\
  **`memcpy` 가 최적화로 사라지는지**(어셈블리를 찍어야 한다) ·\
  **clang 에 앨리어싱 경고를 더 켜는 다른 플래그**가 있는지.
- ★ **못 잰 것 — 「C 가 union 펀닝을 허용한다」를 실행으로 확인할 수는 없다.**\
  허용은 **「깨지지 않는다」는 보장**인데, **깨지지 않는 것을 몇 벌 관찰해도 보장을 확인한 것이 아니다.**\
  ★ 이 문서가 할 수 있었던 것은 **반대쪽(포인터 캐스트)이 실제로 깨지는 것을 보인 것**까지다.\
  ★ 같은 이유로 **「C++ 에서 비활성 멤버 읽기가 UB 다」도 실행으로 못 보였다** —\
  대신 **활성 멤버 모형이 강제되는 다른 자리**(`s23h.cpp`)를 던졌다.
- ★ **`-Wstrict-aliasing` 이 `=2` 말고 다른 수준에서 어떻게 달라지는지**는 던지지 않았다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **gcc·clang 이 갈리는 최적화 수준** — **UB 칸이라 언제든 옮겨 갈 수 있다.** 4번 표를 통째로 다시 찍는다.
- ★★ **clang 이 앨리어싱 위반을 경고하게 됐는지**(지금은 `-O2` 에서도 0건).
- ★★ **UBSan 에 앨리어싱 검사가 생겼는지**(지금은 `-fsanitize=undefined,address` 로 `run exit=0`).
- ★ **g++ 의 진단 문구**(`U::U()` · `non-trivial …`)는 **문구 대조를 깨뜨릴 수 있는 자리**다.
- **union 의 크기·정렬·offset 0·공통 초기 시퀀스는 다시 돌릴 필요가 없다** — C89 이후 바뀐 적이 없다.
