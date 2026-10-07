# architecture/02-integer-overflow-and-truncation — 정수 오버플로와 좁히기 절단: 고정 폭이 값을 감고 자른다 — 정리 (힌트)

## 해결하는 문제

CPU 레지스터와 정수 타입은 폭이 정해져 있다(8·16·32·64비트).\
수학의 정수는 끝이 없다. 결과가 폭을 넘으면 하드웨어는 **넘친 자리를 버린다.** 값이 조용히 감기거나 잘린다.

쉬운 예: 여섯 자리 주행거리계.

```text
  999,999 km 에서 1 km 더 달리면 → 000,000
  "100만 km 탄 차"가 "새 차"로 보인다. 계기판은 경고하지 않는다.
```

똑같은 구조다.\
Java의 32비트 `int` 덧셈이 2,147,483,647을 넘으면 음수로 감긴다(C의 부호 있는 넘침은 감김이 아니라 미정의 동작 — 6절). 64비트 `double`을 16비트 정수로 옮기면 언어마다 갈린다. Java는 먼저 정수로 바꾼 뒤 그 정수의 상위 비트를 버리고, Ada는 예외를 낸다(5절).

실무 예:
- 잔액 20억 원에 3억 원을 더한 `int` 합이 −1,994,967,296원이 된다(아래 실험).
- Ariane 5 첫 발사(1996-06-04): 64비트 부동소수를 16비트 부호 있는 정수로 바꾸다 Operand Error가 났다. 관성 기준 장치 두 대가 같은 이유로 멈췄다(조사 보고서).
- C에서 `total - hdr`이 `size_t`라서 음수 대신 18,446,744,073,709,551,612가 된다. 이 값으로 할당·복사를 시도한다.
- Boeing 787: 전원을 248일 연속 켜 두면 발전기 제어 장치의 소프트웨어 카운터가 넘친다. 주 GCU 4대를 동시에 켰다면 교류 전원을 모두 잃을 수 있다(FAA AD 2015-09-07).

## 동작·원리

### 1. 덧셈 넘침 — 수직선이 원이 된다

```text
  32비트 int (2의 보수)

  −2,147,483,648 ─────────── 0 ─────────── 2,147,483,647
        ▲                                         │
        └───────────── +1 하면 여기로 ────────────┘

  양의 넘침: 양수 + 양수 → 음수      (20억 + 3억 = −1,994,967,296)
  음의 넘침: 음수 + 음수 → 양수      (MIN − 1 = MAX)
```

- 진짜 합이 2³¹ 이상이면 2³²를 뺀 값, −2³¹ 미만이면 2³²를 더한 값이 남는다(CS:APP 2.3.2 "Two's-Complement Addition").
- 무부호 덧셈은 2ʷ 이상이 되면 2ʷ를 뺀다. 결과가 두 피연산자 중 하나보다 작아지면 넘친 것이다(CS:APP 2.3.1 "Unsigned Addition").
- Java는 이 동작을 명세로 정했다. "넘친 정수 덧셈의 결과는 수학적 합의 하위 비트"(JLS §15.18.2). "정수 연산자는 넘침을 어떤 식으로도 알리지 않는다"(JLS §4.2.2).
- 2의 보수 표현 자체는 [01-number-systems-twos-complement](../01-number-systems-twos-complement/2-summary.md), 모듈로 관점은 [math/11-modular-arithmetic](../../math/11-modular-arithmetic/2-summary.md) 6절.

### 2. 하드웨어는 넘침을 안다 — 플래그 두 개

```text
  add %esi,%edi        ← 덧셈 명령은 하나
     │
     ├─ CF (Carry Flag)    : 무부호로 보면 넘쳤나   → setb / jc 로 읽음
     └─ OF (Overflow Flag) : 2의 보수로 보면 넘쳤나 → seto / jo 로 읽음

  0xFFFFFFFF + 1:   CF = 1 (무부호 4294967295 + 1 넘침)
                    OF = 0 (부호 있는 −1 + 1 = 0, 정상)
```

