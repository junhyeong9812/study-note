# c/syntax/11 — 비트 연산과 시프트: 자리를 다루는 법과 **넘으면 안 되는 선** — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고·sanitizer 진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux(`CHAR_BIT=8` · `sizeof(int)=4`)에서 실제로 돌려 얻은 것이다.\
> 기본 플래그는 `-std=c17 -Wall -Wextra -pedantic`. ★ **UB 가 걸린 문항은 `-O0`\~`-Os` 다섯 벌을 전부 돌렸다.**
> ★★ **UB 문항의 「값」은 답이 아니다.** 답은 「**어느 층이고 누가 말해 주나**」다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 마스크 관용구 넷 — 한 자리만 건드린다

**출력**

```text
flags        00001010   0x0A  10
MASK         00000100   0x04  4
set  |=      00001110   0x0E  14
clear &=~    00001010   0x0A  10
toggle ^=    00001110   0x0E  14
test (flags & MASK) != 0 : 0
test (flags & 0x02) != 0 : 1
~flags(low8) 11110101   0xF5  245
~flags whole = 4294967285  (0xFFFFFFF5)
exit=0
```

**왜 그런가**

```text
   자리         7 6 5 4 3 2 1 0
   flags        0 0 0 0 1 0 1 0
   MASK         0 0 0 0 0 1 0 0    <- 2번 자리 하나

   |   설정   0 0 0 0 1 1 1 0   없으면 켠다 (이미 켜져 있으면 그대로)
   &~  해제   0 0 0 0 1 0 1 0   있으면 끈다 (원래 0 이라 변화 없음)
   ^   토글   0 0 0 0 1 1 1 0   뒤집는다 (두 번 하면 원래대로)
   &   검사   0 0 0 0 0 0 0 0   -> 0 -> 꺼져 있다
```

- **`~flags` 는 하위 8비트만 보면 `11110101`** 이지만 **전체는 `0xFFFFFFF5`**(= `4294967285`)다.\
  `~` 는 **타입 전체**를 뒤집는다 — 8비트만 뒤집는 연산자는 없다.
- ★ **`(flags & MASK) != 0` 의 괄호는 필수다.** 빼면 `flags & (MASK != 0)` 로 묶여 **`flags & 1`** 이 된다 —\
  [09번 형제](../09-operator-precedence-and-associativity/)에서 `&` 가 `!=` 보다 **약하다**는 것을 봤고, gcc 가 `-Wparentheses`(`-Wall`)로 말해 준다.
- **`|=` 는 여러 번 해도 결과가 같다**(멱등). `^=` 는 **홀수 번/짝수 번이 다르다.**

```text
===== 소스: ex.c (11-a 곁가지) =====
#include <stdio.h>
int main(void){
    unsigned flags = 0x0Au, MASK = 0x04u;
    printf("(flags & MASK) != 0 = %d\n", (flags & MASK) != 0);
    printf("flags & MASK != 0   = %u\n", flags & MASK != 0);
    unsigned f = 0x0Au;
    f |= MASK; printf("1회 = 0x%02X\n", f);
    f |= MASK; printf("2회 = 0x%02X\n", f);
    f |= MASK; printf("3회 = 0x%02X\n", f);
    unsigned g = 0x0Au;
    g ^= MASK; printf("^1회 = 0x%02X\n", g);
    g ^= MASK; printf("^2회 = 0x%02X\n", g);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
ex.c: In function ‘main’:
ex.c:5:55: warning: suggest parentheses around comparison in operand of ‘&’ [-Wparentheses]
    5 |     printf("flags & MASK != 0   = %u\n", flags & MASK != 0);
      |                                                  ~~~~~^~~~
(flags & MASK) != 0 = 0
flags & MASK != 0   = 0
1회 = 0x0E
2회 = 0x0E
3회 = 0x0E
^1회 = 0x0E
^2회 = 0x0A
```

- ★★ **이 값 두 개가 우연히 같다는 것에 주의하라.** `flags` 가 `0x0A` 라 `flags & 1` 도 `0` 이다 —\
  **괄호를 빼도 답이 같아 보이는 데이터**를 고르면 아무것도 증명하지 못한다.\
  **말해 준 것은 값이 아니라 `-Wparentheses` 경고 한 줄**이다([09번 형제](../09-operator-precedence-and-associativity/)가 같은 교훈을 적었다).
- `|=` 는 세 번 해도 `0x0E` 로 같고, `^=` 는 **두 번 하면 `0x0A` 로 돌아온다.**

### 2. 작은 타입을 뒤집으면 — **승격이 먼저 일어난다** ★★

**출력**

