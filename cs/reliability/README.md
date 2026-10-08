# 운영·신뢰성 — `cs/reliability/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §11에서 `scripts/notes/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 53 · 검수 완료 0

> "여러 대가 돌 때 어떻게 버티고, 어떻게 보고, 어떻게 바꾸나". 기존 ops-patterns(복원력 패턴)·server-design(컬렉션)·failure 노트가 주력이다. 신규는 **성능 측정·관측성·사고 대응**.
> 뼈대: Google 『Site Reliability Engineering』(이하 SRE — 장 번호 3·4·6·21·22 외 `[?]`), Nygard 『Release It!』 [?], Gregg 『Systems Performance』 [?], Dean–Barroso 2013.

## 11.1 신뢰성 개념

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `fault-error-failure-availability` | fault/error/failure 구분, 가용성(9의 개수), MTBF/MTTR, 직렬·병렬 합성 | 필수 | 초안(Claude) | [01-fault-error-failure-availability](01-fault-error-failure-availability/) · [../systems/server-design/05-ha-topology.md](../systems/server-design/05-ha-topology.md) |
| 02 | `slo-sli-error-budget` | SLI 선택·SLO·에러 버짓·번 레이트 | 필수 | 초안(Claude) | [02-slo-sli-error-budget](02-slo-sli-error-budget/) · [../systems/server-design/09-capacity-slo.md](../systems/server-design/09-capacity-slo.md) |
| 03 | `failure-at-scale` | 부분 실패 상시화·재시도 증폭·균등 가정 붕괴·상태의 확장 불가 | 필수 | 초안(Claude) | [03-failure-at-scale](03-failure-at-scale/) · [../ops-patterns/failure-at-scale](../ops-patterns/failure-at-scale/) |
| 04 | `failure-modes-catalog` | 실패 카탈로그 F-01~25(동시성·DB / 분산·비동기 / 결제) | 필수 | 초안(Claude) | [04-failure-modes-catalog](04-failure-modes-catalog/) · [../ops-patterns/failure-modes](../ops-patterns/failure-modes/) |
| 27 | `failure-point-checklist` | 설계 시 실패 지점 점검 절차 | 권장 | 초안(Claude) | [27-failure-point-checklist](27-failure-point-checklist/) · [../engineering/failure-point-checklist](../engineering/failure-point-checklist/) |

