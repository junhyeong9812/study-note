# c/syntax/08 — `sizeof`·정렬·`offsetof`: 구조체에 난 구멍을 눈으로 본다 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 수치·출력·에러는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> **구조체 배치는 `offsetof` 로 재고 실제 바이트 덤프로 대조했다 — 손으로 계산한 수치는 하나도 없다.**\
> UB 가 걸린 답(4번)은 `-O0`·`-O2`·sanitizer 로 돌렸다. 기본 플래그는 `-std=c17 -Wall -Wextra`.
> ★ **이 주제의 수치는 전부 「이 ABI 의 사실」이지 언어의 보장이 아니다.** 9번이 그 방어선이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `sizeof` 의 세 얼굴

**출력**

```text
sizeof(int)        = 4   <- 괄호 필수
sizeof i           = 4   <- 괄호 없이도 된다
sizeof i + 1       = 5   <- ★ (sizeof i) + 1 로 묶인다
sizeof a           = 40   원소 수 = 10
sizeof s           = 8   <- 포인터 크기 (문자열 길이가 아니다)
sizeof "hello"     = 6   <- 배열이다 ('\0' 포함)
sizeof 의 결과 타입 -> unsigned long (= size_t)
```

**여섯 줄**

- `4` · `4` · **`5`** · `40` · `8` · **`6`**

**셋째 줄**

```text
   sizeof i + 1

   sizeof 는 ★ 단항 연산자라 + 보다 먼저 묶인다

   (sizeof i) + 1  =  4 + 1  =  5
   sizeof (i + 1)  =  4              <- 이걸 원했다면 괄호를 쳐야 한다
```

- **`(sizeof i) + 1` 로 묶인다.** `sizeof(i + 1)` 이 아니다.
- 그래서 `sizeof x * 2` 같은 식도 `(sizeof x) * 2` 다 — 대개 의도와 맞지만 **우연**이다.

**`sizeof s` 와 `sizeof "hello"`**

```text
   char *s = "hello";

   s            : char * 를 담은 ★ 변수       -> sizeof = 8 (포인터)
   "hello"      : char[6] 인 ★ 배열 리터럴     -> sizeof = 6 ('\0' 포함)

   -> s 는 "그 배열을 가리키는 포인터" 이고 배열 자체가 아니다
```

- `sizeof s` 는 **포인터의 크기**, `sizeof "hello"` 는 **배열의 크기**다.
- 문자열 길이(`strlen`)는 5다 — **세 수가 전부 다르다**(8 · 6 · 5).

**결과 타입**

- **`size_t`**(여기선 `unsigned long`)다.
- **부호가 없다**는 것이 사고의 씨앗이다 — `sizeof(int) - 5` 가 `-1` 이 아니라 `18446744073709551615` 다.\
  [02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)·[03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)가 그 정본이다.

### 2. 피연산자가 평가되나

**출력**

```text
--- sizeof 의 피연산자는 평가되지 않는다 ---
sizeof(boom())     = 4
side = 0  (0 이면 boom 이 안 불린 것)
sizeof(j++)        = 4, 그 뒤 j = 0
```

**`boom 이 불렸다` 가 나오나**

- **안 나온다.** 한 줄도 안 찍혔다.

**`side` 와 `j`**

- 둘 다 **0** 이다. 함수도 안 불리고 증가도 안 일어났다.
- `sizeof` 는 **피연산자의 타입만** 본다. 값을 구하지 않는다.

**예외**

- **VLA** 다.

```text
시작 호출 수 = 0
sizeof(int[n()]) = 16 뒤 호출 수 = 1
VLA a 의 sizeof = 12 (m=3)
m 을 100 으로 바꾼 뒤 sizeof a = 12  <- 배열을 만든 시점의 값이다
sizeof(j++) 뒤 j = 0
```

- `sizeof(int[n()])` 를 한 번 쓰자 **호출 수가 0에서 1로 늘었다.**
- ★ **확인 방법에 함정이 있었다.** 처음에는 같은 `printf` 안에 `sizeof(int[n()])` 와 `calls` 를 나란히 넣었는데,\
  gcc 가 **인자를 오른쪽부터 평가**해서 `calls` 를 먼저 읽는 바람에 「안 늘었다」는 **틀린 관찰**이 나왔다.\
  **문을 나눠 다시 재니 답이 뒤집혔다.** 함수 인자 평가 순서는 **미명시**다([05번 형제](../05-explicit-casts-and-pointer-conversions/)).\
  **측정 코드 자체가 미명시에 걸릴 수 있다.**