```text
ex.c: In function ‘main’:
ex.c:9:66: warning: promoted bitwise complement of an unsigned value is always nonzero [-Wsign-compare]
    9 |     printf("~c == 0 ? %d   /  (unsigned char)~c == 0 ? %d\n", ~c == 0, (unsigned char)~c == 0);
      |                                                                  ^~
sizeof c        = 1
sizeof (~c)     = 4
~c              = -256   (0xFFFFFF00)
(unsigned char)~c = 0 (0x0)
~c == 0 ? 0   /  (unsigned char)~c == 0 ? 1
~s              = -65536
c << 8          = 65280
(unsigned char)(c << 8) = 0
CHAR_BIT=8  sizeof(int)=4  INT_MAX=2147483647  UINT_MAX=4294967295
exit=0
```

**왜 그런가**

```text
   unsigned char c = 0xFF      8비트 :            1111 1111

   ★ ~ 를 계산하기 전에 c 가 int 로 승격된다  (03번의 정수 승격)
                              32비트 : 0000 0000 0000 0000 0000 0000 1111 1111
   그 32비트를 뒤집는다
                              32비트 : 1111 1111 1111 1111 1111 1111 0000 0000
                                       = 0xFFFFFF00 = ★ -256      sizeof 는 ★ 4
```

- **`sizeof c` 는 1 인데 `sizeof (~c)` 는 4 다** — 연산자가 **승격된 타입**에 작용하기 때문이다([03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)).
- **`~c` 는 `0` 이 아니라 `-256`** 이고 **부호 있는 값**이다. `0` 이 되는 것은 **다시 8비트로 자른** `(unsigned char)~c` 뿐이다.
- **경고는 1건**이고 문구는 **「promoted bitwise complement of an unsigned value is always nonzero」**,\
  플래그는 ★ **`-Wsign-compare`** 다. **`-Wall` 단독으로는 0건**이고 **`-Wextra` 에서 나온다.**
- **`if (~c)` 는 언제나 참이다.** 위 경고가 바로 그 이야기다.
- `c << 8` 이 **`65280`** 인 것도 같은 이유다 — 8비트 타입인데 **값이 8비트 밖으로 나간다.**

### 3. 시프트량이 변수일 때 셋 — UBSan 이 각각 다른 문구로 ★★★

**출력**

```text
===== 소스: ex.c (11-d) =====
#include <stdio.h>
int main(void) {
    int w = 32;
    volatile int n = -1;      /* 음수 시프트량 */
    volatile int m = 32;      /* 폭 이상 */
    volatile int v = 1;
    printf("v << n (n=-1) = %d\n", v << n);
    printf("v << m (m=32) = %d\n", v << m);
    volatile int big = 1073741824;   /* 2^30 */
    printf("big << 2      = %d\n", big << 2);   /* 부호 비트를 넘긴다 */
    volatile int neg = -8;
    printf("neg >> 1      = %d\n", neg >> 1);
    printf("w             = %d\n", w);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
(경고 ★ 0 건) exit=0

===== gcc -O0 / -O1 / -O2 / -O3 / -Os — 다섯 벌이 같다 =====
v << n (n=-1) = -2147483648
v << m (m=32) = 1
big << 2      = 0
neg >> 1      = -4
w             = 32
exit=0

===== gcc -fsanitize=undefined (recover 허용) =====
ex.c:7:38: runtime error: shift exponent -1 is negative
ex.c:8:38: runtime error: shift exponent 32 is too large for 32-bit type 'int'
ex.c:10:40: runtime error: left shift of 1073741824 by 2 places cannot be represented in type 'int'
(그 뒤 출력은 위와 같다)  exit=0

===== gcc -fsanitize=undefined -fno-sanitize-recover=all =====
ex.c:7:38: runtime error: shift exponent -1 is negative
exit=1
★ 한 줄뿐이다 — 첫 건에서 프로그램을 끝내기 때문이다.
```

**왜 그런가**

```text
   ① v << -1     "판을 뒤로 민다"        -> ★ UB
      관찰값 -2147483648  (x86 이 시프트량을 5비트로 가려 31 이 됐다)
   ② v << 32     "32칸 판을 32칸 민다"    -> ★ UB
      관찰값 1            (x86 이 32 & 31 = 0 으로 가렸다 — 안 민 것이다)
   ③ (2^30) << 2 "부호 비트를 넘긴다"     -> ★ UB
      관찰값 0
   ④ -8 >> 1     "음수를 오른쪽으로"      -> ★ 구현 정의 (UB 아님)
      값 -4. UBSan 이 이 줄에 대해 아무 말도 안 했다.
```

- **경고는 0건**이다. **시프트량이 변수라 컴파일러가 값을 모른다**(7번 답).
- **UBSan 은 셋을 각각 다른 문구로** 잡는다 — `shift exponent ... is negative` /\
  `... is too large for 32-bit type 'int'` / `left shift of ... cannot be represented in type 'int'`.
