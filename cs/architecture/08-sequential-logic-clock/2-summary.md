# architecture/08-sequential-logic-clock — 래치·플립플롭·클록·레지스터·상태 기계, 메타안정성 — 정리 (힌트)

## 해결하는 문제

[07](../07-logic-gates-to-adder/2-summary.md)의 가산기는 입력이 사라지면 결과도 사라진다. 기억이 없다.\
CPU가 "다음 명령"으로 넘어가려면 두 가지가 더 필요하다.

- 값을 **붙잡아 두는** 회로(기억).
- 모든 회로가 **같은 순간에** 다음 단계로 넘어가게 하는 신호(클록).

쉬운 예: 단체 사진.
- 사람들은 계속 움직인다(조합 회로의 출력이 계속 바뀐다).
- 셔터가 눌리는 순간의 모습만 사진에 남는다(클록 에지에 레지스터가 값을 잡는다).
- 셔터 순간에 누가 반쯤 움직이고 있으면 흐릿하게 찍힌다(메타안정).

똑같은 구조다.\
레지스터는 클록 에지에만 입력을 찍어 두고, 그 사이에 조합 회로가 다음 값을 계산한다.

실무 예:
- CPU의 레지스터·프로그램 카운터·파이프라인 단계 사이 버퍼가 모두 이 구조다.
- 서로 다른 클록으로 도는 두 회로(예: 외부 버튼, 다른 칩)가 신호를 주고받으면 드물게 간헐 오동작이 난다. 재현이 거의 안 된다.
- 코드의 주문 상태·TCP 연결 상태도 같은 "상태 + 다음 상태 함수" 구조다.

## 동작·원리

### 1. 되먹임으로 기억한다 — SR 래치

```text
   R ──┐                    S R │ Q   Q'
       NOR ──┬── Q          0 0 │ 유지 (이전 값)
   ┌───┘     │              1 0 │ 1   0   셋
   │   ┌─────┘              0 1 │ 0   1   리셋
   │   │                    1 1 │ 0   0   금지 (Q 와 Q' 가 같아짐)
   │   └─────┐
   └───┐     │
   S ──NOR ──┴── Q'
   두 NOR 의 출력이 서로의 입력으로 돌아간다
```

- *순차 논리(sequential logic)*: 출력이 지금 입력과 **과거 상태**로 정해지는 회로(원고 §5).
- *SR 래치*: 셋(S)·리셋(R) 입력과 되먹임으로 1비트를 기억하는 회로.
- 원고 [foundations/hardware-basics](../../foundations/hardware-basics/README.md) §5가 NAND판 SR 래치와 "출력이 저장된다"를 설명한다.

실험 1(단위 지연 시뮬레이션, 각 구간 8단위):

```text
  유지            S=0 R=0 → Q=0 Q'=1   (t1..t8 QQ': 01 01 01 01 01 01 01 01)
  S=1(셋)         S=1 R=0 → Q=1 Q'=0   (t1..t8 QQ': 00 10 10 10 …)
  유지            S=0 R=0 → Q=1 Q'=0   ← 입력이 사라져도 1을 기억
  S=R=1(금지)     S=1 R=1 → Q=0 Q'=0
  S,R 동시에 0으로  S=0 R=0 → (t1..t8 QQ': 11 00 11 00 11 00 11 00)   ← 끝없이 흔들림
  S 먼저, R 1단위 뒤 →        (t1..t8 QQ': 01 01 01 01 …)             ← 늦게 내린 쪽이 이김
```

- 금지 상태에서 두 입력을 **정확히 동시에** 내리면, 이 이상화 모델에서는 두 게이트가 서로를 영원히 뒤집는다. 조금이라도 어긋나면 한쪽으로 정해진다.
- 실제 회로에서는 이것이 아날로그 현상인 *메타안정성*으로 나타난다(5절). 모델의 무한 진동은 그 디지털 그림자일 뿐이다(해석). Ginosar 2011은 실제 메타안정 출력이 VDD/2에서 흔들리는 모습으로 보이는 경우는 드물고, 대개 0이나 1로 나오되 **늦게** 정해진다고 적는다.