## 11.2 복원력 패턴

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 05 | `timeouts-and-deadline-propagation` | 타임아웃 계층 정렬·데드라인 전파. gRPC는 절대 시각 대신 경과 시간을 뺀 타임아웃으로 전파(시계 어긋남 회피)하고, 서버는 취소를 주기적으로 확인할 책임이 있다(심화는 08·09) | 필수 | 초안(Claude) | [05-timeouts-and-deadline-propagation](05-timeouts-and-deadline-propagation/) · [../ops-patterns/deadline-propagation](../ops-patterns/deadline-propagation/) · [../systems/server-design/06-resilience.md](../systems/server-design/06-resilience.md) |
| 06 | `retry-backoff-jitter` | 지수 백오프·지터·재시도 예산 — 구체형: Finagle 기본(요청의 20% + 초당 최소 10회, 토큰 10초 만료), gRPC `retryThrottling`(maxTokens·tokenRatio — 토큰이 절반 미만이면 재시도·헤지 중단) | 필수 | 초안(Claude) | [06-retry-backoff-jitter](06-retry-backoff-jitter/) · [../ops-patterns/01-retry-backoff](../ops-patterns/01-retry-backoff/) |
| 10 | `circuit-breaker` | 닫힘·열림·반열림 | 필수 | 초안(Claude) | [10-circuit-breaker](10-circuit-breaker/) · [../ops-patterns/02-circuit-breaker](../ops-patterns/02-circuit-breaker/) |
| 11 | `rate-limiter` | 토큰 버킷·리키 버킷·고정/슬라이딩 윈도·분산 제한 | 필수 | 초안(Claude) | [11-rate-limiter](11-rate-limiter/) · [../ops-patterns/04-rate-limiter](../ops-patterns/04-rate-limiter/) |
| 12 | `backpressure-and-load-shedding` | 역압·큐 한도·우선순위 셰딩 | 필수 | 초안(Claude) | [12-backpressure-and-load-shedding](12-backpressure-and-load-shedding/) · [../ops-patterns/05-backpressure](../ops-patterns/05-backpressure/) · [../systems/server-design/06-resilience.md](../systems/server-design/06-resilience.md) |
| 13 | `idempotency` | 멱등 키 저장소·중복 억제·결과 재생 | 필수 | 초안(Claude) | [13-idempotency](13-idempotency/) · [../ops-patterns/06-idempotency-store](../ops-patterns/06-idempotency-store/) |
| 14 | `graceful-shutdown` | SIGTERM → 준비 해제 → 드레이닝 → 종료 | 필수 | 초안(Claude) | [14-graceful-shutdown](14-graceful-shutdown/) · [../ops-patterns/19-graceful-shutdown](../ops-patterns/19-graceful-shutdown/) · [../systems/server-design/02-request-path.md](../systems/server-design/02-request-path.md) |
| 28 | `bulkhead` | 자원 격벽(스레드풀·커넥션 분리) | 권장 | 초안(Claude) | [28-bulkhead](28-bulkhead/) · [../ops-patterns/03-bulkhead](../ops-patterns/03-bulkhead/) |
| 29 | `cache-stampede` | 스탬피드·관통·눈사태 방어 | 권장 | 초안(Claude) | [29-cache-stampede](29-cache-stampede/) · [../ops-patterns/09-stampede](../ops-patterns/09-stampede/) |
| 30 | `scheduler-and-cron-ha` | 스케줄러 이중화·중복 실행 방지·미실행 보정 | 권장 | 초안(Claude) | [30-scheduler-and-cron-ha](30-scheduler-and-cron-ha/) · [../ops-patterns/10-scheduler](../ops-patterns/10-scheduler/) |
| 33 | `hysteresis-and-flapping` | 방향별 임계값 분리로 진동 방지 | 권장 | 초안(Claude) | [33-hysteresis-and-flapping](33-hysteresis-and-flapping/) · [../systems/Hysteresis](../systems/Hysteresis/) |
| 34 | `tail-latency-and-stragglers` | 팬아웃에서 꼬리 지연 증폭, hedged request | 권장 | 초안(Claude) | [34-tail-latency-and-stragglers](34-tail-latency-and-stragglers/) · [../systems/straggler](../systems/straggler/) |
| 48 | `performance-and-stability-antipatterns-in-code` | 코드 수준 안티패턴 — Chatty I/O·Extraneous Fetching·Improper Instantiation(요청마다 HTTP 클라이언트·커넥션 생성)·Synchronous I/O·Busy Database·Busy Front End·Monolithic Persistence, Nygard의 Integration Points·Blocked Threads·Unbounded Result Sets·Self-Denial·Dogpile | 필수 | 초안(Claude) | [48-performance-and-stability-antipatterns-in-code](48-performance-and-stability-antipatterns-in-code/) |
| 49 | `steady-state-fail-fast-and-supervision` | Steady State(무한 증가 자원 정리 — 로그·세션·캐시·테이블), Fail Fast(입구 검증), Let It Crash + 감독 트리, Handshaking, Governor(자동화 속도 제한), Test Harness | 권장 | 초안(Claude) | [49-steady-state-fail-fast-and-supervision](49-steady-state-fail-fast-and-supervision/) |
| 50 | `sidecar-ambassador-and-service-mesh` | Sidecar·Ambassador, 서비스 메시(데이터·컨트롤 플레인, mTLS·재시도·관측 위임), Microservice Chassis(라이브러리) vs 메시, 서비스 디스커버리(클라이언트·서버 측, 레지스트리, 자기·제3자 등록) | 권장 | 초안(Claude) | [50-sidecar-ambassador-and-service-mesh](50-sidecar-ambassador-and-service-mesh/) |

