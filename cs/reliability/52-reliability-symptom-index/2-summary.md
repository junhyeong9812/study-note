# reliability/52-reliability-symptom-index — 증상 사전: 지연 급증·에러율 급증·연쇄 장애·배포 직후 502·메모리 우상향 → 보이는 형태·원인·첫 진단·leaf — 정리 (힌트)

## 해결하는 문제

운영·신뢰성 영역의 다른 노트는 **원인에서 증상으로** 간다.\
"재시도를 층마다 3번씩 걸었다 → 하류 부하가 64배가 된다 → 원인이 사라져도 복구되지 않는다"처럼 쓴다.\
장애 현장에서는 반대 방향이 필요하다.\
손에 든 것은 그래프 한 장(p99가 계단처럼 오른다), 로그 한 줄(`Connection is not available, request timed out after 30001ms`), 고객 문의 한 줄("결제 실패라고 떴는데 돈은 빠졌어요")뿐이다.

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                              이 노트 (역방향)
  원인 --> 메커니즘 --> 증상                       증상 --> 보이는 형태 --> 흔한 원인 --> 첫 진단 --> leaf
  "층마다 재시도 → 곱셈 증폭 → 복구 불가"          "같은 상관 ID의 쿼리가 DB에 수십 번. 재시도 설정부터 센다"
```

쉬운 예: 자동차 계기판의 경고등 안내표다.\
"엔진 경고등 + 출력 저하"면 점화 계통부터, "배터리 경고등"이면 발전기부터 본다.\
표는 차를 고치지 않는다. **어디를 먼저 열어 볼지**만 정한다.

똑같은 구조다.\
"평균은 괜찮은데 p99만 나쁘다"면 지표의 집계 방식부터 의심한다.\
"의존성 하나가 느린데 서비스 전체가 죽었다"면 스레드 덤프에서 멈춘 지점을 센다.\
표가 첫 진단과 leaf를 알려 준다.

실무 예:
- 같은 사건이 층마다 **다른 이름**으로 보인다. 외부 결제사가 느려지면 앱에서는 `SQLTransientConnectionException`(트랜잭션 안에서 외부를 불러 커넥션을 붙든 경우), 게이트웨이에서는 `504`, 사용자에게는 "결제 실패"로 보인다.
- 신뢰성 증상의 상당수는 **에러가 없다.** 평균 지연이 꼬리를 가리고, 스킵한 행이 `COMPLETED` 뒤에 숨고, 버려진 INFO 로그는 흔적을 남기지 않는다.
- **완화(mitigation)와 원인 규명은 다른 일이다.** 이 색인의 "첫 진단"은 원인을 가르는 확인이다. 배포 직후라면 진단보다 롤백이 먼저일 수 있다([26-1](../26-incident-response-and-postmortem/2-summary.md)).

이 노트는 기존 [server-design/10 상황별 플레이북](../../systems/server-design/10-playbook-by-symptom.md)을 이어받는다. 원본의 A~H 항목은 아래 §12에서 이 노트의 칸과 대응시키고, 고칠 점은 "참고:" 줄로 적는다.

## 동작·원리

### 0. 증상이 올라오는 길 — 어느 층이 만든 말인가

```text
  +------------------------------------------------------------------------------+
  | 사용자·업무    "가끔 몇 초씩 멈춤" "결제 실패인데 돈이 빠짐" "정산이 두 번"      |
  +------------------------------------------------------------------------------+
  | 엣지·게이트웨이  HTTP 502/503/504, Envoy 응답 플래그·통계(upstream_rq_timeout)  |
  +------------------------------------------------------------------------------+
  | 앱 프레임워크   CallNotPermittedException, TimeoutException, HttpTimeoutException|
  |                 RejectedExecutionException, OutOfMemoryError                   |
  +------------------------------------------------------------------------------+
  | 자원 풀        스레드 풀·커넥션 풀·큐 — pending·active=max·queue 길이            |
  +------------------------------------------------------------------------------+
  | 하류·데이터    DB `sorry, too many clients already`, 복제 지연, 락 대기          |
  +------------------------------------------------------------------------------+
  | 플랫폼·OS     종료 코드 137/143, OOMKilled, ENOSPC, EADDRNOTAVAIL, 프로브 실패   |
  +------------------------------------------------------------------------------+
```

- 아래층 사건이 위층 이름으로 **번역**된다. 번역하면서 정보가 줄어든다.
  - 예: DB 락 대기 → 앱 커넥션 풀 고갈(`Connection is not available ...`) → 요청 스레드 고갈 → 게이트웨이 `504`. 사용자에게 보이는 것은 마지막 하나다.
- 그래서 색인을 쓰기 전에 네 가지를 확보한다.
  - **원문**: 예외 체인 전체, 응답 본문(Envoy는 504 본문이 `upstream request timeout`), 제품과 판.
  - **모양**: 즉시 실패인가, 멈췄다 실패인가, 느리게 성공인가, 에러 없이 값만 틀렸나, 주기적인가.
  - **시각**: 무엇이 바뀐 순간과 겹치나. SRE 책 1장은 "장애의 약 70%가 운영 중 시스템의 변경 때문"이라고 적는다.
  - **범위**: 엔드포인트 하나·인스턴스 하나·셀 하나·전체 중 어디까지인가.

  - *색인(index)*: 찾을 말 → 그 말이 나오는 위치 목록. 여기서는 증상 → leaf의 「장애 시나리오와 대처」 번호다.
  - *첫 진단*: 원인을 확정하는 조사가 아니라, 가설을 가장 빨리 가르는 확인 한 가지다.

### 1. 모양으로 먼저 가른다

```text
                         증상 하나
                            |
     +-----------+----------+----------+-------------+--------------+
     |           |          |          |             |              |
  즉시 실패   멈췄다 실패  느린 성공   에러 없이 틀림   주기적·시각 고정  변경 직후
  (ms 단위)   (설정값 근처) (꼬리 증가)  (대사에서 발견)  (정각·TTL 주기)  (배포·설정·플래그)
     |           |          |          |             |              |
  거절·차단    타임아웃     포화·대기    중복·누락·스킵   동기화된 부하     공존·롤백·워밍업
  §3·§4       §3·§4·§6     §2·§6       §7·§8           §4·§8            §5