### 2. 레벨 래치 vs 에지 플립플롭

```text
  D 래치: CLK=1 동안 Q 가 D 를 따라간다(투명), CLK=0 이면 붙잡는다
  D 플립플롭(마스터–슬레이브): 래치 두 개를 반대 클록으로 이어,
                             상승 에지 순간의 D 만 Q 로 넘어간다

  실험 2 (같은 D·CLK 파형, ▔=1 ▁=0)
  t     0         10        20        30        40        50        60        70
  CLK   ▁▁▁▁▁▁▁▁▁▁▔▔▔▔▔▔▔▔▔▔▁▁▁▁▁▁▁▁▁▁▔▔▔▔▔▔▔▔▔▔▁▁▁▁▁▁▁▁▁▁▔▔▔▔▔▔▔▔▔▔▁▁▁▁▁▁▁▁▁▁▔▔▔▔▔▔▔▔▔▔
  D     ▁▁▁▔▔▔▔▔▔▔▔▔▔▔▁▁▁▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
  Q래치 ▁▁▁▁▁▁▁▁▁▁▁▁▔▔▔▔▁▁▁▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔
  Q FF  ▁▁▁▁▁▁▁▁▁▁▁▁▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▔▔▔▔▔▔▔▔
```

- *D 래치(level-sensitive)*: 클록이 1인 동안 내내 입력을 통과시킨다. t=14~16의 D 글리치(짧은 0)가 Q래치에 그대로 나왔다. t=33에 D가 내려가자 클록이 1인 구간이라 Q래치도 따라 내려갔다.
- *D 플립플롭(edge-triggered)*: 클록 상승 에지의 D만 잡는다. 같은 글리치와 t=33 변화를 무시하고, 다음 에지(t=50)의 D=0, t=70의 D=1만 반영했다. 각 변화는 게이트 지연 2단위 뒤에 보인다.
- *레지스터*: 같은 클록을 받는 D 플립플롭 n개. n비트를 한 번에 잡는다(원고 §5·§7).
- 참고: 원고 §6의 "D 플립플롭 진리표"(CLK=1이면 Q=D, CLK=0이면 유지)는 레벨 감지 **D 래치**의 동작이다. 원고도 "상승 에지에 맞춰" 실행한다고 쓰는데, 에지에서만 잡는 것이 플립플롭이고 그 차이가 위 실험의 글리치 처리에서 드러난다.

### 3. 클록 — 주기, 주파수, 타이밍 예산

```text
  ┌──┐  ┌──┐  ┌──┐     주기 T = 1 / f      5 GHz → 0.2 ns,  800 MHz → 1.25 ns
  ┘  └──┘  └──┘  └──   상승 에지마다 모든 레지스터가 동시에 값을 잡는다

  레지스터 ─clk→Q─> [ 조합 논리 ] ─> 레지스터
  T ≥ t_clk→Q + t_조합(최장) + t_setup          (07 §7)
```

- *클록*: 일정한 주기로 0과 1을 오가는 신호. *주파수*는 1초에 반복하는 주기 수다.
  - 참고: 원고 §6은 주파수를 "전자가 1초 동안 왕복한 횟수"로 설명한다. 클록 주파수는 클록 **신호**가 1초에 반복하는 횟수다. 주기 = 1/주파수라는 관계는 원고와 같다.
- *셋업 시간*·*홀드 시간*: 에지 전·후로 입력이 안정돼 있어야 하는 최소 시간. 이 창 안에서 입력이 바뀌면 메타안정이 될 수 있다(Ginosar 2011의 T_W 창).
- 이 호스트(i7-13700HX, `intel_pstate`·`powersave`)의 클록은 고정이 아니다. `lscpu`가 최대 5000 MHz, 최소 800 MHz를 보였고, 한가할 때 `/proc/cpuinfo`의 앞 논리 CPU 4개가 약 800 MHz였다(실험 5). 주파수를 낮추면 주기가 길어진다. 다만 성능 상태(P-state)는 주파수와 전압을 함께 바꾸고(커널 문서 "CPU Performance Scaling"), 전압이 낮으면 게이트도 느려진다. 그래서 각 동작점(주파수·전압 짝)이 그 전압의 지연까지 포함해 타이밍을 만족하도록 정해져 있어야 맞게 돈다(해석).

