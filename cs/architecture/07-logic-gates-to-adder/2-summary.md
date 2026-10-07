# architecture/07-logic-gates-to-adder — 트랜지스터 → 게이트 → 가산기·ALU, 캐리 전파 지연 — 정리 (힌트)

## 해결하는 문제

CPU의 `add` 명령은 결국 전기 스위치 수천 개다.\
스위치는 "켜짐/꺼짐"밖에 모른다. 이것만으로 덧셈을 하려면 두 가지를 풀어야 한다.

- 스위치로 논리(AND·OR·XOR)를 만드는 법.
- 논리로 "자리올림이 있는 덧셈"을 만드는 법, 그리고 그 자리올림이 **얼마나 빨리** 끝나는가.

쉬운 예: 손으로 `0999 + 0001`을 한다.

```text
    0 9 9 9
  + 0 0 0 1
  ─────────
    1 0 0 0      ← 맨 오른쪽 받아올림이 왼쪽 끝까지 차례로 번진다
```

- 일의 자리를 끝내야 십의 자리를 확정할 수 있다. 자리 수가 길수록 마지막 자리는 늦게 확정된다.

똑같은 구조다.\
2진 가산기도 아래 비트의 캐리(받아올림)를 기다려야 윗비트가 확정된다. 이 기다림은 CPU 클록을 얼마나 빠르게 돌릴 수 있는지를 제약하는 경로 중 하나다. 실제 주기는 가산기를 포함한 모든 경로 중 가장 느린 경로에 맞춘다(7절).

실무 예:
- 같은 `add` 명령 결과를 C는 "부호 있는 오버플로"로도, "무부호 캐리"로도 읽는다. 둘은 가산기의 서로 다른 출력 비트다(실험 8).
- 대규모 서버 군에서 특정 CPU 코어 하나가 특정 입력에서만 틀린 값을 낸다. 로그는 깨끗하다(Meta 2021, Google 2021). 원인 후보 중 하나가 신호 도착 시각이 어긋나는 **타이밍 경로 오류**다.

## 동작·원리

### 1. 트랜지스터는 전압으로 여닫는 스위치다

```text
     입력 0 (낮은 전압)          입력 1 (높은 전압)
   VDD ─┐                      VDD ─┐
        ⊸ 위쪽 스위치 ON              ⊸ 위쪽 스위치 OFF
        ├── 출력 = 1                 ├── 출력 = 0
        ⊸ 아래쪽 스위치 OFF           ⊸ 아래쪽 스위치 ON
   GND ─┘                      GND ─┘
   CMOS 인버터(NOT): 입력이 위·아래 스위치를 반대로 연다 (개념도)
```

- *트랜지스터*: 한 단자의 전압으로 다른 두 단자 사이를 잇거나 끊는 소자. 여기서는 스위치로만 본다.
- *CMOS*: 위(전원 쪽)와 아래(접지 쪽)에 성질이 반대인 스위치를 짝으로 두는 회로 방식. Ginosar 2011은 동기화기 MTBF 계산 예로 28nm 고성능 CMOS 공정의 ASIC을 든다.
- *논리 레벨*: "1"과 "0"은 정확한 전압 값이 아니라 전압 구간이다. 두 구간 사이의 중간 전압은 0으로도 1로도 확실히 읽히지 않는다. 플립플롭이 이렇게 전이 중인 입력을 에지에서 잡으면 한동안 0과 1 사이에 머무를 수 있다(메타안정, [08](../08-sequential-logic-clock/2-summary.md)).
- 원고 [foundations/hardware-basics](../../foundations/hardware-basics/README.md) §1에 전압·트랜지스터 기초가 있다.
  - 참고: 원고 §1은 베이스·콜렉터·이미터(바이폴라 트랜지스터)와 0V/5V로 설명한다. 이는 옛 TTL식 설명이고, 오늘날 CPU 논리는 CMOS(MOSFET) 공정으로 만든다(예: Ginosar 2011의 28nm CMOS ASIC). 원리(전압으로 여닫는 스위치)는 같다. 구체 전압 값은 공정마다 다르다.

### 2. 게이트와 불리언 대수 — NAND 하나면 다 된다

