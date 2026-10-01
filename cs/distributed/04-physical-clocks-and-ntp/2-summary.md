# distributed/04-physical-clocks-and-ntp — 벽시계와 단조 시계, NTP, 시계 어긋남, 윤초 — 정리 (힌트)

## 해결하는 문제

프로그램은 시계에 두 종류의 질문을 한다(DDIA 1판 8장 "Unreliable Clocks").

```text
  "얼마나 걸렸나?" (지속 시간, duration)        "지금 몇 시인가?" (시각, point in time)
  ─────────────────────────────────           ─────────────────────────────────
  요청이 타임아웃 됐나?                          이 글은 언제 게시됐나?
  p99 응답 시간은?                              알림 메일을 언제 보내나?
  지난 5분 초당 요청 수는?                       이 캐시는 언제 만료되나?
  → 단조 시계로 잰다                             → 벽시계(+ 동기화)로 잰다
```

둘을 섞으면 깨진다. 벽시계로 경과 시간을 재면 시계가 뒤로 갈 때 **음수 시간**이 나온다. 다른 기계의 벽시계로 순서를 정하면 시계가 어긋날 때 **나중 일이 먼저**가 된다.

쉬운 예: 손목시계 두 개.
- 스톱워치(단조 시계)는 "누른 뒤 몇 초"만 센다. 지금이 몇 시인지는 모른다. 대신 뒤로 가지 않는다.
- 벽에 걸린 시계(벽시계)는 몇 시인지 알려 준다. 대신 누가 시간을 맞추면 바늘이 앞뒤로 뛴다.
- 친구 집 벽시계와 우리 집 벽시계는 몇 분씩 다르다.

똑같은 구조다.\
경과 시간은 스톱워치로, 시각은 벽시계로 잰다. 벽시계끼리는 **NTP**로 맞추지만 완벽하게 맞지는 않는다.

실무 예:
- Cloudflare DNS(2017-01-01): 윤초로 시간이 1초 뒤로 가면서 측정한 RTT가 음수가 됐고, 그 값을 받은 Go `rand.Int63n`이 panic을 냈다.
- 발급 서버 시계가 30초 빠르다. 다른 서버가 방금 받은 JWT를 "`nbf`(이 시각 이전엔 무효)가 미래다"라며 거절한다.
- 다중 리더 DB에서 나중에 쓴 값이 더 작은 타임스탬프를 받아 LWW(마지막 쓰기 승리)에서 조용히 사라진다.

## 동작·원리

### 1. 두 시계 — 벽시계와 단조 시계

```text
  실제 시간 ──────────────────────────────────────────────────→
  벽시계     10:00:00 ─ 10:00:01 ─ 10:00:02 ┐ NTP가 되돌림(step)
  (REALTIME)                               └→ 09:59:59 ─ 10:00:00 ─ …   ← 뒤로 뛴다
  단조 시계   1000.0 ─── 1001.0 ─── 1002.0 ─── 1003.0 ─── 1004.0 ─ …   ← 뒤로 안 간다
  (MONOTONIC) (값 자체엔 뜻이 없다. 부팅 후 초 등. 차이만 쓴다)
```

| | 벽시계(time-of-day) | 단조 시계(monotonic) |
|---|---|---|
| Linux | `clock_gettime(CLOCK_REALTIME)` | `clock_gettime(CLOCK_MONOTONIC)` |
| Java | `System.currentTimeMillis()`, `Instant.now()` | `System.nanoTime()` |
| 값의 뜻 | 1970-01-01 UTC부터의 초(윤초 제외) | 임의 기준점부터의 경과. **다른 기계·다른 JVM과 비교 불가** |
| 뒤로 가나 | 간다(수동 설정, NTP step) | 안 간다 |
| NTP의 영향 | 뛰기(step)와 속도 조절(slew) 둘 다 | 속도 조절만(뛰기 없음) |
| 쓰는 곳 | 시각 기록, 만료 시각, 일정 | 타임아웃, 응답 시간, 경과 시간 |

