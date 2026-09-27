# c/syntax/07 — `enum` 과 열거 상수: 이름이 붙은 정수일 뿐이다 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고·에러는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 플래그는 `-std=c17 -Wall -Wextra`. **표준 버전·`-pedantic`·`-fshort-enums` 가 갈리는 답은 그 자리에 밝혔다.**\
> `gdb`·`clang 18.1.3` 을 쓴 자리도 그 자리에 밝혔다.
> ★ **이 주제에는 UB 가 없다.** 그래서 sanitizer 출력이 한 줄도 안 나온다 — 그것도 결과다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 세 가지 타입을 물어본다 ★

**출력**

```text
--- 열거 상수 자체의 타입 ---
S_A            -> int
B_A (INT_MAX)  -> int
H_A (INT_MAX+1)-> unsigned int
N_A (-1)       -> int
--- 열거 타입 변수의 타입 ---
enum Small 변수 -> unsigned int
enum Huge  변수 -> unsigned int
enum Neg   변수 -> int
enum Tiny  변수 -> unsigned int
--- sizeof ---
sizeof(enum Small)=4 Neg=4 Big=4 Huge=4 Tiny=4  (int=4)
--- 값 ---
S_A=0 S_B=1 S_C=2  N_A=-1  B_A=2147483647
H_A=2147483648
```

**열거 상수 셋**

- `S_A` → **`int`** · `N_A`(-1) → **`int`** · `B_A`(INT_MAX) → **`int`**
- `H_A`(2147483648u) → **`unsigned int`** ★
- C17 의 규칙은 「열거 상수는 `int`」인데 `H_A` 는 `int` 에 안 들어간다.\
  그래서 **C17 에서는 제약 위반**이고 gcc 가 확장으로 받아 준 것이다(6번·10번).

**열거 타입 변수 셋**

- `enum Small`·`enum Tiny`·`enum Huge` 변수 → **`unsigned int`**
- `enum Neg` 변수 → **`int`** ★

**왜 다른가**

```text
   enum Color { RED, GREEN, BLUE };

   ① 열거 상수 RED      -> ★ int          표준이 정한다 (C17)
   ② 변수 c 의 타입      -> ★ unsigned int 구현이 고른다

   둘은 서로 다른 규칙을 따른다.
   "상수의 타입" 과 "열거 타입" 은 같은 것이 아니다.
```

- ① 은 **표준**이 정하고 ② 는 **구현**이 고른다. 두 층이 다르다.
- 그래서 `RED` 와 `(enum Color)RED` 가 **다른 타입**일 수 있다.

**넷을 가르는 것**

- **음수 열거자가 있느냐**다.

```text
   enum Small { 0, 1, 2 }      음수 없음 -> unsigned int
   enum Tiny  { 0, 255 }       음수 없음 -> unsigned int
   enum Huge  { 2147483648 }   음수 없음 -> unsigned int
   enum Neg   { -1, 0 }        ★ 음수 있음 -> int
```

- 표준은 「열거 타입은 `char` · 부호 있는 정수 타입 · 부호 없는 정수 타입 중 하나와 호환되고,\
  모든 열거자 값을 담을 수 있어야 한다」까지만 정한다. **어느 것인지는 구현 정의**다.
- gcc 는 **담을 수 있는 가장 좁은 규칙으로 `int`/`unsigned int`** 를 고른다.
- clang 18.1.3 도 같은 답이었다 — **그래서 더 위험하다.** 「둘이 같으니 보장이겠지」가 아니다.

### 2. `enum` 값에서 1을 빼면 ★★★

**출력**

```text
arith.c:11:44: warning: comparison of unsigned expression in ‘< 0’ is always false [-Wtype-limits]
   11 |     printf("r - 1 < 0 인가  : %d\n", r - 1 < 0);
      |                                            ^
변수 r 의 타입          -> unsigned int
식 r - 1 의 타입        -> unsigned int
상수 RED - 1 의 타입    -> int
r - 1 을 %d 로 : -1
r - 1 을 %u 로 : 4294967295
r - 1 < 0 인가  : 0
RED - 1 < 0 인가: 1
```

**네 줄**

- `%d` → **`-1`** · `%u` → **`4294967295`** · `r - 1 < 0` → **`0`(거짓)** · `RED - 1 < 0` → **`1`(참)**

