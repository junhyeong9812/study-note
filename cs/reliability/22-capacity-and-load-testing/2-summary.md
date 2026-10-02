# reliability/22-capacity-and-load-testing — 사이징·부하 테스트 설계·헤드룸, open vs closed 부하 모델 — 정리 (힌트)

## 해결하는 문제

"피크에 몇 대가 필요한가", "그 대수로 정말 버티나", "넘치면 어떻게 무너지나"에 미리 숫자로 답해야 한다.\
답이 없으면 피크가 올 때마다 운에 맡기거나, 반대로 필요 이상으로 사서 돈을 태운다.

쉬운 예: 놀이공원의 롤러코스터다.
- 한 번에 24명, 한 바퀴 3분 → 시간당 약 480명이 한계다. 이것이 "인스턴스당 한계 처리량"이다.
- 그런데 리허설을 직원 20명으로만 했다면(테스트 데이터가 작음), 실제 개장일 줄과 대기 시간은 모른다.
- 리허설에서 "앞 사람이 내릴 때까지 다음 사람을 안 보냈다"면(closed 모델), 줄이 길어지는 장면 자체가 안 나온다.

똑같은 구조다.\
실무 예: 블랙프라이데이 사이징, 신규 서비스 오픈 전 부하 테스트, 이벤트 푸시 직후 트래픽, 캐시를 붙인 뒤 "캐시가 비면 버티나" 확인.

원본 [server-design/09-capacity-slo](../../systems/server-design/09-capacity-slo.md) §2(용량 산정 절차)·§3(부하 테스트 종류·설계 요령·붕괴 방식)이 기초다. 오토스케일링 절(§4)은 [41-autoscaling](../41-autoscaling/2-summary.md), SLO 절(§1)은 [02-slo-sli-error-budget](../02-slo-sli-error-budget/2-summary.md)이 이어받는다.

## 동작·원리

### 1. 사이징 = 피크 수요 ÷ (대당 한계 × 목표 이용률) + 여유 대수

```text
 ① 피크 수요            일 요청 → 평균 RPS → × 피크 계수 → 피크 RPS        (원본 §2 ①, 예시 수치)
        │
 ② 대당 한계 처리량      부하 테스트로 "p99가 SLO를 넘기 직전"의 처리량을 잰다  ← 추정 금지, 측정
        │
 ③ 목표 이용률          한계의 몇 %까지 평소에 쓸 것인가(헤드룸)
        │
 ④ 필요 대수 = ⌈ 피크 RPS / (대당 한계 × 목표 이용률) ⌉
        │
 ⑤ 여유 대수           N + 1 / N + 2 — 장애·배포로 빠지는 대수
```

- *헤드룸(headroom)*: 평소 사용량과 한계 사이에 남기는 여유. 노드 장애, 배포 중 빠지는 인스턴스, 오토스케일 반응 시간, 예측 오차를 흡수한다(원본 §2 ③).
- *N + 2*: 두 단위가 동시에 빠져도 피크를 감당하는 구성. SRE 책 22장 예: 클러스터 하나의 한계가 5,000 QPS, 피크 19,000 QPS면 N + 2로 약 6개 클러스터가 필요하다.
  - 계산: 19,000 / 5,000 = 3.8 → 4개, 여기에 + 2 = 6개.
- 대당 한계는 **추정하지 않고 잰다.** 그리고 그 측정이 운영과 같은 조건이어야 한다. 아래 실험이 그 조건 차이를 보인다.

### 2. 왜 헤드룸이 필요한가 — 이용률과 지연은 비선형이다

```text
 p99 지연
   │                                  ╱
   │                                 ╱   ← 한계 근처에서 급등
   │                              _-
   │                         __--
   │ ____________________----
   └────────────────────────────────── 이용률
   0%        50%        80%   90% 100%
```

- 이용률이 1에 가까워지면 대기열이 비선형으로 길어진다(대기 이론 — [21-scaling-principles](../21-scaling-principles/2-summary.md) 자료구조 절).
- 아래 실험의 prod 줄: 도착률 600 → 1,200 → 1,500 → 1,800/s에서 p99가 20.6 → 25.1 → 40.8 → 433.7ms였다. 한계(약 1,630/s)를 넘는 순간 대기열이 계속 자란다.