```

- **즉시 실패**는 대개 누군가 "하지 않기로" 결정한 것이다. 서킷 열림, 격벽 가득, 리미터 거절, 유계 큐 거절, 연결 거부.
- **설정값 근처에서 실패**하면 그 값을 가진 타임아웃이 범인이다. 실패까지 걸린 시간을 각 층의 타임아웃 값과 맞춰 본다(1초면 Resilience4j 2.4.0 TimeLimiter 기본값, 30초면 HikariCP 6.3.0 기본 `connectionTimeout`, 약 131초면 리눅스 6.5+ 기본 SYN 재전송 한도 — [07-1](../07-timeout-taxonomy-by-layer/2-summary.md)).
- **느린 성공**은 어딘가에서 줄을 서고 있다. 줄은 포화된 자원 앞에 생긴다(USE의 포화 — [16-5](../16-metrics-and-golden-signals/2-summary.md)).
- **에러 없이 틀림**은 로그로는 못 찾는다. 원천과 결과의 건수·합계 대사가 사실상 유일한 탐지 수단인 경우가 많다([01-4](../01-fault-error-failure-availability/2-summary.md)).

### 2. 지연 — 느리다

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 평균은 평탄한데 "가끔 몇 초씩 멈춘다" 문의. 대시보드에 p99·max 패널이 없다 | 평균이 드문 긴 지연을 희석. 빠른 실패가 평균을 끌어내림 | p50·p99·max를 성공·실패로 나눠 그린다 | [19-1](../19-performance-measurement/2-summary.md) · [02-1](../02-slo-sli-error-budget/2-summary.md) · [16-2](../16-metrics-and-golden-signals/2-summary.md) |
| p99가 7초로 보이는데 트레이스로는 느린 요청도 2초대. p99 그래프가 계단 | `histogram_quantile`이 넓은 버킷 안을 선형 보간 | 버킷 경계 목록과 실제 분포 비교 | [16-3](../16-metrics-and-golden-signals/2-summary.md) |
| "전체 p99 120ms" 보고, 사용자 체감 400ms | 인스턴스별 분위수를 평균 냄(`avg(quantile)`) | 쿼리가 `sum by (le)` 후 `histogram_quantile`인가 | [19-3](../19-performance-measurement/2-summary.md) |
| SLO 대시보드 지연 SLI가 "No data"이거나 일부 인스턴스가 빠짐 | 쿼리의 `le` 값이 일부 서비스의 버킷 경계와 다름 | 서비스별 버킷 경계 | [02-4](../02-slo-sli-error-budget/2-summary.md) |
| 하위 서비스는 모두 초록인데 상위 API p99(심하면 p50)가 나쁨 | 팬아웃이 리프의 꼬리를 증폭(N=100이면 63%가 느린 리프를 만남) | 팬아웃 수와 리프 p99·p99.9 | [03-2](../03-failure-at-scale/2-summary.md) · [34-1](../34-tail-latency-and-stragglers/2-summary.md) |
| hedge를 켠 뒤 하류 요청이 사용자 요청의 1.5~2배, 부하가 오르면 전체가 수 초 | hedge 지연이 0이나 p50 → 부하 증가 → 큐 증가 → hedge 증가 | hedge 비율·지연 기준 | [34-2](../34-tail-latency-and-stragglers/2-summary.md) |
| hedge 비율은 3%인데 하류 CPU 30% 증가 | 취소가 하류 작업 중단으로 이어지지 않음 | 응답 받은 뒤에도 하류에서 끝까지 실행된 로그 | [34-4](../34-tail-latency-and-stragglers/2-summary.md) |
| CPU 30%인데 p99 상승. 풀 활성 = 최대, `pending` 증가 | 제약 자원이 CPU가 아니라 풀·락·하류 동시성 | 풀·큐마다 이용률·포화 지표 | [16-5](../16-metrics-and-golden-signals/2-summary.md) · [20-4](../20-performance-method-and-amdahl/2-summary.md) |
| 톰캣 스레드를 200 → 400으로 올렸더니 처리량 그대로, p99 2배 | 병목이 하류 풀(DB)로 이동, 늘린 스레드는 그 앞에서 줄 섬 | 커넥션 풀 대기 시간 | [20-3](../20-performance-method-and-amdahl/2-summary.md) |
| 로그 수집기·NFS가 느린 시각에 API p99 동반 상승, CPU 한가. 스레드 덤프에 `FileOutputStream.write` | 동기 로깅 — 목적지 꼬리가 요청 경로에 들어옴 | 스레드 덤프의 쓰기 프레임 수 | [15-3](../15-logging/2-summary.md) |
| 평소 몇 ms인 API가 가끔 500ms 넘게 멈춤 | Logback 비동기 큐가 차서 WARN 이상 기록에서 기다림 | appender 큐 크기·`neverBlock`·남은 칸(`getRemainingCapacity()`). Logback 1.5.18은 버린 수를 세지 않으므로 직접 계측한 값 | [15-4](../15-logging/2-summary.md) |
| 특정 요청 유형(큰 페이로드)만 꾸준히 실패, 서버는 한가 | 데드라인이 그 유형에는 너무 짧음 | 요청 유형별 실패율·지연 분포 | [05-5](../05-timeouts-and-deadline-propagation/2-summary.md) |
| 타임아웃 에러는 없는데 호출이 수십 초~수 분. 스레드 덤프에 소켓 `read` | read(idle) 타임아웃만 있음 → 조금씩 흘러오는 응답(slow drip)은 안 끝남 | 클라이언트에 전체(call) 타임아웃이 있나 | [07-2](../07-timeout-taxonomy-by-layer/2-summary.md) |
| 호출 타임아웃은 2초인데 사용자 지연 30초 초과 | 풀 대기가 타임아웃 밖. HikariCP 기본 `connectionTimeout` 30초 | `hikaricp_connections_pending`, 풀 획득 시간 | [07-3](../07-timeout-taxonomy-by-layer/2-summary.md) |
| 배치 도입 뒤 처리량은 늘었는데 한가한 시간 p99 +20ms | 배치 모으기 대기(maxWait)가 지연에 더해짐 | 시간대별 배치 크기와 대기 | [40-3](../40-batching-and-round-trips/2-summary.md) |
| 야간 적재가 몇 분, DB CPU 한가. 같은 INSERT `calls`가 행 수만큼 | 행마다 왕복 + 커밋 flush | 문장 통계의 calls·평균 시간 | [40-1](../40-batching-and-round-trips/2-summary.md) |
| 조용한 시간 뒤 첫 1초에만 하류 지연이 튐 | 토큰 버킷의 1초 상한 = 용량 + 충전량 | 리미터 용량 설정 | [11-3](../11-rate-limiter/2-summary.md) |
| 리미터를 켠 뒤 요청 스레드 고갈 | Resilience4j `RateLimiter` 기본 `timeoutDuration` 5초 동안 허가를 기다림 | 스레드 덤프의 리미터 대기 | [11-5](../11-rate-limiter/2-summary.md) |
| 격벽을 넣었는데 지연이 더 김. 스레드 덤프에 `Semaphore.tryAcquire` | 격벽 `maxWaitDuration`이 길어 기다리는 것도 요청 스레드 | 격벽 대기 설정 | [28-2](../28-bulkhead/2-summary.md) |
| 한 셀·한 샤드·한 파티션만 느림, 늘려도 그대로 | 큰 테넌트·핫 키. 해시는 고객 수만 고르게 나눔 | `topk`로 테넌트·키별 트래픽 | [51-3](../51-cells-stamps-and-blast-radius/2-summary.md) · [03-3](../03-failure-at-scale/2-summary.md) · [21-5](../21-scaling-principles/2-summary.md) |

**배포·확장 직후에만 느리다** (커리큘럼 추가 증상)

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 배포·스케일아웃 직후 몇 분간 p99만 튐, 평균은 멀쩡. 새 파드만 느림 | JIT 워밍업·캐시 채우기를 트래픽을 받으며 함. readiness가 "포트 열림"만 봄 | 파드별 지연, 첫 N건의 지연 계단 | [42-2](../42-cold-start-and-scale-from-zero/2-summary.md) · [19-4](../19-performance-measurement/2-summary.md) · [language/23-jit-tiered-compilation-and-warmup](../../language/23-jit-tiered-compilation-and-warmup/2-summary.md) |
| 새 인스턴스 쪽에만 타임아웃, `curl -w`의 `time_appconnect`가 큼 | 타임아웃 값이 재사용 연결 기준 — 새 연결의 TLS가 넘음 | 새 연결과 재사용 연결의 시간 분해 | [07-4](../07-timeout-taxonomy-by-layer/2-summary.md) |
| 한동안 호출이 없던 함수의 첫 요청만 타임아웃. `REPORT` 줄에 `Init Duration` | 서버리스 Init(패키지·정적 초기화·JVM 시작) | Init Duration 분포, 호출자 타임아웃 | [42-1](../42-cold-start-and-scale-from-zero/2-summary.md) |
| provisioned concurrency를 켰는데 피크에만 지연 | 예열 수 < 피크 동시성(피크 초당 요청 × 실행 시간) | 동시 실행 수가 설정을 넘는 구간 | [42-4](../42-cold-start-and-scale-from-zero/2-summary.md) |
| 전체 재시작 뒤 DB 과부하, 그 때문에 워밍업도 늦음 | 모든 인스턴스가 콜드 캐시로 동시 시작 | 재시작 직후 적중률·DB QPS | [42-5](../42-cold-start-and-scale-from-zero/2-summary.md) · [22-5](../22-capacity-and-load-testing/2-summary.md) |

**비동기·가상 스레드로 바꿨더니 더 느리다** (커리큘럼 추가 증상)

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| WebFlux 전환 뒤 부하가 조금만 와도 전부 느림. `reactor-http-nio-*` 스택이 JDBC 소켓 읽기 | 이벤트 루프(몇 개뿐 — Reactor Netty 기본 max(코어 수, 4)) 위에서 블로킹 호출 | 루프 스레드 스택 | [39-1](../39-async-io-gains-and-limits/2-summary.md) |
| 가상 스레드 전환 뒤 동시성이 코어 수 근처에 묶임. JFR `jdk.VirtualThreadPinned` | JDK 21에서 `synchronized` 안 블로킹 → 운반 스레드 고정 | 고정 이벤트의 스택 | [39-3](../39-async-io-gains-and-limits/2-summary.md) |
| 가상 스레드 전환 뒤 DB 풀 고갈 | 동시 요청이 스레드 풀 크기에서 사실상 무제한으로 → 대기 장소가 DB 풀 앞으로 이동 | 커넥션 pending·획득 시간 p99 | [39-2](../39-async-io-gains-and-limits/2-summary.md) |
| 전환 뒤 처리량 변화 없음, CPU는 이미 높음 | CPU 바운드 — 코어 수가 상한 | CPU 사용률·프로파일 | [39-5](../39-async-io-gains-and-limits/2-summary.md) |

**고쳤는데 빨라지지 않는다** — 측정·최적화 방법의 증상

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 직렬화 라이브러리를 바꿔 그 구간이 2배 빨라졌는데 p99 그대로 | Amdahl — 5% 구간이면 전체 약 2.5%, 잡음에 묻힘 | 착수 전 구간별 비율과 최대 단축률 | [20-1](../20-performance-method-and-amdahl/2-summary.md) |
| 2주 최적화 뒤 p99 그대로, wall 프로파일은 풀 대기 | CPU 프로파일만 봄 — 기다리는 스레드는 CPU 프로파일에 안 보임 | CPU가 바쁜가 → 아니면 wall·lock·off-CPU | [36-1](../36-profiling/2-summary.md) |
| 프로파일러가 지목한 작은 메서드를 고쳐도 무변화 | 세이프포인트 편향 샘플러 | async-profiler로 다시 뜸 | [36-2](../36-profiling/2-summary.md) |
| 장애 때 느렸는데 다음 날 프로파일은 깨끗 | 문제 구간이 지난 뒤 떴음 | 지속 프로파일링 기록이 있나 | [36-4](../36-profiling/2-summary.md) |
| `perf_event_open ... failed: Operation not permitted`, 커널 시간이 프로파일에 없음 | Docker 기본 seccomp·`perf_event_paranoid` | 프로파일러 경고, 이벤트 모드(`ctimer`) | [36-3](../36-profiling/2-summary.md) |
| JVM·커널 플래그를 한꺼번에 바꾼 뒤 회귀, 원인 모름 | 변경과 효과의 대응이 깨짐 | 하나씩 다시 적용(bisect) | [20-2](../20-performance-method-and-amdahl/2-summary.md) |
| `top`의 CPU 30%라 "여유 있다" → 실제는 디스크 대기열 | 가로등 효과 — 도구가 보여 주는 자원만 봄 | USE 자원 목록 전체 | [20-4](../20-performance-method-and-amdahl/2-summary.md) |
| 마이크로벤치 결과가 1ns 미만("100배 빠름") | 결과를 버려 DCE, 상수 접기 | 빈 메서드 baseline과 비교 | [38-1](../38-microbenchmarking/2-summary.md) |
| 같은 손 측정이 3배 다름, 반복 수를 바꾸면 ns/op도 변함 | 워밍업·OSR 구간이 섞임 | JMH로 다시 | [38-2](../38-microbenchmarking/2-summary.md) |
| 벤치마크 실행 순서마다 결과가 뒤바뀜 | 포크 없이 한 JVM에서 프로파일이 섞임 | `@Fork` 값 | [38-3](../38-microbenchmarking/2-summary.md) |
| 37ns vs 33ns로 "10% 개선" 머지, 다음 측정은 반대 | Error 구간이 차이보다 큼 | 포크·반복을 늘려 구간 비교 | [38-4](../38-microbenchmarking/2-summary.md) |

### 3. 에러 — 실패한다

#### 3-1. 문구 사전 (제품·판 명시, 출처는 관련 주제·근거)

| 보이는 문구 | 누가 냈나 | 흔한 원인 | leaf |
|---|---|---|---|
| HTTP `504`, 본문 `upstream request timeout`, 통계 `upstream_rq_timeout` | Envoy(1.35 `router.cc`) 라우트 타임아웃 | 게이트웨이 timeout < 서비스 안 최악 시간, 폴백 몫 없음 | [35-1](../35-timeout-design-worksheet/2-summary.md) · [08-5](../08-time-budget-allocation/2-summary.md) |
| `upstream_rq_per_try_timeout`·`upstream_rq_retry` 증가 + 결제사 승인 2~3건 | Envoy per-try 재시도 | 비멱등 POST 라우트에 `retry_on` | [35-2](../35-timeout-design-worksheet/2-summary.md) |
| `503`, 본문 `upstream connect error or disconnect/reset before headers. ...` | Envoy(1.35 `router.cc`) — 응답 헤더 전에 연결 실패·리셋 | 종료 중인 대상, 사이드카 미기동, 레지스트리의 죽은 인스턴스, 메시 설정 오류 | [14-1](../14-graceful-shutdown/2-summary.md) · [50-2](../50-sidecar-ambassador-and-service-mesh/2-summary.md) · [50-3](../50-sidecar-ambassador-and-service-mesh/2-summary.md) · [50-4](../50-sidecar-ambassador-and-service-mesh/2-summary.md) |
| `502`·`connection refused`가 롤링 배포 구간에만 짧게 | 인그레스·LB | LB 해제 반영 전에 앱이 종료 | [14-1](../14-graceful-shutdown/2-summary.md) |
| 오래 조용하다가 첫 요청이 `Connection reset`·`socket hang up`·502 | 클라이언트(OS·Node) | 클라이언트 idle 수명 > 중간 장비·서버 idle | [07-5](../07-timeout-taxonomy-by-layer/2-summary.md) |
| `UND_ERR_SOCKET`·"connection reset"이 전환 순간 한 번 튐 | Node undici 클라이언트 | 블루그린 전환·reload 때 옛 인스턴스가 keep-alive를 닫음 | [23-4](../23-deployment-strategies/2-summary.md) |
| `java.net.http.HttpTimeoutException: request timed out` | JDK 21 `HttpClient`(실행 확인) | 응답 헤더까지 늦음. 요청 `timeout`이 없으면 무한히 기다림 | [05-2](../05-timeouts-and-deadline-propagation/2-summary.md) · [07-2](../07-timeout-taxonomy-by-layer/2-summary.md) |
| `HttpConnectTimeoutException: HTTP connect timed out` / `ConnectException: Connection timed out` | JDK 21 `HttpClient` / OS 재전송 한도 | connect 타임아웃 설정 유무. SYN이 DROP됨 | [07-1](../07-timeout-taxonomy-by-layer/2-summary.md) |
| `CallNotPermittedException: CircuitBreaker 'x' is OPEN and does not permit further calls` | Resilience4j 2.4.0 | 회로 열림. 폴백 없음, 과민 임계, 4xx를 실패로 셈, 재시도가 바깥 | [10-2](../10-circuit-breaker/2-summary.md) · [10-1](../10-circuit-breaker/2-summary.md) · [10-4](../10-circuit-breaker/2-summary.md) · [10-5](../10-circuit-breaker/2-summary.md) |
| `BulkheadFullException: Bulkhead 'x' is full and does not permit further calls` | Resilience4j 2.4.0 | 하류가 느려 칸이 참(의도된 거절) 또는 칸이 작음 | [28-1](../28-bulkhead/2-summary.md) · [28-5](../28-bulkhead/2-summary.md) |
| `RequestNotPermitted: RateLimiter 'x' does not permit further calls` | Resilience4j 2.4.0 | 한도 초과. 서킷 브레이커가 이것을 실패로 세면 안 됨 | [10-4](../10-circuit-breaker/2-summary.md) · [11-5](../11-rate-limiter/2-summary.md) |
| `TimeoutException`(TimeLimiter) 지표는 높은데 서킷은 CLOSED·실패율 0% | Resilience4j 데코레이터 순서 `TL(CB(call))` | 데코레이터 순서, `slowCallDurationThreshold` | [35-4](../35-timeout-design-worksheet/2-summary.md) · [10-3](../10-circuit-breaker/2-summary.md) |
| `SQLTransientConnectionException: <풀> - Connection is not available, request timed out after Nms (total=…, active=…, idle=…, waiting=…)` | HikariCP 6.3.0 `HikariPool` | 느린 쿼리·누수·트랜잭션 안 외부 호출·동시성 급증 | [07-3](../07-timeout-taxonomy-by-layer/2-summary.md) · [39-2](../39-async-io-gains-and-limits/2-summary.md) · [28-4](../28-bulkhead/2-summary.md) · [29-1](../29-cache-stampede/2-summary.md) |
| `FATAL: sorry, too many clients already` | PostgreSQL 17 | 인스턴스 수 × 풀 크기 > `max_connections` | [47-4](../47-server-design-antipatterns/2-summary.md) · [21-2](../21-scaling-principles/2-summary.md) · [41-3](../41-autoscaling/2-summary.md) · [03-4](../03-failure-at-scale/2-summary.md) |
| `RejectedExecutionException: Task … rejected from java.util.concurrent.ThreadPoolExecutor@…[Running, pool size = …, active threads = …, queued tasks = …, …]` | JDK 21 `ThreadPoolExecutor`(실행 확인) | 유계 큐가 참 — 의도된 거절이면 503으로 매핑 | [12-1](../12-backpressure-and-load-shedding/2-summary.md) |
| `429`가 한 IP에 몰리고 그 뒤에 계정 수백 개 | 리미터 | 제한 키가 IP(NAT) | [11-4](../11-rate-limiter/2-summary.md) |
| `429` 비율 90% 초과, 요청 수가 오히려 증가 | 리미터 + 클라이언트 | `Retry-After` 없음, 지터 없는 즉시 재시도. nginx `limit_req` 기본 거절 코드는 503 | [11-6](../11-rate-limiter/2-summary.md) |
| `431 Request Header Fields Too Large` | 하류 서버 | baggage 항목이 계속 덧붙음 | [17-5](../17-distributed-tracing/2-summary.md) |
| `Packet for query is too large (N > M). You can change this value on the server by setting the 'max_allowed_packet' variable.` | MySQL Connector/J(9.x `LocalizedErrorMessages`) | 배치 하나가 패킷 한도 초과 | [40-2](../40-batching-and-round-trips/2-summary.md) |
| `Cannot assign requested address`(`EADDRNOTAVAIL`), `ss` TIME_WAIT 수만 | 커널 `connect(2)` | 요청마다 HTTP 클라이언트·연결 생성 | [48-1](../48-performance-and-stability-antipatterns-in-code/2-summary.md) |
| `No space left on device`(`ENOSPC`) | 커널 | 로그 회전 없음, 힙 덤프, 정리 작업 부재 | [15-1](../15-logging/2-summary.md) · [37-3](../37-memory-leak-and-heap-analysis/2-summary.md) · [49-1](../49-steady-state-fail-fast-and-supervision/2-summary.md) |
| `UnrecognizedPropertyException` 류 역직렬화 예외, **양쪽 버전 모두**에서 | 앱(Jackson 등) | 신·구 버전 공존 중 형식 비호환 | [23-1](../23-deployment-strategies/2-summary.md) |
| 롤백한 옛 버전이 `column "…" does not exist` | DB | 새 버전이 이미 스키마를 바꿈(롤백은 코드만 되돌림) | [23-2](../23-deployment-strategies/2-summary.md) |
| `ERROR: function pg_current_xlog_location() does not exist` | PostgreSQL 10+ | 런북 명령이 구 버전 기준 | [44-2](../44-runbooks-and-operational-readiness/2-summary.md) |
| 평가 reason이 `ERROR`로 몰림, `FLAG_NOT_FOUND` 류가 특정 파드에서만 | OpenFeature SDK | 플래그 서비스 장애 → 코드의 기본값. 설정을 분기 제거보다 먼저 지움 | [24-2](../24-feature-flag-lifecycle/2-summary.md) · [24-5](../24-feature-flag-lifecycle/2-summary.md) |
| 이벤트 `TooManyMissedTimes`: `too many missed start times. Set or decrease .spec.startingDeadlineSeconds or check clock skew` | Kubernetes 1.34 CronJob 컨트롤러 | 놓친 회차가 100개 초과 | [30-4](../30-scheduler-and-cron-ha/2-summary.md) |
| `CrashLoopBackOff` | kubelet | 재시작으로 안 낫는 원인(poison pill, 설정 오류, 없는 의존성) | [49-4](../49-steady-state-fail-fast-and-supervision/2-summary.md) |
| `Readiness probe failed: …`·`Liveness probe failed: …` | kubelet(1.34 `prober.go`의 `%s probe failed: %s`) | 프로브가 의존성을 봄, 같은 풀을 씀, 프로브 타임아웃이 꼬리 안 | [47-2](../47-server-design-antipatterns/2-summary.md) · [48-3](../48-performance-and-stability-antipatterns-in-code/2-summary.md) · [33-5](../33-hysteresis-and-flapping/2-summary.md) · [41-5](../41-autoscaling/2-summary.md) |

#### 3-2. 문구 없는 에러 패턴

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 회로가 열렸는데 에러율 그대로, 지연만 0ms | 폴백 없음 — 열림 예외가 500으로 매핑 | 열림 예외 처리 위치 | [10-2](../10-circuit-breaker/2-summary.md) |
| 하류는 반쯤 살아 있는데(실패 30%) 회로가 초 단위로 열고 닫힘 | 창·최소 표본이 작고 반열림 허용 1건 | 상태 전이 로그 빈도, `not_permitted` 수 | [10-1](../10-circuit-breaker/2-summary.md) · [33-4](../33-hysteresis-and-flapping/2-summary.md) |
| 하류 지표는 정상(4xx만 증가)인데 우리 회로 OPEN | 기본 설정이 모든 예외를 실패로 셈 | `recordExceptions`·`ignoreExceptions` | [10-4](../10-circuit-breaker/2-summary.md) |
| 잠깐 흔들렸을 뿐인데 회로가 열림, 창에 같은 요청의 시도가 여러 건 | Retry가 CircuitBreaker 바깥 | 애스펙트 순서 | [10-5](../10-circuit-breaker/2-summary.md) |
| 하류 p99 30초인데 회로 CLOSED, 창 기록 수가 안 늚 | 결과는 호출이 끝나야 기록. 느린 호출 기준 기본 60초·100% | `slowCall*` 설정, 안쪽 타임아웃 | [10-3](../10-circuit-breaker/2-summary.md) |
| "재시도 3회"인데 재시도 지표 거의 0, 실패 지연이 전체 타임아웃 근처 | per-try 타임아웃 없음 → 첫 시도가 예산을 다 씀 | 실패 요청의 지연 분포 | [08-2](../08-time-budget-allocation/2-summary.md) |
| "재시도 3회"인데 일시 지연에도 바로 실패, 실패 뒤에도 하류 호출 로그 | `TimeLimiter(Retry(call))` — 바깥 TimeLimiter가 재시도 전체를 자름 | 실패까지 걸린 시간 = TimeLimiter 값인가 | [35-3](../35-timeout-design-worksheet/2-summary.md) |
| 앞 단계가 조금 느린 날 마지막 단계만 설정값보다 짧게 타임아웃 | 단계 타임아웃의 합 > 전체 예산 | 예산표 합계 | [08-1](../08-time-budget-allocation/2-summary.md) |
| 폴백을 만들어 뒀는데 장애 때 504 | 폴백·직렬화 몫을 예약하지 않음 | 폴백 실행 로그 수 | [08-5](../08-time-budget-allocation/2-summary.md) |
| 하류 지연이 조금 오르자 타임아웃 수십 %, 하류 요청량 2배 | 타임아웃을 p50 근처로 잡음 → 정상 응답 절반을 끊고 재시도 | 타임아웃 값 vs 하류 분포 | [08-4](../08-time-budget-allocation/2-summary.md) |
| 하류 실패가 10%대로 조금 올랐는데 사용자 에러가 그보다 크게 늚, "throttled" 로그 | 재시도 스로틀(gRPC `tokenRatio`)이 예민 | 재시도 토큰 지표 | [06-5](../06-retry-backoff-jitter/2-summary.md) |
| Redis가 내려가자 모든 API 에러 | 리미터 오류가 요청 실패로 전파(fail closed) | 리미터 예외 처리 | [11-5](../11-rate-limiter/2-summary.md) |
| 한도 100/초인데 하류가 초 경계마다 200/초 가까이 받음 | 고정 창 경계 리셋 | 하류 요청률의 초 경계 봉우리 | [11-1](../11-rate-limiter/2-summary.md) |
| 한도 100인데 사용자당 105~110건 통과, 부하 높을수록 초과 | "GET → 비교 → INCR" 비원자(TOCTOU) | 리미터 구현의 원자성 | [11-2](../11-rate-limiter/2-summary.md) |
| 새벽에 요청 몇 건 중 1건 실패로 page | 비율 SLI의 분모가 작음 | 그 시간대 요청 수 | [02-5](../02-slo-sli-error-budget/2-summary.md) · [43-4](../43-alerting-and-on-call/2-summary.md) |
| 특정 서버만 데드라인 초과가 거의 없거나, 받자마자 거절 | 절대 시각을 전파 + 그 서버 시계 어긋남 | `chronyc tracking` 오프셋 | [05-3](../05-timeouts-and-deadline-propagation/2-summary.md) |
| 헬스체크 업타임 ~100%인데 "자주 안 된다" 문의, 특정 지역·API·고객만 실패 | 시간 기반 가용성이 부분 장애를 못 봄, 헬스체크가 실제 경로를 안 탐 | 요청 기반 SLI를 경로·고객군별로 | [01-3](../01-fault-error-failure-availability/2-summary.md) |
| 파드 첫 몇 초만 외부 호출 실패, localhost 프록시 포트로 `ConnectException`(raw 소켓은 `Connection refused`, JDK 21 `HttpClient`는 메시지 `null` + 원인 `ClosedChannelException`) | 사이드카보다 앱이 먼저 시작 | 컨테이너 시작 순서 | [50-2](../50-sidecar-ambassador-and-service-mesh/2-summary.md) |
| 파드 종료 몇 초 동안 그 파드가 보낸 외부 호출 실패 | 일반 컨테이너 사이드카가 먼저 종료 | 사이드카 종료 시각 | [50-5](../50-sidecar-ambassador-and-service-mesh/2-summary.md) |
| 인스턴스 하나가 죽은 뒤 몇 초~몇십 초 동안 요청의 1/N 실패 | 레지스트리 TTL 동안 죽은 주소 잔존 | 실패 주소가 하나로 모이나 | [50-3](../50-sidecar-ambassador-and-service-mesh/2-summary.md) |
| 셔플 샤딩을 했는데 독 고객과 작업자 하나만 겹친 고객도 오류 | 클라이언트가 다른 작업자로 재시도하지 않음 | 클라이언트 재시도 대상 | [51-4](../51-cells-stamps-and-blast-radius/2-summary.md) |

### 4. 연쇄·전면 장애 — 번지고, 복구되지 않는다

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 의존성 하나가 느려졌는데 서비스 전체가 거의 모든 요청에 실패. 스레드 덤프 대부분이 같은 소켓 읽기 | 타임아웃 없음 + 공유 스레드 풀 | `jcmd <pid> Thread.print`를 맨 위 프레임으로 묶어 센다(적용 3) | [05-2](../05-timeouts-and-deadline-propagation/2-summary.md) · [28-1](../28-bulkhead/2-summary.md) · [21-3](../21-scaling-principles/2-summary.md) |
| 위와 같은데 liveness 실패로 파드가 연달아 재시작 | 헬스체크가 같은 풀을 씀. 재시작이 처리 중 요청까지 끊음 | 프로브 경로가 요청 풀과 분리됐나 | [48-3](../48-performance-and-stability-antipatterns-in-code/2-summary.md) |
| DB가 2초 느려졌을 뿐인데 전 인스턴스 unhealthy, 전면 503 | 깊은 헬스체크(의존성 확인) | 헬스체크 지연 = DB 지연인가 | [47-2](../47-server-design-antipatterns/2-summary.md) |
| 셰딩을 시작한 인스턴스가 LB에서 빠지고 남은 인스턴스가 차례로 과부하 | 헬스체크가 같은 큐·입장 판정을 탐 | 대상 제외 이벤트의 연쇄 | [12-4](../12-backpressure-and-load-shedding/2-summary.md) |
| 피크에 한 대가 죽자 나머지가 연쇄로 넘어짐 | 평소 이용률이 (N−1)/N보다 높음 | "한 대 빠지면" 사용률 | [22-2](../22-capacity-and-load-testing/2-summary.md) · [47-3](../47-server-design-antipatterns/2-summary.md) · [25-5](../25-high-availability-topology/2-summary.md) |
| DB가 몇 초 느렸을 뿐인데 수십 분 회복 안 됨. 도착률이 신규의 몇 배 | 재시도가 유지 효과가 된 준안정(metastable) 고장 | 재시도 비율·도착률 vs 신규 요청률 | [03-1](../03-failure-at-scale/2-summary.md) · [06-3](../06-retry-backoff-jitter/2-summary.md) |
| DB에 같은 상관 ID의 같은 쿼리가 수십 번, 층마다 `retries: 3` | 계층마다 재시도 → 곱셈 증폭(4³ = 64) | 층별 재시도 설정 목록 | [06-2](../06-retry-backoff-jitter/2-summary.md) · [50-1](../50-sidecar-ambassador-and-service-mesh/2-summary.md) |
| 하류 요청률이 일정 간격(100·200·400ms…)으로 뾰족, 봉우리마다 503 | 지터 없는 지수 백오프 — 동기화된 재시도 | 재시도 시각 분포 | [06-1](../06-retry-backoff-jitter/2-summary.md) |
| 503을 늘렸더니 요청이 2~3배, 같은 요청 ID가 짧은 간격으로 반복 | 클라이언트가 거절을 즉시 재시도 | 요청 ID별 시도 수 | [12-5](../12-backpressure-and-load-shedding/2-summary.md) |
| 과부하 동안 CPU 100%인데 성공 응답 거의 0, 부하를 조금 줄여도 회복 안 됨 | 헛일 — 클라이언트가 포기한 요청을 끝까지 처리, FIFO 큐 대기가 데드라인 초과 | 응답 쓰기의 `Broken pipe` 수, 큐 대기 시간, 상류·하류 타임아웃 역전(상류 5s·하류 10s) | [09-1](../09-cancellation-propagation/2-summary.md) · [12-2](../12-backpressure-and-load-shedding/2-summary.md) · [05-1](../05-timeouts-and-deadline-propagation/2-summary.md) · [08-3](../08-time-budget-allocation/2-summary.md) |
| 큐에서 늦은 요청을 버리게 고쳤는데 타임아웃률 그대로 | 꺼낼 때는 안 늦었지만 처리 시간을 더하면 늦음 | 성공 응답 지연이 데드라인 바로 위에 몰리나 | [12-3](../12-backpressure-and-load-shedding/2-summary.md) |
| 캐시 재시작 직후 DB 과부하 | 용량이 캐시 위에 있었음 | 적중률 하락과 DB 부하의 시각 | [03-5](../03-failure-at-scale/2-summary.md) |
| 정각·주기마다 DB CPU 100%, `pg_stat_activity`에 같은 SELECT 수백 개 | 인기 키 만료 순간의 동시 miss(스탬피드) | 같은 쿼리 동시 실행 수 | [29-1](../29-cache-stampede/2-summary.md) |
| 싱글플라이트를 넣었는데 인스턴스 수만큼 같은 쿼리 | 싱글플라이트는 프로세스 로컬 | DB 쪽 동시 실행 수 = 인스턴스 수인가 | [29-2](../29-cache-stampede/2-summary.md) |
| 배포 뒤 정확히 TTL마다 DB 스파이크, 점점 잦아듦 | 같은 시각에 채운 키가 같은 시각에 만료(눈사태) | DB 쿼리 수의 TTL 주기 톱니 | [29-3](../29-cache-stampede/2-summary.md) |
| 적중률 낮고 DB 조회 많은데 결과는 대부분 0행 | "없음"을 캐시하지 않음(관통) | 로더가 null을 돌려주는 비율 | [29-4](../29-cache-stampede/2-summary.md) |
| DB 장애가 끝났는데 특정 키만 계속 실패, 재시작하면 나음 | 싱글플라이트가 실패한 Future를 안 지움 | 같은 예외가 원인 해소 뒤에도 반복되나 | [29-5](../29-cache-stampede/2-summary.md) |
| 매일 00:00 정각에 수직 상승, 또는 쿠폰 푸시 직후 멈춤 | Dogpile(모든 인스턴스가 같은 시각) · Self-Denial(우리 결정이 만든 트래픽) | 요청 출처 | [48-4](../48-performance-and-stability-antipatterns-in-code/2-summary.md) · [41-1](../41-autoscaling/2-summary.md) |
| 셀로 나눴는데 전 셀 고객이 동시에 멈춤 | 셀 간 공유 구성 요소 | 공통 의존성 오류 시각 | [51-1](../51-cells-stamps-and-blast-radius/2-summary.md) |
| 셀은 멀쩡한데 전부 접속 불가 | 셀 라우터·매핑 저장소가 SPOF | 라우터 5xx, 셀 쪽 트래픽 0 | [51-2](../51-cells-stamps-and-blast-radius/2-summary.md) |
| 설정 하나 배포 직후 무관한 서비스들이 동시에 503 | 메시 컨트롤 플레인이 모든 프록시에 내려보냄 | 컨트롤 플레인 배포 이력 | [50-4](../50-sidecar-ambassador-and-service-mesh/2-summary.md) |
| Active-Active 2대가 같은 시각에 함께 죽음 | 공통 원인 고장(같은 배포·설정·인증서·AZ) | 두 인스턴스의 에러 시작 시각과 변경 이력 | [01-2](../01-fault-error-failure-availability/2-summary.md) · [25-2](../25-high-availability-topology/2-summary.md) |
| 의존 서비스가 느려지자 오토스케일러가 `maxReplicas`까지 늘림, 처리량 그대로 | 지표가 "일이 많다"와 "막혀 있다"를 구분 못 함 | 레플리카 수 vs 처리량 vs 하류 오류율 | [41-4](../41-autoscaling/2-summary.md) |
| 몇 분 만에 인스턴스·데이터·디스크 대부분이 사라짐 | 자동화 대상 판정 버그(빈 집합 = 전부) + 속도 상한 없음 | 자동화 로그의 삭제 요청 수·대상 목록 | [49-5](../49-steady-state-fail-fast-and-supervision/2-summary.md) |
| 복구 직후 밀린 회차 수십 개가 한꺼번에 돌아 DB가 다시 느려짐 | 보정 정책이 "전부, 즉시, 동시" | 재시작 직후 동시 실행 수 | [30-5](../30-scheduler-and-cron-ha/2-summary.md) |

### 5. 배포·변경 직후

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 롤링 배포 구간에만 502 몇 초, 앱 로그에는 오류 없음 | LB 해제(EndpointSlice 반영) 전에 앱 종료 | 502 시각과 파드 종료 시각 | [14-1](../14-graceful-shutdown/2-summary.md) |
| 종료가 매번 유예 시간을 꽉 채우고 종료 코드 137, `OOMKilled=false`, SIGTERM 수신 로그 없음 | 셸 형식 CMD로 `sh`가 PID 1 — SIGTERM을 앱에 안 넘김 | `/proc/1/cmdline` | [14-2](../14-graceful-shutdown/2-summary.md) |
| 종료 로그에 "기한 초과, 처리 중 N건"이 매번 | keep-alive·HTTP/2 연결로 새 요청이 계속 들어옴 | 드레이닝 중 새 요청 수 | [14-3](../14-graceful-shutdown/2-summary.md) |
| 종료 훅 로그가 중간에 끊기고 137 | 유예 < 전파 대기 + 드레이닝 기한 | 두 기한의 합 | [14-4](../14-graceful-shutdown/2-summary.md) |
| 배포 뒤 일부 메시지가 다시 처리되거나 흔적 없이 사라짐 | 종료 훅이 HTTP만 드레이닝, 컨슈머는 그냥 끊음 | 같은 메시지 ID 처리 로그 수 | [14-5](../14-graceful-shutdown/2-summary.md) |
| 배포를 시작하면 4xx·5xx 상승, 끝나면 사라짐, 롤백 중에도 상승 | 신·구 버전 공존 비호환 | 버전 레이블별 오류 — 양쪽 모두인가 | [23-1](../23-deployment-strategies/2-summary.md) |
| 롤백했는데 옛 버전이 오류 | 되돌릴 수 없는 변경(스키마·새 형식 데이터) | 옛 버전 로그의 스키마 오류 | [23-2](../23-deployment-strategies/2-summary.md) |
| 대부분 정상인데 한 대만 이상 동작 | 그 한 대에만 배포 누락(Knight Capital: 8대 중 1대) | 전 서버 실행 버전 조회 | [23-3](../23-deployment-strategies/2-summary.md) · [24-1](../24-feature-flag-lifecycle/2-summary.md) · [04-4](../04-failure-modes-catalog/2-summary.md) |
| 카나리는 멀쩡했는데 100%에서 지연 폭증 | 카나리 표본이 대표적이지 않음(시간대·트래픽) | 카나리 기간·비교 방식(before/after인가) | [23-5](../23-deployment-strategies/2-summary.md) |
| 플래그 서비스가 내려간 순간 5% 기능이 전원에게 열림 | SDK가 오류 시 코드의 기본값(`true`)을 돌려줌 | 평가 reason 분포 | [24-2](../24-feature-flag-lifecycle/2-summary.md) |
| 새로고침마다 다른 버튼, 한 화면에 신·구 UI | 요청 단위 무작위 평가 | 평가 키가 사용자 키인가 | [24-3](../24-feature-flag-lifecycle/2-summary.md) |
| "특정 플래그 조합에서만" 나는 버그 | 방치 플래그 수백 개 | 등록부와 코드의 플래그 대조 | [24-4](../24-feature-flag-lifecycle/2-summary.md) |
| 배포 직후 Prometheus 메모리가 오르다 OOM 재시작 | 레이블 카디널리티 폭발(`user_id`·원시 URL) | `prometheus_tsdb_head_series`, `/api/v1/status/tsdb` | [16-1](../16-metrics-and-golden-signals/2-summary.md) |
| 재시작할 때마다 요청률 그래프에 평소의 수십~수백 배 같은 거대한 스파이크(`rate()`는 음수를 내지 않는다) | `rate(sum(...))` — 합친 카운터가 조금 줄면 `rate()`가 리셋으로 보고 직전 값 전체를 증가분에 더함 | 식의 집계 순서 | [16-4](../16-metrics-and-golden-signals/2-summary.md) |
| 배포 직후 캐시 값 역직렬화 실패 | 캐시 포맷 변경 | [database/56 증상 사전](../../database/56-db-symptom-index/2-summary.md) | [23-1](../23-deployment-strategies/2-summary.md) |
| 배포 뒤 다음 회차 잡이 "이미 실행 중"으로 시작 안 함, `STARTED`인데 프로세스 없음 | SIGTERM에 잡이 죽어 락·상태만 남음 | 실행 테이블 상태와 하트비트 | [31-4](../31-batch-job-restart-and-checkpoint/2-summary.md) |
| 배포 직후 오류율이 꺾였는데 원인 분석만 한 시간 | 완화와 원인 규명을 한 단계로 생각 | 배포 시각과 겹치나 → 먼저 롤백 | [26-1](../26-incident-response-and-postmortem/2-summary.md) |

### 6. 자원 — 메모리·스레드·커넥션·디스크

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 힙 바닥선이 GC 뒤에도 우상향하는 톱니 → `java.lang.OutOfMemoryError: Java heap space`(실행 확인) | 루트(static·싱글턴)에서 닿는 컬렉션 증가 | `HeapDumpOnOutOfMemoryError` 덤프의 지배자 트리 | [37-1](../37-memory-leak-and-heap-analysis/2-summary.md) |
| 에러 0%인데 p99 계단 상승, 힙이 톱니 없이 우상향 → OOM | 무한 큐(`newFixedThreadPool`의 무제한 큐 등) | 큐 길이·체류 시간 | [12-1](../12-backpressure-and-load-shedding/2-summary.md) |
| 동시 작업 수에 비례해 힙 상승 → Full GC 연속 → OOM | 비동기 팬아웃에 상한 없음 | 동시 작업 수 | [39-4](../39-async-io-gains-and-limits/2-summary.md) |
| 특정 고객 요청에서만 OOM, 덤프에 엔티티 리스트 수백만 | `LIMIT` 없는 조회 | 요청별 결과 건수 | [48-2](../48-performance-and-stability-antipatterns-in-code/2-summary.md) |
| **힙은 평평한데 RSS만 우상향** → 종료 코드 137, `OOMKilled=true` | direct buffer·스레드 스택·metaspace·native `malloc` | NMT baseline/diff, `docker inspect`의 OOMKilled | [37-2](../37-memory-leak-and-heap-analysis/2-summary.md) |
| `OutOfMemoryError: Cannot reserve N bytes of direct buffer memory (allocated: …, limit: …)`(실행 확인) | JDK 21 direct buffer 한도 도달 — 커널 kill 대신 JVM 예외로 바꾼 상태 | `MaxDirectMemorySize`와 컨테이너 한도 | [37-2](../37-memory-leak-and-heap-analysis/2-summary.md) |
| 재배포(핫 리로드)할 때마다 메모리 증가 → `OutOfMemoryError: Metaspace` | ThreadLocal·리스너가 옛 클래스로더를 붙듦 | 덤프에 같은 클래스가 로더별로 여러 벌 | [37-4](../37-memory-leak-and-heap-analysis/2-summary.md) |
| 원인 찾으려 덤프를 떴더니 서비스가 오래 멈추고 디스크가 참 | `GC.heap_dump`는 full GC + 힙 전체 쓰기 | GC 로그 `Pause Full (Heap Dump Initiated GC)` | [37-3](../37-memory-leak-and-heap-analysis/2-summary.md) |
| TimeLimiter 타임아웃이 잦아진 뒤 전용 풀이 차고 큐가 자람 | CompletionStage 경로는 원래 작업을 취소하지 않음 | 스레드 덤프의 하류 호출 중인 풀 스레드 수 | [09-2](../09-cancellation-propagation/2-summary.md) |
| 스레드풀 격벽으로 응답은 빨라졌는데 하류 부하 그대로 | `Future.get(timeout)`은 호출자만 놓아 줌 | 하류 접근 로그 수 vs 호출자 타임아웃 수 | [28-3](../28-bulkhead/2-summary.md) |
| 격벽 거절 0인데 결제 타임아웃, 풀 대기 메시지 | 칸 수 > 하류 커넥션 수 | 칸 수 vs 하류별 풀 크기 | [28-4](../28-bulkhead/2-summary.md) |
| 2코어 컨테이너에서만 `ThreadPoolBulkhead` 스레드 1~2개, 큐 가득 | Resilience4j 기본이 `availableProcessors` 기준 | 격벽 지표의 코어·최대 스레드 | [28-5](../28-bulkhead/2-summary.md) |
| 종료·취소해도 특정 작업이 끝까지 돎 | `catch (InterruptedException e) {}` | 코드의 인터럽트 처리 | [09-3](../09-cancellation-propagation/2-summary.md) |
| 같은 멱등 키 요청들이 DB 락 대기(`Lock: transactionid`)에 걸려 스레드·연결 고갈 | 한 트랜잭션 방식에서 진 쪽이 이긴 쪽 커밋을 기다림 | 대기 이벤트별 세션 수 | [13-5](../13-idempotency/2-summary.md) |
| 스레드 수가 시간에 따라 증가 + TIME_WAIT 수만 + `EADDRNOTAVAIL` | 요청마다 `new HttpClient` | `ss -tan state time-wait \| wc -l` | [48-1](../48-performance-and-stability-antipatterns-in-code/2-summary.md) |
| `ss`에 SYN-SENT가 쌓이고 스레드 덤프에 `Net.connect` | connect 타임아웃 없음 + 방화벽 DROP | SYN-SENT 수 | [07-1](../07-timeout-taxonomy-by-layer/2-summary.md) |
| 커넥션 풀 고갈 메시지 + 동기 복제 대기 세션(`wait_event = SyncRep`) | 동기 대기 서버 하나가 느림·끊김 | `pg_stat_activity`의 대기 이벤트 | [46-3](../46-disaster-recovery/2-summary.md) |
| 노드 디스크 100%, 같은 노드 다른 서비스까지 쓰기 실패, 같은 스택 트레이스 초당 수천 줄 | 실패 경로 로그 폭증, 회전 없음(Docker `json-file` 기본 `max-size=-1`) | 로그 줄 수 지표 | [15-1](../15-logging/2-summary.md) |
| 몇 달간 조금씩 느려지다 어느 날 쓰기 실패 | 쌓이는 자원(로그·이력 테이블)에 정리 장치 없음 | 디렉터리·테이블 크기 추이, 정리 잡 성공 지표 | [49-1](../49-steady-state-fail-fast-and-supervision/2-summary.md) |

### 7. 결과가 모호하다 — 중복·누락·"504인데 결제됨"

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| **사용자는 504를 받았는데 PG에는 승인**. "결제 실패라고 떠서 다시 했더니 두 번 빠짐" | 게이트웨이가 서비스의 결과 확정 전에 끊음 · 보낸 뒤의 호출은 취소 불가 · 타임아웃을 실패로 기록 | 같은 주문의 게이트웨이 504와 PG 승인 시각 | [35-1](../35-timeout-design-worksheet/2-summary.md) · [09-4](../09-cancellation-propagation/2-summary.md) · [35-5](../35-timeout-design-worksheet/2-summary.md) · [domain-modeling/25-reconciliation](../../domain-modeling/25-reconciliation/2-summary.md) |
| PG에 같은 주문 승인 두 건, 우리 로그는 첫 시도 타임아웃 + 두 번째 성공 | 멱등 키 없이 재시도 | 재시도가 같은 키를 썼나 | [06-4](../06-retry-backoff-jitter/2-summary.md) · [13-1](../13-idempotency/2-summary.md) |
| 서버 재시작 직후 PG 이중 청구, 우리 DB에는 한 건 | 외부 호출 뒤 완료 기록 전에 죽음 → 재선점한 재시도가 다시 호출 | 키 행의 `in_progress`·`locked_at` | [13-2](../13-idempotency/2-summary.md) |
| 금액을 고쳐 다시 결제했는데 이전 금액 응답 | 지문 검사 없이 키만으로 재생 | 응답 금액 vs 요청 금액 | [13-3](../13-idempotency/2-summary.md) |
| 오프라인에서 쌓인 요청을 하루 뒤 보냈더니 두 번째 주문 | 키 보관 기간 < 클라이언트 재시도 기간 | 키 행 생성 시각 vs 청소 주기 | [13-4](../13-idempotency/2-summary.md) |
| 결제·주문 생성이 가끔 두 번, 두 복제본에서 각각 성공 | 비멱등 요청에 hedge | hedge 대상 목록 | [34-3](../34-tail-latency-and-stragglers/2-summary.md) |
| 서로 다른 실행 환경에서 같은 "고유" ID·같은 난수열, 중복 키 오류. 복원 직후 첫 DB 호출이 끊긴 커넥션으로 실패 | 스냅숏 복원(SnapStart)이 초기화 때 만든 ID·시드·커넥션을 복제 | 그 값이 초기화 코드에서 만들어지나 | [42-3](../42-cold-start-and-scale-from-zero/2-summary.md) |
| 페일오버 뒤 일부 주문이 두 번 | 커밋 응답 전 연결 끊김 → "모름"을 재시도 | 재시도 전 키로 존재 확인했나 | [46-5](../46-disaster-recovery/2-summary.md) |
| 같은 `event_id` 처리 로그 두 줄, 소비자 재시작·리밸런스 시각 | at-least-once + 조회 기반 중복 검사 | `event_id` 유일 제약이 업무 변경과 같은 트랜잭션인가 | [04-2](../04-failure-modes-catalog/2-summary.md) · [27-2](../27-failure-point-checklist/2-summary.md) |
| 동시 요청에서 포인트·재고가 가끔 덜 쌓임, 에러 없음 | 읽고-고치고-절대값 저장(lost update) | 두 요청 로그가 같은 이전 값을 읽었나 | [04-1](../04-failure-modes-catalog/2-summary.md) |
| 하루 몇 건씩 적립 누락, 에러 없음, 재시작 시각에 몰림 | 처리 완료 전 오프셋 커밋 | 커밋 호출 위치 | [27-3](../27-failure-point-checklist/2-summary.md) |
| 브로커 한 대 장애 뒤 일부 메시지 소실 | `min.insync.replicas=1`(Kafka 4.1 기본) | 토픽 설정 조회 | [27-4](../27-failure-point-checklist/2-summary.md) |
| 특정 파티션 lag만 증가, 같은 오프셋에서 같은 예외 무한 반복 | poison pill + 순서 처리 | 반복 예외의 오프셋 | [04-3](../04-failure-modes-catalog/2-summary.md) |
| 에러율 0, 경보 없음. 몇 주 뒤 정산 대사에서 차이 | 잠재 오류·신호 없는 고장 | 원천 vs 결과 건수·합계 대사 | [01-4](../01-fault-error-failure-availability/2-summary.md) |
| 동기화 "완료"인데 일부 레코드가 대상에 없음, 응답은 200 | 항목별 결과(Elasticsearch `errors: true`, Redis 파이프라인 `-ERR`)를 안 읽음 | 응답 본문의 항목별 결과 | [40-4](../40-batching-and-round-trips/2-summary.md) |
| 같은 배치가 재시도마다 실패, `updateCounts` 전부 `-3` | 영구 실패 행 하나가 원자 배치 전체를 실패시킴 | 제약 위반 메시지의 행 | [40-5](../40-batching-and-round-trips/2-summary.md) |
| **앱은 타임아웃으로 끊었는데 DB 쿼리는 계속 돔** | 소켓 타임아웃은 소켓만 닫음 | `pg_stat_activity`에 끊긴 세션의 쿼리가 active인가 | [09-5](../09-cancellation-propagation/2-summary.md) · [database/22 장애 5](../../database/22-database-side-timeouts/2-summary.md) |
| "RPO 0" 약속인데 페일오버 뒤 성공 응답을 받은 주문이 사라짐 | 비동기 복제 — RPO = 페일오버 순간의 복제 지연 | 승격된 복제본의 마지막 행 시각 | [46-2](../46-disaster-recovery/2-summary.md) |
| 분할이 풀린 뒤 같은 키에 서로 다른 값 | 쿼럼·펜싱 없는 승격(split-brain) | 두 노드가 같은 시간대에 쓰기를 받았나 | [25-3](../25-high-availability-topology/2-summary.md) |
| 짧은 단절 뒤 쓰기가 먼 리전으로 넘어가 느려지고 되돌릴 수도 없음 | 페일오버 범위 제한 없음(GitHub 2018) | 쓰기 지연 = 리전 간 왕복인가 | [25-4](../25-high-availability-topology/2-summary.md) |
| 잘못된 배치가 지운 테이블이 DR 복제본에서도 지워짐 | 복제는 논리 사고를 그대로 옮김 | 복제본 상태 | [46-4](../46-disaster-recovery/2-summary.md) |
| 백업이 있는데 복원이 안 되거나 예상의 몇 배 걸림 | 복원해 본 적 없는 백업, 복제를 백업으로 착각 | 복원 리허설 기록 | [47-5](../47-server-design-antipatterns/2-summary.md) |
| 한 인스턴스만 틀린 값을 계속 냄, 재시작하니 멀쩡 | 예상 못 한 예외를 잡고 손상된 상태로 계속 실행 | 잡힌 예외 뒤 같은 인스턴스의 응답 | [49-3](../49-steady-state-fail-fast-and-supervision/2-summary.md) |
| 석 달 전 환불의 승인자를 못 찾음 | 감사 사건을 짧은 보존의 앱 로그에만 | 로그 보존 기간, 업무 행의 행위자 칸 | [18-1](../18-logs-traces-audit-roles/2-summary.md) |
| 로그 레벨을 올린 사이의 환불 기록이 없음 | 업무 사건을 운영 로그 정책 아래 둠 | 업무 이벤트의 로거·경로 | [18-2](../18-logs-traces-audit-roles/2-summary.md) |
| "이 사용자가 이 API를 불렀나"를 트레이스에서 못 찾음, DB엔 결과 | 트레이스는 샘플링·짧은 보존 | 샘플링 비율 | [18-3](../18-logs-traces-audit-roles/2-summary.md) |
| 삭제 요청 처리에 로그 저장소·백업까지 뒤짐, 로그에 토큰·이메일 | 요청 본문·헤더를 통째로 로깅 | 로그 줄의 민감 필드 | [18-4](../18-logs-traces-audit-roles/2-summary.md) · [15-5](../15-logging/2-summary.md) |
| 환불 행은 있는데 감사 기록 없음(또는 반대) | 업무 커밋과 감사 쓰기가 원자적이지 않음 | 두 저장소 건수 대사 | [18-5](../18-logs-traces-audit-roles/2-summary.md) |

### 8. 배치·스케줄 작업

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| **잡이 멈춘(hang) 뒤 같은 날짜가 두 번 반영**, 두 실행의 시간대가 겹침 | 겹침 허용 기본(K8s `concurrencyPolicy: Allow`) + 잡 타임아웃 없음 | 실행 이력의 시간 구간 겹침 | [32-1](../32-batch-and-job-time-bounds/2-summary.md) · [31-5](../31-batch-job-restart-and-checkpoint/2-summary.md) |
| 파드를 2개(3대)로 늘린 날부터 정산이 두 번(세 번) | 인메모리 스케줄러가 인스턴스마다 돎 | 같은 예정 시각의 실행 로그 호스트 수 | [30-1](../30-scheduler-and-cron-ha/2-summary.md) · [47-1](../47-server-design-antipatterns/2-summary.md) · [21-4](../21-scaling-principles/2-summary.md) |
| ShedLock을 붙였는데 짧은 작업이 가끔 두 번, 수십~수백 ms 간격 | 작업 끝나자마자 락 해제 + 시계 차이·방아쇠 지연 | `lockAtLeastFor` 값 | [30-2](../30-scheduler-and-cron-ha/2-summary.md) |
| 작업이 길어지자 다른 인스턴스가 같은 작업 시작, `locked_by`가 실행 중 바뀜 | lease(`lockAtMostFor`) < 실행 시간 | 실행 시간 추세 vs lease | [30-3](../30-scheduler-and-cron-ha/2-summary.md) |
| 3시간 스케줄러 공백 동안 집계 세 칸이 비었는데 아무도 모름 | 지나간 회차를 다시 돌리지 않음 | 실행 이력의 빈칸 | [30-4](../30-scheduler-and-cron-ha/2-summary.md) |
| 재실행 뒤 정산 금액이 원천보다 큼, 에러 없음 | 체크포인트 없음 + 비멱등 쓰기로 처음부터 재실행 | 같은 원천 ID 중복 대사 | [31-1](../31-batch-job-restart-and-checkpoint/2-summary.md) |
| 대시보드는 매일 초록(`COMPLETED`, 종료 코드 0)인데 일부 가맹점 미정산 | 스킵을 성공과 구분해 보고하지 않음, 합계만 대사 | 스텝 실행 테이블의 스킵 수, 행 수 대사 | [31-2](../31-batch-job-restart-and-checkpoint/2-summary.md) |
| DST 전환일에 `30 2 * * *` 잡이 없거나 `30 1 * * *` 잡이 두 번 | 지역 시간대 스케줄 — 그 시각이 그날 없거나 두 번 있음 | 그날 실행 이력 | [31-3](../31-batch-job-restart-and-checkpoint/2-summary.md) |
| 잡이 `DeadlineExceeded`로 실패, 어느 단계인지 모름 | 한도·관측이 잡 단위뿐 | 단계별 시작·끝 시각 | [32-2](../32-batch-and-job-time-bounds/2-summary.md) |
| 다음 단계 보고서 숫자가 작음, 에러 없음, 산출물 수정 시각 = kill 시각 | 최종 위치에 직접 씀 → 부분 산출물 | 산출물 행 수·완료 표식 | [32-3](../32-batch-and-job-time-bounds/2-summary.md) |
| 한도를 조금 넘기기 시작한 뒤 한 번도 성공 못 함, 매번 같은 진행률에서 타임아웃 | 체크포인트 없이 0부터 재시작 | 재시도마다 처음부터인가 | [32-4](../32-batch-and-job-time-bounds/2-summary.md) |
| 잡이 멈춘 날 아침까지 경보 없음 | 끝나야 검사하는 경보 | 경보 규칙이 완료 이벤트 기반인가 | [32-5](../32-batch-and-job-time-bounds/2-summary.md) |
| 겹침 방지를 넣었더니 잡이 며칠째 안 돎, 리스 소유자는 며칠 전 실행 | 별도 스레드 heartbeat가 생존만 증명 | 리스 소유 실행의 진척 로그 | [32-6](../32-batch-and-job-time-bounds/2-summary.md) |
| 마지막 단계 실패로 앞 단계 보상(롤백)이 자주 돎 | 실패를 입구에서 미리 보지 않음(Fail Fast 부재) | 보상 로그와 서킷 열림 시간대 | [49-2](../49-steady-state-fail-fast-and-supervision/2-summary.md) |

### 9. 확장·용량·가용성

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 앱을 늘렸더니 더 느려짐, DB 커넥션 급증·`too many connections` | 병목이 상태 자원(DB·락) | 증설 전후 DB 커넥션·락 대기 | [03-4](../03-failure-at-scale/2-summary.md) · [21-2](../21-scaling-principles/2-summary.md) · [41-3](../41-autoscaling/2-summary.md) · [47-4](../47-server-design-antipatterns/2-summary.md) |
| 8 → 16대로 늘렸더니 처리량 감소, 노드 간 RPC·무효화가 노드 수보다 빨리 늚 | USL 역행 — 경합·일관성 비용 | 노드 수별 처리량 곡선 | [21-1](../21-scaling-principles/2-summary.md) |
| 트래픽이 수 초에 4배, 오토스케일은 동작했지만 몇 분간 타임아웃 | 반응 시간(동기화 주기 + 파드 준비) > 급증 속도 | HPA 이벤트와 준비 안 된 파드 수 | [41-1](../41-autoscaling/2-summary.md) |
| 레플리카가 몇 분마다 오르내림 | 축소 안정화 창 없음·짧음, 올림·내림 기준이 가까움 | HPA `New size` 이벤트 간격 | [41-2](../41-autoscaling/2-summary.md) · [33-1](../33-hysteresis-and-flapping/2-summary.md) |
| 트래픽이 높은데 HPA가 더 안 늘림, Ready 0/1 파드가 오래 남음 | 준비 안 된 파드는 계산에서 0%로 쳐짐 | `kubectl describe hpa`의 지표 | [41-5](../41-autoscaling/2-summary.md) |
| LB가 한 인스턴스를 뺐다 넣었다 반복 | 실패 1번에 빼고 성공 1번에 넣음, 프로브 타임아웃이 꼬리 안 | 대상 상태 변경 간격 | [33-5](../33-hysteresis-and-flapping/2-summary.md) |
| 부하 테스트에서 3,000을 버텼는데 운영 1,500에서 p99 폭발 | 테스트 키가 캐시에 다 들어감 | 테스트와 운영의 캐시 적중률 | [22-1](../22-capacity-and-load-testing/2-summary.md) |
| 부하 테스트 p99는 2ms, 운영에서는 GC 때마다 수백 ms | closed 모델 + coordinated omission | 테스트 중 실제 도착률이 목표를 지켰나 | [19-2](../19-performance-measurement/2-summary.md) · [22-3](../22-capacity-and-load-testing/2-summary.md) |
| 서버 CPU 40%인데 RPS가 안 오름, 발생기 CPU 100%·`dropped_iterations` > 0 | 부하 발생기가 병목 | 발생기 자원, 서버 쪽 실제 도착률 | [22-4](../22-capacity-and-load-testing/2-summary.md) |
| GC 멈춤·짧은 단절 뒤 주 노드가 바뀌어 있고 옛 주는 멀쩡 | 페일오버 임계 < 멈춤 길이, 한 관찰자 시야 | 승격 시각의 GC 로그·링크 장애 | [25-1](../25-high-availability-topology/2-summary.md) |
| 페일오버는 됐는데 새 주가 부하를 못 버팀 | 대기 노드가 작거나 설정이 다름 | 대기 노드 사양·사용률 | [25-5](../25-high-availability-topology/2-summary.md) |
| 각 팀 목표 99.9%는 지켰는데 고객 SLA 위반 | 5개 직렬이면 0.999⁵ ≈ 99.5% | 게이트웨이에서 잰 종단 성공률 | [01-1](../01-fault-error-failure-availability/2-summary.md) |
| 1년 안정화 작업에도 가용성 숫자 그대로 | MTTR을 그대로 둠 | 사고당 탐지·복구 시간 | [01-5](../01-fault-error-failure-availability/2-summary.md) |
| DR 선언했는데 DR 리전 앱이 안 뜨거나 주 리전 DB를 가리킴 | 드리프트, 한 번도 실행하지 않은 경로 | DR 리전 설정·할당량·이미지 | [46-1](../46-disaster-recovery/2-summary.md) |
| Redis 주 서버가 바뀌었는데 앱은 계속 실패, 재시작해야 복구 | 끊긴 연결을 안 버림(재연결·타임아웃 없음), 엔드포인트 캐시 | 페일오버 주입 실험 | [45-1](../45-chaos-and-resilience-testing/2-summary.md) |
| 카오스 실험 중 전체 오류율 상승, 중단에 20분 | 중단 조건·범위 제한 없음 | 실험 정의의 자동 중단 조건 | [45-2](../45-chaos-and-resilience-testing/2-summary.md) |
| 카오스 실험은 늘 "통과"인데 실제 사고는 남 | 정상 상태 지표가 내부 속성(CPU·메모리) | 정상 상태 정의에 사용자 지표가 있나 | [45-3](../45-chaos-and-resilience-testing/2-summary.md) |
| 작년 게임 데이에서 통과한 페일오버가 올해 실패 | 그 사이 시스템이 바뀜 | 마지막 실험 날짜 vs 변경 이력 | [45-4](../45-chaos-and-resilience-testing/2-summary.md) |
| 셀을 하나 늘렸더니 테넌트 대부분이 이동해야 함 | `hash % N` 매핑 | 매핑 방식 | [51-5](../51-cells-stamps-and-blast-radius/2-summary.md) |

### 10. 관측·경보·대응 자체가 증상일 때

| 보이는 형태 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 밤마다 page, 대부분 행동 없이 닫힘. 진짜 장애 page를 30분 늦게 봄 | 원인 기반 경보 남발 | 행동 없이 닫힌 page 비율 | [43-1](../43-alerting-and-on-call/2-summary.md) · [02-3](../02-slo-sli-error-budget/2-summary.md) |
| 몇 분짜리 출렁임마다 page, 깨서 보면 이미 끝남 | 예산 소모와 무관한 짧은 창 고정 임계 | 경보식이 번 레이트인가 | [43-2](../43-alerting-and-on-call/2-summary.md) |
| 이틀간 0.5% 에러로 월 예산 3분의 1이 사라졌는데 page 없음, 또는 끝난 장애 경보가 한 시간 더 울림 | 한 창 번 레이트 | 여러 창 OR + 짧은 창 AND인가 | [43-3](../43-alerting-and-on-call/2-summary.md) |
| 같은 경보가 한 시간에 수십 번 FIRING·RESOLVED | `for` 없음, 임계가 평소 잡음 안 | 지표 분포와 임계 | [33-2](../33-hysteresis-and-flapping/2-summary.md) |
| 장애가 끝났는데 몇 시간째 firing, 다음 장애 알림이 안 옴 | `keep_firing_for`가 흔들림 주기보다 김 | 경보의 firing 지속 시간 | [33-3](../33-hysteresis-and-flapping/2-summary.md) |
| 감시 시스템이 멈춘 동안 장애, page 없음("조용한 밤") | 경보 시스템 자신을 감시하지 않음 | dead man's switch가 있나 | [43-5](../43-alerting-and-on-call/2-summary.md) |
| 경보는 제때 울렸는데 "이거 누가 알아요?"로 30분 | 런북·에스컬레이션 없음 | 경보의 `runbook_url` | [44-1](../44-runbooks-and-operational-readiness/2-summary.md) |
| 런북 명령이 실패하거나 엉뚱한 대상을 바꿈 | 런북이 구 인프라 기준 | 명령 주기 실행 점검 | [44-2](../44-runbooks-and-operational-readiness/2-summary.md) |
| 새 기능 장애를 고객 문의로 처음 앎 | 출시 기준에 관측 없음(PRR 부재) | 탐지 경로 | [44-3](../44-runbooks-and-operational-readiness/2-summary.md) |
| 교대 직후 같은 경보 재발, 임시 완화가 풀림 | 인수인계 누락 | 인수인계 기록 | [44-4](../44-runbooks-and-operational-readiness/2-summary.md) |
| 고객 문의 한 건 조사에 몇 시간, 비동기 단계 뒤 줄에 요청 ID 없음(또는 남의 ID) | MDC가 스레드에 붙어 넘어가지 않음 | "ID 없는 줄" 비율 | [15-2](../15-logging/2-summary.md) |
| 트레이스는 200ms에 끝났는데 실제 응답 2초, 부모 없는 루트 스팬 다수 | 비동기 경계에서 컨텍스트 끊김 | 부모 없는 INTERNAL 루트 스팬 비율 | [17-1](../17-distributed-tracing/2-summary.md) · [05-4](../05-timeouts-and-deadline-propagation/2-summary.md) |
| 장애 시각의 에러 트레이스가 대부분 없음 | head 샘플링 | 샘플링 방식 | [17-2](../17-distributed-tracing/2-summary.md) |
| 주문 1의 트레이스에 주문 2·3 처리 시간이 들어 있음 | 배치 처리 스팬의 부모를 첫 메시지로 | span link 사용 여부 | [17-3](../17-distributed-tracing/2-summary.md) |
| 게이트웨이 뒤부터 trace ID가 바뀜 | 프록시가 헤더를 지우거나 다른 형식(B3)만 전파 | 경계별 `traceparent` 확인 | [17-4](../17-distributed-tracing/2-summary.md) |
| 장애 조사 중 그 시각 INFO가 듬성듬성 빔 | 비동기 appender가 INFO 이하를 버림 | 직접 계측한 버린 수(Logback 1.5.18 자체는 세지 않음)·큐 남은 칸 | [15-4](../15-logging/2-summary.md) |
| 포스트모템이 "A가 잘못된 명령"으로 끝남, 이후 작은 사고 보고가 줆 | 개인 비난 → 은폐 | "처음 인지"와 "선언" 간격 | [26-2](../26-incident-response-and-postmortem/2-summary.md) |
| 완화 중 누군가 배포해 2차 사고 | 지휘 밖 변경(프리랜싱) | 사고 채널에 없는 변경 | [26-3](../26-incident-response-and-postmortem/2-summary.md) |
| 고객 문의가 며칠째 쌓이는데 버그 트래커에서만 다룸 | 사고 선언 기준 없음 | 선언 기준 | [26-4](../26-incident-response-and-postmortem/2-summary.md) |
| 같은 원인의 사고가 분기마다 | 추적 없는 조치 항목 | 조치 항목의 담당·버그 번호 | [26-5](../26-incident-response-and-postmortem/2-summary.md) |
| 회고까지 쓴 사고가 새 기능에서 똑같이 | 교훈이 점검 절차로 안 옮겨짐, "멱등하게 한다"는 문장만 | 설계 문서의 "막는 것" 칸이 장치·위치인가 | [27-1](../27-failure-point-checklist/2-summary.md) · [04-5](../04-failure-modes-catalog/2-summary.md) |
| 질문 200개 점검표를 "예"만 체크 | 근거 없는 질문 누적 | 질문마다 근거 사고가 있나 | [27-5](../27-failure-point-checklist/2-summary.md) |
| 배포 회의마다 "위험하다/괜찮다" 반복 | SLO·에러 버짓 정책 없음 | 결정 기록에 숫자가 있나 | [02-2](../02-slo-sli-error-budget/2-summary.md) |

### 11. 오독 사전 — 이렇게 읽으면 틀린다

| 잘못된 읽기 | 왜 틀리나 | 대신 볼 것 | leaf |
|---|---|---|---|
| "평균이 괜찮으니 괜찮다" | 평균은 드문 긴 지연을 희석한다. 빠른 실패는 평균을 오히려 낮춘다 | p99·max, 성공·실패를 나눈 지연 | [19-1](../19-performance-measurement/2-summary.md) · [16-2](../16-metrics-and-golden-signals/2-summary.md) |
| "인스턴스 p99를 평균 내면 전체 p99" | 분위수는 평균으로 합칠 수 없다 | 버킷 합친 뒤 `histogram_quantile` | [19-3](../19-performance-measurement/2-summary.md) |
| "재시도하면 낫는다" | 과부하 실패에서 재시도는 부하를 키워 회복을 막는다. 층마다 걸면 곱이 된다 | 재시도 비율, 재시도 예산, 한 층에서만 | [03-1](../03-failure-at-scale/2-summary.md) · [06-2](../06-retry-backoff-jitter/2-summary.md) · [06-3](../06-retry-backoff-jitter/2-summary.md) |
| "타임아웃 = 실패" | 상대는 처리했을 수 있다("모름") | 같은 키로 상태 조회, 대사 | [35-1](../35-timeout-design-worksheet/2-summary.md) · [09-4](../09-cancellation-propagation/2-summary.md) · [06-4](../06-retry-backoff-jitter/2-summary.md) |
| "헬스체크 실패 = 죽었다" | 과부하·스레드 고갈·깊은 의존성 확인으로도 실패한다. 빼면 남은 쪽이 더 무거워진다(SRE 22장) | 프로브 경로·지연, 프로브가 무엇을 확인하나 | [12-4](../12-backpressure-and-load-shedding/2-summary.md) · [47-2](../47-server-design-antipatterns/2-summary.md) · [48-3](../48-performance-and-stability-antipatterns-in-code/2-summary.md) |
| "CPU가 낮으니 여유 있다" | 기다리는 스레드는 CPU를 안 쓴다. 제약은 풀·락·디스크일 수 있다 | USE: 이용률·포화·에러를 자원마다 | [16-5](../16-metrics-and-golden-signals/2-summary.md) · [20-4](../20-performance-method-and-amdahl/2-summary.md) · [36-1](../36-profiling/2-summary.md) |
| "스레드 덤프가 RUNNABLE이니 일하는 중" | 소켓 읽기에서 막힌 JDK 21 스레드도 `RUNNABLE`이다(적용 3의 실행 확인: 12개 모두 `RUNNABLE  sun.nio.ch.SocketDispatcher.read0`) | 상태가 아니라 **맨 위 프레임** | [05-2](../05-timeouts-and-deadline-propagation/2-summary.md) · [28-1](../28-bulkhead/2-summary.md) |
| "종료 코드 137 = 메모리 부족" | 137은 SIGKILL(128+9)이다. 유예 시간 초과 강제 종료도 137이다 | `OOMKilled` 플래그, 종료 직전 로그 | [14-2](../14-graceful-shutdown/2-summary.md) · [37-2](../37-memory-leak-and-heap-analysis/2-summary.md) |
| "힙 그래프가 평평하니 메모리 문제가 아니다" | direct buffer·스레드 스택·metaspace·native는 힙 밖이다 | RSS 추이, NMT | [37-2](../37-memory-leak-and-heap-analysis/2-summary.md) |
| "에러율 0이면 정상" | 스킵·누락·이중 반영·LWW는 에러를 안 낸다 | 원천 vs 결과 대사(건수·합계·누락 키) | [01-4](../01-fault-error-failure-availability/2-summary.md) · [31-2](../31-batch-job-restart-and-checkpoint/2-summary.md) · [27-3](../27-failure-point-checklist/2-summary.md) |
| "`COMPLETED`(종료 코드 0)면 다 처리됨" | 스킵이 성공 뒤에 숨는다 | 스킵 수, 행 수 대사 | [31-2](../31-batch-job-restart-and-checkpoint/2-summary.md) |
| "heartbeat가 오니 잡이 진행 중" | 별도 스레드 heartbeat는 프로세스 생존만 증명한다 | 진척(처리 건수) 기반 리스 갱신 | [32-6](../32-batch-and-job-time-bounds/2-summary.md) |
| "서킷이 열렸으니 하류가 죽었다" | 4xx·리미터 거절을 실패로 세거나, 재시도 시도마다 창을 채워도 열린다 | 하류 자체 지표, 실패로 센 예외 목록 | [10-4](../10-circuit-breaker/2-summary.md) · [10-5](../10-circuit-breaker/2-summary.md) |
| "로그·트레이스에 없으니 일어나지 않았다" | 비동기 appender가 버렸거나, 샘플링에서 빠졌거나, 레벨에서 걸렀다 | 버린 수 지표, 샘플링 비율, 업무 사건은 감사 기록 | [15-4](../15-logging/2-summary.md) · [17-2](../17-distributed-tracing/2-summary.md) · [18-3](../18-logs-traces-audit-roles/2-summary.md) |
| "경보가 없으니 조용한 밤이다" | 경보 시스템이 죽어도 조용하다 | dead man's switch | [43-5](../43-alerting-and-on-call/2-summary.md) |
| "늘리면 빨라진다" | 병목이 DB·락이면 앞단 증설이 뒷단 경합을 키운다(USL 역행) | 증설 전 병목 자원, 총 커넥션 계산 | [21-1](../21-scaling-principles/2-summary.md) · [21-2](../21-scaling-principles/2-summary.md) · [41-3](../41-autoscaling/2-summary.md) |
| "롤백했는데도 에러니 배포와 무관하다" | 롤백은 코드만 되돌린다. 바뀐 스키마·새 형식 데이터·캐시는 남는다 | 배포가 쓴 데이터 | [23-2](../23-deployment-strategies/2-summary.md) |
| "부하 테스트를 통과했으니 운영도 버틴다" | 캐시에 다 들어가는 데이터, closed 모델, 발생기 병목이면 낙관적이다 | 적중률·실제 도착률·발생기 자원 | [22-1](../22-capacity-and-load-testing/2-summary.md) · [22-3](../22-capacity-and-load-testing/2-summary.md) · [22-4](../22-capacity-and-load-testing/2-summary.md) |
| "원인을 알아야 조치할 수 있다" | 배포와 시각이 겹치면 롤백(완화)이 먼저다. 증거는 먼저 떠 둔다 | 변경 이력과 시각 | [26-1](../26-incident-response-and-postmortem/2-summary.md) |

### 12. 원본 플레이북과의 대응

원본 [server-design/10](../../systems/server-design/10-playbook-by-symptom.md)의 A~H는 이 노트의 다음 칸으로 이어진다. 원본의 처방 목록은 그대로 읽어도 되고, 이 노트는 각 칸에 보이는 형태(문구·지표)와 leaf 번호를 더했다.

| 원본 | 이 노트 |
|---|---|
| A-1 평균은 괜찮은데 p99만 나쁘다 | §2 첫 표, §11 첫 줄 |
| A-2 서버를 늘렸는데 안 빨라진다 | §9 첫 두 줄 |
| A-3 DB CPU 100% · B-1 커넥션 풀 고갈 | §3-1 HikariCP·PostgreSQL 문구, [database/56](../../database/56-db-symptom-index/2-summary.md) |
| A-4 특정 시간대에만 느리다 · A-5 캐시를 넣었는데 더 느려졌다 | §4 스탬피드·눈사태·Dogpile 줄, §2 "배포·확장 직후" |
| B-2 메모리가 계속 증가 · B-3 스레드 풀 고갈 | §6 |
| C-1·C-2 부하 쏠림·핫스팟 | §2 마지막 줄 |
| D-1 외부 API 하나에 전체 마비 · D-2 복구했는데 다시 죽음 · D-3 스파이크 | §4 |
| D-4 DB failover 후 앱 미복구 | §9의 [45-1](../45-chaos-and-resilience-testing/2-summary.md) 줄 |
| D-5 배포 직후 에러 급증 | §5 |
| E-1~E-4 데이터 정합성 · F-1~F-3 비동기·큐 | §7·§8, [distributed/35](../../distributed/35-distributed-symptom-index/2-summary.md) |
| G 진단 순서 · H 즉시 적용 우선순위 | §0의 네 가지, 적용 1 |

- 참고: 원본 A-1의 "캐시는 p99를 개선하지 않는다"는 미스 비율이 1%를 넘을 때의 이야기다. 미스가 1% 미만이면 p99 위치의 요청도 적중 경로라서 p99가 줄어든다(분위수 정의에서 나오는 산술). 그래서 첫 진단은 "미스 비율이 1%를 넘나"다.
- 참고: 원본 A-5의 "히트율 80% 미만이면 키 설계나 대상 선정이 잘못된 것"은 출처가 없는 경험칙이다. 받아들일 적중률은 미스 경로 비용과 하류 용량으로 정한다([22-1](../22-capacity-and-load-testing/2-summary.md)·[03-5](../03-failure-at-scale/2-summary.md)가 하류 용량 쪽 사례).
- 참고: 원본 B-3의 처방 순서("타임아웃 → 서킷 브레이커 → 벌크헤드")와 D-1의 순서("타임아웃 → 벌크헤드 → 서킷 → 폴백")가 서로 다르다. 서킷은 결과가 기록돼야 판단하므로([10-3](../10-circuit-breaker/2-summary.md)) 판단이 늦는 동안의 스레드 고갈은 격벽이 막는다([28-1](../28-bulkhead/2-summary.md)). D-1의 순서로 읽는다.
- 참고: 원본 A-1의 헤지 처방(p95를 넘으면 다른 인스턴스에 중복 요청)은 읽기와 멱등 키가 있는 쓰기에만 쓴다. 비멱등 요청은 이중 처리가 된다([34-3](../34-tail-latency-and-stragglers/2-summary.md)). 부하가 높을 때는 오히려 지연을 키운다([34-2](../34-tail-latency-and-stragglers/2-summary.md)).
- 참고: 원본 G의 "가장 강력한 단서는 항상 '언제부터'"는 단정이 지나치다. SRE 책 1장의 수치는 "약 70%가 변경 때문"이다. 나머지 몫에는 부하 급증·용량 감소·잠복 버그 같은 변경 밖 원인이 들어간다. 해석: Slack 2021은 자기 시스템의 변경이 아니라 연휴 뒤 트래픽 급증이 방아쇠였다([53](../53-reliability-incidents/2-summary.md)).

## 쓰이는 자료구조·알고리즘

- **역색인(inverted index)**: 이 노트 자체다. 증상(키) → leaf 장애 번호 목록(값). 정방향(leaf → 증상)을 뒤집어 만든다. 한 증상에 leaf가 여럿이면 "보이는 형태"로 후보를 지운다.
- **결정 트리**: §1의 모양 분류. 질문 하나(즉시인가·설정값 근처인가·에러가 있나)로 가지를 반씩 잘라 후보 칸을 줄인다.
- **해시맵 집계(group-by count)**: 스레드 덤프를 "상태 + 맨 위 프레임"으로 묶어 센다(적용 3). 수백 개 스레드를 몇 줄로 줄여 "풀 크기만큼 같은 곳에 멈춤"을 보이게 한다.
- **히스토그램과 분위수**: 지연 증상의 거의 전부가 분포의 문제다. 고전 히스토그램은 버킷을 더해 합칠 수 있고, 분위수는 합칠 수 없다([16-3](../16-metrics-and-golden-signals/2-summary.md)·[19-3](../19-performance-measurement/2-summary.md)).
- **시계열 상관(시각 조인)**: 증상 시작 시각과 변경 이력(배포·설정·플래그·스케일 이벤트)을 시간으로 맞춘다. 범위가 겹치는 구간 찾기(interval overlap)다.
- **USE 행렬**: 자원 × (이용률·포화·에러) 표. 빈칸이 "안 본 자원"이다(Gregg의 USE 방법, [16-5](../16-metrics-and-golden-signals/2-summary.md)·[20-4](../20-performance-method-and-amdahl/2-summary.md)).
- **대사(reconciliation)**: 원천과 결과를 키로 조인해 누락·중복·불일치를 센다. 에러 없는 증상(§7)의 탐지기다.

## 적용 — 풀어나가는 법

### 1. 순서

```text
  ① 원문·모양·시각·범위 확보 (§0)
        |
  ② 변경과 겹치나? ──예──> 완화 먼저(롤백·플래그 끄기·트래픽 차단), 증거는 먼저 떠 둠 ([26-1](../26-incident-response-and-postmortem/2-summary.md))
        | 아니오/완화 후
  ③ 모양으로 칸 고르기 (§1) ──> §2~§10 표의 "보이는 형태"와 대조
        |
  ④ 첫 진단 한 가지 실행 ──> 후보가 둘 이상 남으면 다음 진단
        |
  ⑤ leaf 장애 절로 가서 대처·재발 방지