```text
  a b │ NOT a  AND  OR  XOR  NAND
  0 0 │   1     0    0    0    1
  0 1 │   1     0    1    1    1
  1 0 │   0     0    1    1    1
  1 1 │   0     1    1    0    0

  NOT a   = NAND(a, a)
  AND     = NOT(NAND(a, b))
  OR      = NAND(NOT a, NOT b)          ← 드모르간
  XOR     = NAND(NAND(a, n), NAND(b, n)),  n = NAND(a, b)   (게이트 4개, 깊이 3)
```

- *논리 게이트*: 비트 입력을 받아 불리언 함수 값을 내는 회로. 진리표가 정의다 — [math/01-propositional-logic](../../math/01-propositional-logic/2-summary.md).
- *함수적 완전성*: NAND만으로 모든 불리언 함수를 만들 수 있다. 실험 1이 NAND만으로 만든 NOT·AND·OR·XOR의 진리표를 확인했다.
- *조합 논리*: 출력이 지금 입력만으로 정해지는 회로. 기억이 없다. 가산기·ALU가 여기 속한다(원고 §3·§4, CS:APP 4.2.2).
- *게이트 지연*: 입력이 바뀐 뒤 출력이 따라 바뀌기까지의 시간. 이 노트의 시뮬레이션은 모든 게이트 지연을 1 단위로 놓는다(단순화 모델).

### 3. 반가산기 → 전가산기

```text
  반가산기 (1비트 + 1비트)            전가산기 (a + b + cin)
   a ─┬─[XOR]── s                   a ─┬─[XOR]─ p ─┬─[XOR]──────── s
   b ─┼─[AND]── c                   b ─┼─[AND]─ g  │
      │                          cin ──┼───────────┴─[AND]─ pc
                                       │                     │
                                       g ─────────[OR]───────┴─ cout
   s = a XOR b, c = a AND b          s = a ⊕ b ⊕ cin,  cout = ab + (a⊕b)·cin
```

- *반가산기*: 두 비트를 더해 합 s와 캐리 c를 낸다. XOR 하나와 AND 하나(원고 §4).
- *전가산기*: 아래에서 올라온 캐리 `cin`까지 세 비트를 더한다. 반가산기 2개 + OR 1개.
- 실험 2의 진리표: `1 + 1 + 1 = 11`(cout 1, 합 1), `0 + 1 + 1 = 10`.

### 4. 리플 캐리 가산기 — 캐리가 한 칸씩 번진다

```text
  a3 b3      a2 b2      a1 b1      a0 b0
   │  │       │  │       │  │       │  │
  ┌┴──┴┐ c3  ┌┴──┴┐ c2  ┌┴──┴┐ c1  ┌┴──┴┐
  │ FA │<────│ FA │<────│ FA │<────│ FA │<── cin
  └─┬──┘     └─┬──┘     └─┬──┘     └─┬──┘
 cout s3       s2         s1         s0
  캐리 하나가 지나갈 때마다 AND + OR = 게이트 2단씩 늦어진다
```

- *리플 캐리 가산기(ripple-carry adder)*: 전가산기 n개를 캐리 선으로 줄줄이 이은 것. 게이트 수도, 최장 지연도 n에 비례한다.
- 실험 3(구조적 최장 경로): 16비트 33단, 32비트 65단, 64비트 129단 = 2n + 1.
- 실제 걸리는 시간은 입력에 따라 다르다. 캐리가 멀리 번지는 입력이 가장 오래 걸린다(실험 4).

```text
  16비트 리플, 0+0 에서 새 입력으로 바꾼 뒤 출력이 마지막으로 바뀐 시각(게이트 지연 단위)
  0x0001 + 0x0001 →  3          0x00FF + 0x0001 → 17
  0x7FFF + 0x0001 → 31          0xFFFF + 0x0001 → 32       0x5555 + 0xAAAA → 2

  0xFFFF + 1 의 합 비트(cout | s15…s0)가 시간에 따라 바뀌는 모습 (실험 5)
  t=2 : 0 1111111111111110      ← 먼저 a XOR b 가 나온다
  t=9 : 0 1111111111100000      ← 캐리가 2단마다 한 비트씩 지우며 올라간다
  t=25: 0 1110000000000000
  t=31: 0 0000000000000000
  t=32: 1 0000000000000000      ← cout 이 마지막
```