- x86-64의 `add`는 덧셈 한 번에 두 해석의 넘침을 모두 계산해 플래그에 둔다. 무시할지 확인할지는 소프트웨어가 정한다.
  - 플래그를 두는지, 어떤 명령이 갱신하는지는 ISA마다 다르다. RISC-V 기본 정수 ISA는 넘침 전용 지원을 두지 않고 분기로 검사한다(`add t0, t1, t2; bltu t0, t1, overflow` — RISC-V 비특권 명세 RV32I 장). AArch64는 플래그를 갱신하는 `ADDS`를 `ADD`와 따로 둔다 `[?]`(Arm 매뉴얼 원문 미확인).
- 부호 있는 넘침 판정 규칙: **두 피연산자의 부호가 같고 결과의 부호가 다르면** 넘친 것이다.
  - JDK 21 `Math.addExact(int,int)` 소스가 이 규칙을 그대로 쓴다: `if (((x ^ r) & (y ^ r)) < 0) throw new ArithmeticException("integer overflow");` (소스 주석 "HD 2-12 Overflow iff both arguments have the opposite sign of the result"). 이 메서드는 `@IntrinsicCandidate`이고 HotSpot `vmIntrinsics.hpp`에 `_addExactI`로 등록돼 있다. JIT이 실제로 어떤 명령을 내는지는 이번에 확인하지 않았다.
- C에서는 gcc·clang의 `__builtin_add_overflow`가 있다. 규칙은 "무한 정밀도 결과가 저장 타입에 들어가는가"이고, 컴파일러는 가능하면 하드웨어 명령으로 구현한다(GCC 매뉴얼 "Integer Overflow Builtins"). x86-64 gcc 13.3 `-O2`에서는 이 플래그를 읽는 코드로 컴파일됐다. 부호 있는 판은 `add` + `seto`, 무부호 판은 `add` + `setb`였다(아래 실험).

### 3. 곱셈 넘침 — 넓히는 시점이 늦으면 이미 잘렸다

```text
  long micros = 30 * 24 * 60 * 60 * 1000 * 1000;   ← int 끼리 곱한 뒤 long 에 대입
                └──────────── int 곱셈 (32비트에서 감김) ───────────┘
                                                      → 2,134,720,512 (틀림)
  long micros = 30L * 24 * 60 * 60 * 1000 * 1000;  → 2,592,000,000,000 (맞음)
```

- 곱셈도 결과의 하위 w비트만 남긴다(CS:APP 2.3.4·2.3.5, JLS §15.17.1).
- 대입하는 쪽이 `long`이어도 오른쪽 식은 `int`로 먼저 계산된다. `javap`로 본 `imul` → `i2l` 순서 설명은 [languages/java/syntax/02](../../../languages/java/syntax/02-numeric-operations/2-summary.md) (2)절에 있다.

### 4. 좁히기 — 상위 비트를 버린다

```text
  int 70000  = 0000 0000 0000 0001 0001 0001 0111 0000
                                   └──── 하위 16비트 ────┘
  (short)    =                     0001 0001 0111 0000  = 4464   (70000 − 65536)

  int 200    = ... 0000 0000 1100 1000
  (byte)     =               1100 1000  = −56   (맨 위 비트가 켜져 음수로 읽힘)
```

- *좁히기 변환(narrowing)*: 더 좁은 정수 타입으로 바꾸는 것. Java는 "하위 n비트만 남기고 버린다. 부호가 바뀔 수 있다"(JLS §5.1.3).
- C는 무부호 타입으로의 변환은 2ⁿ 모듈로로 정의, 부호 있는 타입으로의 범위 밖 변환은 구현 정의다(N1570 §6.3.1.3). gcc는 2ⁿ 모듈로로 정했다(GCC 매뉴얼 "Integers implementation").
- CS:APP 2.2.7 "Truncating Numbers".
- Java의 `+=`·`-=`에는 보이지 않는 좁히기 캐스트가 들어 있다. `short s = 32767; s += 1;`은 컴파일되고 −32768이 된다. `E1 op= E2`는 `E1 = (T)((E1) op (E2))`와 같다. 단 `E1`은 한 번만 평가된다(JLS §15.26.2, 실험).