**셋째와 넷째**

- **다르다.** 같은 모양의 식인데 답이 반대다.

```text
   RED - 1                         r - 1
   = int(0) - int(1)               = unsigned(0) - int(1)
   = int(-1)                       -> 통상 산술 변환: unsigned 가 이긴다
   -> -1 < 0 은 ★ 참                = unsigned(4294967295)
                                    -> 4294967295 < 0 은 ★ 거짓
```

- 갈린 것은 「**상수냐 변수냐**」다. 상수는 `int`, 변수는 `unsigned int`(1번).
- [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)의 `-1 < 1u` 와 **완전히 같은 사고**다.\
  거기서는 `unsigned` 리터럴이 원인이었고, 여기서는 **`enum` 이 조용히 `unsigned` 를 끌고 온다.**

**사실을 보여 주는 것**

- **`%u`** 다. `%d` 로 찍으면 `4294967295` 도 `-1` 로 보인다.
- ★ **화면에는 `-1` 이 찍히는데 비교는 거짓**이다. 출력만 보고 판단하면 절대 못 잡는다.

**잡는 경고**

```text
[] 0
[-Wall] 0
[-Wextra] 1
[-Wall -Wextra] 1
```

- **`-Wtype-limits`** 이고 **`-Wextra`** 에 있다. `-Wall` 은 0건이다.
- **clang 18.1.3 은 `-Wall -Wextra` 로 0건**이었다(값은 같게 냈다).\
  ★ **컴파일러를 바꾸면 안 보인다** — 「우리는 clang 으로 검사한다」가 여기서는 통하지 않는다.

**고치는 형태**

```c
if ((int)r - 1 < 0) { }        /* 먼저 int 로 올린다 */
```

- 또는 애초에 **`enum` 값에 산술을 하지 않는다.** 「이전 값」이 필요하면 `switch` 나 표를 쓴다.

### 3. `sizeof(enum E)` 를 값 범위를 바꿔 가며

**출력**

```text
sizeof(enum Small)=4 Neg=4 Big=4 Huge=4 Tiny=4  (int=4)
```

```text
sizeof(enum Small)=1 Neg=1 Big=4 Huge=4 Tiny=1  (int=4)
```

**다섯 값 · 범위에 따라 달라지나**

- 기본 빌드에서 **전부 4**다. `enum Tiny { 0, 255 }` 도 4다.
- ★ **값 범위를 바꿔도 안 달라진다.** 「작은 값만 쓰면 작아진다」는 **이 컴파일러에서 재현되지 않는다.**

**`-fshort-enums` 를 붙이면**

| `enum` | 값 범위 | 기본 | `-fshort-enums` |
|---|---|---|---|
| `Small` | 0\~2 | 4 | **1** |
| `Neg` | -1\~0 | 4 | **1** |
| `Big` | 2147483647 | 4 | 4 |
| `Huge` | 2147483648 | 4 | 4 |
| `Tiny` | 0\~255 | 4 | **1** |

- **범위에 맞춰 줄인다.** 같은 컴파일러가 **답을 둘 갖고 있다.**

**어느 층인가**

- **구현 정의**다. 문서화 의무가 있고, gcc 는 `-fshort-enums` 를 문서로 설명한다.
- ★ **플래그 하나로 뒤집어 보이는 것**이 「구현 정의」를 증명하는 가장 싼 방법이다.\
  ([05번 형제](../05-explicit-casts-and-pointer-conversions/)가 `-funsigned-char` 로 같은 일을 했다.)

**어디에 쓰면 안 되나**

- **파일 형식·네트워크 프로토콜·공유 라이브러리 경계.**
- `-fshort-enums` 는 **ABI 를 바꾼다.** 이 플래그로 빌드한 오브젝트와 아닌 오브젝트를 링크하면\
  구조체 레이아웃이 어긋나는데 **링커가 말해 주지 않는다.**
- 그런 자리에는 **고정폭 정수**(`uint8_t`·`int32_t`)를 쓴다([02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)).

### 4. 범위 밖 값을 넣으면

**출력**

```text
c = 999, d = -5
sizeof(c) = 4
c+1 = 1000
```

```text
[] 0
[-Wall] 0
[-Wextra] 0
[-Wall -Wextra] 0
[-Wall -Wextra -Wconversion] 0
[-Wall -Wextra -pedantic] 0
```