```

### 2. 첫 진단 세트

PromQL(지연·에러·포화 — 대상 이름은 예시)

```text
# p99 지연: 인스턴스별 rate 먼저, le로 합친 뒤 분위수
histogram_quantile(0.99, sum by (le) (rate(http_server_requests_seconds_bucket[5m])))

# 5xx 비율
sum(rate(http_server_requests_seconds_count{status=~"5.."}[5m]))
  / sum(rate(http_server_requests_seconds_count[5m]))

# 커넥션 풀 포화 (HikariCP Micrometer 지표)
max by (pool) (hikaricp_connections_pending)

# 재시도 비율 (Envoy)
sum(rate(envoy_cluster_upstream_rq_retry[5m])) / sum(rate(envoy_cluster_upstream_rq_total[5m]))
```

JVM·OS·쿠버네티스

```text
jcmd <pid> Thread.print                 # 멈춘 지점 — 적용 3처럼 맨 위 프레임으로 센다
jcmd <pid> GC.heap_info                 # 힙 바닥선
jcmd <pid> VM.native_memory summary     # 힙 밖 (-XX:NativeMemoryTracking=summary 필요)
ss -tan state time-wait | wc -l         # 임시 포트 고갈
ss -tan state syn-sent                  # connect 멈춤
curl -o /dev/null -s -w 'dns=%{time_namelookup} connect=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total}\n' https://example.com/
kubectl get events --sort-by=.lastTimestamp       # 프로브 실패·OOMKilled·TooManyMissedTimes
kubectl describe pod <pod>                         # Last State: Terminated, Reason, Exit Code
```

### 3. 실행 확인: 스레드 덤프를 맨 위 프레임으로 센다

스레드 고갈 증상(§4 첫 줄)의 첫 진단이다. 응답하지 않는 하류에 타임아웃 없이 매달린 스레드 12개, 락을 기다리는 스레드 3개를 만들고 `jcmd` 출력을 묶어 셌다.

```java
// Stuck.java (핵심) — 하류가 accept만 하고 아무것도 안 보낸다
ExecutorService pool = Executors.newFixedThreadPool(12, r -> new Thread(r, "http-nio-exec"));
for (int i = 0; i < 12; i++) pool.submit(() -> {
    try (Socket s = new Socket("127.0.0.1", mute.getLocalPort())) {   // 읽기 타임아웃 없음
        return s.getInputStream().read();
    }
});
// lock-holder가 LOCK을 쥐고 잠들고, lock-waiter 3개가 synchronized(LOCK)에서 기다린다
```

```sh
# triage.sh — "상태 + 맨 위 프레임"으로 묶어 센다
jcmd "$1" Thread.print | awk '
  /^"/ { name=$0; top=""; state=""; next }
  /java.lang.Thread.State:/ { state=$2; getline; sub(/^[ \t]+at /,""); top=$0;
                              if (name ~ /http-nio-exec|lock-/) cnt[state "  " top]++ }
  END { for (k in cnt) printf "%3d  %s\n", cnt[k], k }' | sort -rn