**무엇을 기억하나**

- **배열을 만든 시점의 크기**다. `m` 을 3에서 100으로 바꿔도 `sizeof a` 는 **12 그대로**였다.
- 정본은 목록의 **18번 주제**.

### 3. 멤버 순서만 바꾸면 ★★★

**출력**

```text
멤버 크기: char=1 int=4 double=8
멤버 정렬: char=1 int=4 double=8

Bad          sizeof=24 _Alignof=8
Good         sizeof=16 _Alignof=8

struct Bad  offsets: a=0 b=4 c=8 d=16
struct Good offsets: d=0 b=8 a=12 c=13

멤버 크기 합 = 14
```

```text
struct Bad   a...bbbbc.......dddddddd   (24 바이트, '.' 이 구멍)
struct Good  ddddddddbbbbac..   (16 바이트, '.' 이 구멍)
```

```text
struct Bad 의 실제 바이트 (0xFF 로 채우고 멤버만 0 대입):
00 ff ff ff 00 00 00 00
00 ff ff ff ff ff ff ff
00 00 00 00 00 00 00 00
  -> ff 로 남은 자리가 패딩이다
```

**두 `sizeof` 와 합**

- `Bad` = **24** · `Good` = **16** · 멤버 크기의 합 = **14**
- **같은 멤버인데 8바이트 차이**다. 100만 개 배열이면 8MB 차이다.

**두 `_Alignof`**

- **둘 다 8** 이다. 가장 엄한 멤버(`double`)의 정렬을 따른다.

**구멍의 자리**

```text
   struct Bad (24바이트)                      struct Good (16바이트)

   0  a        char                          0  d d d d d d d d   double
   1  .  ) 3바이트 구멍                        8  b b b b         int
   2  .  )   (b 의 정렬 4 에 맞추려고)          12  a               char
   3  .  )                                   13  c               char
   4  b b b b   int                          14  .  ) 2바이트 구멍
   8  c        char                          15  .  )   (sizeof 를 8의 배수로)
   9  .  )                                   ----------------------
  10  .  ) 7바이트 구멍                         구멍 2바이트
  ...   )   (d 의 정렬 8 에 맞추려고)
  15  .  )
  16  d d d d d d d d   double
   ----------------------
   구멍 10바이트
```

- `Bad` — `a` 뒤에 **3바이트**, `c` 뒤에 **7바이트**. 합 10.
- `Good` — 끝에 **2바이트**뿐. 합 2.

**다른 방법으로 확인**

- **메모리를 `0xFF` 로 채우고 멤버에만 0을 대입한 뒤 바이트를 찍는다.**
- 위 덤프에서 `ff` 로 남은 자리가 **지도의 `.` 자리와 정확히 일치**한다.
- ★ **한 방법만 썼으면 「내 지도가 맞나」를 확인할 길이 없었다.** 두 방법이 같은 답을 내야 믿는다.

**규칙 셋**

```text
   ① 각 멤버는 자기 정렬의 배수 자리에서 시작한다
        -> b(정렬 4) 가 1이 아니라 4 에서 시작

   ② 구조체의 정렬 = 가장 엄한 멤버의 정렬
        -> double 이 있으면 8

   ③ sizeof 는 ②의 배수여야 한다
        -> 배열로 늘어놓아도 각 원소가 정렬을 지켜야 하니까
```

- ③을 여섯 구조체로 확인했다(7번).

### 4. `#pragma pack` 의 대가 ★★

**출력**

```text
struct Bad    sizeof=24 _Alignof=8  offsets a=0 b=4 c=8 d=16
struct Packed sizeof=14 _Alignof=1  offsets a=0 b=1 c=5 d=6
&p.b 가 4로 나눠지나: 0
*q = 0x41424344
```

```text
pack.c:20:8: runtime error: store to misaligned address 0x5d0f2cfc6199 for type 'int', which requires 4 byte alignment
pack.c:21:5: runtime error: load of misaligned address 0x5d0f2cfc6199 for type 'int', which requires 4 byte alignment
```

**두 값**

- `sizeof` = **14**(멤버 크기의 합과 같다) · `_Alignof` = **1**

```text
   struct Bad (24)                  struct Packed (14)
   +-+---+----+-+-------+--------+  +-+----+-+--------+
   |a|...| b  |c|.......|   d    |  |a| b  |c|   d    |
   +-+---+----+-+-------+--------+  +-+----+-+--------+
    0    4     8        16           0 1    5 6
    _Alignof = 8                     _Alignof = ★ 1

   얻은 것: 10바이트                  잃은 것: b(1번지)·d(6번지) 가 정렬을 안 지킨다
```