### 3. open 모델 vs closed 모델

```text
 closed (사용자 수 고정)                         open (도착률 고정)
 VU1: [요청──응답][쉼][요청────응답][쉼]...       t=0   t=10ms  t=20ms  t=30ms ...  ← 시계가 요청을 보낸다
 VU2:   [요청──응답][쉼][요청──────응답]...        ↓      ↓       ↓       ↓
  ↑ 서버가 느려지면 다음 요청도 늦게 나간다          서버가 느려져도 요청은 예정대로 온다
  → 도착률이 스스로 줄어 서버를 봐준다              → 대기열이 쌓이는 장면이 그대로 보인다
```

- *closed 모델*: 가상 사용자(VU)가 응답을 받은 뒤에야 다음 요청을 보낸다. 동시 사용자 수가 고정이다.
  - k6 문서: 응답이 느려지면 반복이 길어져 새 반복의 도착률이 줄어든다. 이것을 테스트 문헌에서는 *coordinated omission*이라고 부른다.
- *open 모델*: 도착이 응답 완료와 무관하다. 정해진 비율로 요청이 들어온다. k6에서는 `constant-arrival-rate`·`ramping-arrival-rate` 실행기다.
- closed에서는 응답 시간 R과 처리량 X가 묶인다. 사용자 U명, 쉬는 시간 Z일 때 X = U / (Z + R)이다(대화형 응답 시간 법칙 — Little's Law를 사용자 루프에 적용한 것).
- 고르는 법
  - **공개 웹·API 트래픽**: 사용자는 서버가 느리다고 덜 오지 않는다 → open.
  - **고정된 수의 클라이언트**: 배치 워커 K개, 커넥션 수가 고정된 내부 호출자, 정원이 정해진 상담원 → closed가 실제와 같다.
  - 한계와 붕괴 방식을 보려면 open으로 도착률을 계단식으로 올린다.

### 4. 실험: 테스트 데이터가 작으면 · 모델이 closed면 무엇을 놓치나

- 서비스: 워커 16개, LRU 캐시 1만 키. 캐시 적중 2ms, 미스 20ms(DB 흉내 — 대기라 CPU를 쓰지 않는다). 측정 4초씩.
- 데이터: **test** = 키 2,000개 균등(전부 캐시에 들어감). **prod** = 키 100만 개 Zipf(s=1) 분포.
  - *Zipf 분포*: 순위 k의 빈도가 1/k에 비례하는 분포. 인기 키 몇 개에 몰리고 긴 꼬리가 있다.
- open: 포아송 도착을 정해진 시각에 넣고, 지연은 **도착 예정 시각부터** 잰다(coordinated omission을 피하는 방식).
- closed: 사용자 200명, 응답 후 100ms 쉼.

```java
// open 모델의 핵심: 도착 시각을 미리 정하고, 지연은 그 시각부터 잰다
t += (long) (-Math.log(1 - r.nextDouble()) / rate * 1e9);   // 포아송 도착 간격(지수 분포)
while (System.nanoTime() < t) LockSupport.parkNanos(t - System.nanoTime());
final long intended = t;
pool.execute(() -> { serve(cache, k); lat[idx] = System.nanoTime() - intended; });

// closed 모델의 핵심: 응답을 받아야 다음 요청
pool.submit(() -> serve(cache, k)).get();
Thread.sleep(thinkMs);
```

(실험, JDK 21.0.12 temurin, Docker `--cpus=2`, 2026-10-01 — 두 번 실행했다. 첫 실행은 도착률 600·900·1,200·1,500/s로 같은 경향(prod p99 20.6 → 21.3 → 25.2 → 40.5ms)이었고, 아래는 1,800/s를 넣은 두 번째 실행이다)

```text
cpus=2 JDK 21.0.12+8-LTS, 워커 16, 캐시 10000키, 적중 2ms/미스 20ms, 구간 4s
open   test 도착률   600/s → 처리    584/s 적중률 100% 평균=   2.5ms p50=   2.3ms p99=    6.2ms 최대 대기열     8
open   test 도착률  1200/s → 처리   1186/s 적중률 100% 평균=   2.3ms p50=   2.2ms p99=    4.3ms 최대 대기열     6
open   test 도착률  1500/s → 처리   1497/s 적중률 100% 평균=   2.3ms p50=   2.2ms p99=    3.7ms 최대 대기열    14
open   test 도착률  1800/s → 처리   1787/s 적중률 100% 평균=   2.2ms p50=   2.2ms p99=    3.1ms 최대 대기열     9
open   prod 도착률   600/s → 처리    594/s 적중률  57% 평균=  10.1ms p50=   2.4ms p99=   20.6ms 최대 대기열     6
open   prod 도착률  1200/s → 처리   1205/s 적중률  57% 평균=  10.4ms p50=   3.2ms p99=   25.1ms 최대 대기열    17
open   prod 도착률  1500/s → 처리   1490/s 적중률  57% 평균=  15.1ms p50=  15.4ms p99=   40.8ms 최대 대기열    42
open   prod 도착률  1800/s → 처리   1629/s 적중률  57% 평균= 222.9ms p50= 225.6ms p99=  433.7ms 최대 대기열   706
closed prod 사용자 200명 think 100ms → 처리   1559/s 적중률  56% 평균=  27.3ms p50=  21.8ms p99=  175.7ms
```

- 사실 점검 재실행(같은 조건, 2026-10-01): prod 1,800/s 처리 1,620/s·p99 457.2ms·최대 대기열 740, closed 처리 1,562/s·p99 176.3ms·평균 27.7ms. 값은 실행마다 몇 % 다르고 경향은 같다(prod 1,800/s p99 434~457ms, 처리 1,620~1,629/s).
- 관찰 1 — 데이터 크기: test는 1,800/s에서도 p99 3.1ms로 여유롭다. 같은 서비스가 prod 분포에서는 적중률 57%, 1,800/s에서 처리 1,629/s로 넘쳤다. **test만 보면 한계를 실제보다 크게 잡는다.**
  - 해석: 대당 한계 ≈ 워커 16 / 평균 서비스 시간. test는 약 2ms라 한계가 수천/s, prod는 0.57×2 + 0.43×20 ≈ 9.7ms라 약 1,650/s다. 측정 1,629/s와 맞는다.
- 관찰 2 — 이용률과 지연: prod에서 600 → 1,500/s(한계의 약 90%)까지 p99가 2배, 1,800/s(한계 초과)에서 약 20배가 됐다.
- 관찰 3 — 한계를 넘으면: 4초 동안 대기열이 706까지 자랐다. (1,800 − 1,629) × 4초 ≈ 684와 비슷하다. 시간이 갈수록 계속 자라는 구간이다.
- 관찰 4 — closed 모델: 같은 prod 서비스에 200명이 붙자 처리량은 1,559/s에서 멈췄고 p99는 176ms로 "버티는 것처럼" 보인다. 서버가 느려지자 사용자들이 요청을 늦게 보냈기 때문이다.
  - 검산: X = U / (Z + R) → R = 200 / 1,559 − 0.1 = 28.3ms. 측정 평균 27.3ms와 1ms 차이(쉼 `sleep`의 추가 지연 — 해석).
  - 같은 서비스를 open 1,800/s로 밀면 대기열이 끝없이 자란다. closed 결과만으로는 "1,800/s가 오면 어떻게 되나"를 알 수 없다.

### 5. 캐시는 지연용인가 용량용인가

- SRE 책 22장 "Slow Startup and Cold Caching"의 구분이다.
  - *지연 캐시(latency cache)*: 캐시가 비어도 예상 부하를 감당한다. 캐시는 빠르게 해 줄 뿐이다.
  - *용량 캐시(capacity cache)*: 캐시가 비면 예상 부하를 감당하지 못한다. 캐시가 사실상 필수 의존성이다.
- 구분은 예상 부하와 견줘야 정해진다. 위 실험의 서비스는 적중률 100% 기준이면 한계가 수천/s지만, 캐시가 비면(적중 0%) 16 / 20ms = 800/s다. 예상 피크가 800/s를 넘으면(예: 1,200/s — 예시) 용량 캐시, 600/s라면 지연 캐시다.
- 그래서 부하 테스트에 **콜드 캐시 시나리오**를 넣는다. 재시작·새 클러스터·유지보수 복귀가 콜드 캐시를 만든다(같은 절).

## 쓰이는 자료구조·알고리즘

- **포아송 도착 생성** — 도착 간격을 지수 분포로 뽑는다(역변환: −ln(1−U)/λ). open 모델 부하 생성기의 기본.
- **Zipf 분포 샘플링** — 누적 분포 배열을 만들고 균등 난수로 이진 탐색한다. 운영 키 분포 흉내.
- **LRU 캐시** — Java `LinkedHashMap(accessOrder=true)` + `removeEldestEntry`. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).
- **분위수 계산** — 지연을 모아 정렬 후 위치로 p50·p99. 운영에서는 히스토그램(HdrHistogram·Prometheus 히스토그램)으로 근사한다. 측정 방법론은 [19-performance-measurement](../19-performance-measurement/2-summary.md).
- **대화형 응답 시간 법칙** — closed 모델에서 R = U/X − Z. Little's Law([21](../21-scaling-principles/2-summary.md))의 변형.