- Linux `clock_gettime(2)` man 페이지
  - `CLOCK_REALTIME`: 설정 가능한 시스템 전체 시계. 관리자가 시간을 바꾸는 것 같은 **불연속 점프**와 NTP의 주파수 조정 영향을 받는다.
  - `CLOCK_MONOTONIC`: 설정할 수 없다. 불연속 점프의 영향은 받지 않고 **주파수 조정의 영향은 받는다**. Linux에서는 부팅 후 경과 초에 해당한다.
  - `CLOCK_MONOTONIC_RAW`: 주파수 조정도 받지 않는 하드웨어 기반 원시 시간. `CLOCK_BOOTTIME`: `MONOTONIC`과 같지만 시스템 일시 정지(suspend) 시간도 센다.
- Java 21 `System.nanoTime()` 문서: 경과 시간을 재는 데만 쓸 수 있고 벽시계와 관계없다. 기준점은 임의이고(미래일 수도 있어 음수 값도 가능), **같은 JVM 안에서** 두 값의 차이만 의미가 있다.
- Java 21 `System.currentTimeMillis()` 문서: 1970-01-01 UTC부터의 밀리초. 단위는 ms지만 실제 갱신 간격은 OS에 따라 더 클 수 있다.
- Go는 1.9부터 `time.Now()`가 단조 시계 값을 함께 담아, 두 `Time`의 차이 계산이 벽시계 조정에 안전해졌다(Go 1.9 릴리스 노트). Cloudflare 사고(2017-01-01) 당시 RRDNS의 Go는 단조 시계를 제공하지 않았다(사고 보고서).

### 2. 벽시계는 왜 흔들리나

```text
  수정 진동자(quartz)  ──드리프트──→  기계마다 조금씩 빠르거나 느리다(온도에 따라 변함)
         │
         ▼  NTP가 주기적으로 맞춘다
  어긋남 작다 → slew(속도를 살짝 바꿔 천천히 따라잡음)
  어긋남 크다 → step(값을 한 번에 바꿈) ← 이때 앞뒤로 뛴다
         │
         ▼  그 밖에
  윤초(1분이 61초) · VM 일시 정지(앞으로 뜀) · 방화벽에 막힌 NTP(조용히 벌어짐) · 사용자가 바꾼 기기 시계
```

- 드리프트: Google은 서버 시계 드리프트를 200 ppm으로 가정한다. 30초마다 맞추면 6 ms, 하루에 한 번 맞추면 17초까지 벌어질 수 있는 양이다(DDIA 8장이 Spanner 논문을 인용).
  - *ppm(parts per million)*: 백만분의 1. 200 ppm = 1초에 0.2 ms.
- NTP의 속도 조절 한도: DDIA 8장은 "NTP는 기본적으로 시계 속도를 최대 0.05%까지 올리거나 내릴 수 있다"고 쓴다(= 500 ppm). Google 윤초 스미어 문서도 "NTP의 500 ppm 최대"라고 적는다.
- 인터넷 NTP 서버로 맞추면 잘해야 수십 ms, 혼잡하면 100 ms를 넘는 오차가 날 수 있다(DDIA 8장). 그러므로 벽시계 값은 "한 점"이 아니라 **오차 구간**이다. 이 구간을 드러내는 API가 TrueTime이다(26번).
- 어긋남은 조용하다. CPU가 고장 나면 금방 알지만, 시계가 천천히 벌어지면 대부분이 멀쩡히 돌아간다. 피해는 큰 장애가 아니라 **조금씩 조용히 사라지는 데이터**로 나타난다(DDIA 8장 "Relying on Synchronized Clocks").

### 3. NTP — 네 개의 타임스탬프로 오프셋 추정

```text
  클라이언트 A                                 서버 B
     T1 ──── 요청(가는 길 d1) ────────────→ T2
                                            │ 처리
     T4 ←─── 응답(오는 길 d2) ───────────── T3
  (T1·T4는 A의 시계, T2·T3는 B의 시계)

  왕복 지연  δ = (T4 − T1) − (T3 − T2)
  오프셋     θ = ((T2 − T1) + (T3 − T4)) / 2      ← "B 시계 − A 시계" 추정
  추정 오차 = (d1 − d2) / 2  → 가는 길·오는 길이 같다고 가정한 대가.  |오차| ≤ δ / 2
```