**`&p.b` 가 4의 배수인가**

- **아니다**(`0` 이 찍혔다 — 나머지가 0이 아니라는 뜻). `b` 가 1번지에서 시작한다.

**sanitizer**

- **두 줄**이다 — `store` 와 `load`.
- 이 UB 는 [05번 형제](../05-explicit-casts-and-pointer-conversions/)의 `(int *)(buf + 1)` 과 **완전히 같은 것**이다. 만드는 경로만 다르다.
- ★ **멤버를 직접 읽고 쓰는 것(`p.b = 1`)은 안전하다** — 컴파일러가 정렬이 안 맞는 줄 알고 바이트 단위로 처리한다.\
  **위험한 것은 그 멤버의 주소를 꺼내는 것**이다.

**`-Wall -Wextra`**

```text
[] 0
[-Wall] 0
[-Wall -Wextra] 0
```

- ★★ **0건이다.**

**`__attribute__((packed))` 로 바꾸면**

```text
pack2.c:10:14: warning: taking address of packed member of ‘struct Q’ may result in an unaligned pointer value [-Waddress-of-packed-member]
```

```text
[] 1
[-Wall] 1
[-Wall -Wextra] 1
[-Wall -Wextra -Waddress-of-packed-member] 1
```

- **경고가 나온다.** 플래그를 하나도 안 줘도 나온다(기본으로 켜져 있다).
- 그런데 **같은 소스에 `#pragma pack` 짜리 `struct P` 도 있었고 그쪽은 한 줄도 안 나왔다.**

**배치는 같은가**

```text
P: sizeof=5 _Alignof=1 offset(b)=1
Q: sizeof=5 _Alignof=1 offset(b)=1
```

- ★★ **완전히 같다.** 크기도 정렬도 오프셋도 같다.
- **같은 위험인데 하나만 경고한다.** clang 도 `struct Q` 쪽만 잡았다.
- ★ **「경고가 없다」가 「안전하다」가 아니라는 가장 싼 증거**다 — 같은 파일 안에서 두 결과가 나왔다.

### 5. 유연 배열 멤버

**출력**

```text
sizeof(struct Buf) = 4   <- a[] 를 안 센다
offsetof(struct Buf, a) = 4
한 번 할당한 크기 = 24, a[4] = 16
(asan 통과)
```

**두 값**

- `sizeof(struct Buf)` = **4** · `offsetof(struct Buf, a)` = **4**
- **`a[]` 는 세어지지 않는다.** 크기 0으로 취급된다.
- ★ 두 값이 **같다**는 것이 핵심이다 — 「구조체가 끝나는 자리에서 배열이 시작한다」.

**`malloc` 에 넘긴 크기**

```text
   malloc(sizeof *b + 5 * sizeof b->a[0])
        =  4 + 5*4
        =  24

   +----+----+----+----+----+----+
   | n  |a[0]|a[1]|a[2]|a[3]|a[4]|
   +----+----+----+----+----+----+
    0    4    8    12   16   20
   ★ 헤더와 데이터가 한 번의 할당으로 붙어 있다
```

- **24** 다. `a[4] = 16`(=4²)이 정확히 읽혔다.
- `sizeof b->a[0]` 로 쓰면 **원소 타입이 바뀌어도 안 고쳐도 된다.**

**ASan**

- **통과했다.** 경계 밖 접근이 없다는 확인이다.

**포인터 멤버보다 나은 점**

| | 유연 배열 멤버 | 포인터 멤버 + 별도 할당 |
|---|---|---|
| 할당 횟수 | **1번** | 2번 |
| 해제 | `free(b)` **한 번** | 두 번(순서도 지켜야) |
| 지역성 | 헤더와 데이터가 **붙어 있다** | 떨어져 있다 |
| 통째로 복사 | `memcpy` 한 번 | 깊은 복사가 필요 |

- 정본은 목록의 **26번 주제**.

### 6. 빈 구조체

**출력**

```text
0
```

```text
empty.c:2:8: warning: struct has no members [-Wpedantic]
    2 | struct Empty { };
      |        ^~~~~
```

```text
empty.c:2:8: error: struct has no members [-Wpedantic]
```

```text
1
```

**gcc 기본**

- **컴파일된다.** `sizeof` 가 **0** 이고 경고도 없다.
- ★ **C 에는 빈 구조체가 없다.** gcc 가 확장으로 받아 주는 것이다.