## 적용 — 풀어나가는 법

### 1. 부하 테스트 설계 순서

1. **목표를 정한다.** "피크 1,500 req/s에서 p99 < 200ms, 오류율 < 0.1%"처럼 SLO 형태로(예시).
2. **모델을 고른다.** 외부 트래픽이면 open(`constant-arrival-rate`·`ramping-arrival-rate`). 고정 클라이언트면 closed.
3. **데이터를 운영과 맞춘다.** 키 개수·분포(인기 키 쏠림), 데이터 크기(빈 DB 금지), 쓰기 비율, 캐시 상태(웜·콜드 둘 다).
4. **계단식으로 올린다.** 도착률을 단계마다 몇 분 유지하며 p99·오류율·대기열·자원 이용률을 기록한다. p99와 오류율 목표 중 **먼저** 깨지기 직전의 도착률이 대당 한계다.
5. **넘겨 본다.** 한계 위로 올려 **붕괴 방식**을 본다 — 빠르게 거절하나, 전부 느려지다 연쇄 실패하나(원본 §3, SRE 22장 "Load test components until they break").
6. **부하 발생기를 의심한다.** 발생기의 CPU·네트워크가 먼저 차지 않았는지, 의도한 도착률을 실제로 냈는지 확인한다(k6의 `dropped_iterations`).
7. **사이징에 반영한다.** 필요 대수 = ⌈피크 / (대당 한계 × 목표 이용률)⌉ + 여유 대수.