- 0x5555 + 0xAAAA는 모든 비트에서 a⊕b = 1이지만 a·b = 0이라 캐리가 생기지 않는다. 그래서 빨리 끝난다.
- 구조적 최장 경로(33)와 0xFFFF+1의 32가 1 다른 것은, 이 입력의 캐리가 a0·b0의 AND(1단)에서 시작하고 최장 경로는 a0⊕b0을 거치는 XOR→AND→OR(3단)에서 시작하기 때문이다.

### 5. 캐리 룩어헤드 — 캐리를 미리 계산한다

```text
  비트 i 에서                 두 구간 (높은 쪽 H, 낮은 쪽 L)을 합치면
  g_i = a_i AND b_i   생성      G = G_H OR (P_H AND G_L)
  p_i = a_i XOR b_i   전달      P = P_H AND P_L
  "이 구간이 캐리를 만든다(G)", "들어온 캐리를 통과시킨다(P)"

  Kogge–Stone: 구간 길이를 1 → 2 → 4 → 8 … 로 log2(n) 단계에 걸쳐 합친다
  비트: 7 6 5 4 3 2 1 0
  단계1  [76][65][54][43][32][21][10]
  단계2  [7..4][6..3][5..2][4..1][3..0][2..0]…
  단계3  [7..0][6..0]…                   → 모든 비트의 캐리가 log2(n) 단계 뒤에 나온다
```

- *캐리 룩어헤드 가산기(CLA)*: 각 비트의 캐리를 아래 비트의 g·p로 직접 계산해, 캐리가 한 칸씩 번지기를 기다리지 않는 가산기.
- *병렬 프리픽스(parallel prefix)*: (G, P) 합치기 연산이 결합 법칙을 만족하므로, 누적합처럼 log2(n) 단계에 모든 접두 구간의 결과를 얻는다. Kogge–Stone은 그 한 형태다(Wikipedia "Kogge–Stone adder"·"Carry-lookahead adder", 2차 정리). 누적합 알고리즘은 [algorithm/10-prefix-sum](../../algorithm/10-prefix-sum/2-summary.md).

```text
  실험 3: n비트 가산기의 게이트 수 / 최장 경로 (게이트 단계)
     n   ripple 게이트  깊이   kogge-stone 게이트  깊이
     4        20         9          29            7
     8        40        17          77            9
    16        80        33         197           11
    32       160        65         485           13
    64       320       129        1157           15
```

- 깊이: 리플은 2n+1(O(n)), Kogge–Stone은 2·log2(n)+3(O(log n)).
- 대가: 게이트 수가 n·log n에 비례해 늘어난다. 64비트에서 리플의 약 3.6배. 넓이·전력과 속도를 맞바꾼다. 실제 CPU가 어떤 가산기 구조를 쓰는지는 공개 자료로 확인하지 못했다 [?].
- 실험 4에서 같은 0xFFFF + 1이 리플 32, Kogge–Stone 10 단위에 끝났다.

### 6. ALU — 같은 가산기로 뺄셈과 플래그

```text
  a − b = a + (NOT b) + 1        (2의 보수, 01번)
          └ b 를 XOR 1 로 뒤집고, cin 에 1 을 넣는다

  플래그 (n비트 결과에서)
  C (carry)    = 최상위 비트에서 나간 캐리            → 무부호 오버플로
  V (overflow) = 최상위로 들어간 캐리 XOR 나간 캐리   → 부호 있는 오버플로
  Z, N         = 결과가 0 인가, 최상위 비트
  뺄셈 a − b 에서 가산기 캐리 출력 1 = "빌림 없음"
  x86 sub·cmp 의 CF 는 빌림(= 가산기 캐리의 반대): 3 − 5 → 캐리 출력 0, CF 1
```