- 공식은 RFC 5905 §8 "On-Wire Protocol" 그대로다.
- 오차 식과 상한(δ/2)은 위 공식에 `T2 = T1 + d1 + θ`, `T4 = T3 − θ + d2`를 넣어 얻은 것이다(계산).
- *clock filter 알고리즘*(RFC 5905 §10): 최근 표본 8개(`NSTAGE = 8`)를 시프트 레지스터에 담고 **δ가 가장 작은 표본**의 θ를 고른다. 지연이 작을수록 비대칭 오차의 상한(δ/2)도 작기 때문이다.
- *selection·cluster·combine*(RFC 5905 §11.2): 여러 서버의 신뢰 구간(θ ± λ)을 겹쳐 과반이 동의하는 교집합을 찾는다(Marzullo의 방법을 고친 것). 엉터리 서버 하나는 이상치로 빠진다.
- *clock discipline*(RFC 5905 §11.2.3·§11.3, Figure 27·28): 오프셋이 125 ms(`STEPT`)보다 작으면 천천히 맞추고, 125 ms 이상이면 한 번에 뛴다(step). 정상 동기 중(SYNC 상태)에는 큰 오프셋이 stepout 문턱 `WATCH`(900 s) 동안 이어진 뒤에야 step한다(망 혼잡 때 함부로 뛰지 않도록). 예외로 시계를 처음 맞추는 상태(Figure 28의 NSET·FSET)에서는 900 s를 기다리지 않고 바로 step한다. 1000 s(`PANICT`)를 넘으면 진단 메시지와 함께 프로그램을 끝내야 한다(SHOULD).
  - 이 문턱은 RFC의 참조 설계 값이다. 실제 데몬(ntpd·chrony·systemd-timesyncd)은 설정과 기본값이 다를 수 있다 `[?]`.

### 4. 윤초

```text
  UTC  23:59:58 → 23:59:59 → 23:59:60 → 00:00:00        (양의 윤초: 1분이 61초)
  POSIX 시간(윤초 없음)은 23:59:60을 표현할 수 없다
   → 커널이 1초를 되감아 23:59:59를 한 번 더 지난다  ← 벽시계가 1초 뒤로 간다
   → 또는 NTP 서버가 하루에 걸쳐 1초를 펴 바른다(leap smear)
```

- NTP 패킷의 LI(Leap Indicator) 2비트가 윤초를 예고한다. 1 = 그날 마지막 분이 61초, 2 = 59초, 3 = 시계 미동기(RFC 5905 Figure 9).
- Cloudflare 보고서: 그 순간 "시간이 1초 뒤로 간다"는 것이 사고의 근본 원인이었다.
- Google 권장 스미어: 정오부터 정오까지 24시간 **선형**으로 1초를 펴 바른다. 속도 변화는 약 11.6 ppm으로, NTP의 500 ppm 한도 안이다(Google Public NTP "Leap Smear" 문서).
- 1972년 이후 윤초는 27번 들어갔고, 마지막은 2016-12-31이다(위키백과 "Leap second", 2026 기준).

### 실험 A: 벽시계를 진짜로 3초 되감고 두 시계로 경과 시간 재기

컨테이너 안에서 `libfaketime`을 `LD_PRELOAD`로 걸어 **이 JVM의 벽시계만** 뒤로 돌렸다. `DONT_FAKE_MONOTONIC=1`로 단조 시계는 진짜 그대로 둔다. 호스트 시계는 건드리지 않는다.

```java
long w0 = System.currentTimeMillis(), m0 = System.nanoTime();
Thread.sleep(500);
setOffset("-3");                       // libfaketime 설정 파일을 원자적으로 바꿔 벽시계를 3초 되감는다
Thread.sleep(500);
long wallMs = System.currentTimeMillis() - w0;
long monoMs = (System.nanoTime() - m0) / 1_000_000;

// Cloudflare 모양: 벽시계로 잰 RTT → 이동 평균 → 가중치 무작위 선택
srtt = 0.75 * srtt + 0.25 * rtt;                        // 이동 평균(예시 계수)
ThreadLocalRandom.current().nextLong((long) srtt + 1);  // 음수 bound면 IllegalArgumentException
```