실험 3 — 8비트 카운터(레지스터 ← 리플 가산기 +1)에서 클록 주기를 줄였다:

```text
  주기 40·20·17·16 단위: 256클록 중 틀리게 잡은 횟수 0
  주기 12 단위: 10번   처음 틀린 클록 #62: 62(0x3E) 다음에 127(0x7F)을 잡음
  주기  8 단위: 46번   처음 틀린 클록 #14: 14(0x0E) 다음에 31(0x1F)을 잡음
  주기  4 단위: 172번  처음 틀린 클록 #2:  2(0x02) 다음에 7(0x07)을 잡음

  61→62 로 입력이 바뀐 뒤 가산기 합 출력의 시각별 값 (같은 모델의 Python 복제로 추적)
  t: 1   2   3   4   5   6   7   8   9  10  11  12  13  14 …
     62  61  61  59  59  55  55  47  47  31  31 127 127  63   ← t=12 에 잡으면 127
```

- 이 회로의 최악 경로는 약 16단위다. 주기가 그보다 짧으면 레지스터가 **중간값**을 잡는다.
- 중간값은 무작위가 아니다. 입력이 바뀔 때 옛 캐리가 사라지기 전에 새 전달 비트가 켜져, 짧은 캐리 펄스(*글리치*)가 위로 번진다. 그 펄스를 잡은 순간이 127이다.
  - *글리치(glitch)·해저드*: 조합 회로 출력이 최종값에 닿기 전에 잠깐 다른 값이 되는 것. 클록이 최악 경로를 기다리면 문제가 안 되지만, 래치(레벨 감지)나 비동기 경로에서는 그대로 전파된다(실험 2).

### 4. 유한 상태 기계 = 상태 레지스터 + 다음 상태 함수

```text
            입력 ──┐
                   ▼
   ┌──────> [ 다음 상태 조합 논리 ] ──> [ 상태 레지스터 ] ──┬──> 출력(무어: 상태만으로)
   │                                       ▲ CLK            │
   └───────────────────────────────────────┴────────────────┘

   소프트웨어 판:  state = TABLE[state][event]   (없으면 거부)
   CLOSED ─CONNECT→ SYN_SENT ─SYNACK→ ESTABLISHED ─CLOSE→ FIN_WAIT ─ACK→ CLOSED
                       └──TIMEOUT──> CLOSED
   (TCP 이름을 빌린 4상태 단순화 예 — 실제 TCP 종료는 FIN-WAIT-1 → FIN-WAIT-2 → TIME-WAIT → CLOSED 등, RFC 9293 §3.3.2)
```

- *유한 상태 기계(FSM)*: 상태 몇 개와 "현재 상태 + 입력 → 다음 상태" 규칙으로 동작하는 모델. 하드웨어에서는 상태를 레지스터에, 규칙을 조합 회로에 둔다.
  - *무어 기계*: 출력이 상태만으로 정해진다. *밀리 기계*: 출력이 상태와 입력으로 정해진다.
- 상태 k개를 2진 부호로 담으려면 플립플롭이 적어도 ⌈log2 k⌉개 필요하다(상태마다 1비트를 쓰는 one-hot 부호화면 k개). 실험 4의 4상태 연결 기계는 2개.
- 실험 4: 표에 없는 전이(`ESTABLISHED + SYNACK`, `CLOSED + CLOSE`)는 거부하고 상태를 유지했다. 순서 감지기 "1011"(겹침 허용)은 입력 `110110101101011`에 `000010000100001`을 냈다.
- 원고 §7의 PC·IR도 상태 레지스터다. CPU 전체가 거대한 FSM이라고 볼 수 있다(CS:APP 4.3.1 "Organizing Processing into Stages"가 Y86-64 처리를 단계로 나눈다 — 절 제목 기준).

### 5. 메타안정성 — 비동기 입력은 언젠가 창 안에 들어온다

