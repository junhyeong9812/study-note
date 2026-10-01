# 분산 시스템 — `cs/distributed/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §10에서 `docs/plans/2026-09-28/cs-restructure/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 36 · 검수 완료 0

> 모델(무엇이 실패하나) → 시간 → 복제·일관성 → 합의·조정 → 분산 트랜잭션·데이터 흐름. 기존 ops-patterns의 분산 패턴(논리 시계·CRDT·리더 선출·분산 락·Snowflake·outbox·saga·event sourcing)이 **이론 단원 안으로** 들어온다.
> 뼈대: DDIA 1판 5·8·9·10·11장(확인), MIT 6.5840 Spring 2026 강의(이하 6.5840 L#, 확인), 원논문.

## 10.1 모델

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `why-distributed-and-fallacies` | 분산의 이유와 8가지 오류(네트워크는 믿을 만하다 등) | 필수 | 초안(Claude) | [01-why-distributed-and-fallacies](01-why-distributed-and-fallacies/) |
| 02 | `system-and-failure-models` | 동기/부분동기/비동기, crash-stop·crash-recovery·비잔틴 | 필수 | 초안(Claude) | [02-system-and-failure-models](02-system-and-failure-models/) |
| 03 | `partial-failure-and-timeouts` | 부분 실패·모호한 결과·타임아웃 선택 | 필수 | 초안(Claude) | [03-partial-failure-and-timeouts](03-partial-failure-and-timeouts/) · [../ops-patterns/failure-at-scale](../ops-patterns/failure-at-scale/) |
| 25 | `impossibility-results` | 두 장군 문제·FLP 불가능성 | 권장 | 초안(Claude) | [25-impossibility-results](25-impossibility-results/) |

## 10.2 시간

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 04 | `physical-clocks-and-ntp` | 벽시계·단조 시계·NTP·clock skew·윤초 | 필수 | 초안(Claude) | [04-physical-clocks-and-ntp](04-physical-clocks-and-ntp/) |
| 05 | `logical-clocks` | 램포트 시계·벡터 시계·happens-before | 필수 | 초안(Claude) | [05-logical-clocks](05-logical-clocks/) · [../ops-patterns/14-logical-clock](../ops-patterns/14-logical-clock/) |
| 26 | `hybrid-clocks-and-truetime` | HLC·TrueTime·commit wait | 심화 | 초안(Claude) | [26-hybrid-clocks-and-truetime](26-hybrid-clocks-and-truetime/) |

## 10.3 복제·일관성

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 06 | `replication-strategies` | 단일 리더·다중 리더·리더리스 | 필수 | 초안(Claude) | [06-replication-strategies](06-replication-strategies/) |
| 07 | `consistency-models` | 선형화·순차·인과·최종 일관성, 세션 보장 | 필수 | 초안(Claude) | [07-consistency-models](07-consistency-models/) |
| 08 | `cap-and-pacelc` | 분할 시 C vs A, 평시 L vs C | 필수 | 초안(Claude) | [08-cap-and-pacelc](08-cap-and-pacelc/) |
| 09 | `quorums` | R+W>N·sloppy quorum·hinted handoff·anti-entropy | 권장 | 초안(Claude) | [09-quorums](09-quorums/) |
| 24 | `conflict-resolution-and-crdt` | LWW·버전 벡터·CRDT | 권장 | 초안(Claude) | [24-conflict-resolution-and-crdt](24-conflict-resolution-and-crdt/) · [../ops-patterns/15-crdt](../ops-patterns/15-crdt/) |
| 27 | `chain-replication-and-striping` | 체인 복제·앙상블/쓰기 정족수·스트라이핑 | 심화 | 초안(Claude) | [27-chain-replication-and-striping](27-chain-replication-and-striping/) · [../systems/striping](../systems/striping/) |
| 33 | `collaborative-editing-ot-and-sequence-crdt` | 실시간 공동 편집: OT(변환 함수·중앙 서버) vs 시퀀스 CRDT(RGA·Yjs), 오프라인 병합, 프레즌스·커서 | 심화 | 초안(Claude) | [33-collaborative-editing-ot-and-sequence-crdt](33-collaborative-editing-ot-and-sequence-crdt/) |

## 10.4 합의·조정

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 10 | `leader-election` | 리더 선출·리스·임기 | 필수 | 초안(Claude) | [10-leader-election](10-leader-election/) · [../ops-patterns/12-leader-election](../ops-patterns/12-leader-election/) |
| 11 | `consensus-raft` | 리더 선출·로그 복제·안전성·멤버십 변경 | 필수 | 초안(Claude) | [11-consensus-raft](11-consensus-raft/) |
| 12 | `coordination-and-fencing` | ZooKeeper·etcd·분산 락·**fencing token** | 필수 | 초안(Claude) | [12-coordination-and-fencing](12-coordination-and-fencing/) · [../ops-patterns/11-distributed-lock](../ops-patterns/11-distributed-lock/) |
| 13 | `distributed-id-generation` | Snowflake·UUIDv7·시퀀스 블록 | 권장 | 초안(Claude) | [13-distributed-id-generation](13-distributed-id-generation/) · [../ops-patterns/13-snowflake](../ops-patterns/13-snowflake/) |
| 28 | `consensus-paxos` | Paxos 기본형 | 권장 | 초안(Claude) | [28-consensus-paxos](28-consensus-paxos/) |

## 10.5 분산 트랜잭션·데이터 흐름

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 14 | `two-phase-commit` | 2PC·코디네이터·in-doubt | 필수 | 초안(Claude) | [14-two-phase-commit](14-two-phase-commit/) |
| 15 | `saga` | 보상 트랜잭션·순방향/역방향 복구 | 필수 | 초안(Claude) | [15-saga](15-saga/) · [../ops-patterns/08-saga](../ops-patterns/08-saga/) |
| 16 | `outbox-and-dual-write` | 이중 쓰기 문제·transactional outbox·CDC(상세 — 스냅샷·복제 슬롯·DDL — 는 `data-engineering/05`) | 필수 | 초안(Claude) | [16-outbox-and-dual-write](16-outbox-and-dual-write/) · [../ops-patterns/07-outbox](../ops-patterns/07-outbox/) |
| 17 | `queues-logs-and-delivery-semantics` | 큐 vs 로그, at-most/at-least/effectively-once, 순서 | 필수 | 초안(Claude) | [17-queues-logs-and-delivery-semantics](17-queues-logs-and-delivery-semantics/) · [../systems/server-design/07-async-messaging.md](../systems/server-design/07-async-messaging.md) |
| 18 | `consumer-failure-handling` | 오프셋 커밋 순서·재시도·DLQ·poison pill·리밸런스 | 필수 | 초안(Claude) | [18-consumer-failure-handling](18-consumer-failure-handling/) · [../systems/kafka-consumer-failure](../systems/kafka-consumer-failure/) |
| 21 | `kafka-internals` | 파티션·세그먼트·페이지 캐시·zero-copy·ISR | 권장 | 초안(Claude) | [21-kafka-internals](21-kafka-internals/) · [../systems/kafka-why-fast](../systems/kafka-why-fast/) |
| 22 | `event-sourcing` | 이벤트를 원천으로, 스냅샷·재생·버전 | 권장 | 초안(Claude) | [22-event-sourcing](22-event-sourcing/) · [../systems/event-sourcing](../systems/event-sourcing/) · [../ops-patterns/16-event-sourcing](../ops-patterns/16-event-sourcing/) |
| 23 | `orchestration-vs-choreography` | 중앙 조정 vs 이벤트 연쇄 | 권장 | 초안(Claude) | [23-orchestration-vs-choreography](23-orchestration-vs-choreography/) · [../systems/orchestration-choreography](../systems/orchestration-choreography/) |
| 29 | `outbox-vs-dispatch-log` | outbox와 dispatch log의 경계 | 심화 | 초안(Claude) | [29-outbox-vs-dispatch-log](29-outbox-vs-dispatch-log/) · [../systems/outbox-vs-dispatch-log](../systems/outbox-vs-dispatch-log/) |
| 30 | `batch-and-stream-processing` | MapReduce·스트림·윈도·워터마크 | 권장 | 초안(Claude) | [30-batch-and-stream-processing](30-batch-and-stream-processing/) |
| 31 | `byzantine-and-blockchain` | 비잔틴 장애·PBFT·블록체인 | 심화 | 초안(Claude) | [31-byzantine-and-blockchain](31-byzantine-and-blockchain/) · [../ops-patterns/18-blockchain](../ops-patterns/18-blockchain/) |
| 32 | `distributed-cache-consistency` | 대규모 캐시 일관성·lease·무효화 | 심화 | 초안(Claude) | [32-distributed-cache-consistency](32-distributed-cache-consistency/) |

## 10.5b 통합·메시징 패턴 (2026-09-28 추가)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 19 | `message-types-channels-and-endpoints` | 메시지 종류(Command·Event·Document), Correlation ID·Return Address·Expiration, 채널(P2P·Pub-Sub·Datatype·Dead Letter·Invalid Message), 소비 쪽 확장(Competing Consumers·Queue-Based Load Leveling·Priority Queue·Sequential Convoy·Selective Consumer) | 필수 | 초안(Claude) | [19-message-types-channels-and-endpoints](19-message-types-channels-and-endpoints/) |
| 20 | `data-ownership-and-cross-service-queries` | Database per Service vs Shared Database, API Composition·Command-side Replica·Materialized View·Index Table — 서비스 경계를 넘는 조회 | 필수 | 초안(Claude) | [20-data-ownership-and-cross-service-queries](20-data-ownership-and-cross-service-queries/) |
| 34 | `message-routing-and-transformation` | Pipes-and-Filters, Content-based Router·Filter·Recipient List·Splitter/Aggregator·Resequencer·Scatter-Gather·Routing Slip, Translator·Enricher·Claim Check·Normalizer·Canonical Data Model, Wire Tap·Message Store | 권장 | 초안(Claude) | [34-message-routing-and-transformation](34-message-routing-and-transformation/) |

## 10.6 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 35 | `distributed-symptom-index` | 역색인: 중복 처리·유실·순서 역전·리더 둘·오래된 읽기·블로킹된 트랜잭션·음수 시간 | 필수 | 초안(Claude) | [35-distributed-symptom-index](35-distributed-symptom-index/) |
| 36 | `distributed-incidents` | 실사건: GitHub 43초 분할 → 24시간 복구(2018-10-21) · Cloudflare 윤초 RRDNS(2017-01-01) · AWS EBS 재미러링 폭풍(2011-04) · metastable failure | 권장 | 초안(Claude) | [36-distributed-incidents](36-distributed-incidents/) |
