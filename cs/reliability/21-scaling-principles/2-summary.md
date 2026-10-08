# reliability/21-scaling-principles — 확장의 원리: 병목 이동·Little's Law·USL·무상태화 — 정리 (힌트)

## 해결하는 문제

"트래픽이 늘었으니 서버를 늘리자"가 통하지 않는 경우가 많다.\
서버를 2배로 늘렸는데 처리량이 그대로이거나, 오히려 줄어든다.

쉬운 예: 마트 계산대다.
- 계산대(병렬 구간)를 늘리면 줄이 빨리 준다.
- 그런데 출구에 영수증 검사원이 한 명(직렬 구간)이면, 계산대를 아무리 늘려도 검사원 속도에서 막힌다.
- 계산대끼리 "지금 몇 번 손님 받았어?"를 매번 서로 물어봐야 한다면(조율), 계산대가 많을수록 묻는 시간이 늘어 오히려 느려진다.

똑같은 구조다.\
실무 예: 앱 서버를 늘렸더니 DB 커넥션이 먼저 바닥난다. 분산 락·캐시 무효화 브로드캐스트를 쓰는 서비스는 노드를 늘리자 처리량이 꺾인다. 인메모리 스케줄러는 인스턴스 수만큼 같은 잡을 돌린다.

이 노트는 세 질문에 숫자로 답하는 법을 다룬다.
1. 지금 병목은 어디인가 → 병목 이동
2. 동시에 몇 건을 붙잡고 있어야 하나 → Little's Law
3. 늘리면 얼마나 늘어나나, 어디서 꺾이나 → USL

기초 설명(병목 후보 훑는 순서, 무상태화 체크리스트, 확장 전에 할 일)은 원본 [server-design/01-scaling-principles](../../systems/server-design/01-scaling-principles.md) §1·§4·§5에 있다. 여기서는 짧게 잇고, 식이 성립하는 조건과 실험을 보탠다.

## 동작·원리

### 1. 병목은 없어지지 않고 옮겨 간다

```text
 요청 ──> [LB] ──> [앱 ×N] ──> [커넥션 풀 ×N] ──> [DB 1대] ──> [디스크]
                     ↑ 늘림         ↑ 여기가 먼저 참     ↑ 그다음 여기
 앱을 늘림 → 병목이 커넥션 풀로 → 풀을 늘림 → DB CPU로 → 복제본 → 쓰기(주 DB)로 → 샤딩 → 샤드 간 쿼리로
```

- *병목(bottleneck)*: 전체 처리량을 정하는 가장 좁은 구간.
- 병목 자원의 처리량 한계가 시스템 전체의 한계다. 병목 자원이 한 건에 쓰는 시간을 D라 하면 처리량 X는 1/D를 넘지 못한다(한 번에 한 건만 처리하는 자원 — 락·단일 디스크 같은 경우. 같은 일을 동시에 m건 처리하는 자원이면 상한은 m/D).
  - 이것은 이용률 식(U = X × D, U ≤ 1)에서 바로 나온다. 아래 실험의 contention 모드가 이 상한에 붙는다.
- 그래서 확장을 말할 때 첫 질문은 "지금 병목이 어디인가"다(원본 §1).

### 2. Little's Law — 동시 건수 = 도착률 × 체류 시간

```text
      도착 λ (건/초)                         떠남 λ (안정 상태면 들어온 만큼 나간다)
  ───────────────>  ┌──────────────────┐  ───────────────>
                    │ 시스템 안에 평균 L건 │
                    │ 한 건이 평균 W초 머묾 │
                    └──────────────────┘
                 L = λ × W
```

- *Little's Law*: 안정 상태에서 시스템 안의 평균 건수 L은 도착률 λ와 평균 체류 시간 W의 곱이다(Little 1961, "A Proof for the Queuing Formula: L = λW").
  - 도착 분포·서비스 시간 분포·처리 순서와 무관하다. 그래서 어디에나 쓴다.
  - 조건은 "장기 평균이 존재한다"(들어온 만큼 나간다)는 것이다. 큐가 끝없이 자라는 과부하 구간에서는 L이 수렴하지 않는다.