### 5. 부동소수 → 정수 — 언어마다 결과가 셋으로 갈린다

```text
  double 40000.7  →  16비트 부호 있는 정수(범위 −32768 … 32767)

  Java  (short) 40000.7   1단계: int 로 (0 쪽으로 버림) = 40000
                          2단계: short 로 좁히기       = −25536      예외 없음 (명세)
  Java  (int) 1e10        int 범위 밖 → int 최댓값 2147483647 으로 포화   (명세)
  C     (int) 1e10        미정의 동작. x86-64 gcc -O0 에서 cvttsd2si → −2147483648
  Ada   (Ariane 5 SRI)    변환 중 Operand Error 예외 → 보호 없음 → 명세대로 프로세서 정지
```

- Java는 두 단계를 명세로 정했다(JLS §5.1.3).
  - 1단계: NaN은 0, 범위 밖은 `int`/`long`의 최솟값·최댓값으로 포화, 나머지는 0 쪽으로 버림.
  - 2단계: 목표가 `byte`·`short`·`char`면 1단계 `int` 결과를 다시 정수 좁히기(하위 비트).
  - 그래서 `(short) 1e10`은 `(short) Integer.MAX_VALUE` = −1이다(실험). 포화 뒤에 절단이 한 번 더 일어난다.
- C는 "정수 부분이 목표 타입으로 표현되지 않으면 동작이 정의되지 않는다"(N1570 §6.3.1.4 ¶1). x86-64의 `cvttsd2si`는 범위 밖이면 invalid 예외를 올리고, 그 예외가 마스크돼 있으면 "integer indefinite" 값 0x80000000을 돌려준다(Intel SDM 명령 설명의 비공식 사본 <https://www.felixcloutier.com/x86/cvttsd2si>, 실험에서 −2147483648). `-fsanitize=float-cast-overflow`가 이것을 런타임 오류로 보고한다.
- *포화(saturation)*: 범위를 넘으면 최댓값·최솟값에 붙여 두는 것. 감기는 것(wrap)보다 피해가 작을 때가 많지만, 틀린 값인 것은 같다.

### 6. 언어별 넘침 의미

| 언어 | 부호 있는 정수 넘침 | 무부호 넘침 | 근거 |
|---|---|---|---|
| Java | 하위 비트로 감김(정의됨), 알림 없음 | 무부호 타입 없음 | JLS §4.2.2·§15.18.2 |
| C | **미정의 동작** | 2ʷ 모듈로(정의됨, "넘치지 않는다"고 표현) | N1570 §6.5 ¶5, §6.2.5 ¶9 |
| Python | 넘침 없음(정수는 임의 정밀도) | — | Python 문서 "Integers have unlimited precision" |

- C의 미정의 동작은 "감긴 값"이 아니다. 컴파일러는 넘침이 없다고 **가정**해도 된다.
  - gcc 13.3에서 `int will_overflow(int x) { return x + 1 < x; }`는 `-O0`에서도 `-O2`에서도 상수 0을 돌려주는 코드로 접혔다(실험). 넘침 검사를 넘침에 기대어 쓰면 검사가 사라진다.
  - `-fsanitize=undefined`로 빌드하면 같은 호출에서 `runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'`가 나오고 결과도 1로 바뀌었다.
- 승격·변환 규칙과 UB가 최적화로 바뀌는 다른 예는 [languages/c/syntax/03](../../../languages/c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/2-summary.md) (4)~(6)절.

### 실험: 감김·절단·포화·플래그

- 환경: i7-13700HX, Linux 7.0.0-34, gcc 13.3.0(호스트) / OpenJDK 21.0.12+8-LTS(`eclipse-temurin:21-jdk`, Docker `--cpus=2 --network none`), 2026-10-07. 결정적 출력(2회 실행 같음).
- Java(`Overflow.java`) 핵심과 출력:

```java
int balance = 2_000_000_000, deposit = 300_000_000;
System.out.println(balance + deposit);
Math.addExact(balance, deposit);                       // 예외
System.out.println((short) 70000 + ", " + (short) 40_000.7 + ", " + (int) 1e10 + ", " + (short) 1e10);
```

```text
int 20억 + 3억 = -1994967296
Math.addExact -> java.lang.ArithmeticException: integer overflow
long 으로 넓혀 더하면 = 2300000000
30일(µs) int 곱 = 2134720512, long 곱 = 2592000000000
(short) 70000 = 4464  (70000 - 65536 = 4464)
(byte) 200 = -56, (int) 3_000_000_000L = -1294967296
Math.toIntExact(3e9) -> java.lang.ArithmeticException: integer overflow
(int) 40000.7 = 40000, (short) 40000.7 = -25536
(int) 1e10 = 2147483647, (int) NaN = 0, (long) -Inf = -9223372036854775808
(short) 1e10 = -1  (= (short) Integer.MAX_VALUE)
short s = 32767; s += 1 -> -32768
2^31 centiseconds = 248.55 days
(lo+hi)/2 = -397483648, (lo+hi)>>>1 = 1750000000, lo+(hi-lo)/2 = 1750000000
```

- C(`flags.c`, gcc `-O2`) 출력과 `objdump -d`:

```text
INT_MAX + 1 : overflow=1, wrapped=-2147483648
UINT_MAX + 1: carry=1, wrapped=0
same bits 0xFFFFFFFF + 1: as int overflow=0 (0), as unsigned carry=1 (0)
sat_add_u8(200, 100) = 255, plain (uint8_t)(200+100) = 44

<add_s>:  add %esi,%edi ; mov %edi,(%rdx) ; seto %al ; ret
<add_u>:  add %esi,%edi ; mov %edi,(%rdx) ; setb %al ; ret
```

- C(`sizet.c`) 출력 — 할당은 하지 않고 값만 찍었다:

```text
body_len(4, 8) = 18446744073709551612 (0xfffffffffffffffc)
SIZE_MAX       = 18446744073709551615
cnt=1073741825, cnt*4 (uint32) = 4 bytes  <- 원소 10억 개에 4바이트 버퍼
will_overflow(INT_MAX) = 0                      (-O0, -O2 모두. objdump: -O0 mov $0x0,%eax / -O2 xor %eax,%eax; ret)
will_overflow(INT_MAX) = 1                      (-O2 -fsanitize=undefined, 위 runtime error 와 함께)
```

- C(`f2i.c`, gcc `-O0`): `(int)1e10 = -2147483648, (short)40000.7 = -25536`. `-fsanitize=float-cast-overflow`를 켜면 `1e+10 is outside the range of representable values of type 'int'`와 `40000.7 is outside the range of representable values of type 'short int'`가 나왔다.
- 관찰: 같은 0xFFFFFFFF + 1이 부호 있는 해석에서는 넘침이 아니고 무부호 해석에서는 자리올림이다. 하드웨어는 같은 `add`를 하고 플래그만 다르게 읽는다.

## 쓰이는 자료구조·알고리즘

- **넘침 검출**(🔧): 부호 판정 규칙(`((x ^ r) & (y ^ r)) < 0`), `Math.addExact`·`multiplyExact`·`toIntExact`, C `__builtin_*_overflow`, 128비트 곱 `Math.multiplyHigh`.
- **포화 산술**(🔧): 넘치면 끝값에 붙인다. Java 21 `Math.clamp(long value, int min, int max)`는 `long` 결과를 `int` 범위에 붙여 돌려준다(Java 21 API).
- **이진 탐색 중간값**: `(lo + hi) / 2` 넘침 → `lo + (hi - lo) / 2` 또는 `(lo + hi) >>> 1`. 둘 다 `0 ≤ lo ≤ hi`인 배열 인덱스를 전제로 한다(음수 `lo`·`hi`면 `>>> 1`이 큰 양수를 내고, 범위 양 끝이면 `hi - lo`도 넘친다) → [algorithm/43-alg-incidents](../../algorithm/43-alg-incidents/2-summary.md) 사건 1, [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md).
- **링 버퍼 순번**: 감기는 순번을 일부러 쓰는 구조. 차이는 `(a - b)`의 부호로 비교한다 → [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md).
- **모듈러 거듭제곱의 넘침 경계**: `(m − 1)² ≤ 2⁶³ − 1` → [math/11](../../math/11-modular-arithmetic/2-summary.md) 5절.

## 적용 — 풀어나가는 법

### 1. 증상 → 원인

| 증상 | 의심 |
|---|---|
| 큰 금액·누계·ID에서만 음수, 부호 뒤집힘 | `int` 덧셈·곱셈 넘침 |
| 값이 65536·256 단위로 틀어짐(70000 → 4464) | `short`·`byte`·`char`로 좁히기 |
| 부동소수에서 온 정수가 2147483647 또는 −2147483648에 붙음 | 부동소수 → 정수 포화(Java) 또는 범위 밖 변환(C UB, x86 0x80000000) |
| 거대한 크기(1.8×10¹⁹, 4×10⁹)로 할당·복사 시도 | 무부호 뺄셈 언더플로(`size_t`) |
| 오래 켜 둔 장비·프로세스만 수백 일 뒤 이상 | 시간 카운터 넘침(2³¹ 틱) |

### 2. 확인하는 법

- 넘침이 나는 크기를 계산한다. 1/100초 틱을 부호 있는 32비트에 세면 2³¹ / 100 / 86400 ≈ 248.55일, 1밀리초 틱이면 약 24.86일이다(계산).
- C: `-fsanitize=undefined`(부호 있는 넘침, 시프트), `-fsanitize=float-cast-overflow`, `-Wconversion`(좁히기 대입 경고). 개발 빌드에 켠다.
- Java: 의심 연산을 `Math.*Exact`로 바꿔 테스트를 돌리면 넘침 지점이 `ArithmeticException` 스택으로 드러난다.
- 바이너리: `objdump -d`에서 `jo`·`seto`(부호 있는 넘침 검사), `jc`·`setb`(자리올림 검사)가 있는지 본다.

### 3. 코드로 고정한다 (Java 21)

```java
long total = Math.addExact(a, b);                 // 넘치면 예외 — 금액·수량
int  n     = Math.toIntExact(longCount);          // long → int 좁히기 검사
short s    = (short) Math.clamp(v, Short.MIN_VALUE, Short.MAX_VALUE); // 의도적 포화
long micros = 30L * 24 * 60 * 60 * 1000 * 1000;   // 곱셈 시작 전에 long
```

```c
/* C: 뺄셈 전에 크기 비교, 곱셈은 검사 내장 함수 */
if (total < hdr) return -1;
size_t body = total - hdr;
size_t bytes;
if (__builtin_mul_overflow(cnt, sizeof(elem_t), &bytes)) return -1;
```

## 장애 시나리오와 대처

### 1. `int` 금액이 21억을 넘어 음수 (⚠ 커리큘럼)

- **현상**: 법인 계좌의 합계·월 누계가 어느 날 음수로 표시된다. 음수 잔액이라 출금 차단·정산 실패.
- **보이는 형태**: 예외 없음. 로그에 `-1994967296` 같은 값. DB에는 `BIGINT`로 맞게 있는데 애플리케이션 DTO만 `int`.
- **원인**: 2,147,483,647원 초과를 `int`로 더했다. Java는 넘침을 알리지 않는다(JLS §4.2.2).
- **대처**: 금액은 `long`(최소 단위) 또는 `BigDecimal`. 누적은 `Math.addExact`. DTO·DB·JSON 타입 폭을 함께 점검한다([domain-modeling/14](../../domain-modeling/14-money-arithmetic-rounding-allocation/2-summary.md)).

### 2. Ariane 5 501편 — 64비트 → 16비트 변환 (⚠ 커리큘럼)

- **현상**(보고서 원문 요지): 1996-06-04 첫 비행. H0 + 약 36.7초에 예비·주 관성 기준 장치(SRI)가 거의 동시에 멈췄다. 주 컴퓨터가 SRI의 진단 비트 패턴을 비행 데이터로 해석해 일어나지 않은 자세 편차를 고치려고 노즐을 크게 꺾었다("a large correction", 3.1 h — 2.1은 결과를 "full nozzle deflections"로 적는다). H0 + 39초에 공력 하중으로 분해됐다.
- **보이는 형태**: "data conversion from 64-bit floating point to 16-bit signed integer value"에서 Operand Error. 변환된 값(수평 편향 BH)이 16비트 부호 있는 정수로 표현할 수 있는 값보다 컸다.
- **원인**(보고서)
  - 이 정렬 함수는 이륙 전에만 의미가 있는데, Ariane 4 요구사항 때문에 이륙 뒤 약 40초까지 돌았다.
  - Ariane 5의 초기 궤적은 Ariane 4보다 수평 속도가 훨씬 커서 BH가 예상보다 컸다.
  - 변환 위험이 있는 변수 7개 중 4개만 보호했다. 나머지 3개는 "물리적으로 제한되거나 여유가 크다"는 추론이었는데 BH에서는 틀렸다. 보호하지 않은 이유로 SRI 컴퓨터 작업량 목표 80%가 언급됐다.
  - 예외가 나면 실패를 버스에 알리고, 상태를 EEPROM에 저장하고, 프로세서를 정지하도록 명세돼 있었다. 보고서는 "프로세서를 멈추기로 한 결정이 결국 치명적이었다"고 적는다.
- **대처**(보고서 권고 중): 센서가 최선의 데이터를 계속 보내게 할 것(R3), 장비가 주는 값에 대한 코드의 암묵적 가정을 찾아 범위를 검증할 것(R5), 궤적 데이터를 명세·시험 요구사항에 넣을 것(R10).
- 해석: 좁히기 자체보다 "범위 가정이 재사용 환경에서 깨짐"과 "예외 = 정지" 설계가 결합해 사고가 됐다. 같은 변환을 Java로 쓰면 예외 없이 −25536 같은 틀린 값이 나온다(실험) — 정지 대신 조용한 오값이다.

### 3. `size_t` 언더플로 → 거대 할당·버퍼 넘침 (⚠ 커리큘럼)

- **현상**: 잘린 패킷(전체 4바이트, 헤더 8바이트)을 받자 프로세스가 `malloc` 실패·`SIGSEGV`로 죽거나, 메모리를 넘어 쓴다.
- **보이는 형태**: 로그의 길이 `18446744073709551612`(0xfffffffffffffffc), `std::bad_alloc`, `Cannot allocate memory`.
- **원인**: `total - hdr`가 무부호라 음수 대신 2⁶⁴ − 4가 되었다. 반대 방향으로는 `cnt * 4`가 32비트에서 감겨 원소 약 10.7억 개(1,073,741,825)에 4바이트 버퍼가 잡힌다(실험) — 이후 복사가 힙을 넘어 쓴다.
- **대처**: 빼기 전에 `if (total < hdr)`. 곱셈은 `__builtin_mul_overflow`·`calloc`·`reallocarray`(원소 수·크기를 따로 받아 곱 넘침이면 오류를 돌려준다 — Linux man-pages `malloc(3)`). 공격으로 이어지는 경로는 [security/24](../../security/24-memory-safety-exploits/2-summary.md).

### 4. 248일 카운터 — 오래 켜 둔 장비만 고장

- **현상**: Boeing 787을 248일 연속 전원 공급하면 GCU가 failsafe 모드로 들어간다. 주 발전기 제어 장치(GCU) 4대를 동시에 켰다면 4대가 동시에 failsafe 모드로 들어가 교류 전원을 모두 잃을 수 있다(FAA AD 2015-09-07, Federal Register 2015-05-01).
- **원인**(AD 원문): "a software counter internal to the GCUs that will overflow after 248 days of continuous power".
- 해석: 2³¹ / 100 / 86400 = 248.55일이다(실험 계산). 1/100초 틱을 부호 있는 32비트로 셌다면 이 날짜와 맞는다. AD는 카운터 폭·단위를 밝히지 않으므로 이것은 추정이다.
- **대처**: AD는 스스로를 임시 조치(interim action)라 하고, 120일을 넘지 않는 간격의 반복 전원 차단 정비를 요구했다. 제조사는 GCU 소프트웨어 개선판을 개발 중이었다. 일반 대처: 경과 시간은 64비트로 세고, 두 시각의 **차**로 비교하며(`now - start`), 감김 시점을 앞당긴 시험(카운터 초기값을 MAX 근처로)을 둔다.

### 5. 넘침 검사가 최적화로 사라짐

- **현상**: `if (x + 1 < x) return ERR;` 검사가 있는데 넘침이 그대로 통과한다.
- **보이는 형태**: 검사 코드가 상수 0으로 접혔다. `-O0`은 `mov $0x0,%eax`, `-O2`는 `xor %eax,%eax; ret`(실험, gcc 13.3).
- **원인**: C에서 부호 있는 넘침은 미정의 동작이라, 컴파일러는 `x + 1 < x`가 거짓이라고 가정해도 된다(N1570 §6.5 ¶5).
- **대처**: 넘치기 **전에** 비교한다(`if (x > INT_MAX - 1)`), 또는 `__builtin_add_overflow`. 개발 빌드에 `-fsanitize=undefined`.

## 핵심 문장

- 고정 폭 정수는 결과의 하위 w비트만 남긴다. 넘치면 2ʷ만큼 감긴다.
- x86-64의 `add`는 무부호 넘침(CF)과 부호 있는 넘침(OF)을 플래그로 남긴다(플래그 방식은 ISA마다 다르다). 대부분의 언어는 그것을 읽지 않는다.
- Java 정수 넘침은 정의된 감김이고 알림이 없다. `Math.*Exact`가 같은 계산에 예외를 단다.
- C의 부호 있는 넘침은 미정의 동작이라 컴파일러가 넘침 검사를 지울 수 있다. 무부호는 2ʷ 모듈로다.
- 좁히기는 상위 비트를 버린다. 부동소수 → 정수는 Java 포화, C 미정의, Ada 예외로 갈린다.
- 넘침의 피해는 "언제 터지나"로 나뉜다. 큰 입력, 오래 켜 둔 시간, 재사용된 환경에서 터진다.

## 관련 주제·근거

- 선행: [01-number-systems-twos-complement](../01-number-systems-twos-complement/2-summary.md)
- 이 영역: [03-floating-point-ieee754](../03-floating-point-ieee754/2-summary.md)(부동소수 → 정수 변환의 다른 쪽), [07 가산기·자리올림](../07-logic-gates-to-adder/2-summary.md)
- 연결
  - [languages/c/syntax/03-integer-promotion-and-usual-arithmetic-conversions](../../../languages/c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/2-summary.md) — C의 UB·모듈러·경고 옵션
  - [languages/java/syntax/02-numeric-operations](../../../languages/java/syntax/02-numeric-operations/2-summary.md) — `imul`/`i2l`, `Math.*Exact`, 복합 대입 캐스트
  - [math/11-modular-arithmetic](../../math/11-modular-arithmetic/2-summary.md) · [algorithm/43-alg-incidents](../../algorithm/43-alg-incidents/2-summary.md) · [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md)
  - [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md) · [domain-modeling/14-money-arithmetic-rounding-allocation](../../domain-modeling/14-money-arithmetic-rounding-allocation/2-summary.md) · [security/24-memory-safety-exploits](../../security/24-memory-safety-exploits/2-summary.md)
- 근거
  - CS:APP 3판 — 2.2.7 Truncating Numbers, 2.3.1 Unsigned Addition, 2.3.2 Two's-Complement Addition, 2.3.4 Unsigned Multiplication, 2.3.5 Two's-Complement Multiplication(절 번호: <https://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf> 목차)
  - JLS SE 21 §4.2.2(넘침을 알리지 않음), §5.1.3(좁히기 — 정수 하위 비트, 부동소수 2단계·포화), §15.17.1·§15.18.2(넘친 곱·합 = 하위 비트) <https://docs.oracle.com/javase/specs/jls/se21/html/jls-5.html>. §15.26.2(복합 대입 = 암묵 캐스트).
  - Java SE 21 API `Math.addExact`·`toIntExact`·`multiplyHigh`·`clamp` <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Math.html>
  - OpenJDK jdk21u `src/java.base/share/classes/java/lang/Math.java`(`addExact` 본문, "HD 2-12"), `src/hotspot/share/classfile/vmIntrinsics.hpp`(`_addExactI`)
  - N1570(C11 초안) §6.2.5 ¶9(무부호는 넘치지 않음), §6.3.1.3(정수 변환), §6.3.1.4 ¶1(부동소수 → 정수 범위 밖 UB), §6.5 ¶5(예외 조건 UB) <https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf>
  - GCC 매뉴얼 "Integers implementation" <https://gcc.gnu.org/onlinedocs/gcc/Integers-implementation.html>
  - Intel SDM `CVTTSD2SI` 명령 설명(범위 밖 → invalid, 마스크 시 integer indefinite 80000000H) — 비공식 HTML 사본 <https://www.felixcloutier.com/x86/cvttsd2si>
  - Linux man-pages `malloc(3)` — `calloc`·`reallocarray`의 곱 넘침 검사, `malloc(n*size)`는 검사하지 않음
  - Python 문서 Built-in Types "Integers have unlimited precision" <https://docs.python.org/3/library/stdtypes.html>
  - "ARIANE 5 Flight 501 Failure — Report by the Inquiry Board"(의장 J. L. Lions, 1996-07-19) — 2.1·2.2절, 권고 R3·R5·R10. ESA PDF <https://esamultimedia.esa.int/docs/esa-x-1819eng.pdf>(스캔본이라 텍스트 추출 불가), 본문 텍스트 사본 <https://www-users.cse.umn.edu/~arnold/disasters/ariane5rep.html>
  - FAA AD 2015-09-07(Amendment 39-18153, Docket FAA-2015-0936), Federal Register 문서 2015-10066, 2015-05-01 게재 <https://www.federalregister.gov/documents/2015/05/01/2015-10066/airworthiness-directives-the-boeing-company-airplanes>
- 실험 목록
  - `Overflow.java` — 금액 넘침, `addExact`·`toIntExact`, 곱셈 넓히기 시점, `(short)`·`(byte)` 절단, 부동소수 → 정수 포화·2단계, `+=` 암묵 캐스트, 248일 계산, 이진 탐색 중간값. OpenJDK 21.0.12, Docker `--cpus=2 --network none`.
  - `flags.c` — `__builtin_add_overflow` 부호/무부호, 포화 덧셈, `objdump -d`(`seto`/`setb`). gcc 13.3.0 `-O2`, 호스트.
  - `sizet.c` — `size_t` 언더플로, `uint32` 크기 곱 감김, `x + 1 < x` 접힘(`-O0`·`-O2`·`-fsanitize=undefined`). 할당은 하지 않음.
  - `f2i.c` — C 범위 밖 부동소수 → 정수(`cvttsd2si`), `-fsanitize=float-cast-overflow`.
  - 파일 위치: scratchpad `arch/01/e02/`.
