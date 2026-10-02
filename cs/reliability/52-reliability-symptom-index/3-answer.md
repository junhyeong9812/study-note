# reliability/52-reliability-symptom-index — 정답

## 정답

### 1. 역방향 색인이 필요한 이유와 네 가지

- leaf는 "원인 → 메커니즘 → 증상"으로 쓴다. 현장에서 손에 든 것은 증상(그래프·로그 한 줄·고객 문의)뿐이라 반대 방향이 필요하다.
- 같은 사건이 층마다 다른 이름으로 보인다(DB 락 대기 → 커넥션 풀 고갈 메시지 → 스레드 고갈 → 게이트웨이 504). 맨 위 이름만으로는 원인 층을 모른다.

| 확보할 것 | 왜 |
|---|---|
| 원문(예외 체인·응답 본문·제품과 판) | 번역되며 정보가 줄어든다. 문구는 제품·판마다 다르다 |
| 모양(즉시 실패·설정값 근처 실패·느린 성공·에러 없이 틀림·주기적) | 모양 하나로 후보 칸이 크게 준다(§1) |
| 시각(무엇이 바뀐 순간과 겹치나) | SRE 책 1장: 장애의 약 70%가 운영 중 변경 때문. 겹치면 완화가 먼저 |
| 범위(엔드포인트·인스턴스·셀·전체) | 한 대만이면 배포 누락·핫 키, 전체면 공유 구성 요소·설정 |

### 2. 실패까지 걸린 시간으로 층 고르기

| 시간 | 먼저 의심 | 근거 |
|---|---|---|
| (가) 약 1초 | Resilience4j TimeLimiter 기본 `timeoutDuration` 1초(2.4.0 `TimeLimiterConfig`). 재시도가 있는데도 1초에 끝나면 `TimeLimiter(Retry(call))` 순서 착오 | [35-3](../35-timeout-design-worksheet/2-summary.md) |
| (나) 약 30초 | HikariCP 기본 `connectionTimeout` 30초(6.3.0 `HikariConfig`) — 풀 대기. 메시지 `Connection is not available, request timed out after 30000ms` 근처 | [07-3](../07-timeout-taxonomy-by-layer/2-summary.md) |
| (다) 약 131초 | connect 타임아웃 없음 + 방화벽 SYN DROP. 리눅스 기본 `tcp_syn_retries=6`의 재전송 한도(6.5+에서 약 131초) | [07-1](../07-timeout-taxonomy-by-layer/2-summary.md) |

- 원리: 실패가 설정값 근처에 몰리면 그 값을 가진 층이 범인이다(§1). 각 층의 타임아웃 값 목록을 먼저 만들어 두면 대조가 빠르다.

### 3. 스레드 덤프 세기

(실행 확인, OpenJDK 21.0.12)

```text
 12  RUNNABLE  sun.nio.ch.SocketDispatcher.read0(java.base@21.0.12/Native Method)
  3  BLOCKED  Stuck.lambda$main$4(Stuck.java:19)
```

- 상태만 세면 `RUNNABLE` 12, `BLOCKED` 3이다. "대부분 일하는 중"으로 오독한다. 소켓 읽기에서 막힌 스레드도 `RUNNABLE`이기 때문이다.
- 맨 위 프레임까지 묶으면 12개가 **같은 소켓 읽기**에 모여 있다. 풀 크기만큼 같은 곳에 멈춘 모양이다.
- 다음: 그 호출의 타임아웃(connect·read·전체)을 확인한다. 공유 풀이면 하류별 격벽을 넣는다([05-2](../05-timeouts-and-deadline-propagation/2-summary.md) · [28-1](../28-bulkhead/2-summary.md)). `BLOCKED` 3개는 같은 `synchronized` 줄이고, 쥔 쪽은 `- locked <0x…>`로 찾는다.

### 4. 137 가르기

- 137 = 128 + 9, 즉 SIGKILL로 끝났다는 뜻뿐이다. 누가 왜 죽였는지는 따로 본다.
- 첫 확인: `kubectl describe pod`·`docker inspect`의 `OOMKilled`.