(실험, Temurin 21.0.12 컨테이너 + libfaketime 0.9.10, `FAKETIME_NO_CACHE=1`·`DONT_FAKE_MONOTONIC=1`, 2026-10-01)

```text
== A. 1초 기다리는 동안 벽시계를 3초 뒤로 되돌린다(NTP step·수동 조정 흉내)
  시작   Instant.now() = 2026-10-01T01:06:18.910206996Z
  끝     Instant.now() = 2026-10-01T01:06:16.918003124Z
  currentTimeMillis 차이 = -1991 ms | nanoTime 차이 = 1008 ms
  Duration.between(시작 Instant, 끝 Instant) 음수? true
== B. Cloudflare RRDNS(2017-01-01)와 같은 모양: RTT 이동 평균 → 가중치 무작위 선택
  [wall] 요청 1: rtt=5 ms, srtt=5.0 ms
  [wall] 요청 2: rtt=5 ms, srtt=5.0 ms
  [wall] 요청 3: rtt=-994 ms, srtt=-244.8 ms
  [wall] 요청 4: rtt=6 ms, srtt=-182.1 ms
  [wall] 요청 5: rtt=5 ms, srtt=-135.3 ms
  [wall] 요청 6: rtt=5 ms, srtt=-100.2 ms
  [wall] 가중치 선택 nextLong(-99) → IllegalArgumentException: bound must be positive
  [mono] 요청 1: rtt=6 ms, srtt=5.3 ms
  [mono] 요청 2: rtt=5 ms, srtt=5.2 ms
  [mono] 요청 3: rtt=34 ms, srtt=12.4 ms
  [mono] 요청 4: rtt=5 ms, srtt=10.5 ms
  [mono] 요청 5: rtt=5 ms, srtt=9.2 ms
  [mono] 요청 6: rtt=5 ms, srtt=8.1 ms
  [mono] 가중치 선택 nextLong(9) = 6 → 정상
```

- 관찰
  - 1초 동안 벽시계로 잰 경과는 **−1991 ms**, 단조 시계는 **1008 ms**. 같은 1초가 정반대로 나왔다. `Instant.now()`도 벽시계라 끝 시각이 시작보다 앞섰다.
  - B: 1초 되감김이 요청 3의 측정 도중 일어나 RTT −994 ms. 이동 평균이 음수로 내려가 이후 정상 표본 세 개로도 회복하지 못했다. 그 값을 `nextLong(bound)`에 넣자 `IllegalArgumentException: bound must be positive`. Go `rand.Int63n`이 음수 인자에 panic한 Cloudflare 사고와 같은 모양이다.
  - `[mono]` 요청 3의 34 ms는 시계 설정 파일을 쓰는 시간이 측정 구간에 들어가서다. 실행마다 11~34 ms였다. 음수는 한 번도 나오지 않았다.
- 시간 값은 실행마다 다르다. 벽시계 차이는 세 번 실행에서 −1991·−1984·−1978 ms였다.

### 실험 B: 이 호스트의 실제 NTP 상태

(실험, Ubuntu 호스트 systemd 255 `timedatectl timesync-status`, 2026-10-01)

```text
       Server: 91.189.91.157 (ntp.ubuntu.com)
Poll interval: 34min 8s (min: 32s; max 34min 8s)
         Leap: normal
      Version: 4
      Stratum: 2
    Precision: 1us (-24)
Root distance: 22.353ms (max: 5s)
       Offset: -19.480ms
        Delay: 188.889ms
       Jitter: 31.111ms
 Packet count: 487
    Frequency: +15.189ppm
```

- 사실 점검 때 다시 본 값(같은 호스트, 재부팅 뒤): 서버 185.125.190.56, Offset +572 µs, Delay 266.3 ms, Frequency +11.210 ppm, `Leap: normal`. 값은 볼 때마다 다르다.
- 관찰
  - 마지막 측정의 오프셋 −19.48 ms, 왕복 지연 188.9 ms. 공식상 비대칭 오차는 δ/2 ≈ 94 ms까지 가능하다. "−19 ms 어긋남"은 그 정도 폭 안의 추정이다.
  - `Frequency: +15.189ppm` — 이 기계의 진동자 속도를 그만큼 보정하고 있다는 뜻이다(드리프트).
  - `Leap: normal` — 예고된 윤초가 없다(LI = 0).