## 11.2b 시간 예산 설계 (2026-09-28 추가)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 07 | `timeout-taxonomy-by-layer` | 호출 하나에 달린 타임아웃 목록과 포함 관계: 풀 획득 → DNS → connect → TLS 핸드셰이크 → 요청 쓰기 → 첫 바이트(응답 헤더) → 읽기 idle → 전체(call) → 커넥션 idle·수명. 라이브러리마다 다른 기본값과 "무엇이 포함되나" | 필수 | 초안(Claude) | [07-timeout-taxonomy-by-layer](07-timeout-taxonomy-by-layer/) |
| 08 | `time-budget-allocation` | **총 예산을 단계에 나누는 설계 패턴.** SLO에서 총 예산 역산, 단계별 타임아웃 = 하류 p99.x 기반(오탐률 선택), per-try 타임아웃 vs 전체, 재시도·폴백·응답 직렬화 몫 예약, 남은 예산이 최소치 미만이면 시작하지 않기 | 필수 | 초안(Claude) | [08-time-budget-allocation](08-time-budget-allocation/) |
| 09 | `cancellation-propagation` | 타임아웃이 나면 **작업을 실제로 멈추는** 방법: Go `context`, Java 인터럽트·`Future.cancel`·구조적 동시성(StructuredTaskScope), gRPC 취소, DB 쿼리 취소, 취소 불가 구간(외부 결제 호출)의 처리 | 필수 | 초안(Claude) | [09-cancellation-propagation](09-cancellation-propagation/) |
| 32 | `batch-and-job-time-bounds` | 배치·스케줄 작업의 시간 한도: 잡 전체·단계·태스크 타임아웃, heartbeat·lease, 마감 알림(끝나지 않아도 발화), 체크포인트와 재개(설계 본문은 31), 강제 종료 후 부분 산출물 정리 | 권장 | 초안(Claude) | [32-batch-and-job-time-bounds](32-batch-and-job-time-bounds/) |
| 35 | `timeout-design-worksheet` | 종합 연습: 요청 경로 하나(게이트웨이 → 서비스 A → B·DB·외부 PG)에 **단계별 시간 예산표**를 쓰고 Envoy(route `timeout`·`per_try_timeout`·`idle_timeout`, cluster `connect_timeout`)와 Resilience4j(TimeLimiter·Retry·CircuitBreaker 순서) 설정으로 옮긴다. 결과가 모호한 단계는 멱등 키와 대사 경로를 붙인다 | 권장 | 초안(Claude) | [35-timeout-design-worksheet](35-timeout-design-worksheet/) |