**`-pedantic` 과 `-pedantic-errors`**

- `-pedantic` → **경고**(`struct has no members`)
- `-pedantic-errors` → **에러**. 컴파일이 멈춘다.
- [07번 형제](../07-enum-and-enumeration-constants/)의 C23 문법과 같은 패턴이다 — **`-std=` 가 아니라 `-pedantic` 이 표준을 강제한다.**

**C++ 로 컴파일하면**

- **`1`** 이다.

```text
   같은 소스, 다른 언어

   C   (gcc)   -> sizeof(struct Empty) = 0   (확장)
   C++ (g++)   -> sizeof(struct Empty) = 1   (★ 표준이 그렇게 정했다)

   C++ 이 1 인 이유: 서로 다른 객체는 서로 다른 주소를 가져야 하는데
                     크기가 0 이면 두 객체가 같은 주소를 갖게 된다
```

**문제가 되는 자리**

- **같은 헤더를 C 와 C++ 양쪽에서 쓰는 경우.** 빈 구조체를 멤버로 가진 구조체의 배치가 **언어에 따라 어긋난다.**
- 라이브러리 헤더가 `extern "C"` 로 감싸여 있어도 **`sizeof` 는 컴파일러가 정하는 것**이라 안 맞는다.
- 쓸 일이 생기면 **`char dummy;` 를 하나 넣는다.** 그러면 양쪽에서 1이다.

### 7. 구조체 정렬은 어떻게 정해지나

**출력**

```text
A         sizeof= 1 _Alignof= 1  sizeof % _Alignof = 0
B         sizeof= 4 _Alignof= 2  sizeof % _Alignof = 0
C         sizeof= 8 _Alignof= 4  sizeof % _Alignof = 0
D         sizeof=16 _Alignof= 8  sizeof % _Alignof = 0
E         sizeof=16 _Alignof= 8  sizeof % _Alignof = 0
F         sizeof= 3 _Alignof= 1  sizeof % _Alignof = 0
```

**`_Alignof(struct)` 를 정하는 규칙**

- **가장 엄한(큰) 멤버의 정렬**이다.

```text
   A {char}                -> max(1) = 1
   B {char, short}         -> max(1, 2) = 2
   C {char, int}           -> max(1, 4) = 4
   D {char, double}        -> max(1, 8) = 8
   E {double, char}        -> max(8, 1) = 8      ★ 순서와 무관
   F {char, char, char}    -> max(1,1,1) = 1
```

**`sizeof % _Alignof`**

- **여섯 개 모두 0** 이다.
- 그래야 하는 이유:

```text
   struct D arr[3];

   arr[0] 이 8의 배수 주소에 있다면
   arr[1] 의 주소 = arr[0] + sizeof(struct D)

   sizeof 가 8의 배수가 아니면 arr[1] 이 정렬을 못 지킨다
   -> 그래서 sizeof 는 ★ _Alignof 의 배수여야 한다
```

**`struct { double a; char b; }` 가 16인 이유**

- 멤버 크기의 합은 9인데, `_Alignof` 가 8이므로 **8의 배수**여야 한다 → 16.
- **끝에 7바이트가 붙는다.** 「패딩은 멤버 사이에만 있다」고 생각하면 이 자리를 놓친다.

**구조체 배열과의 관계**

```text
sizeof(struct T)=8  배열 3개=24  (3배인가: 1)
sizeof(struct Tail)=8 offsets b=0 a=4  <- 끝 3바이트가 패딩
```

- **배열의 크기는 정확히 n배**다. 원소 사이에 추가 패딩이 없다.
- 그게 가능한 이유가 **끝 패딩**이다 — 끝에 미리 넣어 두었기 때문에 이어 붙이기만 하면 된다.
- 즉 **끝 패딩과 배열 규칙은 같은 사실의 두 얼굴**이다.

### 8. `_Alignof`·`_Alignas`·`alignof`

**출력**

```text
_Alignof: char=1 short=2 int=4 long=8 double=8 long double=16
_Alignof(void*)=8  _Alignof(struct S)=8  sizeof(struct S)=16
_Alignof(max_align_t)=16 sizeof(max_align_t)=32
alignof (stdalign.h) 로도 같은 값: 4
_Alignas(64) 배열 주소 % 64 = 0
_Alignas(16) 배열 주소 % 16 = 0
malloc(1) 주소 % _Alignof(max_align_t) = 0
aligned_alloc(64,128) 주소 % 64 = 0
```

**정렬 값**

