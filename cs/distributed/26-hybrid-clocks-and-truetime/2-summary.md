# distributed/26-hybrid-clocks-and-truetime — HLC·TrueTime·commit wait — 정리 (힌트)

## 해결하는 문제

분산 DB는 "이 트랜잭션은 시각 t에 커밋됐다"는 타임스탬프로 스냅샷 읽기·MVCC를 한다. 그 타임스탬프를 무엇으로 정할까?

```text
  벽시계(물리 시각)   사람이 읽을 수 있음, "10:00 기준 스냅샷" 가능   ✗ 노드마다 어긋나 인과가 뒤집힘
  논리 시계(05번)     인과 보존                                   ✗ 물리 시각과 무관 → "10:00 기준"을 못 물음
  HLC               둘 다: 물리 시각에 가깝고 인과도 보존            △ 시계가 가정보다 크게 어긋나면 흔들림
  TrueTime          시각을 구간 [earliest, latest]로 받음 + 기다림   △ 하드웨어 시계 기반 오차 상한이 필요
```

- 목표 성질: *외부 일관성(external consistency)*. T1이 커밋을 마친 **뒤에** T2가 시작했다면 T2의 커밋 타임스탬프가 T1보다 커야 한다(Spanner 논문).
  - 시스템 밖(사용자가 화면을 보고 다음 요청을 누름)에서 생긴 순서까지 타임스탬프 순서가 따라야 한다는 뜻이다. 05번의 "숨은 채널" 문제다.

쉬운 예: 은행 창구 두 곳의 시계가 다르다.
- 1번 창구에서 입금을 마친 손님이 바로 2번 창구로 가 잔액을 조회한다.
- 2번 창구 시계가 늦으면 "입금 전 시각"의 장부를 보여 준다.

똑같은 구조다.\
해법은 둘이다. 시계를 오차 범위와 함께 쓰고 그 오차만큼 기다리거나(TrueTime), 주고받은 타임스탬프로 시계를 끌어올린다(HLC).
- 단, HLC는 타임스탬프가 메시지로 전달된 순서만 지킨다(정리 1). 손님이 창구를 옮기듯 타임스탬프 없이 생긴 순서는 그 타임스탬프를 함께 넘기거나, 불확실성 구간·대기 같은 별도 장치로 막아야 한다.

실무 예:
- Google Spanner: TrueTime + commit wait로 외부 일관성(Corbett 외 2012).
- CockroachDB: HLC + 최대 시계 오프셋(기본 500ms) + 불확실성 구간(타임스탬프 올림, 필요하면 재시도)([database/55](../../database/55-distributed-databases/2-summary.md)).

## 동작·원리

### 1. HLC — 물리 시각 l + 논리 카운터 c

```text
  보내기·로컬 사건:                         받기(메시지 m의 l.m, c.m):
    l' = l                                  l' = l
    l  = max(l', pt)                        l  = max(l', l.m, pt)
    c  = (l == l') ? c + 1 : 0              c  = l == l' == l.m ? max(c, c.m) + 1
                                                 : l == l'      ? c + 1
                                                 : l == l.m     ? c.m + 1
                                                 : 0
  타임스탬프 = (l, c), 사전순 비교            pt = 이 노드의 물리 시계 값
```

- Kulkarni 외 2014의 Figure 5 알고리즘이다. 성질(같은 논문)
  - 정리 1: `e → f`이면 `(l.e, c.e) < (l.f, c.f)`. 램포트 시계처럼 인과를 지킨다.
  - 정리 2: `l.f ≥ pt.f`. l은 자기 물리 시계보다 작아지지 않는다.
  - 따름정리 1: `|l.f − pt.f| ≤ ε`. 여기서 ε은 노드 간 시계 동기 오차 상한이다. 즉 l은 "지금까지 들은 가장 큰 물리 시각"이고 **자기 물리 시계 pt**에서 ε 이상 벗어나지 않는다. 진짜 시각과의 차이는 pt 자체의 절대 오차가 더해진다(모든 노드가 함께 1시간 앞서도 ε은 작을 수 있다).
  - c도 유계다(따름정리 3: `c ≤ N·(ε + 1)`). 이 수치는 시계 동기 가정에 더해 "한 노드의 연속한 두 사건 사이에 물리 시계가 최소 한 단위 오른다"는 제약을 쓴 증명이다. 한 틱(예: 1ms) 안에 사건이 여럿이면 이 수치는 그대로 적용되지 않는다.