| | `OOMKilled=true` | `OOMKilled=false` |
|---|---|---|
| 모양 | 힙은 평평, RSS만 우상향 | 종료가 매번 유예 시간(Docker 10초·K8s 30초)을 꽉 채움, SIGTERM 수신 로그 없음 |
| 원인 | 힙 밖 누수(direct buffer·스레드 스택·metaspace·native) | 셸 형식 CMD로 `sh`가 PID 1 → SIGTERM 미전달, 또는 유예 < 드레이닝 기한 |
| 대처 | NMT diff로 영역 좁히기, `MaxDirectMemorySize`를 컨테이너 한도 안쪽으로(커널 kill → JVM 예외로) | exec 형식 ENTRYPOINT·`exec java`·`--init`, 유예를 전파 대기 + 드레이닝 + 정리에서 역산 |
| leaf | [37-2](../37-memory-leak-and-heap-analysis/2-summary.md) | [14-2](../14-graceful-shutdown/2-summary.md) · [14-4](../14-graceful-shutdown/2-summary.md) |

- 힙만 늘리는 것은 앞 경우를 악화시킬 수 있다. 컨테이너 한도 안에서 힙 밖에 남은 자리가 줄어든다.

### 5. 504인데 결제됨

- 대조: 같은 주문의 게이트웨이 504 시각, 서비스 로그의 응답 쓰기 실패, PG 승인 기록.
- 원인: 게이트웨이 timeout < 서비스 안 최악 시간. 서비스가 결과를 확정하기 전에 게이트웨이가 끊었다. 보낸 뒤의 외부 호출은 취소할 수 없다.
- 504 건 처리: "실패"가 아니라 "모름" 상태로 둔다. 같은 멱등 키로 PG 상태를 조회해 확정한다. 이미 난 중복은 대사로 찾아 환불한다.
- 설정: 게이트웨이 timeout > 서비스 안 최악 시간(예산표). 결제 요청에 멱등 키를 받아 재결제가 같은 키면 재생되게 한다. 비멱등 라우트의 게이트웨이 재시도는 끈다([35-1](../35-timeout-design-worksheet/2-summary.md) · [35-2](../35-timeout-design-worksheet/2-summary.md) · [09-4](../09-cancellation-propagation/2-summary.md)).

### 6. 세 지연 증상

| | 원인 | 첫 진단 | leaf |
|---|---|---|---|
| (가) | 평균이 드문 긴 지연을 희석. 빠른 실패가 평균을 낮춤 | p50·p99·max를 성공·실패로 나눠 그림 | [19-1](../19-performance-measurement/2-summary.md) · [16-2](../16-metrics-and-golden-signals/2-summary.md) |
| (나) | 인스턴스별 분위수를 평균 냄 — 분위수는 합칠 수 없음 | 쿼리가 `sum by (le)` 후 `histogram_quantile`인가 | [19-3](../19-performance-measurement/2-summary.md) |
| (다) | 넓은 버킷 안을 선형 보간, +Inf 버킷이면 두 번째로 높은 경계값 | 버킷 경계 목록 vs 실제 분포 | [16-3](../16-metrics-and-golden-signals/2-summary.md) |

### 7. 회복 안 되는 과부하

- 모양: 방아쇠(DB 몇 초 지연)는 사라졌는데 재시도가 부하를 붙잡는 준안정 고장이다. 층마다 재시도하면 곱이 된다(4³ = 64).
- 증설하면: 증폭된 부하를 진짜 수요로 읽은 것이다. 앱을 늘리면 병목이 DB 커넥션으로 옮겨 `too many clients`·풀 고갈이 먼저 온다([41-3](../41-autoscaling/2-summary.md) · [21-2](../21-scaling-principles/2-summary.md)).
- 볼 것: 재시도 비율, 도착률 vs 신규 요청률, 같은 상관 ID의 하류 쿼리 수, 층별 재시도 설정.
- 완화: 재시도를 끄거나 예산으로 묶는다. 부하를 용량 훨씬 아래로 일시 차단한 뒤 점진 복귀한다(SRE 22장). 근본은 한 층 재시도 + 지터 + 예산([03-1](../03-failure-at-scale/2-summary.md) · [06-2](../06-retry-backoff-jitter/2-summary.md) · [06-3](../06-retry-backoff-jitter/2-summary.md) · [12-2](../12-backpressure-and-load-shedding/2-summary.md)).