- 쓰는 법 셋
  - 풀 크기: 목표 λ = 1,000 req/s, W = 0.2초 → 평균 200건이 동시에 처리 중이다(예시). 스레드가 요청 하나를 끝까지 붙잡는 구조라면 200은 필요한 스레드 수의 하한이다 — 정확히 200개면 이용률 1이라 대기열이 발산하므로 여유를 둔다(지수 서비스 가정 Erlang C 계산: 210개면 평균 대기 7.5 ms, 220개면 1.1 ms — [math/10-queueing-and-littles-law](../../math/10-queueing-and-littles-law/2-summary.md) §4).
  - 대기 시간 역산: 큐에 10,000건, 처리율 100 건/s → 앞선 건부터 처리하는(FIFO) 큐이고 처리율이 그대로라면 지금 넣은 건은 약 100초 뒤에 나온다(원본 §2). Little's Law는 평균의 관계라서 한 건의 시각은 이런 가정 아래의 추정이다.
  - 측정 검증: λ, W, L을 각각 재서 L ≈ λW인지 본다. 안 맞으면 측정이 틀렸거나(샘플링·누락) 안정 상태가 아니다.
- JEP 444(가상 스레드)도 서버 확장성을 이 법칙으로 설명한다. 지연이 같다면 처리량을 10배 하려면 동시 처리 건수도 10배가 돼야 한다.

### 3. USL — 늘릴수록 얼마나 느는가

```text
 처리량 X(N)
   │            ideal (α=β=0): 직선
   │          ／
   │        ／    ___________ α만 있음: 1/α로 수렴(Amdahl)
   │      ／ __---
   │    ／_-      ‾‾--__
   │  ／-               ‾‾--__  β>0: 정점 뒤 꺾임(retrograde)
   │／                        ‾‾--
   └──────────────────────────────── N (노드·스레드·사용자 수)
                  ↑ N_max = √((1−α)/β)
```

```text
              N
 C(N) = ───────────────────────     C(N) = X(N)/X(1) (상대 처리량)
         1 + α(N−1) + βN(N−1)
```

- *USL(Universal Scalability Law)*: Gunther의 확장성 모델. 세 C로 설명한다(perfdynamics.com USL 페이지).
  - *동시성(concurrency)*: 이상적 병렬. 분자 N.
  - *경합(contention, α)*: 공유 자원을 기다리는(줄 서는) 비용. 락·단일 DB·단일 리더.
  - *일관성(coherency, β)*: 자원끼리 데이터를 맞추느라 드는 지연. 점대점 교환이라 항이 N(N−1)에 비례한다.
- β = 0이고 γ = 1이면 Amdahl의 법칙과 같은 식이 된다(같은 페이지 식 (3)의 NOTE).
  - *γ*: 같은 페이지 식 (3)의 처리량 비례 상수(X(1) = γ). 위 C(N)은 X(1)로 나눈 상대값이라 γ가 빠져 있다.
- β > 0이면 처리량이 정점 N_max = √((1−α)/β)를 지나 **줄어든다**. 이것이 "늘렸더니 느려졌다"의 모양이다.
- N은 하드웨어 수(프로세서·노드)일 수도, 고정 하드웨어 위의 부하(사용자 수)일 수도 있다. Gunther는 둘을 같은 동전의 양면이라고 적는다.
- USL은 곡선을 점마다 맞추는 도구가 아니다. 측정 몇 점으로 α·β를 추정해 "어디서 꺾일지"와 "무엇이 원인인지(α냐 β냐)"를 가늠한다.

### 4. 실험: 경합과 조율이 처리량을 어떻게 바꾸나 + Little's Law 확인