## 11.3 성능·용량

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 19 | `performance-measurement` | 지연 분포·백분위·벤치마크 방법론·coordinated omission, open vs closed 부하 모델(도착률 고정 vs 사용자 수 고정) | 필수 | 초안(Claude) | [19-performance-measurement](19-performance-measurement/) |
| 20 | `performance-method-and-amdahl` | 측정 → 병목 특정 → 한 가지만 바꾸기 → 재측정. Amdahl의 법칙, 병목 이동, 안티 방법론(가로등 효과·무작위 튜닝) | 필수 | 초안(Claude) | [20-performance-method-and-amdahl](20-performance-method-and-amdahl/) |
| 21 | `scaling-principles` | 병목 이동·Little's Law·USL·무상태화 | 필수 | 초안(Claude) | [21-scaling-principles](21-scaling-principles/) · [../systems/server-design/01-scaling-principles.md](../systems/server-design/01-scaling-principles.md) |
| 22 | `capacity-and-load-testing` | 사이징·부하 테스트 설계·헤드룸, open vs closed 부하 모델 선택 | 필수 | 초안(Claude) | [22-capacity-and-load-testing](22-capacity-and-load-testing/) · [../systems/server-design/09-capacity-slo.md](../systems/server-design/09-capacity-slo.md) |
| 36 | `profiling` | CPU·메모리·락·off-CPU 프로파일링, 플레임 그래프, 실습: async-profiler(AsyncGetCallTrace + perf_events) — 힙 분석 심화는 37 | 권장 | 초안(Claude) | [36-profiling](36-profiling/) |
| 37 | `memory-leak-and-heap-analysis` | 힙 덤프·히스토그램, 지배자 트리와 retained size, 누수 패턴(static 컬렉션·리스너·ThreadLocal·무제한 캐시), 힙 밖 누수(direct buffer·native·NMT), RSS vs 힙 | 필수 | 초안(Claude) | [37-memory-leak-and-heap-analysis](37-memory-leak-and-heap-analysis/) |
| 38 | `microbenchmarking` | JMH, 워밍업·반복·포크, 데드 코드 제거·상수 접기 함정, Blackhole, 결과 비교의 통계 | 권장 | 초안(Claude) | [38-microbenchmarking](38-microbenchmarking/) |
| 39 | `async-io-gains-and-limits` | 비동기·논블로킹·가상 스레드가 늘려 주는 것은 **동시성**(처리량)이지 지연이 아니다. CPU 바운드에서는 이득 없음, 블로킹 경로가 섞였을 때, 병목이 하류 풀로 이동 | 권장 | 초안(Claude) | [39-async-io-gains-and-limits](39-async-io-gains-and-limits/) |
| 40 | `batching-and-round-trips` | 왕복(RTT) 줄이기: 요청 배칭, 파이프라이닝, bulk insert·`COPY`, DataLoader식 모으기. 배치 크기 ↔ 지연 트레이드오프, 배치의 부분 실패 | 권장 | 초안(Claude) | [40-batching-and-round-trips](40-batching-and-round-trips/) |
| 41 | `autoscaling` | 지표 기반 확장·반응 지연·쿨다운 | 권장 | 초안(Claude) | [41-autoscaling](41-autoscaling/) |
| 42 | `cold-start-and-scale-from-zero` | 서버리스 Init 단계, 컨테이너 이미지 pull, 런타임 시작 + JIT 워밍업, readiness 설계, provisioned concurrency·스냅숏 복원(SnapStart) | 권장 | 초안(Claude) | [42-cold-start-and-scale-from-zero](42-cold-start-and-scale-from-zero/) |

## 11.4 관측성

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 15 | `logging` | 구조화 로그·상관 ID·레벨·샘플링 | 필수 | 초안(Claude) | [15-logging](15-logging/) |
| 16 | `metrics-and-golden-signals` | 4 골든 시그널·RED·USE, 카운터/게이지/히스토그램 | 필수 | 초안(Claude) | [16-metrics-and-golden-signals](16-metrics-and-golden-signals/) · [../systems/server-design/08-deployment-ops.md](../systems/server-design/08-deployment-ops.md) |
| 17 | `distributed-tracing` | 트레이스·스팬·컨텍스트 전파·샘플링, **baggage**(업무 문맥 전파 — W3C Baggage, 64항목·8192바이트까지 전파 의무), **span link**(큐·배치에서 여러 부모 연결) | 필수 | 초안(Claude) | [17-distributed-tracing](17-distributed-tracing/) |
| 18 | `logs-traces-audit-roles` | 네 가지 기록의 역할 구분. 운영 로그(버려도 됨·샘플링 가능), 지표, 추적(인과·지연 — 샘플링됨), **감사 기록·업무 기록**(버리면 안 됨·보존 기한·변조 방지). "이 사건은 어디에 남겨야 하나" 판정 기준 | 필수 | 초안(Claude) | [18-logs-traces-audit-roles](18-logs-traces-audit-roles/) |
| 43 | `alerting-and-on-call` | 증상 기반 알람·번 레이트 알람·온콜 | 권장 | 초안(Claude) | [43-alerting-and-on-call](43-alerting-and-on-call/) |

