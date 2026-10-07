# architecture/01-number-systems-twos-complement — 진수·2의 보수·부호/무부호: 같은 비트, 두 해석 — 정리 (힌트)

## 해결하는 문제

컴퓨터 메모리에는 비트만 있다. "−4"라는 표시도, "부호 없음"이라는 표시도 저장되지 않는다.\
같은 비트 묶음을 **어떤 규칙으로 읽느냐**가 값을 정한다.

쉬운 예: 세 자리 자동차 주행거리계.

```text
  000 에서 한 칸 뒤로 돌리면 → 999
  "999 는 −1 로 읽자"고 약속하면 → 덧셈만으로 뺄셈이 된다
     005 + 999 = 1004 → 세 자리만 남기면 004   (5 + (−1) = 4)
```

- 자리 수가 정해진 계기판은 넘친 자리를 버린다. 그래서 "뒤로 한 칸"과 "앞으로 999칸"이 같은 결과가 된다.

똑같은 구조다.\
32비트 정수의 `0xFFFFFFFF`는 "부호 없는 4,294,967,295"로도, "부호 있는 −1"로도 읽힌다. 비트는 하나, 해석은 둘이다.

실무 예:
- C에서 `if (-1 > 0u)`가 참이 되어 경계 검사가 뚫린다.
- 네트워크에서 받은 길이 바이트 `0xC8`(200)을 Java `byte`로 읽으면 −56이 된다. 배열 크기가 음수라 예외가 난다.
- 같은 문자열의 해시를 Java와 C에서 따로 계산했더니 값이 다르다. 한쪽은 바이트를 부호 있게, 한쪽은 부호 없게 읽었다.
- 프로그램이 `return -1`로 끝났는데 셸의 `$?`는 255다.

## 동작·원리

### 1. 진수 — 같은 수, 다른 표기

```text
  10진  45
   2진  0010 1101          ← 4비트씩 끊는다
  16진     2    D   = 0x2D  ← 4비트 한 묶음 = 16진 한 자리
```

- 16진 한 자리가 정확히 4비트라서, 2진을 4자리씩 끊으면 바로 16진이 된다. 메모리 덤프·주소를 16진으로 쓰는 이유다.
  - *니블(nibble)*: 4비트 묶음. 16진 한 자리.
- 진수 변환 기초와 Python `bin`·`hex` 예는 원고 [foundations/data-representation](../../foundations/data-representation/README.md) §1에 있다. 여기서는 되풀이하지 않는다.
- CS:APP 3판 2.1.1 "Hexadecimal Notation".

### 2. 무부호와 2의 보수 — 4비트 원으로 본다

```text
  비트    무부호   2의 보수          4비트 수직선을 원으로 말면
  0000      0        0               0111(7) 다음 칸이 1000(−8)
  0001      1        1               1111(−1) 다음 칸이 0000(0)
  0010      2        2
  0011      3        3                  0000
  0100      4        4              1111    0001
  0101      5        5            1110        0010
  0110      6        6           1101   원     0011
  0111      7        7            1100        0100
  1000      8       −8              1011    0101
  1001      9       −7                1010 0110
  1010     10       −6                 1001 0111
  1011     11       −5                   1000
  1100     12       −4
  1101     13       −3
  1110     14       −2           같은 비트 = 같은 칸
  1111     15       −1           두 해석의 차이 = 16 (= 2⁴)
```