### 2. k6 open 모델 스크립트 (JS)

```javascript
import http from 'k6/http';

export const options = {
  scenarios: {
    step_up: {
      executor: 'ramping-arrival-rate',   // open 모델: 도착률을 단계별로
      startRate: 300,
      timeUnit: '1s',
      preAllocatedVUs: 200,
      maxVUs: 2000,                       // 서버가 느려지면 VU를 더 써서 도착률을 지킨다
      stages: [                           // stage는 target까지 선형으로 올린다 — 같은 target을 한 번 더 두면 그 도착률을 유지한다(k6 문서)
        { target: 600,  duration: '1m' },  // 600까지 올림
        { target: 600,  duration: '3m' },  // 600 유지
        { target: 1200, duration: '1m' },
        { target: 1200, duration: '3m' },
        { target: 1800, duration: '1m' },
        { target: 1800, duration: '3m' },
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(99)<200'],     // 전송+응답 대기+수신만 잰다(연결 대기 http_req_blocked·연결 수립은 빠짐)
    http_req_failed: ['rate<0.001'],      // 오류율 목표 0.1%
    dropped_iterations: ['count<1'],      // 발생기가 도착률을 못 지켰으면 실패로 본다
  },
};

// 운영과 같은 키 분포(예: 인기 키 쏠림)로 요청 대상을 고른다 — 고정 키 몇 개만 쓰면 캐시만 테스트한다
export default function () {
  const id = pickZipfKey();               // 운영 로그에서 뽑은 키 목록·분포로 구현
  http.get(`https://staging.example.com/items/${id}`);
}
```

- `constant-arrival-rate`의 필수 옵션은 `rate`·`duration`·`preAllocatedVUs`이고, `maxVUs`를 안 주면 `preAllocatedVUs`와 같다(k6 문서). arrival-rate 실행기에는 반복 끝에 `sleep()`을 넣지 않는다(같은 문서).
- `dropped_iterations`: 빈 VU가 없어 시작하지 못한 반복 수(k6 문서 "Dropped iterations").
- `http_req_duration`은 `http_req_sending + http_req_waiting + http_req_receiving`이다(k6 내장 지표 문서). 연결 슬롯 대기(`http_req_blocked`)·연결 수립 시간은 들어가지 않는다. 그래서 이 threshold는 "예정 도착 시각부터 잰 지연"과 범위가 다르다. 예정대로 시작했는지는 `dropped_iterations`로, 연결 대기는 `http_req_blocked`로 따로 본다.

### 3. 헤드룸 정하기

- 원본 §2 ③의 항목(노드 장애 (N−1)/N, 배포 중 빠지는 인스턴스, 오토스케일 반응 시간, 예측 오차)을 더해 목표 이용률을 정한다.
- 이 실험 서비스라면: 한계 약 1,630/s, 1,500/s(약 90%)에서 이미 p99가 2배였다. 목표 이용률을 60~70%로 두면 약 1,000~1,140/s가 대당 운영 상한이다(예시 계산).

## 장애 시나리오와 대처

### 1. 부하 테스트가 운영보다 낙관적이었다 (⚠ 캐시에 다 들어가는 테스트 데이터)

- 현상: 테스트에서 3,000 req/s를 버텼는데 운영 1,500 req/s에서 p99가 터졌다.
- 보이는 형태: 운영 캐시 적중률이 테스트보다 크게 낮다. DB QPS·디스크 읽기가 테스트 때보다 훨씬 많다. 위 실험의 test(적중 100%) vs prod(57%).
- 원인: 테스트 키가 몇천 개라 캐시에 전부 들어갔다. 대당 한계를 캐시 적중 경로로만 쟀다.
- 대처: 운영 로그에서 키 분포를 뽑아 재현한다. 데이터 크기를 운영과 맞춘다. 적중률을 테스트 결과에 함께 적고, 운영 적중률과 다르면 결과를 무효로 본다.

### 2. 헤드룸 없이 피크에 들어갔다 (⚠)

- 현상: 평소 이용률 85%로 운영하다가, 피크에 한 대가 죽자 나머지가 연쇄로 넘어졌다.
- 보이는 형태: 한 대 장애 직후 남은 인스턴스들의 대기열·p99 급등, 헬스 체크 실패로 더 빠지는 인스턴스, 오류율 급증.
- 원인: 이용률-지연 비선형 구간에서 운영했다. 한 대가 빠지면 나머지의 이용률이 0.85N/(N−1)로 오른다(같은 인스턴스 N대에 균등 분산일 때). N ≤ 6이면 100%를 넘고, 10대여도 약 94%라 지연이 가파른 구간 깊숙이 들어간다(이 노트 실험의 서비스는 한계의 약 90%에서 p99가 2배). SRE 22장: 과부하로 서버가 죽기 시작하면, 부하를 장애 직전 수준 아래로 조금 내려서는 회복되지 않는다.
- 대처: N + 1·N + 2 여유 대수, 목표 이용률을 부하 테스트 곡선에서 정한다. 넘치면 빠르게 거절하는 로드 셰딩([12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md))을 둔다.

### 3. closed 모델로 재서 한계를 잘못 알았다

- 현상: "동시 사용자 200명에서 p99 176ms"라 안심했는데, 실제 트래픽 급증에 큐가 무한히 자랐다.
- 보이는 형태: 테스트 도구의 RPS가 목표보다 낮은 채로 평평했다. 응답이 느려질수록 RPS가 같이 줄었다.
- 원인: closed 모델은 서버가 느려지면 도착률을 스스로 줄인다(coordinated omission).
- 대처: 외부 트래픽은 open 모델(arrival-rate 실행기)로 다시 잰다. 지연은 예정 도착 시각부터 잰다.

### 4. 부하 발생기가 병목이었다

- 현상: 서버 CPU는 40%인데 RPS가 더 오르지 않는다.
- 보이는 형태: 발생기 CPU 100%, `dropped_iterations` > 0, 발생기 쪽 커넥션 오류.
- 원인: 발생기 자원 부족·VU 부족·네트워크 한도.
- 대처: 발생기를 여러 대로 나눈다. `maxVUs`를 늘린다. 서버 쪽 지표로 실제 도착률을 교차 확인한다.

### 5. 재시작 뒤 콜드 캐시로 버티지 못했다

- 현상: 배포 후 몇 분간 오류율이 치솟다가 서서히 회복됐다.
- 보이는 형태: 배포 직후 캐시 적중률 바닥, DB 부하 급증.
- 원인: 용량 캐시인데 콜드 캐시 시나리오를 테스트하지 않았다. 위 실험 서비스라면 콜드 캐시 한계는 16 / 20ms = 800/s(계산)다.
- 대처: 콜드 캐시 상태로도 부하 테스트를 한다. 트래픽을 천천히 올려 캐시를 데운다(SRE 22장). 캐시를 별도 프로세스로 빼 재시작에도 남게 한다. 콜드 스타트 전반은 [42-cold-start-and-scale-from-zero](../42-cold-start-and-scale-from-zero/2-summary.md).

## 핵심 문장

- 필요 대수 = ⌈피크 ÷ (대당 한계 × 목표 이용률)⌉ + 여유 대수. 대당 한계는 추정하지 않고 운영과 같은 조건에서 잰다.
- 이용률과 지연은 비선형이다. 실험에서 한계의 약 90%에서 p99가 2배, 한계를 넘자 약 20배가 되고 대기열이 계속 자랐다.
- 테스트 데이터가 캐시에 다 들어가면 캐시만 테스트한 것이다. 실험에서 같은 서비스가 test 분포로는 1,800/s에도 p99 3.1ms, 운영 분포로는 넘쳤다.
- 외부 트래픽은 open 모델로 잰다. closed 모델은 서버가 느려지면 도착률을 스스로 줄여(coordinated omission) 한계 뒤의 붕괴를 감춘다.
- 캐시가 비면 버티지 못하는 서비스(용량 캐시)는 콜드 캐시 시나리오를 따로 테스트한다.

## 관련 주제·근거

- 선행
  - [21-scaling-principles](../21-scaling-principles/2-summary.md) — Little's Law·병목
  - [19-performance-measurement](../19-performance-measurement/2-summary.md) — 분위수·coordinated omission·HdrHistogram
  - 원본 [server-design/09-capacity-slo](../../systems/server-design/09-capacity-slo.md) §2 용량 산정 절차(피크 계수·Little's Law·헤드룸·데이터 증가), §3 부하 테스트 종류 표·설계 요령·붕괴 방식
- 후속·연결
  - [41-autoscaling](../41-autoscaling/2-summary.md) — 원본 §4 오토스케일링 절을 이어받음
  - [42-cold-start-and-scale-from-zero](../42-cold-start-and-scale-from-zero/2-summary.md) — 콜드 캐시·워밍업
  - [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md) — 좋은 붕괴 방식
  - [database/30-caching-with-databases](../../database/30-caching-with-databases/2-summary.md)
- 문서·책
  - Google SRE 책 22장 "Addressing Cascading Failures" — Perform capacity planning(N + 2 예: 5,000 QPS·19,000 QPS·6개), Slow Startup and Cold Caching(지연 캐시 vs 용량 캐시), Testing for Cascading Failures("Load test components until they break") <https://sre.google/sre-book/addressing-cascading-failures/>
  - Google SRE 책 18장 "Software Engineering in SRE" — Auxon(의도 기반 용량 계획, "N + 2 per continent" 같은 요구, 성능 데이터는 부하 테스트 또는 과거 성능에서) <https://sre.google/sre-book/software-engineering-in-sre/>
  - Grafana k6 "Open and closed models"(closed 모델의 도착률 감소 = coordinated omission), "Constant arrival rate"(옵션·기본값), "Dropped iterations" <https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/>
- 실험 목록
  - E22 test(2,000키 균등) vs prod(100만 키 Zipf) × open 도착률 600~1,800/s, closed 200명·think 100ms — JDK 21.0.12 temurin 컨테이너 `--cpus=2`, 2회 실행 + 사실 점검 재실행 1회