- *ALU(arithmetic logic unit)*: 덧셈·뺄셈·AND·OR 등을 고르는 신호에 따라 하나의 결과를 내는 조합 회로(원고 §3).
- 실험 7: 같은 16비트 가산기로 `3 − 5` → `0xFFFE`(short로 −2), `0x8000 − 1` → `0x7FFF`.
- 실험 6: 무작위 10만 쌍에서 `V = c_in(MSB) XOR c_out`이 Java `(short)` 합의 오버플로 판정과 10만 번 모두 일치했다.
- 실험 8(x86-64, gcc 13.3 `-O2`): 부호 있는·없는 `__builtin_add_overflow`가 **똑같은 `add`** 명령을 쓰고, 뒤에 `seto`(V)냐 `setb`(C)냐만 달랐다. 비교 `a < b`도 같은 `cmp` 뒤에 `setl`(부호 있음) / `setb`(무부호)였다. 하드웨어 가산기는 하나, 해석은 둘이다([01](../01-number-systems-twos-complement/2-summary.md)).

### 7. 지연이 클록을 정한다

```text
  레지스터 ──clk→Q──> [ 조합 논리 (가산기 등) ] ──> 레지스터
           t_clk→Q        t_조합(최장 경로)       t_setup
  클록 주기 T 는 적어도  t_clk→Q + t_조합(최대) + t_setup  보다 길어야 한다
  짧으면 레지스터가 아직 계산 중인 값을 잡는다 → 타이밍 위반
```

- *셋업 시간(setup time)*: 클록 에지 전에 입력이 안정돼 있어야 하는 최소 시간. Ginosar 2011은 동기화 회로의 해소 시간을 `S = T_C − t_pCQ − t_SETUP − t_PD(wire)`로 쓴다. 같은 구조의 예산이다.
- 그래서 동기식 회로는 **최악 경로**에 클록을 맞춘다. 실험 4처럼 입력에 따라 빨리 끝나는 경우가 있어도 클록은 기다린다(해석: CPU의 덧셈 결과가 값에 따라 늦어지지 않는 이유).
- 클록 주기를 최악 경로보다 짧게 하면 무엇이 잡히는지는 [08](../08-sequential-logic-clock/2-summary.md)의 카운터 실험이 보여 준다.
- CS:APP 4.2(Logic Design and HCL)·4.2.5(Memory and Clocking)가 이 구조를 다룬다(절 제목은 머리말 목차로 확인, 본문은 이 작업에서 열지 못함).

### 실험: 게이트 넷리스트로 가산기를 만들고 캐리 지연을 잰다

환경: i7-13700HX, Linux 7.0.0-34, Docker `eclipse-temurin:21-jdk`(OpenJDK 21.0.12) `--cpus=2 --network none`. 호스트 gcc 13.3.0, GNU objdump. 2026-10-07. **실제 회로의 시간이 아니라 "게이트 지연 = 1 단위" 모델의 시뮬레이션**이다. 결과는 결정적이다.

```java
// Adder07.java 핵심 — 넷리스트와 단위 지연 시뮬레이션
enum T { IN, CONST0, NOT, AND, OR, XOR, NAND }
int[] step(int[] v) {                       // 매 단위 시간: 모든 게이트가 직전 값으로 다시 계산
    int[] nv = v.clone();
    for (int i = 0; i < type.size(); i++) nv[i] = eval(type.get(i), in.get(i), v);
    return nv;
}
// 리플: 비트마다 p=XOR(a,b), g=AND(a,b), s=XOR(p,c), c'=OR(g, AND(p,c))
// Kogge–Stone: G[i] = OR(G[i], AND(P[i], G[i-d])), P[i] = AND(P[i], P[i-d]),  d = 1,2,4,…
```

```c
/* flags07.c — 같은 덧셈, 다른 플래그 */
bool add_s(int32_t a, int32_t b, int32_t *r)   { return __builtin_add_overflow(a, b, r); }
bool add_u(uint32_t a, uint32_t b, uint32_t *r) { return __builtin_add_overflow(a, b, r); }
```