- *무부호(unsigned) 해석*: 비트 i의 무게가 2ⁱ다. 4비트면 0~15.
- *2의 보수(two's complement) 해석*: 맨 위 비트의 무게만 **−2ʷ⁻¹**이다. 나머지는 그대로 2ⁱ다.
  - 4비트 `1100` = −8 + 4 = −4. 무부호로는 8 + 4 = 12.
  - CS:APP 2.2.2 "Unsigned Encodings", 2.2.3 "Two's-Complement Encodings" 절이 이 두 해석을 다룬다(절 제목은 목차로 확인, 본문의 식 표기는 원문 미확인).
- 맨 위 비트가 1인 패턴에서만 두 해석의 차이가 2ʷ이다(0이면 두 값이 같다). 음수 x의 무부호 해석은 x + 2ʷ다. 4비트에서 −4 ↔ 12(= −4 + 16), 32비트에서 −1 ↔ 4,294,967,295.
- *부호 비트*: 맨 위 비트. 1이면 2의 보수로 읽은 값이 음수다.
  - 흔한 오해: "부호 비트를 뒤집으면 부호가 바뀐다." 그것은 부호-크기 방식이다. 2의 보수에서 `0100`(4)의 맨 위 비트를 켜면 `1100` = −4가 맞지만, `0011`(3)은 `1011` = −5가 된다.

음수를 만드는 법:

```text
   4  = 0100
  ~4  = 1011     비트를 모두 뒤집는다
  +1  = 1100     1을 더한다  → −4
```

- 원 위에서 −x는 0을 기준으로 x의 반대편 칸이다. "16 − 4 = 12 칸"이 곧 `1100`이다.
- 비대칭: 음수가 하나 더 많다. 4비트 범위는 −8~7, Java `int`는 −2,147,483,648~2,147,483,647(JLS §4.2.1).
  - −(−8)은 4비트에 없다. 뒤집고 1을 더하면 다시 `1000` = −8이다. Java의 `-Integer.MIN_VALUE`, `Math.abs(Integer.MIN_VALUE)`가 음수인 이유다(아래 실험, [math/11](../../math/11-modular-arithmetic/2-summary.md) 6절).

### 3. 왜 2의 보수인가 — 덧셈기 하나로 두 해석을 다 처리한다

```text
     1111        무부호: 15        2의 보수: −1
   + 0001                + 1                 + 1
   ------
   1 0000        넘친 1은 버림 → 0000
                 무부호: 0 (자리올림 발생)    2의 보수: 0 (정답)
```

- 4비트 덧셈기는 결과의 하위 4비트만 남긴다. 그 결과가 무부호로도, 2의 보수로도 "2⁴로 나눈 나머지" 의미에서 맞다.
- 그래서 x86-64 같은 CPU는 부호 있는 덧셈과 부호 없는 덧셈에 **같은 명령**을 쓴다. 다른 것은 "넘쳤는지"를 알려 주는 플래그뿐이다.
  - 넘침 처리는 ISA마다 다르다. MIPS32는 넘치면 예외를 내는 `ADD`와 같은 덧셈을 하되 예외를 내지 않는 `ADDU`를 따로 둔다(MIPS32 Architecture for Programmers Vol. II, ADD 항목). 결과 하위 비트는 둘이 같다.
  - x86-64(gcc 13.3 `-O2`)에서 `__builtin_add_overflow`를 부호 있는 `int`와 `unsigned`로 각각 쓰면 둘 다 `add` 명령 하나다. 넘침 판정만 `seto`(부호 있는 넘침, OF)와 `setb`(자리올림, CF)로 갈린다. 자세한 것은 [02-integer-overflow-and-truncation](../02-integer-overflow-and-truncation/2-summary.md) 실험.
- 원고 §1(48행)의 "+ 연산이 효율이 좋기 때문에, 두 수를 합칠 때 맨 앞의 1은 버릴 수 있도록" 설명이 이 그림이다.

다른 표현과 비교:

| 방식 | 4비트 −3 | 0의 개수 | 덧셈기 |
|---|---|---|---|
| 부호-크기 | `1011` | 2개(`0000`, `1000`) | 부호를 보고 더할지 뺄지 갈라야 한다 |
| 1의 보수 | `1100` | 2개(`0000`, `1111`) | 끝자리올림을 다시 더해야 한다 |
| 2의 보수 | `1101` | 1개 | 그냥 더하고 넘친 자리를 버린다 |

- 표준이 어떻게 정했나
  - Java: `byte`·`short`·`int`·`long`은 2의 보수 정수다(JLS SE21 §4.2 "signed two's-complement integers").
  - C11: 세 방식을 모두 허용했다(N1570 §6.2.6.2 — sign and magnitude, two's complement, ones' complement).
  - C23: 2의 보수만 남겼다(WG14 N2412 "Two's complement sign representation for C2x", 2019). 다만 **부호 있는 넘침은 여전히 미정의 동작**이다. N2412는 "넘침을 모듈로로 정의하는 것은 합의를 못 했다"고 적는다.

### 4. 부호/무부호 변환 — 비트는 그대로, 해석만 바뀐다

```text
  int  −1  = 1111 1111 1111 1111 1111 1111 1111 1111
                     │ (unsigned) 캐스트: 비트 복사, 명령 없음
  unsigned = 4,294,967,295                  = −1 + 2³²
```

- 2의 보수 기계에서 같은 폭의 부호/무부호 변환은 비트를 바꾸지 않는다(CS:APP 2.2.4 "Conversions between Signed and Unsigned").
- C 표준의 말로는 "새 타입이 무부호면 최댓값 + 1을 더하거나 빼서 범위에 넣는다"(N1570 §6.3.1.3 ¶2). 2의 보수 기계에서는 이 결과가 "비트 그대로"와 같다.
- 거꾸로 무부호 → 부호 있는 타입으로 범위 밖 값을 넣으면 C11에서는 **구현 정의**다(같은 절 ¶3). gcc는 "폭 N인 타입이면 2^N 모듈로 줄이고 시그널은 없다"고 문서화했다(GCC 매뉴얼 "Integers implementation").

### 5. C의 섞인 비교 — `-1 > 0u`가 참이 되는 길

```text
   int −1   ─┐
             ├─ 통상 산술 변환: 같은 폭이면 무부호 쪽으로
   unsigned 0u ┘
   → 4294967295 > 0  → 참(1)
```

- C는 `int`와 `unsigned`를 비교할 때 `int`를 `unsigned`로 바꾼 뒤 비교한다(N1570 §6.3.1.8 "Usual arithmetic conversions", CS:APP 2.2.5 "Signed versus Unsigned in C").
- `size_t`(x86-64 Linux에서 무부호 64비트)와 `int`의 비교도 같은 함정이다. `strlen(s) > -1`은 `-1`이 `SIZE_MAX`가 되어 거짓이다(아래 실험).
- 승격·변환 규칙 전체와 경고 옵션 전수 표는 [languages/c/syntax/03](../../../languages/c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/2-summary.md)에 있다. 여기서는 "비트는 그대로, 비교 명령만 무부호로 바뀐다"까지만 본다.
- Java에는 무부호 정수 타입이 없다. `char`만 16비트 무부호다(JLS §4.2.1). 대신 `Integer.compareUnsigned`·`toUnsignedString`·`Byte.toUnsignedInt`가 "같은 비트를 무부호로 읽는" 메서드다.

### 6. 넓히기 — 부호 확장과 0 확장

```text
  8비트 1100 1000 (0xC8)

  부호 확장 (signed char → int)        0 확장 (unsigned char → int)
  1111 1111 ... 1111 1100 1000         0000 0000 ... 0000 1100 1000
  └─ 맨 위 비트(1)를 복사 ─┘             └──── 0으로 채움 ────┘
  = −56                                 = 200
```

- *부호 확장(sign extension)*: 폭을 늘릴 때 새 상위 비트를 원래 부호 비트로 채운다. 2의 보수 값이 보존된다(CS:APP 2.2.6 "Expanding the Bit Representation of a Number").
- *0 확장(zero extension)*: 새 상위 비트를 0으로 채운다. 무부호 값이 보존된다.
- 기계어에서도 명령이 다르다. x86-64(gcc 13.3 `-O2`)에서 `signed char`를 `int`로 돌려주는 함수는 `movsbl`(move sign-extend byte to long), `unsigned char`는 `movzbl`(zero-extend)이다(아래 실험).
- Java `byte`는 부호 있는 타입이다. `int`로 넓히면 부호 확장된다. 프로토콜 바이트를 0~255로 읽으려면 `b & 0xFF` 또는 `Byte.toUnsignedInt(b)`.
- *좁히기(truncation)*: 폭을 줄이면 상위 비트를 버린다. 값이 바뀔 수 있다 → [02-integer-overflow-and-truncation](../02-integer-overflow-and-truncation/2-summary.md).

### 7. 오른쪽 시프트도 두 가지다

```text
  −16 = 1111 ... 1111 0000
  >> 2  (산술)   1111 ... 1111 1100 = −4        맨 위 비트를 복사해 채움
  >>> 28 (논리)  0000 ... 0000 1111 = 15        0으로 채움
```

- Java는 `>>`(산술)와 `>>>`(논리)를 따로 둔다(JLS §15.19). C는 무부호 타입이면 논리, 부호 있는 음수의 `>>`는 **구현 정의**다(N1570 §6.5.7). gcc는 부호 확장(산술 시프트)으로 정했다(GCC 매뉴얼 "Integers implementation").
- 시프트·마스크 기법은 [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md)에 있다.

### 실험: 같은 비트의 두 해석, 섞인 비교, 확장 명령

- 환경: i7-13700HX, Linux 7.0.0-34, gcc 13.3.0(호스트) / OpenJDK 21.0.12+8-LTS(`eclipse-temurin:21-jdk`, Docker `--cpus=2 --network none`), 2026-10-07. 출력은 결정적이다(2회 실행 같은 출력).
- C 코드 핵심(`signcmp.c`):

```c
int m1 = -1; unsigned z = 0u;
printf("-1 > 0u -> %d\n", m1 > z);
printf("strlen(s) > want (size_t vs int) -> %d\n", strlen(s) > want);   /* want = -1 */
int widen_s(signed char c)        { return c; }   /* 부호 확장 */
unsigned widen_u(unsigned char c) { return c; }   /* 0 확장 */
```

- `gcc -O0 -Wall -Wextra signcmp.c` 출력:

```text
warning: comparison of integer expressions of different signedness: 'int' and 'unsigned int' [-Wsign-compare]
warning: comparison of integer expressions of different signedness: 'size_t' {aka 'long unsigned int'} and 'int' [-Wsign-compare]
bits of -4 (int8)      11111100  (0xFC)
as signed  int8 : -4
as unsigned int8: 252
-1 > 0u           -> 1
(unsigned)-1      -> 4294967295
-1 > 0 (both int) -> 0
strlen(s) > want (size_t vs int) -> 0
signed char 0xFF -> int   -1 (0xFFFFFFFF)
unsigned char 0xFF -> int 255 (0x000000FF)
INT8 range -128..127, -(-128) as int8 = -128
```

- 관찰 1: `-Wall`만 켜면 경고가 0개였다. `-Wextra`를 더해야 `-Wsign-compare` 경고 2개가 나왔다(같은 파일, gcc 13.3 C 모드).
- 관찰 2: `strlen("abc") > -1`은 거짓이다. 3이 `SIZE_MAX`보다 크지 않기 때문이다.
- `objdump -d`(gcc `-O2`)로 본 확장 명령:

```text
0000000000000000 <widen_s>:
   4:	40 0f be c7          	movsbl %dil,%eax
0000000000000010 <widen_u>:
  14:	movzbl %dil,%eax
```

- Java(`Bits.java`) 출력:

```text
25 -> bin 11001, hex 19, 0x2d=45, 0b101101=45
~4 + 1 = -4  bits 11111111111111111111111111111100
-1 as unsigned = 4294967295, Integer.compareUnsigned(-1, 0) = 1
byte 0xC8: buf[0]=-56, buf[0] & 0xFF=200, Byte.toUnsignedInt=200
-16 >> 2 = -4, -16 >>> 28 = 15
-Integer.MIN_VALUE = -2147483648, Math.abs(MIN) = -2147483648
0xFFFFFFFF (int) = -1, 0xFFFFFFFFL = 4294967295
```

- 관찰 3: 16진 리터럴 `0xFFFFFFFF`도 `int`로는 −1이다. `L`을 붙여야 4,294,967,295다.

## 쓰이는 자료구조·알고리즘

- **모듈러 산술**: w비트 무부호 정수 연산(그리고 Java 정수 연산)은 2ʷ로 나눈 나머지 계산이다. C의 부호 있는 넘침은 미정의 동작이라 여기서 빠진다. 2의 보수는 그 나머지 중 −2ʷ⁻¹~2ʷ⁻¹−1을 대표값으로 고른 것이다 → [math/11-modular-arithmetic](../../math/11-modular-arithmetic/2-summary.md).
- **비트 연산**(🔧): 마스크 `& 0xFF`, 부호 비트 검사 `x < 0` 또는 `(x >>> 31) == 1`, 2의 거듭제곱 판정 `x & (x - 1)` → [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md).
- **비트셋**: 무부호 해석이 자연스러운 자료구조. Java `BitSet`·`long[]` 단어 배열 → [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md).
- **논리 연산**: 비트 단위 AND·OR·NOT은 명제 논리의 연결사를 자리마다 적용한 것이다 → [math/01-propositional-logic](../../math/01-propositional-logic/2-summary.md).
- **해시**: `(h & 0x7fffffff) % n`은 부호 비트를 지워 음수 인덱스를 막는 관용구다. `Math.abs(h) % n`은 `MIN_VALUE`에서 음수가 남는다.

## 적용 — 풀어나가는 법

### 1. 증상 → 원인

| 증상 | 먼저 의심할 표현 문제 |
|---|---|
| 음수인데 경계 검사를 통과한다 / 루프가 끝나지 않는다 | 부호 있는 값과 무부호(`size_t`·`unsigned`)의 비교·변환(`memcpy` 길이 인자 등) |
| 0~255여야 할 값이 음수(−128~−1) | Java `byte`·C `signed char`의 부호 확장 |
| 같은 입력의 해시·체크섬이 언어마다 다르다 | 바이트를 한쪽은 부호 있게, 한쪽은 부호 없게 더함 |
| 로그의 4294967295, 65535, 255 | −1을 32·16·8비트 무부호로 찍음 |
| `Math.abs` 결과가 음수 | `MIN_VALUE`(2의 보수 비대칭) |

### 2. 확인하는 법

- 바이트를 직접 본다: `xxd file | head`, Java `HexFormat.of().formatHex(bytes)`.
- C 컴파일 경고: C에서는 `-Wall`만으로 `-Wsign-compare`가 켜지지 않는다. `-Wall -Wextra`(그리고 대입까지 보려면 `-Wsign-conversion`).
- 기계어로 본다: `objdump -d` 출력에서 `movsbl`/`movsx`면 부호 확장, `movzbl`/`movzx`면 0 확장이다.
- 셸 종료 코드: 프로세스 종료 상태는 하위 8비트만 부모에게 간다(`man 3 exit`: "status & 0xFF"). `return -1`은 255로 보인다(실험: `./ex; echo $?` → 255).

### 3. 코드로 고정한다 (Java 21)

```java
int len   = Byte.toUnsignedInt(buf[off]);          // 0..255
long u32  = Integer.toUnsignedLong(readInt());     // 0..4294967295, 무부호 32비트 필드
int idx   = (key.hashCode() & 0x7fffffff) % n;     // 음수 인덱스 방지 (또는 Math.floorMod)
boolean b = Integer.compareUnsigned(a, c) < 0;     // 무부호 비교
```

- C에서는 비교 전에 부호를 먼저 확인한다: `if (i < 0 || (size_t)i >= n) error;`.

## 장애 시나리오와 대처

### 1. `-1 > 0u` — 음수 길이가 경계 검사를 통과 (⚠ 커리큘럼)

- **현상**: `int len`, `int max`일 때 클라이언트가 보낸 길이 −1은 `if (len > max)` 검사를 그대로 통과한다(둘 다 부호 있는 비교). 이어서 `memcpy(dst, src, len)`의 `size_t` 인자로 바뀌며 거대 길이가 된다. 반대로 `max`가 `size_t`면 −1이 `SIZE_MAX`가 되어 `len > max`가 참이다. 이번엔 정상 경로가 엉뚱하게 막힌다.
- **보이는 형태**: 컴파일 경고 `-Wsign-compare`(켜져 있다면). 런타임에는 아무 표시 없이 잘못된 분기. 뒤따라 거대 `memcpy`로 `SIGSEGV`.
- **원인**: 부호 있는 `int`가 `unsigned`/`size_t`와 만나는 자리(섞인 비교, 무부호 인자 전달)에서 무부호로 바뀌었다(5절).
- **대처**: 부호를 먼저 검사한다. 길이·인덱스 타입을 한 가지로 맞춘다. CI에서 `-Wall -Wextra -Werror=sign-compare`. 넘침까지 이어지는 경우는 [02](../02-integer-overflow-and-truncation/2-summary.md)·[security/24-memory-safety-exploits](../../security/24-memory-safety-exploits/2-summary.md).

### 2. 부호 확장 실수 — 길이 바이트 200이 −56 (⚠ 커리큘럼)

- **현상**: 바이너리 프로토콜 파서가 128 이상의 길이에서만 실패한다.
- **보이는 형태**: Java `NegativeArraySizeException: -56` 또는 `IndexOutOfBoundsException`. 길이 127까지는 테스트가 통과한다.
- **원인**: `int len = buf[i];`가 `byte` 0xC8을 부호 확장해 −56이 되었다(6절, 실험).
- **대처**: `Byte.toUnsignedInt`/`& 0xFF`. 테스트에 경계값 127·128·255를 넣는다.

### 3. 언어마다 다른 해시 — 비ASCII 바이트에서만 어긋남

- **현상**: Java 서비스와 C 확장 모듈이 같은 키로 다른 샤드를 고른다. ASCII 키에서는 같다.
- **보이는 형태**: 캐시 적중률 하락, "키가 없다" 오류가 한글·악센트 키에만 몰림.
- **원인**: UTF-8 바이트 0x80 이상을 Java는 `byte`(음수)로, C는 `unsigned char`로 더했다.
  - 실험(`Hash.java`·`hash.c`): "café"(`63 61 66 c3 a9`)에 `h = h*31 + b`를 적용하면 Java `byte`는 94414350, Java `b & 0xFF`와 C `unsigned char`는 둘 다 94422542.
- **대처**: 바이트 해시는 명세에 "바이트를 0~255로 본다"고 적고, 교차 언어 테스트 벡터에 0x80 이상 바이트를 넣는다.

### 4. `Math.abs(hash) % n`이 음수

- **현상**: 수십억 건 중 드물게 `ArrayIndexOutOfBoundsException: -3`.
- **원인**: `hashCode()`가 `Integer.MIN_VALUE`일 때 `Math.abs`가 음수를 돌려준다(2절 비대칭, 실험).
- **대처**: `Math.floorMod(h, n)` 또는 `(h & 0x7fffffff) % n`. 상세는 [math/11](../../math/11-modular-arithmetic/2-summary.md) 장애 3.

### 5. 로그의 4294967295 — −1을 잘못 찍음

- **현상**: 모니터링에 "남은 재시도 4294967295회", 종료 코드 255.
- **원인**: 감소 카운터가 0 아래로 내려가 무부호로 감겼다. 또는 −1(실패 표시)을 무부호로 출력했다.
- **대처**: 로그에 16진(`0xFFFFFFFF`)을 함께 찍으면 "−1이 무부호로 보인 것"이 바로 보인다. 카운터는 0에서 멈추게 검사한다.

## 핵심 문장

- 메모리에는 비트만 있다. 부호 있음·없음은 그 비트를 읽는 규칙이다.
- 2의 보수는 맨 위 비트의 무게를 −2ʷ⁻¹로 읽는 규칙이다. 덕분에 부호 있는 덧셈과 부호 없는 덧셈이 같은 덧셈기를 쓴다(x86-64에서는 같은 명령).
- 2의 보수에서 같은 폭의 부호/무부호 변환은 비트를 바꾸지 않는다. 맨 위 비트가 1이면 값이 2ʷ만큼 달라진다.
- C에서 `int`와 `unsigned`를 비교하면 `int`가 무부호로 바뀐다. `-1 > 0u`가 참이다.
- 넓힐 때 부호 있는 타입은 부호 확장, 무부호 타입은 0 확장된다. Java `byte`는 부호 있는 타입이다.
- 2의 보수 범위는 비대칭이다. `MIN_VALUE`의 부호를 뒤집으면 자기 자신이 된다.

## 관련 주제·근거

- 선행: [math/01-propositional-logic](../../math/01-propositional-logic/2-summary.md)
- 원고: [foundations/data-representation](../../foundations/data-representation/README.md) §1(진수 변환·2의 보수)
- 후속(이 영역): [02-integer-overflow-and-truncation](../02-integer-overflow-and-truncation/2-summary.md) · [03-floating-point-ieee754](../03-floating-point-ieee754/2-summary.md) · [06-byte-order-and-alignment](../06-byte-order-and-alignment/2-summary.md) · [04 문자 인코딩](../04-character-encoding-unicode/2-summary.md), [07 게이트·가산기](../07-logic-gates-to-adder/2-summary.md)
- 연결
  - [math/11-modular-arithmetic](../../math/11-modular-arithmetic/2-summary.md) — 2의 보수 = 2ʷ 모듈로, `MIN_VALUE` 비대칭
  - [languages/c/syntax/03-integer-promotion-and-usual-arithmetic-conversions](../../../languages/c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/2-summary.md) — C 승격·변환 규칙 전체
  - [languages/java/syntax/02-numeric-operations](../../../languages/java/syntax/02-numeric-operations/2-summary.md) — Java 시프트·승격
  - [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md) · [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)
  - [security/24-memory-safety-exploits](../../security/24-memory-safety-exploits/2-summary.md) — 부호 혼동이 메모리 오류로 이어지는 경로
- 근거
  - R. Bryant, D. O'Hallaron, 『Computer Systems: A Programmer's Perspective』 3판(CS:APP) — 2.1.1 Hexadecimal Notation, 2.2.2 Unsigned Encodings, 2.2.3 Two's-Complement Encodings, 2.2.4 Conversions between Signed and Unsigned, 2.2.5 Signed versus Unsigned in C, 2.2.6 Expanding the Bit Representation of a Number(절 번호는 저자 사이트 머리말 PDF의 목차로 확인 <https://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf>)
  - JLS SE 21 §4.2(2의 보수 정수), §4.2.1(범위, `char` 무부호), §15.19(시프트) <https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html>
  - ISO C11 위원회 초안 N1570 — §6.2.6.2(세 가지 부호 표현 허용), §6.3.1.3(정수 간 변환), §6.3.1.8(통상 산술 변환) <https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf>. §6.5.7(음수 `>>` 구현 정의).
  - GCC 매뉴얼 "Integers implementation"(부호 있는 타입으로의 범위 밖 변환은 2^N 모듈로, 음수 `>>`는 부호 확장) <https://gcc.gnu.org/onlinedocs/gcc/Integers-implementation.html>
  - WG14 N2412, J. Bastien·J. Gustedt, "Two's complement sign representation for C2x", 2019 <https://www.open-std.org/jtc1/sc22/wg14/www/docs/n2412.pdf>
  - Linux man-pages `exit(3)` — "status & 0xFF"
- 실험 목록
  - `signcmp.c` — 8비트 두 해석, `-1 > 0u`, `strlen > -1`, 부호/0 확장, `INT8_MIN` 부정. gcc 13.3.0 `-O0 -Wall -Wextra`(경고 2), `-Wall`만(경고 0), `-O2` 목적 파일 `objdump -d`(`movsbl`/`movzbl`). 호스트 i7-13700HX, Linux 7.0.0-34.
  - `Bits.java` — 진수 표기, `~x+1`, `compareUnsigned`, `byte` 부호 확장, `>>`/`>>>`, `MIN_VALUE`, `0xFFFFFFFF` 리터럴. OpenJDK 21.0.12, Docker `--cpus=2 --network none`.
  - `Hash.java`·`hash.c` — "café" UTF-8 바이트 해시의 부호 차이. 같은 환경.
  - `ex.c` — `return -1` → `$?` 255(셸), Python `subprocess` 255.
  - 파일 위치: scratchpad `arch/01/e01/`.