- 노드 N개(스레드)가 닫힌 루프로 요청을 처리한다. 한 요청 = 아래 구간들.
  - parallel: 2ms 대기(`LockSupport.parkNanos` — CPU를 쓰지 않는 I/O 흉내)
  - contention: + 전역 락 안에서 0.1ms(α 흉내)
  - coherence: + 다른 노드마다 그 노드의 락을 잡고 0.02ms(β 흉내 — 노드 수만큼 할 일이 늘고, 서로의 락에서 부딪친다)
- 2초씩 재서 처리량, 평균 체류 시간 W, 그리고 1ms마다 센 진행 중 건수의 평균 L을 낸다.
- 코드 핵심(전체는 실험 목록의 경로):

```java
while (System.nanoTime() < end) {
    long t0 = System.nanoTime();
    inFlight.incrementAndGet();
    LockSupport.parkNanos(WORK_NS);                                      // 병렬 구간
    if (!mode.equals("parallel")) {
        global.lock(); try { LockSupport.parkNanos(SERIAL_NS); } finally { global.unlock(); }   // α
    }
    if (mode.equals("coherence")) {
        for (int j = 0; j < n; j++) {
            if (j == me) continue;
            peer[j].lock(); try { LockSupport.parkNanos(PEER_NS); } finally { peer[j].unlock(); } // β
        }
    }
    inFlight.decrementAndGet();
    latSum.addAndGet(System.nanoTime() - t0);
    done.incrementAndGet();
}
```

(실험, JDK 21.0.12 temurin, Docker `--cpus=2`, 2026-10-01 — 처리량은 실행마다 수 % 다르다. 첫 실행 출력. 사실 점검 재실행 포함 3회)

```text
== 모드: parallel
   N   처리량(req/s)  C(N)=X(N)/X(1)   W 평균(ms)   λ×W     측정 L
   1          472       1.00            2.11     0.99     0.99
   2          953       2.02            2.10     2.00     2.00
   4         1901       4.03            2.10     3.99     3.99
   8         3813       8.08            2.10     7.99     7.98
  16         7652      16.21            2.09    15.98    15.97
  32        15367      32.56            2.08    31.92    31.95
  64        30832      65.32            2.07    63.77    63.93
== 모드: contention
   N   처리량(req/s)  C(N)=X(N)/X(1)   W 평균(ms)   λ×W     측정 L
   1          441       1.00            2.27     1.00     1.00
   2          882       2.00            2.27     2.00     2.00
   4         1738       3.94            2.30     4.00     4.00
   8         3502       7.95            2.28     8.00     7.99
  16         5006      11.36            3.20    15.99    15.99
  32         5042      11.45            6.35    32.00    32.00
  64         5016      11.39           12.76    64.00    64.00
   USL 적합: α=0.0270 β=0.00073 → 처리량 정점 N*=sqrt((1-α)/β)=36.4
== 모드: coherence
   N   처리량(req/s)  C(N)=X(N)/X(1)   W 평균(ms)   λ×W     측정 L
   1          441       1.00            2.27     1.00     1.00
   2          850       1.93            2.35     2.00     2.00
   4         1584       3.59            2.53     4.00     4.00
   8         2812       6.38            2.85     8.00     8.00
  16         4412      10.00            3.63    16.00    16.00
  32         3358       7.61            9.53    32.00    32.00
  64         1493       3.38           44.36    66.20    63.99
   USL 적합: α=-0.0566 β=0.00531 → 처리량 정점 N*=sqrt((1-α)/β)=14.1
```

- 관찰 1 — parallel: N을 64배로 늘리자 처리량도 약 65배다. 대기만 하는 일은 2코어 제한에서도 선형으로 는다.
- 관찰 2 — contention: N=16부터 약 5,000 req/s에서 멈춘다. 그 뒤로는 N을 늘려도 W만 길어진다(16 → 64에서 3.2ms → 12.8ms).
  - 해석: 전역 락이 병목 자원이다. 처리량 상한 약 5,000/s에서 역산하면 락 한 번 점유가 약 0.2ms다. `parkNanos(0.1ms)`가 실제로는 더 길게 잔 것이다.
  - 이 모드는 USL의 매끄러운 수렴보다 "병목 자원 상한(X ≤ 1/D)"에 가깝다. 그래서 β도 0이 아닌 값으로 적합됐다. 모형은 근사다.