```text
== 6. 무작위 100000쌍 검증 (16비트) ==
  ripple·kogge-stone 오답 0건, V=1(부호 있는 16비트 오버플로) 24986건, Java (short) 합 판정과 일치 100000/100000
== 8. gcc -O2 / objdump -d ==
  <add_s>: add %esi,%edi ; mov %edi,(%rdx) ; seto %al ; ret
  <add_u>: add %esi,%edi ; mov %edi,(%rdx) ; setb %al ; ret
  <lt_s>:  xor %eax,%eax ; cmp %esi,%edi ; setl %al ; ret
  <lt_u>:  xor %eax,%eax ; cmp %esi,%edi ; setb %al ; ret
  same bits 0xFFFFFFFF + 1: signed overflow=0 (=0), unsigned carry=1 (=0)
```

관찰과 해석
- 3·4: 리플의 지연은 비트 수에 비례해 늘고, 룩어헤드는 로그로 는다. 대신 룩어헤드는 게이트가 많다.
- 6: 무작위 입력의 약 25%(24,986/100,000)에서 부호 있는 16비트 오버플로가 났다. 두 수의 부호가 같고(확률 1/2) 그중 합이 범위를 넘는 경우(그 절반쯤)라서 1/4 근처가 나온 것으로 해석한다.
- 8: 같은 비트 `0xFFFFFFFF + 1`이 부호 있는 해석으로는 `−1 + 1 = 0`(오버플로 아님), 무부호로는 캐리 1이다.

## 쓰이는 자료구조·알고리즘

- **불리언 대수·드모르간**: 게이트 변환(NAND로 OR 만들기)은 드모르간 법칙이다 — [math/01-propositional-logic](../../math/01-propositional-logic/2-summary.md).
- **리플 캐리 = 자릿수 덧셈 알고리즘**: 아래 자리부터 캐리를 넘긴다. 정확성은 "i번째 단계 뒤 하위 i비트가 맞다"는 불변식으로 귀납 증명한다 — [math/02-induction-and-invariants](../../math/02-induction-and-invariants/2-summary.md).
  - 소프트웨어 판: OpenJDK 21 `BigInteger.add(int[], int[])`는 32비트 조각을 아래부터 더하며 `sum >>> 32`를 다음 조각으로 넘긴다(`src/java.base/share/classes/java/math/BigInteger.java`). 큰 수 곱셈의 자리올림은 [algorithm/24-divide-conquer](../../algorithm/24-divide-conquer/2-summary.md).