- 64비트에 담기(논문 §6): l이 64비트 NTP 타임스탬프의 상위 48비트만 따라가게 한다(올림, 마이크로초 수준 정밀도). 나머지 16비트를 c에 준다(최대 65536).
  - 아래 적용 2의 Java는 단순하게 Unix ms를 48비트 자리에 담는다. 논문의 NTP 형식과는 다른 예시 배치다.
- HLC는 물리 시계를 **읽기만** 한다. 남이 보낸 더 큰 시각을 받아도 OS 시계를 고치지 않고 l·c에만 반영한다. 그래서 NTP를 쓰는 다른 프로그램에 영향이 없다.
- 모델: 정리 1은 비동기 모델에서도 성립한다. 따름정리 1(유계)은 "시계가 ε 안에서 맞는다"는 가정이 있어야 성립한다.

### 2. TrueTime — 시각을 구간으로

```text
  TT.now()     → [earliest, latest]      진짜 시각이 이 안에 있음을 보장
  TT.after(t)  → t가 확실히 지났나        TT.before(t) → t가 확실히 안 왔나

        earliest      진짜 시각      latest
  ─────────[─────────────●─────────────]──────> 시간
           |←── ε ──→|←── ε ──→|
```

- 구현(Spanner 논문 §3): 데이터센터마다 시각 마스터(대부분 GPS 수신기, 일부는 원자시계를 단 "Armageddon master")와 기계마다 timeslave 데몬.
  - 데몬이 여러 마스터를 폴링하고 Marzullo 알고리즘 변형으로 거짓말하는 마스터를 걸러 낸다.
  - 동기화 사이에는 최악의 드리프트(200µs/s 가정)만큼 ε을 키운다. 폴링 간격 30초.
  - 운영 환경의 ε은 폴링 주기마다 약 1~7ms 톱니 모양, 대부분 약 4ms(평균 ε̄).
- 기준 시각은 윤초를 smearing한 Unix 시각과 비슷하다(논문 §3).

### 3. commit wait — 오차만큼 기다린다

```text
  코디네이터 A                                    진짜 시각
  커밋 요청 도착 ──> s1 ≥ TT.now().latest   ─┐
                    TT.after(s1)이 참이 될 때까지 대기 (기대 대기 ≥ 2ε̄)
                    → 이제 s1은 확실히 과거 ─┘──> 클라이언트에 커밋 완료
                                                      │ (사용자가 결과를 보고)
  다른 노드 B                                          ▼
  T2 시작 ──> s2 ≥ TT.now().latest ≥ 진짜 시각 > s1     ⇒  s1 < s2
```

- 증명 사슬(논문 §4.1.2): `s1 < t(T1 커밋)`(commit wait) → `t(T1 커밋) < t(T2 시작)`(가정) → `t(T2 시작) ≤ t(T2 서버 도착) ≤ s2`(start 규칙) → `s1 < s2`.
- 대가: 쓰기 트랜잭션마다 약 2ε̄을 기다린다. 이 대기는 Paxos 통신과 겹쳐 진행된다(§4.2.1). 1-복제본 실험에서 commit wait는 약 5ms였다(§5.1).
- 이 보장은 **TrueTime 구간이 진짜 시각을 포함한다**는 가정 위에 있다. 시계가 광고한 ε보다 더 틀리면 깨진다(실험 3).

### 실험: HLC와 commit wait 시뮬레이션

- 코드: `Hlc.java`. 시계를 실제로 조작하지 않았다. "실제 시각 + 노드별 어긋남"을 물리 시계로 쓰는 결정적 시뮬레이션이다(단위: 1·2절은 ms, 3절은 µs).

```java
Ts receive(long real, Ts m) {                   // Figure 5: receive event
    long l0 = l; l = Math.max(Math.max(l0, m.l), pt(real));
    if (l == l0 && l == m.l) c = Math.max(c, m.c) + 1;
    else if (l == l0) c = c + 1;
    else if (l == m.l) c = m.c + 1;
    else c = 0;
    return new Ts(l, c);
}
```

(실험, eclipse-temurin 21 JDK 컨테이너, 2026-10-01)