```text
         T_W (셋업+홀드 창)
           ├──┤
  CLK  ____|‾‾‾‾‾      입력이 이 창 안에서 바뀌면 플립플롭이 0/1 사이에 머문다
  D    ___/‾‾‾‾‾‾      머무는 시간이 t 를 넘을 확률 ≈ e^(−t/τ)

  메타안정 진입률 = T_W · F_C · F_D
  MTBF = e^(S/τ) / (T_W · F_C · F_D)          (Ginosar 2011)
    S: 다음 플립플롭이 잡기 전까지 해소에 쓸 수 있는 시간
    τ: 해소 시정수(공정 게이트 지연 수준), F_C: 클록, F_D: 입력 변화율

  두 플립플롭 동기화기
  비동기 입력 ──>[FF1]──>[FF2]──> 내부 회로       FF1 이 메타안정이어도 한 주기(S ≈ T_C) 안에 대부분 해소
                 CLK    CLK
```

- *메타안정성(metastability)*: 쌍안정 소자가 0도 1도 아닌 중간 상태에 일정 시간 머무는 현상. 머무는 시간에 상한이 없고, 확률만 지수적으로 줄어든다(Ginosar 2011, Chaney·Molnar 1973).
- *비동기 입력*: 받는 쪽 클록과 무관한 시각에 바뀌는 신호. 버튼, 다른 클록 도메인의 신호, 외부 칩.
- *동기화기(synchronizer)*: 비동기 입력을 받는 쪽 클록으로 옮기는 회로. 대표가 플립플롭 두 개 직렬.
- 실험 6(Ginosar의 예 τ=10ps, T_W=20ps, F_C=1GHz, F_D=F_C/10을 그대로 계산):

```text
  메타안정 진입률 T_W*F_C*F_D = 2e+06 회/초
  S = 0.1 주기   MTBF = 0.011 초
  S = 0.2 주기   MTBF = 243 초
  S = 0.5 주기   MTBF = 2.59e+15 초 = 8.21e+07 년
  S = 1 주기     MTBF = 1.34e+37 초 = 4.26e+29 년   ← 논문 값 "4 × 10^29 years"와 일치
```

- 진입은 초당 200만 번 일어난다. 실패를 막는 것은 진입이 아니라 **해소 시간 S**다. S를 0.2주기에서 1주기로 늘리자 MTBF가 4분에서 10^29년대로 뛰었다.
- Ginosar의 경고: 데이터 여러 비트를 비트마다 따로 동기화하면 일부 비트는 한 주기, 일부는 두 주기 뒤에 넘어와 값이 깨진다. 같은 비동기 입력을 두 동기화기로 따로 받으면 하나는 1, 하나는 0으로 해소돼 상태가 모순된다. 여러 비트는 FIFO와 Gray 부호 포인터로 넘긴다.
  - *Gray 부호*: 이웃한 수가 1비트만 다른 2진 부호. 실험 7에서 3비트 카운터가 3→4로 바뀌는 순간 2진 부호는 0~7 아무 값으로나 읽힐 수 있었고, Gray 부호는 3이나 4로만 읽혔다.

### 실험: 래치·플립플롭·클록 위반·FSM·MTBF·Gray 부호

환경: i7-13700HX, Linux 7.0.0-34, Docker `eclipse-temurin:21-jdk`(OpenJDK 21.0.12) `--cpus=2 --network none`, 호스트 Python 3.12.3(표준 라이브러리). 2026-10-07. 1~4는 07과 같은 **게이트 지연 = 1 단위 모델**의 시뮬레이션이고, 6은 논문 식 계산, 7은 경우의 수 열거다. 모두 결정적이다.

```java
// Seq08.java 핵심
int q = g.add(T.NOR, R, 0), qn = g.add(T.NOR, S, 0);
g.set(q, R, qn); g.set(qn, S, q);                     // 되먹임 배선 = SR 래치
int master = dLatch(g, D, clkN);                      // CLK=0 에 투명
int qFF    = dLatch(g, master, CLK);                  // CLK=1 에 투명 → 상승 에지 플립플롭
for (int t = 0; t < period; t++) v = g.step(v);       // 다음 에지까지 주기만큼 흐른 뒤
int sampled = /* 가산기 합 출력 */;                    // 레지스터가 잡는다
Conn nx = TABLE.get(st).get(e);                       // FSM: 없으면 거부
```