## 11.5 배포·변경·사고 대응

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 23 | `deployment-strategies` | 롤링·블루그린·카나리·피처 플래그·롤백 | 필수 | 초안(Claude) | [23-deployment-strategies](23-deployment-strategies/) · [../systems/server-design/08-deployment-ops.md](../systems/server-design/08-deployment-ops.md) |
| 24 | `feature-flag-lifecycle` | 플래그 유형(릴리스·운영 킬 스위치·실험·권한), 평가 일관성, 플래그 서비스 장애 시 기본값, 제거 부채 | 필수 | 초안(Claude) | [24-feature-flag-lifecycle](24-feature-flag-lifecycle/) |
| 25 | `high-availability-topology` | 이중화 모델·페일오버·split-brain·다중 AZ/리전 | 필수 | 초안(Claude) | [25-high-availability-topology](25-high-availability-topology/) · [../systems/server-design/05-ha-topology.md](../systems/server-design/05-ha-topology.md) |
| 26 | `incident-response-and-postmortem` | 사고 지휘·완화 우선·비난 없는 포스트모템 | 필수 | 초안(Claude) | [26-incident-response-and-postmortem](26-incident-response-and-postmortem/) |
| 31 | `batch-job-restart-and-checkpoint` | 배치 설계: 청크 커밋·체크포인트, 멱등 재실행, 실행 이력(잡 저장소), 부분 실패 보고, 크론 시간대·DST, 배포와 장시간 잡 공존 | 필수 | 초안(Claude) | [31-batch-job-restart-and-checkpoint](31-batch-job-restart-and-checkpoint/) |
| 44 | `runbooks-and-operational-readiness` | 런북 구조(증상·확인 명령·완화·에스컬레이션), 알람 → 런북 링크, 출시 전 운영 준비도 점검(PRR), 온콜 인수인계 | 권장 | 초안(Claude) | [44-runbooks-and-operational-readiness](44-runbooks-and-operational-readiness/) |
| 45 | `chaos-and-resilience-testing` | 장애 주입·게임 데이 | 권장 | 초안(Claude) | [45-chaos-and-resilience-testing](45-chaos-and-resilience-testing/) |
| 46 | `disaster-recovery` | RPO/RTO·백업 리전·복구 훈련 | 권장 | 초안(Claude) | [46-disaster-recovery](46-disaster-recovery/) |
| 47 | `server-design-antipatterns` | 흔한 안티패턴 카탈로그(구조·운영 — 코드 수준 성능·안정성 안티패턴은 48) | 권장 | 초안(Claude) | [47-server-design-antipatterns](47-server-design-antipatterns/) · [../systems/server-design/11-antipatterns.md](../systems/server-design/11-antipatterns.md) |
| 51 | `cells-stamps-and-blast-radius` | Deployment Stamps·셀 기반 아키텍처·Geode·셔플 샤딩 — 장애 반경을 구조로 제한 | 권장 | 초안(Claude) | [51-cells-stamps-and-blast-radius](51-cells-stamps-and-blast-radius/) |

## 11.6 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 52 | `reliability-symptom-index` | **증상 → 진단 → 처방 플레이북**(지연 급증·에러율 급증·연쇄 장애·배포 직후 502·메모리 우상향 등). 추가: 배포 직후만 느림(language/23, 42), RSS만 우상향(37), 비동기 전환 후 더 느림(39), 504인데 결제됨(35·domain-modeling/25), 타임아웃 났는데 DB 쿼리는 계속 돔(09·database/22), 잡 hang 후 이중 실행(32) | 필수 | 초안(Claude) | [52-reliability-symptom-index](52-reliability-symptom-index/) · [../systems/server-design/10-playbook-by-symptom.md](../systems/server-design/10-playbook-by-symptom.md) |
| 53 | `reliability-incidents` | 실사건: AWS S3 us-east-1 오타 명령(2017-02-28) · Slack 연휴 후 복귀 트래픽(2021-01-04) · Roblox Consul 73시간(2021-10) · CrowdStrike 채널 파일(2024-07-19) | 권장 | 초안(Claude) | [53-reliability-incidents](53-reliability-incidents/) |