- ★★ **`-fno-sanitize-recover=all` 을 붙이면 한 줄만 나온다.** 첫 진단에서 **프로그램을 끝내는** 옵션이기 때문이다.\
  **「UBSan 이 한 건 냈다」는 「UB 가 하나다」가 아니다.** 전수를 보려면 **recover 를 허용**해 한 번 더 돌린다.
- ★ **UB 가 아닌 것은 `neg >> 1`** 이고 층은 **구현 정의**다(5번 답).
- **관찰된 값들은 전부** 「**하드웨어가 우연히 그렇게 한 것**」이지 C 의 답이 아니다.

### 4. `u` 한 글자를 붙이면 — UB 와 안전이 갈린다 ★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
(경고 ★ 0 건)
1 << 31        = -2147483648
1u << 31       = 2147483648
(int)(1u<<31)  = -2147483648
1u << 31 == INT_MIN ? 1
1 << 30        = 1073741824

===== gcc -Wall -Wextra -pedantic -Wshift-overflow=2 =====
ex.c:4:39: warning: result of ‘1 << 31’ requires 33 bits to represent, but ‘int’ only has 32 bits [-Wshift-overflow=]
    4 |     printf("1 << 31        = %d\n", 1 << 31);
      |                                       ^~

===== gcc -fsanitize=undefined =====
ex.c:4:39: runtime error: left shift of 1 by 31 places cannot be represented in type 'int'

===== clang -std=c17 -Wall -Wextra =====
(경고 ★ 0 건)
```

**왜 그런가**

```text
   1 << 31   (int = 부호 있는 32비트)
   자리       31 30 ...  1  0
   결과        1  0 ...  0  0     <- 31번은 ★ 부호 비트
   int 의 최대는 2^31 - 1 인데 결과는 2^31 -> ★ UB

   1u << 31  (unsigned = 부호 없는 32비트)
   결과        1  0 ...  0  0     <- 31번도 그냥 값의 자리
   unsigned 의 최대는 2^32 - 1 -> ★ 정의된 동작. 값은 2147483648
```

- **첫 줄은 `-Wall -Wextra -pedantic` 에서 0건**이다. gcc 도 clang 도 말이 없다.\
  ★ **`-Wshift-overflow=2` 를 켜야** 말해 준다 — 기본 레벨 1 은 **`1 << 31` 을 봐준다.**
- ★ **UBSan 은 잡는다.** **컴파일 타임 침묵과 런타임 진단이 엇갈리는 대표 자리**다.
- **`(int)(1u << 31)` 은 `INT_MIN`** 이었다. 이 변환(범위 밖 값 → 부호 있는 타입)은 **UB 가 아니라 구현 정의**다([05번 형제](../05-explicit-casts-and-pointer-conversions/)).
- 규칙은 한 줄이다 — ★ **마스크는 언제나 `1u << n`.**

### 5. 음수를 오른쪽으로 밀면 — 구현 정의이고 나눗셈이 아니다

**출력**

```text
===== gcc -O0 / gcc -O2 / clang -O2 — 세 벌이 같다 =====
-1 >> 1   = -1
-8 >> 1   = -4
-8 >> 2   = -2
-8 / 2    = -4
-8 / 4    = -2
0xFFFFFFFFu >> 1 = 0x7FFFFFFF
-7 >> 1   = -4   (-7/2 = -3)
===== gcc -fsanitize=undefined -fno-sanitize-recover=all =====
exit=0   (진단 ★ 0줄)
```

```text
===== gcc -O2 -S -masm=intel  (int sh(int v){ return v >> 1; }) =====
sh:
	endbr64
	mov	eax, edi
	sar	eax
	ret
```

**왜 그런가**

```text
   -1 을 한 칸 오른쪽으로 밀면 빈 왼쪽 칸을 무엇으로 채우나?

   산술 시프트                      논리 시프트
   1111 1111 -> 1111 1111           1111 1111 -> 0111 1111
   부호 비트를 복사                  0 을 채운다
   -1                               2147483647

   ★ C 는 "둘 중 하나" 라고만 한다 = 구현 정의.