- 한계: `systemd-timesyncd`는 **SNTP만** 구현한다. 큰 어긋남은 step하고 작은 차이는 천천히 맞춘다. 완전한 NTP(여러 서버 선택·클러스터링)가 필요하면 chrony·ntpd를 쓴다(systemd-timesyncd man 페이지). 위 출력의 서버도 하나뿐이다.

### 실험 C: NTP 표본 8개, clock filter, LWW, `nbf` (시뮬레이션)

진짜 오프셋 +20.0 ms를 두고 가는 길·오는 길 지연을 다르게 준 표본 8개를 만들었다(시드 고정).

```text
== NTP 표본 8개 (진짜 오프셋 +20.0 ms, 가는 길·오는 길 지연은 매번 다르다)
  표본 | 가는 길 | 오는 길 | delta(왕복) | theta(오프셋 추정) | 추정 오차
     1 |     13 |     10 |       23.0 |              21.5 |    +1.5
     2 |     13 |     12 |       25.0 |              20.5 |    +0.5
     3 |     89 |     14 |      103.0 |              57.5 |   +37.5
     4 |     13 |     12 |       25.0 |              20.5 |    +0.5
     5 |     11 |     14 |       25.0 |              18.5 |    -1.5
     6 |     80 |     13 |       93.0 |              53.5 |   +33.5
     7 |     14 |     94 |      108.0 |             -20.0 |   -40.0
     8 |     13 |     12 |       25.0 |              20.5 |    +0.5
  8개 theta 단순 평균 = 24.1 ms (오차 +4.1)
  clock filter: delta 최소 표본의 theta = 21.5 ms (오차 +1.5)
== LWW: 노드 A 시계 +5 ms, 노드 B 시계 0 ms
  클라이언트1: A에 x=1 (진짜 1000, 타임스탬프 1005)
  클라이언트2: x=1을 읽고 B에 x=2 (진짜 1003, 타임스탬프 1003)
  복제 후 LWW(큰 타임스탬프 승) 결과: x=1  ← 나중 쓰기 x=2가 조용히 사라짐
== JWT nbf: 발급 서버 시계 +30 s
  leeway  0 s: now=1790000000, nbf=1790000030 → 거절(아직 유효하지 않음)
  leeway 60 s: now=1790000000, nbf=1790000030 → 통과
```

- 관찰
  - 추정 오차는 표마다 정확히 (가는 길 − 오는 길)/2다. 한쪽만 막힌 표본(3·6·7)은 오차가 33~40 ms로 컸다.
  - 단순 평균은 오차 +4.1 ms, 지연이 가장 작은 표본 하나를 고르는 clock filter는 +1.5 ms였다.
  - LWW: 5 ms 어긋남만으로 인과적으로 나중인 쓰기가 사라졌다. DDIA 그림 8-3(3 ms 미만 어긋남에서 증가 연산 유실)과 같은 모양이다.
  - `nbf`: RFC 7519 §4.1.5는 시계 어긋남을 위한 "보통 몇 분 이하의 작은 여유(leeway)"를 둘 수 있다고 한다(MAY).

## 쓰이는 자료구조·알고리즘

- **NTP clock filter**: 8단 시프트 레지스터에 (θ, δ, ε, t) 표본 → δ 오름차순 정렬 → 첫 표본 채택. 지터는 나머지 표본과의 RMS 차(RFC 5905 §10).
- **NTP selection(교집합)**: 각 서버의 구간 [θ−λ, θ+λ] 끝점을 정렬해 과반이 겹치는 구간을 찾는다(Marzullo 계열, RFC 5905 §11.2.1). 구간 스케줄링·스위프 라인과 같은 모양이다.
- **이동 평균(EWMA)**: `srtt = (1−α)·srtt + α·rtt`. 이상치 하나가 오래 남는다(실험 A-B). TCP RTT 추정도 같은 꼴이다([network/16](../../network/16-tcp-reliability-retransmission/2-summary.md)).
- **오차 구간 시간(TrueTime)**: 시각을 [earliest, latest]로 다룬다. 26번.
- **논리 시계**: 순서만 필요하면 물리 시계 대신 카운터를 쓴다. [05-logical-clocks](../05-logical-clocks/2-summary.md) 또는 [ops-patterns/14-logical-clock](../../ops-patterns/14-logical-clock/2-summary.md).