```

(실행 확인, eclipse-temurin:21-jdk 컨테이너 — OpenJDK 21.0.12, `--cpus=2`, 2026-10-01)

```text
 12  RUNNABLE  sun.nio.ch.SocketDispatcher.read0(java.base@21.0.12/Native Method)
  3  BLOCKED  Stuck.lambda$main$4(Stuck.java:19)
  1  TIMED_WAITING  java.lang.Thread.sleep0(java.base@21.0.12/Native Method)
```

- 풀 크기(12)만큼 같은 프레임에 멈춘 줄이 맨 위에 나온다. 이 모양이면 그 호출에 타임아웃이 없는지부터 본다([05-2](../05-timeouts-and-deadline-propagation/2-summary.md) · [07-2](../07-timeout-taxonomy-by-layer/2-summary.md)).
- 소켓 읽기에서 막힌 스레드의 상태는 `RUNNABLE`이다. 상태만 세면 "다 일하는 중"으로 오독한다(§11). 맨 위 프레임을 함께 묶어야 한다.
- `BLOCKED` 3개는 같은 줄(`Stuck.java:19`의 `synchronized`)에 모였다. 락 경합이면 이 모양이고, 쥔 쪽은 덤프의 `- locked <0x…>`로 찾는다.

### 4. 실행 확인: 문구 사전의 JDK 메시지

§3-1·§6의 JDK 문구 넷은 직접 내 보고 실었다(같은 환경).

```java
// Messages.java (핵심) — 인자별로 하나씩 일으킨다
case "heap"   -> { List<long[]> keep = new ArrayList<>(); while (true) keep.add(new long[1 << 20]); }  // -Xmx32m
case "direct" -> ByteBuffer.allocateDirect(4 << 20);                                                 // -XX:MaxDirectMemorySize=1m
case "reject" -> { /* 코어 1, 큐 1인 ThreadPoolExecutor에 작업 3개 */ }
case "http"   -> { /* 응답하지 않는 서버에 HttpRequest.timeout(300ms) */ }
```

```text
java.lang.OutOfMemoryError: Java heap space
java.lang.OutOfMemoryError: Cannot reserve 4194304 bytes of direct buffer memory (allocated: 8192, limit: 1048576)
java.util.concurrent.RejectedExecutionException: Task Messages$$Lambda/0x00007c8e3015c208@333291e3 rejected from java.util.concurrent.ThreadPoolExecutor@192d43ce[Running, pool size = 1, active threads = 1, queued tasks = 1, completed tasks = 0]
elapsed=352ms
java.net.http.HttpTimeoutException: request timed out
```

- 거절 메시지에 풀 상태(`pool size`, `active threads`, `queued tasks`)가 들어 있다. 로그에 이 줄이 있으면 유계 큐가 의도대로 거절한 것이다. 500이 아니라 503으로 매핑할 대상이다([12-1](../12-backpressure-and-load-shedding/2-summary.md)).
- `HttpTimeoutException`은 300ms 설정에 352ms에 났다(점검 재실행 3회는 319~322ms — 경과 시간은 실행마다 다르다). 람다 주소·해시값도 실행마다 다르다.

### 5. leaf로 간다

- 표의 `NN-k`는 그 노트의 「장애 시나리오와 대처」 k번이다. 대처·재현 실험·진단 명령은 그쪽이 정본이다.
- 원인이 이 영역 밖이면 다른 색인으로 간다.
  - SQLSTATE·풀·ORM: [database/56](../../database/56-db-symptom-index/2-summary.md)
  - 중복·유실·순서 역전·리더 둘: [distributed/35](../../distributed/35-distributed-symptom-index/2-summary.md)
  - errno·종료 코드·D 상태: [os/37](../../os/37-os-symptom-index/2-summary.md)
  - `ECONNRESET`·`ETIMEDOUT`·DNS·TLS: [network/52](../../network/52-network-symptom-index/2-summary.md)
- 여러 칸에 걸친 실제 사건은 [53-reliability-incidents](../53-reliability-incidents/2-summary.md)에서 사건 단위로 본다.

## 장애 시나리오와 대처

이 노트의 장애는 **색인을 잘못 쓰는 것**이다. 증상을 엉뚱한 칸에 넣거나, 첫 진단을 건너뛰고 대처로 간다.

### 1. 504를 "실패"로 닫는다

- **현상**: 결제 API 504 급증 뒤 "실패 건이니 고객에게 재시도 안내"로 닫았다. 이튿날 이중 청구 문의가 쌓인다.
- **보이는 형태**: Envoy 504 본문 `upstream request timeout`. 같은 주문의 PG 승인 기록.
- **원인**: §11의 "타임아웃 = 실패" 오독. 게이트웨이 timeout이 서비스 안 최악 시간보다 짧았다([35-1](../35-timeout-design-worksheet/2-summary.md)).
- **대처**: 504 건을 "모름"으로 두고 같은 멱등 키로 상태를 조회해 확정한다. 이미 난 중복은 대사로 찾아 환불한다. 게이트웨이 timeout과 서비스 예산을 정렬한다([08-1](../08-time-budget-allocation/2-summary.md)).

### 2. 스레드 고갈을 "스레드 수 늘리기"로 덮는다

- **현상**: 요청이 쌓여 톰캣 `max-threads`를 2배로 올렸다. 잠시 나아졌다가 하류가 더 느려진 날 다시 전면 장애.
- **보이는 형태**: 스레드 덤프 대부분이 한 하류의 소켓 읽기(적용 3의 모양). 스레드를 늘린 뒤에는 하류 커넥션 풀 대기가 늘었다.
- **원인**: 증상(줄)을 늘려 덮었다. 하류 호출에 타임아웃이 없고 격벽이 없다. 늘린 스레드는 같은 곳에서 기다린다([20-3](../20-performance-method-and-amdahl/2-summary.md) · [21-3](../21-scaling-principles/2-summary.md)).
- **대처**: 맨 위 프레임으로 센 결과를 근거로 그 호출에 타임아웃 → 하류별 격벽(대기 0) → 서킷 → 폴백 순으로 넣는다([05-2](../05-timeouts-and-deadline-propagation/2-summary.md) · [28-1](../28-bulkhead/2-summary.md)).

### 3. "exit 137"을 메모리 부족으로 읽고 힙만 늘린다

- **현상**: 파드가 137로 재시작한다. `-Xmx`를 올렸더니 오히려 더 자주 죽는다.
- **보이는 형태**: 힙 그래프는 평평, RSS는 우상향, `OOMKilled=true`. 다른 경우에는 `OOMKilled=false`인 137이 배포 때마다 유예 시간에 맞춰 난다.
- **원인**: 137은 SIGKILL일 뿐이다. 앞의 경우는 힙 밖 메모리 누수인데 힙을 늘려 컨테이너 한도 안의 남은 자리를 줄였다([37-2](../37-memory-leak-and-heap-analysis/2-summary.md)). 뒤의 경우는 SIGTERM을 못 받은 종료다([14-2](../14-graceful-shutdown/2-summary.md)).
- **대처**: `OOMKilled`부터 본다. 참이면 RSS vs 힙, NMT diff. 거짓이면 종료 직전 로그와 `/proc/1/cmdline`.

### 4. 재시도 폭풍을 "부하가 많다"로 읽고 증설만 한다

- **현상**: 하류 원인이 고쳐진 뒤에도 부하가 안 내려가 앱과 하류를 증설했다. 하류 DB의 커넥션이 먼저 바닥났다.
- **보이는 형태**: 도착률이 신규 요청의 몇 배, 재시도 비율 50% 초과, 같은 상관 ID 쿼리 수십 번.
- **원인**: 증폭된 부하(지속 효과)를 진짜 수요로 읽었다([03-1](../03-failure-at-scale/2-summary.md) · [06-3](../06-retry-backoff-jitter/2-summary.md)). 증설은 병목을 DB로 옮겼다([41-3](../41-autoscaling/2-summary.md)).
- **대처**: 재시도를 끄거나 예산으로 묶고, 부하를 용량 훨씬 아래로 일시 차단한 뒤 점진 복귀한다(SRE 22장, [12-2](../12-backpressure-and-load-shedding/2-summary.md)). 근본은 한 층 재시도 + 지터 + 예산.

### 5. 에러가 없어 "정상"으로 닫는다

- **현상**: 정산 문의에 "잡은 매일 `COMPLETED`, 에러 0"이라고 답했다. 다음 달 대사에서 미지급 가맹점이 나왔다.
- **보이는 형태**: 종료 코드 0, 스킵 수는 스텝 실행 테이블에만. 금액 합계 대사는 통과(NULL이 합에서 빠짐).
- **원인**: §11의 "에러율 0이면 정상" 오독. 조용한 실패는 로그가 아니라 대사로 찾는다([31-2](../31-batch-job-restart-and-checkpoint/2-summary.md) · [01-4](../01-fault-error-failure-availability/2-summary.md)).
- **대처**: 행 수·누락 키 대사를 먼저 돌린다. 스킵을 0이 아닌 종료 코드와 경보로 만든다.

## 핵심 문장

- 신뢰성 증상은 모양(즉시 실패·설정값 근처 실패·느린 성공·에러 없이 틀림·주기적·변경 직후)으로 먼저 가르면 후보 칸이 크게 준다.
- 같은 사건이 층마다 다른 이름으로 보인다. 원문(예외 체인·응답 본문·제품과 판), 모양, 시각, 범위를 먼저 모은다.
- 실패까지 걸린 시간을 각 층의 타임아웃 값과 맞춰 보면 범인 층이 드러나는 경우가 많다.
- 스레드 덤프는 상태가 아니라 맨 위 프레임으로 센다. 소켓에 막힌 스레드도 `RUNNABLE`이다.
- 타임아웃은 실패가 아니라 "모름"이고, 137은 메모리 부족이 아니라 SIGKILL이며, `COMPLETED`는 전부 처리가 아니다.
- 변경과 시각이 겹치면 원인 규명보다 완화가 먼저다. 증거는 완화 전에 떠 둔다.

## 관련 주제·근거

- 선행(이 영역 전체 — 색인의 원천)
  - 개념: [01](../01-fault-error-failure-availability/2-summary.md) · [02](../02-slo-sli-error-budget/2-summary.md) · [03](../03-failure-at-scale/2-summary.md) · [04](../04-failure-modes-catalog/2-summary.md) · [27](../27-failure-point-checklist/2-summary.md)
  - 복원력: [05](../05-timeouts-and-deadline-propagation/2-summary.md) · [06](../06-retry-backoff-jitter/2-summary.md) · [10](../10-circuit-breaker/2-summary.md) · [11](../11-rate-limiter/2-summary.md) · [12](../12-backpressure-and-load-shedding/2-summary.md) · [13](../13-idempotency/2-summary.md) · [14](../14-graceful-shutdown/2-summary.md) · [28](../28-bulkhead/2-summary.md) · [29](../29-cache-stampede/2-summary.md) · [30](../30-scheduler-and-cron-ha/2-summary.md) · [33](../33-hysteresis-and-flapping/2-summary.md) · [34](../34-tail-latency-and-stragglers/2-summary.md) · [48](../48-performance-and-stability-antipatterns-in-code/2-summary.md) · [49](../49-steady-state-fail-fast-and-supervision/2-summary.md) · [50](../50-sidecar-ambassador-and-service-mesh/2-summary.md)
  - 시간 예산: [07](../07-timeout-taxonomy-by-layer/2-summary.md) · [08](../08-time-budget-allocation/2-summary.md) · [09](../09-cancellation-propagation/2-summary.md) · [32](../32-batch-and-job-time-bounds/2-summary.md) · [35](../35-timeout-design-worksheet/2-summary.md)
  - 성능·용량: [19](../19-performance-measurement/2-summary.md) · [20](../20-performance-method-and-amdahl/2-summary.md) · [21](../21-scaling-principles/2-summary.md) · [22](../22-capacity-and-load-testing/2-summary.md) · [36](../36-profiling/2-summary.md) · [37](../37-memory-leak-and-heap-analysis/2-summary.md) · [38](../38-microbenchmarking/2-summary.md) · [39](../39-async-io-gains-and-limits/2-summary.md) · [40](../40-batching-and-round-trips/2-summary.md) · [41](../41-autoscaling/2-summary.md) · [42](../42-cold-start-and-scale-from-zero/2-summary.md)
  - 관측성: [15](../15-logging/2-summary.md) · [16](../16-metrics-and-golden-signals/2-summary.md) · [17](../17-distributed-tracing/2-summary.md) · [18](../18-logs-traces-audit-roles/2-summary.md) · [43](../43-alerting-and-on-call/2-summary.md)
  - 배포·사고: [23](../23-deployment-strategies/2-summary.md) · [24](../24-feature-flag-lifecycle/2-summary.md) · [25](../25-high-availability-topology/2-summary.md) · [26](../26-incident-response-and-postmortem/2-summary.md) · [31](../31-batch-job-restart-and-checkpoint/2-summary.md) · [44](../44-runbooks-and-operational-readiness/2-summary.md) · [45](../45-chaos-and-resilience-testing/2-summary.md) · [46](../46-disaster-recovery/2-summary.md) · [47](../47-server-design-antipatterns/2-summary.md) · [51](../51-cells-stamps-and-blast-radius/2-summary.md)
- 후속: [53-reliability-incidents](../53-reliability-incidents/2-summary.md) — 여러 칸에 걸친 실사건(AWS S3 2017, Slack 2021, Roblox 2021, CrowdStrike 2024)
- 이어받은 원본: [systems/server-design/10-playbook-by-symptom.md](../../systems/server-design/10-playbook-by-symptom.md)(§12에서 대응·참고)
- 다른 영역 색인: [database/56](../../database/56-db-symptom-index/2-summary.md) · [distributed/35](../../distributed/35-distributed-symptom-index/2-summary.md) · [os/37](../../os/37-os-symptom-index/2-summary.md) · [network/52](../../network/52-network-symptom-index/2-summary.md)
- 커리큘럼이 이 노트에 이은 다른 영역 leaf: [database/22-database-side-timeouts](../../database/22-database-side-timeouts/2-summary.md) · [database/21-connection-pooling](../../database/21-connection-pooling/2-summary.md) · [distributed/03-partial-failure-and-timeouts](../../distributed/03-partial-failure-and-timeouts/2-summary.md) · [language/23-jit-tiered-compilation-and-warmup](../../language/23-jit-tiered-compilation-and-warmup/2-summary.md) · [domain-modeling/25-reconciliation](../../domain-modeling/25-reconciliation/2-summary.md)
- 후속(AI 엔지니어링): [ai-engineering/25-ai-symptom-index](../../ai-engineering/25-ai-symptom-index/2-summary.md) — LLM 호출 증상 색인
- 메시지 원문 출처(이 노트가 직접 대조한 것 — 각 leaf가 실험으로 확인한 문구는 그 leaf가 출처)
  - Envoy v1.35.0 `source/common/router/router.cc`(`upstream request timeout`, `upstream connect error or disconnect/reset before headers. `) <https://github.com/envoyproxy/envoy/blob/v1.35.0/source/common/router/router.cc>
  - Resilience4j v2.4.0 `CallNotPermittedException.java`(`CircuitBreaker '%s' is %s and does not permit further calls`), `BulkheadFullException.java`(`Bulkhead '%s' is full and does not permit further calls`), `RequestNotPermitted.java`(`RateLimiter '%s' does not permit further calls`) <https://github.com/resilience4j/resilience4j/tree/v2.4.0>
  - HikariCP 6.3.0 `HikariPool.java`(`SQLTransientConnectionException`, `- Connection is not available, request timed out after …ms (total=…, active=…, idle=…, waiting=…)`) <https://github.com/brettwooldridge/HikariCP/blob/HikariCP-6.3.0/src/main/java/com/zaxxer/hikari/pool/HikariPool.java>
  - PostgreSQL REL_17_STABLE `src/backend/storage/lmgr/proc.c`(`sorry, too many clients already`)
  - MySQL Connector/J release/9.x `LocalizedErrorMessages.properties`(`PacketTooBigException.0`)
  - OpenJDK jdk21u `java/nio/Bits.java`(`Cannot reserve … bytes of direct buffer memory`), `hotspot/share/memory/universe.cpp`(`Java heap space`, `Metaspace`, `GC overhead limit exceeded`), `java/util/concurrent/ThreadPoolExecutor.java`(`rejected from`), `jdk/internal/net/http/ResponseTimerEvent.java`(`request timed out`, `HTTP connect timed out`) <https://github.com/openjdk/jdk21u>
  - Kubernetes v1.34.0 `pkg/controller/cronjob/utils.go`(`TooManyMissedTimes`, `too many missed start times. …`), `pkg/kubelet/prober/prober.go`(`%s probe failed: %s`), `pkg/kubelet/kuberuntime/kuberuntime_manager.go`(`CrashLoopBackOff`) <https://github.com/kubernetes/kubernetes/tree/v1.34.0>
- 교재
  - Google SRE 책 1장 Introduction("roughly 70% of outages are due to changes in a live system"), 22장 Addressing Cascading Failures(스레드 고갈·자원 고갈이 헬스체크 실패로 이어짐) <https://sre.google/sre-book/table-of-contents/>
  - Brendan Gregg, USE Method <https://www.brendangregg.com/usemethod.html>
- 실행 확인(실험 의무는 면제된 종합 편 — 적용 절의 명령·코드가 실제로 도는지, 실은 문구가 맞는지 확인한 것)
  - eclipse-temurin:21-jdk(OpenJDK 21.0.12), `--cpus=2`, 일회용 컨테이너 `sn-rl-w52-*`: 적용 3 `Stuck.java` + `triage.sh`, 적용 4 `Messages.java`