```text
-O0  : c = 999, d = -5 sizeof(c) = 4 c+1 = 1000 
-O2  : c = 999, d = -5 sizeof(c) = 4 c+1 = 1000 
ubsan: c = 999, d = -5 sizeof(c) = 4 c+1 = 1000 exit=0
```

**컴파일되나 · 무엇이 찍히나**

- **컴파일된다.** `999` 와 `-5` 가 그대로 들어가고 `c + 1` 은 `1000` 이다.

**플래그별 건수**

- ★ **여섯 조합 전부 0건**이다. `-pedantic` 도, `-Wconversion` 도 말하지 않는다.

**최적화·sanitizer**

- **세 빌드가 전부 같은 값**이고 `exit=0` 이다.
- ★ **UB 가 아니다.** 열거 타입은 호환되는 정수 타입(여기선 `unsigned int`)의 범위를 갖고,\
  `999` 는 그 안이다. **그래서 sanitizer 가 볼 것이 없다.**
- 다만 `d = (enum Color)-5` 는 `unsigned` 에 담겨 `4294967291` 이 되고, `(int)` 로 다시 읽어 `-5` 로 보인다 —\
  2번과 같은 함정이다.

**잡아 주는 도구**

```text
range.c:4:20: warning: integer constant not in range of enumerated type 'enum Color' [-Wassign-enum]
    4 |     enum Color c = 999;                      /* ★ 범위 밖 */
      |                    ^
```

- **clang 의 `-Wassign-enum`** 이다.
- 단 **`-Wall -Wextra` 로는 clang 도 0건**이고, 플래그를 **명시**해야 나온다.
- 그리고 **gcc 에는 그 플래그가 아예 없다.**

```text
gcc: error: unrecognized command-line option ‘-Wassign-enum’
```

- ★ **처음에 이 플래그를 gcc 에 그냥 붙여서 「0건」이라는 결과를 얻었는데, 그건 컴파일이 실패한 것이었다.**\
  「경고 0건」과 「컴파일 실패」가 `grep -c warning` 으로는 **똑같이 0으로 보인다.**\
  **플래그를 세기 전에 컴파일이 성공했는지부터 봐야 한다.**

### 5. `switch` 에서 열거자를 빠뜨리면

**출력**

```text
sw.c:4:5: warning: enumeration value ‘BLUE’ not handled in switch [-Wswitch]
red green ?
```

```text
[] 0
[-Wall] 1
[-Wextra] 0
[-Wall -Wextra] 1
[-Wswitch] 1
[-Wall -Wswitch-enum] 1
```

**어떤 진단 · 어느 플래그**

- **`-Wswitch`** 이고 **`-Wall`** 에 있다. `-Wextra` 만으로는 0건이다.
- ★ 2번의 `-Wtype-limits` 는 `-Wextra` 였다. **같은 주제 안에서도 소속이 갈린다** — 세어 보는 수밖에 없다.

**`default:` 를 넣으면**

```text
[-Wall] 0
[-Wall -Wswitch-enum] 1
```

- **`-Wswitch` 가 침묵한다.** 「나머지는 `default` 가 받는다」로 읽기 때문이다.

**말하게 하려면**

```text
sw2.c:4:5: warning: enumeration value ‘BLUE’ not handled in switch [-Wswitch-enum]
```

- **`-Wswitch-enum`** 을 켠다. `default:` 가 있어도 열거자를 전부 적으라고 요구한다.

**「`enum` 을 왜 쓰나」에의 답**

```text
   enum 이 주는 것 셋

   ① switch 경고   <- ★ 열거자를 늘렸을 때 고칠 자리를 찾아 준다
   ② 디버거 표시    <- 값이 이름으로 보인다 (9번)
   ③ 정수 상수식    <- 배열 크기·case·비트필드 폭

   ①이 가장 크고, default: 가 그것을 끈다.
```

- 「닫힌 집합」을 다루는 값어치가 거의 전부 ①에 있다.
- **`default:` 를 습관적으로 넣으면 `enum` 을 쓰는 이유의 절반이 사라진다.**

### 6. C23 의 고정 기반 타입 ★★

**출력** (`-std=c2x`)

```text
__STDC_VERSION__ = 202000L
sizeof(enum Byte) = 1
변수의 타입   -> unsigned char
상수 B_MAX 의 타입 -> unsigned char
B_MAX = 255
```