```text
== 1. 물리 시각 vs HLC: 핑퐁 메시지 (A 시계 +40ms, B 시계 0, 전송 지연 5ms) ==
사건          실제  pt(물리)  HLC(l,c)
A send #0    1000    1040   (1040,0)
B recv #0    1005    1005   (1040,1)   ← pt로는 수신(1005)이 송신(1040)보다 '먼저'
B send #0    1006    1006   (1040,2)
A recv #0    1011    1051   (1051,0)
...
== 2. 무작위 교환: 인과 쌍에서 pt 역전 수 vs HLC 역전 수, |l-pt| 최대, c 최대 ==
인과(송신→수신) 쌍 20000: 물리 시각 역전 10013 (50.1%), HLC 역전 0, 최대 l−pt = 66ms (어긋남 폭 100ms 이내), 최대 c = 26

== 2b. 시계가 10초 앞선 노드 X가 메시지 하나를 보내면 (가정 위반) ==
X send pt=15000 (15000,0) → Y recv pt=5001 (15000,1)  (Y의 l−pt = 9999ms)
   1000ms 뒤 Y 로컬 사건 pt=6001 (15000,2)  l−pt=8999ms
   5000ms 뒤 Y 로컬 사건 pt=10001 (15000,3)  l−pt=4999ms
   9998ms 뒤 Y 로컬 사건 pt=14999 (15000,4)  l−pt=1ms
  10001ms 뒤 Y 로컬 사건 pt=15002 (15002,0)  l−pt=0ms

== 3. TrueTime commit wait: T1(노드 A) 커밋 확인 뒤 T2(노드 B) 시작 — s1 < s2 가 지켜지나 ==
실제 어긋남  광고 ε   commit wait  위반/시도   평균 대기(µs)
± 4000µs    4000µs   켬                0/100000   8001
± 4000µs    4000µs   끔            46940/100000   -
± 4000µs    7000µs   켬                0/100000   14001
± 7000µs    4000µs   켬             8432/100000   8001
±10000µs    4000µs   켬            17063/100000   8001
```

- 출력 1은 앞 4줄만 실었다(`...`). 나머지 8줄도 같은 모양이다.
- 관찰
  - 1·2: 물리 시각으로는 인과 쌍의 약 절반이 역전됐다. HLC는 0이다. l은 가장 앞선 노드의 물리 시각을 따라가고(최대 l−pt 66ms), 노드 간 어긋남 폭(100ms)을 넘지 않았다.
  - 2b: 시계가 10초 앞선 노드의 메시지 하나로 Y의 l이 15000에 묶였다. 이후 약 10초 동안 Y의 l은 물리 시각과 멀고 c만 오른다. ε 가정이 깨지면 HLC의 물리 성분은 "지금"을 뜻하지 않는다.
  - 3: 시계 오차가 광고한 ε 안이면 commit wait로 위반 0이다. 끄면 약 47%가 위반이다. 오차가 ε을 넘으면 commit wait를 해도 8~17%가 위반된다. 평균 대기는 2ε(8001µs, 14001µs)이었다.
- 해석: 실험 3의 위반 비율은 이 시뮬레이션의 분포(균등 어긋남, T2가 0~0.5ms 뒤 시작)에 따른 값이다. 실제 비율이 아니라 "가정이 깨지면 0이 아니다"를 보이는 용도다.

### 4. CockroachDB — HLC로 같은 문제를 다르게

- 노드는 요청에 자기 HLC 타임스탬프를 싣고, 받는 노드는 그것으로 자기 HLC를 올린다(Transaction Layer 문서).
- 최대 시계 오프셋 `--max-offset` 기본 500ms(v26.3 `cockroach start` 문서).
  - 노드가 클러스터 절반 이상과의 차이가 이 값의 80%를 넘었다고 감지하면 스스로 종료한다.
  - 이 범위 밖의 어긋남은 "인과 관계가 있는 트랜잭션 사이의 단일 키 선형화"를 깨뜨릴 수 있다고 문서가 적는다. SERIALIZABLE 직렬성 자체는 시계와 무관하게 유지된다.
- 읽기가 자기 시각보다 약간 미래(불확실성 구간 안)의 쓰기를 만나면 트랜잭션 타임스탬프를 그 값 너머로 올린다(`ReadWithinUncertaintyIntervalError`, [database/55](../../database/55-distributed-databases/2-summary.md)). SERIALIZABLE에서는 앞서 읽은 값을 *refresh*로 다시 확인해, 통과하면 그대로 계속하고 실패하면 올린 타임스탬프로 재시도한다(Transaction Layer 문서 Read refreshing). Spanner가 "커밋 쪽에서 기다리는" 비용을 CockroachDB는 주로 "읽기 타임스탬프 조정·재시도"로 낸다.
  - *refresh*: 원래 타임스탬프와 올린 타임스탬프 사이에 내가 읽은 키에 새 쓰기가 없었는지 검사하는 것.