```

- **`-1 >> 1` 이 `-1`** 이었다 — **부호 비트를 복사**했다는 뜻이다.
- ★ **어셈블리가 증거다.** `sar`(shift **a**rithmetic **r**ight)가 나왔다. 논리 시프트였다면 `shr` 였을 것이다.\
  **지어낼 수 없고 독자가 자기 머신에서 재현한다.**
- ★★ **`neg7 >> 1` 은 `-4` 인데 `neg7 / 2` 는 `-3` 이다.** 시프트는 **아래로**(−∞ 방향) 내리고\
  나눗셈은 **0 쪽으로** 자른다. **음수에서만 갈리므로 양수 테스트는 통과해 버린다.**
- **UBSan 은 한 줄도 안 낸다** — **UB 가 아니라 구현 정의**이기 때문이다. 3번의 셋은 같은 실행에서 다 잡혔다.
- `unsigned` 의 우시프트는 구현 정의가 아니다 — **언제나 0 을 채운다**(`0x7FFFFFFF`).

### 6. 같은 UB 를 일곱 벌로 돌리면 — 하나가 갈린다 ★★

**출력**

```text
===== 소스: ex.c (11-h) =====
#include <stdio.h>
static int sum_bits(int n) {
    int s = 0;
    for (int i = 0; i < n; i++) s += (1 << i);    /* i >= 31 이면 UB */
    return s;
}
int main(void) {
    printf("sum_bits(4)  = %d\n", sum_bits(4));
    printf("sum_bits(40) = %d\n", sum_bits(40));
    return 0;
}
```

```text
gcc   -O0 : sum_bits(4)  = 15   sum_bits(40) = 254
gcc   -O1 : sum_bits(4)  = 15   sum_bits(40) = 254
gcc   -O2 : sum_bits(4)  = 15   sum_bits(40) = 254
gcc   -O3 : sum_bits(4)  = 15   sum_bits(40) = 254
gcc   -Os : sum_bits(4)  = 15   sum_bits(40) = 254
clang -O0 : sum_bits(4)  = 15   sum_bits(40) = 254
clang -O2 : sum_bits(4)  = 15   sum_bits(40) = ★ 1

[gcc -O2 -Wall -Wextra -pedantic] 경고 0 건 exit=0

===== gcc -fsanitize=undefined (recover 허용) =====
ex.c:4:41: runtime error: left shift of 1 by 31 places cannot be represented in type 'int'
sum_bits(4)  = 15
sum_bits(40) = 254
exit=0
★ 진단은 ★ 한 줄이다.
```

**왜 그런가**

```text
   루프는 i = 0..39 를 돈다.
     i = 0..30   -> 정상
     i = 31      -> ★ 부호 비트를 넘기는 좌시프트 (UB)
     i = 32..39  -> ★ 폭 이상의 시프트량 (UB)
   즉 UB 를 ★ 아홉 번 지난다.

   그런데 UBSan 진단은 ★ 한 줄이고, 그것도 "by 31" 하나다.
   -> ★ 같은 소스 위치는 한 번만 보고한다.
      진단 줄 수는 UB 횟수가 아니다.
```

- **여섯 벌이 `254` 로 같았고 clang `-O2` 하나가 `1`** 이었다. **컴파일러가 아니라 같은 컴파일러의 최적화 수준**이 갈랐다.
- ★★ **「다섯 수준에서 같았다」를 근거로 삼았다면 여섯 번째에서 뒤집혔을 것이다.**\
  **한 수준만 돌리고 UB 의 값을 단정하면 그 문장이 틀린다.**
- **경고는 0건**이다 — 시프트량 `i` 가 변수이기 때문이다(7번 답).
- ★ 진단이 말한 것은 **`by 31`**(부호 비트 넘김)뿐이고 **`i >= 32` 의 「폭 이상」은 같은 줄이라 보고되지 않았다.**

### 7. 경고가 상수와 변수를 다르게 잡는 것 — **컴파일러가 값을 알아야 한다** ★★

**출력**

```text
===== 소스: ex.c (11-g) =====
#include <stdio.h>
int main(void) {
    int a = 1 << -1;          /* 상수: 음수 시프트량 */
    int b = 1 << 32;          /* 상수: 폭 이상 */
    int c = 1073741824 << 2;  /* 상수: 부호 비트를 넘긴다 */
    int d = 1 << 31;          /* 상수: 부호 비트 자리 */
    printf("%d %d %d %d\n", a, b, c, d);
    return 0;
}
```

```text
상수로 쓴 판  (ex.c 11-g 그대로)
[gcc                                ] ★ 3 건 exit=0     플래그를 하나도 안 줘도
[gcc -Wall                          ]   3 건 exit=0
[gcc -Wextra                        ]   3 건 exit=0
[gcc -Wall -Wextra                  ]   3 건 exit=0
[gcc -Wall -Wextra -pedantic        ]   3 건 exit=0
[gcc -Wall -Wno-shift-count-negative]   2 건 exit=0
[gcc -Wall -Wextra -Wno-shift-overflow] 2 건 exit=0