**세 줄**

- `__STDC_VERSION__` = **`202000L`** · `sizeof(enum Byte)` = **1** · 변수의 타입 = **`unsigned char`**

**`B_MAX` 의 타입**

- **`unsigned char`** 다. **`int` 가 아니다.**
- ★ **C23 의 고정 기반 타입은 열거 「상수」의 타입까지 바꾼다.** 1번의 「상수는 `int`」가 여기서 무너진다.
- 그래서 `B_MAX - 1` 같은 식의 승격 경로도 달라진다(`unsigned char` → `int` 로 승격).

**`-std=c17` 로 컴파일하면**

```text
__STDC_VERSION__ = 201710L
sizeof(enum Byte) = 1
변수의 타입   -> unsigned char
상수 B_MAX 의 타입 -> unsigned char
B_MAX = 255
```

- ★★ **에러가 안 난다. 그냥 컴파일되고 똑같이 돈다.**
- `-Wall -Wextra` 로도 **0건**이다.

**`-std=c17 -pedantic`**

```text
fixed.c:2:6: warning: ISO C does not support specifying ‘enum’ underlying types before C2X [-Wpedantic]
    2 | enum Byte : unsigned char { B_ZERO = 0, B_MAX = 255 };
      |      ^~~~
```

- `-std=c89 -pedantic` 에서도 **같은 문구**가 나온다.
- ★ **`-std=` 는 「이 표준으로 해석해라」이지 「이 표준 밖을 막아라」가 아니다.**\
  gcc 는 확장을 기본으로 켜 두고, **`-pedantic` 이 그것을 보고**한다.

**`-std=c23` 이 있나**

```text
gcc: error: unrecognized command-line option ‘-std=c23’; did you mean ‘-std=c2x’?
```

- **없다.** gcc 13 은 **`-std=c2x`** 뿐이고, 그때 `__STDC_VERSION__` 이 `202000L` 이다\
  (정식 C23 값인 `202311L` 이 아니다 — **아직 초안 단계의 값**이라는 뜻이다).

### 7. 값 지정·이어붙기·중복

**출력**

```text
A=0 B=10 C=11 D=10 E_=-1 F=0
B == D ? 1
```

```text
[-Wall -Wextra] 0
[-Wall -Wextra -pedantic] 0
```

**여섯 값**

- `A=0` · `B=10` · `C=11` · `D=10` · `E_=-1` · `F=0`

**규칙 한 줄**

```text
   값을 안 쓰면 ★ 직전 열거자의 값 + 1 이다. (순서 번호가 아니다)

   A            -> 0        (첫 번째는 0)
   B = 10       -> 10
   C            -> 10 + 1 = 11
   D = 10       -> 10
   E_ = -1      -> -1
   F            -> -1 + 1 = 0     ★ 앞으로 되감겼다
```

- **첫 열거자는 0, 그 뒤는 직전 값 + 1.**
- 그래서 중간에 음수를 넣으면 **그 뒤가 앞으로 되감긴다** — `F` 가 `A` 와 같은 0이 됐다.

**중복**

- **`B == D` 는 `1`** 이다. 중복이 **허용**된다.
- `A` 와 `F` 도 둘 다 0이다.
- 이것이 비트 플래그에서 조합값을 열거자로 넣는 관용구를 가능하게 한다(8번).

**경고 건수**

- **0건**이다. `-pedantic` 까지 켜도 0건.
- ★ **중복을 검사하는 도구가 없다.** `switch` 에서 같은 `case` 값이 두 번 나오면 그때 에러가 나지만,\
  선언만으로는 아무도 말해 주지 않는다.

### 8. 비트 플래그로 쓰면

**출력**

```text
P_READ | P_WRITE 의 타입 -> int
enum Perm 변수의 타입     -> unsigned int
both = 3, 이름은 없다
show(both) = 다른 것
P_READ|P_WRITE 가 열거 상수 중 하나인가? 0
```

```text
[-Wall -Wextra] 0
[-Wall -Wextra -Wconversion] 0
```

**`|` 의 타입**

- **`int`** 다. 피연산자가 둘 다 열거 상수(=`int`)이므로 결과도 `int`.
- **열거 타입이 아니다.** 변수끼리 `|` 해도 `unsigned int` 로 승격되어 역시 열거 타입이 아니다.