| 타입 | `_Alignof` |
|---|---|
| `char` | 1 |
| `short` | 2 |
| `int` | 4 |
| `long` · `double` · `void *` | 8 |
| `long double` | **16** |
| `max_align_t` | **16** |

- 대개 **`sizeof` 와 같은데 `long double` 이 예외**다 — `sizeof` 가 16이고 정렬도 16이지만\
  **실제 정밀도는 64비트뿐**이다([04번 형제](../04-floating-point-types-and-conversions/)).

**`_Alignas(1) int x;`**

```text
alred.c:2:34: error: ‘_Alignas’ specifiers cannot reduce alignment of ‘x’
```

- **에러**다. `_Alignas` 는 **늘리기만** 된다.
- 늘리는 쪽은 된다 — `_Alignas(64) int x;` 의 `_Alignof(x)` 가 **64** 이고 주소도 64의 배수였다.

**`malloc` 의 보장**

- **`max_align_t` 의 정렬**(여기선 16)을 지킨다. 즉 **어떤 타입으로 써도 정렬이 맞는다.**
- 확인 방법은 `(unsigned long)p % _Alignof(max_align_t)` 를 찍는 것 — **나머지가 0** 이었다.
- 더 큰 정렬이 필요하면 **`aligned_alloc`**(C11) 이다. `aligned_alloc(64, 128)` 의 주소가 64의 배수였다.
- 정본은 목록의 **37번 주제**.

**`alignof` 철자**

```text
[c17] c23.c:2:15: error: expected declaration specifiers or ‘...’ before ‘sizeof’
[c2x] alignof(double)=8
```

```text
   C11 ~ C17   _Alignof / _Alignas         헤더 없이
               alignof  / alignas          ★ <stdalign.h> 가 필요
               _Static_assert              헤더 없이
               static_assert               ★ <assert.h> 가 필요

   C23         alignof / alignas / static_assert    전부 헤더 없이
```

- **C23**(`-std=c2x`)이 필요하다. `-std=c17` 에서는 에러다.
- `<stdalign.h>` 를 넣으면 `-std=c17` 에서도 `alignof` 가 쓰이고 **같은 값**(4)을 준다.

### 9. `_Static_assert` 로 못 박기

**출력**

```text
_Static_assert 세 개 통과
```

```text
sa2.c:3:1: error: static assertion failed: "assumed no padding"
    3 | _Static_assert(sizeof(struct S) == 9, "assumed no padding");
      | ^~~~~~~~~~~~~~
```

**쓸 수 있나**

- **셋 다 쓸 수 있다.** `sizeof`·`offsetof`·`_Alignof` 가 전부 **정수 상수식**이기 때문이다.

```c
_Static_assert(sizeof(struct S) == 16, "이 ABI 에서 struct S 는 16바이트");
_Static_assert(offsetof(struct S, d) == 8, "d 는 8번째 바이트에서 시작");
_Static_assert(_Alignof(struct S) == _Alignof(double), "구조체 정렬 = 가장 엄한 멤버");
```

- VLA 의 `sizeof` 는 상수가 아니므로 **못 쓴다**(2번).

**거짓이면**

- **컴파일이 멈춘다.** `error: static assertion failed:` 뒤에 메시지가 붙는다.

**런타임 `assert` 와의 차이 셋**

```text
   assert (런타임)                    _Static_assert (컴파일 타임)
   +--------------------------+      +--------------------------+
   | ① 그 줄이 실행돼야 안다    |      | ① ★ 빌드가 안 된다         |
   | ② NDEBUG 로 사라진다      |      | ② 절대 안 사라진다          |
   | ③ 실행 파일에 코드가 생긴다 |      | ③ ★ 코드가 한 바이트도 안 생김|
   +--------------------------+      +--------------------------+
```

- ①이 결정적이다 — **다른 플랫폼에서 빌드하는 순간** 거기서 멈춘다. 테스트를 안 돌려도 된다.

**메시지 주의점**

- ★ **ASCII 로 쓴다.** 한글 메시지를 넣었더니 진단에 **8진 이스케이프로 깨져 나왔다.**

```text
error: static assertion failed: "\37777777755\37777777614\37777777650\37777777753\37777777624\37777777651\37777777754\37777777635\37777777664 \37777777754\37777777627\37777777606\37777777753\37777777613\37777777644\37777777752\37777777663\37777777640 \37777777752\37777777660\37777777600\37777777754\37777777640\37777777625\37777777755\37777777626\37777777610\37777777753\37777777613\37777777644"
```