## 적용 — 풀어나가는 법

1. **질문을 분류한다.** "얼마나 걸렸나" → 단조 시계. "지금 몇 시" → 벽시계. 두 기계 사이의 순서 → 물리 시계로 정하지 않는다(논리 시계·버전·리더가 부여한 번호).
2. **경과 시간·타임아웃은 `nanoTime`으로.** 벽시계 차이를 쓸 수밖에 없으면 음수 검사를 넣는다(Cloudflare의 수정 방향).
3. **시계를 주입한다.** `java.time.Clock`을 받아 테스트에서 뒤로 돌리는 경우를 시험한다.
4. **다른 기계가 만든 시각을 비교할 때는 여유를 둔다.** JWT `nbf`·`exp`·`iat`, 인증서 유효 기간, lease 만료.
5. **어긋남을 감시하고, 너무 벌어진 노드는 뺀다.** 동기화된 시계를 가정하는 소프트웨어라면 필수다(DDIA 8장).

```java
// 경과 시간: 단조 시계
long start = System.nanoTime();
callUpstream();
long elapsedNanos = System.nanoTime() - start;            // 벽시계가 뛰어도 음수가 안 된다

// 시각이 필요한 로직: Clock 주입 (테스트에서 Clock.offset으로 되감기를 재현)
class TokenVerifier {
    private final Clock clock;
    private final Duration leeway = Duration.ofSeconds(60);
    TokenVerifier(Clock clock) { this.clock = clock; }
    boolean notYetValid(Instant nbf) {
        return Instant.now(clock).plus(leeway).isBefore(nbf); // 여유를 둔 비교
    }
}
// 테스트: new TokenVerifier(Clock.offset(Clock.systemUTC(), Duration.ofSeconds(-30)))
```

진단 명령·지표:
- 이 기계의 동기 상태: `timedatectl timesync-status`(systemd-timesyncd), `chronyc tracking`·`chronyc sources -v`(chrony), `ntpq -p`(ntpd)
- 노드 간 비교: 여러 노드에서 `date -u +%s.%N`을 동시에 찍어 차이를 본다(대략값 — 명령 지연 포함).
- 지표: node_exporter `node_timex_offset_seconds`, `node_timex_sync_status`, `node_timex_maxerror_seconds`
- 윤초 예고: NTP 응답의 LI 필드(`timedatectl`의 `Leap:`)

## 장애 시나리오와 대처

### 1. 벽시계로 경과 시간 계산 → 음수 duration → panic (⚠ 커리큘럼)

- **현상**: 윤초·NTP step·수동 시간 변경 순간에 서비스 일부가 오류를 낸다.
- **보이는 형태**(Cloudflare 2017-01-01 사고 보고서 원문): 00:00 UTC에 영향 시작. CNAME 조회 경로에서 RRDNS가 panic(Go `recover`로 잡힘). 정점에 Cloudflare DNS 질의의 약 0.2%, HTTP 요청의 1% 미만이 오류. 영향 받은 머신은 102개 데이터센터 중 일부. 가장 영향이 큰 머신은 90분 안에 패치, 06:45 UTC에 전 세계 수정 완료.
- **원인**: `time.Now().Sub(start)`가 음수가 될 수 있는데 "최악이 0"이라고 가정했다. 음수 RTT가 이동 평균으로 쌓였고 `rand.Int63n(음수)`가 panic했다. 실험 A에서 Java로 같은 모양을 재현했다(`IllegalArgumentException: bound must be positive`).
- **대처**: 경과 시간은 단조 시계로(Go 1.9 이후 `time.Now()`는 단조 시계를 함께 담는다, Java는 `nanoTime`). 시간 차이를 쓰는 곳에 음수 방어. Cloudflare는 시간이 뒤로 가면 업스트림 성능 기록을 버리고 다시 쌓게 고쳤다.

### 2. 시계 어긋남 → JWT `nbf`·인증서 거절 (⚠ 커리큘럼)