**경고**

- **0건**이다. gcc 는 `int` 를 열거 타입 변수에 넣는 것을 막지 않는다.
- clang 은 `-Wassign-enum` 을 명시하면 말한다.

```text
flags.c:11:29: warning: integer constant not in range of enumerated type 'enum Perm' [-Wassign-enum]
```

**`case` 로 받을 수 있나**

```text
   enum Perm { P_READ = 1, P_WRITE = 2, P_EXEC = 4 };

   P_READ | P_WRITE  =  3
                        ^
                     ★ 3 이라는 열거자가 없다

   switch (perm) {
   case P_READ:  ...   /* 1 */
   case P_WRITE: ...   /* 2 */
   case P_EXEC:  ...   /* 4 */
   }                    -> 3 은 어디에도 안 걸린다
```

- **못 받는다.** `3` 이라는 이름이 없어서 `case` 라벨을 쓸 수가 없다.
- 디버거도 이름을 못 붙이고, `-Wswitch` 도 도움이 안 된다(빠진 열거자가 없으니 침묵한다).
- 실측에서 `show(both)` 가 `다른 것` 을 돌려줬다.

**두 관례**

1. **조합값도 열거자로 적는다** — `P_RW = P_READ | P_WRITE` 처럼.\
   `switch` 와 디버거가 살아난다. 대신 조합이 늘면 열거자가 폭발한다.
2. **변수 타입은 `unsigned` 로 두고 값만 `enum` 으로 만든다** — `unsigned flags = P_READ | P_WRITE;`\
   「이건 열거 타입이 아니다」를 타입으로 정직하게 말하는 쪽이다. **이쪽이 관례로 더 흔하다.**

### 9. 익명 `enum` 과 `#define`

**출력**

```text
sizeof a=256 b=256
BUFSZ 의 타입 -> int
sizeof(BUFSZ)=4
```

```text
N=4 sizeof arr=16 비트필드 폭 4
```

```text
Breakpoint 1, main () at dbg.c:7
7	    printf("%d %d\n", (int)c, d);
$1 = GREEN
$2 = 0
$3 = RED
No symbol "DRED" in current context.
```

**둘 다 되나**

- **둘 다 된다.** 배열 크기(`sizeof a == sizeof b == 256`)·`case` 라벨·비트필드 폭·`_Static_assert` 전부.
- 열거 상수는 **정수 상수식**이기 때문이다.

**`gdb` 로 물어보면**

| 물어본 것 | 답 |
|---|---|
| `print c` (`enum Color` 변수) | **`GREEN`** — 값이 아니라 **이름** |
| `print d` (`int` 변수) | `0` |
| `print RED` (열거 상수) | **`RED`** |
| `print DRED` (`#define`) | **`No symbol "DRED" in current context.`** |

```text
   enum                          #define
   +----------------------+     +----------------------+
   | 컴파일러가 안다       |     | 전처리기가 ★ 지운다   |
   | 디버그 정보에 남는다   |     | 컴파일러가 못 본다    |
   | print RED -> RED     |     | print DRED -> 없음   |
   +----------------------+     +----------------------+
```

- ★ **디버거에서 이름이 보이는 것**이 `enum` 의 두 번째 이득이다.
- `print c` 가 `GREEN` 이라고 답하는 것은 **`enum Color` 라는 타입 정보가 디버그 정보에 있기 때문**이다.

**스코프**

- **열거 상수는 블록 스코프**를 따른다. 함수 안에서 선언하면 그 함수 안에서만 보인다.
- **`#define` 은 파일 끝까지**(또는 `#undef` 까지) 간다. 스코프라는 개념이 없다.
- 그래서 `#define` 은 다른 헤더의 이름과 충돌한다 — 대문자 관례가 생긴 이유다.

**`#define` 만 되는 자리**

- **`#if` 조건식**이다. 전처리기는 `enum` 을 모른다 — `#if BUFSZ > 100` 에서 `BUFSZ` 는 0으로 읽힌다.
- 이 문서에서는 **던져 보지 않았다.**

### 10. C17 과 C23 이 무엇이 다른가

**C23 이 바꾼 것 둘**