- 메시지가 안 읽히면 단언의 값이 절반 사라진다. **왜 이 단언이 있는지**를 영어로 한 줄 적는 편이 낫다.

### 10. `memcmp` 로 구조체를 비교하면

**출력**

```text
멤버는 같은데 memcmp = -255  (0 이 아니면 다르다고 본 것)
멤버로 비교하면 같은가: 1
```

**무엇을 돌려주나**

- **`-255`** 다. 「다르다」는 답이다.

**왜 그런가**

```text
   struct T { char a; int b; };   sizeof = 8

   x : memset 0x00 -> a=1, b=2 대입
       01 00 00 00 02 00 00 00
          ^^^^^^^^  패딩 = 00

   y : memset 0xFF -> a=1, b=2 대입
       01 ff ff ff 02 00 00 00
          ^^^^^^^^  패딩 = ff

   -> 멤버는 전부 같은데 ★ 2번째 바이트에서 00 vs ff 로 갈린다
      0x00 - 0xff = -255
```

- **패딩 바이트의 값은 미명시**다. 표준이 「어떤 값이든 될 수 있다」고 둔 자리다.
- 대입·초기화 방식에 따라 달라지고, **같은 프로그램 안에서도 두 객체가 다를 수 있다.**

**도구가 잡나**

| | 결과 |
|---|---|
| `-Wall -Wextra` | **0건** |
| `-pedantic` | 0건 |
| UBSan | **못 잡는다** |
| ASan | 못 잡는다 |

- ★ **아무도 안 잡는다.** 「미명시」 층이라 **원리상 잡을 수가 없다** — UB 가 아니므로 sanitizer 가 볼 근거가 없고,\
  값이 「몇 가지 중 하나」일 뿐이므로 경고할 근거도 없다.

**`y = x;` 로 대입한 뒤에는**

```text
-O0  : 대입 뒤 memcmp = 0 y 의 바이트: 01 00 00 00 02 00 00 00  
-O2  : 대입 뒤 memcmp = 0 y 의 바이트: 01 00 00 00 02 00 00 00  
```

- **`memcmp` 가 0** 이 된다. `y` 의 패딩이 `ff` 에서 `00` 으로 바뀌었다 — gcc 가 객체를 통째로 복사했다.
- ★ **그런데 이것을 보장으로 읽으면 안 된다.** 표준은 대입이 패딩을 어떻게 하는지 정하지 않는다.
- **두 최적화 수준에서 같았다는 것이 오히려 함정**이다 —\
  [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)의 「여러 판에서 같았다는 것이 보장이 아니다」와 정확히 같은 자리다.
- 안전한 답은 **멤버끼리 비교하는 것**이다(실측 `1`). 정본은 목록의 **50번 주제**.

### 11. `offsetof` 의 경계

**출력**

```text
#define offsetof(TYPE,MEMBER) __builtin_offsetof (TYPE, MEMBER)
```

```text
표준 offsetof(d) = 8
옛날 관용구      = 8
```

```text
oldoff.c:7:45: runtime error: member access within null pointer of type 'struct S'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior oldoff.c:7:45 
```

```text
bf.c:3:46: error: attempt to take address of bit-field structure member ‘f’
    3 | int main(void) { return (int)offsetof(struct B, f); }
```

**무엇으로 정의되어 있나**

- **`__builtin_offsetof`** 다. `gcc -E -dM` 으로 매크로 정의를 찍어 확인했다.
- 컴파일러 내장이라 **UB 를 안 만든다.**

**옛날 관용구는 같은 답을 주나**

- **준다**(둘 다 8). 보통 빌드에서는 구별이 안 된다.

**sanitizer 로 돌리면**

| 도구 | 결과 |
|---|---|
| gcc `-fsanitize=undefined` | **조용하다** |
| clang `-fsanitize=undefined` | **`member access within null pointer` 로 잡는다** |

- ★ **컴파일러에 따라 갈린다.** [05번 형제](../05-explicit-casts-and-pointer-conversions/)의 `-fsanitize=function`(gcc 에 없음)과 같은 종류의 차이다.
- **「sanitizer 로 돌렸다」가 컴파일러마다 다른 의미**라는 것을 이 주제에서도 한 번 더 확인한 셈이다.
- 그래서 **표준 `offsetof` 를 쓴다.** 직접 만들 이유가 없다.

**비트필드에 쓰면**

- **에러**다 — `attempt to take address of bit-field structure member`.
- 비트필드 멤버는 **주소가 없다**(바이트 경계에 안 맞을 수 있으므로). 정본은 목록의 **24번 주제**.