- 관찰 3 — coherence: N=16에서 정점(4,412·4,450), 32에서 3,358·3,657, 64에서 1,493·1,543으로 **줄었다**. USL 적합 정점 N* ≈ 13~14와 맞는다.
  - α가 음수로 나온 것은 이 흉내가 USL의 가정과 정확히 같은 모양이 아니어서 생긴 적합 오차다(해석). 판단에 쓰는 것은 β > 0과 정점 위치다.
- 관찰 4 — Little's Law: coherence N=64 한 행을 빼면 λ×W와 측정 L이 소수 둘째 자리까지 거의 같다. 닫힌 루프라 L = N이다. 그래서 W = N / X로 처리량에서 지연을 바로 계산할 수 있다(contention N=64: 64 / 5,016 = 12.76ms).
  - coherence N=64의 λ×W 66.2 vs L 64.0은 측정 끝에 걸친 요청 몇 건이 만든 차이다(2초 창에 비해 W 44ms가 길다 — 해석).
- 두 번째 실행: contention 정점 5,127/s, coherence N=16 4,450 → N=64 1,543, 적합 N* 14.2. 모양이 같다.
- 세 번째 실행(사실 점검 재실행, 같은 조건): contention N=16 4,849 → 64 5,067, coherence N=16 4,480 → 64 1,310, 적합 N* 13.0. 3회 범위는 contention 평탄 구간 약 4,850~5,130/s, coherence 정점 뒤 N=64 1,310~1,543/s, 적합 N* 13.0~14.2다.

### 5. 상태가 확장을 막는다 — 무상태화

```text
 상태를 인스턴스 안에 둠                    상태를 밖으로 밀어냄
 [앱1: 세션 A]  [앱2: 세션 B]              [앱1] [앱2] [앱3]   ← 누구나 같은 요청을 처리
   ↑ A는 앱1로만 가야 함                       └──┬──┘
   ↑ 앱1이 죽으면 A 로그아웃                 [세션 저장소·DB·오브젝트 스토리지]
```

- *무상태(stateless)*: 요청을 처리하는 데 필요한 상태를 인스턴스 안에 두지 않는 것. 그래야 LB가 아무 인스턴스에 보내도 된다.
- 상태는 사라지지 않는다. 앱 계층에서 빼서 그 일을 잘하는 저장소로 밀어낸다. 그래서 확장의 어려움은 결국 데이터 계층으로 모인다(원본 §4).
- 체크리스트(세션·로컬 파일·인메모리 캐시·인메모리 스케줄러·로컬 락·인메모리 카운터)는 원본 §4 표.
- USL로 다시 보면: 밀어낸 상태 저장소가 α(경합)가 되고, 인스턴스끼리 상태를 맞추는 일(캐시 무효화 방송·분산 락)이 β가 된다.

## 쓰이는 자료구조·알고리즘

- **큐(대기열)** — Little's Law의 "시스템". 처리 중 + 대기 중을 합친 것이 L이다. 이용률이 1에 가까우면 대기가 비선형으로 는다(M/M/1에서 시스템 안 평균 건수 = ρ/(1−ρ) — 표준 대기행렬 결과). 수학 기초는 [math/10-queueing-and-littles-law](../../math/10-queueing-and-littles-law/2-summary.md)(원본은 [server-design/01](../../systems/server-design/01-scaling-principles.md) §2).
- **USL 적합 = 최소제곱 회귀** — 식을 N/C(N) − 1 = α(N−1) + βN(N−1)로 바꾸면 α·β에 대해 선형이다. 측정 점 4~6개로 두 계수를 푼다(실험 코드의 `fit`).
- **락·직렬 구간** — α의 실체. [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md).
- **해시 파티셔닝** — 조율이 필요 없게 데이터를 나눠 β를 없앤다. [database/33-partitioning-and-sharding](../../database/33-partitioning-and-sharding/2-summary.md).
- **이동 평균·샘플링** — L을 재는 법(일정 간격으로 진행 중 건수를 세어 평균). 실험은 1ms 샘플링.

