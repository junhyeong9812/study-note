# c/syntax/08 — `sizeof`·정렬·`offsetof`: 구조체에 난 구멍을 눈으로 본다 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — sizeof](https://en.cppreference.com/w/c/language/sizeof) · [cppreference — _Alignof / _Alignas](https://en.cppreference.com/w/c/language/_Alignof) · [cppreference — offsetof](https://en.cppreference.com/w/c/types/offsetof) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html)
> **실행 검증** — 이 문서의 모든 수치·출력·에러는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> **구조체 배치는 `offsetof` 로 재고, 그 위에 실제 바이트 덤프로 한 번 더 대조했다** — 손으로 계산한 수치는 하나도 없다.\
> UB 가 걸린 블록(`#pragma pack` 역참조)은 `-O0`·`-O2`·sanitizer 로 돌렸다. 기본 플래그는 `-std=c17 -Wall -Wextra`.
> **버전** — `sizeof`·`offsetof` 는 C89 부터. **`_Alignof`/`_Alignas`/`_Static_assert` 는 C11부터**,\
> **`alignof`/`alignas`/`static_assert` 철자는 C23부터**(C11\~C17 은 `<stdalign.h>`/`<assert.h>` 가 필요하다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> **경계** — 「구조체 패딩·정렬」의 정본은 목록의 **22번 주제**다. 여기는 **`sizeof`·`_Alignof`·`offsetof` 라는 도구**로 그것을 재는 쪽이다.\
> 「배열 감쇠」는 [목록의 **16번 주제**](../16-array-pointer-decay-and-function-parameters/), 「VLA」는 목록의 **18번 주제**, 「유연 배열 멤버」는 목록의 **26번 주제**가 정본이다.

## 한눈에 — 쉽게 말하면

**구조체는 멤버를 붙여 놓은 것이 아니다. 중간중간 구멍이 뚫려 있다.**

그 구멍의 자리와 크기를 **외우는 것이 아니라 물어보는 것**이 이 주제다 —\
`sizeof` 로 전체 크기를, `_Alignof` 로 정렬 요구를, `offsetof` 로 **구멍이 어디 있는지**를 묻는다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **주차장의 칸 선** — 아무 데나 못 대고 칸에 맞춰 댄다 | **정렬**(alignment) — `int` 는 4의 배수 주소에 |
| 큰 차는 **넓은 칸**에만 댈 수 있다 | `double` 은 8의 배수, `long double` 은 16의 배수 |
| 앞차가 칸을 어중간하게 먹으면 **빈 자리가 남는다** | **패딩**(padding) — 멤버 사이의 구멍 |
| 큰 차부터 대면 **빈 자리가 줄어든다** | 멤버를 큰 것부터 놓으면 `sizeof` 가 작아진다 |
| 주차장 **전체 길이**는 칸 크기의 배수여야 한다 | `sizeof` 는 `_Alignof` 의 배수다 |
| 칸 선을 지우면(`#pragma pack`) **더 많이 들어가지만** | 크기는 줄지만 **정렬 위반 UB** 가 생긴다 |

```text
   struct { char a; int b; char c; double d; };

   내가 기대한 것 (14바이트)
   +-+----+-+--------+
   |a| b  |c|   d    |
   +-+----+-+--------+

   실제 (24바이트)
   +-+---+----+-+-------+--------+
   |a|...| b  |c|.......|   d    |
   +-+---+----+-+-------+--------+
      ^^^        ^^^^^^^
      구멍 3     구멍 7          ★ 10바이트가 구멍이다
```

- 이 그림의 구멍 위치를 **`offsetof` 로 직접 물어봤다.** 외운 것이 아니다.
- 그리고 **멤버 순서만 바꾸면 24가 16이 된다.**

> **정렬(alignment)** — 어떤 타입의 객체가 놓일 수 있는 주소의 배수 조건.\
> 예: `int` 의 정렬이 4라는 것은 `int` 객체의 주소가 **4의 배수**여야 한다는 뜻이다. `_Alignof(int)` 로 물어본다.

> **패딩(padding)** — 정렬을 맞추려고 멤버 사이나 구조체 끝에 넣는 빈 바이트.\
> 예: `char` 다음에 `int` 가 오면 3바이트를 버린다. **그 값은 불확정이다.**

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `sizeof` 는 **언제 컴파일 시간에 정해지고 언제 아닌가** — 피연산자는 평가되는가.
2. 구조체의 크기는 **누가 어떤 규칙으로** 정하는가 — 구멍이 어디에 생기는지 어떻게 보는가.
3. 정렬을 **깨뜨리면**(`#pragma pack`) 무엇을 얻고 무엇을 잃는가.

## 동작 방식

### (1) `sizeof` 의 세 얼굴

**언제 쓰나** — 배열 원소 수를 세거나 `malloc` 크기를 계산할 때.

```text
sizeof(int)        = 4   <- 괄호 필수
sizeof i           = 4   <- 괄호 없이도 된다
sizeof i + 1       = 5   <- ★ (sizeof i) + 1 로 묶인다
sizeof a           = 40   원소 수 = 10
sizeof s           = 8   <- 포인터 크기 (문자열 길이가 아니다)
sizeof "hello"     = 6   <- 배열이다 ('\0' 포함)
--- sizeof 의 피연산자는 평가되지 않는다 ---
sizeof(boom())     = 4
side = 0  (0 이면 boom 이 안 불린 것)
sizeof(j++)        = 4, 그 뒤 j = 0
sizeof 의 결과 타입 -> unsigned long (= size_t)
```

```text
   sizeof 의 세 얼굴

   ① 타입에 묻는다      sizeof(int)        ★ 괄호가 필수다
   ② 식에 묻는다        sizeof i           괄호 없이도 된다 (단항 연산자)
   ③ 배열에 묻는다      sizeof a           ★ 원소 전체의 바이트 수

   그리고 셋 다 ★ 컴파일 시간에 정해진다 (VLA 만 예외 — (7))
```

그림 해설 (한 단계씩):

- **`sizeof i + 1` 이 5** 다. `sizeof` 는 단항 연산자라 `+` 보다 **먼저** 묶인다.\
  `sizeof(i + 1)` 을 쓰려면 괄호를 직접 쳐야 한다.
- **`sizeof s` 는 8** 이다 — `char *` 의 크기다. 문자열 길이가 아니다.\
  `sizeof "hello"` 는 **6** 이다 — 리터럴은 `char[6]` 배열이고 `'\0'` 을 센다.
- ★ **피연산자가 평가되지 않는다.** `sizeof(boom())` 뒤에도 `boom` 이 안 불렸고(`side = 0`),\
  `sizeof(j++)` 뒤에도 `j` 가 **0 그대로**다.
- 결과 타입은 **`size_t`**(여기선 `unsigned long`)다. [02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)·[03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)가 사고의 씨앗으로 다룬 그 타입이다.

비용 — 없다. **기계어에 흔적이 없다**(상수가 된다).

### (2) ★★ 멤버 순서만 바꾸면 크기가 달라진다 — 이 주제의 본체

**언제 쓰나** — 구조체를 선언할 때마다. 배열로 100만 개 만들 거면 특히.

```c
struct Bad  { char a; int b; char c; double d; };   /* 나쁜 순서 */
struct Good { double d; int b; char a; char c; };   /* 큰 것부터 */
```

```text
멤버 크기: char=1 int=4 double=8
멤버 정렬: char=1 int=4 double=8

Bad          sizeof=24 _Alignof=8
Good         sizeof=16 _Alignof=8

struct Bad  offsets: a=0 b=4 c=8 d=16
struct Good offsets: d=0 b=8 a=12 c=13

멤버 크기 합 = 14
```

`offsetof` 로 잰 자리를 **바이트 지도**로 그렸다(`.` 이 구멍).

```text
struct Bad   a...bbbbc.......dddddddd   (24 바이트, '.' 이 구멍)
struct Good  ddddddddbbbbac..   (16 바이트, '.' 이 구멍)
```

그리고 **실제 메모리로 한 번 더 대조했다** — `0xFF` 로 채운 뒤 멤버에만 0을 넣었다.

```text
struct Bad 의 실제 바이트 (0xFF 로 채우고 멤버만 0 대입):
00 ff ff ff 00 00 00 00
00 ff ff ff ff ff ff ff
00 00 00 00 00 00 00 00
  -> ff 로 남은 자리가 패딩이다
```

```text
   struct Bad (24바이트)                      struct Good (16바이트)

   0  a        char                          0  d d d d d d d d   double
   1  .  ) 3바이트 구멍                        8  b b b b         int
   2  .  )                                   12  a               char
   3  .  )                                   13  c               char
   4  b b b b   int                          14  .  ) 2바이트 구멍
   8  c        char                          15  .  )
   9  .  )                                   ----------------------
  10  .  ) 7바이트 구멍                         구멍 2바이트
  ...   )
  15  .  )
  16  d d d d d d d d   double
   ----------------------
   구멍 10바이트                              ★ 같은 멤버, 8바이트 차이
```

그림 해설 (한 단계씩):

- **멤버 크기의 합은 14** 인데 `Bad` 는 24, `Good` 은 16이다. **구멍이 10바이트와 2바이트.**
- 규칙은 셋이다.
  - 각 멤버는 **자기 정렬의 배수 자리**에서 시작한다(`b` 가 1이 아니라 4에서 시작).
  - 구조체의 정렬은 **가장 엄한 멤버의 정렬**이다(여기선 `double` 의 8).
  - **`sizeof` 는 그 정렬의 배수**여야 한다 — 배열로 늘어놓아도 각 원소가 정렬을 지켜야 하니까.
- 마지막 규칙을 여섯 구조체로 확인했다.

```text
A         sizeof= 1 _Alignof= 1  sizeof % _Alignof = 0
B         sizeof= 4 _Alignof= 2  sizeof % _Alignof = 0
C         sizeof= 8 _Alignof= 4  sizeof % _Alignof = 0
D         sizeof=16 _Alignof= 8  sizeof % _Alignof = 0
E         sizeof=16 _Alignof= 8  sizeof % _Alignof = 0
F         sizeof= 3 _Alignof= 1  sizeof % _Alignof = 0
```

- **나머지가 전부 0** 이다. 그래서 `struct E { double a; char b; }` 가 9가 아니라 **16**이다 — 끝에 7바이트가 붙는다.
- 배열로 늘어놓아도 **그대로 3배**다.

```text
sizeof(struct T)=8  배열 3개=24  (3배인가: 1)
```

비용 — **순서를 바꾸는 것은 공짜다.** 큰 것부터 놓으면 대개 최소가 된다.

### (3) `offsetof` 로 구멍을 직접 본다

**언제 쓰나** — 왜 이 크기가 나왔는지 설명해야 할 때. 직렬화 코드를 쓸 때.

```c
#include <stddef.h>
offsetof(struct Bad, d)        /* -> 16 */
```

```text
#define offsetof(TYPE,MEMBER) __builtin_offsetof (TYPE, MEMBER)
```

```text
   offsetof(struct Bad, b) = 4
                              ^
   0        4        8              16
   +--------+--------+--------------+
   | a +패딩 |  b  c  |    +패딩     | d ...
   +--------+--------+--------------+

   -> 앞 멤버의 끝과 다음 offsetof 사이의 차이가 ★ 구멍의 크기다
      (a 는 1바이트인데 b 가 4에서 시작 -> 구멍 3)
```

그림 해설 (한 단계씩):

- **gcc 의 `offsetof` 는 `__builtin_offsetof`** 다. 옛날 관용구 `((size_t)&(((T *)0)->M))` 가 아니다.
- 옛날 관용구는 **널 포인터를 역참조하는 모양**이라 도구가 잡는다.

```text
oldoff.c:7:45: runtime error: member access within null pointer of type 'struct S'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior oldoff.c:7:45 
```

  ★ 단 **이것은 clang 의 UBSan 만 잡았다.** gcc 의 UBSan 은 조용했다(값은 둘 다 8로 맞았다).
- **비트필드 멤버에는 못 쓴다** — 주소가 없기 때문이다.

```text
bf.c:3:46: error: attempt to take address of bit-field structure member ‘f’
```

비용 — 없다. 컴파일 시간 상수다.

### (4) `_Alignof`·`_Alignas` — 물어보고 지시한다

**언제 쓰나** — 캐시 라인에 맞추거나, SIMD 버퍼를 만들거나, 「왜 이 크기냐」를 따질 때.

```text
_Alignof: char=1 short=2 int=4 long=8 double=8 long double=16
_Alignof(void*)=8  _Alignof(struct S)=8  sizeof(struct S)=16
_Alignof(max_align_t)=16 sizeof(max_align_t)=32
alignof (stdalign.h) 로도 같은 값: 4
_Alignas(64) 배열 주소 % 64 = 0
_Alignas(16) 배열 주소 % 16 = 0
malloc(1) 주소 % _Alignof(max_align_t) = 0
aligned_alloc(64,128) 주소 % 64 = 0
_Static_assert 세 개 통과
```

```text
   물어보는 쪽                 지시하는 쪽
   +----------------------+   +----------------------+
   | _Alignof(T)          |   | _Alignas(N) 선언     |
   | -> 이 타입의 정렬은?   |   | -> 이 객체를 N 배수에  |
   |                      |   |                      |
   | offsetof(T, m)       |   | ★ 줄이는 것은 안 된다  |
   | -> 이 멤버는 몇 번째?  |   |                      |
   +----------------------+   +----------------------+
```

그림 해설 (한 단계씩):

- **`_Alignof(long double)` 이 16** 이다. [04번 형제](../04-floating-point-types-and-conversions/)가 「16바이트인데 유효 비트는 64」라고 본 그 타입이다.
- **`max_align_t` 의 정렬이 16** 이고, **`malloc` 이 그 배수를 돌려준다** — 실측으로 나머지가 0이었다.\
  그래서 `malloc` 으로 받은 메모리는 **어떤 타입으로 써도 정렬이 맞는다.**
- **`_Alignas` 로 정렬을 줄일 수는 없다.**

```text
alred.c:2:34: error: ‘_Alignas’ specifiers cannot reduce alignment of ‘x’
```

- 늘리는 것은 된다 — `_Alignas(64) int x;` 의 `_Alignof(x)` 가 **64** 이고 주소도 64의 배수였다.
- **철자가 세 가지**다.

```text
   C11 ~ C17       _Alignof / _Alignas            헤더 없이
                   alignof  / alignas             ★ <stdalign.h> 필요
   C23             alignof  / alignas             헤더 없이
```

  `-std=c2x` 에서 헤더 없이 `alignof(double)` 이 `8` 을 냈고, `-std=c17` 에서는 에러였다((8) 참조).

비용 — `_Alignas(64)` 는 **메모리를 더 쓴다.** 64바이트 경계에 맞추느라 앞뒤가 비는 자리가 생긴다.

### (5) `_Static_assert` — 배치를 컴파일 타임에 못 박는다

**언제 쓰나** — 구조체 배치에 의존하는 코드를 쓸 때. **이 주제의 방어선이다.**

```c
_Static_assert(sizeof(struct S) == 16, "이 ABI 에서 struct S 는 16바이트");
_Static_assert(offsetof(struct S, d) == 8, "d 는 8번째 바이트에서 시작");
_Static_assert(_Alignof(struct S) == _Alignof(double), "구조체 정렬 = 가장 엄한 멤버");
```

```text
_Static_assert 세 개 통과
```

틀리면 **컴파일이 멈춘다.**

```text
sa2.c:3:1: error: static assertion failed: "assumed no padding"
    3 | _Static_assert(sizeof(struct S) == 9, "assumed no padding");
      | ^~~~~~~~~~~~~~
```

```text
   런타임 검사 (assert)              컴파일 타임 검사 (_Static_assert)
   +--------------------------+     +--------------------------+
   | 그 줄이 실행돼야 안다      |     | ★ 빌드가 안 된다          |
   | NDEBUG 로 사라진다        |     | 절대 안 사라진다          |
   | 테스트가 그 경로를 타야 함 |     | 다른 머신에서 빌드해도 걸림 |
   +--------------------------+     +--------------------------+
```

그림 해설 (한 단계씩):

- **「이 구조체는 16바이트다」는 이 플랫폼의 사실**이지 언어의 보장이 아니다.\
  `_Static_assert` 를 두면 **다른 플랫폼에서 빌드할 때 거기서 멈춘다.**
- 「돌려 보고 아는 것」과 「빌드가 막는 것」은 등급이 다르다 —\
  [02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)가 같은 수법을 타입 크기에 썼다.
- ★ 실무 팁 — **메시지는 ASCII 로 쓴다.** 한글 메시지를 넣었더니 진단에 **8진 이스케이프로 깨져 나왔다**\
  (앞부분만 옮기면 `"\37777777755\37777777614\37777777650\37777777753…"` — 전문은 정답 9번에 있다).\
  메시지가 안 읽히면 단언의 값이 절반 사라진다.

비용 — 없다. 코드가 한 바이트도 안 생긴다.

### (6) `#pragma pack` — 무엇을 얻고 무엇을 잃나

**언제 쓰나** — 파일 형식·네트워크 패킷 구조체를 「그대로」 매핑하고 싶을 때.

```c
#pragma pack(push, 1)
struct Packed { char a; int b; char c; double d; };
#pragma pack(pop)
```

```text
struct Bad    sizeof=24 _Alignof=8  offsets a=0 b=4 c=8 d=16
struct Packed sizeof=14 _Alignof=1  offsets a=0 b=1 c=5 d=6
&p.b 가 4로 나눠지나: 0
*q = 0x41424344
```

```text
   struct Bad (24)                  struct Packed (14)
   +-+---+----+-+-------+--------+  +-+----+-+--------+
   |a|...| b  |c|.......|   d    |  |a| b  |c|   d    |
   +-+---+----+-+-------+--------+  +-+----+-+--------+
    0    4     8        16           0 1    5 6
    _Alignof = 8                     _Alignof = ★ 1

   얻은 것: 10바이트                 잃은 것: ★ b 와 d 가 정렬을 안 지킨다
```

정렬이 깨진 멤버의 주소를 역참조하면 **[05번 형제](../05-explicit-casts-and-pointer-conversions/)가 본 그 UB** 다.

```text
pack.c:20:8: runtime error: store to misaligned address 0x5d0f2cfc6199 for type 'int', which requires 4 byte alignment
pack.c:21:5: runtime error: load of misaligned address 0x5d0f2cfc6199 for type 'int', which requires 4 byte alignment
```

그림 해설 (한 단계씩):

- **`_Alignof` 가 1이 된다.** 「아무 주소에나 놓아도 된다」는 선언이고, 그러면 멤버들이 정렬을 못 지킨다.
- `&p.b` 는 4의 배수가 **아니었다**(`0`). 그 포인터를 역참조하면 UBSan 이 두 줄을 낸다.
- **멤버를 직접 읽고 쓰는 것은 컴파일러가 알아서 처리**한다(`p.b = 1` 은 안전하다).\
  **위험한 것은 그 멤버의 주소를 꺼내 쓰는 것**이다.
- ★★ **그런데 gcc 는 `#pragma pack` 에 대해 경고하지 않는다.**

```text
pack2.c:10:14: warning: taking address of packed member of ‘struct Q’ may result in an unaligned pointer value [-Waddress-of-packed-member]
```

```text
[] 1
[-Wall] 1
[-Wall -Wextra] 1
[-Wall -Wextra -Waddress-of-packed-member] 1
```

  이 한 건은 **`__attribute__((packed))` 로 선언한 `struct Q`** 의 줄이다.\
  같은 소스의 `#pragma pack` 짜리 `struct P` 줄에는 **아무 말도 안 나왔다.**\
  두 구조체의 배치는 **완전히 같은데** 말이다.

```text
P: sizeof=5 _Alignof=1 offset(b)=1
Q: sizeof=5 _Alignof=1 offset(b)=1
```

- ★ **같은 위험을 하나는 잡고 하나는 안 잡는다.** `-Wall -Wextra` 에서도, 플래그를 명시해도 마찬가지다.\
  (clang 도 `struct Q` 쪽만 잡았다.) **「경고가 없다」가 「안전하다」가 아니라는 가장 싼 증거**다.

비용 — 크기 10바이트를 얻고 **정렬 보장과 경고를 둘 다 잃는다.**\
이식 가능한 대안은 **`memcpy` 로 바이트를 직접 옮기는 것**이다([05번 형제](../05-explicit-casts-and-pointer-conversions/)와 같은 답).

### (7) 예외 둘 — VLA 와 유연 배열 멤버

**언제 쓰나** — `sizeof` 가 「언제나 컴파일 시간 상수」인지 확인할 때.

**VLA 는 `sizeof` 가 런타임에 계산되고, 피연산자도 평가된다.**

```text
시작 호출 수 = 0
sizeof(int[n()]) = 16 뒤 호출 수 = 1
VLA a 의 sizeof = 12 (m=3)
m 을 100 으로 바꾼 뒤 sizeof a = 12  <- 배열을 만든 시점의 값이다
sizeof(j++) 뒤 j = 0
```

```text
   고정 배열                       VLA
   +--------------------------+   +--------------------------+
   | sizeof a  -> 컴파일 상수  |   | sizeof a  -> ★ 런타임 계산 |
   | 피연산자 평가 안 함        |   | 피연산자 ★ 평가한다        |
   | sizeof(j++) 뒤 j 그대로   |   | sizeof(int[n()]) 가 n() 호출|
   +--------------------------+   +--------------------------+
```

- `sizeof(int[n()])` 를 한 번 쓰자 **`n()` 호출 수가 0에서 1로 늘었다.**
- VLA 의 `sizeof` 는 **배열을 만든 시점의 크기**를 기억한다 — `m` 을 100으로 바꿔도 12 그대로다.
- 정본은 목록의 **18번 주제**.

**유연 배열 멤버는 `sizeof` 가 그것을 세지 않는다.**

```c
struct Buf { int n; int a[]; };       /* C99 유연 배열 멤버 */
```

```text
sizeof(struct Buf) = 4   <- a[] 를 안 센다
offsetof(struct Buf, a) = 4
한 번 할당한 크기 = 24, a[4] = 16
```

```text
   struct Buf { int n; int a[]; };

   sizeof(struct Buf) = 4          offsetof(a) = 4
   +----+
   | n  |            <- 이것만 센다
   +----+
   |    a[] 는 크기가 0 으로 취급된다

   malloc(sizeof *b + n * sizeof b->a[0])
   +----+----+----+----+----+----+
   | n  |a[0]|a[1]|a[2]|a[3]|a[4]|   = 4 + 5*4 = 24
   +----+----+----+----+----+----+
   -> 헤더와 데이터가 ★ 한 번의 할당으로 붙어 있다
```

- ASan 으로 돌려도 **통과**했다 — 할당 크기 계산이 맞다는 확인이다.
- 정본은 목록의 **26번 주제**.

비용 — VLA 는 스택을 쓴다(목록의 **18번 주제**). 유연 배열 멤버는 **할당 한 번**으로 줄여 준다.

## 문법 — 형태와 규칙

### 형태

```c
sizeof(타입)          /* 괄호 필수 */
sizeof 식             /* 괄호 선택 — 단항 연산자다 */
sizeof(식)

#include <stddef.h>
offsetof(구조체타입, 멤버)      /* size_t */

_Alignof(타입)                 /* C11 — 크기가 아니라 정렬 */
_Alignas(N)      선언          /* C11 — 늘리기만 된다 */
_Alignas(타입)   선언

_Static_assert(정수상수식, "메시지");   /* C11 */
static_assert(정수상수식, "메시지");    /* C23 — 헤더 없이 */
alignof(타입)                          /* C23 — 헤더 없이 */
```

### 금지 사례 — 걸리는 것과 안 걸리는 것

```c
/* (1) 함수 파라미터의 배열에 sizeof -> 경고, 답은 포인터 크기 */
void f(int a[10]) { size_t n = sizeof a / sizeof a[0]; }

/* (2) 불완전 타입에 sizeof -> 에러 */
struct S; sizeof(struct S);

/* (3) 빈 구조체 -> ★ gcc 는 받아 준다 (C++ 과 다르다) */
struct Empty { };

/* (4) 비트필드에 offsetof -> 에러 */
struct B { unsigned f : 3; }; offsetof(struct B, f);

/* (5) memcmp 로 구조체 비교 -> ★ 안 걸린다. 패딩 때문에 틀린다 */
memcmp(&x, &y, sizeof x);

/* (6) packed 멤버의 주소 -> __attribute__ 는 경고, #pragma pack 은 ★ 침묵 */
int *q = &packed.b;
```

(1)과 (4)의 출력이다.

```text
param.c:2:72: warning: ‘sizeof’ on array function parameter ‘a’ will return size of ‘int *’ [-Wsizeof-array-argument]
밖에서 sizeof(a) = 40
함수 안  sizeof(a) = 8
```

```text
bf.c:3:46: error: attempt to take address of bit-field structure member ‘f’
```

(3)은 **컴파일러가 표준에서 벗어난 자리**다.

```text
0
```

```text
empty.c:2:8: warning: struct has no members [-Wpedantic]
```

```text
empty.c:2:8: error: struct has no members [-Wpedantic]
```

```text
1
```

- 위에서부터 gcc 기본(`sizeof` 가 **0**) · `-pedantic`(경고) · `-pedantic-errors`(에러) · **같은 소스를 C++ 로**(`1`).
- ★ **C 에는 빈 구조체가 없다.** gcc 가 확장으로 받아 주고 크기를 0으로 준다.\
  **C++ 은 빈 클래스의 크기를 1로 정해 놓았다** — 같은 소스가 언어에 따라 0과 1을 낸다.

### 규칙 불릿

- `sizeof` 의 결과 타입은 **`size_t`**(부호 없음)다.
- **피연산자는 평가되지 않는다** — VLA 만 예외.
- `sizeof(char)` 는 **언제나 1** 이다([02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)).
- 각 멤버는 **자기 정렬의 배수 자리**에서 시작하고, 구조체의 정렬은 **가장 엄한 멤버의 정렬**,\
  **`sizeof` 는 그 정렬의 배수**다. 그래서 끝에도 패딩이 붙을 수 있다.
- **멤버 순서를 바꾸면 크기가 바뀐다.** 큰 것부터 놓으면 대개 최소가 된다.
- **패딩의 값은 불확정**이다 — `memcmp` 로 구조체를 비교하면 안 된다.
- `offsetof` 는 **비트필드 멤버에 못 쓴다.**
- `_Alignas` 는 정렬을 **늘리기만** 할 수 있다.
- `_Static_assert` 는 **정수 상수식**만 받고, 참이면 코드가 한 바이트도 안 생긴다.
- **유연 배열 멤버는 `sizeof` 가 안 센다.** `sizeof *p + n * sizeof p->a[0]` 로 할당한다.

## 어디서 틀리나

### 1. 멤버 크기를 더해서 `sizeof` 를 예측한다

- 합이 14인데 실제는 **24**(순서 나쁨) 또는 **16**(순서 좋음)이다.
- ★ **`offsetof` 로 물어보는 것이 유일하게 맞는 방법**이다. 손으로 계산하면 틀린다.
- 「끝에도 패딩이 붙는다」를 빠뜨리기 쉽다 — `struct { double; char; }` 가 9가 아니라 **16**이다.

### 2. `memcmp` 로 구조체를 비교한다

```text
sizeof(struct T)=8  배열 3개=24  (3배인가: 1)
sizeof(struct Tail)=8 offsets b=0 a=4  <- 끝 3바이트가 패딩
멤버는 같은데 memcmp = -255  (0 이 아니면 다르다고 본 것)
멤버로 비교하면 같은가: 1
```

- 멤버 값이 **전부 같은데 `memcmp` 가 `-255`** 를 돌려줬다. **패딩 바이트가 달랐기 때문**이다.
- 경고는 **한 건도 없다.**
- 막는 법: **멤버끼리 비교**한다. 또는 만들 때 `memset(&x, 0, sizeof x)` 로 패딩까지 0으로 맞춘다\
  (그러면 대입으로 복사했을 때 패딩이 다시 불확정이 될 수 있다 — 안전한 답은 멤버 비교다).

### 3. 함수 안에서 `sizeof(배열)` 로 원소 수를 센다

- 파라미터의 배열은 **포인터로 감쇠**한다 — 밖에서 40, 안에서 **8**.
- `-Wsizeof-array-argument`(**플래그 없이도 켜져 있다**)가 잡아 준다. 정본은 [목록의 **16번 주제**](../16-array-pointer-decay-and-function-parameters/).
- 원소 수를 함께 넘기거나, 매크로를 **호출자 쪽에서** 쓴다.

### 4. `#pragma pack` 을 「크기를 줄이는 옵션」으로 읽는다

- 크기는 24 → **14** 로 줄지만 `_Alignof` 가 **1** 이 되어 멤버 주소가 정렬을 안 지킨다.
- 그 주소를 역참조하면 **UBSan 이 두 줄**을 낸다.
- ★★ **그리고 `#pragma pack` 쪽은 gcc 가 경고하지 않는다** — `__attribute__((packed))` 만 잡는다.\
  배치가 완전히 같은데도 그렇다.
- 이식 가능한 답은 **`memcpy` 로 바이트를 직접 옮기는 것**이다.

### 5. `sizeof` 의 피연산자에 부작용을 넣는다

- `sizeof(j++)` 뒤에 `j` 가 **안 늘어난다.** 평가되지 않는다.
- 그런데 **VLA 면 평가된다** — `sizeof(int[n()])` 가 `n()` 을 불렀다.
- 「평가 안 된다」를 외우지 말고 「**VLA 가 아니면 평가 안 된다**」로 기억한다.

### 6. 「빈 구조체」를 C 에서 쓴다

- gcc 기본에서는 `sizeof` 가 **0** 이고 경고도 없다. `-pedantic` 이라야 말한다.
- **C++ 로 컴파일하면 1** 이다. 같은 헤더를 두 언어에서 쓰면 **배치가 어긋난다.**

## 구현 세부사항 대 언어 보장

C 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★ **이 주제는 「구현 정의」가 본체**다 — 구조체 배치의 구체적인 수치는 전부 거기에 있고,\
표준이 주는 것은 **「순서는 지킨다」와 「`sizeof` 는 정렬의 배수다」** 같은 뼈대뿐이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | `sizeof(char)` == 1 · 결과 타입이 `size_t` · **피연산자를 평가하지 않는 것**(VLA 제외) · **멤버가 선언 순서대로 배치**되는 것 · 첫 멤버의 `offsetof` 가 0인 것 · **`sizeof` 가 `_Alignof` 의 배수**인 것 · 유연 배열 멤버를 `sizeof` 가 안 세는 것 · `_Alignas` 로 **줄일 수 없는 것** · 불완전 타입·비트필드에 대한 에러 | `sizeof`·`offsetof` 실행 · `side = 0` · 여섯 구조체의 `sizeof % _Alignof` 전부 0 · 컴파일 에러 | — |
| **조건부 표준** | 매크로가 정의될 때만 | **해당 없음** | — | — |
| **구현 정의** | 문서화 의무가 있다 | **각 타입의 정렬**(`_Alignof(int)`=4 등) · **패딩의 양과 자리** · `sizeof(struct Bad)`=24 · `_Alignof(max_align_t)`=16 · `malloc` 이 그 정렬을 지키는 것 · **빈 구조체를 받아 주는 것**(확장) · `#pragma pack` 의 효과 | `offsetof` + **실제 바이트 덤프** 이중 확인 · `-pedantic` 으로 확장임을 확인 | 수치는 **찍어야만** 안다. 경고가 없다 |
| **미명시** | 몇 가지 중 하나 | **패딩 바이트의 값** — 어떤 값이든 될 수 있고 대입할 때마다 달라질 수 있다 | `memcmp` 가 `-255` (멤버는 같은데) | ★ **sanitizer 가 원리상 못 잡는다.** 경고도 0건 |
| **UB** | 아무 일이나 | **정렬이 안 맞는 멤버 주소의 역참조**(`#pragma pack`) · 패딩 바이트를 읽고 판단에 쓰는 것 | UBSan 이 `misaligned address` 2줄 | ★ **`#pragma pack` 쪽은 경고가 0건** — `__attribute__((packed))` 만 잡힌다 |

### 「구현 정의」를 두 겹으로 확인한다

이 주제의 수치는 전부 **`offsetof` 로 재고 실제 바이트로 대조**했다.

```text
struct Bad   a...bbbbc.......dddddddd   (24 바이트, '.' 이 구멍)
```

```text
00 ff ff ff 00 00 00 00
00 ff ff ff ff ff ff ff
00 00 00 00 00 00 00 00
```

- 위는 `offsetof` 에서 만든 지도, 아래는 `0xFF` 로 채운 메모리에 멤버만 0을 넣은 것이다.
- **`ff` 가 남은 자리와 `.` 자리가 정확히 일치**한다. 두 방법이 같은 답을 냈다.
- ★ **한 방법만 썼으면 「내가 그린 지도가 맞나」를 확인할 길이 없었다.**

### 「도구가 못 보는 것」을 층마다

| 사실 | `-Wall -Wextra` | `-pedantic` | UBSan | ASan |
|---|---|---|---|---|
| 멤버 순서가 나빠 8바이트를 버린 것 | 0건 | 0건 | 못 잡는다 | 못 잡는다 |
| `memcmp` 로 구조체 비교 | **0건** | 0건 | **못 잡는다** | 못 잡는다 |
| `#pragma pack` 멤버 주소 | **0건** | 0건 | (역참조하면 잡는다) | 못 잡는다 |
| `__attribute__((packed))` 멤버 주소 | **1건** | — | 〃 | — |
| 정렬 위반 역참조 | 0건 | — | **잡는다** | 못 잡는다 |
| 함수 파라미터의 `sizeof` | **1건**(`-Wall`) | — | — | — |
| 빈 구조체 | 0건 | **1건** | — | — |
| 옛날 `offsetof` 관용구 | 0건 | 0건 | **gcc 는 못 잡고 clang 은 잡는다** | — |

- ★ **패딩 관련 사고는 경고도 sanitizer 도 거의 못 본다.** 「미명시」 층이라 **원리상 잡을 수가 없다.**
- 이 주제에서 쓸 수 있는 유일한 자동 검사는 **`_Static_assert`** 다. 그래서 (5)가 이 주제의 방어선이다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 배열 원소 수 | `sizeof a / sizeof a[0]` (**배열이 보이는 곳에서**) | 함수 파라미터에서 같은 식 |
| `malloc` 크기 | `malloc(n * sizeof *p)` (**타입이 아니라 대상**) | `malloc(n * sizeof(int))` |
| 구조체 크기 근거 | **`offsetof` 로 찍는다** | 멤버 크기를 더한다 |
| 배치 고정 | **`_Static_assert`** | 주석에 적기 |
| 구조체 비교 | 멤버끼리 비교 | `memcmp` |
| 크기 줄이기 | **멤버 순서 바꾸기**(공짜) | `#pragma pack` |
| 파일·패킷 매핑 | **`memcpy` 로 바이트 옮기기** | packed 구조체를 그대로 캐스트 |
| 캐시 라인 맞추기 | `_Alignas(64)` | 수동 패딩 멤버 |
| 헤더+가변 데이터 | **유연 배열 멤버** | 포인터 멤버 + 별도 할당 |
| 정렬 큰 힙 메모리 | `aligned_alloc` | `malloc` + 수동 보정 |

판단 규칙 두 줄.

- **크기와 배치는 외우지 말고 물어본다** — `sizeof`·`_Alignof`·`offsetof` 가 그 질문이다.
- **물어본 답에 의존하는 코드를 쓰면 `_Static_assert` 를 같이 쓴다.** 다른 플랫폼에서 빌드가 멈추게.

## 핵심 문장

- **멤버 순서만 바꿔 `sizeof` 가 24에서 16이 됐다.** 멤버 크기의 합은 14다 — 나머지는 구멍이다.
- 구멍의 자리는 **`offsetof` 로 재고 실제 바이트 덤프로 대조**했다. **손으로 계산한 수치는 하나도 없다.**
- 규칙 셋 — 멤버는 **자기 정렬의 배수 자리**에서 시작하고, 구조체의 정렬은 **가장 엄한 멤버의 것**이며,\
  **`sizeof` 는 그 정렬의 배수**다(여섯 구조체에서 나머지가 전부 0이었다).
- **`sizeof` 의 피연산자는 평가되지 않는다** — `sizeof(j++)` 뒤에 `j` 가 그대로다.\
  **VLA 만 예외**로, `sizeof(int[n()])` 가 `n()` 을 실제로 불렀다.
- **`#pragma pack` 은 24를 14로 줄이는 대신 `_Alignof` 를 1로 만든다** — 멤버 주소를 역참조하면 UB 다.\
  ★ 그런데 **gcc 는 `#pragma pack` 에 경고하지 않고 `__attribute__((packed))` 만 잡는다.** 배치는 완전히 같다.
- **패딩 바이트의 값은 미명시**다 — 멤버가 전부 같은 두 구조체의 `memcmp` 가 `-255` 를 냈고,\
  **경고도 sanitizer 도 한 줄도 안 냈다.**
- **`_Static_assert` 가 이 주제의 유일한 자동 방어선**이다. 틀리면 빌드가 멈춘다.

## 관련 자료

- [`../README.md`](../README.md) — C 문법·API 주제 목록(이 주제는 08번)
- [`02-basic-types-sizes-and-fixed-width-integers/`](../02-basic-types-sizes-and-fixed-width-integers/) — **그쪽은 「`sizeof(int)` 가 왜 고정이 아닌가」까지, 여기는 「그 타입들을 모아 놓으면 무엇이 되나」부터.** `size_t`·`_Static_assert` 의 첫 등장이 거기
- [`03-integer-promotion-and-usual-arithmetic-conversions/`](../03-integer-promotion-and-usual-arithmetic-conversions/) — `sizeof` 의 결과가 `size_t`(부호 없음)라서 나는 사고
- [`05-explicit-casts-and-pointer-conversions/`](../05-explicit-casts-and-pointer-conversions/) — **정렬 위반 역참조가 왜 UB 인가**의 반대편. 거기는 캐스트가 만들고 여기는 `#pragma pack` 이 만든다
- [`../../../../data-representation/`](../../../../data-representation/) — **그쪽은 비트·바이트·엔디언까지, 여기는 그 바이트들이 구조체 안에서 어디에 놓이나부터**
- [목록의 **16번 주제**](../16-array-pointer-decay-and-function-parameters/) (배열-포인터 감쇠) — 함수 안에서 `sizeof(arr)` 가 달라지는 것의 정본
- 목록의 **18번 주제** (VLA) — `sizeof` 가 런타임인 유일한 자리
- 목록의 **21번 주제** (구조체 선언·초기화) · 목록의 **22번 주제** (구조체 패딩·정렬) — **패딩 규칙의 정본은 22번**. 여기는 **그것을 재는 도구** 쪽
- 목록의 **24번 주제** (비트필드) — `offsetof` 를 못 쓰는 멤버
- 목록의 **26번 주제** (유연 배열 멤버) — (7)이 정본으로 다뤄지는 곳
- 목록의 **37번 주제** (`malloc` 계열) — `malloc` 이 `max_align_t` 정렬을 지키는 계약
- 목록의 **50번 주제** (`<string.h>` 메모리 함수) — `memcmp` 로 구조체를 비교하면 안 되는 것의 정본
- 목록의 **53번 주제** (`assert` 와 `static_assert`) — `_Static_assert` 의 정본

## 용어 풀이

- **`sizeof`** — 객체·타입이 차지하는 바이트 수를 주는 단항 연산자. 결과 타입은 `size_t`.
- **`size_t`** — `sizeof` 의 결과 타입. 부호 없음. 여기서는 `unsigned long`.
- **정렬(alignment)** — 객체의 주소가 지켜야 하는 배수. `_Alignof` 로 물어본다.
- **패딩(padding)** — 정렬을 맞추려고 넣는 빈 바이트. **값은 미명시다.**
- **`offsetof`** — 구조체 시작에서 멤버까지의 바이트 수. gcc 는 `__builtin_offsetof` 로 구현한다.
- **`_Alignof`** — 타입의 정렬 요구를 묻는 연산자(C11). C23 부터 `alignof` 철자를 헤더 없이 쓴다.
- **`_Alignas`** — 객체의 정렬을 지시하는 지정자(C11). **늘리기만** 된다.
- **`max_align_t`** — 모든 스칼라 타입 중 가장 엄한 정렬을 갖는 타입. `malloc` 이 이 정렬을 지킨다.
- **`_Static_assert`** — 컴파일 시간 단언(C11). 거짓이면 컴파일이 멈춘다. C23 부터 `static_assert` 철자.
- **`#pragma pack`** — 패딩을 줄이는 컴파일러 지시. **표준이 아니고 ABI 를 바꾼다.**
- **유연 배열 멤버(flexible array member)** — 구조체 끝의 크기 없는 배열(C99). `sizeof` 가 안 센다.
- **VLA(가변 길이 배열)** — 크기가 런타임에 정해지는 배열. `sizeof` 가 상수가 아닌 **유일한** 자리.

---

## 더 들어가면

- **`alignas`/`static_assert` 철자는 C23 부터 헤더 없이** 쓸 수 있다. 던져서 확인했다.

```text
[c17] c23.c:2:15: error: expected declaration specifiers or ‘...’ before ‘sizeof’
[c2x] alignof(double)=8
```

  `-std=c17` 에서는 `<stdalign.h>`·`<assert.h>` 가 필요하고, 헤더를 넣으면 `alignof` 가 `_Alignof` 와 같은 값을 준다(실측 4).

- **`aligned_alloc` 은 C11** 이다. 실측에서 `aligned_alloc(64, 128)` 의 주소가 64의 배수였다.\
  POSIX 의 `posix_memalign` 과 달리 **크기가 정렬의 배수여야 한다**는 제약이 있는데, 그것을 어겼을 때\
  무엇이 나오는지는 **던져 보지 않았다.**

- **구조체 배치를 정렬 순으로 재배열하는 것은 컴파일러가 안 해 준다.** C 는 **선언 순서를 지킨다**고 정해 놓았다.\
  그래서 순서를 바꾸는 것이 **프로그래머의 일**이다. (Rust 는 기본적으로 재배열한다 — 논증은 [`../../../c-cpp-csharp.md`](../../../c-cpp-csharp.md) 쪽이다.)

- ★ **`-Wpadded` 가 이 주제의 구멍을 전부 이름으로 불러 준다.** 던져서 확인했다.

```text
pad.c:4:27: warning: padding struct to align ‘b’ [-Wpadded]
pad.c:4:45: warning: padding struct to align ‘d’ [-Wpadded]
pad.c:5:8: warning: padding struct size to alignment boundary with 2 bytes [-Wpadded]
```

  (2)의 `struct Bad` 에서 **`b` 앞과 `d` 앞** 두 구멍을, `struct Good` 에서 **끝의 2바이트**를 정확히 짚었다.\
  「표준 헤더의 구조체까지 전부 걸려서 못 쓴다」는 말을 들었는데, `<stdio.h>`·`<stddef.h>` 를 넣은 이 파일에서\
  **3건뿐**이었다 — **재현되지 않았다.** 다만 큰 프로젝트에서는 어떨지 **재 보지 않았다.**

- **캐시 라인 크기는 `_Alignas` 로 지정할 수 있지만 그 값을 표준으로 물어볼 방법은 없다.**\
  C++17 의 `hardware_destructive_interference_size` 같은 것이 C 에는 없다.\
  실무에서는 64를 상수로 박고 `_Static_assert` 로 지킨다. 이 머신의 실제 캐시 라인 크기는 **확인하지 않았다.**

- **패딩 바이트를 0으로 맞추고 싶으면** `memset(&x, 0, sizeof x)` 로 시작한 뒤 멤버를 채운다.\
  그러면 **구조체 대입(`y = x`)이 패딩까지 복사하나?** 던져서 확인했다 — `x` 를 0으로, `y` 를 `0xFF` 로 채우고 대입했다.

```text
-O0  : 대입 뒤 memcmp = 0 y 의 바이트: 01 00 00 00 02 00 00 00  
-O2  : 대입 뒤 memcmp = 0 y 의 바이트: 01 00 00 00 02 00 00 00  
```

  **두 수준 모두 `memcmp` 가 0** 이고 `y` 의 패딩 바이트가 `ff` 에서 `00` 으로 바뀌었다 — gcc 는 객체를 통째로 복사한다.\
  ★ **그런데 이것은 관찰이지 보장이 아니다.** 표준은 대입이 패딩을 어떻게 하는지 정하지 않는다\
  (「미명시」 층이다). **두 수준에서 같았다는 것이 오히려 함정**이다 — [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)의 「여러 판에서 같았다는 것이 보장이 아니다」와 같은 자리다.\
  안전한 답은 여전히 **멤버끼리 비교하는 것**이다.