### 12. 그래서 무엇을 하나

**크기를 줄이는 두 방법**

```text
   공짜 방법                        대가가 있는 방법
   +--------------------------+    +--------------------------+
   | 멤버를 큰 것부터 놓는다    |    | #pragma pack(1)          |
   | 24 -> 16                 |    | 24 -> 14                 |
   |                          |    |                          |
   | 잃는 것: ★ 없다           |    | 잃는 것: ★ 정렬 보장      |
   | (선언 순서만 바뀐다)       |    |        ★ 경고까지 잃는다  |
   +--------------------------+    +--------------------------+
```

- 먼저 **순서**를 고친다. 그래도 모자라면 그때 `#pragma pack` 을 생각한다.
- `-Wpadded` 를 한 번 켜서 **구멍이 어디 있는지** 보는 것이 출발점이다.

**반드시 같이 쓸 것**

- **`_Static_assert`** 다.

```c
_Static_assert(sizeof(struct Packet) == 14, "wire format size");
_Static_assert(offsetof(struct Packet, payload) == 6, "payload offset");
```

- 이 주제의 수치는 전부 「**이 ABI 의 사실**」이지 언어의 보장이 아니다.\
  다른 플랫폼에서 빌드할 때 **거기서 멈추게** 하는 것이 유일한 방어선이다.

**파일 형식·패킷의 이식 가능한 형태**

```c
/* 구조체를 그대로 캐스트하지 않는다 */
unsigned char buf[14];
uint32_t b;
memcpy(&b, buf + 1, sizeof b);      /* 정렬·패딩·엔디언에 안 걸린다 */
```

- **`memcpy` 로 바이트를 옮긴다.** [05번 형제](../05-explicit-casts-and-pointer-conversions/)가 앨리어싱 쪽에서 낸 답과 **같은 답**이다.
- 엔디언까지 맞추려면 바이트를 직접 조립한다(그 정본은 [`../../../../data-representation/`](../../../../data-representation/)).
- 고정폭 정수(`uint8_t`·`uint32_t`)를 쓴다 — `enum` 이나 `int` 를 그대로 쓰지 않는다([07번 형제](../07-enum-and-enumeration-constants/)·[02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)).

**도구가 원리상 못 잡는 층**

- **「미명시」** 층이다. 여기 해당하는 것은 **패딩 바이트의 값** 하나다.
- UB 가 아니므로 sanitizer 가 볼 근거가 없고, 「몇 가지 중 하나」일 뿐이라 경고할 근거도 없다.
- 그래서 `memcmp` 로 구조체를 비교하는 코드는 **아무 도구도 안 잡는다.** 사람이 규칙으로 막아야 한다.

**빌드 플래그 한 줄**