## 적용 — 풀어나가는 법

### 1. 순서

1. **병목을 찾는다.** 자원(CPU·메모리·디스크·네트워크) → 슬롯(스레드·커넥션·FD) → 직렬 구간(락·단일 리더·단일 파티션) → 외부 한도(서드파티 레이트 리밋) 순으로 훑는다(원본 §1). 방법론은 [20-performance-method-and-amdahl](../20-performance-method-and-amdahl/2-summary.md).
2. **Little's Law로 필요한 동시성을 계산한다.** 피크 λ × 부하 상태의 W. W는 하류가 느려지면 커진다는 것을 같이 적는다.
3. **확장 실험을 한다.** N을 1, 2, 4, 8, … 로 늘리며 처리량을 잰다. 세 점 이상에서 USL을 적합해 β가 0보다 큰지, N_max가 어디인지 본다.
4. **α면 직렬 구간을 줄이고, β면 조율을 없앤다.** α: 락 범위 축소, 샤딩, 큐로 직렬화. β: 파티셔닝, 비동기·최종적 일관성, 브로드캐스트 제거.
5. **상태를 밖으로 밀어낸다.** 체크리스트를 돌고, 밀어낸 저장소가 새 병목이 되는지 1번으로 돌아간다.

### 2. 풀 크기 계산 (Java)

```java
/** Little's Law로 필요한 동시 처리 수를 구하고, 인스턴스 수로 나눈다. 모든 숫자는 측정값을 넣는다. */
static int threadsPerInstance(double peakRps, double wSecondsUnderLoad, int instances, double headroom) {
    double l = peakRps * wSecondsUnderLoad;            // L = λW
    return (int) Math.ceil(l * (1 + headroom) / instances);
}
// 예시: 피크 1,000 req/s, 부하 상태 평균 0.2초, 인스턴스 4대, 여유 30% → 65
```

- 스레드를 늘리기 전에, 그 스레드가 붙잡는 하류 자원(DB 커넥션)의 **총합**을 본다. 인스턴스 수 × 인스턴스당 풀 크기가 DB 한도를 넘으면 병목이 DB로 옮겨 갈 뿐이다([database/21-connection-pooling](../../database/21-connection-pooling/2-summary.md)).

### 3. 운영 지표로 Little's Law 검증 (PromQL 예)

```text
# λ: 초당 요청 (Micrometer가 Prometheus로 내보내는 타이머 이름 예)
sum(rate(http_server_requests_seconds_count[5m]))
# W: 평균 체류 시간
sum(rate(http_server_requests_seconds_sum[5m])) / sum(rate(http_server_requests_seconds_count[5m]))
# λ × W 를, 앱이 따로 내보내는 "진행 중 요청 수" 게이지의 평균과 비교한다(게이지 이름은 라이브러리마다 다르다)
```

- 둘이 크게 다르면: 측정 누락(타이머가 일부 경로만 잼), 큐에서 기다린 시간이 W에 안 들어감, 안정 상태가 아님 중 하나다.

### 4. USL 적합 (Java — 실험 코드 발췌)

```java
// y = N/C - 1, x1 = N-1, x2 = N(N-1) 로 절편 없는 2변수 최소제곱
double det = s11 * s22 - s12 * s12;
double alpha = (sy1 * s22 - sy2 * s12) / det, beta = (s11 * sy2 - s12 * sy1) / det;
double nMax = Math.sqrt((1 - alpha) / beta);
```

## 장애 시나리오와 대처