### 8. 헬스체크 실패 ≠ 죽음

- 오독 이유: 헬스체크는 과부하·스레드 고갈·의존성 지연으로도 실패한다(SRE 22장: 스레드 고갈·파일 디스크립터 부족이 헬스체크 실패로 이어진다). 살아 있는 대상을 빼면 남은 대상이 더 무거워진다.

| 경로 | leaf | 대처 |
|---|---|---|
| 셰딩 중인 인스턴스가 헬스체크까지 버림 → LB가 뺌 → 남은 쪽 과부하 연쇄 | [12-4](../12-backpressure-and-load-shedding/2-summary.md) | 헬스체크·관리 요청은 별도 경로·최고 중요도 |
| 깊은 헬스체크(DB 확인) → DB 2초 지연에 전 인스턴스 unhealthy → 전면 503 | [47-2](../47-server-design-antipatterns/2-summary.md) | liveness는 프로세스 자신만. 의존성 문제는 오류·폴백으로 |
| 요청 스레드 전부가 느린 외부 호출에 묶임 + 프로브가 같은 풀 → liveness 실패 → 연쇄 재시작 | [48-3](../48-performance-and-stability-antipatterns-in-code/2-summary.md) | 통합 지점 타임아웃·격벽, 프로브 경로 분리 |

### 9. 에러 없이 틀린 셋

| 증상 | 원인 | 탐지 |
|---|---|---|
| 배치 `COMPLETED` 뒤 미지급 | 스킵을 성공과 구분해 보고하지 않음, 합계만 대사(NULL이 합에서 빠짐) | 스킵 수, 행 수·누락 키 대사, 스킵 시 0이 아닌 종료 코드 — [31-2](../31-batch-job-restart-and-checkpoint/2-summary.md) |
| 하루 몇 건 적립 누락 | 처리 완료 전 오프셋 커밋(자동 커밋 + 비동기 처리) | 원천 vs 결과 건수 대사, 커밋 위치 점검 — [27-3](../27-failure-point-checklist/2-summary.md) |
| 장애 시각 INFO 빈칸 | 비동기 appender 큐 포화 → INFO 이하 폐기(Logback 기본) | 버린 수 지표, 큐 설정 명시 — [15-4](../15-logging/2-summary.md) |

- 공통: "에러율 0 = 정상"으로 읽으면 놓친다. 원천과 결과를 키로 맞추는 대사가 사실상 유일한 탐지 수단인 경우가 많다([01-4](../01-fault-error-failure-availability/2-summary.md)).

### 10. 원본 플레이북 두 곳

- "캐시는 p99를 개선하지 않는다"
  - 미스 비율 3%: 가장 느린 1%는 미스 경로 안에 있다. p99 = 미스 경로 지연이라 캐시를 넣어도 p99는 그대로다. 원본의 말이 맞는 경우다.
  - 미스 비율 0.5%: p99 위치의 요청도 적중 경로다. p99가 적중 경로 지연으로 내려간다. 원본의 말이 틀리는 경우다(p99.9는 여전히 미스 경로).
  - 그래서 첫 진단은 "미스 비율이 1%를 넘나"다.
- 처방 순서: B-3("타임아웃 → 서킷 → 벌크헤드")와 D-1("타임아웃 → 벌크헤드 → 서킷 → 폴백")이 다르다. D-1로 읽는다. 서킷은 호출 결과가 기록돼야 판단하므로 느린 하류에는 늦게 열린다([10-3](../10-circuit-breaker/2-summary.md)). 그동안의 스레드 고갈은 격벽이 막는다([28-1](../28-bulkhead/2-summary.md)).