```text
== 5. 클록 관찰 (호스트) ==
  cpu MHz : 800.029  799.676  800.008  801.186      (/proc/cpuinfo 앞 논리 CPU 4개, 세 번 읽음, 모두 800 근처)
  최대 CPU MHz: 5000.0000   최소 CPU MHz: 800.0000   scaling_driver intel_pstate, governor powersave
```

## 쓰이는 자료구조·알고리즘

- **유한 상태 기계**: 문자열 매칭 오토마톤([algorithm/25-string-matching](../../algorithm/25-string-matching/2-summary.md), [algorithm/26-aho-corasick](../../algorithm/26-aho-corasick/2-summary.md)), TCP 연결 상태([network/15-tcp-handshake-and-backlog](../../network/15-tcp-handshake-and-backlog/2-summary.md), [network/19-tcp-termination-fin-rst-half-open](../../network/19-tcp-termination-fin-rst-half-open/2-summary.md)), 그래핌 경계 규칙([05](../05-text-length-segmentation-and-case/2-summary.md))이 같은 구조다.
- **전이표**: `상태 × 입력 → 다음 상태`의 2차원 배열(또는 `EnumMap`). 표에 없는 칸을 명시적으로 거부하는 것이 핵심이다.
- **Gray 부호**: `g = x ^ (x >> 1)`. 이웃 값이 1비트만 달라, 한 번의 전환 중에 읽으면 옛 값이나 새 값만 나온다. 실제 회로에서는 비트 사이 지연 차(스큐)가 작아야 이 성질이 지켜진다(Intel 두 클록 FIFO 문서는 Gray 포인터 경로에 skew 제약을 건다) — [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md).
- **두 클록 FIFO = 링 버퍼**: 쓰기 포인터와 읽기 포인터를 각자의 클록 도메인에 두고 Gray 부호로 넘긴다(Ginosar 2011 그림 12) — [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md).
- **지수 꼬리 확률**: 메타안정 지속 확률 e^(−t/τ)는 지수 분포의 꼬리와 같은 꼴이다 — [math/09-common-distributions](../../math/09-common-distributions/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 하드웨어 증상 → 원인

| 증상 | 회로 수준 원인 | 확인·대처 |
|---|---|---|
| 드물게, 재현 안 되는 오동작. 외부 입력·다른 클록과 관련 | 동기화기 없는 비동기 입력 → 메타안정 | 모든 클록 도메인 경계에 동기화기가 있는지(설계 검토), MTBF 계산 |
| 클록을 올리면 특정 값에서만 틀림 | 셋업 위반(최악 경로 > 주기) | 기본 클록으로 재현, 정적 타이밍 분석 |
| 잡음·짧은 펄스가 상태를 바꿈 | 레벨 래치의 투명 구간에 글리치 통과 | 에지 플립플롭 사용 |
| 여러 비트 값이 가끔 엉뚱한 값 | 비트마다 따로 동기화 | FIFO + Gray 부호 포인터 |

### 2. 코드의 상태 기계는 같은 규칙을 따른다

- 상태는 한 곳(레지스터 ↔ DB 컬럼 하나)에 두고, 다음 상태는 표로 정한다. 표에 없는 전이는 예외로 거부한다.

```java
enum Order { CREATED, PAID, SHIPPED, CANCELLED }
static final Map<Order, Set<Order>> NEXT = Map.of(
        Order.CREATED, EnumSet.of(Order.PAID, Order.CANCELLED),
        Order.PAID,    EnumSet.of(Order.SHIPPED, Order.CANCELLED),
        Order.SHIPPED, EnumSet.noneOf(Order.class),
        Order.CANCELLED, EnumSet.noneOf(Order.class));
static Order move(Order from, Order to) {
    if (!NEXT.get(from).contains(to)) throw new IllegalStateException(from + " → " + to);
    return to;
}
```

- 여러 서버가 같은 상태를 바꾸면 "에지에서만 바꾼다"에 해당하는 원자적 전이가 필요하다. DB에서는 `UPDATE … SET state='PAID' WHERE id=? AND state='CREATED'`(조건부 갱신)로 한 번에 검사·전이한다 — [database/18-app-level-concurrency-patterns](../../database/18-app-level-concurrency-patterns/2-summary.md).
- 비유(해석): 다른 스레드가 쓰는 여러 필드를 락 없이 하나씩 읽는 것은 "비트마다 따로 동기화"와 같은 모양이다. 일부 필드는 새 값, 일부는 옛 값이 섞인다. 묶어서 넘기려면 불변 객체 하나를 `volatile`·`AtomicReference`로 교체한다 — [os/15-race-conditions](../../os/15-race-conditions/2-summary.md), 메모리 순서는 이 영역 [14번](../14-cache-coherence-and-memory-ordering/2-summary.md).

### 3. 클록을 관찰한다

```bash
lscpu | grep MHz                    # 최대·최소 주파수
grep "cpu MHz" /proc/cpuinfo        # 논리 CPU별 보고 주파수(바뀐다)
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```

- 벤치마크 결과가 들쑥날쑥하면 주파수 변화(절전 governor, 하이브리드 P/E 코어)를 먼저 의심한다. 이 호스트는 한가할 때 800 MHz 근처였다(실험 5).

## 장애 시나리오와 대처

### 1. 비동기 신호 동기화 실패 → 메타안정성으로 간헐 오동작 (⚠ 커리큘럼)

- **현상**: 장비가 몇 주에 한 번 이상한 상태에 빠진다. 같은 시험을 반복해도 재현이 안 된다.
- **보이는 형태**: 로그상 "불가능한" 상태 조합. Ginosar 2011 서두의 예화(우주선 J)는 동기화기 실패로 논리가 모순된 상태에 빠져 너무 많은 장치가 동시에 켜지고 전원부가 타 버렸다는 이야기다(튜토리얼의 도입 예화로, 실제 사건 보고서는 아니다).
- **원인**: 비동기 입력이 셋업·홀드 창 안에서 바뀌어 플립플롭이 늦게 해소됐고, 그 사이 다음 회로가 서로 다른 값으로 읽었다. 진입 자체는 흔하다(실험 6의 조건에서 초당 200만 번). 해소 시간이 부족하면 실패가 된다.
- **대처**: 충분히 오래 유지되는 1비트 제어 신호는 두(필요하면 세) 플립플롭 동기화기로 받는다. 짧은 펄스는 놓칠 수 있으므로 req/ack 핸드셰이크로, 여러 비트 데이터는 제어 신호만 동기화하거나 두 클록 FIFO로 넘긴다(Ginosar 그림 10·12). 두 플립플롭은 가까이 배치해 배선 지연이 해소 시간을 깎지 않게 한다(Ginosar). MTBF를 계산해 제품 수명보다 훨씬 크게 둔다.

### 2. 해소 시간이 모자란 동기화기 — MTBF가 분 단위

- **현상**: 동기화기는 넣었는데 클록을 올린 뒤 오동작이 생겼다.
- **보이는 형태**: 실험 6의 같은 조건에서 해소 시간 S가 0.2주기이면 MTBF 243초(약 4분), 0.1주기이면 0.011초.
- **원인**: MTBF는 S에 지수적으로 민감하다. 클록 주기가 줄면 S도 준다. 동기화기 사이에 논리를 끼우면 S가 더 준다.
- **대처**: 동기화기 사이에 논리를 두지 않는다. 빠른 클록에서는 플립플롭 단을 늘린다. MTBF는 동기화기 수에 대략 반비례해 줄어든다. 그래서 Ginosar는 동기화기 1,000개를 쓰는 시스템이면 각 동기화기를 시스템 신뢰도 목표보다 적어도 세 자릿수 큰 MTBF로 설계하라고 예를 든다 — 동기화기 수와 목표를 함께 보고 정한다.

### 3. 같은 입력을 두 동기화기로, 또는 여러 비트를 따로 동기화

- **현상**: 두 하위 회로가 같은 이벤트에 대해 다른 결정을 내린다. 넘겨받은 카운터 값이 가끔 크게 튄다.
- **보이는 형태**: 3→4 전환을 다른 클록이 읽으면 2진 부호는 0~7 어느 값으로도 읽힐 수 있다(실험 7).
- **원인**: 동기화기마다 해소 결과(0/1)와 걸리는 주기 수가 다를 수 있다. Ginosar는 이를 "데이터의 완전한 손실", "모순된 상태"로 부르며 금지한다.
- **대처**: 하나의 동기화기 출력을 나눠 쓴다. 여러 비트는 제어 신호만 동기화하거나, 두 클록 FIFO에서 포인터를 Gray 부호로 넘긴다.

### 4. 래치의 투명 구간에 글리치가 통과

- **현상**: 클록이 1인 동안 생긴 짧은 잡음이 상태를 바꾼다.
- **보이는 형태**: 실험 2에서 t=14~16의 D 글리치가 Q래치에는 나타났고, 같은 입력의 에지 플립플롭에는 없었다.
- **원인**: 레벨 감지 래치는 클록이 1인 동안 입력을 계속 통과시킨다.
- **대처**: 상태 저장은 에지 트리거 플립플롭으로 한다. 래치를 쓰는 설계는 투명 구간 동안 입력이 안정됨을 타이밍으로 보장한다.

### 5. 소프트웨어 FSM이 정의 안 된 전이를 받아들임

- **현상**: 취소된 주문이 나중에 도착한 결제 승인 콜백 때문에 다시 "결제 완료"가 된다.
- **보이는 형태**: 상태 이력에 `CANCELLED → PAID`가 있다. 오류 로그 없음.
- **원인**: 전이 규칙 없이 "들어온 이벤트대로 상태를 덮어쓰기"를 했다. 하드웨어 FSM이 정의된 다음 상태만 갖는 것과 달리, 코드는 아무 값이나 쓸 수 있다.
- **대처**: 전이표로 검사하고 표에 없으면 거부한다(적용 2). 동시에 오는 이벤트는 조건부 갱신으로 원자적으로 전이한다.

## 핵심 문장

- 되먹임이 있는 회로는 기억을 갖는다. SR 래치 → D 래치 → 에지 트리거 D 플립플롭 → 레지스터 순으로 쌓는다.
- 래치는 클록이 1인 동안 투명하고, 플립플롭은 에지 순간만 잡는다. 그래서 에지에서 먼 글리치는 플립플롭에 저장되지 않는다. 에지 근처의 변화는 셋업·홀드 타이밍으로 막아야 한다.
- 클록 주기는 조합 회로 최악 경로보다 길어야 한다. 짧으면 레지스터가 글리치·중간값을 잡는다.
- 유한 상태 기계 = 상태 레지스터 + 다음 상태 함수. 코드에서도 전이표로 정의 밖 전이를 거부한다.
- 비동기 입력은 언젠가 셋업·홀드 창에 걸린다. 메타안정은 막을 수 없고, 해소 시간을 줘서 MTBF = e^(S/τ)/(T_W·F_C·F_D)를 충분히 키운다.

## 관련 주제·근거

- 선행: [07-logic-gates-to-adder](../07-logic-gates-to-adder/2-summary.md)
- 원고: [foundations/hardware-basics](../../foundations/hardware-basics/README.md) §5(순차 논리·플립플롭), §6(클록·D 플립플롭), §7(레지스터 IR·PC)
- 후속(이 영역): [09-isa-and-machine-code](../09-isa-and-machine-code/2-summary.md) · [18 파이프라인](../18-pipelining-and-branch-prediction/2-summary.md) · [14 캐시 일관성·메모리 순서](../14-cache-coherence-and-memory-ordering/2-summary.md)
- 연결
  - [algorithm/25-string-matching](../../algorithm/25-string-matching/2-summary.md) · [algorithm/26-aho-corasick](../../algorithm/26-aho-corasick/2-summary.md) — 오토마톤
  - [network/15-tcp-handshake-and-backlog](../../network/15-tcp-handshake-and-backlog/2-summary.md) · [network/19-tcp-termination-fin-rst-half-open](../../network/19-tcp-termination-fin-rst-half-open/2-summary.md) — TCP 상태 기계
  - [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md) — 두 클록 FIFO의 소프트웨어 짝
  - [database/18-app-level-concurrency-patterns](../../database/18-app-level-concurrency-patterns/2-summary.md) — 조건부 갱신으로 원자적 상태 전이
  - [os/15-race-conditions](../../os/15-race-conditions/2-summary.md)
- 근거
  - CS:APP 3판 4.2.5 "Memory and Clocking", 4.3 "Sequential Y86-64 Implementations"(절 제목은 저자 사이트 머리말 PDF 목차로 확인 <https://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf>, 본문은 이 작업에서 열지 못함)
  - Patterson & Hennessy 부록 A(래치·플립플롭·FSM) [?] — 장 번호 미확인
  - R. Ginosar, "Metastability and Synchronizers: A Tutorial", IEEE Design & Test of Computers, Sept/Oct 2011 — 메타안정 진입률 T_W·F_C·F_D, 지속 확률 e^(−t/τ), MTBF 식과 28nm 예(4 × 10^29년), 두 플립플롭 동기화기, 비트별 동기화·이중 동기화 금지, 두 클록 FIFO·Gray 포인터 <http://webee.technion.ac.il/~ran/papers/Metastability-and-Synchronizers.IEEEDToct2011.pdf>
  - T. J. Chaney, C. E. Molnar, "Anomalous Behavior of Synchronizer and Arbiter Circuits", IEEE Trans. Computers, 1973 <http://ibm-1401.info/AnomalousSynchronizer_ChaneyMolnar_IEEE1973.pdf>
  - Linux 커널 문서 "CPU Performance Scaling"(P-state = 주파수·전압 구성) <https://docs.kernel.org/admin-guide/pm/cpufreq.html> · "x86 Topology"(`/proc/cpuinfo` 항목은 논리 CPU=스레드 단위) <https://docs.kernel.org/arch/x86/topology.html>
  - Intel Quartus 문서 "Dual Clock FIFO Timing Constraints"(Gray 포인터 경로의 `set_max_skew`) <https://www.intel.com/content/www/us/en/docs/programmable/683082/22-1/dual-clock-fifo-timing-constraints.html> (Internet Archive 사본으로 열람)
  - RFC 9293 §3.3.2 TCP 상태 기계 <https://www.rfc-editor.org/rfc/rfc9293.html#section-3.3.2>
  - Wikipedia "Flip-flop (electronics)"·"Metastability (electronics)"(2차 정리 — 래치/플립플롭 용어, 동기화기 그림)
- 실험 목록
  - `Seq08.java` — 1. NOR SR 래치(셋·리셋·유지·금지·동시 해제 진동·어긋난 해제), 2. D 래치 vs 마스터–슬레이브 D 플립플롭 파형, 3. 8비트 카운터 클록 주기 40~4 단위의 오답 수, 4. 전이표 FSM과 "1011" 순서 감지기. 단위 지연 모델. OpenJDK 21.0.12, Docker `--cpus=2 --network none`.
  - 61→62 전환 글리치 추적 — 같은 모델을 Python으로 복제해 시각별 합 출력 확인(Java 결과 127과 일치). 복제 스크립트는 scratchpad `arch/fc-05/e/trace08.py`(출력 `out-trace08.txt`, 2차 검토에서 다시 돌려 같은 출력).
  - `mtbf08.py` — Ginosar 식으로 S별 MTBF. `gray08.py` — 3비트 2진/Gray 카운터의 전환 중 읽힐 수 있는 값 열거. Python 3.12.3.
  - 호스트 클록 관찰 — `lscpu`, `/proc/cpuinfo`, `scaling_driver`·`scaling_governor`(읽기만).
  - 파일 위치: scratchpad `arch/05/`(Seq08.java, mtbf08.py, gray08.py, out-seq08.txt, out-mtbf08.txt, out-gray08.txt, out-freq08.txt).