### 1. 인스턴스를 늘렸는데 처리량이 역전 (⚠ USL 역행)

- 현상: 피크 대비 8대 → 16대로 늘렸더니 처리량이 줄고 지연이 늘었다.
- 보이는 형태: 인스턴스당 CPU는 낮은데 p99가 오른다. 분산 락 대기 시간, 캐시 무효화 메시지 수, 노드 간 RPC 수가 노드 수보다 빠르게 는다. 실험 coherence의 N=16 → 32 → 64 모양.
- 원인: 경합(α)·일관성 비용(β). 노드끼리 상태를 맞추는 일이 N(N−1)로 는다.
- 대처: N을 정점 아래로 되돌려 완화한다. 근본은 조율을 없애는 것 — 키로 파티셔닝해 한 키는 한 노드만 쓰게, 전체 브로드캐스트를 대상 지정으로, 강한 일관성이 필요 없는 곳은 비동기로.

### 2. 앱을 늘렸더니 DB가 먼저 죽는다 (병목 이동)

- 현상: 오토스케일로 앱이 20대에서 50대가 된 직후 DB 연결 오류가 쏟아진다.
- 보이는 형태: DB 쪽 `too many connections`류 오류, 앱 쪽 커넥션 획득 타임아웃. DB CPU·커넥션 수가 앱 수에 비례해 뛴다.
- 원인: 병목이 앱에서 DB 커넥션으로 옮겨 갔다. 인스턴스 수 × 풀 크기 총합이 DB 한도를 넘었다.
- 대처: 커넥션 총량 상한을 설계값으로 둔다(인스턴스당 풀 축소, PgBouncer 같은 풀러). 오토스케일 최대치를 DB 한도에서 역산한다([41-autoscaling](../41-autoscaling/2-summary.md)).

### 3. 하류가 느려지자 스레드풀이 바닥남 (Little's Law 오산)

- 현상: 평소 W = 50ms로 풀 크기를 정했는데, 하류 지연이 500ms가 되자 요청이 줄을 선다.
- 보이는 형태: 풀의 활성 스레드 = 최대치, 큐 길이 증가, 모든 엔드포인트 지연 동반 상승(느린 하류와 무관한 것까지).
- 원인: λ가 같아도 W가 10배면 L도 10배다. 풀 크기는 평소 W로 정해서 부족해졌다.
- 대처: 하류 호출에 타임아웃을 둬서 스레드가 하류에 붙잡히는 시간(이 장애에서 W를 늘린 몫)에 상한을 만든다. 큐 대기까지 묶으려면 요청 전체 기한을 둔다([08-time-budget-allocation](../08-time-budget-allocation/2-summary.md)). 하류별로 풀을 나눈다(벌크헤드 — [28-bulkhead](../28-bulkhead/2-summary.md)). 대기열에 상한을 두고 넘치면 거절한다([12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md)).

### 4. 수평 확장 후 같은 잡이 N번 돈다 (상태가 인스턴스 안에 있음)

- 현상: 인스턴스를 3대로 늘린 다음 날, 정산 메일이 세 통씩 나갔다.
- 보이는 형태: 같은 시각에 인스턴스마다 같은 잡 시작 로그.
- 원인: 인메모리 스케줄러가 인스턴스마다 돈다. 무상태화 체크리스트의 한 줄이다.
- 대처: 스케줄을 한 곳(리더·분산 락·외부 스케줄러)에서만 돌린다. 잡 자체를 멱등으로 만든다([30-scheduler-and-cron-ha](../30-scheduler-and-cron-ha/2-summary.md)).

### 5. 늘려도 그대로인 단일 핫 파티션

- 현상: 소비자를 늘렸는데 특정 키의 처리 지연만 그대로다.
- 보이는 형태: 한 파티션(샤드)의 지연·적재량만 높고 나머지는 한가하다.
- 원인: 직렬 구간이 키 하나에 묶여 있다. 그 키는 한 곳에서만 처리되므로 N과 무관하다(α가 1에 가까운 부분).
- 대처: 핫 키를 쪼갠다(키에 접미사, 집계는 나중에 합침). 순서가 꼭 필요한 범위를 좁힌다.