- **현상**: 특정 서버에서만 "토큰이 아직 유효하지 않음", "인증서가 아직 유효하지 않음" 오류가 난다. 재시도하면 몇 초 뒤엔 통과하기도 한다.
- **보이는 형태**: JWT 라이브러리의 `nbf`/`iat` 관련 예외, TLS의 `certificate is not yet valid`류 오류. 해당 노드의 NTP 오프셋이 크다.
- **원인**: 발급자 시계가 빠르거나 검증자 시계가 느리다(실험 C: 30초 어긋남 + leeway 0 → 거절).
- **대처**: 양쪽 NTP 정상화가 근본. 검증 쪽에 몇 분 이하의 leeway(RFC 7519가 허용). 인증서 유효 기간 검사는 [network/30-x509-and-chain-validation](../../network/30-x509-and-chain-validation/2-summary.md).

### 3. 시계 어긋남 → LWW 역전, 쓰기가 조용히 사라짐 (⚠ 커리큘럼)

- **현상**: 사용자가 바꾼 값이 가끔 되돌아간다. 오류 로그는 없다.
- **보이는 형태**: 같은 키에 대해 나중에 쓴 값의 타임스탬프가 앞선 값보다 작다. 시계가 빠른 노드를 거친 쓰기가 계속 이긴다.
- **원인**: 타임스탬프가 각 노드의 벽시계에서 나온다. 빠른 노드의 쓰기는 느린 노드가 그 차이만큼 시간이 지나기 전까지 덮이지 않는다(DDIA 8장, 실험 C에서 5 ms 어긋남으로 재현). Cassandra 같은 리더리스 DB가 LWW를 쓴다고 DDIA가 예로 든다.
- **대처**: 인과 관계가 중요한 값은 LWW를 피한다(버전 벡터·CRDT, 24번). 조건부 쓰기(CAS·버전 번호). 시계 어긋남 감시.

### 4. NTP가 조용히 막힘 → 시계가 천천히 벌어짐

- **현상**: 몇 주 동안 아무 문제 없다가 로그 순서가 어긋나고, 토큰 만료가 이상하고, 일별 집계가 경계에서 틀린다.
- **보이는 형태**: `timedatectl`에 동기 안 됨, 마지막 동기 시각이 오래전. 커널의 최대 오차 추정 `node_timex_maxerror_seconds`가 초당 0.5 ms씩 커지다가 16 s에서 멈추고, 그때 `node_timex_sync_status`가 0이 된다(Linux `kernel/time/ntp.c`: `MAXFREQ` 500 µs/s, 상한 `NTP_PHASE_LIMIT`에서 `STA_UNSYNC`).
  - `node_timex_offset_seconds`는 커널이 데몬에게서 받은 **보정 오프셋**이다. NTP가 끊기면 새로 재지 않으므로 실제 어긋남을 따라 커지지 않는다. 이 값만 보면 놓친다.
- **원인**: 방화벽 변경으로 NTP(UDP 123)가 막혔는데 아무도 몰랐다. DDIA 8장은 이런 일이 실제로 일어난다는 증거가 있다고 쓴다. 드리프트 200 ppm이면 하루 17초까지 벌어질 수 있다.
- **대처**: 동기 실패(`sync_status`)·마지막 동기 시각·`maxerror` 알람, 오프셋 알람. 어긋남이 큰 노드는 클러스터에서 빼도록 한다(DDIA 8장). NTP 서버를 여러 개 둔다.

## 핵심 문장

- 경과 시간은 단조 시계(`nanoTime`, `CLOCK_MONOTONIC`)로, 시각은 벽시계로 잰다. 벽시계는 뒤로 갈 수 있다.
- 실험에서 벽시계를 3초 되감자 1초 경과가 −1991 ms로, 단조 시계로는 1008 ms로 나왔다.
- NTP는 왕복 네 타임스탬프로 오프셋을 추정한다. 가는 길·오는 길이 다르면 오차는 최대 왕복 지연의 절반이다. 그래서 지연이 가장 작은 표본을 고른다.
- 벽시계 값은 한 점이 아니라 오차 구간이다. 인터넷 NTP로는 수십 ms 단위 오차가 보통이다.
- 다른 기계의 벽시계로 이벤트 순서를 정하면 어긋남만큼 나중 쓰기가 사라질 수 있다(LWW). 순서는 논리 시계로 정한다.
- 시계 어긋남은 크게 터지지 않고 조용히 데이터를 잃는다. 오프셋을 감시하고, 비교에는 여유를 둔다.