```text
개발·운영 빌드
  gcc -std=c17 -O2 -Wall -Wextra -Werror
  + 한 번씩 -Wpadded 를 켜서 구멍을 눈으로 본다

이식성 확인
  gcc -std=c17 -pedantic-errors        (빈 구조체 같은 확장을 막는다)

테스트 빌드
  gcc -std=c17 -O1 -g -fsanitize=undefined,address -fno-sanitize-recover=all
  (packed 멤버의 정렬 위반을 여기서 잡는다)

소스에
  ★ _Static_assert 로 sizeof·offsetof·_Alignof 를 못 박는다
    -> 이 주제에서 유일하게 자동으로 막아 주는 것
```

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 플래그로 돌렸나 |
|---|---|---|
| `sizeof` 세 얼굴 | 타입·식·배열 · `sizeof i + 1` = 5 · `sizeof s`(8) ↔ `sizeof "hello"`(6) · 결과 타입 `unsigned long` | `-std=c17 -Wall -Wextra` |
| 피연산자 평가 | `sizeof(boom())` 뒤 `side=0` · `sizeof(j++)` 뒤 `j=0` | 〃 |
| VLA 예외 | `sizeof(int[n()])` 가 `n()` 을 부름(호출 수 0→1) · `m` 을 바꿔도 `sizeof a` 는 12 · **★ 첫 측정은 인자 평가 순서 때문에 틀렸고 문을 나눠 다시 쟀다** | 〃 |
| 패딩 | `Bad`=24 / `Good`=16 (멤버 합 14) · `offsetof` 4개씩 · **바이트 지도** · **`0xFF` 덤프로 이중 확인** | 〃 |
| 정렬 규칙 | 여섯 구조체의 `sizeof % _Alignof` 가 **전부 0** · `{double,char}` 가 16 · 배열이 정확히 3배 | 〃 |
| `#pragma pack` | 24→14 · `_Alignof` 1 · `&p.b` 가 4의 배수 아님 · UBSan **2줄** · **`-Wall -Wextra` 0건** | `-O0`·`-O2`·ubsan·플래그 3벌 |
| packed 두 방식 | `__attribute__((packed))` 는 **경고 1건**(플래그 없이도), `#pragma pack` 은 **0건** · **배치는 완전히 같음**(5/1/1) | 플래그 4벌 · clang |
| 유연 배열 멤버 | `sizeof`=4 · `offsetof(a)`=4 · 할당 24 · `a[4]`=16 · **ASan 통과** | `-Wall -Wextra` · asan |
| 빈 구조체 | gcc 기본 **0** · `-pedantic` 경고 · `-pedantic-errors` 에러 · **C++ 은 1** | gcc 3벌 · g++ |
| `_Alignof`/`_Alignas` | 6타입 + `void*`·`max_align_t` · `_Alignas(1)` 은 **에러** · `_Alignas(64)` 주소 나머지 0 · `malloc` 이 `max_align_t` 정렬 · `aligned_alloc(64,128)` | `-std=c17 -Wall -Wextra` |
| `_Static_assert` | 세 개 통과 · 틀리면 `static assertion failed` · **한글 메시지가 8진 이스케이프로 깨짐** | `-std=c17` |
| C23 철자 | `-std=c2x` 는 헤더 없이 `static_assert`·`alignof` OK · `-std=c17` 은 에러 · `<stdalign.h>` 면 c17 도 OK(4) | `c17`/`c2x` |
| `memcmp` | 멤버가 같은데 **`-255`** · 멤버 비교는 1 · **경고 0건 · 도구 무반응** | `-Wall -Wextra`·ubsan·asan |
| 구조체 대입 | `y = x` 뒤 `memcmp`=0 · 패딩이 `ff`→`00` · **`-O0`·`-O2` 동일**(관찰이지 보장 아님) | `-O0`·`-O2` |
| `offsetof` 경계 | `__builtin_offsetof` 로 정의됨(`-E -dM`) · 옛날 관용구도 8 · **gcc ubsan 무반응, clang 은 잡음** · 비트필드는 에러 | `-E -dM` · gcc/clang ubsan |
| `-Wpadded` | `struct Bad` 의 구멍 둘 + `struct Good` 의 끝 패딩을 **정확히 3건**으로 짚음 | `-Wpadded` |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0)에서만** 그렇다.

- 모든 `sizeof`·`_Alignof`·`offsetof` 수치 — **전부 구현 정의**다. 다른 ABI 에서는 다르다.
- `_Alignof(max_align_t)`=16 · `sizeof(max_align_t)`=32.
- `_Alignof(long double)`=16 — x86-64 의 80비트 확장 형식 때문이다.
- 빈 구조체를 받아 주고 `sizeof` 를 0으로 주는 것 — **gcc 의 확장**이다.
- `#pragma pack` 에 `-Waddress-of-packed-member` 가 안 붙는 것 — gcc·clang 둘 다 그랬지만 **보장이 아니다.**
- 구조체 대입이 패딩까지 복사하는 것 — **미명시** 층이다. 관찰일 뿐이다.
- gcc UBSan 에 널 포인터 멤버 접근 검사가 **없는 것**(clang 에는 있다).

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `aligned_alloc` 에서 **크기가 정렬의 배수가 아닐 때** 무엇이 나오는지 ·\
  `-Wpadded` 를 큰 프로젝트에 켰을 때의 소음 · 이 머신의 **실제 캐시 라인 크기** ·\
  `_Alignas` 를 구조체 멤버에 붙이기 · 비트필드의 배치 규칙(목록의 **24번 주제**).
- **못 잰 것** — 다른 ABI(32비트·ARM)의 배치. 이 머신은 x86-64 하나뿐이고 32비트 헤더가 없다\
  ([04번 형제](../04-floating-point-types-and-conversions/)·[05번 형제](../05-explicit-casts-and-pointer-conversions/)가 같은 자리에서 막혔다).

**버전이 올랐을 때 다시 돌려야 하는 것**

- 3·7번의 모든 수치(구현 정의 — **보장이 아니다**).
- `#pragma pack` 에 `-Waddress-of-packed-member` 가 붙게 됐는지.
- gcc UBSan 이 널 포인터 멤버 접근을 잡게 됐는지.
- `-std=c17` 에서 `alignof`·`static_assert` 철자가 헤더 없이 되게 됐는지.