```text
   ① 열거자 값이 int 범위를 넘어도 된다
      enum Huge { H_A = 2147483648u };
      C17: 제약 위반 (gcc 는 확장으로 받아 준다)
      C23: 적법

   ② 고정 기반 타입 (fixed underlying type)
      enum Byte : unsigned char { ... };
      크기·부호·★ 상수의 타입까지 내가 정한다
```

**gcc 가 문구로 말해 주는 자리**

```text
huge.c:1:19: warning: ISO C restricts enumerator values to range of ‘int’ before C2X [-Wpedantic]
```

```text
fixed.c:2:6: warning: ISO C does not support specifying ‘enum’ underlying types before C2X [-Wpedantic]
```

- ★ **두 문구 모두 「before C2X」라고 직접 말한다.** 기억으로 적을 필요가 없다 — **컴파일러에게 물어본 것**이다.
- `-std=c2x` 로 바꾸면 둘 다 **0건**이 된다.

**`-std=c17` 이 막아 주나**

- **안 막는다.** 두 기능 모두 `-std=c17` 에서 경고 없이 컴파일되고 똑같이 돈다.
- `-std=c89` 로 내려도 마찬가지다.

**이식성을 확인하려면**

```text
gcc -std=c17 -pedantic          -> 경고로 알려 준다
gcc -std=c17 -pedantic-errors   -> 에러로 막는다
```

- **`-pedantic`** 을 붙인다. 정말 막고 싶으면 **`-pedantic-errors`** 다.
- ★ 이것은 `enum` 만의 이야기가 아니다 — [06번 형제](../06-typedef-and-type-aliases/)의 `typedef` 재정의도 같았고,\
  [08번 형제](../08-sizeof-alignment-and-offsetof/)의 빈 구조체도 같다. **gcc 에서 「표준 준수」는 `-pedantic` 의 몫이다.**

### 11. 그래서 언제 쓰나

**값어치 둘**

1. **`switch` 경고** — 열거자를 늘렸을 때 고칠 자리를 컴파일러가 찾아 준다(`-Wswitch`, `-Wall`).
2. **디버거 표시** — 값이 이름으로 보인다(`print c` → `GREEN`).

- 여기에 **정수 상수식**(배열 크기·`case`·비트필드 폭)이 덤으로 붙는데, 그건 `#define` 도 된다.

**안 쓸 거면 무엇이 다른가**

- **거의 없다.** 타입 안전도 없고(4번), 크기 보장도 없고(3번), 부호도 구현 정의다(1번).
- `default:` 를 넣고 디버거를 안 쓰면 **이름이 붙은 `#define` 묶음**과 실질적으로 같다.

**크기·부호가 중요한 자리**

| 자리 | 쓸 것 |
|---|---|
| 파일 형식·네트워크 | `uint8_t`·`int32_t` 같은 **고정폭 정수** |
| 구조체 멤버로 1바이트여야 함 | C23 `enum E : uint8_t`, 또는 고정폭 정수 + `enum` 상수 |
| 공유 라이브러리 경계 | 고정폭 정수(`-fshort-enums` 가 ABI 를 바꾼다) |
| 내부 로직의 닫힌 상태 | **`enum`**(`default:` 없이) |

**빌드 플래그 한 줄**

```text
개발·운영 빌드
  gcc -std=c17 -O2 -Wall -Wextra -Wswitch-enum -Werror
  (-Wall 이 -Wswitch 를, -Wextra 가 -Wtype-limits 를 준다 —
   ★ 둘 다 켜야 이 주제의 두 함정이 덮인다)

이식성 확인
  gcc -std=c17 -pedantic-errors      (C23 문법이 새 들어오는 것을 막는다)

교차 확인
  clang -Wassign-enum                (gcc 에는 이 검사가 없다)

ABI 확인
  ★ -fshort-enums 를 한쪽에만 쓰지 않는다 (링커가 안 잡아 준다)
```

- **sanitizer 는 목록에 없다.** 이 주제에는 UB 가 없어서 런타임 도구가 할 일이 없다.\
  ★ **검사가 전부 컴파일 타임에 있고, 그래서 「플래그를 세는 것」이 이 주제의 유일한 검증 방법**이다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 플래그로 돌렸나 |