## 관련 주제·근거

- 선행
  - [02-system-and-failure-models](../02-system-and-failure-models/2-summary.md) — 시간 가정, 프로세스 멈춤
- 후속
  - [05-logical-clocks](../05-logical-clocks/2-summary.md) — 물리 시계 대신 인과 순서
  - [26-hybrid-clocks-and-truetime](../26-hybrid-clocks-and-truetime/2-summary.md) — 오차 구간과 commit wait
  - [24-conflict-resolution-and-crdt](../24-conflict-resolution-and-crdt/2-summary.md) — LWW와 그 대안(버전 벡터·CRDT)
- 연결
  - [database/27-temporal-types-and-session-timezone](../../database/27-temporal-types-and-session-timezone/2-summary.md) — DB 시각 타입·시간대
  - [network/30-x509-and-chain-validation](../../network/30-x509-and-chain-validation/2-summary.md) — 인증서 유효 기간 검사
  - [network/16-tcp-reliability-retransmission](../../network/16-tcp-reliability-retransmission/2-summary.md) — RTT 이동 평균
  - [ops-patterns/14-logical-clock](../../ops-patterns/14-logical-clock/2-summary.md)
- 근거
  - DDIA 1판 8장 "Unreliable Clocks" — "Monotonic Versus Time-of-Day Clocks", "Clock Synchronization and Accuracy"(200 ppm, 0.05%, 방화벽, 윤초·스미어, VM), "Relying on Synchronized Clocks"(그림 8-3 LWW, 신뢰 구간)
  - RFC 5905 "Network Time Protocol Version 4" — §8 On-Wire Protocol(θ·δ), §10 Clock Filter Algorithm(NSTAGE 8), §11.2 Selection/Cluster/Combine, §11.3 Clock Discipline(STEPT 125 ms, PANICT 1000 s), Figure 9 Leap Indicator <https://www.rfc-editor.org/rfc/rfc5905>
  - RFC 7519 §4.1.4–4.1.5(`exp`·`nbf` leeway) <https://www.rfc-editor.org/rfc/rfc7519>
  - Cloudflare, "How and why the leap second affected Cloudflare DNS"(2017-01-01 사고) <https://blog.cloudflare.com/how-and-why-the-leap-second-affected-cloudflare-dns/>
  - Linux man-pages `clock_gettime(2)` — `CLOCK_REALTIME`·`CLOCK_MONOTONIC`·`CLOCK_MONOTONIC_RAW`·`CLOCK_BOOTTIME`
  - Java SE 21 API `System.nanoTime()`·`System.currentTimeMillis()` <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/System.html>
  - Go 1.9 Release Notes "Transparent Monotonic Time support" <https://go.dev/doc/go1.9>
  - Google Public NTP "Leap Smear"(24시간 선형, 11.6 ppm, NTP 500 ppm 최대) <https://developers.google.com/time/smear>
  - systemd-timesyncd man 페이지(systemd 255) — SNTP만 구현
  - Prometheus node_exporter `collector/timex.go` — `node_timex_*` 지표
- 실험 목록
  - `WallVsMono.java` — libfaketime 0.9.10로 JVM의 벽시계만 3초·1초 되감기, `currentTimeMillis`·`Instant`·`nanoTime` 경과 비교, Cloudflare 모양(이동 평균 → `nextLong`) 재현. 전용 일회용 컨테이너 `sn-dw-w01-ft`(Temurin 21.0.12 + apt로 libfaketime 설치), 실험 후 삭제.
  - `timedatectl timesync-status` — 이 호스트의 실제 NTP(SNTP) 오프셋·지연·주파수 보정.
  - `ClockSkew.java` — NTP θ·δ와 clock filter, LWW 역전, JWT `nbf` leeway 시뮬레이션(시드 고정). Temurin 21.0.12.