- **병렬 프리픽스(룩어헤드)**: 결합적인 (G, P) 연산의 누적을 log 단계로 — [algorithm/10-prefix-sum](../../algorithm/10-prefix-sum/2-summary.md).
- **비트 연산**: XOR = 캐리 없는 덧셈, AND = 캐리 생성. `a + b = (a ^ b) + ((a & b) << 1)` — [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 증상 → 회로 수준 원인

| 증상 | 회로 수준에서 무슨 일 | 확인 |
|---|---|---|
| 큰 양수 둘을 더했더니 음수 | V 플래그를 아무도 안 봤다(2의 보수 랩어라운드) | `Math.addExact`, C `__builtin_add_overflow`([02](../02-integer-overflow-and-truncation/2-summary.md)) |
| 같은 비교가 부호 있게/없게 다르게 동작 | 같은 `cmp` 뒤 `jl`·`setl`(부호) vs `jb`·`setb`(무부호) | `objdump -d`로 조건 명령 확인(실험 8) |
| 한 서버·한 코어에서만, 특정 입력에서만 계산이 틀림 | 하드웨어 결함(타이밍 경로 등)으로 인한 조용한 데이터 손상 | 코어 고정(`taskset -c`) 재실행, 다른 머신 결과와 비교 |
| 오버클럭·저전압 설정 뒤 간헐적 크래시 | 클록 주기가 최악 경로보다 짧아짐(타이밍 위반) | 기본 설정으로 되돌려 재현 여부 |

### 2. 어셈블리로 플래그 사용을 본다

```bash
gcc -O2 -c flags07.c && objdump -d --no-show-raw-insn flags07.o
# add 뒤 seto(부호 있는 오버플로) / setb(무부호 캐리), cmp 뒤 setl / setb
```

- Java에서는 `Math.addExact`가 오버플로 때 `ArithmeticException`을 던진다. JIT가 이를 플래그 검사 분기로 바꾸는지는 09·02에서 다룬다.

### 3. 코드에서 지킬 것

- 금액·카운터처럼 넘치면 안 되는 덧셈은 넘침을 검사하는 연산(`Math.addExact`, `__builtin_add_overflow`)을 쓴다. 하드웨어는 플래그를 매번 계산하지만, 언어가 그것을 묻지 않으면 사라진다.
- 같은 비트를 부호 있게·없게 섞어 비교하지 않는다(무부호 비교는 `Integer.compareUnsigned`).
- 계산 결과의 무결성이 중요한 배치(정산·압축·암호)에는 하드웨어도 틀릴 수 있다는 전제로 검증(체크섬, 다른 노드 재계산)을 둔다 — [os/33-data-integrity-checksums](../../os/33-data-integrity-checksums/2-summary.md).

## 장애 시나리오와 대처

### 1. 캐리 전파 지연이 클록 주기를 넘음 → 타이밍 위반 (⚠ 커리큘럼)

- **현상**: 클록을 올리거나 전압을 낮춘 장비에서 간헐적으로 계산이 틀리거나 프로세스가 죽는다. 같은 입력을 다시 돌리면 맞기도 한다.
- **보이는 형태**: 오류 메시지가 없거나, 엉뚱한 곳의 `SIGSEGV`·체크섬 불일치로 나타난다.
- **원인**: 레지스터가 다음 에지에서 조합 회로(가산기)의 최종값을 보장받지 못한다. 이전 값·중간값을 잡거나, 에지 근처에서 입력이 바뀌면 메타안정에 빠질 수 있다([08](../08-sequential-logic-clock/2-summary.md)). 캐리가 멀리 번지는 입력(0x7F…F + 1)에서만 늦게 끝나므로 데이터에 따라 증상이 난다. [08](../08-sequential-logic-clock/2-summary.md) 실험 3에서 주기 16 단위까지는 오답 0, 12 단위에서 256클록 중 10번, 8 단위에서 46번, 4 단위에서 172번 틀렸다(시뮬레이션).
- **대처**: 제조사가 검증한 클록·전압으로 되돌린다. 하드웨어 설계에서는 정적 타이밍 분석으로 최악 경로가 주기 안에 드는지 확인하고, 안 들면 룩어헤드 구조나 파이프라인 단계 분할로 경로를 줄인다(해석).

### 2. 조용한 데이터 손상 — 특정 코어가 특정 입력에서만 틀림

- **현상**: Spark 압축 해제 파이프라인에서 파일 크기 계산이 가끔 0을 돌려줘 파일이 누락됐다. 결국 "압축 해제 후 데이터 손실"로 보고됐다(Dixit 외, Meta 2021).
- **보이는 형태**: 시스템 이벤트 로그·커널 로그가 깨끗했다. 다중 스레드에서는 산발적이었고, 단일 스레드로 줄이자 한 코어(Core 59)에서 특정 값에 대해 일관되게 틀렸다. `Int(1.1^53)`이 0, `Int(1.1^52)`는 142로 맞았다(원문).
- **원인**: 원문 §3은 CPU 결함의 범주로 장치 오류(설계상 코너 케이스, **신호 도착 시각 불확실성으로 인한 타이밍 경로 오류**, 제조 편차), 초기 고장, 사용에 따른 열화, 수명 말기 마모를 든다. 이 사례 결함의 정확한 회로 위치는 원문 범위 밖이다(해석: 이 노트의 "최악 경로가 주기를 넘는" 모델과 같은 범주).
  - Google의 Hochschild 외(HotOS 2021)는 이런 코어를 "mercurial core"라 부르고, 수천 대 서버당 몇 개 수준으로 관측된다고 적는다.
- **대처**: 코어 고정 재현(`taskset -c N`)으로 코어를 특정하고 격리한다. 중요한 계산은 결과 검증(체크섬, 중복 계산 비교)을 둔다. Dixit 외 §7은 참값을 아는 계산을 돌려 비교하는 탐지 방법 셋(유휴 기계 활용, 주기적 점검, 운영 중 경량 테스트)을 든다.

### 3. 오버플로 플래그를 버림 → 음수 금액

- **현상**: 합계가 21억을 넘는 순간 정산 금액이 음수가 된다.
- **보이는 형태**: 예외 없음. 로그에 `-2147483648` 근처 값.
- **원인**: 가산기는 V 플래그를 계산했지만 Java `int +`는 그 플래그를 보지 않고 하위 32비트만 남긴다(JLS §15.18.2). C에서 하위 비트만 남는다고 보장되는 것은 무부호 `+`이고(C11 §6.2.5¶9), 부호 있는 `+`가 넘치면 정의되지 않은 동작이다(C11 §6.5¶5). 실험 8의 `INT32_MAX + 1 → -2147483648`은 `__builtin_add_overflow`가 돌려준 결과다.
- **대처**: `Math.addExact`·`long`·`BigDecimal`. 자세한 것은 [02-integer-overflow-and-truncation](../02-integer-overflow-and-truncation/2-summary.md).

### 4. 부호 있는/없는 비교를 섞음 → 경계 검사 통과

- **현상**: `int len`, `int max`일 때 길이 검사 `if (len < max)`를 음수 길이 −1이 통과한다. 뒤의 `memcpy(dst, src, len)`에서 `len`이 `size_t`로 바뀌어 거대 길이가 된다. 반대로 `max`가 `size_t`면 −1이 `SIZE_MAX`가 되어 같은 검사가 엉뚱하게 거짓이 된다.
- **보이는 형태**: 검사 쪽은 `cmp` 뒤 `jl`/`setl`(부호 있음)인데, 같은 값을 받는 `memcpy`의 길이 인자는 무부호다. 섞인 비교(`int` vs `size_t`)라면 `cmp` 뒤가 `jb`/`setb`(무부호)다.
- **원인**: 같은 `cmp`(= 뺄셈 가산기) 결과를 S·V(부호)로 읽느냐 C(무부호 — x86에서는 빌림을 뜻하는 CF)로 읽느냐의 차이다. 검사와 사용이 서로 다른 해석을 썼다. 섞인 비교에서는 C의 통상 산술 변환이 `int`를 무부호로 바꾼다.
- **대처**: 타입을 맞추고 `-Wsign-compare` 경고를 켠다. 기초는 [01](../01-number-systems-twos-complement/2-summary.md) 장애 1.

## 핵심 문장

- 트랜지스터는 전압으로 여닫는 스위치이고, 스위치를 조합하면 게이트가 된다. NAND 하나로 모든 불리언 함수를 만들 수 있다.
- 전가산기는 반가산기 2개와 OR 1개다. n개를 줄줄이 이은 리플 캐리 가산기의 최장 지연은 n에 비례한다(16비트 33단).
- 캐리 룩어헤드는 (생성 G, 전달 P)를 병렬 프리픽스로 합쳐 지연을 log n으로 줄이고, 그 대가로 게이트를 더 쓴다.
- 뺄셈은 b를 뒤집고 캐리 입력 1을 넣은 덧셈이다. 같은 가산기에서 C 플래그는 무부호, V 플래그는 부호 있는 오버플로를 알린다.
- 클록 주기는 조합 회로의 최악 경로보다 길어야 한다. 짧으면 레지스터가 계산 중인 값을 잡고, 증상은 데이터에 따라 간헐적으로 나온다.

## 관련 주제·근거

- 선행: [01-number-systems-twos-complement](../01-number-systems-twos-complement/2-summary.md) · [math/01-propositional-logic](../../math/01-propositional-logic/2-summary.md)
- 원고: [foundations/hardware-basics](../../foundations/hardware-basics/README.md) §1(전압·트랜지스터), §2(논리 게이트), §3(CPU 내부·조합 논리), §4(반가산기·전가산기)
- 후속(이 영역): [08-sequential-logic-clock](../08-sequential-logic-clock/2-summary.md) · [09-isa-and-machine-code](../09-isa-and-machine-code/2-summary.md) · [02-integer-overflow-and-truncation](../02-integer-overflow-and-truncation/2-summary.md)
- 연결
  - [algorithm/10-prefix-sum](../../algorithm/10-prefix-sum/2-summary.md) · [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md) · [algorithm/24-divide-conquer](../../algorithm/24-divide-conquer/2-summary.md)
  - [math/02-induction-and-invariants](../../math/02-induction-and-invariants/2-summary.md)
  - [os/33-data-integrity-checksums](../../os/33-data-integrity-checksums/2-summary.md) — 하드웨어가 틀릴 때의 검증
- 근거
  - CS:APP 3판 — 2.1.6 Introduction to Boolean Algebra, 4.2 Logic Design and the Hardware Control Language HCL(4.2.1 Logic Gates, 4.2.2 Combinational Circuits, 4.2.3 Word-Level Combinational Circuits, 4.2.5 Memory and Clocking). 절 번호는 저자 사이트 머리말 PDF 목차로 확인 <https://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf>. 본문은 이 작업에서 열지 못했다.
  - Patterson & Hennessy 『Computer Organization and Design』 부록 A(논리 설계 기초·캐리 룩어헤드) [?] — 열 수 있는 목차가 없어 장 번호를 확인하지 못했다.
  - R. Ginosar, "Metastability and Synchronizers: A Tutorial", IEEE Design & Test of Computers, Sept/Oct 2011 — CMOS 공정 예, 타이밍 예산 식 <http://webee.technion.ac.il/~ran/papers/Metastability-and-Synchronizers.IEEEDToct2011.pdf>
  - H. D. Dixit 외, "Silent Data Corruptions at Scale", arXiv:2102.11245, 2021 — §3.1 Device Errors(타이밍 경로 오류)·§3.3 Degradation, §4·§5 Spark 사례(Core 59, `Int(1.1^53)` = 0), §7 탐지 방법 <https://arxiv.org/abs/2102.11245>
  - P. H. Hochschild 외, "Cores that don't count", HotOS 2021 — mercurial core, 수천 대당 몇 개 <https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s01-hochschild.pdf>
  - Wikipedia "Carry-lookahead adder"·"Kogge–Stone adder"(2차 정리, 생성·전달 개념과 log2 n 단계) — 위키 원문 <https://en.wikipedia.org/wiki/Kogge%E2%80%93Stone_adder>
  - OpenJDK 21 `java/math/BigInteger.java` `add(int[] x, int[] y)` <https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/math/BigInteger.java>
  - ISO/IEC 9899:2011 위원회 초안 N1570 — §6.2.5¶9(무부호 연산은 넘치지 않고 나머지로 줄어든다), §6.5¶5(범위를 넘는 결과는 정의되지 않은 동작) <https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf> · JLS SE21 §15.18.2(정수 덧셈이 넘치면 하위 비트) <https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.18.2>
- 실험 목록
  - `Adder07.java` — 1. NAND만으로 NOT·AND·OR·XOR 진리표, 2. 전가산기 진리표, 3. 리플·Kogge–Stone의 게이트 수·최장 경로(4~64비트), 4. 16비트 입력별 출력 안정 시각, 5. 0xFFFF+1 시각별 합 비트, 6. 무작위 10만 쌍 정확성·V 플래그 대 Java `(short)` 판정, 7. 반전+캐리 입력 뺄셈. 단위 지연 모델. OpenJDK 21.0.12, Docker `--cpus=2 --network none`.
  - `flags07.c` — `__builtin_add_overflow` 부호 있음/없음, `<` 부호 있음/없음. gcc 13.3.0 `-O2`, `objdump -d`. 호스트 i7-13700HX.
  - `cf07.c`(2차 검토 보강) — `a − b`의 가산기 캐리 출력(`a + ~b + 1`) 대 x86 `cmp` 뒤 `setc`: `3 − 5`는 캐리 출력 0·CF 1, `5 − 3`·`7 − 7`은 캐리 출력 1·CF 0. gcc 13.3.0 `-O2`, 호스트 i7-13700HX.
  - 파일 위치: scratchpad `arch/05/`(Adder07.java, flags07.c, out-adder07.txt, out-flags07.txt). · `arch/adj-04/`(cf07.c, out-cf07.txt)