같은 것을 변수로 쓴 판
[gcc -Wall                          ] ★ 0 건 exit=0
[gcc -Wall -Wextra                  ] ★ 0 건 exit=0
[gcc -Wall -Wextra -pedantic        ] ★ 0 건 exit=0
[gcc -O2 -Wall -Wextra              ] ★ 0 건 exit=0
```

```text
ex.c:3:15: warning: left shift count is negative [-Wshift-count-negative]
ex.c:4:15: warning: left shift count >= width of type [-Wshift-count-overflow]
ex.c:5:24: warning: result of ‘1073741824 << 2’ requires 34 bits to represent, but ‘int’ only has 32 bits [-Wshift-overflow=]
```

**왜 그런가**

- **상수면 플래그 없이도 3건**이다 — `-Wshift-count-negative`·`-Wshift-count-overflow`·`-Wshift-overflow=` 는 **기본으로 켜져 있다.**
- ★★ **변수면 네 조합 전부 0건**이다. `-O2` 를 켜도 그렇다. **컴파일러가 시프트량을 모르기 때문**이고,\
  **실무의 시프트량은 대부분 변수**다.
- 어느 경고가 누구 것인지는 **`-Wno-…` 로 끄고 건수가 줄어드는지** 보면 갈린다(3건 → 2건).
- 그래서 변수 시프트량은 **① 시프트 직전 범위 검사 ② UBSan 을 CI 에 걸기 ③ 최적화 수준 여러 벌**로만 잡힌다.

### 8. sanitizer 가 침묵한 자리 — **설계이고, 10번과 같은 종류다** ★★

**답**

| 침묵한 자리 | 층 | 침묵의 종류 |
|---|---|---|
| `-1 >> 1` (이 주제) | **구현 정의** | ★ **원리상 못 본다** — UB 가 아니므로 UB sanitizer 의 대상이 아니다 |
| 인자 평가 순서 ([10번](../10-evaluation-order-and-sequence-points/)) | **미명시** | ★ **원리상 못 본다** — 같은 이유다 |
| `i = i++` ([10번](../10-evaluation-order-and-sequence-points/)) | **UB** | ★ **지금 안 본다** — UB 인데 기본 검사 집합에 항목이 없다 |
| 루프의 9회 UB (6번) | **UB** | ★ **한 번만 말한다** — 같은 소스 위치는 **첫 회만** 보고 |

- **버그가 아니라 설계다.** UBSan 은 **U(ndefined) B(ehavior) sanitizer** 이고,\
  **구현 정의와 미명시는 undefined 가 아니다.** ★ **범위 밖이지 놓친 것이 아니다.**
- ★★ **그래서 [10번 형제](../10-evaluation-order-and-sequence-points/)의 침묵과 여기 침묵은 같은 종류다** — 둘 다 「UB 가 아니라서」다.\
  다른 것은 **그 주제에서 그 층이 본체냐**뿐이다.
- **같은 소스 위치는 한 번만 보고한다.** 그래서 **「진단 한 줄」에서 「UB 가 한 번 일어났다」를 주장할 수 없다.**\
  주장할 수 있는 것은 「**적어도 한 번 일어났다**」까지다.

### 9. 비트필드는 어디까지 믿나 — **값은 이식되고 바이트는 아니다**

**출력**

```text
===== 소스: ex.c (11-i) =====
#include <stdio.h>
struct Flags {
    unsigned a : 1;
    unsigned b : 3;
    signed   c : 4;
    int      d : 4;
};
int main(void) {
    struct Flags f = { 1, 5, -3, 7 };
    printf("sizeof(struct Flags) = %zu\n", sizeof(struct Flags));
    printf("a=%u b=%u c=%d d=%d\n", f.a, f.b, f.c, f.d);
    f.b = 9;                       /* 3비트에 9 는 안 들어간다 */
    printf("b = 9 를 넣으면 b=%u\n", f.b);
    f.d = 8;                       /* int : 4 에 8 */
    printf("d = 8 을 넣으면 d=%d\n", f.d);
    unsigned char *p = (unsigned char *)&f;
    printf("바이트 = %02X %02X %02X %02X\n", p[0], p[1], p[2], p[3]);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
ex.c:12:11: warning: unsigned conversion from ‘int’ to ‘unsigned char:3’ changes value from ‘9’ to ‘1’ [-Woverflow]
ex.c:14:11: warning: overflow in conversion from ‘int’ to ‘signed char:4’ changes value from ‘8’ to ‘-8’ [-Woverflow]
sizeof(struct Flags) = 4
a=1 b=5 c=-3 d=7
b = 9 를 넣으면 b=1
d = 8 을 넣으면 d=-8
바이트 = D3 78 00 00

===== clang -std=c17 -Wall -Wextra =====
ex.c:12:9: warning: implicit truncation from 'int' to bit-field changes value from 9 to 1 [-Wbitfield-constant-conversion]
ex.c:14:9: warning: implicit truncation from 'int' to bit-field changes value from 8 to -8 [-Wbitfield-constant-conversion]
2 warnings generated.
sizeof(struct Flags) = 4
a=1 b=5 c=-3 d=7
b = 9 를 넣으면 b=1
d = 8 을 넣으면 d=-8
바이트 = D3 08 00 00
```

**왜 그런가**

```text
   같은 구조체 · 같은 값 · 같은 플래그

   gcc   -> 바이트 = D3 ★78 00 00
   clang -> 바이트 = D3 ★08 00 00

   필드 값은 양쪽 다 a=1 b=5 c=-3 d=-8 로 같다.
   ★ 다른 것은 "아무도 안 쓰는 자리" 에 남은 비트다.
```

- **`sizeof` 는 4**, 필드 값은 **`a=1 b=5 c=-3 d=7`** 이고 **두 컴파일러가 같다.**
- **넘치는 값은 조용히 잘린다** — `b = 9` → `1`, `d = 8` → `-8`. ★ **상수를 넣을 때만 경고가 난다**(변수면 7번과 같은 이유로 침묵).
- ★★ **앞 4바이트가 다르다.** **비트필드의 할당 순서·패딩·미사용 비트가 구현에 맡겨져 있다.**\
  그래서 **구조체를 바이트로 읽어 프로토콜·파일 포맷에 쓰면 그 자리에서 깨진다.**
- ★ **`int d : 4` 의 부호는 구현이 정한다.** 여기서는 **부호 있는 것**으로 잡혔고(`8` → `-8`),\
  gcc 의 진단도 그것을 **`signed char:4`** 라고 적었다. **`signed`·`unsigned` 를 명시하지 않으면 이식되지 않는다.**

### 10. 「경고 0건」이 두 가지 뜻인 자리 ★★

**출력**

```text
[gcc -std=c89 -Wall -Wextra          ] 경고 ★ 0 건  exit=0
[gcc -std=c89 -Wall -Wextra -pedantic] 경고   1 건  exit=0
[gcc -std=c99 -Wall -Wextra          ] 경고 ★ 0 건  exit=0
[gcc -std=c99 -Wall -Wextra -pedantic] 경고   1 건  exit=0
[gcc -std=c17 -Wall -Wextra          ] 경고 ★ 0 건  exit=0
[gcc -std=c17 -Wall -Wextra -pedantic] 경고   1 건  exit=0
[gcc -std=c23 -Wall -Wextra          ] 경고 ★ 0 건  ★ exit=1
[gcc -std=c23 -Wall -Wextra -pedantic] 경고 ★ 0 건  ★ exit=1
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
ex.c: In function ‘main’:
ex.c:3:21: warning: binary constants are a C2X feature or GCC extension
    3 |     unsigned mask = 0b1011;        /* C23 의 2진 리터럴 */
      |                     ^~~~~~
0b1011 = 11

===== gcc -std=c23 =====
gcc: error: unrecognized command-line option ‘-std=c23’; did you mean ‘-std=c2x’?
exit=1

===== gcc -std=c2x -Wall -Wextra -pedantic =====
(경고 0 건) exit=0
0b1011 = 11
```

**왜 그런가**

- ★★ **C23 문법이 `-std=c89` 에서 경고 0건으로 통과한다.** `-std=` 는 **강제가 아니라 기본값 선택**이다.\
  **표준 준수를 주장하려면 `-pedantic` 이 필요하다.** 그것을 켜면 `-std=c89`·`c99`·`c17` 전부 1건이 된다.
- ★★★ **마지막 두 줄이 이 문항의 핵심이다** — `-std=c23` 은 **경고 0건인데 `exit=1`** 이다.\
  **gcc 13.3.0 에 그 옵션이 없어 컴파일 자체가 실패한 것**이고, 경고만 세었다면 **「0건 통과」로 기록됐을 것**이다.
- **gcc 13 에서 C23 을 쓰려면 `-std=c2x`** 다(clang 18 은 `-std=c23` 을 받는다).
- ★ [09번 형제](../09-operator-precedence-and-associativity/)가 `-Wprecedence` 로 **같은 사고를 재현했다** — **경고를 셀 때는 종료 코드를 같이 본다.**

### 11. 다섯 층으로 갈라 보기 — 10번과 두께가 뒤집힌다 ★★

**답**

| 층 | 이 주제(11번) | [10번 형제](../10-evaluation-order-and-sequence-points/) |
|---|---|---|
| **표준** | `& \| ^ ~` 의 비트별 동작 · 마스크 관용구 · **피연산자 정수 승격** · `unsigned` 좌시프트의 모듈로 2^N · `unsigned` 우시프트가 0 을 채움 · 비트필드의 **값** | 시퀀스 포인트 일곱 자리 · 단락 평가 · 두 호출이 섞이지 않는 것 |
| **조건부 표준** | ★ **해당 없음** | ★ **해당 없음** |
| **구현 정의** | ★ **찬다** — `-1 >> 1`(산술 시프트) · `int x:4` 의 부호 · 비트필드 바이트 배치 · `int` 의 폭 | ★ **비어 있다** — 평가 순서에는 **문서화 의무가 없다** |
| **미명시** | ★ **해당 없음** — 비트 연산 자체에는 없다 | ★★ **본체** — 인자·부분식 평가 순서 |
| **UB** | ★★ **본체 셋** — 음수 시프트량 · 폭 이상 · 부호 비트를 넘기는 좌시프트 | 같은 객체를 한 식에서 두 번 건드리는 것 |

- **비어 있는 칸은** 「**조건부 표준**」과 「**미명시**」다. 조건부 보장이 걸릴 매크로가 없고,\
  **비트 연산은 「여러 가능성 중 하나」로 둘 자리가 없다** — 결과가 하나로 정해지거나(표준), 구현이 문서화하거나(구현 정의), 아예 뜻이 없거나(UB) 셋뿐이다.
- ★★ **10번과 비교하면 「미명시」와 「UB」의 두께가 통째로 뒤집힌다.** 10번에서 **비어 있던 구현 정의 칸**이 여기서는 차고,\
  10번의 **본체였던 미명시 칸**이 여기서는 빈다.
- **「도구가 원리상 못 보는 층」** — 11번은 **구현 정의**(`-1 >> 1`), 10번은 **미명시**(인자 순서).\
  ★ **둘 다 「UB 가 아니라서」 같은 이유로 침묵한다.** 층 이름만 다르다.

### 12. 그래서 어떻게 쓰나

**규칙 두 줄**

```text
   ★ 마스크는 unsigned, 시프트량은 검사한다.
     - 마스크는 언제나 1u << n      -> UB ③ (부호 비트 넘김) 이 사라진다
     - 시프트 전에 0 <= n < 폭 검사  -> UB ① ② 가 사라진다
```

**빌드·CI 플래그**

```text
개발·운영 빌드
  gcc   -std=c17 -O2 -Wall -Wextra -pedantic -Wshift-overflow=2 -Wconversion -Werror
  clang -std=c17 -O2 -Wall -Wextra -pedantic -Werror

CI 에 한 벌 더
  gcc -std=c17 -O1 -fsanitize=undefined                 (전수 관찰 — recover 허용)
  gcc -std=c17 -O1 -fsanitize=undefined -fno-sanitize-recover=all   (빌드를 깨기)
  ★ 두 실행은 목적이 다르다. 하나로 겸하면 첫 건 뒤가 안 보인다.

값을 단정하기 전에
  -O0 -O1 -O2 -O3 -Os 다섯 벌 + 컴파일러 두 대
  ★ 그리고 종료 코드를 같이 본다.
```

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 플래그 설정·해제 | `f \|= (1u<<n);` · `f &= ~(1u<<n);` | `1 << 31` 로 마스크 만들기 |
| 플래그 검사 | `if ((f & MASK) != 0)` | `if (f & MASK != 0)` |
| 2 로 나누기 | `v / 2` | `v >> 1`(음수에서 값이 다르다) |
| 0 을 채우고 싶다 | `(unsigned)v >> 1` | `v >> 1`(구현 정의) |
| 작은 타입 뒤집기 | `(unsigned char)~c` | `~c` 를 그대로 비교 |
| 외부 포맷 | `unsigned` + 시프트·마스크 | 비트필드 구조체를 바이트로 읽기 |

**형제 주제**

- **비트 트릭·응용 자체**(popcount·부분집합 순회·비트마스크 DP)의 정본은 [`algorithm/29-bit-manipulation/`](../../../../../algorithm/29-bit-manipulation/)다.\
  **여기는 「그 트릭이 어느 타입에서 깨지나」까지**다.
- **2진 표현·2의 보수**의 정본은 [`data-representation/`](../../../../data-representation/)다. 여기는 **C 연산자가 그 표현을 어떻게 다루나**다.
- **승격 규칙**은 [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/), **묶이는 순서**는 [09번 형제](../09-operator-precedence-and-associativity/), **UB 를 잡는 도구**는 목록의 **58번 주제**가 정본이다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 컴파일러·플래그로 돌렸나 |
|---|---|---|
| 마스크 넷 (11-a) | `\|`·`&~`·`^`·`&` 의 8비트 결과 · `~flags` 가 `0xFFFFFFF5` | gcc `-Wall -Wextra -pedantic` |
| 마스크 관용구 (11-b) | `perm` 이 `03`→`07`→`05`→`04` · `~F_WRITE` = `0xFFFFFFFD` · ★ `-Wconversion` 에서만 1건 | gcc 4벌 |
| 승격 (11-c) | `sizeof (~c)`=4 · `~c`=-256 · `c<<8`=65280 · **`-Wextra` 의 `-Wsign-compare` 1건**(`-Wall` 단독 0건) | gcc 5벌 |
| 시프트 UB 셋 (11-d) | UBSan 진단 **3줄**(각각 다른 문구) · `-fno-sanitize-recover=all` 은 **1줄 exit=1** · 경고 **0건** | gcc `-O0`\~`-Os` · gcc·clang UBSan 2벌 |
| `1<<31` (11-e) | 기본 경고 **0건**(gcc·clang) · `-Wshift-overflow=2` **1건** · UBSan **잡음** · `(int)(1u<<31)`=`INT_MIN` | gcc 3벌 · clang 1벌 |
| 우시프트 (11-f) | `-1>>1`=-1 · `-7>>1`=-4 ↔ `-7/2`=-3 · `0xFFFFFFFFu>>1`=`0x7FFFFFFF` · UBSan **0줄** | gcc `-O0`·`-O2` · clang `-O2` · UBSan |
| 〃 어셈블리 | `v >> 1` 이 **`sar`** — 산술 시프트임을 명령 이름으로 | gcc `-O2 -S -masm=intel` |
| 상수 대 변수 (11-g) | 상수 **3건**(플래그 0개에서도) ↔ 변수 **0건**(`-O2` 포함) · `-Wno-…` 로 소속 확인 | gcc 7벌 · clang 1벌 |
| 루프 UB (11-h) | 일곱 벌 중 **clang `-O2` 만 `1`**, 나머지 `254` · 경고 0건 · ★ UBSan **1줄**(UB 는 9회) | gcc 5벌 · clang 2벌 · UBSan |
| 비트필드 (11-i) | `sizeof`=4 · 필드 값 일치 · ★ **바이트가 gcc `D3 78 00 00` ↔ clang `D3 08 00 00`** · 절단 경고 2건 | gcc·clang `-Wall -Wextra` |
| `-std=` (11-j) | C23 리터럴이 **c89 에서 0건** · `-pedantic` 에서 1건 · ★ **`-std=c23` 은 0건 `exit=1`** | gcc 8벌 · clang 1벌 |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3)에서만** 그렇다.

- `CHAR_BIT=8` · `sizeof(int)=4` — 「폭 이상」이 **32부터**인 근거다([02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)).
- `-1 >> 1` 이 `-1` 인 것(**산술 시프트**) — ★ **구현 정의**다. 어셈블리 `sar` 가 이 구현의 선택을 보여 준다.
- `int d : 4` 가 **부호 있는 것**으로 잡힌 것 · 비트필드 바이트가 `D3 78 00 00`(gcc) / `D3 08 00 00`(clang)인 것.
- `(int)(1u << 31)` 이 `INT_MIN` 인 것 — **구현 정의 변환**이다.
- `v << -1` 이 `-2147483648`, `v << 32` 가 `1` 인 것 — ★ **UB 라서 값 자체가 근거가 못 된다.** x86 의 시프트량 마스킹이 보인 것뿐이다.
- `-Wshift-*` 계열이 **기본으로 켜져 있는 것** · `-Wsign-compare` 가 **`-Wextra`** 에 있는 것 — gcc 의 분류다.
- gcc 13.3.0 에 **`-std=c23` 이 없는 것**(`-std=c2x`).

**비트 연산자의 규칙 자체는 구현 의존이 아니다.** `& \| ^ ~` 의 비트별 동작과 **승격이 먼저 일어난다는 것**은 어느 C 구현에서도 같다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `-fsanitize=shift-base`/`shift-exponent` 로 쪼개 보기 · `-fsanitize=list` 로 검사 항목 전수 훑기 ·\
  회전 관용구 `(v<<n)|(v>>(32-n))` 의 `n==0` 함정 · `_BitInt(N)`(C23) 의 시프트 규칙 · `CHAR_BIT != 8` 인 구현.
- **못 잰 것** — **「UB 라서 오늘 이 값이 나왔다」의 원인.** 관찰된 `-2147483648`·`1`·`0` 은 하드웨어의 결과이고,\
  **컴파일러가 그 UB 를 어떻게 가정했는지**는 값으로 확인할 수 없다. 확인할 수 있는 것은\
  **「최적화 수준을 바꾸니 답이 달라졌다」**(6번)까지다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- `-Wshift-overflow` 의 **기본 레벨**이 바뀌어 `1 << 31` 을 잡기 시작했는지.
- `-Wsign-compare` 의 소속(`-Wextra`)과 **문구**(이 문서는 문구를 그대로 인용한다).
- gcc 가 **`-std=c23` 을 받기 시작했는지**(13.3.0 은 `-std=c2x` 뿐).
- clang `-O2` 의 `sum_bits(40)` 이 여전히 `1` 인지 — ★ **UB 라서 언제든 바뀐다.** 바뀌어도 결론은 그대로다.
- **`& \| ^ ~` 와 시프트의 UB 규칙 자체는 다시 돌릴 필요가 없다** — C89 이후 바뀐 적이 없다.