|---|---|---|
| 타입 3종 | 열거 상수 `int`(단 `H_A` 는 `unsigned`) · 열거 타입 변수 `unsigned int`(음수 있으면 `int`) · `sizeof` 5벌 전부 4 | `-std=c17`·`-std=c2x` × `-Wall -Wextra` |
| `enum` 산술 | `r-1` 이 `unsigned`, `RED-1` 이 `int` · `%d` 는 `-1`, `%u` 는 `4294967295` · `r-1<0` 거짓 / `RED-1<0` 참 | `-Wall -Wextra` · 플래그 4벌로 세기 · clang |
| `-fshort-enums` | `Small`·`Neg`·`Tiny` 가 **4 → 1** · `Big`·`Huge` 는 4 유지 | 기본 / `-fshort-enums` |
| 범위 밖 대입 | `c=999`·`d=-5` 통과 · **6개 플래그 조합 전부 0건** · `-O0`·`-O2`·ubsan 동일, `exit=0` | 플래그 6벌 · `-O0`·`-O2`·ubsan |
| 〃 clang | `-Wassign-enum` 으로 1건 · `-Wall -Wextra` 로는 0건 · **gcc 에는 플래그 자체가 없음** | clang 3벌 · gcc |
| 값 규칙 | `A=0 B=10 C=11 D=10 E_=-1 F=0` · `B==D` 참 · `-pedantic` 까지 **0건** | `-Wall -Wextra` ± `-pedantic` |
| `switch` | `-Wswitch` 가 **`-Wall`** 에 있음(6벌로 세기) · `default:` 가 침묵시킴 · `-Wswitch-enum` 은 말함 | 플래그 6벌 × 2소스 |
| C23 열거자 범위 | `-std=c17 -pedantic` **1건**(「before C2X」) · `-std=c2x -pedantic` **0건** | 5벌 × 2표준 |
| C23 고정 기반 타입 | `-std=c2x`: `sizeof`=1, **상수도 `unsigned char`** · **`-std=c17` 도 그냥 컴파일됨** · `-pedantic` 이 「before C2X」 · `-std=c23` 은 **없는 옵션** | `c17`·`c2x`·`c89` × `-pedantic` |
| 비트 플래그 | `\|` 결과가 `int` · 변수는 `unsigned int` · `both=3` 은 어떤 열거자도 아님 · gcc 0건 / clang 1건 | `-Wall -Wextra` ± `-Wconversion` · clang |
| 익명 `enum` | 배열 크기 256 · 타입 `int` · `case`·비트필드 폭·`_Static_assert` 전부 통과 | `-Wall -Wextra` |
| `gdb` | `print c` → **`GREEN`** · `print RED` → `RED` · `print DRED` → **`No symbol`** | `-g -O0` + `gdb -batch` |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0)에서만** 그렇다.

- 열거 타입이 **`unsigned int`/`int`** 로 정해지는 규칙 — **구현 정의**다(clang 도 같았지만 **보장이 아니다**).
- `sizeof(enum E)` 가 전부 **4** 인 것 — `-fshort-enums` 로 1이 되는 것이 그 증거다.
- `int` 범위 밖 열거자를 **C17 에서도 받아 주는 것** — gcc 의 확장이다.
- C23 문법이 **`-std=c17` 에서도 되는 것** — gcc 의 확장 노출 정책이다.
- `__STDC_VERSION__` 이 `-std=c2x` 에서 **`202000L`** 인 것 — 초안 단계의 값이다.
- `-Wswitch` 가 `-Wall` 에, `-Wtype-limits` 가 `-Wextra` 에 있는 것 — gcc 의 분류다.
- `-Wassign-enum` 이 **gcc 에 없는 것** — clang 과 다르다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — 불완전 열거 타입(`enum Color;`) · C23 에서 `bool`·`char` 를 기반 타입으로 주기 ·\
  `#if` 에서 열거 상수가 0으로 읽히는 것 · `-fshort-enums` 를 **한쪽에만** 쓴 링크 · X-매크로로 이름 배열 만들기.
- **못 잰 것** — `-fshort-enums` 가 **기본인 ABI**(일부 ARM)의 동작. 이 머신은 x86-64 하나뿐이다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- `-std=c23` 이 생겼는지, 그때 `__STDC_VERSION__` 이 `202311L` 인지.
- `-std=c17` 에서 C23 문법이 여전히 통과하는지.
- gcc 에 `-Wassign-enum` 에 해당하는 검사가 생겼는지.
- 열거 타입의 호환 타입 선택 규칙(구현 정의 — **보장이 아니다**).