## 핵심 문장

- 확장은 병목을 없애지 않고 옮긴다. 병목 자원이 한 건에 쓰는 시간 D가 처리량 상한 1/D를 정한다(한 번에 한 건 처리하는 자원 기준, 동시에 m건이면 m/D).
- Little's Law L = λW는 분포와 무관하게 안정 상태에서 성립한다. 풀 크기 계산과 측정 검증에 쓴다. 실험에서 λ×W와 측정 L이 한 행(측정 창 끝에 걸친 요청 — 66.2 vs 64.0)을 빼고 거의 같았다.
- USL은 경합(α)과 일관성 비용(β)으로 확장 곡선을 설명한다. β > 0이면 정점 √((1−α)/β)를 지나 처리량이 줄어든다. 실험의 조율 모드는 N=16 정점 뒤 N=64에서 처리량이 약 1/3로 줄었다.
- α는 직렬 구간을 줄여서, β는 조율 자체를 없애서(파티셔닝) 고친다.
- 상태는 없애는 게 아니라 인스턴스 밖으로 밀어내는 것이다. 밀어낸 저장소가 다음 병목이 된다.

## 관련 주제·근거

- 선행
  - [math/10-queueing-and-littles-law](../../math/10-queueing-and-littles-law/2-summary.md) (원본 [server-design/01](../../systems/server-design/01-scaling-principles.md) §2가 Little's Law 절)
  - 원본 [server-design/01-scaling-principles](../../systems/server-design/01-scaling-principles.md) — 병목 후보 순서, 무상태화 체크리스트, 확장 전에 할 일, 확장성을 말하는 방식
- 후속·연결
  - [22-capacity-and-load-testing](../22-capacity-and-load-testing/2-summary.md) — 이 원리로 사이징하고 부하 테스트로 확인
  - [19-performance-measurement](../19-performance-measurement/2-summary.md) · [20-performance-method-and-amdahl](../20-performance-method-and-amdahl/2-summary.md)
  - [39-async-io-gains-and-limits](../39-async-io-gains-and-limits/2-summary.md) — Little's Law로 본 가상 스레드
  - [41-autoscaling](../41-autoscaling/2-summary.md) — 늘리는 일을 자동으로
  - [database/21-connection-pooling](../../database/21-connection-pooling/2-summary.md), [database/33-partitioning-and-sharding](../../database/33-partitioning-and-sharding/2-summary.md)
  - [distributed/03-partial-failure-and-timeouts](../../distributed/03-partial-failure-and-timeouts/2-summary.md) — 노드가 늘면 부분 실패가 상시가 된다
  - [os/36-server-concurrency-architectures](../../os/36-server-concurrency-architectures/2-summary.md)
- 논문·문서
  - J. D. C. Little, "A Proof for the Queuing Formula: L = λW", Operations Research 9(3), 1961
  - N. J. Gunther, Universal Scalability Law 페이지(식 (1)·(3), 세 C, N_max = √((1−α)/β), β=0·γ=1이면 Amdahl) <https://www.perfdynamics.com/Manifesto/USLscalability.html> · 『Guerrilla Capacity Planning』(2007)
  - G. Amdahl, "Validity of the single processor approach to achieving large scale computing capabilities", AFIPS 1967
  - JEP 444 "Virtual Threads" — Motivation 절의 Little's Law 설명 <https://openjdk.org/jeps/444>
- 실험 목록
  - E21 USL·Little's Law: N개 스레드 닫힌 루프, 모드 parallel/contention/coherence, 처리량·W·L 측정과 USL 적합 — JDK 21.0.12 temurin 컨테이너 `--cpus=2`, 3회 실행(사실 점검 재실행 포함)