- 비차단 트랜잭션(non-blocking range)은 쓰기 타임스탬프를 미래로 잡고, HLC가 그 시각을 지날 때까지 기다리는 "commit-wait"를 한다(문서).

## 쓰이는 자료구조·알고리즘

- **사전순 튜플 비교 (l, c)** — HLC 순서. 64비트 정수 하나로 압축하면 정수 비교 한 번이다.
- **램포트 시계의 max 규칙** — HLC의 c가 그 역할. [05-logical-clocks](../05-logical-clocks/2-summary.md)
- **구간 시간(interval)** — TrueTime `[earliest, latest]`. 두 구간이 겹치면 순서를 모른다.
- **Marzullo 알고리즘** — 여러 시각 소스의 구간 중 가장 많은 소스가 동의하는 구간을 고르는 방법. TrueTime 데몬이 거짓 마스터를 거를 때 변형을 쓴다.
- **MVCC 타임스탬프** — 커밋 타임스탬프로 버전을 고른다. [database/16-mvcc](../../database/16-mvcc/2-summary.md) · [database/17-occ-and-timestamp-ordering](../../database/17-occ-and-timestamp-ordering/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 무엇을 보장해야 하나부터

| 필요한 것 | 선택 |
|---|---|
| 인과만 지키면 되고 사람이 읽을 시각도 필요 | HLC (이벤트·로그 타임스탬프) |
| 한 키에 대한 "더 최근"만 필요 | 단조 토큰·버전(12번) |
| 사용자가 본 결과 이후의 쓰기가 반드시 더 큰 타임스탬프 | 외부 일관성: TrueTime + commit wait, 또는 중앙 타임스탬프 발급(TSO) |
| 시계 오차를 감당 못 하는 환경(VM 정지가 잦음 등) | 중앙 발급(TSO) 또는 합의 로그 순번 |

### 2. Java — 64비트 HLC (48비트 ms + 16비트 c)

```java
public final class HybridClock {
    private long l;  private int c;                       // 단일 스레드 가정(필요하면 synchronized)
    private final LongSupplier physicalMs;                // System::currentTimeMillis
    private final long maxOffsetMs;                       // 믿을 수 있는 어긋남 상한 (예시: 500)
    public HybridClock(LongSupplier physicalMs, long maxOffsetMs) { this.physicalMs = physicalMs; this.maxOffsetMs = maxOffsetMs; }

    public long now() {                                   // 로컬·보내기
        long pt = physicalMs.getAsLong(), l0 = l;
        l = Math.max(l0, pt);  c = (l == l0) ? c + 1 : 0;
        return pack();
    }
    public long update(long remote) {                     // 받기
        long rl = remote >>> 16; int rc = (int) (remote & 0xFFFF);
        long pt = physicalMs.getAsLong();
        if (rl - pt > maxOffsetMs)                         // 가정 위반을 그냥 받아들이지 않는다 (실험 2b)
            throw new IllegalStateException("remote clock ahead by " + (rl - pt) + "ms");
        long l0 = l;  l = Math.max(Math.max(l0, rl), pt);
        if (l == l0 && l == rl) c = Math.max(c, rc) + 1;
        else if (l == l0) c++;
        else if (l == rl) c = rc + 1;
        else c = 0;
        return pack();
    }
    private long pack() {
        if (c > 0xFFFF) throw new IllegalStateException("logical counter overflow");
        return (l << 16) | c;
    }
}
```

- 원격 시각이 상한보다 앞서면 거부하는 줄은 논문 알고리즘에 없는 **방어 정책**이다. 받아들이면 실험 2b처럼 l이 미래에 묶인다. 거부할지, 경고만 할지는 시스템 정책이다.

### 3. 운영 점검

```bash
chronyc tracking            # System time 오프셋, Last offset, RMS offset — 노드별로 모아 비교
chronyc sources -v          # 시각 소스와 상태
```

- 모든 노드가 같은 시각 소스, 또는 같은 방식으로 윤초를 smearing하는 소스에 붙어야 한다. CockroachDB FAQ: Google·Amazon 시각 서비스는 smearing 방식이 같아 섞어도 되지만, 기본 NTP pool(smearing 안 함)과 섞으면 안 된다.
- CockroachDB는 노드 간 오프셋을 지표·로그로 낸다. 최대 오프셋의 80% 전에 알람을 건다.

## 장애 시나리오와 대처

### 1. 시계 불확실성 상한 초과 → 외부 일관성 위반 (커리큘럼 ⚠)

- **현상**: 사용자가 방금 저장한 값을 다른 화면에서 조회하면 옛 값이 나온다. 드물고 재현이 어렵다.
- **보이는 형태**: 두 트랜잭션의 커밋 타임스탬프 순서가 실제 순서와 반대. 시계 오프셋 지표가 설정 상한(ε, max-offset)을 넘은 구간과 겹친다. 실험 3의 `±7000µs / 4000µs → 8432/100000`.
- **원인**: commit wait·불확실성 구간은 "실제 오차 ≤ 상한"을 가정한다. 그 가정이 깨지면 기다려도 순서가 보장되지 않는다.
- **대처**
  - 시계 오프셋을 상한보다 낮은 문턱으로 감시하고, 넘는 노드를 빼낸다. CockroachDB는 80%에서 스스로 종료한다. Spanner는 주파수 이상이 큰 기계를 축출한다(논문 §3).
  - 상한을 키우면 안전해지지만 commit wait·읽기 재시작이 늘어난다(CockroachDB `--max-offset` 문서).

### 2. 앞선 시계 하나가 HLC를 미래로 끌고 감

- **현상**: 타임스탬프가 실제보다 수 초~수 분 미래로 찍힌다. "10:00 기준 스냅샷"이 엉뚱한 범위를 본다.
- **보이는 형태**: 물리 성분 l은 멈추고 논리 성분 c만 오른다. 실험 2b에서 Y의 l이 약 10초 동안 15000에 묶였다. c 16비트가 넘칠 수도 있다.
- **원인**: HLC는 들은 것 중 가장 큰 물리 시각을 따라간다. 한 노드의 시계가 크게 앞서면 그 값이 메시지를 타고 퍼진다. 유계 증명(따름정리 1)은 시계가 ε 안에서 맞는다는 가정이 있을 때만 성립한다.
- **대처**: 받은 타임스탬프가 자기 시계 + 상한보다 크면 거부·경고한다(적용 2의 방어 정책). 시계 앞섬을 지표로 감시한다.

### 3. VM 정지·이동 뒤 낡은 시계

- **현상**: VM 일시 정지(vMotion 등) 직후 잠깐 오래된 데이터를 읽고, 그것을 바탕으로 쓴다.
- **보이는 형태**: 재개 직후 노드 시계가 앞으로 크게 점프한다.
- **원인**: 정지 동안 시계가 멈춰 있다가 재개 뒤 맞춰진다. 그 사이 노드는 자기가 과거에 있는 줄 모른다.
- **대처**: CockroachDB는 `server.clock.forward_jump_check_enabled`로 앞쪽 점프를 감지해 알리고, `--clock-device`로 PTP 하드웨어 시계를 쓰게 한다(FAQ).
  - *PTP(Precision Time Protocol)*: 하드웨어 타임스탬프로 NTP보다 정밀하게 시계를 맞추는 프로토콜(IEEE 1588).

### 4. ε이 커지면 쓰기 지연이 커짐

- **현상**: 특정 데이터센터의 쓰기 p50이 몇 ms씩 오른다.
- **보이는 형태**: commit wait 시간이 늘었다. 실험 3에서 ε을 4ms → 7ms로 키우자 평균 대기가 8001µs → 14001µs.
- **원인**: commit wait는 약 2ε. ε은 시각 마스터와의 통신 지연, 동기 간격 사이의 드리프트 추정에 따라 커진다(논문 §3).
- **대처**: 시각 인프라(마스터 연결·폴링)를 점검한다. 애플리케이션은 쓰기마다 고정 지연이 있다고 보고 묶어서 쓴다.

### 5. 윤초 처리 방식이 노드마다 다름

- **현상**: 윤초 전후 하루 동안 노드 간 오프셋이 수백 ms 벌어져 노드가 종료되거나 재시작이 늘어난다.
- **보이는 형태**: 일부 노드는 smearing 소스(하루 동안 조금씩), 일부는 계단식 윤초 소스를 쓴다.
- **원인**: 윤초 근처에서는 같은 순간에도 smearing 소스와 계단식 소스의 시각이 서로 다르다. 차이의 크기는 smearing 구현(기간·모양)에 따라 다르다.
- **대처**: 모든 노드를 같은 시각 소스 또는 같은 smearing 방식의 소스에 붙인다(CockroachDB FAQ). 윤초 자체는 [04번](../04-physical-clocks-and-ntp/2-summary.md).

## 핵심 문장

- 외부 일관성은 "커밋을 본 뒤 시작한 트랜잭션은 더 큰 타임스탬프"라는 성질이고, 시스템 밖의 순서까지 따라야 한다.
- HLC는 (l, c)로 인과를 지키고, l이 자기 물리 시계에서 시계 오차 상한 ε 이상 벗어나지 않게 한다. 다만 그 유계성은 시계가 ε 안에서 맞을 때만 성립한다.
- TrueTime은 시각을 구간으로 주고, Spanner는 쓰기 커밋 타임스탬프 s를 `TT.now().latest` 이상(prepare 타임스탬프 등 다른 제약도 만족)으로 정한 뒤 `TT.after(s)`까지(약 2ε) 기다려 외부 일관성을 얻는다.
- 두 방식 모두 "실제 오차 ≤ 상한"이 깨지면 보장이 깨진다. 그래서 시계 오프셋 감시와 넘는 노드 제거가 프로토콜의 일부다.
- Spanner는 쓰기 쪽 대기로, CockroachDB는 주로 불확실성 구간 안의 읽기 타임스탬프 조정·재시도로(비차단 범위에서는 commit-wait로도) 같은 불확실성 비용을 낸다.

## 관련 주제·근거

- 선행: [05-logical-clocks](../05-logical-clocks/2-summary.md) — happens-before, 램포트 시계, 숨은 채널
- 선행: [04-physical-clocks-and-ntp](../04-physical-clocks-and-ntp/2-summary.md) — NTP·윤초·단조 시계
- 연결
  - [database/55-distributed-databases](../../database/55-distributed-databases/2-summary.md) — TSO·TrueTime·HLC 비교, 불확실성 재시작(40001)
  - [database/16-mvcc](../../database/16-mvcc/2-summary.md) · [database/17-occ-and-timestamp-ordering](../../database/17-occ-and-timestamp-ordering/2-summary.md)
  - [24-conflict-resolution-and-crdt](../24-conflict-resolution-and-crdt/2-summary.md) — LWW 타임스탬프가 시계에 의존하는 문제
  - [13-distributed-id-generation](../13-distributed-id-generation/2-summary.md) — 시각을 앞에 둔 ID
  - [07-consistency-models](../07-consistency-models/2-summary.md) — 선형화(외부 일관성과 가까운 실시간 순서 조건)
  - [08-cap-and-pacelc](../08-cap-and-pacelc/2-summary.md)(평시 지연 vs 일관성)
- 논문
  - S. Kulkarni, M. Demirbas, D. Madeppa, B. Avva, M. Leone, "Logical Physical Clocks and Consistent Snapshots in Globally Distributed Databases", 2014 — Figure 5 HLC, 정리 1~4, 따름정리 1·3, 48+16비트 <https://cse.buffalo.edu/tech-reports/2014-04.pdf>
  - J. C. Corbett 외, "Spanner: Google's Globally-Distributed Database", OSDI 2012 — §3 TrueTime(API, GPS·Armageddon 마스터, Marzullo, ε 1~7ms·평균 4ms, 200µs/s, 30초), §4.1.2 commit wait와 외부 일관성 증명, §4.2.1 기대 대기 ≥ 2ε̄, §5.1 commit wait 약 5ms <https://static.googleusercontent.com/media/research.google.com/en//archive/spanner-osdi2012.pdf>
- 강의: MIT 6.5840 Spring 2026 LEC 12 Spanner(3월 31일, 준비 자료 Spanner 2012 논문) <https://pdos.csail.mit.edu/6.824/schedule.html>
- 제품 문서
  - CockroachDB v26.3 `cockroach start` — `--max-offset` 기본 500ms <https://www.cockroachlabs.com/docs/stable/cockroach-start>
  - CockroachDB Transaction Layer — HLC, Max clock offset enforcement(80%), non-blocking transactions의 commit-wait <https://www.cockroachlabs.com/docs/stable/architecture/transaction-layer>
  - CockroachDB Operational FAQs — 시계 비동기 시 동작, vMotion·`server.clock.forward_jump_check_enabled`·`--clock-device`, 윤초 smearing 소스 혼용 금지 <https://www.cockroachlabs.com/docs/stable/operational-faqs>
- 실험 목록
  - `Hlc.java` — Figure 5 HLC 핑퐁(A +40ms), 5노드 무작위 2만 메시지(±50ms), 10초 앞선 노드의 전파, TrueTime commit wait 몬테카를로(각 10만 회, 실제 어긋남·ε·대기 조합). eclipse-temurin 21 JDK 컨테이너, 시계 조작 없는 시뮬레이션.
